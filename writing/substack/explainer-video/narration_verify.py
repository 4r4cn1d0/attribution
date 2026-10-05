"""Verify a narration build.  This file does not import the builder: it reads script.json, the reviewed script,
timings.json, narration.srt and the WAVs, measures the sound itself, and asks ffmpeg for loudness and true peak.

Checks: the audio is not older than the script (each scene's "built_from" equals the fingerprint that this file
works out from script.json, the voice is the script's, the builder names no scene as out of date or not built,
and, without --only, no scene was built with --only since the last full build); the words in timings.json rebuild
the script (and the script is in the reviewed text); word times are in order; line edges sit on the sound's own
edges; the pauses between lines and inside lines are as the script set them, and silent; there is no click in a
pause or at a scene's ends; the programme is at the target loudness with its true peak under -1.5 dBTP; every
duration is a multiple of 1/15 s and equals the WAV's length; the silence after a scene's last word is the tail
that the script asks; subtitle cues are in order, at most 2 lines of 42 characters, and equal to narration.srt.

    tmp/explainer-venv/bin/python writing/substack/explainer-video/narration_verify.py
        [--audio DIR] [--script script.json] [--reviewed script-and-storyboard.md] [--only S03 S04] [--voice NAME]

--voice names the voice that the audio must have when a build used narration.py --voice (default: the script's).
Exit status 0 means that every check passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BUILD = Path(os.environ.get("EXPLAINER_BUILD") or ROOT / "tmp" / "explainer-build-v2")

RATE, GRID_FPS = 48000, 15
LEAD, TAIL, LAST_TAIL = 0.40, 0.60, 1.50
PAUSE_NAMES = {"short": 0.30, "normal": 0.50, "long": 0.90}
TARGET_LUFS, PEAK_LIMIT_DBTP = -16.0, -1.5
SILENT_DB, BREATH_DB = -40.0, -30.0        # below the loudest 10 ms of the same line
LOOSE_DB, STRICT_DB = -35.0, -45.0         # an edge of the sound is where the level crosses between these two
LINE_CHARS, CUE_LINES = 42, 2
T_JSON, T_EDGE, T_AUDIO = 0.002, 0.030, 0.030   # tolerances: a time in the JSON; an edge on the sound; a pause in the sound
CLICK_STEP = 0.02                               # largest sample-to-sample step inside a silence (full scale = 1)


class Report:
    def __init__(self) -> None:
        self.passed, self.failed = 0, []

    def check(self, ok: bool, text: str) -> bool:
        self.passed += bool(ok)
        if not ok:
            self.failed.append(text)
        print(("  PASS " if ok else "  FAIL ") + text)
        return bool(ok)


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def bare(word: str) -> str:
    return re.sub(r"^\W+|\W+$", "", word).lower()


def plain(text: str) -> str:
    """The form for the word-for-word comparison with the reviewed text."""
    text = "\n".join(re.sub(r"^\s*(?:>\s*)*(?:(?:[-+*]|\d+[.)])\s+)?", "", x) for x in text.splitlines())
    return squash(text.replace("*", "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"'))


def seconds(value) -> float:
    """A pause of script.json in seconds: a number, a name, or text such as "1.6 s"."""
    if isinstance(value, str):
        value = value.strip()
        return PAUSE_NAMES[value] if value in PAUSE_NAMES else float(value.rstrip("s"))
    return float(value)


def scene_tail(scene: dict, last: bool) -> float:
    """The silence that the script asks after a scene's last word: "tail" if the scene sets it; else the pause of
    its last line, which runs across the scene boundary (tail, then the lead of the next scene), but never less
    than the default tail.  Rounded as the builder rounds it, because the fingerprint holds this value."""
    default = LAST_TAIL if last else TAIL
    if "tail" in scene:
        return seconds(scene["tail"])
    asked = seconds(scene["lines"][-1]["pause_after"]) - (0.0 if last else LEAD)
    return round(asked, 3) if asked > default + 1e-9 else default


def fingerprint(scene: dict, last: bool) -> str:
    """The value that the builder writes as the scene's "built_from", worked out here from script.json alone: it
    changes when a line's words, pause, speed, 'say' or inner pauses change, or the scene's tail (the voice apart)."""
    said = [[squash(ln["text"]), seconds(ln["pause_after"]), float(ln.get("speed", 1.0)), ln.get("say"),
             sorted((str(a), seconds(v)) for a, v in (ln.get("pauses") or {}).items())] for ln in scene["lines"]]
    return hashlib.sha256(json.dumps([said, scene_tail(scene, last)], ensure_ascii=False).encode()).hexdigest()[:16]


def levels(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(centre time, dB) of 10 ms frames, 5 ms apart."""
    w, h = RATE // 100, RATE // 200
    n = 1 + (len(x) - w) // h
    frames = np.lib.stride_tricks.sliding_window_view(x.astype(np.float64), w)[::h][:n]
    return (np.arange(n) * h + w / 2) / RATE, 10 * np.log10((frames ** 2).mean(axis=1) + 1e-24)


def sound_edges(tt: np.ndarray, rel: np.ndarray, end: float, start: float, level: float) -> tuple[float, float]:
    """Around the silence between two word times: (when the sound before it falls under ``level``, when the
    sound after it rises over ``level``).  Each side is searched from 0.15 s outside the word time to the middle."""
    mid = (end + start) / 2
    before = np.flatnonzero((tt >= end - 0.15) & (tt <= mid) & (rel > level))
    after = np.flatnonzero((tt >= mid) & (tt <= start + 0.15) & (rel > level))
    return (tt[before[-1]] + 0.005 if len(before) else end - 0.15), (tt[after[0]] - 0.005 if len(after) else start + 0.15)


def ebur128(pcm: np.ndarray) -> tuple[float, float]:
    """(integrated LUFS, true peak dBTP) of 16-bit mono 48 kHz samples, measured by ffmpeg."""
    run = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-f", "s16le", "-ar", str(RATE), "-ac", "1", "-i", "pipe:0",
                          "-af", "ebur128=peak=true", "-f", "null", "-"], input=pcm.astype("<i2").tobytes(), capture_output=True)
    text = run.stderr.decode("utf-8", "replace")
    tail = text[text.rfind("Summary"):]
    loud, peak = re.search(r"I:\s+(-?[\d.]+) LUFS", tail), re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail)
    if run.returncode != 0 or not loud or not peak:
        raise RuntimeError("ffmpeg ebur128 gave no result: " + text[-300:])
    return float(loud.group(1)), float(peak.group(1))


def verify_scene(rep: Report, audio: Path, key: str, lines: list[dict], tail: float, entry: dict,
                 reviewed: str | None) -> np.ndarray | None:
    """All checks of one scene.  Returns its samples (16 bit) for the loudness checks, or None without a WAV."""
    wav = Path(entry["wav"])
    in_place = wav.exists() and wav.resolve() == (audio / f"{key}.wav").resolve()
    if not rep.check(in_place, f"'wav' names an existing file in the audio directory: {wav}"):
        return None
    info = sf.info(wav)
    pcm, _ = sf.read(wav, dtype="int16")
    x = pcm.astype(np.float32) / 32768.0
    total = len(x) / RATE
    print(f"\n{key}: {total:.3f} s, {len(lines)} lines")
    rep.check(info.samplerate == RATE and info.channels == 1 and info.subtype == "PCM_16",
              f"48 kHz, mono, 16 bit (is {info.samplerate} Hz, {info.channels} ch, {info.subtype})")
    grid = RATE // GRID_FPS
    rep.check(len(x) % grid == 0 and abs(entry["duration"] - total) < 1e-9,
              f"duration {entry['duration']:.6f} s = {len(x) / grid:g} frames at 15 fps, and the WAV has exactly that length ({len(x)} samples)")
    if "frames" in entry:
        rep.check(all(entry["frames"][str(f)] * RATE == len(x) * f for f in (15, 30, 60)),
                  f"'frames' gives the same length at 15, 30 and 60 fps: {entry['frames']}")

    S = entry["sentences"]
    if not rep.check(len(S) == len(lines), f"one 'sentences' entry per script line ({len(S)} and {len(lines)})"):
        return pcm
    words = [w for s in S for w in s["words"]]
    rep.check(all(" ".join(w["w"] for w in s["words"]) == squash(ln["text"]) == s["text"] for s, ln in zip(S, lines)),
              "the words of each line, joined, are exactly the script's text")
    if reviewed is not None:
        absent = [ln["text"] for ln in lines if plain(ln["text"]) not in reviewed]
        rep.check(not absent, "every line is in the reviewed script word for word" + (f" (not found: {absent})" if absent else ""))
    rep.check(all(w["s"] <= w["e"] for w in words) and all(a["e"] <= b["s"] + 1e-6 for a, b in zip(words, words[1:])),
              f"{len(words)} words: start <= end, in order, no overlap")
    rep.check(all(s["start"] == s["words"][0]["s"] and s["end"] == s["words"][-1]["e"] for s in S)
              and entry["starts"] == [s["start"] for s in S],
              "each line's start and end are its first and last word; 'starts' lists the line starts")
    rep.check(abs(S[0]["start"] - LEAD) <= T_JSON, f"the first word starts at {S[0]['start']:.3f} s (lead {LEAD} s)")
    hold = total - S[-1]["end"]
    rep.check(tail - T_JSON <= hold < tail + 1 / GRID_FPS + T_JSON,
              f"after the last word: {hold:.3f} s (the script asks a tail of {tail:.2f} s; the scene ends on the 1/15 s grid)")

    # Level of every 10 ms, relative to the loudest 10 ms of the line it belongs to.
    tt, db = levels(x)
    rel = np.full(len(tt), -200.0)
    for s in S:
        near = (tt >= s["start"] - 0.3) & (tt <= s["end"] + 0.3)
        rel[near] = np.maximum(rel[near], db[near] - db[(tt >= s["start"]) & (tt <= s["end"])].max())

    def silence(end: float, start: float) -> tuple[float, float, float, float, float]:
        """A silence given by two word times, measured in the sound: (how far the end lies outside the band of the
        sound's fall, how far the start lies outside the band of its rise, shortest length, longest length,
        loudest level inside)."""
        (off_a, on_a), (off_b, on_b) = sound_edges(tt, rel, end, start, LOOSE_DB), sound_edges(tt, rel, end, start, STRICT_DB)
        inside = rel[(tt > end + 0.02) & (tt < start - 0.02)]
        return (max(off_a - end, end - off_b, 0.0), max(on_b - start, start - on_a, 0.0), on_b - off_b, on_a - off_a,
                float(inside.max()) if len(inside) else -200.0)

    def silence_ok(end: float, start: float, want: float) -> tuple[bool, str]:
        _, _, shortest, longest, loud = silence(end, start)
        ok = abs(start - end - want) <= T_JSON and shortest - T_AUDIO <= want <= longest + T_AUDIO and loud < BREATH_DB
        return ok, (f"asked {want:.2f} s, timings {start - end:.3f} s, sound {shortest:.3f} to {longest:.3f} s "
                    f"(loudest inside {loud:.0f} dB)")

    bounds = [(0.0, S[0]["start"])] + [(a["end"], b["start"]) for a, b in zip(S, S[1:])] + [(S[-1]["end"], total)]
    off_err = max(silence(a, b)[0] for a, b in bounds[1:])
    on_err = max(silence(a, b)[1] for a, b in bounds[:-1])
    rep.check(max(on_err, off_err) <= T_EDGE,
              f"line starts and ends sit on the sound's edges (where the level crosses {LOOSE_DB:.0f} to {STRICT_DB:.0f} dB): "
              f"largest error {1000 * on_err:.0f} ms at a start, {1000 * off_err:.0f} ms at an end")

    gaps, all_ok = [], True
    for li in range(len(S) - 1):
        want = seconds(lines[li]["pause_after"])
        ok, text = silence_ok(S[li]["end"], S[li + 1]["start"], want)
        all_ok &= ok and abs(S[li]["pause_after"] - want) <= T_JSON
        gaps.append((S[li]["end"], S[li + 1]["start"]))
        print(f"     {'ok  ' if ok else 'BAD '}after line {li}: {text}")
    rep.check(all_ok, f"the {len(S) - 1} pauses between lines are as the script set them, in timings.json and in the sound, and are silent")
    for li, ln in enumerate(lines):
        ws = S[li]["words"]
        for anchor, want in (ln.get("pauses") or {}).items():
            hits = [i for i, w in enumerate(ws) if w["w"] == anchor] or [i for i, w in enumerate(ws) if bare(w["w"]) == bare(anchor)]
            if not rep.check(len(hits) == 1 and hits[0] + 1 < len(ws), f"line {li}: the pause anchor {anchor!r} names one word"):
                continue
            ok, text = silence_ok(ws[hits[0]]["e"], ws[hits[0] + 1]["s"], seconds(want))
            gaps.append((ws[hits[0]]["e"], ws[hits[0] + 1]["s"]))
            rep.check(ok, f"line {li}: pause after {anchor!r}: {text}")
    faint = [f"{w['w']!r} in line {li} at {w['s']:.2f}-{w['e']:.2f} s" for li, s in enumerate(S) for w in s["words"]
             if w["e"] - w["s"] < 0.02 or (rel[(tt >= w["s"]) & (tt <= w["e"])] > SILENT_DB).mean() < 0.5]
    rep.check(not faint, "every word's interval holds sound" + (f" (too short or mostly silent: {'; '.join(faint)})" if faint else ""))

    # Clicks: inside every pause of 0.12 s or more, in the lead and in the tail, the sound may not jump.
    gaps += [(a["e"], b["s"]) for a, b in zip(words, words[1:]) if b["s"] - a["e"] >= 0.12]
    gaps += [(-0.02, S[0]["start"]), (S[-1]["end"], total + 0.02)]
    step = np.abs(np.diff(x))
    jumps = [float(step[int((a + 0.02) * RATE):max(int((a + 0.02) * RATE), int((b - 0.02) * RATE))].max(initial=0.0)) for a, b in gaps]
    rep.check(max(jumps) < CLICK_STEP and abs(x[0]) < 1e-3 and abs(x[-1]) < 1e-3,
              f"no click: largest sample step inside {len(gaps)} silences {max(jumps):.4f} (limit {CLICK_STEP}); "
              "the scene starts and ends at zero")
    rep.check(abs(float(x.mean())) < 1e-3 and int(np.abs(pcm).max()) < 32767,
              f"no clipped sample and no offset (largest sample {np.abs(pcm).max()}, mean {x.mean():+.5f})")

    cues = entry["cues"]
    rep.check(all(0 <= c["start"] < c["end"] <= total + 1e-6 for c in cues)
              and all(a["end"] <= b["start"] + 1e-6 for a, b in zip(cues, cues[1:])),
              f"{len(cues)} cues: inside the scene, in order, no overlap")
    longest = max(len(part) for c in cues for part in c["text"].split("\n"))
    rep.check(all(c["text"].count("\n") < CUE_LINES for c in cues) and longest <= LINE_CHARS,
              f"cues have at most {CUE_LINES} lines of {LINE_CHARS} characters (longest line: {longest})")
    rep.check(" ".join(c["text"].replace("\n", " ") for c in cues) == " ".join(s["text"] for s in S),
              "the cue texts, joined, are exactly the script's text")
    starts = {w["s"] for w in words}
    rep.check(all(c["start"] in starts for c in cues), "every cue starts with a word")
    rate = [len(c["text"]) / (c["end"] - c["start"]) for c in cues]
    speech = sum(s["end"] - s["start"] for s in S)
    print(f"     reading speed: median {np.median(rate):.1f}, highest {max(rate):.1f} characters per second; "
          f"shortest cue {min(c['end'] - c['start'] for c in cues):.2f} s")
    print(f"     pace: {60 * len(words) / total:.0f} words per minute over the scene, {60 * len(words) / speech:.0f} while speaking; "
          f"sound within the lines {100 * speech / total:.0f}% of the scene")
    return pcm


def clock(text: str) -> float:
    h, m, rest = text.split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest.replace(",", "."))


def verify(audio: Path, script: Path, reviewed: Path | None, only: list[str] | None, voice: str | None = None) -> tuple[int, list[str]]:
    """Run every check and print it.  Returns (number of checks passed, the checks that failed)."""
    rep = Report()
    data = json.loads(script.read_text(encoding="utf-8"))
    timings = json.loads((audio / "timings.json").read_text(encoding="utf-8"))
    meta = timings.get("_meta", {})
    reviewed_text = plain(reviewed.read_text(encoding="utf-8")) if reviewed else None
    keys = [s["key"] for s in data["scenes"]]
    chosen = [k for k in keys if not only or k in only]
    print(f"audio {audio}\nscript {script}\nreviewed {reviewed}")
    rep.check(all(k in timings for k in chosen), f"timings.json has every scene: {' '.join(chosen)}")
    want_voice = voice or data.get("voice", "af_heart")
    rep.check(meta.get("sample_rate") == RATE and meta.get("voice") == want_voice,
              f"_meta: sample rate {meta.get('sample_rate')}, voice {meta.get('voice')} (the script's voice is {data.get('voice', 'af_heart')}"
              + (f"; --voice asks {voice})" if voice else ")"))
    old = [f"{s['key']} (built from {timings[s['key']].get('built_from')}, the script gives {fingerprint(s, i == len(keys) - 1)})"
           for i, s in enumerate(data["scenes"]) if s["key"] in chosen and s["key"] in timings
           and timings[s["key"]].get("built_from") != fingerprint(s, i == len(keys) - 1)]
    rep.check(not old, "each scene's audio was built from its lines as script.json has them now (fingerprint of words, pauses, "
              "speed, 'say', tail)" + (f"; OLDER THAN THE SCRIPT: {'; '.join(old)}; build these scenes again" if old else ""))
    stale = [k for k in meta.get("stale") or [] if k in chosen]
    absent = [k for k in meta.get("missing") or [] if k in chosen]
    rep.check(not stale and not absent, "the builder names no scene as older than the script or not built"
              + (f" (older than the script: {' '.join(stale) or 'none'}; not built: {' '.join(absent) or 'none'})" if stale or absent else ""))
    partial = meta.get("partial_since_full") or []
    if only:
        print(f"     not checked with --only: whether scenes were built with --only since the last full build ({' '.join(partial) or 'none'})")
    else:
        rep.check(not partial, "no scene was built with --only since the last full build"
                  + (f" (built alone: {' '.join(partial)}; run a full build before the final video, or verify these scenes with --only)"
                     if partial else ""))
    pcm = {}
    for i, scene in enumerate(data["scenes"]):
        if scene["key"] in chosen and scene["key"] in timings:
            tail = scene_tail(scene, i == len(keys) - 1)
            got = verify_scene(rep, audio, scene["key"], scene["lines"], tail, timings[scene["key"]], reviewed_text)
            if got is not None:
                pcm[scene["key"]] = got

    print("\nloudness and peak (ffmpeg ebur128)")
    target = float(meta.get("target_lufs", TARGET_LUFS))
    if not rep.check(shutil.which("ffmpeg") is not None, "ffmpeg is available") or not pcm:
        return rep.passed, rep.failed
    per = {k: ebur128(v) for k, v in pcm.items()}
    for k, (loud, peak) in per.items():
        print(f"     {k}: {loud:.1f} LUFS, true peak {peak:.1f} dBTP")
    whole = ebur128(np.concatenate([pcm[k] for k in keys if k in pcm]))
    complete = set(pcm) == set(keys)
    rep.check(abs(whole[0] - target) <= 0.5,
              f"{'the programme' if complete else 'the verified scenes together'}: {whole[0]:.1f} LUFS (target {target:.1f}, +-0.5)")
    top = max(max(p for _, p in per.values()), whole[1])
    rep.check(top < PEAK_LIMIT_DBTP, f"true peak {top:.1f} dBTP (limit {PEAK_LIMIT_DBTP})")
    spread = max(v for v, _ in per.values()) - min(v for v, _ in per.values())
    rep.check(all(abs(v - target) <= 1.0 for v, _ in per.values()),
              f"every scene is within 1 LU of the target (scenes differ by {spread:.1f} LU)")

    print("\nnarration.srt")
    built = [k for k in meta.get("scenes", keys) if k in timings]
    want, offset = [], 0.0
    for k in built:
        want += [(offset + c["start"], offset + c["end"], c["text"]) for c in timings[k]["cues"]]
        offset += timings[k]["duration"]
    srt = re.findall(r"(\d+)\n([\d:,]+) --> ([\d:,]+)\n(.+?)(?:\n\n|\n*$)", (audio / "narration.srt").read_text(encoding="utf-8"), flags=re.S)
    same = len(srt) == len(want) and all(
        int(n) == i + 1 and abs(clock(a) - w[0]) <= T_JSON and abs(clock(b) - w[1]) <= T_JSON and text == w[2]
        for i, ((n, a, b, text), w) in enumerate(zip(srt, want)))
    rep.check(same, f"narration.srt holds the {len(want)} cues of {len(built)} scenes, numbered, each scene placed after the durations before it")
    rep.check(abs(offset - sum(len(pcm[k]) for k in built if k in pcm) / RATE) < 1e-6 or not complete,
              f"the scene WAVs joined are as long as the durations added up ({offset:.3f} s): no hole between scenes")
    return rep.passed, rep.failed


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Verify a narration build (independent of the builder).")
    ap.add_argument("--audio", type=Path, default=BUILD / "audio", help="the build directory (timings.json, the WAVs, narration.srt)")
    ap.add_argument("--script", type=Path, default=HERE / "script.json")
    ap.add_argument("--reviewed", type=Path, default=HERE / "script-and-storyboard.md")
    ap.add_argument("--only", nargs="+", metavar="KEY", help="verify only these scenes")
    ap.add_argument("--voice", help="the voice that the audio must have, when it was built with narration.py --voice (default: the script's)")
    a = ap.parse_args(argv)
    absent = [str(f) for f in (a.audio / "timings.json", a.audio / "narration.srt", a.script, a.reviewed) if not f.exists()]
    if absent:
        raise SystemExit("cannot verify, these files do not exist: " + ", ".join(absent))
    passed, failed = verify(a.audio, a.script, a.reviewed, a.only, a.voice)
    print(f"\nRESULT: {passed} checks passed, {len(failed)} failed")
    for f in failed:
        print("  FAILED: " + f)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
