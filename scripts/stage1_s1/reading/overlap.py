"""Section 9.4's overlap control under the primary model: HB-C of the halves (REV4 9.4 with LN-26; addendum 11
point 11, 24 point 4, 32 point 4, 33; LW-01; LN-35; LN-37; post-W1 deviation D-4). Report only: it changes no label,
no Phi node and no headline word.

The rule (REV4 9.4, the frozen W1 text, LN-26 adopted as written): "Each evaluation prompt's highest similarity to
the add set (theta0 embeddings). 'Holds' = the add contrast on the lower-similarity half has the same sign as on all
prompts and its 90% interval excludes 0; else the text says 'not shown on the less similar half'."

The contrasts (addendum 33 point 1): the add effect against a0 governs, a0 - m for each add arm of the reading
(plan A and block A only: S1, S3, S4; plan B: S1, S4), each on its own add set's halves (B14's orientation). The
primary family's orientation (P4 = a0 - S1, P5 = S1 - S3, P6 = S1 - S4; plan B P6) is printed beside it, labelled
report only.

The halves (addendum 33 point 3): B14's sealed split, read from B14's own strata and report documents that the input
embeds and that the schema checks by SHA-256 (``schema._overlap``): k = floor(n / 2), b = the (k + 1)-th smallest S;
lower = {S < b}, higher = {S >= b}; ties at b go to the higher half. The U items are in the strata's prompt-id order,
and the U table at the halves' positions must reproduce the report's ``cells_u_pp``.

The model (addendum 11 point 11): HB-C as the primary reading fits it (REV4 3.2), refitted on each half. The U cells of
every fit arm of the full-corpus cluster are recomputed on the half's prompts; the cluster is fitted by REML with the
U floor, LN-35's stop rule and floor mode, and D-4's starts (the pre-registered start and every floor pattern; the
highest REML log-likelihood governs); the estimate is the paired mean on the common seeds; the seed part is the REML
(sigma^2_c + sigma^2_m) / J with its Satterthwaite df from the information; the item part comes from the J x P_h
table on the half; df by Satterthwaite; the 90% interval. On all prompts it equals the primary U contrast (tested).
A pair that is not inside one fit (a0 under plan B) takes LN-20 item 2's paired form, as the primary reading does;
under plan B the two-arm cluster {S1, S4} takes the sum rule (REV4 3.5).

S-p (LN-37; addendum 11 point 11): B14's per-contrast paired form (the J - 1 df paired seed part plus the item
part, ``overlap_strata.contrast``) on the same halves, with its own verdict, printed as the S-p sensitivity; for the
governing contrasts it equals B14's printed S-p. D-4's sensitivity: HB-C from the pre-registered start's own fits
with its verdict, beside the governing one. The HB-C verdict governs the text.

Readings (each in the settings' ``overlap`` block, printed in the output): a sign within ``sign_tolerance_pp`` of 0
is 0 and a sign of 0 never matches; "excludes 0" is strict (an interval end at exactly 0 does not exclude it); a half
with fewer than ``min_prompts`` prompts, or whose fit or variance does not exist, is "not computable" and its verdict
is "not shown". The higher half is printed for completeness; the rule reads only the lower half and all prompts. A
fit that stops at the 25-step limit is used as the primary reading uses it (LN-35); the HB-C verdict says whether
the fits behind it (all prompts and the lower half) met the tolerance (``fits_converged``). A block-A-only reading's
verdict texts carry the design's label suffix (addendum 33 point 4).
"""

from __future__ import annotations

import numpy as np

from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import sensitivities
from scripts.stage1_s1.reading.reml import RemlError
from scripts.stage1_s1.reading.settings import Design, Refusal

HALVES = ("all", "lower", "higher")
COMPARATORS = ("primary", "a0")
HBC, S_P, HBC_PRE = "HB-C", "S-p", "HB-C, pre-registered start"


def add_sets(dsg: Design) -> tuple[str, ...]:
    """The design's add arms, in design order (plan A: S1, S3, S4; plan B: S1, S4)."""
    return tuple(arm for arm in dsg.arms if dsg.kind[arm] == "add")


def contrasts(dsg: Design, cfg: dict, mode: str | None = None) -> tuple:
    """((name, comparator, repair), ...): section 9.4's add contrasts under a comparator reading (default: the
    governing one, settings overlap.comparator = "a0", addendum 33 point 1). The half of each is its repair arm's
    add set."""
    mode = mode or cfg["overlap"]["comparator"]
    if mode == "primary":
        return tuple((name, c, m) for name, c, m in dsg.contrasts if dsg.kind[m] == "add")
    if mode == "a0":
        return tuple((f"a0-{m}", "a0", m) for m in add_sets(dsg))
    raise Refusal(f"the settings' overlap.comparator is not one of {COMPARATORS}")


def restrict(table: dict, idx: np.ndarray) -> dict:
    """The table with every item vector cut to the half's positions."""
    return {key: items[idx] for key, items in table.items()}


def sign(x: float, tol: float) -> int:
    """The sign, with |x| <= tol read as 0 (settings overlap.sign_rule)."""
    return 0 if abs(x) <= tol else (1 if x > 0 else -1)


def _within(dsg: Design, table: dict, fits: dict, c: str, m: str, scale: float, name: str, form: str) -> con.Estimate:
    """The primary form, exactly as the reading's Context.within: the cluster fit when both arms are fit arms of one
    cluster (REV4 3.2), else the pair's own paired variance on the common seeds (LN-20 item 2)."""
    common = dsg.common_seeds(c, m)
    if dsg.in_fit(c) and dsg.in_fit(m) and dsg.same_cluster(c, m):
        return con.contrast_fit(table, fits[dsg.cluster[c]], c, m, common, scale, True, name, form)
    return con.contrast_paired(table, c, m, common, scale, True, name, "paired (J - 1 df; LN-20 item 2)")


def _fit_record(fit) -> dict:
    """A fit with D-4's start record: the governing start, the number of starts, the flag, and the pre-registered
    start's own end point (its variances, floored arms, steps and REML log-likelihood) beside it."""
    rec = {"arms": list(fit.arms), "sigma2": fit.sigma2, "at_floor": list(fit.at_floor), "iterations": fit.iterations,
           "converged": fit.converged, "two_arm": fit.two_arm, "pairs": fit.pairs, "residual_df": fit.residual_df,
           "floor": fit.floor, "loglik": fit.loglik, "starts": fit.starts, "governing_start": fit.governing_start,
           "start_differs": fit.start_differs}
    if fit.prereg is not None:
        pre = fit.prereg
        rec["prereg_start"] = {"sigma2": pre.sigma2, "at_floor": list(pre.at_floor), "iterations": pre.iterations,
                               "converged": pre.converged, "loglik": pre.loglik}
    return rec


def prereg_fits(fits: dict) -> dict:
    """The pre-registered start's own fits (D-4's sensitivity): each cluster's ``prereg`` where the multi-start ran."""
    return {cl: (f.prereg if f.prereg is not None else f) for cl, f in fits.items()}


def _fit_half(table_h: dict, dsg: Design, scale: float, floor: float, cfg: dict):
    """HB-C's full-corpus cluster refitted on one half (the fit arms of that cluster; LN-35's floor and stop rule,
    D-4's starts): (fits, record, reason). A fit that does not exist gives (None, None, reason)."""
    try:
        fits = sensitivities.fit_clusters(table_h, dsg, scale, floor, arms=dsg.cluster_arms("full"), cfg=cfg)
    except RemlError as exc:
        return None, None, f"the REML fit on this half does not exist ({exc})"
    return fits, {cl: _fit_record(f) for cl, f in fits.items()}, None


def _form(estimate_of, level: float) -> dict:
    try:
        e = estimate_of()
    except (Refusal, RemlError) as exc:
        return {"computable": False, "reason": str(exc)}
    lo, hi = e.interval(level)
    return {"computable": True, "estimate": e.as_dict(), "interval_90": [lo, hi]}


def _half(dsg, table_h, fits, fit_reason, c, m, scale, level, name, prompts, min_prompts) -> dict:
    """One half of one contrast: the paired mean, the HB-C and S-p estimates with their 90% intervals, and HB-C from
    the pre-registered start's fits when a start other than it governs there (D-4)."""
    if prompts == 0:
        reason = "the half holds no prompt"
        return {"prompts": 0, "paired_mean_pp": None, HBC: {"computable": False, "reason": reason},
                S_P: {"computable": False, "reason": reason}, HBC_PRE: {"computable": False, "reason": reason}}
    common = dsg.common_seeds(c, m)
    rec = {"prompts": prompts, "paired_mean_pp": con.paired_mean(table_h, c, m, common, scale)}
    if prompts < min_prompts:
        reason = f"the half holds {prompts} prompt(s), fewer than {min_prompts}: no item part exists"
        return {**rec, HBC: {"computable": False, "reason": reason}, S_P: {"computable": False, "reason": reason},
                HBC_PRE: {"computable": False, "reason": reason}}
    if fits is None:
        rec[HBC] = {"computable": False, "reason": fit_reason}
        rec[HBC_PRE] = {"computable": False, "reason": fit_reason}
    else:
        rec[HBC] = _form(lambda: _within(dsg, table_h, fits, c, m, scale, name, HBC), level)
        if any(f.start_differs for f in fits.values()):
            rec[HBC_PRE] = _form(lambda: _within(dsg, table_h, prereg_fits(fits), c, m, scale, name, HBC_PRE), level)
        else:
            rec[HBC_PRE] = {**rec[HBC], "same_as": HBC}
    rec[S_P] = _form(lambda: con.contrast_paired(table_h, c, m, common, scale, True, name, "S-p paired t"), level)
    return rec


def verdict(all_mean, lower: dict, texts: dict, tol: float) -> dict:
    """REV4 9.4: "holds" = the lower half's estimate has the all-prompt estimate's sign (a sign of 0 never matches)
    and the lower half's 90% interval excludes 0 (strictly); else "not shown on the less similar half"."""
    sign_all = sign(all_mean, tol) if all_mean is not None else 0
    if not lower.get("computable"):
        return {"holds": False, "text": texts["not_shown"], "sign_all": sign_all, "sign_lower": None,
                "reason": f"the lower-similarity half is not computable ({lower.get('reason')})"}
    sign_lower = sign(lower["estimate"]["est"], tol)
    lo, hi = lower["interval_90"]
    same = sign_all != 0 and sign_lower == sign_all
    excludes = lo > 0 or hi < 0
    holds = same and excludes
    if holds:
        reason = "same sign as on all prompts and the 90% interval excludes 0"
    elif not same:
        reason = "the sign differs from the all-prompt estimate's (or a sign is 0)"
    else:
        reason = "the 90% interval contains 0"
    return {"holds": holds, "text": texts["holds"] if holds else texts["not_shown"], "sign_all": sign_all,
            "sign_lower": sign_lower, "reason": reason}


def _suffixed(v: dict, suffix) -> dict:
    """Addendum 33 point 4: a block-A-only reading's verdict text carries the design's label suffix."""
    return {**v, "text": f"{v['text']} [{suffix}]"} if suffix else v


def read_halves(ov: dict, dsg: Design, table: dict, scale: float, floor: float, cfg: dict) -> dict:
    """The overlap control of one validated input (``ov`` is schema.Input.overlap). Governing (addendum 33 point 1):
    per add arm m, the add effect a0 - m on m's own halves: HB-C and S-p on all prompts and on each half, the HB-C
    verdict (the text), the S-p verdict, and the verdict from the pre-registered REML start's fits (D-4). Beside it,
    labelled report only, the primary family's orientation (P4-P6; plan B P6) on the repair arm's halves."""
    o = cfg["overlap"]
    level, tol, texts = float(o["interval"]), float(o["sign_tolerance_pp"]), o["texts"]
    min_prompts = int(o["min_prompts"])
    suffix = dsg.label_suffix
    items = len(next(iter(table.values())))
    positions = {"all": np.arange(items)}
    for m, block in ov["add_sets"].items():
        positions[f"{m} lower"], positions[f"{m} higher"] = block["lower"], block["higher"]
    cache, fit_records = {}, {}

    def half_fit(key):
        if key not in cache:
            table_h = restrict(table, positions[key])
            if len(positions[key]) >= min_prompts:
                fits, record, reason = _fit_half(table_h, dsg, scale, floor, cfg)
            else:
                fits, record, reason = None, None, f"the half holds {len(positions[key])} prompt(s), fewer than {min_prompts}"
            cache[key] = (table_h, fits, reason)
            fit_records[key] = record if record is not None else {"fitted": False, "reason": reason}
        return cache[key]

    def block_of(name, c, m, role):
        halves, differ = {}, []
        for h in HALVES:
            key = "all" if h == "all" else f"{m} {h}"
            table_h, fits, reason = half_fit(key)
            halves[h] = _half(dsg, table_h, fits, reason, c, m, scale, level, name, len(positions[key]), min_prompts)
            if fits is not None and any(f.start_differs for f in fits.values()):
                differ.append(key)
        all_mean = halves["all"]["paired_mean_pp"]
        v = {**verdict(all_mean, halves["lower"][HBC], texts, tol), "model": HBC,
             "fits_converged": all(bool(fit_records[key].get("full", {}).get("converged")) for key in ("all", f"{m} lower"))}
        v_p = {**verdict(all_mean, halves["lower"][S_P], texts, tol), "model": S_P, "role": o["s_p_label"]}
        v_0 = {**verdict(all_mean, halves["lower"][HBC_PRE], texts, tol), "model": HBC_PRE, "role": o["prereg_start_label"]}
        return {"role": role, "comparator": c, "repair": m, "add_set": m, "common_seeds": list(dsg.common_seeds(c, m)),
                "half_sizes": {h: halves[h]["prompts"] for h in HALVES}, "halves": halves,
                "verdict": _suffixed(v, suffix), "s_p_verdict": _suffixed(v_p, suffix), "s_p_differs": v_p["holds"] != v["holds"],
                "prereg_start_verdict": _suffixed(v_0, suffix), "fits_where_the_start_differs": differ,
                "prereg_start_differs": v_0["holds"] != v["holds"]}

    governing = contrasts(dsg, cfg)
    out = {name: block_of(name, c, m, o["governing_label"]) for name, c, m in governing}
    beside = {}
    for name, c, m in contrasts(dsg, cfg, o["report_only"]):
        rec = block_of(name, c, m, o["report_only_label"])
        rec["same_contrast_as"] = next((g for g, gc, gm in governing if (gc, gm) == (c, m)), None)
        beside[name] = rec
    used = {m for _, _, m in governing}
    return {"computed": True, "rule": o["rule"], "model": o["model"], "s_p": o["s_p"], "role": o["role"],
            "comparator": o["comparator"], "comparator_rule": o["comparator_rule"], "report_only": o["report_only"],
            "interval": level, "label_suffix": suffix,
            "readings": {k: o[k] for k in ("sign_rule", "excludes_rule", "halves_input", "starts_rule")},
            "strata_sha256": ov["strata_sha256"], "report_sha256": ov["report_sha256"],
            "contrasts": out, "report_only_contrasts": beside, "fits": fit_records,
            "add_sets_in_no_contrast": [m for m in add_sets(dsg) if m not in used]}
