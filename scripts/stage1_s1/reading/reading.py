"""The stage-1 reading, one call: ``read(doc)`` turns the validated input into estimates, tests, labels and headline
words (REV3 sections 3-4, 5.3, 6.4-6.7; AMD A, B, D, E, F). Every rule is named at the function that applies it.

Order of work: validate the input (schema) -> HB-C fits per endpoint (reml; one per cluster; a two-arm cluster by
the sum rule; the stop settings and floor mode from the pinned settings) -> per-contrast estimates (contrast): U_k,
O_k's two parts, L_k's two parts, F_k on O_k's theta0 estimate, each O number with its seed-only value "on these
prompts" -> Phi (phi, at the settings' alpha) -> per-arm states, coherence flags, label rows and headline words
(labels) -> sensitivities (sensitivities; S-a's O and L tests run their own Phi) -> references and dominance
(references) -> the best feasible repair, per actor too. The output is one JSON-ready dict: numbers, names and rule
texts only. A RemlError inside the reading becomes a Refusal (exit 2 at the command line).
"""

from __future__ import annotations

import platform
from dataclasses import dataclass
from fractions import Fraction as Fr

import numpy as np

from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import labels, phi, references, sensitivities
from scripts.stage1_s1.reading.reml import RemlError
from scripts.stage1_s1.reading.schema import Input, validate
from scripts.stage1_s1.reading.settings import (ENDPOINTS, SETTINGS_SHA256, Design, Refusal, alpha, design,
                                                 level_per_comparison, module_hashes, settings)

MIN_O_COMPARATOR_SEEDS = 3        # LN-12's fallback (review-statistics ST-13): fewer than 3 R seeds -> "not tested"


@dataclass
class Context:
    design: Design
    tables: dict
    theta0_o: np.ndarray
    scale: dict
    floor: dict
    fits: dict                                   # endpoint -> {cluster: RemlFit}

    def within(self, e: str, first: str, second: str) -> con.Estimate:
        """v(first) - v(second) in the primary form: the cluster fit when both are fit arms of one cluster
        (REV3 3.2), else the pair's own paired variance on the common seeds (LN-20 item 2; REV3 3.5 item 2)."""
        dsg = self.design
        common = dsg.common_seeds(first, second)
        name = f"{first}-{second}"
        if dsg.in_fit(first) and dsg.in_fit(second) and dsg.same_cluster(first, second):
            return con.contrast_fit(self.tables[e], self.fits[e][dsg.cluster[first]], first, second, common,
                                    self.scale[e], True, name, "HB-C")
        return con.contrast_paired(self.tables[e], first, second, common, self.scale[e], True, name,
                                   "paired (J - 1 df; LN-20 item 2)")

    def vs_a0(self, e: str, m: str) -> con.Estimate:
        return self.within(e, m, "a0")

    def o_seeds(self, m: str) -> tuple:
        return tuple(sorted(j for a, j in self.tables["O"] if a == m))

    def vs_theta0(self, m: str) -> con.Estimate:
        """O(m) - O(theta0) (LN-20 item 1): one estimate, one SE and one df for F_k, O_k's theta0 part and the state.
        Over m's seeds with O-bank answers (R may hold fewer, LN-12)."""
        seeds = tuple(sorted(j for a, j in self.tables["O"] if a == m))
        return con.contrast_theta0(self.tables["O"], m, seeds, self.theta0_o, self.scale["O"], True, f"{m}-theta0")


def _context(inp: Input) -> Context:
    cfg = settings()
    dsg = design(inp.reading)
    scale = {e: float(cfg["endpoints"][e]["scale"]) for e in ENDPOINTS}
    floor = {e: float(cfg["endpoints"][e]["floor"]) for e in ENDPOINTS}
    fits = {e: sensitivities.fit_clusters(inp.tables[e], dsg, scale[e], floor[e], cfg=cfg) for e in ENDPOINTS}
    return Context(dsg, inp.tables, inp.theta0_o, scale, floor, fits)


def _fit_record(fit) -> dict:
    return {"arms": list(fit.arms), "sigma2": fit.sigma2, "at_floor": list(fit.at_floor), "iterations": fit.iterations,
            "converged": fit.converged, "residual_df": fit.residual_df, "residual_df_by_arm": fit.residual_df_by_arm,
            "start": fit.start, "two_arm": fit.two_arm, "pairs": fit.pairs, "not_identified": list(fit.not_identified),
            "floor": fit.floor, "steps": list(fit.steps),
            "note": "an arm at the floor is printed; no re-fit, no change of model (AMD A.3; LN-35)" if fit.at_floor else
                    ("the two-arm cluster: only the sum of the two variances is identified; no split is printed (REV3 3.5)"
                     if fit.two_arm else None)}


def _o_comparator_seeds(ctx: Context, c: str, m: str) -> tuple:
    seeds_c = {j for a, j in ctx.tables["O"] if a == c}
    return tuple(sorted(seeds_c & set(ctx.design.seeds[m])))


def _with_seed_only(e: con.Estimate | None, level: float) -> dict | None:
    """An O estimate with its interval and, beside it, the seed-only value labelled 'on these prompts' (REV3 3.6;
    6.6; LW-03): the same estimate with the item part dropped (S-0's form), its SE, df and interval."""
    if e is None:
        return None
    s = con.seed_only(e)
    return {"label": settings()["texts"]["on_these_prompts"], "estimate": s.as_dict(), "interval_90": list(s.interval(level))}


def _contrast(ctx: Context, name: str, c: str, m: str, start_level_u: Fr) -> dict:
    """U_k, O_k's parts, L_k's parts and F_k for one contrast (REV3 3.1-3.2, 3.6, 4.1, 4.3). ``start_level_u`` is
    U_k's two-sided start level in Phi (the printed MDE's level)."""
    dsg, cfg = ctx.design, settings()
    tau_o, tau_l = float(cfg["tau_o"]["star_pp"]), float(cfg["tau_l"]["nats"])
    level = level_per_comparison()
    u = ctx.within("U", c, m)
    o_seeds = _o_comparator_seeds(ctx, c, m)
    o_comp = None
    if len(o_seeds) >= MIN_O_COMPARATOR_SEEDS:
        if len(o_seeds) == len(dsg.common_seeds(c, m)):
            o_comp = ctx.within("O", m, c)
        else:
            o_comp = con.contrast_paired(ctx.tables["O"], m, c, o_seeds, ctx.scale["O"], True, f"{m}-{c}",
                                         "paired on the O seeds present (LN-12)")
    o_theta = ctx.vs_theta0(m)
    l_comp = ctx.within("L", m, c)
    l_a0 = ctx.within("L", m, "a0") if c != "a0" else l_comp
    p_o_comp = o_comp.p_upper(0.0) if o_comp is not None else 1.0
    p_o_theta = o_theta.p_upper(tau_o)
    p = {"U": u.p_two_sided(), "O": phi.iut(p_o_comp, p_o_theta), "L": phi.iut(l_comp.p_upper(0.0), l_a0.p_upper(tau_l)),
         "F": o_theta.p_lower(tau_o)}
    fam_level = 1.0 - 2.0 * float(alpha()) / dsg.familywise_sides
    return {"comparator": c, "repair": m, "common_seeds": list(dsg.common_seeds(c, m)),
            "U": u.as_dict(), "U_interval_90": list(u.interval(level)), "U_interval_familywise": list(u.interval(fam_level)),
            "familywise_level": fam_level, "U_mde_80_at_start_level": u.mde(float(start_level_u)),
            "U_start_level_two_sided": str(start_level_u),
            "O": {"comparator_part": o_comp.as_dict() if o_comp is not None else None,
                  "comparator_part_note": None if o_comp is not None else
                  f"not tested: {len(o_seeds)} R seeds with O-bank answers, fewer than {MIN_O_COMPARATOR_SEEDS} (LN-12)",
                  "comparator_interval_90": list(o_comp.interval(level)) if o_comp is not None else None,
                  "comparator_on_these_prompts": _with_seed_only(o_comp, level),
                  "theta0_part": o_theta.as_dict(), "theta0_interval_90": list(o_theta.interval(level)),
                  "theta0_on_these_prompts": _with_seed_only(o_theta, level),
                  "p_comparator": p_o_comp, "p_theta0": p_o_theta},
            "L": {"comparator_part": l_comp.as_dict(), "comparator_interval_90": list(l_comp.interval(level)),
                  "a0_part": l_a0.as_dict(), "a0_interval_90": list(l_a0.interval(level)),
                  "p_comparator": l_comp.p_upper(0.0), "p_a0": l_a0.p_upper(tau_l),
                  "reduces_to_a0_part": c == "a0"},
            "p_values": p, "_estimates": {"U": u, "O_comp": o_comp, "O_theta": o_theta, "L_comp": l_comp, "L_a0": l_a0}}


def _node_key(n) -> str:
    return f"{n[0]}:{n[1]}"


def _graph(dsg: Design):
    return phi.build_graph([name for name, _, _ in dsg.contrasts])


def _run_phi(dsg: Design, contrasts: dict, override: dict | None = None) -> tuple:
    """Phi at the settings' alpha on the contrasts' p-values; ``override`` maps (kind, contrast) to a p-value that
    replaces the primary one (a sensitivity's run)."""
    graph = _graph(dsg)
    pvalues = {}
    for name, _, _ in dsg.contrasts:
        p = contrasts[name]["p_values"]
        for kind in phi.KINDS:
            pvalues[(kind, name)] = p[kind]
    if override:
        pvalues.update(override)
    return graph, phi.run(graph, pvalues, alpha())


def _phi_record(outcome) -> dict:
    return {"alpha": str(alpha()), "rejected": [_node_key(n) for n in outcome.rejected],
            "level_at_rejection": {_node_key(n): str(v) for n, v in outcome.level_at_rejection.items()},
            "start_levels": {_node_key(n): str(v) for n, v in outcome.start_levels.items()},
            "final_levels": {_node_key(n): str(v) for n, v in outcome.final_levels.items()}}


def _o_states(o_ci, cfg) -> dict:
    return {f"tau_o_{g:g}": labels.feasibility_state(o_ci, float(g)) for g in cfg["tau_o"]["grid_pp"]}


def _states(ctx: Context, m: str) -> dict:
    """The per-comparison feasibility states of arm m (REV3 6.4): O against theta0 at the tau_O grid, L against a0;
    each O state beside its seed-only value 'on these prompts' (REV3 6.6). An arm with fewer than two O seeds has
    its theta0 contrast 'not tested' (LN-12's R; verify-code N3)."""
    cfg, t, level = settings(), settings()["texts"], level_per_comparison()
    below = f"tau_o_{cfg['tau_o']['below_resolution_pp']:g}"
    l = ctx.vs_a0("L", m) if m != "a0" else None
    out = {"l_vs_a0": l.as_dict() if l else None, "l_interval_90": list(l.interval(level)) if l else None,
           "l_state": labels.feasibility_state(l.interval(level), float(cfg["tau_l"]["nats"])) if l else None,
           "o_below_resolution": below, "o_below_resolution_text": f"{below}: {t['below_resolution']}"}
    if len(ctx.o_seeds(m)) < 2:
        out.update({"o_vs_theta0": None, "o_interval_90": None, "o_states": {k: t["not_tested"] for k in _o_states((0.0, 0.0), cfg)},
                    "o_on_these_prompts": None,
                    "o_note": f"{t['not_tested']}: {len(ctx.o_seeds(m))} seed(s) with O-bank answers (LN-12)"})
        return out
    o = ctx.vs_theta0(m)
    s = con.seed_only(o)
    o_ci, s_ci = o.interval(level), s.interval(level)
    out.update({"o_vs_theta0": o.as_dict(), "o_interval_90": list(o_ci), "o_states": _o_states(o_ci, cfg),
                "o_on_these_prompts": {"label": t["on_these_prompts"], "estimate": s.as_dict(), "interval_90": list(s_ci),
                                       "o_states": _o_states(s_ci, cfg)}})
    return out


def _arms(ctx: Context, inp: Input) -> dict:
    out = {}
    level = level_per_comparison()
    for arm in ctx.design.arms:
        rec = {"seeds": list(ctx.design.seeds[arm]),
               "means": {e: float(con.arm_values(ctx.tables[e], arm, sorted(j for a, j in ctx.tables[e] if a == arm), ctx.scale[e]).mean())
                         for e in ENDPOINTS},
               "coherence": labels.coherence_of_arm(inp.coherence[arm])}
        if arm != "a0":
            g = ctx.within("U", "a0", arm)                  # G_m = U(a0) - U(m) (REV3 3.1)
            rec["restoration_G"] = g.as_dict()
            rec["restoration_interval_90"] = list(g.interval(level))
        rec.update(_states(ctx, arm))
        out[arm] = rec
    return out


def _row(ctx: Context, name: str, k: dict, outcome, arms: dict) -> dict:
    """One label row (REV3 4.6) with its headline word; the U part again at the 4 pp margin as a reported
    sensitivity (REV3 4.4; PLAN-S:115), which never changes the word."""
    dsg, cfg = ctx.design, settings()
    delta = float(cfg["margin"]["delta_pp"])
    delta_s = float(cfg["margin"]["delta_sensitivity_pp"])
    rejected = set(outcome.rejected)
    u = labels.u_part(("U", name) in rejected, k["U"]["est"], tuple(k["U_interval_90"]), tuple(k["U_interval_familywise"]), delta)
    o_rej, l_rej, f_rej = ("O", name) in rejected, ("L", name) in rejected, ("F", name) in rejected
    m, c = k["repair"], k["comparator"]
    flags = labels.coherence_flags(arms[m]["coherence"]["passes"], arms[c]["coherence"]["passes"])
    head = labels.headline(u, o_rej, l_rej)
    side = []
    if o_rej:
        side.append(cfg["texts"]["worse_o"])
    if l_rej:
        side.append(cfg["texts"]["worse_l"])
    u_s = labels.u_part(("U", name) in rejected, k["U"]["est"], tuple(k["U_interval_90"]), tuple(k["U_interval_familywise"]), delta_s)
    row = {"contrast": name, "comparator": c, "repair": m,
           "u_part": u.as_dict(),
           "side_effect_part": {"words": side, "o_vs_comparator": k["O"]["comparator_part"], "o_vs_comparator_interval_90": k["O"]["comparator_interval_90"],
                                "o_vs_comparator_on_these_prompts": k["O"]["comparator_on_these_prompts"],
                                "o_vs_theta0_interval_90": k["O"]["theta0_interval_90"],
                                "o_vs_theta0_on_these_prompts": k["O"]["theta0_on_these_prompts"],
                                "l_vs_comparator_interval_90": k["L"]["comparator_interval_90"],
                                "l_vs_a0_interval_90": k["L"]["a0_interval_90"], "o_comparator_note": k["O"]["comparator_part_note"]},
           "feasibility_part": {"F_k_rejects_in_phi": f_rej, "F_k_text": "feasible (O, tau_O = 5)" if f_rej else None,
                                "states": arms[m]["o_states"], "l_state": arms[m]["l_state"],
                                "states_on_these_prompts": arms[m]["o_on_these_prompts"]["o_states"] if arms[m]["o_on_these_prompts"] else None,
                                "below_resolution": arms[m]["o_below_resolution"],
                                "below_resolution_text": arms[m]["o_below_resolution_text"]},
           "coherence_part": list(flags), "sensitivity_part": [],
           "margin_sensitivity": {"delta_pp": delta_s, "u_part": u_s.as_dict(), "headline": labels.headline(u_s, o_rej, l_rej),
                                  "note": "reported at the 4 pp margin (REV3 4.4); the label is the 5 pp one"},
           "headline": head, "label_suffix": dsg.label_suffix}
    if dsg.label_suffix:
        row["headline"]["cell"] = f"{head['cell']} [{dsg.label_suffix}]"
    return row


def _sensitivity_block(ctx: Context, inp: Input, contrasts: dict, rows: dict, outcome) -> dict:
    """REV3 3.4: every sensitivity's U estimates; its U-part words under Phi with the primary O, L and F p-values;
    those that differ print in the row's sensitivity part. S-a also runs its O and L tests (LW-02 S-1): the
    comparator parts and L's a0 part by Welch, O's theta0 part by LW-33's form, through Phi with S-a's U p-values;
    its headline word prints beside the primary's when it differs. The S-a equal-variance flag reads the rejection
    sets of the S-a and S-aW runs (LW-02; verify-code F9)."""
    dsg, cfg = ctx.design, settings()
    delta = float(cfg["margin"]["delta_pp"])
    level = level_per_comparison()
    table, scale, floor = ctx.tables["U"], ctx.scale["U"], ctx.floor["U"]
    fam_level = 1.0 - 2.0 * float(alpha()) / dsg.familywise_sides
    block, rejected_by_code = {}, {}

    def words_of(name, est, rej):
        return labels.u_part(rej, est.est, est.interval(level), est.interval(fam_level), delta).words

    def record(code, ests, extra_override=None):
        override = {("U", n): e.p_two_sided() for n, e in ests.items()}
        override.update(extra_override or {})
        _, out = _run_phi(dsg, contrasts, override)
        rejected = set(out.rejected)
        rejected_by_code[code] = rejected
        rec = {}
        for name, e in ests.items():
            words = words_of(name, e, ("U", name) in rejected)
            differs = list(words) != list(rows[name]["u_part"]["words"])
            rec[name] = {"estimate": e.as_dict(), "interval_90": list(e.interval(level)), "u_part_words": list(words),
                         "differs_from_primary": differs, "rejected_in_phi": ("U", name) in rejected}
            if differs:
                rows[name]["sensitivity_part"].append({"code": code, "u_part_words": list(words)})
        return rec, out

    for code in ("HB", "S-a", "S-aW", "S-b2x", "S-0", "S-p"):
        block[code], _ = record(code, sensitivities.u_estimates(code, table, dsg, scale, floor, ctx.fits["U"], cfg))
    for name, _, _ in dsg.contrasts:
        flag = ("U", name) in rejected_by_code["S-a"] and ("U", name) not in rejected_by_code["S-aW"]
        block["S-a"][name]["equal_variance_flag"] = flag
        if flag:
            rows[name]["sensitivity_part"].append({"code": "S-a", "flag": cfg["texts"]["equal_variance_flag"]})
    block["S-a (O, L)"] = _s_a_side_effects(ctx, contrasts, rows, block["S-a"], record)
    block["S-G"] = {v: record(f"S-G {v}", ests)[0] for v, ests in sensitivities.variant_estimates(inp.variants, dsg, scale, floor, cfg).items()}
    block["S-A8"] = _s_a8(ctx)
    block["S-tok"] = sensitivities.token_axis(table, dsg, scale, inp.token_axis) if inp.token_axis else None
    block["note"] = cfg["sensitivities_rule"]
    return block


def _s_a_side_effects(ctx: Context, contrasts: dict, rows: dict, s_a_u: dict, record) -> dict:
    """S-a's O and L tests (REV3 3.4; 3.6 item 3): per contrast the Welch comparator parts, L's Welch a0 part and
    LW-33's theta0 part, their IUT p-values and F's; Phi with S-a's U and these O, L, F p-values; the side-effect
    words and the headline word under S-a, printed in the row's sensitivity part when the word differs."""
    dsg, cfg, level = ctx.design, settings(), level_per_comparison()
    tau_o, tau_l = float(cfg["tau_o"]["star_pp"]), float(cfg["tau_l"]["nats"])
    ests = sensitivities.s_a_side_effects(ctx.tables, dsg, ctx.scale, ctx.theta0_o, MIN_O_COMPARATOR_SEEDS)
    override, per = {}, {}
    for name, c, m in dsg.contrasts:
        e = ests[name]
        p_o_comp = e["O_comp"].p_upper(0.0) if e["O_comp"] is not None else 1.0
        p_o_theta = e["O_theta"].p_upper(tau_o)
        p = {"O": phi.iut(p_o_comp, p_o_theta), "L": phi.iut(e["L_comp"].p_upper(0.0), e["L_a0"].p_upper(tau_l)),
             "F": e["O_theta"].p_lower(tau_o)}
        for kind, value in p.items():
            override[(kind, name)] = value
        per[name] = {"O": {"comparator_part": e["O_comp"].as_dict() if e["O_comp"] is not None else None,
                           "comparator_interval_90": list(e["O_comp"].interval(level)) if e["O_comp"] is not None else None,
                           "theta0_part": e["O_theta"].as_dict(), "theta0_interval_90": list(e["O_theta"].interval(level)),
                           "p_comparator": p_o_comp, "p_theta0": p_o_theta},
                     "L": {"comparator_part": e["L_comp"].as_dict(), "comparator_interval_90": list(e["L_comp"].interval(level)),
                           "a0_part": e["L_a0"].as_dict(), "a0_interval_90": list(e["L_a0"].interval(level)),
                           "p_comparator": e["L_comp"].p_upper(0.0), "p_a0": e["L_a0"].p_upper(tau_l)},
                     "p_values": p}
    u_ests = {name: _estimate_from(s_a_u[name]["estimate"]) for name in s_a_u}
    _, out = record("S-a (O, L)", u_ests, override)
    rejected = set(out.rejected)
    for name, c, m in dsg.contrasts:
        rec = per[name]
        rec["p_values"]["U"] = u_ests[name].p_two_sided()
        u = labels.u_part(("U", name) in rejected, u_ests[name].est, u_ests[name].interval(level),
                          u_ests[name].interval(1.0 - 2.0 * float(alpha()) / dsg.familywise_sides), float(cfg["margin"]["delta_pp"]))
        o_rej, l_rej, f_rej = ("O", name) in rejected, ("L", name) in rejected, ("F", name) in rejected
        head = labels.headline(u, o_rej, l_rej)
        rec.update({"rejected": [_node_key(n) for n in out.rejected if n[1] == name], "u_part_words": list(u.words),
                    "side_effect_words": [w for w, r in ((cfg["texts"]["worse_o"], o_rej), (cfg["texts"]["worse_l"], l_rej)) if r],
                    "F_k_rejects": f_rej, "headline": head, "differs_from_primary": head["word"] != rows[name]["headline"]["word"]})
        # record() already listed a differing U part under the code; the headline word is the sensitivity's label
        rows[name]["sensitivity_part"] = [s for s in rows[name]["sensitivity_part"] if s.get("code") != "S-a (O, L)"]
        if rec["differs_from_primary"]:
            rows[name]["sensitivity_part"].append({"code": "S-a (O, L)", "headline_word": head["word"]})
    per["rule"] = ("REV3 3.4: under S-a the O and L 'worse' tests use the per-contrast Welch form and O's feasibility "
                   "variance against theta0 LW-33's form; printed; the primary governs (LW-02)")
    return per


def _estimate_from(d: dict) -> con.Estimate:
    fields = {k: d[k] for k in ("name", "form", "est", "se", "df", "seed_var", "seed_df", "item_var", "item_q", "pairs", "items", "with_item")}
    return con.Estimate(**fields)


def _s_a8(ctx: Context) -> dict:
    """S-A8 (REV3 3.4; review-statistics ST-2): AMD A.8's theta0 form and the in-model cross-cluster form, printed
    as 'seed shift omitted' beside LN-20's forms."""
    dsg, out = ctx.design, {}
    cfg = settings()
    for name, c, m in dsg.contrasts:
        rec = {}
        fit_o = ctx.fits["O"].get(dsg.cluster[m])
        if fit_o is not None and not fit_o.two_arm and m in fit_o.arms:
            a8 = con.contrast_theta0_a8(ctx.tables["O"], fit_o, m, dsg.seeds[m], ctx.theta0_o, ctx.scale["O"], f"{m}-theta0")
            rec["o_vs_theta0_a8"] = a8.as_dict()
            rec["o_vs_theta0_ln20"] = ctx.vs_theta0(m).as_dict()
        if dsg.cluster[m] == "removal" and dsg.in_fit("a0") and "full" in ctx.fits["L"] and not ctx.fits["L"]["full"].two_arm:
            merged = _merged_fit(ctx.fits["L"]["removal"], ctx.fits["L"]["full"])
            common = dsg.common_seeds(m, "a0")
            rec["l_vs_a0_in_model_a8"] = con.contrast_cross_a8(ctx.tables["L"], merged, m, "a0", common, ctx.scale["L"], f"{m}-a0").as_dict()
            rec["l_vs_a0_ln20"] = ctx.vs_a0("L", m).as_dict()
        out[name] = rec
    out["label"] = cfg["texts"]["seed_shift_omitted"]
    return out


def _merged_fit(a, b):
    """Two cluster fits read as one (block-diagonal information): AMD A.8's in-model cross-cluster form."""
    from scripts.stage1_s1.reading.reml import RemlFit
    arms = a.arms + b.arms
    n_a = len(a.arms)
    inv = np.zeros((len(arms), len(arms)))
    inv[:n_a, :n_a] = a.info_inv
    inv[n_a:, n_a:] = b.info_inv
    return RemlFit(arms=arms, sigma2={**a.sigma2, **b.sigma2}, info_inv=inv, at_floor=a.at_floor + b.at_floor,
                   iterations=max(a.iterations, b.iterations), converged=a.converged and b.converged,
                   residual_df=a.residual_df + b.residual_df, residual_df_by_arm={**a.residual_df_by_arm, **b.residual_df_by_arm},
                   start={**a.start, **b.start}, not_identified=a.not_identified + b.not_identified, two_arm=False, floor=a.floor)


def _references(ctx: Context, inp: Input, arms: dict) -> dict:
    if not inp.references:
        return {"tested": False, "reason": "no reference in the input", "per_repair": {}, "family_1b": {"tested": False, "reason": "no reference", "contrasts": {}}}
    dsg, cfg = ctx.design, settings()
    per_repair = {m: [] for m in dsg.repair_arms}
    for ref in inp.references:
        if ref.kind == "point":
            fits = {e: references.reference_fit(references.merge(ctx.tables[e], ref.tables[e]), dsg, ref.name, ref.seeds,
                                                ctx.scale[e], ctx.floor[e], cfg) for e in ENDPOINTS}
            for m in dsg.repair_arms:
                per_repair[m].append(references.beats_point(ctx, m, ref.name, ref.tables, ref.seeds, fits))
        else:
            for m in dsg.repair_arms:
                per_repair[m].append(references.beats_curve(ctx, m, ref, ctx.vs_a0("L", m), ref.theta0["U"], ref.theta0["L"]))
    for m, points in per_repair.items():
        if not arms[m]["coherence"]["passes"]:
            for p in points:
                # REV3 3.7 item 5: a failing arm cannot dominate; its D_k component carries p = 1 into family 1b
                # (the arm keeps its place in the Holm family; verify-code F1)
                p["beats"] = False
                p["p_iut"] = 1.0
                p["blocked_by_coherence"] = "a failing arm cannot dominate a reference (REV3 3.7 item 5)"
    return {"tested": True, "per_repair": per_repair, "family_1b": references.dominance(per_repair, dsg.contrasts)}


def _candidates(ctx: Context, rows: dict, arms: dict, tau_o_key: str) -> list:
    """The repairs with their 'better' and 'feasible' flags: at tau_O* = 5 feasibility is F_k's Phi result; at
    tau_O = 2 or 10 the per-comparison state; at tau_L always the per-comparison L state (REV3 4.6 last row)."""
    t = settings()["texts"]
    out = []
    for name, c, m in ctx.design.contrasts:
        row = rows[name]
        if tau_o_key == "tau_o_5":
            o_ok = row["feasibility_part"]["F_k_rejects_in_phi"]
        else:
            o_ok = row["feasibility_part"]["states"][tau_o_key] == t["feasible"]
        feasible = o_ok and row["feasibility_part"]["l_state"] == t["feasible"] and arms[m]["coherence"]["passes"]
        out.append({"arm": m, "contrast": name, "restoration": arms[m]["restoration_G"]["est"],
                    "better": row["u_part"]["better"], "feasible": bool(feasible)})
    return out


def _best_feasible(ctx: Context, rows: dict, arms: dict, contrasts: dict) -> dict:
    """REV3 4.6 last row and 4.9: the best feasible repair at tau_O* = 5 (F_k in Phi) and tau_L (the state)."""
    candidates = _candidates(ctx, rows, arms, "tau_o_5")
    result = labels.best_feasible_repair(candidates, lambda a, b: ctx.within("U", b, a))
    result["candidates"] = candidates
    result["rule"] = ("better, feasible at tau_O* = 5 (F_k rejects in Phi) and at tau_L (the per-comparison state), separated "
                      "from the runner-up by the 90% interval of their seed-matched contrast; else 'too close to call'. "
                      "No single error rate (REV3 4.6; ST-15)")
    return result


def _actors(ctx: Context, rows: dict, arms: dict) -> dict:
    """REV3 4.9 and 9.4 (LN-08): per actor the menu, every pair's separation, and the best data arm by point
    estimate (G_m) among the menu's better and feasible repairs at tau_O* = 5 and tau_L, and at tau_O = 2 and 10 by
    the per-comparison states; 'too close to call' unless separated (verify-code F8). Report only."""
    cfg = settings()
    level = level_per_comparison()
    out = {}
    for actor, menu in cfg["actors"].items():
        if actor == "rule":
            continue
        present = [a for a in menu if a in ctx.design.arms]
        pairs = {}
        for i, a in enumerate(present):
            for b in present[i + 1:]:
                e = ctx.within("U", a, b)
                pairs[f"{a}-{b}"] = {"estimate": e.as_dict(), "interval_90": list(e.interval(level)),
                                     "separated": labels.separated(e), "form": e.form}
        best = {}
        for key in (f"tau_o_{g:g}" for g in cfg["tau_o"]["grid_pp"]):
            cands = [c for c in _candidates(ctx, rows, arms, key) if c["arm"] in present]
            result = labels.best_feasible_repair(cands, lambda a, b: ctx.within("U", b, a))
            result["candidates"] = cands
            best[key] = result
        out[actor] = {"menu": present, "pairs": pairs, "best_data_arm": best,
                      "best_reference": None, "best_reference_note": "references are compared in family 1b (REV3 5.3); no per-actor reference menu is in this input"}
    out["rule"] = cfg["actors"]["rule"]
    return out


def _strip(obj):
    """Drop the private Estimate objects and make everything JSON-ready."""
    if isinstance(obj, dict):
        return {str(k): _strip(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [_strip(v) for v in obj]
    if isinstance(obj, Fr):
        return str(obj)
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, float) and not np.isfinite(obj):
        return None if np.isnan(obj) else ("inf" if obj > 0 else "-inf")
    return obj


def read(doc: dict, input_sha256: str | None = None) -> dict:
    """The whole reading of one validated input document; a RemlError becomes a Refusal."""
    try:
        return _read(doc, input_sha256)
    except RemlError as exc:
        raise Refusal(f"the REML fit refused: {exc}") from None


def _read(doc: dict, input_sha256: str | None) -> dict:
    inp = validate(doc)
    ctx = _context(inp)
    dsg = ctx.design
    start = phi.levels(_graph(dsg), alpha())
    contrasts = {name: _contrast(ctx, name, c, m, start[("U", name)]) for name, c, m in dsg.contrasts}
    graph, outcome = _run_phi(dsg, contrasts)
    arms = _arms(ctx, inp)
    rows = {name: _row(ctx, name, contrasts[name], outcome, arms) for name in contrasts}
    sens = _sensitivity_block(ctx, inp, contrasts, rows, outcome)
    refs = _references(ctx, inp, arms)
    best = _best_feasible(ctx, rows, arms, contrasts)
    out = {"kind": "stage1 reading output", "version": 1, "reading": inp.reading, "label_suffix": dsg.label_suffix,
           "provenance": {"settings_sha256": SETTINGS_SHA256, "modules": module_hashes(), "input_sha256": input_sha256,
                          "python": platform.python_version(), "numpy": np.__version__},
           "design": {"arms": list(dsg.arms), "fit_arms": list(dsg.fit_arms), "cluster": dsg.cluster,
                      "seeds": {a: list(s) for a, s in dsg.seeds.items()}, "contrasts": [list(c) for c in dsg.contrasts],
                      "familywise_sides": dsg.familywise_sides},
           "fits": {e: {cl: _fit_record(f) for cl, f in ctx.fits[e].items()} for e in ENDPOINTS},
           "arms": arms, "contrasts": contrasts, "phi": _phi_record(outcome), "rows": rows,
           "headline": {name: rows[name]["headline"]["word"] for name in rows},
           "headline_cells": {name: rows[name]["headline"]["cell"] for name in rows},
           "sensitivities": sens, "references": refs, "best_feasible_repair": best, "actors": _actors(ctx, rows, arms),
           "notes": _notes(ctx, outcome)}
    return _strip(out)


def _notes(ctx: Context, outcome) -> list:
    cfg = settings()
    notes = [cfg["phi"]["rule"], cfg["phi"]["iut"], cfg["reml"]["floors_rule"], cfg["reml"]["stop_rule"],
             f"REML floor mode: {cfg['reml']['floor_mode']} ({cfg['reml']['floor_mode_rule']})",
             "the O error model is prompts random (LW-03); every O number carries its seed-only value 'on these prompts' beside it; S-0 is the U contrasts' seed-only form",
             "'the best feasible repair' has no single error rate (REV3 4.6; ST-15)"]
    if ctx.design.label_suffix:
        notes.append(f"every label carries '{ctx.design.label_suffix}'; the record prints block A's MDE per contrast")
    for e in ENDPOINTS:
        for cl, f in ctx.fits[e].items():
            if f.at_floor:
                notes.append(f"{e} {cl}: arm(s) at the floor {list(f.at_floor)} (expected in about half of all fits; no action)")
            if not f.converged and not f.two_arm:
                notes.append(f"{e} {cl}: the REML stopped at {f.iterations} steps without meeting the tolerance")
    return notes
