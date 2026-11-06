"""The 7-8B kit's jobs of one host, in order (runs on the pod after the bootstrap and the preflight; K2 of the
readiness plan's T4; the lead's ruling 11 KD3, KD5, KD11; the addendum's A1; the ADAPTATION of the stage-1 kit's
setup/job_runner_stage1.py, whose 1B kinds (W1-18, D-2, B10/B11, C1-C3, the O-ext pass, similarity, the plant pilot)
are not in this copy: block 0 runs ``arm`` and ``a0_arm`` under the family's main config, nothing else; K4b's scorer
block "sc" runs one job of rules_78b.SC_KINDS per pod, by ``sc_commands`` and ``run_sc_job`` below).

    venv/bin/python job_runner_stage1.py HOST [--dry-run [--remaining SECONDS] [--free-gb GB] [--s-obs X]]

Checks first (an identity failure refuses with an AssertionError before any job, as the stage-1 kit does: the pod is
not the planned one): no token variable or token file; this host has not run (no JOB-DONE.json); BOOTSTRAP-READY ok;
PREFLIGHT-DONE ok for the family's main config, and the preflight's verification.json present at PREFLIGHT-DONE's
``folder`` with PREFLIGHT-DONE's ``verification_sha256`` (the two documents of one preflight); the plan's family is
this pod's (kit-family.json, stage1_rules.kit_identity) and every job's; one engine per pod, the host's engine
stage1_rules.ENGINES[engine] and the packed engine's own code identity equal to it (G4); the main config at its byte
pin and its config SHA-256 (the engine's canonical hash) equal to plan.json's and rules_78b's; the prepared manifest
equal to the plan's pin and to the preflight's; sealed-files.json at the plan's pin with every listed file present.

Then the rule's key check (rules_78b.check_keys; KCR:147, A-V3) for every job, with the evaluation bank built from the
recipe (generation.max_new_tokens, generation.batch_size) and the packed bank's counts (the prepared manifest's dev
bank: the generated kinds arc_generation + harm + overrefusal + safety = 468 greedy prompts; harm 200 x
harm_samples.count 3 = 600 sampled answers; M: both prepared manifests) and required equal to what the preflight saw
(verification.json's full_length.max_new_tokens, full_length.batch, the generate and sample stages' bank_units).
A refused key (a kind that needs recipe S_78 while RECIPE_S is null, addendum A1; another GPU; another bank) is
RECORDED, not asserted: every job gets status ``deferred`` with the refusal's reason, deferral.json says why and
JOB-DONE.json carries ``stopped`` "refused". So the retrain kind (ruling 10, A2) refuses on the pod while RECIPE_S is
None, as it refuses at planning.

The per-job gate (KD3, KD5, KD11; rules_78b.job_decision with the preflight's TWO documents, PREFLIGHT-DONE.json and
verification.json): the governing stop from the pod timer's heartbeat (a missing or unreadable heartbeat stops the
host, ``heartbeat_unreadable``); the free space on the volume before each job (shutil.disk_usage of the run root;
below FREE_SPACE_MIN_GB refuses, KD5); s_pod from the preflight's fields (a missing field refuses, "none never
fits"; s_pod > 1.15 refuses before any job); the job's requirement at max(s_pod, s_obs) x upper_M + 30 min, never
below the sanity floor; a job that does not fit the remaining time defers this job and every later one, in order
(deferral.json, reason "remaining"). After each complete arm the runner reads that unit's progress.jsonl (generate
rows: batch seconds, rows, capped counts; never an answer) and sets s_obs = the slowest capped 32-row batch after the
first over BATCH_MAX, at least 1 (rules_78b.s_obs_from_progress, KD11, KCR:113); later arms use the largest s_obs
seen so far (a conservative reading of "later arms use max(s_pod, s_obs)"); s_obs > 1.15 defers the later arms (reason
"s_obs"); a progress record the rule cannot read (a generate row without an integer capped or rows, no 32-row batch,
no record at all; A-V1) refuses the later arms (reason "s_obs_record") and the lead records the case. Before a job its
edit file is checked against sealed-files.json, its job's SHA-256 and its engine arm, and the main config against its
pin; a mismatch stops the host (``sealed_file_mismatch``). A non-zero exit, or no new COMPLETE.json, is a crash: the
job is ``crashed``, later jobs ``not_started``, and the host stops.

Each job is one process under process_receipt.py: the engine's ``calibrate`` with the FAMILY'S MAIN config (P78:99;
stage1_rules.arm_commands; an edit arm with --edit edits/<SHA-256>.edit.json and its edit-<SHA-256> arm; a0 without).
No O-ext step runs at 7-8B (N's gate and the seed rule read the engine's own U only, Part 1 §3). After a complete
a0_arm job the readable job-I/a0-adapter-fingerprint.json is written (the stage-1 kit's K6: fingerprints and identity
hashes only).

Records: job-done/JOB-<i>.json per job and JOB-DONE.json at the end (plan_tool record-done's schema: index, kind, arm,
seed, status, engine, engine_sha256, unit, complete_sha256, outputs {relpath: SHA-256}, reason; plus this kit's
timing numbers requirement_s, remaining_s, free_gb, s_pod, s_obs, s, s_obs_after); job-I/cost-ledger.json (FR-10
stages in seconds). SR-2: no outcome file is read for a value. The runner hashes outputs, reads COMPLETE.json's
identity and fingerprint fields, states/e1/state.json's fingerprint and progress.jsonl's batch numbers; no U, no HB,
no O, no answer and no prompt text reaches a record or a printed line (the test walks every record and every line).
Last, the stop is shortened to 1 h from now when more remains.

--dry-run prints every job's commands (placeholders for values known only at run time) and writes nothing; with a
PREFLIGHT-DONE.json and its verification.json in the current folder it also prints rules_78b.pod_dry_run's decisions
(s_pod, s, the requirement and run/defer per job) at --remaining SECONDS (default: the heartbeat's remaining time,
else none, which never fits), --free-gb GB (default: this folder's volume) and --s-obs X (default 1.0).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
for _folder in (HERE, HERE.parent):                 # the pod: beside this script; the kit: one folder up
    if (_folder / "stage1_rules.py").is_file():
        sys.path.insert(0, str(_folder))
        break
import stage1_rules as rules  # noqa: E402
import rules_78b as r78  # noqa: E402

ROOT = pathlib.Path("/workspace/attribution-headroom")
HEARTBEAT = pathlib.Path("/workspace/.pod-timer/heartbeat.json")
ENGINE = list(rules.ENGINE_ARGV)
TOKEN_ENV_NAMES = rules.TOKEN_ENV_NAMES
ROUND = rules.ROUND_DIR
DATA = "data"                                         # the bundle's data root (mirrors the checkout's tmp/)
PREPARED = f"{DATA}/kt-prepared/{rules.PREPARED_NAME}" if rules.PREPARED_NAME else None   # None in the committed folder
SHORTEN_TO_S = 3600
LEDGER_FILE = "cost-ledger.json"
LEDGER_STAGES = ("setup", "training", "greedy_generation", "sampled_generation", "judging", "scoring",
                 "pod_overhead", "transform")
PROGRESS_FILE = "progress.jsonl"                      # the engine unit's batch record (KD11 reads its generate rows)
VERIFICATION_FILE = "verification.json"               # the preflight's second document, in PREFLIGHT-DONE's folder
BLOCK0_KINDS = tuple(rules.BLOCK_KINDS["0"])          # ("arm", "a0_arm")
GENERATED_KINDS = ("arc_generation", "harm", "overrefusal", "safety")   # the dev bank's generated items: 96+200+100+72
STEP_STAGE = (("-calibrate", "training"),)            # the engine's one step counts as training (its ledger splits it)
REFUSAL_REASONS = ("preflight", "free_space", "recipe_pin", "key", "s_obs_record", "kind", "rule")
DEFER_REASONS = ("remaining", "s_obs")


class Unrunnable(Exception):
    """A job the kit cannot run as planned (named before anything starts)."""


class Refusal(Exception):
    """A rule refusal before a job (rules_78b.Refused, classified): recorded as a deferral with its reason."""

    def __init__(self, reason: str, text: str):
        super().__init__(text)
        self.reason, self.text = reason, text


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def next_attempt(root: pathlib.Path, prefix: str) -> int:
    """The next unused attempt number N of folders or files PREFIXN* under root (1 when none exists)."""
    parent = (root / prefix).parent
    stem = pathlib.Path(prefix).name
    numbers = []
    if parent.is_dir():
        for p in parent.glob(stem + "*"):
            tail = p.name[len(stem):].split(".")[0]
            if tail.isdigit():
                numbers.append(int(tail))
    return max(numbers, default=0) + 1


engine_arm = rules.engine_arm


def edit_bundle(job: dict) -> str | None:
    edit = job.get("edit")
    return f"edits/{edit['sha256']}.edit.json" if edit else None


def family_of_plan(plan: dict) -> str:
    """This pod's family (kit-family.json beside stage1_rules, or the working copy's name), which plan.json must name."""
    return rules.family_or_refuse(plan.get("family"))


def recipe_path(job: dict) -> str:
    """Every block-0 job runs the family's main config (recipe "B"; P78:99)."""
    if job.get("recipe") != "B":
        raise Unrunnable(f"job of kind {job.get('kind')!r} names recipe {job.get('recipe')!r}: a 7-8B arm runs under the "
                         "family's main config only (recipe B; P78:99)")
    return rules.REC


def preflight_recipe(h: dict) -> str:
    """The host's preflight recipe: the family's main config (block 0's one recipe)."""
    return rules.REC


def job_commands(plan: dict, host: str, index: int, root: pathlib.Path, units: dict | None = None,
                 sealed_doc: dict | None = None) -> list[tuple[str, list[str]]]:
    """(receipt name, argv) of job ``index``: the engine's calibrate under the main config (stage1_rules.arm_commands).
    A kind that needs recipe S_78 (the retrain, A1's pass) refuses through rules_78b.recipe_s_or_refuse while the pin
    is null (addendum A1), and has no command in this round even once it is filled; any other kind outside block 0
    refuses (its single-job pod comes in a later round, KD6)."""
    job = plan["hosts"][host]["jobs"][index]
    kind = job["kind"]
    family = family_of_plan(plan)
    if plan["hosts"][host].get("block") == r78.SC_BLOCK:   # K4b: the scorer block's single-job pods
        return sc_commands(plan, host, index, root, units or {}, sealed_doc if sealed_doc is not None else load_sealed(root))
    if kind in r78.S78_KINDS:
        try:
            r78.recipe_s_or_refuse(family)
        except r78.Refused as exc:
            raise Unrunnable(f"job {index} ({kind}): {exc}") from None
        raise Unrunnable(f"job {index} ({kind}): the {kind} kind's command line is a later round's (after S_78 is pinned "
                         "and its pod is planned; ruling 10, addendum A2)")
    if kind not in BLOCK0_KINDS:
        raise Unrunnable(f"job {index} ({kind}): not a block-0 kind ({', '.join(BLOCK0_KINDS)}); the single-job kinds "
                         "come in a later round (KD6)")
    if PREPARED is None:
        raise Unrunnable(f"job {index} ({kind}): this kit folder names no family (KD7)")
    try:
        steps = rules.arm_commands(job, PREPARED, family)
    except ValueError as exc:
        raise Unrunnable(f"job {index} ({kind}): {exc}") from None
    return [(f"job-{index}-{name}", list(argv)) for name, argv in steps]


def load_sealed(root: pathlib.Path) -> dict:
    path = root / "sealed-files.json"
    return json.loads(path.read_text()) if path.is_file() else {"files": {}, "inputs": {}}


def oext_fallback(plan: dict) -> bool:
    """No O-ext step exists at 7-8B, so no fallback (c) either: always False. Kept by name because orchestrate.py's
    check_plan (the launch path, K3's) reads it; the stage-1 kit's record has no 7-8B counterpart."""
    return False


def sealed_paths(job: dict, h: dict | None = None, index: int = 0, sealed_doc: dict | None = None,
                 fallback: bool = False) -> list[str]:
    """Every bundle file a block-0 job uses: the main config, the prepared manifest files and the edit file
    (``fallback`` is the stage-1 signature's fifth argument, which orchestrate.py still passes; nothing reads it)."""
    paths = [rules.REC] if rules.REC else []
    if PREPARED:
        paths += [f"{PREPARED}/manifest.json", f"{PREPARED}/manifest.sha256"]
    if job.get("edit"):
        paths.append(edit_bundle(job))
    if job.get("kind") in r78.SC_KINDS and (h or {}).get("block") == r78.SC_BLOCK:   # K4b
        paths += sc_paths(job, sealed_doc if sealed_doc is not None else {"files": {}, "inputs": {}})
    return paths


def sealed_check(job: dict, sealed: dict, root: pathlib.Path, h: dict | None = None, index: int = 0,
                 sealed_doc: dict | None = None) -> list[str]:
    """Names of the job's files that are not listed or differ from sealed-files.json; an edit file must also hash to
    its job's edit SHA-256 and engine arm (edit-<SHA-256 of its bytes>); the main config to its byte pin."""
    bad = []
    for rel in sealed_paths(job, h, index, sealed_doc):
        path = root / rel
        if rel not in sealed or not path.is_file() or sha(path) != sealed[rel]:
            bad.append(rel)
    if rules.REC and (not (root / rules.REC).is_file() or sha(root / rules.REC) != rules.RECIPE_PINS.get(rules.REC)):
        bad.append(f"{rules.REC} (its pin)")
    if job.get("edit"):
        path = root / edit_bundle(job)
        if not path.is_file() or sha(path) != job["edit"]["sha256"] or "edit-" + sha(path) != engine_arm(job):
            bad.append(f"{edit_bundle(job)} (its arm)")
    return bad


def remaining(now: dt.datetime) -> float | None:
    """Seconds to the governing stop of the pod timer; None when the heartbeat is missing or unreadable."""
    try:
        stop = json.loads(HEARTBEAT.read_text())["governing"]["stop_at_utc"]
        return (dt.datetime.fromisoformat(stop.replace("Z", "+00:00")) - now).total_seconds()
    except Exception:  # noqa: BLE001 - every failure means unknown, which never fits
        return None


def shorten(remaining_s: float | None) -> bool:
    return remaining_s is not None and remaining_s > SHORTEN_TO_S


def free_space_gb(path: pathlib.Path) -> float | None:
    """GB (10^9 bytes, RunPod's unit) free on the volume that holds ``path``; None when it cannot be read (not ok)."""
    try:
        return shutil.disk_usage(path).free / 1e9
    except OSError:
        return None


def complete_attempts(root: pathlib.Path, pattern: str) -> set[str]:
    return {str(p.parent.relative_to(root)) for p in root.glob(f"{pattern}/COMPLETE.json")}


def _engine_identity() -> str:
    from experiments.safety_selection.common import code_identity
    return code_identity()["sha256"]


def _recipe_config_sha(path: pathlib.Path) -> str:
    from experiments.safety_selection.config import config_sha256, load_recipe
    return config_sha256(load_recipe(str(path)))


# ===== the evaluation bank (KCR:147; the T2 fixer's and re-verifier's jobs for T4) ==================================
def bank_record(root: pathlib.Path, recipe_rel: str, prepared_rel: str) -> dict:
    """The bank rules_78b.check_keys takes, from the recipe's generation block (max_new_tokens, batch_size,
    harm_samples.count) and the packed prepared set's manifest.json counts (banks.dev: the generated kinds give the
    greedy prompts; harm x the sample count gives the sampled answers). Counts and settings only; no bank row is read."""
    recipe = json.loads((root / recipe_rel).read_text())
    gen = recipe["generation"]
    manifest = json.loads((root / prepared_rel / "manifest.json").read_text())
    dev = manifest["banks"]["dev"]
    greedy = sum(int(dev[k]) for k in GENERATED_KINDS)
    return {"cap_tokens": int(gen["max_new_tokens"]), "greedy_prompts": greedy,
            "harm_samples": int(dev["harm"]) * int(gen["harm_samples"]["count"]), "generation_batch": int(gen["batch_size"])}


def bank_from_verification(verification: dict) -> dict:
    """The same four numbers as the preflight saw them (M: the 17 measured verification.json files carry
    full_length.max_new_tokens, full_length.batch and the generate and sample stages' bank_units)."""
    v = verification if isinstance(verification, dict) else {}
    full = v.get("full_length") if isinstance(v.get("full_length"), dict) else {}
    timing = v.get("evaluation_timing") if isinstance(v.get("evaluation_timing"), dict) else {}
    projection = timing.get("projection_to_dev_bank") if isinstance(timing.get("projection_to_dev_bank"), dict) else {}
    stages = projection.get("stages") if isinstance(projection.get("stages"), dict) else {}
    generate = stages.get("generate") if isinstance(stages.get("generate"), dict) else {}
    sample = stages.get("sample") if isinstance(stages.get("sample"), dict) else {}
    return {"cap_tokens": full.get("max_new_tokens"), "greedy_prompts": generate.get("bank_units"),
            "harm_samples": sample.get("bank_units"), "generation_batch": full.get("batch")}


def gpu_name_of(verification: dict) -> str | None:
    env = verification.get("environment") if isinstance(verification, dict) else None
    cuda = env.get("cuda") if isinstance(env, dict) else None
    return cuda.get("name") if isinstance(cuda, dict) else None


def load_verification(root: pathlib.Path, pre: dict) -> dict:
    """The preflight's verification.json at PREFLIGHT-DONE's ``folder``, which must hash to its ``verification_sha256``
    (the two documents are one preflight's). AssertionError otherwise."""
    folder = pre.get("folder")
    assert isinstance(folder, str) and folder and "/" not in folder.strip("/") and ".." not in folder, \
        "PREFLIGHT-DONE.json names no preflight folder"
    path = root / folder / VERIFICATION_FILE
    assert path.is_file(), f"the preflight's {VERIFICATION_FILE} is missing from {folder}"
    assert sha(path) == pre.get("verification_sha256"), \
        f"the preflight's {VERIFICATION_FILE} differs from PREFLIGHT-DONE.json's verification_sha256"
    doc = json.loads(path.read_text())
    assert isinstance(doc, dict), f"the preflight's {VERIFICATION_FILE} is not a record"
    return doc


_TOKEN_PATHS = None


def token_paths():
    """setup/download_models_stage1.py (beside this script on the pod and in the kit), loaded by path once: its
    no_token_left() resolves the token file and stored_tokens as huggingface_hub does (verify-K-gated D6; the
    re-verifier's RV2-8). Loaded at the first call, not at import (its import sets two HF_HUB_* switches)."""
    global _TOKEN_PATHS
    if _TOKEN_PATHS is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("download_models_stage1_for_runner",
                                                      HERE / "download_models_stage1.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _TOKEN_PATHS = module
    return _TOKEN_PATHS


def preflight_checks(plan: dict, host: str, pre: dict, root: pathlib.Path) -> tuple[dict, dict, dict]:
    """Refuse (AssertionError) before any job unless the pod is the planned one; returns (sealed-files.json's doc,
    the preflight's verification.json, the bank built from the recipe and the packed prepared set)."""
    h = plan["hosts"][host]
    jobs = h["jobs"]
    family = family_of_plan(plan)
    present = [name for name in TOKEN_ENV_NAMES if os.environ.get(name)]
    assert not present, f"a token is present: a token variable is set: {present}"
    try:                                       # RV2-8: the library's own token paths (HF_TOKEN_PATH, else HF_HOME/token,
        token_paths().no_token_left()          # and stored_tokens), the one resolver the download and preflight use (D6)
    except SystemExit as exc:
        raise AssertionError(f"a token is present: {exc}") from None
    assert not (root / "JOB-DONE.json").exists(), "this host already ran its jobs"
    assert json.loads((root / "BOOTSTRAP-READY.json").read_text())["ok"] is True, "bootstrap not ready"
    assert pre.get("ok") is True and pre.get("recipe") == preflight_recipe(h), \
        "the preflight did not pass for the host's recipe"
    verification = load_verification(root, pre)
    assert all(j.get("family", family) == family for j in jobs), f"a job of another family than {family}'s on this pod"
    assert h["engine_sha256"] == engine_pin(h["engine"]), "the host's engine is not a pinned engine (G4)"
    assert all(j["engine"] == h["engine"] for j in jobs), "two engines on one pod (G4)"
    assert _engine_identity() == h["engine_sha256"], "engine code differs from the plan (G4)"
    rec = rules.REC
    assert rec in plan.get("recipes", {}), f"recipe {pathlib.Path(rec).name} is not in plan.json"
    assert sha(root / rec) == rules.RECIPE_PINS[rec], f"recipe {pathlib.Path(rec).name} differs from its pin"
    config = _recipe_config_sha(root / rec)
    assert config == plan["recipes"][rec]["config_sha256"] == rules.REC_CONFIG_SHA256, \
        f"recipe {pathlib.Path(rec).name} differs from the plan (its config SHA-256)"
    assert verification.get("recipe_sha256") == config, "the preflight ran another recipe than the plan's"
    for job in jobs:                                   # K4b: an S_78 job's config, once its pin is filled (A1)
        if job.get("recipe") == "S" and r78.RECIPE_S.get(family) is not None:
            s78 = job.get("recipe_s78") or {}
            path = s78.get("path")
            assert isinstance(path, str) and path in plan.get("recipes", {}), "the S_78 config is not in plan.json"
            assert sha(root / path) == plan["recipes"][path]["sha256"], "the S_78 config differs from plan.json's bytes"
            assert _recipe_config_sha(root / path) == plan["recipes"][path]["config_sha256"] == \
                s78.get("config_sha256") == r78.RECIPE_S[family], "the S_78 config differs from its pin (A1)"
    name, digest = next(iter(sorted(plan["prepared"].items())))
    assert name == rules.PREPARED_NAME and digest == rules.PREPARED_MANIFESTS[name], "the plan's prepared set is not the family's"
    assert (root / PREPARED / "manifest.sha256").read_text().strip() == digest, "prepared data differ from the plan"
    assert sha(root / PREPARED / "manifest.json") == digest, "the prepared manifest differs from its own hash file"
    assert verification.get("manifest_sha256") == digest, "the preflight ran on another prepared set than the plan's"
    assert sha(root / "sealed-files.json") == h["sealed_files_sha256"], "sealed-files.json differs from the plan"
    doc = json.loads((root / "sealed-files.json").read_text())
    sealed = doc["files"]
    bad = [rel for rel, d in sealed.items() if not (root / rel).is_file() or sha(root / rel) != d]
    assert not bad, f"{len(bad)} sealed file(s) missing or changed"
    bank = bank_record(root, rec, PREPARED)
    seen = bank_from_verification(verification)
    assert bank == seen, (f"the packed bank and recipe {sorted(bank.items())} differ from what the preflight saw "
                          f"{sorted(seen.items())}")
    return doc, verification, bank


def key_refusal(plan: dict, host: str, verification: dict, bank: dict) -> tuple[int, str] | None:
    """(the first job's index, why) that rules_78b.check_keys refuses on this pod, or None: the kind, the recipe (the
    main config's config SHA-256 from plan.json, which preflight_checks tied to the pod's file), the engine, the GPU
    the preflight saw, the prepared manifest and the bank."""
    h = plan["hosts"][host]
    family = family_of_plan(plan)
    recipe = plan["recipes"][rules.REC]["config_sha256"]
    manifest = next(iter(sorted(plan["prepared"].values())))
    for i, job in enumerate(h["jobs"]):
        key = (job.get("recipe_s78") or {}).get("config_sha256") if job.get("recipe") == "S" else recipe   # K4b (A1)
        try:
            r78.check_keys(family, job["kind"], key, h["engine_sha256"], gpu_name_of(verification), manifest, bank)
        except r78.Refused as exc:
            return i, f"job {i} ({job['kind']}): {exc}"
    return None


def refusal_reason(family: str, pre: dict, verification: dict, job: dict, free_gb) -> str:
    """Which rule refused, in rules_78b.job_decision's order: the preflight's fields or speed, the free space, a null
    recipe pin, else the rule itself."""
    try:
        r78.speed_factor(family, r78.preflight_fields(pre, verification))
    except r78.Refused:
        return "preflight"
    if not r78.free_space_ok(free_gb):
        return "free_space"
    if job["kind"] in r78.S78_KINDS or job["kind"] in r78.BQI_KINDS:
        return "recipe_pin"
    return "rule"


# ===== K4b: the scorer block's single-job pods (ruling 11 KD6, KD10; the check's C1, M1; A1, A2, A8, A13; PP1-PP16) =====
# Each pod of the block "sc" runs ONE job of rules_78b.SC_KINDS. The commands are scripts/scale78b/SCORERS-78B.md
# section 2's (the scorer layer's map), with every input a packed, sealed file whose SHA-256 is the job's plan.json pin
# (job["inputs"], fixed at init-block sc from the kit's and the scorer layer's pins). The wrapper kinds run
# scripts/scale78b/scorers_78b.py with -I -B (the brief's form); the record keeps counts and hashes only: each output's
# SHA-256, a unit's COMPLETE.json SHA-256 and fingerprints, and from each wrapper call's wrapper_78b_record.json its
# exit_code, doses.fallback_fired, doses.kept and doses.top_dose (no U, no answer, no prompt, no row id).
# Round 4b: every unit the runner records (the retrain, a1_pass, o_only_with_regenerate's regenerated unit) is checked
# by the engine's verify, a non-zero exit a crash, as run_job does (the core verifier's D2); c0 is unitless (PP18: its
# outputs, B17's OUT/train and OUT/lean and OUT/c0_record.json, are hashed under its job folder); PP17's
# o_only_with_regenerate regenerates a reused a0 side unit (train only), verifies it, checks it against the side unit's
# COMPLETE.json fingerprints (the stage-1 kit's J2 / LN-12 acceptance; a unit that differs is complete with acceptance
# false and reason LS-04, and its O-ext pass does not run), then runs the O-ext pass on its e1 state.
SC_PY = ["venv/bin/python", "-I", "-B"]                   # the scorer wrapper (SCORERS-78B.md: "-I -B as the brief says")
PY_B = ["venv/bin/python", "-B"]
RETRAIN_ROOT = "rescore"                                  # the retrain's and A1's pass's own run root (own registry)
SC_UNIT_KINDS = ("retrain", "a1_pass", "o_only_with_regenerate")   # the kinds that write an engine unit (verified)
SC_FINGERPRINT_KINDS = ("retrain", "o_only_with_regenerate")       # train-only units: their q and e1 fingerprints
#                                                           (the certificate compares them on the Mac; ruling 10)
WRAPPER_RECORD_KEYS = {"exit_code": int, "fallback_fired": bool, "kept": int, "top_dose": str}
ACCEPT_FILE = "regeneration-acceptance.json"             # PP17's acceptance record (fingerprints and identities only)
ACCEPT_KIND = "stage1-78b regeneration acceptance"
LS04 = "LS-04"                                           # the stage-1 kit's reason for a regeneration that differs
C0_RECORD = "c0_record.json"                             # B17's record (R: scripts/stage1_s1/lean_eval_job.py:147)
ACCEPT_POINTS = ("q", "e1")
ACCEPT_FINGERPRINTS = ("adapter_fingerprint", "optimizer_fingerprint")
ACCEPT_IDENTITY = ("training_identity", "manifest_sha256")


def engine_pin(engine: str) -> str | None:
    """The pinned identity of ``engine`` (rules_78b.engine_sha: X, or Y once ENGINE_Y is filled), else None."""
    try:
        return r78.engine_sha(engine)
    except r78.Refused:
        return None


def sc_paths(job: dict, sealed_doc: dict) -> list[str]:
    """The bundle files a scorer-block job uses beyond the main config and the prepared manifest: its code
    (stage1_rules.scorer_code), the S_78 config of an S_78 job, and every file of its named inputs (a folder input:
    every sealed file under it)."""
    files, inputs = dict(sealed_doc.get("files") or {}), dict(sealed_doc.get("inputs") or {})
    paths = list(rules.scorer_code(job["kind"]))
    if job.get("recipe") == "S" and (job.get("recipe_s78") or {}).get("path"):
        paths.append(job["recipe_s78"]["path"])
    for name in rules.sc_input_names(job["kind"], job.get("seed")) if job["kind"] in rules.SC_INPUTS else ():
        rel = inputs.get(name)
        if rel is None:
            paths.append(f"inputs/{name} (not packed)")
        elif name in rules.SC_FOLDER_INPUTS:
            paths += sorted(f for f in files if f.startswith(rel.rstrip("/") + "/")) or [f"{rel}/COMPLETE.json"]
        else:
            paths.append(rel)
    return paths


def sc_inputs(job: dict, index: int, sealed_doc: dict) -> dict:
    """name -> (bundle path, SHA-256) of the job's named inputs, each equal to its plan.json pin (a folder input by
    its COMPLETE.json). Unrunnable when an input is not packed, its pin is null, or the packed file differs."""
    files, inputs = dict(sealed_doc.get("files") or {}), dict(sealed_doc.get("inputs") or {})
    pins = job.get("inputs") or {}
    out = {}
    for name in rules.sc_input_names(job["kind"], job.get("seed")):
        pin, rel = pins.get(name), inputs.get(name)
        if rules.hex64(pin) is None:
            raise Unrunnable(f"job {index} ({job['kind']}): the input {name!r} has no pin in plan.json (A13)")
        if rel is None:
            raise Unrunnable(f"job {index} ({job['kind']}): the input {name!r} is not packed")
        packed = files.get(f"{rel.rstrip('/')}/COMPLETE.json") if name in rules.SC_FOLDER_INPUTS else files.get(rel)
        if packed != pin:
            raise Unrunnable(f"job {index} ({job['kind']}): the packed input {name!r} differs from the plan's pin")
        out[name] = (rel, pin)
    return out


def sc_recipe(plan: dict, job: dict, index: int, family: str) -> str:
    """The job's config path: the main config (recipe "B"; PP1 for the untuned pass and the anchor job), or the
    family's S_78 config (recipe "S"; A1), which must be RECIPE_S's pin and plan.json's."""
    if job.get("recipe") == "B":
        return rules.REC
    if job.get("recipe") != "S":
        raise Unrunnable(f"job {index} ({job['kind']}): recipe {job.get('recipe')!r} is neither the main config nor S_78")
    try:
        pin = r78.recipe_s_or_refuse(family)
    except r78.Refused as exc:
        raise Unrunnable(f"job {index} ({job['kind']}): {exc}") from None
    s78 = job.get("recipe_s78") or {}
    path = s78.get("path")
    if s78.get("config_sha256") != pin or ((plan.get("recipes") or {}).get(path) or {}).get("config_sha256") != pin:
        raise Unrunnable(f"job {index} ({job['kind']}): the job's S_78 config is not RECIPE_S's pin (A1)")
    return path


def _engine_unit(kind: str, label: str, job: dict, index: int, root: pathlib.Path, rec: str, folder: str,
                 registry: str, arm: list[str]) -> list:
    """make-job run-one (train only, --pin-code) and run-one: the stage-1 kit's J2/J20 form (a regenerate into round1/,
    the retrain into rescore/ with its own registry)."""
    seed, tag = str(job["seed"]), f"job-{index}"
    n = next_attempt(root, f"jobs/{kind}-{seed}-{label}-a")
    job_file = f"jobs/{kind}-{seed}-{label}-a{n}.json"
    out = f"{folder}/{seed}-{label}-a{next_attempt(root, f'{folder}/{seed}-{label}-a')}"
    make = [*ENGINE, "make-job", "run-one", "--prepared", PREPARED, "--recipe", rec, "--split", "dev", *arm,
            "--seed", seed, "--role", "development", "--target", "e1", "--pin-code", "--out", job_file]
    return [(f"{tag}-make-job", make),
            (f"{tag}-run-one", [*ENGINE, "run-one", "--job", job_file, "--prepared", PREPARED, "--recipe", rec,
                                "--out", out, "--registry", registry])]


def sc_commands(plan: dict, host: str, index: int, root: pathlib.Path, units: dict, sealed_doc: dict) -> list:
    """(receipt name, argv) of a scorer-block job (SCORERS-78B.md section 2; the stage-1 kit's J2, J3, J5-J8, J11, J20,
    J21 forms; Gate B's anchor job)."""
    h = plan["hosts"][host]
    job = h["jobs"][index]
    kind, family = job["kind"], family_of_plan(plan)
    if kind not in r78.SC_KINDS:
        raise Unrunnable(f"job {index} ({kind}): not a kind of the scorer block ({', '.join(r78.SC_KINDS)})")
    if len(h["jobs"]) != 1:
        raise Unrunnable(f"job {index} ({kind}): a scorer-block pod holds one job (KD6)")
    if PREPARED is None:
        raise Unrunnable(f"job {index} ({kind}): this kit folder names no family (KD7)")
    rec = sc_recipe(plan, job, index, family)
    ins = sc_inputs(job, index, sealed_doc)
    tag, out, p = f"job-{index}", f"job-{index}", PREPARED
    wrap = [*SC_PY, rules.WRAPPER]

    def ps(name: str) -> str:
        return f"{ins[name][0]}:{ins[name][1]}"

    if kind == "anchor":
        return [(f"{tag}-anchor", [*PY_B, rules.ANCHOR_SCRIPT, "--prompts", ins["anchor_prompts"][0], "--recipe", rec,
                                   "--out", f"{out}/anchors"])]
    if kind == "untuned_answers":                        # PP1: REC and recipe S both the main config; PP2: two calls
        common = [*wrap, "untuned_answers", "--family", family, "--recipe", rec, "--recipe-s", rec]
        return [(f"{tag}-untuned-s3", [*common, "--list", f"s3={ps('list:s3')}", "--loss", f"s1={ps('loss:s1')}",
                                       "--loss", f"s3_safe={ps('loss:s3_safe')}", "--out", f"{out}/{rules.UNTUNED_CALLS[0]}"]),
                (f"{tag}-untuned-s4", [*common, "--list", f"s4={ps('list:s4')}", "--out", f"{out}/{rules.UNTUNED_CALLS[1]}"])]
    if kind == "rep_pass":                               # REQ-3's two passes (the stage-1 kit's J5), recipe S_78
        common = [*wrap, "rep_pass", "--family", family, "--prepared", p, "--recipe", rec, "--anchors",
                  ins["anchor_bank"][0]]
        return [(f"{tag}-representation", [*common, "--pool", ps("pool:s3_safe"), "--out", f"{out}/representation"]),
                (f"{tag}-representation-s3-orig", [*common, "--pool", ps("pool:s3_orig"), "--pools-only",
                                                   "--out", f"{out}/representation-s3-orig"])]
    if kind == "l1_scan":
        return [(f"{tag}-l1-scan", [*wrap, "l1_scan", "--family", family, "--prepared", p, "--recipe", rec,
                                    "--anchors", ins["anchor_bank"][0], "--out", f"{out}/l1-scan"])]
    if kind == "classifier":                             # PP4: under S_78, no --pool at 7-8B (EM-4)
        return [(f"{tag}-classifier", [*wrap, "classifier", "--family", family, "--prepared", p, "--recipe", rec,
                                       "--anchors", ins["anchor_bank"][0], "--out", f"{out}/classifier"])]
    if kind == "o_only":                                 # M1: theta0, the O-ext pass's --untuned route
        if job.get("arm") != "theta0":
            raise Unrunnable(f"job {index} (o_only): the scorer block's O-only pass is theta0's (the untuned model)")
        return [(f"{tag}-oext", [*PY_B, r78.OEXT_UNIT_SCRIPT, "run", "--untuned", "--prepared", p, "--recipe", rec,
                                 "--oext-bank", ins["oext_bank"][0], "--oext-record", ins["oext_record"][0],
                                 "--out", f"{out}/oext"])]
    if kind == "o_only_with_regenerate":                 # PP17: regenerate, (verify, accept: run_sc_job), O-ext on e1
        if job.get("arm") != "a0":
            raise Unrunnable(f"job {index} (o_only_with_regenerate): it regenerates a reused a0 side unit (ruling 7)")
        steps = _engine_unit(kind, "a0-regen", job, index, root, rec, ROUND, f"{ROUND}/registry.jsonl", ["--arm", "a0"])
        unit = steps[1][1][steps[1][1].index("--out") + 1]
        return [*steps, (f"{tag}-oext", [*PY_B, r78.OEXT_UNIT_SCRIPT, "run", "--run", unit, "--checkpoint", "e1",
                                         "--prepared", p, "--recipe", rec, "--oext-bank", ins["oext_bank"][0],
                                         "--oext-record", ins["oext_record"][0], "--out", f"{out}/oext"])]
    if kind == "retrain":                                # ruling 10: a0-1101 under S_78, to q and e1
        return _engine_unit(kind, "a0-retrain", job, index, root, rec, RETRAIN_ROOT, f"{RETRAIN_ROOT}/registry.jsonl",
                            ["--arm", "a0"])
    if kind == "c0":                                     # B17's X-pin check on N's R_1 at 1101 (the stage-1 kit's J11)
        if not job.get("edit") or rules.hex64(job.get("expect_fingerprint")) is None:
            raise Unrunnable(f"job {index} (c0): the plan carries no R_1 edit or no expected e1 fingerprint (C0_SOURCE)")
        steps = _engine_unit(kind, "R-c0", job, index, root, rec, ROUND, f"{ROUND}/registry.jsonl",
                             ["--edit", edit_bundle(job)])
        job_file = steps[0][1][-1]
        return [steps[0], (f"{tag}-lean", [*PY_B, r78.C0_SCRIPT, "run", "--job", job_file, "--prepared", p, "--recipe",
                                           rec, "--out", f"{out}/c0", "--registry", f"{out}/c0-registry.jsonl",
                                           "--expect-adapter-fingerprint", job["expect_fingerprint"],
                                           "--oext-bank", ins["oext_bank"][0], "--oext-record", ins["oext_record"][0]])]
    if kind == "a1_pass":                                # A1's attributes pass (the stage-1 kit's J21 form), PP3
        groups = job.get("groups")
        if not (isinstance(groups, list) and len(groups) == rules.UNITS and len(set(groups)) == len(groups)
                and all(isinstance(g, str) for g in groups)):
            raise Unrunnable(f"job {index} (a1_pass): plan.json carries no {rules.UNITS} distinct unit groups")
        state = ins["retrain_unit"][0]
        seed = str(job["seed"])
        n = next_attempt(root, f"jobs/a1_pass-{seed}-a")
        job_file, unit = f"jobs/a1_pass-{seed}-a{n}.json", f"{RETRAIN_ROOT}/{seed}-attributes-a{n}"
        make = [*ENGINE, "make-job", "attributes", "--prepared", p, "--recipe", rec, "--split", "dev", "--seed", seed,
                "--role", "development", *[a for c in ("q", "e1") for a in ("--a0-state", f"{c}={state}")],
                "--groups", ",".join(groups), "--anchors", ins["anchor_bank"][0], "--pin-code", "--out", job_file]
        return [(f"{tag}-make-job", make), (f"{tag}-attributes", [*ENGINE, "attributes", "--job", job_file, "--prepared",
                                                                   p, "--recipe", rec, "--out", unit])]
    raise Unrunnable(f"job {index} ({kind}): no command")   # pragma: no cover - SC_KINDS is closed above


def out_dirs(commands: list) -> list[str]:
    """The --out folder of every step that writes outputs (not a make-job's job file)."""
    dirs = []
    for name, argv in commands:
        if "--out" in argv and not name.endswith("-make-job"):
            dirs.append(argv[argv.index("--out") + 1])
    return dirs


def hashed_outputs(root: pathlib.Path, folders: list[str]) -> dict:
    """{relpath: SHA-256} of every file under the folders (names and hashes only; no file is read for a value)."""
    out = {}
    for folder in folders:
        base = root / folder
        if base.is_dir():
            for f in sorted(base.rglob("*")):
                if f.is_file() and not f.is_symlink():
                    out[str(f.relative_to(root))] = sha(f)
    return out


def wrapper_summary(root: pathlib.Path, folder: str) -> tuple[dict | None, str | None]:
    """(the counts of one wrapper call's wrapper_78b_record.json, None) or (None, why): exit_code, and from its doses
    block fallback_fired, kept and top_dose (a dose name), each type-checked; plus the record's SHA-256. The record
    is text-free by the scorer layer's rule; nothing else of it is read."""
    path = root / folder / rules.WRAPPER_RECORD
    try:
        doc = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        return None, f"{folder}/{rules.WRAPPER_RECORD} cannot be read ({type(exc).__name__})"
    if not isinstance(doc, dict) or doc.get("kind") != "scale78b scorer wrapper record":
        return None, f"{folder}/{rules.WRAPPER_RECORD} is not a scale78b scorer wrapper record"
    doses = doc.get("doses") if isinstance(doc.get("doses"), dict) else {}
    out = {"exit_code": doc.get("exit_code"), "fallback_fired": doses.get("fallback_fired"), "kept": doses.get("kept"),
           "top_dose": doses.get("top_dose"), "record_sha256": sha(path)}
    if type(out["exit_code"]) is not int:
        return None, f"{folder}/{rules.WRAPPER_RECORD}: exit_code is not an integer"
    for key in ("fallback_fired", "kept", "top_dose"):
        if out[key] is not None and type(out[key]) is not WRAPPER_RECORD_KEYS[key]:
            return None, f"{folder}/{rules.WRAPPER_RECORD}: doses.{key} has the wrong type"
    if out["top_dose"] is not None and not (out["top_dose"].startswith("s4") and len(out["top_dose"]) <= 12
                                           and out["top_dose"].replace("_", "").isalnum()):
        return None, f"{folder}/{rules.WRAPPER_RECORD}: doses.top_dose is not a dose name"
    return out, None


def unit_step(kind: str, commands: list) -> str | None:
    """The name of the step that writes a unit kind's engine unit (run-one, or attributes for A1's pass), else None."""
    if kind not in SC_UNIT_KINDS:
        return None
    suffix = "-attributes" if kind == "a1_pass" else "-run-one"
    found = [name for name, _ in commands if name.endswith(suffix)]
    return found[0] if len(found) == 1 else None


def verify_unit(root: pathlib.Path, unit: str, env: dict) -> dict:
    """The engine's verify of a recorded unit (run_job's form): {exit, tail} (names and hashes only, 600 characters)."""
    check = subprocess.run([*ENGINE, "verify", "--run", unit, "--prepared", PREPARED], env=env, cwd=root,
                           capture_output=True, text=True)
    return {"exit": check.returncode, "tail": (check.stdout + check.stderr)[-600:]}


def acceptance(root: pathlib.Path, unit: str, job: dict, index: int, ins: dict) -> dict:
    """PP17 (the stage-1 kit's J2 / LN-12): the regenerated unit against the reused side unit, field by field: every
    q and e1 adapter and optimizer fingerprint the side unit's COMPLETE.json lists (e1's adapter fingerprint required),
    its training identity and its prepared manifest (the side unit's COMPLETE.json is ruling 7's by its pin). Written to
    job-I/ACCEPT_FILE (fingerprints and identities only). ValueError when a record cannot be read."""
    name = rules.SIDE_COMPLETE.format(seed=job["seed"])
    rel, pin = ins[name]
    if sha(root / rel) != pin:
        raise ValueError("the side unit's COMPLETE.json differs from its pin")
    side, regen = json.loads((root / rel).read_text()), json.loads((root / unit / "COMPLETE.json").read_text())
    if not isinstance(side, dict) or not isinstance(regen, dict):
        raise ValueError("a COMPLETE.json is not an object")
    side_points = side.get("checkpoints") if isinstance(side.get("checkpoints"), dict) else {}
    regen_points = regen.get("checkpoints") if isinstance(regen.get("checkpoints"), dict) else {}
    if rules.hex64((side_points.get("e1") or {}).get("adapter_fingerprint")) is None:
        raise ValueError("the side unit's COMPLETE.json lists no e1 adapter fingerprint")
    fields = {}
    for point in ACCEPT_POINTS:
        listed = side_points.get(point) if isinstance(side_points.get(point), dict) else {}
        for key in ACCEPT_FINGERPRINTS:
            if key in listed:
                source, got = listed[key], (regen_points.get(point) or {}).get(key)
                fields[f"{point}.{key}"] = (source, got)
    side_id = side.get("identity") if isinstance(side.get("identity"), dict) else {}
    regen_id = regen.get("identity") if isinstance(regen.get("identity"), dict) else {}
    for key in ACCEPT_IDENTITY:                          # the side unit is ruling 7's by its pinned COMPLETE.json
        fields[f"identity.{key}"] = (side_id.get(key), regen_id.get(key))
    table = {f: {"source": src if rules.hex64(src) else None, "regenerated": got if rules.hex64(got) else None,
                 "equal": rules.hex64(src) is not None and src == got} for f, (src, got) in sorted(fields.items())}
    passed = all(v["equal"] for v in table.values())
    doc = {"kind": ACCEPT_KIND, "version": 1, "job": index, "arm": job["arm"], "seed": job["seed"], "unit": unit,
           "side_complete_sha256": pin, "regenerated_complete_sha256": sha(root / unit / "COMPLETE.json"),
           "fields": table, "pass": passed, "failure": None if passed else LS04}
    (root / f"job-{index}").mkdir(parents=True, exist_ok=True)
    (root / f"job-{index}" / ACCEPT_FILE).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return doc


def run_sc_job(plan: dict, host: str, index: int, root: pathlib.Path, units: dict, env: dict, sealed_doc: dict) -> dict:
    """Run one scorer-block job's steps; the record says complete or crashed, with counts and hashes only. The S4
    call's exit 3 (fewer than 48 kept: Part 1 section 10's pre-set fallback, no dose file) is the pass's own end, not a
    crash; every other non-zero exit is a crash. A unit kind's unit is verified by the engine right after the step that
    writes it (a non-zero verify is a crash); o_only_with_regenerate's acceptance check comes next, before its O-ext
    pass (PP17)."""
    job = plan["hosts"][host]["jobs"][index]
    kind = job["kind"]
    commands = sc_commands(plan, host, index, root, units, sealed_doc)
    exits, steps = {}, []
    record = {"exits": exits, "steps": steps}
    writes_unit = unit_step(kind, commands)
    if kind in SC_UNIT_KINDS and writes_unit is None:                  # pragma: no cover - sc_commands is closed
        return {**record, "status": "crashed", "why": "no step writes the job's unit"}
    summary = {"kind": kind}
    accepted = None
    for name, argv in commands:
        start = time.monotonic()
        done = subprocess.run(["python3", "process_receipt.py", "--out", name, "--", *argv], env=env, cwd=root)
        steps.append({"name": name, "seconds": round(time.monotonic() - start, 3), "exit": done.returncode})
        exits[name] = done.returncode
        s4_few = kind == "untuned_answers" and name.endswith("-untuned-s4") and done.returncode == 3
        if done.returncode and not s4_few:
            return {**record, "status": "crashed", "why": f"exit {done.returncode} in {name}"}
        if name != writes_unit:
            continue
        unit = argv[argv.index("--out") + 1]             # the engine unit this step wrote (round1/ or rescore/)
        if not (root / unit / "COMPLETE.json").is_file():
            return {**record, "status": "crashed", "why": "no COMPLETE.json in the job's unit"}
        record.update(unit=unit, complete_sha256=sha(root / unit / "COMPLETE.json"), verified=verify_unit(root, unit, env))
        if record["verified"]["exit"]:
            return {**record, "status": "crashed", "why": "the unit's verify failed"}
        if kind in SC_FINGERPRINT_KINDS:
            fields, why = unit_fingerprints(root, unit)
            if fields is None:
                return {**record, "status": "crashed", "why": why}
            summary["fingerprints"] = fields
        if kind == "o_only_with_regenerate":
            try:
                accepted = acceptance(root, unit, job, index, sc_inputs(job, index, sealed_doc))
            except (KeyError, ValueError, OSError) as exc:
                return {**record, "status": "crashed", "why": f"the acceptance check failed to run: {exc}"}
            summary.update(acceptance=accepted["pass"],
                           acceptance_record_sha256=sha(root / f"job-{index}" / ACCEPT_FILE))
            if not accepted["pass"]:                     # LS-04: the unit stands, its O-ext pass does not run
                break
    folders = [f for f in out_dirs(commands) if f.startswith(f"job-{index}/")]
    record["outputs"] = hashed_outputs(root, folders)    # outputs under the job folder (a unit is recorded by its
    if accepted is not None:                             # COMPLETE.json, which lists its own files' SHA-256)
        record["outputs"][f"job-{index}/{ACCEPT_FILE}"] = summary["acceptance_record_sha256"]
        if not accepted["pass"]:
            return {**record, "sc": summary, "status": "complete", "acceptance": False, "reason": LS04}
        record["acceptance"] = True
        if not any(rel.startswith(f"job-{index}/oext/") for rel in record["outputs"]):
            return {**record, "status": "crashed", "why": "the O-ext pass wrote no output"}
    if kind in rules.WRAPPER_KINDS:
        calls = {}
        for folder in folders:
            got, why = wrapper_summary(root, folder)
            if got is None:
                return {**record, "status": "crashed", "why": why}
            if got["exit_code"] != exits[next(n for n, a in commands if a[a.index("--out") + 1] == folder)]:
                return {**record, "status": "crashed", "why": f"{folder}: the wrapper record's exit_code is not the step's"}
            calls[folder] = got
        summary["wrapper"] = calls
    if kind == "untuned_answers":
        pool = f"{folders[0]}/s3_orig.pool.json"
        summary["s3_orig_pool_sha256"] = record["outputs"].get(pool)
        if summary["s3_orig_pool_sha256"] is None:
            return {**record, "status": "crashed", "why": "the S3 call wrote no s3_orig.pool.json"}
    if kind == "anchor":
        summary["anchor_file_sha256"] = record["outputs"].get(f"{folders[0]}/anchors.json")
        summary["anchor_record_sha256"] = record["outputs"].get(f"{folders[0]}/anchors.sealed.json")
        if summary["anchor_file_sha256"] is None or summary["anchor_record_sha256"] is None:
            return {**record, "status": "crashed", "why": "the anchor job wrote no anchors.json or anchors.sealed.json"}
    if kind == "c0":                                     # PP18: unitless; B17's record among the hashed outputs
        summary["c0_record_sha256"] = record["outputs"].get(f"job-{index}/c0/{C0_RECORD}")
        if summary["c0_record_sha256"] is None:
            return {**record, "status": "crashed", "why": f"the lean job wrote no {C0_RECORD}"}
    if not record["outputs"] and kind not in SC_UNIT_KINDS:
        return {**record, "status": "crashed", "why": "the job wrote no output"}
    return {**record, "sc": summary, "status": "complete"}


# ===== after each arm: s_obs (KD11) ================================================================================
def read_progress(root: pathlib.Path, unit: str) -> list:
    """The unit's progress.jsonl rows (JSON objects; the rule reads kind, elapsed_s, rows and capped only). A missing
    or unreadable file gives no rows, which the rule refuses."""
    path = root / unit / PROGRESS_FILE
    rows = []
    try:
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
    except (OSError, ValueError):
        return []
    return rows


def arm_s_obs(root: pathlib.Path, unit: str, family: str) -> tuple[float | None, str | None]:
    """(s_obs of the finished arm, None) or (None, why the rule refused the record)."""
    try:
        return r78.s_obs_from_progress(family, read_progress(root, unit)), None
    except r78.Refused as exc:
        return None, str(exc)


# ===== the job ======================================================================================================
def stage_of(step: str) -> str:
    return next((stage for suffix, stage in STEP_STAGE if suffix in step), "setup")


def write_ledger(root: pathlib.Path, index: int, job: dict, host: str, engine_sha: str, started: float,
                 ended: float, steps: list[dict]) -> str:
    """job-I/cost-ledger.json (FR-10): stage seconds by step and the job slot (start to end inside the pod)."""
    stages = {s: 0.0 for s in LEDGER_STAGES}
    for step in steps:
        stages[stage_of(step["name"])] += step["seconds"]
    ledger = {"kind": "stage1 cost ledger", "version": 1, "host": host, "index": index, "job_kind": job["kind"],
              "job_id": job.get("job_id"), "arm": job.get("arm"), "seed": job.get("seed"), "engine": job["engine"],
              "engine_sha256": engine_sha, "stages_s": {k: round(v, 3) for k, v in stages.items()},
              "slot_s": round(ended - started, 3), "steps": steps,
              "rule": "FR-10 stages in GPU-seconds of this job's steps (the engine's calibrate step counts as training; "
                      "the engine unit's own ledger splits it)"}
    (root / f"job-{index}").mkdir(parents=True, exist_ok=True)
    path = root / f"job-{index}" / LEDGER_FILE
    path.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n")
    return f"job-{index}/{LEDGER_FILE}"


def unit_fingerprints(root: pathlib.Path, unit: str) -> tuple:
    """The fingerprint fields of a calibrate unit for a readable record (the stage-1 kit's K6): ({complete_sha256,
    checkpoints {e1, q}, identity {manifest_sha256, training_identity}}, None), else (None, why). e1 is
    states/e1/state.json's adapter_fingerprint and must equal COMPLETE.json's checkpoints.e1.adapter_fingerprint; q is
    COMPLETE.json's checkpoints.q (or null). Only these fields are read: no evaluation value, no edit field."""
    folder = root / unit
    try:
        complete = json.loads((folder / "COMPLETE.json").read_text())
        state = json.loads((folder / "states" / "e1" / "state.json").read_text())
    except (OSError, ValueError) as exc:
        return None, f"the unit's COMPLETE.json or states/e1/state.json cannot be read ({type(exc).__name__})"
    complete, state = (complete if isinstance(complete, dict) else {}), (state if isinstance(state, dict) else {})
    points = complete.get("checkpoints") if isinstance(complete.get("checkpoints"), dict) else {}
    e1, q = state.get("adapter_fingerprint"), (points.get("q") or {}).get("adapter_fingerprint")
    if rules.hex64(e1) is None or e1 != (points.get("e1") or {}).get("adapter_fingerprint"):
        return None, "states/e1/state.json's adapter_fingerprint is not a SHA-256 equal to COMPLETE.json's e1 one"
    if q is not None and rules.hex64(q) is None:
        return None, "COMPLETE.json's q adapter_fingerprint is not a SHA-256"
    identity = complete.get("identity") if isinstance(complete.get("identity"), dict) else {}
    return {"complete_sha256": sha(folder / "COMPLETE.json"), "checkpoints": {"e1": e1, "q": q},
            "identity": {k: identity.get(k) for k in ("manifest_sha256", "training_identity")}}, None


def a0_fingerprint_record(root: pathlib.Path, unit: str, job: dict, index: int) -> tuple:
    """(job-I/a0-adapter-fingerprint.json, None) once written, else (None, why): the stage-1 kit's K6 record (seal.py
    classes *adapter-fingerprint*.json readable), in the format of the B10/B11 re-pin tool."""
    fields, why = unit_fingerprints(root, unit)
    if fields is None:
        return None, why
    doc = {"kind": rules.A0_FINGERPRINT_KIND, "version": 1, "job": index, "arm": "a0", "seed": job["seed"],
           "unit": unit, **fields}
    rel = f"job-{index}/{rules.A0_FINGERPRINT_RECORD}"
    (root / f"job-{index}").mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return rel, None


def run_job(plan: dict, host: str, index: int, root: pathlib.Path, units: dict, env: dict, sealed_doc: dict) -> dict:
    """Run one job's steps; the record says complete (unit, COMPLETE.json SHA-256, outputs) or crashed."""
    h = plan["hosts"][host]
    job = h["jobs"][index]
    kind = job["kind"]
    commands = job_commands(plan, host, index, root, units, sealed_doc)
    arm = engine_arm(job)
    pattern = f"{ROUND}/{job['seed']}-{arm}-e1-a*"
    before = complete_attempts(root, pattern)
    exits, steps = {}, []
    for name, argv in commands:
        start = time.monotonic()
        done = subprocess.run(["python3", "process_receipt.py", "--out", name, "--", *argv], env=env, cwd=root)
        steps.append({"name": name, "seconds": round(time.monotonic() - start, 3), "exit": done.returncode})
        exits[name] = done.returncode
        if done.returncode:
            return {"status": "crashed", "why": f"exit {done.returncode} in {name}", "exits": exits, "steps": steps}
    record = {"exits": exits, "steps": steps}
    new = sorted(complete_attempts(root, pattern) - before)
    if len(new) != 1:
        return {**record, "status": "crashed", "why": "no new COMPLETE.json"}
    unit = new[0]
    check = subprocess.run([*ENGINE, "verify", "--run", unit, "--prepared", PREPARED], env=env, cwd=root,
                           capture_output=True, text=True)
    record.update(unit=unit, complete_sha256=sha(root / unit / "COMPLETE.json"),
                  verified={"exit": check.returncode, "tail": (check.stdout + check.stderr)[-600:]}, outputs={})
    if check.returncode:
        return {**record, "status": "crashed", "why": "the unit's verify failed"}
    if kind == "a0_arm":                                 # K6: the a0 fingerprint, readable after the block's seal
        rel, why = a0_fingerprint_record(root, unit, job, index)
        if rel is None:
            record["a0_fingerprint_record"] = why        # the unit stands; the reference phase refuses its seed
        else:
            record["outputs"][rel] = sha(root / rel)
    return {**record, "status": "complete"}


def write_record(root: pathlib.Path, index: int, record: dict) -> None:
    (root / "job-done").mkdir(exist_ok=True)
    (root / "job-done" / f"JOB-{index}.json").write_text(json.dumps(record, indent=2) + "\n")


def base_record(job: dict, index: int, h: dict, engine_sha: str) -> dict:
    return {"index": index, "kind": job["kind"], "arm": job["arm"], "seed": job["seed"], "engine": job["engine"],
            "engine_sha256": engine_sha, "job_id": job.get("job_id"), "requirement_s": job.get("start_requirement_s")}


def dry_run_options(args: list[str]) -> dict:
    """--remaining SECONDS, --free-gb GB, --s-obs X after --dry-run (each optional)."""
    out = {"remaining": None, "free_gb": None, "s_obs": 1.0}
    names = {"--remaining": "remaining", "--free-gb": "free_gb", "--s-obs": "s_obs"}
    i = 0
    while i < len(args):
        if args[i] in names:
            if i + 1 >= len(args):
                raise SystemExit(f"{args[i]} needs a number")
            out[names[args[i]]] = float(args[i + 1])
            i += 2
        else:
            i += 1
    return out


def dry_run(plan: dict, host: str, root: pathlib.Path, options: dict) -> dict:
    """Every job's commands and inputs, and (with the preflight's two documents in root) the rule's decisions."""
    h = plan["hosts"][host]
    jobs = h["jobs"]
    doc = load_sealed(root)
    out = []
    for i, job in enumerate(jobs):
        try:
            commands = [[name, argv] for name, argv in job_commands(plan, host, i, root, {}, doc)]
        except Unrunnable as exc:
            commands = {"unrunnable": str(exc)}
        out.append({"index": i, "kind": job["kind"], "arm": job["arm"], "seed": job["seed"], "engine": job["engine"],
                    "commands": commands, "inputs": sealed_paths(job, h, i, doc)})
    decisions = None
    left = options["remaining"] if options["remaining"] is not None else remaining(dt.datetime.now(dt.timezone.utc))
    free = options["free_gb"] if options["free_gb"] is not None else free_space_gb(root)
    pre_path = root / "PREFLIGHT-DONE.json"
    if pre_path.is_file():
        try:
            pre = json.loads(pre_path.read_text())
            verification = load_verification(root, pre)
            family = plan.get("family") or rules.FAMILY
            if left is None:                             # no heartbeat and no --remaining: none never fits
                decisions = [{"index": k, **r78.job_decision(family, pre, verification, job, None, free, options["s_obs"])}
                             for k, job in enumerate(jobs)]
            else:
                decisions = r78.pod_dry_run(family, pre, verification, jobs, left, free, options["s_obs"])
        except (AssertionError, ValueError, OSError) as exc:    # rules_78b.Refused is a ValueError
            decisions = {"refused": str(exc)}
    return {"host": host, "family": plan.get("family"), "engine": h["engine"], "jobs": out, "dry_run": True,
            "remaining_s": left, "free_gb": free, "s_obs": options["s_obs"], "decisions": decisions}


def main(argv=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    host, dry = args[0], "--dry-run" in args[1:]
    root = pathlib.Path.cwd() if dry else ROOT
    if not dry:
        os.chdir(root)
    plan = json.loads((root / "plan.json").read_text())
    h = plan["hosts"][host]
    assert h["base_eval"] is False, "base_eval must be false on every stage-1 host"
    jobs = h["jobs"]
    if dry:
        print(json.dumps(dry_run(plan, host, root, dry_run_options(args[1:])), indent=1))
        return 0
    pre = json.loads((root / "PREFLIGHT-DONE.json").read_text())
    sealed_doc, verification, bank = preflight_checks(plan, host, pre, root)
    sealed = sealed_doc["files"]
    family = family_of_plan(plan)
    engine_sha = h["engine_sha256"]
    env = {k: v for k, v in os.environ.items() if k not in TOKEN_ENV_NAMES}
    env.update({"CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
                "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(root), "HF_HUB_OFFLINE": "1"})
    for folder in (ROUND, "jobs"):
        (root / folder).mkdir(exist_ok=True)
    records, units, stopped, refusal = [], {}, None, None
    s_obs, pending = 1.0, None                           # the largest s_obs so far; a refusal to apply at the next job
    keys = key_refusal(plan, host, verification, bank)   # the pod's key check, recorded (never asserted)
    if keys is not None:
        pending = Refusal("key" if jobs[keys[0]]["kind"] not in r78.S78_KINDS | r78.BQI_KINDS else "recipe_pin", keys[1])
    for i, job in enumerate(jobs):
        left = remaining(dt.datetime.now(dt.timezone.utc))
        free = free_space_gb(root)
        base = {**base_record(job, i, h, engine_sha), "remaining_s": left, "free_gb": free, "s_obs": s_obs, "utc": utc()}
        decision = None
        if pending is not None:
            stopped, refusal = "refused", pending
        elif left is None:
            stopped = "heartbeat_unreadable"
        else:
            try:
                decision = r78.job_decision(family, pre, verification, job, left, free, s_obs)
            except r78.Refused as exc:
                stopped, refusal = "refused", Refusal(refusal_reason(family, pre, verification, job, free), str(exc))
        if decision is not None:
            base.update(requirement_s=decision["requirement_s"], s_pod=decision["s_pod"], s=decision["s"])
            if decision["action"] == "defer":
                stopped, refusal = "deferred", Refusal(decision["reason"], f"job {i} ({job['kind']}): deferred, {decision['reason']}")
            else:
                bad = sealed_check(job, sealed, root, h, i, sealed_doc)
                if bad:
                    stopped = "sealed_file_mismatch"
                    base["sealed_mismatch"] = bad
        if stopped:
            later = "deferred" if stopped in ("deferred", "refused") else "not_started"
            for k in range(i, len(jobs)):
                rec = {**base, "status": later} if k == i else {**base_record(jobs[k], k, h, engine_sha), "status": later}
                if refusal is not None:
                    rec.update(reason=refusal.reason, refusal=refusal.text)
                records.append(rec)
                write_record(root, k, rec)
            if later == "deferred":
                (root / "deferral.json").write_text(json.dumps({
                    "utc": utc(), "host": host, "family": family, "first_deferred": i, "remaining_s": left, "free_gb": free,
                    "requirement_s": base.get("requirement_s"), "s_pod": base.get("s_pod"), "s_obs": s_obs,
                    "stopped": stopped, "reason": refusal.reason, "refusal": refusal.text,
                    "deferred": list(range(i, len(jobs)))}, indent=2) + "\n")
            break
        started = time.monotonic()
        try:
            result = (run_sc_job if h.get("block") == r78.SC_BLOCK else run_job)(plan, host, i, root, units, env,
                                                                                  sealed_doc)
        except Unrunnable as exc:
            result = {"status": "crashed", "why": str(exc), "exits": {}, "steps": []}
        ended = time.monotonic()
        ledger = write_ledger(root, i, job, host, engine_sha, started, ended, result.pop("steps", []))
        if result["status"] == "complete" and job["kind"] not in BLOCK0_KINDS:   # K4b: no s_obs after a scorer job
            result.setdefault("outputs", {})
            result["outputs"][ledger] = sha(root / ledger)
        elif result["status"] == "complete":
            result.setdefault("outputs", {})
            result["outputs"][ledger] = sha(root / ledger)
            observed, problem = arm_s_obs(root, result["unit"], family)      # KD11: this arm's slowest capped batch
            result["s_obs_after"] = observed
            if problem is not None:
                result["s_obs_problem"] = problem
                pending = Refusal("s_obs_record", f"after job {i} ({job['kind']}): {problem}")
            else:
                s_obs = max(s_obs, observed)
        rec = {**base, **result, "ended_utc": utc()}
        records.append(rec)
        write_record(root, i, rec)
        if result["status"] != "complete":
            stopped = "crashed"
            for k in range(i + 1, len(jobs)):
                later = {**base_record(jobs[k], k, h, engine_sha), "status": "not_started"}
                records.append(later)
                write_record(root, k, later)
            break
        units[i] = result.get("unit")
    started_ = [r for r in records if r["status"] in ("complete", "crashed")]
    done = {"utc": utc(), "host": host, "family": family, "engine": h["engine"], "engine_sha256": engine_sha,
            "jobs": records, "stopped": stopped,
            "refusal": None if refusal is None else {"reason": refusal.reason, "text": refusal.text},
            "s_obs_final": s_obs,
            "ok": stopped in (None, "deferred") and all(r["status"] == "complete" for r in started_)}
    (root / "JOB-DONE.json").write_text(json.dumps(done, indent=2) + "\n")
    print(json.dumps({"host": host, "ok": done["ok"], "stopped": stopped, "reason": done["refusal"] and done["refusal"]["reason"],
                      "statuses": [r["status"] for r in records]}), flush=True)
    left = remaining(dt.datetime.now(dt.timezone.utc))
    if shorten(left):                                    # the last action; never extends
        subprocess.run(["python3", "extend_cap.py", str(SHORTEN_TO_S)], cwd=root)
    return 0 if done["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
