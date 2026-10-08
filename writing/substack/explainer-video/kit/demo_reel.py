"""The whole kit in one continuous 35-second shot. This reel is the visual standard for the film.

It uses the real base class with a small timings file that it writes itself (silent sound, no speech):

    tmp/explainer-venv/bin/manim render -ql --media_dir tmp/explainer-build-v2/foundation/kit/media/draft \
        writing/substack/explainer-video/kit/demo_reel.py DemoReel
    (add  -r 1920,1080 --fps 30  and another --media_dir for the review size; EXPLAINER_LINT=1 runs the lint)

The numerals are the post's (1,440; 20%; about 18.5%; six groups). Nothing here is a claim: the reel shows the
style, and the pictures of the film are the storyboard's business. Its colours follow the storyboard's map: the pool
is starlight (DATA), the group that is changed is gold (FOCUS), what we read or measure is white (INK).
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _HERE]   # kit/ itself must not be an import root
sys.path.insert(0, str(_HERE.parent))                                      # the folder that holds kit/

from kit import *  # noqa: E402,F403

REEL_DURATION = 35.4
REEL_LINES = [(0.4, "Start with one point of light."),
              (3.8, "Then draw more: slowly at first, then faster."),
              (9.0, "The field regroups."),
              (12.6, "One group lifts out."),
              (16.0, "Follow it closely."),
              (19.6, "Then step back and measure."),
              (25.2, "It stops short of the gate."),
              (28.6, "Hold on the gap.")]
REEL_TIMINGS = silent_timings(BUILD / "foundation" / "kit" / "demo_timings.json", "DemoReel", REEL_LINES, REEL_DURATION)

N = 1440                                        # the post's number of configurations; here simply "many points"
GROUPS = 6
HOME = np.array([0.6, -0.15, 0.0])              # centre of the first field
RING = np.array([0.6, 0.55, 0.0])               # centre of the ring of groups, and the place of the group that lifts out
RULER_Y, RULER_X0, UNIT = -2.4, -5.6, 0.5       # the measuring line: zero at RULER_X0, 0.5 scene units per percent
GROUP_R = 0.8                                   # radius of one group
GATE, RESULT = 20.0, 18.5


class DemoReel(Narrated):
    timings_file = REEL_TIMINGS

    def build(self):
        rng = np.random.default_rng(11)

        # ---- the field: 1,440 points, the first one already alight at t = 0 (no empty first frame)
        home = sunflower_points(N, 2.45, HOME, jitter=0.3, seed=11)
        shade = rng.random(N)
        rgbas = np.column_stack([np.array([mix(DATA_LO, DATA_HI, 0.45 + 0.55 * u).to_rgb() for u in shade]), 0.55 + 0.45 * rng.random(N)])
        field = DotCloud(home, radius=DOT_R * (0.8 + 0.4 * rng.random(N)), rgbas=rgbas, glow=0.2).drift(0.014, seed=3, twinkle=0.12)
        base_alpha = field.rgbas[:, 3].copy()
        field.set_opacities(0.0, np.arange(1, N)).set_glows(1.0, [0]).set_radii(DOT_R_HERO, [0]).set_colors(DATA_HI, [0])
        seed_halo = ambient(glow_sprite(0.55, DATA, peak=0.55).move_to(HOME), amp=0.0, pulse=0.12, seed=2)
        tag, cite = self.hud_tag(), self.hud_cite("kit demo reel  ·  type scale 64 / 44 / 32 / 24 / 18")
        self.add(seed_halo, field, tag, cite)

        # ---- line 0: the type scale as a title card; an underline lands on its word in the same play
        head = put(T("Points of light", "display", parts={"k": "light"}), -SAFE_X, 1.0)
        sub = put(T("one continuous shot", "title", INK_LO), -SAFE_X, 0.0)
        body = put(T("type, light, motion", "body", INK_LO), -SAFE_X, -0.8)
        note = put(T("labels in Inter", "label", MUTED), -SAFE_X, -1.4)
        bar = underline(head.part["k"], of=head, color=FOCUS)
        light = self.word_span(0, "light")
        self.at(0)
        self.play_until(light[1] + 0.5, enter(head, rate_func=late(0.0, 0.45)), enter(sub, rate_func=late(0.25, 0.65)),
                        enter(body, rate_func=late(0.4, 0.8)), enter(note, rate_func=late(0.55, 0.95)),
                        timed(sweep_in(bar, rate_func=MOVE), light[0], light[1] + 0.5),
                        timed(head.part["k"].animate(rate_func=MOVE).set_color(FOCUS), light[0], light[1] + 0.3))

        # ---- line 1: the sampling rhythm with a live count; the title card hands over to a small, pinned title.
        #      The first draws are on the right of the field, clear of the card while it leaves.
        title = self.pin(backstroke(put(T("Points of light", "title"), -SAFE_X, TITLE_Y)))     # pinned over a world that moves
        unit = self.pin(backstroke(put(T("points", "label", MUTED), SAFE_X, TITLE_Y, edge=RIGHT)))
        count = self.pin(backstroke(LiveNumber(N, size="title", reserve=N).place([unit.get_left()[0] - GAP_S, TITLE_Y, 0])))
        self.at(1)
        span = self.line_start(2) - 0.3 - self.now
        rhythm = sampling_rhythm(N - 1, total=span - 0.4, slow=1.0, mid=0.4)
        turn = rng.random(N)                                         # the order of the draws: anywhere in the field
        right = 1 + np.nonzero(home[1:, 0] > HOME[0] + 0.4)[0]
        first = rng.choice(right, 1 + RHYTHM_N_MID, replace=False)   # the slow draws: on the right, clear of the leaving card,
        turn[first] = -1.0 + 0.01 * np.arange(len(first))           # and larger, so each one is seen
        pop = np.full(N, 0.8)
        pop[first] = 2.6
        clock = ValueTracker(0.0)
        count.follow(clock, lambda t: 1 + np.searchsorted(rhythm.starts, t, side="right"))
        self.play(field.appear(rhythm.starts, fade=np.where(np.arange(N - 1) <= RHYTHM_N_MID, 0.6, 0.3), idx=np.arange(1, N),
                               order=turn, opacity=base_alpha[1:], pop=pop, flash=1.0, run_time=span),
                  field.to(radius=DOT_R * 1.1, glow=0.2, idx=[0], span=0.25),
                  clock.animate(rate_func=CLOCK).set_value(span),
                  *[enter(m, rate_func=window(1.0, 1.8, span)) for m in (count, unit)],     # they come with draw 2
                  leave(seed_halo, rate_func=late(0.0, 0.25, EXIT)),
                  hand_over(head, title, rate_func=window(0.3, 1.6, span)),
                  leave(bar, rate_func=window(0.1, 0.7, span, EXIT)),
                  AnimationGroup(*[leave(m, shift=0.15 * LEFT) for m in (sub, body, note)], lag_ratio=0.25,
                                 rate_func=window(0.2, 1.3, span, linear)),
                  run_time=span)

        # ---- line 2: the field regroups into six groups, one after the other (every point goes to a near group)
        angles = np.linspace(0, TAU, GROUPS, endpoint=False)
        centres = RING + np.column_stack([3.6 * np.cos(angles), 1.3 * np.sin(angles), 0 * angles])
        labels = nearest_labels(home, centres, [N // GROUPS] * GROUPS)
        target = np.empty_like(home)
        for k in range(GROUPS):
            members = np.nonzero(labels == k)[0]
            target[members] = match_points(home[members], sunflower_points(len(members), GROUP_R, centres[k], turn=0.7 * k, jitter=0.3, seed=k))
        far = np.linalg.norm(target - home, axis=1)
        self.at(2)
        self.play(field.to(centers=target, lag=0.5, order=labels + 0.6 * far / far.max(), arc=0.45), run_time=3.2)

        # ---- line 3: one group lights up and lifts out to the centre; the rest steps back to 40%; its name is born
        #      where it lands
        hero_k = int(np.argmax(centres[:, 1] - 0.3 * centres[:, 0]))
        hero = field.split(np.nonzero(labels == hero_k)[0])
        halo = glow_sprite(1.9, FOCUS, peak=0.16).move_to(centres[hero_k]).set_opacity(0)
        name = backstroke(T("one group", "label", FOCUS))
        name.next_to(RING + (GROUP_R + 0.4) * DOWN, DOWN, buff=0)       # clear of the runner's orbit
        self.add(halo, hero)
        self.at(3)
        self.play(hero.to(centers=hero.points + (RING - centres[hero_k]), color=FOCUS, glow=0.5, lag=0.35, order="radial", arc=-0.7),
                  field.to(opacity=field.rgbas[:, 3] * 0.4, glow=0.05),
                  halo.animate(rate_func=late(0.3, 1.0, MOVE)).move_to(RING).set_opacity(1),
                  born_from(RING + GROUP_R * DOWN, name, rate_func=late(0.55)), run_time=2.6)
        ambient(halo, amp=0.0, pulse=0.1, seed=5)

        # ---- line 4: the camera pushes in (the title, the count, the tag and the group's name keep their size on
        #      screen); a runner is born from the group and circles it
        t_orbit, t_dive, t_bar = 4.6, 2.0, 4.6
        zero = np.array([RULER_X0, RULER_Y, 0.0])
        runner = Runner(self._path(zero, t_orbit, t_dive, t_bar), color=INK_HI, duration=t_orbit + t_dive + t_bar, tail=1.0,
                        halo=0.45, width=0.085)
        self.at(4)
        self.add(runner)
        runner.start()
        s0 = self.now                                       # the runner's clock is (scene time - s0)
        self.follow_label(name, hero)
        self.play(self.push_in(RING + 0.2 * DOWN, 1.4), enter(runner, rate_func=late(0.0, 0.2)), run_time=3.0)

        # ---- line 5: pull back; the measuring line is drawn, its gate is born from it, and "20%" from the gate; the
        #      runner dives to the zero and becomes the bar. The number is born from the head once it passes 10, so
        #      its digits fill the room kept for 18.5 (no gap after "about")
        value = lambda: RESULT * COUNT(float(np.clip((runner.clock.get_value() - t_orbit - t_dive) / t_bar, 0, 1)))  # noqa: E731
        measure = LiveLength(0, start=zero, unit=UNIT, color=INK, track=GATE + 0.7, gate=GATE, halo=0)
        measure.follow(runner.clock, lambda t: value())
        gate_name = put(T("20%", "label", INK), RULER_X0 + GATE * UNIT, RULER_Y + 1.0, edge=ORIGIN)
        number = backstroke(LiveNumber(RESULT, decimals=1, unit="%", prefix="about", size="title", color=INK_HI, prefix_color=INK_LO,
                                       reserve=RESULT))
        number.follow(runner.clock, lambda t: value())
        placer = lambda m: m.place(measure.tip_point + [-0.55, 0.4, 0])  # noqa: E731   the number rides above the tip
        number.add_updater(placer)
        number.update(0)
        u10 = 1 - (1 - 10 / RESULT) ** (1 / 3)              # when the count passes 10 (COUNT is a cubic ease-out)
        born = s0 + t_orbit + t_dive + u10 * t_bar
        self.at(5)
        self.add(measure, runner)
        self.play(self.pull_back(run_time=2.6), leave(name, rate_func=late(0.0, 0.4, EXIT)), leave(cite, rate_func=late(0.0, 0.5, EXIT)),
                  Create(measure.track, rate_func=late(0.45, 0.9, MOVE)), Create(measure.zero, rate_func=late(0.45, 0.7, MOVE)),
                  born_from(measure.track, measure.gate, rate_func=late(0.65)),
                  born_from(measure.gate, gate_name, rate_func=late(0.8)), run_time=2.6)
        self.play_until(self.line_start(6), timed(born_from(runner.path(np.array([born - s0]))[0], number), born, born + 1.0))

        # ---- line 6: the count lands short of the gate; the head dims, the tail runs in, and the gap is born from
        #      the gate as a soft band
        land = s0 + t_orbit + t_dive + t_bar
        gap = soft_band((GATE - RESULT) * UNIT, 0.5, INK, peak=0.18).move_to(zero + RIGHT * (GATE + RESULT) / 2 * UNIT)
        self.play_until(self.line_start(7), timed(runner.halo.animate(rate_func=MOVE).set_opacity(0.3), land, land + 1.0),
                        timed(born_from(measure.gate, gap), land + 0.3, land + 1.5))
        ambient(gap, amp=0.0, pulse=0.15, seed=9)

        # ---- line 7: hold on the gap (the number and "20%" keep their size on screen), then step back to the result
        number.remove_updater(placer)                       # from here it is placed on screen, beside the tip
        self.follow_label(number, measure.tip)
        self.follow_label(gate_name, measure.gate)
        heads = (title, count, unit)                        # the read-outs step back while we look at the gap
        self.at(7)
        self.play(self.push_in([3.2, -1.7, 0], 1.6, run_time=2.4), *[m.animate(rate_func=MOVE).set_opacity(0.25) for m in heads])
        self.wait(1.8)
        self.play_until(self.scene_duration - 0.4, self.pull_back(), *[m.animate(rate_func=MOVE).set_opacity(1.0) for m in heads])

    @staticmethod
    def _path(zero: np.ndarray, t_orbit: float, t_dive: float, t_bar: float):
        """The runner's path in simulated time: a widening orbit of the lifted group, a dive to the zero of the
        measuring line, then along the line to the result, slowing as a count does."""
        end = zero + RIGHT * RESULT * UNIT

        def orbit(t):
            u = np.clip(t / t_orbit, 0, 1)
            r = 0.22 + 0.95 * u ** 0.8
            a = 0.9 * TAU + 2.35 * TAU * u ** 0.9
            return RING + np.column_stack([1.25 * r * np.cos(a), 0.85 * r * np.sin(a), 0 * u])

        p0 = orbit(np.array([t_orbit]))[0]
        v0 = (p0 - orbit(np.array([t_orbit - 1e-3]))[0]) / 1e-3
        v1 = (COUNT(1e-3) * RESULT * UNIT / 1e-3) / t_bar * RIGHT

        def dive(t):                                        # a cubic that leaves the orbit and meets the line, both smoothly
            u = np.clip((t - t_orbit) / t_dive, 0, 1)[:, None]
            h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
            return h00 * p0 + h10 * t_dive * 0.35 * v0 + h01 * zero + h11 * t_dive * 0.15 * v1   # damped: no loop past the zero

        def along(t):
            u = np.clip((t - t_orbit - t_dive) / t_bar, 0, 1)
            return zero + np.outer(np.array([COUNT(float(x)) for x in u]), end - zero)

        def path(ts):
            ts = np.asarray(ts, dtype=float)
            return np.where((ts < t_orbit)[:, None], orbit(ts), np.where((ts < t_orbit + t_dive)[:, None], dive(ts), along(ts)))

        return path
