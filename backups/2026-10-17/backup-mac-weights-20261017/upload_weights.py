"""Back up the Mac-only model weights and states to a PRIVATE DRAFT GitHub release (the user's yes, relayed by FAQ, 17 Oct
IST; scope: this upload only). Lead: General Implementation VI.

    python3.11 -B upload_weights.py prepare      # hash, hard-link stage with flattened names, manifest, scans; no upload
    python3.11 -B upload_weights.py upload       # privacy check, draft create (small files), upload each asset with retries
    python3.11 -B upload_weights.py verify       # download each asset back ONE AT A TIME, compare SHA-256, delete the copy
    python3.11 -B upload_weights.py all

Sources: tmp/sp-repr/out/*/*/states/e1/adapter.safetensors (20) and tmp/cause-study-20261012/combined/cause/units/
*-1121/states/** (66; never the prefetch/ hard links). The Mac copies are never changed or deleted. gh runs without RunPod,
HF or other token variables (the Gate B backup tool's gh_env). Asset name = the repo-relative path with '/' -> '__'.
State: state.json beside this script (resumable); log: one JSON line per event on stdout.
"""
import datetime as dt, glob, hashlib, json, os, pathlib, re, subprocess, sys, tempfile, time

sys.dont_write_bytecode = True
ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tmp/gate-b-olmo"))
import backup_records_gateb as bk  # noqa: E402  (gh_env, gh, gh_json, release_absent, repo_privacy)
import secret_scan  # noqa: E402

TAG = "backup-2026-10-17-mac-weights"
TITLE = "Private backup 2026-10-17 (Mac-only model weights and states: 20 probe adapters, causal pilot 1121 states)"
STAGE = HERE / "stage"
STATE = HERE / "state.json"
MAN = HERE / "manifest.json"
SUMS = HERE / "SHA256SUMS"
NOTES = HERE / "README.md"
RETRIES = 6


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


def sources() -> list[pathlib.Path]:
    a = sorted(glob.glob(str(ROOT / "tmp/sp-repr/out/*/*/states/e1/adapter.safetensors")))
    c = sorted(p for p in glob.glob(str(ROOT / "tmp/cause-study-20261012/combined/cause/units/*-1121/states/**"), recursive=True)
               if os.path.isfile(p))
    if len(a) != 20 or len(c) != 66:
        raise SystemExit(f"unexpected file counts: adapters {len(a)} (want 20), cause states {len(c)} (want 66)")
    return [pathlib.Path(p) for p in a + c]


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"uploaded": [], "verified": {}}


def save_state(s: dict) -> None:
    STATE.write_text(json.dumps(s, indent=1) + "\n")


def privacy(env, point):
    p = bk.repo_privacy(env)
    log(event="privacy", point=point, **p)
    if not p["is_private"]:
        raise SystemExit(f"{point}: the repository is not reported private; stop")
    return p


def release_info(env) -> dict:
    return bk.gh_json(["release", "view", TAG, "--json", "isDraft,url,assets"], env) or {}


def prepare() -> None:
    files = sources()
    STAGE.mkdir(exist_ok=True)
    entries = []
    for p in files:
        rel = str(p.relative_to(ROOT))
        name = rel.replace("/", "__")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
            raise SystemExit(f"asset name has an unexpected character: {name}")
        link = STAGE / name
        if link.exists():
            if os.stat(link).st_ino != os.stat(p).st_ino:
                raise SystemExit(f"stage name exists and is not a hard link to its source: {name}")
        else:
            os.link(p, link)
        entries.append({"asset": name, "path": rel, "bytes": p.stat().st_size, "sha256": sha(p)})
        log(event="hashed", asset=name, bytes=entries[-1]["bytes"])
    names = [e["asset"] for e in entries]
    if len(set(names)) != len(names) or max(e["bytes"] for e in entries) >= 2 * 1024 ** 3:
        raise SystemExit("asset names are not unique, or an asset is 2 GiB or larger")
    total = sum(e["bytes"] for e in entries)
    MAN.write_text(json.dumps({"release": TAG, "draft": True, "repo_must_be_private": True, "created_utc": now(),
                               "kind": "private research backup: Mac-only model weights and states (adapters, optimizer, RNG, state.json)",
                               "authority": "the user's 'go ahead' in the FAQ chat on 17 Oct IST, relayed by FAQ to the lead (GI VI); this upload only",
                               "not_included": ["tmp/cause-study-20261012/prefetch/ (hard links to the same files)",
                                                "the public Granite GGUF", "states on stopped pods (OLMo Gate A seed 1102; Gate B w0b-2 retrain)"],
                               "files": len(entries), "bytes": total, "assets": entries}, indent=1) + "\n")
    SUMS.write_text("".join(f"{e['sha256']}  {e['asset']}\n" for e in entries))
    NOTES.write_text(f"# {TITLE}\n\nPrivate draft release. {len(entries)} files, {total} bytes ({total / 1024 ** 3:.2f} GiB). Each asset name is "
                     "the repository-relative source path with '/' replaced by '__'; manifest.json maps each asset to its path, bytes and SHA-256. "
                     "Not included: the prefetch/ hard links, the public Granite GGUF, and the states that exist only on stopped pods.\n")
    small = [MAN, SUMS, NOTES] + [p for p in files if p.suffix == ".json"]
    hits = secret_scan.scan_paths(small)
    ipv4 = [str(p) for p in small if re.search(rb"\b(?:\d{1,3}\.){3}\d{1,3}\b", p.read_bytes())]
    log(event="prepared", files=len(entries), bytes=total, scan_files=len(small), scan_hits=len(hits), ipv4_files=ipv4,
        manifest_sha256=sha(MAN))
    if hits:
        raise SystemExit("secret scan hit in the manifest, notes or state.json files: stop")


def upload() -> None:
    env = bk.gh_env()
    log(event="gh-env", dropped=bk.gh_dropped())
    privacy(env, "before-upload")
    man = json.loads(MAN.read_text())
    st = load_state()
    info = release_info(env)
    if not info:
        bk.release_absent(TAG, env)
        p = bk.gh(["release", "create", TAG, "--draft", "--title", TITLE, "--notes-file", str(NOTES), str(MAN), str(SUMS)], env)
        log(event="release-create", exit=p.returncode)
        if p.returncode:
            raise SystemExit("gh release create failed")
        info = release_info(env)
    if info.get("isDraft") is not True:
        raise SystemExit("the release is not a draft: stop")
    have = {a["name"]: a.get("size") for a in info.get("assets") or []}
    for e in man["assets"]:
        if have.get(e["asset"]) == e["bytes"]:
            if e["asset"] not in st["uploaded"]:
                st["uploaded"].append(e["asset"]); save_state(st)
            continue
        for attempt in range(1, RETRIES + 1):
            t0 = time.time()
            p = bk.gh(["release", "upload", TAG, str(STAGE / e["asset"]), "--clobber"], env)
            log(event="upload", asset=e["asset"], bytes=e["bytes"], attempt=attempt, exit=p.returncode, seconds=round(time.time() - t0))
            if p.returncode == 0:
                st["uploaded"].append(e["asset"]); save_state(st); break
            time.sleep(min(600, 30 * attempt))
        else:
            raise SystemExit(f"upload failed after {RETRIES} tries: {e['asset']}")
    info = release_info(env)
    log(event="after-upload", is_draft=info.get("isDraft"), assets=len(info.get("assets") or []))
    privacy(env, "after-upload")


def verify() -> None:
    env = bk.gh_env()
    man = json.loads(MAN.read_text())
    st = load_state()
    for e in man["assets"]:
        if st["verified"].get(e["asset"]) == e["sha256"]:
            continue
        with tempfile.TemporaryDirectory(dir=str(HERE)) as d:
            for attempt in range(1, RETRIES + 1):
                p = bk.gh(["release", "download", TAG, "--pattern", e["asset"], "--dir", d, "--clobber"], env)
                got = pathlib.Path(d) / e["asset"]
                ok = p.returncode == 0 and got.is_file()
                digest = sha(got) if ok else None
                log(event="download", asset=e["asset"], attempt=attempt, exit=p.returncode, match=digest == e["sha256"])
                if digest == e["sha256"]:
                    st["verified"][e["asset"]] = digest; save_state(st); break
                time.sleep(min(600, 30 * attempt))
            else:
                raise SystemExit(f"download-back failed or SHA-256 differs: {e['asset']}")
    info = release_info(env)
    p = privacy(env, "end")
    out = {"release": TAG, "url": info.get("url"), "release_is_draft": info.get("isDraft") is True, "repo_is_private": p["is_private"],
           "assets_expected": len(man["assets"]) + 2, "assets_listed": len(info.get("assets") or []),
           "download_back_hashes_ok": all(st["verified"].get(e["asset"]) == e["sha256"] for e in man["assets"]),
           "verified_files": len(st["verified"]), "bytes": man["bytes"], "checked_utc": now()}
    (HERE / "upload-verification.json").write_text(json.dumps(out, indent=1) + "\n")
    log(event="verified", **out)
    if not (out["release_is_draft"] and out["repo_is_private"] and out["download_back_hashes_ok"]):
        raise SystemExit("verification failed")


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step in ("prepare", "all"):
        prepare()
    if step in ("upload", "all"):
        upload()
    if step in ("verify", "all"):
        verify()
    if step not in ("prepare", "upload", "verify", "all"):
        raise SystemExit(__doc__)
