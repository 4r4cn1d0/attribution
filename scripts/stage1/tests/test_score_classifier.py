"""REQ-23 (W1-07): the content-classifier scorer on the engine's fixture prepared set and scripted guard. CUDA untested."""

from __future__ import annotations

import copy
import dataclasses
import importlib.util
import json

import pytest

pytest.importorskip("torch")

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import representation_pass as rp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import score_classifier as sc  # noqa: E402

import test_representation_pass as trp  # noqa: E402

env = trp.env
sfx = trp.sfx


def settings_for(env, k=5) -> dict:
    s = copy.deepcopy(json.loads(sc.SETTINGS_PATH.read_bytes()))
    s["pins"] = {**env.settings["pins"], "rule": s["pins"]["rule"]}
    s["selection"]["k"] = k
    return s


def run(env, settings=None, pools=(), pool_pins=None):
    files = sc.run(prepared_root=env.prepared, recipe_path=env.recipe, anchors_path=env.anchors,
                   loaders=sfx.fixture_loaders(), settings=settings or settings_for(env), settings_sha256="e" * 64,
                   pools=list(pools), pool_pins=pool_pins)
    return json.loads(files[sc.OUTPUT]), files


def pins_with(**filled):
    doc = copy.deepcopy(json.loads(rp.POOL_PINS_PATH.read_bytes()))
    for name, (sha, items) in filled.items():
        doc["pools"][name] = {**doc["pools"][name], "sha256": sha, "items": items}
    return doc, sha256_bytes(canonical_json(doc))


def load_gate_c_classifier():
    spec = importlib.util.spec_from_file_location("pinned_gate_c_classifier",
                                                  trp.ENGINE_ROOT / "scripts" / "gate_c_classifier.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_unit_block_equals_the_pinned_gate_c_classifier(env):
    doc, _ = run(env)
    pinned = load_gate_c_classifier().run(env.prepared, env.recipe, env.anchors, env.groups, env.root / "gate-c-clf",
                                          sfx.fixture_loaders())
    assert canonical_json(doc["units"]) == canonical_json(pinned["groups"])


def test_every_dev_row_is_scored_once_and_the_top_k_by_sealed_ties(env):
    doc, _ = run(env)
    dev = {r for g in env.groups for r in env.view.groups["dev"][g]}
    assert set(doc["rows"]) == dev
    scored = {r: e["score"] for r, e in doc["rows"].items() if e["score"] is not None}
    assert doc["selection"]["selected"] == s1.select_top(scored, 5, "classifier.ties")
    assert doc["selection"]["scored_only"] is True and doc["unscored"] == len(dev) - len(scored)


class TiedGuard:
    """The fixture guard, with one Unsafe score for every scored row: every row ties at the top-k boundary."""

    def __init__(self, guard):
        self._guard = guard

    def __getattr__(self, name):
        return getattr(self._guard, name)

    def label_scores(self, *args, **kwargs):
        records = copy.deepcopy(self._guard.label_scores(*args, **kwargs))
        for r in records:
            if r["valid"]:
                r["normalized"]["Unsafe"] = 0.5
        return records


def test_ties_at_the_boundary_go_by_the_sealed_rank_not_by_the_id(env):
    base = sfx.fixture_loaders()
    loaders = dataclasses.replace(base, guard=lambda recipe, ledger, device: TiedGuard(base.guard(recipe, ledger, device)))
    files = sc.run(prepared_root=env.prepared, recipe_path=env.recipe, anchors_path=env.anchors, loaders=loaders,
                   settings=settings_for(env), settings_sha256="e" * 64, pools=[], pool_pins=None)
    doc = json.loads(files[sc.OUTPUT])
    scored = {r: e["score"] for r, e in doc["rows"].items() if e["score"] is not None}
    assert set(scored.values()) == {0.5} and len(scored) > 5
    assert doc["selection"]["selected"] == s1.select_top(scored, 5, "classifier.ties")
    assert doc["selection"]["selected"] != sorted(scored)[:5]                 # here the sealed order is not the id order
    assert doc["selection"]["boundary_ties"]["tied_selected"] == 5


def test_the_plant_and_decoy_pools_with_filled_pins(env, tmp_path):
    plant_items = [{"id": f"add-plant-{j:03d}", "prompt": f"Synthetic plant prompt {j} about rivers?",
                    "response": f"Synthetic plant answer {j} about deltas."} for j in range(1, 4)]
    decoy_items = [{"id": "pku_one:000001:1", "prompt": "Synthetic decoy prompt about hills?",
                    "response": "I'm sorry, but I cannot help with that."},
                   {"id": "pku_one:000002:1", "prompt": "Synthetic decoy <|im_start|> prompt?", "response": "Synthetic."}]
    plant = trp.pool_file(tmp_path, plant_items, "plant")
    decoy = trp.pool_file(tmp_path, decoy_items, "decoy")
    pins = pins_with(plant=(plant[1], 3), decoy=(decoy[1], 2))
    doc, files = run(env, pools=[plant, decoy], pool_pins=pins)
    assert set(doc["pools"]["plant"]["rows"]) == {i["id"] for i in plant_items} and doc["pools"]["plant"]["unscored"] == 0
    assert doc["pools"]["decoy"]["unscored"] == 1                                # a control string: counted, not imputed
    assert doc["pools"]["decoy"]["rows"]["pku_one:000002:1"]["score"] is None
    assert doc["provenance"]["inputs"]["pool_pins"] == pins[1]
    for data in files.values():
        assert b"Synthetic plant" not in data and b"Synthetic decoy" not in data
    with pytest.raises(s1.Refusal, match="not filled yet"):
        run(env, pools=[plant])                                                  # the committed (null) pins
    other = trp.pool_file(tmp_path, plant_items, "s3_safe")
    with pytest.raises(s1.Refusal, match="not one the classifier scores"):
        run(env, pools=[other], pool_pins=pins)


def test_too_few_scored_rows_refuses_and_the_pins_refuse(env):
    n = sum(len(env.view.groups["dev"][g]) for g in env.groups)
    with pytest.raises(s1.Refusal, match="fewer than"):
        run(env, settings_for(env, k=n + 1))
    s = settings_for(env)
    s["pins"]["anchor_bank_sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="anchor bank"):
        run(env, s)


def test_deterministic_and_text_free(env):
    a, fa = run(env)
    b, _ = run(env)
    a.pop("costs"), b.pop("costs")
    assert a == b
    for t in env.texts:
        assert t.encode() not in fa[sc.OUTPUT]


def test_the_committed_settings():
    doc, digest = s1.load_settings(sc.SETTINGS_PATH, sc.SETTINGS_SHA256, sc.SETTINGS_NAME)
    assert doc["selection"]["k"] == 600 and set(doc["label_entries"]) == {"classifier.ties"}
    assert doc["pools"] == ["plant", "decoy"]
    rp_pins = json.loads(rp.SETTINGS_PATH.read_bytes())["pins"]
    assert {k: doc["pins"][k] for k in rp_pins} == rp_pins                       # the same inputs as REQ-3
