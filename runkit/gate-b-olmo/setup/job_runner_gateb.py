"""The Gate B jobs of one host, in order (runs on the pod after the bootstrap and the preflight; brief B2, B3, B7).

    venv/bin/python job_runner_gateb.py HOST [--dry-run]

Checks first (any failure refuses before a job starts): no token variable or token file; this host has not run
(no JOB-DONE.json); BOOTSTRAP-READY ok; PREFLIGHT-DONE ok for the host's recipe; for a job host, the preflight's
fixture equal to the expected one (wave 0a's, recorded on the Mac); engine code, recipe and prepared manifest equal
to the plan; every file sealed-files.json lists present with its SHA-256, and sealed-files.json itself equal to the
plan's pin. Then each job, in order, one engine process per step under process_receipt.py (B2):
  anchor       scripts/make_anchor_answers.py --prompts LIST --recipe REC --out anchor-N
  arm          calibrate --prepared P --recipe S --arms edit-<sha> --edit FILE --seeds J --checkpoints e1 --out-root round1
  retrain      make-job run-one ... --split dev --arm a0 --seed 1101 --role development --target e1 --pin-code (no --bank,
               so evaluate_bank is null), then run-one --job JOB ... --registry round1/registry.jsonl
  diagnostics  make-job attributes ... --a0-state q=RETRAIN --a0-state e1=RETRAIN --groups <the 8 ids> --anchors A
               --pin-code, attributes, then the two Gate C scripts (all rows; [D8])
Before a job (B3): the governing stop from the pod timer's heartbeat; a missing or unreadable heartbeat stops the host
(``heartbeat_unreadable``; None never fits). The job starts only if the remaining time is at least its requirement
(gateb_rules.requirements: max(plan value, this pod's preflight projection), the retrain linked to its diagnostics);
otherwise this job and every later one are ``deferred``, in order (deferral.json). Before a script or an edit file is
used its SHA-256 is checked against sealed-files.json (and an edit file against its arm). A non-zero exit, or no new
COMPLETE.json, is a crash: the job is ``crashed``, later jobs ``not_started``, and the host stops. Each new unit is
verified by the engine. Per job a record job-done/JOB-<i>.json; at the end JOB-DONE.json (ok: every started job
completed and verified; deferral is not a failure; a heartbeat stop or a refused file is). Last, the stop is
shortened to 1 h from now when more remains (never extended). --dry-run prints every job's commands and writes nothing.
"""
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
for _folder in (HERE, HERE.parent):                 # the pod: beside this script; the kit: one folder up
    if (_folder / "gateb_rules.py").is_file():
        sys.path.insert(0, str(_folder))
        break
import gateb_rules as rules  # noqa: E402

ROOT = pathlib.Path("/workspace/attribution-headroom")
HEARTBEAT = pathlib.Path("/workspace/.pod-timer/heartbeat.json")
ENGINE = ["venv/bin/python", "-m", "experiments.safety_selection"]
SCRIPT = ["venv/bin/python"]
TOKEN_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
ROUND = "round1"
ANCHOR_PROMPTS = "anchors/anchor_prompts.json"        # bundle paths (pack_setup.py writes them there)
ANCHOR_FILE = "anchors/anchor_bank.json"
SEALED_DIR = "sealed"                                 # the SEAL out/ folder in the bundle
ANCHOR_SCRIPT = "scripts/make_anchor_answers.py"
GATE_C_SCRIPTS = ("scripts/gate_c_representation.py", "scripts/gate_c_classifier.py")
EXPECTED_FIXTURE = "expected-fixture-gateb.json"
SHORTEN_TO_S = 3600


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def next_attempt(root: pathlib.Path, prefix: str) -> int:
    """The next unused attempt number N of folders PREFIXN under root (1 when none exists)."""
    parent = (root / prefix).parent
    stem = pathlib.Path(prefix).name
    numbers = [int(p.name[len(stem):]) for p in parent.glob(stem + "*") if p.name[len(stem):].isdigit()] \
        if parent.is_dir() else []
    return max(numbers, default=0) + 1


def unit_groups(plan: dict) -> list[str]:
    return sorted(plan["unit_groups"])


def job_commands(plan: dict, host: str, index: int, root: pathlib.Path, units: dict) -> list[tuple[str, list[str]]]:
    """(receipt name, argv) of job ``index`` (B2). ``units`` maps an earlier job index to its unit folder (a
    diagnostics job reads its retrain's folder; in a dry run the retrain's planned folder)."""
    h = plan["hosts"][host]
    job, recipe, prepared = h["jobs"][index], h["recipe_path"], plan["prepared_name"]
    tag = f"job-{index}"
    if job["kind"] == "anchor":
        n = next_attempt(root, "anchor-")
        return [(f"{tag}-anchor", [*SCRIPT, ANCHOR_SCRIPT, "--prompts", ANCHOR_PROMPTS, "--recipe", recipe,
                                   "--out", f"anchor-{n}"])]
    if job["kind"] == "arm":
        return [(f"{tag}-calibrate", [*ENGINE, "calibrate", "--prepared", prepared, "--recipe", recipe,
                                      "--arms", job["arm"], "--edit", f"{SEALED_DIR}/{job['edit']}",
                                      "--seeds", str(job["seed"]), "--checkpoints", "e1", "--out-root", ROUND])]
    if job["kind"] == "retrain":
        seed = str(job["seed"])
        n = next_attempt(root, f"{ROUND}/{seed}-a0-e1-a")
        job_file, out = f"jobs/retrain-{seed}-a{n}.json", f"{ROUND}/{seed}-a0-e1-a{n}"
        return [(f"{tag}-make-job", [*ENGINE, "make-job", "run-one", "--prepared", prepared, "--recipe", recipe,
                                     "--split", "dev", "--arm", "a0", "--seed", seed, "--role", "development",
                                     "--target", "e1", "--pin-code", "--out", job_file]),
                (f"{tag}-run-one", [*ENGINE, "run-one", "--job", job_file, "--prepared", prepared, "--recipe", recipe,
                                    "--out", out, "--registry", f"{ROUND}/registry.jsonl"])]
    if job["kind"] == "diagnostics":
        seed, retrain = str(job["seed"]), units[job["a0_source"]]
        n = next_attempt(root, f"{ROUND}/{seed}-attributes-a")
        job_file, out = f"jobs/attributes-{seed}-a{n}.json", f"{ROUND}/{seed}-attributes-a{n}"
        common = ["--prepared", prepared, "--recipe", recipe, "--anchors", ANCHOR_FILE,
                  "--groups", ",".join(unit_groups(plan))]                # the A9 scripts' CLI (Part A)
        return [(f"{tag}-make-job", [*ENGINE, "make-job", "attributes", "--prepared", prepared, "--recipe", recipe,
                                     "--split", "dev", "--seed", seed, "--role", "development",
                                     "--a0-state", f"q={retrain}", "--a0-state", f"e1={retrain}",
                                     "--groups", ",".join(unit_groups(plan)), "--anchors", ANCHOR_FILE,
                                     "--pin-code", "--out", job_file]),
                (f"{tag}-attributes", [*ENGINE, "attributes", "--job", job_file, "--prepared", prepared,
                                       "--recipe", recipe, "--out", out]),
                (f"{tag}-representation", [*SCRIPT, GATE_C_SCRIPTS[0], *common,
                                           "--out", f"gatec/representation-a{n}"]),
                (f"{tag}-classifier", [*SCRIPT, GATE_C_SCRIPTS[1], *common, "--out", f"gatec/classifier-a{n}"])]
    raise ValueError(f"unknown job kind {job['kind']!r}")


def planned_unit(plan: dict, host: str, index: int, root: pathlib.Path) -> str | None:
    """The folder a retrain job would write (its run-one --out), for the dry run's diagnostics commands."""
    commands = job_commands(plan, host, index, root, {})
    run = commands[-1][1]
    return run[run.index("--out") + 1] if plan["hosts"][host]["jobs"][index]["kind"] == "retrain" else None


def sealed_paths(job: dict) -> list[str]:
    """The bundle files a job uses, each checked against sealed-files.json before the job starts (B2, B7)."""
    if job["kind"] == "anchor":
        return [ANCHOR_SCRIPT, ANCHOR_PROMPTS]
    if job["kind"] == "arm":
        return [f"{SEALED_DIR}/{job['edit']}"]
    if job["kind"] == "diagnostics":
        return [*GATE_C_SCRIPTS, ANCHOR_FILE]
    return []


def sealed_check(job: dict, sealed: dict, root: pathlib.Path) -> list[str]:
    """Names of the job's files that are not listed or differ from sealed-files.json; an edit file must also hash to
    its arm (edit-<SHA-256 of its bytes>)."""
    bad = []
    for rel in sealed_paths(job):
        path = root / rel
        if rel not in sealed or not path.is_file() or sha(path) != sealed[rel]:
            bad.append(rel)
    if job["kind"] == "arm":
        path = root / SEALED_DIR / job["edit"]
        if not path.is_file() or "edit-" + sha(path) != job["arm"]:
            bad.append(f"{SEALED_DIR}/{job['edit']} (its arm)")
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


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def preflight_checks(plan: dict, host: str, pre: dict, root: pathlib.Path) -> dict:
    """Refuse (AssertionError) before any job unless the pod is the planned one; returns sealed-files.json's map."""
    h = plan["hosts"][host]
    present = [name for name in TOKEN_ENV_NAMES if os.environ.get(name)]
    assert not present and not (pathlib.Path.home() / ".cache/huggingface/token").exists(), "a token is present"
    assert not (root / "JOB-DONE.json").exists(), "this host already ran its jobs"
    assert json.loads((root / "BOOTSTRAP-READY.json").read_text())["ok"] is True, "bootstrap not ready"
    assert pre.get("ok") is True and pre.get("recipe") == h["recipe_path"], "the preflight did not pass for the recipe"
    assert pre.get("cap_projection") or not any(j["kind"] in ("arm", "retrain") for j in h["jobs"]), \
        "no preflight projection for an arm or the retrain"
    if h["role"] == "job":
        x = json.loads((root / pre["folder"] / "verification.json").read_text())
        e = json.loads((root / EXPECTED_FIXTURE).read_text())
        for key in plan["fixture_compare"]["equal_keys"]:
            assert x[key] == e[key], f"fixture differs from the expected one: {key}"
        for key in plan["fixture_compare"]["resume_keys"]:
            assert x["resume"][key] == e["resume"][key], f"fixture differs from the expected one: resume.{key}"
    from experiments.safety_selection.common import code_identity
    from experiments.safety_selection.config import config_sha256, load_recipe
    assert code_identity()["sha256"] == plan["engine_sha256"], "engine code differs from the plan"
    assert config_sha256(load_recipe(str(root / h["recipe_path"]))) == h["recipe_sha256"], "recipe differs from the plan"
    prepared = plan["prepared_name"]
    assert (root / prepared / "manifest.sha256").read_text().strip() == plan["prepared"][prepared], \
        "prepared data differ from the plan"
    assert sha(root / "sealed-files.json") == h["sealed_files_sha256"], "sealed-files.json differs from the plan"
    sealed = json.loads((root / "sealed-files.json").read_text())["files"]
    bad = [rel for rel, digest in sealed.items() if not (root / rel).is_file() or sha(root / rel) != digest]
    assert not bad, f"{len(bad)} sealed file(s) missing or changed"
    return sealed


def run_job(plan: dict, host: str, index: int, root: pathlib.Path, units: dict, env: dict) -> dict:
    """Run one job's steps; the record says complete (with its unit and COMPLETE.json SHA-256) or crashed."""
    job = plan["hosts"][host]["jobs"][index]
    pattern = f"{ROUND}/{job['seed']}-{job['arm']}-e1-a*" if job["kind"] == "arm" else None
    before = complete_attempts(root, pattern) if pattern else set()
    exits = {}
    commands = job_commands(plan, host, index, root, units)
    for name, argv in commands:
        done = subprocess.run(["python3", "process_receipt.py", "--out", name, "--", *argv], env=env, cwd=root)
        exits[name] = done.returncode
        if done.returncode:
            return {"status": "crashed", "why": f"exit {done.returncode} in {name}", "exits": exits}
    unit = None
    if job["kind"] == "arm":
        new = sorted(complete_attempts(root, pattern) - before)
        unit = new[0] if len(new) == 1 else None
    elif job["kind"] in ("retrain", "diagnostics"):        # run-one's or attributes' --out
        step = commands[1][1] if job["kind"] == "diagnostics" else commands[-1][1]
        candidate = step[step.index("--out") + 1]
        unit = candidate if (root / candidate / "COMPLETE.json").is_file() else None
    else:                                                 # anchor: the script's output folder
        folder = commands[0][1][commands[0][1].index("--out") + 1]
        if not (root / folder).is_dir() or not any((root / folder).iterdir()):
            return {"status": "crashed", "why": "no anchor output", "exits": exits}
        return {"status": "complete", "unit": folder, "complete_sha256": None, "exits": exits, "verified": None}
    if unit is None:
        return {"status": "crashed", "why": "no new COMPLETE.json", "exits": exits}
    check = subprocess.run([*ENGINE, "verify", "--run", unit, "--prepared", plan["prepared_name"]], env=env, cwd=root,
                           capture_output=True, text=True)
    record = {"unit": unit, "complete_sha256": sha(root / unit / "COMPLETE.json"), "exits": exits,
              "verified": {"exit": check.returncode, "tail": (check.stdout + check.stderr)[-600:]}}
    if check.returncode:
        return {**record, "status": "crashed", "why": "the engine's verify failed"}
    return {**record, "status": "complete"}


def write_record(root: pathlib.Path, index: int, record: dict) -> None:
    (root / "job-done").mkdir(exist_ok=True)
    (root / "job-done" / f"JOB-{index}.json").write_text(json.dumps(record, indent=2) + "\n")


def main(argv=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    host, dry = args[0], "--dry-run" in args[1:]
    root = pathlib.Path.cwd() if dry else ROOT
    if not dry:
        os.chdir(root)
    plan = json.loads((root / "plan.json").read_text())
    h = plan["hosts"][host]
    assert h["base_eval"] is False, "base_eval must be false on every Gate B host"
    jobs = h["jobs"]
    if dry:
        planned, out = {}, []
        for i, job in enumerate(jobs):
            out.append({"index": i, "kind": job["kind"], "arm": job["arm"], "seed": job["seed"],
                        "commands": [[name, argv] for name, argv in job_commands(plan, host, i, root, planned)]})
            if job["kind"] == "retrain":
                planned[i] = planned_unit(plan, host, i, root)
        print(json.dumps({"host": host, "jobs": out}, indent=1))
        return 0
    pre = json.loads((root / "PREFLIGHT-DONE.json").read_text())
    sealed = preflight_checks(plan, host, pre, root)
    env = {k: v for k, v in os.environ.items() if k not in TOKEN_ENV_NAMES}
    env.update({"CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
                "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(root), "HF_HUB_OFFLINE": "1"})
    (root / ROUND).mkdir(exist_ok=True)
    (root / "jobs").mkdir(exist_ok=True)
    need = rules.requirements(jobs, pre.get("cap_projection") or {})
    records, units, stopped = [], {}, None
    for i, job in enumerate(jobs):
        left = remaining(dt.datetime.now(dt.timezone.utc))
        base = {"index": i, "kind": job["kind"], "arm": job["arm"], "seed": job["seed"], "requirement_s": need[i],
                "remaining_s": left, "utc": utc()}
        bad = sealed_check(job, sealed, root)
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
                rec = {**base, "status": later} if k == i else {"index": k, "kind": jobs[k]["kind"],
                                                                 "arm": jobs[k]["arm"], "seed": jobs[k]["seed"],
                                                                 "requirement_s": need[k], "status": later}
                records.append(rec)
                write_record(root, k, rec)
            if stopped == "deferred":
                (root / "deferral.json").write_text(json.dumps({"utc": utc(), "host": host, "first_deferred": i,
                                                                "remaining_s": left, "requirement_s": need[i],
                                                                "deferred": list(range(i, len(jobs)))}, indent=2) + "\n")
            break
        result = run_job(plan, host, i, root, units, env)
        rec = {**base, **result, "ended_utc": utc()}
        records.append(rec)
        write_record(root, i, rec)
        if result["status"] != "complete":
            stopped = "crashed"
            for k in range(i + 1, len(jobs)):
                later = {"index": k, "kind": jobs[k]["kind"], "arm": jobs[k]["arm"], "seed": jobs[k]["seed"],
                         "requirement_s": need[k], "status": "not_started"}
                records.append(later)
                write_record(root, k, later)
            break
        units[i] = result["unit"]
    started = [r for r in records if r["status"] in ("complete", "crashed")]
    done = {"utc": utc(), "host": host, "jobs": records, "stopped": stopped,
            "ok": stopped in (None, "deferred") and all(r["status"] == "complete" for r in started)}
    (root / "JOB-DONE.json").write_text(json.dumps(done, indent=2) + "\n")
    print(json.dumps({"host": host, "ok": done["ok"], "stopped": stopped,
                      "statuses": [r["status"] for r in records]}), flush=True)
    left = remaining(dt.datetime.now(dt.timezone.utc))
    if shorten(left):                                    # the last action; never extends
        subprocess.run(["python3", "extend_cap.py", str(SHORTEN_TO_S)], cwd=root)
    return 0 if done["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
