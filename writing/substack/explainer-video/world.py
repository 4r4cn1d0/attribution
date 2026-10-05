"""world.py: the one world of the explainer film (storyboard sections 3.1 to 3.12 and 4).

GUIDE FOR SCENE AUTHORS (read this, not the whole file)
=======================================================

1. Start from your pose, end in the next one
--------------------------------------------
    from kit import *
    import world

    class S07(Narrated):
        def build(self):
            w = world.pose("P06", self)          # scene N starts in pose P(N-1) ...
            ...                                  # ... and must end in exactly what world.pose("P07", ...) builds

``pose`` adds every object of the pose in its exact state, sets the camera on its station (and saves it, so
``pull_back()`` returns there), adds the tag when the pose has it, and returns a namespace ``w``. Check the joins:
render.py S07, then ``scenes/_pose_check.py S07`` (first.png against a still of P06, last.png against P07; it prints
the pixel differences and writes frames/<quality>/S07/posecheck.png). ``_pose_check.py --poses`` renders every pose
still, its lint and a contact sheet: those stills are the targets. A held pose matches its still to the pixel.

Coordinates: the question is in canvas coordinates; the pilot in P-local ones. ``world.PL(x, y)`` is the canvas
point of P-local (x, y) (canvas y = P-local y - 5.2); ``world.C(x, y)`` is a canvas point.

2. The namespace ``w`` (absent objects are None)
------------------------------------------------
  w.pool      Pool        700 post-training examples, 14 groups ("gA".."gD", "x0".."x9"), outlines, tints, marks
  w.model     Model       drawn back to front: model.behind (threads, S04), core disc, glow, rim,
                          model.between (beams, S11), 40 needles. Put threads/beams INTO those slots
  w.twin      Twin        the hollow gold twin (P04)
  w.test      TestArc     24 lights (rings, one core cloud, one haze cloud), the shade
  w.cost      CostFloor   floor line, 14 band segments, end tick, shortcut lane, mini dials
  w.lone      LonePoint   the point of the pilot before S06, canvas (-5.4, -5.4) = PL(-5.4, -0.2)
  w.boundary  Boundary    open along canvas y = -3.0 (S05 to S09) or closed round the emblem (S10, S11)
  w.emblem    Emblem      the drawn miniature of the pilot
  w.fork      Fork        start dot, event rings, bright paths with tails, breathing heads, ghosts, comparison
  w.bars      ChoiceBars  bars A and B (own widths), pointers, link, piles, lit segments
  w.strip     Strip       axis, ticks (one per distinct height), centre line, band, ghost edges
  w.field     Field       1,440 units (main or parked), family outline, lower-part curve, lit units u1 and u2
  w.ruler     Ruler       zero tick, tracks, condition line, two results (head, glow, trail), longer-horizon fork
  w.labels    dict        every string on screen, by its key in world.STRINGS ("data change", "copy A@bar", ...;
                          "about 18.5%" / "about 14.1%" are result rows with .about and .num)
  w.extra     dict        pulse (P00), safer (P02), threads (P04), beams, ranges, hairline, signoff (P11),
                          "strongest threads" (P09)
  w.tag       the HUD tag, when the pose has it on      w.question  [pool, model, test, cost floor]
  w.station   the camera station of the pose

3. How to change a lasting object
---------------------------------
Every lasting object is a ``Lasting`` (a VGroup) with a ``level`` ("dim, do not delete") and ``paint()``. Change it
ONLY through its methods: ``set_*`` changes at once (use it to set up); ``to_*`` returns an animation (a ``Tween``:
it moves state numbers and repaints, never stops idle motion; it takes run_time and rate_func and works inside
window()/timed()/late()). Do NOT FadeIn/FadeOut/``.animate`` a part of a lasting object: objects with idle motion
repaint their parts every frame. ``obj.to_level(0.35)`` dims, ``obj.to_level(1)`` restores; e.g. the world at 35%:
``*[o.to_level(0.35) for o in w.question]``. Idle motion (drift, tremble, breathing, glints) reads the film clock and
the kit's idle gain, so it rests by itself in the first and last 0.4 s of every scene: you need do nothing.

  Pool       outlines: set_outlines({"gA": .6}) / to_outlines({...}, lag); tints (S11): set_tints / to_tints;
             groups: gold(name), lift(name, dy, dx), remove_group(name) (0.6 up, 0.4 left, fade; holes stay),
             restore(name); set_gold / set_lift (immediate); marked points: set_marks / to_marks(level);
             pool.idx(name), pool.centre(name), pool.outline(name); pool.cloud is the kit DotCloud (to/appear/split).
  Model      PATTERNS "M0" "MA" "MB" "MC" "M*": set_pattern / to_pattern(name, lag) (ring by ring, outer first);
             ask() (12-degree flick, right to left, 0.4 s); to_still(0/1) (tremble off/on); glint(i);
             Model.rim_point(p).
  Twin       to_jitter(1/0) (seed 47: needles jump 6 a second, lights change at most twice a second; driven by the
             film clock, so it can run across S04 -> S05 and rests at every boundary); set_rest(). P04 builds it
             with jitter 0 (identical at rest): S05 sets ``w.twin.jitter = 1`` before its first play.
  TestArc    set_split / to_split(1, lag) (odd lights slide out to 3.95); set_states / to_states({k: "hollow" |
             "pale" | "red" | "dark" | "soft"}, lag); states_with(red, others, outer); set_shade_on / to_shade_on
             (the shade exists: S03 wipes it in); set_shade / to_shade (1 down, 0 lifted to its hairline);
             set_grey / to_grey (red shows grey while the camera is on the pilot); set_haze (soft halos, S03);
             pos(k). Lists: RED_FIRST, RED_INNER, RED_OUTER, INNER, OUTER, RETRAIN_RED, ROUNDS_INNER. ask_path(k).
  CostFloor  set_line / to_line(f) (drawn from the left); set_segments / to_segments(["none" | "outline" | "solid"]
             * 14, lag); set_tick; to_tick_down(1) (grows across the lane, S05); set_lane / to_lane(drawn);
             dial(i, share) -> a kit Dial on segment i (add it yourself, born from the lights).
  LonePoint  level (0.1 off frame, 1 at rest); ``swell`` (0..) swells the halo; the halo breathes.
  Boundary   set_open(); set_closed(centre, bright); Boundary.closed_curve(centre) for S10's Transform of
             ``boundary.curve`` (16 anchors in matching order: no twist); to_bright(x); to_glow(x).
  Emblem     Emblem(centre) (S10 builds it at PL(0, -0.6) and moves it to EMBLEM_HOME); level.
  Fork       set_nodes(a_nodes, b_nodes) (P-local, start first, head last; TOY.nodes / TOY.future_nodes);
             set_ghosts(TOY.ghost_edges(...)); to_paths(x); to_comparison(x); ``rings``; head_a, head_b.
  ChoiceBars set_widths / to_widths("A", probs); set_pointer / to_pointer("A", u, shown); set_link / to_link(uA,
             uB, shown); set_lit("A", seg, x); set_piles("A", counts); land("A", seg) (one more dot);
             to_outline_flash("A"); bar_x(u).
  Strip      set_band / to_band(half) (TOY.half[...]); add_tick(D) (30% + 10% per repeat, at most 70%);
             to_tick_dim(1/3); to_ghost(1/0) (the no-coordination edges at 30%); ``centre_hi``.
  Field      set_park / to_park(1); set_family / to_family(1); set_lower / to_lower(1); set_lit / to_lit("u1", 1);
             set_units / to_units(0.4); unit("u1"); FAMILY, LOWER, BLOOM_ORDER (seed 19), field_pos(i, park).
  Ruler      set_result(i, x, shown); run_x(t, t0, t1, L) and run2_start(t2, v1) are the runs of 3.6 (drive
             set_result from an updater that reads self.now, or from the film clock); to_track(1, 1) (draw track
             2, linear); to_condition(1); to_horizon(level); glimmer(); ``zero_flash``, ``zero_on``.

4. Camera, clock-driven motion, labels
--------------------------------------
STATIONS[name] = (centre, width): TEST-IN, W, STARE, WAYPOINT, SPECK, P, GAP. ``set_station(scene, name)``.
``clock_move(scene, station, t0, t1, rate=GLIDE, path=None)``: an updater (not a play) that from scene time t0
moves the frame from where it is to the station, arrives at t1 and removes itself; ``path=MOVE4`` for move 4
(straight down, a rounded turn that starts 0.6 s before the straight descent would end, the zoom only after the
pool has left the frame; checked at import). ``jitter(scene, seed, rate, t0, t1, apply)``: calls apply(k) (or
apply(k, rng)) for the k-th jump at t0 + k / rate, for every k before t1, several per frame if needed, then removes
itself; ``rand(seed, k, n)`` depends only on (seed, k). Both read the film clock, so plays never squeeze them.
``label(key)`` builds a string of 3.10 at its place, size and colour, with a backstroke; ``result_row("18.5%")``;
``riding_label("A", head)``; ``CITATION`` for hud_cite. ``follow(scene, label, anchor_of(key))``: a label that keeps
its size on screen and stays at its canvas place while the camera moves (use it for every label that is on screen
during a camera move; P03's ``held back`` is built this way).

5. The toy, seeds, checks (3.7, 3.12)
-------------------------------------
``TOY`` is computed at import by exact sums over every pair of futures; import fails if the guard of 3.7 fails.
TOY.probs(h), step(h, c), seg(p, u), y(h), X, h_event, h, bars["event" | "A1" | "B1" | "A2" | "B2"], nodes(copy, upto),
futures (40, seed 11, no coordination), future_nodes(f, copy), ghost_edges(), tick_counts(), tick_y(D),
var / mean / half / change ["none" | "straight" | "crossed"], outside, line5, line6 (landings: (form, k), seed 17),
landing(form, k) -> (uA, uB), pile_counts, final_link (0.46), grid_u(k).
SEEDS; EXTRA_GROUPS_SEED = 21 (searched from 21: the first that keeps the rules); MARKED (seven marked points,
seed-13 order) and THREAD_ENDS (70); FAMILY_PHASES (seed 37), LOWER_PHASE (seed 43); EMBLEM_FACTOR (0.65: with
0.58 a white dot is 0.015 from the mark at the drawn size). Import also checks: the 40-point groups and padded outlines do not touch,
u1 and u2 in the family, u2 under the wavy line and u1 above it, the thread of ``strongest`` to u1 clear of the
lower part, the emblem's clearance, move 4.

6. Passing objects
------------------
title_lines() (S02); Safer() (``safer?`` with its breathing backstroke); choice_ring(name); make_threads(level)
(S04, into model.behind); make_lens() / lens_check() / glyphs_in_place() (S01); PairingGlyph(oracle);
step_glyphs(); web() (S09: .art to bake, .run live); Lamp() (S10: attach(scene, w.question), move .x .y, .strength,
detach()); beam(name, opacity) (into model.between); ranges_hairline(); Range(name); sign_off().

7. Where this file departs from the storyboard text, and why (reported to the orchestrator)
------------------------------------------------------------------------------------------
- ``held back`` has its left edge at 4.85, not 4.9: at 4.9 its right end is at x 6.43, outside the safe area at W.
- ``full suppression`` on the 14.1% row sits 0.2 left of the row's ``about`` (right edge about -1.54), not at -1.2:
  the real ``about 14.1%`` spans x -1.34 to 1.45 (3.10 estimated -1.0), so at -1.2 the two overlap.
- The lens of S01 fails its own check (glyphs 0.007 apart, need 0.08): make_lens() raises; glyphs_in_place() is the
  storyboard's fallback.
- The emblem is drawn at 0.9 of 1.36 x 0.72 (EMBLEM_SCALE): at full size its zero tick and disc touch the closed
  curve's W_BOLD stroke. All its proportions are kept.
- The lower part's second curve is the seeded wavy line drawn across the family outline (the two close round the
  lower part): a padded hull of those units bulges or lies along the family outline.
- The field's two outlines use soft_hull() (an exactly padded convex hull); the kit's hull_blob bulges on wide sets.
- Strokes are world units: at TEST-IN, STARE and SPECK they are 1.36, 1.14 and 1.4 times wider on screen. Only text
  keeps its size (follow); keep_stroke is not applied in any pose.
"""

from __future__ import annotations

import inspect
import math
from types import SimpleNamespace

import numpy as np

from kit import *  # noqa: F401,F403  (Manim, the theme, type, fx, motion, shapes, Narrated)
from kit import fx as _fx
from kit.fx import _hash01

TAU_ = 2 * np.pi
DEG = np.pi / 180
FW = FRAME_W                      # 14.222...: the width of frame W
PY = -5.2                         # canvas y = P-local y + PY

# =================================================================================================== helpers


def C(x, y) -> np.ndarray:
    """A canvas point."""
    return np.array([float(x), float(y), 0.0])


def PL(x, y) -> np.ndarray:
    """The canvas point of P-local (x, y)."""
    return np.array([float(x), float(y) + PY, 0.0])


def rand(seed: int, k: int, n=None):
    """Uniform numbers in [0, 1) that depend only on (seed, k): the k-th jump of a seeded jitter."""
    return np.random.default_rng([int(seed), int(k)]).random(n)


def smoothstep(e0: float, e1: float, x):
    u = np.clip((np.asarray(x, dtype=float) - e0) / (e1 - e0), 0.0, 1.0)
    return u * u * (3 - 2 * u)


def _lerp(a, b, t):
    return a + (b - a) * t


def _resample(points: np.ndarray, closed: bool = False, step: float = 0.01) -> tuple[np.ndarray, np.ndarray]:
    """A polyline resampled by arc length. Returns (points, cumulative length)."""
    p = np.asarray(points, dtype=float)
    if p.shape[1] == 2:
        p = np.column_stack([p, np.zeros(len(p))])
    if closed:
        p = np.vstack([p, p[:1]])
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(int(cum[-1] / step), 8)
    s = np.linspace(0, cum[-1], n)
    q = np.column_stack([np.interp(s, cum, p[:, k]) for k in range(3)])
    return q, s


def soft_hull(points, pad: float = 0.06, n: int = 48, **style) -> VMobject:
    """A soft outline round a set of points: their convex hull padded by ``pad`` on every side (exactly), drawn as a
    smooth closed curve through ``n`` evenly spaced points of it. Unlike the kit's hull_blob it does not bulge out
    on a wide, flat set (the lower part of the family), so "pad 0.06" stays 0.06."""
    from scipy.spatial import ConvexHull
    p = np.asarray(points, dtype=float)[:, :2]
    ang = np.linspace(0, TAU_, 32, endpoint=False)
    ring = np.column_stack([np.cos(ang), np.sin(ang)]) * pad
    cloud = (p[:, None, :] + ring[None, :, :]).reshape(-1, 2)
    hull = cloud[ConvexHull(cloud).vertices]
    q, sarc = _resample(np.column_stack([hull, np.zeros(len(hull))]), closed=True, step=0.002)
    k = np.linspace(0, sarc[-1], n, endpoint=False)
    anchors = np.column_stack([np.interp(k, sarc, q[:, j]) for j in range(3)])
    return smooth_closed(anchors, **style)


def curve_samples(vm: VMobject, n: int = 240) -> np.ndarray:
    return np.array([vm.point_from_proportion(a) for a in np.linspace(0, 1, n)])


def polyline(points, color=INK, width=W_LINE, opacity=1.0) -> VMobject:
    m = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity, fill_color=color, fill_opacity=0)
    m.set_points_as_corners(np.asarray(points, dtype=float))
    return m


def dashed(points, color=FOCUS, width=W_LINE, opacity=1.0, dash: float = 0.09, gap: float = 0.065,
           closed: bool = True) -> VMobject:
    """A dashed line along a polyline as ONE VMobject (one subpath per dash): one stroke, cheap, no double light."""
    q, s = _resample(points, closed)
    m = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity, fill_color=color, fill_opacity=0)
    total, a = s[-1], 0.0
    n_d = max(int(round(total / (dash + gap))), 1)
    pitch = total / n_d
    for k in range(n_d):
        a = k * pitch
        ss = np.linspace(a, a + pitch * dash / (dash + gap), 4)
        pts = np.column_stack([np.interp(ss, s, q[:, j]) for j in range(3)])
        m.start_new_path(pts[0])
        m.add_points_as_corners(pts[1:])
    return m


def dots_along(points, step: float = 0.07, radius: float = 0.012, color=INK, opacity=1.0, fade=None) -> DotCloud:
    """A dotted line: dots every ``step`` along a polyline; ``fade(s)`` (s from 0 to 1) scales the opacity."""
    q, s = _resample(points, False, 0.002)
    k = np.arange(0, s[-1] + 1e-9, step)
    pts = np.column_stack([np.interp(k, s, q[:, j]) for j in range(3)])
    a = np.full(len(k), float(opacity))
    if fade is not None:
        a = a * np.array([fade(x / max(s[-1], 1e-9)) for x in k])
    return DotCloud(pts, radius=radius, color=color, opacity=a)


def text(s: str, size="label", color=INK, x=None, y=None, edge=LEFT, opacity: float = 1.0):
    """A string of the film: T() with a backstroke, placed by an edge and its baseline."""
    t = backstroke(T(s, size, color))
    put(t, x, y, edge=edge)
    if opacity < 1:
        t.set_opacity(opacity)
    return t


def row_right(parts, right: float, y: float, gap: float = 0.2) -> VGroup:
    """Strings on one baseline, ``gap`` apart, the right edge of the last at ``right`` (the result rows of S09)."""
    g = VGroup(*parts)
    x = right
    for p in reversed(parts):
        put(p, x, y, edge=RIGHT)
        x = p.get_left()[0] - gap
    return g


# =================================================================================================== animation


class Tween(Animation):
    """Move a state attribute of a lasting object to a value and repaint on every frame.

    ``lag`` (0..1) with ``order`` (one sort key per element of an array attribute) gives every element its own
    window, as Manim's lag_ratio does. The object's own updaters keep running (idle motion never stops).
    """

    def __init__(self, obj, attr: str, value, lag: float = 0.0, order=None, **kw):
        kw.setdefault("rate_func", MOVE)
        kw.setdefault("run_time", T_QUICK)
        super().__init__(obj, suspend_mobject_updating=False, **kw)
        self.attr, self.target, self.lag, self.order = attr, value, float(lag), order

    def create_starting_mobject(self):
        return Mobject()

    def begin(self) -> None:
        self.start = np.array(getattr(self.mobject, self.attr), dtype=float).copy()
        self.goal = np.broadcast_to(np.array(self.target, dtype=float), self.start.shape).copy()
        if self.start.ndim and self.lag > 0:
            n = self.start.shape[0]
            keys = np.arange(n) if self.order is None else np.asarray(self.order, dtype=float)
            rank = np.argsort(np.argsort(keys, kind="stable"), kind="stable") / max(n - 1, 1)
            self.delay = rank * self.lag
        else:
            self.delay = None
        super().begin()

    def interpolate_mobject(self, alpha: float) -> None:
        if self.delay is None:
            a = self.rate_func(alpha)
            val = self.start + (self.goal - self.start) * a
        else:
            local = np.clip((alpha - self.delay) / max(1 - self.lag, 1e-6), 0, 1)
            a = np.array([self.rate_func(float(x)) for x in local])
            a = a.reshape((-1,) + (1,) * (self.start.ndim - 1))
            val = self.start + (self.goal - self.start) * a
        setattr(self.mobject, self.attr, val if np.ndim(val) else float(val))
        self.mobject.paint()


class Lasting(VGroup):
    """A lasting object: a VGroup with a level (0..1, "dim, do not delete") and a paint() that draws its state."""

    idle = False                      # True: paint() runs on every frame (idle motion that reads the film clock)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.level = 1.0
        self.lamp = None              # S10: a function of positions (N, 3) -> 0..1, set by the Lamp
        if self.idle:
            self.add_updater(lambda m: m.paint())

    def lev(self, p=None):
        """The level of a part at position(s) p: the object's level, raised toward 1 under the lamp."""
        if self.lamp is None or p is None:
            return self.level
        return self.level + (1 - self.level) * self.lamp(np.atleast_2d(p))

    def paint(self):
        return self

    def set_level(self, x: float):
        self.level = float(x)
        return self.paint()

    def to_level(self, x: float, **kw) -> Animation:
        return Tween(self, "level", x, **kw)

    def tween(self, attr: str, value, **kw) -> Animation:
        return Tween(self, attr, value, **kw)


# =================================================================================================== camera

STATIONS = {
    "TEST-IN": ((1.6, 0.38), 10.46),
    "W": ((0.0, 0.0), FW),
    "STARE": ((2.4, 0.43), 12.47),
    "WAYPOINT": ((0.0, -5.4), FW),
    "SPECK": ((-5.4, -5.4), 10.16),
    "P": ((0.0, -5.2), FW),
    "GAP": ((0.3, -5.5), 13.17),
}
_LAST_SCENE = [None]


def _frame_of(target):
    return target.camera.frame if isinstance(target, Scene) else target


def set_station(scene, name: str) -> None:
    (cx, cy), width = STATIONS[name]
    frame = scene.camera.frame
    frame.set(width=width)
    frame.move_to(C(cx, cy))


def _scene_of(target):
    if isinstance(target, Scene):
        return target
    if _LAST_SCENE[0] is None:
        raise RuntimeError("world: pass the scene (clock_move(self, ...)), or call world.pose() first")
    return _LAST_SCENE[0]


def _scene_time(scene) -> float:
    return film_time() - float(getattr(scene, "film_start", 0.0))


def _driver(scene, fn):
    """An empty mobject at the FRONT of the scene list whose updater runs fn() on every frame (before every other
    updater, so labels that follow the camera see this frame's camera)."""
    d = Mobject()
    d.add_updater(lambda m: fn(m))
    scene.add(d)
    scene.bring_to_back(d)
    return d


def _move4_path():
    """Move 4 (S05): W straight down toward (0, -5.4), a rounded turn, left to SPECK; the frame narrows only when
    the pool's lowest point has left the top of the frame. Returns path(s) -> (cx, cy, width), s = 0..1 by length."""
    T4, lead = 3.4, 0.6
    u_turn = (T4 / 2 - lead) / T4                      # the unrounded descent would end at half of a GLIDE
    s_turn = (1 - math.cos(math.pi * u_turn)) / 2
    r = (5.4 - s_turn * 10.8) / (1 - s_turn * 2 + s_turn * math.pi / 2)   # (5.4 - r) = s_turn * L(r)
    r = 5.4 - s_turn * (10.8 - 2 * r + math.pi * r / 2)
    for _ in range(50):                                # solve 5.4 - r = s_turn * (10.8 - 2r + pi r / 2)
        r = 5.4 - s_turn * (10.8 - 2 * r + math.pi * r / 2)
    a, arc = 5.4 - r, math.pi * r / 2
    L = 2 * a + arc
    pool_low = POOL_BOX[2] - 0.12                      # the lowest point of the pool with its drift and radius

    def centre(d):
        if d <= a:
            return 0.0, -d
        if d <= a + arc:
            phi = (d - a) / r
            return -r + r * math.cos(phi), -(a) - r * math.sin(phi)
        return -r - (d - a - arc), -5.4

    d_zoom = None                                     # the first length at which the pool has left at full width
    for d in np.linspace(0, L, 2001):
        if centre(d)[1] + FW * 9 / 32 < pool_low:
            d_zoom = float(d)
            break
    s_zoom = d_zoom / L

    def path(s):
        cx, cy = centre(float(np.clip(s, 0, 1)) * L)
        k = float(smoothstep(s_zoom, 1.0, s))
        return cx, cy, FW + (STATIONS["SPECK"][1] - FW) * k

    path.radius, path.s_zoom, path.length = r, s_zoom, L
    return path


def clock_move(target, station: str, t0: float, t1: float, rate=GLIDE, path=None):
    """Clock-driven camera move (3.9, item 10). ``target`` is the scene (or its frame, after world.pose()).
    From scene time t0 the frame moves from where it is then to ``station`` and arrives at t1; then the updater
    removes itself. ``path(s) -> (cx, cy, width)`` with s = rate(u) replaces the straight interpolation (MOVE4)."""
    scene = _scene_of(target)
    frame = scene.camera.frame
    (tx, ty), tw = STATIONS[station]
    state = {"from": None}

    def step(m):
        t = _scene_time(scene)
        if t < t0 - 1e-9:
            return
        if state["from"] is None:
            state["from"] = (frame.get_center().copy(), float(frame.width))
        u = min(max((t - t0) / max(t1 - t0, 1e-9), 0.0), 1.0)
        s = rate(u)
        if path is not None:
            cx, cy, w = path(s)
            c = C(cx, cy)
        else:
            c0, w0 = state["from"]
            c, w = _lerp(c0, C(tx, ty), s), w0 + (tw - w0) * s
        if u >= 1.0:
            c, w = C(tx, ty), tw
        frame.set(width=w)
        frame.move_to(c)
        if u >= 1.0:
            m.clear_updaters()

    return _driver(scene, step)


def jitter(target, seed: int, rate: float, t0: float, t1: float, apply):
    """Seeded clock-driven jumps (3.9, item 11): apply(k) for the k-th jump at scene time t0 + k / rate, for every
    k whose time is before t1 (several in one frame if the rate is above the frame rate), then it removes itself.
    The jumps depend only on the seed and k: ``rand(seed, k)`` or the rng passed as a second argument."""
    scene = _scene_of(target)
    two = len([p for p in inspect.signature(apply).parameters.values()
               if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]) >= 2
    last = [-1]
    k_end = max(int(math.ceil((t1 - t0) * rate - 1e-9)) - 1, -1)      # the last k with t0 + k / rate < t1

    def step(m):
        t = _scene_time(scene)
        if t < t0 - 1e-9:
            return
        k_now = min(int(math.floor((t - t0) * rate + 1e-9)), k_end)
        for k in range(last[0] + 1, k_now + 1):
            apply(k, np.random.default_rng([int(seed), int(k)])) if two else apply(k)
        last[0] = max(last[0], k_now)
        if t >= t1 - 1e-9 or last[0] >= k_end:
            m.clear_updaters()

    return _driver(scene, step)


def follow(scene, label, anchor, edge=LEFT):
    """A world label that keeps its size class on screen and stays at the screen place of its canvas ``anchor``
    (the point where 3.10 places it: its edge x and baseline y) while the camera moves. Place the label at its
    anchor as if the camera were at W (``world.label(key)`` does), then call this. Works at any station."""
    frame = scene.camera.frame
    a = np.array(anchor, dtype=float)

    def on_screen(p):
        return (p - frame.get_center()) * FW / float(frame.width)

    label.shift(on_screen(a) - a)                       # at W this is no shift: screen = canvas
    set_pinned(label)
    off = label.get_center() - on_screen(a)
    label.add_updater(lambda m: m.shift(on_screen(a) + off - m.get_center()))
    return label


# =================================================================================================== seeds

SEEDS = dict(pool=7, extra_groups_from=21, patterns=3, threads=13, futures=11, jumps=12, piles=17, bloom=19,
             halo=29, breath=31, family=37, web=41, lower=43, twin=47)

# =================================================================================================== the pool

POOL_N = 700
POOL_BOX = (-6.2, -1.9, -0.9, 2.8)                 # x0, x1, y0, y1
POOL_CENTRE = C(-4.05, 0.95)
GROUP_CENTRES = {"gA": C(-5.1, 2.0), "gB": C(-5.2, 0.0), "gC": C(-2.95, 2.0), "gD": C(-3.1, 0.15)}
LABEL_SLOT = (-6.1, -1.4)
LENS_CENTRE, LENS_R, LENS_N, LENS_MAG = C(-3.9, 0.9), 1.0, 20, 2.5


def _make_pool():
    pts, fade = soft_field(POOL_N, 5.2, 4.4, seed=SEEDS["pool"], centre=(-4.05, 0.95))
    p = pts[:, :2]
    lo, hi = p.min(axis=0), p.max(axis=0)
    box0, box1 = np.array([POOL_BOX[0], POOL_BOX[2]]), np.array([POOL_BOX[1], POOL_BOX[3]])
    p = box0 + (p - lo) / (hi - lo) * (box1 - box0)        # exactly x -6.2 to -1.9, y -0.9 to 2.8
    rng = np.random.default_rng(SEEDS["pool"])
    u, v = rng.random(POOL_N), rng.random(POOL_N)
    rho = np.hypot((p[:, 0] - POOL_CENTRE[0]) / 2.15, (p[:, 1] - POOL_CENTRE[1]) / 1.85)
    radii = 0.028 + 0.022 * np.clip(1 - rho, 0, 1) ** 0.8 * (0.55 + 0.45 * u)
    alpha = 0.35 + 0.60 * np.clip(0.55 * (fade - 0.3) / 0.7 + 0.45 * v, 0, 1)
    return np.column_stack([p, np.zeros(POOL_N)]), radii, alpha


POOL_PTS, POOL_RADII, POOL_ALPHA = _make_pool()

MOVE4 = _move4_path()                        # the rounded path of camera move 4 (S05): clock_move(..., path=MOVE4)
for _s in np.linspace(0, 1, 401):            # the build check of 3.1: the frame narrows only once the pool has left
    _cx, _cy, _w = MOVE4(_s)
    if _w < FW - 1e-9 and _cy + _w * 9 / 32 >= POOL_BOX[2] - 0.12:
        raise RuntimeError("world: move 4 narrows before the pool's lowest point has left the top of the frame")


def _nearest(points, centre, n):
    d = np.linalg.norm(points[:, :2] - np.asarray(centre)[:2], axis=1)
    return np.sort(np.argsort(d, kind="stable")[:n])


def _hull_poly(points, pad):
    """The outline points of hull_blob(points, pad) (as a polygon, for the touch checks)."""
    return curve_samples(hull_blob(points, pad=pad), 160)[:, :2]


def _poly_gap(a, b) -> float:
    """The smallest distance between two closed polygons (0 if they cross or one is inside the other)."""
    if _fx._inside(b, a).any() or _fx._inside(a, b).any():
        return 0.0
    d = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1))
    return float(d.min())


def _extra_groups(seed: int):
    """The ten extra groups for one seed (dart throwing over interior pool points), or None if the rule fails."""
    rng = np.random.default_rng(seed)
    base = {k: _nearest(POOL_PTS, c, 40) for k, c in GROUP_CENTRES.items()}
    used = np.zeros(POOL_N, bool)
    for idx in base.values():
        used[idx] = True
    rho = np.hypot((POOL_PTS[:, 0] - POOL_CENTRE[0]) / 2.15, (POOL_PTS[:, 1] - POOL_CENTRE[1]) / 1.85)
    cand = [i for i in rng.permutation(POOL_N) if not used[i]]
    centres = []
    for i in cand:
        c = POOL_PTS[i, :2]
        if all(np.linalg.norm(c - g[:2]) >= 0.95 for g in GROUP_CENTRES.values()) and \
           all(np.linalg.norm(c - q) >= 0.7 for q in centres):
            centres.append(c)
        if len(centres) == 10:
            break
    if len(centres) < 10:
        return None
    groups = {f"x{j}": _nearest(POOL_PTS, c, 8) for j, c in enumerate(centres)}
    allg = {**base, **groups}
    flat = np.concatenate(list(allg.values()))
    if len(np.unique(flat)) != len(flat):
        return None
    polys = {k: _hull_poly(POOL_PTS[v], 0.12) for k, v in allg.items()}
    names = list(polys)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if _poly_gap(polys[a], polys[b]) <= 0.0:
                return None
    return groups


def search_extra_groups(start: int = 21, tries: int = 400) -> int:
    """The first seed from ``start`` whose ten groups keep every rule of 3.5 (run once; the result is stored)."""
    for s in range(start, start + tries):
        if _extra_groups(s) is not None:
            return s
    raise RuntimeError("world: no seed for the ten extra groups")


EXTRA_GROUPS_SEED = 21                       # found by search_extra_groups(21); verified below
_EXTRA = _extra_groups(EXTRA_GROUPS_SEED)
if _EXTRA is None:
    raise RuntimeError(f"world: the stored seed {EXTRA_GROUPS_SEED} of the ten extra groups no longer keeps the rules "
                       f"of 3.5; run world.search_extra_groups() and store the seed it returns")
GROUPS = {**{k: _nearest(POOL_PTS, c, 40) for k, c in GROUP_CENTRES.items()}, **_EXTRA}
GROUP_NAMES = list(GROUPS)                   # gA, gB, gC, gD, x0 .. x9
EXTRA_NAMES = [n for n in GROUP_NAMES if n.startswith("x")]
GROUP_POLYS = {k: _hull_poly(POOL_PTS[v], 0.12) for k, v in GROUPS.items()}


def _inside_outline(i: int, name: str) -> bool:
    return bool(_fx._inside(POOL_PTS[i:i + 1, :2], GROUP_POLYS[name])[0])


def search_marked(seed: int = 13, n_ends: int = 70):
    """The seven marked points (the first seven pool indices in seed order that keep the rules of Object 1: none in
    gB, at most one in any other outline, 0.8 or more apart) and the 70 thread ends (the marked seven and the
    next 63 in seed order)."""
    order = np.random.default_rng(seed).permutation(POOL_N)
    marked, per = [], {}
    for i in order:
        if _inside_outline(i, "gB"):
            continue
        inside = [k for k in GROUP_NAMES if k != "gB" and _inside_outline(i, k)]
        if any(per.get(k, 0) >= 1 for k in inside):
            continue
        if any(np.linalg.norm(POOL_PTS[i, :2] - POOL_PTS[j, :2]) < 0.8 for j in marked):
            continue
        marked.append(int(i))
        for k in inside:
            per[k] = per.get(k, 0) + 1
        if len(marked) == 7:
            break
    ends = list(marked) + [int(i) for i in order if int(i) not in marked][: n_ends - len(marked)]
    return marked, ends


MARKED, THREAD_ENDS = search_marked(SEEDS["threads"])
if len(MARKED) != 7:
    raise RuntimeError("world: fewer than seven marked points keep the rules of Object 1")

# =================================================================================================== the model

M_C = C(0.5, 0.55)
M_R = 1.15
RINGS = [(8, 0.35, 0.20), (14, 0.65, 0.05), (18, 0.95, 0.12)]     # count, radius, angular offset (rad)
NEEDLE_LEN = 0.22


def _needle_layout():
    pos, phi, ring = [], [], []
    for r_i, (n, r, off) in enumerate(RINGS):
        for j in range(n):
            a = off + TAU_ * j / n
            pos.append([r * math.cos(a), r * math.sin(a), 0.0])
            phi.append(a)
            ring.append(r_i)
    return np.array(pos), np.array(phi), np.array(ring)


NEEDLE_POS, NEEDLE_PHI, NEEDLE_RING = _needle_layout()


def _pattern(A1, p1, A2, p2, tilt):
    return NEEDLE_PHI + np.pi / 2 + A1 * np.sin(2 * NEEDLE_PHI + p1) + A2 * np.sin(3 * NEEDLE_PHI + p2) + np.asarray(tilt)[NEEDLE_RING]


def _patterns():
    out = {"M0": _pattern(0.55, 0.3, 0.25, 1.1, (0.0, 0.35, -0.2))}
    rng = np.random.default_rng(SEEDS["patterns"])
    for name in ("MA", "MB", "MC"):
        out[name] = _pattern(rng.uniform(0.3, 0.8), rng.uniform(0, TAU_), rng.uniform(0.1, 0.4), rng.uniform(0, TAU_),
                             rng.uniform(-0.6, 0.6, 3))
    out["M*"] = out["M0"] + rng.uniform(-1, 1, 40) * 15 * DEG                     # the supposed tuning: a little shift
    return out


PATTERNS = _patterns()
_NS = np.linspace(-0.5, 0.5, 13)
_NW = np.sin(np.clip((0.5 - np.abs(_NS)) / 0.3, 0, 1) * np.pi / 2)


class Needle(VMobject):
    """A tapered needle (a filled lens shape, or its outline when hollow); set_angle keeps the point count."""

    def __init__(self, centre, length=NEEDLE_LEN, half=W_LINE * 0.005, color=MODEL, hollow=False, **kw):
        super().__init__(stroke_color=color, stroke_width=W_HAIR if hollow else 0, stroke_opacity=1.0,
                         fill_color=color, fill_opacity=0.0 if hollow else 1.0, **kw)
        self.c, self.L, self.half, self.angle = np.array(centre, dtype=float), float(length), float(half), 0.0
        self.set_angle(0.0)

    def set_angle(self, a: float):
        self.angle = float(a)
        u = np.array([math.cos(a), math.sin(a), 0.0])
        n = np.array([-math.sin(a), math.cos(a), 0.0])
        s = (_NS * self.L)[:, None]
        w = (_NW * self.half)[:, None]
        top, bot = self.c + s * u + w * n, self.c + s * u - w * n
        self.set_points_as_corners([*top, *bot[::-1], top[0]])
        return self


class Model(Lasting):
    """The model (Object 2). Drawing order: behind (threads), core disc, glow, rim, between (beams), needles."""

    idle = True

    def __init__(self, pattern: str = "M0"):
        super().__init__()
        self.behind = VGroup()
        self.core = Circle(radius=M_R, stroke_width=0, fill_color=BG, fill_opacity=0.85).move_to(M_C)
        self.glow = glow_sprite(1.7, MODEL, peak=0.22).move_to(M_C)
        self.rim = Circle(radius=M_R, stroke_color=MODEL, stroke_width=W_LINE, stroke_opacity=0.4, fill_opacity=0).move_to(M_C)
        self.between = VGroup()
        self.needles = VGroup(*[Needle(M_C + p) for p in NEEDLE_POS])
        self.add(self.behind, self.core, self.glow, self.rim, self.between, self.needles)
        self.angles = PATTERNS[pattern].copy()
        self.flick = np.zeros(40)
        self.bright = np.zeros(40)            # 0..1: a needle glints (S01)
        self.still = 1.0                      # 0: the needles hold still (no tremble)
        h = _hash01(SEEDS["patterns"] + 100, np.arange(40), 2)
        self._tw, self._tp = TAU_ / (2.2 + 1.6 * h[:, 0]), TAU_ * h[:, 1]
        self.paint()

    def paint(self):
        g, t = idle_gain(), film_time()
        tremble = g * self.still * 1.5 * DEG * np.sin(self._tw * t + self._tp)
        xw = M_C[0] - 1.9 + 3.8 * ((t % 5.0) / 2.0)                     # a slow wave of light, once every 5 s
        wave = g * np.exp(-(((M_C[0] + NEEDLE_POS[:, 0]) - xw) / 0.45) ** 2)
        lev = self.lev(M_C + NEEDLE_POS)
        lev = np.broadcast_to(lev, (40,))
        for i, nd in enumerate(self.needles):
            nd.set_angle(self.angles[i] + self.flick[i] + tremble[i])
            hot_ = min(0.45 * wave[i] + self.bright[i], 1.0)
            nd.set_fill(mix(MODEL, MODEL_HI, hot_), opacity=float(lev[i]))
        lv = float(np.mean(lev)) if self.lamp is not None else self.level
        self.core.set_fill(opacity=0.85 * lv)
        self.glow.set_fill(opacity=lv)
        self.rim.set_stroke(opacity=0.4 * lv)
        return self

    def set_pattern(self, name: str):
        self.angles = PATTERNS[name].copy()
        return self.paint()

    def to_pattern(self, name: str, lag: float = 0.5, **kw) -> Animation:
        """The needles turn to a pattern, ring by ring (outer ring first), each by its shorter turn."""
        target = PATTERNS[name].copy()
        d = (target - self.angles + np.pi / 2) % np.pi - np.pi / 2
        kw.setdefault("run_time", T_MOVE)
        return Tween(self, "angles", self.angles + d, lag=lag, order=-NEEDLE_RING + 0.01 * np.arange(40), **kw)

    def ask(self, run_time: float = 0.4) -> Animation:
        """Asked: the needles flick 12 degrees in a wave from right to left."""
        order = -(NEEDLE_POS[:, 0])
        rank = (order - order.min()) / max(np.ptp(order), 1e-9)

        def f(m, a):
            local = np.clip((a - 0.5 * rank) / 0.5, 0, 1)
            m.flick = 12 * DEG * np.sin(np.pi * local)
            m.paint()

        return UpdateFromAlphaFunc(self, f, run_time=run_time, rate_func=linear, suspend_mobject_updating=False)

    def to_still(self, x: float, **kw) -> Animation:
        return Tween(self, "still", x, **kw)

    def glint(self, i: int, run_time: float = 0.5) -> Animation:
        def f(m, a):
            m.bright[i] = math.sin(math.pi * a)
            m.paint()

        return UpdateFromAlphaFunc(self, f, run_time=run_time, rate_func=linear, suspend_mobject_updating=False)

    @staticmethod
    def rim_point(p) -> np.ndarray:
        v = np.array(p, dtype=float) - M_C
        return M_C + M_R * v / max(np.linalg.norm(v), 1e-9)


TWIN_C = C(0.5, -1.45)
TWIN_LIGHT_ANGLES = (-20, -10, 0, 10, 20)


class Twin(Lasting):
    """The hollow gold twin (S04, S05): half size at (0.5, -1.45), outline needles, five hollow lights."""

    idle = True

    def __init__(self):
        super().__init__()
        rest = PATTERNS["M0"] + 8 * DEG
        rot = np.array([[math.cos(8 * DEG), -math.sin(8 * DEG), 0], [math.sin(8 * DEG), math.cos(8 * DEG), 0], [0, 0, 1]])
        self.rest = rest
        self.rim = Circle(radius=M_R / 2, stroke_color=FOCUS, stroke_width=W_LINE, stroke_opacity=0.7,
                          fill_color=BG, fill_opacity=0.0).move_to(TWIN_C)
        self.needles = VGroup(*[Needle(TWIN_C + 0.5 * (rot @ p), length=NEEDLE_LEN / 2, half=0.010, color=FOCUS, hollow=True)
                                for p in NEEDLE_POS])
        self.light_pos = [TWIN_C + 1.5 * C(math.cos(a * DEG), math.sin(a * DEG)) for a in TWIN_LIGHT_ANGLES]
        self.rings = VGroup(*[Circle(radius=0.11, stroke_color=FOCUS, stroke_width=W_LINE, stroke_opacity=0.55,
                                     fill_opacity=0).move_to(p) for p in self.light_pos])
        self.cores = VGroup(*[Circle(radius=0.09, stroke_width=0, fill_color=FAIL, fill_opacity=0.35).move_to(p)
                              for p in self.light_pos])
        self.add(self.rim, self.needles, self.rings, self.cores)
        self.jitter = 0.0
        self.paint()

    def paint(self):
        g, t = idle_gain(), film_time()
        amp = g * self.jitter
        k = int(math.floor(t * 6))
        jump = (rand(SEEDS["twin"], k, 40) * 2 - 1) * 20 * DEG
        lv = self.level
        for i, nd in enumerate(self.needles):
            nd.set_angle(self.rest[i] + amp * jump[i])
            nd.set_stroke(opacity=0.85 * lv)
        k2 = int(math.floor(t * 2))
        pick = rand(SEEDS["twin"], 100000 + k2, 5) < 0.5
        for j, c in enumerate(self.cores):
            col, op = (INK, 0.40) if pick[j] else (FAIL, 0.35)
            c.set_fill(mix(FAIL, col, amp), opacity=(0.35 + (op - 0.35) * amp) * lv)
        self.rim.set_stroke(opacity=0.7 * lv)
        self.rings.set_stroke(opacity=0.55 * lv)
        return self

    def set_rest(self):
        self.jitter = 0.0
        return self.paint()

    def to_jitter(self, x: float, **kw) -> Animation:
        return Tween(self, "jitter", x, **kw)


# =================================================================================================== the safety test

TEST_A0, TEST_DA = -42.55, 3.7
RED_FIRST = [0, 3, 6, 9, 10, 14, 15, 20, 21]
RED_INNER = [0, 6, 10, 14, 20]
RED_OUTER = [3, 9, 15, 21]
INNER, OUTER = list(range(0, 24, 2)), list(range(1, 24, 2))
RETRAIN_RED = {"MA": [0, 3, 6, 9, 10, 15, 21], "MB": [0, 3, 6, 9, 10, 14, 15, 20, 21], "MC": [0, 3, 6, 9, 10, 14, 15, 21]}
ROUNDS_INNER = [[0, 6, 10, 14, 20], [6, 10, 14], [10], []]
SHADE = dict(r0=3.72, r1=4.08, a0=-40.5, a1=44.0)
LIGHT_R, CORE_R, RED_GLOW_R = 0.11, 0.09, 0.25
_LOOK = {   # r, g, b, alpha, glow, ring
    "hollow": (*np.array(INK.to_rgb()), 0.0, 0.0, 0.6),
    "pale": (*np.array(INK.to_rgb()), 0.6, 0.0, 0.6),
    "red": (*np.array(FAIL.to_rgb()), 1.0, 0.9, 0.6),
    "dark": (*np.array(GREY_4.to_rgb()), 1.0, 0.0, 0.6),
    "soft": (*np.array(INK.to_rgb()), 0.35, 0.0, 0.0),
}


def light_angle(k: int) -> float:
    return (TEST_A0 + TEST_DA * k) * DEG


def light_pos(k: int, split: float = 0.0) -> np.ndarray:
    r = 3.0 if k % 2 == 0 else 3.25 + (3.95 - 3.25) * split
    a = light_angle(k)
    return M_C + r * C(math.cos(a), math.sin(a))


def _sector_points(r0, r1, a0, a1, n=72):
    a = np.linspace(a0 * DEG, a1 * DEG, n)
    outer = np.column_stack([M_C[0] + r1 * np.cos(a), M_C[1] + r1 * np.sin(a), 0 * a])
    inner = np.column_stack([M_C[0] + r0 * np.cos(a[::-1]), M_C[1] + r0 * np.sin(a[::-1]), 0 * a])
    return np.vstack([outer, inner, outer[:1]]), outer


class TestArc(Lasting):
    """The safety test (Object 3): 24 rings, one cloud of 24 cores (each with its glow), one haze cloud (the soft
    state of S03, screen blend), and the shade over the outer row."""

    def __init__(self, states=None, split: float = 0.0, shade: float = 1.0, shade_on: float = 1.0):
        super().__init__()
        self.split = np.full(24, float(split))
        self.shade_on = float(shade_on)       # 0: there is no shade yet (S01, S02); S03 wipes it in
        self.look = np.array([_LOOK["hollow"]] * 24, dtype=float)
        self.haze = np.zeros((24, 2))          # alpha (0..1; 0.5 is the 30% of S03), radius share (0: 0.45, 1: 0.8)
        self.shade = float(shade)
        self.grey = 0.0
        pos = np.array([light_pos(k, split) for k in range(24)])
        self.rings = VGroup(*[Circle(radius=LIGHT_R, stroke_color=GREY_2, stroke_width=W_LINE, stroke_opacity=0.6,
                                     fill_opacity=0).move_to(p) for p in pos])
        self.cores = DotCloud(pos, radius=CORE_R, color=INK, opacity=0.0, glow=0.0, glow_reach=RED_GLOW_R / CORE_R)
        self.cores.drift(amp=0.0, period=5.1, seed=SEEDS["patterns"] + 7, twinkle=0.08)
        d = self.cores._drift
        d["w"][:, 0] = TAU_ / (3.0 * 1.7)                    # lit cores breathe with a period of 3 s
        d["twp"][:] = 0.0
        self.hz = DotCloud(pos, radius=0.001, color=INK, opacity=0.0, glow=1.0, glow_reach=450.0)
        set_blend(self.hz, "screen")
        sector_pts, outer = _sector_points(**SHADE)
        self.sector = VMobject(stroke_width=0, fill_color=BG, fill_opacity=0.88)
        self.sector.set_points_as_corners(sector_pts)
        self.edge = polyline(sector_pts, GREY_3, W_LINE)
        self.hairline = polyline(outer, GREY_3, W_LINE)
        self.add(self.rings, self.cores, self.hz, self.sector, self.edge, self.hairline)
        self.set_states(states or {})

    # positions
    def pos(self, k: int) -> np.ndarray:
        return light_pos(k, float(self.split[k]))

    def paint(self):
        pos = np.array([self.pos(k) for k in range(24)])
        for k, r in enumerate(self.rings):
            r.move_to(pos[k])
        lev = np.broadcast_to(self.lev(pos), (24,))
        rgb = self.look[:, :3].copy()
        red = np.array(FAIL.to_rgb())
        is_red = np.linalg.norm(rgb - red, axis=1) < 0.25
        if self.grey > 0:
            rgb[is_red] = rgb[is_red] + (np.array(GREY_2.to_rgb()) - rgb[is_red]) * self.grey
        glow = self.look[:, 4] * (1 - self.grey * is_red)
        self.cores.points = pos.copy()
        self.cores.rgbas = np.column_stack([rgb, self.look[:, 3] * lev])
        self.cores.glows = glow
        self.cores._drift["tw"] = 0.08 * (self.look[:, 3] > 0.3)
        for k, r in enumerate(self.rings):
            r.set_stroke(opacity=float(self.look[k, 5] * lev[k]))
        self.hz.points = pos.copy()
        self.hz.rgbas = np.column_stack([np.tile(np.array(INK.to_rgb()), (24, 1)), self.haze[:, 0] * lev])
        self.hz.radii = (0.45 + 0.35 * self.haze[:, 1]) / 450.0
        sh = self.lev(C(4.0, 0.5)) if self.lamp is not None else self.level
        sh = float(np.mean(sh))
        on = self.shade_on * sh
        self.sector.set_fill(opacity=0.88 * self.shade * on)
        self.edge.set_stroke(opacity=self.shade * on)
        self.hairline.set_stroke(opacity=(1 - self.shade) * on)
        return self

    # states
    def _looks(self, states) -> np.ndarray:
        look = self.look.copy()
        items = states.items() if isinstance(states, dict) else enumerate(states)
        for k, s in items:
            look[int(k)] = _LOOK[s]
        return look

    def set_states(self, states):
        self.look = self._looks(states)
        return self.paint()

    def to_states(self, states, lag: float = 0.0, order=None, **kw) -> Animation:
        return Tween(self, "look", self._looks(states), lag=lag, order=order, **kw)

    def set_split(self, x: float):
        self.split[:] = x
        return self.paint()

    def to_split(self, x: float = 1.0, lag: float = 0.3, **kw) -> Animation:
        return Tween(self, "split", np.full(24, float(x)), lag=lag, **kw)

    def set_shade(self, x: float):
        self.shade = float(x)
        return self.paint()

    def to_shade(self, x: float, **kw) -> Animation:
        return Tween(self, "shade", x, **kw)

    def set_shade_on(self, x: float):
        self.shade_on = float(x)
        return self.paint()

    def to_shade_on(self, x: float, **kw) -> Animation:
        return Tween(self, "shade_on", x, **kw)

    def set_grey(self, x: float):
        self.grey = float(x)
        return self.paint()

    def to_grey(self, x: float, **kw) -> Animation:
        return Tween(self, "grey", x, **kw)

    def set_haze(self, alpha, radius_share=0.0, ks=None):
        ks = range(24) if ks is None else ks
        for k in ks:
            self.haze[k] = (alpha, radius_share)
        return self.paint()

    def states_with(self, red, others="pale", outer=None) -> dict:
        """A state dict: ``red`` lights red, the rest ``others``; ``outer`` overrides the odd lights."""
        out = {k: ("red" if k in red else others) for k in range(24)}
        if outer is not None:
            out.update({k: outer for k in OUTER})
        return out


def ask_path(k: int, test: TestArc | None = None) -> np.ndarray:
    """Samples of the straight path from light k to the model's rim (a request; reverse it for the answer)."""
    p = test.pos(k) if test is not None else light_pos(k)
    q = Model.rim_point(p)
    return np.array([_lerp(p, q, s) for s in np.linspace(0, 1, 12)])


# =================================================================================================== the cost floor

FLOOR_Y, FLOOR_X0, FLOOR_X1, LANE_Y = -2.3, -3.0, 5.4, -2.75
SEG_W, SEG_H, SEG_PITCH = 0.56, 0.10, 0.60


def seg_box(i: int):
    x0 = FLOOR_X0 + SEG_PITCH * i
    return x0, x0 + SEG_W


class CostFloor(Lasting):
    """The cost floor (Object 4): floor line, 14 band segments (none, outline or solid), end tick, shortcut lane."""

    idle = True

    def __init__(self, segments="outline", line: float = 1.0, tick: bool = True, lane: float = 0.0):
        super().__init__()
        self.line = Line(C(FLOOR_X0, FLOOR_Y), C(FLOOR_X1, FLOOR_Y), stroke_color=GREY_3, stroke_width=W_LINE)
        self.segs = VGroup()
        for i in range(14):
            x0, x1 = seg_box(i)
            r = Rectangle(width=SEG_W, height=SEG_H, stroke_color=GREY_1, stroke_width=W_LINE, stroke_opacity=0.25,
                          fill_color=GREY_1, fill_opacity=0.0).move_to(C((x0 + x1) / 2, FLOOR_Y + SEG_H / 2))
            self.segs.add(r)
        self.tick = Line(C(FLOOR_X1, FLOOR_Y - 0.04), C(FLOOR_X1, FLOOR_Y + 0.30), stroke_color=GREY_1, stroke_width=W_LINE)
        self.lane = VGroup()
        n = 42
        for j in range(n):
            a = FLOOR_X0 + (FLOOR_X1 - FLOOR_X0) * j / n
            self.lane.add(Line(C(a, LANE_Y), C(a + (FLOOR_X1 - FLOOR_X0) / n * 0.6, LANE_Y), stroke_color=GREY_3,
                               stroke_width=W_LINE))
        self.dials = VGroup()
        self.add(self.line, self.segs, self.tick, self.lane, self.dials)
        self.drawn = float(line)
        self.shown = np.zeros(14)       # 1: the segment exists (outline)
        self.solid = np.zeros(14)       # 1: solid (spent)
        self.tick_on = 1.0 if tick else 0.0
        self.tick_down = 0.0            # S05: the tick grows down across the lane
        self.lane_on = float(lane)
        self.lane_drawn = 1.0
        self.set_segments([segments] * 14 if isinstance(segments, str) else segments)

    def paint(self):
        g, t = idle_gain(), film_time()
        lv = self.level
        x_end = FLOOR_X0 + (FLOOR_X1 - FLOOR_X0) * max(self.drawn, 1e-4)
        self.line.put_start_and_end_on(C(FLOOR_X0, FLOOR_Y), C(x_end, FLOOR_Y))
        self.line.set_stroke(opacity=lv * float(self.drawn > 1e-3) * float(np.mean(self.lev(C(1.2, FLOOR_Y)))))
        ph = (t % 6.0) / 6.0
        xg = FLOOR_X0 - 0.6 + (FLOOR_X1 - FLOOR_X0 + 1.2) * ph / 0.45
        for i, r in enumerate(self.segs):
            x0, x1 = seg_box(i)
            xc = (x0 + x1) / 2
            glint = 1.0 + (0.5 * g * math.exp(-((xc - xg) / 0.6) ** 2) if ph < 0.45 else 0.0)
            lvi = float(np.mean(self.lev(C(xc, FLOOR_Y))))
            r.set_fill(opacity=min(self.solid[i] * lvi * glint, 1.0))
            r.set_stroke(opacity=min(0.25 * self.shown[i] * (1 - self.solid[i]) * lvi * glint, 1.0))
        self.tick.put_start_and_end_on(C(FLOOR_X1, FLOOR_Y - 0.04 - 0.52 * self.tick_down), C(FLOOR_X1, FLOOR_Y + 0.30))
        self.tick.set_stroke(opacity=self.tick_on * float(np.mean(self.lev(C(FLOOR_X1, FLOOR_Y)))))
        n = len(self.lane)
        for j, d in enumerate(self.lane):
            on = 1.0 if (j + 0.5) / n <= self.lane_drawn else 0.0
            d.set_stroke(opacity=self.lane_on * on * float(np.mean(self.lev(d.get_center()))))
        self.dials.set_opacity(lv)
        return self

    def set_segments(self, states):
        for i, s in enumerate(states):
            self.shown[i] = 0.0 if s == "none" else 1.0
            self.solid[i] = 1.0 if s == "solid" else 0.0
        return self.paint()

    def to_segments(self, states, lag: float = 0.0, order=None, **kw) -> Animation:
        solid = np.array([1.0 if s == "solid" else 0.0 for s in states])
        shown = np.array([0.0 if s == "none" else 1.0 for s in states])
        self_shown = Tween(self, "shown", np.maximum(shown, self.shown), lag=lag, order=order, **kw)
        return AnimationGroup(self_shown, Tween(self, "solid", solid, lag=lag, order=order, **kw))

    def set_line(self, f: float):
        self.drawn = float(f)
        return self.paint()

    def to_line(self, f: float = 1.0, **kw) -> Animation:
        kw.setdefault("rate_func", linear)
        return Tween(self, "drawn", f, **kw)

    def set_tick(self, on: bool = True):
        self.tick_on = 1.0 if on else 0.0
        return self.paint()

    def to_tick_down(self, x: float, **kw) -> Animation:
        return Tween(self, "tick_down", x, **kw)

    def set_lane(self, on: float = 1.0, drawn: float = 1.0):
        self.lane_on, self.lane_drawn = float(on), float(drawn)
        return self.paint()

    def to_lane(self, drawn: float = 1.0, **kw) -> Animation:
        self.lane_on = 1.0
        return Tween(self, "lane_drawn", drawn, **kw)

    def dial(self, i: int, share: float) -> "Dial":
        """A mini dial standing on the right end of segment i (not added: born_from a copy of the test lights)."""
        x1 = seg_box(i)[1]
        d = Dial(share, radius=0.16)
        d.move_to(C(x1, FLOOR_Y + SEG_H + 0.18))
        d.set_share(share)
        return d


# =================================================================================================== the lone point

LONE = PL(-5.4, -0.2)


class LonePoint(Lasting):
    """The point of the pilot before S06: core 0.07 GREY_1, a white halo 0.32 that breathes."""

    idle = True

    def __init__(self, level: float = 0.1):
        super().__init__()
        self.halo = glow_sprite(0.32, INK_HI, peak=0.55).move_to(LONE)
        self.core = Circle(radius=0.07, stroke_width=0, fill_color=GREY_1, fill_opacity=1.0).move_to(LONE)
        self.add(self.halo, self.core)
        self.level = level
        self.swell = 0.0
        self.paint()

    def paint(self):
        g, t = idle_gain(), film_time()
        breath = 1.0 - 0.18 * g * (0.5 - 0.5 * math.cos(TAU_ * t / 2.4))
        self.core.set_fill(opacity=self.level)
        self.halo.set_fill(opacity=min(self.level * breath * (1 + self.swell), 1.0))
        return self


# =================================================================================================== the boundary

BOUND_Y = -3.0
CLOSED_W, CLOSED_H = 1.6, 0.92
EMBLEM_HOME = C(-5.4, -1.6)


def open_anchors() -> np.ndarray:
    xs = [-12 + 3 * i for i in range(9)] + [12 - 3 * (i - 8) for i in range(9, 16)]
    return np.array([[x, BOUND_Y, 0.0] for x in xs], dtype=float)


def closed_anchors(centre=EMBLEM_HOME) -> np.ndarray:
    a = np.array([(180 - 22.5 * i) * DEG for i in range(16)])
    c = np.asarray(centre, dtype=float)
    return np.column_stack([c[0] + CLOSED_W / 2 * np.cos(a), c[1] + CLOSED_H / 2 * np.sin(a), 0 * a])


class Boundary(Lasting):
    """The boundary (Object 6): open along canvas y = -3.0 (bleed), or closed round the emblem."""

    idle = True

    def __init__(self, closed: bool = False, centre=EMBLEM_HOME):
        super().__init__()
        self.curve = smooth_closed(open_anchors(), stroke_color=INK_HI, stroke_width=W_LINE, stroke_opacity=0.45,
                                   fill_opacity=0)
        self.glows = VGroup(*[smooth_closed(closed_anchors(centre), stroke_color=INK_HI, stroke_width=w, stroke_opacity=0,
                                            fill_opacity=0) for w in (9.0, 18.0)])
        for m in (self.curve, *self.glows):
            m.bleed_ok = True
        self.add(self.glows, self.curve)
        self.closed, self.bright, self.glow = False, 0.45, 0.0
        if closed:
            self.set_closed(centre)
        self.paint()

    @staticmethod
    def closed_curve(centre=EMBLEM_HOME, bright: float = 0.45, width=W_LINE) -> VMobject:
        """The closed curve (16 anchors in the order of Object 6) for the Transform of S10."""
        m = smooth_closed(closed_anchors(centre), stroke_color=INK_HI, stroke_width=width, stroke_opacity=bright,
                          fill_opacity=0)
        m.bleed_ok = True
        return m

    def set_open(self):
        self.curve.become(smooth_closed(open_anchors(), stroke_color=INK_HI, stroke_width=W_LINE, stroke_opacity=0.45,
                                        fill_opacity=0))
        self.curve.bleed_ok = True
        self.closed, self.bright, self.glow = False, 0.45, 0.0
        return self.paint()

    def set_closed(self, centre=EMBLEM_HOME, bright: bool = True):
        self.curve.become(self.closed_curve(centre, 1.0 if bright else 0.45, W_BOLD if bright else W_LINE))
        self.curve.bleed_ok = True
        for g in self.glows:
            g.become(smooth_closed(closed_anchors(centre), stroke_color=INK_HI, stroke_width=g.stroke_width,
                                   stroke_opacity=0, fill_opacity=0))
        self.closed, self.bright, self.glow = True, 1.0 if bright else 0.45, 1.0 if bright else 0.0
        return self.paint()

    def paint(self):
        g, t = idle_gain(), film_time()
        breath = 1.0 + 0.6 * g * math.sin(TAU_ * t / 4.0)
        self.curve.set_stroke(opacity=self.bright * self.level)
        for m, base in zip(self.glows, (0.07, 0.03)):
            m.set_stroke(opacity=base * self.glow * breath * self.level)
        return self

    def to_glow(self, x: float, **kw) -> Animation:
        return Tween(self, "glow", x, **kw)

    def to_bright(self, x: float, **kw) -> Animation:
        return Tween(self, "bright", x, **kw)


# =================================================================================================== the toy (3.7)


class _Toy:
    """The toy behind the pilot pictures (3.7), computed by exact sums over every pair of futures."""

    LEVELS = np.array([0.72, 1.71, 0.19])
    ETA, TEMP = 0.35, 0.86
    X = (-5.4, -3.9, -2.4, -0.9)        # start, after the event, after step 1, after step 2 (P-local x)

    def probs(self, h: float) -> np.ndarray:
        w = np.exp(-np.abs(h - self.LEVELS) / self.TEMP)
        return w / w.sum()

    def step(self, h: float, c: int) -> float:
        return h + self.ETA * (self.LEVELS[c] - h)

    @staticmethod
    def seg(p, u: float) -> int:
        """The segment that a pointer at u reads, in the fixed order 1, 2, 3 (0-based)."""
        return int(min(np.searchsorted(np.cumsum(p), u, side="right"), 2))

    @staticmethod
    def y(h: float) -> float:
        return -0.2 + 1.25 * h

    def joint(self, pa, pb, mode: str) -> dict:
        if mode == "none":
            return {(i, j): pa[i] * pb[j] for i in range(3) for j in range(3)}
        f = (lambda u: u) if mode == "straight" else (lambda u: 1 - u)
        cuts = {0.0, 1.0} | {float(min(x, 1.0)) for x in np.cumsum(pa)}
        cuts |= {float(min(x, 1.0)) if mode == "straight" else float(min(max(1 - x, 0.0), 1.0)) for x in np.cumsum(pb)}
        cuts = sorted(cuts)
        out = {}
        for lo, hi in zip(cuts, cuts[1:]):
            if hi - lo < 1e-15:
                continue
            m = (lo + hi) / 2
            key = (self.seg(pa, m), self.seg(pb, f(m)))
            out[key] = out.get(key, 0.0) + hi - lo
        return out

    def dist(self, mode: str) -> dict:
        hA0, hB0 = self.h_event["A"], self.h_event["B"]
        out = {}
        for (a1, b1), p1 in self.joint(self.probs(hA0), self.probs(hB0), mode).items():
            hA1, hB1 = self.step(hA0, a1), self.step(hB0, b1)
            for (a2, b2), p2 in self.joint(self.probs(hA1), self.probs(hB1), mode).items():
                D = round(self.step(hB1, b2) - self.step(hA1, a2), 12)
                out[D] = out.get(D, 0.0) + p1 * p2
        return out

    def __init__(self):
        self.h_event = {"A": self.step(0.0, 1), "B": 0.0}               # the event: segment 2, no draw; B suppressed
        hA0, hB0 = self.h_event["A"], self.h_event["B"]
        self.choices = {"A": (1, 0), "B": (0, 2)}                       # the future of S06: steps 1 and 2 (0-based)
        hA1, hB1 = self.step(hA0, 1), self.step(hB0, 0)
        hA2, hB2 = self.step(hA1, 0), self.step(hB1, 2)
        self.h = {"A": (0.0, hA0, hA1, hA2), "B": (0.0, hB0, hB1, hB2)}
        self.bars = {"event": self.probs(0.0), "A1": self.probs(hA0), "B1": self.probs(hB0),
                     "A2": self.probs(hA1), "B2": self.probs(hB1)}
        self.d = {m: self.dist(m) for m in ("none", "straight", "crossed")}
        self.mean = {m: sum(k * v for k, v in d.items()) for m, d in self.d.items()}
        self.var = {m: sum(v * (k - self.mean[m]) ** 2 for k, v in d.items()) for m, d in self.d.items()}
        self.half = {m: 2.0 * math.sqrt(v) for m, v in self.var.items()}
        self.change = {m: 100 * (self.var[m] / self.var["none"] - 1) for m in self.var}
        self.values = sorted(set(self.d["none"]) | set(self.d["straight"]) | set(self.d["crossed"]))
        sd = math.sqrt(self.var["none"])
        self.outside = sum(v for k, v in self.d["none"].items() if abs(k - self.mean["none"]) > sd)
        # the 40 futures of S07 (seed 11, no coordination)
        rng = np.random.default_rng(SEEDS["futures"])
        self.futures = []
        for _ in range(40):
            u = rng.random(4)
            a1, b1 = self.seg(self.probs(hA0), u[0]), self.seg(self.probs(hB0), u[1])
            hA1_, hB1_ = self.step(hA0, a1), self.step(hB0, b1)
            a2, b2 = self.seg(self.probs(hA1_), u[2]), self.seg(self.probs(hB1_), u[3])
            hA2_, hB2_ = self.step(hA1_, a2), self.step(hB1_, b2)
            self.futures.append(dict(a=(a1, a2), b=(b1, b2), hA=(hA0, hA1_, hA2_), hB=(hB0, hB1_, hB2_),
                                     D=round(hB2_ - hA2_, 12)))
        # the stratified landings of S07 lines 5 and 6 (seed 17 orders them)
        rng = np.random.default_rng(SEEDS["piles"])
        self.line5 = [("straight", int(k)) for k in rng.permutation(30)]
        crossed = [1, 28, 4, 25, 7, 22, 10, 19, 13, 16]
        rest = [k for k in range(30) if k not in crossed]
        blocks = [("straight", rest[0::2]), ("crossed", crossed), ("straight", rest[1::2])]
        self.line6 = [(form, int(k)) for form, ks in blocks for k in rng.permutation(ks)]
        self.pile_counts = {"line5": (self.piles(self.line5, "A1", "B1")), "line6": self.piles(self.line6, "A2", "B2")}
        self.final_link = 0.46

    @staticmethod
    def grid_u(k: int) -> float:
        return (k + 0.5) / 30

    def landing(self, form: str, k: int) -> tuple[float, float]:
        """(u on bar A, u on bar B) of landing k under a form."""
        u = self.grid_u(k)
        return u, (u if form == "straight" else 1 - u)

    def piles(self, schedule, bar_a: str, bar_b: str):
        ca, cb = [0, 0, 0], [0, 0, 0]
        for form, k in schedule:
            ua, ub = self.landing(form, k)
            ca[self.seg(self.bars[bar_a], ua)] += 1
            cb[self.seg(self.bars[bar_b], ub)] += 1
        return tuple(ca), tuple(cb)

    def tick_y(self, D: float) -> float:
        return -0.05 + 2.0 * (D + 0.3514)

    def nodes(self, copy: str, upto: int = 3, h=None) -> list:
        """P-local nodes of a copy's path: start, after the event, step 1, step 2 (``upto`` = the last index)."""
        hs = self.h[copy] if h is None else h
        return [np.array([self.X[i], self.y(hs[i]), 0.0]) for i in range(upto + 1)]

    def future_nodes(self, f: dict, copy: str) -> list:
        hs = (0.0, *(f["hA"] if copy == "A" else f["hB"]))
        return [np.array([self.X[i], self.y(hs[i]), 0.0]) for i in range(4)]

    def ghost_edges(self, futures=None, include_s06: bool = True) -> list:
        """The distinct edges of steps 1 and 2 of these futures (each drawn once: repeats add no ghost)."""
        futures = self.futures if futures is None else futures
        edges = {}
        paths = [(c, self.future_nodes(f, c)) for f in futures for c in "AB"]
        if include_s06:
            paths += [(c, self.nodes(c)) for c in "AB"]
        for c, nd in paths:
            for i in (1, 2):
                key = (c, round(nd[i][1], 6), round(nd[i + 1][1], 6), i)
                edges[key] = (c, nd[i], nd[i + 1])
        return list(edges.values())

    def tick_counts(self, futures=None) -> dict:
        futures = self.futures if futures is None else futures
        out = {}
        for f in futures:
            out[f["D"]] = out.get(f["D"], 0) + 1
        return out

    def guard(self) -> list[str]:
        bad = []
        s, c = self.change["straight"], self.change["crossed"]
        if not -9.5 <= s <= -5.0:
            bad.append(f"the straight pairing changes the variance by {s:+.2f}% (must lower it by 5% to 9.5%)")
        if abs(c) > 3.0:
            bad.append(f"the crossed pairing changes the variance by {c:+.2f}% (must stay within 3%)")
        if max(abs(m - self.mean["none"]) for m in self.mean.values()) > 1e-9:
            bad.append(f"the means differ between pairings: {self.mean}")
        ys = [self.tick_y(D) for D in self.values]
        if min(ys) < -1.65 or max(ys) > 1.95:
            bad.append(f"a tick height lies outside the strip's axis: {min(ys):.3f} .. {max(ys):.3f}")
        if len(self.values) != 49:
            bad.append(f"the toy has {len(self.values)} possible values of D, not 49")
        if self.pile_counts["line5"] != ((15, 4, 11), (9, 3, 18)):
            bad.append(f"line-5 piles end at {self.pile_counts['line5']}")
        if self.pile_counts["line6"] != ((14, 8, 8), (10, 4, 16)):
            bad.append(f"line-6 piles end at {self.pile_counts['line6']}")
        rng = np.random.default_rng(2000)
        for _ in range(200):                                     # the schedule holds in every order of each block
            sched = []
            for blk in (self.line6[:10], self.line6[10:20], self.line6[20:]):
                sched += [blk[i] for i in rng.permutation(10)]
            if self.piles(sched, "A2", "B2") != ((14, 8, 8), (10, 4, 16)):
                bad.append("a reordered line-6 schedule misses its counts")
                break
        A2, B2 = self.bars["A2"], self.bars["B2"]
        if (self.seg(A2, self.final_link), self.seg(B2, self.final_link)) != (0, 2):
            bad.append("the final link at 0.46 is not in segment 1 of bar A and segment 3 of bar B")
        for name, p, u, want in (("step1 A", self.bars["A1"], 0.57, 1), ("step1 B", self.bars["B1"], 0.18, 0),
                                 ("step2 A", A2, 0.24, 0), ("step2 B", B2, 0.78, 2)):
            if self.seg(p, u) != want:
                bad.append(f"the S06 pointer {name} at u = {u} is not in segment {want + 1}")
        return bad


TOY = _Toy()
_bad = TOY.guard()
if _bad:
    raise RuntimeError("world: the toy of 3.7 fails its guard: " + "; ".join(_bad))

# =================================================================================================== the field (3.6)

FIELD_N = 1440
FIELD_MAIN = (C(1.2, -0.2), 2.2, 0.034)          # P-local centre, radius, unit radius
FIELD_PARK = (C(4.4, 0.95), 1.1, 0.02)
U_OFF = {"u1": np.array([0.32, 0.27]), "u2": np.array([0.27, -0.32])}
FAMILY_PHASES = tuple(float(x) for x in np.random.default_rng(SEEDS["family"]).uniform(0, TAU_, 2))
LOWER_PHASE = float(np.random.default_rng(SEEDS["lower"]).uniform(0, TAU_))


def family_r(theta, factor: float = 0.58):
    a, b = FAMILY_PHASES
    return factor + 0.06 * np.cos(2 * theta + a) + 0.04 * np.cos(3 * theta + b)


def _field_offsets():
    """Unit offsets from the centre in units of the radius (sunflower, jittered), with u1 and u2 exactly placed."""
    pts = sunflower_points(FIELD_N, 1.0, (0.0, 0.0), jitter=0.3, seed=SEEDS["bloom"])[:, :2]
    idx = {}
    for name, off in U_OFF.items():
        i = int(np.argmin(np.linalg.norm(pts - off, axis=1)))
        pts[i] = off
        idx[name] = i
    return pts, idx


FIELD_OFF, FIELD_U = _field_offsets()
_th = np.arctan2(FIELD_OFF[:, 1], FIELD_OFF[:, 0])
FAMILY = np.nonzero(np.hypot(FIELD_OFF[:, 0], FIELD_OFF[:, 1]) < family_r(_th))[0]
LOWER = np.array([i for i in FAMILY if FIELD_OFF[i, 1] < -0.06 + 0.05 * math.sin(5 * FIELD_OFF[i, 0] + LOWER_PHASE)])
for _u in ("u1", "u2"):
    if FIELD_U[_u] not in FAMILY:
        raise RuntimeError(f"world: {_u} lies outside the target family (seed 37)")
if FIELD_U["u2"] not in LOWER or FIELD_U["u1"] in LOWER:
    raise RuntimeError("world: u2 must lie in the lower part and u1 must not (seed 43)")
BLOOM_ORDER = np.random.default_rng(SEEDS["bloom"]).permutation(FIELD_N)


def field_pos(i, park: float = 1.0) -> np.ndarray:
    """P-local -> canvas position of unit(s) i at a park share (0 main, 1 parked)."""
    (c0, r0, _), (c1, r1, _) = FIELD_MAIN, FIELD_PARK
    c, r = _lerp(c0, c1, park), r0 + (r1 - r0) * park
    off = FIELD_OFF[i]
    off = np.atleast_2d(off)
    out = np.column_stack([c[0] + r * off[:, 0], c[1] + PY + r * off[:, 1], np.zeros(len(off))])
    return out if np.ndim(i) else out[0]


def _strongest_threads():
    start = PL(3.22, 0.96)
    ends = {}
    for u in ("u1", "u2"):
        p = field_pos(FIELD_U[u], 1.0)
        v = p - start
        ends[u] = start + v * (np.linalg.norm(v) - 0.2) / np.linalg.norm(v)
    return start, ends


STRONGEST_START, STRONGEST_ENDS = _strongest_threads()
def wave_y(x, park: float = 1.0):
    """The seeded wavy line of the lower part (3.6) in canvas y at canvas x, for a park share."""
    (c0, r0, _), (c1, r1, _) = FIELD_MAIN, FIELD_PARK
    c, R = _lerp(c0, c1, park), r0 + (r1 - r0) * park
    return c[1] + PY + R * (-0.06 + 0.05 * np.sin(5 * (np.asarray(x) - c[0]) / R + LOWER_PHASE))


def lower_curve_points(park: float = 1.0, n: int = 120) -> np.ndarray:
    """The second curve of S09: the wavy line from one side of the family outline to the other. With the family
    outline it closes round the lower part, so it is drawn once, with no second line along the outline."""
    fam = curve_samples(soft_hull(field_pos(FAMILY, park), 0.06), 600)[:, :2]
    xs = np.linspace(fam[:, 0].min(), fam[:, 0].max(), 1200)
    inside = _fx._inside(np.column_stack([xs, wave_y(xs, park)]), fam)
    k = np.nonzero(inside)[0]
    x0, x1 = xs[k[0]], xs[k[-1]]
    xx = np.linspace(x0, x1, n)
    return np.column_stack([xx, wave_y(xx, park), np.zeros(n)])


def _lower_region():
    fam = curve_samples(soft_hull(field_pos(FAMILY, 1.0), 0.06), 600)[:, :2]
    below = fam[:, 1] <= wave_y(fam[:, 0])
    return fam[below]


_LOWER_POLY = np.vstack([_lower_region(), lower_curve_points()[::-1, :2]])
_low_pts = field_pos(LOWER, 1.0)[:, :2]
if (_low_pts[:, 1] > wave_y(_low_pts[:, 0]) + 1e-9).any():
    raise RuntimeError("world: a unit of the lower part lies above its wavy line")
_t1 = np.array([_lerp(STRONGEST_START, STRONGEST_ENDS["u1"], s) for s in np.linspace(0, 1, 200)])[:, :2]
if _fx._inside(_t1, _LOWER_POLY).any():
    raise RuntimeError("world: the thread of `strongest` to u1 crosses the second curve (3.10)")


class Field(Lasting):
    """The field of 1,440 toy configurations (3.6): one DotCloud, main or parked, family outline, lower part, lit
    units u1 and u2. Each unit breathes by 10% with its own phase (seed 31); the field does not drift."""

    def __init__(self, park: float = 1.0, units: float = 0.6):
        super().__init__()
        self.park = float(park)
        self.units = float(units)
        self.lit = np.zeros(2)                 # u1, u2: 0 grey, 1 lit (INK_HI, glow 0.2)
        self.family = 0.0
        self.lower = 0.0
        self.cloud = DotCloud(field_pos(np.arange(FIELD_N), park), radius=FIELD_PARK[2], color=GREY_2, opacity=units,
                              glow=0.0, glow_reach=0.2 / FIELD_PARK[2])
        self.cloud.drift(amp=0.0, period=10.0, seed=SEEDS["breath"], twinkle=0.10)
        fam = field_pos(FAMILY, 1.0)
        low = field_pos(LOWER, 1.0)
        self.family_outline = soft_hull(fam, 0.06, stroke_color=INK, stroke_width=W_LINE, stroke_opacity=0.0, fill_opacity=0)
        self.lower_outline = polyline(lower_curve_points(1.0), INK, W_LINE, 0.0)
        self.add(self.cloud, self.family_outline, self.lower_outline)
        self.paint()

    def paint(self):
        r0, r1 = FIELD_MAIN[2], FIELD_PARK[2]
        self.cloud.points = field_pos(np.arange(FIELD_N), self.park)
        self.cloud.radii = np.full(FIELD_N, r0 + (r1 - r0) * self.park)
        self.cloud.glow_reach = 0.2 / self.cloud.radii[0]
        rgba = np.tile([*GREY_2.to_rgb(), self.units], (FIELD_N, 1))
        glows = np.zeros(FIELD_N)
        for u, x in zip(("u1", "u2"), self.lit):
            i = FIELD_U[u]
            rgba[i, :3] = np.array(GREY_2.to_rgb()) + (np.array(INK_HI.to_rgb()) - np.array(GREY_2.to_rgb())) * x
            rgba[i, 3] = self.units + (1.0 - self.units) * x
            glows[i] = x
        self.cloud.rgbas = rgba
        self.cloud.glows = glows
        self.cloud.set_fill(opacity=self.level)
        self.family_outline.set_stroke(opacity=0.55 * self.family * self.level)
        self.lower_outline.set_stroke(opacity=0.55 * self.lower * self.level)
        return self

    def unit(self, name_or_i) -> np.ndarray:
        i = FIELD_U[name_or_i] if isinstance(name_or_i, str) else int(name_or_i)
        return field_pos(i, self.park)

    def set_park(self, x: float):
        self.park = float(x)
        return self.paint()

    def to_park(self, x: float = 1.0, **kw) -> Animation:
        return Tween(self, "park", x, **kw)

    def set_family(self, x: float):
        self.family = float(x)
        return self.paint()

    def to_family(self, x: float, **kw) -> Animation:
        return Tween(self, "family", x, **kw)

    def set_lower(self, x: float):
        self.lower = float(x)
        return self.paint()

    def to_lower(self, x: float, **kw) -> Animation:
        return Tween(self, "lower", x, **kw)

    def set_units(self, x: float):
        self.units = float(x)
        return self.paint()

    def to_units(self, x: float, **kw) -> Animation:
        return Tween(self, "units", x, **kw)

    def set_lit(self, u: str, x: float):
        self.lit[("u1", "u2").index(u)] = float(x)
        return self.paint()

    def to_lit(self, u: str, x: float, **kw) -> Animation:
        goal = self.lit.copy()
        goal[("u1", "u2").index(u)] = x
        return Tween(self, "lit", goal, **kw)


# =================================================================================================== the fork, bars, strip


class Fork(Lasting):
    """The tiny learner's two copies (Object 5, P-local nodes): start dot, event rings, bright paths with brighter
    tails, heads that breathe, ghosts of earlier futures, the comparison segment."""

    idle = True

    def __init__(self):
        super().__init__()
        self.ghosts = VGroup()
        self.path_a = polyline([PL(-5.4, -0.2), PL(-5.39, -0.2)], MODEL, W_BOLD)
        self.path_b = polyline([PL(-5.4, -0.2), PL(-5.39, -0.2)], COPY_B, W_BOLD)
        self.tail_a, self.tail_b = Trail(), Trail()
        self.comparison = Line(PL(-0.9, 0.0), PL(-0.9, 0.5), stroke_color=INK, stroke_width=W_BOLD, stroke_opacity=0.0)
        self.ring_a = Circle(radius=0.15, stroke_color=INK, stroke_width=W_LINE, fill_color=INK, fill_opacity=1.0)
        self.ring_b = Circle(radius=0.15, stroke_color=COPY_B, stroke_width=W_LINE, fill_color=BG, fill_opacity=1.0)
        self.start = Circle(radius=0.05, stroke_width=0, fill_color=GREY_1, fill_opacity=1.0).move_to(PL(-5.4, -0.2))
        self.heads = {}
        for c, col in (("A", MODEL), ("B", COPY_B)):
            glow = glow_sprite(0.28, col, peak=0.6)
            core = Circle(radius=0.07, stroke_width=0, fill_color=hot(col, 0.45), fill_opacity=1.0)
            self.heads[c] = VGroup(glow, core)
        self.head_a, self.head_b = self.heads["A"], self.heads["B"]
        self.add(self.ghosts, self.path_a, self.path_b, self.tail_a, self.tail_b, self.comparison,
                 self.ring_a, self.ring_b, self.start, self.head_a, self.head_b)
        self.nodes = {"A": TOY.nodes("A"), "B": TOY.nodes("B")}
        self.paths = 1.0        # level of the bright paths, tails and heads
        self.comp = 0.0         # the comparison segment
        self.rings = 1.0        # the event rings
        self.ghost = 0.14       # ghosts: share of the fork's level
        self.ghost_edges = []
        self.paint()

    def set_nodes(self, a_nodes=None, b_nodes=None):
        """P-local node lists (start first, head last); a list of (x, y) or 3-vectors."""
        for c, nd in (("A", a_nodes), ("B", b_nodes)):
            if nd is not None:
                self.nodes[c] = [np.array([p[0], p[1], 0.0]) for p in nd]
        return self.paint()

    def set_ghosts(self, edges):
        """edges: (copy, P-local p, P-local q) from TOY.ghost_edges(); each drawn once, MODEL or COPY_B."""
        self.ghost_edges = list(edges)
        self.ghosts.remove(*self.ghosts.submobjects)
        self.ghosts.add(*[Line(PL(p[0], p[1]), PL(q[0], q[1]), stroke_color=MODEL if c == "A" else COPY_B,
                               stroke_width=W_LINE, stroke_opacity=0.0) for c, p, q in self.ghost_edges])
        return self.paint()

    @staticmethod
    def _tail(nodes, length=0.8, n=24):
        p = np.array([PL(q[0], q[1]) for q in nodes])
        seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        total = cum[-1]
        s = np.linspace(max(total - length, 0.0), total, n)
        pts = np.column_stack([np.interp(s, cum, p[:, k]) for k in range(3)])
        return pts, (s - s[0]) / max(s[-1] - s[0], 1e-9)

    def paint(self):
        g, t = idle_gain(), film_time()
        lv = self.level
        breath = 1.0 - 0.35 * g * (0.5 - 0.5 * math.cos(TAU_ * t / 1.6))      # heads breathe (period 1.6 s)
        for c, path, tail, col in (("A", self.path_a, self.tail_a, MODEL), ("B", self.path_b, self.tail_b, COPY_B)):
            nd = self.nodes[c]
            pts = np.array([PL(q[0], q[1]) for q in nd])
            if len(pts) < 2 or np.linalg.norm(pts[-1] - pts[0]) < 1e-6:
                pts = np.array([pts[0], pts[0] + np.array([1e-3, 0, 0])])
                vis = 0.0
            else:
                vis = 1.0
            path.set_points_as_corners(pts)
            path.set_stroke(opacity=0.55 * lv * self.paths * vis)
            tp, a = self._tail(nd)
            rgba = np.column_stack([np.tile(np.array(col.to_rgb()), (len(tp), 1)), (0.45 * a ** 1.3) * lv * self.paths * vis])
            tail.set_samples(tp, np.full(len(tp), W_BOLD * 0.01), rgba)
            head = self.heads[c]
            head.move_to(pts[-1])
            head[0].set_fill(opacity=lv * self.paths * breath)
            head[1].set_fill(opacity=lv * self.paths)
        ya, yb = self.head_a.get_center(), self.head_b.get_center()
        if np.linalg.norm(ya - yb) > 1e-4:
            self.comparison.put_start_and_end_on(yb, ya)
        self.comparison.set_stroke(opacity=lv * self.comp)
        self.ring_a.move_to(PL(-4.65, TOY.y(TOY.h_event["A"] / 2)))
        self.ring_b.move_to(PL(-4.65, -0.2))
        self.ring_a.set_fill(opacity=lv * self.rings).set_stroke(opacity=lv * self.rings)
        self.ring_b.set_fill(opacity=lv * self.rings).set_stroke(opacity=lv * self.rings)
        self.start.set_fill(opacity=lv)
        for m in self.ghosts:
            m.set_stroke(opacity=self.ghost * lv)
        return self

    def to_paths(self, x: float, **kw) -> Animation:
        return Tween(self, "paths", x, **kw)

    def to_comparison(self, x: float, **kw) -> Animation:
        return Tween(self, "comp", x, **kw)


BAR_X0, BAR_LEN, BAR_H = -4.2, 5.0, 0.42
BAR_Y = {"A": -1.35, "B": -2.3}
SEG_GREYS = (GREY_2, GREY_1, GREY_3)
PILE_PITCH, PILE_R = 0.07, 0.035


def bar_x(u: float) -> float:
    return BAR_X0 + BAR_LEN * u


class ChoiceBars(Lasting):
    """The two probability bars (Object 5): three grey segments with the copy's own widths, a tab in the copy's
    colour, pointers (step 1 and 2), the link (straight or crossed), piles of landings."""

    def __init__(self, widths=None):
        super().__init__()
        self.widths = {"A": np.array(TOY.bars["A2"]), "B": np.array(TOY.bars["B2"])}
        if widths:
            self.widths.update({k: np.array(v, dtype=float) for k, v in widths.items()})
        self.lit = {"A": np.zeros(3), "B": np.zeros(3)}
        self.flash = {"A": 0.0, "B": 0.0}
        self.ptr = {"A": [0.24, 0.0], "B": [0.78, 0.0]}           # u, shown
        self.link = [0.46, 0.46, 0.0]                              # u on A, u on B, shown
        self.counts = {"A": [0, 0, 0], "B": [0, 0, 0]}
        self.pile_level = 1.0
        self.parts = {}
        for c, col in (("A", MODEL), ("B", COPY_B)):
            y = BAR_Y[c]
            segs = VGroup(*[VMobject(stroke_width=0, fill_color=SEG_GREYS[j], fill_opacity=0.9) for j in range(3)])
            seps = VGroup(*[Line(PL(0, y - BAR_H / 2), PL(0, y + BAR_H / 2), stroke_color=BG, stroke_width=W_LINE) for _ in range(2)])
            tab = Rectangle(width=0.08, height=BAR_H, stroke_width=0, fill_color=col, fill_opacity=1.0).move_to(PL(BAR_X0 + 0.04, y))
            outline = Rectangle(width=BAR_LEN + 0.06, height=BAR_H + 0.06, stroke_color=col, stroke_width=W_LINE,
                                stroke_opacity=0.0, fill_opacity=0).move_to(PL(BAR_X0 + BAR_LEN / 2, y))
            pile = DotCloud(np.tile(PL(0, y), (30, 1)), radius=PILE_R, color=INK, opacity=0.0)
            ptr = VGroup(Line(PL(0, 0), PL(0, 1), stroke_color=INK_HI, stroke_width=W_LINE),
                         Circle(radius=0.04, stroke_width=0, fill_color=INK_HI, fill_opacity=1.0))
            self.parts[c] = SimpleNamespace(segs=segs, seps=seps, tab=tab, outline=outline, pile=pile, ptr=ptr)
            self.add(segs, seps, tab, outline, pile)
        self.link_m = VGroup(Line(PL(0, 0), PL(0, 1), stroke_color=INK_HI, stroke_width=W_LINE),
                             Circle(radius=0.04, stroke_width=0, fill_color=INK_HI, fill_opacity=1.0),
                             Circle(radius=0.04, stroke_width=0, fill_color=INK_HI, fill_opacity=1.0))
        self.add(self.parts["A"].ptr, self.parts["B"].ptr, self.link_m)
        self.paint()

    @staticmethod
    def ends(c: str):
        """(near end, far end) y of a pointer on bar c: through the bar and 0.16 beyond it, away from the other bar."""
        y = BAR_Y[c]
        return (y - BAR_H / 2, y + BAR_H / 2 + 0.16) if c == "A" else (y + BAR_H / 2, y - BAR_H / 2 - 0.16)

    def pile_points(self, c: str) -> np.ndarray:
        y = BAR_Y[c]
        w = self.widths[c]
        edges = np.concatenate([[0], np.cumsum(w)])
        out = []
        for j in range(3):
            xc = bar_x((edges[j] + edges[j + 1]) / 2)
            for n in range(self.counts[c][j]):
                r, col = divmod(n, 5)
                dy = 0.06 + r * PILE_PITCH
                out.append(PL(xc + (col - 2) * PILE_PITCH, y + BAR_H / 2 + dy if c == "A" else y - BAR_H / 2 - dy))
        return np.array(out)

    def paint(self):
        lv = self.level
        for c in "AB":
            P = self.parts[c]
            y = BAR_Y[c]
            w = self.widths[c] / self.widths[c].sum()
            edges = np.concatenate([[0], np.cumsum(w)])
            for j, s in enumerate(P.segs):
                x0, x1 = bar_x(edges[j]), bar_x(edges[j + 1])
                s.set_points_as_corners([PL(x0, y - BAR_H / 2), PL(x1, y - BAR_H / 2), PL(x1, y + BAR_H / 2),
                                         PL(x0, y + BAR_H / 2), PL(x0, y - BAR_H / 2)])
                s.set_fill(mix(SEG_GREYS[j], INK_HI, 0.7 * self.lit[c][j]), opacity=0.9 * lv)
            for j, s in enumerate(P.seps):
                xs = bar_x(edges[j + 1])
                s.put_start_and_end_on(PL(xs, y - BAR_H / 2), PL(xs, y + BAR_H / 2))
                s.set_stroke(opacity=lv)
            P.tab.set_fill(opacity=lv)
            P.outline.set_stroke(opacity=self.flash[c] * lv)
            pts = self.pile_points(c)
            n = len(pts)
            pp = np.tile(PL(bar_x(0.5), y), (30, 1))
            if n:
                pp[:n] = pts
            P.pile.points = pp
            a = np.zeros(30)
            a[:n] = 0.7
            P.pile.set_opacities(a)
            P.pile.set_fill(opacity=lv * self.pile_level)
            u, shown = self.ptr[c]
            near, far = self.ends(c)
            x = bar_x(u)
            P.ptr[0].put_start_and_end_on(PL(x, near), PL(x, far))
            P.ptr[1].move_to(PL(x, far))
            P.ptr[0].set_stroke(opacity=shown * lv)
            P.ptr[1].set_fill(opacity=shown * lv)
        ua, ub, shown = self.link
        xa, xb = bar_x(ua), bar_x(ub)
        top, bot = self.ends("A")[1], self.ends("B")[1]
        self.link_m[0].put_start_and_end_on(PL(xa, top), PL(xb, bot))
        self.link_m[1].move_to(PL(xa, top))
        self.link_m[2].move_to(PL(xb, bot))
        self.link_m[0].set_stroke(opacity=shown * lv)
        self.link_m[1].set_fill(opacity=shown * lv)
        self.link_m[2].set_fill(opacity=shown * lv)
        return self

    def set_widths(self, c: str, probs):
        self.widths[c] = np.array(probs, dtype=float)
        return self.paint()

    def to_widths(self, c: str, probs, **kw) -> Animation:
        return Tween(self, "_w" + c, probs, **kw)

    # Tween needs plain attributes: expose the widths of each copy as _wA, _wB
    @property
    def _wA(self):
        return self.widths["A"]

    @_wA.setter
    def _wA(self, v):
        self.widths["A"] = np.array(v, dtype=float)

    @property
    def _wB(self):
        return self.widths["B"]

    @_wB.setter
    def _wB(self, v):
        self.widths["B"] = np.array(v, dtype=float)

    def set_pointer(self, c: str, u: float, shown: float = 1.0):
        self.ptr[c] = [float(u), float(shown)]
        return self.paint()

    def to_pointer(self, c: str, u: float, shown: float = 1.0, **kw) -> Animation:
        return Tween(self, "_p" + c, [u, shown], **kw)

    @property
    def _pA(self):
        return self.ptr["A"]

    @_pA.setter
    def _pA(self, v):
        self.ptr["A"] = [float(v[0]), float(v[1])]

    @property
    def _pB(self):
        return self.ptr["B"]

    @_pB.setter
    def _pB(self, v):
        self.ptr["B"] = [float(v[0]), float(v[1])]

    def set_link(self, ua: float, ub: float, shown: float = 1.0):
        self.link = [float(ua), float(ub), float(shown)]
        return self.paint()

    def to_link(self, ua: float, ub: float, shown: float = 1.0, **kw) -> Animation:
        return Tween(self, "link", [ua, ub, shown], **kw)

    def set_lit(self, c: str, seg: int, x: float = 1.0):
        self.lit[c] = np.zeros(3)
        if seg is not None:
            self.lit[c][seg] = x
        return self.paint()

    def set_piles(self, c: str, counts):
        self.counts[c] = [int(n) for n in counts]
        return self.paint()

    def land(self, c: str, seg: int):
        """One more dot on the pile of segment ``seg`` (0-based) of bar c (call it from a jitter's apply)."""
        self.counts[c][seg] += 1
        return self.paint()

    def to_outline_flash(self, c: str, run_time: float = 0.6) -> Animation:
        def f(m, a):
            m.flash[c] = math.sin(math.pi * a)
            m.paint()
        return UpdateFromAlphaFunc(self, f, run_time=run_time, rate_func=linear, suspend_mobject_updating=False)


STRIP_X, STRIP_Y0, STRIP_Y1, STRIP_CY = 4.3, -1.65, 1.95, -0.05


class Strip(Lasting):
    """The strip of S07 (3.6): axis, ticks (one per distinct height), centre line (the estimate), the band
    (variance) with its edge lines, the ghost edges."""

    def __init__(self, half: float | None = None):
        super().__init__()
        self.axis = Line(PL(STRIP_X, STRIP_Y0), PL(STRIP_X, STRIP_Y1), stroke_color=GREY_3, stroke_width=W_LINE)
        self.band = soft_band(0.7, 1.0, INK, peak=0.12, edge=0.3).move_to(PL(STRIP_X, STRIP_CY))
        self.edges = VGroup(*[Line(PL(STRIP_X - 0.35, 0), PL(STRIP_X + 0.35, 0), stroke_color=INK, stroke_width=W_LINE)
                              for _ in range(2)])
        self.ghost_edges = VGroup(*[Line(PL(STRIP_X - 0.35, 0), PL(STRIP_X + 0.35, 0), stroke_color=INK, stroke_width=W_LINE)
                                    for _ in range(2)])
        self.ticks = VGroup()
        self.centre = Line(PL(STRIP_X - 0.45, STRIP_CY), PL(STRIP_X + 0.45, STRIP_CY), stroke_color=INK, stroke_width=W_LINE)
        self.add(self.axis, self.band, self.ghost_edges, self.edges, self.ticks, self.centre)
        self.half = TOY.half["straight"] if half is None else float(half)
        self.band_on = 1.0
        self.ghost = 0.0
        self.tick_dim = 1.0
        self.centre_hi = 0.0
        self.counts = {}
        self._tick_of = {}
        self.paint()

    def paint(self):
        lv = self.level
        h = max(self.half, 1e-3)
        self.band.stretch_to_fit_height(2 * h).move_to(PL(STRIP_X, STRIP_CY))
        self.band.set_fill(opacity=lv * self.band_on)
        for s, e in zip((1, -1), self.edges):
            e.put_start_and_end_on(PL(STRIP_X - 0.35, STRIP_CY + s * h), PL(STRIP_X + 0.35, STRIP_CY + s * h))
            e.set_stroke(opacity=0.45 * lv * self.band_on)
        g = TOY.half["none"]
        for s, e in zip((1, -1), self.ghost_edges):
            e.put_start_and_end_on(PL(STRIP_X - 0.35, STRIP_CY + s * g), PL(STRIP_X + 0.35, STRIP_CY + s * g))
            e.set_stroke(opacity=0.30 * self.ghost * lv)
        self.axis.set_stroke(opacity=lv)
        self.centre.set_stroke(mix(INK, INK_HI, self.centre_hi), opacity=lv)
        for D, m in self._tick_of.items():
            n = self.counts[D]
            m.set_stroke(opacity=min(0.3 + 0.1 * (n - 1), 0.7) * self.tick_dim * lv)
        return self

    def add_tick(self, D: float):
        """One comparison lands: a new tick at its height, or 10% more on the tick that is there (at most 70%)."""
        D = round(float(D), 9)
        self.counts[D] = self.counts.get(D, 0) + 1
        if D not in self._tick_of:
            y = TOY.tick_y(D)
            m = Line(PL(STRIP_X - 0.25, y), PL(STRIP_X + 0.25, y), stroke_color=INK_HI, stroke_width=W_LINE)
            self._tick_of[D] = m
            self.ticks.add(m)
        return self.paint()

    def set_ticks(self, values):
        for D in values:
            self.add_tick(D)
        return self

    def set_band(self, half: float, on: float = 1.0):
        self.half, self.band_on = float(half), float(on)
        return self.paint()

    def to_band(self, half: float, **kw) -> Animation:
        return Tween(self, "half", half, **kw)

    def to_ghost(self, x: float, **kw) -> Animation:
        return Tween(self, "ghost", x, **kw)

    def to_tick_dim(self, x: float, **kw) -> Animation:
        return Tween(self, "tick_dim", x, **kw)


# =================================================================================================== the scale (3.6)

ZERO_X, COND_X, TRACK_Y = -5.6, 4.4, (-1.3, -2.3)
RESULT_X = (3.65, 1.45)
RESULT_L = (9.25, 7.05)


def run_x(t: float, t0: float, t1: float, L: float, v: float | None = None, x0: float = ZERO_X) -> float:
    """The run of 3.6: one steady speed v = L / (t1 - t0 - 0.3), then a 0.6 s ease-out that stops exactly at t1."""
    v = L / (t1 - t0 - 0.3) if v is None else v
    if t <= t0:
        return x0
    if t >= t1:
        return x0 + L
    if t <= t1 - 0.6:
        return x0 + v * (t - t0)
    return x0 + L - (v / 1.2) * (t1 - t) ** 2


def run2_start(t2: float, v1: float, L: float = RESULT_L[1]) -> float:
    """When run 2 must start so that it stops at t2 with run 1's speed v1."""
    return t2 - L / v1 - 0.3


def _horizon_points():
    stem = [PL(4.4, -0.6), PL(4.9, -0.5)]
    b1 = [PL(4.9, -0.5), PL(6.2, -0.25)]
    b2 = [PL(4.9, -0.5), PL(6.2, -0.5)]
    return stem, b1, b2


class Ruler(Lasting):
    """The scale of S08 and S09 (3.6): zero tick, two tracks, condition line (no glow), two results (white marker,
    small glow, trail), and the faint longer-horizon fork."""

    idle = True

    def __init__(self):
        super().__init__()
        self.zero = Line(PL(ZERO_X, -2.75), PL(ZERO_X, -1.0), stroke_color=GREY_1, stroke_width=W_BOLD)
        self.tracks = VGroup(*[Line(PL(ZERO_X, y), PL(COND_X, y), stroke_color=GREY_3, stroke_width=W_LINE) for y in TRACK_Y])
        self.cond = Line(PL(COND_X, -2.7), PL(COND_X, -0.6), stroke_color=INK_HI, stroke_width=W_BOLD)
        stem, b1, b2 = _horizon_points()
        hz = [dots_along(stem, 0.07, 0.012, INK, 1.0)]
        for b in (b1, b2):
            hz.append(dots_along(b, 0.07, 0.012, INK, 1.0, fade=lambda s: (1 - s) ** 1.2))
        self.horizon = VGroup(*hz)
        self.trails = VGroup(*[Line(PL(ZERO_X, y), PL(ZERO_X + 0.01, y), stroke_color=INK_HI, stroke_width=W_HERO) for y in TRACK_Y])
        self.glows = VGroup(*[glow_sprite(0.12, INK_HI, peak=0.5) for _ in TRACK_Y])
        self.heads = VGroup(*[Circle(radius=0.08, stroke_width=0, fill_color=INK_HI, fill_opacity=1.0) for _ in TRACK_Y])
        self.add(self.tracks, self.trails, self.zero, self.cond, self.horizon, self.glows, self.heads)
        self.track = np.array([1.0, 0.0])        # drawn share of each track
        self.x = np.array([ZERO_X, ZERO_X])      # head positions
        self.shown = np.array([1.0, 0.0])        # results shown
        self.cond_level = 0.85
        self.cond_drawn = 1.0
        self.horizon_level = 0.16
        self.zero_on = 1.0
        self.zero_flash = 0.0
        self.paint()

    def paint(self):
        g, t = idle_gain(), film_time()
        lv = self.level
        for i, (tr, y) in enumerate(zip(self.tracks, TRACK_Y)):
            xe = ZERO_X + (COND_X - ZERO_X) * max(self.track[i], 1e-4)
            tr.put_start_and_end_on(PL(ZERO_X, y), PL(xe, y))
            tr.set_stroke(opacity=lv * float(self.track[i] > 1e-3))
        for i, y in enumerate(TRACK_Y):
            x = float(self.x[i])
            tr = self.trails[i]
            tr.put_start_and_end_on(PL(ZERO_X, y), PL(max(x, ZERO_X + 1e-3), y))
            tr.set_stroke(opacity=lv * self.shown[i] * float(x > ZERO_X + 1e-3))
            breath = 1.0 - 0.10 * g * (0.5 - 0.5 * math.cos(TAU_ * t / 2.2 + i))
            self.heads[i].move_to(PL(x, y)).set_fill(opacity=lv * self.shown[i])
            self.glows[i].move_to(PL(x, y)).set_fill(opacity=lv * self.shown[i] * breath)
        self.zero.set_stroke(mix(GREY_1, INK_HI, self.zero_flash), opacity=lv * self.zero_on)
        ye = -2.7 + 2.1 * max(self.cond_drawn, 1e-4)
        self.cond.put_start_and_end_on(PL(COND_X, -2.7), PL(COND_X, ye))
        self.cond.set_stroke(opacity=lv * self.cond_level * float(self.cond_drawn > 1e-3))
        for h in self.horizon:
            h.set_fill(opacity=lv * self.horizon_level)
        return self

    def set_result(self, i: int, x: float, shown: float = 1.0):
        self.x[i], self.shown[i] = float(x), float(shown)
        return self.paint()

    def to_track(self, i: int, f: float = 1.0, **kw) -> Animation:
        kw.setdefault("rate_func", linear)
        goal = self.track.copy()
        goal[i] = f
        return Tween(self, "track", goal, **kw)

    def to_condition(self, x: float = 1.0, **kw) -> Animation:
        return Tween(self, "cond_level", x, **kw)

    def to_horizon(self, x: float, **kw) -> Animation:
        return Tween(self, "horizon_level", x, **kw)

    def glimmer(self, run_time: float = 0.8) -> Animation:
        def f(m, a):
            m.horizon_level = 0.16 + 0.08 * math.sin(math.pi * a)
            m.paint()
        return UpdateFromAlphaFunc(self, f, run_time=run_time, rate_func=linear, suspend_mobject_updating=False)


# =================================================================================================== the emblem


def _emblem_clearance(factor: float) -> float:
    th_ = np.linspace(0, TAU_, 4000)
    r = 0.16 * family_r(th_, factor)
    curve = np.column_stack([r * np.cos(th_), r * np.sin(th_)])
    dots = [np.array([0.491 - 0.44, 0.243 - 0.20]), np.array([0.483 - 0.44, 0.149 - 0.20])]
    return float(min(np.linalg.norm(curve - d, axis=1).min() for d in dots))


EMBLEM_SCALE = 0.9      # the box of Object 6 (1.36 x 0.72) is drawn at 0.9 so that it clears the closed curve's stroke
EMBLEM_FACTOR = 0.58 if _emblem_clearance(0.58) * EMBLEM_SCALE >= 0.02 else 0.65
if _emblem_clearance(EMBLEM_FACTOR) * EMBLEM_SCALE < 0.02:
    raise RuntimeError("world: the emblem's family mark comes within 0.02 of a white dot even with factor 0.65")


class Emblem(Lasting):
    """The drawn miniature of the pilot (Object 6): 1.36 x 0.72, no numerals, no words; the family mark encloses
    both white dots."""

    def __init__(self, centre=EMBLEM_HOME):
        super().__init__()
        o = np.asarray(centre, dtype=float)
        E = lambda x, y: o + C(x, y)  # noqa: E731
        self.zero = Line(E(-0.62, -0.30), E(-0.62, -0.04), stroke_color=GREY_1, stroke_width=W_LINE)
        self.cond = Line(E(0.50, -0.32), E(0.50, -0.02), stroke_color=INK_HI, stroke_width=W_LINE)
        self.trail1 = Line(E(-0.62, -0.10), E(0.416, -0.10), stroke_color=INK_HI, stroke_width=W_LINE)
        self.trail2 = Line(E(-0.62, -0.24), E(0.170, -0.24), stroke_color=INK_HI, stroke_width=W_LINE)
        self.stub = dots_along([E(0.50, -0.02), E(0.66, 0.02)], 0.035, 0.007, INK, 0.30)
        disc = sunflower_points(60, 0.16, (0.0, 0.0), jitter=0.2, seed=SEEDS["family"])[:, :2]
        whites = [np.array([0.051, 0.043]), np.array([0.043, -0.051])]
        wi = []
        for wpt in whites:
            d = np.linalg.norm(disc - wpt, axis=1)
            d[wi] = 9
            i = int(np.argmin(d))
            disc[i] = wpt
            wi.append(i)
        cols = np.tile([*GREY_2.to_rgb(), 0.9], (60, 1))
        radii = np.full(60, 0.0085)
        for i in wi:
            cols[i] = [*INK_HI.to_rgb(), 1.0]
            radii[i] = 0.012
        dc = o + C(0.44, 0.20)
        self.disc = DotCloud(np.column_stack([dc[0] + disc[:, 0], dc[1] + disc[:, 1], np.zeros(60)]), radius=radii, rgbas=cols)
        th_ = np.linspace(0, TAU_, 64, endpoint=False)
        r = 0.16 * family_r(th_, EMBLEM_FACTOR)
        self.mark = smooth_closed(np.column_stack([dc[0] + r * np.cos(th_), dc[1] + r * np.sin(th_), 0 * th_]),
                                  stroke_color=INK, stroke_width=W_HAIR, stroke_opacity=0.55, fill_opacity=0)
        self.add(self.zero, self.cond, self.trail1, self.trail2, self.stub, self.disc, self.mark)
        self.scale(EMBLEM_SCALE, about_point=o)
        self.disc.radii = self.disc.radii * EMBLEM_SCALE
        self.stub.radii = self.stub.radii * EMBLEM_SCALE
        self.paint()

    def paint(self):
        lv = self.level
        for m in (self.zero, self.cond, self.trail1, self.trail2):
            m.set_stroke(opacity=lv)
        self.mark.set_stroke(opacity=0.55 * lv)
        self.stub.set_fill(opacity=lv)
        self.disc.set_fill(opacity=lv)
        return self


# =================================================================================================== the pool object


class Pool(Lasting):
    """The pool (Object 1): one DotCloud of 700 points that drift and twinkle, 14 groups with dashed gold outlines,
    gold tints (S11), marked points (S04)."""

    def __init__(self, level: float = 1.0, outlines=None):
        super().__init__()
        self.cloud = DotCloud(POOL_PTS.copy(), radius=POOL_RADII.copy(), color=DATA, opacity=POOL_ALPHA.copy())
        self.cloud.drift(amp=0.045, period=8.0, seed=SEEDS["pool"], twinkle=0.15)
        h = _hash01(SEEDS["pool"] + 1000, self.cloud.ids, 3)
        d = self.cloud._drift
        d["amp"] = 0.03 + 0.03 * h[:, 0]                                  # each point: its own loop of 0.03 to 0.06
        d["w"] = TAU_ / (6.0 + 5.0 * h[:, 1:3])                           # with a period of 6 to 11 s
        self.home = POOL_PTS.copy()
        self.alpha0 = POOL_ALPHA.copy()
        self.tints = VGroup(*[hull_blob(POOL_PTS[GROUPS[n]], pad=0.12, stroke_width=0, fill_color=FOCUS, fill_opacity=0.0)
                              for n in GROUP_NAMES])
        self.outlines = VGroup(*[dashed(GROUP_POLYS[n], FOCUS, W_LINE, 0.0) for n in GROUP_NAMES])
        self.marks = DotCloud(POOL_PTS[MARKED], radius=0.04, color=INK, opacity=0.9, glow=1.0, glow_reach=3.0,
                              ids=np.array(MARKED))
        self.marks.drift(amp=0.045, period=8.0, seed=SEEDS["pool"], twinkle=0.0)
        hm = _hash01(SEEDS["pool"] + 1000, np.array(MARKED), 3)
        self.marks._drift["amp"] = 0.03 + 0.03 * hm[:, 0]
        self.marks._drift["w"] = TAU_ / (6.0 + 5.0 * hm[:, 1:3])
        self.add(self.tints, self.cloud, self.outlines, self.marks)
        self.ol = np.zeros(len(GROUP_NAMES))
        self.tint = np.zeros(len(GROUP_NAMES))
        self.mark_level = 0.0
        self._lamp_alpha = None
        self.level = float(level)
        if outlines:
            self.set_outlines(outlines)
        self.paint()

    @staticmethod
    def idx(name: str) -> np.ndarray:
        return GROUPS[name]

    @staticmethod
    def centre(name: str) -> np.ndarray:
        return GROUP_CENTRES[name] if name in GROUP_CENTRES else np.append(POOL_PTS[GROUPS[name], :2].mean(axis=0), 0.0)

    def outline(self, name: str) -> VMobject:
        return self.outlines[GROUP_NAMES.index(name)]

    def paint(self):
        if self.lamp is not None:
            if self._lamp_alpha is None:
                self._lamp_alpha = self.cloud.rgbas[:, 3].copy()
            self.cloud.set_fill(opacity=1.0)
            self.cloud.rgbas[:, 3] = self._lamp_alpha * self.lev(self.cloud.points)
        else:
            if self._lamp_alpha is not None:
                self.cloud.rgbas[:, 3] = self._lamp_alpha
                self._lamp_alpha = None
            self.cloud.set_fill(opacity=self.level)
        for j, n in enumerate(GROUP_NAMES):
            lv = float(np.mean(self.lev(self.centre(n))))
            self.outlines[j].set_stroke(opacity=float(self.ol[j]) * lv)
            self.tints[j].set_fill(opacity=float(self.tint[j]) * lv)
        self.marks.set_fill(opacity=self.mark_level * self.level)
        return self

    def _vec(self, values: dict, base) -> np.ndarray:
        v = np.array(base, dtype=float).copy()
        for n, x in values.items():
            v[GROUP_NAMES.index(n)] = x
        return v

    def set_outlines(self, values: dict):
        self.ol = self._vec(values, self.ol)
        return self.paint()

    def to_outlines(self, values: dict, lag: float = 0.0, **kw) -> Animation:
        order = [list(values).index(n) if n in values else 99 for n in GROUP_NAMES]
        return Tween(self, "ol", self._vec(values, self.ol), lag=lag, order=order, **kw)

    def set_tints(self, values: dict):
        self.tint = self._vec(values, self.tint)
        return self.paint()

    def to_tints(self, values: dict, **kw) -> Animation:
        return Tween(self, "tint", self._vec(values, self.tint), **kw)

    # group states (immediate)
    def set_gold(self, name: str, on: bool = True):
        i = GROUPS[name]
        self.cloud.set_colors(FOCUS if on else DATA, i)
        self.cloud.set_opacities(np.clip(self.alpha0[i] + (0.2 if on else 0.0), 0, 1), i)
        return self

    def set_lift(self, name: str, dy: float = 0.5, dx: float = 0.0):
        i = GROUPS[name]
        self.cloud.points[i] = self.home[i] + C(dx, dy)
        return self

    # group states (animations: the kit's CloudTo)
    def gold(self, name: str, **kw) -> Animation:
        i = GROUPS[name]
        return self.cloud.to(color=FOCUS, opacity=np.clip(self.alpha0[i] + 0.2, 0, 1), idx=i, **kw)

    def lift(self, name: str, dy: float = 0.5, dx: float = 0.0, **kw) -> Animation:
        i = GROUPS[name]
        return self.cloud.to(centers=self.home[i] + C(dx, dy), idx=i, **kw)

    def remove_group(self, name: str, **kw) -> Animation:
        """Removed: the (gold) points lift 0.6 up and 0.4 left while they fade to 0; the holes stay."""
        i = GROUPS[name]
        kw.setdefault("lag", 0.02 * 39 / 40)
        return self.cloud.to(centers=self.home[i] + C(-0.4, 0.6), opacity=0.0, idx=i, **kw)

    def restore(self, name: str, **kw) -> Animation:
        i = GROUPS[name]
        return self.cloud.to(centers=self.home[i], color=DATA, opacity=self.alpha0[i], idx=i, **kw)

    def set_marks(self, level: float):
        self.mark_level = float(level)
        return self.paint()

    def to_marks(self, level: float, **kw) -> Animation:
        return Tween(self, "mark_level", level, **kw)


# =================================================================================================== passing objects


THREAD_LEVEL = 0.15


def thread_curves(test: TestArc | None = None, k: int = 10) -> list:
    """The ~70 thread paths of S04 (seed 13): from light k (split arrangement) behind the model's core to the pool."""
    start = test.pos(k) if test is not None else light_pos(k, 1.0)
    rng = np.random.default_rng(SEEDS["threads"])
    out = []
    for i in THREAD_ENDS:
        end = POOL_PTS[i]
        bend = rng.uniform(-0.35, 0.35)
        p1 = M_C + C(0.9, 0.12 + 0.5 * bend)
        p2 = M_C + C(-0.9, 0.08 + 0.7 * bend)
        out.append(np.array([bezier([start, p1, p2, end])(s) for s in np.linspace(0, 1, 48)]))
    return out


def make_threads(level: float = THREAD_LEVEL, test: TestArc | None = None) -> VGroup:
    """The threads as hair-thin INK strokes (one VMobject each), to go into ``model.behind``."""
    return VGroup(*[polyline(c, INK, W_HAIR, level) for c in thread_curves(test)])


class Safer(Lasting):
    """``safer?`` (S02, S03): 44 serif INK_HI at left 4.15, baseline 0.4; its backstroke halo breathes."""

    idle = True

    def __init__(self):
        super().__init__()
        self.text = label("safer?")
        self.add(self.text)
        self.paint()

    def paint(self):
        g, t = idle_gain(), film_time()
        b = 1.0 - 0.10 * g * (0.5 - 0.5 * math.cos(TAU_ * t / 2.0))
        self.text.set_fill(opacity=self.level)
        self.text.set_stroke(opacity=self.level * b, background=True)
        return self


def title_lines() -> VGroup:
    """The post's title (S02): two lines, 44 serif INK_HI, backstroke, centred at x = 0."""
    return VGroup(label("title 1"), label("title 2"))


def choice_ring(name: str = "gA") -> Circle:
    return Circle(radius=0.55, stroke_color=INK_HI, stroke_width=W_LINE, fill_opacity=0).move_to(Pool.centre(name))


def sign_off() -> VGroup:
    a, b = label("sign-off 1"), label("sign-off 2")
    return VGroup(a, b).set_opacity(0.9)


BEAM_ENDS = {"gA": C(1.64, 0.66), "gD": C(1.58, 0.16)}
RANGES = {"gA": (0.66, 1.8, 2.75), "gD": (0.16, 2.1, 3.05)}


def beam(name: str, opacity: float = 1.0) -> VMobject:
    """A dashed gold beam from a group through the model's core to its right rim (goes into ``model.between``)."""
    return dashed([Pool.centre(name), BEAM_ENDS[name]], FOCUS, W_LINE, opacity, dash=0.12, gap=0.08, closed=False)


def ranges_hairline(opacity: float = 1.0) -> VMobject:
    return dashed([C(1.75, -0.2), C(3.0, -0.2)], GREY_3, W_LINE, opacity, dash=0.08, gap=0.06, closed=False)


class Range(Lasting):
    """A dotted gold interval on its own row with dotted caps (S11): no fill, no centre line, no edge lines."""

    def __init__(self, name: str):
        super().__init__()
        self.y, self.x0, self.x1 = RANGES[name]
        self.row = DotCloud(np.zeros((40, 3)), radius=0.018, color=FOCUS, opacity=0.0)
        self.caps = DotCloud(np.zeros((10, 3)), radius=0.016, color=FOCUS, opacity=0.0)
        self.add(self.row, self.caps)
        self.paint()

    def paint(self):
        n = max(int(round((self.x1 - self.x0) / 0.06)) + 1, 2)
        n = min(n, 40)
        xs = np.linspace(self.x0, self.x1, n)
        pts = np.zeros((40, 3))
        pts[:n, 0], pts[:n, 1] = xs, self.y
        pts[n:] = [self.x0, self.y, 0]
        a = np.zeros(40)
        a[:n] = 0.95
        self.row.points, self.row.rgbas[:, 3] = pts, a
        cy = np.linspace(-0.12, 0.12, 5)
        caps = np.array([[x, self.y + d, 0] for x in (self.x0, self.x1) for d in cy])
        self.caps.points = caps
        self.caps.rgbas[:, 3] = 0.95
        self.row.set_fill(opacity=self.level)
        self.caps.set_fill(opacity=self.level)
        return self


class PairingGlyph(VGroup):
    """A miniature of the two bars joined by a soft link with no readable form (S08). Baseline: GREY_2, 0.6 wide.
    Oracle: INK_HI, 0.75 wide."""

    def __init__(self, oracle: bool = False):
        super().__init__()
        w = 0.75 if oracle else 0.6
        col = INK_HI if oracle else GREY_2
        top = Line(C(-w / 2, 0.125), C(w / 2, 0.125), stroke_color=col, stroke_width=W_BOLD)
        bot = Line(C(-w / 2, -0.125), C(w / 2, -0.125), stroke_color=col, stroke_width=W_BOLD)
        link = soft_band(w * 0.8, 0.25, col, peak=0.32, edge=0.45, axis=0)
        self.add(link, top, bot)


class StepGlyph(VGroup):
    """An event ring (radius 0.1) and one or two steps with a glowing head (S08 line 1), GREY_1, 0.3 high."""

    def __init__(self, steps: int = 1):
        super().__init__()
        w = 0.7 if steps == 1 else 1.15
        x0 = -w / 2
        ring = Circle(radius=0.1, stroke_color=GREY_1, stroke_width=W_LINE, fill_opacity=0).move_to(C(x0 + 0.1, -0.05))
        pts = [C(x0 + 0.2, -0.05)]
        for k in range(steps):
            pts.append(C(x0 + 0.2 + (w - 0.25) * (k + 1) / steps, -0.05 + (0.15 if k % 2 == 0 else 0.0)))
        path = polyline(pts, GREY_1, W_LINE)
        head = VGroup(glow_sprite(0.1, GREY_1, peak=0.6).move_to(pts[-1]),
                      Circle(radius=0.03, stroke_width=0, fill_color=GREY_1, fill_opacity=1.0).move_to(pts[-1]))
        self.add(ring, path, head)


def step_glyphs() -> VGroup:
    return VGroup(StepGlyph(1).move_to(PL(-0.55, -2.7)), StepGlyph(2).move_to(PL(3.18, -2.7)))


def lens_glyph_positions():
    """The 20 points nearest the lens centre and their places at 2.5 times their distance (Object 1)."""
    d = np.linalg.norm(POOL_PTS[:, :2] - LENS_CENTRE[:2], axis=1)
    idx = np.argsort(d)[:LENS_N]
    return idx, LENS_CENTRE + (POOL_PTS[idx] - LENS_CENTRE) * LENS_MAG, float(d[idx].max())


def _glyph_segments(c):
    return [((c[0] - 0.09, c[1] + 0.035), (c[0] + 0.09, c[1] + 0.035)),
            ((c[0] - 0.135, c[1] - 0.035), (c[0] + 0.135, c[1] - 0.035))]


def lens_check() -> dict:
    """The build checks of the lens: the 20 points within 0.4 of its centre; no two glyphs closer than 0.08."""
    idx, q, far = lens_glyph_positions()
    mn = 9.0
    for i in range(len(q)):
        for j in range(i + 1, len(q)):
            for (a0, a1) in _glyph_segments(q[i]):
                for (b0, b1) in _glyph_segments(q[j]):
                    dx = max(0.0, max(a0[0], b0[0]) - min(a1[0], b1[0]))
                    mn = min(mn, math.hypot(dx, a0[1] - b0[1]))
    return dict(within=far, within_ok=far <= 0.4, glyph_gap=mn, glyph_ok=mn >= 0.08)


def example_glyph(centre) -> VGroup:
    """A request stroke (0.18, GREY_2) over a response stroke (0.27, DATA), stroke W_LINE: strokes, never text."""
    c = np.asarray(centre, dtype=float)
    return VGroup(Line(c + C(-0.09, 0.035), c + C(0.09, 0.035), stroke_color=GREY_2, stroke_width=W_LINE),
                  Line(c + C(-0.135, -0.035), c + C(0.135, -0.035), stroke_color=DATA, stroke_width=W_LINE))


def make_lens(strict: bool = True) -> VGroup:
    """The magnifier of S01 (Object 1): a BG disc, the glyphs (clipped to the circle) and the rim. With strict=True it
    raises when the check of Object 1 fails (it does for this pool: see lens_check()); use glyphs_in_place()."""
    chk = lens_check()
    if strict and not (chk["within_ok"] and chk["glyph_ok"]):
        raise RuntimeError(f"world: the lens fails its build check ({chk}); the storyboard's fallback is "
                           f"world.glyphs_in_place() (8 points 0.5 apart open into glyphs in place)")
    idx, q, _ = lens_glyph_positions()
    clip = Circle(radius=LENS_R, stroke_width=0, fill_opacity=0).move_to(LENS_CENTRE)
    disc = Circle(radius=LENS_R, stroke_width=0, fill_color=BG, fill_opacity=1.0).move_to(LENS_CENTRE)
    glyphs = VGroup(*[example_glyph(p) for p in q])
    set_clip(glyphs, clip)
    rim = Circle(radius=LENS_R, stroke_color=INK, stroke_width=W_LINE, stroke_opacity=0.6, fill_opacity=0).move_to(LENS_CENTRE)
    g = VGroup(clip, disc, glyphs, rim)
    g.clip, g.disc, g.glyphs, g.rim, g.idx = clip, disc, glyphs, rim, idx
    return g


def glyphs_in_place(n: int = 8, gap: float = 0.5) -> tuple[np.ndarray, VGroup]:
    """The fallback of S01: n pool points near the lens centre, each 0.5 or more from the others, open into glyphs
    in place. Returns (indices, glyphs)."""
    order = np.argsort(np.linalg.norm(POOL_PTS[:, :2] - LENS_CENTRE[:2], axis=1))
    pick = []
    for i in order:
        if all(np.linalg.norm(POOL_PTS[i, :2] - POOL_PTS[j, :2]) >= gap for j in pick):
            pick.append(int(i))
        if len(pick) == n:
            break
    return np.array(pick), VGroup(*[example_glyph(POOL_PTS[i]) for i in pick])


class Lamp:
    """The lamp of S10 (3.8): a soft circle of light round a moving centre L(t) that draws nothing. Every frame it
    raises each part of the question under it toward 100%: level + (1 - level) * s(d), s = 1 for d <= 0.8, 0 for
    d >= 1.1 (smoothstep between), times its strength. ``attach(scene, objects)``; move ``lamp.x``/``lamp.y``
    (ValueTrackers, canvas; keep x <= 5.2 and y >= -2.3) and ``lamp.strength``; ``detach()`` at the end."""

    def __init__(self, x: float = -5.0, y: float = 2.0):
        self.x, self.y, self.strength = ValueTracker(x), ValueTracker(y), ValueTracker(0.0)
        self.objects, self.driver = [], None

    def fn(self, p):
        c = np.array([min(self.x.get_value(), 5.2), max(self.y.get_value(), -2.3)])
        d = np.linalg.norm(np.atleast_2d(p)[:, :2] - c, axis=1)
        return self.strength.get_value() * (1 - smoothstep(0.8, 1.1, d))

    def attach(self, scene, objects):
        self.objects = list(objects)
        for o in self.objects:
            o.lamp = self.fn

        def step(m):
            for o in self.objects:
                o.paint()
        self.driver = _driver(scene, step)
        scene.add(self.x, self.y, self.strength)
        return self

    def detach(self):
        for o in self.objects:
            o.lamp = None
            o.paint()
        if self.driver is not None:
            self.driver.clear_updaters()
        return self


def web(copy_a=MODEL, copy_b=COPY_B) -> SimpleNamespace:
    """The oracle's web of S09 (3.8), P-local: two soft trees and one woven sheet (vector art: bake it, wipe it in with
    set_clip, fold it by stretching the layer to height 0.02 onto y = -1.3) and the bright run (live on top)."""
    rng = np.random.default_rng(SEEDS["web"])
    parts = VGroup()
    sheet = VMobject(stroke_color=INK, stroke_width=W_HAIR, stroke_opacity=0.10, fill_opacity=0)
    ends = {}
    for c, col, root, arc_x, end_x in (("A", copy_a, (-4.9, 0.75), -3.9, -2.9), ("B", copy_b, (0.1, 0.75), -0.9, -1.9)):
        wedge = VMobject(stroke_width=0, fill_color=col, fill_opacity=0.10)
        wedge.set_points_as_corners([PL(*root), PL(arc_x, 0.15), PL(arc_x, 1.35), PL(*root)])
        arc = VMobject(stroke_color=col, stroke_width=W_BOLD, stroke_opacity=0.35, fill_opacity=0)
        arc.set_points_smoothly([PL(arc_x + 0.05 * math.sin(k), 0.15 + 1.2 * k / 8) for k in range(9)])
        ys = 0.75 + 0.067 * (np.arange(27) - 13)
        fan = VMobject(stroke_color=col, stroke_width=W_HAIR, stroke_opacity=0.5, fill_opacity=0)
        for k, y in enumerate(ys):
            a = PL(arc_x, 0.15 + 1.2 * (k + 0.5) / 27)
            fan.start_new_path(a)
            fan.add_line_to(PL(end_x, y))
        ends[c] = [PL(end_x, y) for y in ys]
        parts.add(wedge, arc, fan)
    for a in ends["A"]:
        for b in ends["B"]:
            mid = (a + b) / 2 + C(0, 0.04 * (rng.random() - 0.5))
            sheet.start_new_path(a)
            sheet.add_quadratic_bezier_curve_to(mid, b)
    parts.add(sheet)
    ia, ib = int(rng.integers(5, 22)), int(rng.integers(5, 22))
    ja, jb = int(rng.integers(0, 27)), int(rng.integers(0, 27))
    run = VGroup(
        polyline([PL(-4.9, 0.75), PL(-3.9, 0.15 + 1.2 * (ia + 0.5) / 27), ends["A"][ja]], copy_a, W_LINE, 0.9),
        polyline([PL(0.1, 0.75), PL(-0.9, 0.15 + 1.2 * (ib + 0.5) / 27), ends["B"][jb]], copy_b, W_LINE, 0.9),
        ArcBetweenPoints(PL(-3.9, 0.15 + 1.2 * (ia + 0.5) / 27), PL(-0.9, 0.15 + 1.2 * (ib + 0.5) / 27), angle=-0.5,
                         stroke_color=INK_HI, stroke_width=W_LINE),
        ArcBetweenPoints(ends["A"][ja], ends["B"][jb], angle=-0.6, stroke_color=INK_HI, stroke_width=W_LINE),
    )
    return SimpleNamespace(art=parts, run=run)


# =================================================================================================== strings (3.10)

#  key: (string, size, colour, x, y, edge, space)   space "C" canvas, "P" P-local
STRINGS = {
    "model": ("model", "label", MODEL, 0.5, 1.95, ORIGIN, "C"),
    "safety test": ("safety test", "label", INK, 4.0, 0.45, LEFT, "C"),
    "post-training examples": ("post-training examples", "label", DATA, -6.1, -1.4, LEFT, "C"),
    "data change": ("data change", "label", FOCUS, -6.1, -1.4, LEFT, "C"),
    "computation": ("computation", "label", GREY_1, -3.2, -2.34, RIGHT, "C"),
    "title 1": ("Which training data should we change", "title", INK_HI, 0.0, 0.5, ORIGIN, "C"),
    "title 2": ("to make an AI safer?", "title", INK_HI, 0.0, -0.3, ORIGIN, "C"),
    "safer?": ("safer?", "title", INK_HI, 4.15, 0.4, LEFT, "C"),
    "held back": ("held back", "label", GREY_1, 4.85, 0.45, LEFT, "C"),     # 3.10 says 4.9: its right end would be 6.43
    "associated with this answer": ("associated with this answer", "label", INK, -6.1, -1.4, LEFT, "C"),
    "a shortcut": ("a shortcut", "label", INK, -3.2, -2.84, RIGHT, "C"),
    "tiny learner": ("tiny learner", "label", INK, -6.3, -0.95, LEFT, "P"),
    "one event": ("one event", "label", INK, -4.9, 0.75, ORIGIN, "P"),
    "copy A@column": ("copy A", "label", MODEL, -0.3, 0.86, LEFT, "P"),
    "copy B@column": ("copy B", "label", COPY_B, -0.3, -0.06, LEFT, "P"),
    "the comparison@column": ("the comparison", "label", INK, -0.3, 0.40, LEFT, "P"),
    "copy A@bar": ("copy A", "label", MODEL, -4.45, -1.44, RIGHT, "P"),
    "copy B@bar": ("copy B", "label", COPY_B, -4.45, -2.39, RIGHT, "P"),
    "the comparison@strip": ("the comparison", "label", INK, 4.3, -2.10, ORIGIN, "P"),
    "variance": ("variance", "title", INK_HI, 3.75, 1.0, RIGHT, "P"),
    "coupling": ("coupling", "title", INK_HI, 1.2, -1.98, LEFT, "P"),
    "1,440": ("1,440", "title", INK_HI, -1.5, 0.6, RIGHT, "P"),
    "toy configurations": ("toy configurations", "label", GREY_1, -1.5, 0.05, RIGHT, "P"),
    "one- or two-step": ("one- or two-step", "label", GREY_1, 1.2, -2.8, ORIGIN, "P"),
    "six baselines": ("six baselines", "label", GREY_1, -6.2, -0.45, LEFT, "P"),
    "oracle": ("oracle", "label", INK, -3.35, -1.85, LEFT, "P"),
    "≥20%": ("≥20%", "title", INK_HI, 4.6, -1.5, LEFT, "P"),
    "variance reduction": ("variance reduction", "label", GREY_1, -5.45, -1.0, LEFT, "P"),
    "best baseline": ("best baseline", "label", GREY_1, -5.45, -2.72, LEFT, "P"),
    "target family": ("target family", "label", INK, 3.1, 0.85, RIGHT, "P"),
    "full suppression@curve": ("full suppression", "label", INK, 3.1, 0.45, RIGHT, "P"),
    "full suppression@row": ("full suppression", "label", INK, -1.2, -2.0, RIGHT, "P"),
    "strongest": ("strongest", "label", INK, 3.1, 0.9, RIGHT, "P"),
    "the pilot": ("the pilot", "label", GREY_1, -4.38, -1.7, LEFT, "C"),
    "sign-off 1": ("Notes from an ongoing", "body", INK, 0.5, 2.9, ORIGIN, "C"),
    "sign-off 2": ("research project", "body", INK, 0.5, 2.3, ORIGIN, "C"),
}
CITATION = 'including in "work on reducing noise in counterfactual estimates" (arXiv 2111.06888)'
RESULT_ROWS = {"18.5%": ("display", 3.65, -1.0), "14.1%": ("title", 1.45, -2.0)}


def anchor_of(key: str) -> np.ndarray:
    s, size, col, x, y, edge, space = STRINGS[key]
    return PL(x, y) if space == "P" else C(x, y)


def label(key: str, opacity: float = 1.0):
    """The string ``key`` of 3.10 at its place, size and colour (with a backstroke)."""
    s, size, col, x, y, edge, space = STRINGS[key]
    a = anchor_of(key)
    if key == "full suppression@row":            # 0.2 left of the row's `about` (3.10's -1.2 assumed narrower glyphs)
        a = a.copy()
        a[0] = result_row("14.1%").about.get_left()[0] - 0.2
    return text(s, size, col, a[0], a[1], edge=edge, opacity=opacity)


def result_row(numeral: str) -> VGroup:
    """``about`` (32 serif INK) and the numeral (64 or 44 serif INK_HI) on one row, gap 0.2, right edge at 3.10's x.
    ``row.about`` and ``row.num`` are the parts; the numeral lands whole: FadeIn(row.num, scale=0.92)."""
    size, right, y = RESULT_ROWS[numeral]
    about = backstroke(T("about", "body", INK))
    num = backstroke(T(numeral, size, INK_HI))
    g = row_right([about, num], PL(right, y)[0], PL(right, y)[1], 0.2)
    g.about, g.num = about, num
    return g


def riding_label(copy: str, head) -> np.ndarray:
    """Where ``copy A`` / ``copy B`` ride: 0.25 above (A) or below (B) and left of the head (its right edge and
    baseline). Use with put(label, *riding_label(...)[:2], edge=RIGHT)."""
    h = np.asarray(head, dtype=float)
    return h + (C(-0.25, 0.25) if copy == "A" else C(-0.25, -0.25 - 0.17))


# =================================================================================================== poses (section 4)

POSES = [f"P{i:02d}" for i in range(12)]
REST_STATES = None


def _rest_test(test: TestArc):
    test.set_split(1.0)
    test.set_states(test.states_with(RED_INNER, "pale", outer="dark"))
    test.set_shade(1.0)


def _question(scene, ns, *, pool_level=1.0, outlines=None, model="M0", test="rest", cost=None, level=1.0,
              grey=False, lone=0.1):
    pool = Pool(level=pool_level, outlines=outlines if outlines is not None else {"gA": 0.4, "gB": 0.4, "gC": 0.4, "gD": 0.4})
    lp = LonePoint(lone) if lone is not None else None
    cf = None
    if cost is not None:
        cf = CostFloor(**cost)
    mdl = Model(model)
    ta = TestArc()
    if test == "rest":
        _rest_test(ta)
    else:
        test(ta)
    ta.set_grey(1.0 if grey else 0.0)
    objs = [pool] + ([lp] if lp else []) + ([cf] if cf else []) + [mdl, ta]
    for o in (pool, mdl, ta) + ((cf,) if cf else ()):
        if level != 1.0:
            o.set_level(o.level * level)
    scene.add(*objs)
    ns.pool, ns.lone, ns.cost, ns.model, ns.test = pool, lp, cf, mdl, ta
    ns.question = [o for o in (pool, mdl, ta, cf) if o is not None]
    return ns


def _labels(scene, ns, keys, opacity=None):
    opacity = opacity or {}
    for k in keys:
        m = label(k, opacity.get(k, 1.0))
        ns.labels[k] = m
        scene.add(m)


def pose(name: str, scene) -> SimpleNamespace:
    """Build pose ``name`` (P00 to P11) in ``scene``: every object in its exact state, the camera on its station.
    Returns the namespace of the objects (see the guide at the top of this file)."""
    if name not in POSES:
        raise KeyError(f"world.pose: no pose {name!r}; the poses are {POSES}")
    _LAST_SCENE[0] = scene
    ns = SimpleNamespace(name=name, scene=scene, pool=None, model=None, twin=None, test=None, cost=None, lone=None,
                         boundary=None, emblem=None, fork=None, bars=None, strip=None, field=None, ruler=None,
                         labels={}, extra={}, tag=None, question=[], station=None)
    ns.label = lambda k: ns.labels[k]
    tag = False
    REST_COST = dict(segments="outline", line=1.0, tick=True, lane=1.0)
    P02_COST = dict(segments="outline", line=1.0, tick=True, lane=0.0)
    ten = {n: 0.25 for n in EXTRA_NAMES}

    if name == "P00":
        ns.station = "TEST-IN"

        def t00(ta):
            ta.set_split(0.0)
            ta.set_shade_on(0.0)
            ta.set_states({k: "hollow" for k in range(24)})
        _question(scene, ns, pool_level=0.1, outlines={}, test=t00)
        pulse = Runner(ask_path(10, ns.test), INK, duration=0.5, tail=0.2, radius=0.045, halo=0.16)
        pulse.set_time(0.15)
        scene.add(pulse)
        ns.extra["pulse"] = pulse

    elif name == "P01":
        ns.station = "W"

        def t01(ta):
            ta.set_split(0.0)
            ta.set_shade_on(0.0)
            ta.set_states(ta.states_with(RED_FIRST, "pale"))
        _question(scene, ns, outlines={"gA": 0.6, "gB": 0.6, "gC": 0.6, "gD": 0.6}, test=t01)
        _labels(scene, ns, ["data change"])
        tag = True

    elif name == "P02":
        ns.station = "W"

        def t02(ta):
            ta.set_split(0.0)
            ta.set_shade_on(0.0)
            ta.set_states(ta.states_with(RED_FIRST, "pale"))
        _question(scene, ns, outlines={"gA": 0.6, "gB": 0.6, "gC": 0.6, "gD": 0.6, **ten}, test=t02, cost=P02_COST)
        s = Safer()
        scene.add(s)
        ns.extra["safer"] = s
        ns.labels["safer?"] = s.text
        tag = True

    elif name == "P03":
        ns.station = "STARE"

        def t03(ta):
            ta.set_split(1.0)
            st = {k: "pale" for k in INNER}
            st.update({k: ("red" if k in RED_OUTER else "pale") for k in OUTER})
            ta.set_states(st)
            ta.set_shade(0.0)
            ta.set_haze(0.1 / 0.6, 0.0, ks=INNER)
        _question(scene, ns, outlines={"gA": 0.6, "gB": 0.6, "gC": 0.6, "gD": 0.6, **ten}, model="M*", test=t03,
                  cost=P02_COST)
        ns.cost.set_level(0.0)
        hb = label("held back")
        scene.add(hb)
        set_station(scene, "STARE")
        follow(scene, hb, anchor_of("held back"))
        ns.labels["held back"] = hb
        tag = True

    elif name == "P04":
        ns.station = "W"
        _question(scene, ns, outlines={"gA": 0.4, "gB": 1.0, "gC": 0.4, "gD": 0.4, **ten}, cost=P02_COST)
        ns.pool.set_gold("gB").set_lift("gB", 0.5)
        ns.pool.set_marks(0.1)
        th_ = make_threads(0.10, ns.test)
        ns.model.behind.add(th_)
        ns.extra["threads"] = th_
        tw = Twin()
        scene.add(tw)
        ns.twin = tw
        _labels(scene, ns, ["associated with this answer"], {"associated with this answer": 0.4})
        tag = True

    elif name == "P05":
        ns.station = "SPECK"
        _question(scene, ns, cost=REST_COST, level=0.15, grey=True, lone=1.0)
        ns.cost.set_level(0.0)
        b = Boundary()
        scene.add(b)
        ns.boundary = b

    elif name in ("P06", "P07", "P08", "P09"):
        ns.station = "P"
        _question(scene, ns, cost=REST_COST, level=0.15, grey=True, lone=None)
        ns.cost.set_level(0.0)
        b = Boundary()
        scene.add(b)
        ns.boundary = b
        if name == "P06":
            _pilot_p06(scene, ns)
        elif name == "P07":
            _pilot_p07(scene, ns)
        elif name == "P08":
            _pilot_p08(scene, ns)
        else:
            _pilot_p09(scene, ns)
        tag = name in ("P06", "P07")

    elif name == "P10":
        ns.station = "W"
        _question(scene, ns, cost=REST_COST, level=0.35, lone=None)
        b = Boundary(closed=True)
        em = Emblem()
        scene.add(b, em)
        ns.boundary, ns.emblem = b, em
        _labels(scene, ns, ["the pilot"])
        tag = True

    elif name == "P11":
        ns.station = "W"
        _question(scene, ns, outlines={"gA": 1.0, "gB": 0.4, "gC": 0.4, "gD": 1.0}, cost=REST_COST, lone=None)
        ns.pool.set_tints({"gA": 0.12, "gD": 0.12})
        beams = VGroup(beam("gA", 0.3), beam("gD", 0.3))
        ns.model.between.add(beams)
        hair = ranges_hairline()
        ra, rd = Range("gA"), Range("gD")
        scene.add(hair, ra, rd)
        ns.extra.update(beams=beams, ranges=VGroup(ra, rd), hairline=hair)
        b = Boundary(closed=True)
        em = Emblem()
        scene.add(b, em)
        ns.boundary, ns.emblem = b, em
        _labels(scene, ns, ["the pilot"])
        so = sign_off()
        scene.add(so)
        ns.extra["signoff"] = so
        ns.labels["sign-off 1"], ns.labels["sign-off 2"] = so[0], so[1]
        tag = True

    set_station(scene, ns.station)
    scene.camera.frame.save_state()
    if tag:
        ns.tag = scene.hud_tag()
        scene.add(ns.tag)
    return ns


def _pilot_p06(scene, ns):
    fork = Fork()
    fork.set_nodes(TOY.nodes("A"), TOY.nodes("B"))
    fork.comp = 1.0
    fork.paint()
    bars = ChoiceBars({"A": TOY.bars["A2"], "B": TOY.bars["B2"]})
    bars.set_pointer("A", 0.24, 1.0)
    bars.set_pointer("B", 0.78, 1.0)
    scene.add(bars, fork)
    ns.fork, ns.bars = fork, bars
    _labels(scene, ns, ["one event", "copy A@column", "the comparison@column", "copy B@column"])


def _pilot_p07(scene, ns):
    fork = Fork()
    fork.set_nodes(TOY.nodes("A", upto=2), TOY.nodes("B", upto=2))
    fork.set_ghosts(TOY.ghost_edges())
    fork.set_level(0.45)
    bars = ChoiceBars({"A": TOY.bars["A2"], "B": TOY.bars["B2"]})
    bars.set_link(TOY.final_link, TOY.final_link, 1.0)
    bars.lit["A"][TOY.seg(TOY.bars["A2"], TOY.final_link)] = 1.0
    bars.lit["B"][TOY.seg(TOY.bars["B2"], TOY.final_link)] = 1.0
    ca, cb = TOY.pile_counts["line6"]
    bars.counts = {"A": list(ca), "B": list(cb)}
    bars.paint()
    strip = Strip(TOY.half["straight"])
    strip.tick_dim = 1 / 3
    for f in TOY.futures:
        strip.add_tick(f["D"])
    scene.add(strip, bars, fork)
    ns.fork, ns.bars, ns.strip = fork, bars, strip
    _labels(scene, ns, ["copy A@bar", "copy B@bar", "variance", "coupling"])


def _pilot_p08(scene, ns):
    field = Field(park=1.0, units=0.6)
    field.set_family(1.0)
    ruler = Ruler()
    ruler.set_result(0, ZERO_X, 1.0)
    scene.add(field, ruler)
    ns.field, ns.ruler = field, ruler
    _labels(scene, ns, ["variance reduction", "best baseline", "≥20%", "target family"])


def _pilot_p09(scene, ns):
    field = Field(park=1.0, units=0.4)
    field.family, field.lower = 1.0, 1.0
    field.lit = np.ones(2)
    field.paint()
    ruler = Ruler()
    ruler.track[:] = 1.0
    ruler.x[:] = [ZERO_X + RESULT_L[0], ZERO_X + RESULT_L[1]]
    ruler.shown[:] = 1.0
    ruler.cond_level = 1.0
    ruler.paint()
    threads = VGroup(*[Line(STRONGEST_START, STRONGEST_ENDS[u], stroke_color=INK, stroke_width=W_LINE, stroke_opacity=0.15)
                       for u in ("u1", "u2")])
    scene.add(field, ruler, threads)
    ns.field, ns.ruler = field, ruler
    ns.extra["strongest threads"] = threads
    _labels(scene, ns, ["variance reduction", "best baseline", "≥20%", "full suppression@row", "strongest"])
    for num in ("18.5%", "14.1%"):
        r = result_row(num)
        scene.add(r)
        ns.labels["about " + num] = r

