"""S05 A question, not a method (storyboard section 5, S05). It starts in pose P04 and ends in pose P05.

# qa: bleed   (the open boundary is bleed_ok: it crosses |x| = 6.4, rule 17 of 1.2)

Rows (kit lines from 0) and what lands on which word:
  at(0)                    the S04 label, the threads and the marked points fade; the twin keeps flickering
  at_word(0, "method")     gB sinks back and turns starlight (outline stays dashed); the ten extra outlines fade
  at(1)                    the shortcut lane draws from its left end; `a shortcut` lands on "shortcut"
  at_word(1, "computation") `computation` lands; eight pieces of work fall into the lane (1.0 s, lag 0.1); a dotted
                           continuation reaches the end tick as "directly" ends
  at_word(1, "it")         the end tick grows down across both rows; both ends pulse on "helped"
  line_end(1)              the "if" is taken back; the four outlines pulse in turn from line 3's first word; on
                           "evidence" the pieces lift and dissolve and the twin dissolves back into the model
  at_word(2, "cheaply")    nothing moves on the lane; on "reliably" the shaded held-back row pulses once
  at_word(2, "existing")   the outlines settle at 40%; the two labels fade: the question is in REST
  line_end(2)              the question dims to 60%
  at(3)                    move 4 (MOVE4, GLIDE, 3.4 s); the boundary wipes in as the frame crosses it; the
                           question sinks to 15%, the cost floor fades to 0; the tag goes as the test lights leave
                           the frame; the lone point brightens in the last 1.0 s of the move
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/ and world.py

import math  # noqa: E402

import numpy as np  # noqa: E402

from kit import *  # noqa: E402,F401,F403
import world  # noqa: E402
from world import C  # noqa: E402

LANE_Y, FLOOR_Y, FLOOR_X1 = world.LANE_Y, world.FLOOR_Y, world.FLOOR_X1
PIECE = GREY_1                # pieces of supposed work: GREY_1 at 60% (3.5, Object 4, states of the lane)
PIECE_OP = 0.6
T4 = 3.4                      # move 4 (3.1)


def _clip01(x):
    return float(min(max(x, 0.0), 1.0))


def ramp(t, a, b, func=MOVE):
    """0 before a, 1 after b, ``func`` in between (scene seconds)."""
    return float(func(_clip01((t - a) / max(b - a, 1e-9))))


def bump(t, a, b):
    """One PULSE (there and back) from a to b."""
    return float(PULSE(_clip01((t - a) / max(b - a, 1e-9))))


def cubic(p0, p1, p2, p3):
    p0, p1, p2, p3 = (np.asarray(p, dtype=float) for p in (p0, p1, p2, p3))

    def f(s):
        s = _clip01(s)
        return (1 - s) ** 3 * p0 + 3 * (1 - s) ** 2 * s * p1 + 3 * (1 - s) * s * s * p2 + s ** 3 * p3
    return f


class Drive(Animation):
    """Calls fn(t) on every frame of a play with the scene time t of that frame (t0 + alpha * run_time), so that
    windows are written in scene seconds; at alpha = 1 it gives the state of the play's end. The objects it changes
    keep their own updaters (idle motion never stops)."""

    def __init__(self, scene, fn, **kw):
        kw.setdefault("rate_func", linear)
        super().__init__(Mobject(), suspend_mobject_updating=False, **kw)
        self._scene, self.fn = scene, fn

    def begin(self) -> None:
        self.t0 = float(self._scene.now)
        super().begin()

    def interpolate_mobject(self, alpha: float) -> None:
        self.fn(self.t0 + alpha * self.run_time)


def _calm_paint(self):
    """Twin.paint, and then the needles held still by ``calm`` (0..1) while its lights keep changing (the needles
    "settle for a moment" as the retrain segment drops; the what-if stays open, so the lights do not settle)."""
    world.Twin.paint(self)
    if getattr(self, "calm", 0.0) > 0.0:
        amp = idle_gain() * self.jitter * (1.0 - self.calm)
        k = int(math.floor(film_time() * 6))
        jump = (world.rand(world.SEEDS["twin"], k, 40) * 2 - 1) * 20 * world.DEG
        for i, nd in enumerate(self.needles):
            nd.set_angle(self.rest[i] + amp * jump[i])
    return self


def _masked_paint(self):
    """CostFloor.paint, and then the dashes of the shortcut lane hidden where supposed work lies on it
    (``lane_mask``, one value per dash): the pieces and the dotted line take the lane's place while they are there,
    and the empty dashed lane comes back exactly when they go."""
    world.CostFloor.paint(self)
    mask = getattr(self, "lane_mask", None)
    if mask is not None and np.any(mask > 0):
        for d, m in zip(self.lane, mask):
            if m > 0:
                d.set_stroke(opacity=d.get_stroke_opacity() * (1.0 - m))
    return self


class S05(Narrated):
    def build(self):
        w = world.pose("P04", self)
        pool, model, test, cost, twin, lone = w.pool, w.model, w.test, w.cost, w.twin, w.lone
        f = 1.0 / self.fps
        ws = self.word_span

        # cues (scene seconds)
        t_l0, t_l1, t_l2, t_l3 = (self.line_start(i) for i in range(4))
        t_method = ws(0, "method")[0]
        t_short = ws(1, "shortcut")[0]
        t_comp = ws(1, "computation")[0]
        t_direct_end = ws(1, "directly")[1]
        t_it = ws(1, "it")[0]
        t_helped = ws(1, "helped")[0]
        t_l1_end = self.line_end(1)
        t_evid = ws(2, "evidence")[0]
        t_cheap = ws(2, "cheaply")[0]
        t_reli = ws(2, "reliably")[0]
        t_exist = ws(2, "existing")[0]
        t_l2_end = self.line_end(2)
        # Move 4 runs 3.4 s and must be at SPECK on the last frame: the narration leaves 3.36 s from line 4's first
        # word to the end of the scene, so it ends 0.1 s before the end and starts 0.14 s before "The".
        m1 = self.scene_duration - 0.1
        m0 = m1 - T4

        # the what-if stays open: the twin flickers from the first frame (the idle gain eases it in)
        twin.jitter = 1.0
        twin.calm = 0.0
        twin.paint = types.MethodType(_calm_paint, twin)
        cost.lane_mask = np.zeros(len(cost.lane))
        cost.paint = types.MethodType(_masked_paint, cost)
        dash_x = np.array([d.get_center()[0] for d in cost.lane])

        # ---------------------------------------------------------------- row 1: at(0) "This is a research question"
        threads = w.extra["threads"]
        lab_assoc = w.labels["associated with this answer"]

        def fade_threads(t):
            u = ramp(t, t_l0, t_l0 + 1.0)
            for th_ in threads:
                th_.set_stroke(opacity=0.10 * (1 - u))

        self.at(0)
        self.play_until(t_method - f,
                        Drive(self, fade_threads),
                        timed(pool.to_marks(0.0), t_l0, t_l0 + 1.0),
                        timed(leave(lab_assoc), t_l0, t_l0 + 1.0))
        model.behind.remove(threads)

        # ---------------------------------------------------------------- row 2: "not a method"
        # gB's points sink back and turn starlight over the whole row; its outline stays dashed and steps back to
        # 60%, so that the four outlines can pulse alike in line 3 and settle together at 40% on "existing".
        self.play_until(t_l1 - f,
                        pool.restore("gB"),
                        timed(pool.to_outlines({"gB": 0.6, **{n: 0.0 for n in world.EXTRA_NAMES}}, run_time=1.2),
                              t_method, t_method + 1.2))

        # ---------------------------------------------------------------- row 3: at(1) "If a shortcut"
        lab_short = world.label("a shortcut")
        lab_comp = world.label("computation")
        cost.set_lane(1.0, 0.0)
        self.play_until(t_comp - f,
                        timed(cost.to_lane(1.0, run_time=0.8), t_l1, t_l1 + 0.8),
                        timed(enter(lab_short), t_short, t_short + 0.6))

        # ---------------------------------------------------------------- row 4: "computation as trying every change directly"
        # Eight pieces of work (C36, C38, without words): six ticks from the four outlines (score candidates), one
        # segment from the twin with sparks (retrain), one pulse from the held-back row (validate). They come down
        # on arcs, right of x = -2.8 at the end, and line up from the lane's left end over 1.6.
        def outline_point(name, deg):
            poly = np.asarray(world.GROUP_POLYS[name])[:, :2]
            c = np.asarray(world.GROUP_CENTRES[name])[:2]
            d = np.array([math.cos(math.radians(deg)), math.sin(math.radians(deg))])
            p = poly[np.argmax((poly - c) @ d)]
            return C(p[0], p[1])

        tick_src = [("gB", -40), ("gA", -70), ("gA", -15), ("gD", -55), ("gC", -75), ("gC", -20)]
        slots = [C(-2.95 + 0.11 * j, LANE_Y) for j in range(6)] + [C(-2.0, LANE_Y), C(-1.5, LANE_Y)]
        pieces = [Line(C(0, -0.09), C(0, 0.09), stroke_color=PIECE, stroke_width=W_LINE, stroke_opacity=0.0)
                  for _ in range(6)]
        pieces.append(Rectangle(width=world.SEG_W, height=world.SEG_H, stroke_width=0, fill_color=PIECE,
                                fill_opacity=0.0))
        pieces.append(Circle(radius=0.055, stroke_width=0, fill_color=PIECE, fill_opacity=0.0))
        paths = []
        for j, (name, deg) in enumerate(tick_src):
            s = outline_point(name, deg)
            paths.append(cubic(s, s + C(0.8, 0.2), slots[j] + C(0.6, 1.4), slots[j]))
        s_twin = world.TWIN_C + C(-0.35, -0.42)                       # the twin's lower-left rim
        paths.append(cubic(s_twin, s_twin + C(-0.5, 0.1), slots[6] + C(0.6, 0.7), slots[6]))
        s_held = test.pos(1)                                          # the lowest light of the held-back row
        paths.append(cubic(s_held, s_held + C(-1.2, -0.2), C(-0.7, -2.12), slots[7]))
        for p, path in zip(pieces, paths):
            p.move_to(path(0.0))

        n_p, lag = len(pieces), 0.1
        d_one = 1.0 / (1 + lag * (n_p - 1))                            # 1.0 s with lag_ratio 0.1
        starts = [t_comp + i * lag * d_one for i in range(n_p)]
        t_landed = starts[-1] + d_one

        sparks = DotCloud(np.tile(s_twin, (5, 1)), radius=0.02, color=PIECE, opacity=0.0)
        spark_dir = np.array([[math.cos(a), math.sin(a), 0.0] for a in np.linspace(0.6, 2.6, 5)])

        dotted = world.dots_along(np.array([[-1.4, LANE_Y, 0.0], [FLOOR_X1, LANE_Y, 0.0]]), step=0.085, radius=0.02,
                                  color=PIECE, opacity=PIECE_OP)
        dot_x = dotted.points[:, 0].copy()
        dotted.rgbas[:, 3] = 0.0
        head = {"x": -1.4}

        # the stretch of lane that each piece covers once it has landed (they line up from -3.0 to -1.4)
        cover = [(-3.0 + 0.11 * j, -3.0 + 0.11 * (j + 1)) for j in range(6)] + [(-2.34, -1.66), (-1.66, -1.4)]

        def mask_lane(present, x_head):
            m = np.zeros(len(dash_x))
            for (a, b), pr in zip(cover, present):
                m = np.maximum(m, pr * ((dash_x >= a) & (dash_x < b)))
            m = np.maximum(m, (dash_x >= -1.4) * np.clip((x_head - dash_x) / 0.12 + 0.5, 0.0, 1.0))
            cost.lane_mask = m

        def set_piece(p, pos, op):
            p.move_to(pos)
            if isinstance(p, Line):
                p.set_stroke(opacity=op)
            else:
                p.set_fill(opacity=op)

        def paint_dotted(x_head):
            head["x"] = x_head
            dotted.rgbas[:, 3] = PIECE_OP * np.clip((x_head - dot_x) / 0.09, 0.0, 1.0)

        def fall(t):
            for i, (p, path) in enumerate(zip(pieces, paths)):
                a = _clip01((t - starts[i]) / d_one)
                op = ramp(a, 0.0, 0.18, linear) * (1.0 - (1.0 - PIECE_OP) * ramp(a, 0.8, 1.0, linear))
                set_piece(p, path(MOVE(a)), op)
            a6 = _clip01((t - starts[6]) / d_one)                        # the retrain segment and its sparks
            pts = np.array([paths[6](MOVE(_clip01(a6 - 0.06 * (k + 1)))) + 0.22 * a6 * spark_dir[k] for k in range(5)])
            sparks.points = pts
            sparks.rgbas[:, 3] = 0.8 * (a6 > 0.0) * (1 - a6) * np.ones(5)
            twin.calm = min(ramp(t, starts[6] - 0.15, starts[6] + 0.15), 1 - ramp(t, t_landed + 0.1, t_landed + 0.45))
            paint_dotted(-1.4 + (FLOOR_X1 + 1.5) * ramp(t, t_landed, t_direct_end, linear))
            mask_lane([ramp(_clip01((t - starts[i]) / d_one), 0.9, 1.0, linear) for i in range(n_p)], head["x"])

        self.add(dotted, sparks, *pieces)
        self.play_until(t_it - f,
                        Drive(self, fall),
                        timed(enter(lab_comp), t_comp, t_comp + 0.6))

        # ---------------------------------------------------------------- row 5: "it has not helped us very much"
        ends = [glow_sprite(0.24, GREY_1, peak=0.8).move_to(C(FLOOR_X1, FLOOR_Y + 0.05)),
                glow_sprite(0.24, GREY_1, peak=0.8).move_to(C(FLOOR_X1, LANE_Y))]
        for g in ends:
            g.set_fill(opacity=0.0)

        def both_ends(t):
            p = bump(t, t_helped, t_helped + 0.6)
            for g in ends:
                g.set_fill(opacity=p)

        self.add(*ends)
        self.play_until(t_l1_end - f,
                        timed(cost.to_tick_down(1.0, run_time=0.4), t_it, t_it + 0.4),
                        Drive(self, both_ends))
        self.remove(*ends)

        # ---------------------------------------------------------------- row 6: the "if" is taken back; "evidence"
        four = ["gA", "gB", "gC", "gD"]
        ol_base = pool.ol.copy()
        slot_pos = [p.get_center().copy() for p in pieces]
        tw_rim0 = twin.rim.points.copy()
        tw_c0 = [nd.c.copy() for nd in twin.needles]
        tw_L0 = [nd.L for nd in twin.needles]
        tw_ring0 = [r.points.copy() for r in twin.rings]
        tw_core0 = [c.points.copy() for c in twin.cores]
        tw_light0 = [np.asarray(p, dtype=float) for p in twin.light_pos]
        tw_anchor0 = [world.TWIN_C + (p - world.TWIN_C) * (world.M_R / 2) / 1.5 for p in tw_light0]   # its right rim
        t_back = t_l1_end + 0.8

        def take_back(t):
            # (0 to 0.8 s) the dotted line draws back to the end of the pieces
            paint_dotted(FLOOR_X1 + 0.1 - (FLOOR_X1 + 1.5) * ramp(t, t_l1_end, t_back))
            # from line 3's first word: gA, gB, gC, gD pulse once in turn, 0.5 s each
            ol = ol_base.copy()
            for j, n in enumerate(four):
                p = bump(t, t_l2 + 0.5 * j, t_l2 + 0.5 * (j + 1))
                k = world.GROUP_NAMES.index(n)
                ol[k] = ol_base[k] + (1.0 - ol_base[k]) * p
                pool.outline(n).set_stroke(color=FOCUS if p <= 0 else mix(FOCUS, FOCUS_HI, 0.85 * p))
            pool.ol = ol
            pool.paint()
            # on "evidence" (1.2 s): the pieces lift out of the lane and dissolve ...
            present = []
            for i, p in enumerate(pieces):
                u = ramp(t, t_evid + 0.04 * i, t_evid + 0.04 * i + 0.9)
                set_piece(p, slot_pos[i] + C(0, 0.35 * u), PIECE_OP * (1 - u))
                present.append(1.0 - u)
            mask_lane(present, head["x"])
            # ... and the twin and its small arc dissolve back into the model (the reverse of its birth in S04)
            u = ramp(t, t_evid, t_evid + 1.2)
            u2 = ramp(t, t_evid, t_evid + 0.7)
            ctr = world.TWIN_C + (world.M_C - world.TWIN_C) * u
            k = 1.0 + u
            twin.rim.points = ctr + (tw_rim0 - world.TWIN_C) * k
            for nd, c0, L0 in zip(twin.needles, tw_c0, tw_L0):
                nd.c = ctr + (c0 - world.TWIN_C) * k
                nd.L = L0 * k
            sh = max(1.0 - u2, 1e-3)
            for r, c_, r0, c0, l0, a0 in zip(twin.rings, twin.cores, tw_ring0, tw_core0, tw_light0, tw_anchor0):
                anchor = ctr + (a0 - world.TWIN_C) * k
                pos = anchor + (l0 - a0) * (1.0 - u2)
                r.points = pos + (r0 - l0) * sh
                c_.points = pos + (c0 - l0) * sh
            twin.level = 1.0 - u

        self.play_until(t_cheap - f,
                        Drive(self, take_back),
                        timed(cost.to_tick_down(0.0, run_time=0.8), t_l1_end, t_back))
        for n in four:
            pool.outline(n).set_stroke(color=FOCUS)
        self.remove(twin, dotted, sparks, *pieces)

        # ---------------------------------------------------------------- row 7: "more cheaply or more reliably"
        # On "cheaply" nothing moves on the lane. On "reliably" the shaded held-back row pulses once and stays dark.
        look0 = test.look.copy()
        outer = np.array(world.OUTER)
        grey3 = np.array(GREY_3.to_rgb())

        def held_pulse(t):
            p = bump(t, t_reli, t_reli + 0.8)
            test.edge.set_stroke(color=GREY_3 if p <= 0 else mix(GREY_3, GREY_2, p))     # grey, never white: not "chosen"
            look = look0.copy()
            look[outer, :3] = look0[outer, :3] + (grey3 - look0[outer, :3]) * p
            test.look = look
            test.paint()

        self.play_until(t_exist - f, Drive(self, held_pulse))
        test.look = look0.copy()
        test.edge.set_stroke(color=GREY_3)
        test.paint()

        # ---------------------------------------------------------------- row 8: "than strong existing methods"
        self.play_until(t_l2_end - f,
                        timed(pool.to_outlines({"gB": 0.4}, run_time=0.8), t_exist, t_exist + 0.8),
                        timed(leave(lab_short), t_exist, t_exist + 0.6),
                        timed(leave(lab_comp), t_exist, t_exist + 0.6))

        # ---------------------------------------------------------------- row 9: the pause; the question dims to 60%
        world.clock_move(self, "SPECK", m0, m1, rate=GLIDE, path=world.MOVE4)
        self.play_until(t_l3 - f, *[o.to_level(0.6) for o in (pool, model, test, cost)])

        # ---------------------------------------------------------------- row 10: at(3) "...is narrower." Move 4.
        # When do the test lights leave the frame (with their glow)? The tag goes then, and their red turns grey
        # out of sight (no red in the question while the camera is on the pilot).
        lights = np.array([world.light_pos(k, 1.0) for k in range(24)])
        t_out = m1
        for t in np.arange(m0, m1, 0.01):
            cx, cy, wd = world.MOVE4(GLIDE(_clip01((t - m0) / T4)))
            hh = wd * 9 / 16
            if np.all((np.abs(lights[:, 0] - cx) > wd / 2 + 0.3) | (np.abs(lights[:, 1] - cy) > hh / 2 + 0.3)):
                t_out = float(t)
                break
        # The boundary draws from left to right (clip wipe) while the frame crosses it.
        t_cross = m0
        for t in np.arange(m0, m1, 0.01):
            if world.MOVE4(GLIDE(_clip01((t - m0) / T4)))[1] <= world.BOUND_Y:
                t_cross = float(t)
                break
        wipe0, wipe1 = t_cross - 0.55, t_cross + 0.55
        bound = world.Boundary()
        clip = Rectangle(width=1.0, height=1.2, stroke_width=0, fill_color=BG, fill_opacity=0.0)
        clip_state = {"on": True}

        def set_clip_right(x):
            clip.stretch_to_fit_width(x + 13.0)
            clip.move_to(C((x - 13.0) / 2, world.BOUND_Y))

        set_clip_right(-7.4)
        set_clip(bound, clip)

        def wipe(t):
            u = ramp(t, wipe0, wipe1, MOVE)
            set_clip_right(-7.4 + 14.8 * u if u < 1 else 13.0)
            if u >= 1 and clip_state["on"]:
                for m in bound.get_family():
                    m.fx_clip = None
                clip_state["on"] = False

        self.add(clip, bound)
        q_end = t_l3 + 1.5
        self.play_until(self.scene_duration,
                        Drive(self, wipe),
                        *[timed(o.to_level(0.15, run_time=1.5), t_l3, q_end) for o in (pool, model, test)],
                        timed(cost.to_level(0.0, run_time=0.75), t_l3, t_l3 + 0.75),
                        timed(test.to_grey(1.0, run_time=0.3), t_out, t_out + 0.3),
                        timed(leave(w.tag, run_time=0.6, rate_func=MOVE), t_out, t_out + 0.6),
                        timed(lone.to_level(1.0, run_time=1.0), m1 - 1.0, m1))
        self.remove(clip)
