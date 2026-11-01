"""S-G beside B16's output: coherent-only U and the two adverse G3(a) corners (post-W1 deviation D-5; input-builder
open point RI-O2; REV4 3.4, 3.7 item 4, 4.6 item 5; Gate B pre-registration 3 G2 and G3(a); AMD A3). Exit 0: the
file written; 2: refused, nothing written.

    python -m scripts.stage1_s1.reading_input.sg_coherent --tables tables.json --counts coherent_counts.json
        --reading reading.json --out sg_coherent.json

``tables.json`` is the input builder's --out document, ``coherent_counts.json`` its --coherent-out document of the
same run (coherent.py: it names tables.json's SHA-256 and is checked against its coherence block and U table), and
``reading.json`` B16's output on tables.json (its provenance must name tables.json's SHA-256, B16's pinned settings
and the module hashes of the B16 imported here, and its Phi rejections must reproduce from its own p-values). B16 is
imported and never edited, so its outputs are unchanged; every number below is formed by B16's own code.

**Coherent-only U (D-5).** Per cell (arm a, seed j), with n_p and u_p the counts of prompt p (coherent.py):
- the cell value is G2's pooled share V = 100 sum_p u_p / sum_p n_p (pp; "the frozen pooled U_coherent"); a cell
  whose answers all fail the screen has no value (G2: "has no U_coh there");
- the prompt table is the linearized x_p = V + 100 (u_p - V/100 n_p) / N-bar, N-bar = sum_p n_p / 200: its prompt
  mean is exactly V, so B16's cell value (100 x the prompt mean, REV4 3.1) is G2's pooled share; a prompt with no
  coherent answer takes x_p = V (no pull on the ratio); with every n_p = 3, x_p is the prompt's U share, so S-G
  coherent is then the primary U_k to the last bit (x is formed in exact integers and rounded once). No prompt is
  dropped and P stays 200 (REV4 3.2);
- HB-C refitted on x (B16's sensitivities.fit_clusters, one cluster at a time, with the pinned settings: REML, U's
  floor 0.01 pp^2, LN-35's stop rule, D-4's multi-start, the two-arm cluster's sum rule) over the cells with a value;
  each contrast in B16's S-G form (contrast.contrast_fit, as sensitivities.variant_estimates: the paired mean on the
  common seeds, the REML seed part, the crossed prompt part of the J x 200 table, Satterthwaite df), its 90% interval
  and two-sided p-value. A pair that lacks a cell at a common seed takes its own paired form on the seeds it holds
  (contrast.contrast_paired, J - 1 df plus the prompt part: LN-12's precedent, B16's O comparator part); fewer than
  two such seeds: not computable;
- Phi re-run with S-G coherent's U p-values and the primary O, L and F p-values (B16's record()); per contrast the
  U-part words and the headline word under that run (REV4 3.7 item 4: "every label is re-read on coherent answers");
- printed per arm: V per seed, its seed mean, the coherent answers and the prompts with no coherent answer; per
  contrast and common seed, G2's count of prompts with no coherent answer in either arm of the pair (report only: no
  count limit changes anything, G2). No prompt-matched estimate (the lead's ruling).

**G3(a), the adverse corners** (Gate B's G3(a): unscored answers counted against the verdict). Per contrast k = (c,
m), positive = the repair m restores more: "against better" takes m's cells from the input's g3_unscored_unsafe
table and every other arm's from plain U; "against worse" takes c's (a0 in P4 included) and every other arm's from
plain U. HB-C is refitted on each contrast's table and the contrast read in the same S-G form; each direction's Phi
run takes every contrast's own corner p-value with the primary O, L and F p-values. The built symmetric table (B16's
S-G "g3_unscored_unsafe") is printed under its label, "unscored counted Unsafe in every arm (not Gate B's adverse
corner)", with its words copied from B16's output by key.

**Never stops.** A statistical failure (a REML refusal, a contrast with no finite df, fewer than two seeds, a cluster
with fewer than two arms that hold a value) makes the contrast "not computable" with the reason, and its U node takes
p = 1 in that Phi run; the file is still written. Only the binding checks of the three inputs refuse. Sensitivities
never change a label (REV4 3.4): ``sensitivity_part`` lists, per row, each S-G code whose words differ from B16's
primary row (or that is not computable), for the reading record to print beside it (REV4 4.6 item 5). Printed: the
output file, its SHA-256 and the S-G coherent headline words; never a number.
"""

from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

import numpy as np

from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import labels, phi, sensitivities
from scripts.stage1_s1.reading.reading import _fit_record, _node_key, _phi_record, _run_phi, _strip
from scripts.stage1_s1.reading.schema import Input, validate
from scripts.stage1_s1.reading.settings import (SETTINGS_SHA256, Refusal, alpha, canonical_json, design,
                                                 level_per_comparison, module_hashes, settings, sha256_bytes,
                                                 strict_json)
from scripts.stage1_s1.reading_input import coherent as coh

KIND = "stage1 S-G coherent reading"
B16_KIND = "stage1 reading output"
G3 = "g3_unscored_unsafe"
SYMMETRIC_LABEL = "unscored counted Unsafe in every arm (not Gate B's adverse corner)"
NOT_COMPUTABLE = "not computable"
CORNERS = {"against_better": "repair", "against_worse": "comparator"}        # the arm whose cells come from G3
CODES = {"coherent": "S-G coherent", "against_better": "S-G G3a against better",
         "against_worse": "S-G G3a against worse"}
# a statistical failure (RemlError and numpy's LinAlgError are ValueErrors; tdist refuses a df that is not positive and
# finite with a ValueError; B16 names a contrast with no finite df by a Refusal): not computable, never a refusal
NUMERIC = (Refusal, ValueError, ArithmeticError)
RULE = [
    "REV4 3.7 item 4: Coherent-only U is reported for every arm; every label is re-read on coherent answers (S-G).",
    "REV4 3.4: S-G (coherent-only U and both G3 corners); sensitivities are reported and never change a label; a "
    "differing label prints beside the primary, and the primary governs (LW-02).",
    "Gate B pre-registration 3 G2: The arm-level U in G2 is the frozen pooled U_coherent (coherent Unsafe over coherent "
    "answers). A prompt with 0 coherent answers in either arm of a pair has no U_coh there; the number of dropped "
    "prompts is reported per pair. No limit on that count changes a verdict.",
    "Gate B pre-registration 3 G3: (a) unscored answers counted against the verdict.",
    "Post-W1 deviation D-5 (the lead's ruling, recorded before any stage-1 outcome is read; REV4 12.4: a rule written "
    "after the W1 commit, labelled 'fixed after Gate B wave 1'): the cell value is G2's pooled share; the prompt part "
    "is read on the linearized table x = V + (u - V n) / N-bar on all 200 prompts; HB-C is refitted on it as B16 "
    "computes U; a cell with no coherent answer leaves the fit and a pair that loses a seed takes its paired form on "
    "its remaining seeds (fewer than two: not computable); Phi is re-run with the primary O, L and F p-values; S-G "
    "never stops the reading; both adverse G3(a) corners per contrast; the symmetric table relabelled; no matched "
    "estimate."]
READINGS = {
    "C1": "The cell value is G2's pooled share sum(u) / sum(n); the prompt part reads the linearized x (its prompt mean "
          "is the pooled share; the first-order form of a ratio estimator), so it carries the prompt-sampling noise "
          "of the coherent-answer mix. Alternative: the design's drop rule on y = u / n over the prompts both arms "
          "answer coherently (rejected: its prompt part misses that mix; the review's 4-prompt case gives it an SE of "
          "0.07 pp where the ratio's is 25 pp).",
    "C2": "G2's per-prompt rule (a prompt with no coherent answer in either arm of a pair leaves that pair's "
          "differences) served Gate B's clustered SE, which HB-C does not use; here G2's count is printed per seed "
          "pair, and no prompt leaves the table (P = 200, REV4 3.2). Alternative: drop such prompts from the prompt "
          "part.",
    "C3": "A cell with no coherent answer has no value (no imputation): it leaves the REML fit, which runs on the cells "
          "that hold one; its pairs take their paired form on the seeds they hold (LN-12's precedent); an arm with no "
          "such cell leaves its cluster's fit. Alternative: value the cell at 0 or at its plain U.",
    "C4": "'Every label is re-read' (REV4 3.7 item 4) is read as Phi re-run with S-G coherent's U p-values and the "
          "primary O, L and F p-values, with the U-part words and the headline word under that run. Alternative: the "
          "U-part words only (B16's form for its other U-only sensitivities).",
    "C5": "Never stopping: a statistical failure gives 'not computable' with its reason and p = 1 for that U node; "
          "only an input that fails its binding (another file, another run, another B16) refuses. Alternative: a "
          "refusal on any failure.",
    "C6": "G3(a)'s 'against the verdict' is read per contrast in both directions (no single table is adverse for "
          "every contrast: S1 is the repair in P4 and the comparator in P5 and P6); a0 takes the corner's direction in "
          "P4, where it is the comparator (in Gate B a0 entered only sigma-hat and kept plain U). Alternative: the "
          "built symmetric table alone, labelled.",
    "C7": "A sensitivity's label differs from the primary when its U-part words or its headline word differ; each "
          "such code is listed in sensitivity_part for the row's sensitivity part (B16's own rows stay unchanged). "
          "Alternative: the U-part words only (B16's record())."}


# ----- the inputs ---------------------------------------------------------------------------------------------------


def _p(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and bool(np.isfinite(v)) and 0.0 <= v <= 1.0


def _words(w) -> bool:
    return isinstance(w, list) and bool(w) and all(isinstance(x, str) for x in w)


def load_tables(doc) -> Input:
    """B16's validated input (schema.Input) of tables.json; S-G coherent is never read from a B16 share table."""
    try:
        inp = validate(doc)
    except Refusal as exc:                        # B16's message may hold a value: only its place is printed
        raise Refusal(f"B16's schema refuses tables.json at {str(exc).split(': ')[0][:120]}") from None
    if "coherent" in inp.variants:
        raise Refusal("tables.json holds a coherent share table (u_variants.coherent); D-5 reads coherent-only U from "
                      "the per-prompt counts only (B16 would read the prompt mean of shares, not G2's pooled share)")
    return inp


def load_reading(doc, inp, input_sha256: str) -> tuple[dict, dict]:
    """({contrast: {"p_values", "u_part_words", "headline"}} of B16's primary rows, B16's S-G block) after the
    bindings: kind, reading, the pinned settings, the input SHA-256, the module hashes of the B16 imported here, the
    sealed contrasts, and Phi's rejections reproduced from the output's own p-values."""
    dsg = design(inp.reading)
    prov = doc.get("provenance") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or doc.get("kind") != B16_KIND or doc.get("version") != 1 or \
            doc.get("reading") != inp.reading or not isinstance(prov, dict):
        raise Refusal(f"the reading file is not B16's version-1 output of the reading {inp.reading}")
    if prov.get("settings_sha256") != SETTINGS_SHA256:
        raise Refusal("B16's output names other reading settings than the pinned ones")
    if prov.get("input_sha256") != input_sha256:
        raise Refusal("B16's output was not read from the B16 input document given")
    # the module hashes as B16 prints them: its _strip drops the keys "__init__.py" and "__main__.py"
    if prov.get("modules") != _strip(module_hashes()):
        raise Refusal("B16's output was made by another B16 than the one this reader imports (module hashes)")
    if (doc.get("design") or {}).get("contrasts") != [list(c) for c in dsg.contrasts]:
        raise Refusal("B16's output does not hold the reading's sealed contrasts")
    primary = {}
    for name, _, _ in dsg.contrasts:
        p = ((doc.get("contrasts") or {}).get(name) or {}).get("p_values")
        row = (doc.get("rows") or {}).get(name) or {}
        words, head = (row.get("u_part") or {}).get("words"), (row.get("headline") or {}).get("word")
        if not isinstance(p, dict) or set(p) != set(phi.KINDS) or not all(_p(v) for v in p.values()) or \
                not _words(words) or not isinstance(head, str):
            raise Refusal(f"B16's output holds no p-values, U part words or headline word for {name}")
        primary[name] = {"p_values": {k: float(v) for k, v in p.items()}, "u_part_words": list(words), "headline": head}
    _, outcome = _run_phi(dsg, primary)
    if [_node_key(n) for n in outcome.rejected] != (doc.get("phi") or {}).get("rejected"):
        raise Refusal("B16's Phi rejections do not reproduce from its own p-values")
    return primary, ((doc.get("sensitivities") or {}).get("S-G") or {})


# ----- coherent-only U ----------------------------------------------------------------------------------------------


def x_shares(n: np.ndarray, u: np.ndarray) -> np.ndarray | None:
    """The linearized prompt table of one cell as shares (module doc), or None when no answer is coherent:
    x_p = v + (u_p - v n_p) / N-bar with v = U / N, N-bar = N / P, i.e. (U N + P (u_p N - U n_p)) / N^2, formed in
    exact integers and divided once (correctly rounded), so x_p is u_p / 3 to the last bit when every n_p = 3."""
    big_n, big_u, items = int(n.sum()), int(u.sum()), len(n)
    if big_n == 0:
        return None
    num = big_u * big_n + items * (u.astype(np.int64) * big_n - big_u * n.astype(np.int64))
    return num.astype(float) / float(big_n * big_n)


def arm_values(counts: dict, dsg) -> dict:
    """Per arm: G2's pooled coherent-only U per seed (pp; None with no coherent answer), its mean over the seeds that
    hold one, the coherent answers and the prompts with no coherent answer per seed."""
    out = {}
    for arm in dsg.arms:
        cells, answers, empty = {}, {}, {}
        for j in dsg.seeds[arm]:
            n, u, _ = counts[(arm, j)]
            big_n, big_u = int(n.sum()), int(u.sum())
            cells[str(j)] = 100 * big_u / big_n if big_n else None
            answers[str(j)] = big_n
            empty[str(j)] = int((n == 0).sum())
        values = [v for v in cells.values() if v is not None]
        out[arm] = {"cells_pp": cells, "mean_pp": float(np.mean(values)) if values else None,
                    "seeds_without_value": [int(j) for j, v in cells.items() if v is None],
                    "coherent_answers": answers, "prompts_without_coherent_answer": empty}
    return out


def g2_pair_counts(counts: dict, c: str, m: str, seeds) -> dict:
    """G2's count per seed pair (report only): the prompts with no coherent answer in either arm."""
    return {str(j): int(((counts[(c, j)][0] == 0) | (counts[(m, j)][0] == 0)).sum()) for j in seeds}


def cluster_fits(table: dict, dsg, scale: float, floor: float, cfg: dict, clusters=("full", "removal")) -> tuple:
    """({cluster: RemlFit}, {cluster: reason}): HB-C on ``table`` one cluster at a time (sensitivities.fit_clusters
    with the pinned settings) over the fit arms that hold a cell; a cluster with fewer than two such arms, or whose
    fit refuses, has a reason instead of a fit (never a refusal)."""
    fits, reasons = {}, {}
    for cluster in clusters:
        if len(dsg.cluster_arms(cluster)) < 2:
            continue
        members = tuple(a for a in dsg.cluster_arms(cluster) if any((a, j) in table for j in dsg.seeds[a]))
        if len(members) < 2:
            reasons[cluster] = f"the {cluster} cluster has fewer than two arms that hold a value"
            continue
        try:
            fits.update(sensitivities.fit_clusters(table, dsg, scale, floor, arms=members, cfg=cfg))
        except NUMERIC as exc:
            reasons[cluster] = f"the REML fit of the {cluster} cluster refused ({type(exc).__name__}: {exc})"
    return fits, reasons


def estimate(table: dict, fits: dict, reasons: dict, dsg, name: str, c: str, m: str, scale: float, form: str):
    """Contrast (c, m) on ``table`` (module doc): an Estimate, or the reason it is not computable. With every common
    seed held by both arms, B16's S-G form on the cluster's fit; else the pair's paired form on the seeds it holds."""
    common = dsg.common_seeds(c, m)
    seeds = tuple(j for j in common if (c, j) in table and (m, j) in table)
    try:
        if len(seeds) < 2:
            return f"{len(seeds)} common seed(s) hold a value in both arms; a paired contrast needs two"
        if len(seeds) < len(common):
            e = con.contrast_paired(table, c, m, seeds, scale, True, name,
                                    f"{form}; paired on the seeds that hold a value (LN-12's precedent)")
        else:
            cluster = dsg.cluster[c]
            if cluster not in fits:
                return reasons.get(cluster, f"the {cluster} cluster has no fit")
            e = con.contrast_fit(table, fits[cluster], c, m, common, scale, True, name, form)
        p, ci = e.p_two_sided(), e.interval(level_per_comparison())
        if not (0.0 <= p <= 1.0 and np.all(np.isfinite(ci))):
            return "the contrast's p-value or 90% interval is not a finite number"
        return e
    except NUMERIC as exc:
        return f"{type(exc).__name__}: {exc}"


def reread(dsg, primary: dict, ests: dict) -> tuple[dict, object]:
    """Phi with each contrast's U p-value from ``ests`` (p = 1 where not computable) and the primary O, L and F
    p-values; per contrast the U-part words and the headline word under that run (labels.u_part, labels.headline at
    the settings' delta and levels), and whether they differ from B16's primary row."""
    cfg = settings()
    level, delta = level_per_comparison(), float(cfg["margin"]["delta_pp"])
    fam_level = 1.0 - 2.0 * float(alpha()) / dsg.familywise_sides
    override = {("U", name): e.p_two_sided() if isinstance(e, con.Estimate) else 1.0 for name, e in ests.items()}
    _, outcome = _run_phi(dsg, primary, override)
    rejected = set(outcome.rejected)
    out = {}
    for name, e in ests.items():
        if not isinstance(e, con.Estimate):
            out[name] = {"computable": False, "reason": f"{NOT_COMPUTABLE}: {e}", "u_part_words": None,
                         "headline": None, "p_in_phi": 1.0, "rejected_in_phi": ("U", name) in rejected}
            continue
        u = labels.u_part(("U", name) in rejected, e.est, e.interval(level), e.interval(fam_level), delta)
        head = labels.headline(u, ("O", name) in rejected, ("L", name) in rejected)
        cell = f"{head['cell']} [{dsg.label_suffix}]" if dsg.label_suffix else head["cell"]
        words_differ = list(u.words) != primary[name]["u_part_words"]
        head_differs = head["word"] != primary[name]["headline"]
        out[name] = {"computable": True, "estimate": e.as_dict(), "interval_90": list(e.interval(level)),
                     "p_in_phi": e.p_two_sided(), "rejected_in_phi": ("U", name) in rejected,
                     "u_part": u.as_dict(), "u_part_words": list(u.words), "headline": head["word"],
                     "headline_cell": cell, "u_part_words_differ": words_differ, "headline_differs": head_differs,
                     "differs_from_primary": words_differ or head_differs}
    return out, outcome


# ----- G3(a) --------------------------------------------------------------------------------------------------------


def corner_table(plain: dict, g3: dict, arm: str) -> dict:
    """Plain U with ``arm``'s cells taken from the g3_unscored_unsafe table: one adverse G3(a) corner's table."""
    out = dict(plain)
    out.update({key: items for key, items in g3.items() if key[0] == arm})
    return out


def corners(inp, dsg, scale: float, floor: float, cfg: dict) -> dict:
    """{direction: ({contrast: Estimate or reason}, {contrast: fit record or None}, {contrast: the arm from G3})}:
    each contrast's adverse G3(a) corner in both directions (module doc), HB-C refitted on the contrast's cluster."""
    g3 = inp.variants.get(G3)
    out = {}
    for direction, role in CORNERS.items():
        ests, fit_recs, moved, cache = {}, {}, {}, {}
        for name, c, m in dsg.contrasts:
            arm = m if role == "repair" else c
            moved[name] = arm
            if g3 is None:
                ests[name], fit_recs[name] = f"the input holds no {G3} table", None
                continue
            cluster = dsg.cluster[c]
            if (cluster, arm) not in cache:              # P1-P3 share R's "against worse" table: one fit
                table = corner_table(inp.tables["U"], g3, arm)
                cache[(cluster, arm)] = (table, *cluster_fits(table, dsg, scale, floor, cfg, clusters=(cluster,)))
            table, fits, reasons = cache[(cluster, arm)]
            ests[name] = estimate(table, fits, reasons, dsg, name, c, m, scale, f"S-G G3a {direction.replace('_', ' ')}")
            fit_recs[name] = _fit_record(fits[cluster]) if cluster in fits else None
        out[direction] = (ests, fit_recs, moved)
    return out


def symmetric(b16_sg: dict, dsg) -> dict:
    """The built symmetric G3 table as B16 read it, under its label: B16's words copied by key."""
    block = b16_sg.get(G3)
    if not isinstance(block, dict):
        return {"label": SYMMETRIC_LABEL, "computed": False, "reason": f"B16's output holds no S-G {G3}"}
    per = {}
    for name, _, _ in dsg.contrasts:
        rec = block.get(name) or {}
        per[name] = {"u_part_words": rec.get("u_part_words"), "differs_from_primary": rec.get("differs_from_primary")}
    return {"label": SYMMETRIC_LABEL, "computed": True, "b16_key": f"sensitivities.S-G.{G3}", "contrasts": per}


# ----- the whole S-G reading ----------------------------------------------------------------------------------------


def sg(tables_doc: dict, counts_doc: dict, reading_doc: dict, tables_sha256: str, counts_sha256: str,
       reading_sha256: str) -> dict:
    """The S-G reading beside B16's output (module doc). Refuses only on a binding failure of its inputs."""
    inp = load_tables(tables_doc)
    counts = coh.check(counts_doc, inp, tables_sha256)
    primary, b16_sg = load_reading(reading_doc, inp, tables_sha256)
    dsg, cfg = design(inp.reading), settings()
    scale, floor = float(cfg["endpoints"]["U"]["scale"]), float(cfg["endpoints"]["U"]["floor"])
    x = {}
    for key, (n, u, _) in counts.items():
        shares = x_shares(n, u)
        if shares is not None:                     # a cell with no coherent answer has no value: it leaves the fit
            x[key] = shares
    fits, reasons = cluster_fits(x, dsg, scale, floor, cfg)
    ests = {name: estimate(x, fits, reasons, dsg, name, c, m, scale, "S-G coherent") for name, c, m in dsg.contrasts}
    per, outcome = reread(dsg, primary, ests)
    for name, c, m in dsg.contrasts:
        per[name].update({"comparator": c, "repair": m, "common_seeds": list(dsg.common_seeds(c, m)),
                          "g2_prompts_without_coherent_answer_per_seed_pair":
                              g2_pair_counts(counts, c, m, dsg.common_seeds(c, m))})
    coherent = {"computed": True, "arms": arm_values(counts, dsg),
                "fits": {cl: _fit_record(f) for cl, f in fits.items()}, "fits_not_computable": reasons,
                "contrasts": per, "phi": _phi_record(outcome),
                "headline": {name: rec["headline"] if rec["computable"] else NOT_COMPUTABLE
                             for name, rec in per.items()}}
    g3a = {"rule": "per contrast (c, m): 'against better' takes the repair m's cells from g3_unscored_unsafe, "
                   "'against worse' the comparator c's (a0 in P4 included); every other arm plain U; HB-C refitted "
                   "on the contrast's cluster; each direction's Phi run takes every contrast's own corner p-value"}
    for direction, (c_ests, fit_recs, moved) in corners(inp, dsg, scale, floor, cfg).items():
        d_per, d_outcome = reread(dsg, primary, c_ests)
        for name in d_per:
            d_per[name].update({"arm_from_g3": moved[name], "fit": fit_recs[name]})
        g3a[direction] = {"contrasts": d_per, "phi": _phi_record(d_outcome)}
    part = {name: [] for name, _, _ in dsg.contrasts}
    for key, block in (("coherent", per), ("against_better", g3a["against_better"]["contrasts"]),
                       ("against_worse", g3a["against_worse"]["contrasts"])):
        for name, rec in block.items():
            if not rec["computable"]:
                part[name].append({"code": CODES[key], "not_computable": rec["reason"]})
            elif rec["differs_from_primary"]:
                part[name].append({"code": CODES[key], "u_part_words": rec["u_part_words"],
                                   "headline_word": rec["headline"]})
    level = level_per_comparison()
    here = Path(__file__).resolve().parent
    out = {"kind": KIND, "version": 1, "reading": inp.reading, "label_suffix": dsg.label_suffix,
           "provenance": {"tables_sha256": tables_sha256, "counts_sha256": counts_sha256,
                          "reading_sha256": reading_sha256, "b16_settings_sha256": SETTINGS_SHA256,
                          "modules": {p: sha256_bytes((here / p).read_bytes())
                                      for p in ("coherent.py", "sg_coherent.py")},
                          "b16_modules": module_hashes(), "python": platform.python_version(), "numpy": np.__version__},
           "rule": list(RULE), "readings": dict(READINGS),
           "model": {"scale": scale, "floor_pp2": floor, "interval_level": level,
                     "familywise_level": 1.0 - 2.0 * float(alpha()) / dsg.familywise_sides,
                     "delta_pp": float(cfg["margin"]["delta_pp"]),
                     "x": "x_p = V + 100 (u_p - V/100 n_p) / N-bar on all 200 prompts; its prompt mean is V",
                     "fits": "HB-C refitted per cluster on the cells with a value (sensitivities.fit_clusters, pinned "
                             "settings); contrasts by contrast.contrast_fit, or contrast.contrast_paired for a pair "
                             "that lost a seed"},
           "primary": {name: {"u_part_words": rec["u_part_words"], "headline": rec["headline"]}
                       for name, rec in primary.items()},
           "coherent": coherent, "g3a": g3a, "g3_unscored_symmetric": symmetric(b16_sg, dsg),
           "sensitivity_part": part}
    return _strip(out)


# ----- the command line ---------------------------------------------------------------------------------------------


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m scripts.stage1_s1.reading_input.sg_coherent",
                                description="S-G's coherent-only U and adverse G3(a) corners beside B16's output (D-5)")
    p.add_argument("--tables", required=True, type=Path)
    p.add_argument("--counts", required=True, type=Path)
    p.add_argument("--reading", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args(argv)
    try:
        if args.out.exists():
            raise Refusal(f"{args.out.name} exists; the S-G reading never overwrites")
        data = {k: getattr(args, k).read_bytes() for k in ("tables", "counts", "reading")}
        out = sg(*(strict_json(data[k]) for k in ("tables", "counts", "reading")),
                 *(sha256_bytes(data[k]) for k in ("tables", "counts", "reading")))
        text = canonical_json(out)
        try:
            with open(args.out, "xb") as handle:
                handle.write(text)
        except FileExistsError:
            raise Refusal(f"{args.out.name} exists; the S-G reading never overwrites") from None
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - any other error may carry a value in its text: print its type only
        print(f"REFUSED: an unexpected {type(exc).__name__} (its message is withheld: it may hold a value)",
              file=sys.stderr)
        return 2
    print(f"wrote {args.out} sha256 {sha256_bytes(text)}")
    print("S-G coherent headline: " + "; ".join(f"{k} {w}" for k, w in out["coherent"]["headline"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
