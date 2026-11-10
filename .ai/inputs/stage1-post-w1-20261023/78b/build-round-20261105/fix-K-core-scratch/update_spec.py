"""fix-K-core: update tests/mutation_spec_rules_78b.json (stdlib): re-target two find texts that the PP8 edit moved and
add the fix round's mutants (ids FK-m-*). Run once: PY2 -I -B update_spec.py SPEC_PATH."""
import json
import pathlib
import sys

spec_path = pathlib.Path(sys.argv[1])
spec = json.loads(spec_path.read_text(encoding="utf-8"))
by_id = {m["id"]: m for m in spec["mutants"]}

# PP8 moved these two lines; the mutation is the same.
by_id["T2-m-rep-pass-17"].update({
    "describes": "A1's cap 16.5 -> 17.0 h (PP8: the kind is a1_pass; same mutation)",
    "find": "A1_PASS_CAP_H_MAX = 16.5 ",
    "replace": "A1_PASS_CAP_H_MAX = 17.0 "})
by_id["T2-m-s78-kinds-empty"].update({
    "find": 'S78_KINDS = frozenset({"retrain", "rep_pass", "a1_pass", "classifier"})',
    "replace": "S78_KINDS = frozenset()"})

new = [
    {"id": "FK-m-s78-kinds-no-classifier", "part": "PP8 (PP4)",
     "describes": "the classifier leaves the S_78 kinds (runs under the main recipe)",
     "file": "rules_78b.py",
     "find": 'S78_KINDS = frozenset({"retrain", "rep_pass", "a1_pass", "classifier"})',
     "replace": 'S78_KINDS = frozenset({"retrain", "rep_pass", "a1_pass"})'},
    {"id": "FK-m-s78-kinds-no-a1-pass", "part": "PP8 (PP3)",
     "describes": "a1_pass leaves the S_78 kinds",
     "file": "rules_78b.py",
     "find": 'S78_KINDS = frozenset({"retrain", "rep_pass", "a1_pass", "classifier"})',
     "replace": 'S78_KINDS = frozenset({"retrain", "rep_pass", "classifier"})'},
    {"id": "FK-m-rep-pass-takes-a1-window", "part": "PP8",
     "describes": "rep_pass takes A1's 16.5 h window instead of its own E cap",
     "file": "rules_78b.py",
     "find": '        upper = WIDE_CAP_FACTOR * size * STAGE1_1B_ESTIMATES_S["rep_pass"]\n',
     "replace": '        upper = A1_PASS_CAP_H_MAX * 3600 - POD_OVERHEAD_S - START_MARGIN_S\n'},
    {"id": "FK-m-rep-pass-no-size-factor", "part": "PP8",
     "describes": "rep_pass's E cap drops the scorer-kind size factor 2.3",
     "file": "rules_78b.py",
     "find": '        upper = WIDE_CAP_FACTOR * size * STAGE1_1B_ESTIMATES_S["rep_pass"]\n',
     "replace": '        upper = WIDE_CAP_FACTOR * STAGE1_1B_ESTIMATES_S["rep_pass"]\n'},
    {"id": "FK-m-a1-pass-takes-rep-pass-cap", "part": "PP8 (KD6)",
     "describes": "a1_pass loses A1's 16.5 h window and takes the 1B-estimate cap",
     "file": "rules_78b.py",
     "find": "        upper = A1_PASS_CAP_H_MAX * 3600 - POD_OVERHEAD_S - START_MARGIN_S\n",
     "replace": '        upper = WIDE_CAP_FACTOR * size * STAGE1_1B_ESTIMATES_S["rep_pass"]\n'},
    {"id": "FK-m-scorer-kinds-no-a1-pass", "part": "PP8 (M3)",
     "describes": "the need printout's scorer table drops a1_pass",
     "file": "rules_78b.py",
     "find": 'SCORER_KINDS = ("untuned_answers", "o_only", "anchor", "rep_pass", "a1_pass", "l1_scan", "classifier", "c0")',
     "replace": 'SCORER_KINDS = ("untuned_answers", "o_only", "anchor", "rep_pass", "l1_scan", "classifier", "c0")'},
    {"id": "FK-m-r-edits-any-family", "part": "D1 (the core verifier's V-H17, re-targeted)",
     "describes": "block0_r_edits takes any family's edit entry with a block-0 draw (Gate B's M edits at draws 1-2)",
     "file": "rules_78b.py",
     "find": '        if not sealed_edit_entry(e) or e.get("family") != "R":\n',
     "replace": '        if not sealed_edit_entry(e):\n'},
    {"id": "FK-m-r-edits-seed-unchecked", "part": "D1",
     "describes": "a Llama-form seed that is not 1100 + d passes",
     "file": "rules_78b.py",
     "find": "        if seed != R_SEED_BASE + d:\n",
     "replace": "        if False:\n"},
    {"id": "FK-m-r-edits-duplicate-passes", "part": "D1",
     "describes": "a draw listed twice silently takes the last entry",
     "file": "rules_78b.py",
     "find": "        if d in out:\n            raise Refused",
     "replace": "        if False:\n            raise Refused"},
    {"id": "FK-m-r-edits-missing-passes", "part": "D1",
     "describes": "a missing block-0 draw passes (the caller gets fewer edits)",
     "file": "rules_78b.py",
     "find": "    missing = [d for d in draws if d not in out]\n    if missing:\n        raise Refused(f\"the sealed set's MANIFEST lists no R edit",
     "replace": "    missing = []\n    if missing:\n        raise Refused(f\"the sealed set's MANIFEST lists no R edit"},
    {"id": "FK-m-edit-entry-any-path", "part": "D1",
     "describes": "an entry outside edits/ counts as an edit (a sample file at an R draw would duplicate R_d1)",
     "file": "rules_78b.py",
     "find": "    if not (isinstance(role, str) and role) or not (isinstance(path, str) and EDIT_PATH_RE.match(path)):\n",
     "replace": "    if not (isinstance(role, str) and role) or not isinstance(path, str):\n"},
    {"id": "FK-m-edit-entry-role-edit-only", "part": "D1 (the defect itself)",
     "describes": "only role == 'edit' entries are edits (the committed Llama form is refused again)",
     "file": "rules_78b.py",
     "find": "    if not (isinstance(role, str) and role) or not (isinstance(path, str) and EDIT_PATH_RE.match(path)):\n",
     "replace": "    if role != \"edit\" or not (isinstance(path, str) and EDIT_PATH_RE.match(path)):\n"},
    {"id": "FK-m-llama-pin-null", "part": "PP7",
     "describes": "the Llama sealed set's pin falls back to null",
     "file": "rules_78b.py",
     "find": '                   "sha256": "2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c"},\n}',
     "replace": '                   "sha256": None},\n}'},
    {"id": "FK-m-idle-running-rate", "part": "D2 (KD5; KCR:161)",
     "describes": "idle storage at the running volume rate ($0.10 per GB per month)",
     "file": "rules_78b.py",
     "find": "IDLE_STORAGE_USD_PER_GB_MONTH = 0.20 ",
     "replace": "IDLE_STORAGE_USD_PER_GB_MONTH = 0.10 "},
    {"id": "FK-m-idle-not-in-report", "part": "D2 (KD5)",
     "describes": "block0_report drops the idle-storage block",
     "file": "rules_78b.py",
     "find": '           "idle_storage": idle_storage(len(pods)), "retrain_pods": {}, "scorer_pods": {}}',
     "replace": '           "idle_storage": None, "retrain_pods": {}, "scorer_pods": {}}'},
    {"id": "FK-m-idle-per-pod-only", "part": "D2 (KD5)",
     "describes": "the idle-storage line counts one pod whatever the block holds",
     "file": "rules_78b.py",
     "find": '           "idle_storage": idle_storage(len(pods)), "retrain_pods": {}, "scorer_pods": {}}',
     "replace": '           "idle_storage": idle_storage(1), "retrain_pods": {}, "scorer_pods": {}}'},
]
for m in new:
    assert m["id"] not in by_id, m["id"]
spec["mutants"].extend(new)
spec["note"] += (" fix-K-core (5 Nov): PP8 moved two find texts (T2-m-rep-pass-17 -> A1_PASS_CAP_H_MAX; T2-m-s78-kinds-empty's"
                 " four-kind literal; same mutations); 16 mutants added (ids FK-m-*) for D1 (both MANIFEST forms;"
                 " V-H17 re-targeted as FK-m-r-edits-any-family), D2 (the idle-storage line), PP7 (the Llama pin) and PP8"
                 " (a1_pass, rep_pass, the S_78 kinds).")
spec_path.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(spec["mutants"]), "mutants")
