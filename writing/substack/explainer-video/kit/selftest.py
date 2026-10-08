"""Fast checks of the kit. Run from the project root with the project Python:

    tmp/explainer-venv/bin/python writing/substack/explainer-video/kit/selftest.py            # all checks
    tmp/explainer-venv/bin/python writing/substack/explainer-video/kit/selftest.py lint timing   # some of them

It prints one PASS or FAIL line per check and exits with status 1 if any check fails. Nothing is written outside
BUILD/foundation/kit/selftest (or KIT_SELFTEST_DIR).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import traceback
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _HERE]   # kit/ itself must not be an import root
sys.path.insert(0, str(_HERE.parent))                                      # the folder that holds kit/

from manim import config, tempconfig  # noqa: E402

WORK = Path(os.environ.get("KIT_SELFTEST_DIR", _HERE.parents[3] / "tmp" / "explainer-build-v2" / "foundation" / "kit" / "selftest"))
shutil.rmtree(WORK / "media", ignore_errors=True)                           # a fresh text cache for every run
WORK.mkdir(parents=True, exist_ok=True)
config.media_dir = str(WORK / "media")
config.verbosity = "ERROR"
config.progress_bar = "none"

from kit import *  # noqa: E402,F403
from kit import fx, motion, shapes, theme, typekit  # noqa: E402

RESOLUTIONS = [(854, 480), (1920, 1080), (2560, 1440), (3840, 2160)]
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}", flush=True)
    return bool(ok)


def write_timings(key: str, duration: float, starts=(0.2, 0.6)) -> Path:
    sentences = [{"text": f"line {i} word", "start": s, "end": s + 0.3, "words": [{"w": "line", "s": s, "e": s + 0.1},
                 {"w": f"{i}", "s": s + 0.1, "e": s + 0.2}, {"w": "word.", "s": s + 0.2, "e": s + 0.3}]} for i, s in enumerate(starts)]
    path = WORK / f"{key}.json"
    path.write_text(json.dumps({key: {"wav": str(WORK / "none.wav"), "duration": duration, "starts": list(starts), "sentences": sentences}}))
    return path


def run(scene_cls, width: int = 854, height: int = 480, fps: float = 15, **cfg):
    """Render a scene in this process without writing a movie; return the scene (its camera holds the last frame)."""
    os.environ["EXPLAINER_NO_AUDIO"] = "1"
    with tempconfig({**dict(pixel_width=width, pixel_height=height, frame_rate=fps, dry_run=True, disable_caching=True), **cfg}):
        scene = scene_cls()
        scene.render()
        scene.last_frame = scene.camera.pixel_array.copy()
        return scene


# --------------------------------------------------------------------------- 1. fonts
def test_fonts() -> None:
    import manimpango

    listed = set(manimpango.list_fonts())
    check("fonts: families are registered", {"NewComputerModern10", "NewComputerModernMath", "Inter"} <= listed)
    for name, font, want in (("serif", SERIF, 0.431), ("sans", SANS, 0.546)):
        x = Text("x", font=font, font_size=96, warn_missing_font=False)
        ratio = x.height / (96 / 72)
        check(f"fonts: {name} resolves to the right face", abs(ratio - want) < 0.01, f"x-height {ratio:.3f} em (want {want})")
    fallback = Text("x", font="Helvetica", font_size=96, warn_missing_font=False).height / (96 / 72)
    check("fonts: the fallback face is told apart", abs(fallback - 0.431) > 0.02 and abs(fallback - 0.546) > 0.02, f"Helvetica x-height {fallback:.3f} em")
    approx = T("≈", "title")
    check("fonts: the math fallback supplies ≈", approx.width > 0.2, f"width {approx.width:.3f}")
    check("fonts: T() picks serif for body, Inter for label", T("a", "body").font.startswith("NewComputerModern10") and T("a", "label").font == "Inter")


# --------------------------------------------------------------------------- 2. baselines
def test_baselines() -> None:
    worst = 0.0
    for size in ("display", "title", "body", "label", "fine"):
        for s in ("xgate", "x(gypsy) 18.5%", "xnao", "x→≈Δ", "x1,440"):
            t = T(s, size)
            worst = max(worst, abs(t[0].get_bottom()[1] - baseline_y(t)) * 135)     # the x sits on the baseline
    check("baselines: predicted baseline = bottom of x, with and without descenders", worst < 0.05, f"worst error {worst:.4f} px at 1080p")
    a, b, c, d = T("gate (gypsy)", "title"), T("xnao", "title"), LiveNumber(18.5, 1, "%", size="title"), T("copy", "label")
    row(a, b, c, d)
    ys = [baseline_y(m) for m in (a, b, c, d)]
    check("baselines: row() puts text, a number and a label on one baseline", max(ys) - min(ys) < 1e-6, f"spread {max(ys) - min(ys):.2e}")
    naive = VGroup(Text("gate", font=SERIF, font_size=44), Text("xnao", font=SERIF, font_size=44)).arrange(RIGHT)
    spread = abs(naive[0].get_bottom()[1] - naive[1].get_bottom()[1]) * 135
    check("baselines: (control) arrange(RIGHT) does misalign them", spread > 3, f"{spread:.1f} px")
    block = lines(T("held-back tests", "body"), T("xnao", "body"), T("gypsy", "body"))
    gaps = [baseline_y(block[i]) - baseline_y(block[i + 1]) for i in range(2)]
    check("baselines: lines() gives an exact leading on the grid", all(abs(g - 0.6) < 1e-6 for g in gaps), f"{gaps}")


# --------------------------------------------------------------------------- 3. live number
def test_number() -> None:
    n = LiveNumber(0, size="title")
    right = []
    for v in range(0, 1441, 7):
        n.set_value(v)
        right.append(n.digits[len(n.shown) - 1].get_center()[0])            # the units digit's cell
    cells = [n._glyph(d)[1] for d in "0123456789"]
    check("number: every digit has the same advance in the serif", max(cells) - min(cells) < 1e-9)
    n.set_value(1440)
    ref = T("1,440", "title")
    ink = n.digits[4].get_right()[0] - n.digits[0].get_left()[0]
    check("number: 1,440 is set exactly as Pango sets it", abs(ink - ref.width) * 135 < 0.05, f"difference {abs(ink - ref.width) * 135:.3f} px")
    p = LiveNumber(0, 1, "%", "about", size="title", reserve=18.5)
    box = []
    for v in np.linspace(0, 18.5, 75):
        p.set_value(v)
        box.append([p.get_left()[0], p.get_right()[0], p.unit.get_left()[0], p.prefix.get_left()[0], baseline_y(p)])
    move = (np.max(box, axis=0) - np.min(box, axis=0)) * 135
    check("number: the box, the unit and the prefix do not move while it counts", move.max() < 1e-6, f"max motion {move.max():.2e} px")
    check("number: the unit and the prefix are separate parts", len(p.unit.points) > 0 and len(p.prefix.points) > 0 and p.shown == "18.5")
    family = len(p.family_members_with_points())
    p.set_value(3.2)
    check("number: its family never changes (safe under a running Transform)", len(p.family_members_with_points()) == family)
    p.shift([1.5, -0.7, 0]).scale(1.5)
    p.set_value(18.5)
    q = LiveNumber(18.5, 1, "%", "about", size=66, reserve=18.5)
    q.place(p.anchor_point)
    off = max(abs(p.width - q.width), np.abs(p.get_center() - q.get_center()).max()) * 135
    check("number: it keeps its place and size after shift and scale", abs(p.font_size - 66) < 1e-6 and off < 0.3,
          f"font size {p.font_size:.2f}, {off:.3f} px from the same number built at that size")
    inter = LiveNumber(0, size="label", anchor="left")
    last = []
    for v in (1110, 4440, 9090):
        inter.set_value(v)
        last.append(inter.digits[4].get_center()[0])
    plain = [T(str_, "label")[-1].get_center()[0] - T(str_, "label")[0].get_left()[0] for str_ in ("1,110", "4,440", "9,090")]
    check("number: Inter digits (proportional) are put in equal cells", max(last) - min(last) < 1e-9 and max(plain) - min(plain) > 0.03,
          f"last digit moves {(max(last) - min(last)) * 135:.2f} px (plain Text: {(max(plain) - min(plain)) * 135:.1f} px)")

    class Count(Narrated):
        timings_file = write_timings("Count", 1.0)

        def build(self):
            self.n = LiveNumber(0, 1, "%", size="title", reserve=18.5).place([2, 0, 0])
            label = T("gate", "label").next_to(self.n, DOWN)
            self.add(self.n, label)
            self.seen = []
            self.n.add_updater(lambda m: self.seen.append((m.shown, m.unit.get_left()[0], m.get_right()[0])))
            self.play(count_to(self.n, 18.5), self.n.animate.shift(UP), run_time=0.8)

    s = run(Count)
    values = [float(v[0]) for v in s.seen]
    check("number: it counts while a .animate moves it", values[-1] == 18.5 and len(set(values)) > 5 and abs(s.n.anchor_point[1] - 1) < 1e-6,
          f"{len(set(values))} values, ends at {values[-1]}")


# --------------------------------------------------------------------------- 4. resolutions
class Probe(Narrated):
    """A little of everything, to compare across render sizes."""

    timings_file = write_timings("Probe", 1.0)

    def build(self):
        title = put(T("Held-back tests (gypsy)", "title"), -SAFE_X, TITLE_Y)
        cloud = DotCloud(sunflower_points(300, 1.6, [-3, -0.4, 0]), color=DATA, glow=0.6)
        halo = glow_sprite(1.1, FOCUS).move_to([3, 0.3, 0])
        ring = RadialGlow(0.7, MODEL).move_to([3, -1.8, 0])
        num = put(LiveNumber(18.5, 1, "%", "about", size="title", color=MODEL), SAFE_X, -2.6, edge=RIGHT)
        line = Stroke(np.array([[-6, -2.6, 0], [1, -2.6, 0]]), W_HERO, MODEL)
        runner = Runner(lambda t: np.column_stack([-5 + 4 * t, 1.6 + 0.8 * np.sin(3 * t), 0 * t]), duration=2.0, t=1.6)
        tag = self.hud_tag()
        self.add(cloud, halo, ring, line, runner, title, num, tag)
        self.parts = dict(title=title, cloud=cloud, halo=halo, ring=ring, num=num, line=line, runner=runner, tag=tag)
        self.play(self.push_in([1, 0, 0], 1.5, run_time=0.4))
        self.zoomed = {k: (m.get_center().copy(), m.width) for k, m in self.parts.items()}
        self.play(self.pull_back(run_time=0.4))


def _small(frame: np.ndarray):
    from PIL import Image

    return np.asarray(Image.fromarray(frame[..., :3]).resize((240, 135), Image.BOX), dtype=float)


def test_resolutions() -> None:
    scenes = {wh: run(Probe, *wh, fps=5) for wh in RESOLUTIONS}
    ref = scenes[(1920, 1080)]
    worst = 0.0
    for wh, s in scenes.items():
        for k, m in s.parts.items():
            worst = max(worst, np.abs(m.get_center() - ref.parts[k].get_center()).max(), abs(m.width - ref.parts[k].width),
                        np.abs(s.zoomed[k][0] - ref.zoomed[k][0]).max(), abs(s.zoomed[k][1] - ref.zoomed[k][1]))
    check("resolutions: every object has the same place and size in scene units at 480p, 1080p, 1440p, 2160p", worst < 1e-6, f"worst difference {worst:.2e}")
    base = _small(ref.last_frame)
    diffs = {wh: float(np.abs(_small(s.last_frame) - base).mean()) for wh, s in scenes.items() if wh != (1920, 1080)}
    moved = _small(np.roll(ref.last_frame, 14, axis=1))                          # control: the 1080p frame shifted by 0.1 units
    control = float(np.abs(moved - base).mean())
    check("resolutions: the pictures agree when they are scaled to one size (less than a third of a 0.1-unit shift)",
          max(diffs.values()) < control / 3, "mean abs difference " + ", ".join(f"{w}x{h}: {d:.2f}" for (w, h), d in diffs.items())
          + f"; a 0.1-unit shift: {control:.2f}")
    bg = {wh: s.last_frame[: wh[1] // 8, : wh[0] // 8, :3].astype(float) for wh, s in scenes.items()}
    flat = max(int(np.max(np.diff(np.nonzero(np.diff(b[b.shape[0] // 2, :, 2]) != 0)[0], prepend=0))) for b in bg.values())
    check("resolutions: the vignette is dithered at every size (no flat band)", flat < 40, f"longest flat run {flat} px")


# --------------------------------------------------------------------------- 5. timing contract
def test_timing() -> None:
    class Fits(Narrated):
        timings_file = write_timings("Fits", 2.0, (0.2, 0.9))

        def build(self):
            d = DotCloud(sunflower_points(40, 1.0)).drift()
            self.add(d)
            self.at(0)
            self.play(d.to(color=FOCUS), run_time=0.37)
            self.at_word(1, "word")
            self.t_word = self.now
            self.play_until(self.line_end(1) + 0.31, d.to(glow=1.0))
            self.t_end, self.d_seen = self.now, self.scene_duration

    for fps in (15, 30):
        s = run(Fits, fps=fps)
        frames = round(s.renderer.time * fps)
        check(f"timing: a scene lasts exactly its duration at {fps} fps", frames == round(2.0 * fps) and abs(s.renderer.time - 2.0) < 1e-6,
              f"{frames} frames, {s.renderer.time:.4f} s")
        check(f"timing: scene_duration is the duration of the timings, also after plays (Manim overwrites Scene.duration) at {fps} fps", s.d_seen == 2.0)
        check(f"timing: at_word stops one frame before the word (the next play changes ON it) and play_until lands on the frame at {fps} fps",
              abs(s.t_word - (round(1.1 * fps) - 1) / fps) < 1e-6 and abs(s.t_end - round(1.51 * fps) / fps) < 1e-6, f"{s.t_word:.4f} s, {s.t_end:.4f} s")
    s = run(Fits, save_last_frame=True, write_to_movie=False, dry_run=False)        # the -s mode skips the animations
    check("timing: the last-frame mode (-s) keeps the same clock", abs(s.renderer.time - 2.0) < 1e-6 and abs(s.t_word - (round(1.1 * 15) - 1) / 15) < 1e-6,
          f"{s.renderer.time:.4f} s")

    class Overrun(Narrated):
        timings_file = write_timings("Overrun", 1.0)

        def build(self):
            self.add(Dot(color=MODEL))
            self.wait(1.4)

    class MissedCue(Narrated):
        timings_file = write_timings("MissedCue", 2.0, (0.2, 0.6))

        def build(self):
            self.add(Dot(color=MODEL))
            self.wait(1.0)
            self.at(1)

    class BadWord(Narrated):
        timings_file = write_timings("BadWord", 2.0)

        def build(self):
            self.at_word(0, "absent")

    class Waits(Narrated):
        timings_file = write_timings("Waits", 1.0)

        def build(self):
            clock, dot = ValueTracker(0.0), Dot(color=MODEL)
            dot.add_updater(lambda m: m.move_to([clock.get_value(), 0, 0]))        # an updater without dt
            self.add(dot)
            clock.set_value(2.0)
            self.wait(0.4)
            self.x_seen = float(dot.get_center()[0])

    check("timing: a plain wait is live, so an updater without dt runs in it", run(Waits).x_seen == 2.0)

    for cls, needles in ((Overrun, ("Overrun", "6 frames (0.400 s) past the scene duration 1.000 s", "line 1")), (MissedCue, ("MissedCue", "line 1", "6 frames, 0.400 s late")),
                         (BadWord, ("BadWord", "absent", "line 0"))):
        try:
            run(cls)
            check(f"timing: {cls.__name__} raises", False, "no error was raised")
        except TimingError as e:
            check(f"timing: {cls.__name__} raises with the key, the line and the amount", all(n in str(e) for n in needles), str(e)[:150])

    def late_by(frames: int):
        class Late(Narrated):
            timings_file = write_timings("Late", 2.0, (0.2, 0.6))

            def build(self):
                self.add(Dot(color=MODEL))
                self.wait(0.6 + frames / self.fps)
                self.at(1)
        return Late

    got = {}
    for fps, frames in ((15, 1), (15, 2), (30, 2), (30, 3)):
        try:
            run(late_by(frames), fps=fps)
            got[(fps, frames)] = "tolerated"
        except TimingError:
            got[(fps, frames)] = "error"
    check("timing: the cue tolerance is 0.07 s: 1 frame at 15 fps, 2 frames at 30 fps", got == {(15, 1): "tolerated", (15, 2): "error",
          (30, 2): "tolerated", (30, 3): "error"}, str(got))

    class NoTimings(Narrated):
        timings_file = WORK / "does-not-exist.json"

        def build(self):
            pass

    try:
        run(NoTimings)
        check("timing: a missing timings file is an error", False)
    except FileNotFoundError as e:
        check("timing: a missing timings file is an error", "NoTimings" in str(e))
    os.environ.pop("EXPLAINER_NO_AUDIO", None)
    try:
        with tempconfig(dict(dry_run=True, frame_rate=15, pixel_width=854, pixel_height=480)):
            Fits().render()
        check("timing: a missing sound file is an error unless EXPLAINER_NO_AUDIO=1", False)
    except FileNotFoundError as e:
        check("timing: a missing sound file is an error unless EXPLAINER_NO_AUDIO=1", "EXPLAINER_NO_AUDIO" in str(e))


# --------------------------------------------------------------------------- 6. lint
def test_lint() -> None:
    def rules(*mobs, **kw):
        return sorted({it["rule"] for it in check_layout(list(mobs), **kw)})

    title = put(T("Two best cases", "title"), -SAFE_X, TITLE_Y)
    label = put(T("held-back tests", "label"), -SAFE_X, 0.0)
    check("lint: a clean layout has no issue", rules(title, label) == [], str(rules(title, label)))
    clash = put(T("copy A", "label"), -SAFE_X + 1.0, 0.05)
    check("lint: finds the planted overlap", rules(title, label, clash) == ["text-text"], str(rules(title, label, clash)))
    out = put(T("outside", "label"), SAFE_X - 0.5, 0.0)
    found = check_layout([title, out])
    check("lint: finds the planted safe-area break", [it["rule"] for it in found] == ["safe-area"] and "outside" in found[0]["msg"], found[0]["msg"] if found else "")
    bleed = out.copy()
    bleed.bleed_ok = True
    check("lint: a marked bleed is allowed", rules(bleed) == [])
    cloud = DotCloud(sunflower_points(200, 1.5), color=DATA)
    on_art = T("one group", "label").move_to([0.2, 0.1, 0])
    check("lint: text on art without a backstroke is an issue", rules(cloud, on_art) == ["text-shape"], str(rules(cloud, on_art)))
    check("lint: text on art with a backstroke passes", rules(cloud, backstroke(on_art.copy())) == [])
    line = Line([-1, 0, 0], [1, 0, 0], stroke_width=W_LINE, color=MODEL)
    check("lint: a line through a label is an issue", rules(line, T("gate", "label")) == ["text-shape"])
    check("lint: an off-scale font size is an issue", rules(T("odd", 28)) == ["type-scale"], str(rules(T("odd", 28))))
    check("lint: 18 is for the HUD only", rules(T("small print", "fine")) == ["text-size"], str(rules(T("small print", "fine"))))
    many = lines(*[T("one two three four five", "label") for _ in range(3)]).move_to([0, 0, 0])
    check("lint: more than 12 words is an issue", rules(many) == ["word-count"], str(rules(many)))
    hidden = clash.copy().set_opacity(0)
    check("lint: invisible things are ignored", rules(title, label, hidden) == [])

    line = put(T("held-back tests of one tiny learner", "label"), -SAFE_X, -1.0)
    ws = words(line)
    check("lint: the words of words() are text: counted, on one baseline, and not held against each other",
          rules(*ws) == [] and typekit.word_count(list(ws)) == 6 and max(abs(baseline_y(w) - baseline_y(line)) for w in ws) < 1e-9
          and rules(*ws, *words(T("one two three four five six seven", "label"))) == ["word-count"], str(rules(*ws)))
    marked = put(T("the gate", "title", parts={"k": "gate"}), -SAFE_X, 1.0)
    check("lint: an underline and a marker belong to their text", rules(marked, underline(marked.part["k"], of=marked), marker(marked.part["k"], FOCUS)) == [])

    class Linted(Narrated):
        timings_file = write_timings("Linted", 1.0, (0.2, 0.6))

        def build(self):
            a = put(T("copy A", "label"), 0, 0)
            self.add(a, self.hud_tag(), self.hud_cite("Data Attribution in Adaptive Learning  ·  arXiv 2604.04892"))
            self.at(0)
            self.play(a.animate.shift(RIGHT * 6.2), run_time=0.2)

    os.environ.update(EXPLAINER_LINT="1", EXPLAINER_LINT_JSON=str(WORK / "Linted.lint.json"))
    try:
        s = run(Linted)
    finally:
        os.environ.pop("EXPLAINER_LINT")
        os.environ.pop("EXPLAINER_LINT_JSON")
    got = [(it["rule"], it["label"]) for it in s.lint_issues]
    check("lint: EXPLAINER_LINT=1 checks after every play and at the end, reports an issue once, and the HUD passes",
          got == [("safe-area", "line 0")], str(got))
    saved = json.loads((WORK / "Linted.lint.json").read_text())
    check("lint: EXPLAINER_LINT_JSON gets the issues with the scene key, the time, the rule and the message",
          [(it["scene"], it["time"], it["rule"]) for it in saved] == [("Linted", 0.333, "safe-area")]
          and "copy A" in saved[0]["msg"], str(saved[0]) if saved else "empty")

    class Zoomed(Narrated):
        timings_file = write_timings("Zoomed", 1.0)

        def build(self):
            self.label = T("copy A", "label").move_to([3.5, 1.8, 0])
            self.tag = self.hud_tag()
            self.add(self.label, self.tag)
            self.play(self.push_in([3.0, 1.5, 0], 2.0, run_time=0.3))
            self.inside = check_layout(self.mobjects, frame=self.frame)
            self.world = self.pin(T("copy B", "label").move_to([3.0, 1.2, 0]))        # pinned while the camera is in
            self.pinned_at = self.world.get_center().copy()
            self.back = self.unpin(self.world.copy()).get_center()

    s = run(Zoomed)
    check("lint: positions and sizes are judged on screen while the camera is in", s.inside == [], str([it["msg"] for it in s.inside]))

    class Away(Narrated):
        timings_file = write_timings("Away", 1.0)

        def build(self):
            far = T("far away", "label").move_to([-5.5, -3.0, 0])                     # outside the picture after the push-in
            art = DotCloud(sunflower_points(300, 1.6, [5.5, 1.2, 0]), color=DATA)     # runs off the safe area
            cut = T("cut off", "label").move_to([2.0, 3.0, 0])                        # half out of the safe area after the push-in
            out = self.pin(backstroke(T("pinned", "label")).move_to([6.3, -2.5, 0]))  # a pinned object, outside the safe area
            self.add(far, art, cut, out)
            names = lambda: sorted(it["msg"].split('"')[1] if '"' in it["msg"] else "cloud" for it in check_layout(self.mobjects, frame=self.frame))  # noqa: E731
            self.rest = names()
            self.play(self.push_in([3.0, 1.25, 0], 2.0, run_time=0.3))
            self.away = names()

    aw = run(Away)
    check("lint: at rest everything in the picture is held to the safe area", aw.rest == ["cloud", "pinned"], str(aw.rest))
    check("lint: while the camera is away, the world may run off the picture; text and pinned objects may not",
          aw.away == ["cut off", "pinned"], str(aw.away))
    check("pin: the HUD tag (Inter 24) is in screen coordinates and keeps them during a push-in",
          abs(s.tag.get_right()[0] - SAFE_X) < 1e-9 and abs(typekit.em(s.tag) - 24 / 72) < 1e-9, f"right edge at {s.tag.get_right()[0]:.4f}")
    check("pin: pin() converts a world object to its place on screen, unpin() brings it back",
          np.abs(s.pinned_at - np.array([0.0, -0.6, 0.0])).max() < 1e-9 and np.abs(s.back - np.array([3.0, 1.2, 0.0])).max() < 1e-9, f"{s.pinned_at}")


# --------------------------------------------------------------------------- 7. camera effects
def still(build, width: int = 854, height: int = 480, key: str = "Still"):
    """The last frame of a one-frame scene whose build() is ``build(scene)``."""

    class Still(Narrated):
        timings_file = write_timings(key, 0.2, (0.0,))

        def build(self):
            build(self)

    return run(Still, width, height, fps=5)


def pixel(frame: np.ndarray, x: float, y: float) -> np.ndarray:
    h, w = frame.shape[:2]
    return frame[int(round(h / 2 - y * h / 8)), int(round(w / 2 + x * h / 8)), :3].astype(float)


def test_fx() -> None:
    rng = np.random.default_rng(5)
    paths = [np.column_stack([np.linspace(-5, 5, 40), np.cumsum(rng.normal(0, 0.12, 40)), np.zeros(40)]) for _ in range(30)]

    def art():
        return VGroup(*[VMobject(stroke_color=MODEL, stroke_width=W_LINE, stroke_opacity=0.25).set_points_as_corners(q) for q in paths])

    live = still(lambda s: s.add(art())).last_frame
    baked = still(lambda s: s.add(bake(s, art()))).last_frame
    diff = float(np.abs(live[..., :3].astype(float) - baked[..., :3]).mean())
    check("fx: baked art is the same picture as the live art", diff < 0.6 and float(np.abs(live[..., :3].astype(float) - live[0, 0, :3]).max()) > 30,
          f"mean abs difference {diff:.3f}")

    def clipped(s):
        clip = Circle(radius=1.0, stroke_width=0).move_to([-2, 0, 0])
        s.add(clip, set_clip(Rectangle(width=8, height=4, stroke_width=0, fill_color=FOCUS, fill_opacity=1), clip))

    f = still(clipped).last_frame
    check("fx: set_clip shows an object only inside its clip", pixel(f, -2, 0)[0] > 200 and pixel(f, 1.5, 0).max() < 30, f"inside {pixel(f, -2, 0)}, outside {pixel(f, 1.5, 0)}")

    def discs(mode):
        def build(s):
            a = Circle(radius=1.0, stroke_width=0, fill_color=MODEL, fill_opacity=0.5).shift(LEFT * 0.5)
            b = a.copy().shift(RIGHT)
            s.add(a, set_blend(b, mode))
        return build

    over, add = pixel(still(discs(None)).last_frame, 0, 0), pixel(still(discs("add")).last_frame, 0, 0)
    check("fx: set_blend('add') makes overlapping light brighter", add.sum() > over.sum() + 40, f"over {over}, add {add}")

    def pinned(zoom):
        def build(s):
            s.frame.scale(1 / zoom).move_to([1.0, 0.5, 0] if zoom != 1 else ORIGIN)
            s.world = Circle(radius=1.5, stroke_color=DATA, stroke_width=W_BOLD)
            s.label = s.pin(T("pinned", "label").move_to(s.frame.get_center() + UP * 2 / zoom).scale(1 / zoom))
            s.add(s.world, s.hud_tag(), s.label)
        return build

    def region(m, width: int = 854, height: int = 480, pad: int = 6) -> tuple[slice, slice]:
        """The pixels of a mobject that is in screen coordinates (a pinned one, or any one while the camera is at rest)."""
        k = height / 8
        return (slice(int(height / 2 - m.get_top()[1] * k) - pad, int(height / 2 - m.get_bottom()[1] * k) + pad),
                slice(int(width / 2 + m.get_left()[0] * k) - pad, int(width / 2 + m.get_right()[0] * k) + pad))

    sa, sb = still(pinned(1.0)), still(pinned(1.8))
    a, b = sa.last_frame[..., :3].astype(float), sb.last_frame[..., :3].astype(float)
    same = max(float(np.abs(a[region(m)] - b[region(m)]).mean()) for m in (sa.label, sa.hud_tag()))
    ink = float(np.abs(a[region(sa.label)] - a[0, 0]).max())
    moved = float(np.abs(a[region(sa.world)] - b[region(sa.world)]).mean())
    check("fx: pinned objects are painted at the same pixels when the camera zooms", same < 0.05 and ink > 100 and moved > 1.0,
          f"the pinned regions differ by {same:.3f}, the world by {moved:.2f}")

    def faint_zone(row: np.ndarray, centre: int, radius: int = 337) -> np.ndarray:
        """The part of a scan line through a glow where its light is 1 to 12 code values: where rings would show."""
        return row[centre - radius + 37:centre - radius + 115]

    def undithered(radius: float, color, peak: float) -> RasterLayer:
        px = int(np.ceil(2 * radius * px_per_unit()))
        y, x = np.mgrid[-1:1:px * 1j, -1:1:px * 1j]
        alpha = np.rint(peak * np.clip(1 - np.hypot(x, y), 0, 1) ** GLOW_POWER * 255)
        rgba = np.dstack([np.rint(alpha[..., None] * np.array(ManimColor(color).to_rgb())), alpha]).astype(np.uint8)
        return RasterLayer(rgba, height=2 * radius, premultiplied=True)

    def glows(s):
        install_background(s, noise=0.0)                                           # a flat ground: no grain to hide rings
        s.add(glow_sprite(2.5, FOCUS, peak=0.5).move_to([-3, 1.2, 0]), RadialGlow(2.5, FOCUS, peak=0.5).move_to([3, 1.2, 0]),
              undithered(2.5, FOCUS, 0.5).move_to([0, -1.5, 0]))

    f = still(glows, 1920, 1080).last_frame.astype(int)
    top, low = 540 - 162, 540 + 202                                                # the rows through the centres
    lively = {name: float(np.mean(np.diff(faint_zone(f[row, :, 2], col)) != 0))    # blue: the channel with the fewest levels
              for name, row, col in (("sprite", top, 555), ("gradient", top, 1365), ("control", low, 960))}
    for name in ("sprite", "gradient"):
        rise = np.convolve(f[top, :, 0], np.ones(15) / 15, mode="valid")[(218 if name == "sprite" else 1028):][:330:15]
        check(f"fx: the glow {name} is dithered and rises smoothly (no rings on a flat ground)",
              lively[name] > 0.2 and np.all(np.diff(rise) > -0.5),
              f"{lively[name]:.0%} of neighbouring pixels differ in its faint zone (undithered control: {lively['control']:.0%})")
    check("fx: (control) the same glow without dither does band", lively["control"] < 0.1, f"{lively['control']:.0%}")
    g = glow_sprite(1.1, FOCUS)
    check("fx: a glow sprite has the box of its radius, and one picture pixel per screen pixel", abs(g.width - 2.2) < 1e-9 and g.fx_snap
          and abs(g.width * g.fx_bleed * px_per_unit() - g.fx_pixels.shape[1]) < 1e-6)

    c = DotCloud(sunflower_points(50, 1.0)).drift(0.03, seed=1)
    before, xy0 = c.points.copy(), c.drawn_xy().copy()
    c.update(0.5)
    amb = ambient(Circle(radius=1, color=MODEL))
    amb.update(1.0)
    check("fx: ambient motion moves the picture, not the points", np.array_equal(before, c.points) and np.abs(c.drawn_xy() - xy0).max() > 1e-4
          and np.abs(amb.fx_ambient.offset()).max() > 1e-4 and np.abs(amb.get_center()).max() < 1e-9)
    home = field_points(400, 6.0, 3.0, seed=2)
    two = DotCloud(home, color=DATA, opacity=0.5)
    near = np.argsort(np.linalg.norm(home - [1.5, 0, 0], axis=1))[:80]
    rest = np.setdiff1d(np.arange(400), near)
    goal = match_points(home[near], sunflower_points(80, 0.6, [1.5, 0, 0]))
    anims = [two.to(centers=goal, color=FOCUS, glow=1.0, idx=near, lag=0.4, order="radial", arc=0.5), two.to(opacity=0.2, idx=rest, pop=0.5)]
    for a in anims:
        a.begin()
    for alpha in np.linspace(0, 1, 13):
        for a in anims:
            a.interpolate(alpha)
    check("fx: two cloud.to() on one cloud in one play both arrive (a group gathers while the rest steps back)",
          np.abs(two.points[near] - goal).max() < 1e-12 and np.array_equal(two.points[rest], home[rest])
          and np.allclose(two.rgbas[near, :3], ManimColor(FOCUS).to_rgb()) and np.allclose(two.rgbas[near, 3], 0.5)
          and np.allclose(two.rgbas[rest, 3], 0.2) and np.allclose(two.glows[near], 1.0) and np.allclose(two.glows[rest], 0.0)
          and np.allclose(two.radii, DOT_R), f"worst distance from the target {np.abs(two.points[near] - goal).max():.1e}")
    late_ones = DotCloud(home, color=DATA, opacity=0.0)
    a = late_ones.appear(sampling_rhythm(400, total=2.0, slow=0.5, mid=0.2, n_mid=3).starts, fade=0.3, opacity=0.8, run_time=2.0)
    a.begin()
    a.interpolate(0.0)
    hidden = float(late_ones.rgbas[:, 3].max())
    a.interpolate(1.0)
    check("fx: cloud.appear() with a run time shorter than the last fade still ends with every point there",
          hidden == 0.0 and np.allclose(late_ones.rgbas[:, 3], 0.8) and np.allclose(late_ones.glows, 0.0) and np.allclose(late_ones.radii, DOT_R))
    part = c.split(np.arange(10))
    check("fx: DotCloud.split takes points out as a new cloud", (part.n, c.n) == (10, 40) and part.radii.shape == (10,) and c.rgbas.shape == (40, 4))
    target = match_points(c.points, c.points[::-1].copy())
    check("fx: match_points finds the shortest regrouping", np.abs(target - c.points).max() < 1e-12)
    s = Stroke(np.array([[-2, 0, 0], [2, 0, 0]]), W_HERO, MODEL, taper=(0.3, 0.3))
    check("fx: a tapered stroke is widest in the middle and closes to nothing at its ends", abs(s.height - 0.045) < 1e-6 and abs(s.width - 4) < 1e-6,
          f"height {s.height:.4f}")


def test_tex() -> None:
    try:
        m = tex(r"\mathrm{H}", "title")
    except Exception as e:
        check("tex: LaTeX compiles through xelatex and pdftocairo", False, str(e)[:120])
        return
    h = T("H", "title")
    check("tex: a formula has the same em as text of that size", abs(m.height - h.height) / h.height < 0.01, f"H is {m.height * 135:.2f} px, text H is {h.height * 135:.2f} px")
    f = tex(r"\frac{⟦num|\sigma^2⟧}{⟦den|n⟧} \geq 0", "body")
    r = row(T("variance", "body"), f)
    check("tex: a formula sits on the text baseline and has named parts", abs(baseline_y(r[0]) - baseline_y(f)) < 1e-9 and set(f.part) == {"num", "den"}
          and f.get_bottom()[1] < baseline_y(f) < f.get_top()[1])


# --------------------------------------------------------------------------- 9. rules of the kit itself
def test_rules() -> None:
    names = {n for n in dir(__import__("manim.utils.color.manim_colors", fromlist=["x"])) if n.isupper()}
    bad = []
    for path in sorted(_HERE.glob("*.py")):
        if path.name in ("theme.py", "selftest.py"):
            continue
        text = path.read_text()
        code = re.sub(r'""".*?"""|#.*', "", text, flags=re.S)
        bad += [f"{path.name}: {m}" for m in re.findall(r"#[0-9A-Fa-f]{6}\b", code)]
        bad += [f"{path.name}: {m}" for m in re.findall(r"\b[A-Z][A-Z_]+[A-E]?\b", code) if m in names]
    check("rules: no colour literal and no Manim colour constant outside theme.py", not bad, ", ".join(bad[:6]))
    ns: dict = {}
    exec("from kit import *", ns)
    check("rules: from kit import * does not shadow type() and does not export Manim's colours",
          ns.get("type", type) is type and not (names & set(ns)), f"{len(ns)} names")
    check("rules: the scale and the strokes are the brief's", theme.SCALE == {"display": 64, "title": 44, "body": 32, "label": 24, "fine": 18}
          and (W_HAIR, W_LINE, W_BOLD, W_HERO) == (1.0, 2.0, 3.0, 4.5) and (SAFE_X, SAFE_Y, GRID) == (6.4, 3.4, 0.2))
    r = sampling_rhythm(400, total=6.0)
    gaps = np.diff(r.starts)
    check("rhythm: one slow draw, a few at about 0.45 s, then many per second",
          abs(gaps[0] - 1.4) < 1e-9 and np.allclose(gaps[1:4], 0.45) and gaps[-1] < 0.02 and np.all(gaps[4:] <= gaps[3:-1] + 1e-9) and abs(r.total - 6.0) < 1e-9,
          f"first gaps {np.round(gaps[:6], 2)}, last gap {gaps[-1] * 1000:.1f} ms")


def test_motion() -> None:
    old, new = lines(T("a tiny learner", "body"), T("two copies", "body"), T("one shared draw", "body")), T("the pool", "body").shift(RIGHT * 3)
    shape = new.width / new.height
    anim = hand_over(old, new)
    anim.begin()
    anim.interpolate(0.5)
    mid = anim.animations[1].mobject
    check("motion: a text hand-over to other words cross-fades without stretching", abs(mid.width / mid.height - shape) < 1e-6
          and abs(mid.height - T("the pool", "body").height) < 1e-6 and 0 < mid.get_center()[0] < 3)
    big, small = T("Points of light", "display"), T("Points of light", "title").shift(UP * 2)
    check("motion: the same words at another size travel and change size (FadeTransform)", type(hand_over(big, small)).__name__ == "FadeTransform"
          and type(born_from(big, T("other words", "title"))).__name__ == "AnimationGroup")
    a, b = Circle(radius=1, color=MODEL), Square(side_length=1, color=DATA)
    check("motion: shapes morph (TransformFromCopy, ReplacementTransform); a point gives birth by growing",
          [type(x).__name__ for x in (born_from(a, b), hand_over(a, b), born_from([0, 0, 0], b))] == ["TransformFromCopy", "ReplacementTransform", "FadeIn"])
    f = late(0.6)
    check("motion: late(0.6) does nothing until 60% of the play and then lands", f(0.59) == 0 and 0 < f(0.8) < 1 and f(1.0) == 1)
    check("motion: lag_for follows the stagger rule", [lag_for(n) for n in (3, 12, 100, 1440)] == [LAG_FEW, LAG_SOME, LAG_MANY, 1 / 1440])
    r = Runner(lambda t: np.column_stack([t, 0 * t, 0 * t]), duration=2.0, tail=0.5)
    r.set_time(1.0)
    r.start().update(0.25)
    check("motion: a runner follows its path in simulated time and carries a tail", abs(r.head[0] - 1.25) < 1e-9
          and abs(r.trail.points[0, 0] - 0.75) < 1e-9 and abs(r.trail.points[-1, 0] - 1.25) < 1e-9 and r.trail.widths[0] < r.trail.widths[-1])
    n = LiveNumber(0, 1, "%", size="title")
    count_to(n, 18.5)
    check("motion: count_to gives the number a tracker and keeps room for the final value", n.tracker is not None and n.reserve == 18.5)


def test_docs() -> None:
    import ast

    readme = (_HERE / "README.md").read_text()
    source = (_HERE / "example_scene.py").read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "Example")
    example = "\n".join(source.splitlines()[node.lineno - 1:node.end_lineno])
    check("docs: the example in README.md is the code of example_scene.py", example in readme)
    names = [n for mod in (typekit, fx, motion, shapes) for n in mod.__all__] + ["Narrated", "TimingError", "keep_stroke", "follow_label", "silent_timings"]
    internal = {"SANS", "MEDIUM", "register_fonts", "tex_svg", "atoms", "describe", "size_of", "font_for", "AmbientState", "glow_rgba",
                "set_pinned", "vignette_array", "set_encoder", "Rhythm", "Timed"}
    missing = [n for n in names if n not in internal and not re.search(r"(?<![A-Za-z_])" + re.escape(n) + r"(?![A-Za-z_])", readme)]
    check("docs: README.md names every public function and class of the kit", not missing, ", ".join(missing))
    count = len(re.findall(r"^\s+check\(", (_HERE / "selftest.py").read_text(), flags=re.M))
    check("docs: every Manim class that needs dvisvgm has a stand-in that says what to use", all(type(globals().get(n)).__name__ == "_NoLatex" for n in NO_LATEX)
          and "LiveNumber" in str(DecimalNumber), f"{len(NO_LATEX)} stand-ins; {count} check() calls in this file")


# --------------------------------------------------------------------------- 10. the film clock, joins, cues
def test_clock() -> None:
    def body(self):
        runner = Runner(lambda t: np.column_stack([t, 0 * t, 0 * t]), duration=100.0, tail=0.5)
        self.add(runner, Dot(color=MODEL))
        mover, still_dot = Dot(color=MODEL), Dot(color=MODEL)
        self.dts = []
        still_dot.add_updater(lambda m, dt: self.dts.append(dt))
        self.add(mover, still_dot)
        runner.start()
        self.t0 = self.now
        for _ in range(10):                      # ten cues: a wait, then a short play
            self.wait(0.2)
            self.play(mover.animate.shift(RIGHT * 0.1), run_time=0.2)
        self.ran, self.clock = self.now - self.t0, runner.clock.get_value()

    for fps in (15, 30):
        cls = type(f"Clock{fps}", (Narrated,), {"timings_file": write_timings(f"Clock{fps}", 5.0, (0.2,)), "build": body})
        s = run(cls, fps=fps)
        lost = (s.ran - s.clock) * fps - 1          # the clock shows the last painted frame; now is one frame later
        check(f"clock: a started runner keeps scene time through 10 waits and 10 plays at {fps} fps (Manim gives dt = 0 at each play start)",
              abs(lost) < 1e-6 and abs(sum(s.dts) - s.now) < 1.01 / fps, f"{lost:+.2f} frames lost; dt of an updater sums to {sum(s.dts):.3f} s in {s.now:.3f} s")

    path = WORK / "Join.json"
    sent = lambda: [{"text": "a", "start": 0.2, "end": 0.5, "words": [{"w": "a", "s": 0.2, "e": 0.5}]}]  # noqa: E731
    path.write_text(json.dumps({"J1": {"wav": "", "duration": 2.0, "starts": [0.2], "sentences": sent()},
                                "J2": {"wav": "", "duration": 1.0, "starts": [0.2], "sentences": sent()}, "_meta": {"scenes": ["J1", "J2"]}}))
    pts = sunflower_points(300, 2.0, jitter=0.3)

    def scene(key, ease, keep):
        def build(self):
            c = DotCloud(pts, color=DATA, glow=0.3).drift(0.05, seed=4, twinkle=0.15)
            ambient(halo := glow_sprite(0.8, FOCUS).move_to([3, 0, 0]), amp=0.05, pulse=0.2, seed=2)
            self.add(halo, c)
            self.wait(self.scene_duration)
            keep[key] = (c.drawn_xy().copy(), c.twinkle_factor().copy(), halo.fx_ambient.offset().copy(), fx.film.t, fx.film.gain, self.film_start)
        return type(key, (Narrated,), {"timings_file": path, "rest_ease": ease, "build": build})

    for ease in (theme.REST_EASE, 0.0):
        keep: dict = {}
        first: dict = {}

        def j2_first(self, keep=keep, first=first):
            c = DotCloud(pts, color=DATA, glow=0.3).drift(0.05, seed=4, twinkle=0.15)
            ambient(halo := glow_sprite(0.8, FOCUS).move_to([3, 0, 0]), amp=0.05, pulse=0.2, seed=2)
            self.add(halo, c)
            self.wait(1 / self.fps)                 # one frame: the first frame of the scene
            first["J2"] = (c.drawn_xy().copy(), c.twinkle_factor().copy(), halo.fx_ambient.offset().copy(), fx.film.t, fx.film.gain, self.film_start)
            self.wait(self.scene_duration - self.now)

        run(scene("J1", ease, keep), fps=30)
        run(type("J2", (Narrated,), {"timings_file": path, "rest_ease": ease, "build": j2_first}), fps=30)
        (x1, w1, o1, t1, g1, _), (x2, w2, o2, t2, g2, start2) = keep["J1"], first["J2"]
        jump = float(np.abs(x1 - x2).max()) * 135
        if ease:
            check("clock: at a scene join idle motion is at rest on both sides (rest_ease), so the last and the first frame are one picture",
                  jump < 1e-9 and float(np.abs(w1 - w2).max()) < 1e-12 and float(np.abs(o1 - o2).max()) < 1e-12 and g1 == g2 == 0.0,
                  f"jump {jump:.2e} px; gains {g1}, {g2}")
        else:
            check("clock: without the rest ease the drift continues across the join on film time (one frame of motion, no jump)",
                  abs(start2 - 2.0) < 1e-9 and abs(t2 - t1 - 1 / 30) < 1e-9 and jump < 0.05 * 0.05 * 135 * 2, f"film {t1:.4f} -> {t2:.4f} s; jump {jump:.3f} px")

    c = DotCloud(sunflower_points(80, 1.0), color=DATA).drift(0.05, seed=2)
    order = np.random.default_rng(1).permutation(80)
    d = DotCloud(c.points[order], color=DATA, ids=c.ids[order]).drift(0.05, seed=2)
    c._drift["t"] = d._drift["t"] = 12.3
    part = c.split(np.arange(30))
    whole = DotCloud.join(c, part)
    back = np.argsort(order)
    check("clock: a point's drift depends on its id, not on its place in the array; ids and drift survive split and join",
          np.allclose(d.drawn_xy()[back], DotCloud(sunflower_points(80, 1.0), color=DATA).drift(0.05, seed=2).drawn_xy() * 0 + d.drawn_xy()[back])
          and np.allclose(DotCloud(c.points, ids=c.ids).drift(0.05, seed=2)._drift["ph"], c._drift["ph"])
          and sorted(whole.ids.tolist()) == list(range(80)) and whole._drift["w"].shape == (80, 2) and part.ids.tolist() == list(range(30)))

    class Spans(Narrated):
        timings_file = write_timings("Spans", 2.0, (0.2, 0.6))

        def build(self):
            self.errors = []
            for f in (lambda: self.word_span(0, "word", nth=0), lambda: self.word_span(0, " "), lambda: self.at(9), lambda: self.line_end(-1)):
                try:
                    f()
                    self.errors.append("no error")
                except TimingError as e:
                    self.errors.append(str(e))

    s = run(Spans)
    check("timing: word_span(nth=0), an empty word and a missing line are TimingErrors that name the scene",
          len(s.errors) == 4 and all(e.startswith("Spans:") for e in s.errors), " | ".join(e[:40] for e in s.errors))

    def until(frames, min_time=None):
        def build(self):
            d = Dot(color=MODEL)
            self.add(d)
            self.wait(0.6)
            kw = {} if min_time is None else {"min_time": min_time}
            self.play_until(self.now + frames / self.fps, d.animate.shift(RIGHT), **kw)
        return type("Until", (Narrated,), {"timings_file": write_timings("Until", 2.0, (0.2,)), "build": build})

    out = []
    for frames, mt in ((1, None), (3, None), (6, None), (0, 0.0)):
        try:
            run(until(frames, mt))
            out.append("ok")
        except TimingError:
            out.append("error")
    check("timing: play_until needs 0.3 s unless min_time=0 (a move does not silently become a pop)", out == ["error", "error", "ok", "ok"], str(out))

    def left_test(self):
        a = put(T("one event", "label"), -4, 0)
        self.at(0)
        self.left_seen = self.left(1.0)
        self.play_until(1.6, Wait(), timed(enter(a), 0.8))
        self.seen = a

    class Timer(Narrated):
        timings_file = write_timings("Timer", 2.0, (0.2,))
        build = left_test

    probe = {}
    orig = motion.Timed.interpolate

    def spy(self, alpha):
        probe.setdefault("calls", []).append((alpha, self.a, self.b))
        return orig(self, alpha)

    motion.Timed.interpolate = spy
    try:
        s = run(Timer, fps=30)
    finally:
        motion.Timed.interpolate = orig
    a0, a, b = probe["calls"][0]
    start = (round(0.2 * 30) - 1) / 30
    check("motion: timed(anim, t0) runs inside a longer play from t0 for its own run time; left(t) is the time to t",
          abs(a * (1.6 - start) + start - 0.8) < 0.02 and abs(b * (1.6 - start) + start - 1.8 if b < 1 else 0) < 0.02 and abs(s.left_seen - (1.0 - start)) < 1e-9,
          f"window {a:.3f} to {b:.3f} of a play from {start:.3f} s to 1.6 s")

    os.environ["EXPLAINER_QUALITY"] = "draft"
    os.environ["EXPLAINER_TIMINGS_USED"] = str(WORK / "used.json")
    try:
        class Stand(Narrated):
            timings_file = write_timings("Stand", 1.0)

            def build(self):
                pass

        try:
            run(Stand)
            stand = "no error"
        except TimingError as e:
            stand = str(e)
        os.environ["EXPLAINER_TIMINGS"] = str(write_timings("Pipe", 1.0))

        class Pipe(Narrated):
            def build(self):
                pass

        run(Pipe)
        used = json.loads((WORK / "used.json").read_text())
    finally:
        for k in ("EXPLAINER_QUALITY", "EXPLAINER_TIMINGS_USED", "EXPLAINER_TIMINGS"):
            os.environ.pop(k, None)
    check("timing: under render.py (EXPLAINER_QUALITY) a scene with its own timings_file stops; the timings used are written down",
          "must not set timings_file" in stand and used["key"] == "Pipe" and len(used["timings"]) == 16, f"{stand[:60]} | {used}")


# --------------------------------------------------------------------------- 11. lint coverage
def test_lint2() -> None:
    def rules(*mobs):
        return sorted({it["rule"] for it in check_layout(list(mobs))})

    from manim import Line as _Line, Rectangle as _Rect
    seen = []
    for length in (6, 12):
        line = _Line([-length / 2, 0, 0], [length / 2, 0, 0], stroke_width=W_LINE, color=GREY_2)
        seen += [rules(line, T("gate", "label").move_to([x, 0, 0])) == ["text-shape"] for x in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5)]
    box = _Rect(width=10, height=5, stroke_width=W_LINE, color=MODEL)
    seen += [rules(box, T("gate", "label").move_to([x, 2.5, 0])) == ["text-shape"] for x in np.linspace(-4, 4, 8)]
    check("lint: a label on a long line or a long edge is seen wherever it is (outlines are sampled by length)", all(seen), f"{sum(seen)} of {len(seen)}")
    on = [rules(RadialGlow(1.5, FOCUS), T("gate", "label")), rules(glow_sprite(1.5, FOCUS), T("gate", "label")),
          rules(Circle(radius=1.5, stroke_width=0, fill_color=MODEL, fill_opacity=0.8), T("gate", "label"))]
    off = [rules(RadialGlow(1.5, FOCUS), backstroke(T("gate", "label"))), rules(Circle(radius=1.5, stroke_width=0, fill_color=SLATE, fill_opacity=1), T("gate", "label")),
           rules(glow_sprite(0.5, FOCUS).move_to([-3, 0, 0]), T("gate", "label").move_to([2, 0, 0]))]
    check("lint: text on a glow, a picture or a bright fill without a backstroke is text-on-fill; a backstroke, a dark panel or distance pass",
          all(r == ["text-on-fill"] for r in on) and all(r == [] for r in off), f"{on} {off}")
    raw = Text("eight words of raw text in the system font", font_size=24, color=INK).move_to([0, 2, 0])
    check("lint: a Text not built with T() is text-face and its words are counted", rules(raw) == ["text-face"] and word_count([raw]) == 9, str(rules(raw)))
    check("lint: Manim's default colours are reported (Circle() is Manim red, Line() and Dot() are white); theme colours pass",
          rules(Circle()) == rules(_Line()) == rules(Dot()) == ["colour"] and rules(Circle(color=MODEL)) == rules(Dot(color=dim(FAIL, 0.4))) == [])
    try:
        T("first line\nsecond line", "label")
        nl = "accepted"
    except AssertionError as e:
        nl = str(e)
    check("type: T() refuses a newline", "lines()" in nl, nl)

    class Parts(Narrated):
        timings_file = write_timings("Parts", 3.0, (0.2, 1.5))

        def build(self):
            q = put(T("Which change helps most on new tests?", "body", parts={"k": "most on new tests"}), -SAFE_X, 1.4)
            n = LiveNumber(0, 1, "%", size="title", reserve=18.5).place([3, -1, 0])
            label = T("gate", "label").next_to(n, DOWN)
            self.add(q, n, label)
            self.counted = []
            n.add_updater(lambda m: self.counted.append(m.shown))
            self.play(q.part["k"].animate.set_color(FOCUS), count_to(n, 18.5), VGroup(n, label).animate.shift(UP * 0.5), run_time=0.6)
            self.after_colour = (word_count(self.mobjects), [type(m).__name__ for m in self.mobjects])
            self.play(FadeOut(q.part["k"]), run_time=0.4)
            self.after_fade = (word_count(self.mobjects), max(g.get_fill_opacity() for g in q.part["k"]),
                               any(g in self.get_mobject_family_members() for g in q.part["k"]))

    s = run(Parts)
    check("scene: animating a part of a text keeps the text whole (9 words: 7, the number, the label), and a number in an animated group counts",
          s.after_colour[0] == 9 and s.after_colour[1][:3] == ["Text", "LiveNumber", "Text"] and len(set(s.counted)) > 4, f"{s.after_colour}, {len(set(s.counted))} values")
    check("scene: a faded-out part leaves the screen, and the loose words left of its text are still counted by the lint (3 + the '?' of tests?)",
          not s.after_fade[2] and s.after_fade[0] == 6, f"{s.after_fade}")

    class Peak(Narrated):
        timings_file = write_timings("Peak", 4.0, (0.2, 3.5))

        def build(self):
            self.add(put(T("a world label that is cut", "label", MODEL), 2.4, 2.0))
            self.at(0)
            self.play(self.push_in([-1.0, 0.0, 0.0], 1.6, run_time=1.0))
            self.play(self.pull_back(run_time=1.0))

    class HandOver(Narrated):
        timings_file = write_timings("HandOver", 3.0, (0.2, 1.4, 2.5))

        def build(self):
            a, b = put(T("the pool", "label", DATA), 0, 0), put(T("one group", "label", FOCUS), 0.3, 0)
            c, d = put(T("copy A", "label"), -4, -1), put(T("copy B", "label"), -4, -1)
            self.add(a, c)
            self.at(0)
            self.play_until(self.line_start(1) + 0.6, hand_over(a, b), leave(c, rate_func=late(0, 0.5, EXIT)), enter(d, rate_func=late(0.5)))

    os.environ["EXPLAINER_LINT"] = "1"
    try:
        peak, hand = run(Peak), run(HandOver)
    finally:
        os.environ.pop("EXPLAINER_LINT")
    check("lint: it runs after every play, so a label cut at a push-in peak is found, and a hand-over across a line start is not an overlap",
          [it["rule"] for it in peak.lint_issues] == ["safe-area"] and hand.lint_issues == [], f"{[(i['rule'], i['time']) for i in peak.lint_issues]} {hand.lint_issues}")


# --------------------------------------------------------------------------- 12. motion and shapes
def test_motion2() -> None:
    cloud = DotCloud(field_points(200, 6, 3, seed=1), color=DATA, opacity=0.45)
    g = np.arange(50)
    ok = []
    for first in ("opacity", "colour"):
        cloud.set_opacities(0.45).set_colors(DATA)
        a1, a2 = cloud.to(opacity=0.8), cloud.to(color=FOCUS, idx=g, rate_func=window(0.3, 1.3, 2.0))
        anims = [a1, a2] if first == "opacity" else [a2, a1]
        for a in anims:
            a.begin()
        for al in np.linspace(0, 1, 13):
            for a in anims:
                a.interpolate(al)
        ok.append(np.allclose(cloud.rgbas[:, 3], 0.8) and np.allclose(cloud.rgbas[g, :3], ManimColor(FOCUS).to_rgb())
                  and np.allclose(cloud.rgbas[50:, :3], ManimColor(DATA).to_rgb()))
    check("fx: a colour to() and an opacity to() on one cloud share a play in either order (each owns its colour columns)", all(ok), str(ok))
    t = T("the strongest result in that family", "label")
    anim = enter(t, rate_func=late(0.7))
    anim.begin()
    starts = []
    for a in np.linspace(0, 1, 401):
        anim.interpolate(a)
        if not starts and t.family_members_with_points()[0].get_fill_opacity() > 0.02:
            starts.append(a)
    full = min(gl.get_fill_opacity() for gl in t.family_members_with_points())
    check("motion: enter(text, rate_func=late(0.7)) keeps the glyph stagger inside its window", starts and starts[0] >= 0.7 and full > 0.99, f"first glyph at {starts}")
    s = Stroke(np.column_stack([np.linspace(-6, 6, 400), np.sin(np.linspace(0, 6 * PI, 400)), np.zeros(400)]), W_BOLD)
    short = Stroke(np.array([[0, 0, 0], [1, 0, 0]]), W_BOLD)
    check("motion: a Stroke has one outline sample every 0.04 units (a long curve has no facets)", s.samples >= 400 and short.samples == 48 and len(s.points) > 3200,
          f"{s.samples} samples for {s.length:.1f} units")
    kinds = [type(x).__name__ for x in (born_from(cloud, Circle(color=MODEL)), hand_over(cloud, Circle(color=MODEL)),
                                         born_from(cloud, cloud.copy()), born_from(glow_sprite(0.5), Circle(color=MODEL)))]
    check("motion: born_from / hand_over grow a shape out of a cloud or a picture (no tangle of points); two equal clouds regroup",
          kinds == ["FadeIn", "AnimationGroup", "TransformFromCopy", "FadeIn"], str(kinds))
    f = pulses([0.5, 2.0], 3.0, 0.6)
    check("motion: pulses() gives one PULSE at each time of a play", f(0.0) == 0 and f(0.8 / 3) > 0.95 and f(1.5 / 3) == 0 and f(2.3 / 3) > 0.95)
    pts, fade = soft_field(500, 4.0, 3.0, seed=2, centre=(1, 0))
    rim = fade < 0.99
    check("fx: soft_field gives exactly n points inside a wavy outline, with a fade at its rim", len(pts) == 500 and fade.min() >= 0.3 - 1e-9
          and 0.05 < rim.mean() < 0.5 and np.abs(pts[:, 0] - 1).max() < 2.3, f"{rim.mean():.0%} of the points are in the rim")

    class Fly(Narrated):
        timings_file = write_timings("Fly", 3.0, (0.2,))

        def build(self):
            r = Runner(Line([-3, 0, 0], [3, 0, 0]), MODEL, duration=1.0, tail=0.4)
            self.play(r.run(), run_time=0.6)
            self.run_in = r in self.mobjects
            young = Runner(Line([-3, -1, 0], [3, -1, 0]), MODEL, duration=4.0, tail=1.2)
            young.set_time(0.3)
            self.young = (young.trail.widths[0], young.trail.widths[-1], young.trail.rgbas[0, 3])
            self.seen = []
            flier = Runner(Line([-3, 1, 0], [3, 1, 0]), FOCUS, duration=1.0, tail=0.3)
            watch = Dot(color=MODEL).add_updater(lambda m: self.seen.append(flier.core.get_fill_opacity()))
            self.add(watch)                         # a scene object: it updates after the animations of each frame
            self.play(LaggedStart(Wait(run_time=0.2), flier.flight(), lag_ratio=0.5), run_time=1.2)
            self.after = flier in self.get_mobject_family_members()

    s = run(Fly, fps=30)
    check("motion: run() is an animation on the runner (play adds it to the scene); a young tail tapers to nothing at its oldest end",
          s.run_in and s.young[0] == 0 and s.young[1] > 0 and s.young[2] == 0, f"in scene {s.run_in}; widths {s.young[0]:.3f} .. {s.young[1]:.3f}")
    check("motion: flight() fades the head in, runs, lets the tail in and is absorbed; inside a LaggedStart it waits for its turn",
          s.seen[0] == 0 and max(s.seen) == 1 and s.seen[-1] < 0.2 and not s.after, f"head opacity {s.seen[0]:.2f} -> {max(s.seen):.2f} -> {s.seen[-1]:.2f}")

    clock = ValueTracker(10.0)
    bar = LiveLength(0, start=(-5, -2, 0), unit=0.5, track=20, gate=20, notches=(5, 15)).follow(clock)
    bar.update(0)
    dial = Dial(0.25)
    area = Area(lambda x: 1.0, 0, 4, base=0).set_range(0, 2)
    check("shapes: LiveLength, Dial and Area draw a value as a length, an angle and an area, zero-based, without numbers",
          abs(bar.tip_point[0] - 0.0) < 1e-9 and bar.notches[0].get_stroke_opacity() > 0 and bar.notches[1].get_stroke_opacity() == 0
          and abs(dial.arc.get_top()[1] - dial.ring.get_top()[1]) < 0.01 and abs(dial.arc.get_right()[0] - dial.ring.get_right()[0]) < 0.01
          and dial.arc.get_left()[0] > -0.01 and abs(area.width - 2) < 1e-6 and abs(area.height - 1) < 1e-6)
    words_ = put(T("These were best cases", "body", parts={"k": "best cases"}), -3, 0)
    band = marker(words_.part["k"], FOCUS, of=words_)
    check("type: marker() starts at the phrase's left edge and runs from under the baseline to just over the x-height (below the capitals)",
          abs(band.get_left()[0] - words_.part["k"].get_left()[0]) < 1e-9 and band.get_top()[1] < words_.part["k"].get_top()[1] - 0.05
          and band.get_bottom()[1] < baseline_y(words_) < band.get_top()[1], f"band {band.get_bottom()[1]:.3f} to {band.get_top()[1]:.3f}")

    class Follow(Narrated):
        timings_file = write_timings("Follow", 1.0)

        def build(self):
            core = Circle(radius=1.0, color=MODEL).move_to([1, 0.5, 0])
            name = put(T("model", "label", MODEL), 1, 1.75, edge=ORIGIN)
            line = Stroke(np.array([[-5, -2, 0], [5, -2, 0]]), W_BOLD, GREY_1)
            self.add(core, name, line, self.hud_cite("first citation"), self.hud_cite("second citation", row=1))
            self.follow_label(name, core)
            keep_stroke(line, self.frame)
            gap0 = name.get_bottom()[1] - (core.get_top()[1] - self.frame.get_center()[1])
            self.play(self.push_in(core, 1.6, run_time=0.4))
            zoom = config.frame_width / self.frame.width
            top = (core.get_top()[1] - self.frame.get_center()[1]) * zoom
            self.result = (typekit.em(name) * 72, name.get_bottom()[1] - top, gap0, line.half * 2 * zoom * 100)
            self.cites = [baseline_y(m) for m in self._hud.values()]

    s = run(Follow)
    check("scene: follow_label keeps a label 24 on screen and at its gap from its object under a push-in; keep_stroke keeps a Stroke's width",
          abs(s.result[0] - 24) < 1e-6 and abs(s.result[1] - s.result[2]) < 0.01 and abs(s.result[3] - W_BOLD) < 1e-6, f"{np.round(s.result, 3)}")
    check("scene: hud_cite(row=1) sits one fine leading above row 0", np.allclose(s.cites, [FINE_Y, FINE_Y + 0.4]), str(s.cites))
    tex(r"\mathrm{x}^{2}", "body")
    check("tex: a formula is read from a private copy (no '_' file is left in the cache)", not list(paths.TEX_CACHE.glob("*_.svg")))


TESTS = {"motion": test_motion, "docs": test_docs, "fonts": test_fonts, "baselines": test_baselines, "number": test_number, "resolutions": test_resolutions,
         "timing": test_timing, "lint": test_lint, "fx": test_fx, "tex": test_tex, "rules": test_rules, "clock": test_clock, "lint2": test_lint2,
         "motion2": test_motion2}

if __name__ == "__main__":
    for name in (sys.argv[1:] or TESTS):
        try:
            TESTS[name]()
        except Exception:
            traceback.print_exc()
            check(f"{name}: ran to the end", False, "exception above")
    failed = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)} passed, {len(failed)} failed" + ("" if not failed else ": " + "; ".join(failed)))
    sys.exit(1 if failed else 0)
