"""K2 second re-verifier's probes (the follow-up for K2R-1 to K2R-4; GXB R-49 to R-52). Scratch only; synthetic
fixtures. *_refuses expects a refusal; *_accepted asserts the kit takes a value it should not (PASS = a residual)."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

import test_planning_ab_78b as T
from test_planning_ab_78b import wa, wb  # noqa: F401


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def edit(path: Path) -> bytes:
    keep = path.read_bytes()
    path.write_bytes(keep + b"\n# edited after the blinding record\n")
    return keep


def gate_doc(w) -> dict:
    return json.loads((w.repo / w.r78.GATE_78B["path"]).read_text())


# ===== N1: K2R-1 / R-49 at sr2_status and record-plan-b-78b, each of the four files ====================================
@pytest.mark.parametrize("which", ["a-copy-plan_tool", "blinded_sigma", "test_blinded_sigma", "test_planning"])
def test_n1_each_file_edited_after_the_record_refuses_at_sr2_status_and_record_plan_b(wa, which):
    w = wa
    T.a_done_c(w)
    got = w.tool.write_blinded_inputs()
    target = {"a-copy-plan_tool": w.root / "plan_tool.py",
              "blinded_sigma": w.repo / "scripts/scale78b/blinded_sigma.py",
              "test_blinded_sigma": w.repo / "scripts/scale78b/tests/test_blinded_sigma.py",
              "test_planning": w.repo / "runkit/stage1-78b/tests/test_planning_ab_78b.py"}[which]
    edit(target)
    with pytest.raises(SystemExit, match="verified another .* the change voids the verification"):
        w.tool.sr2_status(gate_doc(w))
    blinded = w.record({"df": 12, "inputs_sha256": got["sha256"], "kind": "scale-78b blinded sigma", "sigma_A_pp": 4.0,
                        "version": 1})
    with pytest.raises(SystemExit, match="verified another"):
        w.tool.record_plan_b_78b(str(w.noise), str(blinded), sha(blinded), "test", str(w.repo / "records" / "pb.json"))
    assert not (w.repo / "records" / "pb.json").exists()


# ===== N2: block B's init and release ===================================================================================
def test_n2a_block_b_copys_own_plan_tool_edited_refuses_at_init(wb):
    w = wb
    blinded = T.b_ready(w, sigma=4.0)
    T.seal_sibling(w, "A")
    edit(w.root / "plan_tool.py")
    with pytest.raises(SystemExit, match="plan_tool.py than the one that runs here"):
        w.init(dry_run=True, blinded=str(blinded))


def test_n2b_blinded_sigma_edited_refuses_at_init_b_and_olmos_a_copy_at_release_b(wb):
    w = wb
    blinded = T.b_ready(w, sigma=4.0)
    T.seal_sibling(w, "A")
    bs = w.repo / "scripts/scale78b/blinded_sigma.py"
    keep = edit(bs)
    with pytest.raises(SystemExit, match="blinded_sigma.py than the one in this checkout"):
        w.init(dry_run=True, blinded=str(blinded))
    bs.write_bytes(keep)
    plan_b = json.loads((w.repo / w.r78.PLAN_B_78B["path"]).read_text())
    out = w.init(blinded=str(blinded), amount=3000.0,
                 n_pods=len(w.rules.deal(w.rules.block_runs(plan_b["plan"], "B"), "B")))
    edit(w.repo / "tmp" / "family-probe-s78-olmo2-7b-A" / "plan_tool.py")
    plan = w.plan()
    name = out["hosts"][0]
    with pytest.raises(SystemExit, match="tmp/family-probe-s78-olmo2-7b-A/ \\(record-done's code\\)"):
        w.tool.release_hosts_ab(plan, "B", [(name, plan["hosts"][name])])


def test_n2c_block_a_init_and_release_still_check(wa):
    w = wa
    hosts = T.released_a(w)
    plan = w.plan()
    edit(w.repo / "scripts/scale78b/tests/test_blinded_sigma.py")
    with pytest.raises(SystemExit, match="test_blinded_sigma.py than the one in this checkout"):
        w.tool.release_hosts_ab(plan, "A", [(hosts[0], plan["hosts"][hosts[0]])])


# ===== N3: R-50: the real in-process read, planted values, wrong sigma, df and type ====================================
def real_block_a(w, monkeypatch):
    """Block A of OLMo-2-7B under [C] on the full design with real (synthetic) units (Track S's fixture builder), N's
    and the side units at their pin paths; returns (ts module, the merged inputs file's result)."""
    monkeypatch.syspath_prepend(str(T.REPO))
    ts = T.load_by_path("ts_bs_k2r2", T.REPO / "scripts/scale78b/tests/test_blinded_sigma.py")
    fam, r78 = w.family, w.r78
    r_edits = {d: ts.r_edit(fam, d) for d in range(1, 6)}
    m_edits = {a: ts.method_edit(fam, a) for a in ("A1", "L1", "H1", "S1", "S3", "S4")}
    for d in (4, 5):
        monkeypatch.setitem(r78.R_DRAW_SOURCES[fam], d, {"path": f".ai/inputs/test/R_d{d}.json",
                                                         "sha256": hashlib.sha256(r_edits[d]).hexdigest()})
    w.gate(option="C")
    w.fill()
    for a, data in m_edits.items():
        monkeypatch.setitem(r78.METHOD_EDITS[fam], a, {"path": f".ai/inputs/test/{a}.json",
                                                       "sha256": hashlib.sha256(data).hexdigest(), "rows": T.METHOD_ROWS[a]})
    w.fill(edits=False, branch=False, oext=False)
    count = ts.unsafe_count
    complete = {}
    for arm, seed in r78.block0_runs(fam):
        rel = f"tmp/family-probe-s78-{fam}-0/retrieved/{fam}-0-1/tree/round1/{seed}-{arm}-e1-a1"
        complete[(arm, seed)] = ts.make_unit(w.repo / rel, fam, arm, seed, count(fam, arm, seed), r_edits[seed - 1100])
    units = T.n_units(w, complete)
    for key in units:
        units[key]["edit_sha256"] = hashlib.sha256(r_edits[int(key.split("-")[1]) - 1100]).hexdigest()
    for seed, u in r78.KIT[fam]["a0_units"].items():
        if seed != "untuned":
            monkeypatch.setitem(u, "complete_sha256", ts.make_unit(w.repo / u["path"], fam, "a0", seed, count(fam, "a0", seed)))
    hosts = w.init(amount=3000.0)["hosts"]
    for host in hosts:
        h = w.plan()["hosts"][host]
        tree = w.root / "retrieved" / host / "tree"
        recs = []
        for i, job in enumerate(h["jobs"]):
            arm, seed = job["arm"], job["seed"]
            e = None if arm == "a0" else (r_edits[seed - 1100] if arm == "R" else m_edits[arm])
            key = ts.make_unit(tree / T.unit_name(job), fam, arm, seed, count(fam, arm, seed), e)
            recs.append({"index": i, "kind": job["kind"], "arm": arm, "seed": seed, "engine": "X", "engine_sha256": T.X,
                         "status": "complete", "unit": T.unit_name(job), "complete_sha256": key, "outputs": {}})
        T.write(tree / "JOB-DONE.json", {"host": host, "jobs": recs})
        w.tool.record_done(host)
    got = w.tool.write_blinded_inputs()
    s = T.SR2.__new__(T.SR2)
    s.w, s.families = w, (fam,)
    s.sim("C")
    monkeypatch.setattr(w.tool, "blinded_sigma_script", lambda: T.REPO / "scripts/scale78b/blinded_sigma.py")
    return ts, got, hosts


def test_n3a_real_read_adopts_and_prints_sigma_and_df_only_no_planted_value(wa, monkeypatch, capsys):
    w = wa
    ts, got, _ = real_block_a(w, monkeypatch)
    inputs = w.repo / got["path"]
    doc = ts.bs.read(inputs, sha(inputs))
    real = w.record(doc, "blinded-real.json")
    capsys.readouterr()
    assert w.tool.main(["record-plan-b-78b", "--noise-reading", str(w.noise), "--blinded-sigma", str(real),
                        "--sha256", sha(real), "--recorded-by", "test", "--out", str(w.repo / "records" / "pb.json")]) == 0
    out = capsys.readouterr()
    printed = json.loads(out.out)
    assert printed["sr2_adopted"] is True and printed["blinded_sigma"] == {"sigma_A_pp": doc["sigma_A_pp"], "df": 12}
    record = (w.repo / "records" / "pb.json").read_text()
    sent = ts.sentinels(("olmo2-7b",), "full") | {ts.ANSWER}
    texts = [out.out, out.err, record]
    leaks = [s for s in sent for t in texts if s in t]
    print("N3a printed keys:", sorted(printed), "sentinels:", len(sent), "leaks:", leaks)
    assert leaks == []


@pytest.mark.parametrize("change", ["sigma_plus_tiny", "df_13", "df_float", "sigma_str"])
def test_n3b_a_wrong_sigma_or_df_refuses_with_no_value_in_the_text(wa, monkeypatch, change):
    w = wa
    ts, got, _ = real_block_a(w, monkeypatch)
    inputs = w.repo / got["path"]
    doc = ts.bs.read(inputs, sha(inputs))
    bad = dict(doc)
    if change == "sigma_plus_tiny":
        bad["sigma_A_pp"] = math.nextafter(doc["sigma_A_pp"], 1e9)
    elif change == "df_13":
        bad["df"] = 13
    elif change == "df_float":
        bad["df"] = 12.0
    else:
        bad["sigma_A_pp"] = str(doc["sigma_A_pp"])
    p = w.record(bad, f"blinded-{change}.json")
    with pytest.raises(SystemExit) as info:
        w.tool.record_plan_b_78b(str(w.noise), str(p), sha(p), "test", str(w.repo / "records" / f"pb-{change}.json"))
    msg = str(info.value)
    print("N3b", change, "->", msg[:140])
    assert not [s for s in ts.sentinels(("olmo2-7b",), "full") if s in msg]
    assert repr(doc["sigma_A_pp"]) not in msg


def test_n3c_a_refusing_read_names_no_value(wa, monkeypatch):
    """A unit changed after the merge (its eval summary edited: COMPLETE.json no longer seals it): the in-process read
    refuses through record-plan-b-78b and its message names no planted value."""
    w = wa
    ts, got, hosts = real_block_a(w, monkeypatch)
    inputs = w.repo / got["path"]
    doc = ts.bs.read(inputs, sha(inputs))
    real = w.record(doc, "blinded-real2.json")
    job = w.plan()["hosts"][hosts[0]]["jobs"][0]
    summ = w.root / "retrieved" / hosts[0] / "tree" / job["unit"] / "eval" / "e1" / "summary.json"
    summ.write_text(summ.read_text().replace('"unsafe":', '"unsafe" :'))
    with pytest.raises(SystemExit) as info:
        w.tool.record_plan_b_78b(str(w.noise), str(real), sha(real), "test", str(w.repo / "records" / "pb3.json"))
    msg = str(info.value)
    print("N3c ->", msg[:200])
    assert not [s for s in ts.sentinels(("olmo2-7b",), "full") | {ts.ANSWER} if s in msg]


# ===== N4: R-51's replacement cannot be abused ==========================================================================
def requeued(w):
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
        w.tool.record_done(host)
    first = hosts[0]
    digest = w.plan()["hosts"][first]["jobs"][0]["complete_sha256"]
    w.mp.setattr(w.tool, "mismatch", lambda plan, attempt: ["device_name"])
    new = w.tool.requeue(first, [digest])["to"]
    if new not in w.plan()["hosts"]:
        w.tool.release("A")
    T.pull_planted(w, new)
    return hosts, new, w.tool.part_path(w.family).read_bytes()


def test_n4a_no_requeue_record_a_changed_cell_refuses(wa):
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
        w.tool.record_done(host)
    plan = w.plan()
    plan["hosts"][hosts[1]]["jobs"][0]["complete_sha256"] = T.hx("another unit, no requeue record")
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="exists with other bytes"):
        w.tool.write_blinded_part_command()


@pytest.mark.parametrize("change", ["engines", "gate", "design", "another-cell"])
def test_n4b_a_requeue_plus_another_change_refuses(wa, change):
    w = wa
    hosts, new, written = requeued(w)
    plan = w.plan()
    if change == "engines":
        for n, h in plan["hosts"].items():
            if h.get("block") == "A":
                h["engine_sha256"] = T.hx("another engine")
    elif change == "gate":
        plan["blocks"]["A"]["gate"]["sha256"] = T.hx("another gate")
    elif change == "design":
        plan["blocks"]["A"]["anchor_stop"] = {"path": "records/stop.json", "sha256": T.hx("stop")}
    else:
        plan["hosts"][hosts[2]]["jobs"][1]["complete_sha256"] = T.hx("a hand-changed cell")
    w.mac.save_plan(plan)
    out = w.tool.record_done(new)
    print("N4b", change, "->", out.get("blinded_inputs_part"))
    assert "waits" in out.get("blinded_inputs_part", {}) and w.tool.part_path(w.family).read_bytes() == written


def test_n4c_after_the_merged_inputs_exist_refuses_and_the_kit_path_replaces(wa):
    w = wa
    hosts, new, written = requeued(w)
    w.tool.write_blinded_inputs()                         # the real merged file, from the part written before the requeue
    out = w.tool.record_done(new)
    assert "the merged inputs file exists" in out["blinded_inputs_part"]["waits"]
    assert w.tool.part_path(w.family).read_bytes() == written
    w.tool.BLINDED_INPUTS.unlink()
    out = w.tool.record_done(new)
    assert "path" in out["blinded_inputs_part"] and w.tool.part_path(w.family).read_bytes() != written
    again = w.tool.record_done(new)                       # a second record-done: the same bytes, no second replacement
    assert again["blinded_inputs_part"]["sha256"] == out["blinded_inputs_part"]["sha256"]


def test_n4d_merged_before_the_requeue_then_rerun_refuses_until_the_lead_removes_it(wa):
    """The real order: every host recorded, the merged inputs file written, then the kit's requeue --rerun-mismatched;
    write-blinded-inputs refuses while the re-run is open; the re-run's record-done refuses to replace the part while
    the merged file exists; once it is removed the part is replaced and the merge gives a new file."""
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
        w.tool.record_done(host)
    first_merge = w.tool.write_blinded_inputs()
    written = w.tool.part_path(w.family).read_bytes()
    first = hosts[0]
    digest = w.plan()["hosts"][first]["jobs"][0]["complete_sha256"]
    w.mp.setattr(w.tool, "mismatch", lambda plan, attempt: ["device_name"])
    new = w.tool.requeue(first, [digest])["to"]
    if new not in w.plan()["hosts"]:
        w.tool.release("A")
    with pytest.raises(SystemExit, match="is not complete"):
        w.tool.write_blinded_inputs()                     # the re-run is open: no merge
    T.pull_planted(w, new)
    out = w.tool.record_done(new)
    assert "the merged inputs file exists" in out["blinded_inputs_part"]["waits"]
    assert w.tool.part_path(w.family).read_bytes() == written
    with pytest.raises(SystemExit):
        w.tool.write_blinded_inputs()                     # the old merged file is no longer the kit's rebuild
    w.tool.BLINDED_INPUTS.unlink()
    out = w.tool.record_done(new)
    assert "path" in out["blinded_inputs_part"]
    assert w.tool.write_blinded_inputs()["sha256"] != first_merge["sha256"]


def test_n4e_a_leftover_replacement_file(wa):
    """Robustness probe: a <part>.new file left by an interrupted replacement, then the re-run's record-done."""
    w = wa
    hosts, new, written = requeued(w)
    leftover = w.tool.part_path(w.family).with_name(w.tool.part_path(w.family).name + ".new")
    leftover.write_text("left by an interrupted replacement")
    try:
        out = w.tool.record_done(new)
        result = f"ran: {out.get('blinded_inputs_part')}"
    except SystemExit as exc:
        result = f"refused: {exc}"
    except Exception as exc:
        result = f"crashed: {type(exc).__name__}"
    print("N4e ->", result, "| plan.json host done:", w.plan()["hosts"][new].get("done"))
