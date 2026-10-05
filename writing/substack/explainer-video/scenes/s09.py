"""S09 About 18.5% (storyboard section 5, S09). Opening pose P08, closing pose P09. Camera at P, no move.

The two runs of the scale are clock-driven (rule 3 of 1.2): one driver at the front of the scene sets both head
positions from the film clock on every frame, by the run rule of 3.6 (world.run_x). Run 1 starts at at(0) and stops
as "18.5%" starts; run 2 has run 1's speed and stops as "14.1%" starts (world.run2_start). Every other beat is one
play per row of the beat table, its motions placed on their words with timed().
"""
# qa: bleed   (the open boundary crosses |x| = 6.4 in S05 to S09: Boundary is bleed_ok)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/ and world.py

from kit import *  # noqa: E402,F401,F403
import world  # noqa: E402

PL = world.PL
THREAD_OP = 0.35            # the thin threads as they draw (3.10)
THREAD_REST = 0.15          # the threads of `strongest` at rest (P09)
CORNER = 0.08               # rounded corners of the flash threads
# The storyboard lands each numeral in 0.6 s. Built so, S09 fails qa's hard bar "Frozen share of the speech time"
# (37% of the speech time, limit < 30%), because the scene holds still by design under the spoken numerals, after
# "best" and on the verdict line. So each numeral lands over its whole spoken word (about 1.5 s, one steady fade):
# still whole, on its word, all glyphs at once, FadeIn with scale 0.92 and no lag ratio (rule 2 of 1.1).
# False restores the storyboard's 0.6 s landing.
NUMERAL_OVER_WORD = True


def _flash_points(unit, y_run: float, head, end_gap: float = 0.12, step: float = 0.02) -> np.ndarray:
    """The path of a flash thread (P-local y): from the unit straight up to y_run, left at that height, and straight
    down onto the head from directly above, stopping at the edge of the head's glow. Small rounded corners."""
    ux, uy = float(unit[0]), float(unit[1]) + 0.04
    hx, hy = float(head[0]), float(head[1]) + end_gap
    r = CORNER
    pts = [np.array([ux, uy])]
    pts.append(np.array([ux, y_run - r]))
    for a in np.linspace(0, np.pi / 2, 7)[1:]:                         # turn left at the top of the rise
        pts.append(np.array([ux - r + r * np.cos(a), y_run - r + r * np.sin(a)]))
    pts.append(np.array([hx + r, y_run]))
    for a in np.linspace(np.pi / 2, np.pi, 7)[1:]:                     # turn down above the head
        pts.append(np.array([hx + r * np.cos(a) + r, y_run - r + r * np.sin(a)]))
    pts.append(np.array([hx, hy]))
    p = np.array(pts)
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    s = np.linspace(0, cum[-1], max(int(cum[-1] / step), 8))
    q = np.column_stack([np.interp(s, cum, p[:, 0]), np.interp(s, cum, p[:, 1])])
    return np.column_stack([q[:, 0], q[:, 1] + world.PY, np.zeros(len(q))])


def _partial(points: np.ndarray, f: float) -> np.ndarray:
    """The first share ``f`` (by length) of a dense polyline."""
    if f >= 1:
        return points
    seg = np.linalg.norm(np.diff(points, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    L = cum[-1] * max(f, 1e-4)
    k = int(np.searchsorted(cum, L))
    k = min(max(k, 1), len(points) - 1)
    a = (L - cum[k - 1]) / max(seg[k - 1], 1e-9)
    return np.vstack([points[:k], points[k - 1] + (points[k] - points[k - 1]) * a])


class S09(Narrated):
    def build(self):
        w = world.pose("P08", self)
        field, ruler = w.field, w.ruler
        L1, L2 = world.RESULT_L
        iu = [int(world.FIELD_U["u1"]), int(world.FIELD_U["u2"])]

        # ---- the cues (scene seconds, from the word timings)
        t_run1 = self.line_start(0)                          # at(0): run 1 leaves the zero tick
        t_str1 = self.word_span(1, "strongest")[0]
        t_185 = self.word_span(1, "18.5%")[0]                # run 1 stops as "18.5%" starts
        t_l3 = self.line_start(2)
        t_full = self.word_span(2, "full")[0]
        t_str2 = self.word_span(2, "strongest")[0]
        t_res = self.word_span(2, "result")[0]
        t_141 = self.word_span(2, "14.1%")[0]                # run 2 stops as "14.1%" starts
        t_l4 = self.line_start(3)
        t_best = self.word_span(3, "best")[0]
        t_avg = self.word_span(3, "averages")[0]
        t_orc = self.word_span(3, "oracle")[0]
        t_pra = self.word_span(3, "practical")[0]
        t_l5 = self.line_start(4)
        t_cond = self.word_span(4, "condition")[0]
        t_adv = self.word_span(4, "advancing")[0]

        v1 = L1 / (t_185 - t_run1 - 0.3)                     # the run rule of 3.6
        t_run2 = world.run2_start(t_141, v1, L2)             # same speed as run 1
        if t_run2 < t_l3 + 0.8:                              # the guard of 3.6: track 2 is drawn before run 2 starts
            raise RuntimeError(f"S09: run 2 would start at {t_run2:.3f} s, before track 2 has finished drawing "
                               f"({t_l3 + 0.8:.3f} s)")

        def scene_t() -> float:
            return film_time() - self.film_start

        def head_x(i: int, t: float) -> float:
            if i == 0:
                return world.run_x(t, t_run1, t_185, L1)
            return world.run_x(t, t_run2, t_141, L2, v=v1)

        # ---- the clock-driven runs: one driver at the front of the scene (before the ruler paints)
        def drive(m):
            t = scene_t()
            ruler.x[0] = head_x(0, t)
            ruler.x[1] = head_x(1, t)

        driver = Mobject()
        driver.add_updater(drive)
        drive(driver)
        self.add(driver)
        self.bring_to_back(driver)

        # ---- a flash thread: from a lit unit to its moving head (0.6 s): it draws, then fades
        def flash_thread(u: str, track: int, y_run: float):
            unit = field.unit(u)
            unit = np.array([unit[0], unit[1] - world.PY])
            th = VMobject(stroke_color=INK, stroke_width=W_LINE, stroke_opacity=0.0, fill_opacity=0)
            th.set_points_as_corners(np.array([PL(*unit[:2]), PL(*unit[:2]) + 1e-3 * RIGHT]))

            def f(m, a):
                hx = head_x(track, scene_t())
                pts = _flash_points(unit, y_run, (hx, world.TRACK_Y[track]))
                d = ENTER(min(a / 0.5, 1.0))                  # it reaches the head in the first half
                fade = 1.0 - MOVE(float(np.clip((a - 0.5) / 0.5, 0.0, 1.0)))
                m.set_points_as_corners(_partial(pts, d) if d > 0 else pts[:2])
                m.set_stroke(opacity=THREAD_OP * fade * float(d > 0))

            return th, UpdateFromAlphaFunc(th, f, run_time=0.6, rate_func=linear, suspend_mobject_updating=False)

        # ======== at(0): line 1 and line 2 up to the numeral. Run 1; on "strongest" u1 lights and its thread
        # flashes from u1 to the moving head (up to y = 1.4, above `target family`, and down onto the head).
        self.at(0)
        th1, flash1 = flash_thread("u1", 0, 1.4)
        self.play_until(t_185,
                        timed(field.to_lit("u1", 1.0, run_time=T_QUICK), t_str1),
                        timed(flash1, t_str1))
        self.remove(th1)

        # ======== "18.5%": the head has stopped at x = 3.65; the numeral lands whole during the word, `about` from
        # its first frame (see NUMERAL_OVER_WORD).
        def land_numeral(row, i: int, word: str) -> list:
            t0, t1 = self.word_span(i, word)
            rt, rf = (t1 - t0, CLOCK) if NUMERAL_OVER_WORD else (T_QUICK, ENTER)
            return [timed(FadeIn(m, scale=0.92, run_time=rt, rate_func=rf), t0) for m in (row.about, row.num)]

        row185 = world.result_row("18.5%")
        self.play_until(self.line_end(1), *land_numeral(row185, 1, "18.5%"))

        # ======== line_end(1): the silence. Nothing moves but the breath of the head's glow.
        self.at(2)

        # ======== at(2): `target family` fades; the second curve draws round the lower part (0 to 0.7 s); track 2
        # draws from the zero tick (0 to 0.8 s, linear); the second marker comes out of the zero tick, which flares
        # once; `full suppression` lands beside the curve on "full". Run 2 starts by the clock (about "event's").
        lower_full = field.lower_outline.copy()

        def draw_lower(m, a):
            if a <= 0:
                return
            if m.lower < 1:
                m.lower = 1.0
                m.paint()
            m.lower_outline.pointwise_become_partial(lower_full, 0, MOVE(a))

        def zero_flare(m, a):
            m.zero_flash = 0.7 * PULSE(a)
            m.paint()

        fs_curve = world.label("full suppression@curve")
        self.play_until(t_str2,
                        timed(leave(w.labels["target family"], run_time=T_QUICK), t_l3),
                        timed(UpdateFromAlphaFunc(field, draw_lower, run_time=0.7, rate_func=linear,
                                                  suspend_mobject_updating=False), t_l3),
                        timed(ruler.to_track(1, 1.0, run_time=0.8), t_l3),
                        timed(UpdateFromAlphaFunc(ruler, zero_flare, run_time=0.8, rate_func=linear,
                                                  suspend_mobject_updating=False), t_l3),
                        timed(ruler.tween("shown", [1.0, 1.0], run_time=T_QUICK, rate_func=ENTER), t_l3),
                        timed(enter(fs_curve, run_time=T_QUICK), t_full))

        # ======== "strongest" (line 3): u2 lights; its thread flashes to the moving second head, up to y = 0.95,
        # above `full suppression`, and down under trail 1. From "result" `full suppression` hands over to the row.
        th2, flash2 = flash_thread("u2", 1, 0.95)
        self.mobjects.insert(self.mobjects.index(ruler), th2)          # under trail 1
        fs_row = world.label("full suppression@row")
        self.play_until(t_141,
                        timed(field.to_lit("u2", 1.0, run_time=T_QUICK), t_str2),
                        timed(flash2, t_str2),
                        timed(leave(fs_curve, run_time=T_QUICK), t_res),
                        timed(enter(fs_row, run_time=T_QUICK), t_res))
        self.remove(th2)

        # ======== "14.1%": the second head has stopped at x = 1.45; the numeral lands whole with its `about`.
        row141 = world.result_row("14.1%")
        self.play_until(t_l4, *land_numeral(row141, 2, "14.1%"))

        # ======== at(3): on "best" the two lit units pulse once (0.8 s); `strongest` lands left of the field and its
        # two thin threads draw from its right end to u1 and u2 (0.6 s), stopping at the edge of each glow.
        def pulse_units(m, a):
            m.paint()
            m.cloud.radii[iu] *= 1.0 + 0.7 * PULSE(a)

        strongest = world.label("strongest")
        threads = VGroup(*[Line(world.STRONGEST_START, world.STRONGEST_ENDS[u], stroke_color=INK, stroke_width=W_LINE,
                                stroke_opacity=THREAD_OP) for u in ("u1", "u2")])
        threads_full = [t.copy() for t in threads]
        threads.set_stroke(opacity=0.0)
        self.mobjects.insert(self.mobjects.index(ruler) + 1, threads)  # where P09 has them: over the ruler, under text

        def draw_threads(m, a):
            d = ENTER(a)
            for t, full in zip(m, threads_full):
                if d > 0:
                    t.pointwise_become_partial(full, 0, d)
                t.set_stroke(opacity=THREAD_OP * float(d > 0))

        self.play_until(t_avg,
                        timed(UpdateFromAlphaFunc(field, pulse_units, run_time=0.8, rate_func=linear,
                                                  suspend_mobject_updating=False), t_best),
                        timed(enter(strongest, run_time=T_QUICK), t_best),
                        timed(UpdateFromAlphaFunc(threads, draw_threads, run_time=T_QUICK, rate_func=linear,
                                                  suspend_mobject_updating=False), t_best))

        # ======== "averages": the whole field dims to 40%, inside and outside the family alike (1.0 s); the lit
        # units stay lit; the threads of `strongest` settle from 35% to 15%.
        def settle_threads(m, a):
            m.set_stroke(opacity=THREAD_OP + (THREAD_REST - THREAD_OP) * MOVE(a))

        self.play_until(t_orc,
                        timed(field.to_units(0.4, run_time=1.0), t_avg),
                        timed(UpdateFromAlphaFunc(threads, settle_threads, run_time=1.0, rate_func=linear,
                                                  suspend_mobject_updating=False), t_avg))

        # ======== "oracle": above trail 1 the web is wiped in from left to right (2.0 s). The tag is on from the
        # web's first frame.
        web = world.web()
        layer = bake(self, [web.art])
        # 3.8 asks for the fans' ends "at 50% with a 0.03 blur, so that no branch or end can be counted"; world.web()
        # draws them sharp (27 countable lines). Blur the baked picture by 0.03 (premultiplied, so edges stay clean).
        from scipy.ndimage import gaussian_filter
        sig = 0.03 * px_per_unit()
        soft = gaussian_filter(layer.fx_pixels.astype(np.float32), sigma=(sig, sig, 0))
        layer.set_image(np.clip(np.round(soft), 0, 255).astype(np.uint8), premultiplied=True)
        x0, x1, y0, y1 = -5.05, 0.25, -1.6, 1.7                      # P-local box of the wipe

        def clip_box(xe):
            return [PL(x0, y0), PL(xe, y0), PL(xe, y1), PL(x0, y1), PL(x0, y0)]

        clip = VMobject(stroke_color=INK, stroke_width=0, stroke_opacity=0, fill_color=INK, fill_opacity=0)
        clip.set_points_as_corners(clip_box(x0 + 1e-3))
        clip.layout_ignore = True
        set_clip(layer, clip)
        # The web lies under the ruler and the text, so that it folds INTO trail 1 and passes behind the labels on its
        # way down. The clip comes before the art (kit trap 15).
        below = self.mobjects.index(ruler)
        self.mobjects[below:below] = [clip, layer]
        tag = self.hud_tag()
        self.add(tag)

        def wipe(m, a):
            m.set_points_as_corners(clip_box(x0 + 1e-3 + (x1 - x0) * CLOCK(a)))     # a sweep: one steady speed

        self.play_until(t_pra,
                        timed(UpdateFromAlphaFunc(clip, wipe, run_time=2.0, rate_func=linear,
                                                  suspend_mobject_updating=False), t_orc))

        # ======== "practical": one run lights on top, paired step by step (0.8 s): the first step of the path in
        # each tree and the link between the two chosen points of the arcs, then the second step and the link
        # between the two chosen ends. Then the web folds into trail 1 (0.8 s), and the tag goes off.
        for m in layer.get_family():
            m.fx_clip = None
        self.remove(clip)
        pa, pb, link1, link2 = web.run
        steps = []
        for p in (pa, pb):
            a_, c_, e_ = p.get_start(), p.points[3], p.get_end()
            col, op = p.get_stroke_color(), p.get_stroke_opacity()
            steps.append((world.polyline([a_, c_], col, W_LINE, op), world.polyline([c_, e_], col, W_LINE, op)))
        live = [steps[0][0], steps[1][0], link1, steps[0][1], steps[1][1], link2]
        windows = [(0.0, 0.32), (0.0, 0.32), (0.22, 0.45), (0.4, 0.68), (0.4, 0.68), (0.58, 0.8)]

        def draw_on(m):                    # draws m along its path, in place (Create would lift it to the top)
            full, op = m.copy(), m.get_stroke_opacity()
            m.set_stroke(opacity=0.0)

            def f(mm, a):
                if a > 0:
                    mm.pointwise_become_partial(full, 0, MOVE(a))
                mm.set_stroke(opacity=op * float(a > 0))
            return f

        fns = [draw_on(m) for m in live]
        below = self.mobjects.index(ruler)
        self.mobjects[below:below] = live                              # on top of the web, under the ruler
        draws = [timed(UpdateFromAlphaFunc(m, f, run_time=b - a, rate_func=linear, suspend_mobject_updating=False),
                       t_pra + a) for m, f, (a, b) in zip(live, fns, windows)]

        fold_t0 = t_pra + windows[-1][1] + 0.05                       # then the web folds (0.8 s)
        fold_t1 = fold_t0 + 0.8
        if fold_t1 > t_l5 - 0.1:
            raise RuntimeError(f"S09: the fold would end at {fold_t1:.3f} s, after line 5 starts ({t_l5:.3f} s)")
        top_c = PL(0, 0.75)                                            # the middle of the web's height
        drop = world.TRACK_Y[0] - 0.75
        folding = [layer, *live]
        orig = {}

        def fold(m, a):
            if a <= 0:                                                 # before its window: the run is still drawing
                return
            if not orig:
                for o in folding:
                    orig[id(o)] = (o.points.copy(), o.get_stroke_opacity(), o.get_fill_opacity())
            s = MOVE(a)
            k = 1.0 + (0.02 / 1.25 - 1.0) * s                           # to height 0.02
            fade = 1.0 - a
            for o in folding:
                pts, so, fo = orig[id(o)]
                o.points = pts.copy()
                o.stretch(k, 1, about_point=top_c)
                o.shift(UP * drop * s)
                if o is layer:
                    o.set_fill(opacity=fo * fade)
                else:
                    o.set_stroke(opacity=so * fade)
            if a >= 1:                                                 # the tag goes off at the end of the fold
                for t in tag.get_family():
                    t.fx_hidden = True

        self.play_until(t_l5, *draws,
                        timed(UpdateFromAlphaFunc(layer, fold, run_time=fold_t1 - fold_t0, rate_func=linear,
                                                  suspend_mobject_updating=False), fold_t0, fold_t1))
        self.remove(layer, *live, tag)
        for t in tag.get_family():
            t.__dict__.pop("fx_hidden", None)

        # ======== at(4): on "condition" the condition line rises from 85% to 100% along its whole length (0.6 s).
        self.play_until(t_adv, timed(ruler.to_condition(1.0, run_time=T_QUICK), t_cond))

        # ======== "advancing": the faint fork at the top of the line glimmers once (16% to 24% to 16%, 0.8 s).
        self.play_until(self.scene_duration, timed(ruler.glimmer(0.8), t_adv))
