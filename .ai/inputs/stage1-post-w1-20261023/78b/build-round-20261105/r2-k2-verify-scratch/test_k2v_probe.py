"""K2V probes (the adversarial verifier's own checks; scratch only, never in the kit). Each probe states what it
expects; a probe that FAILS on its 'expect accepted' line shows the kit refuses (good), one that PASSES on an
'accepted' assertion shows a value the kit takes that it should not. Synthetic fixtures only."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

import test_planning_ab_78b as T
from test_planning_ab_78b import wa, wb, waf  # noqa: F401  (fixtures)

SENT = T.SENTINELS


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def scan(texts):
    return [s for s in SENT for t in texts if s in t]


# ----- P1: block A's record-done on the crash and refusal paths -----------------------------------------------------
def test_p1_crash_path_prints_and_writes_no_planted_value(wa, capsys):
    w = wa
    hosts = T.released_a(w)
    capsys.readouterr()
    for host in hosts:
        T.pull_planted(w, host)
    last = hosts[-1]
    tree = w.root / "retrieved" / last / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    rec = done["jobs"][-1]
    rec.update(status="crashed", why=f"Traceback: U was {SENT[0]}", exits={f"{last}-e1": 1},
               refusal={"reason": "crash", "text": f"coherence {SENT[6]}"})
    rec.pop("complete_sha256")
    done["refusal"] = {"reason": "crash", "text": f"harm {SENT[2]}"}
    done["stopped"] = "crashed"
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    printed = []
    for host in hosts:
        assert w.tool.main(["record-done", host]) == 0
        printed.append(capsys.readouterr())
    texts = [p.out + p.err for p in printed] + [(w.root / "plan.json").read_text(),
                                                (w.root / "operator-actions.jsonl").read_text()]
    assert scan(texts) == []
    assert all("blinded_inputs_part" not in p.out for p in printed)
    assert not (w.root / "blinded").exists()


def test_p1b_a_crashed_jobs_reason_field_is_copied_verbatim_into_plan_json(wa, capsys):
    """Observation probe: record_done stores JOB-DONE's per-job 'reason' text in plan.json as it is."""
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
    last = hosts[-1]
    tree = w.root / "retrieved" / last / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    done["jobs"][-1].update(status="crashed", reason=f"U {SENT[0]}")
    done["jobs"][-1].pop("complete_sha256")
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    for host in hosts:
        w.tool.main(["record-done", host])
    out = capsys.readouterr()
    assert SENT[0] not in out.out + out.err
    assert SENT[0] in (w.root / "plan.json").read_text()      # PASS = the reason text reaches plan.json verbatim


def test_p1c_refusal_paths_name_no_planted_value(wa, capsys):
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
    host = hosts[0]
    tree = w.root / "retrieved" / host / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    unit = tree / done["jobs"][0]["unit"] / "COMPLETE.json"
    unit.write_text(json.dumps({"complete": True, "evaluation": {"u": SENT[0]}}))   # COMPLETE.json changed after pull
    with pytest.raises(SystemExit) as info:
        w.tool.main(["record-done", host])
    msgs = [str(info.value)]
    (tree / "JOB-DONE.json").write_text(json.dumps({**done, "host": SENT[1]}))
    with pytest.raises(SystemExit) as info:
        w.tool.main(["record-done", host])
    msgs.append(str(info.value))
    out = capsys.readouterr()
    assert scan(msgs + [out.out, out.err, (w.root / "plan.json").read_text()]) == [], msgs


# ----- P3: PLAN_B_78B's SR-2 status at block B's init ---------------------------------------------------------------
def hand_plan_b(w, **fields) -> Path:
    doc = {"kind": "stage1-78b block-B plan record", "version": 1, "plan": "A", "sr2_adopted": False,
           "sr2_reason": "simulation_reading", "plan_basis": "sigma_pool_N", "sigma_A_pp": None,
           "blinded_sigma_output_sha256": None, "blinded_sigma_inputs_sha256": None,
           "utc": "2026-11-21T12:00:00+00:00", "recorded_by": "by hand"}
    doc.update(fields)
    p = w.record(doc, f"hand-plan-b-{w.n}.json")
    w.pin("PLAN_B_78B", p)
    return p


def n_pods_b(w, code: str) -> int:
    return len(w.rules.deal(w.rules.block_runs(code, "B", (), 0, None), "B"))


def test_p3a_init_b_accepts_sr2_adopted_while_the_blinding_record_says_not_verified(wb):
    w = wb
    T.b_ready(w, sigma=None)                     # the kit's own step: blinding not verified -> not adopted, plan A
    T.seal_sibling(w, "A")
    kit_doc = json.loads((w.repo / w.r78.PLAN_B_78B["path"]).read_text())
    assert (kit_doc["sr2_adopted"], kit_doc["sr2_reason"], kit_doc["plan"]) == (False, "blinding_test_not_verified", "A")
    out, inputs = T.blinded_output(w, 5.0)        # a blinded output giving B9
    hand_plan_b(w, plan="B9", sr2_adopted=True, sr2_reason=None, plan_basis="sigma_A", sigma_A_pp=5.0,
                blinded_sigma_output_sha256=sha(out), blinded_sigma_inputs_sha256=sha(inputs))
    got = w.init(n_pods=n_pods_b(w, "B9"), dry_run=True, blinded=str(out))
    assert (got["plan"], got["runs"]) == ("B9", 32)   # PASS = a hand-written SR-2 status is accepted


def test_p3b_init_b_accepts_not_adopted_while_both_triggers_pass(wb):
    w = wb
    blinded = T.b_ready(w, sigma=5.0)             # the kit's own step: adopted, plan B9
    T.seal_sibling(w, "A")
    kit_doc = json.loads((w.repo / w.r78.PLAN_B_78B["path"]).read_text())
    assert (kit_doc["sr2_adopted"], kit_doc["plan"]) == (True, "B9")
    hand_plan_b(w, plan="A", sr2_adopted=False, sr2_reason="simulation_reading", plan_basis="sigma_pool_N")
    got = w.init(n_pods=n_pods_b(w, "A"), dry_run=True)
    assert (got["plan"], got["runs"]) == ("A", 23)    # PASS = SR-2 dropped by hand is accepted
    assert blinded is not None


def test_p3c_a_wrong_plan_for_its_basis_refuses(wb):
    w = wb
    T.b_ready(w, sigma=5.0)
    T.seal_sibling(w, "A")
    out, inputs = T.blinded_output(w, 5.0)
    hand_plan_b(w, plan="A", sr2_adopted=True, sr2_reason=None, plan_basis="sigma_A", sigma_A_pp=5.0,
                blinded_sigma_output_sha256=sha(out), blinded_sigma_inputs_sha256=sha(inputs))
    with pytest.raises(SystemExit, match="GXB R-24"):
        w.init(n_pods=n_pods_b(w, "A"), dry_run=True, blinded=str(out))


# ----- P4: provenance of blinded_sigma's inputs and the parts -------------------------------------------------------
def test_p4a_record_plan_b_takes_a_hand_made_inputs_file(wb):
    w = wb
    w.gate(option="B", plan="A", sigma_f=("A", False))
    w.fill()
    T.SR2(w, "B")
    inputs = w.record({"kind": "scale-78b blinded sigma inputs", "version": 1, "option": "B",
                       "families": {"olmo2-7b": {"hand": "made"}, "llama31-8b": {"hand": "made"}}}, "hand-inputs.json")
    out = w.record({"df": 24, "inputs_sha256": sha(inputs), "kind": "scale-78b blinded sigma", "sigma_A_pp": 3.0,
                    "version": 1}, "hand-blinded.json")
    got = T.plan_b(w, out, inputs)
    assert (got["plan"], got["sr2_adopted"]) == ("A", True)   # PASS = an inputs file no kit step wrote is accepted


def test_p4b_write_blinded_inputs_takes_a_hand_made_part_from_anywhere(wa):
    w = wa
    T.released_a(w)                               # gate [C], OLMo only
    part = w.record({"kind": "stage1-78b blinded sigma inputs part", "version": 1, "family": "olmo2-7b",
                     "option": "C", "gate_sha256": w.r78.GATE_78B["sha256"],
                     "entry": {"design": "full", "engine": {}, "edits": {}, "cells": {"A1": {"1102": {
                         "path": "elsewhere/unit", "complete_sha256": "0" * 64}}}}}, "hand-part.json")
    out = w.repo / "records" / "inputs-from-hand-part.json"
    got = w.tool.write_blinded_inputs([f"{part}={sha(part)}"], str(out))
    assert got["files_named"] == {"olmo2-7b": 1}       # PASS = a part no record-done wrote is merged


# ----- P5: the noise reading's plan field is not cross-checked against its sigma ------------------------------------
def test_p5_record_gate_takes_a_plan_field_that_its_own_sigma_contradicts(wa):
    w = wa
    doc = T.noise_doc(plan="A")
    doc["seed_rule"]["sigma_pp"] = 9.0            # noise_reading.seed_rule's own sigma field: 9.0 pp gives H, not A
    doc["pooled"] = {"seed_rule": {"plan": "H", "review": False, "sigma_pp": 9.0}}
    noise = w.record(doc, "noise-edited.json")
    out = w.repo / "records" / "gate-edited.json"
    got = w.tool.record_gate_78b(str(noise), sha(noise), "B", "500", "test", str(out))
    assert got["provisional_plan"] == "A"         # PASS = the plan field is taken over its own sigma


# ----- P6: the anchor-stopped design (S-6) through the kit's part and the real blinded_sigma.py, split engines -------
def test_p6_anchor_stopped_part_with_per_role_engines_is_read_by_blinded_sigma(wa, monkeypatch):
    w = wa
    monkeypatch.syspath_prepend(str(T.REPO))
    ts = T.load_by_path("ts_blinded_sigma_tests_k2v", T.REPO / "scripts/scale78b/tests/test_blinded_sigma.py")
    fam, r78 = w.family, w.r78
    assert ts.ENGINE_X == T.X
    split = ts.ENGINES_SPLIT
    r_edits = {d: ts.r_edit(fam, d) for d in range(1, 6)}
    m_edits = {a: ts.method_edit(fam, a) for a in ("A1", "L1", "H1", "S1", "S3", "S4")}
    for d in (4, 5):
        monkeypatch.setitem(r78.R_DRAW_SOURCES[fam], d, {"path": f".ai/inputs/test/R_d{d}.json",
                                                         "sha256": hashlib.sha256(r_edits[d]).hexdigest()})
    w.gate(option="C", engines={"a0": split["a0"], "R": split["R"]})
    w.fill()
    for a, data in m_edits.items():
        monkeypatch.setitem(r78.METHOD_EDITS[fam], a, {"path": f".ai/inputs/test/{a}.json",
                                                       "sha256": hashlib.sha256(data).hexdigest(), "rows": T.METHOD_ROWS[a]})
    w.fill(edits=False, branch=False, oext=False)
    # the stop record at its pin (the shared fixture's form), checked against "its" JOB-DONE.json
    done = w.repo / "records" / "JOB-DONE.json"
    done.write_bytes(b"anchor job done (synthetic)")
    stop_doc = {**json.loads(T.SHARED_STOP.read_bytes()), "job_done_sha256": sha(done)}
    stop = T.write(w.repo / "records" / "stop.json", T.canon(stop_doc).decode())
    w.pin("ANCHOR_STOP", stop, fam)
    count = ts.unsafe_count
    complete = {}
    for arm, seed in r78.block0_runs(fam):
        rel = f"tmp/family-probe-s78-{fam}-0/retrieved/{fam}-0-1/tree/round1/{seed}-{arm}-e1-a1"
        complete[(arm, seed)] = ts.make_unit(w.repo / rel, fam, arm, seed, count(fam, arm, seed), r_edits[seed - 1100],
                                             engine=split["R"])
    units = T.n_units(w, complete)
    for key in units:
        arm, seed = key.split("-")
        units[key]["edit_sha256"] = hashlib.sha256(r_edits[int(seed) - 1100]).hexdigest()
    for seed, u in r78.KIT[fam]["a0_units"].items():
        if seed != "untuned":
            monkeypatch.setitem(u, "complete_sha256", ts.make_unit(w.repo / u["path"], fam, "a0", seed,
                                                                   count(fam, "a0", seed), engine=split["a0"]))
    stopped_runs = [(a, s) for s in (1102, 1103, 1104) for a in ("H1", "S1", "S4")] + [("R", 1104), ("R", 1105),
                                                                                      ("a0", 1104)]
    n = len(w.rules.deal(stopped_runs, "A"))
    hosts = w.init(n_pods=n, amount=3000.0, anchor_job_done=str(done))["hosts"]
    out = None
    for host in hosts:
        h = w.plan()["hosts"][host]
        tree = w.root / "retrieved" / host / "tree"
        recs = []
        for i, job in enumerate(h["jobs"]):
            arm, seed = job["arm"], job["seed"]
            edit = None if arm == "a0" else (r_edits[seed - 1100] if arm == "R" else m_edits[arm])
            key = ts.make_unit(tree / T.unit_name(job), fam, arm, seed, count(fam, arm, seed), edit)
            recs.append({"index": i, "kind": job["kind"], "arm": arm, "seed": seed, "engine": "X", "engine_sha256": T.X,
                         "status": "complete", "unit": T.unit_name(job), "complete_sha256": key, "outputs": {}})
        T.write(tree / "JOB-DONE.json", {"host": host, "jobs": recs})
        out = w.tool.record_done(host)
    part = out["blinded_inputs_part"]
    pdoc = json.loads((w.repo / part["path"]).read_text())
    assert pdoc["entry"]["design"] == "anchor_stopped" and set(pdoc["entry"]["edits"]) == {"H1", "S1", "S4"}
    assert pdoc["entry"]["engine"] == {"a0": split["a0"], "R": split["R"], "block_a": T.X}
    inputs = w.repo / "elsewhere" / "blinded-inputs.json"
    inputs.parent.mkdir()
    w.tool.write_blinded_inputs([f"{w.repo / part['path']}={part['sha256']}"], str(inputs))
    doc = ts.bs.read(inputs, sha(inputs))
    fit = ts.numpy_fit(fam, "anchor_stopped")
    df = sum(c["df"] for c in fit.values())
    assert doc["df"] == df == 6
    assert math.isclose(doc["sigma_A_pp"], math.sqrt(2 * sum(c["rss"] for c in fit.values()) / df), rel_tol=1e-12)


# ----- P7: the 1B block-A commands are still reachable in a 7-8B block-A copy ----------------------------------------
@pytest.mark.parametrize("cmd", [["block-a-need"], ["write-block-a-plan", "--out", "OUT", "--recorded-by", "t"]])
def test_p7_1b_block_a_commands_in_a_7_8b_copy(wa, capsys, cmd):
    w = wa
    w.gate()
    w.fill()
    argv = [str(w.repo / "records" / "plan-a.json") if x == "OUT" else x for x in cmd]
    try:
        code = w.tool.main(argv)
        result = f"ran, exit {code}: {capsys.readouterr().out[:300]}"
    except SystemExit as exc:
        result = f"refused: {str(exc)[:300]}"
    except Exception as exc:                           # an unguarded crash
        result = f"crashed: {type(exc).__name__}: {str(exc)[:200]}"
    print("P7", cmd[0], "->", result)
    assert result.startswith("refused"), result
