"""Measure rendered scenes or the assembled video against the quality bars of INTERFACES.md.

THE GATE for the film (run it before the film is shown to anyone; exit 0 means the film passed):

    tmp/explainer-venv/bin/python writing/substack/explainer-video/qa.py -q review --gate

``--gate`` holds the whole film (BUILD/out/explainer-<quality>.mp4, every scene of script.json) to every bar: the
motion warnings fail (``--strict``), a bar that could not be measured fails, narration_verify.py runs as one more
bar, and every warning fails unless ``--waive`` names it. The last lines list every waiver that was used: the
flags below, the ``# qa:`` marks, ``assemble.py --force`` and ``--allow-silent`` (from the manifest), ``--waive``.
Without ``--gate`` the tool is for work in progress: exit 0 there means only that no hard bar failed.

    tmp/explainer-venv/bin/python writing/substack/explainer-video/qa.py                            # BUILD/out/explainer-draft.mp4
    tmp/explainer-venv/bin/python writing/substack/explainer-video/qa.py --scenes S03 S04           # scene files ("all": every scene)
    tmp/explainer-venv/bin/python writing/substack/explainer-video/qa.py --video FILE --timings T.json --order timings \
        --scene-dir DIR --source old/explainer.py --text-funcs card Dial                            # any other video (v1)

The quality is draft unless ``-q`` says otherwise (the default of render.py and assemble.py too). The tool writes
BUILD/out/qa-report.md and qa-report.json (``--out-dir``, ``--name``) and evidence pictures next to them, and
exits with status 1 when a hard bar fails. The last line says PART OF THE FILM when not every scene is measured.

Hard bars (FAIL): a freeze over 2.5 s while the voice speaks; a frozen share of 30% or more of the speech time;
a cut to an empty frame; a join where the picture jumps, and ink outside the safe area on a cue frame (each
unless the scene is marked, see below); loudness outside -16 LUFS +-1; true peak above -1.5 dBTP; a hole in the
audio timestamps; a sample rate other than 48 kHz; sound that is longer or shorter than the picture by more
than one frame; a WAV that does not last its ``duration`` or does not lie next to timings.json; a scene file
that is not lossless RGB or a final file that is not H.264 yuv420p with BT.709 tags; a picture length that
differs from timings.json; a picture rendered before the narration or its code changed, rendered with another
version of a shared file than the other scenes, or with the lint overlay drawn in it; a film joined before one
of its scenes was rendered again; narration that is not built from the lines of script.json, or lines that the
reviewed script does not hold (narration.check_script); a forbidden class in a scene; a font size outside the
scale; a numeral that the post does not have; an issue of the kit's layout lint; the default film name on a
part of the film. A hard bar that cannot be measured (no lint, no render record, no fingerprint) fails when the
whole film is measured, and is a warning for a part.
Everything else is a warning (WARN) or a number for the reader (INFO). A warning is a craft rule of the
research, or a bar that could not be measured.

The freeze bars are about a picture that does not change at all, so the kit's ambient motion satisfies them.
"Meaningful motion" and "no event" (below) do not count ambient motion; they are warnings, and ``--strict`` (and
``--gate``) makes them fail.

How the picture is measured (the v1 critique's method, so the numbers compare: v1 is 75% still):
- The video is read at 15 fps and 480x270, grey. Two frames are "the same" when 0.02% or fewer of the pixels
  differ by more than 10 levels.
- Frozen: a frame that is the same as the frame before it and as the frame 0.2 s before or after it. Slow
  ambient motion (the kit's drift) is not frozen: over 0.2 s it moves enough to see.
- No event: a frame that is the same as the frame 0.53 s before or after it when ambient motion is allowed: a
  sway of up to 2 pixels (8 at 1080p) and a change of brightness of up to 5% plus 10 levels, compared on a
  slightly blurred copy (a field of small points that drift would twinkle without the blur). The kit's
  ``ambient`` and ``drift`` are "no event". The share of a spoken line that has an event is its "meaningful
  motion" (the brief asks for about 60%); a long stretch under speech with no event is a warning. The slow
  start and end of an eased animation are under the threshold: an eased fade counts for about two thirds of
  its length, an eased move for about 85%, a linear move for all of it (measured on synthetic frames).
- A freeze "while the voice speaks" is a frozen run cut to the first and the last moment of speech inside it. A
  pause between two sentences inside the run counts; silence before or after it does not.
- Ink: a pixel more than 14 levels brighter than the frame's background (the median colour, at most 48) in any
  channel. A frame with ink on less than 0.1% of its pixels is empty.
- Cue frame: the first frame after a narration line ends. The box around its solid ink (48 levels over the
  background, so the faint outer part of a glow does not count) must be inside |x| <= 6.4, |y| <= 3.4. Not on a
  cue frame where the camera is away from its rest framing (render.py records those frames): the world runs off
  the picture by design there, and the kit's lint holds text and pinned objects to the safe area.
- Join: scene N's last frame against scene N+1's first frame. The join is continuous when under 0.5% of the
  pixels change, or when the change is at most twice the change between the two frames before the join or the
  two frames after it (the first frame of a scene is already one step into its first animation). If not, it is
  a "small shift" when the two frames are the same picture within ambient motion (the pose is right, but the
  ambient motion of scene N+1 does not continue that of scene N), and a "jump" otherwise.

Marks in a scene's source (comments inside the scene class):
    # qa: bleed      ink outside the safe area is deliberate in this scene (also ``--allow-bleed KEY`` or ``KEY:LINE``)
    # qa: bleed 2 3  the same, but only on the cue frames of lines 2 and 3 (a push-in, for example)
    # qa: cut        the scene does not start on the last frame of the scene before it (also ``--allow-cut KEY``)

Overlaps between objects and the number of words on screen at one moment cannot be seen in pixels. The kit's
layout lint measures both inside the scene: render.py turns it on and copies its issues into the scene's render
record, assemble.py copies the record into the film's manifest, and this tool holds those issues against the bar
(for a scene file with no record: BUILD/logs/<quality>/<Key>.lint.json, or ``--lint-dir``). The lint marks a
deliberate bleed with ``mob.bleed_ok = True``; the pixel check of a cue frame with the camera at rest needs
``# qa: bleed`` as well.

The pacing bars (plays under 1 s, of 2 s or more) use the plays as they ran, from the render records; the source
estimate is used only for a scene with no record. The source checks know the kit: ``enter`` counts as an entrance
from nothing; ``born_from``, ``hand_over``, ``cloud.to(centers=...)`` and ``cloud.split(idx)`` as hand-overs;
``cloud.to()``, ``push_in`` and the other functions that return an animation as animation objects; and the size
names ("display" ... "fine") as their numbers. They are read from the kit when it can be imported. Absolute
placement counts only a literal point in ``move_to`` (``put(m, x, y)`` on the grid is the kit's way). The numerals
are those of on-screen strings, of ``LiveNumber(value)`` and of ``count_to(m, value)``; a number made at run time
(an f-string with a value, a computed LiveNumber or count) is reported as not checked.

Ways to a wrong film that this tool lets pass, or cannot see (the gate lists the first three when they are used):
- the waivers: ``--allow-bleed``, ``--allow-cut``, ``# qa: bleed`` / ``# qa: cut``, ``--allow-unspoken``,
  ``--whole-file``, ``--waive``, ``assemble.py --force`` and ``--allow-silent``;
- without ``--gate``: any number of warnings, and an unmeasured bar on a part of the film;
- a cue up to 2 frames late (the kit's tolerance) gives no message;
- the voice: a wrong reading with a right phoneme table (heteronyms such as "estimate", "project", "used") needs
  a listener; word times inside running speech are Kokoro's own, not checked against an alignment; an edit of
  the pronunciation table is reviewed by no tool; the synthesis cache is trusted by its key (text, voice name,
  speed, seed, Kokoro version, device), not by the model or voice file;
- the picture: a change of hue with the same brightness, a small moving point, a text scaled after it was made,
  anything between the cue frames and line starts, inputs of a scene that are not Python files (fonts, pictures,
  data files), and whether a picture is true;
- BUILD/audio/narration.srt is not the film's subtitle file after --dissolve or for a part: use BUILD/out/<stem>.srt;
- every scene join carries the silence of a tail and a lead (about 1.0 s), plus up to one frame of the grid.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import re
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from assemble import audio_stream, loudness, mixed_code, narration_tie, narration_track, stamp, wav_problems, write_wav
from render import (BUILD, DEFAULT_QUALITY, VID, _font, code_changed, cue_frame, film_stem, frame_check, in_ranges, is_lossless_rgb,
                    lint_groups, load_timings, probe, quality, record_changes, render_record, run, scene_order, select_filter, stale, table,
                    timings_digest, timings_path, x264_settings)

AFPS, AW, AH = 15, 480, 270
LEVELS, MOVING_SHARE = 10, 2e-4
BACK_STILL, BACK_EVENT = 3, 8                   # analysis frames (0.2 s, 0.53 s)
SWAY, PULSE, BLUR = 2, 0.05, 1.0                # ambient motion: pixels at 480x270 it may move, share of brightness it may change; blur sigma
INK_LEVELS, SOLID_LEVELS, BG_CEILING, EMPTY_INK = 14, 48, 48, 1e-3
MAX_FREEZE, MAX_FROZEN_SHARE, MAX_NO_EVENT, MIN_EVENT_SHARE = 2.5, 0.30, 4.0, 0.5
FRAME_W, FRAME_H, SAFE_X, SAFE_Y = 128 / 9, 8.0, 6.4, 3.4
JOIN_SAME = 0.005
UNKNOWN = "not measured"                        # a hard bar that could not be measured: FAIL for the whole film, WARN for a part
LUFS, LUFS_TOL, PEAK, RATE = -16.0, 1.0, -1.5, 48000
SCALE = {64, 44, 32, 24, 18}
MAX_WORDS, MAX_WORDS_STRING, MIN_TILES = 12, 6, 0.55
FORBIDDEN = {"Tex", "MathTex", "SingleStringMathTex", "DecimalNumber", "Integer", "Variable", "Title", "BulletedList",
             "ThreeDScene", "SpecialThreeDScene", "ThreeDCamera", "ThreeDAxes", "Surface"}
DISCOURAGED = {"RoundedRectangle", "SurroundingRectangle", "BackgroundRectangle", "Arrow", "CurvedArrow", "DoubleArrow",
               "CurvedDoubleArrow", "Indicate", "Cross", "Circumscribe", "Table", "BarChart"}
TEXT_FUNCS = {"T", "Text", "MarkupText", "Paragraph", "tex", "LiveNumber", "label", "caption", "cite", "tag"}
HUD_FUNCS = {"hud_tag", "hud_cite"}             # the kit's fixed tag and citation line: fine print, not counted as words
NO_WORDS = {"tex", "LiveNumber"}                # their first argument is a formula or a value, not words
CONTAINERS = {"LaggedStart", "LaggedStartMap", "AnimationGroup", "Succession", "timed"}
ENTRANCES = {"FadeIn", "enter"}                 # an object that comes from nothing
HANDOVERS = {"Transform", "ReplacementTransform", "TransformFromCopy", "FadeTransform", "FadeTransformPieces", "MoveToTarget",
             "Restore", "TransformMatchingShapes", "TransformMatchingTex", "ClockwiseTransform", "CounterclockwiseTransform",
             "born_from", "hand_over"}
KIT_HANDOVERS = {".to(centers)", ".split"}     # a cloud that regroups into new places; a cloud born from part of another
CONTINUOUS = {"ValueTracker", "add_updater", "always_redraw", "always", "f_always", "UpdateFromFunc", "UpdateFromAlphaFunc",
              "TracedPath", "follow", "drift", "ambient", "Runner"}
CAMERA_MOVES = {"push_in", "pull_back"}
KIT = {"functions": {"enter", "leave", "born_from", "hand_over", "draw", "count_to", "sweep_in"},      # used when the kit cannot be imported
       "methods": {"to", "appear", "run", "push_in", "pull_back"},
       "roles": {"display": 64.0, "title": 44.0, "body": 32.0, "label": 24.0, "fine": 18.0},
       "size_at": {"T": 1, "tex": 1, "LiveNumber": 4}, "defaults": {"T": 32.0, "tex": 32.0, "LiveNumber": 44.0},
       "run_times": {"enter": 1.0, "leave": 0.6, "born_from": 2.0, "hand_over": 2.0, "draw": 2.0, "count_to": 2.5, "push_in": 3.0, "pull_back": 3.0}}
FALLBACK_ANIMS = {"FadeIn", "FadeOut", "Create", "Uncreate", "Write", "Unwrite", "DrawBorderThenFill", "GrowFromCenter",
                  "GrowFromEdge", "GrowFromPoint", "GrowArrow", "SpinInFromNothing", "Rotate", "Rotating", "MoveAlongPath",
                  "ShowPassingFlash", "Flash", "FocusOn", "Wiggle", "ApplyWave", "ApplyMethod", "ApplyFunction", "ChangeDecimalToValue",
                  "ShrinkToCenter", "AddTextLetterByLetter", "Homotopy", "Wait"} | HANDOVERS | DISCOURAGED & {"Indicate", "Circumscribe"}
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9,.'%-]*")
NUMERAL = re.compile(r"\d[\d,]*(?:\.\d+)?")
POST_NUMERALS = {1440.0, 20.0, 18.5, 14.1, 6.0, 1.0, 2.0}     # BRIEF.md, fidelity rule 2: 1,440; six; 20%; 18.5%; 14.1%; one- or two-step
COUNT_FROM = {0.0}                              # a LiveNumber may start at zero and count to a numeral of the post


@dataclass
class Segment:
    key: str
    start: int            # first frame on the timeline
    frames: int
    source: Path
    offset: int           # first frame in the source file
    overlap: int = 0      # dissolve frames shared with the scene before


# --------------------------------------------------------------------------- what is measured
def timeline(args: argparse.Namespace, timings: dict) -> tuple[list[Segment], float, dict]:
    """The scenes on one time axis, the frame rate, and facts about the target."""
    q = quality(args.quality)
    order = [k for k in timings if not k.startswith("_")] if args.order == "timings" else scene_order(timings, args.script)
    if args.scenes:
        keys = order if args.scenes == ["all"] else args.scenes
        scene_dir = (args.scene_dir or BUILD / "scenes" / q.name).resolve()
        missing = [k for k in keys if not (scene_dir / f"{k}.mp4").exists() or k not in timings]
        if missing:
            raise SystemExit(f"no scene file or no timings for: {', '.join(missing)} (in {scene_dir})")
        segs, start, fps = [], 0, None
        for k in keys:
            info = probe(scene_dir / f"{k}.mp4")
            fps = fps or info["fps"]
            segs.append(Segment(k, start, info["frames"], scene_dir / f"{k}.mp4", 0))
            start += info["frames"]
        return segs, fps, {"mode": "scenes", "target": str(scene_dir), "complete": keys == order, "order": order,
                           "records": {s.key: render_record(s.source) for s in segs}, "records_from": "the render records of the scene files"}
    video = args.video.resolve() if args.video else BUILD / "out" / f"{args.stem or film_stem(q)}.mp4"
    if not video.exists():
        raise SystemExit(f"no video at {video}")
    info = probe(video)
    manifest = args.manifest or video.with_suffix(".json")
    meta = {"mode": "video", "target": str(video), "video": info, "complete": True, "order": order, "records": {}, "records_from": None,
            "film_stem": film_stem(q)}
    if manifest.exists():
        m = json.loads(manifest.read_text())
        segs = [Segment(s["key"], s["start_frame"], s["frames"], video, s["start_frame"], s.get("overlap_frames", 0)) for s in m["scenes"]]
        copied = all("record" in s for s in m["scenes"])           # a manifest of an older assemble.py has no copies
        meta |= {"manifest": str(manifest), "sources": [s["source"] for s in m["scenes"]], "complete": [s.key for s in segs] == order,
                 "digests": {s["key"]: s.get("timings") for s in m["scenes"]}, "made_at": m.get("quality"),
                 "film_stem": film_stem(quality(m.get("quality") or q.name)),
                 "lossless": {s["key"]: s["lossless"] for s in m["scenes"] if "lossless" in s},
                 "records": {s["key"]: s.get("record") for s in m["scenes"]} if copied else {},
                 "records_from": "the manifest (copies of the render records made when the film was joined)" if copied else None,
                 "waivers": m.get("waivers", [f"--force: {n[8:]}" for n in m.get("notes", []) if n.startswith("forced: ")])}
        return segs, info["fps"], meta
    segs, start, estimated = [], 0, False
    for k in order:
        f = (args.scene_dir / f"{k}.mp4") if args.scene_dir else None
        if f and f.exists():
            n = probe(f)["frames"]
        else:
            n, estimated = timings[k].get("frames", {}).get(str(int(info["fps"]))) or round(timings[k]["duration"] * info["fps"]), True
        segs.append(Segment(k, start, n, video, start))
        start += n
    meta["scene_starts"] = "from timings.json (estimates)" if estimated else f"from the scene files in {args.scene_dir}"
    if start != info["frames"]:
        meta["scene_starts"] += f"; the scenes add up to {start} frames but the video has {info['frames']}"
        segs[-1].frames += info["frames"] - start
    return segs, info["fps"], meta


def ambient_range(grey: np.ndarray, sway: int, blur: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A soft copy of a grey frame, and the brightest and the darkest value that ambient motion may give each pixel.

    The blur keeps the light of a small point when the point moves by part of a pixel (without it a field of
    drifting points twinkles and every frame looks like an event).
    """
    from scipy.ndimage import gaussian_filter, maximum_filter, minimum_filter
    soft = gaussian_filter(grey.astype(np.float32), blur)
    size = 2 * sway + 1
    return soft, maximum_filter(soft, size) * (1 + PULSE) + LEVELS, minimum_filter(soft, size) * (1 - PULSE) - LEVELS


def beyond_ambient(a: tuple, b: tuple) -> float:
    """Share of the pixels where two frames (as from ``ambient_range``) differ by more than a sway and a pulse can explain."""
    return float(((a[0] > b[1]) | (a[0] < b[2]) | (b[0] > a[1]) | (b[0] < a[2])).mean())


def scan(source: Path, history: list | None = None) -> tuple[dict, list]:
    """Per analysis frame: the share of pixels that differ from the frame before (``d1``), from the frame 0.2 s
    before (``d3``), from the frame 0.53 s before when ambient motion is allowed (``ev``), and the share of ink."""
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(source), "-an", "-vf", f"fps={AFPS},scale={AW}:{AH}:flags=area,format=gray",
                             "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    history = list(history or [])                      # (frame, its ``ambient_range``) of the last frames
    out = {"d1": [], "d3": [], "ev": [], "ink": []}
    while True:
        buf = proc.stdout.read(AW * AH)
        if len(buf) < AW * AH:
            break
        f = np.frombuffer(buf, dtype=np.uint8).reshape(AH, AW).astype(np.int16)
        soft = ambient_range(f, SWAY, BLUR)
        for name, back in (("d1", 1), ("d3", BACK_STILL)):
            out[name].append(float((np.abs(f - history[-back][0]) > LEVELS).mean()) if len(history) >= back else np.nan)
        out["ev"].append(beyond_ambient(soft, history[-BACK_EVENT][1]) if len(history) >= BACK_EVENT else np.nan)
        out["ink"].append(float((f > min(float(np.median(f)), BG_CEILING) + INK_LEVELS).mean()))
        history = (history + [(f, soft)])[-BACK_EVENT:]
    if proc.wait() != 0:
        raise SystemExit(f"ffmpeg could not decode {source}")
    return {k: np.array(v) for k, v in out.items()}, history


def iter_frames(source: Path, indices: list[int], width: int):
    """Yield (index, RGB array) for these frames of one file, in order, in one decoding pass."""
    order = sorted(set(indices))
    if not order:
        return
    info = probe(source)
    w = min(width, info["width"])
    h = round(info["height"] * w / info["width"] / 2) * 2
    vf = f"{select_filter(order)},scale={w}:{h}:flags=area"
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(source), "-an", "-vf", vf, "-fps_mode", "passthrough", "-f", "rawvideo",
                             "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    for i in order:
        buf = proc.stdout.read(w * h * 3)
        if len(buf) < w * h * 3:
            raise SystemExit(f"{source.name}: no frame {i}")
        yield i, np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 3)
    proc.stdout.close()
    proc.wait()


# --------------------------------------------------------------------------- motion
def runs(flags: np.ndarray) -> list[tuple[int, int]]:
    """(first, last) index of each run of True."""
    edges = np.flatnonzero(np.diff(np.concatenate([[0], flags.astype(np.int8), [0]])))
    return [(int(a), int(b) - 1) for a, b in zip(edges[::2], edges[1::2])]


def same_as_neighbour(d: np.ndarray, back: int) -> np.ndarray:
    """True where a frame is the same as the frame ``back`` steps before it or after it (``d``: change against ``back`` steps before)."""
    ok = np.nan_to_num(d, nan=1.0) <= MOVING_SHARE
    return ok | np.concatenate([ok[back:], np.zeros(min(back, len(ok)), dtype=bool)])


def clipped_runs(flags: np.ndarray, t: np.ndarray, speech: list[tuple]) -> tuple[list[tuple[float, float]], list[dict]]:
    """Runs of True as (start, end) seconds, and each run cut to the first and last moment of speech inside it."""
    dt = 1 / AFPS
    spans = [(float(t[a] - dt), float(t[b])) for a, b in runs(flags)]
    cut = []
    for a, b in spans:
        inside = [x for x in speech if x[0] < b and x[1] > a]
        if inside:
            first, last = max(a, min(x[0] for x in inside)), min(b, max(x[1] for x in inside))
            cut.append({"start": round(first, 2), "end": round(last, 2), "seconds": round(last - first, 2),
                        "lines": [f"{x[2]}:{x[3]}" for x in inside], "text": " / ".join(x[4] for x in inside)[:160]})
    return spans, cut


def motion(segs: list[Segment], fps: float, timings: dict) -> dict:
    times, parts, history, scanned = [], {"d1": [], "d3": [], "ev": [], "ink": []}, None, {}
    for s in segs:
        if s.source not in scanned:
            scanned[s.source], history = scan(s.source, history if s.offset == 0 else None)
        j = np.arange(len(scanned[s.source]["d1"]))
        mine = (j / AFPS >= s.offset / fps - 1e-9) & (j / AFPS < (s.offset + s.frames) / fps - 1e-9)
        times.append(s.start / fps + j[mine] / AFPS - s.offset / fps)
        for k in parts:
            parts[k].append(scanned[s.source][k][mine])
    t, (d1, d3, ev, ink) = np.concatenate(times), (np.concatenate(parts[k]) for k in ("d1", "d3", "ev", "ink"))
    still_v1 = np.nan_to_num(d1, nan=1.0) <= MOVING_SHARE         # the v1 critique's test: the same as the frame before
    still = still_v1 & same_as_neighbour(d3, BACK_STILL)
    quiet = still | same_as_neighbour(ev, BACK_EVENT)          # no event: frozen, or only ambient motion
    dt = 1 / AFPS
    speech = [(s.start / fps + x["start"], s.start / fps + x["end"], s.key, i, x.get("text", ""))
              for s in segs for i, x in enumerate(timings[s.key]["sentences"])]
    mid = t - dt / 2
    speaking = np.zeros(len(t), dtype=bool)
    for a, b, *_ in speech:
        speaking |= (mid >= a) & (mid < b)
    still_runs, freezes = clipped_runs(still, t, speech)
    _, quiets = clipped_runs(quiet, t, speech)
    per_line = []
    for a, b, key, i, text in speech:
        sel = (mid >= a) & (mid < b)
        if sel.any():
            per_line.append({"scene": key, "line": i, "seconds": round(b - a, 2), "event_share": round(float((~quiet[sel]).mean()), 3),
                             "moving_share": round(float((~still[sel]).mean()), 3), "text": text[:80]})
    scenes = []
    for s in segs:
        a, b = s.start / fps, (s.start + s.frames) / fps
        sel = (mid >= a) & (mid < b)
        fr, qu = [f for f in freezes if a <= f["start"] < b], [f for f in quiets if a <= f["start"] < b]
        mine, empty_run = ink[sel], 0
        while empty_run < len(mine) and mine[empty_run] < EMPTY_INK:
            empty_run += 1
        share = lambda flags, where: round(float(flags[where].mean()), 3) if where.any() else None
        scenes.append({"scene": s.key, "start": round(a, 3), "seconds": round(b - a, 3), "still_seconds": round(float(still[sel].sum() * dt), 2),
                       "still_share": share(still, sel), "speech_seconds": round(float((sel & speaking).sum() * dt), 2),
                       "frozen_speech_share": share(still, sel & speaking), "no_event_speech_share": share(quiet, sel & speaking),
                       "longest_freeze": max((f["seconds"] for f in fr), default=0.0),
                       "freezes_over_limit": sum(f["seconds"] > MAX_FREEZE for f in fr),
                       "longest_no_event": max((f["seconds"] for f in qu), default=0.0),
                       "empty_at_start_seconds": round(empty_run * dt, 2), "mean_ink_share": share(ink, sel) if sel.any() else None})
    lengths = [b - a for a, b in still_runs]
    return {"seconds": round(float(len(t) * dt), 2), "still_seconds": round(float(still.sum() * dt), 1),
            "still_share": round(float(still.mean()), 3), "still_share_v1_method": round(float(still_v1.mean()), 3),
            "still_seconds_v1_method": round(float(still_v1.sum() * dt), 1), "speech_seconds": round(float(speaking.sum() * dt), 1),
            "frozen_speech_share": round(float(still[speaking].mean()), 3) if speaking.any() else None,
            "no_event_share": round(float(quiet.mean()), 3),
            "no_event_speech_share": round(float(quiet[speaking].mean()), 3) if speaking.any() else None,
            "still_runs_2s": sum(x >= 2 for x in lengths), "still_runs_4s": sum(x >= 4 for x in lengths),
            "longest_still_run": round(max(lengths, default=0.0), 2),
            "longest_freeze": max((f["seconds"] for f in freezes), default=0.0),
            "freezes_over_limit": sorted((f for f in freezes if f["seconds"] > MAX_FREEZE), key=lambda f: f["start"]),
            "longest_no_event": max((f["seconds"] for f in quiets), default=0.0),
            "no_event_over_limit": sorted((f for f in quiets if f["seconds"] > MAX_NO_EVENT), key=lambda f: f["start"]),
            "median_event_share_per_line": round(statistics.median(x["event_share"] for x in per_line), 3) if per_line else None,
            "median_moving_share_per_line": round(statistics.median(x["moving_share"] for x in per_line), 3) if per_line else None,
            "lines_with_little_event": [x for x in per_line if x["event_share"] < 0.3],
            "lines": per_line, "scenes": scenes}


# --------------------------------------------------------------------------- cue frames and joins
def ink_mask(rgb: np.ndarray, levels: int = INK_LEVELS) -> np.ndarray:
    a = rgb.astype(np.int16)
    bg = np.minimum(np.median(a[::4, ::4].reshape(-1, 3), axis=0), BG_CEILING)
    return ((a - bg) > levels).any(axis=2)


def measure_frame(rgb: np.ndarray) -> dict:
    """Ink box, margins, use of the frame and safe-area overshoot of one frame.

    The box and the margins are those of solid ink (48 levels over the background): the faint outer part of a glow
    may pass the safe area, as in the kit's lint. The edge of a glyph that sits exactly on the safe area spills by
    part of a pixel, so the overshoot must be more than 1.5 pixels (and more than 2 pixels at 1080p).
    """
    mask = ink_mask(rgb)
    h, w = mask.shape
    share = float(mask.mean())
    ys, xs = np.nonzero(mask)
    if share < EMPTY_INK / 20:
        return {"empty": True, "ink_share": round(share, 5), "tiles": 0.0, "bbox_share": 0.0, "outside": {}}
    tiles = len(set((ys * 8 // h) * 12 + xs * 12 // w))
    out = {"empty": share < EMPTY_INK, "ink_share": round(share, 4), "tiles": round(tiles / 96, 3), "bbox_share": 0.0, "outside": {}}
    ys, xs = np.nonzero(ink_mask(rgb, SOLID_LEVELS))
    if not len(xs):
        return out
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    unit = w / FRAME_W                                           # pixels for one frame unit
    safe = (w / 2 - SAFE_X * unit, w / 2 + SAFE_X * unit, h / 2 - SAFE_Y * unit, h / 2 + SAFE_Y * unit)
    tol = max(2 * w / 1920, 1.5)
    over = {"left": safe[0] - x0, "right": x1 + 1 - safe[1], "top": safe[2] - y0, "bottom": y1 + 1 - safe[3]}
    return out | {"bbox": [x0, y0, x1, y1], "bbox_share": round((x1 - x0 + 1) * (y1 - y0 + 1) / (w * h), 3),
                  "margins_px_1080": {k: round(v * 1920 / w) for k, v in (("left", x0), ("right", w - 1 - x1), ("top", y0), ("bottom", h - 1 - y1))},
                  "outside": {k: round(v / unit, 3) for k, v in over.items() if v > tol}}


def evidence(rgb: np.ndarray, path: Path, m: dict | None = None, label: str = "") -> None:
    from PIL import Image, ImageDraw
    im = Image.fromarray(rgb)
    if m is not None:
        d, (w, h) = ImageDraw.Draw(im), im.size
        unit = w / FRAME_W
        d.rectangle([w / 2 - SAFE_X * unit, h / 2 - SAFE_Y * unit, w / 2 + SAFE_X * unit, h / 2 + SAFE_Y * unit], outline=(88, 196, 221), width=2)
        if "bbox" in m:
            d.rectangle(m["bbox"], outline=(255, 107, 94), width=2)
        d.text((12, 8), label, font=_font(max(14, w // 80)), fill=(255, 255, 255))
    im.thumbnail((1280, 1280))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def frames_pass(segs: list[Segment], fps: float, timings: dict, out: Path, bleed: set[str],
                away: dict[str, list] | None = None) -> tuple[list[dict], list[dict]]:
    """Measure every cue frame, and the two frames on each side of every join. ``away``: for each scene, the frame ranges
    with the camera away from its rest framing (from the render records)."""
    away = away or {}
    wanted: dict[Path, dict[int, list[tuple]]] = {}

    def want(seg: Segment, local: int, tag: tuple) -> None:
        wanted.setdefault(seg.source, {}).setdefault(seg.offset + local, []).append(tag)

    for n, s in enumerate(segs):
        for i, line in enumerate(timings[s.key]["sentences"]):
            want(s, cue_frame(line["end"], fps, s.frames), ("cue", n, i))
        after = segs[n + 1].overlap if n + 1 < len(segs) else 0
        for tag, local in (("first", s.overlap), ("first2", s.overlap + 1), ("last2", s.frames - 2 - after), ("last", s.frames - 1 - after)):
            want(s, min(max(local, 0), s.frames - 1), (tag, n))
    cues, ends = [], {}
    for source, picks in wanted.items():
        for index, rgb in iter_frames(source, list(picks), 1920):
            for tag in picks[index]:
                s = segs[tag[1]]
                if tag[0] == "cue":
                    m = measure_frame(rgb)
                    waived = s.key in bleed or f"{s.key}:{tag[2]}" in bleed
                    moved = in_ranges(away.get(s.key), index - s.offset)
                    row = {"scene": s.key, "line": tag[2], "time": round((s.start + index - s.offset) / fps, 2), **m,
                           "bleed_allowed": waived, "camera_away": moved}
                    if m["outside"]:
                        row["evidence"] = str(out / f"safe_{s.key}_line{tag[2]:02d}.png")
                        evidence(rgb, Path(row["evidence"]), m, f"{s.key} line {tag[2]}: outside the safe area {m['outside']} (frame units)"
                                 + ("; the camera is away from rest" if moved else ""))
                    cues.append(row)
                else:
                    small = rgb[::2, ::2] if rgb.shape[1] > 1000 else rgb
                    ends[(tag[0], tag[1])] = (small.copy(), measure_frame(rgb))
    cues.sort(key=lambda r: ([s.key for s in segs].index(r["scene"]), r["line"]))
    joins = []
    changed = lambda x, y: float((np.abs(x.astype(np.int16) - y.astype(np.int16)).max(axis=2) > LEVELS).mean())

    def soft(x: np.ndarray) -> tuple:
        k = x.shape[1] / AW
        return ambient_range(x.astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32), round(SWAY * k), BLUR * k)

    for n in range(1, len(segs)):
        (a, ma), (b, mb) = ends[("last", n - 1)], ends[("first", n)]
        across, before, after = changed(a, b), changed(ends[("last2", n - 1)][0], a), changed(b, ends[("first2", n)][0])
        beyond = beyond_ambient(soft(a), soft(b))
        continuous = bool(across < JOIN_SAME or across <= 2 * max(before, after))
        to_empty = bool(mb["empty"] and not ma["empty"])
        path = out / f"join_{segs[n - 1].key}_{segs[n].key}.png"
        evidence(np.concatenate([a, np.full((a.shape[0], 8, 3), 90, dtype=np.uint8), b], axis=1), path)
        joins.append({"from": segs[n - 1].key, "to": segs[n].key, "time": round(segs[n].start / fps, 3),
                      "changed_share": round(across, 4), "changed_before": round(before, 4), "changed_after": round(after, 4),
                      "changed_beyond_ambient": round(beyond, 4),
                      "last_ink_share": ma["ink_share"], "first_ink_share": mb["ink_share"], "to_empty": to_empty, "continuous": continuous,
                      "verdict": "cut to an empty frame" if to_empty else "continuous" if continuous
                      else "small shift" if beyond < JOIN_SAME else "jump",
                      "dissolve_frames": segs[n].overlap, "evidence": str(path)})
    first = ends[("first", 0)][1]
    return cues, joins + [{"opening": True, "to": segs[0].key, "first_ink_share": first["ink_share"], "to_empty": bool(first["empty"])}]


# --------------------------------------------------------------------------- sound
def sound(segs: list[Segment], fps: float, timings: dict, meta: dict, out: Path, timings_file: Path) -> dict:
    res: dict = {"wavs": []}
    for s in segs:
        wav = Path(timings[s.key].get("wav") or "")
        if wav.is_file():
            w = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                                "stream=sample_rate,channels,bits_per_sample,duration,duration_ts", "-of", "json", wav]))["streams"][0]
            rate = int(w["sample_rate"])
            samples = int(w["duration_ts"]) if str(w.get("duration_ts", "")).isdigit() else round(float(w["duration"]) * rate)
            res["wavs"].append({"scene": s.key, "sample_rate": rate, "channels": w["channels"], "bits": w.get("bits_per_sample"),
                                "seconds": round(samples / rate, 4), "pad_ms": round(1000 * (s.frames / fps - samples / rate)),
                                "problems": wav_problems(s.key, timings[s.key], timings_file, round(samples * RATE / rate))})
        else:
            res["wavs"].append({"scene": s.key, "missing": str(wav), "problems": wav_problems(s.key, timings[s.key], timings_file, None)})
    pauses = [round(b["start"] - a["end"], 3) for s in segs for a, b in zip(timings[s.key]["sentences"], timings[s.key]["sentences"][1:])]
    res["pauses"] = {"n": len(pauses), "mean": round(statistics.mean(pauses), 3) if pauses else None,
                     "sd": round(statistics.pstdev(pauses), 3) if pauses else None, "min": min(pauses, default=None), "max": max(pauses, default=None)}
    words = sum(len(x.get("words", [])) or len(WORD.findall(x.get("text", ""))) for s in segs for x in timings[s.key]["sentences"])
    res["narration_words"] = words
    if meta["mode"] == "video":
        a = audio_stream(Path(meta["target"]))
        res |= {"source": "the video's audio stream", **a, **(loudness(Path(meta["target"])) if a["present"] else {})}
        if a["present"]:
            res["audio_minus_video"] = round(a["seconds"] - meta["video"]["frames"] / meta["video"]["fps"], 3)
            res["hole_seconds"] = round(sum(h["seconds"] for h in a["holes"]), 2)
    else:
        scenes = [{"key": s.key, "start_frame": s.start, "frames": s.frames} for s in segs]
        track, notes = narration_track(scenes, timings, fps, segs[-1].start + segs[-1].frames, allow_silent=True)
        out.mkdir(parents=True, exist_ok=True)
        write_wav(out / "narration-check.wav", track)
        res |= {"source": "the scene WAVs, each padded or cut to its picture (as assemble.py does)", "present": bool(np.abs(track).max(initial=0)),
                "sample_rate": RATE, "holes": [], "notes": notes, **loudness(out / "narration-check.wav")}
        (out / "narration-check.wav").unlink()
    return res


# --------------------------------------------------------------------------- source checks
def num(node) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        v = num(node.operand)
        return None if v is None else -v
    return None


def is_point(node) -> bool:
    """A literal [x, y, z] with a number for z (x and y may be expressions); not the zero vector."""
    return (isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) == 3 and num(node.elts[2]) is not None
            and not all(num(e) == 0 for e in node.elts))


def call_name(node) -> str | None:
    f = node.func if isinstance(node, ast.Call) else None
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def placed_at_point(node: ast.Call) -> bool:
    """``move_to([x, y, z])`` or ``move_to(np.array([x, y, z]))`` with a literal point."""
    a = node.args[0] if node.args else None
    return is_point(a) or (isinstance(a, ast.Call) and call_name(a) == "array" and bool(a.args) and is_point(a.args[0]))


def literal_text(node, unchecked: list[str] | None = None) -> list[str]:
    """The on-screen strings in one argument (a string, an f-string, a sum of strings, or a list of them). A value that
    is made at run time counts as one word and as no numeral, and is added to ``unchecked``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        if unchecked is not None and any(isinstance(v, ast.FormattedValue) for v in node.values):
            unchecked.append(ast.unparse(node))
        return ["".join(v.value if isinstance(v, ast.Constant) else "N" for v in node.values)]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = literal_text(node.left, unchecked), literal_text(node.right, unchecked)
        if left and right:
            return [a + b for a in left for b in right]
        if unchecked is not None and (left or right):
            unchecked.append(ast.unparse(node))
        return left + right
    if isinstance(node, (ast.List, ast.Tuple)):
        return [t for e in node.elts for t in literal_text(e, unchecked)]
    return []


def shown_value(node: ast.Call, name: str) -> tuple[float | None, str | None]:
    """The number that ``LiveNumber(value)`` shows or ``count_to(m, value)`` counts to: (the literal, or None and the
    expression when it is made at run time). (None, None) for any other call."""
    at = {"LiveNumber": 0, "count_to": 1}.get(name)
    if at is None:
        return None, None
    v = node.args[at] if len(node.args) > at else keyword(node, "value")
    if v is None:
        return (0.0, None) if name == "LiveNumber" else (None, None)
    return (num(v), None) if num(v) is not None else (None, f"{name}({ast.unparse(v)})")


def animation_names() -> set[str]:
    """Names of Manim's animation classes, and of the kit's when the kit can be imported."""
    try:
        import manim
        from manim.animation.animation import Animation
    except Exception:
        return set(FALLBACK_ANIMS)
    names = {n for n in dir(manim) if isinstance(getattr(manim, n), type) and issubclass(getattr(manim, n), Animation)} | HANDOVERS
    for module in ("kit.fx", "kit.motion"):
        try:
            mod = __import__(module, fromlist=["x"])
            names |= {n for n, v in vars(mod).items() if isinstance(v, type) and issubclass(v, Animation)}
        except Exception:
            pass
    return names


def kit_names() -> dict:
    """What the kit gives a scene, read from the kit itself: the functions and the methods that return an animation
    (by their return annotation), the named font sizes, and where each text function takes its size."""
    out = {k: (set(v) if isinstance(v, set) else dict(v)) for k, v in KIT.items()} | {"read_from_kit": False}
    try:
        import importlib
        import inspect
        from manim.animation.animation import Animation
        mods = [importlib.import_module(f"kit.{m}") for m in ("theme", "fx", "motion", "type", "scene")]
    except Exception:
        return out
    out |= {"functions": set(), "methods": set(), "run_times": {}, "read_from_kit": True}

    def gives_animation(f, scope: dict) -> bool:
        cls = scope.get(str(getattr(f, "__annotations__", {}).get("return", "")).strip("\"' "))
        if not (isinstance(cls, type) and issubclass(cls, Animation) and cls.__name__ not in CONTAINERS):
            return False
        d = inspect.signature(f).parameters.get("run_time")
        if d is not None and isinstance(d.default, (int, float)):
            out["run_times"][f.__name__] = float(d.default)
        return True

    for mod in mods:
        if isinstance(vars(mod).get("SCALE"), dict):
            out["roles"] = {k: float(v) for k, v in vars(mod)["SCALE"].items()}
        for name, v in vars(mod).items():
            if getattr(v, "__module__", None) != mod.__name__:
                continue
            if inspect.isfunction(v) and gives_animation(v, vars(mod)):
                out["functions"].add(name)
            elif inspect.isclass(v):
                out["methods"] |= {m for m, g in vars(v).items() if inspect.isfunction(g) and not m.startswith("_") and gives_animation(g, vars(mod))}
            if name in TEXT_FUNCS and callable(v):
                params = list(inspect.signature(v).parameters.values())
                at = next((i for i, p in enumerate(params) if p.name == "size"), None)
                if at is not None:
                    d = params[at].default
                    d = out["roles"].get(d) if isinstance(d, str) else d
                    out["size_at"][name] = at
                    out["defaults"] |= {name: float(d)} if isinstance(d, (int, float)) else {}
    return out


def keyword(node: ast.Call, name: str):
    return next((k.value for k in node.keywords if k.arg == name), None)


def play_seconds(node: ast.Call, kit: dict) -> float | None:
    """The length of one play() as far as its literals tell: its ``run_time``, else the longest of its animations
    (their ``run_time`` or the default of their class or kit function). None when a time is not a literal."""
    rt = keyword(node, "run_time")
    if rt is not None:
        return num(rt)
    longest = 0.0
    for a in node.args:
        if isinstance(a, ast.Call) and call_name(a) in CONTAINERS:
            t = play_seconds(a, kit)
        elif isinstance(a, ast.Call) and keyword(a, "run_time") is not None:
            t = num(keyword(a, "run_time"))
        else:
            t = kit["run_times"].get(call_name(a), 1.0) if isinstance(a, ast.Call) else 1.0
        if t is None:
            return None
        longest = max(longest, t)
    return longest or 1.0


def scene_stats(nodes: list[ast.AST], anims: set[str], text_funcs: set[str], kit: dict, narration: str) -> dict:
    plays, run_times, timed, waits = 0, [], 0, 0
    objects: dict[str, int] = {}
    coords, move_to_coords, put_coords, sizes, strings, hud = 0, 0, 0, [], [], []
    forbidden, discouraged, continuous, camera, values, unchecked = set(), {}, 0, 0, [], []
    roles, size_at, defaults = kit["roles"], kit["size_at"], kit["defaults"]
    size_of = lambda n: roles.get(n.value) if isinstance(n, ast.Constant) and isinstance(n.value, str) else num(n)
    for root in nodes:
        for node in ast.walk(root):
            name = call_name(node)
            if isinstance(node, ast.ClassDef):
                forbidden |= {b.id if isinstance(b, ast.Name) else getattr(b, "attr", "") for b in node.bases} & FORBIDDEN
            if isinstance(node, ast.Attribute):
                if node.attr == "animate":
                    objects[".animate"] = objects.get(".animate", 0) + 1
                if node.attr == "frame" and (isinstance(node.value, ast.Attribute) and node.value.attr == "camera"
                                             or isinstance(node.value, ast.Name) and node.value.id == "self"):
                    camera += 1
            coords += is_point(node)
            if name is None:
                continue
            method = isinstance(node.func, ast.Attribute)
            if name in ("play", "play_until"):
                plays += 1
                seconds = None if name == "play_until" else play_seconds(node, kit)
                if seconds is None:
                    timed += 1
                else:
                    run_times.append(seconds)
            waits += name == "wait"
            first = node.args[0] if node.args else None
            if method and name == "to" and (keyword(node, "centers") is not None or first is not None and num(first) is None
                                            and not (isinstance(first, ast.Constant) and first.value is None)):
                objects[".to(centers)"] = objects.get(".to(centers)", 0) + 1
            elif method and name == "split" and len(node.args) == 1 and not node.keywords and not isinstance(first, ast.Constant):
                objects[".split"] = objects.get(".split", 0) + 1
            elif (name in anims or name in kit["functions"]) and name not in CONTAINERS:
                objects[name] = objects.get(name, 0) + 1
            elif method and name in kit["methods"]:
                objects["." + name] = objects.get("." + name, 0) + 1
            if name in FORBIDDEN:
                forbidden.add(name)
            if name in DISCOURAGED:
                discouraged[name] = discouraged.get(name, 0) + 1
            continuous += name in CONTINUOUS
            camera += method and name in CAMERA_MOVES
            move_to_coords += name == "move_to" and placed_at_point(node)
            if name == "put" and len(node.args) >= 3 and num(node.args[1]) is not None and num(node.args[2]) is not None:
                put_coords += 1
            for k in node.keywords:
                if k.arg == "font_size" and num(k.value) is not None:
                    sizes.append(num(k.value))
            if name in HUD_FUNCS:
                sizes.append(roles.get("fine", 18.0))
                hud += literal_text(node.args[0]) if node.args else []
            value, made = shown_value(node, name)
            if value is not None:
                values.append((name, value))
            elif made:
                unchecked.append(made)
            if name in text_funcs:
                size, at = keyword(node, "size"), size_at.get(name)
                if size is None and at is not None and len(node.args) > at and not any(isinstance(a, ast.Starred) for a in node.args[:at + 1]):
                    size = node.args[at]
                if size is not None and size_of(size) is not None:
                    sizes.append(size_of(size))
                elif size is None and name in defaults:
                    sizes.append(defaults[name])
                if node.args and name not in NO_WORDS:
                    strings += literal_text(node.args[0], unchecked)
                if name == "LiveNumber":
                    strings += [t for k in ("prefix", "unit") if keyword(node, k) is not None for t in literal_text(keyword(node, k), unchecked)]
    said = " " + " ".join(re.sub(r"[^a-z0-9 ]", "", narration.lower().replace("-", " ")).split()) + " "
    texts, cites, verbatim, numerals = [], list(hud), [], []
    for s in strings:
        s = re.sub(r"<[^>]+>", "", s)                                # Pango markup is not on screen
        if re.search(r"arxiv|\b\d{4}\.\d{4,5}\b", s, flags=re.I):
            cites.append(s)
            continue
        numerals += [x for x in NUMERAL.findall(s) if float(x.replace(",", "")) not in POST_NUMERALS]
        n = len(WORD.findall(s.replace("\n", " ")))
        if n:
            texts.append({"text": s.replace("\n", " / "), "words": n})
            flat = " ".join(re.sub(r"[^a-z0-9 ]", "", s.lower().replace("\n", " ").replace("-", " ")).split())
            if n >= 4 and f" {flat} " in said:
                verbatim.append(s.replace("\n", " / "))
    numerals += [f"{v:g} ({n})" for n, v in values if v not in POST_NUMERALS and not (n == "LiveNumber" and v in COUNT_FROM)]
    total = sum(objects.values())
    handovers = sum(v for k, v in objects.items() if k in HANDOVERS or k in KIT_HANDOVERS)
    known = len(run_times)
    entrances = sum(v for k, v in objects.items() if k in ENTRANCES)
    scale = set(roles.values()) or SCALE
    return {"plays": plays, "plays_timed_by_narration": timed, "plays_with_fixed_time": known,
            "plays_under_1s": sum(r < 1 for r in run_times), "plays_2s_or_more": sum(r >= 2 for r in run_times),
            "share_under_1s": round(sum(r < 1 for r in run_times) / known, 3) if known else None,
            "share_2s_or_more": round(sum(r >= 2 for r in run_times) / known, 3) if known else None,
            "waits": waits, "animation_objects": total, "animations": dict(sorted(objects.items(), key=lambda kv: -kv[1])),
            "fade_in": entrances, "fade_in_share": round(entrances / total, 3) if total else None,
            "handovers": handovers, "handover_share": round(handovers / total, 3) if total else None,
            "animate_share": round(objects.get(".animate", 0) / total, 3) if total else None,
            "literal_points": coords, "move_to_coordinates": move_to_coords, "put_coordinates": put_coords,
            "font_sizes": sorted(set(sizes)), "font_sizes_off_scale": sorted({s for s in sizes if s not in scale}),
            "strings": len(texts), "words": sum(t["words"] for t in texts), "longest_string_words": max((t["words"] for t in texts), default=0),
            "long_strings": [t["text"] for t in texts if t["words"] > MAX_WORDS_STRING], "spoken_word_for_word": verbatim,
            "other_numerals": sorted(set(numerals)), "numerals_not_checked": sorted(set(unchecked)), "citations": cites, "forbidden": sorted(forbidden), "discouraged": discouraged, "continuous_motion_calls": continuous,
            "camera_frame_uses": camera}


def source_checks(files: list[Path], keys: list[str], timings: dict, text_funcs: set[str]) -> dict:
    """Static counts for each scene class, with the helpers that the scene uses (top-level functions and classes of these files)."""
    anims, kit = animation_names(), kit_names()
    out = {"files": [str(f) for f in files], "scenes": {}, "marks": {"bleed": [], "cut": []}, "twice": [],
           "kit": "read from the kit" if kit["read_from_kit"] else "the kit could not be imported: its names are the built-in list"}
    trees = []
    for f in files:
        try:
            trees.append((f, f.read_text(encoding="utf-8"), ast.parse(f.read_text(encoding="utf-8"))))
        except SyntaxError as e:
            raise SystemExit(f"{f} does not parse: {e}")
    shared: dict[str, ast.AST] = {}
    for _, _, tree in trees:
        shared |= {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name not in keys and n.name not in shared}
    for name, n in shared.items():                      # a text helper of the scene files: where it takes its size, and its default
        if isinstance(n, ast.FunctionDef) and name in text_funcs:
            a = n.args
            names = [x.arg for x in a.args]
            pairs = list(zip(names[len(names) - len(a.defaults):], a.defaults)) + \
                [(x.arg, d) for x, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None]
            kit["defaults"] |= {name: num(d) for arg, d in pairs if arg == "size" and num(d) is not None}
            kit["size_at"] |= {name: names.index("size")} if "size" in names else {}
    for f, text, tree in trees:
        top = shared | {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        scenes = {name: n for name, n in top.items() if isinstance(n, ast.ClassDef) and name in keys and n in tree.body}
        out["twice"] += [f"{name} (also in {f.name}, not used)" for name in scenes if name in out["scenes"]]
        scenes = {name: n for name, n in scenes.items() if name not in out["scenes"]}
        for key, node in scenes.items():
            used, todo = [node], [node]
            while todo:
                for n in ast.walk(todo.pop()):
                    ref = n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) \
                        and n.value.id != "self" else None
                    if ref in top and ref not in keys and top[ref] not in used:
                        used.append(top[ref])
                        todo.append(top[ref])
            narration = " ".join(x.get("text", "") for x in timings.get(key, {}).get("sentences", []))
            out["scenes"][key] = {"file": str(f), **scene_stats(used, anims, text_funcs, kit, narration)}
            segment = ast.get_source_segment(text, node) or ""
            if re.search(r"#\s*qa:\s*cut\b", segment):
                out["marks"]["cut"].append(key)
            for m in re.finditer(r"#\s*qa:\s*bleed\b[ \t]*((?:\d+[ \t,]*)*)", segment):
                out["marks"]["bleed"] += [f"{key}:{int(n)}" for n in re.findall(r"\d+", m.group(1))] or [key]
    out["scenes"] = {k: out["scenes"][k] for k in keys if k in out["scenes"]}
    out["missing"] = [k for k in keys if k not in out["scenes"]]
    out["scale"] = sorted(set(kit["roles"].values()), reverse=True)
    s = list(out["scenes"].values())
    if s:
        total = lambda name: sum(x[name] for x in s)
        share = lambda part, whole: round(total(part) / total(whole), 3) if total(whole) else None
        out["total"] = {"plays": total("plays"), "plays_with_fixed_time": total("plays_with_fixed_time"),
                        "plays_timed_by_narration": total("plays_timed_by_narration"),
                        "share_under_1s": share("plays_under_1s", "plays_with_fixed_time"),
                        "share_2s_or_more": share("plays_2s_or_more", "plays_with_fixed_time"),
                        "animation_objects": total("animation_objects"), "fade_in": total("fade_in"), "handovers": total("handovers"),
                        "fade_in_share": share("fade_in", "animation_objects"), "handover_share": share("handovers", "animation_objects"),
                        "literal_points": total("literal_points"), "move_to_coordinates": total("move_to_coordinates"),
                        "font_sizes": sorted({z for x in s for z in x["font_sizes"]}), "words": total("words"), "strings": total("strings"),
                        "median_words_per_scene": statistics.median(x["words"] for x in s)}
    return out


def code_state(segs: list[Segment], meta: dict, src: dict | None) -> dict:
    """Is each picture as new as its code? From the code hashes of the render records (the manifest's copies for a
    film): the files that changed since the render, and the files that the scenes were rendered with in two versions.
    For a record with no hash, the old test: the render started before the file that holds the scene class changed."""
    records, out = meta["records"], {"changed": {}, "unknown": [], "older": []}
    for s in segs:
        changed = code_changed(records.get(s.key))
        if changed:
            out["changed"][s.key] = changed
        elif changed is None:
            out["unknown"].append(s.key)
    out["mixed"] = mixed_code({k: records.get(k) for k in [s.key for s in segs]})
    files = {s.key: s.source for s in segs} if meta["mode"] == "scenes" else {Path(f).stem: Path(f) for f in meta.get("sources", [])}
    for key in out["unknown"]:
        record, v = records.get(key) or (render_record(files[key]) if key in files else None), (src or {}).get("scenes", {}).get(key)
        if record and v and record.get("rendered_at") and Path(v["file"]).stat().st_mtime > record["rendered_at"]:
            out["older"].append(key)
    return out


def joined_state(segs: list[Segment], meta: dict) -> dict:
    """Was the film joined from the scene files that exist now? Each scene's render record today against the copy in
    the manifest. A scene file that is gone is not a failure: the manifest's copy describes the film."""
    out = {"changed": {}, "gone": [], "unknown": []}
    if meta["mode"] != "video":
        return out
    sources = {Path(f).stem: Path(f) for f in meta.get("sources", [])}
    for s in segs:
        joined = meta["records"].get(s.key)
        now = render_record(sources[s.key]) if s.key in sources and sources[s.key].exists() else None
        if joined is None:
            out["unknown"].append(s.key)
        elif now is None:
            out["gone"].append(s.key)
        elif record_changes(joined, now):
            out["changed"][s.key] = record_changes(joined, now)
    return out


def lint_state(keys: list[str], meta: dict, folder: Path) -> dict:
    """The kit's layout lint of each scene: from its render record (the manifest's copy for a film); for a scene with
    no record, or a record of an older render.py, from <Key>.lint.json in ``folder``."""
    out = {"dir": str(folder), "from": meta["records_from"], "scenes": {}, "not_linted": [], "from_files": []}
    for k in keys:
        record = meta["records"].get(k) or {}
        if "lint_issues" in record:
            if record.get("lint") is None or record["lint_issues"] is None:
                out["not_linted"].append(k)
            else:
                out["scenes"][k] = record["lint_issues"]
            continue
        f = folder / f"{k}.lint.json"
        if not f.is_file():
            out["not_linted"].append(k)
            continue
        out["scenes"][k] = lint_groups(json.loads(f.read_text()))
        out["from_files"].append(k)
    return out


def played(meta: dict, keys: list[str]) -> dict | None:
    """The plays as they ran (from the render records; waits left out): how many, and how many under 1 s or of 2 s or more."""
    runs = [p["seconds"] for k in keys for p in (meta["records"].get(k) or {}).get("plays") or [] if set(p["anims"]) - {"Wait"}]
    have = [k for k in keys if (meta["records"].get(k) or {}).get("plays") is not None]
    if not have:
        return None
    return {"plays": len(runs), "scenes": len(have), "of": len(keys), "under_1s": sum(r < 1 for r in runs),
            "2s_or_more": sum(r >= 2 - 1e-6 for r in runs), "median": round(statistics.median(runs), 2) if runs else None}


def script_state(timings: dict, keys: list[str], script: Path, reviewed: Path, whole: bool, review_flags: dict) -> dict:
    """Is the narration built from script.json as it is now, and is every spoken line in the reviewed script?"""
    problems, unknown = narration_tie(timings, keys, script, whole)
    out = {"tie": {"problems": problems, "unknown": unknown, "script": str(script)}, "review": {"problems": [], "unknown": "", "note": ""}}
    try:
        import narration
        scenes = narration.load_script(script)[1]
        markdown = reviewed.read_text(encoding="utf-8")
    except SystemExit as e:
        out["review"]["unknown"] = f"{script} does not load ({str(e).splitlines()[0] if str(e) else 'no reason given'})"
        return out
    except OSError as e:
        out["review"]["unknown"] = f"the reviewed script {reviewed} does not read ({e.strerror})"
        return out
    except Exception as e:
        out["review"]["unknown"] = f"narration.py does not import ({type(e).__name__}: {e})"
        return out
    takes = inspect.signature(narration.check_script).parameters
    found, notes = narration.check_script(scenes, markdown, **{k: v for k, v in review_flags.items() if k in takes})
    out["review"] |= {"problems": [p.splitlines()[0] for p in found], "note": f"{notes[0]} ({reviewed.name})" if notes else reviewed.name}
    return out


def verify_narration(timings_file: Path, script: Path, reviewed: Path, out: Path) -> dict:
    """Run narration_verify.py on the narration build that timings_file belongs to; its output goes to ``out``."""
    if timings_file.name != "timings.json":
        return {"ok": UNKNOWN, "value": f"not run: narration_verify.py reads {timings_file.parent / 'timings.json'}, not {timings_file.name}"}
    p = subprocess.run([sys.executable, str(VID / "narration_verify.py"), "--audio", str(timings_file.parent), "--script", str(script),
                        "--reviewed", str(reviewed)], capture_output=True, text=True, cwd=VID.parents[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(p.stdout + p.stderr, encoding="utf-8")
    failed = [x.strip() for x in p.stdout.splitlines() if x.strip().startswith("FAIL")]
    return {"ok": p.returncode == 0, "value": f"exit {p.returncode}" + (f", {len(failed)} checks failed, first: {failed[0][5:][:120]}" if failed else "")
            + f" (output: {out.name})"}


# --------------------------------------------------------------------------- bars and report
def build_bars(meta: dict, mo: dict, cues: list[dict], joins: list[dict], snd: dict, src: dict | None, fmt: dict, lint: dict,
               strict: bool = False, gate: bool = False) -> list[dict]:
    bars, must, strict = [], meta["complete"] or gate, strict or gate

    def bar(name: str, value: str, limit: str, ok, hard: bool = True) -> None:
        status = ("FAIL" if must and hard else "WARN") if ok is UNKNOWN else "INFO" if ok is None else "PASS" if ok else "FAIL" if hard else "WARN"
        bars.append({"bar": name, "measured": value, "limit": limit, "status": status})

    bar("Longest freeze while the voice speaks", f"{mo['longest_freeze']:.2f} s ({len(mo['freezes_over_limit'])} over the limit)",
        f"<= {MAX_FREEZE} s", mo["longest_freeze"] <= MAX_FREEZE)
    fs = mo["frozen_speech_share"]
    bar("Frozen share of the speech time", "no speech" if fs is None else f"{100 * fs:.0f}%", f"< {100 * MAX_FROZEN_SHARE:.0f}%",
        None if fs is None else fs < MAX_FROZEN_SHARE)
    bar("Still share of the running time", f"{100 * mo['still_share']:.0f}% ({mo['still_seconds']} s of {mo['seconds']} s); by the v1 critique's "
        f"method {100 * mo['still_share_v1_method']:.0f}% ({mo['still_seconds_v1_method']} s)", "v1: 75% by the critique's method",
        mo["still_share"] < MAX_FROZEN_SHARE, hard=False)
    bar("Meaningful motion inside a spoken line (median)", f"{100 * (mo['median_event_share_per_line'] or 0):.0f}% of the line "
        f"(any motion, ambient too: {100 * (mo['median_moving_share_per_line'] or 0):.0f}%); lines under 30%: {len(mo['lines_with_little_event'])}",
        "about 60% (v1: 20%)", (mo["median_event_share_per_line"] or 0) >= MIN_EVENT_SHARE, hard=strict)
    bar("Longest stretch under speech with no event (frozen, or ambient motion only)",
        f"{mo['longest_no_event']:.2f} s ({len(mo['no_event_over_limit'])} over {MAX_NO_EVENT:g} s)", f"<= {MAX_NO_EVENT:g} s", not mo["no_event_over_limit"], hard=strict)
    cuts, opening = [j for j in joins if not j.get("opening")], joins[-1]
    empty = [j for j in cuts if j["to_empty"]]
    film_start = bool(meta["order"]) and opening["to"] == meta["order"][0]
    alone = [opening["to"]] if opening["to_empty"] and not film_start else []      # measured without the scene before it
    bar("Cuts to an empty frame", f"{len(empty)} of {len(cuts)} joins" + (": " + ", ".join(j["to"] for j in empty) if empty else "")
        + (f"; {alone[0]} starts on an empty frame and is not the first scene of the film" if alone else ""), "0", not empty and not alone)
    jumps = [j for j in cuts if j["verdict"] in ("jump", "cut to an empty frame") and j["to"] not in fmt["cut_allowed"]]
    bar("Joins where the picture jumps", f"{len(jumps)} of {len(cuts)}" + (": " + ", ".join(j["to"] for j in jumps) if jumps else ""),
        "0 unless the storyboard says so (# qa: cut)", not jumps)
    shifts = [j for j in cuts if j["verdict"] == "small shift" and j["to"] not in fmt["cut_allowed"]]
    bar("Joins where the same picture shifts by a few pixels", f"{len(shifts)} of {len(cuts)}" + (": " + ", ".join(j["to"] for j in shifts) if shifts else ""),
        "0 (the ambient motion of the new scene must continue the old one)", not shifts, hard=False)
    bar("Opening frame", "empty" if opening["to_empty"] else f"ink on {100 * opening['first_ink_share']:.1f}% of the pixels", "-", None)
    out = [c for c in cues if c["outside"] and not c["bleed_allowed"] and not c.get("camera_away")]
    allowed = [c for c in cues if c["outside"] and c["bleed_allowed"] and not c.get("camera_away")]
    moving = [c for c in cues if c["outside"] and c.get("camera_away")]
    worst = max((max(c["outside"].values()) for c in out), default=0)
    bar("Cue frames with ink outside the safe area", f"{len(out)} of {len(cues)}" + (f" (worst {worst:.2f} units)" if out else "")
        + (f"; {len(allowed)} marked as bleed" if allowed else "")
        + (f"; {len(moving)} with the camera away from rest, not held (the kit's lint holds text and pinned objects)" if moving else ""), "0", not out)
    if cues:
        tiles = statistics.mean(c["tiles"] for c in cues)
        bar("Use of the frame on cue frames", f"mean {100 * tiles:.0f}% of 96 tiles; median ink {100 * statistics.median(c['ink_share'] for c in cues):.1f}%",
            f">= {100 * MIN_TILES:.0f}% of the tiles", tiles >= MIN_TILES, hard=False)
        blank = [c for c in cues if c["empty"]]
        bar("Cue frames that are empty", f"{len(blank)} of {len(cues)}", "0", not blank, hard=False)
    if not snd.get("present"):
        bar("Sound", "no audio", "narration present", False)
    else:
        bar("Loudness", "silent" if snd["lufs"] is None else f"{snd['lufs']:.1f} LUFS", f"{LUFS:.0f} +-{LUFS_TOL:.0f} LUFS",
            snd["lufs"] is not None and abs(snd["lufs"] - LUFS) <= LUFS_TOL, hard=must)
        bar("True peak", "-" if snd["true_peak"] is None else f"{snd['true_peak']:.1f} dBTP", f"< {PEAK} dBTP",
            snd["true_peak"] is not None and snd["true_peak"] < PEAK)
        bar("Holes in the audio timestamps", f"{len(snd['holes'])}" + (f" ({snd.get('hole_seconds', 0)} s in all)" if snd["holes"] else ""), "0",
            not snd["holes"])
        rates = {snd["sample_rate"]} | {w["sample_rate"] for w in snd["wavs"] if "sample_rate" in w and meta["mode"] == "scenes"}
        bar("Sample rate", ", ".join(f"{r} Hz" for r in sorted(rates)), f"{RATE} Hz", rates == {RATE})
        if "audio_minus_video" in snd:
            bar("Sound length against picture length", f"{1000 * snd['audio_minus_video']:+.0f} ms", "within one frame",
                abs(snd["audio_minus_video"]) <= 1 / meta["video"]["fps"] + 1e-6)
    off = [p for w in snd["wavs"] for p in w.get("problems", [])]
    bar("Scene WAVs against timings.json (each lasts its duration to the sample and lies next to timings.json)",
        "; ".join(off) or f"every WAV fits ({sum('missing' not in w for w in snd['wavs'])})", "all", not off)
    missing = [w["scene"] for w in snd["wavs"] if "missing" in w]
    if missing and meta["mode"] == "scenes":
        bar("Scenes with no WAV", ", ".join(missing), "none", False)
    if snd["pauses"]["n"] > 2:
        bar("Pauses between lines", f"mean {snd['pauses']['mean']} s, standard deviation {snd['pauses']['sd']} s", "varied (v1: sd 0.03 s)",
            snd["pauses"]["sd"] > 0.1, hard=False)
    for name, value, limit, ok, hard in fmt["bars"]:
        bar(name, value, limit, ok, hard)
    name = "Layout lint of the kit (overlaps, safe area, sizes, words; at each line start and at the end)"
    found = {k: v for k, v in lint["scenes"].items() if v}
    count = lambda v: ", ".join(f"{sum(i['rule'] == r for i in v)} {r}" for r in dict.fromkeys(i["rule"] for i in v))
    unlinted = (f"not measured for {', '.join(lint['not_linted'])} (no lint in the render record: render.py --lint 0, or a scene "
                "that is not on kit.Narrated)") if lint["not_linted"] else ""
    if found:
        bar(name, f"issues: {sum(len(v) for v in found.values())} (" + "; ".join(f"{k}: {count(v)}" for k, v in found.items()) + ")"
            + (f"; {unlinted}" if unlinted else ""), "0 issues", False)
    else:
        bar(name, unlinted or f"0 issues ({len(lint['scenes'])} scenes)", "0 issues", UNKNOWN if unlinted else True)
    if src is None or not src["scenes"]:
        bar("Scene sources (forbidden classes, font sizes, numerals)", "not measured: no scene source found", "-", UNKNOWN)
    else:
        bad = {k: v["forbidden"] for k, v in src["scenes"].items() if v["forbidden"]}
        bar("Forbidden classes in scenes", "; ".join(f"{k}: {', '.join(v)}" for k, v in bad.items()) or "none", "none", not bad)
        off = {k: v["font_sizes_off_scale"] for k, v in src["scenes"].items() if v["font_sizes_off_scale"]}
        n_off = sorted({z for v in off.values() for z in v})
        bar("Font sizes outside the scale", f"{', '.join(f'{z:g}' for z in n_off)} (in {', '.join(off)})" if off else "none",
            "only " + " / ".join(f"{z:g}" for z in src["scale"]), not off)
        digits = {k: v["other_numerals"] for k, v in src["scenes"].items() if v["other_numerals"]}
        bar("Numerals on screen that the post does not have (strings, LiveNumber values, count_to targets)",
            "; ".join(f"{k}: {', '.join(v)}" for k, v in digits.items()) or "none",
            "only 1,440, 20%, 18.5%, 14.1% (and 6, 1, 2; a count may start at 0); citations excepted", not digits)
        made = {k: v["numerals_not_checked"] for k, v in src["scenes"].items() if v["numerals_not_checked"]}
        bar("Numbers and text made at run time (not checked against the post's numerals)",
            "; ".join(f"{k}: {', '.join(v[:4])}{' ...' if len(v) > 4 else ''}" for k, v in made.items()) or "none", "none, or checked by eye",
            not made, hard=False)
        t, ran = src["total"], fmt["played"]
        if ran and ran["plays"]:
            how = f"of {ran['plays']} plays as they ran ({ran['scenes']} of {ran['of']} scenes have a render record; waits left out)"
            bar("Plays under 1 s", f"{100 * ran['under_1s'] / ran['plays']:.0f}% {how}", "about 0% (v1: 41%)", ran["under_1s"] / ran["plays"] <= 0.10, hard=False)
            bar("Plays of 2 s or more", f"{100 * ran['2s_or_more'] / ran['plays']:.0f}% {how}; median {ran['median']} s", ">= 35% (v1: 1%)",
                ran["2s_or_more"] / ran["plays"] >= 0.35, hard=False)
        elif t["share_under_1s"] is not None:
            fixed = f"of {t['plays_with_fixed_time']} plays with a fixed time in the source ({t['plays_timed_by_narration']} more are timed by the narration; no render record)"
            bar("Plays under 1 s", f"{100 * t['share_under_1s']:.0f}% {fixed}", "about 0% (v1: 41%)", t["share_under_1s"] <= 0.10, hard=False)
            bar("Plays of 2 s or more", f"{100 * t['share_2s_or_more']:.0f}% {fixed}", ">= 35% (v1: 1%)", t["share_2s_or_more"] >= 0.35, hard=False)
        elif t["plays"]:
            bar("Plays under 1 s / of 2 s or more", f"not known: all {t['plays']} plays are timed by the narration and no render record has them", "-", None)
        if t["fade_in_share"] is not None:
            bar("Entrances from nothing (FadeIn, enter) among the animation objects",
                f"{100 * t['fade_in_share']:.0f}% ({t['fade_in']} of {t['animation_objects']})", "<= 25% (v1: 60%)", t["fade_in_share"] <= 0.25, hard=False)
            bar("Hand-overs (Transform classes, born_from, hand_over, cloud.to(centers=), cloud.split) among the animation objects",
                f"{100 * t['handover_share']:.0f}% ({t['handovers']} of {t['animation_objects']})", ">= 15% (v1: 3%)", t["handover_share"] >= 0.15, hard=False)
        many = [k for k, v in src["scenes"].items() if v["move_to_coordinates"] > 1]
        bar("Absolute placement: literal [x, y, z] points in move_to", f"{t['move_to_coordinates']} in all" + (f"; more than one in {', '.join(many)}" if many else ""),
            "at most 1 for each scene (v1: 40); put(m, x, y) on the grid is the kit's way", not many, hard=False)
        wordy = [k for k, v in src["scenes"].items() if v["words"] > MAX_WORDS]
        linted = bool(lint["scenes"]) and not lint["not_linted"]          # then the lint counted the words on screen at each line start
        bar("Words in on-screen strings", f"{t['words']} in all, median {t['median_words_per_scene']:g} for each scene"
            + (f"; over {MAX_WORDS} in {', '.join(wordy)}" if wordy else ""),
            f"<= {MAX_WORDS} on screen at one time (" + ("the layout lint counts that" if linted else "check the frames") + ")",
            None if linted else not wordy, hard=False)
        long_ = sum(len(v["long_strings"]) for v in src["scenes"].values())
        spoken = sum(len(v["spoken_word_for_word"]) for v in src["scenes"].values())
        bar("Strings over 6 words / strings that the voice says word for word", f"{long_} / {spoken}", "0 / 0", not long_ and not spoken, hard=False)
        boxes = {k: v["discouraged"] for k, v in src["scenes"].items() if v["discouraged"]}
        bar("Arrows, boxes and other discouraged classes", "; ".join(f"{k}: " + ", ".join(f"{n} x{c}" for n, c in v.items()) for k, v in boxes.items()) or "none",
            "none", not boxes, hard=False)
        dead = [k for k, v in src["scenes"].items() if not v["continuous_motion_calls"]]
        bar("Scenes with no value tracker, updater or ambient motion", ", ".join(dead) or "none", "none", not dead, hard=False)
        length = {x["scene"]: x["seconds"] for x in mo["scenes"]}
        fixed = [k for k, v in src["scenes"].items() if not v["camera_frame_uses"] and length.get(k, 0) > 20]
        bar("Scenes over 20 s with no camera move", ", ".join(fixed) or "none", "none", not fixed, hard=False)
        if src["missing"]:
            bar("Scenes with no source found (their classes, sizes and numerals are not checked)", ", ".join(src["missing"]), "none", UNKNOWN)
        if src["twice"]:
            bar("Scene classes defined twice", ", ".join(src["twice"]), "none", False, hard=False)
    return bars


def format_checks(segs: list[Segment], fps: float, timings: dict, meta: dict, prov: dict) -> dict:
    """The bars on the files and on what the film is made from (narration, script, code, render records)."""
    out, records, n = [], meta["records"], len(segs)
    if meta["mode"] == "scenes":
        lossy = [s.key for s in segs if not is_lossless_rgb(s.source)]
        out.append(("Scene files that are not lossless RGB", ", ".join(lossy) or "none", "none", not lossy, True))
    else:
        v = meta["video"]
        crf = re.search(r"crf=([\d.]+)", x264_settings(Path(meta["target"])))
        tags = "/".join(str(v[k] or "none") for k in ("color_space", "color_primaries", "color_transfer"))
        ok = (v["codec"], v["pix_fmt"], tags) == ("h264", "yuv420p", "bt709/bt709/bt709")
        out.append(("Final file", f"{v['codec']} {v['pix_fmt']}, colour tags {tags}, {v['width']}x{v['height']} at {v['fps']:g} fps"
                    + (f", x264 CRF {float(crf.group(1)):g}" if crf else ""), "h264 yuv420p, tags bt709/bt709/bt709", ok, True))
        lossless = meta.get("lossless") or {}
        sources = [Path(p) for p in meta.get("sources", []) if Path(p).exists()]
        if len(lossless) == n:
            lossy = [k for k, x in lossless.items() if not x]
            out.append(("Lossy encodes before the final one", ", ".join(lossy) or f"none (the {n} scene files were lossless RGB when the film was joined)",
                        "none", not lossy, True))
        elif sources:
            lossy = [p.stem for p in sources if not is_lossless_rgb(p)]
            out.append(("Lossy encodes before the final one", (", ".join(lossy) or f"none ({len(sources)} scene files are lossless RGB)")
                        + " (the scene files of today: the manifest does not say what they were at the join)", "none", not lossy, True))
        else:
            out.append(("Lossy encodes before the final one", "not measured (no manifest, or the scene files are gone)", "none", UNKNOWN, True))
    wrong = []
    for s in segs:
        ok, _, text = frame_check(s.frames, timings[s.key], fps)
        if not ok:
            wrong.append(f"{s.key}: {text}")
    out.append(("Picture length against timings.json", "; ".join(wrong) or f"every scene matches ({n})", "to the frame", not wrong, True))
    old, unknown = [], []
    for s in segs:
        made = meta.get("digests", {}).get(s.key)
        state = stale(s.source, timings[s.key]) if meta["mode"] == "scenes" else None if made is None else made != timings_digest(timings[s.key])
        if state is not False:
            (old if state else unknown).append(s.key)
    out.append(("Pictures rendered against these timings", f"not these: {', '.join(old)} (the narration changed after the render)" if old
                else f"not measured for {', '.join(unknown)} (no record of the render)" if unknown else f"every scene ({n})",
                "all", False if old else UNKNOWN if unknown else True, True))
    cs = prov["code"]
    if cs["changed"]:
        value, ok = "; ".join(f"{k}: {', '.join(v[:3])}{' ...' if len(v) > 3 else ''}" for k, v in cs["changed"].items()) + " changed since the render", False
    elif cs["unknown"]:
        value, ok = (f"not measured for {', '.join(cs['unknown'])} (no code hash in the render record)"
                     + (f"; by the file times, rendered before the scene's file changed: {', '.join(cs['older'])}" if cs["older"] else "")), UNKNOWN
    else:
        value, ok = f"every scene ({n})", True
    out.append(("Pictures rendered from the code of today (the scene's file, kit/, helper modules)", value, "all", ok, True))
    out.append(("One version of each shared file across the scenes", "; ".join(f"{f}: {' / '.join(g)}" for f, g in cs["mixed"].items()) or "yes",
                "one version", not cs["mixed"], True))
    over = [k for k in [s.key for s in segs] if (records.get(k) or {}).get("lint_overlay")]
    out.append(("Scenes with the lint overlay in the picture (render.py --lint 2)", ", ".join(over) or "none", "none", not over, True))
    if meta["mode"] == "video":
        js = prov["joined"]
        if js["changed"]:
            value, ok = "; ".join(f"the film was joined before {k} was last rendered ({', '.join(v)} differ)" for k, v in js["changed"].items()) + ": join it again", False
        elif js["unknown"]:
            value, ok = f"not measured for {', '.join(js['unknown'])} (the manifest holds no copy of the render record)", UNKNOWN
        else:
            value, ok = f"every scene ({n})" + (f"; the scene files of {', '.join(js['gone'])} are gone (the manifest's copies are used)" if js["gone"] else ""), True
        out.append(("Film joined from the scene files that exist now", value, "all", ok, True))
    tie, review = prov["tie"], prov["review"]
    out.append(("Narration built from the lines of script.json (narration build's _meta, built_from against the fingerprints)",
                "; ".join(tie["problems"]) or (f"not measured: {'; '.join(tie['unknown'])}" if tie["unknown"] else f"every scene ({n}) of {tie['script']}"),
                "all", False if tie["problems"] else UNKNOWN if tie["unknown"] else True, True))
    out.append(("Spoken lines in the reviewed script, word for word and in order (narration.check_script)",
                "; ".join(review["problems"][:3]) + (f" ... ({len(review['problems'])} problems)" if len(review["problems"]) > 3 else "")
                if review["problems"] else f"not measured: {review['unknown']}" if review["unknown"] else review["note"],
                "no problem", False if review["problems"] else UNKNOWN if review["unknown"] else True, True))
    if meta["mode"] == "video" and (Path(meta["target"]).stem == meta.get("film_stem") or prov["gate"]):
        missing = [k for k in meta["order"] if k not in [s.key for s in segs]]
        out.append(("The film has every scene of script.json, in order", "yes" if meta["complete"] else
                    f"no: {len(segs)} scenes ({', '.join(s.key for s in segs)}), script.json has {len(meta['order'])}"
                    + (f"; missing {', '.join(missing)}" if missing else ""), "all", meta["complete"], True))
    if prov.get("verify") is not None:
        out.append(("narration_verify.py on the narration build", prov["verify"]["value"], "exit 0", prov["verify"]["ok"], True))
    return {"bars": out, "played": prov["played"]}


def write_report(path: Path, report: dict) -> None:
    b, mo, snd, src, lint = report["bars"], report["motion"], report["sound"], report.get("source"), report["lint"]
    fails, warns = [x for x in b if x["status"] == "FAIL"], [x for x in b if x["status"] == "WARN"]
    md = [f"# QA report: {Path(report['meta']['target']).name}", "",
          f"Made {report['made']} by `qa.py`. Target: `{report['meta']['target']}` ({report['meta']['mode']}), {len(report['segments'])} scenes, "
          f"{mo['seconds']} s. Timings: `{report['timings']}`.", "",
          f"**Result: {'FAIL' if fails else 'PASS'}** ({len(fails)} hard bars failed, {len(warns)} warnings)."
          + (f" **Gate: {'PASS' if report['gate_passed'] else 'FAIL'}** (every warning fails unless it is waived)." if report["gate"] else ""), ""]
    if not report["meta"].get("complete", True):
        md += ["**PART OF THE FILM**: only part of the film is measured here, so the loudness bar and the bars that could not be measured "
               "are warnings and not failures.", ""]
    if report["waivers"]:
        md += ["Waivers used: " + "; ".join(f"`{w}`" for w in report["waivers"]) + ".", ""]
    if report["meta"].get("scene_starts"):
        md += [f"Scene starts: {report['meta']['scene_starts']}.", ""]
    md += ["## Bars", "", "| Bar | Measured | Limit | Status |", "|---|---|---|---|"]
    md += [f"| {x['bar']} | {x['measured']} | {x['limit']} | **{x['status']}** |" if x["status"] in ("FAIL", "WARN", "WAIVED")
           else f"| {x['bar']} | {x['measured']} | {x['limit']} | {x['status']} |" for x in b]
    md += ["", "## Motion", "",
           f"Still for {mo['still_seconds']} s of {mo['seconds']} s ({100 * mo['still_share']:.0f}%); by the v1 critique's method (a frame is still "
           f"when it is the same as the frame before, so a slow fade counts as still) {mo['still_seconds_v1_method']} s "
           f"({100 * mo['still_share_v1_method']:.0f}%). No event for {100 * mo['no_event_share']:.0f}% of the time. Still runs of 2 s or more: {mo['still_runs_2s']}; "
           f"of 4 s or more: {mo['still_runs_4s']}; the longest: {mo['longest_still_run']} s. Speech: {mo['speech_seconds']} s.", "",
           "| Scene | Starts | Length s | Still | Frozen under speech | Longest freeze s | Freezes over limit | No event under speech | "
           "Longest no-event s | Empty at start s |", "|---|---|---|---|---|---|---|---|---|---|"]
    pct = lambda v: "-" if v is None else f"{100 * v:.0f}%"
    md += [f"| {s['scene']} | {stamp(s['start'], '.')} | {s['seconds']:.2f} | {pct(s['still_share'])} | {pct(s['frozen_speech_share'])} | "
           f"{s['longest_freeze']:.2f} | {s['freezes_over_limit']} | {pct(s['no_event_speech_share'])} | {s['longest_no_event']:.2f} | "
           f"{s['empty_at_start_seconds']:.2f} |" for s in mo["scenes"]]
    if mo["freezes_over_limit"]:
        md += ["", f"Freezes over {MAX_FREEZE} s while the voice speaks:", "", "| From | To | Seconds | Lines | The voice says |", "|---|---|---|---|---|"]
        md += [f"| {stamp(f['start'], '.')} | {stamp(f['end'], '.')} | {f['seconds']:.2f} | {', '.join(f['lines'])} | {f['text']} |" for f in mo["freezes_over_limit"]]
    if mo["no_event_over_limit"]:
        md += ["", f"Stretches over {MAX_NO_EVENT:g} s under speech with no event (the picture is frozen or only sways):", "",
               "| From | To | Seconds | Lines | The voice says |", "|---|---|---|---|---|"]
        md += [f"| {stamp(f['start'], '.')} | {stamp(f['end'], '.')} | {f['seconds']:.2f} | {', '.join(f['lines'])} | {f['text']} |" for f in mo["no_event_over_limit"]]
    if mo["lines_with_little_event"]:
        md += ["", "Lines with meaningful motion for less than 30% of their time: "
               + ", ".join(f"{x['scene']}:{x['line']} ({100 * x['event_share']:.0f}%)" for x in mo["lines_with_little_event"]) + "."]
    md += ["", "## Joins", "", "Changed pixels across the join, between the two frames before it and the two frames after it, and across the join "
           f"when ambient motion is allowed (a sway of 8 pixels at 1080p, {100 * PULSE:.0f}% of brightness).", "",
           "| Join | At | Across | Before | After | Beyond ambient | Ink before | Ink after | Verdict | Picture |", "|---|---|---|---|---|---|---|---|---|---|"]
    for j in report["joins"]:
        if j.get("opening"):
            continue
        md.append(f"| {j['from']} to {j['to']} | {stamp(j['time'], '.')} | {100 * j['changed_share']:.2f}% | {100 * j['changed_before']:.2f}% | "
                  f"{100 * j['changed_after']:.2f}% | {100 * j['changed_beyond_ambient']:.2f}% | {100 * j['last_ink_share']:.1f}% | "
                  f"{100 * j['first_ink_share']:.1f}% | {j['verdict']} | `{Path(j['evidence']).name}` |")
    cues = report["cues"]
    md += ["", "## Cue frames", ""]
    if cues:
        side = lambda k: min((c["margins_px_1080"][k] for c in cues if "margins_px_1080" in c), default="-")
        md += [f"{len(cues)} cue frames. Smallest margins (pixels at 1080p): left {side('left')}, right {side('right')}, top {side('top')}, "
               f"bottom {side('bottom')}. The safe area needs 96 left and right, 81 top and bottom.", "",
               "| Scene | Cue frames | Mean tiles used | Mean ink | Outside the safe area |", "|---|---|---|---|---|"]
        for key in dict.fromkeys(c["scene"] for c in cues):
            mine = [c for c in cues if c["scene"] == key]
            bad = [f"line {c['line']} ({', '.join(f'{k} {v:.2f}' for k, v in c['outside'].items())})"
                   + (" camera away" if c.get("camera_away") else " allowed" if c["bleed_allowed"] else "") for c in mine if c["outside"]]
            md.append(f"| {key} | {len(mine)} | {100 * statistics.mean(c['tiles'] for c in mine):.0f}% | "
                      f"{100 * statistics.mean(c['ink_share'] for c in mine):.1f}% | {'; '.join(bad) or '-'} |")
    if any(lint["scenes"].values()):
        where = lint["from"] or f"`{lint['dir']}`"
        md += ["", "## Layout lint", "", f"From {where}" + (f" (from `{lint['dir']}` for {', '.join(lint['from_files'])})" if lint["from_files"] and lint["from"] else "")
               + ": what the kit's lint found during the render of each scene. The times are scene seconds.", "",
               "| Scene | Rule | Issue | At |", "|---|---|---|---|"]
        md += [f"| {k} | {i['rule']} | {i['msg']} | {', '.join(f'{t:g}' for t in i['times'][:6])}{' ...' if len(i['times']) > 6 else ''} |"
               for k, v in lint["scenes"].items() for i in v]
    md += ["", "## Sound", "", f"Measured on {snd.get('source', '-')}."]
    if snd.get("present"):
        md += ["", f"- Loudness {snd['lufs']} LUFS, loudness range {snd['lra']} LU, true peak {snd['true_peak']} dBTP, {snd['sample_rate']} Hz.",
               f"- Timestamp holes: {len(snd['holes'])}" + (" at " + ", ".join(f"{h['at']} s ({h['seconds']} s)" for h in snd["holes"][:20]) if snd["holes"] else "") + ".",
               f"- Narration: {snd['narration_words']} words; pauses between lines: mean {snd['pauses']['mean']} s, standard deviation {snd['pauses']['sd']} s, "
               f"from {snd['pauses']['min']} to {snd['pauses']['max']} s."]
    if src is not None and src["scenes"]:
        md += ["", "## Scene sources", "", f"Files: {', '.join('`' + f + '`' for f in src['files'])}. Names of the kit's animations and sizes: {src['kit']}.", "",
               "Plays as they ran come from the render records (waits left out); the other columns are read from the source.", "",
               "| Scene | Plays as they ran | Under 1 s | 2 s or more | Entrances from nothing | Hand-overs | Camera | move_to points | Sizes | Strings | Words | Forbidden |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        records = report["meta"].get("records") or {}
        for k, v in src["scenes"].items():
            ran = [p["seconds"] for p in (records.get(k) or {}).get("plays") or [] if set(p["anims"]) - {"Wait"}]
            plays = (f"{len(ran)} | {sum(r < 1 for r in ran)} | {sum(r >= 2 - 1e-6 for r in ran)}" if (records.get(k) or {}).get("plays") is not None
                     else f"{v['plays']} in the source | {v['plays_under_1s']} | {v['plays_2s_or_more']}")
            md.append(f"| {k} | {plays} | {v['fade_in']} of {v['animation_objects']} | {pct(v['handover_share'])} | {v['camera_frame_uses']} | "
                      f"{v['move_to_coordinates']} | {', '.join(f'{z:g}' for z in v['font_sizes']) or '-'} | {v['strings']} | {v['words']} | "
                      f"{', '.join(v['forbidden']) or '-'} |")
        notes = [f"- {k}: animation objects: {', '.join(f'{n} {c}' for n, c in v['animations'].items())}" for k, v in src["scenes"].items() if v["animations"]]
        notes += [f"- {k}: says word for word: {'; '.join(v['spoken_word_for_word'])}" for k, v in src["scenes"].items() if v["spoken_word_for_word"]]
        notes += [f"- {k}: over {MAX_WORDS_STRING} words: {'; '.join(v['long_strings'])}" for k, v in src["scenes"].items() if v["long_strings"]]
        notes += [f"- {k}: made at run time, not checked: {'; '.join(v['numerals_not_checked'])}" for k, v in src["scenes"].items() if v["numerals_not_checked"]]
        md += [""] + notes if notes else []
    md += ["", "## Limits of this report", "",
           "- A soft object that sways slowly (a glow) can count as frozen: its pixels change by less than the threshold. So can a picture in which "
           "only one small point moves (under about 10 pixels across at 1080p): a change must cover 0.02% of the frame.",
           f"- 'No event' allows a sway of 8 pixels at 1080p and a change of brightness of {100 * PULSE:.0f}% plus {LEVELS} levels. A real motion that is "
           "slower than about 15 pixels a second counts as ambient. A cut inside a scene is not an event: nothing moves before it or after it.",
           "- An eased fade counts as an event for about two thirds of its length, an eased move for about 85%.",
           "- The picture is measured in grey: a change of hue with no change of brightness is not seen.",
           "- The source checks read the scene classes and the helpers that they name in the scene files. They do not run the code: a size, a word "
           "or a run time made at run time is not seen.",
           "- Overlaps and the number of words on screen at one moment come from the kit's layout lint, at the line starts and at the end of each "
           "scene only. The lint and the safe-area check of the cue frames do not see what happens between those moments. A cue frame with "
           "the camera away from rest is not held to the safe area in pixels.",
           "- The code hash of a render covers the Python files of the project that the scene imports, not fonts, pictures or data files.",
           "- Sound is measured, not heard: a wrong reading by the voice, word times inside running speech and the pronunciation table need a "
           "listener. A cue up to 2 frames late gives no message.",
           "- Without --gate, warnings do not change the exit status.", ""]
    path.write_text("\n".join(md), encoding="utf-8")


# --------------------------------------------------------------------------- command line
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Measure scenes or the assembled video against the quality bars. "
                                             "The gate for the film: qa.py -q review --gate")
    ap.add_argument("-q", "--quality", choices=("draft", "review", "final"), default=DEFAULT_QUALITY)
    ap.add_argument("--gate", action="store_true",
                    help="the gate for the whole film: --strict, an unmeasured bar fails, narration_verify.py runs, every warning fails "
                         "unless --waive names it, and the waivers that were used are listed")
    ap.add_argument("--waive", nargs="+", default=[], metavar="BAR",
                    help="accept the warnings of the bars whose names start with these words (listed as waivers)")
    ap.add_argument("--scenes", nargs="+", metavar="KEY", help="measure scene files (render.py), not the assembled video; 'all' = every scene")
    ap.add_argument("--video", type=Path, help="measure this video (default BUILD/out/<stem>.mp4)")
    ap.add_argument("--stem", default=None, help="name of the assembled video (default explainer-<quality>, the whole film)")
    ap.add_argument("--manifest", type=Path, default=None, help="the .json that assemble.py wrote (default: next to the video)")
    ap.add_argument("--timings", type=Path, default=None)
    ap.add_argument("--script", type=Path, default=None, help="script.json (default: next to this file)")
    ap.add_argument("--reviewed", type=Path, default=None, help="the reviewed script (default script-and-storyboard.md next to this file)")
    ap.add_argument("--allow-unspoken", action="store_true", help="for the reviewed-script check: reviewed narration may stay unspoken (a waiver)")
    ap.add_argument("--whole-file", action="store_true", help="for the reviewed-script check: look each line up in the whole file (a waiver)")
    ap.add_argument("--narration-column", nargs="*", default=[], help="for the reviewed-script check: more names of the narration column")
    ap.add_argument("--order", choices=("script", "timings"), default="script", help="where the scene order comes from")
    ap.add_argument("--scene-dir", type=Path, default=None, help="scene files (for --scenes, or for exact scene starts of --video)")
    ap.add_argument("--source", type=Path, nargs="*", default=None, help="scene source files (default explainer.py and scenes/*.py)")
    ap.add_argument("--text-funcs", nargs="*", default=[], help="more function names whose first argument is on-screen text")
    ap.add_argument("--lint-dir", type=Path, default=None, help="<Key>.lint.json for scenes with no render record (default BUILD/logs/<quality>)")
    ap.add_argument("--allow-bleed", nargs="*", default=[], metavar="KEY[:LINE]")
    ap.add_argument("--allow-cut", nargs="*", default=[], metavar="KEY")
    ap.add_argument("--strict", action="store_true",
                    help="the two motion warnings fail too: a median under 50%% of meaningful motion in a line, a stretch over 4 s with no event")
    ap.add_argument("--legacy-tail", type=float, default=0.6, help="v1 timings: seconds of picture after the sound of a scene")
    ap.add_argument("--legacy-gap", type=float, default=0.35, help="v1 timings: silence between two sentences")
    ap.add_argument("--out-dir", type=Path, default=BUILD / "out")
    ap.add_argument("--name", default="qa-report")
    args = ap.parse_args(argv)
    if args.gate and args.scenes:
        raise SystemExit("--gate measures the assembled film, not scene files (leave out --scenes)")

    t0 = time.time()
    timings = load_timings(args.timings, args.legacy_tail, args.legacy_gap)
    tfile = timings_path(args.timings)
    script, reviewed = (args.script or VID / "script.json").resolve(), (args.reviewed or VID / "script-and-storyboard.md").resolve()
    segs, fps, meta = timeline(args, timings)
    keys = [s.key for s in segs]
    out_dir = args.out_dir.resolve()
    ev = out_dir / f"{args.name}-evidence"
    files = args.source if args.source is not None else [f for f in [VID / "explainer.py", *sorted((VID / "scenes").glob("*.py"))] if f.exists()]
    src = source_checks([f.resolve() for f in files], keys, timings, TEXT_FUNCS | set(args.text_funcs)) if files else None
    marks = src["marks"] if src else {"bleed": [], "cut": []}
    print(f"measuring {meta['target']} ({meta['mode']}): {len(segs)} scenes, {segs[-1].start + segs[-1].frames} frames at {fps:g} fps"
          + ("" if meta["complete"] else f"; PART OF THE FILM ({len(segs)} of {len(meta['order'])} scenes)"))
    mo = motion(segs, fps, timings)
    away = {k: (r or {}).get("camera_away") for k, r in meta["records"].items()}
    cues, joins = frames_pass(segs, fps, timings, ev, set(args.allow_bleed) | set(marks["bleed"]), away)
    snd = sound(segs, fps, timings, meta, ev, tfile)
    flags = {"allow_unspoken": args.allow_unspoken, "whole_file": args.whole_file, "columns": tuple(args.narration_column)}
    prov = {"code": code_state(segs, meta, src), "joined": joined_state(segs, meta), "played": played(meta, keys), "gate": args.gate,
            **script_state(timings, keys, script, reviewed, meta["complete"] or args.gate, flags),
            "verify": verify_narration(tfile, script, reviewed, out_dir / f"{args.name}-narration-verify.txt") if args.gate else None}
    fmt = format_checks(segs, fps, timings, meta, prov) | {"cut_allowed": set(args.allow_cut) | set(marks["cut"])}
    lint = lint_state(keys, meta, (args.lint_dir or BUILD / "logs" / (meta.get("made_at") or args.quality)).resolve())
    bars = build_bars(meta, mo, cues, joins, snd, src, fmt, lint, args.strict, args.gate)
    waived = []
    for b in bars:
        if b["status"] == "WARN" and any(b["bar"].lower().startswith(w.lower()) for w in args.waive):
            b["status"] = "WAIVED"
            waived.append(f"--waive: {b['bar']} ({b['measured'] if len(b['measured']) <= 90 else b['measured'][:87] + '...'})")
    waivers = ([f"--allow-bleed {x}" for x in args.allow_bleed] + [f"# qa: bleed in {x}" for x in marks["bleed"]]
               + [f"--allow-cut {x}" for x in args.allow_cut] + [f"# qa: cut in {x}" for x in marks["cut"]]
               + [f"--{k.replace('_', '-')}" for k in ("allow_unspoken", "whole_file") if flags[k]]
               + [f"assemble.py {w}" for w in meta.get("waivers", [])] + waived)
    fails = [b for b in bars if b["status"] == "FAIL"]
    warns = [b for b in bars if b["status"] == "WARN"]
    report = {"made": time.strftime("%Y-%m-%d %H:%M:%S"), "meta": meta, "timings": str(tfile), "script": str(script), "reviewed": str(reviewed),
              "segments": [{"key": s.key, "start_frame": s.start, "frames": s.frames, "source": str(s.source)} for s in segs],
              "fps": fps, "bars": bars, "motion": mo, "joins": joins, "cues": cues, "sound": snd, "source": src, "lint": lint,
              "provenance": prov, "waivers": waivers, "gate": args.gate, "passed": not fails, "gate_passed": not fails and not warns}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{args.name}.json").write_text(json.dumps(report, indent=1, default=str))
    write_report(out_dir / f"{args.name}.md", report)
    print(table([[b["status"], b["bar"], b["measured"], b["limit"]] for b in bars], ["status", "bar", "measured", "limit"]))
    print("\nwaivers used: " + ("none" if not waivers else "\n  " + "\n  ".join(waivers)))
    part = "" if meta["complete"] else f" PART OF THE FILM ({len(segs)} of {len(meta['order'])} scenes: {', '.join(keys)})."
    print(f"\n{'FAIL' if fails else 'PASS'}: {len(fails)} hard bars failed, {len(warns)} warnings, {time.time() - t0:.1f} s. "
          f"Report: {out_dir / (args.name + '.md')}.{part}")
    if args.gate:
        print(f"GATE {'PASS' if report['gate_passed'] else 'FAIL'}: {len(fails)} hard bars failed, {len(warns)} warnings without a waiver, "
              f"{len(waivers)} waivers used.")
        return 0 if report["gate_passed"] else 1
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
