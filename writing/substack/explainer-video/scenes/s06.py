"""S06 A tiny learner (storyboard section 5, S06). Opens in pose P05 (SPECK), ends in pose P06 (P).

# qa: bleed      (the open boundary crosses |x| = 6.4, as in every scene from S05 to S09)

Beats (rows of the storyboard; every time below is read from timings.json, none is typed by hand):
  at(0)                    the point's halo swells once; camera SPECK -> P (clock_move, 3.0 s); `tiny learner`
                           lands in the pause after "learner,".
  "suppressing"            tab of bar A and the tag on together; a thread leaves the point (an L-curve) to the tab;
                           the bar unrolls (1.2 s in all); three faint dashed stubs fan out (0.5 s).
  "event"                  segment 2 lights (no pointer) and its stub brightens; the point steps along it with a
                           tail (1.0 s); a white ring marks mid-step; `one event`; two faint dotted steps reach on;
                           from "behaviour" the bar takes its new widths (0.6 s) and the lit segment settles.
  at(1)                    the point runs back along its tail; the start stays as a grey dot; the point takes the
                           event's step again in blue (copy A, 0.9 s), its ring is lit, the tab turns blue; the
                           white path, dotted steps, stubs and thread fade; `copy A` lands.
  "other"                  a violet point at the start; a copy of the pre-event bar slides down with a violet tab;
                           its segment 2 lights; the violet point travels level; its ring appears and goes hollow on
                           "suppressed"; the bar does not change; `copy B` lands.
  at(2)                    step 1 in lock-step: pointers drop (A u = 0.57, B u = 0.18), heads move.
  line_end(2)              widths change; step 2 (A u = 0.24, B u = 0.78); the comparison draws from head to head;
                           the three labels settle in one column right of it.
  (Labels: `copy A` / `copy B` ride on the right of their heads; see the departures below.)

Departures from the storyboard text (reported to the orchestrator):
  - `copy A` and `copy B` ride 0.25 above (A) or below (B) and RIGHT of their heads, not left (3.10). The left
    places collide three times (measured): `copy A` at the event's node would lie on `one event` (x -5.24 to -4.15
    against -5.68 to -4.13, at one height); `copy B` at the event's node would sit 0.03 under its own hollow ring; and
    `copy B` after step 1 would lie across its own violet path. On the right nothing is crossed, the labels lead their
    heads instead of trailing into them, and the final settle into the column right of the comparison is a short
    move (0.47 and 0.44 units) instead of a 1.9-unit jump across each head.
  - The thread leaves the point 14 degrees below the horizontal before it turns down (a rounded L), not along the
    horizontal: the stub of segment 3 leaves the point 3.2 degrees above the horizontal and would merge with it.
  - Riding labels move at up to about 2 to 2.4 units a second in the steps, not 1.5: the heads take 1.5 units in
    0.9 to 1.0 s; each label uses the gentlest ease (GLIDE) over a window a little longer than its head's.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/ and world.py

import numpy as np  # noqa: E402

from kit import *  # noqa: E402,F401,F403
import world  # noqa: E402
from world import PL, TOY  # noqa: E402

FULL = {c: TOY.nodes(c) for c in "AB"}          # P-local nodes: start, after the event, after step 1, after step 2
START = FULL["A"][0]


def _partial(nodes, prog: float) -> list:
    """The nodes of a path that has travelled ``prog`` node-steps (0 = at the start, 3 = the whole path)."""
    if prog >= len(nodes) - 1:
        return list(nodes)
    if prog <= 0:
        return [nodes[0], nodes[0].copy()]
    k = int(math.floor(prog))
    f = prog - k
    out = list(nodes[:k + 1])
    if f > 1e-9:
        out.append(nodes[k] + f * (nodes[k + 1] - nodes[k]))
    return out


def tw(obj, attr: str, value, t0: float, t1: float, rate=MOVE, **kw):
    """A Tween of a state attribute that runs from scene time t0 to t1 inside the row's play."""
    return timed(world.Tween(obj, attr, value, rate_func=rate, run_time=max(t1 - t0, 1e-3), **kw), t0, t1)


def hump(t0: float, t1: float, a0: float, a1: float, b0: float, b1: float, up=MOVE, down=MOVE):
    """A rate over the window [t0, t1]: 0 -> 1 over [a0, a1], hold, 1 -> 0 over [b0, b1] (scene seconds)."""
    def f(u: float) -> float:
        t = t0 + u * (t1 - t0)
        if t <= a0:
            return 0.0
        if t < a1:
            return float(up((t - a0) / (a1 - a0)))
        if t <= b0:
            return 1.0
        if t < b1:
            return 1.0 - float(down((t - b0) / (b1 - b0)))
        return 0.0
    return f


class _Fork(world.Fork):
    """world.Fork with the states that S06 builds up: how far each copy has travelled, whether each head is there,
    the event rings (A's an outline first, then lit; B's lit, then hollow), the start dot and the comparison drawn
    from head to head. With every state at 1 (and both paths whole) it paints exactly what world.Fork paints."""

    progA = progB = 3.0
    showA = showB = 1.0
    ringA = ringA_fill = ringB = ringB_hollow = 1.0
    start_lv = 1.0
    comp_draw = 1.0

    def paint(self):
        self.nodes = {"A": _partial(FULL["A"], self.progA), "B": _partial(FULL["B"], self.progB)}
        super().paint()
        lv = self.level
        breath = 1.0 - 0.35 * idle_gain() * (0.5 - 0.5 * math.cos(2 * math.pi * film_time() / 1.6))
        for c, show, path, tail in (("A", self.showA, self.path_a, self.tail_a), ("B", self.showB, self.path_b, self.tail_b)):
            if show < 1:
                head = self.heads[c]
                head[0].set_fill(opacity=lv * self.paths * breath * show)
                head[1].set_fill(opacity=lv * self.paths * show)
                path.set_stroke(opacity=path.get_stroke_opacity() * show)
                if len(tail.rgbas):
                    rg = np.array(tail.rgbas, dtype=float)
                    rg[:, 3] *= show
                    tail.rgbas = rg
        base = lv * self.rings
        if self.ringA < 1 or self.ringA_fill < 1:
            self.ring_a.set_stroke(opacity=base * self.ringA)
            self.ring_a.set_fill(opacity=base * self.ringA * self.ringA_fill)
        self.ring_b.set_stroke(opacity=base * self.ringB)
        self.ring_b.set_fill(BG if self.ringB_hollow >= 1 else mix(INK, BG, self.ringB_hollow), opacity=base * self.ringB)
        if self.start_lv < 1:
            self.start.set_fill(opacity=lv * self.start_lv)
        if self.comp_draw < 1:
            ya, yb = self.head_a.get_center(), self.head_b.get_center()
            if self.comp_draw > 1e-3 and np.linalg.norm(ya - yb) > 1e-4:
                self.comparison.put_start_and_end_on(yb, yb + (ya - yb) * self.comp_draw)
                self.comparison.set_stroke(opacity=lv)
            else:
                self.comparison.set_stroke(opacity=0.0)
        return self


class _Bars(world.ChoiceBars):
    """world.ChoiceBars with S06's states: bar A unrolls from its tab (grey while the learner is one, blue once it is
    copy A); bar B is a copy that slides down from bar A; pointers drop in from 0.3 away. Lit segments, pointer
    places and shows are plain attributes so that a Tween can move them. With every state at rest it paints exactly
    what world.ChoiceBars paints."""

    revealA = 1.0
    tabA = 1.0
    blueA = 1.0
    lvB = 1.0
    dyB = 0.0
    dropA = dropB = 0.0

    def _get_lit(self, c):
        return self.lit[c]

    def _set_lit(self, c, v):
        self.lit[c] = np.array(v, dtype=float)

    _litA = property(lambda s: s._get_lit("A"), lambda s, v: s._set_lit("A", v))
    _litB = property(lambda s: s._get_lit("B"), lambda s, v: s._set_lit("B", v))
    _uA = property(lambda s: s.ptr["A"][0], lambda s, v: s.ptr["A"].__setitem__(0, float(v)))
    _uB = property(lambda s: s.ptr["B"][0], lambda s, v: s.ptr["B"].__setitem__(0, float(v)))
    _sA = property(lambda s: s.ptr["A"][1], lambda s, v: s.ptr["A"].__setitem__(1, float(v)))
    _sB = property(lambda s: s.ptr["B"][1], lambda s, v: s.ptr["B"].__setitem__(1, float(v)))

    def paint(self):
        super().paint()
        lv = self.level
        A, B = self.parts["A"], self.parts["B"]
        if self.revealA < 1:
            xr = world.bar_x(self.revealA)
            y, h = world.BAR_Y["A"], world.BAR_H / 2
            w = self.widths["A"] / self.widths["A"].sum()
            e = np.concatenate([[0.0], np.cumsum(w)])
            for j, s in enumerate(A.segs):
                x0, x1 = world.bar_x(e[j]), min(world.bar_x(e[j + 1]), xr)
                if x1 - x0 < 1e-3:
                    s.set_fill(opacity=0.0)
                else:
                    s.set_points_as_corners([PL(x0, y - h), PL(x1, y - h), PL(x1, y + h), PL(x0, y + h), PL(x0, y - h)])
            for j, s in enumerate(A.seps):
                if world.bar_x(e[j + 1]) > xr - 1e-3:
                    s.set_stroke(opacity=0.0)
        A.tab.set_fill(MODEL if self.blueA >= 1 else mix(GREY_1, MODEL, self.blueA), opacity=lv * self.tabA)
        if self.lvB < 1 or self.dyB != 0:
            d = UP * self.dyB
            for s in B.segs:
                s.set_fill(opacity=0.9 * lv * self.lvB)
                s.shift(d)
            for s in B.seps:
                s.set_stroke(opacity=lv * self.lvB)
                s.shift(d)
        B.tab.move_to(PL(world.BAR_X0 + 0.04, world.BAR_Y["B"] + self.dyB))
        B.tab.set_fill(opacity=lv * self.lvB)
        if self.dropA:
            A.ptr.shift(UP * 0.3 * self.dropA)
        if self.dropB:
            B.ptr.shift(DOWN * 0.3 * self.dropB)
        return self


class _Walker(world.Lasting):
    """The learner's first step in line 1: the lone point itself walks from the start toward the event's node,
    drawing a white path with a tail (like a copy of the fork, but white and before there are copies); ``k`` swells
    its halo."""

    idle = True

    def __init__(self, lone):
        super().__init__()
        self.lone = lone
        self.s, self.drawn, self.path_lv, self.k, self._k = 0.0, 0.0, 1.0, 1.0, 1.0
        self.path = world.polyline([PL(START[0], START[1]), PL(START[0] + 0.01, START[1])], INK, W_BOLD, 0.0)
        self.tail = Trail()
        self.add(self.path, self.tail)
        self.paint()

    def paint(self):
        n1 = FULL["A"][1]
        S, N = PL(START[0], START[1]), PL(n1[0], n1[1])
        if self.k != self._k:
            self.lone.halo.scale(self.k / self._k)
            self._k = self.k
        self.lone.move_to(S + self.s * (N - S))
        if self.drawn > 1e-3 and self.path_lv > 0:
            self.path.set_points_as_corners([S, S + self.drawn * (N - S)])
            self.path.set_stroke(opacity=0.55 * self.path_lv)
        else:
            self.path.set_stroke(opacity=0.0)
        if self.s > 1e-3:
            tp, a = world.Fork._tail([START, START + self.s * (n1 - START)])
            rgba = np.column_stack([np.tile(np.array(INK.to_rgb()), (len(tp), 1)), 0.45 * a ** 1.3 * self.path_lv])
            self.tail.set_samples(tp, np.full(len(tp), W_BOLD * 0.01), rgba)
        else:
            self.tail.set_samples(np.zeros((0, 3)), np.zeros(0), np.zeros((0, 4)))
        return self


class _Prop(world.Lasting):
    """A passing object whose look is a function of a few state attributes (so that Tweens can drive them)."""

    def __init__(self, fn, mobs=(), **attrs):
        super().__init__()
        for k, v in attrs.items():
            setattr(self, k, np.array(v, dtype=float) if isinstance(v, (list, tuple)) else v)
        self.fn = fn
        self.add(*mobs)
        self.paint()

    def paint(self):
        self.fn(self)
        return self


class _Mover(world.Lasting):
    """Moves a label (not a child: it stays a top-level object of the scene) by the sum of several legs, each with
    its own progress attribute 0..1."""

    def __init__(self, mob, legs: dict):
        super().__init__()
        self.mob, self.legs, self.base = mob, legs, mob.get_center().copy()
        for k in legs:
            setattr(self, k, 0.0)

    def paint(self):
        p = self.base.copy()
        for k, v in self.legs.items():
            p = p + getattr(self, k) * v
        self.mob.move_to(p)
        return self


def _centre_at(lbl, x: float, y: float, edge) -> np.ndarray:
    m = lbl.copy()
    put(m, x, y, edge=edge)
    return m.get_center()


class S06(Narrated):
    def build(self):
        w = world.pose("P05", self)
        lone = w.lone

        # ---------------------------------------------------------------- the cast (all invisible at the first frame)
        bars = _Bars({"A": TOY.bars["event"], "B": TOY.bars["B1"]})
        bars.revealA, bars.tabA, bars.blueA, bars.lvB, bars.dyB = 0.0, 0.0, 0.0, 0.0, world.BAR_Y["A"] - world.BAR_Y["B"]
        bars.dropA = bars.dropB = 1.0
        bars.ptr = {"A": [0.57, 0.0], "B": [0.18, 0.0]}
        bars.paint()

        fork = _Fork()
        fork.progA = fork.progB = 0.0
        fork.showA = fork.showB = 0.0
        fork.ringA = fork.ringA_fill = fork.ringB = fork.ringB_hollow = 0.0
        fork.start_lv, fork.comp_draw, fork.comp = 0.0, 0.0, 1.0
        fork.paint()

        # three possible moves from the start: dashed stubs toward the three nodes that one step could reach
        S = PL(START[0], START[1])
        aims = [PL(-3.9, TOY.y(TOY.step(0.0, c))) for c in range(3)]
        dirs = [(a - S) / np.linalg.norm(a - S) for a in aims]
        angles = [math.atan2(d[1], d[0]) for d in dirs]
        full_stubs = [world.dashed([S + 0.16 * d, S + 0.80 * d], INK, W_LINE, 1.0, dash=0.07, gap=0.05, closed=False)
                      for d in dirs]
        stub_mobs = [m.copy() for m in full_stubs]

        def paint_stubs(p):
            for i, m in enumerate(stub_mobs):
                if p.grow[i] < 1e-3 or p.lv <= 0:
                    m.set_stroke(opacity=0.0)
                    continue
                m.pointwise_become_partial(full_stubs[i], 0.0, float(min(p.grow[i], 1.0)))
                m.set_stroke(opacity=p.lv * (0.28 + 0.47 * p.bright[i]))

        stubs = _Prop(paint_stubs, stub_mobs, grow=[0.0, 0.0, 0.0], bright=[0.0, 0.0, 0.0], lv=1.0)

        # two faint dotted steps that reach on to the right of the event's node (later steps, not yet taken)
        y1 = FULL["A"][1][1]
        xs = np.concatenate([np.arange(-3.62, -2.5, 0.08), np.arange(-2.30, -0.95, 0.08)])
        dot_pts = np.array([PL(x, y1) for x in xs])
        dot_base = 0.5 * (1.0 - 0.65 * (xs - xs[0]) / (xs[-1] - xs[0]))
        dots = DotCloud(dot_pts, radius=0.016, color=INK, opacity=0.0)

        def paint_dots(p):
            n = len(xs)
            a = np.clip((p.reveal * (n + 3) - np.arange(n)) / 3.0, 0.0, 1.0)
            dots.set_opacities(dot_base * a * p.lv)

        dotted = _Prop(paint_dots, [dots], reveal=0.0, lv=1.0)

        # the thread from the point to the top of bar A's tab: a rounded L
        d0 = np.array([math.cos(math.radians(-14)), math.sin(math.radians(-14)), 0.0])
        p0 = S + 0.10 * d0
        p1, p2 = PL(world.BAR_X0 + 0.04, -0.80), PL(world.BAR_X0 + 0.04, world.BAR_Y["A"] + world.BAR_H / 2)
        thread = VMobject(stroke_color=INK, stroke_width=W_LINE, stroke_opacity=0.45, fill_opacity=0.0)
        thread.start_new_path(p0)
        thread.add_cubic_bezier_curve_to(p0 + 0.55 * d0, p1 + 0.35 * UP, p1)
        thread.add_line_to(p2)

        walker = _Walker(lone)

        # z-order: bars, stubs, dots, the white walk, the fork, and the lone point on top of its own path
        self.add(bars, stubs, dotted, walker, fork)
        self.remove(lone)
        self.add(lone)

        # ---------------------------------------------------------------- labels
        tiny = world.label("tiny learner")
        event_lbl = world.label("one event")
        comp_lbl = world.label("the comparison@column")
        nA, nB = [PL(*FULL["A"][i][:2]) for i in range(4)], [PL(*FULL["B"][i][:2]) for i in range(4)]

        def right_of(copy, head):
            """0.25 above (A) or below (B) and RIGHT of the head: the mirror of world.riding_label (left edge, baseline)."""
            rl = world.riding_label(copy, head)
            return 2 * head[0] - rl[0], rl[1]

        a_lbl = world.label("copy A@column")
        col_a = a_lbl.get_center().copy()
        put(a_lbl, *right_of("A", nA[1]), edge=LEFT)
        a0 = a_lbl.get_center().copy()
        a1, a2 = (_centre_at(a_lbl, *right_of("A", nA[k]), LEFT) for k in (2, 3))
        mover_a = _Mover(a_lbl, {"ride1": a1 - a0, "ride2": a2 - a1, "settle": col_a - a2})

        b_lbl = world.label("copy B@column")
        col_b = b_lbl.get_center().copy()
        put(b_lbl, *right_of("B", nB[1]), edge=LEFT)
        b0 = b_lbl.get_center().copy()
        b1, b2 = (_centre_at(b_lbl, *right_of("B", nB[k]), LEFT) for k in (2, 3))
        mover_b = _Mover(b_lbl, {"ride1": b1 - b0, "ride2": b2 - b1, "settle": col_b - b2})

        tag = self.hud_tag()

        # ---------------------------------------------------------------- cue times (scene seconds, from the voice)
        T0, T1, T2 = self.line_start(0), self.line_start(1), self.line_start(2)
        t_tiny = self.word_span(0, "tiny")[0]
        learner_end = self.word_span(0, "learner")[1]
        t_sup = self.word_span(0, "suppressing")[0]
        t_ev = self.word_span(0, "event")[0]
        t_later = self.word_span(0, "later")[0]
        t_beh = self.word_span(0, "behaviour")[0]
        t_oth = self.word_span(1, "other")[0]
        t_supd = self.word_span(1, "suppressed")[0]
        E = self.line_end(2)
        END = self.scene_duration

        # Row 1. Line 1, "We built a tiny learner": the halo swells once; the camera follows to frame P.
        self.at(0)
        world.clock_move(self, "P", T0, T0 + 3.0)
        world.follow(self, tiny, world.anchor_of("tiny learner"))
        self.play_until(
            t_sup,
            tw(walker, "k", 1.5, t_tiny - 0.4, t_tiny + 0.4, PULSE),        # the swell peaks on "tiny"
            tw(lone, "swell", 0.5, t_tiny - 0.4, t_tiny + 0.4, PULSE),
            timed(enter(tiny, run_time=0.6), learner_end - 0.06, learner_end + 0.54),
        )

        # Row 2. "suppressing": the bar of its choices is born from the point (thread, then the bar unrolls); the tag
        # comes on with the bar's first frame (its tab); three possible moves fan out.
        self.at_word(0, "suppressing")
        self.play_until(
            t_ev,
            tw(bars, "tabA", 1.0, t_sup, t_sup + 0.4, ENTER),
            timed(enter(tag, run_time=0.6), t_sup, t_sup + 0.6),
            timed(Create(thread, rate_func=ENTER), t_sup, t_sup + 0.5),
            tw(bars, "revealA", 1.0, t_sup + 0.4, t_sup + 1.2, MOVE),
            tw(stubs, "grow", [1.0, 1.0, 1.0], t_sup + 1.15, t_sup + 1.65, ENTER, lag=0.3, order=angles),
        )

        # Row 3. "event": segment 2 lights by itself (no pointer); the point takes that step; its ring; the later
        # steps reach on; from "behaviour" the bar takes its new widths.
        self.at_word(0, "event")
        step0, step1 = t_ev + 0.3, t_ev + 1.3
        mid = step0 + 0.5 * (step1 - step0)
        self.play_until(
            T1,
            tw(bars, "_litA", [0.0, 1.0, 0.0], t_ev, t_beh + 0.6, hump(t_ev, t_beh + 0.6, t_ev, t_ev + 0.3, t_beh, t_beh + 0.6)),
            tw(stubs, "bright", [0.0, 1.0, 0.0], t_ev, t_ev + 0.3, MOVE),
            tw(walker, "s", 1.0, step0, step1, MOVE),
            tw(walker, "drawn", 1.0, step0, step1, MOVE),
            tw(fork, "ringA", 1.0, mid - 0.1, mid + 0.2, ENTER),
            timed(enter(event_lbl, run_time=0.6), mid - 0.3, mid + 0.3),    # with its ring
            tw(dotted, "reveal", 1.0, t_later - 0.1, t_later + 0.7, MOVE),
            tw(bars, "_wA", TOY.bars["A1"], t_beh, t_beh + 0.6, MOVE),
        )

        # Row 4. Line 2, "One copy learns normally": back to the start; the point becomes copy A (blue) and takes the
        # event's step again; its ring is lit; what was only the learner's fades.
        self.at(1)
        goA0, goA1 = T1 + 0.62, T1 + 1.52
        midA = goA0 + 0.5 * (goA1 - goA0)
        fade0, fade1 = T1 + 0.8, T1 + 1.4
        self.play_until(
            t_oth,
            tw(walker, "s", 0.0, T1, T1 + 0.6, MOVE),
            timed(leave(tiny, run_time=0.6), T1, T1 + 0.6),
            tw(fork, "start_lv", 1.0, T1 + 0.45, T1 + 0.75, ENTER),
            tw(lone, "level", 0.0, T1 + 0.55, T1 + 0.85, MOVE),
            tw(fork, "showA", 1.0, T1 + 0.55, T1 + 0.85, MOVE),
            tw(bars, "blueA", 1.0, T1 + 0.55, T1 + 1.15, MOVE),
            tw(fork, "progA", 1.0, goA0, goA1, MOVE),
            tw(fork, "ringA_fill", 1.0, midA - 0.1, midA + 0.2, ENTER),
            tw(walker, "path_lv", 0.0, fade0, fade1, MOVE),
            tw(stubs, "lv", 0.0, fade0, fade1, MOVE),
            tw(dotted, "lv", 0.0, fade0, fade1, MOVE),
            timed(leave(thread, run_time=0.6), fade0, fade1),
            timed(enter(a_lbl, run_time=0.6), T1 + 1.45, T1 + 2.05),
        )
        self.remove(walker, stubs, dotted, lone)

        # Row 5. "in the other ... suppressed": copy B from the same start; a copy of the pre-event bar slides down;
        # the same choice lights; the violet point stays level; its ring goes hollow on "suppressed".
        self.at_word(1, "other")
        goB0, goB1 = t_oth + 1.1, t_oth + 2.0
        midB = goB0 + 0.5 * (goB1 - goB0)
        self.play_until(
            T2,
            tw(fork, "showB", 1.0, t_oth, t_oth + 0.4, ENTER),
            tw(bars, "lvB", 1.0, t_oth + 0.15, t_oth + 0.75, ENTER),     # seen only as it clears bar A: no double bar
            tw(bars, "dyB", 0.0, t_oth, t_oth + 0.8, ENTER),
            tw(bars, "_litB", [0.0, 1.0, 0.0], t_oth + 0.8, t_supd + 0.6,
               hump(t_oth + 0.8, t_supd + 0.6, t_oth + 0.8, t_oth + 1.1, t_supd, t_supd + 0.6)),
            tw(fork, "progB", 1.0, goB0, goB1, MOVE),
            tw(fork, "ringB", 1.0, midB - 0.1, midB + 0.2, ENTER),
            tw(fork, "ringB_hollow", 1.0, t_supd, t_supd + 0.4, MOVE),
            timed(enter(b_lbl, run_time=0.6), t_supd + 0.32, t_supd + 0.92),
        )

        # Row 6. Line 3, "Both then carry on learning": step 1 in lock-step; a pointer drops on each bar.
        self.at(2)
        self.play_until(
            E,
            tw(bars, "_sA", 1.0, T2, T2 + 0.4, ENTER),
            tw(bars, "_sB", 1.0, T2, T2 + 0.4, ENTER),
            tw(bars, "dropA", 0.0, T2, T2 + 0.4, ENTER),
            tw(bars, "dropB", 0.0, T2, T2 + 0.4, ENTER),
            tw(fork, "progA", 2.0, T2 + 0.3, T2 + 1.3, MOVE),
            tw(fork, "progB", 2.0, T2 + 0.3, T2 + 1.3, MOVE),
            tw(mover_a, "ride1", 1.0, T2 + 0.1, E - 0.02, GLIDE),
            tw(mover_b, "ride1", 1.0, T2 + 0.1, E - 0.02, GLIDE),
        )

        # Row 7. The silence: the bars change; step 2; the comparison draws from head to head; the labels settle.
        self.at_time(E, "the end of line 2")
        down0, down1, up0, up1 = E, E + 0.3, E + 0.39, E + 0.69
        go0, go1 = E + 0.54, E + 1.44
        self.play_until(
            END,
            tw(bars, "_wA", TOY.bars["A2"], E, E + 0.5, MOVE),
            tw(bars, "_wB", TOY.bars["B2"], E, E + 0.5, MOVE),
            tw(bars, "_sA", 0.0, down0, up1, hump(down0, up1, down0, down1, up0, up1)),
            tw(bars, "_sB", 0.0, down0, up1, hump(down0, up1, down0, down1, up0, up1)),
            tw(bars, "dropA", 1.0, down0, up1, hump(down0, up1, down0, down1, up0, up1)),
            tw(bars, "dropB", 1.0, down0, up1, hump(down0, up1, down0, down1, up0, up1)),
            tw(bars, "_uA", 0.24, down1 + 0.01, up0 - 0.01, MOVE),
            tw(bars, "_uB", 0.78, down1 + 0.01, up0 - 0.01, MOVE),
            tw(fork, "progA", 3.0, go0, go1, MOVE),
            tw(fork, "progB", 3.0, go0, go1, MOVE),
            tw(mover_a, "ride2", 1.0, go0 - 0.1, go1 + 0.05, GLIDE),
            tw(mover_b, "ride2", 1.0, go0 - 0.1, go1 + 0.05, GLIDE),
            tw(fork, "comp_draw", 1.0, go1, go1 + 0.5, MOVE),
            tw(mover_a, "settle", 1.0, go1 + 0.27, go1 + 1.07, MOVE),
            tw(mover_b, "settle", 1.0, go1 + 0.27, go1 + 1.07, MOVE),
            timed(enter(comp_lbl, run_time=0.6), go1 + 0.4, go1 + 1.0),
        )
