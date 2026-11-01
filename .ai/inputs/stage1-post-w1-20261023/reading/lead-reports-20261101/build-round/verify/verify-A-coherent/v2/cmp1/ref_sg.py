"""Independent reference for S-G coherent (post-W1 deviation D-5) and the adverse G3(a) corners.

Written by the verifier from the lead's rulings (task text) and the review's section 2.3; it never imports
scripts.stage1_s1.reading_input (the builder's new code). It uses only frozen B16 pieces as black boxes:
settings/design (the sealed designs), reml.fit_cells with the pinned options (the REML fit itself: "as B16 computes
U"), phi.build_graph/run (the graph) and labels.u_part/headline (the word rules). Everything else is re-derived here:
the linearized table in exact fractions, which cells enter which fit, the choice between the cluster form and the
pair's paired form, the seed part from the fit's variances and information, the crossed prompt part, Satterthwaite
df, t p-values and quantiles by mpmath (40 digits), the Phi inputs, the corner tables.
"""

from __future__ import annotations

import math
from fractions import Fraction

import mpmath as mp
import numpy as np

from scripts.stage1_s1.reading import labels, phi, reml
from scripts.stage1_s1.reading.settings import alpha, design, settings

mp.mp.dps = 40
P_ITEMS = 200
DF_CAP = 1e7            # B16's tdist caps df at 1e7 (only matters for df above it)


# ----- t distribution (mpmath) ---------------------------------------------------------------------------------------

def t_p_two(t: float, df: float) -> float:
    df = min(df, DF_CAP)
    if t == 0:
        return 1.0
    x = mp.mpf(df) / (mp.mpf(df) + mp.mpf(t) ** 2)
    return float(mp.betainc(mp.mpf(df) / 2, mp.mpf(1) / 2, 0, x, regularized=True))


def t_quantile(q: float, df: float) -> float:
    """The q quantile (q > 1/2) by bisection on the mpmath CDF."""
    df = min(df, DF_CAP)
    target = mp.mpf(q)

    def cdf(t):
        x = mp.mpf(df) / (mp.mpf(df) + t * t)
        return 1 - mp.betainc(mp.mpf(df) / 2, mp.mpf(1) / 2, 0, x, regularized=True) / 2
    lo, hi = mp.mpf(0), mp.mpf(1)
    while cdf(hi) < target:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if cdf(mid) < target:
            lo = mid
        else:
            hi = mid
    return float((lo + hi) / 2)


# ----- the linearized table --------------------------------------------------------------------------------------------

def x_exact(n, u):
    """[x_p] as shares, each the correctly rounded float of the exact rational V + (u_p - V n_p) / N-bar."""
    big_n, big_u = int(sum(int(v) for v in n)), int(sum(int(v) for v in u))
    if big_n == 0:
        return None
    v = Fraction(big_u, big_n)
    nbar = Fraction(big_n, len(n))
    return np.array([float(v + (Fraction(int(ui)) - v * int(ni)) / nbar) for ni, ui in zip(n, u)])


def pooled_pp(n, u):
    big_n = int(sum(int(v) for v in n))
    return None if big_n == 0 else float(Fraction(100 * int(sum(int(v) for v in u)), big_n))


# ----- one contrast ------------------------------------------------------------------------------------------------

class NC(Exception):
    pass


def cell_value(x):
    return float(100.0 * x.mean())


def item_part(rows_shares: np.ndarray):
    """(V_item pp^2, q) of the J x P table of share differences (crossed prompts and seeds, no replication)."""
    d = 100.0 * rows_shares
    j, p = d.shape
    g = d.mean()
    rm = d.mean(axis=1, keepdims=True)
    cm = d.mean(axis=0, keepdims=True)
    ms_p = j * float(((cm - g) ** 2).sum()) / (p - 1)
    ms_e = float(((d - rm - cm + g) ** 2).sum()) / ((p - 1) * (j - 1))
    k = 1.0 / (p * j)
    v_item = max(0.0, ms_p - ms_e) * k
    q = ((ms_p * k) ** 2 / (p - 1) + (ms_e * k) ** 2 / ((p - 1) * (j - 1))) if ms_p > ms_e else 0.0
    return v_item, q


def finish(est, v_seed, df_seed, rows, level, fam_level):
    v_item, q = item_part(rows)
    v = v_seed + v_item
    if v <= 0:
        raise NC("zero variance")
    den = (v_seed * v_seed / df_seed if math.isfinite(df_seed) else 0.0) + q
    df = v * v / den if den > 0 else math.inf
    if not math.isfinite(df):
        raise NC("no finite df")
    se = math.sqrt(v)
    p = t_p_two(est / se, df)
    h = t_quantile(0.5 + level / 2, df) * se
    hf = t_quantile(0.5 + fam_level / 2, df) * se
    return {"est": est, "se": se, "df": df, "seed_var": v_seed, "seed_df": df_seed, "item_var": v_item, "item_q": q,
            "p": p, "ci": (est - h, est + h), "ci_fam": (est - hf, est + hf), "pairs": rows.shape[0]}


def fit_of(table, dsg, cluster, cfg):
    """B16's REML (black box) on the cluster's arms that hold a cell; None (with a reason) when fewer than two."""
    members = [a for a in dsg.fit_arms if dsg.cluster[a] == cluster and any((a, j) in table for j in dsg.seeds[a])]
    if len(members) < 2:
        return None, "fewer than two arms"
    cells = [(a, j, cell_value(table[(a, j)])) for a in members for j in dsg.seeds[a] if (a, j) in table]
    try:
        return reml.fit_cells(cells, tuple(members), float(cfg["endpoints"]["U"]["floor"]), **reml.options(cfg)), None
    except ValueError as exc:
        return None, f"REML refused: {exc}"


def contrast(table, fits, dsg, c, m, level, fam_level):
    common = sorted(set(dsg.seeds[c]) & set(dsg.seeds[m]))
    held = [j for j in common if (c, j) in table and (m, j) in table]
    if len(held) < 2:
        raise NC(f"{len(held)} seeds")
    rows = np.stack([table[(c, j)] - table[(m, j)] for j in held])
    diffs = np.array([cell_value(table[(c, j)]) - cell_value(table[(m, j)]) for j in held])
    est = float(diffs.mean())
    if len(held) < len(common):                       # the pair's own paired form on the seeds it holds
        out = finish(est, float(diffs.var(ddof=1)) / len(held), float(len(held) - 1), rows, level, fam_level)
        out["form"] = "paired"
        return out
    fit, why = fits[dsg.cluster[c]]
    if fit is None:
        raise NC(why)
    jj = len(held)
    if fit.two_arm:
        if set(fit.arms) != {c, m}:
            raise NC("two-arm fit of other arms")
        v_seed, df_seed = fit.sigma2["sum"] / jj, float(fit.pairs - 1)
    else:
        i, k = fit.arms.index(c), fit.arms.index(m)
        v_seed = (fit.sigma2[c] + fit.sigma2[m]) / jj
        var_v = (fit.info_inv[i, i] + fit.info_inv[k, k] + 2.0 * fit.info_inv[i, k]) / jj ** 2
        df_seed = 2.0 * v_seed * v_seed / var_v if var_v > 0 else math.inf
    out = finish(est, v_seed, df_seed, rows, level, fam_level)
    out["form"] = "cluster"
    return out


def read_table(table, dsg, cfg, clusters=None):
    level = float(cfg["intervals"]["per_comparison"])
    fam_level = 1.0 - 2.0 * float(alpha()) / dsg.familywise_sides
    fits = {cl: fit_of(table, dsg, cl, cfg) for cl in (clusters or ("full", "removal"))}
    out = {}
    for name, c, m in dsg.contrasts:
        if dsg.cluster[c] not in fits:
            continue
        try:
            out[name] = contrast(table, fits, dsg, c, m, level, fam_level)
        except NC as exc:
            out[name] = str(exc)
    return out, fits


def words(dsg, ests: dict, primary_p: dict, cfg):
    """Phi with these U p-values (1 where not computable) and the primary O, L, F; U-part words and headline."""
    delta = float(cfg["margin"]["delta_pp"])
    graph = phi.build_graph([n for n, _, _ in dsg.contrasts])
    pv = {}
    for name, _, _ in dsg.contrasts:
        for kind in ("O", "L", "F"):
            pv[(kind, name)] = primary_p[name][kind]
        e = ests[name]
        pv[("U", name)] = e["p"] if isinstance(e, dict) else 1.0
    outcome = phi.run(graph, pv, alpha())
    rej = set(outcome.rejected)
    per = {}
    for name, _, _ in dsg.contrasts:
        e = ests[name]
        if not isinstance(e, dict):
            per[name] = None
            continue
        u = labels.u_part(("U", name) in rej, e["est"], e["ci"], e["ci_fam"], delta)
        per[name] = (list(u.words), labels.headline(u, ("O", name) in rej, ("L", name) in rej)["word"])
    return per, [f"{k}:{c}" for k, c in outcome.rejected]


def reference(tables_doc: dict, counts_doc: dict, reading_doc: dict) -> dict:
    """The whole reference from the three documents' contents (no binding checks: those are tested separately)."""
    cfg = settings()
    reading = tables_doc["reading"]
    dsg = design(reading)
    counts = {(a, int(j)): (np.array(c["n"]), np.array(c["u"]), np.array(c["u_fail"]))
              for a, per in counts_doc["cells"].items() for j, c in per.items()}
    x = {}
    for key, (n, u, _) in counts.items():
        xx = x_exact(n, u)
        if xx is not None:
            x[key] = xx
    coh, fits = read_table(x, dsg, cfg)
    primary_p = {name: reading_doc["contrasts"][name]["p_values"] for name, _, _ in dsg.contrasts}
    coh_words, coh_rej = words(dsg, coh, primary_p, cfg)
    arms = {}
    for arm in dsg.arms:
        vals = {str(j): pooled_pp(counts[(arm, j)][0], counts[(arm, j)][1]) for j in dsg.seeds[arm]}
        held = [v for v in vals.values() if v is not None]
        arms[arm] = {"cells_pp": vals, "mean_pp": float(np.mean(held)) if held else None,
                     "empty": {str(j): int((counts[(arm, j)][0] == 0).sum()) for j in dsg.seeds[arm]}}
    g2 = {name: {str(j): int(((counts[(c, j)][0] == 0) | (counts[(m, j)][0] == 0)).sum())
                 for j in sorted(set(dsg.seeds[c]) & set(dsg.seeds[m]))} for name, c, m in dsg.contrasts}
    plain = {(a, int(j)): np.array(v, dtype=float) for a, per in tables_doc["endpoints"]["U"]["cells"].items()
             for j, v in per.items()}
    g3doc = (tables_doc.get("u_variants") or {}).get("g3_unscored_unsafe")
    corners = {}
    for direction in ("against_better", "against_worse"):
        ests = {}
        for name, c, m in dsg.contrasts:
            if g3doc is None:
                ests[name] = "no g3 table"
                continue
            arm = m if direction == "against_better" else c
            table = dict(plain)
            for j, v in g3doc[arm].items():
                table[(arm, int(j))] = np.array(v, dtype=float)
            one, _ = read_table(table, dsg, cfg, clusters=(dsg.cluster[c],))
            ests[name] = one[name]
        w, rej = words(dsg, ests, primary_p, cfg)
        corners[direction] = {"ests": ests, "words": w, "rejected": rej}
    return {"coherent": {"ests": coh, "words": coh_words, "rejected": coh_rej, "fits": fits}, "arms": arms, "g2": g2,
            "corners": corners}
