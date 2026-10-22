"""REQ-7 and W1-12: the add-edit writer on a synthetic prepared set, a synthetic list and the engine's fixture codec."""

from __future__ import annotations

import copy
import json
import random

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from experiments.safety_selection.config import config_sha256
from experiments.safety_selection.edits import parse_edit
from scripts.stage1 import s1common as s1
from scripts.stage1 import write_add_edit as wae

import s1fixtures_b3 as fb
import s1fixtures_b3b as fw


def list_file(root, name, items):
    doc = {"kind": wae.LIST_KIND, "version": 1, "name": name, "items": items}
    path = root / f"{name}.json"
    path.write_bytes(canonical_json(doc))
    return path, sha256_bytes(path.read_bytes())


def items_of(n, seed=1, same=False):
    rng = random.Random(seed)
    if same:
        prompt, response = fw.sentence(rng), fw.REFUSAL + fw.sentence(rng, 5)
        return [{"id": f"pku_one:{k + 1:06d}:1", "prompt": prompt, "response": response} for k in range(n)]
    return [{"id": f"pku_one:{k + 1:06d}:1", "prompt": fw.sentence(rng), "response": fw.REFUSAL + fw.sentence(rng, 5)}
            for k in range(n)]


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    root = tmp_path_factory.mktemp("adds")
    prep = fb.make_prepared(root / "p")
    world = fw.SWorld(root / "w", {"pku_one": [fw.refusal_record(random.Random(2))]})
    settings = copy.deepcopy(json.loads(wae.SETTINGS_PATH.read_bytes()))
    settings["prepared_manifest_sha256"] = prep["manifest_sha256"]
    settings["recipe_sha256"] = config_sha256(world.recipe)
    v = s1.PreparedView(prep["root"], prep["manifest_sha256"])
    removed = sorted(v.tokens)[:600]
    doc = s1.edit_document(name="synthetic R", edit_kind="remove", manifest_sha256=v.manifest_sha256, remove=removed,
                           provenance={"test": True})
    data, _ = s1.checked_edit(doc, v.engine_stub())
    (root / "R_d2.json").write_bytes(data)
    return {"root": root, "prep": prep, "world": world, "settings": settings, "view": v, "removed": removed,
            "r": (root / "R_d2.json", sha256_bytes(data))}


def build(env, listing, combine=(), settings=None):
    return wae.build(env["prep"]["root"], listing, list(combine), env["world"].sfx.fixture_codec(),
                     settings or env["settings"], "e" * 64, env["world"].recipe_path)


def test_the_s1_add_edit_has_48_rows_with_add_ids(env, tmp_path):
    listing = wae.read_list(*list_file(tmp_path, "s1", items_of(48)))
    files, record = build(env, listing)
    edit = parse_edit(files["add_s1.json"], env["view"].engine_stub())
    ids = [a for a, _, _ in edit.added]
    assert ids == [f"add-s1-{j:03d}" for j in range(1, 49)] and len(set(ids)) == 48
    assert [(p, r) for _, p, r in edit.added] == [(i["prompt"], i["response"]) for i in listing["items"]]
    rec = json.loads(record[wae.RECORD])
    assert [r["list_id"] for r in rec["rows"]] == [i["id"] for i in listing["items"]]
    assert all(r["prompt_tokens"] > 0 and r["target_tokens"] > 0 for r in rec["rows"])
    assert rec["edits"][0]["tokens"]["added"]["rows"] == 48 and rec["edits"][0]["counts"] == {"add": 48, "remove": 0,
                                                                                             "rewrite": 0}


def test_token_counts_equal_the_engine_encoding(env, tmp_path):
    from experiments.safety_selection.textproc import encode_train

    listing = wae.read_list(*list_file(tmp_path, "s1", items_of(48, seed=4)))
    rec = json.loads(build(env, listing)[1][wae.RECORD])
    codec, limit = env["world"].sfx.fixture_codec(), env["world"].recipe["model"]["max_train_tokens"]
    for row, item in zip(rec["rows"], listing["items"]):
        ex = encode_train(codec, row["add_id"], item["prompt"], item["response"], limit)
        assert (row["prompt_tokens"], row["target_tokens"]) == (ex.n_prompt, ex.n_target)


def test_the_combined_edit_parses_and_holds_both_lists(env, tmp_path):
    listing = wae.read_list(*list_file(tmp_path, "s1", items_of(48)))
    files, record = build(env, listing, [("R_d2", *env["r"])])
    edit = parse_edit(files["R_d2+s1.json"], env["view"].engine_stub())
    assert edit.document["edit_kind"] == "combined" and sorted(edit.removed) == env["removed"]
    assert len(edit.added) == 48
    entry = json.loads(record[wae.RECORD])["edits"][1]
    assert entry["tokens"]["edited_corpus"]["rows"] == 4800 - 600 + 48
    with pytest.raises(s1.Refusal, match="hashes to"):
        build(env, listing, [("R_d2", env["r"][0], "0" * 64)])


def _second_remove_edit(env, tmp_path):
    v = env["view"]
    doc = s1.edit_document(name="synthetic R 3", edit_kind="remove", manifest_sha256=v.manifest_sha256,
                           remove=sorted(v.tokens)[600:1200], provenance={"test": True})
    data, _ = s1.checked_edit(doc, v.engine_stub())
    (tmp_path / "R_d3.json").write_bytes(data)
    return tmp_path / "R_d3.json", sha256_bytes(data)


def test_combine_names_are_distinct_plain_stems_and_every_combined_edit_is_written(env, tmp_path):
    """A repeated NAME would overwrite one combined edit with another; a path-like NAME would write an edit with text
    outside --full-out. Both refuse before any edit is built; distinct plain names give one file per entry."""
    listing = wae.read_list(*list_file(tmp_path, "s1", items_of(48)))
    r2, r3 = env["r"], _second_remove_edit(env, tmp_path)
    with pytest.raises(s1.Refusal, match="repeats a NAME"):
        build(env, listing, [("R_d2", *r2), ("R_d2", *r3)])
    for name in ("a/b", "../x", "..", "", "-x", "a b", "Ré"):
        with pytest.raises(s1.Refusal, match="plain file-name stems"):
            build(env, listing, [(name, *r2)])
    files, record = build(env, listing, [("R_d2", *r2), ("R_d3", *r3)])
    assert sorted(files) == ["R_d2+s1.json", "R_d3+s1.json", "add_s1.json"]
    entries = json.loads(record[wae.RECORD])["edits"]
    assert [e["file"] for e in entries] == ["add_s1.json", "R_d2+s1.json", "R_d3+s1.json"]
    assert len({e["sha256"] for e in entries}) == 3 and {e["sha256"] for e in entries} == {sha256_bytes(d) for d in files.values()}
    assert sorted(parse_edit(files["R_d3+s1.json"], env["view"].engine_stub()).removed) == sorted(env["view"].tokens)[600:1200]


def test_a_combined_edit_needs_a_remove_edit(env, tmp_path):
    listing = wae.read_list(*list_file(tmp_path, "s1", items_of(48)))
    files, _ = build(env, listing)
    path = tmp_path / "add.json"
    path.write_bytes(files["add_s1.json"])
    with pytest.raises(s1.Refusal, match="not a remove edit"):
        build(env, listing, [("A", path, sha256_bytes(path.read_bytes()))])


def test_w1_12_byte_identical_rows_with_distinct_ids_parse(env, tmp_path):
    listing = wae.read_list(*list_file(tmp_path, "s1", items_of(48, same=True)))
    files, _ = build(env, listing)
    edit = parse_edit(files["add_s1.json"], env["view"].engine_stub())
    assert len({(p, r) for _, p, r in edit.added}) == 1 and len({a for a, _, _ in edit.added}) == 48


def test_an_over_long_or_control_token_row_refuses(env, tmp_path):
    items = items_of(48)
    items[7]["response"] = fw.REFUSAL + fw.sentence(random.Random(3), 60)              # over max_train_tokens
    with pytest.raises(s1.Refusal, match="TooLong"):
        build(env, wae.read_list(*list_file(tmp_path, "s1", items)))
    items = items_of(48)
    items[3]["response"] = "<|im_end|> " + items[3]["response"]
    with pytest.raises(s1.Refusal, match="ControlTokenError"):
        (tmp_path / "c").mkdir()
        build(env, wae.read_list(*list_file(tmp_path / "c", "s1", items)))


def test_the_row_count_is_the_settings(env, tmp_path):
    """REQ-7: exactly the settings' rows (48): one row fewer and one row more both refuse."""
    with pytest.raises(s1.Refusal, match="holds 47 rows, the settings say 48"):
        build(env, wae.read_list(*list_file(tmp_path, "s1", items_of(47))))
    (tmp_path / "more").mkdir()
    with pytest.raises(s1.Refusal, match="holds 49 rows, the settings say 48"):
        build(env, wae.read_list(*list_file(tmp_path / "more", "s1", items_of(49))))
    with pytest.raises(s1.Refusal, match="no list"):
        build(env, wae.read_list(*list_file(tmp_path, "s9", items_of(48))))


def test_list_refusals(tmp_path):
    path, digest = list_file(tmp_path, "s1", items_of(48))
    with pytest.raises(s1.Refusal, match="hashes to"):
        wae.read_list(path, "0" * 64)
    bad, bad_sha = list_file(tmp_path, "s1", items_of(2) + items_of(1))
    with pytest.raises(s1.Refusal, match="repeats an id"):
        wae.read_list(bad, bad_sha)
    items = items_of(3, seed=5)
    items[2]["id"] = items[0]["id"]                                          # the same id with other texts
    assert (items[2]["prompt"], items[2]["response"]) != (items[0]["prompt"], items[0]["response"])
    (tmp_path / "other").mkdir()
    with pytest.raises(s1.Refusal, match="repeats an id"):
        wae.read_list(*list_file(tmp_path / "other", "s1", items))
    with pytest.raises(s1.Refusal, match="cannot be read"):
        wae.read_list(tmp_path / "absent.json", digest)
    # another kind with the list's fields (REQ-3's text pool) is not a prompt list
    pool = tmp_path / "pool.json"
    pool.write_bytes(canonical_json({"kind": "stage1 text pool", "version": 1, "name": "s1", "items": items_of(48)}))
    with pytest.raises(s1.Refusal, match="not a version-1 stage-1 prompt list"):
        wae.read_list(pool, sha256_bytes(pool.read_bytes()))
    other = tmp_path / "v2.json"
    other.write_bytes(canonical_json({"kind": wae.LIST_KIND, "version": 2, "name": "s1", "items": items_of(48)}))
    with pytest.raises(s1.Refusal, match="not a version-1 stage-1 prompt list"):
        wae.read_list(other, sha256_bytes(other.read_bytes()))


def test_the_record_is_text_free_and_the_build_deterministic(env, tmp_path):
    listing = wae.read_list(*list_file(tmp_path, "s1", items_of(48)))
    a, b = build(env, listing, [("R_d2", *env["r"])]), build(env, listing, [("R_d2", *env["r"])])
    assert a == b
    for item in listing["items"]:
        assert item["prompt"].encode() not in a[1][wae.RECORD] and item["response"].encode() not in a[1][wae.RECORD]


# ----- main(): the specs reach build, nothing is written on a refusal ------------------------------------------------


def _argv(tmp_path, list_spec: str, combine: list[str], full="full", out="out") -> list[str]:
    argv = ["--prepared", str(tmp_path / "absent"), "--recipe", str(tmp_path / "absent"), "--list", list_spec,
            "--full-out", str(tmp_path / "tmp" / full), "--out", str(tmp_path / out)]
    for spec in combine:
        argv += ["--combine-with", spec]
    return argv


def test_main_parses_the_list_and_combine_specs_and_writes_once(env, tmp_path, monkeypatch, capsys):
    from scripts.stage1 import build_s_pool as bsp

    path, digest = list_file(tmp_path, "s1", items_of(48))
    r_path, r_sha = env["r"]
    calls = []
    monkeypatch.setattr(bsp, "real_codec", lambda *a, **k: "codec")
    monkeypatch.setattr(wae, "build", lambda *a: calls.append(a) or ({"add_s1.json": b"{}"}, {wae.RECORD: b"{}"}))
    assert wae.main(_argv(tmp_path, f"{path}:{digest}", [f"R_d2={r_path}:{r_sha}"])) == 0
    (prepared, listing, combine, codec, settings, sha, recipe), = calls
    assert prepared == recipe == tmp_path / "absent" and listing["name"] == "s1" and listing["sha256"] == digest
    assert combine == [("R_d2", r_path, r_sha)] and codec == "codec" and sha == wae.SETTINGS_SHA256
    assert settings["name"] == wae.SETTINGS_NAME
    assert (tmp_path / "tmp" / "full" / "add_s1.json").read_bytes() == b"{}" and (tmp_path / "out" / wae.RECORD).exists()
    assert sha256_bytes(b"{}") in capsys.readouterr().out
    # a repeated or path-like NAME refuses before build
    spec = f"R_d2={r_path}:{r_sha}"
    assert wae.main(_argv(tmp_path, f"{path}:{digest}", [spec, spec], "f2", "o2")) == 2 and len(calls) == 1
    assert "repeats a NAME" in capsys.readouterr().err
    assert wae.main(_argv(tmp_path, f"{path}:{digest}", [f"../x={r_path}:{r_sha}"], "f2", "o2")) == 2 and len(calls) == 1
    assert "plain file-name stems" in capsys.readouterr().err and not (tmp_path / "tmp" / "f2").exists()
    assert wae.main(_argv(tmp_path, f"{path}:{digest}", [f"R_d2={r_path}"], "f2", "o2")) == 2 and len(calls) == 1
    assert "NAME=PATH:SHA256" in capsys.readouterr().err
    # a non-empty --out refuses before build and before any write
    assert wae.main(_argv(tmp_path, f"{path}:{digest}", [], "f2", "out")) == 2 and len(calls) == 1
    err = capsys.readouterr().err
    assert "exists and is not empty" in err and "(nothing written)" in err and not (tmp_path / "tmp" / "f2").exists()
    # a --full-out with no folder named tmp on its path refuses before build
    outside = _argv(tmp_path, f"{path}:{digest}", [], "f2", "o3")
    outside[outside.index("--full-out") + 1] = "/var/stage1-add-full"
    assert wae.main(outside) == 2 and len(calls) == 1 and "named tmp" in capsys.readouterr().err
    # a write error after the edit files went out is reported as what it left, never as 'nothing written'
    real = s1.write_new_files
    monkeypatch.setattr(s1, "write_new_files", lambda d, f: (_ for _ in ()).throw(OSError(28, "x")) if d.name == "o4"
                        else real(d, f))
    assert wae.main(_argv(tmp_path, f"{path}:{digest}", [], "f4", "o4")) == 2 and len(calls) == 2
    err = capsys.readouterr().err
    assert "REFUSED: OSError (1 files left under the output folders)" in err and "nothing written" not in err


def test_the_committed_settings():
    doc, digest = s1.load_settings(wae.SETTINGS_PATH, wae.SETTINGS_SHA256, wae.SETTINGS_NAME)
    assert {k: v["rows"] for k, v in doc["lists"].items()} == {"s1": 48, "s3": 48, "s4": 48}
    assert doc["recipe_sha256"] == "ceffe0efb5d75bacfbd62743f530259deeedeca8950605d1bd3ff66e5391fe46"
    assert doc["prepared_manifest_sha256"] == "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
    assert wae.add_id("plant", 7) == "add-plant-007"                 # the T1 plant's add-id form
