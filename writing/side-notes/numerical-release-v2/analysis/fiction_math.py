"""Original registered pooled-t fiction arithmetic; data loading omitted."""
import math
from fractions import Fraction
DOLLY_DIFFERS="fiction differs from Dolly ({})"
LABEL_NAMES={"content":{"both":"content matters, smaller than m","matters":"content matters","within":"no difference larger than m","none":"inconclusive"},"fiction_minus_dolly":{"both":"fiction differs from Dolly, smaller than m","matters":DOLLY_DIFFERS,"within":"no difference from Dolly larger than m","none":"inconclusive"}}

def mean(values) -> Fraction:
    values = [Fraction(v) for v in values]
    return sum(values, Fraction(0)) / len(values)

def t_cdf(t: float, df: int) -> float:
    """Student t CDF for an integer df >= 1, by the closed forms of Abramowitz and Stegun 26.7.3 (odd df) and 26.7.4
    (even df): A(t|df) = P(|T| <= t) and F = (1 + A) / 2, with theta = atan(t / sqrt(df))."""
    if isinstance(df, bool) or not isinstance(df, int) or df < 1:
        raise ValueError("df must be a positive integer")
    if t < 0:
        return 1.0 - t_cdf(-t, df)
    theta = math.atan(t / math.sqrt(df))
    s, c = math.sin(theta), math.cos(theta)
    total, term = 1.0, 1.0
    if df % 2:                         # odd: A = 2/pi (theta + sin cos [1 + 2/3 c^2 + 2*4/(3*5) c^4 + ...])
        for k in range(1, (df - 1) // 2):
            term *= c * c * (2 * k) / (2 * k + 1)
            total += term
        a = 2 / math.pi * (theta + (s * c * total if df > 1 else 0.0))
    else:                              # even: A = sin [1 + 1/2 c^2 + 1*3/(2*4) c^4 + ...]
        for k in range(1, df // 2):
            term *= c * c * (2 * k - 1) / (2 * k)
            total += term
        a = s * total
    return 0.5 + a / 2

def t_quantile(p: float, df: int) -> float:
    """The t whose CDF is p (0.5 < p < 1), by bisection on t_cdf down to adjacent doubles (deterministic)."""
    if not 0.5 < p < 1:
        raise ValueError("p must lie in (0.5, 1)")
    lo, hi = 0.0, 1.0
    while t_cdf(hi, df) < p:
        lo, hi = hi, hi * 2
    for _ in range(2000):
        mid = (lo + hi) / 2
        if mid in (lo, hi):
            break
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return hi

def excludes_zero(diff: Fraction, se2: Fraction, t: Fraction):
    """'above' when diff +- t SE lies wholly above 0, 'below' when wholly below, else None. Exact on squares:
    |diff| > t SE <=> diff^2 > t^2 SE^2 (an endpoint at exactly 0 does not exclude 0)."""
    if diff * diff > t * t * se2:
        return "above" if diff > 0 else "below"
    return None

def inside_margin(diff: Fraction, se2: Fraction, t: Fraction, margin: Fraction) -> bool:
    """diff +- t SE lies strictly inside (-margin, +margin), i.e. margin - |diff| > t SE; exact on squares."""
    gap = margin - abs(diff)
    return gap > 0 and gap * gap > t * t * se2

def pooled_t(x, y, margin=None, other_margin=None) -> dict:
    """Two-sample t interval on per-seed values (pp) with a pooled SD: diff = mean x - mean y, df = n1 + n2 - 2,
    SE^2 = s_p^2 (1/n1 + 1/n2), interval diff +- t SE at 95% (t at 0.975) and at 90% (t at 0.95)."""
    x, y = [Fraction(v) for v in x], [Fraction(v) for v in y]
    n1, n2 = len(x), len(y)
    if n1 < 2 or n2 < 2:
        raise ValueError("each group needs at least two values")
    m1, m2 = mean(x), mean(y)
    diff, df = m1 - m2, n1 + n2 - 2
    sp2 = (sum((v - m1) ** 2 for v in x) + sum((v - m2) ** 2 for v in y)) / df
    se2 = sp2 * (Fraction(1, n1) + Fraction(1, n2))
    t95, t90 = t_quantile(0.975, df), t_quantile(0.95, df)
    se = math.sqrt(se2)
    out = {"diff_pp": float(diff), "diff_exact": str(diff), "mean_pp": [float(m1), float(m2)],
           "per_seed_pp": [[float(v) for v in x], [float(v) for v in y]], "n": [n1, n2], "df": df,
           "sd_pooled_pp": math.sqrt(sp2), "se_pp": se, "t95": t95, "t90": t90,
           "ci95_pp": [float(diff) - t95 * se, float(diff) + t95 * se],
           "ci90_pp": [float(diff) - t90 * se, float(diff) + t90 * se],
           "ci95_excludes_0": excludes_zero(diff, se2, Fraction(t95)),
           "margin_pp": None if margin is None else float(margin),
           "ci90_inside_margin": None, "ci90_inside_other_margin": None}
    if margin is not None:
        out["ci90_inside_margin"] = inside_margin(diff, se2, Fraction(t90), Fraction(margin))
    if other_margin is not None:
        out["ci90_inside_other_margin"] = inside_margin(diff, se2, Fraction(t90), Fraction(other_margin))
    return out

def outcome_of(u: dict, hb: dict, inside_key: str = "ci90_inside_margin") -> str:
    """'both', 'matters', 'within' or 'none' (PREREG §4, both judges together; 'both' takes precedence)."""
    matters = u["ci95_excludes_0"] is not None and u["ci95_excludes_0"] == hb["ci95_excludes_0"]
    within = u[inside_key] is True and hb[inside_key] is True
    return "both" if matters and within else "matters" if matters else "within" if within else "none"

def label_of(u: dict, hb: dict, contrast: str = "content", inside_key: str = "ci90_inside_margin") -> str:
    """The label of one contrast in that contrast's own names (the Dolly contrast never reuses the content names)."""
    name = LABEL_NAMES[contrast][outcome_of(u, hb, inside_key)]
    if name == DOLLY_DIFFERS:
        name = name.format("higher" if u["ci95_excludes_0"] == "above" else "lower")
    return name
