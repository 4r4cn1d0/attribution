"""S01 "Which one would actually help?" (storyboard section 5, S01). Starts in pose P00, ends in pose P01.

Rows of the beat table, one play each (rule 3 of 1.2); every play ends one frame before the next row's cue, as
at() does, so the next row's first change is on its word.

  row 1  start .. "fails"      the first ask, slowly: the request pulse of P00 reaches the rim, the needles ripple
                               right to left, the answer pulse runs back to light 10; `model` lands on "model"
  row 2  "fails" .. line 2     light 10 turns red (tag on with it); three sweeps of the 24 lights (1.0, 0.6, 0.4 s),
                               hollow in between, the same nine red each time; `safety test` from "safety"
  row 3  line 2 .. "post-training"   camera TEST-IN -> W (clock_move, 3.0 s); the pool lights up from the model's
                               side outward, then brightens once; `post-training examples` as the camera arrives
  row 4  "post-training" .. "trained"   the lens fallback (world.py: the lens fails its own check): 8 points, each
                               0.5 or more from the others, open into example glyphs in place
  row 5  "trained" .. line 3   the needles hold still for 1 s; on "taught" the response strokes brighten left to
                               right and a faint copy of each drifts to the model's left rim, where a needle glints
  row 6  line 3 .. "replace"   the glyphs close into their points, the label fades; gA turns gold on "remove",
                               then lifts and fades (removed; the holes stay)
  row 7  "replace" .. line 4   40 different points (starlight core, gold halo) fly in on arcs into the same holes
  row 8  line 4 .. "which"     the change undoes; gA's outline stays; gB, gC, gD outlines draw; `data change`
  row 9  "which" .. end        the four outlines pulse round and round; the nine red lights pulse once on "help"

Motions that are pure functions of the scene time (the sweeps, the copies and glints, the outline pulses) run as
``Clocked`` animations: each reads the film clock on every frame, so it continues across a cue without a seam
and a play's length can neither squeeze it nor cut it (rule 3 of 1.2, the clock-driven exception).
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/ (render.py sets it too)

from kit import *  # noqa: E402,F401,F403
import world  # noqa: E402

G4 = ("gA", "gB", "gC", "gD")


class Clocked(Animation):
    """``fn(t)`` on every frame of the play, with t the scene time of that frame (read from the film clock, which the
    kit sets before it interpolates), held at t0 before the window and at t1 after it. It ignores the play's alpha,
    so a play's length can neither squeeze it nor cut it, and the same function can continue in the next play."""

    def __init__(self, scene, fn, t0: float, t1: float, carrier=None, **kw):
        super().__init__(carrier if carrier is not None else Mobject(), rate_func=CLOCK,
                         suspend_mobject_updating=False, **kw)
        self.scene_, self.fn, self.t0, self.t1 = scene, fn, float(t0), float(t1)

    def create_starting_mobject(self):
        return Mobject()

    def interpolate_mobject(self, alpha: float) -> None:
        t = film_time() - float(self.scene_.film_start)
        self.fn(float(np.clip(t, self.t0, self.t1)))


def held(rise: float, fall: float):
    """A rate function built from MOVE: up to 1 in the first ``rise`` of the play, held, back to 0 in the last ``fall``."""
    def f(a: float) -> float:
        if a < rise:
            return MOVE(a / rise)
        if a > 1.0 - fall:
            return MOVE((1.0 - a) / fall)
        return 1.0
    return f


def _u(t: float, t0: float, dur: float) -> float:
    return float(np.clip((t - t0) / max(dur, 1e-9), 0.0, 1.0))


class S01(Narrated):
    def build(self):
        w = world.pose("P00", self)
        pool, model, test, cloud = w.pool, w.model, w.test, w.pool.cloud
        f1 = 1.0 / self.fps

        def cue(t: float) -> float:
            """A row's play ends one frame before the next cue (as at() stops), so the next change lands ON it."""
            return t - f1

        word = lambda i, s: self.word_span(i, s)[0]              # noqa: E731
        T_MODEL, T_FAILS, T_SAFETY = word(0, "model"), word(0, "fails"), word(0, "safety")
        T_L1, T_POST, T_TRAINED, T_TAUGHT = self.line_start(1), word(1, "post-training"), word(1, "trained"), word(1, "taught")
        T_L2, T_REMOVE, T_REPLACE = self.line_start(2), word(2, "remove"), word(2, "replace")
        T_L3, T_CHANGE, T_WHICH, T_HELP = self.line_start(3), word(3, "change"), word(3, "which"), word(3, "help")
        END = self.scene_duration

        gA = pool.idx("gA")
        home, alpha0 = pool.home, pool.alpha0

        # ============================================================ row 1: the first ask, slowly (start .. "fails")
        pulse = w.extra["pulse"]                                   # P00: on its way from light 10, 30% of its path

        def request(t: float) -> None:                             # the rest of the path, then the tail runs into the rim
            c = 0.15 + 0.55 * _u(t, 0.0, 0.75)
            pulse.set_time(c)
            if c > 0.5:
                pulse.set_presence(1.0 - float(world.smoothstep(0.5, 0.7, c)))

        answer = Runner(world.ask_path(10, test)[::-1].copy(), INK, duration=0.5, tail=0.2, radius=0.045, halo=0.16)
        lbl_model = world.follow(self, world.label("model"), world.anchor_of("model"))
        T_RIPPLE = 0.5
        T_ANSWER = T_RIPPLE + 0.5
        self.play_until(
            cue(T_FAILS),
            Clocked(self, request, 0.0, 0.75),
            timed(model.ask(0.4), T_RIPPLE, T_RIPPLE + 0.4),                   # right to left, from where it arrived
            timed(enter(lbl_model), T_MODEL - 0.1, T_MODEL + 0.5),             # late in the ripple, on "model"
            timed(answer.flight(appear=0.08, absorb=0.25), T_ANSWER, T_ANSWER + 0.8),
            timed(pool.to_outlines({n: 0.0 for n in G4}), 0.0, 0.6),          # see needs_world_change: P00 outlines
        )
        self.remove(pulse)

        # ============================================================ row 2: fails, then three sweeps ("fails" .. line 2)
        self.at_word(0, "fails")
        hollow = test._looks({k: "hollow" for k in range(24)})
        target = test._looks(test.states_with(world.RED_FIRST, "pale"))
        LF = 0.35                                                   # a streak is 35% of its ray
        sweeps, holes = [], []
        s = T_FAILS + 0.31
        for D, d in ((1.0, 0.10), (0.6, 0.075), (0.4, 0.067)):     # one slowly, then faster, then fast; each leg 2-4 frames at 30 fps
            item = 2 * d + 0.06
            sweeps.append(dict(start=s, gap=(D - item) / 23, d=d, v=(1 + LF) / d))
            s += D + 0.03
            if len(sweeps) < 3:
                holes.append((s, 0.22))                             # the lights go hollow before the next sweep
                s += 0.22 + 0.03
        SWEEP_END = s - 0.03
        assert SWEEP_END <= T_L1 - 0.1, f"S01: the third sweep must end in the silence before line 2 ({SWEEP_END:.2f})"

        rays = []
        for k in range(24):
            p = test.pos(k)
            q = world.Model.rim_point(p)
            u = (q - p) / np.linalg.norm(q - p)
            rays.append((p + 0.15 * u, q))
        streaks = VGroup(*[VMobject(stroke_color=INK, stroke_width=W_LINE, stroke_opacity=0.0, fill_opacity=0.0)
                           .set_points_as_corners([a, a + 1e-3 * RIGHT]) for a, _ in rays])

        def put_streak(k: int, p0: float, p1: float) -> None:
            a, b = rays[k]
            lo, hi = max(p0, 0.0), min(p1, 1.0)
            if hi - lo < 0.02:
                streaks[k].set_stroke(opacity=0.0)
                return
            streaks[k].set_points_as_corners([a + (b - a) * lo, a + (b - a) * hi])
            streaks[k].set_stroke(opacity=0.75)

        def sweep_state(t: float) -> None:
            look = hollow.copy()
            look[10] = hollow[10] + (target[10] - hollow[10]) * MOVE(_u(t, T_FAILS, 0.3))
            shown = [None] * 24
            phases = [("sweep", sw) for sw in sweeps]
            for j, h in enumerate(holes):
                phases.insert(2 * j + 1, ("hollow", h))
            for kind, ph in phases:
                if kind == "hollow":
                    if t < ph[0]:
                        break
                    look = look + (hollow - look) * MOVE(_u(t, *ph))
                    continue
                if t < ph["start"]:
                    break
                for k in range(24):
                    st = ph["start"] + k * ph["gap"]
                    d, v = ph["d"], ph["v"]
                    if st <= t < st + d:                            # the request: light -> rim
                        head = v * (t - st)
                        shown[k] = (head - LF, head)
                    elif st + d <= t < st + 2 * d:                  # the answer: rim -> light
                        head = 1.0 - v * (t - st - d)
                        shown[k] = (head, head + LF)
                    arrive = st + d + 1.0 / v                        # the answer reaches the light: it shows its state
                    look[k] = look[k] + (target[k] - look[k]) * MOVE(_u(t, arrive, 0.06))
            test.look = look
            test.paint()
            for k in range(24):
                if shown[k] is None:
                    streaks[k].set_stroke(opacity=0.0)
                else:
                    put_streak(k, *shown[k])

        tag = self.hud_tag()
        lbl_safety = world.follow(self, world.label("safety test"), world.anchor_of("safety test"))
        self.add(streaks)
        self.play_until(
            cue(T_L1),
            Clocked(self, sweep_state, T_FAILS, SWEEP_END + 0.05, carrier=streaks),
            timed(FadeIn(tag), T_FAILS, T_FAILS + 0.6),                         # the tag comes on with the first red light
            timed(enter(lbl_safety), T_SAFETY, T_SAFETY + 0.6),
        )
        self.remove(streaks)
        test.set_states(test.states_with(world.RED_FIRST, "pale"))               # the same values, exactly

        # ============================================================ row 3: pull back to W (line 2 .. "post-training")
        self.at(1)
        world.clock_move(self.frame, "W", T_L1, T_L1 + 3.0)       # move 1: TEST-IN to W, 3.0 s
        pool.set_level(1.0)                                         # the same picture: the 10% moves from the
        cloud.set_opacities(0.1 * alpha0)                           # whole cloud into each point's own alpha
        near_model = np.linalg.norm(home[:, :2] - world.M_C[:2], axis=1)
        T_FLARE = T_L1 + 2.2

        def flare(t: float) -> None:                                # the whole pool brightens once, late in the move
            cloud.glows[:] = 0.22 * PULSE(_u(t, T_FLARE, 0.6))

        lbl_pte = world.follow(self, world.label("post-training examples"), world.anchor_of("post-training examples"))
        self.play_until(
            cue(T_POST),
            timed(leave(lbl_model), T_L1, T_L1 + 0.6),
            timed(leave(lbl_safety), T_L1, T_L1 + 0.6),
            timed(cloud.to(opacity=alpha0, lag=0.7, order=near_model), T_L1 + 0.2, T_L1 + 2.2),
            Clocked(self, flare, T_FLARE, T_FLARE + 0.6),
            timed(enter(lbl_pte), T_L1 + 2.45, T_L1 + 3.0),             # as the camera arrives
        )
        cloud.set_glows(0.0)

        # ============================================================ row 4: points open into glyphs ("post-training" .. "trained")
        self.at_word(1, "post-training")
        pick, glyphs = world.glyphs_in_place()                      # the storyboard's fallback (make_lens fails its check)
        order = np.argsort(home[pick, 0])                           # left to right
        pick, glyphs = pick[order], VGroup(*[glyphs[i] for i in order])
        xy = cloud.drawn_xy()
        for g, i in zip(glyphs, pick):
            g.shift(np.append(xy[i] - home[i, :2], 0.0))           # on the point as it is drawn now
            g[1].set_stroke(opacity=0.7)                            # the response stroke brightens on "taught"
        gap = np.linalg.norm(home[:, None, :2] - home[pick][None, :, :2], axis=2).min(axis=1)
        pocket = np.setdiff1d(np.nonzero(gap < 0.2)[0], pick)       # the points round each glyph step back
        assert not np.intersect1d(np.concatenate([pick, pocket]), gA).size
        t_open = [T_POST + 0.1 + 0.11 * k for k in range(8)]

        def rank_of(idx):                                           # sort keys for cloud.to: one per point of the cloud
            keys = np.zeros(cloud.n)
            keys[idx] = np.arange(len(idx))
            return keys

        self.play_until(
            cue(T_TRAINED),
            *[timed(born_from(np.append(xy[i], 0.0), g, run_time=0.6), t, t + 0.6) for g, i, t in zip(glyphs, pick, t_open)],
            timed(cloud.to(opacity=0.0, idx=pick, lag=0.56, order=rank_of(pick)), t_open[0], t_open[-1] + 0.6),
            timed(cloud.to(opacity=0.2 * alpha0[pocket], idx=pocket), T_POST, T_POST + 0.8),
        )

        # ============================================================ row 5: trained, taught ("trained" .. line 3)
        self.at_word(1, "trained")
        b = [T_TAUGHT + 0.11 * k for k in range(8)]                 # each response stroke brightens, left to right
        FLY = 0.75
        dep = [t + 0.2 for t in b]
        arr = [t + FLY for t in dep]
        rank_y = np.argsort(np.argsort(home[pick, 1]))              # the lowest glyph goes to the lowest rim point
        ang = np.radians(np.linspace(214.0, 146.0, 8))[rank_y]
        P0 = [g[1].get_center() for g in glyphs]
        P2 = [world.M_C + world.M_R * np.array([math.cos(a), math.sin(a), 0.0]) for a in ang]
        P1 = [(p + q) / 2 + 0.35 * UP for p, q in zip(P0, P2)]
        needle_xy = world.M_C + world.NEEDLE_POS
        needle = [int(np.argmin(np.linalg.norm(needle_xy - q, axis=1))) for q in P2]
        copies = VGroup(*[VMobject(stroke_color=DATA, stroke_width=W_LINE, stroke_opacity=0.0, fill_opacity=0.0)
                          .set_points_as_corners([p, p + 1e-3 * RIGHT]) for p in P0])
        GLINT = 0.45
        ABSORB_END = arr[-1] - 0.08 + GLINT + 0.02

        def absorb(t: float) -> None:                               # copies drift to the left rim; a needle glints
            bright = np.zeros(40)
            for k in range(8):
                s_ = (t - dep[k]) / FLY
                c = copies[k]
                if s_ <= 0.0 or s_ >= 1.0:
                    c.set_stroke(opacity=0.0)
                else:
                    e = MOVE(s_)
                    p = (1 - e) ** 2 * P0[k] + 2 * (1 - e) * e * P1[k] + e ** 2 * P2[k]
                    half = 0.135 * (1.0 - 0.55 * e)
                    c.set_points_as_corners([p - half * RIGHT, p + half * RIGHT])
                    c.set_stroke(opacity=0.5 * min(1.0, s_ / 0.1) * (1.0 - float(world.smoothstep(0.7, 1.0, s_))))
                u = (t - (arr[k] - 0.08)) / GLINT
                if 0.0 < u < 1.0:
                    bright[needle[k]] = max(bright[needle[k]], math.sin(math.pi * u))
            model.bright[:] = bright

        self.add(copies)
        self.play_until(
            cue(T_L2),
            timed(model.to_still(0.0, rate_func=held(0.12, 0.2)), T_TRAINED, T_TAUGHT + 0.25),   # 1 s of stillness
            *[timed(g[1].animate(rate_func=MOVE).set_stroke(DATA_HI, opacity=1.0), t, t + 0.45) for g, t in zip(glyphs, b)],
            Clocked(self, absorb, b[0], ABSORB_END, carrier=copies)   # crosses line 3,
        )

        # ============================================================ row 6: remove (line 3 .. "replace")
        self.at(2)
        xy = cloud.drawn_xy()
        back = np.concatenate([pick, pocket])
        self.play_until(
            cue(T_REPLACE),
            *[timed(FadeOut(g, target_position=np.append(xy[i], 0.0), scale=0.15), T_L2, T_L2 + 0.5)
              for g, i in zip(glyphs, pick)],                       # the glyphs close into their points
            timed(cloud.to(opacity=alpha0[back], idx=back), T_L2, T_L2 + 0.5),
            timed(leave(lbl_pte), T_L2, T_L2 + 0.5),
            Clocked(self, absorb, b[0], ABSORB_END, carrier=copies),   # the last glints finish
            timed(cloud.to(color=FOCUS, idx=gA), T_REMOVE, T_REMOVE + 0.4),
            timed(pool.remove_group("gA"), T_REMOVE + 0.45, T_REMOVE + 1.65),
        )
        self.remove(copies)
        model.bright[:] = 0.0

        # ============================================================ row 7: replace ("replace" .. line 4)
        self.at_word(2, "replace")
        rng = np.random.default_rng(101)
        starts = np.column_stack([-7.9 + rng.uniform(-0.5, 0.5, 40), -4.7 + rng.uniform(-0.5, 0.5, 40), np.zeros(40)])
        new = cloud.subset(gA)                                      # 40 different points: starlight core ...
        new.set_colors(DATA).set_opacities(alpha0[gA]).set_glows(0.0)
        halo = cloud.subset(gA)                                     # ... and a gold halo (one glow: one cloud)
        halo.set_colors(FOCUS).set_opacities(1.0).set_radii(0.001).set_glows(0.55)
        halo.glow_reach = 110.0
        for c in (new, halo):
            c.points = starts.copy()
        self.add(halo, new)
        ARC = -1.0                                                  # in from beyond the left edge, clear of the label slot
        self.play_until(
            cue(T_L3),
            *[timed(c.to(centers=home[gA], lag=0.45, order="random", seed=5, arc=ARC), T_REPLACE, T_REPLACE + 1.4)
              for c in (halo, new)],
        )

        # ============================================================ row 8: undo, outlines (line 4 .. "which")
        self.at(3)
        cloud.set_colors(DATA, gA)                                  # gA's own points (at 0, unseen) come back as starlight
        lbl_dc = world.label("data change")
        drawn = {n: pool.outline(n).copy().set_stroke(opacity=0.6) for n in G4}
        t_draw = {"gA": T_L3 + 0.3, "gB": T_L3 + 0.75, "gC": T_L3 + 1.05, "gD": T_L3 + 1.35}
        assert t_draw["gD"] + 0.6 <= T_WHICH - 2 * f1
        self.play_until(
            cue(T_WHICH),
            *[timed(c.to(centers=starts, opacity=0.0, lag=0.3, order="random", seed=5, arc=-ARC), T_L3, T_L3 + 1.0)
              for c in (halo, new)],                                # they leave the way they came
            timed(pool.restore("gA", lag=0.2), T_L3, T_L3 + 1.0),   # gA's own points come back from the upper left
            timed(enter(lbl_dc), T_CHANGE, T_CHANGE + 0.6),
            *[timed(Create(drawn[n], rate_func=MOVE), t_draw[n], t_draw[n] + 0.6) for n in G4],
        )
        self.remove(halo, new, *drawn.values())
        pool.set_outlines({n: 0.6 for n in G4})                     # the drawn copies become the pool's own outlines
        cloud.points[gA] = home[gA]                                 # the values the plays ended on, without float residue
        cloud.set_colors(DATA).set_opacities(alpha0).set_glows(0.0)

        # ============================================================ row 9: which one? ("which" .. end)
        self.at_word(3, "which")
        ring = ["gA", "gC", "gD", "gB", "gA"]                       # round the four, clockwise, and once more

        def round_and_round(t: float) -> None:
            vals = {n: 0.6 for n in G4}
            for j, n in enumerate(ring):
                u = (t - (T_WHICH + 0.35 * j)) / 0.5
                if 0.0 < u < 1.0:
                    vals[n] = max(vals[n], 0.6 + 0.4 * PULSE(u))
            pool.set_outlines(vals)

        loud = target.copy()
        red = [k for k in range(24) if k in world.RED_FIRST]
        loud[red, :3] = np.array(FAIL_HI.to_rgb())
        loud[red, 4] = 1.5
        self.play_until(
            END,
            Clocked(self, round_and_round, T_WHICH, T_WHICH + 0.35 * (len(ring) - 1) + 0.5),
            timed(world.Tween(test, "look", loud, rate_func=PULSE), T_HELP, T_HELP + 0.6),   # the nine, once, on "help"
        )


