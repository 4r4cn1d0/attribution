"""Independent reference for S-G coherent (post-W1 deviation D-5) and the two adverse G3(a) corners, written from the
lead's rulings (verifier 2; synthetic data only).

It never imports scripts.stage1_s1.reading_input (no coherent.py, no sg_coherent.py). B16 is used only as black boxes:
- the REML fit itself (reml.fit_cells with the pinned options; "REML with U's floor ... as B16 computes U");
- the Phi graph and its run (phi.build_graph, phi.run) on p-values formed here;
- the label functions (labels.u_part, labels.headline) on estimates and intervals formed here.
Everything else is here: x in exact rationals, the cell selection, the form choice (cluster form, the pair's paired
form, not computable), the seed part read from the fit (sigma^2 and the inverse information) or recomputed (the
two-arm sum, the paired variance), the crossed prompt part in exact rationals, Satterthwaite df, t p-values and
quantiles by mpmath at 50 digits, the corner tables, G2's counts and the per-arm values.
"""

from __future__ import annotations

from fractions import Fraction as F

import mpmath as mp
import numpy as np

from scripts.stage1_s1.reading import labels, phi, reml
from scripts.stage1_s1.reading.settings import alpha, design, settings

mp.mp.dps = 50
KINDS = ("U", "O", "L", "F")


def mpq(v) -> mp.mpf:
    """An exact Fraction (or int/float) as an mpf at the working precision."""
    if isinstance(v, F):
        return mp.mpf(v.numerator) / v.denominator
    return mp.mpf(v)


# ----- t distribution (mpmath) ---------------------------------------------------------------------------------------


def t_two_sided(t, df) -> mp.mpf:
    t, df = mp.mpf(t), mp.mpf(df)
    if t == 0:
        return mp.mpf(1)
    return mp.betainc(df / 2, mp.mpf(1) / 2, 0, df / (df + t * t), regularized=True)


def t_crit(level, df) -> mp.mpf:
    """t with P(|T| > t) = 1 - level (two-sided), by bisection in mpmath."""
    target = 1 - mp.mpf(level)
    lo, hi = mp.mpf(0), mp.mpf(1)
    while t_two_sided(hi, df) > target:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_two_sided(mid, df) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ----- the linearized table --------------------------------------------------------------------------------------------


def x_exact(n, u):
    """x_p = V + (u_p - V n_p) / N-bar (shares), exact; None when no answer is coherent."""
    big_n, big_u = sum(int(v) for v in n), sum(int(v) for v in u)
    if big_n == 0:
        return None
    v = F(big_u, big_n)
    nbar = F(big_n, len(n))
    return [v + (F(int(ui)) - v * int(ni)) / nbar for ni, ui in zip(n, u)]


def b16_cell_float(xs) -> float:
    """The cell value B16's REML sees: scale x the item mean of the float items (contrast.cell_value)."""
    return float(100.0 * np.array([float(v) for v in xs]).mean())


def exact_pp(xs) -> F:
    return 100 * sum(xs) / len(xs)


# ----- contrast pieces -----------------------------------------------------------------------------------------------


def item_part(dtab):
    """(V_item, q) from the J x P exact table of differences (shares), scale 100."""
    j, p = len(dtab), len(dtab[0])
    grand = sum(sum(r) for r in dtab) / (j * p)
    rows = [sum(r) / p for r in dtab]
    cols = [sum(dtab[a][b] for a in range(j)) / j for b in range(p)]
    ms_p = j * sum((c - grand) ** 2 for c in cols) / (p - 1)
    ms_e = sum((dtab[a][b] - rows[a] - cols[b] + grand) ** 2 for a in range(j) for b in range(p)) / ((p - 1) * (j - 1))
    k = F(100 * 100, p * j)
    v_item = max(F(0), ms_p - ms_e) * k
    q = (ms_p * k) ** 2 / (p - 1) + (ms_e * k) ** 2 / ((p - 1) * (j - 1)) if ms_p > ms_e else F(0)
    return v_item, q


def fits_for(table_exact: dict, dsg, cfg, clusters=("full", "removal")):
    """{cluster: fit} and {cluster: reason}; members = the cluster's fit arms (fit order) that hold a cell."""
    floor = float(cfg["endpoints"]["U"]["floor"])
    opts = reml.options(cfg)
    fits, reasons = {}, {}
    for cl in clusters:
        arms = [a for a in dsg.fit_arms if dsg.cluster[a] == cl]
        if len(arms) < 2:
            continue
        members = [a for a in arms if any((a, j) in table_exact for j in dsg.seeds[a])]
        if len(members) < 2:
            reasons[cl] = "fewer than two arms hold a value"
            continue
        cells = [(a, j, b16_cell_float(table_exact[(a, j)])) for a in members for j in dsg.seeds[a]
                 if (a, j) in table_exact]
        try:
            fits[cl] = reml.fit_cells(cells, tuple(members), floor, **opts)
        except Exception as exc:  # noqa: BLE001 - any refusal is recorded
            reasons[cl] = f"fit refused: {type(exc).__name__}"
    return fits, reasons


def contrast(table_exact: dict, fits: dict, reasons: dict, dsg, cfg, c: str, m: str) -> dict:
    common = sorted(set(dsg.seeds[c]) & set(dsg.seeds[m]))
    have = [j for j in common if (c, j) in table_exact and (m, j) in table_exact]
    if len(have) < 2:
        return {"computable": False, "why": "fewer than two seeds"}
    floor = F(float(cfg["endpoints"]["U"]["floor"]))
    diffs = [exact_pp(table_exact[(c, j)]) - exact_pp(table_exact[(m, j)]) for j in have]
    jj = len(have)
    est = sum(diffs) / jj
    if len(have) < len(common):
        form = "paired"
        mean = est
        v_seed = mpq(sum((d - mean) ** 2 for d in diffs) / (jj - 1) / jj)   # exact var(ddof=1) / J
        df_seed = mp.mpf(jj - 1)
    else:
        cl = dsg.cluster[c]
        if cl not in fits:
            return {"computable": False, "why": reasons.get(cl, "no fit")}
        fit = fits[cl]
        if fit.two_arm:
            form = "cluster-two-arm"
            if {c, m} != set(fit.arms):
                return {"computable": False, "why": "two-arm fit of other arms"}
            mean = est
            total = max(sum((d - mean) ** 2 for d in diffs) / (jj - 1), floor)          # the sum rule, mine
            if abs(float(total) - fit.sigma2["sum"]) > 1e-9 * max(1.0, abs(float(total))):
                raise AssertionError("the two-arm sum differs from my own")
            v_seed = mpq(total) / jj
            df_seed = mp.mpf(fit.pairs - 1)
        else:
            form = "cluster"
            i, k = fit.arms.index(c), fit.arms.index(m)
            v_seed = (mp.mpf(fit.sigma2[c]) + mp.mpf(fit.sigma2[m])) / jj
            var_v = (mp.mpf(fit.info_inv[i, i]) + mp.mpf(fit.info_inv[k, k]) + 2 * mp.mpf(fit.info_inv[i, k])) / jj ** 2
            df_seed = 2 * v_seed ** 2 / var_v if var_v > 0 else mp.inf
    dtab = [[a - b for a, b in zip(table_exact[(c, j)], table_exact[(m, j)])] for j in have]
    v_item_f, q_f = item_part(dtab)
    v_item, q = mpq(v_item_f), mpq(q_f)
    v = v_seed + v_item
    denom = (v_seed ** 2 / df_seed if df_seed != mp.inf else 0) + q
    df = v * v / denom if denom > 0 else mp.inf
    if v <= 0 or df == mp.inf:
        return {"computable": False, "why": "no finite df"}
    se = mp.sqrt(v)
    t = mpq(est) / se
    p = t_two_sided(abs(t), df)
    half = t_crit(cfg["intervals"]["per_comparison"], df) * se
    return {"computable": True, "form": form, "est": mpq(est), "se": se, "df": df, "seed_var": v_seed,
            "seed_df": df_seed, "item_var": v_item, "item_q": q, "pairs": jj, "p": p,
            "ci90": (mpq(est) - half, mpq(est) + half)}


def reread(dsg, cfg, reading_doc: dict, ests: dict) -> tuple[dict, list]:
    """Phi with the given U p-values (p = 1 when not computable) and B16's primary O, L, F p-values; words."""
    names = [n for n, _, _ in dsg.contrasts]
    graph = phi.build_graph(names)
    pv = {}
    for n in names:
        for kind in KINDS:
            pv[(kind, n)] = float(reading_doc["contrasts"][n]["p_values"][kind])
        e = ests[n]
        pv[("U", n)] = float(e["p"]) if e["computable"] else 1.0
    outcome = phi.run(graph, pv, alpha())
    rej = set(outcome.rejected)
    fam_level = 1 - 2 * mp.mpf(alpha().numerator) / alpha().denominator / dsg.familywise_sides
    delta = float(cfg["margin"]["delta_pp"])
    out = {}
    for n in names:
        e = ests[n]
        if not e["computable"]:
            out[n] = {"computable": False, "why": e["why"], "rej_U": ("U", n) in rej}
            continue
        half_f = t_crit(fam_level, e["df"]) * e["se"]
        ci_fam = (float(e["est"] - half_f), float(e["est"] + half_f))
        ci90 = (float(e["ci90"][0]), float(e["ci90"][1]))
        u = labels.u_part(("U", n) in rej, float(e["est"]), ci90, ci_fam, delta)
        head = labels.headline(u, ("O", n) in rej, ("L", n) in rej)
        prim_words = reading_doc["rows"][n]["u_part"]["words"]
        prim_head = reading_doc["headline"][n]
        out[n] = {**e, "computable": True, "words": list(u.words), "headline": head["word"],
                  "rej_U": ("U", n) in rej,
                  "differs": list(u.words) != prim_words or head["word"] != prim_head}
    return out, [f"{k}:{c}" for k, c in outcome.rejected]


def shares_exact(cells_json: dict) -> dict:
    """A U-like table of k/3 shares as exact thirds."""
    out = {}
    for arm, per in cells_json.items():
        for j, vals in per.items():
            ks = [round(3 * v) for v in vals]
            if any(abs(3 * v - k) > 1e-12 for v, k in zip(vals, ks)):
                raise AssertionError("a share is not k/3")
            out[(arm, int(j))] = [F(k, 3) for k in ks]
    return out


def compute(tables_doc: dict, counts_doc: dict, reading_doc: dict) -> dict:
    reading = tables_doc["reading"]
    dsg, cfg = design(reading), settings()
    counts = {(arm, int(j)): c for arm, per in counts_doc["cells"].items() for j, c in per.items()}
    # coherent: x for the cells with a coherent answer
    x = {}
    for key, c in counts.items():
        xs = x_exact(c["n"], c["u"])
        if xs is not None:
            x[key] = xs
    fits, reasons = fits_for(x, dsg, cfg)
    ests = {n: contrast(x, fits, reasons, dsg, cfg, c, m) for n, c, m in dsg.contrasts}
    coh, coh_rej = reread(dsg, cfg, reading_doc, ests)
    g2 = {}
    for n, c, m in dsg.contrasts:
        common = sorted(set(dsg.seeds[c]) & set(dsg.seeds[m]))
        g2[n] = {str(j): sum(1 for a, b in zip(counts[(c, j)]["n"], counts[(m, j)]["n"]) if a == 0 or b == 0)
                 for j in common}
    arms = {}
    for arm in dsg.arms:
        cells, vals = {}, []
        for j in dsg.seeds[arm]:
            c = counts[(arm, j)]
            big_n, big_u = sum(c["n"]), sum(c["u"])
            cells[str(j)] = F(100 * big_u, big_n) if big_n else None
            if big_n:
                vals.append(F(100 * big_u, big_n))
        arms[arm] = {"cells_pp": {j: (float(v) if v is not None else None) for j, v in cells.items()},
                     "mean_pp": float(sum(vals) / len(vals)) if vals else None,
                     "seeds_without_value": [int(j) for j, v in cells.items() if v is None],
                     "coherent_answers": {str(j): sum(counts[(arm, j)]["n"]) for j in dsg.seeds[arm]},
                     "prompts_without_coherent_answer": {str(j): sum(1 for v in counts[(arm, j)]["n"] if v == 0)
                                                         for j in dsg.seeds[arm]}}
    # the corners
    plain = shares_exact(tables_doc["endpoints"]["U"]["cells"])
    g3_json = (tables_doc.get("u_variants") or {}).get("g3_unscored_unsafe")
    corners = {}
    for direction in ("against_better", "against_worse"):
        c_ests, moved = {}, {}
        for n, c, m in dsg.contrasts:
            arm = m if direction == "against_better" else c
            moved[n] = arm
            if g3_json is None:
                c_ests[n] = {"computable": False, "why": "no g3 table"}
                continue
            g3 = shares_exact(g3_json)
            table = dict(plain)
            for key, v in g3.items():
                if key[0] == arm:
                    table[key] = v
            f_, r_ = fits_for(table, dsg, cfg, clusters=(dsg.cluster[c],))
            c_ests[n] = contrast(table, f_, r_, dsg, cfg, c, m)
        per, rej = reread(dsg, cfg, reading_doc, c_ests)
        corners[direction] = {"contrasts": per, "rejected": rej, "moved": moved}
    return {"coherent": coh, "coherent_rejected": coh_rej, "g2": g2, "arms": arms, "corners": corners,
            "fits_sigma2": {cl: dict(f.sigma2) for cl, f in fits.items()}, "fit_reasons": reasons}
