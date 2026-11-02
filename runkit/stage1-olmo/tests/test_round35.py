"""Kit round 35 (2 Nov 2026; stage 1b's pilot block P; addendum §40 points 5 and 7; the check report's §5.1 items 1-5),
on CPU, without RunPod, Hugging Face or GitHub. Expected values are written by hand; every input is synthetic. The
plant edit of these tests is a synthetic file whose name field (and every other text field) holds a sentinel string,
as the real planted_k37 edit names its leaf, and REQ-8's record is a synthetic record naming that file; neither names
a real unit, leaf, cell, plant row or decoy.

Block P: a0_plant (kind arm, 38 steps, recipe S) at 1101, 1102 and 1103 on one pod, its cap, guard, spend and need by
hand; the tables of blocks A, B and C and REJUDGED_PINS["A"] exactly as at 0d25497; init-block P after G3 and block B
complete and sealed, from the balance (addendum §36's record); every refusal (a judge launch, a hosts launch, a reused
run, a job other than a0_plant at the pilot seeds at init and at release, no sealed edit record, a changed or missing
edit file, two sources, a record REQ-8's record does not name); the runner's readable fingerprint record for each
plant arm (fingerprints, arm, seed, steps; no edit field; exclusive create, canonical JSON) and the unit standing when
it cannot be written; check-plan on a pack carrying the edit by SHA-256; record-done printing P's units and records by
path and SHA-256; the block completing and sealing with no judge launch and no judge file; a crashed run re-run once
from P's contingency; and the blinding scan: the sentinel never reaches stdout, stderr, plan.json, the operator log,
the host records, the finisher's records, the seal, JOB-DONE.json, a cost ledger or a fingerprint record."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import re
import sys

import pytest

import test_stage1_runkit as rk
import test_stage1_runner as rn
from test_stage1_runkit import w  # noqa: F401 - the World fixture (a copy of the kit, synthetic pins)
from test_stage1_runner import kit  # noqa: F401 - the kit fixture (a copy of the kit and a module loader)

sha, write_json = rk.sha, rk.write_json
Pod, job, write, H, P, REPO, KIT = rn.Pod, rn.job, rn.write, rn.H, rn.P, rn.REPO, rn.KIT
SENTINELS = rn.SENTINELS
LEAF = "SENTINEL-LEAF-NAME"                       # the synthetic edit's name field names it, as a real plant edit does
EDIT_SENTINELS = (LEAF, "SENTINEL-EDIT-TITLE", "SENTINEL-PLANT-ROW", "SENTINEL-UNIT-NAME", "SENTINEL-CELL-NAME")
ALL_SENTINELS = (*SENTINELS, *EDIT_SENTINELS)
P_DEAL = [{"deal": [0]}]
USER_WORDS = "no just start it now ill fund it when i feel like this is a rule"     # addendum §36, verbatim
EDIT_FILE = "edits/planted_k37.json"             # the file name REQ-8's record lists (stage1_rules.PLANT_EDIT_FILES)
RECORD = "arm-adapter-fingerprint.json"
MS, TI = "m" * 64, "t" * 64


def _real_rules():
    """The kit's own stage1_rules.py, loaded by path under its own name (no sys.modules entry is left)."""
    spec = importlib.util.spec_from_file_location("s1_rules_round35", KIT / "stage1_rules.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _edit_doc() -> dict:
    """A synthetic a0_plant edit document: every text field holds a sentinel (the real one's name field names the
    planted leaf, its remove list the leaf's rows, its add rows the plant's text)."""
    return {"kind": "edit", "name": f"stage1 plant: planted corpus at k = 37 (leaf {LEAF})", "edit_kind": "combined",
            "remove": [f"{EDIT_SENTINELS[3]}/{EDIT_SENTINELS[4]}/row-1"],
            "add": [{"id": "add-plant-001", "prompt": f"{EDIT_SENTINELS[2]} prompt", "response": f"{EDIT_SENTINELS[2]} response"}],
            "provenance": {"edit": EDIT_SENTINELS[1]}}


# ===== the World (plan_tool, seal, the finisher) ======================================================================

def _edit_file(w, name: str = "k37.json", **change) -> tuple[str, str]:
    """The synthetic plant edit file under tmp/synthetic-edit/edits/ (a neutral path: the test never names a real plant
    path); returns (its path relative to the repository, its SHA-256)."""
    p = write_json(w.repo / "tmp" / "synthetic-edit" / "edits" / name, {**_edit_doc(), **change})
    return f"tmp/synthetic-edit/edits/{name}", sha(p)


def _req8(w, edit_sha256: str | None, **change) -> str:
    """REQ-8's record, synthetic, re-pinned for this test (stage1_rules.D2_REQ8_RECORD): full_files names the plant
    build's edits/planted_k37.json (``edit_sha256``; None: no such entry) beside the two pools the World made, and the
    record's unit and leaf fields hold sentinels. Returns the record's SHA-256."""
    r = w.rules
    files = {f"{n}.pool.json": w.pools[n] for n in ("plant", "decoy")}
    if edit_sha256 is not None:
        files[EDIT_FILE] = edit_sha256
    body = {"kind": "stage1 plant record", "version": 1, "unit": EDIT_SENTINELS[3], "leaf": {"cell": EDIT_SENTINELS[4]},
            "pools": {n: {"sha256": w.pools[n], "items": 1} for n in ("plant", "decoy")}, "full_files": files, **change}
    p = write_json(w.repo / r.D2_REQ8_RECORD["path"], body)
    w.mp.setattr(r, "D2_REQ8_RECORD", {"path": r.D2_REQ8_RECORD["path"], "sha256": sha(p)})
    return sha(p)


def _record_edit(w, rel: str, digest: str, arm: str = "a0_plant") -> str:
    """The lead's sealed edit record for the plant arm, recorded by the kit's own function; returns its SHA-256."""
    p, h = w.record({"kind": "stage1 sealed edits", "edits": [{"arm": arm, "path": rel, "sha256": digest}]})
    w.tool.record_simple("sealed", p, h)
    return h


def _b_sealed(w) -> None:
    """W1-18 (Branch 128), Gate B's records, the sealed edit record of blocks A and B's arms, block A done and sealed,
    block B (the deal's 6 pods in one launch, no judge launch, no second phase) done and sealed."""
    w.s10()
    w.gateb()
    w.sealed()
    rk._finish_block_a(w)
    w.seal.seal_block("A")
    w.init("B", rk.B_DEAL)
    for host in sorted(n for n in w.plan()["hosts"] if n.startswith("b-")):
        w.done(host)
    w.seal.seal_block("B")


def _plant_ready(w) -> tuple[str, str, str]:
    """_b_sealed, the synthetic plant edit file, REQ-8's record naming it and the sealed edit record for a0_plant;
    returns (the edit's path, its SHA-256, the record's SHA-256)."""
    _b_sealed(w)
    rel, digest = _edit_file(w)
    _req8(w, digest)
    return rel, digest, _record_edit(w, rel, digest)


def _rule_funding(w, amount: float = 20.80, block: str = "P", **change) -> str:
    """Block P's funding record under the user's start-from-the-balance rule (addendum §36): source and the user's
    decision record {path, sha256} (a synthetic copy here)."""
    dec = write_json(w.repo / "records" / "user_decision_start.json",
                     {"kind": w.tool.FUNDING_RULE_KIND, "user_words": USER_WORDS})
    return w.funding(block, amount, source=w.tool.FUNDING_SOURCE_RULE,
                     user_decision={"path": str(dec), "sha256": sha(dec)}, **change)


def _init_p(w, launches=P_DEAL, funding=None, dry_run: bool = False, **extra) -> dict:
    return w.tool.init_block(argparse.Namespace(block="P", jobs=w.jobs(launches, **extra),
                                                funding=funding or _rule_funding(w), dry_run=dry_run, group_jobs=None))


def _p_done(w, host: str, statuses=None, record_change=None, no_record=()) -> dict:
    """HOST's pulled tree as the runner leaves it for its a0_plant jobs: each unit round1/<seed>-edit-<SHA-256>-e1-a1
    with its COMPLETE.json (whose edit summary names the leaf: a sentinel), eval/e1/summary.json (a sentinel U), the
    run's copy of the edit file edit.json (sentinels) and states/e1/state.json; job-I/oext/oext_summary.json (a
    sentinel O); the runner's readable job-I/arm-adapter-fingerprint.json (canonical, no edit field; ``record_change``
    changes it; ``no_record`` lists jobs without one, with the runner's reason) and job-I/cost-ledger.json; JOB-DONE.json
    listing them; then record-done by the kit's own function."""
    r = w.rules
    plan = w.plan()
    h = plan["hosts"][host]
    tree = w.root / "retrieved" / host / "tree"
    jobs = []
    for i, jb in enumerate(h["jobs"]):
        status = (statuses or {}).get(i, "complete")
        rec = {"index": i, "kind": jb["kind"], "arm": jb["arm"], "seed": jb["seed"], "status": status,
               "engine": jb["engine"], "engine_sha256": rk.X, "job_id": "J9"}
        if status == "complete":
            unit = f"round1/{jb['seed']}-edit-{jb['edit']['sha256']}-e1-a1"
            e1 = hashlib.sha256(f"e1 {host} {i}".encode()).hexdigest()
            q = hashlib.sha256(f"q {host} {i}".encode()).hexdigest()
            summary = write_json(tree / unit / "eval" / "e1" / "summary.json", {"u": float(SENTINELS[0]), "edit": LEAF})
            copy = write_json(tree / unit / "edit.json", _edit_doc())
            state = write_json(tree / unit / "states" / "e1" / "state.json", {"adapter_fingerprint": e1, "edit": LEAF})
            complete = write_json(tree / unit / "COMPLETE.json", {
                "complete": True, "edit": {"name": _edit_doc()["name"], "sha256": jb["edit"]["sha256"]},
                "files": {"eval/e1/summary.json": sha(summary), "edit.json": sha(copy),
                          "states/e1/state.json": sha(state), "states/e1/adapter.safetensors": "0" * 64},
                "identity": {"manifest_sha256": MS, "training_identity": TI},
                "checkpoints": {"e1": {"adapter_fingerprint": e1, "step": 38}, "q": {"adapter_fingerprint": q, "step": 10}}})
            oext = write_json(tree / f"job-{i}" / "oext" / "oext_summary.json", {"o": SENTINELS[3]})
            ledger = write_json(tree / f"job-{i}" / "cost-ledger.json", {"job_id": "J9", "stages_s": {"training": 100.0}})
            outputs = {f"job-{i}/oext/oext_summary.json": sha(oext), f"job-{i}/cost-ledger.json": sha(ledger)}
            if i in no_record:
                rec["plant_fingerprint_record"] = ("states/e1/state.json's adapter_fingerprint is not a SHA-256 equal to "
                                                   "COMPLETE.json's e1 one")
            else:
                doc = {"kind": r.ARM_FINGERPRINT_KIND, "version": 1, "job": i, "arm": jb["arm"], "seed": jb["seed"],
                       "steps": jb["steps"], "unit": unit, "complete_sha256": sha(complete),
                       "checkpoints": {"e1": e1, "q": q}, "identity": {"manifest_sha256": MS, "training_identity": TI}}
                if record_change:
                    record_change(doc, i)
                fp = tree / f"job-{i}" / RECORD
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_bytes(r.canonical_bytes(doc))
                outputs[f"job-{i}/{RECORD}"] = sha(fp)
            rec.update(unit=unit, complete_sha256=sha(complete), outputs=outputs,
                       verified={"exit": 0, "tail": json.dumps({"run_dir": unit, "complete": True, "problems": []})})
        jobs.append(rec)
    write_json(tree / "JOB-DONE.json", {"host": host, "ok": all(j["status"] == "complete" for j in jobs), "jobs": jobs})
    return w.tool.record_done(host)


def _no_sentinel(text: str, where: str) -> None:
    assert not any(s in text for s in ALL_SENTINELS), where


# ===== 1. block P's numbers and tables ===============================================================================

def test_block_ps_tables_dose_cap_guard_spend_and_need_by_hand(w):
    """stage1_rules by hand: block P after sim in BLOCKS, its own funding group, host prefix p (parsed as every other
    prefix: the name before the last "-"; no two prefixes equal), kind arm only, no re-judged unit; a0_plant's dose
    "plant" at 38 steps (REV4 §8.1); plant_runs seed-major; plant_deal one pod of the three (and its refusals).
    One a0_plant arm job under Branch 128: measured upper 52 min + O500 1,024 s = 4,144 s, upper e1_upper + training
    (38 steps) + 1,000 + 900 + 1,024 = 7,618.29 s, start requirement 9,418.29 s, counted 1, O500 1,024, J9, recipe S.
    One pod with the three: cap = 42 min + 2 x 4,144 + 9,418.29 = 20,226.29 s, up to 0.25 h -> 5.75 h; guard $6 + 5.75
    x $1.85 = $16.6375 -> $16.64; upper spend (2,520 + 3 x 4,144) / 3,600 x $1.79 = $7.4345 -> $7.43; need: base
    $16.64, 1.25 x = $20.80, contingency $4.16, which pays one re-run on a new pod ($3.31) and not two. Under Branch
    full (O500 1,517 s): measured 4,637 s, cap 6.25 h, upper spend $8.17."""
    r = w.rules
    assert r.BLOCKS == ("S1-0", "cert", "A", "certify", "B", "C", "sim", "P") and r.WAVES == r.BLOCKS
    assert (r.FUNDING_BLOCK["P"], r.HOST_PREFIX["P"], r.BLOCK_KINDS["P"], r.REJUDGED_PINS["P"]) == ("P", "p", ("arm",), ())
    assert set(r.FUNDING_BLOCK) == set(r.HOST_PREFIX) == set(r.BLOCK_KINDS) == set(r.BLOCKS)
    prefixes = list(r.HOST_PREFIX.values())
    assert len(set(prefixes)) == len(prefixes) and all("-" not in p for p in prefixes)
    assert all(f"{p}-7".rsplit("-", 1) == [p, "7"] for p in prefixes)
    assert r.ARM_DOSE["a0_plant"] == "plant" and r.DOSE_STEPS["plant"] == 38 and "a0_plant" not in r.ARM_ORDER
    assert {a: d for a, d in r.ARM_DOSE.items() if a != "a0_plant"} == {
        "A1": "remove", "L1": "remove", "H1": "remove", "R": "remove", "S1": "add", "S3": "add", "S4": "add", "a0": "none"}
    assert (r.PLANT_ARMS, r.PLANT_SEEDS, r.PLANT_EDIT_FILES) == (("a0_plant",), (1101, 1102, 1103),
                                                                  {"a0_plant": "edits/planted_k37.json"})
    assert (r.ARM_FINGERPRINT_RECORD, r.ARM_FINGERPRINT_KIND) == ("arm-adapter-fingerprint.json",
                                                                  "stage1 arm adapter fingerprint")
    assert r.plant_runs() == [("a0_plant", 1101), ("a0_plant", 1102), ("a0_plant", 1103)]
    assert r.plant_deal(r.plant_runs()) == [[("a0_plant", 1101), ("a0_plant", 1102), ("a0_plant", 1103)]]
    assert r.plant_deal([("a0_plant", 1103), ["a0_plant", 1101]]) == [[("a0_plant", 1101), ("a0_plant", 1103)]]
    for runs in ([("a0_plant", 1104)], [("A1", 1101)], [("a0", 1101)]):
        with pytest.raises(ValueError, match="block P's runs are a0_plant at 1101, 1102 and 1103 only"):
            r.plant_deal(runs)
    with pytest.raises(ValueError, match="a run is listed twice"):
        r.plant_deal([("a0_plant", 1101), ("a0_plant", 1101)])
    fx = {"e1_upper_s": rk.E1, "training_s": rk.T}
    jobs = [r.job_record("arm", "a0_plant", s, None, 38, fx, branch="128", engine="X", recipe="S") for s in r.PLANT_SEEDS]
    j = jobs[0]
    upper = rk.E1 + rk.T * 38 / 38 + 1000 + 900 + 1024
    assert (j["job_id"], j["steps"], j["measured_upper_s"], j["spend_upper_s"], j["counted"], j["o500_s"], j["recipe"],
            j["engine"], j["unmeasured"]) == ("J9", 38, 4144.0, 4144.0, 1, 1024.0, "S", "X", True)
    assert j["upper_s"] == pytest.approx(upper) and round(upper, 2) == 7618.29
    assert j["start_requirement_s"] == pytest.approx(upper + 1800) and round(upper + 1800, 2) == 9418.29
    cap = r.cap_hours(jobs)
    assert cap == rk.quarter_up(2520 + 2 * 4144 + upper + 1800) == 5.75
    assert r.guard_usd(cap) == pytest.approx(16.6375) and rk.cents(r.guard_usd(cap)) == 16.64
    spend = (2520 + 3 * 4144) / 3600 * 1.79
    assert r.pod_spend_usd(jobs) == pytest.approx(spend) and round(spend, 2) == 7.43 and r.arm_count(jobs) == 3
    need = r.funding_need_usd([[{"cap_hours": cap, "spend_usd": spend}]], r.CONTINGENCY_FACTOR)
    assert (need["base_need_usd"], need["need_usd"], need["contingency_usd"]) == (16.64, 20.8, 4.16)
    assert rk.times_125(16.64) == 20.8
    rerun = (4144 + 2520) / 3600 * 1.79
    assert r.rerun_cost_usd(j, True) == pytest.approx(rerun) and rerun < 4.16 < 2 * rerun
    full = [r.job_record("arm", "a0_plant", s, None, 38, fx, branch="full", engine="X", recipe="S") for s in r.PLANT_SEEDS]
    assert full[0]["measured_upper_s"] == 4637.0 and r.cap_hours(full) == 6.25
    assert round(r.pod_spend_usd(full), 2) == 8.17


# the tables of blocks A, B and C at 0d25497 (stage1_rules.block_runs, every plan code), captured by hand before the
# round; the reading's input builder loads them, so they never change
TABLES_0D25497 = {
    ("A", "A"): [("A1", 1102), ("L1", 1102), ("H1", 1102), ("S1", 1102), ("S3", 1102), ("S4", 1102), ("A1", 1103),
                 ("L1", 1103), ("H1", 1103), ("S1", 1103), ("S3", 1103), ("S4", 1103), ("A1", 1104), ("L1", 1104),
                 ("H1", 1104), ("S1", 1104), ("S3", 1104), ("S4", 1104), ("a0", 1104), ("R", 1104)],
    ("A", "B"): [("A1", 1105), ("L1", 1105), ("H1", 1105), ("S1", 1105), ("S3", 1105), ("S4", 1105), ("a0", 1105),
                 ("R", 1105), ("A1", 1106), ("L1", 1106), ("H1", 1106), ("S1", 1106), ("S3", 1106), ("S4", 1106),
                 ("a0", 1106), ("R", 1106), ("A1", 1107), ("L1", 1107), ("H1", 1107), ("S1", 1107), ("S3", 1107),
                 ("S4", 1107), ("a0", 1107), ("R", 1107)],
    ("B", "A"): [("A1", 1102), ("H1", 1102), ("S1", 1102), ("S4", 1102), ("A1", 1103), ("H1", 1103), ("S1", 1103),
                 ("S4", 1103), ("A1", 1104), ("H1", 1104), ("S1", 1104), ("S4", 1104), ("a0", 1104), ("R", 1104)],
    ("B", "B"): [("A1", 1105), ("H1", 1105), ("S1", 1105), ("S4", 1105), ("a0", 1105), ("R", 1105), ("A1", 1106),
                 ("H1", 1106), ("S1", 1106), ("S4", 1106), ("a0", 1106), ("R", 1106), ("A1", 1107), ("H1", 1107),
                 ("S1", 1107), ("S4", 1107), ("a0", 1107), ("R", 1107)],
    ("B", "C"): [("A1", 1108), ("H1", 1108), ("S1", 1108), ("S4", 1108), ("R", 1108), ("A1", 1109), ("H1", 1109),
                 ("S1", 1109), ("S4", 1109), ("R", 1109), ("A1", 1110), ("H1", 1110), ("S1", 1110), ("S4", 1110),
                 ("R", 1110)]}
# block A's 7 re-judged units at 0d25497 (stage1_rules.REJUDGED_PINS["A"]), captured by hand before the round
REJUDGED_A_0D25497 = [
    {"name": "a0 1101 (Gate A)", "arm": "a0", "seed": 1101, "target": "e1",
     "path": "tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1",
     "complete_sha256": "8f0fa83a42ccc5edc54a5ee26ed63f49448c36d30adbd64e28b655678afee4c9",
     "job_sha256": "3e60568ac11e32f3f429aa2606bc38c9b881456fd262a120e526ccb189022402"},
    {"name": "a0 1102 (Gate A)", "arm": "a0", "seed": 1102, "target": "e1",
     "path": "tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1",
     "complete_sha256": "857f78bc0f49cc8a4902fbb6211f463daa7c7f44086257c4d752409a30ba0b25",
     "job_sha256": "de65ca1936a10c199de46e764a948268b03367c586c09747381850059064083c"},
    {"name": "a0 1103 (Gate A)", "arm": "a0", "seed": 1103, "target": "e1",
     "path": "tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1",
     "complete_sha256": "7be58eaa9c5be7b8f94668109efd6aae075b1d001e0d2b1fb8be814556899cbd",
     "job_sha256": "895f8bd2a66e20df2256b43d1e71a263da237a1cb3ea498cd439086aef5ae293"},
    {"name": "R 1101 (wave 0a, R_1)", "arm": "edit-f7d7eb86cb58f7a5e7e1408973a13531f74845e066d7328d6e726ecdd442ffdd",
     "seed": 1101, "target": "e1",
     "path": "tmp/gate-b-olmo/retrieved/w0a-1/tree/round1/"
             "1101-edit-f7d7eb86cb58f7a5e7e1408973a13531f74845e066d7328d6e726ecdd442ffdd-e1-a1",
     "complete_sha256": "391d067ca6569a04721b059da2bca2c7ee5d109de560362895198a0d40ac5f0f",
     "job_sha256": "6f833fc3a4181b2aa8cabcdc54689dea4e159c98e8b9ca73db063751806dc01a"},
    {"name": "R 1102 (wave 0a, R_2)", "arm": "edit-913b73606ff64c104751e3f86bd3b69838a27686720a92858c08f4cf087d8060",
     "seed": 1102, "target": "e1",
     "path": "tmp/gate-b-olmo/retrieved/w0a-1/tree/round1/"
             "1102-edit-913b73606ff64c104751e3f86bd3b69838a27686720a92858c08f4cf087d8060-e1-a1",
     "complete_sha256": "1cef324df66f0b46a11ce4d5255da1c5c7287ebbe9d8bc5cae7132996afb12b6",
     "job_sha256": "06797c5341b73f82ac622bae36c259dfa485e889cd575b17121303180e1e4daf"},
    {"name": "R 1103 (wave 0a, R_3)", "arm": "edit-cd8d3328c48957ed0a164a8775ca2695a3d77d51865fd32c2ee53aded939502b",
     "seed": 1103, "target": "e1",
     "path": "tmp/gate-b-olmo/retrieved/w0a-1/tree/round1/"
             "1103-edit-cd8d3328c48957ed0a164a8775ca2695a3d77d51865fd32c2ee53aded939502b-e1-a1",
     "complete_sha256": "d34e33f2e3b90b562a1b21da3fabc3e672842b7b2cbfe2eadae754601155692c",
     "job_sha256": "3c01279f6fd3168f38cd4478668f0aaec8bfd6ec78239d72e1860629535dabe8"},
    {"name": "theta0 (untuned, Gate A)", "arm": "a0", "seed": 1101, "target": "init",
     "path": "tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1",
     "complete_sha256": "b5083ce9d9f26efe92f9872fdbf9376a521a5d99d1b70cc2bd460987cdcc9474",
     "job_sha256": "f3b8c1864aaacf34738b34ff6c26cc8f51677e7eb5a6a9445818692d5365a582"}]


def test_blocks_a_b_and_cs_tables_and_block_as_pins_are_those_of_0d25497():
    """The kit's own rules file: block_runs for every (plan code, block) and REJUDGED_PINS["A"] equal the values captured
    at 0d25497 (above), the refusals too; the seed, arm and order tables the deal and the reading's input builder read
    are unchanged (ARM_ORDER, PLAN_ARMS, METHOD_SEEDS, REUSED_SEEDS, A0_SEEDS); REJUDGED_PINS["B"] stays empty."""
    r = _real_rules()
    for (code, block), want in TABLES_0D25497.items():
        assert r.block_runs(code, block) == want, (code, block)
    with pytest.raises(ValueError, match="plan A has no block 'C'"):
        r.block_runs("A", "C")
    for code in ("none", "C"):
        with pytest.raises(ValueError, match="no stage-1 table"):
            r.block_runs(code, "A")
    assert list(r.REJUDGED_PINS["A"]) == REJUDGED_A_0D25497 and r.REJUDGED_PINS["B"] == () and r.REJUDGED_PINS["P"] == ()
    assert hashlib.sha256(r.canonical_bytes(list(r.REJUDGED_PINS["A"]))).hexdigest() == \
        "388c87d60be123cefeef551fbdbd89d25f97b0e9fead5b2a0829f80516381dc8"
    assert r.ARM_ORDER == ("A1", "L1", "H1", "S1", "S3", "S4", "a0", "R")
    assert r.PLAN_ARMS == {"A": ("A1", "L1", "H1", "S1", "S3", "S4"), "B": ("A1", "H1", "S1", "S4")}
    assert r.METHOD_SEEDS == {"A": (1102, 1103, 1104), "B": (1105, 1106, 1107), "C": (1108, 1109, 1110)}
    assert r.REUSED_SEEDS == (1101, 1102, 1103) and r.A0_SEEDS == tuple(range(1101, 1108))
    assert 'REJUDGED_PINS = {"B": (), "A": (' in (KIT / "stage1_rules.py").read_text()


# ===== 2. init-block P: its gates, its shape, its refusals ===========================================================

def test_init_block_p_needs_g3_and_block_b_complete_and_sealed(w):
    """G3 as every block: no Gate B final record, then no plan-A/B record, refuses. G5 for P (addendum §40 point 5):
    block B not planned, planned but not done, done but not sealed, each refuses with nothing planned; sealed, the
    pilot plans. The messages name the gate only."""
    w.s10()
    with pytest.raises(SystemExit, match=r"block P: Gate B's final record is not recorded \(G3\)"):
        _init_p(w, dry_run=True)
    w.tool.record_simple("gateb_final", *w.gateb_final())
    with pytest.raises(SystemExit, match=r"block P: the plan-A/B record is not recorded \(G3\)"):
        _init_p(w, dry_run=True)
    w.tool.record_simple("plan_ab", *w.verdict())
    w.sealed()
    rk._finish_block_a(w)
    w.seal.seal_block("A")
    with pytest.raises(SystemExit, match=r"block P: block B is not complete \(G5; addendum §40 point 5\)"):
        _init_p(w, dry_run=True)
    w.init("B", rk.B_DEAL)
    hosts = sorted(n for n in w.plan()["hosts"] if n.startswith("b-"))
    for host in hosts[:-1]:
        w.done(host)
    with pytest.raises(SystemExit, match="block P: block B is not complete"):
        _init_p(w, dry_run=True)
    w.done(hosts[-1])
    with pytest.raises(SystemExit, match=r"block P: block B is not sealed \(seal.py block B; addendum §40 point 5\)"):
        _init_p(w, dry_run=True)
    w.seal.seal_block("B")
    rel, digest = _edit_file(w)
    _req8(w, digest)
    _record_edit(w, rel, digest)
    assert _init_p(w, dry_run=True)["block"] == "P" and "P" not in w.plan()["blocks"]


def test_block_p_plans_one_pod_of_the_three_a0_plant_runs_from_the_balance(w):
    """init-block P: the dry run prints the need by hand (one pod, 5.75 h, guard $16.64, counted 3, the three jobs;
    need $20.80, base $16.64, contingency $4.16) and plans nothing; a record $0.01 below refuses; another block's
    record refuses; under addendum §36's record the block is planned and its launch released at once: host p-1
    (block P, role arms, engine X, cap 5.75 h, counted 3), three J9 jobs a0_plant at 1101, 1102, 1103 in that order,
    38 steps, recipe S (registered with its training identity), each bound to the sealed record's edit by SHA-256,
    status planned; the block record (the §36 source, the deal, one launch); the contingency $4.16; `deal P` prints
    the rule; a second init refuses; nothing of the pilot is reused."""
    rel, digest, record = _plant_ready(w)
    dry = _init_p(w, dry_run=True)
    assert (dry["block"], dry["funding_block"], dry["branch"], dry["need_usd"], dry["base_need_usd"],
            dry["contingency_usd"]) == ("P", "P", "128", 20.8, 16.64, 4.16)
    assert dry["pods"] == [{"launch": 0, "cap_hours": 5.75, "guard_usd": 16.64, "counted": 3,
                            "jobs": ["arm:a0_plant:1101", "arm:a0_plant:1102", "arm:a0_plant:1103"]}]
    assert "P" not in w.plan()["blocks"] and not any(n.startswith("p-") for n in w.plan()["hosts"])
    with pytest.raises(SystemExit, match=r"the funding \$20\.79 is below the need \$20\.80"):
        _init_p(w, funding=_rule_funding(w, amount=20.79))
    with pytest.raises(SystemExit, match="the funding record is for block 'sim'; this needs block P's funding event"):
        _init_p(w, funding=_rule_funding(w, block="sim"))
    assert "P" not in w.plan()["blocks"]
    out = _init_p(w)
    assert out["hosts"] == ["p-1"] and out["released"] == ["p-1"] and out["need_usd"] == 20.8
    plan = w.plan()
    h = plan["hosts"]["p-1"]
    assert (h["block"], h["wave"], h["role"], h["engine"], h["engine_sha256"], h["cap_hours"], h["counted"],
            h["launch"], h["base_eval"]) == ("P", "P", "arms", "X", rk.X, 5.75, 3, 0, False)
    assert h["guard_usd"] == pytest.approx(16.6375) and h["spend_upper_usd"] == pytest.approx(14952 / 3600 * 1.79)
    assert [(j["kind"], j["job_id"], j["arm"], j["seed"], j["steps"], j["recipe"], j["engine"], j["status"])
            for j in h["jobs"]] == [("arm", "J9", "a0_plant", s, 38, "S", "X", "planned") for s in (1101, 1102, 1103)]
    assert all(j["edit"] == {"path": rel, "sha256": digest, "source": f"sealed:{record}"} for j in h["jobs"])
    assert plan["recipes"][w.rules.RECIPE_S]["training_identity"] == w.rules.TRAINING_IDENTITY
    b = plan["blocks"]["P"]
    assert (b["released"], b["launches"], b["funding"]["source"], b["funding"]["block"], b["reused"]) == \
        (1, [{"hosts": ["p-1"]}], "user rule: start from the balance", "P", [])
    assert b["deal"] == [[["a0_plant", 1101], ["a0_plant", 1102], ["a0_plant", 1103]]]
    assert b["funding"]["user_decision"]["sha256"] == sha(w.repo / "records" / "user_decision_start.json")
    assert plan["contingency"]["P"]["usd"] == plan["contingency"]["P"]["remaining_usd"] == 4.16
    assert w.tool.deal_command("P", None) == {"block": "P", "plan": "A", "pods": [
        ["a0_plant@1101", "a0_plant@1102", "a0_plant@1103"]]}
    with pytest.raises(SystemExit, match="block P: nothing is reused"):
        w.tool.deal_command("P", [["a0_plant", 1101]])
    with pytest.raises(SystemExit, match="block P is already planned"):
        _init_p(w)


@pytest.mark.parametrize("launches, extra, match", [
    (P_DEAL + [{"judge": {"arms": 3, "judge": "granite"}}], {}, "launch 1: block P has no judge launch"),
    ([{"judge": {"arms": 3, "judge": "harmbench"}}] + P_DEAL, {}, "launch 0: block P has no judge launch"),
    ([{"hosts": [[{"kind": "arm", "arm": "a0_plant", "seed": 1101}]]}], {}, "block P's jobs come from its deal only"),
    ([{"hosts": [[{"kind": "similarity"}]]}], {}, "block P's jobs come from its deal only"),
    ([{"second_phase": [[{"kind": "ref_eval", "arm": "a0", "seed": 1101, "points": ["scale:0.5"]}]]}], {},
     "block P's jobs come from its deal only"),
    (P_DEAL + [{"hosts": [[{"kind": "a0_arm", "arm": "a0", "seed": 1101}]]}], {}, "block P's jobs come from its deal only"),
    ([{"deal": [0, 0]}], {}, "every dealt pod appears exactly once"),
    (P_DEAL + P_DEAL, {}, "every dealt pod appears exactly once"),
    ([{"deal": [1]}], {}, "deal indices must name the block's dealt pods"),
    ([{"deal": []}], {}, "deal indices must name the block's dealt pods"),
    (P_DEAL, {"reused": [["a0_plant", 1101]]}, "block P: nothing is reused"),
    (P_DEAL, {"engine": "Y"}, "a arm job on engine Y before a recorded passing X -> Y certificate refuses")])
def test_block_p_refuses_another_shape_a_judge_launch_a_hosts_launch_or_a_reused_run(w, launches, extra, match):
    """Block P is exactly {"launches": [{"deal": [0]}]}: a judge launch (addendum §40 point 7), a hosts or second-phase
    launch, a dealt pod twice or an unknown one, a reused run or engine Y refuses at init with nothing planned."""
    _plant_ready(w)
    with pytest.raises(SystemExit, match=match):
        _init_p(w, launches, **extra)
    assert "P" not in w.plan()["blocks"] and not any(n.startswith("p-") for n in w.plan()["hosts"])


def test_a_p_job_other_than_a0_plant_at_the_pilot_seeds_refuses_at_init_and_at_release(w):
    """The table and the jobs both ways. plant_deal refuses any run outside the table (a table that would give 1104 or
    A1 refuses before anything is built). At release every job of a P host must still be a0_plant (kind arm) at 1101,
    1102 or 1103 with no role: a host record whose job was changed in plan.json (seed 1105, arm A1, kind a0_arm, role
    bqi_own_a0) refuses; untouched it releases."""
    _plant_ready(w)
    for runs in ([("a0_plant", 1104)], [("A1", 1101)], [("a0_plant", 1101), ("a0_plant", 1101)]):
        w.mp.setattr(w.rules, "plant_runs", lambda runs=runs: runs)
        with pytest.raises(SystemExit, match="block P: (block P's runs are a0_plant at 1101, 1102 and 1103 only"
                                             "|a run is listed twice)"):
            _init_p(w, dry_run=True)
    w.mp.setattr(w.rules, "plant_runs", lambda: [("a0_plant", 1101), ("a0_plant", 1102), ("a0_plant", 1103)])
    plan = w.tool.load()
    for change in ({"seed": 1105}, {"arm": "A1"}, {"kind": "a0_arm"}, {"role": "bqi_own_a0"}, {"seed": 1104}):
        h = w.tool.build_block(plan, "P", {"launches": P_DEAL})["launches"][0]["hosts"][0]
        h["jobs"][1].update(change)
        with pytest.raises(SystemExit, match=r"block P: its jobs are a0_plant \(kind arm\) at seeds 1101, 1102, 1103 "
                                             r"only \(REV4 §8.2; addendum §40 point 5\)"):
            w.tool.release_hosts(plan, "P", [("p-1", h)])
        assert "p-1" not in plan["hosts"]
    h = w.tool.build_block(plan, "P", {"launches": P_DEAL})["launches"][0]["hosts"][0]
    assert w.tool.release_hosts(plan, "P", [("p-1", h)]) == ["p-1"]


# ===== 3. the edit: the sealed record, REQ-8's record, the file ======================================================

def test_block_p_needs_the_sealed_edit_record_and_refuses_a_changed_or_missing_edit_file(w):
    """Both ways, each with nothing planned: no sealed edit record for a0_plant (the dry run refuses too); the file
    changed on disk after its record; the file missing; REQ-8's record (re-pinned) naming another SHA-256 for
    edits/planted_k37.json; two sealed records naming different a0_plant files; then the good world plans, and a file
    changed between init and release refuses at release."""
    _b_sealed(w)
    rel, digest = _edit_file(w)
    _req8(w, digest)
    with pytest.raises(SystemExit, match="a0_plant at 1101: no edit file in MAN1, Gate B's MANIFEST or a recorded "
                                         "sealed record"):
        _init_p(w, dry_run=True)
    _record_edit(w, rel, digest)
    edit = w.repo / rel
    kept = edit.read_bytes()
    edit.write_bytes(kept + b" ")
    with pytest.raises(SystemExit, match="a0_plant at 1101: the edit file is missing or its SHA-256 is not the sealed one"):
        _init_p(w)
    edit.unlink()
    with pytest.raises(SystemExit, match="a0_plant at 1101: the edit file is missing or its SHA-256 is not the sealed one"):
        _init_p(w)
    edit.write_bytes(kept)
    _req8(w, "0" * 64)
    with pytest.raises(SystemExit, match=r"the edit recorded for a0_plant is not the file REQ-8's record names as "
                                         r"edits/planted_k37\.json"):
        _init_p(w)
    other_rel, other = _edit_file(w, name="k37-other.json", variant="another synthetic edit")
    _req8(w, other)
    _record_edit(w, other_rel, other)
    _req8(w, digest)
    with pytest.raises(SystemExit, match="a0_plant at 1101: two sources name different edit files; the lead decides"):
        _init_p(w)
    assert "P" not in w.plan()["blocks"]
    plan = w.plan()
    plan["records"]["sealed"] = plan["records"]["sealed"][:-1]
    w.mac.save_plan(plan)
    plan = w.tool.load()
    h = w.tool.build_block(plan, "P", {"launches": P_DEAL})["launches"][0]["hosts"][0]
    edit.write_bytes(kept + b"\n")
    with pytest.raises(SystemExit, match="a0_plant at 1101: the edit file is missing or its SHA-256 is not the sealed one"):
        w.tool.release_hosts(plan, "P", [("p-1", h)])
    edit.write_bytes(kept)
    assert _init_p(w)["hosts"] == ["p-1"]


def test_record_sealed_binds_a_plant_edit_to_req8s_record_by_key_and_prints_no_field(w, capsys):
    """record-sealed for an a0_plant edit (the sealed route of every arm, once ARM_DOSE names it): REQ-8's record at
    its pin must list edits/planted_k37.json in full_files with the recorded SHA-256; another SHA-256, no such entry,
    or a record off its pin refuses (fixed messages, no hash); the matching record is recorded once; an a0_plant edit
    with a draw refuses as every non-R edit; a non-plant arm's edit is not bound to REQ-8's record (unchanged route).
    REQ-8's unit and leaf fields and the edit's text fields are sentinels: none reaches stdout or stderr."""
    _b_sealed(w)
    rel, digest = _edit_file(w)
    r = w.rules

    def refused(match: str) -> None:
        before = list(w.plan()["records"]["sealed"])
        with pytest.raises(SystemExit, match=match) as caught:
            _record_edit(w, rel, digest)
        assert w.plan()["records"]["sealed"] == before and "0000" not in str(caught.value)
        assert digest[:8] not in str(caught.value)

    binding = (r"the edit recorded for a0_plant is not the file REQ-8's record names as edits/planted_k37\.json \(its "
               r"SHA-256 differs, or the record lists no such file; addendum §40 point 5\)")
    _req8(w, "0" * 64)
    refused(binding)
    _req8(w, None)
    refused(binding)
    _req8(w, digest, full_files="not a map")
    refused(binding)
    pin = _req8(w, digest)
    (w.repo / r.D2_REQ8_RECORD["path"]).write_text("{}")
    refused(r"REQ-8's record \(.*\) is missing or differs from its pin")
    _req8(w, digest)
    assert sha(w.repo / r.D2_REQ8_RECORD["path"]) == pin
    with pytest.raises(SystemExit, match=r"every sealed edit is \{arm, path, sha256\} \(R with its draw\)"):
        w.tool.record_simple("sealed", *w.record({"kind": "stage1 sealed edits", "edits": [
            {"arm": "a0_plant", "path": rel, "sha256": digest, "draw": 1}]}))
    record = _record_edit(w, rel, digest)
    assert [x["sha256"] for x in w.plan()["records"]["sealed"]][-1] == record
    _req8(w, "1" * 64)                                   # a non-plant arm: never checked against REQ-8's record
    other_rel, other = _edit_file(w, name="l1.json")
    _record_edit(w, other_rel, other, arm="L1")
    assert len(w.plan()["records"]["sealed"]) == 3
    printed = capsys.readouterr()
    _no_sentinel(printed.out + printed.err, "record-sealed's output")


# ===== 4. the runner: the plant arm's readable fingerprint record ====================================================

def _plant_edit_ref() -> tuple[str, dict]:
    """The synthetic plant edit's bytes and its reference as plan_tool binds it (path, SHA-256, source)."""
    text = json.dumps(_edit_doc(), indent=1, sort_keys=True) + "\n"
    digest = hashlib.sha256(text.encode()).hexdigest()
    return text, {"path": "tmp/synthetic-edit/edits/k37.json", "sha256": digest, "source": "sealed:synthetic"}


def plant_pod(kit, tmp_path, monkeypatch, extra_jobs=()):
    """A synthetic pod for block P's three a0_plant jobs (and ``extra_jobs``), the plant edit sealed by SHA-256 as the
    X pack carries it; the fake engine's calibrate then also writes what a real a0_plant unit holds in sealed-class
    files: the edit summary with its name in COMPLETE.json, the run's copy edit.json and a sentinel in
    eval/e1/summary.json; its verify prints the unit path and the verdict (the real verify's fields)."""
    text, ref = _plant_edit_ref()
    pod = Pod(kit, tmp_path, monkeypatch,
              lambda r: [job(r, "arm", "a0_plant", s, edit=ref, recipe="S", steps=38, branch="128")
                         for s in (1101, 1102, 1103)] + [j(r) for j in extra_jobs], branch="128")
    root = pod.root
    bundle = f"edits/{ref['sha256']}.edit.json"
    write(root / bundle, text)
    doc = json.loads((root / "sealed-files.json").read_text())
    doc["files"][bundle] = ref["sha256"]
    write(root / "sealed-files.json", doc)
    pod.plan["hosts"]["h-1"]["sealed_files_sha256"] = sha(root / "sealed-files.json")
    write(root / "plan.json", pod.plan)
    inner = pod.run

    def run(args, **kwargs):
        if list(args[:3]) == rn.ENGINE and "verify" in args:
            unit = args[args.index("--run") + 1]
            return rn.subprocess.CompletedProcess(args, 0, json.dumps({"run_dir": unit, "kind": "run-one",
                                                                      "complete": True, "problems": []}), "")
        done = inner(args, **kwargs)
        argv = list(args[5:]) if list(args[:2]) == ["python3", "process_receipt.py"] else []
        if "calibrate" in argv and "--edit" in argv:
            arm, seed = argv[argv.index("--arms") + 1], argv[argv.index("--seeds") + 1]
            unit = root / "round1" / f"{seed}-{arm}-e1-a1"
            complete = json.loads((unit / "COMPLETE.json").read_text())
            complete["edit"] = {"name": _edit_doc()["name"], "sha256": ref["sha256"]}
            write(unit / "COMPLETE.json", complete)
            write(unit / "edit.json", _edit_doc())
            write(unit / "eval" / "e1" / "summary.json", {"u": float(SENTINELS[0]), "edit": LEAF})
        return done

    monkeypatch.setattr(pod.runner.subprocess, "run", run)
    pod.edit = ref
    return pod


def test_the_runner_writes_the_plant_arms_readable_fingerprint_record_with_no_edit_field(kit, tmp_path, monkeypatch,
                                                                                        capsys):
    """Three a0_plant jobs and an A1 arm on one pod: each a0_plant job runs calibrate with --arms edit-<SHA-256> --edit
    edits/<SHA-256>.edit.json --seeds <seed> --checkpoints e1 (then the O-ext step), is complete with its unit
    round1/<seed>-edit-<SHA-256>-e1-a1, and lists job-I/arm-adapter-fingerprint.json among its outputs at its SHA-256:
    by hand {kind "stage1 arm adapter fingerprint", version 1, job, arm a0_plant, seed, steps 38, unit,
    complete_sha256, checkpoints {e1 (states/e1/state.json's, equal to COMPLETE.json's), q null}, identity}, in
    canonical JSON, with no edit key. The A1 arm writes none. The sealed-class unit files do hold the sentinel; no
    sentinel is in JOB-DONE.json, a record, a cost ledger or anything printed."""
    a1 = rn.edit_ref("A1")
    pod = plant_pod(kit, tmp_path, monkeypatch,
                    extra_jobs=[lambda r: job(r, "arm", "A1", 1102, edit=a1, recipe="S", branch="128")])
    r, ref = pod.rules, pod.edit
    pod.remaining([30 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete"] * 4
    argv = [a[5:] for a in pod.ran if a[:2] == ["python3", "process_receipt.py"]]
    assert argv[0] == [*rn.ENGINE, "calibrate", "--prepared", P, "--recipe", rn.S, "--arms", f"edit-{ref['sha256']}",
                       "--edit", f"edits/{ref['sha256']}.edit.json", "--seeds", "1101", "--checkpoints", "e1",
                       "--out-root", "round1"]
    assert pod.receipts()[:2] == ["job-0-calibrate", "job-0-oext"]
    records = pod.done()["jobs"]
    for i, seed in enumerate((1101, 1102, 1103)):
        rec = records[i]
        unit = f"round1/{seed}-edit-{ref['sha256']}-e1-a1"
        rel = f"job-{i}/{RECORD}"
        assert rec["unit"] == unit and rec["outputs"][rel] == sha(pod.root / rel) and "plant_fingerprint_record" not in rec
        data = (pod.root / rel).read_bytes()
        want = {"kind": "stage1 arm adapter fingerprint", "version": 1, "job": i, "arm": "a0_plant", "seed": seed,
                "steps": 38, "unit": unit, "complete_sha256": sha(pod.root / unit / "COMPLETE.json"),
                "checkpoints": {"e1": "5" * 64, "q": None}, "identity": {"manifest_sha256": rn.MS, "training_identity": rn.TI}}
        assert json.loads(data) == want and data == r.canonical_bytes(want) and "edit" not in json.loads(data)
        assert json.loads((pod.root / unit / "states" / "e1" / "state.json").read_text())["adapter_fingerprint"] == "5" * 64
        assert LEAF in (pod.root / unit / "COMPLETE.json").read_text()      # the sealed-class leak path is real
        assert LEAF in (pod.root / unit / "edit.json").read_text()
        _no_sentinel(data.decode(), rel)
        _no_sentinel((pod.root / f"job-{i}" / "cost-ledger.json").read_text(), f"job-{i}/cost-ledger.json")
    assert not any(k.endswith("adapter-fingerprint.json") for k in records[3]["outputs"])
    _no_sentinel((pod.root / "JOB-DONE.json").read_text(), "JOB-DONE.json")
    printed = capsys.readouterr()
    _no_sentinel(printed.out + printed.err, "the runner's output")
    assert (r.ARM_FINGERPRINT_RECORD, r.ARM_FINGERPRINT_KIND) == (RECORD, "stage1 arm adapter fingerprint")
    import fnmatch
    patterns = re.search(r"^READABLE_PATTERNS = \((.*)\)$", (kit.root / "seal.py").read_text(), re.MULTILINE).group(1)
    assert any(fnmatch.fnmatch(r.ARM_FINGERPRINT_RECORD, p.strip(' "')) for p in patterns.split(","))


def test_the_unit_stands_when_the_plant_record_cannot_be_written_and_a_record_is_never_written_over(kit, tmp_path,
                                                                                                  monkeypatch):
    """The other way (K6's rule): a state fingerprint that is not COMPLETE.json's e1 one gives no record, the reason in
    the job's record, the unit complete; a job-0/arm-adapter-fingerprint.json present before the job is left as it
    was (exclusive create), the reason recorded, the unit complete."""
    pod = plant_pod(kit, tmp_path, monkeypatch)
    pod.state_fp = "6" * 64
    pod.remaining([30 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete"] * 3
    for i, rec in enumerate(pod.done()["jobs"]):
        assert not (pod.root / f"job-{i}" / RECORD).exists()
        assert not any(k.endswith("adapter-fingerprint.json") for k in rec["outputs"])
        assert rec["plant_fingerprint_record"] == ("states/e1/state.json's adapter_fingerprint is not a SHA-256 equal "
                                                   "to COMPLETE.json's e1 one")
    (tmp_path / "second").mkdir()
    pod = plant_pod(kit, tmp_path / "second", monkeypatch)
    write(pod.root / "job-0" / RECORD, "an earlier record\n")
    pod.remaining([30 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete"] * 3
    recs = pod.done()["jobs"]
    assert recs[0]["plant_fingerprint_record"] == "the fingerprint record could not be written (FileExistsError)"
    assert (pod.root / "job-0" / RECORD).read_text() == "an earlier record\n" and f"job-0/{RECORD}" not in recs[0]["outputs"]
    assert recs[1]["outputs"][f"job-1/{RECORD}"] == sha(pod.root / "job-1" / RECORD)


def test_check_plan_passes_for_a_block_p_host_only_with_the_edit_packed_by_sha256(kit, monkeypatch):
    """$0 on the Mac: a P host's three a0_plant jobs need the O-ext runner and settings and the edit file
    edits/<SHA-256>.edit.json in the packed stage; without the edit check-plan names it (by SHA-256 only) for every
    job; with it the host passes."""
    _, ref = _plant_edit_ref()
    oext = ["scripts/stage1_s1/oext_unit.py", "scripts/stage1_s1/settings/oext_unit.json"]
    jobs = lambda r: [job(r, "arm", "a0_plant", s, edit=ref, recipe="S", steps=38) for s in (1101, 1102, 1103)]  # noqa: E731
    o = rn.orch(kit, monkeypatch, jobs, sealed_extra=oext)
    with pytest.raises(SystemExit) as caught:
        o.check_plan("h-1")
    text = str(caught.value)
    assert "h-1: the plan cannot run on its packed stage" in text
    assert text.count(f"1 file(s) not packed: ['edits/{ref['sha256']}.edit.json']") == 3
    _no_sentinel(text, "check-plan's refusal")
    o = rn.orch(kit, monkeypatch, jobs, sealed_extra=oext + [f"edits/{ref['sha256']}.edit.json"])
    assert o.check_plan("h-1") == {"host": "h-1", "jobs": 3, "ok": True}


# ===== 5. record-done, the seal, the re-run and the blinding scan ====================================================

def test_record_done_prints_block_ps_units_and_fingerprint_records_by_path_and_sha256(w):
    """record-done of the pilot's host: plant_units lists each complete a0_plant job's unit (path from the repository
    root, COMPLETE.json SHA-256: the pilot reader's inputs) and its fingerprint record {path, sha256}; a job without
    one prints null and plan.json keeps the runner's reason; a listed record that is not this run's refuses (its kind,
    job, arm, seed, unit, COMPLETE.json SHA-256, a non-int steps, an e1 that is no SHA-256, an edit field), nothing
    recorded."""
    _plant_ready(w)
    _init_p(w)
    out = _p_done(w, "p-1", no_record=(1,))
    plan = w.plan()
    jobs = plan["hosts"]["p-1"]["jobs"]
    tree = "runkit/stage1-olmo/retrieved/p-1/tree"
    assert out["statuses"] == ["complete"] * 3 and len(out["plant_units"]) == 3
    for i, seed in enumerate((1101, 1102, 1103)):
        unit = f"round1/{seed}-edit-{jobs[i]['edit']['sha256']}-e1-a1"
        rec = None if i == 1 else {"path": f"{tree}/job-{i}/{RECORD}",
                                   "sha256": sha(w.root / "retrieved" / "p-1" / "tree" / f"job-{i}" / RECORD)}
        assert out["plant_units"][i] == {"job": i, "arm": "a0_plant", "seed": seed, "unit": f"{tree}/{unit}",
                                         "complete_sha256": jobs[i]["complete_sha256"], "fingerprint_record": rec}
        assert jobs[i]["unit"] == unit and jobs[i]["status"] == "complete"
    assert jobs[1]["fingerprint_record_problem"] == ("states/e1/state.json's adapter_fingerprint is not a SHA-256 equal "
                                                     "to COMPLETE.json's e1 one")
    assert all("fingerprint_record_problem" not in jobs[i] for i in (0, 2))
    plan["hosts"]["p-1"]["done"] = False
    for j in jobs:
        j.update(status="planned", unit=None, complete_sha256=None, outputs=None)
    w.mac.save_plan(plan)
    message = (f"p-1: job-2/{RECORD} is not this run's fingerprint record ('stage1 arm adapter fingerprint', version 1, "
               "its job, arm, seed, steps, unit and COMPLETE.json SHA-256, a 64-hex e1, no edit field)")
    for change in (lambda d: d.update(kind="stage1 a0 adapter fingerprint"), lambda d: d.update(job=5),
                   lambda d: d.update(arm="a0"), lambda d: d.update(seed=1101), lambda d: d.update(unit="units/x"),
                   lambda d: d.update(complete_sha256="0" * 64), lambda d: d.update(steps="38"),
                   lambda d: d["checkpoints"].update(e1="not a fingerprint"), lambda d: d.update(edit={"name": LEAF}),
                   lambda d: d["checkpoints"].pop("q")):
        with pytest.raises(SystemExit) as refused:
            _p_done(w, "p-1", record_change=lambda d, i, c=change: c(d) if i == 2 else None)
        assert str(refused.value) == message
        assert w.plan()["hosts"]["p-1"].get("done") is not True
    assert _p_done(w, "p-1")["plant_units"][2]["fingerprint_record"]["path"] == f"{tree}/job-2/{RECORD}"


def test_block_p_completes_and_seals_with_no_judge_launch_and_no_judge_file(w):
    """Addendum §40 point 7: once p-1 is recorded done the block is complete (no judge launch to release, no judge
    file to index: judges_needed is empty, planned_judged_units 3 is the count a judge launch would have to cover);
    seal.py block P seals it: 3 units x 4 files + 3 x (ledger, O-ext, record) + JOB-DONE.json = 22 files, 7 readable
    (JOB-DONE.json, the ledgers, the records), no judge record, no judge not-run decision, no judges/P folder; the
    seal's status lines print kinds, statuses, counts and hashes only."""
    _plant_ready(w)
    _init_p(w)
    plan = w.plan()
    assert w.tool.block_complete(plan, "P") is False
    assert w.tool.judges_needed(plan, "P") == [] and w.tool.judges_done(plan, "P") == set()
    assert w.tool.planned_judged_units("P", plan["hosts"]["p-1"]["jobs"]) == 3
    _p_done(w, "p-1")
    plan = w.plan()
    assert w.tool.block_complete(plan, "P") is True and w.tool.block_open_jobs(plan, "P") == []
    out = w.seal.seal_block("P")
    assert (out["block"], out["files"], out["sealed"], out["readable"]) == ("P", 22, 15, 7)
    record = json.loads((w.root / "seals" / "block-P.json").read_text())
    assert (record["hosts"], record["judge_record"], record["judge_not_run"], record["not_run"], record["moved"],
            record["skipped"]) == (["p-1"], None, [], [], [], [])
    readable = sorted(f["path"] for f in record["files"] if f["class"] == "readable")
    assert readable == ["JOB-DONE.json"] + sorted(f"job-{i}/{n}" for i in range(3) for n in ("arm-adapter-fingerprint.json",
                                                                                           "cost-ledger.json"))
    assert not (w.root / "judges" / "P").exists() and w.plan()["seals"]["P"]["sha256"] == sha(w.root / "seals" / "block-P.json")
    lines = w.seal.status()
    assert any(line.startswith("p-1") and "block P" in line and "arm:complete,arm:complete,arm:complete" in line
               for line in lines)
    assert any(line == "seal P: 22 files (15 sealed), sha256 " + w.plan()["seals"]["P"]["sha256"] for line in lines)
    _no_sentinel("\n".join(lines), "seal status")
    with pytest.raises(SystemExit, match="block P is already sealed"):
        w.seal.seal_block("P")


def test_a_crashed_a0_plant_run_is_re_run_once_from_block_ps_contingency(w):
    """The kit's re-run rule on block P: record-done with the third run crashed; defer moves it to p-2 (the same edit,
    deferred_from p-1), paid from P's contingency on a new pod ((4,144 + 2,520) / 3,600 x $1.79 = $3.31 of $4.16, not
    twice); p-2's cap alone is 42 min + 9,418.29 s -> 3.5 h; record-done of p-2 completes the block; the seal lists both
    hosts."""
    _plant_ready(w)
    _init_p(w)
    out = _p_done(w, "p-1", statuses={2: "crashed"})
    assert out["statuses"] == ["complete", "complete", "crashed"] and len(out["plant_units"]) == 2
    assert w.tool.block_complete(w.plan(), "P") is False
    moved = w.tool.defer("p-1")
    assert (moved["to"], moved["jobs"], moved["cap_hours"]) == ("p-2", 1, 3.5)
    plan = w.plan()
    c = plan["contingency"]["P"]
    cost = (4144 + 2520) / 3600 * 1.79
    assert [s["cost_usd"] for s in c["spent"]] == [pytest.approx(cost)] and c["remaining_usd"] == pytest.approx(4.16 - cost)
    j = plan["hosts"]["p-2"]["jobs"][0]
    assert (j["arm"], j["seed"], j["edit"], j["deferred_from"], j["steps"]) == (
        "a0_plant", 1103, plan["hosts"]["p-1"]["jobs"][2]["edit"], "p-1", 38)
    assert plan["hosts"]["p-2"]["block"] == "P" and plan["hosts"]["p-2"]["counted"] == 1
    out = _p_done(w, "p-2")
    assert out["statuses"] == ["complete"] and out["plant_units"][0]["seed"] == 1103
    assert w.tool.block_complete(w.plan(), "P") is True
    assert w.seal.seal_block("P")["files"] == 15 + 8   # p-1: 2 units x 4 + 2 x 3 job files + JOB-DONE; p-2: 4 + 3 + 1
    assert json.loads((w.root / "seals" / "block-P.json").read_text())["hosts"] == ["p-1", "p-2"]


def test_blinding_the_edits_name_never_reaches_a_readable_kit_file_or_the_output(w, capsys):
    """The sealed edit record's file holds a sentinel in its name field and every other text field; REQ-8's record's
    unit and leaf fields are sentinels; the pulled units' COMPLETE.json, edit.json, summary and state files hold them
    (sealed class). Through init-block P (dry run and real), deal, record-done, the finisher's light check (its
    finished.json, verified.jsonl and log records), seal P and seal status, the sentinel is in no printed line and in
    no readable kit file: plan.json, operator-actions.jsonl, hosts/, seals/, retrieved/p-1/verified.jsonl, JOB-DONE.json,
    the cost ledgers, the fingerprint records; the seal classes the holding files sealed and the records readable."""
    _plant_ready(w)
    outputs = [json.dumps(_init_p(w, dry_run=True)), json.dumps(_init_p(w)), json.dumps(w.tool.deal_command("P", None)),
               json.dumps(_p_done(w, "p-1"))]
    spec = importlib.util.spec_from_file_location("s1_finisher_round35", w.root / "finisher.py")
    fin = importlib.util.module_from_spec(spec)                        # the World's rules and plan_tool (sys.path)
    spec.loader.exec_module(fin)
    tree = w.root / "retrieved" / "p-1" / "tree"
    logged = []
    w.mp.setattr(fin, "tool", lambda *a: rn.subprocess.CompletedProcess(a, 0, "stopped", ""))
    w.mp.setattr(fin, "unpack", lambda h: tree)
    w.mp.setattr(fin, "log", lambda **f: logged.append(json.dumps(f)))
    (w.root / "hosts" / "p-1").mkdir(parents=True, exist_ok=True)
    fin.finish("p-1", {"exit_code": 0})
    assert json.loads((w.root / "hosts" / "p-1" / "finished.json").read_text())["status"] == "verified-and-stopped"
    outputs += [json.dumps(w.seal.seal_block("P")), "\n".join(w.seal.status()), *logged]
    printed = capsys.readouterr()
    _no_sentinel(printed.out + printed.err + "\n".join(outputs), "a printed line or a command's output")
    record = json.loads((w.root / "seals" / "block-P.json").read_text())
    by_class = {c: sorted(f["path"] for f in record["files"] if f["class"] == c) for c in ("sealed", "readable")}
    holders, scanned = [], 0
    for p in sorted(x for x in w.root.rglob("*") if x.is_file() and "__pycache__" not in x.parts):
        rel = p.relative_to(w.root).as_posix()
        if rel.startswith("retrieved/") and not rel.startswith("retrieved/p-1/"):
            continue                                   # blocks A and B's pulled trees: the World's own synthetic outcomes
        text = p.read_text(errors="replace")
        if rel.startswith("retrieved/p-1/tree/") and rel[len("retrieved/p-1/tree/"):] in by_class["sealed"]:
            if any(s in text for s in EDIT_SENTINELS):
                holders.append(rel[len("retrieved/p-1/tree/"):])
            continue
        scanned += 1
        _no_sentinel(text, rel)
    assert scanned >= 7 + 4 and {"plan.json", "operator-actions.jsonl", "seals/block-P.json", "hosts/p-1/finished.json",
                                 "retrieved/p-1/verified.jsonl", "retrieved/p-1/tree/JOB-DONE.json"} <= {
        x.relative_to(w.root).as_posix() for x in w.root.rglob("*") if x.is_file()}
    assert sorted(holders) == sorted(f"round1/{s}-edit-{sha(w.repo / 'tmp' / 'synthetic-edit' / 'edits' / 'k37.json')}-e1-a1/{n}"
                                     for s in (1101, 1102, 1103)
                                     for n in ("COMPLETE.json", "edit.json", "eval/e1/summary.json", "states/e1/state.json"))
    assert by_class["readable"] == ["JOB-DONE.json"] + sorted(f"job-{i}/{n}" for i in range(3)
                                                              for n in ("arm-adapter-fingerprint.json", "cost-ledger.json"))
    assert LEAF in (w.repo / "tmp" / "synthetic-edit" / "edits" / "k37.json").read_text()
    assert EDIT_SENTINELS[3] in (w.repo / w.rules.D2_REQ8_RECORD["path"]).read_text()


def test_the_round_35_files_compile_and_hold_no_secret(tmp_path):
    """The round's changed kit files compile and hold no secret pattern (the kit's own scanner)."""
    import py_compile
    names = ("stage1_rules.py", "plan_tool.py", "setup/job_runner_stage1.py", "tests/test_round35.py")
    for rel in names:
        py_compile.compile(str(KIT / rel), cfile=str(tmp_path / "x.pyc"), doraise=True)
    spec = importlib.util.spec_from_file_location("s1_scan_round35", KIT / "secret_scan.py")
    scan = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scan)
    assert scan.scan_paths([KIT / rel for rel in (*names, "README.md")]) == []
    assert "s1_scan_round35" not in sys.modules
