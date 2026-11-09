"""K2 re-verifier's probes after the fix round (scratch only). A probe named *_refuses expects the kit to refuse; one
named *_accepted asserts the kit takes a value it should not (PASS = a residual defect). Synthetic fixtures only."""
from __future__ import annotations

import hashlib
import importlib
import json
import math
from pathlib import Path

import pytest

import test_planning_ab_78b as T
from test_planning_ab_78b import wa, wb  # noqa: F401  (fixtures)

SENT = T.SENTINELS


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def hand_plan_b(w, **fields) -> Path:
    p = w.record(T.plan_b_doc(**fields), f"hand-plan-b-{w.n}.json")
    w.pin("PLAN_B_78B", p)
    return p


def n_b(w, code):
    return len(w.rules.deal(w.rules.block_runs(code, "B", (), 0, None), "B"))


# ===== R1: K2V-1 / R-43 =================================================================================================
def test_r1a_p3a_hand_adopted_while_blinding_unverified_refuses(wb):
    w = wb
    T.b_ready(w, sigma=None)
    T.seal_sibling(w, "A")
    out, inputs = T.blinded_output(w, 5.0)
    hand_plan_b(w, plan="B9", sr2_adopted=True, sr2_reason=None, plan_basis="sigma_A", sigma_A_pp=5.0,
                blinded_sigma_output_sha256=sha(out), blinded_sigma_inputs_sha256=sha(inputs))
    with pytest.raises(SystemExit, match="GXB R-43"):
        w.init(n_pods=n_b(w, "B9"), dry_run=True, blinded=str(out))


def test_r1b_p3b_hand_not_adopted_while_both_pass_refuses(wb):
    w = wb
    T.b_ready(w, sigma=5.0)
    T.seal_sibling(w, "A")
    hand_plan_b(w, plan="A", sr2_adopted=False, sr2_reason="simulation_reading", plan_basis="sigma_pool_N")
    with pytest.raises(SystemExit, match="GXB R-43"):
        w.init(n_pods=n_b(w, "A"), dry_run=True)


def test_r1c_not_adopted_with_the_wrong_reason_refuses(wb):
    w = wb
    T.b_ready(w, sigma=None)                     # the pinned records: not adopted, blinding_test_not_verified
    T.seal_sibling(w, "A")
    hand_plan_b(w, plan="A", sr2_adopted=False, sr2_reason="simulation_reading", plan_basis="sigma_pool_N")
    with pytest.raises(SystemExit, match="GXB R-43"):
        w.init(n_pods=n_b(w, "A"), dry_run=True)


def test_r1d_hand_adopted_while_the_simulation_reads_above_6_percent_refuses(wb):
    w = wb
    T.b_ready(w, sigma=5.0)
    T.seal_sibling(w, "A")
    s = T.SR2.__new__(T.SR2)
    s.w, s.families = w, w.r78.GATE_OPTIONS["B"]
    s.sim("B", count=1300)                       # 6.5% above the 6% rule: SR-2 not adopted by the records
    with pytest.raises(SystemExit, match=r"the pinned records give False \(simulation_reading\)"):
        w.init(n_pods=n_b(w, "B9"), dry_run=True, blinded=str(w.repo / "records" / "x"))


def test_r1e_release_b_refuses_when_the_records_change_after_init(wb):
    w = wb
    T.b_ready(w, sigma=None)
    T.seal_sibling(w, "A")
    out = w.init(n_pods=n_b(w, "A"), amount=3000.0)
    name = out["hosts"][1] if len(out["hosts"]) > 1 else out["hosts"][0]
    plan = w.plan()
    pending = plan["blocks"]["B"]["pending"]
    host = next(iter(pending)) if pending else name
    h = pending.get(host) or plan["hosts"][host]
    w.blinding(verified=True)                    # re-pinned blinding record no block-A copy read
    with pytest.raises(SystemExit, match="was not planned under the pinned blinding record"):
        w.tool.release_hosts_ab(plan, "B", [(host, h)])


def test_r1f_right_status_wrong_plan_refuses(wb):
    w = wb
    T.b_ready(w, sigma=None)                     # not adopted (blinding); the gate's provisional plan is A
    T.seal_sibling(w, "A")
    hand_plan_b(w, plan="B9", sr2_adopted=False, sr2_reason="blinding_test_not_verified", plan_basis="sigma_pool_N")
    with pytest.raises(SystemExit, match="GXB R-24"):
        w.init(n_pods=n_b(w, "B9"), dry_run=True)


def test_r1g_llamas_block_a_read_another_blinding_record_refuses(wb):
    w = wb
    T.b_ready(w, sigma=None)
    T.seal_sibling(w, "A")
    path = w.repo / "tmp" / "family-probe-s78-llama31-8b-A" / "plan.json"
    doc = json.loads(path.read_text())
    doc["blocks"]["A"]["blinding"] = {"sha256": T.hx("another record")}
    path.write_text(json.dumps(doc))
    with pytest.raises(SystemExit, match="block A of llama31-8b .* was not planned under the pinned blinding record"):
        w.init(n_pods=n_b(w, "A"), dry_run=True)


# ===== R2: K2V-2 =========================================================================================================
def test_r2a_p9_deferral_part_written(wa):
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
    first, new = T.defer_one(w, hosts)
    T.pull_planted(w, new)
    out = w.tool.record_done(new)
    assert "path" in out["blinded_inputs_part"], out


def test_r2b_crash_then_defer_part_written(wa):
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
    first = hosts[1]
    tree = w.root / "retrieved" / first / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    done["jobs"][1].update(status="crashed")
    done["jobs"][1].pop("complete_sha256")
    for j in done["jobs"][2:]:
        j.update(status="not_started")
        j.pop("complete_sha256")
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    for h in hosts:
        w.tool.record_done(h)
    new = w.tool.defer(first)["to"]
    if new not in w.plan()["hosts"]:
        w.tool.release("A")
    T.pull_planted(w, new)
    out = w.tool.record_done(new)
    assert "path" in out["blinded_inputs_part"], out
    part = json.loads((w.repo / out["blinded_inputs_part"]["path"]).read_text())
    paths = [c["path"] for v in part["entry"]["cells"].values() for c in v.values()]
    assert sum(f"/retrieved/{new}/" in x for x in paths) == len(w.plan()["hosts"][new]["jobs"])


def test_r2c_rerun_mismatched_requeue_part(wa, capsys):
    """A complete block-A unit re-queued as environment-mismatched (requeue --rerun-mismatched), re-run complete on
    the new host: which unit does the part take?"""
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
        w.tool.record_done(host)
    first = hosts[0]
    digest = w.plan()["hosts"][first]["jobs"][0]["complete_sha256"]
    w.mp.setattr(w.tool, "mismatch", lambda plan, attempt: ["device_name"])   # the environment differs (stand-in)
    moved = w.tool.requeue(first, [digest])
    new = moved["to"]
    if new not in w.plan()["hosts"]:
        w.tool.release("A")
    T.pull_planted(w, new)
    out = w.tool.record_done(new)
    print("R2c record-done ->", {k: v for k, v in out.items() if k != "statuses"})
    with pytest.raises(SystemExit) as info:
        w.tool.write_blinded_part_command()
    print("R2c write-blinded-part ->", info.value)
    found, problem = w.tool.block_a_cells(w.plan())
    print("R2c block_a_cells ->", problem)
    assert problem and "two complete units" in problem       # PASS = the kit's own rerun path leaves no part


def test_r2d_an_open_job_that_no_move_took_refuses(wa):
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
    tree = w.root / "retrieved" / hosts[2] / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    done["jobs"][-1].update(status="deferred", reason="remaining")
    done["jobs"][-1].pop("complete_sha256")
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    outs = [w.tool.record_done(h) for h in hosts]
    assert not any("blinded_inputs_part" in o for o in outs)
    with pytest.raises(SystemExit, match="once every block-A arm job is complete"):
        w.tool.write_blinded_part_command()


# ===== R3: K2V-4 / R-45 ==================================================================================================
def orch_world(tmp_path, monkeypatch):
    w, sb = T.sc_world(tmp_path, monkeypatch)
    w.fill(oext=True)
    w.pack(*sb.oext_inputs(w))
    return w, sb


def test_r3a_pinned_o_ext_pod_not_held_edited_and_null_held(tmp_path, monkeypatch):
    w, sb = orch_world(tmp_path, monkeypatch)
    try:
        host = w.init([{"kind": "o_only"}])["released"][0]
        orch = importlib.import_module("orchestrate")
        monkeypatch.setattr(orch, "log", lambda *a, **k: None)
        assert orch.w1_18_hold(host) is None
        pin = dict(w.r78.BRANCH_78B[w.family])
        w.mp.setitem(w.r78.BRANCH_78B, w.family, {**pin, "sha256": T.hx("another record")})   # the pin edited
        with pytest.raises(SystemExit, match="waits for W1-18's branch record"):
            orch.w1_18_hold(host)
        w.mp.setitem(w.r78.BRANCH_78B, w.family, {**pin, "path": "../outside.json"})
        with pytest.raises(SystemExit, match="waits for W1-18's branch record"):
            orch.w1_18_hold(host)
        w.mp.setitem(w.r78.BRANCH_78B, w.family, pin)
        assert orch.w1_18_hold(host) is None
    finally:
        T.close(w)


def test_r3b_w1_18_pod_runs_with_the_branch_null(tmp_path, monkeypatch):
    w, sb = T.sc_world(tmp_path, monkeypatch)
    try:
        w.mp.setitem(w.r78.BRANCH_78B, w.family, None)
        orch = importlib.import_module("orchestrate")
        monkeypatch.setattr(orch, "log", lambda *a, **k: None)
        plan = w.mac.load_plan() if w.mac.PLAN.exists() else {"hosts": {}}
        plan.setdefault("hosts", {})["x-w1"] = {"block": "sc", "jobs": [{"kind": "w1_18", "arm": "theta0", "seed": None}]}
        monkeypatch.setattr(orch, "plan", lambda: plan)
        assert orch.w1_18_hold("x-w1") is None
    finally:
        T.close(w)


def test_r3c_block_a_arm_pod_held_once_its_branch_is_off(wa, monkeypatch):
    w = wa
    hosts = T.released_a(w)
    orch = importlib.import_module("orchestrate")
    monkeypatch.setattr(orch, "log", lambda *a, **k: None)
    assert orch.w1_18_hold(hosts[0]) is None
    branch = w.repo / w.r78.BRANCH_78B[w.family]["path"]
    branch.write_text(branch.read_text() + " ")
    with pytest.raises(SystemExit, match="waits for W1-18's branch record"):
        orch.w1_18_hold(hosts[0])


# ===== R4: R-44 =========================================================================================================
def test_r4a_stale_record_refuses_at_init(wa):
    w = wa
    w.gate()
    w.fill()
    (w.root / "plan_tool.py").write_text((w.root / "plan_tool.py").read_text() + "\n# edited after the record\n")
    with pytest.raises(SystemExit, match="plan_tool.py than the one that runs here"):
        w.init(dry_run=True)


def test_r4b_record_done_code_edited_after_the_last_release_accepted(wa):
    """An edit of the A copy's plan_tool.py (record-done's code) after block A's last release: record-done, the part,
    write-blinded-inputs and record-plan-b-78b take it (PASS = R-44's 'a later change voids it' is not enforced there)."""
    w = wa
    hosts = T.released_a(w)
    (w.root / "plan_tool.py").write_text((w.root / "plan_tool.py").read_text() + "\n# record-done edited after release\n")
    for host in hosts:
        T.pull_planted(w, host)
        out = w.tool.record_done(host)
    assert "path" in out["blinded_inputs_part"]
    got = w.tool.write_blinded_inputs()
    s = T.SR2.__new__(T.SR2)
    s.w, s.families = w, ("olmo2-7b",)
    s.sim("C")
    s.sim("B")
    blinded = w.record({"df": 12, "inputs_sha256": got["sha256"], "kind": "scale-78b blinded sigma", "sigma_A_pp": 4.0,
                        "version": 1}, "blinded-after-edit.json")
    out = w.repo / "records" / "plan-b-after-edit.json"
    rec = w.tool.record_plan_b_78b(str(w.noise), str(blinded), sha(blinded), "test", str(out))
    assert rec["sr2_adopted"] is True                         # PASS = adopted on a record-done edited after the record


def test_r4c_blinded_sigma_edited_after_block_a_accepted(wa):
    """scripts/scale78b/blinded_sigma.py edited after block A's init (before it runs on block A's inputs):
    record-plan-b-78b still reads SR-2 as adopted (PASS = residual)."""
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
        w.tool.record_done(host)
    got = w.tool.write_blinded_inputs()
    bs = w.repo / "scripts/scale78b/blinded_sigma.py"
    bs.write_text(bs.read_text() + "\n# edited after block A\n")
    s = T.SR2.__new__(T.SR2)
    s.w, s.families = w, ("olmo2-7b",)
    s.sim("C")
    s.sim("B")
    blinded = w.record({"df": 12, "inputs_sha256": got["sha256"], "kind": "scale-78b blinded sigma", "sigma_A_pp": 4.0,
                        "version": 1}, "blinded-after-bs-edit.json")
    out = w.repo / "records" / "plan-b-after-bs-edit.json"
    rec = w.tool.record_plan_b_78b(str(w.noise), str(blinded), sha(blinded), "test", str(out))
    assert rec["sr2_adopted"] is True


# ===== R5: K2V-3 =========================================================================================================
def done_a(w):
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
        w.tool.record_done(host)
    s = T.SR2.__new__(T.SR2)
    s.w, s.families = w, ("olmo2-7b",)
    s.sim("C")
    return hosts


def test_r5a_p4a_hand_made_inputs_file_refuses(wa):
    w = wa
    done_a(w)
    inputs = T.write(w.tool.BLINDED_INPUTS, {"kind": "scale-78b blinded sigma inputs", "version": 1, "option": "C",
                                             "families": {"olmo2-7b": {"hand": "made"}}})
    blinded = w.record({"df": 12, "inputs_sha256": sha(inputs), "kind": "scale-78b blinded sigma", "sigma_A_pp": 3.0,
                        "version": 1}, "hand-blinded.json")
    with pytest.raises(SystemExit, match="is not the one the kit writes"):
        w.tool.record_plan_b_78b(str(w.noise), str(blinded), sha(blinded), "test", str(w.repo / "records" / "pb.json"))
    inputs.unlink()
    got = w.tool.write_blinded_inputs()
    blinded = w.record({"df": 12, "inputs_sha256": got["sha256"], "kind": "scale-78b blinded sigma", "sigma_A_pp": 3.0,
                        "version": 1}, "kit-blinded.json")
    rec = w.tool.record_plan_b_78b(str(w.noise), str(blinded), sha(blinded), "test", str(w.repo / "records" / "pb2.json"))
    assert (rec["plan"], rec["sr2_adopted"]) == ("A", True)


def test_r5b_p4b_hand_made_part_refuses_and_old_cli_gone(wa):
    w = wa
    done_a(w)
    part = w.tool.part_path(w.family)
    doc = json.loads(part.read_text())
    doc["entry"]["cells"]["A1"]["1102"]["path"] = "elsewhere/unit"
    part.write_bytes(T.canon(doc))
    with pytest.raises(SystemExit, match="is not the one its block-A copy's plan.json gives"):
        w.tool.write_blinded_inputs()
    with pytest.raises(SystemExit) as info:
        w.tool.main(["write-blinded-inputs", "--part", f"{part}={sha(part)}", "--out", "x.json"])
    assert info.value.code == 2                               # argparse: the old arguments no longer exist


def test_r5c_hand_edited_block_a_plan_json_moves_a_cell_limit(wa):
    """Limit probe: an edit of block A's plan.json itself (a cell's unit swapped) and the part written again from it
    pass write-blinded-inputs (the kit's state file is its own source of truth)."""
    w = wa
    hosts = done_a(w)
    plan = w.plan()
    plan["hosts"][hosts[0]]["jobs"][0]["complete_sha256"] = T.hx("another unit")
    w.mac.save_plan(plan)
    w.tool.part_path(w.family).unlink()
    w.tool.write_blinded_part_command()
    assert w.tool.write_blinded_inputs()["sha256"]


# ===== R6: no regression in the blinding half ============================================================================
def snap(root: Path) -> dict:
    return {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}


def test_r6a_success_path_changes_three_files_none_with_a_value(wa, capsys):
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
    capsys.readouterr()
    before = snap(w.repo)
    for host in hosts:
        assert w.tool.main(["record-done", host]) == 0
    out = capsys.readouterr()
    changed = sorted(p.relative_to(w.repo).as_posix() for p, d in snap(w.repo).items() if before.get(p) != d)
    print("R6a changed:", changed)
    assert len(changed) == 3
    texts = [out.out, out.err] + [(w.repo / c).read_text() for c in changed]
    assert not [s for s in SENT for t in texts if s in t]


def test_r6b_crash_and_deferral_paths_carry_no_value(wa, capsys):
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
    last = hosts[-1]
    tree = w.root / "retrieved" / last / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    done["jobs"][-2].update(status="crashed", why=f"Traceback: U was {SENT[0]}", exits={f"{last}-e1": 1})
    done["jobs"][-2].pop("complete_sha256")
    done["jobs"][-1].update(status="deferred", reason="s_obs", refusal=f"text {SENT[6]}")
    done["jobs"][-1].pop("complete_sha256")
    done["refusal"] = {"reason": "s_obs", "text": f"harm {SENT[2]}"}
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    capsys.readouterr()
    for host in hosts:
        assert w.tool.main(["record-done", host]) == 0
    out = capsys.readouterr()
    texts = [out.out, out.err, (w.root / "plan.json").read_text(), (w.root / "operator-actions.jsonl").read_text()]
    assert not [s for s in SENT for t in texts if s in t]
    assert "blinded_inputs_part" not in out.out


def test_r6c_refusal_texts_carry_no_value(wa):
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
    tree = w.root / "retrieved" / hosts[0] / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    (tree / done["jobs"][0]["unit"] / "COMPLETE.json").write_text(json.dumps({"evaluation": {"u": SENT[0]}}))
    msgs = []
    with pytest.raises(SystemExit) as info:
        w.tool.record_done(hosts[0])
    msgs.append(str(info.value))
    done["jobs"][1]["reason"] = f"U {SENT[0]}"
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    with pytest.raises(SystemExit) as info:
        w.tool.record_done(hosts[0])
    msgs.append(str(info.value))
    assert not [s for s in SENT for m in msgs if s in m], msgs


def test_r6d_anchor_stopped_part_through_the_real_blinded_sigma(wa, monkeypatch):
    """My P6, on the fixed API: OLMo-2-7B stopped, engines split per role, record-done, write-blinded-inputs (its one
    place) and the real blinded_sigma.read: df 6, sigma equal to numpy."""
    w = wa
    monkeypatch.syspath_prepend(str(T.REPO))
    ts = T.load_by_path("ts_bs_k2r", T.REPO / "scripts/scale78b/tests/test_blinded_sigma.py")
    fam, r78 = w.family, w.r78
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
    done = w.repo / "records" / "JOB-DONE-anchor.json"
    done.write_bytes(b"anchor job done (k2r)")
    stop = T.write(w.repo / "records" / "stop-k2r.json",
                   T.canon({**json.loads(T.SHARED_STOP.read_bytes()), "job_done_sha256": sha(done)}).decode())
    w.pin("ANCHOR_STOP", stop, fam)
    count = ts.unsafe_count
    complete = {}
    for arm, seed in r78.block0_runs(fam):
        rel = f"tmp/family-probe-s78-{fam}-0/retrieved/{fam}-0-1/tree/round1/{seed}-{arm}-e1-a1"
        complete[(arm, seed)] = ts.make_unit(w.repo / rel, fam, arm, seed, count(fam, arm, seed), r_edits[seed - 1100],
                                             engine=split["R"])
    units = T.n_units(w, complete)
    for key in units:
        units[key]["edit_sha256"] = hashlib.sha256(r_edits[int(key.split("-")[1]) - 1100]).hexdigest()
    for seed, u in r78.KIT[fam]["a0_units"].items():
        if seed != "untuned":
            monkeypatch.setitem(u, "complete_sha256", ts.make_unit(w.repo / u["path"], fam, "a0", seed,
                                                                   count(fam, "a0", seed), engine=split["a0"]))
    stopped = [(a, s) for s in (1102, 1103, 1104) for a in ("H1", "S1", "S4")] + [("R", 1104), ("R", 1105), ("a0", 1104)]
    hosts = w.init(n_pods=len(w.rules.deal(stopped, "A")), amount=3000.0, anchor_job_done=str(done))["hosts"]
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
        w.tool.record_done(host)
    got = w.tool.write_blinded_inputs()
    inputs = w.repo / got["path"]
    doc = ts.bs.read(inputs, sha(inputs))
    fit = ts.numpy_fit(fam, "anchor_stopped")
    assert doc["df"] == 6
    assert math.isclose(doc["sigma_A_pp"], math.sqrt(2 * sum(c["rss"] for c in fit.values()) / 6), rel_tol=1e-12)
