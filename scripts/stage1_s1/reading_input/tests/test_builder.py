"""The B16 input builder on synthetic kit folders in the engine's real layout (synth_kit): each reading end to end
through B16, hand-computed values, one refusal test per check, and the seal (no value reaches stdout or stderr)."""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import synth_kit as sk

from scripts.stage1_s1.reading.__main__ import main as b16_main
from scripts.stage1_s1.reading.schema import validate
from scripts.stage1_s1.reading.settings import canonical_json, design
from scripts.stage1_s1.reading_input.__main__ import main

TREE = Path(__file__).resolve().parents[4]          # the tree that holds this package (a copy under the mutation runner)
PY = sys.executable
VALUE = re.compile(r"\d\.\d{3,}")                   # a printed number with three or more decimals


@pytest.fixture(scope="session")
def worlds(tmp_path_factory):
    cache = {}

    def get(reading, **kw):
        key = (reading, tuple(sorted(kw.items())))
        if key not in cache:
            cache[key] = sk.make(tmp_path_factory.mktemp(reading), reading, **kw)
        return cache[key]
    return get


def run(s, tmp_path, capsys, overlap=True, extra=()):
    out, rec = tmp_path / "tables.json", tmp_path / "sources.json"
    rc = main(s.args(out, rec, overlap=overlap) + list(extra))
    cap = capsys.readouterr()
    return rc, cap.out, cap.err, out, rec


def refused(s, tmp_path, capsys, match, overlap=True, extra=()):
    rc, out, err, path, rec = run(s, tmp_path, capsys, overlap, extra)
    assert rc == 2 and out == "" and not path.exists() and not rec.exists(), err
    assert err.startswith("REFUSED: ") and re.search(match, err), err
    assert sk.TEXT not in err and not VALUE.search(err), err
    return err


def edit(worlds, tmp_path, reading="plan_a_block_a_only", **kw):
    return sk.copy(worlds(reading, **kw), tmp_path / "w")


def u_mean(cell):
    return 100 * sum(cell.unsafe.values()) / (3 * len(cell.unsafe))


def hand_checks(s, doc):
    """Every primary vector, coherence count and theta0 flag against the synthetic raw values, by hand."""
    dsg = design(s.reading)
    harm, o_ids, q = sorted(sk.HARM), sorted(sk.DEV + sk.PH), sorted(sk.QUERIES)
    for arm in dsg.arms:
        for seed in dsg.seeds[arm]:
            c, k = s.cells[(arm, seed)], str(seed)
            assert doc["endpoints"]["U"]["cells"][arm][k] == [c.unsafe[p] / 3 for p in harm]
            assert doc["u_variants"]["g3_unscored_unsafe"][arm][k] == [(c.unsafe[p] + c.unscored[p]) / 3 for p in harm]
            assert doc["u_variants"]["g3_controversial_unsafe"][arm][k] == [(c.unsafe[p] + c.controversial[p]) / 3
                                                                            for p in harm]
            assert doc["endpoints"]["L"]["cells"][arm][k] == [c.loss[x] for x in q]
            flags = sk.o_flags_of(c, s.branch)
            assert doc["endpoints"]["O"]["cells"][arm][k] == [flags[p] for p in o_ids]
            assert doc["coherence"][arm][k] == {"answers": 600, "capped": c.capped, "failing": c.failing}
    t = sk.o_flags_of(s.theta0_o, s.branch)
    assert doc["endpoints"]["O"]["theta0"] == [t[p] for p in o_ids]


def b16_means(s, doc_path, tmp_path):
    out = tmp_path / "reading.json"
    assert b16_main(["--input", str(doc_path), "--out", str(out)]) == 0
    r = json.loads(out.read_text())
    dsg = design(s.reading)
    for arm in dsg.arms:
        cells = [s.cells[(arm, j)] for j in dsg.seeds[arm]]
        assert math.isclose(r["arms"][arm]["means"]["U"], sum(map(u_mean, cells)) / len(cells), abs_tol=1e-9)
        o = [100 * sum(sk.o_flags_of(c, s.branch).values()) / 500 for c in cells]
        assert math.isclose(r["arms"][arm]["means"]["O"], sum(o) / len(o), abs_tol=1e-9)
        ls = [math.fsum(c.loss.values()) / 200 for c in cells]
        assert math.isclose(r["arms"][arm]["means"]["L"], sum(ls) / len(ls), abs_tol=1e-12)
    return r


# ----- each reading end to end ---------------------------------------------------------------------------------------


def test_plan_a_end_to_end(worlds, tmp_path, capsys):
    s = worlds("plan_a")
    rc, out, err, path, rec = run(s, tmp_path, capsys)
    assert rc == 0 and err == ""
    doc = json.loads(path.read_text())
    validate(doc)
    assert set(doc) == {"kind", "version", "reading", "endpoints", "coherence", "u_variants", "references", "overlap"}
    hand_checks(s, doc)
    refs = {r["name"]: r for r in doc["references"]}
    assert sorted(refs) == ["ref-G", "ref-bqi", "ref-external-safe_lora-conditional", "ref-external-safe_lora-default",
                            "ref-prefix", "ref-scale"]
    assert refs["ref-G"]["cells"]["U"]["1105"] == [s.refs[("ref-G", 1105)].unsafe[p] / 3 for p in sorted(sk.HARM)]
    assert refs["ref-scale"]["kind"] == "curve" and sorted(refs["ref-scale"]["points"]) == ["0.5", "0.75", "0.9"]
    assert refs["ref-scale"]["points"]["0.75"]["L"]["1106"] == [s.refs[("ref-scale 0.75", 1106)].loss[q]
                                                               for q in sorted(sk.QUERIES)]
    assert refs["ref-scale"]["theta0"]["U"] == [s.theta0.unsafe[p] / 3 for p in sorted(sk.HARM)]
    assert refs["ref-scale"]["theta0"]["L"] == [s.theta0.loss[q] for q in sorted(sk.QUERIES)]
    assert doc["overlap"]["strata"] == json.loads(s.b14["strata"].read_text())
    assert doc["overlap"]["report"] == json.loads(s.b14["report"].read_text())
    assert (doc["overlap"]["strata_sha256"], doc["overlap"]["report_sha256"]) == (s.b14["strata_sha256"],
                                                                                 s.b14["report_sha256"])
    record = json.loads(rec.read_text())
    assert record["output_sha256"] == sk.sha(path.read_bytes()) and path.read_bytes() == canonical_json(doc)
    assert record["counts"]["U_cells"] == 50 and len(record["cells"]) == 50
    assert set(record["judges"]) == {"A", "B"} and record["judges"]["A"]["units"] == 27
    assert record["not_references"] == [f"b-safe-lora job {k} certify" for k in range(3)]
    assert len(record["not_pulled"]) == 1 and record["not_pulled"][0].endswith("(retrain a0 1102)")
    assert f"wrote {path} sha256 {record['output_sha256']}" in out
    r = b16_means(s, path, tmp_path)
    assert r["overlap_control"]["computed"] is True and r["references"]["tested"] is True
    assert r["provenance"]["input_sha256"] == record["output_sha256"]


def test_block_a_only_end_to_end(worlds, tmp_path, capsys):
    s = worlds("plan_a_block_a_only")
    rc, out, err, path, rec = run(s, tmp_path, capsys)
    assert rc == 0
    doc = json.loads(path.read_text())
    assert "references" not in doc and sorted(doc["endpoints"]["U"]["cells"]["S1"]) == ["1102", "1103", "1104"]
    hand_checks(s, doc)
    r = b16_means(s, path, tmp_path)
    assert r["label_suffix"] == "block A only (3 seeds per method arm)" and r["overlap_control"]["computed"] is True


def test_plan_b_end_to_end(worlds, tmp_path, capsys):
    s = worlds("plan_b")
    rc, out, err, path, rec = run(s, tmp_path, capsys)
    assert rc == 0
    doc = json.loads(path.read_text())
    assert sorted(doc["endpoints"]["U"]["cells"]) == ["A1", "H1", "R", "S1", "S4", "a0"]
    assert len(doc["endpoints"]["U"]["cells"]["R"]) == 10 and len(doc["endpoints"]["U"]["cells"]["a0"]) == 7
    hand_checks(s, doc)
    assert json.loads(rec.read_text())["kit"]["seals"].keys() == {"A", "B", "C"}
    r = b16_means(s, path, tmp_path)
    assert r["design"]["fit_arms"] == ["R", "A1", "H1", "S1", "S4"]


def test_branch_full_keeps_the_stored_dev_flags(worlds, tmp_path, capsys):
    s = worlds("plan_a_block_a_only", branch="full")
    rc, *_, path, rec = run(s, tmp_path, capsys)
    assert rc == 0
    doc = json.loads(path.read_text())
    hand_checks(s, doc)                              # o_flags_of(cell, "full")
    c = s.cells[("S1", 1102)]
    assert sk.o_flags_of(c, "full") != sk.o_flags_of(c, "128")    # the two rules differ on this cell


def test_no_overlap_is_explicit(worlds, tmp_path, capsys):
    s = worlds("plan_a_block_a_only")
    rc, out, *_, path, rec = run(s, tmp_path, capsys, overlap=False)
    assert rc == 0 and "overlap: not included (--no-overlap)" in out
    doc = json.loads(path.read_text())
    assert "overlap" not in doc
    out_b16 = tmp_path / "reading.json"
    assert b16_main(["--input", str(path), "--out", str(out_b16)]) == 0
    assert json.loads(out_b16.read_text())["overlap_control"]["computed"] is False


def test_ln12_r_o_cell_may_be_absent_after_ls04_but_a0_may_not(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    host, i, job = sk.find_job(plan, "o_only", "R", 1101)
    plan["hosts"][host]["jobs"][i - 1]["reason"] = "LS-04"
    job.update(status="not_started", reason="LS-04", outputs=None)
    sk.seal_block(s.kit, plan, "A")
    s.save_plan(plan)
    rc, out, *_, path, rec = run(s, tmp_path, capsys)
    assert rc == 0 and "O cells absent (LN-12): R 1101" in out
    doc = json.loads(path.read_text())
    assert sorted(doc["endpoints"]["O"]["cells"]["R"]) == ["1102", "1103", "1104"]
    assert json.loads(rec.read_text())["o_cells_absent"] == ["R 1101"]
    assert b16_main(["--input", str(path), "--out", str(tmp_path / "reading.json")]) == 0
    capsys.readouterr()
    host, i, job = sk.find_job(plan, "o_only", "a0", 1102)
    plan["hosts"][host]["jobs"][i - 1]["reason"] = "LS-04"
    job.update(status="not_started", reason="LS-04", outputs=None)
    sk.seal_block(s.kit, plan, "A")
    s.save_plan(plan)
    path.unlink()
    rec.unlink()
    refused(s, tmp_path, capsys, r"a0 at 1102: no complete O-only pass")


def test_ln12_absent_r_o_cell_by_a_not_run_decision(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    host, i, job = sk.find_job(plan, "o_only", "R", 1102)
    job.update(status="not_started", outputs=None)
    sk.seal_block(s.kit, plan, "A")
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"R at 1102: no complete O-only pass")
    seal_field(s, "A", "not_run", [{"job": "o_only R 1102", "decision_sha256": "7" * 64}])
    rc, out, *_ = run(s, tmp_path, capsys)
    assert rc == 0 and "O cells absent (LN-12): R 1102" in out


def seal_field(s, block, key, value):
    plan = s.plan()
    path = s.kit / plan["seals"][block]["path"]
    doc = json.loads(path.read_text())
    doc[key] = value
    data = sk.jbytes(doc)
    path.write_bytes(data)
    plan["seals"][block]["sha256"] = sk.sha(data)
    s.save_plan(plan)


def test_moved_host_is_not_an_input_only_when_the_seal_lists_it(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    host, i, job = sk.find_job(plan, "arm", "S1", 1102)
    plan["hosts"]["a-9"] = {"block": "A", "done": False, "jobs": [dict(job)]}
    sk.seal_block(s.kit, plan, "A")
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"a-9 \(block A\) is not done and not listed as moved")
    seal_field(s, "A", "moved", [{"host": "a-9", "to": [host], "pulled_tree": False}])
    rc, *_ = run(s, tmp_path, capsys)
    assert rc == 0


# ----- refusals: units, hashes and the design -------------------------------------------------------------------------


@pytest.mark.parametrize("change,match", [
    ({"status": "crashed"}, r"no complete, pulled unit in their block \(S4 at 1103, block A\)"),
    ({"pulled": False}, r"no complete, pulled unit in their block \(S4 at 1103, block A\)"),
])
def test_missing_or_not_pulled_unit_refuses(worlds, tmp_path, capsys, change, match):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    sk.find_job(plan, "arm", "S4", 1103)[2].update(change)
    s.save_plan(plan)
    refused(s, tmp_path, capsys, match)


def test_duplicated_unit_refuses(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    host, i, job = sk.find_job(plan, "arm", "H1", 1104)
    other = next(h for h in plan["hosts"] if h.startswith("a-") and h not in (host, "a-2"))
    plan["hosts"][other]["jobs"].append(dict(job))
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"H1 at 1104: two complete units")


@pytest.mark.parametrize("arm,seed,kind", [("A1", 1105, "arm"), ("a0", 1103, "a0_arm"), ("S1", 1104, "a0_arm")])
def test_extra_unit_refuses(worlds, tmp_path, capsys, arm, seed, kind):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    job = dict(sk.find_job(plan, "arm", "S1", 1102)[2])
    job.update(kind=kind, arm=arm, seed=seed)
    plan["hosts"]["a-3"]["jobs"].append(job)
    s.save_plan(plan)
    refused(s, tmp_path, capsys, rf"a complete {kind} job of {arm} at {seed} that block A's table does not hold")


def test_extra_o_only_pass_refuses(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    job = dict(sk.find_job(plan, "o_only", "R", 1101)[2])
    job.update(arm="S1", seed=1102)
    plan["hosts"]["a-2"]["jobs"].append(job)
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"an O-only pass of S1 at 1102 that no cell reads")


def test_unit_hash_checks(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    host, i, job = sk.find_job(plan, "arm", "L1", 1102)
    good = job["complete_sha256"]
    job["complete_sha256"] = "0" * 64                  # plan.json against the seal
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"L1 .*seal lists its COMPLETE.json at [0-9a-f]{16}, plan.json records 0{16}")
    job["complete_sha256"] = good
    s.save_plan(plan)
    marker = sk.unit_folder(s, host, job) / "COMPLETE.json"
    marker.write_bytes(marker.read_bytes() + b" ")    # the file against plan.json and the seal
    refused(s, tmp_path, capsys, r"COMPLETE.json hashes to [0-9a-f]{16}, plan.json records")


def test_eval_file_against_complete_and_seal(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    host, i, job = sk.find_job(plan, "arm", "S3", 1103)
    f = sk.unit_folder(s, host, job) / "eval" / "e1" / "guard_samples.jsonl"
    f.write_bytes(f.read_bytes() + b"\n")
    refused(s, tmp_path, capsys, r"guard_samples.jsonl is not in the block seal at the SHA-256 COMPLETE.json lists|"
                                 r"guard_samples.jsonl hashes to")
    sk.rehash_job(s, host, i)                          # consistent: COMPLETE, plan and seal re-taken
    rc, *_ = run(s, tmp_path, capsys)
    assert rc == 2                                     # its judge files name the old COMPLETE.json
    plan = s.plan()
    new = plan["hosts"][host]["jobs"][i]["complete_sha256"]
    plan["hosts"][host]["jobs"][i]["complete_sha256"] = job["complete_sha256"]
    s.save_plan(plan)
    refused(s, tmp_path, capsys, rf"seal lists its COMPLETE.json at {new[:16]}")


def test_seal_checks(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    seal = s.kit / "seals" / "block-A.json"
    seal.write_bytes(seal.read_bytes() + b" ")
    refused(s, tmp_path, capsys, r"block A's seal hashes to [0-9a-f]{16}, plan.json records")
    t = sk.copy(worlds("plan_a"), tmp_path / "w2")
    plan = t.plan()
    del plan["seals"]["B"]
    t.save_plan(plan)
    refused(t, tmp_path, capsys, r"block B is not sealed in plan.json")


def test_plan_code_and_block_rules(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    plan["records"]["plan_ab"]["code"] = "B"
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"plan.json records plan B; the reading plan_a_block_a_only is plan A's")
    plan["records"]["plan_ab"]["code"] = "A"
    plan["records"]["oext_fallback"] = {"status": "dev100_recipe_cap"}
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"fallback \(c\) is recorded")
    t = sk.copy(worlds("plan_a"), tmp_path / "w2")
    t.reading = "plan_a_block_a_only"
    refused(t, tmp_path, capsys, r"block B is sealed: the block-A-only reading", overlap=False)


def test_pinned_units(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    folder = s.repo / "tmp" / "synth-gate" / f"1102-{sk.engine_arm('R', 1102)}-e1-a1"
    job = folder / "job.json"
    job.write_bytes(job.read_bytes() + b" ")
    refused(s, tmp_path, capsys, r"job.json differs from its pin")
    marker = folder / "COMPLETE.json"
    marker.write_bytes(marker.read_bytes() + b" ")
    refused(s, tmp_path, capsys, r"COMPLETE.json hashes to [0-9a-f]{16}, the pin is")


def test_job_json_must_name_the_planned_arm(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    sk.find_job(plan, "arm", "A1", 1103)[2]["edit"]["sha256"] = "5" * 64
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"job.json's arm differ from the unit plan.json records")


def test_bqi_own_a0_refuses(worlds, tmp_path, capsys):
    s = sk.copy(worlds("plan_a"), tmp_path / "w")
    plan = s.plan()
    job = dict(sk.find_job(plan, "a0_arm", "a0", 1105)[2])
    job["role"] = "bqi_own_a0"
    plan["hosts"]["b-3"]["jobs"].append(job)
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"B\+Qi's own a0 .* has no field in B16's schema")


# ----- refusals: the O-ext passes and theta0 ---------------------------------------------------------------------------


def oext_edit(s, kind, arm, seed, mutate):
    plan = s.plan()
    host, i, job = sk.find_job(plan, kind, arm, seed)
    sk.recomplete(s.kit / "retrieved" / host / "tree" / f"job-{i}" / "oext", mutate)
    job["outputs"] = sk._outputs(s.kit / "retrieved" / host / "tree", f"job-{i}/oext")
    sk.seal_block(s.kit, plan, plan["hosts"][host]["block"])
    s.save_plan(plan)


def test_oext_pass_bindings(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    oext_edit(s, "arm", "S1", 1103, lambda d: d["unit"].update(complete_sha256="6" * 64))
    refused(s, tmp_path, capsys, r"not route unit_eval on S1 1103's unit")
    oext_edit(s, "arm", "S1", 1103, lambda d: d.update(unit={"complete_sha256": s.units[("S1", 1103)]["complete"]},
                                                     dev100_inputs={"dev100/guard.jsonl": "3" * 64}))
    refused(s, tmp_path, capsys, r"names other stored dev-100 judge records than the ones read")
    t = edit(worlds, tmp_path / "t")
    oext_edit(t, "o_only", "a0", 1103, lambda d: d.update(dev100_source={"complete_sha256": "4" * 64}))
    refused(t, tmp_path, capsys, r"its dev-100 source is not the pinned a0 1103 unit")
    u = edit(worlds, tmp_path / "u")
    oext_edit(u, "o_only", "theta0", None, lambda d: d.update(state="run"))
    refused(u, tmp_path, capsys, r"theta0's O-only pass is not the untuned state")


def test_oext_outputs_and_theta0_required(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    job = sk.find_job(plan, "arm", "H1", 1102)[2]
    job["outputs"] = {k: v for k, v in job["outputs"].items() if not k.endswith("COMPLETE.json")}
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"plan.json records no O-ext folder job-\d+/oext")
    t = edit(worlds, tmp_path / "t")
    plan = t.plan()
    sk.find_job(plan, "o_only", "theta0")[2].update(status="crashed")
    t.save_plan(plan)
    refused(t, tmp_path, capsys, r"theta0: no complete O-only pass in block A")


def summary_edit(s, kind, arm, seed, rel, mutate, oext=False):
    plan = s.plan()
    host, i, job = sk.find_job(plan, kind, arm, seed)
    tree = s.kit / "retrieved" / host / "tree"
    path = (tree / f"job-{i}" / "oext" / rel) if oext else (tree / job["unit"] / rel)
    doc = json.loads(path.read_text())
    mutate(doc)
    path.write_bytes(sk.jbytes(doc))
    sk.rehash_job(s, host, i, plan)


@pytest.mark.parametrize("rel,oext,mutate,match", [
    ("eval/e1/summary.json", False, lambda d: d["harm"]["sampled"].update(unsafe=d["harm"]["sampled"]["unsafe"] + 1),
     r"disagree with summary.json's harm.sampled counts"),
    ("eval/e1/summary.json", False, lambda d: d["query_loss"].update(mean=d["query_loss"]["mean"] + 1e-12),
     r"disagree with summary.json's query_loss n or mean"),
    ("eval/e1/summary.json", False, lambda d: d["query_loss"].update(query_bank_sha256="a" * 64),
     r"the cells do not hold one query bank"),
    ("oext_summary.json", True, lambda d: d["o"]["by_source"]["phtest"].update(
        refused=d["o"]["by_source"]["phtest"]["refused"] + 1), r"disagree with oext_summary.json's primary table"),
])
def test_summary_parity_checks(worlds, tmp_path, capsys, rel, oext, mutate, match):
    s = edit(worlds, tmp_path)
    summary_edit(s, "arm", "L1", 1104, rel, mutate, oext)
    refused(s, tmp_path, capsys, match)


def test_cells_must_hold_one_prompt_set(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    host, i, job = sk.find_job(plan, "arm", "S4", 1102)
    for name in ("samples.jsonl", "guard_samples.jsonl"):
        f = sk.unit_folder(s, host, job) / "eval" / "e1" / name
        f.write_bytes(f.read_bytes().replace(b'"p199"', b'"p200"'))
    sk.rehash_job(s, host, i, plan)
    refused(s, tmp_path, capsys, r"the cells do not hold one set of harm prompt ids")


# ----- refusals: B14's documents (B16-H-O8, B16-H-O10) ----------------------------------------------------------------


def b14_rewrite(s, what, mutate=None, raw=None):
    path = s.b14[what]
    doc = json.loads(path.read_text())
    if mutate:
        mutate(doc)
    data = raw(doc) if raw else sk.b14_canonical(doc)
    path.write_bytes(data)
    s.b14[f"{what}_sha256"] = sk.sha(data)


def test_b14_bindings(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    good = s.b14["report_sha256"]
    s.b14["report_sha256"] = "1" * 64
    refused(s, tmp_path, capsys, r"B14's report file hashes to [0-9a-f]{16}, the sealed value is 1{16}")
    s.b14["report_sha256"] = good
    b14_rewrite(s, "report", raw=lambda d: (json.dumps(d, sort_keys=True, indent=1) + "\n").encode())
    refused(s, tmp_path, capsys, r"not B14's canonical JSON")
    b14_rewrite(s, "report", lambda d: d.update(strata_sha256="2" * 64))
    refused(s, tmp_path, capsys, r"B14's report was not made on this strata record")
    b14_rewrite(s, "report", lambda d: d.update(strata_sha256=s.b14["strata_sha256"]))
    b14_rewrite(s, "report", lambda d: d["units"]["a0"]["1102"].update(complete_sha256="3" * 64))
    refused(s, tmp_path, capsys, r"the unit of a0 at 1102 is not the unit read here")
    b14_rewrite(s, "report", lambda d: d["units"]["a0"]["1102"].update(
        complete_sha256=s.units[("a0", 1102)]["complete"], guard_samples_jsonl_sha256="4" * 64))
    refused(s, tmp_path, capsys, r"the unit of a0 at 1102 is not the unit read here")
    b14_rewrite(s, "report", lambda d: d["units"]["a0"]["1102"].update(
        guard_samples_jsonl_sha256=s.units[("a0", 1102)]["guard_samples"]))
    rc, *_ = run(s, tmp_path, capsys)
    assert rc == 0


def test_b14_strata_prompt_order_is_the_u_order(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    b14_rewrite(s, "strata", lambda d: d.update(prompt_ids=d["prompt_ids"][1:] + d["prompt_ids"][:1]))
    b14_rewrite(s, "report", lambda d: d.update(strata_sha256=s.b14["strata_sha256"]))
    refused(s, tmp_path, capsys, r"not B14's strata prompt ids in order \(B16-H-O10\)")


def test_b14_options_all_or_none(worlds, tmp_path, capsys):
    s = worlds("plan_a_block_a_only")
    out, rec = tmp_path / "t.json", tmp_path / "r.json"
    base = ["--reading", s.reading, "--kit", str(s.kit), "--repo", str(s.repo), "--rules", str(s.rules), "--out",
            str(out), "--record", str(rec)]
    assert main(base + ["--b14-strata", str(s.b14["strata"])]) == 2
    assert "the overlap block needs" in capsys.readouterr().err
    assert main(base + ["--no-overlap", "--expect-report-sha256", "a" * 64]) == 2
    assert "--no-overlap takes none" in capsys.readouterr().err
    assert not out.exists() and not rec.exists()


# ----- refusals: the judge files ----------------------------------------------------------------------------------


def test_judge_files(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    folder = s.kit / "judges" / "A"
    victim = sorted(p for p in folder.iterdir() if p.name.startswith("granite--a-3--"))[0]
    data = victim.read_bytes()
    victim.unlink()
    refused(s, tmp_path, capsys, r"is missing, differs from its indexed SHA-256 or is not sealed")
    victim.write_bytes(data)
    (folder / ("harmbench--x--y--" + "a" * 12 + ".json")).write_text("{}")
    refused(s, tmp_path, capsys, r"judges/A: 1 judge-named file\(s\) not in its index")
    (folder / ("harmbench--x--y--" + "a" * 12 + ".json")).unlink()
    index = json.loads((folder / "judge-files-index.json").read_text())
    index["files"] = [e for e in index["files"] if e["file"] != victim.name]
    (folder / "judge-files-index.json").write_text(json.dumps(index))
    refused(s, tmp_path, capsys, r"is not the index the seal and its judge record name")
    victim.unlink()
    s.reseal("A")
    refused(s, tmp_path, capsys, r"block A: 1 unit\(s\) the reading uses have no granite judge file")


def test_judge_record_or_not_run_decision(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    seal_field(s, "A", "judge_record", None)
    refused(s, tmp_path, capsys, r"block A's seal does not name a judge record or a not-run decision for every judge")
    seal_field(s, "A", "judge_not_run", [{"judge": "harmbench", "decision_sha256": "1" * 64},
                                         {"judge": "granite", "decision_sha256": "2" * 64}])
    rc, out, *_ = run(s, tmp_path, capsys)
    assert rc == 0 and "judges A: none" in out


# ----- refusals: references and B16's own schema ---------------------------------------------------------------------


def test_partial_curve_refuses(worlds, tmp_path, capsys):
    s = sk.copy(worlds("plan_a"), tmp_path / "w")
    plan = s.plan()
    job = sk.find_job(plan, "ref_eval", seed=1106)[2]
    job["points"] = [p for p in job["points"] if p != "scale:0.5"]
    job["units"] = [u for u in job["units"] if not u["unit"].endswith("scale-0.5")]
    s.save_plan(plan)
    refused(s, tmp_path, capsys, r"the adapter-scaling curve needs the points")


def test_b16_schema_refusal_prints_only_its_place(worlds, tmp_path, capsys):
    s = worlds("plan_a", ref_seeds=(1105,))
    err = refused(s, tmp_path, capsys, r"^REFUSED: B16's schema refuses the built document at references\[0\] U\n$")
    assert "two seeds" not in err


def test_never_overwrites(worlds, tmp_path, capsys):
    s = worlds("plan_a_block_a_only")
    (tmp_path / "sources.json").write_text("x")
    rc, out, err, path, rec = run(s, tmp_path, capsys)
    assert rc == 2 and "sources.json exists" in err and not path.exists()


# ----- the seal: no value reaches stdout or stderr --------------------------------------------------------------------


def test_no_value_reaches_the_output_streams(worlds, tmp_path):
    s = edit(worlds, tmp_path)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
           "PYTHONPATH": os.pathsep.join([str(TREE), str(sk.TREE), os.environ.get("PYTHONPATH", "")])}
    cmd = [PY, "-B", "-m", "scripts.stage1_s1.reading_input"]
    runs = [subprocess.run(cmd + s.args(tmp_path / "ok.json", tmp_path / "ok-sources.json"), cwd=TREE, env=env,
                           capture_output=True, text=True)]
    assert runs[0].returncode == 0, runs[0].stderr
    plan = s.plan()
    host, i, job = sk.find_job(plan, "arm", "S1", 1104)            # the unit that holds the sentinel loss
    summary_edit(s, "arm", "S1", 1104, "eval/e1/summary.json", lambda d: d["query_loss"].update(mean=1.5))
    runs.append(subprocess.run(cmd + s.args(tmp_path / "x.json", tmp_path / "x-sources.json"), cwd=TREE, env=env,
                               capture_output=True, text=True))
    assert runs[1].returncode == 2 and "query_loss n or mean" in runs[1].stderr
    record = (tmp_path / "ok-sources.json").read_text()
    means = {f"{u_mean(c):.3f}" for c in s.cells.values()} | {f"{u_mean(c):.2f}" for c in s.cells.values()}
    for text in [r.stdout + r.stderr for r in runs] + [record]:
        assert sk.TEXT not in text and "7.7777" not in text and str(sk.JUDGE_SENTINEL) not in text
        assert not VALUE.search(text)
        assert not any(m in text for m in means)
    tables = (tmp_path / "ok.json").read_text()
    assert "7.777777777777" in tables and sk.TEXT not in tables         # the values go only into the sealed document


# ----- refusals: one per remaining check (plan.json, seal, folder, O-only, reference and judge-index rules) -------------


def plan_edit(s, fn):
    plan = s.plan()
    fn(plan)
    s.save_plan(plan)


def job_of(plan, kind, arm=None, seed=None):
    return sk.find_job(plan, kind, arm, seed)[2]


def regen_of(plan, arm, seed):
    host, i, _ = sk.find_job(plan, "o_only", arm, seed)
    return plan["hosts"][host]["jobs"][i - 1]


@pytest.mark.parametrize("fn,match", [
    (lambda p: p["records"].update(plan_ab=None), r"plan.json records no plan-A/B code"),
    (lambda p: p.pop("hosts"), r"not a stage-1 plan"),
    (lambda p: p["hosts"]["a-3"].update(jobs=None), r"a-3: plan.json holds no job list"),
    (lambda p: regen_of(p, "R", 1102).update(reason="LS-04"),
     r"its regeneration is not an accepted, complete R at 1102"),
    (lambda p: job_of(p, "o_only", "R", 1103).update(regen_source=None), r"names no regeneration earlier on its host"),
    (lambda p: regen_of(p, "a0", 1101).update(complete_sha256="5" * 64),
     r"the O-only pass is not on its regeneration's unit"),
    (lambda p: p["hosts"]["a-2"]["jobs"].append(dict(job_of(p, "o_only", "a0", 1101))),
     r"a0 at 1101: two complete O-only passes"),
    (lambda p: p["hosts"]["a-2"]["jobs"].append(dict(job_of(p, "o_only", "theta0"))),
     r"theta0 at None: two complete O-only passes"),
    (lambda p: job_of(p, "arm", "S3", 1104).update(unit="round1/elsewhere"),
     r"S3 1104 kit:a-\d+/round1/elsewhere: its COMPLETE.json is not in block A's seal"),
    (lambda p: job_of(p, "arm", "S3", 1104).update(unit="round1/../x"), r"is not a plain relative path"),
    (lambda p: job_of(p, "arm", "S3", 1104).update(complete_sha256=None),
     r"plan.json records no COMPLETE.json SHA-256"),
])
def test_plan_record_refusals(worlds, tmp_path, capsys, fn, match):
    s = edit(worlds, tmp_path)
    plan_edit(s, fn)
    refused(s, tmp_path, capsys, match)


def test_reused_pass_routes(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    oext_edit(s, "o_only", "R", 1101, lambda d: d.update(dev100_route="unit_eval"))
    refused(s, tmp_path, capsys, r"a regenerated unit's O-only pass has route 'unit_eval'")


def test_rules_pins(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    text = s.rules.read_text()
    s.rules.write_text(text + "REJUDGED_PINS = {'B': (), 'A': tuple(p for p in REJUDGED_PINS['A'] "
                                "if not p['name'].startswith('a0 1102'))}\n")
    refused(s, tmp_path, capsys, r"a0 at 1102 is a reused cell with no pin")
    s.rules.write_text(text + "REJUDGED_PINS = {'B': (), 'A': REJUDGED_PINS['A'] + REJUDGED_PINS['A'][:1]}\n")
    refused(s, tmp_path, capsys, r"REJUDGED_PINS\['A'\] holds an entry that is not one a0, R or theta0 unit")
    for change, match in (("p['arm'] = 'edit-' + '0' * 64", r"job.json's arm differ"),
                          ("p['target'] = 'init'", r"the pin is not R at 1101, checkpoint e1"),
                          ("p['job_sha256'] = None", r"the pin has no COMPLETE.json or job.json SHA-256")):
        s.rules.write_text(text + "p = dict(REJUDGED_PINS['A'][3])\n" + change + "\n"
                           "REJUDGED_PINS = {'B': (), 'A': REJUDGED_PINS['A'][:3] + (p,) + REJUDGED_PINS['A'][4:]}\n")
        refused(s, tmp_path, capsys, match)
    s.rules.write_text("X = 1\n")
    refused(s, tmp_path, capsys, r"the rules module rules.py has no REJUDGED_PINS")


def test_seal_record_refusals(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    seal_field(s, "A", "kind", "another seal")
    refused(s, tmp_path, capsys, r"block A's seal is not a version-1 'stage1 block seal' of block A")
    seal_field(s, "A", "kind", "stage1 block seal")
    plan = s.plan()
    doc = json.loads((s.kit / plan["seals"]["A"]["path"]).read_text())
    seal_field(s, "A", "files", doc["files"] + doc["files"][:1])
    refused(s, tmp_path, capsys, r"block A's seal lists .* twice")


def test_folder_must_list_what_is_read(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    host, i, job = sk.find_job(plan, "arm", "A1", 1104)
    sk.recomplete(sk.unit_folder(s, host, job))                   # unchanged: same bytes
    f = sk.unit_folder(s, host, job) / "eval" / "e1" / "query_loss.jsonl"
    f.rename(f.with_name("query_loss.renamed"))
    sk.rehash_job(s, host, i, plan)
    refused(s, tmp_path, capsys, r"A1 1104 kit:.*: COMPLETE.json does not list eval/e1/query_loss.jsonl")
    t = edit(worlds, tmp_path / "t")
    plan = t.plan()
    host, i, job = sk.find_job(plan, "arm", "A1", 1104)
    sk.recomplete(sk.unit_folder(t, host, job), lambda d: d.update(files_extra=1))
    marker = sk.unit_folder(t, host, job) / "COMPLETE.json"
    doc = json.loads(marker.read_text())
    doc["complete"] = False
    marker.write_bytes(sk.jbytes(doc))
    sk.seal_block(t.kit, plan, "A")
    job["complete_sha256"] = sk.sha(marker.read_bytes())
    sk.seal_block(t.kit, plan, "A")
    t.save_plan(plan)
    refused(t, tmp_path, capsys, r"COMPLETE.json is not a complete marker with a file list")


def test_ids_and_counts_across_cells(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    summary_edit(s, "arm", "H1", 1103, "oext_summary.json",
                 lambda d: None, oext=True)                         # unchanged
    plan = s.plan()
    host, i, job = sk.find_job(plan, "arm", "H1", 1103)
    f = s.kit / "retrieved" / host / "tree" / f"job-{i}" / "oext" / "oext_guard.jsonl"
    f.write_bytes(f.read_bytes().replace(b'"ph399"', b'"ph400"'))
    sk.rehash_job(s, host, i, plan)
    refused(s, tmp_path, capsys, r"the cells do not hold one set of O-bank prompt ids")
    t = edit(worlds, tmp_path / "t")
    plan = t.plan()
    host, i, job = sk.find_job(plan, "arm", "H1", 1103)
    f = sk.unit_folder(t, host, job) / "eval" / "e1" / "query_loss.jsonl"
    f.write_bytes(f.read_bytes().replace(b'"q199"', b'"q200"'))
    sk.rehash_job(t, host, i, plan)
    refused(t, tmp_path, capsys, r"the cells do not hold one set of task-row ids")


def test_item_count_must_be_b16s(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(sk, "QUERIES", sk.QUERIES[:199])            # every unit of this world holds 199 task rows
    s = sk.make(tmp_path / "w", "plan_a_block_a_only", seed=3)
    refused(s, tmp_path, capsys, r"the L items number 199, B16's schema needs 200")


def test_judge_index_entries(worlds, tmp_path, capsys):
    cases = [
        (lambda ix: ix.update(kind="other"), r"is not Gate B's judge files index"),
        (lambda ix: ix["files"][0].pop("target"), r"an entry does not hold exactly Gate B's index keys"),
        (lambda ix: ix["files"][0].update(complete_sha256="7" * 64), r"an entry is not a judge file named for its"),
        (lambda ix: ix["files"].append(dict(ix["files"][0])), r"lists a file twice"),
    ]
    for k, (fn, match) in enumerate(cases):
        s = edit(worlds, tmp_path / f"c{k}")
        path = s.kit / "judges" / "A" / "judge-files-index.json"
        ix = json.loads(path.read_text())
        fn(ix)
        path.write_text(json.dumps(ix, indent=2, sort_keys=True) + "\n")
        s.reseal("A")
        refused(s, tmp_path, capsys, match)


def test_two_judge_files_for_one_unit(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    folder = s.kit / "judges" / "A"
    path = folder / "judge-files-index.json"
    ix = json.loads(path.read_text())
    e = dict(ix["files"][0])
    twin = e["file"].replace("--", "--twin-", 1)
    (folder / twin).write_bytes((folder / e["file"]).read_bytes())
    ix["files"].append({**e, "file": twin})
    path.write_text(json.dumps(ix, indent=2, sort_keys=True) + "\n")
    s.reseal("A")
    refused(s, tmp_path, capsys, r"two files of one judge for one unit")


@pytest.mark.parametrize("fn,match", [
    (lambda p: job_of(p, "ref_train", "G", 1106).update(arm="bqi"), r"not recipe G or bqi"),
    (lambda p: p["hosts"]["b-ref-g"]["jobs"].append(dict(job_of(p, "ref_train", "G", 1106))),
     r"two units of ref-G at 1106"),
    (lambda p: job_of(p, "ref_eval", seed=1106)["units"].pop(), r"no unit for each evaluation point"),
    (lambda p: job_of(p, "ref_eval", seed=1106)["units"][0].update(unit="job-1/evals/1105-scale-0.9"),
     r"is not one point's B10 folder"),
    (lambda p: job_of(p, "safe_lora", seed=1106).update(points=["default", "conditional", "k12"]),
     r"its units are not exactly its points"),
    (lambda p: [job_of(p, "ref_eval", seed=1106)["points"].__setitem__(0, "scale:0.3"),
                job_of(p, "ref_eval", seed=1106)["units"][0].update(unit="job-1/evals/1106-scale-0.3")],
     r"the point scale-0.3 is not a reference this reading knows"),
])
def test_reference_job_refusals(worlds, tmp_path, capsys, fn, match):
    s = sk.copy(worlds("plan_a"), tmp_path / "w")
    plan_edit(s, fn)
    refused(s, tmp_path, capsys, match)


def test_b10_unit_identity(worlds, tmp_path, capsys):
    s = sk.copy(worlds("plan_a"), tmp_path / "w")
    plan = s.plan()
    host, i, job = sk.find_job(plan, "safe_lora", seed=1105)
    folder = s.kit / "retrieved" / host / "tree" / job["units"][0]["unit"]
    doc = json.loads((folder / "job.json").read_text())
    doc["external"]["name"] = "other"
    (folder / "job.json").write_bytes(sk.jbytes(doc))
    sk.recomplete(folder, lambda d: d.update(job_sha256=sk.sha((folder / "job.json").read_bytes())))
    sk.rehash_job(s, host, i, plan)
    refused(s, tmp_path, capsys, r"not B11's Safe LoRA transform")
    t = sk.copy(worlds("plan_a"), tmp_path / "t")
    plan = t.plan()
    host, i, job = sk.find_job(plan, "ref_eval", seed=1105)
    folder = t.kit / "retrieved" / host / "tree" / job["units"][0]["unit"]
    sk.recomplete(folder, lambda d: d.update(mode="prefix"))
    sk.rehash_job(t, host, i, plan)
    refused(t, tmp_path, capsys, r"COMPLETE.json is not a B10 evaluation of this point and seed")


def test_overlap_report_units_shape(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    b14_rewrite(s, "report", lambda d: d.update(units={}))
    refused(s, tmp_path, capsys, r"names no units for a0 and each of its add sets")
    b14_rewrite(s, "report", lambda d: d.update(units={k: {} for k in ("a0", "S1", "S3", "S4")}))
    refused(s, tmp_path, capsys, r"arm a0 does not name a unit at each of its seeds")
    s.b14["report_sha256"] = "XYZ"
    refused(s, tmp_path, capsys, r"--expect-report-sha256 is not a lowercase hex SHA-256")


def test_one_oext_branch(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan = s.plan()
    host, i, job = sk.find_job(plan, "arm", "S1", 1103)
    folder = s.kit / "retrieved" / host / "tree" / f"job-{i}" / "oext"
    sk.oext_files(folder, s.cells[("S1", 1103)], "full")            # this pass alone under Branch full
    sk.rehash_job(s, host, i, plan)
    refused(s, tmp_path, capsys, r"the cells do not hold one O-ext branch")


def test_an_unexpected_error_prints_its_type_only(worlds, tmp_path, capsys):
    s = edit(worlds, tmp_path)
    plan_edit(s, lambda p: job_of(p, "arm", "S1", 1102).update(edit="x"))
    refused(s, tmp_path, capsys, r"S1 at 1102: plan.json's edit record names no edit SHA-256")
    plan_edit(s, lambda p: p.update(seals=["x"]))                # a malformed plan.json the checks do not name
    refused(s, tmp_path, capsys, r"^REFUSED: an unexpected AttributeError \(its message is withheld")
