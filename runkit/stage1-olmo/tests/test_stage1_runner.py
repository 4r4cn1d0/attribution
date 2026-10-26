"""The stage-1 kit's runner side (runkit/stage1-olmo/; B15 BUILD-RUNNER; brief notes/b15-brief.md §3, §4, §6, §7 with the
lead's §8 defaults) on CPU, without RunPod, Hugging Face or GitHub: the job runner's exact commands for J1-J18 (each
engine argv parsed by engine X's or Y's own CLI parser, each stage-1 script's argv by that script's own argparse
parser, each O-ext unit step by the kit's contract parser; --dry-run writes nothing), the per-job gate with a fake
heartbeat (in order, deferral, crash, heartbeat), every input checked against its SHA-256 before use, the per-job engine
record and cost ledger, the J2 regeneration acceptance and the LS-04 hold, the Safe LoRA job (the V/V' check before the
projection, the timing in the ledger, K = 12, the base download at its commit and pins), the preflight's O500
projection, the packer per engine (X, and Y against YHASH), orchestrate's gates, the judge wrapper for B10 units and
one device per contrast, the backup's stage-1 records, and a sentinel scan of every printed line and record. Every
script runs from a copy of the kit in a temporary folder; every input is synthetic (no sealed file, row, prompt, answer
or unit evaluation file is read); every fake token is built at run time. Expected values are written by hand."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import math
import os
import random
import re
import shutil
import string
import subprocess
import sys
from pathlib import Path

import pytest

REAL_RUN = subprocess.run             # the Pod's fake replaces subprocess.run; the tests' own children use this
KIT = Path(__file__).resolve().parents[1]
REPO = KIT.parents[1]                 # this repository; nothing outside it is read (B15 round 2, item 4)
WS_B15 = WS_S1 = REPO                 # the W1 scripts and the S1 package: this tree's own scripts/
WS_Y = Path(os.environ.get("STAGE1_ENGINE_Y_TREE", str(REPO / "tmp" / "engine-y-34bfd288")))   # engine Y's frozen tree
GBK = KIT.parent / "gate-b-olmo"
PY = sys.executable
MODULES = ("stage1_rules", "gateb_mac", "plan_tool", "seal", "budget", "secret_scan", "host", "launch", "probes",
           "pack_setup", "orchestrate", "judge_units_stage1", "backup_records_stage1", "units", "common")
X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
Y = "34bfd28879fdefc5d6605cb73a707d1edd2ec5d102b4b86c0026bc6ac36969f6"
E1, T = 4360.619162873324, 333.6683323532343
SENTINELS = ("0.7319284756", "SENTINEL-U-VALUE", "41.0613", "SENTINEL-O-RATE")
P = "data/kt-prepared/prepared-kt-dolly-olmo2"
REC = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json"
S = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json"
G = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-g-mb4-20261008.json"
BQI = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-bq-mb4-20261022.json"
ENGINE = ["venv/bin/python", "-m", "experiments.safety_selection"]
H = 3600.0
FP, TI, MS, DC = "1" * 64, "2" * 64, "3" * 64, "4" * 64       # the synthetic source unit's accept fields


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(obj if isinstance(obj, str) else json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return path


def fake_token() -> str:
    rng = random.Random(os.getpid())
    return "hf" + "_" + "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(34))


@pytest.fixture
def kit(tmp_path, monkeypatch):
    """A copy of the kit at tmp/runkit/stage1-olmo (ROOT = tmp) and a loader of its modules."""
    copy = tmp_path / "runkit" / "stage1-olmo"
    shutil.copytree(KIT, copy, ignore=shutil.ignore_patterns("__pycache__", "tests"))
    monkeypatch.syspath_prepend(str(copy))
    for name in MODULES:
        monkeypatch.delitem(sys.modules, name, raising=False)

    def load(relative: str):
        spec = importlib.util.spec_from_file_location(f"s1kit_{Path(relative).stem}", copy / relative)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    load.root, load.repo = copy, tmp_path
    yield load
    for name in MODULES:
        sys.modules.pop(name, None)


# ----- a synthetic pod --------------------------------------------------------------------------------------------

EDITS = {"R1": "edit file r1 (synthetic)\n", "A1": "edit file a1 (synthetic)\n"}


def edit_ref(name: str) -> dict:
    digest = hashlib.sha256(EDITS[name].encode()).hexdigest()
    return {"path": f"x/{name}.edit.json", "sha256": digest, "source": "test"}


INPUT_FILES = {"reuse_spec": None, "oext_bank": "inputs/oext_bank/oext_bank.json",
               "oext_record": "inputs/oext_record/oext_record.json", "w1_18_record": "inputs/w1_18_record/w1.json",
               "anchor_bank": "inputs/anchor_bank/anchor_bank.json", "pool:plant": "inputs/pool-plant/plant.json",
               "pool:decoy": "inputs/pool-decoy/decoy.json", "pool:s3_safe": "inputs/pool-s3_safe/s3safe.json",
               "list:s3": "inputs/list-s3/s3.json", "list:s4": "inputs/list-s4/s4.json",
               "list:sd600": "inputs/list-sd600/sd600.json", "loss:s1": "inputs/loss-s1/s1.json",
               "loss:s3_safe": "inputs/loss-s3_safe/s3safe.json", "certification_report": "inputs/cert/1101.compare.json",
               "prefix_file": "inputs/prefix/prefix.txt", "cert_spec": "inputs/cert_spec/cert_spec.json",
               "c3_subsample": "inputs/c3/subsample.json", "source_complete:R:1101": "inputs/src-R-1101/COMPLETE.json",
               "d2_pool_pins": "inputs/d2_pool_pins/representation_pools.filled.json",
               "req8_record": "inputs/req8_record/plant_record.json", "c3_record": "inputs/c3_record/c3_record.json"}


def reuse_spec(accept_change: dict | None = None) -> dict:
    accept = {"e1_adapter_fingerprint": FP, "training_identity": TI, "manifest_sha256": MS, "data_config_sha256": DC}
    jobs = [{"id": "regenerate-a0_1101", "kind": "regenerate", "arm": "a0", "seed": 1101,
             "accept": {**accept, **(accept_change or {})}},
            {"id": "regenerate-R_1101", "kind": "regenerate", "arm": "edit-" + edit_ref("R1")["sha256"], "seed": 1101,
             "accept": dict(accept)}]
    return {"kind": "stage1 reuse job spec", "jobs": jobs}


def job(rules, kind, arm=None, seed=None, *, engine="X", points=None, recipe=None, regen_source=None, edit=None,
        steps=None, branch="full"):
    fx = {"e1_upper_s": E1, "training_s": T}
    steps = steps if steps is not None else {"arm": 33, "regenerate": 38 if arm == "a0" else 33, "a0_arm": 38,
                                             "ref_train": 38, "cert_c1": 33, "cert_c2": 38, "c0": 33,
                                             "retrain": 38}.get(kind)
    rec = rules.job_record(kind, arm, seed, edit, steps, fx, branch=branch, engine=engine, points=points,
                           recipe=recipe, regen_source=regen_source)
    if kind == "a1_rescore":                              # plan_tool.build_block's groups (Gate B's 8 unit groups)
        rec["groups"] = GROUPS
    return rec


GROUPS = [f"unit-{u}" for u in range(1, 9)]


def host_record(rules, jobs, engine="X", role="job", block="A"):
    return {"wave": block, "block": block, "launch": 0, "role": role, "base_eval": False, "engine": engine,
            "engine_sha256": rules.ENGINES[engine], "stage": f"stage1-{engine}", "sealed_files_sha256": None,
            "cap_hours": rules.cap_hours(jobs), "jobs": jobs, "done": False}


class Pod:
    """A pod folder for job_runner_stage1.main: plan.json, the sealed files and inputs, the receipts and a fake
    engine (``run``) that writes what each step would write (outcome files carry the SENTINELS)."""

    def __init__(self, kit, tmp_path, monkeypatch, jobs_spec, engine="X", branch="full", accept_change=None,
                 projection=None, omit=(), tamper=None, extra_inputs=None):
        self.runner = kit("setup/job_runner_stage1.py")
        r = self.rules = self.runner.rules
        self.root = root = tmp_path / "pod"
        root.mkdir()
        for path in (REC, S, G, BQI):
            write(root / path, {"recipe": path, "guard": {"batch_size": 8}})
            monkeypatch.setitem(r.RECIPE_PINS, path, sha(root / path))
        write(root / P / "manifest.sha256", "m" * 64 + "\n")
        sealed, inputs = {}, {}

        def seal(rel, text):
            write(root / rel, text)
            sealed[rel] = sha(root / rel)
        for rels in (*self.runner.SCRIPTS.values(), *self.runner.D2_SCRIPTS.values()):
            for rel in rels:
                seal(rel, f"# {rel}\n")
        for rel in (self.runner.OEXT_MODULE, "scripts/stage1_s1/settings/oext_eval.json", self.runner.OEXT_UNIT_SCRIPT,
                    self.runner.OEXT_UNIT_SETTINGS):                        # round 3c: the runner's settings too
            seal(rel, f"# {rel}\n")
        for name in EDITS:
            ref = edit_ref(name)
            write(root / f"edits/{ref['sha256']}.edit.json", EDITS[name])
            sealed[f"edits/{ref['sha256']}.edit.json"] = ref["sha256"]
        files = {**INPUT_FILES, **(extra_inputs or {})}
        files["reuse_spec"] = "inputs/reuse_spec/reuse_spec.json"
        for name, rel in files.items():
            if name in omit:
                continue
            body = {"reuse_spec": reuse_spec(accept_change), "cert_spec": {"replicate_of": "round1/1101-R-e1-a1"},
                    "source_complete:R:1101": {"checkpoints": {"e1": {"adapter_fingerprint": "f" * 64}}}}.get(
                name, {"synthetic": name})
            seal(rel, body)
            inputs[name] = rel
        for seed in (1101, 1104):
            seal(f"inputs/gate_a_complete-{seed}/COMPLETE.json", {"seed": seed})
            inputs[f"gate_a_complete:{seed}"] = f"inputs/gate_a_complete-{seed}/COMPLETE.json"
        seal("inputs/gate_a_eval-1101/eval/summary.json", {"x": 1})
        inputs["gate_a_eval:1101"] = "inputs/gate_a_eval-1101"
        seal("data/units/u1/COMPLETE.json", {"u": 1})
        inputs["w1_18_data"] = "data"
        seal("inputs/source_unit-a0-1101/COMPLETE.json", {"source": "a0 1101"})   # LN-19's source unit (Q15)
        inputs["source_unit:a0:1101"] = "inputs/source_unit-a0-1101"
        sealed[f"{P}/manifest.sha256"] = sha(root / P / "manifest.sha256")
        write(root / "sealed-files.json", {"kind": "stage1 sealed files", "engine": engine, "files": sealed,
                                          "inputs": inputs})
        if tamper:
            write(root / tamper, "changed after sealing\n")
        jobs = jobs_spec(r)
        for j in jobs:                                   # what plan_tool writes: the pins of the packed files
            if j["kind"] in r.D2_KINDS and "d2" not in j:
                pin = {n: {"path": inputs.get(n), "sha256": sealed.get(inputs.get(n))} for n in ("d2_pool_pins",
                                                                                                  "req8_record")}
                j["d2"] = {"pool_pins": pin["d2_pool_pins"], "req8_record": pin["req8_record"],
                           "pools": {n: sealed.get(inputs.get(f"pool:{n}")) for n in ("plant", "decoy", "s3_safe")}}
            if j["kind"] == "cert_c3" and "c3" not in j:
                j["c3"] = {k: {"path": inputs.get(n), "sha256": sealed.get(inputs.get(n))}
                           for k, n in (("subsample", "c3_subsample"), ("record", "c3_record"))}
        h = host_record(r, jobs, engine)
        h["sealed_files_sha256"] = sha(root / "sealed-files.json")
        recipes = {path: {"sha256": r.RECIPE_PINS[path], "config_sha256": "c" * 64} for path in (REC, S, G, BQI)}
        self.plan = {"hosts": {"h-1": h}, "prepared": {"prepared-kt-dolly-olmo2": "m" * 64}, "recipes": recipes,
                     "fixture": {"e1_upper_s": E1, "training_s": T},
                     "records": {"branch": {"branch": branch, "source": "w1_18"} if branch else None}}
        write(root / "plan.json", self.plan)
        write(root / "BOOTSTRAP-READY.json", {"ok": True})
        projection = projection or {"e1_upper_s": E1, "training_s": T, "overhead_s": 1000, "margin_s": 900}
        write(root / "PREFLIGHT-DONE.json", {"ok": True, "recipe": self.runner.preflight_recipe(h),
                                             "cap_projection": projection})
        write(root / "model-download-receipt.json", {"models": {"policy": {"snapshot": "/hf/instruct/48d788ec"},
                                                                "base": {"snapshot": "/hf/base/a1847dff"}}})
        monkeypatch.setattr(self.runner, "ROOT", root)
        monkeypatch.setattr(self.runner, "_engine_identity", lambda: r.ENGINES[engine])
        monkeypatch.setattr(self.runner, "_recipe_config_sha", lambda path: "c" * 64)
        monkeypatch.setenv("HOME", str(tmp_path))
        for name in self.runner.TOKEN_ENV_NAMES:
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setattr(self.runner, "HEARTBEAT", tmp_path / "heartbeat.json")
        self.ran = []
        self.fail = {}
        self.regen = {"e1_adapter_fingerprint": FP, "training_identity": TI, "manifest_sha256": MS,
                      "data_config_sha256": DC}
        monkeypatch.setattr(self.runner.subprocess, "run", self.run)
        self.mp = monkeypatch

    def remaining(self, values):
        values = list(values)
        self.mp.setattr(self.runner, "remaining", lambda now: values.pop(0) if len(values) > 1 else values[0])

    def run(self, args, **kwargs):
        self.ran.append(list(args))
        root = self.root
        if args[:2] != ["python3", "process_receipt.py"]:
            return subprocess.CompletedProcess(args, 0, "", "")
        name, argv = args[3], args[5:]
        code = self.fail.get(name, 0)
        if code:
            return subprocess.CompletedProcess(args, code, "", "")
        out = argv[argv.index("--out") + 1] if "--out" in argv else None
        text = " ".join(argv)
        if "calibrate" in argv:
            arm, seed = argv[argv.index("--arms") + 1], argv[argv.index("--seeds") + 1]
            unit = root / "round1" / f"{seed}-{arm}-e1-a1"
            write(unit / "eval" / "e1" / "summary.json", {"u": float(SENTINELS[0])})
            write(unit / "COMPLETE.json", {"complete": True, "files": {}})
        elif argv[3:4] == ["run-one"]:
            identity = {k: v for k, v in self.regen.items() if k != "e1_adapter_fingerprint"}
            write(root / out / "COMPLETE.json", {"complete": True, "identity": identity, "files": {},
                                                 "checkpoints": {"e1": {"adapter_fingerprint":
                                                                        self.regen["e1_adapter_fingerprint"]}}})
            write(root / out / "eval" / "e1" / "summary.json", {"u": SENTINELS[1]})
        elif argv[3:4] == ["make-job"]:
            write(root / out, {"job": True})
        elif argv[3:4] == ["attributes"]:                   # LN-15e's re-score (Gate B's attributes unit)
            write(root / out / "rows.jsonl", '{"row": "r1", "cosine": "' + SENTINELS[0] + '"}\n')
            write(root / out / "COMPLETE.json", {"complete": True, "files": {}})
        elif "oext_unit.py" in text or "transfer" in argv[2:3]:
            write(root / out / "oext_summary.json", {"o": SENTINELS[3]})
        elif "overrefusal_checks.py" in text:
            write(root / out / "overrefusal_checks.json", {"kind": "stage1 over-refusal checks",
                                                           "truncation_check": {"units": 11, "pass": True},
                                                           "flags": SENTINELS[2]})
        elif "eval_adapter.py" in text and argv[2] == "run":
            seed = argv[argv.index("--seed") + 1]
            for label in argv[argv.index("--evaluations") + 1].split(","):    # one unit per evaluation (B10)
                unit = root / argv[argv.index("--eval-root") + 1] / f"{seed}-{label}"
                write(unit / "job.json", {"kind": "stage1-eval-adapter"})
                write(unit / "COMPLETE.json", {"complete": True, "files": {}})
                write(unit / "eval" / "e1" / "summary.json", {"u": SENTINELS[0]})
            write(root / argv[argv.index("--regen-out") + 1] / "run" / "COMPLETE.json", {"complete": True})
        elif "eval_adapter.py" in text and argv[2] == "regenerate":
            write(root / out / "run" / "states" / "e1" / "adapter.safetensors", "w")
            write(root / out / "run" / "COMPLETE.json", {"complete": True})
        elif "eval_adapter.py" in text and argv[2] == "evaluate":
            write(root / out / "job.json", {"kind": "stage1-eval-adapter"})
            write(root / out / "COMPLETE.json", {"complete": True, "files": {}})
            write(root / out / "eval" / "e1" / "summary.json", {"u": SENTINELS[0]})
        elif "safe_lora.py" in text:
            command = argv[2]
            fname = {"vcheck": "safe_lora_vcheck.json", "check": "safe_lora_check.json",
                     "transform": "safe_lora_record.json"}[command]
            write(root / out / fname, {"kind": command})
            if command == "transform":
                write(root / out / "adapter.safetensors", "w2")
            write(root / out / "safe_lora_timing.json", {"seconds": {"total": 12.5 if command == "transform" else 3.0}})
        elif "lean_eval_job.py" in text:
            write(root / out / "c0_record.json", {"o": SENTINELS[3]})
        else:                                               # the diagnostics scripts
            write(root / out / "record.json", {"value": SENTINELS[2]})
            if "make_untuned_answers.py" in text:            # J6 writes the s3_orig pool J5's second pass reads
                write(root / out / "s3_orig.pool.json", {"pool": "s3_orig (synthetic)"})
        return subprocess.CompletedProcess(args, 0, "", "")

    def main(self):
        return self.runner.main(["h-1"])

    def done(self) -> dict:
        return json.loads((self.root / "JOB-DONE.json").read_text())

    def statuses(self) -> list[str]:
        return [r["status"] for r in self.done()["jobs"]]

    def receipts(self) -> list[str]:
        return [a[3] for a in self.ran if a[:2] == ["python3", "process_receipt.py"]]


def regen_pair(r):
    return [job(r, "regenerate", "a0", 1101), job(r, "o_only", "a0", 1101, regen_source=0)]


# ===== Commands (brief §7 "Commands") ==================================================================================

def all_hosts(r):
    """Every job kind, grouped by engine (one engine per pod): (engine, jobs)."""
    r1, a1 = edit_ref("R1"), edit_ref("A1")
    x = [job(r, "w1_18"), job(r, "regenerate", "a0", 1101), job(r, "o_only", "a0", 1101, regen_source=1),
         job(r, "o_only", "theta0"), job(r, "transfer_report", "theta0", branch="128"),
         job(r, "untuned_answers"), job(r, "rep_pass"), job(r, "l1_scan"), job(r, "classifier"),
         job(r, "arm", "A1", 1102, edit=a1, recipe="S"), job(r, "a0_arm", "a0", 1104, recipe="S"),
         job(r, "ref_train", "G", 1102, recipe="G"),
         job(r, "b10_certify", "a0", 1101, points=["certify", "scale:0"], recipe="B"),
         job(r, "ref_eval", "a0", 1104, points=["scale:0.9", "prefix"], recipe="B"),
         job(r, "safe_lora", "a0", 1104, points=["default"], recipe="B"),
         job(r, "c0", "R", 1101, edit=r1, recipe="S"),                      # round 3b: engine X (addendum §26)
         job(r, "retrain", "a0", 1102, recipe="S"),                         # LN-15e (round 3b)
         job(r, "a1_rescore", "a0", 1102, recipe="S", regen_source=16)]
    y = [job(r, "cert_c1", "R", 1101, engine="Y", edit=r1, recipe="S"),
         job(r, "cert_c2", "bqi", 1101, engine="Y", recipe="bqi"),
         job(r, "cert_c3", engine="Y", recipe="S"),
         job(r, "ref_train", "bqi", 1102, engine="Y", recipe="bqi")]
    return x, y


def dry_run(kit, tmp_path, jobs, engine, monkeypatch, branch="full", **pod_options):
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: jobs(r), engine=engine, branch=branch, **pod_options)
    before = sorted(str(p.relative_to(pod.root)) for p in pod.root.rglob("*"))
    done = REAL_RUN([PY, "-B", str(kit.root / "setup" / "job_runner_stage1.py"), "h-1", "--dry-run"],
                          cwd=pod.root, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin",
                                                                              "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0, done.stderr[-800:]
    assert sorted(str(p.relative_to(pod.root)) for p in pod.root.rglob("*")) == before    # --dry-run writes nothing
    return pod, json.loads(done.stdout)


def test_the_dry_run_prints_exactly_the_brief_commands_and_writes_nothing(kit, tmp_path, monkeypatch):
    pod, out = dry_run(kit, tmp_path, lambda r: all_hosts(r)[0], "X", monkeypatch)
    cmds = {j["index"]: j["commands"] for j in out["jobs"]}
    a1 = edit_ref("A1")["sha256"]
    py = ["venv/bin/python"]
    o = ["--oext-bank", "inputs/oext_bank/oext_bank.json", "--oext-record", "inputs/oext_record/oext_record.json",
         "--w1-18-record", "inputs/w1_18_record/w1.json"]
    sealed = json.loads((pod.root / "sealed-files.json").read_text())["files"]

    def ps(rel):
        return f"{rel}:{sealed[rel]}"
    assert cmds[0] == [["job-0-w1-18", [*py, "scripts/stage1/limits/overrefusal_checks.py", "--out", "job-0/w1-18",
                                        "--data-root", "data", "--device", "cuda", "--guard-batch-size", "8"]]]
    assert cmds[1] == [["job-1-make-job", [*ENGINE, "make-job", "run-one", "--prepared", P, "--recipe", S, "--split",
                                           "dev", "--arm", "a0", "--seed", "1101", "--role", "development", "--target",
                                           "e1", "--pin-code", "--out", "jobs/regenerate-1101-a0-regen-a1.json"]],
                       ["job-1-run-one", [*ENGINE, "run-one", "--job", "jobs/regenerate-1101-a0-regen-a1.json",
                                          "--prepared", P, "--recipe", S, "--out", "round1/1101-a0-regen-a1",
                                          "--registry", "round1/registry.jsonl"]]]
    assert cmds[2] == [["job-2-oext", [*py, "scripts/stage1_s1/oext_unit.py", "run", "--run", "round1/1101-a0-regen-a1",
                                       "--checkpoint", "e1", "--prepared", P, "--recipe", S, *o, "--out", "job-2/oext"]]]
    assert cmds[3] == [["job-3-oext", [*py, "scripts/stage1_s1/oext_unit.py", "run", "--untuned", "--prepared", P,
                                       "--recipe", S, *o, "--out", "job-3/oext"]]]
    assert cmds[4] == [["job-4-transfer", [*py, "scripts/stage1_s1/oext_unit.py", "transfer", "--untuned", "--prepared",
                                           P, "--recipe", REC, *o, "--out", "job-4/transfer"]]]
    lists = ["--list", f"s3={ps(INPUT_FILES['list:s3'])}", "--list", f"s4={ps(INPUT_FILES['list:s4'])}",
             "--list", f"sd600={ps(INPUT_FILES['list:sd600'])}", "--loss", f"s1={ps(INPUT_FILES['loss:s1'])}",
             "--loss", f"s3_safe={ps(INPUT_FILES['loss:s3_safe'])}"]
    assert cmds[5] == [["job-5-untuned", [*py, "scripts/stage1/make_untuned_answers.py", "--recipe", REC, "--recipe-s",
                                          S, *lists, "--out", "job-5/untuned"]]]
    anchors = INPUT_FILES["anchor_bank"]
    pools = [a for n in ("plant", "decoy", "s3_safe") for a in ("--pool", ps(INPUT_FILES[f"pool:{n}"]))]
    d2 = ["--pool-pins", ps(INPUT_FILES["d2_pool_pins"]), "--req8-record", ps(INPUT_FILES["req8_record"])]
    rep = "scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py"          # J5 through D-2 (addendum §19 point 3)
    assert cmds[6] == [["job-6-representation", [*py, rep, "--prepared", P, "--recipe", S, "--anchors", anchors,
                                                 *pools, "--out", "job-6/representation", *d2]],      # recipe S (pod a-1)
                       ["job-6-representation-s3-orig", [*py, rep, "--prepared", P, "--recipe", S, "--anchors",
                                                         anchors, "--pool", "@pathsha:job-5/untuned/s3_orig.pool.json",
                                                         "--pools-only", "--out", "job-6/representation-s3-orig", *d2]]]
    assert cmds[7] == [["job-7-l1-scan", [*py, "scripts/stage1/score_l1_larf.py", "scan", "--prepared", P, "--recipe",
                                          REC, "--anchors", anchors, "--out", "job-7/l1-scan"]]]
    assert cmds[8] == [["job-8-classifier", [*py, "scripts/stage1_s1/d2_pool_pins/d2_score_classifier.py", "--prepared",
                                             P, "--recipe", S, "--anchors", anchors, *pools[:4], "--out",
                                             "job-8/classifier", *d2]]]                    # --pool PATH:SHA256 (§21)
    assert cmds[9] == [["job-9-calibrate", [*ENGINE, "calibrate", "--prepared", P, "--recipe", S, "--arms",
                                            f"edit-{a1}", "--edit", f"edits/{a1}.edit.json", "--seeds", "1102",
                                            "--checkpoints", "e1", "--out-root", "round1"]],
                       ["job-9-oext", [*py, "scripts/stage1_s1/oext_unit.py", "run", "--run", "@unit:9", "--checkpoint",
                                       "e1", "--prepared", P, "--recipe", S, *o, "--out", "job-9/oext"]]]
    assert cmds[10][0] == ["job-10-calibrate", [*ENGINE, "calibrate", "--prepared", P, "--recipe", S, "--arms", "a0",
                                                "--seeds", "1104", "--checkpoints", "e1", "--out-root", "round1"]]
    assert cmds[11][0][1][cmds[11][0][1].index("--recipe") + 1] == G
    ga = "inputs/gate_a_complete-1101/COMPLETE.json"
    assert cmds[12] == [["job-12-b10-run", [*py, "scripts/stage1_s1/eval_adapter.py", "run", "--prepared", P, "--recipe",
                                            REC, "--seed", "1101", "--reference", ga, "--regen-out", "job-12/regen",
                                            "--eval-root", "job-12/evals", "--evaluations", "certify,scale:0",
                                            "--gate-reference-eval", "inputs/gate_a_eval-1101", *o]]]
    cert = INPUT_FILES["certification_report"]
    g4 = "inputs/gate_a_complete-1104/COMPLETE.json"
    assert cmds[13] == [["job-13-b10-run", [*py, "scripts/stage1_s1/eval_adapter.py", "run", "--prepared", P, "--recipe",
                                            REC, "--seed", "1104", "--reference", g4, "--regen-out", "job-13/regen",
                                            "--eval-root", "job-13/evals", "--evaluations", "scale:0.9,prefix",
                                            "--prefix-file", INPUT_FILES["prefix_file"], "--certification-report", cert,
                                            "--certification-report-sha256", sealed[cert], *o]]]
    st, models = "job-14/regen/run/states/e1", ["--seed", "1104", "--aligned", "@snapshot:policy", "--base",
                                                  "@snapshot:base"]
    assert [c[0] for c in cmds[14]] == ["job-14-b10-regenerate", "job-14-vcheck", "job-14-check",
                                        "job-14-transform-default", "job-14-evaluate-default"]    # V/V' first
    assert cmds[14][1][1] == [*py, "scripts/stage1_s1/safe_lora.py", "vcheck", "--adapter", st, *models,
                              "--out", "job-14/vcheck"]
    assert cmds[14][3][1] == [*py, "scripts/stage1_s1/safe_lora.py", "transform", "--point", "default", "--adapter", st,
                              *models, "--out", "job-14/transform-default"]
    tf = "job-14/transform-default"
    assert cmds[14][4][1] == [*py, "scripts/stage1_s1/eval_adapter.py", "evaluate", "--prepared", P, "--recipe", REC,
                              "--source-run", "job-14/regen/run", "--reference", g4, "--out", "job-14/eval-default",
                              "--mode", "external", "--external", "safe_lora", "--adapter-file",
                              f"{tf}/adapter.safetensors", "--adapter-sha256", f"@sha256:{tf}/adapter.safetensors",
                              "--adapter-record", f"{tf}/safe_lora_record.json", "--adapter-record-sha256",
                              f"@sha256:{tf}/safe_lora_record.json", "--certification-report", cert,
                              "--certification-report-sha256", sealed[cert], *o]
    assert cmds[15][1][1] == ["venv/bin/python", "scripts/stage1_s1/lean_eval_job.py", "run", "--job",
                              "jobs/c0-1101-R-c0-a1.json", "--prepared", P, "--recipe", S, "--out", "job-15/c0",
                              "--registry", "job-15/c0-registry.jsonl", "--expect-adapter-fingerprint",
                              "@fingerprint:source_complete:R:1101", *o]       # c0 on engine X (round 3b, §26)
    assert "--bank" not in cmds[15][0][1]                    # c0's job is train only (evaluate_bank null)
    # LN-15e (round 3b): Gate B's retrain into rescore/ with its own registry, then the attributes step on its q and
    # e1 states with the 8 unit groups and the packed anchor bank (no Gate C script)
    assert cmds[16] == [["job-16-make-job", [*ENGINE, "make-job", "run-one", "--prepared", P, "--recipe", S, "--split",
                                             "dev", "--arm", "a0", "--seed", "1102", "--role", "development",
                                             "--target", "e1", "--pin-code", "--out",
                                             "jobs/retrain-1102-a0-retrain-a1.json"]],
                        ["job-16-run-one", [*ENGINE, "run-one", "--job", "jobs/retrain-1102-a0-retrain-a1.json",
                                            "--prepared", P, "--recipe", S, "--out", "rescore/1102-a0-retrain-a1",
                                            "--registry", "rescore/registry.jsonl"]]]
    assert cmds[17] == [["job-17-make-job", [*ENGINE, "make-job", "attributes", "--prepared", P, "--recipe", S,
                                             "--split", "dev", "--seed", "1102", "--role", "development",
                                             "--a0-state", "q=rescore/1102-a0-retrain-a1", "--a0-state",
                                             "e1=rescore/1102-a0-retrain-a1", "--groups", ",".join(GROUPS),
                                             "--anchors", "inputs/anchor_bank/anchor_bank.json", "--pin-code",
                                             "--out", "jobs/a1_rescore-1102-a1.json"]],
                        ["job-17-attributes", [*ENGINE, "attributes", "--job", "jobs/a1_rescore-1102-a1.json",
                                               "--prepared", P, "--recipe", S, "--out", "rescore/1102-attributes-a1"]]]
    assert out["engine"] == "X" and all(j["engine"] == "X" for j in out["jobs"])


def test_the_engine_y_pod_commands(kit, tmp_path, monkeypatch):
    pod, out = dry_run(kit, tmp_path, lambda r: all_hosts(r)[1], "Y", monkeypatch)
    cmds = {j["index"]: j["commands"] for j in out["jobs"]}
    r1 = edit_ref("R1")["sha256"]
    sealed = json.loads((pod.root / "sealed-files.json").read_text())["files"]
    assert cmds[0][0][1] == [*ENGINE, "make-job", "run-one", "--prepared", P, "--recipe", S, "--split", "dev", "--edit",
                             f"edits/{r1}.edit.json", "--seed", "1101", "--role", "development", "--target", "e1",
                             "--bank", "dev", "--replicate-of", "@json:cert_spec:replicate_of", "--pin-code", "--out",
                             "jobs/cert_c1-1101-R-c1-a1.json"]
    assert cmds[0][1][1][-4:] == ["--out", "cert/1101-R-c1-a1", "--registry", "cert/registry-cert_c1.jsonl"]
    assert cmds[1][0][1][cmds[1][0][1].index("--recipe") + 1] == BQI and "--bank" not in cmds[1][0][1]   # train only
    sub = INPUT_FILES["c3_subsample"]
    c3 = cmds[2][0][1]
    assert c3[c3.index("--bank") + 1] == f"subsample-{sealed[sub]}" and c3[c3.index("--bank-file") + 1] == sub
    assert [j["kind"] for j in out["jobs"]] == ["cert_c1", "cert_c2", "cert_c3", "ref_train"]   # no c0 (§26)


PARSE = r'''
import argparse, importlib, json, sys
tree, target = sys.argv[1], sys.argv[2]
sys.path.insert(0, tree)
argvs = json.loads(sys.stdin.read())
class Got(Exception):
    pass
original = argparse.ArgumentParser.parse_args
def patched(self, args=None, namespace=None):
    raise Got(vars(original(self, args, namespace)))
argparse.ArgumentParser.parse_args = patched
if target == "engine":
    from experiments.safety_selection.__main__ import _parser
    call = lambda a: _parser().parse_args(a)
else:
    module = importlib.import_module(target)
    call = lambda a: module.main(a)
out = []
for a in argvs:
    try:
        call(a)
        out.append({"ok": False, "why": "returned without parsing"})
    except Got as g:
        out.append({"ok": True, "ns": {k: v if isinstance(v, (str, int, float, bool, type(None))) else str(v)
                                        for k, v in g.args[0].items()}})
    except SystemExit as e:
        out.append({"ok": False, "why": f"exit {e.code}"})
print(json.dumps(out))
'''


def parse_with(tree: Path, target: str, argvs: list[list[str]]) -> list[dict]:
    """Each argv parsed by the target's own argparse parser (engine: experiments.safety_selection's _parser; else the
    module's main, stopped right after its parse_args), in a fresh interpreter in that tree."""
    done = REAL_RUN([PY, "-B", "-c", PARSE, str(tree), target], input=json.dumps(argvs), cwd=tree,
                          capture_output=True, text=True, timeout=300,
                          env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1"})
    assert done.returncode == 0, done.stderr[-800:]
    return json.loads(done.stdout.strip().splitlines()[-1])


SCRIPT_MODULE = {"scripts/stage1/limits/overrefusal_checks.py": (WS_B15, "scripts.stage1.limits.overrefusal_checks"),
                 "scripts/stage1/make_untuned_answers.py": (WS_B15, "scripts.stage1.make_untuned_answers"),
                 "scripts/stage1/representation_pass.py": (WS_B15, "scripts.stage1.representation_pass"),
                 "scripts/stage1/score_l1_larf.py": (WS_B15, "scripts.stage1.score_l1_larf"),
                 "scripts/stage1/score_classifier.py": (WS_B15, "scripts.stage1.score_classifier"),
                 "scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py":
                     (WS_B15, "scripts.stage1_s1.d2_pool_pins.d2_representation_pass"),
                 "scripts/stage1_s1/d2_pool_pins/d2_score_classifier.py":
                     (WS_B15, "scripts.stage1_s1.d2_pool_pins.d2_score_classifier"),
                 "scripts/stage1_s1/eval_adapter.py": (WS_S1, "scripts.stage1_s1.eval_adapter"),
                 "scripts/stage1_s1/safe_lora.py": (WS_S1, "scripts.stage1_s1.safe_lora"),
                 "scripts/stage1_s1/lean_eval_job.py": (WS_S1, "scripts.stage1_s1.lean_eval_job"),
                 "scripts/stage1_s1/oext_unit.py": (WS_S1, "scripts.stage1_s1.oext_unit")}     # round 3c: the runner


def test_every_jobs_argv_parses_with_its_targets_own_parser(kit, tmp_path, monkeypatch):
    """Every engine step by engine X's (or, on the Y pod, engine Y's) _parser; every stage-1 script step by that
    script's own argparse parser (W1 scripts, D-2 and the S1 package in this tree's scripts/); every O-ext
    unit step by the kit's contract parser and (round 3c) by the committed runner's own parser
    (scripts/stage1_s1/oext_unit.py). Placeholders stand in for run-time values."""
    groups = {}
    for engine, tree in (("X", WS_B15), ("Y", WS_Y)):
        sub = tmp_path / engine
        sub.mkdir()
        _, out = dry_run(kit, sub, lambda r, e=engine: all_hosts(r)[0 if e == "X" else 1], engine, monkeypatch)
        for j in out["jobs"]:
            for name, argv in j["commands"]:
                argv = [v.replace("@unit:9", "round1/x").replace("@", "AT-") for v in argv]
                if argv[:3] == ENGINE:
                    groups.setdefault((tree, "engine"), []).append(argv[3:])
                elif argv[1] == "scripts/stage1_s1/oext_unit.py":
                    groups.setdefault(("contract", None), []).append(argv[2:])
                    groups.setdefault(SCRIPT_MODULE[argv[1]], []).append(argv[2:])     # round 3c: the real runner
                else:
                    groups.setdefault(SCRIPT_MODULE[argv[1]], []).append(argv[2:])
        for name in MODULES:
            sys.modules.pop(name, None)
    runner = kit("setup/job_runner_stage1.py")
    seen = set()
    for (tree, target), argvs in groups.items():
        if tree == "contract":
            for a in argvs:
                runner.oext_unit_contract().parse_args(a)
            seen.add("contract")
            continue
        results = parse_with(tree, target, argvs)
        assert all(r["ok"] for r in results), [(a, r) for a, r in zip(argvs, results) if not r["ok"]][:2]
        seen.add(target if target != "engine" else f"engine-{'Y' if tree == WS_Y else 'X'}")
        if target == "scripts.stage1.limits.overrefusal_checks":
            assert results[0]["ns"]["device"] == "cuda" and results[0]["ns"]["guard_batch_size"] == 8
        if target == "engine":
            for a, r in zip(argvs, results):
                if a[:2] == ["make-job", "run-one"] and "--bank" not in a:
                    assert r["ns"]["bank"] is None and r["ns"]["pin_code"] is True     # train only, code pinned
    assert seen == {"engine-X", "engine-Y", "contract", *[m for _, m in SCRIPT_MODULE.values()]} - {
        "scripts.stage1.representation_pass", "scripts.stage1.score_classifier"}    # D-2's routes (W1: fallback only)


# (C, 25 Oct: pod a-1's J5 refused "the recipe hashes to 9e9bde6f..., the settings pin ceffe0ef...") every step's
# recipe arguments against the pins of the committed settings of the script that step runs (read from this tree)
def _settings(rel: str) -> dict:
    return json.loads((REPO / rel).read_text())


def recipe_pins() -> dict:
    """script -> {flag: the config SHA-256 values its committed settings accept for that flag}."""
    rep = {_settings("scripts/stage1/settings/representation_pass.json")["pins"]["recipe_sha256"]}
    cls = {_settings("scripts/stage1/settings/score_classifier.json")["pins"]["recipe_sha256"]}
    j6 = _settings("scripts/stage1/settings/make_untuned_answers.json")["pins"]
    return {"scripts/stage1/representation_pass.py": {"--recipe": rep},
            "scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py": {"--recipe": rep},   # forwards it to REQ-3
            "scripts/stage1/score_classifier.py": {"--recipe": cls},
            "scripts/stage1_s1/d2_pool_pins/d2_score_classifier.py": {"--recipe": cls},
            "scripts/stage1/score_l1_larf.py":
                {"--recipe": {_settings("scripts/stage1/settings/score_l1_larf.json")["pins"]["rec_recipe_sha256"]}},
            "scripts/stage1/make_untuned_answers.py": {"--recipe": {j6["rec_recipe_sha256"]},
                                                        "--recipe-s": {j6["recipe_s_sha256"]}},
            "scripts/stage1_s1/eval_adapter.py":
                {"--recipe": {_settings("scripts/stage1_s1/settings/eval_adapter.json")["recipe"]["config_sha256"]}},
            "scripts/stage1_s1/lean_eval_job.py":
                {"--recipe": set(_settings("scripts/stage1_s1/settings/lean_eval_job.json")["job"]["allowed_recipes"]
                                 .values())},
            "scripts/stage1_s1/oext_unit.py":
                {"--recipe": set(_settings("scripts/stage1_s1/settings/oext_unit.json")["recipes"]["allowed"].values())}}


NO_RECIPE_SCRIPTS = ("scripts/stage1/limits/overrefusal_checks.py", "scripts/stage1_s1/safe_lora.py")   # take none


def engine_configs(tree: Path, paths: list[str]) -> dict:
    """path -> config_sha256(load_recipe(tree/path)) by that tree's own engine code (a fresh interpreter)."""
    code = ("import json,sys;sys.path.insert(0,sys.argv[1]);from experiments.safety_selection.config import "
            "load_recipe,config_sha256;print(json.dumps({p: config_sha256(load_recipe(sys.argv[1] + '/' + p)) "
            "for p in sys.argv[2:]}))")
    done = REAL_RUN([PY, "-B", "-c", code, str(tree), *paths], cwd=tree, capture_output=True, text=True, timeout=300,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0, done.stderr[-800:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_every_steps_recipe_is_the_one_its_target_scripts_settings_pin(kit, tmp_path, monkeypatch):
    """For every job kind (both engines' pods), every --recipe/--recipe-s the kit passes names a committed recipe file
    whose config SHA-256 (engine X's code for REC, S and G; engine Y's code in Y's tree for B+Qi's, which is there
    only) is one the target script's committed settings accept; an engine step takes the job's own recipe. This is the
    check pod a-1's J5 failed (REC passed, recipe S pinned). One gap is known and stated: B+Qi's O-ext step on Y (the
    unit's own recipe) is not yet in oext_unit.json's recipes (its rule: B+Qi joins at the engine Y re-pin)."""
    r = kit("stage1_rules.py")
    configs = {**engine_configs(REPO, [REC, S, G]), **engine_configs(WS_Y, [BQI])}
    assert configs[S] == _settings("scripts/stage1/settings/representation_pass.json")["pins"]["recipe_sha256"]
    pins, steps, seen = recipe_pins(), [], set()
    for engine in ("X", "Y"):
        sub = tmp_path / engine
        sub.mkdir()
        _, out = dry_run(kit, sub, lambda r_, e=engine: all_hosts(r_)[0 if e == "X" else 1], engine, monkeypatch)
        jobs = (all_hosts(r)[0 if engine == "X" else 1])
        for j in out["jobs"]:
            for name, argv in j["commands"]:
                steps.append((engine, j["kind"], jobs[j["index"]].get("recipe"), name, argv))
        for m in MODULES:
            sys.modules.pop(m, None)
    bad = []
    for engine, kind, recipe, name, argv in steps:
        script = "engine" if argv[:3] == ENGINE else argv[1]
        flags = {f: argv[argv.index(f) + 1] for f in ("--recipe", "--recipe-s") if f in argv}
        if script == "engine":
            assert flags == {"--recipe": r.RECIPE_NAMES[recipe or "S"]}, (kind, name)     # the job's own recipe
            continue
        if script in NO_RECIPE_SCRIPTS:
            assert not flags, (kind, name)
            continue
        assert set(flags) == set(pins[script]), (kind, name, script)    # a script without a pin entry fails here
        seen.add(script)
        for flag, path in flags.items():
            if configs[path] not in pins[script][flag]:
                bad.append((engine, kind, name, script, flag, path))
    assert bad == [("Y", "ref_train", "job-3-oext", "scripts/stage1_s1/oext_unit.py", "--recipe", BQI)]
    assert seen == set(pins) - {"scripts/stage1/representation_pass.py", "scripts/stage1/score_classifier.py"}
    rep = [argv for _, kind, _, _, argv in steps if kind == "rep_pass"]
    assert len(rep) == 2 and all(a[a.index("--recipe") + 1] == S for a in rep)          # J5: recipe S, both passes


def test_engine_x_refuses_y_only_arguments_so_c3_runs_on_y(kit, tmp_path, monkeypatch):
    _, out = dry_run(kit, tmp_path, lambda r: [job(r, "cert_c3", engine="Y", recipe="S")], "Y", monkeypatch)
    make = [v.replace("@", "AT-") for v in out["jobs"][0]["commands"][0][1][3:]]
    assert parse_with(WS_B15, "engine", [make])[0]["ok"] is False            # --bank-file is engine Y's
    assert parse_with(WS_Y, "engine", [make])[0]["ok"] is True


def test_a_missing_input_makes_the_job_unrunnable_and_k12_refuses(kit, tmp_path, monkeypatch):
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "classifier"), job(r, "safe_lora", "a0", 1104,
                                                                               points=["k12"], recipe="B")],
              omit=("anchor_bank",))
    with pytest.raises(pod.runner.Unrunnable, match="anchor_bank"):
        pod.runner.job_commands(pod.plan, "h-1", 0, pod.root, {})
    with pytest.raises(pod.runner.Unrunnable, match="K = 12"):
        pod.runner.job_commands(pod.plan, "h-1", 1, pod.root, {})


# ===== The per-job gate, records and ledger =============================================================================

def test_jobs_run_in_order_with_engine_records_and_cost_ledgers(kit, tmp_path, monkeypatch):
    a1 = edit_ref("A1")
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [*regen_pair(r), job(r, "arm", "A1", 1102, edit=a1, recipe="S"),
                                                     job(r, "l1_scan")])
    pod.remaining([20 * H])
    assert pod.main() == 0
    done = pod.done()
    assert pod.statuses() == ["complete"] * 4 and done["ok"] is True and done["stopped"] is None
    assert pod.receipts() == ["job-0-make-job", "job-0-run-one", "job-1-oext", "job-2-calibrate", "job-2-oext",
                              "job-3-l1-scan"]
    for rec in done["jobs"]:
        assert rec["engine"] == "X" and rec["engine_sha256"] == X
        ledger = json.loads((pod.root / f"job-{rec['index']}" / "cost-ledger.json").read_text())
        assert set(ledger["stages_s"]) == {"setup", "training", "greedy_generation", "sampled_generation", "judging",
                                           "scoring", "pod_overhead", "transform"}
        assert rec["outputs"][f"job-{rec['index']}/cost-ledger.json"] == sha(pod.root / f"job-{rec['index']}" /
                                                                             "cost-ledger.json")
        assert ledger["slot_s"] >= 0 and ledger["engine_sha256"] == X
    assert done["jobs"][2]["unit"] == f"round1/1102-edit-{a1['sha256']}-e1-a1"
    oext = [a for a in pod.ran if "job-2-oext" in a][0]
    assert oext[oext.index("--run") + 1] == done["jobs"][2]["unit"]          # the O-ext pass on the new unit's e1
    assert done["jobs"][3]["complete_sha256"] is None and done["jobs"][3]["outputs"]["job-3/l1-scan/record.json"]
    assert sorted(p.name for p in (pod.root / "job-done").iterdir()) == [f"JOB-{i}.json" for i in range(4)]


def test_a_job_that_does_not_fit_and_every_later_one_are_deferred_in_order(kit, tmp_path, monkeypatch):
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "l1_scan"), job(r, "classifier"), job(r, "rep_pass")])
    first, second = (j["start_requirement_s"] for j in pod.plan["hosts"]["h-1"]["jobs"][:2])
    pod.remaining([first + 1, second - 1, 10 * H])
    assert pod.main() == 0
    assert pod.statuses() == ["complete", "deferred", "deferred"] and pod.receipts() == ["job-0-l1-scan"]
    deferral = json.loads((pod.root / "deferral.json").read_text())
    assert deferral["first_deferred"] == 1 and deferral["deferred"] == [1, 2]


@pytest.mark.parametrize("beat", ["missing", "unreadable"])
def test_a_missing_or_unreadable_heartbeat_stops_the_host(kit, tmp_path, monkeypatch, beat):
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "l1_scan"), job(r, "classifier")])
    if beat == "unreadable":
        (tmp_path / "heartbeat.json").write_text("{not json")
    assert pod.main() == 1
    assert pod.done()["stopped"] == "heartbeat_unreadable" and pod.statuses() == ["not_started"] * 2
    assert pod.receipts() == []


def test_a_crash_stops_the_host_and_later_jobs_do_not_start(kit, tmp_path, monkeypatch):
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "l1_scan"), job(r, "classifier"), job(r, "rep_pass")])
    pod.remaining([20 * H])
    pod.fail = {"job-1-classifier": 1}
    assert pod.main() == 1
    assert pod.statuses() == ["complete", "crashed", "not_started"] and pod.done()["stopped"] == "crashed"
    assert pod.receipts() == ["job-0-l1-scan", "job-1-classifier"]


def test_a_pod_requirement_uses_the_larger_of_the_plan_and_the_projections_o500(kit, tmp_path, monkeypatch):
    a1 = edit_ref("A1")
    proj = {"e1_upper_s": E1, "training_s": T, "overhead_s": 1000, "margin_s": 900, "o500_s": 3000.0}
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "arm", "A1", 1102, edit=a1, recipe="S")], projection=proj)
    plan_req = E1 + T * 33 / 38 + 1900 + 1517 + 1800                     # by hand: the plan's start requirement
    pod_req = E1 + T * 33 / 38 + 1900 + 3000 + 1800                      # the projection's larger O500
    assert pod.plan["hosts"]["h-1"]["jobs"][0]["start_requirement_s"] == pytest.approx(plan_req)
    pod.remaining([pod_req - 1])
    assert pod.main() == 0 and pod.statuses() == ["deferred"]
    assert json.loads((pod.root / "deferral.json").read_text())["requirement_s"] == pytest.approx(pod_req)


def rescore_pod(r):
    return [job(r, "retrain", "a0", 1102, recipe="S"), job(r, "a1_rescore", "a0", 1102, recipe="S", regen_source=0),
            job(r, "retrain", "a0", 1103, recipe="S"), job(r, "a1_rescore", "a0", 1103, recipe="S", regen_source=2)]


def test_ln_15e_retrains_and_re_scores_run_as_linked_pairs_and_record_their_units(kit, tmp_path, monkeypatch):
    """Round 3b item 4 (addendum §25 point 1; REV4 LN-15e): each a0 retrain at 1102/1103 runs into rescore/ with its
    own registry, then the attributes step on THAT unit's q and e1 states; each job records its verified unit and its
    ledger puts the attributes step under scoring. By hand: the re-score's start requirement 1.5 x 3.04 h + 30 min =
    18,216 s; its retrain's max(4,033.67, 540 + 18,216) = 18,756 s."""
    pod = Pod(kit, tmp_path, monkeypatch, rescore_pod)
    need = pod.rules.requirements(pod.plan["hosts"]["h-1"]["jobs"])
    assert need == pytest.approx([18756.0, 18216.0, 18756.0, 18216.0])
    pod.remaining([20 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete"] * 4
    done = pod.done()["jobs"]
    assert [d["unit"] for d in done] == ["rescore/1102-a0-retrain-a1", "rescore/1102-attributes-a1",
                                         "rescore/1103-a0-retrain-a1", "rescore/1103-attributes-a1"]
    make = [a for a in pod.ran if "job-3-make-job" in a][0]
    assert make[make.index("--a0-state") + 1] == "q=rescore/1103-a0-retrain-a1" and \
        "e1=rescore/1103-a0-retrain-a1" in make
    run = [a for a in pod.ran if "job-2-run-one" in a][0]
    assert run[-2:] == ["--registry", "rescore/registry.jsonl"]          # never round1/registry.jsonl (J2's)
    ledger = json.loads((pod.root / "job-1" / "cost-ledger.json").read_text())
    assert [st["name"] for st in ledger["steps"]] == ["job-1-make-job", "job-1-attributes"] and \
        ledger["job_id"] == "J21"
    assert all(d["verified"]["exit"] == 0 and d["complete_sha256"] for d in done)
    printed = json.dumps(pod.done())
    assert not any(v in printed for v in SENTINELS)                    # no row value is read or recorded


def test_a_re_score_without_its_groups_or_after_a_crashed_retrain_never_runs(kit, tmp_path, monkeypatch):
    """Round 3b: a re-score whose plan.json carries no 8 unit groups is a crash before any step (named); a crashed
    retrain stops the host, so its re-score is not_started; a pod short of the pair's requirement defers both."""
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [{**j, "groups": j.get("groups", [])[:7]} for j in rescore_pod(r)])
    pod.remaining([20 * H])
    assert pod.main() == 1 and pod.statuses()[:2] == ["complete", "crashed"]
    assert "8 unit groups" in pod.done()["jobs"][1]["why"] and "job-1-make-job" not in pod.receipts()
    (tmp_path / "b").mkdir()
    pod = Pod(kit, tmp_path / "b", monkeypatch, rescore_pod)
    pod.remaining([20 * H])
    pod.fail = {"job-0-run-one": 1}
    assert pod.main() == 1 and pod.statuses() == ["crashed", "not_started", "not_started", "not_started"]
    (tmp_path / "c").mkdir()
    pod = Pod(kit, tmp_path / "c", monkeypatch, rescore_pod)
    pod.remaining([18756.0 - 1])
    assert pod.main() == 0 and pod.statuses() == ["deferred"] * 4 and pod.receipts() == []


def test_a_re_score_whose_groups_repeat_one_never_runs(kit, tmp_path, monkeypatch):
    """Fix round (F4): 8 groups with one repeated (7 distinct) are not Gate B's 8 unit groups: the re-score is a
    crash before any of its steps, named, as plan_tool.rescore_groups refuses it at planning."""
    def jobs(r):
        return [{**j, "groups": j["groups"][:7] + j["groups"][6:7]} if j["kind"] == "a1_rescore" else j
                for j in rescore_pod(r)]
    pod = Pod(kit, tmp_path, monkeypatch, jobs)
    assert len(pod.plan["hosts"]["h-1"]["jobs"][1]["groups"]) == 8
    pod.remaining([20 * H])
    assert pod.main() == 1 and pod.statuses()[:2] == ["complete", "crashed"]
    assert "a group is repeated" in pod.done()["jobs"][1]["why"] and "job-1-make-job" not in pod.receipts()


# ===== Edits and inputs (every input checked against its SHA-256 before use) ============================================

@pytest.mark.parametrize("tamper, kind", [("inputs/anchor_bank/anchor_bank.json", "l1_scan"),
                                          ("inputs/reuse_spec/reuse_spec.json", "regenerate"),
                                          ("scripts/stage1/score_l1_larf.py", "l1_scan"),
                                          ("inputs/oext_bank/oext_bank.json", "o_only"),
                                          ("scripts/stage1_s1/oext_eval.py", "o_only"),
                                          ("inputs/gate_a_eval-1101/eval/summary.json", "b10_certify"),
                                          ("inputs/list-s4/s4.json", "untuned_answers"),
                                          ("data/units/u1/COMPLETE.json", "w1_18")])
def test_a_changed_byte_in_any_input_refuses_its_job(kit, tmp_path, monkeypatch, tamper, kind):
    def jobs(r):
        return {"l1_scan": [job(r, "l1_scan")], "regenerate": regen_pair(r)[:1], "o_only": [job(r, "o_only", "theta0")],
                "b10_certify": [job(r, "b10_certify", "a0", 1101, points=["certify"], recipe="B")],
                "untuned_answers": [job(r, "untuned_answers")], "w1_18": [job(r, "w1_18")]}[kind]
    pod = Pod(kit, tmp_path, monkeypatch, jobs)
    h = pod.plan["hosts"]["h-1"]
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    assert pod.runner.sealed_check(h["jobs"][0], doc["files"], pod.root, h, 0, doc) == []
    write(pod.root / tamper, "changed after sealing\n")
    assert tamper in pod.runner.sealed_check(h["jobs"][0], doc["files"], pod.root, h, 0, doc)
    monkeypatch.setattr(pod.runner, "preflight_checks", lambda *a: doc)       # the mid-host check, alone
    pod.remaining([30 * H])
    assert pod.main() == 1
    assert pod.done()["stopped"] == "sealed_file_mismatch" and pod.receipts() == []
    assert pod.done()["jobs"][0]["sealed_mismatch"]


def test_the_start_up_check_refuses_any_changed_sealed_file(kit, tmp_path, monkeypatch):
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "l1_scan")], tamper="inputs/pool-plant/plant.json")
    with pytest.raises(AssertionError, match="sealed file"):
        pod.runner.preflight_checks(pod.plan, "h-1", json.loads((pod.root / "PREFLIGHT-DONE.json").read_text()),
                                    pod.root)


def test_an_edit_file_must_hash_to_its_jobs_sha256_and_arm(kit, tmp_path, monkeypatch):
    a1, r1 = edit_ref("A1"), edit_ref("R1")
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "arm", "A1", 1102, edit=a1, recipe="S")])
    h = pod.plan["hosts"]["h-1"]
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    assert pod.runner.sealed_check(h["jobs"][0], doc["files"], pod.root, h, 0, doc) == []
    other = {**h["jobs"][0], "edit": {**a1, "engine_arm": "edit-" + r1["sha256"]}}   # A1's file under R_1's arm
    assert pod.runner.sealed_check(other, doc["files"], pod.root, h, 0, doc) == [f"edits/{a1['sha256']}.edit.json (its arm)"]
    unsealed = {**h["jobs"][0], "edit": {**a1, "sha256": "9" * 64}}               # not the sealed file
    assert pod.runner.sealed_check(unsealed, doc["files"], pod.root, h, 0, doc)


def test_the_runner_refuses_a_token_a_second_run_and_a_wrong_engine(kit, tmp_path, monkeypatch):
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "l1_scan")])
    pre = json.loads((pod.root / "PREFLIGHT-DONE.json").read_text())
    monkeypatch.setenv("HF_TOKEN", fake_token())
    with pytest.raises(AssertionError, match="token"):
        pod.runner.preflight_checks(pod.plan, "h-1", pre, pod.root)
    monkeypatch.delenv("HF_TOKEN")
    monkeypatch.setattr(pod.runner, "_engine_identity", lambda: Y)
    with pytest.raises(AssertionError, match="engine code differs"):
        pod.runner.preflight_checks(pod.plan, "h-1", pre, pod.root)
    monkeypatch.setattr(pod.runner, "_engine_identity", lambda: X)
    two = json.loads(json.dumps(pod.plan))
    two["hosts"]["h-1"]["jobs"].append({**two["hosts"]["h-1"]["jobs"][0], "engine": "Y"})
    with pytest.raises(AssertionError, match="two engines"):
        pod.runner.preflight_checks(two, "h-1", pre, pod.root)
    write(pod.root / "JOB-DONE.json", {})
    with pytest.raises(AssertionError, match="already ran"):
        pod.runner.preflight_checks(pod.plan, "h-1", pre, pod.root)


def test_the_w1_18_and_branch_gates_on_the_pod(kit, tmp_path, monkeypatch):
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "o_only", "theta0")], branch=None)
    pre = json.loads((pod.root / "PREFLIGHT-DONE.json").read_text())
    with pytest.raises(AssertionError, match="W1-18's branch record"):
        pod.runner.preflight_checks(pod.plan, "h-1", pre, pod.root)
    pod.plan["records"]["branch"] = {"branch": "128", "source": "w1_18"}
    with pytest.raises(AssertionError, match="another branch"):
        pod.runner.preflight_checks(pod.plan, "h-1", pre, pod.root)
    pod.plan["records"]["branch"]["branch"] = "full"
    pod.runner.preflight_checks(pod.plan, "h-1", pre, pod.root)
    pod.plan["hosts"]["h-1"]["jobs"].insert(0, job(pod.rules, "w1_18"))
    with pytest.raises(AssertionError, match="W1-18 runs alone"):
        pod.runner.preflight_checks(pod.plan, "h-1", pre, pod.root)


# ===== Regeneration (J2, LN-12) ===========================================================================================

def test_a_regeneration_is_accepted_on_every_listed_field_and_its_o_only_pass_runs(kit, tmp_path, monkeypatch):
    pod = Pod(kit, tmp_path, monkeypatch, regen_pair)
    pod.remaining([20 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete", "complete"]
    rec = json.loads((pod.root / "job-0" / "regeneration-adapter-fingerprint.json").read_text())
    assert rec["pass"] is True and set(rec["fields"]) == {"e1_adapter_fingerprint", "training_identity",
                                                          "manifest_sha256", "data_config_sha256"}
    assert pod.done()["jobs"][0]["acceptance"] is True
    assert pod.done()["jobs"][0]["outputs"]["job-0/regeneration-adapter-fingerprint.json"]


@pytest.mark.parametrize("field", ["e1_adapter_fingerprint", "training_identity", "manifest_sha256",
                                   "data_config_sha256"])
def test_a_regeneration_that_differs_in_one_field_holds_its_o_only_pass_ls_04(kit, tmp_path, monkeypatch, field):
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [*regen_pair(r), job(r, "l1_scan")])
    pod.regen[field] = "9" * 64
    pod.remaining([20 * H])
    assert pod.main() == 0
    done = pod.done()
    assert pod.statuses() == ["complete", "not_started", "complete"]          # later unrelated jobs go on
    assert done["jobs"][0]["acceptance"] is False and done["jobs"][0]["reason"] == "LS-04"
    assert done["jobs"][1]["reason"] == "LS-04" and done["jobs"][1]["held_by"] == 0
    assert "job-1-oext" not in pod.receipts()
    rec = json.loads((pod.root / "job-0" / "regeneration-adapter-fingerprint.json").read_text())
    assert [f for f, v in rec["fields"].items() if not v["equal"]] == [field]


def test_an_accept_field_listed_in_the_spec_is_always_compared(kit, tmp_path, monkeypatch):
    """A field reuse_spec.json adds under accept is compared too (the runner never keeps its own field list)."""
    pod = Pod(kit, tmp_path, monkeypatch, regen_pair, accept_change={"extra_field_sha256": "5" * 64})
    pod.remaining([20 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete", "not_started"]


def test_an_r_regeneration_runs_its_edit_and_matches_its_spec_entry_by_engine_arm(kit, tmp_path, monkeypatch):
    r1 = edit_ref("R1")
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "regenerate", "R", 1101, edit=r1),
                                                     job(r, "o_only", "R", 1101, regen_source=0)])
    pod.remaining([20 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete", "complete"]
    make = [a for a in pod.ran if "job-0-make-job" in a][0]
    assert make[make.index("--edit") + 1] == f"edits/{r1['sha256']}.edit.json" and "--arm" not in make[5:]
    rec = json.loads((pod.root / "job-0" / "regeneration-adapter-fingerprint.json").read_text())
    assert rec["spec_job"] == "regenerate-R_1101"


def test_an_o_only_pass_without_its_regeneration_on_this_pod_does_not_run(kit, tmp_path, monkeypatch):
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "o_only", "a0", 1101, regen_source=0)])
    pod.remaining([20 * H])
    assert pod.main() == 1 and pod.statuses() == ["crashed"] and pod.receipts() == []


def test_record_done_accepts_a_complete_o_only_pass_by_its_outputs(kit, tmp_path, monkeypatch):
    """BUILD-RUNNER defect fix (stage1_rules.UNITLESS_KINDS): an O-only pass writes the O-ext files and no engine
    unit (theta0 has no unit at all), so record-done must accept it complete by its hashed outputs."""
    tool = kit("plan_tool.py")
    r = tool.rules
    jobs = [job(r, "o_only", "theta0")]
    write(kit.root / "plan.json", {"hosts": {"a-1": host_record(r, jobs)}, "deferrals": [], "requeues": []})
    tree = kit.root / "retrieved" / "a-1" / "tree"
    out = write(tree / "job-0" / "oext" / "oext_summary.json", {"o": SENTINELS[3]})
    write(tree / "JOB-DONE.json", {"host": "a-1", "jobs": [
        {"index": 0, "kind": "o_only", "arm": "theta0", "seed": None, "status": "complete", "engine": "X",
         "engine_sha256": X, "outputs": {"job-0/oext/oext_summary.json": sha(out)}}]})
    assert tool.record_done("a-1")["statuses"] == ["complete"]


# ===== Safe LoRA job (J17) =================================================================================================

def safe_pod(kit, tmp_path, monkeypatch, points=("default",)):
    return Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "safe_lora", "a0", 1104, points=list(points), recipe="B")])


def test_the_safe_lora_job_checks_v_against_v_prime_before_the_projection(kit, tmp_path, monkeypatch):
    pod = safe_pod(kit, tmp_path, monkeypatch, points=("default", "conditional"))
    pod.remaining([30 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete"]
    order = pod.receipts()
    assert order == ["job-0-b10-regenerate", "job-0-vcheck", "job-0-check", "job-0-transform-default",
                     "job-0-evaluate-default", "job-0-transform-conditional", "job-0-evaluate-conditional"]
    vcheck = [a for a in pod.ran if "job-0-vcheck" in a][0]
    assert vcheck[vcheck.index("--aligned") + 1] == "/hf/instruct/48d788ec"        # the snapshots from the receipt
    assert vcheck[vcheck.index("--base") + 1] == "/hf/base/a1847dff"
    ev = [a for a in pod.ran if "job-0-evaluate-default" in a][0]
    tf = pod.root / "job-0" / "transform-default"
    assert ev[ev.index("--adapter-sha256") + 1] == sha(tf / "adapter.safetensors")
    assert ev[ev.index("--adapter-record-sha256") + 1] == sha(tf / "safe_lora_record.json")
    ledger = json.loads((pod.root / "job-0" / "cost-ledger.json").read_text())
    assert ledger["stages_s"]["transform"] == 25.0                              # 12.5 s x two points, by hand
    assert pod.done()["jobs"][0]["unit"] == "job-0/eval-conditional"            # the first B10 unit (sorted)


def test_a_missing_v_check_stops_the_job_before_any_projection(kit, tmp_path, monkeypatch):
    pod = safe_pod(kit, tmp_path, monkeypatch)
    real = pod.run

    def no_vcheck(args, **kw):
        if args[:2] == ["python3", "process_receipt.py"] and args[3] == "job-0-vcheck":
            pod.ran.append(list(args))
            return subprocess.CompletedProcess(args, 0, "", "")             # exit 0 but nothing written
        return real(args, **kw)
    monkeypatch.setattr(pod.runner.subprocess, "run", no_vcheck)
    pod.remaining([30 * H])
    assert pod.main() == 1 and pod.statuses() == ["crashed"]
    assert "V/V'" in pod.done()["jobs"][0]["why"]
    assert pod.receipts() == ["job-0-b10-regenerate", "job-0-vcheck"]          # no check, no transform


def test_a_transform_without_its_timing_file_is_a_crash(kit, tmp_path, monkeypatch):
    pod = safe_pod(kit, tmp_path, monkeypatch)
    real = pod.run

    def no_timing(args, **kw):
        out = real(args, **kw)
        if args[:2] == ["python3", "process_receipt.py"] and "transform" in args[3]:
            (pod.root / "job-0" / "transform-default" / "safe_lora_timing.json").unlink()
        return out
    monkeypatch.setattr(pod.runner.subprocess, "run", no_timing)
    pod.remaining([30 * H])
    assert pod.main() == 1 and "timing" in pod.done()["jobs"][0]["why"]


def test_k12_never_runs_even_with_a_recorded_yes(kit, tmp_path, monkeypatch):
    pod = safe_pod(kit, tmp_path, monkeypatch, points=("k12",))
    pod.remaining([30 * H])
    assert pod.main() == 1 and "K = 12" in pod.done()["jobs"][0]["why"] and pod.receipts() == []


def _downloader(kit, monkeypatch, tmp_path, files: dict, revision_dir: str | None = None):
    dl = kit("setup/download_models_stage1.py")
    probes = kit("probes.py")
    snap = tmp_path / "hub" / "snapshots" / (revision_dir or probes.BASE["revision"])
    blobs = tmp_path / "hub" / "blobs"
    blobs.mkdir(parents=True, exist_ok=True)
    snap.mkdir(parents=True)
    pins = []
    for name, data in files.items():
        lfs = name.endswith(".safetensors")
        blob = blobs / (hashlib.sha256(data).hexdigest() if lfs else hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest())
        blob.write_bytes(data)
        (snap / name).symlink_to(blob)
        pins.append({"rfilename": name, "size": len(data),
                     "git_blob_id": hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest(),
                     "lfs_sha256": hashlib.sha256(data).hexdigest() if lfs else None})
    entry = {**probes.BASE, "patterns": list(files), "files": pins}
    calls = []
    monkeypatch.setattr(dl, "snapshot_download", lambda **kw: calls.append(kw) or str(snap))
    return dl, entry, calls, snap


def test_the_base_model_downloads_at_its_commit_and_every_file_is_checked(kit, tmp_path, monkeypatch):
    files = {"config.json": b"{}", "model-00001-of-00002.safetensors": b"weights-1"}
    dl, entry, calls, snap = _downloader(kit, monkeypatch, tmp_path, files)
    models = dl.download([entry], None)
    dl.check_base(entry, models["base"])
    assert calls[0]["revision"] == "a1847dff35000b4271fa70afc5db10fd29fedbdf" and calls[0]["token"] is False
    assert calls[0]["allow_patterns"] == list(files) and calls[0]["endpoint"] == "https://huggingface.co"
    probes = kit("probes.py")
    assert len(probes.BASE_FILES) == 12 and probes.base_entry()["revision"] == probes.BASE["revision"]
    assert [e["role"] for e in probes.stage1_download_plan("olmo2-1b", with_base=True)][-1] == "base"
    assert "base" not in [e["role"] for e in probes.stage1_download_plan("olmo2-1b")]


@pytest.mark.parametrize("change", ["git blob", "lfs sha", "size", "extra file", "folder"])
def test_a_base_file_that_differs_from_its_pin_refuses(kit, tmp_path, monkeypatch, change):
    files = {"config.json": b"{}", "model-00001-of-00002.safetensors": b"weights-1"}
    dl, entry, calls, snap = _downloader(kit, monkeypatch, tmp_path, files,
                                         revision_dir="main" if change == "folder" else None)
    if change == "git blob":
        entry["files"][0]["git_blob_id"] = "0" * 40
    elif change == "lfs sha":
        entry["files"][1]["lfs_sha256"] = "0" * 64
    elif change == "size":
        entry["files"][0]["size"] += 1
    elif change == "extra file":
        entry["files"] = entry["files"][:1]
    models = dl.download([entry], None)
    with pytest.raises(SystemExit):
        dl.check_base(entry, models["base"])


@pytest.mark.parametrize("revision", ["main", "a1847dff", None, "A1847DFF35000B4271FA70AFC5DB10FD29FEDBDF"])
def test_a_download_at_main_or_a_short_revision_refuses_before_any_request(kit, tmp_path, monkeypatch, revision):
    dl = kit("setup/download_models_stage1.py")
    probes = kit("probes.py")
    write(tmp_path / "probe.json", {"plan": [{**probes.base_entry(), "revision": revision}], "weight_pins": []})
    calls = []
    monkeypatch.setattr(dl, "snapshot_download", lambda **kw: calls.append(kw))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="full commit"):
        dl.main(["--with-base", "--probe-file", str(tmp_path / "probe.json")])
    assert calls == []


def test_the_fetch_script_passes_with_base_and_the_reused_setup_files_are_gate_bs(kit):
    text = (kit.root / "setup" / "setup_and_fetch_stage1.sh").read_text()
    assert 'download_models_stage1.py "$@"' in text
    for name in ("bootstrap_hr.sh", "constraints.txt", "extend_cap.py"):
        assert (kit.root / "setup" / name).read_bytes() == (GBK / "setup" / name).read_bytes(), name


# ===== The preflight's O500 projection ======================================================================================

@pytest.mark.parametrize("pod_e1, branch, expected", [(E1, "full", 1517.0), (2 * E1, "full", 3034.0),
                                                      (0.5 * E1, "full", 1517.0), (1.2 * E1, "128", 1.2 * 1024.0)])
def test_the_preflight_projects_o500_from_the_pods_evaluation_speed(kit, pod_e1, branch, expected):
    pre = kit("setup/preflight_stage1.py")
    plan = {"fixture": {"e1_upper_s": E1}, "records": {"branch": {"branch": branch}}}
    got = pre.o500_projection({"e1_upper_s": pod_e1}, plan)
    assert got["o500_s"] == pytest.approx(expected)                        # never below the plan's own value
    assert pre.o500_projection({}, plan)["o500_s"] is None
    assert pre.o500_projection({"e1_upper_s": E1}, {"fixture": {"e1_upper_s": E1}, "records": {}})["branch"] == "full"


# ===== The packer: one stage per engine, inputs by SHA-256 ===================================================================

class Repo:
    """A synthetic checkout around the kit copy (ROOT = tmp) for pack_setup.py: engine files, the W1 pins, MAN1, Gate
    B's MANIFEST, W1-18's settings and one unit, the prepared set, the base pins record and the lead's inputs."""

    def __init__(self, kit, monkeypatch):
        self.kit, self.mp = kit, monkeypatch
        self.repo = repo = kit.repo
        self.pack = kit("pack_setup.py")
        r = self.rules = self.pack.rules
        mp = monkeypatch
        write(repo / "experiments/minimal_safety/requirements.lock", "torch==2.8.0\n")
        write(repo / "experiments/safety_selection/engine.py", "ENGINE = 'x'\n")
        for name in self.pack.PREFLIGHT_SCRIPTS:
            write(repo / "scripts" / name, f"# {name}\n")
        for path in (REC, S, G):
            mp.setitem(r.RECIPE_PINS, path, sha(write(repo / path, {"recipe": path})))
        write(repo / self.pack.PROCESS_RECEIPT, "# process receipt\n")
        reader = write(repo / "scripts/family_probe_reading.py", "# reader\n")
        unit = repo / "tmp" / "gate-a/u1"
        complete, jobf = write(unit / "COMPLETE.json", {"complete": True}), write(unit / "job.json", {"j": 1})
        write(unit / "eval" / "e1" / "generations.jsonl", '{"text": "SENTINEL-U-VALUE"}\n')
        settings = write(repo / self.pack.W1_18_SETTINGS, {
            "units": {"u1": {"path": "gate-a/u1", "complete_sha256": sha(complete), "job_sha256": sha(jobf)}},
            "frozen_reader": {"r": {"path": "scripts/family_probe_reading.py", "sha256": sha(reader)}}})
        code = write(repo / "scripts/stage1/limits/overrefusal_checks.py", "# w1-18\n")
        mp.setattr(r, "STAGE1_PINS", {self.pack.W1_18_SETTINGS: sha(settings)})
        mp.setattr(r, "D2_CODE", {rel: sha(write(repo / rel, f"# {rel} (synthetic)\n")) for rel in r.D2_CODE})
        # round 3b: the S1 package by its pins (synthetic bytes; each settings file pins engine X, addendum §11.7)
        mp.setattr(r, "S1_CODE", {rel: sha(write(repo / rel, {"name": rel, "engine_x": X} if rel.endswith(".json")
                                                 else f"# {rel} (synthetic)\n")) for rel in r.S1_CODE})
        a1 = write(repo / r.A1_EDIT["path"], "a1 edit\n")
        pin = {"path": r.A1_EDIT["path"], "sha256": sha(a1)}
        mp.setattr(r, "MAN1_EDIT_ARMS", {"A1": pin})
        self.anchor = write(repo / "tmp/anchors/anchor_bank.json", {"anchors": "synthetic"})
        self.man1 = [{**pin, "role": "sealed record"},
                     {"path": "scripts/stage1/limits/overrefusal_checks.py", "sha256": sha(code), "role": "code"},
                     {"path": "tmp/anchors/anchor_bank.json", "sha256": sha(self.anchor), "role": "pinned input"}]
        self.write_man1()
        r1 = write(repo / Path(r.MAN_PATH).parent / "edits/r1.edit.json", "r1 edit\n")
        mp.setattr(r, "MAN_SHA256", sha(write(repo / r.MAN_PATH, {"files": [
            {"role": "edit", "family": "R", "draw": 1, "arm": "edit-" + sha(r1), "path": "edits/r1.edit.json",
             "sha256": sha(r1)}]})))
        prep = write(repo / "tmp/kt-prepared/prepared-kt-dolly-olmo2/manifest.sha256", "p" * 64 + "\n")
        write(prep.parent / "manifest.json", {"m": 1})
        mp.setattr(r, "PREPARED_MANIFESTS", {"prepared-kt-dolly-olmo2": "p" * 64})
        probes = self.pack.probes
        base = write(repo / r.BASE_PINS_RECORD["path"], {"repo_id": probes.BASE["repo_id"],
                                                          "revision": probes.BASE["revision"],
                                                          "files": probes.BASE_FILES})
        mp.setattr(r, "BASE_PINS_RECORD", {"path": r.BASE_PINS_RECORD["path"], "sha256": sha(base)})
        write(repo / "tmp/evals/1101/eval/e1/summary.json", {"u": SENTINELS[0]})
        self.identity = {"X": X, "Y": Y}
        mp.setattr(self.pack, "git_state", lambda: "c" * 40)
        mp.setattr(self.pack, "engine_code", lambda tree: self.identity["Y" if tree != self.pack.ROOT else "X"])

    def write_man1(self):
        self.mp.setattr(self.rules, "MAN1_SHA256", sha(write(self.repo / self.rules.MAN1_PATH, {"entries": self.man1})))

    def inputs(self, engine="X", extra=None, **change):
        summary = self.repo / "tmp/evals/1101/eval/e1/summary.json"
        doc = {"kind": "stage1 pack inputs", "engine": engine, "recorded_by": "test", "utc": "2026-10-23T14:00:00Z",
               "code": [{"path": "scripts/stage1/limits/overrefusal_checks.py",
                         "sha256": sha(self.repo / "scripts/stage1/limits/overrefusal_checks.py")}],
               "inputs": [{"name": "anchor_bank", "path": "tmp/anchors/anchor_bank.json", "sha256": sha(self.anchor)},
                          {"name": "gate_a_eval:1101", "path": "tmp/evals/1101",
                           "files": [{"path": "eval/e1/summary.json", "sha256": sha(summary)}]},
                          *(extra or [])], **change}
        p = write(self.repo / "records" / f"inputs-{engine}.json", doc)
        return ["--inputs", str(p), "--inputs-sha256", sha(p)]

    def y_tree(self, good=True) -> Path:
        tree = self.repo / "engine-y-tree"
        shutil.copytree(self.repo / "experiments", tree / "experiments")
        shutil.copytree(self.repo / "scripts", tree / "scripts")
        bqi = write(tree / BQI, {"recipe": "bqi"})
        self.mp.setitem(self.rules.RECIPE_PINS, BQI, sha(bqi))
        listed = tree / "experiments/safety_selection/engine.py"
        line = f"{sha(listed)}  experiments/safety_selection/engine.py\n{sha(bqi)}  {BQI}\n"
        yh = write(self.repo / self.rules.YHASH_PIN["path"], line)
        self.mp.setattr(self.rules, "YHASH_PIN", {"path": self.rules.YHASH_PIN["path"], "sha256": sha(yh)})
        if not good:
            listed.write_text("ENGINE = 'changed'\n")
        return tree


def test_the_pack_takes_pool_s3_orig_only_at_the_sha256_j6s_record_names(kit, monkeypatch):
    """(D, pod a-1) pool:s3_orig is J6's pulled s3_orig pool, accepted only at the SHA-256 that plan.json's complete
    J6 records and that J6's own record names (stage1_rules.s3_orig_pin); another file, or no complete J6, refuses."""
    repo = Repo(kit, monkeypatch)
    tree = kit.root / "retrieved" / "a-1" / "tree"
    pool = write(tree / "job-0/untuned/s3_orig.pool.json", {"kind": "stage1 text pool", "name": "s3_orig", "items": "x"})
    other = write(tree / "job-0/untuned/other.pool.json", {"kind": "stage1 text pool", "name": "s3_orig", "items": "y"})
    rec = write(tree / "job-0/untuned/untuned_answers_record.json",
                {"kind": "stage1 untuned answers record", "version": 1, "complete": True,
                 "full_files": {"s3_orig.pool.json": sha(pool)}, "lists": {"s3": {"s3_orig_pool_sha256": sha(pool)}}})
    j6 = {"kind": "untuned_answers", "status": "complete",
          "outputs": {"job-0/untuned/s3_orig.pool.json": sha(pool), "job-0/untuned/untuned_answers_record.json": sha(rec)}}
    rel = "runkit/stage1-olmo/retrieved/a-1/tree/job-0/untuned/"
    write(kit.root / "plan.json", {"hosts": {"a-1": {"jobs": [{**j6, "status": "crashed"}]}}})
    with pytest.raises(SystemExit, match="no pin from J6's record in plan.json"):
        repo.pack.main(["X", *repo.inputs(extra=[{"name": "pool:s3_orig", "path": rel + "s3_orig.pool.json",
                                                  "sha256": sha(pool)}])])
    write(kit.root / "plan.json", {"hosts": {"a-1": {"jobs": [j6]}}})
    with pytest.raises(SystemExit, match="not J6's s3_orig pool"):
        repo.pack.main(["X", *repo.inputs(extra=[{"name": "pool:s3_orig", "path": rel + "other.pool.json",
                                                  "sha256": sha(other)}])])
    assert not (kit.root / "setup" / "packed-stage1-X").exists()
    repo.pack.main(["X", *repo.inputs(extra=[{"name": "pool:s3_orig", "path": rel + "s3_orig.pool.json",
                                              "sha256": sha(pool)}])])
    doc = json.loads((kit.root / "setup/packed-stage1-X/sealed-files.json").read_text())
    assert doc["inputs"]["pool:s3_orig"] == "inputs/pool-s3_orig/s3_orig.pool.json"
    assert doc["files"]["inputs/pool-s3_orig/s3_orig.pool.json"] == sha(pool)


def test_the_x_pack_seals_every_input_and_edit_by_sha256(kit, monkeypatch, capsys):
    repo = Repo(kit, monkeypatch)
    repo.pack.main(["X", *repo.inputs()])
    out = kit.root / "setup" / "packed-stage1-X"
    receipt = json.loads((out / "setup-receipt.json").read_text())
    doc = json.loads((out / "sealed-files.json").read_text())
    assert receipt["engine_sha256"] == X and receipt["stage"] == "stage1-X"
    assert receipt["sealed_files_sha256"] == sha(out / "sealed-files.json")
    assert doc["inputs"] == {"anchor_bank": "inputs/anchor_bank/anchor_bank.json", "gate_a_eval:1101":
                             "inputs/gate_a_eval-1101", "w1_18_data": "data"}
    files = doc["files"]
    assert files["inputs/anchor_bank/anchor_bank.json"] == sha(repo.anchor)
    assert files["inputs/gate_a_eval-1101/eval/e1/summary.json"]
    assert files[f"edits/{repo.rules.A1_EDIT and repo.rules.MAN1_EDIT_ARMS['A1']['sha256']}.edit.json"]
    assert len([f for f in files if f.startswith("edits/")]) == 2              # R_1 from Gate B's MANIFEST and A1
    assert files["data/gate-a/u1/COMPLETE.json"] and files[f"data/kt-prepared/prepared-kt-dolly-olmo2/manifest.sha256"]
    assert files["scripts/family_probe_reading.py"] and files["scripts/stage1/limits/overrefusal_checks.py"]
    probe = json.loads((out / "probe.json").read_text())
    assert probe["plan"][-1]["role"] == "base" and probe["plan"][-1]["revision"] == repo.pack.probes.BASE["revision"]
    boot = (out / "worker_bootstrap_stage1.sh").read_text()
    assert 'bash setup_and_fetch_stage1.sh "$@"' in boot and f"'data/kt-prepared',name" in boot
    printed = capsys.readouterr().out
    assert not any(s in printed for s in SENTINELS)


@pytest.mark.parametrize("case", ["changed input byte", "unknown name", "differs from MAN1", "engine identity",
                                  "constraints", "a second pack"])
def test_the_pack_refuses_before_writing_anything(kit, monkeypatch, case):
    repo = Repo(kit, monkeypatch)
    args = repo.inputs()
    if case == "changed input byte":
        args = repo.inputs()
        repo.anchor.write_text('{"anchors": "changed"}')
    elif case == "unknown name":
        args = repo.inputs(extra=[{"name": "hidden_bank", "path": "tmp/anchors/anchor_bank.json",
                                   "sha256": sha(repo.anchor)}])
    elif case == "differs from MAN1":
        other = write(repo.repo / "tmp/anchors/other.json", {"a": 2})
        repo.man1.append({"path": "tmp/anchors/other.json", "sha256": "0" * 64, "role": "pinned input"})
        repo.write_man1()
        args = repo.inputs(extra=[{"name": "pool:plant", "path": "tmp/anchors/other.json", "sha256": sha(other)}])
    elif case == "engine identity":
        repo.identity["X"] = Y
    elif case == "constraints":
        (kit.root / "setup" / "constraints.txt").write_text("setuptools==1.0\n")
    elif case == "a second pack":
        (kit.root / "setup" / "packed-stage1-X").mkdir()
    with pytest.raises(SystemExit):
        repo.pack.main(["X", *args])
    if case != "a second pack":
        assert not (kit.root / "setup" / "packed-stage1-X").exists()


@pytest.mark.parametrize("kind", ["file", "folder"])
def test_a_named_input_that_man1_lists_with_another_sha256_refuses_by_that_check_alone(kit, monkeypatch, kind):
    """Round 3b item 3, survivor B15-r-pack-man1 (round 2's spec): a named input whose path MAN1 lists must carry
    MAN1's SHA-256. The round-1 case used pool:plant, which input_pins refuses anyway (not its D-2 pin); here the
    input is the anchor bank (no D-2 pin), so only the MAN1 comparison can refuse it, and the message names it."""
    repo = Repo(kit, monkeypatch)
    if kind == "file":
        repo.man1[-1] = {**repo.man1[-1], "sha256": "0" * 64}           # MAN1 lists the anchor bank at another hash
        repo.write_man1()
        args, match = repo.inputs(), "input anchor_bank differs from MAN1"
    else:
        repo.man1.append({"path": "tmp/evals/1101/eval/e1/summary.json", "sha256": "0" * 64, "role": "pinned input"})
        repo.write_man1()
        args, match = repo.inputs(), "input gate_a_eval:1101: eval/e1/summary.json differs from MAN1"
    with pytest.raises(SystemExit, match=match):
        repo.pack.main(["X", *args])
    assert not (kit.root / "setup" / "packed-stage1-X").exists()


def test_the_y_pack_comes_from_the_frozen_tree_checked_against_yhash(kit, monkeypatch):
    repo = Repo(kit, monkeypatch)
    tree = repo.y_tree()
    assert repo.pack.parse(["Y", *repo.inputs("Y")]).y_tree == str(kit.root.parents[1] / "tmp" / "engine-y-34bfd288")
    with pytest.raises(SystemExit):
        repo.pack.parse(["X", "--y-tree", str(tree), *repo.inputs("X")])       # --y-tree goes with Y only
    repo.pack.main(["Y", "--y-tree", str(tree), *repo.inputs("Y")])
    receipt = json.loads((kit.root / "setup" / "packed-stage1-Y" / "setup-receipt.json").read_text())
    assert receipt["engine_sha256"] == Y and receipt["yhash_files"] == 2 and receipt["git_commit"] is None
    shutil.rmtree(kit.root / "setup" / "packed-stage1-Y")
    with pytest.raises(SystemExit, match="inputs"):
        repo.pack.main(["Y", "--y-tree", str(tree), *repo.inputs("X")])         # a record for another engine


def test_a_y_tree_that_fails_yhash_refuses(kit, monkeypatch):
    repo = Repo(kit, monkeypatch)
    tree = repo.y_tree(good=False)
    with pytest.raises(SystemExit, match="YHASH"):
        repo.pack.main(["Y", "--y-tree", str(tree), *repo.inputs("Y")])
    assert not (kit.root / "setup" / "packed-stage1-Y").exists()
    repo2_tree = tree
    write(repo.repo / repo.rules.YHASH_PIN["path"], "changed list\n")
    with pytest.raises(SystemExit, match="YHASH"):
        repo.pack.y_tree_check(repo2_tree)


def test_the_base_row_must_equal_the_pins_record(kit, monkeypatch):
    repo = Repo(kit, monkeypatch)
    monkeypatch.setitem(repo.pack.probes.BASE_FILES[0], "size", 1)
    with pytest.raises(SystemExit, match="base model row"):
        repo.pack.check_base_pins()


# ===== orchestrate: check-plan, the W1-18 hold, the packed engine and the reference ============================================

def orch(kit, monkeypatch, jobs_fn, engine="X", branch=True, sealed_extra=(), certification=None, reference=True):
    o = kit("orchestrate.py")
    r = o.rules
    jobs = jobs_fn(r)
    h = host_record(r, jobs, engine)
    packed = kit.root / "setup" / f"packed-stage1-{engine}"
    files = {rel: "a" * 64 for rels in o.runner.SCRIPTS.values() for rel in rels}
    files.update({o.runner.OEXT_MODULE: "a" * 64, "scripts/stage1_s1/settings/oext_eval.json": "a" * 64})
    files.update({rel: "a" * 64 for rel in sealed_extra})
    inputs = {name: rel for name, rel in INPUT_FILES.items() if rel} | {"reuse_spec": "inputs/r/reuse_spec.json"}
    files.update({rel: "a" * 64 for rel in inputs.values()})
    sealed = write(packed / "sealed-files.json", {"files": files, "inputs": inputs})
    write(packed / "setup-receipt.json", {"engine_sha256": r.ENGINES[engine], "sealed_files_sha256": sha(sealed)})
    h["sealed_files_sha256"] = sha(sealed)
    plan = {"hosts": {"h-1": h}, "records": {"branch": {"branch": "full"} if branch else None,
                                             "certification": certification},
            "reference": {"fields": {"f": 1}, "bootstrap": {}, "guard": None} if reference else None}
    write(kit.root / "plan.json", plan)
    return o


def test_check_plan_refuses_a_job_whose_o_ext_script_is_not_packed(kit, monkeypatch):
    """Round 3c: an O-ext step needs the runner AND its settings in the packed stage (the X pack carries both by
    their S1_CODE pins); with either missing check-plan refuses, with both it passes."""
    o = orch(kit, monkeypatch, lambda r: [job(r, "o_only", "theta0")])
    with pytest.raises(SystemExit, match="2 file.s. not packed"):
        o.check_plan("h-1")
    for missing in ("scripts/stage1_s1/oext_unit.py", "scripts/stage1_s1/settings/oext_unit.json"):
        o = orch(kit, monkeypatch, lambda r: [job(r, "o_only", "theta0")],
                 sealed_extra=[rel for rel in ("scripts/stage1_s1/oext_unit.py",
                                               "scripts/stage1_s1/settings/oext_unit.json") if rel != missing])
        with pytest.raises(SystemExit, match=re.escape(f"1 file(s) not packed: ['{missing}']")):
            o.check_plan("h-1")
    o = orch(kit, monkeypatch, lambda r: [job(r, "o_only", "theta0")],
             sealed_extra=["scripts/stage1_s1/oext_unit.py", "scripts/stage1_s1/settings/oext_unit.json"])
    assert o.check_plan("h-1")["ok"] is True
    o = orch(kit, monkeypatch, lambda r: [job(r, "l1_scan")])
    assert o.check_plan("h-1")["ok"] is True


@pytest.mark.parametrize("branch, needed", [("128", True), ("full", False)])
def test_under_branch_128_check_plan_needs_w1_18s_record_packed(kit, monkeypatch, branch, needed):
    """(F) Branch 128's O-ext settings pin W1-18's record, so every O-ext step reads it: check-plan refuses a Branch-128
    O-ext job whose pack holds no w1_18_record ($0, on the Mac) instead of the pod refusing; under Branch full it stays
    optional (Branch full by default has no record)."""
    extra = ["scripts/stage1_s1/oext_unit.py", "scripts/stage1_s1/settings/oext_unit.json"]
    o = orch(kit, monkeypatch, lambda r: [job(r, "o_only", "theta0", branch=branch)], sealed_extra=extra)
    assert o.check_plan("h-1")["ok"] is True
    packed = kit.root / "setup" / "packed-stage1-X"
    doc = json.loads((packed / "sealed-files.json").read_text())
    del doc["files"][doc["inputs"].pop("w1_18_record")]
    sealed = write(packed / "sealed-files.json", doc)
    write(packed / "setup-receipt.json", {"engine_sha256": X, "sealed_files_sha256": sha(sealed)})
    plan = json.loads((kit.root / "plan.json").read_text())
    plan["hosts"]["h-1"]["sealed_files_sha256"] = sha(sealed)
    write(kit.root / "plan.json", plan)
    if needed:
        with pytest.raises(SystemExit, match="<input w1_18_record>"):
            o.check_plan("h-1")
    else:
        assert o.check_plan("h-1")["ok"] is True


def test_check_plan_refuses_a_packed_engine_that_is_not_the_hosts(kit, monkeypatch):
    o = orch(kit, monkeypatch, lambda r: [job(r, "l1_scan")])
    receipt = kit.root / "setup" / "packed-stage1-X" / "setup-receipt.json"
    write(receipt, {**json.loads(receipt.read_text()), "engine_sha256": Y})
    with pytest.raises(SystemExit, match="G4"):
        o.check_plan("h-1")
    plan = json.loads((kit.root / "plan.json").read_text())
    plan["hosts"]["h-1"]["stage"] = "stage1-Y"
    write(kit.root / "plan.json", plan)
    with pytest.raises(SystemExit, match="G4"):
        o.packed("h-1")


def test_the_w1_18_hold(kit, monkeypatch):
    o = orch(kit, monkeypatch, lambda r: [job(r, "w1_18"), job(r, "l1_scan")])
    with pytest.raises(SystemExit, match="alone"):
        o.w1_18_hold("h-1")
    o = orch(kit, monkeypatch, lambda r: [job(r, "o_only", "theta0")], branch=False)
    with pytest.raises(SystemExit, match="W1-18's branch record"):
        o.w1_18_hold("h-1")
    o = orch(kit, monkeypatch, lambda r: [job(r, "o_only", "theta0")])
    o.w1_18_hold("h-1")
    o = orch(kit, monkeypatch, lambda r: [job(r, "w1_18")], branch=False)
    o.w1_18_hold("h-1")


def test_reference_pods_compare_with_the_certification_pod_and_others_with_gate_b(kit, monkeypatch):
    stub = write(kit.repo / "stub" / "reading.py", "def compared_fields(environment, lock, policy):\n"
                                                    "    return {'lock_sha256': lock, **environment}\n")
    o = orch(kit, monkeypatch, lambda r: [job(r, "l1_scan")])
    monkeypatch.setattr(o.mac, "READING", stub)
    ref, strict = o.reference_for("h-1")
    assert strict is True and ref["fields"] == {"f": 1}
    o = orch(kit, monkeypatch, lambda r: [job(r, "l1_scan")], reference=False)
    with pytest.raises(SystemExit, match="import-reference"):
        o.reference_for("h-1")
    jobs = lambda r: [job(r, "ref_eval", "a0", 1104, points=["scale:0.9"], recipe="B")]
    o = orch(kit, monkeypatch, jobs, certification=None)
    with pytest.raises(SystemExit, match="certification"):
        o.reference_for("h-1")
    o = orch(kit, monkeypatch, jobs, certification={"host": "cfy-1", "pass": True})
    monkeypatch.setattr(o.mac, "READING", stub)
    write(kit.root / "hosts" / "cfy-1" / "bootstrap-ready.json", {"lock_sha256": "l" * 64, "gpu": "A100",
                                                                  "cuda_runtime": "12.8", "pip_version": "25"})
    write(kit.root / "hosts" / "cfy-1" / "verification.json", {"environment": {"torch": "2.8.0"}})
    write(kit.root / "hosts" / "cfy-1" / "preflight-done.json", {"guard": {"g": 1}})
    ref, strict = o.reference_for("h-1")
    assert ref["fields"] == {"lock_sha256": "l" * 64, "torch": "2.8.0"} and ref["guard"] == {"g": 1}
    assert ref["bootstrap"]["gpu"] == "A100" and "certification pod cfy-1" == ref["source"]
    o = orch(kit, monkeypatch, jobs, certification={"host": "cfy-1", "pass": False})
    with pytest.raises(SystemExit, match="passing"):
        o.reference_for("h-1")


def test_the_preflight_plan_names_the_hosts_preflight_recipe(kit, monkeypatch):
    runner = kit("setup/job_runner_stage1.py")
    r = runner.rules
    assert runner.preflight_recipe({"jobs": [job(r, "l1_scan"), job(r, "arm", "A1", 1102, recipe="S")]}) == S
    assert runner.preflight_recipe({"jobs": [job(r, "w1_18")]}) == REC
    assert runner.preflight_recipe({"jobs": [job(r, "ref_train", "bqi", 1102, engine="Y", recipe="bqi")]}) == BQI


# ===== Judges: B10 units through the stage-1 wrapper, one device type per contrast ============================================

def judge_tree(kit):
    judges = kit.repo / "scripts" / "gate_b_mac_judges"
    judges.mkdir(parents=True)
    for name in ("units.py", "common.py"):
        shutil.copy(WS_B15 / "scripts" / "gate_b_mac_judges" / name, judges / name)
    tree = kit.repo / "retrieved" / "b-1" / "tree"

    def unit(rel, job_doc, identity):
        folder = tree / rel
        gen = write(folder / "eval" / "e1" / "generations.jsonl",
                    json.dumps({"kind": "harm", "prompt_id": "p1", "text": SENTINELS[1]}) + "\n")
        jb = write(folder / "job.json", job_doc)
        if identity:
            write(folder / "identity.json", {"i": 1})
        write(folder / "COMPLETE.json", {"complete": True, "job_sha256": sha(jb),
                                         "files": {"eval/e1/generations.jsonl": sha(gen)}})
        return folder
    b10 = unit("job-3/evals/1105-scale", {"kind": "stage1-eval-adapter", "evaluate_bank": "dev", "checkpoint": "e1",
                                          "seed": 1105, "mode": "scale", "adapter_scale": 0.9}, identity=False)
    eng = unit("round1/1105-a0-e1-a1", {"kind": "run-one", "evaluate_bank": "dev", "target_checkpoint": "e1",
                                        "arm": "a0", "seed": 1105}, identity=True)
    return tree.parents[1], b10, eng


def test_a_b10_unit_is_judged_by_the_stage1_wrapper_and_still_skipped_by_gate_bs_units(kit, monkeypatch):
    root, b10, eng = judge_tree(kit)
    wrapper = kit("judge_units_stage1.py")
    units = wrapper.gate_b_units()
    gb, skipped = units.enumerate_units([root])
    assert [u.unit for u in gb] == ["round1/1105-a0-e1-a1"]                  # Gate B judges the engine unit only
    assert any(s["unit"] == "job-3/evals/1105-scale" for s in skipped)
    found, skipped2 = wrapper.enumerate_units([root])
    assert [(u.unit, u.arm, u.kind) for u in found] == [("job-3/evals/1105-scale", "ref-scale-0.9",
                                                         "stage1-eval-adapter"),
                                                        ("round1/1105-a0-e1-a1", "a0", "run-one")]
    assert not any(s["unit"] == "job-3/evals/1105-scale" for s in skipped2)
    assert (WS_B15 / "scripts/gate_b_mac_judges/units.py").read_bytes() == \
        (kit.repo / "scripts/gate_b_mac_judges/units.py").read_bytes()       # units.py unchanged
    with wrapper.stage1_enumeration():
        listed, _ = units.units_from_args(argparse.Namespace(run_root=[root], unit=[], targets=["init", "e1"]))
    assert len(listed) == 2 and units.enumerate_units.__module__ != wrapper.__name__  # restored afterwards
    write(b10 / "eval" / "e1" / "stray.json", {})
    with pytest.raises(units.Refusal):
        wrapper.enumerate_units([root])                                      # fail-closed, as units.py


def test_one_device_type_per_contrast(kit, monkeypatch):
    judge_tree(kit)
    wrapper = kit("judge_units_stage1.py")
    a100 = {"device": "cuda", "environment": {"gpu": "NVIDIA A100-SXM4-80GB"}}
    h100 = {"device": "cuda", "environment": {"gpu": "NVIDIA H100 80GB HBM3"}}
    assert wrapper.check_devices({"A1-vs-a0": ["u1", "u2"]}, {"u1": a100, "u2": a100})["A1-vs-a0"]["units"] == 2
    with pytest.raises(wrapper.gate_b_units().Refusal, match="device types"):
        wrapper.check_devices({"A1-vs-a0": ["u1", "u2"]}, {"u1": a100, "u2": h100})
    with pytest.raises(wrapper.gate_b_units().Refusal, match="without a judge run record"):
        wrapper.check_devices({"A1-vs-a0": ["u1", "u3"]}, {"u1": a100})
    with pytest.raises(wrapper.gate_b_units().Refusal, match="device types"):
        wrapper.check_devices({"c": ["u1", "u2"]}, {"u1": a100, "u2": {**a100, "device": "mps"}})


# ===== Seal: no printed line and no record holds an outcome value ==============================================================

def test_no_printed_line_or_runner_record_holds_a_sentinel_value(kit, tmp_path, monkeypatch, capsys):
    a1 = edit_ref("A1")
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [*regen_pair(r), job(r, "arm", "A1", 1102, edit=a1, recipe="S"),
                                                     job(r, "o_only", "theta0"), job(r, "classifier")])
    pod.remaining([30 * H])
    assert pod.main() == 0
    texts = [capsys.readouterr().out]
    for p in [pod.root / "JOB-DONE.json", *(pod.root / "job-done").iterdir(), *pod.root.glob("job-*/cost-ledger.json"),
              *pod.root.glob("job-*/regeneration-adapter-fingerprint.json")]:
        texts.append(p.read_text())
    assert len(texts) >= 12
    outcome = (pod.root / "job-3" / "oext" / "oext_summary.json").read_text()
    assert SENTINELS[3] in outcome                                           # the fixture holds the sentinel ...
    for text in texts:
        assert not any(s in text for s in SENTINELS)                         # ... and nothing the kit wrote or printed


def test_the_backup_stages_the_stage1_records_and_the_seal(kit, tmp_path, monkeypatch, capsys):
    backup = kit("backup_records_stage1.py")
    r = backup.rules
    k = kit.root
    w1 = [job(r, "w1_18")]
    w1[0].update(status="complete", outputs=None)
    tree = k / "retrieved" / "s10-1" / "tree"
    out = write(tree / "job-0" / "w1-18" / "overrefusal_checks.json", {"flags": SENTINELS[2]})
    w1[0]["outputs"] = {"job-0/w1-18/overrefusal_checks.json": sha(out)}
    h = host_record(r, w1, block="S1-0", role="w1_18")
    seal = write(k / "seals" / "block-S1-0.json", {"files": [{"host": "s10-1", "path": "job-0/w1-18/overrefusal_checks.json",
                                                             "sha256": sha(out), "class": "sealed"}]})
    write(k / "plan.json", {"name": "stage1-olmo", "hosts": {"s10-1": h}, "prepared": {"prepared-kt-dolly-olmo2": "p" * 64},
                            "seals": {"S1-0": {"sha256": sha(seal)}}})
    prep = kit.repo / "tmp/kt-prepared/prepared-kt-dolly-olmo2"
    write(prep / "manifest.json", {"m": 1})
    plan = json.loads((k / "plan.json").read_text())
    plan["prepared"] = {"prepared-kt-dolly-olmo2": sha(prep / "manifest.json")}
    write(k / "plan.json", plan)
    write(prep / "manifest.sha256", sha(prep / "manifest.json") + "\n")
    for name in ("budget-checks.jsonl", "operator-actions.jsonl", "hosts-full-s10-1.log", "launch.log", "finisher.log"):
        write(k / name, "{}\n")
    write(k / "hosts" / "s10-1" / "finished.json", {"ok": True})
    assert backup.main(["--dry-run", "--tag", "backup-2026-10-23-stage1"]) == 0
    printed = capsys.readouterr().out
    assert "analyses/seals/block-S1-0.json" in printed and not any(s in printed for s in SENTINELS)
    out.write_text("changed")
    assert backup.main(["--dry-run", "--tag", "backup-2026-10-23-stage1"]) == 2
    capsys.readouterr()
    sel = backup.select(json.loads((k / "plan.json").read_text()), ["s10-1"], 50 * 1024 * 1024)
    assert any("recorded output" in m for m in sel["missing"]) and any("seal of block S1-0" in m for m in sel["missing"])


# ===== The kit's files ==========================================================================================================

RUNNER_FILES = ("orchestrate.py", "pack_setup.py", "probes.py", "backup_records_stage1.py", "judge_units_stage1.py",
                "setup/job_runner_stage1.py", "setup/preflight_stage1.py", "setup/download_models_stage1.py",
                "setup/extend_cap.py")
GBK_PINS = {"orchestrate.py": "30d284dd54fd2b25", "pack_setup.py": "0c985e5e3ac05b73",
            "backup_records_gateb.py": "7f5dcc12fbb7ae5c", "setup/job_runner_gateb.py": "5e7f1e8f6145d0a7",
            "setup/preflight_gateb.py": "64b0a3526fe600e2", "setup/download_models_gateb.py": "e471368a984fb918",
            "README.md": "9f23367effb8684d", "probes.py": "6c2e9afe", "setup/bootstrap_hr.sh": "563a128a",
            "setup/setup_and_fetch_gateb.sh": "f76cbc7a", "setup/extend_cap.py": "8af2f6cc",
            "setup/constraints.txt": "cdd9f130"}           # brief §6's SHA-256 prefixes of the Gate B kit files


def test_the_runner_files_compile_hold_no_secret_and_gate_b_is_unchanged(tmp_path):
    import py_compile
    for rel in RUNNER_FILES:
        py_compile.compile(str(KIT / rel), cfile=str(tmp_path / "x.pyc"), doraise=True)
    sys.path.insert(0, str(KIT))
    try:
        sys.modules.pop("secret_scan", None)
        import secret_scan
        assert secret_scan.scan_paths([KIT / rel for rel in (*RUNNER_FILES, "README.md", "setup/setup_and_fetch_stage1.sh",
                                                               "tests/test_stage1_runner.py")]) == []
    finally:
        sys.path.remove(str(KIT))
        sys.modules.pop("secret_scan", None)
    for rel, prefix in GBK_PINS.items():
        assert sha(GBK / rel).startswith(prefix), rel
    readme = (KIT / "README.md").read_text()
    for needle in ("([D16] 8)", "([D17] 3)", "([D17] 4)", "([D21])", "**G0", "**G1", "**G2", "**G3", "**G4", "**G5",
                   "**G6", "attribution-s1-", "user RunPod top-up"):
        assert needle in readme, needle
    assert '"attribution-s1-"' in (KIT / "stage1_rules.py").read_text()



# ===== The B15 fix round (notes/b15-fix.json; each defect test failed on the kit before its fix) ======================

def test_every_b10_unit_of_a_multi_point_job_is_verified_and_recorded(kit, tmp_path, monkeypatch):
    """VR-2: one B10 unit per evaluation point; each is verified, and the record lists each with its SHA-256."""
    pod = safe_pod(kit, tmp_path, monkeypatch, points=("default", "conditional"))
    pod.remaining([30 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete"]
    verified = [a[a.index("--unit") + 1] for a in pod.ran if "eval_adapter.py" in " ".join(a) and "verify" in a]
    assert verified == ["job-0/eval-conditional", "job-0/eval-default"]
    units = pod.done()["jobs"][0]["units"]
    assert [(u["unit"], u["complete_sha256"]) for u in units] == [
        (u, sha(pod.root / u / "COMPLETE.json")) for u in ("job-0/eval-conditional", "job-0/eval-default")]


def test_a_multi_point_b10_job_missing_one_unit_is_a_crash(kit, tmp_path, monkeypatch):
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "ref_eval", "a0", 1104, points=["scale:0.9", "scale:0.5"],
                                                         recipe="B")])
    real = pod.run

    def one_unit(args, **kw):
        out = real(args, **kw)
        if args[:2] == ["python3", "process_receipt.py"] and args[3] == "job-0-b10-run":
            shutil.rmtree(pod.root / "job-0" / "evals" / "1104-scale:0.5")
        return out
    monkeypatch.setattr(pod.runner.subprocess, "run", one_unit)
    pod.remaining([30 * H])
    assert pod.main() == 1 and pod.statuses() == ["crashed"]
    assert "1 B10 unit(s) for 2 evaluation point(s)" in pod.done()["jobs"][0]["why"]


def test_each_safe_lora_point_has_its_own_judge_label(kit, monkeypatch):
    """VR-3: B10's job.json names no Safe LoRA point; the unit folder job-I/eval-<point> does."""
    root, _, _ = judge_tree(kit)
    tree = root / "b-1" / "tree"
    wrapper = kit("judge_units_stage1.py")

    def external(rel):
        folder = tree / rel
        gen = write(folder / "eval" / "e1" / "generations.jsonl", json.dumps({"kind": "harm", "text": "t"}) + "\n")
        jb = write(folder / "job.json", {"kind": "stage1-eval-adapter", "evaluate_bank": "dev", "checkpoint": "e1",
                                         "seed": 1104, "mode": "external",
                                         "external": {"name": "safe_lora",
                                                      "adapter_sha256": hashlib.sha256(rel.encode()).hexdigest()}})
        write(folder / "COMPLETE.json", {"complete": True, "job_sha256": sha(jb),
                                         "files": {"eval/e1/generations.jsonl": sha(gen)}})
        return folder
    external("job-5/eval-default")
    external("job-5/eval-conditional")
    found, _ = wrapper.enumerate_units([root])
    labels = sorted((u.arm, u.seed) for u in found if u.kind == "stage1-eval-adapter" and u.seed == 1104)
    assert labels == [("ref-external-safe_lora-conditional", 1104), ("ref-external-safe_lora-default", 1104)]
    external("job-6/elsewhere")
    with pytest.raises(wrapper.gate_b_units().Refusal, match="eval-<point>"):
        wrapper.enumerate_units([root])


def test_under_fallback_c_no_o_ext_step_runs(kit, tmp_path, monkeypatch):
    """C-1: addendum §11 point 1 fallback (c) (dev100_recipe_cap): arms run calibrate only; B10 and B17 get no O-ext
    flags; an O-only pass is unrunnable; the O-ext files and inputs are not needed."""
    a1 = edit_ref("A1")
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "arm", "A1", 1102, edit=a1, recipe="S"),
                                                     job(r, "ref_eval", "a0", 1104, points=["scale:0.9"], recipe="B"),
                                                     job(r, "o_only", "theta0")])
    pod.plan["records"]["oext_fallback"] = {"status": "dev100_recipe_cap"}
    write(pod.root / "plan.json", pod.plan)
    pod.remaining([30 * H])
    assert pod.main() == 1 and pod.statuses() == ["complete", "complete", "crashed"]
    assert pod.receipts() == ["job-0-calibrate", "job-1-b10-run"]
    b10 = [a for a in pod.ran if "job-1-b10-run" in a][0]
    assert "--oext-bank" not in b10 and "--oext-record" not in b10
    assert pod.done()["jobs"][0]["unit"] == f"round1/1102-edit-{a1['sha256']}-e1-a1"
    assert "fallback (c)" in pod.done()["jobs"][2]["why"]
    h = pod.plan["hosts"]["h-1"]
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    paths = pod.runner.sealed_paths(h["jobs"][0], h, 0, doc, True)
    assert pod.runner.OEXT_UNIT_SCRIPT not in paths and pod.runner.OEXT_MODULE not in paths
    assert pod.runner.OEXT_UNIT_SETTINGS not in paths                       # round 3c: nor the runner's settings


def test_a_branch_128_o_only_pass_on_a_regenerated_unit_names_its_source_unit(kit, tmp_path, monkeypatch):
    """C-2 (LN-19, §8 Q15): under Branch 128 the source unit's stored dev-100 answers are cut to 128 tokens, so the
    O-only pass on a regenerated a0 or R unit gets the source unit folder; theta0's does not."""
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "regenerate", "a0", 1101, branch="128"),
                                                     job(r, "o_only", "a0", 1101, regen_source=0, branch="128"),
                                                     job(r, "o_only", "theta0", branch="128")], branch="128")
    pod.remaining([30 * H])
    assert pod.main() == 0
    oext = [a for a in pod.ran if a[:2] == ["python3", "process_receipt.py"] and a[3].endswith("-oext")]
    parsed = [vars(pod.runner.oext_unit_contract().parse_args(a[7:])) for a in oext]
    assert parsed[0]["dev100_source"] == "inputs/source_unit-a0-1101" and parsed[1]["dev100_source"] is None
    h = pod.plan["hosts"]["h-1"]
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    assert "inputs/source_unit-a0-1101/COMPLETE.json" in pod.runner.sealed_paths(h["jobs"][1], h, 1, doc)


@pytest.mark.parametrize("pin, ok", [(X, True), ("0" * 64, False), (None, False)])
def test_the_pack_refuses_s1_settings_not_re_pinned_on_its_engine(kit, monkeypatch, pin, ok):
    """C-6 (addendum §11 point 7, 'a B15 pre-launch check'): a packed S1 settings file must pin the pack's engine."""
    repo = Repo(kit, monkeypatch)
    rel = "scripts/stage1_s1/settings/lean_eval_job.json"
    settings = write(repo.repo / rel, {"name": "lean", **({"engine_x": pin} if pin else {})})
    monkeypatch.setitem(repo.rules.S1_CODE, rel, sha(settings))     # round 3b: the X pack carries S1_CODE itself
    args = repo.inputs()
    if ok:
        repo.pack.main(["X", *args])
        assert json.loads((kit.root / "setup/packed-stage1-X/sealed-files.json").read_text())["files"][rel]
    else:
        with pytest.raises(SystemExit, match="re-pinned on engine X"):
            repo.pack.main(["X", *args])
        assert not (kit.root / "setup" / "packed-stage1-X").exists()


# ----- C-5: the pre-job stop path of B15's orchestrate copy (Gate B's [D17] 3 behaviour, re-run here) -----------------

@pytest.mark.parametrize("code, started", [(0, True), (1, False), (255, None), ("raise", None)])
def test_job_started_reads_exit_0_and_1_and_nothing_else(kit, monkeypatch, code, started):
    o = orch(kit, monkeypatch, lambda r: [job(r, "l1_scan")])

    def ssh(host, command):
        if code == "raise":
            raise OSError("synthetic")
        return subprocess.CompletedProcess([host], code, "", "")
    monkeypatch.setattr(o, "ssh", ssh)
    assert o.job_started("h-1") is started


@pytest.mark.parametrize("ssh_code, event", [(1, "pre-job-failed"), (255, "job-start-unknown")])
def test_a_failure_before_the_job_stops_the_pod_and_logs_its_step(kit, monkeypatch, ssh_code, event):
    """after_create: a failure before the job logs pre-job-failed with its step (job-start-unknown when the pod
    cannot say), moves the in-pod stop to 2 min and stops the pod (never deletes it), then logs pre-job-stop."""
    o = orch(kit, monkeypatch, lambda r: [job(r, "o_only", "theta0")])          # its O-ext script is not packed
    calls = []
    monkeypatch.setattr(o, "tool", lambda *a, **k: calls.append(a) or subprocess.CompletedProcess(a, 0, "", ""))
    monkeypatch.setattr(o, "ssh", lambda host, command: subprocess.CompletedProcess([host], ssh_code, "", ""))
    with pytest.raises(SystemExit, match="not packed"):
        o.after_create("h-1")
    assert calls == [("extend-cap", "h-1", "120"), ("stop", "h-1")]
    events = [json.loads(line) for line in (kit.root / "hosts" / "h-1" / "orchestrate.jsonl").read_text().splitlines()]
    assert [(e["event"], e.get("step"), e.get("exit")) for e in events] == [(event, "check-plan", None),
                                                                           ("pre-job-stop", None, 0)]
    assert not any(s in json.dumps(events) for s in SENTINELS)


# ===== B15 round 2 (addendum §19-§23): D-2 in J5 and J8, C3's pins, engine Y at 34bfd288, this repository only =========

DIAG = lambda r: [job(r, "untuned_answers"), job(r, "rep_pass"), job(r, "classifier")]     # noqa: E731


def test_j5_and_j8_run_through_d2_and_record_their_outputs(kit, tmp_path, monkeypatch):
    pod = Pod(kit, tmp_path, monkeypatch, DIAG)
    pod.remaining([20 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete"] * 3
    assert pod.receipts() == ["job-0-untuned", "job-1-representation", "job-1-representation-s3-orig",
                              "job-2-classifier"]
    sealed = json.loads((pod.root / "sealed-files.json").read_text())["files"]
    ran = {a[3]: a[5:] for a in pod.ran if a[:2] == ["python3", "process_receipt.py"]}
    pins = ["--pool-pins", f"{INPUT_FILES['d2_pool_pins']}:{sealed[INPUT_FILES['d2_pool_pins']]}",
            "--req8-record", f"{INPUT_FILES['req8_record']}:{sealed[INPUT_FILES['req8_record']]}"]
    s3 = "job-0/untuned/s3_orig.pool.json"
    assert ran["job-1-representation-s3-orig"][:2] == ["venv/bin/python", pod.rules.D2_REP_SCRIPT]
    assert ran["job-1-representation-s3-orig"][-4:] == pins and "--pools-only" in ran["job-1-representation-s3-orig"]
    assert f"{s3}:{sha(pod.root / s3)}" in ran["job-1-representation-s3-orig"]       # resolved at run time
    assert ran["job-2-classifier"][1] == pod.rules.D2_CLASSIFIER_SCRIPT and ran["job-2-classifier"][-4:] == pins
    assert pod.done()["jobs"][1]["outputs"]


# (D, 25 Oct: pod a-1) J5, J7 and J8 on a new pod without J6 (J6 complete on a-1, never re-run): J5's s3_orig pass
# reads J6's pool as the packed input pool:s3_orig by the moved job's plan.json pin
S3_ORIG_REL = "inputs/pool-s3_orig/s3_orig.pool.json"


def moved_diag(pin=None):
    def jobs(r):
        j5 = job(r, "rep_pass")
        digest = sha(pin) if isinstance(pin, Path) else pin            # the sealed file's SHA-256, or a given pin
        j5["s3_orig"] = {"host": "a-1", "index": 0, "sha256": digest,
                         "record": {"path": "job-0/untuned/untuned_answers_record.json", "sha256": "d" * 64},
                         "pool": {"path": "job-0/untuned/s3_orig.pool.json", "sha256": digest}}
        return [j5, job(r, "l1_scan"), job(r, "classifier")]
    return jobs


def test_a_moved_j5_reads_j6s_pool_as_the_pinned_packed_input_through_d2(kit, tmp_path, monkeypatch):
    """The s3_orig pools-only pass gets --pool <packed pool:s3_orig>:<SHA-256> (recipe S, --pools-only), which the D-2
    wrapper's own parser takes and forwards unchanged; representation_pass names a pool absent from its pins file
    (W1's and D-2's filled one) by the SHA-256 given with it ("command line"), so s3_orig needs no pins entry."""
    pool = tmp_path / "pod" / S3_ORIG_REL
    pod, out = dry_run(kit, tmp_path, moved_diag(pool), "X", monkeypatch, extra_inputs={"pool:s3_orig": S3_ORIG_REL})
    sealed = json.loads((pod.root / "sealed-files.json").read_text())["files"]
    cmds = {j["index"]: j["commands"] for j in out["jobs"]}
    s3 = cmds[0][1][1]
    assert cmds[0][1][0] == "job-0-representation-s3-orig" and s3[1] == "scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py"
    assert s3[s3.index("--pool") + 1] == f"{S3_ORIG_REL}:{sealed[S3_ORIG_REL]}" and "--pools-only" in s3
    assert s3[s3.index("--recipe") + 1] == S and cmds[0][0][1][cmds[0][0][1].index("--recipe") + 1] == S
    assert [j["kind"] for j in out["jobs"]] == ["rep_pass", "l1_scan", "classifier"]
    h = pod.plan["hosts"]["h-1"]
    assert S3_ORIG_REL in pod.runner.sealed_paths(h["jobs"][0], h, 0, json.loads((pod.root / "sealed-files.json")
                                                                                  .read_text()))
    argvs = [[v.replace("@", "AT-") for v in c[1][2:]] for c in cmds[0]]
    parsed = parse_with(REPO, "scripts.stage1_s1.d2_pool_pins.d2_representation_pass", argvs)
    assert all(p["ok"] for p in parsed) and parsed[1]["ns"]["pools_only"] is True
    assert f"{S3_ORIG_REL}:{sealed[S3_ORIG_REL]}" in parsed[1]["ns"]["pool"]
    code = ("import json,sys;sys.path.insert(0,sys.argv[1]);from scripts.stage1 import representation_pass as rp;"
            "out=[];\nfor f in sys.argv[2:]:\n  pins=rp.check_pool_pins(json.loads(open(f).read()))\n"
            "  out.append(rp.pin_of({'name':'s3_orig','sha256':'0'*64,'items':[1]},pins))\nprint(json.dumps(out))")
    done = REAL_RUN([PY, "-B", "-c", code, str(REPO), str(REPO / "scripts/stage1/settings/representation_pools.json"),
                     str(REPO / ".ai/inputs/stage1-post-w1-20261023/pool-pins/representation_pools.filled.json")],
                    cwd=REPO, capture_output=True, text=True, timeout=120,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0, done.stderr[-600:]
    assert json.loads(done.stdout.strip().splitlines()[-1]) == ["command line", "command line"]


@pytest.mark.parametrize("case, match", [("other pin", "packed s3_orig pool differs from the plan's pin"),
                                         ("not packed", "'pool:s3_orig' is not packed"),
                                         ("no pin, no J6", "no untuned_answers job earlier on this pod")])
def test_a_moved_j5_refuses_without_j6s_pinned_pool(kit, tmp_path, monkeypatch, case, match):
    extra = {} if case == "not packed" else {"pool:s3_orig": S3_ORIG_REL}
    jobs = moved_diag("0" * 64 if case == "other pin" else "c" * 64 if case == "not packed"
                      else tmp_path / "pod" / S3_ORIG_REL)
    if case == "no pin, no J6":
        jobs = (lambda base: (lambda r: [{k: v for k, v in j.items() if k != "s3_orig"} for j in base(r)]))(jobs)
    pod = Pod(kit, tmp_path, monkeypatch, jobs, extra_inputs=extra)
    with pytest.raises(pod.runner.Unrunnable, match=re.escape(match)):
        pod.runner.job_commands(pod.plan, "h-1", 0, pod.root, {})
    assert pod.runner.job_commands(pod.plan, "h-1", 1, pod.root, {})            # J7 is unaffected


def test_check_plan_accepts_the_moved_diagnostics_host_with_the_pinned_pool(kit, monkeypatch):
    def jobs(r):
        d2 = {"pool_pins": {"sha256": "a" * 64}, "req8_record": {"sha256": "a" * 64},
              "pools": {n: "a" * 64 for n in ("plant", "decoy", "s3_safe")}}
        j5, j7, j8 = job(r, "rep_pass"), job(r, "l1_scan"), job(r, "classifier")
        j5["d2"], j8["d2"] = d2, {**d2, "pools": {n: "a" * 64 for n in ("plant", "decoy")}}
        j5["s3_orig"] = {"host": "a-1", "index": 0, "sha256": "a" * 64}
        return [j5, j7, j8]
    o = orch(kit, monkeypatch, jobs)
    o = orch(kit, monkeypatch, jobs, sealed_extra=sorted({rel for rels in o.runner.D2_SCRIPTS.values() for rel in rels}))
    packed = kit.root / "setup" / "packed-stage1-X"
    with pytest.raises(SystemExit, match="pool:s3_orig"):
        o.check_plan("h-1")                                            # J6's pool is not packed yet
    doc = json.loads((packed / "sealed-files.json").read_text())
    doc["inputs"]["pool:s3_orig"], doc["files"][S3_ORIG_REL] = S3_ORIG_REL, "a" * 64
    sealed = write(packed / "sealed-files.json", doc)
    write(packed / "setup-receipt.json", {"engine_sha256": X, "sealed_files_sha256": sha(sealed)})
    plan = json.loads((kit.root / "plan.json").read_text())
    plan["hosts"]["h-1"]["sealed_files_sha256"] = sha(sealed)
    write(kit.root / "plan.json", plan)
    assert o.check_plan("h-1") == {"host": "h-1", "jobs": 3, "ok": True}
    plan["hosts"]["h-1"]["jobs"][0]["s3_orig"]["sha256"] = "b" * 64
    write(kit.root / "plan.json", plan)
    with pytest.raises(SystemExit, match="differs from the plan's pin"):
        o.check_plan("h-1")


def test_under_the_d2_fallback_j5_keeps_s3_safe_only_and_j8_runs_the_w1_script_with_no_pools(kit, tmp_path, monkeypatch):
    fb = {"fallback": {"path": "records/d2-fallback.json", "sha256": "e" * 64}}

    def jobs(r):
        out = DIAG(r)
        s3 = sha(tmp_path / "pod" / INPUT_FILES["pool:s3_safe"])
        out[1]["d2"], out[2]["d2"] = {**fb, "pools": {"s3_safe": s3}}, {**fb, "pools": {}}
        return out
    pod, out = dry_run(kit, tmp_path, jobs, "X", monkeypatch)
    cmds = {j["index"]: j["commands"] for j in out["jobs"]}
    sealed = json.loads((pod.root / "sealed-files.json").read_text())["files"]
    s3 = f"{INPUT_FILES['pool:s3_safe']}:{sealed[INPUT_FILES['pool:s3_safe']]}"
    py, anchors = "venv/bin/python", INPUT_FILES["anchor_bank"]
    assert cmds[1] == [["job-1-representation", [py, "scripts/stage1/representation_pass.py", "--prepared", P,
                                                 "--recipe", S, "--anchors", anchors, "--pool", s3,
                                                 "--out", "job-1/representation"]],
                       ["job-1-representation-s3-orig", [py, "scripts/stage1/representation_pass.py", "--prepared",
                                                         P, "--recipe", S, "--anchors", anchors, "--pool",
                                                         "@pathsha:job-0/untuned/s3_orig.pool.json", "--pools-only",
                                                         "--out", "job-1/representation-s3-orig"]]]
    assert cmds[2] == [["job-2-classifier", [py, "scripts/stage1/score_classifier.py", "--prepared", P, "--recipe", S,
                                             "--anchors", anchors, "--out", "job-2/classifier"]]]
    h = pod.plan["hosts"]["h-1"]
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    paths = pod.runner.sealed_paths(h["jobs"][2], h, 2, doc)
    assert not any("d2_pool_pins" in p or "pool-plant" in p for p in paths)          # no D-2 file under the fallback
    argvs = [[v.replace("@", "AT-") for v in c[1][2:]] for j in (1, 2) for c in cmds[j]]
    assert all(r["ok"] for r in parse_with(REPO, "scripts.stage1.representation_pass", argvs[:2]))
    assert parse_with(REPO, "scripts.stage1.score_classifier", argvs[2:])[0]["ok"]


@pytest.mark.parametrize("case, match", [("pins file", "packed d2_pool_pins differs"),
                                         ("req8 record", "packed req8_record differs"),
                                         ("plant pool", "packed plant pool differs"),
                                         ("s3_safe pool", "packed s3_safe pool differs"),
                                         ("no d2 entry", "no D-2 pins"), ("no j6", "no untuned_answers job")])
def test_a_j5_or_j8_whose_packed_files_differ_from_the_plans_pins_is_unrunnable(kit, tmp_path, monkeypatch, case, match):
    def jobs(r):
        out = DIAG(r) if case != "no j6" else [job(r, "rep_pass")]
        return out
    pod = Pod(kit, tmp_path, monkeypatch, jobs)
    h = pod.plan["hosts"]["h-1"]
    index = 0 if case == "no j6" else 1
    d2 = h["jobs"][index]["d2"]
    if case == "pins file":
        d2["pool_pins"]["sha256"] = "0" * 64
    elif case == "req8 record":
        d2["req8_record"]["sha256"] = "0" * 64
    elif case == "plant pool":
        d2["pools"]["plant"] = "0" * 64
    elif case == "s3_safe pool":
        d2["pools"]["s3_safe"] = "0" * 64
    elif case == "no d2 entry":
        del h["jobs"][index]["d2"]
    with pytest.raises(pod.runner.Unrunnable, match=match):
        pod.runner.job_commands(pod.plan, "h-1", index, pod.root, {})


@pytest.mark.parametrize("tamper", [rel for rel in ("scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py",
                                                    "scripts/stage1_s1/d2_pool_pins/fill_pins.py",
                                                    ".ai/inputs/stage1-commitments-20261016/MANIFEST.json",
                                                    "inputs/d2_pool_pins/representation_pools.filled.json",
                                                    "inputs/req8_record/plant_record.json",
                                                    "inputs/pool-decoy/decoy.json")])
def test_every_d2_file_of_j5_is_checked_before_it_runs(kit, tmp_path, monkeypatch, tamper):
    pod = Pod(kit, tmp_path, monkeypatch, DIAG)
    h = pod.plan["hosts"]["h-1"]
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    assert pod.runner.sealed_check(h["jobs"][1], doc["files"], pod.root, h, 1, doc) == []
    write(pod.root / tamper, "changed after sealing\n")
    assert tamper in pod.runner.sealed_check(h["jobs"][1], doc["files"], pod.root, h, 1, doc)


def test_the_d2_commands_parse_with_the_wrappers_own_parsers_in_this_repository(kit, tmp_path, monkeypatch):
    _, out = dry_run(kit, tmp_path, DIAG, "X", monkeypatch)
    cmds = {j["index"]: j["commands"] for j in out["jobs"]}
    rep = [[v.replace("@", "AT-") for v in c[1][2:]] for c in cmds[1]]
    res = parse_with(REPO, "scripts.stage1_s1.d2_pool_pins.d2_representation_pass", rep)
    assert all(r["ok"] for r in res) and res[1]["ns"]["pools_only"] is True
    assert res[0]["ns"]["pool_pins"].startswith(INPUT_FILES["d2_pool_pins"] + ":")
    cls = parse_with(REPO, "scripts.stage1_s1.d2_pool_pins.d2_score_classifier", [cmds[2][0][1][2:]])[0]
    assert cls["ok"] and cls["ns"]["req8_record"].startswith(INPUT_FILES["req8_record"] + ":")


def test_c3_runs_only_with_the_plans_subsample_and_record_pins(kit, tmp_path, monkeypatch):
    pod, out = dry_run(kit, tmp_path, lambda r: [job(r, "cert_c3", engine="Y", recipe="S")], "Y", monkeypatch)
    pin = pod.plan["hosts"]["h-1"]["jobs"][0]["c3"]["subsample"]["sha256"]
    make = out["jobs"][0]["commands"][0][1]
    assert make[make.index("--bank") + 1] == f"subsample-{pin}"
    h = pod.plan["hosts"]["h-1"]
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    assert INPUT_FILES["c3_record"] in pod.runner.sealed_paths(h["jobs"][0], h, 0, doc)
    for key in ("subsample", "record"):
        bad = json.loads(json.dumps(pod.plan))
        bad["hosts"]["h-1"]["jobs"][0]["c3"][key]["sha256"] = "0" * 64
        with pytest.raises(pod.runner.Unrunnable, match="C3 pin"):
            pod.runner.job_commands(bad, "h-1", 0, pod.root, {})


def test_the_x_pack_carries_the_d2_package_man1_and_pinned_d2_inputs(kit, monkeypatch):
    repo = Repo(kit, monkeypatch)
    r = repo.rules
    filled = write(repo.repo / "tmp/d2/filled.json", {"pins": "filled"})
    req8 = write(repo.repo / "tmp/d2/plant_record.json", {"record": "req8"})
    plant, s3 = write(repo.repo / "tmp/d2/plant.pool.json", {"p": 1}), write(repo.repo / "tmp/d2/s3safe.json", {"s": 1})
    decoy = write(repo.repo / "tmp/d2/decoy.pool.json", {"d": 1})       # VR2-3: pool:decoy is packed and checked too
    spool = write(repo.repo / "tmp/d2/s_pool_record.json", {"s3_pool": {"sha256": sha(s3)},
                                                             "full_files": {"s3_safe.pool.json": sha(s3)}})
    monkeypatch.setattr(r, "D2_POOL_PINS", {"path": "tmp/d2/filled.json", "sha256": sha(filled)})
    monkeypatch.setattr(r, "D2_REQ8_RECORD", {"path": "tmp/d2/plant_record.json", "sha256": sha(req8)})
    monkeypatch.setattr(r, "D2_POOLS", {"plant": sha(plant), "decoy": sha(decoy)})
    monkeypatch.setattr(r, "S_POOL_RECORD", {"path": "tmp/d2/s_pool_record.json", "sha256": sha(spool)})
    good = [{"name": "d2_pool_pins", "path": "tmp/d2/filled.json", "sha256": sha(filled)},
            {"name": "req8_record", "path": "tmp/d2/plant_record.json", "sha256": sha(req8)},
            {"name": "pool:plant", "path": "tmp/d2/plant.pool.json", "sha256": sha(plant)},
            {"name": "pool:decoy", "path": "tmp/d2/decoy.pool.json", "sha256": sha(decoy)},
            {"name": "pool:s3_safe", "path": "tmp/d2/s3safe.json", "sha256": sha(s3)}]
    repo.pack.main(["X", *repo.inputs(extra=good)])
    doc = json.loads((kit.root / "setup/packed-stage1-X/sealed-files.json").read_text())
    for rel, pin in r.D2_CODE.items():
        assert doc["files"][rel] == pin
    assert doc["files"][r.MAN1_PATH] == r.MAN1_SHA256
    assert {n for n in doc["inputs"]} >= {"d2_pool_pins", "req8_record", "pool:plant", "pool:decoy", "pool:s3_safe"}
    shutil.rmtree(kit.root / "setup/packed-stage1-X")
    other = write(repo.repo / "tmp/d2/other.json", {"o": 1})
    for i in range(5):                                   # each D-2 input under another SHA-256 refuses
        bad = [dict(e) for e in good]
        bad[i].update(path="tmp/d2/other.json", sha256=sha(other))
        with pytest.raises(SystemExit, match="not its D-2 pin"):
            repo.pack.main(["X", *repo.inputs(extra=bad)])
        assert not (kit.root / "setup/packed-stage1-X").exists()
    # VR2-3: an S-pool record whose two s3_safe hashes disagree names no s3_safe pin, even for its s3_pool.sha256
    spool2 = write(repo.repo / "tmp/d2/s_pool_record2.json", {"s3_pool": {"sha256": sha(s3)},
                                                              "full_files": {"s3_safe.pool.json": sha(other)}})
    monkeypatch.setattr(r, "S_POOL_RECORD", {"path": "tmp/d2/s_pool_record2.json", "sha256": sha(spool2)})
    with pytest.raises(SystemExit, match="pool:s3_safe \\(not its D-2 pin\\)"):
        repo.pack.main(["X", *repo.inputs(extra=good)])
    assert not (kit.root / "setup/packed-stage1-X").exists()


def test_the_x_pack_carries_every_s1_package_file_by_its_pin(kit, monkeypatch):
    """Round 3b item 1 (VR2-5): the X pack carries every S1_CODE file (scripts/stage1_s1/__init__.py included) with
    its pin, though the lead's inputs record names none of them; the Y pack carries none."""
    repo = Repo(kit, monkeypatch)
    repo.pack.main(["X", *repo.inputs()])
    files = json.loads((kit.root / "setup/packed-stage1-X/sealed-files.json").read_text())["files"]
    for rel, pin in repo.rules.S1_CODE.items():
        assert files[rel] == pin, rel
    assert files["scripts/stage1_s1/__init__.py"] == repo.rules.S1_CODE["scripts/stage1_s1/__init__.py"]
    tree = repo.y_tree()
    repo.pack.main(["Y", "--y-tree", str(tree), *repo.inputs("Y")])
    files_y = json.loads((kit.root / "setup/packed-stage1-Y/sealed-files.json").read_text())["files"]
    assert not any(f.startswith("scripts/stage1_s1/") for f in files_y)


@pytest.mark.parametrize("rel", ["scripts/stage1_s1/__init__.py", "scripts/stage1_s1/eval_adapter.py",
                                 "scripts/stage1_s1/safe_lora.py", "scripts/stage1_s1/lean_eval_job.py",
                                 "scripts/stage1_s1/oext_eval.py", "scripts/stage1_s1/settings/eval_adapter.json",
                                 "scripts/stage1_s1/settings/lean_eval_job.json",
                                 "scripts/stage1_s1/settings/oext_eval.json",
                                 "scripts/stage1_s1/settings/safe_lora.json",
                                 "scripts/stage1_s1/oext_unit.py",                      # round 3c: the O-ext unit
                                 "scripts/stage1_s1/settings/oext_unit.json"])          # runner and its settings
def test_an_s1_package_file_whose_bytes_differ_refuses_the_pack(kit, monkeypatch, rel):
    """Round 3b item 1: one changed byte in any pinned S1 file refuses the X pack before anything is written, and the
    refusal names the file. Fix round (F2): a settings file's changed byte keeps it valid JSON with its engine pin (one
    letter of its "name" value), and the match is the bare list entry "'<rel>'", so only the pin check can refuse it
    (a '(not JSON)' or engine refusal names "'<rel> (...)'" and does not match)."""
    repo = Repo(kit, monkeypatch)
    f = repo.repo / rel
    data = f.read_bytes()
    if rel.endswith(".json"):
        i = data.index(b'"name": "') + len(b'"name": "')
        changed = data[:i] + bytes([data[i] ^ 0x01]) + data[i + 1:]
        assert json.loads(changed)["engine_x"] == X and changed != data
    else:
        changed = data[:-1] + bytes([data[-1] ^ 0x01])
    f.write_bytes(changed)
    with pytest.raises(SystemExit, match=re.escape(f"'{rel}'")):
        repo.pack.main(["X", *repo.inputs()])
    assert not (kit.root / "setup" / "packed-stage1-X").exists()


@pytest.mark.parametrize("case", ["another sha256", "an unpinned file", "the O-ext unit runner, another sha256",
                                  "its settings, another sha256", "a D-2 file at its pin", "an S1 file at its pin",
                                  "the O-ext unit runner at its pin"])
def test_a_lead_code_entry_under_the_s1_package_must_be_its_pin(kit, monkeypatch, case):
    """Round 3b item 1: a lead's code entry under scripts/stage1_s1/ must carry the kit's pin (S1_CODE or D2_CODE);
    another SHA-256 (even of a real file) or a file the kit does not pin refuses. Round 3c: the O-ext unit runner and
    its settings are S1_CODE pins, so the round-3b exception (the runner taken by the lead's hash) is gone: the
    runner or its settings at another SHA-256 refuses. Fix round (F3): an entry naming a D-2 or an S1 file with the
    kit's own pin packs."""
    repo = Repo(kit, monkeypatch)
    rel = {"another sha256": "scripts/stage1_s1/eval_adapter.py", "an unpinned file": "scripts/stage1_s1/extra.py",
           "the O-ext unit runner, another sha256": "scripts/stage1_s1/oext_unit.py",
           "its settings, another sha256": "scripts/stage1_s1/settings/oext_unit.json",
           "a D-2 file at its pin": repo.rules.D2_REP_SCRIPT,
           "an S1 file at its pin": "scripts/stage1_s1/safe_lora.py",
           "the O-ext unit runner at its pin": "scripts/stage1_s1/oext_unit.py"}[case]
    f = repo.repo / rel
    if case in ("another sha256", "the O-ext unit runner, another sha256"):
        f.write_text("# the same path, other bytes\n")
    elif case == "its settings, another sha256":
        write(f, {"name": "oext_unit, other bytes", "engine_x": X})          # valid JSON, engine X: only its pin
    elif case == "an unpinned file":
        write(f, f"# {rel} (synthetic)\n")
    code = [{"path": "scripts/stage1/limits/overrefusal_checks.py",
             "sha256": sha(repo.repo / "scripts/stage1/limits/overrefusal_checks.py")}, {"path": rel, "sha256": sha(f)}]
    if case in ("a D-2 file at its pin", "an S1 file at its pin", "the O-ext unit runner at its pin"):
        assert sha(f) == {**repo.rules.D2_CODE, **repo.rules.S1_CODE}[rel]
        repo.pack.main(["X", *repo.inputs(code=code)])
        files = json.loads((kit.root / "setup/packed-stage1-X/sealed-files.json").read_text())["files"]
        assert files[rel] == sha(f)
        return
    with pytest.raises(SystemExit, match=re.escape(f"{rel} (an S1 package file must be its stage1_rules pin at main "
                                                   "3ea5ae1)")):
        repo.pack.main(["X", *repo.inputs(code=code)])
    assert not (kit.root / "setup" / "packed-stage1-X").exists()


@pytest.mark.parametrize("where, spelled", [
    ("code", "scripts/./stage1_s1/extra.py"), ("code", "scripts//stage1_s1/extra.py"),
    ("code", "scripts/stage1_s1/./extra.py"), ("code", "scripts/./stage1_s1/settings/extra.json"),
    ("code", "scripts/stage1_s1//settings/extra.json"), ("input", "tmp/./anchors/anchor_bank.json"),
    ("input", "tmp//anchors/anchor_bank.json"), ("folder", "eval/./e1/summary.json"),
    ("folder", "eval//e1/summary.json")])
def test_a_path_not_in_normal_form_refuses_the_pack(kit, monkeypatch, where, spelled):
    """Fix round (F1, verify-pins): a path spelled with a '.' or an empty part names the same file but would pass by the
    S1-package pin rule ('scripts/stage1_s1/'), the S1-settings engine check ('scripts/stage1_s1/settings/') and a
    named input's MAN1 comparison (its path as MAN1 spells it). Each such path refuses, nothing written. The code
    cases name an unpinned file (and a settings file pinning engine Y), so that before the fix they were PACKED; the
    input cases have MAN1 list the file at another SHA-256, so that before the fix the MAN1 check was skipped."""
    repo = Repo(kit, monkeypatch)
    args, match = None, None
    if where == "code":
        plain = spelled.replace("/./", "/").replace("//", "/")
        f = write(repo.repo / plain, {"name": "extra", "engine_x": Y} if plain.endswith(".json") else "# extra\n")
        code = [{"path": "scripts/stage1/limits/overrefusal_checks.py",
                 "sha256": sha(repo.repo / "scripts/stage1/limits/overrefusal_checks.py")},
                {"path": spelled, "sha256": sha(f)}]
        args, match = repo.inputs(code=code), re.escape(f"{spelled} (code entries are scripts/ files, each path in "
                                                        "normal form)")
    else:
        summary = repo.repo / "tmp/evals/1101/eval/e1/summary.json"
        anchor = {"name": "anchor_bank", "path": "tmp/anchors/anchor_bank.json", "sha256": sha(repo.anchor)}
        folder = {"name": "gate_a_eval:1101", "path": "tmp/evals/1101",
                  "files": [{"path": "eval/e1/summary.json", "sha256": sha(summary)}]}
        if where == "input":
            repo.man1[-1] = {**repo.man1[-1], "sha256": "0" * 64}       # MAN1 lists the anchor bank at another hash
            anchor["path"] = spelled
            match = re.escape("input anchor_bank (path, in normal form)")
        else:
            repo.man1.append({"path": "tmp/evals/1101/eval/e1/summary.json", "sha256": "0" * 64,
                              "role": "pinned input"})
            folder["files"][0]["path"] = spelled
            match = re.escape("input gate_a_eval:1101 (a file path, in normal form)")
        repo.write_man1()
        args = repo.inputs(inputs=[anchor, folder])
    with pytest.raises(SystemExit, match=match):
        repo.pack.main(["X", *args])
    assert not (kit.root / "setup" / "packed-stage1-X").exists()


def test_every_s1_package_file_the_runner_uses_is_pinned():
    """Round 3b item 1: every scripts/stage1_s1/ path the job runner checks or runs is one of the kit's pins (S1_CODE,
    D2_CODE); round 3c: the O-ext unit runner and its settings too, with no exception left."""
    sys.path.insert(0, str(KIT))
    try:
        for name in ("stage1_rules",):
            sys.modules.pop(name, None)
        import stage1_rules as r
        spec = importlib.util.spec_from_file_location("jr_pins", KIT / "setup" / "job_runner_stage1.py")
        jr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(jr)
        used = {p for paths in jr.SCRIPTS.values() for p in paths} | {p for paths in jr.D2_SCRIPTS.values() for p in paths}
        used |= {jr.OEXT_MODULE, "scripts/stage1_s1/settings/oext_eval.json", jr.B10_SCRIPT, jr.B11_SCRIPT,
                 jr.B17_SCRIPT, jr.OEXT_UNIT_SCRIPT, jr.OEXT_UNIT_SETTINGS, "scripts/stage1_s1/__init__.py"}
        s1 = {p for p in used if p.startswith("scripts/stage1_s1/")}
        assert s1 - set(r.S1_CODE) - set(r.D2_CODE) == set() and not hasattr(r, "S1_UNPINNED")
        assert {jr.OEXT_UNIT_SCRIPT, jr.OEXT_UNIT_SETTINGS} <= set(r.S1_CODE)
        assert set(r.S1_CODE) <= s1                                  # nothing pinned that the kit never uses
    finally:
        sys.path.remove(str(KIT))
        sys.modules.pop("stage1_rules", None)


def test_a_y_tree_with_another_identity_refuses_even_when_yhash_passes(kit, monkeypatch):
    """Item 7 (addendum §23): Y is pinned at 34bfd288; a tree whose code identity differs refuses right after YHASH."""
    repo = Repo(kit, monkeypatch)
    tree = repo.y_tree()
    repo.identity["Y"] = "c641c84b" + "0" * 56                          # the F5 build's identity, not adopted
    with pytest.raises(SystemExit, match="34bfd288"):
        repo.pack.main(["Y", "--y-tree", str(tree), *repo.inputs("Y")])
    assert not (kit.root / "setup" / "packed-stage1-Y").exists()
    repo.identity["Y"] = Y
    repo.pack.main(["Y", "--y-tree", str(tree), *repo.inputs("Y")])
    files = json.loads((kit.root / "setup/packed-stage1-Y/sealed-files.json").read_text())["files"]
    assert not any(f.startswith("scripts/stage1_s1/d2_pool_pins/") for f in files)    # D-2 runs on X only


def test_the_default_y_tree_passes_yhash_and_is_34bfd288():
    """Item 4: the tests find engine Y through STAGE1_ENGINE_Y_TREE, default <repo>/tmp/engine-y-34bfd288; that tree
    passes YHASH (every listed file by its SHA-256) and its code identity is engine Y's pin."""
    assert WS_Y.is_dir()
    listed = (REPO / "backups/2026-10-22/engine-round-y-34bfd288.sha256")
    assert sha(listed) == "9baa5c79a7227b60c5276070144a858695a588d497163b7f92638f04c7435dca"
    rows = [line.split("  ", 1) for line in listed.read_text().splitlines() if line.strip()]
    assert rows and all(sha(WS_Y / rel) == digest for digest, rel in rows)
    done = REAL_RUN([PY, "-B", "-c", "from experiments.safety_selection.common import code_identity;"
                     "print(code_identity()['sha256'])"], cwd=WS_Y, capture_output=True, text=True, timeout=120,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0 and done.stdout.strip() == Y


def test_no_kit_file_or_test_names_another_workspace_or_worktree():
    """Item 4: no path to a ws-* folder or to the lead's worktree in kit code or tests."""
    import re
    words = ["(?<![\\w-])" + "ws" + "-[a-z0-9]", "claude" + "-workspaces", "work" + "trees/", "kind" + "-hawking"]
    bad = re.compile("|".join(words))                    # built from parts, so this file holds none of them
    for f in sorted(KIT.rglob("*")):
        if f.is_file() and f.suffix in {".py", ".sh", ".md", ".txt", ".json"} and "__pycache__" not in f.parts:
            hits = [m.group(0) for m in bad.finditer(f.read_text())]
            assert not hits, (f.name, hits[:3])



@pytest.mark.parametrize("route", ["d2", "fallback"])
def test_one_changed_byte_in_any_file_j5_or_j8_uses_is_named_on_both_routes(kit, tmp_path, monkeypatch, route):
    """VR2-2 (ported from notes/b15r2-verify-runner-evidence/test_vr2_exp.py::test_e2): one flipped bit in each path
    sealed_paths lists for J5 and J8 is named by sealed_check. J8's list holds d2_representation_pass.py (its wrapper
    imports it); under the D-2 fallback J5's list holds pool:s3_safe and no D-2 file."""
    def jobs(r):
        out = DIAG(r)
        if route == "fallback":
            fb = {"fallback": {"path": "records/d2-fallback.json", "sha256": "e" * 64}}
            s3 = sha(tmp_path / "pod" / INPUT_FILES["pool:s3_safe"])
            out[1]["d2"], out[2]["d2"] = {**fb, "pools": {"s3_safe": s3}}, {**fb, "pools": {}}
        return out
    pod = Pod(kit, tmp_path, monkeypatch, jobs)
    h = pod.plan["hosts"]["h-1"]
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    listed = {}
    for index in (1, 2):
        paths = pod.runner.sealed_paths(h["jobs"][index], h, index, doc)
        assert pod.runner.sealed_check(h["jobs"][index], doc["files"], pod.root, h, index, doc) == []
        for rel in paths:
            f = pod.root / rel
            data = f.read_bytes()
            f.write_bytes(bytes([data[0] ^ 0x01]) + data[1:])
            bad = pod.runner.sealed_check(h["jobs"][index], doc["files"], pod.root, h, index, doc)
            f.write_bytes(data)
            assert rel in bad, (index, rel, bad)
        listed[index] = paths
    if route == "d2":
        assert pod.rules.D2_REP_SCRIPT in listed[2] and pod.rules.D2_CLASSIFIER_SCRIPT in listed[2]
        for n in ("plant", "decoy", "s3_safe"):
            assert INPUT_FILES[f"pool:{n}"] in listed[1]
        assert INPUT_FILES["pool:s3_safe"] not in listed[2]
    else:
        assert INPUT_FILES["pool:s3_safe"] in listed[1]
        assert not any("d2_pool_pins" in p or p in pod.rules.D2_CODE for p in listed[1] + listed[2])


# ===== Round 3c (notes/b15r3c-build.json): the O-ext unit runner pinned, packed, sealed and parsed =================

OEXT_FILES = {"scripts/stage1_s1/oext_unit.py", "scripts/stage1_s1/settings/oext_unit.json",
              "scripts/stage1_s1/oext_eval.py", "scripts/stage1_s1/settings/oext_eval.json"}


def test_every_o_ext_steps_commands_parse_under_the_real_runners_own_parser(kit, tmp_path, monkeypatch):
    """Round 3c item 1: the O-ext steps of J3 (a regenerated a0 unit and theta0, under Branch full; the same under
    Branch 128, where the regenerated unit's pass names its packed source unit), J4 (Branch 128), J9, J10 and J18, as
    the dry run prints them, parse under the committed scripts/stage1_s1/oext_unit.py's own argparse parser (its main,
    stopped right after parse_args, in a fresh interpreter in this tree) to exactly the values the kit's contract
    parser gives. Hand values: 8 O-ext steps; the one --dev100-source is LN-19's source unit of a0 at 1101."""
    a1 = edit_ref("A1")
    specs = (("full", lambda r: [job(r, "regenerate", "a0", 1101), job(r, "o_only", "a0", 1101, regen_source=0),
                                 job(r, "o_only", "theta0"), job(r, "arm", "A1", 1102, edit=a1, recipe="S"),
                                 job(r, "a0_arm", "a0", 1104, recipe="S"), job(r, "ref_train", "G", 1102, recipe="G")]),
             ("128", lambda r: [job(r, "regenerate", "a0", 1101, branch="128"),
                                job(r, "o_only", "a0", 1101, regen_source=0, branch="128"),
                                job(r, "o_only", "theta0", branch="128"),
                                job(r, "transfer_report", "theta0", branch="128")]))
    steps = []
    for branch, jobs in specs:
        sub = tmp_path / branch
        sub.mkdir()
        _, out = dry_run(kit, sub, jobs, "X", monkeypatch, branch=branch)
        steps += [(j["kind"], [v.replace("@", "AT-") for v in argv[2:]]) for j in out["jobs"]
                  for _, argv in j["commands"] if argv[1] == "scripts/stage1_s1/oext_unit.py"]
        for name in MODULES:
            sys.modules.pop(name, None)
    assert sorted(k for k, _ in steps) == ["a0_arm", "arm", "o_only", "o_only", "o_only", "o_only", "ref_train",
                                           "transfer_report"]
    real = parse_with(WS_S1, "scripts.stage1_s1.oext_unit", [a for _, a in steps])
    runner = kit("setup/job_runner_stage1.py")
    for (kind, a), got in zip(steps, real):
        assert got["ok"], (kind, a, got)
        contract = vars(runner.oext_unit_contract().parse_args(a))
        assert got["ns"] == {k: v if isinstance(v, (str, int, float, bool, type(None))) else str(v)
                             for k, v in contract.items()}, kind
    assert sorted({g["ns"]["command"] for g in real}) == ["run", "transfer"]
    dev = [g["ns"] for g in real if g["ns"]["dev100_source"]]
    assert [(d["run"], d["dev100_source"], d["checkpoint"]) for d in dev] == [
        ("round1/1101-a0-regen-a1", "inputs/source_unit-a0-1101", "e1")]


O_EXT_STEPS = {"J3 a0": (lambda r: regen_pair(r), 1, "full"),
               "J3 theta0": (lambda r: [job(r, "o_only", "theta0")], 0, "full"),
               "J4": (lambda r: [job(r, "transfer_report", "theta0", branch="128")], 0, "128"),
               "J9": (lambda r: [job(r, "arm", "A1", 1102, edit=edit_ref("A1"), recipe="S")], 0, "full"),
               "J10": (lambda r: [job(r, "a0_arm", "a0", 1104, recipe="S")], 0, "full"),
               "J18": (lambda r: [job(r, "ref_train", "G", 1102, recipe="G")], 0, "full")}


@pytest.mark.parametrize("tamper", ["scripts/stage1_s1/settings/oext_unit.json", "scripts/stage1_s1/oext_unit.py"])
@pytest.mark.parametrize("step", sorted(O_EXT_STEPS))
def test_every_o_ext_step_seals_the_runner_and_its_settings(kit, tmp_path, monkeypatch, step, tamper):
    """Round 3c item 1: J3, J4, J9, J10 and J18 each check the runner, its settings and oext_eval's module and settings
    against sealed-files.json before the job; a changed byte in the runner or its settings stops the host at that
    job (sealed_file_mismatch), and no step of that job runs."""
    jobs, index, branch = O_EXT_STEPS[step]
    pod = Pod(kit, tmp_path, monkeypatch, jobs, branch=branch)
    h = pod.plan["hosts"]["h-1"]
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    assert OEXT_FILES <= set(pod.runner.sealed_paths(h["jobs"][index], h, index, doc))
    assert pod.runner.sealed_check(h["jobs"][index], doc["files"], pod.root, h, index, doc) == []
    write(pod.root / tamper, "changed after sealing\n")
    assert tamper in pod.runner.sealed_check(h["jobs"][index], doc["files"], pod.root, h, index, doc)
    monkeypatch.setattr(pod.runner, "preflight_checks", lambda *a: doc)       # the mid-host check, alone
    pod.remaining([30 * H])
    assert pod.main() == 1
    assert pod.done()["stopped"] == "sealed_file_mismatch" and pod.done()["jobs"][index]["sealed_mismatch"]
    assert not [n for n in pod.receipts() if n.startswith(f"job-{index}-")]


def test_the_x_pack_alone_carries_every_file_an_o_ext_step_seals(kit, monkeypatch):
    """Round 3c item 1: with no lead code entry naming the runner, the X pack carries oext_unit.py and its settings by
    their S1_CODE pins, so every script and settings file the O-ext steps of J3, J4, J9, J10 and J18 seal is in the
    packed stage at its pin (check-plan's file rule; the named inputs are the lead's --inputs), and nothing refuses an
    O-ext step as 'not built'."""
    repo = Repo(kit, monkeypatch)
    repo.pack.main(["X", *repo.inputs()])
    doc = json.loads((kit.root / "setup/packed-stage1-X/sealed-files.json").read_text())
    runner = kit("setup/job_runner_stage1.py")
    r = runner.rules
    for j in (job(r, "o_only", "a0", 1101, regen_source=0), job(r, "o_only", "theta0"),
              job(r, "transfer_report", "theta0", branch="128"), job(r, "arm", "A1", 1102, recipe="S"),
              job(r, "a0_arm", "a0", 1104, recipe="S"), job(r, "ref_train", "G", 1102, recipe="G")):
        code = [p for p in runner.sealed_paths(j, {"jobs": [j]}, 0, {"files": doc["files"], "inputs": {}})
                if p.startswith("scripts/")]
        assert set(code) == OEXT_FILES, j["kind"]
        assert all(doc["files"][p] == repo.rules.S1_CODE[p] for p in code), j["kind"]


# ===== Addendum §29 (round 29, 26 Oct): the pull list covers every unit the runner records; the finisher checks every
# stage-1 host role ===================================================================================================

GATEB_PULL = ("round1 job-* jobs anchor-* gatec cuda-preflight-* preflight-process-* preflight-outer "
              "worker-bootstrap-process-001 setup-001 BOOTSTRAP-READY.json BUNDLE-CHECKED.json pip-version.txt "
              "PREFLIGHT-DONE.json JOB-DONE.json deferral.json model-download-receipt.json environment-linux.lock")


def pulled(rel: str, items: str) -> bool:
    """host.py pull's rule, by hand: on the pod, ``cd RUN && ls -d ITEMS | tar -cf - -T -`` takes every top-level
    entry that a pattern of ITEMS matches (a shell glob), with everything under it."""
    import fnmatch
    return any(fnmatch.fnmatchcase(rel.split("/")[0], p) for p in items.split())


def pods_of_every_kind(r, which: str):
    """(engine, branch, jobs): every stage-1 job kind on four pods (one engine per pod; W1-18 alone; Branch 128 for
    theta0's LN-14 report). The X pod mirrors the job order of block A's LN-12 and diagnostics pods."""
    r1, a1 = edit_ref("R1"), edit_ref("A1")
    if which == "x":
        return "X", "full", [
            job(r, "regenerate", "a0", 1101), job(r, "o_only", "a0", 1101, regen_source=0),
            job(r, "untuned_answers"), job(r, "rep_pass"), job(r, "l1_scan"), job(r, "classifier"),
            job(r, "arm", "A1", 1102, edit=a1, recipe="S"), job(r, "a0_arm", "a0", 1104, recipe="S"),
            job(r, "ref_train", "G", 1102, recipe="G"), job(r, "c0", "R", 1101, edit=r1, recipe="S"),
            job(r, "retrain", "a0", 1102, recipe="S"), job(r, "a1_rescore", "a0", 1102, recipe="S", regen_source=10),
            job(r, "b10_certify", "a0", 1101, points=["certify", "scale:0"], recipe="B"),
            job(r, "ref_eval", "a0", 1104, points=["scale:0.9", "prefix"], recipe="B"),
            job(r, "safe_lora", "a0", 1104, points=["default"], recipe="B")]
    if which == "x128":
        return "X", "128", [job(r, "o_only", "theta0", branch="128"), job(r, "transfer_report", "theta0", branch="128")]
    if which == "w1":
        return "X", "full", [job(r, "w1_18")]
    return "Y", "full", [job(r, "cert_c1", "R", 1101, engine="Y", edit=r1, recipe="S"),
                         job(r, "cert_c2", "bqi", 1101, engine="Y", recipe="bqi"),
                         job(r, "cert_c3", engine="Y", recipe="S"),
                         job(r, "ref_train", "bqi", 1102, engine="Y", recipe="bqi")]


@pytest.mark.parametrize("which, unit_tops, outside_gateb", [
    ("x", {"round1", "rescore", "job-12", "job-13", "job-14"}, {"rescore"}),
    ("y", {"cert", "round1"}, {"cert"}),
    ("x128", set(), set()),
    ("w1", set(), set())])
def test_every_unit_and_record_path_the_runner_writes_lies_under_the_pull_list(kit, tmp_path, monkeypatch, which,
                                                                               unit_tops, outside_gateb):
    """Addendum §29 point 2 (kit gap 1): each pod runs every job to completion with the synthetic engine; every path
    it writes (units, outputs, job files, ledgers, job-done/ and JOB-DONE.json), every step's receipt folder and
    every unit and output path JOB-DONE.json records lies under host.py's PULL_ITEMS (the runner's empty round1/,
    jobs/, cert/ and rescore/ folders, made on every pod, too). By hand: the units lie under
    round1/, rescore/ (LN-15e) and cert/ (C1-C3) and B10's under job-I/. The other way: Gate B's old list, which the
    stage-1 kit used until this round, leaves out exactly the rescore/ and cert/ paths (a-2's jobs 12-15)."""
    host = kit("host.py")
    engine, branch = {"x": ("X", "full"), "x128": ("X", "128"), "w1": ("X", "full"), "y": ("Y", "full")}[which]
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: pods_of_every_kind(r, which)[2], engine=engine, branch=branch)
    assert pods_of_every_kind(pod.rules, which)[:2] == (engine, branch)
    before = {str(p.relative_to(pod.root)) for p in pod.root.rglob("*") if p.is_file()}
    pod.remaining([1000 * H])
    assert pod.main() == 0 and set(pod.statuses()) == {"complete"}
    done = pod.done()["jobs"]
    written = {str(p.relative_to(pod.root)) for p in pod.root.rglob("*") if p.is_file()} - before   # every file
    units = {u for d in done for u in [d.get("unit")] + [x["unit"] for x in d.get("units") or []] if u}
    recorded = units | {rel for d in done for rel in d.get("outputs") or {}}
    paths = written | recorded | set(pod.receipts())
    assert "JOB-DONE.json" in written and "job-done/JOB-0.json" in written and recorded <= paths
    assert {u.split("/")[0] for u in units} == unit_tops
    assert [p for p in sorted(paths) if not pulled(p, host.PULL_ITEMS)] == []
    assert {p.split("/")[0] for p in paths if not pulled(p, GATEB_PULL)} == outside_gateb
    runner = pod.runner
    for folder in (runner.ROUND, "jobs", runner.CERT_ROOT, runner.RESCORE_ROOT, "job-done", "JOB-DONE.json",
                   "deferral.json", "job-0", "job-12-attributes"):
        assert pulled(folder, host.PULL_ITEMS), folder
    assert not pulled("elsewhere/1102-a0-retrain-a1/COMPLETE.json", host.PULL_ITEMS)    # the check can fail


def _finisher_tree(kit, role: str):
    fin = kit("finisher.py")
    write(kit.root / "plan.json", {"hosts": {"h-1": {"role": role, "cap_hours": 7.0}}})
    tree = kit.root / "retrieved" / "h-1" / "tree"
    unit = tree / "round1" / "1102-edit-x-e1-a1"
    listed = write(unit / "eval" / "e1" / "summary.json", {"u": SENTINELS[0]})
    write(unit / "COMPLETE.json", {"files": {"eval/e1/summary.json": sha(listed),
                                             "states/e1/adapter.safetensors": "0" * 64}})
    write(tree / "JOB-DONE.json", {"host": "h-1", "ok": True, "jobs": []})
    (kit.root / "hosts" / "h-1").mkdir(parents=True)
    return fin, tree, listed


def _finish(fin, kit, monkeypatch, tree, exit_code=0) -> tuple[str, list]:
    calls = []
    monkeypatch.setattr(fin, "tool", lambda *a: calls.append(a) or subprocess.CompletedProcess(a, 0, "stopped", ""))
    monkeypatch.setattr(fin, "unpack", lambda h: tree)
    monkeypatch.setattr(fin, "log", lambda **f: None)
    (kit.root / "hosts" / "h-1" / "finished.json").unlink(missing_ok=True)
    fin.finish("h-1", {"exit_code": exit_code})
    return json.loads((kit.root / "hosts" / "h-1" / "finished.json").read_text())["status"], calls


@pytest.mark.parametrize("role", ["w1_18", "cert", "certify", "job", "diagnostics", "arms", "a-role-of-no-list"])
def test_the_finisher_light_checks_every_stage_1_host_role(kit, monkeypatch, role):
    """Addendum §29 point 4 (kit gap 3): the finisher light-checks the pulled tree of every host, whatever its role
    (the six roles plan_tool gives stage-1 hosts: w1_18, cert, certify, job, diagnostics, arms; and any other, so no
    host is passed unchecked), not only Gate B's "job", "first" and "anchor". A good tree is verified-and-stopped with
    its check in verified.jsonl (the model state left on the pod is counted, not checked); the other ways: a listed
    file that differs, a JOB-DONE.json that is not ok, or a non-zero outer exit is review-needed-stopped. The pod is
    stopped in every case."""
    fin, tree, listed = _finisher_tree(kit, role)
    status, calls = _finish(fin, kit, monkeypatch, tree)
    assert status == "verified-and-stopped" and calls[-2:] == [("extend-cap", "h-1", "120"), ("stop", "h-1")]
    check = json.loads((kit.root / "retrieved" / "h-1" / "verified.jsonl").read_text().splitlines()[-1])
    assert check["results"] == {"round1/1102-edit-x-e1-a1": {"exit": 0, "tail": "bad []; states left on the pod: 1"}}
    assert _finish(fin, kit, monkeypatch, tree, exit_code=1)[0] == "review-needed-stopped"
    write(tree / "JOB-DONE.json", {"host": "h-1", "ok": False, "jobs": []})
    assert _finish(fin, kit, monkeypatch, tree)[0] == "review-needed-stopped"
    write(tree / "JOB-DONE.json", {"host": "h-1", "ok": True, "jobs": []})
    listed.write_text("changed after the pod wrote it\n")
    status, calls = _finish(fin, kit, monkeypatch, tree)
    assert status == "review-needed-stopped" and calls[-2:] == [("extend-cap", "h-1", "120"), ("stop", "h-1")]


def test_the_backup_lists_jobs_complete_not_pulled_and_leaves_c0s_states_aside(kit, capsys):
    """Addendum §29 point 3, the backup side (a-2's shape): a retrain and its re-score recorded complete (not pulled)
    under the lead's decision (pulled false, the decision's SHA-256) are listed with that mark and not required (their
    units are only on the pod's volume); c0's recorded .safetensors outputs, which the light pull leaves on the pod, are
    not required (model weights aside, as for a unit). The other ways: a pulled-false mark without the decision's
    SHA-256, or a missing c0 output that is not a model state, is a missing record (exit 2)."""
    backup = kit("backup_records_stage1.py")
    r = backup.rules
    k = kit.root
    tree = k / "retrieved" / "a-2" / "tree"
    jobs = [job(r, "retrain", "a0", 1102, recipe="S"), job(r, "a1_rescore", "a0", 1102, recipe="S", regen_source=0),
            job(r, "c0", "R", 1101, edit=edit_ref("R1"), recipe="S")]
    decision = "d" * 64
    for i, unit in ((0, "rescore/1102-a0-retrain-a1"), (1, "rescore/1102-attributes-a1")):
        jobs[i].update(status="complete", unit=unit, complete_sha256=hashlib.sha256(unit.encode()).hexdigest(),
                       pulled=False, unpulled_decision_sha256=decision,
                       outputs={f"job-{i}/cost-ledger.json": sha(write(tree / f"job-{i}" / "cost-ledger.json", {"i": i}))})
    record = write(tree / "job-2" / "c0" / "c0_record.json", {"o": SENTINELS[3]})
    jobs[2].update(status="complete", unit=None, complete_sha256=None, states_on_pod=1, outputs={
        "job-2/c0/c0_record.json": sha(record), "job-2/c0/train/states/e1/adapter.safetensors": "e" * 64})
    write(tree / "JOB-DONE.json", {"host": "a-2", "jobs": []})
    prep = kit.repo / "tmp/kt-prepared/prepared-kt-dolly-olmo2"
    write(prep / "manifest.json", {"m": 1})
    write(prep / "manifest.sha256", sha(prep / "manifest.json") + "\n")
    plan = {"name": "stage1-olmo", "hosts": {"a-2": host_record(r, jobs)}, "seals": {},
            "prepared": {"prepared-kt-dolly-olmo2": sha(prep / "manifest.json")}}
    write(k / "plan.json", plan)
    for name in ("budget-checks.jsonl", "operator-actions.jsonl", "hosts-full-a-2.log", "launch.log", "finisher.log"):
        write(k / name, "{}\n")
    write(k / "hosts" / "a-2" / "finished.json", {"ok": True})
    write(k / "edits" / "x.edit.json", EDITS["R1"])
    plan["hosts"]["a-2"]["jobs"][2]["edit"] = {"path": "runkit/stage1-olmo/edits/x.edit.json",
                                              "sha256": edit_ref("R1")["sha256"]}
    write(k / "plan.json", plan)
    sel = backup.select(plan, ["a-2"], 50 * 1024 * 1024)
    assert sel["missing"] == []
    assert [(j["index"], j.get("pulled"), j.get("unpulled_decision_sha256")) for j in sel["jobs"]["a-2"]] == [
        (0, False, decision), (1, False, decision), (2, None, None)]
    assert backup.main(["--dry-run", "--tag", "backup-2026-10-26-stage1-a"]) == 0
    capsys.readouterr()
    plan["hosts"]["a-2"]["jobs"][0].pop("unpulled_decision_sha256")
    record.unlink()
    write(k / "plan.json", plan)
    sel = backup.select(plan, ["a-2"], 50 * 1024 * 1024)
    assert sel["missing"] == ["a-2: job 0 is complete in plan.json but its unit is not sealed in the pulled tree",
                              "a-2: job 2: 1 recorded output(s) not staged or changed"]
    assert backup.main(["--dry-run", "--tag", "backup-2026-10-26-stage1-a"]) == 2
