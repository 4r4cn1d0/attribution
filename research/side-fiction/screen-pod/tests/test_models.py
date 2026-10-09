"""The three pinned snapshots: the pins against the Mac's copies and the probe pods' receipts, the snapshot check, and
the download's refusals (a fake snapshot_download; no network)."""
from __future__ import annotations

import hashlib
import json
import pathlib

import pytest
from conftest import P
from common import Refusal
import screen_models as M


def test_granite_pins_equal_the_mac_copies():
    tok = P.ROOT / "tmp/judge-models/granite-guardian-3.3-8b-tokenizer"
    if not tok.is_dir():
        pytest.skip("the Mac's Granite tokenizer folder is absent")
    found = {p.name: (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()) for p in tok.iterdir()
             if p.is_file()}
    assert found == P.GRANITE_TOK_FILES
    meta = P.ROOT / "tmp/judge-models/.cache/huggingface/download/granite-guardian-3.3-8b-Q4_K_M.gguf.metadata"
    lines = meta.read_text().splitlines()
    assert lines[0] == P.GRANITE_GGUF_REVISION and lines[1] == P.GRANITE_GGUF_SHA256       # commit, LFS etag
    assert (P.ROOT / "tmp/judge-models" / P.GRANITE_GGUF_FILE).stat().st_size == P.GRANITE_GGUF_BYTES
    for f in (tok / ".cache/huggingface/download").glob("*.metadata"):
        assert f.read_text().splitlines()[0] == P.GRANITE_TOK_REVISION
    from common import GRANITE_GGUF_SHA256
    assert GRANITE_GGUF_SHA256 == P.GRANITE_GGUF_SHA256


def test_qwen_pins_equal_the_probe_receipts_and_the_recipe():
    receipts = sorted(P.ROOT.glob("tmp/family-probe-*/retrieved/*/tree/model-download-receipt.json"))
    if not receipts:
        pytest.skip("no probe receipt on this machine")
    for r in receipts[:5]:
        guard = json.loads(r.read_bytes())["models"]["guard"]
        assert (guard["repo_id"], guard["revision"]) == (P.QWEN_REPO, P.QWEN_REVISION)
        assert {k: (v["bytes"], v["sha256"]) for k, v in guard["files"].items()} == P.QWEN_FILES
    recipe = json.loads((P.ROOT / P.RECIPE_REL).read_bytes())
    assert hashlib.sha256((P.ROOT / P.RECIPE_REL).read_bytes()).hexdigest() == P.RECIPE_SHA256
    assert recipe["guard"] == P.QWEN_GUARD_SPEC and recipe["model"]["device"] == "cuda"
    import guard_screen as GS
    assert GS.load_recipe(P.ROOT)["guard"]["revision"] == P.QWEN_REVISION


def _fake_snapshot(hub: pathlib.Path, name: str, extra=None, skip=None, corrupt=None) -> None:
    folder = M.snapshot_dir(name, hub)
    folder.mkdir(parents=True, exist_ok=True)
    for rel in M.SNAPSHOTS[name][3]:
        if rel == skip:
            continue
        (folder / rel).write_bytes(b"x")
    if extra:
        (folder / extra).write_bytes(b"y")
    if corrupt:
        (folder / corrupt).write_bytes(b"zz")


def test_verify_snapshot_refuses_missing_extra_and_changed_files(tmp_path, monkeypatch):
    pins = {"a.json": (1, hashlib.sha256(b"x").hexdigest()), "b.txt": (1, hashlib.sha256(b"x").hexdigest())}
    monkeypatch.setitem(M.SNAPSHOTS, "granite_tokenizer", (P.GRANITE_TOK_REPO, P.GRANITE_TOK_REVISION, tuple(pins),
                                                          pins))
    _fake_snapshot(tmp_path, "granite_tokenizer")
    assert M.verify_snapshot("granite_tokenizer", tmp_path) == {k: v[1] for k, v in pins.items()}
    _fake_snapshot(tmp_path, "granite_tokenizer", extra="c.bin")
    with pytest.raises(Refusal, match="extra"):
        M.verify_snapshot("granite_tokenizer", tmp_path)
    (M.snapshot_dir("granite_tokenizer", tmp_path) / "c.bin").unlink()
    _fake_snapshot(tmp_path, "granite_tokenizer", corrupt="b.txt")
    with pytest.raises(Refusal, match="bytes"):
        M.verify_snapshot("granite_tokenizer", tmp_path)
    with pytest.raises(Refusal, match="missing"):
        M.verify_snapshot("qwen3guard", tmp_path)


def test_download_refuses_tokens_and_offline_and_checks_every_file(tmp_path, monkeypatch):
    calls = []

    def fake_snapshot_download(**kw):
        calls.append(kw)
        name = next(n for n, s in M.SNAPSHOTS.items() if s[0] == kw["repo_id"])
        _fake_snapshot(pathlib.Path(kw["cache_dir"]), name)
        return str(M.snapshot_dir(name, pathlib.Path(kw["cache_dir"])))
    with pytest.raises(Refusal, match="HF_TOKEN"):
        M.download(fake_snapshot_download, {"HF_TOKEN": "x"}, tmp_path)
    with pytest.raises(Refusal, match="HF_HUB_OFFLINE"):
        M.download(fake_snapshot_download, {"HF_HUB_OFFLINE": "1"}, tmp_path)
    monkeypatch.setattr(M, "MIN_FREE_BYTES", 0)
    with pytest.raises(Refusal):                                   # the fake files are not the pinned bytes
        M.download(fake_snapshot_download, {}, tmp_path)
    assert calls[0] == {"repo_id": P.GRANITE_GGUF_REPO, "revision": P.GRANITE_GGUF_REVISION,
                        "allow_patterns": [P.GRANITE_GGUF_FILE], "token": False, "cache_dir": str(tmp_path)}
    monkeypatch.setattr(M, "verify_snapshot", lambda name, hub=None: {"ok": name})
    got = M.download(fake_snapshot_download, {}, tmp_path)
    assert set(got) == {"granite_gguf", "granite_tokenizer", "qwen3guard"}
    assert [c["repo_id"] for c in calls[-3:]] == [P.GRANITE_GGUF_REPO, P.GRANITE_TOK_REPO, P.QWEN_REPO]
    assert calls[-1]["allow_patterns"] == list(P.QWEN_PATTERNS) and all(c["token"] is False for c in calls)
