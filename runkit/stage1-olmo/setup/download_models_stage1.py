"""Pinned model downloads for one stage-1 host (runs on the pod, in the run folder; copied from
runkit/gate-b-olmo/setup/download_models_gateb.py, itself from runkit/family-probe/setup/download_models_probe.py).

Stage 1 (B15, brief §3 J17): with --with-base (a host that runs Safe LoRA) the base model allenai/OLMo-2-0425-1B is
downloaded too, at its full pinned commit a1847dff35000b4271fa70afc5db10fd29fedbdf, never "main" (every entry's
revision must be a 40-hex commit; "main" or a branch name refuses before any request), with its 12 file names as the
only patterns, and every downloaded file is checked against its pin (probes.BASE_FILES, packed into probe.json): the
set of files equals the 12 names; each size equals its pin; a git file's git blob id (SHA-1 of "blob SIZE\0" + bytes)
equals its pin; an LFS file's SHA-256 equals its LFS pin and its cached blob name. Any difference refuses, and the
receipt (model-download-receipt.json) records the base's snapshot, its files and "base_checked": true. Without
--with-base the base entry is skipped. The endpoint pin, token=False and the receipt are unchanged.
From the Gate B script: Gate B downloads OLMo-2-0425-1B-Instruct and Qwen3Guard-Gen-4B,
both open repositories: the bootstrap runs the open download only; the gated path is kept unchanged and unused.

    venv/bin/python download_models_stage1.py [--with-base]             the open repositories (the bootstrap)
    venv/bin/python download_models_stage1.py --dry-run [--with-base]   print the plan (repository, revision, patterns)

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


COMMIT_CHARS = set("0123456789abcdef")


def check_revisions(entries: list[dict]) -> None:
    """Every download names a full 40-hex commit: "main" or any branch or tag name refuses (J17: never main)."""
    for entry in entries:
        rev = entry.get("revision")
        if not (isinstance(rev, str) and len(rev) == 40 and not set(rev) - COMMIT_CHARS):
            raise SystemExit(f"{entry['repo_id']}: the revision must be a full commit, never {rev!r}")


def git_blob_id(path: pathlib.Path) -> str:
    """The git object id of a file stored in git: SHA-1 of "blob SIZE\0" followed by its bytes."""
    digest = hashlib.sha1(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_base(entry: dict, model: dict) -> None:
    """The base snapshot against its 12 file pins (module doc); a difference refuses."""
    pins = {f["rfilename"]: f for f in entry["files"]}
    folder = pathlib.Path(model["snapshot"])
    if folder.name != entry["revision"]:
        raise SystemExit("the base snapshot is not the pinned commit")
    if set(model["files"]) != set(pins):
        raise SystemExit(f"the base snapshot's files differ from the {len(pins)} pinned files")
    for name, pin in sorted(pins.items()):
        path, got = folder / name, model["files"][name]
        if got["bytes"] != pin["size"]:
            raise SystemExit(f"base {name}: its size differs from the pin")
        if pin["lfs_sha256"] is not None:
            if got["sha256"] != pin["lfs_sha256"] or path.resolve().name != pin["lfs_sha256"]:
                raise SystemExit(f"base {name}: its SHA-256 or blob differs from the LFS pin")
        elif git_blob_id(path) != pin["git_blob_id"]:
            raise SystemExit(f"base {name}: its git blob id differs from the pin")


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
    ap.add_argument("--with-base", action="store_true", help="also the base model (a Safe LoRA host)")
    a = ap.parse_args(argv)
    probe = json.loads(pathlib.Path(a.probe_file).read_text())
    plan = [e for e in probe["plan"] if e["role"] != "base" or a.with_base]
    check_revisions(plan)
    if a.dry_run:
        print(json.dumps([{k: e[k] for k in ("role", "repo_id", "revision", "gated", "patterns")} for e in plan], indent=1))
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
    entries = [e for e in plan if e["gated"] == a.gated]
    receipt_name = "gated-download-receipt.json" if a.gated else "model-download-receipt.json"
    receipt = {"kind": "pinned model downloads and content verification", "ok": False, "gated": a.gated,
               "token_source": "stdin" if a.gated else None, "gated_repos": [e["repo_id"] for e in entries if e["gated"]],
               "endpoint": endpoint}
    try:
        models = download(entries, token)
        check_pins(models, probe["weight_pins"])
        for entry in entries:
            if entry["role"] == "base":
                check_base(entry, models["base"])
                receipt["base_checked"] = True
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
