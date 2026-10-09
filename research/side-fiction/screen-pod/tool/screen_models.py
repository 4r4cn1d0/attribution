"""The screen's pinned Hub snapshot (Qwen3Guard-Gen-4B): where it sits on the pod, its download and its check.

Kept from the lead's partial build (9 October 2026); reviewed 10:27 UTC (clock checked). Stdlib only, except
`download`, which imports huggingface_hub (the guard venv's 0.36.2, as the judge pod's download). The snapshot sits in
the default Hub cache (~/.cache/huggingface/hub, on the container disk; screen_run.sh unsets HF_HOME, HF_HUB_CACHE and
XDG_CACHE_HOME), which is also where the engine's loaders look for Qwen3Guard (experiments.minimal_safety.plan
.snapshot_dir). The folder must hold exactly the pinned files with the pinned sizes and SHA-256 (symlinks to the
cache's blobs are followed); anything else refuses. The repository is public: no token is used or accepted.
Revised 9 October 2026 (17:11 UTC, clock checked): the Granite GGUF and tokenizer are no longer downloaded here. The
lead's Granite job downloads the GGUF (pod_job.py download, into /root/granite-gguf) and the bundle carries the Mac's
tokenizer folder (gate_b/granite-tokenizer), both checked by the lead's code (granite_pod.check_files).
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import screen_pins as P  # noqa: E402
from common import Refusal  # noqa: E402

HUB = pathlib.Path.home() / ".cache" / "huggingface" / "hub"      # replaced in tests
TOKEN_VARS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
OFFLINE_VARS = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
MIN_FREE_BYTES = 30 * 1024 ** 3        # 8.8 GB here, then the lead's 4.9 GB GGUF, CUDA build and venv, plus room
# name -> (repository, revision, allow_patterns, pinned files)
SNAPSHOTS = {
    "qwen3guard": (P.QWEN_REPO, P.QWEN_REVISION, P.QWEN_PATTERNS, P.QWEN_FILES),
}


def snapshot_dir(name: str, hub: pathlib.Path | None = None) -> pathlib.Path:
    repo, revision, _, _ = SNAPSHOTS[name]
    return pathlib.Path(HUB if hub is None else hub) / f"models--{repo.replace('/', '--')}" / "snapshots" / revision


def sha256_path(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


def verify_snapshot(name: str, hub: pathlib.Path | None = None) -> dict:
    """Refuses unless the snapshot folder holds exactly the pinned files (sizes and SHA-256). Returns {file: sha256}."""
    folder = snapshot_dir(name, hub)
    pins = SNAPSHOTS[name][3]
    if not folder.is_dir():
        raise Refusal(f"the {name} snapshot folder is missing")
    found = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())
    if found != sorted(pins):
        raise Refusal(f"the {name} snapshot holds {len(found)} files, not the {len(pins)} pinned ones; extra "
                      f"{sorted(set(found) - set(pins))[:5]}, missing {sorted(set(pins) - set(found))[:5]}")
    hashes = {}
    for rel, (size, digest) in sorted(pins.items()):
        path = folder / rel
        if path.stat().st_size != size:
            raise Refusal(f"{name}: {rel} is not {size} bytes")
        hashes[rel] = sha256_path(path)
        if hashes[rel] != digest:
            raise Refusal(f"{name}: {rel} has SHA-256 {hashes[rel][:16]}, not the pinned {digest[:16]}")
    return hashes


def download(snapshot_download=None, environ=None, hub: pathlib.Path | None = None) -> dict:
    """The pinned snapshot from the Hub without a token (the repository is public), then every file checked.
    Refuses when a token variable or an offline variable is set, or when the disk has too little room."""
    environ = os.environ if environ is None else environ
    for name in OFFLINE_VARS:
        if environ.get(name, "") not in ("", "0"):
            raise Refusal(f"{name} is set; the download step runs online")
    for name in TOKEN_VARS:
        if environ.get(name):
            raise Refusal(f"{name} is set; the screen's models are public and are downloaded without a token")
    hub = pathlib.Path(HUB if hub is None else hub)
    hub.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(hub).free
    if free < MIN_FREE_BYTES:
        raise Refusal(f"{free // 1024 ** 3} GiB free under the Hub cache; at least {MIN_FREE_BYTES // 1024 ** 3} needed")
    if snapshot_download is None:
        from huggingface_hub import snapshot_download
    out = {}
    for name, (repo, revision, patterns, _) in SNAPSHOTS.items():
        path = snapshot_download(repo_id=repo, revision=revision, allow_patterns=list(patterns), token=False,
                                 cache_dir=str(hub))
        if pathlib.Path(path).resolve() != snapshot_dir(name, hub).resolve():
            raise Refusal(f"the {name} snapshot landed elsewhere than its cache folder")
        out[name] = {"repo": repo, "revision": revision, "files": verify_snapshot(name, hub)}
    return out
