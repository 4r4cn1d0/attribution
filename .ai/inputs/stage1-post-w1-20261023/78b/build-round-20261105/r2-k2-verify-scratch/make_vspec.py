import json, sys
M = [
 ("V-part-design-always-full", "plan_tool.py", '    entry = {"design": "anchor_stopped" if stopped else "full",', '    entry = {"design": "full",', "the part names the full design on a stopped family (S-6)"),
 ("V-part-stop-record-dropped", "plan_tool.py", '    if stopped:\n        entry["anchor_stop"]', '    if False:\n        entry["anchor_stop"]', "the part omits the stop record (S-6)"),
 ("V-merge-stop-path-not-rebased", "plan_tool.py", '        refs += [entry["anchor_stop"]] if "anchor_stop" in entry else []', '        refs += []', "the stop record's path is not rebased"),
 ("V-planb-inputs-sha-unchecked", "plan_tool.py", '    if doc["inputs_sha256"] != plan_b["blinded_sigma_inputs_sha256"]:', '    if False:', "block B never compares the inputs hash"),
 ("V-planb-inputs-families-unchecked", "plan_tool.py", 'sorted(inputs.get("families") or {}) != sorted(gate["families"])', 'False', "record-plan-b takes an inputs file of other families"),
 ("V-merge-gate-unchecked", "plan_tool.py", 'doc.get("gate_sha256") != r78.GATE_78B["sha256"]', 'False', "a part of another gate is merged"),
 ("V-release-planb-unchecked", "plan_tool.py", '    if block == "B" and r78.PLAN_B_78B["sha256"] != b["plan_b"]["sha256"]:', '    if False:', "release accepts another block-B plan record"),
 ("V-release-stop-donefile-unchecked", "plan_tool.py", '    if (stop or {}).get("job_done_sha256") != (b.get("anchor_stop") or {}).get("job_done_sha256"):', '    if False:', "release accepts another anchor JOB-DONE.json"),
 ("V-gate-record-sigma-f-llama", "plan_tool.py", '"sigma_F_plan": by_f[r78.GATE_OPTIONS["C"][0]] if option == "C" else None,', '"sigma_F_plan": by_f["llama31-8b"] if option == "C" else None,', "record-gate takes Llama's sigma_F plan under [C]"),
 ("V-gate-check-sigma-f-llama", "plan_tool.py", 'want = by_f[r78.GATE_OPTIONS["C"][0]] if gate_doc["option"] == "C" else None', 'want = by_f["llama31-8b"] if gate_doc["option"] == "C" else None', "init compares the gate with Llama's sigma_F plan"),
 ("V-sibling-seal-hash-unchecked", "plan_tool.py", ' or not p.is_file() or mac.sha(p) != seal.get("sha256"):', ' or not p.is_file():', "a sibling seal record off its SHA-256 passes"),
 ("V-c0-fingerprint-unchecked", "plan_tool.py", 'if not SHA_RE.fullmatch(str(got)) or got != (values.get("C0_SOURCE") or {}).get("e1_fingerprint"):', 'if not SHA_RE.fullmatch(str(got)):', "c0's release check reads but never compares the fingerprint"),
 ("V-arms-done-unpulled-ok", "plan_tool.py", 'all(j.get("status") == "complete" and j.get("pulled") is not False for h in hosts for j in h["jobs"])', 'all(j.get("status") == "complete" for h in hosts for j in h["jobs"])', "an unpulled block-A job counts as done"),
 ("V-part-unpulled-ok", "plan_tool.py", '            if j.get("status") != "complete" or j.get("pulled") is False or not j.get("unit") or', '            if j.get("status") != "complete" or not j.get("unit") or', "the part names an unpulled unit"),
 ("V-part-two-engines-ok", "plan_tool.py", '            len(block_engines) != 1:', '            len(block_engines) < 1:', "block A on two engines passes"),
 ("V-branch-units-count-free", "plan_tool.py", '        if len(units) != len(r78.w1_18_units(family)):', '        if len(units) < 1:', "a W1-18 record over fewer units makes a branch"),
 ("V-planb-plan-vs-sigma-unchecked", "plan_tool.py", '    if r78.plan_for_sigma(doc["sigma_A_pp"]) != plan_b["plan"]:', '    if False:', "block B's plan need not be sigma_A's (RK checks it too)"),
 ("V-merge-family-set-unchecked", "plan_tool.py", '    if sorted(families) != sorted(gate["families"]):', '    if not families:', "the inputs file may cover fewer families than the gate"),
 ("V-seal-copies-only-block0", "seal.py", 'COPY_SEALS = {"A": ("0", "sc")}', 'COPY_SEALS = {"A": ("0",)}', "block A's seal names block 0's seal only"),
 ("V-states-kept-1104-only", "states_tool.py", 'KEPT_A0_SEEDS = (1104, 1105, 1106, 1107)', 'KEPT_A0_SEEDS = (1104,)', "only a0-1104's state is kept"),
]
src = sys.argv[1]
out = {"kind": "verifier probe mutants (K2V)", "note": "scratch only", "mutants": []}
for i, f, find, repl, d in M:
    text = open(f"{src}/{f}").read()
    n = text.count(find)
    assert n == 1, (i, n)
    out["mutants"].append({"id": i, "part": "K2V", "describes": d, "file": f, "find": find, "replace": repl})
json.dump(out, open(sys.argv[2], "w"), indent=1)
print(len(out["mutants"]))
