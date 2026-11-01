"""Scratch tool (not part of the repository): re-pin B14's re-pinned mutants to the D-6 settings and append the near
mutants of D-6, the inputs writer and its second computation. Validates every find text (exactly once, applied in
order per mutant, as T1's runner applies them). Usage: python3 update_b14_spec.py WORKTREE [--write]"""

import hashlib
import json
import sys
from pathlib import Path

ws = Path(sys.argv[1])
pkg = ws / "scripts" / "stage1_s1"
spec_path = pkg / "mutation" / "mutants_b14.json"
spec = json.loads(spec_path.read_text())
SETTINGS = "settings/overlap_strata.json"
STR = "overlap_strata.py"
INP = "overlap_inputs.py"
CHK = "overlap_inputs_check.py"
settings_text = (pkg / SETTINGS).read_text()
pin = hashlib.sha256(settings_text.encode()).hexdigest()
OLD_PIN_LINE = 'SETTINGS_SHA256 = "b98d012e9cc92dbe847f92d9ccda54cf2ee22964dbd941e5aa8bd672bff19f87"'
PIN_LINE = f'SETTINGS_SHA256 = "{pin}"'
assert (pkg / STR).read_text().count(PIN_LINE) == 1, "overlap_strata.py does not hold the new pin"


def repinned_sha(settings_edits):
    text = settings_text
    for e in settings_edits:
        assert text.count(e["find"]) == 1, e["find"][:80]
        text = text.replace(e["find"], e["replace"])
    return hashlib.sha256(text.encode()).hexdigest()


# 1. the six re-pinned mutants: the module literal follows the new file
repinned = 0
for m in spec["mutants"]:
    edits = m.get("edits") or []
    pins = [e for e in edits if e["file"] == STR and e["find"].startswith("SETTINGS_SHA256 = ")]
    if not pins:
        continue
    assert pins[0]["find"] == OLD_PIN_LINE, m["id"]
    sha = repinned_sha([e for e in edits if e["file"] == SETTINGS])
    pins[0]["find"] = PIN_LINE
    pins[0]["replace"] = f'SETTINGS_SHA256 = "{sha}"'
    repinned += 1
assert repinned == 6, repinned

# 2. the near mutants
G = "c004349c29d2b535a91a92af6de620416d2b30f5784e86d31158a99e32b1e134"
BQI = "37942cf565a7de7d4f68260ec4f769818fb03af9978b0f0356dc90851aa7644c"
S = "ceffe0efb5d75bacfbd62743f530259deeedeca8950605d1bd3ff66e5391fe46"
REC = "9e9bde6f2f32876098410479883deff5ef3141e471a79ed231c7a5db15ad399b"
MAN = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
REFUSED = f'"refused_recipes": ["{G}", "{BQI}"],'
IDENTITY = f'"identity": {{\n      "manifest_sha256": "{MAN}"\n    }},'


def d6(mid, describes, edits):
    """A settings mutant, re-pinned (the module literal follows the file): only the D-6 tests can kill it."""
    sha = repinned_sha(edits)
    return {"id": mid, "part": "B14 D-6 (1 Nov 2026: the reading's recipes)",
            "describes": describes + " (re-pinned: the module literal follows the file)",
            "edits": [{"file": SETTINGS, **e} for e in edits]
            + [{"file": STR, "find": PIN_LINE, "replace": f'SETTINGS_SHA256 = "{sha}"'}]}


def one(mid, part, describes, file, find, replace):
    return {"id": mid, "part": part, "describes": describes, "file": file, "find": find, "replace": replace}


D6 = "B14 D-6 (1 Nov 2026: the reading's recipes)"
W = "B14 inputs writer (overlap_inputs.py)"
C = "B14 inputs second computation (overlap_inputs_check.py)"
new = [
    d6("B14D6-refused-without-g", "recipe G no longer refused", [{"find": REFUSED, "replace": f'"refused_recipes": ["{BQI}"],'}]),
    d6("B14D6-refused-without-bqi", "B+Qi no longer refused", [{"find": REFUSED, "replace": f'"refused_recipes": ["{G}"],'}]),
    d6("B14D6-recipe-s-refused-too", "recipe S added to the refused recipes", [{"find": REFUSED, "replace": f'"refused_recipes": ["{G}", "{BQI}", "{S}"],'}]),
    d6("B14D6-reverted", "D-6 reverted: REC an identity field, recipe S the refused recipe",
       [{"find": IDENTITY, "replace": f'"identity": {{\n      "recipe_sha256": "{REC}",\n      "manifest_sha256": "{MAN}"\n    }},'},
        {"find": REFUSED, "replace": f'"refused_recipes": ["{S}"],'}]),
    d6("B14D6-identity-rec", "REC an identity field again (every kit unit of recipe S refuses)",
       [{"find": IDENTITY, "replace": f'"identity": {{\n      "recipe_sha256": "{REC}",\n      "manifest_sha256": "{MAN}"\n    }},'}]),
    d6("B14D6-identity-s", "recipe S an identity field (Gate A's a0 units of REC refuse)",
       [{"find": IDENTITY, "replace": f'"identity": {{\n      "recipe_sha256": "{S}",\n      "manifest_sha256": "{MAN}"\n    }},'}]),
    d6("B14D6-identity-empty", "the manifest dropped from the identity fields", [{"find": IDENTITY, "replace": '"identity": {},'}]),
    one("B14D6-refused-not-passed", D6, "the settings' refused recipes not passed to check_unit", STR,
        '"refused_recipes": rep["refused_recipes"]}', '"refused_recipes": []}'),
    # the inputs writer
    one("B14I-plan-code-off", W, "plan.json's plan code not checked", INP, "    if recorded != code:", "    if False:"),
    one("B14I-seal-entry-off", W, "a block read without a seal entry accepted", INP,
        '        entry = (plan.get("seals") or {}).get(block)', '        entry = {"sha256": "0" * 64}'),
    one("B14I-two-tables-off", W, "a cell in two blocks' tables accepted (the later block wins)", INP,
        "            if (arm, seed) in tables:", "            if False:"),
    one("B14I-reused-in-table-off", W, "a reused cell that a table holds accepted (the pin wins)", INP,
        "        if cell in reused and cell in tables:", "        if False:"),
    one("B14I-no-table-off", W, "a cell in no table not refused by name", INP,
        "        if cell not in reused and cell not in tables:", "        if False:"),
    one("B14I-no-reused-seeds", W, "a0 at the reused seeds looked for in the kit, not the pins", INP,
        "    reused = {(st.COMPARATOR, seed) for seed in rules.REUSED_SEEDS}", "    reused = set()"),
    one("B14I-pin-by-arm", W, "a0's pin taken by its arm, not its name (theta0's pin is arm a0)", INP,
        'and str(p.get("name", "")).split(" ")[0] == st.COMPARATOR and p.get("seed") == seed]',
        'and p.get("arm") == st.COMPARATOR and p.get("seed") == seed]'),
    one("B14I-pin-target-off", W, "a pin of another arm or checkpoint accepted", INP,
        '    if pin.get("arm") != st.COMPARATOR or pin.get("target") != CHECKPOINT:', "    if False:"),
    one("B14I-pin-hash-off", W, "a pinned unit's files not compared with the pin", INP,
        '    if file_sha256(folder / COMPLETE, f"the a0 pin at {seed}: {COMPLETE}") != complete \\\n'
        '            or file_sha256(folder / JOB, f"the a0 pin at {seed}: {JOB}") != job:', "    if False:"),
    one("B14I-pin-path-not-plain", W, "a pin's path not checked as a plain relative path", INP,
        '    folder = Path(repo) / plain(pin.get("path"), f"the a0 pin at {seed}: its path")',
        '    folder = Path(repo) / pin.get("path")'),
    one("B14I-bqi-own-a0-off", W, "B+Qi's own a0 not refused", INP, "            if job.get(\"role\") == BQI_OWN_A0:",
        "            if False:"),
    one("B14I-kind-off", W, "a job of the other kind (an arm job of a0) accepted", INP,
        '            if job.get("kind") != KINDS.get(cell[0], "arm"):', "            if False:"),
    one("B14I-status-off", W, "a job that is not complete taken as a unit", INP,
        '            if job.get("status") != "complete":', "            if False:"),
    one("B14I-block-off", W, "a complete unit outside its block's table accepted", INP,
        '            if where[cell] != h.get("block"):', "            if False:"),
    one("B14I-done-off", W, "a complete unit on a host that is not done accepted", INP,
        '            if h.get("done") is not True:', "            if False:"),
    one("B14I-not-pulled-taken", W, "a unit recorded complete but not pulled taken", INP,
        '            if job.get("pulled") is False:\n                continue', "            if False:\n                continue"),
    one("B14I-second-unit-wins", W, "two complete units of one cell: the later taken", INP,
        "            if cell in found:", "            if False:"),
    one("B14I-missing-off", W, "a cell with no unit not refused by name", INP,
        '    missing = sorted(c for c, b in where.items() if b != "reused" and c not in found)', "    missing = []"),
    one("B14I-recipe-not-kit-off", W, "a kit unit whose recipe is not the kit's arm recipe accepted", INP,
        '    if job.get("recipe") not in tuple(rules.TRAINING_IDENTITY_RECIPES):', "    if False:"),
    one("B14I-recipe-refused-off", W, "a kit unit of a recipe B14 refuses accepted (no early D-6 check)", INP,
        '    if config_sha in rep["refused_recipes"]:', "    if False:"),
    one("B14I-engine-off", W, "a kit unit of an engine B14 does not allow accepted", INP,
        '    if code not in rep["allowed_code_sha256"]:', "    if False:"),
    one("B14I-a0-edit-off", W, "an a0 unit with an edit accepted", INP,
        '        if edit:\n            raise s1.Refusal(f"{label}: an a0 unit with an edit")',
        '        if False:\n            raise s1.Refusal(f"{label}: an a0 unit with an edit")'),
    one("B14I-edit-record-off", W, "an add set's unit without an edit record not refused by name", INP,
        '        if not isinstance(edit, dict) or not isinstance(edit.get("sha256"), str) or not s1.HEX64.match(edit["sha256"]):',
        "        if False:"),
    one("B14I-edit-arm-off", W, "an add set's unit of another edit accepted", INP,
        "        if (edit.get(\"engine_arm\") or f\"edit-{edit['sha256']}\") != want_arm:", "        if False:"),
    one("B14I-complete-hash-off", W, "COMPLETE.json not compared with plan.json's SHA-256", INP,
        '    if file_sha256(folder / COMPLETE, f"{label}: {COMPLETE}") != complete:', "    if False:"),
    one("B14I-job-sha-of-complete", W, "job_sha256 taken from COMPLETE.json's bytes", INP,
        'file_sha256(folder / JOB, f"{label}: {JOB}"), {"block": block', 'file_sha256(folder / COMPLETE, f"{label}: {JOB}"), {"block": block'),
    one("B14I-origin-index", W, "a kit unit's origin names the next job index", INP,
        '{"block": block, "host": host, "job": i}', '{"block": block, "host": host, "job": i + 1}'),
    one("B14I-unit-not-plain", W, "plan.json's unit path not checked as a plain relative path", INP,
        "    rel = plain(job.get(\"unit\"), f\"{label}: plan.json's unit\")", '    rel = job.get("unit")'),
    one("B14I-path-from-checkout", W, "paths relative to the data root's parent", INP,
        "    root, real = Path(data_root).resolve(), Path(folder).resolve()",
        "    root, real = Path(data_root).resolve().parent, Path(folder).resolve()"),
    one("B14I-inside-root-off", W, "a folder outside the data root not refused by name", INP,
        "    if root not in real.parents:", "    if False:"),
    one("B14I-path-form-off", W, "a path B14's path_pattern refuses accepted", INP,
        '    if ".." in Path(rel).parts or not re.fullmatch(pattern, rel):', "    if False:"),
    one("B14I-symlink-followed", W, "a symbolic link hashed as its target", INP,
        "    if path.is_symlink() or not path.is_file():", "    if not path.is_file():"),
    one("B14I-one-unit-off", W, "one folder or one COMPLETE.json for two cells accepted", INP,
        "        if rel in folders or complete in completes:", "        if False:"),
    one("B14I-strata-sets-off", W, "a strata record without an add set of the plan not refused by name", INP,
        '    missing = [name for name in plan_sets if name not in doc["add_sets"]]', "    missing = []"),
    one("B14I-strata-unchecked", W, "the strata record parsed without the report's check (SHA-256, settings)", INP,
        "    doc = st._strata_record(data, digest, settings_sha256)", "    doc = s1.strict_json(data)"),
    one("B14I-strata-arm-off", W, "a strata add set whose arm is not edit-<its edit SHA-256> accepted", INP,
        '        if block.get("arm") != "edit-" + edit:', "        if False:"),
    one("B14I-rules-names-off", W, "a rules module without the names used not refused by name", INP,
        "    missing = [name for name in RULES_NAMES if not hasattr(module, name)]", "    missing = []"),
    one("B14I-plan-sha-of-parsed", W, "plan.json's SHA-256 taken of its parsed document, not its bytes", INP,
        "    return plan, sha256_bytes(data)", "    return plan, sha256_bytes(canonical_json(plan))"),
    one("B14I-settings-sha-other", W, "the sources name another settings SHA-256", INP,
        '"settings_sha256": settings_sha256, "origins": origins}}', '"settings_sha256": st.SETTINGS_SHA256[::-1], "origins": origins}}'),
    one("B14I-not-canonical", W, "the file not in canonical JSON (indent 1)", INP,
        "    return canonical_json(doc)", '    return canonical_json(doc).replace(b"  ", b" ")'),
    one("B14I-overwrites", W, "the output written over an existing one", INP,
        "        written = s1.write_new_files(args.out.resolve(), {OUTPUT: data})",
        "        args.out.mkdir(parents=True, exist_ok=True); (args.out / OUTPUT).write_bytes(data); "
        "written = {OUTPUT: sha256_bytes(data)}"),
    # the second computation
    one("B14C-always-same", C, "the comparison always reports equal bytes", CHK, "    if given == data:", "    if True:"),
    one("B14C-first-candidate", C, "two candidates: the first taken", CHK, "            if len(found) != 1:", "            if not found:"),
    one("B14C-kit-job-of-complete", C, "a kit unit's job_sha256 taken from COMPLETE.json", CHK,
        '                job = file_digest(folder / "job.json", f"{name} at {seed}: job.json")\n'
        '                origins[name][str(seed)] = {"block": block, "host": host, "job": index}',
        '                job = file_digest(folder / "COMPLETE.json", f"{name} at {seed}: job.json")\n'
        '                origins[name][str(seed)] = {"block": block, "host": host, "job": index}'),
    one("B14C-pin-check-off", C, "a pinned unit's files not compared with the pin", CHK,
        '                if (complete, job) != (item.get("complete_sha256"), item.get("job_sha256")):', "                if False:"),
    one("B14C-complete-check-off", C, "a kit unit's COMPLETE.json not compared with plan.json", CHK,
        '                if complete != record.get("complete_sha256"):', "                if False:"),
    one("B14C-not-pulled-counted", C, "a unit recorded complete but not pulled counted as a candidate", CHK,
        '(kind, name, seed, "complete") and job.get("pulled") is not False:', '(kind, name, seed, "complete"):'),
    one("B14C-not-done-counted", C, "a host that is not done searched", CHK,
        '        if record.get("block") not in blocks or record.get("done") is not True:',
        '        if record.get("block") not in blocks:'),
    one("B14C-any-block", C, "hosts of every block searched", CHK,
        '        if record.get("block") not in blocks or record.get("done") is not True:',
        '        if record.get("done") is not True:'),
    one("B14C-path-from-checkout", C, "paths relative to the data root's parent", CHK,
        "    rel = os.path.relpath(os.path.realpath(folder), os.path.realpath(data_root))",
        "    rel = os.path.relpath(os.path.realpath(folder), os.path.realpath(os.path.dirname(data_root)))"),
    one("B14C-indent-1", C, "the recomputed document serialized with indent 1", CHK,
        "    return (json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)",
        "    return (json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False, allow_nan=False)"),
    one("B14C-strata-hash-of-plan", C, "strata_sha256 taken of plan.json's bytes", CHK,
        '    strata_sha = hashlib.sha256(read(Path(strata), "the strata record")).hexdigest()',
        "    strata_sha = hashlib.sha256(plan_bytes).hexdigest()"),
    one("B14C-target-ignored", C, "a0's pins counted at every checkpoint (theta0's init pin too)", CHK,
        '                and pin.get("seed") == seed and pin.get("target") == CHECKPOINT]',
        '                and pin.get("seed") == seed]'),
    one("B14C-difference-unnamed", C, "the first difference not named", CHK,
        '    return None if (type(a), a) == (type(b), b) else (where.rstrip(".") or "the document")',
        '    return None if (type(a), a) == (type(b), b) else "the document"'),
    one("B14C-plan-code-off", C, "plan.json's plan code not checked", CHK,
        '    if ((plan.get("records") or {}).get("plan_ab") or {}).get("code") != code:', "    if False:"),
]
ids = {m["id"] for m in spec["mutants"]}
for m in new:
    assert m["id"] not in ids, m["id"]
    ids.add(m["id"])
    texts = {}
    for e in (m["edits"] if "edits" in m else [m]):
        text = texts.get(e["file"]) or (pkg / e["file"]).read_text()
        assert text.count(e["find"]) == 1, (m["id"], text.count(e["find"]), e["find"][:90])
        texts[e["file"]] = text.replace(e["find"], e["replace"])
# the six updated mutants' find texts too
for m in spec["mutants"]:
    texts = {}
    for e in (m["edits"] if "edits" in m else [m]):
        text = texts.get(e["file"]) or (pkg / e["file"]).read_text()
        assert text.count(e["find"]) == 1, ("existing", m["id"], text.count(e["find"]))
        texts[e["file"]] = text.replace(e["find"], e["replace"])
spec["mutants"].extend(new)
spec["d6_and_inputs"] = ("D-6 and the inputs writer (1 Nov 2026): the six re-pinned B14S mutants re-pinned to the D-6 "
                         f"settings ({pin[:8]}); {sum(m['id'].startswith('B14D6-') for m in new)} mutants of D-6 (ids "
                         f"B14D6-*), {sum(m['id'].startswith('B14I-') for m in new)} of the inputs writer (B14I-*) and "
                         f"{sum(m['id'].startswith('B14C-') for m in new)} of its second computation (B14C-*) added")
print(len(spec["mutants"]), "mutants;", len(new), "new;", repinned, "re-pinned;", spec["d6_and_inputs"])
if "--write" in sys.argv:
    spec_path.write_text(json.dumps(spec, indent=2) + "\n")
    print("written", hashlib.sha256(spec_path.read_bytes()).hexdigest())
