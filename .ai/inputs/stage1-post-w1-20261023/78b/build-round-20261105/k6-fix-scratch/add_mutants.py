"""K6: append this round's mutants to the kit's mutation specs (idempotent: refuses an id already present; checks
that each find text occurs exactly once in its target file). Usage: PY -B -I add_mutants.py KIT_DIR HM_SPEC"""
import json
import pathlib
import sys

kit, hm = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
hm_by_id = {m["id"]: m for m in json.loads(hm.read_text())["mutants"]}
P = "K6 (round 6)"


def from_hm(mid, killed_by=None):
    m = hm_by_id[mid]
    out = {"id": mid, "part": P + ", the K5 re-verifier's " + m["item"], "describes": m["describes"],
           "file": m["file"], "find": m["find"], "replace": m["replace"]}
    if killed_by:
        out["killed_by"] = killed_by
    return out


SCORER = "tests/test_scorer_block_78b.py::"
GATED = "tests/test_gated_78b.py::"
PW = "tests/test_pp10_process_wide.py::"
RUNNER = "tests/test_kit_78b_runner.py::"
BUNDLE_CALL = ('    refuse_secrets(files, {**payload, "probe.json": probe_json, rules.KIT_FAMILY_FILE: family_json}, DATA_PREFIXES,\n'
               '                   frozenset(f"{data_base}/{rel}" for rel in data_scan))\n')
new = {
 "mutation_spec_scorer_78b.json": [
  from_hm("K5v-D1c-link-accepted"),
  from_hm("K5v-R21-no-e1-checkpoint-accepted"),
  {"id": "K5v-R4-call-site-skips-edits", "part": P + ", K5v-6",
   "describes": "the bundle's scan is called with edits/ among the skipped prefixes (the constant DATA_PREFIXES unchanged)",
   "file": "pack_setup.py", "find": BUNDLE_CALL,
   "replace": BUNDLE_CALL.replace("family_json}, DATA_PREFIXES,", "family_json}, (*DATA_PREFIXES, \"edits/\"),")},
  {"id": "K6-pack-unlisted-data-not-scanned", "part": P + ", K5v-3",
   "describes": "the bundle's scan is not given the prepared set's unpinned files (scan_anyway dropped at the call site)",
   "file": "pack_setup.py", "find": BUNDLE_CALL,
   "replace": '    refuse_secrets(files, {**payload, "probe.json": probe_json, rules.KIT_FAMILY_FILE: family_json}, DATA_PREFIXES)\n'},
  {"id": "K6-refuse-ignores-scan-anyway", "part": P + ", K5v-3",
   "describes": "refuse_secrets skips every file under the skipped prefixes, scan_anyway or not",
   "file": "pack_setup.py",
   "find": "    scanned = [f for name, f in files.items() if not name.startswith(data_prefixes) or name in scan_anyway]\n",
   "replace": "    scanned = [f for name, f in files.items() if not name.startswith(data_prefixes)]\n"},
  {"id": "K6-macos-metadata-packed", "part": P + ", K5v-3",
   "describes": "a macOS metadata file is packed (unscanned) instead of skipped",
   "file": "pack_setup.py",
   "find": "        elif macos_metadata(rel):\n            skipped.append(rel)\n",
   "replace": "        elif macos_metadata(rel):\n            skipped.append(rel)\n            packed[rel] = (f, got)\n"},
  {"id": "K6-macos-metadata-every-dotfile", "part": P + ", K5v-3",
   "describes": "every file whose name starts with '.' counts as macOS metadata (skipped unscanned)",
   "file": "pack_setup.py",
   "find": "    return any(part in MACOS_METADATA or part.startswith(\"._\") for part in rel.split(\"/\"))\n",
   "replace": "    return any(part in MACOS_METADATA or part.startswith(\".\") for part in rel.split(\"/\"))\n"},
  {"id": "K6-listed-hash-not-checked", "part": P + ", K5v-3",
   "describes": "a file the manifest lists stays outside the scan whatever its bytes",
   "file": "pack_setup.py", "find": "        if listed.get(rel) == got:\n", "replace": "        if rel in listed:\n"},
  {"id": "K6-manifest-pin-not-checked", "part": P + ", K5v-3",
   "describes": "manifest.json's list is trusted even when manifest.json is not at the family's pin",
   "file": "pack_setup.py", "find": "        if hashlib.sha256(data).hexdigest() == digest:\n", "replace": "        if True:\n"},
  {"id": "K6-listed-files-scanned", "part": P + ", K5v-3",
   "describes": "the manifest-listed files are scanned too (against the ruling)",
   "file": "pack_setup.py", "find": "        if listed.get(rel) == got:\n            packed[rel] = (f, got)\n",
   "replace": "        if listed.get(rel) == got:\n            packed[rel] = (f, got)\n            scan.add(rel)\n"},
  {"id": "K6-c0-pack-check-removed", "part": P + ", item 23",
   "describes": "the pack does not check the c0 source unit's e1 fingerprint against C0_SOURCE",
   "file": "pack_setup.py", "find": "    if C0_INPUT in named:", "replace": "    if False:"},
  {"id": "K6-c0-pack-reads-q", "part": P + ", item 23",
   "describes": "the pack's c0 check reads the q checkpoint's fingerprint instead of e1's",
   "file": "pack_setup.py",
   "find": "    e1 = points.get(\"e1\") if isinstance(points.get(\"e1\"), dict) else {}\n    got = e1.get(\"adapter_fingerprint\")\n    if not pinned(got):\n        raise SystemExit(f\"--inputs FILE: {C0_INPUT!r}",
   "replace": "    e1 = points.get(\"q\") if isinstance(points.get(\"q\"), dict) else {}\n    got = e1.get(\"adapter_fingerprint\")\n    if not pinned(got):\n        raise SystemExit(f\"--inputs FILE: {C0_INPUT!r}"},
  {"id": "K6-c0-pack-compares-complete-sha", "part": P + ", item 23",
   "describes": "the pack's c0 check compares the fingerprint with C0_SOURCE's complete_sha256",
   "file": "pack_setup.py", "find": "    if got != c0.get(\"e1_fingerprint\"):\n",
   "replace": "    if got != c0.get(\"complete_sha256\"):\n"},
  {"id": "K6-c0-pack-missing-fp-not-named", "part": P + ", item 23",
   "describes": "a source unit with no e1 fingerprint is not refused as such (only the comparison remains)",
   "file": "pack_setup.py",
   "find": "    if not pinned(got):\n        raise SystemExit(f\"--inputs FILE: {C0_INPUT!r} (c0's source unit) lists no e1 adapter fingerprint\")\n",
   "replace": ""},
  {"id": "K6-c0-pack-unreadable-as-empty", "part": P + ", item 23",
   "describes": "a source unit that is not JSON is read as an empty document",
   "file": "pack_setup.py",
   "find": "    except ValueError:\n        raise SystemExit(f\"--inputs FILE: {C0_INPUT!r} (c0's source unit) is not a readable COMPLETE.json\") from None\n",
   "replace": "    except ValueError:\n        doc = {}\n"},
 ],
 "mutation_spec_gated_78b.json": [
  from_hm("K5v-G1-wrapper-skips-explicit-proto",
          PW + "test_k6_v3_the_wrapper_refuses_real_sockets_made_with_an_explicit_protocol"),
  from_hm("K5v-G2-hook-default-named-threads-free",
          PW + "test_k6_v4_the_hook_refuses_in_a_default_named_thread_and_in_a_raw_thread"),
  from_hm("K5v-G2-hook-dummy-threads-free",
          PW + "test_k6_v4_the_hook_refuses_in_a_default_named_thread_and_in_a_raw_thread"),
  from_hm("K5v-G3-redirect-keeps-token",
          GATED + "test_k6_v5_a_redirect_off_the_hub_through_the_whole_dispatch_drops_the_token"),
 ],
 "mutation_spec_runner_78b.json": [
  {"id": "K6-free-space-folders-collide", "part": P + ", K5v-9",
   "describes": "the free-space test's three worlds share one folder name (the flake's mechanism, now at every seed)",
   "file": "tests/test_kit_78b_runner.py", "find": "        w2 = rk.World(pod.w.repo / f\"w-{i}\", monkeypatch, w.family)\n",
   "replace": "        w2 = rk.World(pod.w.repo / \"w-0\", monkeypatch, w.family)\n",
   "killed_by": RUNNER + "test_the_free_space_check_refuses_a_job_that_would_not_fit_and_records_why"},
 ],
}
for spec_name, mutants in new.items():
    path = kit / "tests" / spec_name
    doc = json.loads(path.read_text())
    have = {m["id"] for m in doc["mutants"]}
    for m in mutants:
        assert m["id"] not in have, m["id"]
        n = (kit / m["file"]).read_text().count(m["find"])
        assert n == 1, (m["id"], n)
        doc["mutants"].append(m)
    path.write_text(json.dumps(doc, indent=1) + "\n")
    print(spec_name, len(doc["mutants"]), "(+", len(mutants), ")")
