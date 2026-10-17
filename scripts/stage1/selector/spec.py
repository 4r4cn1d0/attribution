"""The selector spec (REQ-16): one code path for simulation and replay (numpy; Mac, $0).

Objects. An option (id; kind keep, removal, add or cell; dose in rows; full-run cost in FRE). A menu (the
category menu of the 8 Gate B units; the method menu of the stage-1 primary arms; the planted menus of 8, 32
and 128 nested cells; Llama's Gate B-lite category menu). A budget B in units of c0 of a cost convention
(C-full: 1 FRE; C-lean: the lean job). Keep (a0, or a0_plant on planted menus) is in every menu with G = 0;
its seeds were already run, outside B.

Trials. A trial is (option, seed index, phi, psi): a training fraction phi and a prompt fraction psi, priced
by the ledger cost model: (setup + phi x training + psi x evaluation) / c0. Raising a trained model's prompt
fraction from psi_a to psi_b costs (psi_b - psi_a) x evaluation / c0, so a cost depends only on the final
state of each (option, seed). A full run is phi = psi = 1. Under C-lean variant (b) every full run also pays
the over-refusal and task-loss passes that the screen needs, at their full-evaluation cost.

Rules (each is fixed-budget: its schedule is chosen before any data and never spends more than B):
  one_shot   screen as many options as the budget allows with one trial each at the screen fidelity (seed 0),
             in the sealed tie order; give the best ones 2 full-run seeds (as many as the rest of B allows, at
             most the settings' finalists, default 2); spend what is left on more full-run seeds for them,
             round robin in rank order.
  halving    successive halving on a rung ladder: the screen trial, then the psi ladder of the same model
             (seed 0), then one more full-run seed per rung; half of the options (rounded up) go on after
             each rung, until one option holds at least 2 full-run seeds. The first rung holds the largest
             number of options whose whole schedule fits B; what is left buys more full-run seeds for the
             options that hold 2 or more, round robin in rank order.
  bisection  nested menus only: from the root, test both halves of the current group with t screen trials
             each and follow the half with the lower U (a tie follows the left half); the leaf reached gets
             2 full-run seeds; t is the largest that fits B; the rest buys more seeds for that leaf.
A diagnostic policy pays c_d out of B (if B - c_d < 2 it picks keep), keeps its top k options (keep is never
dropped) and runs the same rule on them in the sealed tie order; bisection becomes halving (lead decisions
L15 (8)).

Pick. Among the options with at least 2 full-run seeds that pass the feasibility screen, the largest
empirical-Bayes-shrunk estimate of G = U(keep) - U(option) (normal-normal, method of moments, over every option
with at least one full-run seed; variances from the pooled U residuals); a tie between options goes to the
raw estimate, then to the sealed tie order; the pick is keep unless the best shrunk estimate is above 0, so a
tie with keep goes to keep.

Feasibility screen. An option is dropped if the upper end of the two-sided interval at the settings' quantile
(default 0.95: the two-sided 90% interval) of O(option) - O(theta0) is above tau_O, or that of L(option) -
L(reference) is above tau_L, or if it fails the coherence gate. The O SE adds the prompt part under the
prompts-random error model; the seed part comes from the pooled residuals (lead decisions L16) or from the
option's own seeds plus the crossed item part (the HB form), by a settings switch. The screen bounds O and L
separately: the U-O noise correlation enters the generative model only (a reading, settings screen.uo_reading).
The screen uses the settings' L reference; a replay also reports the L bound against the other one (W1-13 row 4).

All randomness comes from s1common by registry key: the sealed tie order of a menu's options, and the prompt
subsample of a psi-trial replayed from saved labels. The settings file settings/selector_spec.json is pinned by
SHA-256 below. Messages carry ids, counts and hashes only.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
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

SETTINGS_PATH = STAGE1 / "settings" / "selector_spec.json"
SETTINGS_SHA256 = "2846cdfa33d38b0e86395af98e2eec1b4f758f2b5ebfc151bf97ef3e5985d724"
SETTINGS_NAME = "selector_spec"
KEEP = -1
EPS = 1e-9
RULES = ("one_shot", "halving", "bisection")
LABELS_KIND = "stage1 selector saved labels"
LABELS_VERSION = 2               # version 2 adds samples_per_prompt (the options' and keep's U sampling)


# ----- objects -------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Option:
    id: str
    kind: str                    # keep, removal, add or cell
    dose: int                    # rows removed (removal, cell) or added (add); 0 for keep
    cost_fre: float              # full-run cost in FRE; keep: 0 (its seeds ran outside B)


@dataclass(frozen=True)
class Menu:
    id: str
    kind: str                    # category, method or planted
    keep: Option
    options: tuple[Option, ...]  # menu order (for a nested menu: unit, quartile, quarter)
    keep_seeds: int              # keep's seeds already run (outside B)
    nested: bool

    @property
    def M(self) -> int:
        return len(self.options)

    @property
    def ids(self) -> list[str]:
        return [o.id for o in self.options]

    def axis_size(self) -> int:
        """Menu options, then (nested menus) the M - 2 group nodes of the binary tree other than the root."""
        return 2 * self.M - 2 if self.nested else self.M


@dataclass(frozen=True)
class CostModel:
    """Seconds of one full run by stage; the unit c0 = setup + training + evaluation."""
    name: str
    setup: float
    training: float
    evaluation: float
    extra_full: float            # C-lean (b): the screen's O and L passes, paid by every full run
    samples_per_prompt: int      # U's sampled answers per harm prompt in this convention's evaluation

    @property
    def unit(self) -> float:
        return self.setup + self.training + self.evaluation

    def trial(self, phi: float, psi: float) -> float:
        full = self.extra_full if (phi == 1.0 and psi == 1.0) else 0.0
        return (self.setup + phi * self.training + psi * self.evaluation + full) / self.unit

    def topup(self, psi_from: float, psi_to: float) -> float:
        if psi_to <= psi_from:
            return 0.0
        full = self.extra_full if psi_to == 1.0 else 0.0
        return ((psi_to - psi_from) * self.evaluation + full) / self.unit

    @property
    def full(self) -> float:
        return self.trial(1.0, 1.0)


@dataclass(frozen=True)
class Context:
    """Everything the rules, the screen and the pick read besides the observations."""
    menu: Menu
    cost: CostModel
    phi_grid: tuple[float, ...]
    psi_grid: tuple[float, ...]
    screen_phi: int              # index into phi_grid
    screen_psi: int              # index into psi_grid
    max_seeds: int
    tie_rank: np.ndarray         # (M,) position of each menu option in the sealed tie order
    min_seeds: int               # the pick's full-run seeds
    upper_quantile: float
    o_error_model: str           # prompts_random or seed_only
    o_prompt_sd: float           # pp; the prompt part of O's SE under prompts_random
    se_form: str                 # pooled_residuals or hb
    l_item_sd: float             # nats; the crossed task-row part of L's SE under the HB form
    tau_l_reference: str         # a0 or r
    coherence_gate: bool
    o_theta0: float              # pp
    tau_o: tuple[float, ...]     # pp
    tau_l: float                 # nats
    one_shot_finalists: int      # the one-shot screen's largest number of finalists
    shrink_min_options: int
    diag_min_budget: float       # B - c_d below this: the diagnostic policy picks keep
    bisection_becomes: str
    keep_samples_per_prompt: int  # keep's seeds are C-full runs at any convention

    @property
    def a1(self) -> int:
        return len(self.phi_grid) - 1

    @property
    def c1(self) -> int:
        return len(self.psi_grid) - 1

    @property
    def screen_cost(self) -> float:
        return self.cost.trial(self.phi_grid[self.screen_phi], self.psi_grid[self.screen_psi])

    def promote_cost(self, screened_seeds: int) -> float:
        """Cost to give an option 2 full-run seeds when it holds screen trials at seeds 0..screened_seeds-1."""
        out = 0.0
        for seed in (0, 1):
            if seed < screened_seeds and self.phi_grid[self.screen_phi] == 1.0:
                out += self.cost.topup(self.psi_grid[self.screen_psi], 1.0)
            else:
                out += self.cost.full
        return out


@dataclass
class Observations:
    """What the policies may read, with a leading batch axis n (replicates x grid points; a replay is n = 1).
    u: (n, A, J, n_phi, n_psi) U in pp of every trial a policy may ask for (A = menu options, then group
    nodes of a nested menu); o, l: (n, M, J) O in pp and task loss in nats of full runs; keep_* (n, J_keep):
    keep's seeds; ref_l (n, J_ref): the dose-matched L reference arm, if used; coherent (n, M): the coherence
    gate per option. A value that the design does not hold is NaN; a policy that reads one refuses."""
    u: np.ndarray
    o: np.ndarray
    l: np.ndarray
    keep_u: np.ndarray
    keep_o: np.ndarray
    keep_l: np.ndarray
    coherent: np.ndarray
    ref_l: np.ndarray | None = None

    @property
    def n(self) -> int:
        return self.u.shape[0]


@dataclass
class State:
    """level[b, a, j]: the largest psi index evaluated at phi = 1 for (option a, seed j), or -1; low[b, a, j]:
    a trial at the screen's phi < 1 ran at seed j."""
    level: np.ndarray
    low: np.ndarray

    @classmethod
    def empty(cls, n: int, axis: int, seeds: int) -> "State":
        return cls(np.full((n, axis, seeds), -1, dtype=np.int16), np.zeros((n, axis, seeds), dtype=bool))


@dataclass
class Selection:
    pick: np.ndarray             # (n, n_tau) option index in menu order, or KEEP
    spent: np.ndarray            # (n,) in units of c0, c_d included
    full_seeds: np.ndarray       # (n, M) full-run seeds per menu option
    rule: str                    # the rule that ran (a diagnostic's bisection runs as halving)
    view: Any = None             # the view the rule ran on (None if no rule ran); a replay reads it for its report
    state: Any = None            # the final trial state on that view


# ----- settings and contexts -----------------------------------------------------------------------------


def load(path: str | Path = SETTINGS_PATH) -> tuple[dict, str]:
    """The pinned spec settings."""
    settings, digest = s1.load_settings(path, SETTINGS_SHA256, SETTINGS_NAME)
    check(settings)
    return settings, digest


def check(settings: Mapping[str, Any]) -> None:
    """Structural checks of a spec settings document (also run on test documents)."""
    if settings["ties"]["key"] != "selector.ties" or settings["psi_subsample"]["key"] != "selector.psi":
        raise s1.Refusal("the spec settings name other registry keys for the tie order or the psi subsample")
    trials = settings["trials"]
    for name in ("phi_grid", "psi_grid"):
        grid = trials[name]
        if not grid or grid != sorted(grid) or len(set(grid)) != len(grid) or grid[-1] != 1.0 or grid[0] <= 0:
            raise s1.Refusal(f"trials.{name} must rise strictly to 1.0")
    if trials["screen_phi"] not in trials["phi_grid"] or trials["screen_psi"] not in trials["psi_grid"]:
        raise s1.Refusal("the screen fidelity is not on the trial grids")
    if settings["pick"]["min_full_run_seeds"] < 2:
        raise s1.Refusal("the pick needs at least 2 full-run seeds (REQ-16)")
    screen = settings["screen"]
    if screen["o_error_model"] not in ("prompts_random", "seed_only") or screen["se_form"] not in (
            "pooled_residuals", "hb") or screen["tau_l_reference"] not in ("a0", "r"):
        raise s1.Refusal("a screen switch holds a value outside its stated options")
    if not 0.5 < screen["upper_quantile"] < 1.0:
        raise s1.Refusal("the screen's upper quantile is outside (0.5, 1)")
    if settings["diagnostic"]["bisection_becomes"] != "halving":
        raise s1.Refusal("a diagnostic's bisection becomes halving (lead decisions L15 (8))")
    if settings["rules"]["simplicity_order"] != list(RULES):
        raise s1.Refusal("the simplicity order is not one_shot, halving, bisection")
    if settings["rules"]["one_shot"]["finalists"] < 1:
        raise s1.Refusal("the one-shot screen needs at least 1 finalist")
    labels = settings["saved_labels"]
    if labels["kind"] != LABELS_KIND or labels["version"] != LABELS_VERSION:
        raise s1.Refusal(f"the spec settings describe saved labels other than version {LABELS_VERSION}")


def planted_options(geometry: Mapping[str, Any], level: str) -> list[Option]:
    """The cells of a planted menu in nesting order: units (M = 8), quartiles (32), quarters (128)."""
    units, quartiles, quarters = geometry["units"], geometry["quartiles"], geometry["quarter_rows"]
    quartile_rows = sum(quarters)
    out = []
    for u in range(units):
        if level == "unit":
            out.append(Option(f"u{u}", "cell", quartiles * quartile_rows, 1.0))
            continue
        for q in range(quartiles):
            if level == "quartile":
                out.append(Option(f"u{u}-q{q}", "cell", quartile_rows, 1.0))
                continue
            for t, rows in enumerate(quarters):
                out.append(Option(f"u{u}-q{q}-t{t}", "cell", rows, 1.0))
    return out


def menu_from(settings: Mapping[str, Any], menu_id: str) -> Menu:
    cfg = settings["menus"][menu_id]
    keep = Option(cfg["keep"]["id"], "keep", 0, 0.0)
    if "planted_level" in cfg:
        options = planted_options(settings["planted_geometry"], cfg["planted_level"])
    else:
        options = [Option(o["id"], o["kind"], int(o["dose"]), float(o["cost_fre"])) for o in cfg["options"]]
    ids = [o.id for o in options] + [keep.id]
    if len(set(ids)) != len(ids) or any(o.kind not in ("removal", "add", "cell") for o in options):
        raise s1.Refusal(f"menu {menu_id}: option ids repeat or an option kind is not removal, add or cell")
    if any(o.cost_fre != 1.0 for o in options):
        raise s1.Refusal(f"menu {menu_id}: an option's full-run cost is not 1 FRE; the convention's cost model prices "
                         "every trial, and a per-option cost is not built")
    menu = Menu(menu_id, cfg["kind"], keep, tuple(options), int(cfg["keep_seeds"]), bool(cfg["nested"]))
    if menu.keep_seeds < 2:
        raise s1.Refusal(f"menu {menu_id}: keep needs at least 2 seeds for the pooled residuals")
    if menu.nested and (menu.M < 2 or menu.M & (menu.M - 1)):
        raise s1.Refusal(f"menu {menu_id}: a nested menu needs a power-of-two number of cells")
    return menu


def tie_rank(menu: Menu) -> np.ndarray:
    """Each option's position in the sealed tie order (registry key selector.ties) over the ids other than keep."""
    order = s1.sealed_order(menu.ids, "selector.ties")
    position = {oid: p for p, oid in enumerate(order)}
    return np.array([position[oid] for oid in menu.ids], dtype=np.int64)


def cost_model(settings: Mapping[str, Any], convention: str) -> CostModel:
    conv = settings["cost_conventions"][convention]
    if "variants" in conv:
        conv = conv["variants"][conv["contents"]]
    return CostModel(convention, float(conv["setup_s"]), float(conv["training_s"]), float(conv["evaluation_s"]),
                     float(conv["extra_full_s"]), int(conv["samples_per_prompt"]))


def context(settings: Mapping[str, Any], menu_id: str, convention: str, *, menu: Menu | None = None) -> Context:
    menu = menu or menu_from(settings, menu_id)
    trials, screen, limits = settings["trials"], settings["screen"], settings["limits"]
    return Context(
        menu=menu, cost=cost_model(settings, convention),
        phi_grid=tuple(float(x) for x in trials["phi_grid"]), psi_grid=tuple(float(x) for x in trials["psi_grid"]),
        screen_phi=trials["phi_grid"].index(trials["screen_phi"]),
        screen_psi=trials["psi_grid"].index(trials["screen_psi"]),
        max_seeds=int(trials["max_seeds"]), tie_rank=tie_rank(menu),
        min_seeds=int(settings["pick"]["min_full_run_seeds"]),
        upper_quantile=float(screen["upper_quantile"]), o_error_model=screen["o_error_model"],
        o_prompt_sd=float(screen["o_prompt_sd_pp"]), se_form=screen["se_form"],
        l_item_sd=float(screen["l_item_sd_nats"]), tau_l_reference=screen["tau_l_reference"],
        coherence_gate=bool(screen["coherence_gate"]),
        o_theta0=float(limits["o_theta0_pp"]), tau_o=tuple(float(x) for x in limits["tau_o_grid_pp"]),
        tau_l=float(limits["tau_l_nats"]),
        one_shot_finalists=int(settings["rules"]["one_shot"]["finalists"]),
        shrink_min_options=int(settings["shrinkage"]["min_options"]),
        diag_min_budget=float(settings["diagnostic"]["min_remaining_budget"]),
        bisection_becomes=settings["diagnostic"]["bisection_becomes"],
        keep_samples_per_prompt=int(settings["cost_conventions"]["C-full"]["samples_per_prompt"]))


# ----- the ledger ----------------------------------------------------------------------------------------


def ledger_cost(ctx: Context, state: State) -> np.ndarray:
    """What a final state cost, from the trials it holds (independent of the rules' own planning)."""
    c = ctx.cost
    psi = np.asarray(ctx.psi_grid)
    level = state.level
    ran = level >= 0
    seconds = np.where(ran, c.setup + c.training + psi[np.clip(level, 0, None)] * c.evaluation, 0.0)
    seconds = seconds + np.where(level == ctx.c1, c.extra_full, 0.0)
    low = ctx.cost.trial(ctx.phi_grid[ctx.screen_phi], ctx.psi_grid[ctx.screen_psi]) if ctx.screen_phi != ctx.a1 else 0.0
    return seconds.sum(axis=(1, 2)) / c.unit + state.low.sum(axis=(1, 2)) * low


# ----- reading observations ------------------------------------------------------------------------------


def _checked(values: np.ndarray) -> np.ndarray:
    if np.isnan(values).any():
        raise s1.Refusal("the policy asks for a trial that the observations do not hold (not replayable)")
    return values


def _gather(arr: np.ndarray, rows: np.ndarray, opts: np.ndarray) -> np.ndarray:
    """arr[b, opts[b, i], ...] for every row b."""
    return arr[rows[:, None], opts]


@dataclass
class _View:
    """The options a rule runs on, in one axis: a compact view holds the available options in the sealed tie
    order (tie positions 0..m-1); the bisection view holds the whole menu axis in menu order."""
    u: np.ndarray
    o: np.ndarray
    l: np.ndarray
    coherent: np.ndarray
    tie: np.ndarray              # (m,) tie position of each menu option in this view
    m: int                       # menu options in the view (the first m entries of the axis)
    keep_u: np.ndarray
    keep_o: np.ndarray
    keep_l: np.ndarray
    ref_l: np.ndarray | None
    index: np.ndarray | None     # (n, m) original option index of each view position (compact views)

    @property
    def n(self) -> int:
        return self.u.shape[0]


def _compact(obs: Observations, ctx: Context, avail: np.ndarray) -> _View:
    n, M = avail.shape
    counts = avail.sum(axis=1)
    if counts.size and (counts != counts[0]).any():
        raise s1.Refusal("the available options differ in number between rows")
    m = int(counts[0]) if counts.size else 0
    key = np.where(avail, ctx.tie_rank[None, :], M + ctx.tie_rank[None, :])
    index = np.argsort(key, axis=1, kind="stable")[:, :m]
    rows = np.arange(n)
    return _View(u=_gather(obs.u, rows, index), o=_gather(obs.o, rows, index), l=_gather(obs.l, rows, index),
                 coherent=_gather(obs.coherent, rows, index), tie=np.arange(m), m=m,
                 keep_u=obs.keep_u, keep_o=obs.keep_o, keep_l=obs.keep_l, ref_l=obs.ref_l, index=index)


def _full_view(obs: Observations, ctx: Context) -> _View:
    return _View(u=obs.u, o=obs.o, l=obs.l, coherent=obs.coherent, tie=ctx.tie_rank, m=ctx.menu.M,
                 keep_u=obs.keep_u, keep_o=obs.keep_o, keep_l=obs.keep_l, ref_l=obs.ref_l, index=None)


def _rank(est: np.ndarray, active: np.ndarray, tie: np.ndarray) -> np.ndarray:
    """Positions sorted by (estimate ascending: lower U is better, tie position); inactive entries last."""
    key = np.where(active, est, np.inf)
    return np.lexsort((np.broadcast_to(tie, key.shape), key), axis=-1)


def _keep_best(est: np.ndarray, active: np.ndarray, tie: np.ndarray, m: int) -> np.ndarray:
    order = _rank(est, active, tie)
    out = np.zeros_like(active)
    np.put_along_axis(out, order[:, :m], True, axis=1)
    return out & active


def _full_mean(view: _View, state: State, axis_slice: slice | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Mean full-run U and the number of full-run seeds per option of the view's axis."""
    level = state.level if axis_slice is None else state.level[:, axis_slice]
    u = view.u[:, :level.shape[1], :, -1, -1]
    full = level == (view.u.shape[-1] - 1)
    _checked(u[full])
    n_full = full.sum(axis=2)
    total = np.where(full, u, 0.0).sum(axis=2)
    return total / np.maximum(n_full, 1), n_full


# ----- the rules -----------------------------------------------------------------------------------------


def _screen_trial(ctx: Context, state: State, rows: np.ndarray, opts: np.ndarray, seed: int) -> None:
    if ctx.screen_phi == ctx.a1:
        current = state.level[rows, opts, seed]
        state.level[rows, opts, seed] = np.maximum(current, ctx.screen_psi)
    else:
        state.low[rows, opts, seed] = True


def _screen_value(ctx: Context, view: _View, rows: np.ndarray, opts: np.ndarray, seed: int) -> np.ndarray:
    return _checked(view.u[rows, opts, seed, ctx.screen_phi, ctx.screen_psi])


def _raise_to_full(ctx: Context, state: State, rows: np.ndarray, opts: np.ndarray, seeds: np.ndarray | int) -> None:
    state.level[rows, opts, seeds] = ctx.c1


def _extra_seeds(ctx: Context, view: _View, state: State, ranked: np.ndarray, budget_left: float) -> None:
    """Spend what is left on full-run seeds, round robin over the ranked options (n, r), at each option's next
    free seed index, never past max_seeds."""
    n, r = ranked.shape
    if r == 0 or n == 0:
        return
    rows = np.arange(n)
    left = np.full(n, int(math.floor(max(budget_left, 0.0) / ctx.cost.full + EPS)), dtype=np.int64)
    counts = (state.level == ctx.c1).sum(axis=2)[rows[:, None], ranked]       # full seeds 0..count-1
    q, idle = 0, 0
    while (left > 0).any() and idle < r:
        room = (counts[:, q] < ctx.max_seeds) & (left > 0)
        if room.any():
            state.level[rows[room], ranked[room, q], counts[room, q]] = ctx.c1
            counts[room, q] += 1
            left[room] -= 1
            idle = 0
        else:
            idle += 1
        q = (q + 1) % r


def _one_shot(ctx: Context, view: _View, budget: float) -> State:
    n, m = view.n, view.m
    state = State.empty(n, view.u.shape[1], ctx.max_seeds)
    c_s, c_p = ctx.screen_cost, ctx.promote_cost(1)
    if m == 0 or budget + EPS < c_s + c_p:
        return state
    n_s = min(m, int(math.floor((budget - c_p) / c_s + EPS)))
    rows = np.arange(n)
    visited = np.broadcast_to(np.arange(n_s), (n, n_s))
    _screen_trial(ctx, state, rows[:, None], visited, 0)
    est = _screen_value(ctx, view, rows[:, None], visited, 0)
    order = visited[rows[:, None], np.lexsort((np.broadcast_to(view.tie[:n_s], est.shape), est), axis=-1)]
    n_f = min(n_s, ctx.one_shot_finalists, int(math.floor((budget - n_s * c_s) / c_p + EPS)))
    finalists = order[:, :n_f]
    _raise_to_full(ctx, state, rows[:, None], finalists, 0)
    _raise_to_full(ctx, state, rows[:, None], finalists, 1)
    _extra_seeds(ctx, view, state, finalists, budget - n_s * c_s - n_f * c_p)
    return state


def _rungs(ctx: Context) -> list[dict]:
    """The halving ladder: the screen trial; the psi ladder of the same model at seed 0 (screen phi = 1) or a
    full run at seed 0 (screen phi < 1); then one more full-run seed per rung."""
    out = [{"kind": "screen", "seed": 0, "cost": ctx.screen_cost, "full_after": int(
        ctx.screen_phi == ctx.a1 and ctx.screen_psi == ctx.c1)}]
    if ctx.screen_phi == ctx.a1:
        previous = ctx.psi_grid[ctx.screen_psi]
        for c in range(ctx.screen_psi + 1, len(ctx.psi_grid)):
            out.append({"kind": "psi", "seed": 0, "psi_index": c, "cost": ctx.cost.topup(previous, ctx.psi_grid[c]),
                        "full_after": int(c == ctx.c1)})
            previous = ctx.psi_grid[c]
    else:
        out.append({"kind": "full", "seed": 0, "cost": ctx.cost.full, "full_after": 1})
    for seed in range(1, ctx.max_seeds):
        out.append({"kind": "full", "seed": seed, "cost": ctx.cost.full, "full_after": seed + 1})
    return out


def halving_schedule(ctx: Context, n1: int) -> tuple[list[int], float]:
    """The options on each rung, from n1 on the first, and the schedule's total cost."""
    sizes, total, n = [], 0.0, n1
    rungs = _rungs(ctx)
    for t, rung in enumerate(rungs):
        sizes.append(n)
        total += n * rung["cost"]
        if (rung["full_after"] >= 2 and n == 1) or t == len(rungs) - 1:
            break
        n = (n + 1) // 2
    return sizes, total


def _halving(ctx: Context, view: _View, budget: float) -> State:
    n, m = view.n, view.m
    state = State.empty(n, view.u.shape[1], ctx.max_seeds)
    chosen = None
    for n1 in range(m, 0, -1):
        sizes, total = halving_schedule(ctx, n1)
        if total <= budget + EPS:
            chosen = (n1, sizes, total)
            break
    if chosen is None:
        return state
    n1, sizes, total = chosen
    rows = np.arange(n)
    active = np.zeros((n, view.u.shape[1]), dtype=bool)
    active[:, :n1] = True
    rungs = _rungs(ctx)
    tie = np.concatenate([view.tie, np.arange(view.m, view.u.shape[1])])
    for t, size in enumerate(sizes):
        rung = rungs[t]
        r_idx, o_idx = np.nonzero(active)
        if rung["kind"] == "screen":
            _screen_trial(ctx, state, r_idx, o_idx, 0)
            est = np.full(active.shape, np.inf)
            est[r_idx, o_idx] = _screen_value(ctx, view, r_idx, o_idx, 0)
        elif rung["kind"] == "psi":
            state.level[r_idx, o_idx, 0] = np.maximum(state.level[r_idx, o_idx, 0], rung["psi_index"])
            est = np.full(active.shape, np.inf)
            est[r_idx, o_idx] = _checked(view.u[r_idx, o_idx, 0, ctx.a1, rung["psi_index"]])
        else:
            _raise_to_full(ctx, state, r_idx, o_idx, rung["seed"])
            est = _full_mean(view, state)[0]
        if t + 1 < len(sizes):
            active = _keep_best(est, active, tie, sizes[t + 1])
    mean_u, n_full = _full_mean(view, state)
    holders = n_full >= 2
    r = int(holders[0].sum()) if n else 0
    ranked = _rank(mean_u, holders, tie)[:, :r]
    _extra_seeds(ctx, view, state, ranked, budget - total)
    return state


def tree_axis(M: int, node: np.ndarray) -> np.ndarray:
    """Axis index of heap node h (root 1): a leaf h >= M is option h - M; an inner node is M + h - 2."""
    return np.where(node >= M, node - M, M + node - 2)


def bisection_plan(ctx: Context, budget: float) -> tuple[int, float]:
    """The largest number t of screen trials per half per level that fits B with the leaf's 2 full-run seeds."""
    levels = int(round(math.log2(ctx.menu.M)))
    best = (0, 0.0)
    for t in range(1, ctx.max_seeds + 1):
        total = 2 * levels * t * ctx.screen_cost + ctx.promote_cost(t)
        if total <= budget + EPS:
            best = (t, total)
    return best


def _bisection(ctx: Context, view: _View, budget: float) -> State:
    menu = ctx.menu
    if not menu.nested:
        raise s1.Refusal(f"bisection needs a nested menu; {menu.id} is not nested")
    n = view.n
    state = State.empty(n, view.u.shape[1], ctx.max_seeds)
    t, total = bisection_plan(ctx, budget)
    if t == 0:
        return state
    rows = np.arange(n)
    node = np.ones(n, dtype=np.int64)
    levels = int(round(math.log2(menu.M)))
    for _ in range(levels):
        left, right = tree_axis(menu.M, 2 * node), tree_axis(menu.M, 2 * node + 1)
        means = []
        for child in (left, right):
            values = []
            for seed in range(t):
                _screen_trial(ctx, state, rows, child, seed)
                values.append(_screen_value(ctx, view, rows, child, seed))
            means.append(np.mean(values, axis=0))
        node = np.where(means[1] < means[0], 2 * node + 1, 2 * node)
    leaf = node - menu.M
    _raise_to_full(ctx, state, rows, leaf, 0)
    _raise_to_full(ctx, state, rows, leaf, 1)
    _extra_seeds(ctx, view, state, leaf[:, None], budget - total)
    return state


RULE_FUNCTIONS = {"one_shot": _one_shot, "halving": _halving, "bisection": _bisection}


# ----- shrinkage, the screen and the pick ----------------------------------------------------------------


def shrink(g: np.ndarray, v: np.ndarray, members: np.ndarray, min_options: int = 2) -> np.ndarray:
    """Normal-normal empirical Bayes by the method of moments, per row over the member options: mu = their mean,
    tau^2 = max(0, their variance (ddof 1) - their mean v); each member moves to mu + tau^2/(tau^2 + v)(g - mu).
    Rows with fewer than min_options members, and non-members, keep g."""
    k = members.sum(axis=1)
    safe_k = np.maximum(k, 1)
    mu = np.where(members, g, 0.0).sum(axis=1) / safe_k
    dev = np.where(members, (g - mu[:, None]) ** 2, 0.0).sum(axis=1)
    var = dev / np.maximum(k - 1, 1)
    mean_v = np.where(members, v, 0.0).sum(axis=1) / safe_k
    tau2 = np.maximum(0.0, var - mean_v)
    den = tau2[:, None] + v
    factor = np.where(den > 0, tau2[:, None] / np.where(den > 0, den, 1.0), 1.0)
    out = mu[:, None] + factor * (g - mu[:, None])
    use = members & (k >= max(min_options, 2))[:, None]
    return np.where(use, out, g)


def _pooled(values: np.ndarray, full: np.ndarray, n_full: np.ndarray, extra: np.ndarray) -> np.ndarray:
    """Pooled within-option variance over the options with 2 or more full-run seeds and the extra arm's seeds."""
    mean = np.where(full, values, 0.0).sum(axis=2) / np.maximum(n_full, 1)
    many = n_full >= 2
    ss = np.where(full & many[..., None], (values - mean[..., None]) ** 2, 0.0).sum(axis=(1, 2))
    df = np.where(many, n_full - 1, 0).sum(axis=1)
    ss = ss + ((extra - extra.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
    df = df + extra.shape[1] - 1
    return ss / df


def _own(values: np.ndarray, full: np.ndarray, n_full: np.ndarray) -> np.ndarray:
    mean = np.where(full, values, 0.0).sum(axis=2) / np.maximum(n_full, 1)
    ss = np.where(full, (values - mean[..., None]) ** 2, 0.0).sum(axis=2)
    return ss / np.maximum(n_full - 1, 1)


def _l_upper(ctx: Context, l: np.ndarray, full: np.ndarray, n_full: np.ndarray, l_mean: np.ndarray,
             safe: np.ndarray, reference: np.ndarray, z: float) -> np.ndarray:
    """(n, m) upper end of L(option) - L(reference arm) at the screen's quantile."""
    if ctx.se_form == "pooled_residuals":
        l_var = _pooled(l, full, n_full, reference)[:, None] * (1.0 / safe + 1.0 / reference.shape[1])
    else:
        l_var = (_own(l, full, n_full) / safe + reference.var(axis=1, ddof=1)[:, None] / reference.shape[1]
                 + ctx.l_item_sd ** 2)
    return l_mean - reference.mean(axis=1)[:, None] + z * np.sqrt(l_var)


def screen_bounds(ctx: Context, view: _View, full: np.ndarray, n_full: np.ndarray, *,
                  both_references: bool = False) -> dict:
    """The screen's upper bounds: "o" (n, m) of O(option) - O(theta0) and "l" (n, m) of L(option) - L(the
    reference in force); with both_references also "l_by_reference" {"a0": (n, m), "r": (n, m) or None when the
    observations hold no R arm} (W1-13 row 4: compute both, the screen uses the settings' reference)."""
    z = NormalDist().inv_cdf(ctx.upper_quantile)
    m = full.shape[1]
    o, l = view.o[:, :m], view.l[:, :m]
    _checked(o[full])
    _checked(l[full])
    safe = np.maximum(n_full, 1)
    o_mean = np.where(full, o, 0.0).sum(axis=2) / safe
    l_mean = np.where(full, l, 0.0).sum(axis=2) / safe
    arms = {"a0": view.keep_l, "r": view.ref_l}
    reference = arms[ctx.tau_l_reference]
    if reference is None:
        raise s1.Refusal("the L screen's reference arm R has no observations")
    if ctx.se_form == "pooled_residuals":
        o_seed = _pooled(o, full, n_full, view.keep_o)[:, None] / safe
    else:
        o_seed = _own(o, full, n_full) / safe
    o_prompt = ctx.o_prompt_sd ** 2 if ctx.o_error_model == "prompts_random" else 0.0
    out = {"o": o_mean - ctx.o_theta0 + z * np.sqrt(o_seed + o_prompt),
           "l": _l_upper(ctx, l, full, n_full, l_mean, safe, reference, z)}
    if both_references:
        out["l_by_reference"] = {name: (None if arm is None else _l_upper(ctx, l, full, n_full, l_mean, safe, arm, z))
                                 for name, arm in arms.items()}
    return out


def feasibility(ctx: Context, view: _View, full: np.ndarray, n_full: np.ndarray) -> np.ndarray:
    """(n, m, n_tau): the option passes the O screen at each tau_O, the L screen and the coherence gate."""
    m = full.shape[1]
    bounds = screen_bounds(ctx, view, full, n_full)
    o_upper, l_upper = bounds["o"], bounds["l"]
    ok = (o_upper[..., None] <= np.asarray(ctx.tau_o)) & (l_upper <= ctx.tau_l)[..., None]
    if ctx.coherence_gate:
        ok = ok & view.coherent[:, :m, None]
    return ok


def estimates(ctx: Context, view: _View, state: State) -> dict:
    """Raw and shrunk G estimates of the view's menu options from their full-run seeds."""
    m = view.m
    level = state.level[:, :m]
    full = level == ctx.c1
    mean_u, n_full = _full_mean(view, state, slice(0, m))
    u = view.u[:, :m, :, ctx.a1, ctx.c1]
    keep_mean = view.keep_u.mean(axis=1)
    g_raw = keep_mean[:, None] - mean_u
    s2 = _pooled(u, full, n_full, view.keep_u)
    v = s2[:, None] * (1.0 / np.maximum(n_full, 1) + 1.0 / view.keep_u.shape[1])
    g_shrunk = shrink(g_raw, v, n_full >= 1, ctx.shrink_min_options)
    return {"full": full, "n_full": n_full, "g_raw": g_raw, "g_shrunk": g_shrunk}


def pick(ctx: Context, view: _View, state: State, keep_kept: np.ndarray) -> np.ndarray:
    """(n, n_tau) view position of the pick, or KEEP."""
    est = estimates(ctx, view, state)
    n_full, g_raw, g_shrunk = est["n_full"], est["g_raw"], est["g_shrunk"]
    candidate = n_full >= ctx.min_seeds
    feasible = feasibility(ctx, view, est["full"], n_full)
    n = view.n
    rows = np.arange(n)
    tie = np.broadcast_to(view.tie, g_raw.shape)
    out = np.full((n, len(ctx.tau_o)), KEEP, dtype=np.int64)
    for t in range(len(ctx.tau_o)):
        ok = candidate & feasible[:, :, t]
        primary = np.where(ok, -g_shrunk, np.inf)
        secondary = np.where(ok, -g_raw, np.inf)
        best = np.lexsort((tie, secondary, primary), axis=-1)[:, 0]
        has = ok[rows, best]
        beats_keep = g_shrunk[rows, best] > 0.0
        out[:, t] = np.where(has & (beats_keep | ~keep_kept), best, KEEP)
    return out


# ----- the diagnostic and the one selection function -----------------------------------------------------


def diagnostic_filter(scores: np.ndarray, k: int, tie: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The k options with the highest diagnostic scores (ties by the sealed tie order) and keep, which top-k
    never drops (lead decisions L15 (2))."""
    n, M = scores.shape
    if not 1 <= k <= M:
        raise s1.Refusal(f"k = {k} is outside 1..{M}")
    order = np.lexsort((np.broadcast_to(tie, scores.shape), -scores), axis=-1)
    avail = np.zeros((n, M), dtype=bool)
    np.put_along_axis(avail, order[:, :k], True, axis=1)
    keep_kept = np.ones(n, dtype=bool)
    return avail, keep_kept


def select(ctx: Context, obs: Observations, *, rule: str, budget: float, scores: np.ndarray | None = None,
           k: int | None = None, c_d: float = 0.0) -> Selection:
    """THE selection function: the simulation and the replay both call it (one code path). Without scores it
    runs the runs-only rule on the whole menu with budget B; with scores it is the diagnostic policy."""
    if rule not in RULES:
        raise s1.Refusal(f"no rule {rule!r}")
    n, M = obs.coherent.shape
    if M != ctx.menu.M or obs.u.shape[1] != ctx.menu.axis_size() or obs.u.shape[2] != ctx.max_seeds:
        raise s1.Refusal("the observations do not have the menu's axis or the settings' seed count")
    keep_all = np.full((n, len(ctx.tau_o)), KEEP, dtype=np.int64)
    if scores is None:
        paid, remaining, ran = 0.0, float(budget), rule
        avail, keep_kept = np.ones((n, M), dtype=bool), np.ones(n, dtype=bool)
    else:
        if k is None:
            raise s1.Refusal("a diagnostic policy needs its k")
        ran = ctx.bisection_becomes if rule == "bisection" else rule
        if c_d > budget + EPS:
            return Selection(keep_all, np.zeros(n), np.zeros((n, M), dtype=np.int64), ran)
        paid, remaining = float(c_d), float(budget) - float(c_d)
        if remaining + EPS < ctx.diag_min_budget:
            return Selection(keep_all, np.full(n, paid), np.zeros((n, M), dtype=np.int64), ran)
        avail, keep_kept = diagnostic_filter(scores, k, ctx.tie_rank)
    if ran == "bisection":
        view = _full_view(obs, ctx)
    else:
        view = _compact(obs, ctx, avail)
    state = RULE_FUNCTIONS[ran](ctx, view, remaining)
    position = pick(ctx, view, state, keep_kept)
    full_seeds = (state.level[:, :view.m] == ctx.c1).sum(axis=2)
    if view.index is not None:
        rows = np.arange(n)[:, None]
        chosen = np.where(position == KEEP, KEEP, view.index[rows, np.maximum(position, 0)])
        seeds = np.zeros((n, M), dtype=np.int64)
        seeds[rows, view.index] = full_seeds
    else:
        chosen, seeds = position, full_seeds
    return Selection(chosen, paid + ledger_cost(ctx, state), seeds, ran, view, state)


# ----- replay from saved labels --------------------------------------------------------------------------


def _mean_of(values: Mapping[str, Any], scale: float, what: str) -> float:
    if not isinstance(values, Mapping) or not values:
        raise s1.Refusal(f"saved labels: {what} is not a non-empty object")
    numbers = list(values.values())
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in numbers):
        raise s1.Refusal(f"saved labels: {what} holds a value that is not a finite number")
    return scale * math.fsum(numbers) / len(numbers)


def _count(x: Any) -> int | None:
    return x if isinstance(x, int) and not isinstance(x, bool) else None


def observations_from_labels(ctx: Context, labels: Mapping[str, Any]) -> Observations:
    """A batch of 1 from saved per-prompt labels: U = 100 x the mean Unsafe share over the harm prompts (a psi
    trial: over a sealed sample of round(psi x n) prompts, registry key selector.psi, parts (option, seed index,
    psi)); O = 100 x the mean refusal flag; L = the mean task loss. A trial that the labels do not hold is NaN.
    Each Unsafe share is over samples_per_prompt sampled answers: the options' count must be the convention's
    (C-full 3, C-lean 1) and keep's must be C-full's, so the replay has the model's sampling variance (a lean
    replay of full evaluations would need a sealed 1-of-3 sample and a new registry key; not built)."""
    if (labels.get("kind") != LABELS_KIND or labels.get("version") != LABELS_VERSION
            or labels.get("menu") != ctx.menu.id):
        raise s1.Refusal(f"not version-{LABELS_VERSION} saved selector labels of menu {ctx.menu.id}")
    samples = _count(labels.get("samples_per_prompt"))
    keep_samples = _count(labels["keep"].get("samples_per_prompt")) if isinstance(labels.get("keep"), Mapping) else None
    if samples != ctx.cost.samples_per_prompt or keep_samples != ctx.keep_samples_per_prompt:
        raise s1.Refusal(f"saved labels: the options' U holds {samples} and keep's {keep_samples} samples per prompt; "
                         f"a {ctx.cost.name} replay needs {ctx.cost.samples_per_prompt} and "
                         f"{ctx.keep_samples_per_prompt}")
    menu, J = ctx.menu, ctx.max_seeds
    u = np.full((1, menu.axis_size(), J, len(ctx.phi_grid), len(ctx.psi_grid)), np.nan)
    o = np.full((1, menu.M, J), np.nan)
    l = np.full((1, menu.M, J), np.nan)
    coherent = np.ones((1, menu.M), dtype=bool)
    unknown = set(labels["options"]) - set(menu.ids)
    if unknown:
        raise s1.Refusal(f"saved labels name {len(unknown)} options outside menu {menu.id}")

    def seed_values(entry: Mapping[str, Any], option_id: str) -> tuple[int, list[float], float, float]:
        j = entry["seed_index"]
        if isinstance(j, bool) or not isinstance(j, int) or not 0 <= j < J:
            raise s1.Refusal(f"saved labels: option {option_id} has a seed index outside 0..{J - 1}")
        prompts = entry["u_prompts"]
        values = []
        for c, psi in enumerate(ctx.psi_grid):
            if c == ctx.c1:
                values.append(_mean_of(prompts, 100.0, f"{option_id} seed {j} u_prompts"))
                continue
            size = int(round(psi * len(prompts)))
            if size < 1:
                raise s1.Refusal(f"saved labels: psi {psi} leaves no prompt")
            chosen = s1.sealed_sample(sorted(prompts), size, "selector.psi", option_id, j, f"{psi:g}")
            values.append(_mean_of({p: prompts[p] for p in chosen}, 100.0, f"{option_id} seed {j} psi"))
        return j, values, _mean_of(entry["o_prompts"], 100.0, f"{option_id} o_prompts"), _mean_of(
            entry["l_rows"], 1.0, f"{option_id} l_rows")

    for i, oid in enumerate(menu.ids):
        entry = labels["options"].get(oid)
        if entry is None:
            continue
        coherent[0, i] = bool(entry["coherent"])
        for seed_entry in entry["seeds"]:
            j, values, ov, lv = seed_values(seed_entry, oid)
            u[0, i, j, ctx.a1, :] = values
            o[0, i, j], l[0, i, j] = ov, lv

    def arm(name: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        seeds = labels[name]["seeds"]
        values = [seed_values(entry, name) for entry in sorted(seeds, key=lambda e: e["seed_index"])]
        return (np.array([[v[1][-1] for v in values]]), np.array([[v[2] for v in values]]),
                np.array([[v[3] for v in values]]))

    keep_u, keep_o, keep_l = arm("keep")
    if keep_u.shape[1] != menu.keep_seeds:
        raise s1.Refusal(f"saved labels hold {keep_u.shape[1]} keep seeds, the menu names {menu.keep_seeds}")
    ref_l = arm("reference_r")[2] if "reference_r" in labels else None
    return Observations(u=u, o=o, l=l, keep_u=keep_u, keep_o=keep_o, keep_l=keep_l, coherent=coherent, ref_l=ref_l)


def replay(settings: Mapping[str, Any], menu_id: str, convention: str, rule: str, budget: float,
           labels: Mapping[str, Any], *, scores: Mapping[str, float] | None = None, k: int | None = None,
           c_d: float = 0.0) -> dict:
    """The replay entry point: a batch of 1 through select(), the function the simulation calls."""
    ctx = context(settings, menu_id, convention)
    obs = observations_from_labels(ctx, labels)
    score_array = None
    if scores is not None:
        checked = s1.check_scores(scores, ctx.menu.ids)
        score_array = np.array([[checked[oid] for oid in ctx.menu.ids]])
    result = select(ctx, obs, rule=rule, budget=budget, scores=score_array, k=k, c_d=c_d)
    picks = {}
    for t, tau in enumerate(ctx.tau_o):
        p = int(result.pick[0, t])
        picks[f"{tau:g}"] = ctx.menu.keep.id if p == KEEP else ctx.menu.ids[p]
    return {"menu": menu_id, "convention": convention, "rule": rule, "ran": result.rule, "budget": budget,
            "c_d": c_d, "k": k, "pick_by_tau_o": picks, "spent": float(result.spent[0]),
            "full_seeds": {oid: int(result.full_seeds[0, i]) for i, oid in enumerate(ctx.menu.ids)},
            "l_upper_nats": l_bounds_report(ctx, result)}


def l_bounds_report(ctx: Context, result: Selection) -> dict:
    """A replay's L screen against both references (W1-13 row 4; DRAFT section 6.6 LQ38's interim rule): the
    upper bound of L(option) - L(a0) and of L(option) - L(R) for each option with the pick's full-run seeds; r is
    None when the saved labels hold no R arm. The screen used the reference in force."""
    out: dict = {"reference_in_force": ctx.tau_l_reference, "tau_l_nats": ctx.tau_l, "a0": None, "r": None}
    if result.state is None:
        return out
    view, state = result.view, result.state
    est = estimates(ctx, view, state)
    bounds = screen_bounds(ctx, view, est["full"], est["n_full"], both_references=True)["l_by_reference"]
    index = view.index[0] if view.index is not None else range(view.m)
    ids = [ctx.menu.ids[int(i)] for i in index]
    candidate = est["n_full"][0] >= ctx.min_seeds
    for name, arr in bounds.items():
        out[name] = None if arr is None else {oid: float(arr[0, p]) for p, oid in enumerate(ids) if candidate[p]}
    return out
