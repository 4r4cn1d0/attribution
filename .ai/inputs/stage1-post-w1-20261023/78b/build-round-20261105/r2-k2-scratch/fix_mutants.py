"""R2 K2 fix round: the verifier's surviving mutants (adapted where the code they mutated changed) and the fix's own
mutants, appended to tests/mutation_spec_scorer_78b.json; each find text checked to occur exactly once."""
import json, pathlib, sys
V = [  # (id, file, find, replace, describes) — the verifier's 16 survivors, ids kept
    ("V-part-design-always-full", "plan_tool.py", '    entry = {"design": "anchor_stopped" if stopped else "full",', '    entry = {"design": "full",', "the part names the full design on a stopped family (S-6)"),
    ("V-part-stop-record-dropped", "plan_tool.py", '    if stopped:\n        entry["anchor_stop"]', '    if False:\n        entry["anchor_stop"]', "the part omits the stop record (S-6)"),
    ("V-merge-stop-path-not-rebased", "plan_tool.py", '        refs += [entry["anchor_stop"]] if "anchor_stop" in entry else []', '        refs += []', "the stop record's path is not rebased"),
    ("V-planb-inputs-sha-unchecked", "plan_tool.py", '    if doc["inputs_sha256"] != plan_b["blinded_sigma_inputs_sha256"]:', '    if False:', "block B never compares the inputs hash"),
    ("V-planb-inputs-families-unchecked", "plan_tool.py", '    if data is None or data != kit_inputs(gate) or hashlib.sha256(data).hexdigest() != inputs_sha256:', '    if data is None or hashlib.sha256(data).hexdigest() != inputs_sha256:', "re-targeted (K2V-3 replaced the families check by the kit's rebuild): the inputs file need not be the kit's"),
    ("V-merge-gate-unchecked", "plan_tool.py", '    if doc["gate_sha256"] != gate_sha256:', '    if False:', "re-targeted to kit_part: a part of another gate is merged"),
    ("V-merge-family-set-unchecked", "plan_tool.py", '    for f in sorted(gate["families"]):\n        entry = json.loads', '    for f in sorted(gate["families"])[:1]:\n        entry = json.loads', "re-targeted to kit_inputs: the inputs file may cover fewer families than the gate"),
    ("V-release-planb-unchecked", "plan_tool.py", '    if block == "B" and r78.PLAN_B_78B["sha256"] != b["plan_b"]["sha256"]:', '    if False:', "release accepts another block-B plan record"),
    ("V-release-stop-donefile-unchecked", "plan_tool.py", '    if (stop or {}).get("job_done_sha256") != (b.get("anchor_stop") or {}).get("job_done_sha256"):', '    if False:', "release accepts another anchor JOB-DONE.json"),
    ("V-gate-record-sigma-f-llama", "plan_tool.py", '"sigma_F_plan": by_f[r78.GATE_OPTIONS["C"][0]] if option == "C" else None,', '"sigma_F_plan": by_f["llama31-8b"] if option == "C" else None,', "record-gate takes Llama's sigma_F plan under [C]"),
    ("V-gate-check-sigma-f-llama", "plan_tool.py", 'want = by_f[r78.GATE_OPTIONS["C"][0]] if gate_doc["option"] == "C" else None', 'want = by_f["llama31-8b"] if gate_doc["option"] == "C" else None', "init compares the gate with Llama's sigma_F plan"),
    ("V-sibling-seal-hash-unchecked", "plan_tool.py", ' or not p.is_file() or mac.sha(p) != seal.get("sha256"):', ' or not p.is_file():', "a sibling seal record off its SHA-256 passes"),
    ("V-arms-done-unpulled-ok", "plan_tool.py", '                if j.get("pulled") is False or not j.get("unit") or not SHA_RE.fullmatch(str(j.get("complete_sha256"))):', '                if not j.get("unit") or not SHA_RE.fullmatch(str(j.get("complete_sha256"))):', "re-targeted to block_a_cells (one check now serves arms-done and the part): an unpulled block-A job counts as done"),
    ("V-part-unpulled-ok", "plan_tool.py", '                    return {}, f"{name}:{i}: a block-A job is complete but not pulled with its unit"', '                    pass', "re-targeted to block_a_cells: the part names an unpulled unit"),
    ("V-part-two-engines-ok", "plan_tool.py", '            len(block_engines) != 1:', '            len(block_engines) < 1:', "block A on two engines passes"),
    ("V-states-kept-1104-only", "states_tool.py", 'KEPT_A0_SEEDS = (1104, 1105, 1106, 1107)', 'KEPT_A0_SEEDS = (1104,)', "only a0-1104's state is kept"),
]
F = [  # the fix round's own mutants
    ("K2F-m-status-unchecked", "R-43", "plan_tool.py", '    if (plan_b["sr2_adopted"], plan_b["sr2_reason"]) != (status["adopted"], status["reason"]):', '    if False:', "block B's plan record's SR-2 status is never compared with the pinned records'"),
    ("K2F-m-init-b-status-off", "R-43", "plan_tool.py", '        plan_b_status_check(plan_b_doc, gate_doc)        # GXB R-43: SR-2\'s status from the pinned records\n', '        pass\n', "block B's init takes the recorded SR-2 status"),
    ("K2F-m-release-b-status-off", "R-43", "plan_tool.py", '        plan_b_status_check(plan_b_doc, gate_doc)\n        if plan_b_doc["sr2_adopted"]:\n            kit_inputs_check(gate_doc, plan_b_doc["blinded_sigma_inputs_sha256"])\n    stop =', '        pass\n        if plan_b_doc["sr2_adopted"]:\n            kit_inputs_check(gate_doc, plan_b_doc["blinded_sigma_inputs_sha256"])\n    stop =', "block B's release takes the recorded SR-2 status"),
    ("K2F-m-snapshot-unchecked", "R-44", "plan_tool.py", '        if snap.get("sha256") != got["sha256"]:', '        if False:', "a blinding record no block-A copy read passes"),
    ("K2F-m-blinding-files-unchecked", "R-44", "plan_tool.py", '            if not here.is_file() or mac.sha(here) != files[rel]:', '            if not here.is_file():', "a verified file may differ from the one that runs"),
    ("K2F-m-blinding-form-files-free", "R-44", "plan_tool.py", '            not isinstance(files, dict) or sorted(files) != sorted(BLINDING_FILES) or \\\n', '            not isinstance(files, dict) or \\\n', "the blinding record may name other files"),
    ("K2F-m-blinding-commit-free", "R-44", "plan_tool.py", 'not COMMIT_RE.fullmatch(str(doc.get("commit")))', 'False', "the blinding record needs no commit"),
    ("K2F-m-init-a-no-blinding", "R-44", "plan_tool.py", '        blinding = sr2_blinding_reading(check_files=True)\n', '        blinding = None\n', "block A plans without the blinding record"),
    ("K2F-m-release-a-blinding-repin-ok", "R-44", "plan_tool.py", '        if got["sha256"] != (b.get("blinding") or {}).get("sha256"):', '        if False:', "block A's release accepts a re-pinned blinding record"),
    ("K2F-m-cells-two-units-ok", "K2V-2", "plan_tool.py", '                if key in cells:\n', '                if False:\n', "two complete units for one block-A run pass"),
    ("K2F-m-cells-open-job-ok", "K2V-2", "plan_tool.py", '            elif not (name in moved and carried(plan, name, j)):', '            elif False:', "an open block-A job that no move took counts as done"),
    ("K2F-m-cells-moved-skipped-wrongly", "K2V-2", "plan_tool.py", '            elif not (name in moved and carried(plan, name, j)):', '            elif not (name in moved):', "a moved host's job counts though no move took it"),
    ("K2F-m-kit-part-bytes-unchecked", "K2V-3", "plan_tool.py", '    if not p.is_file() or p.read_bytes() != rules.canonical_bytes(doc):', '    if not p.is_file():', "a hand-made part at the part's place is merged"),
    ("K2F-m-init-b-kit-inputs-off", "K2V-3", "plan_tool.py", '        if plan_b_doc["sr2_adopted"]:                    # K2V-3: the inputs are the kit\'s\n            kit_inputs_check(', '        if False:\n            kit_inputs_check(', "block B's init takes any inputs file"),
    ("K2F-m-orch-branch-unread", "R-45", "orchestrate.py", '        problem = rules.r78.bank500_problem(family, j["kind"], h.get("block"), data)\n', '        problem = None\n', "the orchestrator never holds a 500-bank pod"),
    ("K2F-m-orch-bytes-never-read", "R-45", "orchestrate.py", '        data = (ROOT / pin["path"]).read_bytes()\n', '        data = None\n', "the orchestrator holds every 500-bank pod (the branch bytes never read)"),
    ("K2F-m-noise-sigma-unchecked", "K2V-9", "plan_tool.py", '    if derived != code:\n        fail(f"{what}: its seed rule', '    if False:\n        fail(f"{what}: its seed rule', "a noise plan its own sigma contradicts passes"),
    ("K2F-m-noise-pooled-unchecked", "K2V-9", "plan_tool.py", '    if doc.get("seed_rule") != (doc.get("pooled") or {}).get("seed_rule"):', '    if False:', "a seed rule that is not the pooled reading's passes"),
    ("K2F-m-top-dose-ge", "K2V-7", "plan_tool.py", '    want = "s4_192" if kept >= r78.S4_KEEP else "s4_top"', '    want = "s4_192" if kept > r78.S4_KEEP else "s4_top"', "192 kept rows read as the fallback's top dose"),
    ("K2F-m-top-dose-96", "K2V-7", "plan_tool.py", '    want = "s4_192" if kept >= r78.S4_KEEP else "s4_top"', '    want = "s4_192" if kept >= r78.S4_KEEP else "s4_96" if kept == 96 else "s4_top"', "96 kept rows read as s4_96 (the defect)"),
    ("K2F-m-1b-commands-reachable", "K2V-10", "plan_tool.py", '    if a.command in BLOCK_A_1B_COMMANDS:', '    if False:', "the 1B block-A commands are reachable"),
    ("K2F-m-reason-any-text", "K2V-11", "plan_tool.py", '        if r.get("reason") is not None and r.get("reason") not in RUNNER_REASONS:', '        if False:', "record-done copies any reason text"),
]
kit = pathlib.Path(sys.argv[1])
texts, bad = {}, []
for m in V:
    t = texts.setdefault(m[1], (kit / m[1]).read_text())
    if t.count(m[2]) != 1: bad.append((m[0], t.count(m[2])))
for m in F:
    t = texts.setdefault(m[2], (kit / m[2]).read_text())
    if t.count(m[3]) != 1: bad.append((m[0], t.count(m[3])))
print(json.dumps({"verifier": len(V), "fix": len(F), "bad": bad}))
if "--write" in sys.argv and not bad:
    sp = kit / "tests" / "mutation_spec_scorer_78b.json"
    d = json.loads(sp.read_text()); ids = {m["id"] for m in d["mutants"]}
    for i, f, find, rep, desc in V:
        assert i not in ids
        d["mutants"].append({"id": i, "part": "K2V", "describes": desc + " (the K2 verifier's)", "file": f, "find": find, "replace": rep})
    for i, part, f, find, rep, desc in F:
        assert i not in ids
        d["mutants"].append({"id": i, "part": part, "describes": desc, "file": f, "find": find, "replace": rep})
    sp.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
    print("written", len(d["mutants"]))
