"""Run the verifier's extra mutants with the builder's runner functions (prepare, run_suite, verdict; loaded by path
from WS, unchanged): the same copied tree, the same pytest command, the same kill rule; baseline first.
Usage: PY -B run_extra.py WS SCRATCH SPEC OUT [ID,...]"""
import hashlib, importlib.util, json, pathlib, sys
ws, scratch, spec_path, out = map(pathlib.Path, sys.argv[1:5])
want = set(sys.argv[5].split(",")) if len(sys.argv) > 5 else None
spec = importlib.util.spec_from_file_location("runner_sr2", ws / "scripts/scale78b/tests/run_mutants_sr2.py")
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
mutants = [m for m in json.loads(spec_path.read_text())["mutants"] if want is None or m["id"] in want]
repo = R.prepare(ws, scratch)
pkg = repo / R.PKG_REL
report = {"baseline": R.run_suite(repo, scratch, 0, 600), "results": []}
print(json.dumps({"baseline": report["baseline"]}), flush=True)
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
                          "exit": entry.get("result", {}).get("exit")}), flush=True)
out.write_text(json.dumps(report, indent=1) + "\n")
