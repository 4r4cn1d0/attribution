"""Mutation runner for runkit/stage1-olmo/tests/mutants_b15.json (B15 kit round 31, 27 Oct 2026; stdlib only).

    PY -B run_mutants_b15.py SOURCE_ROOT SCRATCH OUT.json SELECT [--near BASE_KIT] [--deselect NODEID]...
                             [--timeout SECONDS]

SELECT: BASELINE (the baseline only), ALL, NEW (ids starting B15-31-), NEAR (every mutant whose find text starts
within 40 lines of a line this round changed: --near names the kit folder before the round), or ID[,ID...].

SOURCE_ROOT is a repository root holding runkit/stage1-olmo (the round's tree or the integrating copy); it is never
written. SCRATCH is a new folder outside SOURCE_ROOT. The runner copies runkit/stage1-olmo and runkit/gate-b-olmo into
SCRATCH/repo/runkit/ and links every other top-level entry of SOURCE_ROOT (scripts, experiments, .ai, research,
backups, tmp when present, ...) and the other runkit folders inside SCRATCH/repo, as the mutants file's note asks (no
sibling folder). Mutations are applied to the copy only, one mutant at a time; the copy's file bytes are restored and
re-hashed after each.

Each run is the same command: PY -B -m pytest -p no:cacheprovider -q -x -rfE --basetemp SCRATCH/pt-<n> <the kit's
five test files, test_round30a.py and test_stage1_judge_route.py included>, cwd SCRATCH/repo, with
PYTHONDONTWRITEBYTECODE=1 (STAGE1_ENGINE_Y_TREE is passed on when set). The baseline runs first with that command and
must exit 0, else nothing else runs (deselect only the baseline's environment failures). A mutant is KILLED only by a
real test failure: pytest exit 1 with at least one FAILED line and no ERROR line. Exit 0 is SURVIVED (a mutant marked
"expect": "survive" is reported as survived as expected). Anything else (exit 2-5, an ERROR line, a collection error,
a timeout) is INVALID, never killed. A mutant whose find text is not exactly once in its file is INVALID and not run.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

KIT_REL = pathlib.Path("runkit/stage1-olmo")
COPIED = ("stage1-olmo", "gate-b-olmo")
TESTS = ("tests/test_round31.py", "tests/test_stage1_judge_route.py", "tests/test_round30a.py",
         "tests/test_stage1_runkit.py", "tests/test_stage1_runner.py")
NEAR_LINES = 40


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def edits_of(m: dict) -> list[dict]:
    return m["edits"] if "edits" in m else [{"file": m["file"], "find": m["find"], "replace": m["replace"]}]


def prepare(source: pathlib.Path, scratch: pathlib.Path) -> pathlib.Path:
    """SCRATCH/repo: the two kit folders copied, everything else linked (read only)."""
    if scratch.exists():
        raise SystemExit(f"{scratch} exists; give a new folder")
    if scratch.resolve().is_relative_to(source.resolve()):
        raise SystemExit("SCRATCH must lie outside SOURCE_ROOT")
    repo = scratch / "repo"
    (repo / "runkit").mkdir(parents=True)
    for entry in sorted(source.iterdir()):
        if entry.name != "runkit":
            (repo / entry.name).symlink_to(entry.resolve())
    for entry in sorted((source / "runkit").iterdir()):
        if entry.name in COPIED:
            shutil.copytree(entry, repo / "runkit" / entry.name, symlinks=True,
                            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        else:
            (repo / "runkit" / entry.name).symlink_to(entry.resolve())
    return repo


def run_suite(repo: pathlib.Path, scratch: pathlib.Path, n: int, deselect: list[str], timeout: int) -> dict:
    cmd = [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", "-rfE",
           "--basetemp", str(scratch / f"pt-{n}"), *[str(KIT_REL / t) for t in TESTS],
           *[a for d in deselect for a in ("--deselect", d)]]
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH",)}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        done = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=timeout)
        code, text = done.returncode, done.stdout + done.stderr
    except subprocess.TimeoutExpired as exc:            # a timeout is an invalid run, never a kill
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


def changed_lines(base_kit: pathlib.Path, kit: pathlib.Path, rel: str) -> list[int] | None:
    """0-based line numbers of the new file that this round changed (None: a new file, every line)."""
    old = base_kit / rel
    new = (kit / rel).read_text().splitlines()
    if not old.is_file():
        return None
    out = []
    for tag, _, _, j1, j2 in difflib.SequenceMatcher(None, old.read_text().splitlines(), new,
                                                     autojunk=False).get_opcodes():
        if tag != "equal":
            out += list(range(j1, max(j2, j1 + 1)))
    return out


def near(m: dict, kit: pathlib.Path, base_kit: pathlib.Path) -> bool:
    for e in edits_of(m):
        text = (kit / e["file"]).read_text()
        if text.count(e["find"]) != 1:
            return True                                   # run it: it is reported invalid
        start = text[:text.index(e["find"])].count("\n")
        lines = changed_lines(base_kit, kit, e["file"])
        if lines is None or any(abs(start - k) <= NEAR_LINES for k in lines):
            return True
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("source", type=pathlib.Path)
    ap.add_argument("scratch", type=pathlib.Path)
    ap.add_argument("out", type=pathlib.Path)
    ap.add_argument("select")
    ap.add_argument("--near", type=pathlib.Path, default=None, help="the kit folder before this round (NEAR)")
    ap.add_argument("--deselect", action="append", default=[])
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args(argv)
    source = a.source.resolve()
    doc = json.loads((source / KIT_REL / "tests" / "mutants_b15.json").read_text())
    mutants = doc["mutants"]
    if a.select == "BASELINE":
        chosen = []
    elif a.select == "ALL":
        chosen = mutants
    elif a.select == "NEW":
        chosen = [m for m in mutants if m["id"].startswith("B15-31-")]
    elif a.select == "NEAR":
        if a.near is None:
            raise SystemExit("NEAR needs --near BASE_KIT")
        chosen = [m for m in mutants if not m["id"].startswith("B15-31-") and near(m, source / KIT_REL, a.near)]
    else:
        ids = a.select.split(",")
        chosen = [m for m in mutants if m["id"] in ids]
        if len(chosen) != len(set(ids)):
            raise SystemExit(f"unknown mutant id(s): {sorted(set(ids) - {m['id'] for m in chosen})}")
    repo = prepare(source, a.scratch)
    kit = repo / KIT_REL
    report = {"kind": "stage1 kit mutation results", "runner": "notes/run_mutants_b15.py (kit round 31)",
              "source_root": str(source), "select": a.select, "deselect": a.deselect, "started_utc": utc(),
              "rule": "killed only by pytest exit 1 with a FAILED line and no ERROR line; exit 0 survived; anything "
                      "else invalid; the baseline (same command, no mutation) must exit 0 first",
              "tests": list(TESTS), "baseline": None, "results": []}
    report["baseline"] = run_suite(repo, a.scratch, 0, a.deselect, a.timeout)
    a.out.write_text(json.dumps(report, indent=1) + "\n")
    if report["baseline"]["exit"] != 0:
        print(json.dumps({"baseline": report["baseline"]}))
        return 2
    for n, m in enumerate(chosen, 1):
        originals = {}
        row = {"id": m["id"], "files": sorted({e["file"] for e in edits_of(m)}), "expect": m.get("expect", "kill")}
        try:
            for e in edits_of(m):
                p = kit / e["file"]
                originals.setdefault(p, p.read_bytes())
                text = p.read_text()
                if text.count(e["find"]) != 1:
                    raise ValueError(f"find text found {text.count(e['find'])} times in {e['file']}")
                p.write_text(text.replace(e["find"], e["replace"]))
            r = run_suite(repo, a.scratch, n, a.deselect, a.timeout)
            row.update(verdict=verdict(r), killed_by=r["failed"] if verdict(r) == "killed" else [], exit=r["exit"],
                       errors=r["errors"], tail=r["tail"])
        except ValueError as exc:
            row.update(verdict="invalid", killed_by=[], exit=None, errors=0, tail=str(exc))
        finally:
            for p, data in originals.items():
                p.write_bytes(data)
                if sha(p.read_bytes()) != sha(data):
                    raise SystemExit(f"{p} was not restored")
        row["as_expected"] = (row["verdict"] == "killed") if row["expect"] == "kill" else \
            (row["verdict"] == "survived")
        report["results"].append(row)
        a.out.write_text(json.dumps(report, indent=1) + "\n")
        print(json.dumps({k: row[k] for k in ("id", "verdict", "killed_by", "exit")}), flush=True)
    counts = {}
    for row in report["results"]:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    report.update(finished_utc=utc(), counts=counts,
                  not_as_expected=[row["id"] for row in report["results"] if not row["as_expected"]])
    a.out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({"counts": counts, "not_as_expected": report["not_as_expected"]}))
    return 0 if not report["not_as_expected"] else 1


if __name__ == "__main__":
    sys.exit(main())
