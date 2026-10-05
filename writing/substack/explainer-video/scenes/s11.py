"""S11 I would rather know (storyboard section 5, S11). Opening pose P10, closing pose P11, then the fade.

Rows of the beat table, one play each (rule 3 of 1.2). Every play ends one frame before the next row's cue, so the
next play's first change is on its cue.

  at(0)                      the question returns from 35% to 100%, left to right: pool, model, lights, floor (one
                             2.0 s stagger with lag_ratio 0.3, fitted to the row); on "recommendation" the outlines of
                             gA and gD brighten to 100% and take their gold tint at 12% (0.6 s)
  at_word(0, "trustworthy")  two dashed gold beams run from gA and gD through the model's core (model.between: above
                             the core disc, under the needles) to its right rim (1.2 s each, 0.3 s apart); the dashed
                             hairline at y = -0.2 draws (window 0.9 to 1.5 s)
  at(1)                      each range is born from its beam: its first dot slides from the beam's end to the range's
                             left end (0 to 0.3 s), then the dotted range grows to the right with its caps (0.3 to 1.9
                             s); the beams settle to 30% (1.0 s); then the ranges breathe (centres +-0.06, slowly)
  at_word(1, "weak")         the stretch where the ranges overlap brightens: a soft gold column over both rows (0.6 s);
                             on "changes" gA and then gD pulse (their tint, 0.5 s each)
  at(2)                      from "rather" the breathing slows to stillness (1.5 s, ease-out); on "know" the column
                             brightens once and settles (0.8 s); nothing new after it
  at_word(2, "ranking")      each range folds into one crisp white tick at its centre (0.5 s snap); the column goes
  at_word(2, "no")           the hairline fades (0.6 s); from "reliable" the ticks swap places three times, 0.3 s apart
  line_end(2)                the ticks melt back into the two dotted ranges and the hairline returns (0.8 s); the
                             ranges breathe very slowly; from 0.8 s in the sign-off writes, two lines (1.4 s); hold;
                             in the last 0.8 s everything fades to the background

The passing objects of this scene (beams, hairline, ranges, ticks, column) are set by one function of the scene time,
``state(t)``, that runs in every play (``Drive``): so each window is written in scene seconds, the drawing is the
same at every frame rate, and the end state is exactly P11 (beams at 30%, hairline at 100%, ranges at rest).
``END_FADE`` is the length of the closing fade; P11 is the frame before it (storyboard: "P11: the last frame before
the fade"). A subclass with END_FADE = 0 ends exactly in P11 (that is how the pose check of the last frame is run).
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/ and world.py

from kit import *  # noqa: E402,F401,F403
from manim import ManimColor, color_to_rgb, config  # noqa: E402
import world  # noqa: E402

C = world.C
RANGES = world.RANGES                       # name: (row y, left x, right x)
BEAM_X = {n: float(p[0]) for n, p in world.BEAM_ENDS.items()}
NAMES = ("gA", "gD")
PITCH = (RANGES["gA"][2] - RANGES["gA"][1]) / 16          # world.Range's dot pitch at rest (17 dots over 0.95)
TICK_H = 0.36                                              # a crisp white tick (rule 16: 0.3 or more)
OVERLAP = (max(RANGES[n][1] for n in NAMES), min(RANGES[n][2] for n in NAMES))   # x 2.1 to 2.75
BREATH = 0.06                                              # the ranges' centres move left and right by this much
BREATH_PHASE = {"gA": 0.0, "gD": 2.1}                      # the two do not breathe in step
BEAM_DRAWN, BEAM_REST = 0.9, 0.3


def _u(t: float, a: float, b: float) -> float:
    return 0.0 if t <= a else (1.0 if t >= b else (t - a) / (b - a))


def _e(func, u: float) -> float:
    """A kit rate function with exact ends."""
    return 0.0 if u <= 0.0 else (1.0 if u >= 1.0 else float(func(u)))


def _lerp(a: float, b: float, u: float) -> float:
    return b if u >= 1.0 else (a if u <= 0.0 else a + (b - a) * u)


class Drive(Animation):
    """Calls fn(t) on every frame of a play with the scene time t of that frame (as in s05.py). With ``mob`` and
    ``introducer=True`` it brings ``mob`` into the scene in its place in the play's list (the end fade uses this to
    lie over the sign-off, which enters in the same play)."""

    def __init__(self, scene, fn, mob=None, **kw):
        kw.setdefault("rate_func", CLOCK)
        super().__init__(mob if mob is not None else Mobject(), suspend_mobject_updating=False, **kw)
        self._scene, self.fn = scene, fn

    def begin(self) -> None:
        self.t0 = float(self._scene.now)
        super().begin()

    def interpolate_mobject(self, alpha: float) -> None:
        self.fn(self.t0 + alpha * self.run_time)


class LiveRange(world.Range):
    """world.Range with three more numbers, all at their rest value in P11:
    ``dx``  the breathing offset of the whole range;
    ``cap`` 0..1, the height and light of the two dotted caps (0 while the first dot slides out of the beam);
    ``live`` True while the range grows, folds or melts: its dots keep the rest pitch from the left end, so they
    appear one by one at the moving end instead of re-spacing on every frame.
    With dx = 0, cap = 1 and live False it paints exactly world.Range (the pose's object)."""

    def paint(self):
        dx, cap, live = getattr(self, "dx", 0.0), getattr(self, "cap", 1.0), getattr(self, "live", False)
        x0, x1 = self.x0, self.x1
        if not live:
            self.x0, self.x1 = x0 + dx, x1 + dx
            try:
                super().paint()
            finally:
                self.x0, self.x1 = x0, x1
        else:
            a0, a1 = x0 + dx, x1 + dx
            k = min(int(np.floor(max(a1 - a0, 0.0) / PITCH + 1e-6)) + 1, 40)
            pts = np.zeros((40, 3))
            pts[:, 0], pts[:, 1] = a0, self.y
            pts[:k, 0] = a0 + PITCH * np.arange(k)
            a = np.zeros(40)
            a[:k] = 0.95
            self.row.points, self.row.rgbas[:, 3] = pts, a
            cy = np.linspace(-0.12, 0.12, 5)
            self.caps.points = np.array([[x, self.y + d, 0] for x in (a0, a1) for d in cy])
            self.caps.rgbas[:, 3] = 0.95
            self.row.set_fill(opacity=self.level)
            self.caps.set_fill(opacity=self.level)
        if cap != 1.0:
            p = self.caps.points.copy()
            p[:, 1] = self.y + (p[:, 1] - self.y) * cap
            self.caps.points = p
            self.caps.rgbas[:, 3] = 0.95 * cap
        return self


def soft_column(x0: float, x1: float, y0: float, y1: float, color, peak: float, fx: float, fy: float) -> RasterLayer:
    """A soft glow over the canvas box (x0..x1, y0..y1): full only in its middle, falling off smoothly over ``fx``
    beyond its left and right ends and ``fy`` beyond its top and bottom (inside the box too), as one dithered
    picture. No edge can be seen: it is a brightening, not a fill (the kit's soft_band is soft on two sides only)."""
    ppu = px_per_unit()
    W, H = (x1 - x0) + 2 * fx, (y1 - y0) + 2 * fy
    w, h = max(int(round(W * ppu)), 2), max(int(round(H * ppu)), 2)

    def prof(n: int, size: float, fe: float) -> np.ndarray:
        s = (np.arange(n) + 0.5) / n * size
        u = np.clip(np.minimum(s, size - s) / (2 * fe), 0, 1)
        return u * u * (3 - 2 * u)

    a = peak * 255 * np.outer(prof(h, H, fy), prof(w, W, fx))
    d = np.random.default_rng(11).random((h, w))
    rgb = np.array(color_to_rgb(ManimColor(color)), dtype=float)
    out = np.empty((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.floor(a[..., None] * rgb[None, None, :] + d[..., None])
    out[..., 3] = np.floor(a + d)
    out[a <= 0] = 0
    layer = RasterLayer(out, height=H, premultiplied=True).stretch_to_fit_width(W)
    return layer.move_to(C((x0 + x1) / 2, (y0 + y1) / 2))


class S11(Narrated):
    END_FADE = 0.8                          # seconds; 0 ends the scene in P11 itself (pose check of the last frame)

    def build(self):
        w = world.pose("P10", self)
        pool, model, test, cost = w.pool, w.model, w.test, w.cost
        f = 1.0 / self.fps
        D = self.scene_duration

        # ------------------------------------------------------------------ the voice
        t_l0, t_l1, t_l2 = self.line_start(0), self.line_start(1), self.line_start(2)
        t_rec = self.word_span(0, "recommendation")[0]
        t_tw = self.word_span(0, "trustworthy")[0]
        t_weak = self.word_span(1, "weak")[0]
        t_ch = self.word_span(1, "changes")[0]
        t_rather = self.word_span(2, "rather")[0]
        t_know = self.word_span(2, "know")[0]
        t_rank = self.word_span(2, "ranking")[0]
        t_no = self.word_span(2, "no")[0]
        t_rel = self.word_span(2, "reliable")[0]
        t_end2 = self.line_end(2)

        # windows (scene seconds). A window ends inside its row (rule 3), with a margin of one draft frame so that
        # draft and review draw the same thing at the same time: the beams' 1.5 s (1.2 s each, 0.3 s apart) is fitted
        # to the row "trustworthy?" when it is shorter, and the two pulses to the row "weak ... changes".
        edge = 1.0 / 15
        k = min(1.0, (t_l1 - edge - t_tw) / 1.5)
        beam_win = {"gA": (t_tw, t_tw + 1.2 * k), "gD": (t_tw + 0.3 * k, t_tw + 1.5 * k)}
        hair_draw = (t_tw + 0.9 * k, t_tw + 1.5 * k)
        pulse_win = (t_ch, min(t_ch + 1.0, t_l2 - edge))
        slide, grow = (t_l1, t_l1 + 0.3), (t_l1 + 0.3, t_l1 + 1.9)
        settle = (t_l1 + 0.3, t_l1 + 1.3)
        col_in, col_pulse, col_out = (t_weak, t_weak + 0.6), (t_know, t_know + 0.8), (t_rank, t_rank + 0.4)
        fold = (t_rank, t_rank + 0.5)
        hair_out = (t_no, t_no + 0.6)
        flips = [(t_rel + 0.3 * k, t_rel + 0.3 * k + 0.1) for k in range(3)]
        melt = (t_end2, t_end2 + 0.8)
        sign = [(t_end2 + 0.8, t_end2 + 1.7), (t_end2 + 1.3, t_end2 + 2.2)]       # the two lines, 1.4 s in all
        fade = (D - self.END_FADE, D - f)                                           # the last frame is the background

        # ------------------------------------------------------------------ breathing (a function of scene time)
        ts = np.arange(0.0, D + 0.01, 0.002)
        smooth = np.vectorize(lambda u: _e(MOVE, float(u)))
        b0, b1 = grow[1], melt[1]
        calm = np.clip((ts - t_rather) / 1.5, 0, 1)
        live = (1 - calm) ** 2                                      # ease-out to stillness from "rather"
        amp = np.where(ts < b1, smooth((ts - b0) / 1.2) * live, 0.7 * smooth((ts - b1) / 1.5))
        speed = np.where(ts < b1, TAU / 3.6 * live, TAU / 6.0)      # very slowly in the silence
        phase = np.concatenate([[0.0], np.cumsum(speed[:-1] * np.diff(ts))])

        def breath(name: str, t: float) -> float:
            a = float(np.interp(t, ts, amp))
            if a <= 0:
                return 0.0
            return BREATH * a * idle_gain() * math.sin(float(np.interp(t, ts, phase)) + BREATH_PHASE[name])

        # ------------------------------------------------------------------ the passing objects (added unseen)
        full_beams = {n: world.beam(n, BEAM_REST) for n in NAMES}
        beams = VGroup(*[world.beam(n, 0.0) for n in NAMES])
        live_beams = dict(zip(NAMES, beams))
        model.between.add(beams)
        full_hair = world.ranges_hairline()
        hair = world.ranges_hairline(0.0)
        column = soft_column(OVERLAP[0], OVERLAP[1], RANGES["gD"][0] - 0.3, RANGES["gA"][0] + 0.3, FOCUS,
                             peak=0.24, fx=0.13, fy=0.3).set_opacity(0.0)
        ranges = {n: LiveRange(n) for n in NAMES}
        centre = {n: (RANGES[n][1] + RANGES[n][2]) / 2 for n in NAMES}
        ticks = {n: Line(C(centre[n], RANGES[n][0] - TICK_H / 2), C(centre[n], RANGES[n][0] + TICK_H / 2),
                         stroke_color=INK_HI, stroke_width=W_BOLD, stroke_opacity=0.0) for n in NAMES}

        def tick_x(name: str, t: float) -> float:
            p = sum((-1) ** k * _e(MOVE, _u(t, *flips[k])) for k in range(3))     # 0 -> 1 -> 0 -> 1
            other = centre["gD" if name == "gA" else "gA"]
            return _lerp(centre[name], other, p) if 0 < p < 1 else (other if p >= 1 else centre[name])

        def draw_partial(live_m, full_m, a: float, opacity: float) -> None:
            if a <= 0:
                live_m.set_stroke(opacity=0.0)
                return
            if a >= 1:
                live_m.set_points(full_m.points)
            else:
                live_m.pointwise_become_partial(full_m, 0, a)
            live_m.set_stroke(opacity=opacity)

        def state(t: float) -> None:
            # beams: drawn from their group, then settle to 30% as the ranges grow
            op = _lerp(BEAM_DRAWN, BEAM_REST, _e(MOVE, _u(t, *settle)))
            for n in NAMES:
                draw_partial(live_beams[n], full_beams[n], _e(MOVE, _u(t, *beam_win[n])), op)
            # hairline: draws, fades on "no", returns in the melt
            hop = 1.0 - _e(MOVE, _u(t, *hair_out)) if t < melt[0] else _e(MOVE, _u(t, *melt))
            draw_partial(hair, full_hair, _e(MOVE, _u(t, *hair_draw)), hop)
            # the soft column over the overlap
            if t < fold[0]:
                cop = 0.6 * _e(MOVE, _u(t, *col_in)) + 0.4 * _e(PULSE, _u(t, *col_pulse))
            else:
                cop = 0.6 * (1.0 - _e(MOVE, _u(t, *col_out)))
            column.set_opacity(cop)
            # ranges and ticks
            for n in NAMES:
                y, x0f, x1f = RANGES[n]
                r, tk = ranges[n], ticks[n]
                r.cap, r.level, r.live = 1.0, 1.0, False
                if t < slide[0]:
                    r.x0 = r.x1 = BEAM_X[n]
                    r.level = 0.0
                elif t < grow[0]:                                    # the first dot leaves the beam's end
                    r.x0 = r.x1 = _lerp(BEAM_X[n], x0f, _e(MOVE, _u(t, *slide)))
                    r.cap, r.live = 0.0, True
                elif t < grow[1]:                                    # and the range grows to the right
                    r.x0, r.x1 = x0f, _lerp(x0f, x1f, _e(MOVE, _u(t, *grow)))
                    r.cap, r.live = _e(ENTER, _u(t, grow[0], grow[0] + 0.5)), True
                elif t < fold[0]:
                    r.x0, r.x1 = x0f, x1f
                elif t < melt[0]:                                    # folds into its tick
                    uf = _e(ENTER, _u(t, *fold))
                    r.x0, r.x1 = _lerp(x0f, centre[n], uf), _lerp(x1f, centre[n], uf)
                    r.level = 1.0 - _e(MOVE, _u(t, fold[0] + 0.25, fold[1]))
                    r.live = True
                else:                                                # and melts back from where the tick is
                    tx, um = tick_x(n, melt[0]), _e(MOVE, _u(t, *melt))
                    r.x0, r.x1 = _lerp(tx, x0f, um), _lerp(tx, x1f, um)
                    r.level = _e(MOVE, _u(t, melt[0], melt[0] + 0.35))
                    r.live = um < 1.0
                r.dx = breath(n, t)
                r.paint()
                if t < fold[0]:
                    top = 0.0
                elif t < melt[0]:
                    top = _e(MOVE, _u(t, fold[0] + 0.25, fold[1]))
                else:
                    top = 1.0 - _e(MOVE, _u(t, melt[0], melt[0] + 0.35))
                h = _lerp(0.24, TICK_H, _e(MOVE, _u(t, fold[0] + 0.25, fold[1])))
                x = tick_x(n, t)
                tk.put_start_and_end_on(C(x, y - h / 2), C(x, y + h / 2))
                tk.set_stroke(opacity=top)

        state(0.0)
        self.add(column, hair, *ranges.values(), *ticks.values())

        def drive() -> Drive:
            return Drive(self, state)

        # ------------------------------------------------------------------ row 1: at(0) "What evidence would make a recommendation"
        # The question returns left to right: four staggered windows with lag_ratio 0.3 that fill the row.
        L1 = (t_tw - edge) - t_l0
        d = L1 / (1 + 3 * 0.3)
        rise = [timed(o.to_level(1.0, run_time=d), t_l0 + 0.3 * d * i, t_l0 + 0.3 * d * i + d)
                for i, o in enumerate((pool, model, test, cost))]
        self.at(0)
        self.play_until(t_tw - f, drive(), *rise,
                        timed(pool.to_outlines({"gA": 1.0, "gD": 1.0}, run_time=0.6), t_rec, t_rec + 0.6),
                        timed(pool.to_tints({"gA": 0.12, "gD": 0.12}, run_time=0.6), t_rec, t_rec + 0.6))

        # ------------------------------------------------------------------ row 2: "trustworthy?" the beams, the hairline
        self.play_until(t_l1 - f, drive())

        # ------------------------------------------------------------------ row 3: at(1) the ranges are born from the beams
        self.play_until(t_weak - f, drive())

        # ------------------------------------------------------------------ row 4: "weak" the overlap; "changes" the two groups pulse
        goal = pool._vec({"gA": 0.34, "gD": 0.34}, pool.tint)
        order = [0 if n == "gA" else (2 if n == "gD" else 1) for n in world.GROUP_NAMES]    # gA first, gD last
        pulse = world.Tween(pool, "tint", goal, lag=0.5, order=order, rate_func=PULSE, run_time=1.0)
        self.play_until(t_l2 - f, drive(), timed(pulse, *pulse_win))

        # ------------------------------------------------------------------ row 5: at(2) "rather" calm; "know" the column once
        self.play_until(t_rank - f, drive())

        # ------------------------------------------------------------------ row 6: "ranking" the ranges fold into ticks
        self.play_until(t_no - f, drive())

        # ------------------------------------------------------------------ row 7: "no" the hairline fades; "reliable" three flips
        self.play_until(t_end2 - f, drive())
        self.remove(column)

        # ------------------------------------------------------------------ row 8: line_end(2) melt, sign-off, hold, fade
        so = world.sign_off()
        anims = [drive(), *[timed(enter(so[i], run_time=b - a), a, b) for i, (a, b) in enumerate(sign)]]
        if self.END_FADE > 0:
            cover = RasterLayer(np.array(self.camera.background), height=config.frame_height)
            cover.fx_snap = True
            cover.move_to(self.frame.get_center()).set_opacity(0.0)
            cover.layout_ignore = True

            def fade_to_background(t: float) -> None:
                cover.set_opacity(_e(MOVE, _u(t, *fade)))

            anims.append(Drive(self, fade_to_background, mob=cover, introducer=True))   # last: it lies over everything
        self.play_until(D, *anims)
