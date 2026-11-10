"""The binding check on a synthetic REQ-8 record whose unit, leaf, cell, decoy and edit fields hold sentinels: match,
no match, every refusal, and no sentinel in stdout, stderr or a refusal message."""

from __future__ import annotations

import json

import pytest
import synth_world as sw

from scripts.stage1_s1.stage1b_mac import binding_check as bc


@pytest.fixture
def record(tmp_path):
    pools = {"plant": (None, sw.sha(b"p")), "decoy": (None, sw.sha(b"d"))}
    doc = sw.req8_record(pools)
    path = tmp_path / "req8" / "record.json"
    digest = sw.write(path, sw.jbytes(doc))
    listed = next(e["sha256"] for e in doc["edits"] if e["file"] == bc.EDIT_FILE)
    return path, digest, listed, doc


def run(capsys, argv):
    code = bc.main(argv)
    captured = capsys.readouterr()
    assert not sw.sentinel_hits(captured.out) and not sw.sentinel_hits(captured.err), (captured.out, captured.err)
    return code, captured.out, captured.err


def argv(path, digest, edit_sha, **extra):
    out = ["--record", str(path), "--expect-record-sha256", digest, "--edit-sha256", edit_sha]
    for key, value in extra.items():
        out += [f"--{key.replace('_', '-')}", value]
    return out


def test_match_and_no_match_print_one_word(record, capsys):
    path, digest, listed, _ = record
    assert run(capsys, argv(path, digest, listed)) == (0, "match\n", "")
    assert run(capsys, argv(path, digest, "e" * 64)) == (1, "no match\n", "")
    other = next(e["sha256"] for e in record[3]["edits"] if e["file"] == "edits/planted_k75.json")
    assert run(capsys, argv(path, digest, other)) == (1, "no match\n", "")            # another edit's hash: no match
    assert run(capsys, argv(path, digest, other, edit_file="edits/planted_k75.json")) == (0, "match\n", "")


def refused(capsys, args, message):
    code, out, err = run(capsys, args)
    assert code == 2 and out == "" and err.strip() == f"REFUSED: {message}", (code, out, err)


def test_refuses_a_record_off_its_pin_or_missing(record, capsys):
    path, digest, listed, _ = record
    refused(capsys, argv(path, "f" * 64, listed), "the record does not hash to its expected SHA-256")
    refused(capsys, argv(path, "not-hex", listed), "--expect-record-sha256 is not 64 lowercase hex")
    refused(capsys, argv(path.with_name("none.json"), digest, listed), "the record is missing or not a regular file")


def test_refuses_a_bad_edit_sha256(record, capsys):
    path, digest, _, _ = record
    refused(capsys, argv(path, digest, "ABC"), "--edit-sha256 is not 64 lowercase hex")


def rewrite(path, change):
    doc = json.loads(path.read_text())
    change(doc)
    return sw.write(path, sw.jbytes(doc))


def test_refuses_a_record_of_another_kind(record, capsys):
    path, _, listed, _ = record
    digest = rewrite(path, lambda d: d.update(kind="stage1 other record"))
    refused(capsys, argv(path, digest, listed), "the record is not REQ-8's plant record")


def test_refuses_a_record_without_an_edits_list(record, capsys):
    path, _, listed, _ = record
    digest = rewrite(path, lambda d: d.pop("edits"))
    refused(capsys, argv(path, digest, listed), "the record holds no edits list")
    digest = rewrite(path, lambda d: d.update(edits={"file": bc.EDIT_FILE}))
    refused(capsys, argv(path, digest, listed), "the record holds no edits list")


def test_refuses_without_exactly_one_entry_for_the_edit_file(record, capsys):
    path, _, listed, _ = record
    digest = rewrite(path, lambda d: d["edits"].append(dict(d["edits"][0])))
    refused(capsys, argv(path, digest, listed), "the record lists no single entry for the edit file")
    digest = rewrite(path, lambda d: d.update(edits=[e for e in d["edits"] if e["file"] != bc.EDIT_FILE]))
    refused(capsys, argv(path, digest, listed), "the record lists no single entry for the edit file")


def test_refuses_an_entry_without_a_sha256(record, capsys):
    path, _, listed, _ = record

    def strip(d):
        for e in d["edits"]:
            if e["file"] == bc.EDIT_FILE:
                e["sha256"] = sw.SENTINELS["edit_name"]
    digest = rewrite(path, strip)
    refused(capsys, argv(path, digest, listed), "the record's entry for the edit file names no SHA-256")


def test_refuses_a_record_that_is_not_a_json_object(record, capsys, tmp_path):
    path = tmp_path / "list.json"
    digest = sw.write(path, b"[1, 2]")
    refused(capsys, argv(path, digest, "a" * 64), "the record is not a JSON object")
    digest = sw.write(path, b"{" + sw.SENTINELS["unit"].encode())
    refused(capsys, argv(path, digest, "a" * 64), "the record is not JSON")
