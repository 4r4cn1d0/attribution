"""Fetch the pinned tokenizer files of one family into the Mac's HF cache, for the Mac data preparation (brief Item 5b;
administrative; the lead runs it with the user's download approval).

    python3.11 fetch_tokenizers_mac.py olmo2                       open repository, token=False
    python3.11 fetch_tokenizers_mac.py olmo3                       open repository, token=False: the six tokenizer and
                                                                   template files plus config.json of OLMo 3 (fetched
                                                                   1 Nov 2026 with the user's yes; the pins are the
                                                                   receipt's blob ids, tokenizer-receipt-olmo3.json)
    HF_TOKEN=... python3.11 fetch_tokenizers_mac.py llama3 [--token-env NAME]
                                                                   gated repository; the token is read once from NAME

snapshot_download(allow_patterns=[exact names]) into the normal HF cache, so that the engine's load_tokenizer finds the
pinned snapshot. Each file's git blob SHA-1 must equal its pin: either the SHA-1 of the file itself, or (a file kept in
Git LFS, whose pin is its pointer's blob) the pointer blob that the Hub lists for that path, with the file's SHA-256
equal to the LFS SHA-256 the Hub lists. A .safetensors file in the snapshot folder refuses. Writes
tokenizer-receipt-FAMILY.json: repository, revision, files, sizes, oids, how each oid was checked and token_used. Never
the token, its length or its source variable's value. Review fix 8: HF_ENDPOINT must be unset or
https://huggingface.co; every Hub call passes that endpoint explicitly and the receipt records it.
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys

os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
HERE = pathlib.Path(__file__).resolve().parent
ENDPOINT = "https://huggingface.co"
TOKENIZER_FILES = ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]
FAMILIES = {
    "olmo2": {"repo_id": "allenai/OLMo-2-0425-1B-Instruct", "revision": "48d788eca847d4d7548f375ad03d3c9312f6139e",
              "gated": False,
              "oids": {"tokenizer.json": "5fe172127988c3709a49d8d2ce20e11bb266cd57",
                       "tokenizer_config.json": "6a68ef73052b644e4a32208ae0114236db221028",
                       "special_tokens_map.json": "9d133a8f4995ff315a8a3e68dbba03409d214a8e",
                       "vocab.json": "51135344eec01a62fc4deaca39c72ac08f5b9709",
                       "merges.txt": "354558edcdbd64ca7abd407b8be3d5d09d39d781"}},
    "llama3": {"repo_id": "meta-llama/Llama-3.1-8B-Instruct", "revision": "0e9e39f249a16976918f6564b8830bc894c89659",
               "gated": True,
               "oids": {"tokenizer.json": "5cc5f00a5b203e90a27a3bd60d1ec393b07971e8",
                        "tokenizer_config.json": "db88166e2bc4c799fd5d1ae643b75e84d03ee70e",
                        "special_tokens_map.json": "02ee80b6196926a5ad790a004d9efd6ab1ba6542"}},
    # OLMo 3 7B Instruct (blocker B2): the template lives in chat_template.jinja; config.json is for the LoRA count.
    # Blob ids from .ai/inputs/stage1-post-w1-20261023/olmo3/tokenizer-receipt-olmo3.json (each equal to MC §5's).
    "olmo3": {"repo_id": "allenai/Olmo-3-7B-Instruct", "revision": "6e5971d9eba42665f5bd5a0fcf047f299ce1dccc",
              "gated": False,
              "oids": {"tokenizer.json": "54b3f7c465454c7878d6e955e44064d23c5a4052",
                       "tokenizer_config.json": "277b816675b12d22c3ca0e2b4af1b9dc88e30043",
                       "special_tokens_map.json": "9d133a8f4995ff315a8a3e68dbba03409d214a8e",
                       "vocab.json": "9c2954b1c94c5267dc84a5d0214efbc79ff8c3bd",
                       "merges.txt": "354558edcdbd64ca7abd407b8be3d5d09d39d781",
                       "chat_template.jinja": "a21396285102846aa0787dd598623e7b8dbb2b67",
                       "config.json": "9c118c14e7871ec96335dc859995b4ef554bb097"}},
}


def snapshot_download(**kwargs):             # replaced by a fake in tests
    from huggingface_hub import snapshot_download as real
    return real(**kwargs)


def paths_info(repo_id: str, revision: str, paths: list[str], token) -> dict:
    """{path: {"blob_id", "lfs_sha256" or None}} from the Hub (replaced by a fake in tests)."""
    from huggingface_hub import HfApi
    out = {}
    for entry in HfApi(endpoint=ENDPOINT).get_paths_info(repo_id, paths, revision=revision, token=token):
        out[entry.path] = {"blob_id": entry.blob_id, "lfs_sha256": entry.lfs.sha256 if entry.lfs else None}
    return out


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def check_files(folder: pathlib.Path, oids: dict, lookup) -> dict:
    """Every pinned file is present and equals its pin; no .safetensors file is present. lookup() is called only when
    some file's own SHA-1 differs from its pin (an LFS file)."""
    if any(folder.rglob("*.safetensors")):
        raise SystemExit("a .safetensors file is in the tokenizer snapshot")
    files, info = {}, None
    for name, pin in sorted(oids.items()):
        path = folder / name
        if not path.is_file():
            raise SystemExit(f"{name}: missing from the snapshot")
        data = path.read_bytes()
        record = {"bytes": len(data), "oid": pin}
        if git_blob_sha1(data) == pin:
            record["oid_checked"] = "file"
        else:
            info = info if info is not None else lookup()
            hub = info.get(name) or {}
            if hub.get("blob_id") != pin or not hub.get("lfs_sha256") or hub["lfs_sha256"] != hashlib.sha256(data).hexdigest():
                raise SystemExit(f"{name}: the file differs from its pinned oid")
            record["oid_checked"] = "lfs-pointer"
            record["sha256"] = hub["lfs_sha256"]
        files[name] = record
    return files


def main(argv=None, env=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("family", choices=sorted(FAMILIES))
    ap.add_argument("--token-env", default="HF_TOKEN")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    env = os.environ if env is None else env
    if env.get("HF_ENDPOINT") not in (None, "", ENDPOINT):          # review fix 8: before any Hub call
        raise SystemExit("HF_ENDPOINT points elsewhere than https://huggingface.co: refusing to send any request")
    spec = FAMILIES[a.family]
    token = False
    if spec["gated"]:
        token = env.get(a.token_env, "").strip()
        if not token:
            raise SystemExit(f"{a.token_env} is not set: the {a.family} tokenizer is gated")
    names = sorted(spec["oids"])
    receipt = {"kind": "pinned tokenizer files for the Mac preparation", "ok": False, "family": a.family,
               "repo_id": spec["repo_id"], "revision": spec["revision"], "token_used": bool(spec["gated"]),
               "endpoint": ENDPOINT}
    out = pathlib.Path(a.out) if a.out else HERE / f"tokenizer-receipt-{a.family}.json"
    try:
        folder = pathlib.Path(snapshot_download(repo_id=spec["repo_id"], revision=spec["revision"],
                                                allow_patterns=names, token=token, endpoint=ENDPOINT))
        receipt["files"] = check_files(folder, spec["oids"],
                                       lambda: paths_info(spec["repo_id"], spec["revision"], names, token))
        receipt["ok"] = True
    finally:
        token = None
        out.write_text(json.dumps(receipt, indent=1) + "\n")
    print(json.dumps({"ok": True, "family": a.family, "files": len(receipt["files"]), "token_used": receipt["token_used"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
