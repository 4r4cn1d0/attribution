"""Fetch OLMo 3 7B Instruct's tokenizer files (and config.json) at the pinned revision into the Mac's HF cache, as
runkit/family-probe/fetch_tokenizers_mac.py does for olmo2 and llama3 (the user's yes, 1 Nov 2026: "Yes, go ahead").

    PY -I fetch_olmo3_tokenizer.py RECEIPT_OUT [--dry]

Open repository, no token. Pins come from a direct Hub API read (get_paths_info) at the revision and are compared with
the sizes and id prefixes the 17 Oct model check recorded (model-check.md section 5). Each downloaded file must equal
its Hub git blob id (or, for an LFS file, the LFS SHA-256). A .safetensors file in the snapshot refuses. The receipt
(exclusive create) holds repository, revision, endpoint, files, sizes, ids and how each id was checked.
"""
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys

os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
for name in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
    os.environ.pop(name, None)
if os.environ.get("HF_ENDPOINT", "https://huggingface.co") != "https://huggingface.co":
    raise SystemExit("HF_ENDPOINT must be unset or https://huggingface.co")
from huggingface_hub import HfApi, snapshot_download  # noqa: E402

ENDPOINT = "https://huggingface.co"
REPO = "allenai/Olmo-3-7B-Instruct"
REVISION = "6e5971d9eba42665f5bd5a0fcf047f299ce1dccc"
# model-check.md section 5 (17 Oct): sizes and the known blob-id prefixes
EXPECTED = {"tokenizer.json": (7137175, "54b3f7c4"), "vocab.json": (1611055, "9c2954b1"),
            "merges.txt": (916646, "354558ed"), "tokenizer_config.json": (4318, None),
            "chat_template.jinja": (2613, None), "special_tokens_map.json": (581, "9d133a8f")}
EXTRA = ["config.json"]                         # the LoRA count needs it (user item 4); metadata only
NAMES = sorted(EXPECTED) + EXTRA


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


out = pathlib.Path(sys.argv[1])
dry = "--dry" in sys.argv[2:]
if out.exists():
    raise SystemExit(f"{out} exists")
api = HfApi(endpoint=ENDPOINT)
info = api.model_info(REPO, revision=REVISION, token=False)
if info.sha != REVISION:
    raise SystemExit(f"the Hub resolves the revision to {info.sha}")
hub = {}
for entry in api.get_paths_info(REPO, NAMES, revision=REVISION, token=False):
    hub[entry.path] = {"blob_id": entry.blob_id, "size": entry.size,
                       "lfs_sha256": entry.lfs.sha256 if entry.lfs else None}
missing = [n for n in NAMES if n not in hub]
if missing:
    raise SystemExit(f"not on the Hub at the revision: {missing}")
for name, (size, prefix) in EXPECTED.items():
    if hub[name]["size"] != size:
        raise SystemExit(f"{name}: the Hub size {hub[name]['size']} differs from the model check's {size}")
    if prefix and not hub[name]["blob_id"].startswith(prefix):
        raise SystemExit(f"{name}: the Hub blob id {hub[name]['blob_id'][:8]} differs from the model check's {prefix}")
total = sum(hub[n]["size"] for n in NAMES)
print(json.dumps({"repo": REPO, "revision": REVISION, "files": len(NAMES), "bytes": total,
                  "hub": {n: [hub[n]["size"], hub[n]["blob_id"][:12], bool(hub[n]["lfs_sha256"])] for n in NAMES}}))
if dry:
    raise SystemExit(0)
folder = pathlib.Path(snapshot_download(repo_id=REPO, revision=REVISION, allow_patterns=NAMES, token=False,
                                        endpoint=ENDPOINT))
if any(folder.rglob("*.safetensors")):
    raise SystemExit("a .safetensors file is in the snapshot")
files = {}
for name in NAMES:
    data = (folder / name).read_bytes()
    rec = {"bytes": len(data), "blob_id": hub[name]["blob_id"], "sha256": hashlib.sha256(data).hexdigest()}
    if git_blob_sha1(data) == hub[name]["blob_id"]:
        rec["checked"] = "git blob sha1 of the file equals the Hub blob id"
    elif hub[name]["lfs_sha256"] and hashlib.sha256(data).hexdigest() == hub[name]["lfs_sha256"]:
        rec["checked"] = "sha256 of the file equals the Hub LFS sha256"
    else:
        raise SystemExit(f"{name}: the file differs from the Hub's ids")
    if len(data) != hub[name]["size"]:
        raise SystemExit(f"{name}: size differs")
    files[name] = rec
receipt = {"kind": "OLMo 3 tokenizer fetch receipt (Mac HF cache)", "version": 1, "repo_id": REPO,
           "revision": REVISION, "endpoint": ENDPOINT, "token_used": False,
           "snapshot_folder": str(folder).replace(str(pathlib.Path.home()), "~"),
           "files": files, "bytes_total": sum(f["bytes"] for f in files.values()),
           "approval": ".ai/inputs/stage1-post-w1-20261023/olmo3/user_yes_tokenizer_download_and_env_20261101.json",
           "fetched_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
with out.open("x") as handle:
    handle.write(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
print(json.dumps({"written": str(out), "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                  "files": {n: [f["bytes"], f["checked"].split(" ")[0]] for n, f in files.items()}}))
