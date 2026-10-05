"""A 13-second example scene on the kit: the patterns that a scene of the film is built from (README.md, "Example").

    tmp/explainer-venv/bin/manim render -ql --media_dir tmp/explainer-build-v2/foundation/kit/media/example \
        writing/substack/explainer-video/kit/example_scene.py Example

It is not a scene of the film: it has stand-in timings without speech, and its picture makes no claim.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _HERE]   # kit/ itself must not be an import root
sys.path.insert(0, str(_HERE.parent))                                      # the folder that holds kit/

from kit import *  # noqa: E402,F403

LINES = [(0.4, "Here is a pool of 1,440 examples."), (4.6, "Suppose we change one group of them."),
         (8.8, "Look at that group closely.")]
TIMINGS = silent_timings(BUILD / "foundation" / "kit" / "example_timings.json", "Example", LINES, 13.0)


class Example(Narrated):
    timings_file = TIMINGS          # only here: a scene of the film reads BUILD/audio/timings.json by its class name

    def build(self):
        n, lit = 1440, 60
        home, fade = soft_field(n, 9.0, 3.8, seed=3, centre=(-0.2, -0.4))     # a soft organic outline, not a box of dots
        shade = np.random.default_rng(3).random(n)                             # uneven: shade and size vary a little
        rgbas = np.column_stack([[mix(DATA_LO, DATA, 0.45 + 0.55 * u).to_rgb() for u in shade], (0.45 + 0.5 * shade) * fade])
        turn = np.random.default_rng(4).random(n)                    # the order in which the points arrive
        rest = np.argsort(turn)[lit:]                                # all but the first 60: they arrive in line 0

        # The stage is set at t = 0 (no empty first frame): some of the pool, its read-out and the tag are there.
        pool = DotCloud(home, radius=DOT_R * (0.75 + 0.5 * fade), rgbas=rgbas, glow=0.15).drift(seed=3, twinkle=0.15)
        alpha = pool.rgbas[:, 3].copy()
        pool.set_opacities(0.0, rest)
        unit = self.pin(put(T("examples", "label", MUTED), SAFE_X, TITLE_Y, edge=RIGHT))
        count = self.pin(LiveNumber(lit, size="title", reserve=n).place([unit.get_left()[0] - GAP_S, TITLE_Y, 0]))
        self.add(pool, count, unit, self.hud_tag())

        # Line 0. A process, not a chart: one draw, a few, then many. The number and the points have ONE source, the
        # clock, and the count lands on the word "1,440". The name lands on its word inside the same play (timed).
        self.at(0)
        rhythm = sampling_rhythm(n - lit, total=self.word_span(0, "1,440")[1] - self.now, slow=0.5, mid=0.2, n_mid=3)
        clock = ValueTracker(0.0)
        count.follow(clock, lambda t: lit + np.searchsorted(rhythm.starts, t, side="right"))
        name = put(T("the pool", "label", DATA), -4.6, 1.8)          # a label: 1 to 4 words, at its object, in its colour
        self.play(pool.appear(rhythm.starts, idx=rest, order=turn, opacity=alpha[rest], run_time=rhythm.total),
                  clock.animate(rate_func=CLOCK).set_value(rhythm.total),
                  timed(enter(name), self.word_span(0, "pool")[0]), run_time=rhythm.total)

        # Line 1. On the word "one", the points nearest to a spot gather and take the colour of the thing we change;
        # the rest steps back to 35% of its own opacity. The new label is born from the old one, late in the same play.
        spot = np.array([3.4, -0.5, 0.0])
        group = np.argsort(np.linalg.norm(home - spot, axis=1))[:240]
        others = np.setdiff1d(np.arange(n), group)
        disc = match_points(home[group], sunflower_points(240, 1.0, spot, jitter=0.3))
        group_name = backstroke(T("one group", "label", FOCUS)).next_to(spot + 1.0 * UP, UP, buff=GAP_S)   # it sits on art
        self.at_word(1, "one")
        self.play(pool.to(centers=disc, color=FOCUS, opacity=0.95, glow=0.6, idx=group, lag=0.4, order="radial", arc=0.5),
                  pool.to(opacity=0.35 * alpha[others], glow=0.0, idx=others),
                  hand_over(name, group_name, rate_func=late(0.5)), run_time=T_MOVE)

        # Line 2. The camera goes to the group and comes back (a scene ends in its rest framing). The read-out and the
        # tag are pinned; the group's name follows the group and keeps its size on screen.
        self.at(2)
        self.follow_label(group_name, spot + 1.0 * UP)
        self.play(self.push_in(spot, 1.6, run_time=2.2), pool.to(glow=1.0, idx=group, lag=0.6, order="random"), run_time=2.2)
        self.play_until(self.scene_duration - 0.4, self.pull_back())
