"""REQ-4: the R draws (the frozen builder reproduced, d = 6..10 by it, R_1200 and R_2400), on a synthetic P."""

from __future__ import annotations

import copy
import json
import random
import shutil

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from experiments.safety_selection.edits import parse_edit
from scripts.stage1 import build_r_draws as brd
from scripts.stage1 import s1common as s1

import s1fixtures_b3 as fb


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    root = tmp_path_factory.mktemp("rdraws")
    prep = fb.make_prepared(root / "p")
    sealed = root / "sealed"
    manifest_sha = fb.seal_r_files(sealed, prep)
    settings = copy.deepcopy(json.loads(brd.SETTINGS_PATH.read_bytes()))
    settings["inputs"]["prepared_manifest_sha256"] = prep["manifest_sha256"]
    settings["inputs"]["sealed_manifest_sha256"] = manifest_sha
    return {"root": root, "prep": prep, "sealed": sealed, "settings": settings, "cache": {}}


@pytest.fixture()
def patched(monkeypatch, env):
    """The wrapper's own loader (with its SHA-256 check), then the synthetic set's manifest constant in the loaded
    module object (the frozen file is never changed)."""
    real = brd.load_frozen

    def load(path, expected):
        module = real(path, expected)
        module.PREPARED_MANIFEST_SHA256 = env["prep"]["manifest_sha256"]
        return module
    monkeypatch.setattr(brd, "load_frozen", load)


def files_of(env, sealed=None, settings=None):
    return brd.build(env["prep"]["root"], fb.FROZEN_BUILDER, sealed or env["sealed"], settings or env["settings"], "e" * 64)


def cached(env):
    if "files" not in env["cache"]:
        env["cache"]["files"] = files_of(env)
    return env["cache"]["files"]


def view(env):
    return s1.PreparedView(env["prep"]["root"], env["prep"]["manifest_sha256"])


def test_the_sealed_files_are_reproduced_byte_for_byte(env, patched):
    rec = json.loads(cached(env)[brd.RECORD])
    assert sorted(rec["reproduction"]) == ["1", "2", "3", "4", "5"]
    assert all(v["byte_identical"] and v["rows"] == 600 for v in rec["reproduction"].values())


def test_a_changed_sealed_byte_refuses(env, patched, tmp_path):
    other = tmp_path / "sealed"
    shutil.copytree(env["sealed"], other)
    path = other / "edits" / "R_d3.json"
    doc = json.loads(path.read_bytes())
    doc["name"] = doc["name"] + " "
    path.write_bytes(canonical_json(doc))
    with pytest.raises(s1.Refusal, match="R_d3.json is not the file the sealed manifest lists"):
        files_of(env, sealed=other)
    manifest = json.loads((other / "MANIFEST.json").read_bytes())
    for f in manifest["files"]:
        if f["path"] == "edits/R_d3.json":
            f["sha256"] = sha256_file(path)
    (other / "MANIFEST.json").write_bytes(canonical_json(manifest))
    settings = copy.deepcopy(env["settings"])
    settings["inputs"]["sealed_manifest_sha256"] = sha256_file(other / "MANIFEST.json")
    with pytest.raises(s1.Refusal, match="R_3: the frozen builder's file differs"):
        files_of(env, sealed=other, settings=settings)


def test_a_changed_frozen_builder_byte_refuses(env, tmp_path):
    copy_path = tmp_path / "build_sealed.py"
    copy_path.write_bytes(fb.FROZEN_BUILDER.read_bytes() + b"\n# changed\n")
    with pytest.raises(s1.Refusal, match="the frozen builder hashes to"):
        brd.load_frozen(copy_path, env["settings"]["inputs"]["frozen_builder_sha256"])


def test_the_frozen_builder_is_the_pinned_one():
    settings = json.loads(brd.SETTINGS_PATH.read_bytes())
    assert sha256_file(fb.FROZEN_BUILDER) == settings["inputs"]["frozen_builder_sha256"] == \
        "80cb8944cbea2847a4d39cddae225158f98431a8612282e2dd7161239050d3c6"
    assert settings["inputs"]["sealed_manifest_sha256"] == "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8"
    assert settings["frozen_r"]["draws"] == [6, 7, 8, 9, 10] and settings["reproduce"]["draws"] == [1, 2, 3, 4, 5]
    assert settings["seed_map"]["offset"] == 1100
    assert settings["doses"]["R_1200"]["per_unit"] == 150 and settings["doses"]["R_2400"]["per_unit"] == 300
    assert settings["doses"]["R_1200"]["draws"] == settings["doses"]["R_2400"]["draws"] == [2, 3, 4]


def test_d6_to_d10_are_the_frozen_builders_own_draws(env, patched):
    files = cached(env)
    frozen = fb.load_frozen(env["prep"]["manifest_sha256"])
    inputs = frozen.Inputs(env["prep"]["root"])
    rec = json.loads(files[brd.RECORD])
    for d in (6, 7, 8, 9, 10):
        doc = json.loads(files[f"edits/R_d{d}.json"])
        assert doc["remove"] == frozen.draw_r(inputs, d)[0] and len(doc["remove"]) == 600
        assert doc["provenance"]["builder_sha256"] == sha256_file(fb.FROZEN_BUILDER)
        assert doc["provenance"]["stage1_wrapper"]["script_sha256"] == sha256_file(brd.__file__)
        entry = next(r for r in rec["files"] if r["file"] == f"edits/R_d{d}.json")
        assert entry["seed"] == 1100 + d and entry["tokens"]["removed"]["rows"] == 600
    assert len({tuple(json.loads(files[f"edits/R_d{d}.json"])["remove"]) for d in (6, 7, 8, 9, 10)}) == 5


def test_build_refuses_a_changed_frozen_builder_before_running_it(env, patched, tmp_path):
    """build() checks the frozen file against the settings pin (not the file's own hash) before executing it: a
    changed copy whose import leaves a marker refuses and the marker never appears."""
    marker = tmp_path / "ran"
    changed = tmp_path / "build_sealed.py"
    changed.write_bytes(fb.FROZEN_BUILDER.read_bytes() +
                        f"\nopen({str(marker)!r}, 'w').close()  # a side effect at import\n".encode())
    with pytest.raises(s1.Refusal, match="the frozen builder hashes to"):
        brd.build(env["prep"]["root"], changed, env["sealed"], env["settings"], "e" * 64)
    assert not marker.exists()


def test_a_sealed_file_claiming_another_builder_refuses(env, patched, tmp_path):
    other = tmp_path / "sealed"
    shutil.copytree(env["sealed"], other)
    path = other / "edits" / "R_d1.json"
    doc = json.loads(path.read_bytes())
    doc["provenance"]["builder_sha256"] = "1" * 64
    path.write_bytes(canonical_json(doc))
    manifest = json.loads((other / "MANIFEST.json").read_bytes())
    for f in manifest["files"]:
        if f["path"] == "edits/R_d1.json":
            f["sha256"] = sha256_file(path)
    (other / "MANIFEST.json").write_bytes(canonical_json(manifest))
    settings = copy.deepcopy(env["settings"])
    settings["inputs"]["sealed_manifest_sha256"] = sha256_file(other / "MANIFEST.json")
    with pytest.raises(s1.Refusal, match="not written by the pinned frozen builder"):
        files_of(env, sealed=other, settings=settings)


def test_the_record_states_seed_1100_plus_d_and_the_roles_for_every_file(env, patched):
    rec = json.loads(cached(env)[brd.RECORD])
    by_file = {r["file"]: r for r in rec["files"]}
    assert sorted(by_file) == sorted([f"edits/R_d{d}.json" for d in (6, 7, 8, 9, 10)] +
                                     [f"edits/{fam}_d{d}.json" for fam in ("R_1200", "R_2400") for d in (2, 3, 4)])
    for family in ("R_1200", "R_2400"):
        for d in (2, 3, 4):
            entry = by_file[f"edits/{family}_d{d}.json"]
            assert entry["seed"] == 1100 + d and entry["draw"] == d and entry["family"] == family
            assert "secondary" in entry["role"]
    for d in (6, 7):
        assert by_file[f"edits/R_d{d}.json"]["role"].startswith("primary")
    for d in (8, 9, 10):
        assert by_file[f"edits/R_d{d}.json"]["role"].startswith("plan B only")
    assert rec["seed_map"] == {"offset": 1100, "rule": env["settings"]["seed_map"]["rule"]}
    pin = "80cb8944cbea2847a4d39cddae225158f98431a8612282e2dd7161239050d3c6"
    assert rec["provenance"]["inputs"]["frozen_builder"] == pin == env["settings"]["inputs"]["frozen_builder_sha256"]
    assert rec["provenance"]["inputs"]["sealed_manifest"] == env["settings"]["inputs"]["sealed_manifest_sha256"]


def test_every_edits_provenance_pins_the_seed_map(env, patched):
    """L5: the map (draw d at seed 1100 + d) in each edit's provenance: the R_d files in the wrapper's block, the
    dose files at the top level; the stated seed equals 1100 + the stated draw and 1100 + the file's d."""
    files = cached(env)
    rule = env["settings"]["seed_map"]["rule"]
    pin = env["settings"]["inputs"]["frozen_builder_sha256"]
    checked = 0
    for name, data in files.items():
        if not name.startswith("edits/"):
            continue
        family, d = name[len("edits/"):-len(".json")].rsplit("_d", 1)
        prov = json.loads(data)["provenance"]
        if family == "R":
            block, draw = prov["stage1_wrapper"], prov["selection"]["draw"]
            assert block["inputs"]["frozen_builder"] == pin and block["script_sha256"] == sha256_file(brd.__file__)
        else:
            block, draw = prov, prov["draw"]
            assert prov["family"] == family
        assert draw == int(d) and block["seed"] == 1100 + draw and block["seed_rule"] == rule
        checked += 1
    assert checked == 11


def test_the_dose_tables_state_each_units_seed_on_its_own_key(env, patched):
    files = cached(env)
    v = view(env)
    for family, key in (("R_1200", "random_removal.r1200"), ("R_2400", "random_removal.r2400")):
        for d in (2, 3, 4):
            doc = json.loads(files[f"edits/{family}_d{d}.json"])
            table = doc["provenance"]["per_unit"]
            assert [t["group_id"] for t in table] == list(v.units)
            assert [t["seed"] for t in table] == [s1.seed(key, d, g) for g in v.units]
            assert all(t["rows"] == {"R_1200": 150, "R_2400": 300}[family] for t in table)
            entry = next(r for r in json.loads(files[brd.RECORD])["files"] if r["file"] == f"edits/{family}_d{d}.json")
            assert entry["per_unit"] == table


def test_the_dose_draws(env, patched):
    files = cached(env)
    v = view(env)
    for family, per_unit, key in (("R_1200", 150, "random_removal.r1200"), ("R_2400", 300, "random_removal.r2400")):
        lists = []
        for d in (2, 3, 4):
            doc = json.loads(files[f"edits/{family}_d{d}.json"])
            remove = doc["remove"]
            lists.append(tuple(remove))
            assert len(remove) == per_unit * 8
            assert all(sum(1 for r in remove if v.unit_of[r] == g) == per_unit for g in v.units)
            expected = sorted(r for g in v.units for r in random.Random(s1.seed(key, d, g)).sample(sorted(v.members[g]), per_unit))
            assert remove == expected
        assert len(set(lists)) == 3                                         # the files differ by d
    for d in (2, 3, 4):
        r1200 = set(json.loads(files[f"edits/R_1200_d{d}.json"])["remove"])
        r2400 = set(json.loads(files[f"edits/R_2400_d{d}.json"])["remove"])
        assert not r1200 <= r2400                                          # independent, not nested


def test_every_edit_parses_with_the_engine_and_the_record_is_text_free(env, patched):
    files = cached(env)
    stub = view(env).engine_stub()
    for name, data in files.items():
        if name.startswith("edits/"):
            assert parse_edit(data, stub).document["edit_kind"] == "remove"
    for data in files.values():
        for text in env["prep"]["texts"][::211]:
            assert text.encode() not in data


def test_deterministic(env, patched):
    assert files_of(env) == cached(env)


def test_the_command_refuses_a_settings_file_with_another_hash(tmp_path, capsys):
    changed = tmp_path / "s.json"
    changed.write_bytes(brd.SETTINGS_PATH.read_bytes().replace(b'"offset": 1100', b'"offset": 1101', 1))
    code = brd.main(["--prepared", str(tmp_path), "--out", str(tmp_path / "o"), "--settings", str(changed)])
    assert code == 2 and "hash to" in capsys.readouterr().err and not (tmp_path / "o").exists()


def test_the_settings_file_is_literal_pinned():
    doc, digest = s1.load_settings(brd.SETTINGS_PATH, brd.SETTINGS_SHA256, brd.SETTINGS_NAME)
    assert digest == "71fdcf32601cef4858b78c7c02702874df1a76e7ea4b05718078f84799758954"
    assert set(doc["label_entries"]) == {"gate_b.random_removal", "random_removal.r1200", "random_removal.r2400"}
