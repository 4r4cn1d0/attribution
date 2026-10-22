"""Back up the main checkout's tmp/ to a PRIVATE DRAFT GitHub release, then move the entries the next steps do not
need to the Trash (the user, 22 Oct, GI VI chat: "just put it all on github whatever is needed for the paper but not
locally right now everything").

    python3.11 -B backup_tmp.py prepare      # classify, scan for secrets, pack one .tar.gz per tmp/ entry (split > 1.9 GB)
    python3.11 -B backup_tmp.py upload       # privacy check, draft create, upload each asset with retries (resumable)
    python3.11 -B backup_tmp.py verify       # download every asset back, one at a time, and compare SHA-256
    python3.11 -B backup_tmp.py trash        # move the verified "trash" entries to ~/.Trash/attribution-tmp-20261022/
    python3.11 -B backup_tmp.py clean-stage  # delete the local tar files once every asset is verified

Rules: the repository must be private at every step; the release stays a draft; a file whose text matches a key or token
pattern (the kit's secret_scan) or holds the exact value of a secret in ~/.config/attribution/secrets.env is never
packed (its path and the pattern name are listed, never its text); ssh folders, key files and env files are never
packed; the venv (tmp/minimal-experiment-20261002/venv) is skipped (rebuilt from environment.lock). Nothing is deleted:
"trash" moves entries to the Trash only after their assets are verified, and only entries classified "trash"; the
user empties the Trash. Entries other sessions own (the GPT lead's side paper and grants) are backed up and left in
place. gh runs without RunPod or Hugging Face variables.
"""
import datetime as dt, fnmatch, hashlib, json, os, pathlib, shutil, sys, tarfile, tempfile, time

sys.dont_write_bytecode = True
ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution")
TMP = ROOT / "tmp"
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tmp/gate-b-olmo"))
import backup_records_gateb as bk  # noqa: E402  (gh_env, gh, gh_json, release_absent, repo_privacy)
import secret_scan  # noqa: E402

TAG = "backup-2026-10-22-local-tmp"
TITLE = "Private backup 2026-10-22 (the Mac's tmp/: study units, records, kits, pilots; secrets excluded)"
STAGE = pathlib.Path(os.environ.get("BACKUP_STAGE", "/private/tmp/claude-501/attribution-backup-stage-20261022"))
STATE, MAN, SUMS, NOTES, VER = (HERE / n for n in ("state.json", "manifest.json", "SHA256SUMS", "README.md",
                                                    "upload-verification.json"))
TRASH = pathlib.Path.home() / ".Trash" / "attribution-tmp-20261022"
PART = 1_900_000_000
RETRIES = 6

# Needed by the next steps, or read by code and tests (git grep of tmp/ paths in experiments, scripts, runkit, pilot;
# the W1-18 units found by their pinned COMPLETE.json hashes; the O-ext source; the lead's records and workspaces).
KEEP = {"claude-workspaces", "claude-handoffs", "family-probe-budget.lock", "family-probe-judge", "family-probe-olmo2-1b",
        "family-probe-olmo2-1b-bt", "family-probe-olmo2-1b-g", "family-probe-olmo2-1b-g-r16",
        "family-probe-olmo2-1b-g-seed1102", "family-probe-olmo2-1b-g-seed1103", "family-probe-olmo2-1b-gateA-1102",
        "family-probe-olmo2-1b-gateA-1103", "family-probe-sp-olmo2-1b-bt-seed1102", "family-probe-sp-olmo2-1b-bt-seed1103",
        "backup-stage-olmo2-1b-recipe-g", "gate-a-common-recipe", "gate-b-anchors", "gate-b-d14-rereview", "gate-b-olmo",
        "gate-b-sealed", "gi-v-granite-converter", "gi-v-steps-4-9", "gi-vi-stage1", "judge-models", "judge-pod",
        "kill-test-7b-check", "kill-test-gateA-b", "kt-prepared", "mechanism-recipes", "minimal-experiment-20261002",
        "oext-phtest-20261017", "sp-repr", "study-v2-20261002", "study-v2-20261004", "cost-ledger"}
# Owned by other sessions (the GPT lead: side paper, grants; the Side Project chat): backed up, never moved.
OTHER = ["cause-study-*", "causal-followup-*", "family-probe-cause-*", "family-probe-causal2-*", "family-probe-sp-*",
         "judge-pod-sp-*", "judge-pod-side-*", "side-*", "sp-*", "bluedot-*", "grant-*", "anonymous-*"]
SKIP_DIRS = {"__pycache__", ".pytest_cache", "ssh", ".ssh"}
SKIP_FILES = ["id_rsa*", "id_ed25519*", "*.pem", "*.key", "known_hosts", "authorized_keys", "*.env", "secrets*",
              "credentials*", ".DS_Store"]
BINARY = (".safetensors", ".bin", ".pt", ".pth", ".npy", ".npz", ".gguf")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def log(**f):
    print(json.dumps({"utc": now(), **f}), flush=True)


def sha(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def load(p, default):
    return json.loads(p.read_text()) if p.exists() else default


def secret_values() -> list[str]:
    vals = []
    for line in (pathlib.Path.home() / ".config/attribution/secrets.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            v = line.split("=", 1)[1].strip().strip('"').strip("'")
            if len(v) >= 16:
                vals.append(v)
    return vals


def classify(name: str) -> str:
    if name in KEEP:
        return "keep"
    if any(fnmatch.fnmatch(name, pat) for pat in OTHER):
        return "other_owner"
    return "trash"


def skipped(entry: pathlib.Path, rel: pathlib.PurePath) -> bool:
    if any(part in SKIP_DIRS for part in rel.parts):
        return True
    return entry.name == "minimal-experiment-20261002" and rel.parts[1:2] == ("venv",)


def members(entry: pathlib.Path, values: list[str]):
    """(path, arcname) for every file to pack, and the excluded files with their reason (never their text)."""
    keep, excluded = [], []
    paths = [entry] if entry.is_file() else sorted(entry.rglob("*"))
    for p in paths:
        rel = p.relative_to(TMP)
        if skipped(entry, rel) or p.is_symlink() or not p.is_file():
            continue
        if any(fnmatch.fnmatch(p.name, pat) for pat in SKIP_FILES):
            excluded.append({"path": str(rel), "reason": "key, env or secrets file name"})
            continue
        if not p.name.endswith(BINARY):
            text = p.read_bytes().decode("utf-8", "ignore")
            hits = secret_scan.scan_text(text) + (["value of a secrets.env entry"] if any(v in text for v in values) else [])
            if hits:
                excluded.append({"path": str(rel), "reason": "matches " + ", ".join(sorted(set(hits)))})
                continue
        keep.append((p, str(rel)))
    return keep, excluded


def prepare() -> None:
    STAGE.mkdir(parents=True, exist_ok=True)
    values = secret_values()
    entries, total = [], 0
    for entry in sorted(TMP.iterdir()):
        if entry.name == ".DS_Store":
            continue
        files, excluded = members(entry, values)
        base = f"tmp--{entry.name}.tar.gz"
        tarpath = STAGE / base
        with tarfile.open(tarpath, "w:gz", compresslevel=1) as tf:
            for p, arc in files:
                tf.add(p, arcname=arc, recursive=False)
        size = tarpath.stat().st_size
        whole = sha(tarpath)
        assets = []
        if size > PART:
            with open(tarpath, "rb") as fh:
                i = 0
                while chunk := fh.read(PART):
                    part = STAGE / f"{base}.part{i:02d}"
                    part.write_bytes(chunk)
                    assets.append({"asset": part.name, "bytes": len(chunk), "sha256": sha(part)})
                    i += 1
            tarpath.unlink()
        else:
            assets.append({"asset": base, "bytes": size, "sha256": whole})
        raw = sum(p.stat().st_size for p, _ in files)
        entries.append({"entry": entry.name, "class": classify(entry.name), "files": len(files), "raw_bytes": raw,
                        "tar_sha256": whole, "assets": assets, "excluded": excluded})
        total += sum(a["bytes"] for a in assets)
        log(event="packed", entry=entry.name, cls=classify(entry.name), files=len(files), assets=len(assets),
            excluded=len(excluded))
    MAN.write_text(json.dumps({"release": TAG, "draft": True, "repo_must_be_private": True, "created_utc": now(),
                               "kind": "private research backup of the Mac's tmp/ (secrets excluded; the venv skipped)",
                               "entries": entries, "asset_bytes": total}, indent=1, sort_keys=True) + "\n")
    SUMS.write_text("".join(f"{a['sha256']}  {a['asset']}\n" for e in entries for a in e["assets"]))
    n_assets = sum(len(e["assets"]) for e in entries)
    NOTES.write_text(f"# {TITLE}\n\nPrivate draft release. {len(entries)} tmp/ entries in {n_assets} assets, "
                     f"{total} bytes ({total / 1024 ** 3:.2f} GiB). Each asset is `tmp--<entry>.tar.gz` (a `.partNN` "
                     "suffix splits one above 1.9 GB; join the parts in order with cat). Files matching a key or token "
                     "pattern, key and env files, and the venv are not included; manifest.json lists every excluded "
                     "path with its reason. Restore: download, check SHA256SUMS, `tar -xzf` from the repository root.\n")
    log(event="prepared", entries=len(entries), assets=n_assets, bytes=total,
        excluded=sum(len(e["excluded"]) for e in entries))


def privacy(env, point):
    p = bk.repo_privacy(env)
    log(event="privacy", point=point, **p)
    if not p["is_private"]:
        raise SystemExit(f"{point}: the repository is not reported private; stop")
    return p


def release_info(env) -> dict:
    return bk.gh_json(["release", "view", TAG, "--json", "isDraft,url,assets"], env) or {}


def upload() -> None:
    env = bk.gh_env()
    privacy(env, "before upload")
    man, state = load(MAN, None), load(STATE, {"uploaded": [], "verified": {}})
    if man is None:
        raise SystemExit("run prepare first")
    info = release_info(env)
    if not info:
        bk.release_absent(TAG, env)
        p = bk.gh(["release", "create", TAG, "--draft", "--title", TITLE, "--notes-file", str(NOTES), str(MAN), str(SUMS)], env)
        log(event="release-create", exit=p.returncode)
        if p.returncode != 0:
            raise SystemExit("gh release create failed")
        info = release_info(env)
    if info.get("isDraft") is not True:
        raise SystemExit("the release is not a draft: stop")
    for e in man["entries"]:
        for a in e["assets"]:
            if a["asset"] in state["uploaded"]:
                continue
            for attempt in range(1, RETRIES + 1):
                p = bk.gh(["release", "upload", TAG, str(STAGE / a["asset"]), "--clobber"], env)
                log(event="upload", asset=a["asset"], attempt=attempt, exit=p.returncode)
                if p.returncode == 0:
                    state["uploaded"].append(a["asset"])
                    STATE.write_text(json.dumps(state, indent=1) + "\n")
                    break
                time.sleep(10 * attempt)
            else:
                raise SystemExit(f"upload failed after {RETRIES} attempts: {a['asset']}")
    privacy(env, "after upload")
    log(event="after-upload", is_draft=release_info(env).get("isDraft"), uploaded=len(state["uploaded"]))


def verify() -> None:
    env = bk.gh_env()
    p0 = privacy(env, "before verify")
    man, state = load(MAN, None), load(STATE, {"uploaded": [], "verified": {}})
    for e in man["entries"]:
        for a in e["assets"]:
            if state["verified"].get(a["asset"]) == a["sha256"]:
                continue
            with tempfile.TemporaryDirectory(dir=STAGE.parent) as d:
                for attempt in range(1, RETRIES + 1):
                    p = bk.gh(["release", "download", TAG, "--pattern", a["asset"], "--dir", d, "--clobber"], env)
                    if p.returncode == 0:
                        break
                    time.sleep(10 * attempt)
                got = pathlib.Path(d) / a["asset"]
                ok = got.exists() and sha(got) == a["sha256"]
            log(event="verify", asset=a["asset"], ok=ok)
            if ok:
                state["verified"][a["asset"]] = a["sha256"]
                STATE.write_text(json.dumps(state, indent=1) + "\n")
    info = release_info(env)
    n = sum(len(e["assets"]) for e in man["entries"])
    out = {"release": TAG, "url": info.get("url"), "release_is_draft": info.get("isDraft") is True,
           "repo_is_private": p0["is_private"], "assets": n, "verified": len(state["verified"]),
           "download_back_hashes_ok": len(state["verified"]) == n, "checked_utc": now()}
    VER.write_text(json.dumps(out, indent=1) + "\n")
    log(event="verified", **out)


def trash() -> None:
    man, state, ver = load(MAN, None), load(STATE, {}), load(VER, {})
    if not (ver.get("download_back_hashes_ok") and ver.get("release_is_draft") and ver.get("repo_is_private")):
        raise SystemExit("the release is not fully verified: nothing moved")
    TRASH.mkdir(parents=True, exist_ok=True)
    moved = []
    for e in man["entries"]:
        if e["class"] != "trash" or any(state["verified"].get(a["asset"]) != a["sha256"] for a in e["assets"]):
            continue
        src = TMP / e["entry"]
        if src.exists():
            shutil.move(str(src), str(TRASH / e["entry"]))
            moved.append(e["entry"])
    (HERE / "trashed.json").write_text(json.dumps({"moved_utc": now(), "to": str(TRASH), "entries": moved}, indent=1) + "\n")
    log(event="trashed", entries=len(moved))


def clean_stage() -> None:
    """Delete the local tar files once every asset is verified (memory: remove tar files after use and backup)."""
    if load(VER, {}).get("download_back_hashes_ok"):
        shutil.rmtree(STAGE, ignore_errors=True)
        log(event="stage-removed", path=str(STAGE))


if __name__ == "__main__":
    {"prepare": prepare, "upload": upload, "verify": verify, "trash": trash, "clean-stage": clean_stage}[sys.argv[1]]()
