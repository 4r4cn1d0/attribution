"""Audio steps for the narration builder, with numpy and scipy only.

Speech edges and silences on a 10 ms level, raised-cosine fades, exact 2x upsampling to 48 kHz, integrated
loudness (ITU-R BS.1770-4), and a zero-delay limiter that works on the peaks between the samples (true peak).
Nothing here changes the length of a signal, so every timestamp stays valid.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
from scipy.signal import lfilter, resample_poly

WIN, HOP = 0.010, 0.005
# K-weighting for 48 kHz, as printed in BS.1770-4 (high shelf, then high-pass).
K_SHELF = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
K_HIGH_PASS = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])


def frame_db(x: np.ndarray, rate: int) -> tuple[np.ndarray, np.ndarray]:
    """(centre time, level in dB) of every 10 ms frame, 5 ms apart."""
    w, h = int(round(WIN * rate)), int(round(HOP * rate))
    if len(x) < w:
        x = np.concatenate([x, np.zeros(w - len(x), dtype=x.dtype)])
    total = np.concatenate([[0.0], np.cumsum(x.astype(np.float64) ** 2)])
    i = h * np.arange(1 + (len(x) - w) // h)
    power = np.maximum(total[i + w] - total[i], 0.0) / w
    return (i + w / 2) / rate, 10 * np.log10(power + 1e-24)


def speech_bounds(x: np.ndarray, rate: int, thresh_db: float) -> tuple[float, float]:
    """Start of the first and end of the last frame whose level is within thresh_db of the loudest frame."""
    t, db = frame_db(x, rate)
    on = np.flatnonzero(db - db.max() > thresh_db)
    return float(t[on[0]] - WIN / 2), float(t[on[-1]] + WIN / 2)


def silences(x: np.ndarray, rate: int, thresh_db: float, min_len: float) -> list[tuple[float, float]]:
    """[(start, end)] where the level stays more than thresh_db below the loudest frame for at least min_len."""
    t, db = frame_db(x, rate)
    quiet = np.concatenate([[False], db - db.max() < thresh_db, [False]])
    edges = np.flatnonzero(np.diff(quiet.astype(np.int8)))
    out = []
    for a, b in zip(edges[::2], edges[1::2] - 1):          # first and last quiet frame of each run
        start = max(0.0, float(t[a] - WIN / 2))
        end = len(x) / rate if b == len(t) - 1 else float(t[b] + WIN / 2)
        if end - start >= min_len:
            out.append((start, end))
    return out


def fade(x: np.ndarray, rate: int, fade_in: float, fade_out: float) -> np.ndarray:
    """Raised-cosine fades, so that a cut away from a zero crossing cannot click."""
    y = x.astype(np.float32).copy()
    a, b = min(len(y), int(fade_in * rate)), min(len(y), int(fade_out * rate))
    if a > 1:
        y[:a] *= (0.5 - 0.5 * np.cos(np.pi * np.arange(a) / a)).astype(np.float32)
    if b > 1:
        y[-b:] *= (0.5 + 0.5 * np.cos(np.pi * np.arange(b) / b)).astype(np.float32)
    return y


def to_48k(x: np.ndarray, rate: int = 24000) -> np.ndarray:
    """Exact 2x polyphase upsampling: the sample count doubles and there is no lag."""
    if rate != 24000:
        raise ValueError("to_48k expects 24 kHz input")
    return resample_poly(x.astype(np.float32), 2, 1).astype(np.float32)


def k_weighted(x: np.ndarray) -> np.ndarray:
    return lfilter(*K_HIGH_PASS, lfilter(*K_SHELF, x.astype(np.float64)))


def gated_loudness(y: np.ndarray, rate: int = 48000) -> float:
    """Integrated loudness of a K-weighted signal: 400 ms blocks, 100 ms apart, gates at -70 LUFS and -10 LU."""
    w, h = int(0.4 * rate), int(0.1 * rate)
    if len(y) < w:
        return float("-inf")
    total = np.concatenate([[0.0], np.cumsum(y ** 2)])
    i = np.arange(0, len(y) - w + 1, h)
    z = np.maximum(total[i + w] - total[i], 0.0) / w
    loud = -0.691 + 10 * np.log10(z + 1e-30)
    keep = loud > -70.0
    if not keep.any():
        return float("-inf")
    keep &= loud > -0.691 + 10 * np.log10(z[keep].mean()) - 10.0
    return float(-0.691 + 10 * np.log10(z[keep].mean()))


def lufs(x: np.ndarray, rate: int = 48000) -> float:
    """Integrated loudness (ITU-R BS.1770-4) of a mono signal at 48 kHz."""
    if rate != 48000:
        raise ValueError("the loudness meter is written for 48 kHz")
    return gated_loudness(k_weighted(x), rate)


def peak_envelope(x: np.ndarray, oversample: int = 4) -> np.ndarray:
    """For each sample, the largest absolute value of the oversampled signal within half a sample of it."""
    up = np.abs(resample_poly(x.astype(np.float32), oversample, 1))
    near = maximum_filter1d(up, size=oversample + 1, mode="constant")[::oversample]
    return np.maximum(near, np.abs(x)).astype(np.float32)


def true_peak_db(x: np.ndarray) -> float:
    """Largest peak in dBTP on the 4x oversampled signal.  Only the neighbourhoods of samples within 6 dB of the
    largest sample are oversampled: the content sits below a quarter of the sample rate (it comes from 24 kHz),
    so a peak between samples has such a sample next to it."""
    a = np.abs(x)
    if not len(a) or a.max() == 0.0:
        return float("-inf")
    near = maximum_filter1d((a >= 0.5 * a.max()).astype(np.uint8), size=129, mode="constant")
    return float(20 * np.log10(peak_envelope(x[near > 0]).max()))


def limiter_gain(peak: np.ndarray, rate: int, ceiling_db: float, hold: float = 0.008,
                 release_db_per_s: float = 100.0) -> np.ndarray:
    """Gain curve (0..1] that keeps peak * gain under the ceiling.

    The gain drops before a peak (look-ahead, no delay), holds across the pitch periods of a loud vowel, and
    recovers at a fixed slope in dB.  It is never above the gain that a sample needs.
    """
    need = np.minimum(1.0, 10 ** (ceiling_db / 20) / np.maximum(peak.astype(np.float64), 1e-9))
    n = max(1, int(hold * rate))
    g = minimum_filter1d(need, size=2 * n + 1, mode="nearest")
    if g.min() < 1.0:
        ramp = np.arange(len(g)) * (release_db_per_s / rate)
        g = 10 ** ((np.minimum.accumulate(20 * np.log10(g) - ramp) + ramp) / 20)
        g = uniform_filter1d(g, size=n, mode="nearest")
    return np.minimum(g, need)


def master(x: np.ndarray, rate: int, target_lufs: float, ceiling_db: float, gain_db: float | None = None,
           parts: list[int] | None = None, step_db: float = 0.1, max_iter: int = 8) -> tuple[np.ndarray, dict]:
    """One gain for the whole signal, then the limiter.  Returns (y, info).

    With gain_db=None the gain is searched so that the limited result lands on target_lufs; with a number, that
    gain is applied as it is (a partial build re-uses the gain of the whole programme).  The searched gain is a
    multiple of step_db: a small change of the programme (one pause) then keeps the gain, and the scenes that
    did not change keep their samples.  ``parts`` are the sample counts of the scenes; info['parts_lufs'] then
    holds each scene's own loudness.
    """
    peak = peak_envelope(x)
    before = lufs(x, rate)
    if not np.isfinite(before):
        raise ValueError("the signal is too short or too quiet to measure its loudness")
    searched = gain_db is None
    on_step = lambda v: round(round(v / step_db) * step_db, 3)                      # noqa: E731
    gain_db = on_step(target_lufs - before + 0.4) if searched else round(float(gain_db), 3)   # the limiter takes about 0.4 LU
    for i in range(max_iter):                   # the gain that is reported is exactly the gain that is applied
        lin = 10 ** (gain_db / 20)
        g = limiter_gain(peak * lin, rate, ceiling_db)
        y = (x * (lin * g)).astype(np.float32)
        weighted = k_weighted(y)
        after = gated_loudness(weighted, rate)
        if not searched or i == max_iter - 1 or on_step(gain_db + target_lufs - after) == gain_db:
            break
        gain_db = on_step(gain_db + target_lufs - after)
    info = {"target_lufs": target_lufs, "ceiling_dbtp": ceiling_db, "gain_db": gain_db,
            "lufs_before": round(before, 2), "lufs_after": round(after, 2),
            "max_gain_reduction_db": round(float(-20 * np.log10(g.min())), 2),
            "share_limited_over_1db": round(float((g < 10 ** (-1 / 20)).mean()), 4),
            "sample_peak_dbfs": round(float(20 * np.log10(np.abs(y).max() + 1e-12)), 2)}
    if parts:
        ends = np.cumsum(parts)
        info["parts_lufs"] = [round(gated_loudness(weighted[e - n:e], rate), 2) for n, e in zip(parts, ends)]
    return y, info
