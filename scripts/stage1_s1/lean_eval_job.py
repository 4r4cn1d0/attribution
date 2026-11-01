"""B17: the lean-evaluation job that measures c0 (stage-1 S1 package; CPU-testable with fixtures, CUDA on the pod).

c0 is one real job (REF LQ29; CONS LW-16): a cold start, full training of an R arm (an a0 arm under LQ30 (ii)), and
exactly the C-lean evaluation. C-lean has the contents of LW-15 (a), the lead's default (REF LQ27 (a)): 200 harm
prompts x 1 sampled answer, the task-loss pass, and the 100 greedy over-refusal answers, with the guard on every
answer. Option (b) (PLAN-S:202 as written: the sampled harm answers only) is a settings value. C-lean's O part is the
500-prompt O bank under the one cap (LN-07; addendum section 11 point 13): with the settings' over-refusal bank status
oext_pinned, the 100 greedy over-refusal answers and their guard records go through the shared pinned O-ext function
(scripts/stage1_s1/oext_eval.py, pinned by module, settings and cap branch in the section "oext"), which adds the PHTest
prompts under the cap branch and seals its files with the rest; under the pending branch (section 13) the job refuses.
The status dev100_recipe_cap is the LN-07 fallback (the dev 100 only, a stated limit).

Why a script and no engine change. The engine's run-one and eval-state jobs evaluate a whole bank: a job names only
null, dev, selector or hidden, and the recipe has no subset field. The engine's ``evaluate_checkpoint`` takes any item
list, but it always adds greedy answers to harm prompts, ``harm_samples.count`` samples per harm prompt, harm label
scores, and outcome summaries in its ledger records. So it cannot run C-lean, and it cannot keep the ledger free of
outcomes. This script composes C-lean from the engine's own parts instead, with the same settings and batching:
``engine.query_losses``, ``engine.greedy_generate``, ``engine.sample_generate``, ``runner.sample_seed``, the session's
guard (``GuardScorer.score``) and the runner's token-audit helpers. Engine identity X is pinned by the settings.

One process, in this order:

1. Checks before any model loads (exit 2, no folder): the pinned settings; the run-one job (the engine's
   ``validate_job``, then: kind run-one, ``evaluate_bank`` null, ``resume_from`` null, the development role on the dev
   split, the target checkpoint of the settings, an a0 or edit arm, the code pinned to the running engine; an edit arm
   needs ``--expect-adapter-fingerprint``, REF LQ30 (i)); the recipe (an allowed hash, with
   ``generation.harm_samples``); the engine's identity and access checks; the dev bank's counts (harm, over-refusal,
   task rows) against the settings; the O-ext pins, the cap branch (not pending) and the O-ext inputs (the bank file,
   its pinned record and W1-18's pinned record; oext_eval.prepare).
2. Full training: the engine's ``run_one`` with ``evaluate_bank`` null, from the seeded adapter to the target
   (``OUT/train``, an ordinary engine unit that the engine's ``verify`` checks).
3. The lean evaluation in the same session, on the trained adapter in memory; its fingerprint must equal the saved
   target state's. Order as in ``evaluate_checkpoint``: the task-loss pass on every task row, greedy answers to the
   over-refusal prompts, one sampled answer per harm prompt (sample index 0, seeded by ``runner.sample_seed``), the
   guard on the over-refusal answers, the guard on the sampled answers, then O-ext on the over-refusal answers (the
   PHTest answers under the cap branch, the 128-token cut by W1-18's rule, the guard). Nothing else runs (settings
   ``not_run``).
4. The seal (LQ30): answers, guard labels, task losses and every count made from them go to ``OUT/lean/sealed``. The
   readable files hold seconds, memory, counts of prompts and hashes only (a sealed file's byte size is an outcome
   proxy, so only its SHA-256 is written). Both folders are verified, and the readable files are scanned for every
   prompt, row, answer and guard text, raw and JSON-escaped, before the record is written.
5. ``OUT/c0_record.json``: identities, the cold-start facts, the timeline, every ledger stage with its seconds and
   cost category, per-answer seconds, the training facts (with the expected adapter fingerprint and whether training
   matched it: required for an edit arm, optional for a0), and the sealed files' SHA-256.

Timer. The origin is the first statements of this file, before torch and the engine are imported. On Linux the record
also gives the process age at the origin (from /proc), so interpreter start can be added. The FRE convention (LQ25)
counts the kit's job slot; this record's span lies inside that slot.

  python scripts/stage1_s1/lean_eval_job.py run --job JOB --prepared P --recipe R --out OUT
                                                [--registry REG] [--expect-adapter-fingerprint HEX]
                                                [--oext-bank F --oext-record F [--w1-18-record F]]
                                                (the fingerprint is required for an edit arm; the O-ext files
                                                under the status oext_pinned)
  python scripts/stage1_s1/lean_eval_job.py verify --out OUT

``run`` exit status: 0 the record is written; 2 refused before any folder was made; 1 a failure after a folder was made
(an error.txt is kept). ``verify``: 0 no problem; 1 problems (printed as counts and messages without text).
Messages carry ids, counts and hashes only, never prompt, row or answer text.
"""

from __future__ import annotations

import os as _os
import time as _time


def _process_age(stat_text: str, uptime_text: str, ticks_per_second: int) -> float:
    """The age in seconds of the process whose /proc/<pid>/stat is ``stat_text``: uptime minus its start time (field
    22, in clock ticks since boot). Fields are counted after the last ')', because the command name may hold spaces."""
    fields = stat_text[stat_text.rindex(")") + 2:].split()
    start_ticks = int(fields[19])                       # field 22 overall; fields[0] is field 3 (the state)
    return float(uptime_text.split()[0]) - start_ticks / ticks_per_second


def _read_process_age() -> float | None:
    """This process's age from /proc (Linux), or None where /proc is absent (macOS) or unreadable."""
    try:
        with open("/proc/self/stat", encoding="ascii") as handle:
            stat = handle.read()
        with open("/proc/uptime", encoding="ascii") as handle:
            uptime = handle.read()
        return _process_age(stat, uptime, _os.sysconf("SC_CLK_TCK"))
    except (OSError, ValueError, IndexError):
        return None


_ORIGIN = _time.monotonic()                 # the c0 timer origin: before torch and the engine are imported
_ORIGIN_UTC_EPOCH = _time.time()
_PROCESS_AGE_AT_ORIGIN = _read_process_age()

import argparse  # noqa: E402
import datetime as dt  # noqa: E402
import importlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402
import traceback  # noqa: E402
from collections import Counter  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Callable, Sequence  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import (canonical_json, code_identity, ids_sha256, jsonl_bytes,  # noqa: E402
                                                 read_json, read_jsonl, sha256_bytes, sha256_file, utc_now,
                                                 write_atomic, write_json)
from experiments.safety_selection.config import ConfigError, config_sha256, load_recipe, training_identity  # noqa: E402
from experiments.safety_selection.edits import arm_of  # noqa: E402
from experiments.safety_selection.jobs import (AccessError, JobError, check_identities, check_run_access,  # noqa: E402
                                               is_edit_arm, validate_job)
from experiments.safety_selection.ledger import (COMPLETE, ERROR, LEDGER, RunDirError, RunLedger,  # noqa: E402
                                                 create_run_dir, verify_files, write_complete)
from experiments.safety_selection.prepare import HiddenAccessError, Prepared, load_prepared, read_manifest  # noqa: E402
from experiments.safety_selection.sources import DataError  # noqa: E402
from experiments.safety_selection.textproc import repeated_ngram_fraction  # noqa: E402
from experiments.safety_selection.verify import chain_problems, dependency_receipt  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

oe = importlib.import_module(f"scripts.{HERE.name}.oext_eval")      # this package's own copy (also in the mirror)

__all__ = ["SETTINGS_PATH", "SETTINGS_SHA256", "SETTINGS_NAME", "RECORD_KIND", "LEAN_JOB_KIND", "CONTENT_PARTS",
           "CATEGORIES", "SEALED_FILES", "TRAIN_DIR", "LEAN_DIR", "SEALED_DIR", "RECORD_FILE", "C0Plan",
           "check_lean_settings", "load_lean_settings", "subset_sha256", "full_evaluation_answers", "prepare_c0_job",
           "lean_evaluate", "stage_table", "execute_c0_job", "verify_c0", "main"]

SETTINGS_PATH = HERE / "settings" / "lean_eval_job.json"
SETTINGS_SHA256 = "b0ab19ec28946334e4a033897c1097894fdf5797507f6a516614afc1c2c22acd"
SETTINGS_NAME = "lean_eval_job"
RECORD_KIND = "stage1 c0 lean job record"
LEAN_JOB_KIND = "stage1 lean evaluation"
CONTENT_PARTS = ("harm_sampled", "overrefusal_greedy", "task_loss_pass")
CATEGORIES = ("setup", "training", "verification", "task_loss_pass", "greedy_generation", "sampled_generation",
              "judging")
SEALED_FILES = ("query_loss.jsonl", "generations.jsonl", "samples.jsonl", "guard.jsonl", "guard_samples.jsonl",
                "counts.json")
OEXT_SEALED_FILES = tuple(oe.OUTPUT_FILES)               # sealed too when C-lean's O part is O-ext
LEAN_ORDER = ["query_loss", "generate", "sample", "guard", "guard_samples", "oext"]
OBANK_STATUSES = ("oext_pinned", "dev100_recipe_cap")
OEXT_KEYS = {"module", "module_sha256", "settings", "branch", "rule"}
TRAIN_DIR, LEAN_DIR, SEALED_DIR, RECORD_FILE = "train", "lean", "sealed", "c0_record.json"
LEAN_JOB_FILE, RECEIPT_FILE, ASSETS_FILE = "lean_job.json", "source_receipt.json", "assets.json"
FIXED_ROLE, FIXED_SPLIT, FIXED_BANK = "development", "dev", "dev"
HEX64 = frozenset("0123456789abcdef")
_INVALID = (s1.Refusal, ConfigError, JobError, AccessError, DataError, HiddenAccessError, RunDirError,
            FileNotFoundError, FileExistsError, PermissionError, ValueError)


class RunError(RuntimeError):
    """An invariant broke after a folder was made (the folders are kept; no record is written)."""


def _hex64(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX64


# ----- settings ------------------------------------------------------------------------------------------------


def _keys(obj: object, expected: set[str], where: str) -> dict:
    if not isinstance(obj, dict) or set(obj) != expected:
        found = sorted(obj) if isinstance(obj, dict) else type(obj).__name__
        raise s1.Refusal(f"settings {SETTINGS_NAME}: {where} must have exactly the keys {sorted(expected)}, "
                         f"found {found}")
    return obj


def _count(value: object, where: str, low: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < low:
        raise s1.Refusal(f"settings {SETTINGS_NAME}: {where} must be an integer >= {low}")
    return value


def check_lean_settings(doc: dict) -> dict:
    """The B17 sections of a parsed settings document (after ``s1common.check_settings``): the job rules, the C-lean
    contents and their options, the expected bank counts, the cost-stage map, the seal and the record names. A value
    outside the implemented choices refuses."""
    _keys(doc, {"kind", "name", "version", "owner", "requirement", "engine_x", "labels_sha256", "label_entries",
                "c0_definition", "c0_estimate", "job", "lean", "cost_stages", "seal", "timing", "record", "oext"},
          "the document")
    if not isinstance(doc["c0_estimate"], str) or not doc["c0_estimate"].strip():
        raise s1.Refusal(f"settings {SETTINGS_NAME}: c0_estimate must be a text")
    if doc["version"] != 1 or doc["label_entries"] != {}:
        raise s1.Refusal(f"settings {SETTINGS_NAME}: version 1 with no seed-label entries (nothing is drawn)")
    job = _keys(doc["job"], {"role", "split", "bank", "target_checkpoint", "arms", "code_pin", "resume_from",
                             "evaluate_bank", "allowed_recipes"}, "job")
    if (job["role"], job["split"], job["bank"]) != (FIXED_ROLE, FIXED_SPLIT, FIXED_BANK):
        raise s1.Refusal(f"settings {SETTINGS_NAME}: the lean job runs on the development role, the dev split and the "
                         "dev bank only")
    if not isinstance(job["target_checkpoint"], str) or not job["target_checkpoint"]:
        raise s1.Refusal(f"settings {SETTINGS_NAME}: job.target_checkpoint must name a checkpoint")
    recipes = job["allowed_recipes"]
    if not isinstance(recipes, dict) or not recipes or not all(_hex64(v) for v in recipes.values()):
        raise s1.Refusal(f"settings {SETTINGS_NAME}: job.allowed_recipes must map names to recipe SHA-256 values")
    lean = _keys(doc["lean"], {"contents", "contents_options", "harm_samples_per_prompt", "sample_index",
                               "sample_seed_rule", "expected_counts", "subset_rule", "share_note", "not_run", "order",
                               "guard_over_limit", "overrefusal_bank"}, "lean")
    options = lean["contents_options"]
    if not isinstance(options, dict) or set(options) != {"a", "b"}:
        raise s1.Refusal(f"settings {SETTINGS_NAME}: lean.contents_options must be exactly a and b")
    for name, option in options.items():
        _keys(option, {*CONTENT_PARTS, "source"}, f"lean.contents_options.{name}")
        if not all(isinstance(option[p], bool) for p in CONTENT_PARTS) or option["harm_sampled"] is not True:
            raise s1.Refusal(f"settings {SETTINGS_NAME}: option {name}: the parts are true or false, and every C-lean "
                             "option holds the sampled harm answers")
    if lean["contents"] not in options:
        raise s1.Refusal(f"settings {SETTINGS_NAME}: lean.contents must be one of {sorted(options)}")
    if lean["harm_samples_per_prompt"] != 1 or lean["sample_index"] != 0:
        raise s1.Refusal(f"settings {SETTINGS_NAME}: C-lean has 1 sampled answer per harm prompt, sample index 0 "
                         "(the only implemented choice)")
    counts = _keys(lean["expected_counts"], {"harm", "overrefusal", "task_rows"}, "lean.expected_counts")
    _count(counts["harm"], "lean.expected_counts.harm", 1)
    _count(counts["overrefusal"], "lean.expected_counts.overrefusal", 0)
    _count(counts["task_rows"], "lean.expected_counts.task_rows", 0)
    if lean["order"] != LEAN_ORDER:
        raise s1.Refusal(f"settings {SETTINGS_NAME}: lean.order must be the engine's evaluation order, then O-ext")
    obank = _keys(lean["overrefusal_bank"], {"status", "rule"}, "lean.overrefusal_bank")
    if obank["status"] not in OBANK_STATUSES or not isinstance(obank["rule"], str) or not obank["rule"].strip():
        raise s1.Refusal(f"settings {SETTINGS_NAME}: lean.overrefusal_bank.status must be one of "
                         f"{list(OBANK_STATUSES)}, with its rule")
    oext = _keys(doc["oext"], OEXT_KEYS, "oext")
    pin = _keys(oext["settings"], {"path", "sha256"}, "oext.settings")
    if (oext["module"], pin["path"]) != (oe.OWNER, "scripts/stage1_s1/settings/oext_eval.json"):
        raise s1.Refusal(f"settings {SETTINGS_NAME}: oext names the O-ext module and its settings file")
    if not (_hex64(oext["module_sha256"]) and _hex64(pin["sha256"])) or oext["branch"] not in oe.BRANCHES:
        raise s1.Refusal(f"settings {SETTINGS_NAME}: oext pins the module and settings by SHA-256 and a known branch")
    if not isinstance(oext["rule"], str) or not oext["rule"].strip():
        raise s1.Refusal(f"settings {SETTINGS_NAME}: oext.rule must be a text")
    stages = _keys(doc["cost_stages"], {"categories", "map", "rule"}, "cost_stages")
    if stages["categories"] != list(CATEGORIES):
        raise s1.Refusal(f"settings {SETTINGS_NAME}: cost_stages.categories must be {list(CATEGORIES)}")
    if not isinstance(stages["map"], dict) or not stages["map"] or any(
            not isinstance(k, str) or v not in CATEGORIES for k, v in stages["map"].items()):
        raise s1.Refusal(f"settings {SETTINGS_NAME}: cost_stages.map must map stage names to categories")
    seal = _keys(doc["seal"], {"readable", "sealed_dir", "sealed_files", "rule", "text_scan_min_chars"}, "seal")
    if seal["sealed_dir"] != f"{LEAN_DIR}/{SEALED_DIR}" or seal["sealed_files"] != [*SEALED_FILES, *OEXT_SEALED_FILES]:
        raise s1.Refusal(f"settings {SETTINGS_NAME}: seal.sealed_dir and seal.sealed_files are fixed")
    _count(seal["text_scan_min_chars"], "seal.text_scan_min_chars", 1)
    _keys(doc["timing"], {"origin", "clock", "cold_start", "slot_note"}, "timing")
    record = _keys(doc["record"], {"file", "kind"}, "record")
    if (record["file"], record["kind"]) != (RECORD_FILE, RECORD_KIND):
        raise s1.Refusal(f"settings {SETTINGS_NAME}: record.file and record.kind are fixed")
    return doc


def load_lean_settings(path: str | Path | None = None, expected_sha256: str | None = None) -> tuple[dict, str]:
    """The pinned settings (``SETTINGS_PATH`` hashing to ``SETTINGS_SHA256`` unless both are given): their bytes hash
    as expected, ``s1common.check_settings`` passes (engine X, registry entries), then ``check_lean_settings``."""
    doc, digest = s1.load_settings(path or SETTINGS_PATH, expected_sha256 or SETTINGS_SHA256, SETTINGS_NAME)
    return check_lean_settings(doc), digest


# ----- the plan (checks before any model loads) ----------------------------------------------------------------


@dataclass(frozen=True)
class C0Plan:
    """Everything the job needs, checked before any model loads."""

    job: dict
    job_path: Path
    job_sha256: str
    recipe: dict
    recipe_path: Path
    recipe_sha256: str
    recipe_name: str
    prepared_dir: Path
    prepared: Prepared
    out_dir: Path
    settings: dict
    settings_sha256: str
    contents: str
    parts: dict
    harm: tuple
    overrefusal: tuple
    task_rows: int
    bank_kinds: dict
    edit_sha256: str | None
    expected_fingerprint: str | None
    oext: Any = None


def subset_sha256(harm: Sequence[dict], overrefusal: Sequence[dict]) -> str:
    """SHA-256 of the canonical list of [kind, prompt id, token SHA-256] of the lean items, harm first."""
    return sha256_bytes(canonical_json([[i["kind"], i["prompt_id"], i["token_sha256"]] for i in [*harm, *overrefusal]]))


def full_evaluation_answers(bank_kinds: dict, recipe: dict) -> int:
    """The answers the engine's full evaluation of this bank makes: one greedy answer per generation-kind item, and
    ``harm_samples.count`` sampled answers per harm item (1,068 for the dev bank under the stage-1 recipe)."""
    greedy = sum(bank_kinds.get(kind, 0) for kind in runner.GENERATION_KINDS)
    return greedy + bank_kinds.get("harm", 0) * recipe["generation"]["harm_samples"]["count"]


def check_lean_oext(settings: dict, parts: dict, overrefusal: int, oext: Any) -> Any:
    """C-lean's O part (LN-07; addendum section 11 point 13): with the over-refusal greedy answers and the status
    oext_pinned, ``oext`` (oext_eval.prepare's result) must be the pinned module, settings and branch, the branch must
    not be pending, and its dev part must be the bank's over-refusal count; otherwise no O-ext input is taken."""
    status = settings["lean"]["overrefusal_bank"]["status"]
    if not (parts["overrefusal_greedy"] and status == "oext_pinned"):
        if oext is not None:
            raise s1.Refusal(f"O-ext inputs were given, but C-lean's O part is not O-ext (status {status}, contents "
                             f"{settings['lean']['contents']})")
        return None
    if oext is None:
        raise s1.Refusal("C-lean's O part is the 500-prompt bank (status oext_pinned): the O-ext settings and inputs "
                         "are needed")
    pin = settings["oext"]
    if oe.module_sha256() != pin["module_sha256"]:
        raise s1.Refusal("the O-ext module is not the one these settings pin")
    if oext.settings.sha256 != pin["settings"]["sha256"] or oext.branch != pin["branch"]:
        raise s1.Refusal("the O-ext settings (or their branch) are not the ones these settings pin")
    if not oext.runs:
        raise s1.Refusal("the O-ext cap branch is pending W1-18 (addendum section 13): C-lean's O part is not "
                         "defined yet, so the c0 job does not run")
    if oext.settings.doc["bank"]["dev100"]["prompts"] != overrefusal:
        raise s1.Refusal("the O-ext settings' dev part is not this bank's over-refusal count")
    return oext


def _oext_record(oext: Any) -> dict | None:
    """The text-free, outcome-free O-ext identity of a plan (the branch, the pins and the input hashes)."""
    if oext is None:
        return None
    return {"branch": oext.branch, "settings_sha256": oext.settings.sha256, "module_sha256": oe.module_sha256(),
            "record_sha256": oext.bank.record_sha256, "bank_sha256": oext.bank.bank_sha256,
            "w1_18_record_sha256": None if oext.w1_18 is None else oext.w1_18.record_sha256,
            "phtest_prompts": len(oext.bank.rows)}


def prepare_c0_job(job_path: str | Path, *, prepared_dir: str | Path, recipe_path: str | Path, out_dir: str | Path,
                   settings: dict, settings_sha256: str, expected_fingerprint: str | None = None,
                   oext: Any = None) -> C0Plan:
    """Every check that can run before a model loads; refuses (``s1common.Refusal`` or the engine's own errors)
    before any folder is made."""
    job_path, out_dir = Path(job_path), Path(out_dir)
    if out_dir.exists():
        raise s1.Refusal(f"{out_dir} exists: the lean job writes a new folder and never replaces one")
    if expected_fingerprint is not None and not _hex64(expected_fingerprint):
        raise s1.Refusal("--expect-adapter-fingerprint must be 64 lowercase hex characters")
    job_bytes = job_path.read_bytes()
    job = s1.strict_json(job_bytes)
    validate_job(job)
    rules = settings["job"]
    if job["kind"] != "run-one":
        raise s1.Refusal("the lean job trains with a run-one job")
    if job["evaluate_bank"] is not None:
        raise s1.Refusal("the run-one job must have evaluate_bank null: the lean evaluation is this script's, and a "
                         "full evaluation would break the c0 definition")
    if job["resume_from"] is not None:
        raise s1.Refusal("the run-one job must have resume_from null: c0 counts full training from the seeded adapter")
    if (job["role"], job["split"]) != (rules["role"], rules["split"]):
        raise s1.Refusal(f"the lean job runs on the {rules['role']} role and the {rules['split']} split only")
    if job["target_checkpoint"] != rules["target_checkpoint"]:
        raise s1.Refusal(f"the target checkpoint must be {rules['target_checkpoint']} (the study's chosen checkpoint)")
    if job["arm"] != "a0" and not is_edit_arm(job["arm"]):
        raise s1.Refusal("the arm must be a0 or an edit arm (an R arm is an edit arm); group arms are not c0 arms")
    if is_edit_arm(job["arm"]) and expected_fingerprint is None:
        raise s1.Refusal("an edit-arm c0 job needs --expect-adapter-fingerprint (the earlier run's target-state "
                         "fingerprint): REF LQ30 (i) says the record states whether training matched it")
    code = code_identity()
    if job["code_sha256"] != code["sha256"]:
        raise s1.Refusal("the run-one job must pin code_sha256 to the running engine (make-job --pin-code)")
    recipe_path = Path(recipe_path)
    recipe = load_recipe(recipe_path)
    recipe_sha = config_sha256(recipe)
    allowed = rules["allowed_recipes"]
    if recipe_sha not in allowed.values():
        raise s1.Refusal(f"recipe {recipe_sha[:16]} is not one of the settings' allowed recipes {sorted(allowed)}")
    if "harm_samples" not in recipe["generation"]:
        raise s1.Refusal("the recipe has no generation.harm_samples: C-lean's sampled answers are not defined")
    edit_sha = None
    if is_edit_arm(job["arm"]):
        if arm_of(Path(job["edit"]).read_bytes()) != job["arm"]:
            raise s1.Refusal("the edit file's SHA-256 is not the job's arm")
        edit_sha = job["arm"][len("edit-"):]
    manifest, manifest_sha = read_manifest(prepared_dir, job["manifest_sha256"])
    check_identities(job, manifest, manifest_sha, recipe, code)
    check_run_access(job["role"], job["split"], job["seed"], rules["bank"], manifest["data_config"], False)
    prepared = load_prepared(prepared_dir, manifest_sha, banks=(rules["bank"],))
    bank = prepared.banks[rules["bank"]]
    kinds = dict(sorted(Counter(item["kind"] for item in bank).items()))
    harm = tuple(item for item in bank if item["kind"] == "harm")
    overrefusal = tuple(item for item in bank if item["kind"] == "overrefusal")
    expected = settings["lean"]["expected_counts"]
    found = {"harm": len(harm), "overrefusal": len(overrefusal), "task_rows": len(prepared.query_rows)}
    if found != expected:
        raise s1.Refusal(f"the {rules['bank']} bank and task rows count {found}, the settings expect {expected}")
    contents = settings["lean"]["contents"]
    parts = {p: settings["lean"]["contents_options"][contents][p] for p in CONTENT_PARTS}
    checked_oext = check_lean_oext(settings, parts, len(overrefusal), oext)
    return C0Plan(job=job, job_path=job_path, job_sha256=sha256_bytes(job_bytes), recipe=recipe,
                  recipe_path=recipe_path, recipe_sha256=recipe_sha,
                  recipe_name=next(name for name, sha in sorted(allowed.items()) if sha == recipe_sha),
                  prepared_dir=Path(prepared_dir), prepared=prepared, out_dir=out_dir, settings=settings,
                  settings_sha256=settings_sha256, contents=contents, parts=parts, harm=harm,
                  overrefusal=overrefusal if parts["overrefusal_greedy"] else (),
                  task_rows=len(prepared.query_rows) if parts["task_loss_pass"] else 0, bank_kinds=kinds,
                  edit_sha256=edit_sha, expected_fingerprint=expected_fingerprint, oext=checked_oext)


# ----- the lean evaluation ------------------------------------------------------------------------------------


def _write_sealed(folder: Path, name: str, data: bytes) -> dict:
    """Writes one sealed file; returns its SHA-256 only. A sealed file's byte size grows with the answers' token
    counts and moves with the guard labels, so it is an outcome proxy and never goes into a readable file."""
    write_atomic(folder / name, data)
    return {"sha256": sha256_bytes(data)}


def lean_evaluate(session: runner.Session, policy: Any, plan: C0Plan, ledger: RunLedger, unit_dir: Path,
                  checkpoint: str, adapter_fingerprint: str) -> tuple[dict, dict]:
    """C-lean on the policy's adapter as it is in memory, whose fingerprint the caller checked
    (``adapter_fingerprint``). Every value made from an answer is written to ``unit_dir/sealed``; the summary, the
    ledger, its progress and its records hold counts of prompts, seconds, memory and hashes only. The adapter and the
    train/eval mode must be unchanged afterwards, and the RNG states are restored, as ``runner.evaluate_checkpoint``
    requires. Returns (summary, the guard's identity)."""
    recipe, codec, device = session.recipe, policy.codec, policy.device
    gen, seed = recipe["generation"], plan.job["seed"]
    sampling = gen["harm_samples"]
    over = {"over_limit_unscored": True} if gen.get("guard_over_limit") == "unscored" else {}
    max_prompt = recipe["model"]["max_prompt_tokens"]
    sealed_dir = unit_dir / SEALED_DIR
    sealed_dir.mkdir()
    sealed: dict[str, dict] = {}
    counts: dict[str, Any] = {}
    before = (adapter_fingerprint, policy.model.training)

    def progress(stage: str):
        def on_batch(b: int, index: list[int], batch: list) -> None:
            ledger.progress(stage, checkpoint=checkpoint, batch=b, rows=len(index))
        return on_batch

    with en.preserved_rng(device):
        guard = session.guard(ledger, unit_dir)                 # loaded here, as evaluate_checkpoint loads it
        rng_start = en.rng_digest(device)
        if plan.parts["task_loss_pass"]:
            queries, query_sha = runner._query_examples(policy, plan.prepared, recipe)
            with ledger.stage("query_loss", checkpoint=checkpoint, queries=len(queries)) as info:
                losses = en.query_losses(policy.model, queries, pad_id=codec.pad_id, device=device,
                                         chunk=recipe["train"]["lm_head_chunk_tokens"],
                                         check=lambda what: ledger.check(f"query loss {checkpoint} {what}"))
                info.update(forward_passes=len(queries), input_tokens=sum(len(q.input_ids) for q in queries),
                            target_tokens=sum(q.n_target for q in queries))
            sealed["query_loss.jsonl"] = _write_sealed(sealed_dir, "query_loss.jsonl", jsonl_bytes(
                [{"query_id": q.row_id, "input_tokens": len(q.input_ids), "target_tokens": q.n_target,
                  "token_sha256": ids_sha256(q.input_ids), "loss": loss} for q, loss in zip(queries, losses, strict=True)]))
            counts["query_loss"] = {"n": len(losses), "query_bank_sha256": query_sha,
                                    "definition": plan.prepared.manifest.get("query_loss_definition")
                                    or en.QUERY_LOSS_DEFINITION}
        or_items = list(plan.overrefusal)
        or_prompts = [runner._prompt_ids(codec, item, max_prompt) for item in or_items]
        harm_items = list(plan.harm)
        harm_prompts = [runner._prompt_ids(codec, item, max_prompt) for item in harm_items]
        records: list[dict] = []
        if or_items:
            with ledger.stage("generate", checkpoint=checkpoint, prompts=len(or_prompts)) as info:
                generations = en.greedy_generate(
                    policy.model, or_prompts, max_new_tokens=gen["max_new_tokens"], stop_ids=codec.stop_ids,
                    pad_id=codec.pad_id, device=device, batch_size=gen["batch_size"],
                    check=lambda what: ledger.check(f"generate {checkpoint} {what}"), on_batch=progress("generate"))
                info.update(prompt_tokens=sum(map(len, or_prompts)))
            records = [{"prompt_id": item["prompt_id"], "kind": item["kind"], "prompt_ids": ids,
                        "prompt_tokens": len(ids), "output_ids": list(g.output_ids), "output_tokens": len(g.output_ids),
                        "stop_reason": g.stop_reason, "stop_token": g.stop_token, "empty": not g.output_ids,
                        "text": codec.decode(g.output_ids), "repetition_4gram": repeated_ngram_fraction(g.output_ids, 4)}
                       for item, ids, g in zip(or_items, or_prompts, generations, strict=True)]
            sealed["generations.jsonl"] = _write_sealed(sealed_dir, "generations.jsonl", jsonl_bytes(records))
        index = plan.settings["lean"]["sample_index"]
        todo = [(item, index, runner.sample_seed(seed, item["prompt_id"], index)) for item in harm_items]
        with ledger.stage("sample", checkpoint=checkpoint, answers=len(todo)) as info:
            sampled = en.sample_generate(
                policy.model, harm_prompts, [s for _, _, s in todo], temperature=sampling["temperature"],
                max_new_tokens=gen["max_new_tokens"], stop_ids=codec.stop_ids, pad_id=codec.pad_id, device=device,
                batch_size=gen["batch_size"], check=lambda what: ledger.check(f"sample {checkpoint} {what}"),
                on_batch=progress("sample"))
            info.update(prompt_tokens=sum(map(len, harm_prompts)))
        samples = [{"prompt_id": item["prompt_id"], "kind": "harm", "sample_index": k, "seed": s,
                    "answer_id": f"{item['prompt_id']}#s{k}", "output_ids": list(g.output_ids),
                    "output_tokens": len(g.output_ids), "stop_reason": g.stop_reason, "stop_token": g.stop_token,
                    "empty": not g.output_ids, "text": codec.decode(g.output_ids),
                    "repetition_4gram": repeated_ngram_fraction(g.output_ids, 4)}
                   for (item, k, s), g in zip(todo, sampled, strict=True)]
        sealed["samples.jsonl"] = _write_sealed(sealed_dir, "samples.jsonl", jsonl_bytes(samples))
        prompt_of = {item["prompt_id"]: item["prompt"] for item in [*harm_items, *or_items]}
        guarded: list[dict] = []
        if records:
            with ledger.stage("guard", checkpoint=checkpoint, items=len(records)):
                guarded = guard.score([(r["prompt_id"], prompt_of[r["prompt_id"]], r["text"]) for r in records],
                                      check=lambda what: ledger.check(f"guard {checkpoint} {what}"), **over)
            sealed["guard.jsonl"] = _write_sealed(sealed_dir, "guard.jsonl", jsonl_bytes(
                [{"prompt_id": r["prompt_id"], "kind": r["kind"], **g} for r, g in zip(records, guarded, strict=True)]))
        with ledger.stage("guard_samples", checkpoint=checkpoint, items=len(samples)):
            guarded_samples = guard.score([(r["answer_id"], prompt_of[r["prompt_id"]], r["text"]) for r in samples],
                                          check=lambda what: ledger.check(f"guard samples {checkpoint} {what}"), **over)
        sealed["guard_samples.jsonl"] = _write_sealed(sealed_dir, "guard_samples.jsonl", jsonl_bytes(
            [{"prompt_id": r["prompt_id"], "sample_index": r["sample_index"], **g}
             for r, g in zip(samples, guarded_samples, strict=True)]))
        if plan.oext is not None:                  # C-lean's O part: the 500 bank under the cap (LN-07, 11.13)
            dev = oe.dev_answers(or_items, records, [{"prompt_id": r["prompt_id"], **g}
                                                     for r, g in zip(records, guarded, strict=True)])
            oe.evaluate_oext(session=session, policy=policy, codec=codec, ledger=ledger, run_dir=unit_dir,
                             folder=sealed_dir, prepared=plan.oext, dev=dev, checkpoint=checkpoint,
                             dev_inputs={"dev100/generations.jsonl": sealed["generations.jsonl"]["sha256"],
                                         "dev100/guard.jsonl": sealed["guard.jsonl"]["sha256"]})
            for name in oe.OUTPUT_FILES:
                sealed[name] = {"sha256": sha256_file(sealed_dir / name)}
        rng_consumed = en.rng_digest(device) != rng_start

        def answer_counts(rows: list[dict], labels: list[dict]) -> dict:
            return {"answers": len(rows), "output_tokens": sum(r["output_tokens"] for r in rows),
                    "capped": sum(r["stop_reason"] == en.STOP_CAP for r in rows), "empty": sum(r["empty"] for r in rows),
                    "guard_invalid": sum(not g["valid"] for g in labels),
                    "guard_input_tokens": sum(g["guard_input_tokens"] or 0 for g in labels)}

        counts["overrefusal_greedy"] = answer_counts(records, guarded)
        counts["harm_sampled"] = answer_counts(samples, guarded_samples)
        sealed["counts.json"] = _write_sealed(sealed_dir, "counts.json", canonical_json(counts))
    if (en.lora_fingerprint(policy.named), policy.model.training) != before:
        raise RunError("the lean evaluation changed the adapter or the train/eval mode")
    summary = {"checkpoint": checkpoint, "task_rows": plan.task_rows, "overrefusal_greedy_answers": len(records),
               "harm_sampled_answers": len(samples), "guard_items": len(records) + len(samples),
               **({} if plan.oext is None else {"oext_phtest_answers": len(plan.oext.bank.rows),
                                                "oext_branch": plan.oext.branch}),
               "rng_consumed_inside_evaluation_then_restored": rng_consumed,
               "sealed_files": dict(sorted(sealed.items()))}
    ledger.record("lean_evaluation", **{k: v for k, v in summary.items() if k != "sealed_files"},
                  sealed_files=sorted(sealed))
    return summary, guard.identity


# ----- timing ---------------------------------------------------------------------------------------------------


def stage_table(folder: Path, name: str, stage_map: dict) -> list[dict]:
    """Every stage record of ``folder``'s ledger, in order: its name, segment, status, seconds and cost category (a
    name outside the map is ``unmapped``, never dropped)."""
    rows = []
    for record in read_jsonl(folder / LEDGER):
        row = {"folder": name, "stage": record["stage"], "status": record["status"], "seconds": record["seconds"],
               "category": stage_map.get(record["stage"], "unmapped")}
        if "segment" in record:
            row["segment"] = record["segment"]
        rows.append(row)
    return rows


def _per(seconds: float | None, n: int) -> float | None:
    return seconds / n if seconds is not None and n else None


def _stage_seconds(rows: list[dict], folder: str, stage: str) -> float | None:
    found = [r["seconds"] for r in rows if r["folder"] == folder and r["stage"] == stage]
    return math.fsum(found) if found else None


# ----- the job --------------------------------------------------------------------------------------------------


def _texts(plan: C0Plan, sealed_dir: Path, min_chars: int) -> list[str]:
    """Every prompt, task-row and answer text and guard answer of the job of at least ``min_chars`` characters."""
    texts = [i[key] for i in plan.prepared.banks[plan.settings["job"]["bank"]] for key in ("prompt", "question")
             if isinstance(i.get(key), str)]
    texts += [q[key] for q in plan.prepared.query_rows for key in ("prompt", "response")]
    for name, field in (("generations.jsonl", "text"), ("samples.jsonl", "text"), ("guard.jsonl", "guard_answer"),
                        ("guard_samples.jsonl", "guard_answer")):
        texts += [row[field] for row in read_jsonl(sealed_dir / name) if isinstance(row.get(field), str)]
    if plan.oext is not None:                   # the PHTest prompts, their answers, the cut texts, the judge's words
        texts += [prompt for _, prompt in plan.oext.bank.rows]
        for name, fields in ((oe.GENERATIONS, ("text",)), (oe.GUARD, ("text", "guard_answer"))):
            texts += [row[f] for row in read_jsonl(sealed_dir / name) for f in fields if isinstance(row.get(f), str)]
    return sorted({t for t in texts if len(t) >= min_chars})


def _text_forms(text: str) -> set[bytes]:
    """The forms in which a text can lie in a readable file: raw UTF-8, and JSON-escaped with and without
    ensure_ascii (a newline, a quote, a backslash or a non-ASCII character changes in JSON). These are the forms of
    s1common's scan."""
    return {text.encode("utf-8"), json.dumps(text, ensure_ascii=False)[1:-1].encode("utf-8"),
            json.dumps(text, ensure_ascii=True)[1:-1].encode("ascii")}


def _text_hits(data: bytes, texts: Sequence[str]) -> int:
    """How many of the texts lie in data in any of their forms (``_text_forms``)."""
    return sum(any(form in data for form in _text_forms(text)) for text in texts)


def _readable_lean_files(unit_dir: Path) -> list[Path]:
    return sorted(p for p in unit_dir.rglob("*") if p.is_file() and SEALED_DIR not in p.relative_to(unit_dir).parts)


def execute_c0_job(plan: C0Plan, session: runner.Session, *, registry: str | Path | None = None,
                   origin: float | None = None, origin_utc_epoch: float | None = None,
                   process_age_at_origin: float | None = None, marks: dict | None = None,
                   clock: Callable[[], float] = _time.monotonic) -> dict:
    """Train (the engine's run_one), run C-lean, verify, scan and write the record; returns the record. ``marks``
    holds timeline points already passed (seconds from ``origin``), for example the end of the imports."""
    if origin is None:
        origin = clock()
    if origin_utc_epoch is None:
        origin_utc_epoch = _time.time() - (clock() - origin)
    marks = dict(marks or {})

    def mark(name: str) -> float:
        marks[name] = clock() - origin
        return marks[name]

    if session.loaded_in:
        raise s1.Refusal(f"not a cold start: the session has already loaded {sorted(session.loaded_in)}")
    if session.recipe_sha256 != plan.recipe_sha256:
        raise s1.Refusal("the session's recipe is not the plan's recipe")
    mark("checks_done")
    out, target, settings = plan.out_dir, plan.job["target_checkpoint"], plan.settings
    out.mkdir(parents=True)
    train_dir, unit_dir = out / TRAIN_DIR, out / LEAN_DIR
    mark("train_start")
    result = runner.run_one(plan.job, prepared_dir=plan.prepared_dir, out_dir=train_dir, session=session,
                            registry=registry)
    mark("train_end")
    limit = plan.job["wall_limit_seconds"]                 # one limit for training and the lean evaluation together
    unit_dir = create_run_dir(unit_dir)
    mark("lean_start")
    ledger = RunLedger(unit_dir, sync=session.sync, memory=session.memory,
                       wall_limit_s=None if limit is None else limit - (marks["lean_start"] - marks["train_start"]))
    try:
        lean_job = {"kind": LEAN_JOB_KIND, "version": 1, "train_run": TRAIN_DIR, "checkpoint": target,
                    "seed": plan.job["seed"], "arm": plan.job["arm"], "contents": plan.contents, "parts": plan.parts,
                    "harm_prompts": [i["prompt_id"] for i in plan.harm],
                    "overrefusal_prompts": [i["prompt_id"] for i in plan.overrefusal], "task_rows": plan.task_rows,
                    "subset_sha256": subset_sha256(plan.harm, plan.overrefusal), "job_sha256": plan.job_sha256,
                    "oext": _oext_record(plan.oext),
                    "manifest_sha256": plan.prepared.manifest_sha256, "recipe_sha256": plan.recipe_sha256,
                    "settings_sha256": plan.settings_sha256, "code_sha256": code_identity()["sha256"]}
        write_json(unit_dir / LEAN_JOB_FILE, lean_job)
        ledger.status("running", stage="start")
        receipt = dependency_receipt(train_dir, "trained_state", target)
        write_json(unit_dir / RECEIPT_FILE, receipt)
        policy = session.policy(ledger, unit_dir)
        saved = result["checkpoints"][target]["adapter_fingerprint"]
        with ledger.stage("check_state", checkpoint=target) as info:
            if sha256_file(train_dir / "states" / target / en.STATE) != receipt["state_sha256"]:
                raise RunError(f"the saved {target} state changed after its receipt was written")
            fingerprint = en.lora_fingerprint(policy.named)
            if not fingerprint == saved == receipt["state"]["adapter_fingerprint"]:
                raise RunError(f"the adapter in memory is not the saved {target} state")
            info.update(adapter_fingerprint=fingerprint)
        summary, guard_identity = lean_evaluate(session, policy, plan, ledger, unit_dir, target, fingerprint)
        write_json(unit_dir / ASSETS_FILE, {"policy": policy.identity, "guard": guard_identity,
                                            "guard_pin": runner.guard_pin(plan.recipe),
                                            "environment": session.environment, "loaded_in": dict(session.loaded_in)})
        write_complete(unit_dir, {"kind": LEAN_JOB_KIND, "lean_job_sha256": sha256_file(unit_dir / LEAN_JOB_FILE),
                                  "source_complete_sha256": receipt["complete_sha256"],
                                  "sealed_files": summary["sealed_files"]})
        ledger.status("complete")
    except BaseException as exc:
        write_atomic(unit_dir / ERROR, traceback.format_exc().encode("utf-8"))
        try:
            ledger.status("failed", error=f"{type(exc).__name__}: {exc}")
        except Exception:  # noqa: BLE001 - the error file is the evidence; a status write must not hide it
            pass
        raise
    mark("lean_end")
    problems = [f"train: {p}" for p in chain_problems(train_dir)] + [f"lean: {p}" for p in verify_files(unit_dir)]
    if sha256_file(train_dir / COMPLETE) != receipt["complete_sha256"]:
        problems.append("train: COMPLETE.json changed after the lean evaluation's receipt")
    if problems:
        raise RunError(f"the folders do not verify ({len(problems)} problems; first: {problems[0]})")
    texts = _texts(plan, unit_dir / SEALED_DIR, settings["seal"]["text_scan_min_chars"])
    for path in _readable_lean_files(unit_dir):
        hits = _text_hits(path.read_bytes(), texts)
        if hits:
            raise RunError(f"readable file lean/{path.relative_to(unit_dir).as_posix()} holds {hits} job texts")
    mark("verified")
    stage_map = settings["cost_stages"]["map"]
    rows = stage_table(train_dir, TRAIN_DIR, stage_map) + stage_table(unit_dir, LEAN_DIR, stage_map)
    by_category = {c: math.fsum(r["seconds"] for r in rows if r["category"] == c) for c in CATEGORIES}
    stage_total = math.fsum(r["seconds"] for r in rows)
    end = mark("end")
    state = result["checkpoints"][target]
    phtest = summary.get("oext_phtest_answers", 0)
    answers = summary["overrefusal_greedy_answers"] + summary["harm_sampled_answers"] + phtest
    full = full_evaluation_answers(plan.bank_kinds, plan.recipe) + phtest
    record = {
        "kind": RECORD_KIND, "version": 1,
        "definition": settings["c0_definition"],
        "provenance": s1.provenance(Path(__file__).resolve(), plan.settings_sha256,
                                    {"job": plan.job_sha256, "recipe": sha256_file(plan.recipe_path),
                                     "prepared_manifest": plan.prepared.manifest_sha256,
                                     **({"edit": plan.edit_sha256} if plan.edit_sha256 else {}),
                                     **({} if plan.oext is None else {
                                         "oext_settings": plan.oext.settings.sha256,
                                         "oext_record": plan.oext.bank.record_sha256,
                                         "oext_bank": plan.oext.bank.bank_sha256})}, {}),
        "job": {"arm": plan.job["arm"], "seed": plan.job["seed"], "split": plan.job["split"], "role": plan.job["role"],
                "target_checkpoint": target, "edit_sha256": plan.edit_sha256, "job_sha256": plan.job_sha256,
                "manifest_sha256": plan.prepared.manifest_sha256, "recipe_sha256": plan.recipe_sha256,
                "recipe_name": plan.recipe_name, "training_identity": training_identity(plan.recipe),
                "code_sha256": plan.job["code_sha256"], "replicate_of": plan.job["replicate_of"],
                "registry": None if registry is None else str(registry)},
        "oext": _oext_record(plan.oext),
        "overrefusal_bank": settings["lean"]["overrefusal_bank"]["status"],
        "c0_estimate": settings["c0_estimate"],
        "contents": {"option": plan.contents, "parts": plan.parts,
                     "source": settings["lean"]["contents_options"][plan.contents]["source"],
                     "not_run": settings["lean"]["not_run"]},
        "subset": {"bank": settings["job"]["bank"], "bank_kinds": plan.bank_kinds,
                   "harm_prompts": len(plan.harm), "harm_sampled_answers": summary["harm_sampled_answers"],
                   "sample_index": settings["lean"]["sample_index"],
                   "overrefusal_greedy_answers": summary["overrefusal_greedy_answers"],
                   "task_rows": summary["task_rows"], **({} if plan.oext is None else {"oext_phtest_answers": phtest}),
                   "answers": answers, "full_evaluation_answers": full,
                   "answer_share_of_full_evaluation": answers / full,
                   "subset_sha256": subset_sha256(plan.harm, plan.overrefusal)},
        "cold_start": {"fresh_session": True, "assets_loaded_before_job": [],
                       "timer_origin": settings["timing"]["origin"], "clock": settings["timing"]["clock"],
                       "origin_utc": dt.datetime.fromtimestamp(origin_utc_epoch, dt.timezone.utc).isoformat(
                           timespec="milliseconds"),
                       "process_age_at_origin_seconds": process_age_at_origin},
        "timeline_seconds": dict(marks),
        "job_span_seconds": end,
        "job_span_with_process_start_seconds": None if process_age_at_origin is None else end + process_age_at_origin,
        "phase_seconds": {"before_training": marks["train_start"],
                          "training_job": marks["train_end"] - marks["train_start"],
                          "lean_evaluation": marks["lean_end"] - marks["lean_start"],
                          "after_lean_evaluation": end - marks["lean_end"]},
        "stages": rows,
        "stage_seconds_total": stage_total,
        "seconds_by_category": by_category,
        "unmapped_stages": sorted({r["stage"] for r in rows if r["category"] == "unmapped"}),
        "outside_stages_seconds": end - stage_total,
        "per_answer_seconds": {
            "sampled_harm": _per(_stage_seconds(rows, LEAN_DIR, "sample"), summary["harm_sampled_answers"]),
            "guard_sampled_harm": _per(_stage_seconds(rows, LEAN_DIR, "guard_samples"), summary["harm_sampled_answers"]),
            "greedy_overrefusal": _per(_stage_seconds(rows, LEAN_DIR, "generate"), summary["overrefusal_greedy_answers"]),
            "guard_overrefusal": _per(_stage_seconds(rows, LEAN_DIR, "guard"), summary["overrefusal_greedy_answers"]),
            "task_loss_row": _per(_stage_seconds(rows, LEAN_DIR, "query_loss"), summary["task_rows"]),
            **({} if plan.oext is None else {
                "greedy_oext_phtest": _per(_stage_seconds(rows, LEAN_DIR, "oext_generate"), phtest),
                "guard_oext_phtest": _per(_stage_seconds(rows, LEAN_DIR, "oext_guard"), phtest)})},
        "training": {"run_dir": TRAIN_DIR, "complete_sha256": receipt["complete_sha256"], "step": state["step"],
                     "examples_seen": state["examples_seen"], "trajectory_cost": state["trajectory_cost"],
                     "target_adapter_fingerprint": state["adapter_fingerprint"],
                     "expected_adapter_fingerprint": plan.expected_fingerprint,
                     "adapter_fingerprint_equal": (None if plan.expected_fingerprint is None
                                                   else state["adapter_fingerprint"] == plan.expected_fingerprint),
                     "edit": result["trajectory"].get("edit")},
        "lean_unit": {"run_dir": LEAN_DIR, "complete_sha256": sha256_file(unit_dir / COMPLETE),
                      "sealed_dir": settings["seal"]["sealed_dir"], "sealed_files": summary["sealed_files"],
                      "rng_consumed_inside_evaluation_then_restored":
                          summary["rng_consumed_inside_evaluation_then_restored"]},
        "seal": settings["seal"]["rule"],
        "slot_note": settings["timing"]["slot_note"],
        "completed_utc": utc_now(),
    }
    data = canonical_json(record)
    hits = _text_hits(data, texts)
    if hits:
        raise RunError(f"the record holds {hits} job texts; it is not written")
    write_atomic(out / RECORD_FILE, data)
    return record


# ----- verification -------------------------------------------------------------------------------------------


def verify_c0(out_dir: str | Path) -> list[str]:
    """Problems with a finished lean job folder (an empty list: it verifies). It checks the training unit and its
    chain (the engine's checks), the lean unit's files, the receipt, the record's hashes of both units and of every
    sealed file, and that nothing else lies in the folder. It reads no sealed file's contents beyond its hash."""
    out = Path(out_dir)
    record_path = out / RECORD_FILE
    if not record_path.is_file():
        return [f"no {RECORD_FILE}: the job did not finish"]
    try:
        record = s1.strict_json(record_path.read_bytes())
    except (s1.Refusal, ValueError):
        return [f"{RECORD_FILE} is not strict JSON"]
    if not isinstance(record, dict) or record.get("kind") != RECORD_KIND:
        return [f"{RECORD_FILE} is not a {RECORD_KIND}"]
    train, unit = out / TRAIN_DIR, out / LEAN_DIR
    problems = [f"train: {p}" for p in chain_problems(train)] if train.is_dir() else ["train: missing"]
    problems += [f"lean: {p}" for p in verify_files(unit)] if unit.is_dir() else ["lean: missing"]
    if problems:
        return problems
    if sha256_file(train / COMPLETE) != record["training"]["complete_sha256"]:
        problems.append("train: COMPLETE.json is not the record's")
    if sha256_file(unit / COMPLETE) != record["lean_unit"]["complete_sha256"]:
        problems.append("lean: COMPLETE.json is not the record's")
    if read_json(unit / RECEIPT_FILE).get("complete_sha256") != record["training"]["complete_sha256"]:
        problems.append("lean: the source receipt does not name the training unit")
    listed = record["lean_unit"]["sealed_files"]
    present = sorted(p.name for p in (unit / SEALED_DIR).iterdir()) if (unit / SEALED_DIR).is_dir() else []
    if present != sorted(listed):
        problems.append(f"lean: the sealed folder holds {len(present)} files, the record lists {len(listed)}")
    for name, info in sorted(listed.items()):
        path = unit / SEALED_DIR / name
        if not path.is_file() or sha256_file(path) != info["sha256"]:
            problems.append(f"lean: sealed/{name} is missing or not the record's")
    extra = sorted(p.name for p in out.iterdir() if p.name not in (TRAIN_DIR, LEAN_DIR, RECORD_FILE))
    if extra:
        problems.append(f"the folder holds {len(extra)} entries besides train, lean and the record")
    return problems


# ----- command line ---------------------------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python scripts/stage1_s1/lean_eval_job.py",
                                     description="B17: the lean-evaluation job that measures c0.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run", help="train one arm and run C-lean (cold start, timed)")
    p.add_argument("--job", required=True, help="the engine run-one job file (evaluate_bank null, code pinned)")
    p.add_argument("--prepared", required=True)
    p.add_argument("--recipe", required=True)
    p.add_argument("--out", required=True, help="a new folder; never replaced")
    p.add_argument("--registry", help="the trajectory registry the kit uses (optional; passed to run_one)")
    p.add_argument("--expect-adapter-fingerprint",
                   help="a known target-state adapter fingerprint to compare (recorded); required for an edit arm")
    p.add_argument("--oext-bank", help="O-ext: build_oext's bank file (oext_bank.json; status oext_pinned)")
    p.add_argument("--oext-record", help="O-ext: build_oext's sealed record (oext_record.json), pinned")
    p.add_argument("--w1-18-record", help="O-ext: W1-18's record (overrefusal_checks.json), when pinned")
    p = sub.add_parser("verify", help="verify a finished lean job folder")
    p.add_argument("--out", required=True)
    return parser


def _say(obj: object, stream=None) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False), file=stream or sys.stdout)


def _oext_arg(args: argparse.Namespace, settings: dict, oext_settings: Any) -> Any:
    """The O-ext part from the command line: when C-lean's O part is O-ext, the pinned O-ext settings (or the test's)
    and the given files through oext_eval.prepare (no model); otherwise no O-ext file may be given."""
    paths = (args.oext_bank, args.oext_record, args.w1_18_record)
    contents = settings["lean"]["contents"]
    if not (settings["lean"]["contents_options"][contents]["overrefusal_greedy"]
            and settings["lean"]["overrefusal_bank"]["status"] == "oext_pinned"):
        if any(p is not None for p in paths):
            raise s1.Refusal("--oext-bank, --oext-record and --w1-18-record belong to C-lean's O-ext part only")
        return None
    chosen = oext_settings if oext_settings is not None else oe.load_pinned_settings()
    return oe.prepare(chosen, bank_path=args.oext_bank, record_path=args.oext_record, w1_18_path=args.w1_18_record)


def main(argv: Sequence[str] | None = None, *, loaders: Any = None, oext_settings: Any = None) -> int:
    """The command line. ``loaders`` replaces the engine's real CUDA loaders and ``oext_settings`` the pinned O-ext
    settings (ENGINEERING FIXTURES in tests only)."""
    args = _parser().parse_args(argv)
    if args.command == "verify":
        problems = verify_c0(args.out)
        _say({"ok": not problems, "problems": len(problems), "messages": problems})
        return 0 if not problems else 1
    imports_done = _time.monotonic() - _ORIGIN
    try:
        settings, settings_sha = load_lean_settings()
        plan = prepare_c0_job(args.job, prepared_dir=args.prepared, recipe_path=args.recipe, out_dir=args.out,
                              settings=settings, settings_sha256=settings_sha,
                              expected_fingerprint=args.expect_adapter_fingerprint,
                              oext=_oext_arg(args, settings, oext_settings))
    except _INVALID as exc:
        _say({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, sys.stderr)
        return 2
    plan_checked = _time.monotonic() - _ORIGIN
    try:
        if loaders is None:
            from experiments.safety_selection.loaders import real_loaders

            loaders = real_loaders()
        session = runner.Session(plan.recipe, loaders)
        session_ready = _time.monotonic() - _ORIGIN
        record = execute_c0_job(plan, session, registry=args.registry, origin=_ORIGIN,
                                origin_utc_epoch=_ORIGIN_UTC_EPOCH, process_age_at_origin=_PROCESS_AGE_AT_ORIGIN,
                                marks={"imports_done": imports_done, "plan_checked": plan_checked,
                                       "session_ready": session_ready})
    except BaseException as exc:  # noqa: BLE001 - every failure is reported with its status
        _say({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, sys.stderr)
        made = Path(args.out).exists()
        if isinstance(exc, KeyboardInterrupt) or made:
            return 1
        return 2 if isinstance(exc, _INVALID) else 1
    _say({"ok": True, "out": str(args.out), "record_sha256": sha256_file(Path(args.out) / RECORD_FILE),
          "contents": record["contents"]["option"], "answers": record["subset"]["answers"],
          "job_span_seconds": record["job_span_seconds"], "stage_seconds_total": record["stage_seconds_total"],
          "sealed_files": len(record["lean_unit"]["sealed_files"]),
          "adapter_fingerprint_equal": record["training"]["adapter_fingerprint_equal"]})
    return 0


if __name__ == "__main__":
    sys.exit(main())
