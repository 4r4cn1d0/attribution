"""The stage-1 jobs of one host, in order (runs on the pod after the bootstrap and the preflight; B15, brief
notes/b15-brief.md §3 J1-J18 and §4; copied from runkit/gate-b-olmo/setup/job_runner_gateb.py).

    venv/bin/python job_runner_stage1.py HOST [--dry-run]

Checks first (any failure refuses before a job starts): no token variable or token file; this host has not run (no
JOB-DONE.json); BOOTSTRAP-READY ok; PREFLIGHT-DONE ok for the host's preflight recipe (``preflight_recipe``) and with a
cap projection when the host holds an arm-like job or a regeneration; one engine per pod and the packed engine's code
identity equal to the host's engine_sha256, which must be stage1_rules.ENGINES[engine] (G4); every recipe file equal to
its pin and its config SHA-256 equal to plan.json's; the prepared manifest equal to the plan; sealed-files.json equal to
the plan's pin and every file it lists present with its SHA-256; a 500-bank job only with plan.json's recorded W1-18
branch, and only on that branch (G1); a W1-18 job only alone on its host (§8 Q1 (a)).

Then each job, in order, one process per step under process_receipt.py (the commands of ``job_commands``, brief §3):
  w1_18          scripts/stage1/limits/overrefusal_checks.py --out job-I/w1-18 --data-root data --device cuda
                 --guard-batch-size N (N: REC's guard batch size, passed explicitly; report only in W1-18's record)
  regenerate     engine make-job run-one (train only: no --bank, so evaluate_bank is null; --pin-code) and run-one; then
                 the acceptance check below (J2, LN-12)
  o_only         the O-ext unit pass (OEXT_UNIT_SCRIPT run; theta0: --untuned) on the accepted regenerated e1 state of
                 the regeneration its regen_source names on this pod (J3)
  transfer_report  OEXT_UNIT_SCRIPT transfer --untuned (J4; Branch 128 only)
                 (round 3c: every O-ext unit step, J3, J4, J9, J10 and J18, seals OEXT_UNIT_SCRIPT and its settings
                 OEXT_UNIT_SETTINGS, both stage1_rules.S1_CODE pins, with oext_eval.py and its settings)
  rep_pass       D-2's scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py with the plant, decoy and s3_safe pools
                 and --pool-pins/--req8-record (PATH:SHA256 of the packed filled pins file and REQ-8's record, equal to
                 the job's plan.json pins); then the s3_orig pools-only pass on the earlier untuned_answers job's
                 output, also through D-2 (J5; addendum §19 point 3). Under the job's D-2 fallback: the W1
                 scripts/stage1/representation_pass.py with s3_safe only, and the same s3_orig pass (§19 point 4).
                 Both passes take --recipe recipe S (representation_pass.json pins it). A J5 moved off J6's pod
                 (defer) reads J6's pool as the packed input pool:s3_orig by plan.json's pin (job.s3_orig)
  untuned_answers  scripts/stage1/make_untuned_answers.py --list/--loss NAME=PATH:SHA256 (J6)
  l1_scan        scripts/stage1/score_l1_larf.py scan (J7)
  classifier     D-2's scripts/stage1_s1/d2_pool_pins/d2_score_classifier.py with --pool PATH:SHA256 for plant and
                 decoy and the same two pins (J8; addendum §21); under its fallback the W1 scripts/stage1/
                 score_classifier.py with no pools
  arm, a0_arm, ref_train  engine calibrate --checkpoints e1 (an edit arm with --edit and its edit-<SHA-256> arm),
                 then the O-ext unit pass on the new unit's e1 state (J9, J10, J18)
  c0             engine make-job run-one (R_1, seed 1101, train only, --pin-code) and scripts/stage1_s1/lean_eval_job.py run
                 --expect-adapter-fingerprint <R_1101's e1 fingerprint, from its pinned COMPLETE.json> with a fresh
                 registry and the O-ext inputs (J11; engine X, on block A's LN-12 pod: addendum §26)
  retrain        LN-15e (J20): Gate B's retrain, engine make-job run-one --arm a0 --seed 1102|1103 --target e1 (train
                 only, --pin-code) and run-one into rescore/ with its own registry rescore/registry.jsonl (the J2
                 regeneration of the same seed writes round1/registry.jsonl; one registry refuses a seed twice)
  a1_rescore     LN-15e (J21): Gate B's diagnostics attributes step on the retrain its regen_source names on this pod:
                 make-job attributes --a0-state q=UNIT --a0-state e1=UNIT --groups <Gate B's 8 unit groups, from
                 plan.json> --anchors <the packed anchor bank> --pin-code, then attributes (A1's bi-anchored cosine
                 per row; report only, the Jaccard and Kendall tau against the sealed A1 set are read on the Mac)
  cert_c1        engine make-job run-one --bank dev --replicate-of <R_1101's run folder> and run-one in the cert/ run
                 root (J12, engine Y)
  cert_c2        engine make-job run-one with the B+Qi recipe, train only, and run-one (J13, engine Y)
  cert_c3        engine make-job run-one --bank subsample-<SHA-256> --bank-file F and run-one (J14, engine Y); the
                 packed subsample file and the writer's record must hash to the job's plan.json pins (§22 point 2)
  b10_certify    scripts/stage1_s1/eval_adapter.py run --evaluations certify[,scale:0] --gate-reference-eval DIR (B10's
                 run writes the in-process comparison <seed>-certify.compare.json) (J15)
  ref_eval       eval_adapter.py run --evaluations ... --certification-report F --certification-report-sha256 H (J16)
  safe_lora      eval_adapter.py regenerate; then ON THE CPU, BEFORE THE PROJECTION, scripts/stage1_s1/safe_lora.py
                 vcheck (per matrix ||V - V'||_F / ||V||_F, V' = float32(W_Instruct) - float32(bf16(W_base)), and
                 whether the K = 39 set changes); then safe_lora.py check, and per point transform --point P and
                 eval_adapter.py evaluate --mode external --external safe_lora with the transform's file and record by
                 SHA-256 (J17); the transform's safe_lora_timing.json seconds.total enters the cost ledger as the
                 "transform" stage. A k12 point refuses: B11 offers no K = 12 point.
Every 500-bank step gets the O-ext bank, its record and (when packed) W1-18's record. Under Branch 128 an O-only
pass on a regenerated a0 or R unit also gets --dev100-source, the source unit's folder (packed input
source_unit:ARM:SEED): LN-19 cuts that unit's stored dev-100 answers to 128 tokens, and only PHTest is generated from
the regenerated adapter (§8 Q15). Under fallback (c) (plan.json records.oext_fallback, status dev100_recipe_cap;
addendum §11 point 1) no O-ext step runs: arms run calibrate only, B10 and B17 get no O-ext flags, and an O-only pass
or transfer report is unrunnable.

The per-job gate (unchanged from Gate B): the governing stop from the pod timer's heartbeat; a missing or unreadable
heartbeat stops the host (``heartbeat_unreadable``). A job starts only if the remaining time is at least its
requirement (stage1_rules.requirements: max(plan, this pod's projection), a regeneration linked to its O-only pass);
otherwise this job and every later one are ``deferred``, in order (deferral.json). Before a job its every input (the
scripts, settings, the edit file against its arm, the named stage-1 inputs and data folders) is checked against
sealed-files.json; a mismatch stops the host (``sealed_file_mismatch``) and nothing of that job runs. A non-zero exit,
or no new output, is a crash: the job is ``crashed``, later jobs ``not_started``, and the host stops. A regeneration
whose unit differs from reuse_spec.json's ``accept`` fields (every field listed there: the e1 adapter fingerprint, the
training identity, the prepared manifest and the data config) is complete with ``acceptance`` false and reason
``LS-04``; its O-only pass is then ``not_started`` with reason ``LS-04`` and the later jobs go on (LS-04 (a)).

Records: job-done/JOB-<i>.json per job and JOB-DONE.json at the end (plan_tool record-done's schema: index, kind,
arm, seed, status, engine, engine_sha256, unit, complete_sha256, outputs {relpath: SHA-256}, reason); each job also
writes job-I/cost-ledger.json (FR-10: the stages setup, training, greedy_generation, sampled_generation, judging,
scoring, pod_overhead and transform, in seconds; the slot from start to end inside the pod). No outcome file is read:
the runner hashes outputs, reads COMPLETE.json identity and fingerprint fields (J2), the regenerated unit's
fingerprint record and the transform's timing file. Last, the stop is shortened to 1 h from now when more remains.
--dry-run prints every job's commands (placeholders for values known only at run time) and writes nothing.
"""
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
for _folder in (HERE, HERE.parent):                 # the pod: beside this script; the kit: one folder up
    if (_folder / "stage1_rules.py").is_file():
        sys.path.insert(0, str(_folder))
        break
import stage1_rules as rules  # noqa: E402

ROOT = pathlib.Path("/workspace/attribution-headroom")
HEARTBEAT = pathlib.Path("/workspace/.pod-timer/heartbeat.json")
ENGINE = ["venv/bin/python", "-m", "experiments.safety_selection"]
SCRIPT = ["venv/bin/python"]
TOKEN_ENV_NAMES = rules.TOKEN_ENV_NAMES
ROUND = "round1"
CERT_ROOT = "cert"                                    # C1-C3's own run root (no Gate B reading opens it)
DATA = "data"                                         # the bundle's data root (mirrors the checkout's tmp/)
PREPARED = f"{DATA}/kt-prepared/{rules.PREPARED_NAME}"
SHORTEN_TO_S = 3600
W1_18_SCRIPT = "scripts/stage1/limits/overrefusal_checks.py"
REP_SCRIPT = "scripts/stage1/representation_pass.py"
UNTUNED_SCRIPT = "scripts/stage1/make_untuned_answers.py"
L1_SCRIPT = "scripts/stage1/score_l1_larf.py"
CLASSIFIER_SCRIPT = "scripts/stage1/score_classifier.py"
B10_SCRIPT = "scripts/stage1_s1/eval_adapter.py"
B11_SCRIPT = "scripts/stage1_s1/safe_lora.py"
B17_SCRIPT = "scripts/stage1_s1/lean_eval_job.py"
OEXT_MODULE = "scripts/stage1_s1/oext_eval.py"
OEXT_UNIT_SCRIPT = "scripts/stage1_s1/oext_unit.py"   # the O-ext unit runner (contract below); round 3c: S1_CODE pin
OEXT_UNIT_SETTINGS = "scripts/stage1_s1/settings/oext_unit.json"   # its pinned settings (round 3c: S1_CODE pin)
B11_POINTS = ("default", "conditional", "certify")    # safe_lora.POINTS (k12 is a kit-only gated point B11 lacks)
VCHECK_FILE, TIMING_FILE = "safe_lora_vcheck.json", "safe_lora_timing.json"
B11_ADAPTER, B11_RECORD = "adapter.safetensors", "safe_lora_record.json"
ACCEPT_FILE = "regeneration-adapter-fingerprint.json"  # readable by the seal (fingerprints and identities only)
LEDGER_FILE = "cost-ledger.json"
LEDGER_STAGES = ("setup", "training", "greedy_generation", "sampled_generation", "judging", "scoring",
                 "pod_overhead", "transform")
LS04 = "LS-04"
# the stage-1 inputs a job names (sealed-files.json "inputs": name -> bundle path, file or folder)
OEXT_INPUTS = ("oext_bank", "oext_record")
D2_INPUTS = ("d2_pool_pins", "req8_record")          # the filled pins file and REQ-8's record (addendum §19 point 3)
D2_COMMON = ["scripts/stage1_s1/d2_pool_pins/__init__.py", "scripts/stage1_s1/d2_pool_pins/fill_pins.py",
             "scripts/stage1_s1/d2_pool_pins/settings/d2_pool_pins.json", rules.MAN1_PATH,
             REP_SCRIPT, "scripts/stage1/settings/representation_pass.json",
             "scripts/stage1/settings/representation_pools.json"]
D2_SCRIPTS = {"rep_pass": [rules.D2_REP_SCRIPT, *D2_COMMON],     # the D-2 route's files (not under the job's fallback)
              "classifier": [rules.D2_CLASSIFIER_SCRIPT, "scripts/stage1_s1/d2_pool_pins/settings/d2_score_classifier.json",
                             rules.D2_REP_SCRIPT, *D2_COMMON]}
POOLS_J5 = ("plant", "decoy", "s3_safe")
S3_ORIG_INPUT = rules.S3_ORIG_INPUT                  # J6's s3_orig pool for a J5 moved off J6's pod (plan.json pin)
POOLS_J8 = ("plant", "decoy")
J6_LISTS = (("list", "s3"), ("list", "s4"), ("list", "sd600"), ("loss", "s1"), ("loss", "s3_safe"))
SCRIPTS = {"w1_18": [W1_18_SCRIPT, "scripts/stage1/limits/limits_common.py", "scripts/stage1/s1common.py",
                     "scripts/stage1/settings/limits_overrefusal_checks.json"],
           "rep_pass": [REP_SCRIPT, "scripts/stage1/settings/representation_pass.json",
                        "scripts/stage1/settings/representation_pools.json"],
           "untuned_answers": [UNTUNED_SCRIPT, "scripts/stage1/settings/make_untuned_answers.json"],
           "l1_scan": [L1_SCRIPT],
           "classifier": [CLASSIFIER_SCRIPT, "scripts/stage1/settings/score_classifier.json"],
           "c0": [B17_SCRIPT, "scripts/stage1_s1/settings/lean_eval_job.json"],
           "b10_certify": [B10_SCRIPT, "scripts/stage1_s1/settings/eval_adapter.json"],
           "ref_eval": [B10_SCRIPT, "scripts/stage1_s1/settings/eval_adapter.json"],
           "safe_lora": [B10_SCRIPT, "scripts/stage1_s1/settings/eval_adapter.json", B11_SCRIPT,
                         "scripts/stage1_s1/settings/safe_lora.json"]}
OEXT_STEP_KINDS = ("o_only", "transfer_report", "arm", "a0_arm", "ref_train")   # the kit's O-ext unit step
B10_OEXT_KINDS = ("c0", "ref_eval", "safe_lora")      # O-ext through B10's or B17's own flags (b10_certify: report)
ARM_LIKE_PREFLIGHT = ("arm", "a0_arm", "ref_train", "regenerate", "cert_c1", "cert_c2", "cert_c3", "c0", "retrain")
RESCORE_ROOT = "rescore"                              # LN-15e's retrains and re-scores (own registry)


def oext_unit_contract():
    """The CLI the kit calls for the O-ext pass on an engine unit's state (OEXT_UNIT_SCRIPT is not built; whoever
    builds it must accept exactly this; the kit's tests parse every O-ext step with this parser)."""
    import argparse
    ap = argparse.ArgumentParser(prog=OEXT_UNIT_SCRIPT)
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("run", "transfer"):
        p = sub.add_parser(name)
        state = p.add_mutually_exclusive_group(required=True)
        state.add_argument("--run", help="an engine unit folder (its states/CHECKPOINT state)")
        state.add_argument("--untuned", action="store_true", help="theta0: no adapter")
        p.add_argument("--checkpoint", choices=("e1",))
        p.add_argument("--prepared", required=True)
        p.add_argument("--recipe", required=True)
        p.add_argument("--oext-bank", required=True)
        p.add_argument("--oext-record", required=True)
        p.add_argument("--w1-18-record")
        p.add_argument("--dev100-source", help="Branch 128, a regenerated unit: the source unit (LN-19, §8 Q15)")
        p.add_argument("--out", required=True)
    return ap


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


def recipe_path(job: dict) -> str:
    return rules.RECIPE_NAMES[job.get("recipe") or "S"]


def preflight_recipe(h: dict) -> str:
    """The host's preflight recipe: the recipe of its first arm-like job or regeneration, else REC."""
    for job in h["jobs"]:
        if job["kind"] in ARM_LIKE_PREFLIGHT:
            return recipe_path(job)
    return rules.REC


def engine_arm(job: dict) -> str | None:
    """The engine's arm id of an edit job: edit-<SHA-256 of the edit file> (a0 jobs: "a0")."""
    edit = job.get("edit")
    if not edit:
        return "a0" if job.get("arm") in ("a0", "G", "bqi") or job["kind"] in ("a0_arm", "ref_train") else None
    return edit.get("engine_arm") or f"edit-{edit['sha256']}"


def edit_bundle(job: dict) -> str | None:
    edit = job.get("edit")
    return f"edits/{edit['sha256']}.edit.json" if edit else None


def inputs_of(sealed_doc: dict) -> dict:
    return dict(sealed_doc.get("inputs") or {})


def input_path(inputs: dict, name: str, required: bool = True) -> str | None:
    path = inputs.get(name)
    if path is None and required:
        raise KeyError(name)
    return path


def oext_fallback(plan: dict) -> bool:
    """Fallback (c) recorded (addendum §11 point 1): no O-ext step runs."""
    rec = (plan.get("records") or {}).get("oext_fallback")
    return bool(rec) and rec.get("status") == rules.OEXT_FALLBACK_STATUS


def dev100_source(job: dict) -> str | None:
    """The packed source-unit input of an O-only pass on a regenerated unit under Branch 128 (LN-19; §8 Q15)."""
    if job["kind"] == "o_only" and job.get("arm") in ("a0", "R") and job.get("branch") == "128":
        return f"source_unit:{job['arm']}:{job['seed']}"
    return None


def oext_args(inputs: dict) -> list[str]:
    out = ["--oext-bank", input_path(inputs, "oext_bank"), "--oext-record", input_path(inputs, "oext_record")]
    if inputs.get("w1_18_record"):
        out += ["--w1-18-record", inputs["w1_18_record"]]
    return out


def pathsha(inputs: dict, files: dict, name: str) -> str:
    """PATH:SHA256 of a named input (the stage-1 scripts' input form)."""
    path = input_path(inputs, name)
    return f"{path}:{files[path]}"


def guard_batch(root: pathlib.Path) -> str:
    try:
        return str(int(json.loads((root / rules.REC).read_text())["guard"]["batch_size"]))
    except (OSError, ValueError, KeyError, TypeError):
        return "@recipe-guard-batch-size"


class Unrunnable(Exception):
    """A job the kit cannot run as planned (named before anything starts)."""


def d2_fallback_job(job: dict) -> bool:
    """The job's plan.json D-2 entry names the D-2 fallback record (addendum §19 point 4, §21)."""
    return bool((job.get("d2") or {}).get("fallback"))


def d2_route(job: dict, index: int, inputs: dict, files: dict) -> tuple[dict, str, list[str]]:
    """J5/J8: (the job's D-2 entry, the script, the D-2 arguments). The D-2 route passes --pool-pins and
    --req8-record as PATH:SHA256 of the packed files, which must hash to the job's plan.json pins; under the fallback
    the W1 script runs with no D-2 argument."""
    d2 = job.get("d2")
    if not isinstance(d2, dict) or not isinstance(d2.get("pools"), dict):
        raise Unrunnable(f"job {index} ({job['kind']}): plan.json carries no D-2 pins for this job")
    if d2.get("fallback"):
        return d2, (REP_SCRIPT if job["kind"] == "rep_pass" else CLASSIFIER_SCRIPT), []
    extra = []
    for name, key in (("d2_pool_pins", "pool_pins"), ("req8_record", "req8_record")):
        path = input_path(inputs, name)
        if files.get(path) != (d2.get(key) or {}).get("sha256"):
            raise Unrunnable(f"job {index} ({job['kind']}): the packed {name} differs from the plan's pin")
        extra += [f"--{key.replace('_', '-')}", f"{path}:{files[path]}"]
    return d2, (rules.D2_REP_SCRIPT if job["kind"] == "rep_pass" else rules.D2_CLASSIFIER_SCRIPT), extra


def s3_orig_arg(job: dict, index: int, h: dict, inputs: dict, files: dict) -> str:
    """J5's s3_orig pools-only pass reads J6's s3_orig pool. A J5 moved off J6's pod (defer; J6 complete there and
    never re-run, PREREG) carries plan.json's pin (job.s3_orig: the pool's SHA-256 from J6's own
    untuned_answers_record.json, checked by plan_tool) and reads the packed input pool:s3_orig, which must hash to it;
    otherwise J6 runs earlier on this pod and the pass reads its output (@pathsha, resolved before the step)."""
    pin = (job.get("s3_orig") or {}).get("sha256")
    if pin is not None:
        path = input_path(inputs, S3_ORIG_INPUT)
        if files.get(path) != pin:
            raise Unrunnable(f"job {index} (rep_pass): the packed s3_orig pool differs from the plan's pin (J6's record)")
        return f"{path}:{files[path]}"
    earlier = [k for k in range(index) if h["jobs"][k]["kind"] == "untuned_answers"]
    if not earlier:
        raise Unrunnable(f"job {index} (rep_pass): no untuned_answers job earlier on this pod and no pinned s3_orig "
                         "pool (pool:s3_orig) for the s3_orig pools-only pass")
    return f"@pathsha:job-{earlier[-1]}/untuned/s3_orig.pool.json"   # REQ-3's s3_orig pass after J6 (same pod)


def pool_arg(job: dict, index: int, inputs: dict, files: dict, name: str) -> str:
    """PATH:SHA256 of a packed pool, which must hash to the job's plan.json pool pin."""
    path = input_path(inputs, f"pool:{name}")
    if files.get(path) != job["d2"]["pools"].get(name):
        raise Unrunnable(f"job {index} ({job['kind']}): the packed {name} pool differs from the plan's pin")
    return f"{path}:{files[path]}"


def job_commands(plan: dict, host: str, index: int, root: pathlib.Path, units: dict,
                 sealed_doc: dict | None = None) -> list[tuple[str, list[str]]]:
    """(receipt name, argv) of job ``index`` (brief §3). ``units`` maps an earlier job index to its unit folder;
    placeholders "@..." are resolved just before their step (``resolve``)."""
    h = plan["hosts"][host]
    job = h["jobs"][index]
    kind, seed = job["kind"], job.get("seed")
    sealed_doc = sealed_doc if sealed_doc is not None else load_sealed(root)
    inputs, files = inputs_of(sealed_doc), dict(sealed_doc.get("files") or {})
    rec, tag, out = recipe_path(job), f"job-{index}", f"job-{index}"
    p = PREPARED
    fallback = oext_fallback(plan)
    if fallback and kind in rules.OEXT_ONLY_KINDS:
        raise Unrunnable(f"job {index} ({kind}): fallback (c) is recorded; an O-ext pass never runs")
    try:
        if kind == "w1_18":
            return [(f"{tag}-w1-18", [*SCRIPT, W1_18_SCRIPT, "--out", f"{out}/w1-18", "--data-root", DATA,
                                      "--device", "cuda", "--guard-batch-size", guard_batch(root)])]
        if kind in ("regenerate", "cert_c1", "cert_c2", "cert_c3", "c0", "retrain"):
            return _run_one(job, index, root, rec, inputs, files, fallback)
        if kind == "a1_rescore":
            return _rescore(job, index, root, rec, inputs, units)
        if kind == "o_only":
            if job.get("arm") == "theta0":
                state = ["--untuned"]
            else:
                state = ["--run", units.get(job[rules.LINK_FIELD], f"@unit:{job[rules.LINK_FIELD]}"),
                         "--checkpoint", "e1"]
                if dev100_source(job):
                    state += ["--dev100-source", input_path(inputs, dev100_source(job))]
            return [(f"{tag}-oext", [*SCRIPT, OEXT_UNIT_SCRIPT, "run", *state, "--prepared", p, "--recipe", rec,
                                     *oext_args(inputs), "--out", f"{out}/oext"])]
        if kind == "transfer_report":
            return [(f"{tag}-transfer", [*SCRIPT, OEXT_UNIT_SCRIPT, "transfer", "--untuned", "--prepared", p,
                                         "--recipe", rules.REC, *oext_args(inputs), "--out", f"{out}/transfer"])]
        if kind == "rep_pass":
            _, script, extra = d2_route(job, index, inputs, files)
            pools = [a for name in (POOLS_J5 if extra else ("s3_safe",))
                     for a in ("--pool", pool_arg(job, index, inputs, files, name))]
            s3 = s3_orig_arg(job, index, h, inputs, files)
            anchors = input_path(inputs, "anchor_bank")
            # REQ-3's recipe is recipe S (representation_pass.json pins.recipe_sha256), never REC (pod a-1, 25 Oct)
            return [(f"{tag}-representation", [*SCRIPT, script, "--prepared", p, "--recipe", rules.RECIPE_S,
                                               "--anchors", anchors, *pools, "--out", f"{out}/representation", *extra]),
                    (f"{tag}-representation-s3-orig",
                     [*SCRIPT, script, "--prepared", p, "--recipe", rules.RECIPE_S, "--anchors", anchors, "--pool",
                      s3, "--pools-only", "--out", f"{out}/representation-s3-orig", *extra])]
        if kind == "untuned_answers":
            lists = [a for flag, name in J6_LISTS if inputs.get(f"{flag}:{name}")
                     for a in (f"--{flag}", f"{name}={pathsha(inputs, files, f'{flag}:{name}')}")]
            return [(f"{tag}-untuned", [*SCRIPT, UNTUNED_SCRIPT, "--recipe", rules.REC, "--recipe-s", rules.RECIPE_S,
                                        *lists, "--out", f"{out}/untuned"])]
        if kind == "l1_scan":
            return [(f"{tag}-l1-scan", [*SCRIPT, L1_SCRIPT, "scan", "--prepared", p, "--recipe", rules.REC,
                                        "--anchors", input_path(inputs, "anchor_bank"), "--out", f"{out}/l1-scan"])]
        if kind == "classifier":
            _, script, extra = d2_route(job, index, inputs, files)
            pools = [a for name in (POOLS_J8 if extra else ()) for a in
                     ("--pool", pool_arg(job, index, inputs, files, name))]
            return [(f"{tag}-classifier", [*SCRIPT, script, "--prepared", p, "--recipe", rules.RECIPE_S,
                                           "--anchors", input_path(inputs, "anchor_bank"), *pools,
                                           "--out", f"{out}/classifier", *extra])]
        if kind in ("arm", "a0_arm", "ref_train"):
            arm = engine_arm(job)
            edit = ["--edit", edit_bundle(job)] if job.get("edit") else []
            steps = [(f"{tag}-calibrate", [*ENGINE, "calibrate", "--prepared", p, "--recipe", rec, "--arms", arm,
                                           *edit, "--seeds", str(seed), "--checkpoints", "e1", "--out-root", ROUND])]
            if not fallback:
                steps.append((f"{tag}-oext", [*SCRIPT, OEXT_UNIT_SCRIPT, "run", "--run", f"@unit:{index}",
                                              "--checkpoint", "e1", "--prepared", p, "--recipe", rec,
                                              *oext_args(inputs), "--out", f"{out}/oext"]))
            return steps
        if kind in ("b10_certify", "ref_eval"):
            ref = input_path(inputs, f"gate_a_complete:{seed}")
            common = ["--prepared", p, "--recipe", rules.REC, "--seed", str(seed), "--reference", ref,
                      "--regen-out", f"{out}/regen", "--eval-root", f"{out}/evals", "--evaluations",
                      ",".join(job["points"])]
            if kind == "b10_certify":
                extra = ["--gate-reference-eval", input_path(inputs, f"gate_a_eval:{seed}")]
                extra += oext_args(inputs) if inputs.get("oext_bank") and not fallback else []
            else:
                cert = input_path(inputs, "certification_report")
                extra = (["--prefix-file", input_path(inputs, "prefix_file")] if "prefix" in job["points"] else [])
                extra += ["--certification-report", cert, "--certification-report-sha256", files[cert],
                          *([] if fallback else oext_args(inputs))]
            return [(f"{tag}-b10-run", [*SCRIPT, B10_SCRIPT, "run", *common, *extra])]
        if kind == "safe_lora":
            return _safe_lora(job, index, inputs, files, fallback)
    except KeyError as exc:
        raise Unrunnable(f"job {index} ({kind}): the stage-1 input {exc.args[0]!r} is not packed") from None
    raise ValueError(f"unknown job kind {kind!r}")


def _run_one(job: dict, index: int, root: pathlib.Path, rec: str, inputs: dict, files: dict,
             fallback: bool = False) -> list:
    """The engine's make-job run-one and run-one (J2, C1-C3) or B17's lean job (c0)."""
    kind, seed, tag = job["kind"], str(job["seed"] if job.get("seed") is not None else 1101), f"job-{index}"
    label = {"regenerate": f"{job['arm']}-regen", "cert_c1": "R-c1", "cert_c2": "bqi-c2", "cert_c3": "a0-c3",
             "c0": "R-c0", "retrain": "a0-retrain"}[kind]
    n = next_attempt(root, f"jobs/{kind}-{seed}-{label}-a")
    job_file = f"jobs/{kind}-{seed}-{label}-a{n}.json"
    arm = ["--edit", edit_bundle(job)] if job.get("edit") else ["--arm", "a0"]
    make = [*ENGINE, "make-job", "run-one", "--prepared", PREPARED, "--recipe", rec, "--split", "dev", *arm,
            "--seed", seed, "--role", "development", "--target", "e1"]
    if kind == "cert_c1":
        make += ["--bank", "dev", "--replicate-of", "@json:cert_spec:replicate_of"]
        input_path(inputs, "cert_spec")
    if kind == "cert_c3":
        sub, rec_c3, pin = input_path(inputs, "c3_subsample"), input_path(inputs, "c3_record"), job.get("c3") or {}
        if files.get(sub) != (pin.get("subsample") or {}).get("sha256") or \
                files.get(rec_c3) != (pin.get("record") or {}).get("sha256"):
            raise Unrunnable(f"job {index} (cert_c3): the packed subsample file or its record differs from the plan's "
                             "C3 pin (addendum §22 point 2)")
        make += ["--bank", f"subsample-{pin['subsample']['sha256']}", "--bank-file", sub]
    make += ["--pin-code", "--out", job_file]
    if kind == "c0":
        input_path(inputs, "source_complete:R:1101")
        lean = [*SCRIPT, B17_SCRIPT, "run", "--job", job_file, "--prepared", PREPARED, "--recipe", rec,
                "--out", f"{tag}/c0", "--registry", f"{tag}/c0-registry.jsonl",
                "--expect-adapter-fingerprint", "@fingerprint:source_complete:R:1101",
                *([] if fallback else oext_args(inputs))]
        return [(f"{tag}-make-job", make), (f"{tag}-lean", lean)]
    folder = CERT_ROOT if kind.startswith("cert_") else RESCORE_ROOT if kind == "retrain" else ROUND
    registry = f"{CERT_ROOT}/registry-{kind}.jsonl" if kind.startswith("cert_") else \
        f"{RESCORE_ROOT}/registry.jsonl" if kind == "retrain" else f"{ROUND}/registry.jsonl"
    out = f"{folder}/{seed}-{label}-a{next_attempt(root, f'{folder}/{seed}-{label}-a')}"
    return [(f"{tag}-make-job", make),
            (f"{tag}-run-one", [*ENGINE, "run-one", "--job", job_file, "--prepared", PREPARED, "--recipe", rec,
                                "--out", out, "--registry", registry])]


def _rescore(job: dict, index: int, root: pathlib.Path, rec: str, inputs: dict, units: dict) -> list:
    """LN-15e (J21): Gate B's diagnostics attributes step (make-job attributes, then attributes) on the q and e1
    states of the retrain that regen_source names on this pod, with plan.json's 8 unit groups and the packed anchor
    bank. No Gate C script runs (the re-score is A1's score only)."""
    seed, tag = str(job["seed"]), f"job-{index}"
    groups = job.get("groups")
    if not (isinstance(groups, list) and len(groups) == rules.UNITS and all(isinstance(g, str) for g in groups)):
        raise Unrunnable(f"job {index} (a1_rescore): plan.json carries no {rules.UNITS} unit groups for the re-score")
    if len(set(groups)) != len(groups):                  # round 3b fix (F4): 8 distinct groups, as plan_tool plans
        raise Unrunnable(f"job {index} (a1_rescore): plan.json carries no {rules.UNITS} unit groups for the re-score "
                         "(a group is repeated)")
    state = units.get(job[rules.LINK_FIELD], f"@unit:{job[rules.LINK_FIELD]}")
    n = next_attempt(root, f"jobs/a1_rescore-{seed}-a")
    job_file, out = f"jobs/a1_rescore-{seed}-a{n}.json", f"{RESCORE_ROOT}/{seed}-attributes-a{n}"
    make = [*ENGINE, "make-job", "attributes", "--prepared", PREPARED, "--recipe", rec, "--split", "dev",
            "--seed", seed, "--role", "development",
            *[a for c in rules.RESCORE_CHECKPOINTS for a in ("--a0-state", f"{c}={state}")],
            "--groups", ",".join(groups), "--anchors", input_path(inputs, "anchor_bank"), "--pin-code",
            "--out", job_file]
    return [(f"{tag}-make-job", make),
            (f"{tag}-attributes", [*ENGINE, "attributes", "--job", job_file, "--prepared", PREPARED, "--recipe", rec,
                                   "--out", out])]


def _safe_lora(job: dict, index: int, inputs: dict, files: dict, fallback: bool = False) -> list:
    """J17: regenerate a0 at seed j (B10), the V/V' check BEFORE the projection, B11's check, then per point the
    transform and B10's external evaluation of its file (both by SHA-256)."""
    seed, tag, out = str(job["seed"]), f"job-{index}", f"job-{index}"
    if "k12" in job["points"]:
        raise Unrunnable(f"job {index}: B11 offers no K = 12 point (safe_lora.POINTS); the kit refuses it")
    ref = input_path(inputs, f"gate_a_complete:{seed}")
    cert = input_path(inputs, "certification_report")
    state = f"{out}/regen/run/states/e1"
    models = ["--seed", seed, "--aligned", "@snapshot:policy", "--base", "@snapshot:base"]
    steps = [(f"{tag}-b10-regenerate", [*SCRIPT, B10_SCRIPT, "regenerate", "--prepared", PREPARED, "--recipe", rules.REC,
                                        "--seed", seed, "--reference", ref, "--out", f"{out}/regen"]),
             (f"{tag}-vcheck", [*SCRIPT, B11_SCRIPT, "vcheck", "--adapter", state, *models, "--out", f"{out}/vcheck"]),
             (f"{tag}-check", [*SCRIPT, B11_SCRIPT, "check", "--adapter", state, *models, "--out", f"{out}/check"])]
    for point in job["points"]:
        folder = f"{out}/transform-{point}"
        steps.append((f"{tag}-transform-{point}", [*SCRIPT, B11_SCRIPT, "transform", "--point", point, "--adapter",
                                                   state, *models, "--out", folder]))
        steps.append((f"{tag}-evaluate-{point}", [
            *SCRIPT, B10_SCRIPT, "evaluate", "--prepared", PREPARED, "--recipe", rules.REC, "--source-run",
            f"{out}/regen/run", "--reference", ref, "--out", f"{out}/eval-{point}", "--mode", "external",
            "--external", "safe_lora", "--adapter-file", f"{folder}/{B11_ADAPTER}",
            "--adapter-sha256", f"@sha256:{folder}/{B11_ADAPTER}", "--adapter-record", f"{folder}/{B11_RECORD}",
            "--adapter-record-sha256", f"@sha256:{folder}/{B11_RECORD}", "--certification-report", cert,
            "--certification-report-sha256", files[cert], *([] if fallback else oext_args(inputs))]))
    return steps


def planned_unit(plan: dict, host: str, index: int, root: pathlib.Path) -> str | None:
    """The folder a regeneration (or LN-15e's retrain) would write (its run-one --out), for the dry run's linked
    commands."""
    if plan["hosts"][host]["jobs"][index]["kind"] not in rules.LINK_SOURCES:
        return None
    run = job_commands(plan, host, index, root, {})[-1][1]
    return run[run.index("--out") + 1]


def load_sealed(root: pathlib.Path) -> dict:
    path = root / "sealed-files.json"
    return json.loads(path.read_text()) if path.is_file() else {"files": {}, "inputs": {}}


def input_names(job: dict, h: dict, index: int, fallback: bool = False) -> list[str]:
    """The named stage-1 inputs a job uses (checked before the job starts)."""
    kind, seed = job["kind"], job.get("seed")
    names = []
    if (kind in rules.BANK500_KINDS or kind == "b10_certify") and not fallback:
        names += [n for n in OEXT_INPUTS] + ["w1_18_record"]
    if dev100_source(job):
        names.append(dev100_source(job))
    if kind == "w1_18":
        names.append("w1_18_data")
    if kind in ("regenerate", "o_only"):
        names.append("reuse_spec")
    if kind in ("rep_pass", "l1_scan", "classifier", "a1_rescore"):
        names.append("anchor_bank")
    if kind in rules.D2_KINDS and not d2_fallback_job(job):
        names += list(D2_INPUTS) + [f"pool:{n}" for n in (POOLS_J5 if kind == "rep_pass" else POOLS_J8)]
    elif kind == "rep_pass":
        names.append("pool:s3_safe")                       # §19 point 4: no plant or decoy under the D-2 fallback
    if kind == "rep_pass" and (job.get("s3_orig") or {}).get("sha256") is not None:
        names.append(S3_ORIG_INPUT)                        # a J5 moved off J6's pod: J6's s3_orig pool by its pin
    if kind == "untuned_answers":
        names += [f"{f}:{n}" for f, n in J6_LISTS]
    if kind in ("b10_certify", "ref_eval", "safe_lora"):
        names.append(f"gate_a_complete:{seed}")
    if kind == "b10_certify":
        names.append(f"gate_a_eval:{seed}")
    if kind in ("ref_eval", "safe_lora"):
        names.append("certification_report")
    if kind == "ref_eval" and "prefix" in (job.get("points") or []):
        names.append("prefix_file")
    if kind == "c0":
        names.append("source_complete:R:1101")
    if kind == "cert_c1":
        names.append("cert_spec")
    if kind == "cert_c3":
        names += ["c3_subsample", "c3_record"]
    return names


def sealed_paths(job: dict, h: dict, index: int, sealed_doc: dict, fallback: bool = False) -> list[str]:
    """Every bundle file a job uses: its scripts and settings, the O-ext module, the edit file, the named inputs
    (a folder input covers every sealed file under it). Each is checked against sealed-files.json first. Under
    fallback (c) the O-ext files and inputs are not used."""
    kind = job["kind"]
    files, inputs = sealed_doc.get("files") or {}, inputs_of(sealed_doc)
    paths = list(SCRIPTS.get(kind, []))
    if kind in D2_SCRIPTS and not d2_fallback_job(job):
        paths += [f for f in D2_SCRIPTS[kind] if f not in paths]
    if kind in OEXT_STEP_KINDS and not fallback:
        paths.append(OEXT_UNIT_SCRIPT)
        paths.append(OEXT_UNIT_SETTINGS)                    # round 3c: the runner's settings, sealed with it
    if (kind in OEXT_STEP_KINDS or kind in B10_OEXT_KINDS) and not fallback:
        paths += [OEXT_MODULE, "scripts/stage1_s1/settings/oext_eval.json"]
    if job.get("edit"):
        paths.append(edit_bundle(job))
    for name in input_names(job, h, index, fallback):
        path = inputs.get(name)
        if path is None:
            if (name == "w1_18_record" and job.get("branch") != "128") or name.startswith(("list:", "loss:")):
                continue                                   # optional: passed only when packed
            # (F) under Branch 128 the O-ext settings pin W1-18's record: every O-ext step needs it packed
            paths.append(f"<input {name}>")
            continue
        under = [f for f in files if f.startswith(path.rstrip("/") + "/")]
        paths += under if under and path not in files else [path]
    return paths


def sealed_check(job: dict, sealed: dict, root: pathlib.Path, h: dict | None = None, index: int = 0,
                 sealed_doc: dict | None = None, fallback: bool = False) -> list[str]:
    """Names of the job's files that are not listed or differ from sealed-files.json; an edit file must also hash to
    its job's edit SHA-256 and engine arm (edit-<SHA-256 of its bytes>)."""
    doc = sealed_doc if sealed_doc is not None else {"files": sealed, "inputs": {}}
    bad = []
    for rel in sealed_paths(job, h or {"jobs": [job]}, index, doc, fallback):
        path = root / rel
        if rel.startswith("<input ") or rel not in sealed or not path.is_file() or sha(path) != sealed[rel]:
            bad.append(rel)
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


def complete_attempts(root: pathlib.Path, pattern: str) -> set[str]:
    return {str(p.parent.relative_to(root)) for p in root.glob(f"{pattern}/COMPLETE.json")}


def _engine_identity() -> str:
    from experiments.safety_selection.common import code_identity
    return code_identity()["sha256"]


def _recipe_config_sha(path: pathlib.Path) -> str:
    from experiments.safety_selection.config import config_sha256, load_recipe
    return config_sha256(load_recipe(str(path)))


def preflight_checks(plan: dict, host: str, pre: dict, root: pathlib.Path) -> dict:
    """Refuse (AssertionError) before any job unless the pod is the planned one; returns sealed-files.json's doc."""
    h = plan["hosts"][host]
    jobs = h["jobs"]
    present = [name for name in TOKEN_ENV_NAMES if os.environ.get(name)]
    assert not present and not (pathlib.Path.home() / ".cache/huggingface/token").exists(), "a token is present"
    assert not (root / "JOB-DONE.json").exists(), "this host already ran its jobs"
    assert json.loads((root / "BOOTSTRAP-READY.json").read_text())["ok"] is True, "bootstrap not ready"
    assert pre.get("ok") is True and pre.get("recipe") == preflight_recipe(h), \
        "the preflight did not pass for the host's recipe"
    assert pre.get("cap_projection") or not any(j["kind"] in rules.ARM_LIKE_KINDS or j["kind"] in rules.LINK_SOURCES
                                                for j in jobs), "no preflight projection for an arm or a regeneration"
    assert h["engine"] in rules.ENGINES and h["engine_sha256"] == rules.ENGINES[h["engine"]], \
        "the host's engine is not a pinned engine (G4)"
    assert all(j["engine"] == h["engine"] for j in jobs), "two engines on one pod (G4)"
    assert _engine_identity() == h["engine_sha256"], "engine code differs from the plan (G4)"
    for path in sorted({recipe_path(j) for j in jobs} | {rules.REC}):
        if path not in plan.get("recipes", {}):
            if path == rules.REC and not any(recipe_path(j) == path for j in jobs):
                continue
            raise AssertionError(f"recipe {pathlib.Path(path).name} is not in plan.json")
        assert sha(root / path) == rules.RECIPE_PINS[path], f"recipe {pathlib.Path(path).name} differs from its pin"
        assert _recipe_config_sha(root / path) == plan["recipes"][path]["config_sha256"], \
            f"recipe {pathlib.Path(path).name} differs from the plan"
    name, digest = next(iter(sorted(plan["prepared"].items())))
    assert (root / PREPARED / "manifest.sha256").read_text().strip() == digest, "prepared data differ from the plan"
    assert sha(root / "sealed-files.json") == h["sealed_files_sha256"], "sealed-files.json differs from the plan"
    doc = json.loads((root / "sealed-files.json").read_text())
    sealed = doc["files"]
    bad = [rel for rel, d in sealed.items() if not (root / rel).is_file() or sha(root / rel) != d]
    assert not bad, f"{len(bad)} sealed file(s) missing or changed"
    branch = (plan.get("records") or {}).get("branch")
    for j in jobs:
        if j["kind"] in rules.BANK500_KINDS:
            assert branch is not None, "a 500-bank job before W1-18's branch record (G1)"
            assert j["branch"] == branch["branch"], "a 500-bank job on another branch than the recorded one (G1)"
    if any(j["kind"] == "w1_18" for j in jobs):
        assert len(jobs) == 1, "W1-18 runs alone on its pod (§8 Q1 (a))"
    return doc


def resolve(argv: list[str], root: pathlib.Path, units: dict, sealed_doc: dict) -> list[str]:
    """Replace the run-time placeholders: @unit:K (job K's unit), @sha256:REL, @pathsha:REL (REL:SHA256),
    @snapshot:ROLE (model-download-receipt.json), @json:INPUT:KEY (a text-free record's field) and
    @fingerprint:INPUT (a pinned COMPLETE.json's e1 adapter fingerprint)."""
    inputs, files = inputs_of(sealed_doc), sealed_doc.get("files") or {}
    out = []
    for v in argv:
        if not v.startswith("@"):
            out.append(v)
            continue
        head, _, rest = v[1:].partition(":")
        if head == "unit":
            out.append(units[int(rest)])
        elif head == "sha256":
            out.append(sha(root / rest))
        elif head == "pathsha":
            out.append(f"{rest}:{sha(root / rest)}")
        elif head == "snapshot":
            models = json.loads((root / "model-download-receipt.json").read_text())["models"]
            out.append(models[rest]["snapshot"])
        elif head in ("json", "fingerprint"):
            name, _, key = rest.rpartition(":") if head == "json" else (rest, "", None)
            path = input_path(inputs, name)
            if sha(root / path) != files.get(path):
                raise ValueError(f"the input {name} differs from sealed-files.json")
            doc = json.loads((root / path).read_text())
            out.append(str(doc[key]) if head == "json" else doc["checkpoints"]["e1"]["adapter_fingerprint"])
        else:
            out.append(v)
    return out


STEP_STAGE = (("-make-job", "setup"), ("-calibrate", "training"), ("-run-one", "training"),
              ("-b10-regenerate", "training"), ("-lean", "training"), ("-oext", "greedy_generation"),
              ("-transfer", "greedy_generation"), ("-untuned", "greedy_generation"), ("-b10-run", "greedy_generation"),
              ("-evaluate-", "greedy_generation"), ("-w1-18", "judging"), ("-representation", "scoring"),
              ("-l1-scan", "scoring"), ("-classifier", "scoring"), ("-vcheck", "scoring"), ("-check", "scoring"),
              ("-transform-", "setup"), ("-verify", "scoring"), ("-attributes", "scoring"))


def stage_of(step: str) -> str:
    return next(stage for suffix, stage in STEP_STAGE if suffix in step)


def write_ledger(root: pathlib.Path, index: int, job: dict, host: str, engine_sha: str, started: float,
                 ended: float, steps: list[dict]) -> str:
    """job-I/cost-ledger.json (FR-10): stage seconds by step, the transform's own seconds.total as "transform" (its
    step's wall time is then not counted again), and the job slot (start to end inside the pod)."""
    stages = {s: 0.0 for s in LEDGER_STAGES}
    for step in steps:
        if step.get("transform_seconds_total") is not None:
            stages["transform"] += float(step["transform_seconds_total"])
        else:
            stages[stage_of(step["name"])] += step["seconds"]
    ledger = {"kind": "stage1 cost ledger", "version": 1, "host": host, "index": index, "job_kind": job["kind"],
              "job_id": job.get("job_id"), "arm": job.get("arm"), "seed": job.get("seed"), "engine": job["engine"],
              "engine_sha256": engine_sha, "stages_s": {k: round(v, 3) for k, v in stages.items()},
              "slot_s": round(ended - started, 3), "steps": steps,
              "rule": "FR-10 stages in GPU-seconds of this job's steps (engine steps count as training; the engine "
                      "unit's own ledger splits them); the transform stage is safe_lora_timing.json seconds.total"}
    (root / f"job-{index}").mkdir(parents=True, exist_ok=True)
    path = root / f"job-{index}" / LEDGER_FILE
    path.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n")
    return f"job-{index}/{LEDGER_FILE}"


def reuse_entry(spec: dict, job: dict) -> dict:
    """reuse_spec.json's regenerate job of this (engine arm, seed)."""
    arm = engine_arm(job)
    found = [j for j in spec.get("jobs") or [] if j.get("kind") == "regenerate" and j.get("seed") == job["seed"]
             and j.get("arm") == arm]
    if len(found) != 1:
        raise ValueError(f"reuse_spec.json holds no single regeneration of {job['arm']} at {job['seed']}")
    if not isinstance(found[0].get("accept"), dict) or not found[0]["accept"]:
        raise ValueError("reuse_spec.json's regeneration lists no accept fields")
    return found[0]


def regenerated_value(complete: dict, field: str):
    if field == "e1_adapter_fingerprint":
        return ((complete.get("checkpoints") or {}).get("e1") or {}).get("adapter_fingerprint")
    return (complete.get("identity") or {}).get(field)


def acceptance(root: pathlib.Path, unit: str, job: dict, index: int, sealed_doc: dict) -> dict:
    """J2 (LN-12): every field reuse_spec.json lists under ``accept`` against the regenerated unit's COMPLETE.json;
    written to job-I/regeneration-adapter-fingerprint.json (fingerprints and identities only)."""
    inputs, files = inputs_of(sealed_doc), sealed_doc.get("files") or {}
    path = input_path(inputs, "reuse_spec")
    if sha(root / path) != files.get(path):
        raise ValueError("reuse_spec.json differs from sealed-files.json")
    entry = reuse_entry(json.loads((root / path).read_text()), job)
    complete = json.loads((root / unit / "COMPLETE.json").read_text())
    fields = {f: {"source": v, "regenerated": regenerated_value(complete, f),
                  "equal": regenerated_value(complete, f) == v} for f, v in sorted(entry["accept"].items())}
    record = {"kind": "stage1 regeneration acceptance", "version": 1, "job": index, "arm": job["arm"],
              "seed": job["seed"], "unit": unit, "reuse_spec_sha256": files[path], "spec_job": entry.get("id"),
              "fields": fields, "pass": all(f["equal"] for f in fields.values()),
              "failure": None if all(f["equal"] for f in fields.values()) else LS04}
    (root / f"job-{index}").mkdir(parents=True, exist_ok=True)
    (root / f"job-{index}" / ACCEPT_FILE).write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return record


def output_files(root: pathlib.Path, folders: list[str]) -> dict:
    """relpath -> SHA-256 of every regular file under the folders (hashes only; no file is parsed)."""
    out = {}
    for folder in folders:
        base = root / folder
        if base.is_file():
            out[folder] = sha(base)
        elif base.is_dir():
            for p in sorted(base.rglob("*")):
                if p.is_file() and not p.is_symlink():
                    out[str(p.relative_to(root))] = sha(p)
    return out


def out_folders(commands: list) -> list[str]:
    folders = []
    for _, argv in commands:
        for flag in ("--out", "--eval-root", "--regen-out"):
            if flag in argv:
                folders.append(argv[argv.index(flag) + 1])
    return folders


def run_job(plan: dict, host: str, index: int, root: pathlib.Path, units: dict, env: dict, sealed_doc: dict) -> dict:
    """Run one job's steps; the record says complete (unit, COMPLETE.json SHA-256, outputs) or crashed."""
    h = plan["hosts"][host]
    job = h["jobs"][index]
    kind = job["kind"]
    commands = job_commands(plan, host, index, root, units, sealed_doc)
    arm = engine_arm(job)
    pattern = f"{ROUND}/{job['seed']}-{arm}-e1-a*" if kind in ("arm", "a0_arm", "ref_train") else None
    before = complete_attempts(root, pattern) if pattern else set()
    exits, steps, unit = {}, [], None
    for name, raw in commands:
        if name.endswith("-oext") and kind in ("arm", "a0_arm", "ref_train"):
            new = sorted(complete_attempts(root, pattern) - before)
            if len(new) != 1:
                return {"status": "crashed", "why": "no new COMPLETE.json", "exits": exits, "steps": steps}
            unit = new[0]
            units[index] = unit
        if ("-check" in name or "-transform-" in name) and kind == "safe_lora" and \
                not (root / f"job-{index}" / "vcheck" / VCHECK_FILE).is_file():
            return {"status": "crashed", "why": "the V/V' check did not run before the projection", "exits": exits,
                    "steps": steps}
        try:
            argv = resolve(raw, root, units, sealed_doc)
        except (KeyError, ValueError, OSError) as exc:
            return {"status": "crashed", "why": f"cannot resolve {name}: {type(exc).__name__}", "exits": exits,
                    "steps": steps}
        start = time.monotonic()
        done = subprocess.run(["python3", "process_receipt.py", "--out", name, "--", *argv], env=env, cwd=root)
        step = {"name": name, "seconds": round(time.monotonic() - start, 3), "exit": done.returncode}
        if "-transform-" in name and done.returncode == 0:
            timing = root / argv[argv.index("--out") + 1] / TIMING_FILE
            try:
                step["transform_seconds_total"] = float(json.loads(timing.read_text())["seconds"]["total"])
            except (OSError, ValueError, KeyError, TypeError):
                return {"status": "crashed", "why": "the transform wrote no readable timing file", "exits": exits,
                        "steps": steps + [step]}
        steps.append(step)
        exits[name] = done.returncode
        if done.returncode:
            return {"status": "crashed", "why": f"exit {done.returncode} in {name}", "exits": exits, "steps": steps}
    record = {"exits": exits, "steps": steps}
    if kind in ("arm", "a0_arm", "ref_train") and unit is None:      # fallback (c): no O-ext step found it
        new = sorted(complete_attempts(root, pattern) - before)
        if len(new) != 1:
            return {**record, "status": "crashed", "why": "no new COMPLETE.json"}
        unit = new[0]
    b10_units = []
    if kind in ("regenerate", "cert_c1", "cert_c2", "cert_c3", "retrain", "a1_rescore"):
        run = commands[-1][1]
        candidate = run[run.index("--out") + 1]
        unit = candidate if (root / candidate / "COMPLETE.json").is_file() else None
    elif kind in ("b10_certify", "ref_eval", "safe_lora"):
        found = sorted(str(p.parent.relative_to(root)) for p in (root / f"job-{index}").rglob("COMPLETE.json")
                       if (p.parent / "job.json").is_file() and "regen" not in p.parent.relative_to(root).parts)
        if len(found) != len(job["points"]):              # one B10 unit per evaluation point
            return {**record, "status": "crashed",
                    "why": f"{len(found)} B10 unit(s) for {len(job['points'])} evaluation point(s)"}
        b10_units = found
        unit = found[0] if found else None
    elif kind in rules.UNITLESS_KINDS:
        outputs = output_files(root, out_folders(commands))
        if not outputs:
            return {**record, "status": "crashed", "why": "no output"}
        return {**record, "status": "complete", "unit": None, "complete_sha256": None, "outputs": outputs,
                "verified": None}
    if unit is None:
        return {**record, "status": "crashed", "why": "no new COMPLETE.json"}
    if kind in ("b10_certify", "ref_eval", "safe_lora"):
        checks = [subprocess.run([*SCRIPT, B10_SCRIPT, "verify", "--unit", u], env=env, cwd=root,
                                 capture_output=True, text=True) for u in b10_units]
        record["units"] = [{"unit": u, "complete_sha256": sha(root / u / "COMPLETE.json"), "verify_exit": c.returncode}
                           for u, c in zip(b10_units, checks)]
        check = next((c for c in checks if c.returncode), checks[0])
    else:
        check = subprocess.run([*ENGINE, "verify", "--run", unit, "--prepared", PREPARED], env=env, cwd=root,
                               capture_output=True, text=True)
    record.update(unit=unit, complete_sha256=sha(root / unit / "COMPLETE.json"),
                  verified={"exit": check.returncode, "tail": (check.stdout + check.stderr)[-600:]})
    outputs = output_files(root, [f for f in out_folders(commands) if f.startswith(f"job-{index}")])
    if kind == "regenerate":
        try:
            accepted = acceptance(root, unit, job, index, sealed_doc)
        except (KeyError, ValueError, OSError) as exc:
            return {**record, "status": "crashed", "why": f"the acceptance check failed to run: {exc}"}
        record["acceptance"] = accepted["pass"]
        outputs[f"job-{index}/{ACCEPT_FILE}"] = sha(root / f"job-{index}" / ACCEPT_FILE)
        if not accepted["pass"]:
            record["reason"] = LS04
    record["outputs"] = outputs
    if check.returncode:
        return {**record, "status": "crashed", "why": "the unit's verify failed"}
    return {**record, "status": "complete"}


def write_record(root: pathlib.Path, index: int, record: dict) -> None:
    (root / "job-done").mkdir(exist_ok=True)
    (root / "job-done" / f"JOB-{index}.json").write_text(json.dumps(record, indent=2) + "\n")


def base_record(job: dict, index: int, h: dict, engine_sha: str) -> dict:
    return {"index": index, "kind": job["kind"], "arm": job["arm"], "seed": job["seed"], "engine": job["engine"],
            "engine_sha256": engine_sha, "job_id": job.get("job_id")}


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
        planned, out = {}, []
        doc = load_sealed(root)
        for i, job in enumerate(jobs):
            try:
                commands = [[name, argv] for name, argv in job_commands(plan, host, i, root, planned, doc)]
            except Unrunnable as exc:
                commands = {"unrunnable": str(exc)}
            out.append({"index": i, "kind": job["kind"], "arm": job["arm"], "seed": job["seed"],
                        "engine": job["engine"], "commands": commands,
                        "inputs": [p for p in sealed_paths(job, h, i, doc, oext_fallback(plan))]})
            if job["kind"] in rules.LINK_SOURCES:
                planned[i] = planned_unit(plan, host, i, root)
        print(json.dumps({"host": host, "engine": h["engine"], "jobs": out}, indent=1))
        return 0
    pre = json.loads((root / "PREFLIGHT-DONE.json").read_text())
    sealed_doc = preflight_checks(plan, host, pre, root)
    sealed = sealed_doc["files"]
    engine_sha = h["engine_sha256"]
    env = {k: v for k, v in os.environ.items() if k not in TOKEN_ENV_NAMES}
    env.update({"CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
                "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(root), "HF_HUB_OFFLINE": "1"})
    for folder in (ROUND, "jobs", CERT_ROOT, RESCORE_ROOT):
        (root / folder).mkdir(exist_ok=True)
    need = rules.requirements(jobs, pre.get("cap_projection") or {})
    records, units, stopped, held = [], {}, None, {}
    for i, job in enumerate(jobs):
        left = remaining(dt.datetime.now(dt.timezone.utc))
        base = {**base_record(job, i, h, engine_sha), "requirement_s": need[i], "remaining_s": left, "utc": utc()}
        if i in held:                                    # LS-04 (a): the O-only pass of a refused regeneration waits
            rec = {**base, "status": "not_started", "reason": LS04, "held_by": held[i]}
            records.append(rec)
            write_record(root, i, rec)
            continue
        bad = sealed_check(job, sealed, root, h, i, sealed_doc, oext_fallback(plan))
        if left is None:
            stopped = "heartbeat_unreadable"
        elif not rules.gate(left, need[i]):
            stopped = "deferred"
        elif bad:
            stopped = "sealed_file_mismatch"
            base["sealed_mismatch"] = bad
        if stopped:
            later = "deferred" if stopped == "deferred" else "not_started"
            for k in range(i, len(jobs)):
                rec = {**base, "status": later} if k == i else {**base_record(jobs[k], k, h, engine_sha),
                                                                 "requirement_s": need[k], "status": later}
                records.append(rec)
                write_record(root, k, rec)
            if stopped == "deferred":
                (root / "deferral.json").write_text(json.dumps({"utc": utc(), "host": host, "first_deferred": i,
                                                                "remaining_s": left, "requirement_s": need[i],
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
        rec = {**base, **result, "ended_utc": utc()}
        records.append(rec)
        write_record(root, i, rec)
        if result["status"] != "complete":
            stopped = "crashed"
            for k in range(i + 1, len(jobs)):
                later = {**base_record(jobs[k], k, h, engine_sha), "requirement_s": need[k], "status": "not_started"}
                records.append(later)
                write_record(root, k, later)
            break
        units[i] = result.get("unit")
        if job["kind"] == "regenerate" and result.get("acceptance") is False:
            follower = rules.linked_follower(jobs, i)
            if follower is not None:
                held[follower] = i
    started_ = [r for r in records if r["status"] in ("complete", "crashed")]
    done = {"utc": utc(), "host": host, "engine": h["engine"], "engine_sha256": engine_sha, "jobs": records,
            "stopped": stopped,
            "ok": stopped in (None, "deferred") and all(r["status"] == "complete" for r in started_)}
    (root / "JOB-DONE.json").write_text(json.dumps(done, indent=2) + "\n")
    print(json.dumps({"host": host, "ok": done["ok"], "stopped": stopped,
                      "statuses": [r["status"] for r in records]}), flush=True)
    left = remaining(dt.datetime.now(dt.timezone.utc))
    if shorten(left):                                    # the last action; never extends
        subprocess.run(["python3", "extend_cap.py", str(SHORTEN_TO_S)], cwd=root)
    return 0 if done["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
