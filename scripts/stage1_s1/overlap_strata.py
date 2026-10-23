"""B14, part 2: the sealed similarity strata and the overlap-control report (RS B14; PLAN-S:172; stage-1
pre-registration DRAFT revision 2, section 9.4, with S-25 / CONS LS-19; Mac, $0, standard library only).

    python -B scripts/stage1_s1/overlap_strata.py strata --similarity FILE --similarity-sha256 HEX --out DIR
    python -B scripts/stage1_s1/overlap_strata.py report --strata FILE --inputs FILE --out DIR [--data-root D]

**strata.** Reads the pod's ``similarity.json`` only by its SHA-256 (made under the pinned similarity settings,
``similarity_settings_sha256``) and splits, per add set, the n evaluation prompts by S(e; A), the prompt's highest
similarity to the add set: k = floor(n / 2), b = the (k + 1)-th smallest S; the lower-similarity half is
{S < b} and the higher-similarity half is {S >= b}. Prompts whose S equals b (exact float equality) all go to the
higher half, so max(S on the lower half) < min(S on the higher half) always holds; with ties at b the lower half
holds fewer than k prompts and the record counts the ties. The rule draws no random number. Output ``strata.json``
(prompt ids, numbers and hashes). It is sealed: written once, its SHA-256 recorded, before any add-arm outcome is
read.

**report.** Reads ``strata.json`` only by the SHA-256 that the inputs file names, and the sealed evaluation units of
a0 and of each add arm of one pinned seed plan (``inputs``: kind "stage1 overlap report inputs", version 1,
``strata_sha256``, ``seed_plan``, ``units``: {"a0" or an add set's name: {seed: {path, complete_sha256,
job_sha256}}}). A seed plan names its common seeds and the add arms that run under it (plan B runs S1 and S4, not
S3). The strata record must hold every add set of the plan, and the inputs must name units of a0 and of exactly the
plan's add sets at exactly the plan's seeds; a strata add set outside the plan is listed in the output, not reported.
Each unit is checked by ``limits_common.check_unit`` (the frozen sealed check, the pins, job.json's
arm, seed, checkpoint and identity fields, the refused recipes; the code identity must be an allowed one); an add
arm's job.json must name ``edit-<the add set's edit SHA-256>``. Of each unit only ``guard_samples.jsonl`` (reduced at
once to prompt_id, sample_index, valid, safety) and ``summary.json`` (its harm sampled counts, which must equal the
records') are read. Per add arm m and half h (all prompts, lower, higher): Lambda_h = the mean over the common seeds
of U_h(a0, j) - U_h(m, j); its variance by the per-contrast paired form (HB's two-arm reduction: the seed part from
the J paired differences, the prompt part from the J x P table, Satterthwaite df); the 90% interval at the real df.
A Satterthwaite df so small that the t quantile is not finite (below about 0.07; it needs MS_P just above MS_E and
nearly equal seed differences) makes that half "not computable": its interval is unbounded, so it contains 0.
**Holds** (S-25): the lower half's Lambda has the same sign as the all-prompt Lambda and its 90% interval excludes
0; else the text is "not shown on the less similar half". The paired form, its intervals and this verdict are printed
as the **S-p sensitivity** only (addendum section 11 point 11; LN-37): each verdict carries the label "S-p
sensitivity", and the report names section 9.4's primary model of the halves, HB-C, which the stage-1 reading (B16)
computes from each add set's ``cells_u_pp``. Output ``overlap_report.json`` (also the per-cell U of each half, the
input that B16 needs to read the halves under the primary model).

Messages and outputs carry ids, counts, numbers and hashes only. Exit 0: written; exit 2: refused, nothing written.
"""

from __future__ import annotations

import argparse
import math
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1.limits import limits_common as lc  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "overlap_strata.json"
SETTINGS_SHA256 = "b98d012e9cc92dbe847f92d9ccda54cf2ee22964dbd941e5aa8bd672bff19f87"
SETTINGS_NAME = "overlap_strata"
STRATA_KIND = "stage1 overlap strata"
REPORT_KIND = "stage1 overlap report"
INPUTS_KIND = "stage1 overlap report inputs"
STRATA_FILE = "strata.json"
REPORT_FILE = "overlap_report.json"
HALVES = ("all", "lower", "higher")
COMPARATOR = "a0"
S_P = ("S-p", "sensitivity", "S-p sensitivity")     # addendum 11.11 / LN-37: the paired form's printed role


# ----- Student t at a real df (regularized incomplete beta, Lentz's continued fraction) -----------------------------


class QuantileOutOfRange(s1.Refusal):
    """The t quantile is above the search bound (a df below about 0.07): the interval is unbounded."""


def _beta_cf(a: float, b: float, x: float) -> float:
    tiny, eps = 1e-300, 1e-15
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 1000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            return h
    raise s1.Refusal("the incomplete beta continued fraction did not converge")


def beta_inc(a: float, b: float, x: float) -> float:
    """The regularized incomplete beta function I_x(a, b) for a, b > 0 and 0 <= x <= 1."""
    if not (a > 0 and b > 0 and 0.0 <= x <= 1.0):
        raise s1.Refusal("beta_inc takes a, b > 0 and 0 <= x <= 1")
    if x in (0.0, 1.0):
        return x
    log_front = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(log_front) * _beta_cf(a, b, x) / a
    return 1.0 - math.exp(log_front) * _beta_cf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: float) -> float:
    """The Student t CDF at a real df > 0."""
    if not (isinstance(df, (int, float)) and not isinstance(df, bool) and math.isfinite(df) and df > 0):
        raise s1.Refusal("the t distribution needs a finite df > 0")
    tail = 0.5 * beta_inc(df / 2.0, 0.5, df / (df + t * t))
    return 1.0 - tail if t > 0 else tail


def t_quantile(p: float, df: float) -> float:
    """The Student t quantile for 0.5 < p < 1 at a real df > 0, by bisection on t_cdf (to about 1e-12)."""
    if not 0.5 < p < 1:
        raise s1.Refusal("t_quantile takes 0.5 < p < 1")
    low, high = 0.0, 1.0
    while t_cdf(high, df) < p:
        high *= 2.0
        if high > 1e12:
            raise QuantileOutOfRange("the t quantile is out of range")
    for _ in range(400):
        mid = (low + high) / 2
        if t_cdf(mid, df) < p:
            low = mid
        else:
            high = mid
        if high - low < 1e-12 * max(1.0, high):
            break
    return (low + high) / 2


# ----- the split ------------------------------------------------------------------------------------------------------


def split_halves(values: Mapping[str, Any]) -> dict:
    """The lower- and higher-similarity halves of prompt id -> S (the rule in the module docstring)."""
    checked = s1.check_scores(values)
    n = len(checked)
    if n < 2:
        raise s1.Refusal("a split needs at least 2 prompts")
    k = n // 2
    boundary = sorted(checked.values())[k]
    lower = sorted(pid for pid, v in checked.items() if v < boundary)
    higher = sorted(pid for pid, v in checked.items() if v >= boundary)
    if lower and max(checked[p] for p in lower) >= min(checked[p] for p in higher):
        raise s1.Refusal("internal: the halves overlap in S")
    return {"n": n, "k": k, "boundary": boundary, "ties_at_boundary": sum(v == boundary for v in checked.values()),
            "lower_n": len(lower), "higher_n": len(higher),
            "lower_max": max(checked[p] for p in lower) if lower else None, "higher_min": boundary,
            "lower": lower, "higher": higher}


def check_content(doc: Mapping[str, Any]) -> None:
    """The settings' own content (s1common.check_settings checks kind, name, registry entries and engine X)."""
    lc.hex64(doc.get("similarity_settings_sha256"), "settings: similarity_settings_sha256")
    if doc.get("label_entries") != {}:
        raise s1.Refusal("settings: this script draws nothing, so label_entries must be empty")
    if (doc.get("split") or {}).get("boundary_ties") != "higher":
        raise s1.Refusal("settings: boundary ties go to the higher half")
    rep = doc.get("report") or {}
    minimum = rep.get("minimum") or {}
    if not all(isinstance(minimum.get(k), int) and not isinstance(minimum.get(k), bool) and minimum[k] >= 2
               for k in ("seeds", "prompts")):
        raise s1.Refusal("settings: the minimum seeds and prompts are integers of at least 2")
    if rep.get("comparator") != COMPARATOR or rep.get("interval") != 0.9:
        raise s1.Refusal("settings: the comparator is a0 and the interval is the 90% interval")
    if not isinstance(rep.get("checkpoint"), str) or not isinstance(rep.get("samples_per_prompt"), int) \
            or isinstance(rep.get("samples_per_prompt"), bool) or rep["samples_per_prompt"] < 1:
        raise s1.Refusal("settings: the checkpoint or the samples per prompt are missing")
    texts = rep.get("texts") or {}
    if not all(isinstance(texts.get(k), str) and texts[k] for k in ("holds", "not_shown")):
        raise s1.Refusal("settings: the two report texts are missing")
    s_p = rep.get("s_p") or {}
    if (s_p.get("name"), s_p.get("role"), s_p.get("label")) != S_P or not isinstance(s_p.get("rule"), str) \
            or not s_p["rule"]:
        raise s1.Refusal("settings: the paired form is printed as the S-p sensitivity (addendum 11.11; LN-37)")
    if not isinstance(rep.get("primary_model"), str) or "HB-C" not in rep["primary_model"] \
            or "cells_u_pp" not in rep["primary_model"]:
        raise s1.Refusal("settings: the primary model of the halves is HB-C from cells_u_pp (addendum 11.11)")
    plans = rep.get("seed_plans")
    if not isinstance(plans, dict) or not plans:
        raise s1.Refusal("settings: no seed plan")
    for name, plan in plans.items():
        seeds = plan.get("seeds") if isinstance(plan, dict) else None
        sets = plan.get("add_sets") if isinstance(plan, dict) else None
        if not (isinstance(seeds, list) and len(seeds) >= rep["minimum"]["seeds"]
                and all(isinstance(j, int) and not isinstance(j, bool) for j in seeds) and seeds == sorted(set(seeds))):
            raise s1.Refusal(f"settings: seed plan {name} is not a sorted list of distinct seeds")
        if not (isinstance(sets, list) and sets and all(isinstance(n, str) and n and n != COMPARATOR for n in sets)
                and sets == sorted(set(sets))):
            raise s1.Refusal(f"settings: seed plan {name} names no sorted list of distinct add sets")
    for code in rep.get("allowed_code_sha256") or ():
        lc.hex64(code, "settings: an allowed code identity")
    if not rep.get("allowed_code_sha256"):
        raise s1.Refusal("settings: no allowed code identity")


# ----- strata ---------------------------------------------------------------------------------------------------------


def _similarity_record(data: bytes, digest: str, settings: Mapping[str, Any]) -> dict:
    lc.hex64(digest, "the similarity record's SHA-256")
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"the similarity record hashes to {sha256_bytes(data)}, not {digest}")
    doc = s1.strict_json(data)
    want = settings["similarity_record"]
    if not isinstance(doc, dict) or doc.get("kind") != want["kind"] or doc.get("version") != want["version"]:
        raise s1.Refusal("the file is not a version-1 overlap similarity record")
    made_under = (doc.get("provenance") or {}).get("settings_sha256")
    if made_under != settings["similarity_settings_sha256"]:
        raise s1.Refusal(f"the similarity record was made under settings {made_under}, "
                         f"not the pinned {settings['similarity_settings_sha256']}")
    prompt_ids = (doc.get("eval") or {}).get("prompt_ids")
    if not (isinstance(prompt_ids, list) and prompt_ids == sorted(set(prompt_ids)) and len(prompt_ids) >= 2):
        raise s1.Refusal("the similarity record's prompt ids are not a sorted list of distinct ids")
    sets = doc.get("add_sets")
    if not isinstance(sets, dict) or not sets:
        raise s1.Refusal("the similarity record holds no add set")
    for name, block in sets.items():
        per = block.get("per_prompt") if isinstance(block, dict) else None
        if not isinstance(per, dict) or sorted(per) != prompt_ids:
            raise s1.Refusal(f"add set {name}: the per-prompt values do not cover exactly the record's prompts")
        row_ids = set(block.get("row_ids") or ())
        for pid, value in per.items():
            s_max = value.get("s_max") if isinstance(value, dict) else None
            if isinstance(s_max, bool) or not isinstance(s_max, (int, float)) or not math.isfinite(s_max) \
                    or abs(s_max) > 1 + 1e-9 or value.get("nearest") not in row_ids:
                raise s1.Refusal(f"add set {name}: prompt {pid} has no finite cosine in [-1, 1] or no nearest row")
        lc.hex64(block.get("edit_sha256"), f"add set {name}: edit_sha256")
        if block.get("arm") != "edit-" + block["edit_sha256"]:
            raise s1.Refusal(f"add set {name}: its arm is not edit-<its edit SHA-256>")
    return doc


def strata(similarity_bytes: bytes, similarity_sha256: str, settings: Mapping[str, Any], settings_sha256: str) -> bytes:
    """strata.json's bytes from the similarity record (read by its SHA-256)."""
    check_content(settings)
    doc = _similarity_record(similarity_bytes, similarity_sha256, settings)
    block = {}
    for name, s in sorted(doc["add_sets"].items()):
        halves = split_halves({pid: v["s_max"] for pid, v in s["per_prompt"].items()})
        block[name] = {"edit_sha256": s["edit_sha256"], "arm": s["arm"], **halves}
    out = {"kind": STRATA_KIND, "version": 1, "requirement": settings["requirement"], "rule": settings["split"],
           "similarity": {"sha256": similarity_sha256, "settings_sha256": settings["similarity_settings_sha256"],
                          "hidden_state_index": doc["model"]["hidden_state_index"], "read": doc["model"]["read"]},
           "prompt_ids": doc["eval"]["prompt_ids"], "add_sets": block,
           "provenance": s1.provenance(Path(__file__), settings_sha256, {"similarity.json": similarity_sha256}, {})}
    return canonical_json(out)


# ----- the evaluation units ---------------------------------------------------------------------------------------------


def _strata_record(data: bytes, digest: str, settings_sha256: str) -> dict:
    lc.hex64(digest, "the strata record's SHA-256")
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"the strata record hashes to {sha256_bytes(data)}, not the sealed {digest}")
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != STRATA_KIND or doc.get("version") != 1:
        raise s1.Refusal("the file is not a version-1 overlap strata record")
    if (doc.get("provenance") or {}).get("settings_sha256") != settings_sha256:
        raise s1.Refusal("the strata record was made under other overlap_strata settings")
    prompts = doc.get("prompt_ids")
    for name, block in (doc.get("add_sets") or {}).items():
        lower, higher = block.get("lower"), block.get("higher")
        if not (isinstance(lower, list) and isinstance(higher, list)) or sorted(lower + higher) != prompts \
                or set(lower) & set(higher):
            raise s1.Refusal(f"add set {name}: the halves do not partition the strata's prompts")
    if not doc.get("add_sets"):
        raise s1.Refusal("the strata record holds no add set")
    return doc


def unit_cells(unit: lc.CheckedUnit, prompts: Sequence[str], samples: int) -> tuple[dict, dict]:
    """(prompt id -> (Unsafe count, answers), the two file SHA-256) of one checked unit's sampled harm answers."""
    data, gs_sha = lc.unit_file(unit, "guard_samples.jsonl")
    records = lc.fields_of(data, f"{unit.name} guard_samples.jsonl", ("prompt_id", "sample_index", "valid", "safety"))
    del data
    seen: dict[str, set] = {}
    cells: dict[str, list[int]] = {}
    for r in records:
        pid, index = r["prompt_id"], r["sample_index"]
        if not isinstance(pid, str) or isinstance(index, bool) or not isinstance(index, int):
            raise s1.Refusal(f"unit {unit.name}: a sampled guard record has no prompt id or sample index")
        if index in seen.setdefault(pid, set()):
            raise s1.Refusal(f"unit {unit.name}: prompt {pid} repeats sample {index}")
        seen[pid].add(index)
        cell = cells.setdefault(pid, [0, 0])
        cell[0] += bool(r["valid"]) and r["safety"] == "Unsafe"        # the engine's and the frozen reading's rule
        cell[1] += 1
    if sorted(cells) != list(prompts):
        raise s1.Refusal(f"unit {unit.name}: its sampled answers cover {len(cells)} prompts, not the strata's "
                         f"{len(prompts)}")
    bad = [pid for pid, indices in seen.items() if indices != set(range(samples))]
    if bad:
        raise s1.Refusal(f"unit {unit.name}: {len(bad)} prompts do not hold samples 0..{samples - 1}")
    sdata, s_sha = lc.unit_file(unit, "summary.json")
    sampled = ((s1.strict_json(sdata).get("harm") or {}).get("sampled") or {})
    if sampled.get("answers") != sum(c[1] for c in cells.values()) or \
            sampled.get("unsafe") != sum(c[0] for c in cells.values()):
        raise s1.Refusal(f"unit {unit.name}: the sampled guard records disagree with summary.json's harm counts")
    return {pid: (c[0], c[1]) for pid, c in sorted(cells.items())}, {"guard_samples.jsonl": gs_sha,
                                                                      "summary.json": s_sha}


def read_units(inputs: Mapping[str, Any], strata_doc: Mapping[str, Any], settings: Mapping[str, Any],
               data_root: Path) -> tuple[list[int], list[str], dict, dict]:
    """(seeds, the plan's add sets, cells[arm name][seed] = {pid: (unsafe, n)}, unit records) for a0 and each add set
    of the seed plan. The strata record must hold every add set of the plan."""
    rep = settings["report"]
    plans = rep["seed_plans"]
    if not isinstance(inputs.get("seed_plan"), str) or inputs.get("seed_plan") not in plans:
        raise s1.Refusal(f"the inputs name seed plan {inputs.get('seed_plan')!r}, not one of {sorted(plans)}")
    plan = plans[inputs["seed_plan"]]
    seeds, plan_sets = list(plan["seeds"]), list(plan["add_sets"])
    missing = [name for name in plan_sets if name not in strata_doc["add_sets"]]
    if missing:
        raise s1.Refusal(f"seed plan {inputs['seed_plan']} needs add sets {missing}, which the strata record does not "
                         f"hold")
    units = inputs.get("units")
    names = [COMPARATOR] + plan_sets
    if not isinstance(units, dict) or sorted(units) != sorted(names):
        raise s1.Refusal(f"the inputs must name units for exactly {names}")
    reader = lc.frozen_reader(rep["frozen_reader"])
    rules = {"path_pattern": rep["path_pattern"], "require_pins": True, "identity": rep["identity"],
             "refused_recipes": rep["refused_recipes"]}
    prompts = strata_doc["prompt_ids"]
    cells: dict[str, dict[int, dict]] = {}
    records: dict[str, dict[str, dict]] = {}
    for name in names:
        given = units[name]
        if not isinstance(given, dict) or sorted(given) != sorted(str(j) for j in seeds):
            raise s1.Refusal(f"arm {name}: the inputs name seeds {sorted(given) if isinstance(given, dict) else None}, "
                             f"the seed plan {inputs['seed_plan']} needs {seeds}")
        arm = COMPARATOR if name == COMPARATOR else strata_doc["add_sets"][name]["arm"]
        for seed in seeds:
            entry = given[str(seed)]
            if not isinstance(entry, dict):
                raise s1.Refusal(f"arm {name} seed {seed}: the unit entry is not an object")
            spec = {"path": entry.get("path"), "complete_sha256": entry.get("complete_sha256"),
                    "job_sha256": entry.get("job_sha256"), "arm": arm, "seed": seed, "checkpoint": rep["checkpoint"]}
            unit = lc.check_unit(data_root, f"{name}@{seed}", spec, rules, reader)
            code = unit.job.get("code_sha256")
            if code not in rep["allowed_code_sha256"]:
                raise s1.Refusal(f"unit {name}@{seed}: its code identity {code} is not an allowed one")
            cell, digests = unit_cells(unit, prompts, rep["samples_per_prompt"])
            cells.setdefault(name, {})[seed] = cell
            records.setdefault(name, {})[str(seed)] = {
                "path": unit.path, "arm": arm, "complete_sha256": unit.complete_sha256, "job_sha256": unit.job_sha256,
                "code_sha256": code, **{f"{k}_sha256".replace(".", "_"): v for k, v in digests.items()}}
    return seeds, plan_sets, cells, records


# ----- the contrast ------------------------------------------------------------------------------------------------------


def cell_u(cell: Mapping[str, tuple[int, int]], prompts: Sequence[str]) -> float:
    """U on a set of prompts: 100 x the mean over them of the per-prompt Unsafe share, in pp (exact, then a float)."""
    return float(100 * sum(Fraction(*cell[p]) for p in prompts) / len(prompts))


def contrast(comparator: Mapping[int, Mapping[str, tuple[int, int]]], arm: Mapping[int, Mapping[str, tuple[int, int]]],
             seeds: Sequence[int], prompts: Sequence[str], minimum: Mapping[str, int]) -> dict:
    """Lambda = mean_j [U(c, j) - U(m, j)] on these prompts, with the per-contrast paired variance (settings
    report.variance_model) and the 90% interval. Every share is a ratio of counts, so Lambda, the two variance parts,
    MS_P, MS_E, q and the df are computed exactly (fractions); only the square root and the t quantile are floats."""
    J, P = len(seeds), len(prompts)
    out: dict[str, Any] = {"seeds": J, "prompts": P}
    if J < minimum["seeds"] or P < minimum["prompts"]:
        return {**out, "computable": False, "reason": f"needs at least {minimum['seeds']} seeds and "
                                                      f"{minimum['prompts']} prompts"}
    table = [[Fraction(*comparator[j][p]) - Fraction(*arm[j][p]) for p in prompts] for j in seeds]
    rows = [sum(r) / P for r in table]
    d = [100 * r for r in rows]
    lam = sum(d) / J
    s2 = sum((x - lam) ** 2 for x in d) / (J - 1)
    v_seed = s2 / J
    grand = sum(rows) / J
    cols = [sum(table[j][p] for j in range(J)) / J for p in range(P)]
    ms_p = J * sum((c - grand) ** 2 for c in cols) / (P - 1)
    ms_e = sum((table[j][p] - rows[j] - cols[p] + grand) ** 2
               for j in range(J) for p in range(P)) / ((P - 1) * (J - 1))
    scale = Fraction(10 ** 4, P * J)
    v_prompt = max(Fraction(0), ms_p - ms_e) * scale
    q = ((ms_p * scale) ** 2 / (P - 1) + (ms_e * scale) ** 2 / ((P - 1) * (J - 1))) if ms_p > ms_e else Fraction(0)
    v = v_seed + v_prompt
    out.update(estimate=float(lam), seed_differences=[float(x) for x in d], v_seed=float(v_seed), df_seed=J - 1,
               ms_p=float(ms_p), ms_e=float(ms_e), v_prompt=float(v_prompt), q=float(q), variance=float(v))
    if v == 0:
        return {**out, "computable": False, "reason": "the variance is 0, so no interval exists"}
    df = float(v * v / (v_seed * v_seed / (J - 1) + q))
    se = math.sqrt(v)
    try:
        t = t_quantile(0.95, df)
    except QuantileOutOfRange:
        return {**out, "computable": False, "df": df,
                "reason": "the Satterthwaite df is too small for a finite t quantile, so the interval is unbounded"}
    return {**out, "computable": True, "df": df, "se": se, "t": t, "lower": float(lam) - t * se,
            "upper": float(lam) + t * se}


def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


def verdict(all_prompts: Mapping[str, Any], lower: Mapping[str, Any], texts: Mapping[str, str]) -> dict:
    """S-25: the lower half's Lambda has the all-prompt Lambda's sign (never 0) and its 90% interval excludes 0."""
    if "estimate" not in all_prompts:
        return {"holds": False, "text": texts["not_shown"], "reason": "the all-prompt contrast has no estimate"}
    sign_all = _sign(all_prompts["estimate"])
    if not lower.get("computable"):
        return {"holds": False, "text": texts["not_shown"],
                "reason": f"the lower-similarity half is not computable ({lower.get('reason')})"}
    same = sign_all != 0 and _sign(lower["estimate"]) == sign_all
    excludes = lower["lower"] > 0 or lower["upper"] < 0
    holds = same and excludes
    reason = "same sign and the 90% interval excludes 0" if holds else (
        "the sign differs from the all-prompt contrast (or that sign is 0)" if not same else
        "the 90% interval contains 0")
    return {"holds": holds, "text": texts["holds"] if holds else texts["not_shown"], "reason": reason,
            "sign_all": sign_all, "sign_lower": _sign(lower["estimate"])}


def report(strata_bytes: bytes, inputs: Mapping[str, Any], settings: Mapping[str, Any], settings_sha256: str,
           data_root: Path) -> bytes:
    """overlap_report.json's bytes."""
    check_content(settings)
    if not isinstance(inputs, dict) or inputs.get("kind") != INPUTS_KIND or inputs.get("version") != 1:
        raise s1.Refusal("the inputs file is not a version-1 overlap report inputs file")
    strata_sha = lc.hex64(inputs.get("strata_sha256"), "the inputs' strata_sha256")
    doc = _strata_record(strata_bytes, strata_sha, settings_sha256)
    seeds, plan_sets, cells, units = read_units(inputs, doc, settings, Path(data_root))
    rep = settings["report"]
    out_sets = {}
    for name in plan_sets:
        block = doc["add_sets"][name]
        halves = {"all": doc["prompt_ids"], "lower": block["lower"], "higher": block["higher"]}
        results = {h: contrast(cells[COMPARATOR], cells[name], seeds, prompts, rep["minimum"])
                   for h, prompts in halves.items()}
        table = {arm: {str(j): {h: (cell_u(cells[arm][j], prompts) if prompts else None)
                                for h, prompts in halves.items()} for j in seeds} for arm in (COMPARATOR, name)}
        out_sets[name] = {"arm": block["arm"], "edit_sha256": block["edit_sha256"],
                          "half_sizes": {h: len(p) for h, p in halves.items()},
                          "ties_at_boundary": block["ties_at_boundary"], "cells_u_pp": table,
                          "contrasts": results,
                          "verdict": {**verdict(results["all"], results["lower"], rep["texts"]),
                                      "role": rep["s_p"]["label"]}}
    inputs_digests = {"strata.json": strata_sha}
    for name, per_seed in units.items():
        for seed, record in per_seed.items():
            inputs_digests[f"{name}@{seed}/COMPLETE.json"] = record["complete_sha256"]
            inputs_digests[f"{name}@{seed}/job.json"] = record["job_sha256"]
            inputs_digests[f"{name}@{seed}/guard_samples.jsonl"] = record["guard_samples_jsonl_sha256"]
            inputs_digests[f"{name}@{seed}/summary.json"] = record["summary_json_sha256"]
    out = {"kind": REPORT_KIND, "version": 1, "requirement": settings["requirement"],
           "outcome": rep["outcome"], "contrast": rep["contrast"], "variance_model": rep["variance_model"],
           "interval": rep["interval"], "holds_rule": rep["holds"], "s_p": rep["s_p"],
           "primary_model": rep["primary_model"], "seed_plan": inputs["seed_plan"], "seeds": seeds,
           "strata_sha256": strata_sha, "units": units, "add_sets": out_sets,
           "strata_add_sets_not_in_plan": sorted(set(doc["add_sets"]) - set(plan_sets)),
           "provenance": s1.provenance(Path(__file__), settings_sha256, inputs_digests, {})}
    return canonical_json(out)


# ----- the command line --------------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("strata", help="split the evaluation prompts per add set (Mac, $0)")
    a.add_argument("--similarity", type=Path, required=True)
    a.add_argument("--similarity-sha256", required=True)
    a.add_argument("--out", type=Path, required=True, help="output folder (absent or empty)")
    a.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    b = sub.add_parser("report", help="the add effect on each half (Mac, $0)")
    b.add_argument("--strata", type=Path, required=True)
    b.add_argument("--inputs", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True, help="output folder (absent or empty)")
    b.add_argument("--data-root", type=Path, default=lc.DEFAULT_DATA_ROOT)
    b.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        if args.command == "strata":
            data = strata(args.similarity.read_bytes(), args.similarity_sha256, settings, digest)
            name = STRATA_FILE
        else:
            inputs = s1.strict_json(args.inputs.read_bytes())
            data = report(args.strata.read_bytes(), inputs, settings, digest, args.data_root)
            name = REPORT_FILE
        written = s1.write_new_files(args.out.resolve(), {name: data})
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)",
              file=sys.stderr)
        return 2
    doc = s1.strict_json(data)
    print(f"wrote {name} into {args.out} ({written[name]})")
    for set_name, block in doc["add_sets"].items():
        if args.command == "strata":
            print(f"  {set_name}: lower {block['lower_n']}, higher {block['higher_n']}, "
                  f"ties at the boundary {block['ties_at_boundary']}")
        else:
            print(f"  {set_name}: {block['verdict']['role']}: {block['verdict']['text']} ({block['verdict']['reason']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
