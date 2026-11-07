"""The 7-8B kit's job runner (K2 of T4): the arm and a0_arm jobs under the family's main config with the plan's edit
file; the engine identity on the pod; the in-pod speed check s_obs after each arm (KD11); the free-space check before
each job (KD5); the job decision with the preflight's two documents (KCR test 12 on fake files); the evaluation bank
for check_keys; SR-2 (no U value and no answer text in any record or printed line, walked); the retrain kind's
refusal while RECIPE_S is null (A1); the dry run that computes s and defers the right job; the preflight's speed and
bank fields; states_tool.py and the finisher's states pull (KD5); the backup's states group; the seal of block 0.
On CPU, no pod, no network; every input is synthetic (the World of tests/test_stage1_runkit.py plus a synthetic pod
folder with a fake engine); a fake token is built at run time. Expected values are written by hand.

    PYTHONDONTWRITEBYTECODE=1 PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests/test_kit_78b_runner.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

import test_stage1_runkit as rk
from test_stage1_runkit import w, wf  # noqa: F401 - the 7-8B World fixtures (one family; both families)

KIT = rk.KIT
ROOT = KIT.parents[1]
X = rk.X
PY = sys.executable
REAL_RUN = subprocess.run             # the Pod's fake replaces subprocess.run; the tests' own children use this
H = 3600.0
SENTINELS = ("0.7319284756", "SENTINEL-U-VALUE", "SENTINEL-ANSWER-TEXT the model wrote this", rk.SENTINEL)
MS_FULL = {"olmo2-7b": 236.11, "llama31-8b": 100.0}         # below the divisors 269.03 / 104.32 ms: s_pod = 1
TRAINING_S = {"olmo2-7b": 952.03, "llama31-8b": 1100.0}     # below the divisors 1,202.05 / 1,261.79 s
UNTUNED_S = 2337.436
GPU = "NVIDIA A100-SXM4-80GB"
DEV = {"arc_generation": 96, "arc_utility": 189, "harm": 200, "overrefusal": 100, "safety": 72}   # both prepared sets (M)


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(obj if isinstance(obj, str) else json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return path


def load_by_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_preflight_done(family: str, **changes) -> dict:
    """A PREFLIGHT-DONE.json with the keys the 17 measured files hold (none holds untuned_projected_s), plus K2's."""
    doc = {"utc": "2026-11-20T10:00:00+00:00", "ok": True, "folder": "cuda-preflight-1", "cap_remaining_s": 43472.86,
           "generation_batch": 32, "init_equals_untuned": True, "ms_per_step_full": MS_FULL[family], "overhead_s": 1000,
           "projected_job_upper_s": 41077.72, "training_s": TRAINING_S[family], "verification_sha256": None,
           "tried": [{"exit": 0, "folder": "cuda-preflight-1"}], "family": family}
    doc.update(changes)
    return {k: v for k, v in doc.items() if v is not ...}


def fake_verification(family: str, recipe_sha256: str, manifest_sha256: str, **changes) -> dict:
    """The preflight's verification.json: the blocks the runner reads (cap_projection, full_length, the two bank_units,
    environment.cuda.name, manifest_sha256, recipe_sha256). ``cp_X`` changes cap_projection.X; ``...`` drops a key."""
    cp = {"batches_capped": 34, "e1_upper_s": 16695.63, "margin_s": 900, "overhead_measured_s": 14.1, "overhead_s": 1000,
          "projected_job_upper_s": 36243.29, "training_s": TRAINING_S[family], "untuned_projected_s": UNTUNED_S,
          "untuned_upper_s": 16695.63}
    stages = {"generate": {"bank_units": 468, "projected_seconds": 981.0}, "sample": {"bank_units": 600},
              "guard": {"bank_units": 468}, "guard_samples": {"bank_units": 600}, "harm_scores": {"bank_units": 800},
              "arc_utility": {"bank_units": 189}}
    doc = {"kind": "cuda preflight verification (synthetic)", "cap_projection": cp, "generation_batch": 32,
           "generation_memory_ok": True,
           "full_length": {"batch": 32, "max_new_tokens": 2048, "ms_per_step_full": MS_FULL[family], "rows_capped": 32},
           "evaluation_timing": {"harm_capped": 0, "projection_to_dev_bank": {"stages": stages}},
           "environment": {"cuda": {"name": GPU, "capability": "8.0"}, "device": "cuda"},
           "manifest_sha256": manifest_sha256, "recipe_sha256": recipe_sha256, "training_identity": "0" * 64,
           "verdict": {"use_this_recipe": True, "init_equals_untuned": True, "generation_memory_ok": True}}
    for key, value in changes.items():
        if key.startswith("cp_"):
            if value is ...:
                cp.pop(key[3:], None)
            else:
                cp[key[3:]] = value
        elif key == "sample_units":
            stages["sample"]["bank_units"] = value
        elif key == "generate_units":
            stages["generate"]["bank_units"] = value
        elif key == "gpu":
            doc["environment"]["cuda"]["name"] = value
        elif value is ...:
            doc.pop(key, None)
        else:
            doc[key] = value
    return doc


HF_PATH_VARS = ("HF_HOME", "XDG_CACHE_HOME", "HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "HF_TOKEN_PATH")


class Pod:
    """A synthetic pod folder for job_runner_stage1.main from a World (tests/test_stage1_runkit.py): K1's block-0 plan
    (init-block 0, the real route) or hand-given job records; the recipe, the prepared manifest files and the edit
    files sealed in sealed-files.json; the preflight's two documents; a fake engine (``run``) that writes what a
    calibrate step writes, with the SENTINELS in the outcome files (U in eval/e1/summary.json, answer text in
    generations/, the edit's trap text in the packed edit file) and a progress.jsonl whose capped 32-row batches take
    ``batch_s`` seconds (per arm when a list)."""

    def __init__(self, w, monkeypatch, jobs=None, pre_change=None, ver_change=None, batch_s=200.0, free_gb=40.0,
                 progress_change=None, recipe_change=None, manifest_change=None):
        self.w, self.mp = w, monkeypatch
        r, r78, family = w.rules, w.r78, w.family
        self.rules, self.r78, self.family = r, r78, family
        self.runner = load_by_path("jr78_runner", w.root / "setup" / "job_runner_stage1.py")
        assert self.runner.rules is r and self.runner.r78 is r78           # the World's modules, so patches hold
        w.init(amount=56.06)                                              # K1's block-0 plan, the real route
        plan = w.plan()
        self.host = list(plan["hosts"])[0]
        h = plan["hosts"][self.host]
        if jobs is not None:
            h["jobs"] = jobs
        root = self.root = w.repo / "pod"
        root.mkdir()
        # the recipe file at REC (synthetic bytes with the generation block the bank is built from), pinned
        recipe = {"name": Path(r.REC).stem, "synthetic": True, "model": {"attn_implementation": "sdpa"},
                  "generation": {"max_new_tokens": 2048, "batch_size": 32, "decoding": "greedy",
                                 "harm_samples": {"count": 3, "temperature": 0.7}}}
        if recipe_change:
            recipe_change(recipe)
        write(root / r.REC, recipe)
        monkeypatch.setitem(r.RECIPE_PINS, r.REC, sha(root / r.REC))
        # the prepared set's manifest files (counts only) and the pins
        self.prepared = f"data/kt-prepared/{r.PREPARED_NAME}"
        manifest = {"kind": "prepared manifest (synthetic)", "banks": {"dev": dict(DEV)}}
        if manifest_change:
            manifest_change(manifest)
        write(root / self.prepared / "manifest.json", manifest)
        self.digest = sha(root / self.prepared / "manifest.json")
        write(root / self.prepared / "manifest.sha256", self.digest + "\n")
        monkeypatch.setitem(r78.MANIFESTS, family, self.digest)
        monkeypatch.setitem(r.PREPARED_MANIFESTS, r.PREPARED_NAME, self.digest)
        plan["prepared"] = {r.PREPARED_NAME: self.digest}
        # the sealed files: the edit files (from the World's synthetic sealed set), the recipe, the manifest files
        sealed = {r.REC: sha(root / r.REC), f"{self.prepared}/manifest.json": self.digest,
                  f"{self.prepared}/manifest.sha256": sha(root / self.prepared / "manifest.sha256")}
        for job in h["jobs"]:
            if job.get("edit"):
                rel = f"edits/{job['edit']['sha256']}.edit.json"
                shutil.copy(w.repo / job["edit"]["path"], write(root / rel, ""))
                sealed[rel] = sha(root / rel)
                assert sealed[rel] == job["edit"]["sha256"]
        write(root / "sealed-files.json", {"kind": "stage1-78b sealed files", "version": 1, "engine": "X",
                                          "family": family, "files": sealed, "inputs": {}})
        h["sealed_files_sha256"] = sha(root / "sealed-files.json")
        self.plan = plan
        write(root / "plan.json", plan)
        write(root / "BOOTSTRAP-READY.json", {"ok": True, "gpu": GPU})
        # the preflight's two documents
        self.ver = fake_verification(family, r.REC_CONFIG_SHA256, self.digest, **(ver_change or {}))
        write(root / "cuda-preflight-1" / "verification.json", self.ver)
        self.pre = fake_preflight_done(family, recipe=r.REC,
                                       verification_sha256=sha(root / "cuda-preflight-1" / "verification.json"),
                                       **(pre_change or {}))
        write(root / "PREFLIGHT-DONE.json", self.pre)
        write(root / "process_receipt.py", "# a placeholder: the fake run never executes it\n")
        # the runner's environment
        monkeypatch.setattr(self.runner, "ROOT", root)
        monkeypatch.setattr(self.runner, "_engine_identity", lambda: X)
        monkeypatch.setattr(self.runner, "_recipe_config_sha", lambda path: r.REC_CONFIG_SHA256)
        monkeypatch.setattr(self.runner, "HEARTBEAT", w.repo / "heartbeat.json")
        monkeypatch.setenv("HOME", str(w.repo))
        for name in self.runner.TOKEN_ENV_NAMES + HF_PATH_VARS:      # RV2-8: the library's path variables too
            monkeypatch.delenv(name, raising=False)
        self.free([free_gb] if not isinstance(free_gb, list) else free_gb)
        self.batch_s = batch_s if isinstance(batch_s, list) else [batch_s] * 8
        self.progress_change = progress_change
        self.ran, self.fail, self.e1_fp, self.state_fp, self.calibrated = [], {}, "5" * 64, None, 0
        monkeypatch.setattr(self.runner.subprocess, "run", self.run)

    def remaining(self, values):
        values = list(values)
        self.mp.setattr(self.runner, "remaining", lambda now: values.pop(0) if len(values) > 1 else values[0])

    def free(self, values):
        values = list(values)
        self.mp.setattr(self.runner, "free_space_gb", lambda path: values.pop(0) if len(values) > 1 else values[0])

    def progress_rows(self, n_arm: int) -> list[dict]:
        """A greedy series of 15 capped 32-row batches (the first 300 s, excluded by the rule) then a 20-row last
        batch, then a sampled series of 19 batches: kind, batch, elapsed_s, rows, capped, output_tokens."""
        rows, elapsed = [], 50.0
        seconds = self.batch_s[min(n_arm, len(self.batch_s) - 1)]
        for b in range(16):
            elapsed += 300.0 if b == 0 else seconds if b < 15 else 60.0
            rows.append({"kind": "generate", "checkpoint": "e1", "batch": b, "elapsed_s": round(elapsed, 3),
                         "rows": 32 if b < 15 else 20, "capped": 3, "output_tokens": 40000})
        for b in range(19):
            elapsed += 100.0
            rows.append({"kind": "generate", "checkpoint": "e1", "batch": b, "elapsed_s": round(elapsed, 3),
                         "rows": 32 if b < 18 else 24, "capped": 1, "output_tokens": 30000})
        if self.progress_change:
            rows = self.progress_change(rows)
        return rows

    def run(self, args, **kwargs):
        self.ran.append(list(args))
        root = self.root
        if args[:2] != ["python3", "process_receipt.py"]:
            return subprocess.CompletedProcess(args, 0, "verify ok (synthetic)\n", "")
        name, argv = args[3], args[5:]
        code = self.fail.get(name, 0)
        if code:
            return subprocess.CompletedProcess(args, code, "", "")
        if "calibrate" in argv:
            arm, seed = argv[argv.index("--arms") + 1], argv[argv.index("--seeds") + 1]
            unit = root / "round1" / f"{seed}-{arm}-e1-a1"
            write(unit / "eval" / "e1" / "summary.json", {"u": float(SENTINELS[0]), "label": SENTINELS[1]})
            write(unit / "generations" / "e1" / "answers.jsonl", json.dumps({"prompt_id": "dev-1", "answer": SENTINELS[2]}) + "\n")
            write(unit / "states" / "e1" / "state.json", {"adapter_fingerprint": self.state_fp or self.e1_fp})
            write(unit / "states" / "e1" / "adapter.safetensors", "w" * 64)
            progress = write(unit / "progress.jsonl", "".join(json.dumps(x) + "\n" for x in self.progress_rows(self.calibrated)))
            self.calibrated += 1
            if progress.read_text() == "":
                progress.unlink()
            files = {"eval/e1/summary.json": sha(unit / "eval" / "e1" / "summary.json"),
                     "states/e1/state.json": sha(unit / "states" / "e1" / "state.json"),
                     "states/e1/adapter.safetensors": sha(unit / "states" / "e1" / "adapter.safetensors"),
                     "progress.jsonl": sha(progress) if progress.exists() else None}
            write(unit / "COMPLETE.json", {"complete": True, "files": {k: v for k, v in files.items() if v},
                                           "identity": {"manifest_sha256": self.digest,
                                                        "training_identity": self.rules.TRAINING_IDENTITY},
                                           "checkpoints": {"e1": {"adapter_fingerprint": self.e1_fp}},
                                           "evaluation": {"e1": {"u": float(SENTINELS[0])}}})
        return subprocess.CompletedProcess(args, 0, "", "")

    def main(self) -> int:
        return self.runner.main([self.host])

    def done(self) -> dict:
        return json.loads((self.root / "JOB-DONE.json").read_text())

    def statuses(self) -> list[str]:
        return [r["status"] for r in self.done()["jobs"]]

    def receipts(self) -> list[str]:
        return [a[3] for a in self.ran if a[:2] == ["python3", "process_receipt.py"]]

    def texts(self) -> list[str]:
        """Every record the runner wrote (JOB-DONE.json, job-done/*, the ledgers, the fingerprint records, deferral)."""
        out = []
        for p in [self.root / "JOB-DONE.json", self.root / "deferral.json", *(self.root / "job-done").glob("*.json"),
                  *self.root.glob("job-*/*.json")]:
            if p.is_file():
                out.append(p.read_text())
        return out


def arm_job(w, kind: str, arm: str, seed: int, edit=None, steps=None, recipe="B") -> dict:
    return w.rules.job_record(kind, arm, seed, edit, steps, recipe=recipe)


# ===== 1. the arm and a0_arm commands under the main config with the plan's edit file; the engine identity ==========
def test_the_arm_and_a0_arm_jobs_run_under_the_main_config_with_the_plans_edit_file(wf, monkeypatch, local_processes):
    """P78:99 (plan T4 step 4): every block-0 job is the engine's calibrate with the FAMILY'S main config, the edit
    arms with --edit edits/<SHA-256>.edit.json and the arm edit-<SHA-256>, a0 without; one unit per job under
    round1/<seed>-<arm>-e1-a1; the engine identity is checked on the pod (G4) and a differing one refuses before any
    job; the dry run parses with the engine's own CLI parser (the W1-18 O-ext step of the stage-1 kit is gone)."""
    w = wf
    pod = Pod(w, monkeypatch)
    r = w.rules
    jobs = pod.plan["hosts"][pod.host]["jobs"]
    expected_kinds = ["arm", "arm", "arm"] + (["a0_arm"] if w.family == "llama31-8b" else [])
    assert [j["kind"] for j in jobs] == expected_kinds and [j["seed"] for j in jobs][:3] == [1101, 1102, 1103]
    for i, job in enumerate(jobs):
        commands = pod.runner.job_commands(pod.plan, pod.host, i, pod.root)
        assert [name for name, _ in commands] == [f"job-{i}-calibrate"]
        argv = commands[0][1]
        assert argv[:4] == ["venv/bin/python", "-m", "experiments.safety_selection", "calibrate"]
        assert argv[argv.index("--recipe") + 1] == r.REC == r.RECIPE_NAMES["B"]
        assert r.REC.endswith({"olmo2-7b": "study-kt-olmo2-7b-r64-b-mb2-20261008.json",
                               "llama31-8b": "study-kt-llama31-8b-r64-b5e5-mb2-20261010.json"}[w.family])
        assert argv[argv.index("--prepared") + 1] == pod.prepared and argv[argv.index("--seeds") + 1] == str(job["seed"])
        assert argv[argv.index("--checkpoints") + 1] == "e1" and argv[argv.index("--out-root") + 1] == "round1"
        if job["kind"] == "arm":
            assert argv[argv.index("--edit") + 1] == f"edits/{job['edit']['sha256']}.edit.json"
            assert argv[argv.index("--arms") + 1] == f"edit-{job['edit']['sha256']}"
        else:
            assert "--edit" not in argv and argv[argv.index("--arms") + 1] == "a0"
        assert "oext" not in " ".join(argv) and "--recipe-s" not in argv
    # the engine's own parser accepts every argv (a fresh interpreter in this repository)
    code = ("import json,sys\nfrom experiments.safety_selection.__main__ import _parser\n"
            "print(json.dumps([vars(_parser().parse_args(a))['command'] for a in json.load(sys.stdin)]))")
    argvs = [pod.runner.job_commands(pod.plan, pod.host, i, pod.root)[0][1][3:] for i in range(len(jobs))]
    done = REAL_RUN([PY, "-B", "-c", code], input=json.dumps(argvs), cwd=ROOT, capture_output=True, text=True,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1"}, timeout=300)
    assert done.returncode == 0, done.stderr[-800:]
    assert json.loads(done.stdout.strip().splitlines()[-1]) == ["calibrate"] * len(jobs)
    # the run: one unit per job, the engine's verify, the ledgers, the a0 fingerprint record on Llama
    pod.remaining([30 * H])
    assert pod.main() == 0
    done = pod.done()
    assert done["ok"] is True and done["stopped"] is None and done["refusal"] is None and done["family"] == w.family
    assert pod.statuses() == ["complete"] * len(jobs)
    assert pod.receipts() == [f"job-{i}-calibrate" for i in range(len(jobs))]
    for i, (rec, job) in enumerate(zip(done["jobs"], jobs)):
        arm = f"edit-{job['edit']['sha256']}" if job["kind"] == "arm" else "a0"
        assert rec["unit"] == f"round1/{job['seed']}-{arm}-e1-a1" and rec["engine_sha256"] == X
        assert rec["complete_sha256"] == sha(pod.root / rec["unit"] / "COMPLETE.json")
        assert rec["outputs"][f"job-{i}/cost-ledger.json"] == sha(pod.root / f"job-{i}" / "cost-ledger.json")
        assert rec["s_pod"] == 1.0 and rec["s"] == 1.0 and rec["s_obs_after"] == 1.0 and rec["verified"]["exit"] == 0
        assert rec["requirement_s"] == pytest.approx(job["start_requirement_s"])     # s = 1: the plan's own value
        if job["kind"] == "a0_arm":
            rel = f"job-{i}/a0-adapter-fingerprint.json"
            assert rec["outputs"][rel] == sha(pod.root / rel)
            doc = json.loads((pod.root / rel).read_text())
            assert doc["checkpoints"] == {"e1": "5" * 64, "q": None} and doc["identity"]["manifest_sha256"] == pod.digest
    verifies = [a for a in pod.ran if a[:3] == ["venv/bin/python", "-m", "experiments.safety_selection"] and "verify" in a]
    assert len(verifies) == len(jobs) and all(a[a.index("--prepared") + 1] == pod.prepared for a in verifies)


def test_the_pod_refuses_another_engine_family_recipe_prepared_set_or_sealed_file(w, monkeypatch, tmp_path):
    """G4 and KD7 on the pod: a differing engine identity, a plan of the other family, a recipe or manifest off its
    pin, a sealed file changed, the verification.json not PREFLIGHT-DONE's: each refuses before any job
    (AssertionError or ValueError; nothing runs, no JOB-DONE.json)."""
    pod = Pod(w, monkeypatch)
    pod.remaining([30 * H])
    runner, root = pod.runner, pod.root

    def refuses(match, exc=AssertionError):
        with pytest.raises(exc, match=match):
            pod.main()
        assert not (root / "JOB-DONE.json").exists() and pod.receipts() == []

    monkeypatch.setattr(runner, "_engine_identity", lambda: "0" * 64)
    refuses("engine code differs from the plan")
    monkeypatch.setattr(runner, "_engine_identity", lambda: X)
    plan = json.loads((root / "plan.json").read_text())
    other = w.other
    write(root / "plan.json", {**plan, "family": other})
    refuses("never plans, packs or launches", ValueError)
    write(root / "plan.json", plan)
    recipe = root / w.rules.REC
    original = recipe.read_text()
    recipe.write_text(original + " ")
    refuses("differs from its pin|sealed file")
    recipe.write_text(original)
    monkeypatch.setattr(runner, "_recipe_config_sha", lambda path: "1" * 64)
    refuses("differs from the plan \\(its config SHA-256\\)")
    monkeypatch.setattr(runner, "_recipe_config_sha", lambda path: w.rules.REC_CONFIG_SHA256)
    manifest = root / pod.prepared / "manifest.sha256"
    manifest.write_text("0" * 64 + "\n")
    refuses("prepared data differ from the plan|sealed file")
    manifest.write_text(pod.digest + "\n")
    edit = next(p for p in (root / "edits").iterdir())
    edit_text = edit.read_text()
    edit.write_text(edit_text + "\n")
    refuses("sealed file\\(s\\) missing or changed")
    edit.write_text(edit_text)
    ver = root / "cuda-preflight-1" / "verification.json"
    ver_text = ver.read_text()
    ver.write_text(ver_text + "\n")
    refuses("differs from PREFLIGHT-DONE.json's verification_sha256")
    ver.write_text(ver_text)
    (root / "JOB-DONE.json").write_text("{}")
    with pytest.raises(AssertionError, match="already ran"):
        pod.main()
    (root / "JOB-DONE.json").unlink()
    monkeypatch.setenv("HF_TOKEN", rk.fake_token())
    refuses("a token is present")
    monkeypatch.delenv("HF_TOKEN")
    assert pod.main() == 0 and pod.statuses() == ["complete"] * 3     # the untouched pod runs


def test_rv2_8_the_runners_pre_job_token_check_reads_the_librarys_token_paths(w, monkeypatch):
    """The security re-verifier's RV2-8: the runner's check before any job calls download_models_stage1's
    no_token_left() (the library's HF_TOKEN_PATH, else HF_HOME/token, else XDG_CACHE_HOME/huggingface/token, and
    stored_tokens beside it), so a stored login where huggingface_hub would read it refuses the pod even when it is
    not at ~/.cache/huggingface/token. Every file is synthetic; HOME is the World's."""
    pod = Pod(w, monkeypatch)
    pod.remaining([20 * H])
    other = w.repo / "elsewhere"
    cases = {"HF_HOME": (other / "hfhome", other / "hfhome" / "token"),
             "XDG_CACHE_HOME": (other / "xdg", other / "xdg" / "huggingface" / "token"),
             "HF_TOKEN_PATH": (other / "secrets" / "hf-token", other / "secrets" / "hf-token")}
    for name, (value, stored) in cases.items():
        monkeypatch.setenv(name, str(value))
        for path in (stored, stored.parent / "stored_tokens"):
            write(path, "a stored login the library would read (synthetic)")
            with pytest.raises(AssertionError, match="a token is present: a stored HF login exists: " + re.escape(str(path))):
                pod.main()
            path.unlink()
            assert not (pod.root / "JOB-DONE.json").exists() and pod.receipts() == []
        default = w.repo / ".cache" / "huggingface" / "token"           # not the library's file while the variable is set
        write(default, "not the library's file (synthetic)")
        assert pod.runner.token_paths().token_file() != default
        default.unlink()
        monkeypatch.delenv(name)
    for name in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        monkeypatch.setenv(name, rk.fake_token())
        with pytest.raises(AssertionError, match=rf"a token is present: a token variable is set: \['{name}'\]"):
            pod.main()
        monkeypatch.delenv(name)
    assert pod.runner.token_paths().no_token_left is not None
    assert pod.main() == 0 and pod.statuses() == ["complete"] * 3     # the untouched pod runs


# ===== 2. s_obs after each arm (KD11; KCR:113) =======================================================================
def test_s_obs_after_each_arm_defers_the_later_arms_above_1_15_and_raises_their_requirement_below(w, monkeypatch):
    """KD11: after each arm the runner reads the unit's progress.jsonl and sets s_obs = the slowest capped 32-row
    batch after the first / BATCH_MAX (at least 1). A first arm at 1.10 x BATCH_MAX raises the second arm's
    requirement (s = 1.10) and everything runs; at 1.20 x the later arms defer with reason s_obs and the lead reads
    the case in deferral.json; the short last batch and the first batch never count."""
    r78, f = w.r78, w.r78.FAMILIES[w.family]
    batch_max = f["BATCH_MAX_S"]
    pod = Pod(w, monkeypatch, batch_s=[1.10 * batch_max, 1.0 * batch_max, 1.0 * batch_max])
    pod.remaining([30 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete"] * 3
    recs = pod.done()["jobs"]
    assert recs[0]["s_obs_after"] == pytest.approx(1.10, abs=1e-4) and recs[0]["s_obs"] == 1.0 and recs[0]["s"] == 1.0
    assert recs[1]["s_obs"] == pytest.approx(1.10, abs=1e-4) and recs[1]["s"] == pytest.approx(1.10, abs=1e-4)
    need_1 = r78.requirement_s(w.family, 33, "arm", 1.0, recs[1]["s_obs"], None)
    assert recs[1]["requirement_s"] == pytest.approx(need_1) and need_1 > recs[0]["requirement_s"]
    assert recs[2]["s_obs"] == pytest.approx(1.10, abs=1e-4)             # the largest s_obs so far, not the last arm's
    assert pod.done()["s_obs_final"] == pytest.approx(1.10, abs=1e-4)
    # above 1.15: the later arms defer
    w2 = rk.World(pod.w.repo / "w2", monkeypatch, w.family)
    pod2 = Pod(w2, monkeypatch, batch_s=[1.20 * batch_max, 1.0 * batch_max])
    pod2.remaining([30 * H])
    assert pod2.main() == 0
    assert pod2.statuses() == ["complete", "deferred", "deferred"] and pod2.receipts() == ["job-0-calibrate"]
    done = pod2.done()
    assert done["stopped"] == "deferred" and done["ok"] is True and done["refusal"]["reason"] == "s_obs"
    assert done["jobs"][0]["s_obs_after"] == pytest.approx(1.20, abs=1e-4)
    assert done["jobs"][1]["reason"] == "s_obs" == done["jobs"][2]["reason"]
    deferral = json.loads((pod2.root / "deferral.json").read_text())
    assert deferral["first_deferred"] == 1 and deferral["deferred"] == [1, 2] and deferral["reason"] == "s_obs"
    assert deferral["s_obs"] == pytest.approx(1.20, abs=1e-4) and deferral["stopped"] == "deferred"


@pytest.mark.parametrize("drift", ["no capped field", "no rows field", "no 32-row batch", "no progress file",
                                   "one generate row"])
def test_a_progress_record_the_rule_cannot_read_refuses_the_next_arm(w, monkeypatch, drift):
    """A-V1 (T2's fixed behaviour): a finished arm whose progress.jsonl lacks an integer capped or rows on a generate
    row, holds no 32-row batch, or is missing, must not pass as s_obs = 1: the next arm does not start (deferred,
    reason s_obs_record; JOB-DONE stopped "refused", ok false), the unit itself stands complete."""
    def change(rows):
        if drift == "no capped field":
            return [{k: v for k, v in r.items() if k != "capped"} for r in rows]
        if drift == "no rows field":
            return [{k: v for k, v in r.items() if k != "rows"} for r in rows]
        if drift == "no 32-row batch":
            return [{**r, "rows": 16} for r in rows]
        if drift == "no progress file":
            return []
        return rows[:1]
    pod = Pod(w, monkeypatch, progress_change=change)
    pod.remaining([30 * H])
    assert pod.main() == 1
    assert pod.statuses() == ["complete", "deferred", "deferred"] and pod.receipts() == ["job-0-calibrate"]
    done = pod.done()
    assert done["stopped"] == "refused" and done["ok"] is False and done["refusal"]["reason"] == "s_obs_record"
    assert done["jobs"][0]["s_obs_after"] is None and "s_obs_problem" in done["jobs"][0]
    assert done["jobs"][1]["reason"] == "s_obs_record" and "job 0" in done["jobs"][1]["refusal"]
    assert done["jobs"][0]["complete_sha256"] == sha(pod.root / done["jobs"][0]["unit"] / "COMPLETE.json")
    assert json.loads((pod.root / "deferral.json").read_text())["reason"] == "s_obs_record"


# ===== 3. the free-space check before each job (KD5) ================================================================
def test_the_free_space_check_refuses_a_job_that_would_not_fit_and_records_why(w, monkeypatch):
    """KD5: FREE_SPACE_MIN_GB = 8.0 on the 50 GB volume. Below it (or unreadable) before a job, that job and every
    later one are deferred with reason free_space and the refusal names KD5; the check runs before EACH job (the
    first arm runs at 40 GB free, the second does not at 7.9 GB)."""
    assert w.r78.FREE_SPACE_MIN_GB == 8.0 == w.rules.FREE_SPACE_MIN_GB and w.r78.VOLUME_GB == 50
    pod = Pod(w, monkeypatch, free_gb=[40.0, 7.9, 40.0])
    pod.remaining([30 * H])
    assert pod.main() == 1
    assert pod.statuses() == ["complete", "deferred", "deferred"] and pod.receipts() == ["job-0-calibrate"]
    done = pod.done()
    assert done["stopped"] == "refused" and done["refusal"]["reason"] == "free_space" and "KD5" in done["refusal"]["text"]
    assert done["jobs"][0]["free_gb"] == 40.0 and done["jobs"][1]["free_gb"] == 7.9 and done["jobs"][1]["reason"] == "free_space"
    assert json.loads((pod.root / "deferral.json").read_text())["free_gb"] == 7.9
    for free in (None, float("nan"), 8.0 - 1e-6):
        w2 = rk.World(pod.w.repo / f"w-{abs(hash(repr(free))) % 1000}", monkeypatch, w.family)
        pod2 = Pod(w2, monkeypatch, free_gb=free)
        pod2.remaining([30 * H])
        assert pod2.main() == 1 and pod2.statuses() == ["deferred"] * 3 and pod2.receipts() == []
        assert pod2.done()["refusal"]["reason"] == "free_space"
    assert pod.runner.free_space_gb(pod.root) > 0                        # the real reading: this disk's free GB


# ===== 4. the job decision with the preflight's two documents (KCR test 12 on fake files) ============================
@pytest.mark.parametrize("case", ["pre ms_per_step_full missing", "pre training_s missing", "verification no cap_projection",
                                  "verification untuned_projected_s missing", "the two documents disagree",
                                  "s_pod above 1.15", "pre training_s not finite"])
def test_job_decision_takes_both_documents_and_refuses_a_missing_field_or_a_slow_pod(w, monkeypatch, case):
    """KCR test 12 (fake PREFLIGHT-DONE.json and verification.json): a missing or non-finite speed field in either
    document, a cap_projection block missing, the two documents disagreeing on training_s, or s_pod > 1.15 refuse the
    pod before any job (every job deferred, reason preflight; JOB-DONE stopped "refused")."""
    f = w.r78.FAMILIES[w.family]
    pre, ver = {}, {}
    if case == "pre ms_per_step_full missing":
        pre = {"ms_per_step_full": ...}
    elif case == "pre training_s missing":
        pre = {"training_s": ...}
    elif case == "pre training_s not finite":
        pre = {"training_s": float("nan")}
    elif case == "verification no cap_projection":
        ver = {"cap_projection": ...}
    elif case == "verification untuned_projected_s missing":
        ver = {"cp_untuned_projected_s": ...}
    elif case == "the two documents disagree":
        ver = {"cp_training_s": TRAINING_S[w.family] + 1.0}
    else:
        pre = {"training_s": 1.2 * f["PRE_TRAINING_S_MAX"]}
        ver = {"cp_training_s": 1.2 * f["PRE_TRAINING_S_MAX"]}
    pod = Pod(w, monkeypatch, pre_change=pre, ver_change=ver)
    pod.remaining([30 * H])
    assert pod.main() == 1
    assert pod.statuses() == ["deferred"] * 3 and pod.receipts() == []
    done = pod.done()
    assert done["stopped"] == "refused" and done["ok"] is False and done["refusal"]["reason"] == "preflight"
    text = done["refusal"]["text"]
    if case == "s_pod above 1.15":
        assert "1.200 x the slowest measured pod" in text
    elif case == "the two documents disagree":
        assert "not one preflight" in text
    else:
        assert "missing or not finite" in text or "no cap_projection" in text


def test_a_good_pod_runs_at_the_two_documents_values_and_a_slower_one_scales_the_requirement(w, monkeypatch):
    """The decision at s_pod from PREFLIGHT-DONE's training_s and ms_per_step_full and verification.json's
    cap_projection: a pod at 1.10 x the slowest measured training_s runs with s = 1.10 and a requirement 1.10 x
    upper_M + 1,800 s; the sanity floor F_pre never lowers it; the remaining time decides run or defer per job."""
    f = w.r78.FAMILIES[w.family]
    slow = 1.10 * f["PRE_TRAINING_S_MAX"]
    pod = Pod(w, monkeypatch, pre_change={"training_s": slow}, ver_change={"cp_training_s": slow})
    need = w.r78.requirement_s(w.family, 33, "arm", 1.10, 1.0, {"training_s": slow, "ms_per_step_full": MS_FULL[w.family],
                                                               "untuned_projected_s": UNTUNED_S})
    assert need == pytest.approx(1.10 * w.r78.upper_m_s(w.family, 33) + 1800)
    pod.remaining([need + 1, need - 1, 30 * H])
    assert pod.main() == 0
    assert pod.statuses() == ["complete", "deferred", "deferred"]
    recs = pod.done()["jobs"]
    assert recs[0]["s_pod"] == pytest.approx(1.10) and recs[0]["requirement_s"] == pytest.approx(need)
    assert recs[1]["reason"] == "remaining" and recs[1]["requirement_s"] == pytest.approx(need)
    assert json.loads((pod.root / "deferral.json").read_text())["reason"] == "remaining"


def test_check_keys_takes_the_bank_from_the_recipe_and_the_packed_manifest_and_the_preflight_must_agree(w, monkeypatch):
    """KCR:147 (A-V3; the T2 fixer's job 9 and the re-verifier's job 6): bank = {cap_tokens 2048, greedy_prompts 468,
    harm_samples 600, generation_batch 32} from the recipe (generation.max_new_tokens, batch_size, harm_samples.count 3)
    and the prepared manifest's dev counts (96 + 200 + 100 + 72 generated prompts; 200 harm prompts x 3 = 600 sampled
    answers, never 200); the preflight's verification.json must show the same four numbers; check_keys refuses any
    other bank, another GPU and a kind off the allow-list, and the refusal is recorded (every job deferred, reason
    key)."""
    pod = Pod(w, monkeypatch)
    runner, root, r = pod.runner, pod.root, w.rules
    bank = runner.bank_record(root, r.REC, pod.prepared)
    assert bank == {"cap_tokens": 2048, "greedy_prompts": 468, "harm_samples": 600, "generation_batch": 32} == w.r78.BANK
    assert runner.bank_from_verification(pod.ver) == bank
    assert runner.bank_from_verification({}) == {"cap_tokens": None, "greedy_prompts": None, "harm_samples": None,
                                                  "generation_batch": None}
    assert runner.gpu_name_of(pod.ver) == GPU and runner.gpu_name_of({"environment": {}}) is None
    assert runner.key_refusal(pod.plan, pod.host, pod.ver, bank) is None
    # the preflight saw another bank than the pack: the pod is not the planned one (asserted)
    pod.remaining([30 * H])
    ver = root / "cuda-preflight-1" / "verification.json"
    for change in ({"sample_units": 200}, {"generate_units": 500}):
        doc = fake_verification(w.family, r.REC_CONFIG_SHA256, pod.digest, **change)
        write(ver, doc)
        write(root / "PREFLIGHT-DONE.json", {**pod.pre, "verification_sha256": sha(ver)})
        with pytest.raises(AssertionError, match="differ from what the preflight saw"):
            pod.main()
    # the pack and the preflight agree on a bank the basis does not hold for: recorded (deferred, reason key)
    doc = fake_verification(w.family, r.REC_CONFIG_SHA256, pod.digest, sample_units=200)
    write(ver, doc)
    write(root / "PREFLIGHT-DONE.json", {**pod.pre, "verification_sha256": sha(ver)})
    recipe = json.loads((root / r.REC).read_text())
    recipe["generation"]["harm_samples"]["count"] = 1
    write(root / r.REC, recipe)
    monkeypatch.setitem(r.RECIPE_PINS, r.REC, sha(root / r.REC))
    sealed = json.loads((root / "sealed-files.json").read_text())
    sealed["files"][r.REC] = sha(root / r.REC)
    write(root / "sealed-files.json", sealed)
    plan = json.loads((root / "plan.json").read_text())
    plan["hosts"][pod.host]["sealed_files_sha256"] = sha(root / "sealed-files.json")
    write(root / "plan.json", plan)
    assert runner.bank_record(root, r.REC, pod.prepared)["harm_samples"] == 200
    assert pod.main() == 1 and pod.statuses() == ["deferred"] * 3 and pod.receipts() == []
    done = pod.done()
    assert done["refusal"]["reason"] == "key" and "harm_samples = 200" in done["refusal"]["text"]
    # another GPU: recorded too
    recipe["generation"]["harm_samples"]["count"] = 3
    write(root / r.REC, recipe)
    monkeypatch.setitem(r.RECIPE_PINS, r.REC, sha(root / r.REC))
    sealed["files"][r.REC] = sha(root / r.REC)
    write(root / "sealed-files.json", sealed)
    plan["hosts"][pod.host]["sealed_files_sha256"] = sha(root / "sealed-files.json")
    write(root / "plan.json", plan)
    write(ver, fake_verification(w.family, r.REC_CONFIG_SHA256, pod.digest, gpu="NVIDIA H100 80GB HBM3"))
    write(root / "PREFLIGHT-DONE.json", {**pod.pre, "verification_sha256": sha(ver)})
    (root / "JOB-DONE.json").unlink()
    shutil.rmtree(root / "job-done")
    assert pod.main() == 1 and pod.done()["refusal"]["reason"] == "key"
    assert "has no measured basis" in pod.done()["refusal"]["text"]


# ===== 5. SR-2: no U value and no answer text in any record or printed line (a walk) =================================
def test_no_record_or_printed_line_holds_a_u_value_an_answer_or_the_edits_text(wf, monkeypatch, capsys):
    """SR-2 (blinding; at block 0 the only reader of U is scripts/scale78b/noise_reading.py): the fake engine writes
    the SENTINELS into the unit's eval summary (a U value), its generations (answer text) and COMPLETE.json's
    evaluation block; the packed edit file carries the World's trap text. The walk: every record the runner wrote
    (JOB-DONE.json, job-done/*, the ledgers, the a0 fingerprint record), every printed line, and then plan_tool's
    record-done on the pulled tree (its printout, plan.json, operator-actions.jsonl) hold none of them."""
    w = wf
    pod = Pod(w, monkeypatch)
    pod.remaining([30 * H])
    assert pod.main() == 0
    printed = capsys.readouterr().out
    texts = [printed, *pod.texts()]
    assert len(texts) >= 5
    unit = pod.root / pod.done()["jobs"][0]["unit"]
    assert SENTINELS[0] in (unit / "eval" / "e1" / "summary.json").read_text()          # the fixture holds them ...
    assert SENTINELS[2] in (unit / "generations" / "e1" / "answers.jsonl").read_text()
    assert rk.SENTINEL in next((pod.root / "edits").iterdir()).read_text()
    for text in texts:
        assert not any(s in text for s in SENTINELS), text[:200]                        # ... and the kit wrote none
    # record-done on the Mac (plan_tool, K1's copy) over the pulled tree
    tree = w.root / "retrieved" / pod.host / "tree"
    shutil.copytree(pod.root, tree, ignore=shutil.ignore_patterns("plan.json", "sealed-files.json", "edits", "data",
                                                                  "experiments", "process_receipt.py"))
    out = w.tool.record_done(pod.host)
    printed = capsys.readouterr().out
    assert out["statuses"] == ["complete"] * len(pod.plan["hosts"][pod.host]["jobs"])
    plan_text = (w.root / "plan.json").read_text()
    actions = (w.root / "operator-actions.jsonl").read_text()
    for text in (printed, json.dumps(out), plan_text, actions):
        assert not any(s in text for s in SENTINELS)
    plan = w.plan()
    h = plan["hosts"][pod.host]
    assert h["done"] is True and all(j["status"] == "complete" for j in h["jobs"])
    assert all(j["complete_sha256"] == sha(tree / j["unit"] / "COMPLETE.json") for j in h["jobs"])
    if w.family == "llama31-8b":
        assert h["jobs"][3]["kind"] == "a0_arm" and "job-3/a0-adapter-fingerprint.json" in h["jobs"][3]["outputs"]
    # the seal of block 0 (seal.py, the stage-1 kit's): every pulled file by SHA-256, the readable classes only
    seal = load_by_path("seal78", w.root / "seal.py")
    sealed = seal.seal_block("0")
    doc = json.loads((w.root / "seals" / "block-0.json").read_text())
    assert sealed["block"] == "0" and sealed["files"] == len(doc["files"]) > 6
    readable = sorted({f["path"].split("/")[-1] for f in doc["files"] if f["class"] == "readable"})
    assert readable == sorted(set(readable)) and "JOB-DONE.json" in readable and "cost-ledger.json" in readable
    assert all(f["class"] == "sealed" for f in doc["files"] if f["path"].endswith(("summary.json", "answers.jsonl",
                                                                                  "COMPLETE.json", "progress.jsonl")))
    assert not any(s in (w.root / "seals" / "block-0.json").read_text() for s in SENTINELS)
    assert w.plan()["seals"]["0"]["sha256"] == sha(w.root / "seals" / "block-0.json")
    with pytest.raises(SystemExit, match="already sealed"):
        seal.seal_block("0")


# ===== 6. the retrain kind refuses on the pod while RECIPE_S is None (A1) ============================================
def test_the_retrain_kind_refuses_on_the_pod_while_recipe_s_is_null(w, monkeypatch, local_processes):
    """Addendum A1 (ruling 10, A2): the a0-1101 retrain needs recipe S_78, whose pin is null until the anchor job and
    the lead's commit; the job runner refuses it at the key check and the job decision (deferred, reason recipe_pin),
    the dry run prints it unrunnable with the pin's text, and no command exists for it in this round."""
    r = w.rules
    assert w.r78.RECIPE_S[w.family] is None and r.RECIPE_S is None and "retrain" in w.r78.S78_KINDS
    retrain = r.job_record("retrain", "a0", 1101, None, 38)
    assert retrain["unmeasured"] is True and retrain["start_requirement_s"] > 0            # priced (M3), not run
    pod = Pod(w, monkeypatch, jobs=[retrain])
    with pytest.raises(pod.runner.Unrunnable, match="RECIPE_S|S_78"):
        pod.runner.job_commands(pod.plan, pod.host, 0, pod.root)
    pod.remaining([30 * H])
    assert pod.main() == 1
    assert pod.statuses() == ["deferred"] and pod.receipts() == []
    done = pod.done()
    assert done["stopped"] == "refused" and done["refusal"]["reason"] == "recipe_pin"
    assert "S_78" in done["refusal"]["text"] or "RECIPE_S" in done["refusal"]["text"]
    out = REAL_RUN([PY, "-B", str(w.root / "setup" / "job_runner_stage1.py"), pod.host, "--dry-run"], cwd=pod.root,
                   capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert out.returncode == 0, out.stderr[-800:]
    printed = json.loads(out.stdout)
    assert "unrunnable" in printed["jobs"][0]["commands"] and "retrain" in printed["jobs"][0]["commands"]["unrunnable"]
    assert isinstance(printed["decisions"], dict) and "S_78" in printed["decisions"]["refused"]
    # once the pin is filled the kind still has no command in this round (a later round's), never the main config
    monkeypatch.setitem(w.r78.RECIPE_S, w.family, "a" * 64)
    with pytest.raises(pod.runner.Unrunnable, match="later round"):
        pod.runner.job_commands(pod.plan, pod.host, 0, pod.root)
    with pytest.raises(pod.runner.Unrunnable, match="not a block-0 kind"):
        pod.runner.job_commands({**pod.plan, "hosts": {pod.host: {**pod.plan["hosts"][pod.host],
                                                                  "jobs": [r.job_record("l1_scan")]}}}, pod.host, 0, pod.root)
    with pytest.raises(pod.runner.Unrunnable, match="main config only"):
        pod.runner.recipe_path({"kind": "arm", "recipe": "S"})


# ===== 8. the dry run computes s and defers the right job (M) =======================================================
def test_the_dry_run_on_fake_preflight_documents_computes_s_and_defers_the_right_job(w, monkeypatch, local_processes):
    """The brief's item 8 (plan T4's acceptance; KCR test 12): job_runner_stage1.py HOST --dry-run in a folder with
    PREFLIGHT-DONE.json and its verification.json prints rules_78b.pod_dry_run's decisions: at --remaining between the
    first and the second requirement the first job runs and the second and third defer (reason remaining, then
    "earlier job deferred"); a pod 1.10 x slower in training_s gives s_pod 1.10 and the requirement 1.10 x upper_M +
    1,800 s; --free-gb below 8 refuses; the dry run writes nothing."""
    f = w.r78.FAMILIES[w.family]
    pod = Pod(w, monkeypatch)
    jobs = pod.plan["hosts"][pod.host]["jobs"]
    need = jobs[0]["start_requirement_s"]
    upper = jobs[0]["measured_upper_s"]
    before = sorted(str(p.relative_to(pod.root)) for p in pod.root.rglob("*"))

    def dry(*extra) -> dict:
        done = REAL_RUN([PY, "-B", str(w.root / "setup" / "job_runner_stage1.py"), pod.host, "--dry-run", *extra],
                        cwd=pod.root, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
        assert done.returncode == 0, done.stderr[-800:]
        assert sorted(str(p.relative_to(pod.root)) for p in pod.root.rglob("*")) == before    # writes nothing
        return json.loads(done.stdout)

    out = dry("--remaining", str(upper + need + 1), "--free-gb", "40")
    assert out["dry_run"] is True and out["family"] == w.family and out["remaining_s"] == upper + need + 1
    d = out["decisions"]
    assert [x["action"] for x in d] == ["run", "run", "defer"] and d[2]["reason"] == "remaining"
    assert d[0]["s_pod"] == 1.0 and d[0]["s"] == 1.0 and d[0]["requirement_s"] == pytest.approx(need)
    out = dry("--remaining", str(need + 1), "--free-gb", "40")
    assert [x["action"] for x in out["decisions"]] == ["run", "defer", "defer"]
    assert [x["reason"] for x in out["decisions"]][:2] == [None, "remaining"]
    assert out["decisions"][2]["reason"] in ("remaining", "earlier job deferred")   # its own shortfall, or the cascade
    out = dry("--free-gb", "7.5", "--remaining", str(30 * H))
    assert "below 8.0 GB" in out["decisions"]["refused"]
    out = dry("--remaining", str(30 * H), "--free-gb", "40", "--s-obs", "1.16")
    assert [x["action"] for x in out["decisions"]] == ["defer"] * 3 and out["decisions"][0]["reason"] == "s_obs"
    out = dry("--free-gb", "40")                                            # no heartbeat, no --remaining: never fits
    assert out["remaining_s"] is None and [x["action"] for x in out["decisions"]] == ["defer"] * 3
    # a slower pod: s_pod from the two documents
    slow = 1.10 * f["PRE_TRAINING_S_MAX"]
    ver = write(pod.root / "cuda-preflight-1" / "verification.json",
                fake_verification(w.family, w.rules.REC_CONFIG_SHA256, pod.digest, cp_training_s=slow))
    write(pod.root / "PREFLIGHT-DONE.json", {**pod.pre, "training_s": slow, "verification_sha256": sha(ver)})
    before = sorted(str(p.relative_to(pod.root)) for p in pod.root.rglob("*"))
    out = dry("--remaining", str(30 * H), "--free-gb", "40")
    d = out["decisions"][0]
    assert d["s_pod"] == pytest.approx(1.10) and d["s"] == pytest.approx(1.10)
    assert d["requirement_s"] == pytest.approx(1.10 * w.r78.upper_m_s(w.family, 33) + 1800)
    assert out["jobs"][0]["commands"][0][0] == "job-0-calibrate" and out["jobs"][0]["inputs"][-1].startswith("edits/")


# ===== the preflight (setup/preflight_stage1.py) ====================================================================
@pytest.mark.parametrize("shell_login", [False, True], ids=["clean-shell", "shell-with-a-stored-login"])
def test_the_preflight_writes_the_speed_and_bank_fields_and_refuses_a_slow_pod(w, monkeypatch, tmp_path, shell_login):
    """The 7-8B preflight: the family's main config is the one candidate; PREFLIGHT-DONE.json keeps the measured
    files' keys and adds family, bank (the four numbers from verification.json) and speed {s_pod, refused}; a pod
    past 1.15 (KD3) or a missing speed field makes ok false (exit 1) so no job starts; another family's plan or a
    second recipe refuses before anything runs. Round 4b (the security verifier's D4): the test isolates the
    library's token paths (HF_HOME, HF_TOKEN_PATH, XDG_CACHE_HOME and the hub caches), so a shell whose variables point
    at a stored login (a FAKE one, made here) does not change the result."""
    if shell_login:                                      # the shell's variables at a stored login (fake value)
        login = tmp_path / "shell-login"
        (login / "huggingface").mkdir(parents=True)
        (login / "huggingface" / "token").write_text("hf_" + "F4ke" * 9 + "\n")
        (login / "token").write_text("hf_" + "F4ke" * 9 + "\n")
        for name, value in (("HF_HOME", login), ("HF_TOKEN_PATH", login / "token"), ("XDG_CACHE_HOME", login)):
            monkeypatch.setenv(name, str(value))
    r, f = w.rules, w.r78.FAMILIES[w.family]
    pf = load_by_path("pf78", w.root / "setup" / "preflight_stage1.py")
    root = tmp_path / "pod"
    root.mkdir()
    monkeypatch.setattr(pf, "ROOT", root)
    monkeypatch.setattr(pf, "HEARTBEAT", tmp_path / "no-heartbeat.json")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    for name in pf.TOKEN_ENV_NAMES + HF_PATH_VARS:       # D4: the token variables AND the library's path variables
        monkeypatch.delenv(name, raising=False)
    write(root / r.REC, {"generation": {"batch_size": 32, "max_new_tokens": 2048, "harm_samples": {"count": 3}},
                         "model": {"attn_implementation": "sdpa"}})
    write(root / "plan.json", {"family": w.family, "preflight_recipes": [r.REC], "preflight_prepared": "data/kt-prepared/x"})
    write(root / "BOOTSTRAP-READY.json", {"ok": True})
    write(root / "probe.json", {"plan": [{"gated": False}]})
    ran = []
    training = {"value": TRAINING_S[w.family]}

    def fake_run(args, **kwargs):
        ran.append(list(args))
        if args[:2] == ["python3", "process_receipt.py"]:
            out = args[args.index("--out", 5) + 1] if "--out" in args[5:] else None
            write(root / out / "verification.json",
                  fake_verification(w.family, r.REC_CONFIG_SHA256, "m" * 64, cp_training_s=training["value"]))
        return subprocess.CompletedProcess(args, 0, '{"guard": "synthetic"}\n', "")
    monkeypatch.setattr(pf.subprocess, "run", fake_run)
    assert pf.main([]) == 0
    done = json.loads((root / "PREFLIGHT-DONE.json").read_text())
    assert done["ok"] is True and done["family"] == w.family and done["recipe"] == r.REC and done["folder"] == "cuda-preflight-1"
    assert done["verification_sha256"] == sha(root / "cuda-preflight-1" / "verification.json")
    assert done["training_s"] == TRAINING_S[w.family] and done["ms_per_step_full"] == MS_FULL[w.family]
    assert done["bank"] == {"cap_tokens": 2048, "greedy_prompts": 468, "harm_samples": 600, "generation_batch": 32}
    assert done["speed"] == {"s_pod": 1.0, "refused": None, "limit": 1.15} and done["guard"] == {"guard": "synthetic"}
    assert "o500_projection" not in done and done["cap_projection"]["untuned_projected_s"] == UNTUNED_S
    for key in ("ok", "recipe", "folder", "verification_sha256", "init_equals_untuned", "ms_per_step_full",
                "projected_job_upper_s", "training_s", "overhead_s", "generation_batch", "tried", "cap_projection", "guard"):
        assert key in done, key
    assert ran[0][:2] == ["python3", "process_receipt.py"] and "cuda_preflight_family.py" in " ".join(ran[0])
    # a slow pod: the speed factor refuses, ok false, exit 1
    (root / "PREFLIGHT-DONE.json").unlink()
    shutil.rmtree(root / "cuda-preflight-1")
    training["value"] = 1.2 * f["PRE_TRAINING_S_MAX"]
    assert pf.main([]) == 1
    done = json.loads((root / "PREFLIGHT-DONE.json").read_text())
    assert done["ok"] is False and done["speed"]["s_pod"] is None and "1.200 x the slowest measured pod" in done["speed"]["refused"]
    # another family's plan, or two recipes: refused before anything runs
    (root / "PREFLIGHT-DONE.json").unlink()
    write(root / "plan.json", {"family": w.other, "preflight_recipes": [r.REC], "preflight_prepared": "x"})
    with pytest.raises(ValueError, match="never plans, packs or launches"):
        pf.main([])
    write(root / "plan.json", {"family": w.family, "preflight_recipes": [r.REC, "other.json"], "preflight_prepared": "x"})
    with pytest.raises(SystemExit, match="main config only"):
        pf.main([])
    assert not (root / "PREFLIGHT-DONE.json").exists()
    assert pf.speed_record(w.family, {})["refused"] is not None                 # no fields: refused, never 1.0


# ===== states_tool.py and the finisher's states pull (KD5) ==========================================================
def states_tree(kit_root: Path, host: str, units: dict) -> tuple[Path, Path]:
    """A pulled light tree (round1/UNIT/COMPLETE.json listing states/e1/ files by hash) and a states-e1 tar of those
    files (from a separate folder, as host.py pull-states tars them on the pod)."""
    tree = kit_root / "retrieved" / host / "tree"
    pod = kit_root / "pod-side"
    for unit, saved in units.items():
        files = {}
        for rel, text in saved.items():
            p = write(pod / "round1" / unit / rel, text)
            files[rel] = sha(p)
            if not rel.endswith(".safetensors"):              # the light pull leaves out *.safetensors only
                write(tree / "round1" / unit / rel, text)
        summary = write(tree / "round1" / unit / "eval" / "e1" / "summary.json", {"u": 0.5})
        write(tree / "round1" / unit / "COMPLETE.json", {"complete": True, "files": {**files, "eval/e1/summary.json": sha(summary)}})
    tar_path = kit_root / "retrieved" / host / "states-e1-20261105T120000Z.tar"
    with tarfile.open(tar_path, "w") as t:
        for unit in units:
            folder = pod / "round1" / unit / "states" / "e1"
            if folder.is_dir():
                t.add(folder, arcname=f"round1/{unit}/states/e1")
    return tree, tar_path


def test_states_tool_verifies_the_pulled_e1_states_against_each_units_complete_json(w, capsys):
    """KD5's state rule, the Mac side: the newest states-e1-*.tar is unpacked (states members only) and every
    states/e1/ file a unit's COMPLETE.json lists must be present with its hash; the record holds names, counts and
    hashes; a changed state, a member outside states/e1/, a unit with no e1 state listed anywhere, and a tar unit the
    tree does not seal refuse (exit 2); the kit has no delete command (host.py)."""
    st = load_by_path("states78", w.root / "states_tool.py")
    host = "olmo2-7b-0-1"
    units = {"1101-edit-aa-e1-a1": {"states/e1/adapter.safetensors": "A" * 100, "states/e1/state.json": '{"s": 1}'},
             "1102-edit-bb-e1-a1": {"states/e1/adapter.safetensors": "B" * 100, "states/e1/state.json": '{"s": 2}'}}
    tree, tar_path = states_tree(w.root, host, units)
    assert st.main(["check", host, "e1"]) == 0
    printed = capsys.readouterr().out
    assert printed.startswith("states verified: 2 units")
    record = json.loads(next((w.root / "retrieved" / host).glob("states-e1-check-*.json")).read_text())
    assert record["verified_units"] == 2 and record["tar_sha256"] == sha(tar_path) and record["members"] >= 4
    assert record["units"]["1101-edit-aa-e1-a1"] == {"files": 2, "bytes": 108} and record["checkpoint"] == "e1"
    assert record["kind"].startswith("stage1-78b state rule (KD5)")
    assert (tree / "round1" / "1101-edit-aa-e1-a1" / "states" / "e1" / "adapter.safetensors").read_text() == "A" * 100
    # a changed state file refuses
    (w.root / "pod-side" / "round1" / "1101-edit-aa-e1-a1" / "states" / "e1" / "adapter.safetensors").write_text("X")
    with tarfile.open(w.root / "retrieved" / host / "states-e1-20261105T130000Z.tar", "w") as t:
        for unit in units:
            t.add(w.root / "pod-side" / "round1" / unit / "states" / "e1", arcname=f"round1/{unit}/states/e1")
    with pytest.raises(SystemExit, match="1 state file\\(s\\) missing or changed"):
        st.main(["check", host, "e1"])
    # a member outside states/e1/ refuses before anything is extracted
    bad = w.root / "retrieved" / host / "states-e1-20261105T140000Z.tar"
    with tarfile.open(bad, "w") as t:
        t.add(tree / "round1" / "1101-edit-aa-e1-a1" / "COMPLETE.json", arcname="round1/1101-edit-aa-e1-a1/COMPLETE.json")
    with pytest.raises(SystemExit, match="outside round1"):
        st.main(["check", host, "e1"])
    bad.unlink()
    with pytest.raises(SystemExit, match="checkpoint must be one of"):
        st.main(["check", host, "e2"])
    with pytest.raises(SystemExit, match="no states-q-\\*.tar"):
        st.main(["check", host, "q"])
    assert st.main(["rule"]) == 0 and "no delete command" in capsys.readouterr().out
    host_text = (w.root / "host.py").read_text()
    assert '"delete"' not in host_text and "def delete" not in host_text                 # the kit has no delete command


def test_the_finisher_pulls_and_verifies_the_e1_states_before_the_stop_and_never_removes_their_tar(w, monkeypatch, local_processes):
    """KD5 in the finisher: after the light check, host.py pull-states HOST e1 and states_tool.py check run while the
    pod has its SSH address, then the stop; finished.json's "states" entry says verified; a host.py without the
    pull-states command (K3's port pending) or a failing check leaves review-needed-stopped with the states on the
    volume; the states tar stays, the light pull-*.tar goes."""
    fin = load_by_path("fin78", w.root / "finisher.py")
    host = "olmo2-7b-0-1"
    units = {"1101-edit-aa-e1-a1": {"states/e1/adapter.safetensors": "A" * 100, "states/e1/state.json": '{"s": 1}'}}
    tree, tar_path = states_tree(w.root, host, units)
    write(tree / "JOB-DONE.json", {"host": host, "ok": True, "jobs": []})
    write(w.root / "retrieved" / host / "pull-20261105T120000Z.tar", "light tar (synthetic)")
    write(w.root / "plan.json", {"hosts": {host: {"role": "arms", "cap_hours": 8.5}}, "deferrals": [], "requeues": []})
    (w.root / "hosts" / host).mkdir(parents=True)
    calls = []

    def tool(*a):
        calls.append(a)
        if a[0] == "pull-states":
            return subprocess.CompletedProcess(a, 0, json.dumps({"file": tar_path.name, "bytes": tar_path.stat().st_size,
                                                                 "sha256": sha(tar_path)}) + "\n", "")
        return subprocess.CompletedProcess(a, 0, "stopped", "")
    monkeypatch.setattr(fin, "tool", tool)
    monkeypatch.setattr(fin, "unpack", lambda h: tree)
    monkeypatch.setattr(fin, "log", lambda **f: None)
    fin.finish(host, {"exit_code": 0, "elapsed_s": 100})
    record = json.loads((w.root / "hosts" / host / "finished.json").read_text())
    assert record["status"] == "verified-and-stopped"
    assert record["states"]["e1"]["pulled"] is True and record["states"]["e1"]["verified"] is True
    assert record["states"]["e1"]["sha256"] == sha(tar_path) and record["states"]["e1"]["check"].startswith("states verified: 1 units")
    assert [c[0] for c in calls] == ["pull-light", "pull-states", "extend-cap", "stop"] and calls[1] == ("pull-states", host, "e1")
    assert tar_path.exists() and not list((w.root / "retrieved" / host).glob("pull-*.tar"))   # the states tar stays
    # a host.py without pull-states (an older copy's): review-needed-stopped, the states stay on the volume
    def tool_no_states(*a):
        calls.append(a)
        if a[0] == "pull-states":
            return subprocess.CompletedProcess(a, 1, "", "unknown command")
        return subprocess.CompletedProcess(a, 0, "stopped", "")
    monkeypatch.setattr(fin, "tool", tool_no_states)
    (w.root / "hosts" / host / "finished.json").unlink()
    fin.finish(host, {"exit_code": 0, "elapsed_s": 100})
    record = json.loads((w.root / "hosts" / host / "finished.json").read_text())
    assert record["status"] == "review-needed-stopped" and record["states"]["e1"] == {"pulled": False, "verified": False,
                                                                                      "note": "unknown command"}
    assert calls[-2:] == [("extend-cap", host, "120"), ("stop", host)]
    assert "def pull_states(" in (w.root / "host.py").read_text()       # K3 ported the OLMo 3 kit's command (tests/test_gated_78b.py)
    assert not hasattr(fin, "similarity_check") and fin.STATE_PULLS == ("e1",)


# ===== the backup: the states check record always, the states tar with --states (KD5 step 3) =======================
def test_the_backup_stages_the_states_check_record_and_the_states_tar_only_with_states(w, monkeypatch, capsys):
    backup = load_by_path("backup78", w.root / "backup_records_stage1.py")
    assert backup.RUNKIT == ROOT.resolve() / "runkit" / "stage1-78b" or backup.RUNKIT.name == "stage1-78b"
    host = "olmo2-7b-0-1"
    r = w.rules
    units = {"1101-edit-aa-e1-a1": {"states/e1/adapter.safetensors": "A" * 100, "states/e1/state.json": '{"s": 1}'}}
    tree, tar_path = states_tree(w.root, host, units)
    write(w.root / "retrieved" / host / "states-e1-check-20261105T120100Z.json", {"verified_units": 1})
    write(tree / "JOB-DONE.json", {"host": host, "ok": True, "jobs": []})
    job = r.job_record("arm", "R", 1101, {"path": "x/none.json", "sha256": "0" * 64}, 33)
    job.update(status="deferred")
    h = {"wave": "0", "block": "0", "launch": 0, "role": "arms", "base_eval": False, "engine": "X", "engine_sha256": X,
         "stage": "stage1-X", "sealed_files_sha256": None, "cap_hours": 8.5, "jobs": [job], "done": True}
    prep = w.repo / "tmp" / "kt-prepared" / r.PREPARED_NAME
    write(prep / "manifest.json", {"m": 1})
    write(prep / "manifest.sha256", sha(prep / "manifest.json") + "\n")
    write(w.root / "plan.json", {"name": f"stage1-78b-{w.family}", "hosts": {host: h}, "deferrals": [], "requeues": [],
                                 "prepared": {r.PREPARED_NAME: sha(prep / "manifest.json")}})
    for name in ("budget-checks.jsonl", "operator-actions.jsonl", f"hosts-full-{host}.log", "launch.log", "finisher.log"):
        write(w.root / name, "{}\n")
    write(w.root / "hosts" / host / "finished.json", {"status": "verified-and-stopped"})
    plan = json.loads((w.root / "plan.json").read_text())
    sel = backup.select(plan, [host], 50 * 1024 * 1024)
    staged = [dst for _, dst in sel["items"]]
    assert f"records/{host}/retrieved/states-e1-check-20261105T120100Z.json" in staged
    assert not any(d.startswith("states/") for d in staged)
    assert any("staged with --states only" in why for _, why in sel["excluded"])
    assert backup.groups_of(sel) == ("units", "records", "edits+analyses")
    sel = backup.select(plan, [host], 50 * 1024 * 1024, states=True)
    staged = [dst for _, dst in sel["items"]]
    assert f"states/{host}/{tar_path.name}" in staged and backup.groups_of(sel) == ("units", "records", "edits+analyses", "states")
    assert backup.asset_names("backup-2026-11-05-s78", backup.groups_of(sel))[-1] == "s78-states.tar.gz"
    assert backup.main(["--dry-run", "--tag", "backup-2026-11-05-s78", "--states"]) == 0
    printed = capsys.readouterr().out
    assert f"states/{host}/{tar_path.name}" in printed and "s78-states.tar.gz" in printed
    assert backup.main(["--dry-run", "--tag", "backup-2026-11-05-s78", "--states", "--max-file-mb", "0.0001"]) == 3   # oversize


# ===== the committed folder and the copied 1B tests' subjects =======================================================
def test_the_committed_kit_folder_imports_every_runner_module_and_runs_nothing(tmp_path, monkeypatch):
    for name in rk.MODULES:
        monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.syspath_prepend(str(KIT))
    runner = load_by_path("jr78_committed", KIT / "setup" / "job_runner_stage1.py")
    assert runner.rules.FAMILY is None and runner.PREPARED is None and runner.BLOCK0_KINDS == ("arm", "a0_arm")
    with pytest.raises(ValueError, match="names no family"):
        runner.job_commands({"hosts": {"h": {"jobs": [{"kind": "arm", "recipe": "B", "arm": "R", "seed": 1101}]}}}, "h", 0, tmp_path)
    for rel in ("setup/preflight_stage1.py", "finisher.py", "seal.py", "backup_records_stage1.py", "states_tool.py"):
        load_by_path(f"k2_{Path(rel).stem}", KIT / rel)
    import py_compile
    for rel in ("setup/job_runner_stage1.py", "setup/preflight_stage1.py", "setup/extend_cap.py", "finisher.py",
                "seal.py", "status.py", "backup_records_stage1.py", "states_tool.py"):
        py_compile.compile(str(KIT / rel), cfile=str(tmp_path / "x.pyc"), doraise=True)
    assert (KIT / "setup" / "extend_cap.py").read_bytes() == (KIT.parent / "stage1-olmo" / "setup" / "extend_cap.py").read_bytes()
    text = (KIT / "setup" / "job_runner_stage1.py").read_text()
    for gone in ("c1_registry_seed", "similarity_record", "plant_fingerprint_record", "W1_18_SCRIPT",
                 "D2_SCRIPTS", "_safe_lora", "MAN1_PATH"):
        assert gone not in text, gone                                     # the 1B machinery is not in this copy
    assert text.count("OEXT_UNIT_SCRIPT") == 2 and text[text.index("def sc_commands("):text.index("def out_dirs(")].count(
        "r78.OEXT_UNIT_SCRIPT") == 2                     # K4b, PP17: only the scorer block's o_only and o_only_with_regenerate
    assert "s_obs_from_progress" in text and "free_space_gb" in text and "check_keys" in text and "job_decision" in text


# ===== K5 (the security re-verifier's R5): the environment of every process a job starts ===========================
def _env_recorder(monkeypatch, runner, inner) -> list:
    """runner.subprocess.run wrapped: every call's argv and ``env`` keyword are recorded, then ``inner`` answers."""
    seen = []

    def run(args, **kwargs):
        seen.append((list(args), kwargs.get("env", "NOT GIVEN")))
        return inner(args, **kwargs)
    monkeypatch.setattr(runner.subprocess, "run", run)
    return seen


def _token_after_preflight(monkeypatch, runner, fake: str) -> None:
    """The pre-job token check passes (no token then), and only after it a FAKE value (built at test time) appears in
    every token variable and HF_HUB_OFFLINE is "0" in os.environ: the jobs' environment must still hold neither."""
    real = runner.preflight_checks

    def checks(*a, **kw):
        out = real(*a, **kw)
        for name in runner.TOKEN_ENV_NAMES:
            monkeypatch.setenv(name, fake)
        monkeypatch.setenv("HF_HUB_OFFLINE", "0")
        return out
    monkeypatch.setattr(runner, "preflight_checks", checks)


def _assert_job_envs(seen, runner, fake: str, steps: int, verifies: int) -> None:
    calls = [(a, e) for a, e in seen if a[:2] == ["python3", "process_receipt.py"] or
             (a[:3] == ["venv/bin/python", "-m", "experiments.safety_selection"] and "verify" in a)]
    assert len([a for a, _ in calls if a[0] == "python3"]) == steps and len(calls) == steps + verifies, \
        [a[:4] for a, _ in seen]
    for argv, env in calls:
        assert isinstance(env, dict), (argv[:4], env)
        assert not set(env) & set(runner.TOKEN_ENV_NAMES), (argv[:4], sorted(set(env) & set(runner.TOKEN_ENV_NAMES)))
        assert env.get("HF_HUB_OFFLINE") == "1", argv[:4]
        assert fake not in json.dumps(env), argv[:4]


def test_k5_r5_run_job_gives_every_step_and_the_verify_the_scrubbed_offline_environment(w, monkeypatch):
    """R5 (run_job, block 0's engine jobs): each calibrate step and each engine verify gets the runner's own
    environment: no token variable (TOKEN_ENV_NAMES) and HF_HUB_OFFLINE == "1", even when os.environ holds a token
    variable and HF_HUB_OFFLINE=0 after the pre-job check."""
    fake = "hf_" + "R5" * 17                              # the HF token's shape, built here; not a token
    pod = Pod(w, monkeypatch)
    pod.remaining([30 * H])
    _token_after_preflight(monkeypatch, pod.runner, fake)
    seen = _env_recorder(monkeypatch, pod.runner, pod.run)
    assert pod.main() == 0
    jobs = len(pod.plan["hosts"][pod.host]["jobs"])
    _assert_job_envs(seen, pod.runner, fake, steps=jobs, verifies=jobs)
    assert not any(fake in t for t in pod.texts())


def test_k5_r5_run_sc_job_and_verify_unit_give_the_scrubbed_offline_environment(monkeypatch, tmp_path):
    """R5 (run_sc_job and verify_unit): o_only_with_regenerate's three steps (make-job, run-one, the O-ext pass) and
    the engine verify of its regenerated unit each get the runner's own environment (no token variable,
    HF_HUB_OFFLINE == "1"), even when os.environ holds a token variable and HF_HUB_OFFLINE=0 after the pre-job check."""
    sb = load_by_path("scorer_block_k5_r5", KIT / "tests" / "test_scorer_block_78b.py")
    fake = "hf_" + "R5" * 17
    sw = sb.ScWorld(tmp_path, monkeypatch, "olmo2-7b")
    try:
        sw.fill(oext=True)
        side = sw.side_unit(1101)
        sw.pack(*sb.oext_inputs(sw), ("side_complete:a0:1101", side, sb.sha(side)))
        host = sw.init([sb.REGEN])["released"][0]
        pod = sb.ScPod(sw, monkeypatch, host)
        _token_after_preflight(monkeypatch, pod.runner, fake)
        seen = _env_recorder(monkeypatch, pod.runner, pod.run)
        assert pod.main() == 0
        assert pod.done()["jobs"][0]["status"] == "complete"
        _assert_job_envs(seen, pod.runner, fake, steps=3, verifies=1)
        assert fake not in json.dumps(pod.done())
    finally:
        for name in rk.MODULES:
            sys.modules.pop(name, None)
