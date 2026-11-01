"""Round-3 independent check of D1 fix round 2 (the verifier's own code; synthetic data only).

    cd <ws-d1> && PYTHONDONTWRITEBYTECODE=1 <venv python> -B <this file> <basetemp>

(a) REV4:813 read literally for every ref_eval point, computed here from the raw ledger files and plan.json (my own
    walk, not cost_table's): the a0_arm run at the same seed, its slot_s - 219.7 + the ref_eval ledger's transform
    stage, over 2,934 s and over the measured c0; the per-reference mean over seeds; K5's null beside; edge cases
    (a planted transform, an a0 slot below the training price, a seed with no a0 run, no c0, two jobs at one seed).
(b) the LN-19 PHTest lines on three synthetic worlds (Branch 128 with and without the transfer pass; Branch full).
(c) the split denominator and the anchor job in the output.
Prints PASS/FAIL lines and a summary; exit 1 on any FAIL.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

WS = Path.cwd()
sys.path.insert(0, str(WS))
sys.path.insert(0, str(WS / "scripts/stage1_s1/reading_extra/tests"))
sys.path.insert(0, str(WS / "scripts/stage1_s1/reading_input/tests"))

import extra_kit as ek  # noqa: E402
import synth_kit as sk  # noqa: E402

from scripts.stage1_s1.reading.settings import Refusal  # noqa: E402
from scripts.stage1_s1.reading_extra import cap_reports as cap  # noqa: E402
from scripts.stage1_s1.reading_extra import cost_table as ct  # noqa: E402
from scripts.stage1_s1.reading_input.__main__ import main as builder  # noqa: E402

FRE = 2934.0
FULL_TRAINING = 219.7          # selector_spec.json cost_conventions C-full training_s (read by key, 55d5f8b)
LEAN_TRAINING = 220.0          # C-lean variants a and b
FAILS: list = []


def check(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAILS.append(what)


# ----- my own walk of a synthetic kit: plan.json + the ledger files ---------------------------------------------------
def ledgers(kit: Path, plan: dict) -> list:
    out = []
    for host, h in sorted(plan["hosts"].items()):
        for i, j in enumerate(h["jobs"]):
            p = kit / "retrieved" / host / "tree" / f"job-{i}" / "cost-ledger.json"
            if j.get("status") == "complete" and p.is_file() and f"job-{i}/cost-ledger.json" in (j.get("outputs") or {}):
                out.append({"host": host, "index": i, "job": j, "ledger": json.loads(p.read_text())})
    return out


def my_813(kit: Path, plan: dict) -> dict:
    """{seed: {...}} for every complete ref_eval job: the REV4:813 value from the matched a0_arm run (same seed)."""
    led = ledgers(kit, plan)
    c0 = [x for x in led if x["job"]["kind"] == "c0"]
    c0_s = c0[0]["ledger"]["slot_s"] if len(c0) == 1 else None
    a0 = {}
    for x in led:
        if x["job"]["kind"] == "a0_arm" and x["job"]["arm"] == "a0":
            assert x["job"]["seed"] not in a0
            a0[x["job"]["seed"]] = x
    rows = {}
    for x in led:
        if x["job"]["kind"] != "ref_eval":
            continue
        seed = x["job"]["seed"]
        transform = x["ledger"]["stages_s"]["transform"]
        base = a0.get(seed)
        if base is None:
            value = None
        else:
            value = base["ledger"]["slot_s"] - FULL_TRAINING + transform
            if value < 0:
                value = None
        rows.setdefault(seed, []).append({
            "host": x["host"], "index": x["index"], "points": x["job"]["points"], "transform": transform,
            "a0": None if base is None else (base["host"], base["index"], base["ledger"]["slot_s"]),
            "seconds": value, "fre": None if value is None else value / FRE,
            "over_c0": None if value is None or c0_s is None else value / c0_s,
            "lean_c0": None if c0_s is None or c0_s - LEAN_TRAINING <= 0 else (c0_s - LEAN_TRAINING) / c0_s})
    return {"c0": c0_s, "rows": rows}


def rewrite_ledger(kit: Path, plan: dict, host: str, i: int, fn) -> None:
    path = kit / "retrieved" / host / "tree" / f"job-{i}" / "cost-ledger.json"
    doc = json.loads(path.read_text())
    fn(doc)
    path.write_bytes(sk.jbytes(doc))
    plan["hosts"][host]["jobs"][i]["outputs"][f"job-{i}/cost-ledger.json"] = sk.sha(path.read_bytes())
    ek.seal(kit, plan, plan["hosts"][host]["block"])
    (kit / "plan.json").write_bytes(sk.jbytes(plan))


def job_at(plan, kind, seed=None, arm=None):
    for host, h in sorted(plan["hosts"].items()):
        for i, j in enumerate(h["jobs"]):
            if j["kind"] == kind and (seed is None or j.get("seed") == seed) and (arm is None or j.get("arm") == arm):
                return host, i
    raise KeyError((kind, seed, arm))


def case_a_main(base: Path):
    """Three ref_eval seeds: 1105 plain, 1106 with its a0 slot below the training price, 1107 with a planted
    transform of 12.25 s."""
    kit, slots, plan = ek.cost_kit(base / "main", "plan_a", extra_ref_eval_seeds=(1106, 1107))
    h7, i7 = job_at(plan, "ref_eval", 1107)
    rewrite_ledger(kit, plan, h7, i7, lambda d: d["stages_s"].update(transform=12.25))
    h6, i6 = job_at(plan, "a0_arm", 1106, "a0")
    rewrite_ledger(kit, plan, h6, i6, lambda d: d.update(slot_s=100.0))
    mine = my_813(kit, plan)
    out = ct.table(kit, "plan_a")
    c0 = mine["c0"]
    check(out["units"]["c0"]["measured_s"] == c0 and out["units"]["full_training_s"] == FULL_TRAINING,
          f"(a) units: c0 {c0} s, full_training_s 219.7")
    evs = {v["seed"]: v for k, v in out["b10_references"].items() if k.startswith("ref_eval")}
    check(set(evs) == {1105, 1106, 1107}, "(a) three ref_eval jobs printed")
    for seed in (1105, 1106, 1107):
        m = mine["rows"][seed][0]
        rec = evs[seed]
        for p in ("scale:0.9", "scale:0.75", "scale:0.5", "prefix"):
            pt = rec["per_point"][p]
            basis = pt["c_full_basis"]
            if m["seconds"] is None:
                check(pt["seconds"] is None and pt["c_full_fre"] is None and pt["approximately_zero"] is None
                      and "below the frozen C-full training price" in basis.get("why", "")
                      and "seconds_over_c0" not in basis and basis["a0_run"] is not None,
                      f"(a) seed {seed} {p}: null with the reason (a0 slot 100 s < 219.7 s), the a0 run still named")
            else:
                check(math.isclose(pt["seconds"], m["seconds"], abs_tol=1e-9)
                      and math.isclose(pt["c_full_fre"], m["fre"], rel_tol=1e-12)
                      and math.isclose(basis["seconds_over_c0"], m["over_c0"], rel_tol=1e-12),
                      f"(a) seed {seed} {p}: {m['seconds']:.3f} s = {m['fre']:.6f} FRE = {m['over_c0']:.6f} c0 "
                      f"(a0 slot {m['a0'][2]:.3f} - 219.7 + transform {m['transform']})")
                check(basis["a0_run"] == {"seed": seed, "host": m["a0"][0], "index": m["a0"][1], "slot_s": m["a0"][2]},
                      f"(a) seed {seed} {p}: the matched a0 run named (same seed)")
                check(pt["approximately_zero"] is (m["fre"] < 0.01), f"(a) seed {seed} {p}: approximately_zero flag")
            check(basis["full_training_s"] == FULL_TRAINING and basis["transform_s"] == m["transform"],
                  f"(a) seed {seed} {p}: training 219.7, transform {m['transform']}")
            check(pt["alternative_k5"]["seconds"] is None and pt["alternative_k5"]["c_full_fre"] is None
                  and pt["alternative_k5"]["why"].startswith("not stated"),
                  f"(a) seed {seed} {p}: K5's 'null: not stated' beside the value")
            check(pt["c_lean_c0"] is not None and math.isclose(pt["c_lean_c0"], m["lean_c0"], rel_tol=1e-12),
                  f"(a) seed {seed} {p}: C-lean (K6) unchanged = {m['lean_c0']:.6f} c0")
        # the whole job's C-full is still its own slot
        check(rec["seconds"] == slots[job_at(plan, "ref_eval", seed)] and rec["c_full_fre"] == rec["seconds"] / FRE,
              f"(a) seed {seed}: the whole ref_eval job's C-full is still its slot")
    # per-reference mean over seeds: 1105 and 1107 have a value, 1106 is listed
    have = {s: mine["rows"][s][0]["fre"] for s in (1105, 1107)}
    for p, name in (("scale:0.9", "adapter scaling 0.9"), ("scale:0.75", "adapter scaling 0.75"),
                    ("scale:0.5", "adapter scaling 0.5"), ("prefix", "SP (the system prompt prefix)")):
        r = out["b10_per_reference"]["ref_eval"][p]
        check(r["menu_name"] == name and r["seeds"] == ["1105", "1106", "1107"] and r["jobs"] == 3,
              f"(a) per reference {p}: menu name '{name}', 3 seeds")
        check(math.isclose(r["c_full_fre_mean"], statistics.fmean(have.values()), rel_tol=1e-12)
              and r["c_full_fre_min"] == min(have.values()) and r["c_full_fre_max"] == max(have.values())
              and r["seeds_without_c_full_fre"] == ["1106"],
              f"(a) per reference {p}: mean over 1105 and 1107 = {statistics.fmean(have.values()):.6f} FRE; 1106 listed")
        lean = mine["rows"][1105][0]["lean_c0"]
        check(math.isclose(r["c_lean_c0_mean"], lean, rel_tol=1e-12) and r["seeds_without_c_lean_c0"] == [],
              f"(a) per reference {p}: C-lean mean {lean:.6f} c0 over all three seeds")
    # Safe LoRA per reference from its measured per-point values
    lora = out["b10_per_reference"]["safe_lora"]
    lj = job_at(plan, "safe_lora", 1105)
    lled = json.loads((kit / "retrieved" / lj[0] / "tree" / f"job-{lj[1]}" / "cost-ledger.json").read_text())
    for p in ("default", "conditional", "certify"):
        t = sum(s["seconds"] for s in lled["steps"] if s["name"].endswith(f"-transform-{p}"))
        e = sum(s["seconds"] for s in lled["steps"] if s["name"].endswith(f"-evaluate-{p}"))
        check(lora[p]["menu_name"] == f"Safe LoRA {p}" and lora[p]["seeds"] == ["1105"]
              and lora[p]["c_full_fre_mean"] == (t + e) / FRE
              and math.isclose(lora[p]["c_lean_c0_mean"], (t + c0 - LEAN_TRAINING) / c0, rel_tol=1e-12),
              f"(a) Safe LoRA {p}: measured per-point C-full {(t + e) / FRE:.6f} FRE and K6 C-lean, one seed")
    # the 813 value equals one evaluation-only state in the frozen planning prices' sense: a0 slot - training
    print(f"     note: 813 value / a0 slot at 1105 = {mine['rows'][1105][0]['seconds'] / mine['rows'][1105][0]['a0'][2]:.4f}")
    return kit, plan


def case_a_no_c0(base: Path):
    kit, slots, plan = ek.cost_kit(base / "noc0", "plan_a", with_c0=False)
    mine = my_813(kit, plan)
    out = ct.table(kit, "plan_a")
    ev = [v for k, v in out["b10_references"].items() if k.startswith("ref_eval")][0]
    m = mine["rows"][1105][0]
    ok = all(math.isclose(pt["seconds"], m["seconds"], abs_tol=1e-9) and pt["c_full_basis"]["seconds_over_c0"] is None
             and pt["c_lean_c0"] is None and pt["alternative_k5"]["seconds"] is None
             for pt in ev["per_point"].values())
    check(ok, "(a) no c0: the C-full value stands (FRE), seconds_over_c0 null, C-lean null")
    r = out["b10_per_reference"]["ref_eval"]["prefix"]
    check(r["c_full_fre_mean"] == m["fre"] and r["c_lean_c0_mean"] is None and r["seeds_without_c_lean_c0"] == ["1105"],
          "(a) no c0: per-reference C-full mean present, C-lean mean null with the seed listed")


def case_a_no_a0(base: Path):
    kit, slots, plan = ek.cost_kit(base / "noa0", "plan_a")
    h, i = job_at(plan, "ref_eval", 1105)
    plan["hosts"][h]["jobs"][i]["seed"] = 1103
    rewrite_ledger(kit, plan, h, i, lambda d: d.update(seed=1103))
    out = ct.table(kit, "plan_a")
    ev = [v for k, v in out["b10_references"].items() if k.startswith("ref_eval")][0]
    ok = all(pt["seconds"] is None and pt["c_full_basis"]["a0_run"] is None
             and "seed 1103" in pt["c_full_basis"]["why"] and pt["c_lean_c0"] is not None
             for pt in ev["per_point"].values())
    check(ok, "(a) a seed with no a0 run in the ledgers (1103, reused): null with the seed named; C-lean stays")
    # also: the a0 run at 1104 is in block A; a ref_eval at 1104 would match it (synthetic only)
    kit2, slots2, plan2 = ek.cost_kit(base / "a0at1104", "plan_a")
    h, i = job_at(plan2, "ref_eval", 1105)
    plan2["hosts"][h]["jobs"][i]["seed"] = 1104
    rewrite_ledger(kit2, plan2, h, i, lambda d: d.update(seed=1104))
    out2 = ct.table(kit2, "plan_a")
    ev2 = [v for k, v in out2["b10_references"].items() if k.startswith("ref_eval")][0]
    a0 = slots2[job_at(plan2, "a0_arm", 1104, "a0")]
    check(all(math.isclose(pt["seconds"], a0 - FULL_TRAINING, abs_tol=1e-9) for pt in ev2["per_point"].values()),
          "(a) the match is by seed over the reading's blocks (a block-A a0 run at 1104 matches a ref_eval at 1104)")


def case_a_two_jobs(base: Path):
    kit, slots, plan = ek.cost_kit(base / "two", "plan_a", extra_ref_eval_seeds=(1105,))
    try:
        ct.table(kit, "plan_a")
        check(False, "(a) two complete ref_eval jobs at one seed refuse")
    except Refusal as e:
        check("ref_eval at 1105: two complete jobs with a ledger" in str(e),
              f"(a) two complete ref_eval jobs at one seed refuse: {e}")


def case_a_block_a_only(base: Path):
    kit, slots, plan = ek.cost_kit(base / "aonly", "plan_a_block_a_only")
    out = ct.table(kit, "plan_a_block_a_only")
    check(out["b10_references"] == {} and out["b10_per_reference"] == {},
          "(a) block A only: no B10 reference, empty per-reference block")
    check("DataShield-style" in out["charging"]["split_denominator"] and "anchor-1" in out["charging"]["anchor_job"]["what"]
          and out["charging"]["anchor_job"]["charged_here"] is None and "DataShield-style" in out["readings"]["K3"]
          and "anchor job" in out["readings"]["K3"],
          "(c) the split denominator names DataShield-style; the anchor job is named, not priced")
    check(any(r.startswith("REV4:774") for r in out["rule"]) and any(r.startswith("REV4:813") for r in out["rule"])
          and "REV4:813" in out["readings"]["K8"] and "REV4:774" in out["readings"]["K8"]
          and "alternative_k5" in out["readings"]["K5"],
          "(a) the reading is stated in the output: RULE has REV4:774 and :813; K8 and K5 cite them")


def case_a_command_line(base: Path, kit: Path):
    out = base / "cost.json"
    args = ["--kit", str(kit), "--reading", "plan_a", "--out", str(out)]
    code = ct.main(args)
    data = out.read_bytes()
    doc = json.loads(data)
    from scripts.stage1_s1.reading.settings import canonical_json
    check(code == 0 and data == canonical_json(doc), "(a) command line: exit 0, canonical JSON on disk")
    check(ct.main(args) == 2 and out.read_bytes() == data, "(a) command line: a second run exits 2 and the file is unchanged")


def case_b(base: Path):
    for label, reading, kw in (("128", "plan_a_block_a_only", {}), ("128-no-transfer", "plan_a_block_a_only",
                                                                     {"transfers": 0}),
                               ("full", "plan_a_block_a_only", {"branch": "full"})):
        root = base / f"cap-{label}"
        root.mkdir(parents=True, exist_ok=True)
        s = sk.make(root / "w", reading, branch=kw.get("branch", "128"))
        planted = ek.with_caps(s, transfers=kw.get("transfers", 1))
        rec = root / "sources.json"
        assert builder(s.args(root / "tables.json", rec, overlap=False)) == 0
        out = cap.read(s.kit, json.loads(rec.read_text()), sk.sha(rec.read_bytes()))
        line = out["ln19"]["pooled"]["phtest"]
        n = sum(v["phtest"]["prompts_with_both_forms"] for v in planted.values())
        own = json.dumps(out["ln19"]["pooled"]) + json.dumps(out["ln19"]["by_arm_or_reference"]) + \
            json.dumps(out["readings"]) + json.dumps(out["rule"]) + json.dumps(out["ln14"])
        check("no full answer exists" not in own, f"(b) {label}: no 'no full answer exists' in the reader's own lines")
        if label == "128":
            fc = out["ln14"]["report"]["flag_change"]
            check(n == 0 and line["share"] is None and "theta0's LN-14" in line["note"]
                  and line["theta0_ln14"] == {"prompts_with_both_forms": 400, "changed": 4, "share": 0.01,
                                              "source": "ln14.report.flag_change (theta0's transfer pass, REV4:554)"}
                  and fc["share"] == 0.01,
                  f"(b) {label}: pooled PHTest line points to theta0's LN-14 pass and copies its share 4/400")
            check(all(v["phtest"]["note"] == line["note"] for v in out["ln19"]["by_arm_or_reference"].values()),
                  f"(b) {label}: the by-arm PHTest lines carry the same pointer")
        elif label == "128-no-transfer":
            check(line["share"] is None and line["theta0_ln14"]["share"] is None
                  and line["theta0_ln14"]["why"].startswith("not run"),
                  f"(b) {label}: without a transfer pass the pointer says 'not run'")
        else:
            check(n > 0 and line["note"] is None and line["share"] == sum(v["phtest"]["changed"] for v in planted.values()) / n
                  and line["theta0_ln14"]["share"] is None and "Branch 128 only" in line["theta0_ln14"]["why"],
                  f"(b) {label}: every unit holds both forms; share {line['share']:.5f}; LN-14 not applicable")
        unit = next(iter(u for u in out["ln19"]["units"].values() if "flag_change" in u))
        print(f"     {label}: a unit's copied PHTest note: {unit['flag_change']['phtest']['note']!r}")


def main():
    base = Path(sys.argv[1]).resolve()
    base.mkdir(parents=True, exist_ok=True)
    kit, plan = case_a_main(base)
    case_a_no_c0(base)
    case_a_no_a0(base)
    case_a_two_jobs(base)
    case_a_block_a_only(base)
    case_a_command_line(base, kit)
    case_b(base)
    print(f"\nSUMMARY: {len(FAILS)} failures")
    for f in FAILS:
        print("  -", f)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
