"""Explicit public downloads of the pinned models of the headroom positive control; no credentials.

    venv/bin/python download_models_hr.py [--with-generator]

The policy is the base model; the audit tokenizer (the instruct snapshot's tokenizer files only, no weights)
is the tokenizer prepared-v2 was audited with; the guard is the study's judge and row scorer; the generator
(Qwen2.5-7B-Instruct) is fetched only on the host that writes the rewrites.
"""
import argparse, hashlib, json, pathlib, time
from huggingface_hub import snapshot_download

ap = argparse.ArgumentParser(); ap.add_argument("--with-generator", action="store_true"); a = ap.parse_args()
root = pathlib.Path("/workspace/attribution-headroom"); start = time.monotonic()
receipt = {"kind": "public pinned model downloads and content verification", "models": {}}
WEIGHTS = ["*.json", "*.safetensors", "merges.txt", "vocab.json", "tokenizer*", "LICENSE", "README.md"]
TOKENIZER = ["*.json", "merges.txt", "vocab.json", "tokenizer*", "LICENSE", "README.md"]
models = [("policy", "Qwen/Qwen2.5-1.5B", "8faed761d45a263340a0528343f099c05c9a4323", WEIGHTS),
          ("audit_tokenizer", "Qwen/Qwen2.5-1.5B-Instruct", "989aa7980e4cf806f80c7fef2b1adb7bc71aa306", TOKENIZER),
          ("guard", "Qwen/Qwen3Guard-Gen-4B", "6ec42827da0c1ff11e7a49dc269d2e810d27e108", WEIGHTS)]
if a.with_generator:
    models.append(("generator", "Qwen/Qwen2.5-7B-Instruct", "a09a35458c702b33eeacc393d103063234e8bc28", WEIGHTS))
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
    if name == "audit_tokenizer":
        assert not any(k.endswith(".safetensors") for k in files), "the audit tokenizer must not fetch weights"
    receipt["models"][name] = {"repo_id": repo, "revision": revision, "snapshot": str(folder), "files": files}
    receipt["elapsed_s"] = time.monotonic() - start
    (root / "model-download-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"model": name, "file_count": len(files), "bytes": sum(f["bytes"] for f in files.values()),
                      "elapsed_s": receipt["elapsed_s"]}), flush=True)
