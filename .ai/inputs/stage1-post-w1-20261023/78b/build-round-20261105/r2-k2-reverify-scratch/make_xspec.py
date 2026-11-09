import json, sys
M = [
 ("X-cells-missing-run-ok", "plan_tool.py", "    if set(cells) != want:", "    if not cells:", "a block-A run with no complete unit passes"),
 ("X-carried-any-job", "plan_tool.py", '    return any(x.get("deferred_from") == host and _carry_key(x) == key for h in plan["hosts"].values()',
  '    return any(x.get("deferred_from") == host for h in plan["hosts"].values()', "any job carried from a host counts for every open job there"),
 ("X-snapshot-first-family-only", "plan_tool.py", "    for f in families:\n        plan_a, copy = sibling_plan(f, \"A\")",
  "    for f in list(families)[:1]:\n        plan_a, copy = sibling_plan(f, \"A\")", "under [B] only one family's block-A snapshot is checked"),
 ("X-kit-inputs-hash-unchecked", "plan_tool.py", "    if data is None or data != kit_inputs(gate) or hashlib.sha256(data).hexdigest() != inputs_sha256:",
  "    if data is None or data != kit_inputs(gate):", "the kit's inputs file need not hash to the output's inputs_sha256"),
]
src, out = sys.argv[1], sys.argv[2]
spec = {"kind": "re-verifier probe mutants (K2R)", "note": "scratch only", "mutants": []}
for i, f, find, repl, d in M:
    n = open(f"{src}/{f}").read().count(find)
    assert n == 1, (i, n)
    spec["mutants"].append({"id": i, "part": "K2R", "describes": d, "file": f, "find": find, "replace": repl})
json.dump(spec, open(out, "w"), indent=1)
print(len(spec["mutants"]))
