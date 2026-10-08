"""S10 Boundaries (storyboard section 5, S10). Opening pose P09, closing pose P10.

Rows of the beat table, one play each (rule 3 of 1.2):

  at(0)                    the S09 strings and the threads of `strongest` fade (0.5 s); then one 2.0 s hand-over:
                           the pilot's picture, baked, shrinks onto the emblem's box at P-local (0, -0.6) and fades,
                           the drawn emblem fades in late (late(0.6): it lands on "approach"), and the open boundary
                           comes down and closes round it (a Transform between the two 16-anchor smooth_closed shapes)
  at_word(0, "It")         the pan P -> W (clock_move, 3.0 s, GLIDE). The emblem and its curve travel in a straight line
                           on the canvas from (0, -5.8) to (-5.4, -1.6) with the same GLIDE (a clock-driven carrier).
                           The question rises from 15% to 35%, light 0 is red again, and in the last third of the move
                           (once the emblem has passed the lane's left end) the cost floor comes back to 35%.
                           The tag stays off
  at(1)                    tag on with the lamp's first frame; the lamp opens over the upper left of the pool (0.6 s)
                           and glides across it (2.0 s)
  at_word(1, "test")       the lamp glides over the model and on over the two rows of lights (2.2 s)
  at_word(1, "demonstrate") the lamp glides down to the right end of the floor and along it to x = -1.0 (2.6 s)
  at(2)                    the lamp fades where it stands (0.6 s); from "boundaries" the curve brightens to 100% and
                           W_BOLD by itself (1.2 s) and `the pilot` lands late in that window; on "develops" the
                           curve's glow breathes once (1.0 s)

The lamp is world.Lamp: it only raises what is already there toward 100% (3.8); it is not born from the boundary and
never reaches the emblem. The two clock-driven motions (camera, carrier) read the film clock, so no play squeezes them.
"""
# qa: bleed   (P09's open boundary is bleed_ok and crosses |x| = 6.4 until it closes round the emblem in row 1)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/ and world.py

from kit import *  # noqa: E402,F401,F403
import world  # noqa: E402

PL, C = world.PL, world.C
BIRTH = PL(0.0, -0.6)               # canvas (0, -5.8): the emblem is drawn here and the boundary closes round it
HOME = world.EMBLEM_HOME            # canvas (-5.4, -1.6): where it rests in frame W (P10)
PAN = 3.0                           # move 6 of 3.1
TEXT_FADE = 0.5                     # the S09 strings and the two threads
HAND_OVER = 2.0                     # the baked picture -> the emblem, and the boundary closing
COST_BACK = (0.68, 1.0)             # share of the pan in which the cost floor returns to 35% (the emblem's right end
                                    # is then left of x = -3.3, clear of the lane's left end at -3.0)
S09_STRINGS = ("variance reduction", "best baseline", "≥20%", "full suppression@row", "strongest",
               "about 18.5%", "about 14.1%")

# The lamp's path (canvas). It stays at x <= 5.2 and y >= -2.3 (3.8), far from the emblem.
LAMP_OPEN = (-5.2, 2.05)                                       # over the upper left of the pool (gA)
LAMP_POOL = [(-5.2, 2.05), (-4.2, 1.15), (-2.5, 0.85)]         # across the pool
LAMP_TEST = [(-2.5, 0.85), (0.5, 0.7), (3.95, 0.5)]            # over the model, then over both rows of lights
LAMP_FLOOR = ((3.95, 0.5), (4.75, -0.6), (5.25, -2.3), (4.4, -2.3), (-1.0, -2.3))   # cubic down, then left


def _path(points) -> VMobject:
    return VMobject().set_points_smoothly([C(*p) for p in points])


def _floor_path() -> VMobject:
    p0, h1, h2, p1, p2 = (C(*p) for p in LAMP_FLOOR)
    vm = VMobject()
    vm.start_new_path(p0)
    vm.add_cubic_bezier_curve_to(h1, h2, p1)
    vm.add_line_to(p2)
    return vm


def _glide(lamp, path: VMobject, rate=GLIDE) -> Animation:
    """The lamp's centre runs along ``path`` (by arc length)."""
    def f(m, a):
        p = path.point_from_proportion(float(np.clip(a, 0.0, 1.0)))
        lamp.x.set_value(float(p[0]))
        lamp.y.set_value(float(p[1]))
    return UpdateFromAlphaFunc(lamp.x, f, rate_func=rate, suspend_mobject_updating=False)


def _shrink(layer, centre) -> Animation:
    """The baked picture of the pilot scales down onto the emblem's box and fades (one MOVE, as the storyboard's
    ``.animate.scale_to_fit_width(...).move_to(...).set_opacity(0)``). The scale maps the zero tick onto the emblem's
    zero tick and the condition line onto its condition tick; the middle of the two tracks onto the middle of the
    two trails, so the shrinking picture lands on the parts of the emblem that fade in over it."""
    k = world.EMBLEM_SCALE
    s = (0.50 - (-0.62)) * k / (world.COND_X - world.ZERO_X)
    src = PL(world.ZERO_X, sum(world.TRACK_Y) / 2)
    dst = np.asarray(centre, dtype=float) + C(-0.62, (-0.10 - 0.24) / 2) * k
    fixed = (dst - s * src) / (1 - s)
    start = layer.points.copy()

    def f(m, a):
        m.set_points(fixed + (1 + (s - 1) * a) * (start - fixed))
        m.set_fill(opacity=1.0 - a)
    return UpdateFromAlphaFunc(layer, f, rate_func=MOVE, suspend_mobject_updating=False)


def _carrier(scene, mobs, delta, t0: float, t1: float):
    """Clock-driven: from scene time t0 to t1 the mobjects travel by ``delta`` in a straight line on the canvas, with
    the camera's GLIDE (they reach it exactly at t1). Then the updater removes itself."""
    delta = np.asarray(delta, dtype=float)
    done = {"v": np.zeros(3)}

    def step(m):
        t = world._scene_time(scene)
        if t < t0 - 1e-9:
            return
        u = min(max((t - t0) / (t1 - t0), 0.0), 1.0)
        want = delta.copy() if u >= 1.0 else delta * GLIDE(u)
        d = want - done["v"]
        if np.any(d != 0):
            for mob in mobs:
                mob.shift(d)
            done["v"] = want
        if u >= 1.0:
            m.clear_updaters()
    return world._driver(scene, step)


def _brighten(boundary) -> Animation:
    """The closed curve brightens by itself: 45% -> 100%, W_LINE -> W_BOLD, its glow 0 -> 1 (P10)."""
    def f(m, a):
        m.bright = 0.45 + 0.55 * a
        m.glow = a
        m.curve.set_stroke(width=W_LINE + (W_BOLD - W_LINE) * a)
        m.paint()
    return UpdateFromAlphaFunc(boundary, f, rate_func=MOVE, suspend_mobject_updating=False)


def _breathe_once(boundary, peak: float = 0.9) -> Animation:
    """One breath of the curve's glow (there and back), on "develops"."""
    def f(m, a):
        m.glow = 1.0 if a >= 1.0 else 1.0 + peak * float(np.sin(np.pi * a))
        m.paint()
    return UpdateFromAlphaFunc(boundary, f, rate_func=linear, suspend_mobject_updating=False)


class S10(Narrated):
    def build(self):
        w = world.pose("P09", self)
        f1 = 1.0 / self.fps

        def cue(t: float) -> float:
            """End a row one frame before the next cue (the next at() then waits 0 frames)."""
            return t - f1

        texts = [w.labels[k] for k in S09_STRINGS] + [w.extra["strongest threads"]]
        emblem = world.Emblem(BIRTH)
        emblem.set_level(0.0)
        self.add(emblem)
        closed = world.Boundary.closed_curve(BIRTH)                  # 45%, W_LINE: brightened only in line 3
        the_pilot = world.label("the pilot")
        tag = self.hud_tag()

        t_line0 = self.line_start(0)
        t_hand = t_line0 + TEXT_FADE
        t_it = self.word_span(0, "It")[0]

        # ======== at(0): "That tells us something about the particular approach we tested."
        self.at(0)
        layer = bake(self, [w.field, w.ruler])                       # the field, its two curves, the scale, the fork
        i = self.mobjects.index(w.field)
        self.remove(w.field, w.ruler)
        self.mobjects.insert(i, layer)                               # in the field's place in the drawing order
        self.play_until(
            cue(t_it),
            *[timed(leave(m), t_line0, t_line0 + TEXT_FADE) for m in texts],
            timed(_shrink(layer, BIRTH), t_hand, t_hand + HAND_OVER),
            timed(emblem.to_level(1.0, rate_func=late(0.6)), t_hand, t_hand + HAND_OVER),
            timed(Transform(w.boundary.curve, closed, rate_func=MOVE), t_hand, t_hand + HAND_OVER),
        )
        self.remove(layer)

        # ======== at_word(0, "It"): "It does not answer the larger data-change question." The pan up.
        world.clock_move(self, "W", t_it, t_it + PAN)
        _carrier(self, [emblem, w.boundary.curve], HOME - BIRTH, t_it, t_it + PAN)
        self.at_word(0, "It")
        self.play_until(
            cue(self.line_start(1)),
            *[timed(o.to_level(0.35), t_it, t_it + PAN) for o in (w.pool, w.model, w.test)],
            timed(w.test.to_grey(0.0), t_it + 0.3, t_it + 1.5),
            # The floor and the lane come back in the last third of the move: earlier, the travelling emblem passes
            # the lane's left end at its height and would read as the head of the shortcut (X21, X49).
            timed(w.cost.to_level(0.35), t_it + COST_BACK[0] * PAN, t_it + COST_BACK[1] * PAN),
        )

        # ======== at(1): "The pilot did not choose batches of training data to remove or replace,"
        lamp = world.Lamp(*LAMP_OPEN).attach(self, w.question)
        t1 = self.line_start(1)
        self.at(1)
        self.play_until(
            cue(self.word_span(1, "test")[0]),
            timed(enter(tag, run_time=T_QUICK), t1, t1 + T_QUICK),
            timed(lamp.strength.animate(rate_func=MOVE).set_value(1.0), t1, t1 + 0.6),
            timed(_glide(lamp, _path(LAMP_POOL)), t1 + 0.6, t1 + 2.6),
        )

        # ======== at_word(1, "test"): "test safety improvements in an LLM,"
        t_test = self.word_span(1, "test")[0]
        self.at_word(1, "test")
        self.play_until(
            cue(self.word_span(1, "demonstrate")[0]),
            timed(_glide(lamp, _path(LAMP_TEST)), t_test, t_test + 2.2),
        )

        # ======== at_word(1, "demonstrate"): "demonstrate a saving in total computation."
        t_dem = self.word_span(1, "demonstrate")[0]
        self.at_word(1, "demonstrate")
        self.play_until(
            cue(self.line_start(2)),
            timed(_glide(lamp, _floor_path()), t_dem, t_dem + 2.6),
        )

        # ======== at(2): "I want to keep those boundaries visible as the project develops." and the tail
        t2 = self.line_start(2)
        t_bound = self.word_span(2, "boundaries")[0]
        t_dev = self.word_span(2, "develops")[0]
        self.at(2)
        self.play_until(
            self.scene_duration,
            timed(lamp.strength.animate(rate_func=MOVE).set_value(0.0), t2, t2 + 0.6),
            timed(_brighten(w.boundary), t_bound, t_bound + 1.2),
            timed(enter(the_pilot, run_time=0.6), t_bound + 0.6, t_bound + 1.2),
            timed(_breathe_once(w.boundary), t_dev, t_dev + 1.0),
        )
