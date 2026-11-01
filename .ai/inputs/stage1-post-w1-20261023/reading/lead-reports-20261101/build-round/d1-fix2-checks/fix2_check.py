"""Hand check of fix round 2 (track D1, cost_table and cap_reports) on the synthetic kits: the REV4:813 value per
ref_eval point from the planted ledgers by hand, the per-reference means, the K5 null beside, the anchor job and the
split denominator, and the LN-19 PHTest line. Usage (from the ws-d1 root, the venv python):

    PYTHONDONTWRITEBYTECODE=1 python -B scratchpad/builds/d1-fix2-checks/fix2_check.py <basetemp>

Prints PASS/FAIL lines and the values; exit 1 on any FAIL. Synthetic data only."""

import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "ws-d1"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "stage1_s1" / "reading_input" / "tests"))
sys.path.insert(0, str(ROOT / "scripts" / "stage1_s1" / "reading_extra" / "tests"))

import extra_kit as ek  # noqa: E402
import synth_kit as sk  # noqa: E402

from scripts.stage1_s1.reading_extra import cap_reports as cap  # noqa: E402
from scripts.stage1_s1.reading_extra import cost_table as ct  # noqa: E402
from scripts.stage1_s1.reading_input.__main__ import main as builder  # noqa: E402

FRE = 2934.0
fails = 0


def check(name, ok, *values):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + name, *values)


def job_of(plan, kind, seed=None):
    for host, h in sorted(plan["hosts"].items()):
        for i, j in enumerate(h["jobs"]):
            if j["kind"] == kind and (seed is None or j["seed"] == seed):
                return host, i
    raise KeyError((kind, seed))


def cost_checks(root: Path) -> None:
    kit, slots, plan = ek.cost_kit(root / "cost", "plan_a", extra_ref_eval_seeds=(1106,))
    out = ct.table(kit, "plan_a")
    c0 = slots[job_of(plan, "c0")]
    print(f"c0 {c0:.3f} s; lean state {c0 - 220.0:.3f} s; full training 219.7 s")
    means = {}
    for key, rec in sorted(out["b10_references"].items()):
        if not key.startswith("ref_eval"):
            continue
        seed = rec["seed"]
        a0_host, a0_i = job_of(plan, "a0_arm", seed)
        a0 = slots[(a0_host, a0_i)]
        ledger = json.loads((kit / "retrieved" / key.split(" ")[1] / "tree" / f"job-{key.split(' ')[3]}" /
                             "cost-ledger.json").read_text())
        transform = ledger["stages_s"]["transform"]
        want = a0 - 219.7 + transform
        print(f"{key}: a0 run {a0_host} job {a0_i} slot {a0:.3f} s, transform {transform} s -> "
              f"{want:.3f} s = {want / FRE:.6f} FRE = {want / c0:.6f} c0 (the ref_eval slot itself {rec['seconds']:.3f} s)")
        for p, point in sorted(rec["per_point"].items()):
            check(f"{key} {p} seconds", math.isclose(point["seconds"], want, abs_tol=1e-9), point["seconds"])
            check(f"{key} {p} c_full_fre", math.isclose(point["c_full_fre"], want / FRE, rel_tol=1e-12))
            check(f"{key} {p} seconds_over_c0", math.isclose(point["c_full_basis"]["seconds_over_c0"], want / c0,
                                                              rel_tol=1e-12))
            check(f"{key} {p} a0 run named", point["c_full_basis"]["a0_run"] == {"seed": seed, "host": a0_host,
                                                                                  "index": a0_i, "slot_s": a0})
            check(f"{key} {p} K5 null beside", point["alternative_k5"]["seconds"] is None and
                  point["alternative_k5"]["c_full_fre"] is None and "not stated" in point["alternative_k5"]["why"])
            check(f"{key} {p} C-lean (K6) unchanged", math.isclose(point["c_lean_c0"], (c0 - 220.0) / c0, rel_tol=1e-12))
            means.setdefault(p, []).append(want / FRE)
    for p, values in sorted(means.items()):
        rec = out["b10_per_reference"]["ref_eval"][p]
        print(f"per reference {p} ({rec['menu_name']}): seeds {rec['seeds']}, mean {rec['c_full_fre_mean']:.6f} FRE "
              f"(by hand {statistics.fmean(values):.6f}), min {rec['c_full_fre_min']:.6f}, max {rec['c_full_fre_max']:.6f}; "
              f"C-lean mean {rec['c_lean_c0_mean']:.6f} c0")
        check(f"per reference {p} mean", math.isclose(rec["c_full_fre_mean"], statistics.fmean(values), rel_tol=1e-12))
        check(f"per reference {p} min/max", rec["c_full_fre_min"] == min(values) and rec["c_full_fre_max"] == max(values))
    lora = out["b10_per_reference"]["safe_lora"]
    check("safe_lora per reference default", lora["default"]["c_full_fre_mean"] == 200.0 / FRE and lora["default"]["seeds"] == ["1105"])
    check("K3 names DataShield-style", "DataShield-style" in out["readings"]["K3"])
    check("split denominator in the output", "DataShield-style" in out["charging"]["split_denominator"])
    check("anchor job named", "anchor-1" in out["charging"]["anchor_job"]["what"] and
          out["charging"]["anchor_job"]["charged_here"] is None)
    print("charging.anchor_job.what:", out["charging"]["anchor_job"]["what"])


def cap_checks(root: Path) -> None:
    s = sk.make(root / "w", "plan_a_block_a_only", branch="128")
    ek.with_caps(s)
    rec = root / "sources.json"
    assert builder(s.args(root / "tables.json", rec, overlap=False)) == 0
    out = cap.read(s.kit, json.loads(rec.read_text()), sk.sha(rec.read_bytes()))
    line = out["ln19"]["pooled"]["phtest"]
    print("LN-19 pooled PHTest note:", line["note"])
    print("theta0_ln14:", line["theta0_ln14"])
    own = json.dumps(out["ln19"]["pooled"]) + json.dumps(out["ln19"]["by_arm_or_reference"]) + json.dumps(out["readings"])
    check("no 'no full answer exists' in the reader's own lines", "no full answer exists" not in own)
    unit_note = next(iter(out["ln19"]["units"].values()))["flag_change"]["phtest"]["note"]
    print("a unit's own copied note (oext_eval's text, by key):", unit_note)
    check("theta0's LN-14 share copied", line["theta0_ln14"]["share"] == out["ln14"]["report"]["flag_change"]["share"] == 4 / 400)
    check("the note points to ln14", "ln14.report.flag_change" in line["note"])


if __name__ == "__main__":
    base = Path(sys.argv[1]).resolve()
    base.mkdir(parents=True, exist_ok=True)
    cost_checks(base)
    cap_checks(base)
    print(f"{fails} FAIL")
    sys.exit(1 if fails else 0)
