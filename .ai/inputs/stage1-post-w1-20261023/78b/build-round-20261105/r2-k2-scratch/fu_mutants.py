"""R2 K2 follow-up (R-49 to R-52): re-target two scorer mutants and add the follow-up's mutants."""
import json, sys
P = sys.argv[1] + "/tests/mutation_spec_scorer_78b.json"
d = json.load(open(P))
ms = {m["id"]: m for m in d["mutants"]}
NOTE = "R2 K2 follow-up: re-targeted to the changed code (same intent)"
ms["K2-m-plan-b-inputs-unchecked"].update(
    find='        kit_inputs_check(gate, doc["inputs_sha256"])\n        again = blinded_sigma_read(',
    replace="        again = blinded_sigma_read(", note=NOTE)
ms["K2F-m-blinding-files-unchecked"].update(
    find="            if not path.is_file() or mac.sha(path) != files[rel]:",
    replace="            if not path.is_file():", note=NOTE)
T = "plan_tool.py"
new = [
    ("K2FU-m-b-files-unchecked", "R-49", "block B's SR-2 status never re-hashes the blinding record's files",
     '    if doc["verified"]:\n        blinding_files_check(doc["files"], copies)\n',
     '    if False:\n        blinding_files_check(doc["files"], copies)\n'),
    ("K2FU-m-b-copies-dropped", "R-49", "the block-A copies' plan_tool.py (record-done's code) is not re-hashed",
     '        blinding_files_check(doc["files"], copies)\n', '        blinding_files_check(doc["files"])\n'),
    ("K2FU-m-b-files-checked-unverified", "R-49", "an unverified record's files are compared too (an edit refuses a 'not adopted' reading)",
     '    if doc["verified"]:\n        blinding_files_check(', '    if True:\n        blinding_files_check('),
    ("K2FU-m-checkout-files-skipped", "R-49", "blinded_sigma.py and the two tests are never re-hashed",
     '            where = [(ROOT / rel, "the one in this checkout")]', '            where = []'),
    ("K2FU-m-reread-off", "R-50", "a hand-written blinded output's sigma or df is taken",
     '        if [(type(again.get(k)), again.get(k)) for k in ("sigma_A_pp", "df", "inputs_sha256")] != \\\n',
     '        if False and [(type(again.get(k)), again.get(k)) for k in ("sigma_A_pp", "df", "inputs_sha256")] != \\\n'),
    ("K2FU-m-reread-no-sigma", "R-50", "the re-read compares df only",
     '        if [(type(again.get(k)), again.get(k)) for k in ("sigma_A_pp", "df", "inputs_sha256")] != \\\n                [(type(doc[k]), doc[k]) for k in ("sigma_A_pp", "df", "inputs_sha256")]:',
     '        if [(type(again.get(k)), again.get(k)) for k in ("df", "inputs_sha256")] != \\\n                [(type(doc[k]), doc[k]) for k in ("df", "inputs_sha256")]:'),
    ("K2FU-m-reread-no-df", "R-50", "the re-read compares sigma only",
     '        if [(type(again.get(k)), again.get(k)) for k in ("sigma_A_pp", "df", "inputs_sha256")] != \\\n                [(type(doc[k]), doc[k]) for k in ("sigma_A_pp", "df", "inputs_sha256")]:',
     '        if [(type(again.get(k)), again.get(k)) for k in ("sigma_A_pp", "inputs_sha256")] != \\\n                [(type(doc[k]), doc[k]) for k in ("sigma_A_pp", "inputs_sha256")]:'),
    ("K2FU-m-reread-no-type", "R-50", "the re-read takes 5 for 5.0",
     '        if [(type(again.get(k)), again.get(k)) for k in ("sigma_A_pp", "df", "inputs_sha256")] != \\\n                [(type(doc[k]), doc[k]) for k in ("sigma_A_pp", "df", "inputs_sha256")]:',
     '        if [again.get(k) for k in ("sigma_A_pp", "df", "inputs_sha256")] != \\\n                [doc[k] for k in ("sigma_A_pp", "df", "inputs_sha256")]:'),
    ("K2FU-m-script-hash-unchecked", "R-50", "blinded_sigma.py is loaded whatever its bytes",
     "    if not path.is_file() or mac.sha(path) != script_sha256:", "    if not path.is_file():"),
    ("K2FU-m-printout-dropped", "R-50", "record-plan-b-78b prints no sigma_A and df",
     '        got["blinded_sigma"] = {"sigma_A_pp": again["sigma_A_pp"], "df": again["df"]}', "        pass"),
    ("K2FU-m-replaced-not-skipped", "R-51", "the kit's replaced attempt still counts",
     '            if j.get("status") == "complete" and (name, j.get("complete_sha256")) in replaced:\n                continue',
     '            if False:\n                continue'),
    ("K2FU-m-replaced-any-reason", "R-51", "any requeue record's attempts are skipped",
     '    replaced = {(r["from"], d) for r in plan.get("requeues") or [] if r.get("reason") == "environment-mismatch"',
     '    replaced = {(r["from"], d) for r in plan.get("requeues") or [] if True'),
    ("K2FU-m-replaced-any-host", "R-51", "a requeue record's attempts are skipped on any host",
     '            if j.get("status") == "complete" and (name, j.get("complete_sha256")) in replaced:',
     '            if j.get("status") == "complete" and j.get("complete_sha256") in {x for _, x in replaced}:'),
    ("K2FU-m-part-superseded-always", "R-51", "a written part with other bytes is replaced without a kit record",
     "            if not part_superseded(old, doc, plan):", "            if False:"),
    ("K2FU-m-superseded-after-merge", "R-51", "a part is replaced after the merged inputs file exists",
     '            if BLINDED_INPUTS.exists():\n                fail(f"{p.relative_to(HERE)} is superseded',
     '            if False:\n                fail(f"{p.relative_to(HERE)} is superseded'),
    ("K2FU-m-superseded-any-cell", "R-51", "any changed cell counts as replaced",
     '.get("complete_sha256") in replaced\n                                 for a, s in changed)',
     '.get("complete_sha256") is not None\n                                 for a, s in changed)'),
    ("K2FU-m-superseded-entry-free", "R-51", "the part's design, engines and edits may change on a re-run",
     ' or rest(was["entry"], "cells") != rest(new["entry"], "cells"):', ":"),
    ("K2FU-m-superseded-gate-free", "R-51", "the part's gate may change on a re-run",
     ' rest(was, "entry") != rest(new, "entry") or', ""),
    ("X-snapshot-first-family-only", "R-52", "under [B] only one family's block-A snapshot is checked (the K2 re-verifier's)",
     '    for f in families:\n        plan_a, copy = sibling_plan(f, "A")',
     '    for f in list(families)[:1]:\n        plan_a, copy = sibling_plan(f, "A")'),
    ("X-kit-inputs-hash-unchecked", "R-52", "the kit's inputs file need not hash to the output's inputs_sha256 (the K2 re-verifier's)",
     "    if data is None or data != kit_inputs(gate) or hashlib.sha256(data).hexdigest() != inputs_sha256:",
     "    if data is None or data != kit_inputs(gate):"),
]
for i, part, desc, find, rep in new:
    assert i not in ms, i
    d["mutants"].append({"id": i, "part": part, "describes": desc, "file": T, "find": find, "replace": rep})
open(P, "w").write(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
print(len(d["mutants"]), len(new))
