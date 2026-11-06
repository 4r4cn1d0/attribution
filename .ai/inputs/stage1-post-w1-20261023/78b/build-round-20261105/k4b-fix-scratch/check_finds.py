"""Every mutant's find text occurs exactly once in its file (kit specs)."""
import json, pathlib, sys
kit = pathlib.Path(sys.argv[1])
bad = 0
for spec in sorted((kit / "tests").glob("mutation_spec_*.json")):
    doc = json.loads(spec.read_text())
    for m in doc["mutants"]:
        edits = m.get("edits") or [[m["find"], m["replace"]]]
        text = (kit / m["file"]).read_text()
        for find, _ in edits:
            n = text.count(find)
            if n != 1:
                bad += 1
                print(spec.name, m["id"], m["file"], n)
    print(spec.name, len(doc["mutants"]))
print("bad", bad)
