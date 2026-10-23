"""B11's settings file: its literal pin, the pre-registered values (REF R.1.3; PREREG section 5.4), the model pins
(no download), agreement with recipe B, and the refusals of a changed settings document. Also a static scan that the
transform draws no random number (ADD L13: Safe LoRA adds no seed label)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import b11_fixtures as fx
import pytest

import experiments.safety_selection as engine_package
from experiments.safety_selection.common import canonical_json, code_identity, sha256_bytes, sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1_s1 import safe_lora as sl

ENGINE_ROOT = Path(engine_package.__file__).resolve().parents[2]      # where the engine's configs live
SAFE_LORA_SETTINGS_SHA256 = "e8a011221b4392bf9ef4f5ad31fc7ed8a51a5d346a5405a92093072f8857ccc0"


def _doc() -> dict:
    return json.loads(sl.SETTINGS_PATH.read_bytes())


def test_the_settings_file_is_pinned_by_literal_and_loads():
    assert sha256_file(sl.SETTINGS_PATH) == SAFE_LORA_SETTINGS_SHA256 == sl.SETTINGS_SHA256
    assert sl.SETTINGS_PATH == s1.REPO / "scripts" / "stage1_s1" / "settings" / "safe_lora.json"
    settings = sl.load_pinned_settings()
    assert settings.sha256 == SAFE_LORA_SETTINGS_SHA256
    assert sl.SETTINGS_PATH.read_bytes() == canonical_json(_doc())


def test_the_pre_registered_rule_and_points():
    settings = sl.load_pinned_settings()
    doc = settings.doc
    assert settings.points == {"default": 39, "conditional": 12, "certify": 0}
    assert sl.POINTS == ("default", "conditional", "certify") and sl.CHECK_POINTS == ("default", "conditional")
    assert settings.matrices == 112 and settings.blocks == 16 and settings.rank == 64
    assert settings.modules == ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
    assert (doc["transform"]["operator"], doc["transform"]["factor"], doc["transform"]["rule"]) == (
        "fast_form_c", "lora_B", "top_k")
    assert settings.taus == (0.35, 0.5) and settings.threads == 1
    assert "UQ9" in settings.point_status["conditional"] and "FC-27" in settings.point_status["conditional"]
    assert settings.point_status["certify"].startswith("never a reference point") and "LQ11" in settings.point_status["certify"]
    assert doc["outputs"] == {"adapter": "adapter.safetensors", "record": "safe_lora_record.json",
                              "check_record": "safe_lora_check.json", "timing": "safe_lora_timing.json"}
    assert doc["engine_x"] == code_identity()["sha256"] == "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
    assert doc["label_entries"] == {} and doc["owner"] == "scripts/stage1_s1/safe_lora.py"


def test_the_model_pins_name_the_base_and_the_instruct_model_without_a_download():
    settings = sl.load_pinned_settings()
    base, aligned = settings.unaligned, settings.aligned
    assert (base["repo_id"], base["revision"], base["dtype"]) == (
        "allenai/OLMo-2-0425-1B", "a1847dff35000b4271fa70afc5db10fd29fedbdf", "float32")    # addendum 11.6: in full
    assert [f["sha256"] for f in base["files"]] == [
        "c52e4ac8bf4867e698d908f9e8c2b84aa891b91dff066d46bf2a7cf453ad77fb",
        "5f80762572fe28aca49b01b98895d96ca529b9792fc10925a977a161ad768d30"]
    assert [(f["file"], f["bytes"]) for f in base["files"]] == [("model-00001-of-00002.safetensors", 4983360992),
                                                                ("model-00002-of-00002.safetensors", 956326560)]
    assert base["total_bytes"] == 5939687552 and base["licence"] == "Apache-2.0" and base["gated"] is False
    assert base["stored_dtype"] == {"F32": 1484916736}
    assert "UQ1" in base["download"] and "never to the Mac" in base["download"]
    assert "revision = this full commit" in base["download"] and "never main" in base["download"]
    assert (aligned["repo_id"], aligned["revision"], aligned["dtype"]) == (
        "allenai/OLMo-2-0425-1B-Instruct", "48d788eca847d4d7548f375ad03d3c9312f6139e", "bfloat16")
    assert aligned["files"] == [{"file": "model.safetensors", "bytes": 2969854224,
                                 "sha256": "36d044c73655bb904f822915e6294ba3dae8e6e1af5e703e9d452f2d6a3a294f"}]


def test_the_accepted_fingerprints_are_the_gate_a_a0_e1_ones():
    """REF R.0.7 prints their prefixes; the full values come from each Gate A unit's states/e1/state.json."""
    accepted = sl.load_pinned_settings().accepted
    prefixes = {"1101": "aad79060c52304ec", "1102": "7c9111c2093b00f2", "1103": "b1ad020bc8d1b1c1"}
    assert set(accepted) == set(prefixes)
    for seed, prefix in prefixes.items():
        assert accepted[seed].startswith(prefix) and len(accepted[seed]) == 64
    assert sl.load_pinned_settings().state_checks == {"arm": "a0", "checkpoint": "e1"}


def test_the_adapter_structure_agrees_with_recipe_b():
    doc = _doc()
    recipe_path = ENGINE_ROOT / doc["recipe"]["path"]
    assert sha256_file(recipe_path) == doc["recipe"]["sha256"]
    recipe = json.loads(recipe_path.read_bytes())
    lora = recipe["model"]["lora"]
    assert list(doc["adapter"]["modules"]) == lora["target_modules"]
    assert (doc["adapter"]["rank"], doc["adapter"]["lora_alpha"]) == (lora["r"], lora["alpha"])
    assert doc["adapter"]["parameters"] == lora["expected_trainable_parameters"]
    assert recipe["model"]["repo_id"] == doc["models"]["aligned"]["repo_id"]
    assert recipe["model"]["revision"] == doc["models"]["aligned"]["revision"]
    assert recipe["model"]["base_dtype"] == doc["models"]["aligned"]["dtype"]
    # OLMo-2-0425-1B: hidden 2048, MLP 8192, no grouped heads (SL section 6): r * (in + out) per matrix
    shapes = {"q_proj": (2048, 2048), "k_proj": (2048, 2048), "v_proj": (2048, 2048), "o_proj": (2048, 2048),
              "gate_proj": (8192, 2048), "up_proj": (8192, 2048), "down_proj": (2048, 8192)}
    assert 16 * sum(64 * (o + i) for o, i in shapes.values()) == doc["adapter"]["parameters"] == 48234496


@pytest.mark.parametrize("change, match", [
    (lambda d: d["transform"]["points"]["default"].update(k=113), "outside 0..112"),
    (lambda d: d["transform"]["points"].pop("conditional"), "default, conditional, certify"),
    (lambda d: d["transform"]["points"].pop("certify"), "default, conditional, certify"),
    (lambda d: d["transform"]["points"]["certify"].update(k=1), "certify point maps nothing"),
    (lambda d: d["transform"]["points"]["certify"].update(k=0.0), "integer"),
    (lambda d: d["transform"].update(operator="exact_projector"), "fast form C"),
    (lambda d: d["transform"].update(factor="lora_A"), "fast form C"),
    (lambda d: d["transform"].update(torch_threads=0), "torch_threads"),
    (lambda d: d["adapter"].update(matrices=111), "blocks x modules"),
    (lambda d: d["adapter"].update(modules=["q_proj", "q_proj"]), "distinct"),
    (lambda d: d["adapter"].update(dtype="bfloat16"), "float32"),
    (lambda d: d["adapter"]["accepted"]["1101"].update(fingerprint="aad79060"), "fingerprint"),
    (lambda d: d["adapter"].update(accepted={}), "accepted"),
    (lambda d: d["adapter"].update(state_checks={"arm": "a0"}), "state_checks"),
    (lambda d: d["models"]["unaligned"].update(revision="a1847df"), "8-40"),
    (lambda d: d["models"]["unaligned"].update(revision="A1847DFF"), "lowercase hex"),
    (lambda d: d["models"]["unaligned"]["files"][0].update(sha256="c52e4ac8bf4"), "12-64"),
    (lambda d: d["models"]["unaligned"]["files"][0].update(url="x"), "other keys"),
    (lambda d: d["models"]["unaligned"].update(dtype="float16"), "dtype"),
    (lambda d: d["models"]["aligned"].update(files=[]), "non-empty"),
    (lambda d: d["models"].pop("aligned"), "aligned, unaligned"),
    (lambda d: d["report"].update(taus=[0.35, 2.0]), "taus"),
    (lambda d: d.update(label_entries={"s1.order": "0" * 64}), "registry entr"),
    (lambda d: d.update(owner="scripts/stage1/safe_lora.py"), "owned by"),
    (lambda d: d.update(engine_x="0" * 64), "engine"),
    (lambda d: d["outputs"].update(record="adapter.safetensors"), "four distinct output files"),
    (lambda d: d["outputs"].update(timing="safe_lora_record.json"), "four distinct output files"),
    (lambda d: d["outputs"].pop("timing"), "four distinct output files"),
    (lambda d: d["outputs"].update(check_record="../x.json"), "four distinct output files"),
    (lambda d: d.pop("outputs"), "four distinct output files"),
])
def test_a_changed_settings_document_refuses(change, match):
    doc = _doc()
    change(doc)
    with pytest.raises(s1.Refusal, match=match):
        sl.validate_settings(doc, sha256_bytes(canonical_json(doc)))


def test_a_valid_registry_entry_is_refused_because_safe_lora_draws_nothing():
    doc = _doc()
    doc["label_entries"] = {"s1.order": s1.entry_digest("s1.order")}
    s1.check_settings(doc, sl.NAME)                                  # the shared check accepts it ...
    with pytest.raises(s1.Refusal, match="names no registry entry"):  # ... this file does not
        sl.validate_settings(doc, sha256_bytes(canonical_json(doc)))


def test_changed_settings_bytes_refuse_on_the_pin(tmp_path):
    doc = _doc()
    doc["transform"]["points"]["default"]["k"] = 38
    path, _ = fx.write_settings_file(tmp_path, doc)
    with pytest.raises(s1.Refusal, match="expected"):
        sl.load_pinned_settings(path)
    assert sl.load_pinned_settings(path, sha256_file(path)).points["default"] == 38


# A static scan in the form of T1's (scripts/stage1/tests/test_labels.py); it catches ordinary draws only.
RANDOM_CALL = re.compile(r"\bderive_seed\b|\brandom\.(?:Random|SystemRandom|seed|shuffle|sample|choices?|random|randrange"
                         r"|randint|uniform|gauss|getrandbits)\b|\bdefault_rng\b|\bRandomState\b|\bnumpy\.random\b"
                         r"|\bnp\.random\b|^\s*import random\b|^\s*from random\b|^\s*from numpy import\b.*\brandom\b"
                         r"|^\s*from numpy\.random\b|\btorch\.(?:Generator|manual_seed|rand\w*|seed)\b|\bhashlib\b"
                         r"|\bsecrets\b|\burandom\b", re.MULTILINE)
LABEL_LITERAL = re.compile(r"\bstage1-[a-z0-9]+(?:-[a-z0-9]+)*-v[1-9][0-9]*\b")


def test_the_transform_draws_no_random_number_and_names_no_seed_label():
    for path in (sl.SETTINGS_PATH.parents[1] / "safe_lora.py", sl.SETTINGS_PATH):
        text = path.read_text()
        assert not RANDOM_CALL.search(text), path.name
        assert not LABEL_LITERAL.search(text), path.name
