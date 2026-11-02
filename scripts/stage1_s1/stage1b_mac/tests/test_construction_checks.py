"""The construction-check runner on the synthetic world: the run, the captured logs, the hash record, the inputs
resolved by path and SHA-256 (every refusal), a failed step and its reason line, and no sentinel in stdout, stderr,
a refusal or the record. The W1 stand-ins leak sentinels on request, so the capture is tested, not assumed. Every
stdout line must match the runner's line grammar (a head word, a name, a SHA-256; or a step's exit code)."""

from __future__ import annotations

import json
import re
import shutil

import pytest
import synth_world as sw

from scripts.stage1_s1.stage1b_mac import construction_checks as cc

HEX = re.compile(r"^[0-9a-f]{64}$")
# the whole stdout grammar: nothing else is printed (a test holds every line to it, on success and on failure)
OUT_LINE = re.compile(r"^(w1 scripts/stage1/[a-z0-9_]+\.py|input [a-z0-9_]+|output (datashield|l1|report)|record \S+)"
                      r" [0-9a-f]{64}$|^step (datashield|l1|report) exit -?\d+$")
FAILED = "FAILED: step {} exited {}; its log stays in the output folder (never opened); no record written"
WITHHELD = "reason: withheld (the step's last message is not a value-free refusal of the pinned W1 scripts)"


@pytest.fixture
def world(tmp_path):
    return sw.make(tmp_path)


def run(world, capsys, monkeypatch, env=None, **changes):
    for key, value in (env or {}).items():
        monkeypatch.setenv(key, value)
    code = cc.main(world.argv(**changes))
    captured = capsys.readouterr()
    assert not sw.sentinel_hits(captured.out) and not sw.sentinel_hits(captured.err), (captured.out, captured.err)
    for line in captured.out.splitlines():
        assert OUT_LINE.match(line), line
    return code, captured.out, captured.err


def test_the_run_writes_the_three_outputs_and_a_text_free_record(world, capsys, monkeypatch):
    code, out, err = run(world, capsys, monkeypatch, env={"FAKE_LEAK": "1"})
    assert code == 0 and err == ""
    lines = out.splitlines()
    assert [l for l in lines if l.startswith("step ")] == ["step datashield exit 0", "step l1 exit 0", "step report exit 0"]
    assert [l.split()[1] for l in lines if l.startswith("w1 ")] == list(cc.W1_SCRIPTS)
    record = json.loads(world.record_out.read_bytes())
    assert not sw.sentinel_hits(world.record_out.read_text())
    assert record["kind"] == cc.RECORD_KIND and record["report_without_counted"] is True
    for name, file in (("datashield", "datashield/datashield_scores.json"), ("l1", "l1/l1_scores.json"),
                       ("report", "report/plant_ranks.json")):
        path = world.out / file
        assert record["outputs"][name] == {"file": file, "sha256": sw.sha(path.read_bytes())}
        assert f"output {name} {record['outputs'][name]['sha256']}" in lines
    assert "--counted" not in record["commands"]["report"] and record["commands"]["report"][0].endswith(cc.REPORT_SCRIPT)
    assert record["inputs"]["rows"] == world.pod["rows"][1] and record["inputs"]["seal"] == world.seal_sha256
    assert record["inputs"]["plant_record"] == world.req8_sha256 and record["inputs"]["plant_pool"] == world.pools["plant"][1]
    assert record["inputs"]["decoy_pool"] == world.pools["decoy"][1] and record["inputs"]["man1"] == world.man1_sha256
    assert record["inputs"]["rules"] == sw.sha(world.rules.read_bytes()) and record["rules_pinned"] is False
    assert record["pod_paths"]["rows"] == f"{sw.HOST}:job-0/representation/representation_rows.jsonl"
    assert record["w1_scripts"][cc.REPORT_SCRIPT] == world.scripts["report"]
    assert record["w1_tree"]["entries"] == world.w1_tree_entries and record["w1_tree"]["roles"] == list(cc.W1_ROLES)
    assert HEX.match(record["w1_tree"]["sha256"]) and record["inputs"]["w1_tree"] == record["w1_tree"]["sha256"]
    assert [s["made_here"] for s in record["steps"]] == [True, True, True]
    # the stand-ins leaked sentinels: they are in the logs inside the "plant" folder and nowhere else
    logs = {p.name: p.read_text() for p in (world.out / "log").iterdir()}
    assert set(logs) == {"datashield.log", "l1.log", "report.log"}
    assert all(sw.sentinel_hits(text) for text in logs.values())
    # the report's output names the unit and leaf (as the real one does): it stays in the folder, unopened here
    assert sw.sentinel_hits((world.out / "report" / "plant_ranks.json").read_text())


def test_given_scorer_outputs_are_used_and_only_the_report_runs(world, capsys, monkeypatch, tmp_path):
    first = sw.make(tmp_path / "first")
    assert cc.main(first.argv()) == 0
    capsys.readouterr()
    l1 = first.out / "l1" / "l1_scores.json"
    ds = first.out / "datashield" / "datashield_scores.json"
    code, out, err = run(world, capsys, monkeypatch, l1=f"{l1}:{sw.sha(l1.read_bytes())}",
                         datashield=f"{ds}:{sw.sha(ds.read_bytes())}")
    assert code == 0
    assert [l for l in out.splitlines() if l.startswith("step ")] == ["step report exit 0"]
    record = json.loads(world.record_out.read_bytes())
    assert [(s["step"], s["made_here"]) for s in record["steps"]] == [("datashield", False), ("l1", False), ("report", True)]
    assert record["inputs"]["l1_given"] == sw.sha(l1.read_bytes()) and "l1" not in record["outputs"]
    assert set((world.out / "log").iterdir()) == {world.out / "log" / "report.log"}
    assert f"--l1" in record["commands"]["report"] and f"{l1}:{sw.sha(l1.read_bytes())}" in record["commands"]["report"]


def test_a_failed_step_stops_the_run_and_withholds_a_reason_that_holds_a_value(world, capsys, monkeypatch):
    code, out, err = run(world, capsys, monkeypatch, env={"FAKE_FAIL": "l1"})
    assert code == 1
    assert [l for l in out.splitlines() if l.startswith("step ")] == ["step datashield exit 0", "step l1 exit 2"]
    assert err.splitlines() == [FAILED.format("l1", 2), WITHHELD]
    assert not world.record_out.exists() and world.record_out.parent.is_dir()   # the record's folder was made first
    assert sw.sentinel_hits((world.out / "log" / "l1.log").read_text())        # the stand-in's refusal went to the log only
    assert not (world.out / "report").exists()


def test_a_failed_step_with_a_value_free_refusal_prints_that_line_only(world, capsys, monkeypatch):
    """The stand-in leaks sentinels on stdout and stderr first, then refuses with one string literal of its pinned
    source: the refusal line is printed, the leaked lines stay in the log."""
    code, out, err = run(world, capsys, monkeypatch, env={"FAKE_FAIL_FIXED": "report", "FAKE_LEAK": "1"})
    assert code == 1
    assert err.splitlines() == [FAILED.format("report", 2),
                                "reason: REFUSED: the rows file is not the one the summary names (nothing written)"]
    log = (world.out / "log" / "report.log").read_text()
    assert sw.sentinel_hits(log) and "the rows file is not the one the summary names" in log
    assert not world.record_out.exists()


def test_a_step_that_prints_bytes_that_are_not_utf8_still_runs_and_is_logged(world, capsys, monkeypatch):
    code, out, err = run(world, capsys, monkeypatch, env={"FAKE_RAW": "1"})
    assert code == 0 and err == ""
    assert b"raw \xff\xfe bytes" in (world.out / "log" / "datashield.log").read_bytes()


def test_an_output_that_differs_from_the_printed_hash_stops_the_run(world, capsys, monkeypatch):
    code, out, err = run(world, capsys, monkeypatch, env={"FAKE_BAD_HASH": "report"})
    assert code == 1 and err.startswith("FAILED: step report left no output at the SHA-256 it printed")
    assert not world.record_out.exists()
    assert "output report" not in out


def refused(world, capsys, monkeypatch, message, **changes):
    code, out, err = run(world, capsys, monkeypatch, **changes)
    assert code == 2, (code, out, err)
    assert err.strip() == f"REFUSED: {message}", err
    assert not world.record_out.exists() and not world.record_out.parent.exists()
    assert not world.out.exists() or not any(world.out.iterdir())        # nothing written
    assert out == ""


def test_refuses_an_output_folder_whose_name_lacks_the_protected_word(world, capsys, monkeypatch, tmp_path):
    refused(world, capsys, monkeypatch, "the output folder's name does not hold the word the path rule protects",
            out=tmp_path / "checks")


def test_refuses_a_non_empty_output_folder(world, capsys, monkeypatch):
    world.out.mkdir()
    (world.out / "old.txt").write_text("x")
    code = cc.main(world.argv())
    err = capsys.readouterr().err
    assert code == 2 and err.strip() == "REFUSED: the output folder exists and is not empty"
    assert list(world.out.iterdir()) == [world.out / "old.txt"]


def test_refuses_an_existing_hash_record(world, capsys, monkeypatch):
    world.record_out.parent.mkdir(parents=True)
    world.record_out.write_text("{}")
    code = cc.main(world.argv())
    assert code == 2 and capsys.readouterr().err.strip() == "REFUSED: the hash record exists: it is written once"
    assert world.record_out.read_text() == "{}" and not world.out.exists()


def test_refuses_a_record_path_holding_a_protected_word(world, capsys, monkeypatch):
    """A record inside the output folder is refused by the same rule: that folder's own name holds "plant"."""
    refused(world, capsys, monkeypatch, "the hash record's path holds a word the path rule protects",
            record=world.out / "record.json")
    refused(world, capsys, monkeypatch, "the hash record's path holds a word the path rule protects",
            record=world.out / "sub" / "record.json")
    for word in cc.PROTECTED_WORDS:
        refused(world, capsys, monkeypatch, "the hash record's path holds a word the path rule protects",
                record=world.root / f"{word}-records" / "hashes.json")
        refused(world, capsys, monkeypatch, "the hash record's path holds a word the path rule protects",
                record=world.root / "records" / f"{word.upper()}.json")


def test_refuses_a_record_folder_that_is_a_file(world, capsys, monkeypatch):
    world.record_out.parent.parent.mkdir(parents=True)
    world.record_out.parent.write_text("not a folder")
    code = cc.main(world.argv())
    assert code == 2 and capsys.readouterr().err.strip() == "REFUSED: the hash record's folder is not a folder"
    assert world.record_out.parent.read_text() == "not a folder" and not world.out.exists()


def test_refuses_a_prepared_path_that_is_not_a_folder(world, capsys, monkeypatch):
    refused(world, capsys, monkeypatch, "the prepared folder is not a folder", prepared=world.prepared / "manifest.json")


def test_refuses_a_rules_module_without_the_pins(world, capsys, monkeypatch):
    world.rules.write_text(world.rules.read_text().replace("D2_POOLS", "OTHER_POOLS"))
    refused(world, capsys, monkeypatch, "the rules module lacks a pin this runner needs")
    world.rules.write_text("nothing = 1\n")
    refused(world, capsys, monkeypatch, "the rules module lacks a pin this runner needs")


def test_the_rules_module_pin_is_checked_when_given(world, capsys, monkeypatch):
    digest = sw.sha(world.rules.read_bytes())
    refused(world, capsys, monkeypatch, "--expect-rules-sha256 is not 64 lowercase hex", expect_rules_sha256="abc")
    refused(world, capsys, monkeypatch, "the rules module does not hash to its expected SHA-256",
            expect_rules_sha256="0" * 64)
    code, out, err = run(world, capsys, monkeypatch, expect_rules_sha256=digest)
    assert code == 0 and f"input rules {digest}" in out.splitlines()
    record = json.loads(world.record_out.read_bytes())
    assert record["rules_pinned"] is True and record["inputs"]["rules"] == digest


def test_refuses_rules_pins_of_another_form(world, capsys, monkeypatch):
    text = world.rules.read_text()
    world.rules.write_text(text.replace(f'"decoy": "{world.pools["decoy"][1]}"', '"other": "x"'))
    refused(world, capsys, monkeypatch, "the rules module's pins are not of the expected form")
    world.rules.write_text(text.replace('"path": ', '"file": '))
    refused(world, capsys, monkeypatch, "the rules module's pins are not of the expected form")


def test_refuses_a_w1_manifest_off_its_pin(world, capsys, monkeypatch):
    path = world.repo / sw.MAN1_REL
    path.write_bytes(path.read_bytes() + b"\n")
    refused(world, capsys, monkeypatch, "the W1 manifest does not hash to its expected SHA-256")
    path.unlink()
    refused(world, capsys, monkeypatch, "the W1 manifest is missing or not a regular file")


def test_refuses_a_w1_script_that_differs_from_its_manifest_entry(world, capsys, monkeypatch):
    path = world.repo / sw.SCRIPTS["report"]
    path.write_bytes(path.read_bytes() + b"# changed\n")
    refused(world, capsys, monkeypatch, "a W1 script does not hash to its expected SHA-256")


def repin_manifest(world, change):
    """Apply ``change(man1_doc)``, rewrite the manifest and re-pin it in the rules module (the world stays consistent)."""
    path = world.repo / sw.MAN1_REL
    doc = json.loads(path.read_text())
    change(doc)
    sw.write(path, sw.jbytes(doc))
    world.man1_sha256 = sw.sha(path.read_bytes())
    world.rules.write_text(sw.rules_text(world.req8_sha256, world.pools, world.man1_sha256))


def test_refuses_a_manifest_without_a_code_entry_for_a_script(world, capsys, monkeypatch):
    def demote(doc):
        for e in doc["entries"]:
            if e["path"] == sw.SCRIPTS["l1"]:
                e["role"] = "settings"
    repin_manifest(world, demote)
    refused(world, capsys, monkeypatch, "the W1 manifest lists no code entry for a script this runner needs")

    def drop_helpers(doc):
        doc["entries"] = [e for e in doc["entries"] if e["path"] != sw.S1COMMON_REL]
    repin_manifest(world, drop_helpers)
    refused(world, capsys, monkeypatch, "the W1 manifest lists no code entry for a script this runner needs")


def test_every_w1_file_the_report_can_run_or_read_is_checked_against_its_manifest_entry(world, capsys, monkeypatch):
    """Code, settings and pinned inputs under scripts/stage1/ are re-hashed (the baseline world lists absent files of
    other roles, which are not checked); a changed settings file, a missing pinned input and an entry without a
    SHA-256 refuse."""
    settings = world.repo / sw.SETTINGS["datashield"]
    data = settings.read_bytes()
    settings.write_bytes(data + b"\n")
    refused(world, capsys, monkeypatch, "a W1 file does not hash to its expected SHA-256")
    settings.write_bytes(data)
    (world.repo / sw.PINNED_INPUT_REL).unlink()
    refused(world, capsys, monkeypatch, "a W1 file is missing or not a regular file")
    sw.write(world.repo / sw.PINNED_INPUT_REL, sw.jbytes({"terms": [sw.SENTINELS["text"]]}))

    def no_hash(doc):
        for e in doc["entries"]:
            if e["path"] == sw.SETTINGS["l1"]:
                e["sha256"] = sw.SENTINELS["text"]
    repin_manifest(world, no_hash)
    refused(world, capsys, monkeypatch, "a W1 manifest entry names no SHA-256")


def test_refuses_req8_record_or_a_pool_off_its_pin(world, capsys, monkeypatch):
    record = world.repo / sw.RECORD_REL
    record.write_bytes(record.read_bytes() + b" ")
    refused(world, capsys, monkeypatch, "REQ-8's record does not hash to its expected SHA-256")
    record.write_bytes(record.read_bytes()[:-1])
    refused(world, capsys, monkeypatch, "the plant pool does not hash to its expected SHA-256",
            plant_pool=world.pools["decoy"][0])
    refused(world, capsys, monkeypatch, "the decoy pool does not hash to its expected SHA-256",
            decoy_pool=world.pools["plant"][0])
    refused(world, capsys, monkeypatch, "the decoy pool is missing or not a regular file",
            decoy_pool=world.root / "pools" / "none.json")


def test_refuses_a_malformed_or_changed_given_scorer_output(world, capsys, monkeypatch):
    refused(world, capsys, monkeypatch, "--l1 is PATH:SHA256", l1="no-hash")
    path = world.root / "old_l1.json"
    path.write_text("{}")
    refused(world, capsys, monkeypatch, "--datashield does not hash to its expected SHA-256",
            datashield=f"{path}:{'a' * 64}")


def test_refuses_a_bad_or_different_seal_sha256(world, capsys, monkeypatch):
    refused(world, capsys, monkeypatch, "--expect-seal-sha256 is not 64 lowercase hex", expect_seal_sha256="abc")
    refused(world, capsys, monkeypatch, "plan.json records no seal of the block at the expected SHA-256",
            expect_seal_sha256="b" * 64)


def test_refuses_a_missing_plan_or_an_unsealed_block(world, capsys, monkeypatch):
    plan = sw.plan_of(world)
    del plan["seals"][sw.BLOCK]
    sw.save_plan(world, plan)
    refused(world, capsys, monkeypatch, "plan.json records no seal of the block at the expected SHA-256")
    (world.kit / "plan.json").unlink()
    refused(world, capsys, monkeypatch, "the kit's plan.json is missing or not a regular file")


def test_refuses_a_seal_file_that_differs_from_plan_json(world, capsys, monkeypatch):
    path = world.kit / "seals" / f"block-{sw.BLOCK}.json"
    path.write_bytes(path.read_bytes() + b"\n")
    refused(world, capsys, monkeypatch, "the block seal does not hash to its expected SHA-256")


def test_refuses_a_seal_record_of_another_kind_or_block(world, capsys, monkeypatch):
    sw.reseal(world, lambda doc: doc.update(block="B"))
    refused(world, capsys, monkeypatch, "the block seal is not the kit's seal record of the block")


def test_refuses_a_host_that_is_not_done_or_not_of_the_block(world, capsys, monkeypatch):
    plan = sw.plan_of(world)
    plan["hosts"][sw.HOST]["done"] = False
    sw.save_plan(world, plan)
    refused(world, capsys, monkeypatch, "plan.json does not record the host as a done host of the block")
    plan["hosts"][sw.HOST]["done"] = True
    plan["hosts"][sw.HOST]["block"] = "B"
    sw.save_plan(world, plan)
    refused(world, capsys, monkeypatch, "plan.json does not record the host as a done host of the block")
    refused(world, capsys, monkeypatch, "plan.json does not record the host as a done host of the block", host="a-9")


def test_refuses_without_one_complete_pulled_job_of_each_kind(world, capsys, monkeypatch):
    plan = sw.plan_of(world)
    plan["hosts"][sw.HOST]["jobs"][1]["status"] = "crashed"
    sw.save_plan(world, plan)
    refused(world, capsys, monkeypatch, "plan.json records no single complete, pulled job of a kind this runner needs")
    plan["hosts"][sw.HOST]["jobs"][1]["status"] = "complete"
    plan["hosts"][sw.HOST]["jobs"][1]["pulled"] = False
    sw.save_plan(world, plan)
    refused(world, capsys, monkeypatch, "plan.json records no single complete, pulled job of a kind this runner needs")
    del plan["hosts"][sw.HOST]["jobs"][1]["pulled"]
    plan["hosts"][sw.HOST]["jobs"].append(dict(plan["hosts"][sw.HOST]["jobs"][2]))
    sw.save_plan(world, plan)
    refused(world, capsys, monkeypatch, "plan.json records no single complete, pulled job of a kind this runner needs")


def test_refuses_a_job_whose_outputs_do_not_list_the_file(world, capsys, monkeypatch):
    plan = sw.plan_of(world)
    outputs = plan["hosts"][sw.HOST]["jobs"][0]["outputs"]
    del outputs["job-0/representation/representation_pass.json"]
    sw.save_plan(world, plan)
    refused(world, capsys, monkeypatch, "the job's recorded outputs do not list a file this runner needs")


def test_refuses_a_pulled_file_that_differs_from_its_recorded_sha256(world, capsys, monkeypatch):
    path = world.pod["classifier"][0]
    path.write_bytes(path.read_bytes() + b" ")
    refused(world, capsys, monkeypatch, "a pod output does not hash to its expected SHA-256")
    path.unlink()
    refused(world, capsys, monkeypatch, "a pod output is missing or not a regular file")


def test_refuses_a_file_the_seal_does_not_list_as_sealed_at_that_sha256(world, capsys, monkeypatch):
    rel = "job-1/l1-scan/l1_scan.json"

    def other_hash(doc):
        for e in doc["files"]:
            if e["path"] == rel:
                e["sha256"] = "c" * 64
    sw.reseal(world, other_hash)
    refused(world, capsys, monkeypatch, "the block seal lists no single sealed entry for a pod output at its recorded SHA-256")

    def readable(doc):
        for e in doc["files"]:
            if e["path"] == rel:
                e["sha256"], e["class"] = world.pod["l1_scan"][1], "readable"
    sw.reseal(world, readable)
    refused(world, capsys, monkeypatch, "the block seal lists no single sealed entry for a pod output at its recorded SHA-256")
    # two entries for one file, the first sound and the second with another hash: an ambiguous seal refuses

    def ambiguous(doc):
        entry = next(e for e in doc["files"] if e["path"] == rel)
        entry["sha256"], entry["class"] = world.pod["l1_scan"][1], "sealed"
        doc["files"].append({**entry, "sha256": "d" * 64})
    sw.reseal(world, ambiguous)
    refused(world, capsys, monkeypatch, "the block seal lists no single sealed entry for a pod output at its recorded SHA-256")
    sw.reseal(world, lambda doc: doc.update(files=[e for e in doc["files"] if e["path"] != rel]))
    refused(world, capsys, monkeypatch, "the block seal lists no single sealed entry for a pod output at its recorded SHA-256")


def test_seal_entries_of_other_hosts_are_not_the_hosts(world, capsys, monkeypatch):
    """The same path and SHA-256 sealed under another host too: the host's own entry is still single, the run is
    unchanged. The entry moved to another host: nothing is sealed for the host, the run refuses."""
    rel = "job-1/l1-scan/l1_scan.json"
    sw.reseal(world, lambda doc: doc["files"].append({"host": "a-3", "path": rel, "sha256": world.pod["l1_scan"][1],
                                                      "class": "sealed"}))
    code, out, err = run(world, capsys, monkeypatch)
    assert code == 0

    def move(doc):
        doc["files"] = [e for e in doc["files"] if not (e["host"] == "a-3" and e["path"] == rel)]
        next(e for e in doc["files"] if e["host"] == sw.HOST and e["path"] == rel)["host"] = "a-3"
    sw.reseal(world, move)
    shutil.rmtree(world.out)
    shutil.rmtree(world.record_out.parent)
    refused(world, capsys, monkeypatch, "the block seal lists no single sealed entry for a pod output at its recorded SHA-256")


def test_the_main_pass_is_read_not_the_s3_orig_pass(world, capsys, monkeypatch):
    """Both representation folders hold a rows file and a summary; the runner names job-I/representation/ exactly."""
    plan = sw.plan_of(world)
    outputs = plan["hosts"][sw.HOST]["jobs"][0]["outputs"]
    main_rows = outputs.pop("job-0/representation/representation_rows.jsonl")
    sw.save_plan(world, plan)
    refused(world, capsys, monkeypatch, "the job's recorded outputs do not list a file this runner needs")
    outputs["job-0/representation/representation_rows.jsonl"] = main_rows
    sw.save_plan(world, plan)
    assert cc.main(world.argv()) == 0
    record = json.loads(world.record_out.read_bytes())
    assert record["inputs"]["rows"] == main_rows and "s3-orig" not in json.dumps(record["commands"])


def test_the_job_index_comes_from_plan_json_not_from_a_fixed_order(tmp_path, capsys, monkeypatch):
    world = sw.make(tmp_path, jobs_order=("classifier", "rep_pass", "l1_scan"))
    code, out, err = run(world, capsys, monkeypatch)
    assert code == 0
    record = json.loads(world.record_out.read_bytes())
    assert record["pod_paths"]["rows"] == f"{sw.HOST}:job-1/representation/representation_rows.jsonl"
    assert record["pod_paths"]["classifier"] == f"{sw.HOST}:job-0/classifier/classifier_scores.json"


def test_the_runner_never_reads_a_unit_folder_or_lists_the_tree(world, capsys, monkeypatch):
    """The other host's unit (its COMPLETE.json names an edit) is replaced by an unreadable folder: the run is unchanged."""
    unit = world.kit / "retrieved" / "a-3"
    shutil.rmtree(unit)
    (world.kit / "retrieved" / "a-3" / "tree").mkdir(parents=True)
    extra = world.kit / "retrieved" / sw.HOST / "tree" / "job-9"
    extra.mkdir()
    (extra / "stray.json").write_text(sw.SENTINELS["edit_name"])
    code, out, err = run(world, capsys, monkeypatch)
    assert code == 0


def test_the_value_free_messages_come_from_the_stand_ins_literals_only(world):
    """Only a Refusal raised with one string literal is whitelisted; the f-string, the concatenation and other calls
    with a literal are not; the built-in OSError type names are."""
    sources = {rel: (world.repo / rel).read_bytes() for rel in cc.MESSAGE_SOURCES}
    messages = cc.value_free_messages(sources)
    assert "REFUSED: the rows file is not the one the summary names (nothing written)" in messages
    assert "REFUSED: a shared check of the W1 helpers failed (nothing written)" in messages
    assert "REFUSED: the output folder is not empty (nothing written)" in messages
    assert "REFUSED: FileNotFoundError (nothing written)" in messages and "REFUSED: OSError (nothing written)" in messages
    assert not any("helpers refuse" in m or "hashes differently" in m or "has no scored row" in m for m in messages)
    assert not any(sw.sentinel_hits(m) for m in messages)
    assert not any("REFUSED: score (nothing written)" == m or "leak" in m for m in messages)   # other calls' literals
    assert all(m.startswith("REFUSED: ") and m.endswith(cc.NOTHING_WRITTEN) for m in messages)
    assert cc.known_reason("x\n" + "REFUSED: the output folder is not empty (nothing written)" + "\n\n", messages) \
        == "REFUSED: the output folder is not empty (nothing written)"
    assert cc.known_reason("REFUSED: the output folder is not empty (nothing written)\nTraceback", messages) is None
    assert cc.known_reason("", messages) is None


def test_an_unexpected_error_prints_its_type_only(world, capsys, monkeypatch):
    monkeypatch.setattr(cc, "load_rules", lambda path, expect: (_ for _ in ()).throw(KeyError(sw.SENTINELS["unit"])))
    code, out, err = run(world, capsys, monkeypatch)
    assert code == 2 and err.strip() == "REFUSED: an unexpected KeyError (its message is withheld: it may hold a value)"
