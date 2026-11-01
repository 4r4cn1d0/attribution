"""One private DRAFT GitHub release of the research records that no release holds yet (administrative; GI V step 4 a).

    python3.11 -I backup_post_1010.py --dry-run [--out DRY.json]
    python3.11 -I backup_post_1010.py --stage STAGE_DIR

Made from runkit/gate-b-olmo/backup_records_gateb.py and the family-probe kits' backup_records_olmo.py (b4ff3e1b...).
Kept from them: a private DRAFT release; tar.gz assets plus inventory.jsonl, secret-scan.json, SHA256SUMS and
manifest.json; the scanner (runkit/gate-b-olmo/secret_scan.py patterns, every recorded pod IP, the values of the token
variables; pattern names and paths only, never matched text) over every source before staging, every staged file and
every generated file; any hit stops the run before upload; the copies must hash like their sources; "release not found"
is the only reply that counts as absent; the repository must be private before staging and after upload; the
download-back check (size and SHA-256 of every asset); gh runs without RunPod, HF or other token variables.

Changes: many sources in one release (one tar.gz per group); a time filter per source (a kit that an earlier release
holds contributes only files changed after that release, less a one-hour margin); a never-open guard (a path with
hidden/, banks/, held-out or selector*.jsonl is listed by name and never read); test scratch folders of the gi-v-*
reviews (bt*, ws, mut, snapshot, snap, sim, merged) are left out; archives that are kept (the side paper's packages)
are scanned member by member; the token values also come from ~/.config/attribution/secrets.env (compared, never
shown, never passed to gh).
Never staged: model weights and states (.safetensors, .bin, .pt, .pth, .gguf, .ckpt); symlinks; pod address files
(pod*.json), known_hosts, timer settings; SSH folders and keys; account state (account*.json); setup bundles and
payloads; locks, caches, partial downloads; kit code identical to the runkit copy.
--dry-run: no network except `gh release list` (read-only, for the earlier releases' times); writes only --out.
"""
import argparse, datetime, gzip, hashlib, importlib.util, io, json, os, pathlib, re, shutil, subprocess, sys
import tarfile, tempfile, zipfile

sys.dont_write_bytecode = True
ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution")
TMP = ROOT / "tmp"
HERE = pathlib.Path(__file__).resolve().parent
TAG = "backup-2026-10-16-post-1010-records"
PREFIX = "post1010"
LAST_RELEASE = "backup-2026-10-10-gateb-anchor"
MARGIN_S = 3600
MAX_BYTES = 50 * 1024 * 1024
_spec = importlib.util.spec_from_file_location("kit_secret_scan", ROOT / "runkit/gate-b-olmo/secret_scan.py")
secret_scan = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(secret_scan)

WEIGHTS = {".safetensors", ".bin", ".pt", ".pth", ".gguf", ".ckpt"}
PRUNE_DIRS = re.compile(r"^(ssh|__pycache__|\.pytest_cache|\.git|node_modules|venv|\.venv)$")
SCRATCH_DIRS = re.compile(r"^(bt.*|ws|mut|snapshot|snap|sim|merged)$")          # gi-v-* review scratch only
NEVER_FILES = re.compile(r"^(pod.*\.json|known_hosts.*|timer-settings.*|account.*\.json|.*\.lock|\.DS_Store|.*\.pyc|"
                         r".*\.part|.*\.pub|secrets.*|.*\.env|key|id_(rsa|ed25519).*)$")
BUNDLES = re.compile(r"^(bundle.*|worker-setup.*|payload)\.(tar\.gz|tgz)$")
ARCHIVES = (".tar.gz", ".tgz", ".tar", ".zip", ".gz")
TOKEN_VARS = ("RUNPOD_OPERATOR_API_KEY", "RUNPOD_API_KEY", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN",
              "CLAUDE_CODE_MESSAGING_TOKEN")
RUNKITS = [ROOT / "runkit" / n for n in ("family-probe", "gate-b-olmo", "kill-test-stage0")]
IPV4 = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def guarded(parts) -> bool:
    """Paths never opened: hidden/, banks/, held-out, selector*.jsonl (by name only)."""
    low = [p.lower() for p in parts]
    return (any(p in ("hidden", "banks") for p in low) or any(re.search(r"held[-_ ]?out", p) for p in low)
            or bool(re.fullmatch(r"selector.*\.jsonl", low[-1])))


# ---- sources -------------------------------------------------------------------------------------------------------
SINCE = {  # kit -> the latest earlier release that holds it
    "gate-b-olmo": "backup-2026-10-10-gateb-anchor",
    "family-probe-llama32-1b": "backup-2026-10-08-llama32-1b-probe",
    "family-probe-llama32-1b-b5e5": "backup-2026-10-09-llama32-1b-b5e5",
    "family-probe-llama32-1b-g": "backup-2026-10-08-llama32-1b-recipe-g",
    "family-probe-llama32-1b-g-seed1102": "backup-2026-10-09-llama32-1b-recipe-g-seed-1102",
    "family-probe-llama32-1b-g-seed1103": "backup-2026-10-09-llama32-1b-recipe-g-seed-1103-granite",
    "family-probe-llama32-1b-g5e5": "backup-2026-10-09-llama32-1b-g5e5-granite",
    "family-probe-olmo2-1b": "backup-2026-10-08-olmo2-1b-gate-a",
    "family-probe-olmo2-1b-bt": "backup-2026-10-08-olmo2-1b-bt",
    "family-probe-olmo2-1b-g": "backup-2026-10-08-olmo2-1b-recipe-g",
    "family-probe-olmo2-1b-g-r16": "backup-2026-10-08-olmo2-1b-g-r16",
    "family-probe-olmo2-1b-g-seed1102": "backup-2026-10-08-olmo2-1b-recipe-g-seed-1102",
    "family-probe-olmo2-1b-g-seed1103": "backup-2026-10-08-olmo2-1b-recipe-g-seed-1103",
    "family-probe-olmo2-1b-g5e5": "backup-2026-10-09-olmo2-1b-g5e5-granite",
    "family-probe-olmo2-1b-g5e5-seed1102": "backup-2026-10-09-olmo2-1b-g5e5-seed-1102-granite",
    "family-probe-olmo2-1b-gateA-1102": "backup-2026-10-08-olmo2-1b-gate-a-seed-1102",
    "family-probe-olmo2-1b-gateA-1103": "backup-2026-10-08-olmo2-1b-gate-a-seed-1103",
    "family-probe-sp-llama32-1b-b-seed1102": "backup-2026-10-09-sp-llama32-1b-b-seed1102",
    "family-probe-sp-llama32-1b-b-seed1103": "backup-2026-10-09-sp-llama32-1b-b-seed1103",
}


DEDUPE = {  # kit -> a local inventory of its earlier release: a file whose SHA-256 that release holds is not staged again
    "gate-b-olmo": TMP / "backup-stage-gateb-anchor-assets" / "inventory.jsonl",
}


def released_digests(name: str) -> set:
    inv = DEDUPE.get(name)
    if not inv:
        return set()
    if not inv.is_file():
        raise SystemExit(f"the earlier release's inventory {inv} is missing")
    return {json.loads(line)["sha256"] for line in inv.read_text().splitlines() if line.strip()}


def sources() -> list[dict]:
    """(group, tmp-relative path, earlier release or None, note) for every source of this release."""
    out = []

    def add(group, name, note, skip_suffix=()):
        p = TMP / name
        if p.exists() and not p.is_symlink():
            out.append({"group": group, "name": name, "since": SINCE.get(name), "note": note, "skip_suffix": skip_suffix})

    add("main-kits", "gate-b-olmo", "Gate B kit: changes after the anchor release (plan w0a-1, operator actions, packs)")
    for name in sorted(SINCE):
        if name.startswith("family-probe-") and not name.startswith("family-probe-sp-"):
            add("main-kits", name, "released kit: records changed after its last release (11-12 Oct restarts)")
    for name in ("family-probe-llama32-1b-b5e5-seed1102", "family-probe-llama32-1b-b5e5-seed1103"):
        add("main-kits", name, "Llama-3.2-1B Gate A seed kit: never released (status report risk 1)")
    add("main-kits", "backup-stage-gateb-anchor-assets", "the anchor release's own records (no tar.gz)", (".tar.gz",))
    for p in sorted(TMP.glob("family-probe-sp-*")):
        add("side-kits", p.name, "Side Project kit (7-8B, replication, Qwen, fiction, bt, Llama B seeds)")
    for name in ("judge-pod", "family-probe-judge", "judge-pod-granite-llama-b", "judge-pod-granite-llama-b2",
                 "judge-pod-hb-llama-b5e5", "judge-pod-sp-7b-qwen", "judge-pod-sp-fiction-bt"):
        add("judges", name, "judge pod runs and their host records (no judge run is in any release)")
    for p in sorted(TMP.glob("judge-pod-*-launch.log")):
        add("judges", p.name, "judge pod launch log")
    add("repr-causal", "sp-repr", "representation probe: results and records, adapters left out")
    for name in ("family-probe-cause-olmo1b-1121", "family-probe-cause-olmo7b-1121", "family-probe-causal2-olmo1b-1122",
                 "family-probe-causal2-olmo7b-1122", "cause-study-20261012", "causal-followup-20261012"):
        add("repr-causal", name, "causal pilot 1121 and follow-up 1122: records, model states left out")
    for p in sorted(TMP.glob("gi-v-*")):
        if p.name != "gi-v-steps-4-9":
            add("gi-v", p.name, "GI V records (review scratch trees left out)")
    add("side-paper", "side-paper-continuation-20261012", "side paper continuation (12-13 Oct): packages and checks")
    return out


GROUPS = ("main-kits", "side-kits", "judges", "repr-causal", "gi-v", "side-paper")


# ---- helpers -------------------------------------------------------------------------------------------------------
def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utc(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gh_drops(name: str, value: str) -> bool:
    u = name.upper()
    return (u.startswith(("RUNPOD", "HF_")) or "HUGGING" in u or u in TOKEN_VARS and u not in ("GH_TOKEN", "GITHUB_TOKEN")
            or ("TOKEN" in u or "API_KEY" in u) and u not in ("GH_TOKEN", "GITHUB_TOKEN")
            or bool(secret_scan.PATTERNS["hf_token"].search(value or ""))
            or bool(secret_scan.PATTERNS["runpod_key"].search(value or "")))


def gh_env() -> dict:
    return {k: v for k, v in os.environ.items() if not _gh_drops(k, v)}


def gh_dropped() -> list[str]:
    return sorted(k for k, v in os.environ.items() if _gh_drops(k, v))


def gh(args, env) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True, env=env)


def _last_line(text: str) -> str:
    line = (text or "").strip().splitlines()[-1:] or [""]
    return "(redacted: matched a secret pattern)" if secret_scan.scan_text(line[0]) else line[0][:200]


def release_times(env) -> dict:
    p = gh(["release", "list", "--limit", "200", "--json", "tagName,createdAt,isDraft"], env)
    if p.returncode != 0:
        raise SystemExit(f"gh release list failed (exit {p.returncode}: {_last_line(p.stderr)})")
    return {r["tagName"]: r for r in json.loads(p.stdout)}


def repo_privacy(env) -> dict:
    p = gh(["repo", "view", "--json", "isPrivate,nameWithOwner,visibility"], env)
    try:
        repo = json.loads(p.stdout) if p.returncode == 0 else {}
    except ValueError:
        repo = {}
    return {"repo": repo.get("nameWithOwner"), "is_private": repo.get("isPrivate") is True,
            "visibility": repo.get("visibility"), "read": "isPrivate" in repo}


def token_values() -> dict:
    """Token values from the environment and ~/.config/attribution/secrets.env (compared, never shown)."""
    vals = {n: os.environ[n].strip() for n in TOKEN_VARS if len(os.environ.get(n, "").strip()) >= 16}
    env_file = pathlib.Path.home() / ".config/attribution/secrets.env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
            if m and len(m.group(2).strip().strip("'\"")) >= 16:
                vals[f"secrets.env:{m.group(1)}"] = m.group(2).strip().strip("'\"")
    return vals


def pod_ips(roots) -> set:
    """Every publicIp (and ip-like value under an ip key) in JSON/JSONL records: every tmp/*/hosts tree, every
    tmp/*/account*.json, every pod*/create-result* file, and every JSON/JSONL file up to 5 MB in the sources."""
    found = set()

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if isinstance(x, str) and re.fullmatch(r"(?i)(public_?ip|ip|ip_?address|host_?ip)", k) and IPV4.match(x.strip()):
                    if x.strip() not in ("127.0.0.1", "0.0.0.0"):
                        found.add(x.strip())
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    files = set()
    for hosts in TMP.glob("*/hosts"):
        if hosts.is_dir() and not hosts.is_symlink():
            files.update(p for p in hosts.rglob("*") if p.suffix in (".json", ".jsonl"))
    files.update(TMP.glob("*/account*.json"))
    for r in roots:
        if r.is_file():
            continue
        for dp, dns, fns in os.walk(r):
            dns[:] = [d for d in dns if not guarded(pathlib.Path(dp, d).relative_to(TMP).parts)
                      and not SCRATCH_DIRS.match(d) and d != ".git"]
            for f in fns:
                p = pathlib.Path(dp, f)
                if p.suffix in (".json", ".jsonl") and not guarded(p.relative_to(TMP).parts):
                    files.add(p)
    for p in sorted(files):
        try:
            if p.is_symlink() or not p.is_file() or p.stat().st_size > 5 * 1024 * 1024:
                continue
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for chunk in ([text] if p.suffix == ".json" else text.splitlines()):
            try:
                walk(json.loads(chunk))
            except ValueError:
                continue
    return found


def runkit_twin(src: pathlib.Path, root: pathlib.Path) -> bool:
    """A kit .py/.sh file identical to the tracked runkit copy at the same relative path."""
    if src.suffix not in (".py", ".sh") or not (root / "plan.json").is_file():
        return False
    rel = src.relative_to(root)
    digest = None
    for kit in RUNKITS:
        ref = kit / rel
        if ref.is_file() and not ref.is_symlink():
            digest = digest or sha(src)
            if sha(ref) == digest:
                return True
    return False


# ---- selection -----------------------------------------------------------------------------------------------------
def select(srcs, times) -> dict:
    items, excluded, guarded_paths, oversize, per_source = [], [], [], [], {}
    for s in srcs:
        root = TMP / s["name"]
        since_ts = None
        if s["since"]:
            if s["since"] not in times:
                raise SystemExit(f"earlier release {s['since']} not found by gh release list")
            created = datetime.datetime.strptime(times[s["since"]]["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
            since_ts = created.replace(tzinfo=datetime.timezone.utc).timestamp() - MARGIN_S
        stat = {"group": s["group"], "since_release": s["since"], "since_utc": utc(since_ts) if since_ts else None,
                "note": s["note"], "staged": 0, "bytes": 0, "older_than_release": 0, "same_content_in_release": 0,
                "excluded": {}}
        per_source[s["name"]] = stat
        held = released_digests(s["name"])

        def consider(src: pathlib.Path):
            rel = src.relative_to(TMP)
            if guarded(rel.parts):
                guarded_paths.append(str(rel)); stat["excluded"]["never-open guard"] = stat["excluded"].get("never-open guard", 0) + 1
                return
            why = None
            if src.is_symlink():
                why = "symlink"
            elif src.suffix in WEIGHTS:
                why = "model weights or states"
            elif NEVER_FILES.match(src.name):
                why = "pod address, host key, timer, account, lock, cache, key or partial file"
            elif BUNDLES.match(src.name):
                why = "setup bundle or payload"
            elif s["skip_suffix"] and src.name.endswith(s["skip_suffix"]):
                why = "already in its release"
            elif not src.is_file():
                why = "not a regular file"
            elif root.is_dir() and runkit_twin(src, root):
                why = "kit code identical to runkit"
            if why:
                excluded.append((str(rel), why)); stat["excluded"][why] = stat["excluded"].get(why, 0) + 1
                return
            st = src.stat()
            if since_ts is not None and st.st_mtime <= since_ts:
                stat["older_than_release"] += 1
                return
            if st.st_size > MAX_BYTES:
                oversize.append((str(rel), st.st_size)); stat["excluded"]["oversize"] = stat["excluded"].get("oversize", 0) + 1
                return
            if held and sha(src) in held:
                stat["same_content_in_release"] += 1
                return
            items.append({"src": src, "dst": f"{s['group']}/{rel}", "bytes": st.st_size, "mtime": utc(st.st_mtime),
                          "source": s["name"]})
            stat["staged"] += 1; stat["bytes"] += st.st_size

        if root.is_file():
            consider(root)
            continue
        for dp, dns, fns in os.walk(root):
            folder = pathlib.Path(dp)
            keep = []
            for d in sorted(dns):
                rel = (folder / d).relative_to(TMP)
                if guarded(rel.parts):
                    guarded_paths.append(str(rel) + "/"); stat["excluded"]["never-open guard"] = stat["excluded"].get("never-open guard", 0) + 1
                elif (folder / d).is_symlink():
                    excluded.append((str(rel) + "/", "symlink")); stat["excluded"]["symlink"] = stat["excluded"].get("symlink", 0) + 1
                elif PRUNE_DIRS.match(d) or (s["group"] == "gi-v" and SCRATCH_DIRS.match(d)):
                    why = "review scratch folder" if s["group"] == "gi-v" and SCRATCH_DIRS.match(d) else "ssh, cache or VCS folder"
                    excluded.append((str(rel) + "/", why)); stat["excluded"][why] = stat["excluded"].get(why, 0) + 1
                else:
                    keep.append(d)                     # setup/ folders are walked; their bundles are dropped by name
            dns[:] = keep
            for f in sorted(fns):
                consider(folder / f)
    dsts = [i["dst"] for i in items]
    if len(dsts) != len(set(dsts)):
        raise SystemExit("two sources for one staged path")
    return {"items": items, "excluded": excluded, "guarded": guarded_paths, "oversize": oversize, "per_source": per_source}


# ---- scanning ------------------------------------------------------------------------------------------------------
def scan_bytes(data: bytes, label: str, ips, values) -> list:
    text = data.decode("utf-8", "ignore")
    hits = [(label, n) for n in secret_scan.scan_text(text)]
    hits += [(label, "pod IP") for ip in sorted(ips) if re.search(rf"(?<![\d.]){re.escape(ip)}(?![\d])", text)]
    hits += [(label, f"value of {n}") for n, v in sorted(values.items()) if v in text]
    return hits


def scan_file(path: pathlib.Path, label: str, ips, values) -> tuple[list, list]:
    """(hits, guarded member names). An archive is scanned member by member, never extracted to disk."""
    name = path.name.lower()
    hits, guard = scan_bytes(path.read_bytes(), label, ips, values), []
    try:
        if name.endswith((".tar.gz", ".tgz", ".tar")):
            with tarfile.open(path, "r:*") as t:
                members = t.getmembers()
                guard = [m.name for m in members if guarded(pathlib.PurePosixPath(m.name).parts or ("",))]
                if guard:
                    return hits, guard
                for m in members:
                    if m.isfile() and m.size <= MAX_BYTES * 4:
                        hits += scan_bytes(t.extractfile(m).read(), f"{label}::{m.name}", ips, values)
        elif name.endswith(".zip"):
            with zipfile.ZipFile(path) as z:
                infos = z.infolist()
                guard = [i.filename for i in infos if guarded(pathlib.PurePosixPath(i.filename).parts or ("",))]
                if guard:
                    return hits, guard
                for i in infos:
                    if not i.is_dir() and i.file_size <= MAX_BYTES * 4:
                        hits += scan_bytes(z.read(i), f"{label}::{i.filename}", ips, values)
        elif name.endswith(".gz"):
            with gzip.open(path) as g:
                hits += scan_bytes(g.read(MAX_BYTES * 4), f"{label}::(gunzip)", ips, values)
    except (tarfile.TarError, zipfile.BadZipFile, OSError, EOFError) as e:
        hits.append((label, f"archive not readable for the scan ({type(e).__name__})"))
    return hits, guard


def scan_all(pairs, ips, values) -> tuple[list, list]:
    hits, guard = [], []
    for path, label in pairs:
        h, g = scan_file(path, label, ips, values)
        hits += h
        guard += [f"{label}::{m}" for m in g]
    return hits, guard


# ---- main ----------------------------------------------------------------------------------------------------------
def summary_of(sel) -> dict:
    by_group = {}
    for i in sel["items"]:
        g = i["dst"].split("/", 1)[0]
        by_group.setdefault(g, {"files": 0, "bytes": 0})
        by_group[g]["files"] += 1; by_group[g]["bytes"] += i["bytes"]
    return by_group


def texts() -> tuple[str, str]:
    title = "Private backup 2026-10-16 (records after 10 Oct 13:58 UTC and never-released records; no model states)"
    notes = ("Private research backup, 2026-10-16 (IST; created 15 Oct UTC): research records that no earlier release "
             f"holds: everything changed after {LAST_RELEASE} (10 Oct 13:58 UTC) in the Gate B kit and the released probe "
             "kits; the Side Project kits (7-8B, replication, Qwen, fiction, bt); the Llama-3.2-1B Gate A seed 1102/1103 "
             "kits; every judge pod run; the representation probe results; the causal pilot and follow-up records; the "
             "GI V review records; the side paper continuation. No model weights or states. Includes model outputs to "
             "unsafe prompts: do not publish.")
    return title, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stage")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.dry_run == bool(a.stage):
        ap.error("give exactly one of --stage and --dry-run")
    env = gh_env()
    times = release_times(env)
    srcs = sources()
    sel = select(srcs, times)
    roots = [TMP / s["name"] for s in srcs]
    ips, values = pod_ips(roots), token_values()
    hits, guard_members = scan_all([(i["src"], i["dst"]) for i in sel["items"]], ips, values)
    # A file with any scan hit (or an archive with a never-open member name) is never staged; it is listed by path
    # and kind only. Everything staged is scanned again below and must be clean.
    not_staged = sorted({(h[0].split("::", 1)[0], h[1]) for h in hits}
                        | {(g.split("::", 1)[0], "archive member with a never-open name") for g in guard_members})
    drop = {d for d, _ in not_staged}
    for i in sel["items"]:
        if i["dst"] in drop:
            st = sel["per_source"][i["source"]]
            st["staged"] -= 1; st["bytes"] -= i["bytes"]
            st["excluded"]["scan hit"] = st["excluded"].get("scan hit", 0) + 1
    sel["items"] = [i for i in sel["items"] if i["dst"] not in drop]
    sel["not_staged_scan_hits"] = [list(x) for x in not_staged]
    report = {"dry_run": a.dry_run, "tag": TAG, "time_utc": now(), "files": len(sel["items"]),
              "bytes": sum(i["bytes"] for i in sel["items"]), "groups": summary_of(sel),
              "sources": sel["per_source"], "guarded_never_opened": sel["guarded"], "oversize": sel["oversize"],
              "excluded_files": len(sel["excluded"]), "not_staged_scan_hits": sel["not_staged_scan_hits"],
              "staged_names_with_anchor": [i["dst"] for i in sel["items"] if "anchors" in i["dst"].rsplit("/", 1)[-1]],
              "scan": {"pod_ips_checked": len(ips), "token_values_checked": sorted(values), "hits": hits,
                       "archive_members_guarded": guard_members},
              "gh_env_dropped_names": gh_dropped()}
    if a.dry_run:
        report["a_real_run_would"] = f"upload {len(sel['items'])} files; leave out {len(drop)} files with scan hits"
        text = json.dumps(report, indent=1)
        if a.out:
            pathlib.Path(a.out).write_text(text + "\n")
            pathlib.Path(a.out).with_suffix(".excluded.tsv").write_text(
                "".join(f"{p}\t{w}\n" for p, w in sel["excluded"]))
        print(json.dumps({k: report[k] for k in ("files", "bytes", "groups", "oversize", "guarded_never_opened",
                                                    "excluded_files", "staged_names_with_anchor", "a_real_run_would")},
                         indent=1))
        print(f"scan: {len(hits)} hits in {len(drop)} files (left out); pod IPs checked {len(ips)}; token values "
              f"checked {sorted(values)}; guarded archive members {len(guard_members)}")
        return 0

    # ---- real run ----
    tag_check = gh(["release", "view", TAG, "--json", "tagName"], env)
    if tag_check.returncode == 0:
        raise SystemExit(f"a release {TAG} already exists: nothing staged or uploaded")
    if "release not found" not in (tag_check.stderr or "").lower():
        raise SystemExit(f"cannot tell whether {TAG} exists (gh exit {tag_check.returncode}: {_last_line(tag_check.stderr)})")
    privacy_before = repo_privacy(env)
    if not privacy_before["is_private"]:
        raise SystemExit("gh repo view does not report a private repository: nothing staged or uploaded")
    stage = pathlib.Path(a.stage).resolve()
    out = stage.parent / (stage.name + "-assets")
    if stage.exists() or out.exists():
        raise SystemExit(f"{stage} or {out} exists")
    stage.mkdir(parents=True)
    for i in sel["items"]:
        t = stage / i["dst"]
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(i["src"], t)
    changed = [i["dst"] for i in sel["items"] if sha(i["src"]) != sha(stage / i["dst"])]
    if changed:
        raise SystemExit(f"{len(changed)} file(s) differ between source and copy (a writer running?): {changed[:5]}")
    staged = sorted(p for p in stage.rglob("*") if p.is_file())
    if len(staged) != len(sel["items"]):
        raise SystemExit("the staging folder holds files that were not selected")
    hits2, guard2 = scan_all([(p, str(p.relative_to(stage))) for p in staged], ips, values)
    mt = {i["dst"]: i["mtime"] for i in sel["items"]}
    inventory = [{"path": str(p.relative_to(stage)), "bytes": p.stat().st_size, "sha256": sha(p),
                  "source_mtime_utc": mt[str(p.relative_to(stage))]} for p in staged]
    out.mkdir()
    scan_record = {"files": len(inventory), "scanner": "runkit/gate-b-olmo/secret_scan.py patterns (names and paths "
                   "only), recorded pod IPs, token values; archives member by member",
                   "patterns": {k: v.pattern for k, v in secret_scan.PATTERNS.items()}, "pod_ips_checked": len(ips),
                   "token_values_checked": sorted(values), "hits": hits2, "archive_members_guarded": guard2,
                   "source_scan_left_out": sel["not_staged_scan_hits"]}
    (out / "secret-scan.json").write_text(json.dumps(scan_record, indent=1) + "\n")
    if hits2 or guard2:
        raise SystemExit(f"secret scan hits in the staged copies, nothing uploaded: {(hits2 + guard2)[:10]}")
    (out / "inventory.jsonl").write_text("".join(json.dumps(r) + "\n" for r in inventory))

    def anon(info):
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        return info

    assets = []
    for g in GROUPS:
        if not (stage / g).is_dir():
            continue
        path = out / f"{PREFIX}-{g}.tar.gz"
        with tarfile.open(path, "w:gz") as t:
            t.add(stage / g, arcname=g, filter=anon)
        assets.append(path)
    assets += [out / "inventory.jsonl", out / "secret-scan.json"]
    (out / "SHA256SUMS").write_text("".join(f"{sha(x)}  {x.name}\n" for x in assets))
    assets.append(out / "SHA256SUMS")
    title, notes = texts()
    manifest = {"release": TAG, "kind": "private research backup: records that no earlier release holds (no model "
                "states)", "draft": True, "made_utc": now(), "previous_release": LAST_RELEASE,
                "script": str(pathlib.Path(__file__).relative_to(ROOT)), "script_sha256": sha(__file__),
                "files": len(inventory), "groups": summary_of(sel),
                "assets": {x.name: {"bytes": x.stat().st_size, "sha256": sha(x)} for x in assets},
                "sources": sel["per_source"], "guarded_never_opened": sel["guarded"], "oversize_not_staged": sel["oversize"],
                "not_staged_scan_hits": sel["not_staged_scan_hits"],
                "source_scan": {"pod_ips_checked": len(ips), "token_values_checked": sorted(values), "hits": len(hits),
                                "files_left_out": len(drop)},
                "excluded_files": len(sel["excluded"]),
                "excluded": "model weights and states (.safetensors, .bin, .pt, .pth, .gguf, .ckpt); symlinks; pod address "
                            "files (pod*.json), known_hosts, timer settings; SSH folders and keys; account state; setup "
                            "bundles and payloads; locks, caches, partial downloads; kit code identical to runkit/; gi-v-* "
                            "review scratch folders (bt*, ws, mut, snapshot, snap, sim, merged); files of a released kit "
                            "older than its release less one hour; hidden/, banks/, held-out and selector*.jsonl (never "
                            "opened); secrets"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    assets.append(out / "manifest.json")
    late, _ = scan_all([(x, x.name) for x in assets if not x.name.endswith(".tar.gz")], ips, values)
    late += [("release title or notes", n) for n in secret_scan.scan_text(title + "\n" + notes)]
    if late:
        raise SystemExit(f"secret scan hits in the generated files, nothing uploaded: {late[:5]}")

    created = gh(["release", "create", TAG, "--draft", "--title", title, "--notes", notes, *[str(x) for x in assets]], env)
    if created.returncode != 0:
        raise SystemExit(f"gh release create failed (exit {created.returncode}: {_last_line(created.stderr)}); check "
                         f"'gh release view {TAG}' before any rerun (a partial draft may exist)")
    back = pathlib.Path(tempfile.mkdtemp(prefix="post1010-check-", dir=HERE))
    downloaded = gh(["release", "download", TAG, "--dir", str(back)], env)
    ver = {x.name: {"bytes": x.stat().st_size, "sha256": sha(x),
                    "downloaded_bytes": (back / x.name).stat().st_size if (back / x.name).is_file() else None,
                    "downloaded_sha256": sha(back / x.name) if (back / x.name).is_file() else None} for x in assets}
    extra = sorted(p.name for p in back.iterdir() if p.name not in ver)
    hashes_ok = downloaded.returncode == 0 and not extra and all(
        v["sha256"] == v["downloaded_sha256"] and v["bytes"] == v["downloaded_bytes"] for v in ver.values())
    shutil.rmtree(back)
    rv = gh(["release", "view", TAG, "--json", "isDraft,url,tagName,assets"], env)
    try:
        release = json.loads(rv.stdout) if rv.returncode == 0 else {}
    except ValueError:
        release = {}
    privacy = repo_privacy(env)
    is_draft = release.get("isDraft") is True
    ok = hashes_ok and is_draft and privacy["is_private"]
    record = {"ok": ok, "checked_utc": now(), "download_back_hashes_ok": hashes_ok, "download_exit": downloaded.returncode,
              "unexpected_downloaded": extra,
              "release": {"tag": TAG, "isDraft": release.get("isDraft"), "url": release.get("url"),
                          "asset_count": len(release.get("assets") or []), "read": "isDraft" in release},
              "repository": {"nameWithOwner": privacy["repo"], "isPrivate": privacy["is_private"],
                             "visibility": privacy["visibility"], "read": privacy["read"]},
              "before_staging": {"tag_check": {"tag": TAG, "absent": True, "gh_exit": tag_check.returncode,
                                               "reply": "release not found"}, "repository": privacy_before},
              "gh_env_dropped_names": gh_dropped(), "assets": ver}
    (out / "upload-verification.json").write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"ok": ok, "download_back_hashes_ok": hashes_ok, "release_is_draft": is_draft,
                      "repo_is_private": privacy["is_private"], "assets": {k: v["bytes"] for k, v in ver.items()},
                      "url": release.get("url"), "files": len(inventory), "out": str(out)}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
