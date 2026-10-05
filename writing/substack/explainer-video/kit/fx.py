"""Light, points and pictures for Manim Community 0.21 (Cairo): the camera and the objects it knows how to draw.

    FxCamera            the scene camera: radial-gradient glow, DotCloud, Trail, RasterLayer, clip, blend, ambient
                        offset, and objects pinned to the screen
    film, film_time, idle_gain   the one clock of all idle motion: film time, set for every frame by Narrated
    DotCloud            thousands of points as ONE object; per-point colour, opacity, radius, glow and id; regrouping
    Trail               a ribbon whose width and opacity change along its length (the tail of a runner)
    RasterLayer, bake   a picture blitted by Cairo; bake() renders complicated static art once
    glow_sprite, RadialGlow, soft_band     soft light
    install_background  the near-black dithered vignette (zero cost per frame)
    set_clip, set_blend, smooth_closed, blob_points, field_points, soft_field, sunflower_points, cluster_points,
    match_points

Everything is in scene units, so one scene gives the same picture at every resolution; pixel sizes
(sprites, the background) are derived from ``config.pixel_height`` when they are made.
All code here is original. It depends on internals of Manim Community 0.21.0: keep the version pinned.
"""

from __future__ import annotations

import copy
from typing import Sequence

import cairo
import numpy as np
from manim import Animation, Circle, ManimColor, MovingCamera, VMobject, color_to_rgb, config, linear

from . import theme as th

TAU = 2 * np.pi


def px_per_unit() -> float:
    """Pixels per scene unit of the current render (135 at 1080p)."""
    return config.pixel_height / config.frame_height


def _rgb(color) -> np.ndarray:
    return np.array(color_to_rgb(ManimColor(color)), dtype=float)


# --------------------------------------------------------------------------- the film clock
class _Film:
    """The one clock of idle motion (drift, ambient, twinkle, a runner that runs by itself).

    t        film time in seconds of the frame that is painted now: the start of the scene in the film (the
             durations of the scenes before it) plus the scene time. Narrated sets it for every frame.
    gain     a factor on every idle amplitude: 1 = full, 0 = everything at its rest value (Narrated.rest_frames)
    driven   True while a Narrated scene sets ``t``. Outside one, each object counts its own dt, as before.

    Idle motion is a function of ``t`` alone. So it loses no frame at a play boundary, draft and review show the
    same picture at the same time, and scene N+1 continues the motion of scene N when it builds the same objects
    (the same seed, amplitude and period, and the same point ids).
    """

    t, gain, driven = 0.0, 1.0, False


film = _Film()


def film_time() -> float:
    """Film time in seconds of the frame that is painted now (0 outside a Narrated scene)."""
    return film.t


def idle_gain() -> float:
    """The factor on idle amplitudes now (1, unless the scene eases its idle motion to rest at its two ends)."""
    return film.gain


def _hash01(seed: int, ids, k: int) -> np.ndarray:
    """(len(ids), k) numbers in [0, 1) that depend only on the seed, the id and the column (a splitmix64 mix).

    The drift of a point is made from these, so it depends on the point's id and not on its place in the array."""
    with np.errstate(over="ignore"):
        x = (np.asarray(ids).astype(np.uint64)[:, None] * np.uint64(0x9E3779B97F4A7C15)
             + np.uint64(int(seed) & 0xFFFFFFFF) * np.uint64(0xD1B54A32D192ED03)
             + np.arange(1, k + 1, dtype=np.uint64)[None, :] * np.uint64(0x8CB92BA72F3D8DD7))
        x ^= x >> np.uint64(30)
        x *= np.uint64(0xBF58476D1CE4E5B9)
        x ^= x >> np.uint64(27)
        x *= np.uint64(0x94D049BB133111EB)
        x ^= x >> np.uint64(31)
    return (x >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def _no_drift(n: int) -> dict:
    """Drift arrays for n points that do not move (a part without drift inside DotCloud.join)."""
    return dict(amp=np.zeros(n), w=np.zeros((n, 2)), ph=np.zeros((n, 2)), tw=np.zeros(n), twp=np.zeros(n), t=0.0)


# --------------------------------------------------------------------------- glow
def glow_rgba(px: int, color=th.FOCUS, power: float = th.GLOW_POWER, peak: float = th.GLOW_PEAK, seed: int = 3,
              rim: float = 1.0) -> np.ndarray:
    """A square PREMULTIPLIED uint8 RGBA picture of a radial glow: alpha = peak * (1 - r) ** power, exactly 0 at the rim.

    ``rim`` is the radius of the glow as a share of the half-width of the picture. Every channel is dithered before
    it is rounded to 8 bits (one threshold per pixel for all four, so the grain is neutral and the colour never
    exceeds the alpha). A large faint glow then shows no rings, if it is drawn pixel for pixel.
    """
    c = (np.arange(px) + 0.5) / px * 2 - 1                                   # pixel centres
    a = peak * np.clip(1 - np.hypot(c[None, :], c[:, None]) / rim, 0, 1) ** power * 255
    u = np.random.default_rng(seed).random((px, px))                         # stochastic rounding = dither
    out = np.empty((px, px, 4), dtype=np.uint8)
    out[..., :3] = np.floor(a[..., None] * _rgb(color)[None, None, :] + u[..., None])
    out[..., 3] = np.floor(a + u)
    out[a <= 0] = 0
    return out


def glow_sprite(radius: float = 0.6, color=th.FOCUS, power: float = th.GLOW_POWER, peak: float = th.GLOW_PEAK) -> "RasterLayer":
    """A soft glow of ``radius`` scene units as one sprite (the cheapest and smoothest glow). Put a small core on top.

    Its bounding box is exactly 2 x radius at every render size. The picture has one pixel per screen pixel of this
    render and is painted on whole pixels, so its dither survives (a resampled picture loses it and shows faint
    rings on a flat ground). Under a camera zoom it is resampled like any picture.
    """
    ppu = px_per_unit()
    want = int(np.ceil(2 * radius * ppu)) + 2
    px = int(np.clip(want, 48, 1024))
    bleed = px / (2 * radius * ppu) if px == want else 1.0
    layer = RasterLayer(glow_rgba(px, color, power, peak, rim=1 / bleed), height=2 * radius, premultiplied=True)
    layer.fx_bleed, layer.fx_snap = bleed, px == want
    return layer


class RadialGlow(Circle):
    """A vector glow: a circle that ``FxCamera`` fills with a dithered radial gradient (centre colour to transparent).

    Unlike a sprite it follows ``set_color``, ``Transform`` and ``stretch``. A small one costs a millisecond or two;
    one with a radius above 1 costs ten times a sprite of that size, so use ``glow_sprite`` for a large halo.
    """

    def __init__(self, radius: float = 0.6, color=th.FOCUS, peak: float = th.GLOW_PEAK, power: float = th.GLOW_POWER, **kw):
        super().__init__(radius=radius, stroke_width=0, fill_color=color, fill_opacity=peak, **kw)
        self.glow_power = power


def soft_band(width: float, height: float, color=th.INK, peak: float = 0.18, edge: float = 0.3, axis: int = 1) -> "RasterLayer":
    """A band of light with soft edges, as one picture: a spread, a range, the room between two lines.

    The opacity is ``peak`` in the middle and falls smoothly to zero over the share ``edge`` of the size at the two
    edges across ``axis`` (1: the top and bottom edges are soft; 0: the left and right ones). It is dithered. It
    follows ``stretch`` and ``stretch_to_fit_height``, so a spread can grow and shrink; ``set_opacity`` fades it.
    """
    ppu = px_per_unit()
    w, h = max(int(round(width * ppu)), 2), max(int(round(height * ppu)), 2)
    u = (np.arange(h if axis == 1 else w) + 0.5) / (h if axis == 1 else w)
    prof = np.clip(np.minimum(u, 1 - u) / max(edge, 1e-6), 0, 1)
    prof = prof * prof * (3 - 2 * prof)
    a = peak * 255 * (np.tile(prof[:, None], (1, w)) if axis == 1 else np.tile(prof[None, :], (h, 1)))
    d = np.random.default_rng(5).random((h, w))
    out = np.empty((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.floor(a[..., None] * _rgb(color)[None, None, :] + d[..., None])
    out[..., 3] = np.floor(a + d)
    out[a <= 0] = 0
    layer = RasterLayer(out, height=height, premultiplied=True)
    return layer.stretch_to_fit_width(width)


# --------------------------------------------------------------------------- raster pictures
class RasterLayer(VMobject):
    """A raster picture (numpy RGBA uint8) blitted by Cairo. A fast stand-in for ImageMobject (which costs 100x more).

    It keeps z-order, follows shift / scale / move_to and camera moves, fades with FadeIn / FadeOut / set_opacity
    (the fill opacity is the layer alpha) and obeys set_clip and set_blend. It cannot rotate.
    ``height`` is in scene units. ``premultiplied`` says how the colour channels of ``rgba`` are stored.
    """

    def __init__(self, rgba: np.ndarray, height: float = th.FRAME_H, smooth: bool = True, premultiplied: bool = False, **kw):
        super().__init__(**kw)
        self.set_image(rgba, premultiplied)
        h, w = rgba.shape[:2]
        hw, hh = height * w / h / 2, height / 2
        self.set_points_as_corners([[-hw, hh, 0], [hw, hh, 0], [hw, -hh, 0], [-hw, -hh, 0], [-hw, hh, 0]])
        self.set_stroke(width=0).set_fill(th.VOID, opacity=1)
        self.fx_smooth = smooth
        self.fx_snap = False                 # True: painted on whole pixels when it is 1:1 on screen (keeps its dither)
        self.fx_bleed = 1.0                  # the picture is this much larger than the bounding box (a transparent rim)
        self.fx_gain = 1.0

    def set_image(self, rgba: np.ndarray, premultiplied: bool = False):
        if premultiplied:
            pre = np.ascontiguousarray(rgba, dtype=np.uint8).copy()
        else:
            a = rgba[..., 3:4].astype(np.uint16)
            pre = np.empty(rgba.shape, dtype=np.uint8)
            pre[..., :3] = (rgba[..., :3].astype(np.uint16) * a + 127) // 255
            pre[..., 3] = rgba[..., 3]
        self.fx_pixels = np.ascontiguousarray(pre)
        self.fx_surface = None                                   # rebuilt lazily by the camera
        return self

    def __deepcopy__(self, memo):
        new = self.__class__.__new__(self.__class__)
        memo[id(self)] = new
        for k, v in self.__dict__.items():                       # a Cairo surface cannot be copied; the pixels are shared
            setattr(new, k, None if k == "fx_surface" else v if k == "fx_pixels" else copy.deepcopy(v, memo))
        return new


def bake(scene, mobjects) -> RasterLayer:
    """Render ``mobjects`` once, as the camera sees them now, and return the picture as a RasterLayer in the same place.

    Use it for complicated static art (many faint paths, a dense texture): after baking, the art costs one blit per
    frame. The picture has the resolution of the render, so do not zoom far into it.
    """
    cam = scene.camera
    keep_bg, keep_px = cam.background, cam.pixel_array.copy()
    cam.background = np.zeros_like(keep_bg)
    cam.reset()
    cam.capture_mobjects(list(mobjects))
    out = cam.pixel_array.copy()                                 # Cairo wrote premultiplied values
    cam.background = keep_bg
    cam.set_pixel_array(keep_px)
    layer = RasterLayer(out, height=cam.frame_height, premultiplied=True)
    return layer.move_to(cam.frame_center)


# --------------------------------------------------------------------------- point layouts
def _lattice(m: int, width: float, height: float, rng, jitter: float) -> np.ndarray:
    """At least ``m`` points of a jittered staggered lattice in a width x height box about the origin."""
    cols = int(np.ceil(np.sqrt(m * width / height * 2 / np.sqrt(3))))
    rows = int(np.ceil(m / cols))
    while rows * cols < m:
        rows += 1
    c, r = np.meshgrid(np.arange(cols), np.arange(rows))
    x = (c + 0.5 + 0.5 * (r % 2)) / (cols + 0.5) - 0.5
    y = (r + 0.5) / rows - 0.5
    pts = np.column_stack([x.ravel() * width, y.ravel() * height])
    return pts + rng.uniform(-jitter, jitter, pts.shape) * [width / cols, height / rows]


def field_points(n: int, width: float, height: float, seed: int = 0, jitter: float = 0.32, centre=(0.0, 0.0)) -> np.ndarray:
    """``n`` points in a loose field: a jittered staggered lattice, so there are no rows to read and no clumps.

    The field fills a ``width`` x ``height`` box about ``centre``; ``jitter`` is the random offset of a point as a
    share of the lattice pitch (0 = a regular lattice). The box has a hard edge: for a field that reads as a cloud
    and not as a box of dots, use ``soft_field``.
    """
    rng = np.random.default_rng(seed)
    pts = _lattice(n, width, height, rng, jitter)
    keep = np.sort(rng.permutation(len(pts))[:n])
    return np.column_stack([pts[keep] + np.array(centre)[:2], np.zeros(n)])


def _inside(xy: np.ndarray, poly: np.ndarray) -> np.ndarray:
    """Which of the points ``xy`` (n, 2) lie inside the closed polygon ``poly`` (m, 2): even-odd rule."""
    x, y = xy[:, 0][:, None], xy[:, 1][:, None]
    x0, y0 = poly[:, 0][None, :], poly[:, 1][None, :]
    x1, y1 = np.roll(poly[:, 0], -1)[None, :], np.roll(poly[:, 1], -1)[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        cross = ((y0 > y) != (y1 > y)) & (x < (x1 - x0) * (y - y0) / (y1 - y0) + x0)
    return cross.sum(axis=1) % 2 == 1


def soft_field(n: int, width: float = 0.0, height: float = 0.0, seed: int = 0, centre=(0.0, 0.0), within=None, rim: float = 0.16,
               floor: float = 0.3, rough: float = 0.07, jitter: float = 0.4) -> tuple[np.ndarray, np.ndarray]:
    """``n`` points of a loose field inside a soft organic outline. Returns (points, fade).

    within   the outline: a closed VMobject (``smooth_closed(blob_points(...))``, ``hull_blob(...)``, a Circle). With
             None the outline is a wavy ellipse of ``width`` x ``height`` about ``centre``; ``rough`` is the size
             of its waves and ``seed`` chooses them
    fade     each point's share of its full opacity: 1 inside, falling to ``floor`` over the outer share ``rim``
             of the field. Use it as ``DotCloud(points, opacity=0.9 * fade, ...)``: the field then has no edge.
    Exactly ``n`` points come back: the ``n`` that lie deepest inside, in lattice order (no rows to read).
    """
    rng = np.random.default_rng(seed)
    if within is None:
        c0, (hw, hh) = np.array(centre, dtype=float)[:2], (width / 2, height / 2)
        f1, f2 = rng.uniform(0, TAU, 2)
    else:
        poly = np.array([within.point_from_proportion(a) for a in np.linspace(0, 1, 240, endpoint=False)])[:, :2]
        c0 = (poly.min(axis=0) + poly.max(axis=0)) / 2
        hw, hh = (poly.max(axis=0) - poly.min(axis=0)) / 2
    m = int(1.7 * n) + 8
    for _ in range(12):
        xy = _lattice(m, 2 * hw, 2 * hh, np.random.default_rng(seed), jitter) + c0
        if within is None:
            d = (xy - c0) / [hw, hh]
            ang = np.arctan2(d[:, 1], d[:, 0])
            score = np.hypot(d[:, 0], d[:, 1]) / (1 + rough * np.sin(3 * ang + f1) + 0.7 * rough * np.sin(5 * ang + f2)) * (1 + 1.7 * rough)
        else:
            near = np.sqrt(((xy[:, None, :] - poly[None, :, :]) ** 2).sum(-1).min(axis=1))
            score = np.where(_inside(xy, poly), 1 - near / max(near.max(), 1e-9), 2.0)
        if int((score <= 1).sum()) >= n:
            break
        m = int(m * 1.3)
    keep = np.sort(np.argsort(score, kind="stable")[:n])
    s = score[keep] / max(score[keep].max(), 1e-9)
    fade = np.clip((1 - s) / max(rim, 1e-6), floor, 1.0)
    return np.column_stack([xy[keep], np.zeros(len(keep))]), fade


def sunflower_points(n: int, radius: float = 1.0, centre=(0.0, 0.0), turn: float = 0.0, jitter: float = 0.0, seed: int = 0) -> np.ndarray:
    """``n`` points that fill a disc evenly (golden-angle spiral). Point 0 is at the centre.

    A large exact spiral shows spiral arms (moiré) on screen: ``jitter`` 0.3 moves every point by up to 0.3 of the
    point spacing in a seeded random direction, which hides the arms and keeps the disc even.
    """
    k = np.arange(n)
    r = radius * np.sqrt((k + 0.5) / max(n, 1))
    a = turn + k * np.pi * (3 - np.sqrt(5))
    pts = np.column_stack([centre[0] + r * np.cos(a), centre[1] + r * np.sin(a), np.zeros(n)])
    if jitter > 0 and n > 1:
        rng = np.random.default_rng(seed)
        step = radius * np.sqrt(np.pi / n)                       # the mean spacing of the points
        ang, rad = rng.uniform(0, TAU, n), jitter * step * np.sqrt(rng.random(n))
        pts[:, 0] += rad * np.cos(ang)
        pts[:, 1] += rad * np.sin(ang)
    return pts


def cluster_points(sizes: Sequence[int], centres, pitch: float = 0.11, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Discs of points, one per cluster, all with the same point spacing ``pitch``. Returns (points, labels)."""
    rng = np.random.default_rng(seed)
    pts, labels = [], []
    for k, (m, c) in enumerate(zip(sizes, centres)):
        pts.append(sunflower_points(m, pitch * np.sqrt(m) * 0.56, c, turn=rng.uniform(0, TAU)))
        labels.append(np.full(m, k))
    return np.vstack(pts), np.concatenate(labels)


def match_points(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Reorder ``dst`` so that point i of ``src`` travels to ``result[i]`` with the least total squared distance.

    A regrouping then reads as one flow, not as a scramble. Exact (Hungarian method); fine up to a few thousand points.
    """
    from scipy.optimize import linear_sum_assignment

    cost = ((src[:, None, :2] - dst[None, :, :2]) ** 2).sum(-1)
    rows, cols = linear_sum_assignment(cost)
    out = np.empty_like(dst)
    out[rows] = dst[cols]
    return out


def nearest_labels(points: np.ndarray, centres, sizes: Sequence[int]) -> np.ndarray:
    """Give every point a cluster label so that cluster k gets exactly ``sizes[k]`` points and points go to a near centre."""
    slots = np.vstack([np.repeat(np.array(c, dtype=float)[None, :2], m, axis=0) for c, m in zip(centres, sizes)])
    owner = np.concatenate([np.full(m, k) for k, m in enumerate(sizes)])
    from scipy.optimize import linear_sum_assignment

    cost = ((points[:, None, :2] - slots[None, :, :]) ** 2).sum(-1)
    rows, cols = linear_sum_assignment(cost)
    labels = np.empty(len(points), dtype=int)
    labels[rows] = owner[cols]
    return labels


# --------------------------------------------------------------------------- dot cloud
def _ease(u: np.ndarray, kind: str) -> np.ndarray:
    if kind == "move":
        return u * u * u * (u * (6 * u - 15) + 10)
    if kind == "enter":
        return 1 - (1 - u) ** 3
    if kind == "exit":
        return u ** 3
    return u


class DotCloud(VMobject):
    """N anti-aliased dots as ONE mobject (needs FxCamera): 1,500 dots cost a few milliseconds per frame.

    The dot centres are ``self.points``, so shift / move_to / scale / ``.animate`` and ``Transform`` between two
    clouds of the same size work. ``scale`` moves the dots apart but does not change their radii.

    Per point:  ``radii`` (N,)   ``rgbas`` (N, 4), the alpha is the point's own opacity   ``glows`` (N,) halo strength 0..1
    Whole cloud: the fill opacity is a global alpha (FadeIn / FadeOut / set_opacity); ``glow_reach`` is the halo radius
    in dot radii. Halos add up where they overlap, so a dense lit cluster burns brighter.

    Change points at once with ``set_colors / set_opacities / set_radii / set_glows(value, idx)``, or as an animation
    with ``to(...)`` (regroup, recolour, light up; every point can have its own delay) and ``appear(...)``.

    ``ids`` (N,) is a stable integer per point (default 0..N-1). It travels with the point through ``split``,
    ``subset`` and ``join``, and the drift of a point is a function of its id, the seed and film time only.
    ``opacity`` may be one value or one per point (for example the ``fade`` of ``soft_field``).
    """

    PER_POINT = ("radii", "rgbas", "glows")          # interpolated by Transform
    SLICED = ("radii", "rgbas", "glows", "ids")      # cut and joined with the points

    def __init__(self, centers, radius=th.DOT_R, color=th.DATA, opacity=1.0, glow=0.0,
                 glow_reach: float = th.GLOW_REACH, rgbas=None, ids=None, **kw):
        super().__init__(**kw)
        self.points = np.array(centers, dtype=float).reshape(-1, 3)
        n = len(self.points)
        self.radii = np.full(n, radius, dtype=float) if np.isscalar(radius) else np.array(radius, dtype=float)
        if rgbas is None:
            self.rgbas = np.tile([*_rgb(color), 1.0], (n, 1))
            self.rgbas[:, 3] = opacity
        else:
            self.rgbas = np.array(rgbas, dtype=float)
        self.glows = np.full(n, glow, dtype=float) if np.isscalar(glow) else np.array(glow, dtype=float)
        self.ids = np.arange(n, dtype=np.int64) if ids is None else np.array(ids, dtype=np.int64).reshape(n)
        self.glow_reach = glow_reach
        self.fx_gain = 1.0
        self._drift = None
        self.set_stroke(width=0).set_fill(th.VOID, opacity=1)

    # ---- state
    @property
    def n(self) -> int:
        return len(self.points)

    @property
    def centers(self) -> np.ndarray:
        return self.points

    @centers.setter
    def centers(self, value) -> None:
        self.points = np.array(value, dtype=float).reshape(-1, 3)

    def get_points_defining_boundary(self):
        return self.points

    def _sel(self, idx):
        return slice(None) if idx is None else idx

    def set_colors(self, color, idx=None):
        self.rgbas[self._sel(idx), :3] = _rgb(color)
        return self

    def set_opacities(self, opacity, idx=None):
        self.rgbas[self._sel(idx), 3] = opacity
        return self

    def set_radii(self, radius, idx=None):
        self.radii[self._sel(idx)] = radius
        return self

    def set_glows(self, glow, idx=None):
        self.glows[self._sel(idx)] = glow
        return self

    def interpolate_color(self, mobject1, mobject2, alpha):
        super().interpolate_color(mobject1, mobject2, alpha)
        if isinstance(mobject1, DotCloud) and isinstance(mobject2, DotCloud) and mobject1.n == mobject2.n:
            for name in self.PER_POINT:
                setattr(self, name, (1 - alpha) * getattr(mobject1, name) + alpha * getattr(mobject2, name))

    # ---- parts
    def _take(self, idx) -> dict:
        out = {name: getattr(self, name)[idx].copy() for name in self.SLICED}
        if self._drift is not None:
            out["_drift"] = dict(self._drift, **{k: self._drift[k][idx].copy() for k in self._DRIFT_ARRAYS})
        return out

    def subset(self, idx) -> "DotCloud":
        """A new cloud with a copy of the chosen points (index array or boolean mask). The original is not changed."""
        new = self.copy()
        new.clear_updaters()
        new.points = self.points[idx].copy()
        for name, value in self._take(idx).items():
            setattr(new, name, value)
        if new._drift is not None:
            new.add_updater(DotCloud._tick)
        return new

    def split(self, idx) -> "DotCloud":
        """Take the chosen points out of this cloud and return them as a new cloud (a cluster that lifts out).

        Call it between plays, never inside an updater. Add the new cloud to the scene yourself.
        """
        mask = np.zeros(self.n, dtype=bool)
        mask[idx] = True
        part = self.subset(mask)
        keep = ~mask
        for name, value in self._take(keep).items():
            setattr(self, name, value)
        self.points = self.points[keep]
        return part

    @classmethod
    def join(cls, *clouds: "DotCloud") -> "DotCloud":
        """One new cloud with all the points of ``clouds`` (their colours, radii, glows, ids and drift), in that order.

        The look of the whole (fill opacity, glow reach) is the first cloud's. Take the parts out of the scene and
        put the result in: ``whole = DotCloud.join(a, b, c); self.remove(a, b, c); self.add(whole)``. Then one
        ``to()`` regroups them all. Ids are kept as they are: join clouds that came from one cloud (split, subset),
        or give them distinct ``ids``.
        """
        new = clouds[0].copy()
        new.clear_updaters()
        new.points = np.vstack([c.points for c in clouds])
        for name in cls.SLICED:
            setattr(new, name, np.concatenate([getattr(c, name) for c in clouds]))
        new._drift = None
        if any(c._drift is not None for c in clouds):
            parts = [c._drift if c._drift is not None else _no_drift(c.n) for c in clouds]
            new._drift = dict(parts[0], **{k: np.concatenate([d[k] for d in parts]) for k in cls._DRIFT_ARRAYS})
            new.add_updater(DotCloud._tick)
        return new

    # ---- ambient motion
    _DRIFT_ARRAYS = ("amp", "w", "ph", "tw", "twp")

    def drift(self, amp: float = th.AMBIENT_AMP, period: float = th.AMBIENT_PERIOD, seed: int = 0, twinkle: float = 0.0):
        """Give every point its own slow sway of ``amp`` scene units (a render-time offset: ``points`` stay exact).

        twinkle  the share by which each point's brightness varies (0.15 = 15%), on the same slow clock
        The sway of a point is a function of (seed, its id, film time) only. Inside a Narrated scene the clock is
        film time, so the motion loses no frame at a play boundary, draft and review show the same picture, and a
        cloud that the next scene builds the same way (same points, ids, seed, amp, period) continues it. All idle
        motion eases to rest at the two ends of a scene (``Narrated.rest_ease``). ``drift(0)`` turns it off.
        """
        self.remove_updater(DotCloud._tick)
        if amp <= 0 and twinkle <= 0:
            self._drift = None
            return self
        h = _hash01(seed, self.ids, 5)
        self._drift = dict(amp=np.full(self.n, float(amp)), w=TAU / period * (0.6 + 0.9 * h[:, 0:2]), ph=TAU * h[:, 2:4],
                           tw=np.full(self.n, float(twinkle)), twp=TAU * h[:, 4], t=0.0)
        self.add_updater(DotCloud._tick)
        return self

    def _tick(self, dt):
        self._drift["t"] += dt

    def _clock(self) -> tuple[float, float]:
        """(time, gain) of the idle motion: film time inside a Narrated scene, else the cloud's own clock."""
        return (film.t, film.gain) if film.driven else (self._drift["t"], 1.0)

    def drawn_xy(self) -> np.ndarray:
        """The (N, 2) positions that are painted: the centres plus the drift."""
        d = self._drift
        if d is None:
            return self.points[:, :2]
        t, g = self._clock()
        return self.points[:, :2] + (g * d["amp"])[:, None] * np.sin(d["w"] * t + d["ph"])

    def twinkle_factor(self):
        """The factor on each point's opacity that the twinkle gives now (1.0 without twinkle)."""
        d = self._drift
        if d is None or not d["tw"].any():
            return 1.0
        t, g = self._clock()
        return 1.0 + g * d["tw"] * np.sin(1.7 * d["w"][:, 0] * t + d["twp"])

    # ---- animations
    def to(self, centers=None, color=None, opacity=None, radius=None, glow=None, idx=None, rgbas=None,
           lag: float = 0.0, order="index", seed: int = 0, delays=None, span=None, **kw) -> "CloudTo":
        """An animation that takes the chosen points (``idx``, default all) to new centres, colour, opacity, radius, glow.

        ``lag`` (0..1) spreads the start of the points over that share of the run time, in the given ``order``:
        "index", "random", "x", "y", "radial" (distance from the cloud centre) or an array of sort keys.
        ``delays`` / ``span`` give every point its own window directly (fractions of the run time).
        Further keywords go to CloudTo: ``arc``, ``ease``, ``flash``, ``pop``, ``run_time``, ``rate_func``.

        ``flash`` adds glow and ``pop`` adds radius (a share of the radius) at the start of each point's window, and
        both decay to nothing by the end of it: a point that "arrives" or "is picked" (a number, or one per point).

        It changes only the chosen points and only the properties that are named (colour and opacity are separate
        properties), so several ``to()`` on one cloud can share a play in any order (one group lights up while the
        rest steps back), as long as no two of them change the same property of the same point.
        """
        sel = self._sel(idx)
        rows = np.zeros(self.n, dtype=bool)
        rows[sel] = True
        tgt: dict = {}
        if centers is not None:
            tgt["centers"] = self.points.copy()
            tgt["centers"][sel] = np.array(centers, dtype=float).reshape(-1, 3)
        if rgbas is not None or color is not None or opacity is not None:
            tgt["rgbas"] = self.rgbas.copy()
            if rgbas is not None:
                tgt["rgbas"][sel] = rgbas
            if color is not None:
                tgt["rgbas"][sel, :3] = _rgb(color)
            if opacity is not None:
                tgt["rgbas"][sel, 3] = opacity
            kw["rgba_cols"] = (0, 1, 2, 3) if rgbas is not None else (0, 1, 2) * (color is not None) + (3,) * (opacity is not None)
        if radius is not None:
            tgt["radii"] = self.radii.copy()
            tgt["radii"][sel] = radius
        if glow is not None:
            tgt["glows"] = self.glows.copy()
            tgt["glows"][sel] = glow
        if delays is None and lag > 0:
            delays = np.zeros(self.n)
            active = np.arange(self.n)[sel]
            delays[active] = lag * self._ranks(order, seed)[active].argsort().argsort() / max(len(active) - 1, 1)
            span = 1 - lag if span is None else span
        return CloudTo(self, rows=rows, delays=delays, span=span, **tgt, **kw)

    def _ranks(self, order, seed: int) -> np.ndarray:
        if isinstance(order, str):
            xy = self.points[:, :2]
            c = xy.mean(axis=0) if self.n else np.zeros(2)
            return {"index": np.arange(self.n, dtype=float), "random": np.random.default_rng(seed).random(self.n),
                    "x": xy[:, 0], "y": -xy[:, 1], "radial": np.hypot(*(xy - c).T)}[order]
        return np.asarray(order, dtype=float)

    def appear(self, starts=None, fade=0.35, idx=None, opacity=None, order="index", seed: int = 0,
               run_time: float | None = None, flash=0.9, pop=0.8, **kw) -> "CloudTo":
        """An animation in which the chosen points come into being: the k-th point (in ``order``) at ``starts[k]``
        seconds, in ``fade`` seconds (a number or one value per point).

        ``starts`` is an array of seconds (see motion.sampling_rhythm) or None for all at once. Each point arrives with
        a short flash of glow and a larger radius (``flash``, ``pop``: a number, or one value per point of the cloud),
        then settles at ``opacity`` (a number or one value per chosen point; default: the opacity the points have
        now). The points are invisible from the first frame of the animation, so the cloud may already be in the
        scene, with these points at opacity 0 or not.
        ``run_time`` defaults to the moment the last point has settled. With a shorter one (the usual case: a count
        that must land on a word) the fades of the last points are cut short, so that all points are there at the end.
        """
        chosen = np.arange(self.n)[self._sel(idx)]
        active = chosen[np.argsort(self._ranks(order, seed)[chosen], kind="stable")]
        starts = np.zeros(len(active)) if starts is None else np.asarray(starts, dtype=float)
        fade = np.broadcast_to(np.asarray(fade, dtype=float), starts.shape)
        total = float((starts + fade).max()) if run_time is None else float(run_time)
        starts = np.minimum(starts, total)
        fade = np.minimum(fade, np.maximum(total - starts, 1e-6))
        delays, spans = np.zeros(self.n), np.ones(self.n)
        delays[active], spans[active] = starts / total, fade / total
        rows = np.zeros(self.n, dtype=bool)
        rows[chosen] = True
        start_alpha = self.rgbas[:, 3].copy()
        start_alpha[chosen] = 0.0
        rgbas = self.rgbas.copy()
        if opacity is not None:
            rgbas[chosen, 3] = opacity
        return CloudTo(self, rgbas=rgbas, rows=rows, delays=delays, span=spans, start_alpha=start_alpha, flash=flash, pop=pop,
                       ease="enter", run_time=total, rgba_cols=(3,), **kw)


class CloudTo(Animation):
    """Take a DotCloud to new per-point values; every point has its own time window and its own easing.

    centers, rgbas, radii, glows   the target arrays (whole cloud); a property that is None is not touched
    rows           boolean mask of the points this animation may change (default: those whose target differs)
    delays, span   per-point window as fractions of the run time (arrays or scalars); default: all points together
    arc            angle of the circular arc every point travels on (0 = straight)
    ease           "move" (slow-fast-slow), "enter" (lands softly), "exit" or "linear": the easing INSIDE each window
    flash, pop     extra glow and extra radius (as a share of the radius) at the start of a point's window; both
                   decay. A number, or one value per point of the cloud.
    rgba_cols      the columns of ``rgbas`` it owns: (0, 1, 2) colour, (3,) opacity, all four by default

    It writes only its own points, properties and colour columns, so several CloudTo on one cloud can run in one
    play, in any order, as long as no two of them change the same property of the same point. At the end every
    point is at its target.
    """

    KEYS = ("points", "rgbas", "radii", "glows")

    def __init__(self, cloud: DotCloud, centers=None, rgbas=None, radii=None, glows=None, rows=None, delays=None, span=None,
                 arc: float = 0.0, ease: str = "move", flash=0.0, pop=0.0, start_alpha=None, rgba_cols=(0, 1, 2, 3), **kw):
        kw.setdefault("rate_func", linear)                       # the easing is per point
        kw.setdefault("run_time", th.T_MOVE)
        kw.setdefault("suspend_mobject_updating", False)         # the drift goes on while the cloud regroups
        self.target = dict(points=centers, rgbas=rgbas, radii=radii, glows=glows)
        self.given_rows = None if rows is None else np.asarray(rows, dtype=bool)
        self.delays = 0.0 if delays is None else np.asarray(delays, dtype=float)
        self.span = (1.0 - float(np.max(self.delays))) if span is None else np.asarray(span, dtype=float)
        self.arc, self.ease, self.start_alpha = arc, ease, start_alpha
        self.cols = np.array(sorted(set(rgba_cols)), dtype=int)
        self.flash, self.pop = np.asarray(flash, dtype=float), np.asarray(pop, dtype=float)
        super().__init__(cloud, **kw)

    def begin(self) -> None:
        c = self.mobject
        n = c.n
        before = {k: getattr(c, k).copy() for k in self.KEYS}
        mine = np.ones(n, dtype=bool) if self.given_rows is None else self.given_rows
        if self.start_alpha is not None:
            c.rgbas[mine, 3] = np.asarray(self.start_alpha, dtype=float)[mine]
        self.start = dict(before, rgbas=c.rgbas.copy())
        self.end = {k: (self.start[k] if v is None else np.array(v, dtype=float).reshape(before[k].shape))
                    for k, v in self.target.items()}
        none = np.zeros(n, dtype=bool)
        rows = {k: (none if v is None else mine) for k, v in self.target.items()}
        if self.given_rows is None:                              # no mask given: the points whose target differs
            rows = {k: m & (np.abs(self.end[k] - self.start[k]).reshape(n, -1).max(axis=1) > 1e-12) for k, m in rows.items()}
            mine = rows["points"] | rows["rgbas"] | rows["radii"] | rows["glows"]
        self.moved = mine
        if self.pop.any():
            rows["radii"] = rows["radii"] | mine
        if self.flash.any():
            rows["glows"] = rows["glows"] | mine
        self.rows = rows
        super().begin()

    def interpolate_mobject(self, alpha: float) -> None:
        c, s, e, rows = self.mobject, self.start, self.end, self.rows
        t = self.rate_func(alpha)
        u = np.clip((t - self.delays) / np.maximum(self.span, 1e-9), 0, 1) * np.ones(len(s["radii"]))
        if t >= 1:
            u[:] = 1.0                                           # whatever the windows are, the end state is the target
        w = _ease(u, self.ease)
        m = rows["points"]
        if m.any():
            p0, p1, wm = s["points"][m], e["points"][m], w[m]
            if self.arc:
                half = (p1 - p0) / 2
                centre = (p0 + p1) / 2 + np.column_stack([-half[:, 1], half[:, 0], 0 * half[:, 0]]) / np.tan(self.arc / 2)
                d = p0 - centre
                cos, sin = np.cos(wm * self.arc), np.sin(wm * self.arc)
                on_arc = centre + np.column_stack([d[:, 0] * cos - d[:, 1] * sin, d[:, 0] * sin + d[:, 1] * cos, d[:, 2]])
                c.points[m] = np.where((wm >= 1)[:, None], p1, np.where((wm <= 0)[:, None], p0, on_arc))
            else:
                c.points[m] = p0 + (p1 - p0) * wm[:, None]
        m = rows["rgbas"]
        if m.any() and len(self.cols):
            r = np.ix_(np.nonzero(m)[0], self.cols)
            c.rgbas[r] = s["rgbas"][r] + (e["rgbas"][r] - s["rgbas"][r]) * w[m][:, None]
        burst = np.where((u > 0) & (u < 1) & self.moved, (1 - u) ** 2, 0.0)
        m = rows["radii"]
        if m.any():
            c.radii[m] = ((s["radii"] + (e["radii"] - s["radii"]) * w) * (1 + self.pop * burst))[m]
        m = rows["glows"]
        if m.any():
            c.glows[m] = np.clip(s["glows"] + (e["glows"] - s["glows"]) * w + self.flash * burst, 0, 1)[m]


# --------------------------------------------------------------------------- trail
class Trail(VMobject):
    """A ribbon along ``self.points`` (M x 3 samples of a centre line) with a width and an RGBA at every sample.

    FxCamera paints it as one smooth shape (a Cairo mesh), so there are no beads and no seams, in every direction
    of travel. Set ``points``, ``widths`` (scene units) and ``rgbas`` in place from an updater; see motion.Runner.
    """

    def __init__(self, points=None, widths=None, rgbas=None, **kw):
        super().__init__(**kw)
        self.points = np.zeros((0, 3)) if points is None else np.array(points, dtype=float)
        m = len(self.points)
        self.widths = np.zeros(m) if widths is None else np.array(widths, dtype=float)
        self.rgbas = np.zeros((m, 4)) if rgbas is None else np.array(rgbas, dtype=float)
        self.fx_gain = 1.0
        self.set_stroke(width=0).set_fill(th.VOID, opacity=1)

    def get_points_defining_boundary(self):
        return self.points

    def set_samples(self, points, widths, rgbas):
        self.points, self.widths, self.rgbas = np.asarray(points, dtype=float), np.asarray(widths, dtype=float), np.asarray(rgbas, dtype=float)
        return self


# --------------------------------------------------------------------------- clip, blend, ambient
def set_clip(mob, clip_mob):
    """Show ``mob`` only inside ``clip_mob`` (any closed VMobject). Move or scale ``clip_mob`` to wipe.

    Add ``clip_mob`` to the scene BEFORE ``mob`` (it may be invisible): Manim repaints only what comes after the
    first moving object, so a clip that is listed after its art has no effect until the play ends.
    """
    for m in mob.get_family():
        m.fx_clip = clip_mob
    return mob


def set_pinned(mob, pinned: bool = True):
    """Paint ``mob`` in screen coordinates (the frame of a camera at rest), whatever the camera does. Its points are
    then positions ON SCREEN. Scenes use ``Narrated.pin`` / ``pin_to_frame``, which also convert the coordinates."""
    for m in mob.get_family():
        m.fx_pinned = pinned
    return mob


def set_blend(mob, mode: str | None = "screen"):
    """Composite ``mob`` with a Cairo operator: "screen" or "add" make overlapping light brighter, "multiply" darkens."""
    for m in mob.get_family():
        m.fx_blend = mode
    return mob


class AmbientState:
    """A slow seeded sway (and an optional pulse of brightness) that FxCamera applies when it paints. See motion.ambient.

    Its clock is film time inside a Narrated scene (the same rule as ``DotCloud.drift``), else its own ``t``.
    """

    def __init__(self, amp: float, period: float, seed: int, pulse: float = 0.0):
        rng = np.random.default_rng(seed)
        self.amp, self.pulse, self.t = amp, pulse, 0.0
        self.w = TAU / period * np.array([[1.0, 1.0], [1.618, 1.414]]) * rng.uniform(0.85, 1.15, (2, 2))
        self.ph = rng.uniform(0, TAU, (2, 2))
        self.pw, self.pph = TAU / period * 1.3, rng.uniform(0, TAU)

    def _clock(self) -> tuple[float, float]:
        return (film.t, film.gain) if film.driven else (self.t, 1.0)

    def offset(self) -> np.ndarray:
        t, g = self._clock()
        s = np.sin(self.w * t + self.ph)
        return g * self.amp * (0.7 * s[0] + 0.3 * s[1])

    def gain(self) -> float:
        t, g = self._clock()
        return 1.0 + g * self.pulse * np.sin(self.pw * t + self.pph)


# --------------------------------------------------------------------------- camera
class FxCamera(MovingCamera):
    """MovingCamera that also paints RadialGlow, DotCloud, Trail and RasterLayer, and applies clip, blend, ambient
    motion and screen pinning.

    It resets the stroke join and cap before every stroke: the stock camera leaves them as the object drawn before
    set them, so an AUTO stroke would look different from frame to frame.
    """

    BLEND = {"add": cairo.OPERATOR_ADD, "screen": cairo.OPERATOR_SCREEN, "lighten": cairo.OPERATOR_LIGHTEN,
             "multiply": cairo.OPERATOR_MULTIPLY, "over": cairo.OPERATOR_OVER}
    GLOW_STOPS = np.linspace(0, 1, 24)
    SNAP_HALOS_ABOVE = 240          # more glowing points than this: halos are placed on whole pixels (4x faster)

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._halo_cache: dict[int, tuple] = {}

    def apply_stroke(self, ctx, vmobject, background: bool = False):
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        return super().apply_stroke(ctx, vmobject, background)

    def apply_fill(self, ctx, vmobject):
        if isinstance(vmobject, RadialGlow):
            return self._fill_glow(vmobject, ctx)
        return super().apply_fill(ctx, vmobject)

    def _fill_glow(self, glow: "RadialGlow", ctx):
        """Fill the bounding box of a RadialGlow with a radial gradient that follows its centre, size and stretch.

        Cairo dithers a gradient only when it PAINTS through a clip on whole pixels; a filled path gets none and
        shows rings. So the gradient is painted into the pixel box around the glow. The path is left as it was.
        """
        rgba = self.get_fill_rgbas(glow)[0]
        if rgba[3] <= 0.002 or glow.width <= 0 or glow.height <= 0:
            return self
        c = glow.get_center()
        path = ctx.copy_path()
        ctx.save()
        ctx.translate(c[0], c[1])
        ctx.scale(glow.width / 2, glow.height / 2)
        pat = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        for s in self.GLOW_STOPS:                                # the surface is BGRA: reverse rgb like the stock camera
            pat.add_color_stop_rgba(float(s), rgba[2], rgba[1], rgba[0], float(rgba[3] * (1 - s) ** glow.glow_power))
        if hasattr(pat, "set_dither"):
            pat.set_dither(cairo.Dither.BEST)
        ctx.set_source(pat)
        (x0, y0), (x1, y1) = ctx.user_to_device(-1, 1), ctx.user_to_device(1, -1)
        ctx.identity_matrix()
        ctx.new_path()
        ctx.rectangle(np.floor(min(x0, x1)), np.floor(min(y0, y1)), np.ceil(abs(x1 - x0)) + 1, np.ceil(abs(y1 - y0)) + 1)
        ctx.clip()
        ctx.paint()
        ctx.restore()
        ctx.new_path()
        ctx.append_path(path)
        return self

    def display_vectorized(self, vmobject, ctx):
        if getattr(vmobject, "fx_hidden", False):
            return self
        clip = getattr(vmobject, "fx_clip", None)
        blend = getattr(vmobject, "fx_blend", None)
        amb = getattr(vmobject, "fx_ambient", None)
        pinned = getattr(vmobject, "fx_pinned", False)
        if clip is None and blend is None and amb is None and not pinned:
            return self._paint(vmobject, ctx, 1.0)
        ctx.save()
        if pinned:                                               # screen coordinates: the camera's own move is ignored
            pw, ph = self.pixel_width, self.pixel_height
            ctx.set_matrix(cairo.Matrix(pw / config.frame_width, 0, 0, -ph / config.frame_height, pw / 2, ph / 2))
        if clip is not None:
            ctx.new_path()
            self.set_cairo_context_path(ctx, clip)
            ctx.clip()
        gain = 1.0
        if amb is not None:
            ctx.translate(*amb.offset())
            gain = amb.gain()
        if blend is not None:
            ctx.set_operator(self.BLEND[blend])
        self._paint(vmobject, ctx, gain)
        ctx.restore()
        return self

    def _paint(self, vmobject, ctx, gain: float):
        if isinstance(vmobject, RasterLayer):
            return self._paint_raster(vmobject, ctx, gain)
        if isinstance(vmobject, DotCloud):
            return self._paint_cloud(vmobject, ctx, gain)
        if isinstance(vmobject, Trail):
            return self._paint_trail(vmobject, ctx, gain)
        return super().display_vectorized(vmobject, ctx)

    def _paint_raster(self, layer: RasterLayer, ctx, gain: float):
        px = layer.fx_pixels
        h, w = px.shape[:2]
        alpha = float(np.clip(layer.get_fill_opacity() * layer.fx_gain * gain, 0, 1))
        if alpha <= 0.002 or layer.width <= 0:
            return self
        if layer.fx_surface is None:
            layer.fx_surface = cairo.ImageSurface.create_for_data(px.data, cairo.FORMAT_ARGB32, w, h, w * 4)
        c, bw, bh = layer.get_center(), layer.width * layer.fx_bleed, layer.height * layer.fx_bleed
        left, top = c[0] - bw / 2, c[1] + bh / 2
        m = ctx.get_matrix()
        ctx.save()
        if layer.fx_snap and abs(bw * m.xx / w - 1) < 2e-3 and abs(bh * -m.yy / h - 1) < 2e-3:
            x, y = ctx.user_to_device(left, top)                 # one picture pixel per screen pixel: no resampling
            ctx.identity_matrix()
            ctx.set_source_surface(layer.fx_surface, round(x), round(y))
            ctx.get_source().set_filter(cairo.FILTER_NEAREST)
        else:
            ctx.translate(left, top)
            ctx.scale(bw / w, -bh / h)
            ctx.set_source_surface(layer.fx_surface, 0, 0)
            ctx.get_source().set_filter(cairo.FILTER_BILINEAR if layer.fx_smooth else cairo.FILTER_NEAREST)
        ctx.paint_with_alpha(alpha)
        ctx.restore()
        return self

    def _halo(self, radius_px: int) -> tuple:
        """An A8 mask of a halo with the given pixel radius (cached). Returns (surface, size, buffer)."""
        radius_px = max(int(radius_px), 1)
        if radius_px not in self._halo_cache:
            if len(self._halo_cache) > 512:
                self._halo_cache.clear()
            size = 2 * radius_px + 1
            y, x = np.mgrid[-radius_px:radius_px + 1, -radius_px:radius_px + 1] / (radius_px + 0.5)
            a = np.clip(1 - np.hypot(x, y), 0, 1) ** th.GLOW_POWER
            stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, size)
            buf = np.zeros((size, stride), dtype=np.uint8)
            buf[:, :size] = np.rint(a * 255)
            surf = cairo.ImageSurface.create_for_data(buf.data, cairo.FORMAT_A8, size, size, stride)
            self._halo_cache[radius_px] = (surf, size, buf)
        return self._halo_cache[radius_px]

    def _paint_cloud(self, cloud: DotCloud, ctx, gain: float):
        n = cloud.n
        if n == 0:
            return self
        fade = float(np.clip(cloud.get_fill_opacity(), 0, 1))
        alpha = np.clip(cloud.rgbas[:, 3] * fade * cloud.twinkle_factor(), 0, 1)
        vis = (alpha > 0.004) & (cloud.radii > 0)
        if not vis.any():
            return self
        xy, r, rgb = cloud.drawn_xy(), cloud.radii, cloud.rgbas[:, :3]
        halo = np.clip(cloud.glows * cloud.fx_gain * gain, 0, 1.5) * alpha
        lit = np.nonzero(vis & (halo > 0.004))[0]
        if len(lit):
            m = ctx.get_matrix()
            dx, dy = xy[lit, 0] * m.xx + m.x0, xy[lit, 1] * m.yy + m.y0
            rpx = np.maximum(np.rint(r[lit] * cloud.glow_reach * abs(m.xx)), 1).astype(int)
            snap = len(lit) > self.SNAP_HALOS_ABOVE
            ctx.save()
            ctx.identity_matrix()
            ctx.set_operator(cairo.OPERATOR_ADD)
            for k, i in enumerate(lit):
                surf, size, _ = self._halo(rpx[k])
                x, y = dx[k] - size / 2, dy[k] - size / 2
                if snap:
                    x, y = round(x), round(y)
                ctx.set_source_rgba(rgb[i, 2], rgb[i, 1], rgb[i, 0], min(0.6 * halo[i], 1.0))
                ctx.mask_surface(surf, x, y)
            ctx.restore()
        heat = 0.5 * np.clip(cloud.glows, 0, 1)[:, None]
        core = rgb + (_rgb(th.CORE)[None, :] - rgb) * heat           # a lit point has a hotter core
        for i in np.nonzero(vis)[0]:
            ctx.set_source_rgba(core[i, 2], core[i, 1], core[i, 0], alpha[i])
            ctx.new_path()
            ctx.arc(xy[i, 0], xy[i, 1], r[i], 0, TAU)
            ctx.fill()
        return self

    def _paint_trail(self, trail: Trail, ctx, gain: float):
        p = trail.points[:, :2]
        if len(p) < 2:
            return self
        fade = float(np.clip(trail.get_fill_opacity() * trail.fx_gain * gain, 0, 1))
        col = trail.rgbas
        a = np.clip(col[:, 3] * fade, 0, 1)
        if a.max() <= 0.004:
            return self
        d = np.gradient(p, axis=0)
        length = np.hypot(d[:, 0], d[:, 1])
        if length.max() <= 1e-9:
            return self
        nrm = np.column_stack([-d[:, 1], d[:, 0]]) / np.maximum(length, 1e-9)[:, None]
        half = nrm * trail.widths[:, None] / 2
        left, right = p + half, p - half
        wide_l, wide_r = p + 1.7 * half + nrm * 0.02, p - 1.7 * half - nrm * 0.02   # the mesh is wider than the fill
        mesh = cairo.MeshPattern()
        for i in range(len(p) - 1):
            mesh.begin_patch()
            mesh.move_to(*wide_l[i])
            mesh.line_to(*wide_l[i + 1])
            mesh.line_to(*wide_r[i + 1])
            mesh.line_to(*wide_r[i])
            c0, c1 = col[i], col[i + 1]
            mesh.set_corner_color_rgba(0, c0[2], c0[1], c0[0], a[i])
            mesh.set_corner_color_rgba(1, c1[2], c1[1], c1[0], a[i + 1])
            mesh.set_corner_color_rgba(2, c1[2], c1[1], c1[0], a[i + 1])
            mesh.set_corner_color_rgba(3, c0[2], c0[1], c0[0], a[i])
            mesh.end_patch()
        ctx.new_path()
        ctx.move_to(*left[0])
        for q in left[1:]:
            ctx.line_to(*q)
        for q in right[::-1]:
            ctx.line_to(*q)
        ctx.close_path()
        ctx.set_source(mesh)
        ctx.fill()
        return self


# --------------------------------------------------------------------------- background
def vignette_array(w: int | None = None, h: int | None = None, inner=th.BG, outer=th.BG_EDGE, centre=(0.5, 0.47),
                   reach: float = 1.08, power: float = 1.7, noise: float = 1.25, seed: int = 7) -> np.ndarray:
    """uint8 RGBA background: a radial falloff from ``inner`` to ``outer`` plus about one code value of noise.

    The noise is the dither. Without it the whole vignette has about nine code values and shows rings, in the PNG
    and after H.264. The same seed gives the same grain in every scene, so a cut between two scenes is invisible.
    """
    w, h = w or config.pixel_width, h or config.pixel_height
    y, x = np.mgrid[0:1:h * 1j, 0:1:w * 1j]
    d = np.hypot((x - centre[0]) * (w / h), y - centre[1])           # distance in frame heights
    t = np.clip(d / reach, 0, 1) ** power
    rgb = 255 * (_rgb(inner)[None, None, :] * (1 - t[..., None]) + _rgb(outer)[None, None, :] * t[..., None])
    rgb = rgb + np.random.default_rng(seed).normal(0, noise, size=(h, w, 1))   # the same noise on r, g, b: neutral grain
    out = np.empty((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.rint(rgb), 0, 255)
    out[..., 3] = 255
    return out


def install_background(scene, **kw) -> None:
    """Make the dithered vignette the camera background. It replaces the flat fill, so it costs nothing per frame.

    Manim's play cache does not see the background: render with caching off (kit.Narrated does this).
    """
    cam = scene.camera
    cam.background = vignette_array(cam.pixel_width, cam.pixel_height, **{**th.VIGNETTE, **kw})
    cam.reset()


# --------------------------------------------------------------------------- organic shapes
def smooth_closed(points: np.ndarray, **style) -> VMobject:
    """A closed smooth blob through ``points`` (N x 3), smooth at the seam wherever it is on screen.

    Do not use ``set_points_smoothly([*pts, pts[0]])``: Manim 0.21.0 treats a loop that starts left of or below the
    origin as open and leaves a corner at the seam.
    """
    from manim.utils.bezier import get_smooth_closed_cubic_bezier_handle_points

    a = np.array([*points, points[0]], dtype=float)
    h1, h2 = get_smooth_closed_cubic_bezier_handle_points(a)
    pts = np.empty((4 * (len(a) - 1), 3))
    pts[0::4], pts[1::4], pts[2::4], pts[3::4] = a[:-1], h1, h2, a[1:]
    m = VMobject(**style)
    m.points = pts
    return m


def blob_points(seed: int = 0, n: int = 10, radius: float = 1.0, rough: float = 0.25, phase: float = 0.0, centre=(0, 0, 0)) -> np.ndarray:
    """Anchor points of an organic closed shape. The same seed with another ``phase`` is the same blob, breathing."""
    rng = np.random.default_rng(seed)
    ang = np.linspace(0, TAU, n, endpoint=False)
    f, ph = rng.uniform(0.6, 1.6, n), rng.uniform(0, TAU, n)
    r = radius * (1 + rough * np.sin(f * phase + ph))
    return np.array(centre, dtype=float) + np.column_stack([r * np.cos(ang), r * np.sin(ang), np.zeros(n)])


def hull_blob(points: np.ndarray, pad: float = 0.25, n: int = 14, **style) -> VMobject:
    """A soft closed outline around a set of points (a cluster): the support of the points in ``n`` directions, padded."""
    c = points[:, :2].mean(axis=0)
    ang = np.linspace(0, TAU, n, endpoint=False)
    dirs = np.column_stack([np.cos(ang), np.sin(ang)])
    reach = ((points[:, :2] - c) @ dirs.T).max(axis=0) + pad
    reach = (np.roll(reach, 1) + 2 * reach + np.roll(reach, -1)) / 4
    return smooth_closed(np.column_stack([c + dirs * reach[:, None], np.zeros(n)]), **style)


# --------------------------------------------------------------------------- encoder
def set_encoder(crf: int = 12, preset: str = "veryfast") -> None:
    """Make Manim encode its scene files with this x264 quality (Manim fixes CRF 23, which is too lossy for dark,
    soft pictures). Call it once before rendering; ``EXPLAINER_CRF`` / ``EXPLAINER_PRESET`` do the same at import.
    """
    from manim.scene.scene_file_writer import SceneFileWriter

    original = getattr(SceneFileWriter, "_kit_original_open", SceneFileWriter.open_partial_movie_stream)

    def opened(self, *a, **k):
        result = original(self, *a, **k)
        job = self._current_encode_job
        if job is not None:
            job.stream.thread_type = "AUTO"
            job.stream.codec_context.options = {"preset": preset, "crf": str(crf)}
        return result

    SceneFileWriter._kit_original_open = original
    SceneFileWriter.open_partial_movie_stream = opened


__all__ = ["FxCamera", "DotCloud", "CloudTo", "Trail", "RasterLayer", "RadialGlow", "AmbientState", "bake", "glow_rgba",
           "glow_sprite", "soft_band", "set_clip", "set_blend", "set_pinned", "install_background", "vignette_array", "smooth_closed",
           "blob_points", "hull_blob", "field_points", "soft_field", "sunflower_points", "cluster_points", "match_points",
           "nearest_labels", "px_per_unit", "set_encoder", "film_time", "idle_gain"]
