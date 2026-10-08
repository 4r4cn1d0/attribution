"""S03 The test we have been staring at (storyboard section 5, S03).

Starts in pose P02 (world.pose("P02", self)) and ends in exactly the state that world.pose("P03", ...) builds.

Rows (kit cues, lines from 0). Each row is one play that ends one frame before the next row's cue, so that the
next row's first change lands ON its word (as at() does):

  at(0)                      the 24 lights go out of focus (1.1 s), then the soft band swells toward "room" (1.5 s)
  at_word(0, "congratulate") two pleased pulses: a light changes somewhere in the haze (its direction cannot be
                             seen) and the band brightens; `safer?` brightens once with the second pulse
  at(1)                      the haze thins; on "define" it snaps back into 24 sharp lights (0.5 s, the allowed snap)
                             and `safer?` dissolves into them; on "measure" a white tick visits the 9 red lights (0.8 s)
  at_word(1, "tests")        every second light slides out (0-0.8 s); their cores go dark (0.4-1.0 s); the shade
                             wipes in over them (0.6-1.2 s, a clip wipe); `held back` lands late(0.6)
  at_word(1, "choose")       one gold pulse: from the outlines, through the model, to the inner row (1.0 s); the
                             inner rings flash; nothing reaches the outer row
  at(2)                      camera W -> STARE (clock_move, 3.9 s from at(2), across the next row); the cost floor
                             fades to 0; round 1 (1.2 s): hollow stream, the needles shift a little, a sweep of
                             the inner row: red 0 6 10 14 20 -> 6 10 14
  at_word(2, "fixing")       round 2 (0.9 s): -> 10; round 3 (0.7 s): -> none; the inner row glows softly
  line_end(2)                from 0.3 s: the shade lifts (0.6 s); one sweep over the held-back lights (0.6 s):
                             3 9 15 21 red again, the others pale; hold

The motions that cross a row are clock-driven (world.clock_move). Everything else lives inside its row's play.
Every temporary thing (the glow behind `safer?`, the ticks, the gold pulse, the hollow streams, the sweep rays)
is gone or at zero before the scene ends; the lasting objects end on P03's state numbers exactly.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/ and world.py

import numpy as np  # noqa: E402

from kit import *  # noqa: E402,F401,F403
import world  # noqa: E402
from world import INNER, M_C, M_R, OUTER, PATTERNS, RED_FIRST, RED_OUTER, ROUNDS_INNER, SHADE, Model  # noqa: E402


# ------------------------------------------------------------------------------------------------ helpers

def _c01(x):
    return np.clip(x, 0.0, 1.0)


def _rate(func, u):
    """A kit rate function on a number or on an array of numbers in [0, 1]."""
    u = np.asarray(u, dtype=float)
    if u.ndim == 0:
        return float(func(float(u)))
    return np.array([func(float(x)) for x in u.ravel()]).reshape(u.shape)


def _flash(t, tp, rise=0.04, decay=0.14):
    """0 -> 1 -> 0 around the peak time(s) ``tp``: up in ``rise`` s, down in ``decay`` s."""
    x = t - np.asarray(tp, dtype=float)
    return np.where(x < 0, _c01((x + rise) / rise), _c01(1.0 - x / decay))


class Clock(Animation):
    """Calls fn(t) on every frame, t = seconds since the play began. The play's run time (set by play_until) is the
    clock's length; the object's own updaters keep running."""

    def __init__(self, mob, fn, **kw):
        kw.setdefault("rate_func", linear)
        super().__init__(mob, suspend_mobject_updating=False, **kw)
        self.fn = fn

    def create_starting_mobject(self):
        return Mobject()

    def interpolate_mobject(self, alpha: float) -> None:
        self.fn(float(alpha) * self.run_time)


class Phases(Animation):
    """Timed changes of ONE state attribute of a lasting object inside one play, one after another (world.Tween
    takes its start value when the play begins, so two Tweens of one attribute in one play would fight).

    phases: [(t0, dur, goal, func)], t0 in seconds from the play start, a number or one per element of the
    attribute (a per-element window: the order in which a sweep reaches the lights). The value is
    start + sum_i (goal_i - goal_(i-1)) * func(u_i); when every window is over it is exactly the last goal.
    """

    def __init__(self, obj, attr: str, phases, **kw):
        kw.setdefault("rate_func", linear)
        super().__init__(obj, suspend_mobject_updating=False, **kw)
        self.attr, self.phases = attr, phases

    def create_starting_mobject(self):
        return Mobject()

    def begin(self) -> None:
        start = np.array(getattr(self.mobject, self.attr), dtype=float).copy()
        self.start, self.chain, prev = start, [], start
        for t0, dur, goal, func in self.phases:
            g = np.broadcast_to(np.array(goal, dtype=float), start.shape).copy()
            self.chain.append((np.asarray(t0, dtype=float), float(dur), prev, g, func))
            prev = g
        super().begin()

    def interpolate_mobject(self, alpha: float) -> None:
        t = float(alpha) * self.run_time
        val, done = self.start.copy(), True
        for t0, dur, a, b, func in self.chain:
            u = _c01((t - t0) / dur)
            done = done and bool(np.all(u >= 1.0))
            f = _rate(func, u)
            if np.ndim(f) == 1 and a.ndim > 1:
                f = f.reshape((-1,) + (1,) * (a.ndim - 1))
            val = val + (b - a) * f
        if done:
            val = self.chain[-1][3].copy()
        setattr(self.mobject, self.attr, val)
        self.mobject.paint()


def _spline(pts, n: int = 40):
    """A Catmull-Rom curve through ``pts``: (samples, arc-length share of each sample)."""
    pts = [np.asarray(p, dtype=float) for p in pts]
    P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (p2 - p0) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s ** 2
                              + (3 * p1 - p0 - 3 * p2 + p3) * s ** 3))
    out.append(pts[-1])
    arr = np.array(out)
    cum = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(arr, axis=0), axis=1))])
    return arr, cum / cum[-1]


def _along(path, s: float) -> np.ndarray:
    arr, share = path
    s = float(np.clip(s, 0.0, 1.0))
    return np.array([np.interp(s, share, arr[:, 0]), np.interp(s, share, arr[:, 1]), 0.0])


def _radial(k: int, test, r0: float, r1: float) -> tuple[np.ndarray, np.ndarray]:
    """Two points on the ray from the model's centre through light k, at radii r0 and r1."""
    v = test.pos(k) - M_C
    v = v / np.linalg.norm(v)
    return M_C + r0 * v, M_C + r1 * v


# A sweep asks every light of a row: a faint white ray from the model's rim to the light, then the light answers.
RAY_PEAK, RAY_RISE, RAY_DECAY = 0.45, 0.04, 0.14


def _sweep_times(ts: float, sd: float, n: int) -> np.ndarray:
    """Peak times of the n rays of a sweep that starts at ts and is over (decay included) at ts + sd."""
    return ts + RAY_RISE + np.arange(n) / max(n - 1, 1) * (sd - RAY_RISE - RAY_DECAY)


# ------------------------------------------------------------------------------------------------ the scene

class S03(Narrated):
    def build(self):
        w = world.pose("P02", self)
        test, model, pool, cost = w.test, w.model, w.pool, w.cost
        safer = w.extra["safer"]
        fr = 1.0 / self.fps

        def cue(t: float) -> float:
            return t - fr          # a row's play ends one frame before the next cue (as at() stops)

        # ---- row 1, line 1: "Make the model safer" -- the lights go out of focus, then the band swells to "room"
        self.at(0)
        soft = test._looks({k: "soft" for k in range(24)})
        soft[:, 3] = 0.06                                # out of focus: no crisp core is left, only the glow

        def haze_in(t):
            a, b = MOVE(_c01(t / 1.1)), MOVE(_c01((t - 1.1) / 1.5))
            # 24 overlapping glows in screen blend add up: a share of 0.2 to 0.26 each gives a soft, pale band
            test.haze[:, 0] = 0.25 * a + 0.09 * b
            test.haze[:, 1] = b                          # and it widens from radius 0.45 to 0.8
            test.paint()

        self.play_until(cue(self.word_span(0, "congratulate")[0]),
                        Phases(test, "look", [(0.0, 1.1, soft, MOVE)]), Clock(test, haze_in))

        # ---- row 2: "congratulate ourselves" -- two pleased pulses; a light changes, we cannot see which way
        self.at_word(0, "congratulate")
        p1, p2, pw = 0.12, 0.98, 0.6
        band0, look0 = test.haze.copy(), test.look.copy()
        changes = ((13, p1), (8, p2))                    # somewhere in the haze, just before each pulse
        halo = glow_sprite(0.95, INK_HI, peak=0.85).stretch(0.45, 1).move_to(safer.text.get_center())
        halo.set_opacity(0.0)
        set_blend(halo, "screen")                        # a bloom over the word: it brightens; it does not move
        self.add(halo)

        def pleased(t):
            band = PULSE(_c01((t - p1) / pw)) + PULSE(_c01((t - p2) / pw))
            haze, look = band0.copy(), look0.copy()
            haze[:, 0] += 0.12 * band
            for k, tc in changes:
                q = PULSE(_c01((t - tc + 0.12) / 0.4))
                look[k, 3] += 0.14 * q
                haze[k, 0] += 0.25 * q
            test.haze, test.look = haze, look
            test.paint()
            halo.set_opacity(PULSE(_c01((t - p2) / pw)))   # `safer?` brightens once, with the second pulse

        self.play_until(cue(self.line_start(1)), Clock(test, pleased))
        self.remove(halo)

        # ---- row 3, line 2: the haze thins; on "define" 24 sharp lights; on "measure" a tick visits each red light
        self.at(1)
        T0 = self.now
        d = self.word_span(1, "define")[0] - T0
        tm = self.word_span(1, "measure")[0] - T0
        sharp = test._looks(test.states_with(RED_FIRST, "pale"))          # the lights of P02 again
        thin = np.tile([0.12, 0.35], (24, 1))
        word = safer.text.copy()                         # `safer?` stops breathing and dissolves into the lights
        self.remove(safer)
        self.add(word)
        into = np.mean([test.pos(k) for k in (11, 12, 13)], axis=0)
        fades = [FadeOut(g, shift=0.3 * (into - g.get_center()), scale=0.6, rate_func=MOVE)
                 for g in word.family_members_with_points()]
        t_def = T0 + d
        tick = DotCloud(np.array([test.pos(k) for k in RED_FIRST]), radius=0.045, color=INK_HI, opacity=0.0, glow=0.0)
        self.add(tick)
        tps = tm + 0.03 + 0.075 * np.arange(len(RED_FIRST))

        def ticks(t):
            e = _flash(t, tps)
            tick.rgbas[:, 3] = e
            tick.glows = 0.9 * e

        self.play_until(cue(self.word_span(1, "tests")[0]),
                        Phases(test, "haze", [(0.0, d, thin, MOVE), (d, 0.5, np.zeros((24, 2)), ENTER)]),
                        Phases(test, "look", [(d, 0.5, sharp, ENTER)]),
                        timed(LaggedStart(*fades, lag_ratio=0.06), t_def - 0.1, t_def + 0.6),
                        Clock(tick, ticks))
        self.remove(tick, word)

        # ---- row 4: "tests held back" -- every second light slides out, goes dark, and the shade wipes in
        self.at_word(1, "tests")
        dark = test._looks(test.states_with(RED_FIRST, "pale", outer="dark"))
        item = 0.8 / (1 + 11 * 0.04)                     # lag_ratio 0.04 over 12 lights in 0.8 s
        t_split = np.array([k // 2 for k in range(24)]) * 0.04 * item
        held = world.label("held back")
        world.follow(self, held, world.anchor_of("held back"))
        wedge = VMobject(stroke_width=0, fill_opacity=0)
        a0, a1 = SHADE["a0"] - 1.5, SHADE["a1"] + 1.5

        def wipe(t):
            s = MOVE(_c01((t - 0.6) / 0.6))
            ang = np.radians(np.linspace(a0, a0 + (a1 - a0) * s, 48))
            arc = np.column_stack([M_C[0] + 4.6 * np.cos(ang), M_C[1] + 4.6 * np.sin(ang), 0 * ang])
            wedge.set_points_as_corners([M_C, *arc, M_C])
            test.shade_on = 1.0 if t >= 0.6 else 0.0
            test.paint()

        wipe(0.0)
        set_clip(test.sector, wedge)
        set_clip(test.edge, wedge)
        self.play_until(cue(self.word_span(1, "choose")[0]),
                        Phases(test, "split", [(t_split, item, 1.0, MOVE)]),
                        Phases(test, "look", [(0.4, 0.6, dark, MOVE)]),
                        Clock(test, wipe),
                        enter(held, rate_func=late(0.6)))
        set_clip(test.sector, None)
        set_clip(test.edge, None)

        # ---- row 5: "while we choose the change" -- one gold pulse from the outlines, through the model, to the inner row
        self.at_word(1, "choose")
        T0 = self.now
        L = cue(self.line_start(2)) - T0
        ol = pool.ol.copy()
        for j, n in enumerate(world.GROUP_NAMES):
            ol[j] = 1.0 if n in ("gA", "gB", "gC", "gD") else 0.45
        paths, ends = self._pulse_paths(test)
        n = len(paths)
        go = 0.06 + 0.004 * np.arange(n)            # one pulse: together into the core, then fanned out
        fl = 0.8
        tail = ((0.0, 1.0, 0.05), (0.035, 0.5, 0.04), (0.07, 0.22, 0.03))     # head and two tail samples
        gold = DotCloud(np.tile(M_C, (3 * n, 1)), radius=0.04, color=FOCUS, opacity=0.0, glow=0.0)
        gold.radii = np.tile([r for _, _, r in tail], n)
        self.add(gold)

        def pulse(t):
            u = _c01((t - go) / fl)
            s = _rate(MOVE, u)
            e = _c01(u / 0.12) * _c01((1.0 - u) / 0.1)
            pts, al = [], []
            for j in range(n):
                for back, a, _ in tail:
                    pts.append(_along(paths[j], s[j] - back))
                    al.append(a * e[j] * float(s[j] - back > 0))
            gold.points = np.array(pts)
            gold.rgbas[:, 3] = al
            gold.glows = 0.7 * np.array(al)

        arrive = go + fl

        def rings(t):
            f = _rate(PULSE, _c01((t - (arrive - 0.1)) / 0.3))
            for j, k in enumerate(ends):
                test.look[k, 5] = 0.6 + 0.4 * f[j]
            test.paint()
            for j, k in enumerate(ends):
                test.rings[k].set_stroke(color=GREY_2 if f[j] <= 0 else mix(GREY_2, INK_HI, float(f[j])))

        self.play_until(T0 + L,
                        pool.tween("ol", ol, rate_func=window(0.0, 0.5, L, func=PULSE)),
                        Clock(gold, pulse), Clock(test, rings))
        self.remove(gold)

        # ---- row 6, line 3: "Otherwise" -- the camera starts to stare; the cost floor fades; round 1
        self.at(2)
        t2 = self.line_start(2)
        world.clock_move(self, "STARE", t2, t2 + 3.9)
        T0 = self.now
        L = cue(self.word_span(2, "fixing")[0]) - T0
        anims, temp = self._rounds(test, model, [(0.25, 1.2, 1)])
        self.play_until(T0 + L, *anims, cost.to_level(0.0, rate_func=window(0.0, 1.2, L)))
        self.remove(*temp)

        # ---- row 7: "fixing the test we have been staring at" -- rounds 2 and 3; the inner row glows softly
        self.at_word(2, "fixing")
        T0 = self.now
        L = cue(self.line_end(2)) - T0
        anims, temp = self._rounds(test, model, [(0.0, 0.9, 2), (0.95, 0.7, 3)])
        glow = np.zeros((24, 2))
        glow[INNER, 0] = 0.1 / 0.6                       # P03: a soft halo at 10% on the inner row
        self.play_until(T0 + L, *anims, test.tween("haze", glow, rate_func=window(1.45, L, L)))
        self.remove(*temp)

        # ---- row 8: the silence -- the shade lifts; one sweep over the held-back lights: the same four fail
        self.at_time(self.line_end(2))
        final = {k: "pale" for k in INNER}
        final.update({k: ("red" if k in RED_OUTER else "pale") for k in OUTER})
        final = test._looks(final)
        tp = _sweep_times(0.9, 0.6, len(OUTER))
        t0 = np.full(24, 0.9)
        t0[OUTER] = tp
        rays = self._rays(test, OUTER, 3.95)
        self.add(rays)

        def sweep(t):
            e = _flash(t, tp, RAY_RISE, RAY_DECAY)
            for j, ray in enumerate(rays):
                ray.set_stroke(opacity=RAY_PEAK * float(e[j]))

        self.play_until(self.scene_duration,
                        test.to_shade(0.0, rate_func=window(0.3, 0.9, self.scene_duration - self.now)),
                        Phases(test, "look", [(t0, 0.08, final, MOVE)]),
                        Clock(rays, sweep))

    # -------------------------------------------------------------------------------------------- parts

    @staticmethod
    def _rays(test, ks, r_light: float) -> VGroup:
        out = VGroup()
        for k in ks:
            a, b = _radial(k, test, M_R + 0.08, r_light - 0.16)
            out.add(Line(a, b, stroke_color=INK, stroke_width=W_LINE, stroke_opacity=0.0))
        return out

    @staticmethod
    def _pulse_paths(test):
        """Twelve gold travellers: three from each of the outlines gA..gD (from the side that faces the model),
        through the model's core, each to one light of the inner row (sorted by height, so paths barely cross)."""
        srcs = []
        for g in ("gA", "gB", "gC", "gD"):
            poly = world.GROUP_POLYS[g]
            c = poly.mean(axis=0)
            d = (M_C[:2] - c) / np.linalg.norm(M_C[:2] - c)
            for phi in np.radians((-40, 0, 40)):
                r = np.array([d[0] * np.cos(phi) - d[1] * np.sin(phi), d[0] * np.sin(phi) + d[1] * np.cos(phi)])
                srcs.append(poly[int(np.argmax(poly @ r))])
        srcs.sort(key=lambda p: p[1])
        paths, ends = [], list(INNER)
        for j, (p, k) in enumerate(zip(srcs, ends)):
            p0 = np.array([p[0], p[1], 0.0])
            q = test.pos(k)
            v = (q - M_C) / np.linalg.norm(q - M_C)
            mid = M_C + np.array([0.0, 0.5 * (j / 11 - 0.5), 0.0])
            paths.append(_spline([p0, Model.rim_point(p0), mid, M_C + M_R * v, q - 0.15 * v]))
        return paths, ends

    def _rounds(self, test, model, rounds):
        """The supposed tuning rounds of line 3, inside one play. Each round (start, length, number): a stream of
        hollow starlight points from the pool's right fringe flows in at the model's left rim; the needles shift a
        little toward M*; a sweep asks the inner row and the lights answer (ROUNDS_INNER)."""
        m0, m1 = PATTERNS["M0"], PATTERNS["M*"]
        rng = np.random.default_rng(61)
        fringe = np.nonzero((world.POOL_PTS[:, 0] > -3.3) & (world.POOL_PTS[:, 1] > -0.5) & (world.POOL_PTS[:, 1] < 2.5))[0]
        counts = {1: 10, 2: 7, 3: 5}
        picks = rng.choice(fringe, sum(counts.values()), replace=False)
        used = {1: picks[:10], 2: picks[10:17], 3: picks[17:]}
        dots, flights = VGroup(), []
        rays = self._rays(test, INNER, 3.0)
        ray_peaks = []
        look_phases, angle_phases = [], []
        for rs, D, r in rounds:
            for i, idx in enumerate(used[r]):
                p = world.POOL_PTS[idx].copy()
                q = Model.rim_point(p)
                mid = (p + q) / 2
                v = (q - p) / np.linalg.norm(q - p)
                bend = np.array([-v[1], v[0], 0.0]) * (1 if v[0] > 0 else -1) * 0.22
                ts = rs + 0.3 * D * i / max(len(used[r]) - 1, 1)
                flights.append((p, mid + bend, q, ts, 0.4 * D))
                dots.add(Circle(radius=0.05, stroke_color=DATA, stroke_width=W_LINE, stroke_opacity=0.0,
                                fill_color=DATA, fill_opacity=0.0).move_to(p))
            angle_phases.append((rs + 0.3 * D, 0.45 * D, m0 + (r / 3) * (m1 - m0), MOVE))
            tp = _sweep_times(rs + 0.55 * D, 0.45 * D, len(INNER))
            ray_peaks.append(tp)
            t0 = np.full(24, rs + 0.55 * D)
            t0[INNER] = tp
            look_phases.append((t0, 0.08, test._looks(test.states_with(ROUNDS_INNER[r], "pale", outer="dark")), MOVE))
        self.add(dots, rays)

        def stream(t):
            for c, (p, b, q, ts, fl) in zip(dots, flights):
                u = float(_c01((t - ts) / fl))
                s = MOVE(u)
                c.move_to((1 - s) ** 2 * p + 2 * (1 - s) * s * b + s ** 2 * q)
                c.set_stroke(opacity=0.6 * float(_c01(u / 0.15) * _c01((1 - u) / 0.2)))

        def sweep(t):
            e = np.max([_flash(t, tp, RAY_RISE, RAY_DECAY) for tp in ray_peaks], axis=0)
            for j, ray in enumerate(rays):
                ray.set_stroke(opacity=RAY_PEAK * float(e[j]))

        anims = [Clock(dots, stream), Clock(rays, sweep), Phases(model, "angles", angle_phases),
                 Phases(test, "look", look_phases)]
        return anims, [dots, rays]
