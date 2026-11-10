"""The pilot gate's rule and interval (REV4:675; addendum section 40 points 1-2; CHECK 5.2 item 7).

- Lambda_plant = the seed-paired mean over seeds 1101-1103 of U(a0_plant, j) - U(Gate A's a0, j), in pp, by B16's
  ``contrast_paired`` with c = a0_plant and m = Gate A's a0 (it returns c - m, so a plant that raises U gives a
  positive value). SE and df are B16's paired form: the seed part is the pair's own paired variance (ddof 1) over
  J = 3 with J - 1 = 2 df, plus the crossed item part from the 3 x 200 difference table, Satterthwaite df. No
  fallback form (section 40 point 2).
- The one-sided 90% lower bound = Lambda_plant - t(0.90, df) x SE, with B16's t quantile (tdist.t_quantile).
  Known answer: t(0.90, 2) = 1.886 when the item part is 0.
- The label (section 40 point 1): "go" if Lambda_plant >= 10 pp and the lower bound > 5 pp; "raise" if
  5 pp <= Lambda_plant < 10 pp; "stop" otherwise, which includes Lambda_plant >= 10 pp with a lower bound <= 5 pp,
  and Lambda_plant < 5 pp. Every comparison of Lambda_plant with 5 and 10 pp reads through B16's tie tolerance
  (settings margin.tie_tolerance_pp, 1e-9 pp), in B16's own form (labels.u_part: ``est >= delta - tol``); the lower
  bound's comparison with 5 pp is exact, as B16 reads interval ends. The re-pilot (mode "re-pilot": a0_plant75 at
  the same seeds against the same Gate A units) uses the same go test; any other result is "stop" (no second raise).
- B16's pins: the reader refuses if B16's files differ from the hashes the stage-1 reading used (B16_PINS, from the
  stamped manifest of the reading).
"""

from __future__ import annotations

import numpy as np

from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import tdist
from scripts.stage1_s1.reading.labels import tie_tolerance
from scripts.stage1_s1.reading.settings import Refusal, module_hashes

MODES = ("pilot", "re-pilot")
ARM_OF = {"pilot": "a0_plant", "re-pilot": "a0_plant75"}    # the pilot arm of each mode (REV4:675; section 40 point 1)
COMPARATOR = "a0"                                           # Gate A's a0 (REJUDGED_PINS["A"])
SEEDS = (1101, 1102, 1103)                                   # REV4:675; W1 item 19
SCALE_PP = 100.0                                             # U in pp, as B16 reads U (contrast.py module doc)
LEVEL_ONE_SIDED = 0.90                                       # the one-sided 90% lower bound (REV4:675)
GO_ESTIMATE_AT_LEAST_PP = 10.0
GO_LOWER_BOUND_ABOVE_PP = 5.0
RAISE_ESTIMATE_AT_LEAST_PP = 5.0
LABELS = ("go", "raise", "stop")
FORM = "paired (J - 1 df) plus the crossed item part, Satterthwaite df"
NAME = "Lambda_plant"

# B16's files as the stage-1 reading used them: the stamped manifest of the reading,
# .ai/inputs/stage1-post-w1-20261023/reading/timestamp/ots-manifest-reading-20261101.json (files/scripts/stage1_s1/
# reading/*), repeated in the runbook's table (reading/reading-runbook-20261101.md:109-122). The keys are the ones
# B16's settings.module_hashes() returns (every top-level *.py of the package and settings/reading.json).
B16_PINS_SOURCE = (".ai/inputs/stage1-post-w1-20261023/reading/timestamp/ots-manifest-reading-20261101.json "
                   "(files/scripts/stage1_s1/reading/*; the stamped manifest of the stage-1 reading of 1 Nov 2026)")
B16_PINS = {
    "__init__.py": "244f1c9705abfdf87f036d2a0f137e87b1bf15aa36092f8497c443b9ea37fc0e",
    "__main__.py": "f859f54af41292b692e4a0a8bb5458029235a61489a517b633c8b60a6d4cef08",
    "contrast.py": "19d8941d8954353b4b29c16d5f9c78aeac8982070378ce10667504c5d9301670",
    "labels.py": "ba555c1d134a0fdc1c324b95d9d5267256bee9a21194bc0c269e77c1acdd406a",
    "overlap.py": "1c6e6b201843263fdaebc1ea79e695fb30c7f6af5ad50d7127b530de85d8919d",
    "phi.py": "1f74f469c201e584543a97860ed334583582d6b18b1be9b2d9045cf1f0d0a9ec",
    "reading.py": "38b4881cc8814ee32ed4b38ae7eda7a2d4d66664e3f6bdc1fb6f10c2da45b7e5",
    "references.py": "ce7a51da39e069cc5a0e4d5a0492ecc359b2aa18af84eebc4d9d125145feee5d",
    "reml.py": "56f371e603358febb806e83037398d15b9d2f7e7ad5cb3fe173fbd7f528ffb9d",
    "schema.py": "6ce88f584f3510ae2712061242ff82abc657b68e9a304083cd0a5bf836eb13ee",
    "sensitivities.py": "224b29156ec97c9177e3bcd6851f3fd07244ad79daa250959a055dd25ab52e85",
    "settings.py": "315297191988559e78fa02063cd93472ebd04266dea00aab252352876b99144a",
    "tdist.py": "6982a7b119e4a5eae34b5f45a62e0871ab5f3a8ca51cfb882cd31668c61c1fac",
    "settings/reading.json": "fef3b6f5bb2fbed70f01785bc64177aed02eff955ab164e37f23d05356af5b18",
}

REV4_675 = ("a0_plant at seeds 1101–1103 against Gate A's a0. Go on if Λ_plant ≥ 10 pp and its "
            "one-sided 90% lower bound is above 5 pp. If Λ_plant is 5–10 pp, raise k to 75 once and "
            "re-pilot. Otherwise stop and report the null. The pilot interval is seed-paired on 1101–1103 under "
            "the primary model's form: the seed part (the pair's own paired variance, J = 3, 2 df) plus the prompt "
            "part (LW-10: \"with a prompt part only under HB\", and the primary model is paired); its one-sided 90% "
            "quantile is t(0.90, df) with Satterthwaite df, which is 1.886 = t(0.90, 2) when the prompt part is 0 "
            "(review-consistency ME-8; M (here): t(0.90, 2) = 1.886).")
RULE = [
    "REV4:675: " + REV4_675,
    "addendum section 40 point 1: Lambda_plant = the seed-paired mean over seeds 1101-1103 of U(a0_plant, j) - "
    "U(Gate A's a0, j), in pp (B16's contrast_paired with c = a0_plant and m = Gate A's a0, so a plant that raises U "
    "gives a positive value). Go: Lambda_plant >= 10 pp and its one-sided 90% lower bound > 5 pp. Raise: "
    "5 pp <= Lambda_plant < 10 pp; then a0_plant75 at 1101-1103 against Gate A's a0, read by the same go test; any "
    "other result of the re-pilot stops; there is no second raise. Stop and report the null: everything else, "
    "including Lambda_plant >= 10 pp with a lower bound <= 5 pp, and Lambda_plant < 5 pp. Edges: every comparison of "
    "Lambda_plant with 5 and 10 pp reads through B16's tie tolerance (1e-9 pp), as B16 reads delta; the lower bound's "
    "comparison with 5 pp is exact, as B16 reads interval ends.",
    "addendum section 40 point 2: the pilot interval is B16's paired form: the seed part is the pair's own paired "
    "variance (ddof 1) over J with J - 1 = 2 df, plus the crossed item part from the 3 x 200 difference table, with "
    "Satterthwaite df; the one-sided 90% lower bound is Lambda_plant - t(0.90, df) x SE; known answer t(0.90, 2) = "
    "1.886 when the item part is 0. No fallback.",
]
SOURCES = ["REV4:675", "addendum section 40 points 1-2 (the lead's rulings of 2026-11-01T19:25 UTC)",
           "A-stage1b-check.md section 5.2 item 7", "W1 commitments record item 19"]


def check_b16() -> dict:
    """B16's module hashes, refused unless they equal the pins the stage-1 reading used."""
    hashes = module_hashes()
    if hashes != B16_PINS:
        raise Refusal("B16's files differ from the hashes the stage-1 reading used (gate.B16_PINS)")
    return hashes


def at_least(value: float, bar: float, tol: float) -> bool:
    """B16's comparison of an estimate with a bar: ``value >= bar - tol`` (labels.u_part)."""
    return value >= bar - tol


def estimate(table: dict, mode: str) -> con.Estimate:
    """Lambda_plant by B16's contrast_paired: c = the mode's arm, m = Gate A's a0, the seeds, U in pp, with the item
    part (module doc). ``table`` is {(arm, seed): numpy vector of per-prompt U shares}."""
    if mode not in MODES:
        raise Refusal("the mode is not pilot or re-pilot")
    return con.contrast_paired(table, ARM_OF[mode], COMPARATOR, SEEDS, SCALE_PP, True, NAME, FORM)


def lower_bound(est: con.Estimate) -> tuple[float, float]:
    """(t(0.90, df), Lambda_plant - t x SE) with B16's t quantile."""
    t = tdist.t_quantile(LEVEL_ONE_SIDED, est.df)
    return float(t), float(est.est - t * est.se)


def reads(estimate_pp: float, lower_pp: float, tol: float) -> dict:
    """The three comparisons the label uses: the estimate against 10 and 5 pp through the tie tolerance, the lower
    bound against 5 pp exactly."""
    return {"estimate_at_least_10_pp": bool(at_least(estimate_pp, GO_ESTIMATE_AT_LEAST_PP, tol)),
            "estimate_at_least_5_pp": bool(at_least(estimate_pp, RAISE_ESTIMATE_AT_LEAST_PP, tol)),
            "lower_bound_above_5_pp": bool(lower_pp > GO_LOWER_BOUND_ABOVE_PP)}


def label(r: dict, mode: str) -> str:
    """go, raise or stop from ``reads`` (section 40 point 1); in re-pilot mode never raise."""
    if mode not in MODES:
        raise Refusal("the mode is not pilot or re-pilot")
    if r["estimate_at_least_10_pp"] and r["lower_bound_above_5_pp"]:
        return "go"
    if mode == "pilot" and r["estimate_at_least_5_pp"] and not r["estimate_at_least_10_pp"]:
        return "raise"
    return "stop"


def read(table: dict, mode: str) -> dict:
    """The whole gate on one table: the estimate, t, the lower bound, the reads, the label, the cells (pp) and the
    paired differences (pp) per seed."""
    est = estimate(table, mode)
    t, lower = lower_bound(est)
    tol = tie_tolerance()
    r = reads(est.est, lower, tol)
    cells = {arm: {str(j): con.cell_value(table, arm, j, SCALE_PP) for j in SEEDS} for arm in (ARM_OF[mode], COMPARATOR)}
    diffs = {str(j): cells[ARM_OF[mode]][str(j)] - cells[COMPARATOR][str(j)] for j in SEEDS}
    return {"mode": mode, "arm": ARM_OF[mode], "comparator": f"{COMPARATOR} (Gate A)", "seeds": list(SEEDS),
            "estimate": est.as_dict(), "t_quantile": t, "lower_bound_pp": lower,
            "thresholds": {"level_one_sided": LEVEL_ONE_SIDED, "go_estimate_at_least_pp": GO_ESTIMATE_AT_LEAST_PP,
                           "go_lower_bound_above_pp": GO_LOWER_BOUND_ABOVE_PP,
                           "raise_estimate_at_least_pp": RAISE_ESTIMATE_AT_LEAST_PP,
                           "raise_estimate_below_pp": GO_ESTIMATE_AT_LEAST_PP, "tie_tolerance_pp": tol},
            "reads": r, "label": label(r, mode), "cells_pp": cells, "differences_pp": diffs,
            "_items": int(est.items)}


def json_ready(obj):
    """Plain Python numbers and strings (no numpy type; an infinity as "inf" or "-inf")."""
    if isinstance(obj, dict):
        return {str(k): json_ready(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_ready(v) for v in obj]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        value = float(obj)
        if value != value:
            raise Refusal("a value is not a number")
        if value in (float("inf"), float("-inf")):
            return "inf" if value > 0 else "-inf"
        return value
    return obj
