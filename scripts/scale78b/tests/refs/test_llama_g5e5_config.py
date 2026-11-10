"""Llama-3.1-8B's recipe-G config at LR 5e-5 (Part 2 section 3.2; DES F2; GXB O11): it equals the LR 1e-4 G config
except the learning rate (and its own name and purpose; the engine's loader derives no field from the LR); its
generation and guard blocks hash to the 1B O-ext pins (PLAN-AB section 5 C3's expression); its LR is the family's main
LR; and, as T-O2's step on a copy (the committed fill is the lead's recorded step), Track O's maker takes it as
Llama's recipe G with only Llama's engine-X pins changing."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import refs_fixtures as rf

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from experiments.safety_selection.config import config_sha256, load_recipe, training_identity
from scripts.scale78b import make_oext_settings_78b as mo
from scripts.scale78b import make_refs_settings_78b as mk
from scripts.scale78b import oext_78b as ox

REPO = mk.REPO
CONFIGS = REPO / "experiments" / "safety_selection" / "configs"
NAME = "study-kt-llama31-8b-r64-g5e5-mb2-20261108"
G_1E4 = "study-kt-llama31-8b-r64-g-mb2-20261011"
MAIN = "study-kt-llama31-8b-r64-b5e5-mb2-20261010"
CONFIG_SHA256 = "81dd70687b729a5977ad6dc117bdd428ea27eebdf0ea3b3e19c29f7c2d334828"     # M: config_sha256, 8 Nov 2026
FILE_SHA256 = "3298dd92be27c3658a851fb063f1bdc30897c2ab9b8cf410114c352e63134be6"       # M: shasum -a 256
ONE_B = json.loads((REPO / "scripts/stage1_s1/settings/oext_unit.json").read_bytes())["recipes"]


def differing(a, b, path=""):
    """Every dotted field where two documents differ (a key missing on one side included)."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for key in sorted(set(a) | set(b)):
            out += differing(a.get(key, KeyError), b.get(key, KeyError), f"{path}.{key}" if path else key)
        return out
    return [] if a == b and type(a) is type(b) else [path]


def test_the_config_is_the_1e4_g_config_with_the_lr_changed():
    new = json.loads((CONFIGS / f"{NAME}.json").read_bytes())
    old = json.loads((CONFIGS / f"{G_1E4}.json").read_bytes())
    assert differing(new, old) == ["name", "purpose", "train.lr"]
    assert (new["train"]["lr"], old["train"]["lr"]) == (5e-05, 0.0001)
    assert new["name"] == NAME and list(new) == list(old) and list(new["train"]) == list(old["train"])


def test_the_lr_is_the_familys_main_lr_and_the_g_fields_are_recipe_gs():
    new, main = load_recipe(CONFIGS / f"{NAME}.json"), load_recipe(CONFIGS / f"{MAIN}.json")
    assert new["train"]["lr"] == main["train"]["lr"] == 5e-05
    g = {"loss_weighting": "token_mean", "lr_schedule": "warmup_cosine", "warmup_steps": 4, "schedule_until": "e1"}
    assert {k: new["train"][k] for k in g} == g
    assert differing(new["model"], main["model"]) == [] and differing(new["generation"], main["generation"]) == []


def test_the_pins_and_the_c3_blocks():
    rec = load_recipe(CONFIGS / f"{NAME}.json")
    assert config_sha256(rec) == CONFIG_SHA256 and sha256_file(CONFIGS / f"{NAME}.json") == FILE_SHA256
    assert sha256_bytes(canonical_json(rec["generation"])) == ONE_B["generation_sha256"]
    assert sha256_bytes(canonical_json(rec["guard"])) == ONE_B["guard_sha256"]
    assert training_identity(rec) != training_identity(load_recipe(CONFIGS / f"{G_1E4}.json"))
    assert (CONFIGS / f"{NAME}.json").read_bytes() == (json.dumps(json.loads((CONFIGS / f"{NAME}.json").read_bytes()),
                                                                  indent=4, ensure_ascii=False) + "\n").encode()


def test_t_o2s_recipe_g_fill_on_a_copy(tmp_path):
    """Fill Llama's recipe G in Track O's pins (a copy, from Llama's G null) with this config and run Track O's maker
    into a copy of the settings: Llama's oext_unit allows it, Llama's RECIPE_G wait is gone, only Llama's oext_unit and
    X index change, the wrapper's check validates the file, and the reference settings (they do not use recipe G) do
    not change."""
    pins, _ = mo.load_pins()
    base = copy.deepcopy(pins)
    base["families"]["llama31-8b"]["recipe_g"] = {"name": None, "config_sha256": None}
    filled = copy.deepcopy(base)
    filled["families"]["llama31-8b"]["recipe_g"] = {"name": NAME, "config_sha256": CONFIG_SHA256}
    sdir = tmp_path / "settings"
    shutil.copytree(mo.SETTINGS_DIR, sdir)

    def run_maker(doc):
        path = tmp_path / "oext_pins_78b.json"
        path.write_bytes(mo.dumps(doc))
        code, _, err = rf.call(mo.main, ["--pins", str(path), "--settings-dir", str(sdir)])
        assert code == 0, err[-300:]
    run_maker(base)
    before = {p.name: p.read_bytes() for p in sdir.iterdir()}
    refs_pins, _ = mk.load_pins()
    refs_before = mk.derive_all(refs_pins, sdir)
    run_maker(filled)
    after = {p.name: p.read_bytes() for p in sdir.iterdir()}
    assert sorted(n for n in after if after[n] != before.get(n)) == \
        sorted([mo.index_name("llama31-8b", "X"), mo.file_name("oext_unit", "llama31-8b")])
    unit = json.loads((sdir / mo.file_name("oext_unit", "llama31-8b")).read_bytes())
    assert unit["recipes"]["allowed"] == {"MAIN": pins["families"]["llama31-8b"]["main"]["config_sha256"],
                                          "G": CONFIG_SHA256}
    index = json.loads((sdir / mo.index_name("llama31-8b", "X")).read_bytes())
    assert "RECIPE_G" not in [w["pin"] for w in index["waits"]]
    idx = sdir / mo.index_name("llama31-8b", "X")
    code, out, err = rf.call(ox.main, ["check", "--family", "llama31-8b", "--index", str(idx), "--index-sha256",
                                       sha256_file(idx)])
    assert code == 0 and json.loads(out)["settings"]["oext_unit"] == "valid", err[-300:]
    assert mk.derive_all(refs_pins, sdir) == refs_before
