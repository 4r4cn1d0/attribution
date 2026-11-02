"""The shared helpers: reads that refuse a missing file, a folder or a symbolic link with a fixed message; the pin
check; the PATH:SHA256 form; the exclusive create; the command-line frame (a refusal's fixed message; any other
error's type only)."""

from __future__ import annotations

import os

import pytest
import synth_world as sw

from scripts.stage1_s1.stage1b_mac import common as co


def test_read_bytes_refuses_a_missing_file_a_folder_and_a_symbolic_link(tmp_path):
    target = tmp_path / "a.json"
    target.write_bytes(b"{}")
    assert co.read_bytes(target, "a file") == b"{}"
    with pytest.raises(co.Refusal, match="^a file is missing or not a regular file$"):
        co.read_bytes(tmp_path / "none.json", "a file")
    with pytest.raises(co.Refusal, match="^a file is missing or not a regular file$"):
        co.read_bytes(tmp_path, "a file")
    link = tmp_path / "link.json"
    os.symlink(target, link)
    with pytest.raises(co.Refusal, match="^a file is missing or not a regular file$"):
        co.read_bytes(link, "a file")


def test_read_pinned_refuses_a_mismatch_with_a_fixed_message(tmp_path):
    target = tmp_path / "a.json"
    target.write_bytes(sw.SENTINELS["unit"].encode())
    digest = co.sha256_bytes(target.read_bytes())
    assert co.read_pinned(target, digest, "a file") == target.read_bytes()
    for wrong in ("0" * 64, "not-hex", None):
        with pytest.raises(co.Refusal, match="^a file does not hash to its expected SHA-256$"):
            co.read_pinned(target, wrong, "a file")


def test_hashed_pair_and_json_object():
    path, digest = co.hashed_pair(f"/x/y:z.json:{'a' * 64}", "--l1")
    assert str(path) == "/x/y:z.json" and digest == "a" * 64
    for bad in ("no-hash", ":" + "a" * 64, "/x/y.json:" + "A" * 64, "/x/y.json:" + "a" * 63):
        with pytest.raises(co.Refusal, match="^--l1 is PATH:SHA256$"):
            co.hashed_pair(bad, "--l1")
    assert co.json_object(b'{"a": 1}', "a doc") == {"a": 1}
    with pytest.raises(co.Refusal, match="^a doc is not JSON$"):
        co.json_object(b"{" + sw.SENTINELS["leaf"].encode(), "a doc")
    with pytest.raises(co.Refusal, match="^a doc is not a JSON object$"):
        co.json_object(b"[1]", "a doc")
    # a repeated key in any object refuses (json.loads alone would keep the last value)
    with pytest.raises(co.Refusal, match="^a doc repeats a key$"):
        co.json_object(b'{"edits": [{"sha256": "a"}], "edits": [{"sha256": "b"}]}', "a doc")
    with pytest.raises(co.Refusal, match="^a doc repeats a key$"):
        co.json_object(b'{"x": {"k": 1, "k": 2}}', "a doc")


def test_write_exclusive_writes_once(tmp_path):
    target = tmp_path / "r.json"
    assert co.write_exclusive(target, b"first", "the record") == co.sha256_bytes(b"first")
    with pytest.raises(co.Refusal, match="^the record exists: it is written once$"):
        co.write_exclusive(target, b"second", "the record")
    assert target.read_bytes() == b"first"


def test_the_frame_prints_a_refusal_or_an_error_type_only(capsys):
    assert co.run_frame(lambda argv: 7, None) == 7
    assert co.run_frame(lambda argv: (_ for _ in ()).throw(co.Refusal("a fixed message")), None) == 2
    assert capsys.readouterr().err == "REFUSED: a fixed message\n"
    assert co.run_frame(lambda argv: (_ for _ in ()).throw(ValueError(sw.SENTINELS["cell"])), None) == 2
    err = capsys.readouterr().err
    assert err == "REFUSED: an unexpected ValueError (its message is withheld: it may hold a value)\n"
    assert not sw.sentinel_hits(err)


def test_module_hashes_cover_the_package():
    hashes = co.module_hashes()
    assert {"common.py", "construction_checks.py", "binding_check.py", "switch_check.py", "__init__.py"} <= set(hashes)
    assert all(co.is_hex64(v) for v in hashes.values())
    assert not any("plant" in name or "decoy" in name for name in hashes)
