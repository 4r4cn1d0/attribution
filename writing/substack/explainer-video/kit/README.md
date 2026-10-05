# kit: the style kit of the explainer film

One package that every scene uses. It holds the look (colours, type, strokes, spacing), the light (glow, point
clouds, the background), the motion grammar, measured shapes, and the base class that locks a scene to the
narration and to the film clock.

```python
from kit import *          # Manim, the theme, type, fx, motion, shapes and the Narrated base class
```

A scene author needs this file and nothing else. The probes that the kit came from are not needed.

| File | What it holds |
|---|---|
| `theme.py` | every colour, stroke width, size, gap and timing constant. No other file holds a colour literal |
| `type.py` | fonts, baseline-true text, the live number, LaTeX without `dvisvgm`, the layout lint |
| `fx.py` | the camera, the film clock, the point cloud, glow, raster pictures, clip and blend, the background, fields and blobs |
| `motion.py` | rate functions, late landings, `timed`, hand-overs, the tapered stroke, the runner, ambient motion, the sampling rhythm |
| `shapes.py` | a quantity as a length (`LiveLength`), an angle (`Dial`) or an area (`Area`), driven by a tracker |
| `scene.py` | `Narrated`: timings, cues, the hold to the exact duration, the film clock, the camera, pinning, labels that follow, the HUD, the lint |
| `example_scene.py` | a 13-second scene that shows the patterns (section 2) |
| `demo_reel.py` | the whole kit in one 35-second shot: the visual standard of the film |
| `selftest.py` | 115 fast checks of the kit |

Toolchain: Manim Community 0.21.0 (Cairo), Python 3.11 in `tmp/explainer-venv`. The kit uses internals of this
Manim version. Keep the version pinned. All commands run from the project root.

**Not in the kit: the film's lasting objects.** The pool, the model, the safety test, the cost floor, the two copies
and the poses at the scene joins belong in `world.py` beside `kit/` (storyboard sections 3.5 to 4 and 3.9; one
builder writes it before the scenes). `world.py` builds them from the kit: `DotCloud` and `soft_field` (the pool),
`Stroke`, `glow_sprite` and `RadialGlow` (the model), `Dial` (the mini dials), `LiveLength` (the scale and the
results), `soft_band` (the variance band, the ranges, the gap), `Area`, `fly` (pulses and travellers),
`follow_label`, `keep_stroke`, and the rest ease that makes every pose one exact picture (section 3).

---

## 1. Running a scene

```
# the film: one process per scene, lossless files, cue frames, lint (the pipeline tool)
tmp/explainer-venv/bin/python writing/substack/explainer-video/render.py S03

# one scene by hand, draft size (854x480, 15 fps), with its own media directory
EXPLAINER_NO_AUDIO=1 tmp/explainer-venv/bin/manim render -ql --media_dir tmp/explainer-build-v2/media/draft/S03 \
    writing/substack/explainer-video/scenes/s03.py S03

# the same at 1920x1080, 30 fps:   -r 1920,1080 --fps 30   (in place of -ql)
# the kit's own checks, example and reel
tmp/explainer-venv/bin/python writing/substack/explainer-video/kit/selftest.py
tmp/explainer-venv/bin/manim render -ql --media_dir tmp/explainer-build-v2/foundation/kit/media/example \
    writing/substack/explainer-video/kit/example_scene.py Example
tmp/explainer-venv/bin/manim render -ql --media_dir tmp/explainer-build-v2/foundation/kit/media/draft \
    writing/substack/explainer-video/kit/demo_reel.py DemoReel
```

**How `kit` gets on `sys.path`** (each way was run through the `manim` command from the project root):

| Where the scene file is | What to do |
|---|---|
| directly in `explainer-video/` (for example `explainer.py`) | nothing. Manim puts the folder of the scene file on `sys.path` |
| rendered through `render.py` | nothing. It sets `PYTHONPATH` |
| in a sub-folder (`scenes/s03.py`), rendered on its own | put these two lines above `from kit import *` |

```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/
```

The `manim` command lists only the scene classes that are defined in the file it is given. A class that is only
imported into `explainer.py` is not listed (`render.py` handles this).

**Environment**

| Variable | Effect |
|---|---|
| `EXPLAINER_TIMINGS` | another timings file (default `BUILD/audio/timings.json`) |
| `EXPLAINER_NO_AUDIO=1` | do not add the scene's sound. The WAV need not exist |
| `EXPLAINER_LINT=1` | run the layout lint after every play (every wait and `at()` too) and at the end; print one `KIT-LINT` line for each issue when it appears |
| `EXPLAINER_LINT=2` | also draw the safe area and a box around each offending object (the boxes show the last check) |
| `EXPLAINER_LINT_JSON=file` | write the issues of the run to this file |
| `EXPLAINER_SNAP=2.5,7,cues` | save lossless PNG frames at these scene times; `cues` = `first.png`, `last.png` and `cueNN.png` (the frame at the end of line NN) |
| `EXPLAINER_SNAP_DIR=dir` | where the PNG files go (default `BUILD/snaps/<SceneKey>`) |
| `EXPLAINER_BUILD` | the build folder (default `tmp/explainer-build-v2`) |
| `EXPLAINER_CRF=12` | encode Manim's own scene file at this x264 quality (Manim fixes CRF 23). `render.py` does not need it |
| `EXPLAINER_QUALITY` | set by `render.py`. Then a scene must read the pipeline's timings file under its class name: a `timings_file` or another `key` stops it with a `TimingError` |
| `EXPLAINER_TIMINGS_USED=file` | the scene writes the timings file, its key, the digest of its entry (the rule of `render.py`'s `timings_digest`) and its film start |

Look at what you make: `EXPLAINER_SNAP` gives exact frames without ffmpeg. Open them.

---

## 2. Example

This is `kit/example_scene.py` (rendered and looked at; the lint finds no issue in it).

```python
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
```

What to copy from it:

- **Write `build()`, not `construct()`.** The class name is the scene key (`S03`).
- **Set the stage with `self.add` before the first cue.** No scene starts on an empty frame.
- **Tie each change to the voice**: `at(i)`, `at_word(i, "word")`, `play_until(t, ...)`, and `timed(anim, t0)` for a
  change that lands on its word inside a longer play. Do not count seconds by hand.
- **One source for a quantity**: the tracker drives the picture and the number.
- **A field is a soft cloud** (`soft_field`), with a little variation in shade and size, never a box of dots.
- **New things come from old things**: `born_from`, `hand_over`, `cloud.to`. A lone fade-in is the exception.
- **Labels keep their size**: `self.follow_label(label, anchor)` before a push-in.
- **End where the next scene starts.** After a push-in, pull back, unless the next scene starts from that framing.

---

## 3. The base class: `Narrated` (`scene.py`)

`Narrated` is a `MovingCameraScene` with the kit camera and the background. It reads the timings of its key, adds
the sound (unless `EXPLAINER_NO_AUDIO=1`), runs `build()`, and then holds the picture to exactly the duration.

**Lines are numbered from 0**, like `starts` and `sentences` in `timings.json`. Times are scene seconds. The `nth`
of a word counts from 1.

| Call | What it does |
|---|---|
| `self.at(i, lead=0.0)` | wait until line `i` starts (`lead` seconds earlier). It stops ONE FRAME before the cue: the first frame of a play shows its start state, so the next play's first change is on the cue |
| `self.at_word(i, "gate", nth=1, lead=0.0)` | wait until that word of line `i` starts (one frame early, as `at`). A phrase works too: `"held-back tests"`. `"1,440"`, `"20%"`, `"18.5%"` match as written |
| `self.at_time(t)` | wait until scene time `t` (one frame early, as `at`) |
| `self.play_until(t, *anims, min_time=0.3)` | play the animations so that they end exactly at `t`, for example `self.line_end(2)`. Less than `min_time` left is a `TimingError`; `min_time=0` for a deliberate snap |
| `self.left(t)` | seconds from now to `t`: the length of a play that ends at `t` (for `window()`) |
| `self.span(i)`, `self.line_start(i)`, `self.line_end(i)` | (start, end) of line `i`; `line_end` is when the voice stops, before the pause |
| `self.word_span(i, "word", nth=1)` | (start, end) of a word or phrase |
| `self.now` | the scene time in seconds |
| `self.scene_duration` | the length of the scene. **Not `self.duration`**: Manim overwrites that at every play, and it is 0 before the first one |
| `self.starts`, `self.sentences`, `self.key`, `self.fps`, `self.film_start` | the timings of the scene; `film_start` is where it starts in the film |
| `self.frame` | the camera frame (a mobject) |
| `self.push_in(target, zoom=1.6, run_time=3.0)` | animation: go to a point or mobject and magnify (at most 2) |
| `self.pull_back(run_time=3.0)` | animation: back to the framing the scene started with |
| `self.pin(mob)` / `self.unpin(mob)` | keep `mob` at its place and size on screen while the camera moves / give it back to the world (`pin_to_frame(mob, frame)` is the function behind it) |
| `self.follow_label(label, anchor, offset=None)` | a label that follows a world object (or point) and keeps its size and its gap on screen during a push-in (`follow_label(label, anchor, frame)` is the function) |
| `keep_stroke(mob, self.frame)` | keep the stroke widths of a world object constant on screen during a zoom (ordinary strokes and the kit's `Stroke`) |
| `self.hud_tag()` | the fixed tag "illustration", bottom right, Inter 24. Add it to every picture that a viewer could take for data |
| `self.hud_cite("... arXiv 2604.04892", row=0)` | a citation line, bottom left, Inter 18. `row=1` sits 0.4 above row 0, for a second citation at the same time |
| `self.lint("label")` | run the layout lint now (it runs by itself after every play with `EXPLAINER_LINT=1`) |

**It fails loudly.** `TimingError` names the scene, the line and the amount:

- `build()` ran past the scene duration: `S03: build() ran 6 frames (0.400 s) past the scene duration ...`
- a cue was missed by more than `tolerance` = 0.07 s (1 frame at 15 fps, 2 frames at 30 fps; the same in seconds
  at draft and at review): `S03: the start of line 4 is at 12.300 s but the scene is already at 12.700 s ...`.
  A cue that is late within the tolerance prints one `KIT-TIMING ... late by n frame(s)` line.
- `play_until` with less than 0.3 s left: `S03: play_until(14.000) has 2 frame(s) left at 13.900 s ...`
- a word is not in the line (the message lists the words that the line has), `nth` below 1, an empty word, a line
  that does not exist.
- under `render.py`, a scene that reads another timings file than the pipeline's (a `timings_file = ...` left in a
  scene of the film), or whose `key` is not its class name.

Shorten what comes before the cue. Do not catch the error.

**The film clock.** For every frame the scene sets the film time: `film_start` (the durations of the scenes before
this one in `timings.json`, in the order of `_meta.scenes`) plus the scene time. All idle motion reads it:
`cloud.drift()`, `ambient()`, and a runner that runs by itself (`runner.start()`). So no frame is lost at a play
boundary (Manim starts every play with `dt = 0`; the kit also gives your own `dt` updaters the right `dt`), draft
and review show the same picture at the same time, and a cloud that the next scene builds the same way continues
its motion. `film_time()` and `idle_gain()` give the clock to your own updaters.

**Joins are exact.** In the first and the last `rest_ease` = 0.4 s of a scene all idle motion eases to its rest
value (`idle_gain()` goes from 1 to 0), so the last frame of scene N and the first frame of scene N+1 are one
picture when both build the same objects in the same state (storyboard rule 6 of 1.2: "exact poses"). Set
`rest_ease = 0` on a scene class to turn it off.

**Animating a part** (`t.part["k"].animate.set_color(...)`, `VGroup(a, b).animate.shift(...)`) animates it in place.
Manim itself adds such a part to the scene and breaks its parents up (a text loses its words for the lint, a group
that holds a `LiveNumber` or a `Runner` stops their updaters, the z-order changes). The kit does not, except for an
animation that removes or replaces its object (`FadeOut(part)`, `ReplacementTransform(part, ...)`), which needs it.

A wait in a `Narrated` scene is never one frozen frame: every updater runs in it. `self.wait(t)` is allowed, but
`at()` and `play_until()` are better, because they follow the voice when the narration changes.

`silent_timings(path, key, [(start, "words"), ...], duration)` writes a stand-in timings file and a silent WAV.
It is for trying things out and for tests, never for a scene of the film (`render.py` refuses it).

---

## 4. The theme (`theme.py`)

**Colour: one meaning for each hue, for the whole film** (the storyboard's map, section 3.2). Each hue has three
shades: `X_LO` (deep: fills, dimmed states), `X` (base), `X_HI` (light: cores, highlights). The design panel may
change the hex values; the names stay.

| Name | Meaning |
|---|---|
| `MODEL` (blue) | the model and the run that learns normally |
| `DATA` (starlight, `#E8E2D0`) | post-training examples |
| `FOCUS` (gold) | the thing that we change. Focus itself is made with brightness: brighten the thing, dim the rest |
| `FAIL` (red) | a failed safety test, nothing else |
| `COPY_B` (violet, `#A98BFF`) | copy B of the tiny learner (its event contribution suppressed), nothing else. Never told from `MODEL` by hue alone |
| `PASS` (green) | not used by the storyboard: a passing test is a quiet pale light (`INK` at 60%). FAIL and PASS nearly merge for a viewer with deuteranopia: never let them differ by colour alone |
| `INK`, `INK_LO`, `INK_HI` | text, and what we read or measure (results, scales, the band, the boundary) |
| `MUTED` | the HUD (tag, citation) |
| `GREY_1` ... `GREY_5` | structure, from light to dark: rulers, ticks, quiet lines |
| `SLATE` | solid bodies that sit on the background |
| `BG`, `BG_EDGE`, `BACKSTROKE` | the vignette and the stroke behind text. Never draw with them |

`mix(a, b, t)`, `dim(colour, t)` (towards the background) and `hot(colour, t)` (towards white) make in-between
colours. Manim's own colour constants (`BLUE`, `YELLOW`, `WHITE`, ...) are not exported by `kit`: a scene that
uses one stops with a `NameError`. A scene must not contain a hex colour. A shape that names no colour gets Manim's
default (`Circle()` is Manim red, `Line()` and `Dot()` are white): the lint reports it as `colour`.

| Group | Names and values |
|---|---|
| Strokes | `W_HAIR` 1, `W_LINE` 2, `W_BOLD` 3, `W_HERO` 4.5. Set every stroke width from these |
| Type scale | `"display"` 64, `"title"` 44, `"body"` 32, `"label"` 24, `"fine"` 18 (`SCALE`); `TAG_SIZE` "label", `CITE_SIZE` "fine" |
| Frame | 14.22 x 8 units. Safe area `SAFE_X` 6.4, `SAFE_Y` 3.4 |
| Grid and gaps | `GRID` 0.2 (baselines); `GAP_XS` 0.1, `GAP_S` 0.25, `GAP_M` 0.5, `GAP_L` 1.0 |
| Fixed baselines | `TITLE_Y` 2.8, `FINE_Y` -3.2 |
| Points | `DOT_R` 0.034, `DOT_R_HERO` 0.07 |
| Run times | `T_QUICK` 0.6, `T_ENTER` 1.0, `T_MOVE` 2.0, `T_COUNT` 2.5, `T_CAMERA` 3.0, `T_REVEAL` 3.5 |
| Stagger | `LAG_FEW` 0.3 (2-5 items), `LAG_SOME` 0.08 (6-30), `LAG_MANY` 0.015 (31-300); `lag_for(n)` picks one |
| Timing contract | `CUE_TOLERANCE` 0.07 s, `MIN_PLAY` 0.3 s, `REST_EASE` 0.4 s |
| Limits | `MAX_WORDS` 12, `MAX_ZOOM` 2.0, `MAX_FREEZE` 2.5 s |

---

## 5. Type (`type.py`)

New Computer Modern Book for display, title and body. Inter (Medium) for label and fine. `T()` picks the face
from the size. The fonts are registered when `kit` is imported.

```python
t = T("Which change helps most on new tests?", "body", parts={"k": "most on new tests"})
t.part["k"].set_color(FOCUS)                         # a named phrase: a VGroup of exactly those glyphs
put(t, -SAFE_X, 1.4)                                 # left edge at x, BASELINE at y (edge=RIGHT or ORIGIN for other anchors)
```

| Call | Use |
|---|---|
| `T(text, size="body", color=INK, parts=None, markup=False, tracking=0.0, slant=NORMAL)` | one line of text that knows its baseline. A `\n` stops it: stack lines with `lines()` |
| `put(m, x, y, edge=LEFT)` | place by an edge and the baseline |
| `row(a, b, c, buff=GAP_S)` | left to right on ONE baseline (text, numbers and formulas mix) |
| `lines(a, b, c, leading=None, align=LEFT)` | stack lines with an exact baseline distance (default 1.2 / 0.8 / 0.6 / 0.4 / 0.4 for the five sizes) |
| `align_baseline(m, ref, dy=0)`, `snap_to_grid(m)`, `baseline_y(m)`, `em(m)` | baseline tools |
| `words(t)` | one group for each word, for a word-by-word entrance |
| `underline(t.part["k"], of=t, color=FOCUS)` + `sweep_in(bar)` | an underline that sweeps in from the left |
| `marker(t.part["k"], FOCUS, of=t)` | a highlighter stroke behind a phrase: from under the baseline to just over the x-height, from the phrase's left edge, with slanted ends. Without `of` the bottom of the phrase is taken as the baseline |
| `backstroke(t)` | a dark stroke behind the letters. **Required for every text that sits on art** |
| `tex(r"\frac{⟦num|\sigma^2⟧}{⟦den|n⟧}", "body")` | a formula (xelatex, pdftocairo). Same em and baseline as `T()`. `f.part["num"]` is colourable. Cached in `BUILD/texcache`; the first compile takes about a second. Safe when several render processes use the same formula |

**The live number.** One class for a number that changes. **Only the post's numerals are shown** (1,440; six; 20%;
about 18.5%; about 14.1%; one- or two-step): every other quantity is a length, an angle or an area with no number
(section 7a).

```python
n = LiveNumber(0, decimals=1, unit="%", prefix="about", size="title", color=INK_HI, reserve=18.5)
put(n, SAFE_X, -2.4, edge=RIGHT)                     # right edge of the whole number (with its unit) at the safe edge
self.add(n)                                          # it must be in the scene before it can follow or count
self.play(count_to(n, 18.5))                         # runs fast, slows into the value
```

- The digits sit in cells of one width, so nothing jitters. The unit (`n.unit`) and the prefix (`n.prefix`) are
  separate parts and do not move while the number counts (measured on rendered frames: 0 pixels change).
- `prefix="about"` or `prefix="≈"`. `commas=True` gives `1,440`. `anchor="right"` (default) keeps the last digit
  in place; `anchor="left"` keeps the first.
- `reserve` is the largest value the number will show. Room for it is kept, so the prefix stays where it is. While
  the value has fewer digits than the reserve, that room is a hole after the prefix ("about   0.0%"): show such a
  number only once it has all its digits (born at 10 on the way to 18.5, as the reel does), or start it there.
- `n.follow(tracker, fn)` shows `fn(tracker.get_value())` on every frame. Drive the geometry from the same tracker.
- `n.place(point)` puts the END OF THE DIGITS on the baseline at `point` (the unit comes after it). Use `put()`
  to place the whole number by an edge.
- It can be faded, moved, scaled and pinned while it counts, also inside a group that is animated.

**The layout lint.** `check_layout(mobjects, frame)` returns the issues; `Narrated` runs it after every play with
`EXPLAINER_LINT=1`. Everything is measured on screen, also while the camera is pushed in.

| Rule | It reports |
|---|---|
| `safe-area` | a visible object outside \|x\| <= 6.4, \|y\| <= 3.4. Exempt: `m.bleed_ok = True`; glows and raster pictures; world shapes while the camera is away from its rest framing. Text and pinned objects are never exempt |
| `text-text` | two texts closer than 0.1 |
| `text-shape` | a shape (its outline, sampled every 0.05) or a cloud point within 0.1 of a text that has no `backstroke()` |
| `text-on-fill` | a text without a backstroke on light: a glow or a picture that is brighter than 12% under it, or inside a bright filled shape (a dark `SLATE` panel passes) |
| `text-size` | text smaller than 24 on screen (18 is for the HUD only) |
| `type-scale` | a font size that is not 64 / 44 / 32 / 24 / 18 |
| `text-face` | a `Text` or `MarkupText` that was not built with `T()` (its words are counted too) |
| `colour` | a stroke or fill in a Manim stock colour that the theme does not have, or pure white or black |
| `word-count` | more than 12 words on screen (the HUD does not count) |

`m.layout_ignore = True` takes an object out of the lint. Use it only for a mark that belongs to a text.
The lint sees the picture after every play and at the end, so a camera move, a label that comes and goes between
two cues, and the cue frames are all checked. An issue is reported once, when it appears. It does not see shape
against shape. When Manim breaks a text up (a part of it is faded out or replaced), the lint still reads the loose
glyphs as that text: they keep their words, their size and their backstroke.
`layout_overlay(issues, frame)` draws the safe area and the boxes; `word_count(mobjects)` counts the words.

---

## 6. Light and points (`fx.py`)

`Narrated` uses `FxCamera`. It draws everything below, and it fixes two faults of the stock camera (stroke caps
and joins that leak from one object to the next).

**`DotCloud`: thousands of points as one object.** Never make a `VGroup` of hundreds of `Dot`s: 1,000 `Dot`s
cost 6 to 7 times more to draw (measured), and more again to move. (`kit.DotCloud` replaces Manim's class of
that name.)

```python
pts, fade = soft_field(700, 4.3, 3.6, seed=7, centre=(-4.05, 0.95))               # a soft organic outline
cloud = DotCloud(pts, color=DATA, opacity=0.9 * fade, glow=0.2).drift(seed=1, twinkle=0.15)
self.play(cloud.appear(sampling_rhythm(700, total=4).starts))                       # points come into being
self.play(cloud.to(centers=target, lag=0.5, order="radial", arc=0.4))               # regroup, each point on an arc
self.play(cloud.to(color=FOCUS, glow=0.8, idx=group), cloud.to(opacity=0.3, idx=others))
hero = cloud.split(group); self.add(hero)                                           # a cluster lifts out as its own cloud
whole = DotCloud.join(cloud, hero); self.remove(cloud, hero); self.add(whole)       # and back into one
```

| Call | Use |
|---|---|
| `DotCloud(centers, radius=DOT_R, color=DATA, opacity=1, glow=0, rgbas=None, ids=None)` | per point: `radii`, `rgbas` (the alpha is the point's opacity), `glows` (0..1), `ids` (a stable integer). `opacity` and `radius` may be one value per point |
| `.to(centers, color, opacity, radius, glow, idx, lag, order, arc, flash, pop)` | animate the chosen points. `order`: `"index"`, `"random"`, `"x"`, `"y"`, `"radial"` or sort keys. `flash` adds glow and `pop` adds radius (a share of the radius) at the start of each point's window; both decay by its end: a point that "arrives" or "is picked" |
| `.appear(starts, fade, idx, opacity, order, flash=0.9, pop=0.8)` | points arrive at their own times, each with a small flash and pop |
| `.set_colors / set_opacities / set_radii / set_glows(value, idx)` | change at once |
| `.drift(amp, period, seed, twinkle=0)` | a slow sway for every point, and a brightness twinkle (a paint-time offset: the centres stay exact). It is a function of (seed, id, film time) |
| `.split(idx)`, `.subset(idx)`, `DotCloud.join(*clouds)` | take points out as a new cloud / copy them / join clouds into one (ids and drift go with the points) |
| `Transform(cloud, other)`, `FadeIn`, `FadeOut`, `.animate.shift(...)` | stock animations work (`Transform` needs equal sizes) |
| `soft_field(n, width, height, seed, centre, within=None, rim=0.16, jitter=0.4)` | exactly `n` points inside a wavy ellipse (or inside a closed shape `within`), and each point's `fade` for a soft rim: the pool |
| `field_points(n, w, h, seed, jitter=0.32, centre=(0, 0))` | a loose field in a box (a hard edge); `jitter` is the random offset as a share of the lattice pitch |
| `sunflower_points(n, radius, centre, turn=0, jitter=0, seed=0)` | an even disc; `jitter=0.3` hides the spiral arms of a large disc |
| `cluster_points(sizes, centres)` | several discs of points |
| `match_points(src, dst)` | reorder `dst` so that the regrouping is one flow, not a scramble |
| `nearest_labels(points, centres, sizes)` | give each point a cluster of a fixed size near it |

Several `cloud.to()` on one cloud can share a play when they change different points or different properties
(colour and opacity are two properties), in any order. The animation class behind `to()` and `appear()` is
`CloudTo`.

Cost at 1920x1080, CPU per frame, measured while other renders ran on the machine: 1,000 points 11 ms, with halos
23 ms; the reel's 1,440 points with halos 33 ms. (The probe measured 3.9 ms for 1,000 points on a quiet machine.)

**The film clock.** `film_time()` is the film time of the frame that is painted now, and `idle_gain()` the factor
on idle amplitudes (0 at the two ends of a scene). Use them in an updater of your own idle motion, so that it
continues across joins and rests in the poses: `m.add_updater(lambda m: m.set_opacity(0.8 + 0.1 * idle_gain() *
np.sin(film_time())))`.

**Glow and soft light**

| Call | Use |
|---|---|
| `glow_sprite(radius, colour, peak=0.85)` | a soft halo as one picture: the cheapest (0.2 ms at radius 0.6, 1.4 ms at radius 2.5). Put a small core on top |
| `RadialGlow(radius, colour, peak)` | a vector halo: follows `set_color`, `Transform`, `stretch`. 1.6 ms at radius 0.6, but 17 ms at radius 2.5: for a large halo use a sprite |
| `soft_band(width, height, colour, peak=0.18, edge=0.3, axis=1)` | a band of light with soft edges, as one picture: a spread, a range, a gap. It stretches and fades |
| `DotCloud(..., glow=0.3)` | a halo under every point. Halos add up where points are dense |
| `Runner(path, colour)` | a glowing head with a tail (section 7) |

Both glows are dithered, so they show no rings, also on a flat ground. Make a sprite inside `build()`: it is made
for the render size (`px_per_unit()` is the number of pixels in one scene unit). `Trail(points, widths, rgbas)` is
the ribbon that `Runner` uses for its tail: a width and a colour at every sample.

**Pictures, clip, blend**

| Call | Use |
|---|---|
| `RasterLayer(rgba, height)` | a numpy picture, blitted (use it in place of `ImageMobject`, which is 100 times slower). It fades, moves, scales. It cannot rotate |
| `bake(self, mobjects)` | render complicated static art once (many faint paths) and get it back as a `RasterLayer` in the same place |
| `set_clip(mob, clip_mob)` | show `mob` only inside `clip_mob`. Move or scale the clip for a wipe. **Add the clip to the scene before the art** |
| `set_blend(mob, "screen" or "add")` | overlapping light gets brighter |
| `smooth_closed(points, **style)`, `blob_points(seed, n, radius, rough, phase)`, `hull_blob(points, pad)` | organic closed shapes; a soft outline around a set of points |
| `install_background(scene, **kw)` | the dithered vignette (`Narrated` does this) |

---

## 7. Motion (`motion.py`)

| Name | Use |
|---|---|
| `ENTER` | things that arrive: fast start, soft landing |
| `MOVE` | A to B, morphs, regrouping |
| `EXIT` | things that leave |
| `CLOCK` | simulated time, sweeps, tracing: linear. A clock must not ease |
| `COUNT` | a number that runs fast and slows into its value |
| `GLIDE` | camera moves |
| `PULSE` | a colour or brightness pulse that returns |

No elastic, bounce or back easing.

| Call | Use |
|---|---|
| `late(start, end=1.0, func=ENTER)` | a rate function that waits: `enter(label, rate_func=late(0.6))` lands the label in the last 40% of the play that moves its object |
| `window(t0, t1, total, func=MOVE)` | the same in seconds of a play that lasts `total` (inside `play_until(t, ...)` the total is `self.left(t)`) |
| `timed(anim, t0, t1=None)` | `anim` runs from scene time `t0` to `t1` (default: `t0` plus its own run time) inside a longer play; the window is worked out when the play begins. `timed(enter(label), *self.word_span(2, "gate"))` lands a label on its word; `timed(leave(old), t)` keeps leave's own length. It takes `x.animate...` too. Use it at the top level of a play |
| `pulses(times, total, width=0.6)` | a rate function with one PULSE at each of `times` (seconds of a play of `total` seconds) |
| `lag_for(n)` | the stagger for `n` items |
| `enter(mob)`, `leave(mob)` | the standard entrance (text: glyph by glyph, without moving; the stagger stays inside `late()`, `window()` and `timed()`) and exit (1 s). Updaters keep running |
| `born_from(source, new, arc=0)` | `new` comes from a copy of `source` (or grows out of a point). `source` stays. Out of a cloud, a picture, a trail or a runner, `new` grows from its centre (they cannot be morphed); for one point of a cloud use `born_from(cloud.points[i], new)` |
| `hand_over(old, new, arc=0)` | `old` becomes `new` |
| `Stroke(points, width, colour, taper=(head, tail))` + `draw(stroke)` | a stroke whose ends taper, drawn along its path. One outline sample every 0.04 units, so a long curve has no facets |
| `Runner(path, colour, duration, tail=1.2, halo=0.42)` | a glowing head with a fading tail. `path`: a function of time, samples, or a VMobject. `halo` is the radius of its light. `runner.clock` is its `ValueTracker` |
| `runner.run(to)` | an animation ON the runner (`play` adds it to the scene): the head runs to `to` and stays lit |
| `runner.flight(appear=0.12, absorb=0.3)` | an animation: the head fades in, runs the whole path, its tail runs in, and it is absorbed and leaves the scene. Works in `LaggedStart`, `window()` and `timed()` |
| `fly(path, colour, tail=0.6)` | a runner and its flight in one call: `self.play(LaggedStart(*[fly(p, DATA, rate_func=MOVE) for p in paths], lag_ratio=0.15), run_time=2.6)` |
| `runner.start()`, `runner.stop()` | the clock runs by itself (film time) through waits and other plays |
| `ambient(mob, amp, period, seed, pulse=0)`, `still(mob)` | a slow seeded sway and brightness pulse for a hold (art only, never text that must be read); it reads the film clock |
| `sampling_rhythm(n, total, slow=1.4, mid=0.45, n_mid=4)` | start times for "one slow draw, a few at 0.45 s, then many per second". `.starts` feeds `cloud.appear`; `.group(anims)` squeezes separate animations into the rhythm |
| `count_to(number_or_tracker, value)` | count a `LiveNumber` (or any tracker) to a value |

Shapes morph in `born_from` and `hand_over`. Text does not: the same words at another size travel and change
size; other words cross-fade while they travel.

### 7a. Measured shapes (`shapes.py`)

A quantity that is not one of the post's numerals is drawn as a length, an angle or an area, zero-based, with no
number and no axis numbers. Each one has a fixed family, so it is safe in updaters; `follow(tracker, fn)` drives it.

| Call | Use |
|---|---|
| `LiveLength(value, start, unit=0.5, color=INK, track=None, gate=None, notches=(), halo=0.3)` | a bar from a zero point with a glowing end; `track` draws a hairline to that value and a zero tick, `gate` a bold gate tick (0.2 under to 0.8 over the bar), `notches` small cuts that show once the bar has passed them. `tip_point` is the end now |
| `Dial(share, radius=0.16, color=FAIL)` | a ring with an arc for a share of a whole (the storyboard's mini dial); `set_share(v)` |
| `Area(fn, x0, x1, base=0, color=INK, opacity=0.18)` | the area under `y = fn(x)`; `set_range(a, b)` or `follow(tracker)` sweeps it; `curve_points()` gives the curve for a `Stroke` |

---

## 8. Rules

The lint (L), the QA tool `qa.py` (Q) or the reviewer (R) checks each one.

**Pacing**
1. Most plays last 1 to 3 s. No play under 1 s, except a deliberate snap (at most 2 in a scene). (Q)
2. At least a third of the plays last 2 s or more. The main change of a scene lasts 3 to 5 s. (Q)
3. Camera moves last 2 to 6 s. Zoom at most 2 (`push_in` refuses more). (Q)
4. An entrance shares its play with the exit or the dimming of what came before. Lone fade-ins are at most a
   quarter of the animations; hand-overs at least 15%. (Q)
5. A label that names a moving thing lands late in the same play (`late`, `timed`), not in a play of its own. (R)

**Motion**
6. No freeze longer than 2.5 s while the voice speaks; frozen share under 30%. Ambient motion alone does not
   count as an event. Aim for motion through about 60% of each spoken line. (Q)
7. A hold is never fully still: `cloud.drift()`, `ambient()`, a runner. Text that must be read does not drift. (R)
8. A `LiveNumber` only for the post's numerals. Every other quantity is a length, an angle or an area with no
   number (`LiveLength`, `Dial`, `Area`), driven by one tracker. (R)
9. Randomness is seeded draws that are animated (`sampling_rhythm`), never a static row of items. (R)
10. A moving point that matters has a glow and a tail (`Runner`, `fly`). At most 5 glowing objects at one time; a
    cloud is one. (R)

**Words**
11. At most 12 words on screen, citations excepted. (L)
12. Labels have 1 to 4 words, sit within 0.25 of their object, and have its colour. No legends. Never show the
    sentence that the voice is saying. (R)
13. Font sizes only from the scale; 18 only for the citation; no text under 24 on screen. (L, Q)
14. Text on art has a `backstroke()`. (L)
15. Text enters with `enter()` or word by word. Emphasis is a colour change in place, an underline sweep or a
    marker. Text does not move while it must be read. No bold for emphasis. (R)

**Layout**
16. Nothing visible outside the safe area, unless it is marked `bleed_ok` (and `# qa: bleed` in the scene). (L, Q)
17. Gaps from `GAP_XS / S / M / L`. Baselines on the grid: give `put()` a multiple of 0.2. (R)
18. The stage is set at t = 0. The first frame of scene N+1 is the last frame of scene N: both build the same
    objects in the same state (the pose; same seeds, amplitudes, periods and point ids), and the rest ease makes the
    picture exact. (Q)
19. Titles and read-outs are pinned during camera moves; labels of world objects use `follow_label`. A push-in ends
    with a pull-back, unless the next scene starts from that framing. (R)
20. Focus is made by dimming the rest (opacity 0.2 to 0.4) and restoring it. (R)

**Colour and finish**
21. Colours only from `kit.theme`, each with its one meaning. At most 3 hues plus greys in a frame. (L for Manim's
    defaults; R; no colour literal passes review)
22. Every stroke width is one of the four. A line gets quieter through opacity or a grey, not through thinness. (R)
23. No rounded word-cards, no bullet or numbered lists, no stamps, no strike-through lists, no rotated text, no
    grid of squares as data, no plain arrow between two labels. (Q warns)
24. Only the kit's rate functions. (R)
25. A picture that a viewer could take for data carries `self.hud_tag()`. (R)

---

## 9. Traps

1. **No `Tex`, `MathTex`, `DecimalNumber`, `Integer`, `Variable`, `Title`, `BulletedList`, `Matrix`, `MathTable`,
   `BraceLabel`.** They need `dvisvgm`, which is not installed. `kit` replaces them with stand-ins that stop the
   scene and name the way out (`NO_LATEX`). Use `tex()`, `T()`, `LiveNumber`. Axis numbers need LaTeX too.
2. **`self.duration` is Manim's**, the run time of the last play (0 before the first one). The scene length is
   `self.scene_duration`.
3. **`self.play(a, b, run_time=3)` sets 3 s on every animation in the play**, also on one that was given its own
   `run_time`. Shape the inside of a play with `late()`, `window()` and `timed()`.
4. **Updaters.** (a) Never replace submobjects inside an updater: the old ones stay on screen until the play
   ends. Change points in place (`LiveNumber`, `Runner`, `Stroke` and the shapes do). `always_redraw` is safe.
   (b) Set the first state by hand before `self.add` (call the updater once). (c) Updaters run in scene order: add
   the driver before the thing it drives. (d) Manim stops the updaters of an object while an animation plays on
   it; `enter()`, `leave()`, `LiveNumber` and `Runner` do not stop. A group that holds a `LiveNumber` or a `Runner`
   is safe to animate when its members are in the scene (the kit animates it in place). A group that is NOT in
   the scene and is played with a stock animation (`FadeIn(VGroup(n, label))`, also inside a `LaggedStart`) stops
   them for the play (measured: the number shows 2 values instead of 14): use `enter()` or pass
   `suspend_mobject_updating=False`.
5. **Never share a media directory between two render processes.** One process reads a text file while the
   other writes it, and it crashes. One `--media_dir` for each process (`render.py` does this).
6. **The text cache.** Manim keeps one SVG per text in `<media_dir>/texts`, named by the font NAME. If a scene
   was ever rendered while a font was missing, the fallback glyphs come back for ever. `T()` checks the face
   and stops with a message; then delete that `texts` folder.
7. **Registration order.** A font that is registered after the first `Text` of the process is listed but not
   used. `from kit import *` must come before anything that builds text. A font family list has no space after
   the comma (`SERIF`).
8. **Transforms between two font sizes.** `TransformMatchingShapes` finds no match between a text at 44 and the
   same text at 32, and a glyph morph between two strings looks broken. Use `hand_over` / `born_from`.
9. **Two faces in one line** need `T(..., markup=True)` with `<span font_family=...>`. `t2f` breaks the baseline.
10. **Strokes are in scene units**: at 2x zoom a line is twice as thick on screen. `keep_stroke(mob, self.frame)`
    (ordinary strokes and `Stroke`; not the radii of a cloud or a runner's tail, which are sizes in the world) or
    `self.pin(mob)`. A world label grows with the zoom too: `self.follow_label(label, anchor)`.
11. **A pinned object is in screen coordinates.** `next_to` between a pinned and a world object is right only
    while the camera is at rest. Build and pin text while the camera is at rest: text built in world units while
    the camera is pushed in keeps that size ON SCREEN when it is pinned (a 24 label built at 2x becomes 48).
12. **One `VMobject` is one stroke**: paths inside one object do not get brighter where they cross. Make one
    object for each path at low opacity, then `bake()`.
13. **A closed smooth shape** made with `set_points_smoothly([*pts, pts[0]])` gets a corner when it starts left
    of or below the origin. Use `smooth_closed`.
14. **A colour list on a stroke** is a straight gradient across the bounding box, not along the path.
15. **`set_clip`: add the clip before the art** (`self.add(clip, art)`), or the wipe shows only when the play ends.
16. **Static art first.** Manim paints the objects before the first moving one once per play. Add the still
    things first. While the camera moves, everything is painted on every frame.
17. **`DotCloud`**: `scale()` moves the points apart but keeps their radii; `split()` and `join()` are for the time
    between two plays; two `to()` in one play must not change the same property of the same point (colour and
    opacity are different properties).
18. **`cloud.appear(..., run_time=...)`** shorter than the last fade cuts the last fades short. That is intended
    (a count that lands on a word).
19. **`bake()`** has the resolution of the render and the framing of the camera at that moment. Do not zoom far
    into it.
20. **Caching is off** in `Narrated` (Manim's play cache does not see the background and would go stale).
21. Manim prints `Some options were not used: {'shortest': ...}` when a scene has sound. It is harmless.
22. **Names.** `from kit import *` brings short names: `lines`, `words`, `row`, `window`, `still`, `draw`, `put`,
    `timed`, `fly`, `pulses`. Do not use them as variable names: the kit function is then hidden.
23. **A runner in a play.** `runner.run()` and `runner.flight()` add the runner to the scene. A started runner
    (`start()`) must be added by hand (`self.add(runner)`), or nothing runs.
24. **`at()` stops one frame before the cue.** After `self.at(2)`, `self.now` is one frame before line 2 starts;
    the next play's first change is on the cue. Do not test `self.now >= self.line_start(2)`.

---

## 10. Checks, costs, limits

- `selftest.py`: 115 checks in about 10 s. Fonts and faces; baselines; the live number; the same layout at
  854x480, 1920x1080, 2560x1440 and 3840x2160; the timing contract (frames, tolerance, the play_until floor, cue
  errors, the render.py guard); the film clock (no frame lost at play boundaries at 15 and 30 fps; exact joins);
  the lint (every rule, lint after every play, parts of texts); the camera effects; the motion helpers (stagger
  windows, hand-overs from clouds, runners and flights, `timed`, pulses); the shapes; LaTeX; the kit's own rules.
- The reel (35 s): about 10 s to render at draft size, about 30 s at 1920x1080 and 30 fps with the lint on (measured
  on this machine while other work ran).
- Everything is in scene units. Pixel sizes (sprites, halos, the background) come from the render size.
- Not tested: 60 fps, `ThreeDScene`, `ZoomedScene`, the OpenGL renderer.
