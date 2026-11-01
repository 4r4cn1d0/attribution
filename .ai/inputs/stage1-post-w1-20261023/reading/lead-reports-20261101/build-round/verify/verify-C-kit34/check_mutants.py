"""Verifier's check of mutants_b15.json in ws-c: every find occurs exactly once; every mutated .py compiles;
the 36 round-34 ids and the 3 retargeted ones are listed (read-only)."""
import json, pathlib, sys
kit = pathlib.Path(sys.argv[1])
spec = json.loads((kit / "tests" / "mutants_b15.json").read_text())
ms = spec["mutants"]
print("total", len(ms), "ids unique", len({m["id"] for m in ms}) == len(ms))
bad = []
for m in ms:
    edits = m["edits"] if "edits" in m else [{"file": m["file"], "find": m["find"], "replace": m["replace"]}]
    texts = {}
    for e in edits:
        f = kit / e["file"]
        text = texts.get(e["file"], f.read_text())
        n = text.count(e["find"])
        if n != 1:
            bad.append((m["id"], e["file"], n))
            continue
        texts[e["file"]] = text.replace(e["find"], e["replace"], 1)
    for name, text in texts.items():
        if name.endswith(".py"):
            try:
                compile(text, name, "exec")
            except SyntaxError as exc:
                bad.append((m["id"], name, "syntax " + str(exc)))
print("bad", bad)
new = [m["id"] for m in ms if m["id"].startswith("B15-34-")]
print("new", len(new))
print("retargeted", [m["id"] for m in ms if m.get("retargeted")])
print("expect survive among new", [m["id"] for m in ms if m["id"].startswith("B15-34-") and m.get("expect")])
