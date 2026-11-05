"""Derive ``measured-basis-78b.json`` for the 7-8B cap rule (KCR §3-§4; the lead's ruling 11, KD1 and KD9).

    PY -I -B derive_78b_basis.py --root /abs/path/to/attribution/tmp --out measured-basis-78b.json
    PY -I -B derive_78b_basis.py --root ROOT --out OUT --extra-unit FAMILY:KIT_FOLDER ...   (KD9: a re-measure)

The basis is the text-free timing record of the 17 measured 7-8B units (KCR:9 names them: nine OLMo-2-7B kits and
eight Llama-3.1-8B kits under ``tmp/family-probe-sp-*``). The script reads each kit's records read-only, by absolute
path, and opens ONLY these file names (KCR:135; the plan's T2 privacy rule):

    hosts/<host>/{verification.json, finished.json, create-intent.json, create-result.json}
    retrieved/<host>/tree/{BOOTSTRAP-READY.json, PREFLIGHT-DONE.json, JOB-DONE.json}
    retrieved/<host>/tree/round1/<unit>/{ledger.jsonl, progress.jsonl}

It never opens ``eval/``, generations, samples, prompts, ``ssh/``, ``selector.jsonl`` or ``hidden/`` (``open_record``
refuses any other file name and any path with a forbidden part). Its output holds numbers, booleans, hashes, stage
names, host names and UTC stamps: no string longer than a hash (KCR test 15). The output is deterministic (no clock
value inside it), so ``rules_78b.py`` can pin its SHA-256; the clock is printed to stdout only.

What each unit record holds (seconds unless named otherwise): the outer job time (``finished.json``
``outer_elapsed_min`` x 60), the pod overhead ((create -> confirmed stop) - the outer job), the preflight's speed
fields (``training_s``, ``ms_per_step_full``, ``untuned_projected_s``, the memory peaks and allocator retries), the
ledger's stage seconds (training per step, the early stages, the scoring stages, generation and sampling), the time
outside the stages (outer - the sum of every ledger stage of every unit the job ran; KCR §14 correction 1), and from
``progress.jsonl`` each generation batch's seconds, rows and capped count (the first greedy batch apart, KCR:64).

KD9 (a re-measure on the first engine-Y pod): ``--extra-unit FAMILY:KIT_FOLDER`` adds a unit from a kit folder of the
same layout; the output then lists every engine identity it saw per family, and the lead records the step, re-pins
the basis hash in ``rules_78b.py`` and re-runs the tests (RULES-78B.md).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import re
import sys

FAMILIES = ("olmo2-7b", "llama31-8b")
# KCR:9: the 17 measured units (kit folder names under tmp/).
UNIT_KITS = {
    "olmo2-7b": ("family-probe-sp-olmo2-7b-b-a0", "family-probe-sp-olmo2-7b-b-seed1102",
                 "family-probe-sp-olmo2-7b-b-seed1103", "family-probe-sp-olmo2-7b-b5e5-seed1101",
                 "family-probe-sp-olmo2-7b-b5e5-seed1102", "family-probe-sp-olmo2-7b-b5e5-seed1103",
                 "family-probe-sp-olmo2-7b-g-seed1101", "family-probe-sp-olmo2-7b-g-seed1102",
                 "family-probe-sp-olmo2-7b-g-seed1103"),
    "llama31-8b": ("family-probe-sp-llama31-8b-b-a0", "family-probe-sp-llama31-8b-b-seed1102",
                   "family-probe-sp-llama31-8b-b-seed1103", "family-probe-sp-llama31-8b-b5e5-1101",
                   "family-probe-sp-llama31-8b-b5e5-seed1102", "family-probe-sp-llama31-8b-g-seed1101",
                   "family-probe-sp-llama31-8b-g-seed1102", "family-probe-sp-llama31-8b-g-seed1103"),
}
ALLOWED_NAMES = frozenset({"verification.json", "finished.json", "create-intent.json", "create-result.json",
                           "BOOTSTRAP-READY.json", "PREFLIGHT-DONE.json", "JOB-DONE.json", "ledger.jsonl",
                           "progress.jsonl"})
# A-V6: each allowed name is read from one place only (the kit layout in the docstring): "host" = hosts/<host>/NAME,
# "tree" = retrieved/<host>/tree/NAME, "unit" = retrieved/<host>/tree/round1/<unit>/NAME. An allowed name anywhere
# else (for example tree/cuda-preflight-1/verification.json) refuses before any open; so does any other create-*.json.
PLACE_OF = {"verification.json": "host", "finished.json": "host", "create-intent.json": "host",
            "create-result.json": "host", "BOOTSTRAP-READY.json": "tree", "PREFLIGHT-DONE.json": "tree",
            "JOB-DONE.json": "tree", "ledger.jsonl": "unit", "progress.jsonl": "unit"}
FORBIDDEN_PARTS = frozenset({"eval", "generations", "samples", "prompts", "ssh", "hidden", "selector.jsonl",
                             "states", "judges", "seals", "units"})
EARLY_STAGES = ("load_policy", "tokenize", "memory_preflight", "init_state")
SCORING_STAGES = ("load_guard", "query_loss", "arc_utility", "guard", "guard_samples", "harm_scores",
                  "verify_trajectory")
GENERATION_STAGES = ("generate", "sample")
CAP_TOKENS = 2048                           # the generation cap (every measured recipe; KCR §3)
GREEDY_PROMPTS, HARM_SAMPLES, BATCH = 468, 600, 32   # the family-probe evaluation bank (KCR §3)
GREEDY_BATCHES = -(-GREEDY_PROMPTS // BATCH)         # 15
SAMPLED_BATCHES = -(-HARM_SAMPLES // BATCH)          # 19
MAX_STRING = 64                              # KCR test 15: no output string longer than a hash
STRING_OK = re.compile(r"^[A-Za-z0-9._:+-]+( [A-Za-z0-9._:+-]+)?$")   # hashes, names, stage names, UTC stamps,
#                                         a GPU name (one space at most); never a sentence


class RecordRefused(Exception):
    """A file outside the allow-list, or a record that does not fit."""


def in_place(path: pathlib.Path) -> bool:
    """Whether a name sits in its one place (PLACE_OF): hosts/<host>/NAME, retrieved/<host>/tree/NAME or
    retrieved/<host>/tree/round1/<unit>/NAME. A name without a place is never in place."""
    parents = [p.name for p in path.parents]              # nearest first
    place = PLACE_OF.get(path.name)
    if place == "host":
        return len(parents) >= 2 and parents[1] == "hosts"
    if place == "tree":
        return len(parents) >= 3 and parents[0] == "tree" and parents[2] == "retrieved"
    if place == "unit":
        return len(parents) >= 5 and parents[1] == "round1" and parents[2] == "tree" and parents[4] == "retrieved"
    return False


def check_path(path: pathlib.Path) -> pathlib.Path:
    """The one gate every read passes: an allow-listed file name (exactly; no create-* wildcard), in its one place,
    and no forbidden path part anywhere in the path (A-V6)."""
    path = pathlib.Path(path)
    if path.name not in ALLOWED_NAMES:
        raise RecordRefused(f"file name not on the allow-list: {path.name}")
    if not in_place(path):
        raise RecordRefused(f"{path.name} is not in its place ({PLACE_OF[path.name]}): {path}")
    if any(part in FORBIDDEN_PARTS for part in path.parts):
        raise RecordRefused(f"forbidden path part in {path}")
    return path


def open_record(path: pathlib.Path):
    """Parse an allow-listed JSON file, or a JSONL file as a list of rows."""
    path = check_path(path)
    with open(path, "r", encoding="utf-8") as handle:
        if path.suffix == ".jsonl":
            return [json.loads(line) for line in handle if line.strip()]
        return json.load(handle)


def parse_utc(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def finite(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise RecordRefused(f"a timing field is missing or not finite: {value!r}")
    return float(value)


def host_of(kit: pathlib.Path) -> pathlib.Path:
    """The one host of the kit that finished (finished.json) and whose tree has JOB-DONE.json."""
    hosts = sorted(p for p in (kit / "hosts").iterdir() if p.is_dir() and (p / "finished.json").is_file()
                   and (kit / "retrieved" / p.name / "tree" / "JOB-DONE.json").is_file())
    if len(hosts) != 1:
        raise RecordRefused(f"{kit.name}: expected one finished host with a retrieved tree, found {len(hosts)}")
    return hosts[0]


def recipe_label(kit_name: str) -> str:
    """b (the 1e-4 recipe), b5e5 (the 5e-5 recipe) or g from a family-probe-sp kit folder's name; ``other`` for any other
    name (a KD9 unit from a tmp/family-probe-s78-* copy). The recipe's identity is the unit's recipe_sha256 (M); the
    label only groups the hashes in the families block."""
    m = re.search(r"-(b|b5e5|g)-(a0|seed\d{4}|\d{4})$", kit_name)
    return m.group(1) if m else "other"


def batch_rows(progress: list, ledger_rows: list) -> dict:
    """Each generation batch's seconds (its elapsed_s minus the previous generate row's; the very first minus the
    generate stage's start_s), rows and capped count, split into the greedy and the sampled series by the ledger's
    stage windows. The same differences the rule's in-pod speed check takes (rules_78b.s_obs_from_progress)."""
    stages = {r["stage"]: r for r in ledger_rows if r.get("stage") in GENERATION_STAGES}
    if set(stages) != set(GENERATION_STAGES):
        raise RecordRefused("ledger without a generate or sample stage")
    out = {}
    previous = finite(stages["generate"]["start_s"])
    for stage, series in (("generate", "greedy"), ("sample", "sampled")):
        start, end = finite(stages[stage]["start_s"]), finite(stages[stage]["end_s"])
        rows = [r for r in progress if r.get("kind") == "generate" and start < finite(r["elapsed_s"]) <= end]
        rows.sort(key=lambda r: r["elapsed_s"])
        batches = []
        for i, r in enumerate(rows):
            if int(r["batch"]) != i:
                raise RecordRefused(f"{stage}: batch {r['batch']} out of order (expected {i})")
            seconds = finite(r["elapsed_s"]) - previous
            previous = finite(r["elapsed_s"])
            batches.append({"batch": i, "rows": int(r["rows"]), "capped": int(r["capped"]),
                            "output_tokens": int(r["output_tokens"]), "seconds": round(seconds, 3),
                            "ms_per_step": round(seconds / CAP_TOKENS * 1000, 3)})
        out[series] = batches
    if len(out["greedy"]) != GREEDY_BATCHES or len(out["sampled"]) != SAMPLED_BATCHES:
        raise RecordRefused(f"batch counts {len(out['greedy'])}/{len(out['sampled'])}, expected "
                            f"{GREEDY_BATCHES}/{SAMPLED_BATCHES}")
    return out


def ledger_summary(rows: list) -> dict:
    """Stage seconds and the numeric fields the rule reads (training per step, tokens, capped counts, memory)."""
    seconds = {}
    for r in rows:
        if r.get("status") != "ok":
            raise RecordRefused(f"ledger stage {r.get('stage')} not ok")
        seconds[r["stage"]] = round(seconds.get(r["stage"], 0.0) + finite(r["seconds"]), 3)
    train = [r for r in rows if r["stage"] == "train"]
    if not train:
        raise RecordRefused("ledger without a train stage")
    steps = sum(int(r["steps"]) for r in train)
    train_s = sum(finite(r["seconds"]) for r in train)
    segment_max = max(finite(r["seconds"]) / int(r["steps"]) for r in train)
    by = {r["stage"]: r for r in rows if r["stage"] != "train"}
    gen, smp = by.get("generate"), by.get("sample")
    peak_reserved = max(int(r["memory"]["cuda_peak_reserved_bytes"]) for r in rows if r.get("memory"))
    peak_alloc = max(int(r["memory"]["cuda_peak_allocated_bytes"]) for r in rows if r.get("memory"))
    return {
        "stage_seconds": seconds, "sum_stage_s": round(sum(seconds.values()), 3),
        "first_start_s": round(finite(rows[0]["start_s"]), 3), "ledger_end_s": round(finite(rows[-1]["end_s"]), 3),
        "train_steps": steps, "train_s": round(train_s, 3),
        "train_s_per_step": round(train_s / steps, 4),          # KCR §3 "training per step": the whole run / its steps
        "train_s_per_step_segment_max": round(segment_max, 4),  # the slowest segment (the first holds the warm-up)
        "train_padded_tokens": sum(int(r["padded_tokens"]) for r in train),
        "train_input_tokens": sum(int(r["input_tokens"]) for r in train),
        "early_s": round(sum(seconds.get(s, 0.0) for s in EARLY_STAGES), 3),
        "scoring_s": round(sum(seconds.get(s, 0.0) for s in SCORING_STAGES), 3),
        "scoring_without_load_guard_s": round(sum(seconds.get(s, 0.0) for s in SCORING_STAGES
                                                  if s not in ("load_guard", "verify_trajectory")), 3),
        "generation_s": round(sum(seconds.get(s, 0.0) for s in GENERATION_STAGES), 3),
        "generate_capped": int(gen["capped"]) if gen else None,
        "generate_output_tokens": int(gen["output_tokens"]) if gen else None,
        "generate_prompts": int(gen["prompts"]) if gen else None,
        "sample_capped": int(smp["capped"]) if smp else None,
        "sample_output_tokens": int(smp["output_tokens"]) if smp else None,
        "sample_answers": int(smp["answers"]) if smp else None,
        "guard_items": int(by["guard"]["items"]) if "guard" in by else None,
        "guard_samples_items": int(by["guard_samples"]["items"]) if "guard_samples" in by else None,
        "harm_scores_answers": int(by["harm_scores"]["answers"]) if "harm_scores" in by else None,
        "trainable_parameters": int(by["load_policy"]["trainable_parameters"]) if "load_policy" in by else None,
        "cuda_peak_reserved_bytes": peak_reserved, "cuda_peak_allocated_bytes": peak_alloc,
    }


def unit_record(family: str, kit: pathlib.Path) -> dict:
    host = host_of(kit)
    tree = kit / "retrieved" / host.name / "tree"
    finished = open_record(host / "finished.json")
    created = open_record(host / "create-result.json")
    intent = open_record(host / "create-intent.json")
    verification = open_record(host / "verification.json")
    ready = open_record(tree / "BOOTSTRAP-READY.json")
    preflight = open_record(tree / "PREFLIGHT-DONE.json")
    done = open_record(tree / "JOB-DONE.json")
    if finished.get("status") != "verified-and-stopped" or finished.get("outer_exit") != 0 or not done.get("ok"):
        raise RecordRefused(f"{kit.name}: the job did not finish clean")
    outer_s = finite(finished["outer_elapsed_min"]) * 60.0
    create_utc, stop_utc = parse_utc(created["utc"]), parse_utc(finished["utc"])
    overhead_s = (stop_utc - create_utc).total_seconds() - outer_s
    # The engine units this job ran (names only); the e1 unit is the measured one, the others (the untuned
    # evaluation of a seed-1101 a0 pod) add their stage seconds to the job's total.
    unit_dirs = sorted(p for p in (tree / "round1").iterdir() if p.is_dir())
    e1 = [p for p in unit_dirs if "-e1-" in p.name]
    if len(e1) != 1:
        raise RecordRefused(f"{kit.name}: expected one e1 unit, found {len(e1)}")
    ledger_rows = open_record(e1[0] / "ledger.jsonl")
    progress = open_record(e1[0] / "progress.jsonl")
    ledger = ledger_summary(ledger_rows)
    other_stage_s = 0.0
    for p in unit_dirs:
        if p is not e1[0]:
            other_stage_s += sum(finite(r["seconds"]) for r in open_record(p / "ledger.jsonl"))
    batches = batch_rows(progress, ledger_rows)
    greedy, sampled = batches["greedy"], batches["sampled"]
    capped32 = [b for b in greedy[1:] + sampled if b["capped"] > 0 and b["rows"] == BATCH]
    cp, fl, env = verification["cap_projection"], verification["full_length"], verification["environment"]
    record = {
        "unit": host.name, "family": family, "kit": kit.name, "recipe_label": recipe_label(kit.name),
        "recipe_sha256": verification["recipe_sha256"], "manifest_sha256": verification["manifest_sha256"],
        "engine_sha256": ready["engine_sha256"], "training_identity": verification["training_identity"],
        "gpu_name": env["cuda"]["name"], "total_memory_bytes": int(env["cuda"]["total_memory_bytes"]),
        "cost_per_hr": finite(created["pod"]["costPerHr"]), "cap_hours_intent": finite(intent["cap_hours"]),
        "create_utc": created["utc"], "bootstrap_ready_utc": ready["utc"], "preflight_done_utc": preflight["utc"],
        "job_done_utc": done["utc"], "stop_confirmed_utc": finished["utc"],
        "outer_job_s": round(outer_s, 3), "pod_overhead_s": round(overhead_s, 3),
        "units_in_job": len(unit_dirs), "outer_includes_untuned_evaluation": len(unit_dirs) > 1,
        "other_units_stage_s": round(other_stage_s, 3),
        "outside_s": round(outer_s - ledger["sum_stage_s"] - other_stage_s, 3),
        "outside_after_ledger_end_s": round(outer_s - ledger["ledger_end_s"] - other_stage_s, 3),
        "preflight": {
            "training_s": finite(cp["training_s"]), "ms_per_step_full": finite(fl["ms_per_step_full"]),
            "untuned_projected_s": finite(cp["untuned_projected_s"]), "e1_upper_s": finite(cp["e1_upper_s"]),
            "projected_job_upper_s": finite(cp["projected_job_upper_s"]),
            "overhead_measured_s": finite(cp["overhead_measured_s"]), "batches_capped": int(cp["batches_capped"]),
            "full_length_seconds": finite(fl["seconds"]), "num_alloc_retries": int(fl["num_alloc_retries"]),
            "full_length_peak_reserved_bytes": int(fl["peak_reserved_bytes"]),
            "full_length_peak_allocated_bytes": int(fl["peak_allocated_bytes"]),
            "generation_memory_ok": bool(verification["generation_memory_ok"]),
            "preflight_elapsed_s": finite(verification["elapsed_s"]),
            "tried": len(preflight.get("tried") or []),
        },
        "ledger": ledger,
        "batches": batches,
        "first_greedy_batch_s": greedy[0]["seconds"],
        "first_greedy_batch_capped": greedy[0]["capped"],
        "capped32_batch_max_s": max((b["seconds"] for b in capped32), default=None),
        "capped32_batches": len(capped32),
        "greedy_batches_capped": sum(1 for b in greedy if b["capped"] > 0),
        "sampled_batches_capped": sum(1 for b in sampled if b["capped"] > 0),
    }
    return record


def all_capped_s(unit: dict, score_allcap_s: float, batches: int = GREEDY_BATCHES + SAMPLED_BATCHES) -> float:
    """KCR test 3: this unit's own all-capped time: every batch at its own slowest capped 32-row batch (the first
    greedy batch at its own first-batch time), its training, the scoring allowance, its early and outside time."""
    slow = max(unit["capped32_batch_max_s"] or 0.0, 0.0)
    first = max(unit["first_greedy_batch_s"], slow)
    return (first + (batches - 1) * slow + unit["ledger"]["train_s"] + score_allcap_s + unit["ledger"]["early_s"]
            + unit["outside_s"])


def linear_fit(points: list[tuple[float, float]]) -> tuple[float, float]:
    """Least squares y = a + b x (stdlib)."""
    n = len(points)
    mx, my = sum(x for x, _ in points) / n, sum(y for _, y in points) / n
    sxx = sum((x - mx) ** 2 for x, _ in points)
    b = sum((x - mx) * (y - my) for x, y in points) / sxx if sxx else 0.0
    return my - b * mx, b


def scoring_fit(units: list[dict]) -> dict:
    """KCR §4 SCORE_ALLCAP (E): linear fits of the guard, guard-on-samples and harm-score seconds on the output
    tokens they scored, extrapolated to every answer at the cap; plus the largest fixed stages."""
    pts = {"guard": [], "guard_samples": [], "harm_scores": []}
    fixed = 0.0
    for u in units:
        s, led = u["ledger"]["stage_seconds"], u["ledger"]
        pts["guard"].append((led["generate_output_tokens"], s["guard"]))
        pts["guard_samples"].append((led["sample_output_tokens"], s["guard_samples"]))
        pts["harm_scores"].append((led["generate_output_tokens"] + led["sample_output_tokens"], s["harm_scores"]))
        fixed = max(fixed, sum(s.get(k, 0.0) for k in SCORING_STAGES if k not in pts))
    fits = {k: linear_fit(v) for k, v in pts.items()}
    tokens = {"guard": GREEDY_PROMPTS * CAP_TOKENS, "guard_samples": HARM_SAMPLES * CAP_TOKENS,
              "harm_scores": (GREEDY_PROMPTS + HARM_SAMPLES) * CAP_TOKENS}
    allcap = {k: fits[k][0] + fits[k][1] * tokens[k] for k in fits}
    return {"intercept_s": {k: round(v[0], 3) for k, v in fits.items()},
            "ms_per_token": {k: round(v[1] * 1000, 5) for k, v in fits.items()},
            "all_capped_tokens": tokens, "all_capped_s": {k: round(v, 3) for k, v in allcap.items()},
            "fixed_stages_max_s": round(fixed, 3), "all_capped_total_s": round(sum(allcap.values()) + fixed, 3),
            "n_units": len(units)}


def median(values) -> float:
    """The middle value, or the mean of the two middle values (even n)."""
    v = sorted(values)
    n = len(v)
    return round(v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2, 3)


def family_constants(units: list[dict]) -> dict:
    """The per-family maxima the rule's constants must equal (KCR test 2)."""
    fine_tune_only = [u for u in units if not u["outer_includes_untuned_evaluation"]]
    return {
        "n_units": len(units), "n_fine_tune_only": len(fine_tune_only),
        "engine_sha256": sorted({u["engine_sha256"] for u in units}),
        "recipe_sha256_by_label": {label: sorted({u["recipe_sha256"] for u in units if u["recipe_label"] == label})
                                   for label in sorted({u["recipe_label"] for u in units})},
        "manifest_sha256": sorted({u["manifest_sha256"] for u in units}),
        "gpu_name": sorted({u["gpu_name"] for u in units}),
        "cost_per_hr": sorted({u["cost_per_hr"] for u in units}),
        "train_step_max_s": max(u["ledger"]["train_s_per_step"] for u in units),
        "train_step_segment_max_s": max(u["ledger"]["train_s_per_step_segment_max"] for u in units),
        "first_batch_max_s": max(u["first_greedy_batch_s"] for u in units),
        "batch_max_s": max(u["capped32_batch_max_s"] for u in units if u["capped32_batch_max_s"] is not None),
        "batch_ms_per_step_max": round(max(u["capped32_batch_max_s"] for u in units
                                           if u["capped32_batch_max_s"] is not None) / CAP_TOKENS * 1000, 3),
        "early_max_s": max(u["ledger"]["early_s"] for u in units),
        "outside_max_s": max(u["outside_s"] for u in units),
        "outside_after_ledger_end_max_s": max(u["outside_after_ledger_end_s"] for u in units),
        "scoring_max_s": max(u["ledger"]["scoring_s"] for u in units),
        "scoring_without_load_guard_max_s": max(u["ledger"]["scoring_without_load_guard_s"] for u in units),
        "arm_job_max_s": max(u["outer_job_s"] for u in fine_tune_only),
        "arm_job_median_s": median(u["outer_job_s"] for u in fine_tune_only),
        "job_with_untuned_evaluation_max_s": max((u["outer_job_s"] for u in units
                                                  if u["outer_includes_untuned_evaluation"]), default=None),
        "pod_overhead_max_s": max(u["pod_overhead_s"] for u in units),
        "pod_overhead_median_s": median(u["pod_overhead_s"] for u in units),
        "preflight_training_s_max": max(u["preflight"]["training_s"] for u in units),
        "preflight_ms_per_step_full_max": max(u["preflight"]["ms_per_step_full"] for u in units),
        "preflight_untuned_projected_s_max": max(u["preflight"]["untuned_projected_s"] for u in units),
        "num_alloc_retries_max": max(u["preflight"]["num_alloc_retries"] for u in units),
        "cuda_peak_reserved_bytes_max": max(u["ledger"]["cuda_peak_reserved_bytes"] for u in units),
        "total_memory_bytes": sorted({u["total_memory_bytes"] for u in units}),
        "scoring_fit": scoring_fit(units),
    }


def check_strings(obj, where="") -> None:
    """KCR test 15: no string longer than a hash, and nothing that reads as text."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            check_strings(k, where + "/" + str(k))
            check_strings(v, where + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_strings(v, f"{where}[{i}]")
    elif isinstance(obj, str):
        if len(obj) > MAX_STRING or not STRING_OK.match(obj):
            raise RecordRefused(f"output string not allowed at {where}: length {len(obj)}")


def derive(root: pathlib.Path, extra: list[tuple[str, pathlib.Path]] = (), kits: dict | None = None) -> dict:
    """The basis from the 17 kits under ``root`` (``kits`` overrides UNIT_KITS in tests only) plus any extra units."""
    units = []
    for family in FAMILIES:
        for kit_name in (UNIT_KITS if kits is None else kits)[family]:
            units.append(unit_record(family, root / kit_name))
    for family, folder in extra:
        if family not in FAMILIES:
            raise RecordRefused(f"unknown family {family}")
        units.append(unit_record(family, folder))
    units.sort(key=lambda u: (u["family"], u["unit"]))
    out = {"kind": "measured-basis-78b", "version": 1, "cap_tokens": CAP_TOKENS,
           "greedy_prompts": GREEDY_PROMPTS, "harm_samples": HARM_SAMPLES, "generation_batch": BATCH,
           "batches_per_evaluation": GREEDY_BATCHES + SAMPLED_BATCHES,
           "families": {f: family_constants([u for u in units if u["family"] == f]) for f in FAMILIES},
           "units": units}
    check_strings(out)
    return out


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=pathlib.Path, required=True,
                    help="the folder that holds the family-probe-sp-* kits (read-only; usually <checkout>/tmp)")
    ap.add_argument("--out", type=pathlib.Path, required=True, help="where to write the basis (a new path)")
    ap.add_argument("--extra-unit", action="append", default=[], metavar="FAMILY:KIT_FOLDER",
                    help="KD9: add a unit from a kit folder of the same layout (absolute path)")
    args = ap.parse_args(argv)
    extra = []
    for item in args.extra_unit:
        family, _, folder = item.partition(":")
        extra.append((family, pathlib.Path(folder)))
    basis = derive(args.root.resolve(), extra)
    data = canonical(basis)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "wb") as handle:
        handle.write(data)
    digest = hashlib.sha256(data).hexdigest()
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    print(json.dumps({"wrote": str(args.out), "sha256": digest, "units": len(basis["units"]), "utc": now,
                      "families": {f: {k: basis["families"][f][k] for k in (
                          "n_units", "train_step_max_s", "first_batch_max_s", "batch_max_s", "early_max_s",
                          "outside_max_s", "scoring_max_s", "arm_job_max_s", "pod_overhead_max_s",
                          "preflight_training_s_max", "preflight_ms_per_step_full_max")} for f in FAMILIES}},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
