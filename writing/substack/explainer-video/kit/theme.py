"""The single source of every colour, stroke width, size, spacing and timing constant of the film.

No other file of the kit, and no scene, may hold a colour literal or a Manim colour constant. The
design panel may change the hex values here; the names and their meanings stay.

    MODEL  blue       the model and the ordinary run
    DATA   starlight  training data (a warm near-white: the design panel's value; it differs from MODEL by more
                      than hue, so the two stay apart when they are dimmed)
    FOCUS  gold       the thing we change
    FAIL   red        failure
    COPY_B violet     copy B of the tiny learner (its event contribution suppressed), nothing else
    PASS   green      pass (the storyboard does not use it: there a passing test is a quiet pale light, INK at 60%)
    INK, MUTED and the grey ramp carry text and structure, never meaning.

FAIL and PASS nearly merge for a viewer with deuteranopia: never let them differ by colour alone (add a shape or a
position cue).

Every hue has three shades: ``X_LO`` (deep, for fills and dimmed states), ``X`` (base) and ``X_HI``
(light, for cores and highlights).
"""

from __future__ import annotations

from manim import ManimColor, interpolate_color

# --------------------------------------------------------------------------- canvas
BG = ManimColor("#0C0E13")          # near-black with a little blue: the centre of the vignette
BG_EDGE = ManimColor("#040507")     # the corners of the vignette
VIGNETTE = dict(centre=(0.5, 0.47), reach=1.08, power=1.7, noise=1.25, seed=7)

# --------------------------------------------------------------------------- hues (one meaning each)
MODEL_LO, MODEL, MODEL_HI = ManimColor("#22718C"), ManimColor("#58C4DD"), ManimColor("#A9E3F1")
DATA_LO, DATA, DATA_HI = ManimColor("#8F8B7F"), ManimColor("#E8E2D0"), ManimColor("#FFF9EA")
FOCUS_LO, FOCUS, FOCUS_HI = ManimColor("#B98A1B"), ManimColor("#FFD24A"), ManimColor("#FFE9A3")
FAIL_LO, FAIL, FAIL_HI = ManimColor("#A83F36"), ManimColor("#FF6B5E"), ManimColor("#FFA79E")
COPY_B_LO, COPY_B, COPY_B_HI = ManimColor("#5D4C9E"), ManimColor("#A98BFF"), ManimColor("#D6C9FF")   # copy B (pilot), nothing else
PASS_LO, PASS, PASS_HI = ManimColor("#4F8F38"), ManimColor("#8BD55E"), ManimColor("#C0EBA4")

# --------------------------------------------------------------------------- neutrals
INK_LO, INK, INK_HI = ManimColor("#B5B1A7"), ManimColor("#ECE7DB"), ManimColor("#FFFDF7")
MUTED = ManimColor("#8D95A5")       # small notes, the HUD tag, citations
GREY_1, GREY_2, GREY_3, GREY_4, GREY_5 = (ManimColor(h) for h in ("#C8CCD6", "#9299A8", "#646B7A", "#3B414E", "#20242D"))
SLATE = ManimColor("#161A22")       # solid bodies ("machine" faces) that sit on the background
CORE = ManimColor("#FFFFFF")        # the white-hot centre of a glow; never used for text
VOID = ManimColor("#000000")        # technical black (masks, placeholders); never a visible colour
BACKSTROKE = ManimColor("#080A0D")  # the dark stroke behind text that sits on art (between BG and BG_EDGE)
LINT_SAFE, LINT_BAD = MODEL, FAIL   # the debug overlay

HUES = {"MODEL": MODEL, "DATA": DATA, "FOCUS": FOCUS, "FAIL": FAIL, "PASS": PASS, "COPY_B": COPY_B}
PALETTE = {name: value for name, value in list(globals().items()) if isinstance(value, ManimColor)}


def mix(a, b, t: float = 0.5) -> ManimColor:
    """The colour a fraction ``t`` of the way from ``a`` to ``b`` (RGB)."""
    return interpolate_color(ManimColor(a), ManimColor(b), t)


def dim(color, t: float = 0.6) -> ManimColor:
    """``color`` pushed a fraction ``t`` of the way into the background (for the parts that are not in focus)."""
    return mix(color, BG, t)


def hot(color, t: float = 0.6) -> ManimColor:
    """``color`` pushed a fraction ``t`` of the way to white (for the core of a glow)."""
    return mix(color, CORE, t)


# --------------------------------------------------------------------------- strokes (Manim stroke units; 1 = 0.01 scene units)
W_HAIR, W_LINE, W_BOLD, W_HERO = 1.0, 2.0, 3.0, 4.5
BACKSTROKE_WIDTH = {"display": 6.0, "title": 6.0, "body": 5.0, "label": 3.5, "fine": 3.0}

# --------------------------------------------------------------------------- frame, safe area, grid, gaps
FRAME_H = 8.0
FRAME_W = FRAME_H * 16 / 9
SAFE_X, SAFE_Y = 6.4, 3.4                 # nothing visible outside |x| <= 6.4, |y| <= 3.4 (except a marked bleed)
GRID = 0.2                                # baseline grid pitch
GAP_XS, GAP_S, GAP_M, GAP_L = 0.1, 0.25, 0.5, 1.0
TITLE_Y, FINE_Y = 2.8, -3.2               # baselines of a scene title and of the fine-print line
MAX_ZOOM = 2.0                            # a camera push-in never magnifies by more than this

# --------------------------------------------------------------------------- type scale
SCALE = {"display": 64, "title": 44, "body": 32, "label": 24, "fine": 18}
LEADING = {"display": 6 * GRID, "title": 4 * GRID, "body": 3 * GRID, "label": 2 * GRID, "fine": 2 * GRID}
SERIF_SIZES = ("display", "title", "body")     # New Computer Modern Book; "label" and "fine" are Inter
MAX_WORDS = 12                                  # on screen at one time, citations and the HUD tag excepted
TAG_TEXT, TAG_SIZE, CITE_SIZE = "illustration", "label", "fine"   # the two fixed marks: the tag is Inter 24, a citation Inter 18

# --------------------------------------------------------------------------- points and glows
DOT_R = 0.034                             # one point of a field
DOT_R_HERO = 0.07                         # the head of a runner, a single point that matters
GLOW_REACH = 4.5                          # halo radius of a field point, in dot radii
GLOW_POWER = 2.2                          # falloff exponent of every halo: alpha = (1 - r) ** GLOW_POWER
GLOW_PEAK = 0.85

# --------------------------------------------------------------------------- timing
T_QUICK, T_ENTER, T_MOVE, T_REVEAL, T_CAMERA, T_COUNT = 0.6, 1.0, 2.0, 3.5, 3.0, 2.5
LAG_FEW, LAG_SOME, LAG_MANY = 0.3, 0.08, 0.015   # 2-5 items, 6-30 items, 31-300 items (above that use motion.lag_for)
RHYTHM_SLOW, RHYTHM_MID, RHYTHM_N_MID = 1.4, 0.45, 4   # the sampling rhythm: one slow draw, a few at 0.45 s, then many
AMBIENT_AMP, AMBIENT_PERIOD = 0.022, 7.0         # the gentle motion of a hold: 3 px at 1080p, one sway in 7 s
MAX_FREEZE = 2.5                                  # seconds; QA measures this, the kit only names it
CUE_TOLERANCE = 0.07                              # seconds a cue may be late before the scene stops (2 frames at 30 fps, 1 at 15)
MIN_PLAY = 0.3                                    # seconds that play_until() must have left, unless it is told min_time=0
REST_EASE = 0.4                                   # seconds over which idle motion eases to rest at the two ends of a scene

__all__ = [name for name, value in list(globals().items())
           if not name.startswith("_") and name not in ("annotations", "ManimColor", "interpolate_color")]
