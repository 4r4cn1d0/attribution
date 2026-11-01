"""The selector predictions (REQ-18) and the one command-line entry point of Part E (numpy; Mac, $0).

Commands:
  predict       run the frozen grid of settings/selector_simulate.json for every menu that
                settings/selector_predict.json predicts, under both cost conventions, and write predictions.json
                (numbers, code and settings hashes; byte-identical on a re-run with the same settings) and
                timing.json (wall-clock seconds, kept apart so the predictions stay deterministic) into --out.
  replay        one replay from saved labels (a batch of 1 through spec.select, the function the simulation
                calls); prints ids and numbers only.
  check-inputs  recompute the SHA-256 of every input the simulate settings list, under --root (the main
                checkout); refuse a changed or missing file and a path under a Gate B wave folder that the
                settings do not name; with --resolve, find each unpinned input by its path hint and SHA-256
                prefix (hashes only).

predictions.json holds, per menu, convention and budget B (in units of c0): the frozen runs-only rule with the
criterion table (under the default freeze scope one rule and one k per (menu, M, B), the same in both
conventions' blocks, with each convention's criterion mean beside the pooled one); per tau_O: V_max, and for
each runs-only rule and the diagnostic policy E[G(pick)], P(best
found), regret and the violation rate; the diagnostic's frozen k per c_d/c0 and, per quality grid point, Delta
and c* as curves in c_d/c0; intervals over the prior grid (parameter uncertainty about the effect shape and size)
with the sensitivity cases beside them; Monte Carlo SEs; the placement statistics; Llama's held-out Gate B-lite
predictions; the content classifier's planted-menu row. Exit 0: written; exit 2: refused, nothing written.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np

HERE = Path(__file__).resolve().parent
STAGE1 = HERE.parent
REPO = STAGE1.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1.selector import simulate as sm  # noqa: E402
from scripts.stage1.selector import spec  # noqa: E402

SETTINGS_PATH = STAGE1 / "settings" / "selector_predict.json"
SETTINGS_SHA256 = "2d45c3c280ad08c5640bd38b02c201d9db597e5c6599b857ce9ddaed5f516cb0"
SETTINGS_NAME = "selector_predict"
PREDICTIONS_KIND = "stage1 selector predictions"
GATE_B_WAVE_PREFIXES = ("tmp/gate-b-olmo/",)


PLANTED_STATISTICS = ("row_auc", "top_k_hit")


def load(path: str | Path = SETTINGS_PATH) -> tuple[dict, str]:
    settings, digest = s1.load_settings(path, SETTINGS_SHA256, SETTINGS_NAME)
    check(settings)
    return settings, digest


def check(pred: Mapping[str, Any]) -> None:
    """Structural checks of a predict settings document: the planted placement names both statistics, one as
    primary and one as secondary (LW-11 fixes which; the pinned file is tested for it)."""
    placement = pred["placement"]
    pair = (placement["planted_primary"], placement["planted_secondary"])
    if sorted(pair) != sorted(PLANTED_STATISTICS):
        raise s1.Refusal("the planted placement must name row_auc and top_k_hit, one primary and one secondary")


def num(x: Any) -> float | None:
    """A float with 10 significant digits (None for NaN or infinity)."""
    x = float(x)
    if not math.isfinite(x):
        return None
    return float(f"{x:.10g}")


# ----- c* ------------------------------------------------------------------------------------------------


def c_star(grid: list[float], delta: list[float]) -> dict:
    """The first crossing (lead decisions L15 (5)) of Delta on the ascending c_d/c0 grid."""
    if len(grid) != len(delta) or not grid or grid != sorted(grid) or grid[0] != 0.0:
        raise s1.Refusal("c* needs an ascending c_d/c0 grid from 0 with one Delta per point")
    if delta[0] < 0:
        return {"kind": "none", "value": None, "interpolated": None,
                "non_monotone": bool(any(d >= 0 for d in delta[1:]))}
    j = 0
    while j + 1 < len(grid) and delta[j + 1] >= 0:
        j += 1
    if j == len(grid) - 1:
        return {"kind": "at_least_grid_max", "value": grid[-1], "interpolated": None, "non_monotone": False}
    d0, d1 = delta[j], delta[j + 1]
    interpolated = grid[j] + (grid[j + 1] - grid[j]) * d0 / (d0 - d1)
    later = any(d >= 0 for d in delta[j + 2:])
    return {"kind": "grid_point", "value": grid[j], "interpolated": num(interpolated), "non_monotone": bool(later)}


# ----- summaries -----------------------------------------------------------------------------------------


def _point_names(points: list[tuple[str, float]]) -> list[str]:
    return [f"{shape}:{size:g}" for shape, size in points]


def _metric(total: np.ndarray, total2: np.ndarray | None, n: int, names: list[str], t: int,
            per_point: bool = True) -> dict:
    """Mean over the prior grid points (equal weight) of one metric at tau index t, with each point's mean and
    Monte Carlo SE; the SE of the equal-weight mean is bounded by the mean of the points' SEs (the points share
    their noise, so their covariances are not known from the sums)."""
    means = total[:, t] / n
    out = {"mean": num(means.mean()), "interval_prior_grid": [num(means.min()), num(means.max())]}
    if total2 is not None:
        var = np.maximum(total2[:, t] / n - means ** 2, 0.0) * n / max(n - 1, 1)
        se = np.sqrt(var / n)
        out["mc_se_bound"] = num(se.mean())
        if per_point:
            out["by_prior_point"] = {name: {"mean": num(m), "mc_se": num(s)} for name, m, s in zip(names, means, se)}
    elif per_point:
        out["by_prior_point"] = {name: num(m) for name, m in zip(names, means)}
    return out


def _bernoulli(total: np.ndarray, n: int, names: list[str], t: int, per_point: bool = False) -> dict:
    p = total[:, t] / n
    se = np.sqrt(p * (1 - p) / n)
    out = {"mean": num(p.mean()), "interval_prior_grid": [num(p.min()), num(p.max())], "mc_se_bound": num(se.mean())}
    if per_point:
        out["by_prior_point"] = {name: num(x) for name, x in zip(names, p)}
    return out


def summarize(s: sm.Sums, names: list[str], t: int, paired: bool = False, per_point: bool = True) -> dict:
    """E_G (with each prior point's mean and MC SE when per_point), P_best, regret, violation, Delta."""
    n = s.n
    out = {"E_G": _metric(s.data["g"], s.data["g2"], n, names, t, per_point),
           "P_best": _bernoulli(s.data["found"], n, names, t, per_point),
           "regret": _metric(s.data["regret"], s.data["regret2"], n, names, t, False),
           "violation": _bernoulli(s.data["violation"], n, names, t),
           "spent_mean": num(s.spent / (n * len(names)))}
    if paired:
        out["Delta"] = _metric(s.data["d"], s.data["d2"], n, names, t, False)
    return out


def placement_summary(placement: Mapping[str, Any], points: list[tuple[str, float]], q_range: list[float],
                      planted: bool, ks: list[int]) -> dict:
    names = _point_names(points)
    P = len(points)
    out = {}
    lo, hi = q_range
    for q, values in placement.items():
        entry: dict = {}
        if planted:
            hits = {}
            for k in ks:
                v = values["top_k_hit"][k].astype(float).reshape(P, -1)
                hits[str(k)] = {"P_hit": num(v.mean()), "range_90": [num(np.quantile(v, lo)), num(np.quantile(v, hi))],
                                "by_prior_point": {name: num(row.mean()) for name, row in zip(names, v)}}
            entry["top_k_hit"] = hits
            if "row_auc" in values:
                auc = values["row_auc"].reshape(P, -1)[0]          # the row AUC does not depend on the effect size
                entry["row_auc"] = {"mean": num(auc.mean()), "range_90": [num(np.quantile(auc, lo)),
                                                                          num(np.quantile(auc, hi))]}
        else:
            rho = values["spearman_rho"].reshape(P, -1)
            entry["spearman_rho"] = {"mean": num(rho.mean()),
                                     "range_90": [num(np.quantile(rho, lo)), num(np.quantile(rho, hi))],
                                     "by_prior_point": {name: [num(np.quantile(row, lo)), num(np.quantile(row, hi))]
                                                        for name, row in zip(names, rho)}}
        out[q] = entry
    return out


def cell_block(res: dict, sim: Mapping[str, Any], tau_o: tuple[float, ...], b: float) -> dict:
    names = _point_names(res["points"])
    grid = [float(c) for c in sim["grids"]["c_d_grid"]]
    frozen_rule = res["frozen"]["rule"][str(b)]
    runs = {}
    for rule in res["rules"]:
        s = res["sums_a"][(0.0, b, rule)]
        runs[rule] = {f"{tau:g}": summarize(s, names, t) for t, tau in enumerate(tau_o)}
    by_rho = {}
    for rho in res["rho_grid"]:
        if rho == 0.0:
            continue
        by_rho[f"{rho:g}"] = {rule: {f"{tau:g}": summarize(res["sums_a"][(rho, b, rule)], names, t)
                                     for t, tau in enumerate(tau_o)} for rule in res["rules"]}
    v_max = {}
    for t, tau in enumerate(tau_o):
        v_max[f"{tau:g}"] = _metric(res["V"], res["V2"], res["n_a"], names, t)
    frozen_k = {f"{c:g}": res["frozen"]["k"][f"{b:g}|{c:g}"] for c in grid}
    diag = {}
    for t, tau in enumerate(tau_o):
        per_q = {}
        for q in res["qualities_main"]:
            rows = [summarize(res["sums_b"][(b, c, q, frozen_k[f"{c:g}"])], names, t, paired=True,
                              per_point=False) for c in grid]
            delta = [r["Delta"]["mean"] for r in rows]
            per_q[q] = {"c_d_grid": grid, "k": [frozen_k[f"{c:g}"] for c in grid],
                        "E_G": [r["E_G"]["mean"] for r in rows], "Delta": delta,
                        "Delta_mc_se_bound": [r["Delta"]["mc_se_bound"] for r in rows],
                        "Delta_interval_prior_grid": [r["Delta"]["interval_prior_grid"] for r in rows],
                        "P_best": [r["P_best"]["mean"] for r in rows], "regret": [r["regret"]["mean"] for r in rows],
                        "violation": [r["violation"]["mean"] for r in rows],
                        "c_star": c_star(grid, delta)}
        avg = [float(np.mean([per_q[q]["Delta"][i] for q in res["qualities_main"]])) for i in range(len(grid))]
        diag[f"{tau:g}"] = {"by_quality": per_q, "quality_average": {"Delta": [num(x) for x in avg],
                                                                     "c_star": c_star(grid, avg)}}
    sens = {}
    for name in sim["sensitivities"]:
        runs_c = {}
        for rule in res["rules"]:
            runs_c[rule] = {}
            for t, tau in enumerate(tau_o):
                r = summarize(res["sums_c"][(name, b, "runs", rule)], names, t, per_point=False)
                runs_c[rule][f"{tau:g}"] = {"E_G": r["E_G"], "P_best": r["P_best"]["mean"],
                                            "regret": r["regret"]["mean"], "violation": r["violation"]["mean"]}
        block = {"runs_only": runs_c}
        dq = {}
        for q in res["qualities_main"] + res["qualities_report"]:
            dq[q] = {}
            for t, tau in enumerate(tau_o):
                rows = [summarize(res["sums_c"][(name, b, c, q)], names, t, paired=True, per_point=False)
                        for c in grid]
                delta = [r["Delta"]["mean"] for r in rows]
                dq[q][f"{tau:g}"] = {"Delta": delta, "c_star": c_star(grid, delta)}
        block["diagnostic"] = dq
        sens[name] = block
    oracle = {}
    for t, tau in enumerate(tau_o):
        best = max(res["rules"], key=lambda r: (runs[r][f"{tau:g}"]["E_G"]["mean"], -res["rules"].index(r)))
        oracle[f"{tau:g}"] = {"rule": best, "E_G": runs[best][f"{tau:g}"]["E_G"]["mean"]}
    return {"boundary_cell": b == float(sim["grids"]["boundary_budget"]),
            "frozen_over_conventions": res["frozen_over"],
            "runs_only": {"frozen_rule": frozen_rule, "rule_choice": _choice_table(res["rule_choice"][str(b)]),
                          "by_rule": runs, "by_rho": by_rho,
                          "oracle_best_rule_by_mean": oracle,
                          "oracle_note": "report only (PLAN-S section 4.5): the rule with the largest E[G] at each tau_O in hindsight; the frozen rule is chosen by the criterion over every tau_O point"},
            "V_max": v_max,
            "diagnostic": {"rule_run": "halving" if frozen_rule == "bisection" else frozen_rule,
                           "frozen_k": frozen_k,
                           "k_choice": {f"{c:g}": _choice_table(res["k_choice"][f"{b:g}|{c:g}"]) for c in grid},
                           "by_tau_o": diag},
            "sensitivities": sens}


def _choice_table(choice: Mapping[str, Any]) -> dict:
    def value(vv: Any) -> Any:
        if isinstance(vv, float):
            return num(vv)
        if isinstance(vv, dict):
            return {c: num(x) for c, x in vv.items()}
        return vv
    return {"chosen": choice["chosen"], "best_by_mean": choice["best_by_mean"], "conventions": choice["conventions"],
            "table": {k: {kk: value(vv) for kk, vv in v.items()} for k, v in choice["table"].items()}}


# ----- the Llama block and the classifier row ------------------------------------------------------------


def llama_block(spec_settings: Mapping[str, Any], sim: Mapping[str, Any], pred: Mapping[str, Any],
                workers: int) -> dict:
    cfg = pred["llama"]
    menu_id = cfg["menu"]
    out: dict = {"rule": cfg["rule"], "design": cfg["design"], "conventions": {}}
    for convention in pred["conventions"]:
        ctx = spec.context(spec_settings, menu_id, convention)
        parts = sm.run_pass(spec_settings, sim, menu_id, convention, "A", int(sim["replicates"]["rule_choice"]),
                            workers=workers)
        sums = sm.reduce_sums(parts)
        menu = spec.menu_from(spec_settings, menu_id)
        names = _point_names(sm.prior_points(sim, sm.geometry(spec_settings, menu)))
        block = {}
        for b in cfg["budgets"]:
            block[f"{b:g}"] = {}
            for rule in cfg["rules"]:
                s = sums[(0.0, float(b), rule)]
                block[f"{b:g}"][rule] = {f"{tau:g}": {"P_best": _bernoulli(s.data["found"], s.n, names, t),
                                                      "regret": _metric(s.data["regret"], s.data["regret2"], s.n,
                                                                        names, t)}
                                         for t, tau in enumerate(ctx.tau_o)}
        out["conventions"][convention] = {"predictions": block,
                                          "replay_check": replay_check(spec_settings, sim, menu_id, convention,
                                                                       cfg)}
    return out


def replay_check(spec_settings: Mapping[str, Any], sim: Mapping[str, Any], menu_id: str, convention: str,
                 cfg: Mapping[str, Any]) -> dict:
    """What each Llama rule can ask for, counted on 200 simulated replicates, against Gate B-lite's design
    (Llama note section 15 items 3-4). Which units it asks for is data-dependent and is not checked here."""
    menu, geom, ctx, d, points, G, tr = sm._setup(spec_settings, sim, menu_id, convention, range(200))
    obs = sm.observations(geom, ctx, sim, d, G, sm.NoiseCase(float(sim["model"]["u_seed_sd_pp"]["central"]), 0.0),
                          tr["coherent"])
    design = cfg["design"]
    out = {}
    for b in cfg["budgets"]:
        for rule in cfg["rules"]:
            sel = spec.select(ctx, obs, rule=rule, budget=float(b))
            seeds = sel.full_seeds
            two = int((seeds >= 2).sum(axis=1).max())
            four = int((seeds >= 4).sum(axis=1).max())
            most = int(seeds.max())
            fits = (two <= design["units_with_seed_indices_1_2"] and most <= 5
                    and four <= design["units_with_seed_indices_3_4"] and ctx.screen_phi == ctx.a1)
            out[f"{b:g}|{rule}"] = {"max_options_with_2_full_seeds": two, "max_full_seeds_of_one_option": most,
                                    "max_options_with_4_full_seeds": four,
                                    "phi_below_1_requested": ctx.screen_phi != ctx.a1,
                                    "fits_the_design_by_counts": bool(fits)}
    return out


def classifier_row(menus: Mapping[str, Any], pred: Mapping[str, Any]) -> dict:
    cfg = pred["named_diagnostics"]["classifier"]
    rows = {}
    for menu_id in [m for m in cfg["menus"] if m in menus]:
        block = menus[menu_id]
        rows[menu_id] = {}
        for convention, conv in block["conventions"].items():
            rows[menu_id][convention] = {}
            for b, cell in conv["budgets"].items():
                rows[menu_id][convention][b] = {
                    tau: {q: {"Delta": v["Delta"], "c_star": v["c_star"]} for q, v in by_tau["by_quality"].items()}
                    for tau, by_tau in cell["diagnostic"]["by_tau_o"].items()}
    return {"quality_grid": cfg["quality_grid"], "quality_fitted": cfg["quality_fitted"], "c_d": cfg["c_d"],
            "source": cfg["source"], "curves": rows}


# ----- the predictions document --------------------------------------------------------------------------


def build(spec_settings: Mapping[str, Any], sim: Mapping[str, Any], pred: Mapping[str, Any],
          digests: Mapping[str, str], workers: int = 1, timing: dict | None = None) -> bytes:
    """predictions.json's bytes (nothing is written here)."""
    spec.check(spec_settings)
    sm.check(sim)
    check(pred)
    menus: dict = {}
    for menu_id in pred["menus_predicted"]:
        menu = spec.menu_from(spec_settings, menu_id)
        geom = sm.geometry(spec_settings, menu)
        block = {"M": menu.M, "kind": menu.kind, "nested": menu.nested, "rules": sm.menu_rules(menu),
                 "k_grid": sm.k_grid(menu.M), "prior_points": _point_names(sm.prior_points(sim, geom)),
                 "freeze_scope": sim["criterion"]["freeze_scope"], "conventions": {}}
        start = time.monotonic()
        results = sm.simulate_menu(spec_settings, sim, menu_id, list(pred["conventions"]), workers=workers,
                                   placement_convention=pred["conventions"][0], timing=timing)
        if timing is not None:
            timing[menu_id] = round(time.monotonic() - start, 1)
        for i, convention in enumerate(pred["conventions"]):
            res = results[convention]
            ctx = spec.context(spec_settings, menu_id, convention, menu=menu)
            block["conventions"][convention] = {
                "replicates": {"rule_choice": res["n_a"], "diagnostic": res["n_b"], "sensitivity": res["n_c"]},
                "unit": spec_settings["cost_conventions"][convention].get("unit") or spec_settings[
                    "cost_conventions"][convention]["variants"][spec_settings["cost_conventions"][convention][
                        "contents"]]["unit"],
                "costs_in_c0": {"full_run": num(ctx.cost.full), "screen_trial": num(ctx.screen_cost),
                                "promotion": num(ctx.promote_cost(1)), "unit_seconds": num(ctx.cost.unit),
                                "full_run_seconds": num(ctx.cost.full * ctx.cost.unit),
                                "o_bank_seconds": num(spec.o_bank_seconds(spec_settings, convention))},
                "screen": {"o_prompts": ctx.o_prompts, "o_prompt_sd_pp": num(ctx.o_prompt_sd),
                           "l_item_sd_nats": num(ctx.l_item_sd)},
                "budgets": {f"{b:g}": cell_block(res, sim, ctx.tau_o, float(b)) for b in sim["grids"]["budgets"]}}
            if i == 0:
                block["placement"] = {"computed_under": convention, "rule": pred["placement"]["rule"],
                                      "statistic": (pred["placement"]["category"] if not geom.planted else
                                                    {"primary": pred["placement"]["planted_primary"],
                                                     "secondary": pred["placement"]["planted_secondary"]}),
                                      "by_quality": placement_summary(res["placement"], res["points"],
                                                                      pred["placement"]["range_quantiles"],
                                                                      geom.planted, res["ks"])}
        menus[menu_id] = block
    start = time.monotonic()
    llama = llama_block(spec_settings, sim, pred, workers)
    if timing is not None:
        timing["llama"] = round(time.monotonic() - start, 1)
    files = {"spec.py": sha256_file(HERE / "spec.py"), "simulate.py": sha256_file(HERE / "simulate.py"),
             "predict.py": sha256_file(HERE / "predict.py")}
    labels = {**spec_settings["label_entries"], **sim["label_entries"]}
    prov = s1.provenance(Path(__file__).resolve(), digests["selector_predict"],
                         {"selector_spec_settings": digests["selector_spec"],
                          "selector_simulate_settings": digests["selector_simulate"],
                          "spec_py": files["spec.py"], "simulate_py": files["simulate.py"]}, labels)
    doc = {"kind": PREDICTIONS_KIND, "version": 1, "requirement": pred["requirement"],
           "settings_sha256": dict(digests), "code_sha256": files, "provenance": prov,
           "units": spec_settings["budget_unit"], "definitions": pred["definitions"],
           "model": {"u_seed_sd_pp": sim["model"]["u_seed_sd_pp"], "rho_grid": sm.rho_grid(sim),
                     "rho_average_for_rule": bool(sim["model"]["rho_average_for_rule"]),
                     "sensitivities": list(sim["sensitivities"]),
                     "uo_correlation": num(sm.uo_correlation(sim)),
                     "parameter_uncertainty": sim["model"]["parameter_uncertainty"]["mode"],
                     "o_error_model": spec_settings["screen"]["o_error_model"],
                     "screen_upper_quantile": spec_settings["screen"]["upper_quantile"],
                     "se_form": spec_settings["screen"]["se_form"],
                     "tau_l_reference": spec_settings["screen"]["tau_l_reference"],
                     "c_lean_contents": spec_settings["cost_conventions"]["C-lean"]["contents"]},
           "criterion": sim["criterion"], "intervals": pred["intervals"], "c_star_rule": pred["c_star"]["rule"],
           "conventions": pred["conventions"], "menus": menus, "llama": llama,
           "named_diagnostics": {"classifier": classifier_row(menus, pred)}}
    return canonical_json(doc)


def load_all(spec_path: Path, sim_path: Path, pred_path: Path) -> tuple[dict, dict, dict, dict]:
    spec_settings, d1 = spec.load(spec_path)
    sim, d2 = sm.load(sim_path)
    pred, d3 = load(pred_path)
    return spec_settings, sim, pred, {"selector_spec": d1, "selector_simulate": d2, "selector_predict": d3}


# ----- check-inputs --------------------------------------------------------------------------------------


def resolve_input(entry: Mapping[str, Any], root: Path) -> dict:
    """An unpinned input's one file under root: the files that its path_hint names (each <...> part matches one
    folder name) whose SHA-256 starts with its pinned 16-character prefix. Files are hashed only; nothing is read
    for its values. Refuses unless exactly one file matches."""
    hint, prefix = entry.get("path_hint"), entry.get("sha256_prefix")
    if not isinstance(hint, str) or not isinstance(prefix, str) or not re.fullmatch(r"[0-9a-f]{16,63}", prefix):
        raise s1.Refusal(f"input {entry['id']} has no path hint or no hexadecimal prefix of at least 16 characters")
    if hint.startswith(GATE_B_WAVE_PREFIXES) and not entry.get("gate_b_value"):
        raise s1.Refusal(f"input {entry['id']} lies under a Gate B wave folder and is not named as a Gate B value")
    pattern = re.sub(r"<[^<>]*>", "*", hint)
    if pattern.startswith("/") or ".." in Path(pattern).parts:
        raise s1.Refusal(f"input {entry['id']}: the path hint is not a relative path under the root")
    matches = [(p, d) for p in sorted(root.glob(pattern)) if p.is_file() for d in [sha256_file(p)]
               if d.startswith(prefix)]
    if len(matches) != 1:
        raise s1.Refusal(f"input {entry['id']}: {len(matches)} files under the root match its path hint and prefix")
    found, digest = matches[0]
    return {"id": entry["id"], "status": "resolved (copy path and sha256 into the settings, then re-pin)",
            "path": found.relative_to(root).as_posix(), "sha256": digest}


def check_inputs(sim: Mapping[str, Any], root: Path, resolve: bool = False) -> list[dict]:
    """Every listed input's SHA-256 under root; refuses a mismatch, a missing file, or an unnamed Gate B path.
    An unpinned input is reported as unpinned, or with resolve, found by its path hint and prefix."""
    out = []
    for entry in sim["inputs"]:
        path = entry.get("path")
        if path is None:
            if resolve:
                out.append(resolve_input(entry, root))
                continue
            out.append({"id": entry["id"], "status": "unpinned (the lead pins the path)",
                        "sha256_prefix": entry.get("sha256_prefix")})
            continue
        if path.startswith(GATE_B_WAVE_PREFIXES) and not entry.get("gate_b_value"):
            raise s1.Refusal(f"input {entry['id']} lies under a Gate B wave folder and is not named as a Gate B value")
        full = root / path
        if not full.is_file():
            raise s1.Refusal(f"input {entry['id']} is missing under the root")
        digest = sha256_file(full)
        want = entry.get("sha256")
        if want is not None and digest != want:
            raise s1.Refusal(f"input {entry['id']} hashes to {digest}, the settings pin {want}")
        if want is None and not digest.startswith(entry.get("sha256_prefix", "-")):
            raise s1.Refusal(f"input {entry['id']} hashes to {digest}, not the pinned prefix")
        out.append({"id": entry["id"], "status": "ok", "sha256": digest})
    return out


# ----- command line --------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("predict", help="run the frozen grid and write predictions.json")
    p.add_argument("--out", type=Path, required=True, help="output folder (absent or empty)")
    p.add_argument("--workers", type=int, default=1, help="processes (the output does not depend on it)")
    r = sub.add_parser("replay", help="one replay from saved labels")
    r.add_argument("--labels", type=Path, required=True)
    r.add_argument("--labels-sha256", required=True)
    r.add_argument("--menu", required=True)
    r.add_argument("--convention", required=True)
    r.add_argument("--rule", required=True, choices=spec.RULES)
    r.add_argument("--budget", type=float, required=True)
    r.add_argument("--scores", type=Path)
    r.add_argument("--scores-sha256")
    r.add_argument("--k", type=int)
    r.add_argument("--c-d", type=float, default=0.0)
    c = sub.add_parser("check-inputs", help="recompute the listed inputs' SHA-256 under --root")
    c.add_argument("--root", type=Path, required=True)
    c.add_argument("--resolve", action="store_true",
                   help="find each unpinned input by its path hint and SHA-256 prefix (hashes only)")
    for q in (p, r, c):
        q.add_argument("--spec-settings", type=Path, default=spec.SETTINGS_PATH)
        q.add_argument("--simulate-settings", type=Path, default=sm.SETTINGS_PATH)
        q.add_argument("--predict-settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        spec_settings, sim, pred, digests = load_all(args.spec_settings, args.simulate_settings,
                                                     args.predict_settings)
        if args.command == "predict":
            out_dir = args.out.resolve()
            if out_dir.exists() and any(out_dir.iterdir()):
                raise s1.Refusal(f"{out_dir} exists and is not empty: a sealed output never overwrites")
            timing: dict = {}
            start = time.monotonic()
            data = build(spec_settings, sim, pred, digests, workers=args.workers, timing=timing)
            timing["total"] = round(time.monotonic() - start, 1)
            timing_doc = {"kind": "stage1 selector timing", "version": 1, "workers": args.workers,
                          "seconds": timing, "predictions_sha256": sha256_bytes(data),
                          "replicates": sim["replicates"]}
            written = s1.write_new_files(args.out.resolve(), {"predictions.json": data,
                                                              "timing.json": canonical_json(timing_doc)})
            for name, digest in sorted(written.items()):
                print(f"  {digest}  {name}")
            print(f"total {timing['total']} s with {args.workers} workers")
            return 0
        if args.command == "replay":
            raw = args.labels.read_bytes()
            if sha256_bytes(raw) != args.labels_sha256:
                raise s1.Refusal("the saved labels do not hash to --labels-sha256")
            scores = None
            if args.scores is not None:
                sraw = args.scores.read_bytes()
                if sha256_bytes(sraw) != args.scores_sha256:
                    raise s1.Refusal("the scores do not hash to --scores-sha256")
                scores = s1.strict_json(sraw)
            result = spec.replay(spec_settings, args.menu, args.convention, args.rule, args.budget,
                                 s1.strict_json(raw), scores=scores, k=args.k, c_d=args.c_d)
            print(json.dumps(result, sort_keys=True))
            return 0
        for row in check_inputs(sim, args.root.resolve(), resolve=args.resolve):
            print(json.dumps(row, sort_keys=True))
        return 0
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
