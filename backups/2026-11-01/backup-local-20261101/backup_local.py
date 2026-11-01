"""Private backup of the lead's local-only items after the stage-1 reading, as a DRAFT GitHub release (1 Nov 2026).

    python3.11 -B backup_local.py --dry-run
    python3.11 -B backup_local.py STAGE_DIR          # STAGE_DIR must not exist; the assets go to STAGE_DIR-assets

Items (each one tar.gz): the sealed LN-31 draw tmp/hlc/draw-20261101/ (key and weights; packed by bytes, never opened by
hand); the restored LN-31 inputs tmp/hlc-inputs/; the lead's integration notes of 17-27 Oct (the worktree
kind-hawking-a6ce04's tmp/claude-workspaces/stage1-integrate-20261017/notes/, which hold ADD:428's evidence); the build
rounds' scratch evidence of 1 Nov (scratchpad builds/ without the ws-* worktrees). Rules as the kit's
backup_records_stage1.py, whose functions this script imports: the repository must be private; a draft release; every
file scanned for the kit's secret patterns, the token values set and every pod IP under the kit's hosts/, and any hit
stops the backup before upload; ssh, key and env files and pod*.json, known_hosts and timer settings are never packed;
gh runs without RunPod or Hugging Face variables; every asset is downloaded back and its SHA-256 compared.
"""
import json, os, pathlib, re, shutil, subprocess, sys, tarfile, tempfile

sys.dont_write_bytecode = True
ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution")
sys.path.insert(0, str(ROOT / "tmp/stage1-olmo"))
import backup_records_stage1 as bk  # noqa: E402

TAG = "backup-2026-11-01-local-after-reading"
HERE = pathlib.Path(__file__).resolve().parent
SCR = pathlib.Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/"
                   "ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad")
ITEMS = {
    "hlc-draw-sealed-20261101": ROOT / "tmp/hlc/draw-20261101",
    "hlc-inputs": ROOT / "tmp/hlc-inputs",
    "lead-notes-stage1-integrate-20261017": ROOT / ".claude/worktrees/kind-hawking-a6ce04/tmp/claude-workspaces/stage1-integrate-20261017/notes",
    "build-rounds-scratch-20261101": SCR / "builds",
}
NEVER = re.compile(r"(^|/)(\.ssh|id_[a-z0-9]+|.*\.pem|.*\.key|\.env|secrets\.env)(/|$)|(^|/)(pod.*\.json|known_hosts.*|timer-settings.*)$")
SKIP_DIRS = re.compile(r"^build-rounds-scratch-20261101/(ws-[a-z0-9]+|staging-records)(/|$)|(^|/)(__pycache__|\.pytest_cache|\.git)(/|$)")


def select():
    files, excluded = [], []
    for name, src in ITEMS.items():
        if not src.is_dir():
            raise SystemExit(f"missing item: {src}")
        for p in sorted(src.rglob("*")):
            if p.is_symlink():
                excluded.append((f"{name}/{p.relative_to(src)}", "symlink")); continue
            if not p.is_file():
                continue
            rel = f"{name}/{p.relative_to(src).as_posix()}"
            if SKIP_DIRS.search(rel):
                continue
            if NEVER.search(rel):
                excluded.append((rel, "never packed")); continue
            files.append((p, rel))
    return files, excluded


def main():
    files, excluded = select()
    ips, values = bk.pod_ips(), bk.token_values()
    hits = bk.scan(files, ips, values)
    size = sum(p.stat().st_size for p, _ in files)
    summary = {"tag": TAG, "files": len(files), "bytes": size, "excluded": len(excluded),
               "items": {n: sum(1 for _, r in files if r.startswith(n + "/")) for n in ITEMS},
               "scan": {"pod_ips_checked": len(ips), "token_values_checked": sorted(values), "hits": hits}}
    if sys.argv[1:] == ["--dry-run"]:
        print(json.dumps({**summary, "a_real_run_would": "refuse" if hits else "upload"}, indent=1))
        return 3 if hits else 0
    stage = pathlib.Path(sys.argv[1]).resolve(); out = stage.parent / (stage.name + "-assets")
    if stage.exists() or out.exists():
        raise SystemExit(f"{stage} or {out} exists: give a new STAGE_DIR")
    if hits:
        raise SystemExit(f"secret scan hits, nothing staged: {hits[:5]}")
    env = bk.gh_env()
    bk.release_absent(TAG, env)
    if not bk.repo_privacy(env)["is_private"]:
        raise SystemExit("the repository is not reported private: nothing uploaded")
    stage.mkdir(parents=True)
    for p, rel in files:
        t = stage / rel; t.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, t)
    staged = sorted(q for q in stage.rglob("*") if q.is_file())
    if bk.scan([(q, str(q.relative_to(stage))) for q in staged], ips, values):
        raise SystemExit("secret scan hits in the staged copies: nothing uploaded")
    inventory = [{"path": str(q.relative_to(stage)), "bytes": q.stat().st_size, "sha256": bk.sha(q)} for q in staged]
    out.mkdir(); assets = []
    for name in ITEMS:
        path = out / f"{name}.tar.gz"
        with tarfile.open(path, "w:gz") as t:
            t.add(stage / name, arcname=name, filter=bk._anonymous)
        assets.append(path)
    (out / "inventory.jsonl").write_text("".join(json.dumps(r) + "\n" for r in inventory)); assets.append(out / "inventory.jsonl")
    scanrec = {"files": len(inventory), "pod_ips_checked": len(ips), "token_values_checked": sorted(values), "hits": [],
               "excluded": [{"path": r, "why": w} for r, w in excluded]}
    (out / "secret-scan.json").write_text(json.dumps(scanrec, indent=1) + "\n"); assets.append(out / "secret-scan.json")
    (out / "SHA256SUMS").write_text("".join(f"{bk.sha(x)}  {x.name}\n" for x in assets)); assets.append(out / "SHA256SUMS")
    manifest = {"release": TAG, "draft": True, "kind": "private research backup: the lead's local-only items after the "
                "stage-1 reading (the sealed LN-31 draw, its restored inputs, the 17-27 Oct integration notes, the 1 Nov "
                "build rounds' scratch)", "items": {n: str(p).replace(str(pathlib.Path.home()), "~") for n, p in ITEMS.items()},
                "files": len(inventory), "assets": {x.name: {"bytes": x.stat().st_size, "sha256": bk.sha(x)} for x in assets}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n"); assets.append(out / "manifest.json")
    title = "Private backup 2026-11-01 (local-only items after the stage-1 reading; secrets excluded)"
    notes = "Draft, private. The sealed LN-31 draw is packed by bytes and was never opened. See manifest.json."
    created = bk.gh(["release", "create", TAG, "--draft", "--title", title, "--notes", notes, *[str(x) for x in assets]], env)
    if created.returncode != 0:
        raise SystemExit(f"gh release create failed (exit {created.returncode}); check 'gh release view {TAG}'")
    back = pathlib.Path(tempfile.mkdtemp(prefix="local-backup-check-"))
    dl = bk.gh(["release", "download", TAG, "--dir", str(back)], env)
    got = {x.name: bk.sha(back / x.name) if (back / x.name).is_file() else None for x in assets}
    want = {x.name: bk.sha(x) for x in assets}
    view = bk.gh_json(["release", "view", TAG, "--json", "isDraft,url"], env) or {}
    priv = bk.repo_privacy(env)
    ver = {"download_exit": dl.returncode, "hashes_match": got == want, "is_draft": view.get("isDraft") is True,
           "url": view.get("url"), "repo_private": priv["is_private"], "assets": want}
    shutil.rmtree(back)
    for name in ("manifest.json", "SHA256SUMS", "secret-scan.json"):
        shutil.copy2(out / name, HERE / name)
    (HERE / "upload-verification.json").write_text(json.dumps(ver, indent=1) + "\n")
    print(json.dumps({k: v for k, v in ver.items() if k != "assets"}))
    return 0 if ver["hashes_match"] and ver["is_draft"] and ver["repo_private"] and dl.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
