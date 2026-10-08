# Final script and storyboard: explainer video, version 2

Design panel, synthesis, revised in rounds 1 to 3 after four reviews each (fidelity, picture honesty, craft,
voice). Round 3 applies the round-2 reviews with the orchestrator's rulings (`design/DECISIONS-round3.md`).
Status: a design for the user's review. Nothing here is rendered, and no audio was made.
Base treatment: **A (one world)**. The scene order and the cue grammar come from B. The economy, the type events
and the ruler come from D. One sentence, the second curve, the step glyphs and the build guard come from C.
The machine-readable narration is `design/script.json`; its lines are identical to the lines in section 5. One
generator writes both files from one copy of the narration, so they cannot differ.

All positions are in Manim frame units (frame 14.22 x 8; safe area |x| <= 6.4, |y| <= 3.4). All times are
estimates from the narration builder's own text analysis (13.4 phonemes a second for `af_heart`). The build takes
its cues from word timings (column "Cue" of every beat table), not from these seconds.

**What changed in round 3** (the reasons are in the round-2 reviews, `design/_results.json`, key
`last_verification`, and in the rulings; what was not applied is in section 8, point 15). Earlier rounds'
changes are part of the text; section 8, point 14 keeps the review points that round 1 did not apply.

- Voice. S05's framing question "What have we actually tested?" is gone. S04 line 1 has the post's "to improve
  future answers" again, and no "the". S03 line 2 ends "tests held back while we choose the change". S09 line 5
  is "The pilot did not meet the condition for advancing." (the words of S08 line 3), so the longer test has one
  spoken name. S02 line 2 has the post's "repeating the process". S07 line 1 says "these futures". S06 line 1
  has a comma and a 0.3 s pause after "learner", at speed 0.9. A third stress mark, on "that" in S11 line 3.
  Five pauses after lines and three pauses inside lines changed. 597 words by the builder's count, 612 as read; the
  binding limit is 620 as read (ruling 1).
- The result (S09). No gap band: the gap is dark track, and a build check measures the dark run. The head's glow
  has radius 0.12 and breathes in opacity only; the condition line has no glow. `best baseline` sits under
  track 2. The 14.1% case is the lower lit unit, in the lower part of the family, and its thread goes to its own
  moving head; both runs have one speed. `target family` stays until line 3, `full suppression` stays on the
  14.1% row to the end, and `strongest` names the two lit units. `20%` is written `≥20%`, one token that keeps
  "at least". On "averages" the whole field dims evenly.
- The field (S08). The S07 picture is baked and dissolves in place; after a 0.3 s beat the field blooms from its
  own centre. The disc never parts. The family is an irregular outline, and no share of the record is drawn. No
  highlight hops among the six glyphs. The tag stays on until "The condition".
- The web (S09): uncountable soft fans and one woven sheet, under the tag from its first frame to the end of
  its fold.
- Coupling (S07). Two pairings (straight, crossed). An index schedule makes both piles end exactly at their
  counts. The ghost edges fade in the last 0.8 s, and no rim brightens. When the bars go back to step 1, the dim
  heads go back with them. The comparison is a plain segment from head to head.
- The ending (S11). The two ranges are dotted gold intervals between the model and the inner row; the beams end
  at the model's rim; the held-back row stays shaded and untouched; no `held back` label. Line 3 moves.
- S04: seven marked points with no ring; a core disc of the model hides the threads. S05: no bead; on "cheaply"
  the lane stays empty and still.
- For the build: clock-driven `world.clock_move` and `world.jitter` for every motion that crosses a cue; the
  shade, TEST-IN and STARE inside the safe area; exact emblem coordinates; a lamp that only changes opacities;
  default durations (rule 18 of 1.2); the exact red lights of every retrain and round.
- Closing pass of round 3 (the seven medium issues of the confirmation reviews; section 8, point 16). Two thin
  threads tie `strongest` to the two lit units, so it does not name the field or the outline. The dark-run check
  compares P09 with a control render of the bare track, not with the background. The emblem keeps the family
  mark round its two white dots. `≥20%` is one string with no space, so the kit counts one word. The flash on
  "confident" in S11 is gone. Four rows state their windows: S02's return of the world, S09's track 2, the
  birth of the S11 ranges and the end of the S07 hairline jitter. No narration line changed.

---

## 1. Rules for this video

### 1.1 Fidelity (these do not bend)

1. **Claims.** The voice and the screen make only claims that the post makes. Each line of section 5 names its
   entries of `design/claims-ledger.md`. A line states a claim at the post's strength or more weakly. One line
   is a framing question with no claim of its own; it presupposes only what the post says (S09 line 1 rests on
   C60 and C65).
2. **Numerals.** Only these are spoken or shown: `1,440`; `six`; `20%`; `about 18.5%`; `about 14.1%`;
   `one- or two-step`. No counter runs. No percentage runs. Each numeral lands whole, on its word: all its glyphs
   at once (`FadeIn` with `scale=0.92` and no `lag_ratio`), never glyph by glyph, which would read as counting.
   `about` is on screen with `18.5%` and with `14.1%` from their first frame, at serif 32 in both rows. `20%` is
   always written `≥20%`, one token in serif 44: its sign carries the post's "at least" (H05) for as long as
   20% is on screen, so the hedge cannot leave the number and cannot attach to a result. It is one string with
   no space, `T("≥20%")`, because the kit counts words with `split()` and any space between the sign and the
   number would count as a second word (section 8, point 9). It sits right of the condition line, with its
   baseline 0.5 from the row of each result numeral. Every other quantity is a length,
   an area or a spread with no number and no axis numbers.
3. **Status.** The project is a research question, not a method shown to work. No shape is drawn for a method
   that works, for "existing methods", or for a shortcut that is cheaper. At rest the shortcut is an empty lane,
   and while the voice says "more cheaply" nothing moves on it.
4. **The pilot is narrower work.** It is in another place of the picture, behind a boundary. No thread joins it
   to the pool, the model, the safety test or the cost, and no light travels between them: the lamp of S10 opens
   over the question and fades there. While the camera is on the pilot, the question above the boundary is dim,
   has no red and has no cost floor. The voice says what the pilot did not do (S10 line 2), that the results
   were best cases and not averages, and that they came from an oracle whose own computation was not a
   practical shortcut (S09 line 4).
5. **Papers.** One citation is shown: `including in "work on reducing noise in counterfactual estimates" (arXiv
   2111.06888)`. The quoted title and the arXiv number are exact; "including in" is the post's own lead-in (C54,
   H13), in the citation's style, so that the paper reads as one example of coupling and not as its source. The
   other paper ("Data Attribution in Adaptive Learning", arXiv 2604.04892) is not shown, because the sentence
   that it belongs to is not spoken (section 8, point 5).
6. **Honest pictures.**
   - The tag `illustration` is on for every invented outcome. In S08 it stays on until the condition line draws
     ("The condition"), so the field's drawing, the six glyphs and the oracle's flicker sit under it. It is off
     from there to the end of the result scene (S09), where the line, the scale and the numbers are the post's,
     except while the oracle's web is on screen: on from the web's first frame ("oracle") to the end of its fold.
     It is on again from the lamp's first frame in S10, so that the emblem lands untagged.
   - The result is a length on a scale of `variance reduction` that starts at a zero tick named `best baseline`;
     the name sits at the foot of the tick, under both tracks. The condition line is at 20%. The scale is 10
     units long, so the gap is 0.75 units (about 101 px at 1080p) with no zoom. The gap is dark track: only
     the bare hairline of track 1, which nothing fills and nothing lights. The head's glow has radius 0.12 and
     the line has no glow, so neither eats into the gap, and a build check measures the dark run against a
     control render of the bare track (3.6). The camera does not lean in. The marker runs
     at one steady speed and stops with a 0.6 s ease-out: no creep toward the line. Both runs have the same
     speed.
   - Results, the condition line, the family outline and the lit units are white or grey. They are never gold
     (the hue of a data change) and never red. No unit is lit before the result names it.
   - Coupling is a mechanism: one shared random number through two different bars. Each copy keeps its own
     probabilities; piles of dots prove it, and under every form they end exactly at each bar's own counts. Two
     pairings are shown: one a hair better than no coordination (straight) and one about the same (crossed). The
     band of the comparison answers each pairing by an amount that the code computes from the toy. The straight
     pairing lowers the variance by 5% to 9.5%, and the crossed pairing changes it by 3% or less. The build stops
     otherwise (section 3.7).
   - "Associated with" is not "caused by": the voice says "does not automatically" (S04 line 1), the label says
     `associated with this answer`, the threads pass behind the model's core, and no marked point turns gold or
     lifts by itself. The seven marked points have no ring, because a thin white ring means "chosen" (S02).
   - No word of judgement about the result: no "close", no "almost", no "failed", no stamp, no red, no lit gap.
   - Details of the project record keep a picture from being wrong. They are never said and never shown as a
     claim (no method names, no parameter values, no family name, no size of the family, no share of the field,
     no kind of baseline, no count of the oracle's futures, no winner among the baselines).
7. **Licence.** Techniques from 3b1b/videos, no code. No Pi creature, no 3Blue1Brown logo.

### 1.2 Rules for every scene

1. Every scene is a `Narrated` scene. Its first frame is the closing pose of the scene before it (section 4).
   The stage is set with `world.pose(...)` before the first cue. No scene starts on an empty frame.
2. **Cues.** Each beat row has one cue in the kit's 0-based line numbering (column "Cue"): `at(i)`,
   `at_word(i, "w")` or `line_end(i)`; `at(0, lead=0.4)` is the first frame of the scene, and `at_word` takes
   the first time that the word occurs in the line (the kit's default). In the column "Line"
   and in the "Lines to speak" tables, lines are numbered from 1. So "line 3" is `at(2)`.
3. **One row, one play.** A beat row is one play: `play_until(` the next row's cue `)`, or to the end of the
   scene for the last row. Its motions sit inside that play with `window()` or `late()`; a time in parentheses
   is a window inside the play. The bold word is where the key change lands. A motion that must end on a word is
   scheduled backwards from that word. At most one new event for each 1.2 s of speech. The first time a process
   is shown, it takes 1.5 s or more. Snaps (`min_time=0`) are allowed only for S03 "define", S11 "ranking" and
   the S11 flips.
   **Exception: clock-driven motion.** The six camera moves, the S07 stream of futures, the second run of S09 and
   the seeded jitters of 3.12 (pointer and hairline jumps, the twin's flicker, the halo in the family) are not
   plays. Each is an updater that reads the film clock (`world.clock_move`, `world.jitter`, `Runner.start()`;
   section 3.9). It starts at its cue or at its computed time and stops at its stated end time, whatever rows it
   crosses, so no play squeezes it and no row end cuts it short. A row says where such a motion starts and ends.
4. **One slowly, a few faster, then many.** The first test, the first retrain, the first random future and the
   first unit of the field each take 1 to 2.5 s. The next few take under 1 s. Then they run.
5. Nothing freezes. In a hold, the pool drifts, the needles tremble, lit lights breathe and each glow pulses.
   A "hold" below means "no new event".
6. **Exact poses.** In the last 12 frames of a scene all idle motion eases to its rest value. In the first 12
   frames of the next scene it eases in again. So a closing pose is one exact picture.
7. **No reset inside a punchline pause.** A supposed case is undone in the first second of the next scene.
8. **Hollow or solid.** Solid means "it happened in the picture". Hollow, dashed or dotted means "only supposed",
   "not asked" or "not done". Every solid thing that was only a "could" turns hollow again.
9. **Soft or sharp.** Soft means "not definite". Sharp means "definite". The lights blur for "Make the model
   safer" and snap sharp on "define". At the end two dotted ranges (supposed, not definite) snap into a sharp
   ranking and melt back.
10. **Dim, do not delete.** A lasting object goes to 10% to 35% and comes back in the same place. One exception:
    the cost floor (line, band, end tick, dials and lane) fades to 0 whenever the camera is at STARE, SPECK, P or
    GAP. At STARE it would sit in the band under y = -2.9 that belongs to the tag; in the pilot's frames it would
    run beside the result tracks. It fades during the move that leaves W and returns during the move back.
11. **Born from.** A new thing comes out of the thing that it belongs to (`born_from`, `hand_over`). A lone
    fade-in is the exception, and the rows say so.
12. **Words on screen.** At most 12 at one time (the tag and the citation do not count). Never the sentence that
    the voice is saying. A label has 1 to 4 words, sits 0.2 to 0.25 from its object, has the object's colour, and
    has a dark backstroke where it lies on art. It arrives on its word and leaves when the next idea starts.
    No text is rotated. No text moves while it must be read. Two exceptions to the distance: a label that names
    the pool or a spread of its parts (`post-training examples`, `data change`, `associated with this answer`)
    uses the pool's label slot; and `strongest` (S09) stands left of the parked field, the only free place,
    with two thin threads from its right end to the two units that it names (3.10).
13. **Size under a camera move.** Every label keeps its size class on screen and follows its object
    (`follow_label`, section 3.9). A label's place is given at the station where it is first read. Lines that
    must stay thin use `keep_stroke`.
14. **Colour.** At most three hues in a frame (in the question: blue, gold, red; in the pilot: blue and violet)
    plus starlight, white and greys. At most five glows at one time; a cloud is one, and the 24 test lights are
    one cloud. Copy A and copy B never differ by hue alone: place, label and the event ring differ too.
15. **No arrows and no boxes.** No arrowhead, no rounded word-card, no list, no stamp, no strike-through.
    A direction is a motion.
16. **Minimum sizes** (for a phone): a test light has a core radius of 0.09 and at least 0.1 between cores; a
    ring that carries meaning has a radius of 0.15 or more; a probability bar is 0.42 high; the field has a radius
    of 2.2 when it is the main object; a line that carries meaning has stroke `W_LINE` (2) or more; nothing that
    carries meaning is under 0.3 high. The emblem of the pilot (S10, S11) and the two step glyphs of S08 are
    exempt: each is a small whole.
17. **Bleeds.** The open boundary is `bleed_ok`: it crosses |x| = 6.4 in S05 to S09, and those scenes carry
    `# qa: bleed`. In SPECK, P and GAP the strip of the question above the boundary is at 15%, grey, with no red;
    it is the only other thing outside the safe area. Nothing else bleeds.
18. **Default durations.** Unless a row says otherwise: a fade or a dim takes 0.6 s; a label lands in 0.6 s with
    `late(0.6)`; a line draws in 0.8 s; a settle takes 0.8 s. Every stream into the model in S03 is hollow
    starlight (`DATA` outline at 60%).

---

## 2. Glossary (one name per thing)

The voice and the screen use only the name in the first column. A label can be a short form of it.

| Name | The thing | In the voice | On screen |
|---|---|---|---|
| model | The AI model of the supposed case | "a model", "the model" | `model` (once, S01) |
| post-training examples | The examples that teach an already trained model how to respond; the points of the pool | "examples"; "training data" only in the post's own sentences (S02 line 3, S10 line 2) | `post-training examples` |
| data change | Removing a group of post-training examples, or replacing them with different ones | "change" ("each change", "every change", "many changes", "two changes"); "the larger data-change question" once; "batches of training data" only in the post's sentence of S10 line 2 | `data change` |
| retrain | To train the model again after a change | "retrain" | (the stream and the needles) |
| safety test | The test that the model fails; all 24 lights | "a particular safety test", "the test" | `safety test` |
| held-back tests | The part of the test that is not used to choose a change; the outer row. Nothing that chooses a change touches it (S03, S11) | "tests held back" | `held back` (S03 only) |
| computation | The work that a retrain or any other step costs | "computation" | `computation` |
| a shortcut | A way to choose with less computation than trying every change directly | "a shortcut"; "a practical shortcut" in S09 | `a shortcut` |
| tiny learner | The small system of the pilot. Never "model" | "a tiny learner" | `tiny learner` |
| event | The one learning step whose contribution is suppressed. Never "example", never "learning moment" | "one event", "that event" | `one event` |
| copy A, copy B | Copy A learns normally (blue). In copy B the event's contribution is suppressed (violet) | "one copy", "the other", "each copy", "the two copies" | `copy A`, `copy B` |
| comparison | The difference between the two copies at the end of one random run | "a comparison", "the comparison" | `the comparison` |
| estimate | What many comparisons give; the centre line of the strip | "the estimate" (once) | (the centre line) |
| variance | How much the comparison fluctuates between random runs; the soft band | "variance" | `variance` |
| coupling | Coordinating the random choices of the two copies; one way to do it is a pairing | "coupling"; "how the choices are paired" | `coupling` |
| toy configuration | One fully specified small problem; one unit of the field | "toy configurations", "configuration" | `toy configurations` |
| baseline | One of the six ordinary pairing methods; the best of them in a configuration is the best baseline | "six baseline pairing methods", "the best baseline" | `six baselines`, `best baseline` |
| oracle | The calculation that could find the best allowed pairing in the tiny setup. Never "our method" | "an oracle", "the oracle" | `oracle` |
| condition | The rule for advancing to the planned longer-horizon test. "Gate" is not used | "the condition"; "the condition for advancing" | `≥20%` at the line |
| longer-horizon test | The planned extension. Drawn faint (16%) at the top end of the condition line on "longer-horizon"; on "advancing" (S09 line 5) it glimmers once to 24% and back (0.8 s); never above 24%, never lit | "the planned longer-horizon test" (S08 line 3), its only spoken name. S09 line 5 says "the condition for advancing", the words of S08 line 3 | (no label) |
| target family | The chosen part of the configurations. No name and no size | "target family", "that family" | `target family` |
| variance reduction | The quantity on the scale: reduction in variance against the best baseline | "reduction in variance" | `variance reduction` |
| the pilot | The completed, narrower work | "our pilot", "the pilot" | `the pilot` |
| boundary | The line between the pilot and the larger question | "those boundaries" | (the line) |

---

## 3. The world

### 3.1 The place

The video is one dark canvas that the camera travels on. It has two territories.

- **The question** is the upper territory: the pool, the model, the safety test and the cost floor. The frame
  **W** (centre (0, 0), width 14.22) shows all of it. Coordinates of this territory are canvas coordinates.
- **The pilot** is the lower territory. The frame **P** (centre at canvas (0, -5.2), width 14.22) shows it.
  Coordinates of this territory are **P-local**: P-local y = canvas y + 5.2, and x is the same.
- **The boundary** lies between them at canvas y = -3.0 (P-local y = 2.2). It is drawn in S05. In frame P the
  top 1.8 units show the underside of the question at 15%: the three lowest test lights, the lower tip of light
  2's ring and the lower end of the shade, all grey (light 0's red core is grey while the camera is on the pilot;
  its red returns in S10). The cost floor and the shortcut lane
  are faded out there (rule 10 of 1.2). So the question is "up there", dark and untouched, for the whole pilot.
- In S10 the boundary closes round the pilot, the pilot becomes a small emblem, and the emblem comes back up
  with the camera. The last frame is frame W with the pilot small inside its boundary, off the rows of the cost.

**Camera stations.** The camera only travels between these.

| Station | Centre (canvas) | Width | Zoom | Shows |
|---|---|---|---|---|
| TEST-IN | (1.6, 0.38) | 10.46 | 1.36 | The model and the 24 lights, large (first frame of the video). Light 23's ring top is at screen y 3.37; light 0's red glow ends at -2.87, above the band of the tag |
| W | (0, 0) | 14.22 | 1.0 | The whole question |
| STARE | (2.4, 0.43) | 12.47 | 1.14 | The model and both rows of lights; the right fringe of the pool. The lights span screen y -2.81 to 3.31 and the shade -2.88 to 3.37 |
| (waypoint) | (0, -5.4) | 14.22 | 1.0 | Move 4 passes near it on one rounded path: the pool leaves the top of the frame before the frame narrows |
| SPECK | (-5.4, -5.4) | 10.16 | 1.4 | One point of light under the boundary |
| P | (0, -5.2) | 14.22 | 1.0 | The whole pilot, with the dim strip of the question above the boundary |
| GAP | (0.3, -5.5) | 13.17 | 1.08 | Not used by default (the lean of section 8, point 7) |

| # | Scene | Move | Cue and time | Why |
|---|---|---|---|---|
| 1 | S01 | TEST-IN to W | `at(1)`, 3.0 s | From one failing test to the whole problem |
| 2 | S03 | W to STARE | `at(2)`, 3.9 s | The camera does the staring; it arrives on "staring at" |
| 3 | S04 | STARE to W | `at(0, lead=0.4)`, 2.8 s | Back to the whole question for the threads |
| 4 | S05 | W through (0, -5.4) to SPECK | `at(3)`, one 3.4 s `GLIDE` on one rounded path (the turn toward SPECK begins 0.6 s before the straight descent would end) | Straight down while the boundary draws; then "narrower": the frame narrows onto one point. The zoom-in starts only when the pool's lowest point has left the top of the frame; the build checks this |
| 5 | S06 | SPECK to P | `at(0)`, 3.0 s | It follows the learner's first step |
| 6 | S10 | P to W | `at_word(0, "It")`, 3.0 s | The larger question is still there |

Six moves, all 2 to 6 s long, none past zoom 1.4. Each is a `world.clock_move` (rule 3 of 1.2, section 3.9): it
starts at its cue and ends at its own end time, whatever cues it crosses. There is no move in S09: the result is
watched from frame P.

### 3.2 Colour map

Four hues, one meaning each, for the whole video. The names are the names of `kit/theme.py`.

| Colour | Kit name | Hex | The one meaning | Where |
|---|---|---|---|---|
| Blue | `MODEL` (`MODEL_LO`, `MODEL_HI`) | `#58C4DD` (`#22718C`, `#A9E3F1`) | The model, and the run that learns normally | Needles and rim of the model; copy A |
| Gold | `FOCUS` (`FOCUS_LO`, `FOCUS_HI`) | `#FFD24A` (`#B98A1B`, `#FFE9A3`) | A data change | Changed points, outlines, the S11 tint, beams and ranges; the supposed twin of the model (the model after a supposed change) |
| Violet | `COPY_B` (`COPY_B_LO`, `COPY_B_HI`), new | `#A98BFF` (`#5D4C9E`, `#D6C9FF`) | Copy B, whose event contribution is suppressed. Nothing else | Copy B's head, tail, bar tab, label, event-ring outline, its tree in the web |
| Red | `FAIL` (`FAIL_LO`, `FAIL_HI`) | `#FF6B5E` (`#A83F36`, `#FFA79E`) | A failed safety test. Nothing else | Cores of test lights; the arc of a mini dial |
| Starlight | `DATA` (value changed) | `#E8E2D0` | Post-training examples. Nothing else | The points of the pool and the strokes of an example glyph |
| White | `INK`, `INK_HI` | `#ECE7DB`, `#FFFDF7` | The thing that we read or measure | Type; the comparison, the link, the band, the boundary, the scale, the results, the lit units, the lamp |
| Greys | `MUTED`; `GREY_1` to `GREY_5` | `#8D95A5`; `#C8CCD6`, `#9299A8`, `#646B7A`, `#3B414E`, `#20242D` | Structure, cost and things that are not in focus | Tag and citation; the cost floor (solid segments, sparks and end tick in `GREY_1`); the lone point's core; units of the field, baseline glyphs, bar segments, tracks, rings of lights |
| Background | `BG`, `BG_EDGE`, `BACKSTROKE` | `#0C0E13`, `#040507`, `#080A0D` | The vignette and the stroke behind text | Never a drawing colour |

- **No green and no teal.** A test that passes is a quiet pale light (`INK` at 60%). `PASS` is not used. `DATA`
  keeps its name and gets the starlight value, so the pool and the model differ by more than hue.
- Starlight and white differ by a CIELAB difference of 3.6 and look the same. So nothing near the pool
  is drawn in white that could read as data: the cost is `GREY_1` (difference 17 from starlight), and the S01
  stream into the model is starlight because it is data.
- Gold is never used for focus. Focus is made with brightness: brighten the thing, dim the rest.
- **Violet and colour vision.** I simulated colour-vision deficiency (Machado 2009, full severity) and measured
  the CIELAB difference between `COPY_B` and `MODEL`: 69 with normal vision, 38 (protan), 30 (deutan), 43
  (tritan). Gold against blue was 92 (protan) and 95 (deutan), so copy A and copy B are now harder to tell apart
  by hue for those viewers. They never rely on hue alone (rule 14 of 1.2): copy A is above, copy B below; each
  has its label; copy A's event ring is lit and copy B's is hollow. Of nine violets that I tried, `#A98BFF` kept
  the largest difference from blue under every simulation (and 78 or more from red). The kit's palette check
  must run on it before the build.
- The field of 1,440 is cool grey (`GREY_2`), even and still. The pool is warm starlight, uneven and drifting.
  They are in different territories and never share a place on screen.

### 3.3 Type scale

New Computer Modern Book for 64, 44 and 32. Inter Medium for 24 and 18. All text is built with `T()`.

| Size (kit name) | Face | Used for, and nothing else |
|---|---|---|
| 64 (`display`) | Serif | `18.5%`. It is the only 64 in the video |
| 44 (`title`) | Serif | The title (two lines) and its word `safer?`; `variance`; `coupling`; `1,440`; `≥20%`; `14.1%` |
| 32 (`body`) | Serif | The sign-off (two lines); `about` beside `18.5%` and beside `14.1%`: one face for the hedge, and not lost beside the 64 |
| 24 (`label`) | Inter | Every label; the tag |
| 18 (`fine`) | Inter | The citation only |

### 3.4 The two fixed marks

| Mark | String | Style | Place (screen, pinned) | On |
|---|---|---|---|---|
| Tag | `illustration` | Inter 24, `MUTED` | Right edge x = 6.4, baseline y = -3.2 | S01 from the first red light; S02 to S05 until the test lights leave the frame (late in move 4); S06 from the bar's first frame (on "suppressing"); S07; S08 until the condition line draws (`at(2)`, "The condition"); S09 from the web's first frame ("oracle") to the end of its fold; S10 from the lamp's first frame (`at(1)`); S11 to the fade. In S10 and S11 the tag refers to the world; the emblem's two trails are the post's results at true proportion, its two white dots sit inside its family mark, and the emblem lands before the tag comes back |
| Citation | `including in "work on reducing noise in counterfactual estimates" (arXiv 2111.06888)` | Inter 18, `MUTED` | Left edge x = -6.4, baseline y = -3.2 | S07, from "established" to "step" |

The band under y = -2.9 (screen) belongs to these two marks. No art and no label goes there. (The kit's
`hud_tag()` is already Inter 24: `theme.TAG_SIZE`.)

### 3.5 The six lasting objects

**Object 1. The pool** (post-training examples). Code: `world.Pool`.

| | |
|---|---|
| Made of | One `DotCloud` of 700 points (seed 7) in an uneven cloud: x from -6.2 to -1.9, y from -0.9 to 2.8, centre (-4.05, 0.95). Radius 0.028 to 0.05, larger near the centre. Colour `DATA` at 35% to 95% |
| Example glyph | Only inside the lens (S01): a request stroke 0.18 long (`GREY_2`) over a response stroke 0.27 long (`DATA`), stroke `W_LINE`, at display size. Strokes, never text. The build checks that no two glyphs come closer than 0.08 |
| Lens | A magnifier: a circle of radius 1.0 at (-3.9, 0.9), rim `INK` at 60%, stroke `W_LINE`. It shows the 20 points nearest (-3.9, 0.9), all within 0.4 of it, at 2.5 times their distance from the centre. It is clipped to its circle (`set_clip`) and sits over a `BG` disc at 100%, which hides the unmagnified points under it |
| Groups | gA (-5.1, 2.0), gB (-5.2, 0.0), gC (-2.95, 2.0), gD (-3.1, 0.15): each the 40 points nearest its centre. Ten more groups stand for "many": 8 points each (an outline radius of about 0.33), on centres from a seeded search (3.12) that keeps them 0.7 or more apart and 0.95 or more from the centres of gA to gD. The build stops if two padded outlines touch |
| Outline | `hull_blob(points, pad=0.12)`, dashed, `FOCUS`, stroke `W_LINE`. An outline with its points untouched is a data change that nobody has made |
| States of a group | *at rest* (starlight); *in a change* (points gold); *removed* (the gold points lift 0.6 up and 0.4 left while they fade to 0; the holes stay); *replaced* (different points fly in: starlight core, gold halo); *outlined*; *tinted* (S11: the outline stays dashed, at 100%; a faint gold tint at 12% inside) |
| Marked points (S04) | Seven points of the pool, chosen by index (3.12): none in gB, at most one in any other outline, each 0.8 or more from the others. Marked, a point's core brightens to `INK` at 90% with a glow of radius 0.12 (the seven glows are one cloud: one glow in the count of rule 14). No ring: a thin white ring means "chosen" (S02) |
| Rest motion | Each point drifts on its own small loop (0.03 to 0.06, period 6 to 11 s) and twinkles by 15% |
| Label slot | Under the pool: left edge x = -6.1, baseline y = -1.4. One label at a time: `post-training examples`, `data change`, `associated with this answer` |

**Object 2. The model.** Code: `world.Model`.

| | |
|---|---|
| Made of | A round core, centre (0.5, 0.55), radius 1.15. 40 needles on three rings (8 at radius 0.35, 14 at 0.65, 18 at 0.95), each a tapered stroke 0.22 long, `MODEL`, stroke `W_LINE`. A rim circle, `MODEL` at 40%, stroke `W_LINE`. A `glow_sprite` of radius 1.7, `MODEL`, peak 0.22. A core disc of radius 1.15, fill `BG` at 85%. No box and no layers of a network |
| Drawing order | Back to front: the threads of S04; the core disc, which hides them inside radius 1.15; the glow sprite; the rim; the beams of S11; the needles. So a thread passes behind the model and touches no needle, and a beam goes through it |
| States | *M0* (the trained pattern); *MA*, *MB*, *MC* (three other seeded patterns, after a supposed retrain; their red lights are in 3.12); *M-star* (the supposed tuning of S03); *asked* (the needles flick 12 degrees in a wave from right to left, 0.4 s); *retraining* (starlight flows in at the left rim and the needles turn to a new pattern, ring by ring) |
| The twin (S04, S05) | A hollow copy at half size, centre (0.5, -1.45): gold outline needles. Five hollow lights (core radius 0.09) at radius 1.5 from (0.5, -1.45), at -20, -10, 0, 10 and 20 degrees; the lowest is at (1.91, -1.96). The needles jump by up to 20 degrees, 6 times a second; the lights change at most twice a second, only between `FAIL` at 35% and `INK` at 40%. Both are `world.jitter` (seed 47, 3.12), driven by the film clock and the idle gain. At a scene boundary the needles rest in pattern M0 turned by +8 degrees and the lights rest at `FAIL` 35% |
| Rest motion | Needles tremble by 1.5 degrees. A slow wave of brightness crosses the core every 5 s |
| Label | `model` (24, `MODEL`), centred at x = 0.5, baseline y = 1.95. Once, in S01 |

**Object 3. The safety test.** Code: `world.TestArc`.

| | |
|---|---|
| Made of | 24 lights on arcs round the model's centre. Light k (k = 0 to 23) is at the angle -42.55 + 3.7 k degrees. A light is a ring (radius 0.11, `GREY_2`, stroke `W_LINE` at 60%) with a core (radius 0.09). The 24 cores and their glows are one `DotCloud` with a glow for each point: one glow in the count of rule 14 |
| Two arrangements | *One test* (S01, S02): even k at radius 3.0 and odd k at radius 3.25, a zig-zag. *Split* (from S03): odd k slide out to radius 3.95 and are the held-back row; even k stay and are the row that we look at |
| States of a light | *hollow* (not asked: ring only); *pale* (asked, no failure: core `INK` at 60%); *red* (failed: core `FAIL`, glow of radius 0.25); *dark* (held back under the shade: core `GREY_4`); *soft* (S03: no ring, a pale glow of radius 0.45 to 0.8 at 30%, from the same cloud, screen blend) |
| The supposed failure | Red lights: k = 0, 6, 10, 14, 20 (inner row) and k = 3, 9, 15, 21 (outer row). Nine of 24. It is a drawing of "repeatedly fails", not a rate |
| Ask | A pulse runs from a light to the model's rim and a pulse comes back. The first one takes 0.5 s each way. In a sweep, each takes 2 to 4 frames |
| Shade | A ring sector, radius 3.72 to 4.08, angle -40.5 to 44.0 degrees: fill `BG` at 88%, edge `GREY_3`. It covers the outer rings (radius 3.84 to 4.06; light 1's ring ends at -40.45 degrees, light 23's at 44.15). At W it spans y -2.10 to 3.38, inside the safe area; at STARE, screen y -2.88 to 3.37. Lifted, it is a hairline at radius 4.08 over the same angles (`GREY_3`) |
| Rest motion | Lit cores breathe by 8% (period 3 s) |
| Labels | `safety test` (24, `INK`): left edge x = 4.0, baseline y = 0.45 (S01). `held back` (24, `GREY_1`): left edge x = 4.9, baseline y = 0.45 (S03 only) |
| Key places | Light 0 at (2.71, -1.48); light 6 at (3.31, -0.49); light 8 at (3.42, -0.12); light 10 at (3.49, 0.26); light 12 at (3.50, 0.65). Split: light 1 at (3.58, -1.93), light 3 at (3.87, -1.51), light 9 at (4.40, -0.09), light 11 at (4.45, 0.42), light 13 at (4.43, 0.93), light 21 at (3.73, 2.82), light 23 at (3.41, 3.22) |

**Object 4. The cost floor** (cost of computation). Code: `world.CostFloor`.

| | |
|---|---|
| Made of | A floor line at y = -2.3 from x = -3.0 to 5.4 (`GREY_3`, stroke `W_LINE`). On it the **direct band**: 14 segments, each 0.56 long and 0.10 high, with gaps of 0.04. An end tick at x = 5.4 (0.34 high, `GREY_1`). Under it the **shortcut lane**: a dashed line at y = -2.75 from x = -3.0 to 5.4 (`GREY_3`, stroke `W_LINE`) |
| States of a segment | *solid* (`GREY_1`: computation that the picture has spent); *outline* (`GREY_1` at 25%: only supposed). A segment is born from sparks (`GREY_1`) that fall from the model |
| Mini dial | The result of one retrain: a circle of radius 0.16 (`GREY_2`) that stands on the end of its segment, with a red arc as long as the red share of the test. Born from a copy of the test lights |
| States of the lane | *empty* (rest); *supposed work* (S05: pieces at `GREY_1` 60% and a dotted continuation). The lane is never filled at rest |
| Visibility | Faded to 0 whenever the camera is at STARE, SPECK, P or GAP (rule 10 of 1.2) |
| Rest motion | A slow glint runs along the band every 6 s |
| Labels | `computation` (24, `GREY_1`): right edge x = -3.2, baseline y = -2.34. `a shortcut` (24, `INK`): right edge x = -3.2, baseline y = -2.84 |

**Object 5. The tiny learner and its two copies** (pilot territory, P-local). Code: `world.Fork`,
`world.ChoiceBars`, `world.TOY`.

| | |
|---|---|
| The lone point | At S = (-5.4, -0.2). Core of radius 0.07, neutral `GREY_1`; a white halo (`glow_sprite`, radius 0.32). It is larger than a point of the pool, cool and not warm, and behind the boundary; the pool has left the frame before it brightens (S05). It takes blue and violet only at the split (S06 line 2). Before S05 it sits at canvas (-5.4, -5.4) at 10%, always off frame |
| The fork | Time runs to the right: x = -5.4 (start), -3.9 (after the event), -2.4 (after step 1), -0.9 (after step 2). Height is the learner's state: y = -0.2 + 1.25 h. Copy A: core and tail `MODEL`. Copy B: core and tail `COPY_B`. Paths: stroke `W_BOLD`, with a comet tail behind each head. The start, once the point has become copy A, is a `GREY_1` dot of radius 0.05 with no halo. Ghosts of earlier futures: 14% of the fork's level, drawn once for each distinct path (a repeat adds no ghost, so the faint tree does not brighten where paths repeat) |
| The event | The first step. A ring of radius 0.15 at mid-step, x = -4.65: filled `INK` on copy A (at y = 0.17), hollow with a `COPY_B` outline on copy B (at y = -0.2): its light is out |
| The bars | One for each copy, 5.0 long and 0.42 high, from x = -4.2 to 0.8. Bar A at y = -1.35, bar B at y = -2.3. Three segments: segment 1 `GREY_2`, segment 2 `GREY_1`, segment 3 `GREY_3`. A tab 0.08 wide in the copy's colour at the left end. The widths are that copy's own probabilities now |
| Pointer | A white hairline with a cap (a filled dot of radius 0.04) that lands on a bar: one random choice. **Pointers appear only at step 1 and step 2. The event has no pointer:** its choice is given, and its segment lights by itself. In S06 the pointers land at u = 0.57 on bar A and u = 0.18 on bar B at step 1 (segments 2 and 1), and at u = 0.24 and u = 0.78 at step 2 (segments 1 and 3) |
| Link | Two pointers can join into one hairline through both bars. A link joins the pointer of bar A to the pointer of bar B: *straight* (the same number u) or *crossed* (a mirrored number, 1 - u). No other form is shown |
| Piles | Small dots (radius 0.035, `INK` 70%) that land above bar A and under bar B where the pointer landed. A pile is a stack 5 dots wide at a pitch of 0.07, centred on its segment, growing away from the bar; at most 4 rows (0.28), so the piles under bar B stay above y = -2.85. Landings are stratified by index: landing k reads u = (k + 0.5) / 30 on bar A, each k once (3.12). Each form's block of indices is closed under that form's map, so copy B's 30 values are also each grid value once, and both piles end exactly at the grid's counts: 15, 4, 11 and 9, 3, 18 at step 1; 14, 8, 8 and 10, 4, 16 at step 2 (3.7) |
| The comparison | A plain white segment from one head to the other (at x = -0.9 after step 2), stroke `W_BOLD`, drawn under the two heads. No caps: its ends are the heads. It is the effect of one run; only the band of S07 means a spread |
| Rest motion | Heads breathe (period 1.6 s). The last 0.8 units of a tail are brighter |
| Labels | `tiny learner` (24, `INK`): left edge x = -6.3, baseline y = -0.95, under and left of the point (placed for frame P; its top is 0.19 under the point's halo at P and 0.06 under it at SPECK); `one event` (24, `INK`): centred x = -4.9, baseline y = 0.75; `copy A` (24, `MODEL`), riding 0.25 above and left of its head; `copy B` (24, `COPY_B`), riding 0.25 below and left of its head (each at most 1.5 units a second); `the comparison` (24, `INK`) |

**Object 6. The boundary.** Code: `world.Boundary`, `world.Emblem`.

| | |
|---|---|
| Open (S05 to S09) | A flat `smooth_closed` loop of 16 anchors along canvas y = -3.0 (`INK_HI` at 45%, stroke `W_LINE`, `bleed_ok`): anchor i at x = -12 + 3i for i = 0 to 8, then at x = 12 - 3(i - 8) for i = 9 to 15, all at y = -3.0. S05 draws it with a clip wipe from the left (`set_clip` and a growing rectangle), not with `Create` |
| Closed (S10, S11) | A `smooth_closed` curve with the same 16 anchors, 1.6 wide and 0.92 high, round the emblem: anchor i at the angle 180 - 22.5i degrees (0 at the left, 4 at the top, 8 at the right, 12 at the bottom), so that the `Transform` pairs the flat loop's upper run with the top half and does not twist. At rest in frame W its centre is (-5.4, -1.6): it spans x -6.2 to -4.6 and y -2.06 to -1.14, above the rows of the cost floor and the lane, and away from the places of `computation` and `a shortcut`. After S10 line 3 it is `INK_HI` at 100%, stroke `W_BOLD` |
| The emblem | A drawn miniature of the pilot, 1.36 wide and 0.72 high. It is not a scaled picture. No numerals and no words. Its parts, in emblem-local coordinates (origin at the centre of its box): zero tick at x = -0.62 from y = -0.30 to -0.04 (`GREY_1`); condition tick at x = 0.50 from y = -0.32 to -0.02 (`INK_HI`); trail 1 at y = -0.10 from x = -0.62 to 0.416 (0.925 of the scale) and trail 2 at y = -0.24 from x = -0.62 to 0.170 (0.705), both white, stroke `W_LINE`, so the 18.5% trail is the upper one, as in S09; a dotted stub from (0.50, -0.02) to (0.66, 0.02) at 30%; a disc of 60 grey dots, all one grey, radius 0.16, centre (0.44, 0.20), with white dots at (0.491, 0.243) for 18.5% (u1, the upper) and (0.483, 0.149) for 14.1% (u2, the lower); and the **family mark**, a faint irregular outline round the inner dots that encloses both white dots: the closed curve r(θ) = 0.16 (0.58 + 0.06 cos(2θ + a) + 0.04 cos(3θ + b)) round the disc's centre, with the phases a and b of the field's family (seed 37, 3.6), `INK` at 55%, stroke `W_HAIR`, solid. No second curve and no label: the mark only keeps "in that family" in the last frame (pilot facts, open point 3). The white dots are at 0.42 of the disc's radius and the curve never comes closer than 0.48 of it, so it always encloses them. The build measures the distance from each white dot's centre to the curve; if either is under 0.02 (about 2.7 px in frame W), the factor 0.58 becomes 0.65 in the emblem only, which gives at least 0.021 for every phase (section 7.3) |
| Rest motion | The curve's glow breathes (period 4 s). The emblem is still. During the pan of S10 the emblem and its curve travel in a straight line on the canvas, with the camera's `GLIDE` |
| Label | `the pilot` (24, `GREY_1`): left edge x = -4.38, baseline y = -1.7, right of the curve. It is 0.6 or more below the pool and not in the pool's label slot |

### 3.6 Instruments of the pilot (they cross scene boundaries; P-local)

**The strip** (S07). Code: `world.Strip`.

- A vertical axis at x = 4.3 from y = -1.65 to 1.95 (`GREY_3`, stroke `W_LINE`). A tick is one comparison: a
  white dash 0.5 wide at the height y = -0.05 + 2.0 (D + 0.3514), where D is the comparison in the toy's units.
  The toy has 49 possible values of D; with this mapping every possible tick lies between y = -1.61 and 1.90,
  on the axis and under the boundary (2.2). The build checks this (3.7). A tick is drawn once for each distinct
  height, at 30% plus 10% for each repeat, at most 70%, so repeated heights do not stack into bright blots.
- **The estimate** is the centre line at y = -0.05 (`INK`, 0.9 wide). It never moves.
- **Variance** is a soft band round the centre line: 0.7 wide, fill `INK` at 12%, soft edges, with a thin edge
  line at its top and at its bottom. Its half-height is the toy's standard deviation times 2.0, computed in the
  code for the pairing on screen: 0.614 (no coordination), 0.587 (straight), 0.621 (crossed). It is a typical
  spread, not the range of all values: about three in ten of the toy's futures (0.30 of the probability) fall
  outside it.
- **The ghost** is a copy of the two edge lines at the no-coordination half-height (0.614), at 30%. It is drawn
  when line 6 begins and fades to 0 in the last 0.8 s of S07, so P07 holds the live band only and no "no
  coordination" reference goes into S08. The rim between an edge and its ghost (0.027, about 3.6 px at 1080p for
  the straight pairing) is never brightened. If it is hard to see, make the ghost brighter; never make the effect
  larger.
- `variance` (44, serif, `INK_HI`): right edge x = 3.75, baseline y = 1.0.

**The field** (S08, S09). Code: `world.Field`.

- 1,440 units, one `DotCloud`, colour `GREY_2` at 60% (never `INK`, so that they differ from the pile dots of
  S07), in a sunflower disc. *Main object:* centre (1.2, -0.2), radius 2.2, unit radius 0.034. *Parked:* centre
  (4.4, 0.95), radius 1.1, unit radius 0.02.
- The disc has no parts with a meaning, and it never parts: no halves and no sectors. No share of the project
  record is drawn, said or used to size anything in the field. No size of the family is said or shown.
- **Target family:** a seeded, irregular set of units near the middle (seed 37, 3.12): the units inside the
  closed curve r(θ) = R (0.58 + 0.06 cos(2θ + a) + 0.04 cos(3θ + b)), with R the field's radius and a, b from
  the seed. Its outline is a soft `hull_blob` of those units (pad 0.06), `INK` at 55%, stroke `W_LINE`, solid.
  It is not a circle, and its share of the units is whatever the seed gives; the build does not report it. The
  build stops if u1 or u2 lies outside it.
- **The lower part** (the second curve of S09): the family units under the seeded wavy line
  y = R (-0.06 + 0.05 sin(5x / R + c)) (seed 43). It holds u2 and not u1. Its outline is a `hull_blob` of those
  units (pad 0.06), `INK` at 55%, stroke `W_LINE`, solid, like the family outline. It is not a half, and no
  fraction is drawn.
- Named units, as offsets from the centre in units of the radius: u1 (0.32, 0.27), in the family and above the
  lower part (the strongest result in the family); u2 (0.27, -0.32), in the lower part (the strongest result
  with full suppression). Parked, u1 is at (4.75, 1.25) and u2 at (4.70, 0.60). So the 18.5% unit is the upper
  lit unit and the 14.1% unit the lower, in the same order as their tracks. The place where S07 dissolves is not
  a unit and not the field's source: the toy of 3.7 is not one of the 1,440.
- A lit unit is `INK_HI` with a glow of radius 0.2. Only u1 and u2 are ever lit, and each only from "strongest"
  in the line that names its result (S09 lines 2 and 3). From "best" (S09 line 4) the label `strongest` names
  both: two thin threads run from its right end to them (3.10).
- Rest motion: each unit breathes by 10% with its own phase. The field does not drift.

**The scale** (S08, S09). Code: `world.Ruler`.

- **Zero tick** at x = -5.6, from y = -2.75 to -1.0 (`GREY_1`, stroke `W_BOLD`). It is the best baseline.
- **Track 1** at y = -1.3 and **track 2** at y = -2.3: hairlines from the zero tick to the condition line
  (`GREY_3`, stroke `W_LINE`).
- **Condition line** at x = 4.4, from y = -2.7 to -0.6 (`INK_HI` at 85%, stroke `W_BOLD`, no glow). On
  "condition" (S09 line 5) it rises to 100% along its whole length (0.6 s) and stays. The distance from zero to
  the line is 10.0 units, so 1% is 0.5 units.
- A **result** is a white marker (radius 0.08) with a small glow (radius 0.12, peak 0.5) from its first frame in
  S08. It runs along a track from the zero tick and leaves a white trail (stroke `W_HERO`). Once it stops, its
  glow breathes in opacity only (90% to 100%), never in radius. About 18.5% stops at x = 3.65. About 14.1% stops
  at x = 1.45.
- **The run.** One steady speed and a 0.6 s ease-out, nothing else. For a run from x0 = -5.6 over a length L
  that starts at t0 and must stop at t1: v = L / (t1 - t0 - 0.3); x(t) = x0 + v (t - t0) up to t1 - 0.6; then
  x(t) = x0 + L - (v / 1.2) (t1 - t)^2. Position and speed are continuous, and the head stops exactly at t1.
  Run 1 (L = 9.25) starts at S09 `at(0)` and stops as "18.5%" starts; this gives v1 (about 1.94 units a second
  by the estimates). Run 2 (L = 7.05) has the same speed v1 and stops as "14.1%" starts, at t2, so it starts at
  t2 - 7.05 / v1 - 0.3 (about 10.8 s, on "event's", by the estimates). It is clock-driven (rule 3 of 1.2). The
  build stops if run 2 would start before track 2 has finished drawing.
- **The gap** is the dark track from the stopped head to the line: only the bare `GREY_3` hairline of track 1.
  Nothing fills it and nothing lights it.
  **Build check:** render P09 at 1080p, and a control still of P09 with the same background (vignette and
  dither) in which both heads, their glows, both trails and the condition line are hidden; track 1 stays.
  Along the pixel row of track 1 (y = -1.3), from the head's centre to the line's centre, the longest unbroken
  run of pixels that differ from the control by at most 3 grey levels must be at least 80 px (0.6 units). The
  build stops otherwise. Do not compare with the background: the hairline is about 90 grey levels above `BG`,
  so every pixel of the row would fail. By my estimate the run is about 85 px: 101 px of gap, less about 13 px
  where the head and its glow show (the glow falls under 3 grey levels at about 0.10 from the head's centre)
  and about 3 px of the line's half-stroke. A larger head or glow can take it under 80; that is what the check
  is for.
- **The longer-horizon test:** it is not on the scale. A dotted stem leaves the top end of the condition line,
  (4.4, -0.6), to (4.9, -0.5), and splits into two dotted branches that rise to the right to (6.2, -0.25) and
  (6.2, -0.5), fading out toward their ends (`INK` at 16%). It continues the line like a door; no part of it is
  at the height of a track. No step can be counted on it. It is drawn faint (16%) on "longer-horizon" (S08); on
  "advancing" (S09 line 5) it glimmers once to 24% and back (0.8 s). It is never above 24% and never lit.
- Strings: `variance reduction` (24, `GREY_1`): left edge x = -5.45, baseline y = -1.0. `best baseline`
  (24, `GREY_1`): left edge x = -5.45, baseline y = -2.72, at the foot of the zero tick and under track 2 (no
  descender, so its top is at about -2.55, 0.25 under track 2 and clear of the band of the tag); no text row of
  a result reads into it. `≥20%` (44, serif, `INK_HI`): left edge x = 4.6, baseline y = -1.5, 0.2 right of the
  line and 0.5 from the row of each result numeral (-1.0 and -2.0).

**The pairing glyph** (S08). A miniature of the two bars: two short grey bars 0.6 long and 0.25 apart, joined by
a soft, blurred link that has no readable form. 0.6 wide, 0.45 high. A baseline glyph is `GREY_2`. The six
baseline glyphs are identical; they differ only in the phase of a faint shimmer. None is ever highlighted, so
the picture says nothing about which baseline is best where. No glyph uses a link form of S07. The oracle's
glyph is `INK_HI` and 0.75 wide; its link is also soft. No glyph has a name, a kind or a rank. A soft link stands
for any joint table, including drawing the two choices separately.

**The step glyphs** (S08 line 1). Two small drawings under the field, one on each side of `one- or two-step`:
on the left an event ring (radius 0.1) and one step with a glowing head, 0.7 wide, centre (-0.55, -2.7); on the
right a ring and two steps, 1.15 wide, centre (3.18, -2.7). Both 0.3 high, `GREY_1`, stroke `W_LINE`. They are
tied to no part of the field, and they fade with the label.

### 3.7 The toy behind the pilot pictures

The fork, the bars and the strip are computed from one small rule (`world.TOY`). It is an invention for the
pictures. It is not a configuration of the pilot, it is not one of the 1,440, and none of its values is shown
or spoken.

| Thing | Value |
|---|---|
| State | One number h. On screen y = -0.2 + 1.25 h |
| Three lessons | Segment 1 pulls to h = 0.72, segment 2 to h = 1.71, segment 3 to h = 0.19. The levels are never drawn |
| A step | The learner moves 0.35 of the way to the level of the chosen segment |
| A choice | The probability of a segment is in proportion to exp(-d / 0.86), where d is the distance from h to the level of that segment. A pointer reads its bar in the fixed order segment 1, 2, 3 |
| Start and event | h = 0. The event is the choice of segment 2, with no draw. Copy A goes to h = 0.5985. Copy B stays at 0 (full suppression) |
| Bar before the event | 0.316, 0.100, 0.585 |
| Bars at step 1 | Copy A: 0.492, 0.156, 0.352. Copy B: 0.316, 0.100, 0.585 |
| The future that S06 draws | Step 1: copy A takes segment 2, copy B takes segment 1. Step 2: copy A takes segment 1, copy B takes segment 3 |
| Bars at step 2 of that future | Copy A: 0.470, 0.277, 0.254. Copy B: 0.343, 0.108, 0.549 |
| Heads of that future (P-local) | Copy A: (-3.9, 0.55), (-2.4, 1.03), (-0.9, 0.92). Copy B: (-3.9, -0.2), (-2.4, 0.12), (-0.9, 0.09) |
| The comparison | D = h of copy B minus h of copy A after step 2; 49 possible values, from -1.131 to 0.625 |
| Pairings (the same rule at both steps) | Straight: copy B reads u. Crossed: copy B reads 1 - u. Copy A always reads u. No other pairing is shown |
| Variance of D, exact | No coordination: 0.0943. Straight: 0.0863 (8.6% less). Crossed: 0.0966 (2.3% more) |
| Mean of D | -0.3514 under all three |
| Same choice at step 1 | 38% of runs with no coordination; 67% with the straight pairing. Coordinated is not equal |
| Ticks outside the band | 0.30 of the probability with no coordination: about three futures in ten |
| Stratified piles of 30 | Step-1 widths, all 30 indices under the straight form: bar A 15, 4, 11; bar B 9, 3, 18. Step-2 widths, three blocks by index (3.12): bar A 14, 8, 8; bar B 10, 4, 16 |

I computed every value of this table by summing over every pair of futures, and checked the line-6 schedule in
2,000 landing orders: both piles end exactly at their counts in all of them (section 7.3). **The build must
compute them again from the rule and stop if** the straight pairing does not lower the variance by 5% to 9.5%;
if the crossed pairing changes it by more than 3% in either direction; if the mean differs between pairings; if
any possible tick height lies outside the axis of the strip; or if a pile of line 5 or line 6 does not end at
the counts of this table. This keeps the drawn effect modest and away from both results of the post, and it
keeps each copy's own probabilities visible under both forms.

### 3.8 Passing objects

| Object | Scene | What it is |
|---|---|---|
| The title | S02 | Two lines, 44, serif, `INK_HI`, backstroke, centred at x = 0: `Which training data should we change` (baseline y = 0.5) and `to make an AI safer?` (baseline y = -0.3). The world is at 35% under it |
| `safer?` | S02, S03 | The last word of the title. It lets go of the title and stays at left edge x = 4.15, baseline y = 0.4. It does not move while it is read: its backstroke halo breathes (opacity 90% to 100%, period 2 s) |
| The choice ring | S02 | A thin white ring of radius 0.55 that hops between outlines and does not settle |
| The threads | S04 | About 70 hair-thin white threads from one red light, behind the model's core disc (hidden inside radius 1.15; they touch no needle), to scattered points of the pool. Seven of their end points are marked (Object 1): the core brightens, with a small glow; no ring. Baked when they rest (the camera is still by then) |
| The web | S09 | Two small soft trees that face each other, and a woven sheet between their ends, under the tag. Copy A's tree (`MODEL`): root (-4.9, 0.75); a soft wedge of light to a feathered arc at x = -3.9 (y 0.15 to 1.35), with no node dots; from it a dense fan of 27 faint ends at x = -2.9, 0.067 apart round y = 0.75, at 50% with a 0.03 blur, so that no branch or end can be counted. Copy B's tree (`COPY_B`) mirrors it: root (0.1, 0.75), feathered arc at x = -0.9, ends at x = -1.9. Between x = -2.9 and -1.9 a soft sheet of white threads joins every end of one tree to every end of the other: one `VMobject` drawn as one stroke, so crossings do not brighten and no thread can be told apart. The whole web is one `RasterLayer`, wiped in from left to right. The bright run is live on top: one path in each tree (seed 41) and two bright links that bow above the sheet, one between the two chosen points of the arcs and one between the two chosen ends. It folds by stretching the layer to height 0.02 onto y = -1.3 (trail 1) while it fades (0.8 s) |
| The lamp | S10 | A soft circle of light round a moving centre L(t). It draws nothing itself. One updater sets the opacity of each pool point, outline, needle, light, floor segment and lane dash to 0.35 + 0.65 s(d), where d is its distance from L(t) and s = 1 for d ≤ 0.8, 0 for d ≥ 1.1, with a smoothstep between. L stays at x ≤ 5.2 and y ≥ -2.3, clear of the band of the tag. It opens in place over the pool; it is never born from the boundary |
| The beams | S11 | Two thin dashed gold lines, from gA and from gD through the model's core (drawn above the core disc and under the needles), each ending at the model's right rim at the height of its range: gA's at (1.64, 0.66), gD's at (1.58, 0.16). No beam reaches either row of lights |
| The ranges | S11 | Inside the arc between the model and the inner row of lights. A dashed horizontal hairline (`GREY_3`) at y = -0.2 from x = 1.75 to 3.0. Two dotted gold intervals on their own rows: gA's at y = 0.66 from x = 1.8 to 2.75, gD's at y = 0.16 from x = 2.1 to 3.05 (they overlap by 0.65). Each is a row of gold dots along its row from end to end, with a short dotted gold cap (0.24 high) at each end: hollow, because it is only supposed. No fill, no band, no centre line and no edge lines: they share nothing with the strip of S07. No label. The held-back row stays shaded and untouched |
| The sign-off | S11 | Two lines, 32, serif, `INK` at 90%, backstroke, centred at x = 0.5: `Notes from an ongoing` (baseline y = 2.9) and `research project` (baseline y = 2.3) |

### 3.9 Shared code to write before any scene

One builder writes these first. The scene authors then use them and do not re-make them.

1. **`world.py`** beside `kit/`: the classes of sections 3.5 to 3.8, the constants of this document, the toy with
   its guard, the seeds of 3.12, and **`world.pose(name, scene)`**, which adds every object of a pose of section
   4 in its exact state. A scene starts with `world.pose("P03", self)` and ends in the state of
   `world.pose("P04", ...)`. A test renders the last frame of each scene and the first frame of the next and
   compares them.
2. **`follow_label(text, anchor, offset, ...)`**: a label that follows a point of the world and keeps its size
   class on screen while the camera moves (its backstroke too). The kit's `pin` fixes a place on screen; it does
   not follow.
3. **An amplitude envelope** for `drift()` and `ambient()`, so that idle motion can ease to rest in the last 12
   frames of a scene and ease in again (rule 6 of 1.2).
4. **The tag:** the kit's `hud_tag()` is already Inter 24 (`theme.TAG_SIZE`); nothing to change. `hud_cite()`
   stays at Inter 18, bottom left, and takes the lead-in "including in" in its own style.
5. **`theme.py`:** `DATA` gets the starlight value `#E8E2D0` (with `DATA_LO` `#8F8B7F` and `DATA_HI` `#FFF9EA`).
   New: `COPY_B` `#A98BFF`, `COPY_B_LO` `#5D4C9E`, `COPY_B_HI` `#D6C9FF`; run the kit's palette and
   colour-vision check on them. No other hex changes.
6. **Scene tails** come from `script.json`: the last line's `pause_after` is the scene tail (for the last scene
   all of it; for the others, all of it but the 0.40 s lead of the next scene). No scene sets `tail`.
7. **No bake of the question.** The question is live in every scene, at its stated level (35% under the title and
   in S10, 60% in the pause after S05 line 3, 15% while the camera is on the pilot): one cloud of 700 points, 40
   needles, one cloud of 24 lights and the outlines.
   A bake would hold only the framing of its moment and would pop when it is swapped for the live world.
8. **Numerals** enter with `FadeIn(scale=0.92)` and no `lag_ratio`; the kit's `enter()` (glyph by glyph) is not
   used for `1,440`, `≥20%`, `18.5%` or `14.1%`.
9. **Probes are parts, not pictures.** A scene that takes a part from a probe strips what must not reach the
   video: from `repo-prob` P6 the tick numbers, the brace "1.5 points short", the red line and the coloured
   bars; from P2 the counter "26 of 31" and the title; from P10 its title, its labels and its vertical ranges.
   Nothing is taken from P4 (outcome axes, a title, a number and a large effect). A lit unit is always inside the
   family (P8 lights one in a field with no family). From P6, also not its glow on the line or a band in the gap.
10. **`world.clock_move(frame, station, t0, t1, rate=GLIDE, path=None)`**: an updater on the camera frame that
   reads `film_time()` and moves the frame from where it is at t0 to the station at t1 (along `path` if given,
   for move 4), then removes itself. It is started at its cue and is not a play, so a row's `play_until` neither
   squeezes it nor cuts it (rule 3 of 1.2). Every camera move of 3.1 uses it.
11. **`world.jitter(seed, rate, t0, t1, apply)`**: a seeded, clock-driven updater that calls `apply(k)` for the
   k-th jump at the times t0 + k / rate up to t1, then removes itself. The jumps depend only on the seed and on
   k, never on the frame rate or on a play's length. It drives the twin's needles and lights (S04, S05), the
   pointer and hairline jumps (S07), the stream of 36 futures (S07 line 2) and the halo in the family (S08).

### 3.10 Every string on screen

All strings of the video, with their one place. Places of the question are canvas coordinates; places of the
pilot are P-local. "Left", "right" and "centred" say which edge of the string is at x. y is the baseline.

| String | Size and colour | Place | Scenes |
|---|---|---|---|
| `illustration` | 24, `MUTED` | right x = 6.4, y = -3.2 (screen) | see 3.4 |
| `including in "work on reducing noise in counterfactual estimates" (arXiv 2111.06888)` | 18, `MUTED` | left x = -6.4, y = -3.2 (screen) | S07 |
| `model` | 24, `MODEL` | centred x = 0.5, y = 1.95 | S01 |
| `safety test` | 24, `INK` | left x = 4.0, y = 0.45 | S01 |
| `post-training examples` | 24, `DATA` | left x = -6.1, y = -1.4 | S01 |
| `data change` | 24, `FOCUS` | left x = -6.1, y = -1.4 | S01, start of S02 |
| `computation` | 24, `GREY_1` | right x = -3.2, y = -2.34 | S02, S05 |
| `Which training data should we change` | 44, serif, `INK_HI` | centred x = 0, y = 0.5 | S02 |
| `to make an AI safer?` | 44, serif, `INK_HI` | centred x = 0, y = -0.3 | S02 |
| `safer?` | 44, serif, `INK_HI` | left x = 4.15, y = 0.4 | S02, S03 |
| `held back` | 24, `GREY_1` | left x = 4.9, y = 0.45 | S03 |
| `associated with this answer` | 24, `INK` | left x = -6.1, y = -1.4 | S04, start of S05 |
| `a shortcut` | 24, `INK` | right x = -3.2, y = -2.84 | S05 |
| `tiny learner` | 24, `INK` | left x = -6.3, y = -0.95 (placed for frame P) | S06 |
| `one event` | 24, `INK` | centred x = -4.9, y = 0.75 | S06, start of S07 |
| `copy A` | 24, `MODEL` | with its head, 0.25 above and left of it; then left x = -0.3, y = 0.86; in S07 right x = -4.45, y = -1.44 | S06, S07 |
| `copy B` | 24, `COPY_B` | with its head, 0.25 below and left of it; then left x = -0.3, y = -0.06; in S07 right x = -4.45, y = -2.39 | S06, S07 |
| `the comparison` | 24, `INK` | left x = -0.3, y = 0.40; in S07 centred x = 4.3, y = -2.10 | S06, S07 |
| `variance` | 44, serif, `INK_HI` | right x = 3.75, y = 1.0 | S07 |
| `coupling` | 44, serif, `INK_HI` | left x = 1.2, y = -1.98 | S07 |
| `1,440` | 44, serif, `INK_HI` | right x = -1.5, y = 0.6 | S08 |
| `toy configurations` | 24, `GREY_1` | right x = -1.5, y = 0.05 | S08 |
| `one- or two-step` | 24, `GREY_1` | centred x = 1.2, y = -2.8 | S08 |
| `six baselines` | 24, `GREY_1` | left x = -6.2, y = -0.45 | S08 |
| `oracle` | 24, `INK` | left x = -3.35, y = -1.85 | S08 |
| `≥20%` | 44, serif, `INK_HI`; one string with no space, `T("≥20%")`, so the kit counts one word (8.9) | left x = 4.6, y = -1.5 | S08, S09 |
| `variance reduction` | 24, `GREY_1` | left x = -5.45, y = -1.0 | S08, S09 |
| `best baseline` | 24, `GREY_1` | left x = -5.45, y = -2.72 (under track 2, at the foot of the zero tick) | S08, S09 |
| `target family` | 24, `INK` | right x = 3.1, y = 0.85 | S08, S09 until line 3 |
| `about` `18.5%` | 32, serif, `INK`; 64, serif, `INK_HI` | one row, gap 0.2, right x = 3.65, y = -1.0 | S09 |
| `full suppression` | 24, `INK` | right x = 3.1, y = 0.45, beside the lower part (from "full"); then right x = -1.2, y = -2.0, on the 14.1% row (from "result") | S09 from line 3 to the end |
| `about` `14.1%` | 32, serif, `INK`; 44, serif, `INK_HI` | one row, gap 0.2, right x = 1.45, y = -2.0 (so `about` spans x -1.0 to -0.05) | S09 |
| `strongest` | 24, `INK` | right x = 3.1, y = 0.9, between the heights of u1 and u2, 0.2 left of the field. Two thin threads (`INK`, stroke `W_LINE` as rule 16 of 1.2 asks, 35% as they draw, then 15%) run from (3.22, 0.96), 0.12 right of its end, to u1 and to u2, each ending 0.2 short of its unit's centre, at the edge of its glow: at (4.555, 1.210) and (4.503, 0.646). The thread to u1 stays above the lower part (the build stops if it crosses the second curve); the thread to u2 enters it. The threads belong to the label: they fade with it at the start of S10 | S09 from "best" |
| `the pilot` | 24, `GREY_1` | left x = -4.38, y = -1.7 | S10, S11 |
| `Notes from an ongoing` | 32, serif, `INK` | centred x = 0.5, y = 2.9 | S11 |
| `research project` | 32, serif, `INK` | centred x = 0.5, y = 2.3 | S11 |

### 3.11 The first check, before the full build

(a) A draft render of S07, S08 and S09 with real word times, with stills at a width of 390 px. (b) A 10-second
test of the model and the pool with no label: does a viewer say "a model and its data"? (c) Show S05 to S11 to
one person with the sound off and ask: "What does 18.5% measure against?", "Did it nearly work?", "Does copy B
still choose for itself?", "Where did the point of light come from?", "What does `strongest` name?", and, on the
last frame, "What is the small framed shape at the lower left? Does it belong to the cost, the shortcut or the
examples?" and "Are its two white dots the best of the whole disc, or of a marked part of it?". If the point
seems to come from the pool, dim the pool to 10% at the start of move 4. If the framed shape seems to belong to
any of the three, move it again. If the white dots read as the best of the whole disc, raise the emblem's
family mark to `INK` at 75%. The run has no lean by default; try the lean (section 8, point 7) only if the
answer to "Did it nearly work?" stays "no" with it in place. (d) On a 1080p still of P09 and its control still,
the dark-run check of 3.6: at least 80 px of track 1, between the head's centre and the line's centre, within 3
grey levels of the bare track. (e) On a still of P09 at 390 px, ask: "Which number goes with full suppression?"
and "What does `strongest` name?" The answers must be 14.1% and the two lit units. If the threads of
`strongest` cannot be seen at 390 px, raise their rest level from 15% to 25% and ask again. If `strongest` is
still read as the name of the outline or of the field, drop it (section 8, point 9). (f) The kit's
`word_count` returns 12 on P09, on the frame of S09 with the web, and on the first frame of S10.

### 3.12 Seeds and exact counts

Every random element that survives a scene boundary has a seed and an exact count, and `world.pose` replays it.

| Element | Seed | Exact count, and the rule |
|---|---|---|
| The pool | 7 | 700 points |
| The ten extra groups (S02) | 21, then upward | The first seed from 21 whose ten centres keep 0.7 or more apart and 0.95 or more from gA to gD, and whose padded outlines do not touch. `world.py` stores the seed it used |
| Retrain patterns MA, MB, MC and M-star | 3 | One pattern each. Red lights after each supposed retrain: MA 0, 3, 6, 9, 10, 15, 21 (7); MB 0, 3, 6, 9, 10, 14, 15, 20, 21 (9, the same nine as before: no change); MC 0, 3, 6, 9, 10, 14, 15, 21 (8). Red lights of the inner row in the S03 rounds: 0, 6, 10, 14, 20; then 6, 10, 14; then 10; then none |
| The threads (S04) | 13 | 70 thread ends. The seven marked points are the first seven indices, in seed-13 order, that keep the rules of Object 1 (none in gB, at most one in any other outline, 0.8 or more apart). `world.py` lists their indices |
| The futures (S07) | 11 | Exactly 40, drawn with no coordination: 4 in line 1 and 36 in line 2, spread evenly from "Variance" to `line_end(1)` (`world.jitter`). The future of P06 is not one of them and has no tick. P07 shows the ghosts and ticks of exactly these 40 (a ghost once for each distinct path; a tick once for each distinct height, 30% plus 10% for each repeat, at most 70%) |
| Pointer and hairline jumps (S07 lines 3 to 5) | 12 | 5 a second for each pointer, from the end of the rewind play (`line_end(1)`) to "coordinating", where the two pointers slide together; then 4 a second for the hairline, from the moment that they have joined (0.8 s after "coordinating") to "own" (line 5), where the seed-17 landings take over (`world.jitter`, each with its stated end). No jump survives the scene, and the last link of line 6 is fixed at 0.46 |
| The piles (S07 lines 5 and 6) | 17 (order only) | By index, u = (k + 0.5) / 30 on bar A. Line 5: k = 0 to 29, straight form. Line 6: three blocks, straight k = 0, 3, 6, 9, 12, 15, 18, 21, 24, 27; crossed k = 1, 28, 4, 25, 7, 22, 10, 19, 13, 16 (five mirror pairs k and 29 - k, so 1 - u stays on the grid); straight k = 2, 5, 8, 11, 14, 17, 20, 23, 26, 29. Seed 17 orders the landings inside each block. Both piles end exactly at the counts of 3.7 in every order (checked in 2,000 of 2,000) |
| The bloom of the field (S08) | 19 | 1,440 units, in seed order |
| The grey halo in the family (S08) | 29 | 5 hops a second, only among the units of the target family (`world.jitter`) |
| Breathing phases of the field | 31 | One phase for each unit |
| The target family (S08, S09) | 37 | The phases a and b of the family's curve (3.6), used again for the emblem's family mark (3.5, Object 6). The build stops if u1 or u2 is outside it |
| The web (S09) | 41 | The bright run's path in each tree. The fans have 27 ends for each copy and the sheet is one stroke: nothing in it can be counted |
| The lower part (S09) | 43 | The phase c of the wavy line (3.6). The build stops if u2 is not under it or u1 is |
| The twin (S04, S05) | 47 | Needles: jumps of up to 20 degrees, 6 a second. Lights: at most 2 changes a second, between `FAIL` 35% and `INK` 40% (`world.jitter`) |

---

## 4. Poses

A pose is the exact picture at a scene boundary. Scene N ends in pose P(N), and scene N+1 starts in it.
`world.pose("P03", scene)` builds it. Coordinates are canvas coordinates for the poses in frames TEST-IN, W and
STARE, and P-local coordinates for the poses in frames SPECK and P (P-local y = canvas y + 5.2).
Idle motion is at its rest value in a pose (rule 6 of 1.2).

**REST** is the rest state of the question. S05 reaches it, the pilot never changes it, and S10 returns to it.

| Object | REST |
|---|---|
| Pool | Full, all points starlight. Outlines gA, gB, gC, gD dashed at 40%. No other outline, no ring, no thread |
| Model | M0. No twin |
| Safety test | Split. Inner row: lights 0, 6, 10, 14, 20 red; the other seven pale. Outer row: all dark under the shade |
| Cost floor | Floor line; 14 outlined segments; end tick at x = 5.4; empty lane. No dial |
| Lone point | Until S05: at canvas (-5.4, -5.4), at 10%, off frame. From S06 it is the learner of the pilot. Absent from P08 onward |
| Text | None |

### P00: the first frame of the video

| | |
|---|---|
| Camera | TEST-IN: centre (1.6, 0.38), width 10.46 |
| Model | M0, needles trembling |
| Safety test | One-test arrangement. All 24 lights hollow. One request pulse is on its way from light 10 to the model, 30% of the way |
| Pool | At 10%; only its right fringe is in the frame |
| Lone point | At canvas (-5.4, -5.4), at 10%, off frame |
| Cost floor, boundary, pilot | Not there |
| Strings | None. Tag off |

### P01: after S01

| | |
|---|---|
| Camera | W: centre (0, 0), width 14.22 |
| Pool | Full. Outlines gA, gB, gC, gD dashed at 60% |
| Model | M0 |
| Safety test | One-test arrangement. Red: 0, 3, 6, 9, 10, 14, 15, 20, 21. The other 15 pale |
| Cost floor | Not there |
| Lone point | At canvas (-5.4, -5.4), at 10%, off frame |
| Strings | `data change` (24, `FOCUS`): left edge x = -6.1, baseline y = -1.4. Tag on. 2 words |

### P02: after S02

| | |
|---|---|
| Camera | W |
| Pool | Full. Outlines gA to gD at 60%; ten more outlines (8 points each) at 25% |
| Model | M0 |
| Safety test | As P01 |
| Cost floor | Floor line from x = -3.0; 14 outlined segments; end tick at x = 5.4. No dial. The lane is not drawn yet |
| Lone point | At canvas (-5.4, -5.4), at 10%, off frame |
| Strings | `safer?` (44, serif, `INK_HI`): left edge x = 4.15, baseline y = 0.4. Tag on. 1 word |

### P03: after S03

| | |
|---|---|
| Camera | STARE: centre (2.4, 0.43), width 12.47 |
| Pool | As P02 (only its right fringe is in the frame) |
| Model | M-star (the supposed tuning) |
| Safety test | Split. Inner row: all 12 pale, with a soft halo at 10%. Outer row: shade lifted (a hairline at radius 4.08, -40.5 to 44.0 degrees); lights 3, 9, 15, 21 red; the other eight pale |
| Cost floor | Faded to 0 (it would sit in the band of the tag) |
| Lone point | At canvas (-5.4, -5.4), at 10%, off frame |
| Strings | `held back` (24, `GREY_1`): left edge x = 4.9, baseline y = 0.45. Tag on. 2 words |

### P04: after S04

| | |
|---|---|
| Camera | W |
| Pool | Seven marked points and the threads, all at 10% (the threads hidden inside the model's core disc). gB: points gold, lifted 0.5, outline at 100%. Outlines gA, gC, gD at 40%. Ten more outlines at 25% |
| Model | M0, and its hollow gold twin at (0.5, -1.45), half size: needles at rest in M0 turned by +8 degrees; five hollow lights at radius 1.5 from (0.5, -1.45), at -20 to 20 degrees, resting at `FAIL` 35% |
| Safety test | Split. Inner row: 0, 6, 10, 14, 20 red, seven pale. Outer row: dark under the shade |
| Cost floor | As P02 (back at full level) |
| Lone point | At canvas (-5.4, -5.4), at 10%, off frame |
| Strings | `associated with this answer` (24, `INK` at 40%): left edge x = -6.1, baseline y = -1.4. Tag on. 4 words |

### P05: after S05

| | |
|---|---|
| Camera | SPECK: centre at canvas (-5.4, -5.4), width 10.16 |
| The lone point | At the centre of the frame (P-local (-5.4, -0.2)), at its rest level, halo at rest |
| Boundary | Open, at P-local y = 2.2 (on screen 3.36 above the centre) |
| The question | REST, live, at 15%; the cost floor and the lane faded to 0. Nothing of it is in the frame but the boundary's edge |
| Strings | None. Tag off |

### P06: after S06

| | |
|---|---|
| Camera | P: centre at canvas (0, -5.2), width 14.22 |
| The question | REST at 15% above the boundary (P-local y from 2.2 to 4.0): lights 0, 1 and 3, the lower tip of light 2's ring and the lower end of the shade, all grey (light 0's core is grey while the camera is on the pilot). Cost floor and lane at 0 |
| Boundary | Open, at y = 2.2 |
| Fork | Start (-5.4, -0.2): a `GREY_1` dot of radius 0.05 with no halo. Copy A (blue): path through (-3.9, 0.55) and (-2.4, 1.03) to its head at (-0.9, 0.92). Copy B (violet): path through (-3.9, -0.2) and (-2.4, 0.12) to its head at (-0.9, 0.09). Rings (radius 0.15) at x = -4.65: lit on copy A (y = 0.17), hollow on copy B (y = -0.2). The first white path, the dotted steps, the three stubs and the thread to bar A of line 1 are gone |
| Bars | Bar A at y = -1.35: widths 0.470, 0.277, 0.254; its pointer rests at u = 0.24 (segment 1). Bar B at y = -2.3: widths 0.343, 0.108, 0.549; its pointer rests at u = 0.78 (segment 3) |
| The comparison | A plain white segment from head to head at x = -0.9, from y = 0.09 to 0.92, under the heads, with no caps |
| Strings | `one event`: centred x = -4.9, baseline y = 0.75. In one column, left edge x = -0.3: `copy A` (baseline 0.86), `the comparison` (0.40), `copy B` (-0.06). Tag on. 8 words |

### P07: after S07

| | |
|---|---|
| Camera | P |
| The question, boundary | As P06 |
| Fork | At 45%: the faint tree of the 40 futures (ghosts at 14% of the fork's level, once for each distinct path), and the future of P06, bright up to step 1: its heads at (-2.4, 1.03) and (-2.4, 0.12); its step-2 part is a ghost. No comparison segment |
| Bars | Step-2 widths as in P06. One straight link through both bars at 0.46 of the bar length; on each bar the segment that it lands in is lit: segment 1 of bar A and segment 3 of bar B, the bright future's step-2 pair. Complete piles of the line-6 landings: above bar A 14, 8, 8 dots; under bar B 10, 4, 16 |
| Strip | Axis at x = 4.3 from y = -1.65 to 1.95. The ticks of exactly the 40 futures, dimmed to a third of their level (10% to 23%). Centre line at y = -0.05. Band at half-height 0.587 (straight). No ghost edges |
| Strings | `copy A` (right edge x = -4.45, baseline y = -1.44); `copy B` (right edge x = -4.45, baseline y = -2.39); `variance` (44, serif, `INK_HI`): right edge x = 3.75, baseline y = 1.0; `coupling` (44, serif, `INK_HI`): left edge x = 1.2, baseline y = -1.98. Tag on. Citation off. 6 words |

### P08: after S08

| | |
|---|---|
| Camera | P |
| The question, boundary | As P06 |
| Field | Parked: centre (4.4, 0.95), radius 1.1. The family's irregular outline (3.6). All units one grey (`GREY_2` at 60%); no unit is lit; no other part is marked |
| Scale | Zero tick at x = -5.6, from y = -2.75 to -1.0. Track 1 at y = -1.3, empty. The white marker (glow radius 0.12) rests on the zero tick at (-5.6, -1.3). Condition line at x = 4.4, from y = -2.7 to -0.6, at 85%, no glow. Track 2 is not drawn yet |
| Longer-horizon test | Faint (16%) dotted fork from the top end of the condition line: stem to (4.9, -0.5), branches to (6.2, -0.25) and (6.2, -0.5) |
| Lone point, toy | Absent: the S07 picture dissolved at the start of S08 |
| Strings | `variance reduction` (left edge x = -5.45, baseline y = -1.0); `best baseline` (left edge x = -5.45, baseline y = -2.72); `≥20%` (44; left edge x = 4.6, baseline y = -1.5); `target family` (24, `INK`): right edge x = 3.1, baseline y = 0.85. Tag off. 7 words |

### P09: after S09

| | |
|---|---|
| Camera | P |
| The question, boundary | As P06 |
| Field | Parked. Every unit at 40%, inside and outside the family alike, except u1 (upper) and u2 (lower), which are lit. The family outline, and the second curve round its lower part, at their levels |
| Scale | Zero tick. Trail 1 from x = -5.6 to 3.65 with its head (glow radius 0.12, at rest). From x = 3.65 to 4.4 there is only the bare hairline of track 1: nothing fills it and nothing lights it. Track 2 with trail 2 from x = -5.6 to 1.45 and its head. Condition line at 100%, no glow. No ring beside either result |
| Longer-horizon test | As P08: faint (16%), unlit, at the top end of the line |
| Strings | `variance reduction`; `best baseline` (baseline -2.72); `≥20%` (baseline -1.5); `about` (32, serif) and `18.5%` (64) on one baseline y = -1.0, right edge x = 3.65; on one baseline y = -2.0, `full suppression` (24, right edge x = -1.2), `about` (32, serif) and `14.1%` (44, right edge x = 1.45); `strongest` (24): right edge x = 3.1, baseline y = 0.9, with its two thin threads (`INK` at 15%) from (3.22, 0.96) to u1 and to u2 (3.10). Tag off. 12 words (`≥20%` is one) |

### P10: after S10

| | |
|---|---|
| Camera | W |
| The question | REST, live, at 35%, with the cost floor back; light 0 red again |
| Boundary and emblem | Closed curve, centre (-5.4, -1.6), 1.6 x 0.92, `INK_HI` at 100%, stroke `W_BOLD`. The emblem inside it (3.5, Object 6), with its family mark round both white dots |
| Strings | `the pilot` (24, `GREY_1`): left edge x = -4.38, baseline y = -1.7. Tag on. 2 words |

### P11: the last frame before the fade

| | |
|---|---|
| Camera | W |
| The question | REST at 100%, with the shade down over the outer row, and two changes supposed: the outlines of gA and gD dashed at 100%, each with a faint gold tint at 12% inside. Two dashed gold beams from gA and gD through the model's core to its right rim, at 30% |
| The ranges | Between the model and the inner row: the dashed hairline at y = -0.2 (x 1.75 to 3.0). Two dotted gold intervals with dotted caps, overlapping: gA's on y = 0.66 (x 1.8 to 2.75), gD's on y = 0.16 (x 2.1 to 3.05) |
| Boundary and emblem | As P10: the emblem with its family mark round both white dots |
| Strings | `the pilot`; sign-off, two lines (32, serif): `Notes from an ongoing` (baseline y = 2.9) and `research project` (baseline y = 2.3), centred at x = 0.5. Tag on. 8 words |

---

## 5. Script and storyboard

Eleven scenes. First person, the post's voice. A line is one voice call: one sentence, or two short sentences
in one breath. The lines below are the narration; `design/script.json` holds the same text, character for
character.

How to read the tables.

- **Lines to speak.** "Pause after" is the silence from the end of the line to the first word of the next line,
  in seconds. For the last line of a scene it runs across the scene boundary: the scene's tail, then the 0.40 s
  before the next scene's first word (in the last scene all of it is tail). "Pause inside" sets the length of a
  pause that the voice makes at a mark inside the line. Speed 1.0 is the voice's normal speed. A *Say* note gives
  the markup that is sent to the voice; the words do not change.
- **Beats.** "Cue" is where the row starts, in the kit's 0-based line numbers (rule 2 of 1.2). Each row is one
  play until the next row's cue, or to the end of the scene (rule 3). "t" is seconds from the start of the
  scene: an estimate from the builder's text analysis that the build never uses. The **bold** word is where the
  key change lands. A time in parentheses is a window inside the row's play. `lag_ratio` is Manim's lag ratio
  inside the stated run time. "Born from" names the object that a new thing comes out of. An empty camera cell
  means that the camera does not move. A string is given exactly, with its size and colour; places are in
  sections 3 and 4.

Voice: Kokoro `af_heart`. For the first build, listen to "AI’s" and "post-training" (the builder has a reviewed
two-stress reading for "post-training"); `1,440` is read "one thousand four hundred forty" and takes about 1.8 s.
Each question is a wh-question with 0.9 s or more after it. Three lines carry a stress mark in `say` (S01 line 4
on "which", S09 line 4 on "not", S11 line 3 on "that", which Kokoro's text analysis otherwise reads as a weak
conjunction); the voice probe found such a stress on a function word mild and safe (`research/tts-probe.md`,
2.6). Each mark stays one token, so the word timing does not change. S03 line 1
asks for a 0.25 s pause after “safer”; if Kokoro makes no silence there, the build stops and says so, and section
8, point 8, has the fallback.

---

### S01 Which one would actually help? (about 23 s)

**Purpose.** Open inside one failing test, show that it fails again and again, show what we could change, and
end on the question that the viewer now has.

**Opening pose.** P00.

**Lines to speak.**

| # | Words to speak | Pause after (s) | Speed | Pause inside | Ledger |
|---|---|---|---|---|---|
| 1 | Suppose a model repeatedly fails a particular safety test. | 1.2 | 1.0 | none | C07, exact |
| 2 | We have several ideas for changing the examples used in its post-training, the stage where an already trained model is taught how to respond. | 0.5 | 1.0 | 0.35 after `post-training,` | C08, C09, exact |
| 3 | We could remove a group of examples. We could replace them with different ones. | 0.5 | 1.0 | 0.4 after `examples.` | C10, C11, exact |
| 4 | Each change sounds reasonable, but which one would actually help? | 1.2 | 0.9 | none | C12, C13, exact |

*Say* (stress markup only; the words do not change): line 4 is sent as `Each change sounds reasonable, but [which](+2) one would actually help?`.

**Beats.**

| Cue (kit, 0-based) | Line · anchor (t in s) | On screen, and what moves (duration) | Born from | Camera | Strings and numerals |
|---|---|---|---|---|---|
| `at(0, lead=0.4)` | Lead and line 1, "**Suppose** a model repeatedly" (0.0 to 1.9) | One test, slowly (one play): the request pulse runs from light 10 into the model's rim (0.5 s); the needles ripple from right to left (0.4 s); an answer pulse runs back (0.5 s). | Light 10; the model | TEST-IN | `model` (24, `MODEL`) on "model", late in the ripple |
| `at_word(0, "fails")` | "repeatedly **fails** a particular safety test." and the pause (1.9 to 5.0) | Light 10 turns red, with a glow (0.3 s). Then the sweep: all 24 lights exchange pulses with the model (1.0 s, `lag_ratio` 0.05): 9 red, 15 pale. The lights go hollow (0.3 s) and the sweep runs again, faster (0.6 s): the same nine are red. And again (0.4 s): the same nine. The third sweep ends in the silence before line 2. | The answer pulse; the lights | | Tag on, with the first red light. `safety test` (24, `INK`) from "safety" |
| `at(1)` | Line 2, "We have several **ideas** for changing the examples used in its" (5.0 to 8.4) | We pull back. `model` and `safety test` fade as the move starts. The pool comes into the frame and lights up from the model's side outward (2.0 s); late in the move the whole pool brightens once (0.6 s). | The camera shows it | TEST-IN to W, 3.0 s from `at(1)` (`clock_move`); it arrives at about 8.0 | `post-training examples` (24, `DATA`) in the label slot, as the camera arrives |
| `at_word(1, "post-training")` | "its **post-training**, the stage where an already" (8.4 to 10.8) | A lens opens on the pool (0.8 s): the magnifier of Object 1 over (-3.9, 0.9). The 20 points under it open into example glyphs: a request stroke over a response stroke (0.8 s, `lag_ratio` 0.3). | The pool's points | | |
| `at_word(1, "trained")` | "already **trained** model is **taught** how to respond." and the pause (10.8 to 13.2) | The needles of the model hold still for 1 s: it is already trained. Then the response strokes brighten one after another, left to right (1.4 s). A faint copy of each drifts to the model's left rim; where it arrives, a needle glints. | The glyphs | | |
| `at(2)` | Line 3, "We could **remove** a group of examples." (13.2 to 15.9) | The lens closes into the pool and `post-training examples` fades (0.5 s). In the same play group gA turns gold (0.4 s), then its points lift 0.6 up and 0.4 left while they fade to 0 (1.2 s, `lag_ratio` 0.02): removed. Its holes stay. | The pool | | |
| `at_word(2, "replace")` | "We could **replace** them with different ones." and the pause (15.9 to 18.2) | 40 different points (starlight core, gold halo) fly in on arcs from the lower left into the same holes (1.4 s). | Outside the frame (a lone arrival: they are new) | | |
| `at(3)` | Line 4, "Each **change** sounds reasonable," (18.2 to 20.3) | The change undoes (1.0 s): the different points leave the way they came, and gA's own points come back from the upper left, fading in. A dashed gold outline stays round gA. Outlines draw round gB, gC and gD (0.6 s each, 0.3 s apart). | The pool | | `data change` (24, `FOCUS`) in the label slot, on "change" |
| `at_word(3, "which")` | "but **which** one would actually help?" and the tail (20.3 to 22.8) | The four outlines pulse one after another, round and round (0.35 s each). On "help" the nine red lights pulse together once. | | | |

**Closing pose.** P01.

**Numerals shown.** None. **Words on screen, most at one time:** 3.

**Honesty.** "Suppose" is the post's word, and the tag is on from the first red light: no real model and no real
test (ledger X06). Nine red lights of 24 are a drawing of "repeatedly fails", not a rate; no numeral. The
request and the answer are pulses and strokes: the video invents no prompt and shows no harmful request. Remove
and replace are the only two kinds of change (X11), and replace acts on the same group, as in the post
("replace them"). Four outlines stand for "several"; no count is said. No cost is shown yet.

**Building blocks.** `world.Model` (needles from the kit's tapered `Stroke`), `world.TestArc` (one `DotCloud`
for the 24 cores with a glow for each point), `world.Pool` (`DotCloud` with `drift`), `ShowPassingFlash`
pulses, `hull_blob` outlines, `cloud.to(..., arc=)` for the group (probe `repo-ml` P2), the lens (`set_clip`
over a `BG` disc), `follow_label`, the camera move of kit section 3.

**Risk: medium.** The pull-back redraws about 800 points and 90 strokes on each frame (cheap as clouds). The
lens is new. TEST-IN is at zoom 1.36, so that light 0's red glow stays above the band of the tag. **Fallback:** no
lens; 8 points that are at least 0.5 apart open into glyphs in place. If the first
frame reads as empty at a small size, start at W with the pool dark and no camera move.

---

### S02 Somewhere in that sentence (about 29 s)

**Purpose.** Show the direct way and what it costs, take the payment back, and let the author say the question
and the driest line of the post, with the title as its punchline.

**Opening pose.** P01.

**Lines to speak.**

| # | Words to speak | Pause after (s) | Speed | Pause inside | Ledger |
|---|---|---|---|---|---|
| 1 | We could retrain the model for every change and compare the results. | 0.3 | 1.0 | none | C14 (“option” becomes “change”) |
| 2 | That gives us something concrete to measure, but repeating the process for many changes could become expensive. | 0.7 | 1.0 | none | C15, C16 (“many candidate changes” becomes “many changes”; keeps “repeating the process”, “could become”) |
| 3 | I’m trying to work out whether we can make a better decision about an AI’s training data, before paying to retrain it for every possible decision. | 0.9 | 1.0 | 0.35 after `data,` | C04, exact, one comma added |
| 4 | There is a fairly simple question somewhere in that sentence. | 0.8 | 0.9 | none | C05, exact |
| 5 | Getting it into a form I can actually test is taking a little longer. | 1.2 | 1.0 | none | C06, exact |

**Beats.**

| Cue (kit, 0-based) | Line · anchor (t in s) | On screen, and what moves (duration) | Born from | Camera | Strings and numerals |
|---|---|---|---|---|---|
| `at(0)` | Line 1, "We could **retrain** the model for every change" (0.4 to 2.9) | One retrain, slowly (one play of 2.2 s): gA's points lift out (0.4 s); the rest of the pool sends a stream of starlight copies along a shallow curve into the model's left rim (1.4 s); the needles turn to pattern MA, ring by ring; grey sparks fall from the model's lower rim on an arc down and to the left, onto segment 1 (0.6 s), and the floor line draws left to right from x = -3.0 (0.8 s, starting with the sparks); segment 1 lights. `data change` fades. | The pool; the model | | |
| `at_word(0, "compare")` | "and **compare** the results." and the pause (2.9 to 4.3) | The test is swept once on the retrained model (0.6 s): seven red (3.12). A copy of the lights shrinks and lands on the end of segment 1 as a mini dial (0.8 s). | The test lights | | |
| `at(1)` | Line 2, "That gives us something concrete to **measure**," (4.3 to 8.3) | Two more retrains, faster, with no reset between them. gB (1.0 s): gA's points fall back into their holes as gB's lift out, and the stream turns the needles from MA to MB; its dial has 9 red, no change. gC (0.8 s): 8 red. Segments 2 and 3. From "measure" the three dials pulse in turn. | The model; the test lights | | |
| `at_word(1, "many")` | "but repeating the process for **many** changes could become **expensive**." (8.3 to 10.3) | Ten more dashed outlines appear across the pool (0.6 s, `lag_ratio` 0.12). The band runs on along the floor with a glowing head (1.5 s, linear), segments 4 to 14, and its end tick lands on "expensive". | The pool; the band | | `computation` (24, `GREY_1`) at the band's left end, on "expensive" |
| `line_end(1)` | The pause and line 3, "I’m **trying** to work out whether we can make a better" (10.3 to 13.6) | The model and the pool come to rest: gC's points back, the needles in M0; the lights show their first answers, nine red (0.6 s). From "I’m" the picture takes it back: segments 14 to 1 turn from solid to outline, from right to left (1.4 s). The three dials fade. | | | |
| `at_word(2, "decision")` | "a better **decision** about an AI’s training data," (13.6 to 15.9) | A thin white ring opens on gA and hops gA, gC, gD, gB (about 0.55 s a hop). The outline that it visits brightens. It does not settle. | Outline gA | | |
| `at_word(2, "before")` | "before **paying** to retrain it for every possible decision." (15.9 to 18.9) | A light runs along the whole outlined band, left to right (2.4 s, linear). On "every" all 14 outlines in the pool pulse in a wave. | | | |
| `line_end(2)` | The pause and line 4, "**There** is a fairly simple question somewhere in that sentence." (18.9 to 24.0) | The ring fades. The world dims to 35% (0.9 s). `computation` fades. From line 4's first word (a window from 0.9 s) the post's title writes itself in the middle of the frame, two lines (1.8 s, complete by "somewhere"). It holds to the end of the 0.8 s pause after the line. The pool keeps drifting under it. | | | Title (44, serif, `INK_HI`, backstroke): `Which training data should we change` / `to make an AI safer?` |
| `at(4)` | Line 5, "**Getting** it into a form I can actually test is taking a little **longer**." and the tail (24.0 to 28.6) | The title lets go (1.4 s): every word except the last fades out glyph by glyph, left to right; `safer?` slides on a shallow arc to its place right of the test lights. In the same play the world returns to 100% from left to right (pool, model, lights, floor; 2.6 s, `lag_ratio` 0.3), in a window that ends with the lights' part on "longer" (by the estimates the group runs from 25.2 to 27.8 s), complete at least 0.8 s before the scene ends. Once placed, `safer?` stays still and does not settle into the test: only its backstroke halo breathes. | The title | | `safer?` (44, serif, `INK_HI`) |

**Closing pose.** P02.

**Numerals shown.** None. **Words on screen, most at one time:** 11 (the title alone).

**Honesty.** "We could" is a supposed case: every solid segment and every dial is taken back in line 3, so at the
end nothing is retrained and nothing is paid. The direct way gets its credit: it gives real dials (ledger H25).
The supposed dials differ: two show fewer red and one shows no change. The picture shows that results differ,
not that a data change is known to help, and it is taken back in line 3 (X08, X10). The band has an end: "could
become expensive" is long, not endless, and it has no
unit and no price (X12). The title is the post's title (C01) in sentence case. It is the only sentence shown in
the video, and it is not the sentence that the voice says. The title stands beside the line; the post does not
say that the title is the question in C04.

**Building blocks.** Stream and sparks as small `DotCloud`s; `world.CostFloor`; `born_from` for the dial;
`T`, `lines`, `enter` and `backstroke` for the title; `hand_over` for `safer?`.

**Risk: medium.** Three retrains and eleven more segments in 9 s. **Fallback:** one slow retrain with its dial,
then the band runs with no further dial. If the title is hard to read over the model, take the world to 25% for
those 4 s.

---

### S03 The test we have been staring at (about 17 s)

**Purpose.** Make "specific" and "new" two things that happen to the test lights, and spring the trap in
silence.

**Opening pose.** P02.

**Lines to speak.**

| # | Words to speak | Pause after (s) | Speed | Pause inside | Ledger |
|---|---|---|---|---|---|
| 1 | “Make the model safer” leaves rather a lot of room to congratulate ourselves. | 0.8 | 1.0 | 0.25 after `safer”` | C22, exact |
| 2 | We need a failure we can define and measure, then tests held back while we choose the change. | 0.35 | 1.0 | 0.3 after `measure,` | C23, C24 (“examples held back from the process of choosing the change” becomes “tests held back while we choose the change”; “tests” from C20) |
| 3 | Otherwise, we could end up very good at fixing the test we have been staring at. | 2.3 | 0.9 | none | C25, exact |

**Beats.**

| Cue (kit, 0-based) | Line · anchor (t in s) | On screen, and what moves (duration) | Born from | Camera | Strings and numerals |
|---|---|---|---|---|---|
| `at(0)` | Line 1, "“Make the model **safer**” leaves rather a lot of **room**" (0.4 to 3.3) | The 24 lights go out of focus (1.1 s): each core swells into a pale glow of the light cloud, the rings fade, and the red ones cannot be told from the rest. The test is one soft, pleasant band, and `safer?` sits in it. Then the band swells and widens toward "room" (1.5 s). | The lights | | `safer?` |
| `at_word(0, "congratulate")` | "to **congratulate** ourselves." and the pause (3.3 to 5.4) | Two pleased pulses (0.6 s each): somewhere in the haze a light changes, we cannot see which way, and the whole band brightens. `safer?` brightens once with the second pulse; it does not move. | | | |
| `at(1)` | Line 2, "We need a failure we can **define** and **measure**," (5.4 to 8.2) | The haze thins (1.2 s) and on "define" snaps back into 24 sharp lights (0.5 s; an allowed snap). `safer?` dissolves into them. On "measure" a white tick of light visits each red light in turn (9 in 0.8 s). | The haze | | `safer?` leaves |
| `at_word(1, "tests")` | "then tests **held** back" (8.2 to 9.4) | Every second light slides out along its radius to an outer row (window 0 to 0.8 s, `lag_ratio` 0.04). Their cores go dark (0.4 to 1.0 s). The shade wipes in over the outer row (0.6 to 1.2 s). | The same 24 lights | | `held back` (24, `GREY_1`): left edge x = 4.9, baseline y = 0.45, with `late(0.6)` |
| `at_word(1, "choose")` | "while we **choose** the change." and the pause (9.4 to 10.5) | One gold pulse runs from the outlines in the pool, through the model, to the inner row (1.0 s). The inner rings flash. It does not reach the outer row. | The outlines | | |
| `at(2)` | Line 3, "**Otherwise**, we could end up very good at" (10.5 to 12.8) | Round 1 (1.2 s): a stream of hollow points (rule 18 of 1.2) comes from the pool, the needles shift a little, the inner row is swept. Red lights on the inner row: 0, 6, 10, 14 and 20, then 6, 10 and 14 (3.12). As the camera leaves W, the cost floor fades to 0 (rule 10 of 1.2). | The pool | W to STARE, 3.9 s from `at(2)` (`clock_move`, which runs on through the next row) | |
| `at_word(2, "fixing")` | "very good at **fixing** the test we have been **staring** at." (12.8 to 15.1) | Round 2 (0.9 s): three, then one (light 10). Round 3 (0.7 s): one, then none. The inner row is all pale and glows softly. The test fills the height of the frame. | | Arrives on "staring" (about 14.4) | |
| `line_end(2)` | The silence (15.1 to 17.0) | From 0.3 s in: the shade lifts (0.6 s) and leaves its hairline at radius 4.08. One sweep runs over the held-back lights (0.6 s): lights 3, 9, 15 and 21 turn red, the same four as before. The others turn pale. Hold. | | | |

**Closing pose.** P03.

**Numerals shown.** None. **Words on screen, most at one time:** 2.

**Honesty.** "Could end up" is a supposed trap: the three streams are hollow and the tag is on. No model was
tuned, and no held-back test exists yet: the post says "We need" (X16). The voice says the held-back tests are
kept out of the choice ("while we choose the change"), and the gold choosing pulse never reaches them. The
held-back lights come out exactly as
they were in the first sweep. So the picture says "the fix did not reach the tests that we did not stare at".
It does not say that a change makes held-back tests worse. The haze is a picture of the phrase "a lot of room",
not a quantity. The supposed tuning is undone in the first second of S04, not inside this silence. The push
stops at zoom 1.14, so every light and the shade stay whole and inside the frame, clear of the band of the tag.

**Building blocks.** The light cloud's per-point glows that scale and fade (`set_blend("screen")`),
`MoveToTarget` along radii, a clip wipe for the shade (`set_clip`), probe `repo-ml` P6 (a cover over a held-back
group), the camera push.

**Risk: low to medium.** The haze must read as "vague", not as "broken". **Fallback:** the lights fade to 25%
and one soft glow fades in over them. If the push is too much with the label, hold at W and skip the push.

---

### S04 Looking back, or asking what if (about 15 s)

**Purpose.** Answer the viewer's first idea ("find the examples behind the bad answer and delete them"): one
question runs backward along threads, the other makes a fork.

**Opening pose.** P03.

**Lines to speak.**

| # | Words to speak | Pause after (s) | Speed | Pause inside | Ledger |
|---|---|---|---|---|---|
| 1 | Finding examples associated with a bad answer does not automatically tell us which to remove to improve future answers. | 0.8 | 1.0 | none | C32 (“training examples” becomes “examples”; “which examples to remove” becomes “which to remove”; keeps “associated with”, “does not automatically” and “to improve future answers”) |
| 2 | One question looks back at how the model got here. The other asks what would happen if we changed something. | 1.5 | 1.0 | 0.45 after `here.` | C33, C34, exact |

**Beats.**

| Cue (kit, 0-based) | Line · anchor (t in s) | On screen, and what moves (duration) | Born from | Camera | Strings and numerals |
|---|---|---|---|---|---|
| `at(0, lead=0.4)` | The first second and line 1, "Finding examples" (0.0 to 1.5) | The supposed tuning undoes itself (0.8 s): the needles go back to M0, the inner row goes back to its five red lights, the shade settles over the outer row and its lights go dark. `held back` fades. The cost floor fades back in as the camera returns. | | STARE to W, 2.8 s, `GLIDE` (`clock_move`, which runs on through the next row) | |
| `at_word(0, "associated")` | "examples **associated** with a bad answer does not" (1.5 to 3.5) | The red light 10 flares (0.3 s). A white thread leaves it to the left, passes behind the model's core disc (hidden inside radius 1.15; it touches no needle), and fans into about 70 hair-thin threads that end on scattered points of the pool (1.6 s; each thread is a passing flash). Seven of their end points, spread over the pool, are marked: each core brightens to `INK` at 90% with a small glow (radius 0.12). No ring. The threads stay at 15%. | The failed light | | `associated with this answer` (24, `INK`) in the label slot, late in the play |
| `at_word(0, "automatically")` | "does not **automatically** tell us which to remove to improve **future** answers." and the pause (3.5 to 7.8) | The outlines gA, gB, gC and gD brighten in turn (0.5 s each). The marked points stay white: none turns gold, none lifts, no outline closes round them. On "future" the five red lights of the inner row pulse once, together (0.8 s): the answers we would want to improve. Nothing in the pool changes with them. | | | |
| `at(1)` | Line 2, "One question looks **back** at how the model got here." (7.8 to 10.9) | A slow current of light runs along the threads from the red light back to the pool, right to left (2.2 s, linear). | The threads | | |
| `at_word(1, "other")` | "The other asks what would **happen**" (10.9 to 12.6) | The threads and the seven marked points dim to 10%, and the label to 40% (0.8 s). Outline gB brightens. Its points turn gold and lift 0.5 (1.0 s). No marked point is in gB. The other three outlines settle at 40%. | The pool | | |
| `at_word(1, "changed")` | "if we **changed** something." and the pause (12.6 to 14.5) | A hollow gold twin of the model slides out of the model, down to (0.5, -1.45), at half its size (1.4 s). Its needles are outlines that jump and will not settle. Five hollow lights grow from its right rim, at radius 1.5 from its centre; each changes, at most twice a second, between `FAIL` at 35% and `INK` at 40% (`world.jitter`, seed 47, running on into S05). Nobody knows yet. | The model | | |

**Closing pose.** P04.

**Numerals shown.** None. **Words on screen, most at one time:** 4.

**Honesty.** This is the "linked to, not caused by" picture (brief rule 2.6). The voice says "associated with"
and "does not automatically" (H37, H38), and the label uses the post's word. The threads are thin, many and
weak; they pass behind the model's core disc and touch none of its needles, so they are not drawn as a path
through it; they run backward from the answer, and they fade. The seven marked points have no ring: S02 taught
that a thin white ring is the mark of choosing. They stay white: none turns gold, none lifts and no outline
closes round them, so the picture does not say which examples to remove, or that our groups have missed the
culprits. Seven is not nine, so the marks do not echo the red lights one for one. The what-if lifts gB, which
holds no marked point: the threads do not choose the change. The field of threads is not thrown away: it only
does not choose a change. The line keeps both hedges and the post's purpose clause ("to improve future
answers"); on "future" only the red lights pulse, so nothing in the pool is shown as the way to improve them. The
twin's lights stay undecided: the post gives no answer to "what would happen". The twin is hollow: nobody has
made that change.

**Building blocks.** `influence_arcs` and `flash_along` (probe `repo-ml` P3) in white, drawn under the model's
core disc; `bake` for the resting threads (the camera is still by then); `born_from` for the twin; needles as
outlines with a seeded jump (`world.jitter`).

**Risk: medium.** This is the shortest scene. **Fallback:** 30 threads in place of 70. If 15 s is too short for a
render unit, render S03 and S04 as one unit; P03 is then an inner pose.

---

### S05 A question, not a method (about 23 s)

**Purpose.** State the status plainly while the what-if is still open, say what a shortcut must beat, keep every
object that would show a method empty, and go through the door to the only work that is done.

**Opening pose.** P04.

**Lines to speak.**

| # | Words to speak | Pause after (s) | Speed | Pause inside | Ledger |
|---|---|---|---|---|---|
| 1 | This is a research question, not a method we have already shown to work. | 0.6 | 0.9 | none | C40, exact |
| 2 | If a shortcut takes as much computation as trying every change directly, it has not helped us very much. | 0.9 | 1.0 | 0.4 after `directly,` | C39 (“the shortcut” becomes “a shortcut”; “the alternatives” becomes “every change”) |
| 3 | I don’t yet have evidence that we can make this decision more cheaply or more reliably than strong existing methods. | 1.0 | 1.0 | none | C42, exact |
| 4 | The work we have completed so far is narrower. | 1.3 | 0.9 | none | C43, exact |

**Beats.**

| Cue (kit, 0-based) | Line · anchor (t in s) | On screen, and what moves (duration) | Born from | Camera | Strings and numerals |
|---|---|---|---|---|---|
| `at(0)` | Line 1, "This is a research **question**," (0.4 to 2.5) | The twin's five lights keep changing and do not settle: the what-if is still open. `associated with this answer`, the threads and the marked points fade (1.0 s). | | | |
| `at_word(0, "method")` | "not a **method** we have already shown to work." and the pause (2.5 to 5.1) | Over the whole row (`window(0, left)`) gB's points sink back and turn starlight; its outline stays dashed. The ten extra outlines fade out (1.2 s). Nothing is drawn for a method. The twin stays, hollow and undecided. | | | |
| `at(1)` | Line 2, "If a **shortcut** takes as much" (5.1 to 6.5) | Under the floor the shortcut lane draws from its left end (0.8 s). | The floor | | `a shortcut` (24, `INK`) and `computation` (24, `GREY_1`) at the left ends of the two rows |
| `at_word(1, "computation")` | "**computation** as trying every change **directly**," (6.5 to 9.6) | Bits of work fall into the lane (1.0 s, `lag_ratio` 0.1): six small ticks drop from the four outlines in the pool; one segment drops from the twin, with sparks, as its needles settle for a moment; one pulse drops from the held-back row. They come down on arcs right of x = -2.8, clear of the two labels, and line up from the lane's left end: 1.6 long. In the same play, as the last piece lands, the lane goes on from their end as a dotted line, steadily (linear), and reaches the end tick of the direct band as "directly" ends. So a short solid lane is never held alone. The tick has stood there since S02. | The pool, the twin, the held-back row; the band | | |
| `at_word(1, "it")` | "it has not **helped** us very much." (9.6 to 11.2) | The end tick grows down across both rows (0.4 s). The two ends are level. Both pulse once, together, on "helped". Nothing else happens. | | | |
| `line_end(1)` | The pause and line 3, "I don’t yet have **evidence** that we can make this decision" (11.2 to 15.2) | (0 to 0.8 s) It was an "if": the dotted line draws back, and the end tick goes back to its own height. From line 3's first word the outlines gA, gB, gC and gD pulse once in turn (0.5 s each): the decision is still open. On "evidence" (a window of 1.2 s) the pieces of work lift out of the lane and dissolve, and the twin and its small arc dissolve back into the model. The lane is empty. | | | |
| `at_word(2, "cheaply")` | "more **cheaply** or more **reliably**" (15.2 to 17.2) | On "cheaply" nothing moves on the lane: it stays empty and still. On "reliably" the shaded held-back row pulses once (0.8 s) and stays dark. | | | |
| `at_word(2, "existing")` | "than strong **existing** methods." (17.2 to 18.2) | Nothing new is drawn. The outlines settle at 40%. `computation` and `a shortcut` fade. The question is in REST. | | | |
| `line_end(2)` | The pause (18.2 to 19.2) | The question dims to 60% (1.0 s). The pool keeps drifting. | | | |
| `at(3)` | Line 4, "The work we have completed so far is **narrower**." and the tail (19.2 to 22.8) | One camera move of 3.4 s (`clock_move`, `GLIDE`) on one rounded path: first straight down from W toward (0, -5.4) at full width, while the boundary draws from left to right as the frame crosses it (clip wipe). Above it the question sinks to 15%, and the cost floor and the lane fade to 0. The pool leaves the top of the frame; only then does the frame turn left and narrow onto SPECK (the turn begins 0.6 s before the straight descent would end). In the last 1.0 s of the move the lone point, which was there in the dark all the time, brightens from 10% to its rest level; it ends at the centre of the frame. Its halo breathes. | Nothing: the point is its own thing | W through (0, -5.4) to SPECK, 3.4 s from `at(3)` | Tag off as the test lights leave the frame |

**Closing pose.** P05.

**Numerals shown.** None. **Words on screen, most at one time:** 4 (while the S04 label fades).

**Honesty.** The first status sentence (H18) comes while the hollow twin of S04 is still on screen, so "This" is
the what-if question, and nothing is drawn for a method. The equal lengths are the post's "If" (C39), drawn
dotted, and they are taken back. The three kinds of work in the lane are the post's "score candidates",
"retrain selected candidates" and "validate the final choice" (C36, C38), without words and without a named
technique (X13). The lane is never filled, and at rest it is an empty lane, not a shorter band under a longer
one: no shortcut is shown to be cheaper (X01). Nothing is drawn for "strong existing methods": the picture must
not say what they are or what they cost (X04). The second status sentence (H19) is spoken while the lane stays
empty and still and a shaded row stays dark: nothing runs on the lane, not even a short way. The pilot comes on
the post's own hinge (C43), straight after the status sentences; no question presents it as the tested part of
the main question (X18, X21). The point of the pilot is not born from the model, and nothing travels
from the question to it: the post has no sentence that joins the pilot to the data-change decision (X21, O8).
The camera first goes straight down, so the pool has left the frame before the point brightens and before the
frame narrows: the move does not say "we zoomed into one example of the pool" (X20). The point is cool grey with
a white halo and is larger than a point of the pool.

**Building blocks.** `world.CostFloor`; a dashed line shown through a clip (`set_clip`); `world.clock_move` on
one rounded path with `GLIDE`; the boundary's clip wipe; the question stays live (3.9, item 7).

**Risk: low to medium.** Lines 1 and 3 are quiet on purpose; the events must still land on their words.
**Fallback:** the three kinds of work fall as one group. If the two legs read as fussy, use one move from W to
SPECK and dim the pool to 10% as it starts.

---

### S06 A tiny learner (about 18 s)

**Purpose.** Show the pilot's setup as it was: one learner, one event, two copies, and both carry on.

**Opening pose.** P05.

**Lines to speak.**

| # | Words to speak | Pause after (s) | Speed | Pause inside | Ledger |
|---|---|---|---|---|---|
| 1 | We built a tiny learner, to study how suppressing the learning contribution from one event changes its later behaviour. | 0.5 | 0.9 | 0.3 after `learner,` | C44, exact, one comma added |
| 2 | One copy learns normally; in the other, that event’s contribution is suppressed. | 0.4 | 1.0 | 0.4 after `normally;` | C45, exact |
| 3 | Both then carry on learning. | 3.0 | 1.0 | none | C46, exact |

**Beats.** Coordinates are P-local.

| Cue (kit, 0-based) | Line · anchor (t in s) | On screen, and what moves (duration) | Born from | Camera | Strings and numerals |
|---|---|---|---|---|---|
| `at(0)` | Line 1, "We built a **tiny** learner, to study how" (0.4 to 2.8) | The point's halo swells once and settles (0.8 s). | | SPECK to P, 3.0 s from `at(0)` (`clock_move`, which runs on through the next row) | `tiny learner` (24, `INK`): left edge x = -6.3, baseline y = -0.95, under and left of the point, clear of its halo; it lands in the 0.3 s pause after "learner," |
| `at_word(0, "suppressing")` | "**suppressing** the learning contribution from one" (2.8 to 5.6) | A thread leaves the point, runs right to x = -4.16 and turns down to the top of bar A's tab (an L-curve), and the bar unrolls to the right (1.2 s): three grey segments. Three faint stubs fan out from the point: its three possible moves (0.5 s). | The point | Arrives at about 3.4 | Tag on, with the bar's first frame |
| `at_word(0, "event")` | "one **event** changes its later **behaviour**." and the pause (5.6 to 8.2) | The second segment of the bar lights (0.3 s), with no pointer: the event's choice is given, not drawn. The matching stub brightens, and the point takes one step along it to (-3.9, 0.55), with a tail (1.0 s). A white ring (radius 0.15) marks the middle of the step. From "behaviour" the segments of the bar shift to new widths (0.6 s): it learned. Two faint dotted steps reach on to the right (0.8 s). | The bar; the point | | `one event` (24, `INK`) above the ring |
| `at(1)` | Line 2, "One copy learns **normally**;" (8.2 to 10.3) | The point runs back along its tail to the start (0.6 s); the start stays as a small grey dot with no halo. Then the point takes the event's step again, in blue (0.9 s): it is now copy A. Its ring is lit. The white path, the dotted steps, the three stubs and the thread to bar A fade (0.6 s). `tiny learner` fades. | The point | | `copy A` (24, `MODEL`), riding 0.25 above and left of its head |
| `at_word(1, "other")` | "in the **other**, that event’s contribution is **suppressed**." and the pause (10.3 to 13.6) | A violet point leaves the same start. A copy of the bar as it was before the event slides down to the place of bar B, with a violet tab (0.8 s). Its second segment lights in the same way: the same choice. Its ring appears at the same x as copy A's ring, and goes hollow on "suppressed". The violet point travels level to (-3.9, -0.2) (0.9 s). Its bar does not change. | The start; bar A | | `copy B` (24, `COPY_B`), riding 0.25 below and left of its head |
| `at(2)` | Line 3, "**Both** then carry on learning." (13.6 to 14.9) | Step 1, in lock-step, slowly (1.3 s): a pointer drops on each bar, at different places (bar A: u = 0.57, segment 2; bar B: u = 0.18, segment 1). Each head moves: copy A to (-2.4, 1.03), copy B to (-2.4, 0.12). | Each bar | | |
| `line_end(2)` | The silence (14.9 to 17.5) | Both bars change their widths (0.5 s). Step 2 (1.0 s): pointers (bar A: u = 0.24, segment 1; bar B: u = 0.78, segment 3); heads to (-0.9, 0.92) and (-0.9, 0.09). Then a plain white segment draws from head to head at x = -0.9, under the heads, with no caps (0.5 s). The three labels settle in one column right of it (0.8 s). | The two heads | | `the comparison` (24, `INK`) |

**Closing pose.** P06.

**Numerals shown.** None. **Words on screen, most at one time:** 8.

**Honesty** (against `design/pilot-facts.md`, 2.1 to 2.5). A point of light, not a model: no layers, no needles,
no pool that feeds it. The event is the first step from the start; there is no long shared past. The event has
no pointer: its choice is given, and the randomness is only in the steps after it (pilot facts 2.2 and 2.5).
Pointers appear only at step 1 and step 2, so the event is never drawn as a random draw that the two copies
share, and nothing is coupled at the event (must-not 19). Copy B makes the same choice at the event, its step
still happens, its mark stays on the path, and it does not move: full suppression. Two steps follow the event,
in lock-step, and no more. The split is "different", not "worse": copy A goes up, copy B stays level, and then
each goes its own way. No axis, no number, no size of the gap. The bars that differ after the event, and that
change again after each step, are the feedback of C47 and C48: drawn, not spoken. Three segments agree with the
record; the count is not said. Copy B is violet, not gold, so it does not read as the model after a data change.
The comparison is a plain segment from head to head with no caps, so it does not look like an error bar; one
scene later only the band means a spread, and the comparison is never read as noise (pilot facts 2.12). The tag
is on from the bar's first frame.

**Building blocks.** `world.Fork`, `world.ChoiceBars`, `world.TOY`; `Runner` and `Trail` for heads and tails
(probe `repo-ml` P4); `stacked_bar` and `index_of` (probe `repo-prob` P2, without its counter and its title);
`follow_label`.

**Risk: medium.** Line 2 has four small events in 3 s; they are one `Succession`. **Fallback:** leave out the
three stubs and the dotted steps of line 1.

---

### S07 How the choices are paired (about 27 s)

**Purpose.** Define variance on a moving picture before it is needed, then show coupling as a mechanism in which
each copy keeps its own probabilities and only the pairing changes.

**Opening pose.** P06.

**Lines to speak.**

| # | Words to speak | Pause after (s) | Speed | Pause inside | Ledger |
|---|---|---|---|---|---|
| 1 | Because these futures involve randomness, a comparison can be noisy. | 0.3 | 1.0 | none | C50, C51 (“those” becomes “these”: the futures are on screen, and the voice has not named them) |
| 2 | Variance measures how much the comparison fluctuates between random runs. | 0.8 | 0.9 | none | C64, exact |
| 3 | Our pilot asked whether coordinating the random choices between the two copies could make the estimate more precise. | 0.4 | 1.0 | none | C52, exact |
| 4 | This is called coupling, an established idea. | 0.5 | 1.0 | none | C53, C54 (shortened; the citation is on screen, with “including in”) |
| 5 | Each copy still has to follow its own probabilities at every step. | 0.35 | 0.9 | none | C55 without “training” and without its last clause (weaker, not stronger; only the core of H14 is spoken) |
| 6 | We change how the choices are paired. | 2.4 | 0.9 | none | C56, exact |

**Beats.** Coordinates are P-local.

| Cue (kit, 0-based) | Line · anchor (t in s) | On screen, and what moves (duration) | Born from | Camera | Strings and numerals |
|---|---|---|---|---|---|
| `at(0)` | Line 1, "Because these **futures** involve randomness, a" (0.4 to 3.0) | Another future, slowly (one play of 1.5 s): the bright paths of steps 1 and 2 fall to ghosts; both heads go back to their places after the event; the bars go back to their step-1 widths; the pointers land in new places; new bright paths draw. The comparison (the plain segment from head to head) jumps to the new pair of ends. A copy of it flies right, turns flat, and lands as the first tick on a vertical strip at x = 4.3 (0.8 s, late in the same play). `one event` fades. | The fork; the comparison | | `copy A` and `copy B` move to the left ends of their bars. `the comparison` rides to the foot of the strip (centred x = 4.3, baseline y = -2.10) |
| `at_word(0, "comparison")` | "a **comparison** can be noisy." and the pause (3.0 to 4.7) | Three more futures at 0.45 s each. Each leaves a ghost (only if its path is new) and a tick at another height (or adds 10% to a tick that is already there). | | | |
| `at(1)` | Line 2, "**Variance** measures how much the comparison" (4.7 to 7.1) | From here to `line_end(1)` the other 36 futures run as one clock-driven stream (`world.jitter`, seed 11), spread evenly over that time (about 8 a second). The ghosts fill in a faint tree of futures. Ticks pile up round a centre line. On "Variance" a soft band grows from the centre line outward to cover the middle of the pile (1.0 s). | The ticks | | `variance` (44, serif, `INK_HI`) left of the strip, written on its word |
| `at_word(1, "fluctuates")` | "**fluctuates** between random runs." (7.1 to 9.2) | The newest tick jumps from place to place; it jumps, it does not glide. About three in ten land outside the band (the seeded futures as they fall): the band is a typical spread, not the range of all values. In the fork the comparison jumps long, short, long, in step with it. | | | |
| `line_end(1)` | The pause and line 3, "Our pilot asked **whether**" (9.2 to 11.3) | (0 to 0.6 s) The stream ends on the future of P06, lit again, with no tick of its own; the band breathes. (0.4 to 1.2 s) The fork and the strip dim to 45%, and `the comparison` and its segment fade. In the same play time goes back one step: the two dim heads slide back along their paths to their places after the event (x = -3.9), their bright paths fading to ghosts behind them, and the bars go back with them to their step-1 widths (copy A 0.492, 0.156, 0.352; copy B 0.316, 0.100, 0.585). This play ends at least 0.8 s before "coordinating". Then the bars brighten, and on each bar its own pointer jumps, each on its own, 5 times a second (`world.jitter`, seed 12), until "coordinating". | | | |
| `at_word(2, "coordinating")` | "**coordinating** the random choices between the two copies could make the" (11.3 to 14.8) | The pointers' jitter stops. The two pointers slide to one new place between them, which is neither copy's old place, and join into one white hairline through both bars (0.8 s). From there it keeps jumping, 4 times a second (`world.jitter`, seed 12), across the next rows; the hairline jitter stops on "own" (line 5), where the seed-17 landings take over. Under it each bar lights the segment that it lands in: often the same in both, sometimes not. | The two pointers | | |
| `at_word(2, "estimate")` | "the **estimate** more **precise**." and the pause (14.8 to 16.4) | The strip returns to 100%, and its centre line brightens: the estimate is the centre. On "precise" a shimmer runs along the centre line from left to right (0.8 s). The band's edges neither move nor shimmer. It is a question. | The band | | |
| `at(3)` | Line 4, "This is called **coupling**," (16.4 to 17.9) | The word writes right of the bars, on its word (0.8 s). | The link | | `coupling` (44, serif, `INK_HI`) |
| `at_word(3, "established")` | "an **established** idea." and the pause (17.9 to 19.4) | The citation fades in (0.6 s). | | | Citation (18): `including in "work on reducing noise in counterfactual estimates" (arXiv 2111.06888)` |
| `at(4)` | Line 5, "Each copy still has to follow its" (19.4 to 21.2) | The outline of bar A flashes blue, then the outline of bar B flashes violet (0.6 s each). | | | |
| `at_word(4, "own")` | "its **own** probabilities at every **step**." and the pause (21.2 to 23.5) | Until "step": each landing of the hairline leaves a small dot above the chosen segment of bar A and under the chosen segment of bar B: 30 stratified landings (each index once, in seed-17 order; 3.12), about 18 a second, so that each pile grows in step with the width of its own segment and ends exactly at 15, 4, 11 above bar A and 9, 3, 18 under bar B. After its last landing the hairline rests there until line 6. On "step" both bars change to their step-2 widths (0.6 s), and in the same play the two dim heads glide on along their own step-1 paths to (-2.4, 1.03) and (-2.4, 0.12): time moves on one step. No place flashes. The piles clear, and the citation fades. | The hairline | | |
| `at(5)` | Line 6, "We change how the choices are **paired**." and the silence (23.5 to 27.2) | (0 to 0.4 s) The ticks dim to a third of their level, and a ghost copy of the band's two edges stays at their present half-height, at 30%: they are runs with no coordination. The hairline becomes a link whose two ends can part. Then two forms, with fading after-images: straight (the same number; 0.4 to 1.3 s), crossed (a mirrored number; from 1.3 s, near "paired", to 2.3 s), and straight again (2.3 to 2.9 s). The bars do not change. A new set of 30 stratified landings runs across the three blocks, ten in each (by index, 3.12): the piles grow in step with each bar's own step-2 widths whatever the form, and end exactly at 14, 8, 8 and 10, 4, 16. On the strip the live band answers each form by its computed amount: a hair narrower, about the same, a hair narrower again. The centre line does not move. (2.9 to 3.3 s) The link settles at 0.46 of the bar length, and on each bar the segment that it lands in lights: segment 1 of bar A, segment 3 of bar B. In the last 0.8 s the ghost edges fade to 0. Nothing brightens. | The hairline; the band | | |

**Closing pose.** P07.

**Numerals shown.** None, except the arXiv number inside the citation. **Words on screen, most at one time:** 8
(the first frame).

**Honesty.**
- The tag is on for the whole scene. The futures illustrate the post's definition of variance (C64). The pilot
  did not sample runs (X29), and nothing on screen says that it did: the futures belong to the toy of 3.7.
- The band is the spread of the comparison round a fixed centre. It is not the gap between the two copies
  (pilot facts 2.12).
- "Asked whether ... could" stays a question in line 3 (H12): the band does not change there, and the shimmer
  runs along the centre line, not inward from the edges, so it does not preview a narrowing.
- The drawn effect is modest and computed: for the straight pairing the toy's variance is 8.6% lower, so the
  band is 4.4% narrower. Crossed: 2.3% more, about the same. The largest drawn effect is a hair, under both
  results of the post, with no number. Two forms only, one a hair better and one about the same, so the picture
  does not say that most ways of pairing make the comparison noisier (X36). The build guard of section 3.7 stops
  the scene otherwise. The toy was chosen so that the effect is modest; the tag says that it is a drawing.
- A bar changes only when a new step begins or when time goes back. It never changes when the pairing changes.
  When the bars go back to their step-1 widths (line 3), the heads go back with them and the play ends before
  "coordinating", so it reads as time going back, not as an effect of coordinating (pilot facts, must-not 2). No
  copy's choice is written over by the other's (brief rule 2.6): the two pointers meet at a new place, not at
  either copy's place. The piles prove that each copy keeps its own probabilities: under both forms of line 6
  they end exactly at each bar's own counts, because each form's block of landings maps the grid onto itself.
- The ghosts and the ticks are drawn once for each distinct path or height, so repeats do not stack into a bright
  tree. The band is a typical spread: about three ticks in ten fall outside it.
- In line 6 the ticks dim with the ghost edges: they are runs with no coordination, so only the live band, which
  is computed for the pairing on screen, answers the pairing. In the last 0.8 s the ghost edges fade, and nothing
  brightens between them and the band, so P07 carries no "coordinated against uncoordinated" pair toward the
  result (pilot facts, must-not 1; X24).
- Coordinated is not equal: the hairline visibly lands in different segments, and the final link at 0.46 lies
  in segment 1 of bar A and in segment 3 of bar B, as the bright future does; both segments light.
- On "step" the dim heads glide on along their own paths and no place flashes, so no step-1 pair is shown as the
  outcome of the straight landings.
- Both forms keep each copy's own probabilities. They are examples of ways to pair. They are not a list of the
  pilot's six baselines; neither has a name, neither is called the best, and S08 does not reuse them.
- The futures are never longer than two steps. The centre line does not move; the voice does not say so (X35).
- "Including in" is not spoken, so it is written before the citation, in the citation's style (H13). The citation
  is on screen from "established" to "step".
- C55 is spoken without "training" and without "given what has happened in both runs so far": a weaker rule,
  not a stronger one. "Training" would also pull the tiny learner toward the post-training of the first half.

**Building blocks.** Probe `repo-prob` P2 (two bars, two pointers, one shared hairline; without its counter
"26 of 31" and without its title) and P7 (faint runs, one bright); seeded draws (3.12); stratified landings for
the piles
(by index, each k once, so that each pile ends exactly at its count; 3.7, 3.12); piles and ticks as
`DotCloud`s; `world.Strip` with the band from `world.TOY`; `T` and `enter` for the two words; `hud_cite` with
its lead-in; `world.jitter` for the stream of futures and the jumps. The link has two forms; its after-images are
copies at falling opacity.

**Risk: medium to high.** Six lines and the most ideas of any scene. The thin rim is about 3.6 px at 1080p; that
is honest. Do not make it larger; make the ghost brighter. **Fallback, in this order:** no ghost and no change of
the band at all (mechanism only); the futures of line 2 baked as one faint picture.

---

### S08 The condition (about 26 s)

**Purpose.** Let the toy go, count the 1,440, name what was compared, and draw the line before any result.

**Opening pose.** P07.

**Lines to speak.**

| # | Words to speak | Pause after (s) | Speed | Pause inside | Ledger |
|---|---|---|---|---|---|
| 1 | We checked 1,440 toy configurations with one- or two-step continuations. | 0.6 | 1.0 | none | C57, C58, exact |
| 2 | We compared six baseline pairing methods with an oracle that could find the best allowed pairing in the tiny setup. | 0.5 | 1.0 | none | C59, C60, exact |
| 3 | The condition for advancing to the planned longer-horizon test: at least a 20% reduction in variance against the best baseline, in at least one configuration from our chosen target family. | 1.2 | 0.9 | 0.5 after `test:`; 0.4 after `baseline,` | C61, C62, C63 (“was” becomes a colon; one comma added) |

**Beats.** Coordinates are P-local.

| Cue (kit, 0-based) | Line · anchor (t in s) | On screen, and what moves (duration) | Born from | Camera | Strings and numerals |
|---|---|---|---|---|---|
| `at(0, lead=0.4)` | Line 1, "We **checked** **1,440**" (0.0 to 2.6) | The tag stays on. `copy A`, `copy B`, `variance` and `coupling` leave first (0.3 s). The rest of the S07 picture (fork, tree, start dot, bars, piles, strip; not the boundary and not the dim strip of the question above it) is baked at that moment into one `RasterLayer`, which fades in place (0.6 s, opacity only: it neither shrinks nor moves), scheduled backwards so that it is gone as "1,440" starts. Then for 0.3 s nothing new appears. Then a seed of neutral light lights at the field's own centre, (1.2, -0.2), not where the toy was, and blooms the field: three units slowly, then a dozen, then all the others, each to its place in the disc (about 1.5 s, ending as the word ends). The seed fades as the units land. The units are `GREY_2`, never `INK`. The numeral lands whole as the last unit lands. No count runs. | The field is born from its own seed at its own centre: a lone arrival (rule 11 exception); the toy is not its source | | `1,440` (44, serif, `INK_HI`): right edge x = -1.5, baseline y = 0.6, whole |
| `at_word(0, "toy")` | "toy **configurations**" (2.6 to 4.1) | The units take their slow breathing. All have one grey. | | | `toy configurations` (24, `GREY_1`): right edge x = -1.5, baseline y = 0.05 |
| `at_word(0, "one-")` | "with **one-** or **two-step** continuations." and the pause (4.1 to 6.5) | The disc does not part. Under the field the two step glyphs of 3.6 draw, one on each side of the label: on "one-" a ring and one step with a glowing head, left of the label; on "two-step" a ring and two steps, right of it (0.8 s each). In the pause the two glyphs and `one- or two-step` fade. | The label (a lone arrival: the glyphs belong to no part of the field) | | `one- or two-step` (24, `GREY_1`): centred x = 1.2, baseline y = -2.8 |
| `at(1)` | Line 2, "We compared **six** baseline pairing methods with an" (6.5 to 9.1) | Six grey pairing glyphs come out of the field's centre on arcs to a row at the left (1.4 s, `lag_ratio` 0.15): y = -0.9, x = -5.9, -5.1, -4.3, -3.5, -2.7, -1.9. They are identical: their links are soft and have no readable form, and only a faint shimmer, each in its own phase, tells them apart. None is ever highlighted. | The field | | `six baselines` (24, `GREY_1`): left edge x = -6.2, baseline y = -0.45 |
| `at_word(1, "oracle")` | "an **oracle** that could find the" (9.1 to 10.4) | A seventh glyph, `INK_HI` and a little larger, comes out of the field's centre and lands under the row at (-3.9, -1.75) (0.8 s). Its link is soft too. | The field | | `oracle` (24, `INK`): left edge x = -3.35, baseline y = -1.85 |
| `at_word(1, "best")` | "the **best** allowed pairing in the" (10.4 to 11.7) | The oracle's soft link flickers quickly (12 a second, 1.1 s) and then holds still. It settles on no readable form. Its two bars do not change. | | | |
| `at_word(1, "tiny")` | "tiny **setup**." and the pause (11.7 to 12.8) | A soft band of light sweeps the field from left to right (1.1 s): the same comparison in each configuration. The six glyphs stay unlit and identical. | | | |
| `at(2)` | Line 3, "The **condition** for advancing to the planned" (12.8 to 15.2) | `1,440` and `toy configurations` fade. The field parks: it shrinks and moves to the upper right (1.4 s). In the same play a white line draws upward at x = 4.4, from y = -2.7 to -0.6 (1.0 s), at 85%, with no glow. | | | Tag off as the line draws: from here the line, its number and the scale are the post's |
| `at_word(2, "longer-horizon")` | "**longer-horizon** test: at least a" (15.2 to 17.6) | From the top end of the line a longer fork draws itself, dotted and faint (16%; 1.6 s, steady): a short stem and two branches that rise to the right to about x = 6.2 and fade out. No step can be counted on it. No part of it is at the height of a track. | The line | | |
| `at_word(2, "20%")` | "**20%**" (17.6 to 18.7) | The label of the line lands whole on "20%" (0.6 s), as one token whose sign carries the "at least" that the voice has just said. | The line | | `≥20%` (44, serif, `INK_HI`): left edge x = 4.6, baseline y = -1.5 |
| `at_word(2, "reduction")` | "**reduction** in variance against the best" (18.7 to 21.0) | The scale, in one play of 1.2 s: all six glyphs, unlit and identical, slide down together to x = -5.6 and merge into the zero tick (0.8 s): the zero is the best of the six in each configuration, and no single glyph becomes it. `six baselines` fades. In the same play track 1 draws from the zero tick to the line (1.2 s, linear). | The six baseline glyphs | | `variance reduction` (24, `GREY_1`) above the left end of the track; it lands late, when the glyphs are gone |
| `at_word(2, "baseline")` | "**baseline**," (21.0 to 22.5) | The zero tick flashes. The oracle's glyph flies to the zero tick and becomes the white marker, with its small glow (radius 0.12) (0.8 s). `oracle` fades. | The oracle's glyph | | `best baseline` (24, `GREY_1`) at the foot of the zero tick (left edge x = -5.45, baseline y = -2.72), under the place of track 2; it lands late, when the glyph has left |
| `at_word(2, "one")` | "in at least **one** configuration from our chosen target" (22.5 to 25.2) | In the middle of the parked field a faint, hollow grey halo hops from unit to unit, 5 a second, only among the units of the target family (`world.jitter`, seed 29, until "family"): any one of them would be enough. No unit lights. | The field | | |
| `at_word(2, "family")` | "**family**." and the pause (25.2 to 26.5) | A soft white outline closes round the target family (1.2 s): an irregular hull round a seeded set of units near the middle (3.6), not a circle. The halo fades. No unit stays lit; the marker rests at zero. | The field | | `target family` (24, `INK`) left of the field |

**Closing pose.** P08.

**Numerals shown.** `1,440` (from its word to "The condition"); `20%` (from its word on, written `≥20%`). Each
lands whole. **Words on screen, most at one time:** 7.

**Honesty** (against `design/pilot-facts.md`, 2.7 to 2.11).
- The S07 picture dissolves in place, under the tag, before anything else appears. After a beat of 0.3 s the
  field blooms from a seed at its own centre, not from the place of the toy, and its units are cool grey, not
  the white of the pile dots. So the toy and its drawn effect never become pilot data, and the field does not
  say that the pilot sampled runs (X29, X37). Each unit is one small problem: not a run, not a model, not an
  experiment on an AI.
- There are exactly 1,440 units, all one neutral grey. None gets a colour or a value for a result (X47). The
  field is cool grey, even and still, and it stands in the pilot's territory: it must not look like the pool.
- No counter: the units do the counting, and the numeral lands whole (brief rule 2.2).
- The disc has no parts with a meaning and never parts. The step glyphs stand beside the label, under the
  field, and belong to no part of it. The family is an irregular outline of no stated or drawn size, and no
  share of the project record is drawn (X31; pilot facts 2.7). So the places of u1 and u2 say nothing about one
  or two steps or about a share of the field.
- The six glyphs are identical, with soft links of no readable form: no name, no kind, no ranking, and none of
  the forms of S07. A soft link stands for any joint table, including drawing the two choices separately. No
  glyph is ever highlighted, and all six merge together into the zero tick: the zero is the best of the six in
  each configuration, no single glyph becomes it, and the picture says nothing about which baseline wins where
  (pilot facts 2.9; must-not 22).
- The oracle is a search: its soft link flickers and holds still with no readable form, so the picture says
  nothing about which kind of pairing is best (pilot facts 2.10). It is never "our method".
- The scale starts at the zero tick, and the zero is the best baseline: the oracle is measured against the best
  ordinary pairing, not against no pairing (X24). `best baseline` sits at the foot of the zero tick, under the
  tracks, so it never reads as the name of a track. There is no tick number; the only numeral on the scale is
  the post's 20%, written `≥20%` so that "at least" stays with it. The line is a level to reach, not a
  ceiling, and it has no glow.
- The line is drawn before any result. The voice does not say when it was set (X28).
- The longer test leaves the top end of the line like a door. It is not on the scale, so it cannot read as
  "more than 20%". It has no step count, no light and no result, and it is drawn at 16% (pilot facts 2.15;
  must-not 31).
- "Any one would be enough" is only supposed: the halo is grey and hollow, and no unit is lit before the result
  names it (pilot facts 2.13; must-not 29).
- The tag is on until the condition line draws, so the field's drawing, the step glyphs, the six glyphs and the
  oracle's flicker sit under it (the count 1,440 is the post's). From the condition line on it is off: the line,
  its number and the scale are the post's.

**Building blocks.** A bake and an in-place fade for line 1 (no shrink: `DotCloud.scale` keeps the dot radii,
and text must not shrink below 24); `sunflower_points`, `cloud.appear` in a
`sampling_rhythm` and `cloud.to(centers=, radius=)` for the field (kit example; frame `fx/14_sample_1440`);
`born_from` and `hand_over` for the glyphs, the zero tick and the marker; probe `repo-prob` P6 for the scale,
**without** its tick numbers, its brace "1.5 points short", its red line and its coloured bars; `hull_blob` for
the outline.

**Risk: medium to high.** It is the fullest scene. **Fallback:** no glyph row: on "six baseline pairing methods"
six identical grey ticks appear at the place of the zero tick, unlit, and merge into one zero tick on
"reduction"; on "an oracle" the white marker appears there. The step glyphs can go; `one- or two-step` stays.

---

### S09 About 18.5% (about 29 s)

**Purpose.** The high point: one marker runs toward a line that was drawn before, stops short, and the picture
holds. Then the second result, and what both numbers are.

**Opening pose.** P08.

**Lines to speak.**

| # | Words to speak | Pause after (s) | Speed | Pause inside | Ledger |
|---|---|---|---|---|---|
| 1 | What did the oracle find? | 0.9 | 1.0 | none | framing question; its presupposition rests on C60 (“could find”) and C65 |
| 2 | The strongest result in that family was about 18.5%. | 2.4 | 0.88 | none | C65, exact |
| 3 | With full suppression of the event’s learning contribution, the strongest result was about 14.1%. | 0.7 | 1.0 | 0.45 after `contribution,` | C66, exact |
| 4 | These were best cases, not averages, and they came from an oracle whose own computation was not a practical shortcut. | 0.8 | 1.0 | 0.35 after `averages,` | C67, C68, exact |
| 5 | The pilot did not meet the condition for advancing. | 1.8 | 0.9 | none | C69 (“for that extension” becomes “for advancing”, the words of C61 in S08 line 3; no new claim, and the planned longer-horizon test keeps one spoken name) |

*Say* (stress markup only; the words do not change): line 4 is sent as `These were best cases, [not](+2) averages, and they came from an oracle whose own computation was not a practical shortcut.`.

**Beats.** Coordinates are P-local.

| Cue (kit, 0-based) | Line · anchor (t in s) | On screen, and what moves (duration) | Born from | Camera | Strings and numerals |
|---|---|---|---|---|---|
| `at(0)` | Line 1 and line 2 up to the numeral, "**What** did the oracle find? The **strongest** result in that family was about" (0.4 to 5.5) | The marker leaves the zero tick and runs right along track 1 at one steady speed, with a 0.6 s ease-out at the end, so that it stops at x = 3.65 as the word "18.5%" starts (the run rule of 3.6: about 5.1 s, about 1.94 units a second). It leaves a white trail; its glow stays small (radius 0.12). On "strongest" u1 lights (`INK_HI`, glow 0.2), and a thin thread (`INK` at 35%) flashes from it to the moving head (0.6 s): it rises from u1 to y = 1.4, runs left at that height, above `target family`, and comes down onto the head from directly above. Nothing else in the field changes while the marker runs. | The marker of P08 | P (no lean) | `target family` stays |
| `at_word(1, "18.5%")` | "**18.5%**." (5.5 to 6.9) | The marker has stopped at x = 3.65 as the word starts. The line is at x = 4.4. The numeral lands whole during the word (0.6 s), with `about` from its first frame. | The head | | `about` (32, serif, `INK`) and `18.5%` (64, serif, `INK_HI`) above the head, on one row. Numeral: 18.5% |
| `line_end(1)` | The silence (6.9 to 9.3) | Nothing moves but the breath of the head's small glow, in opacity only. Between the head and the line there is only the bare hairline of track 1: nothing fills it and nothing lights it. No word. | | | |
| `at(2)` | Line 3, "With **full** suppression of the event’s learning contribution, the" (9.3 to 13.1) | `target family` fades; the family outline stays. In the field a second curve draws round the lower part of the family (3.6; window 0 to 0.7 s). In parallel, track 2 draws from the zero tick to the line (window 0 to 0.8 s, linear), so it is complete before run 2 starts (the guard of 3.6). From about "event's" the second marker leaves the zero tick and runs along track 2 by the rule of 3.6, at the same speed as the first, clock-driven, so that it stops at x = 1.45 as "14.1%" starts (about 3.9 s). | The field; the zero tick | | `full suppression` (24, `INK`): right edge x = 3.1, baseline y = 0.45, beside the second curve |
| `at_word(2, "strongest")` | "the **strongest** result was about" (13.1 to 14.7) | u2 lights (`INK_HI`, glow 0.2), and a thin thread (`INK` at 35%) flashes from it to the moving second head (0.6 s), by the same rule as u1's: it rises from u2 to y = 0.95, above `full suppression`, runs left, and comes down onto the second head from directly above, under trail 1. From "result" `full suppression` hands over to its place on the 14.1% row: the copy beside the curve fades as the copy on the row fades in (0.6 s), finished before "14.1%". No text moves. | u2; the label | | `full suppression` (24, `INK`): right edge x = -1.2, baseline y = -2.0 |
| `at_word(2, "14.1%")` | "**14.1%**." and the pause (14.7 to 16.9) | The second marker has stopped at x = 1.45 as the word starts. The numeral lands whole during the word (0.6 s), with `about` from its first frame. The row now reads `full suppression  about 14.1%`. No ring and no symbol stands beside it. | The second head | | `about` (32, serif, `INK`) and `14.1%` (44, serif, `INK_HI`) above the second head, on one row. Numeral: 14.1% |
| `at(3)` | Line 4, "These were **best** cases, not" (16.9 to 18.5) | On "best" the two lit units pulse once (0.8 s), and `strongest` lands left of the field, between their heights. In the same 0.6 s two thin threads (`INK` at 35%, as in lines 2 and 3; stroke `W_LINE`) draw from the right end of `strongest` to u1 and to u2 and stop at the edge of each unit's glow (3.10): the label names the two lit units, not the field or the outline. | The label | | `strongest` (24, `INK`): right edge x = 3.1, baseline y = 0.9, with its two threads |
| `at_word(3, "averages")` | "**averages**, and they came from an" (18.5 to 20.5) | The whole field dims to 40%, every unit inside and outside the family alike (1.0 s): no value is shown, which is not the same as zero, and no part of the field is set apart. The two lit units stay lit; the family outline and the second curve keep their levels. In the same 1.0 s the two threads of `strongest` settle from 35% to 15%, where they stay to the end of S09. | | | |
| `at_word(3, "oracle")` | "**oracle** whose own computation was not a" (20.5 to 22.7) | Above trail 1 the web is wiped in from left to right (2.0 s; 3.8): two soft trees of possible futures of the two copies, blue and violet, whose branches and ends cannot be counted, and a woven sheet of white threads between the ends of one and the ends of the other, all at one even brightness. | Trail 1 | | Tag on, from the web's first frame |
| `at_word(3, "practical")` | "**practical** shortcut." and the pause (22.7 to 24.7) | One run lights on top (0.8 s): one path in each tree, and two bright links that bow above the sheet, first between the two chosen points of the arcs, then between the two chosen ends: the pairing is made step by step. The sheet keeps one even brightness behind it; no thread is picked out. Then the web folds into trail 1: the layer stretches to height 0.02 onto y = -1.3 while it fades (0.8 s). | | | Tag off at the end of the fold |
| `at(4)` | Line 5, "The pilot did not meet the **condition** for" (24.7 to 27.0) | On "condition" the condition line rises from 85% to 100% along its whole length at once (0.6 s); nothing travels along it, and nothing lights the gap. The two heads rest where they stopped. | | | |
| `at_word(4, "advancing")` | "**advancing**." and the tail (27.0 to 29.0) | At the top end of the line the faint fork glimmers once (16% to 24% to 16%, 0.8 s). It is the fork that S08 drew on "longer-horizon", the test that "advancing" leads to. It stays unlit. It is not removed and not crossed out. | | | |

**Closing pose.** P09.

**Numerals shown.** `20%` (as `≥20%`), `18.5%`, `14.1%`. Each lands whole on its own word and stays. No number
runs. **Words on screen, most at one time:** 12 (from "best"; the tag does not count). At the high point: 9.

**Honesty** (brief rules 2, 4 and 6; `design/pilot-facts.md`, 3 and 5).
- True size on a scale from zero: the line is 10.0 units from the zero tick; the trails are 9.25 and 7.05 long;
  the gap is 0.75 (about 101 px at 1080p). There is no camera lean and no cut axis. The gap is dark track:
  nothing fills it and nothing lights it, the head's glow has radius 0.12 and the line has no glow, so the
  dark run between them is at least 80 px (about 85 px by estimate; the build check of 3.6 compares it with a
  control render of the bare track) and the gap looks as wide as it is. A lit or
  soft band there would read as an error bar that reaches 20%, or as "nearly passed" (X41; must-not 27).
- The run has one steady speed and a 0.6 s ease-out: no creep toward the line, nothing that says "it nearly made
  it" (X41, O4). Both runs have the same speed, so neither looks easier or of another kind. "What did the oracle
  find?" uses the verb of C60 and asks what a calculation found, not how far an agent travelled. The 2.4 s hold
  on the gap stays, as the brief asks.
- `variance reduction` and `best baseline` are on screen whenever a result numeral is on screen. So 18.5% cannot
  read as "coupled against not coupled". `best baseline` sits at the foot of the zero tick, under both tracks,
  so no text row reads "best baseline ... about 14.1%" as if 14.1% were the baseline's result (must-not 1).
- No word of judgement is said or shown (X41, X42). The gap is a length and a silence. The result is white, not
  red and not gold.
- No running percentage. `about` is on screen with each numeral from its first frame, at serif 32 in both rows,
  so that the hedge is not lost beside the 64 (H01). `≥20%` holds "at least" in its sign, 0.5 from each
  result's row, so it cannot attach to a result (H05).
- With the sound off each number names its case. The 18.5% unit is the upper lit unit and its track is the upper
  track; the 14.1% unit is the lower lit unit, inside the lower part of the family, and its track is the lower.
  Each unit's thread flashes to its own moving head on "strongest", in the sentence that names its result.
  `full suppression` stands beside the second curve while the voice says it, then stays on the 14.1% row to the
  end, so 14.1% never reads as a second try, a correction or a later value (pilot facts 3.3; X40). `target
  family` stays until line 3, and the family outline to the end, so "in that family" stays on screen while
  14.1% is shown (pilot facts, open point 3).
- Nothing in the family twinkles while the marker runs, so the run is not drawn as the work of the whole family.
  u1 lights only on "strongest", the word that names its result, and a thread ties it to the run (pilot facts
  2.13).
- Two trails, two units, two tracks. The second starts from zero; the first never slides down to it (pilot
  facts 3.3). The second unit is inside a part of the family, so its trail cannot be the longer one. The other
  part gets no name: the post names no other kind of suppression (X30). The second curve is an irregular part
  with no fraction, not a half (X31). Row 1 carries no word of a case: the post's sentence for 18.5% names only
  "that family", and the outline shows it.
- The second number arrives on its own sentence. It does not arrive on "not averages".
- Both lit units are inside the family outline, which stays on screen. On "averages" the whole field dims
  evenly, inside and outside the family, so no part of it reads as better or worse (must-not 3 and 21; X39).
  `strongest` names the two lit units as the strongest of their groups, the post's own word, not as typical
  ones. It stands outside the field, where `target family` stood until line 3, so two thin threads tie it to
  the two lit units: without them it would read as a new name for the outline ("the strongest family") or for
  the field, which the post does not claim, and which the record contradicts (record note of X39; must-not 3).
  There is no bar for an average.
- The web is every possible future of both copies against one run: an exhaustive calculation, not a method and
  not cheap. Its fans and its sheet cannot be counted, so it states no number of choices, steps or pairs
  (pilot facts 2.14, must-not 34; X26), and the tag is on while it is on screen. The sheet keeps one brightness
  and the run is paired step by step, so the web does not show finished runs matched by their end results
  (must-not 18). No count, no cost meter. Nothing of the question's cost floor moves; it is not even in the
  frame.
- On "condition" the line brightens all at once; nothing travels up it into the fork, so the verdict does not
  show an attempt to pass, and nothing lights the gap. Line 5 says "the condition for advancing", the words of
  S08 line 3 (C61), so the longer test keeps one spoken name, and the fork that S08 drew on "longer-horizon"
  glimmers on "advancing".
- The tag is off for the scale, the line, the three numerals and their lengths, which are the post's. It is on
  while the web, a drawing, is on screen.

**Building blocks.** `world.Ruler`; `Runner` with a `Trail`, driven by a `ValueTracker` on the run of 3.6 (run 2
started by the clock at its computed time); per-point opacity in the field cloud for u1, u2 and the dimming;
`hull_blob` for the second curve; `FadeIn(scale=0.92)` for the numerals (no `LiveNumber` that counts); the web's
sheet as one `VMobject` before the bake, `bake` and `set_clip` for the web, with the bright run live on top, and
a stretch of the layer for the fold.

**Risk: medium.** The scene is simple; its timing is not: both stops come from word times, and run 2's start
comes from run 1's speed. **Fallback:** the web can be one soft wedge for each copy and the sheet, with no
bright run (never the faint tree of S07: the toy is not the pilot).

---

### S10 Boundaries (about 22 s)

**Purpose.** Say what the result tells and what it does not, by going back up to a question that the pilot never
touched.

**Opening pose.** P09.

**Lines to speak.**

| # | Words to speak | Pause after (s) | Speed | Pause inside | Ledger |
|---|---|---|---|---|---|
| 1 | That tells us something about the particular approach we tested. It does not answer the larger data-change question. | 0.9 | 1.0 | 0.6 after `tested.` | C70, C71, exact |
| 2 | The pilot did not choose batches of training data to remove or replace, test safety improvements in an LLM, or demonstrate a saving in total computation. | 0.6 | 1.0 | 0.3 after `replace,`; 0.45 after `LLM,` | C72, C73, C74, exact |
| 3 | I want to keep those boundaries visible as the project develops. | 1.3 | 1.0 | none | C75, exact |

**Beats.** Coordinates are P-local until the pan, then canvas.

| Cue (kit, 0-based) | Line · anchor (t in s) | On screen, and what moves (duration) | Born from | Camera | Strings and numerals |
|---|---|---|---|---|---|
| `at(0)` | Line 1, "That tells us something about the particular **approach** we tested." and the pause (0.4 to 4.4) | First all text of the pilot fades, with the two threads of `strongest` (0.5 s): no numeral stays without its `about`, and no thread is baked. Then one play of 2.0 s: the pilot's picture (field with its family outline and second curve, scale, trails, line, faint fork), baked as one layer by its bounding box (P-local x -5.6 to 6.2, y -2.75 to 2.05), scales down to the emblem's box at (0, -0.6) and fades, while the drawn emblem (3.5, Object 6), with its family mark round both white dots, fades in with `late(0.6)`; in the same play the boundary lets go of the frame edges, comes down, and closes round the emblem (a `Transform` between the two `smooth_closed` shapes of Object 6, anchor for anchor). | The pilot's picture; the boundary | | All strings of S09 leave. The tag stays off |
| `at_word(0, "It")` | "It does not **answer** the larger data-change question." and the pause (4.4 to 7.9) | We pan up. The emblem, inside its closed boundary, travels in a straight line on the canvas from (0, -5.8) to (-5.4, -1.6), with the camera's `GLIDE`, and settles at the lower left of the question. The question comes down into view, live at 35%, in REST exactly as S05 left it. The cost floor and the lane fade back in to 35% as they enter the frame, and light 0 is red again. | | P to W, 3.0 s from `at_word(0, "It")` (`clock_move`) | The tag stays off during the pan, so the emblem lands untagged |
| `at(1)` | Line 2, "The pilot did not choose **batches** of training data to remove or replace," (7.9 to 11.8) | The lamp (3.8): its centre opens over the upper left of the pool (0.6 s) and glides across it (2.0 s). It draws nothing: under it the points and the dashed outlines rise from 35% to 100%. It is not born from the boundary. No group lifts. No outline fills. | None: it opens in place | | Tag on, with the lamp's first frame |
| `at_word(1, "test")` | "test safety improvements in an **LLM**," (11.8 to 14.7) | The lamp glides over the model and on over the two rows of lights (2.2 s). The needles tremble as before. The red lights stay red. The shade stays down. | | | |
| `at_word(1, "demonstrate")` | "demonstrate a saving in total **computation**." and the pause (14.7 to 17.8) | The lamp glides down to the right end of the floor (its centre stays at x ≤ 5.2 and y ≥ -2.3) and along it to the left, to x = -1.0 (2.6 s): outlined segments and an empty lane. Nothing changes. It stops far from the emblem. | | | |
| `at(2)` | Line 3, "I want to keep those **boundaries** visible as the project **develops**." and the tail (17.8 to 22.2) | The lamp fades where it stands, over the floor (0.6 s). Then, from "boundaries", the boundary curve brightens to 100% by itself (1.2 s). On "develops" its glow breathes once. The emblem inside it is still. | The boundary | | `the pilot` (24, `GREY_1`): left edge x = -4.38, baseline y = -1.7, right of the curve |

**Closing pose.** P10.

**Numerals shown.** `20%` (as `≥20%`), `18.5%`, `14.1%` for the first half second. None after it.
**Words on screen, most at one time:** 12 (the first half second), then 2.

**Honesty.** This is brief rule 4 as a picture. The voice says the three things that the pilot did not do, in
the post's words (H17). Each is an object that the lamp visits and that does not change. Nothing is struck
through, and there is no list. The lamp opens over the question and fades over it: no light comes out of the
pilot and travels over the pool, the model, the test or the cost, so the picture does not say that the pilot
sheds light on the main question (brief rule 4; X48). The lamp adds no light of its own: it only raises what is
already there to its full level. The boundary then brightens by itself. The tag comes back with the lamp, after
the emblem has landed, so the tag refers to the world and not to the post's results in the emblem. Nothing of the
pilot is drawn on the pool, the model, the test or the cost floor (pilot facts, must-not 32). The emblem rests
above the rows of the cost floor and the empty lane, away from the places where `computation` and `a shortcut`
stood, and its label is not in the pool's label slot: it is not the head of the shortcut, a share of the cost or
a label of the examples (X21, X49). "Something" is not explained: the post does not say what it is (X43). No
label `coupling` is put on "the particular approach we tested": the post does not name the approach there (H15,
X36). The emblem is the whole pilot, small, with its scale from zero: the last frames do not show a cut view of
the gap. It has no numerals. It keeps the family mark: a faint outline round its inner dots encloses both white
dots, so the last frame, which holds for all of S11, still says "in that family" and not "the two best of the
whole field" (H02, H06; pilot facts, open point 3 and must-not 3; X39). The faint stub of the longer test is still in it, at the top end of the condition
tick: the post does not say what happens to that test later (X44).

**Building blocks.** One 2.0 s play for the hand-over: the baked layer with
`.animate.scale_to_fit_width(1.36).move_to(...).set_opacity(0)` and, in parallel,
`FadeIn(emblem, rate_func=late(0.6))` (the kit's `hand_over` would interpolate unrelated points between a raster
and strokes); `Transform` of the boundary between two `smooth_closed` shapes with 16 anchors in the order of
Object 6; the camera pan (`clock_move`); the lamp as one updater that sets opacities from its centre L(t) (3.8),
with per-point opacity in the clouds. There is no second copy of the question.

**Risk: medium.** Two things move while the camera pans: the emblem and the incoming question (live at 35%).
**Fallback:** the emblem forms after the pan: the pilot's picture fades as we pan up, and the emblem with its
boundary draws itself at the lower left on "It does not answer".

---

### S11 I would rather know (about 19 s)

**Purpose.** A real ending: come back to the open decision, show what an honest answer looks like, and stop on
the author's best sentence.

**Opening pose.** P10.

**Lines to speak.**

| # | Words to speak | Pause after (s) | Speed | Pause inside | Ledger |
|---|---|---|---|---|---|
| 1 | What evidence would make a recommendation trustworthy? | 0.9 | 1.0 | none | C79, as a sentence of its own |
| 2 | A method should also be able to tell us when the evidence is too weak to choose between two changes. | 0.45 | 1.0 | none | C80 (“two options” becomes “two changes”) |
| 3 | I would rather know that than get a confident ranking with no reliable basis. | 5.0 | 0.88 | none | C81, exact |

*Say* (stress markup only; the words do not change): line 3 is sent as `I would rather know [that](+2) than get a confident ranking with no reliable basis.`.

**Beats.**

| Cue (kit, 0-based) | Line · anchor (t in s) | On screen, and what moves (duration) | Born from | Camera | Strings and numerals |
|---|---|---|---|---|---|
| `at(0)` | Line 1, "What evidence would make a **recommendation**" (0.4 to 2.6) | The question returns from 35% to 100%, from left to right: pool, model, lights, floor (2.0 s, `lag_ratio` 0.3). The shade stays down over the outer row. On "recommendation" the dashed outlines of gA and gD brighten to 100% and take a faint gold tint inside, at 12% (0.6 s): two changes, still only supposed. | | | |
| `at_word(0, "trustworthy")` | "**trustworthy**?" and the pause (2.6 to 4.2) | From each of the two a thin dashed gold beam runs through the model's core (above the core disc, under the needles) and ends at the model's right rim, at the height of its range: gA's at (1.64, 0.66), gD's at (1.58, 0.16) (1.2 s each, 0.3 s apart). No beam reaches either row of lights. Between the model and the inner row a dashed horizontal hairline draws at y = -0.2, from x = 1.75 to 3.0 (window 0.9 to 1.5 s). | The two groups | | |
| `at(1)` | Line 2, "A **method** should also be able to tell us when the evidence is too" (4.2 to 7.3) | Each range is born from its beam. Its first gold dot leaves the end of its beam and slides right along the beam's row to the range's own left end (window 0 to 0.3 s; gA x = 1.64 to 1.8, gD x = 1.58 to 2.1). From there the dotted gold range grows to the right along its own row (window 0.3 to 1.9 s): a row of gold dots with a short dotted cap at each end; no fill and no centre line. gA's runs from x = 1.8 to 2.75, gD's from 2.1 to 3.05: they overlap over most of their length. As the ranges grow, the beams settle to 30% (1.0 s). Then both ranges breathe: their centres move left and right by 0.06, slowly. | The beams | | |
| `at_word(1, "weak")` | "**weak** to choose between two **changes**." and the pause (7.3 to 9.4) | On "weak" the stretch where the two ranges overlap brightens, a soft column over both rows (0.6 s). On "changes" the two gold groups pulse in turn (0.5 s each). | | | |
| `at(2)` | Line 3, "I would **rather** **know** that than get a confident" (9.4 to 11.9) | From "rather" the ranges' breathing slows to stillness (1.5 s, ease-out). On "know" the overlap column brightens once and settles (0.8 s). Nothing new starts after it: by the estimates the row is without a new motion for about 0.6 s before "ranking". The two ranges stand clear and overlapping: this is the picture that the line prefers. | | | |
| `at_word(2, "ranking")` | "**ranking**" (11.9 to 12.6) | Each range snaps into one crisp white vertical tick at its centre (0.5 s; an allowed snap). One is right of the other: a sharp order. | The ranges | | |
| `at_word(2, "no")` | "with **no** reliable **basis**." (12.6 to 13.8) | The dashed hairline under the ticks fades (0.6 s). From "reliable" the ticks swap places three times, 0.3 s apart: the order flips, flips back, flips again (allowed snaps). | | | |
| `line_end(2)` | The silence (13.8 to 18.8) | The ticks melt back into the two dotted ranges, and the hairline returns (0.8 s). The ranges breathe very slowly. Five lights are still red. The held-back row is still shaded. The lane is still empty. The pilot sits inside its bright boundary. From 0.8 s in: the sign-off writes above the model, two lines (1.4 s). Hold. In the last 0.8 s everything fades to the background. | | | Sign-off (32, serif, `INK`): `Notes from an ongoing` / `research project` |

**Closing pose.** P11, then the fade.

**Numerals shown.** None. **Words on screen, most at one time:** 8.

**Honesty.** The two ranges are an illustration under the tag: the post shows no way to draw uncertainty (X14)
and has no method that does this ("should": H40). The two data changes stay dashed, with only a faint tint:
nothing is retrained and nothing is chosen (C79 is an open question; X08, X10). The beams are dashed. The ranges
are dotted gold intervals with dotted caps, no fill and no centre line: hollow, because they are only supposed
(rule 8 of 1.2), and they share nothing with the band of variance in the pilot, so the picture builds no bridge
from the pilot's coupling to a data-change recommendation (X21, O8). The ranges are supposed evidence for the
choice. They are drawn between the model and the row that we look at, and the held-back row stays shaded and
untouched (C24, as in S03): no beam crosses it and no label names it here. Neither change is marked as
better. The sharp ranking is shown only to be taken back; the flip is a
drawing of "no reliable basis", not a result (X15). There is no axis number. The sign-off is the first half of
the post's subtitle (C02); it carries "ongoing" in place of a spoken status line. The red lights stay red and
the lane stays empty: nothing was fixed and nothing was saved.

**Building blocks.** Each range is one shape with a width tracker (a row of dots with two dotted caps), so that
it can fold into a tick and back; dashed strokes with `flash_along`; `T`, `lines`, `enter` and
`backstroke` for the sign-off. Probe `repo-prob` P10 gives only the idea of two overlapping ranges, not its
vertical shape, its title or its labels.

**Risk: low to medium.** The fold from a range to a tick and back is new. **Fallback:** the ticks fade in over
the ranges, flip, and fade out; the ranges never change.

---

## 6. The three best moments

**1. The shade lifts (S03, about 15.1 to 17.0 s, in silence).**
The camera has pushed in until the test fills the height of the frame. On the left the model is a blue core of
needles. Right of it the inner row of lights runs nearly from the bottom of the frame to the top, all pale, in a
soft halo: the test that we stared at is fixed. Just outside it a dark shade hides the outer row. The voice has
finished "…the test we have been staring at" and is silent. The shade lifts, the twelve held-back lights are
swept in half a second, and four of them are red: the same four as before. Nobody speaks. The joke of the line
and the point of "held back" land in one picture.

**2. The run and the gap (S09, about 0.4 to 9.3 s).**
The frame is nearly empty: a faint track across the lower half, a grey tick at its left end with the words
`best baseline` at its foot, a white line at its right end with `≥20%` beside it, and, from the line's top end,
a dotted fork that is not lit. On "What did the oracle find?" a white point leaves the tick and runs at one
steady speed. On "strongest" one unit of the family lights and a thread touches the moving point. No number runs
beside it. The point eases to a stop as the word "18.5%" begins, and `about 18.5%` stands above it: the only
size-64 type of the video. Between the point and the line is a dark space, 0.75 units wide, and nothing fills
it. For 2.4 s nothing moves but the breath of the point's small glow. No stamp, no red, no word like "close".
The zero is still in the frame, and the camera has not moved.

**3. The ranking that flips, and the last frame (S11, about 11.9 to 18.8 s).**
Between the model and the inner row of lights two dotted gold ranges lie on their own rows and overlap. On "a
confident ranking" each snaps into one sharp white tick, one right of the other. On "no reliable basis" the
hairline under them fades, and the ticks jump: the order flips, flips back, flips again. Then they melt into the
two overlapping ranges, which stay. The voice stops. In the same frame five test lights are still red, the
held-back row is still shaded, the shortcut lane is still empty, the two changes are still dashed, and at the
lower left the whole pilot sits small inside its bright boundary, its trail still short of its line and its two
white dots inside the faint outline of the family. `Notes from an ongoing research project` writes itself above
the model.

---

## 7. Word count and running time

### 7.1 Word count

**597 words** in 41 lines and 11 scenes, by the narration builder's count: one word for each piece
between spaces, so `1,440`, `20%`, `18.5%` and `14.1%` are one word each and `one- or two-step` is three.
**612 words as read aloud.** The binding limit is the hard maximum of 620 words as read aloud (ruling 1 of
`design/DECISIONS-round3.md`); good lines were not cut to reach 600.

| Scene | Lines | Words (text) | Words (as read) | Estimated length (s) |
|---|---|---|---|---|
| S01 | 4 | 57 | 58 | 22.9 |
| S02 | 5 | 79 | 79 | 28.7 |
| S03 | 3 | 47 | 47 | 16.7 |
| S04 | 2 | 39 | 39 | 14.6 |
| S05 | 4 | 62 | 62 | 22.9 |
| S06 | 3 | 36 | 36 | 17.5 |
| S07 | 6 | 64 | 64 | 27.2 |
| S08 | 3 | 60 | 67 | 26.5 |
| S09 | 5 | 57 | 63 | 29.1 |
| S10 | 3 | 55 | 56 | 22.3 |
| S11 | 3 | 41 | 41 | 18.8 |
| All | 41 | 597 | 612 | 247.1 |

- **As the voice reads them** (`1,440` = 5 words, `18.5%` and `14.1%` = 4 each, `20%` = 2, each hyphenated word
  = its parts): 612 words. It is 615 if "per cent" counts as two words, and 617 if `LLM` also counts as three
  letters. Every count is under the hard maximum of 620.
- Against round 2: S05 line 4 is gone (-5); S04 line 1 has "to improve future answers" and no "the" (+3); S03
  line 2 has "while we choose" for "from choosing" (+1); S09 line 5 has "for advancing" for "for that
  extension" (-1); S02 line 2 has the post's "repeating the process for many changes could become expensive"
  (+2); S07 line 1 has "these" for "those" (0). Net 0 by the builder's count (597) and as read (612).
- 44 sentences, from 5 to 30 words, mean 13.6. 2 sentences have 6 words or fewer and 8 have 20 or more. 3
  questions, each a wh-question with 0.9 s or more after it. "I" 5 times, "we" 19 times.
- 29 of the 44 sentences are continuous pieces of the post, character for character (26 of the 41 lines). The
  others are the post's sentences with a glossary name put in, a word or a clause left out, a word changed or
  a mark of punctuation added; the column "Ledger" says which. One sentence is a framing question (S09 line 1).
- Numerals spoken: `1,440`; `one- or two-step`; `six`; `20%`; `about 18.5%`; `about 14.1%`. Each once. No other
  numeral. The small counting words ("one event", "One copy", "the two copies", "at least one", "One
  question", "two changes") are the post's (ledger 2.3).
- Claims of the post that are not spoken: C01 to C03, C17 to C21, C26 to C31, C35 to C38, C41, C47 to C49, C76 to
  C78, C82 to C86. Of these, C01 and C02 are shown as text; C36, C38, C47 and C48 are carried by a picture; the
  lead-in "including in" of C54 is written before the citation.
- The seven required hedges are all spoken, verbatim: H03 and H04 (S09 line 4), H16 (S10 line 1), H17 (S10 line
  2), H18 (S05 line 1), H19 (S05 line 3), H20 (S05 line 4). H08 is kept in its sense: "did not meet the
  condition for advancing".

### 7.2 Estimated running time

About **4 min 7 s** (247.1 s, `narration.py --check-only`), from the narration builder's own text analysis:
13.4 phonemes a second; a slower line is counted at 60% of its change of speed, as the builder's estimate does;
an inner pause is 0.3 s unless the line sets it; each scene starts its first word at 0.40 s. The "t" values of
section 5 come from the same analysis and differ from these lengths by 0.3 s at most. No audio was made.

- 18 different pause lengths after lines (0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.3, 1.5,
  1.8, 2.3, 2.4, 3.0, 5.0 s). No length comes more than 2 times in a row. The two jokes (S02 line 4, S03 line 1)
  get 0.8 s after them, so the timing carries the dryness that the voice cannot.
- Seven silences of 1.4 s or more, and each holds a reveal: the shade (S03), the twin (S04), the two steps (S06),
  the two pairings (S07), the gap (S09), the line and the longer test (S09), the last picture (S11).
- Every sentence of 24 words or more has a pause set inside it (S01 line 2, S02 line 3, S08 line 3, S10 line 2).
  S06 line 1, the densest sentence (three new terms), has a 0.3 s pause after "learner," and speed 0.9.
- 13 lines are slowed: S01 line 4 (0.9); S02 line 4 (0.9); S03 line 3 (0.9); S05 line 1 (0.9); S05 line 4 (0.9);
  S06 line 1 (0.9); S07 line 2 (0.9); S07 line 5 (0.9); S07 line 6 (0.9); S08 line 3 (0.9); S09 line 2 (0.88);
  S09 line 5 (0.9); S11 line 3 (0.88). Each is at 0.9 or below: the voice probe found a clear slow-down (6% to
  8%) only at 0.88 to 0.90, and 0.95 only 2% to 4% slower (`research/tts-probe.md`, 2.4). S09 line 3 is at 1.0,
  so that it does not take weight from the reveal at 0.88, and its inner pause after "contribution," is 0.45 s,
  so that the qualifier is heard as a frame before the number.
- The run of S09 lasts about 5.1 s from "What" to "18.5%" (the brief asks for 5 to 8 s). The second run has the
  same speed and lasts about 3.9 s.

### 7.3 What was read, what was run, what is not tested

- **Read in full for round 3:** `design/DECISIONS-round3.md`; the four round-2 reviews (`design/_results.json`,
  key `last_verification`, 82 issues); `design/BRIEF.md`; the post; `design/claims-ledger.md`;
  `design/pilot-facts.md`; this file and `design/script.json` as round 2 left them. **Read in part:**
  `narration.py` (the check-only report); `kit/theme.py` and `kit/scene.py` (the tag size); the round-2 scratch
  tools (narration source, word-time estimator, layout check), copied into `design/scratch-r3/` and changed
  there.
- **Run in round 3, all in `design/scratch-r3/`, each with exit 0:**
  - `toy_r3.py`: the toy of 3.7 by exact sums over every pair of futures, for no coordination, straight and
    crossed. Variance 0.0943, 0.0863 (-8.6%), 0.0966 (+2.3%); equal means; the guard of 3.7 passes; 49 tick
    heights, all on the axis; 0.30 of the probability outside the band; the bars and the piles of line 5; the
    line-6 schedule by index, exact in 2,000 of 2,000 landing orders; the final link at 0.46 in segment 1 of bar
    A and segment 3 of bar B; the four S06 pointer places in their stated segments.
  - `s11_lint.py`: the S11 ranges, hairline and beam ends against the lights and the model. With the review's
    numbers the nearest gap was 0.086 (gD's cap to red light 10's glow); with both ranges 0.1 further left every
    gap to a light is 0.18 or more and to the model's rim 0.15. Both beams pass within 0.4 of the model's
    centre, so they go through its core.
  - `gen_r3.py`: writes `script.json` from the one narration source and replaces the "Lines to speak" tables of
    this file; it stops if a line is not found exactly once.
  - `times.py` (word times by the builder's own text analysis, for every "t" of section 5) and `stats_r3.py`
    (the counts of 7.1 and 7.2).
  - `verify_r3.py`: the JSON lines equal the tables character for character, with every pause, speed and `say`;
    every opening pose is the previous closing pose; all 101 cues resolve and run forward; one play is under
    1 s, the allowed snap on "ranking".
  - `layout_r3.py`, with estimated text widths, for 19 frames and poses (S01 at TEST-IN, S03 at STARE, P02, P06,
    P07, P08, P09, P10, P11, S06 lines 1 and 2, S07 lines 1 to 3, S08 lines 1 to 3, S09 at the high point, at
    the cross-fade, at the hand-over and with the web): no problems; at most 12 words; no text outside the safe
    area or in the band of the tag; no two texts closer than 0.1; no text closer than 0.1 to the main art. The
    lights span screen y -2.87 to 3.37 at TEST-IN (with light 0's red glow) and -2.81 to 3.31 at STARE; the shade
    spans y -2.10 to 3.38 at W and -2.88 to 3.37 at STARE.
  - `narration.py --check-only` on the new `script.json` against this file, `--out` in `design/scratch-r3/`: all
    41 lines appear word for word and in order, each scene under its own heading, and nothing of the reviewed
    narration is left unspoken; 597 words; estimated length 4:07.1; the three stress marks raise "which", "not"
    and "that" (Kokoro's own /ðæt/ becomes /ðˈæt/); eight notes for the ear ("used", "post-training",
    "estimate", `1,440`, the three percentages and "project").
- **Closing pass of round 3.** Read: the seven medium issues of the two confirmation reviews; the kit's
  `_words_in` and `tex()` (`kit/type.py`: a `T()` string is counted with `split()`, an `SVGMobject` from `tex()`
  as one word) and its `SERIF` stack (the comment there says that symbols the text face lacks, such as `≥`, come
  from New Computer Modern Math). Run, in `design/scratch-r3/`, each with exit 0:
  - `closing_checks.py` (output in `closing_checks.txt`): no problems. With `≥20%` counted by `split()`, P09
    and the web frame have 12 words. The two threads of `strongest` run from (3.22, 0.96) to (4.555, 1.210) and
    (4.503, 0.646); no text is closer than 0.12 to them; the thread to u1 stays at least 0.03 above the highest
    that the lower part can reach for any phase of seed 43. Re-placing `strongest` right of the units (left x
    4.95, baseline 0.85) would lie over the family outline for all 1,296 phase pairs tried. The emblem's family
    curve clears both white dots by at least 0.010 (factor 0.58) or 0.021 (factor 0.65) for every phase. The
    dark run is about 85 px by estimate. S02's return of the world runs from 25.2 to 27.8 s, 0.83 s before the
    scene ends; S09's track 2 is complete at 10.12 s and run 2 starts at 10.76 s; S11 line 3 is without a new
    motion for about 0.6 s before "ranking".
  - `verify_r3.py` (with the project's virtual environment; output in `verify_closing.txt`): the JSON lines
    equal the tables, the pose chain holds, all 101 cues resolve; one play under 1 s, the allowed snap on
    "ranking". `script.json` is byte for byte the same as before this pass: no narration line changed.
- **Not done and not tested:** no audio, no render, no layout lint on real text, no viewer. Every time in this
  file is an estimate. Text widths are estimates (0.145 units a character for Inter 24, 0.19 for serif 32, 0.26
  for serif 44, 0.38 for serif 64). No inner pause is checked against real audio; the pause after “safer” (S03)
  is the likeliest to stop the build. The seeds of 3.12 are rules, not tested seeds; in particular, the seeds 37
  and 43 of the family and its lower part, the dark-run check of 3.6, the emblem's clearance check, the kit's
  `word_count` of 3.11(f) and the sign `≥` from the fallback face of the serif stack (and its gap to the 2) are
  checks for the build. I did not open the font files. The colour-vision figures of 3.2 are from round 1 and
  were not rerun.

---

## 8. Decisions for the user

Each has a default that is built into this document. Change one only if your taste or your ear says so.

1. **The last words.** The voice ends on "I would rather know that than get a confident ranking with no reliable
   basis." The post's own last line ("I’m working out how to turn this version of the question into a useful
   experiment.") is not spoken; the sign-off on screen carries "ongoing". If you want the post's last line as the
   last words, it costs 15 words, and something of equal length must go.
2. **Length (decided, ruling 1).** The binding limit is the hard maximum of 620 words as read aloud. The script
   has 597 words by the builder's count and 612 as read (615 if "per cent" counts as two words, 617 if `LLM`
   also counts as three letters), so it is under 620 on every count. Good lines were not cut to reach 600. Any
   later change should be word-neutral or shorter: 3 words of room remain on the strictest count.
3. **"Tests held back while we choose the change" (ruling 5).** The post says "examples held back from the
   process of choosing the change". The voice says "tests", because "examples" already names the pool, and
   "while we choose" because "held back from choosing" can be heard as "stopped from choosing"; it is also active.
   It makes no new claim: tests kept out of the choice. The post's exact phrase ("...then examples held back
   from the process of choosing the change.") costs 3 words more and is still under 620 (615 as read).
4. **The condition sentence.** The post's "was" is a colon here, so that the voice can take a breath after
   "test". If you want the post's sentence word for word, the breath goes.
5. **The first paper.** "Data Attribution in Adaptive Learning" (arXiv 2604.04892) is not shown, because the
   sentence that it belongs to ("An early change can alter later choices, which can alter the information the
   learner receives.") is not spoken. To restore both costs 15 words.
6. **A drawn effect of coupling.** S07 shows a small computed effect for two pairings: 8.6% less variance in
   the toy for the straight pairing (a hair narrower band), and 2.3% more for the crossed pairing (about the
   same). The slanted pairing is gone (ruling 11): with three forms, two of three widened the band, which could
   read as "most pairings make it noisier". The stricter choice is no effect at all: the first fallback of S07
   does that.
7. **The run.** By default the marker runs at one steady speed with a 0.6 s ease-out, and the camera does not
   move. A camera lean (P to GAP, zoom 1.08, at least 2.4 s long) or a slower approach is an option only if the
   sound-off check of 3.11 still answers "no" to "Did it nearly work?" with it in place.
8. **By ear, in the first build:** `1,440` as "one thousand four hundred forty" (default) or "fourteen forty";
   "AI’s"; "post-training"; whether the three questions sound like questions; the 2.4 s of silence on the gap;
   the stresses on "which" (S01 line 4), "not" (S09 line 4) and "that" (S11 line 3); the 0.8 s after each of the
   two jokes. S03 line 1: if the build stops because Kokoro made no pause after “safer”, or if the line is heard
   as the order "Make the model safer!", use "Saying “make the model safer” leaves rather a lot of room to
   congratulate ourselves." (1 word more, no new claim). S06 line 1: if the ear still trips on "one event
   changes" with the comma, the pause and speed 0.9, use "We built a tiny learner to study how its later
   behaviour changes when we suppress the learning contribution from one event." (2 words more, no new claim;
   the beats then land on "tiny", "behaviour", "suppress" and "event").
9. **`≥20%`.** In S08 and S09 the condition's number is written `≥20%`, one token whose sign carries the
   post's "at least" (H05). It frees one word on screen in P09, so that `full suppression` can stay on the 14.1%
   row and `strongest` can name the two lit units within 12 words (picture honesty, round 2; ruling 8). The
   other way to free the words, letting `at least` leave at the end of S08, would leave `20%` without its hedge.
   The kit counts `T("≥ 20%")` as 2 words: it counts with `split()`, and a thin, narrow or no-break space splits
   too. So the token is built without a space, `T("≥20%")`, and the kit counts 1. The sign comes from New
   Computer Modern Math, the fallback face of the kit's serif stack, and its gap to the 2 is that face's side
   bearing. If the first P09 shows the gap as too tight, or the sign is missing, set the token with the verified
   LaTeX route, `tex(r"\geq 20\%")`: TeX puts its own space after a relation sign, and the kit counts an
   `SVGMobject` as one word. If `strongest` fails the sound-off question of 3.11(e), it goes, and the uniform dim
   on "averages" carries "best cases, not averages" alone; P09 then has 11 words.
10. **The slug** "How much can one learning moment change an AI?" is not used: beside a tiny learner it can
    suggest an AI model.
11. **Copy B in violet.** Gold now means only a data change, so copy B can no longer read as "the model after a
    data change". The cost: blue and violet are closer for viewers with red-green colour blindness (3.2), so the
    two copies never differ by hue alone. If you prefer gold for copy B, the risk that picture honesty raised
    comes back.
12. **"For advancing" (ruling 2).** S09 line 5 is "The pilot did not meet the condition for advancing." It
    repeats the words of S08 line 3 (C61), so it adds no claim, and the planned longer-horizon test keeps one
    spoken name; the fork glimmers on "advancing". The shorter "The pilot did not meet the condition." is not
    offered: it loses H08 (a condition for advancing, not a pass or fail of the pilot), and fidelity does not
    accept it. The post's own "for that extension" is 1 word more and still under the limit, if you prefer the
    post's words to the one-name rule.
13. **The question before the result.** The fidelity review asked to delete "How far did the oracle get?" (it
    turns a calculation into an agent that travels toward the line) and allowed "What did the oracle find?" if a
    question must stay. One must stay: the builder starts every scene's first word at 0.40 s, so with no question
    the run from zero to "18.5%" would last about 2.8 s, against the brief's 5 to 8 s. With the new question it
    lasts about 5.1 s.
14. **Review points not applied in round 1, or applied in another way.**
    - Voice: "groups of examples" in S10 line 2. Fidelity asked that S10 lines 1 to 3 stay verbatim, and
      "batches of training data" is the brief's own wording of rule 4. The inner pause after "tested." (S10 line
      1) is 0.6 s, as the voice review asked. (The 7-word verdict of S09 line 5 is superseded by ruling 2.)
    - Voice: "longer" for "longer-horizon" in S08 line 3. It needs the fidelity owner's consent (H07).
    - Voice: the new order of S06 line 1 is kept for the ear (point 8).
    - Fidelity, optional: the sentence C36 before S05 line 2 (12 words). It is not spoken; the Ledger column and
      the twin's dropped segment carry it. ("To improve future answers" in S04 line 1 and gB's dial with nine red
      were applied in round 3.)
    - Fidelity: no ring beside 14.1%, so the hollow ring and the matching ring round u2 (picture honesty) are
      both gone. (Round 3 keeps `full suppression` on the 14.1% row to the end of S09, by writing `≥20%`:
      point 9.)
    - Fidelity: the layout it suggested for `at least` (one row over the top of the line, the field raised by
      0.65). The raised field would cross the boundary at y = 2.2. Round 3 writes `≥20%` at the place where
      `at least` was, 0.5 from each result's row.
    - Picture honesty: six joint-table squares for the baselines, and an oracle that settles on a table that is
      not the diagonal. Fidelity's soft, identical glyphs are used: a settled table would show which kind of
      pairing is best, a fact of the record only.
    - Picture honesty: the seven ringed points lift as if to be removed while light 10 flickers. Fidelity asked
      that no point lifts. (Round 3 also takes away their rings.)
    - Picture honesty: a straight pan to P with no SPECK station, and a thread from u1 that stays for the whole
      run. Fidelity's two-leg move and its 0.6 s flash on "strongest" solve the same problems; a thread that
      stayed would cross `18.5%` as it lands.
    - Picture honesty: dashed edges and a dotted centre line on the S11 ranges, and a glow on gA and gD. Fidelity
      asked for no centre line and no edge lines, and a faint tint. (Round 3 draws each range as a row of gold
      dots with dotted caps and no fill: point 15.)
    - Craft: the emblem at (-5.3, -1.85) with `the pilot` under it. Fidelity forbids any part of the curve
      between y = -2.95 and -2.1. Fidelity's place is used; the floor starts at x = -3.0 (not -3.4), so that
      `the pilot` lies wholly left of it.
    - Craft: TEST-IN at zoom 1.5 and STARE at zoom 1.25. At those zooms the lowest lights sit in the band under
      y = -2.9 that belongs to the tag. (Round 3: TEST-IN at zoom 1.36 and STARE at 1.14, which also keep light
      0's red glow and the shade out of that band.)
    - Craft: the strip at factor 2.2. Picture honesty's factor 2.0 is used (same aim, higher lens).
    - Craft: `tiny learner` above and left of the point. With my width estimate it came within 0.05 of copy A's
      event ring, so it sits under and left of the point (baseline -0.95 since round 3), clear of the halo, and
      the thread to bar A runs right and then down, so that nothing crosses it.
    - Craft: the lamp's pass ends at the floor's left end. It ends at x = -1.0, far from the emblem.
    - Fidelity: "including in" before the citation is applied. If brief rule 5 ("exactly") forbids any added word
      on that line, remove it and record the limit (point 15 asks the orchestrator).
15. **Review points of round 2 not applied as written, or applied another way** (all others are applied; the
    rulings of `design/DECISIONS-round3.md` bind).
    - Fidelity, S11 geometry: applied, with both ranges and the hairline 0.1 further left than the review's
      numbers (gA 1.8 to 2.75, gD 2.1 to 3.05, hairline 1.75 to 3.0; the overlap stays 0.65). With the review's
      numbers gD's right cap came 0.086 from red light 10's glow and the hairline 0.112 from light 6's glow;
      shifted, every gap to a light is 0.18 or more and the gap to the model's rim is 0.15.
    - Craft, gD's beam near light 10: no longer needed. The beams now end at the model's rim, far from every light.
    - Picture honesty, S05: the pulse along the empty lane on "cheaply" is not used. Fidelity's fix (nothing moves
      on the lane) is stricter and wins. The other half (the dotted continuation starts as the pieces land) is
      applied.
    - Picture honesty, S11 ranges as dotted outlines with no fill: applied another way. An outline would put edge
      lines along each range, which a round-1 fidelity fix forbids (so that the ranges share nothing with the
      band of S07). Each range is a row of gold dots with dotted caps and no fill: hollow, with no edge lines.
    - Picture honesty, tracks continued past the line (optional): not applied. `≥20%` sits right of the line,
      0.5 from both result rows; hairlines past the line would run into it, and no other place keeps it off both
      rows.
    - Picture honesty, `full suppression` to the end and `strongest`: applied by writing `≥20%` (point 9). The
      review left this trade to the orchestrator; please confirm it.
    - Picture honesty, the rewind of S07: "the heads slide back to their step-1 places" is read as the places
      where the step-1 choice is made (after the event, x = -3.9), which agree with the bars' step-1 widths; on
      "step" the heads move on with the bars, and no place flashes (craft).
    - Craft, merged rows: not needed. The new clock-driven helpers (ruling 13) carry every motion that crosses a
      cue, so the rows stay as they were.
    - Craft, emblem: applied, with the two white dots mirrored to agree with ruling 8 (the review's coordinates
      were for the old field, where the 14.1% unit was the upper one).
    - Craft, the S07 picture baked and shrunk to a point: baked, but not shrunk. It fades in place (fidelity;
      ruling 9).
    - Craft, retrain MB with 11 red: replaced by fidelity's 9 red (no change), the same nine as before.
    - Craft, the second curve "above the centre line": drawn round the lower part, under a seeded wavy line,
      with no fraction (fidelity; ruling 8).
    - Fidelity, optional, the tag in S10 from the lamp's first frame: applied.
    - Fidelity, optional, "repeating the process for many changes" in S02 line 2: applied (+2 words).
    - Fidelity, low, "tests held back": no change was required; ruling 5 gives the voice's form.
    - Addition for craft, S04: the restored "to improve future answers" would have left the picture idle; on
      "future" only the five red lights pulse, which adds no meaning and points at no example.
    - **Open for the orchestrator** (fidelity, low): confirm that brief rule 5 allows the lead-in "including in"
      and showing one of the two papers. If either is refused, show `"work on reducing noise in counterfactual
      estimates" (arXiv 2111.06888)` without the lead-in, or show both citations exactly as the brief gives them.
16. **Closing pass of round 3: where the two confirmation reviews differed, or where a fix was applied another
    way** (all seven medium issues are applied).
    - `strongest`: the threads (option A of both reviews) are used. Re-placing the label right of the two units
      (option B) is not: it would lie over the right part of the field and, for every phase of seed 37 that I
      tried, over the family outline (section 7.3), so it would name a part of the field again.
    - The threads of `strongest`: one review asked that they rest at 15% to the end of S09, the other that they
      flash and fade. They rest at 15%, because the sound-off check is made on a still of P09 (3.11(e)), and a
      flash would leave that still with an untied label. They fade with the text at the start of S10, so the
      emblem does not carry them.
    - The emblem's family mark: the review named the stroke `W_THIN`, which is not a name of the kit; `W_HAIR`
      (1.0, the kit's thinnest) is used. The mark is the family's curve itself at the disc's scale, not a hull of
      the 60 dots, so that it encloses both white dots for every phase; a clearance check and a wider factor
      (0.65) cover the tightest phases.
    - The LaTeX route for the token is `tex(r"\geq 20\%")`, not `tex(r"\geq\,20\%")`: TeX already puts a thick
      space after a relation sign, so `\,` would make the gap wider than a word space.
    - The dark-run check compares P09 with a control render in which the heads, their glows, both trails and the
      line are hidden. The other review's "row 0.04 above the track, against the background" is not used: the
      vignette darkens the background toward the edges, so near the line its pixels are not `BG`, and a row off
      the track measures the head's round glow where it is narrower.
    - S11 line 2, the birth of the ranges: the review fixed only the point where each range starts. A first dot that slides
      from the end of the beam to that point (0.3 s) is added, so that gD's range, whose left end is 0.52 from
      its beam's end, is still born from its beam (rule 11 of 1.2). It adds no meaning.
    - S11 line 3: the flash on "confident" is deleted, not moved to "than"; the slowing breath and the column on
      "know" keep the row moving, and the row is then without a new motion for about 0.6 s before "ranking".
    - Not changed (below medium in the reviews): the row `full suppression  about 14.1%` could be read with the
      sound off as an amount of suppression; u2's thread crosses trail 1 on its way down to the second head.
