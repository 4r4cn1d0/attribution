"""Render scenes of the explainer: one Manim process per scene, a lossless intermediate, cue frames and a log.

    tmp/explainer-venv/bin/python writing/substack/explainer-video/render.py S03 S04              # draft
    tmp/explainer-venv/bin/python writing/substack/explainer-video/render.py --all -q review --jobs 3
    tmp/explainer-venv/bin/python writing/substack/explainer-video/render.py S03 --snap 14.6 S03:20  # more frames on the sheet
    tmp/explainer-venv/bin/python writing/substack/explainer-video/render.py --all -q final

Qualities: draft 854x480 at 15 fps (the default of render.py, assemble.py and qa.py), review 1920x1080 at 30 fps,
final from EXPLAINER_FINAL (default 2560x1440@30). A scene key is the Manim class name in explainer.py
(``--file`` points at another file). ``--all`` takes the order from script.json. For each key the tool writes,
under BUILD (tmp/explainer-build-v2 or EXPLAINER_BUILD):

    media/<quality>/<Key>/       Manim's media directory for this one process (wiped first, never shared)
    media/<quality>/<Key>.lock   held while the scene renders: a second render of the same key and quality stops
    scenes/<quality>/<Key>.mp4   the scene: lossless RGB H.264, with the scene's WAV added for review
    scenes/<quality>/<Key>.json  the record of the render (below)
    frames/<quality>/<Key>/      first.png, last.png, cueNN.png (the first frame after narration line NN ends,
                                 lines counted from 0), midNN.png (the middle of line NN), tSSS.SS.png (``--snap``
                                 times), sheet.png (all of them in time order, labelled)
    logs/<quality>/<Key>.log     everything Manim printed, then the checks
    logs/<quality>/<Key>.lint.json   the kit's layout lint of this render; ``--lint 0`` turns it off
    logs/<quality>/<Key>.run.json    what this tool saw inside the Manim process (plays, camera, code)

The record ties the picture to what it was made from. assemble.py copies it into the film's manifest and qa.py
holds the film against it:

    timings        a hash of the scene's timings: a picture that was rendered before the narration changed is refused
    code           a hash of every Python file that the scene's module imports from the project (its own file, kit/,
                   helper modules), as they were when the render started; a file that changes while the scene
                   renders fails the render. The entry file (explainer.py) counts only when it holds the scene class
                   itself: a new import line there does not make every scene old. Fonts, pictures, data files and
                   the LaTeX cache are not in the hash.
    lint, lint_issues, lint_overlay   the kit's layout lint of this render (None: not linted); ``--lint 2`` draws the
                   issues into the picture, and such a scene is refused by assemble.py and qa.py
    plays          the start, the run time and the animation names of every play() (waits too), as they ran
    camera_away    the frames in which the camera is away from its rest framing (qa.py does not hold the safe area
                   against a cue frame there; the kit's lint checks text and pinned objects)
    size, rendered_at   the scene file's bytes and the start of the render

Caching is off for every render. A scene fails, with a non-zero exit and the tail of its log, if Manim fails, if
the file is not lossless RGB, or if its frame count is not duration x fps from timings.json. A failed scene
leaves no scene file behind, so assemble.py cannot pick up an old one. Lint issues do not fail a render: they
are counted in the table, printed in the log as ``KIT-LINT`` lines, and qa.py holds them against the bar.

Why the intermediate is lossless RGB (measured on a busy 6 s test scene; tmp/explainer-build-v2/foundation/pipeline/enc/):

- Manim's own encoder is fixed at libx264 yuv420p CRF 23 and converts RGB with BT.601 without a tag. That is
  35.7 dB against the rendered frames, and a player that assumes BT.709 for HD shows coral #FF6B6B as (255,121,105).
- ``--format png`` is public API but 7 times slower (33.9 s against 5.0 s at 1080p), 2.2 MB per frame, and it drops
  frames: a wait with nothing moving writes one PNG (31 PNG files for a 45-frame scene).
- An option hook with CRF 10 or 12 is 39.0 or 38.5 dB. After the final encode it is 37.0 or 36.8 dB, against
  38.7 dB from lossless RGB (the limit set by 4:2:0 alone is 41.3 dB).
- Lossless RGB (libx264rgb, qp 0, preset veryfast) is identical to the rendered frames, bit for bit, on 180 of 180
  frames at 1080p and at 1440p. It costs 5.0 s against 4.2 s, and 17 MB per second of busy picture at 1080p
  (27 MB at 1440p). The one colour conversion (to BT.709) and the one lossy encode both happen in assemble.py.

The hook replaces the stream that Manim opens for each play(), just before the play's first frame is written;
Manim's files are not changed. Because it acts at the first frame, a hook on ``open_partial_movie_stream``
(kit.fx.set_encoder) cannot undo it. It uses private names (``_current_encode_job``, ``job.stream``,
``job.container``, ``job.path``), so the tool checks every result: if the file is not lossless RGB the scene
fails. These files do not play in QuickTime or a browser (profile High 4:4:4 Predictive). For a file to watch,
run assemble.py (it takes scene keys).
"""

from __future__ import annotations

import argparse
import ast
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

VID = Path(__file__).resolve().parent
ROOT = VID.parents[2]
BUILD = Path(os.environ.get("EXPLAINER_BUILD", ROOT / "tmp" / "explainer-build-v2")).resolve()
X264_PRESET = "veryfast"
LOG_TAIL = 30
DEFAULT_QUALITY = "draft"                       # one default for render.py, assemble.py and qa.py
FILM_STEM = "explainer-{quality}"               # the name of the whole film in BUILD/out; a part of it never takes this name
AT_REST = 1e-6                                  # the camera is at rest within this (the kit's lint uses the same)


# --------------------------------------------------------------------------- shared with assemble.py and qa.py
@dataclass(frozen=True)
class Quality:
    name: str
    width: int
    height: int
    fps: int


def quality(name: str) -> Quality:
    if name == "draft":
        return Quality(name, 854, 480, 15)
    if name == "review":
        return Quality(name, 1920, 1080, 30)
    m = re.fullmatch(r"(\d+)[x,](\d+)(?:[@,](\d+))?", os.environ.get("EXPLAINER_FINAL", "2560x1440@30").strip())
    if not m:
        raise SystemExit("EXPLAINER_FINAL must look like 2560x1440@30")
    return Quality("final", int(m[1]), int(m[2]), int(m[3] or 30))


def run(cmd: list, **kw) -> str:
    """Run a command; on failure raise with the end of what it printed."""
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if p.returncode != 0:
        raise RuntimeError(f"{Path(str(cmd[0])).name} exit {p.returncode}: {' '.join(str(c) for c in cmd)}\n{p.stderr[-2000:]}")
    return p.stdout


def timings_path(path: str | Path | None = None) -> Path:
    return Path(path or os.environ.get("EXPLAINER_TIMINGS") or BUILD / "audio" / "timings.json").resolve()


def load_timings(path: str | Path | None = None, legacy_tail: float = 0.6, legacy_gap: float = 0.35) -> dict:
    """timings.json as in INTERFACES.md. A v1 file (starts and duration only) gets sentences and the picture length."""
    path = timings_path(path)
    if not path.exists():
        raise SystemExit(f"no timings file at {path}")
    data = json.loads(path.read_text())
    texts: list[str] = []
    srt = path.with_name("narration.srt")
    if srt.exists():
        texts = re.findall(r"\d+\n[\d:,]+ --> [\d:,]+\n(.+?)\n\n", srt.read_text(encoding="utf-8") + "\n\n", flags=re.S)
    n = 0
    for key, t in data.items():
        if key.startswith("_"):
            continue
        if "sentences" not in t:
            ends = [s - legacy_gap for s in t["starts"][1:]] + [t["duration"] - legacy_gap]
            t["sentences"] = [{"text": texts[n + i] if n + i < len(texts) else "", "start": a, "end": b}
                              for i, (a, b) in enumerate(zip(t["starts"], ends))]
            t["duration"] += legacy_tail
            n += len(t["starts"])
        t.setdefault("cues", [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in t["sentences"]])
        if t.get("wav") and not Path(t["wav"]).is_absolute():
            t["wav"] = str(ROOT / t["wav"])
    return data


def timings_digest(t: dict) -> str:
    """A short hash of what a scene's picture is locked to: its duration and the times of its lines and words."""
    ms = lambda x: round(float(x) * 1000)
    core = [ms(t["duration"]), [ms(x) for x in t.get("starts", [])],
            [[ms(x["start"]), ms(x["end"]), [[w["w"], ms(w["s"]), ms(w["e"])] for w in x.get("words", [])]] for x in t.get("sentences", [])]]
    return hashlib.sha1(json.dumps(core, separators=(",", ":")).encode()).hexdigest()[:16]


def render_record(scene: Path) -> dict | None:
    """What render.py wrote next to a scene file (None for a scene file from somewhere else)."""
    try:
        return json.loads(scene.with_suffix(".json").read_text())
    except (OSError, ValueError):
        return None


def stale(scene: Path, t: dict) -> bool | None:
    """Was this scene rendered against other timings than ``t``? None when there is no record of the render."""
    record = render_record(scene)
    return None if record is None else record.get("timings") != timings_digest(t)


def sha1_file(path: str | Path) -> str | None:
    try:
        return hashlib.sha1(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        return None


def code_label(path: str | Path) -> str:
    """A short name for a source file: its path inside the video folder or inside the project."""
    for base in (VID, ROOT):
        if base in Path(path).parents:
            return str(Path(path).relative_to(base))
    return str(path)


def code_candidates(scene_file: Path) -> dict[str, str]:
    """The hash, now, of each Python file that a scene is usually made from: the scene file, VID/*.py, kit/, scenes/."""
    files = {scene_file.resolve(), *VID.glob("*.py"), *(VID / "kit").rglob("*.py"), *(VID / "scenes").rglob("*.py")}
    return {str(f.resolve()): h for f in sorted(files) if (h := sha1_file(f))}


def code_changed(record: dict | None) -> list[str] | None:
    """The source files of a render that are not today what they were then (None: the record holds no code hash)."""
    files = ((record or {}).get("code") or {}).get("files")
    if not files:
        return None
    return [code_label(f) for f, h in files.items() if sha1_file(f) != h]


RECORD_KEYS = ("quality", "frames", "timings", "scene_file", "code", "lint", "lint_issues", "lint_overlay", "plays", "camera_away",
               "size", "rendered", "rendered_at")              # what assemble.py copies into the film's manifest


def record_changes(joined: dict, now: dict | None) -> list[str]:
    """How the render record of a scene file today differs from the copy in a film's manifest ([]: the same render)."""
    if now is None:
        return []
    same = {"rendered_at": lambda r: r.get("rendered_at"), "size": lambda r: r.get("size"),
            "timings": lambda r: r.get("timings"), "code": lambda r: (r.get("code") or {}).get("hash")}
    return [name for name, get in same.items() if get(joined) != get(now)]


def film_stem(q: Quality) -> str:
    return FILM_STEM.format(quality=q.name)


def lint_groups(issues: list[dict]) -> list[dict]:
    """The lint reports of one render as one entry for each different issue, with the scene times at which it was seen."""
    kinds: dict[tuple, list] = {}
    for i in issues:
        kinds.setdefault((i.get("rule", "?"), i.get("msg", "")), []).append(i.get("time"))
    return [{"rule": r, "msg": m, "times": t} for (r, m), t in kinds.items()]


def in_ranges(ranges: list | None, index: int) -> bool:
    return any(a <= index <= b for a, b in ranges or [])


def scene_order(timings: dict, script: str | Path | None = None) -> list[str]:
    """Scene keys in the order of script.json (else of the timings file)."""
    script = Path(script or VID / "script.json")
    if script.exists():
        return [s["key"] for s in json.loads(script.read_text())["scenes"]]
    if "scenes" in timings.get("_meta", {}):
        return list(timings["_meta"]["scenes"])
    return [k for k in timings if not k.startswith("_")]


def probe(path: Path) -> dict:
    """Facts about the first video stream; ``frames`` is a count of the packets, not the header's claim."""
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
               "stream=codec_name,profile,pix_fmt,width,height,r_frame_rate,nb_read_packets,color_space,color_range,"
               "color_primaries,color_transfer", "-of", "json", path])
    s = json.loads(out)["streams"][0]
    return {"codec": s.get("codec_name"), "profile": s.get("profile"), "pix_fmt": s.get("pix_fmt"), "width": s["width"],
            "height": s["height"], "fps": float(Fraction(s["r_frame_rate"])), "frames": int(s["nb_read_packets"]),
            "color_space": s.get("color_space"), "color_range": s.get("color_range"),
            "color_primaries": s.get("color_primaries"), "color_transfer": s.get("color_transfer")}


def x264_settings(path: Path) -> str:
    """The option string that x264 writes into the stream ('' if there is none in the first megabytes)."""
    with open(path, "rb") as f:
        m = re.search(rb"x264 - core \d+[^\x00]*", f.read(4 << 20))
    return m.group(0).decode("latin1") if m else ""


def is_lossless_rgb(path: Path, info: dict | None = None) -> bool:
    info = info or probe(path)
    settings = x264_settings(path)
    return info["codec"] == "h264" and info["pix_fmt"] == "gbrp" and "rc=cqp" in settings and " qp=0" in settings


def frame_check(frames: int, t: dict, fps: float) -> tuple[bool, int | None, str]:
    """Does the picture last ``duration`` to the frame? Returns (ok, expected or None, what to print)."""
    exact = t["duration"] * fps
    want = t.get("frames", {}).get(str(int(fps))) if fps == int(fps) else None
    if want is None and abs(exact - round(exact)) < 1e-3:
        want = round(exact)
    if want is not None:
        return frames == want, want, f"{frames} frames, expected {want} ({t['duration']:.3f} s x {fps:g} fps)"
    return abs(frames - exact) <= 0.5 + 1e-6, None, (f"{frames} frames for {exact:.2f} (duration {t['duration']:.3f} s is not a "
                                                     f"whole number of frames at {fps:g} fps)")


def cue_frame(end: float, fps: float, frames: int) -> int:
    """The first frame after a line ends: what a play_until(line_end) leaves on screen (the kit's EXPLAINER_SNAP picks the same).
    Also the frame at any other scene time."""
    return min(max(int(round(end * fps)), 0), frames - 1)


def select_filter(indices: list[int]) -> str:
    """An ffmpeg ``select`` that passes exactly these frames (a balanced sum: ffmpeg refuses a chain of over 100 terms)."""
    def tree(terms: list[str]) -> str:
        return terms[0] if len(terms) == 1 else f"({tree(terms[:len(terms) // 2])}+{tree(terms[len(terms) // 2:])})"
    return "select='" + tree([f"eq(n,{i})" for i in indices]) + "'"


def extract_frames(video: Path, picks: list[tuple[int, Path]], vf: str = "") -> None:
    """Write the frames with these indices as PNG files, in one decoding pass."""
    if not picks:
        return
    order = sorted({i for i, _ in picks})
    out_dir = picks[0][1].parent
    out_dir.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-an", "-vf", select_filter(order) + ("," + vf if vf else ""), "-fps_mode", "passthrough",
         "-start_number", "0", out_dir / "_pick%05d.png"])
    made = {i: out_dir / f"_pick{k:05d}.png" for k, i in enumerate(order)}
    missing = [i for i, p in made.items() if not p.exists()]
    if missing:
        raise RuntimeError(f"{video.name}: no frame at index {missing}")
    for i, target in picks:
        shutil.copyfile(made[i], target)
    for p in made.values():
        p.unlink()


def _font(size: int):
    from PIL import ImageFont
    for name in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def contact_sheet(tiles: list[tuple[Path, str]], title: str, out: Path, tile_w: int = 640) -> None:
    """One labelled picture of all ``tiles`` (image path, caption)."""
    from PIL import Image, ImageDraw
    first = Image.open(tiles[0][0])
    tile_h = round(tile_w * first.height / first.width)
    cols = 2 if len(tiles) <= 4 else 3 if len(tiles) <= 12 else 4
    rows = -(-len(tiles) // cols)
    pad, cap, head = 12, 44, 44
    sheet = Image.new("RGB", (cols * (tile_w + pad) + pad, head + rows * (tile_h + cap + pad) + pad), (38, 40, 46))
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 10), title, font=_font(24), fill=(255, 255, 255))
    for k, (path, caption) in enumerate(tiles):
        x, y = pad + (k % cols) * (tile_w + pad), head + (k // cols) * (tile_h + cap + pad)
        sheet.paste(Image.open(path).convert("RGB").resize((tile_w, tile_h), Image.LANCZOS), (x, y))
        lines = caption.split("\n")[:2]
        for j, line in enumerate(lines):
            while draw.textlength(line, font=_font(16)) > tile_w and len(line) > 8:
                line = line[:-6] + "…"
            draw.text((x, y + tile_h + 4 + 19 * j), line, font=_font(16), fill=(232, 232, 232) if j == 0 else (170, 174, 184))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def log_tail(text: str, n: int = LOG_TAIL) -> list[str]:
    """The last lines of a scene log, without Manim's two records for each play (they would push the cause off the end)."""
    keep, skip = [], False
    for line in text.splitlines():
        if re.match(r"(\[[^\]]*\]| {20}) ?(DEBUG|INFO|WARNING|ERROR|CRITICAL) ", line):
            skip = "Partial movie file written" in line or "Caching disabled" in line
        elif not line.startswith(" " * 25):
            skip = False
        if not skip and line.strip():
            keep.append(line.rstrip())
    return keep[-n:]


def table(rows: list[list], header: list[str]) -> str:
    cells = [header] + [[str(c) for c in r] for r in rows]
    widths = [max(len(r[i]) for r in cells) for i in range(len(header))]
    return "\n".join("  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip() for r in cells)


# --------------------------------------------------------------------------- inside the Manim process
def _worker(argv: list[str]) -> None:
    """Run the Manim command line with every partial movie stream replaced by lossless RGB, and write down what ran
    (EXPLAINER_RUN_JSON): every play, the frames with the camera away from rest, the project files behind the scene."""
    import av
    import numpy as np
    from manim import Scene, config
    from manim.scene.scene_file_writer import SceneFileWriter

    original, played = SceneFileWriter.write_frame, Scene.play
    state = {"told": False, "frames": 0, "away": [], "plays": [], "module": None, "entry": None}

    def swap(job) -> None:
        job.container.close()                 # nothing was written yet: the encoder thread waits for its first frame
        container = av.open(str(job.path), mode="w")
        stream = container.add_stream("libx264rgb", rate=Fraction(config.frame_rate).limit_denominator(1001),
                                      options={"qp": "0", "preset": X264_PRESET})
        stream.pix_fmt, stream.width, stream.height = "rgb24", config.pixel_width, config.pixel_height
        stream.thread_type = "AUTO"
        job.container, job.stream, job.lossless_rgb = container, stream, True
        if not state["told"]:
            state["told"] = True
            print(f"[render.py] intermediate: libx264rgb qp=0 preset={X264_PRESET} (lossless RGB), "
                  f"{config.pixel_width}x{config.pixel_height} at {config.frame_rate:g} fps", flush=True)

    def camera_away(writer) -> bool:
        frame = getattr(getattr(getattr(writer, "renderer", None), "camera", None), "frame", None)
        if frame is None:
            return False
        return bool(abs(float(frame.width) / config.frame_width - 1) > AT_REST
                    or float(np.abs(np.asarray(frame.get_center(), dtype=float)[:2]).max()) > AT_REST)

    def write_frame(self, frame_or_renderer, num_frames: int = 1):
        job = getattr(self, "_current_encode_job", None)
        if (job is not None and not getattr(job, "lossless_rgb", False) and not config.transparent
                and config.movie_file_extension == ".mp4"):
            swap(job)
        if job is not None:
            first, state["frames"] = state["frames"], state["frames"] + num_frames
            if camera_away(self):
                if state["away"] and state["away"][-1][1] == first - 1:
                    state["away"][-1][1] = first + num_frames - 1
                else:
                    state["away"].append([first, first + num_frames - 1])
        return original(self, frame_or_renderer, num_frames)

    def names(anims) -> list[str]:
        out = []
        for a in anims:
            inner = getattr(a, "animations", None)
            out += names(inner) if isinstance(inner, (list, tuple)) and inner else \
                [".animate" if type(a).__name__ == "_AnimationBuilder" else type(a).__name__]
        return out

    def play(self, *args, **kw):
        start = float(self.renderer.time)
        try:
            return played(self, *args, **kw)
        finally:
            state["plays"].append({"start": round(start, 4), "seconds": round(float(self.renderer.time) - start, 4), "anims": names(args)})

    SceneFileWriter.write_frame, Scene.play = write_frame, play

    # Manim lists only the scene classes that a file defines. explainer.py imports its scenes, so add the one asked for.
    from manim.utils import module_ops
    listed, key = getattr(module_ops, "get_scene_classes_from_module", None), argv[-1]

    def with_imported(module):
        found = listed(module)
        named = getattr(module, key, None)
        if not (isinstance(named, type) and issubclass(named, Scene)):
            sys.exit(f"[render.py] {getattr(module, '__file__', module)} has no scene class {key} (Manim would render another one)")
        state["module"], state["entry"] = named.__module__, getattr(module, "__file__", None)
        return found if named in found else found + [named]

    def project_modules() -> dict[str, Path]:
        """Module name -> file for every loaded module of the project (not the virtual environment, not this tool)."""
        out, venv = {}, Path(sys.prefix).resolve()
        for name, mod in list(sys.modules.items()):
            f = getattr(mod, "__file__", None)
            if f and name != "__main__":
                path = Path(f).resolve()
                if path.suffix == ".py" and ROOT in path.parents and venv not in path.parents and "site-packages" not in path.parts:
                    out[name] = path
        return out

    def imported_by(start: str, local: dict[str, Path]) -> set[Path]:
        """The project files that the module ``start`` imports, directly or through other project files."""
        seen, todo = set(), [start]
        while todo:
            name = todo.pop()
            if name in seen or name not in local:
                continue
            seen.add(name)
            bits = name.split(".")
            todo += [".".join(bits[:i]) for i in range(1, len(bits))]                  # the packages above it ran too
            package = bits if local[name].name == "__init__.py" else bits[:-1]
            for node in ast.walk(ast.parse(local[name].read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        parts = a.name.split(".")
                        todo += [".".join(parts[:i]) for i in range(1, len(parts) + 1)]
                elif isinstance(node, ast.ImportFrom):
                    base = ".".join((package[:len(package) - node.level + 1] if node.level else []) + ([node.module] if node.module else []))
                    todo += [base] + [f"{base}.{a.name}" for a in node.names]
        return {local[n] for n in seen}

    def write_run() -> None:
        out = os.environ.get("EXPLAINER_RUN_JSON")
        if not out:
            return
        local = project_modules()
        try:
            if state["module"] not in local:
                raise KeyError(state["module"])
            files, how = imported_by(state["module"], local), "the imports of the scene's module"
        except (KeyError, OSError, SyntaxError, ValueError):
            files, how = set(local.values()), "every project module that the process loaded"
            files |= {Path(state["entry"]).resolve()} if state["entry"] else set()
        Path(out).write_text(json.dumps({"frames": state["frames"], "camera_away": state["away"], "plays": state["plays"],
                                         "code": {str(f): sha1_file(f) for f in sorted(files)}, "code_from": how}))

    if listed is not None:
        module_ops.get_scene_classes_from_module = with_imported
    from manim.__main__ import main as manim_main
    try:
        manim_main(args=argv, prog_name="manim")
    finally:
        write_run()


# --------------------------------------------------------------------------- one scene
@dataclass
class Result:
    key: str
    ok: bool = False
    frames: int | None = None
    expected: int | None = None
    wall: float = 0.0
    size_mb: float | None = None
    lint: int | None = None
    note: str = ""
    log: Path | None = None


class Failure(Exception):
    pass


def scene_paths(q: Quality, key: str) -> dict[str, Path]:
    return {"media": BUILD / "media" / q.name / key, "lock": BUILD / "media" / q.name / f"{key}.lock",
            "scene": BUILD / "scenes" / q.name / f"{key}.mp4", "frames": BUILD / "frames" / q.name / key,
            "log": BUILD / "logs" / q.name / f"{key}.log", "lint": BUILD / "logs" / q.name / f"{key}.lint.json",
            "run": BUILD / "logs" / q.name / f"{key}.run.json"}


def take_lock(path: Path, key: str) -> int:
    """Hold the scene's lock file for this render, so that a second render of the same key and quality stops
    instead of deleting this one's files. The lock ends with the process, however the process ends."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        holder = os.read(fd, 32).decode(errors="replace").strip()
        os.close(fd)
        raise Failure(f"{key} is being rendered by another process" + (f" (pid {holder})" if holder else "") + f": lock {path}")
    os.ftruncate(fd, 0)
    os.write(fd, str(os.getpid()).encode())
    return fd


def write_frames(scene: Path, out_dir: Path, key: str, t: dict, q: Quality, frames: int, snaps: list[float] = (),
                 away: list | None = None) -> None:
    """first.png, last.png, the end (cueNN) and the middle (midNN) of each narration line, the ``--snap`` times, and
    the labelled sheet of all of them in time order."""
    at = lambda seconds: cue_frame(seconds, q.fps, frames)
    picks = [(0, "first.png", "first frame", "")]
    for i, s in enumerate(t["sentences"]):
        picks += [(at((s["start"] + s["end"]) / 2), f"mid{i:02d}.png", f"line {i} middle", ""),
                  (at(s["end"]), f"cue{i:02d}.png", f"line {i} ends", s.get("text", ""))]
    picks += [(at(x), f"t{x:06.2f}.png", f"snap {x:g} s:", "") for x in snaps]
    picks.append((frames - 1, "last.png", "last frame", ""))
    picks.sort(key=lambda x: x[0])
    extract_frames(scene, [(f, out_dir / name) for f, name, _, _ in picks])
    title = "  ".join(x for x in (key, t.get("title", ""), f"{q.name} {q.width}x{q.height} at {q.fps} fps",
                                  f"{frames / q.fps:.2f} s", f"{frames} frames") if x)
    contact_sheet([(out_dir / name, f"{what}  {f / q.fps:.2f} s  frame {f}{'  camera away' if in_ranges(away, f) else ''}\n{text}")
                   for f, name, what, text in picks], title, out_dir / "sheet.png")


def code_record(key: str, before: dict[str, str], ran: dict, t0: float) -> dict:
    """The hash of each project file behind the scene, as it was when the render started. Fails if one changed since."""
    files = {}
    for f, h in sorted((ran.get("code") or {}).items()):
        if h is None or (f in before and before[f] != h) or (f not in before and Path(f).stat().st_mtime > t0):
            raise Failure(f"{code_label(f)} changed while {key} was rendering: render it again")
        files[f] = h
    whole = hashlib.sha1(json.dumps(sorted(files.items())).encode()).hexdigest()[:16]
    return {"hash": whole, "from": ran.get("code_from", ""), "files": files}


def render_scene(key: str, q: Quality, args: argparse.Namespace, timings: dict) -> Result:
    p = scene_paths(q, key)
    res, t0 = Result(key), time.time()
    try:
        lock = take_lock(p["lock"], key)
    except Failure as e:                      # the other process owns the log and the scene file: leave them alone
        res.note = str(e)
        return res
    try:
        _render(key, q, args, timings, p, res, t0)
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        os.close(lock)
    res.wall = time.time() - t0
    return res


def _render(key: str, q: Quality, args: argparse.Namespace, timings: dict, p: dict[str, Path], res: Result, t0: float) -> None:
    res.log = p["log"]
    for old in (p["media"], p["frames"]):
        shutil.rmtree(old, ignore_errors=True)
    for old in (p["scene"], p["scene"].with_suffix(".json"), p["lint"], p["run"]):
        old.unlink(missing_ok=True)
    for d in (p["media"], p["scene"].parent, p["log"].parent):
        d.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", "render", "-r", f"{q.width},{q.height}", "--fps", str(q.fps),
           "--disable_caching", "--media_dir", str(p["media"]), "--progress_bar", "none", "-v", "INFO", str(args.file), key]
    env = {**os.environ, "EXPLAINER_BUILD": str(BUILD), "EXPLAINER_TIMINGS": str(args.timings), "EXPLAINER_QUALITY": q.name,
           "PYTHONPATH": os.pathsep.join([str(VID)] + [x for x in [os.environ.get("PYTHONPATH")] if x]), "COLUMNS": "200",
           "EXPLAINER_RUN_JSON": str(p["run"])}
    if not args.manim_sound:
        env["EXPLAINER_NO_AUDIO"] = "1"
    for name in ("EXPLAINER_LINT", "EXPLAINER_LINT_JSON"):
        env.pop(name, None)
    if args.lint:
        env |= {"EXPLAINER_LINT": str(args.lint), "EXPLAINER_LINT_JSON": str(p["lint"])}
    with p["log"].open("w", encoding="utf-8") as log:
        log.write(f"# {time.strftime('%Y-%m-%d %H:%M:%S')}  {key}  {q.name} {q.width}x{q.height} at {q.fps} fps\n# {' '.join(cmd)}\n")
        log.flush()
        try:
            if key not in timings:
                raise Failure(f"no timings for {key} in {args.timings}")
            t = timings[key]
            before = code_candidates(args.file)
            try:
                code = subprocess.run(cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                      timeout=args.timeout).returncode
            except subprocess.TimeoutExpired:
                raise Failure(f"no result after {args.timeout} s; the process was stopped")
            if code != 0:
                log.flush()
                errors = re.findall(r"^(?:\[render\.py\] (?!intermediate)|[\w.]*(?:Error|Exception)\b).*$", p["log"].read_text(errors="replace"), flags=re.M)
                raise Failure(f"Manim exit {code}" + (": " + errors[-1].replace("[render.py] ", "")[:300] if errors else ""))
            movies = [m for m in p["media"].glob(f"videos/**/{key}.mp4") if "partial_movie_files" not in m.parts]
            if len(movies) != 1:
                raise Failure(f"Manim exit 0 but wrote {len(movies)} movie files for {key} (is the class in {args.file.name}?)")
            info = probe(movies[0])
            res.frames = info["frames"]
            if (info["width"], info["height"], round(info["fps"], 3)) != (q.width, q.height, q.fps):
                raise Failure(f"picture is {info['width']}x{info['height']} at {info['fps']:g} fps, not {q.width}x{q.height} at {q.fps}")
            if not is_lossless_rgb(movies[0], info):
                raise Failure(f"the file is not lossless RGB ({info['codec']} {info['pix_fmt']} {info['profile']}): "
                              "the encoder hook of render.py did not apply")
            ok, res.expected, text = frame_check(info["frames"], t, q.fps)
            log.write(f"[render.py] {text}\n")
            if not ok:
                raise Failure("frame count: " + text)
            if res.expected is None:
                res.note = "duration is not a whole number of frames"
            try:
                ran = json.loads(p["run"].read_text())
            except (OSError, ValueError):
                raise Failure("the Manim process left no run record: the hooks of render.py did not apply")
            if ran["frames"] != info["frames"]:
                raise Failure(f"the hooks of render.py counted {ran['frames']} frames, the file has {info['frames']}")
            code_now = code_record(key, before, ran, t0)
            if not code_now["files"]:
                raise Failure("the hooks of render.py found no project file behind the scene")
            groups = None
            if p["lint"].is_file():
                try:
                    issues = json.loads(p["lint"].read_text())
                    groups = lint_groups(issues)
                    res.lint = len(groups)
                    log.write(f"[render.py] layout lint: {res.lint} different issues in {len(issues)} reports ({p['lint']})\n")
                except (ValueError, AttributeError) as e:
                    res.note = f"the lint file does not read: {e}"
            if args.lint == 2:
                res.note = "; ".join(x for x in (res.note, "the lint overlay is drawn in the picture: assemble.py and qa.py refuse it") if x)
            wav = Path(t.get("wav") or "")
            if wav.is_file() and not args.no_sound and not args.manim_sound:
                seconds = info["frames"] / q.fps
                tmp = p["scene"].with_suffix(".part.mp4")
                run(["ffmpeg", "-v", "error", "-y", "-i", movies[0], "-i", wav, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                     "-af", f"atrim=end={seconds:.6f},apad=whole_dur={seconds:.6f}", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                     tmp])
                if probe(tmp)["frames"] != info["frames"]:
                    raise Failure("adding the sound changed the frame count")
                tmp.replace(p["scene"])
            else:
                shutil.move(str(movies[0]), p["scene"])
                res.note = "; ".join(x for x in (res.note, "" if args.no_sound or args.manim_sound else "no WAV: silent") if x)
            if not args.keep_media:
                shutil.rmtree(p["media"] / "videos", ignore_errors=True)
            if not args.no_frames:
                snaps = sorted(set(args.snaps.get(key, []) + args.snaps.get("*", [])))
                late = [x for x in snaps if x > info["frames"] / q.fps]
                if late:
                    res.note = "; ".join(x for x in (res.note, f"--snap {late[0]:g} is after the scene's end: it shows the last frame") if x)
                write_frames(p["scene"], p["frames"], key, t, q, info["frames"], snaps, ran["camera_away"])
            res.size_mb = p["scene"].stat().st_size / 1e6
            p["scene"].with_suffix(".json").write_text(json.dumps(
                {"key": key, "quality": q.name, "width": q.width, "height": q.height, "fps": q.fps, "frames": info["frames"],
                 "timings": timings_digest(t), "timings_file": str(args.timings), "scene_file": str(args.file), "code": code_now,
                 "lint": res.lint, "lint_issues": groups, "lint_overlay": args.lint == 2, "plays": ran["plays"],
                 "camera_away": ran["camera_away"], "size": p["scene"].stat().st_size,
                 "rendered": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0)), "rendered_at": t0,
                 "wall_seconds": round(time.time() - t0, 1)}, indent=1))
            res.ok = True
            log.write(f"[render.py] ok: {p['scene']} ({res.size_mb:.1f} MB), frames in {p['frames']}\n")
        except Exception as e:                # a scene that fails must not take the other scenes or the table with it
            res.note = (str(e) if isinstance(e, (Failure, RuntimeError)) else f"{type(e).__name__}: {e}").splitlines()[0]
            for left in (p["scene"], p["scene"].with_suffix(".part.mp4"), p["scene"].with_suffix(".json")):
                left.unlink(missing_ok=True)
            log.write(f"[render.py] FAILED: {e}\n")


# --------------------------------------------------------------------------- command line
def snap_times(items: list[str]) -> dict[str, list[float]]:
    """``--snap 14.6 S03:20`` -> {"*": [14.6], "S03": [20.0]}: scene seconds, for every scene or for one."""
    out: dict[str, list[float]] = {}
    for item in items:
        key, _, value = item.rpartition(":")
        try:
            out.setdefault(key or "*", []).append(float(value))
        except ValueError:
            raise SystemExit(f"--snap takes scene seconds (14.6) or KEY:seconds (S03:14.6), not {item!r}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render explainer scenes to lossless intermediates with cue frames.")
    ap.add_argument("keys", nargs="*", help="scene keys (Manim class names), for example S03 S04")
    ap.add_argument("--all", action="store_true", help="every scene, in script.json order")
    ap.add_argument("-q", "--quality", choices=("draft", "review", "final"), default=DEFAULT_QUALITY)
    ap.add_argument("--jobs", type=int, default=3, help="Manim processes at one time (default 3)")
    ap.add_argument("--file", type=Path, default=VID / "explainer.py", help="the scene file (default explainer.py)")
    ap.add_argument("--timings", type=Path, default=None, help="timings.json (default BUILD/audio/timings.json)")
    ap.add_argument("--script", type=Path, default=None, help="script.json, for the order of --all")
    ap.add_argument("--no-sound", action="store_true", help="do not add the scene's WAV to the scene file")
    ap.add_argument("--manim-sound", action="store_true", help="let the scene add its own sound (EXPLAINER_NO_AUDIO is not set)")
    ap.add_argument("--no-frames", action="store_true", help="do not extract the cue frames and the sheet")
    ap.add_argument("--snap", nargs="+", default=[], metavar="SECONDS",
                    help="more frames for the sheet: scene seconds (14.6), or KEY:seconds for one scene (S03:14.6)")
    ap.add_argument("--lint", type=int, choices=(0, 1, 2), default=1,
                    help="the kit's layout lint: 0 off, 1 on (default; the picture does not change), 2 also draws the issues in "
                         "the picture (to look at only: assemble.py and qa.py refuse such a scene)")
    ap.add_argument("--keep-media", action="store_true", help="keep Manim's partial movie files")
    ap.add_argument("--timeout", type=float, default=3600, help="seconds for one scene before it is stopped (default 3600)")
    args = ap.parse_args(argv)
    args.file, args.timings, args.snaps = args.file.resolve(), timings_path(args.timings), snap_times(args.snap)
    if not args.file.exists():
        raise SystemExit(f"no scene file at {args.file}")
    timings = load_timings(args.timings)
    keys = scene_order(timings, args.script) if args.all else args.keys
    if not keys:
        raise SystemExit("give scene keys or --all")
    if len(set(keys)) != len(keys):
        raise SystemExit("a scene key is given twice")
    q = quality(args.quality)
    print(f"{len(keys)} scene(s), {q.name} {q.width}x{q.height} at {q.fps} fps, {max(1, args.jobs)} at a time, from {args.file}")
    t0, results = time.time(), {}
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = {pool.submit(render_scene, k, q, args, timings): k for k in keys}
        for f in as_completed(futures):
            r = f.result()
            results[r.key] = r
            print(f"  {r.key}: {'ok' if r.ok else 'FAILED'} in {r.wall:.1f} s" + (f"  ({r.note})" if r.note else ""), flush=True)
    rows = [[k, "ok" if r.ok else "FAILED", r.frames if r.frames is not None else "-", r.expected if r.expected is not None else "-",
             f"{r.frames / q.fps:.2f}" if r.frames else "-", f"{r.wall:.1f}", f"{r.size_mb:.1f}" if r.size_mb is not None else "-",
             r.lint if r.lint is not None else "-", r.note] for k, r in ((k, results[k]) for k in keys)]
    print("\n" + table(rows, ["scene", "status", "frames", "expected", "seconds", "wall s", "MB", "lint", "note"]))
    failed = [results[k] for k in keys if not results[k].ok]
    print(f"\n{len(keys) - len(failed)} of {len(keys)} scenes ok, wall time {time.time() - t0:.1f} s, "
          f"scenes in {BUILD / 'scenes' / q.name}, frames in {BUILD / 'frames' / q.name}")
    for r in failed:
        tail = log_tail(r.log.read_text(encoding="utf-8", errors="replace")) if r.log and r.log.exists() else []
        print(f"\n---- {r.key} FAILED: {r.note}" + (f"\n---- last lines of {r.log}\n" + "\n".join(tail) if r.log else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        _worker(sys.argv[2:])
    else:
        sys.exit(main())
