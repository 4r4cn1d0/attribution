"""Type for Manim Community 0.21 (Cairo): fonts, baseline-true text, a live number, LaTeX without dvisvgm, layout lint.

    fonts        register_fonts() exposes New Computer Modern Book and Inter (TeX Live files) to Pango for this
                 process. It must run before the first Text of the process: importing kit does it.
    T()          text that knows its baseline and its em; named sub-phrases; optional tracking
    row, lines, put, align_baseline, snap_to_grid, words      baseline-true layout
    underline, marker, sweep_in, backstroke                    emphasis and legibility
    LiveNumber   a number that counts without jitter: fixed digit cells, separate unit and prefix, thousands separators
    tex()        LaTeX -> PDF -> SVG (pdftocairo) -> SVGMobject, cached under BUILD/texcache, same em and baseline as T()
    check_layout, lint, layout_overlay                         safe area, overlaps, sizes, word count

Never use Tex, MathTex or DecimalNumber: they need dvisvgm, which is not installed.
"""

from __future__ import annotations

import hashlib
import itertools
import os
import re
import shutil
import subprocess
import tempfile

from pathlib import Path

import manimpango
import numpy as np
from manim import (LEFT, NORMAL, RIGHT, UP, ManimColor, MarkupText, Polygon, Rectangle, SVGMobject, Text, Transform,
                   ValueTracker, VGroup, VMobject, config)

from . import theme as th
from .paths import TEX_CACHE, TEXLIVE_OTF

# --------------------------------------------------------------------------- fonts
# family name accepted by Text(font=...)  ->  files to register
FONT_FILES = {
    # NewCM10 Regular and Book share OS/2 weight 400 and Pango cannot tell them apart: register Book only.
    "NewComputerModern10": ["public/newcomputermodern/NewCM10-Book.otf", "public/newcomputermodern/NewCM10-BookItalic.otf",
                            "public/newcomputermodern/NewCM10-Bold.otf", "public/newcomputermodern/NewCM10-BoldItalic.otf"],
    # symbols the text face lacks (>=, <=, ~~, !=, ...) come from here through a Pango family list
    "NewComputerModernMath": ["public/newcomputermodern/NewCMMath-Book.otf"],
    "Inter": ["public/inter/Inter-Regular.otf", "public/inter/Inter-Medium.otf", "public/inter/Inter-SemiBold.otf",
              "public/inter/Inter-Italic.otf"],
}
# A Pango family LIST. There must be NO space after the comma, or the second family is not found and Helvetica is used.
SERIF = "NewComputerModern10,NewComputerModernMath"
SANS = "Inter"
MEDIUM = "MEDIUM"
X_HEIGHT = {SERIF: 0.431, SANS: 0.546}       # x-height in em: how a resolved face is recognised


def register_fonts() -> list[str]:
    """Register the font files with CoreText at process scope and check that Pango lists the families."""
    already = {f.path for f in manimpango.registered_fonts}
    for rels in FONT_FILES.values():
        for rel in rels:
            path = (TEXLIVE_OTF / rel).resolve()
            if not path.exists():
                raise FileNotFoundError(f"kit font file is missing: {path}")
            if str(path) not in already and not manimpango.register_font(str(path)):
                raise RuntimeError(f"could not register {path}")
    missing = [k for k in FONT_FILES if k not in set(manimpango.list_fonts())]
    if missing:
        raise RuntimeError(f"registered but not listed by Pango: {missing}")
    return sorted(FONT_FILES)


register_fonts()

EM_PER_SIZE = 1 / 72                      # 1 em in scene units = font_size / 72 (Pango Text, measured)
_K = 0.05                                 # manim.mobject.text.text_mobject.TEXT_MOB_SCALE_FACTOR
_START_X = 30                             # manim.constants.START_X: x of the Pango layout origin in the text SVG
_PANGO_PT_PER_SIZE = 1 / 4.8              # Manim gives Pango a font size of font_size / 4.8 points
_baseline_cache: dict = {}
_verified: set = set()
_glyph_count_cache: dict = {}
_word_maps: dict = {}
_text_keys = itertools.count(1)


def size_of(size: float | str) -> float:
    return float(th.SCALE[size]) if isinstance(size, str) else float(size)


def font_for(size: float | str) -> str:
    """Serif for display, title and body; Inter for labels and fine print."""
    if isinstance(size, str):
        return SERIF if size in th.SERIF_SIZES else SANS
    return SERIF if size >= th.SCALE["body"] - 1e-6 else SANS


def _verify_face(font: str) -> None:
    """Fail loudly if Pango did not resolve a kit font (a Text was built before the fonts were registered, or the
    media directory holds a stale text SVG from such a run)."""
    if font in _verified or font not in X_HEIGHT:
        return
    x = Text("x", font=font, font_size=96, warn_missing_font=False)
    ratio = x.height / (96 * EM_PER_SIZE)
    if abs(ratio - X_HEIGHT[font]) > 0.02:
        raise RuntimeError(
            f"font {font!r} was not resolved (x-height {ratio:.3f} em, expected {X_HEIGHT[font]:.3f}). Import kit before "
            f"anything builds a Text, and delete the text cache {config.get_dir('text_dir')} (it may hold fallback glyphs).")
    _verified.add(font)


def _svg_baseline(cls, font, size, weight, slant) -> float:
    """Baseline height in the pre-scale SVG frame of a Pango text built with should_center=False.

    Every Text of one font and size is laid out from the same origin, so the baseline is the same for all strings.
    It is read once from a reference "x", whose bottom edge is on the baseline.
    """
    key = (cls.__name__, font, float(size), weight, slant)
    if key not in _baseline_cache:
        ref = cls("x", font=font, font_size=size, weight=weight, slant=slant, should_center=False, warn_missing_font=False)
        c = ref.get_center()[1]
        _baseline_cache[key] = c - (ref.get_bottom()[1] - c) / _K
    return _baseline_cache[key]


def _key_colors(n: int) -> list[str]:
    return [f"#FE{(17 * i + 3) % 256:02X}{(101 * i + 7) % 256:02X}" for i in range(n)]


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------- text with a baseline
def T(text: str, size: float | str = "body", color=th.INK, font: str | None = None, weight: str | None = None,
      slant: str = NORMAL, markup: bool = False, parts: dict[str, str] | None = None, chars: bool = False,
      tracking: float = 0.0, **kw):
    """Pango text with ``.baseline_frac``, ``.em_frac`` and ``.part``. One line only (stack lines with ``lines()``).

    size      a name from the type scale ("display" 64, "title" 44, "body" 32, "label" 24, "fine" 18) or a number
    font      default: New Computer Modern Book for display, title and body; Inter for label and fine
    markup    build a MarkupText (Pango markup: <i>, <span fgcolor=... font_family=...>); two families or weights in
              one line need this, ``t2f`` breaks the baseline
    parts     {"name": "substring"}: ``t.part["name"]`` is the VGroup of those glyphs, for colour or motion
    chars     disable ligatures so that ``t[i]`` is character i (use only for a typewriter effect in Inter)
    tracking  extra letter spacing in em (0.02 opens up small capitals and fine print)
    Every glyph remembers its text and its place in it (``kit_glyph``), so the lint still reads the words when Manim
    breaks the text up (a part that is faded out or replaced).
    """
    assert "\n" not in text, "T() is one line: stack lines with lines()"
    name = size if isinstance(size, str) else None
    size = size_of(size)
    font = font or font_for(name or size)
    weight = weight or (MEDIUM if font == SANS else NORMAL)
    _verify_face(font)
    if tracking:
        assert not parts, "tracking= builds a MarkupText; colour the spans in the markup instead of parts="
        spacing = int(round(tracking * size * _PANGO_PT_PER_SIZE * 1024))
        text, markup = f'<span letter_spacing="{spacing}">{text if markup else _escape(text)}</span>', True
    cls = MarkupText if markup else Text
    base = dict(font=font, font_size=size, weight=weight, slant=slant, should_center=False, warn_missing_font=False)
    if chars:
        base["disable_ligatures"] = True
    if parts:
        assert not markup, "parts= uses t2c; with markup=True colour the spans in the markup instead"
        keys = dict(zip(parts, _key_colors(len(parts))))
        kw = dict(kw, t2c={sub: keys[name_] for name_, sub in parts.items()})
    t = cls(text, color=color, **base, **kw)
    c = t.get_center()[1]
    baseline = c + _K * (c - _svg_baseline(cls, font, size, weight, slant))
    t.baseline_frac = (baseline - t.get_bottom()[1]) / t.height if t.height > 0 else 0.0
    t.em_frac = (size * EM_PER_SIZE) / t.height if t.height > 0 else 1.0
    t.part = {}
    t.spec = dict(cls=cls, base=base, string=re.sub(r"<[^>]+>", "", text) if markup else text)
    info = dict(key=next(_text_keys), line=id(t), string=t.spec["string"], base=base, markup=markup, n=len(t.submobjects),
                em0=size * EM_PER_SIZE, hud=False)
    for i, g in enumerate(t.submobjects):
        g.kit_glyph = (info, i, max(g.width, g.height, 1e-6))
    if parts:
        for name_, key in keys.items():
            hits = [g for g in t if len(g.points) and g.get_fill_color().to_hex().upper() == key]
            assert hits, f"T(): no glyphs found for part {name_!r} = {parts[name_]!r}"
            t.part[name_] = VGroup(*hits)
        t.set_color(color)
    t.center()
    return t


def words(t) -> VGroup:
    """Split a single-line T() into one VGroup per word (ligatures stay intact), for word-by-word entrances.

    Each word knows its baseline, its em and its string, so ``row``, ``align_baseline`` and the lint treat it as text.
    """
    spec = t.spec
    assert spec["cls"] is Text, "words() works on plain T() text, not on markup"
    names = spec["string"].split()
    if spec["base"].get("disable_ligatures"):
        groups, cur = [], []
        for ch, g in zip(spec["string"], t):
            if ch.isspace():
                if cur:
                    groups.append(cur)
                    cur = []
            else:
                cur.append(g)
        if cur:
            groups.append(cur)
    else:
        groups, i = [], 0
        for w in names:
            key = (w, tuple(sorted((k, str(v)) for k, v in spec["base"].items())))
            if key not in _glyph_count_cache:
                _glyph_count_cache[key] = len(Text(w, **spec["base"]))
            n = _glyph_count_cache[key]
            groups.append(t.submobjects[i:i + n])
            i += n
        assert i == len(t.submobjects), f"words(): glyph count mismatch ({i} vs {len(t.submobjects)})"
    out, base, e = VGroup(), baseline_y(t), em(t)
    for name, glyphs in zip(names, groups):
        g = VGroup(*glyphs)
        if g.height > 0:
            g.baseline_frac, g.em_frac = (base - g.get_bottom()[1]) / g.height, e / g.height
        g.spec = dict(cls=Text, base=spec["base"], string=name)
        g.kit_line = id(t)                                   # words of one line may be closer than the lint's gap
        g.kit_backstroke = getattr(t, "kit_backstroke", False)
        out.add(g)
    return out


def baseline_y(m) -> float:
    """y of the text baseline. Mobjects without baseline information use their bottom edge."""
    if isinstance(m, LiveNumber):
        return float(m.anchor_point[1])
    return m.get_bottom()[1] + getattr(m, "baseline_frac", 0.0) * m.height


def em(m) -> float:
    """Current em of a T(), tex() or LiveNumber in scene units."""
    return m.em0 * m._pose()[1] if isinstance(m, LiveNumber) else m.em_frac * m.height


def align_baseline(m, ref, dy: float = 0.0):
    """Shift m vertically so that its baseline is dy above the baseline of ref (ref may be a y value)."""
    target = ref if isinstance(ref, (int, float)) else baseline_y(ref)
    return m.shift(UP * (target + dy - baseline_y(m)))


def put(m, x: float | None = None, y: float | None = None, edge=LEFT):
    """Place m by an edge and its baseline: ``edge`` (LEFT, RIGHT or ORIGIN for the centre) goes to x, the baseline to y."""
    dx = 0.0 if x is None else x - m.get_critical_point(edge)[0]
    dy = 0.0 if y is None else y - baseline_y(m)
    return m.shift([dx, dy, 0])


def row(*mobs, buff: float = th.GAP_S) -> VGroup:
    """Left to right on one shared baseline (VGroup.arrange(RIGHT) centres the bounding boxes instead)."""
    g = VGroup(*mobs)
    for prev, m in zip(mobs, mobs[1:]):
        m.next_to(prev, RIGHT, buff=buff)
        align_baseline(m, mobs[0])
    g.baseline_frac = (baseline_y(mobs[0]) - g.get_bottom()[1]) / g.height
    return g


def lines(*mobs, leading: float | None = None, align=LEFT) -> VGroup:
    """Stack lines so that consecutive baselines are exactly ``leading`` apart (bounding boxes are ignored).

    ``leading`` defaults to 1.3 em of the first line, rounded to whole grid steps (64 -> 1.2, 44 -> 0.8, 32 -> 0.6,
    24 -> 0.4, 18 -> 0.4).
    """
    if leading is None:
        leading = max(1, round(1.3 * em(mobs[0]) / th.GRID)) * th.GRID
    g = VGroup(*mobs)
    x = mobs[0].get_critical_point(align)[0]
    for i, m in enumerate(mobs[1:], start=1):
        m.shift(RIGHT * (x - m.get_critical_point(align)[0]))
        align_baseline(m, mobs[0], dy=-i * leading)
    g.baseline_frac = (baseline_y(mobs[0]) - g.get_bottom()[1]) / g.height
    return g


def snap_to_grid(m, grid: float = th.GRID):
    """Shift m (by less than half a grid step) so that its baseline sits on the baseline grid."""
    y = baseline_y(m)
    return m.shift(UP * (round(y / grid) * grid - y))


def backstroke(mob, width: float | None = None, color=th.BACKSTROKE):
    """A dark stroke BEHIND the fill, so that a label stays readable on art. Required for all text that sits on art."""
    if width is None:
        fs = _font_size_of(mob) or th.SCALE["body"]
        name = min(th.SCALE, key=lambda k: abs(th.SCALE[k] - fs))
        width = th.BACKSTROKE_WIDTH[name]
    mob.set_stroke(color, width, background=True)
    mob.kit_backstroke = True
    return mob


def underline(part, of=None, color=None, gap_em: float = 0.25, thickness_em: float = 0.055, taper: float = 0.07) -> VMobject:
    """A bar under a phrase, with softly tapered ends. ``part`` is a slice of the T() given as ``of``; the bar sits
    ``gap_em`` below the BASELINE of that text (just clear of the descenders), so bars under different phrases line
    up whether or not the phrase has a descender. Bring it in with ``sweep_in``."""
    e = em(of) if of is not None else part.height / 0.7
    y = (baseline_y(of) if of is not None else part.get_bottom()[1]) - gap_em * e - thickness_em * e / 2
    x0, x1, h = part.get_left()[0], part.get_right()[0], thickness_em * e
    u = np.linspace(0, 1, 33)
    prof = np.clip(np.minimum(u, 1 - u) / max(taper, 1e-6), 0, 1)
    prof = 0.18 + 0.82 * np.sin(prof * np.pi / 2)
    top = np.column_stack([x0 + (x1 - x0) * u, y + h / 2 * prof, 0 * u])
    bot = np.column_stack([x0 + (x1 - x0) * u[::-1], y - h / 2 * prof[::-1], 0 * u])
    bar = VMobject(stroke_width=0, fill_opacity=1, fill_color=color if color is not None else part.get_color())
    bar.layout_ignore = True                                 # a mark that belongs to its text: not "a shape that touches text"
    return bar.set_points_as_corners([*top, *bot, top[0]])


def marker(part, color, of=None, opacity: float = 0.28, slant_em: float = 0.16) -> VMobject:
    """A highlighter stroke behind a phrase: from a little under the baseline to a little over the x-height, from
    the phrase's left edge to its right edge, with slanted ends (a felt tip, not a selection box).

    ``of`` is the T() that holds the phrase (for its baseline and face); without it the bottom of the phrase is
    taken as the baseline, which is right only for a phrase without descenders. z_index -1: painted under the text.
    """
    e = em(of) if of is not None else part.height / 0.7
    base = baseline_y(of) if of is not None else part.get_bottom()[1]
    face = (getattr(of, "spec", None) or {}).get("base", {}).get("font", SANS) if of is not None else SANS
    lo, hi = base - 0.12 * e, base + (X_HEIGHT.get(face, 0.5) + 0.04) * e
    x0, x1, k = part.get_left()[0], part.get_right()[0], slant_em * e
    band = VMobject(stroke_width=0, fill_color=color, fill_opacity=opacity)
    band.set_points_as_corners([[x0, lo, 0], [x1 - k, lo, 0], [x1, hi, 0], [x0 + k, hi, 0], [x0, lo, 0]])
    band.set_z_index(-1)
    band.layout_ignore = True
    return band


def sweep_in(bar, **kw) -> Transform:
    """Animation: grow a bar from zero width at its left edge to full width (a true left-to-right sweep)."""
    start = bar.copy().stretch_to_fit_width(1e-3, about_edge=LEFT)
    target = bar.copy()
    bar.become(start)
    return Transform(bar, target, **kw)


# --------------------------------------------------------------------------- live number
class _Strut(VMobject):
    """An undrawable segment on the baseline of a LiveNumber. It is transformed with the number (shift, scale,
    Transform, pin_to_frame), so the number can read its own position and scale back from it."""

    fx_hidden = True
    layout_ignore = True

    def get_stroke_width(self, background: bool = False) -> float:
        return 0.0

    def get_fill_opacity(self) -> float:
        return 0.0


class LiveNumber(VGroup):
    """A number that counts without jitter. Digits sit in cells of one width; the prefix and the unit are separate parts.

    value, decimals   the number and its decimal places; ``commas`` adds thousands separators ("1,440")
    unit              for example "%": its own part, ``n.unit``, right after the digits
    prefix            for example "≈" or "about": its own part, ``n.prefix``, one word space before the digits
    reserve           the largest value the number will show; room for it is kept, so the prefix never moves
    anchor            "right": the right end of the digits stays put (the usual case); "left": the left end
    size, font        as in T(). ``n.digits`` is the group of digit glyphs.

    Position it with ``place(point)`` (the anchor on the baseline) or ``next_to`` / ``move_to`` at its final value.
    Drive it with ``follow(tracker)`` and animate the tracker (motion.count_to), or call ``set_value``.
    It can be shifted, scaled, faded, pinned to the frame and moved with ``.animate`` while it counts.
    """

    POOL = 16
    _cache: dict = {}

    def __init__(self, value: float = 0.0, decimals: int = 0, unit: str = "", prefix: str = "", size: float | str = "title",
                 color=th.INK, font: str | None = None, weight: str | None = None, commas: bool = True,
                 anchor: str = "right", reserve: float | None = None, unit_color=None, prefix_color=None, **kw):
        super().__init__(**kw)
        assert anchor in ("right", "left")
        name = size if isinstance(size, str) else None
        self.size = size_of(size)
        self.font = font or font_for(name or self.size)
        self.weight = weight or (MEDIUM if self.font == SANS else NORMAL)
        _verify_face(self.font)
        self.decimals, self.commas, self.anchor, self.reserve = decimals, commas, anchor, reserve
        self.unit_text, self.prefix_text = unit, prefix
        self.em0 = self.size * EM_PER_SIZE
        self.digit_adv = max(self._glyph(d)[1] for d in "0123456789")
        self.space_adv = self._advance(" ")

        def slot(c):
            return VMobject(fill_color=c, fill_opacity=1, stroke_width=0)

        self.strut = _Strut()
        length = 0.5 * self.em0
        self.strut.set_points_as_corners([[-length, 0, 0], [0, 0, 0]] if anchor == "right" else [[0, 0, 0], [length, 0, 0]])
        self.prefix = slot(prefix_color if prefix_color is not None else color)
        self.unit = slot(unit_color if unit_color is not None else color)
        self.digits = VGroup(*[slot(color) for _ in range(self.POOL)])
        self.add(self.strut, self.prefix, self.digits, self.unit)
        self.tracker: ValueTracker | None = None
        self._follower = None
        self.value = 0.0
        self.set_value(value)

    # ---- glyph metrics (cached per font, size and weight)
    def _text(self, s: str, **kw) -> Text:
        return Text(s, font=self.font, font_size=self.size, weight=self.weight, warn_missing_font=False, **kw)

    def _advance(self, s: str) -> float:
        key = (self.font, self.size, self.weight, "adv", s)
        if key not in self._cache:
            self._cache[key] = self._text(f"0{s}0").width - self._text("00").width
        return self._cache[key]

    def _glyph(self, s: str) -> tuple[np.ndarray, float]:
        """(outline points with the pen at x = 0 and the baseline at y = 0, advance) of a character or a short string."""
        key = (self.font, self.size, self.weight, "glyph", s)
        if key not in self._cache:
            raw = self._text(s, should_center=False)
            cx = raw.get_center()[0]
            lsb = ((cx + (raw.get_left()[0] - cx) / _K) - _START_X) * _K          # ink left edge minus pen position
            g = T(s, size=self.size, font=self.font, weight=self.weight)
            pts = np.vstack([m.points for m in g.family_members_with_points()])
            pts = pts - np.array([g.get_left()[0] - lsb, baseline_y(g), 0.0])
            self._cache[key] = (pts, self._advance(s))
        return self._cache[key]

    # ---- pose: where the anchor is and how large the number is now
    def _pose(self) -> tuple[np.ndarray, float]:
        p = self.strut.points
        a, b = p[0], p[-1]
        s = float(np.linalg.norm(b - a)) / (0.5 * self.em0)
        return (b if self.anchor == "right" else a).copy(), s

    @property
    def anchor_point(self) -> np.ndarray:
        return self._pose()[0]

    @property
    def font_size(self) -> float:
        return self.size * self._pose()[1]

    # ---- value
    def format(self, value: float) -> str:
        s = f"{abs(value):,.{self.decimals}f}" if self.commas else f"{abs(value):.{self.decimals}f}"
        return ("−" if value < 0 and s.strip("0.,") else "") + s

    def _cells(self, s: str) -> list[tuple[np.ndarray, float, float]]:
        out = []
        for ch in s:
            pts, own = self._glyph(ch)
            adv = self.digit_adv if ch.isdigit() else own
            out.append((pts, adv, (adv - own) / 2))
        return out

    def set_value(self, value: float):
        """Show ``value``. Safe inside an updater: the glyphs are a fixed pool that is rewritten in place."""
        anchor, s = self._pose()
        text = self.format(value)
        cells = self._cells(text)
        assert len(cells) <= self.POOL, f"LiveNumber: {text!r} has more than {self.POOL} characters"
        used = sum(adv for _, adv, _ in cells)
        field = max(used, 0.0 if self.reserve is None else sum(adv for _, adv, _ in self._cells(self.format(self.reserve))))
        left, right = (-field, 0.0) if self.anchor == "right" else (0.0, field)
        x = right - used
        for slot, (pts, adv, inset) in zip(self.digits, cells):
            slot.points = anchor + s * (pts + np.array([x + inset, 0.0, 0.0]))
            x += adv
        for slot in self.digits[len(cells):]:          # an unused slot keeps a null curve at the anchor: the family of
            slot.points = np.tile(anchor, (4, 1))      # the number must never change, or a running Transform breaks
        if self.unit_text:
            self.unit.points = anchor + s * (self._glyph(self.unit_text)[0] + np.array([right, 0.0, 0.0]))
        if self.prefix_text:
            pts, adv = self._glyph(self.prefix_text)
            self.prefix.points = anchor + s * (pts + np.array([left - self.space_adv - adv, 0.0, 0.0]))
        self.value, self.shown = value, text
        return self

    def suspend_updating(self, recursive: bool = True):
        """Not suspended: Manim suspends the updaters of an object for the whole run of an animation on it, and a
        number must go on counting while it fades in or is moved."""
        return self

    def place(self, point):
        """Put the anchor (on the baseline, at the right or left end of the digits) at ``point``."""
        return self.shift(np.array(point, dtype=float) - self._pose()[0])

    def follow(self, tracker: ValueTracker | None = None, fn=None):
        """Show ``fn(tracker.get_value())`` on every frame (``fn`` defaults to the identity). Returns self.

        With no tracker the number makes its own, ``self.tracker``. The number must be in the scene for this to run.
        """
        self.tracker = tracker if tracker is not None else ValueTracker(self.value)
        fn = fn or (lambda v: v)
        if self._follower is not None:
            self.remove_updater(self._follower)
        self._follower = lambda m: m.set_value(fn(m.tracker.get_value()))
        self.add_updater(self._follower)
        self.set_value(fn(self.tracker.get_value()))
        return self


# --------------------------------------------------------------------------- LaTeX without dvisvgm
BP_PER_TEXPT = 72 / 72.27
TEX_MAGNIFY = 4                               # pdftocairo rounds outlines to 1/64 bp, so draw them 4x larger
TEX_EM_BP = 10 * BP_PER_TEXPT * TEX_MAGNIFY   # 1 em of the 10pt LaTeX document, in SVG units (PostScript points)
TEX_PREAMBLE = {
    "pdflatex": r"""\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{xcolor}""",
    # New Computer Modern Book (text and math): matches SERIF
    "xelatex": r"""\usepackage{amsmath}
\usepackage{fontspec}
\usepackage{unicode-math}
\setmainfont{NewCM10-Book.otf}[ItalicFont=NewCM10-BookItalic.otf,BoldFont=NewCM10-Bold.otf,BoldItalicFont=NewCM10-BoldItalic.otf]
\setmathfont{NewCMMath-Book.otf}
\usepackage{graphicx}
\usepackage{xcolor}""",
}
TEX_ENGINE = "xelatex"
_PART = re.compile(r"⟦(\w+)\|(.*?)⟧", re.S)


def _run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    return p.returncode, p.stdout


def tex_svg(body: str, mode: str = "math", engine: str | None = None, preamble: str | None = None) -> tuple:
    """Compile a LaTeX fragment to SVG and return (svg_path, dims). Cached by content hash under BUILD/texcache.

    mode: "math" ($...$ text style), "display" (display style), "text" (a paragraph-mode hbox)
    dims: {"wd", "ht", "dp"} of the magnified TeX box in SVG units; the page is exactly this box, so the baseline is
          ``ht`` below the top edge of the SVG.
    """
    engine = engine or TEX_ENGINE
    preamble = TEX_PREAMBLE[engine] if preamble is None else preamble
    inner = {"math": f"${body}$", "display": rf"$\displaystyle {body}$", "text": body}[mode]
    src = "\n".join([
        r"\documentclass[border=0pt]{standalone}", preamble, r"\newsavebox{\tkbox}", r"\begin{document}",
        rf"\sbox{{\tkbox}}{{{inner}}}%",
        r"\typeout{TKDIMS wd=\the\wd\tkbox, ht=\the\ht\tkbox, dp=\the\dp\tkbox}%",
        rf"\scalebox{{{TEX_MAGNIFY}}}{{\usebox{{\tkbox}}}}%", r"\end{document}", ""])
    h = hashlib.sha256((engine + "\0" + src).encode()).hexdigest()[:16]
    TEX_CACHE.mkdir(parents=True, exist_ok=True)
    svg, dimfile = TEX_CACHE / f"{h}.svg", TEX_CACHE / f"{h}.dims"
    if not (svg.exists() and dimfile.exists()):                # .dims is written last: with it, the .svg is whole
        work = Path(tempfile.mkdtemp(prefix=f"{h}-", dir=TEX_CACHE))     # one private folder per process: parallel
        try:                                                              # renders never share a job name or a file
            (work / f"{h}.tex").write_text(src, encoding="utf-8")
            code, out = _run([engine, "-interaction=nonstopmode", "-halt-on-error", f"{h}.tex"], work)
            m = re.search(r"TKDIMS wd=([\d.]+)pt, ht=([\d.]+)pt, dp=([\d.]+)pt", out)
            if code != 0 or not m:
                errs = [ln for ln in out.splitlines() if ln.startswith("!") or ln.startswith("l.")]
                raise ValueError(f"{engine} failed for {body!r}: {' | '.join(errs[:6]) or out[-400:]}")
            # -noshrink -nocenter are REQUIRED: by default pdftocairo shrinks the drawing by a few percent to fit a
            # whole-point page and re-centres it, which changes the size of every formula by a different factor.
            code, out = _run(["pdftocairo", "-svg", "-noshrink", "-nocenter", f"{h}.pdf", f"{h}.svg"], work)
            if code != 0 or not (work / f"{h}.svg").exists():
                raise ValueError(f"pdftocairo failed for {h}.pdf: {out[-400:]}")
            (work / f"{h}.dims").write_text(" ".join(str(float(v) * BP_PER_TEXPT * TEX_MAGNIFY) for v in m.groups()))
            os.replace(work / f"{h}.svg", svg)
            os.replace(work / f"{h}.dims", dimfile)
        finally:
            shutil.rmtree(work, ignore_errors=True)
    wd, ht, dp = (float(v) for v in dimfile.read_text().split())
    return svg, {"wd": wd, "ht": ht, "dp": dp}


def _rule_to_fill(line: VMobject) -> VMobject:
    """TeX draws thin rules (fraction bars, radical bars) as stroked lines. Manim strokes do not scale with the
    mobject, so replace each one by a filled quadrilateral of the same thickness."""
    a, b = line.get_start(), line.get_end()
    d = b - a
    n = np.array([-d[1], d[0], 0.0])
    n = n / (np.linalg.norm(n) or 1.0) * (line.get_stroke_width() / 2)
    return Polygon(a + n, b + n, b - n, a - n, stroke_width=0, fill_opacity=1, fill_color=line.get_stroke_color())


def tex(body: str, size: float | str = "body", color=th.INK, mode: str = "math", engine: str | None = None,
        preamble: str | None = None) -> SVGMobject:
    r"""LaTeX as a filled SVGMobject at the same em as T(size=...), with ``.baseline_frac``, ``.em_frac`` and ``.part``.

    Mark colourable parts in the source with  ⟦name|latex⟧ , for example  tex(r"\frac{⟦num|a+b⟧}{⟦den|n⟧}").
    ``m.part["num"]`` is then the VGroup of those glyphs. The first compile of a formula takes about a second.
    """
    size = size_of(size)
    names: list[str] = []

    def mark(mo):
        names.append(mo.group(1))
        key = _key_colors(len(names))[-1][1:]
        cmd = r"\textcolor" if mode == "text" else r"\mathcolor"
        return rf"{cmd}[HTML]{{{key}}}{{{mo.group(2)}}}"

    svg, dims = tex_svg(_PART.sub(mark, body), mode=mode, engine=engine, preamble=preamble)
    with tempfile.TemporaryDirectory(prefix="kit-tex-") as private:      # SVGMobject writes a file beside the one it
        copy = Path(private) / svg.name                                   # reads: give it a private copy
        shutil.copyfile(svg, copy)
        m = SVGMobject(str(copy), should_center=False, height=None, use_svg_cache=False)
    for i, s in enumerate(list(m.submobjects)):
        if s.get_fill_opacity() == 0 and s.get_stroke_width() > 0 and len(s.points) == 4:
            m.submobjects[i] = _rule_to_fill(s)
    c = m.get_center()[1]                    # the SVG was flipped about the ink centre c: a point at height y is at 2c - y
    baseline = 2 * c - dims["ht"]
    m.baseline_frac = (baseline - m.get_bottom()[1]) / m.height
    m.em_frac = TEX_EM_BP / m.height
    m.part = {}
    keys = dict(zip(names, _key_colors(len(names))))

    def near(a: str, b: str) -> bool:
        return all(abs(int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) <= 2 for i in (1, 3, 5))

    for name, key in keys.items():
        hits = [g for g in m if near(g.get_fill_color().to_hex(), key)]
        assert hits, f"tex(): no glyphs found for part {name!r}"
        m.part.setdefault(name, VGroup()).add(*hits)
    m.set_fill(color, opacity=1).set_stroke(width=0)
    m.scale(size * EM_PER_SIZE / TEX_EM_BP)
    m.spec = dict(cls=SVGMobject, string=body)
    m.center()
    return m


# --------------------------------------------------------------------------- layout checks
def _is_text(m) -> bool:
    return (isinstance(m, (Text, MarkupText, LiveNumber)) or (isinstance(m, SVGMobject) and hasattr(m, "baseline_frac"))
            or hasattr(m, "kit_line"))


def _font_size_of(m) -> float | None:
    """Current font_size of a text mobject in scene units (after any scaling), or None if unknown."""
    if isinstance(m, LiveNumber):
        return m.font_size
    if hasattr(m, "em_frac"):
        return em(m) / EM_PER_SIZE
    if isinstance(m, (Text, MarkupText)):
        return float(m.font_size)
    return None


def _kind(m) -> str:
    return type(m).__name__


def _visible(m) -> bool:
    kind = _kind(m)
    if kind == "DotCloud":
        return m.get_fill_opacity() > 0.02 and bool((m.rgbas[:, 3] > 0.02).any())
    if kind in ("RasterLayer", "Trail"):
        return m.get_fill_opacity() > 0.02
    for s in m.family_members_with_points():
        if getattr(s, "fx_hidden", False):
            continue
        if s.get_fill_opacity() > 0.02 or (s.get_stroke_opacity() > 0.02 and s.get_stroke_width() > 0):
            return True
    return False


def _glyph_words(info: dict) -> list[int]:
    """The word index of every glyph of a T() (from its string and font; cached)."""
    key = info["key"]
    if key not in _word_maps:
        names, n, out = info["string"].split(), info["n"], None
        if not info["markup"] and not info["base"].get("disable_ligatures"):
            counts = []
            for w in names:
                k = (w, tuple(sorted((a, str(v)) for a, v in info["base"].items())))
                if k not in _glyph_count_cache:
                    _glyph_count_cache[k] = len(Text(w, **info["base"]))
                counts.append(_glyph_count_cache[k])
            if sum(counts) == n:
                out = [i for i, c in enumerate(counts) for _ in range(c)]
        if out is None:
            chars = [i for i, w in enumerate(names) for _ in w]
            out = chars if len(chars) == n else [min(int(j * len(names) / max(n, 1)), len(names) - 1) for j in range(n)]
        _word_maps[key] = out
    return _word_maps[key]


def _loose_text(glyphs: list) -> VGroup:
    """A stand-in text atom for loose glyphs of one T() (Manim breaks a text up when a part of it is removed or
    replaced): it has the words, the size, the box, the backstroke and the pinning of those glyphs."""
    info = glyphs[0].kit_glyph[0]
    wmap = _glyph_words(info)
    names = info["string"].split()
    present = sorted({wmap[g.kit_glyph[1]] for g in glyphs if g.kit_glyph[1] < len(wmap)})
    g = VGroup(*glyphs)
    scale = float(np.median([max(m.width, m.height, 1e-6) / m.kit_glyph[2] for m in glyphs]))
    g.em_frac = info["em0"] * scale / max(g.height, 1e-9)
    g.baseline_frac = 0.0
    g.spec = dict(cls=Text, base=info["base"], string=" ".join(names[i] for i in present if i < len(names)) or info["string"])
    g.kit_line = info["line"]
    g.kit_backstroke = any(m.get_stroke_width(background=True) > 0 and m.get_stroke_opacity(background=True) > 0.02 for m in glyphs)
    g.fx_pinned = any(getattr(m, "fx_pinned", False) for m in glyphs)
    g.hud = info.get("hud", False)
    g.kit_loose = True
    return g


def atoms(mobjects) -> list:
    """Flatten to the things a viewer reads as one object: each text block is one atom, each shape is one atom.

    Loose glyphs of a T() (what Manim leaves of a text when a part of it is removed or replaced) are gathered by
    their text into one text atom, so they are still counted as words and held to the text rules."""
    out, loose = [], {}

    def walk(m):
        if getattr(m, "layout_ignore", False):
            return
        if _is_text(m):
            if _visible(m):
                out.append(m)
            return
        tag = getattr(m, "kit_glyph", None)
        if tag is not None:
            if _visible(m):
                loose.setdefault(tag[0]["key"], []).append(m)
            return
        if isinstance(m, VMobject) and len(m.points) and _visible(m):
            out.append(m)
        for s in m.submobjects:
            walk(s)

    for m in mobjects:
        walk(m)
    return out + [_loose_text(gs) for gs in loose.values()]


def _outline_samples(m, step: float = 0.05) -> np.ndarray:
    """Points on the outline of a shape, about ``step`` apart (at least 6 on each curve), or the points of a cloud."""
    kind = _kind(m)
    if kind == "DotCloud":
        return m.points[m.rgbas[:, 3] > 0.02]
    if kind == "Trail":
        return m.points
    if kind in ("RasterLayer", "RadialGlow"):
        return np.zeros((0, 3))                                   # light and pictures: see the text-on-fill rule
    pts = []
    for s in m.family_members_with_points():
        p = s.points
        if len(p) < 4:
            continue
        q = p[: len(p) // 4 * 4].reshape(-1, 4, 3)
        length = np.linalg.norm(np.diff(q, axis=1), axis=2).sum(axis=1)
        for c, n in zip(q, np.maximum(6, np.ceil(length / step)).astype(int)):
            t = np.linspace(0, 1, n)[:, None]
            pts.append((1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3])
    return np.vstack(pts) if pts else np.zeros((0, 3))


def _inside_outline(m, point) -> bool:
    """Is ``point`` inside the outline of the shape ``m`` (even-odd rule on its sampled outline)?"""
    for s in m.family_members_with_points():
        if s.get_fill_opacity() <= 0.3 or len(s.points) < 4:
            continue
        poly = _outline_samples(s, 0.1)[:, :2]
        x, y = point[0], point[1]
        x0, y0, x1, y1 = poly[:, 0], poly[:, 1], np.roll(poly[:, 0], -1), np.roll(poly[:, 1], -1)
        with np.errstate(divide="ignore", invalid="ignore"):
            cross = ((y0 > y) != (y1 > y)) & (x < (x1 - x0) * (y - y0) / (y1 - y0) + x0)
        if int(cross.sum()) % 2 == 1:
            return True
    return False


def _light_under(s, box) -> float:
    """The strongest light (0..1) that a glow or a picture puts under a box (l, r, b, t) in its own coordinates."""
    kind, (l, r, b, t) = _kind(s), box
    if kind == "RadialGlow":
        c, hw, hh = s.get_center(), s.width / 2, s.height / 2
        x, y = np.clip(c[0], l, r), np.clip(c[1], b, t)                       # the point of the box nearest the centre
        d = np.hypot((x - c[0]) / max(hw, 1e-9), (y - c[1]) / max(hh, 1e-9))
        return float(s.get_fill_opacity() * max(1 - d, 0.0) ** getattr(s, "glow_power", th.GLOW_POWER))
    px = s.fx_pixels
    h, w = px.shape[:2]
    c, bw, bh = s.get_center(), s.width * s.fx_bleed, s.height * s.fx_bleed
    c0, c1 = int(np.clip((l - (c[0] - bw / 2)) / bw * w, 0, w)), int(np.clip((r - (c[0] - bw / 2)) / bw * w, 0, w))
    r0, r1 = int(np.clip(((c[1] + bh / 2) - t) / bh * h, 0, h)), int(np.clip(((c[1] + bh / 2) - b) / bh * h, 0, h))
    if c1 <= c0 or r1 <= r0:
        return 0.0
    step = max(1, (r1 - r0) // 24, (c1 - c0) // 24)
    return float(px[r0:r1:step, c0:c1:step, 3].max() / 255 * s.get_fill_opacity() * getattr(s, "fx_gain", 1.0))


def _luma(color) -> float:
    r, g, b = np.asarray(ManimColor(color).to_rgb(), dtype=float)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _off_palette() -> set:
    """Hex values that must not be seen: Manim's stock colours that the theme does not have, pure white, black."""
    import manim.utils.color.manim_colors as stock

    theme = {c.to_hex().upper() for c in th.PALETTE.values()}
    names = {v.to_hex().upper() for n, v in vars(stock).items() if n.isupper() and isinstance(v, ManimColor)}
    return (names - theme) | {th.CORE.to_hex().upper(), th.VOID.to_hex().upper()}


def _colour_faults(m, bad: set) -> list[str]:
    if _kind(m) in ("DotCloud", "Trail", "RasterLayer", "RadialGlow"):
        return []
    found = []
    for s in m.family_members_with_points():
        if getattr(s, "fx_hidden", False):
            continue
        if s.get_fill_opacity() > 0.02 and s.get_fill_color().to_hex().upper() in bad:
            found.append(s.get_fill_color().to_hex().upper())
        if s.get_stroke_width() > 0 and s.get_stroke_opacity() > 0.02 and s.get_stroke_color().to_hex().upper() in bad:
            found.append(s.get_stroke_color().to_hex().upper())
    return sorted(set(found))


def _raw_string(m) -> str:
    """The words of a Text or MarkupText that was not built with T() (Manim keeps them in ``original_text``)."""
    return re.sub(r"<[^>]+>", " ", str(getattr(m, "original_text", None) or getattr(m, "text", "") or "")).strip()


def describe(m) -> str:
    """A short name for a mobject in a lint message."""
    if isinstance(m, LiveNumber):
        return f'number "{m.prefix_text + " " if m.prefix_text else ""}{m.shown}{m.unit_text}"'
    spec = getattr(m, "spec", None)
    if spec is not None:
        return f'"{spec["string"][:40]}"'
    if isinstance(m, (Text, MarkupText)):
        return f'Text "{_raw_string(m)[:40]}"'
    c = m.get_center()
    return f"{_kind(m)} at ({c[0]:.1f}, {c[1]:.1f})"


def _words_in(items) -> int:
    n = 0
    for m in items:
        if not _is_text(m) or getattr(m, "hud", False):
            continue
        if isinstance(m, LiveNumber):
            n += 1 + len(m.prefix_text.split())
        elif getattr(m, "spec", None) and m.spec["cls"] is not SVGMobject:
            n += len(m.spec["string"].split())
        elif isinstance(m, (Text, MarkupText)) and _raw_string(m):
            n += len(_raw_string(m).split())
        else:
            n += 1
    return n


def word_count(mobjects) -> int:
    """Words in these mobjects: the visible text that is not HUD (the illustration tag and citations do not count)."""
    return _words_in(atoms(mobjects))


def check_layout(mobjects, frame=None, safe=(th.SAFE_X, th.SAFE_Y), gap: float = th.GAP_XS, min_size: float = th.SCALE["fine"],
                 max_words: int = th.MAX_WORDS) -> list[dict]:
    """Layout lint for the things now on screen. Returns a list of issues; an empty list means the frame passes.

    Everything is measured ON SCREEN (``frame`` is the camera frame), so the rules hold while the camera is pushed
    in. Things that are wholly outside the picture are not looked at.
      safe-area    every visible atom lies inside |x| <= 6.4, |y| <= 3.4. Exempt: ``m.bleed_ok = True``; glows and
                   raster pictures; and, while the camera is away from its rest framing, shapes of the world (they
                   run off the picture by design; text and pinned objects are still held to the safe area)
      text-text    two text blocks are at least ``gap`` apart (the words of one line from ``words()`` excepted)
      text-shape   no outline point of a shape (sampled every 0.05) or point of a DotCloud lies within ``gap`` of a
                   text block, unless the text has a backstroke (``backstroke(t)``): the one allowed way onto art
      text-on-fill a text without a backstroke lies on light: a RadialGlow or a picture (glow_sprite, bake, soft_band)
                   that is brighter than 12% under it, or inside a bright filled shape (fill opacity above 0.3)
      text-size    text is not smaller than 24 on screen; 18 is for the HUD (tag, citation) only
      type-scale   every font size is one of 64 / 44 / 32 / 24 / 18 (in the world or on screen)
      text-face    a Text or MarkupText that was not built with T() (it has the wrong face and no baseline)
      colour       a stroke or fill in a Manim stock colour that the theme does not have (Circle() is Manim red,
                   Line() and Dot() are white), or pure white or black
      word-count   at most 12 words on screen (HUD excepted)
    Set ``m.layout_ignore = True`` to skip a mobject and everything in it.
    """
    if frame is None:
        centre, zoom = np.zeros(3), 1.0
    else:
        centre, zoom = frame.get_center(), frame.width / config.frame_width
    away = abs(zoom - 1) > 1e-6 or float(np.abs(centre[:2]).max()) > 1e-6

    def view(m):                                   # a pinned object is in screen coordinates already
        return (np.zeros(3), 1.0) if getattr(m, "fx_pinned", False) else (centre, zoom)

    def box(m, pad: float = 0.0):
        c, z = view(m)
        l, r = (m.get_left()[0] - c[0]) / z, (m.get_right()[0] - c[0]) / z
        b, t = (m.get_bottom()[1] - c[1]) / z, (m.get_top()[1] - c[1]) / z
        return l - pad, r + pad, b - pad, t + pad

    def to_world(s, bx):                           # a screen box -> the coordinates of ``s`` (world or screen)
        c, z = view(s)
        return bx[0] * z + c[0], bx[1] * z + c[0], bx[2] * z + c[1], bx[3] * z + c[1]

    def in_picture(m) -> bool:
        l, r, b, t = box(m)
        return r > -th.FRAME_W / 2 and l < th.FRAME_W / 2 and t > -th.FRAME_H / 2 and b < th.FRAME_H / 2

    items = [m for m in atoms(mobjects) if in_picture(m)]
    issues: list[dict] = []
    sx, sy = safe
    scale_sizes = np.array(sorted(th.SCALE.values()), dtype=float)
    bad = _off_palette()
    for m in items:
        l, r, b, t = box(m)
        exempt = (getattr(m, "bleed_ok", False) or _kind(m) in ("RasterLayer", "RadialGlow")
                  or (away and not _is_text(m) and not getattr(m, "fx_pinned", False)))
        if not exempt and (l < -sx - 1e-6 or r > sx + 1e-6 or b < -sy - 1e-6 or t > sy + 1e-6):
            over = max(-sx - l, r - sx, -sy - b, t - sy)
            issues.append(dict(rule="safe-area", a=m, b=None, amount=over, msg=f"{describe(m)} leaves the safe area by {over:.2f}"))
        faults = _colour_faults(m, bad)
        if faults:
            issues.append(dict(rule="colour", a=m, b=None, amount=0.0,
                               msg=f"{describe(m)} has {', '.join(faults)}, which is not a colour of the theme (name one from kit.theme)"))
        if not _is_text(m):
            continue
        if isinstance(m, (Text, MarkupText)) and not hasattr(m, "spec"):
            issues.append(dict(rule="text-face", a=m, b=None, amount=0.0, msg=f"{describe(m)} was not built with T()"))
        fs = _font_size_of(m)
        if fs is None:
            continue
        on_screen = fs / view(m)[1]
        limit = min_size if getattr(m, "hud", False) else th.SCALE["label"]
        if on_screen < limit * 0.97:
            issues.append(dict(rule="text-size", a=m, b=None, amount=limit - on_screen,
                               msg=f"{describe(m)} is font size {on_screen:.1f} on screen, below {limit:g}"))
        elif min(np.abs(scale_sizes - fs).min(), np.abs(scale_sizes - on_screen).min()) > 0.03 * fs:
            issues.append(dict(rule="type-scale", a=m, b=None, amount=0.0,
                               msg=f"{describe(m)} is font size {fs:.1f}, not on the type scale {sorted(th.SCALE.values())}"))
    texts = [m for m in items if _is_text(m)]
    shapes = [m for m in items if not _is_text(m)]
    for i, a in enumerate(texts):
        al, ar, ab, at = box(a, gap / 2)
        for b_ in texts[i + 1:]:
            if getattr(a, "kit_line", a) == getattr(b_, "kit_line", b_):
                continue
            bl, br, bb, bt = box(b_, gap / 2)
            ox, oy = min(ar, br) - max(al, bl), min(at, bt) - max(ab, bb)
            if ox > 1e-6 and oy > 1e-6:
                issues.append(dict(rule="text-text", a=a, b=b_, amount=min(ox, oy),
                                   msg=f"{describe(a)} and {describe(b_)} are closer than {gap} (overlap {min(ox, oy):.2f})"))
        if getattr(a, "kit_backstroke", False):
            continue
        al, ar, ab, at = box(a, gap)
        mid = np.array([(al + ar) / 2, (ab + at) / 2, 0.0])
        for s in shapes:
            sl, sr, sb, st = box(s)
            if sr < al or sl > ar or st < ab or sb > at:
                continue
            kind = _kind(s)
            if kind in ("RasterLayer", "RadialGlow"):
                light = _light_under(s, to_world(s, (al + gap, ar - gap, ab + gap, at - gap)))
                if light > 0.12:
                    issues.append(dict(rule="text-on-fill", a=a, b=s, amount=light,
                                       msg=f"{describe(a)} lies on light ({light:.0%} under it from {describe(s)}) and has no backstroke"))
                continue
            p = _outline_samples(s)
            if len(p):
                c, z = view(s)
                px, py = (p[:, 0] - c[0]) / z, (p[:, 1] - c[1]) / z
                if np.any((px > al) & (px < ar) & (py > ab) & (py < at)):
                    issues.append(dict(rule="text-shape", a=a, b=s, amount=gap,
                                       msg=f"{describe(a)} is touched by {describe(s)} and has no backstroke"))
                    continue
            if kind not in ("DotCloud", "Trail") and isinstance(s, VMobject):
                lit = [q for q in s.family_members_with_points() if q.get_fill_opacity() > 0.3 and _luma(q.get_fill_color()) > 0.15]
                c, z = view(s)
                if lit and _inside_outline(s, mid * z + c):
                    issues.append(dict(rule="text-on-fill", a=a, b=s, amount=0.0,
                                       msg=f"{describe(a)} lies inside the filled {describe(s)} and has no backstroke"))
    n = _words_in(items)
    if n > max_words:
        issues.append(dict(rule="word-count", a=None, b=None, amount=n - max_words, msg=f"{n} words on screen (at most {max_words})"))
    return issues


def layout_overlay(issues, frame=None, safe=(th.SAFE_X, th.SAFE_Y), names: bool = True) -> VGroup:
    """The safe-area frame (item 0) plus, for every issue, a box around each offending mobject and the rule's name."""
    centre, zoom = (np.zeros(3), 1.0) if frame is None else (frame.get_center(), frame.width / config.frame_width)
    g = VGroup(Rectangle(width=2 * safe[0] * zoom, height=2 * safe[1] * zoom, stroke_color=th.LINT_SAFE,
                         stroke_width=th.W_HAIR * zoom, stroke_opacity=0.8).move_to(centre))
    for it in issues:
        boxes = VGroup()
        for m in (it["a"], it["b"]):
            if m is not None:
                k = zoom if getattr(m, "fx_pinned", False) else 1.0       # a pinned object: from the screen to the world
                at = m.get_center() * k + centre if k != 1.0 or getattr(m, "fx_pinned", False) else m.get_center()
                pad = 0.05 * zoom
                boxes.add(Rectangle(width=m.width * k + 2 * pad, height=m.height * k + 2 * pad, stroke_color=th.LINT_BAD,
                                    stroke_width=th.W_LINE * zoom).move_to(at))
        if names and len(boxes):
            tag = T(it["rule"], "fine", th.LINT_BAD).scale(zoom)
            boxes.add(tag.next_to(boxes, UP, buff=0.06 * zoom, aligned_edge=LEFT))
        g.add(boxes)
    g.layout_ignore = True
    return g


def mark_hud(t):
    """Mark a text as HUD (the tag, a citation): the word count leaves it out, also when Manim breaks it up."""
    t.hud = True
    for g in t.family_members_with_points():
        tag = getattr(g, "kit_glyph", None)
        if tag is not None:
            tag[0]["hud"] = True
    return t


def lint(scene, label: str = "", quiet: bool = False, **kw) -> list[dict]:
    """Check the mobjects now on screen and print one ``KIT-LINT`` line per issue (scene, time, label, rule, message)."""
    frame = getattr(scene.camera, "frame", None)
    issues = check_layout(scene.mobjects, frame=frame, **kw)
    t = getattr(scene.renderer, "time", 0.0)
    if not quiet:
        for it in issues:
            print(f"KIT-LINT {type(scene).__name__} t={t:.2f}s {label}: {it['rule']}: {it['msg']}", flush=True)
    return issues


__all__ = ["SERIF", "SANS", "MEDIUM", "register_fonts", "T", "words", "baseline_y", "em", "align_baseline", "put", "row",
           "lines", "snap_to_grid", "backstroke", "underline", "marker", "sweep_in", "LiveNumber", "tex", "tex_svg",
           "check_layout", "layout_overlay", "atoms", "word_count", "describe", "size_of", "font_for"]
