"""Motion grammar: named rate functions, late landings, hand-overs, a tapered stroke, a runner with a tail,
ambient motion for holds, the sampling rhythm and count-ups.

    ENTER, MOVE, EXIT, CLOCK, COUNT, GLIDE, PULSE     the only rate functions a scene should need
    late, window, pulses, lag_for                     land a label late inside a play; several pulses; stagger by count
    timed                                             an animation that runs between two scene times inside a longer play
    enter, leave                                      the standard entrance and exit
    born_from, hand_over                              a new object comes from a copy of its source
    Stroke, draw                                      a stroke whose width tapers; drawn along its path
    Runner, fly                                       a glowing head with a fading tail on a path, in simulated time
    ambient, still                                    a slow seeded sway so that a hold is never frozen
    sampling_rhythm, Rhythm                           one slow draw, a few at about 0.45 s, then many per second
    count_to                                          drive a LiveNumber (and its geometry) from one ValueTracker
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from manim import (ORIGIN, Animation, AnimationGroup, Circle, FadeIn, FadeOut, FadeTransform, Mobject, ReplacementTransform,
                   Text, TransformFromCopy, UpdateFromAlphaFunc, ValueTracker, VGroup, VMobject, linear, rate_functions,
                   smooth, squish_rate_func, there_and_back)

from . import theme as th
from .fx import AmbientState, DotCloud, RasterLayer, Trail, _rgb, film, glow_sprite
from .type import LiveNumber, em

# --------------------------------------------------------------------------- rate functions
ENTER = rate_functions.ease_out_cubic       # things that arrive: fast start, soft landing
MOVE = smooth                               # A to B, morphs, regrouping
EXIT = rate_functions.ease_in_cubic         # things that leave: slow start, fast end
CLOCK = linear                              # simulated time, sweeps, tracing: a clock must not ease
COUNT = rate_functions.ease_out_cubic       # a number that runs fast and slows into its final value
GLIDE = rate_functions.ease_in_out_sine     # camera moves: the gentlest ease
PULSE = there_and_back                      # a colour or brightness pulse that returns


def late(start: float, end: float = 1.0, func=ENTER):
    """A rate function that does nothing until ``start`` and is finished at ``end`` (fractions of the play).

    ``FadeIn(label, rate_func=late(0.6))`` lets a label land in the last 40% of the play that moves its object,
    so the name arrives after the motion has started, in the same play.
    """
    return squish_rate_func(func, start, end)


def window(t0: float, t1: float, total: float, func=MOVE):
    """Like ``late`` but in seconds: the animation runs from ``t0`` to ``t1`` of a play that lasts ``total`` seconds.

    Inside ``play_until`` the total is ``self.left(t)``; ``timed()`` works the window out by itself."""
    return squish_rate_func(func, t0 / total, t1 / total)


def pulses(times, total: float, width: float = 0.6):
    """A rate function with one PULSE (there and back) at each of ``times`` (seconds from the start of a play of
    ``total`` seconds), each ``width`` seconds long: a light that flares on several words of one line, in one play."""
    starts, w = np.asarray(times, dtype=float) / total, width / total

    def f(alpha: float) -> float:
        u = (alpha - starts) / w
        return max([PULSE(float(x)) for x in u if 0.0 <= x <= 1.0], default=0.0)

    return f


class Timed(Animation):
    """Run ``anim`` from scene time ``t0`` to ``t1`` inside whatever play it is part of (see ``timed``)."""

    def __init__(self, anim: Animation, t0: float, t1: float | None = None):
        from manim.animation.animation import prepare_animation

        anim = prepare_animation(anim)                       # ``x.animate.set_color(...)`` works too
        self.inner, self.t0, self.t1, self.own = anim, float(t0), t1, float(anim.run_time)
        super().__init__(anim.mobject, run_time=anim.run_time, rate_func=linear, introducer=anim.is_introducer(),
                         remover=anim.is_remover(), suspend_mobject_updating=False)

    def _setup_scene(self, scene) -> None:
        self.start = float(getattr(scene, "_play_start", scene.renderer.time))
        present = getattr(scene, "_play_present", None)       # what was on screen before this play (kit Narrated)
        self.present = present if present is not None else {id(m) for m in scene.get_mobject_family_members()}
        self.inner._setup_scene(scene)

    def begin(self) -> None:
        total = max(float(self.run_time), 1e-9)
        t1 = self.t0 + self.own if self.t1 is None else float(self.t1)
        self.a = float(np.clip((self.t0 - self.start) / total, 0, 1))
        self.b = float(np.clip((t1 - self.start) / total, self.a, 1))
        self.inner.begin()
        present = getattr(self, "present", set())            # what the inner animation brings in (a copy, a new text)
        family = {id(m): m for top in [self.inner.mobject, *self.inner.get_all_mobjects()] for m in top.get_family()}
        self.newcomers = [m for k, m in family.items() if k not in present]   # hidden until the window opens
        self.was_hidden = [m.__dict__.get("fx_hidden") for m in self.newcomers]

    def _hide(self, hidden: bool) -> None:
        for m, was in zip(self.newcomers, self.was_hidden):
            if hidden:
                m.fx_hidden = True
            elif was is None:
                m.__dict__.pop("fx_hidden", None)            # back to the class default (some kit marks are always hidden)
            else:
                m.fx_hidden = was

    def interpolate(self, alpha: float) -> None:
        u = (1.0 if alpha >= self.a else 0.0) if self.b - self.a < 1e-9 else (alpha - self.a) / (self.b - self.a)
        self._hide(alpha < self.a and self.b - self.a >= 1e-9)
        self.inner.interpolate(float(np.clip(u, 0, 1)))

    def update_mobjects(self, dt: float) -> None:
        self.inner.update_mobjects(dt)

    def finish(self) -> None:
        self._hide(False)
        self.inner.finish()

    def clean_up_from_scene(self, scene) -> None:
        self._hide(False)
        self.inner.clean_up_from_scene(scene)

    def get_all_mobjects(self):
        return self.inner.get_all_mobjects()


def timed(anim: Animation, t0: float, t1: float | None = None) -> Animation:
    """``anim`` runs from scene time ``t0`` to ``t1`` (default: ``t0`` plus its own run time) inside a longer play.

    The window is worked out when the play begins, from its real start and run time, so it is right inside
    ``play_until`` and when the narration moves:
        self.play_until(self.line_end(2), big_move, timed(enter(label), *self.word_span(2, "gate")),
                        timed(leave(old), self.line_start(2)))     # leave() keeps its own 1 s
    Use it at the top level of a play, not inside a LaggedStart.
    """
    return Timed(anim, t0, t1)


def lag_for(n: int) -> float:
    """The stagger (lag_ratio) for ``n`` items: 2-5 items 0.3, 6-30 items 0.08, 31-300 items 0.015, more: 1 / n."""
    if n <= 5:
        return th.LAG_FEW
    if n <= 30:
        return th.LAG_SOME
    if n <= 300:
        return th.LAG_MANY
    return 1.0 / n


# --------------------------------------------------------------------------- entrances, exits, hand-overs
def _is_text(m) -> bool:
    return isinstance(m, (Text, LiveNumber)) or hasattr(m, "baseline_frac")


class _GlyphFade(FadeIn):
    """A glyph-by-glyph fade whose whole stagger lies inside the rate function's window: with ``late(0.7)`` the first
    glyph starts at 0.7 of the play, not earlier (Manim applies the rate function to each glyph after the stagger)."""

    def get_sub_alpha(self, alpha: float, index: int, num_submobjects: int) -> float:
        full = (num_submobjects - 1) * self.lag_ratio + 1
        return float(np.clip(self.rate_func(alpha) * full - index * self.lag_ratio, 0.0, 1.0))


def enter(mob, shift=None, run_time: float = th.T_ENTER, **kw) -> Animation:
    """The standard entrance. Text fades in glyph by glyph, left to right, without moving (moving text smears); the
    stagger stays inside ``late()`` / ``window()``. Anything else fades in with an optional small ``shift``. The
    object's updaters keep running (Manim's own FadeIn suspends them for the whole play); for an ``always_redraw``
    object use plain FadeIn."""
    kw.setdefault("rate_func", ENTER)
    kw.setdefault("suspend_mobject_updating", False)      # a pinned, following or running object stays live as it enters
    if _is_text(mob) and not isinstance(mob, LiveNumber) and shift is None:
        return _GlyphFade(mob, lag_ratio=0.08, run_time=run_time, **kw)
    return FadeIn(mob, shift=ORIGIN if shift is None else shift, run_time=run_time, **kw)


def leave(mob, shift=None, run_time: float = th.T_ENTER, **kw) -> Animation:
    """The standard exit: fade out, slow start and fast end."""
    kw.setdefault("rate_func", EXIT)
    kw.setdefault("suspend_mobject_updating", False)
    return FadeOut(mob, shift=ORIGIN if shift is None else shift, run_time=run_time, **kw)


def _same_words(a, b) -> bool:
    sa, sb = getattr(a, "spec", None), getattr(b, "spec", None)
    return bool(sa and sb and sa.get("string") == sb.get("string"))


def _em_of(m) -> float | None:
    """The em of a text, or of the first line of a block of text."""
    if isinstance(m, LiveNumber) or hasattr(m, "em_frac"):
        return em(m)
    return next((e for e in map(_em_of, m.submobjects) if e), None)


def _text_swap(old, new, run_time: float, **kw) -> Animation:
    """``old`` fades out on its way to the place and type size of ``new`` while ``new`` fades in, coming from the
    place and type size of ``old``. Both keep their proportions (FadeTransform stretches one into the box of the other)."""
    rate = kw.pop("rate_func", MOVE)
    a, b = _em_of(old), _em_of(new)
    k = b / a if a and b else 1.0
    return AnimationGroup(FadeOut(old, target_position=new.get_center(), scale=k, rate_func=rate),
                          FadeIn(new, target_position=old.get_center(), scale=1 / k, rate_func=rate), run_time=run_time, **kw)


def _painted(m) -> bool:
    """A cloud, a picture, a ribbon or a runner (or a group that holds one): FxCamera paints it from its own data,
    so its outline points cannot be morphed into a shape."""
    return isinstance(m, Runner) or any(isinstance(s, (DotCloud, RasterLayer, Trail)) for s in m.get_family())


def _same_cloud(a, b) -> bool:
    return isinstance(a, DotCloud) and isinstance(b, DotCloud) and a.n == b.n


def _size(m) -> float:
    return max(m.width, m.height, 1e-3)


def born_from(source, new, arc: float = 0.0, run_time: float = th.T_MOVE, **kw) -> Animation:
    """A new object comes into being from a copy of its source, so the eye sees where it comes from.

    source   a mobject (a copy of it becomes ``new``) or a point (``new`` grows out of that point)
    Shapes are morphed. Text is not (glyph morphs between two strings look broken): the same words at another size
    or place travel and change size; other words cross-fade while they travel. A DotCloud, a picture, a Trail or a
    Runner is not morphed either (it has no outline): ``new`` grows out of its centre, unless both are clouds of the
    same size, which regroup point by point. For one point of a cloud use ``born_from(cloud.points[i], new)``.
    ``new`` is added to the scene by the animation; ``source`` stays.
    """
    kw.setdefault("rate_func", MOVE)
    if not isinstance(source, Mobject):
        return FadeIn(new, target_position=np.array(source, dtype=float), scale=0.15, run_time=run_time, **kw)
    if (_painted(source) or _painted(new)) and not _same_cloud(source, new):
        return FadeIn(new, target_position=source.get_center(), scale=float(np.clip(_size(source) / _size(new), 0.05, 1.0)),
                      run_time=run_time, **kw)
    if _is_text(source) or _is_text(new):
        if _same_words(source, new):
            return FadeTransform(source.copy(), new, run_time=run_time, **kw)
        return _text_swap(source.copy(), new, run_time, **kw)
    return TransformFromCopy(source, new, path_arc=arc, run_time=run_time, **kw)


def hand_over(old, new, arc: float = 0.0, run_time: float = th.T_MOVE, **kw) -> Animation:
    """``old`` becomes ``new`` (old leaves the scene). Shapes morph; text travels and cross-fades (see ``born_from``);
    a cloud, picture, trail or runner shrinks into the place of ``new`` while ``new`` grows out of it (two clouds
    of the same size regroup point by point)."""
    kw.setdefault("rate_func", MOVE)
    if (_painted(old) or _painted(new)) and not _same_cloud(old, new):
        k = float(np.clip(_size(new) / _size(old), 0.05, 20.0))
        return AnimationGroup(FadeOut(old, target_position=new.get_center(), scale=k),
                              FadeIn(new, target_position=old.get_center(), scale=1 / k), run_time=run_time, **kw)
    if _is_text(old) or _is_text(new):
        if _same_words(old, new):
            return FadeTransform(old, new, run_time=run_time, **kw)
        return _text_swap(old, new, run_time, **kw)
    return ReplacementTransform(old, new, path_arc=arc, run_time=run_time, **kw)


# --------------------------------------------------------------------------- tapered stroke
class Stroke(VMobject):
    """A stroke whose width changes along its length (Cairo strokes cannot): a filled outline around a centre line.

    points   (N, 3) samples of the centre line (a VMobject is sampled for you)
    width    the full width in Manim stroke units (theme.W_LINE, W_BOLD, W_HERO), so it matches ordinary strokes
    taper    (head, tail): the share of the length over which the width grows from zero and falls back to zero
    ``set_span(a, b)`` shows only the part between the proportions a and b, with the taper applied to that part;
    ``draw(stroke)`` animates it. The outline has one sample every 0.04 units of length (48 to 720), chosen once, so
    a long curve has no facets and the point count never changes (safe in updaters).
    """

    SAMPLES, STEP = 48, 0.04

    def __init__(self, points, width: float = th.W_BOLD, color=th.INK, taper: tuple[float, float] = (0.25, 0.25),
                 opacity: float = 1.0, **kw):
        super().__init__(stroke_width=0, fill_color=color, fill_opacity=opacity, **kw)
        if isinstance(points, VMobject):
            rough = np.array([points.point_from_proportion(a) for a in np.linspace(0, 1, 160)])
            n = max(160, int(np.ceil(np.linalg.norm(np.diff(rough, axis=0), axis=1).sum() / 0.02)))
            points = rough if n == 160 else np.array([points.point_from_proportion(a) for a in np.linspace(0, 1, n)])
        self.line = np.asarray(points, dtype=float)
        seg = np.linalg.norm(np.diff(self.line, axis=0), axis=1)
        self.length = float(seg.sum())
        self.cum = np.concatenate([[0.0], np.cumsum(seg)]) / max(seg.sum(), 1e-12)
        self.samples = int(np.clip(np.ceil(self.length / self.STEP), self.SAMPLES, 720))
        self.half = width * 0.01 / 2
        self.taper = taper
        self.span = (0.0, 1.0)
        self.set_span(0.0, 1.0)

    def _at(self, a: np.ndarray) -> np.ndarray:
        return np.column_stack([np.interp(a, self.cum, self.line[:, k]) for k in range(3)])

    def set_span(self, a: float, b: float):
        self.span = (a, b)
        u = np.linspace(0, 1, self.samples)
        p = self._at(a + (b - a) * u)
        d = np.gradient(p, axis=0)
        n = np.column_stack([-d[:, 1], d[:, 0], 0 * d[:, 0]])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        head, tail = self.taper
        prof = np.ones_like(u)
        if head > 0:
            prof *= np.sin(np.clip(u / head, 0, 1) * np.pi / 2)
        if tail > 0:
            prof *= np.sin(np.clip((1 - u) / tail, 0, 1) * np.pi / 2)
        off = n * (self.half * prof)[:, None]
        self.set_points_as_corners([*(p + off), *(p - off)[::-1], (p + off)[0]])
        return self


def draw(stroke: Stroke, run_time: float = th.T_MOVE, rate_func=MOVE, **kw) -> Animation:
    """Animation: the stroke is drawn along its path from its start; the tip stays tapered while it travels."""
    stroke.set_span(0.0, 1e-4)
    return UpdateFromAlphaFunc(stroke, lambda m, a: m.set_span(0.0, max(a, 1e-4)), run_time=run_time, rate_func=rate_func, **kw)


# --------------------------------------------------------------------------- runner
class Runner(VGroup):
    """A glowing head with a tail that fades, on a path, in simulated time.

    path      a function of time t -> point (it may take an array of times), or an (N, 3) array of samples at equal
              time steps, or a VMobject (travelled at constant speed)
    duration  the simulated time at the end of the path (needed for an array or a VMobject; default 1.0)
    tail      seconds of history that stay visible; the tail is sampled from the path itself, so it is smooth at
              every frame rate and in every direction of travel. It tapers to nothing at its oldest end, also while
              the runner is younger than ``tail``.
    halo      the radius of the soft light round the head, in scene units (``glow`` is an older name for it)
    The clock is ``runner.clock`` (a ValueTracker). Three ways to move it:
      ``run(to)``      an animation ON THE RUNNER (``play`` adds the runner to the scene): the head runs to ``to`` and
                       stays lit there
      ``flight()``     an animation in which the head fades in, runs the whole path, its tail runs into it and it is
                       absorbed (fades out, and the runner leaves the scene). ``fly(path, colour)`` builds one
      ``start()``      the clock runs by itself (film time) through waits and other plays, until ``stop()``
    After the end of the path the head stays and the tail runs into it. A runner is positioned by its path only.
    """

    def __init__(self, path, color=th.FOCUS, duration: float | None = None, tail: float = 1.2, radius: float = th.DOT_R_HERO,
                 halo: float = 0.42, width: float | None = None, samples: int = 36, t: float = 0.0, glow: float | None = None, **kw):
        super().__init__(**kw)
        self.path, self.duration = _as_path(path, duration)
        self.tail_seconds, self.samples, self.radius = tail, samples, radius
        self.tail_width = 2 * radius * 0.8 if width is None else width
        self.rgb = _rgb(color)
        self.trail = Trail()
        self.halo = glow_sprite(halo if glow is None else glow, color)
        self.core = Circle(radius=radius, stroke_width=0, fill_color=th.hot(color, 0.72), fill_opacity=1)
        self.add(self.trail, self.halo, self.core)
        self.clock = ValueTracker(t)
        self.speed, self._film_seen = 0.0, None
        self.add_updater(Runner._sync)
        self._sync()

    @property
    def head(self) -> np.ndarray:
        return self.core.get_center()

    def suspend_updating(self, recursive: bool = True):
        """Not suspended: a runner goes on running while an animation (a fade, say) is played on it."""
        return self

    def _sync(self, dt: float = 0.0):
        if self.speed:
            if film.driven:                                  # film time: no frame is lost at a play boundary
                if self._film_seen is not None:
                    self.clock.increment_value(self.speed * (film.t - self._film_seen))
                self._film_seen = film.t
            elif dt:
                self.clock.increment_value(self.speed * dt)
        t = self.clock.get_value()
        here = self.path(np.array([min(max(t, 0.0), self.duration)]))[0]
        self.core.move_to(here)
        self.halo.move_to(here)
        lo, hi = max(t - self.tail_seconds, 0.0), min(t, self.duration)
        if hi - lo <= 1e-6:                             # no tail yet: keep the samples (at the head), with no width
            self.trail.set_samples(np.tile(here, (self.samples, 1)), np.zeros(self.samples), np.zeros((self.samples, 4)))
            return self
        ts = np.linspace(lo, hi, self.samples)
        pts = self.path(ts)
        age = (ts - lo) / (hi - lo)                                         # 0 = the oldest sample, 1 = now
        full = min(1.0, (hi - lo) / self.tail_seconds)                       # a young or a dying tail is short and faint
        inside = np.clip((np.linalg.norm(pts - here, axis=1) - 0.4 * self.radius) / (0.6 * self.radius), 0, 1)   # hidden under the core
        rgba = np.column_stack([np.tile(self.rgb, (self.samples, 1)), 0.9 * full * age ** 1.5 * inside])
        self.trail.set_samples(pts, self.tail_width * age ** 0.9, rgba)
        return self

    def set_time(self, t: float):
        self.clock.set_value(t)
        return self._sync()

    def set_presence(self, a: float):
        """Show the runner at a share ``a`` of its full light (head, halo and tail)."""
        for m in (self.core, self.halo, self.trail):
            m.set_fill(opacity=float(np.clip(a, 0, 1)))
        return self

    def run(self, to: float | None = None, run_time: float | None = None, rate_func=CLOCK) -> Animation:
        """An animation on the runner (``play`` adds it to the scene): advance the simulated time to ``to`` (default:
        the end of the path). The run time defaults to the simulated time that passes, so the screen shows the real
        evolution. The head stays lit where it stops."""
        to = self.duration if to is None else to
        run_time = max(to - self.clock.get_value(), 1e-3) if run_time is None else run_time
        return _RunClock(self, to, run_time=run_time, rate_func=rate_func)

    def flight(self, appear: float = 0.12, absorb: float = 0.3, run_time: float | None = None, rate_func=CLOCK,
               remove: bool = True) -> Animation:
        """An animation on the runner: the head fades in over the first ``appear`` of the play, runs the whole path,
        its tail runs into it, and it fades out over the last ``absorb`` (then it leaves the scene, unless
        ``remove=False``). It works in ``LaggedStart`` and with ``window()`` / ``timed()``: before its window the
        runner is not seen. The run time defaults to the path's duration plus the tail."""
        to = self.duration + self.tail_seconds
        run_time = max(to - self.clock.get_value(), 1e-3) if run_time is None else run_time
        return _RunClock(self, to, presence=(appear, absorb), remover=remove, run_time=run_time, rate_func=rate_func)

    def start(self, speed: float = 1.0):
        """Let the clock run by itself (during waits and other plays) until ``stop()``. It follows film time."""
        self.speed, self._film_seen = speed, (film.t if film.driven else None)
        return self

    def stop(self):
        self.speed, self._film_seen = 0.0, None
        return self


class _RunClock(Animation):
    """Drive a runner's clock (and, for a flight, its presence) from an animation whose mobject is the runner."""

    def __init__(self, runner: Runner, to: float, presence: tuple[float, float] | None = None, **kw):
        kw.setdefault("suspend_mobject_updating", False)
        super().__init__(runner, **kw)
        self.to, self.presence = float(to), presence

    def create_starting_mobject(self):
        return self.mobject                                  # nothing is interpolated from a copy

    def begin(self) -> None:
        self.t0 = float(self.mobject.clock.get_value())
        super().begin()

    def interpolate_mobject(self, alpha: float) -> None:
        a = float(self.rate_func(alpha))
        r = self.mobject
        r.clock.set_value(self.t0 + (self.to - self.t0) * a)
        if self.presence is not None:
            up, down = self.presence
            r.set_presence(min(1.0, a / up if up > 0 else 1.0, (1 - a) / down if down > 0 else 1.0) if a > 0 else 0.0)
        r._sync()


def fly(path, color=th.FOCUS, duration: float | None = None, tail: float = 0.6, appear: float = 0.12, absorb: float = 0.3,
        **kw) -> Animation:
    """A traveller that appears, flies along ``path``, lets its tail run in and is absorbed, as ONE animation:
        self.play(LaggedStart(*[fly(p, MODEL, rate_func=MOVE) for p in paths], lag_ratio=0.1), run_time=2.5)
        self.play_until(t, timed(fly(path, DATA), *self.word_span(2, "flows")))
    ``path`` is anything a Runner takes; ``rate_func``, ``run_time`` and ``remove`` go to ``Runner.flight``; the
    other keywords (radius, halo, width) to the Runner."""
    opts = {k: kw.pop(k) for k in ("rate_func", "run_time", "remove") if k in kw}
    return Runner(path, color, duration=duration, tail=tail, **kw).flight(appear, absorb, **opts)


def _as_path(path, duration: float | None):
    """Normalise a path to a function of an array of times that returns (n, 3) points, plus its duration."""
    if isinstance(path, VMobject):
        path = np.array([path.point_from_proportion(a) for a in np.linspace(0, 1, 400)])
        seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        duration = 1.0 if duration is None else duration

        def by_length(ts, path=path, cum=cum, duration=duration):
            s = np.clip(np.asarray(ts) / duration, 0, 1) * cum[-1]
            return np.column_stack([np.interp(s, cum, path[:, k]) for k in range(3)])

        return by_length, duration
    if callable(path):
        duration = 1.0 if duration is None else duration
        try:
            ok = np.shape(path(np.array([0.0, duration]))) == (2, 3)
        except Exception:
            ok = False
        if ok:
            return (lambda ts: np.asarray(path(np.asarray(ts)), dtype=float)), duration
        return (lambda ts: np.array([path(float(t)) for t in np.asarray(ts)], dtype=float)), duration
    from scipy.interpolate import CubicSpline

    pts = np.asarray(path, dtype=float)
    duration = 1.0 if duration is None else duration
    spline = CubicSpline(np.linspace(0, duration, len(pts)), pts)
    return (lambda ts: spline(np.clip(np.asarray(ts), 0, duration))), duration


# --------------------------------------------------------------------------- ambient motion
def _ambient_tick(m, dt):
    m.fx_ambient.t += dt


def ambient(mob, amp: float = th.AMBIENT_AMP, period: float = th.AMBIENT_PERIOD, seed: int = 0, pulse: float = 0.0):
    """Give ``mob`` a slow, seeded sway of ``amp`` scene units, so that a hold is never fully frozen. Returns mob.

    It is a paint-time offset (needs FxCamera): the object's points, its bounding box and every Transform stay exact.
    ``pulse`` also varies the brightness of sprites, clouds and trails by that share. Use it on art, never on text
    that must be read. A DotCloud has its own per-point version, ``cloud.drift()``.
    """
    still(mob)
    state = AmbientState(amp, period, seed, pulse)
    for m in mob.get_family():
        m.fx_ambient = state
    mob.add_updater(_ambient_tick)
    return mob


def still(mob):
    """Remove the ambient motion of ``mob``."""
    mob.remove_updater(_ambient_tick)
    for m in mob.get_family():
        m.fx_ambient = None
    return mob


# --------------------------------------------------------------------------- sampling rhythm
@dataclass
class Rhythm:
    """Start times of a run of draws, in seconds. ``total`` is when the last draw has had its time."""

    starts: np.ndarray
    total: float

    def windows(self, hold: float = 1.0) -> list[tuple[float, float]]:
        """(start, end) of every draw: each lasts ``hold`` times the gap to the next one."""
        gaps = np.diff(np.concatenate([self.starts, [self.total]]))
        return [(float(s), float(s + hold * g)) for s, g in zip(self.starts, gaps)]

    def group(self, anims, hold: float = 1.0, func=ENTER) -> AnimationGroup:
        """One animation per draw, each squeezed into its own window. Play the result with ``run_time=rhythm.total``."""
        for anim, (a, b) in zip(anims, self.windows(hold)):
            anim.run_time = self.total
            anim.rate_func = squish_rate_func(func, a / self.total, min(b / self.total, 1.0))
        return AnimationGroup(*anims, run_time=self.total)


def sampling_rhythm(n: int, total: float | None = None, slow: float = th.RHYTHM_SLOW, mid: float = th.RHYTHM_MID,
                    n_mid: int = th.RHYTHM_N_MID, fast: float = 12.0) -> Rhythm:
    """The rhythm that shows a process, not a chart: one slow draw, a few at about ``mid`` seconds, then many per second.

    n       the number of draws
    total   the seconds that all draws take together; if None, the rate rises until it reaches ``fast`` draws a second
    Draw 0 starts at 0 and takes ``slow`` seconds; the next ``n_mid`` take ``mid`` seconds each; the rest come at a
    rate that grows exponentially. Feed ``.starts`` to ``DotCloud.appear`` or use ``.group`` for separate animations.
    """
    head = np.concatenate([[0.0], slow + mid * np.arange(min(n_mid, max(n - 1, 0)))])[:n]
    m = n - len(head)
    t1 = slow + mid * n_mid
    if m <= 0:
        return Rhythm(head, float(head[-1] + (slow if n == 1 else mid)))
    r0 = 1.0 / mid
    if total is None:
        k = np.log(max(fast / r0, 1.0 + 1e-9))
        span = m * k / (r0 * (np.exp(k) - 1))
    else:
        span = total - t1
        assert span > 0, f"sampling_rhythm: total {total} s leaves no time after the slow and mid draws ({t1:.2f} s)"
        if m <= r0 * span:
            k = 0.0
        else:                                              # solve r0 * span * (e^k - 1) / k = m for k
            lo, hi = 1e-9, 60.0
            for _ in range(80):
                k = (lo + hi) / 2
                lo, hi = (k, hi) if r0 * span * np.expm1(k) / k < m else (lo, k)
    j = np.arange(m)
    tail = t1 + (span * j / m if k < 1e-8 else span / k * np.log1p(j * k / (r0 * span)))
    return Rhythm(np.concatenate([head, tail]), float(t1 + span))


# --------------------------------------------------------------------------- counting
def count_to(target, value: float, run_time: float = th.T_COUNT, rate_func=COUNT) -> Animation:
    """Animation: count to ``value``. ``target`` is a ValueTracker, or a LiveNumber (its own tracker is used).

    Tie the geometry to the same tracker (an updater that reads ``tracker.get_value()``), so that a quantity is
    shown twice from one source: a length and a number. The number must be in the scene (updaters run only there).
    """
    tracker = target
    if isinstance(target, LiveNumber):
        if target.tracker is None:
            target.follow()
        tracker = target.tracker
        if target.reserve is None or abs(value) > abs(target.reserve):
            target.reserve = value
            target.set_value(target.value)
    return tracker.animate(run_time=run_time, rate_func=rate_func).set_value(value)


__all__ = ["ENTER", "MOVE", "EXIT", "CLOCK", "COUNT", "GLIDE", "PULSE", "late", "window", "pulses", "lag_for", "timed", "Timed",
           "enter", "leave", "born_from", "hand_over", "Stroke", "draw", "Runner", "fly", "ambient", "still", "Rhythm",
           "sampling_rhythm", "count_to"]
