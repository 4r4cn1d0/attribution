"""The re-verifier's mutant runner: the builder's run_mutants_sr2.py functions (prepare, run_suite, verdict; loaded by
path from WS, unchanged): the same copied tree, the same pytest command and the same kill rule; baseline first with
the same command. Optional TESTS override (pytest node ids, relative to the repo) restricts the suite, e.g. to the
SV-2 integration test alone. Usage: PY -B run_extra2.py WS SCRATCH SPEC OUT [ID,...|ALL] [NODE ...]"""
import hashlib, importlib.util, json, pathlib, sys
ws, scratch, spec_path, out = map(pathlib.Path, sys.argv[1:5])
want = None if len(sys.argv) <= 5 or sys.argv[5] == "ALL" else set(sys.argv[5].split(","))
nodes = sys.argv[6:]
spec = importlib.util.spec_from_file_location("runner_sr2", ws / "scripts/scale78b/tests/run_mutants_sr2.py")
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
if nodes:
    R.TESTS = tuple(nodes)
mutants = [m for m in json.loads(spec_path.read_text())["mutants"] if want is None or m["id"] in want]
if want is not None:
    assert {m["id"] for m in mutants} == want, want - {m["id"] for m in mutants}
repo = R.prepare(ws, scratch)
pkg = repo / R.PKG_REL
report = {"tests": list(map(str, R.TESTS)), "spec_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
          "baseline": R.run_suite(repo, scratch, 0, 600), "results": []}
print(json.dumps({"tests": report["tests"], "baseline": report["baseline"]}), flush=True)
if report["baseline"]["exit"] == 0:
    for n, m in enumerate(mutants, start=1):
        target = pkg / m["file"]
        original = target.read_bytes(); text = original.decode()
        entry = {"id": m["id"]}
        if text.count(m["find"]) != 1:
            entry.update(verdict="invalid", reason=f"find occurs {text.count(m['find'])} times")
        else:
            target.write_bytes(text.replace(m["find"], m["replace"]).encode())
            r = R.run_suite(repo, scratch, n, 600)
            entry.update(result=r, verdict=R.verdict(r))
            target.write_bytes(original)
        assert target.read_bytes() == original
        report["results"].append(entry)
        print(json.dumps({"id": m["id"], "verdict": entry["verdict"], "failed": entry.get("result", {}).get("failed"),
                          "exit": entry.get("result", {}).get("exit"), "errors": entry.get("result", {}).get("errors")}), flush=True)
out.write_text(json.dumps(report, indent=1) + "\n")
