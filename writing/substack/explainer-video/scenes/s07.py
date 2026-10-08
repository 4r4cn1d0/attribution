"""S07 How the choices are paired (storyboard section 5, S07). Opens in pose P06 and closes in pose P07.

Variance is defined on a moving picture (futures of the toy of 3.7, their comparisons as ticks on a strip, a band
round a fixed centre), then coupling is shown as a mechanism: one shared number through two bars that keep their
own widths; only the pairing changes, and the piles prove it.

How the code is laid out. Each beat row is ONE play (``play_until`` the next row's cue, ending one frame before it,
so that the next play's first change is on its cue). Inside a play, ``Seg`` windows (absolute scene times taken
from the word timings) change the state of the world objects; a window touches an attribute that no other window
of the same play touches at the same time. The motions that cross cues are clock-driven (``world.jitter``): the
stream of 36 futures, the pointer and hairline jumps, the landings of lines 5 and 6.

Two work-arounds for world.py (reported under needs_world_change):
- ghosts: ``Fork.set_ghosts`` replaces its Line objects; called inside a play the old Lines stay on screen until the
  play ends (Manim freezes the list of moving mobjects at play start), so ghosts would stack. All 22 ghost edges
  are made once, before the first play, and an extra updater on the fork sets each edge's visibility.
- the strip's centre line has no level of its own (it shares the strip's level with the axis): an updater on the
  strip multiplies it by ``self.cl`` so that the axis can arrive with the first tick and the centre line with the
  stream of line 2.
"""
# qa: bleed   (the open boundary of S05 to S09 crosses |x| = 6.4: rule 17 of 1.2)

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/

import numpy as np  # noqa: E402

from kit import *  # noqa: E402,F401,F403
import world  # noqa: E402
from world import PL, TOY, bar_x  # noqa: E402


def _sub(x, a, b):
    """Progress of x through [a, b], clipped to 0..1."""
    return min(max((x - a) / (b - a), 0.0), 1.0)


def _lerp(a, b, x):
    return np.asarray(a, dtype=float) + (np.asarray(b, dtype=float) - np.asarray(a, dtype=float)) * x


def _along(nodes, p):
    """The nodes of a path up to progress ``p`` (an index along the nodes, 1 = the event, 3 = step 2)."""
    i = int(math.floor(p + 1e-9))
    f = p - i
    out = [np.array(q, dtype=float) for q in nodes[:i + 1]]
    if f > 1e-6 and i + 1 < len(nodes):
        out.append(np.asarray(nodes[i], dtype=float) + (np.asarray(nodes[i + 1], dtype=float) - np.asarray(nodes[i], dtype=float)) * f)
    return out


def _ends(nA, nB):
    """The comparison of a future: (head of copy B, head of copy A) after step 2, canvas points."""
    return PL(nB[3][0], nB[3][1]), PL(nA[3][0], nA[3][1])


def _futures():
    """The 40 futures of 3.12 (seed 11), with the pointer places that drew them (the same four draws as world.TOY)."""
    rng = np.random.default_rng(world.SEEDS["futures"])
    hA0, hB0 = TOY.h_event["A"], TOY.h_event["B"]
    out = []
    for f in TOY.futures:
        u = rng.random(4)
        assert (TOY.seg(TOY.probs(hA0), u[0]), TOY.seg(TOY.probs(f["hA"][1]), u[2])) == tuple(f["a"]), "future draw A"
        assert (TOY.seg(TOY.probs(hB0), u[1]), TOY.seg(TOY.probs(f["hB"][1]), u[3])) == tuple(f["b"]), "future draw B"
        nA, nB = TOY.future_nodes(f, "A"), TOY.future_nodes(f, "B")
        out.append(dict(nA=nA, nB=nB, u1=(float(u[0]), float(u[1])), u2=(float(u[2]), float(u[3])),
                        w2=(TOY.probs(f["hA"][1]), TOY.probs(f["hB"][1])), D=f["D"], ends=_ends(nA, nB)))
    return out


FUT = _futures()
S06 = dict(nA=TOY.nodes("A"), nB=TOY.nodes("B"), u2=(0.24, 0.78), w2=(TOY.bars["A2"], TOY.bars["B2"]),
           ends=_ends(TOY.nodes("A"), TOY.nodes("B")))
W1 = (TOY.bars["A1"], TOY.bars["B1"])
W2 = (TOY.bars["A2"], TOY.bars["B2"])


def _edge_key(c, p, q):
    return c, round(float(p[0]), 6), round(float(p[1]), 6), round(float(q[1]), 6)


def _ghost_need():
    """For each edge of TOY.ghost_edges() (the P07 order): how many futures must be retired before it shows as a ghost
    (0: an edge of the future of P06, which is retired first)."""
    s06 = {_edge_key(*e) for e in TOY.ghost_edges([], True)}
    per = [{_edge_key(*e) for e in TOY.ghost_edges([f], False)} for f in TOY.futures]
    need = []
    for e in TOY.ghost_edges():
        k = _edge_key(*e)
        need.append(0 if k in s06 else next(j for j, s in enumerate(per) if k in s) + 1)
    return need


class Seg:
    """A window of a play: from scene time t0 to t1 it calls fn(ease(x)), x = 0..1; once more with x = 1 when a frame
    has passed t1; never before t0. Several windows on one attribute must not overlap in time."""

    def __init__(self, t0, t1, fn, ease=MOVE):
        self.t0, self.t1, self.fn, self.ease, self.done = float(t0), float(t1), fn, ease, False

    def __call__(self, t):
        if self.done or t < self.t0 - 1e-6:
            return
        x = 1.0 if self.t1 - self.t0 < 1e-9 else min(max((t - self.t0) / (self.t1 - self.t0), 0.0), 1.0)
        self.fn(float(self.ease(x)))
        if t >= self.t1 - 1e-6:
            self.done = True


class S07(Narrated):
    def build(self):
        w = world.pose("P06", self)
        fork, bars = w.fork, w.bars
        self.w, self.fork, self.bars = w, fork, bars
        fr = 1.0 / self.fps
        t_last = self.scene_duration - fr                       # the time of the last frame (pose P07)

        # ---- stage (nothing here changes the first frame: it must equal P06 to the pixel)
        self.holder = Mobject()
        self.add(self.holder)
        # The comparison segment: a copy of the fork's own, under the fork, so that it can jump on its own.
        cmp = fork.comparison.copy()
        fork.comp = 0.0
        self.mobjects.insert(self.mobjects.index(fork), cmp)
        self.cmp = cmp
        # Ghosts: all 22 edges of P07 at once, each shown only once its future is retired (self.g).
        fork.set_ghosts(TOY.ghost_edges())
        need = _ghost_need()
        self.g = -1

        def ghost_vis(m, dt=0.0):
            for k, ln in enumerate(m.ghosts):
                ln.set_stroke(opacity=m.ghost * m.level if need[k] <= self.g else 0.0)
        fork.add_updater(ghost_vis)
        fork.paint()
        ghost_vis(fork)
        # The strip: invisible until the first comparison flies to it.
        strip = world.Strip(half=0.001)
        strip.band_on, strip.level = 0.0, 0.0
        self.cl = 0.0                                           # the centre line's own factor
        strip.add_updater(lambda m, dt=0.0: m.centre.set_stroke(opacity=m.level * self.cl))
        strip.paint()
        strip.centre.set_stroke(opacity=0.0)
        self.mobjects.insert(self.mobjects.index(bars), strip)
        self.strip = strip
        # Passing marks of this scene (all invisible until used): four flying comparisons, the newest tick, the
        # shimmer on the centre line, four after-images of the link.
        def hair(width=W_LINE, color=INK_HI):
            return Line(PL(world.STRIP_X - 0.25, world.STRIP_CY), PL(world.STRIP_X + 0.25, world.STRIP_CY),
                        stroke_color=color, stroke_width=width, stroke_opacity=0.0)
        flyers = [hair(W_BOLD, INK) for _ in range(4)]
        newest = hair(W_BOLD)
        shimmer = hair(W_BOLD)
        after = [hair() for _ in range(4)]
        # The light of the estimate (a soft glow along the centre line) and the shimmer's own small light.
        cglow = glow_sprite(0.55, INK_HI, peak=0.45).stretch_to_fit_height(0.24).move_to(PL(world.STRIP_X, world.STRIP_CY))
        sglow = glow_sprite(0.16, INK_HI, peak=0.9).move_to(PL(world.STRIP_X, world.STRIP_CY))
        cglow.set_fill(opacity=0.0)
        sglow.set_fill(opacity=0.0)
        self.add(*flyers, newest, cglow, shimmer, sglow, *after)
        self.newest_y = world.STRIP_CY

        # ---- state helpers
        def show(nA=None, nB=None, wA=None, wB=None, pA=None, pB=None, ends=None, cop=None):
            if nA is not None:
                fork.set_nodes(nA, nB)
            if wA is not None:
                bars.widths["A"], bars.widths["B"] = np.asarray(wA, dtype=float), np.asarray(wB, dtype=float)
            if pA is not None:
                bars.ptr["A"], bars.ptr["B"] = [float(pA[0]), float(pA[1])], [float(pB[0]), float(pB[1])]
            bars.paint()
            if ends is not None and np.linalg.norm(ends[1] - ends[0]) > 1e-4:
                cmp.put_start_and_end_on(ends[0], ends[1])
            if cop is not None:
                cmp.set_stroke(opacity=cop)

        def future_fn(prev, f, i):
            """One future, slowly or fast: the old bright paths fall back to ghosts as the heads return to their
            places after the event, the bars go back to their step-1 widths; step 1 (pointers drop, heads move),
            the bars take this future's step-2 widths, step 2; then the comparison jumps to the new ends."""
            def fn(x):
                self.g = max(self.g, i)
                if x < 0.25:
                    s = MOVE(_sub(x, 0.0, 0.25))
                    nA, nB = _along(prev["nA"], 3 - 2 * s), _along(prev["nB"], 3 - 2 * s)
                elif x < 0.33:
                    nA, nB = _along(f["nA"], 1), _along(f["nB"], 1)
                elif x < 0.53:
                    s = MOVE(_sub(x, 0.33, 0.53))
                    nA, nB = _along(f["nA"], 1 + s), _along(f["nB"], 1 + s)
                elif x < 0.70:
                    nA, nB = _along(f["nA"], 2), _along(f["nB"], 2)
                elif x < 0.90:
                    s = MOVE(_sub(x, 0.70, 0.90))
                    nA, nB = _along(f["nA"], 2 + s), _along(f["nB"], 2 + s)
                else:
                    nA, nB = f["nA"], f["nB"]
                if x < 0.53:
                    s = MOVE(_sub(x, 0.04, 0.25))
                    wA, wB = _lerp(prev["w2"][0], W1[0], s), _lerp(prev["w2"][1], W1[1], s)
                else:
                    s = MOVE(_sub(x, 0.53, 0.62))
                    wA, wB = _lerp(W1[0], f["w2"][0], s), _lerp(W1[1], f["w2"][1], s)
                if x < 0.25:
                    sh = 1 - MOVE(_sub(x, 0.0, 0.12))
                    pA, pB = (prev["u2"][0], sh), (prev["u2"][1], sh)
                elif x < 0.62:
                    sh = ENTER(_sub(x, 0.25, 0.33)) * (1 - MOVE(_sub(x, 0.53, 0.58)))
                    pA, pB = (f["u1"][0], sh), (f["u1"][1], sh)
                else:
                    sh = ENTER(_sub(x, 0.62, 0.70))
                    pA, pB = (f["u2"][0], sh), (f["u2"][1], sh)
                if x < 0.90:
                    ends, cop = prev["ends"], 1 - 0.65 * MOVE(_sub(x, 0.0, 0.15))
                else:
                    ends, cop = f["ends"], 1.0
                show(nA, nB, wA, wB, pA, pB, ends, cop)
            return fn

        def flight_fn(j, f):
            """A copy of the comparison flies right, turns flat and lands as a tick of the strip (it adds 10% to a
            tick that is already there)."""
            fl = flyers[j]
            a, b = f["ends"]
            c0, L0 = (a + b) / 2, float(np.linalg.norm(b - a))
            ty = TOY.tick_y(f["D"])
            c1 = PL(world.STRIP_X, ty)
            ctrl = (c0 + c1) / 2 + 0.6 * UP
            state = {"landed": False}

            def fn(x):
                if state["landed"]:
                    return
                n = strip.counts.get(round(float(f["D"]), 9), 0) + 1
                op1 = min(0.3 + 0.1 * (n - 1), 0.7) * strip.tick_dim * max(strip.level, 1e-3)
                if x >= 1.0:
                    fl.set_stroke(opacity=0.0)
                    strip.add_tick(f["D"])
                    state["landed"] = True
                    return
                c = (1 - x) ** 2 * c0 + 2 * (1 - x) * x * ctrl + x ** 2 * c1
                ang = 0.5 * math.pi * (1 - x)
                L = L0 + (0.5 - L0) * x
                d = np.array([math.cos(ang), math.sin(ang), 0.0]) * L / 2
                fl.put_start_and_end_on(c - d, c + d)
                fl.set_stroke(mix(INK, INK_HI, x), width=W_BOLD + (W_LINE - W_BOLD) * x, opacity=1 + (op1 - 1) * x)
            return fn

        def paint_newest(op):
            newest.put_start_and_end_on(PL(world.STRIP_X - 0.25, self.newest_y), PL(world.STRIP_X + 0.25, self.newest_y))
            newest.set_stroke(opacity=op)
            self.newest_op = op
        self.newest_op = 0.0

        def tween(obj, attr, a, b):
            def fn(x):
                setattr(obj, attr, a + (b - a) * x)
                obj.paint()
            return fn

        def lit(c, seg, x=1.0):
            bars.lit[c] = np.zeros(3)
            if seg is not None:
                bars.lit[c][seg] = x

        def direct(*segs):
            """The windows of one play. At the play's end (alpha 1, after its last frame) every window is completed,
            so a window that ends between the last frame and the cue still lands exactly."""
            segs = list(segs)
            return UpdateFromAlphaFunc(self.holder, lambda m, a: [s(self._st() if a < 1 else math.inf) for s in segs],
                                       rate_func=CLOCK)

        def row(t_next, *anims):
            """One beat row: one play that ends one frame before the next cue."""
            self.play_until(t_next - fr, *anims)

        # ---- cues (scene seconds, from the word timings)
        L = self.line_start
        Wd = lambda i, word: self.word_span(i, word)[0]                     # noqa: E731
        c0, c_cmp, c1, c_fl = L(0), Wd(0, "comparison"), L(1), Wd(1, "fluctuates")
        e1, c_coord, c_est, c_prec = self.line_end(1), Wd(2, "coordinating"), Wd(2, "estimate"), Wd(2, "precise")
        c3, c_coup, c_estab = L(3), Wd(3, "coupling"), Wd(3, "established")
        c4, c_own, c_step, c5 = L(4), Wd(4, "own"), Wd(4, "step"), L(5)
        assert c_cmp - c0 >= 2.5 and c1 - c_cmp >= 1.6, "S07: line 1 is too short for one slow and three fast futures"
        assert e1 + 1.2 <= c_coord - 0.8, "S07: the rewind of line 3 must end 0.8 s before 'coordinating'"

        # ============================================================== line 1: "Because these futures ..."
        # Another future, slowly (1.5 s); its comparison jumps to the new ends; a copy flies to the strip.
        self.at(0)
        lab = w.labels
        bar_a, bar_b = world.label("copy A@bar"), world.label("copy B@bar")
        cmp_strip = world.label("the comparison@strip")
        f0 = FUT[0]
        row(c_cmp,
            direct(Seg(c0, c0 + 1.5, future_fn(S06, f0, 0), ease=CLOCK),
                   Seg(c0 + 1.3, c0 + 2.0, tween(strip, "level", 0.0, 1.0)),
                   Seg(c0 + 1.55, c0 + 2.35, flight_fn(0, f0))),
            timed(leave(lab["one event"], run_time=0.6), c0, c0 + 0.6),
            timed(hand_over(lab["copy A@column"], bar_a, run_time=1.0), c0 + 0.25, c0 + 1.25),
            timed(hand_over(lab["copy B@column"], bar_b, run_time=1.0), c0 + 0.35, c0 + 1.35),
            timed(hand_over(lab["the comparison@column"], cmp_strip, run_time=0.8), c0 + 1.55, c0 + 2.35))

        # "a comparison can be noisy.": three more futures at 0.45 s each, each with its tick.
        self.at_word(0, "comparison")
        segs = []
        prev = f0
        for j in (1, 2, 3):
            t0 = c_cmp + (j - 1) * 0.45
            segs.append(Seg(t0, t0 + 0.45, future_fn(prev, FUT[j], j), ease=CLOCK))
            segs.append(Seg(t0 + 0.42, t0 + 0.74, flight_fn(j, FUT[j])))
            prev = FUT[j]
        row(c1, direct(*segs))

        # ============================================================== line 2: "Variance measures ..."
        # The other 36 futures run as one clock-driven stream (seed 11) to the end of the line; the centre line comes
        # in under the ticks and the band grows out of it; `variance` is written on its word; the bars step back.
        self.at(1)
        rate = 36 / (e1 - c1)

        def stream(k):
            i = 4 + k
            f = FUT[i]
            self.g = i
            show(f["nA"], f["nB"], f["w2"][0], f["w2"][1], (f["u2"][0], 1.0), (f["u2"][1], 1.0), f["ends"], 1.0)
            strip.add_tick(f["D"])
            self.newest_y = TOY.tick_y(f["D"])
            paint_newest(self.newest_op)
        world.jitter(self, world.SEEDS["futures"], rate, c1, c1 + 35.5 / rate, stream)

        def centre_in(x):
            self.cl = x

        def band_in(x):
            strip.band_on = min(1.0, 4 * x)
            strip.half = max(TOY.half["none"] * x, 0.001)
            strip.paint()
        variance = world.label("variance")
        row(c_fl,
            direct(Seg(c1, c1 + 0.5, centre_in),
                   Seg(c1 + 0.2, c1 + 1.2, band_in),
                   Seg(c1, c1 + 0.6, tween(bars, "level", 1.0, 0.55))),
            timed(enter(variance, run_time=0.8), c1, c1 + 0.8))

        # "fluctuates between random runs.": the newest tick jumps (it does not glide); the comparison with it.
        self.at_word(1, "fluctuates")
        row(e1, direct(Seg(c_fl, c_fl + 0.2, lambda x: paint_newest(x))))

        # ============================================================== line 3 (rows 5 to 7)
        # The pause: the stream ends on the future of P06, lit again (no tick); the band breathes. Then time goes back
        # one step (heads to their places after the event, bars to step-1 widths) while the fork and the strip dim
        # and `the comparison` fades. Then the bars brighten and each pointer jumps on its own (seed 12, 5 a second).
        self.at_time(e1, "the end of line 1")

        def lit_again(x):
            self.g = 40
            show(S06["nA"], S06["nB"], W2[0], W2[1], (0.24, 1.0), (0.78, 1.0), S06["ends"], 1.0)

        def breathe(x):
            strip.band_on = 1 - 0.4 * PULSE(x)
            strip.paint()

        def back_one(x):
            s = x
            fork.level = 1 + (0.45 - 1) * s
            strip.level = 1 + (0.45 - 1) * s
            sh = 1 - MOVE(_sub(s, 0.0, 0.5))
            show(_along(S06["nA"], 3 - 2 * s), _along(S06["nB"], 3 - 2 * s), _lerp(W2[0], W1[0], s), _lerp(W2[1], W1[1], s),
                 (0.24, sh), (0.78, sh), None, 1 - s)
            strip.paint()

        t_back = e1 + 1.2

        def k_last(t0, t1, r):                                   # the last k that world.jitter applies
            return max(int(math.ceil((t1 - t0) * r - 1e-9)) - 1, -1)
        tA0, tB0 = t_back, t_back + 0.1                         # B jumps half a beat after A: each on its own
        kA, kB = k_last(tA0, c_coord, 5), k_last(tB0, c_coord, 5)
        assert kA >= 2 and kB >= 2, "S07: too little time for the pointers to jump on their own"
        # Both pointers draw from seed 12 (3.12); B reads its own run of draws, starting at the first offset from 500
        # whose last jump lands 0.3 or more from A's, so that the place where they meet is visibly a new one.
        off_b = 500
        while abs(float(world.rand(world.SEEDS["jumps"], kA)) - float(world.rand(world.SEEDS["jumps"], off_b + kB))) < 0.3:
            off_b += 1
        uA = lambda k: float(world.rand(world.SEEDS["jumps"], k))                     # noqa: E731
        uB = lambda k: float(world.rand(world.SEEDS["jumps"], off_b + k))             # noqa: E731
        world.jitter(self, world.SEEDS["jumps"], 5, tA0, c_coord, lambda k: bars.set_pointer("A", uA(k), 1.0))
        world.jitter(self, world.SEEDS["jumps"], 5, tB0, c_coord, lambda k: bars.set_pointer("B", uB(k), 1.0))
        row(c_coord,
            direct(Seg(e1, e1, lit_again, ease=CLOCK),
                   Seg(e1, e1 + 0.25, lambda x: paint_newest(1 - x)),
                   Seg(e1, e1 + 0.6, breathe, ease=CLOCK),
                   Seg(e1 + 0.4, t_back, back_one),
                   Seg(t_back, t_back + 0.6, tween(bars, "level", 0.55, 1.0))),
            timed(leave(cmp_strip, run_time=0.8), e1 + 0.4, t_back))

        # "coordinating the random choices ...": the two pointers slide to one new place between them (neither copy's
        # old place) and join into one white hairline through both bars (0.8 s); it then jumps 4 times a second (seed
        # 12) until "own"; under it each bar lights the segment that it lands in.
        self.at_word(2, "coordinating")
        ua0, ub0 = uA(kA), uB(kB)
        u_join = (ua0 + ub0) / 2                                 # between them, 0.15 or more from each old place
        assert min(abs(u_join - ua0), abs(u_join - ub0)) >= 0.15

        def join(x):
            ua, ub = ua0 + (u_join - ua0) * x, ub0 + (u_join - ub0) * x
            tie = ENTER(_sub(x, 0.55, 1.0))
            bars.ptr["A"], bars.ptr["B"] = [ua, 1 - tie], [ub, 1 - tie]
            bars.link = [u_join, u_join, tie]
            lit("A", TOY.seg(W1[0], u_join), tie)
            lit("B", TOY.seg(W1[1], u_join), tie)
            bars.paint()

        def hairline(k):
            u = float(world.rand(world.SEEDS["jumps"], 1000 + k))
            bars.link = [u, u, 1.0]
            lit("A", TOY.seg(W1[0], u))
            lit("B", TOY.seg(W1[1], u))
            bars.paint()
        world.jitter(self, world.SEEDS["jumps"], 4, c_coord + 0.8 + 0.25, c_own, hairline)
        row(c_est, direct(Seg(c_coord, c_coord + 0.8, join)))

        # "the estimate more precise.": the strip returns to 100% and its centre line brightens; on "precise" a
        # shimmer runs along the centre line from left to right. The band does not change.
        self.at_word(2, "estimate")

        def centre_light(x):                                     # the centre line brightens (and, row 8, rests)
            strip.centre_hi = x
            strip.paint()
            cglow.set_fill(opacity=x)

        def shimmer_fn(x):
            xc = world.STRIP_X - 0.45 + 0.11 + 0.68 * x
            shimmer.put_start_and_end_on(PL(xc - 0.11, world.STRIP_CY), PL(xc + 0.11, world.STRIP_CY))
            shimmer.set_stroke(opacity=0.9 * math.sin(math.pi * x))
            sglow.move_to(PL(xc, world.STRIP_CY)).set_fill(opacity=math.sin(math.pi * x))
        row(c3, direct(Seg(c_est, c_est + 0.6, tween(strip, "level", 0.45, 1.0)),
                       Seg(c_est + 0.2, c_est + 0.8, centre_light),
                       Seg(c_prec, c_prec + 0.8, shimmer_fn, ease=CLOCK)))

        # ============================================================== line 4: "This is called coupling, ..."
        self.at(3)
        coupling = world.label("coupling")
        row(c_estab,
            direct(Seg(c3, c3 + 1.0, lambda x: centre_light(1 - x))),
            timed(enter(coupling, run_time=0.8), c_coup, min(c_coup + 0.8, c_estab - fr)))

        self.at_word(3, "established")
        cite = self.hud_cite(world.CITATION)
        row(c4, direct(), timed(FadeIn(cite, rate_func=ENTER, run_time=0.6), c_estab, c_estab + 0.6))

        # ============================================================== line 5: "Each copy still has to follow ..."
        # Bar A's outline flashes blue, then bar B's violet.
        self.at(4)

        def flash(c):
            def fn(x):
                bars.flash[c] = math.sin(math.pi * x)
                bars.paint()
            return fn
        row(c_own, direct(Seg(c4 + 0.05, c4 + 0.65, flash("A"), ease=CLOCK),
                          Seg(c4 + 0.75, c4 + 1.35, flash("B"), ease=CLOCK)))

        # "its own probabilities at every step.": 30 stratified landings (seed 17) leave a dot over the chosen
        # segment of each bar; piles end at 15, 4, 11 and 9, 3, 18. On "step" the bars take their step-2 widths while
        # the dim heads glide on along their own step-1 paths; the piles clear; the citation fades. No place flashes.
        self.at_word(4, "own")
        r5 = 30 / (c_step - c_own)

        def land5(k):
            form, kk = TOY.line5[k]
            ua, ub = TOY.landing(form, kk)
            bars.link = [ua, ub, 1.0]
            sa, sb = TOY.seg(W1[0], ua), TOY.seg(W1[1], ub)
            lit("A", sa)
            lit("B", sb)
            bars.counts["A"][sa] += 1
            bars.counts["B"][sb] += 1
            bars.paint()
        world.jitter(self, world.SEEDS["piles"], r5, c_own, c_own + 29.5 / r5, land5)
        ua5, ub5 = TOY.landing(*TOY.line5[29])
        la5, lb5 = TOY.seg(W1[0], ua5), TOY.seg(W1[1], ub5)

        def step_on(x):
            fork.set_nodes(_along(S06["nA"], 1 + x), _along(S06["nB"], 1 + x))
            bars.widths["A"], bars.widths["B"] = _lerp(W1[0], W2[0], x), _lerp(W1[1], W2[1], x)
            bars.pile_level = 1 - MOVE(_sub(x, 0.0, 0.6))
            lit("A", la5, 1 - x)
            lit("B", lb5, 1 - x)
            bars.paint()
        row(c5, direct(Seg(c_step, c_step + 0.6, step_on)), timed(leave(cite, run_time=0.6), c_step, c_step + 0.6))
        assert tuple(bars.counts["A"]) == (15, 4, 11) and tuple(bars.counts["B"]) == (9, 3, 18), bars.counts
        bars.counts = {"A": [0, 0, 0], "B": [0, 0, 0]}
        bars.pile_level = 1.0
        bars.paint()

        # ============================================================== line 6: "We change how the choices are paired."
        # Ticks dim to a third and the band's edges leave a ghost at 30% (runs with no coordination). The link takes
        # two forms with fading after-images: straight, crossed, straight (ten stratified landings each, seed 17);
        # the bars do not change; the piles end at 14, 8, 8 and 10, 4, 16; the band answers each form by its computed
        # amount; the centre line does not move. Then the link settles at 0.46 and its segments light. In the last
        # 0.8 s the ghost edges fade to 0. Nothing brightens.
        self.at(5)
        top, bot = bars.ends("A")[1], bars.ends("B")[1]
        trail = []                                             # (uA, uB, time) of the landings of this line

        def land6(k):
            form, kk = TOY.line6[k]
            ua, ub = TOY.landing(form, kk)
            bars.link = [ua, ub, 1.0]
            sa, sb = TOY.seg(W2[0], ua), TOY.seg(W2[1], ub)
            lit("A", sa)
            lit("B", sb)
            bars.counts["A"][sa] += 1
            bars.counts["B"][sb] += 1
            bars.paint()
            trail.append((ua, ub, self._st()))
        blocks = [(c5 + 0.4, c5 + 1.3), (c5 + 1.3, c5 + 2.3), (c5 + 2.3, c5 + 2.9)]
        for b, (t0, t1) in enumerate(blocks):
            r = 10 / (t1 - t0)
            world.jitter(self, world.SEEDS["piles"], r, t0, t0 + 9.5 / r, (lambda b0: lambda k: land6(b0 + k))(10 * b))

        def afterimages(x):
            t = self._st()
            fade = 1 - _sub(t, c5 + 2.9, c5 + 3.3)
            for j, ln in enumerate(after):
                if len(trail) >= j + 2:
                    ua, ub, tl = trail[-(j + 2)]
                    age = t - trail[-(j + 1)][2]
                    op = 0.4 * (1 - j / 4) * max(0.0, 1 - age / 0.45) * fade
                    ln.put_start_and_end_on(PL(bar_x(ua), top), PL(bar_x(ub), bot))
                    ln.set_stroke(opacity=op)
                else:
                    ln.set_stroke(opacity=0.0)

        def band_to(a, b):
            def fn(x):
                strip.half = a + (b - a) * x
                strip.paint()
            return fn

        def dim_ticks(x):
            strip.tick_dim = 1 + (1 / 3 - 1) * x
            strip.ghost = x
            strip.paint()

        ua6, ub6 = TOY.landing(*TOY.line6[29])

        def settle(x):
            ua, ub = ua6 + (TOY.final_link - ua6) * x, ub6 + (TOY.final_link - ub6) * x
            bars.link = [ua, ub, 1.0]
            lit("A", TOY.seg(W2[0], ua))
            lit("B", TOY.seg(W2[1], ub))
            if x >= 1.0:
                bars.link = [TOY.final_link, TOY.final_link, 1.0]
                bars.ptr = {"A": [0.24, 0.0], "B": [0.78, 0.0]}
            bars.paint()

        def ghost_out(x):
            strip.ghost = 1 - x
            strip.paint()
        H = TOY.half
        self.play_until(self.scene_duration,                  # the last play renders the last frame (pose P07)
            direct(Seg(c5, c5 + 0.4, dim_ticks),
                   Seg(c5 + 0.5, c5 + 1.0, band_to(H["none"], H["straight"])),
                   Seg(c5 + 1.4, c5 + 1.9, band_to(H["straight"], H["crossed"])),
                   Seg(c5 + 2.4, c5 + 2.9, band_to(H["crossed"], H["straight"])),
                   Seg(c5, t_last, afterimages, ease=CLOCK),
                   Seg(c5 + 2.9, c5 + 3.3, settle),
                   Seg(t_last - 0.8, t_last, ghost_out)))
        assert tuple(bars.counts["A"]) == (14, 8, 8) and tuple(bars.counts["B"]) == (10, 4, 16), bars.counts

    def _st(self) -> float:
        """The scene time of the frame that is painted now (the film clock less the scene's film start)."""
        return film_time() - self.film_start
