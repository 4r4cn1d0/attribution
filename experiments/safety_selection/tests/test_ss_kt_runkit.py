"""The kill-test Stage 0 run kit (runkit/kill-test-stage0/) on CPU, without RunPod: the job runner's engine
commands for a baseline host, the baseline's fallback and a plain host (each parsed by the engine's own CLI),
its dry run, the plan tool's first host and job hosts, and the kit's contents. No script that calls RunPod is
run."""

from __future__ import annotations

import importlib.util
import json
import py_compile
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.safety_selection.__main__ import _parser

ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "runkit" / "kill-test-stage0"
RECIPE = "experiments/safety_selection/configs/study-kt-instruct-r64-mb4-20261006.json"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plan() -> dict:
    hosts = {"s0-1101": {"role": "first", "arm": "a0", "seed": 1101, "prepared": "prepared-kt-dolly", "base_eval": True,
                         "cap_hours": 4.0},
             "s0-1102": {"role": "job", "arm": "a0", "seed": 1102, "prepared": "prepared-kt-dolly", "base_eval": False,
                         "cap_hours": 3.0}}
    return {"recipe_path": RECIPE, "checkpoints": ["e3"], "hosts": hosts}


def test_the_job_runner_runs_the_baseline_first_then_calibrate_with_base_eval():
    runner = load(KIT / "setup" / "job_runner_kt.py", "job_runner_kt")
    steps, skipped = runner.engine_steps(plan(), "s0-1101", True)
    assert skipped is None and [name for name, _ in steps] == ["job-process-base-job-1101", "job-process-base-1101",
                                                                "job-process-1101"]
    make, run, calibrate = (args for _, args in steps)
    assert make == ["make-job", "run-one", "--prepared", "prepared-kt-dolly", "--recipe", RECIPE, "--out", "base-job.json",
                    "--split", "dev", "--arm", "a0", "--seed", "1101", "--role", "development", "--target", "init",
                    "--bank", "dev", "--pin-code"]
    assert run == ["run-one", "--job", "base-job.json", "--prepared", "prepared-kt-dolly", "--recipe", RECIPE,
                   "--out", "round1/1101-a0-init-a1", "--registry", "round1/registry.jsonl"]
    assert calibrate[-1] == "--base-eval" and calibrate[calibrate.index("--checkpoints") + 1] == "e3"
    assert calibrate[calibrate.index("--out-root") + 1] == "round1"
    # the baseline's job must equal calibrate's own to be reused: neither passes a wall limit, both pin the code
    assert not any("--wall-limit-seconds" in args for _, args in steps)
    for _, args in steps:                              # every command parses with the engine's own CLI
        _parser().parse_args(args)


def test_without_init_equals_untuned_and_on_plain_hosts_only_calibrate_runs():
    runner = load(KIT / "setup" / "job_runner_kt.py", "job_runner_kt")
    for verdict in (False, None):
        steps, skipped = runner.engine_steps(plan(), "s0-1101", verdict)
        assert [name for name, _ in steps] == ["job-process-1101"] and "--base-eval" not in steps[0][1]
        assert "init_equals_untuned" in skipped
    steps, skipped = runner.engine_steps(plan(), "s0-1102", True)
    assert skipped is None and [name for name, _ in steps] == ["job-process-1102"]
    assert "--base-eval" not in steps[0][1] and steps[0][1][steps[0][1].index("--seeds") + 1] == "1102"


def test_the_job_runners_dry_run_prints_the_engine_commands(tmp_path):
    (tmp_path / "plan.json").write_text(json.dumps(plan()))
    (tmp_path / "PREFLIGHT-DONE.json").write_text(json.dumps({"ok": True, "init_equals_untuned": True}))
    done = subprocess.run([sys.executable, "-B", str(KIT / "setup" / "job_runner_kt.py"), "s0-1101", "--dry-run"],
                          cwd=tmp_path, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0, done.stderr
    out = json.loads(done.stdout)
    assert [s[0] for s in out["steps"]] == ["job-process-base-job-1101", "job-process-base-1101", "job-process-1101"]
    assert out["steps"][1][1][:3] == ["venv/bin/python", "-m", "experiments.safety_selection"]
    assert not list(tmp_path.glob("JOB-DONE.json"))                          # a dry run writes nothing


def test_the_plan_tool_writes_the_first_host_and_the_job_hosts(monkeypatch):
    constants = load(KIT / "kt_constants.py", "kt_constants")
    assert constants.PREPARED_MANIFEST is None                                # set by the lead after the Mac preparation
    with pytest.raises(SystemExit, match="PREPARED_MANIFEST"):
        constants.prepared()
    monkeypatch.setitem(sys.modules, "kt_constants", constants)
    monkeypatch.setattr(constants, "PREPARED_MANIFEST", "f" * 64)
    tool = load(KIT / "plan_tool.py", "plan_tool")
    first = tool.initial_plan({"engine_sha256": "e" * 64, "git_commit": "c" * 40})
    assert first["hosts"] == {"s0-1101": {"role": "first", "arm": "a0", "seed": 1101, "prepared": "prepared-kt-dolly",
                                          "base_eval": True, "cap_hours": 4.0}}
    assert first["prepared"] == {"prepared-kt-dolly": "f" * 64} and first["first_host_recipes"] == constants.RECIPES
    assert first["checkpoints"] == ["e3"] and "lead" not in json.dumps(first["hosts"])
    assert {h: (j["seed"], j["cap_hours"], j["base_eval"]) for h, j in tool.JOB_HOSTS.items()} == {
        "s0-1102": (1102, 3.0, False), "s0-1103": (1103, 3.0, False)}
    for recipe in constants.RECIPES:
        assert (ROOT / recipe).is_file()


def test_the_kit_holds_its_scripts_only_and_every_script_compiles(tmp_path):
    names = {p.relative_to(KIT).as_posix() for p in KIT.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    assert names == {"account.py", "budget.py", "finisher.py", "host.py", "kt_constants.py", "launch.py", "orchestrate.py",
                     "pack_setup.py", "plan_tool.py", "status.py", "setup/bootstrap_hr.sh", "setup/download_models_kt.py",
                     "setup/extend_cap.py", "setup/job_runner_kt.py", "setup/preflight_kt.py", "setup/setup_and_fetch_hr.sh"}
    for name in names:
        if name.endswith(".py"):
            py_compile.compile(str(KIT / name), cfile=str(tmp_path / "x.pyc"), doraise=True)
    text = "\n".join((KIT / n).read_text() for n in names)
    for gone in ("lead_pipeline", "with-generator", "expected-fixture-v2", "worker-setup-v2", "bundle-v2", "collect-lead"):
        assert gone not in text, gone
    assert "cuda_preflight_killtest.py" in (KIT / "setup" / "preflight_kt.py").read_text()
    assert 'f"attribution-killtest-{host}' in (KIT / "host.py").read_text()
    assert "job-process-*" in (KIT / "host.py").read_text()                     # covers job-process-base-SEED


# ----- review fix F1: a pod never bills idle after a failure before its job (fakes; no network) ---------------


def fake_orchestrate(monkeypatch, fail_at: str | None):
    module = load(KIT / "orchestrate.py", "orchestrate_kt")
    calls, events = [], []
    monkeypatch.setattr(module, "plan", lambda: {"hosts": {"s0-1101": {"role": "first"}}, "recipe_path": RECIPE})
    monkeypatch.setattr(module, "log", lambda host, event, **fields: events.append((event, fields)))
    monkeypatch.setattr(module, "tool", lambda *args: calls.append(args) or subprocess.CompletedProcess(args, 0, "stopped", ""))

    def step(name, result=None):
        def run(*args, **kwargs):
            if name == fail_at:
                raise SystemExit(f"{name} failed")
            return result
        return run

    monkeypatch.setattr(module, "wait_ssh", step("wait-ssh"))
    monkeypatch.setattr(module, "check", step("check"))
    monkeypatch.setattr(module, "bootstrap", step("bootstrap"))
    monkeypatch.setattr(module, "wait_file", step("wait-file", {"engine_sha256": "e" * 64}))
    monkeypatch.setattr(module, "preflight", step("preflight", {"ok": True, "recipe": RECIPE}))
    monkeypatch.setattr(module, "record_first", step("record-first"))
    monkeypatch.setattr(module, "start_job", step("start-job"))
    return module, calls, events


@pytest.mark.parametrize("fail_at", ["wait-ssh", "check", "bootstrap", "preflight", "record-first"])
def test_a_failure_before_the_job_stops_the_pod_and_is_raised(monkeypatch, fail_at):
    module, calls, events = fake_orchestrate(monkeypatch, fail_at)
    with pytest.raises(SystemExit, match=f"{fail_at} failed"):
        module.after_create("s0-1101")
    assert calls == [("stop", "s0-1101")]                                       # stop only, never delete
    failed = [fields for event, fields in events if event == "pre-job-failed"]
    assert len(failed) == 1 and failed[0]["step"] == fail_at and failed[0]["error"] == "SystemExit"
    assert any(event == "pre-job-stop" for event, _ in events)


def test_a_job_that_starts_leaves_the_pod_to_the_finisher(monkeypatch):
    module, calls, events = fake_orchestrate(monkeypatch, None)
    module.after_create("s0-1101")
    assert calls == [] and not any(event == "pre-job-failed" for event, _ in events)


def test_the_budget_counts_a_pod_past_its_cap_at_the_fallback_hours(monkeypatch):
    import datetime as dt

    module = load(KIT / "budget.py", "budget_kt")
    now = dt.datetime(2026, 10, 7, 12, 0, tzinfo=dt.timezone.utc)
    assert module.hours_left(None, now) == module.CAP_FALLBACK_H
    assert module.hours_left("2026-10-07T14:30:00+00:00", now) == pytest.approx(2.5)
    assert module.hours_left("2026-10-07T11:00:00+00:00", now) == module.CAP_FALLBACK_H        # the timer failed
    pods = [{"id": "a", "name": "past-cap", "desiredStatus": "RUNNING", "costPerHr": 1.5},
            {"id": "b", "name": "stopped", "desiredStatus": "EXITED", "costPerHr": 1.5}]
    monkeypatch.setattr(module, "call", lambda method, url, payload=None: pods if method == "GET" else
                        {"data": {"myself": {"clientBalance": 30.0, "currentSpendPerHr": 1.5}}})
    monkeypatch.setattr(module, "caps_by_pod_id", lambda: {"a": "2020-01-01T00:00:00+00:00"})
    projection = module.projection()
    assert projection["committed_upper_usd"] == pytest.approx(module.CAP_FALLBACK_H * 1.5)
    assert [r["name"] for r in projection["running"]] == ["past-cap"]
