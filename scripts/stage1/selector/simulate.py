"""The generative model and the pre-outcome simulation (REQ-17; numpy; Mac, $0).

Every replicate r draws its own arrays through s1common by registry key, with the part (replicate) only, so a
replicate's draws never depend on the batch, the policy, the grid point or the worker that asks (common random
numbers, lead decisions L15 (4)). The simulation calls spec.select, the function the replay calls.

The model of one replicate, per (shape, size) grid point of the prior:
  effects   category menus: one winner (a uniform option gets the size) or a spread with the same total (the
            size times Dirichlet(1, ..., 1) shares); planted menus: the plant's cell gets the size, every other
            cell 0 (the background is 0 by default). Keep has G = 0. A group of cells has the sum of its cells.
  U         U(option, seed j, phi, psi) = U0 - G phi^kappa + sigma sqrt(rho) s_j + sd_T T + sqrt(v) e
            + sqrt(v (1/psi - 1)) e_psi: s_j the shared seed shift (one per seed index); T the option's training
            noise per (seed, phi); e the full evaluation's sampling noise; e_psi a psi-subsample's own deviation.
            v = the sampling variance of the convention's evaluation (C-full 3 samples per harm prompt, C-lean 1);
            sd_T^2 = (1 - rho) sigma^2 - v_full, so a C-full full run has total SD sigma. The 2x sensitivity gives
            one option total SD 2 sigma with the shared part unchanged. sigma = 2.65 pp central, 3.85 pp high;
            never the Gate B noise-gate value.
  O         O(option, seed) = O(a0) + its true O effect + sd_O (rho_UO eps + sqrt(1 - rho_UO^2) eta)
            (+ a bank term per option, SD = the prompt part at the convention's over-refusal prompts, 500
            after O-ext, under the prompts-random error model); eps is the full run's standardized U noise.
            Feasible at tau_O if O(a0) + effect - O(theta0) <= tau_O.
  L         L(option, seed) = its true L effect + sd_L eta; feasible if effect - reference effect <= tau_L.
Keep's 3 (or 6) seeds are C-full runs; the dose-matched L reference arm R has its own seeds.

Frozen choices (REQ-17; lead decisions L15 (1), (6)): per (menu, M, B) cell the runs-only rule with the largest
E[G(pick)], with equal weight per (shape, size) grid point, per tau_O point and per cost convention (the
conventions' per-replicate criteria are averaged; the draws are shared, so the pairing holds), at sigma central
and, when rho_average_for_rule is true, on the equal-weight average over the settings' rho grid (in force: A7's
{0, 0.67}, LW-12 and LN-10), else at rho = 0; a tie (a paired difference below 2 Monte Carlo SE under common
random numbers) goes to the simpler rule. Then per (cell, c_d/c0) the diagnostic's k by the same criterion, also
averaged over the quality grid (and over rho with the rho average); a tie goes to the larger k. The reported
curves stay at rho = 0; the rho_0.67 sensitivity reports them at rho = 0.67.
The settings switch criterion.freeze_scope = menu_m_b_convention chooses per (menu, M, B, convention) instead.

The settings file settings/selector_simulate.json is pinned by SHA-256 below.
"""

from __future__ import annotations

import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist
from typing import Any, Mapping

import numpy as np

HERE = Path(__file__).resolve().parent
STAGE1 = HERE.parent
REPO = STAGE1.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1.selector import spec  # noqa: E402

SETTINGS_PATH = STAGE1 / "settings" / "selector_simulate.json"
SETTINGS_SHA256 = "4d9e0064828338bcfdd3703c5039fb179dd2ec7f33501cc448cceb94bb8302b9"
SETTINGS_NAME = "selector_simulate"
DRAW_KEYS = {"noise": "selector.noise", "seed_shift": "selector.seed_shift", "hetero": "selector.hetero",
             "effects": "selector.effects", "plant": "selector.plant", "diagnostic": "selector.diagnostic",
             "uninformative": "selector.uninformative", "sim2": "selector.sim2", "params": "selector.params"}
COMPONENTS = 5                   # the noise array's last axis: U training, U evaluation, O, L, O bank
FOUND_TOL = 1e-12
FREEZE_SCOPES = ("menu_m_b", "menu_m_b_convention")


# ----- settings ------------------------------------------------------------------------------------------


def load(path: str | Path = SETTINGS_PATH) -> tuple[dict, str]:
    settings, digest = s1.load_settings(path, SETTINGS_SHA256, SETTINGS_NAME)
    check(settings)
    return settings, digest


def check(sim: Mapping[str, Any]) -> None:
    if sim["draws"] != DRAW_KEYS:
        raise s1.Refusal("the simulate settings name other registry keys for the draws")
    model = sim["model"]
    if model["u_seed_sd_pp"] != {"central": 2.65, "high": 3.85}:
        raise s1.Refusal("the U noise is 2.65 pp central and 3.85 pp high (lead decisions L15 (1))")
    if model["rho_mode"] not in model["rho_grids"]:
        raise s1.Refusal("rho_mode names no rho grid of the settings")
    if model["rho_grids"]["default"] != [0.0]:
        raise s1.Refusal("the default rho grid is {0} (W1-14 item 1; RC-18)")
    if any(0.0 not in grid for grid in model["rho_grids"].values()):
        raise s1.Refusal("every rho grid holds 0 (the predictions and the Delta curves are read at rho = 0)")
    if sim["criterion"]["freeze_scope"] not in FREEZE_SCOPES:
        raise s1.Refusal(f"criterion.freeze_scope is not one of {', '.join(FREEZE_SCOPES)}")
    if model["parameter_uncertainty"]["mode"] not in ("fixed", "posterior_2df"):
        raise s1.Refusal("parameter_uncertainty.mode is not fixed or posterior_2df")
    if model["uo_correlation"]["mode"] not in ("gate_a_seeds", "fixed"):
        raise s1.Refusal("uo_correlation.mode is not gate_a_seeds or fixed")
    if 0.0 not in sim["grids"]["c_d_grid"] or sim["grids"]["c_d_grid"] != sorted(sim["grids"]["c_d_grid"]):
        raise s1.Refusal("the c_d/c0 grid must rise and include 0 (lead decisions L15 (3))")


def rho_grid(sim: Mapping[str, Any], requested: list[float] | None = None) -> list[float]:
    """The settings' rho grid; any other grid refuses (W1-14 tests; RC-18)."""
    grid = list(sim["model"]["rho_grids"][sim["model"]["rho_mode"]])
    if requested is not None and list(requested) != grid:
        raise s1.Refusal(f"a rho grid other than the settings' grid {grid} was asked for")
    return grid


def seed_correlation(u_values: list[float], o_values: list[float]) -> float:
    """Pearson correlation of per-seed U and O (the seed-level U-O correlation; 3 seeds give 1 df)."""
    u, o = np.asarray(u_values, float), np.asarray(o_values, float)
    if u.shape != o.shape or u.size < 3:
        raise s1.Refusal("the U-O correlation needs at least 3 paired seed values")
    du, do = u - u.mean(), o - o.mean()
    den = math.sqrt(float((du ** 2).sum() * (do ** 2).sum()))
    if den == 0.0:
        raise s1.Refusal("the U-O correlation is undefined (no spread)")
    return float((du * do).sum() / den)


def uo_correlation(sim: Mapping[str, Any]) -> float:
    cfg = sim["model"]["uo_correlation"]
    if cfg["mode"] == "gate_a_seeds":
        return seed_correlation(cfg["gate_a_u_pp"], cfg["gate_a_o_pp"])
    return float(cfg["fixed_value"])


# ----- geometry ------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Geometry:
    menu: spec.Menu
    planted: bool
    leaf_rows: np.ndarray | None      # (128,) rows per leaf of the planted corpus, in nesting order
    leaves_per_cell: int              # planted menus: leaves in one cell of this menu
    units: int
    eligible_rows: int                # the plant leaf's size (L12 (5): a 37-row leaf)

    @property
    def M(self) -> int:
        return self.menu.M

    @property
    def axis(self) -> int:
        return self.menu.axis_size()

    @property
    def noise_options(self) -> int:
        return 2 + self.axis           # keep, the L reference arm R, then the menu axis


def geometry(spec_settings: Mapping[str, Any], menu: spec.Menu) -> Geometry:
    if menu.kind != "planted":
        return Geometry(menu, False, None, 1, 0, 0)
    geo = spec_settings["planted_geometry"]
    quarters = np.array(geo["quarter_rows"], dtype=np.int64)
    leaf_rows = np.tile(quarters, geo["units"] * geo["quartiles"])
    leaves = leaf_rows.size
    if leaves % menu.M:
        raise s1.Refusal(f"menu {menu.id}: {menu.M} cells do not divide {leaves} leaves")
    return Geometry(menu, True, leaf_rows, leaves // menu.M, int(geo["units"]), int(geo["plant_leaf_rows"]))


# ----- draws ---------------------------------------------------------------------------------------------


def draws(geom: Geometry, ctx: spec.Context, sim: Mapping[str, Any], replicates: range) -> dict:
    """Each replicate's own draws, stacked (the order of the replicates in a batch changes nothing)."""
    J, n_phi, n_psi, M = ctx.max_seeds, len(ctx.phi_grid), len(ctx.psi_grid), geom.M
    shape = (geom.noise_options, J, n_phi, n_psi, COMPONENTS)
    out: dict[str, list] = {k: [] for k in ("noise", "shift", "hetero", "winner", "shares", "leaf", "diag",
                                             "uninformative", "sim2", "params")}
    posterior = sim["model"]["parameter_uncertainty"]["mode"] == "posterior_2df"
    for r in replicates:
        out["noise"].append(s1.numpy_generator(DRAW_KEYS["noise"], r).standard_normal(shape))
        out["shift"].append(s1.numpy_generator(DRAW_KEYS["seed_shift"], r).standard_normal(J))
        out["hetero"].append(int(s1.numpy_generator(DRAW_KEYS["hetero"], r).integers(M)))
        if geom.planted:
            g = s1.numpy_generator(DRAW_KEYS["plant"], r)
            unit = int(g.integers(geom.units))
            per_unit = geom.leaf_rows.size // geom.units
            in_unit = np.arange(unit * per_unit, (unit + 1) * per_unit)
            eligible = in_unit[geom.leaf_rows[in_unit] == geom.eligible_rows]
            out["leaf"].append(int(eligible[int(g.integers(eligible.size))]))
            out["diag"].append(s1.numpy_generator(DRAW_KEYS["diagnostic"], r).standard_normal(int(geom.leaf_rows.sum())))
        else:
            g = s1.numpy_generator(DRAW_KEYS["effects"], r)
            out["winner"].append(int(g.integers(M)))
            out["shares"].append(g.dirichlet(np.ones(M)))
            out["diag"].append(s1.numpy_generator(DRAW_KEYS["diagnostic"], r).standard_normal(M + 1))
        out["uninformative"].append(s1.numpy_generator(DRAW_KEYS["uninformative"], r).permutation(M))
        out["sim2"].append(float(s1.numpy_generator(DRAW_KEYS["sim2"], r).random()))
        if posterior:
            df = sim["model"]["parameter_uncertainty"]["posterior_2df"]["df"]
            out["params"].append(s1.numpy_generator(DRAW_KEYS["params"], r).chisquare(df, size=2))
    return {k: np.asarray(v) if v else None for k, v in out.items()}


# ----- the prior and the truth ---------------------------------------------------------------------------


def prior_points(sim: Mapping[str, Any], geom: Geometry) -> list[tuple[str, float]]:
    prior = sim["prior"]["planted" if geom.planted else "category"]
    return [(shape, float(size)) for shape in prior["shapes"] for size in prior["sizes_pp"]]


def planted_cell(geom: Geometry, leaf: np.ndarray) -> np.ndarray:
    return leaf // geom.leaves_per_cell


def tree_sums(G: np.ndarray, M: int) -> np.ndarray:
    """(..., M) option effects -> (..., 2M - 2) on the nested axis: options, then inner nodes 2..M-1."""
    node = np.zeros(G.shape[:-1] + (2 * M,))
    node[..., M:] = G
    for h in range(M - 1, 0, -1):
        node[..., h] = node[..., 2 * h] + node[..., 2 * h + 1]
    return np.concatenate([node[..., M:], node[..., 2:M]], axis=-1)


def true_effects(geom: Geometry, d: dict, points: list[tuple[str, float]], sim: Mapping[str, Any]) -> np.ndarray:
    """(P, R, M) true G of the menu options."""
    R, M = len(d["sim2"]), geom.M
    G = np.zeros((len(points), R, M))
    for p, (shape, size) in enumerate(points):
        if geom.planted:
            background = float(sim["prior"]["planted"]["background_pp"])
            G[p] = background
            G[p, np.arange(R), planted_cell(geom, d["leaf"])] = size + background
        elif shape == "one_winner":
            G[p, np.arange(R), d["winner"]] = size
        elif shape == "spread":
            G[p] = size * d["shares"]
        else:
            raise s1.Refusal(f"no effect shape {shape!r}")
    return G


def per_option(menu: spec.Menu, cfg: Mapping[str, Any]) -> np.ndarray:
    unknown = set(cfg["per_option"]) - set(menu.ids)
    if unknown:
        raise s1.Refusal(f"true effects name {len(unknown)} options outside menu {menu.id}")
    return np.array([float(cfg["per_option"].get(oid, cfg["default"])) for oid in menu.ids])


def truth(geom: Geometry, ctx: spec.Context, sim: Mapping[str, Any], G: np.ndarray) -> dict:
    """True feasibility (rows, M, n_tau), V (rows, n_tau) = max(0, max over truly feasible options of G)."""
    menu, model = geom.menu, sim["model"]
    effects = model["true_effects"]
    d_o, d_l = per_option(menu, effects["o_pp"]), per_option(menu, effects["l_nats"])
    reference = 0.0 if ctx.tau_l_reference == "a0" else float(effects["l_reference_r_nats"])
    failing = set(effects["coherence_failures"])
    if failing - set(menu.ids):
        raise s1.Refusal("a coherence failure names an option outside the menu")
    coherent = np.array([oid not in failing for oid in menu.ids])
    o_ok = (model["o"]["a0_mean_pp"] + d_o - ctx.o_theta0)[:, None] <= np.asarray(ctx.tau_o)[None, :]
    l_ok = (d_l - reference) <= ctx.tau_l
    ok = o_ok & l_ok[:, None] & (coherent[:, None] if ctx.coherence_gate else True)
    rows = G.reshape(-1, G.shape[-1])
    feasible = np.broadcast_to(ok, (rows.shape[0],) + ok.shape)
    best = np.where(feasible, rows[..., None], -np.inf).max(axis=1)
    return {"feasible": feasible, "V": np.maximum(best, 0.0), "coherent": coherent, "G": rows}


# ----- observations --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class NoiseCase:
    sigma: float
    rho: float
    hetero: bool = False


def observations(geom: Geometry, ctx: spec.Context, sim: Mapping[str, Any], d: dict, G: np.ndarray,
                 case: NoiseCase, coherent: np.ndarray) -> spec.Observations:
    """spec.Observations for the rows (P x R) of one convention and one noise case, from the replicates' draws."""
    model = sim["model"]
    P, R, M = G.shape
    Z = d["noise"]
    J, a1, c1 = ctx.max_seeds, ctx.a1, ctx.c1
    v_full = float(model["u_sampling_variance_full_pp2"])
    v = v_full * model["u_samples_full"] / ctx.cost.samples_per_prompt
    sigma, rho = case.sigma, case.rho
    train_var = (1.0 - rho) * sigma ** 2 - v_full
    if train_var < 0:
        raise s1.Refusal(f"sigma {sigma} and rho {rho} leave no room for the C-full sampling variance")
    train_sd = np.full(geom.noise_options, math.sqrt(train_var))
    if case.hetero:
        mult = float(model["hetero"]["multiplier"])
        train_sd = np.broadcast_to(train_sd, (R, geom.noise_options)).copy()
        train_sd[np.arange(R), 2 + d["hetero"]] = math.sqrt((mult ** 2 - rho) * sigma ** 2 - v_full)
    else:
        train_sd = np.broadcast_to(train_sd, (R, geom.noise_options))
    shared = sigma * math.sqrt(rho) * d["shift"]                                   # (R, J)
    T = Z[:, :, :, :, c1, 0]                                                     # (R, opt, J, phi)
    E = Z[:, :, :, :, c1, 1]
    psi = np.asarray(ctx.psi_grid)
    sub_sd = np.sqrt(np.maximum(v * (1.0 / psi - 1.0), 0.0))                     # 0 at psi = 1
    base = shared[:, None, :, None] + train_sd[:, :, None, None] * T + math.sqrt(v) * E
    u_noise = base[..., None] + sub_sd * Z[..., 1]                               # (R, opt, J, phi, psi)
    phi = np.asarray(ctx.phi_grid) ** float(model["phi_effect_exponent"])
    G_axis = tree_sums(G, M) if geom.menu.nested else G                          # (P, R, axis)
    u0 = float(model["u_a0_pp"])
    U = u0 - G_axis[:, :, :, None, None, None] * phi[None, None, None, None, :, None] + u_noise[None, :, 2:]
    keep_j = geom.menu.keep_seeds
    keep_u = (u0 + shared[:, :keep_j] + train_sd[:, 0, None] * T[:, 0, :keep_j, a1]
              + math.sqrt(v_full) * E[:, 0, :keep_j, a1])
    # O and L at full runs
    total_sd = np.sqrt(rho * sigma ** 2 + train_sd[:, 2:2 + M] ** 2 + v)              # (R, M)
    eps = np.where(total_sd[:, :, None] > 0, base[:, 2:2 + M, :, a1] / np.where(total_sd > 0, total_sd, 1.0)[:, :, None],
                   0.0)
    o_cfg, l_cfg = model["o"], model["l"]
    o_sd, l_sd = float(o_cfg["seed_sd_pp"]), float(l_cfg["seed_sd_nats"])
    o_scale, l_scale = np.full(R, o_sd), np.full(R, l_sd)
    if model["parameter_uncertainty"]["mode"] == "posterior_2df":
        df = model["parameter_uncertainty"]["posterior_2df"]["df"]
        o_scale = o_sd * np.sqrt(df / d["params"][:, 0])
        l_scale = l_sd * np.sqrt(df / d["params"][:, 1])
    rho_uo = uo_correlation(sim)
    d_o = per_option(geom.menu, model["true_effects"]["o_pp"])
    d_l = per_option(geom.menu, model["true_effects"]["l_nats"])
    o_eta = Z[:, 2:2 + M, :, a1, c1, 2]
    O = (o_cfg["a0_mean_pp"] + d_o[None, :, None]
         + o_scale[:, None, None] * (rho_uo * eps + math.sqrt(1.0 - rho_uo ** 2) * o_eta))
    if ctx.o_error_model == "prompts_random":
        O = O + ctx.o_prompt_sd * Z[:, 2:2 + M, 0, a1, c1, 4][:, :, None]
    L = d_l[None, :, None] + l_scale[:, None, None] * Z[:, 2:2 + M, :, a1, c1, 3]
    keep_o = o_cfg["a0_mean_pp"] + o_scale[:, None] * Z[:, 0, :keep_j, a1, c1, 2]
    keep_l = l_scale[:, None] * Z[:, 0, :keep_j, a1, c1, 3]
    ref_j = int(model["reference_r_seeds"])
    ref_l = (float(model["true_effects"]["l_reference_r_nats"])
             + l_scale[:, None] * Z[:, 1, :ref_j, a1, c1, 3])

    def rows(x: np.ndarray) -> np.ndarray:                                       # (R, ...) -> (P x R, ...)
        return np.broadcast_to(x, (P,) + x.shape).reshape((P * R,) + x.shape[1:])

    return spec.Observations(u=U.reshape((P * R,) + U.shape[2:]), o=rows(O), l=rows(L), keep_u=rows(keep_u),
                             keep_o=rows(keep_o), keep_l=rows(keep_l),
                             coherent=np.broadcast_to(coherent, (P * R, M)), ref_l=rows(ref_l))


# ----- the diagnostic's scores ---------------------------------------------------------------------------


def quality_points(sim: Mapping[str, Any], geom: Geometry, which: str = "main") -> list[dict]:
    q = sim["quality"]["planted" if geom.planted else "category"]
    if geom.planted:
        if which == "main":
            return [{"kind": "row_auc", "auc": float(a)} for a in q["row_auc_grid"]]
        return [{"kind": "rs", "r": float(r)} for r in q["rs_sensitivity_r_grid"]]
    if which == "main":
        out = [{"kind": "rs", "r": float(r)} for r in q["r_grid"]]
        return out + ([{"kind": "uninformative"}] if q["uninformative"] else [])
    return [{"kind": "sim2", "p_best": float(q["sim2"]["p_best"])}]


def quality_name(point: Mapping[str, Any]) -> str:
    if point["kind"] == "rs":
        return f"r={point['r']:g}"
    if point["kind"] == "row_auc":
        return f"auc={point['auc']:g}"
    if point["kind"] == "sim2":
        return "sim2"
    return "uninformative"


def _cell_sums(geom: Geometry, diag: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-cell sums of the row draws (R, M) and the cell sizes (M,)."""
    starts = np.concatenate([[0], np.cumsum(geom.leaf_rows)[:-1]])
    leaf_sums = np.add.reduceat(diag, starts, axis=1)                             # (R, 128)
    R = diag.shape[0]
    cells = leaf_sums.reshape(R, geom.M, geom.leaves_per_cell).sum(axis=2)
    sizes = geom.leaf_rows.reshape(geom.M, geom.leaves_per_cell).sum(axis=1)
    return cells, sizes


def scores(geom: Geometry, sim: Mapping[str, Any], d: dict, G: np.ndarray, point: Mapping[str, Any]) -> np.ndarray:
    """(P x R, M) diagnostic scores under one quality point (lead decisions L15 (6))."""
    P, R, M = G.shape
    position = np.argsort(d["uninformative"], axis=1)                            # position of option i in the order
    uninformative = np.broadcast_to(-position.astype(float), (P, R, M))
    if point["kind"] == "uninformative":
        return uninformative.reshape(P * R, M)
    if point["kind"] == "sim2":
        best = G.argmax(axis=2)                                                  # (P, R)
        out = uninformative.copy()
        lucky = d["sim2"] < point["p_best"]
        p_idx, r_idx = np.meshgrid(np.arange(P), np.arange(R), indexing="ij")
        out[p_idx, r_idx, best] = np.where(lucky[None, :], np.inf, out[p_idx, r_idx, best])
        top = np.argmax(out, axis=2)
        demote = ~lucky[None, :] & (top == best)
        second = np.argsort(-out, axis=2)[:, :, 1]
        swap = out.copy()
        swap[p_idx, r_idx, best] = out[p_idx, r_idx, second]
        swap[p_idx, r_idx, second] = out[p_idx, r_idx, best]
        return np.where(demote[..., None], swap, out).reshape(P * R, M)
    if geom.planted:
        cells, sizes = _cell_sums(geom, d["diag"])
        if point["kind"] == "row_auc":
            mu = math.sqrt(2.0) * NormalDist().inv_cdf(point["auc"])
            plant = np.zeros((R, M))
            plant[np.arange(R), planted_cell(geom, d["leaf"])] = geom.eligible_rows * mu
            return np.broadcast_to((plant + cells) / sizes, (P, R, M)).reshape(P * R, M)
        z = cells / np.sqrt(sizes)
    else:
        z = d["diag"][:, 1:M + 1]
    s = G.std(axis=2)                                                            # (P, R), over options other than keep
    score = G + point["r"] * s[..., None] * z[None, :, :]
    return np.where((s > 0)[..., None], score, uninformative).reshape(P * R, M)


def placement_values(geom: Geometry, ctx: spec.Context, sim: Mapping[str, Any], d: dict, G: np.ndarray,
                     score: np.ndarray, k_grid: list[int], point: Mapping[str, Any]) -> dict:
    """Placement statistics per row (lead decisions L15 (7); W1-15 item 3), never fitted here."""
    P, R, M = G.shape
    out = {}
    if geom.planted:
        planted = np.broadcast_to(planted_cell(geom, d["leaf"]), (P, R)).reshape(-1)
        order = np.lexsort((np.broadcast_to(ctx.tie_rank, score.shape), -score), axis=-1)
        rank = np.argmax(order == planted[:, None], axis=1)                       # 0 = first
        out["top_k_hit"] = {k: (rank < k) for k in k_grid}
        if point["kind"] == "row_auc":
            mu = math.sqrt(2.0) * NormalDist().inv_cdf(point["auc"])
            starts = np.concatenate([[0], np.cumsum(geom.leaf_rows)])
            auc = np.empty(R)
            for r in range(R):
                leaf = d["leaf"][r]
                lo, hi = starts[leaf], starts[leaf + 1]
                dolly = np.sort(np.concatenate([d["diag"][r, :lo], d["diag"][r, hi:]]))
                plant = d["diag"][r, lo:hi] + mu
                auc[r] = np.searchsorted(dolly, plant, side="left").sum() / (plant.size * dolly.size)
            out["row_auc"] = np.broadcast_to(auc, (P, R)).reshape(-1)
        return out
    # category: Spearman rho of the scores against the wave-1 D_u (one C-full run per unit at seed index 0)
    model = sim["model"]
    v_full = float(model["u_sampling_variance_full_pp2"])
    sigma = float(model["u_seed_sd_pp"]["central"])
    T, E = d["noise"][:, 2:2 + M, 0, ctx.a1, ctx.c1, 0], d["noise"][:, 2:2 + M, 0, ctx.a1, ctx.c1, 1]
    noise = math.sqrt(sigma ** 2 - v_full) * T + math.sqrt(v_full) * E
    D = (G - noise[None]).reshape(P * R, M)
    out["spearman_rho"] = _spearman(score, D)
    return out


def _ranks(x: np.ndarray) -> np.ndarray:
    return np.argsort(np.argsort(x, axis=1, kind="stable"), axis=1, kind="stable").astype(float)


def _spearman(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ra, rb = _ranks(a), _ranks(b)
    ra -= ra.mean(axis=1, keepdims=True)
    rb -= rb.mean(axis=1, keepdims=True)
    return (ra * rb).sum(axis=1) / np.sqrt((ra ** 2).sum(axis=1) * (rb ** 2).sum(axis=1))


# ----- outcomes and sums ---------------------------------------------------------------------------------


def outcome(selection: spec.Selection, tr: dict) -> dict:
    """G(pick) (a truly infeasible pick scores 0 and is a violation), found, violation; each (rows, n_tau)."""
    pick, G, feasible, V = selection.pick, tr["G"], tr["feasible"], tr["V"]
    n, n_tau = pick.shape
    rows = np.arange(n)[:, None]
    safe = np.maximum(pick, 0)
    is_keep = pick == spec.KEEP
    ok = np.where(is_keep, True, feasible[rows, safe, np.arange(n_tau)[None, :]])
    g = np.where(is_keep, 0.0, np.where(ok, G[rows, safe], 0.0))
    return {"g": g, "found": g >= V - FOUND_TOL, "violation": ~ok, "regret": V - g, "spent": selection.spent}


class Sums:
    """Sums over replicates of per-row values, kept per (prior point, tau_O)."""

    def __init__(self, P: int, n_tau: int):
        self.n = 0
        self.data = {name: np.zeros((P, n_tau)) for name in ("g", "g2", "found", "violation", "regret", "regret2",
                                                            "d", "d2")}
        self.spent = 0.0

    def add(self, res: dict, P: int, paired: np.ndarray | None = None) -> None:
        R = res["g"].shape[0] // P
        shape = (P, R, -1)
        g = res["g"].reshape(shape)
        self.data["g"] += g.sum(axis=1)
        self.data["g2"] += (g ** 2).sum(axis=1)
        self.data["found"] += res["found"].reshape(shape).sum(axis=1)
        self.data["violation"] += res["violation"].reshape(shape).sum(axis=1)
        regret = res["regret"].reshape(shape)
        self.data["regret"] += regret.sum(axis=1)
        self.data["regret2"] += (regret ** 2).sum(axis=1)
        if paired is not None:
            diff = g - paired.reshape(shape)
            self.data["d"] += diff.sum(axis=1)
            self.data["d2"] += (diff ** 2).sum(axis=1)
        self.spent += float(res["spent"].sum())
        self.n += R

    def merge(self, other: "Sums") -> None:
        for name in self.data:
            self.data[name] += other.data[name]
        self.spent += other.spent
        self.n += other.n


def criterion_values(res: dict, P: int, tau_weights: np.ndarray) -> np.ndarray:
    """Per replicate: G(pick) averaged with equal weight over the prior grid points and the tau_O points."""
    R = res["g"].shape[0] // P
    return (res["g"].reshape(P, R, -1).mean(axis=0) * tau_weights).sum(axis=1)


# ----- the per-chunk passes ------------------------------------------------------------------------------


def k_grid(M: int) -> list[int]:
    out, k = [], 1
    while k < M:
        out.append(k)
        k *= 2
    return out + [M]


def menu_rules(menu: spec.Menu) -> list[str]:
    return ["one_shot", "halving"] + (["bisection"] if menu.nested else [])


def _setup(spec_settings: Mapping[str, Any], sim: Mapping[str, Any], menu_id: str, convention: str, reps: range):
    menu = spec.menu_from(spec_settings, menu_id)
    geom = geometry(spec_settings, menu)
    ctx = spec.context(spec_settings, menu_id, convention, menu=menu)
    d = draws(geom, ctx, sim, reps)
    points = prior_points(sim, geom)
    G = true_effects(geom, d, points, sim)
    tr = truth(geom, ctx, sim, G)
    return menu, geom, ctx, d, points, G, tr


def run_chunk(task: Mapping[str, Any]) -> dict:
    """One chunk of replicates of one menu and one convention, for one pass:
    A: every runs-only rule at every B (central noise; every rho of the grid);
    B: the diagnostic grid (every c_d, k and main quality point) with the frozen rule, plus the placement
       statistics; the sums at rho = 0, the k criterion at rho = 0 (or averaged over the rho grid with equal
       weight when rho_average_for_rule is true, W1-14 item 4: the rule and k by the same criterion);
    C: the sensitivities, for every runs-only rule and the frozen diagnostic k."""
    spec_settings, sim = task["spec"], task["sim"]
    reps = range(task["start"], task["stop"])
    menu, geom, ctx, d, points, G, tr = _setup(spec_settings, sim, task["menu"], task["convention"], reps)
    P, R = len(points), len(reps)
    n_tau = len(ctx.tau_o)
    tau_w = np.full(n_tau, 1.0 / n_tau)
    budgets = [float(b) for b in sim["grids"]["budgets"]]
    sigma_c = float(sim["model"]["u_seed_sd_pp"]["central"])
    out: dict[str, Any] = {"n": R, "P": P}
    if task["pass"] == "A":
        out["V"] = tr["V"].reshape(P, R, n_tau).sum(axis=1)
        out["V2"] = (tr["V"].reshape(P, R, n_tau) ** 2).sum(axis=1)
        crit: dict = {}
        sums: dict = {}
        for rho in rho_grid(sim):
            obs = observations(geom, ctx, sim, d, G, NoiseCase(sigma_c, rho), tr["coherent"])
            for b in budgets:
                for rule in menu_rules(menu):
                    res = outcome(spec.select(ctx, obs, rule=rule, budget=b), tr)
                    s = Sums(P, n_tau)
                    s.add(res, P)
                    sums[(rho, b, rule)] = s
                    crit[(rho, b, rule)] = criterion_values(res, P, tau_w)
        out["sums"], out["crit"] = sums, crit
        return out
    frozen = task["frozen"]
    if task["pass"] == "B":
        k_rhos = rho_grid(sim) if sim["model"]["rho_average_for_rule"] else [0.0]
        obs_by_rho = {rho: observations(geom, ctx, sim, d, G, NoiseCase(sigma_c, rho), tr["coherent"])
                      for rho in k_rhos}
        qpoints = quality_points(sim, geom, "main")
        q_scores = [scores(geom, sim, d, G, q) for q in qpoints]
        ks = k_grid(menu.M)
        sums, crit = {}, {}
        for rho, b in [(rho, b) for rho in k_rhos for b in budgets]:
            obs = obs_by_rho[rho]
            rule = frozen["rule"][str(b)]
            base = outcome(spec.select(ctx, obs, rule=rule, budget=b), tr)
            for c_d in sim["grids"]["c_d_grid"]:
                per_k = crit.setdefault((b, float(c_d)), np.zeros((R, len(ks))))
                for qi, q in enumerate(qpoints):
                    for ki, k in enumerate(ks):
                        res = outcome(spec.select(ctx, obs, rule=rule, budget=b, scores=q_scores[qi], k=k,
                                                  c_d=float(c_d)), tr)
                        if rho == 0.0:
                            s = Sums(P, n_tau)
                            s.add(res, P, paired=base["g"])
                            sums[(b, float(c_d), quality_name(q), k)] = s
                        per_k[:, ki] += criterion_values(res, P, tau_w) / (len(qpoints) * len(k_rhos))
        out["sums"], out["crit"] = sums, crit
        place = {}
        if task["placement"]:                         # placement reads no cost: one convention computes it
            for qi, q in enumerate(qpoints + quality_points(sim, geom, "report")):
                score = q_scores[qi] if qi < len(qpoints) else scores(geom, sim, d, G, q)
                place[quality_name(q)] = placement_values(geom, ctx, sim, d, G, score, ks, q)
        out["placement"] = place
        return out
    if task["pass"] == "C":
        cases = sensitivity_cases(sim)
        sums = {}
        qpoints = quality_points(sim, geom, "main") + quality_points(sim, geom, "report")
        q_scores = [scores(geom, sim, d, G, q) for q in qpoints]
        for name, case in cases.items():
            obs = observations(geom, ctx, sim, d, G, case, tr["coherent"])
            for b in budgets:
                rule = frozen["rule"][str(b)]
                base = None
                for r_name in menu_rules(menu):
                    res = outcome(spec.select(ctx, obs, rule=r_name, budget=b), tr)
                    s = Sums(P, n_tau)
                    s.add(res, P)
                    sums[(name, b, "runs", r_name)] = s
                    if r_name == rule:
                        base = res
                for c_d in sim["grids"]["c_d_grid"]:
                    k = frozen["k"][f"{b:g}|{float(c_d):g}"]
                    for qi, q in enumerate(qpoints):
                        res = outcome(spec.select(ctx, obs, rule=rule, budget=b, scores=q_scores[qi], k=k,
                                                  c_d=float(c_d)), tr)
                        s = Sums(P, n_tau)
                        s.add(res, P, paired=base["g"])
                        sums[(name, b, float(c_d), quality_name(q))] = s
        out["sums"] = sums
        return out
    raise s1.Refusal(f"no pass {task['pass']!r}")


def sensitivity_cases(sim: Mapping[str, Any]) -> dict[str, NoiseCase]:
    """The report-only noise cases (the rule and k never depend on them)."""
    model = sim["model"]
    central, high = float(model["u_seed_sd_pp"]["central"]), float(model["u_seed_sd_pp"]["high"])
    out = {}
    for name in sim["sensitivities"]:
        if name == "central":
            out[name] = NoiseCase(central, 0.0)
        elif name == "sigma_high":
            out[name] = NoiseCase(high, 0.0)
        elif name == "hetero_2x":
            out[name] = NoiseCase(central, 0.0, True)
        elif name.startswith("rho_"):
            rho = float(name[4:])
            if rho not in model["rho_grids"]["a7_switch"]:
                raise s1.Refusal(f"sensitivity {name}: rho is not on the A7 switch grid")
            out[name] = NoiseCase(central, rho)
        else:
            raise s1.Refusal(f"no sensitivity {name!r}")
    return out


# ----- running the chunks and reducing -------------------------------------------------------------------


def chunks(total: int, size: int) -> list[tuple[int, int]]:
    return [(start, min(start + size, total)) for start in range(0, total, size)]


def run_pass(spec_settings: Mapping[str, Any], sim: Mapping[str, Any], menu_id: str, convention: str, which: str,
             replicates: int, frozen: Mapping[str, Any] | None = None, workers: int = 1,
             placement: bool = False) -> list[dict]:
    """Every chunk of one pass, in chunk order (the result does not depend on the number of workers)."""
    size = int(sim["replicates"]["chunk"][menu_id])
    tasks = [{"spec": spec_settings, "sim": sim, "menu": menu_id, "convention": convention, "pass": which,
              "start": a, "stop": b, "frozen": frozen, "placement": placement} for a, b in chunks(replicates, size)]
    if workers <= 1 or len(tasks) == 1:
        return [run_chunk(t) for t in tasks]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(run_chunk, tasks))


def reduce_sums(parts: list[dict]) -> dict:
    out: dict = {}
    for part in parts:
        for key, s in part["sums"].items():
            if key in out:
                out[key].merge(s)
            else:
                out[key] = s
    return out


def reduce_crit(parts: list[dict]) -> dict:
    keys = parts[0]["crit"].keys()
    return {k: np.concatenate([p["crit"][k] for p in parts], axis=0) for k in keys}


def mean_se(values: np.ndarray) -> tuple[float, float]:
    n = values.shape[0]
    return float(values.mean()), float(values.std(ddof=1) / math.sqrt(n)) if n > 1 else float("nan")


def choose_rule(crit: Mapping[str, np.ndarray], order: list[str], tie_se: float) -> dict:
    """The rule with the largest mean; a paired difference below tie_se Monte Carlo SE goes to the simpler rule."""
    means = {r: float(crit[r].mean()) for r in order}
    best = max(order, key=lambda r: (means[r], -order.index(r)))
    table = {}
    chosen = best
    for r in order:
        diff = crit[best] - crit[r]
        m, se = mean_se(diff)
        tied = r == best or m == 0.0 or (se == se and m < tie_se * se)
        table[r] = {"mean": means[r], "mc_se": mean_se(crit[r])[1], "paired_difference_to_best": m,
                    "paired_difference_mc_se": se, "ties_best": bool(tied)}
    for r in order:                      # the simplest rule that ties the best
        if table[r]["ties_best"]:
            chosen = r
            break
    return {"chosen": chosen, "best_by_mean": best, "table": table}


def choose_k(per_k: np.ndarray, ks: list[int], tie_se: float) -> dict:
    """The k with the largest mean; a paired difference below tie_se MC SE goes to the larger k."""
    means = per_k.mean(axis=0)
    best = int(np.argmax(means))
    table = {}
    for i, k in enumerate(ks):
        m, se = mean_se(per_k[:, best] - per_k[:, i])
        tied = i == best or m == 0.0 or (se == se and m < tie_se * se)
        table[str(k)] = {"mean": float(means[i]), "paired_difference_to_best": m, "paired_difference_mc_se": se,
                         "ties_best": bool(tied)}
    chosen = max(k for k in ks if table[str(k)]["ties_best"])
    return {"chosen": chosen, "best_by_mean": ks[best], "table": table}


def simulate_menu(spec_settings: Mapping[str, Any], sim: Mapping[str, Any], menu_id: str, conventions: list[str],
                  workers: int = 1, placement_convention: str | None = None, timing: dict | None = None) -> dict:
    """The three passes of one menu under each convention, {convention: result}. Under the freeze scope
    menu_m_b (the default; REQ-17 "frozen choice per (menu, M, B) cell") one rule and one k per cell are chosen on
    the equal-weight average of the conventions' per-replicate criteria and used under every convention; under
    menu_m_b_convention each convention chooses its own. The placement statistics are computed under
    placement_convention only (they read no cost)."""
    scope = sim["criterion"]["freeze_scope"]
    if scope not in FREEZE_SCOPES:
        raise s1.Refusal(f"criterion.freeze_scope is not one of {', '.join(FREEZE_SCOPES)}")
    groups = [list(conventions)] if scope == "menu_m_b" else [[c] for c in conventions]
    menu = spec.menu_from(spec_settings, menu_id)
    out: dict = {}
    for group in groups:
        out.update(_simulate_group(spec_settings, sim, menu, group, workers, placement_convention, timing))
    return {c: out[c] for c in conventions}


def simulate(spec_settings: Mapping[str, Any], sim: Mapping[str, Any], menu_id: str, convention: str,
             workers: int = 1, placement: bool = True) -> dict:
    """The three passes of one menu under one convention (its own frozen choices); returns sums, choices and
    placement values."""
    menu = spec.menu_from(spec_settings, menu_id)
    return _simulate_group(spec_settings, sim, menu, [convention], workers, convention if placement else None,
                           None)[convention]


def _timed(timing: dict | None, name: str, fn, *args, **kwargs):
    start = time.monotonic()
    out = fn(*args, **kwargs)
    if timing is not None:
        timing[name] = round(time.monotonic() - start, 1)
    return out


def _simulate_group(spec_settings: Mapping[str, Any], sim: Mapping[str, Any], menu: spec.Menu,
                    conventions: list[str], workers: int, placement_convention: str | None,
                    timing: dict | None) -> dict:
    """The passes of one menu under the conventions of one freeze group; the rule and k are chosen on the
    equal-weight average over the group's conventions (one convention: its own criterion)."""
    menu_id = menu.id
    reps = sim["replicates"]
    tie_se = float(sim["criterion"]["tie_mc_se"])
    budgets = [float(b) for b in sim["grids"]["budgets"]]
    rules = menu_rules(menu)
    rhos = rho_grid(sim)
    part_a = {c: _timed(timing, f"{menu_id}|{c}|A", run_pass, spec_settings, sim, menu_id, c, "A",
                        int(reps["rule_choice"]), workers=workers) for c in conventions}
    crit_a = {c: reduce_crit(part_a[c]) for c in conventions}
    rho_avg = sim["model"]["rho_average_for_rule"]
    choice = {}
    for b in budgets:
        per_conv = {c: {r: (np.mean([crit_a[c][(rho, b, r)] for rho in rhos], axis=0) if rho_avg
                            else crit_a[c][(0.0, b, r)]) for r in rules} for c in conventions}
        per_rule = {r: np.mean([per_conv[c][r] for c in conventions], axis=0) for r in rules}
        choice[str(b)] = choose_rule(per_rule, rules, tie_se)
        for r in rules:
            choice[str(b)]["table"][r]["mean_by_convention"] = {c: float(per_conv[c][r].mean()) for c in conventions}
        choice[str(b)]["conventions"] = list(conventions)
    frozen = {"rule": {str(b): choice[str(b)]["chosen"] for b in budgets}}
    part_b = {c: _timed(timing, f"{menu_id}|{c}|B", run_pass, spec_settings, sim, menu_id, c, "B",
                        int(reps["diagnostic"]), frozen, workers, c == placement_convention) for c in conventions}
    crit_b = {c: reduce_crit(part_b[c]) for c in conventions}
    ks = k_grid(menu.M)
    k_choice = {}
    for b in budgets:
        for c_d in sim["grids"]["c_d_grid"]:
            per_conv = {c: crit_b[c][(b, float(c_d))] for c in conventions}
            key = f"{b:g}|{float(c_d):g}"
            k_choice[key] = choose_k(np.mean([per_conv[c] for c in conventions], axis=0), ks, tie_se)
            for i, k in enumerate(ks):
                k_choice[key]["table"][str(k)]["mean_by_convention"] = {c: float(per_conv[c][:, i].mean())
                                                                        for c in conventions}
            k_choice[key]["conventions"] = list(conventions)
    frozen["k"] = {key: value["chosen"] for key, value in k_choice.items()}
    part_c = {c: _timed(timing, f"{menu_id}|{c}|C", run_pass, spec_settings, sim, menu_id, c, "C",
                        int(reps["sensitivity"]), frozen, workers) for c in conventions}
    return {c: _assemble(spec_settings, sim, menu, c, part_a[c], part_b[c], part_c[c], choice, k_choice, frozen,
                         list(conventions)) for c in conventions}


def _assemble(spec_settings: Mapping[str, Any], sim: Mapping[str, Any], menu: spec.Menu, convention: str,
              part_a: list[dict], part_b: list[dict], part_c: list[dict], choice: dict, k_choice: dict,
              frozen: dict, frozen_over: list[str]) -> dict:
    menu_id = menu.id
    rules, ks, rhos = menu_rules(menu), k_grid(menu.M), rho_grid(sim)
    V = sum(p["V"] for p in part_a)
    V2 = sum(p["V2"] for p in part_a)
    placement: dict = {}
    for p in part_b:
        for q, values in p["placement"].items():
            slot = placement.setdefault(q, {})
            for stat, v in values.items():
                if isinstance(v, dict):
                    inner = slot.setdefault(stat, {})
                    for k, arr in v.items():
                        inner.setdefault(k, []).append(arr)
                else:
                    slot.setdefault(stat, []).append(v)
    for q, slot in placement.items():
        for stat, v in slot.items():
            slot[stat] = ({k: np.concatenate(a) for k, a in v.items()} if isinstance(v, dict) else np.concatenate(v))
    geom = geometry(spec_settings, menu)
    return {"menu": menu_id, "convention": convention, "M": menu.M, "rules": rules, "ks": ks, "rho_grid": rhos,
            "points": prior_points(sim, geom), "n_a": sum(p["n"] for p in part_a),
            "n_b": sum(p["n"] for p in part_b), "n_c": sum(p["n"] for p in part_c),
            "V": V, "V2": V2, "sums_a": reduce_sums(part_a), "rule_choice": choice, "k_choice": k_choice,
            "frozen": frozen, "frozen_over": frozen_over, "freeze_scope": sim["criterion"]["freeze_scope"],
            "sums_b": reduce_sums(part_b), "sums_c": reduce_sums(part_c), "placement": placement,
            "qualities_main": [quality_name(q) for q in quality_points(sim, geom, "main")],
            "qualities_report": [quality_name(q) for q in quality_points(sim, geom, "report")]}
