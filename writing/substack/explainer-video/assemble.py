"""Join the rendered scenes into the video: one continuous narration track, one lossy encode, subtitles, checks.

    tmp/explainer-venv/bin/python writing/substack/explainer-video/assemble.py -q review     # the film
    tmp/explainer-venv/bin/python writing/substack/explainer-video/assemble.py S10 S11 S12      # a part (draft)

With no keys it joins every scene in script.json order into the film, BUILD/out/explainer-<quality>.mp4. Keys
join a part of the film, named part-<first>-<last>-<quality> unless ``--stem`` names it; a part never takes the
film's name. The quality is draft unless ``-q`` says otherwise (the same default as render.py and qa.py). It
reads BUILD/scenes/<quality>/<Key>.mp4 (render.py) and the scene WAVs named in timings.json, and writes into
BUILD/out/:

    <stem>.mp4            H.264 (x264, CRF 16, yuv420p, BT.709 tags), AAC 192 kb/s at 48 kHz, faststart
    <stem>-1080p.mp4      the same from the same lossless frames, when the master is larger than 1920x1080
    <stem>.srt            the cues of timings.json, moved to the real scene starts (the film's subtitles;
                          BUILD/audio/narration.srt is not, after --dissolve or for a part)
    <stem>.narration.wav  the one narration track (16-bit, 48 kHz)
    <stem>.json           the manifest: scene starts, settings, the measured checks, every waiver that was used, and
                          a copy of each scene's render record (qa.py holds the film against it)

The picture is encoded once: the scene files are lossless RGB, and RGB becomes BT.709 4:2:0 here, with the
matrix named in the filter and in the tags. The sound is not taken from the scene files. Each scene's WAV is
padded or cut to the exact length of its picture and all of them are put into one track, so the audio stream
has no timestamp holes (v1 had 14). Scene joins are straight cuts, because scene N+1 is designed to start on
scene N's last frame; ``--dissolve SECONDS`` cross-fades instead (the scenes then overlap by that time).

Before the encode the tool checks that the film is made from today's narration, script and code, and stops if
not (``--force`` joins anyway, and the manifest lists what was forced):

- the picture lasts ``duration`` of timings.json to the frame, and was rendered against the timings of today
  (render.py leaves a record next to each scene file);
- each WAV lasts ``duration`` to the sample and lies next to timings.json (a narration build that was stopped
  between its WAV writes and its timings write, or a timings file that names another build's WAVs);
- the narration was built from the lines that script.json holds now: no scene in the narration build's _meta
  ``missing`` or ``stale``, none built alone since the last full build when the whole film is joined, and each
  scene's ``built_from`` equals the fingerprint of its lines (narration.load_script; no speech model is needed);
- the picture is not older than its code (the hashes in the render record), and the scenes were rendered with one
  version of each shared file (kit/);
- the lint overlay is not drawn in the picture (render.py --lint 2).

After the encode it measures the result and prints it. It exits non-zero if the frame count is wrong, if picture
and sound differ by more than one frame, if the audio stream has a hole, or if the picture is not yuv420p with
BT.709 tags. Every scene join carries the silence of the scene's tail and of the next scene's lead (about 1.0 s,
0.7 s with a tail of 0.3 s), plus up to one frame of the 1/15 s grid.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np

from render import (BUILD, DEFAULT_QUALITY, RECORD_KEYS, VID, code_changed, code_label, film_stem, frame_check, is_lossless_rgb,
                    load_timings, probe, quality, render_record, run, scene_order, stale, table, timings_digest, timings_path)

RATE = 48000
SWS = "flags=accurate_rnd+full_chroma_int+bicubic"
TO_709 = f"out_color_matrix=bt709:out_range=tv:{SWS}"
TAG_709 = "format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv"      # tags on the frames
TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]  # and on the stream


# --------------------------------------------------------------------------- measures (also used by qa.py)
def stamp(seconds: float, sep: str = ",") -> str:
    ms = int(round(seconds * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d}{sep}{ms % 1000:03d}"


def read_pcm(path: Path, rate: int = RATE) -> np.ndarray:
    """Any sound file as mono int16 at ``rate``. Timestamp holes are NOT filled: the samples come one after the other."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-map", "0:a:0", "-ac", "1", "-ar", str(rate),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<i2")


def audio_stream(path: Path) -> dict:
    """Length, format and timestamp holes of the first audio stream (the encoder's priming packet before 0 is not counted).

    A hole is a step between two packets that is longer than one packet of sound. A muxer may write it as a gap or
    as one packet with a stretched duration (v1); both are steps in the timestamps.
    """
    out = run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
               "stream=codec_name,sample_rate,channels,bit_rate:packet=pts_time,duration_time", "-of", "json", path])
    data = json.loads(out)
    if not data.get("streams"):
        return {"present": False, "holes": [], "seconds": 0.0}
    s = data["streams"][0]
    packets = [(float(p["pts_time"]), float(p["duration_time"])) for p in data["packets"] if "pts_time" in p and "duration_time" in p]
    unit = float(np.median([d for _, d in packets])) if packets else 0.0          # one packet of sound (1024 samples for AAC)
    holes = [{"at": round(a + unit, 3), "seconds": round(b - a - unit, 3)} for (a, _), (b, _) in zip(packets, packets[1:])
             if b - a > 1.5 * unit]
    return {"present": True, "codec": s.get("codec_name"), "sample_rate": int(s.get("sample_rate", 0)), "channels": s.get("channels"),
            "bit_rate": int(s["bit_rate"]) if s.get("bit_rate") else None, "start": packets[0][0] if packets else 0.0,
            "seconds": packets[-1][0] + packets[-1][1] - max(packets[0][0], 0.0) if packets else 0.0, "holes": holes,
            "samples_seconds": round(len(packets) * unit, 3)}


def loudness(path: Path) -> dict:
    """EBU R128 integrated loudness, loudness range and true peak of the first audio stream."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0", "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    summary = err[err.rfind("Summary:"):]
    get = lambda pat: (lambda m: float(m.group(1)) if m and m.group(1) not in ("-inf", "nan") else None)(re.search(pat, summary))
    return {"lufs": get(r"I:\s+(-?[\d.]+|-inf) LUFS"), "lra": get(r"LRA:\s+(-?[\d.]+|nan) LU"),
            "true_peak": get(r"Peak:\s+(-?[\d.]+|-inf) dBFS")}


# --------------------------------------------------------------------------- what the film is made from (also used by qa.py)
def narration_tie(timings: dict, keys: list[str], script: Path, whole: bool) -> tuple[list[str], list[str]]:
    """Is the narration of these scenes built from the lines that ``script`` holds now? Returns (problems, what could
    not be told), from narration.py's record in timings.json against narration.load_script (no speech model)."""
    meta, problems = timings.get("_meta", {}), []
    for name, what in (("missing", "no audio"), ("stale", "audio that is older than the script")):
        bad = [k for k in meta.get(name) or [] if k in keys]
        if bad:
            problems.append(f"the narration build left {', '.join(bad)} with {what} (_meta.{name}): run narration.py")
    if whole and meta.get("partial_since_full"):
        problems.append(f"{', '.join(meta['partial_since_full'])} were built alone (--only) since the last full narration build "
                        "(_meta.partial_since_full): run narration.py without --only")
    try:
        sys.path.insert(0, str(VID)) if str(VID) not in sys.path else None
        import narration
        lines = {s.key: s.fingerprint for s in narration.load_script(script)[1]}
    except SystemExit as e:
        return problems, [f"{script} does not load ({str(e).splitlines()[0] if str(e) else 'no reason given'})"]
    except Exception as e:                     # narration.py is not this tool's file: a broken import is reported, not raised
        return problems, [f"narration.py does not import ({type(e).__name__}: {e})"]
    unbuilt = [k for k in keys if k in lines and timings.get(k, {}).get("built_from") is None]
    problems += [f"{k} is not a scene of {script}" for k in keys if k not in lines]
    problems += [f"{k}: the narration was built from other lines than {script.name} holds now: run narration.py" for k in keys
                 if k in lines and k not in unbuilt and timings[k]["built_from"] != lines[k]]
    return problems, [f"timings.json has no built_from for {', '.join(unbuilt)} (the audio was not built by narration.py)"] if unbuilt else []


def wav_problems(key: str, t: dict, timings_file: Path, samples: int | None) -> list[str]:
    """A scene WAV that is not next to its timings file, or that does not last ``duration`` to the sample."""
    wav, out = Path(t.get("wav") or ""), []
    if t.get("wav") and wav.resolve().parent != timings_file.resolve().parent:
        out.append(f"{key}: the WAV {wav} is not next to {timings_file} (the timings name the WAVs of another build)")
    if samples is not None and abs(samples - t["duration"] * RATE) > 1:
        out.append(f"{key}: the WAV lasts {samples / RATE:.4f} s but timings.json says {t['duration']:.4f} s (was the narration build "
                   "stopped between its WAV and timings writes?)")
    return out


def mixed_code(records: dict[str, dict | None]) -> dict[str, list[str]]:
    """Project files that the scenes were rendered with in more than one version: {file: ["S01 S02", "S03"]}."""
    seen: dict[str, dict[str, list[str]]] = {}
    for key, r in records.items():
        for f, h in ((r or {}).get("code") or {}).get("files", {}).items():
            seen.setdefault(f, {}).setdefault(h, []).append(key)
    return {code_label(f): [" ".join(k) for k in v.values()] for f, v in seen.items() if len(v) > 1}


# --------------------------------------------------------------------------- narration track
def narration_track(scenes: list[dict], timings: dict, fps: float, total_frames: int, allow_silent: bool) -> tuple[np.ndarray, list[str]]:
    """One continuous mono track: each scene's WAV at its picture's start, padded or cut to its picture's length."""
    at = lambda frame: int(round(frame * RATE / fps))
    mix, notes = np.zeros(at(total_frames), dtype=np.int32), []
    for s in scenes:
        wav = Path(timings[s["key"]].get("wav") or "")
        if s.get("pcm") is None and not wav.is_file():
            if not allow_silent:
                raise SystemExit(f"no WAV for {s['key']} ({wav}); use --allow-silent to leave the scene silent")
            notes.append(f"{s['key']}: no WAV, the scene is silent")
            continue
        x = s["pcm"] if s.get("pcm") is not None else read_pcm(wav)
        room = at(s["start_frame"] + s["frames"]) - at(s["start_frame"])
        s["wav_seconds"], s["pad_seconds"] = len(x) / RATE, (room - len(x)) / RATE
        if len(x) > room:
            cut = x[room:]
            if np.abs(cut).max(initial=0) > 32768 * 10 ** (-50 / 20):
                notes.append(f"{s['key']}: the WAV is {len(cut) / RATE:.3f} s longer than the picture and the part that was cut is not silent")
            x = x[:room]
        a = at(s["start_frame"])
        if np.abs(mix[a:a + len(x)]).max(initial=0) > 32768 * 10 ** (-50 / 20) and s.get("overlap_frames"):
            notes.append(f"{s['key']}: the dissolve overlaps sound of the scene before it")
        mix[a:a + len(x)] += x
    if np.abs(mix).max(initial=0) > 32767:
        notes.append("the mixed track clipped")
    return np.clip(mix, -32768, 32767).astype("<i2"), notes


def write_wav(path: Path, x: np.ndarray) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(x.tobytes())


# --------------------------------------------------------------------------- picture
def to_rgb(info: dict) -> str:
    """The filter that brings one scene to planar RGB (lossless for render.py's files)."""
    if info["pix_fmt"] in ("gbrp", "rgb24", "bgr24", "bgr0", "rgba", "argb"):
        return "format=gbrp"
    matrix = "bt709" if info["color_space"] == "bt709" else "bt601"          # Manim itself writes BT.601 without a tag
    rng = "pc" if info["color_range"] == "pc" or info["pix_fmt"].startswith("yuvj") else "tv"
    return f"scale=in_color_matrix={matrix}:in_range={rng}:{SWS},format=gbrp"


def filter_graph(scenes: list[dict], fps: float, dissolve_frames: int, small: tuple[int, int] | None) -> str:
    parts = [f"[{i}:v]{to_rgb(s['info'])},setpts=N/({fps:g}*TB),setsar=1[v{i}]" for i, s in enumerate(scenes)]
    if len(scenes) == 1:
        parts.append("[v0]null[j]")
    elif dissolve_frames == 0:
        parts.append("".join(f"[v{i}]" for i in range(len(scenes))) + f"concat=n={len(scenes)}:v=1:a=0[j]")
    else:
        prev = "v0"
        for i, s in enumerate(scenes[1:], start=1):
            parts.append(f"[{prev}][v{i}]xfade=transition=fade:duration={dissolve_frames / fps:.6f}:"
                         f"offset={s['start_frame'] / fps:.6f}[x{i}]")
            prev = f"x{i}"
        parts.append(f"[{prev}]null[j]")
    if small:
        parts.append(f"[j]split[ja][jb];[ja]scale={TO_709},{TAG_709}[main];"
                     f"[jb]scale={small[0]}:{small[1]}:{TO_709.replace('bicubic', 'lanczos')},{TAG_709}[small]")
    else:
        parts.append(f"[j]scale={TO_709},{TAG_709}[main]")
    return ";".join(parts)


def write_srt(path: Path, scenes: list[dict], timings: dict, fps: float) -> int:
    cues = [(s["start_frame"] / fps + c["start"], s["start_frame"] / fps + c["end"], c["text"])
            for s in scenes for c in timings[s["key"]].get("cues", []) if c.get("text", "").strip()]
    cues.sort()
    out = []
    for n, (a, b, text) in enumerate(cues, start=1):
        if n < len(cues):
            b = min(b, cues[n][0] - 0.001)
        out.append(f"{n}\n{stamp(a)} --> {stamp(max(b, a + 0.05))}\n{text.strip()}\n")
    path.write_text("\n".join(out), encoding="utf-8")
    return len(cues)


# --------------------------------------------------------------------------- command line
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Join the rendered scenes into one video with one narration track.")
    ap.add_argument("keys", nargs="*", help="scene keys to join (default: all, in script.json order)")
    ap.add_argument("-q", "--quality", choices=("draft", "review", "final"), default=DEFAULT_QUALITY)
    ap.add_argument("--stem", default=None, help="name of the output files (default explainer-<quality> for the film, "
                                                  "part-<first>-<last>-<quality> for a part)")
    ap.add_argument("--crf", type=float, default=16, help="x264 constant rate factor (default 16)")
    ap.add_argument("--preset", default="slow", help="x264 preset (default slow)")
    ap.add_argument("--dissolve", type=float, default=0.0, metavar="SECONDS", help="cross-fade at scene joins (default 0: cuts)")
    ap.add_argument("--channels", type=int, choices=(1, 2), default=1, help="1 keeps the narration mono (default); 2 writes it to both channels")
    ap.add_argument("--timings", type=Path, default=None)
    ap.add_argument("--script", type=Path, default=None)
    ap.add_argument("--scene-dir", type=Path, default=None, help="default BUILD/scenes/<quality>")
    ap.add_argument("--out-dir", type=Path, default=BUILD / "out")
    ap.add_argument("--no-1080", action="store_true", help="do not write the 1080p copy of a larger master")
    ap.add_argument("--allow-silent", action="store_true", help="a scene with no WAV is silent (default: stop)")
    ap.add_argument("--force", action="store_true", help="join even if the film would not be made from today's narration, script and code "
                                                        "(see the checks above; the manifest lists what was forced)")
    args = ap.parse_args(argv)

    q = quality(args.quality)
    timings = load_timings(args.timings)
    tfile, script = timings_path(args.timings), (args.script or VID / "script.json").resolve()
    order = scene_order(timings, args.script)
    keys = args.keys or order
    whole, film = keys == order, film_stem(q)
    stem = args.stem or (film if whole else f"part-{keys[0]}-{q.name}" if len(keys) == 1 else f"part-{keys[0]}-{keys[-1]}-{q.name}")
    if stem == film and not whole:
        raise SystemExit(f"{film} is the name of the whole film (the {len(order)} scenes of script.json, in order); "
                         f"a part takes another name (--stem, default part-<first>-<last>-<quality>)")
    scene_dir = (args.scene_dir or BUILD / "scenes" / q.name).resolve()
    missing = [k for k in keys if not (scene_dir / f"{k}.mp4").exists()] + [f"{k} (no timings)" for k in keys if k not in timings]
    if missing:
        raise SystemExit(f"missing in {scene_dir}: " + ", ".join(missing))

    scenes, problems, notes, records = [], [], [], {}
    for k in keys:
        path = scene_dir / f"{k}.mp4"
        info = probe(path)
        ok, _, text = frame_check(info["frames"], timings[k], info["fps"])
        if not ok:
            problems.append(f"{k}: {text}")
        lossless = is_lossless_rgb(path, info)
        if not lossless:
            notes.append(f"{k}: the scene file is not lossless RGB ({info['codec']} {info['pix_fmt']}); this encode is a second lossy generation")
        record = records[k] = render_record(path)
        old = stale(path, timings[k])
        if old:
            problems.append(f"{k}: the picture was rendered against other timings (the narration changed after the render)")
        elif old is None:
            notes.append(f"{k}: no record of the render next to the scene file; the tool cannot tell if the picture is older than the timings or its code")
        if record and record.get("lint_overlay"):
            problems.append(f"{k}: the lint overlay is drawn in the picture (render.py --lint 2): render it again with --lint 1")
        changed = code_changed(record) if record else []
        if changed is None:
            notes.append(f"{k}: the render record holds no hash of the code (an older render.py): the tool cannot tell if the picture is older than its code")
        elif changed:
            problems.append(f"{k}: rendered before its code changed ({', '.join(changed[:3])}{' ...' if len(changed) > 3 else ''}): render it again")
        wav = Path(timings[k].get("wav") or "")
        pcm = read_pcm(wav) if wav.is_file() else None
        problems += wav_problems(k, timings[k], tfile, None if pcm is None else len(pcm))
        scenes.append({"key": k, "source": str(path), "frames": info["frames"], "info": info, "timings": timings_digest(timings[k]), "pcm": pcm,
                       "lossless": lossless, "record": {x: record[x] for x in RECORD_KEYS if x in record} if record else None})
    problems += [f"the scenes were rendered with different versions of {f}: {' / '.join(g)}" for f, g in mixed_code(records).items()]
    tie, unknown = narration_tie(timings, keys, script, whole)
    problems += tie
    notes += [f"cannot tell if the narration is built from {script.name}: {u}" for u in unknown]
    shapes = {(s["info"]["width"], s["info"]["height"], s["info"]["fps"]) for s in scenes}
    if len(shapes) != 1:
        raise SystemExit(f"the scenes do not share one size and frame rate: {sorted(shapes)}")
    if problems and not args.force:
        raise SystemExit("the film would not be made from today's narration, script and code (fix the cause, or --force):\n  "
                         + "\n  ".join(problems))
    notes += [f"forced: {p}" for p in problems]
    waivers = [f"--force: {p}" for p in problems]
    width, height, fps = shapes.pop()
    d = int(round(args.dissolve * fps))
    if d and d * 2 >= min(s["frames"] for s in scenes):
        raise SystemExit("the dissolve is longer than half of the shortest scene")
    start = 0
    for i, s in enumerate(scenes):
        s["start_frame"], s["overlap_frames"] = start, d if i else 0
        start += s["frames"] - d
    total = start + d
    seconds = total / fps

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    main_mp4, wav = out_dir / f"{stem}.mp4", out_dir / f"{stem}.narration.wav"
    small_mp4 = out_dir / f"{stem}-1080p.mp4" if height > 1080 and not args.no_1080 else None
    for old in (main_mp4, out_dir / f"{stem}-1080p.mp4", out_dir / f"{stem}.srt", out_dir / f"{stem}.json"):
        old.unlink(missing_ok=True)                # if this run fails, no older video of the same name stays behind
    track, track_notes = narration_track(scenes, timings, fps, total, args.allow_silent)
    notes += track_notes
    waivers += [f"--allow-silent: {n}" for n in track_notes if n.endswith("the scene is silent")]
    write_wav(wav, track)

    cmd = ["ffmpeg", "-v", "error", "-y"]
    for s in scenes:
        cmd += ["-i", s["source"]]
    cmd += ["-i", str(wav), "-filter_complex", filter_graph(scenes, fps, d, (1920, 1080) if small_mp4 else None)]
    for label, target, pixels in (("[main]", main_mp4, width * height), ("[small]", small_mp4, 1920 * 1080)):
        if target is not None:
            compat = ["-refs", "4"] if pixels <= 1920 * 1080 else []          # keeps 1080p at H.264 level 4.x for old decoders
            cmd += ["-map", label, "-map", f"{len(scenes)}:a:0", "-c:v", "libx264", "-preset", args.preset, "-crf", f"{args.crf:g}",
                    *compat, "-pix_fmt", "yuv420p", *TAGS, "-fps_mode", "passthrough", "-c:a", "aac", "-b:a", "192k", "-ar", str(RATE),
                    "-ac", str(args.channels), "-map_metadata", "-1", "-movflags", "+faststart", str(target)]
    print(f"joining {len(scenes)} scenes into {stem} ({'the whole film' if whole else 'a part of the film'}), "
          f"{width}x{height} at {fps:g} fps, {total} frames ({seconds:.2f} s), CRF {args.crf:g}, "
          f"preset {args.preset}" + (f", dissolve {d} frames" if d else ", straight cuts"))
    t0 = time.time()
    try:
        run(cmd)
    except RuntimeError as e:
        for part in (main_mp4, small_mp4):
            if part is not None:
                part.unlink(missing_ok=True)
        raise SystemExit(f"the encode failed: {e}")
    wall = time.time() - t0
    n_cues = write_srt(out_dir / f"{stem}.srt", scenes, timings, fps)

    # verify what was written
    failures = []
    checks = {}
    for name, path in (("master", main_mp4), ("1080p", small_mp4)):
        if path is None:
            continue
        info, a, loud = probe(path), audio_stream(path), loudness(path)
        diff = a["seconds"] - info["frames"] / info["fps"]
        checks[name] = {"file": str(path), "mb": round(path.stat().st_size / 1e6, 2), "video": info, "audio": {**a, **loud},
                        "audio_minus_video": round(diff, 4)}
        if info["frames"] != total:
            failures.append(f"{name}: {info['frames']} frames, expected {total}")
        if abs(diff) > 1 / fps + 1e-6:
            failures.append(f"{name}: sound is {diff:+.3f} s against the picture (more than one frame)")
        if a["holes"]:
            failures.append(f"{name}: {len(a['holes'])} holes in the audio timestamps")
        if (info["pix_fmt"], info["color_space"], info["color_primaries"], info["color_transfer"], info["color_range"]) != \
                ("yuv420p", "bt709", "bt709", "bt709", "tv"):
            failures.append(f"{name}: picture is {info['pix_fmt']} with tags {info['color_space']}/{info['color_primaries']}/"
                            f"{info['color_transfer']}/{info['color_range']}, not yuv420p with bt709/bt709/bt709/tv")
        lufs = "silent" if loud["lufs"] is None else f"{loud['lufs']:.1f} LUFS"
        peak = "" if loud["true_peak"] is None else f", true peak {loud['true_peak']:.1f} dBTP"
        print(f"\n{name}: {path}  ({checks[name]['mb']} MB, {wall:.1f} s to encode)")
        print(f"  picture  {info['width']}x{info['height']} {info['codec']} {info['pix_fmt']} {info['color_space']}, {info['frames']} frames "
              f"at {info['fps']:g} fps = {info['frames'] / info['fps']:.3f} s")
        print(f"  sound    {a['codec']} {a['sample_rate']} Hz, {a['channels']} ch, {a['seconds']:.3f} s ({diff * 1000:+.0f} ms against the "
              f"picture; one frame is {1000 / fps:.0f} ms), {len(a['holes'])} timestamp holes, {lufs}{peak}")
        if loud["lufs"] is not None and abs(loud["lufs"] + 16) > 1:
            notes.append(f"{name}: loudness {loud['lufs']:.1f} LUFS is outside -16 +-1")
        if loud["true_peak"] is not None and loud["true_peak"] > -1.5:
            notes.append(f"{name}: true peak {loud['true_peak']:.1f} dBTP is above -1.5")
    print(f"  subtitles {n_cues} cues in {out_dir / (stem + '.srt')}")
    rows = [[s["key"], stamp(s["start_frame"] / fps, "."), s["start_frame"], s["frames"], f"{s['frames'] / fps:.3f}",
             f"{s.get('pad_seconds', 0) * 1000:+.0f}"] for s in scenes]
    print("\n" + table(rows, ["scene", "starts at", "frame", "frames", "seconds", "WAV pad ms"]))
    for n in notes:
        print(f"note: {n}")
    manifest = {"stem": stem, "quality": q.name, "width": width, "height": height, "fps": fps, "frames": total, "seconds": seconds,
                "crf": args.crf, "preset": args.preset, "dissolve_frames": d, "channels": args.channels,
                "timings": str(tfile), "script": str(script), "whole_film": whole, "subtitles": n_cues, "narration": str(wav),
                "scenes": [{k: s[k] for k in ("key", "source", "start_frame", "frames", "overlap_frames", "timings", "lossless", "record")}
                           | {"start": s["start_frame"] / fps} for s in scenes],
                "checks": checks, "waivers": waivers, "notes": notes, "failures": failures}
    (out_dir / f"{stem}.json").write_text(json.dumps(manifest, indent=1))
    for f in failures:
        print(f"FAILED: {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
