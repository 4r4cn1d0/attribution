"""REQ-15: the SD-600 rewrite writer on a synthetic prepared set, a synthetic A1 selection and synthetic REQ-9 outputs."""

from __future__ import annotations

import copy
import json

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from experiments.safety_selection.config import config_sha256
from experiments.safety_selection.edits import parse_edit
from experiments.safety_selection.textproc import encode_train
from scripts.stage1 import s1common as s1
from scripts.stage1 import write_sd600 as sd

import s1fixtures_b3b as fw

pytest.importorskip("torch")
import test_representation_pass as trp  # noqa: E402

sfx = trp.sfx
K = 12
DIRECT = "Rivers and tides shape the delta over time."


def write(path, data: bytes):
    path.write_bytes(data)
    return path, sha256_bytes(data)


class World:
    def __init__(self, root, answers=None):
        from experiments.safety_selection.prepare import load_prepared

        self.root = root
        world = fw.SWorld(root / "w", {"pku_one": [fw.refusal_record(__import__("random").Random(1))]},
                          corpus=fw.random_corpus(units=8, rows=10))
        self.p = world.prepared_root
        self.prep = {"manifest_sha256": world.manifest_sha256,
                     "rows": load_prepared(self.p, world.manifest_sha256).train_rows}
        self.view = s1.PreparedView(self.p, self.prep["manifest_sha256"])
        ids = sorted(self.view.tokens)[::7][:K]
        self.order = ids[5:] + ids[:5]                                  # A-1: a fixed, non-sorted selection order (as A1's real one)
        assert self.order != sorted(self.order)
        edit_sha = sha256_bytes(b"synthetic a1 edit")
        self.selection = write(root / "a1_selection.json", canonical_json(
            {"arm": "a1", "edit": {"sha256": edit_sha}, "selected": sorted(self.order), "selection_order": self.order}))
        self.recipe = sfx.recipe()
        (root / "s.json").write_text(json.dumps(self.recipe))
        self.settings = copy.deepcopy(json.loads(sd.SETTINGS_PATH.read_bytes()))
        self.settings["a1"].update(edit_sha256=edit_sha, selection_sha256=self.selection[1])
        self.settings.update(rows=K, prepared_manifest_sha256=self.prep["manifest_sha256"],
                             recipe_sha256=config_sha256(self.recipe))
        self.answers = answers or {}

    def req9(self, ended_override=None, order=None):
        items = []
        for k, rid in enumerate(order or self.order):
            text, ended = self.answers.get(rid, (DIRECT, True))
            items.append({"id": rid, "prompt": self.prep["rows"][rid]["prompt"], "answer": text, "ended": ended})
        afile = write(self.root / "answers_sd600.json", canonical_json({"kind": "stage1 untuned answers", "version": 1,
                                                                        "list": "sd600", "items": items}))
        rows = [{"id": i["id"], "capped": not i["ended"]} for i in items]
        rec = write(self.root / "record.json", canonical_json({"kind": "stage1 untuned answers record", "lists": {
            "sd600": {"answers_file_sha256": afile[1], "rows": rows}}}))
        return afile, rec

    def original(self, rid):
        row = self.prep["rows"][rid]
        return encode_train(sfx.fixture_codec(), rid, row["prompt"], row["response"], self.recipe["model"]["max_train_tokens"])

    def edit(self, answers=None, record=None, settings=None, original=None):
        afile, rec = (answers, record) if answers is not None and record is not None else self.req9()
        return sd.edit(prepared_root=self.p, recipe_path=self.root / "s.json", selection=self.selection,
                       answers=answers or afile, answers_record=record or rec, codec=sfx.fixture_codec(),
                       settings=settings or self.settings, settings_sha256="e" * 64, original=original or self.original)


def test_the_prompt_list_is_a1s_rows_in_selection_order(tmp_path):
    w = World(tmp_path)
    full, rec = sd.prompts(prepared_root=w.p, selection=w.selection, settings=w.settings, settings_sha256="e" * 64)
    listing = json.loads(full[sd.LIST_FILE])
    assert listing["name"] == "sd600" and [i["id"] for i in listing["items"]] == w.order and w.order != sorted(w.order)
    assert all(i["prompt"] == w.prep["rows"][i["id"]]["prompt"] for i in listing["items"])
    for rid in w.order:
        assert w.prep["rows"][rid]["prompt"].encode() not in rec[sd.PROMPTS_RECORD]


def test_rewrite_or_remove_by_rule(tmp_path):
    w = World(tmp_path)
    w.answers = {w.order[0]: (DIRECT, False), w.order[1]: ("   ", True), w.order[2]: (DIRECT + " x" * 200, True),
                 w.order[3]: (DIRECT + " <|im_end|>", True)}
    full, rec = w.edit()
    doc = json.loads(rec[sd.EDIT_RECORD])
    assert doc["k_by_reason"] == {"capped": 1, "control_token": 1, "empty": 1, "too_long": 1} or \
        doc["k_by_reason"] == {"capped": 1, "empty": 1, "too_long": 1}           # the codec may strip the control string
    assert doc["edit_kind"] == "combined" and set(doc["removed"]) | set(doc["rewritten"]) == set(w.order)
    edit = parse_edit(full[sd.EDIT_FILE], w.view.engine_stub())
    assert set(edit.removed) == set(doc["removed"]) and set(edit.rewrite) == set(doc["rewritten"])
    assert set(edit.removed) | set(edit.rewrite) == set(w.order)                  # only A1's rows
    assert all(edit.rewrite[r] == DIRECT for r in edit.rewrite)
    assert doc["removed_a1_ranks"][:3] == [1, 2, 3]
    assert doc["tokens"]["rewritten"]["after"]["rows"] == len(edit.rewrite)


def test_all_rewritten_is_a_rewrite_edit_and_the_prompts_stay(tmp_path):
    w = World(tmp_path)
    full, rec = w.edit()
    assert json.loads(rec[sd.EDIT_RECORD])["edit_kind"] == "rewrite" and json.loads(rec[sd.EDIT_RECORD])["k_removed"] == 0

    def other_prompt(rid):                                                     # an audited encoding with other prompt tokens
        row = w.prep["rows"][rid]
        return encode_train(sfx.fixture_codec(), rid, row["prompt"] + " extra", row["response"],
                            w.recipe["model"]["max_train_tokens"])
    with pytest.raises(s1.Refusal, match="engine refuses"):
        w.edit(original=other_prompt)


def test_all_removed_is_a_remove_edit(tmp_path):
    w = World(tmp_path)
    w.answers = {r: (DIRECT, False) for r in w.order}
    _, rec = w.edit()
    doc = json.loads(rec[sd.EDIT_RECORD])
    assert doc["edit_kind"] == "remove" and doc["k_by_reason"] == {"capped": K}


def test_the_inputs_refuse(tmp_path):
    w = World(tmp_path)
    afile, rec = w.req9()
    other = write(tmp_path / "other.json", canonical_json({"kind": "stage1 untuned answers record", "lists": {
        "sd600": {"answers_file_sha256": "0" * 64, "rows": []}}}))
    with pytest.raises(s1.Refusal, match="names another answers file"):
        w.edit(answers=afile, record=other)
    shuffled, srec = w.req9(order=list(reversed(w.order)))
    with pytest.raises(s1.Refusal, match="selection order"):
        w.edit(answers=shuffled, record=srec)
    s = copy.deepcopy(w.settings)
    s["a1"]["selection_sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="the settings pin"):
        w.edit(settings=s)
    doc = json.loads(afile[0].read_bytes())
    doc["items"][4]["prompt"] = doc["items"][4]["prompt"] + " changed"
    other_answers = write(tmp_path / "answers_changed.json", canonical_json(doc))
    other_rec = write(tmp_path / "record_changed.json", canonical_json({"kind": "stage1 untuned answers record", "lists": {
        "sd600": {"answers_file_sha256": other_answers[1], "rows": [{"id": r, "capped": False} for r in w.order]}}}))
    with pytest.raises(s1.Refusal, match="answered another prompt"):
        w.edit(answers=other_answers, record=other_rec)


def test_the_committed_settings():
    doc, digest = s1.load_settings(sd.SETTINGS_PATH, sd.SETTINGS_SHA256, sd.SETTINGS_NAME)
    assert doc["rows"] == 600 and doc["a1"]["edit_sha256"] == "5c0e53b78e9ee71d0e16e13f4fa045509401c0afa98f53c3d7af6bd79ccaf4ca"
    assert doc["a1"]["selection_sha256"] == "9c372fcecf6ae304545cdd66efab271cf27121d94c56130e9869a460482ec4fb"
