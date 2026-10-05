"""S02 Somewhere in that sentence (storyboard section 5, S02). It starts in pose P01 and ends in pose P02.

The direct way and its cost: three supposed retrains (gA, gB, gC), each with its sweep of the test and its mini
dial; the band runs to its end tick; the picture takes all of it back; a choice ring that does not settle; the
post's title, which lets go of every word but `safer?`.

How it is built. Many state changes overlap inside one row (two retrains, their sweeps and dials in line 2), and a
Tween captures its start when the play begins, so two Tweens on one attribute in one play would fight. So the
state of the world in this scene is ONE function of scene time (``_timeline``), built from keyframe tracks; every
row is one play (rule 3 of 1.2) whose ``Clock`` animation applies that function on every frame. The ring and the
outline lights cross cues, and the timeline carries them across. Text, the world's level, the band's head and the
light on the band are ordinary kit animations inside the row's play (``timed``).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/

from kit import *  # noqa: E402,F401,F403

import numpy as np  # noqa: E402

import world  # noqa: E402
from world import C  # noqa: E402

LIFT = C(-0.4, 0.6)                 # a group lifted out of the pool: 0.6 up and 0.4 left (as S01's removal)
LIFT_ALPHA = 0.55                   # its points stay visible, gold, at 55% of their changed opacity
FLOOR_MID = world.FLOOR_Y + world.SEG_H / 2


def _sm(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3 - 2 * u)


def _lin(u):
    return np.clip(u, 0.0, 1.0)


def _bump(u):
    """0 -> 1 -> 0 over u in [0, 1] (a pulse), 0 outside."""
    u = np.asarray(u, dtype=float)
    return np.where((u > 0) & (u < 1), np.sin(np.pi * np.clip(u, 0, 1)) ** 2, 0.0)


class Track:
    """A value (one row per element) that changes in timed steps, in scene seconds; every element has its own
    windows. ``at(t)`` gives the value at scene time t. Steps of one element must not overlap."""

    def __init__(self, v0):
        v0 = np.array(v0, dtype=float)
        self.scalar = v0.ndim == 0
        self.v0 = v0.reshape(1, 1) if self.scalar else v0.reshape(len(v0), -1)
        self.ev = [[] for _ in range(len(self.v0))]
        self.last = -1.0

    def go(self, t0, t1, target, idx=None, ease=_sm):
        n, m = self.v0.shape
        idx = np.arange(n) if idx is None else np.atleast_1d(np.asarray(idx, dtype=int))
        t0 = np.broadcast_to(np.asarray(t0, dtype=float), (len(idx),))
        t1 = np.broadcast_to(np.asarray(t1, dtype=float), (len(idx),))
        tg = np.array(target, dtype=float)
        tg = np.tile(tg.reshape(1, m), (len(idx), 1)) if tg.size == m else tg.reshape(len(idx), m)
        for j, i in enumerate(idx):
            self.ev[i].append((float(t0[j]), float(t1[j]), tg[j].copy(), ease))
            self.ev[i].sort(key=lambda e: e[0])
        self.last = max(self.last, float(np.max(t1)))
        return self

    def target(self, i):
        return self.ev[i][-1][2] if self.ev[i] else self.v0[i]

    def at(self, t: float):
        out = self.v0.copy()
        for i, evs in enumerate(self.ev):
            v = out[i]
            for a, b, g, e in evs:
                if t >= b:
                    v = g
                elif t > a:
                    v = v + (g - v) * float(e((t - a) / (b - a)))
                    break
                else:
                    break
            out[i] = v
        return float(out[0, 0]) if self.scalar else out


class Flight:
    """Particles on quadratic curves p0 -> p1 -> p2, each in its own window (scene seconds), as one DotCloud.
    They fade in over ``fade[0]`` and out over ``fade[1]`` of their window (absorbed where they land)."""

    def __init__(self, p0, p1, p2, t0, t1, rgbas, radius=0.03, radius_end=None, glow=0.0, ease=_sm, fade=(0.15, 0.15)):
        self.p0, self.p1, self.p2 = (np.asarray(p, dtype=float) for p in (p0, p1, p2))
        n = len(self.p0)
        self.t0 = np.broadcast_to(np.asarray(t0, dtype=float), (n,)).copy()
        self.t1 = np.broadcast_to(np.asarray(t1, dtype=float), (n,)).copy()
        self.rgba = np.asarray(rgbas, dtype=float).reshape(n, 4)
        self.r0, self.r1 = float(radius), float(radius if radius_end is None else radius_end)
        self.ease, self.fade = ease, fade
        rg = self.rgba.copy()
        rg[:, 3] = 0.0
        self.cloud = DotCloud(self.p0.copy(), radius=self.r0, rgbas=rg, glow=glow)
        self.start, self.end = float(self.t0.min()), float(self.t1.max())

    def apply(self, t: float) -> None:
        u = np.clip((t - self.t0) / np.maximum(self.t1 - self.t0, 1e-9), 0, 1)
        s = self.ease(u)[:, None]
        self.cloud.points = (1 - s) ** 2 * self.p0 + 2 * (1 - s) * s * self.p1 + s ** 2 * self.p2
        fi, fo = self.fade
        a = np.ones_like(u)
        if fi > 0:
            a = a * np.clip(u / fi, 0, 1)
        if fo > 0:
            a = a * np.clip((1 - u) / fo, 0, 1)
        a = a * ((u > 0) & (u < 1))
        self.cloud.rgbas[:, 3] = self.rgba[:, 3] * a
        self.cloud.radii[:] = self.r0 + (self.r1 - self.r0) * s[:, 0]


class Clock(Animation):
    """Calls fn(t) with the scene time of every frame of its play (the film clock), so a row's play applies the
    scene's timeline however its cues fall."""

    def __init__(self, scene, fn):
        self.scene_, self.fn = scene, fn
        super().__init__(Mobject(), run_time=1.0, rate_func=linear, suspend_mobject_updating=False)

    def interpolate_mobject(self, alpha: float) -> None:
        self.fn(film_time() - self.scene_.film_start)


class S02(Narrated):
    def build(self):
        w = world.pose("P01", self)
        self.w = w
        pool, model, test = w.pool, w.model, w.test
        dt = 1.0 / self.fps

        # ---------------------------------------------------------------- cues (scene seconds)
        T0 = self.line_start(0)                              # "We could retrain"
        T_CMP = self.word_span(0, "compare")[0]
        T_L1 = self.line_start(1)                            # "That gives us"
        T_MEAS = self.word_span(1, "measure")[0]
        T_MANY = self.word_span(1, "many")[0]
        T_EXP = self.word_span(1, "expensive")[0]
        E1 = self.line_end(1)
        T_L2 = self.line_start(2)                            # "I'm trying"
        T_DEC = self.word_span(2, "decision")[0]
        T_BEF = self.word_span(2, "before")[0]
        T_EVERY = self.word_span(2, "every")[0]
        E2 = self.line_end(2)
        T_L3 = self.line_start(3)                            # "There is a fairly simple question"
        T_SOME = self.word_span(3, "somewhere")[0]
        T_L4 = self.line_start(4)                            # "Getting it into a form"
        T_LONG = self.word_span(4, "longer")[0]
        END = self.scene_duration

        # ---------------------------------------------------------------- the cost floor (absent in P01)
        cost = world.CostFloor(segments="none", line=0.0, tick=False, lane=0.0)
        self.add(cost)
        self.mobjects.remove(cost)                           # P02's drawing order: pool, lone point, floor, model, test
        self.mobjects.insert(self.mobjects.index(model), cost)
        self.cost = cost

        # ---------------------------------------------------------------- tracks
        rng = np.random.default_rng(202)
        grp = {g: world.Pool.idx(g) for g in ("gA", "gB", "gC")}
        self.grp_idx = np.concatenate([grp["gA"], grp["gB"], grp["gC"]])
        where = {}
        o = 0
        for g in ("gA", "gB", "gC"):
            where[g] = np.arange(o, o + len(grp[g]))
            o += len(grp[g])
        lift = Track(np.zeros(len(self.grp_idx)))

        def lift_go(g, t0, t1, x):                           # each point its own window (30% stagger, seeded)
            n = len(where[g])
            d = np.random.default_rng(300 + len(lift.ev[where[g][0]]) + ord(g[1])).random(n) * 0.3 * (t1 - t0)
            lift.go(t0 + d, t0 + d + 0.7 * (t1 - t0), x, idx=where[g])

        ang = Track(world.PATTERNS["M0"])
        cur = [world.PATTERNS["M0"].copy()]
        ring_rank = -world.NEEDLE_RING + 0.01 * np.arange(40)
        ring_rank = np.argsort(np.argsort(ring_rank, kind="stable"), kind="stable") / 39.0

        def needles_go(name, t0, t1, lag=0.5):                # ring by ring, outer ring first, each by its shorter turn
            d = (world.PATTERNS[name] - cur[0] + np.pi / 2) % np.pi - np.pi / 2
            cur[0] = cur[0] + d
            s = t0 + ring_rank * lag * (t1 - t0)
            ang.go(s, s + (1 - lag) * (t1 - t0), cur[0], ease=_sm)

        look0 = test.look.copy()
        look = Track(look0)
        LOOK = {k: np.array(v, dtype=float) for k, v in world._LOOK.items()}

        def states(red):
            return np.array([LOOK["red"] if k in red else LOOK["pale"] for k in range(24)])

        def hollow(t0, t1):
            look.go(t0, t1, LOOK["hollow"])

        L = np.array([test.pos(k) for k in range(24)])
        R = np.array([world.Model.rim_point(p) for p in L])
        self.sweeps, self.flicks = [], []

        def sweep(t0, D, red):
            wdt = 0.5 * D
            ks = t0 + np.arange(24) / 23.0 * (D - wdt)
            for k in range(24):
                look.go(ks[k] + 0.7 * wdt, ks[k] + wdt, states(red)[k], idx=[k])
            self.sweeps.append((ks, wdt))
            self.flicks.append((t0 + 0.15 * D, min(0.4, 0.8 * D)))

        drawn = Track(0.0)
        shown = Track(np.zeros(14))
        solid = Track(np.zeros(14))
        tick = Track(0.0)

        def seg_go(i, t0, t1):
            shown.go(t0, t1, 1.0, idx=[i], ease=_lin)
            solid.go(t0, t1, 1.0, idx=[i], ease=_lin)

        flights = []

        def stream(src_excl, t0, t1, n, seed):
            r = np.random.default_rng(seed)
            keep = np.setdiff1d(np.arange(world.POOL_N), grp[src_excl])
            pick = r.choice(keep, n, replace=False)
            p0 = world.POOL_PTS[pick].copy()
            a = np.deg2rad(r.uniform(150, 210, n))
            p2 = world.M_C + world.M_R * np.column_stack([np.cos(a), np.sin(a), 0 * a])
            dd = p2 - p0
            p1 = (p0 + p2) / 2 + np.column_stack([-dd[:, 1], dd[:, 0], 0 * dd[:, 0]]) * 0.16   # a shallow curve
            span = t1 - t0
            s = t0 + r.random(n) * 0.4 * span
            rg = np.tile([*DATA.to_rgb(), 0.95], (n, 1))
            f = Flight(p0, p1, p2, s, s + 0.6 * span, rg, radius=0.036, glow=0.25, ease=_sm, fade=(0.2, 0.25))
            flights.append(f)

        def sparks(i, t0, t1, n, seed):                       # grey sparks fall from the lower rim onto segment i
            r = np.random.default_rng(seed)
            a = np.deg2rad(r.uniform(245, 295, n))
            p0 = world.M_C + world.M_R * np.column_stack([np.cos(a), np.sin(a), 0 * a])
            x0, x1 = world.seg_box(i)
            p2 = np.column_stack([r.uniform(x0 + 0.06, x1 - 0.06, n), np.full(n, FLOOR_MID), np.zeros(n)])
            p1 = np.column_stack([p2[:, 0] + 0.4 * (p0[:, 0] - p2[:, 0]), p0[:, 1] - 0.1, np.zeros(n)])
            span = t1 - t0
            s = t0 + r.random(n) * 0.35 * span
            rg = np.tile([*GREY_1.to_rgb(), 0.9], (n, 1))
            flights.append(Flight(p0, p1, p2, s, s + 0.65 * span, rg, radius=0.026,
                                  ease=lambda u: 0.35 * np.clip(u, 0, 1) + 0.65 * np.clip(u, 0, 1) ** 2, fade=(0.1, 0.12)))

        dials = []

        def dial_from_lights(i, red, t0, t1):
            """A copy of the lights (this retrain's answers) shrinks onto segment i's end and becomes its mini dial:
            the red lights land on the dial's red arc, the pale ones on the rest of its ring."""
            d = cost.dial(i, len(red) / 24.0)
            d.set_stroke(opacity=0.0)
            c = d.ring.get_center()
            order = [k for k in range(24) if k in red] + [k for k in range(24) if k not in red]
            slot = np.empty(24)
            for j, k in enumerate(order):
                slot[k] = j
            th_ = np.pi / 2 - 2 * np.pi * (slot + 0.5) / 24
            p2 = c + 0.16 * np.column_stack([np.cos(th_), np.sin(th_), 0 * th_])
            cen = L.mean(axis=0)
            ctrl = np.array([0.9 * c[0] + 0.1 * cen[0] + 1.6, world.FLOOR_Y + 0.55, 0.0])
            p1 = ctrl + (L - cen) * 0.35
            rg = np.array([[*FAIL.to_rgb(), 1.0] if k in red else [*INK.to_rgb(), 0.6] for k in range(24)])
            span = t1 - t0
            s = t0 + np.arange(24) / 23.0 * 0.12 * span
            f = Flight(L.copy(), p1, p2, s, s + 0.88 * span, rg, radius=world.CORE_R, radius_end=0.022,
                       ease=_sm, fade=(0.0, 0.3))
            flights.append(f)
            dials.append(dict(d=d, c=c, on=Track(0.0).go(t1 - 0.3 * span, t1, 1.0), pulses=[], scale=1.0))

        # ---------------------------------------------------------------- the schedule (storyboard S02, beat by beat)
        # Row 1, at(0): one retrain, slowly (2.2 s): gA lifts out, a stream of starlight copies from the rest of the
        # pool into the model's left rim, the needles turn to MA ring by ring, sparks fall onto segment 1 while the
        # floor line draws from x = -3.0, segment 1 lights. `data change` fades.
        lift_go("gA", T0, T0 + 0.4, 1.0)
        stream("gA", T0 + 0.1, T0 + 1.5, 90, 11)
        hollow(T0 + 0.5, T0 + 0.8)                              # the old answers do not hold for a new model
        needles_go("MA", T0 + 0.85, T0 + 2.0)
        sparks(0, T0 + 1.4, T0 + 2.0, 12, 21)
        drawn.go(T0 + 1.4, T0 + 2.2, 1.0, ease=_lin)
        seg_go(0, T0 + 1.85, T0 + 2.15)
        # Row 2, "compare": the test is swept once (0.6 s): seven red; a copy of the lights lands as dial 1 (0.8 s).
        sweep(T_CMP, 0.6, world.RETRAIN_RED["MA"])
        dial_from_lights(0, world.RETRAIN_RED["MA"], T_CMP + 0.5, T_CMP + 1.3)
        # Row 3, line 2: two more retrains, faster, no reset between them. gB (1.0 s): 9 red, no change. gC (0.8 s):
        # 8 red. Segments 2 and 3. From "measure" the three dials pulse in turn.
        a = T_L1
        lift_go("gA", a, a + 0.4, 0.0)
        lift_go("gB", a, a + 0.4, 1.0)
        stream("gB", a + 0.05, a + 0.8, 50, 12)
        hollow(a + 0.2, a + 0.4)
        needles_go("MB", a + 0.35, a + 0.95, lag=0.4)
        sparks(1, a + 0.55, a + 0.95, 9, 22)
        seg_go(1, a + 0.8, a + 1.0)
        sweep(a + 1.0, 0.4, world.RETRAIN_RED["MB"])
        dial_from_lights(1, world.RETRAIN_RED["MB"], a + 1.3, a + 1.9)
        lift_go("gB", a + 1.25, a + 1.6, 0.0)
        lift_go("gC", a + 1.25, a + 1.6, 1.0)
        stream("gC", a + 1.3, a + 1.95, 50, 13)
        hollow(a + 1.65, a + 1.8)
        needles_go("MC", a + 1.6, a + 2.05, lag=0.4)
        sparks(2, a + 1.7, a + 2.05, 9, 23)
        seg_go(2, a + 1.95, a + 2.1)
        sweep(a + 2.1, 0.4, world.RETRAIN_RED["MC"])
        dial_from_lights(2, world.RETRAIN_RED["MC"], a + 2.4, a + 3.0)
        gap = max((T_MANY - 0.55 - T_MEAS) / 2.0, 0.6)
        for j, tp in enumerate((T_MEAS, T_MEAS + gap, max(T_MEAS + 2 * gap, a + 3.05))):
            dials[j]["pulses"].append(tp)
        # Row 4, "many": ten more outlines appear across the pool (0.6 s, lag 0.12, in the outline lights below);
        # the band runs on with a glowing head (linear) over segments 4 to 14; its end tick lands on "expensive".
        x_start, x_end = world.seg_box(3)[0], world.FLOOR_X1
        v_band = (x_end - x_start) / (T_EXP - T_MANY)
        for i in range(3, 14):
            s0 = T_MANY + (world.seg_box(i)[0] - x_start) / v_band
            seg_go(i, s0, s0 + world.SEG_W / v_band)
        tick.go(T_EXP - 0.05, T_EXP + 0.2, 1.0)
        # Row 5, line_end(1): the model and the pool come to rest (gC back, needles M0, the first answers: nine red);
        # from "I'm" segments 14 to 1 turn from solid to outline, right to left (1.4 s); the three dials fade.
        lift_go("gC", E1, E1 + 0.6, 0.0)
        needles_go("M0", E1, E1 + 0.6, lag=0.4)
        look.go(E1, E1 + 0.6, states(world.RED_FIRST))
        for i in range(14):
            s0 = T_L2 + (13 - i) / 13.0 * 1.1
            solid.go(s0, s0 + 0.3, 0.0, idx=[i])
            if i < 3:
                dials[i]["off"] = Track(1.0).go(s0, s0 + 0.4, 0.0)
        self.T_needles_done = ang.last

        # extras, ring, wave: the outline lights (a function of time, see _outlines)
        cx = np.array([world.Pool.centre(n)[0] for n in world.GROUP_NAMES])
        ext = [i for i, n in enumerate(world.GROUP_NAMES) if n in world.EXTRA_NAMES]
        ext_order = np.argsort(np.argsort(cx[ext]))
        self.ext_t = {ext[j]: T_MANY + 0.6 * 0.12 * ext_order[j] for j in range(len(ext))}
        wave_rank = np.argsort(np.argsort(cx)) / (len(cx) - 1)
        self.wave_t = T_EVERY + 0.6 * wave_rank
        self.ring = world.choice_ring("gA")
        self.ring_base = self.ring.points - self.ring.get_center()
        self.ring.set_stroke(opacity=0.0)

        def lights(m):                       # the ring and the outline lights cross cues: one updater on the film clock
            t = film_time() - self.film_start
            self._ring(t)
            w.pool.ol = self._outlines(t)
            w.pool.paint()
        self.ring.add_updater(lights)
        self.ring_seq = [pool.outline(n).get_center() for n in ("gA", "gC", "gD", "gB")]   # on the outline drawn
        self.T_DEC, self.E2 = T_DEC, E2
        self.band_light = (T_BEF, T_BEF + 2.4)

        # keep everything for the timeline
        self.lift, self.ang, self.look, self.L, self.R = lift, ang, look, L, R
        self.drawn, self.shown, self.solid, self.tick = drawn, shown, solid, tick
        self.flights, self.dials = flights, dials
        self.alpha0 = pool.alpha0[self.grp_idx].copy()
        self.home = pool.home[self.grp_idx].copy()
        self.pulse = DotCloud(L.copy(), radius=0.04, color=INK_HI, opacity=0.0, glow=0.5)
        fx_objs = [f.cloud for f in flights] + [d["d"] for d in dials] + [self.pulse, self.ring]
        self.add(*fx_objs)
        if w.tag is not None:                                   # the tag stays on top
            self.mobjects.remove(w.tag)
            self.mobjects.append(w.tag)

        # ---------------------------------------------------------------- the rows (one play each)
        def row(t_next, *anims, **kw):
            self.play_until(t_next - dt, Clock(self, self._timeline), *anims, **kw)

        dc = w.labels["data change"]
        self.at(0)
        row(T_CMP, timed(leave(dc, run_time=0.6), T0, T0 + 0.6))
        row(T_L1)
        row(T_MANY)
        # Row 4: the ten outlines' points flash as their outlines appear (born from the pool); the band's head runs
        # to the end tick; `computation` lands on "expensive".
        comp = world.label("computation")
        ext_pts = np.concatenate([world.Pool.idx(n) for n in world.EXTRA_NAMES])
        delays = np.zeros(world.POOL_N)
        for n in world.EXTRA_NAMES:
            delays[world.Pool.idx(n)] = (self.ext_t[world.GROUP_NAMES.index(n)] - T_MANY) / 1.2
        flash = pool.cloud.to(radius=pool.cloud.radii[ext_pts].copy(), idx=ext_pts, delays=delays, span=0.35 / 1.2,
                              flash=0.35, pop=0.35, ease="linear")
        head = fly(lambda ts: np.column_stack([x_start + v_band * np.clip(ts, 0, None),
                                               np.full(len(np.atleast_1d(ts)), FLOOR_MID),
                                               np.zeros(len(np.atleast_1d(ts)))]),
                   GREY_1, duration=T_EXP - T_MANY, tail=0.35, radius=0.05, halo=0.24, appear=0.06, absorb=0.2,
                   rate_func=linear)
        row(E1, timed(flash, T_MANY, T_MANY + 1.2), timed(head, T_MANY, T_EXP + 0.35),
            timed(enter(comp, run_time=0.6), T_EXP, T_EXP + 0.6))
        row(T_DEC)
        self.remove(*[f.cloud for f in flights], *[d["d"] for d in dials], self.pulse)
        row(T_BEF)
        b0, b1 = self.band_light
        light = fly(lambda ts: np.column_stack([world.FLOOR_X0 + (world.FLOOR_X1 - world.FLOOR_X0) * np.clip(ts / (b1 - b0), 0, 1),
                                                np.full(len(np.atleast_1d(ts)), FLOOR_MID),
                                                np.zeros(len(np.atleast_1d(ts)))]),
                    GREY_1, duration=b1 - b0, tail=0.4, radius=0.05, halo=0.24, appear=0.05, absorb=0.12,
                    rate_func=linear)
        row(E2, timed(light, b0, b1 + 0.4))
        # Row 8: the ring fades, the world dims to 35% (0.9 s), `computation` fades; from line 4's first word the
        # post's title writes itself, two lines, complete by "somewhere".
        t1 = world.label("title 1")
        t2 = backstroke(T("to make an AI safer?", "title", INK_HI, parts={"s": "safer?"}))
        put(t2, 0.0, -0.3, edge=ORIGIN)
        q = [pool, model, test, cost]
        w1 = min(T_L3 + 1.2, T_SOME - 0.66)
        row(T_L4, *[timed(o.to_level(0.35), E2, E2 + 0.9) for o in q], timed(leave(comp, run_time=0.6), E2, E2 + 0.6),
            timed(enter(t1, run_time=1.2), T_L3, w1), timed(enter(t2, run_time=1.2), w1 - 0.6, T_SOME - 0.06))
        self.remove(self.ring)
        # Row 9: the title lets go (1.4 s): every word but the last fades glyph by glyph, left to right; `safer?`
        # slides on a shallow arc to its place right of the lights. In the same play the world returns to 100% from
        # left to right (pool, model, lights, floor; 2.6 s, lag 0.3), the lights' part ending on "longer".
        safer = world.Safer()
        safer.set_level(0.0)
        self.add(safer)
        self.mobjects.remove(w.tag)
        self.mobjects.append(w.tag)
        part = t2.part["s"]
        line1 = list(t1.submobjects)
        line2 = [g for g in t2.submobjects if not any(g is p for p in part)]
        c0, c1 = part.get_center().copy(), safer.text.get_center().copy()
        ctrl = np.array([c1[0], c0[1], 0.0])                   # right along its own baseline first, then up: it passes
        n1, n2 = len(line1), len(line2)                        # under line 1, whose words are gone before it rises

        def let_go(t):
            u = (t - T_L4) / 1.4
            for i, g in enumerate(line1):                        # glyph by glyph, left to right: line 1, then line 2
                a_ = 1.0 - float(_sm((u - 0.30 * i / (n1 - 1)) / 0.2))
                g.set_fill(opacity=a_)
                g.set_stroke(opacity=a_, background=True)
            for j, g in enumerate(line2):
                a_ = 1.0 - float(_sm((u - 0.30 - 0.30 * j / (n2 - 1)) / 0.25))
                g.set_fill(opacity=a_)
                g.set_stroke(opacity=a_, background=True)
            s = float(_sm((u - 0.25) / 0.75))
            part.move_to((1 - s) ** 2 * c0 + 2 * (1 - s) * s * ctrl + s ** 2 * c1)
            done = u >= 1.0
            part.set_fill(opacity=0.0 if done else 1.0)
            part.set_stroke(opacity=0.0 if done else 1.0, background=True)
            safer.level = 1.0 if done else 0.0

        d_ = 2.6 / 1.9                                           # four parts, lag 0.3: 2.6 s in all
        g0 = T_LONG - 1.6 * d_                                   # the lights' part (third) ends on "longer"
        back = [timed(o.to_level(1.0, run_time=d_), g0 + 0.3 * d_ * j, g0 + 0.3 * d_ * j + d_) for j, o in enumerate(q)]
        self.play_until(END, Clock(self, self._timeline), Clock(self, let_go), *back)
        self.remove(t1, t2)
        assert g0 + 1.9 * d_ <= END - 0.8 + 1e-6, "S02: the world's return must end 0.8 s before the scene ends"

    # -------------------------------------------------------------------- the timeline: the world at scene time t
    def _timeline(self, t: float) -> None:
        w = self.w
        pool, model, test, cost = w.pool, w.model, w.test, self.cost
        # pool groups: lifted out (gold, 0.6 up, 0.4 left) or home
        lf = self.lift.at(t)[:, :1]
        cl = pool.cloud
        cl.points[self.grp_idx] = self.home + lf * LIFT
        rgb_d, rgb_f = np.array(DATA.to_rgb()), np.array(FOCUS.to_rgb())
        cl.rgbas[self.grp_idx, :3] = rgb_d + (rgb_f - rgb_d) * lf
        a_l = LIFT_ALPHA * np.clip(self.alpha0 + 0.2, 0, 1)
        cl.rgbas[self.grp_idx, 3] = self.alpha0 + (a_l - self.alpha0) * lf[:, 0]
        # model: needles and the asked flick
        model.angles = world.PATTERNS["M0"].copy() if t >= self.T_needles_done else self.ang.at(t)[:, 0]
        fl = np.zeros(40)
        order = -(world.NEEDLE_POS[:, 0])
        rank = (order - order.min()) / max(np.ptp(order), 1e-9)
        for f0, fd in self.flicks:
            if f0 < t < f0 + fd:
                loc = np.clip(((t - f0) / fd - 0.5 * rank) / 0.5, 0, 1)
                fl = fl + 12 * world.DEG * np.sin(np.pi * loc)
        model.flick = fl
        # the test
        test.look = self.look.at(t)
        test.paint()
        # pulses of the sweeps (out to the rim and back)
        pos, alpha = self.L.copy(), np.zeros(24)
        for ks, wdt in self.sweeps:
            u = (t - ks) / wdt
            on = (u > 0) & (u < 1)
            if on.any():
                tri = np.where(u < 0.5, _sm(2 * u), _sm(2 - 2 * u))[:, None]
                pos = np.where(on[:, None], self.L + (self.R - self.L) * tri, pos)
                alpha = np.where(on, 1.0, alpha)
        self.pulse.points = pos
        self.pulse.rgbas[:, 3] = alpha
        # the cost floor
        cost.drawn = self.drawn.at(t)
        sh = self.shown.at(t)[:, 0]
        b0, b1 = self.band_light
        if b0 < t < b1 + 0.4:                                    # the light on the band brightens each outline it passes
            xl = world.FLOOR_X0 + (world.FLOOR_X1 - world.FLOOR_X0) * min((t - b0) / (b1 - b0), 1.0)
            xc = np.array([sum(world.seg_box(i)) / 2 for i in range(14)])
            fade = 1.0 - float(_sm((t - b1) / 0.4))
            sh = sh * (1 + 1.6 * fade * np.exp(-((xc - xl) / 0.45) ** 2))
        cost.shown = sh
        cost.solid = self.solid.at(t)[:, 0]
        cost.tick_on = self.tick.at(t)
        cost.paint()
        # flights (streams, sparks, copies of the lights)
        for f in self.flights:
            if f.start - 0.1 <= t <= f.end + 0.1:
                f.apply(t)
        # dials: born, pulsed, faded
        for d in self.dials:
            op = d["on"].at(t) * (d["off"].at(t) if "off" in d else 1.0)
            d["d"].ring.set_stroke(opacity=op)
            d["d"].arc.set_stroke(opacity=op)
            k = 1.0 + 0.3 * float(sum(_bump((t - tp) / 0.5) for tp in d["pulses"]))
            if abs(k - d["scale"]) > 1e-9:
                d["d"].scale(k / d["scale"], about_point=d["c"])
                d["scale"] = k

    def _ring_state(self, t):
        T, HOP, DWELL = self.T_DEC, 0.55, 0.2
        if t <= T:
            return None
        seq = self.ring_seq
        u = (t - T) / 0.4
        tau = t - (T + 0.4)
        if tau < 0:
            pos, scale, op = seq[0], 0.3 + 0.7 * float(_sm(u)), float(_sm(u))
        else:
            j = int(tau // HOP)
            r = tau - j * HOP
            a, b = seq[j % 4], seq[(j + 1) % 4]
            s = 0.0 if r < DWELL else float(_sm((r - DWELL) / (HOP - DWELL)))
            pos = a + (b - a) * s + UP * 0.3 * 4 * s * (1 - s)
            scale, op = 1.0 - 0.15 * 4 * s * (1 - s), 1.0
        op *= 1.0 - float(_sm((t - self.E2) / 0.6))
        return pos, scale, op

    def _ring(self, t):
        st = self._ring_state(t)
        if st is None:
            self.ring.set_stroke(opacity=0.0)
            return
        pos, scale, op = st
        self.ring.set_points(self.ring_base * scale + pos)
        self.ring.set_stroke(opacity=op)

    def _outlines(self, t):
        names = world.GROUP_NAMES
        ol = np.array([0.6 if n in ("gA", "gB", "gC", "gD") else 0.0 for n in names])
        for i, te in self.ext_t.items():                      # the ten appear: up to 55%, then rest at 25% (P02)
            if t > te:
                up = float(_sm((t - te) / 0.25))
                down = float(_sm((t - te - 0.25) / 0.5))
                ol[i] = 0.55 * up + (0.25 - 0.55) * down
        st = self._ring_state(t)
        if st is not None:                                    # the outline that the ring visits brightens
            pos, _, op = st
            for i, n in enumerate(names[:4]):
                dd = float(np.linalg.norm(self.w.pool.outline(n).get_center()[:2] - pos[:2]))
                ol[i] += 0.4 * op * max(0.0, 1.0 - dd / 1.0) ** 2
        ol += 0.4 * _bump((t - self.wave_t) / 0.5)              # on "every": all 14 pulse in a wave, left to right
        return np.clip(ol, 0.0, 1.0)
