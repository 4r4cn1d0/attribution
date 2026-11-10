"""One family probe's job on its host (runs on the pod, after the bootstrap and the preflight; brief Item 6).

    venv/bin/python job_runner_probe.py HOST [--dry-run]

The checks of job_runner_kt.py (bootstrap and preflight ok and for the plan's recipe, the fixture equal to the expected
one, engine code, recipe and prepared manifest equal to the plan), plus no token variable or token file. Then:
  - **no baseline, no probe**: if the preflight's init_equals_untuned is not true, no unit runs; JOB-DONE.json records
    stopped: init_not_proven_equal_to_untuned (the finisher stops the pod; the lead decides);
  - otherwise the untuned baseline in its own process (make-job, run-one into round1/1101-a0-init-a1 with the round's
    registry), then calibrate --base-eval --checkpoints e1, which reuses it and trains a0 to e1;
  - **CAP-CHECK.json** after the init unit: its measured evaluation seconds and capped count, and the projected e1
    upper (every batch capped, at the preflight's ms_per_step_full, plus the init unit's measured non-generation
    stages, the preflight's training projection and half its job overhead, the e1 process's share) against the
    remaining cap; cap_risk when under 30 min would remain. **A cap risk refuses e1** (review fix 9): calibrate does
    not run, JOB-DONE.json records stopped: cap_check_refused, and the finisher pulls the baseline and stops the pod;
  - with base_eval false (GI III round 5, baseline reuse): only calibrate --checkpoints e1 (no --base-eval), no
    CAP-CHECK (it needs the init unit); the plan's baseline_reuse names the sealed untuned unit the reading pairs with;
  - the engine's verify of every sealed unit; JOB-DONE.json;
  - last, **the stop is shortened** to 1 h from now with extend_cap.py, only when more than 1 h remains (never longer).
--dry-run prints the engine commands (or the stop reason) and writes nothing.
"""
import datetime as dt, json, math, os, pathlib, subprocess, sys

ROOT = pathlib.Path("/workspace/attribution-headroom")
HEARTBEAT = pathlib.Path("/workspace/.pod-timer/heartbeat.json")
ENGINE = ["venv/bin/python", "-m", "experiments.safety_selection"]
TOKEN_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
STOPPED = "init_not_proven_equal_to_untuned"
CAP_REFUSED = "cap_check_refused"
GREEDY_PROMPTS, HARM_SAMPLES = 468, 600
GENERATION_STAGES = ("generate", "sample")
EVALUATION_STAGES = ("query_loss", "generate", "sample", "arc_utility", "guard", "guard_samples", "harm_scores")
SHORTEN_TO_S = 3600
RISK_MARGIN_S = 1800


def engine_steps(plan: dict, host: str, init_equals_untuned) -> tuple[list[tuple[str, list[str]]], str | None]:
    """(receipt name, engine arguments) in order, or no step and the reason the probe stops."""
    if init_equals_untuned is not True:
        return [], STOPPED
    job, recipe = plan["hosts"][host], plan["recipe_path"]
    prepared, seed = job["prepared"], str(job["seed"])
    if job.get("base_eval") is False:          # GI III round 5: fine-tune only; the plan names a reused baseline
        calibrate = ["calibrate", "--prepared", prepared, "--recipe", recipe, "--arms", "a0", "--seeds", seed,
                     "--checkpoints", ",".join(plan["checkpoints"]), "--out-root", "round1"]
        return [(f"job-process-{seed}", calibrate)], None
    make = ["make-job", "run-one", "--prepared", prepared, "--recipe", recipe, "--out", "base-job.json", "--split", "dev",
            "--arm", "a0", "--seed", seed, "--role", "development", "--target", "init", "--bank", "dev", "--pin-code"]
    run = ["run-one", "--job", "base-job.json", "--prepared", prepared, "--recipe", recipe,
           "--out", f"round1/{seed}-a0-init-a1", "--registry", "round1/registry.jsonl"]
    calibrate = ["calibrate", "--prepared", prepared, "--recipe", recipe, "--arms", "a0", "--seeds", seed,
                 "--checkpoints", ",".join(plan["checkpoints"]), "--out-root", "round1", "--base-eval"]
    return [(f"job-process-base-job-{seed}", make), (f"job-process-base-{seed}", run), (f"job-process-{seed}", calibrate)], None


def cap_check(stage_seconds: dict, capped: int, ms_per_step_full: float, batch: int, training_s: float,
              remaining_s: float, overhead_s: float = 0.0) -> dict:
    """The projected e1 upper after the init unit, against the remaining cap; a cap risk refuses e1."""
    batches = math.ceil(GREEDY_PROMPTS / batch) + math.ceil(HARM_SAMPLES / batch)
    other = sum(v for k, v in stage_seconds.items() if k not in GENERATION_STAGES)
    upper = ms_per_step_full / 1000 * 2049 * batches + other + training_s + overhead_s / 2
    risk = remaining_s - upper < RISK_MARGIN_S
    return {"init_evaluation_s": sum(stage_seconds.values()), "init_capped": capped, "projected_e1_upper_s": upper,
            "remaining_s": remaining_s, "cap_risk": risk, "e1_refused": risk}


def shorten(remaining_s: float | None) -> bool:
    """Shorten the stop to SHORTEN_TO_S from now only when more remains: it never extends."""
    return remaining_s is not None and remaining_s > SHORTEN_TO_S


def remaining(now: dt.datetime) -> float | None:
    if not HEARTBEAT.exists():
        return None
    stop = json.loads(HEARTBEAT.read_text())["governing"]["stop_at_utc"]
    return (dt.datetime.fromisoformat(stop.replace("Z", "+00:00")) - now).total_seconds()


def init_measurements(unit: pathlib.Path) -> tuple[dict, int]:
    seconds = {}
    for line in (unit / "ledger.jsonl").read_text().splitlines():
        record = json.loads(line)
        if record.get("stage") in EVALUATION_STAGES and record.get("seconds") is not None:
            seconds[record["stage"]] = seconds.get(record["stage"], 0.0) + record["seconds"]
    summary = json.loads((unit / "eval" / "init" / "summary.json").read_text())
    capped = sum((summary.get(k) or {}).get("policy_capped", 0) for k in ("safety", "arc_generation", "overrefusal"))
    capped += summary.get("harm", {}).get("greedy", {}).get("policy_capped", 0) + (summary.get("harm", {}).get("sampled") or {}).get("capped", 0)
    return seconds, capped


def main(argv=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    host, dry = args[0], "--dry-run" in args[1:]
    if not dry:
        os.chdir(ROOT)
    plan = json.loads(pathlib.Path("plan.json").read_text())
    job = plan["hosts"][host]
    assert job["role"] in ("job", "first"), "not a job host"
    pre = json.loads(pathlib.Path("PREFLIGHT-DONE.json").read_text()) if pathlib.Path("PREFLIGHT-DONE.json").exists() else {}
    steps, stopped = engine_steps(plan, host, pre.get("init_equals_untuned"))
    if dry:
        print(json.dumps({"steps": [[name, ENGINE + a] for name, a in steps], "stopped": stopped}, indent=1))
        return 0
    present = [name for name in TOKEN_ENV_NAMES if os.environ.get(name)]
    assert not present and not (pathlib.Path.home() / ".cache/huggingface/token").exists(), "a token is present"
    assert not pathlib.Path("JOB-DONE.json").exists(), "this host already ran its job"
    assert json.loads(pathlib.Path("BOOTSTRAP-READY.json").read_text())["ok"] is True, "bootstrap not ready"
    assert pre["ok"] is True and pre["recipe"] == plan["recipe_path"], "the preflight did not pass for the plan's recipe"
    x = json.loads(pathlib.Path(pre["folder"], "verification.json").read_text())
    e = json.loads(pathlib.Path("expected-fixture-probe.json").read_text())
    for key in plan["fixture_compare"]["equal_keys"]:
        assert x[key] == e[key], f"fixture differs from the expected one: {key}"
    for key in plan["fixture_compare"]["resume_keys"]:
        assert x["resume"][key] == e["resume"][key], f"fixture differs from the expected one: resume.{key}"

    from experiments.safety_selection.common import code_identity
    from experiments.safety_selection.config import config_sha256, load_recipe

    assert code_identity()["sha256"] == plan["engine_sha256"], "engine code differs from the plan"
    assert config_sha256(load_recipe(plan["recipe_path"])) == plan["recipe_sha256"], "recipe differs from the plan"
    prepared = job["prepared"]
    assert pathlib.Path(prepared, "manifest.sha256").read_text().strip() == plan["prepared"][prepared], \
        "prepared data differ from the plan"
    env = {k: v for k, v in os.environ.items() if k not in TOKEN_ENV_NAMES}
    env.update({"CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
                "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(ROOT), "HF_HUB_OFFLINE": "1"})
    pathlib.Path("round1").mkdir(exist_ok=True)
    exits = {}
    stopped_reason = stopped
    for name, step_args in steps:
        run = subprocess.run(["python3", "process_receipt.py", "--out", name, "--", *ENGINE, *step_args], env=env)
        exits[name] = run.returncode
        if run.returncode:
            break
        if name.startswith("job-process-base-") and not name.startswith("job-process-base-job-"):
            unit = pathlib.Path("round1") / f"{job['seed']}-a0-init-a1"
            stage_seconds, capped = init_measurements(unit)
            check = cap_check(stage_seconds, capped, pre["ms_per_step_full"], pre["generation_batch"], pre.get("training_s") or 0.0,
                              remaining(dt.datetime.now(dt.timezone.utc)) or 0.0, pre.get("overhead_s") or 0.0)
            pathlib.Path("CAP-CHECK.json").write_text(json.dumps({"utc": dt.datetime.now(dt.timezone.utc).isoformat(), **check},
                                                                 indent=2) + "\n")
            if check["e1_refused"]:                    # review fix 9: never start an e1 run the cap would likely kill
                stopped_reason = CAP_REFUSED
                break
    verified = {}
    for unit in sorted(p.parent for p in pathlib.Path("round1").glob("*/COMPLETE.json")):
        check = subprocess.run([*ENGINE, "verify", "--run", str(unit), "--prepared", prepared], env=env,
                               capture_output=True, text=True)
        verified[unit.name] = {"exit": check.returncode, "tail": (check.stdout + check.stderr)[-600:]}
    expected_units = {f"{job['seed']}-a0-{plan['checkpoints'][-1]}-a1"}
    if job.get("base_eval") is not False:
        expected_units.add(f"{job['seed']}-a0-init-a1")
    done = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "host": host, "step_exits": exits, "stopped": stopped_reason,
            "init_equals_untuned": pre.get("init_equals_untuned"), "verified": verified,
            "ok": stopped_reason is None and len(exits) == len(steps) and all(c == 0 for c in exits.values())
            and expected_units <= set(verified) and all(v["exit"] == 0 for v in verified.values())}
    pathlib.Path("JOB-DONE.json").write_text(json.dumps(done, indent=2) + "\n")
    print(json.dumps(done), flush=True)
    left = remaining(dt.datetime.now(dt.timezone.utc))
    if shorten(left):                                   # the last action; never extends
        subprocess.run(["python3", "extend_cap.py", str(SHORTEN_TO_S)])
    return 0 if done["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
