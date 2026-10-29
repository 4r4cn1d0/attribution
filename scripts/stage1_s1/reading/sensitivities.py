"""The sensitivity analyses (REV3 section 3.4; LW-01, LW-02; LN-37 S-p; LN-38 S-tok). Reported; they never change a
label. Each gives the U contrasts of the design in its own form; the reading prints a sensitivity's label beside
the primary's when they differ.

- HB: one seed shift for all fit arms, REML arm variances (AMD A.3), crossed item part.
- S-a: unpaired means over all seeds of each arm, one variance pooled over the arms, df n - A (PLAN-S:102); its
  equal-variance flag when S-a rejects and S-aW does not (LW-02). S-a's O and L tests (REV3 3.4; LW-02 S-1): the O
  and L comparator parts and L's a0 part by the per-contrast Welch form, O's theta0 part by LW-33's pooled form.
  Under plan B the pooled variance runs over every arm with cells, a0 included (a0 is outside the HB-C fit, but S-a
  is "pooled over the arms"; a reading the record states: verify-stats N3 (c)).
- S-aW: unpaired Welch.
- S-b2x: seed-blocked with one shift for all arms and one pooled residual (36 residual df under D1), plus the item part.
- S-0: the primary model (HB-C) without its item part ("on these prompts").
- S-G: HB-C on coherent-only U and on the two G3 corners (the input's U variants).
- S-p: the per-contrast paired t on the common seeds (J - 1 df) plus the item part.
- S-A8: AMD A.8's theta0 and in-model cross-cluster SEs ("seed shift omitted"), beside LN-20's (in ``reading``).
- S-tok: removal arms on the token axis (REV3 9.3 item 2): Lambda_tok,m = G_m - G_R(T_m) with the curve by the
  primary estimator; the interval on the common seeds 1102-1104 with every arm paired (LN-38); report only.
The item part of an unpaired form (S-a, S-aW) is read from the common-seed difference table.
"""

from __future__ import annotations

import numpy as np

from scripts.stage1.dose_axis import BEYOND, curve, random_restoration
from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import reml, tdist
from scripts.stage1_s1.reading.settings import Design, Refusal, level_per_comparison, settings


def _cells(table, arms, seeds, scale):
    """The cells present in the table for these arms (O may hold fewer R seeds than the design: LN-12)."""
    return [(arm, j, con.cell_value(table, arm, j, scale)) for arm in arms for j in seeds[arm] if (arm, j) in table]


def fit_one_shift(table, dsg: Design, scale, floor, cfg: dict | None = None) -> reml.RemlFit:
    """HB: one REML fit over the fit arms with one seed effect for all of them; the stop settings and floor mode
    from the pinned settings (``cfg`` is a settings document; the tests pass their own)."""
    return reml.fit_cells(_cells(table, dsg.fit_arms, dsg.seeds, scale), dsg.fit_arms, floor, **reml.options(cfg or settings()))


def fit_clusters(table, dsg: Design, scale, floor, arms=None, cfg: dict | None = None) -> dict:
    """HB-C: one REML fit per design cluster over the (given or fit) arms; a two-arm cluster takes the sum rule.
    tol, max_iter, the step clip and the floor mode come from the settings' 'reml' block (verify-stats F4)."""
    arms = tuple(arms) if arms is not None else dsg.fit_arms
    opts = reml.options(cfg or settings())
    fits = {}
    for cluster in ("full", "removal"):
        members = tuple(a for a in arms if dsg.cluster[a] == cluster)
        if len(members) >= 2:
            fits[cluster] = reml.fit_cells(_cells(table, members, dsg.seeds, scale), members, floor, **opts)
    return fits


def _seeds_of(table, arm):
    return tuple(sorted(j for a, j in table if a == arm))


def u_estimates(code: str, table, dsg: Design, scale, floor, cluster_fits: dict, cfg: dict | None = None,
                fits_out: dict | None = None) -> dict:
    """The U contrasts of one sensitivity: contrast name -> Estimate. ``fits_out`` receives HB's fit (its D-4 start
    record is printed)."""
    out = {}
    seeds_all = {arm: _seeds_of(table, arm) for arm in dsg.arms}
    if code == "HB":
        fit = fit_one_shift(table, dsg, scale, floor, cfg)
        for name, c, m in dsg.contrasts:
            out[name] = con.contrast_fit(table, fit, c, m, dsg.common_seeds(c, m), scale, True, name, "HB")
        if fits_out is not None:
            fits_out["HB"] = fit
    elif code == "S-a":
        for name, c, m in dsg.contrasts:
            out[name] = con.contrast_pooled(table, seeds_all, c, m, dsg.common_seeds(c, m), scale, True, name)
    elif code == "S-aW":
        for name, c, m in dsg.contrasts:
            out[name] = con.contrast_welch(table, c, m, seeds_all[c], seeds_all[m], dsg.common_seeds(c, m), scale, True, name)
    elif code == "S-b2x":
        s2, df = con.blocked_variance(table, seeds_all, scale)
        for name, c, m in dsg.contrasts:
            out[name] = con.contrast_blocked(table, c, m, dsg.common_seeds(c, m), s2, df, scale, True, name)
    elif code == "S-0":
        for name, c, m in dsg.contrasts:
            fit = cluster_fits[dsg.cluster[c]]
            out[name] = con.contrast_fit(table, fit, c, m, dsg.common_seeds(c, m), scale, False, name, "HB-C, no item part")
    elif code == "S-p":
        for name, c, m in dsg.contrasts:
            out[name] = con.contrast_paired(table, c, m, dsg.common_seeds(c, m), scale, True, name, "S-p paired t")
    else:
        raise Refusal(f"no U-contrast sensitivity named {code!r}")
    return out


def variant_estimates(variants: dict, dsg: Design, scale, floor, cfg: dict | None = None, fits_out: dict | None = None) -> dict:
    """S-G: HB-C refitted on each U variant table: variant name -> contrast name -> Estimate. ``fits_out`` receives
    each variant's cluster fits (their D-4 start records are printed)."""
    out = {}
    for vname, table in variants.items():
        fits = fit_clusters(table, dsg, scale, floor, cfg=cfg)
        if fits_out is not None:
            fits_out[vname] = fits
        out[vname] = {name: con.contrast_fit(table, fits[dsg.cluster[c]], c, m, dsg.common_seeds(c, m), scale, True, name, f"S-G {vname}")
                      for name, c, m in dsg.contrasts}
    return out


def equal_variance_flag(s_a: con.Estimate, s_aw: con.Estimate, level: float) -> bool:
    """LW-02 at one fixed level: S-a rejects at the level and S-aW does not. The reading reads the flag from the
    rejection sets of the two Phi runs instead (the local level moves with the graph; verify-code F9)."""
    return s_a.p_two_sided() <= level < s_aw.p_two_sided()


def s_a_side_effects(tables: dict, dsg: Design, scale: dict, theta0_o, min_o_seeds: int) -> dict:
    """S-a's O and L tests (REV3 3.4; LW-02 S-1; 3.6 item 3): per contrast the O comparator part m - c and the L
    comparator part m - c by the per-contrast Welch form over all seeds of each arm (the item part from the common
    seeds; O's from the O seeds present, 'not tested' below ``min_o_seeds`` as LN-12), L's a0 part m - a0 by Welch,
    and O's theta0 part by LW-33's form (s^2_pool,O over the arms' O cells / J_m + the item part). Contrast name ->
    {"O_comp", "O_theta", "L_comp", "L_a0"} (O_comp None when not tested)."""
    out = {}
    seeds = {e: {arm: _seeds_of(tables[e], arm) for arm in dsg.arms} for e in ("O", "L")}
    for name, c, m in dsg.contrasts:
        o_common = tuple(sorted(set(seeds["O"][c]) & set(seeds["O"][m])))
        o_comp = None
        if len(o_common) >= min_o_seeds:
            o_comp = con.contrast_welch(tables["O"], m, c, seeds["O"][m], seeds["O"][c], o_common, scale["O"], True, f"{m}-{c}", "S-a Welch")
        o_theta = con.contrast_theta0_pooled(tables["O"], seeds["O"], m, seeds["O"][m], theta0_o, scale["O"], f"{m}-theta0")
        l_common = tuple(sorted(set(seeds["L"][c]) & set(seeds["L"][m])))
        l_comp = con.contrast_welch(tables["L"], m, c, seeds["L"][m], seeds["L"][c], l_common, scale["L"], True, f"{m}-{c}", "S-a Welch")
        if c == "a0":
            l_a0 = l_comp
        else:
            a0_common = tuple(sorted(set(seeds["L"]["a0"]) & set(seeds["L"][m])))
            l_a0 = con.contrast_welch(tables["L"], m, "a0", seeds["L"][m], seeds["L"]["a0"], a0_common, scale["L"], True, f"{m}-a0", "S-a Welch")
        out[name] = {"O_comp": o_comp, "O_theta": o_theta, "L_comp": l_comp, "L_a0": l_a0}
    return out


def _restoration(table, dsg: Design, arm, seeds, scale):
    """G = U(a0) - U(arm) on the given seeds (the primary estimator's paired mean; the interval is the caller's)."""
    return con.paired_mean(table, "a0", arm, seeds, scale)


def token_axis(table, dsg: Design, scale, axis: dict) -> dict:
    """S-tok for each removal arm with a removed mass (REV3 9.3 item 2; LN-38). The curve points are the primary
    estimator's: G_600 over a0 and R's common seeds, G_1200 and G_2400 over the dose draws' seeds (1102-1104);
    Lambda_tok = G_m - G_R(T_m). The interval re-reads every point on the common seeds, paired per seed."""
    cfg = settings()["token_axis"]
    common = tuple(cfg["common_seeds"])
    merged = dict(table)
    merged.update(axis["cells"])
    g_600 = _restoration(merged, dsg, "R", dsg.common_seeds("a0", "R"), scale)
    g_dose = {600: g_600, 1200: _restoration(merged, dsg, "R_1200", common, scale),
              2400: _restoration(merged, dsg, "R_2400", common, scale)}
    points = curve(axis["masses"], g_dose)
    out = {"axis": axis["axis"], "curve": [list(p) for p in points], "common_seeds": list(common), "arms": {}}
    for arm, t_m in axis["removed"].items():
        g_m = _restoration(merged, dsg, arm, dsg.common_seeds("a0", arm), scale)
        g_r = random_restoration(points, t_m)
        rec = {"t_m": t_m, "g_m": g_m, "g_random_at_t_m": g_r, "first_segment_only": 0 < t_m < points[1][0]}
        if g_r == BEYOND:
            rec.update({"lambda_tok": BEYOND, "interval_90": None})
        else:
            per_seed = []
            for j in common:
                cell = lambda a: con.cell_value(merged, a, j, scale)
                g_j = {600: cell("a0") - cell("R"), 1200: cell("a0") - cell("R_1200"), 2400: cell("a0") - cell("R_2400")}
                try:
                    pts_j = curve(axis["masses"], g_j)
                    gr_j = random_restoration(pts_j, t_m)
                except ValueError:
                    gr_j = BEYOND
                per_seed.append(float("nan") if gr_j == BEYOND else (cell("a0") - cell(arm)) - gr_j)
            d = np.array(per_seed)
            ok = np.all(np.isfinite(d))
            se = float(d.std(ddof=1) / np.sqrt(len(d))) if ok else float("nan")
            # the two-sided per-comparison level from the settings (intervals.per_comparison), not a second copy
            half = tdist.t_quantile(0.5 + level_per_comparison() / 2.0, len(d) - 1) * se if ok and se > 0 else float("nan")
            rec.update({"lambda_tok": g_m - g_r, "per_seed_lambda_tok": d.tolist(), "se_common_seeds": se,
                        "df": len(d) - 1, "interval_90": [g_m - g_r - half, g_m - g_r + half] if ok else None,
                        "interval_note": "centred on the point estimate; half-width from the common seeds 1102-1104, every arm paired (LN-38)"})
        out["arms"][arm] = rec
    return out
