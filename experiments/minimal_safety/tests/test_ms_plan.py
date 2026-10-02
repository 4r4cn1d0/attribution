"""Config validation and the offline dry run. Standard library only; the dry run executes in
a fresh interpreter with sockets disabled and must not import any heavy library."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from experiments.minimal_safety.plan import ConfigError, build_plan, load_config, validate

ROOT = Path(__file__).resolve().parents[3]
SHIPPED = ROOT / "experiments" / "minimal_safety" / "configs" / "calibration.json"
CUDA = SHIPPED.with_name("calibration-cuda.json")
HEAVY = ("torch","transformers", "peft", "numpy", "safetensors", "huggingface_hub", "tokenizers")


def test_shipped_config_matches_the_brief():
    config = load_config(SHIPPED)
    model, train, design = config["model"], config["train"], config["design"]
    assert (model["repo_id"], model["revision"]) == ("Qwen/Qwen2.5-0.5B-Instruct",
                                                     "7ae557604adf67be50417f59c2c2f167def9a775")
    assert model["lora"] == {"r": 8, "alpha": 16, "dropout": 0.0, "target_modules": ["q_proj", "v_proj"],
                             "expected_trainable_parameters": 540672}
    assert (model["dtype"], model["attn_implementation"]) == ("float32", "eager")
    assert config["scorer"]["revision"] == "4d6c22e74ba2fdd26bc4f7238f50766b045a0d94"
    assert config["dataset"]["revision"] == "ad96bd4dca687d8e1d9b6fd4b9eb8dcdddb0361d"
    assert config["dataset"]["train_sha256"].startswith("dcc91989")
    assert config["dataset"]["ref_sha256"].startswith("75351ed4")
    assert sum(design["train_counts"].values()) == 128 and design["removal"]["size"] == 8
    assert (train["seeds"], train["short_steps"], train["long_steps"], train["batch_size"]) == (
        [101, 202], 4, 16, 1)
    assert config["caps"] == {"wall_seconds": 900, "output_bytes": 2 * 1024**3}


def test_cuda_profile_is_the_frozen_recipe_with_only_its_name_and_model_device_changed():
    frozen, cuda = load_config(SHIPPED), load_config(CUDA)
    assert (frozen["model"]["device"], cuda["model"]["device"]) == ("mps", "cuda")
    assert cuda["name"] != frozen["name"]
    for config in (frozen, cuda):
        del config["name"], config["model"]["device"]
    assert cuda == frozen


@pytest.mark.parametrize("edit, message", [
    (lambda c: c.update(extra=1), "unknown"),
    (lambda c: c["train"].pop("lr"), "missing"),
    (lambda c: c["train"].update(batch_size=2), "batch_size"),
    (lambda c: c["eval"].update(decoding="sample"), "decoding"),
    (lambda c: c["design"]["train_counts"].update(Benign=200), "total"),
    (lambda c: c["design"]["removal"].update(size=99), "removal.size"),
    (lambda c: c["train"].update(short_steps=4, long_steps=4), "short_steps"),
    (lambda c: c["model"].update(device="cuda:0"), "device"),
    (lambda c: c["scorer"].update(device="cuda"), "scorer.device"),
    (lambda c: c["model"].update(revision="main"), "revision"),
    (lambda c: c["caps"].update(wall_seconds=0), "caps"),
])
def test_validation_rejects_incomplete_or_unsupported_settings(edit, message):
    config = copy.deepcopy(load_config(SHIPPED))
    edit(config)
    with pytest.raises(ConfigError, match=message):
        validate(config)


def test_plan_reports_streams_and_counts(prepared):
    config, prep_dir, digest = prepared
    plan = build_plan(config, prep_dir)
    assert plan["status"] == "not run" and plan["arms"] == ["a0", "remove_fixture2"]
    assert plan["operations"]["optimizer_steps"] == 16 and plan["operations"]["evaluations"] == 9
    assert plan["prepared"]["manifest_sha256"] == digest
    assert plan["prepared"]["consistent_with_config"] is True
    assert set(plan["prepared"]["exposure"]) == {"1", "2"}
    assert plan["assets"]["model"]["present"] is False  # fixture ids are never cached


def test_dry_run_is_offline_and_imports_no_heavy_library(tmp_path, prepared):
    config, prep_dir, digest = prepared
    config_path = tmp_path / "fixture-config.json"
    config_path.write_text(json.dumps(config))
    code = textwrap.dedent(f"""
        import json, socket, sys
        def _blocked(*args, **kwargs):
            raise RuntimeError("network access attempted during dry run")
        socket.socket = _blocked
        socket.create_connection = _blocked
        from experiments.minimal_safety.__main__ import main
        rc = main(["plan", "--config", {str(config_path)!r}, "--prepared", {str(prep_dir)!r}])
        heavy = sorted(m for m in {HEAVY!r} if m in sys.modules)
        print(json.dumps({{"rc": rc, "heavy": heavy}}), file=sys.stderr)
    """)
    env = {**os.environ, "PYTHONPATH": str(ROOT), "HF_HUB_CACHE": str(tmp_path / "empty-cache")}
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True,
                          text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stderr.strip().splitlines()[-1]) == {"rc": 0, "heavy": []}
    plan = json.loads(proc.stdout)
    assert plan["status"] == "not run" and plan["prepared"]["manifest_sha256"] == digest
