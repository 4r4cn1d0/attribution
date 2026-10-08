"""Measured shapes: a quantity drawn as a length, an angle or an area, driven by one ValueTracker. No numbers.

    LiveLength   a bar from a zero point, with a glowing end, optional notches, a zero tick, a track and a gate tick
    Dial         a ring with an arc for a share (a mini dial: the red share of a test)
    Area         the area under a curve between two x values, which can sweep

Each one has a fixed family and fixed point counts, so it is safe in updaters and under Transform. Drive it with
``follow(tracker)`` (the object must then be in the scene) and animate the tracker, or call ``set_value``.
"""

from __future__ import annotations

import numpy as np
from manim import PI, RIGHT, Circle, Line, ValueTracker, VGroup, VMobject

from . import theme as th
from .fx import glow_sprite


class LiveLength(VGroup):
    """A length that grows from ``start`` along ``direction``: ``value * unit`` scene units long.

    start, unit      the zero point and the scene units per unit of value (zero-based: there is no cut axis)
    track            draw a quiet hairline track from zero to this value (None: no track) and a zero tick
    gate             draw a gate tick at this value (the condition), W_BOLD, from 0.2 under to 0.8 over the bar
    notches          values at which a small notch crosses the bar once the bar has reached it
    halo             the radius of the glow at the end (0: no glowing end)
    ``bar``, ``tip``, ``zero``, ``track``, ``gate`` and ``notches`` are the parts. ``tip_point`` is the end now.
    """

    def __init__(self, value: float = 0.0, start=(0.0, 0.0, 0.0), unit: float = 0.5, color=th.INK, direction=RIGHT,
                 width: float = th.W_HERO, track: float | None = None, gate: float | None = None, notches=(), halo: float = 0.3,
                 tracker: ValueTracker | None = None, **kw):
        super().__init__(**kw)
        self.start, self.unit = np.array(start, dtype=float), float(unit)
        self.dir = np.array(direction, dtype=float) / np.linalg.norm(direction)
        self.normal = np.array([-self.dir[1], self.dir[0], 0.0])
        far = self._at(track) if track is not None else self.start + 1e-3 * self.dir
        self.track = Line(self.start, far, stroke_width=th.W_LINE, color=th.GREY_3)
        self.zero = Line(self.start - 0.2 * self.normal, self.start + 0.5 * self.normal, stroke_width=th.W_BOLD, color=th.GREY_1)
        g = self._at(gate if gate is not None else 0.0)
        self.gate = Line(g - 0.2 * self.normal, g + 0.8 * self.normal, stroke_width=th.W_BOLD, color=th.INK)
        self.notch_values = np.array(notches, dtype=float)
        self.notches = VGroup(*[Line(self._at(v) - 0.09 * self.normal, self._at(v) + 0.09 * self.normal, stroke_width=th.W_LINE,
                                     color=th.GREY_5) for v in self.notch_values])
        self.bar = Line(self.start, self.start + 1e-3 * self.dir, stroke_width=width, color=color)
        self.halo = glow_sprite(halo, color, peak=0.6) if halo > 0 else None
        self.tip = Circle(radius=width * 0.01 * 0.9, stroke_width=0, fill_color=th.hot(color, 0.6), fill_opacity=1 if halo > 0 else 0)
        for part, keep in ((self.track, track is not None), (self.zero, track is not None), (self.gate, gate is not None)):
            if not keep:
                part.set_stroke(opacity=0)
        self.add(self.track, self.zero, self.gate, self.bar, self.notches, *[x for x in (self.halo,) if x is not None], self.tip)
        self.tracker, self._follower = None, None
        self.set_value(value)
        if tracker is not None:
            self.follow(tracker)

    def _at(self, v: float) -> np.ndarray:
        return self.start + self.dir * float(v) * self.unit

    @property
    def tip_point(self) -> np.ndarray:
        return self._at(self.value)

    def set_value(self, value: float):
        """Show ``value``. Safe inside an updater: every part is moved in place."""
        self.value = float(value)
        end = self._at(max(self.value, 0.0))
        self.bar.put_start_and_end_on(self.start, end if np.linalg.norm(end - self.start) > 1e-3 else self.start + 1e-3 * self.dir)
        self.bar.set_stroke(opacity=1.0 if self.value > 1e-6 else 0.0)
        for v, n in zip(self.notch_values, self.notches):
            n.set_stroke(opacity=0.9 if self.value >= v else 0.0)
        if self.halo is not None:
            self.halo.move_to(end)
        self.tip.move_to(end)
        return self

    def follow(self, tracker: ValueTracker | None = None, fn=None):
        """Show ``fn(tracker.get_value())`` on every frame (``fn`` defaults to the identity). Returns self."""
        self.tracker = tracker if tracker is not None else ValueTracker(self.value)
        fn = fn or (lambda v: v)
        if self._follower is not None:
            self.remove_updater(self._follower)
        self._follower = lambda m: m.set_value(fn(m.tracker.get_value()))
        self.add_updater(self._follower)
        return self.set_value(fn(self.tracker.get_value()))


class Dial(VGroup):
    """A ring with an arc for a share of a whole (0..1): an angle, not a number.

    The arc starts at ``start_angle`` (default: the top) and runs clockwise. ``ring`` and ``arc`` are the parts.
    """

    SAMPLES = 64

    def __init__(self, share: float = 0.0, radius: float = 0.16, color=th.FAIL, ring_color=th.GREY_2, width: float = th.W_LINE,
                 arc_width: float | None = None, start_angle: float = PI / 2, clockwise: bool = True, **kw):
        super().__init__(**kw)
        self.radius, self.start_angle, self.sign = float(radius), float(start_angle), -1.0 if clockwise else 1.0
        self.ring = Circle(radius=radius, stroke_width=width, color=ring_color)
        self.arc = VMobject(stroke_width=arc_width or width * 1.5, stroke_color=color, fill_opacity=0)
        self.add(self.ring, self.arc)
        self.tracker, self._follower = None, None
        self.set_share(share)

    def set_share(self, share: float):
        """Show the share (clipped to 0..1). Safe inside an updater: the arc always has the same number of points."""
        self.share = float(np.clip(share, 0, 1))
        c = self.ring.get_center()
        a = self.start_angle + self.sign * 2 * PI * max(self.share, 1e-4) * np.linspace(0, 1, self.SAMPLES)
        self.arc.set_points_smoothly(c + self.radius * np.column_stack([np.cos(a), np.sin(a), 0 * a]))
        self.arc.set_stroke(opacity=1.0 if self.share > 1e-4 else 0.0)
        return self

    def follow(self, tracker: ValueTracker | None = None, fn=None):
        """Show ``fn(tracker.get_value())`` as the share on every frame. Returns self."""
        self.tracker = tracker if tracker is not None else ValueTracker(self.share)
        fn = fn or (lambda v: v)
        if self._follower is not None:
            self.remove_updater(self._follower)
        self._follower = lambda m: m.set_share(fn(m.tracker.get_value()))
        self.add_updater(self._follower)
        return self.set_share(fn(self.tracker.get_value()))


class Area(VMobject):
    """The area between a curve ``y = fn(x)`` and the line ``y = base``, from ``x0`` to ``x1`` (scene units).

    ``set_range(a, b)`` shows only the part between a and b (a sweep); ``follow(tracker)`` moves the right edge.
    No outline: draw the curve itself as a ``Stroke`` of the same samples (``Area.curve_points``).
    """

    SAMPLES = 160

    def __init__(self, fn, x0: float, x1: float, base: float = 0.0, color=th.INK, opacity: float = 0.18, **kw):
        super().__init__(stroke_width=0, fill_color=color, fill_opacity=opacity, **kw)
        self.fn, self.x0, self.x1, self.base = fn, float(x0), float(x1), float(base)
        self.tracker, self._follower = None, None
        self.set_range(x0, x1)

    def curve_points(self, a: float | None = None, b: float | None = None, n: int | None = None) -> np.ndarray:
        """(n, 3) points of the curve from a to b (default: the whole range)."""
        xs = np.linspace(self.x0 if a is None else a, self.x1 if b is None else b, n or self.SAMPLES)
        return np.column_stack([xs, [float(self.fn(x)) for x in xs], np.zeros(len(xs))])

    def set_range(self, a: float, b: float):
        """Show the area between x = a and x = b. Safe inside an updater (a fixed number of points)."""
        self.range = (float(a), float(max(b, a + 1e-4)))
        top = self.curve_points(*self.range)
        bottom = np.column_stack([top[::-1, 0], np.full(len(top), self.base), np.zeros(len(top))])
        self.set_points_as_corners([*top, *bottom, top[0]])
        return self

    def follow(self, tracker: ValueTracker, fn=None):
        """Sweep the right edge to ``fn(tracker.get_value())`` (an x value) on every frame. Returns self."""
        self.tracker, fn = tracker, fn or (lambda v: v)
        if self._follower is not None:
            self.remove_updater(self._follower)
        self._follower = lambda m: m.set_range(m.x0, float(np.clip(fn(m.tracker.get_value()), m.x0, m.x1)))
        self.add_updater(self._follower)
        self._follower(self)
        return self


__all__ = ["LiveLength", "Dial", "Area"]
