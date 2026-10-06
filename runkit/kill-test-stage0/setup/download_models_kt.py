"""Explicit public downloads of the pinned models of kill-test Stage 0; no credentials.

    venv/bin/python download_models_kt.py

The policy is the Instruct snapshot with its weights (its own tokenizer is the audit tokenizer); the guard is the
study's judge. No separate audit tokenizer and no rewrite generator.
"""
import hashlib, json, pathlib, time
from huggingface_hub import snapshot_download

root = pathlib.Path("/workspace/attribution-headroom"); start = time.monotonic()
receipt = {"kind": "public pinned model downloads and content verification", "models": {}}
WEIGHTS = ["*.json", "*.safetensors", "merges.txt", "vocab.json", "tokenizer*", "LICENSE", "README.md"]
models = [("policy", "Qwen/Qwen2.5-1.5B-Instruct", "989aa7980e4cf806f80c7fef2b1adb7bc71aa306", WEIGHTS),
          ("guard", "Qwen/Qwen3Guard-Gen-4B", "6ec42827da0c1ff11e7a49dc269d2e810d27e108", WEIGHTS)]
for name, repo, revision, patterns in models:
    folder = pathlib.Path(snapshot_download(repo_id=repo, revision=revision, token=False, allow_patterns=patterns))
    files = {}
    for p in sorted(folder.rglob("*")):
        if not p.is_file():
            continue
        sha = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
                sha.update(chunk)
        actual = sha.hexdigest(); blob = p.resolve().name
        if p.suffix == ".safetensors":
            assert len(blob) == 64 and actual == blob, (p.name, "LFS SHA mismatch")
        files[str(p.relative_to(folder))] = {"sha256": actual, "blob": blob, "bytes": p.stat().st_size}
    assert any(k.endswith(".safetensors") for k in files), f"{name}: no weights were fetched"
    receipt["models"][name] = {"repo_id": repo, "revision": revision, "snapshot": str(folder), "files": files}
    receipt["elapsed_s"] = time.monotonic() - start
    (root / "model-download-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"model": name, "file_count": len(files), "bytes": sum(f["bytes"] for f in files.values()),
                      "elapsed_s": receipt["elapsed_s"]}), flush=True)
