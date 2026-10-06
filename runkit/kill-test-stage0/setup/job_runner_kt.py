"""One kill-test Stage 0 job on one host (runs on the pod, after its bootstrap and preflight).

    venv/bin/python job_runner_kt.py HOST [--dry-run]

Checks, in order, stopping at the first failure (v2's job_runner.py):
  - BOOTSTRAP-READY.json and PREFLIGHT-DONE.json say ok, and the preflight's recipe is the plan's recipe;
  - this host's two-step fixture equals the expected fixture recorded on the first host (expected-fixture-kt.json):
    plan["fixture_compare"] keys and resume keys;
  - engine code, recipe and the host's prepared manifest equal the plan.
Then the engine steps (``engine_steps``), each its own engine process under a process receipt:
  - a ``base_eval`` host whose preflight found ``init_equals_untuned``: the untuned baseline first, as the seeded
    adapter's init unit (make-job, then run-one into round1/1101-a0-init-a1 with the round's registry; receipts
    job-process-base-job-SEED and job-process-base-SEED), then ``calibrate --base-eval``, which reuses that unit
    (its stored job equals calibrate's own: same fields, code pinned, no wall limit) and trains a0 to e3;
  - a ``base_eval`` host whose preflight did not find it: no baseline; plain calibrate; JOB-DONE.json records why;
  - any other host: plain calibrate (a0 of its seed at e3).
Then the engine's own verify of every sealed unit. JOB-DONE.json records the outcome. ``--dry-run`` prints the
engine commands and checks nothing.
"""
import datetime as dt, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path("/workspace/attribution-headroom")
ENGINE = ["venv/bin/python", "-m", "experiments.safety_selection"]


def engine_steps(plan: dict, host: str, init_equals_untuned: bool | None) -> tuple[list[tuple[str, list[str]]], str | None]:
    """(receipt name, engine arguments) in order, and the reason the baseline was skipped (or None)."""
    job, recipe = plan["hosts"][host], plan["recipe_path"]
    prepared, seed = job["prepared"], str(job["seed"])
    calibrate = ["calibrate", "--prepared", prepared, "--recipe", recipe, "--arms", job["arm"], "--seeds", seed,
                 "--checkpoints", ",".join(plan["checkpoints"]), "--out-root", "round1"]
    if not job.get("base_eval"):
        return [(f"job-process-{seed}", calibrate)], None
    if init_equals_untuned is not True:
        return [(f"job-process-{seed}", calibrate)], "the preflight did not find init_equals_untuned: no baseline unit"
    assert job["arm"] == "a0", "the baseline is a0's init unit"
    make = ["make-job", "run-one", "--prepared", prepared, "--recipe", recipe, "--out", "base-job.json", "--split", "dev",
            "--arm", "a0", "--seed", seed, "--role", "development", "--target", "init", "--bank", "dev", "--pin-code"]
    run = ["run-one", "--job", "base-job.json", "--prepared", prepared, "--recipe", recipe,
           "--out", f"round1/{seed}-a0-init-a1", "--registry", "round1/registry.jsonl"]
    return [(f"job-process-base-job-{seed}", make), (f"job-process-base-{seed}", run),
            (f"job-process-{seed}", calibrate + ["--base-eval"])], None


def main() -> int:
    host, dry = sys.argv[1], "--dry-run" in sys.argv[2:]
    if not dry:                                           # a dry run reads plan.json in the current folder
        os.chdir(ROOT)
    plan = json.loads(pathlib.Path("plan.json").read_text())
    job = plan["hosts"][host]
    assert job["role"] in ("job", "first"), "not a job host"
    if dry:
        pre = json.loads(pathlib.Path("PREFLIGHT-DONE.json").read_text()) if pathlib.Path("PREFLIGHT-DONE.json").exists() else {}
        steps, skipped = engine_steps(plan, host, pre.get("init_equals_untuned"))
        print(json.dumps({"steps": [[name, ENGINE + args] for name, args in steps], "baseline_skipped": skipped}, indent=1))
        return 0
    assert not pathlib.Path("JOB-DONE.json").exists(), "this host already ran its job"
    assert json.loads(pathlib.Path("BOOTSTRAP-READY.json").read_text())["ok"] is True, "bootstrap not ready"
    pre = json.loads(pathlib.Path("PREFLIGHT-DONE.json").read_text())
    assert pre["ok"] is True and pre["recipe"] == plan["recipe_path"], "the preflight did not pass for the plan's recipe"
    x = json.loads(pathlib.Path(pre["folder"], "verification.json").read_text())
    e = json.loads(pathlib.Path("expected-fixture-kt.json").read_text())
    for key in plan["fixture_compare"]["equal_keys"]:
        assert x[key] == e[key], f"fixture differs from the first host's: {key}"
    for key in plan["fixture_compare"]["resume_keys"]:
        assert x["resume"][key] == e["resume"][key], f"fixture differs from the first host's: resume.{key}"

    from experiments.safety_selection.common import code_identity
    from experiments.safety_selection.config import config_sha256, load_recipe

    assert code_identity()["sha256"] == plan["engine_sha256"], "engine code differs from the plan"
    assert config_sha256(load_recipe(plan["recipe_path"])) == plan["recipe_sha256"], "recipe differs from the plan"
    prepared = job["prepared"]
    assert pathlib.Path(prepared, "manifest.sha256").read_text().strip() == plan["prepared"][prepared], \
        "prepared data differ from the plan"
    env = {**os.environ, "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
           "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(ROOT), "HF_HUB_OFFLINE": "1"}
    steps, skipped = engine_steps(plan, host, pre.get("init_equals_untuned"))
    pathlib.Path("round1").mkdir(exist_ok=True)
    exits = {}
    for name, args in steps:
        run = subprocess.run(["python3", "process_receipt.py", "--out", name, "--", *ENGINE, *args], env=env)
        exits[name] = run.returncode
        if run.returncode:
            break                                         # a later step never runs after a failed one
    verified = {}
    for unit in sorted(p.parent for p in pathlib.Path("round1").glob("*/COMPLETE.json")):
        check = subprocess.run([*ENGINE, "verify", "--run", str(unit), "--prepared", prepared], env=env,
                               capture_output=True, text=True)
        verified[unit.name] = {"exit": check.returncode, "tail": (check.stdout + check.stderr)[-600:]}
    expected_units = {f"{job['seed']}-a0-e3-a1"} | ({f"{job['seed']}-a0-init-a1"} if len(steps) == 3 else set())
    done = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "host": host, "step_exits": exits,
            "baseline_skipped": skipped, "init_equals_untuned": pre.get("init_equals_untuned"), "verified": verified,
            "ok": len(exits) == len(steps) and all(code == 0 for code in exits.values())
            and expected_units <= set(verified) and all(v["exit"] == 0 for v in verified.values())}
    pathlib.Path("JOB-DONE.json").write_text(json.dumps(done, indent=2) + "\n")
    print(json.dumps(done), flush=True)
    return 0 if done["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
