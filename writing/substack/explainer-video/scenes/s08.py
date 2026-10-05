"""S08 The condition (storyboard section 5, S08). From pose P07 to pose P08, camera at P throughout.

Let the toy go (a bake that fades in place), bloom the 1,440 from their own centre, name what was compared (six
identical baseline glyphs and the oracle's glyph, all born from the field), then park the field and draw the
condition line, the faint longer-horizon fork, `≥20%`, the scale (the six merge into the zero tick, the oracle's glyph
becomes the white marker) and the target family's outline. Coordinates are P-local (world.PL).
"""
# qa: bleed   (the open boundary of S05 to S09 crosses |x| = 6.4: rule 17 of 1.2)

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kit import *  # noqa: E402,F401,F403
from manim.utils.paths import path_along_arc  # noqa: E402

import world  # noqa: E402
from world import PL, Tween  # noqa: E402

FIELD_C = PL(1.2, -0.2)                                   # the field's own centre (main): the seed of the bloom
ROW_X = (-5.9, -5.1, -4.3, -3.5, -2.7, -1.9)              # the six baseline glyphs, at y = -0.9
ROW_Y = -0.9
ORACLE_AT = PL(-3.9, -1.75)
ZERO_TOP, ZERO_BOT = -1.0, -2.75                          # the zero tick
SHIMMER_ORDER = (0, 4, 2, 5, 1, 3)                        # phases out of order along the row: no wave travels, none leads
FLICKER_SEED = 53                                         # the oracle's flicker (not in 3.12: it never crosses a scene)


def _smooth01(x):
    x = min(max(float(x), 0.0), 1.0)
    return x * x * (3 - 2 * x)


def _arc(a, b, s, angle):
    if abs(angle) < 1e-6:
        return a + (b - a) * s
    return path_along_arc(angle)(a[None, :], b[None, :], s)[0]


class _Glyph(world.Lasting):
    """A pairing glyph of 3.6 (world.PairingGlyph) driven by state numbers, so its flights are Tweens.

    mode "emerge": out of ``src`` (the field's centre) on an arc to ``dst``, growing from 0.15 and fading in.
    mode "merge":  slides to ``dst`` (a sixth of the zero tick) and flattens into it (width to 5%), fading at the end.
    mode "marker": flies on an arc to ``dst`` (the zero tick on track 1) and shrinks to the marker's size, fading.
    ``flick`` = (link opacity, link width, link x offset) for the oracle's flicker. Baseline glyphs shimmer faintly
    (link opacity, each in its own phase)."""

    idle = True

    def __init__(self, oracle: bool = False, phase: float = 0.0):
        super().__init__()
        self.g = world.PairingGlyph(oracle)
        self.add(self.g)
        self.link = self.g[0]
        self.rails = [self.g[1], self.g[2]]
        c = self.g.get_center()
        self.parts = [self.link, *self.rails]
        self.orig = [m.points.copy() - c for m in self.parts]
        self.src = FIELD_C.copy()
        self.dst = FIELD_C.copy()
        self.arc = 0.0
        self.mode = "emerge"
        self.s = 0.0
        self.squash_y = 1.0
        self.flick = np.array([1.0, 1.0, 0.0])
        self.phase = float(phase)
        self.shimmer = 0.0 if oracle else 1.0
        self.paint()

    def state(self):
        s = float(self.s)
        if self.mode == "emerge":
            k = 0.15 + 0.85 * s
            return _arc(self.src, self.dst, s, self.arc), k, k, _smooth01(s / 0.3)
        if self.mode == "merge":                     # keeps its shape for the first third of the slide, then flattens
            f = _smooth01((s - 0.35) / 0.65)
            return (self.src + (self.dst - self.src) * s, 1.0 - 0.95 * f, 1.0 + (self.squash_y - 1.0) * f,
                    1.0 - _smooth01((s - 0.78) / 0.22))
        k = 1.0 - 0.8 * s                                   # "marker"
        return _arc(self.src, self.dst, s, self.arc), k, k, 1.0 - _smooth01((s - 0.55) / 0.4)

    def paint(self):
        pos, sx, sy, alpha = self.state()
        op, fw, dx = (float(v) for v in self.flick)
        for m, o in zip(self.parts, self.orig):
            if m is self.link:
                m.points = pos + np.array([dx * sx, 0.0, 0.0]) + o * np.array([sx * fw, sy, 1.0])
            else:
                m.points = pos + o * np.array([sx, sy, 1.0])
        lv = self.level * alpha
        shim = 1.0 - 0.55 * self.shimmer * idle_gain() * (0.5 + 0.5 * math.sin(TAU * film_time() / 1.2 + self.phase))
        for r in self.rails:
            r.set_stroke(opacity=lv)
        self.link.set_fill(opacity=lv * op * shim)
        return self


class S08(Narrated):
    def build(self):
        w = world.pose("P07", self)
        f1 = 1.0 / self.fps
        ws = self.word_span
        now = lambda: world._scene_time(self)                        # noqa: E731  (scene time of the frame painted now)

        tick = Mobject()                                             # the handle of the clock-driven functions
        self.add(tick)

        def clock(fn):
            """An animation over the whole play that calls fn(t) with the scene time of every frame. Put it LAST in a
            play when it overrides what another animation of the same play sets."""
            return UpdateFromAlphaFunc(tick, lambda m, a: fn(now()), rate_func=linear, suspend_mobject_updating=False)

        def row(t_next, *anims):
            """One beat row = one play, ending one frame before the next row's cue (as at() does)."""
            self.play_until(t_next - f1, *anims)

        # ---------------------------------------------------------------- made now, all invisible
        art = [w.strip, w.bars, w.fork]
        w.fork.clear_updaters()                     # the toy rests in its pose until it is baked away (no breathing pop)
        baked = bake(self, art)                     # the S07 picture as the camera sees it now (the pose, idle at rest)
        baked.set_fill(opacity=0.0)
        self.add(baked)

        field = world.Field(park=0.0, units=0.6)
        field_rgba = field.cloud.rgbas.copy()
        field_pts = field.cloud.points.copy()
        field.cloud.points[:] = FIELD_C
        field.cloud.set_opacities(0.0)
        ruler = world.Ruler()
        ruler.track[:] = 0.0
        ruler.shown[:] = 0.0
        ruler.cond_drawn = 0.0
        ruler.zero_on = 0.0
        hz_alpha = [h.rgbas[:, 3].copy() for h in ruler.horizon]
        hz_x = [h.points[:, 0].copy() for h in ruler.horizon]
        for h in ruler.horizon:
            h.set_opacities(0.0)
        ruler.paint()
        seed = glow_sprite(0.32, GREY_1, peak=0.7).move_to(FIELD_C).set_fill(opacity=0.0)
        self.add(field, ruler, seed)

        lab = {k: world.label(k) for k in ("1,440", "toy configurations", "one- or two-step", "six baselines", "oracle",
                                           "≥20%", "variance reduction", "best baseline", "target family")}
        steps = world.step_glyphs()                 # 3.6 places them by estimate; the real label is wider, so each
        sl = lab["one- or two-step"]                 # glyph sits 0.2 from it (a label's own gap, rule 12 of 1.2)
        steps[0].shift(RIGHT * (sl.get_left()[0] - 0.2 - steps[0].get_right()[0]))
        steps[1].shift(RIGHT * (sl.get_right()[0] + 0.2 - steps[1].get_left()[0]))

        # ---------------------------------------------------------------- line 1: "We checked 1,440 ..."
        t_num0, t_num1 = ws(0, "1,440")
        t_gone = t_num0                              # the bake is gone as "1,440" starts (0.6 s fade, backwards)
        t_bake = t_gone - 0.6
        t_bloom0, t_bloom1 = t_gone + 0.3, t_num1    # a 0.3 s beat, then the bloom ends as the word ends
        old = [w.labels[k] for k in ("copy A@bar", "copy B@bar", "variance", "coupling")]
        hidden = [False]

        def dissolve(t):
            if t >= t_bake and not hidden[0]:
                for m in art:
                    for p in m.get_family():
                        p.fx_hidden = True
                hidden[0] = True
            baked.set_fill(opacity=0.0 if t < t_bake else 1.0 - _smooth01((t - t_bake) / (t_gone - t_bake)))

        T = t_bloom1 - t_bloom0                      # three units slowly, then a dozen, then all the others
        starts, spans = np.zeros(world.FIELD_N), np.zeros(world.FIELD_N)
        starts[:3], spans[:3] = [0.0, 0.17, 0.31], [0.6, 0.45, 0.45]
        starts[3:15] = np.linspace(0.42, 0.62, 12)
        spans[3:15] = 0.32
        m = world.FIELD_N - 15
        t_rest0, t_rest1 = 0.64, T - 0.28
        starts[15:] = t_rest0 + (t_rest1 - t_rest0) * np.sqrt(np.arange(m) / (m - 1))
        spans[15:] = 0.28
        spans = np.minimum(spans, T - starts)
        rank = np.empty(world.FIELD_N, dtype=int)
        rank[world.BLOOM_ORDER] = np.arange(world.FIELD_N)  # unit i blooms as the rank[i]-th of the seed order
        bloom = field.cloud.to(centers=field_pts, opacity=field_rgba[:, 3], delays=starts[rank] / T, span=spans[rank] / T,
                               ease="enter", flash=0.25, pop=0.3, start_alpha=np.zeros(world.FIELD_N), run_time=T)

        def seed_light(t):
            on = _smooth01((t - t_bloom0) / 0.15)
            off = 1.0 - _smooth01((t - (t_bloom0 + 0.45)) / (t_bloom1 - t_bloom0 - 0.45))
            seed.set_fill(opacity=on * off)

        self.at(0, lead=0.4)
        row(ws(0, "toy")[0],
            *[timed(FadeOut(o, rate_func=MOVE), 0.0, 0.3) for o in old],
            clock(dissolve),
            timed(bloom, t_bloom0, t_bloom1),
            clock(seed_light),
            timed(FadeIn(lab["1,440"], scale=0.92, rate_func=MOVE), t_num1 - 0.6, t_num1))
        self.remove(baked, *art, seed)

        # "toy configurations": the units breathe (their own idle twinkle); the name lands on its word
        self.at_word(0, "toy")
        t = ws(0, "toy")[0]
        row(ws(0, "one-")[0], timed(enter(lab["toy configurations"]), t, t + 0.6))

        # "with one- or two-step continuations." and the pause: the label, the two step glyphs, then all fade
        self.at_word(0, "one-")
        t1 = ws(0, "one-")[0]
        t2 = ws(0, "two-step")[0]
        t_fade0, t_fade1 = self.line_end(0), self.line_start(1) - f1

        def draw_glyph(g, t0):
            ring, path, head = g
            return [timed(Create(ring, rate_func=MOVE), t0, t0 + 0.3), timed(Create(path, rate_func=linear), t0 + 0.25, t0 + 0.6),
                    timed(FadeIn(head, rate_func=ENTER), t0 + 0.55, t0 + 0.8)]

        step_lab = lab["one- or two-step"]

        def fade_steps(t):                          # last in the play, so it wins over the entrances' end states
            if t < t_fade0:
                return
            x = 1.0 - _smooth01((t - t_fade0) / (t_fade1 - t_fade0))
            step_lab.set_opacity(x)
            for ring, path, head in steps:
                ring.set_stroke(opacity=x)
                path.set_stroke(opacity=x)
                head.set_fill(opacity=x)

        row(self.line_start(1),
            timed(enter(step_lab), t1, t1 + 0.6),
            *draw_glyph(steps[0], t1), *draw_glyph(steps[1], t2),
            clock(fade_steps))
        self.remove(lab["one- or two-step"], steps, *steps[0], *steps[1])

        # ---------------------------------------------------------------- line 2: "We compared six baseline pairing ..."
        glyphs = [_Glyph(False, phase=TAU * q / 6) for q in SHIMMER_ORDER]
        for j, g in enumerate(glyphs):
            g.src, g.dst, g.arc = FIELD_C.copy(), PL(ROW_X[j], ROW_Y), -0.5
            g.paint()
        oracle = _Glyph(True)
        oracle.src, oracle.dst, oracle.arc = FIELD_C.copy(), ORACLE_AT.copy(), -1.1   # comes in from below its label
        oracle.paint()
        self.add(*glyphs, oracle)

        self.at(1)
        t = self.line_start(1)
        d = 1.4 / (1 + 5 * 0.15)                     # 1.4 s with lag_ratio 0.15: each flight 0.8 s, 0.12 s apart
        flights = [timed(Tween(g, "s", 1.0, rate_func=MOVE), t + k * 0.15 * d, t + k * 0.15 * d + d)
                   for k, g in enumerate(glyphs)]    # the farthest first, so no glyph overtakes another
        t_six = t + 5 * 0.15 * d + d                 # the last glyph lands
        row(ws(1, "oracle")[0], *flights, timed(enter(lab["six baselines"]), t_six - 0.6, t_six))

        # "an oracle that could find the": a seventh glyph, a little larger, out of the field's centre
        self.at_word(1, "oracle")
        t = ws(1, "oracle")[0]
        row(ws(1, "best")[0], timed(Tween(oracle, "s", 1.0, rate_func=MOVE), t, t + 0.8),
            timed(enter(lab["oracle"]), t + 0.6, t + 1.15))

        # "the best allowed pairing": the oracle's soft link flickers (12 a second, 1.1 s), then holds still
        self.at_word(1, "best")
        t_fl = ws(1, "best")[0]

        def flicker(t):
            if t < t_fl or t >= t_fl + 1.1:
                oracle.flick = np.array([1.0, 1.0, 0.0])
            else:
                r = world.rand(FLICKER_SEED, int((t - t_fl) * 12), 3)
                oracle.flick = np.array([0.3 + 0.7 * r[0], 0.55 + 0.7 * r[1], 0.07 * (2 * r[2] - 1)])
            oracle.paint()

        row(ws(1, "tiny")[0], clock(flicker))

        # "tiny setup." and the pause: a soft band of light sweeps the field, left to right (1.1 s)
        self.at_word(1, "tiny")
        t_sw = ws(1, "tiny")[0]
        xs = field.cloud.points[:, 0].copy()
        x_lo, x_hi, half = xs.min(), xs.max(), 0.45

        def sweep(t):
            u = (t - t_sw) / 1.1
            if u <= 0 or u >= 1:
                field.paint()
                return
            xf = x_lo - 2 * half + (x_hi - x_lo + 4 * half) * u
            gain = np.exp(-(((xs - xf) / half) ** 2))
            field.cloud.rgbas[:, 3] = 0.6 + 0.4 * gain

        row(self.line_start(2), clock(sweep))
        field.paint()

        # ---------------------------------------------------------------- line 3: "The condition for advancing ..."
        # In one play: the count and its name fade and the line draws on "condition" (the tag goes off as it draws);
        # then the field parks (1.4 s) through "for advancing to the planned", ending as the row ends.
        self.at(2)
        t = self.line_start(2)
        t_next = ws(2, "longer-horizon")[0]
        row(t_next,
            timed(FadeOut(lab["1,440"], rate_func=MOVE), t, t + 0.6),
            timed(FadeOut(lab["toy configurations"], rate_func=MOVE), t, t + 0.6),
            timed(Tween(ruler, "cond_drawn", 1.0, rate_func=MOVE), t, t + 1.0),
            timed(FadeOut(w.tag, rate_func=MOVE), t, t + 1.0),        # tag off as the line draws
            timed(field.to_park(1.0, rate_func=MOVE), t_next - f1 - 1.4, t_next - f1))
        self.remove(lab["1,440"], lab["toy configurations"])

        # "longer-horizon test:": the faint dotted fork draws itself from the line's top end (16%; 1.6 s, steady)
        self.at_word(2, "longer-horizon")
        t_hz = ws(2, "longer-horizon")[0]
        hz_x0, hz_x1, soft = world.COND_X, 6.2, 0.08

        def horizon(t):
            u = min(max((t - t_hz) / 1.6, 0.0), 1.0)
            xf = hz_x0 + (hz_x1 - hz_x0 + soft) * u
            for h, a, x in zip(ruler.horizon, hz_alpha, hz_x):
                h.rgbas[:, 3] = a * np.clip((xf - x) / soft, 0.0, 1.0) if u < 1 else a

        row(ws(2, "20%")[0], clock(horizon))
        for h, a in zip(ruler.horizon, hz_alpha):
            h.rgbas[:, 3] = a

        # "20%": the line's label lands whole, one token whose sign carries "at least"
        self.at_word(2, "20%")
        t = ws(2, "20%")[0]
        row(ws(2, "reduction")[0], timed(FadeIn(lab["≥20%"], scale=0.92, rate_func=ENTER), t, t + 0.6))

        # "reduction in variance against the best": the six slide down together and merge into the zero tick;
        # track 1 draws from the zero tick to the line (1.2 s, linear); the scale's name lands when the glyphs are gone
        seg = (ZERO_TOP - ZERO_BOT) / 6
        for j, g in enumerate(glyphs):              # leftmost to the bottom sixth, rightmost to the top one
            g.mode, g.src, g.s = "merge", g.dst.copy(), 0.0
            g.dst = PL(world.ZERO_X, ZERO_BOT + seg * (j + 0.5))
            g.squash_y = seg / 0.25
            g.paint()
        self.at_word(2, "reduction")
        t = ws(2, "reduction")[0]
        row(ws(2, "baseline")[0],
            *[timed(Tween(g, "s", 1.0, rate_func=MOVE), t, t + 0.8) for g in glyphs],
            timed(Tween(ruler, "zero_on", 1.0, rate_func=MOVE), t + 0.5, t + 0.8),
            timed(ruler.to_track(0, 1.0), t, t + 1.2),
            timed(FadeOut(lab["six baselines"], rate_func=MOVE), t, t + 0.6),
            timed(enter(lab["variance reduction"]), t + 0.8, t + 1.4))
        self.remove(*glyphs, lab["six baselines"])

        # "baseline,": the zero tick flashes; the oracle's glyph flies to it and becomes the white marker
        oracle.mode, oracle.src, oracle.s = "marker", ORACLE_AT.copy(), 0.0
        oracle.dst, oracle.arc = PL(world.ZERO_X, world.TRACK_Y[0]), 0.6
        oracle.paint()
        self.at_word(2, "baseline")
        t = ws(2, "baseline")[0]
        row(ws(2, "one")[0],
            timed(Tween(ruler, "zero_flash", 1.0, rate_func=PULSE), t, t + 0.6),
            timed(Tween(oracle, "s", 1.0, rate_func=MOVE), t, t + 0.8),
            timed(Tween(ruler, "shown", np.array([1.0, 0.0]), rate_func=MOVE), t + 0.45, t + 0.8),
            timed(FadeOut(lab["oracle"], rate_func=MOVE), t, t + 0.6),
            timed(enter(lab["best baseline"]), t + 0.8, t + 1.4))
        self.remove(oracle, lab["oracle"])

        # "in at least one configuration from our chosen target": a faint hollow grey halo hops among the units of
        # the target family, 5 a second (seed 29), until "family". No unit lights.
        t_one, t_fam = ws(2, "one")[0], ws(2, "family")[0]
        halo = Circle(radius=0.15, stroke_color=GREY_1, stroke_width=W_LINE, stroke_opacity=0.0, fill_opacity=0.0)
        fam = world.FAMILY
        halo.move_to(world.field_pos(int(fam[int(world.rand(world.SEEDS["halo"], 0) * len(fam))]), 1.0))
        self.add(halo)

        def hop(k):
            i = int(fam[int(world.rand(world.SEEDS["halo"], k) * len(fam))])
            halo.move_to(world.field_pos(i, 1.0))

        self.at_word(2, "one")
        world.jitter(self, world.SEEDS["halo"], 5.0, t_one, t_fam, hop)
        # its opacity only, from the clock: a Transform here would put it back at its first place on every frame
        row(t_fam, clock(lambda t: halo.set_stroke(opacity=0.5 * _smooth01((t - t_one) / 0.3))))

        # "family." and the pause: a soft white outline closes round the target family (1.2 s); the halo fades
        self.at_word(2, "family")
        t = t_fam
        ring = field.family_outline.copy().set_stroke(INK, W_LINE, opacity=0.55)
        t_end = min(t + 1.2, self.scene_duration - 0.2)
        self.play_until(self.scene_duration - 0.2,
                        timed(Create(ring, rate_func=MOVE), t, t_end),
                        clock(lambda u: halo.set_stroke(opacity=0.5 * (1.0 - _smooth01((u - t) / 0.6)))),
                        timed(enter(lab["target family"]), t + 0.4, t + 1.0))
        self.remove(ring, halo)
        field.set_family(1.0)
        field.set_park(1.0)
