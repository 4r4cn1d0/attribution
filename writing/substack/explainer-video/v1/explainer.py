"""Manim scenes for the explainer of "Which Training Data Should We Change to Make an AI Safer?".

Each scene plays its Kokoro narration (narration.py) and starts its visuals at the sentence they
illustrate. Run from the project root with the explainer environment, for example:

    tmp/explainer-venv/bin/manim render -r 1920,1080 --fps 30 --media_dir tmp/explainer-build/media \
        writing/substack/explainer-video/explainer.py S01Title

Numbers on screen are the post's numbers only (gate 20%, about 18.5%, about 14.1%, 1,440, six).
The chart's vertical axis is truncated at 70% and says so.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from manim import (BLUE, BLUE_B, BLUE_E, BOLD, DOWN, GREEN, GREY_B, GREY_C, GREY_D, LEFT, ORIGIN, PI, PURPLE, RED,
                   RIGHT, UL, UP, UR, WHITE, YELLOW, AnimationGroup, Arc, Arrow, Circle, Create, CurvedArrow,
                   DashedLine, Dot, FadeIn, FadeOut, GrowFromCenter, GrowFromEdge, Indicate, LaggedStart, Line,
                   Rectangle, Rotate, RoundedRectangle, Scene, Square, Star, SurroundingRectangle, Text,
                   Transform, VGroup, VMobject, Write, config)

FONT = "Helvetica Neue"
config.background_color = "#111318"
TAIL_SECONDS = 0.6
TIMINGS = json.loads(Path(os.environ.get("EXPLAINER_TIMINGS", "tmp/explainer-build/audio/timings.json")).read_text())


def T(text: str, size: float = 34, color=WHITE, **kw) -> Text:
    return Text(text, font=FONT, font_size=size, color=color, **kw)


def card(text: str, width: float = 2.9, color=BLUE_B, size: float = 24) -> VGroup:
    box = RoundedRectangle(width=width, height=0.62, corner_radius=0.12, color=color, fill_opacity=0.12)
    return VGroup(box, T(text, size).move_to(box))


class Narrated(Scene):
    """A scene with its narration; ``at(i)`` waits until sentence ``i`` starts."""

    key = ""

    def setup(self):
        meta = TIMINGS[self.key]
        self.cues, self.total = meta["starts"], meta["duration"]
        self.add_sound(meta["wav"])

    def now(self) -> float:
        return self.renderer.time

    def at(self, i: int, lead: float = 0.15) -> None:
        gap = self.cues[i] - lead - self.now()
        if gap > 1 / 30:
            self.wait(gap)

    def finish(self) -> None:
        rest = self.total + TAIL_SECONDS - self.now()
        if rest > 1 / 30:
            self.wait(rest)


# ---------------------------------------------------------------- 1
class S01Title(Narrated):
    key = "S01Title"

    def construct(self):
        title = VGroup(T("Which training data should we change", 50),
                       T("to make an AI safer?", 50, t2c={"safer": YELLOW})).arrange(DOWN, buff=0.3)
        sub = T("Notes from an ongoing research project", 26, GREY_B).next_to(title, DOWN, buff=0.7)
        self.at(0)
        self.play(FadeIn(sub, shift=0.2 * UP), run_time=1.2)
        self.at(1)
        self.play(Write(title), run_time=2.6)
        self.finish()


# ---------------------------------------------------------------- 2
class S02Decision(Narrated):
    key = "S02Decision"

    def construct(self):
        rect = RoundedRectangle(width=2.0, height=1.1, corner_radius=0.15, color=BLUE, fill_opacity=0.15)
        model = VGroup(rect, T("model", 30).move_to(rect)).move_to([-5.3, 2.3, 0])
        dots = VGroup(*[Circle(radius=0.17, color=WHITE, fill_color=GREY_D, fill_opacity=1, stroke_width=2)
                        for _ in range(10)]).arrange(RIGHT, buff=0.22).move_to([0.4, 2.3, 0])
        test_label = T("safety test", 24, GREY_B).next_to(dots, UP, buff=0.25)
        fails = {1, 3, 6, 8}
        fail_label = T("fails again and again", 22, RED).next_to(dots, DOWN, buff=0.25)

        self.at(0)
        self.play(FadeIn(model), FadeIn(test_label), LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.08),
                  run_time=1.4)
        self.play(*[d.animate.set_fill(RED if i in fails else GREEN) for i, d in enumerate(dots)], FadeIn(fail_label),
                  run_time=1.0)

        grid = VGroup(*[Square(0.32, color=BLUE_B, stroke_width=1.5, fill_color=BLUE_E, fill_opacity=0.7)
                        for _ in range(32)]).arrange_in_grid(rows=4, cols=8, buff=0.08).move_to([-3.4, -1.2, 0])
        grid_label = T("post-training examples", 24, GREY_B).next_to(grid, UP, buff=0.25)
        self.at(1)
        self.play(FadeIn(grid, lag_ratio=0.03), FadeIn(grid_label), run_time=1.4)

        teach = Arrow(grid_label.get_top() + 0.05 * UP, rect.get_bottom(), buff=0.12, color=GREY_B, stroke_width=4)
        teach_label = T("teaches it how to respond", 20, GREY_B).next_to(teach, RIGHT, buff=0.15)
        self.at(2)
        self.play(Create(teach), FadeIn(teach_label), run_time=1.2)

        cols = lambda cs: VGroup(*[grid[r * 8 + c] for r in range(4) for c in cs])
        group_a, group_c = cols([0, 1]), cols([5, 6])
        outline_a = SurroundingRectangle(group_a, color=YELLOW, buff=0.06)
        self.at(3)
        self.play(Create(outline_a), run_time=0.6)
        self.play(group_a.animate.set_opacity(0.12), run_time=0.8)

        outline_c = SurroundingRectangle(group_c, color=YELLOW, buff=0.06)
        self.at(4)
        self.play(Create(outline_c), run_time=0.6)
        self.play(group_c.animate.set_fill(PURPLE, opacity=0.9), run_time=0.8)

        cards = VGroup(card("remove group A"), card("remove group B"), card("replace group C")) \
            .arrange(DOWN, buff=0.25).move_to([3.6, -0.6, 0])
        self.at(5)
        self.play(FadeOut(outline_a), FadeOut(outline_c), LaggedStart(*[FadeIn(c, shift=0.3 * LEFT) for c in cards],
                                                                      lag_ratio=0.25), run_time=1.4)
        question = T("?", 90, YELLOW).next_to(cards, RIGHT, buff=0.35)
        self.at(6)
        self.play(FadeIn(question, scale=0.6), run_time=0.8)

        meter_frame = Rectangle(width=6.0, height=0.36, color=GREY_B).move_to([3.0, -3.25, 0])
        meter_label = T("computation", 22, GREY_B).next_to(meter_frame, LEFT, buff=0.25)
        seg_w = 0.7
        segments = VGroup(*[Rectangle(width=seg_w, height=0.36, stroke_width=0, fill_color=BLUE, fill_opacity=0.85)
                            for _ in range(3)])
        for i, s in enumerate(segments):
            s.move_to(meter_frame.get_left() + RIGHT * (seg_w * (i + 0.5)))
        self.at(7)
        self.play(FadeOut(question), FadeIn(meter_frame), FadeIn(meter_label), run_time=0.6)
        for c, s in zip(cards, segments):
            self.play(Indicate(c, color=YELLOW, scale_factor=1.05), GrowFromEdge(s, LEFT), run_time=0.75)

        results = VGroup(*[VGroup(*[Dot(radius=0.06, color=col) for col in pattern]).arrange(RIGHT, buff=0.08)
                           .next_to(c, RIGHT, buff=0.2)
                           for c, pattern in zip(cards, [(GREEN, RED, GREEN), (RED, RED, GREEN), (GREEN, GREEN, RED)])])
        self.at(8)
        self.play(FadeIn(results, lag_ratio=0.2), run_time=1.0)

        more = T("+ many more options", 22, GREY_B).next_to(cards, DOWN, buff=0.3)
        extra = VGroup(*[Rectangle(width=seg_w, height=0.36, stroke_width=0, fill_color=RED, fill_opacity=0.85)
                         for _ in range(5)])
        for i, s in enumerate(extra):
            s.move_to(meter_frame.get_left() + RIGHT * (seg_w * (i + 3.5)))
        expensive = T("expensive", 24, RED).next_to(meter_frame, UP, buff=0.15).align_to(meter_frame, RIGHT)
        self.at(9)
        self.play(FadeIn(more, lag_ratio=0.2), LaggedStart(*[GrowFromEdge(s, LEFT) for s in extra], lag_ratio=0.3),
                  run_time=1.8)
        self.play(FadeIn(expensive), segments.animate.set_fill(RED), run_time=0.6)
        self.finish()


# ---------------------------------------------------------------- 3
class S03Question(Narrated):
    key = "S03Question"

    def construct(self):
        head = T("The question", 40, YELLOW, weight=BOLD).to_edge(UP, buff=0.7)
        lines = [
            T("A specific safety failure.", 34, t2c={"specific safety failure": YELLOW}),
            T("A set of possible data changes.", 34, t2c={"possible data changes": YELLOW}),
            T("Which change helps most on new tests,", 34, t2c={"most on new tests": YELLOW}),
            T("without fully retraining every option?", 34, t2c={"without fully retraining every option": YELLOW}),
            T("And how uncertain is that choice?", 34, t2c={"how uncertain": YELLOW}),
        ]
        body = VGroup(*lines).arrange(DOWN, buff=0.38, aligned_edge=LEFT).next_to(head, DOWN, buff=0.7)
        self.at(0)
        self.play(FadeIn(head, shift=0.2 * DOWN), run_time=0.8)
        self.at(1)
        self.play(Write(lines[0]), run_time=1.2)
        self.play(Write(lines[1]), run_time=1.2)
        for i, line in zip((2, 3, 4), lines[2:]):
            self.at(i)
            self.play(Write(line), run_time=1.5)
        self.finish()


# ---------------------------------------------------------------- 4
class S04SpecificNew(Narrated):
    key = "S04SpecificNew"

    def construct(self):
        specific = T("specific", 52, YELLOW, weight=BOLD).move_to([-3.6, 2.7, 0])
        new = T("new", 52, YELLOW, weight=BOLD).move_to([3.4, 2.7, 0])
        self.at(0)
        self.play(FadeIn(specific, shift=0.2 * DOWN), FadeIn(new, shift=0.2 * DOWN), run_time=1.0)

        define = VGroup(T("a failure that we can", 26), T("define and measure", 26, YELLOW)) \
            .arrange(DOWN, buff=0.12).next_to(specific, DOWN, buff=0.45)
        self.at(1)
        self.play(FadeIn(define, shift=0.2 * UP), run_time=1.0)

        dots = VGroup(*[Dot(radius=0.12, color=WHITE) for _ in range(16)]).arrange(RIGHT, buff=0.22) \
            .next_to(new, DOWN, buff=0.7)
        self.at(2)
        self.play(FadeIn(dots, lag_ratio=0.05), run_time=0.8)
        left, right = dots[:8], dots[8:]
        left_target = VGroup(*[Dot(radius=0.12) for _ in range(8)]).arrange_in_grid(rows=2, cols=4, buff=0.22) \
            .move_to([-2.6, -1.0, 0])
        right_target = VGroup(*[Dot(radius=0.12) for _ in range(8)]).arrange_in_grid(rows=2, cols=4, buff=0.22) \
            .move_to([2.6, -1.0, 0])
        self.play(*[d.animate.move_to(t).set_color(BLUE) for d, t in zip(left, left_target)],
                  *[d.animate.move_to(t).set_color(GREY_B) for d, t in zip(right, right_target)], run_time=1.4)
        used = T("used to choose", 24, BLUE).next_to(left_target, DOWN, buff=0.3)
        held = T("held back", 24, GREY_B).next_to(right_target, DOWN, buff=0.3)
        vault = SurroundingRectangle(right_target, color=GREY_B, buff=0.25)
        self.play(FadeIn(used), FadeIn(held), Create(vault), run_time=0.9)

        high = Rectangle(width=2.4, height=0.3, stroke_width=0, fill_color=GREEN, fill_opacity=0.9) \
            .next_to(used, DOWN, buff=0.35)
        low = Rectangle(width=0.55, height=0.3, stroke_width=0, fill_color=RED, fill_opacity=0.9) \
            .next_to(held, DOWN, buff=0.35).align_to(high, UP)
        low.align_to(held, LEFT)
        caption = T("good at fixing only the test that we look at", 26, RED).to_edge(DOWN, buff=0.45)
        self.at(3)
        self.play(GrowFromEdge(high, LEFT), run_time=0.9)
        self.play(GrowFromEdge(low, LEFT), run_time=0.7)
        self.play(FadeIn(caption, shift=0.2 * UP), run_time=0.8)
        self.finish()


# ---------------------------------------------------------------- 5
class Dial(VGroup):
    def __init__(self, label: str, value: float, color, **kw):
        super().__init__(**kw)
        self.radius = 1.15
        self.arc = Arc(radius=self.radius, start_angle=0, angle=PI, color=GREY_B, stroke_width=5)
        ticks = VGroup(*[Line(ORIGIN, 0.15 * RIGHT, color=GREY_B).rotate(a, about_point=ORIGIN)
                         .shift((self.radius - 0.15) * np.array([np.cos(a), np.sin(a), 0]))
                         for a in np.linspace(0, PI, 7)])
        self.value = value
        angle = PI * (1 - value)
        self.needle = Line(ORIGIN, (self.radius - 0.2) * np.array([np.cos(angle), np.sin(angle), 0]),
                           color=color, stroke_width=7)
        hub = Dot(ORIGIN, radius=0.08, color=WHITE)
        self.label = T(label, 22, GREY_B).next_to(self.arc, DOWN, buff=0.35)
        self.add(self.arc, ticks, self.needle, hub, self.label)

    def turn_to(self, value: float, color):
        delta = PI * (self.value - value)
        self.value = value
        return AnimationGroup(Rotate(self.needle, angle=delta, about_point=self.arc.get_arc_center()),
                              self.needle.animate.set_color(color))


class S05SideEffects(Narrated):
    key = "S05SideEffects"

    def construct(self):
        harm = Dial("harmful compliance", 0.85, RED).move_to([-4.3, 0.4, 0])
        refuse = Dial("refusals of harmless questions", 0.2, GREEN).move_to([0, 0.4, 0])
        skill = Dial("capability on earlier tasks", 0.8, GREEN).move_to([4.3, 0.4, 0])
        top = T("too often complies with a clearly harmful request", 26, GREY_B).to_edge(UP, buff=0.6)

        self.at(0)
        self.play(FadeIn(harm), FadeIn(top), run_time=1.0)
        self.at(1)
        self.play(harm.turn_to(0.25, GREEN), run_time=1.4)

        side = T("side effects?", 30, YELLOW).move_to([2.15, 2.5, 0])
        self.at(2)
        self.play(FadeIn(refuse), FadeIn(skill), FadeIn(side), run_time=1.0)

        q1 = T("?", 46, RED).next_to(refuse.arc, UR, buff=0.05)
        self.at(3)
        self.play(refuse.turn_to(0.65, RED), FadeIn(q1), run_time=1.3)
        q2 = T("?", 46, RED).next_to(skill.arc, UR, buff=0.05)
        self.at(4)
        self.play(skill.turn_to(0.4, RED), FadeIn(q2), run_time=1.3)

        bottom = T("A lower failure rate on one measure is only part of the result.", 28) \
            .to_edge(DOWN, buff=0.55)
        self.at(5)
        self.play(FadeIn(bottom, shift=0.2 * UP), run_time=1.0)
        self.finish()


# ---------------------------------------------------------------- 6
class S06LookBackWhatIf(Narrated):
    key = "S06LookBackWhatIf"

    def construct(self):
        divider = DashedLine([0, 3.4, 0], [0, -3.4, 0], color=GREY_D)
        self.at(0)
        self.play(Create(divider), run_time=0.8)

        bad = VGroup(RoundedRectangle(width=2.4, height=0.7, corner_radius=0.12, color=RED, fill_opacity=0.15),
                     T("bad answer", 24, RED))
        bad[1].move_to(bad[0])
        bad.move_to([-3.5, 1.9, 0])
        grid = VGroup(*[Square(0.34, color=BLUE_B, stroke_width=1.5, fill_color=BLUE_E, fill_opacity=0.7)
                        for _ in range(24)]).arrange_in_grid(rows=4, cols=6, buff=0.08).move_to([-3.5, -0.6, 0])
        linked = [grid[i] for i in (2, 9, 16)]
        arrows = VGroup(*[Arrow(bad.get_bottom(), sq.get_top(), buff=0.05, color=YELLOW, stroke_width=3,
                                max_tip_length_to_length_ratio=0.12) for sq in linked])
        self.at(1)
        self.play(FadeIn(bad), FadeIn(grid, lag_ratio=0.02), run_time=1.0)
        self.play(LaggedStart(*[Create(a) for a in arrows], lag_ratio=0.25),
                  *[sq.animate.set_fill(YELLOW, opacity=0.8) for sq in linked], run_time=1.2)

        which = T("remove which, to improve future answers?", 22, GREY_B).next_to(grid, DOWN, buff=0.4)
        self.at(2)
        self.play(FadeIn(which), run_time=0.9)

        back = T("looking back", 32, YELLOW, weight=BOLD).move_to([-3.5, 3.2, 0])
        self.at(3)
        self.play(FadeIn(back, shift=0.2 * RIGHT), run_time=0.9)

        start = Dot([0.9, 0.6, 0], color=WHITE)
        stem = Line([0.9, 0.6, 0], [2.5, 0.6, 0], color=WHITE)
        branch_up = Line([2.5, 0.6, 0], [5.9, 1.8, 0], color=GREEN)
        branch_down = Line([2.5, 0.6, 0], [5.9, -0.6, 0], color=GREY_B)
        change = T("change these examples", 20, GREY_B).next_to(stem, DOWN, buff=0.2)
        future = T("future answers?", 24, GREEN).next_to(branch_up.get_center(), UP, buff=0.4)
        what_if = T("what if", 32, YELLOW, weight=BOLD).move_to([3.5, 3.2, 0])
        self.at(4)
        self.play(FadeIn(what_if, shift=0.2 * LEFT), FadeIn(start), Create(stem), FadeIn(change), run_time=1.0)
        self.play(Create(branch_up), Create(branch_down), FadeIn(future), run_time=1.1)

        right_box = SurroundingRectangle(VGroup(what_if, start, branch_up, branch_down, change), color=YELLOW,
                                         buff=0.3)
        this = T("this research", 26, YELLOW).next_to(right_box, DOWN, buff=0.25)
        self.at(5)
        self.play(Create(right_box), FadeIn(this),
                  VGroup(bad, grid, arrows, which, back).animate.set_opacity(0.3), run_time=1.2)
        self.finish()


# ---------------------------------------------------------------- 7
class S07Cost(Narrated):
    key = "S07Cost"

    def construct(self):
        base_y, unit = -2.9, 0.62
        left = VGroup(*[Rectangle(width=1.6, height=unit, stroke_color="#111318", stroke_width=2,
                                  fill_color=GREY_C, fill_opacity=0.9) for _ in range(8)]).arrange(UP, buff=0)
        left.move_to([-3.4, base_y + 4 * unit, 0])
        left_label = T("retrain every option", 24, GREY_B).next_to(left, DOWN, buff=0.25)

        def seg(height, color):
            return Rectangle(width=1.6, height=height, stroke_color="#111318", stroke_width=2, fill_color=color,
                             fill_opacity=0.9)

        x = 1.4
        check = seg(1.24, BLUE).move_to([x, base_y + 0.62, 0])
        check_label = T("retrain some to check", 20).next_to(check, RIGHT, buff=0.25)
        right_label = T("shortcut", 24, GREY_B).next_to(check, DOWN, buff=0.25)
        self.at(0)
        self.play(GrowFromEdge(left, DOWN), FadeIn(left_label), run_time=1.3)
        self.play(GrowFromEdge(check, DOWN), FadeIn(check_label), FadeIn(right_label), run_time=1.0)

        efficient = T("a more efficient search?", 26, GREEN).move_to([2.6, 3.1, 0])
        self.at(1)
        self.play(FadeIn(efficient), run_time=0.8)

        parts = [("score candidates", BLUE_B), ("estimate uncertainty", PURPLE), ("validate the final choice", GREEN)]
        top, pieces = check.get_top()[1], VGroup()
        self.at(2)
        for name, color in parts:
            piece = seg(0.62, color).move_to([x, top + 0.31, 0])
            label = T(name, 20).next_to(piece, RIGHT, buff=0.25)
            self.play(GrowFromEdge(piece, DOWN), FadeIn(label), run_time=0.8)
            pieces.add(piece, label)
            top += 0.62

        level = DashedLine([-4.6, left.get_top()[1], 0], [4.8, left.get_top()[1], 0], color=RED)
        overrun = seg(left.get_top()[1] - top, RED).move_to([x, (top + left.get_top()[1]) / 2, 0])
        overrun.set_fill(RED, opacity=0.45)
        nohelp = T("as much computation: no help", 26, RED).next_to(level, UP, buff=0.15).shift(1.5 * RIGHT)
        self.at(3)
        self.play(Create(level), run_time=0.8)
        self.play(GrowFromEdge(overrun, DOWN), FadeIn(nohelp), FadeOut(efficient), run_time=1.3)
        self.finish()


# ---------------------------------------------------------------- 8
class S08Status(Narrated):
    key = "S08Status"

    def construct(self):
        a = T("A research question", 54, YELLOW, weight=BOLD).move_to([0, 1.8, 0])
        b = T("not a method that we have shown to work", 34).next_to(a, DOWN, buff=0.45)
        c = VGroup(T("No evidence yet that it is", 28, GREY_B), T("cheaper?   more reliable?", 30),
                   T("than strong existing methods", 28, GREY_B)).arrange(DOWN, buff=0.22).next_to(b, DOWN, buff=0.8)
        self.at(0)
        self.play(FadeIn(a, scale=0.9), run_time=1.0)
        self.at(1)
        self.play(FadeIn(b, shift=0.2 * UP), run_time=1.0)
        self.at(2)
        self.play(LaggedStart(*[FadeIn(m, shift=0.2 * UP) for m in c], lag_ratio=0.35), run_time=1.6)
        self.finish()


# ---------------------------------------------------------------- 9
class S09Pilot(Narrated):
    key = "S09Pilot"

    def construct(self):
        head = T("The work so far is narrower", 34, YELLOW).to_edge(UP, buff=0.5)
        self.at(0)
        self.play(FadeIn(head, shift=0.2 * DOWN), run_time=0.9)

        learner = VGroup(Circle(radius=0.45, color=WHITE), Dot(radius=0.09, color=WHITE),
                         T("tiny learner", 22, GREY_B).shift(0.8 * DOWN)).move_to([-5.6, 0.0, 0])
        self.at(1)
        self.play(FadeIn(learner, scale=0.8), run_time=0.9)

        ya, yb, x0, x_split, x1 = 1.6, -0.5, -4.6, 1.4, 5.9
        line_a = Line([x0, ya, 0], [x1, ya, 0], color=BLUE)
        label_a = T("copy A: learns normally", 22, BLUE).next_to(line_a.get_start(), UP, buff=0.2, aligned_edge=LEFT)
        events_a = VGroup(*[Dot([x, ya, 0], radius=0.07, color=BLUE_B) for x in np.linspace(-3.8, 5.2, 8)])
        runner_a = Dot([x0, ya, 0], radius=0.14, color=BLUE)
        self.at(2)
        self.play(Create(line_a), FadeIn(label_a), FadeIn(events_a), FadeIn(runner_a), run_time=1.2)

        line_b = Line([x0, yb, 0], [x_split, yb, 0], color=YELLOW)
        label_b = T("copy B", 22, YELLOW).next_to(line_b.get_start(), UP, buff=0.2, aligned_edge=LEFT)
        events_b = VGroup(*[Dot([x, yb, 0], radius=0.07, color=YELLOW) for x in np.linspace(-3.8, 0.5, 4)])
        event_x = events_b[1].get_center()[0]
        star = Star(n=5, outer_radius=0.22, color=YELLOW, fill_opacity=1).move_to([event_x, yb + 0.5, 0])
        star_label = T("one event", 20, YELLOW).next_to(star, RIGHT, buff=0.12)
        runner_b = Dot([x0, yb, 0], radius=0.14, color=YELLOW)
        suppressed = T("its learning contribution suppressed", 20, GREY_B).next_to(events_b[1], DOWN, buff=0.3)
        self.at(3)
        self.play(Create(line_b), FadeIn(label_b), FadeIn(events_b), FadeIn(runner_b), FadeIn(star),
                  FadeIn(star_label), run_time=1.1)
        self.play(events_b[1].animate.set_opacity(0.15).scale(1.6), FadeIn(suppressed), run_time=0.9)

        self.at(4)
        self.play(runner_a.animate.move_to([x_split, ya, 0]), runner_b.animate.move_to([x_split, yb, 0]),
                  run_time=1.8)

        diverge = Line([x_split, yb, 0], [x1, yb - 1.0, 0], color=YELLOW)
        later = T("later choices change", 20, YELLOW).next_to(diverge.get_end(), DOWN, buff=0.2) \
            .align_to(diverge.get_end(), RIGHT)
        self.at(5)
        self.play(Create(diverge), runner_a.animate.move_to([x1, ya, 0]), runner_b.animate.move_to(diverge.get_end()),
                  FadeIn(later), run_time=1.6)

        infos = VGroup(*[Arrow(diverge.point_from_proportion(p) + 0.75 * UP, diverge.point_from_proportion(p),
                               buff=0.08, color=GREY_B, stroke_width=3, max_tip_length_to_length_ratio=0.25)
                         for p in (0.3, 0.6, 0.9)])
        info_label = T("different information", 20, GREY_B).next_to(infos, UP, buff=0.1)
        self.at(6)
        self.play(LaggedStart(*[GrowFromEdge(a, UP) for a in infos], lag_ratio=0.25), FadeIn(info_label),
                  run_time=1.2)

        loop = VGroup(T("feedback:", 26, YELLOW), T("choices  →  information  →  learning  →  choices", 26)) \
            .arrange(RIGHT, buff=0.3).to_edge(DOWN, buff=0.85)
        cite = T("starting point: Data Attribution in Adaptive Learning (arXiv 2604.04892)", 16, GREY_C) \
            .to_corner(DOWN + RIGHT, buff=0.25)
        self.at(7)
        self.play(FadeIn(loop, shift=0.2 * UP), FadeIn(cite), run_time=1.3)
        self.finish()


# ---------------------------------------------------------------- 10
class S10Coupling(Narrated):
    key = "S10Coupling"

    def construct(self):
        rng = np.random.default_rng(7)
        palette = [BLUE, YELLOW, GREEN]
        n, ya, yb = 12, 2.2, 0.9
        draws_a = rng.integers(0, 3, n)
        draws_b = rng.integers(0, 3, n)
        row_a = VGroup(*[Square(0.36, stroke_width=0, fill_color=palette[k], fill_opacity=0.9) for k in draws_a]) \
            .arrange(RIGHT, buff=0.16).move_to([0.9, ya, 0])
        row_b = VGroup(*[Square(0.36, stroke_width=0, fill_color=palette[k], fill_opacity=0.9) for k in draws_b]) \
            .arrange(RIGHT, buff=0.16).move_to([0.9, yb, 0])
        lab_a = T("copy A", 24, BLUE).next_to(row_a, LEFT, buff=0.4)
        lab_b = T("copy B", 24, YELLOW).next_to(row_b, LEFT, buff=0.4)
        random_label = T("random choices", 22, GREY_B).next_to(row_a, UP, buff=0.25)
        self.at(0)
        self.play(FadeIn(lab_a), FadeIn(lab_b), FadeIn(random_label),
                  LaggedStart(*[FadeIn(s, scale=0.5) for s in [*row_a, *row_b]], lag_ratio=0.04), run_time=1.6)

        def wobble(amplitude: float, seed: int) -> VMobject:
            r = np.random.default_rng(seed)
            xs = np.linspace(-4.6, 4.6, 46)
            ys = -2.2 + amplitude * r.standard_normal(len(xs))
            return VMobject(color=RED).set_points_as_corners([[x, y, 0] for x, y in zip(xs, ys)])

        axis = Line([-4.8, -2.2, 0], [4.8, -2.2, 0], color=GREY_D)
        noisy = wobble(0.55, 3)
        noisy_label = T("difference between the copies: noisy", 22, RED).next_to(axis, DOWN, buff=0.75)
        self.at(1)
        self.play(Create(axis), Create(noisy), FadeIn(noisy_label), run_time=1.6)

        links = VGroup(*[Line(a.get_bottom(), b.get_top(), color=GREY_B, stroke_width=2) for a, b in zip(row_a, row_b)])
        coordinate = T("coordinate the random choices", 22, GREY_B).next_to(row_b, DOWN, buff=0.3)
        self.at(2)
        self.play(Create(links, lag_ratio=0.1), FadeIn(coordinate), run_time=1.4)
        matched = [Square(0.36, stroke_width=0, fill_color=palette[a if i not in (4, 9) else (a + 1) % 3],
                          fill_opacity=0.9).move_to(sq)
                   for i, (a, sq) in enumerate(zip(draws_a, row_b))]
        self.play(*[Transform(sq, m) for sq, m in zip(row_b, matched)], run_time=1.0)

        coupling = T("coupling", 40, YELLOW, weight=BOLD).next_to(random_label, RIGHT, buff=0.6)
        calm = wobble(0.18, 3).set_color(GREEN)
        calm_label = T("difference between the copies: less noisy", 22, GREEN).move_to(noisy_label)
        self.at(3)
        self.play(FadeIn(coupling, scale=0.8), Transform(noisy, calm), Transform(noisy_label, calm_label),
                  run_time=1.6)

        own = T("each copy still follows its own probabilities", 22, WHITE).move_to(coordinate)
        self.at(4)
        self.play(Transform(coordinate, own), Indicate(row_a, color=WHITE, scale_factor=1.03),
                  Indicate(row_b, color=WHITE, scale_factor=1.03), run_time=1.4)

        only = T("only the pairing changes", 24, YELLOW).next_to(coordinate, DOWN, buff=0.2)
        cite = T("established idea: work on reducing noise in counterfactual estimates (arXiv 2111.06888)", 16,
                 GREY_C).to_corner(DOWN + RIGHT, buff=0.25)
        self.at(5)
        self.play(links.animate.set_color(YELLOW).set_stroke(width=3), FadeIn(only), FadeIn(cite), run_time=1.2)
        self.finish()


# ---------------------------------------------------------------- 11 and 12: one chart
Y_MIN, Y_MAX, Y_BOTTOM, Y_TOP = 70.0, 102.0, -2.7, 2.3


def y_of(percent: float) -> float:
    return Y_BOTTOM + (percent - Y_MIN) / (Y_MAX - Y_MIN) * (Y_TOP - Y_BOTTOM)


BAR_X = {"base": 1.7, "oracle": 3.0, "full": 4.3}


def gate_chart() -> dict:
    x_axis = 0.6
    axis = Line([x_axis, Y_BOTTOM, 0], [x_axis, Y_TOP, 0], color=GREY_B)
    ticks = VGroup()
    for p in (70, 80, 90, 100):
        ticks.add(Line([x_axis - 0.08, y_of(p), 0], [x_axis + 0.08, y_of(p), 0], color=GREY_B),
                  T(f"{p}%", 18, GREY_B).next_to([x_axis - 0.08, y_of(p), 0], LEFT, buff=0.12))
    ylabel = T("variance, compared with the best baseline", 18, GREY_B).rotate(PI / 2) \
        .next_to(ticks, LEFT, buff=0.3)
    truncated = T("axis starts at 70%", 15, GREY_C).next_to(ticks, DOWN, buff=0.25).align_to(axis, RIGHT)

    def bar(x: float, top: float, color) -> Rectangle:
        height = y_of(top) - Y_BOTTOM
        return Rectangle(width=0.9, height=height, stroke_width=0, fill_color=color, fill_opacity=0.85) \
            .move_to([x, Y_BOTTOM + height / 2, 0])

    base_bar = bar(BAR_X["base"], 100, GREY_C)
    base_label = T("best\nbaseline", 17, GREY_B).next_to(base_bar, DOWN, buff=0.2)
    gate = DashedLine([x_axis, y_of(80), 0], [6.9, y_of(80), 0], color=YELLOW, dash_length=0.12)
    gate_label = T("gate: at least 20%\nless variance", 17, YELLOW).next_to([4.95, y_of(80), 0], UR, buff=0.1)
    gate_note = T("in at least one\nconfiguration of\nthe target family", 15, YELLOW) \
        .next_to([4.95, y_of(80), 0], DOWN + RIGHT, buff=0.12)
    oracle_card = card("oracle: best allowed pairing", width=4.1, color=BLUE, size=20).move_to([-4.4, -2.3, 0])
    baselines = VGroup(*[card(f"baseline pairing {i}", width=3.0, color=GREY_C, size=18) for i in range(1, 7)]) \
        .arrange(DOWN, buff=0.12).scale(0.85).move_to([-4.4, 0.6, 0])
    return {"axis": axis, "ticks": ticks, "ylabel": ylabel, "truncated": truncated, "bar": bar,
            "base_bar": base_bar, "base_label": base_label, "gate": gate, "gate_label": gate_label,
            "gate_note": gate_note, "oracle_card": oracle_card, "baselines": baselines}


class S11Gate(Narrated):
    key = "S11Gate"

    def construct(self):
        grid = VGroup(*[Square(0.09, stroke_width=0, fill_color=BLUE_B, fill_opacity=0.8) for _ in range(1440)]) \
            .arrange_in_grid(rows=30, cols=48, buff=0.035).move_to([0, 0.3, 0])
        count = T("1,440 toy configurations", 34, WHITE).next_to(grid, UP, buff=0.3)
        steps = T("one- or two-step continuations", 24, GREY_B).next_to(grid, DOWN, buff=0.3)
        self.at(0)
        self.play(FadeIn(grid, lag_ratio=0.0015), FadeIn(count), run_time=1.8)
        self.play(FadeIn(steps), run_time=0.6)

        c = gate_chart()
        self.at(1)
        self.play(FadeOut(VGroup(grid, count, steps)), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(b, shift=0.2 * RIGHT) for b in c["baselines"]], lag_ratio=0.12),
                  FadeIn(c["oracle_card"], shift=0.2 * RIGHT), run_time=1.6)

        tiny = T("in this tiny setup", 18, BLUE_B).next_to(c["oracle_card"], DOWN, buff=0.15)
        self.at(2)
        self.play(Indicate(c["oracle_card"], color=BLUE, scale_factor=1.05), FadeIn(tiny), run_time=1.1)

        self.at(3)
        self.play(Create(c["axis"]), FadeIn(c["ticks"]), FadeIn(c["ylabel"]), FadeIn(c["truncated"]),
                  GrowFromEdge(c["base_bar"], DOWN), FadeIn(c["base_label"]), run_time=1.4)
        self.play(Create(c["gate"]), FadeIn(c["gate_label"]), FadeIn(c["gate_note"]), run_time=1.2)

        def wiggle(amplitude: float, seed: int, y: float) -> VMobject:
            r = np.random.default_rng(seed)
            xs = np.linspace(4.3, 6.8, 26)
            return VMobject(color=GREY_B).set_points_as_corners([[x, y + amplitude * r.standard_normal(), 0]
                                                                 for x in xs])

        hi, lo = wiggle(0.16, 11, 3.2), wiggle(0.04, 11, 2.55)
        hi_l = T("more variance", 16, GREY_B).next_to(hi, LEFT, buff=0.15)
        lo_l = T("less variance", 16, GREY_B).next_to(lo, LEFT, buff=0.15)
        self.at(4)
        self.play(Create(hi), Create(lo), FadeIn(hi_l), FadeIn(lo_l), run_time=1.4)
        self.finish()


class S12Result(Narrated):
    key = "S12Result"

    def construct(self):
        c = gate_chart()
        tiny = T("in this tiny setup", 18, BLUE_B).next_to(c["oracle_card"], DOWN, buff=0.15)
        self.add(c["baselines"], c["oracle_card"], tiny, c["axis"], c["ticks"], c["ylabel"], c["truncated"],
                 c["base_bar"], c["base_label"], c["gate"], c["gate_label"], c["gate_note"])

        oracle_bar = c["bar"](BAR_X["oracle"], 100, BLUE)
        oracle_target = c["bar"](BAR_X["oracle"], 81.5, BLUE)
        oracle_value = T("about\n18.5% less", 18, BLUE_B).next_to(oracle_target, UP, buff=0.12)
        oracle_name = T("oracle", 17, BLUE_B).next_to(oracle_target, DOWN, buff=0.2)
        self.at(0)
        self.play(FadeIn(oracle_bar), FadeIn(oracle_name), run_time=0.8)
        self.play(Transform(oracle_bar, oracle_target), run_time=1.6)
        self.play(FadeIn(oracle_value), run_time=0.6)

        full_bar = c["bar"](BAR_X["full"], 100, PURPLE)
        full_target = c["bar"](BAR_X["full"], 85.9, PURPLE)
        full_value = T("about\n14.1% less", 18, PURPLE).next_to(full_target, UP, buff=0.12)
        full_name = T("full\nsuppression", 17, PURPLE).next_to(full_target, DOWN, buff=0.2)
        self.at(1)
        self.play(FadeIn(full_bar), FadeIn(full_name), run_time=0.7)
        self.play(Transform(full_bar, full_target), run_time=1.4)
        self.play(FadeIn(full_value), run_time=0.6)

        best = T("best cases, not averages", 24, WHITE).move_to([3.7, 3.5, 0])
        self.at(2)
        self.play(FadeIn(best, shift=0.2 * DOWN), run_time=0.8)

        cost = T("the oracle's computation: not a practical shortcut", 20, GREY_B).next_to(best, DOWN, buff=0.15)
        self.at(3)
        self.play(FadeIn(cost, shift=0.2 * DOWN), run_time=0.9)

        stamp_box = RoundedRectangle(width=3.6, height=0.95, corner_radius=0.1, color=RED, stroke_width=6)
        stamp = VGroup(stamp_box, T("gate not met", 36, RED, weight=BOLD).move_to(stamp_box)) \
            .rotate(0.08).move_to([-4.4, 3.05, 0])
        self.at(4)
        self.play(FadeIn(stamp, scale=1.3), run_time=0.8)
        self.finish()


# ---------------------------------------------------------------- 13
class S13NotShown(Narrated):
    key = "S13NotShown"

    def construct(self):
        a = T("tells us something about the approach that we tested", 30, GREEN).move_to([0, 2.9, 0])
        b = T("does not answer the larger question", 30).next_to(a, DOWN, buff=0.35)
        self.at(0)
        self.play(FadeIn(a, shift=0.2 * DOWN), run_time=1.0)
        self.at(1)
        self.play(FadeIn(b, shift=0.2 * DOWN), run_time=1.0)

        head = T("The pilot did not:", 26, GREY_B).next_to(b, DOWN, buff=0.7).align_to(b, LEFT).shift(0.6 * LEFT)
        items = [T("choose batches of training data to remove or replace", 28),
                 T("test safety improvements in a large language model", 28),
                 T("show a saving in total computation", 28)]
        VGroup(*items).arrange(DOWN, buff=0.4, aligned_edge=LEFT).next_to(head, DOWN, buff=0.35, aligned_edge=LEFT) \
            .shift(0.4 * RIGHT)
        for i, item in zip((2, 3, 4), items):
            self.at(i)
            if i == 2:
                self.play(FadeIn(head), run_time=0.5)
            strike = Line(item.get_left() + 0.1 * LEFT, item.get_right() + 0.1 * RIGHT, color=RED, stroke_width=4)
            self.play(FadeIn(item, shift=0.2 * RIGHT), run_time=0.7)
            self.play(Create(strike), item.animate.set_opacity(0.55), run_time=0.6)

        note = T("The pilot is not evidence on the main question.", 26, YELLOW).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(note, shift=0.2 * UP), run_time=0.9)
        self.finish()


# ---------------------------------------------------------------- 14
class S14Next(Narrated):
    key = "S14Next"

    def construct(self):
        head = T("Next: three questions", 36, YELLOW, weight=BOLD).to_edge(UP, buff=0.5)
        qs = [T("1.  Which safety failure should we study?", 28),
              T("2.  Which candidate changes should we compare?", 28),
              T("3.  What evidence makes a recommendation trustworthy?", 28)]
        VGroup(*qs).arrange(DOWN, buff=0.3, aligned_edge=LEFT).next_to(head, DOWN, buff=0.5)
        self.at(0)
        self.play(FadeIn(head, shift=0.2 * DOWN), run_time=0.8)
        for i, q in zip((1, 2, 3), qs):
            self.at(i)
            self.play(FadeIn(q, shift=0.2 * RIGHT), run_time=0.8)

        line = Line([-5.0, -2.3, 0], [1.0, -2.3, 0], color=GREY_D)
        better = T("better", 16, GREY_C).next_to(line.get_end(), DOWN, buff=0.1)

        def interval(lo: float, hi: float, est: float, y: float, color, name: str) -> VGroup:
            seg = Line([lo, y, 0], [hi, y, 0], color=color, stroke_width=6)
            caps = VGroup(Line([lo, y - 0.12, 0], [lo, y + 0.12, 0], color=color),
                          Line([hi, y - 0.12, 0], [hi, y + 0.12, 0], color=color))
            return VGroup(seg, caps, Dot([est, y, 0], radius=0.09, color=color), T(name, 20, color)
                          .next_to([lo, y, 0], LEFT, buff=0.2))

        opt_a = interval(-3.6, -0.4, -2.0, -1.55, BLUE, "option A")
        opt_b = interval(-3.0, 0.2, -1.4, -1.95, GREEN, "option B")
        call = T("too close to call", 28, YELLOW).move_to([-2.0, -3.0, 0])
        self.at(4)
        self.play(Create(line), FadeIn(better), FadeIn(opt_a), FadeIn(opt_b), run_time=1.2)
        self.play(FadeIn(call, scale=0.9), run_time=0.8)

        ranking = VGroup(T("a confident ranking", 24), T("1. option B   2. option A", 24, GREY_B),
                         T("with no reliable basis", 24)).arrange(DOWN, buff=0.15).move_to([4.2, -2.1, 0])
        strike = Line(ranking.get_corner(UL) + 0.15 * LEFT, ranking.get_corner(DOWN + RIGHT) + 0.15 * RIGHT,
                      color=RED, stroke_width=5)
        self.at(5)
        self.play(FadeIn(ranking), run_time=0.8)
        self.play(Create(strike), ranking.animate.set_opacity(0.5), Indicate(call, color=YELLOW), run_time=1.0)
        self.finish()


# ---------------------------------------------------------------- 15
class S15Close(Narrated):
    key = "S15Close"

    def construct(self):
        a = VGroup(T("AI assistants help with", 32, GREY_B), T("implementation and critique", 38)) \
            .arrange(DOWN, buff=0.2).move_to([0, 1.6, 0])
        self.at(0)
        self.play(FadeIn(a, shift=0.2 * UP), run_time=1.0)
        b = VGroup(T("Their suggestions must survive checks against", 28, GREY_B),
                   T("the papers and the results", 32, YELLOW)).arrange(DOWN, buff=0.15).next_to(a, DOWN, buff=0.7)
        self.at(1)
        self.play(FadeIn(b, shift=0.2 * UP), run_time=1.0)
        final = T("The project is still underway.", 44, WHITE, weight=BOLD)
        small = T("Which training data should we change to make an AI safer?", 22, GREY_C) \
            .next_to(final, DOWN, buff=0.5)
        self.at(2)
        self.play(FadeOut(a), FadeOut(b), run_time=0.6)
        self.play(FadeIn(final, scale=0.95), FadeIn(small), run_time=1.0)
        self.finish()


SCENE_ORDER = ["S01Title", "S02Decision", "S03Question", "S04SpecificNew", "S05SideEffects", "S06LookBackWhatIf",
               "S07Cost", "S08Status", "S09Pilot", "S10Coupling", "S11Gate", "S12Result", "S13NotShown",
               "S14Next", "S15Close"]
