"""The verifier's hand-mutant driver: reuses the kit's runner (prepare, run_suite, verdict; read only) with the
verifier's own spec file. Nothing in SOURCE_ROOT is written.

    PY -B run_hand_mutants.py SOURCE_ROOT SCRATCH OUT.json SPEC.json [--timeout SECONDS]
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys

ap = argparse.ArgumentParser()
ap.add_argument("source", type=pathlib.Path)
ap.add_argument("scratch", type=pathlib.Path)
ap.add_argument("out", type=pathlib.Path)
ap.add_argument("spec", type=pathlib.Path)
ap.add_argument("--timeout", type=int, default=300)
ap.add_argument("--all-tests", action="store_true", help="run the kit's whole tests/ folder per mutant")
ap.add_argument("--only", default=None, help="comma-separated mutant ids")
args = ap.parse_args()

runner_path = args.source / "runkit" / "stage1-78b" / "tests" / "run_mutants_gated_78b.py"
spec_mod = importlib.util.spec_from_file_location("kit_runner", runner_path)
R = importlib.util.module_from_spec(spec_mod)
spec_mod.loader.exec_module(R)
if args.all_tests:
    R.TESTS = (R.KIT_REL / "tests",)

spec = json.loads(args.spec.read_text())
if args.only:
    wanted = set(args.only.split(","))
    spec["mutants"] = [m for m in spec["mutants"] if m["id"] in wanted]
repo = R.prepare(args.source, args.scratch)
kit = repo / R.KIT_REL
report = {"kind": spec["kind"], "utc_start": R.utc(), "source": str(args.source), "python": sys.version,
          "spec_sha256": hashlib.sha256(args.spec.read_bytes()).hexdigest(), "results": []}
baseline = R.run_suite(repo, args.scratch, 0, args.timeout)
report["baseline"] = baseline
if baseline["exit"] != 0:
    report["utc_end"] = R.utc()
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({"baseline": baseline, "stopped": "the baseline did not exit 0"}, indent=1))
    sys.exit(2)
for n, m in enumerate(spec["mutants"], start=1):
    target = kit / m["file"]
    original = target.read_bytes()
    text = original.decode("utf-8")
    entry = {"id": m["id"], "describes": m["describes"], "file": m["file"], "before_sha256": R.sha(original)}
    if text.count(m["find"]) != 1:
        entry.update(verdict="invalid", reason=f"find text occurs {text.count(m['find'])} times")
    else:
        target.write_bytes(text.replace(m["find"], m["replace"]).encode("utf-8"))
        r = R.run_suite(repo, args.scratch, n, args.timeout)
        entry.update(result=r, verdict=R.verdict(r))
        target.write_bytes(original)
    entry["restored_sha256"] = R.sha(target.read_bytes())
    assert entry["restored_sha256"] == entry["before_sha256"], m["id"]
    report["results"].append(entry)
    print(json.dumps({k: entry.get(k) for k in ("id", "verdict", "reason")} | {"failed": (entry.get("result") or {}).get("failed", [])[:2]}))
counts = {}
for e in report["results"]:
    counts[e["verdict"]] = counts.get(e["verdict"], 0) + 1
report["counts"] = counts
report["utc_end"] = R.utc()
args.out.write_text(json.dumps(report, indent=1) + "\n")
print(json.dumps({"baseline_exit": baseline["exit"], "counts": counts, "out": str(args.out)}))
