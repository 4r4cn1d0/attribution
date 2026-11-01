"""B14: the settings pins, the pin chain, the frozen inputs the settings name, and two build facts (no draws; the
Mac half is standard library only). One test records why B14 has no seed label (the registry's owner rule)."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

import experiments.safety_selection as engine
from experiments.safety_selection.common import code_identity, sha256_file
from experiments.safety_selection.config import config_sha256, load_recipe
from scripts.stage1 import s1common as s1
from scripts.stage1_s1 import overlap_similarity as sim
from scripts.stage1_s1 import overlap_strata as st

# the engine's checkout (configs, frozen scripts, scripts/stage1's settings), found from the engine import: in a
# mutation copy that holds scripts/stage1 (B10's, B11's and B14's runner layout) s1common's own root is the copy, which
# has no experiments/ (S1 FIX of the merged-tree layout finding)
REPO = Path(engine.__file__).resolve().parents[2]
PKG = Path(sim.__file__).resolve().parent               # the package under test (a mutation copy tests itself)


@pytest.mark.parametrize("module", [sim, st])
def test_each_script_pins_its_settings_file_and_the_settings_pass_the_shared_checks(module):
    assert sha256_file(module.SETTINGS_PATH) == module.SETTINGS_SHA256
    doc, digest = s1.load_settings(module.SETTINGS_PATH, module.SETTINGS_SHA256, module.SETTINGS_NAME)
    module.check_content(doc)
    assert digest == module.SETTINGS_SHA256 and doc["engine_x"] == code_identity()["sha256"]
    assert doc["label_entries"] == {} and doc["owner"] == f"scripts/stage1_s1/{Path(module.__file__).name}"


def test_the_strata_settings_pin_the_similarity_settings():
    doc = json.loads(st.SETTINGS_PATH.read_bytes())
    assert doc["similarity_settings_sha256"] == sim.SETTINGS_SHA256 == sha256_file(sim.SETTINGS_PATH)


def test_the_pinned_recipe_manifest_and_frozen_scripts_are_the_named_ones():
    sim_doc = json.loads(sim.SETTINGS_PATH.read_bytes())
    rec = load_recipe(REPO / "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json")
    assert config_sha256(rec) == sim_doc["recipe_sha256"]
    assert rec["model"]["repo_id"] == "allenai/OLMo-2-0425-1B-Instruct"
    rep = json.loads(st.SETTINGS_PATH.read_bytes())["report"]
    assert rep["identity"]["recipe_sha256"] == sim_doc["recipe_sha256"]
    assert rep["identity"]["manifest_sha256"] == sim_doc["prepared_manifest_sha256"]
    assert rep["samples_per_prompt"] == rec["generation"]["harm_samples"]["count"] == 3
    gate_b_s = load_recipe(REPO / "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json")
    assert rep["refused_recipes"] == [config_sha256(gate_b_s)]
    for entry in rep["frozen_reader"].values():
        assert sha256_file(REPO / entry["path"]) == entry["sha256"]
    limits = json.loads((REPO / "scripts/stage1/settings/limits_check.json").read_bytes())
    assert rep["frozen_reader"] == limits["frozen_reader"]
    assert limits["gate_a_identity"]["code_sha256"] in rep["allowed_code_sha256"]
    assert code_identity()["sha256"] in rep["allowed_code_sha256"]


def test_the_seed_plans_are_the_records_plans():
    plans = json.loads(st.SETTINGS_PATH.read_bytes())["report"]["seed_plans"]
    # UW-03 D1: the add arms 1102-1107, a0 1101-1107
    assert plans["d1_plan_a"] == {"seeds": list(range(1102, 1108)), "add_sets": ["S1", "S3", "S4"]}
    # plan A's block A: the add arms 1102-1104, a0 1101-1104
    assert plans["block_a_only"] == {"seeds": [1102, 1103, 1104], "add_sets": ["S1", "S3", "S4"]}
    # plan B under D1 (LN-02; addendum 11.10; DRAFT rev 3 section 1.3): S1 and S4 at 1102-1110, no S3, a0 1101-1107
    assert plans["plan_b"] == {"seeds": list(range(1102, 1108)), "add_sets": ["S1", "S4"]}
    # plan B's block A (addendum 11.10): S1 and S4 at 1102-1104 (J = 3), beside plan A's block_a_only
    assert plans["plan_b_block_a_only"] == {"seeds": [1102, 1103, 1104], "add_sets": ["S1", "S4"]}
    assert sorted(plans) == ["block_a_only", "d1_plan_a", "plan_b", "plan_b_block_a_only"]
    assert all(1101 not in plan["seeds"] for plan in plans.values())        # the 1101 rule
    names = json.loads(sim.SETTINGS_PATH.read_bytes())["add_sets"]["names"]
    assert all(set(plan["add_sets"]) <= set(names) for plan in plans.values())


@pytest.mark.parametrize("damage", ["list_form", "no_sets", "empty_sets", "unsorted_sets", "comparator_as_set",
                                    "unsorted_seeds", "too_few_seeds", "no_plans"])
def test_a_malformed_seed_plan_refuses(damage):
    doc = json.loads(st.SETTINGS_PATH.read_bytes())
    plans = doc["report"]["seed_plans"]
    if damage == "list_form":
        plans["plan_b"] = [1102, 1103]
    elif damage == "no_sets":
        del plans["plan_b"]["add_sets"]
    elif damage == "empty_sets":
        plans["plan_b"]["add_sets"] = []
    elif damage == "unsorted_sets":
        plans["plan_b"]["add_sets"] = ["S4", "S1"]
    elif damage == "comparator_as_set":
        plans["plan_b"]["add_sets"] = ["S1", "a0"]
    elif damage == "unsorted_seeds":
        plans["plan_b"]["seeds"] = [1103, 1102]
    elif damage == "too_few_seeds":
        plans["plan_b"]["seeds"] = [1102]
    elif damage == "no_plans":
        doc["report"]["seed_plans"] = {}
    with pytest.raises(s1.Refusal, match="seed plan"):
        st.check_content(doc)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_no_script_draws_a_random_number():
    for path in (PKG / "overlap_similarity.py", PKG / "overlap_strata.py"):
        names = _imports(path)
        assert "random" not in names and "secrets" not in names
        assert "numpy_generator" not in path.read_text() and "s1.seed(" not in path.read_text()


def test_the_mac_half_is_standard_library_only():
    assert not _imports(PKG / "overlap_strata.py") & {"torch", "numpy", "transformers", "peft", "scipy"}
    code = ("import sys; sys.path[:0] = [%r, %r]; import scripts.stage1_s1.overlap_strata; "
            "print(sorted(m for m in ('torch', 'numpy', 'transformers') if m in sys.modules))"
            % (str(PKG.parents[1]), str(REPO)))
    out = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[]"


def test_a_seed_label_owned_by_a_stage1_s1_file_would_break_the_registry(tmp_path):
    """Why B14 draws nothing: s1common's OWNER_PATTERN admits owners under scripts/stage1/ only, so appending an entry
    owned by a scripts/stage1_s1 file makes load_registry refuse the whole registry (every stage-1 draw would stop).
    If the lead widens that rule, this test fails and says so."""
    doc = json.loads(s1.LABELS_PATH.read_bytes())
    doc["labels"]["overlap.ties"] = {"base_seed": 20261008, "id_domain": "dev harm prompt ids",
                                     "label": "stage1-overlap-ties-v1", "named_in": "B14 hand-over",
                                     "owner": "scripts/stage1_s1/overlap_strata.py", "parts": ["add_set"],
                                     "use": "a sealed tie order at the split boundary"}
    path = tmp_path / "labels.json"
    path.write_text(json.dumps(doc))
    with pytest.raises(s1.Refusal, match="owner"):
        s1.load_registry(path)
    doc["labels"]["overlap.ties"]["owner"] = "scripts/stage1/overlap_strata.py"
    path.write_text(json.dumps(doc))
    assert "overlap.ties" in s1.load_registry(path)
