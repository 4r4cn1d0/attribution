"""Round-2 edge cases of cost_table on synthetic cost kits (the verifier's own code; synthetic data only).

    cd <ws-d1> && PYTHONDONTWRITEBYTECODE=1 <venv python> -B <this file> <basetemp>

1. A crashed run whose readable ledger is in the seal, re-run complete on another host: the run counts once.
2. A moved host (not done, listed as moved by the seal) with a ledger in its pulled tree: skipped.
3. A crashed c0 beside a complete c0: the complete one is the unit.
4. What the B10 references print per point under C-full (the open K5 question) and what REV4:813's literal form gives.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

WS = Path.cwd()
sys.path.insert(0, str(WS))
sys.path.insert(0, str(WS / "scripts/stage1_s1/reading_extra/tests"))
sys.path.insert(0, str(WS / "scripts/stage1_s1/reading_input/tests"))

import extra_kit as ek  # noqa: E402
import synth_kit as sk  # noqa: E402

from scripts.stage1_s1.reading_extra import cost_table as ct  # noqa: E402

FAILS = []


def check(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAILS.append(what)


def find(plan, kind, arm=None, seed=None):
    for host, h in sorted(plan["hosts"].items()):
        for i, j in enumerate(h["jobs"]):
            if j["kind"] == kind and (arm is None or j.get("arm") == arm) and (seed is None or j.get("seed") == seed):
                return host, i
    raise KeyError((kind, arm, seed))


def add_job(kit, plan, host, job, slot, steps):
    tree = kit / "retrieved" / host / "tree"
    i = len(plan["hosts"][host]["jobs"])
    digest = sk.write(tree / f"job-{i}" / "cost-ledger.json", sk.jbytes(ek.ledger_doc(host, i, job, slot, steps)))
    plan["hosts"][host]["jobs"].append({**job, "outputs": {f"job-{i}/cost-ledger.json": digest}})
    return i


def case_crashed_rerun(base: Path):
    kit, slots, plan = ek.cost_kit(base / "crash", "plan_a_block_a_only")
    host, i = find(plan, "arm", "H1", 1103)
    job = plan["hosts"][host]["jobs"][i]
    job["status"] = "crashed"
    job["outputs"].pop(f"job-{i}/cost-ledger.json")              # record-done copies a ledger only when complete
    k = add_job(kit, plan, "a-2", {"kind": "arm", "arm": "H1", "seed": 1103, "engine": "X", "status": "complete",
                                   "unit": None, "complete_sha256": None, "reason": None}, 4321.0,
                [("job-x-calibrate", 3000.0), ("job-x-oext", 1000.0)])
    ek.seal(kit, plan, "A")
    (kit / "plan.json").write_bytes(sk.jbytes(plan))
    out = ct.table(kit, "plan_a_block_a_only")
    runs = out["arms"]["H1"]["runs"]
    check(runs["1103"]["host"] == "a-2" and runs["1103"]["slot_s"] == 4321.0 and len(runs) == 3,
          "crashed run + complete re-run: the complete one counts, once")
    crashed = [j for j in out["jobs"] if j["host"] == host and j["index"] == i][0]
    check(crashed["status"] == "crashed" and crashed["ledger"] is not None
          and crashed["ledger"]["named_by_plan_outputs"] is False,
          "the crashed job's readable ledger is listed (named_by_plan_outputs false), not counted")


def case_moved_host(base: Path):
    kit, slots, plan = ek.cost_kit(base / "moved", "plan_a_block_a_only")
    plan["hosts"]["a-9"] = {"block": "A", "done": False, "jobs": []}
    add_job(kit, plan, "a-9", {"kind": "arm", "arm": "S1", "seed": 1102, "engine": "X", "status": "complete",
                               "unit": None, "complete_sha256": None, "reason": None}, 9999.0,
            [("job-0-calibrate", 9000.0)])
    ek.seal(kit, plan, "A")
    seal_path = kit / "seals" / "block-A.json"
    doc = json.loads(seal_path.read_text())
    doc["moved"] = [{"host": "a-9", "to": ["a-2"], "pulled_tree": True}]
    data = sk.jbytes(doc)
    seal_path.write_bytes(data)
    plan["seals"]["A"]["sha256"] = sk.sha(data)
    (kit / "plan.json").write_bytes(sk.jbytes(plan))
    out = ct.table(kit, "plan_a_block_a_only")
    check(all(j["host"] != "a-9" for j in out["jobs"]) and
          all(r["slot_s"] != 9999.0 for r in out["arms"]["S1"]["runs"].values()),
          "a moved host's ledger is not read and not counted")


def case_two_c0(base: Path):
    kit, slots, plan = ek.cost_kit(base / "c0", "plan_a_block_a_only")
    host, i = find(plan, "c0")
    plan["hosts"][host]["jobs"][i]["status"] = "crashed"
    plan["hosts"][host]["jobs"][i]["outputs"].pop(f"job-{i}/cost-ledger.json")
    add_job(kit, plan, "a-2", {"kind": "c0", "arm": "R", "seed": 1101, "engine": "X", "status": "complete",
                               "unit": None, "complete_sha256": None, "reason": None}, 1500.0,
            [("job-y-make-job", 30.0), ("job-y-lean", 1450.0)])
    ek.seal(kit, plan, "A")
    (kit / "plan.json").write_bytes(sk.jbytes(plan))
    out = ct.table(kit, "plan_a_block_a_only")
    check(out["units"]["c0"]["measured_s"] == 1500.0 and out["units"]["c0"]["lean_state_s"] == 1280.0,
          "a crashed c0 beside a complete one: the complete one is c0 (1500 s; lean state 1280 s)")


def case_ref_eval_full(base: Path):
    kit, slots, plan = ek.cost_kit(base / "refs", "plan_a")
    out = ct.table(kit, "plan_a")
    ev = [v for k, v in out["b10_references"].items() if k.startswith("ref_eval")][0]
    lora = [v for k, v in out["b10_references"].items() if k.startswith("safe_lora")][0]
    print("     ref_eval per point:", json.dumps({p: {k: r[k] for k in ("seconds", "c_full_fre", "c_lean_c0")}
                                                  for p, r in ev["per_point"].items()}))
    print("     safe_lora per point:", json.dumps({p: {k: round(r[k], 6) for k in ("seconds", "c_full_fre",
                                                                                     "c_lean_c0")}
                                                   for p, r in lora["per_point"].items()}))
    a0 = [r["slot_s"] for r in out["arms"]["a0"]["runs"].values()]
    literal = (statistics.fmean(a0) - 219.7) / 2934.0
    print(f"     REV4:813's literal C-full form for one ref_eval point: (mean a0 slot {statistics.fmean(a0):.3f} s"
          f" - 219.7 s training + transform ~0) / 2,934 s = {literal:.6f} FRE; the reader prints null")
    check(all(p["c_full_fre"] is None for p in ev["per_point"].values()) and
          all(p["c_lean_c0"] is not None for p in ev["per_point"].values()),
          "ref_eval points: C-lean priced (K6) but C-full null (K5) -- the asymmetry reported")


def main():
    base = Path(sys.argv[1])
    base.mkdir(parents=True, exist_ok=True)
    case_crashed_rerun(base)
    case_moved_host(base)
    case_two_c0(base)
    case_ref_eval_full(base)
    print(f"\nSUMMARY: {len(FAILS)} failures")
    for f in FAILS:
        print("  -", f)


if __name__ == "__main__":
    main()
