"""The scene base class: a moving camera, the background, and a picture that is locked to the narration timings.

    class S03(Narrated):              # the class name is the scene key
        def build(self):              # authors write build(), not construct()
            ...
            self.at(2)                                        # wait until line 2 starts
            self.at_word(2, "gate")                           # wait until that word of line 2 starts
            self.play_until(self.line_end(2), anim, ...)      # an animation that ends when line 2 ends

Lines are numbered from 0, like ``starts`` and ``sentences`` in timings.json. Times are scene seconds.
The picture lasts exactly the ``duration`` of the timings (to the frame); a scene reads it as ``self.scene_duration``.
The scene fails loudly, with the scene key, the line and the overrun, if ``build()`` runs past it or waits for a
time that passed more than ``theme.CUE_TOLERANCE`` seconds ago (1 frame at 15 fps, 2 frames at 30 fps).

The scene also drives the film clock (``fx.film``): the time of each painted frame in the whole film (the durations
of the scenes before this one in timings.json, plus the scene time). Idle motion (drift, ambient, a runner that runs
by itself) reads it, so it loses no frame at a play boundary and continues across a scene join.

Environment
    EXPLAINER_TIMINGS    another timings file (default BUILD/audio/timings.json)
    EXPLAINER_NO_AUDIO   1: do not add the scene's sound (the WAV need not exist)
    EXPLAINER_LINT       1: run the layout lint after every play and at the end, print ``KIT-LINT`` lines (each
                         issue once, when it appears)
                         2: also draw the safe area and a box around every offending object
    EXPLAINER_LINT_JSON  a file that receives the lint issues of this run as JSON
    EXPLAINER_SNAP       save lossless PNG frames straight from the renderer: a comma list of scene times
                         ("2.5,7,12.25" -> t002.50.png ...) and/or the word "cues" (cueNN.png = the frame at the END
                         of line NN, plus first.png and last.png)
    EXPLAINER_SNAP_DIR   where the PNG files go (default BUILD/snaps/<SceneKey>)
    EXPLAINER_QUALITY    set by render.py: then a scene must read the pipeline's timings file under its class name
    EXPLAINER_TIMINGS_USED  a file that receives the timings file, the key and a digest of the entry this scene used
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path

import numpy as np
from manim import LEFT, RIGHT, Animation, Mobject, MovingCameraScene, Restore, VMobject, config

from . import fx
from . import theme as th
from .fx import DotCloud, FxCamera, Trail, install_background, set_pinned
from .motion import GLIDE, Stroke
from .paths import BUILD, env_flag, timings_path
from .type import T, backstroke, check_layout, layout_overlay, mark_hud, put


class TimingError(RuntimeError):
    """The picture and the narration do not fit: a cue was missed, or build() ran past the scene's duration."""


# --------------------------------------------------------------------------- things that stay fixed on screen
def _rescale(mob, k: float, about) -> None:
    """Scale ``mob`` by k about a point, with everything that is measured in scene units: stroke widths too."""
    mob.scale(k, about_point=about)
    for s in mob.get_family():
        if isinstance(s, DotCloud):
            s.radii = s.radii * k
        elif isinstance(s, Trail):
            s.widths = s.widths * k
        elif isinstance(s, VMobject):
            s.stroke_width = s.stroke_width * k
            s.background_stroke_width = s.background_stroke_width * k


def pin_to_frame(mob, frame):
    """Keep ``mob`` at its place and size ON SCREEN while the camera frame moves or zooms (HUD, titles, read-outs).

    Where the object is on screen when you call this is where it stays. From then on its coordinates are screen
    coordinates (those of a camera at rest), and FxCamera paints it without the camera's move. No updater is used,
    so it can be faded, moved, transformed and counted like any other object, also while the camera moves.
    Build and pin text while the camera is at rest: text built in world units while the camera is pushed in
    keeps its size ON SCREEN when it is pinned, so a 24 label built at 2x zoom becomes 48 on screen.
    """
    if getattr(mob, "fx_pinned", False):
        return mob
    zoom = float(frame.width) / config.frame_width
    if abs(zoom - 1) > 1e-12:
        _rescale(mob, 1 / zoom, frame.get_center())
    mob.shift(-frame.get_center())
    return set_pinned(mob)


def unpin(mob, frame):
    """Give a pinned object back to the world, at the place where it is on screen now."""
    if not getattr(mob, "fx_pinned", False):
        return mob
    zoom = float(frame.width) / config.frame_width
    mob.shift(frame.get_center())
    if abs(zoom - 1) > 1e-12:
        _rescale(mob, zoom, frame.get_center())
    return set_pinned(mob, False)


def keep_stroke(mob, frame):
    """Keep the stroke widths of ``mob`` constant ON SCREEN while the camera zooms (strokes are in scene units, so
    without this a line looks twice as thick at 2x zoom). The object itself stays in the world.

    It covers ordinary strokes (and backstrokes) and the kit's tapered ``Stroke`` (a filled outline, rebuilt at the
    width that keeps it constant). It does not cover the radii of a DotCloud or the tail of a Runner: those are
    sizes of things in the world. Call it while the camera is at rest; the widths of that moment are kept.
    """
    fam = mob.get_family()
    base = [(s, float(s.stroke_width), float(s.background_stroke_width)) for s in fam if isinstance(s, VMobject)]
    tapered = [(s, s.half) for s in fam if isinstance(s, Stroke)]
    w0 = float(frame.width)

    def follow(_m):
        k = float(frame.width) / w0
        for s, a, b in base:
            s.stroke_width, s.background_stroke_width = a * k, b * k
        for s, h in tapered:
            if abs(s.half - h * k) > 1e-12:
                s.half = h * k
                s.set_span(*s.span)

    mob.add_updater(follow)
    return mob


def follow_label(label, anchor, frame, offset=None):
    """A label that follows a point of the world while it keeps its size on screen (its backstroke too).

    anchor   a mobject, a point, or a function that returns a point, in world coordinates. For a mobject the label
             follows the edge or corner of it that it sits beside (above the object: its top), so the gap between
             object and label stays the same on screen while the object grows under a push-in
    offset   the label's offset from the anchor ON SCREEN; default: the offset it has now (place the label next to
             its object first, while the camera is at rest, then call this)
    The label is pinned (painted in screen coordinates) and moved by an updater, so it must be in the scene. Under a
    push-in it stays 24 on screen and stays beside its object; the lint holds it to the safe area like the HUD.
    ``unpin(label, frame)`` and ``label.clear_updaters()`` give it back to the world.
    """
    side = np.zeros(3)
    if isinstance(anchor, Mobject):
        lc = label.get_center()
        for k in (0, 1):                             # which side of the object's box the label is on, in x and in y
            lo, hi = anchor.get_critical_point(-np.eye(3)[k])[k], anchor.get_critical_point(np.eye(3)[k])[k]
            side[k] = 1.0 if lc[k] > hi else -1.0 if lc[k] < lo else 0.0

    def world():
        if isinstance(anchor, Mobject):
            return anchor.get_critical_point(side)
        return np.array(anchor() if callable(anchor) else anchor, dtype=float)

    def on_screen(p):
        return (p - frame.get_center()) * config.frame_width / float(frame.width)

    pin_to_frame(label, frame)
    off = label.get_center() - on_screen(world()) if offset is None else np.array([*offset, 0.0][:3], dtype=float)

    def follow(m):
        m.shift(on_screen(world()) + off - m.get_center())

    label.add_updater(follow)
    return label


def silent_timings(path: str | Path, key: str, lines: list[tuple[float, str]], duration: float,
                   word_time: float = 0.34) -> Path:
    """Write a stand-in timings file (the format of INTERFACES.md) and a silent 48 kHz WAV of the same length.

    For trying a scene before its narration exists, and for tests: never for a scene of the film (under render.py a
    scene that reads another timings file than the pipeline's stops with a TimingError).
    ``lines`` is [(start, "the words of the line"), ...]; every word gets ``word_time`` seconds. Returns ``path``.
    """
    import wave

    path = Path(path)
    sentences = []
    for start, text in lines:
        t, ws = float(start), []
        for w in text.split():
            ws.append({"w": w, "s": round(t, 3), "e": round(t + word_time - 0.04, 3)})
            t += word_time
        sentences.append({"text": text, "start": float(start), "end": round(t - 0.04, 3), "speed": 1.0, "pause_after": 0.5,
                          "words": ws})
    wav = path.with_suffix(".wav")
    data = {key: {"wav": str(wav), "duration": float(duration), "starts": [float(s) for s, _ in lines],
                  "sentences": sentences,
                  "cues": [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in sentences]},
            "_meta": {"voice": "none (silent stand-in from kit.silent_timings)", "lufs": None, "sample_rate": 48000}}
    text = json.dumps(data, indent=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != text:
        path.write_text(text)
    frames = int(round(48000 * duration))
    if not wav.exists() or wav.stat().st_size != 44 + 2 * frames:
        with wave.open(str(wav), "wb") as fh:
            fh.setnchannels(1)
            fh.setsampwidth(2)
            fh.setframerate(48000)
            fh.writeframes(b"\x00\x00" * frames)
    return path


def timings_digest(t: dict) -> str:
    """A short hash of what a scene's picture is locked to: its duration and the times of its lines and words.

    The same rule as render.py's ``timings_digest``, so the two can be compared."""
    ms = lambda x: round(float(x) * 1000)  # noqa: E731
    core = [ms(t["duration"]), [ms(x) for x in t.get("starts", [])],
            [[ms(x["start"]), ms(x["end"]), [[w["w"], ms(w["s"]), ms(w["e"])] for w in x.get("words", [])]] for x in t.get("sentences", [])]]
    return hashlib.sha1(json.dumps(core, separators=(",", ":")).encode()).hexdigest()[:16]


def _norm(word: str) -> str:
    return re.sub(r"^[^\w%]+|[^\w%]+$", "", word.lower())


def _removes(anim) -> bool:
    """Does this animation (or one inside it) take its mobject out of the scene or replace it? Manim can do that only
    for an object that is in the scene's list, so such a part is added (and the text it belongs to is broken up)."""
    if anim.is_remover() or getattr(anim, "replace_mobject_with_target_in_scene", False):
        return True
    inner = list(getattr(anim, "animations", None) or []) + [x for x in [getattr(anim, "inner", None)] if x is not None]
    return any(_removes(a) for a in inner)


def _smooth(u: float) -> float:
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


# --------------------------------------------------------------------------- the base class
class Narrated(MovingCameraScene):
    """MovingCameraScene + FxCamera + background + narration timings. Subclasses write ``build()``."""

    key: str | None = None                  # default: the class name
    timings_file: str | Path | None = None  # default: EXPLAINER_TIMINGS or BUILD/audio/timings.json
    tolerance: float = th.CUE_TOLERANCE     # seconds a cue may be late (1 frame at 15 fps, 2 at 30)
    cue_lead: int = 1                       # at() stops this many frames before the cue: the next play changes ON it
    rest_ease: float = th.REST_EASE         # seconds over which idle motion eases out of / into rest at the two ends

    def __init__(self, **kw):
        kw.setdefault("camera_class", FxCamera)
        kw.setdefault("always_update_mobjects", True)      # a wait is never one frozen frame: every updater runs in it
        super().__init__(**kw)

    # ---- life cycle
    def construct(self):
        try:
            self._open()
            self.build()
            self._close()
        finally:
            fx.film.driven, fx.film.gain = False, 1.0

    def build(self):
        raise NotImplementedError("a Narrated scene writes build(), not construct()")

    def _open(self) -> None:
        self.key = self.key or type(self).__name__
        self.fps = float(config.frame_rate)
        if not env_flag("EXPLAINER_CACHE"):
            config.disable_caching = True          # Manim's play cache does not see the background: it would go stale
        path = Path(self.timings_file) if self.timings_file else timings_path()
        if not path.exists():
            raise FileNotFoundError(f"{self.key}: no timings file at {path} (run narration.py or set EXPLAINER_TIMINGS)")
        if os.environ.get("EXPLAINER_QUALITY"):        # render.py: the film's timings, under the class name, or nothing
            if path.resolve() != timings_path().resolve():
                raise TimingError(f"{self.key}: render.py renders against {timings_path()}, but this scene reads {path}. "
                                  f"A scene of the film must not set timings_file (silent_timings is for tests).")
            if self.key != type(self).__name__:
                raise TimingError(f"{type(self).__name__}: the scene key must be the class name under render.py; it is {self.key!r}.")
        data = json.loads(path.read_text(encoding="utf-8"))
        if self.key not in data:
            raise KeyError(f"{self.key}: not in {path}; it has {[k for k in data if not k.startswith('_')]}")
        meta = data[self.key]
        self.scene_duration = float(meta["duration"])      # Manim overwrites Scene.duration at every play: do not use it
        self.starts = [float(s) for s in meta["starts"]]
        self.sentences = meta.get("sentences") or []
        self.total_frames = int(round(self.scene_duration * self.fps))
        order = [k for k in (data.get("_meta") or {}).get("scenes") or [] if k in data] or [k for k in data if not k.startswith("_")]
        before = order[:order.index(self.key)] if self.key in order else []
        self.film_start = sum(float(data[k]["duration"]) for k in before)
        used = os.environ.get("EXPLAINER_TIMINGS_USED")
        if used:
            Path(used).write_text(json.dumps({"key": self.key, "timings_file": str(path.resolve()), "timings": timings_digest(meta),
                                              "film_start": self.film_start}))
        install_background(self)
        if not env_flag("EXPLAINER_NO_AUDIO"):
            wav = Path(meta["wav"])
            if not wav.exists():
                raise FileNotFoundError(f"{self.key}: sound file {wav} is missing (set EXPLAINER_NO_AUDIO=1 to render without sound)")
            self.add_sound(str(wav))
        self.frame.save_state()
        self.lint_mode = int(os.environ.get("EXPLAINER_LINT", "0") or 0)
        self.lint_issues: list[dict] = []
        self._lint_seen: set = set()
        self._overlay = None
        self._hud: dict = {}
        self._play_start = 0.0
        self._set_film(0.0)
        fx.film.driven = True
        self._snap_setup()

    def _close(self) -> None:
        over = self._frame(self.now) - self.total_frames
        if over > 0:
            raise TimingError(f"{self.key}: build() ran {over} frames ({over / self.fps:.3f} s) past the scene duration "
                              f"{self.scene_duration:.3f} s (in line {self.line_at(self.now)}). Shorten the last plays or use play_until().")
        if over < 0:
            self._wait_frames(-over)
        if self.lint_mode:
            self.lint("end")
            out = os.environ.get("EXPLAINER_LINT_JSON")
            if out:
                Path(out).write_text(json.dumps([{k: v for k, v in it.items() if k not in ("a", "b")} for it in self.lint_issues], indent=1))

    def _snap_setup(self) -> None:
        """EXPLAINER_SNAP: write chosen frames as PNG at the moment the renderer hands them to the encoder."""
        spec = os.environ.get("EXPLAINER_SNAP", "").strip()
        if not spec:
            return
        last = max(self.total_frames - 1, 0)
        pending: dict[int, list[str]] = {}
        for item in spec.split(","):
            item = item.strip()
            if item == "cues":
                pending.setdefault(0, []).append("first")
                pending.setdefault(last, []).append("last")
                for i in range(len(self.starts)):
                    pending.setdefault(min(self._frame(self.line_end(i)), last), []).append(f"cue{i:02d}")
            elif item:
                pending.setdefault(min(self._frame(float(item)), last), []).append(f"t{float(item):06.2f}")
        out = Path(os.environ.get("EXPLAINER_SNAP_DIR", BUILD / "snaps" / self.key))
        out.mkdir(parents=True, exist_ok=True)
        writer, raw, seen = self.renderer.file_writer, self.renderer.file_writer.write_frame, [0]

        def write(frame, num_frames: int = 1, *a, **k):
            result = raw(frame, num_frames, *a, **k)
            for idx in [i for i in pending if seen[0] <= i < seen[0] + num_frames]:
                from PIL import Image
                for name in pending.pop(idx):
                    Image.fromarray(np.asarray(frame)).save(out / f"{name}.png", compress_level=2)
            seen[0] += num_frames
            return result

        writer.write_frame = write

    # ---- time
    @property
    def frame(self):
        """The camera frame (a mobject): ``self.frame.animate.scale(0.5).move_to(p)``, ``Restore(self.frame)``."""
        return self.camera.frame

    @property
    def now(self) -> float:
        """Scene time in seconds."""
        return float(self.renderer.time)

    def left(self, t: float) -> float:
        """Seconds from now until scene time ``t`` (negative if ``t`` has passed): the length of a play that ends at t."""
        return t - self.now

    def _frame(self, t: float) -> int:
        return int(round(t * self.fps))

    def _run_time(self, n: int) -> float:
        """A run time that Manim renders as exactly ``n`` frames."""
        return 1 / self.fps if n <= 1 else (n - 0.25) / self.fps

    def _wait_frames(self, n: int) -> None:
        if n > 0:
            self.wait(self._run_time(n), frozen_frame=False)

    def _set_film(self, t: float) -> None:
        """Film time and the idle gain for the frame at scene time ``t``."""
        fx.film.t = self.film_start + t
        f, ease = self._frame(t), self.rest_ease * self.fps
        fx.film.gain = 1.0 if ease <= 0 else _smooth(min(f, self.total_frames - 1 - f) / ease)

    def _line(self, i: int) -> int:
        if not 0 <= i < len(self.starts):
            raise TimingError(f"{self.key}: no line {i}; the scene has {len(self.starts)} lines (0 to {len(self.starts) - 1})")
        return i

    def line_start(self, i: int) -> float:
        return self.starts[self._line(i)]

    def line_end(self, i: int) -> float:
        """When the voice finishes line ``i`` (before the pause that follows it)."""
        self._line(i)
        if i < len(self.sentences) and "end" in self.sentences[i]:
            return float(self.sentences[i]["end"])
        return self.starts[i + 1] if i + 1 < len(self.starts) else self.scene_duration

    def span(self, i: int) -> tuple[float, float]:
        """(start, end) of line ``i`` in scene seconds."""
        return self.line_start(i), self.line_end(i)

    def line_at(self, t: float) -> int:
        """The line that is spoken (or was last spoken) at time ``t``."""
        return max([i for i, s in enumerate(self.starts) if s <= t + 1e-9], default=0)

    def word_span(self, i: int, word: str, nth: int = 1) -> tuple[float, float]:
        """(start, end) of the ``nth`` occurrence (1 = the first) of ``word`` (or of a phrase of several words) in line ``i``.

        Matching ignores case and the punctuation around a word; "1,440", "20%" and "18.5%" match as written.
        """
        self._line(i)
        if nth < 1:
            raise TimingError(f"{self.key}: word_span(nth={nth}): occurrences count from 1 (lines count from 0)")
        if i >= len(self.sentences) or not self.sentences[i].get("words"):
            raise TimingError(f"{self.key}: line {i} has no word timings")
        ws = self.sentences[i]["words"]
        have = [_norm(w["w"]) for w in ws]
        want = [_norm(w) for w in word.split()]
        if not want or not all(want):
            raise TimingError(f"{self.key}: word_span({word!r}) has no word in it")
        hits = [k for k in range(len(have) - len(want) + 1) if have[k:k + len(want)] == want]
        if len(hits) < nth:
            raise TimingError(f"{self.key}: line {i} does not have {word!r} {nth} time(s); its words are {' '.join(have)}")
        k = hits[nth - 1]
        return float(ws[k]["s"]), float(ws[k + len(want) - 1]["e"])

    @property
    def tolerance_frames(self) -> int:
        return max(1, int(round(self.tolerance * self.fps)))

    def _frames_until(self, t: float, what: str) -> int:
        n = self._frame(t) - self._frame(self.now)
        if n < -self.tolerance_frames:
            raise TimingError(f"{self.key}: {what} is at {t:.3f} s but the scene is already at {self.now:.3f} s "
                              f"({-n} frames, {-n / self.fps:.3f} s late, in line {self.line_at(self.now)}). "
                              f"Shorten what comes before it.")
        if n < 0:
            print(f"KIT-TIMING {self.key}: {what} is late by {-n} frame(s) ({-n / self.fps:.3f} s, tolerated up to "
                  f"{self.tolerance_frames})", flush=True)
        return n

    def at_time(self, t: float, what: str | None = None) -> None:
        """Wait until scene time ``t`` (updaters keep running), less ``cue_lead`` frames: the first frame of a play shows
        its start state, so a play that begins one frame early shows its first change ON the cue. Fails if ``t``
        passed more than ``tolerance`` seconds ago."""
        n = self._frames_until(t, what or f"time {t:.3f}")
        self._wait_frames(n - self.cue_lead)

    def at(self, i: int, lead: float = 0.0) -> None:
        """Wait until line ``i`` starts (``lead`` seconds earlier if given)."""
        self.at_time(self.line_start(i) - lead, f"the start of line {i}")

    def at_word(self, i: int, word: str, nth: int = 1, lead: float = 0.0) -> None:
        """Wait until the ``nth`` occurrence of ``word`` in line ``i`` starts."""
        self.at_time(self.word_span(i, word, nth)[0] - lead, f"the word {word!r} of line {i}")

    def play_until(self, t: float, *anims, min_time: float = th.MIN_PLAY, **kw) -> None:
        """Play ``anims`` so that they end exactly at scene time ``t`` (for example ``self.line_end(2)``).

        It stops with a TimingError when less than ``min_time`` seconds are left: a move that was meant to take
        seconds must not become a pop because the narration changed. Pass ``min_time=0`` for a deliberate snap.
        """
        n = self._frames_until(t, f"the end time {t:.3f} of play_until")
        need = max(1, int(round(min_time * self.fps)))
        if min_time > 0 and n < need:
            raise TimingError(f"{self.key}: play_until({t:.3f}) has {max(n, 0)} frame(s) left at {self.now:.3f} s "
                              f"(in line {self.line_at(self.now)}); it needs {min_time} s. Start it earlier, or pass min_time=0.")
        self.play(*anims, run_time=self._run_time(max(n, 1)), **kw)

    def play(self, *args, **kw) -> None:
        self._play_start = self.now
        self._play_present = {id(m) for m in self.get_mobject_family_members()}   # before Manim adds the animations' objects
        super().play(*args, **kw)
        if self.renderer.skip_animations:          # -s, -n: Manim adds the exact run time; keep the frame grid
            self.renderer.time = math.ceil(self.renderer.time * self.fps - 1e-6) / self.fps
        if getattr(self, "lint_mode", 0):
            self.lint(f"line {self.line_at(self.now)}")

    def update_to_time(self, t: float) -> None:
        if t == 0 and self.renderer.time > 1e-9:
            self.last_t = -1 / self.fps            # Manim starts every play with dt = 0: one frame of every clock was lost
        self._set_film(self._play_start + t)
        super().update_to_time(t)

    def add_mobjects_from_animations(self, animations) -> None:
        """As Manim, except that an animated PART of what is on screen (``t.part["k"].animate``, ``VGroup(a, b).animate``)
        is animated in place. Manim adds such a part to the scene, which breaks its parents up into loose pieces:
        a text loses its words, a group that holds a LiveNumber or a Runner stops their updaters, the z-order changes."""
        have = {id(m) for m in self.get_mobject_family_members()}
        for animation in animations:
            if animation.is_introducer():
                continue
            mob = animation.mobject
            if mob is None or id(mob) in have:
                continue
            leaves = mob.family_members_with_points()
            if (leaves and all(id(m) in have for m in leaves) and not _removes(animation)
                    and not any(m.updaters for m in mob.get_family() if id(m) not in have)):
                continue
            self.add(mob)
            have |= {id(m) for m in mob.get_family()}

    # ---- camera
    def push_in(self, target, zoom: float = 1.6, run_time: float = th.T_CAMERA, rate_func=GLIDE) -> Animation:
        """Animation: move the camera to ``target`` (a point or a mobject) and magnify by ``zoom`` (at most 2)."""
        assert zoom <= th.MAX_ZOOM + 1e-9, f"zoom {zoom} is more than {th.MAX_ZOOM}"
        point = target.get_center() if hasattr(target, "get_center") else np.array(target, dtype=float)
        return self.frame.animate(run_time=run_time, rate_func=rate_func).set(width=config.frame_width / zoom).move_to(point)

    def pull_back(self, run_time: float = th.T_CAMERA, rate_func=GLIDE) -> Animation:
        """Animation: return the camera to the framing the scene started with."""
        return Restore(self.frame, run_time=run_time, rate_func=rate_func)

    def pin(self, mob):
        """Keep ``mob`` fixed on screen while the camera moves. See ``pin_to_frame``."""
        return pin_to_frame(mob, self.frame)

    def unpin(self, mob):
        """Give a pinned object back to the world, where it is on screen now."""
        return unpin(mob, self.frame)

    def follow_label(self, label, anchor, offset=None):
        """A label that follows ``anchor`` in the world and keeps its size on screen. See ``follow_label``."""
        return follow_label(label, anchor, self.frame, offset)

    # ---- HUD
    def _hud_text(self, text: str, size: str, edge, x: float, y: float, **kw):
        t = mark_hud(backstroke(put(T(text, size, th.MUTED, **kw), x, y, edge=edge)))   # the world may pass under it
        return set_pinned(t)                               # placed in screen coordinates, wherever the camera is

    def hud_tag(self, text: str = th.TAG_TEXT):
        """The small fixed tag for a schematic picture: Inter 24 (``theme.TAG_SIZE``), MUTED, always bottom right.
        Returns the mobject (bring it in with ``self.play(enter(tag))`` or ``self.add(tag)``); the same object is
        returned on every call."""
        if ("tag", text) not in self._hud:
            self._hud[("tag", text)] = self._hud_text(text, th.TAG_SIZE, RIGHT, th.SAFE_X, th.FINE_Y, tracking=0.02)
        return self._hud[("tag", text)]

    def hud_cite(self, text: str, row: int = 0):
        """A citation line, always bottom left, Inter 18 (``theme.CITE_SIZE``). ``row=1`` sits one fine leading (0.4)
        above row 0, for a second citation at the same time. Returns the mobject."""
        if ("cite", text, row) not in self._hud:
            self._hud[("cite", text, row)] = self._hud_text(text, th.CITE_SIZE, LEFT, -th.SAFE_X, th.FINE_Y + row * th.LEADING[th.CITE_SIZE])
        return self._hud[("cite", text, row)]

    # ---- lint
    def lint(self, label: str = "") -> list[dict]:
        """Run the layout lint on what is on screen now and return the issues. Each issue is printed (``KIT-LINT``) and
        collected once, when it appears; one that is still there at the next check is not repeated. With
        EXPLAINER_LINT it runs by itself after every play (also every wait and every at()) and at the end."""
        issues = check_layout([m for m in self.mobjects if m is not self._overlay], frame=self.frame)
        seen = set()
        for it in issues:
            sig = (it["rule"], it["msg"])
            seen.add(sig)
            it.update(scene=self.key, time=round(self.now, 3), label=label)
            if sig not in self._lint_seen:
                print(f"KIT-LINT {self.key} t={self.now:.2f}s {label}: {it['rule']}: {it['msg']}", flush=True)
                self.lint_issues.append(it)
        self._lint_seen = seen
        if self.lint_mode >= 2:
            if self._overlay is not None:
                self.remove(self._overlay)
            self._overlay = layout_overlay(issues, frame=self.frame)
            self.add(self._overlay)
        return issues


__all__ = ["Narrated", "TimingError", "pin_to_frame", "unpin", "keep_stroke", "follow_label", "silent_timings"]
