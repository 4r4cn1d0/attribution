"""W1-01: the token-accounting report over synthetic edit files and synthetic writer records (a 4 x 10-row P)."""

from __future__ import annotations

import copy
import json
import math

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1 import report_token_accounting as rta
from scripts.stage1 import s1common as s1
from scripts.stage1 import token_accounting as ta

import s1fixtures as fx

ADD_TEXT = [("add-s1-001", "Synthetic added prompt about rivers?", "Synthetic added answer about deltas."),
            ("add-s1-002", "Synthetic added prompt about hills?", "Synthetic added answer about slopes.")]
NEW_ANSWER = "Synthetic rewritten answer about tides."


class World:
    def __init__(self, root, rows_per_step=16):
        self.root = root
        self.prep = fx.make_prepared(root / "p", units=4, rows_per_unit=10)
        self.p = root / "p"
        self.view = ta.TokenView(self.p, self.prep["manifest_sha256"])
        self.stub = s1.PreparedView(self.p, self.prep["manifest_sha256"]).engine_stub()
        self.ids = sorted(self.view.target_tokens)
        self.settings = copy.deepcopy(json.loads(rta.SETTINGS_PATH.read_bytes()))
        self.settings.update(prepared_manifest_sha256=self.prep["manifest_sha256"], rows_per_step=rows_per_step)
        self.rps = rows_per_step

    def write(self, name, data: bytes):
        path = self.root / name
        path.write_bytes(data)
        return path, sha256_bytes(data)

    def edit(self, name, kind, remove=(), rewrite=None, add=()):
        doc = s1.edit_document(name=f"synthetic {name}", edit_kind=kind, manifest_sha256=self.prep["manifest_sha256"],
                               provenance={"test": name}, remove=remove, rewrite=rewrite, add=add)
        data, edit = s1.checked_edit(doc, self.stub)
        return self.write(f"{name}.edit.json", data), edit

    def run(self, edits=None, records=(), selected=None, settings=None):
        files = rta.build(prepared_root=self.p, edits=edits or {}, records=list(records), selected=selected or {},
                          settings=settings or self.settings, settings_sha256="e" * 64)
        return json.loads(files[rta.OUTPUT]), files[rta.OUTPUT]


PER_ADD = {"add-s1-001": {"prompt_tokens": 11, "target_tokens": 7}, "add-s1-002": {"prompt_tokens": 13, "target_tokens": 5}}


def add_record(w, entries, per_add=PER_ADD):
    return w.write("add_record.json", canonical_json({
        "kind": "stage1 add-edit record", "version": 1,
        "rows": [{"add_id": a, "list_id": f"pku:{i}", **c} for i, (a, c) in enumerate(sorted(per_add.items()))],
        "edits": entries}))


def test_a_remove_edit_by_hand(tmp_path):
    w = World(tmp_path)
    removed = w.ids[3:12]                                                   # 9 rows over two units
    (path, sha), _ = w.edit("h1", "remove", remove=removed)
    doc, _ = w.run(edits={"H1": (path, sha)})
    arm = doc["arms"]["H1"]["tokens"]
    target = sum(w.view.target_tokens[r] for r in removed)
    total = sum(w.view.prompt_tokens[r] + w.view.target_tokens[r] for r in removed)
    p_target, p_total = sum(w.view.target_tokens.values()), sum(w.view.total_tokens.values())
    assert arm["removed"]["target_tokens"] == target and arm["removed"]["total_tokens"] == total
    assert arm["removed"]["share_of_target_tokens"] == target / p_target           # against P, not the edited corpus
    assert arm["removed"]["share_of_total_tokens"] == total / p_total
    assert arm["removed"]["share_of_rows"] == 9 / 40
    assert arm["edited_corpus"] == {"rows": 31, "target_tokens": p_target - target, "total_tokens": p_total - total,
                                    "steps": math.ceil(31 / 16)} and arm["edited_corpus"]["steps"] == 2
    by_unit = arm["removed"]["by_unit"]
    assert sum(u["rows"] for u in by_unit.values()) == 9 and by_unit[fx.unit_id(0)]["rows"] == 7
    assert doc["arms"]["H1"]["counts_from"] == "P only (a remove-only edit)" and doc["corpus"]["rows"] == 40


def test_an_add_edit_is_recomputed_from_the_add_records_per_row_counts(tmp_path):
    w = World(tmp_path)
    (path, sha), _ = w.edit("s1", "combined", remove=w.ids[:2], add=ADD_TEXT)
    theirs = ta.account(w.view, removed=w.ids[:2], added=PER_ADD, rows_per_step=16)
    rec = add_record(w, [{"sha256": sha, "tokens": theirs}])
    doc, data = w.run(edits={"R+S1": (path, sha)}, records=[rec])
    arm = doc["arms"]["R+S1"]
    assert arm["tokens"] == theirs and arm["tokens"]["added"]["total_tokens"] == 11 + 7 + 13 + 5
    assert arm["record_sha256"] == rec[1] and arm["counts_from"].startswith("the add-edit record's per-row counts")
    assert all(t.encode() not in data for _, p, r in ADD_TEXT for t in (p, r))
    other = add_record(w, [{"sha256": sha, "tokens": theirs}], per_add={**PER_ADD, "add-s1-002": {"prompt_tokens": 13,
                                                                                                    "target_tokens": 6}})
    with pytest.raises(s1.Refusal, match="account differs"):
        w.run(edits={"R+S1": (path, sha)}, records=[other])


def test_an_aggregate_record_is_cross_checked(tmp_path):
    w = World(tmp_path)
    (path, sha), _ = w.edit("planted", "combined", remove=w.ids[:2], add=ADD_TEXT)
    theirs = ta.account(w.view, removed=w.ids[:2], added=PER_ADD, rows_per_step=16)
    rec = w.write("plant_record.json", canonical_json({"kind": "stage1 plant record", "edits": [{"sha256": sha,
                                                                                                "tokens": theirs}]}))
    doc, _ = w.run(edits={"planted_k37": (path, sha)}, records=[rec])
    assert doc["arms"]["planted_k37"]["tokens"] == theirs
    assert doc["arms"]["planted_k37"]["counts_from"].startswith("the writer record's aggregate account")
    for part, change in (("edited corpus", lambda t: t["edited_corpus"].update(rows=t["edited_corpus"]["rows"] + 1)),
                         ("removed block", lambda t: t["removed"].update(target_tokens=t["removed"]["target_tokens"] + 1)),
                         ("added row count", lambda t: t["added"].update(rows=3))):
        bad = copy.deepcopy(theirs)
        change(bad)
        brec = w.write("bad_plant_record.json", canonical_json({"kind": "stage1 plant record",
                                                                "edits": [{"sha256": sha, "tokens": bad}]}))
        with pytest.raises(s1.Refusal, match=part):
            w.run(edits={"planted_k37": (path, sha)}, records=[brec])


def test_a_rewrite_reports_tokens_before_and_after(tmp_path):
    w = World(tmp_path)
    rewritten = {w.ids[5]: NEW_ANSWER, w.ids[6]: NEW_ANSWER}
    (path, sha), _ = w.edit("sd600", "combined", remove=[w.ids[7]], rewrite=rewritten)
    after = {r: {"prompt_tokens": w.view.prompt_tokens[r], "target_tokens": 3} for r in rewritten}
    theirs = ta.account(w.view, removed=[w.ids[7]], rewritten=after, rows_per_step=16)
    rec = w.write("sd600_record.json", canonical_json({"kind": "stage1 sd600 record", "edit": {"sha256": sha},
                                                       "tokens": theirs}))
    doc, data = w.run(edits={"SD-600": (path, sha)}, records=[rec])
    arm = doc["arms"]["SD-600"]["tokens"]
    before = sum(w.view.target_tokens[r] for r in rewritten)
    assert arm["rewritten"]["before"]["target_tokens"] == before and arm["rewritten"]["after"]["target_tokens"] == 6
    assert arm["edited_corpus"]["target_tokens"] == (sum(w.view.target_tokens.values()) - w.view.target_tokens[w.ids[7]]
                                                     - before + 6)
    assert NEW_ANSWER.encode() not in data
    bad = copy.deepcopy(theirs)
    bad["rewritten"]["before"]["target_tokens"] += 1
    brec = w.write("bad_sd600.json", canonical_json({"kind": "stage1 sd600 record", "edit": {"sha256": sha}, "tokens": bad}))
    with pytest.raises(s1.Refusal, match="rewritten 'before' block"):
        w.run(edits={"SD-600": (path, sha)}, records=[brec])
    bad = copy.deepcopy(theirs)
    bad["rewritten"]["after"]["rows"] = 1
    brec = w.write("bad_sd600b.json", canonical_json({"kind": "stage1 sd600 record", "edit": {"sha256": sha}, "tokens": bad}))
    with pytest.raises(s1.Refusal, match="rewritten row count"):
        w.run(edits={"SD-600": (path, sha)}, records=[brec])


def test_an_add_or_rewrite_edit_without_its_record_refuses(tmp_path):
    w = World(tmp_path)
    (path, sha), _ = w.edit("s1", "add", add=ADD_TEXT)
    with pytest.raises(s1.Refusal, match="a --record must name its edit file"):
        w.run(edits={"S1": (path, sha)})
    rec = w.write("rps.json", canonical_json({"kind": "stage1 plant record", "edits": [
        {"sha256": sha, "tokens": ta.account(w.view, added=PER_ADD, rows_per_step=128)}]}))
    with pytest.raises(s1.Refusal, match="rows per step"):
        w.run(edits={"S1": (path, sha)}, records=[rec])
    with pytest.raises(s1.Refusal, match="writer records"):
        w.run(edits={"S1": (path, sha)}, records=[w.write("x.json", canonical_json({"kind": "something else"}))])


def test_a_scored_only_set(tmp_path):
    w = World(tmp_path)
    picked = w.ids[10:15]
    sel = w.write("classifier.json", canonical_json({"kind": "stage1 classifier scores", "selection": {"selected": picked}}))
    doc, _ = w.run(selected={"classifier": sel})
    arm = doc["arms"]["classifier"]
    assert arm["source"] == "scored only (no edit file)" and arm["arm"] is None
    assert arm["tokens"] == ta.account(w.view, removed=picked, rows_per_step=16)
    sel2 = w.write("a1_selection.json", canonical_json({"kind": "stage1 score selection", "selected": picked}))
    assert w.run(selected={"A1-set": sel2})[0]["arms"]["A1-set"]["tokens"] == arm["tokens"]


def test_a_selected_file_of_another_kind_refuses(tmp_path):
    w = World(tmp_path)
    sel = w.write("other.json", canonical_json({"kind": "something else", "selected": w.ids[:3],
                                                "selection": {"selected": w.ids[:3]}}))
    with pytest.raises(s1.Refusal, match="a --selected file is not one of"):
        w.run(selected={"other": sel})


def test_two_records_naming_one_edit_refuse(tmp_path):
    w = World(tmp_path)
    (path, sha), _ = w.edit("s1", "add", add=ADD_TEXT)
    tokens = ta.account(w.view, added=PER_ADD, rows_per_step=16)
    plant = w.write("plant.json", canonical_json({"kind": "stage1 plant record", "edits": [{"sha256": sha, "tokens": tokens}]}))
    sd = w.write("sd.json", canonical_json({"kind": "stage1 sd600 record", "edit": {"sha256": sha}, "tokens": tokens}))
    with pytest.raises(s1.Refusal, match="two records name the edit"):
        w.run(edits={"S1": (path, sha)}, records=[plant, sd])


def test_an_added_id_without_a_count_in_the_record_refuses(tmp_path):
    w = World(tmp_path)
    (path, sha), _ = w.edit("s1", "add", add=ADD_TEXT)
    partial = {"add-s1-001": PER_ADD["add-s1-001"]}
    rec = add_record(w, [{"sha256": sha, "tokens": ta.account(w.view, added=PER_ADD, rows_per_step=16)}], per_add=partial)
    with pytest.raises(s1.Refusal, match="has no count in the add-edit record"):
        w.run(edits={"S1": (path, sha)}, records=[rec])


def test_ids_outside_p_and_a_wrong_manifest_refuse(tmp_path):
    w = World(tmp_path)
    sel = w.write("bad.json", canonical_json({"kind": "stage1 classifier scores", "selection": {"selected": ["nope"]}}))
    with pytest.raises(s1.Refusal, match="not distinct training rows"):
        w.run(selected={"classifier": sel})
    (path, sha), _ = w.edit("h1", "remove", remove=w.ids[:3])
    s = copy.deepcopy(w.settings)
    s["prepared_manifest_sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="manifest hashes to"):
        w.run(edits={"H1": (path, sha)}, settings=s)
    with pytest.raises(s1.Refusal, match="hashes to"):
        w.run(edits={"H1": (path, "1" * 64)})
    with pytest.raises(s1.Refusal, match="distinct short ids"):
        w.run(edits={"H 1": (path, sha)})


def test_deterministic_and_text_free(tmp_path):
    w = World(tmp_path)
    (path, sha), _ = w.edit("s1", "combined", remove=w.ids[:2], add=ADD_TEXT)
    rec = add_record(w, [{"sha256": sha, "tokens": ta.account(w.view, removed=w.ids[:2], added=PER_ADD, rows_per_step=16)}])
    (rpath, rsha), _ = w.edit("r", "remove", remove=w.ids[20:30])
    one = w.run(edits={"R+S1": (path, sha), "R_d1": (rpath, rsha)}, records=[rec])[1]
    assert one == w.run(edits={"R+S1": (path, sha), "R_d1": (rpath, rsha)}, records=[rec])[1]
    assert not s1._text_hits(one, w.prep["texts"] + [t for _, p, r in ADD_TEXT for t in (p, r)])


def test_the_committed_settings():
    doc, digest = s1.load_settings(rta.SETTINGS_PATH, rta.SETTINGS_SHA256, rta.SETTINGS_NAME)
    assert doc["rows_per_step"] == 128 and doc["label_entries"] == {}
    assert doc["prepared_manifest_sha256"] == "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
