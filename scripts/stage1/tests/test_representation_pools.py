"""W1-08 (1), the lead's ruling option (a): REQ-3's pool pins (settings/representation_pools.json), hash-pinned and loaded
by representation_pass.py; null pins until REQ-8's sealed pools exist. Plus the pass's clean refusals of bad inputs."""

from __future__ import annotations

import copy
import json

import pytest

pytest.importorskip("torch")

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import representation_pass as rp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

import test_representation_pass as trp  # noqa: E402  (its env fixture and helpers; its tests are not re-collected)

env = trp.env
ITEMS = [{"id": f"add-plant-{j:03d}", "prompt": f"Synthetic plant prompt {j} about tides?",
          "response": f"Synthetic plant answer {j} about moons."} for j in range(1, 4)]


def committed() -> dict:
    return json.loads(rp.POOL_PINS_PATH.read_bytes())


def pins_with(**filled) -> tuple[dict, str]:
    """The committed pins with some entries filled (name -> (sha256, items)), and the document's own SHA-256."""
    doc = copy.deepcopy(committed())
    for name, (sha, items) in filled.items():
        doc["pools"][name] = {**doc["pools"].get(name, {"source": "a synthetic pool"}), "sha256": sha, "items": items}
    return doc, sha256_bytes(canonical_json(doc))


def pool(name: str, sha: str = "a" * 64, items: int = 3) -> dict:
    return {"name": name, "sha256": sha, "items": [{"id": f"x{k}"} for k in range(items)]}


# ----- the committed file ---------------------------------------------------------------------------------------


def test_the_pool_pins_are_literal_pinned_and_not_filled():
    assert sha256_file(rp.POOL_PINS_PATH) == rp.POOL_PINS_SHA256 == \
        "1451ba5ec435ecaafebd7749f44b6729e45f2157a69a62c55f35e2bbdbae826b"
    doc, digest = rp.load_pool_pins()
    assert digest == rp.POOL_PINS_SHA256 and doc["name"] == "representation_pools" and doc["label_entries"] == {}
    assert {n: (e["sha256"], e["items"]) for n, e in doc["pools"].items()} == {"plant": (None, 75), "decoy": (None, 37)}
    assert "only this pool is passed" in doc["pools"]["plant"]["source"]
    # REQ-3's own settings and their literal pin are unchanged by the ruling
    assert sha256_file(rp.SETTINGS_PATH) == rp.SETTINGS_SHA256 == \
        "a555fd899bd2b5caf8d68fb62578ed2e943977341b5bf2dc2d688dcbd034600b"


def test_a_changed_pins_file_refuses(tmp_path):
    path = tmp_path / "representation_pools.json"
    doc = committed()
    doc["pools"]["plant"]["sha256"] = "b" * 64
    path.write_bytes(canonical_json(doc))
    with pytest.raises(s1.Refusal, match="hash to"):
        rp.load_pool_pins(path)
    with pytest.raises(s1.Refusal, match="cannot be read"):
        rp.load_pool_pins(tmp_path / "absent.json")


@pytest.mark.parametrize("change,match", [
    (lambda d: d["pools"].update(dev={"sha256": None, "items": 1, "source": "x"}), "named 'dev'"),
    (lambda d: d["pools"]["plant"].pop("source"), "is not"),
    (lambda d: d["pools"]["plant"].update(items=0), "is not"),
    (lambda d: d["pools"]["plant"].update(items=True), "is not"),
    (lambda d: d["pools"]["plant"].update(sha256="B" * 64), "is not"),
    (lambda d: d["pools"]["plant"].update(extra=1), "is not"),
    (lambda d: (d["pools"]["plant"].update(sha256="c" * 64), d["pools"]["decoy"].update(sha256="c" * 64)), "one SHA-256"),
    (lambda d: d.update(pools={}), "list no pool"),
    (lambda d: d.update(engine_x="0" * 64), "written for engine"),
    (lambda d: d.update(name="representation_pass"), "not the stage-1 settings"),
])
def test_bad_pins_documents_refuse(change, match):
    doc = copy.deepcopy(committed())
    change(doc)
    with pytest.raises(s1.Refusal, match=match):
        rp.check_pool_pins(doc)


# ----- the rule, by hand ----------------------------------------------------------------------------------------


def test_the_rule_for_each_case():
    null = committed()
    filled, _ = pins_with(plant=("d" * 64, 3))
    assert rp.pin_of(pool("s3_safe"), null) == "command line"                     # an unlisted pool: by its SHA
    assert rp.pin_of(pool("plant", "d" * 64), filled) == "pool pins"
    with pytest.raises(s1.Refusal, match="not filled yet"):
        rp.pin_of(pool("plant", "d" * 64), null)                                  # a W1-known pool, pin null
    with pytest.raises(s1.Refusal, match="not filled yet"):
        rp.pin_of(pool("decoy"), filled)
    with pytest.raises(s1.Refusal, match="the pool pins name"):
        rp.pin_of(pool("plant", "e" * 64), filled)                                # another file under the name
    with pytest.raises(s1.Refusal, match="holds 4 items"):
        rp.pin_of(pool("plant", "d" * 64, items=4), filled)
    with pytest.raises(s1.Refusal, match="do not match"):
        rp.pin_of(pool("plant_75", "d" * 64), filled)                             # the pinned file, another name
    for pins in (null, filled):
        with pytest.raises(s1.Refusal, match="dev rows' source name"):
            rp.pin_of(pool("dev"), pins)


# ----- through the pass -----------------------------------------------------------------------------------------


def test_the_pass_checks_every_pool_against_the_pins(env, tmp_path):
    path, digest = trp.pool_file(tmp_path, ITEMS, "plant")
    with pytest.raises(s1.Refusal, match="not filled yet"):
        trp.run(env, pools=[(path, digest)], score_units=False)                   # the committed (null) pins
    pins = pins_with(plant=(digest, len(ITEMS)))
    files = rp.run(env.prepared, env.recipe, env.anchors, trp.sfx.fixture_loaders(), env.settings, "e" * 64,
                   [(path, digest)], False, pool_pins=pins)
    summary = json.loads(files[rp.SUMMARY_FILE])
    assert summary["pools"] == [{"name": "plant", "sha256": digest, "items": 3, "pinned_by": "pool pins",
                                 "refused_by_reason": {}}]
    assert summary["pool_pins"] == {"file": "settings/representation_pools.json", "sha256": pins[1],
                                    "filled": ["plant"], "not_filled": ["decoy"]}
    assert summary["provenance"]["inputs"]["pool_pins"] == pins[1]
    assert [json.loads(l)["source"] for l in files[rp.ROWS_FILE].splitlines()] == ["plant"] * 3
    for data in files.values():
        assert b"Synthetic plant" not in data
    other, other_sha = trp.pool_file(tmp_path, ITEMS[:2], "plant")
    with pytest.raises(s1.Refusal, match="the pool pins name"):
        rp.run(env.prepared, env.recipe, env.anchors, trp.sfx.fixture_loaders(), env.settings, "e" * 64,
               [(other, other_sha)], False, pool_pins=pins)
    renamed, renamed_sha = trp.pool_file(tmp_path, ITEMS, "dev")
    with pytest.raises(s1.Refusal, match="dev rows' source name"):
        trp.run(env, pools=[(renamed, renamed_sha)], score_units=False)


def test_an_unlisted_pool_is_scored_by_its_command_line_hash(env, tmp_path):
    path, digest = trp.pool_file(tmp_path, ITEMS[:2], "s3_safe")
    summary = json.loads(trp.run(env, pools=[(path, digest)], score_units=False)[rp.SUMMARY_FILE])
    assert summary["pools"][0]["pinned_by"] == "command line" and summary["pools"][0]["sha256"] == digest
    assert summary["pool_pins"]["sha256"] == rp.POOL_PINS_SHA256 and summary["pool_pins"]["filled"] == []


# ----- clean refusals (the critic's notes) ------------------------------------------------------------------------


def test_nothing_to_score_refuses_before_the_model_loads(env):
    loaded = []

    def policy(*_):
        loaded.append(1)
        raise AssertionError("the model was loaded")
    import dataclasses
    with pytest.raises(s1.Refusal, match="nothing to score"):
        trp.run(env, loaders=dataclasses.replace(trp.sfx.fixture_loaders(), policy=policy), score_units=False)
    assert not loaded


@pytest.mark.parametrize("items,match", [
    (["just a string"], "pool items must be"),
    ([{"id": "p-1", "prompt": 7, "response": "Synthetic."}], "pool items must be"),
    ([{"id": "p-1", "prompt": "Synthetic?", "response": None}], "pool items must be"),
    ([{"id": 5, "prompt": "Synthetic?", "response": "Synthetic."}], "distinct short ids"),
])
def test_badly_shaped_pools_refuse_cleanly(tmp_path, items, match):
    path, digest = trp.pool_file(tmp_path, items, "bad")
    with pytest.raises(s1.Refusal, match=match):
        rp.read_pool(path, digest)
    with pytest.raises(s1.Refusal, match="cannot be read"):
        rp.read_pool(tmp_path / "absent.json", digest)


def test_the_command_refuses_cleanly(tmp_path, capsys):
    base = ["--prepared", str(tmp_path), "--recipe", str(tmp_path / "r.json"), "--anchors", str(tmp_path / "a.json"),
            "--out", str(tmp_path / "o")]
    assert rp.main(base + ["--pools-only"]) == 2 and "nothing to score" in capsys.readouterr().err
    assert rp.main(base + ["--pool", "no-hash-here"]) == 2 and "PATH:SHA256" in capsys.readouterr().err
    assert rp.main(base + ["--settings", str(tmp_path / "absent.json")]) == 2 and \
        "settings cannot be read" in capsys.readouterr().err
    assert rp.main(base + ["--pool-pins", str(tmp_path / "absent.json")]) == 2 and \
        "pool pins cannot be read" in capsys.readouterr().err
    # batch 2 rev 3 (the verifier's item 2): a PRESENT pins file is checked against the literal pin, never its own hash:
    # the committed document re-serialised (another SHA-256) refuses
    reserialised = tmp_path / "pins_reserialised.json"
    reserialised.write_text(json.dumps(json.loads(rp.POOL_PINS_PATH.read_bytes()), indent=4) + "\n")
    assert sha256_file(reserialised) != rp.POOL_PINS_SHA256
    assert rp.main(base + ["--pool-pins", str(reserialised)]) == 2 and "hash to" in capsys.readouterr().err
    assert rp.main(base) == 2 and "cannot be read" in capsys.readouterr().err      # absent prepared set and recipe
    assert not (tmp_path / "o").exists()
