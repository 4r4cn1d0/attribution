"""B10's pinned settings: the literal SHA-256 pin (the T1 convention), the canonical bytes, every pin's value against
its binding source (REF R.0.7 and L.4, the recipe file, engine X), and every refusal of validate_settings and
validate_job. Standard library and the engine's stdlib modules only (no model)."""

from __future__ import annotations

import copy
import json

import pytest

import b10_fixtures as fb

from experiments.safety_selection.common import canonical_json, code_identity, sha256_file
from experiments.safety_selection.config import config_sha256, load_recipe, training_identity
from scripts.stage1 import s1common as s1
from scripts.stage1_s1 import eval_adapter as ea
from scripts.stage1_s1 import repin_reference_seeds as rp


def sl_settings_path():
    return ea.REPO / "scripts" / "stage1_s1" / "settings" / "safe_lora.json"

LITERAL = "9cc654ecef9fd35664599baba49eaced218afaa6a6a738771d93d962314fbe9b"
# REF (stage1-prereg-references-DRAFT.md revision 2) R.0.7 and the L.4 table; scripts/gate_b_reading.py:168-169
GATE_A = {"1101": ("8f0fa83a42ccc5edc54a5ee26ed63f49448c36d30adbd64e28b655678afee4c9",
                   "aad79060c52304ecd1b3d0a24b26281da7d147b0fc4a2754ba3a9b323bfae1ec",
                   "322d737a2e0177c85b798ac779e42e637b6617cfd842455c3e1bdf4586008660"),
          "1102": ("857f78bc0f49cc8a4902fbb6211f463daa7c7f44086257c4d752409a30ba0b25", "7c9111c2093b00f2", None),
          "1103": ("7be58eaa9c5be7b8f94668109efd6aae075b1d001e0d2b1fb8be814556899cbd", "b1ad020bc8d1b1c1", None)}
UNTUNED = "b5083ce9d9f26efe92f9872fdbf9376a521a5d99d1b70cc2bd460987cdcc9474"
# the user's SP decision (29 Oct 2026; addendum section 34 point 4): the pinned file and its record
SP_FILE = ".ai/inputs/stage1-post-w1-20261023/block-b/sp_prefix_llama2_default_ptst.txt"
SP_RECORD = ".ai/inputs/stage1-post-w1-20261023/block-b/user_decision_block_b_scope_and_sp.json"
SP_SHA256 = "0fcc6beb8240d7b8e7b8c19bb033af6c8a66e568e50afc33f58707a503fdec98"


def test_the_settings_file_is_pinned_by_its_literal_sha256_and_is_canonical_json():
    assert ea.SETTINGS_SHA256 == LITERAL == sha256_file(ea.SETTINGS_PATH)
    pinned = ea.load_pinned_settings()
    assert pinned.sha256 == LITERAL and ea.validate_settings(fb.real_doc()) == pinned.doc
    assert canonical_json(pinned.doc) == ea.SETTINGS_PATH.read_bytes()
    with pytest.raises(s1.Refusal, match="hash to"):
        s1.load_settings(ea.SETTINGS_PATH, "0" * 64, ea.SETTINGS_NAME)


def test_every_pin_is_its_binding_sources_value():
    doc = fb.real_doc()
    assert doc["engine_x"] == code_identity()["sha256"] == "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
    recipe_path = ea.ENGINE_REPO / doc["recipe"]["path"]
    assert sha256_file(recipe_path) == doc["recipe"]["file_sha256"]
    assert doc["recipe"]["file_sha256"].startswith("a47138f2f4fb032a")                      # REF source table, REC
    recipe = load_recipe(recipe_path)
    assert config_sha256(recipe) == doc["recipe"]["config_sha256"] and doc["recipe"]["config_sha256"].startswith(
        "9e9bde6f2f328760")                                                                   # REF L.4 recipe hash
    assert training_identity(recipe) == doc["recipe"]["training_identity"]
    assert doc["recipe"]["training_identity"].startswith("f46279e5830f4777")                 # RQ section 3.2
    assert doc["prepared"]["manifest_sha256"].startswith("9ed61826") and doc["prepared"]["bank"] == "dev"
    for seed, (complete, e1, q) in GATE_A.items():
        entry = doc["reference_units"][seed]
        assert entry["complete_sha256"] == complete
        assert entry["fingerprint_prefixes"] == {"e1": e1, "q": q}
    # Gate A's three, and any seed 1104-1107 the mid-block re-pin added (the same seeds in B11, by its rule)
    assert set(GATE_A) <= set(doc["reference_units"])
    assert rp.check_seed_pins(doc, s1.strict_json(sl_settings_path().read_bytes())) == sorted(
        set(doc["reference_units"]) - set(GATE_A))
    assert doc["untuned_unit"]["complete_sha256"] == UNTUNED and doc["untuned_unit"]["seed"] == 1101
    assert doc["checkpoint"] == "e1" and doc["label_entries"] == {}
    assert doc["adapter_scale"]["allowed"] == [1.0, 0.9, 0.75, 0.5, 0.0]          # 0.9: LN-15b, addendum 34.5
    assert doc["adapter_scale"]["planned"] == [0.9, 0.75, 0.5]
    assert doc["adapter_scale"]["curve"] == [1.0, 0.75, 0.5, 0.0]
    record = json.loads((ea.ENGINE_REPO / SP_RECORD).read_bytes())                            # the user's decision
    assert doc["prefix"]["text_sha256"] == SP_SHA256 == record["sp_text"]["sha256"] == sha256_file(
        ea.ENGINE_REPO / SP_FILE)
    assert doc["prefix"]["source"] == record["sp_text"]["source"] and record["user_words"] == "Yes, both"
    assert "no documented system turn or default system prompt" in doc["prefix"]["status"]
    assert "system branch" in doc["prefix"]["status"] and "max_prompt_tokens" in doc["prefix"]["length_rule"]
    assert doc["prefix"]["separator"] == "\n\n" and doc["prefix"]["guard_sees"] == "original user text"
    assert doc["prefix"]["apply_to"] == list(ea.PREFIX_KINDS)
    assert set(doc["external_transforms"]) == {"safe_lora"}      # addendum 11.5 (test_b10_b11_integration pins it)
    cert = doc["certification"]
    assert (cert["seed"], cert["mode"], cert["gate_fields"], cert["expected_sampled_answers"]) == (
        1101, "certify", ["valid", "safety"], 600)                                                # LS-08 (a); 200 x 3
    assert doc["regeneration"]["job"] == ea.REGEN_JOB and doc["regeneration"]["registry"] is None
    assert {"q", "e1"} <= set(doc["regeneration"]["compare_checkpoints"])
    # REF R.0.7 (the e1 fingerprint rule) and the engine's eval-state rule (the training identity): the recipe's
    # whole config hash is reported, not required (fix round S-3; LS-04 (b) and stage-1 a0 sources)
    assert doc["regeneration"]["compare_identity"] == ["manifest_sha256", "training_identity"]
    assert doc["regeneration"]["report_identity"] == ["recipe_sha256"]
    # addendum section 11 point 1: every evaluation runs the shared O-ext function, pinned by module and settings
    from scripts.stage1_s1 import oext_eval as oe

    assert doc["overrefusal_bank"]["status"] == "oext_pinned"
    assert doc["oext"]["module"] == "scripts/stage1_s1/oext_eval.py" and doc["oext"]["module_sha256"] == sha256_file(
        ea.REPO / doc["oext"]["module"]) == oe.module_sha256()
    assert doc["oext"]["settings"] == {"path": "scripts/stage1_s1/settings/oext_eval.json",
                                       "sha256": sha256_file(oe.SETTINGS_PATH)} and oe.SETTINGS_SHA256 == sha256_file(
        oe.SETTINGS_PATH)
    assert doc["oext"]["branch"] == oe.load_pinned_settings().doc["cap"]["branch"] == "128"   # section 13; 11.7 re-pin
    assert doc["oext"]["outputs"] == list(oe.OUTPUT_FILES)
    assert "oext" not in ea.CERTIFIED_SETTINGS_KEYS and "overrefusal_bank" not in ea.CERTIFIED_SETTINGS_KEYS
    fields = cert["environment_fields"]
    assert "environment_lock.sha256" in fields and "environment.cuda.capability" in fields
    assert "environment.cuda.driver" in fields and "environment.cuda.env.CUBLAS_WORKSPACE_CONFIG" in fields
    assert not any(f.endswith(("torch_threads", "platform", "python", "CUDA_VISIBLE_DEVICES")) for f in fields)


def test_the_generation_kinds_are_the_engines():
    from experiments.safety_selection import runner

    assert ea.GENERATION_KINDS == runner.GENERATION_KINDS
    assert set(ea.PREFIX_KINDS) == set(runner.GENERATION_KINDS) | {"arc_utility", "task_rows"}


MUTATIONS = [
    ("version", 2), ("owner", "scripts/stage1/other.py"), ("label_entries", {"x.y": "0" * 64}),
    ("requirement", " "), ("recipe.config_sha256", "nothex"), ("recipe.path", ""),
    ("prepared.bank", "hidden"), ("prepared.bank", "selector"), ("checkpoint", "e3"),
    ("regeneration.job.evaluate_bank", "dev"), ("regeneration.job.arm", "edit-x"), ("regeneration.job.pin_code", False),
    ("regeneration.registry", "registry.jsonl"), ("regeneration.compare_checkpoints", ["e1"]),
    ("regeneration.compare_checkpoint_fields", ["step"]), ("regeneration.compare_trajectory", []),
    ("reference_units", {}), ("reference_units.1101.complete_sha256", "0" * 63),
    ("reference_units.1101.fingerprint_prefixes", {"q": None}),
    ("reference_units.1101.fingerprint_prefixes", {"e1": None}),
    ("reference_units.1101.fingerprint_prefixes", {"e1": "abc"}),
    ("reference_units.1101.fingerprint_prefixes", {"e1": "aad79060c52304ec", "e3": None}),
    ("untuned_unit.checkpoint", "e1"), ("untuned_unit.seed", 1199),
    ("adapter_scale.allowed", [0.75, 0.5]), ("adapter_scale.allowed", [1.0, 1.5]),
    ("adapter_scale.allowed", [1.0, 0.5, 0.5]), ("adapter_scale.allowed", [1.0, True]),
    ("adapter_scale.planned", [1.0]), ("adapter_scale.planned", [0.8]), ("adapter_scale.factor", "lora_A"),
    ("prefix.text_sha256", "0" * 63), ("prefix.source", None), ("prefix.source", " "), ("prefix.length_rule", " "),
    ("prefix.length_rule", None), ("prefix.separator", "--"), ("prefix.separator", " " * 9),
    ("prefix.apply_to", ["harm", "hidden"]), ("prefix.apply_to", []), ("prefix.guard_sees", "prefixed text"),
    ("external_transforms", []), ("evaluation.bank", "hidden"), ("evaluation.job_seed", "fresh"),
    ("certification.seed", 1199), ("certification.mode", "scale"), ("certification.gate_fields", ["safety"]),
    ("certification.expected_sampled_answers", 0), ("certification.expected_sampled_answers", True),
    ("certification.required_reference_files", ["samples.jsonl"]), ("exit_codes", {"0": "done"}),
    ("regeneration.compare_identity", ["manifest_sha256"]), ("regeneration.compare_identity", ["training_identity"]),
    ("regeneration.compare_identity", ["manifest_sha256", "training_identity", "other"]),
    ("regeneration.report_identity", ["training_identity"]), ("regeneration.report_identity", ["other"]),
    ("regeneration.report_identity", ["recipe_sha256", "recipe_sha256"]), ("regeneration.report_identity", None),
    ("certification.environment_fields", ["environment.device"]),
    ("certification.environment_fields", ["environment_lock.sha256", "other.device"]),
    ("certification.environment_fields", ["environment_lock.sha256", "environment"]),
    ("certification.environment_fields", []), ("certification.reference_rule", " "),
    ("overrefusal_bank.status", "o-ext"), ("overrefusal_bank.status", None), ("overrefusal_bank.rule", ""),
    ("overrefusal_bank", {"status": "open"}),
    ("engine_x", "0" * 64), ("name", "other"), ("kind", "other"),
]


@pytest.mark.parametrize("dotted, value", MUTATIONS, ids=[f"{d}={v!r}"[:60] for d, v in MUTATIONS])
def test_validate_settings_refuses_each_changed_rule(dotted, value):
    doc = copy.deepcopy(fb.real_doc())
    fb.set_dotted(doc, dotted, value)
    with pytest.raises(s1.Refusal):
        ea.validate_settings(doc)


def test_validate_settings_refuses_an_added_or_missing_key():
    doc = copy.deepcopy(fb.real_doc())
    doc["extra"] = 1
    with pytest.raises(s1.Refusal):
        ea.validate_settings(doc)
    doc = copy.deepcopy(fb.real_doc())
    del doc["combination_rule"]
    with pytest.raises(s1.Refusal):
        ea.validate_settings(doc)


GOOD_ENTRY = {"kind": "callable", "module": fb.TRANSFORM_MODULE, "module_sha256": "a" * 64, "function": "identity",
              "settings": None, "record_keys": None, "require_lora_a_unchanged": False, "role": "fixture"}
FILE_KEYS = {"transform_sha256": "a", "source_adapter_fingerprint": "b", "output_adapter_fingerprint": "c",
             "output_file_sha256": "d"}
BAD_ENTRIES = [
    {"kind": "merge"}, {"module": "experiments/safety_selection/engine.py"}, {"module": "scripts/../x.py"},
    {"module_sha256": "a"}, {"function": "not an identifier"}, {"record_keys": FILE_KEYS},
    {"kind": "file", "function": None}, {"kind": "file", "function": "f", "record_keys": FILE_KEYS},
    {"kind": "file", "function": None, "record_keys": {"transform_sha256": "a"}},
    {"settings": {"path": "x"}}, {"settings": {"path": "x", "sha256": "b"}},
    {"kind": "file", "function": None, "record_keys": FILE_KEYS, "settings": {"path": "x", "sha256": "b" * 64}},
    {"kind": "file", "function": None, "record_keys": {**FILE_KEYS, "transform_settings_sha256": "e"}},
    {"require_lora_a_unchanged": "yes"}, {"role": ""}]


@pytest.mark.parametrize("change", BAD_ENTRIES, ids=[str(sorted(c)) for c in BAD_ENTRIES])
def test_validate_settings_refuses_a_malformed_external_transform(change):
    doc = copy.deepcopy(fb.real_doc())
    doc["external_transforms"] = {"t": {**GOOD_ENTRY, **change}}
    with pytest.raises(s1.Refusal):
        ea.validate_settings(doc)


def test_validate_settings_accepts_well_formed_transforms_and_a_pinned_prefix():
    doc = copy.deepcopy(fb.real_doc())
    doc["external_transforms"] = {"t": dict(GOOD_ENTRY),
                                  "f": {**GOOD_ENTRY, "kind": "file", "function": None,
                                        "record_keys": {**FILE_KEYS, "transform_settings_sha256": "e"},
                                        "settings": {"path": "scripts/stage1_s1/settings/x.json", "sha256": "b" * 64}}}
    doc["prefix"].update(text_sha256="c" * 64, source="a citation")
    assert ea.validate_settings(doc) is doc
    doc["prefix"]["source"] = None
    with pytest.raises(s1.Refusal, match="citation"):
        ea.validate_settings(doc)
    doc = copy.deepcopy(fb.real_doc())
    doc["external_transforms"] = {"Bad-Name": dict(GOOD_ENTRY)}
    with pytest.raises(s1.Refusal, match="short id"):
        ea.validate_settings(doc)


def job(**changes) -> dict:
    base = {"kind": ea.JOB_KIND, "manifest_sha256": "a" * 64, "recipe_sha256": "b" * 64, "code_sha256": "c" * 64,
            "wall_limit_seconds": None, "source_run": "/x/run", "checkpoint": "e1", "evaluate_bank": "dev", "seed": 1101,
            "reference_complete_sha256": "d" * 64, "mode": "certify", "adapter_scale": 1.0, "prefix_sha256": None,
            "external": None, "settings_sha256": "e" * 64, "script_sha256": "f" * 64,
            "certification_report_sha256": None, "oext": None}
    return {**base, **changes}


def test_validate_job_accepts_each_mode_and_refuses_inconsistent_jobs():
    cert = "9" * 64
    assert ea.validate_job(job()) == job()
    assert ea.validate_job(job(mode="scale", adapter_scale=0.5, certification_report_sha256=cert))
    assert ea.validate_job(job(mode="prefix", prefix_sha256="1" * 64, certification_report_sha256=cert))
    assert ea.validate_job(job(mode="external", external={"name": "t"}, certification_report_sha256=cert))
    for bad in (job(kind="eval-state"), job(evaluate_bank="hidden"), job(mode="merge"), job(code_sha256=None),
                job(mode="certify", adapter_scale=0.5), job(mode="scale", adapter_scale=1.0),
                job(mode="certify", prefix_sha256="1" * 64), job(mode="certify", external={"name": "t"}),
                job(seed=True), job(adapter_scale="1"), job(prefix_sha256="x"),
                job(certification_report_sha256=cert), job(mode="scale", adapter_scale=0.5),
                job(mode="scale", adapter_scale=0.5, certification_report_sha256="x")):
        with pytest.raises(s1.Refusal):
            ea.validate_job(bad)
    extra = job()
    extra["more"] = 1
    with pytest.raises(s1.Refusal):
        ea.validate_job(extra)
    oext = {"branch": "128", "settings_sha256": "1" * 64, "module_sha256": "2" * 64, "record_sha256": "3" * 64,
            "bank_sha256": "4" * 64, "w1_18_record_sha256": "5" * 64}
    assert ea.validate_job(job(oext=oext))["oext"] == oext
    for bad in (dict(oext, branch="64"), {k: v for k, v in oext.items() if k != "bank_sha256"}, "128"):
        with pytest.raises(s1.Refusal):
            ea.validate_job(job(oext=bad))
    missing = job()
    del missing["oext"]
    with pytest.raises(s1.Refusal):
        ea.validate_job(missing)


def test_validate_settings_refuses_cases_that_pass_every_earlier_check():
    """Changes that s1common and the other B10 rules accept, so only the rule under test refuses."""
    doc = copy.deepcopy(fb.real_doc())
    key = sorted(s1.registry())[0]
    doc["label_entries"] = {key: s1.entry_digest(key)}               # a real entry with its own digest
    assert s1.check_settings(copy.deepcopy(doc), ea.SETTINGS_NAME)
    with pytest.raises(s1.Refusal, match="no registry entry"):
        ea.validate_settings(doc)
    doc = copy.deepcopy(fb.real_doc())
    doc["adapter_scale"].update(allowed=[0.75, 0.5, 0.0], curve=[0.75, 0.5, 0.0])   # planned stays [0.75, 0.5]
    with pytest.raises(s1.Refusal, match="including 1"):
        ea.validate_settings(doc)
    doc = copy.deepcopy(fb.real_doc())
    doc["regeneration"]["compare_checkpoints"] = ["e1"]
    for entry in doc["reference_units"].values():
        entry["fingerprint_prefixes"].pop("q")
    with pytest.raises(s1.Refusal, match="q and e1"):
        ea.validate_settings(doc)


def test_a_recipe_file_with_other_bytes_refuses_even_with_the_same_config(tmp_path):
    import json

    settings = ea.load_pinned_settings()
    path = ea.ENGINE_REPO / settings.doc["recipe"]["path"]
    assert ea.load_pinned_recipe(path, settings)["name"] == "study-kt-olmo2-1b-r64-b-mb4-20261008"
    other = tmp_path / "recipe.json"
    other.write_text(json.dumps(json.loads(path.read_text()), indent=4))   # the same config, other bytes
    assert config_sha256(load_recipe(other)) == settings.doc["recipe"]["config_sha256"]
    with pytest.raises(s1.Refusal, match="recipe file hashes to"):
        ea.load_pinned_recipe(other, settings)
