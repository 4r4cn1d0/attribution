"""The 7-8B kit's jobs of one host, in order (runs on the pod after the bootstrap and the preflight; K2 of the
readiness plan's T4; the lead's ruling 11 KD3, KD5, KD11; the addendum's A1; the ADAPTATION of the stage-1 kit's
setup/job_runner_stage1.py, whose 1B kinds (W1-18, D-2, B10/B11, C1-C3, the O-ext pass, similarity, the plant pilot)
are not in this copy: block 0 runs ``arm`` and ``a0_arm`` under the family's main config, nothing else).

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


def preflight_checks(plan: dict, host: str, pre: dict, root: pathlib.Path) -> tuple[dict, dict, dict]:
    """Refuse (AssertionError) before any job unless the pod is the planned one; returns (sealed-files.json's doc,
    the preflight's verification.json, the bank built from the recipe and the packed prepared set)."""
    h = plan["hosts"][host]
    jobs = h["jobs"]
    family = family_of_plan(plan)
    present = [name for name in TOKEN_ENV_NAMES if os.environ.get(name)]
    assert not present and not (pathlib.Path.home() / ".cache/huggingface/token").exists(), "a token is present"
    assert not (root / "JOB-DONE.json").exists(), "this host already ran its jobs"
    assert json.loads((root / "BOOTSTRAP-READY.json").read_text())["ok"] is True, "bootstrap not ready"
    assert pre.get("ok") is True and pre.get("recipe") == preflight_recipe(h), \
        "the preflight did not pass for the host's recipe"
    verification = load_verification(root, pre)
    assert all(j.get("family", family) == family for j in jobs), f"a job of another family than {family}'s on this pod"
    assert h["engine"] in rules.ENGINES and h["engine_sha256"] == rules.ENGINES[h["engine"]], \
        "the host's engine is not a pinned engine (G4)"
    assert all(j["engine"] == h["engine"] for j in jobs), "two engines on one pod (G4)"
    assert _engine_identity() == h["engine_sha256"], "engine code differs from the plan (G4)"
    rec = rules.REC
    assert rec in plan.get("recipes", {}), f"recipe {pathlib.Path(rec).name} is not in plan.json"
    assert sha(root / rec) == rules.RECIPE_PINS[rec], f"recipe {pathlib.Path(rec).name} differs from its pin"
    config = _recipe_config_sha(root / rec)
    assert config == plan["recipes"][rec]["config_sha256"] == rules.REC_CONFIG_SHA256, \
        f"recipe {pathlib.Path(rec).name} differs from the plan (its config SHA-256)"
    assert verification.get("recipe_sha256") == config, "the preflight ran another recipe than the plan's"
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
        try:
            r78.check_keys(family, job["kind"], recipe, h["engine_sha256"], gpu_name_of(verification), manifest, bank)
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
            result = run_job(plan, host, i, root, units, env, sealed_doc)
        except Unrunnable as exc:
            result = {"status": "crashed", "why": str(exc), "exits": {}, "steps": []}
        ended = time.monotonic()
        ledger = write_ledger(root, i, job, host, engine_sha, started, ended, result.pop("steps", []))
        if result["status"] == "complete":
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
