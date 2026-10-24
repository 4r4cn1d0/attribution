"""Private backup of the stage-1 kit's records (no model states), as a draft GitHub release (administrative; B15,
brief §6; copied from runkit/gate-b-olmo/backup_records_gateb.py).

    python3.11 backup_records_stage1.py --dry-run --tag TAG [--host HOST ...]
    python3.11 backup_records_stage1.py STAGE_DIR --tag TAG [--host HOST ...] [--allow-missing]

Stage-1 changes (the record list): RUNKIT = runkit/stage1-olmo; the stage-1 hosts (S1-0, cert, A, certify, B, C) of
plan.json; a complete unit-free job (W1-18, the diagnostics, c0, the transfer report) has each of its recorded outputs
staged with its recorded SHA-256 (a complete unit job as before: its sealed unit with its COMPLETE.json SHA-256); the
seal records (seals/block-*.json) are staged and every file a recorded seal lists must be staged with the seal's
SHA-256 (a block seal whose own SHA-256 differs from plan.json's refuses; its judge files, judges/BLOCK/**, are
staged as units/judges/BLOCK/...); the edit file of every started edit job
(arm, regenerate, cert_c1, c0) is staged from its recorded path and checked against its recorded SHA-256; the packed
stages' receipts, sealed-files.json and probe.json, and hosts/HOST/preflight-done.json are kept. The text of the
Gate B description below is otherwise unchanged.

From the Gate B script:

Made from tmp/family-probe-olmo2-1b/backup_records_olmo.py (SHA-256 b4ff3e1b...). Unchanged: a private DRAFT release;
the staging layout (units/, records/, edits/, analyses/; three tar.gz assets, inventory.jsonl, secret-scan.json,
SHA256SUMS, manifest.json); a scan of every staged file that stops the backup on any hit (the kit's secret_scan.py
patterns, every publicIp recorded under hosts/, the values of token variables set here); the download-back
verification; gh's environment without RunPod or HF variables; --dry-run makes no network call and writes nothing
(exit 0 clean, 2 a required record missing, 3 a scan hit or an oversize file); the prepared set's manifest files only.

Gate B changes (B8, [D9] B-4):
  - RUNKIT = runkit/gate-b-olmo (kit code identical to it is not staged); --tag is required (no default tag);
  - units are keyed by (host, unit): two complete attempts of one (arm, seed) on two pods (a stranded retrain, an
    environment re-run, both -a1) are both staged under units/HOST/... and both listed, never merged or refused;
  - the planned-unit check runs over plan.json's jobs: every job the plan records complete has its unit sealed in its
    host's pulled tree, with the recorded COMPLETE.json SHA-256, and every file it lists staged (model weights aside);
    deferred, crashed and not_started jobs are listed, not required;
  - the second-judge and setup/probe.json requirements and JUDGED_TARGETS are gone;
  - staged when present: the Granite and HarmBench per-arm judge files (judges/*.json -> analyses/judges/), the MAN
    edit files of every started arm job (from the sealed folder, checked against MAN -> edits/), operator-actions.jsonl,
    every gate_b_* reading output, the packed stages' receipts, sealed-files.json and probe.json, the expected
    fixture, and the environment-check records (records/HOST/environment-checks.jsonl, bootstrap-ready.json).

Anchor text ([D14], the lead's decision): this private draft-release backup may hold anchor-*/anchors.json (the
anchor host's pulled tree; private repository, draft release, non-commercial research under PKU's CC-BY-NC). [D10]
keeps that text out of git commits, not out of private backups. The release notes say so.
"""
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tarfile, tempfile

sys.dont_write_bytecode = True                    # importing the kit's scanner writes no __pycache__ into the kit
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import secret_scan  # noqa: E402
import stage1_rules as rules  # noqa: E402

RUNKIT = ROOT / "runkit" / "stage1-olmo"
CODE_SKIP = ("retrieved", "hosts", "ssh", "edits", "seals", "tests")           # kit folders that hold no kit code
PREPARED_FILES = (("manifest.json", True), ("manifest.sha256", True), ("prepare_receipt.json", False))
TAG_FORMAT = re.compile(r"backup-(\d{4}-\d{2}-\d{2})-([a-z0-9][a-z0-9.-]*)")
WEIGHTS = {".safetensors", ".bin", ".pt", ".pth", ".gguf", ".ckpt"}
KEEP_RECORDS = re.compile(r"^(finished\.json|orchestrate.*\.jsonl|create-intent.*\.json|create-result.*\.json|stops\.jsonl|"
                          r"attempt.*|restart-(intent|result).*\.json|paused.*\.json|verification.*\.json|"
                          r"cap-override.*\.json|plan-preflight\.json|token-check\.json|gated-download.*\.json|"
                          r"orphans\.jsonl|stop-pending\.json|stop-confirmed-later\.json|pull-failures\.txt|outer\.txt|"
                          r"environment-checks\.jsonl|bootstrap-ready\.json|preflight-done\.json)$")
NEVER_RECORDS = re.compile(r"^(pod.*\.json|known_hosts.*|timer-settings.*)$")
ANALYSES = ("plan.json", "budget-checks.jsonl", "deletions.jsonl", "operator-leases.jsonl",
            "launch-holds.jsonl", "operator-actions.jsonl")
ANALYSES_GLOBS = ("launch*.log", "finisher*.log", "setup/packed-*/setup-receipt.json",
                  "setup/packed-*/sealed-files.json", "setup/packed-*/probe.json", "judges/*.json",
                  "seals/block-*.json")
REQUIRED = ("plan.json", "budget-checks.jsonl", "operator-actions.jsonl")
SEAL_OUT = pathlib.Path(rules.MAN_PATH).parent
TOKEN_VARS = ("RUNPOD_OPERATOR_API_KEY", "RUNPOD_API_KEY", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
GROUPS = ("units", "records", "edits+analyses")
EXCLUDED_NOTE = ("model weights (.safetensors, .bin, .pt, .pth, .gguf, .ckpt); pod address files (pod*.json), known_hosts, "
                 "timer settings; symlinks; setup bundles; prepared data other than the prepared set's manifest.json, "
                 "manifest.sha256 and prepare_receipt.json (never banks/ or the hidden bank); kit code identical to "
                 "runkit/stage1-olmo/; SSH keys; secrets")
GH_DROP_PREFIXES = ("RUNPOD", "HF_")                     # RUNPOD_OPERATOR_API_KEY, RUNPOD_API_KEY, HF_TOKEN, HF_HUB_TOKEN, ...


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def regular(p: pathlib.Path) -> bool:
    return p.is_file() and not p.is_symlink()


def kit_rel(p: pathlib.Path) -> str:
    return str(p.relative_to(HERE))


def source_label(p: pathlib.Path) -> str:
    """A source path for listings: kit-relative inside the kit, repository-relative outside it (the prepared set)."""
    return kit_rel(p) if HERE in p.parents else str(p.relative_to(ROOT))


def kit_code() -> tuple[list[str], list[str]]:
    """Kit .py files (top level and subfolders other than CODE_SKIP) that are absent from or differ from the tracked
    runkit/gate-b-olmo/ copy at the same relative path, and those that are identical."""
    differs, same = [], []
    for p in sorted(HERE.rglob("*.py")):
        rel = p.relative_to(HERE)
        if rel.parts[0] in CODE_SKIP or "__pycache__" in rel.parts or not regular(p):
            continue
        ref = RUNKIT / rel
        (same if regular(ref) and sha(ref) == sha(p) else differs).append(str(rel))
    return differs, same


def prepared_items(plan: dict, missing: list) -> tuple[list, dict]:
    """The plan's prepared set's manifest files (never its banks or hidden data), checked against the plan's pin."""
    items, record = [], {}
    for name, pin in sorted((plan.get("prepared") or {}).items()):
        folder = ROOT / rules.PREPARED_LOCAL / name
        staged = []
        for fname, required in PREPARED_FILES:
            src = folder / fname
            if regular(src):
                items.append((src, f"analyses/prepared/{name}/{fname}"))
                staged.append(fname)
            elif required:
                missing.append(f"{rules.PREPARED_LOCAL}/{name}/{fname}")
        manifest, pinned = folder / "manifest.json", folder / "manifest.sha256"
        digest = sha(manifest) if regular(manifest) else None
        listed = pinned.read_text().strip() if regular(pinned) else None
        matches = digest is not None and digest == pin == listed
        if digest is not None and not matches:
            missing.append(f"{rules.PREPARED_LOCAL}/{name}: manifest.json SHA-256, manifest.sha256 and plan.json's pin differ")
        record[name] = {"plan_pin": pin, "manifest_sha256": digest, "matches_pin": matches, "staged": staged}
    if not record:
        missing.append("plan.json names no prepared set")
    return items, record


def parse(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Private draft-release backup of the stage-1 kit's records")
    ap.add_argument("stage", nargs="?", help="STAGE_DIR (must not exist, outside the kit); omit with --dry-run")
    ap.add_argument("--dry-run", action="store_true", help="list, check and scan only: no network, nothing written")
    ap.add_argument("--host", action="append", help="a host of plan.json (repeatable); default: every plan host")
    ap.add_argument("--tag", required=True, help="draft release tag, backup-YYYY-MM-DD-name")
    ap.add_argument("--allow-missing", action="store_true", help="stage although a check failed (listed in the manifest)")
    ap.add_argument("--max-file-mb", type=float, default=50.0, help="refuse any staged file larger than this")
    a = ap.parse_args(argv)
    if a.dry_run == bool(a.stage):
        ap.error("give exactly one of STAGE_DIR and --dry-run")
    return a


def resolve(a: argparse.Namespace) -> tuple[dict, list[str], str]:
    plan = json.loads((HERE / "plan.json").read_text())
    hosts = sorted(dict.fromkeys(a.host)) if a.host else sorted(plan["hosts"])
    unknown = [h for h in hosts if h not in plan["hosts"]]
    if not hosts or unknown:
        raise SystemExit(f"not a host of this kit's plan.json: {unknown or 'none given'}")
    tag = a.tag
    if not TAG_FORMAT.fullmatch(tag):
        raise SystemExit("--tag must look like backup-YYYY-MM-DD-name (lower case letters, digits, dots, hyphens)")
    return plan, hosts, tag


def select(plan: dict, hosts: list[str], max_bytes: int) -> dict:
    """What a run stages: (source, staged path) pairs, the files left out and why, and the failed checks."""
    items, excluded, missing, trees = [], [], [], []
    for host in hosts:
        tree = HERE / "retrieved" / host / "tree"
        if not tree.is_dir() or tree.is_symlink():
            missing.append(f"retrieved/{host}/tree")
        else:
            trees.append(host)
            for dirpath, dirnames, filenames in os.walk(tree):     # followlinks=False: a linked folder is never entered
                folder = pathlib.Path(dirpath)
                dirnames.sort()
                excluded += [(kit_rel(folder / d), "symlink") for d in dirnames if (folder / d).is_symlink()]
                for name in sorted(filenames):
                    src = folder / name
                    if src.is_symlink():
                        excluded.append((kit_rel(src), "symlink"))
                    elif src.suffix in WEIGHTS:
                        excluded.append((kit_rel(src), "model weights"))
                    elif src.is_file():
                        items.append((src, f"units/{host}/{src.relative_to(tree)}"))
                    else:
                        excluded.append((kit_rel(src), "not a regular file"))
        records = HERE / "hosts" / host
        if not records.is_dir():
            missing.append(f"hosts/{host}")
        else:
            for src in sorted(records.iterdir()):
                if NEVER_RECORDS.match(src.name):
                    excluded.append((kit_rel(src), "pod address, host key or timer settings: never staged"))
                elif regular(src) and KEEP_RECORDS.match(src.name):
                    items.append((src, f"records/{host}/{src.name}"))
                else:
                    excluded.append((kit_rel(src), "not a kept record"))
            if not regular(records / "finished.json"):
                missing.append(f"hosts/{host}/finished.json")
        for name in ("pulls.jsonl", "verified.jsonl"):
            if regular(HERE / "retrieved" / host / name):
                items.append((HERE / "retrieved" / host / name, f"records/{host}/retrieved/{name}"))
    items += edit_items(plan, hosts, missing)
    judges = HERE / "judges"                              # a block's judge files, listed by its seal (seal.py)
    for folder in sorted(p for p in judges.iterdir() if p.is_dir() and not p.is_symlink()) if judges.is_dir() else []:
        items += [(src, f"units/judges/{folder.name}/{src.relative_to(folder).as_posix()}")
                  for src in sorted(folder.rglob("*")) if regular(src)]
    names = [*ANALYSES, *[f"hosts-full-{h}.log" for h in hosts]]
    for pattern in ANALYSES_GLOBS:
        names += sorted(kit_rel(p) for p in HERE.glob(pattern) if regular(p))
    names.append(pathlib.Path(__file__).name)
    code_differs, code_same = kit_code()
    names += code_differs
    items += [(HERE / name, f"analyses/{name}") for name in dict.fromkeys(names) if regular(HERE / name)]
    prepared, prepared_record = prepared_items(plan, missing)
    items += prepared
    missing += [name for name in (*REQUIRED, *[f"hosts-full-{h}.log" for h in hosts]) if not regular(HERE / name)]
    missing += [p for p in ("launch*.log", "finisher*.log") if not any(regular(x) for x in HERE.glob(p))]
    staged = [dst for _, dst in items]
    if len(staged) != len(set(staged)):
        raise SystemExit("two sources for one staged path")
    digests = {dst: sha(src) for src, dst in items}
    sizes = {dst: src.stat().st_size for src, dst in items}
    units, unit_checks = sealed_units(plan, trees, digests, missing)
    seal_checks(plan, digests, missing)
    jobs = job_listing(plan, hosts)
    sources = {kit_rel(src) for src, _ in items if HERE in src.parents}
    not_staged = [p.name + "/" + (" (partly staged)" if any(s.startswith(p.name + "/") for s in sources) else "")
                  if p.is_dir() and not p.is_symlink() else p.name
                  for p in sorted(HERE.iterdir()) if kit_rel(p) not in sources]
    return {"items": items, "excluded": excluded, "missing": missing, "trees": trees, "digests": digests, "sizes": sizes,
            "oversize": sorted(d for d, b in sizes.items() if b > max_bytes), "units": units, "unit_checks": unit_checks,
            "jobs": jobs, "prepared": prepared_record,
            "kit_code": {"runkit": str(RUNKIT.relative_to(ROOT)), "staged_absent_or_different": code_differs,
                         "identical_not_staged": len(code_same)},
            "kit_entries_not_staged": not_staged}


def sealed_units(plan: dict, hosts: list[str], digests: dict, missing: list) -> tuple[dict, dict]:
    """Units keyed by (host, unit) ([D9] B-4): every sealed unit in each selected host's pulled tree is checked (every
    file its COMPLETE.json lists, model weights aside, is staged with the listed SHA-256); every job the plan records
    complete on a host has its unit there, with the recorded COMPLETE.json SHA-256. Two attempts of one (arm, seed) on
    two hosts are two entries."""
    units, checks = {}, {}
    for host in hosts:
        tree = HERE / "retrieved" / host / "tree"
        found = sorted(p.parent for p in tree.rglob("COMPLETE.json")) if tree.is_dir() else []
        for unit in found:
            rel = str(unit.relative_to(tree))
            listed = json.loads((unit / "COMPLETE.json").read_text()).get("files") or {}
            prefix = f"units/{host}/{rel}/"
            weights = [r for r in listed if pathlib.PurePosixPath(r).suffix in WEIGHTS]
            bad = [r for r, d in listed.items() if r not in weights and digests.get(prefix + r) != d]
            checks[f"{host}/{rel}"] = {"listed": len(listed), "weights_not_staged": len(weights), "bad": len(bad)}
            if bad:
                missing.append(f"{host}/{rel}: {len(bad)} listed file(s) not staged or changed")
            units[(host, rel)] = unit
        for i, job in enumerate(plan["hosts"][host].get("jobs") or []):
            if job.get("status") != "complete" or job.get("kind") == "anchor":
                continue
            if job.get("kind") in rules.UNITLESS_KINDS or not job.get("unit"):
                outputs = job.get("outputs") or {}
                if not outputs:
                    missing.append(f"{host}: job {i} is complete in plan.json without its outputs")
                bad = [r for r, d in outputs.items() if digests.get(f"units/{host}/{r}") != d]
                if bad:
                    missing.append(f"{host}: job {i}: {len(bad)} recorded output(s) not staged or changed")
                continue
            unit = tree / str(job.get("unit"))
            if not (unit / "COMPLETE.json").is_file():
                missing.append(f"{host}: job {i} is complete in plan.json but its unit is not sealed in the pulled tree")
            elif sha(unit / "COMPLETE.json") != job.get("complete_sha256"):
                missing.append(f"{host}: job {i}'s COMPLETE.json differs from plan.json's record")
    return units, checks


def job_listing(plan: dict, hosts: list[str]) -> dict:
    """Every job of the selected hosts with its status: complete ones are required (sealed_units), the deferred,
    crashed and not_started ones only listed."""
    return {host: [{"index": i, "kind": j.get("kind"), "arm": j.get("arm"), "seed": j.get("seed"),
                    "status": j.get("status"), "unit": j.get("unit")} for i, j in enumerate(plan["hosts"][host]["jobs"])]
            for host in hosts}


EDIT_KINDS = ("arm", "regenerate", "cert_c1", "c0")


def edit_items(plan: dict, hosts: list[str], missing: list) -> list:
    """The edit file of every started edit job (complete or crashed) of the selected hosts, from its recorded path and
    checked against its recorded SHA-256 (bound at release from MAN1, Gate B's MANIFEST or a sealed record), staged
    under edits/<SHA-256>.edit.json."""
    used = sorted({(j["edit"]["path"], j["edit"]["sha256"]) for h in hosts for j in plan["hosts"][h].get("jobs") or []
                   if j.get("kind") in EDIT_KINDS and j.get("status") in ("complete", "crashed") and j.get("edit")})
    items = []
    for rel, digest in used:
        src = ROOT / rel
        if not regular(src) or sha(src) != digest:
            missing.append(f"edit file {pathlib.PurePosixPath(rel).name} (missing or differs from its record)")
            continue
        items.append((src, f"edits/{digest}.edit.json"))
    return items


def seal_checks(plan: dict, digests: dict, missing: list) -> None:
    """Every recorded block seal: its file staged with plan.json's SHA-256, and every file it lists staged under
    units/HOST/ with the seal's SHA-256 (the backup holds what the seal names, byte for byte)."""
    for block, rec in sorted((plan.get("seals") or {}).items()):
        staged = f"analyses/seals/block-{block}.json"
        path = HERE / "seals" / f"block-{block}.json"
        if digests.get(staged) != rec.get("sha256") or not regular(path):
            missing.append(f"seal of block {block}: missing or differs from plan.json")
            continue
        doc = json.loads(path.read_text())
        bad = [f for f in doc.get("files") or [] if digests.get(f"units/{f['host']}/{f['path']}") != f["sha256"]]
        if bad:
            missing.append(f"seal of block {block}: {len(bad)} sealed file(s) not staged or changed")


def pod_ips() -> set:
    """Every publicIp recorded anywhere under hosts/ (pod.json, pod-latest.json, create results, earlier attempts)."""
    found = set()

    def walk(value):
        if isinstance(value, dict):
            for k, v in value.items():
                if k == "publicIp" and isinstance(v, str) and v.strip():
                    found.add(v.strip())
                else:
                    walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)

    for path in sorted((HERE / "hosts").rglob("*")):
        if not regular(path) or path.suffix not in (".json", ".jsonl"):
            continue
        text = path.read_text(errors="ignore")
        for chunk in ([text] if path.suffix == ".json" else text.splitlines()):
            try:
                walk(json.loads(chunk))
            except ValueError:
                continue
    return found


def token_values() -> dict:
    """The token variables set in this environment (their values are compared, never shown)."""
    return {n: os.environ[n].strip() for n in TOKEN_VARS if len(os.environ.get(n, "").strip()) >= 16}


def scan(files: list[tuple[pathlib.Path, str]], ips: set, values: dict) -> list[tuple[str, str]]:
    """(label, what) for every hit: the kit's secret_scan patterns, a recorded pod IP, a token variable's value."""
    label = {str(p): name for p, name in files}
    hits = [(label[p], what) for p, what in secret_scan.scan_paths([p for p, _ in files])]
    for path, name in files:
        text = path.read_bytes().decode("utf-8", "ignore")
        hits += [(name, "pod IP") for ip in sorted(ips) if ip in text]
        hits += [(name, f"value of {n}") for n, v in sorted(values.items()) if v in text]
    return hits


def texts(plan: dict, hosts: list[str], tag: str) -> tuple[str, str, str]:
    date = TAG_FORMAT.fullmatch(tag).group(1)
    waves = sorted({plan["hosts"][h].get("wave") for h in hosts})
    kind = (f"private research backup: stage-1 kit {plan.get('name')} (hosts {', '.join(hosts)}; blocks {waves}; "
            "records only)")
    title = f"Private backup {date} ({plan.get('name')}, {', '.join(hosts)} records)"
    notes = (f"Private research backup, {date}: {plan.get('name')}, hosts {', '.join(hosts)} (records only; no model "
             "states). Includes model outputs to unsafe prompts: do not publish. May hold anchor-*/anchors.json "
             "(PKU's CC-BY-NC, non-commercial research): kept out of git commits, allowed in this private draft.")
    return title, notes, kind


def asset_names(tag: str) -> list[str]:
    prefix = TAG_FORMAT.fullmatch(tag).group(2)
    return [f"{prefix}-{g.replace('+', '-')}.tar.gz" for g in GROUPS]


def _group(dst: str) -> str:
    return "units" if dst.startswith("units/") else "records" if dst.startswith("records/") else "edits+analyses"


def _anonymous(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info


def _gh_drops(name: str, value: str) -> bool:
    return (name.upper().startswith(GH_DROP_PREFIXES) or "HUGGING" in name.upper()
            or name in (*rules.TOKEN_ENV_NAMES, "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
            or bool(secret_scan.PATTERNS["hf_token"].search(value or ""))
            or bool(secret_scan.PATTERNS["runpod_key"].search(value or "")))


def gh_env(environ=None) -> dict:
    """gh's environment: without any RunPod variable (RUNPOD_OPERATOR_API_KEY included), any HF token variable (by
    name: HF_*, *HUGGING*, the kit's token names; or by a value that looks like an HF or RunPod key). gh needs none."""
    environ = os.environ if environ is None else environ
    return {k: v for k, v in environ.items() if not _gh_drops(k, v)}


def gh_dropped(environ=None) -> list[str]:
    """The names (never values) of the variables gh_env removes."""
    environ = os.environ if environ is None else environ
    return sorted(k for k, v in environ.items() if _gh_drops(k, v))


def _last_line(text: str) -> str:
    line = (text or "").strip().splitlines()[-1:] or [""]
    return "(redacted: matched a secret pattern)" if secret_scan.scan_text(line[0]) else line[0][:200]


def gh(args: list[str], env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True, env=env)


def gh_json(args: list[str], env: dict) -> dict | None:
    p = gh(args, env)
    if p.returncode != 0:
        return None
    try:
        value = json.loads(p.stdout)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def release_absent(tag: str, env: dict) -> dict:
    """Only gh's "release not found" reply counts as absent; an existing release or any other reply refuses."""
    p = gh(["release", "view", tag, "--json", "tagName"], env)
    if p.returncode == 0:
        raise SystemExit(f"a release {tag} already exists: nothing staged or uploaded (give a new --tag)")
    if "release not found" not in (p.stderr or "").lower():
        raise SystemExit(f"cannot tell whether release {tag} exists (gh exit {p.returncode}: {_last_line(p.stderr)}): "
                         "nothing staged or uploaded")
    return {"tag": tag, "absent": True, "gh_exit": p.returncode, "reply": "release not found"}


def repo_privacy(env: dict) -> dict:
    repo = gh_json(["repo", "view", "--json", "isPrivate,nameWithOwner"], env) or {}
    return {"repo": repo.get("nameWithOwner"), "is_private": repo.get("isPrivate") is True,
            "read": "isPrivate" in repo}


def dry_run(plan: dict, hosts: list[str], tag: str, sel: dict) -> int:
    ips, values = pod_ips(), token_values()
    hits = scan([(src, dst) for src, dst in sel["items"]], ips, values)
    title, notes, kind = texts(plan, hosts, tag)
    print(f"# DRY RUN (no network, nothing written): kit {HERE.relative_to(ROOT)}; hosts {', '.join(hosts)}; "
          f"draft release {tag}")
    print(f"# {'bytes':>10}  {'sha256':<64}  staged path  <- kit source")
    for src, dst in sel["items"]:
        print(f"{sel['sizes'][dst]:>12}  {sel['digests'][dst]}  {dst}  <- {source_label(src)}")
    print("# assets a real run uploads (each tar.gz is built from the staged copies; its hash is known only then):")
    for name, group in zip(asset_names(tag), GROUPS):
        members = [d for _, d in sel["items"] if _group(d) == group]
        print(f"#   {name}  ({len(members)} files, {sum(sel['sizes'][d] for d in members)} bytes before compression)")
    print("#   inventory.jsonl, secret-scan.json, SHA256SUMS, manifest.json; then upload-verification.json stays local")
    print("# left out of the retrieved trees and host records:")
    for path, why in sel["excluded"]:
        print(f"#   {path}  ({why})")
    print(f"# kit entries not staged (code, setup bundles, SSH keys, locks, account state): {', '.join(sel['kit_entries_not_staged'])}")
    print(f"# a real run then calls, from {ROOT}, before staging: gh release view {tag} --json tagName (only a "
          f"'release not found' reply counts as absent); gh repo view --json isPrivate,nameWithOwner (must be private); "
          f"after staging and the scans: gh release create {tag} --draft --title {json.dumps(title)} --notes "
          f"{json.dumps(notes)} <7 assets>; gh release download {tag} --dir <temp>; gh release view {tag} --json "
          f"isDraft,url; gh repo view --json isPrivate,nameWithOwner (exit 0 only if hashes match, draft and private)")
    print(f"# gh's environment leaves out these variables set here (names only): {gh_dropped() or 'none set'}")
    summary = {"dry_run": True, "kit": str(HERE.relative_to(ROOT)), "tag": tag, "draft": True, "title": title, "kind": kind,
               "hosts": hosts, "files": len(sel["items"]), "bytes": sum(sel["sizes"].values()),
               "assets": [*asset_names(tag), "inventory.jsonl", "secret-scan.json", "SHA256SUMS", "manifest.json"],
               "units": sel["unit_checks"], "jobs": sel["jobs"],
               "prepared": sel["prepared"], "kit_code": sel["kit_code"],
               "missing": sel["missing"], "oversize": sel["oversize"], "excluded": len(sel["excluded"]),
               "scan": {"files": len(sel["items"]), "pod_ips_checked": len(ips), "token_values_checked": sorted(values),
                        "hits": hits},
               "gh_env_drops": gh_dropped(),
               "a_real_run_would": "refuse" if hits or sel["oversize"] or sel["missing"] else "upload"}
    print(json.dumps(summary, indent=1))
    return 3 if hits or sel["oversize"] else 2 if sel["missing"] else 0


def upload(a: argparse.Namespace, plan: dict, hosts: list[str], tag: str, sel: dict) -> int:
    env = gh_env()
    tag_check = release_absent(tag, env)                    # FIRST: an existing tag refuses before anything is staged
    privacy_before = repo_privacy(env)
    if not privacy_before["is_private"]:
        raise SystemExit("gh repo view does not report a private repository (isPrivate): nothing staged or uploaded")
    stage = pathlib.Path(a.stage).resolve()
    out = stage.parent / (stage.name + "-assets")
    if stage.exists() or out.exists():
        raise SystemExit(f"{stage} or {out} exists: give a new STAGE_DIR")
    if stage == HERE or HERE in stage.parents:
        raise SystemExit("STAGE_DIR must lie outside the kit")
    if not (ROOT / ".git").exists():
        raise SystemExit(f"{ROOT} is not the repository checkout that gh needs")
    if sel["missing"] and not a.allow_missing:
        raise SystemExit("nothing staged; failed checks (--dry-run lists them; --allow-missing stages anyway):\n  "
                         + "\n  ".join(sel["missing"]))
    if sel["oversize"]:
        raise SystemExit(f"nothing staged; files over {a.max_file_mb} MB: {sel['oversize'][:5]}")
    ips, values = pod_ips(), token_values()
    early = scan([(src, dst) for src, dst in sel["items"]], ips, values)     # every source, before anything is staged
    if early:
        raise SystemExit(f"secret scan hits in the sources, nothing staged: {early[:5]}")
    stage.mkdir(parents=True)
    for src, dst in sel["items"]:
        target = stage / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    (stage / "edits").mkdir(exist_ok=True)                  # keep the asset layout when no arm job has started
    changed = [dst for _, dst in sel["items"] if sha(stage / dst) != sel["digests"][dst]]
    if changed:
        raise SystemExit(f"{len(changed)} file(s) changed while staging (is a writer still running?), backup stopped: {changed[:5]}")
    staged = sorted(p for p in stage.rglob("*") if p.is_file())
    hits = scan([(p, str(p.relative_to(stage))) for p in staged], ips, values)
    inventory = [{"path": str(p.relative_to(stage)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in staged]
    record = {"files": len(inventory), "scanner": "this kit's secret_scan.py (pattern names and paths only)",
              "patterns": {k: v.pattern for k, v in secret_scan.PATTERNS.items()}, "pod_ips_checked": len(ips),
              "token_values_checked": sorted(values), "hits": hits}
    (stage / "secret-scan.json").write_text(json.dumps(record, indent=1) + "\n")
    if hits:
        raise SystemExit(f"secret scan hits, backup stopped: {hits[:5]}")
    (stage / "inventory.jsonl").write_text("".join(json.dumps(r) + "\n" for r in inventory))

    out.mkdir()
    assets = []
    for name, group in zip(asset_names(tag), GROUPS):
        path = out / name
        with tarfile.open(path, "w:gz") as t:
            for part in group.split("+"):
                t.add(stage / part, arcname=part, filter=_anonymous)
        assets.append(path)
    for extra in ("inventory.jsonl", "secret-scan.json"):
        shutil.copy2(stage / extra, out / extra); assets.append(out / extra)
    (out / "SHA256SUMS").write_text("".join(f"{sha(x)}  {x.name}\n" for x in assets)); assets.append(out / "SHA256SUMS")
    title, notes, kind = texts(plan, hosts, tag)
    manifest = {"release": tag, "kind": kind, "draft": True, "kit": str(HERE.relative_to(ROOT)), "plan": plan.get("name"),
                "hosts": sel["trees"], "units": [f"{h}/{u}" for h, u in sorted(sel["units"])],
                "engines": plan.get("engines"),
                "files": len(inventory),
                "assets": {x.name: {"bytes": x.stat().st_size, "sha256": sha(x)} for x in assets},
                "checks": {"units": sel["unit_checks"], "jobs": sel["jobs"], "prepared": sel["prepared"],
                           "kit_code": sel["kit_code"]},
                "failed_checks_at_backup": sel["missing"], "excluded": EXCLUDED_NOTE, "excluded_files": len(sel["excluded"])}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n"); assets.append(out / "manifest.json")
    late = scan([(x, x.name) for x in assets if not x.name.endswith(".tar.gz")], ips, values)
    late += [("release title or notes", n) for n in secret_scan.scan_text(title + "\n" + notes)]
    if late:
        raise SystemExit(f"secret scan hits in the generated files, nothing uploaded: {late[:5]}")

    created = gh(["release", "create", tag, "--draft", "--title", title, "--notes", notes, *[str(x) for x in assets]], env)
    if created.returncode != 0:
        raise SystemExit(f"gh release create failed (exit {created.returncode}: {_last_line(created.stderr)}); check "
                         f"'gh release view {tag}' before any rerun (a partial draft may exist)")
    back = pathlib.Path(tempfile.mkdtemp(prefix="stage1-backup-check-"))
    downloaded = gh(["release", "download", tag, "--dir", str(back)], env)
    ver = {x.name: {"bytes": x.stat().st_size, "sha256": sha(x),
                    "downloaded_bytes": (back / x.name).stat().st_size if (back / x.name).is_file() else None,
                    "downloaded_sha256": sha(back / x.name) if (back / x.name).is_file() else None} for x in assets}
    hashes_ok = downloaded.returncode == 0 and all(
        v["sha256"] == v["downloaded_sha256"] and v["bytes"] == v["downloaded_bytes"] for v in ver.values())
    shutil.rmtree(back)
    release = gh_json(["release", "view", tag, "--json", "isDraft,url"], env) or {}
    privacy = repo_privacy(env)
    is_draft = release.get("isDraft") is True
    ok = hashes_ok and is_draft and privacy["is_private"]
    record = {"ok": ok, "download_back_hashes_ok": hashes_ok, "download_exit": downloaded.returncode,
              "release": {"tag": tag, "isDraft": release.get("isDraft"), "url": release.get("url"),
                          "read": "isDraft" in release},
              "repository": {"nameWithOwner": privacy["repo"], "isPrivate": privacy["is_private"], "read": privacy["read"]},
              "before_staging": {"tag_check": tag_check, "repository": privacy_before},
              "gh_env_dropped_names": gh_dropped(), "assets": ver}
    (out / "upload-verification.json").write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"ok": ok, "download_back_hashes_ok": hashes_ok, "release_is_draft": is_draft,
                      "repo_is_private": privacy["is_private"], "assets": {k: v["bytes"] for k, v in ver.items()},
                      "url": release.get("url"), "files": len(inventory), "out": str(out)}))
    if not ok:
        print("NOT OK: " + "; ".join(why for why, bad in (("download-back hash check failed", not hashes_ok),
                                                          ("the release is not reported as a draft", not is_draft),
                                                          ("the repository is not reported as private",
                                                           not privacy["is_private"])) if bad), file=sys.stderr)
    return 0 if ok else 1


def main(argv=None) -> int:
    a = parse(sys.argv[1:] if argv is None else argv)
    plan, hosts, tag = resolve(a)
    sel = select(plan, hosts, int(a.max_file_mb * 1024 * 1024))
    return dry_run(plan, hosts, tag, sel) if a.dry_run else upload(a, plan, hosts, tag, sel)


if __name__ == "__main__":
    sys.exit(main())
