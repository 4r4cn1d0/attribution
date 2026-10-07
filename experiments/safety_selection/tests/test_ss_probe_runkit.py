"""The family-probe run kit (runkit/family-probe/; brief multi-family-probe-engine-20261007, Items 5 and 6) on CPU,
without RunPod or Hugging Face: the job runner's commands and its stop without a proven baseline, the plan tool and the
probe table, the download plan through a fake snapshot_download, the token rules (stdin only, no argument list, no
file, no child environment), the launch checks (a broad-scope token warns, a token without gated access refuses), the
budget guard over every kit, extend-cap, the finisher's deadline, pull-failure stop and secret scan, the cap gate and
the cap-risk log, the pack checks and the tokenizer fetch. Every script runs from a copy of the kit in a temporary
folder. Every fake token is built at run time; no token-like literal is written here."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import py_compile
import random
import shutil
import string
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.safety_selection.__main__ import _parser
from experiments.safety_selection.config import load_data_config, load_recipe

ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "runkit" / "family-probe"
KIT_MODULES = ("probe_constants", "probes", "secret_scan", "budget")
FAMILY_CONFIG = {"prepared-kt-dolly-olmo2": "study-kt-data-dolly-olmo2.json",
                 "prepared-kt-dolly-llama3": "study-kt-data-dolly-llama3.json"}
CONFIGS = ROOT / "experiments" / "safety_selection" / "configs"


def fake_token() -> str:
    """A token-shaped string built at run time (never a literal in source)."""
    rng = random.Random(os.getpid())
    return "hf" + "_" + "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(34))


def files_holding(root: Path, needle: str) -> list[str]:
    return [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and needle.encode() in p.read_bytes()]


@pytest.fixture
def kit(tmp_path, monkeypatch):
    """A copy of the kit at tmp/runkit/family-probe (so ROOT = tmp) and a loader of its modules; the kit's helper
    modules are loaded from the copy and removed from sys.modules afterwards."""
    copy = tmp_path / "runkit" / "family-probe"
    monkeypatch.setenv("HF_HUB_DISABLE_TELEMETRY", "1")             # the download scripts set these at import
    monkeypatch.setenv("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
    shutil.copytree(KIT, copy, ignore=shutil.ignore_patterns("__pycache__"))
    monkeypatch.syspath_prepend(str(copy))
    for name in KIT_MODULES:
        monkeypatch.delitem(sys.modules, name, raising=False)
    loaded = {}

    def load(relative: str, name: str | None = None):
        name = name or Path(relative).stem
        spec = importlib.util.spec_from_file_location(f"probe_kit_{name}", copy / relative)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        loaded[name] = module
        return module

    load.root = copy
    yield load
    for name in KIT_MODULES:
        sys.modules.pop(name, None)


def set_probe(monkeypatch, probe: str, manifest: str | None = "f" * 64):
    import probe_constants as pc  # the copy's module (the kit fixture put its folder first on sys.path)
    import probes
    monkeypatch.setattr(pc, "PROBE", probe)
    if manifest:
        monkeypatch.setitem(pc.PREPARED_MANIFESTS, probes.PROBES[probe]["prepared"], manifest)
    return pc, probes


def write_plan(root: Path, probe: str, **host_changes) -> dict:
    import probes
    spec = probes.PROBES[probe]
    host = {"role": "first", "arm": "a0", "seed": 1101, "prepared": spec["prepared"], "base_eval": True,
            "cap_hours": spec["cap_hours"], "preflight_wait_s": spec["preflight_wait_s"],
            "container_disk_gb": spec["container_disk_gb"], "volume_gb": spec["volume_gb"], **host_changes}
    plan = {"probe": probe, "recipe_path": spec["recipes"][0], "checkpoints": ["e1"], "first_host_recipes": spec["recipes"],
            "hosts": {f"{probe}-1101": host}}
    (root / "plan.json").write_text(json.dumps(plan))
    return plan


# ----- the job runner ------------------------------------------------------------------------------------------


def test_the_job_runner_runs_the_baseline_then_calibrate_to_e1(kit):
    runner = kit("setup/job_runner_probe.py")
    import probes
    plan = {"recipe_path": probes.PROBES["olmo2-1b"]["recipes"][0], "checkpoints": ["e1"],
            "hosts": {"olmo2-1b-1101": {"role": "first", "arm": "a0", "seed": 1101, "prepared": "prepared-kt-dolly-olmo2"}}}
    steps, stopped = runner.engine_steps(plan, "olmo2-1b-1101", True)
    assert stopped is None
    assert [n for n, _ in steps] == ["job-process-base-job-1101", "job-process-base-1101", "job-process-1101"]
    make, run, calibrate = (a for _, a in steps)
    assert make[:2] == ["make-job", "run-one"] and make[make.index("--target") + 1] == "init"
    assert run[run.index("--out") + 1] == "round1/1101-a0-init-a1"
    assert calibrate[-1] == "--base-eval" and calibrate[calibrate.index("--checkpoints") + 1] == "e1"
    for _, args in steps:
        _parser().parse_args(args)


@pytest.mark.parametrize("verdict", [False, None, "true", 1])
def test_without_a_proven_baseline_no_unit_runs(kit, verdict):
    runner = kit("setup/job_runner_probe.py")
    steps, stopped = runner.engine_steps({"hosts": {}}, "x", verdict)
    assert steps == [] and stopped == "init_not_proven_equal_to_untuned"


@pytest.mark.parametrize("verdict, expect_steps", [(True, 3), (False, 0), (None, 0)])
def test_the_job_runners_dry_run_writes_nothing(kit, tmp_path, verdict, expect_steps):
    work = tmp_path / "work"
    work.mkdir()
    import probes  # noqa: F401
    write_plan(work, "llama31-8b")
    (work / "PREFLIGHT-DONE.json").write_text(json.dumps({"ok": True, "init_equals_untuned": verdict}))
    before = sorted(p.name for p in work.iterdir())
    done = subprocess.run([sys.executable, "-B", str(kit.root / "setup" / "job_runner_probe.py"), "llama31-8b-1101", "--dry-run"],
                          cwd=work, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0, done.stderr[-500:]
    out = json.loads(done.stdout)
    assert len(out["steps"]) == expect_steps
    assert out["stopped"] == (None if verdict is True else "init_not_proven_equal_to_untuned")
    assert sorted(p.name for p in work.iterdir()) == before


def test_the_job_runner_refuses_while_a_token_variable_is_set(kit, tmp_path, monkeypatch):
    runner = kit("setup/job_runner_probe.py")
    write_plan(tmp_path, "olmo2-1b")
    (tmp_path / "PREFLIGHT-DONE.json").write_text(json.dumps({"ok": True, "init_equals_untuned": True}))
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HF_TOKEN", fake_token())
    with pytest.raises(AssertionError, match="a token is present"):
        runner.main(["olmo2-1b-1101"])
    assert not (tmp_path / "JOB-DONE.json").exists()


def test_the_cap_check_and_the_end_of_job_shortening(kit):
    runner = kit("setup/job_runner_probe.py")
    check = runner.cap_check({"generate": 900.0, "sample": 300.0, "guard": 200.0, "query_loss": 50.0}, 7,
                             ms_per_step_full=100.0, batch=32, training_s=1000.0, remaining_s=12_000.0)
    upper = 0.1 * 2049 * (15 + 19) + 250.0 + 1000.0
    assert check["projected_e1_upper_s"] == pytest.approx(upper) and check["init_capped"] == 7
    assert check["init_evaluation_s"] == pytest.approx(1450.0)
    assert check["cap_risk"] is (12_000.0 - upper < 1800)
    assert runner.cap_check({}, 0, 100.0, 32, 0.0, remaining_s=0.1 * 2049 * 34 + 1799)["cap_risk"] is True
    assert runner.cap_check({}, 0, 100.0, 32, 0.0, remaining_s=0.1 * 2049 * 34 + 1801)["cap_risk"] is False
    # the shortening moves the stop to 3,600 s from now only when more remains: it can never extend
    for remaining in (None, -5.0, 0.0, 1800.0, 3600.0):
        assert runner.shorten(remaining) is False
    for remaining in (3600.5, 7200.0, 40_000.0):
        assert runner.shorten(remaining) is True and runner.SHORTEN_TO_S < remaining


# ----- the preflight wrapper ------------------------------------------------------------------------------------


def test_the_preflight_wrapper_needs_the_gated_receipt_and_no_token(kit, tmp_path, monkeypatch):
    wrapper = kit("setup/preflight_probe.py")
    import probes
    gated = {"plan": probes.download_plan("llama32-1b")}
    with pytest.raises(SystemExit, match="gated-download-receipt"):
        wrapper.gated_ready(gated, tmp_path)
    (tmp_path / "gated-download-receipt.json").write_text(json.dumps({"ok": False}))
    with pytest.raises(SystemExit, match="gated-download-receipt"):
        wrapper.gated_ready(gated, tmp_path)
    (tmp_path / "gated-download-receipt.json").write_text(json.dumps({"ok": True}))
    with pytest.raises(SystemExit, match="not in the HF cache"):                # review fix 7: a receipt alone is not enough
        wrapper.gated_ready(gated, tmp_path)
    snapshot = tmp_path / "snap"
    snapshot.mkdir()
    (snapshot / "model.safetensors").write_bytes(b"w")
    receipt = {"ok": True, "models": {"policy": {"snapshot": str(snapshot), "files": {"model.safetensors": {}, "config.json": {}}}}}
    (tmp_path / "gated-download-receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(SystemExit, match="1 missing"):                         # the container disk was erased
        wrapper.gated_ready(gated, tmp_path)
    (snapshot / "config.json").write_text("{}")
    wrapper.gated_ready(gated, tmp_path)
    wrapper.gated_ready({"plan": probes.download_plan("olmo2-7b")}, tmp_path / "nowhere")   # open: no receipt needed
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)
    wrapper.token_hygiene()
    monkeypatch.setenv("HF_TOKEN", fake_token())
    with pytest.raises(SystemExit, match="token variable"):
        wrapper.token_hygiene()
    monkeypatch.delenv("HF_TOKEN", raising=False)
    (tmp_path / ".cache" / "huggingface").mkdir(parents=True)
    (tmp_path / ".cache" / "huggingface" / "token").write_text("x")
    with pytest.raises(SystemExit, match="token exists"):
        wrapper.token_hygiene()


def test_the_preflight_skip_rule_and_dry_run(kit, tmp_path):
    wrapper = kit("setup/preflight_probe.py")
    assert wrapper.skipped(32, [32]) and wrapper.skipped(32, [16]) and not wrapper.skipped(16, [32])
    assert not wrapper.skipped(32, [])
    import probes
    plan = {"preflight_prepared": "prepared-kt-dolly-olmo2", "preflight_recipes": probes.PROBES["olmo2-7b"]["recipes"]}
    work = tmp_path / "work"
    work.mkdir()
    (work / "plan.json").write_text(json.dumps(plan))
    done = subprocess.run([sys.executable, "-B", str(kit.root / "setup" / "preflight_probe.py"), "--dry-run"], cwd=work,
                          capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0, done.stderr[-500:]
    commands = json.loads(done.stdout)
    assert len(commands) == 6 and all(c[1] == "scripts/cuda_preflight_family.py" for c in commands)
    assert sorted(p.name for p in work.iterdir()) == ["plan.json"]
    fields = wrapper.cap_fields(_heartbeat(tmp_path, "2026-10-08T12:00:00Z"), dt.datetime(2026, 10, 8, 10, tzinfo=dt.timezone.utc))
    assert fields == {"governing_stop_utc": "2026-10-08T12:00:00Z", "cap_remaining_s": 7200.0}


def _heartbeat(folder: Path, stop: str) -> Path:
    path = folder / "heartbeat.json"
    path.write_text(json.dumps({"governing": {"stop_at_utc": stop}}))
    return path


# ----- the plan tool and the probe table ------------------------------------------------------------------------


PROBE_KEYS = ["olmo2-1b", "olmo2-7b", "olmo2-13b", "llama32-1b", "llama31-8b"]


def test_the_constants_refuse_until_set(kit):
    import probe_constants as pc
    assert pc.PROBE is None and all(v is None for v in pc.PREPARED_MANIFESTS.values())
    with pytest.raises(SystemExit, match="PROBE is not set"):
        pc.probe()
    with pytest.raises(SystemExit, match="PROBE is not set"):
        pc.prepared()


@pytest.mark.parametrize("probe", PROBE_KEYS)
def test_the_plan_tool_writes_one_first_host_per_probe(kit, monkeypatch, probe):
    pc, probes = set_probe(monkeypatch, probe, manifest=None)
    with pytest.raises(SystemExit, match="PREPARED_MANIFESTS"):
        pc.prepared()
    set_probe(monkeypatch, probe)
    tool = kit("plan_tool.py")
    plan = tool.initial_plan({"engine_sha256": "e" * 64, "git_commit": "c" * 40}, pc.probe(), pc.prepared())
    spec = probes.PROBES[probe]
    assert plan["hosts"] == {f"{probe}-1101": {"role": "first", "arm": "a0", "seed": 1101, "prepared": spec["prepared"],
                                               "base_eval": True, "cap_hours": spec["cap_hours"],
                                               "preflight_wait_s": spec["preflight_wait_s"],
                                               "container_disk_gb": spec["container_disk_gb"], "volume_gb": spec["volume_gb"]}}
    assert plan["checkpoints"] == ["e1"] and plan["first_host_recipes"] == spec["recipes"]
    assert plan["prepared"] == {spec["prepared"]: "f" * 64} and plan["preflight_prepared"] == spec["prepared"]
    assert plan["recipe_path"] is None and plan["probe"] == probe


def test_the_probe_table_agrees_with_the_recipes_and_data_configs(kit):
    import probes
    ladders = {"olmo2-1b": ["mb4", "mb2", "mb2-eager"], "llama32-1b": ["mb4", "mb2", "mb2-eager"],
               "llama31-8b": ["mb4", "mb2", "mb1-gc", "mb1-gc-eager"],
               "olmo2-7b": ["mb4", "mb2", "mb1-gc", "mb1-gc-eager", "mb2-g16", "mb1-gc-g16"],
               "olmo2-13b": ["mb2-g16", "mb1-g16", "mb1-gc-g16", "mb1-gc-eager-g16"]}
    assert sorted(probes.PROBES) == sorted(PROBE_KEYS)
    caps = {"olmo2-1b": 6.5, "llama32-1b": 6.5, "olmo2-7b": 7.5, "llama31-8b": 7.5, "olmo2-13b": 15.0}   # review fix 9
    waits = {"olmo2-1b": 3600, "llama32-1b": 3600, "olmo2-7b": 5400, "llama31-8b": 5400, "olmo2-13b": 9000}
    for probe, spec in probes.PROBES.items():
        assert spec["recipes"] == [f"experiments/safety_selection/configs/study-kt-{probe}-r64-b-{c}-20261008.json"
                                   for c in ladders[probe]]
        assert spec["cap_hours"] == caps[probe] and spec["preflight_wait_s"] == waits[probe]
        assert spec["policy"]["gated"] is probe.startswith("llama")
        assert spec["weight_pins"] and all(len(p) == 64 and not set(p) - set("0123456789abcdef") for p in spec["weight_pins"])
        data = load_data_config(CONFIGS / FAMILY_CONFIG[spec["prepared"]])
        for path in spec["recipes"]:
            recipe = load_recipe(ROOT / path)
            assert (recipe["model"]["repo_id"], recipe["model"]["revision"]) == \
                (spec["policy"]["repo_id"], spec["policy"]["revision"])
            assert recipe["model"]["architecture"] == ("LlamaForCausalLM" if probe.startswith("llama") else "Olmo2ForCausalLM")
            tokenizer = recipe["model"].get("tokenizer") or {k: recipe["model"][k] for k in ("repo_id", "revision")}
            assert (tokenizer["repo_id"], tokenizer["revision"]) == (data["tokenizer"]["repo_id"], data["tokenizer"]["revision"])
            audit = spec["audit_tokenizer"]
            assert (audit is None) == ("tokenizer" not in recipe["model"])
            if audit:
                assert (audit["repo_id"], audit["revision"]) == (tokenizer["repo_id"], tokenizer["revision"])
    llama8 = probes.download_plan("llama31-8b")
    assert not any(p.startswith("original") or p.endswith(".pth") for e in llama8 for p in e["patterns"])
    assert sum(p.endswith(".safetensors") for p in llama8[0]["patterns"]) == 4


@pytest.mark.parametrize("probe", PROBE_KEYS)
def test_the_download_plan_per_probe(kit, probe):
    import probes
    plan = probes.download_plan(probe)
    roles = [e["role"] for e in plan]
    assert roles[0] == "policy" and roles[-1] == "guard"
    assert ("audit_tokenizer" in roles) == (probe in ("olmo2-7b", "olmo2-13b", "llama32-1b"))
    gated = {e["repo_id"] for e in plan if e["gated"]}
    assert gated == ({"meta-llama/Llama-3.2-1B-Instruct", "meta-llama/Llama-3.1-8B-Instruct"} if probe == "llama32-1b"
                     else {"meta-llama/Llama-3.1-8B-Instruct"} if probe == "llama31-8b" else set())
    assert all(len(e["revision"]) == 40 for e in plan)
    for entry in plan:
        if entry["gated"]:
            assert not any("*" in p for p in entry["patterns"])        # gated repositories list exact files


# ----- the pod download script (fake snapshot_download) -----------------------------------------------------------


def _probe_json(tmp_path: Path, probe: str, fake_files: dict) -> dict:
    import probes
    pins = [hashlib.sha256(fake_files["model.safetensors"]).hexdigest()]
    record = {"probe": probe, "plan": probes.download_plan(probe), "weight_pins": pins}
    (tmp_path / "probe.json").write_text(json.dumps(record))
    return record


def _fake_snapshot(tmp_path: Path, calls: list, fake_files: dict, fail: bool = False):
    def snapshot_download(**kwargs):
        calls.append(kwargs)
        if fail:
            raise RuntimeError("fake network error")
        folder = tmp_path / "cache" / kwargs["repo_id"].replace("/", "--") / "snapshots" / kwargs["revision"]
        blobs = tmp_path / "cache" / kwargs["repo_id"].replace("/", "--") / "blobs"
        folder.mkdir(parents=True, exist_ok=True)
        blobs.mkdir(parents=True, exist_ok=True)
        for name, data in fake_files.items():
            blob = blobs / hashlib.sha256(data).hexdigest()
            blob.write_bytes(data)
            if not (folder / name).exists():
                (folder / name).symlink_to(blob)
        return str(folder)
    return snapshot_download


def _download_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path / "cache"))
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)


def test_the_open_download_passes_token_false_and_never_touches_a_gated_repository(kit, tmp_path, monkeypatch):
    script = kit("setup/download_models_probe.py")
    _download_env(tmp_path, monkeypatch)
    files = {"model.safetensors": b"weights-1", "config.json": b"{}"}
    record = _probe_json(tmp_path, "llama32-1b", files)
    calls = []
    monkeypatch.setattr(script, "snapshot_download", _fake_snapshot(tmp_path, calls, files))
    assert script.main([]) == 0
    open_repos = [e["repo_id"] for e in record["plan"] if not e["gated"]]
    assert [c["repo_id"] for c in calls] == open_repos and all(c["token"] is False for c in calls)
    with pytest.raises(SystemExit, match="is gated"):
        script.download([e for e in record["plan"] if e["gated"]], None)
    with pytest.raises(SystemExit, match="go together"):
        script.main(["--gated"])
    receipt = json.loads((tmp_path / "model-download-receipt.json").read_text())
    assert receipt["ok"] is True and receipt["gated"] is False and receipt["cache_token_pattern_count"] == 0


@pytest.mark.parametrize("fail", [False, True])
def test_the_gated_download_reads_the_token_from_stdin_and_leaves_it_nowhere(kit, tmp_path, monkeypatch, fail):
    script = kit("setup/download_models_probe.py")
    _download_env(tmp_path, monkeypatch)
    files = {"model.safetensors": b"weights-2", "tokenizer.json": b"{}"}
    record = _probe_json(tmp_path, "llama32-1b", files)
    calls, token = [], fake_token()
    monkeypatch.setattr(script, "snapshot_download", _fake_snapshot(tmp_path, calls, files, fail=fail))
    out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    if fail:
        with pytest.raises(RuntimeError):
            script.main(["--gated", "--token-stdin"], stdin=io.StringIO(token + "\n"))
    else:
        assert script.main(["--gated", "--token-stdin"], stdin=io.StringIO(token + "\n")) == 0
    gated = [e["repo_id"] for e in record["plan"] if e["gated"]]
    assert [c["repo_id"] for c in calls] == (gated[:1] if fail else gated)
    assert all(c["token"] == token for c in calls)
    receipt = json.loads((tmp_path / "gated-download-receipt.json").read_text())
    assert receipt["ok"] is (not fail) and receipt["token_source"] == "stdin" and receipt["gated_repos"] == gated
    assert files_holding(tmp_path, token) == [] and token not in out.getvalue()
    import secret_scan
    outside_kit = [p for p in tmp_path.rglob("*") if p.is_file() and "runkit" not in p.relative_to(tmp_path).parts]
    assert secret_scan.scan_paths(outside_kit) == []
    assert not (tmp_path / "home" / ".cache" / "huggingface" / "token").exists()
    assert "HF_TOKEN" not in os.environ


def test_the_download_refuses_a_weight_that_differs_from_its_pin_or_blob(kit, tmp_path, monkeypatch):
    script = kit("setup/download_models_probe.py")
    _download_env(tmp_path, monkeypatch)
    files = {"model.safetensors": b"weights-3"}
    record = _probe_json(tmp_path, "olmo2-1b", files)
    record["weight_pins"] = ["0" * 64]
    (tmp_path / "probe.json").write_text(json.dumps(record))
    monkeypatch.setattr(script, "snapshot_download", _fake_snapshot(tmp_path, [], files))
    with pytest.raises(SystemExit, match="pinned"):
        script.main([])
    assert json.loads((tmp_path / "model-download-receipt.json").read_text())["ok"] is False


# ----- launch: the token checks and the environments ------------------------------------------------------------


def _fake_hub(role="read", scopes=("repos.read",), whoami=200, ranges=206):
    seen = []

    def get(url, token, headers=None, limit=1):
        seen.append((url, headers))
        if url.endswith("whoami-v2"):
            body = {"auth": {"accessToken": {"role": role, "fineGrained": {"scoped": [{"permissions": list(scopes)}]}}}}
            return whoami, json.dumps(body).encode()
        return (ranges(url) if callable(ranges) else ranges), b""
    return get, seen


def test_launch_refuses_without_the_token_variable_and_skips_open_probes(kit, monkeypatch):
    launch = kit("launch.py")
    set_probe(monkeypatch, "llama31-8b")
    with pytest.raises(SystemExit, match="HF_TOKEN is not set"):
        launch.gated_precheck("llama31-8b-1101", env={})
    set_probe(monkeypatch, "olmo2-13b")
    assert launch.gated_precheck("olmo2-13b-1101", env={}) is None


@pytest.mark.parametrize("role, scopes", [("write", ("repos.write", "repos.read")), ("fineGrained", ("repos.read", "repos.write")),
                                          ("fineGrained", ("repos.read",)), ("read", ())])
def test_a_broad_scope_token_warns_but_passes(kit, monkeypatch, capsys, role, scopes):
    launch = kit("launch.py")
    set_probe(monkeypatch, "llama32-1b")
    token = fake_token()
    get, seen = _fake_hub(role, scopes)
    record = launch.gated_precheck("llama32-1b-1101", env={"HF_TOKEN": token}, get=get)
    import probes
    gated_files = [f"{e['repo_id']}/{p}" for e in probes.download_plan("llama32-1b") if e["gated"] for p in e["patterns"]]
    assert sorted(record["range_status"]) == sorted(gated_files) and set(record["range_status"].values()) == {206}
    assert all(h == {"Range": "bytes=0-0"} for url, h in seen if "resolve" in url)
    warned = role not in ("read", "fineGrained") or any(not s.endswith(".read") for s in scopes)
    assert bool(record["warnings"]) is warned
    if warned:
        assert record["warnings"][0]["event"] == "token-scope-warning" and record["warnings"][0]["role"] == role
        assert '"token-scope-warning"' in capsys.readouterr().out
    assert files_holding(kit.root, token) == []
    assert json.loads((kit.root / "hosts" / "llama32-1b-1101" / "token-check.json").read_text())["role"] == role


@pytest.mark.parametrize("whoami, ranges", [(401, 206), (200, 403), (200, 401), (200, 200),
                                            (200, lambda url: 404 if url.endswith("model.safetensors") else 206)])
def test_launch_refuses_a_token_without_gated_access(kit, monkeypatch, whoami, ranges):
    launch = kit("launch.py")
    set_probe(monkeypatch, "llama32-1b")
    get, _ = _fake_hub(whoami=whoami, ranges=ranges)
    with pytest.raises(SystemExit, match="whoami|gated access"):
        launch.gated_precheck("llama32-1b-1101", env={"HF_TOKEN": fake_token()}, get=get)


def test_a_redirect_to_another_host_never_carries_the_token(kit):
    import email.message
    import urllib.request

    launch = kit("launch.py")
    token = fake_token()
    request = urllib.request.Request("https://huggingface.co/m/resolve/x/f",
                                     headers={"Authorization": "Bearer " + token, "Range": "bytes=0-0"})
    handler = launch.SameHostAuthRedirect()
    far = handler.redirect_request(request, None, 302, "Found", email.message.Message(), "https://cdn-lfs.hf.co/s?sig=1")
    near = handler.redirect_request(request, None, 302, "Found", email.message.Message(), "https://huggingface.co/other")
    assert dict(far.headers) == {"Range": "bytes=0-0"} and token not in json.dumps(dict(far.headers))
    assert near.headers["Authorization"] == "Bearer " + token


def test_launch_gives_the_token_only_to_the_orchestrate_child(kit, monkeypatch):
    launch = kit("launch.py")
    set_probe(monkeypatch, "llama31-8b")
    write_plan(kit.root, "llama31-8b")
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    original = launch.gated_precheck
    get, _ = _fake_hub()
    monkeypatch.setattr(launch, "gated_precheck", lambda host: original(host, get=get))
    runs, popens = [], []

    def run(args, **kwargs):
        runs.append((args, kwargs))
        if args[1:3] == ["host.py", "create"]:
            folder = kit.root / "hosts" / args[3]
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "pod.json").write_text("{}")
        return subprocess.CompletedProcess(args, 0, "", "")

    def popen(args, **kwargs):
        popens.append((args, kwargs))

    assert launch.main(["llama31-8b-1101"], run=run, popen=popen, sleep=lambda s: None) == 0
    assert [a[1:3] for a, _ in runs] == [["host.py", "reconcile"], ["budget.py", "check"], ["host.py", "create"]]
    for args, kwargs in runs:
        assert "HF_TOKEN" not in kwargs["env"] and token not in json.dumps(kwargs["env"]) and token not in args
    (args, kwargs), = popens
    assert args[:2] == ["caffeinate", "-i"] and args[3:] == ["orchestrate.py", "after-create", "llama31-8b-1101"]
    assert kwargs["env"]["HF_TOKEN"] == token and token not in args
    assert files_holding(kit.root, token) == []
    assert "HF_TOKEN" not in os.environ                         # the disputed review item: scrubbed after the loop


# ----- host.py: the gated download, create's environment, extend-cap ---------------------------------------------


def test_host_gated_download_sends_the_token_on_stdin_only(kit, monkeypatch):
    host = kit("host.py")
    write_plan(kit.root, "llama32-1b")
    monkeypatch.setattr(host, "ssh_base", lambda h: ["-p", "22", "root@192.0.2.1"])
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    calls = []

    def runner(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, "done", "")

    record = host.gated_download("llama32-1b-1101", token, runner=runner)
    (args, kwargs), = calls
    assert kwargs["input"] == token + "\n" and not any(token in a for a in args)
    assert "HF_TOKEN" not in kwargs["env"] and "--token-stdin" in args[-1]
    assert record["ok"] is True and set(record) == {"utc", "ok", "exit", "attempt"}
    assert f"gated-download-{record['attempt']} " in args[-1]
    assert files_holding(kit.root, token) == []
    with pytest.raises(SystemExit, match="no token"):
        host.gated_download("llama32-1b-1101", "", runner=runner)


def test_host_create_sends_no_token_to_runpod_or_its_children(kit, monkeypatch):
    host = kit("host.py")
    write_plan(kit.root, "olmo2-13b")
    (kit.root / "ssh").mkdir()
    (kit.root / "ssh" / "key.pub").write_text("fixture-public-key\n")
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", token)
    children, requests = [], []

    def run(args, **kwargs):
        children.append(kwargs.get("env"))
        out = Path(args[args.index("--out") + 1])
        out.write_text(json.dumps({"env": {"POD_TIMER_CAP": "1"}, "cap_stop_utc": "2026-10-08T12:00:00+00:00",
                                   "docker_start_cmd": ["bash"]}))
        return subprocess.CompletedProcess(args, 0)

    def api(method, path, payload=None):
        requests.append(payload)
        if method == "GET":
            return 200, []
        return 200, {"id": "pod-1", "name": host.name_of("olmo2-13b-1101"), "costPerHr": 1.5}

    monkeypatch.setattr(host.subprocess, "run", run)
    monkeypatch.setattr(host, "api", api)
    record = host.create("olmo2-13b-1101")
    assert record["name"] == "attribution-probe-olmo2-13b-1101"
    request = requests[-1]
    assert request["containerDiskInGb"] == 80 and request["volumeInGb"] == 40
    assert token not in json.dumps(request) and not {"HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"} & set(request["env"])
    assert all(env is not None and "HF_TOKEN" not in env and "HUGGING_FACE_HUB_TOKEN" not in env for env in children)
    assert files_holding(kit.root, token) == []


def _pod(kit_root: Path, host: str, name: str, cap: str, pod_id: str = "pod-1") -> None:
    folder = kit_root / "hosts" / host
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "pod.json").write_text(json.dumps({"id": pod_id, "name": name, "cap_stop_utc": cap}))


def test_extend_cap_refuses_when_the_budget_check_fails_and_a_shortening_needs_none(kit, monkeypatch):
    host = kit("host.py")
    write_plan(kit.root, "olmo2-1b")
    soon = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat()
    _pod(kit.root, "olmo2-1b-1101", host.name_of("olmo2-1b-1101"), soon)
    monkeypatch.setattr(host, "ssh_base", lambda h: ["root@192.0.2.1"])
    calls = []

    def refusing(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 3 if "budget.py" in args[1] else 0, "", "")

    with pytest.raises(SystemExit, match="budget guard refused"):
        host.extend_cap("olmo2-1b-1101", 3 * 3600, runner=refusing)
    assert len(calls) == 1 and calls[0][2:4] == ["check", calls[0][3]] and float(calls[0][3]) == pytest.approx(2.0, abs=0.01)
    assert not (kit.root / "hosts" / "olmo2-1b-1101" / "cap-override.json").exists()
    calls.clear()
    line = {"lease": "L1", "governs": True, "acknowledged": True, "stop_at_utc": "2026-10-08T10:30:00.000+00:00"}

    def ssh_ok(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, json.dumps(line) + "\n", "")

    result = host.extend_cap("olmo2-1b-1101", 1800, runner=ssh_ok)              # earlier than the cap: no budget check
    assert len(calls) == 1 and calls[0][0] == "ssh" and result["added_hours"] < 0
    assert json.loads((kit.root / "hosts" / "olmo2-1b-1101" / "cap-override.json").read_text())["lease"] == "L1"


# ----- the budget guard over every kit ---------------------------------------------------------------------------


def test_the_budget_counts_pods_of_every_kit_overrides_and_unknown_pods(kit, monkeypatch):
    budget = kit("budget.py")
    now = dt.datetime.now(dt.timezone.utc)
    other = kit.root.parent / "family-probe-olmo2-7b"
    _pod(kit.root, "olmo2-1b-1101", "attribution-probe-olmo2-1b-1101", (now + dt.timedelta(hours=2)).isoformat(), "a")
    _pod(other, "olmo2-7b-1101", "attribution-probe-olmo2-7b-1101", (now + dt.timedelta(hours=3)).isoformat(), "b")
    (other / "hosts" / "olmo2-7b-1101" / "cap-override.json").write_text(
        json.dumps({"stop_at_utc": (now + dt.timedelta(hours=5)).isoformat().replace("+00:00", "Z")}))
    (kit.root / "hosts" / "olmo2-1b-1101" / "cap-override.json").write_text(
        json.dumps({"stop_at_utc": (now + dt.timedelta(hours=1)).isoformat()}))           # earlier: ignored
    assert budget.CAP_FALLBACK_H == 15.0
    pods = [{"id": "a", "name": "p1", "desiredStatus": "RUNNING", "costPerHr": 1.0},
            {"id": "b", "name": "p2", "desiredStatus": "RUNNING", "costPerHr": 1.0},
            {"id": "c", "name": "unknown", "desiredStatus": "RUNNING", "costPerHr": 1.0},
            {"id": "d", "name": "stopped", "desiredStatus": "EXITED", "costPerHr": 1.0}]
    monkeypatch.setattr(budget, "call", lambda method, url, payload=None: pods if method == "GET" else
                        {"data": {"myself": {"clientBalance": 100.0, "currentSpendPerHr": 3.0}}})
    rows = {r["name"]: r["hours_left_upper"] for r in budget.projection()["running"]}
    assert rows["p1"] == pytest.approx(2.0, abs=0.02) and rows["p2"] == pytest.approx(5.0, abs=0.02)
    assert rows["unknown"] == 15.0 and "stopped" not in rows


# ----- orchestrate: child environments, the gated step, the cap gate, cap-risk, F1 --------------------------------


def test_every_orchestrate_child_gets_no_token(kit, monkeypatch):
    orch = kit("orchestrate.py")
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    seen = []
    monkeypatch.setattr(orch.subprocess, "run", lambda args, **kw: seen.append((args, kw)) or subprocess.CompletedProcess(args, 0, "", ""))
    orch.tool("get", "h")
    orch.tool("gated-download", "h", stdin_text=token + "\n")
    for args, kw in seen:
        assert "HF_TOKEN" not in kw["env"] and token not in args
    assert seen[1][1]["input"] == token + "\n"


def test_the_orchestrator_hands_the_token_to_host_py_on_stdin(kit, monkeypatch):
    orch = kit("orchestrate.py")
    set_probe(monkeypatch, "llama32-1b")
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    calls, events = [], []
    folder = kit.root / "hosts" / "llama32-1b-1101"
    folder.mkdir(parents=True)

    def tool(*args, stdin_text=None):
        calls.append((args, stdin_text))
        (folder / "gated-download.json").write_text(json.dumps({"ok": True, "exit": 0}))
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(orch, "tool", tool)
    monkeypatch.setattr(orch, "log", lambda host, event, **f: events.append((event, f)))
    orch.gated_download("llama32-1b-1101")
    assert calls == [(("gated-download", "llama32-1b-1101"), token + "\n")]
    assert events == [("gated-download-finished", {"ok": True, "exit": 0, "tool_exit": 0})]
    assert "HF_TOKEN" not in os.environ                         # the disputed review item: scrubbed after use
    monkeypatch.setenv("HF_TOKEN", token)
    # review fix 7: an ok record left by an earlier attempt never counts; this call writes none and exits 1
    monkeypatch.setattr(orch, "tool", lambda *a, stdin_text=None: subprocess.CompletedProcess(a, 1, "", ""))
    with pytest.raises(SystemExit, match="gated download failed"):
        orch.gated_download("llama32-1b-1101")
    assert list(folder.glob("gated-download-earlier-*.json"))
    monkeypatch.setenv("HF_TOKEN", token)
    (folder / "gated-download.json").write_text(json.dumps({"ok": True, "exit": 0}))

    def writes_ok_but_fails(*a, stdin_text=None):
        (folder / "gated-download.json").write_text(json.dumps({"ok": True, "exit": 0}))
        return subprocess.CompletedProcess(a, 1, "", "")

    monkeypatch.setattr(orch, "tool", writes_ok_but_fails)
    with pytest.raises(SystemExit, match="gated download failed"):                # host.py's exit must be 0 too
        orch.gated_download("llama32-1b-1101")
    monkeypatch.setenv("HF_TOKEN", token)                         # exit 0 but no new record: the old ok one never counts
    monkeypatch.setattr(orch, "tool", lambda *a, stdin_text=None: subprocess.CompletedProcess(a, 0, "", ""))
    with pytest.raises(SystemExit, match="gated download failed"):
        orch.gated_download("llama32-1b-1101")
    monkeypatch.setenv("HF_TOKEN", token)
    monkeypatch.setattr(orch, "tool", lambda *a, stdin_text=None: subprocess.CompletedProcess(a, 1, "", ""))
    with pytest.raises(SystemExit, match="gated download failed"):
        orch.gated_download("llama32-1b-1101")
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(SystemExit, match="HF_TOKEN is not set"):
        orch.gated_download("llama32-1b-1101")
    set_probe(monkeypatch, "olmo2-1b")
    monkeypatch.setattr(orch, "tool", lambda *a, **k: pytest.fail("an open probe has no gated step"))
    orch.gated_download("olmo2-1b-1101")


def test_the_preflight_wait_never_passes_the_cap(kit):
    orch = kit("orchestrate.py")
    now = dt.datetime(2026, 10, 8, 10, tzinfo=dt.timezone.utc)
    assert orch.preflight_wait(5400, "2026-10-08T12:00:00+00:00", now) == 5400
    assert orch.preflight_wait(9000, "2026-10-08T11:00:00Z", now) == 3600
    assert orch.preflight_wait(3600, "2026-10-08T09:00:00+00:00", now) == 0


def test_start_job_refuses_on_the_cap_gate(kit, monkeypatch):
    orch = kit("orchestrate.py")
    write_plan(kit.root, "olmo2-13b")
    events, sent = [], []
    monkeypatch.setattr(orch, "log", lambda host, event, **f: events.append((event, f)))
    monkeypatch.setattr(orch, "send", lambda *a: sent.append(a))
    monkeypatch.setattr(orch, "start_background", lambda *a: sent.append(a))
    stop = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3)).isoformat()
    for projected in (3 * 3600 - 1700, 3 * 3600 + 10):
        with pytest.raises(SystemExit, match="does not fit"):
            orch.start_job("olmo2-13b-1101", {"governing_stop_utc": stop, "projected_job_upper_s": projected})
    with pytest.raises(SystemExit, match="does not fit"):
        orch.start_job("olmo2-13b-1101", {"governing_stop_utc": None, "projected_job_upper_s": 1.0})
    assert sent == [] and [e for e, _ in events] == ["cap-insufficient"] * 3
    (kit.root / "expected-fixture-probe.json").write_text("{}")
    orch.start_job("olmo2-13b-1101", {"governing_stop_utc": stop, "projected_job_upper_s": 3 * 3600 - 1900})
    assert [e for e, _ in events][-1] == "job-started" and len(sent) == 3


@pytest.mark.parametrize("risk", [True, False])
def test_cap_risk_is_logged_from_the_cap_check(kit, monkeypatch, risk):
    orch = kit("orchestrate.py")
    events = []
    monkeypatch.setattr(orch, "log", lambda host, event, **f: events.append((event, f)))
    monkeypatch.setattr(orch, "cap_stop", lambda host: (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=2)).isoformat())
    monkeypatch.setattr(orch, "wait_file", lambda host, name, seconds, every: {"cap_risk": risk, "projected_e1_upper_s": 9.0,
                                                                                  "remaining_s": 8.0})
    orch.watch_cap_check("olmo2-1b-1101")
    assert events == [("cap-risk" if risk else "cap-check-ok", {"projected_e1_upper_s": 9.0, "remaining_s": 8.0})]


def _fake_after_create(orch, monkeypatch, fail_at):
    calls, events = [], []
    monkeypatch.setattr(orch, "plan", lambda: {"hosts": {"h": {"role": "first"}}})
    monkeypatch.setattr(orch, "log", lambda host, event, **f: events.append((event, f)))
    monkeypatch.setattr(orch, "tool", lambda *a, **k: calls.append(a) or
                        subprocess.CompletedProcess(a, 1 if a[0] == "ssh" else 0, "stopped", ""))   # no job started
    monkeypatch.setattr(orch, "cap_gate", lambda done, now: {"ok": True})

    def step(name, result=None):
        def run(*args, **kwargs):
            if name == fail_at:
                raise SystemExit(f"{name} failed")
            return result
        return run

    for attr, name, result in (("wait_ssh", "wait-ssh", None), ("check", "check", None), ("bootstrap", "bootstrap", None),
                               ("wait_file", "wait-file", {"engine_sha256": "e" * 64}),
                               ("gated_download", "gated-download", None), ("preflight", "preflight", {"ok": True}),
                               ("record_first", "record-first", None), ("start_job", "start-job", None),
                               ("watch_cap_check", "watch", None)):
        monkeypatch.setattr(orch, attr, step(name, result))
    return calls, events


@pytest.mark.parametrize("fail_at", ["wait-ssh", "check", "bootstrap", "gated-download", "preflight", "record-first", "start-job"])
def test_a_failure_before_the_job_stops_the_pod_and_never_deletes_it(kit, monkeypatch, fail_at):
    orch = kit("orchestrate.py")
    calls, events = _fake_after_create(orch, monkeypatch, fail_at)
    with pytest.raises(SystemExit, match=f"{fail_at} failed"):
        orch.after_create("h")
    assert calls[1:] == [("extend-cap", "h", "120"), ("stop", "h")]            # the timer first, then the stop
    assert calls[0][0] == "ssh" and "job-outer/started.json" in calls[0][2]
    assert [f["step"] for e, f in events if e == "pre-job-failed"] == [fail_at]


def test_a_cap_check_watch_failure_never_stops_a_running_job(kit, monkeypatch):
    orch = kit("orchestrate.py")
    calls, events = _fake_after_create(orch, monkeypatch, "watch")
    orch.after_create("h")
    assert calls == [] and [e for e, _ in events if e != "bootstrap-ready"] == ["cap-check-watch-ended"]


# ----- the finisher -----------------------------------------------------------------------------------------------


def _finisher(kit, monkeypatch, probe="olmo2-7b"):
    fin = kit("finisher.py")
    plan = write_plan(kit.root, probe)
    (kit.root / "hosts" / f"{probe}-1101").mkdir(parents=True, exist_ok=True)
    calls = []
    return fin, plan, calls


def test_the_finisher_deadline_follows_caps_extensions_and_launch_delay(kit, monkeypatch):
    fin, plan, _ = _finisher(kit, monkeypatch)
    started = dt.datetime(2026, 10, 8, 0, tzinfo=dt.timezone.utc)
    assert fin.deadline(plan, started) == started + dt.timedelta(hours=2 + 7.5 + 3)   # no pod yet: launch window + cap
    folder = kit.root / "hosts" / "olmo2-7b-1101"
    (folder / "pod.json").write_text(json.dumps({"cap_stop_utc": "2026-10-08T05:00:00+00:00"}))
    assert fin.deadline(plan, started) == dt.datetime(2026, 10, 8, 8, tzinfo=dt.timezone.utc)
    (folder / "cap-override.json").write_text(json.dumps({"stop_at_utc": "2026-10-08T09:30:00Z"}))   # an extension
    assert fin.deadline(plan, started) == dt.datetime(2026, 10, 8, 12, 30, tzinfo=dt.timezone.utc)
    (folder / "cap-override.json").write_text(json.dumps({"stop_at_utc": "2026-10-08T04:00:00Z"}))   # a shortening
    assert fin.deadline(plan, started) == dt.datetime(2026, 10, 8, 8, tzinfo=dt.timezone.utc)
    assert "caffeinate -i" in (kit.root / "finisher.py").read_text()


def test_three_failed_light_pulls_stop_the_pod(kit, monkeypatch):
    fin, plan, calls = _finisher(kit, monkeypatch)
    monkeypatch.setattr(fin, "tool", lambda *a: calls.append(a) or subprocess.CompletedProcess(a, 1 if a[0] == "pull-light" else 0, "stopped", ""))
    host = "olmo2-7b-1101"
    for attempt in (1, 2):
        fin.finish(host, {"exit_code": 0})
        assert ("stop", host) not in calls and not (kit.root / "hosts" / host / "finished.json").exists()
    fin.finish(host, {"exit_code": 0})
    assert calls.count(("pull-light", host)) == 3 and calls[-2:] == [("extend-cap", host, "120"), ("stop", host)]
    assert json.loads((kit.root / "hosts" / host / "finished.json").read_text())["status"] == "pull-failed-stopped"
    assert not any("delete" in " ".join(c) or "terminate" in " ".join(c) for c in calls)


def _tree(root: Path, model_text: str = "", record_text: str = "") -> Path:
    tree = root / "tree"
    unit = tree / "round1" / "1101-a0-init-a1"
    (unit / "eval" / "init").mkdir(parents=True)
    (unit / "eval" / "init" / "generations.jsonl").write_text(json.dumps({"id": "q1", "text": "answer " + model_text}) + "\n")
    (unit / "ledger.jsonl").write_text(json.dumps({"stage": "generate", "note": record_text}) + "\n")
    listed = {rel: hashlib.sha256((unit / rel).read_bytes()).hexdigest()
              for rel in ("eval/init/generations.jsonl", "ledger.jsonl")}
    (unit / "COMPLETE.json").write_text(json.dumps({"files": listed}))
    (tree / "JOB-DONE.json").write_text(json.dumps({"ok": True}))
    return tree


@pytest.mark.parametrize("where", ["none", "model", "record"])
def test_the_finisher_secret_scan(kit, monkeypatch, where):
    fin, plan, calls = _finisher(kit, monkeypatch)
    host = "olmo2-7b-1101"
    token = fake_token()
    tree = _tree(kit.root / "retrieved" / host, token if where == "model" else "", token if where == "record" else "")
    monkeypatch.setattr(fin, "tool", lambda *a: calls.append(a) or subprocess.CompletedProcess(a, 0, "stopped", ""))
    monkeypatch.setattr(fin, "unpack", lambda h: tree)
    lines = []
    monkeypatch.setattr(fin, "log", lambda **f: lines.append(f))
    fin.finish(host, {"exit_code": 0, "elapsed_s": 60})
    record = json.loads((kit.root / "hosts" / host / "finished.json").read_text())
    assert calls[-1] == ("stop", host)
    if where == "record":
        assert record["status"] == "secret-found" and record["secret_hits"] == 1
        assert lines[0]["event"] == "secret-found"
        assert [list(h) for h in lines[0]["hits"]] == [["round1/1101-a0-init-a1/ledger.jsonl", "hf" + "_token"]]
    else:
        assert record["status"] == "verified-and-stopped" and record["secret_hits"] == 0
        assert len(record["model_text_pattern_hits"]) == (1 if where == "model" else 0)
    assert token not in json.dumps(lines) and files_holding(kit.root / "hosts", token) == []


# ----- pack_setup: pins, probe and manifest, secret scan -----------------------------------------------------------


def test_pack_refuses_an_unset_probe_or_manifest_and_a_missing_pin(kit, monkeypatch):
    pack = kit("pack_setup.py")
    with pytest.raises(SystemExit, match="PROBE is not set"):
        pack.main()
    pc, probes = set_probe(monkeypatch, "olmo2-7b", manifest=None)
    with pytest.raises(SystemExit, match="PREPARED_MANIFESTS"):
        pack.main()
    for probe in PROBE_KEYS:
        pack.check_pins(probe)
    monkeypatch.setitem(probes.PROBES["olmo2-7b"], "weight_pins", probes.PROBES["olmo2-7b"]["weight_pins"][:2])
    pack.check_pins("olmo2-7b")                                  # open repository: patterns, not a file list
    monkeypatch.setitem(probes.PROBES["llama31-8b"], "weight_pins", probes.PROBES["llama31-8b"]["weight_pins"][:3])
    with pytest.raises(SystemExit, match="4 listed .safetensors files but 3 pins"):
        pack.check_pins("llama31-8b")
    monkeypatch.setitem(probes.PROBES["olmo2-1b"], "weight_pins", [])
    with pytest.raises(SystemExit, match="missing"):
        pack.check_pins("olmo2-1b")
    monkeypatch.setitem(probes.PROBES["olmo2-1b"], "weight_pins", ["Z" * 64])
    with pytest.raises(SystemExit, match="not a SHA-256"):
        pack.check_pins("olmo2-1b")
    record = pack.probe_record("llama32-1b")
    assert record["probe"] == "llama32-1b" and [e["role"] for e in record["plan"]] == ["policy", "audit_tokenizer", "guard"]


def test_the_pack_scan_flags_a_planted_fake_outside_the_prepared_folder(kit, tmp_path):
    pack = kit("pack_setup.py")
    token = fake_token()
    clean = tmp_path / "clean.py"
    clean.write_text("print('ok')\n")
    planted = tmp_path / "planted.py"
    planted.write_text(f"X = '{token}'\n")
    bank = tmp_path / "bank.jsonl"
    bank.write_text(json.dumps({"text": token}) + "\n")
    pack.refuse_secrets({"scripts/clean.py": clean, "prepared-kt-dolly-olmo2/banks/dev.jsonl": bank}, {"probe.json": b"{}"},
                        {"prepared-kt-dolly-olmo2"})
    with pytest.raises(SystemExit, match="secret pattern") as raised:
        pack.refuse_secrets({"scripts/planted.py": planted}, {}, set())
    assert token not in str(raised.value)
    with pytest.raises(SystemExit, match="secret pattern"):
        pack.refuse_secrets({}, {"bundle-manifest.json": token.encode()}, set())


def test_the_files_the_pack_would_ship_hold_no_secret_pattern(kit):
    import secret_scan
    shipped = [p for c in ("minimal_safety", "safety_selection") for p in (ROOT / "experiments" / c).rglob("*")
               if p.is_file() and "__pycache__" not in p.parts and p.suffix in {".py", ".json", ".md", ".lock"}]
    shipped += [ROOT / "scripts" / n for n in ("cuda_preflight_family.py", "cuda_preflight_killtest.py",
                                               "cuda_preflight_headroom_v3.py", "cuda_preflight_headroom.py")]
    shipped += [p for p in (KIT / "setup").iterdir() if p.is_file()]
    assert secret_scan.scan_paths(shipped) == []


# ----- the Mac tokenizer fetch --------------------------------------------------------------------------------------


def _tokenizer_snapshot(tmp_path, calls, files):
    def snapshot_download(**kwargs):
        calls.append(kwargs)
        folder = tmp_path / "snap"
        folder.mkdir(exist_ok=True)
        for name, data in files.items():
            (folder / name).write_bytes(data)
        return str(folder)
    return snapshot_download


def test_the_tokenizer_fetch_checks_oids_and_uses_the_token_only_for_llama(kit, tmp_path, monkeypatch):
    fetch = kit("fetch_tokenizers_mac.py")
    files = {"tokenizer.json": b'{"a": 1}', "tokenizer_config.json": b"{}", "special_tokens_map.json": b"[]"}
    oids = {n: fetch.git_blob_sha1(d) for n, d in files.items()}
    assert fetch.git_blob_sha1(b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"     # git's empty blob
    monkeypatch.setitem(fetch.FAMILIES["llama3"], "oids", oids)
    monkeypatch.setitem(fetch.FAMILIES["olmo2"], "oids", oids)
    token, calls = fake_token(), []
    monkeypatch.setattr(fetch, "snapshot_download", _tokenizer_snapshot(tmp_path, calls, files))
    monkeypatch.setattr(fetch, "paths_info", lambda *a: pytest.fail("every file matched its own SHA-1"))
    with pytest.raises(SystemExit, match="HF_TOKEN is not set"):
        fetch.main(["llama3", "--out", str(tmp_path / "r.json")], env={})
    assert fetch.main(["llama3", "--out", str(tmp_path / "r.json")], env={"HF_TOKEN": token}) == 0
    assert fetch.main(["olmo2", "--out", str(tmp_path / "o.json")], env={"HF_TOKEN": token}) == 0
    assert calls[0]["token"] == token and calls[1]["token"] is False
    assert calls[0]["allow_patterns"] == sorted(files) and calls[0]["revision"] == fetch.FAMILIES["llama3"]["revision"]
    receipt = json.loads((tmp_path / "r.json").read_text())
    assert receipt["ok"] and receipt["token_used"] is True and receipt["files"]["tokenizer.json"]["oid_checked"] == "file"
    assert json.loads((tmp_path / "o.json").read_text())["token_used"] is False
    assert files_holding(tmp_path, token) == []


def test_the_tokenizer_fetch_refuses_a_mismatch_and_safetensors_and_accepts_an_lfs_pointer(kit, tmp_path, monkeypatch):
    fetch = kit("fetch_tokenizers_mac.py")
    data = b'{"big": true}'
    folder = tmp_path / "snap"
    folder.mkdir()
    (folder / "tokenizer.json").write_bytes(data)
    pointer = "1" * 40
    good = {"tokenizer.json": {"blob_id": pointer, "lfs_sha256": hashlib.sha256(data).hexdigest()}}
    record = fetch.check_files(folder, {"tokenizer.json": pointer}, lambda: good)
    assert record["tokenizer.json"]["oid_checked"] == "lfs-pointer"
    for bad in ({"tokenizer.json": {"blob_id": "2" * 40, "lfs_sha256": good["tokenizer.json"]["lfs_sha256"]}},
                {"tokenizer.json": {"blob_id": pointer, "lfs_sha256": "0" * 64}}, {"tokenizer.json": {"blob_id": pointer}}, {}):
        with pytest.raises(SystemExit, match="differs from its pinned oid"):
            fetch.check_files(folder, {"tokenizer.json": pointer}, lambda: bad)
    with pytest.raises(SystemExit, match="missing"):
        fetch.check_files(folder, {"vocab.json": pointer}, lambda: {})
    (folder / "model.safetensors").write_bytes(b"w")
    with pytest.raises(SystemExit, match="safetensors"):
        fetch.check_files(folder, {"tokenizer.json": fetch.git_blob_sha1(data)}, lambda: {})


# ----- the kit's contents -------------------------------------------------------------------------------------------


def test_the_kit_holds_its_scripts_only_and_every_script_compiles(tmp_path):
    names = {p.relative_to(KIT).as_posix() for p in KIT.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    assert names == {"account.py", "budget.py", "fetch_tokenizers_mac.py", "finisher.py", "host.py", "launch.py",
                     "orchestrate.py", "pack_setup.py", "plan_tool.py", "probe_constants.py", "probes.py", "second_judge_probe.py", "secret_scan.py",
                     "status.py", "setup/bootstrap_hr.sh", "setup/download_models_probe.py", "setup/extend_cap.py",
                     "setup/job_runner_probe.py", "setup/preflight_probe.py", "setup/setup_and_fetch_probe.sh"}
    for name in names:
        if name.endswith(".py"):
            py_compile.compile(str(KIT / name), cfile=str(tmp_path / "x.pyc"), doraise=True)
    sys.path.insert(0, str(KIT))
    try:
        import secret_scan
        assert secret_scan.scan_paths([KIT / n for n in sorted(names) if n != "secret_scan.py"]) == []
    finally:
        sys.path.remove(str(KIT))
        sys.modules.pop("secret_scan", None)
    text = "\n".join((KIT / n).read_text() for n in names)
    for gone in ("kt_constants", "prepared-kt-dolly\"", "worker-setup-kt", "bundle-kt", "job_runner_kt.py\"", "s0-1101",
                 "attribution-killtest"):
        assert gone not in text, gone
    assert 'f"attribution-probe-{host}' in (KIT / "host.py").read_text()
    assert "cuda_preflight_family.py" in (KIT / "setup" / "preflight_probe.py").read_text()
    assert "--token-stdin" in (KIT / "host.py").read_text() and "input=token" in (KIT / "host.py").read_text()


# ----- review fixes (8 October) ---------------------------------------------------------------------------------------


def test_a_renamed_token_variable_and_any_token_valued_variable_are_scrubbed(kit, monkeypatch):
    constants = kit.root / "probe_constants.py"                # the lead renames the variable in a working copy
    constants.write_text(constants.read_text().replace('HF_TOKEN_ENV = "HF_TOKEN"', 'HF_TOKEN_ENV = "HUGGINGFACE_TOKEN"'))
    import probe_constants as pc
    assert pc.TOKEN_ENV_NAMES == ("HUGGINGFACE_TOKEN", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
    token = fake_token()
    monkeypatch.setenv("HUGGINGFACE_TOKEN", "a-value-without-the-token-shape")      # dropped by its name alone
    monkeypatch.setenv("SOME_OTHER_NAME", "x " + token)                 # caught by its value, whatever the name
    monkeypatch.setenv("HARMLESS", "keep me")
    for name in ("launch.py", "orchestrate.py", "host.py"):
        env = kit(name).clean_env()
        assert "HUGGINGFACE_TOKEN" not in env and "SOME_OTHER_NAME" not in env and env["HARMLESS"] == "keep me", name
    monkeypatch.setenv("HUGGINGFACE_TOKEN", token)
    fin = kit("finisher.py")
    seen = []
    monkeypatch.setattr(fin.subprocess, "run", lambda args, **kw: seen.append(kw["env"]) or subprocess.CompletedProcess(args, 0))
    fin.tool("get", "h")
    assert token not in json.dumps(seen)
    import secret_scan
    environ = {"HUGGINGFACE_TOKEN": "plain", "OTHER": "x " + token, "KEEP": "1"}
    secret_scan.scrub_process(environ, pc.TOKEN_ENV_NAMES)
    assert environ == {"KEEP": "1"}
    assert (KIT / "probe_constants.py").read_text().count('HF_TOKEN_ENV = "HF_TOKEN"') == 1      # the default name


def test_a_large_or_unreadable_whoami_reply_only_warns(kit, monkeypatch):
    launch = kit("launch.py")
    set_probe(monkeypatch, "llama32-1b")
    big = json.dumps({"auth": {"accessToken": {"role": "read", "fineGrained": {"scoped": [
        {"entity": {"name": f"org{k}"}, "permissions": ["repo.content.read"]} for k in range(400)]}}}}).encode()
    assert len(big) > 4096
    calls = []

    class Response:
        status = 200

        def __init__(self, body):
            self.body = body

        def read(self, limit):
            calls.append(limit)
            return self.body[:limit]

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class Opener:
        def open(self, request, timeout):
            return Response(big)

    monkeypatch.setattr(launch.urllib.request, "build_opener", lambda *handlers: Opener())
    status, body = launch.http_get("https://huggingface.co/api/whoami-v2", "t", None, launch.WHOAMI_LIMIT)
    assert status == 200 and body == big and calls == [launch.WHOAMI_LIMIT]
    assert launch.http_get("https://huggingface.co/x", "t", {"Range": "bytes=0-0"})[1] == big[:1]   # a Range read: 1 byte

    limits = {}

    def get(url, token, headers=None, limit=1):
        limits["whoami" if url.endswith("whoami-v2") else "range"] = limit
        return (200, b"{not json") if url.endswith("whoami-v2") else (206, b"")

    record = launch.token_checks(fake_token(), probes_plan("llama32-1b"), get)
    assert limits == {"whoami": launch.WHOAMI_LIMIT, "range": 1} and launch.WHOAMI_LIMIT >= 1 << 20
    assert record["role"].startswith("unknown") and record["warnings"][0]["event"] == "token-scope-warning"
    with pytest.raises(SystemExit, match="gated access"):
        launch.token_checks(fake_token(), probes_plan("llama32-1b"),
                            lambda url, token, headers=None, limit=1: (200, b"{not json") if "whoami" in url else (403, b""))


def probes_plan(probe: str) -> list[dict]:
    import probes
    return probes.download_plan(probe)


def test_one_gated_download_folder_per_attempt(kit):
    host = kit("host.py")
    first, second = host.gated_command("20261008T010203Z"), host.gated_command("20261008T020304Z")
    assert "--out gated-download-20261008T010203Z " in first and first != second
    with pytest.raises(ValueError):
        host.gated_command("../x")
    assert "gated-download-*" in host.PULL_ITEMS and "gated-download-001" not in host.PULL_ITEMS


@pytest.mark.parametrize("script", ["download", "fetch"])
def test_the_hub_endpoint_is_pinned(kit, tmp_path, monkeypatch, script):
    if script == "download":
        module = kit("setup/download_models_probe.py")
        _download_env(tmp_path, monkeypatch)
        files = {"model.safetensors": b"w-endpoint", "config.json": b"{}"}
        _probe_json(tmp_path, "olmo2-1b", files)
        calls = []
        monkeypatch.setattr(module, "snapshot_download", _fake_snapshot(tmp_path, calls, files))
        monkeypatch.setenv("HF_ENDPOINT", "https://mirror.example.invalid")
        with pytest.raises(SystemExit, match="HF_ENDPOINT"):
            module.main([])
        assert calls == []
        monkeypatch.setenv("HF_ENDPOINT", "https://huggingface.co")
        assert module.main([]) == 0
        assert {c["endpoint"] for c in calls} == {"https://huggingface.co"}
        assert json.loads((tmp_path / "model-download-receipt.json").read_text())["endpoint"] == "https://huggingface.co"
    else:
        fetch = kit("fetch_tokenizers_mac.py")
        calls = []
        monkeypatch.setattr(fetch, "snapshot_download", lambda **kw: calls.append(kw) or pytest.fail("no call expected"))
        with pytest.raises(SystemExit, match="HF_ENDPOINT"):
            fetch.main(["olmo2", "--out", str(tmp_path / "r.json")], env={"HF_ENDPOINT": "https://mirror.example.invalid"})
        assert calls == []
        files = {"tokenizer.json": b"{}"}
        monkeypatch.setitem(fetch.FAMILIES["olmo2"], "oids", {n: fetch.git_blob_sha1(d) for n, d in files.items()})
        monkeypatch.setattr(fetch, "snapshot_download", _tokenizer_snapshot(tmp_path, calls, files))
        assert fetch.main(["olmo2", "--out", str(tmp_path / "r.json")], env={}) == 0
        assert calls[-1]["endpoint"] == "https://huggingface.co"


def _job_runner_tree(tmp_path: Path, remaining_s: float):
    """A pod folder for job_runner_probe.main with real identities and fake engine processes."""
    from experiments.safety_selection.common import code_identity
    from experiments.safety_selection.config import config_sha256, load_recipe
    import probes
    root = tmp_path / "pod"
    root.mkdir()
    recipe = probes.PROBES["olmo2-1b"]["recipes"][0]
    (root / Path(recipe).parent).mkdir(parents=True)
    shutil.copy(ROOT / recipe, root / recipe)
    (root / "prepared-kt-dolly-olmo2").mkdir()
    (root / "prepared-kt-dolly-olmo2" / "manifest.sha256").write_text("m" * 64 + "\n")
    plan = write_plan(root, "olmo2-1b")
    plan.update(engine_sha256=code_identity()["sha256"], recipe_sha256=config_sha256(load_recipe(ROOT / recipe)),
                prepared={"prepared-kt-dolly-olmo2": "m" * 64},
                fixture_compare={"equal_keys": ["k"], "resume_keys": ["r"]})
    (root / "plan.json").write_text(json.dumps(plan))
    (root / "BOOTSTRAP-READY.json").write_text(json.dumps({"ok": True}))
    (root / "cuda-preflight-1").mkdir()
    (root / "cuda-preflight-1" / "verification.json").write_text(json.dumps({"k": 1, "resume": {"r": 2}}))
    (root / "expected-fixture-probe.json").write_text(json.dumps({"k": 1, "resume": {"r": 2}}))
    (root / "PREFLIGHT-DONE.json").write_text(json.dumps({"ok": True, "recipe": recipe, "folder": "cuda-preflight-1",
                                                          "init_equals_untuned": True, "ms_per_step_full": 50.0,
                                                          "generation_batch": 32, "training_s": 300.0, "overhead_s": 1000.0}))
    stop = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=remaining_s)).isoformat()
    heartbeat = tmp_path / "heartbeat.json"
    heartbeat.write_text(json.dumps({"governing": {"stop_at_utc": stop}}))
    return root, heartbeat


@pytest.mark.parametrize("remaining_s, refused", [(3000.0, True), (40_000.0, False)])
def test_the_cap_check_refuses_e1_when_the_bound_does_not_fit(kit, tmp_path, monkeypatch, remaining_s, refused):
    runner = kit("setup/job_runner_probe.py")
    root, heartbeat = _job_runner_tree(tmp_path, remaining_s)
    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "HEARTBEAT", heartbeat)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)
    ran = []

    def run(args, **kwargs):
        ran.append(args)
        if "--out" in args and args[args.index("--out") + 1] == "job-process-base-1101":
            unit = root / "round1" / "1101-a0-init-a1"
            (unit / "eval" / "init").mkdir(parents=True)
            (unit / "ledger.jsonl").write_text(json.dumps({"stage": "generate", "seconds": 900.0}) + "\n"
                                               + json.dumps({"stage": "guard", "seconds": 200.0}) + "\n")
            (unit / "eval" / "init" / "summary.json").write_text(json.dumps({"harm": {"greedy": {"policy_capped": 3}}}))
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(runner.subprocess, "run", run)
    code = runner.main(["olmo2-1b-1101"])
    done = json.loads((root / "JOB-DONE.json").read_text())
    check = json.loads((root / "CAP-CHECK.json").read_text())
    names = [a[a.index("--out") + 1] for a in ran if "--out" in a]
    assert check["e1_refused"] is refused and check["projected_e1_upper_s"] == pytest.approx(
        0.05 * 2049 * 34 + 200.0 + 300.0 + 500.0)
    if refused:
        assert names == ["job-process-base-job-1101", "job-process-base-1101"] and done["stopped"] == "cap_check_refused"
        assert done["ok"] is False and code == 1
    else:
        assert names[-1] == "job-process-1101" and done["stopped"] is None


def test_the_stop_is_retried_and_confirmed(kit, monkeypatch):
    host = kit("host.py")
    monkeypatch.setattr(host, "SLEEP", lambda s: None)
    replies = {"POST": [(0, {"error": "TimeoutError"}), (502, {}), (200, {})],
               "GET": [(200, {"desiredStatus": "RUNNING"}), (200, {"desiredStatus": "EXITED"})]}
    seen = []

    def api(method, path, payload=None):
        seen.append((method, path))
        return replies[method].pop(0)

    monkeypatch.setattr(host, "api", api)
    result = host.stop_id("pod-1")
    assert result["confirmed"] is True and result["attempts"] == 3 and result["desiredStatus"] == "EXITED"
    assert not any("delete" in p or method == "DELETE" for method, p in seen)
    monkeypatch.setattr(host, "api", lambda method, path, payload=None: (200, {"desiredStatus": "RUNNING"}))
    assert host.stop_id("pod-1")["confirmed"] is False


def test_api_reports_a_dropped_link_as_status_0(kit, monkeypatch):
    host = kit("host.py")
    monkeypatch.setenv("RUNPOD_OPERATOR_API_KEY", "fixture-key")

    def boom(*a, **k):
        raise host.urllib.error.URLError("timed out")

    monkeypatch.setattr(host.urllib.request, "urlopen", boom)
    assert host.api("POST", "/pods", {}) == (0, {"error": "URLError"})


@pytest.mark.parametrize("case", ["existing", "post-failed"])
def test_an_untracked_pod_is_stopped_and_the_next_try_uses_a_new_name(kit, monkeypatch, case):
    host = kit("host.py")
    write_plan(kit.root, "olmo2-13b")
    (kit.root / "ssh").mkdir()
    (kit.root / "ssh" / "key.pub").write_text("fixture-public-key\n")
    folder = kit.root / "hosts" / "olmo2-13b-1101"
    folder.mkdir(parents=True)
    (folder / "create-intent.json").write_text(json.dumps({"cap_stop_utc": "2026-10-08T00:00:00+00:00"}))
    monkeypatch.setattr(host, "SLEEP", lambda s: None)
    stopped, listings = [], {"existing": [[{"id": "p9", "name": "attribution-probe-olmo2-13b-1101"}]],
                             "post-failed": [[], [{"id": "p9", "name": "attribution-probe-olmo2-13b-1101"}]]}[case]

    def api(method, path, payload=None):
        if method == "GET" and path == "/pods":
            return 200, listings.pop(0) if listings else []
        if method == "POST" and path == "/pods":
            return 0, {"error": "TimeoutError"}
        if path.endswith("/stop"):
            stopped.append(path)
            return 200, {}
        return 200, {"desiredStatus": "EXITED"}

    monkeypatch.setattr(host, "api", api)
    monkeypatch.setattr(host.subprocess, "run", lambda args, **kw: Path(args[args.index("--out") + 1]).write_text(json.dumps(
        {"env": {}, "cap_stop_utc": "2026-10-08T12:00:00+00:00", "docker_start_cmd": ["bash"]})) or subprocess.CompletedProcess(args, 0))
    with pytest.raises(SystemExit, match="stopped"):
        host.create("olmo2-13b-1101")
    assert stopped == ["/pods/p9/stop"] and not (folder / "pod.json").exists()
    orphan = json.loads((folder / "orphans.jsonl").read_text().splitlines()[0])
    assert orphan["id"] == "p9" and orphan["stop"]["confirmed"] is True
    assert host.name_of("olmo2-13b-1101") == "attribution-probe-olmo2-13b-1101-r2"
    archived = list(folder.glob("create-intent-failed-*.json"))
    assert bool(archived) is (case == "post-failed")          # archived only after the listing showed no such pod


def test_the_budget_lock_is_held_from_the_check_through_the_create_and_intents_count(kit, monkeypatch):
    import fcntl
    launch = kit("launch.py")
    budget = kit("budget.py")
    set_probe(monkeypatch, "olmo2-1b")
    write_plan(kit.root, "olmo2-1b")
    lock_path = kit.root.parent / budget.LOCK_NAME
    held = []

    def run(args, **kwargs):
        with open(lock_path, "a") as probe:
            try:
                fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
                held.append(False)
                fcntl.flock(probe, fcntl.LOCK_UN)
            except BlockingIOError:
                held.append(True)
        if args[1:3] == ["host.py", "create"]:
            (kit.root / "hosts" / args[3] / "pod.json").write_text("{}")
        return subprocess.CompletedProcess(args, 0, "", "")

    launch.main(["olmo2-1b-1101"], run=run, popen=lambda *a, **k: None, sleep=lambda s: None)
    assert held == [True, True, True]                          # reconcile, budget check and create, all under the lock
    other = kit.root.parent / "family-probe-llama31-8b" / "hosts" / "llama31-8b-1101"
    other.mkdir(parents=True)
    cap = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=4)).isoformat()
    (other / "create-intent.json").write_text(json.dumps({"cap_stop_utc": cap}))
    pending = budget.pending_intents(dt.datetime.now(dt.timezone.utc))
    assert [p["name"] for p in pending] == ["intent:family-probe-llama31-8b/llama31-8b-1101"]
    assert pending[0]["committed_usd"] == pytest.approx(4 * 1.75, abs=0.05)
    (other / "pod.json").write_text("{}")
    assert budget.pending_intents(dt.datetime.now(dt.timezone.utc)) == []


def test_one_launch_per_kit(kit, monkeypatch):
    import fcntl
    launch = kit("launch.py")
    write_plan(kit.root, "olmo2-1b")
    with open(kit.root / "launch.lock", "a") as other:
        fcntl.flock(other, fcntl.LOCK_EX)
        with pytest.raises(SystemExit, match="another launch.py"):
            launch.main(["olmo2-1b-1101"], run=lambda *a, **k: pytest.fail("no run"), popen=None, sleep=None)


def test_wait_file_reads_once_more_after_the_deadline(kit, monkeypatch):
    orch = kit("orchestrate.py")
    clock = iter([0.0, 0.0, 10_000.0, 10_000.0])
    monkeypatch.setattr(orch.time, "time", lambda: next(clock))
    monkeypatch.setattr(orch.time, "sleep", lambda s: None)
    reads = iter([subprocess.CompletedProcess([], 1, "", ""), subprocess.CompletedProcess([], 0, '{"ok": true}', "")])
    monkeypatch.setattr(orch, "ssh", lambda host, command: next(reads))
    assert orch.wait_file("h", "PREFLIGHT-DONE.json", 5400) == {"ok": True}     # the Mac slept through the deadline
    conditions = iter([False, True])
    clock2 = iter([0.0, 0.0, 99_999.0])
    monkeypatch.setattr(orch.time, "time", lambda: next(clock2))
    orch.wait_for(lambda: next(conditions), "x", seconds=60)


def test_a_cap_gate_refusal_comes_before_record_first(kit, monkeypatch):
    orch = kit("orchestrate.py")
    calls, events = _fake_after_create(orch, monkeypatch, None)
    monkeypatch.setattr(orch, "cap_gate", lambda done, now: {"ok": False, "remaining_s": 1.0, "projected_job_upper_s": 9.0})
    recorded = []
    monkeypatch.setattr(orch, "record_first", lambda *a: recorded.append(a))
    with pytest.raises(SystemExit, match="does not fit"):
        orch.after_create("h")
    assert recorded == [] and ("cap-insufficient", {"ok": False, "remaining_s": 1.0, "projected_job_upper_s": 9.0}) in events
    assert [f["step"] for e, f in events if e == "pre-job-failed"] == ["cap-gate"]


def test_a_job_that_started_despite_an_error_is_left_to_the_finisher(kit, monkeypatch):
    orch = kit("orchestrate.py")
    calls, events = _fake_after_create(orch, monkeypatch, "start-job")
    monkeypatch.setattr(orch, "tool", lambda *a, **k: calls.append(a) or subprocess.CompletedProcess(a, 0, "", ""))
    orch.after_create("h")                                     # no raise: the job runs
    assert ("stop", "h") not in calls and ("extend-cap", "h", "120") not in calls
    assert [e for e, _ in events if e in ("job-started", "pre-job-failed")] == ["job-started"]


def test_the_preflight_skip_rules(kit):
    wrapper = kit("setup/preflight_probe.py")
    assert wrapper.skip_reason(16, "sdpa", [], [(16, "sdpa")], False).startswith("an earlier candidate with this")
    assert wrapper.skip_reason(16, "eager", [], [(16, "sdpa")], False) is None          # another attention may pass
    assert wrapper.skip_reason(32, "sdpa", [], [(16, "sdpa")], False) is None
    assert "tokenizer" in wrapper.skip_reason(32, "eager", [], [], True)
    assert "memory" in wrapper.skip_reason(32, "sdpa", [32], [], False)
    assert wrapper.skip_reason(16, "sdpa", [32], [], False) is None


def test_preflight_sample_text_is_model_text(kit, tmp_path):
    import secret_scan
    tree = tmp_path / "tree"
    sample = tree / "cuda-preflight-2" / "eval-sample" / "samples.jsonl"
    sample.parent.mkdir(parents=True)
    sample.write_text("-----BEGIN RSA " + "PRIVATE KEY-----\n")
    record = tree / "cuda-preflight-2" / "verification.json"
    record.write_text("-----BEGIN RSA " + "PRIVATE KEY-----\n")
    scan = secret_scan.scan_tree(tree)
    assert scan["model_text_pattern_hits"] == [("cuda-preflight-2/eval-sample/samples.jsonl", "private_key")]
    assert scan["secret_hits"] == [("cuda-preflight-2/verification.json", "private_key")]


def test_a_failing_finish_step_still_stops_and_an_unconfirmed_stop_is_retried(kit, monkeypatch):
    fin, plan, calls = _finisher(kit, monkeypatch)
    host = "olmo2-7b-1101"
    exits = {"pull-light": 0, "extend-cap": 0, "stop": 1}
    monkeypatch.setattr(fin, "tool", lambda *a: calls.append(a) or subprocess.CompletedProcess(a, exits[a[0]], "", ""))

    def broken(h):
        raise tarfile_error()

    monkeypatch.setattr(fin, "unpack", broken)
    fin.finish(host, {"exit_code": 0})
    record = json.loads((kit.root / "hosts" / host / "finished.json").read_text())
    assert record["status"] == "finisher-error-stopped" and record["stop_confirmed"] is False
    assert calls[-2:] == [("extend-cap", host, "120"), ("stop", host)]
    assert fin.stops_pending() == [host]
    exits["stop"] = 0
    fin.retry_stops()
    assert fin.stops_pending() == [] and (kit.root / "hosts" / host / "stop-confirmed-later.json").exists()


def tarfile_error():
    import tarfile
    return tarfile.FilterError("fixture")


def test_the_finisher_scrubs_its_own_environment_and_needs_no_verify(kit, monkeypatch):
    fin = kit("finisher.py")
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    write_plan(kit.root, "olmo2-1b")
    for host in json.loads((kit.root / "plan.json").read_text())["hosts"]:
        (kit.root / "hosts" / host).mkdir(parents=True)
        (kit.root / "hosts" / host / "finished.json").write_text("{}")
    monkeypatch.setattr(sys, "argv", ["finisher.py", "1"])
    assert fin.main() == 0 and "HF_TOKEN" not in os.environ
    assert not hasattr(fin, "verify")


def test_the_kit_can_point_at_the_rank_16_ladders_and_defaults_to_rank_64(kit, monkeypatch):
    import probe_constants as pc
    import probes
    assert pc.RANK == "r64"
    for probe in PROBE_KEYS:
        assert probes.recipes(probe) == probes.PROBES[probe]["recipes"]
    pc_, _ = set_probe(monkeypatch, "olmo2-1b")
    tool = kit("plan_tool.py")
    default = tool.initial_plan({"engine_sha256": "e" * 64, "git_commit": "c" * 40}, "olmo2-1b", pc.prepared(), pc.RANK)
    assert default["first_host_recipes"] == probes.PROBES["olmo2-1b"]["recipes"] and default["name"] == "family-probe-olmo2-1b"
    monkeypatch.setattr(pc, "RANK", "r16")
    plan = tool.initial_plan({"engine_sha256": "e" * 64, "git_commit": "c" * 40}, "olmo2-1b", pc.prepared(), pc.RANK)
    assert plan["rank"] == "r16" and plan["name"] == "family-probe-olmo2-1b-r16"
    assert plan["first_host_recipes"] == [f"experiments/safety_selection/configs/study-kt-olmo2-1b-r16-b-{c}-20261008.json"
                                          for c in ("mb4", "mb2", "mb2-eager")]
    assert all((ROOT / r).is_file() for probe in probes.RANK16_PROBES for r in probes.recipes(probe, "r16"))
    for probe in ("olmo2-7b", "olmo2-13b", "llama31-8b"):
        with pytest.raises(SystemExit, match="no r16 recipes"):
            probes.recipes(probe, "r16")
    with pytest.raises(SystemExit, match="no r32 recipes"):
        probes.recipes("olmo2-1b", "r32")


def test_the_budget_projection_counts_a_pending_intent(kit, monkeypatch):
    budget = kit("budget.py")
    other = kit.root.parent / "family-probe-olmo2-13b" / "hosts" / "olmo2-13b-1101"
    other.mkdir(parents=True)
    cap = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=10)).isoformat()
    (other / "create-intent.json").write_text(json.dumps({"cap_stop_utc": cap}))
    monkeypatch.setattr(budget, "call", lambda method, url, payload=None: [] if method == "GET" else
                        {"data": {"myself": {"clientBalance": 30.0, "currentSpendPerHr": 0.0}}})
    projection = budget.projection()
    assert projection["committed_upper_usd"] == pytest.approx(10 * 1.75, abs=0.05)      # in flight in another kit


def test_extend_cap_holds_the_budget_lock(kit, monkeypatch):
    import fcntl
    host = kit("host.py")
    write_plan(kit.root, "olmo2-1b")
    soon = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat()
    _pod(kit.root, "olmo2-1b-1101", host.name_of("olmo2-1b-1101"), soon)
    monkeypatch.setattr(host, "ssh_base", lambda h: ["root@192.0.2.1"])
    held = []
    line = {"lease": "L1", "governs": True, "acknowledged": True, "stop_at_utc": "2026-10-08T10:30:00.000+00:00"}

    def runner(args, **kwargs):
        with open(kit.root.parent / host.budget.LOCK_NAME, "a") as probe:
            try:
                fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
                held.append(False)
                fcntl.flock(probe, fcntl.LOCK_UN)
            except BlockingIOError:
                held.append(True)
        return subprocess.CompletedProcess(args, 0, json.dumps(line) + "\n", "")

    host.extend_cap("olmo2-1b-1101", 3 * 3600, runner=runner)
    assert held == [True, True]                                # the budget check and the ssh, both under the lock


@pytest.mark.parametrize("layout", ["wrong-blob-name", "plain-file"])
def test_the_download_refuses_a_weight_whose_content_differs_from_its_blob_name(kit, tmp_path, monkeypatch, layout):
    """download_models_probe.py checks every .safetensors file's SHA-256 against its HF-cache blob name (round 4)."""
    script = kit("setup/download_models_probe.py")
    _download_env(tmp_path, monkeypatch)
    data = b"weights-blob"
    record = _probe_json(tmp_path, "olmo2-1b", {"model.safetensors": data})        # the pin matches the content

    def snapshot_download(**kwargs):
        folder = tmp_path / "cache" / kwargs["repo_id"].replace("/", "--") / "snapshots" / kwargs["revision"]
        folder.mkdir(parents=True, exist_ok=True)
        if layout == "wrong-blob-name":                       # a blob named by another content's SHA-256
            blob = tmp_path / "cache" / "blobs" / hashlib.sha256(b"something else").hexdigest()
            blob.parent.mkdir(parents=True, exist_ok=True)
            blob.write_bytes(data)
            (folder / "model.safetensors").symlink_to(blob)
        else:                                                 # a plain file: its name is no SHA-256
            (folder / "model.safetensors").write_bytes(data)
        return str(folder)

    monkeypatch.setattr(script, "snapshot_download", snapshot_download)
    with pytest.raises(SystemExit, match="differs from its blob name"):
        script.main([])
    assert json.loads((tmp_path / "model-download-receipt.json").read_text())["ok"] is False
    assert record["weight_pins"] == [hashlib.sha256(data).hexdigest()]
