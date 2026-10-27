"""Kit round 30a (27 Oct 2026; the lead's rulings R1 and R2 on the cert runbook's D2 and D4), on CPU, without RunPod,
Hugging Face or GitHub. Expected values are written by hand.

R1 (D2): the stage-1 runner seeds C1's fresh registry cert/registry-cert_c1.jsonl with R_1101's registry line from
the packed cert_spec input before C1's make-job, so engine Y's real claim_trajectory (imported read-only from engine
Y's frozen tree with -I -B; no bytecode is written there) accepts --replicate-of. Shown both ways: Y's claim refuses
the replicate on an empty registry and accepts it once seeded; the synthetic pod's C1 passes Y's claim with the seed
step and crashes without it; every check of the seed step refuses on its own defect, before any engine step, and
passes on the good record.

R2 (D4): compare_c1.py applies removal_digest.py's rule (imported, pinned) to every file of two synthetic units and
prints and writes only file names, verdicts, rule names and booleans: equal; one evaluation byte different; a
timing-only difference that still passes; missing files; the replicate_of rule of job.json; refusals; seal-safety
(no sentinel value, no hash of a unit file in the output); and its verdicts agree with removal_digest.unit_digest."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

import test_stage1_runner as base
from test_stage1_runner import kit  # noqa: F401 - the kit fixture (a copy of the kit in a temporary folder)

Pod, job, edit_ref, cert_spec, write, sha = base.Pod, base.job, base.edit_ref, base.cert_spec, base.write, base.sha
REAL_RUN, PY, WS_Y, KIT, REPO, S, P = base.REAL_RUN, base.PY, base.WS_Y, base.KIT, base.REPO, base.S, base.P
SPEC = base.INPUT_FILES["cert_spec"]                  # inputs/cert_spec/cert_spec.json on the synthetic pod
REGISTRY = "cert/registry-cert_c1.jsonl"

# C1's key by hand (the lead's ruling R1; cert runbook §0 D2; B15 brief J12)
R1_ARM = "edit-f7d7eb86cb58f7a5e7e1408973a13531f74845e066d7328d6e726ecdd442ffdd"
MANIFEST = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
TRAINING = "f46279e5830f477742189ef03c03ffc0ec86107ae060bb5ef9034ba47acabfac"
R1101_RUN = "round1/1101-edit-f7d7eb86cb58f7a5e7e1408973a13531f74845e066d7328d6e726ecdd442ffdd-e1-a1"
C1_KEY = {"arm": R1_ARM, "manifest_sha256": MANIFEST, "role": "development", "seed": 1101, "split": "dev",
          "training_identity": TRAINING}


def json_line(obj) -> bytes:
    """Engine Y's JSONL line (common.append_jsonl), by hand."""
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


# ----- engine Y's own claim_trajectory, read-only --------------------------------------------------------------------

CLAIM = r'''
import json, pathlib, sys
tree, recipe, args = pathlib.Path(sys.argv[1]), sys.argv[2], json.loads(sys.argv[3])
sys.path.insert(0, str(tree))
import experiments.safety_selection as y
assert pathlib.Path(y.__file__).resolve().is_relative_to(tree.resolve()), "not engine Y's tree"
from experiments.safety_selection.config import load_recipe
from experiments.safety_selection.jobs import JobError, claim_trajectory, trajectory_key
key = trajectory_key(args["manifest"], load_recipe(str(tree / recipe)), args["split"], args["arm"], args["seed"],
                     args["role"])
try:
    claim_trajectory(args["registry"], key, args["run_dir"], args["replicate_of"])
    print(json.dumps({"ok": True, "key": key}))
except JobError as exc:
    print(json.dumps({"ok": False, "key": key, "why": str(exc)}))
'''


def y_claim(cwd: Path, registry: str, *, manifest: str, arm: str, seed: int, run_dir: str, replicate_of: str | None,
            split: str = "dev", role: str = "development") -> dict:
    """Engine Y's trajectory_key (on Y's own recipe S) and claim_trajectory, in an isolated interpreter (-I: no
    PYTHONPATH, no user site, no current folder on the path; -B: no bytecode) whose import path starts with Y's tree."""
    args = {"registry": registry, "manifest": manifest, "arm": arm, "seed": seed, "run_dir": run_dir,
            "replicate_of": replicate_of, "split": split, "role": role}
    done = REAL_RUN([PY, "-I", "-B", "-c", CLAIM, str(WS_Y), S, json.dumps(args)], cwd=cwd, capture_output=True,
                    text=True, timeout=120, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0, done.stderr[-800:]
    return json.loads(done.stdout)


@pytest.fixture
def no_y_bytecode():
    """Engine Y's frozen tree gets no new file (no .pyc, no __pycache__)."""
    assert WS_Y.is_dir(), "engine Y's tree (STAGE1_ENGINE_Y_TREE)"
    tree = WS_Y / "experiments"
    before = sorted(map(str, [*tree.rglob("*.pyc"), *tree.rglob("__pycache__")]))
    yield
    assert sorted(map(str, [*tree.rglob("*.pyc"), *tree.rglob("__pycache__")])) == before


def test_engine_y_refuses_c1s_replicate_on_an_empty_registry_and_accepts_it_once_seeded(tmp_path, no_y_bytecode):
    """D2 by engine Y's own code: C1's key (Y's trajectory_key on Y's recipe S, manifest 9ed61826..., R_1's arm, seed
    1101, dev, development) is exactly the lead's hand key (training identity f46279e5...); a replicate_of with no
    registry line refuses and writes nothing; R_1101's line seeded, the claim passes and appends C1's start (key equal,
    replicate_of = R_1101's run folder). The other way twice: a seeded line of another seed, or of another run folder,
    still refuses."""
    c1 = {"manifest": MANIFEST, "arm": R1_ARM, "seed": 1101, "run_dir": "cert/1101-R-c1-a1", "replicate_of": R1101_RUN}
    out = y_claim(tmp_path, REGISTRY, **c1)
    assert out["ok"] is False and out["key"] == C1_KEY
    assert out["why"].startswith(f"replicate_of {R1101_RUN} is not a registered start of this trajectory")
    assert not (tmp_path / REGISTRY).exists()
    seed_line = {"key": C1_KEY, "replicate_of": None, "retry_after_failures": [], "run_dir": R1101_RUN,
                 "utc": "2026-10-16T09:00:00.000+00:00"}
    for wrong in ({**seed_line, "key": {**C1_KEY, "seed": 1102}}, {**seed_line, "run_dir": R1101_RUN[:-1] + "2"}):
        write(tmp_path / REGISTRY, json_line(wrong).decode())
        assert y_claim(tmp_path, REGISTRY, **c1)["ok"] is False
        assert (tmp_path / REGISTRY).read_bytes() == json_line(wrong)           # a refusal appends nothing
    write(tmp_path / REGISTRY, json_line(seed_line).decode())
    out = y_claim(tmp_path, REGISTRY, **c1)
    assert out["ok"] is True and out["key"] == C1_KEY
    lines = (tmp_path / REGISTRY).read_bytes().splitlines(keepends=True)
    assert len(lines) == 2 and lines[0] == json_line(seed_line)
    start = json.loads(lines[1])
    assert (start["key"], start["run_dir"], start["replicate_of"], start["retry_after_failures"]) == (
        C1_KEY, "cert/1101-R-c1-a1", R1101_RUN, [])


# ----- the runner's seed step on the synthetic pod ------------------------------------------------------------------

def cert_pod(kit, tmp_path, monkeypatch, *, claim=True):
    """The cert pod (C1, C2, C3 on engine Y) whose fake engine runs engine Y's real claim_trajectory at C1's run-one,
    with the key Y computes from C1's make-job (the pod's manifest, the edit file's arm, seed, split, role) and the
    make-job's resolved --replicate-of; a refused claim is the run-one's exit 1."""
    r1 = edit_ref("R1")
    tmp_path.mkdir(parents=True, exist_ok=True)
    pod = Pod(kit, tmp_path, monkeypatch, lambda r: [job(r, "cert_c1", "R", 1101, engine="Y", edit=r1, recipe="S"),
                                                     job(r, "cert_c2", "bqi", 1101, engine="Y", recipe="bqi"),
                                                     job(r, "cert_c3", engine="Y", recipe="S")], engine="Y")
    pod.remaining([1000 * base.H])
    pod.claims, made, original = [], {}, pod.run

    def run(args, **kwargs):
        if claim and args[:2] == ["python3", "process_receipt.py"]:
            name, argv = args[3], args[5:]
            if name == "job-0-make-job":
                made["argv"] = argv
            elif name == "job-0-run-one":
                m = made["argv"]
                out = y_claim(pod.root, argv[argv.index("--registry") + 1],
                              manifest=(pod.root / P / "manifest.sha256").read_text().strip(),
                              arm="edit-" + sha(pod.root / m[m.index("--edit") + 1]),
                              seed=int(m[m.index("--seed") + 1]), split=m[m.index("--split") + 1],
                              role=m[m.index("--role") + 1], run_dir=argv[argv.index("--out") + 1],
                              replicate_of=m[m.index("--replicate-of") + 1])
                pod.claims.append(out)
                if not out["ok"]:
                    pod.ran.append(list(args))
                    return subprocess.CompletedProcess(args, 1, "", "")
        return original(args, **kwargs)
    monkeypatch.setattr(pod.runner.subprocess, "run", run)
    return pod


def respec(pod, body) -> None:
    """Replace the packed cert_spec and re-seal (sealed-files.json and the plan's pin), as a re-pack would."""
    write(pod.root / SPEC, body)
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    doc["files"][SPEC] = sha(pod.root / SPEC)
    write(pod.root / "sealed-files.json", doc)
    pod.plan["hosts"]["h-1"]["sealed_files_sha256"] = sha(pod.root / "sealed-files.json")
    write(pod.root / "plan.json", pod.plan)


def test_the_runners_seed_lets_c1s_claim_pass_and_without_it_c1_crashes(kit, tmp_path, monkeypatch, no_y_bytecode):
    """R1 end to end: C1, C2 and C3 complete; engine Y's claim passed once; C1's registry holds exactly R_1101's
    line (the packed record's registry_line, byte for byte in Y's form) and then C1's own start (replicate_of the
    run folder); JOB-0 names the seed by ids and hashes; the registry lies under the light pull. The other way
    (today's runner: the seed step skipped): Y's claim refuses, C1 crashes at its run-one, C2 and C3 never start and
    the registry stays absent."""
    pod = cert_pod(kit, tmp_path / "a", monkeypatch)
    spec = cert_spec(pod.rules)
    assert json.loads((pod.root / SPEC).read_text()) == spec
    assert pod.main() == 0 and pod.statuses() == ["complete", "complete", "complete"]
    assert [c["ok"] for c in pod.claims] == [True]
    lines = (pod.root / REGISTRY).read_bytes().splitlines(keepends=True)
    assert len(lines) == 2 and lines[0] == json_line(spec["registry_line"])
    start = json.loads(lines[1])
    assert (start["key"], start["run_dir"], start["replicate_of"]) == (
        spec["registry_line"]["key"], "cert/1101-R-c1-a1", "round1/1101-R-e1-a1")
    sealed = json.loads((pod.root / "sealed-files.json").read_text())["files"]
    assert pod.done()["jobs"][0]["registry_seed"] == {
        "registry": REGISTRY, "cert_spec": SPEC, "cert_spec_sha256": sealed[SPEC], "replicate_of": "round1/1101-R-e1-a1",
        "line_sha256": hashlib.sha256(lines[0]).hexdigest()}
    assert "registry_seed" not in pod.done()["jobs"][1]
    assert base.pulled(REGISTRY, kit("host.py").PULL_ITEMS)

    other = cert_pod(kit, tmp_path / "b", monkeypatch)
    monkeypatch.setattr(other.runner, "c1_registry_seed", lambda *a: None)
    assert other.main() == 1 and other.statuses() == ["crashed", "not_started", "not_started"]
    assert [c["ok"] for c in other.claims] == [False]
    assert other.done()["jobs"][0]["why"] == "exit 1 in job-0-run-one" and other.done()["stopped"] == "crashed"
    assert not (other.root / REGISTRY).exists()


@pytest.mark.parametrize("change, why", [
    ({"key": {"seed": 1102}}, "cert_spec's registry_line.key is not C1's trajectory key (fields ['seed'])"),
    ({"run_dir": "round1/1101-R-e1-a2"}, "cert_spec's registry_line.run_dir is not its replicate_of"),
    ({"drop": "registry_line"}, "cert_spec holds no registry_line with a key and a run_dir"),
    ({"exists": True}, f"{REGISTRY} exists already; C1's registry must be fresh")])
def test_a_bad_record_crashes_c1_before_any_engine_step(kit, tmp_path, monkeypatch, change, why):
    """R1: a refusal of the seed step through main: C1 is crashed with the check's reason before any step (no
    make-job receipt, so no model ever loads), C2 and C3 are not_started, the host stops, and no registry line is
    written (an existing registry is left as it was)."""
    pod = cert_pod(kit, tmp_path, monkeypatch, claim=False)
    spec = cert_spec(pod.rules, **change.get("key", {}))
    if "run_dir" in change:
        spec["registry_line"]["run_dir"] = change["run_dir"]
    if "drop" in change:
        spec.pop(change["drop"])
    respec(pod, spec)
    if change.get("exists"):
        write(pod.root / REGISTRY, "")
    assert pod.main() == 1 and pod.statuses() == ["crashed", "not_started", "not_started"]
    assert pod.done()["jobs"][0]["why"] == f"job 0 (cert_c1): {why}"
    assert pod.receipts() == [] and pod.done()["stopped"] == "crashed"
    if change.get("exists"):
        assert (pod.root / REGISTRY).read_bytes() == b""
    else:
        assert not (pod.root / REGISTRY).exists()


GOOD = "good"


def seed_case(pod, case: str):
    """(sealed doc, plan) for one check of c1_registry_seed (the record and the pod otherwise good)."""
    r = pod.rules
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    plan = json.loads(json.dumps(pod.plan))
    spec = cert_spec(r)
    key_cases = {"key-arm": {"arm": "edit-" + edit_ref("A1")["sha256"]}, "key-seed": {"seed": 1102},
                 "key-split": {"split": "heldout"}, "key-role": {"role": "selector"},
                 "key-manifest": {"manifest_sha256": "n" * 64}, "key-training": {"training_identity": "0" * 64},
                 "key-extra": {"x": 1}}
    if case in key_cases:
        spec = cert_spec(r, **key_cases[case])
    elif case == "key-missing":
        spec["registry_line"]["key"].pop("role")
    elif case == "plan-manifest":
        plan["prepared"] = {"prepared-kt-dolly-olmo2": "n" * 64}
    elif case == "run-dir":
        spec["registry_line"]["run_dir"] = "round1/1101-R-e1-a2"
    elif case == "no-replicate":
        spec.pop("replicate_of")
    elif case == "empty-replicate":
        spec["replicate_of"] = ""
    elif case == "no-line":
        spec.pop("registry_line")
    elif case == "key-not-object":
        spec["registry_line"]["key"] = "C1"
    elif case == "run-dir-not-text":
        spec["registry_line"]["run_dir"] = None
    elif case == "recipe":
        plan["hosts"]["h-1"]["jobs"][0]["recipe"] = "B"
    if case == "not-packed":
        doc["inputs"].pop("cert_spec")
    elif case == "sha":
        write(pod.root / SPEC, {**spec, "note": "changed after sealing"})
    elif case == "not-json":
        write(pod.root / SPEC, "not a JSON record\n")
        doc["files"][SPEC] = sha(pod.root / SPEC)
    else:
        write(pod.root / SPEC, spec)
        doc["files"][SPEC] = sha(pod.root / SPEC)
    if case == "exists-empty":
        write(pod.root / REGISTRY, "")
    elif case == "exists-line":
        write(pod.root / REGISTRY, json_line(spec["registry_line"]).decode())
    elif case == "exists-link":
        (pod.root / "cert").mkdir(exist_ok=True)
        os.symlink(pod.root / "elsewhere.jsonl", pod.root / REGISTRY)
    return doc, plan


REFUSALS = {
    "not-packed": "the stage-1 input 'cert_spec' is not packed",
    "sha": "cert_spec differs from its packed SHA-256 (sealed-files.json)",
    "not-json": "cert_spec is not a JSON record",
    "no-replicate": "cert_spec names no replicate_of run folder",
    "empty-replicate": "cert_spec names no replicate_of run folder",
    "no-line": "cert_spec holds no registry_line with a key and a run_dir",
    "key-not-object": "cert_spec holds no registry_line with a key and a run_dir",
    "run-dir-not-text": "cert_spec holds no registry_line with a key and a run_dir",
    "run-dir": "cert_spec's registry_line.run_dir is not its replicate_of",
    "recipe": "C1 does not run recipe S, whose training identity C1's key pins",
    "key-arm": "cert_spec's registry_line.key is not C1's trajectory key (fields ['arm'])",
    "key-seed": "cert_spec's registry_line.key is not C1's trajectory key (fields ['seed'])",
    "key-split": "cert_spec's registry_line.key is not C1's trajectory key (fields ['split'])",
    "key-role": "cert_spec's registry_line.key is not C1's trajectory key (fields ['role'])",
    "key-manifest": "cert_spec's registry_line.key is not C1's trajectory key (fields ['manifest_sha256'])",
    "plan-manifest": "cert_spec's registry_line.key is not C1's trajectory key (fields ['manifest_sha256'])",
    "key-training": "cert_spec's registry_line.key is not C1's trajectory key (fields ['training_identity'])",
    "key-extra": "cert_spec's registry_line.key is not C1's trajectory key (fields ['x'])",
    "key-missing": "cert_spec's registry_line.key is not C1's trajectory key (fields ['role'])",
    "exists-empty": f"{REGISTRY} exists already; C1's registry must be fresh",
    "exists-line": f"{REGISTRY} exists already; C1's registry must be fresh",
    "exists-link": f"{REGISTRY} exists already; C1's registry must be fresh"}


@pytest.mark.parametrize("case", [GOOD, *REFUSALS])
def test_every_check_of_the_seed_step_both_ways(kit, tmp_path, monkeypatch, case):
    """R1, each check alone on the same pod: the good record (packed, its SHA-256, replicate_of, registry_line with
    run_dir = replicate_of, recipe S, the key field by field = C1's from the job, the make-job command and the
    runner's constants, no registry yet) writes exactly one line, R_1101's, in engine Y's form, and returns ids and
    hashes; each defect refuses with its reason and writes nothing (an existing registry or link is left as it was)."""
    pod = cert_pod(kit, tmp_path, monkeypatch, claim=False)
    runner = pod.runner
    doc, plan = seed_case(pod, case)
    before = (pod.root / REGISTRY).read_bytes() if (pod.root / REGISTRY).is_file() else None
    if case == GOOD:
        out = runner.c1_registry_seed(plan, "h-1", 0, pod.root, doc)
        line = json_line(cert_spec(pod.rules)["registry_line"])
        assert (pod.root / REGISTRY).read_bytes() == line
        assert out == {"registry": REGISTRY, "cert_spec": SPEC, "cert_spec_sha256": doc["files"][SPEC],
                       "replicate_of": "round1/1101-R-e1-a1", "line_sha256": hashlib.sha256(line).hexdigest()}
        assert runner.c1_key(plan["hosts"]["h-1"]["jobs"][0], runner.job_commands(plan, "h-1", 0, pod.root, {}, doc)[0][1],
                             plan) == cert_spec(pod.rules)["registry_line"]["key"]
        return
    with pytest.raises(runner.Unrunnable) as exc:
        runner.c1_registry_seed(plan, "h-1", 0, pod.root, doc)
    assert str(exc.value) == f"job 0 (cert_c1): {REFUSALS[case]}"
    if case == "exists-link":
        assert (pod.root / REGISTRY).is_symlink() and not (pod.root / "elsewhere.jsonl").exists()
    elif before is not None:
        assert (pod.root / REGISTRY).read_bytes() == before
    else:
        assert not (pod.root / REGISTRY).exists()


def test_the_seed_step_derives_c1s_key_from_the_job_not_from_cert_spec(kit, tmp_path, monkeypatch):
    """R1: the key is the job's and the runner's: a C1 job at another seed (its record not changed) refuses the same
    record, and the dry run (which writes nothing) and check-plan's commands are unchanged by the seed step."""
    pod = cert_pod(kit, tmp_path, monkeypatch, claim=False)
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    plan = json.loads(json.dumps(pod.plan))
    plan["hosts"]["h-1"]["jobs"][0]["seed"] = 1102
    with pytest.raises(pod.runner.Unrunnable, match=r"fields \['seed'\]"):
        pod.runner.c1_registry_seed(plan, "h-1", 0, pod.root, doc)
    assert not (pod.root / REGISTRY).exists()
    cmds = pod.runner.job_commands(pod.plan, "h-1", 0, pod.root, {}, doc)
    assert [c[0] for c in cmds] == ["job-0-make-job", "job-0-run-one"]
    assert cmds[0][1][cmds[0][1].index("--replicate-of") + 1] == "@json:cert_spec:replicate_of"
    assert cmds[1][1][-4:] == ["--out", "cert/1101-R-c1-a1", "--registry", REGISTRY]


# ===== R2: compare_c1.py ============================================================================================

TOOL = KIT / "compare_c1.py"
SENTINEL_TEXTS = ("SENTINEL-U-VALUE", "SENTINEL-ANSWER-TEXT", "SENTINEL-GUARD-LABEL", "0.7319284756", "41.0613")
CODE_X, CODE_Y = "b" * 64, "a" * 64


def load_tool():
    spec = importlib.util.spec_from_file_location("s1kit_compare_c1_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def jsonl(rows) -> str:
    return "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)


def unit_files(side: str) -> dict:
    """A light-pulled unit by hand, with every file name of Gate B's R_1101 unit (no *.safetensors). The two sides
    differ only where they must: job.json's code_sha256, edit path and replicate_of; identity.json's code identity,
    Python and platform; COMPLETE.json's code identity and job hash."""
    c1 = side == "c1"
    code = CODE_Y if c1 else CODE_X
    jobdoc = {"arm": R1_ARM, "code_sha256": code, "edit": f"edits/{R1_ARM[5:]}.edit.json" if c1 else
              "sealed/edits/R_d1.json", "evaluate_bank": "dev", "kind": "run-one", "manifest_sha256": MANIFEST,
              "recipe_sha256": "5" * 64, "replicate_of": R1101_RUN if c1 else None, "resume_from": None,
              "role": "development", "seed": 1101, "split": "dev", "target_checkpoint": "e1", "wall_limit_seconds": None}
    state = {name: {"adapter_fingerprint": f"{k}" * 64, "optimizer_fingerprint": f"{k + 3}" * 64, "step": step,
                    "trajectory_cost": {"steps": step, "train_seconds": 12.5 * step}}
             for k, (name, step) in enumerate((("init", 0), ("q", 8), ("e1", 33)))}
    files = {
        "job.json": jobdoc,
        "identity.json": {"code_sha256": code, "code_files": [{"path": "x.py", "sha256": code}],
                          "python": "3.11.10" if c1 else "3.11.9", "platform": "Linux-6.8" if c1 else "Linux-6.5",
                          "manifest_sha256": MANIFEST, "training_identity": TRAINING,
                          "recipe": {"train": {"lr": 0.0002, "lr_schedule": "constant"}}},
        "plan.json": {"stream": {"seed": 1101, "edit_sha256": R1_ARM[5:]}, "stream_sha256": "6" * 64,
                      "checkpoints": {"init": {"step": 0}, "q": {"step": 8}, "e1": {"step": 33}}},
        "steps.jsonl": jsonl({"step": s, "epoch": 0, "rows": [f"r{s}"], "loss": 2.5 - s / 100, "lr": 0.0002,
                              "seconds": 0.75} for s in (1, 2, 3)),
        "eval/e1/summary.json": {"checkpoint": "e1", "query_loss": {"mean": 41.0613, "n": 2},
                                 "safety": {"u": "SENTINEL-U-VALUE"}, "seconds": 40.0},
        "eval/e1/generations.jsonl": jsonl({"prompt_id": f"p{i}", "text": "SENTINEL-ANSWER-TEXT", "seconds": 0.9}
                                           for i in (1, 2)),
        "eval/e1/samples.jsonl": jsonl({"prompt_id": "p1", "sample_index": i, "text": "SENTINEL-ANSWER-TEXT",
                                        "seconds": 1.1} for i in (0, 1)),
        "eval/e1/guard.jsonl": jsonl({"prompt_id": f"p{i}", "kind": "harm", "label": "SENTINEL-GUARD-LABEL",
                                      "valid": True} for i in (1, 2)),
        "eval/e1/guard_samples.jsonl": jsonl({"prompt_id": "p1", "sample_index": i, "label": "SENTINEL-GUARD-LABEL"}
                                             for i in (0, 1)),
        "eval/e1/harm_scores.jsonl": jsonl([{"answer_id": "p1#g", "loglik": -0.5, "valid": True}]),
        "eval/e1/harm_prompts.jsonl": jsonl([{"prompt_id": "p1", "rate": 0.5}]),
        "eval/e1/arc_utility.jsonl": jsonl([{"item": "a1", "correct": True}]),
        "eval/e1/query_loss.jsonl": jsonl({"query_id": f"q{i}", "loss": 0.7319284756} for i in (1, 2)),
        "edit.json": "edit file r1 (synthetic)\n",
        "COMPLETE.json": {"complete": True, "completed_utc": "2026-10-28T10:00:00Z", "identity": {"code_sha256": code},
                          "job_sha256": ("c" if c1 else "d") * 64, "files": {}},
        "assets.json": {"environment": {"gpu": "A100-SXM4-80GB", "driver": "570" if c1 else "565"}},
        "dependencies.json": {"dependencies": []},
        "environment-linux.lock": "torch==2.8.0\n",
        "ledger.jsonl": jsonl([{"stage": "train", "seconds": 300.0, "start_utc": "2026-10-28T09:00:00Z"}]),
        "progress.jsonl": jsonl([{"kind": "train", "step": 33, "elapsed_s": 310.0}]),
        "records.jsonl": jsonl([{"kind": "checkpoint", "checkpoint": "e1", "utc": "2026-10-28T09:30:00Z"}]),
        "status.json": {"status": "complete", "elapsed_s": 900.0}}
    for name, doc in state.items():
        files[f"states/{name}/state.json"] = doc
    return files


def make_unit(folder: Path, side: str, change=None, drop=()) -> Path:
    files = unit_files(side)
    for rel, value in (change or {}).items():
        files[rel] = value
    for rel in drop:
        files.pop(rel)
    for rel, value in files.items():
        write(folder / rel, value)
    return folder


def pair(tmp_path: Path, c1_change=None, r_change=None, c1_drop=(), r_drop=()) -> tuple[Path, Path]:
    """C1 at .../cert/1101-R-c1-a1 and R_1101 at .../tree/round1/<its run folder> (as on the Mac)."""
    c1 = make_unit(tmp_path / "retrieved/cert-1/tree/cert/1101-R-c1-a1", "c1", c1_change, c1_drop)
    r = make_unit(tmp_path / "gate-b/retrieved/w0a-1/tree" / R1101_RUN, "r1101", r_change, r_drop)
    return c1, r


def run_tool(*args, cwd: Path) -> subprocess.CompletedProcess:
    return REAL_RUN([PY, "-B", str(TOOL), *map(str, args)], cwd=cwd, capture_output=True, text=True, timeout=120,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})


def verdicts(doc: dict) -> dict:
    return {f["file"]: f["verdict"] for f in doc["files"]}


EVERY_FILE = sorted(unit_files("c1"))
NOT_COUNTED = {"COMPLETE.json", "identity.json", "assets.json", "dependencies.json", "environment-linux.lock",
               "ledger.jsonl", "progress.jsonl", "records.jsonl", "status.json"}


def test_compare_c1_two_equal_units_pass_with_the_by_design_differences_outside_the_rule(tmp_path):
    """R2, equal: every file of both units is listed; the counted files (job.json under the removal rule with the
    edit path and C1's replicate_of = R_1101's run folder; plan, steps, the three state records, the nine evaluation
    files, edit.json) are equal; identity.json, COMPLETE.json and assets.json differ by design (code identity,
    environment) and do not count; pass true, exit 0; stdout is the --out file."""
    c1, r = pair(tmp_path)
    out = tmp_path / "c1-certificate-compare.json"
    done = run_tool(c1, r, "--out", out, cwd=tmp_path)
    assert done.returncode == 0 and done.stderr == ""
    doc = json.loads(out.read_text())
    assert done.stdout == out.read_text()
    assert [f["file"] for f in doc["files"]] == EVERY_FILE
    assert {f["file"] for f in doc["files"] if not f["counts"]} == NOT_COUNTED
    want = {rel: "equal" for rel in EVERY_FILE}
    want.update({"identity.json": "differ", "COMPLETE.json": "differ", "assets.json": "differ"})
    assert verdicts(doc) == want
    assert {f["file"]: f["rule"] for f in doc["files"] if f["counts"]} == {
        "job.json": "job", "plan.json": "json", "steps.jsonl": "steps", "edit.json": "bytes",
        **{f"states/{s}/state.json": "state-record" for s in ("init", "q", "e1")},
        **{rel: "eval" for rel in EVERY_FILE if rel.startswith("eval/")}}
    assert (doc["pass"], doc["both_complete"], doc["x6"]) == (True, True, {"u_labels": "equal", "task_loss": "equal"})
    assert (doc["kind"], doc["version"], doc["c1_unit"], doc["r1101_unit"]) == (
        "stage1 c1 certificate comparison", 1, str(c1.resolve()), str(r.resolve()))
    assert doc["rule"] == {"removal_digest": "experiments/safety_selection/tests/removal_digest.py",
                           "removal_digest_sha256": sha(REPO / doc["rule"]["removal_digest"]),
                           "compare_c1_sha256": sha(TOOL)}
    assert sha(REPO / "experiments/safety_selection/tests/removal_digest.py") == \
        "59a713f02ddb74dd60f337077170cc240b24ccbe634a7fe67cfda0493a58da8a"


@pytest.mark.parametrize("rel, x6", [("eval/e1/guard.jsonl", {"u_labels": "differ", "task_loss": "equal"}),
                                     ("eval/e1/query_loss.jsonl", {"u_labels": "equal", "task_loss": "differ"}),
                                     ("eval/e1/summary.json", {"u_labels": "equal", "task_loss": "equal"}),
                                     ("eval/e1/generations.jsonl", {"u_labels": "equal", "task_loss": "equal"}),
                                     ("eval/e1/arc_utility.jsonl", {"u_labels": "equal", "task_loss": "equal"}),
                                     ("states/e1/state.json", {"u_labels": "equal", "task_loss": "equal"}),
                                     ("steps.jsonl", {"u_labels": "equal", "task_loss": "equal"})])
def test_one_changed_byte_in_a_counted_file_fails_the_certificate(tmp_path, rel, x6):
    """R2, one byte different: one character of a value (never a timed key) changed in C1's copy of a counted file;
    that file alone differs among the counted ones, pass false, exit 1 (the file is still written); X-6's verdicts
    follow the guard and query-loss files."""
    files = unit_files("c1")
    text = files[rel] if isinstance(files[rel], str) else json.dumps(files[rel], indent=1, sort_keys=True) + "\n"
    for old, new in (("SENTINEL-GUARD-LABEL", "SENTINEL-GUARD-LABEX"), ("0.7319284756", "0.7319284757"),
                     ("SENTINEL-U-VALUE", "SENTINEL-U-VALUF"), ("SENTINEL-ANSWER-TEXT", "SENTINEL-ANSWER-TEXU"),
                     ('"correct": true', '"correct": false'), ('"step": 33', '"step": 34'),
                     ('"loss": 2.49', '"loss": 2.48')):
        if old in text:
            text = text.replace(old, new, 1)
            break
    assert text != (files[rel] if isinstance(files[rel], str) else json.dumps(files[rel], indent=1, sort_keys=True)
                    + "\n")
    c1, r = pair(tmp_path, c1_change={rel: text})
    out = tmp_path / "out.json"
    done = run_tool(c1, r, "--out", out, cwd=tmp_path)
    doc = json.loads(out.read_text())
    assert done.returncode == 1 and doc["pass"] is False and doc["x6"] == x6
    assert [f["file"] for f in doc["files"] if f["counts"] and f["verdict"] != "equal"] == [rel]


def test_a_timing_only_difference_still_passes_and_a_non_timed_one_does_not(tmp_path):
    """R2, timing only: every TIMED key removal_digest strips changed in C1 (steps' and generations' seconds, the
    summary's seconds, the states' train_seconds, the ledger's seconds and start_utc, progress elapsed_s, status
    elapsed_s, COMPLETE's completed_utc) and the code identity in job.json: pass true. The other way: the same
    change under a key that is not TIMED (a step's loss) fails steps.jsonl."""
    files = unit_files("c1")
    change = {
        "steps.jsonl": files["steps.jsonl"].replace('"seconds": 0.75', '"seconds": 0.5'),
        "eval/e1/generations.jsonl": files["eval/e1/generations.jsonl"].replace('"seconds": 0.9', '"seconds": 2.0'),
        "eval/e1/samples.jsonl": files["eval/e1/samples.jsonl"].replace('"seconds": 1.1', '"seconds": 3.3'),
        "eval/e1/summary.json": {**files["eval/e1/summary.json"], "seconds": 55.5},
        "states/e1/state.json": {**files["states/e1/state.json"],
                                 "trajectory_cost": {"steps": 33, "train_seconds": 999.0}},
        "ledger.jsonl": jsonl([{"stage": "train", "seconds": 1.0, "start_utc": "2026-10-29T01:00:00Z"}]),
        "progress.jsonl": jsonl([{"kind": "train", "step": 33, "elapsed_s": 1.0}]),
        "status.json": {"status": "complete", "elapsed_s": 1.0},
        "records.jsonl": jsonl([{"kind": "checkpoint", "checkpoint": "e1", "utc": "2026-10-29T02:00:00Z"}]),
        "job.json": {**files["job.json"], "code_sha256": "e" * 64}}
    c1, r = pair(tmp_path / "a", c1_change=change)
    done = run_tool(c1, r, "--out", tmp_path / "a.json", cwd=tmp_path)
    doc = json.loads((tmp_path / "a.json").read_text())
    assert done.returncode == 0 and doc["pass"] is True
    assert {rel for rel, v in verdicts(doc).items() if v != "equal"} == {"identity.json", "COMPLETE.json", "assets.json"}
    c1, r = pair(tmp_path / "b", c1_change={"steps.jsonl": files["steps.jsonl"].replace('"loss": 2.49', '"loss": 2.5')})
    done = run_tool(c1, r, "--out", tmp_path / "b.json", cwd=tmp_path)
    doc = json.loads((tmp_path / "b.json").read_text())
    assert done.returncode == 1 and verdicts(doc)["steps.jsonl"] == "differ" and doc["pass"] is False


@pytest.mark.parametrize("c1_drop, r_drop, missing, passes", [
    (("eval/e1/samples.jsonl",), (), "eval/e1/samples.jsonl", False),        # C1 lacks an evaluation file
    ((), ("eval/e1/arc_utility.jsonl",), "eval/e1/arc_utility.jsonl", False),  # R_1101 lacks one
    (("states/q/state.json",), (), "states/q/state.json", False),
    ((), ("steps.jsonl",), "steps.jsonl", False),
    (("eval/e1/summary.json",), ("eval/e1/summary.json",), "eval/e1/summary.json", False),   # a core file in neither
    (("status.json",), (), "status.json", True)])                              # not counted: listed, pass kept
def test_a_missing_file_is_named_and_fails_only_when_it_counts(tmp_path, c1_drop, r_drop, missing, passes):
    """R2, missing: a file present in one unit only (or a core file in neither) is named "missing"; a counted one
    fails the certificate, a file outside the rule does not."""
    c1, r = pair(tmp_path, c1_drop=c1_drop, r_drop=r_drop)
    done = run_tool(c1, r, "--out", tmp_path / "out.json", cwd=tmp_path)
    doc = json.loads((tmp_path / "out.json").read_text())
    assert verdicts(doc)[missing] == "missing" and doc["pass"] is passes and done.returncode == (0 if passes else 1)
    assert [rel for rel, v in verdicts(doc).items() if v == "missing"] == [missing]


@pytest.mark.parametrize("case", ["c1-other-folder", "c1-null", "r1101-not-null", "swapped", "c1-other-arm",
                                  "error-txt", "no-complete"])
def test_job_json_replicate_rule_and_completeness_both_ways(tmp_path, case):
    """R2, job.json and completeness: C1's replicate_of must be R_1101's run-folder string and R_1101's null (the
    equal case passes above); C1 naming another folder or none, R_1101 naming one, the units given in the wrong
    order, or another arm fail job.json; an error.txt or a missing COMPLETE.json fails the pass (both_complete)."""
    c1_job = unit_files("c1")["job.json"]
    r_job = unit_files("r1101")["job.json"]
    c1_change, r_change, c1_drop, r_drop = {}, {}, (), ()
    if case == "c1-other-folder":
        c1_change = {"job.json": {**c1_job, "replicate_of": R1101_RUN[:-1] + "2"}}
    elif case == "c1-null":
        c1_change = {"job.json": {**c1_job, "replicate_of": None}}
    elif case == "r1101-not-null":
        r_change = {"job.json": {**r_job, "replicate_of": R1101_RUN}}
    elif case == "c1-other-arm":
        c1_change = {"job.json": {**c1_job, "arm": "edit-" + "7" * 64}}
    elif case == "error-txt":
        c1_change = {"error.txt": "Traceback (synthetic)\n"}
    elif case == "no-complete":
        r_drop = ("COMPLETE.json",)
    c1, r = pair(tmp_path, c1_change, r_change, c1_drop, r_drop)
    if case == "swapped":
        c1, r = r, c1
    done = run_tool(c1, r, "--out", tmp_path / "out.json", cwd=tmp_path)
    doc = json.loads((tmp_path / "out.json").read_text())
    assert done.returncode == 1 and doc["pass"] is False
    if case in ("error-txt", "no-complete"):
        assert doc["both_complete"] is False
        assert all(f["verdict"] == "equal" for f in doc["files"] if f["counts"])
    else:
        assert doc["both_complete"] is True and verdicts(doc)["job.json"] == "differ"


def test_the_output_holds_no_value_label_answer_count_or_unit_hash(tmp_path):
    """R2, seal-safety: on a passing and on a failing pair the output (stdout = the --out file) holds none of the
    sentinel values, labels or answer texts, no SHA-256 of any unit file, only the listed keys, and each file entry
    only its name, rule, counts and verdict."""
    for name, change in (("pass", {}), ("fail", {"eval/e1/guard.jsonl": "{}\n"})):
        c1, r = pair(tmp_path / name, c1_change=change)
        out = tmp_path / f"{name}.json"
        done = run_tool(c1, r, "--out", out, cwd=tmp_path)
        text = out.read_text()
        assert done.stdout == text and done.stderr == ""
        assert not [s for s in SENTINEL_TEXTS if s in text]
        hashes = {sha(p) for u in (c1, r) for p in u.rglob("*") if p.is_file()}
        assert not [h for h in hashes if h in text]
        doc = json.loads(text)
        assert set(doc) == {"kind", "version", "c1_unit", "r1101_unit", "rule", "both_complete", "files", "x6", "pass"}
        assert all(set(f) == {"file", "rule", "counts", "verdict"} and f["verdict"] in ("equal", "differ", "missing")
                   for f in doc["files"])


def test_compare_c1_refuses_and_writes_nothing(tmp_path, monkeypatch):
    """R2, refusals (exit 2, nothing written, an existing file kept): --out exists; --out inside either unit; --out's
    folder missing; a unit that is not a folder; the same folder twice; removal_digest.py not its pin (in process: a
    changed copy refuses, the pinned file loads)."""
    c1, r = pair(tmp_path)
    keep = write(tmp_path / "exists.json", "kept\n")
    for args in ((c1, r, "--out", keep), (c1, r, "--out", c1 / "out.json"), (c1, r, "--out", r / "eval/out.json"),
                 (c1, r, "--out", tmp_path / "no-folder/out.json"), (c1 / "job.json", r, "--out", tmp_path / "x.json"),
                 (c1, tmp_path / "absent", "--out", tmp_path / "x.json"), (c1, c1, "--out", tmp_path / "x.json")):
        done = run_tool(*args, cwd=tmp_path)
        assert done.returncode == 2 and done.stdout == "" and done.stderr.startswith("compare_c1: refused: "), args
    assert keep.read_text() == "kept\n"
    assert not (c1 / "out.json").exists() and not (r / "eval/out.json").exists() and not (tmp_path / "x.json").exists()
    tool = load_tool()
    assert tool.load_rule().TIMED == {"seconds", "train_seconds", "elapsed_s", "start_s", "end_s", "start_utc",
                                      "end_utc", "updated_utc", "completed_utc", "utc"}
    changed = write(tmp_path / "removal_digest.py",
                    (REPO / "experiments/safety_selection/tests/removal_digest.py").read_text() + "# changed\n")
    with pytest.raises(tool.Refused):
        tool.load_rule(changed)
    monkeypatch.setattr(tool, "REMOVAL_DIGEST", changed)
    assert tool.main([str(c1), str(r), "--out", str(tmp_path / "y.json")]) == 2
    assert not (tmp_path / "y.json").exists()


def test_compare_c1_reads_units_as_removal_digest_does(tmp_path):
    """R2 against the rule itself: for a pair with timing changes and one changed evaluation file, each counted
    plan, steps, state-record and evaluation verdict is "equal" exactly when removal_digest.unit_digest's entry for it
    is equal on the two units."""
    files = unit_files("c1")
    c1, r = pair(tmp_path, c1_change={
        "eval/e1/harm_prompts.jsonl": jsonl([{"prompt_id": "p1", "rate": 0.25}]),
        "eval/e1/generations.jsonl": files["eval/e1/generations.jsonl"].replace('"seconds": 0.9', '"seconds": 7.0'),
        "states/q/state.json": {**files["states/q/state.json"], "adapter_fingerprint": "9" * 64}})
    tool = load_tool()
    rule = tool.load_rule()
    doc = tool.compare(c1, r, rule)
    left, right = rule.unit_digest(c1), rule.unit_digest(r)
    seen = verdicts(doc)
    for name in left["eval"]:
        assert (seen[f"eval/{name}"] == "equal") is (left["eval"][name] == right["eval"][name]), name
    for name in left["states"]:
        assert (seen[f"states/{name}/state.json"] == "equal") is (left["states"][name] == right["states"][name])
    assert (seen["plan.json"] == "equal") is (left["plan"] == right["plan"])
    assert (seen["steps.jsonl"] == "equal") is (left["steps"] == right["steps"])
    assert [rel for rel, v in seen.items() if v == "differ" and rel not in NOT_COUNTED] == [
        "eval/e1/harm_prompts.jsonl", "states/q/state.json"]
    assert left["job"] != right["job"] and seen["job.json"] == "equal"   # the rule's job digest keeps the edit path
