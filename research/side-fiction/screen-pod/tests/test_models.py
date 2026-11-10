"""The screen's one pinned snapshot (Qwen3Guard; Granite's GGUF and tokenizer are the lead's): the pins against the
probe pods' receipts, the snapshot check, and the download's refusals (a fake snapshot_download; no network)."""
from __future__ import annotations

import hashlib
import json
import pathlib

import pytest
from conftest import P
from common import Refusal
import screen_models as M


def test_granite_is_no_longer_downloaded_here():
    """The lead's Granite job downloads and checks the GGUF; the bundle carries the Mac's tokenizer folder."""
    assert set(M.SNAPSHOTS) == {"qwen3guard"} and not hasattr(M, "granite_paths")


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
    monkeypatch.setitem(M.SNAPSHOTS, "qwen3guard", (P.QWEN_REPO, P.QWEN_REVISION, tuple(pins), pins))
    with pytest.raises(Refusal, match="missing"):
        M.verify_snapshot("qwen3guard", tmp_path)
    _fake_snapshot(tmp_path, "qwen3guard")
    assert M.verify_snapshot("qwen3guard", tmp_path) == {k: v[1] for k, v in pins.items()}
    _fake_snapshot(tmp_path, "qwen3guard", extra="c.bin")
    with pytest.raises(Refusal, match="extra"):
        M.verify_snapshot("qwen3guard", tmp_path)
    (M.snapshot_dir("qwen3guard", tmp_path) / "c.bin").unlink()
    _fake_snapshot(tmp_path, "qwen3guard", corrupt="b.txt")
    with pytest.raises(Refusal, match="bytes"):
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
    assert calls[0] == {"repo_id": P.QWEN_REPO, "revision": P.QWEN_REVISION, "allow_patterns": list(P.QWEN_PATTERNS),
                        "token": False, "cache_dir": str(tmp_path)}
    monkeypatch.setattr(M, "verify_snapshot", lambda name, hub=None: {"ok": name})
    got = M.download(fake_snapshot_download, {}, tmp_path)
    assert set(got) == {"qwen3guard"} and [c["repo_id"] for c in calls[-1:]] == [P.QWEN_REPO]
    assert all(c["token"] is False for c in calls)
