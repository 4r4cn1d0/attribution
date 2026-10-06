"""Private backup of headroom-v2 records (no model states), as a draft GitHub release (administrative).

    python3.11 backup_records.py STAGE_DIR

Stages, without any .safetensors file and without pod address files:
  units/HOST/...   every retrieved tree (results, receipts, ledgers, evaluation files)
  records/HOST/... orchestration records: finished.json, orchestrate*.jsonl, create-intent*.json, stops.jsonl,
                   attempt-*.json and restart records. pod*.json, known_hosts and timer settings are left out.
  edits/           the collected edit files; analyses/: decisions, results and noise and regrade analyses
Writes inventory.jsonl (path, bytes, sha256) and runs a scan for credential patterns, this run's pod IP addresses and
SSH key material; any hit stops the backup. Packs three tar.gz assets, SHA256SUMS and manifest.json, creates the draft
release backup-2026-10-06-headroom-v2, downloads every asset back and checks its size and SHA-256 (upload-verification.json).
"""
import hashlib, json, os, pathlib, re, shutil, subprocess, sys, tarfile, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
stage = pathlib.Path(sys.argv[1]).resolve(); assert not stage.exists(); stage.mkdir(parents=True)
KEEP_RECORDS = re.compile(r"^(finished\.json|orchestrate.*\.jsonl|create-intent.*\.json|create-result.*\.json|stops\.jsonl|attempt.*|restart-(intent|result).*\.json|paused.*\.json|verification.*\.json)$")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


for tree in sorted(HERE.glob("retrieved/*/tree")):
    host = tree.parent.name
    for src in tree.rglob("*"):
        if src.is_file() and src.suffix != ".safetensors":
            dst = stage / "units" / host / src.relative_to(tree); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)
for folder in sorted((HERE / "hosts").iterdir()):
    for src in folder.iterdir():
        if src.is_file() and KEEP_RECORDS.match(src.name):
            dst = stage / "records" / folder.name / src.name; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)
for src in (HERE / "edits").glob("*.json"):
    dst = stage / "edits" / src.name; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)
for name in ("plan.json", "expected-fixture-v2.json", "budget-checks.jsonl", "deletions.jsonl", "second-judge-v2-summary.json",
             "second-judge-v2-items.jsonl", "second_judge_v2.py"):
    if (HERE / name).exists():
        dst = stage / "analyses" / name; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(HERE / name, dst)

ips = set()
for p in (HERE / "hosts").rglob("pod*.json"):
    try:
        d = json.loads(p.read_text())
    except ValueError:
        continue
    if d.get("publicIp"):
        ips.add(d["publicIp"])
patterns = [re.compile(r"rpa_[A-Za-z0-9]{10,}"), re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
            re.compile(r"hf_[A-Za-z0-9]{30,}"), re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), re.compile(r"ssh-(ed25519|rsa) AAAA")]
hits, inventory = [], []
for p in sorted(stage.rglob("*")):
    if not p.is_file():
        continue
    rel = str(p.relative_to(stage)); inventory.append({"path": rel, "bytes": p.stat().st_size, "sha256": sha(p)})
    text = p.read_bytes().decode("utf-8", "ignore")
    for pat in patterns:
        if pat.search(text):
            hits.append((rel, pat.pattern))
    for ip in ips:
        if ip in text:
            hits.append((rel, "pod IP"))
scan = {"files": len(inventory), "pod_ips_checked": len(ips), "patterns": [p.pattern for p in patterns], "hits": hits}
(stage / "secret-scan.json").write_text(json.dumps(scan, indent=1) + "\n")
if hits:
    raise SystemExit(f"secret scan hits, backup stopped: {hits[:5]}")
(stage / "inventory.jsonl").write_text("".join(json.dumps(r) + "\n" for r in inventory))

out = stage.parent / (stage.name + "-assets"); out.mkdir()
assets = []
for group in ("units", "records", "edits+analyses"):
    name = f"headroom-v2-{group.replace('+', '-')}.tar.gz"; path = out / name
    with tarfile.open(path, "w:gz") as t:
        for part in group.split("+"):
            t.add(stage / part, arcname=part)
    assets.append(path)
for extra in ("inventory.jsonl", "secret-scan.json"):
    shutil.copy2(stage / extra, out / extra); assets.append(out / extra)
sums = "".join(f"{sha(a)}  {a.name}\n" for a in assets); (out / "SHA256SUMS").write_text(sums); assets.append(out / "SHA256SUMS")
manifest = {"release": "backup-2026-10-06-headroom-v2", "kind": "private research backup: headroom v2 (validation, calibration, lead, positive control; records only)",
            "files": len(inventory), "assets": {a.name: {"bytes": a.stat().st_size, "sha256": sha(a)} for a in assets},
            "excluded": "model states (.safetensors); pod address files; prepared data (incl. hidden bank); secrets"}
(out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n"); assets.append(out / "manifest.json")
notes = ("Private research backup, 6 October 2026: headroom v2 (records only; no model states). "
         "Includes model outputs to unsafe prompts: do not publish.")
subprocess.run(["gh", "release", "create", "backup-2026-10-06-headroom-v2", "--draft", "--title", "Private backup 2026-10-06 (headroom v2 records)",
                "--notes", notes, *[str(a) for a in assets]], cwd=ROOT, check=True)
back = pathlib.Path(tempfile.mkdtemp(prefix="hr-backup-check-"))
subprocess.run(["gh", "release", "download", "backup-2026-10-06-headroom-v2", "--dir", str(back)], cwd=ROOT, check=True)
ver = {a.name: {"bytes": a.stat().st_size, "sha256": sha(a), "downloaded_bytes": (back / a.name).stat().st_size,
                "downloaded_sha256": sha(back / a.name)} for a in assets}
ok = all(v["sha256"] == v["downloaded_sha256"] and v["bytes"] == v["downloaded_bytes"] for v in ver.values())
(out / "upload-verification.json").write_text(json.dumps({"ok": ok, "assets": ver}, indent=1) + "\n")
url = subprocess.run(["gh", "release", "view", "backup-2026-10-06-headroom-v2", "--json", "url", "-q", ".url"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
shutil.rmtree(back)
print(json.dumps({"ok": ok, "assets": {k: v["bytes"] for k, v in ver.items()}, "url": url, "files": len(inventory), "out": str(out)}))
