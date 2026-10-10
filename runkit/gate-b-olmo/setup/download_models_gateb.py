"""Pinned model downloads for one Gate B host (runs on the pod, in the run folder; copied from
runkit/family-probe/setup/download_models_probe.py). Gate B downloads OLMo-2-0425-1B-Instruct and Qwen3Guard-Gen-4B,
both open repositories: the bootstrap runs the open download only; the gated path is kept unchanged and unused.

    venv/bin/python download_models_gateb.py               the open repositories (the bootstrap)
    venv/bin/python download_models_gateb.py --dry-run     print the plan (repository, revision, patterns, gated)

The plan comes from probe.json (packed by pack_setup.py). The open run never touches a gated repository and passes
token=False. The gated run keeps the token in memory only and passes it as ``token=`` to snapshot_download: it is
never written, printed, logged, put in an argument list or in the environment (HF_HUB_DISABLE_IMPLICIT_TOKEN=1).
Afterwards it asserts that ~/.cache/huggingface/token does not exist and that no token variable is set, scans the
non-blob files of the HF cache for token patterns (a count), checks every .safetensors file's SHA-256 against its blob
name and the policy's pins, and writes model-download-receipt.json or gated-download-receipt.json (never the token).
Review fix 8: the Hub endpoint is pinned. HF_ENDPOINT must be unset or https://huggingface.co (checked before
huggingface_hub is imported), every call passes endpoint= explicitly, and the receipt records the endpoint.
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys

os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
TOKEN_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
ENDPOINT = "https://huggingface.co"


def check_endpoint(environ=None) -> str:
    """The token may only go to the Hub itself (review fix 8)."""
    value = (environ if environ is not None else os.environ).get("HF_ENDPOINT")
    if value not in (None, "", ENDPOINT):
        raise SystemExit("HF_ENDPOINT points elsewhere than https://huggingface.co: refusing to send any request")
    return ENDPOINT
PATTERN = None                               # compiled at use: the HF token pattern of secret_scan.PATTERNS


def snapshot_download(**kwargs):             # replaced by a fake in tests
    from huggingface_hub import snapshot_download as real
    return real(**kwargs)


def hf_cache() -> pathlib.Path:
    return pathlib.Path(os.environ.get("HF_HUB_CACHE") or pathlib.Path.home() / ".cache" / "huggingface" / "hub")


def token_file() -> pathlib.Path:
    return pathlib.Path.home() / ".cache" / "huggingface" / "token"


def no_token_left() -> None:
    present = [name for name in TOKEN_ENV_NAMES if os.environ.get(name)]
    if present:
        raise SystemExit(f"a token variable is set: {present}")
    if token_file().exists():
        raise SystemExit("~/.cache/huggingface/token exists")


def cache_pattern_count() -> int:
    import re
    pattern = re.compile(r"hf_[A-Za-z0-9]{30,}")
    count = 0
    for path in hf_cache().rglob("*") if hf_cache().exists() else []:
        if path.is_file() and not path.is_symlink() and "blobs" not in path.parts:
            count += len(pattern.findall(path.read_bytes().decode("utf-8", "ignore")))
    return count


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(entries: list[dict], token) -> dict:
    """Fetch each entry; a gated entry needs a token, an open one never gets it."""
    models = {}
    for entry in entries:
        if entry["gated"] and token is None:
            raise SystemExit(f"{entry['repo_id']} is gated: only the --gated --token-stdin run downloads it")
        folder = pathlib.Path(snapshot_download(repo_id=entry["repo_id"], revision=entry["revision"],
                                                allow_patterns=list(entry["patterns"]), endpoint=ENDPOINT,
                                                token=token if entry["gated"] else False))
        files = {}
        for path in sorted(p for p in folder.rglob("*") if p.is_file()):
            actual, blob = sha256(path), path.resolve().name
            if path.suffix == ".safetensors" and not (len(blob) == 64 and actual == blob):
                raise SystemExit(f"{entry['repo_id']}: {path.name}: the SHA-256 differs from its blob name")
            files[str(path.relative_to(folder))] = {"sha256": actual, "bytes": path.stat().st_size}
        models[entry["role"]] = {"repo_id": entry["repo_id"], "revision": entry["revision"], "gated": entry["gated"],
                                 "snapshot": str(folder), "files": files}
    return models


def check_pins(models: dict, pins: list[str]) -> None:
    if "policy" not in models:
        return
    weights = sorted(f["sha256"] for name, f in models["policy"]["files"].items() if name.endswith(".safetensors"))
    if weights != sorted(pins):
        raise SystemExit("the policy's .safetensors files differ from the pinned SHA-256 values")


def main(argv=None, stdin=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gated", action="store_true")
    ap.add_argument("--token-stdin", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--probe-file", default="probe.json")
    a = ap.parse_args(argv)
    probe = json.loads(pathlib.Path(a.probe_file).read_text())
    if a.dry_run:
        print(json.dumps([{k: e[k] for k in ("role", "repo_id", "revision", "gated", "patterns")} for e in probe["plan"]], indent=1))
        return 0
    if a.gated != a.token_stdin:
        raise SystemExit("--gated and --token-stdin go together")
    endpoint = check_endpoint()
    no_token_left()
    token = None
    if a.gated:
        token = (stdin or sys.stdin).readline().strip()
        if not token:
            raise SystemExit("no token on stdin")
    entries = [e for e in probe["plan"] if e["gated"] == a.gated]
    receipt_name = "gated-download-receipt.json" if a.gated else "model-download-receipt.json"
    receipt = {"kind": "pinned model downloads and content verification", "ok": False, "gated": a.gated,
               "token_source": "stdin" if a.gated else None, "gated_repos": [e["repo_id"] for e in entries if e["gated"]],
               "endpoint": endpoint}
    try:
        models = download(entries, token)
        check_pins(models, probe["weight_pins"])
        receipt["models"] = models
    finally:
        token = None                                          # nothing below sees it
        no_token_left()
        receipt["cache_token_pattern_count"] = cache_pattern_count()
        pathlib.Path(receipt_name).write_text(json.dumps(receipt, indent=1) + "\n")
    if receipt["cache_token_pattern_count"]:
        raise SystemExit("a token pattern is in the HF cache's non-blob files")
    receipt["ok"] = True
    pathlib.Path(receipt_name).write_text(json.dumps(receipt, indent=1) + "\n")
    print(json.dumps({"ok": True, "gated": a.gated, "models": sorted(receipt["models"])}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
