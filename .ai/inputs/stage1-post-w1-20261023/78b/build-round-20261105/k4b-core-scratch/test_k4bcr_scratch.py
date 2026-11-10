"""k4b-core-reverify scratch tests (the re-verifier's own; never merged). They reuse the scorer-block test helpers and
fill every pin TEST-LOCALLY. Each test either prints a plan/need table for both families (written by hand checks) or
pins one gap a surviving hand mutant (K4bcr-R*) showed. No network, no real process, no sealed or outcome file."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

import test_scorer_block_78b as sb
from test_scorer_block_78b import ANCHOR, UNTUNED, anchor_done, untuned_done, stand_in_lists, sha, hx, write, \
    unit_run, load_by_path, oext_inputs, ScPod   # noqa: F401  (fixtures below)
from test_scorer_block_78b import sw, so   # noqa: F401  (pytest fixtures)

OUT = Path(os.environ.get("K4BCR_OUT", "/dev/null"))


def cents(x: float) -> float:
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def dump(name: str, obj) -> None:
    if str(OUT) != "/dev/null":
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")


def pod_row(p: dict) -> dict:
    return {k: p.get(k) for k in ("host", "kind", "seed", "engine", "cap_hours", "guard_usd", "spend_upper_usd",
                                  "need_usd_alone", "launch")} | {"keeps_states": p["idle_storage"]["keeps_states"],
                                                                 "inputs": sorted(p.get("inputs") or {})}


# ----- S1: part 1 of both families with every o_only_with_regenerate seed; each seed's own side pin (R8) -----------
def test_s1_part1_every_seed_its_own_side_pin_and_the_need_by_hand(sw, capsys):
    w = sw
    r78 = w.r78
    seeds = r78.sc_seeds(w.family, "o_only_with_regenerate")
    assert seeds == ([1101, 1102, 1103] if w.family == "olmo2-7b" else [1101, 1102])
    w.fill(oext=True, c0=True)
    sides = {s: w.side_unit(s, kind=f"COMPLETE (synthetic side unit {s})") for s in seeds}
    assert len({sha(p) for p in sides.values()}) == len(seeds)
    launch = [ANCHOR, UNTUNED, {"kind": "o_only"}] + [{"kind": "o_only_with_regenerate", "seed": s} for s in seeds] + \
        [{"kind": "c0"}]
    dry = w.init(launch, amount=None, dry_run=True)
    lines = capsys.readouterr().out.splitlines()
    pods = dry["pods"]
    assert [p["kind"] for p in pods] == [j["kind"] for j in launch]
    for p in pods:
        assert p["engine"] == "X"                                     # PP16: all of part 1 is X-only
        assert p["guard_usd"] == cents(6 + 1.85 * p["cap_hours"])     # guard by hand
        assert p["need_usd_alone"] == cents(1.25 * p["guard_usd"])    # need alone by hand
    regen = [p for p in pods if p["kind"] == "o_only_with_regenerate"]
    for p, s in zip(regen, seeds):                                    # R8: each seed's pin is its own side unit's
        assert p["inputs"][f"side_complete:a0:{s}"] == sha(sides[s]) == r78.KIT[w.family]["a0_units"][s]["complete_sha256"]
        assert p["cap_hours"] == 4.5 and p["idle_storage"]["keeps_states"] is True
    caps = {p["kind"]: p["cap_hours"] for p in pods}
    assert caps == {"anchor": 2.25, "untuned_answers": 6.0, "o_only": 3.75, "o_only_with_regenerate": 4.5,
                    "c0": 4.25 if w.family == "olmo2-7b" else 4.5}
    base = cents(6 + 1.85 * sum(p["cap_hours"] for p in pods))         # one launch: the reserve + 1.85 x the caps
    assert dry["base_need_usd"] == base and dry["need_usd"] == cents(1.25 * base)
    kept = [p for p in pods if p["idle_storage"]["keeps_states"]]
    assert [p["kind"] for p in kept] == ["o_only_with_regenerate"] * len(seeds) + ["c0"]
    dump(f"s1-{w.family}", {"pods": [pod_row(p) for p in pods], "base_need_usd": dry["base_need_usd"],
                            "need_usd": dry["need_usd"], "lines": lines})


# ----- S2: parts 2 and 3 in A2's order, both families; a1_pass's anchor pin bound too (R13) ------------------------
def test_s2_parts_2_and_3_in_a2_order_and_a1_pass_reads_the_recorded_anchor_file(sw, capsys):
    w = sw
    host = f"{w.family}-sc"
    w.pack(*stand_in_lists(w))
    w.init([ANCHOR, UNTUNED])
    other = write(w.repo / "tmp" / "anchors" / "another-anchors.json", {"kind": "another anchor file"})
    anchor_done(w, f"{host}-1")
    untuned_done(w, f"{host}-2")
    w.fill(anchor=True, recipe_s=True, s3_orig=True, engine_y=True)
    capsys.readouterr()
    part2 = [{"kind": "l1_scan"}, {"kind": "classifier"}, {"kind": "rep_pass"}, {"kind": "retrain"}]
    dry2 = w.init(part2, amount=None, dry_run=True)
    lines2 = capsys.readouterr().out.splitlines()
    assert [(p["kind"], p["engine"], p["cap_hours"]) for p in dry2["pods"]] == [
        ("l1_scan", "X", 4.75), ("classifier", "X", 3.25), ("rep_pass", "X", 4.75), ("retrain", "Y", 4.5)]
    base2 = cents(6 + 1.85 * (4.75 + 3.25 + 4.75 + 4.5))
    assert dry2["base_need_usd"] == base2 and dry2["need_usd"] == cents(1.25 * base2)
    # the retrain recorded complete on Y, its unit the pin; then part 3
    w.pack(*stand_in_lists(w), ("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())))
    y = w.root / "setup" / "packed-stage1-Y"
    write(y / "sealed-files.json", {"files": {w.s78["path"]: sha(w.repo / w.s78["path"])}, "inputs": {}})
    write(y / "setup-receipt.json", {"engine_sha256": sb.Y, "family": w.family,
                                     "sealed_files_sha256": sha(y / "sealed-files.json")})
    retrain_host = w.init([{"kind": "retrain"}])["released"][0]
    unit = w.retrain_unit()
    tree = w.root / "retrieved" / retrain_host / "tree"
    shutil.copytree(unit.parent, tree / "rescore" / unit.parent.name)
    w.done(retrain_host, unit=f"rescore/{unit.parent.name}", complete_sha256=sha(unit),
           verified={"exit": 0, "tail": "names"},
           sc={"kind": "retrain", "fingerprints": {"complete_sha256": sha(unit), "checkpoints": {"e1": hx("e1"), "q": hx("q")},
                                                   "identity": {"manifest_sha256": None, "training_identity": None}}})
    w.fill(retrain=sha(unit))
    capsys.readouterr()
    dry3 = w.init([{"kind": "a1_pass"}], amount=None, dry_run=True)
    lines3 = capsys.readouterr().out.splitlines()
    assert [(p["kind"], p["engine"], p["cap_hours"]) for p in dry3["pods"]] == [("a1_pass", "Y", 16.5)]
    assert dry3["need_usd"] == cents(1.25 * cents(6 + 1.85 * 16.5)) == 45.66
    dump(f"s2-{w.family}", {"part2": [pod_row(p) for p in dry2["pods"]], "part2_need": dry2["need_usd"],
                            "part3": [pod_row(p) for p in dry3["pods"]], "part3_need": dry3["need_usd"],
                            "lines2": lines2, "lines3": lines3})
    # R13: with the anchor pin moved to another file after part 2, a1_pass refuses (the pin is not the recorded file)
    doc = w.pins78()
    doc["families"][w.family]["anchor_bank_sha256"] = sha(other)
    write(w.repo / w.rules.PINS_78B, doc)
    w.mp.setitem(w.rules.SCORER_PINS, w.rules.PINS_78B, sha(w.repo / w.rules.PINS_78B))
    for script in ("representation_pass", "score_classifier", "score_l1_larf"):
        rel = f"{w.rules.SCORER_SETTINGS}/{script}__{w.family}.json"
        s = json.loads((w.repo / rel).read_text())
        if "anchor_bank_sha256" in s.get("pins", {}):
            s["pins"]["anchor_bank_sha256"] = sha(other)
            write(w.repo / rel, s)
            w.mp.setitem(w.rules.SCORER_PINS, rel, sha(w.repo / rel))
    index = json.loads((w.repo / w.rules.PINS_INDEX).read_text())
    if "pins_78b_sha256" in index:
        index["pins_78b_sha256"] = sha(w.repo / w.rules.PINS_78B)
        for k in list(index.get("files", {}) or {}):
            if (w.repo / k).is_file():
                index["files"][k] = sha(w.repo / k)
        write(w.repo / w.rules.PINS_INDEX, index)
        w.mp.setitem(w.rules.SCORER_PINS, w.rules.PINS_INDEX, sha(w.repo / w.rules.PINS_INDEX))
    with pytest.raises(SystemExit, match="the ANCHOR_BANK pin is not the anchor_file_sha256"):
        w.init([{"kind": "a1_pass"}], amount=None, dry_run=True)


# ----- S3: the acceptance check's edges (R6, R7, R21) ---------------------------------------------------------------
BASE = {"checkpoints": {"q": {"adapter_fingerprint": hx("q"), "optimizer_fingerprint": hx("q-opt")},
                        "e1": {"adapter_fingerprint": hx("e1"), "optimizer_fingerprint": hx("e1-opt")}},
        "identity": {"training_identity": hx("ti"), "manifest_sha256": hx("man")}}


def copy(doc):
    return json.loads(json.dumps(doc))


def test_s3a_a_side_unit_without_an_e1_adapter_fingerprint_is_a_crash(so, monkeypatch, tmp_path):   # R21
    side = copy(BASE)
    del side["checkpoints"]["e1"]["adapter_fingerprint"]
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, "o_only_with_regenerate", 0, side, {"complete": True, **copy(BASE)})
    assert rec["status"] == "crashed" and "no e1 adapter fingerprint" in rec["why"]


def test_s3b_a_fingerprint_the_side_lists_and_the_regenerated_unit_omits_is_ls04(so, monkeypatch, tmp_path):   # R7
    regen = {"complete": True, **copy(BASE)}
    del regen["checkpoints"]["q"]["optimizer_fingerprint"]
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, "o_only_with_regenerate", 0, copy(BASE), regen)
    assert rec["status"] == "complete" and rec["acceptance"] is False and rec["reason"] == "LS-04"


def test_s3c_an_identity_field_missing_on_both_sides_is_not_equal(so, monkeypatch, tmp_path):   # R6
    side, regen = copy(BASE), {"complete": True, **copy(BASE)}
    del side["identity"]["training_identity"], regen["identity"]["training_identity"]
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, "o_only_with_regenerate", 0, side, regen)
    assert rec["status"] == "complete" and rec["acceptance"] is False and rec["reason"] == "LS-04"


# ----- S4: record-done refuses acceptance false with another reason (R9) -------------------------------------------
def test_s4_record_done_refuses_acceptance_false_with_a_reason_other_than_ls04(so, monkeypatch):
    w = so
    w.fill(oext=True)
    side = w.side_unit(1101)
    w.pack(*oext_inputs(w), ("side_complete:a0:1101", side, sha(side)))
    host = w.init([sb.REGEN])["released"][0]
    differs = {"kind": "COMPLETE (synthetic)", "complete": True,
               "checkpoints": {"e1": {"adapter_fingerprint": hx("e1"), "optimizer_fingerprint": hx("e1-opt")},
                               "q": {"adapter_fingerprint": hx("another q"), "optimizer_fingerprint": hx("q-opt")}},
               "identity": {"training_identity": hx("ti"), "manifest_sha256": hx("man")}}
    pod = ScPod(w, monkeypatch, host, unit_complete=differs)
    assert pod.main() == 0
    rec = pod.done()["jobs"][0]
    tree = w.root / "retrieved" / host / "tree"
    shutil.copytree(pod.root, tree)
    with pytest.raises(SystemExit, match="names no acceptance verdict"):
        w.done(host, unit=rec["unit"], complete_sha256=rec["complete_sha256"], verified={"exit": 0, "tail": ""},
               sc={"kind": "o_only_with_regenerate", "fingerprints": rec["sc"]["fingerprints"], "acceptance": False,
                   "acceptance_record_sha256": rec["sc"]["acceptance_record_sha256"]}, reason="LS-05")


# ----- S5: a unit kind's outputs are its job folder's only, never the unit's files (R1) ------------------------------
@pytest.mark.parametrize("kind", ["retrain", "a1_pass", "o_only_with_regenerate"])
def test_s5_a_unit_kinds_outputs_lie_under_its_job_folder_only(so, monkeypatch, tmp_path, kind):
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, kind)
    assert rec["status"] == "complete", rec.get("why")
    assert all(k.startswith("job-0/") for k in rec["outputs"]), sorted(rec["outputs"])


# ----- S6: the backup checks a1_pass's recorded outputs (its ledger) too (R17) -------------------------------------
def test_s6_the_backup_checks_a1_pass_and_the_retrains_recorded_outputs(so):
    w = so
    backup = load_by_path("backup_sc_k4bcr", w.root / "backup_records_stage1.py")
    tree = w.root / "retrieved" / "h" / "tree"
    attr = write(tree / "rescore" / "1101-attributes-a1" / "attributes.json", {"kind": "attributes (synthetic)"})
    unit = write(tree / "rescore" / "1101-attributes-a1" / "COMPLETE.json", {"files": {"attributes.json": sha(attr)}})
    ledger = write(tree / "job-0" / "cost-ledger.json", {"kind": "stage1 cost ledger"})
    plan = {"hosts": {"h": {"block": "sc", "jobs": [
        {"kind": "a1_pass", "status": "complete", "unit": "rescore/1101-attributes-a1", "complete_sha256": sha(unit),
         "outputs": {"job-0/cost-ledger.json": sha(ledger)}}]}}}
    staged = {f"units/h/{p.relative_to(tree)}": sha(p) for p in tree.rglob("*") if p.is_file()}
    missing = []
    backup.sealed_units(plan, ["h"], staged, missing)
    assert missing == []
    missing = []
    backup.sealed_units(plan, ["h"], {k: v for k, v in staged.items() if "cost-ledger" not in k}, missing)
    assert missing == ["h: job 0: 1 recorded output(s) not staged or changed"]


# ----- S7 (EXPECTED TO FAIL on the round-4b code: a defect demonstration, not a gap test) ----------------------------
# At 1B the runner derived c0's --expect-adapter-fingerprint from the packed, sealed source COMPLETE.json
# (@fingerprint:source_complete:R:1101, R: runkit/stage1-olmo/setup/job_runner_stage1.py:517, :770-776). At 7-8B
# C0_SOURCE holds two typed fields (complete_sha256, e1_fingerprint) and nothing compares them.
def test_s7_c0s_expected_fingerprint_must_be_the_packed_source_units_e1_fingerprint(so):
    w = so
    w.fill(oext=True)
    src = write(w.repo / "tmp" / "n" / "R-1101-k4bcr" / "COMPLETE.json",
                {"kind": "COMPLETE (synthetic)", "checkpoints": {"e1": {"adapter_fingerprint": hx("the real e1")}}})
    w.mp.setitem(w.r78.C0_SOURCE, w.family, {"complete_sha256": sha(src), "e1_fingerprint": hx("a typo in the step")})
    with pytest.raises(SystemExit):
        dry = w.init([{"kind": "c0"}], amount=None, dry_run=True)
        print("planned; expect_fingerprint passed to B17:", "typo" if True else "")
