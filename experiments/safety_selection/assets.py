"""Pinned public assets: explicit download helpers and identities (stdlib; huggingface_hub
only inside ``fetch_models``).

Nothing here runs implicitly: every download needs the explicit ``fetch`` command with
``--confirm-public-download``. Data files are fetched from pinned revisions and refused unless
their SHA-256 matches the data config. Model snapshots are fetched by pinned commit without
credentials (``token=False``: public repositories only) and limited to configuration,
tokenizer, license/card and safetensors files. ARC-Easy is published as parquet; this helper
fetches and hash-checks the parquet files but does not convert them (no parquet reader is a
dependency): the prepared data use the receipted JSONL conversion pinned by its own SHA-256.
"""

from __future__ import annotations

from pathlib import Path

from experiments.minimal_safety.plan import asset_status

from .common import sha256_bytes, write_atomic

__all__ = ["HF_DATASET_URL", "MODEL_PATTERNS", "TOKENIZER_FILES", "fetch_data", "fetch_models",
           "tokenizer_identity"]

HF_DATASET_URL = "https://huggingface.co/datasets/{repo_id}/resolve/{revision}/{path}"
MODEL_PATTERNS = ["*.json", "*.safetensors", "merges.txt", "vocab.json", "tokenizer*", "LICENSE",
                  "README.md"]
TOKENIZER_FILES = ("tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt",
                   "special_tokens_map.json", "added_tokens.json")


def _download(url: str) -> bytes:
    import urllib.request

    with urllib.request.urlopen(url, timeout=300) as response:  # noqa: S310 - pinned https URL
        return response.read()


def fetch_data(data_config: dict, out_dir: str | Path, confirm: bool) -> dict:
    """Download the pinned raw data files into ``out_dir`` (hash-checked)."""
    if not confirm:
        raise PermissionError("refusing to download without --confirm-public-download")
    src, out, written = data_config["sources"], Path(out_dir), {}
    wanted = [
        ("date_train", src["date_lm"], src["date_lm"]["train_file"], src["date_lm"]["train_sha256"]),
        ("date_ref", src["date_lm"], src["date_lm"]["ref_file"], src["date_lm"]["ref_sha256"]),
        ("toxicchat_test", src["toxicchat"], src["toxicchat"]["file"], src["toxicchat"]["sha256"]),
        ("arc_validation_parquet", src["arc_easy"], src["arc_easy"]["validation_parquet"],
         src["arc_easy"]["validation_parquet_sha256"]),
        ("arc_test_parquet", src["arc_easy"], src["arc_easy"]["test_parquet"],
         src["arc_easy"]["test_parquet_sha256"])]
    for name, spec, path, digest in wanted:
        url = HF_DATASET_URL.format(repo_id=spec["repo_id"], revision=spec["revision"], path=path)
        payload = _download(url)
        if sha256_bytes(payload) != digest:
            raise ValueError(f"{url}: downloaded bytes do not match the pinned sha256")
        target = out / f"{name}{Path(path).suffix}"
        write_atomic(target, payload)
        written[name] = {"url": url, "path": str(target), "sha256": digest}
    written["note"] = ("ARC-Easy prepare inputs are the receipted JSONL conversions pinned by "
                       "validation_jsonl_sha256/test_jsonl_sha256; parquet files are fetched for "
                       "provenance only")
    return written


def fetch_models(recipe: dict, which: list[str], confirm: bool) -> dict:
    """Download pinned public model snapshots into the Hugging Face cache, no credentials."""
    if not confirm:
        raise PermissionError("refusing to download without --confirm-public-download")
    from huggingface_hub import snapshot_download

    specs = {"policy": recipe["model"], "guard": recipe["guard"],
             "secondary_toxicity": recipe["secondary_toxicity"]}
    out = {}
    for name in which:
        spec = specs.get(name)
        if spec is None:
            raise ValueError(f"{name}: not configured in this recipe")
        snapshot_download(repo_id=spec["repo_id"], revision=spec["revision"],
                          allow_patterns=MODEL_PATTERNS, token=False)
        status = asset_status(spec["repo_id"], spec["revision"])
        if not status["present"] or not status["safetensors"]:
            raise FileNotFoundError(f"{spec['repo_id']}@{spec['revision']}: no safetensors after download")
        out[name] = {k: status[k] for k in ("repo_id", "revision", "snapshot", "safetensors")}
    return out


def tokenizer_identity(repo_id: str, revision: str) -> dict:
    """Pinned tokenizer files with their resolved blob names (content identity)."""
    status = asset_status(repo_id, revision)
    if not status["present"]:
        raise FileNotFoundError(f"{repo_id}@{revision}: no cached snapshot at {status['snapshot']}")
    files = [f for f in status["files"] if f["file"] in TOKENIZER_FILES]
    if not any(f["file"] == "tokenizer_config.json" for f in files):
        raise FileNotFoundError(f"{repo_id}@{revision}: tokenizer_config.json missing")
    return {"repo_id": repo_id, "revision": revision, "files": files}
