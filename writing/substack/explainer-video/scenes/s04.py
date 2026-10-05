"""S04 Looking back, or asking what if (storyboard section 5, S04).

Starts in pose P03 (world.pose("P03", self)) and ends in exactly the state that world.pose("P04", ...) builds.

Rows (kit cues, lines from 0). Each row is one play that ends one frame before the next row's cue, so that the
next row's first change lands ON its word (as at() does):

  at(0, lead=0.4)             the supposed tuning undoes itself (0.8 s): needles back to M0 (ring by ring), the inner
                              row back to its five red lights, the soft halo goes, the shade settles over the outer
                              row and its lights go dark; `held back` fades. Camera STARE -> W (clock_move, 2.8 s,
                              GLIDE, across the next row); the cost floor fades back in as the camera returns
                              (clock-driven, once the floor has left the band of the tag)
  at_word(0, "associated")    light 10 flares (0.3 s); one white thread leaves it to the left, behind the model's core
                              disc, and fans into 70 hair-thin threads (1.6 s, each a passing flash); the seven marked
                              points brighten as their threads arrive (INK 90%, small glow, no ring); the threads rest
                              at 15%; `associated with this answer` lands late(0.6) in the pool's label slot
  at_word(0, "automatically") gA, gB, gC, gD brighten in turn (0.6 s pulses, 0.45 s apart) and settle back; the marks
                              stay white; on "future" the five red lights of the inner row pulse together (0.8 s)
  at(1)                       a slow current of light runs along the threads from light 10 back to the pool (2.2 s,
                              linear, one steady speed)
  at_word(1, "other")         threads to 10%, marks to 10%, label to 40% (0.8 s); gB's outline brightens, the other
                              three settle at 40%; gB's points turn gold and lift 0.5 (1.0 s, through "happen")
  at_word(1, "changed")       a hollow gold twin slides out of the model, down to (0.5, -1.45) at half size (1.4 s);
                              its outline needles jump (seed 47, world.Twin's film-clock jitter, which S05 continues);
                              five hollow lights grow from its right rim out to radius 1.5 and flicker undecided

Every temporary thing (the flashes, the current, the flare and pulse sizes) is gone before the scene ends; the
lasting objects end on P04's state numbers exactly (set exactly after each row).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/ and world.py

import numpy as np  # noqa: E402

from kit import *  # noqa: E402,F401,F403
import world  # noqa: E402
from world import (C, CORE_R, DEG, GROUP_NAMES, M_C, M_R, NEEDLE_LEN, NEEDLE_POS, PATTERNS, RED_INNER,  # noqa: E402
                   TWIN_C, TWIN_LIGHT_ANGLES)


# ------------------------------------------------------------------------------------------------ helpers

def _c01(x):
    return np.clip(x, 0.0, 1.0)


def _rate(func, u):
    return float(func(float(np.clip(u, 0.0, 1.0))))


class Clock(Animation):
    """Calls fn(t) on every frame, t = seconds since the play began, and done() once at the end. The mobject must
    already be in the scene (the pool: it is first in the drawing order, so the whole picture is repainted)."""

    def __init__(self, mob, fn, done=None, **kw):
        kw.setdefault("rate_func", linear)
        super().__init__(mob, suspend_mobject_updating=False, **kw)
        self.fn, self.done = fn, done

    def create_starting_mobject(self):
        return Mobject()

    def interpolate_mobject(self, alpha: float) -> None:
        self.fn(float(alpha) * self.run_time)

    def finish(self) -> None:
        super().finish()
        if self.done is not None:
            self.done()


def lag_window(t0: float, t1: float, stagger: float, total: float, func=MOVE) -> dict:
    """Keyword arguments for a world Tween with a per-element lag: the first element moves from t0 to t1 - stagger,
    the last from t0 + stagger to t1 (seconds of a play of ``total`` seconds)."""
    lag = stagger / total
    return dict(lag=lag, rate_func=window(t0 / (1 - lag), (t1 - stagger) / (1 - lag), total, func))


def clock_driver(scene, fn):
    """An updater (not a play) that calls fn(t, driver) with the scene time on every frame; it runs first."""
    d = Mobject()
    d.add_updater(lambda m: fn(film_time() - float(scene.film_start), m))
    scene.add(d)
    scene.bring_to_back(d)
    return d


class ThreadSet:
    """The 70 threads of S04 (world.thread_curves, seed 13) with their arc lengths, for drawing and currents."""

    def __init__(self, test, level: float):
        self.curves = world.thread_curves(test)
        self.cum = [np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]) for c in self.curves]
        self.L = np.array([c[-1] for c in self.cum])
        self.lines = world.make_threads(level, test)
        self.full = [m.points.copy() for m in self.lines]
        # where each thread goes behind the model's core disc: before that the 70 lie together as one trunk, so a
        # light that travels on them is drawn ONCE there (on the mean path), not 70 times (which reads as a block)
        self.s_in = np.array([self._enter(c, cum) for c, cum in zip(self.curves, self.cum)])
        mean = np.mean(np.array(self.curves), axis=0)
        cum = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(mean, axis=0), axis=1))])
        self.trunk_end = self._enter(mean, cum) + 0.25         # hidden by the disc from its entry on
        self.trunk_len = float(cum[-1])
        self.trunk_path = mean

    @staticmethod
    def _enter(c, cum) -> float:
        inside = np.nonzero(np.linalg.norm(c - M_C, axis=1) < M_R - 0.03)[0]
        if not len(inside):
            return float(cum[-1])
        k = int(inside[0])
        return float(cum[max(k - 1, 0)])

    def trunk(self, opacity: float = 0.0, taper=(0.7, 0.12), width=W_LINE) -> Stroke:
        st = Stroke(self.trunk_path, width=width, color=INK, taper=taper, opacity=opacity)
        st.set_span(0.0, 1e-4)
        st.set_fill(opacity=0.0)
        return st

    def set_trunk(self, st: Stroke, a: float, b: float, opacity: float):
        """Show the trunk light between arc lengths a and b (clipped to where the trunk goes behind the disc)."""
        b = min(b, self.trunk_end)
        a = min(max(a, 0.0), b)
        if b - a < 1e-3 or opacity <= 1e-4:
            st.set_fill(opacity=0.0)
            return
        st.set_span(a / self.trunk_len, b / self.trunk_len)
        st.set_fill(opacity=float(opacity))

    def at(self, i: int, s) -> np.ndarray:
        c, cum = self.curves[i], self.cum[i]
        s = np.atleast_1d(s)
        return np.column_stack([np.interp(s, cum, c[:, j]) for j in range(3)])

    def body(self, i: int, d: float) -> np.ndarray:
        """The vertices of thread i from its start to arc length d."""
        c, cum = self.curves[i], self.cum[i]
        k = int(np.searchsorted(cum, d, side="left"))
        return np.vstack([c[:max(k, 1)], self.at(i, d)])

    def segment(self, i: int, a: float, b: float, n: int = 10) -> np.ndarray:
        return self.at(i, np.linspace(a, b, n))

    def restore(self, opacity: float):
        for m, p in zip(self.lines, self.full):
            m.set_points(p.copy())
            m.set_stroke(opacity=opacity)


def flash_group(n: int, width=W_LINE) -> VGroup:
    g = VGroup()
    for _ in range(n):
        m = VMobject(stroke_color=INK, stroke_width=width, stroke_opacity=0.0, fill_opacity=0)
        m.set_points_as_corners(np.zeros((2, 3)))
        g.add(m)
    return g


def _set_seg(m: VMobject, pts: np.ndarray, opacity: float):
    if opacity <= 1e-4 or len(pts) < 2:
        m.set_stroke(opacity=0.0)
        return
    m.set_points_as_corners(pts)
    m.set_stroke(opacity=float(opacity))


class SlidingTwin(world.Twin):
    """world.Twin with two more state numbers: ``slide`` (0: a full-size copy over the model; 1: home at half size
    at (0.5, -1.45)) and ``grow`` (0: the five lights are points on its right rim; 1: home at radius 1.5). At
    slide = grow = 1 it is world.Twin exactly (the home geometry is restored from copies, not recomputed)."""

    def __init__(self):
        super().__init__()
        self._home_c = [nd.c.copy() for nd in self.needles]
        self._home_L = [nd.L for nd in self.needles]
        self._home_rest = self.rest.copy()
        self._home_rim = self.rim.points.copy()
        self._home_ring = [m.points.copy() for m in self.rings]
        self._home_core = [m.points.copy() for m in self.cores]
        self._dirs = [C(math.cos(a * DEG), math.sin(a * DEG)) for a in TWIN_LIGHT_ANGLES]
        self.slide, self.grow = 1.0, 1.0
        self._ready = True
        self.paint()

    def paint(self):
        if not getattr(self, "_ready", False):
            return super().paint()
        s, g = float(self.slide), float(self.grow)
        if s >= 1.0 and g >= 1.0:
            for nd, c, L in zip(self.needles, self._home_c, self._home_L):
                nd.c, nd.L = c.copy(), L
            self.rest = self._home_rest.copy()
            self.rim.set_points(self._home_rim.copy())
            for m, p in zip(self.rings, self._home_ring):
                m.set_points(p.copy())
            for m, p in zip(self.cores, self._home_core):
                m.set_points(p.copy())
            return super().paint()
        ctr = M_C + (TWIN_C - M_C) * s
        k = 1.0 - 0.5 * s
        th = 8 * DEG * s
        rot = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
        for i, nd in enumerate(self.needles):
            nd.c, nd.L = ctr + k * (rot @ NEEDLE_POS[i]), NEEDLE_LEN * k
        self.rest = PATTERNS["M0"] + th
        self.rim.set_points(ctr + (self._home_rim - TWIN_C) * (2 * k))
        r_rim, gg = M_R * k, max(g, 1e-3)
        for j, d in enumerate(self._dirs):
            hp = TWIN_C + 1.5 * d
            p = ctr + (r_rim + (1.5 - r_rim) * g) * d
            self.rings[j].set_points(p + (self._home_ring[j] - hp) * gg)
            self.cores[j].set_points(p + (self._home_core[j] - hp) * gg)
        super().paint()
        self.rings.set_stroke(opacity=0.55 * self.level * g)
        for c in self.cores:
            c.set_fill(opacity=c.get_fill_opacity() * g)
        return self


# ------------------------------------------------------------------------------------------------ the scene

class S04(Narrated):
    def build(self):
        w = world.pose("P03", self)
        pool, model, test, cost = w.pool, w.model, w.test, w.cost
        held = w.labels["held back"]
        fr = 1.0 / self.fps

        def cue(t: float) -> float:
            return t - fr          # a row's play ends one frame before the next cue (as at() stops)

        # ---- the camera returns to W (move 3) and the cost floor with it: both clock-driven, across rows 1 and 2
        world.clock_move(self, "W", 0.0, 2.8)
        COST_T0, COST_T1 = 1.0, 2.7      # the floor's lowest edge leaves the band of the tag at about 1.0 s

        def cost_in(t, m):
            cost.level = _rate(MOVE, (t - COST_T0) / (COST_T1 - COST_T0))
            if t >= COST_T1:
                cost.level = 1.0
                m.clear_updaters()
        clock_driver(self, cost_in)

        # ---- row 1: the first second -- the supposed tuning undoes itself
        self.at(0, lead=0.4)
        rest_states = test.states_with(RED_INNER, "pale", outer="dark")
        t_end = cue(self.word_span(0, "associated")[0])
        L = self.left(t_end)
        self.play_until(t_end,
                        model.to_pattern("M0", **lag_window(0.0, 0.8, 0.3, L)),
                        test.tween("haze", np.zeros((24, 2)), rate_func=window(0.0, 0.6, L)),
                        test.to_states(rest_states, rate_func=window(0.1, 0.8, L)),
                        test.to_shade(1.0, rate_func=window(0.1, 0.8, L)),
                        leave(held, rate_func=window(0.0, 0.6, L)))
        model.set_pattern("M0")                            # exact: the shorter turn may differ from M0 by pi
        test.set_states(rest_states)

        # ---- row 2: "associated" -- light 10 flares; one thread leaves it and fans into 70; seven ends are marked
        self.at_word(0, "associated")
        threads = ThreadSet(test, world.THREAD_LEVEL)
        flashes = flash_group(len(threads.L), W_HAIR)
        trunk = threads.trunk()
        for m in threads.lines:
            m.set_stroke(opacity=0.0)
        model.behind.add(threads.lines, flashes, trunk)
        marks = pool.marks
        rg = marks.rgbas.copy()
        rg[:, 3] = 0.0
        marks.rgbas = rg
        pool.set_marks(1.0)                                # the seven cores at INK 90% once their alpha is up
        base_look = test.look.copy()
        r_core = np.array(test.cores.radii, dtype=float).copy()

        FAN_T0, FAN_D, FLASH = 0.2, 1.6, 0.5
        Lmax = float(threads.L.max())
        us = np.linspace(0, 1, 4001)
        ds = Lmax * np.array([MOVE(float(u)) for u in us])
        t_arr = FAN_T0 + FAN_D * np.interp(threads.L, ds, us)          # when each thread reaches its end
        n_mark = len(marks.rgbas)

        def flare(p: float, ks):
            look = base_look.copy()
            for k in ks:
                look[k, :3] = np.array(mix(FAIL, FAIL_HI, 0.7 * p).to_rgb())
            test.look = look
            radii = r_core.copy()
            radii[list(ks)] = CORE_R * (1 + 0.5 * p)
            test.cores.radii = radii
            test.paint()

        def fan(t):
            flare(_rate(PULSE, t / 0.3), [10])
            d_front = Lmax * _rate(MOVE, (t - FAN_T0) / FAN_D)
            for i, (line, fl) in enumerate(zip(threads.lines, flashes)):
                d = min(d_front, threads.L[i])
                if d <= 1e-3:
                    continue
                line.set_points_as_corners(threads.body(i, d))
                line.set_stroke(opacity=world.THREAD_LEVEL)
                fade = 1.0 - _c01((t - t_arr[i]) / 0.25)
                a0 = max(threads.s_in[i], d - FLASH)       # each thread's own flash only from behind the disc on
                _set_seg(fl, threads.segment(i, min(a0, d), d), 0.5 * fade)
            threads.set_trunk(trunk, d_front - 0.9, d_front, 0.9)
            a = np.array([0.9 * _rate(ENTER, (t - t_arr[j] + 0.05) / 0.3) for j in range(n_mark)])
            r = marks.rgbas.copy()
            r[:, 3] = a
            marks.rgbas = r

        def fan_done():
            threads.restore(world.THREAD_LEVEL)
            model.behind.remove(flashes, trunk)
            r = marks.rgbas.copy()
            r[:, 3] = 0.9
            marks.rgbas = r
            test.look = base_look.copy()
            test.cores.radii = r_core.copy()
            test.paint()

        lbl = world.label("associated with this answer")
        self.play_until(cue(self.word_span(0, "automatically")[0]),
                        Clock(pool, fan, fan_done),
                        enter(lbl, rate_func=late(0.6)))

        # ---- row 3: "automatically ... future answers." -- the four outlines brighten in turn; on "future" the
        # five red lights of the inner row pulse once together; nothing in the pool changes with them
        self.at_word(0, "automatically")
        t_end = cue(self.line_start(1))
        t_fut = self.word_span(0, "future")[0] - self.now
        ol0 = pool.ol.copy()
        js = [GROUP_NAMES.index(n) for n in ("gA", "gB", "gC", "gD")]

        def turn(t):
            ol = ol0.copy()
            for n, j in enumerate(js):
                ol[j] = ol0[j] + (1.0 - ol0[j]) * _rate(PULSE, (t - 0.05 - 0.45 * n) / 0.6)
            pool.ol = ol
            pool.paint()
            flare(_rate(PULSE, (t - t_fut) / 0.8), RED_INNER)

        def turn_done():
            pool.ol = ol0.copy()
            pool.paint()
            test.look = base_look.copy()
            test.cores.radii = r_core.copy()
            test.paint()

        self.play_until(t_end, Clock(pool, turn, turn_done))

        # ---- row 4: "One question looks back" -- a slow current runs along the threads from light 10 to the pool
        self.at(1)
        t_end = cue(self.word_span(1, "other")[0])
        cur_tail, cur_head = flash_group(len(threads.L), W_HAIR), flash_group(len(threads.L), W_HAIR)
        cur_trunk = threads.trunk(taper=(0.85, 0.1))
        model.behind.add(cur_tail, cur_head, cur_trunk)
        CUR_T0, CUR_D = 0.1, 2.2
        v = Lmax / CUR_D                                   # one steady speed: the farthest end is reached at 2.2 s

        def current(t):
            d = v * (t - CUR_T0)
            for i, (tl, hd) in enumerate(zip(cur_tail, cur_head)):
                Li = threads.L[i]
                if d <= 1e-3:
                    continue
                fade = 1.0 - _c01((d - Li) / (v * 0.3))
                s0 = threads.s_in[i]                       # each thread's own light only from behind the disc on
                b = min(d, Li)
                a = min(max(s0, d - 1.4), b)
                _set_seg(tl, threads.segment(i, a, b, 16), 0.22 * fade)
                a2 = min(max(s0, d - 0.35), b)
                _set_seg(hd, threads.segment(i, a2, b, 8), 0.5 * fade)
            threads.set_trunk(cur_trunk, d - 1.4, d, 0.7 * _c01(d / 0.3))

        def current_done():
            model.behind.remove(cur_tail, cur_head, cur_trunk)

        self.play_until(t_end, Clock(pool, current, current_done))

        # ---- row 5: "The other asks what would happen" -- the backward look dims; gB is the change
        self.at_word(1, "other")
        t_end = cue(self.word_span(1, "changed")[0])
        L = self.left(t_end)

        def dim(t):
            x = _rate(MOVE, t / 0.8)
            for m in threads.lines:
                m.set_stroke(opacity=world.THREAD_LEVEL + (0.10 - world.THREAD_LEVEL) * x)
            lbl.set_opacity(1.0 - 0.6 * x)

        def dim_done():
            threads.restore(0.10)
            lbl.set_opacity(0.4)

        self.play_until(t_end,
                        Clock(pool, dim, dim_done),
                        pool.to_marks(0.1, rate_func=window(0.0, 0.8, L)),
                        pool.to_outlines({"gA": 0.4, "gB": 1.0, "gC": 0.4, "gD": 0.4}, rate_func=window(0.1, 0.8, L)),
                        pool.gold("gB", rate_func=window(0.5, 1.5, L)),
                        pool.lift("gB", 0.5, lag=0.25, order="random", rate_func=window(0.5, 1.5, L)))
        pool.set_marks(0.1)
        pool.set_outlines({"gA": 0.4, "gB": 1.0, "gC": 0.4, "gD": 0.4})

        # ---- row 6: "if we changed something." -- a hollow gold twin slides out of the model; its lights grow
        self.at_word(1, "changed")
        twin = SlidingTwin()
        twin.slide, twin.grow, twin.level, twin.jitter = 0.0, 0.0, 0.0, 1.0
        twin.paint()
        self.add(twin)
        L = self.left(self.scene_duration)
        self.play_until(self.scene_duration,
                        twin.to_level(1.0, rate_func=window(0.0, 0.5, L)),
                        twin.tween("slide", 1.0, rate_func=window(0.0, 1.4, L)),
                        twin.tween("grow", 1.0, rate_func=window(0.75, 1.55, L, ENTER)))
        twin.slide, twin.grow, twin.level = 1.0, 1.0, 1.0
        twin.paint()
