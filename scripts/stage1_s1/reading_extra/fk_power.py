"""F_k's planning power at the measured discordance q, printed beside each F_k result (REV4 6.4; report only).
Exit 0: the file written; 2: refused, nothing written.

    python -m scripts.stage1_s1.reading_extra.fk_power --input tables.json --reading reading.json --out fk_power.json

``tables.json`` is the input builder's --out document (B16's input; its O table holds every cell's and theta0's
per-prompt refusal flags) and ``reading.json`` B16's output on it (bound: B16's provenance names the input document's
SHA-256). REV4 = research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md (frozen).

The frozen rule, REV4:574: "the stage-1 reading prints F_k's planning power at the measured q beside each F_k result
(report only; after block B, because θ0's and the arms' 500-bank answers are under block A's seal until then)." Its
terms, REV4:565: "The discordance is the open quantity (E: review-statistics §6.1; normal approximation; P = 500,
J = 6). q = the share of prompts on which the arm's refusal flag and θ0's differ. ... Power to show an arm at θ0's
level feasible at 5 pp:" (the table REV4:567-572; its columns "Per comparison (5%)" and "Inside Φ (F_k at 0.375%)").
The same move is recorded at REV4:1257 and :1268 (review finding ST-10). The planning formula is the statistics
review's script (REV4 folder, stat_review_o_power.py: se_df and power_feasible), for an arm at θ0's level (Δ = 0):
    SE² = (q - Δ²) / P x 100² + σ_s² / J   (pp²; the item part, then the seed part with J - 1 df, LN-20 item 1)
    df  = SE⁴ / ((σ_s² / J)² / (J - 1) + ((q - Δ²) / P x 100²)² / (P - 1))   (Satterthwaite)
    power = Φ((τ_O* - Δ) / SE - t(1 - α, df))   (the normal approximation to the noncentral t)
with τ_O* = 5 pp (B16's settings tau_o.star_pp) and t from B16's own quantile (tdist). Every run first reproduces
REV4's printed table (rows 1 and 2, REV4:569-570) to its two decimals, or refuses.

Printed per contrast: the repair arm's measured q (per seed and the mean), P and J, the planning power at that q
for each frozen row (seed SD 0 and 1.15 pp) at 5% per comparison and at 0.375% inside Φ, and beside it F_k's result
copied from B16's output by key (F_k's Φ rejection, its p-value, its level, the theta0 part with its 90% interval).
READINGS gives each reading of the rule and its alternative. Nothing here changes a label: report only.
"""

from __future__ import annotations

import math

import numpy as np

from scripts.stage1_s1.reading.schema import validate
from scripts.stage1_s1.reading.settings import Refusal, settings
from scripts.stage1_s1.reading.tdist import t_quantile
from scripts.stage1_s1.reading_extra import common

KIND = "stage1 reading F_k planning power at the measured discordance"
PLANNING_P, PLANNING_J = 500, 6                    # REV4:565
DELTA_PP = 0.0                                     # REV4:565: "an arm at θ0's level"
SEED_SD_ROWS_PP = (0.0, 1.15)                      # REV4:569-570, the two Branch-full rows
LEVELS = (("per comparison (5%)", 0.05), ("inside Phi (F_k at 0.375%)", 0.00375))   # REV4:567's two columns
TABLE_Q = (0.05, 0.10, 0.20, 0.30, 0.40)           # REV4:567: q = 5 / 10 / 20 / 30 / 40%
TABLE = {(0.0, 0.05): (1.00, 0.97, 0.80, 0.65, 0.55), (0.0, 0.00375): (0.99, 0.80, 0.43, 0.26, 0.18),
         (1.15, 0.05): (1.00, 0.96, 0.78, 0.64, 0.54), (1.15, 0.00375): (0.96, 0.75, 0.40, 0.25, 0.17)}
RULE = [
    "REV4:574: the stage-1 reading prints F_k's planning power at the measured q beside each F_k result (report "
    "only; after block B, because θ0's and the arms' 500-bank answers are under block A's seal until then).",
    "REV4:565: The discordance is the open quantity (E: review-statistics §6.1; normal approximation; P = 500, J = 6). "
    "q = the share of prompts on which the arm's refusal flag and θ0's differ.",
    "REV4:565-572: Power to show an arm at θ0's level feasible at 5 pp; per comparison (5%) and inside Φ (F_k at "
    "0.375%); seed SD of O 0 pp and 1.15 pp (Branch full rows); the Branch 128 rows add +3 and +6 pp of discordance.",
    "stat_review_o_power.py (the REV4 folder): one seed's per-prompt difference has variance q - Δ², so the item part "
    "of the SE is sqrt((q - Δ²)/P); the seed part is σ_s²/J with J - 1 df (LN-20 item 1); df by Satterthwaite; power "
    "uses the normal approximation to the noncentral t: Φ(ncp - t_crit(df))."]
READINGS = {
    "F1": "q of an arm is the mean over its seeds with O-bank answers of the per-seed share of the O items whose flag "
          "differs from θ0's flag (equal to the share over all seed x prompt pairs, since every seed holds every item); "
          "the per-seed shares are printed. Alternative: one seed's q, or the median over seeds.",
    "F2": "P and J are the reading's own (the O items and the repair arm's O seeds): under plan A they equal the "
          "planning values P = 500, J = 6 (REV4:565); under block A only (J = 3) and plan B (J = 9) the formula takes "
          "the reading's J, and the output flags that it differs from the planning J. Alternative: P = 500 and J = 6 "
          "always.",
    "F3": "The rows are REV4's two Branch-full rows (seed SD 0 and 1.15 pp) at the measured q, with no added "
          "discordance: under Branch 128 the measured q already holds the cut's flag changes, so the +3 and +6 pp rows "
          "(planning allowances for them) are not added again. Alternative: all four rows, the Branch 128 rows at "
          "q + 0.03 and q + 0.06.",
    "F4": "The columns are REV4's two levels, 5% per comparison and 0.375% inside Φ, not the level F_k reached in "
          "this reading's Φ run (F_k starts with weight 0; B16's level is printed beside the power). Alternative: the "
          "power at F_k's own final level.",
    "F5": "Δ = 0 and τ_O* = 5 pp (\"an arm at θ0's level feasible at 5 pp\"): planning power, not observed power; the "
          "measured O estimate against θ0 is printed beside it, never put into the formula. Alternative: none in the "
          "text."}


def _normal_cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def planning(q: float, seed_sd_pp: float, alpha: float, p: int, j: int, tau_pp: float, delta_pp: float = DELTA_PP) \
        -> dict:
    """The planning power of F_k (stat_review_o_power.power_feasible) at discordance q, with its SE and df."""
    d = delta_pp / 100.0
    v_item = max(q - d * d, 1e-12) / p * 1e4
    v_seed = seed_sd_pp ** 2 / j
    v = v_item + v_seed
    df = v * v / ((v_seed * v_seed / (j - 1) if v_seed > 0 else 0.0) + v_item * v_item / (p - 1))
    power = _normal_cdf((tau_pp - delta_pp) / math.sqrt(v) - t_quantile(1.0 - alpha, df))
    return {"power": power, "se_pp": math.sqrt(v), "df": df}


def check_table(tau_pp: float) -> None:
    """REV4:569-570 reproduced to their two decimals at P = 500, J = 6, or a refusal."""
    for (sd, alpha), row in TABLE.items():
        got = [planning(q, sd, alpha, PLANNING_P, PLANNING_J, tau_pp)["power"] for q in TABLE_Q]
        if any(abs(g - want) > 0.005 + 1e-9 for g, want in zip(got, row)):
            raise Refusal("the planning formula does not reproduce REV4's power table (REV4:569-570)")


def discordance(o_table: dict, theta0: np.ndarray, arm: str) -> dict:
    """F1: the per-seed share of items whose flag differs from θ0's, and the mean over the arm's O seeds."""
    seeds = sorted(j for a, j in o_table if a == arm)
    if len(seeds) < 2:
        raise Refusal(f"{arm} has fewer than two seeds with O-bank answers; F_k has no planning power")
    flags = [theta0, *(o_table[(arm, j)] for j in seeds)]
    if any(not np.isin(f, (0.0, 1.0)).all() for f in flags):
        raise Refusal(f"the O table of {arm} or theta0 holds a value that is not a 0/1 refusal flag")
    per = {str(j): float(np.mean(o_table[(arm, j)] != theta0)) for j in seeds}
    return {"seeds": seeds, "per_seed": per, "q": float(np.mean(list(per.values())))}


def _f_result(reading_doc: dict, name: str) -> dict:
    """F_k's result as B16 printed it, copied by key."""
    k = (reading_doc.get("contrasts") or {}).get(name) or {}
    row = (reading_doc.get("rows") or {}).get(name) or {}
    phi = reading_doc.get("phi") or {}
    o = k.get("O") or {}
    fp = row.get("feasibility_part") or {}
    node = f"F:{name}"
    if "F_k_rejects_in_phi" not in fp or "theta0_part" not in o or "F" not in (k.get("p_values") or {}):
        raise Refusal(f"B16's output holds no F_k result for {name}")
    return {"F_k_rejects_in_phi": fp["F_k_rejects_in_phi"], "F_k_text": fp.get("F_k_text"),
            "p_value": k["p_values"]["F"], "level_at_rejection": (phi.get("level_at_rejection") or {}).get(node),
            "final_level": (phi.get("final_levels") or {}).get(node), "theta0_part": o["theta0_part"],
            "theta0_interval_90": o.get("theta0_interval_90"), "states": fp.get("states")}


def read(tables_doc: dict, reading_doc: dict, tables_sha256: str, reading_sha256: str) -> dict:
    """The whole output (module doc)."""
    dsg = common.bound_reading(reading_doc, tables_sha256)
    inp = validate(tables_doc)                        # B16's own schema: the same tables B16 read
    if inp.reading != dsg.reading:
        raise Refusal("the input document and B16's output name different readings")
    cfg = settings()
    tau = float(cfg["tau_o"]["star_pp"])
    check_table(tau)
    o_table, theta0 = inp.tables["O"], np.asarray(inp.theta0_o, dtype=float)
    p = int(theta0.size)
    contrasts = {}
    for name, c, m in dsg.contrasts:
        dq = discordance(o_table, theta0, m)
        j = len(dq["seeds"])
        rows = [{"seed_sd_pp": sd, "level": label, "alpha": alpha,
                 **planning(dq["q"], sd, alpha, p, j, tau)} for sd in SEED_SD_ROWS_PP for label, alpha in LEVELS]
        contrasts[name] = {"comparator": c, "repair": m, "items": p, "seeds": j, "o_seeds": dq["seeds"],
                           "planning_p_j": [PLANNING_P, PLANNING_J],
                           "differs_from_planning_p_j": [p, j] != [PLANNING_P, PLANNING_J],
                           "discordance": {"q": dq["q"], "per_seed": dq["per_seed"]},
                           "planning_power": rows, "F_k": _f_result(reading_doc, name)}
    out = {"kind": KIND, "version": 1, "reading": dsg.reading, "label_suffix": dsg.label_suffix,
           "rule": list(RULE), "readings": dict(READINGS),
           "model": {"delta_pp": DELTA_PP, "tau_o_star_pp": tau, "seed_sd_rows_pp": list(SEED_SD_ROWS_PP),
                     "levels": {label: alpha for label, alpha in LEVELS},
                     "table_check": "REV4:569-570 reproduced to two decimals at P = 500, J = 6",
                     "note": "planning power for an arm at θ0's level; report only; it changes no label"},
           "contrasts": contrasts,
           "provenance": common.provenance({"tables.json": tables_sha256, "reading.json": reading_sha256})}
    return common.finish(out)


def main(argv=None) -> int:
    def arguments(p):
        p.add_argument("--input", required=True, help="the builder's tables.json (B16's input)")
        p.add_argument("--reading", required=True, help="B16's reading.json on that input")

    def produce(args):
        t_doc, t_sha = common.read_document(args.input, "the input document")
        r_doc, r_sha = common.read_document(args.reading, "the reading file")
        return read(t_doc, r_doc, t_sha, r_sha), []

    return common.main_frame("python -m scripts.stage1_s1.reading_extra.fk_power",
                             "F_k's planning power at the measured discordance (REV4:574)", arguments, produce, argv)


if __name__ == "__main__":
    raise SystemExit(main())
