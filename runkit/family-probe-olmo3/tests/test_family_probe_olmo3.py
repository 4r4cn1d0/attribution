"""The OLMo 3 probe kit (runkit/family-probe-olmo3/; the readiness scout's kit route; O3A §16.1-16.2, §16.8) on CPU,
without RunPod or Hugging Face: the OLMo 3 entry and its refusals, the five earlier entries byte-equal to the original
kit's, the rung ladders and the nine recipes, the lock packed by hash, the probe's preflight script, the dry pack, the
plan tool's Gate A shape, the price rule, the ids-only control-token count, the state rule's check, the Mac fetch entry,
and the original kit unchanged. Every script runs from a copy of the kit in a temporary folder. No answer text is
written here: the synthetic rows hold ids and a sentinel that must never reach stdout.

    cd <repository root> && tmp/minimal-experiment-20261002/venv/bin/python -B -m pytest -q -p no:cacheprovider \\
        --basetemp=<fresh folder> runkit/family-probe-olmo3/tests
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import py_compile
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402

KIT = ROOT / "runkit" / "family-probe-olmo3"
ORIGINAL = ROOT / "runkit" / "family-probe"
KIT_MODULES = ("probe_constants", "probes", "secret_scan", "budget")
CONFIGS = ROOT / "experiments" / "safety_selection" / "configs"
B = json.loads((CONFIGS / "study-kt-instruct-r64-b-20261007.json").read_text())
OLMO3_RECIPES = sorted(CONFIGS.glob("study-kt-olmo3-7b-r64-*-20261104.json"))
LOCK_SHA = "e4aedff89a4bb0937f7e9f958beee8eb92f8e653a5b498d51e28da091c96ba66"
SENTINEL = "NEVER-PRINTED-ANSWER-TEXT"
PY = [sys.executable, "-B"]
ENV = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def kit(tmp_path, monkeypatch):
    """A copy of the kit at tmp/runkit/family-probe-olmo3 and a loader of its modules (as the engine's kit tests do)."""
    copy = tmp_path / "runkit" / "family-probe-olmo3"
    monkeypatch.setenv("HF_HUB_DISABLE_TELEMETRY", "1")
    monkeypatch.setenv("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
    shutil.copytree(KIT, copy, ignore=shutil.ignore_patterns("__pycache__", "tests", "gate_a"))
    monkeypatch.syspath_prepend(str(copy))
    for name in KIT_MODULES:
        monkeypatch.delitem(sys.modules, name, raising=False)

    def load(relative: str, name: str | None = None):
        return load_module(copy / relative, f"olmo3_kit_{name or Path(relative).stem}")

    load.root = copy
    yield load
    for name in KIT_MODULES:
        sys.modules.pop(name, None)


def set_probe(monkeypatch, probe: str, manifest: str | None = "f" * 64):
    import probe_constants as pc
    import probes
    monkeypatch.setattr(pc, "PROBE", probe)
    if manifest:
        monkeypatch.setitem(pc.PREPARED_MANIFESTS, probes.PROBES[probe]["prepared"], manifest)
    return pc, probes


# ----- the probe table -----------------------------------------------------------------------------------------------


def test_the_olmo3_entry_shape(kit):
    import probes
    spec = probes.PROBES["olmo3-7b"]
    assert spec["policy"] == {"repo_id": "allenai/Olmo-3-7B-Instruct", "revision": "6e5971d9eba42665f5bd5a0fcf047f299ce1dccc",
                              "gated": False, "files": None, "patterns": probes.WEIGHTS + ["chat_template.jinja"]}
    assert spec["audit_tokenizer"] is None and spec["prepared"] == "prepared-kt-dolly-olmo3"
    assert len(spec["weight_pins"]) == 3 and all(len(p) == 64 and not set(p) - set("0123456789abcdef") for p in spec["weight_pins"])
    assert sum(spec["weight_bytes"].values()) == 14_596_063_712                     # MC §1: 14.60 GB in 3 shards
    assert (spec["cap_hours"], spec["preflight_wait_s"], spec["container_disk_gb"], spec["volume_gb"]) == (7.0, 5400, 60, 30)
    assert spec["lock"]["sha256"] == LOCK_SHA == sha(KIT / spec["lock"]["path"])
    record = ROOT / spec["lock"]["record"]
    if record.is_file():                                                             # the frozen record, when present
        assert sha(record) == LOCK_SHA
    assert (KIT / spec["lock"]["path"]).read_text().count("transformers==4.57.1") == 1
    assert spec["preflight_script"] == "cuda_preflight_olmo3.py"
    assert probes.preflight_script_of("olmo3-7b") == "cuda_preflight_olmo3.py"
    assert probes.preflight_script_of("olmo2-7b") == "cuda_preflight_family.py" and probes.lock_of("olmo2-7b") is None
    plan = probes.download_plan("olmo3-7b")
    assert [e["role"] for e in plan] == ["policy", "guard"] and not any(e["gated"] for e in plan)
    assert "chat_template.jinja" in plan[0]["patterns"] and not any(p.endswith(".pth") for p in plan[0]["patterns"])


def test_the_five_earlier_entries_equal_the_original_kits(kit):
    import probes
    original = load_module(ORIGINAL / "probes.py", "original_probes")
    assert sorted(probes.PROBES) == sorted(original.PROBES) + ["olmo3-7b"]
    for key in original.PROBES:
        assert probes.PROBES[key] == original.PROBES[key]
        assert probes.download_plan(key) == original.download_plan(key)
        assert probes.recipes(key) == original.recipes(key)


def test_the_rung_ladders_and_their_refusals(kit):
    import probes
    for rung, kind in probes.RUNGS.items():
        ladder = probes.recipes("olmo3-7b", rung=rung)
        assert ladder == [f"experiments/safety_selection/configs/study-kt-olmo3-7b-r64-{kind}-{c}-20261104.json"
                          for c in ("mb2", "mb1-gc", "mb2-g16")]
        for path in ladder:
            assert (ROOT / path).is_file()
            assert load_recipe(ROOT / path)["train"]["lr"] == probes.LR_OF_RUNG[rung]
    assert probes.recipes("olmo3-7b") == probes.PROBES["olmo3-7b"]["recipes"] == probes.recipes("olmo3-7b", rung=1)
    with pytest.raises(SystemExit, match="rungs are 1"):
        probes.recipes("olmo3-7b", rung=4)
    with pytest.raises(SystemExit, match="no rung 2 recipes"):
        probes.recipes("olmo2-7b", rung=2)
    with pytest.raises(SystemExit, match="no rung 2 recipes"):
        probes.recipes("olmo3-7b", "r16", "b", 2)
    with pytest.raises(SystemExit, match="has no r16 b recipes"):
        probes.recipes("olmo3-7b", "r16")


# ----- the recipes -----------------------------------------------------------------------------------------------


def test_there_are_nine_olmo3_recipes():
    assert [p.name for p in OLMO3_RECIPES] == sorted(f"study-kt-olmo3-7b-r64-{k}-{c}-20261104.json"
                                                     for k in ("b", "b5e5", "b2e5") for c in ("mb2", "mb1-gc", "mb2-g16"))


@pytest.mark.parametrize("path", OLMO3_RECIPES, ids=[p.stem for p in OLMO3_RECIPES])
def test_each_olmo3_recipe_is_recipe_b_with_the_olmo3_model_fields(path):
    recipe = load_recipe(path)
    model = recipe["model"]
    assert recipe["guard"] == B["guard"]
    assert (model["repo_id"], model["revision"], model["architecture"]) == \
        ("allenai/Olmo-3-7B-Instruct", "6e5971d9eba42665f5bd5a0fcf047f299ce1dccc", "Olmo3ForCausalLM")
    assert (model["end_of_turn_token"], model["stop_tokens"], model["pad_token"], model["assistant_header"]) == \
        ("<|endoftext|>", ["<|endoftext|>", "<|im_end|>"], "<|pad|>", "<|im_start|>assistant\n")
    assert "tokenizer" not in model and model["attn_implementation"] == "sdpa"
    assert model["lora"]["expected_trainable_parameters"] == 159_907_840
    assert recipe["train"]["micro_batch"] * recipe["train"]["grad_accum"] == 128
    kind, candidate = path.stem.split("-r64-")[1].rsplit("-20261104", 1)[0].split("-", 1)
    assert recipe["train"]["lr"] == {"b": 1e-4, "b5e5": 5e-5, "b2e5": 2e-5}[kind]
    assert (recipe["train"]["micro_batch"], recipe["train"]["gradient_checkpointing"], recipe["generation"]["batch_size"]) == \
        {"mb2": (2, False, 32), "mb1-gc": (1, True, 32), "mb2-g16": (2, False, 16)}[candidate]
    source = load_recipe(CONFIGS / f"study-kt-olmo2-7b-r64-b-{candidate}-20261008.json")
    for section in ("generation", "arc", "guard", "secondary_toxicity", "attribution"):
        assert recipe[section] == source[section]
    assert {k: v for k, v in recipe["train"].items() if k != "lr"} == {k: v for k, v in source["train"].items() if k != "lr"}
    changed = {k for k in set(model) | set(source["model"]) if model.get(k) != source["model"].get(k)}
    assert changed == {"repo_id", "revision", "architecture", "stop_tokens", "assistant_header", "tokenizer"}


def test_the_gate_a_copy_pins_the_mb2_recipe_of_each_rung():
    tool = load_module(KIT / "gate_a" / "gate_a_common_olmo3.py", "gate_a_common_olmo3_under_test")
    for name, constant in (("b", tool.RECIPE_OLMO3_B), ("b5e5", tool.RECIPE_OLMO3_B5E5), ("b2e5", tool.RECIPE_OLMO3_B2E5)):
        assert config_sha256(load_recipe(CONFIGS / f"study-kt-olmo3-7b-r64-{name}-mb2-20261104.json")) == constant
    assert tool.ROOT == ROOT and sorted(tool.PLANS) == ["llama-B5e5", "llama-G", "olmo-B", "olmo-G", "olmo3-B", "olmo3-B2e5", "olmo3-B5e5"]
    for name in ("olmo3-B", "olmo3-B5e5", "olmo3-B2e5"):
        with pytest.raises(SystemExit, match="pins are not set"):
            tool.refuse_unset_pins(name, tool.PLANS[name])
    assert sha(ROOT / "scripts" / "family_probe_reading.py") == tool.READING_SHA256


# ----- the plan tool: the Gate A shape ---------------------------------------------------------------------------


def _baseline(recipe_path: str, tool) -> dict:
    return {"unit": "1101-a0-init-a1", "path": "x", "job_sha256": "a" * 64, "code_sha256": "e" * 64,
            "manifest_sha256": "f" * 64, "engine_sha256": "e" * 64, "certificate": None,
            "eval_config": tool.eval_config(json.loads((ROOT / recipe_path).read_text()))}


def test_the_plan_tool_keeps_the_gate_a_shape(kit, monkeypatch):
    pc, probes = set_probe(monkeypatch, "olmo3-7b")
    tool = kit("plan_tool.py")
    monkeypatch.setattr(tool, "ROOT", ROOT)                                       # the copy's ROOT is the temp folder
    receipt = {"engine_sha256": "e" * 64, "git_commit": "c" * 40}
    plan = tool.initial_plan(receipt, "olmo3-7b", pc.prepared(), rung=1, seed=1101)
    host = plan["hosts"]["olmo3-7b-1101"]
    assert plan["name"] == "family-probe-olmo3-7b" and plan["rung"] == 1 and host["base_eval"] is True
    assert (host["seed"], host["cap_hours"], host["prepared"]) == (1101, 7.0, "prepared-kt-dolly-olmo3")
    assert plan["first_host_recipes"] == probes.recipes("olmo3-7b", rung=1)
    with pytest.raises(SystemExit, match="the probe pod runs the untuned unit and seed 1101 at rung 1 only"):
        tool.initial_plan(receipt, "olmo3-7b", pc.prepared(), rung=1, seed=1102)
    with pytest.raises(SystemExit, match="the probe pod runs the untuned unit and seed 1101 at rung 1 only"):
        tool.initial_plan(receipt, "olmo3-7b", pc.prepared(), rung=2, seed=1101)
    with pytest.raises(SystemExit, match="Gate A seeds are 1101-1103"):
        tool.initial_plan(receipt, "olmo3-7b", pc.prepared(), rung=1, seed=1104)
    with pytest.raises(SystemExit, match="rungs are 1"):
        tool.initial_plan(receipt, "olmo3-7b", pc.prepared(), rung=4, seed=1101)
    base = _baseline(probes.recipes("olmo3-7b", rung=1)[0], tool)          # the probe pod chose mb2
    with pytest.raises(SystemExit, match="seed 1101 at rung 1 is the probe pod's own unit"):
        tool.initial_plan(receipt, "olmo3-7b", pc.prepared(), baseline=base, rung=1, seed=1101)
    rung2 = tool.initial_plan(receipt, "olmo3-7b", pc.prepared(), baseline=base, rung=2, seed=1101)
    assert rung2["name"] == "family-probe-olmo3-7b-rung2" and rung2["hosts"]["olmo3-7b-1101"]["base_eval"] is False
    assert rung2["first_host_recipes"] == [probes.recipes("olmo3-7b", rung=2)[0]]          # mb2 only: the same evaluation
    assert rung2["baseline_reuse"]["dropped_candidates"] == probes.recipes("olmo3-7b", rung=2)[1:]
    seed2 = tool.initial_plan(receipt, "olmo3-7b", pc.prepared(), baseline=base, rung=1, seed=1102)
    assert seed2["name"] == "family-probe-olmo3-7b-seed1102" and sorted(seed2["hosts"]) == ["olmo3-7b-1102"]
    assert seed2["hosts"]["olmo3-7b-1102"]["seed"] == 1102 and seed2["first_host_recipes"] == [probes.recipes("olmo3-7b")[0]]
    both = tool.initial_plan(receipt, "olmo3-7b", pc.prepared(), baseline=base, rung=3, seed=1103)
    assert both["name"] == "family-probe-olmo3-7b-rung3-seed1103" and both["rung"] == 3
    g16 = _baseline(probes.recipes("olmo3-7b", rung=1)[2], tool)             # the probe pod chose mb2-g16
    assert tool.initial_plan(receipt, "olmo3-7b", pc.prepared(), baseline=g16, rung=2, seed=1102)["first_host_recipes"] == \
        [probes.recipes("olmo3-7b", rung=2)[2]]
    # the earlier probes keep their behaviour: seed 1101 reuse at rung 1 (GI III round 5) and the Gate A seed kits
    pc2, _ = set_probe(monkeypatch, "olmo2-7b")
    base7 = _baseline(probes.recipes("olmo2-7b")[1], tool)
    assert tool.initial_plan(receipt, "olmo2-7b", pc2.prepared(), baseline=base7, rung=1, seed=1101)["name"] == "family-probe-olmo2-7b"
    assert tool.initial_plan(receipt, "olmo2-7b", pc2.prepared(), baseline=base7, rung=1, seed=1103)["name"] == "family-probe-olmo2-7b-seed1103"
    with pytest.raises(SystemExit, match="no rung 2 recipes"):
        tool.initial_plan(receipt, "olmo2-7b", pc2.prepared(), baseline=base7, rung=2, seed=1101)
    with pytest.raises(SystemExit, match="the probe pod runs the untuned unit and seed 1101 at rung 1 only"):
        tool.initial_plan(receipt, "olmo2-7b", pc2.prepared(), rung=1, seed=1102)


def test_the_plan_tool_reads_seed_and_rung_from_the_constants(kit):
    import probe_constants as pc
    tool = kit("plan_tool.py")
    assert (pc.SEED, pc.RUNG, tool.SEED, tool.BASELINE_SEED) == (1101, 1, 1101, 1101)
    assert "prepared-kt-dolly-olmo3" in pc.PREPARED_MANIFESTS and pc.MAX_PRICE == 1.85


# ----- pack_setup: the lock by hash, the preflight script, the dry pack ---------------------------------------------


def test_the_pack_checks_the_lock_by_hash_and_needs_the_preflight_script(kit, monkeypatch, tmp_path):
    pack = kit("pack_setup.py")
    monkeypatch.setattr(pack, "ROOT", ROOT)                                       # the copy's ROOT is the temp folder
    import probes
    for probe in probes.PROBES:
        pack.check_pins(probe)
    path, digest = pack.lock_file("olmo3-7b")
    assert path == kit.root / "setup" / "requirements-olmo3.lock" and digest == LOCK_SHA
    engine_lock, engine_digest = pack.lock_file("olmo2-7b")
    assert engine_lock == ROOT / "experiments/minimal_safety/requirements.lock" and engine_digest != LOCK_SHA
    assert engine_lock.read_text().count("transformers==4.56.2") == 1
    record = pack.probe_record("olmo3-7b")
    assert record["preflight_script"] == "cuda_preflight_olmo3.py" and record["lock"] == {"source": "setup/requirements-olmo3.lock", "sha256": LOCK_SHA}
    assert pack.probe_record("olmo2-7b")["lock"] == {"source": "experiments/minimal_safety/requirements.lock", "sha256": engine_digest}
    if not (ROOT / "scripts" / "cuda_preflight_olmo3.py").is_file():               # track A's script, when not merged yet
        with pytest.raises(SystemExit, match="scripts/cuda_preflight_olmo3.py is missing"):
            pack.preflight_script("olmo3-7b")
    assert pack.preflight_script("olmo2-7b") == ROOT / "scripts" / "cuda_preflight_family.py"
    monkeypatch.setitem(probes.PROBES["olmo3-7b"]["lock"], "sha256", "0" * 64)
    with pytest.raises(SystemExit, match="differs from its pin"):
        pack.lock_file("olmo3-7b")
    monkeypatch.setitem(probes.PROBES["olmo3-7b"]["lock"], "sha256", LOCK_SHA)
    with (kit.root / "setup" / "requirements-olmo3.lock").open("a") as handle:
        handle.write("extra==1.0\n")
    with pytest.raises(SystemExit, match="differs from its pin"):
        pack.lock_file("olmo3-7b")
    (kit.root / "setup" / "requirements-olmo3.lock").unlink()
    with pytest.raises(SystemExit, match="missing from the kit"):
        pack.lock_file("olmo3-7b")


def _fake_root(tmp_path: Path) -> Path:
    """A root with the real engine folders linked in and a scripts/ folder that holds a stand-in OLMo 3 preflight."""
    root = tmp_path / "root"
    root.mkdir()
    (root / "experiments").symlink_to(ROOT / "experiments", target_is_directory=True)
    (root / "scripts").mkdir()
    for name in ("cuda_preflight_family.py", "cuda_preflight_killtest.py", "cuda_preflight_headroom_v3.py", "cuda_preflight_headroom.py"):
        (root / "scripts" / name).symlink_to(ROOT / "scripts" / name)
    (root / "scripts" / "cuda_preflight_olmo3.py").write_text('"""stand-in for track A\'s preflight (test only)"""\n')
    return root


def test_the_dry_pack_lists_the_lock_and_the_script_and_writes_nothing(kit, monkeypatch, tmp_path, capsys):
    pack = kit("pack_setup.py")
    pc, probes = set_probe(monkeypatch, "olmo3-7b")
    root = _fake_root(tmp_path)
    monkeypatch.setattr(pack, "ROOT", root)
    monkeypatch.setattr(pack, "PREP", root / "kt-prepared")                         # no prepared set here

    def fake_git(args, **kwargs):
        assert args[:3] == ["git", "-C", str(root)]
        return subprocess.CompletedProcess(args, 0, stdout="" if "status" in args else "c" * 40 + "\n", stderr="")
    monkeypatch.setattr(pack.subprocess, "run", fake_git)
    before = sorted(p.name for p in (kit.root / "setup").iterdir())
    pack.main(["--dry-run"])
    out = capsys.readouterr().out
    assert sorted(p.name for p in (kit.root / "setup").iterdir()) == before
    final = json.loads(out[out.index("{\n"):])                                     # the indented record after the note line
    assert final["dry_run"] is True and final["lock_sha256"] == LOCK_SHA and final["preflight_script"] == "cuda_preflight_olmo3.py"
    assert {"requirements.lock", "scripts/cuda_preflight_olmo3.py", "scripts/cuda_preflight_family.py", "bootstrap_hr.sh"} <= set(final["files"])
    assert "a real pack refuses" in out
    monkeypatch.setitem(probes.PROBES["olmo3-7b"], "preflight_script", "cuda_preflight_absent.py")
    with pytest.raises(SystemExit, match="scripts/cuda_preflight_absent.py is missing"):
        pack.main(["--dry-run"])


def test_the_preflight_wrapper_runs_the_probes_script(kit, tmp_path):
    wrapper = kit("setup/preflight_probe.py")
    assert wrapper.preflight_script({"preflight_script": "cuda_preflight_olmo3.py"}) == "cuda_preflight_olmo3.py"
    assert wrapper.preflight_script({}) == "cuda_preflight_family.py"
    for bad in ("../x.py", "scripts/x.py", "x.sh"):
        with pytest.raises(SystemExit, match="not a plain scripts/ file name"):
            wrapper.preflight_script({"preflight_script": bad})
    assert wrapper.command("R", "P", 2, "cuda_preflight_olmo3.py")[1] == "scripts/cuda_preflight_olmo3.py"
    import probes
    work = tmp_path / "work"
    work.mkdir()
    (work / "plan.json").write_text(json.dumps({"preflight_prepared": "prepared-kt-dolly-olmo3",
                                                "preflight_recipes": probes.recipes("olmo3-7b")}))
    (work / "probe.json").write_text(json.dumps({"preflight_script": "cuda_preflight_olmo3.py", "plan": probes.download_plan("olmo3-7b")}))
    done = subprocess.run([*PY, str(kit.root / "setup" / "preflight_probe.py"), "--dry-run"], cwd=work, capture_output=True, text=True, env=ENV)
    assert done.returncode == 0, done.stderr[-500:]
    commands = json.loads(done.stdout)
    assert len(commands) == 3 and all(c[1] == "scripts/cuda_preflight_olmo3.py" for c in commands)
    (work / "probe.json").unlink()
    done = subprocess.run([*PY, str(kit.root / "setup" / "preflight_probe.py"), "--dry-run"], cwd=work, capture_output=True, text=True, env=ENV)
    assert done.returncode == 0 and all(c[1] == "scripts/cuda_preflight_family.py" for c in json.loads(done.stdout))
    assert sorted(p.name for p in work.iterdir()) == ["plan.json"]


# ----- host.py: the price rule and the states pull ------------------------------------------------------------------


def test_the_price_rule_and_the_planning_rate(kit):
    host = kit("host.py")
    budget = kit("budget.py")
    import probe_constants as pc
    assert host.MAX_PRICE == 10.0 and pc.MAX_PRICE == 1.85 and budget.MAX_PRICE == 1.85 and budget.RESERVE_USD == 6.0
    assert host.STATE_CHECKPOINTS == ("init", "q", "e1")
    assert "pull-states" in host.__doc__ and "input=token" in (kit.root / "host.py").read_text()


@pytest.mark.parametrize("price, stopped", [(1.79, False), (9.99, False), (10.0, False), (10.01, True), (None, True),
                                            (float("inf"), True), (True, True), ("1.5", True)])
def test_create_stops_a_pod_priced_above_ten_dollars_or_without_a_finite_price(kit, monkeypatch, tmp_path, price, stopped):
    host = kit("host.py")
    import probes
    (kit.root / "ssh").mkdir()
    (kit.root / "ssh" / "key.pub").write_text("ssh-ed25519 " + "A" * 4 + "-fake-public-key-for-the-test\n")   # built at run time
    spec = probes.PROBES["olmo3-7b"]
    (kit.root / "plan.json").write_text(json.dumps({"hosts": {"olmo3-7b-1101": {"cap_hours": spec["cap_hours"], "container_disk_gb": 60, "volume_gb": 30}}}))
    calls = []

    def fake_api(method, path, payload=None):
        calls.append((method, path))
        if (method, path) == ("GET", "/pods"):
            return 200, []
        if (method, path) == ("POST", "/pods"):
            return 201, {"id": "pod1", "name": host.name_of("olmo3-7b-1101"), "costPerHr": price, "desiredStatus": "RUNNING"}
        if path.endswith("/stop"):
            return 200, {}
        if method == "GET":
            return 200, {"id": "pod1", "desiredStatus": "EXITED"}
        raise AssertionError((method, path))

    def fake_settings(args, **kwargs):
        out = Path(args[args.index("--out") + 1])
        out.write_text(json.dumps({"env": {"POD_TIMER_CAP_MINUTES": "420"}, "docker_start_cmd": ["bash"], "cap_stop_utc": "2026-11-13T00:00:00+00:00"}))
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(host, "api", fake_api)
    monkeypatch.setattr(host.subprocess, "run", fake_settings)
    monkeypatch.setattr(host, "SLEEP", lambda s: None)
    monkeypatch.setattr(host, "key", lambda: "k")
    if stopped:
        with pytest.raises(SystemExit, match="above 10.0"):
            host.create("olmo3-7b-1101")
        assert ("POST", "/pods/pod1/stop") in calls and (kit.root / "hosts" / "olmo3-7b-1101" / "price-guard-stop.json").exists()
    else:
        record = host.create("olmo3-7b-1101")
        assert record["id"] == "pod1" and record["cap_stop_utc"] == "2026-11-13T00:00:00+00:00"
        assert not any(p.endswith("/stop") for _, p in calls)
    intent = json.loads((kit.root / "hosts" / "olmo3-7b-1101" / "create-intent.json").read_text())
    assert intent["cap_hours"] == 7.0 and "env" not in intent["request_without_env"]


# ----- the ids-only control-token count ----------------------------------------------------------------------------


def _unit(folder: Path, rows_by_file: dict) -> Path:
    files = {}
    for rel, rows in rows_by_file.items():
        path = folder / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        files[rel] = sha(path)
    (folder / "COMPLETE.json").write_text(json.dumps({"complete": True, "files": files}))
    return folder


def test_the_control_token_count_reads_ids_only(kit, tmp_path):
    script = kit.root / "control_token_count_olmo3.py"
    unit = _unit(tmp_path / "round1" / "1101-a0-e1-a1", {
        "eval/e1/generations.jsonl": [
            {"kind": "harm", "prompt_id": "h1", "output_ids": [1, 2, 100264, 3], "text": SENTINEL},
            {"kind": "harm", "prompt_id": "h2", "output_ids": [5, 6], "text": SENTINEL},
            {"kind": "arc", "prompt_id": "a1", "output_ids": [100266], "text": SENTINEL}],        # not harm: not counted
        "eval/e1/samples.jsonl": [
            {"prompt_id": "h1", "sample_index": 0, "output_ids": [100266, 100269], "text": SENTINEL},
            {"prompt_id": "h1", "sample_index": 1, "output_ids": [100265, 100257], "text": SENTINEL},   # stops only
            {"prompt_id": "h2", "sample_index": 0, "output_ids": [100276], "text": SENTINEL}]})
    out = tmp_path / "count.json"
    done = subprocess.run([*PY, str(script), "--unit", str(unit), "--out", str(out)], capture_output=True, text=True, env=ENV)
    assert done.returncode == 0, done.stderr[-500:]
    assert SENTINEL not in done.stdout and SENTINEL not in out.read_text()
    record = json.loads(out.read_text())
    e1 = record["units"]["1101-a0-e1-a1"]["e1"]
    assert e1["greedy"] == {"answers": 2, "answers_with_control_ids": 1,
                            "answers_per_control_id": {**{n: 0 for n in record["control_ids"]}, "<|im_start|>": 1}}
    assert e1["sampled"]["answers"] == 3 and e1["sampled"]["answers_with_control_ids"] == 2
    assert e1["sampled"]["answers_per_control_id"]["<functions>"] == 1 and e1["sampled"]["answers_per_control_id"]["</function_calls>"] == 1
    assert e1["sampled"]["answers_per_control_id"]["<|endofprompt|>"] == 1
    assert record["control_ids"]["<|im_start|>"] == 100264 and "<|im_end|>" not in record["control_ids"]
    assert out.read_text() == json.dumps(record, indent=1, sort_keys=True) + "\n"
    again = subprocess.run([*PY, str(script), "--unit", str(unit), "--out", str(out)], capture_output=True, text=True, env=ENV)
    assert again.returncode == 2 and "written once" in again.stderr
    with (unit / "eval" / "e1" / "samples.jsonl").open("a") as handle:
        handle.write(json.dumps({"prompt_id": "h9", "sample_index": 0, "output_ids": [1]}) + "\n")
    changed = subprocess.run([*PY, str(script), "--unit", str(unit), "--out", str(tmp_path / "count2.json")], capture_output=True, text=True, env=ENV)
    assert changed.returncode == 2 and "differs from its sealed hash" in changed.stderr
    (unit / "COMPLETE.json").unlink()
    unsealed = subprocess.run([*PY, str(script), "--unit", str(unit), "--out", str(tmp_path / "count3.json")], capture_output=True, text=True, env=ENV)
    assert unsealed.returncode == 2 and "no COMPLETE.json" in unsealed.stderr


# ----- the state rule's check ---------------------------------------------------------------------------------------


def _states_tar(dest: Path, members: dict) -> None:
    with tarfile.open(dest, "w") as archive:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def test_the_states_check_verifies_the_pulled_states(kit, tmp_path):
    tool = kit("states_tool.py")
    tree = kit.root / "retrieved" / "olmo3-7b-1101" / "tree"
    adapter, optimizer, rng, state = b"A" * 32, b"O" * 32, b"R" * 8, b'{"k": 1}\n'
    files = {"states/e1/adapter.safetensors": sha_bytes(adapter), "states/e1/optimizer.safetensors": sha_bytes(optimizer),
             "states/e1/rng.safetensors": sha_bytes(rng), "states/e1/state.json": sha_bytes(state), "job.json": sha_bytes(b"{}")}
    unit = tree / "round1" / "1101-a0-e1-a1"
    unit.mkdir(parents=True)
    (unit / "job.json").write_bytes(b"{}")
    (unit / "COMPLETE.json").write_text(json.dumps({"complete": True, "files": files}))
    _states_tar(kit.root / "retrieved" / "olmo3-7b-1101" / "states-e1-20261104T000000Z.tar",
                {"round1/1101-a0-e1-a1/states/e1/adapter.safetensors": adapter, "round1/1101-a0-e1-a1/states/e1/optimizer.safetensors": optimizer,
                 "round1/1101-a0-e1-a1/states/e1/rng.safetensors": rng, "round1/1101-a0-e1-a1/states/e1/state.json": state})
    done = subprocess.run([*PY, str(kit.root / "states_tool.py"), "check", "olmo3-7b-1101", "e1"], capture_output=True, text=True, env=ENV)
    assert done.returncode == 0 and done.stdout.startswith("states verified: 1 units"), done.stderr[-300:]
    checks = sorted((kit.root / "retrieved" / "olmo3-7b-1101").glob("states-e1-check-*.json"))
    record = json.loads(checks[-1].read_text())
    assert record["units"] == {"1101-a0-e1-a1": {"files": 4, "bytes": 32 + 32 + 8 + len(state)}} and record["members"] == 4
    _states_tar(kit.root / "retrieved" / "olmo3-7b-1101" / "states-e1-20261104T000001Z.tar",
                {"round1/1101-a0-e1-a1/states/e1/adapter.safetensors": b"B" * 32, "round1/1101-a0-e1-a1/states/e1/optimizer.safetensors": optimizer,
                 "round1/1101-a0-e1-a1/states/e1/rng.safetensors": rng, "round1/1101-a0-e1-a1/states/e1/state.json": state})
    changed = subprocess.run([*PY, str(kit.root / "states_tool.py"), "check", "olmo3-7b-1101", "e1"], capture_output=True, text=True, env=ENV)
    assert changed.returncode == 2 and "1 state file(s) missing or changed" in changed.stderr
    _states_tar(kit.root / "retrieved" / "olmo3-7b-1101" / "states-e1-20261104T000002Z.tar",
                {"round1/1101-a0-e1-a1/eval/e1/generations.jsonl": b"x"})
    outside = subprocess.run([*PY, str(kit.root / "states_tool.py"), "check", "olmo3-7b-1101", "e1"], capture_output=True, text=True, env=ENV)
    assert outside.returncode == 2 and "outside round1/*/states/e1/" in outside.stderr
    with pytest.raises(SystemExit, match="checkpoint must be one of"):
        tool.check("olmo3-7b-1101", "e2")
    assert "delete waits" in (kit.root / "host.py").read_text() or "deleted only after" in tool.__doc__


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


STATES = {"adapter.safetensors": b"A" * 32, "optimizer.safetensors": b"O" * 32, "rng.safetensors": b"R" * 8, "state.json": b'{"k": 1}\n'}


def _probe_tree(root: Path) -> Path:
    """The probe pod's light tree (what the finisher unpacks): the untuned unit lists states/init/ and the e1 unit
    states/e1/ (runner.py's init and resume paths); state.json rides in the light pull, the .safetensors files do not."""
    tree = root / "tree"
    for name, checkpoint in (("1101-a0-init-a1", "init"), ("1101-a0-e1-a1", "e1")):
        unit = tree / "round1" / name
        (unit / "eval" / checkpoint).mkdir(parents=True)
        (unit / "states" / checkpoint).mkdir(parents=True)
        (unit / "eval" / checkpoint / "generations.jsonl").write_text(json.dumps({"id": "q1", "text": "answer"}) + "\n")
        (unit / "job.json").write_text("{}\n")
        (unit / "states" / checkpoint / "state.json").write_bytes(STATES["state.json"])
        listed = {rel: sha(unit / rel) for rel in (f"eval/{checkpoint}/generations.jsonl", "job.json", f"states/{checkpoint}/state.json")}
        listed.update({f"states/{checkpoint}/{k}": sha_bytes(v) for k, v in STATES.items() if k != "state.json"})
        (unit / "COMPLETE.json").write_text(json.dumps({"complete": True, "files": listed}))
    (tree / "JOB-DONE.json").write_text(json.dumps({"ok": True}))
    return tree


def _check(kit, host: str, checkpoint: str) -> subprocess.CompletedProcess:
    return subprocess.run([*PY, str(kit.root / "states_tool.py"), "check", host, checkpoint], capture_output=True, text=True, env=ENV)


def test_the_states_check_skips_the_untuned_unit_and_refuses_a_tree_without_the_checkpoint(kit):
    """Verify fix D1: the probe pod's tree holds the untuned unit (states/init/ only) and the e1 unit."""
    retrieved = kit.root / "retrieved" / "olmo3-7b-1101"
    tree = _probe_tree(retrieved)
    _states_tar(retrieved / "states-e1-20261105T000000Z.tar", {f"round1/1101-a0-e1-a1/states/e1/{k}": v for k, v in STATES.items()})
    done = _check(kit, "olmo3-7b-1101", "e1")
    assert done.returncode == 0 and done.stdout.startswith("states verified: 1 units"), done.stderr[-300:]
    record = json.loads(sorted(retrieved.glob("states-e1-check-*.json"))[-1].read_text())
    assert record["units"] == {"1101-a0-init-a1": "not saved", "1101-a0-e1-a1": {"files": 4, "bytes": 32 + 32 + 8 + len(STATES["state.json"])}}
    assert record["verified_units"] == 1 and record["members"] == 4 and record["version"] == 2
    assert (tree / "round1" / "1101-a0-e1-a1" / "states" / "e1" / "adapter.safetensors").read_bytes() == b"A" * 32
    _states_tar(retrieved / "states-init-20261105T000000Z.tar", {f"round1/1101-a0-init-a1/states/init/{k}": v for k, v in STATES.items()})
    init = _check(kit, "olmo3-7b-1101", "init")                                 # the init state: the e1 unit has none
    assert init.returncode == 0 and init.stdout.startswith("states verified: 1 units"), init.stderr[-300:]
    _states_tar(retrieved / "states-q-20261105T000000Z.tar", {f"round1/1101-a0-e1-a1/states/q/{k}": v for k, v in STATES.items()})
    none = _check(kit, "olmo3-7b-1101", "q")                                    # no unit lists q: refused, nothing written
    assert none.returncode == 2 and "no unit of the tree lists a states/q/ file" in none.stderr
    assert not list(retrieved.glob("states-q-check-*.json"))
    _states_tar(retrieved / "states-e1-20261105T000001Z.tar", {f"round1/1101-a0-init-a1/states/e1/{k}": v for k, v in STATES.items()})
    extra = _check(kit, "olmo3-7b-1101", "e1")                                  # a unit the tree does not seal with e1
    assert extra.returncode == 2 and "the tree does not seal with that checkpoint: 1101-a0-init-a1" in extra.stderr


def _tar_bytes(members: dict) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            if data is None:
                info.type = tarfile.DIRTYPE
                archive.addfile(info)
            else:
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def test_pull_states_refuses_an_archive_without_a_file(kit, monkeypatch):
    """Verify note 7: GNU tar writes a 10 KiB archive of zero blocks for an empty -T list; a folder entry alone is empty too."""
    host = kit("host.py")
    monkeypatch.setattr(host, "ssh_base", lambda h: ["-p", "22", "root@0.0.0.0"])
    archives = iter([b"\0" * 10240, _tar_bytes({"round1/1101-a0-e1-a1/states/e1": None}),
                     _tar_bytes({"round1/1101-a0-e1-a1/states/e1": None, "round1/1101-a0-e1-a1/states/e1/adapter.safetensors": b"A" * 32})])

    def fake_ssh(args, stdout=None, **kwargs):
        assert args[0] == "ssh" and "ls -d round1/*/states/e1" in args[-1]
        stdout.write(next(archives))
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(host.subprocess, "run", fake_ssh)
    retrieved = kit.root / "retrieved" / "olmo3-7b-1101"
    assert host.pull_states("olmo3-7b-1101", "e1") == 1
    assert host.pull_states("olmo3-7b-1101", "e1") == 1
    assert sorted(p.name for p in retrieved.iterdir()) == []                        # nothing kept, nothing recorded
    assert host.pull_states("olmo3-7b-1101", "e1") == 0
    kept = sorted(retrieved.glob("states-e1-*.tar"))
    assert len(kept) == 1 and host.tar_file_count(kept[0]) == 1
    line = json.loads((retrieved / "pulls.jsonl").read_text().strip())
    assert line["kind"] == "states e1" and line["file"] == kept[0].name and line["sha256"] == sha(kept[0])
    with pytest.raises(SystemExit, match="checkpoint must be one of"):
        host.pull_states("olmo3-7b-1101", "e2")


# ----- the finisher: the state rule's pull before the stop (verify fix D2) ------------------------------------------


def _plan(root: Path, probe: str = "olmo3-7b") -> str:
    """plan.json with the probe pod's one host (the shape plan_tool.first_host writes); returns the host name."""
    import probes
    spec = probes.PROBES[probe]
    host = f"{probe}-1101"
    entry = {"role": "first", "arm": "a0", "seed": 1101, "prepared": spec["prepared"], "base_eval": True,
             "cap_hours": spec["cap_hours"], "preflight_wait_s": spec["preflight_wait_s"],
             "container_disk_gb": spec["container_disk_gb"], "volume_gb": spec["volume_gb"]}
    (root / "plan.json").write_text(json.dumps({"probe": probe, "recipe_path": spec["recipes"][0], "checkpoints": ["e1"],
                                                "first_host_recipes": spec["recipes"], "hosts": {host: entry}}))
    (root / "hosts" / host).mkdir(parents=True, exist_ok=True)
    return host


def _finisher(kit, monkeypatch, states_tar: dict | None):
    """The finisher on the probe pod's tree with a fake host.py: pull-states writes STATES_TAR under the e1 unit into
    retrieved/HOST/ and prints host.py's record line (None: the pull fails); every other command succeeds.
    states_tool.py check runs for real from the kit copy."""
    fin = kit("finisher.py")
    host = _plan(kit.root)
    retrieved = kit.root / "retrieved" / host
    tree = _probe_tree(retrieved)
    (retrieved / "pull-20261105T000000Z.tar").write_bytes(b"transport")
    calls, lines = [], []

    def fake_tool(*a):
        calls.append(a)
        if a[0] == "pull-states":
            if states_tar is None:
                return subprocess.CompletedProcess(a, 1, "", "ssh: connect to host 0.0.0.0 port 22: Connection refused\n")
            dest = retrieved / f"states-{a[2]}-20261105T000001Z.tar"
            _states_tar(dest, {f"round1/1101-a0-e1-a1/states/{a[2]}/{k}": v for k, v in states_tar.items()})
            return subprocess.CompletedProcess(a, 0, json.dumps({"file": dest.name, "bytes": dest.stat().st_size, "sha256": sha(dest)}) + "\n", "")
        return subprocess.CompletedProcess(a, 0, "stopped", "")
    monkeypatch.setattr(fin, "tool", fake_tool)
    monkeypatch.setattr(fin, "unpack", lambda h: tree)
    monkeypatch.setattr(fin, "log", lambda **f: lines.append(f))
    return fin, host, tree, calls, lines


def test_the_finisher_pulls_and_checks_the_e1_states_before_the_stop(kit, monkeypatch):
    fin, host, tree, calls, lines = _finisher(kit, monkeypatch, STATES)
    assert fin.STATE_PULLS == ("e1",)
    fin.finish(host, {"exit_code": 0, "elapsed_s": 60})
    assert [c[0] for c in calls] == ["pull-light", "pull-states", "extend-cap", "stop"] and calls[1] == ("pull-states", host, "e1")
    record = json.loads((kit.root / "hosts" / host / "finished.json").read_text())
    assert record["status"] == "verified-and-stopped" and record["stop_confirmed"] is True
    e1 = record["states"]["e1"]
    assert e1["pulled"] is True and e1["verified"] is True and e1["file"] == "states-e1-20261105T000001Z.tar"
    assert e1["check"].startswith("states verified: 1 units")
    retrieved = kit.root / "retrieved" / host
    assert sorted(p.name for p in retrieved.glob("*.tar")) == ["states-e1-20261105T000001Z.tar"]   # the light tar removed, the states tar kept
    assert lines[-1]["removed_archives"] == ["pull-20261105T000000Z.tar"]
    check = json.loads(sorted(retrieved.glob("states-e1-check-*.json"))[-1].read_text())
    assert check["units"]["1101-a0-init-a1"] == "not saved" and check["units"]["1101-a0-e1-a1"]["files"] == 4 and check["verified_units"] == 1
    assert (tree / "round1" / "1101-a0-e1-a1" / "states" / "e1" / "adapter.safetensors").read_bytes() == b"A" * 32
    assert not (tree / "round1" / "1101-a0-init-a1" / "states" / "e1").exists()
    assert [line["event"] for line in lines] == ["states-verified", "verified", "finished"]
    assert not any("delete" in " ".join(c) or "terminate" in " ".join(c) for c in calls)


@pytest.mark.parametrize("failure", ["pull", "check"])
def test_a_failed_states_pull_or_check_is_recorded_and_the_pod_still_stops(kit, monkeypatch, failure):
    tar = None if failure == "pull" else {**STATES, "adapter.safetensors": b"B" * 32}
    fin, host, tree, calls, lines = _finisher(kit, monkeypatch, tar)
    fin.finish(host, {"exit_code": 0, "elapsed_s": 60})
    assert calls[-2:] == [("extend-cap", host, "120"), ("stop", host)]
    record = json.loads((kit.root / "hosts" / host / "finished.json").read_text())
    assert record["status"] == "review-needed-stopped" and record["stop_confirmed"] is True
    e1 = record["states"]["e1"]
    if failure == "pull":
        assert e1 == {"pulled": False, "verified": False, "note": "ssh: connect to host 0.0.0.0 port 22: Connection refused"}
    else:
        assert e1["pulled"] is True and e1["verified"] is False and "1 state file(s) missing or changed" in e1["check"]
        assert (kit.root / "retrieved" / host / e1["file"]).is_file()                   # the pulled tar stays for the lead
    alerts = [line for line in lines if line["event"] == "states-not-verified"]
    assert len(alerts) == 1 and "the user starts the pod" in alerts[0]["alert"]
    assert "removed_archives" not in lines[-1] and (kit.root / "retrieved" / host / "pull-20261105T000000Z.tar").is_file()


# ----- the Mac fetch entry, the kit's contents, the original kit -----------------------------------------------------


def test_the_mac_fetch_has_the_olmo3_entry_with_the_receipts_blob_ids(kit):
    fetch = kit("fetch_tokenizers_mac.py")
    spec = fetch.FAMILIES["olmo3"]
    assert (spec["repo_id"], spec["revision"], spec["gated"]) == ("allenai/Olmo-3-7B-Instruct", "6e5971d9eba42665f5bd5a0fcf047f299ce1dccc", False)
    assert sorted(spec["oids"]) == ["chat_template.jinja", "config.json", "merges.txt", "special_tokens_map.json",
                                    "tokenizer.json", "tokenizer_config.json", "vocab.json"]
    receipt = ROOT / ".ai/inputs/stage1-post-w1-20261023/olmo3/tokenizer-receipt-olmo3.json"
    if receipt.is_file():
        record = json.loads(receipt.read_text())
        assert {k: v["blob_id"] for k, v in record["files"].items()} == spec["oids"] and record["revision"] == spec["revision"]
    original = load_module(ORIGINAL / "fetch_tokenizers_mac.py", "original_fetch")
    assert {k: fetch.FAMILIES[k] for k in original.FAMILIES} == original.FAMILIES


def test_the_kit_holds_its_files_and_every_script_compiles(tmp_path):
    names = {p.relative_to(KIT).as_posix() for p in KIT.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    assert names == {"README.md", "account.py", "budget.py", "control_token_count_olmo3.py", "fetch_tokenizers_mac.py",
                     "finisher.py", "host.py", "launch.py", "orchestrate.py", "pack_setup.py", "plan_tool.py",
                     "probe_constants.py", "probes.py", "second_judge_probe.py", "secret_scan.py", "states_tool.py", "status.py",
                     "gate_a/gate_a_common_olmo3.py", "gate_a/gate_a_common_olmo3_test.py",
                     "setup/bootstrap_hr.sh", "setup/download_models_probe.py", "setup/extend_cap.py",
                     "setup/job_runner_probe.py", "setup/preflight_probe.py", "setup/requirements-olmo3.lock",
                     "setup/setup_and_fetch_probe.sh", "tests/test_family_probe_olmo3.py"}
    for name in names:
        if name.endswith(".py"):
            py_compile.compile(str(KIT / name), cfile=str(tmp_path / "x.pyc"), doraise=True)
    secret_scan = load_module(KIT / "secret_scan.py", "olmo3_secret_scan")
    assert secret_scan.scan_paths([KIT / n for n in sorted(names) if n != "secret_scan.py"]) == []
    assert sha(KIT / "setup" / "requirements-olmo3.lock") == LOCK_SHA
    assert 'f"attribution-probe-{host}' in (KIT / "host.py").read_text()


def test_the_original_kit_is_unchanged():
    status = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "runkit/family-probe"], capture_output=True, text=True)
    assert status.returncode == 0 and status.stdout.strip() == ""
    for name in ("account.py", "launch.py", "orchestrate.py", "second_judge_probe.py", "secret_scan.py", "status.py",
                 "setup/bootstrap_hr.sh", "setup/download_models_probe.py", "setup/extend_cap.py", "setup/job_runner_probe.py",
                 "setup/setup_and_fetch_probe.sh"):
        assert sha(KIT / name) == sha(ORIGINAL / name), name                     # untouched copies
    assert "STATE_PULLS" in (KIT / "finisher.py").read_text() and "STATE_PULLS" not in (ORIGINAL / "finisher.py").read_text()
