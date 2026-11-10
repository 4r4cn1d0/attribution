"""Every mutant's find text occurs exactly once in its target file (counts only)."""
import json, pathlib, sys
kit = pathlib.Path(sys.argv[1])
bad = 0
for spec in sorted((kit / "tests").glob("mutation_spec_*.json")):
    d = json.loads(spec.read_text())
    for m in d["mutants"]:
        n = (kit / m["file"]).read_text().count(m["find"])
        if n != 1:
            bad += 1
            print(spec.name, m["id"], n)
    print(spec.name, len(d["mutants"]))
print("bad", bad)
