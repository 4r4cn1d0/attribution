"""Mutation runner for scripts/scale78b/tests/refs/mutation_spec_refs_78b.json (R2 Track R; stdlib only; Track O's
tests/oext/run_mutants_oext_78b.py with its test path and spec changed).

    PY -B run_mutants_refs_78b.py SOURCE_ROOT SCRATCH OUT.json BASELINE|ALL|ID[,ID...] [--timeout SECONDS]

SOURCE_ROOT is a repository root holding scripts/scale78b (never written). SCRATCH is a new folder outside it: the
runner copies scripts/scale78b into SCRATCH/repo/scripts/ and links every other entry of SOURCE_ROOT/scripts and every
other top-level entry of SOURCE_ROOT except .git (read only). Mutations are applied to the copy only, one at a time;
the copy's bytes are restored and re-hashed after each.

Each run is the same command: PY -B -m pytest -p no:cacheprovider -q -x -rfE --basetemp SCRATCH/pt-<n>
scripts/scale78b/tests/refs, cwd SCRATCH/repo, PYTHONDONTWRITEBYTECODE=1. The baseline runs first and must exit 0,
else nothing else runs. A mutant is KILLED only by a real test failure: pytest exit 1 with at least one FAILED line and
no ERROR line. Exit 0 is SURVIVED. Anything else (exit 2-5, an ERROR line, a timeout) is INVALID, never killed. A
mutant whose find text is not exactly once in its file is INVALID and not run. The report holds ids, verdicts, exit
codes, failed test names, hashes and the clock only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

PKG_REL = pathlib.Path("scripts/scale78b")
TEST = PKG_REL / "tests" / "refs"
SPEC = PKG_REL / "tests" / "refs" / "mutation_spec_refs_78b.json"


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare(source: pathlib.Path, scratch: pathlib.Path) -> pathlib.Path:
    if scratch.exists():
        raise SystemExit(f"{scratch} exists; give a new folder")
    if scratch.resolve().is_relative_to(source.resolve()):
        raise SystemExit("SCRATCH must lie outside SOURCE_ROOT")
    repo = scratch / "repo"
    (repo / "scripts").mkdir(parents=True)
    for entry in sorted(source.iterdir()):
        if entry.name not in ("scripts", ".git"):
            (repo / entry.name).symlink_to(entry.resolve())
    for entry in sorted((source / "scripts").iterdir()):
        if entry.name == PKG_REL.name:
            shutil.copytree(entry, repo / "scripts" / entry.name, symlinks=True,
                            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        else:
            (repo / "scripts" / entry.name).symlink_to(entry.resolve())
    return repo


def run_suite(repo: pathlib.Path, scratch: pathlib.Path, n: int, timeout: int) -> dict:
    cmd = [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", "-rfE",
           "--basetemp", str(scratch / f"pt-{n}"), str(TEST)]
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        done = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=timeout)
        code, text = done.returncode, done.stdout + done.stderr
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout
        code, text = None, out.decode("utf-8", "replace") if isinstance(out, bytes) else (out or "")
    shutil.rmtree(scratch / f"pt-{n}", ignore_errors=True)
    lines = text.splitlines()
    failed = [x[len("FAILED "):].split(" - ")[0] for x in lines if x.startswith("FAILED ")]
    errors = [x for x in lines if x.startswith("ERROR ")]
    tail = [x for x in lines if x.strip()][-1:] or [""]
    return {"exit": code, "failed": failed, "errors": len(errors), "tail": tail[0][-200:]}


def verdict(r: dict) -> str:
    if r["exit"] == 1 and r["failed"] and not r["errors"]:
        return "killed"
    if r["exit"] == 0 and not r["errors"]:
        return "survived"
    return "invalid"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("source", type=pathlib.Path)
    ap.add_argument("scratch", type=pathlib.Path)
    ap.add_argument("out", type=pathlib.Path)
    ap.add_argument("select")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args(argv)
    spec = json.loads((args.source / SPEC).read_text(encoding="utf-8"))
    mutants = spec["mutants"]
    if args.select not in ("BASELINE", "ALL"):
        wanted = set(args.select.split(","))
        mutants = [m for m in mutants if m["id"] in wanted]
        missing = wanted - {m["id"] for m in mutants}
        if missing:
            raise SystemExit(f"unknown mutant ids: {sorted(missing)}")
    repo = prepare(args.source, args.scratch)
    pkg = repo / PKG_REL
    tree = {str(p.relative_to(pkg)): sha(p.read_bytes()) for p in sorted(pkg.rglob("*")) if p.is_file()}
    report = {"kind": "scale78b refs mutation run", "utc_start": utc(), "source": str(args.source),
              "python": sys.version, "spec_sha256": sha((args.source / SPEC).read_bytes()), "tree": tree,
              "results": []}
    baseline = run_suite(repo, args.scratch, 0, args.timeout)
    report["baseline"] = baseline
    if baseline["exit"] != 0:
        report["utc_end"] = utc()
        args.out.write_text(json.dumps(report, indent=1) + "\n")
        print(json.dumps({"baseline": baseline, "stopped": "the baseline did not exit 0"}, indent=1))
        return 2
    if args.select == "BASELINE":
        mutants = []
    for n, m in enumerate(mutants, start=1):
        target = pkg / m["file"]
        original = target.read_bytes()
        text = original.decode("utf-8")
        entry = {"id": m["id"], "describes": m["describes"], "file": m["file"], "before_sha256": sha(original)}
        if text.count(m["find"]) != 1:
            entry.update(verdict="invalid", reason=f"find text occurs {text.count(m['find'])} times")
        else:
            target.write_bytes(text.replace(m["find"], m["replace"]).encode("utf-8"))
            entry["mutated_sha256"] = sha(target.read_bytes())
            r = run_suite(repo, args.scratch, n, args.timeout)
            entry.update(result=r, verdict=verdict(r))
            target.write_bytes(original)
        entry["restored_sha256"] = sha(target.read_bytes())
        if entry["restored_sha256"] != entry["before_sha256"]:
            raise SystemExit(f"{m['id']}: the copy did not restore")
        report["results"].append(entry)
        print(json.dumps({k: entry.get(k) for k in ("id", "verdict", "reason")}))
    counts = {}
    for e in report["results"]:
        counts[e["verdict"]] = counts.get(e["verdict"], 0) + 1
    report["counts"] = counts
    report["utc_end"] = utc()
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({"baseline_exit": baseline["exit"], "counts": counts, "out": str(args.out)}))
    return 0 if counts.get("survived", 0) == 0 and counts.get("invalid", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
