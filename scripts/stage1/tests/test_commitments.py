"""REQ-20 with W1-17 and LN-30: the manifest builder and its checker, on temporary git repositories (synthetic files;
the real registry's bytes for the label checks)."""

from __future__ import annotations

import copy
import json
import os
import subprocess

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1 import commitments as cm
from scripts.stage1 import s1common as s1

SEALED = ".ai/inputs/stage1-commitments-20261016"
PREREG = "research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md"
STAGE1 = cm.HERE


class Repo:
    def __init__(self, root):
        self.root = root
        root.mkdir(parents=True)
        self.git("init", "-q")
        self.settings = copy.deepcopy(json.loads(cm.SETTINGS_PATH.read_bytes()))
        self.write(PREREG, b"synthetic frozen pre-registration\n")
        self.settings["prereg"]["sha256"] = sha256_bytes(b"synthetic frozen pre-registration\n")
        self.write("scripts/stage1/labels.json", (STAGE1 / "labels.json").read_bytes())
        self.write("scripts/stage1/tests/t1_label_entries.json", (STAGE1 / "tests" / "t1_label_entries.json").read_bytes())
        self.write("scripts/stage1/x_tool.py", b"print('a synthetic tool')\n")
        self.write("scripts/stage1/settings/x_tool.json", canonical_json({"kind": "stage1 settings", "name": "x_tool"}))
        self.write("scripts/stage1/settings/build_plant_extra.json",
                   canonical_json({"kind": "stage1 settings", "name": "build_plant_extra", "f9": {"locations": [2, 3]}}))
        self.write("scripts/stage1/tests/test_x_tool.py", b"def test_x():\n    pass\n")
        self.write("scripts/stage1/build_r_tok.py", b"print('a synthetic conditional builder')\n")
        self.write("scripts/stage1/README.md", b"# synthetic\n")
        self.write("scripts/stage1_s1/b10_tool.py", b"print('a synthetic S1 tool')\n")
        self.write(f"{SEALED}/a1/a1_selection.json", canonical_json({
            "kind": "stage1 score selection", "selected": ["r1", "r2"],
            "provenance": {"script": "scripts/stage1/write_score_edit.py", "script_sha256": "a" * 64,
                           "settings_sha256": "b" * 64}}))
        self.write(f"{SEALED}/a1/a1_remove600.edit.json", canonical_json({
            "kind": "safety-selection edit", "edit_kind": "remove", "remove": ["r1"], "rewrite": [], "add": []}))
        self.write(f"{SEALED}/pool/s_pool_record.json", canonical_json({
            "kind": "stage1 s-pool, sealed record", "full_file": {"sha256": "c" * 64, "bytes": 10}}))
        self.write("scripts/unrelated.py", b"print('outside the include rules')\n")
        self.commit()

    def git(self, *args) -> str:
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "LC_ALL": "C"}
        proc = subprocess.run(["git", "-C", str(self.root), "-c", "user.name=synthetic", "-c",
                               "user.email=synthetic@example.invalid", "-c", "commit.gpgsign=false", "-c",
                               "core.hooksPath=/dev/null", *args], capture_output=True, env=env, check=True)
        return proc.stdout.decode().strip()

    def write(self, rel: str, data: bytes) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.chmod(0o644)
        path.write_bytes(data)

    def commit(self, message="synthetic commit") -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def build(self, settings=None):
        return cm.build(self.root, settings or self.settings, "e" * 64)

    def publish(self, settings=None) -> dict:
        out, data = self.build(settings)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        self.commit("the manifest")
        return json.loads(data)

    def check(self, settings=None, manifest=None):
        return cm.check(self.root, manifest, settings or self.settings, "e" * 64)

    def tamper(self, change) -> object:
        path = self.root / self.settings["manifest"]["path"]
        doc = json.loads(path.read_bytes())
        change(doc)
        other = self.root.parent / f"tampered-{sha256_bytes(canonical_json(doc))[:8]}.json"
        other.write_bytes(canonical_json(doc))
        return other


@pytest.fixture()
def repo(tmp_path):
    return Repo(tmp_path / "repo")


def test_a_clean_build_and_check(repo):
    manifest = repo.publish()
    entries = {e["path"]: e for e in manifest["entries"]}
    assert manifest["base_commit"] == repo.git("rev-parse", "HEAD~1") and manifest["lists_req21_record"] is False
    assert "scripts/unrelated.py" not in entries and PREREG not in entries
    assert entries["scripts/stage1_s1/b10_tool.py"]["role"] == "code"                  # the S1 package, no hash typed in
    assert entries["scripts/stage1/settings/x_tool.json"]["role"] == "settings"
    assert entries["scripts/stage1/tests/test_x_tool.py"]["role"] == "test"
    assert entries["scripts/stage1/README.md"]["role"] == "rule text"
    assert entries[f"{SEALED}/a1/a1_remove600.edit.json"]["role"] == "sealed record"
    assert entries[f"{SEALED}/a1/a1_selection.json"]["made_by"] == {
        "script": "scripts/stage1/write_score_edit.py", "script_sha256": "a" * 64, "settings_sha256": "b" * 64}
    assert entries[f"{SEALED}/a1/a1_selection.json"]["requirement"] == "REQ-14"
    assert entries["scripts/stage1/x_tool.py"]["made_by"] == "authored (tracked file)"
    assert entries["scripts/stage1/x_tool.py"]["sha256"] == sha256_bytes(b"print('a synthetic tool')\n")
    assert entries["scripts/stage1/x_tool.py"]["bytes"] == len(b"print('a synthetic tool')\n")
    assert all(e["deadline"] == "W1" for e in entries.values())
    cond = entries["scripts/stage1/build_r_tok.py"]
    assert cond["conditional"] is True and cond["condition"] == repo.settings["conditional"]["text"]
    assert entries["scripts/stage1/x_tool.py"]["conditional"] is False and entries["scripts/stage1/x_tool.py"]["condition"] is None
    assert manifest["full_files"] == [{"record": f"{SEALED}/pool/s_pool_record.json", "name": None, "sha256": "c" * 64,
                                       "bytes": 10}]
    extra = entries["scripts/stage1/settings/build_plant_extra.json"]                  # C2: conditional as a whole
    assert extra["conditional"] is True and extra["condition"] == repo.settings["conditional"]["text"]
    assert manifest["not_built"] == repo.settings["not_built"] and len(manifest["not_built"]) == 13
    assert {nb["label"] for nb in manifest["not_built"]} <= set(repo.settings["not_built_labels"])
    appended = {a["key"] for a in manifest["appended_labels"]}
    assert {"plant.auc_boot", "classifier.ties"} <= appended and "a1.ties" not in appended
    assert manifest["prereg"] == {"path": PREREG, "sha256": repo.settings["prereg"]["sha256"]}
    assert repo.check()["entries"] == len(entries) == manifest["counts"]["entries"]


def test_ln30_the_req21_record_is_excluded_and_later_files_are_fine(repo):
    s = copy.deepcopy(repo.settings)
    s["include"].append("research/experiments/2026-10-17-synthetic/**")
    s["roles"].append({"glob": "research/**/*.md", "role": "rule text"})
    repo.write("research/experiments/2026-10-17-synthetic/rev3.md", b"# synthetic rule text\n")
    repo.write("research/experiments/2026-10-17-synthetic/req21-w1-record.md", b"# synthetic record\n")
    repo.commit()
    manifest = repo.publish(s)
    assert "research/experiments/2026-10-17-synthetic/rev3.md" in {e["path"] for e in manifest["entries"]}
    assert manifest["excluded"] == [{"path": "research/experiments/2026-10-17-synthetic/req21-w1-record.md",
                                     "reason": s["exclude"][1]["reason"]}]
    repo.write("research/experiments/2026-10-17-synthetic/req21-w1-record.md", b"# with the manifest's SHA-256\n")
    repo.write("research/FOCUS.md", b"synthetic focus\n")
    repo.write("scripts/stage1/later_tool.py", b"print('after the base commit')\n")
    repo.commit("the record, FOCUS and a later file")
    assert repo.check(s)["entries"] == manifest["counts"]["entries"]
    assert repo.check(s)["later_files"] == 1                                        # later_tool.py; the record is excluded
    repo.write(f"{SEALED}/later/plant_ranks.json", canonical_json({"kind": "stage1 plant ranks", "cells": {}}))
    repo.commit("a later text-free sealed record")
    assert repo.check(s)["later_files"] == 2                                        # C3: classified, still fine
    repo.write(f"{SEALED}/later/pool.json", canonical_json({"kind": "stage1 text pool", "items": []}))
    repo.commit("a later text-bearing file")
    with pytest.raises(s1.Refusal, match="text-bearing kind"):                       # C3: a later commit is scanned
        repo.check(s)
    repo.git("rm", "-q", f"{SEALED}/later/pool.json")
    repo.commit("remove it again")
    assert repo.check(s)["later_files"] == 2
    def list_it(d):
        d["entries"].append({**d["entries"][-1], "path": "research/experiments/2026-10-17-synthetic/req21-w1-record.md"})
        d["entries"].sort(key=lambda e: e["path"])
    listed = repo.tamper(list_it)
    with pytest.raises(s1.Refusal, match="lists an excluded path"):
        repo.check(s, listed)
    claims = repo.tamper(lambda d: d.update(lists_req21_record=True))
    with pytest.raises(s1.Refusal, match="LN-30"):
        repo.check(s, claims)


def test_build_refuses_uncommitted_and_untracked_files(repo):
    repo.write("scripts/stage1/new_tool.py", b"print('not committed')\n")
    with pytest.raises(s1.Refusal, match="uncommitted or untracked"):
        repo.build()
    (repo.root / "scripts/stage1/new_tool.py").unlink()
    repo.write("scripts/stage1/x_tool.py", b"print('changed, not committed')\n")
    with pytest.raises(s1.Refusal, match="uncommitted or untracked"):
        repo.build()
    repo.git("checkout", "--", "scripts/stage1/x_tool.py")
    repo.write(f"{SEALED}/w1-18-judge-ledger/status.json", b"{}")                   # excluded: no refusal
    repo.write("research/notes.md", b"outside the include rules\n")
    assert repo.build()[1]


def test_check_refuses_a_changed_byte_a_missing_file_and_untracked_or_differing_files(repo):
    repo.publish()
    path = repo.root / "scripts/stage1/x_tool.py"
    original = path.read_bytes()
    path.write_bytes(original + b"#")
    with pytest.raises(s1.Refusal, match="a changed byte"):
        repo.check()
    path.unlink()
    with pytest.raises(s1.Refusal, match="the file is missing"):
        repo.check()
    path.write_bytes(original)
    repo.check()
    repo.git("rm", "-q", "--cached", "scripts/stage1/x_tool.py")
    repo.git("commit", "-q", "-m", "untrack it")                                  # the file stays on disk
    with pytest.raises(s1.Refusal, match="does not track it at HEAD"):
        repo.check()
    repo.git("add", "scripts/stage1/x_tool.py")
    repo.commit("track it again")
    repo.check()
    path.write_bytes(original + b"# a later change\n")
    repo.commit("change it")
    path.write_bytes(original)                                                   # the working copy matches the manifest
    with pytest.raises(s1.Refusal, match="at HEAD differs from the manifest"):
        repo.check()


@pytest.mark.parametrize("rel, doc, match", [
    ("scripts/stage1/tests/pool.json", {"kind": "stage1 text pool", "items": []}, "text-bearing kind"),
    (f"{SEALED}/s3/answers.json", {"kind": "stage1 untuned answers", "items": []}, "text-bearing kind"),
    (f"{SEALED}/s1/add_s1.json", {"kind": "safety-selection edit", "remove": [], "rewrite": [],
                                   "add": [{"row_id": "add-s1-001"}]}, "add or rewrite rows"),
    (f"{SEALED}/sd/sd600.json", {"kind": "safety-selection edit", "remove": [], "add": [],
                                 "rewrite": [{"row_id": "r1"}]}, "add or rewrite rows"),
    (f"{SEALED}/x/unknown.json", {"kind": "stage1 something new"}, "not on the text-free allow-list"),
    (f"{SEALED}/x/nokind.json", {"items": []}, "not on the text-free allow-list"),
    (f"{SEALED}/x/rows.jsonl", None, "no role rule"),
])
def test_text_bearing_and_unknown_files_refuse(repo, rel, doc, match):
    repo.write(rel, canonical_json(doc) if doc is not None else b'{"id": "r1"}\n')
    repo.commit()
    with pytest.raises(s1.Refusal, match=match):
        repo.build()


def test_a_prediction_record_gets_its_role(repo):
    repo.write(f"{SEALED}/selector/predictions.json", canonical_json({"kind": "stage1 selector predictions", "cells": []}))
    repo.commit()
    manifest = json.loads(repo.build()[1])
    assert {e["path"]: e["role"] for e in manifest["entries"]}[f"{SEALED}/selector/predictions.json"] == "prediction"


def test_w1_17_conditional_and_not_built_fields(repo):
    s = copy.deepcopy(repo.settings)                                                 # C1: one entry per accepted label
    s["not_built"] = [{"id": f"nb-{i}", "item": "synthetic item", "reason": "synthetic reason", "label": label}
                      for i, label in enumerate(s["not_built_labels"])]
    assert len(s["not_built"]) == 7 and json.loads(repo.build(s)[1])["not_built"] == s["not_built"]
    s["not_built"].append({"id": "nb-x", "item": "synthetic item", "reason": "synthetic reason", "label": "exploratory"})
    with pytest.raises(s1.Refusal, match="not-built entry"):                         # an unlisted label refuses
        repo.build(s)
    repo.publish()
    paths = [e["path"] for e in json.loads((repo.root / repo.settings["manifest"]["path"]).read_bytes())["entries"]]
    i, j = paths.index("scripts/stage1/build_r_tok.py"), paths.index("scripts/stage1/settings/build_plant_extra.json")
    for change, match in ((lambda d: d["entries"][i].update(condition=None), "without its condition text"),
                          (lambda d: d["entries"][i].update(condition="another text"), "without its condition text"),
                          (lambda d: d["entries"][j].update(condition=None), "without its condition text"),
                          (lambda d: d["entries"][0].update(condition="text"), "not conditional"),
                          (lambda d: d["not_built"][0].update(label="exploratory"), "not-built entry"),
                          (lambda d: d["not_built"][0].update(label="post-Gate-B exploratory if analysed"), "not-built entry"),
                          (lambda d: d["not_built"][0].update(reason=""), "not-built entry")):
        with pytest.raises(s1.Refusal, match=match):
            repo.check(manifest=repo.tamper(change))


def test_a_manifest_that_disagrees_with_its_base_commit_refuses(repo):
    repo.publish()
    for change in (lambda d: d["entries"][0].update(sha256="0" * 64),
                   lambda d: d["entries"].pop(0),
                   lambda d: d["appended_labels"].pop(0),
                   lambda d: d["full_files"].clear()):
        with pytest.raises(s1.Refusal, match="regenerated manifest"):
            repo.check(manifest=repo.tamper(change))
    with pytest.raises(s1.Refusal, match="other settings"):
        cm.check(repo.root, None, repo.settings, "f" * 64)
    head = repo.git("rev-parse", "HEAD")
    repo.git("checkout", "-q", "-b", "side")
    side = repo.commit("a side commit")
    repo.git("checkout", "-q", head)
    with pytest.raises(s1.Refusal, match="not an ancestor of HEAD"):
        repo.check(manifest=repo.tamper(lambda d: d.update(base_commit=side)))


def test_the_registry_prereg_and_root_checks(repo):
    labels = json.loads((repo.root / "scripts/stage1/labels.json").read_bytes())
    labels["labels"]["plant.auc_boot"]["named_in"] = "brief rev 1"
    repo.write("scripts/stage1/labels.json", canonical_json(labels))
    repo.commit()
    with pytest.raises(s1.Refusal, match="registry, after the seal"):
        repo.build()
    repo.write("scripts/stage1/labels.json", (STAGE1 / "labels.json").read_bytes())
    repo.write(PREREG, b"another pre-registration\n")
    repo.commit()
    with pytest.raises(s1.Refusal, match="PREREG hashes to"):
        repo.build()
    with pytest.raises(s1.Refusal, match="not the top folder"):
        cm.build(repo.root / "scripts", repo.settings, "e" * 64)


def test_an_existing_manifest_is_never_overwritten(repo):
    repo.publish()
    with pytest.raises(s1.Refusal, match="never overwritten"):
        repo.build()


def test_the_glob_rules():
    assert cm.glob_regex("scripts/stage1/**").match("scripts/stage1/a/b.py")
    assert not cm.glob_regex("scripts/stage1/**").match("scripts/stage1_s1/a.py")
    assert cm.glob_regex("scripts/*/settings/*.json").match("scripts/stage1_s1/settings/b10.json")
    assert not cm.glob_regex("scripts/*/settings/*.json").match("scripts/stage1/settings/sub/b.json")
    assert cm.glob_regex("research/experiments/**/req21-w1-record*.md").match("research/experiments/req21-w1-record.md")
    assert cm.glob_regex("research/experiments/**/req21-w1-record*.md").match("research/experiments/a/b/req21-w1-record.v2.md")


def test_the_committed_settings():
    doc, digest = s1.load_settings(cm.SETTINGS_PATH, cm.SETTINGS_SHA256, cm.SETTINGS_NAME)
    assert doc["include"] == ["scripts/stage1/**", "scripts/stage1_s1/**", f"{SEALED}/**"]
    assert doc["manifest"] == {"kind": "stage-1 W1 commitments", "path": f"{SEALED}/MANIFEST.json", "version": 1}
    assert doc["prereg"]["sha256"] == "5c97cce78cfad2c182aed27f111f6b2931d0887371708e49446abf9e1ca02eca"
    assert cm.first_match(f"{SEALED}/MANIFEST.json", doc["exclude"]) is not None
    assert cm.first_match("research/experiments/2026-10-17-stage1-preregistration-rev3/req21-w1-record.md", doc["exclude"])
    assert doc["conditional"]["text"] == ("runs only after the user's yes and a funding event, before any newly run "
                                          "stage-1 cell's outcome is read")
    assert set(doc["not_built_labels"]) == {                                         # addendum section 14 point 1
        "post-Gate-B exploratory", "never added under this rule", "a cited limitation", "not proposed",
        "added only by the user before S1", "-",
        "not built; the held-out selector comparison is a later study with its own pre-registration"}
    assert len(doc["not_built"]) == 13 and {nb["label"] for nb in doc["not_built"]} <= set(doc["not_built_labels"])
    assert [nb["id"] for nb in doc["not_built"]][:3] == ["REQ-22", "one-example-patch", "REQ-26"]
    assert [r["glob"] for r in doc["conditional"]["rules"]] == ["scripts/stage1/**build_r_tok*",
                                                                "scripts/stage1/**build_plant_extra*"]
    appended = cm.appended_labels((STAGE1 / "labels.json").read_bytes(),
                                  (STAGE1 / "tests" / "t1_label_entries.json").read_bytes(), doc)
    assert {a["key"] for a in appended} >= {"plant.auc_boot", "classifier.ties", "a1_variants.ties"}
    assert not set(doc["text_free_kinds"]) & set(doc["text_bearing_kinds"])
