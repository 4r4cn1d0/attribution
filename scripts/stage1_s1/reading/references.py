"""The reference tests: "m beats r", the adapter-scaling curve matched on task loss, dominance (family 1b) and
the 3-seed fallback (REV3 section 5.3 with LN-15b's revised curve switch; AMD D.1-D.4; review-statistics ST-1, ST-12).

"m beats r" (one reference at one point, over the common seeds): all three bounds hold, each read at the upper
end of the two-sided 90% interval (one-sided 5%): U(m) - U(r) < 0; O(m) - O(r) < m_O = 5 pp; L(m) - L(r) < tau_L.
Levels, not contrasts against each arm's comparator. "r beats m" by the mirror rule.

Variance (AMD D.2 under HB-C): one fit per reference point on the full-corpus repair arms plus r, a0 left out, r in
the full-corpus cluster; a full-corpus repair against r uses that fit; a removal arm against any full-corpus
reference uses the pair's own paired variance (J - 1 df); each plus the item part. Against AS(1) = a0: the primary
form (``Context.vs_a0``); against AS(0) = theta0: LN-20 item 1.

The curve matched on L (LN-15b revised): lambda* = 1 only if L(m) - L(a0) is shown feasible at tau_L (upper 90% end
<= tau_L); then both bounds are tested against a0. Otherwise read the curve of mean L against lambda (piecewise
linear; the first crossing from lambda = 1 down) at the upper end (lambda_up) and the lower end (lambda_dn; 1 if
the lower end <= 0); test the U bound against AS(lambda_lo), the largest grid lambda at or below lambda_up, and the
O bound against AS(lambda_hi), the smallest grid lambda at or above lambda_dn. The L bound is not tested against
the curve; L(m) - L(AS(lambda_hi)) is printed with its interval, and the interpolated point beside it.

Dominance (AMD D.4): D_k = "m_k beats every built reference", an IUT whose p-value is the largest component
one-sided p-value; Holm over the contrasts' D_k at 5%, read after Phi. Per-reference results are per comparison.

The 3-seed fallback: a reference whose common seeds with the method arms number fewer than 3 is tested with S-aW
per pair (unpaired Welch over all seeds of each arm), "beats" is descriptive, family 1b is not tested, and no
sentence says that a data repair dominates or beats model-level repair.
"""

from __future__ import annotations

import numpy as np

from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import phi, reml, tdist
from scripts.stage1_s1.reading.settings import Design, settings
from scripts.stage1_s1.reading.settings import alpha as settings_alpha

BOUNDS = ("U", "O", "L")


def margins() -> dict:
    cfg = settings()
    return {"U": float(cfg["beats"]["u_margin"]), "O": float(cfg["beats"]["m_o_pp"]), "L": float(cfg["tau_l"]["nats"])}


def min_common() -> int:
    return int(settings()["beats"]["fallback_min_common_seeds"])


def merge(table: dict, ref_table: dict) -> dict:
    merged = dict(table)
    merged.update(ref_table)
    return merged


def is_fallback(dsg: Design, r_seeds) -> bool:
    """The 3-seed fallback: fewer than 3 common seeds between the reference and the method arms."""
    return min(len(set(dsg.seeds[a]) & set(r_seeds)) for a in dsg.repair_arms) < min_common()


def bound_level() -> float:
    """The two-sided level whose upper end is the bounds' one-sided 5% bound (settings beats.one_sided)."""
    return 1.0 - 2.0 * float(settings()["beats"]["one_sided"])


def reference_fit(merged, dsg: Design, r: str, r_seeds, scale, floor, cfg: dict | None = None):
    """HB-C on the full-corpus repair arms plus r (a0 out, r in the full cluster); None when no full-corpus repair
    arm or under the fallback. The REML stop settings and floor mode come from the pinned settings."""
    members = tuple(a for a in dsg.repair_arms if dsg.cluster[a] == "full")
    if not members or is_fallback(dsg, r_seeds):
        return None
    cells = [(a, j, con.cell_value(merged, a, j, scale)) for a in members for j in dsg.seeds[a]]
    cells += [(r, j, con.cell_value(merged, r, j, scale)) for j in r_seeds]
    return reml.fit_cells(cells, members + (r,), floor, **reml.options(cfg or settings()))


def welch_fallback(merged, dsg: Design, m, r, r_seeds, scale) -> con.Estimate:
    """S-aW per pair (descriptive): Welch over all seeds of each arm; the item part from the common seeds when at
    least two exist, else the seed part only."""
    common = tuple(sorted(set(dsg.seeds[m]) & set(r_seeds)))
    form = "S-aW (3-seed fallback, descriptive)"
    if len(common) >= 2:
        return con.contrast_welch(merged, m, r, dsg.seeds[m], tuple(r_seeds), common, scale, True, f"{m}-{r}", form)
    vm, vr = con.arm_values(merged, m, dsg.seeds[m], scale), con.arm_values(merged, r, tuple(r_seeds), scale)
    v = float(vm.var(ddof=1)) / len(vm) + float(vr.var(ddof=1)) / len(vr)
    df = tdist.welch_df(float(vm.var(ddof=1)), len(vm), float(vr.var(ddof=1)), len(vr))
    return con.Estimate(f"{m}-{r}", form + "; no common seed: seed part only", float(vm.mean() - vr.mean()), float(np.sqrt(v)),
                        float(df), v, float(df), 0.0, 0.0, 0, int(merged[(m, dsg.seeds[m][0])].shape[0]), False)


def pair_estimate(merged, dsg: Design, m, r, r_seeds, fit, scale) -> con.Estimate:
    """m against r (est = v(m) - v(r)) in the rule's form (AMD D.2; the fallback)."""
    if is_fallback(dsg, r_seeds):
        return welch_fallback(merged, dsg, m, r, r_seeds, scale)
    common = tuple(sorted(set(dsg.seeds[m]) & set(r_seeds)))
    if dsg.cluster[m] == "full" and fit is not None:
        return con.contrast_fit(merged, fit, m, r, common, scale, True, f"{m}-{r}", "reference fit (HB-C)")
    return con.contrast_paired(merged, m, r, common, scale, True, f"{m}-{r}", "paired (J - 1 df; cross-cluster)")


def bound_result(est: con.Estimate, margin: float) -> dict:
    lo, hi = est.interval(bound_level())
    return {"estimate": est.as_dict(), "margin": margin, "interval_90": [lo, hi], "holds": bool(hi < margin),
            "p_one_sided": est.p_lower(margin)}


def beats_point(ctx, m: str, r_name: str, r_tables: dict, r_seeds, fits: dict) -> dict:
    """The three bounds of m against one reference point; fits: endpoint -> the reference fit (or None)."""
    dsg, scale, mg = ctx.design, ctx.scale, margins()
    bounds = {}
    for e in BOUNDS:
        est = pair_estimate(merge(ctx.tables[e], r_tables[e]), dsg, m, r_name, r_seeds, fits.get(e), scale[e])
        bounds[e] = bound_result(est, mg[e])
    fallback = is_fallback(dsg, r_seeds)
    return {"reference": r_name, "repair": m, "kind": "point", "common_seeds": sorted(set(dsg.seeds[m]) & set(r_seeds)),
            "fallback_3_seed": fallback, "descriptive": fallback, "bounds": bounds,
            "beats": all(b["holds"] for b in bounds.values()), "p_iut": max(b["p_one_sided"] for b in bounds.values()),
            "r_beats_m": all(-b["interval_90"][0] < mg[e] for e, b in bounds.items())}


def curve_rise(ctx, ref, theta0_l: np.ndarray) -> dict:
    """Mean L at each lambda (1 = a0, 0 = theta0, the grid points from the reference) minus a0's mean."""
    dsg, s = ctx.design, ctx.scale["L"]
    a0_mean = float(con.arm_values(ctx.tables["L"], "a0", dsg.seeds["a0"], s).mean())
    rise = {1.0: 0.0, 0.0: float(s * np.mean(theta0_l) - a0_mean)}
    for lam, tables in ref.tables.items():
        rise[lam] = float(con.arm_values(merge(ctx.tables["L"], tables["L"]), ref.name, ref.seeds, s).mean() - a0_mean)
    return rise


def lambda_at(rise: dict, target: float) -> float:
    """The first lambda from 1 down where the piecewise-linear rise reaches the target; 1 if the target is at or
    below 0; 0 if the target lies above the whole curve."""
    if target <= 0.0:
        return 1.0
    lams = sorted(rise, reverse=True)
    for a, b in zip(lams, lams[1:]):
        ra, rb = rise[a], rise[b]
        if ra == rb:
            if ra == target:
                return float(a)
            continue
        if min(ra, rb) <= target <= max(ra, rb):
            return float(b + (target - rb) / (ra - rb) * (a - b))
    return 0.0


def grid_bracket(lam_up: float, lam_dn: float, grid) -> tuple[float, float]:
    g = sorted(float(x) for x in grid)
    lo = max([x for x in g if x <= lam_up + 1e-12], default=g[0])
    hi = min([x for x in g if x >= lam_dn - 1e-12], default=g[-1])
    return lo, hi


def beats_curve(ctx, m: str, ref, l_vs_a0: con.Estimate, theta0_u: np.ndarray, theta0_l: np.ndarray) -> dict:
    """The adapter-scaling curve matched on L (LN-15b revised), for one repair m."""
    cfg = settings()["beats"]
    dsg, scale, mg = ctx.design, ctx.scale, margins()
    lo_l, up_l = l_vs_a0.interval(bound_level())
    rise = curve_rise(ctx, ref, theta0_l)
    if up_l <= mg["L"]:
        lam_up = lam_dn = lam_lo = lam_hi = 1.0
        switch = "lambda* = 1: L(m) - L(a0) shown feasible at tau_L; both bounds against AS(1) = a0"
    else:
        lam_up, lam_dn = lambda_at(rise, up_l), lambda_at(rise, lo_l)
        lam_lo, lam_hi = grid_bracket(lam_up, lam_dn, cfg["lambda_grid"])
        switch = "matched on L: lambda_lo at the upper end and lambda_hi at the lower end of the L interval"
    fallback = is_fallback(dsg, ref.seeds)

    def against(lam: float, e: str) -> con.Estimate:
        if lam == 1.0:
            return ctx.vs_a0(e, m)
        if lam == 0.0:
            theta = {"U": theta0_u, "O": ctx.theta0_o, "L": theta0_l}[e]
            return con.contrast_theta0(ctx.tables[e], m, dsg.seeds[m], theta, scale[e], True, f"{m}-AS(0)",
                                       "theta0 (LN-20 item 1)")
        merged = merge(ctx.tables[e], ref.tables[lam][e])
        fit = reference_fit(merged, dsg, ref.name, ref.seeds, scale[e], ctx.floor[e])
        return pair_estimate(merged, dsg, m, ref.name, ref.seeds, fit, scale[e])

    u_bound = bound_result(against(lam_lo, "U"), mg["U"])
    o_bound = bound_result(against(lam_hi, "O"), mg["O"])
    l_print = against(lam_hi, "L")
    return {"reference": ref.name, "repair": m, "kind": "curve", "switch": switch, "l_vs_a0": l_vs_a0.as_dict(),
            "l_interval_90": [lo_l, up_l], "rise_curve": {f"{k:g}": v for k, v in sorted(rise.items(), reverse=True)},
            "lambda_up": lam_up, "lambda_dn": lam_dn, "lambda_lo": lam_lo, "lambda_hi": lam_hi,
            "bounds": {"U": u_bound, "O": o_bound}, "l_against_lambda_hi": l_print.as_dict(),
            "l_interval_against_lambda_hi": list(l_print.interval(bound_level())), "l_interpolated_rise_at_lambda_up": up_l,
            "beats": bool(u_bound["holds"] and o_bound["holds"]), "p_iut": max(u_bound["p_one_sided"], o_bound["p_one_sided"]),
            "fallback_3_seed": fallback, "descriptive": fallback,
            "level_note": "approximately 5%: the U bound's 5% plus at most a 5% chance of a wrong bracket (ST-1)"}


def dominance(per_repair: dict, contrasts, alpha: float | None = None) -> dict:
    """Family 1b: D_k over the contrasts' repairs; Holm at Phi's alpha (5%); not tested when any reference is in the
    fallback. A repair that does not beat every reference never dominates: the coherence block of the reading sets a
    failing arm's p_iut to 1 (REV3 3.7 item 5; verify-code F1), and this function keeps the two fields consistent."""
    alpha = float(settings_alpha()) if alpha is None else alpha
    results, any_fallback = {}, False
    for name, _, m in contrasts:
        points = per_repair.get(m, [])
        if not points:
            continue
        any_fallback |= any(p["fallback_3_seed"] for p in points)
        results[name] = {"repair": m, "p_iut": max(p["p_iut"] for p in points),
                         "beats_every_reference": all(p["beats"] for p in points),
                         "references": [p["reference"] for p in points]}
    if not results:
        return {"tested": False, "reason": "no reference", "contrasts": {}}
    if any_fallback:
        return {"tested": False, "reason": "3-seed fallback: 'beats' is descriptive; family 1b is not tested; no sentence "
                                           "says that a data repair dominates or beats model-level repair", "contrasts": results}
    rejected = phi.holm({k: v["p_iut"] for k, v in results.items()}, alpha)
    for k in results:
        results[k]["dominates"] = k in rejected and results[k]["beats_every_reference"]
    return {"tested": True, "alpha": alpha, "contrasts": results}
