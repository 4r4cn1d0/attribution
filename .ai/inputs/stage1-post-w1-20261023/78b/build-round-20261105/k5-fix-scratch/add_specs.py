"""K5: append round 5's mutants to the kit's four specs (gated, runner, scorer; rules gets none), each find text
checked to occur exactly once in its file. Sources: the security re-verifier's hand_spec.json (H-*), the core
re-verifier's hm_spec.json (K4bcr-R*) and its prior spec (HM6, HM7, HM13), and K5's own."""
import json, pathlib, sys
kit = pathlib.Path(sys.argv[1])
B = pathlib.Path("/Users/spiderishi/Coding/attribution/.ai/inputs/stage1-post-w1-20261023/78b/build-round-20261105")
sec = {m["id"]: m for m in json.loads((B / "k4b-sec-scratch/hand_spec.json").read_text())["mutants"]}
core = {m["id"]: m for m in json.loads((B / "k4b-core-scratch/hm_spec.json").read_text())["mutants"]}
prior = {m["id"]: m for m in json.loads((B / "k4b-core-scratch/prior_hm_spec.json").read_text())["mutants"]}

def from_sec(i, part, killed_by=None):
    m = sec[i]; (find, replace), = m["edits"]
    out = {"id": f"K5-{i}", "part": part, "describes": m["describes"], "file": m["file"], "find": find, "replace": replace}
    if killed_by: out["killed_by"] = killed_by
    return out

def from_core(i, part, src=core, new_id=None):
    m = src[i]
    return {"id": new_id or i, "part": part, "describes": m["describes"], "file": m["file"], "find": m["find"], "replace": m["replace"]}

PW = "tests/test_pp10_process_wide.py"
GT = "tests/test_gated_78b.py::test_rv2_1_http_get_verifies_the_hubs_tls_certificate_and_host_name"
gated = [
    from_sec("H-d1-wrapper-skips-dgram", "K5 (sec R1)", PW + "::test_k4bf_d1_the_wrapper_refuses_sendto_sendmsg_and_inet6_before_any_resolution"),
    from_sec("H-d2-hook-daemon-threads-free", "K5 (sec R2)", PW + "::test_k4bf_d2_the_hook_refuses_in_a_non_main_thread_and_for_bytes_hosts"),
    from_sec("H-d2-hook-executor-threads-free", "K5 (sec R2)", PW + "::test_k4bf_d2_the_hook_refuses_in_a_non_main_thread_and_for_bytes_hosts"),
    from_sec("H-d3-default-open-mixin", "K5 (sec R3)", GT),
    from_sec("H-d3-https-request-downgrade", "K5 (sec R3)", GT),
    from_sec("H-d3-instance-https-open-unverified", "K5 (sec R3)", GT),
    from_sec("H-d3-connection-class-unverified", "K5 (sec R3)", GT),
    from_sec("H-d3-global-unverified-at-call", "K5 (sec R3)", GT),
]
RT = "tests/test_kit_78b_runner.py::test_k5_r5_"
runner = [
    from_sec("H-tok-verify-env-whole", "K5 (sec R5)", RT + "run_sc_job_and_verify_unit_give_the_scrubbed_offline_environment"),
    from_sec("H-tok-sc-steps-env-whole", "K5 (sec R5)", RT + "run_sc_job_and_verify_unit_give_the_scrubbed_offline_environment"),
    from_sec("H-tok-run-job-env-whole", "K5 (sec R5)", RT + "run_job_gives_every_step_and_the_verify_the_scrubbed_offline_environment"),
]
JR = "setup/job_runner_stage1.py"
scorer = [
    {"id": "K5-c0-fp-from-plan", "part": "K5 (core K4bcr-D1)", "describes": "c0 passes the plan's expect_fingerprint, not the packed source unit's",
     "file": JR, "find": "        expect = c0_fingerprint(root, ins[C0_SOURCE_INPUT], job, index)   # K5: from the packed source unit",
     "replace": "        expect = job[\"expect_fingerprint\"]"},
    {"id": "K5-c0-no-compare", "part": "K5 (core K4bcr-D1)", "describes": "c0 takes the packed fingerprint but never compares it with the plan's",
     "file": JR, "find": "    if got != job[\"expect_fingerprint\"]:\n", "replace": "    if False:\n"},
    {"id": "K5-c0-no-rehash", "part": "K5 (core K4bcr-D1)", "describes": "c0 reads the packed source unit without re-hashing it against its pin",
     "file": JR, "find": "    if not path.is_file() or path.is_symlink() or sha(path) != pin:\n        raise Unrunnable(f\"job {index} (c0)",
     "replace": "    if not path.is_file():\n        raise Unrunnable(f\"job {index} (c0)"},
    {"id": "K5-c0-no-e1-check", "part": "K5 (core K4bcr-D1)", "describes": "c0 does not refuse a source unit with no e1 adapter fingerprint by its own message",
     "file": JR, "find": "    if rules.hex64(got) is None:\n        raise Unrunnable(f\"job {index} (c0): the packed source unit's COMPLETE.json lists no e1",
     "replace": "    if False:\n        raise Unrunnable(f\"job {index} (c0): the packed source unit's COMPLETE.json lists no e1"},
    from_core("HM6", "K5 (core K4bcr-D2)", prior, "K5-HM6"),
    from_core("HM7", "K5 (core K4bcr-D2)", prior, "K5-HM7"),
    from_core("HM13", "K5 (core K4bcr-D2)", prior, "K5-HM13"),
    *[from_core(i, "K5 (core K4bcr-D3)") for i in ("K4bcr-R1", "K4bcr-R6", "K4bcr-R7", "K4bcr-R8", "K4bcr-R9", "K4bcr-R13",
                                                   "K4bcr-R17", "K4bcr-R21")],
    from_sec("H-pack-setup-tar-scan-dropped", "K5 (sec R4)"),
    from_sec("H-pack-payload-scan-dropped", "K5 (sec R4)"),
    from_sec("H-pack-bootstrap-scan-dropped", "K5 (sec R4)"),
    from_sec("H-pack-engine-files-unscanned", "K5 (sec R4)"),
    from_sec("H-pack-scripts-unscanned", "K5 (sec R4)"),
    {"id": "K5-pack-edits-unscanned", "part": "K5 (sec R4)", "describes": "the pack skips edits/ again (round 4b's prefixes)",
     "file": "pack_setup.py", "find": "DATA_PREFIXES = (f\"{DATA}/\", \"inputs/\")\n",
     "replace": "DATA_PREFIXES = (f\"{DATA}/\", \"inputs/\", \"edits/\")\n"},
    {"id": "K5-pack-data-scanned", "part": "K5 (sec R4)", "describes": "the pack scans the prepared set under data/ (against the lead's ruling)",
     "file": "pack_setup.py", "find": "DATA_PREFIXES = (f\"{DATA}/\", \"inputs/\")\n", "replace": "DATA_PREFIXES = (\"inputs/\",)\n"},
]
bad = []
for spec_name, new in (("mutation_spec_gated_78b.json", gated), ("mutation_spec_runner_78b.json", runner),
                       ("mutation_spec_scorer_78b.json", scorer)):
    path = kit / "tests" / spec_name
    doc = json.loads(path.read_text())
    ids = {m["id"] for m in doc["mutants"]}
    for m in new:
        n = (kit / m["file"]).read_text().count(m["find"])
        if n != 1 or m["id"] in ids or m["find"] == m["replace"]:
            bad.append((spec_name, m["id"], n))
        ids.add(m["id"])
    if not bad:
        doc["mutants"] += new
        doc["note"] = doc.get("note", "") + f" K5 (round 5) added {len(new)} mutants ({new[0]['id']} ... {new[-1]['id']})."
        path.write_text(json.dumps(doc, indent=1) + "\n")
    print(spec_name, len(doc["mutants"]), "added" if not bad else "NOT WRITTEN", len(new))
print("bad:", bad)
sys.exit(1 if bad else 0)
