"""Synthetic helpers for the Part E selector tests (no real data: every observation is built here)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np

from scripts.stage1.selector import spec

SETTINGS = Path(spec.__file__).resolve().parents[1] / "settings"


def raw(name: str) -> dict:
    return json.loads((SETTINGS / f"{name}.json").read_bytes())


def tiny() -> tuple[dict, dict, dict]:
    """The pinned settings with small replicate counts and small grids, for fast end-to-end tests."""
    S, M, P = raw("selector_spec"), raw("selector_simulate"), raw("selector_predict")
    S["trials"]["max_seeds"] = 8
    M["replicates"] = {"rule_choice": 40, "diagnostic": 20, "sensitivity": 20,
                       "chunk": {k: 20 for k in M["replicates"]["chunk"]}}
    M["grids"]["budgets"] = [2.0, 4.0, 8.0]
    M["grids"]["c_d_grid"] = [0.0, 0.5, 2.0]
    M["prior"]["category"]["sizes_pp"] = [8.0]
    M["prior"]["planted"]["sizes_pp"] = [10.0]
    P["menus_predicted"] = ["category", "planted_8"]
    return S, M, P


def custom_menu(M: int, *, nested: bool = False, keep_seeds: int = 3, prefix: str = "opt") -> spec.Menu:
    options = tuple(spec.Option(f"{prefix}-{i}", "cell" if nested else "removal", 600, 1.0) for i in range(M))
    return spec.Menu(f"test-{prefix}-{M}", "planted" if nested else "category", spec.Option("keep-t", "keep", 0, 0.0),
                     options, keep_seeds, nested)


def context(menu: spec.Menu, convention: str = "C-full", settings: dict | None = None, **screen) -> spec.Context:
    S = copy.deepcopy(settings or raw("selector_spec"))
    S["screen"].update(screen)
    return spec.context(S, menu.id, convention, menu=menu)


def exact_obs(ctx: spec.Context, u_mean: np.ndarray, *, keep_u: float = 50.0, o: float = 4.0, l: float = 0.0,
              coherent: np.ndarray | None = None, keep_o: np.ndarray | None = None,
              keep_l: np.ndarray | None = None) -> spec.Observations:
    """Noise-free observations: every trial of option a reads u_mean[b, a] (axis incl. group nodes); keep reads
    keep_u at every seed; O and L constant unless given as arrays."""
    u_mean = np.asarray(u_mean, float)
    n, A = u_mean.shape
    M = ctx.menu.M
    J = ctx.max_seeds
    shape = (n, A, J, len(ctx.phi_grid), len(ctx.psi_grid))
    u = np.broadcast_to(u_mean[:, :, None, None, None], shape).copy()
    o_arr = np.broadcast_to(np.asarray(o, float), (n, M, J)).copy() if np.ndim(o) < 3 else np.asarray(o, float)
    l_arr = np.broadcast_to(np.asarray(l, float), (n, M, J)).copy() if np.ndim(l) < 3 else np.asarray(l, float)
    kj = ctx.menu.keep_seeds
    return spec.Observations(
        u=u, o=o_arr, l=l_arr, keep_u=np.full((n, kj), keep_u),
        keep_o=np.full((n, kj), 4.0) if keep_o is None else keep_o,
        keep_l=np.zeros((n, kj)) if keep_l is None else keep_l,
        coherent=np.ones((n, M), bool) if coherent is None else coherent, ref_l=np.zeros((n, 3)))


def noisy_obs(ctx: spec.Context, g_true: np.ndarray, rng: np.random.Generator, sd: float = 2.0,
              keep_u: float = 50.0) -> spec.Observations:
    """Observations with independent normal noise on every trial (test-only draws)."""
    g_true = np.asarray(g_true, float)
    n, A = g_true.shape
    M, J = ctx.menu.M, ctx.max_seeds
    shape = (n, A, J, len(ctx.phi_grid), len(ctx.psi_grid))
    u = keep_u - g_true[:, :, None, None, None] + sd * rng.standard_normal(shape)
    kj = ctx.menu.keep_seeds
    return spec.Observations(
        u=u, o=4.0 + rng.standard_normal((n, M, J)), l=0.001 * rng.standard_normal((n, M, J)),
        keep_u=keep_u + sd * rng.standard_normal((n, kj)), keep_o=4.0 + rng.standard_normal((n, kj)),
        keep_l=0.001 * rng.standard_normal((n, kj)), coherent=np.ones((n, M), bool),
        ref_l=0.001 * rng.standard_normal((n, 3)))
