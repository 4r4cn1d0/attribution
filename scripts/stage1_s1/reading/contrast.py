"""Contrast estimates: the estimator, the seed part, the crossed item part, Satterthwaite df, tests and intervals
(REV3 sections 3.1-3.2, 3.6; AMD sections A.2-A.5, A.8; LN-20).

A table is {(arm, seed): items}, items a numpy vector over the endpoint's P items (prompt shares for U, flags for O,
row losses for L). A cell value is scale x the item mean (scale 100 for U and O in pp, 1 for L in nats).

- Estimator (AMD A.2): Lambda-hat = (1/J) sum over the common seeds of [v(c, j) - v(m, j)] (the paired mean, which
  equals the REML/GLS estimate; review-statistics 1.1). Positive = the repair restores more (U) or sits higher (O, L).
- Seed part (REV3 3.2): V_seed = (sigma^2_c + sigma^2_m)/J from the REML fit, df by Satterthwaite from the
  information (AMD A.4). The LN-20 forms: a theta0 contrast takes the arm's own between-seed variance / J with
  J - 1 df; a cross-cluster pair takes its own paired variance with J - 1 df. S-A8 keeps AMD A.8's in-model forms.
- Item part (REV3 3.2, prompts crossed with seeds): from the J x P table D(j, p) = y(c, j, p) - y(m, j, p),
  MS_P on P - 1 df and MS_E on (P - 1)(J - 1) df; V_item = max(0, MS_P - MS_E)/(P J) x scale^2;
  q = (MS_P scale^2/(P J))^2/(P - 1) + (MS_E scale^2/(P J))^2/((P - 1)(J - 1)) when MS_P > MS_E, else 0.
- df = V^2 / (V_seed^2/df_seed + q) (AMD A.4). t = Lambda-hat / SE against Student t with df (AMD A.5).
- Intervals: Lambda-hat +- t((1 + level)/2, df) SE; the 90% interval serves grade 1 and the feasibility states;
  the familywise interval has alpha/(number of contrasts) per side (REV3 4.5).
- The sensitivity forms (REV3 3.4): Welch (S-aW), the pooled unpaired variance with df n - A (S-a), the seed-blocked
  pooled residual with one shift (S-b2x), the paired t with J - 1 df (S-p).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

from scripts.stage1_s1.reading import tdist
from scripts.stage1_s1.reading.reml import RemlFit, own_variance_df, seed_variance
from scripts.stage1_s1.reading.settings import Refusal


@dataclass(frozen=True)
class Estimate:
    name: str
    form: str
    est: float
    se: float
    df: float
    seed_var: float
    seed_df: float
    item_var: float
    item_q: float
    pairs: int
    items: int
    with_item: bool

    @property
    def t(self) -> float:
        return self.est / self.se if self.se > 0 else float("inf") * np.sign(self.est)

    def p_two_sided(self) -> float:
        return tdist.t_two_sided(self.t, self.df) if self.se > 0 else (1.0 if self.est == 0 else 0.0)

    def p_upper(self, margin: float = 0.0) -> float:
        """P(T > (est - margin)/SE): the one-sided p-value against 'the true value is at most margin'."""
        if self.se <= 0:
            return 0.0 if self.est > margin else 1.0
        return tdist.t_sf((self.est - margin) / self.se, self.df)

    def p_lower(self, margin: float = 0.0) -> float:
        """P(T < (est - margin)/SE): against 'the true value is at least margin'."""
        if self.se <= 0:
            return 0.0 if self.est < margin else 1.0
        return 1.0 - tdist.t_sf((self.est - margin) / self.se, self.df)

    def interval(self, level: float) -> tuple[float, float]:
        if not (0.0 < level < 1.0):
            raise Refusal("an interval level is strictly between 0 and 1")
        half = tdist.t_quantile(0.5 + level / 2.0, self.df) * self.se
        return self.est - half, self.est + half

    def mde(self, alpha_two_sided: float, power: float = 0.8) -> float:
        """The planning MDE at this SE and df: (t(1 - alpha/2) + t(power)) SE."""
        return (tdist.t_quantile(1.0 - alpha_two_sided / 2.0, self.df) + tdist.t_quantile(power, self.df)) * self.se

    def as_dict(self) -> dict:
        out = asdict(self)
        out["t"] = self.t
        out["p_two_sided"] = self.p_two_sided()
        return out


def cell_value(table: dict, arm: str, seed: int, scale: float) -> float:
    return float(scale * table[(arm, seed)].mean())


def arm_values(table: dict, arm: str, seeds, scale: float) -> np.ndarray:
    return np.array([cell_value(table, arm, j, scale) for j in seeds])


def paired_rows(table: dict, c: str, m: str, seeds) -> np.ndarray:
    """The J x P table D(j, p) = y(c, j, p) - y(m, j, p) on the given seeds."""
    if len(seeds) < 2:
        raise Refusal(f"a paired contrast needs at least two common seeds ({c} against {m} has {len(seeds)})")
    return np.stack([table[(c, j)] - table[(m, j)] for j in seeds])


def two_way_ms(d: np.ndarray) -> tuple[float, float]:
    """MS_P (P - 1 df) and MS_E ((P - 1)(J - 1) df) of a J x P table with no replication."""
    j, p = d.shape
    if j < 2 or p < 2:
        raise Refusal("the item part needs at least two seeds and two items")
    grand = d.mean()
    row = d.mean(axis=1, keepdims=True)
    col = d.mean(axis=0, keepdims=True)
    ms_p = float(j * ((col - grand) ** 2).sum() / (p - 1))
    resid = d - row - col + grand
    ms_e = float((resid ** 2).sum() / ((p - 1) * (j - 1)))
    return ms_p, ms_e


def item_part(d: np.ndarray, scale: float) -> tuple[float, float]:
    """V_item and the Satterthwaite term q (AMD A.3-A.4) from the J x P difference table."""
    j, p = d.shape
    ms_p, ms_e = two_way_ms(d)
    k = scale * scale / (p * j)
    v_item = max(0.0, ms_p - ms_e) * k
    q = 0.0
    if ms_p > ms_e:
        q = (ms_p * k) ** 2 / (p - 1) + (ms_e * k) ** 2 / ((p - 1) * (j - 1))
    return v_item, q


def satterthwaite_df(v_seed: float, df_seed: float, v_item: float, q: float) -> float:
    v = v_seed + v_item
    if v <= 0:
        return float("inf")
    denominator = (v_seed * v_seed / df_seed if np.isfinite(df_seed) else 0.0) + q
    return v * v / denominator if denominator > 0 else float("inf")


def _assemble(name, form, est, v_seed, df_seed, d, scale, with_item, pairs) -> Estimate:
    v_item, q = item_part(d, scale) if with_item else (0.0, 0.0)
    v = v_seed + v_item
    df = float(satterthwaite_df(v_seed, df_seed, v_item, q))
    if not np.isfinite(df):
        # no variance information (identical cells, or an information matrix of zero): a named refusal, not a
        # traceback from the t distribution (verify-code N1)
        raise Refusal(f"the contrast {name} ({form}) has no finite degrees of freedom: its variance information is zero")
    return Estimate(name=name, form=form, est=float(est), se=float(np.sqrt(v)), df=df, seed_var=float(v_seed),
                    seed_df=float(df_seed), item_var=float(v_item), item_q=float(q), pairs=int(pairs),
                    items=int(d.shape[1]), with_item=bool(with_item))


def seed_only(e: Estimate) -> Estimate:
    """The same estimate with its item part dropped: SE = sqrt(V_seed), df = the seed df. The O error model is
    'prompts random' (LW-03); the seed-only value is printed beside every O number as 'on these prompts' (REV3 3.6,
    6.6; verify-code F7). It is S-0's form for that estimate."""
    if not e.with_item:
        return e
    return Estimate(name=e.name, form=e.form + "; seed part only", est=e.est, se=float(np.sqrt(e.seed_var)),
                    df=float(e.seed_df), seed_var=e.seed_var, seed_df=e.seed_df, item_var=0.0, item_q=0.0,
                    pairs=e.pairs, items=e.items, with_item=False)


def paired_mean(table, c, m, seeds, scale) -> float:
    return float((arm_values(table, c, seeds, scale) - arm_values(table, m, seeds, scale)).mean())


def contrast_fit(table, fit: RemlFit, c, m, seeds, scale, with_item=True, name="", form="HB-C") -> Estimate:
    """The primary form: paired mean, REML seed part, crossed item part (REV3 3.2)."""
    d = paired_rows(table, c, m, seeds)
    v_seed, df_seed = seed_variance(fit, c, m, len(seeds))
    return _assemble(name, form, paired_mean(table, c, m, seeds, scale), v_seed, df_seed, d, scale, with_item, len(seeds))


def contrast_paired(table, c, m, seeds, scale, with_item=True, name="", form="paired (J - 1 df)") -> Estimate:
    """The pair's own paired variance with J - 1 df: LN-20 item 2 (cross-cluster pairs) and S-p."""
    d = paired_rows(table, c, m, seeds)
    diffs = arm_values(table, c, seeds, scale) - arm_values(table, m, seeds, scale)
    v_seed = float(diffs.var(ddof=1)) / len(seeds)
    return _assemble(name, form, diffs.mean(), v_seed, float(len(seeds) - 1), d, scale, with_item, len(seeds))


def contrast_theta0(table, m, seeds, theta0_items, scale, with_item=True, name="", form="theta0 (LN-20 item 1)") -> Estimate:
    """m against the fixed unit theta0 (no seed): m's own between-seed variance / J with J - 1 df, plus the item
    part of the J x P table y(m, j, p) - y(theta0, p) (REV3 3.6; LN-20 item 1). Positive = m above theta0."""
    if len(seeds) < 2:
        raise Refusal(f"a theta0 contrast needs at least two seeds ({m} has {len(seeds)})")
    values = arm_values(table, m, seeds, scale)
    d = np.stack([table[(m, j)] - theta0_items for j in seeds])
    v_seed = float(values.var(ddof=1)) / len(seeds)
    est = values.mean() - scale * float(np.mean(theta0_items))
    return _assemble(name, form, est, v_seed, float(len(seeds) - 1), d, scale, with_item, len(seeds))


def contrast_theta0_pooled(table, arms_seeds: dict, m, seeds, theta0_items, scale, name="", form="S-a theta0 (LW-33 pooled)") -> Estimate:
    """LW-33's form for the theta0 part under S-a (REV3 3.4; 3.6 item 3): V = s^2_pool,O / J_m + the item part of the
    J_m x P table y(m, j, p) - y(theta0, p), with the pooled df n - A and Satterthwaite. The sensitivity only."""
    if len(seeds) < 2:
        raise Refusal(f"a theta0 contrast needs at least two seeds ({m} has {len(seeds)})")
    s2, df = pooled_variance(table, arms_seeds, scale)
    values = arm_values(table, m, seeds, scale)
    d = np.stack([table[(m, j)] - theta0_items for j in seeds])
    est = values.mean() - scale * float(np.mean(theta0_items))
    return _assemble(name, form, est, s2 / len(seeds), df, d, scale, True, len(seeds))


def contrast_theta0_a8(table, fit: RemlFit, m, seeds, theta0_items, scale, name="", form="S-A8 theta0 (seed shift omitted)") -> Estimate:
    """AMD A.8's theta0 form: the REML residual variance / J_m, df from the information (the sensitivity S-A8)."""
    values = arm_values(table, m, seeds, scale)
    d = np.stack([table[(m, j)] - theta0_items for j in seeds])
    v_seed, df_seed = own_variance_df(fit, m, len(seeds))
    est = values.mean() - scale * float(np.mean(theta0_items))
    return _assemble(name, form, est, v_seed, df_seed, d, scale, True, len(seeds))


def contrast_welch(table, c, m, c_seeds, m_seeds, common, scale, with_item=True, name="", form="S-aW Welch") -> Estimate:
    """Unpaired Welch over all seeds of each arm; the item part from the common-seed table (REV3 3.4)."""
    vc, vm = arm_values(table, c, c_seeds, scale), arm_values(table, m, m_seeds, scale)
    if len(vc) < 2 or len(vm) < 2:
        raise Refusal("Welch needs at least two seeds per arm")
    v_seed = float(vc.var(ddof=1)) / len(vc) + float(vm.var(ddof=1)) / len(vm)
    df_seed = tdist.welch_df(float(vc.var(ddof=1)), len(vc), float(vm.var(ddof=1)), len(vm))
    d = paired_rows(table, c, m, common)
    return _assemble(name, form, vc.mean() - vm.mean(), v_seed, df_seed, d, scale, with_item, len(common))


def pooled_variance(table, arms_seeds: dict, scale) -> tuple[float, float]:
    """S-a's pooled variance over the arms (one-way): sum (n_a - 1) s_a^2 / (n - A), df n - A (PLAN-S:102)."""
    ss, df = 0.0, 0.0
    for arm, seeds in arms_seeds.items():
        v = arm_values(table, arm, seeds, scale)
        ss += float(((v - v.mean()) ** 2).sum())
        df += len(v) - 1
    if df <= 0:
        raise Refusal("the pooled variance has no residual df")
    return ss / df, df


def contrast_pooled(table, arms_seeds: dict, c, m, common, scale, with_item=True, name="", form="S-a pooled unpaired") -> Estimate:
    """S-a: unpaired means over all seeds, variance pooled over the arms, df n - A (REV3 3.4; PLAN-S:102)."""
    s2, df = pooled_variance(table, arms_seeds, scale)
    vc, vm = arm_values(table, c, arms_seeds[c], scale), arm_values(table, m, arms_seeds[m], scale)
    v_seed = s2 * (1.0 / len(vc) + 1.0 / len(vm))
    d = paired_rows(table, c, m, common)
    return _assemble(name, form, vc.mean() - vm.mean(), v_seed, df, d, scale, with_item, len(common))


def blocked_variance(table, arms_seeds: dict, scale) -> tuple[float, float]:
    """S-b2x's pooled residual of the OLS fit v = mu_a + s_j + e (one seed shift for every arm): df n - A - S + 1."""
    cells = [(arm, j) for arm, seeds in arms_seeds.items() for j in seeds]
    arms = list(arms_seeds)
    seeds = sorted({j for _, j in cells})
    x = np.zeros((len(cells), len(arms) + len(seeds) - 1))
    y = np.zeros(len(cells))
    for i, (arm, j) in enumerate(cells):
        x[i, arms.index(arm)] = 1.0
        if seeds.index(j) > 0:
            x[i, len(arms) + seeds.index(j) - 1] = 1.0
        y[i] = cell_value(table, arm, j, scale)
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ beta
    df = len(cells) - np.linalg.matrix_rank(x)
    if df <= 0:
        raise Refusal("the blocked model has no residual df")
    return float(resid @ resid) / df, float(df)


def contrast_blocked(table, c, m, common, s2_pool, df_pool, scale, with_item=True, name="", form="S-b2x blocked pooled") -> Estimate:
    """S-b2x: the paired mean with V_seed = 2 s^2_pool / J and the pooled residual df, plus the item part."""
    d = paired_rows(table, c, m, common)
    return _assemble(name, form, paired_mean(table, c, m, common, scale), 2.0 * s2_pool / len(common), df_pool, d,
                     scale, with_item, len(common))


def contrast_cross_a8(table, fit: RemlFit, c, m, seeds, scale, name="", form="S-A8 in-model cross-cluster (seed shift omitted)") -> Estimate:
    """AMD A.8's in-model form for a pair across the clusters: (sigma^2_c + sigma^2_m)/J with df from the two
    fits' information, read as if both arms shared one fit (the sensitivity S-A8). ``fit`` is a merged fit."""
    return contrast_fit(table, fit, c, m, seeds, scale, True, name, form)
