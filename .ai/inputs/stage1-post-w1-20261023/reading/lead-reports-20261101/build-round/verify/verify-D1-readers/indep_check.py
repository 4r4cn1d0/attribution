"""Independent re-computation of the five D1 readers on synthetic worlds (verifier's own code; synthetic data only).

Run from the ws-d1 worktree root with the venv python:
    python -B indep_check.py <basetemp>
It builds synthetic worlds with the builder's synth_kit (and extra_kit's planted O-ext keys), runs the builder and
B16 on them, runs each reader through its command line, and recomputes every printed value with code written here
(not the readers' functions). Prints PASS/FAIL lines and a summary.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

WS = Path.cwd()
sys.path.insert(0, str(WS))
sys.path.insert(0, str(WS / "scripts/stage1_s1/reading_extra/tests"))
sys.path.insert(0, str(WS / "scripts/stage1_s1/reading_input/tests"))

import numpy as np  # noqa: E402
import synth_kit as sk  # noqa: E402
import extra_kit as ek  # noqa: E402

from scripts.stage1_s1.reading.__main__ import main as b16_main  # noqa: E402
from scripts.stage1_s1.reading_input.__main__ import main as builder  # noqa: E402
from scripts.stage1_s1.reading_extra import fk_power, stage3_pick, sa_shift, cap_reports, cost_table  # noqa: E402

FAILS = []


def check(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAILS.append(what)


# the statistics review's own planning script, imported by path (its main() is not run)
REV = Path("/Users/spiderishi/Coding/attribution/research/experiments/2026-10-17-stage1-preregistration-rev3")
spec = importlib.util.spec_from_file_location("srop_verifier", REV / "stat_review_o_power.py")
srop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srop)


def review_power(P, q, sd, alpha, J):
    """power_feasible of the review script, with J passed through se_df (the script's power_feasible fixes J = 6)."""
    se, df = srop.se_df(P, q, 0.0, sd, J=J)
    return srop.ncdf((5.0 - 0.0) / se - srop.t_ppf(1 - alpha, df)), se, df


def world(base: Path, reading: str, branch: str = "128", caps: bool = False):
    root = base / f"w-{reading}-{branch}-{int(caps)}"
    s = sk.make(root / "w", reading, branch=branch)
    planted = ek.with_caps(s) if caps else None
    paths = {k: root / f"{k}.json" for k in ("tables", "sources", "reading")}
    assert builder(s.args(paths["tables"], paths["sources"], overlap=False)) == 0
    assert b16_main(["--input", str(paths["tables"]), "--out", str(paths["reading"])]) == 0
    return s, planted, paths, root


def run_reader(mod, args, out: Path):
    rc = mod.main([*args, "--out", str(out)])
    return rc, (json.loads(out.read_text()) if out.exists() else None)


# ---------------------------------------------------------------------------------------------------------------
def check_fk(paths, root, reading):
    rc, out = run_reader(fk_power, ["--input", str(paths["tables"]), "--reading", str(paths["reading"])],
                         root / "fk.json")
    check(rc == 0, f"fk_power {reading}: exit 0")
    tables = json.loads(paths["tables"].read_text())
    rd = json.loads(paths["reading"].read_text())
    o = tables["endpoints"]["O"]
    th = np.array(o["theta0"], dtype=float)
    for name, c, m in rd["design"]["contrasts"]:
        k = out["contrasts"][name]
        seeds = sorted(o["cells"][m], key=int)
        per = [float((np.array(o["cells"][m][j], dtype=float) != th).sum()) / th.size for j in seeds]
        q = sum(per) / len(per)
        check(abs(k["discordance"]["q"] - q) < 1e-15, f"fk {reading} {name}: q {q:.6f} by hand")
        check(k["items"] == th.size and k["seeds"] == len(seeds), f"fk {reading} {name}: P={th.size}, J={len(seeds)}")
        for r in k["planning_power"]:
            want, se, df = review_power(th.size, q, r["seed_sd_pp"], r["alpha"], len(seeds))
            check(abs(r["power"] - want) < 1e-6 and abs(r["se_pp"] - se) < 1e-12 and abs(r["df"] - df) < 1e-9,
                  f"fk {reading} {name}: power sd={r['seed_sd_pp']} a={r['alpha']} {r['power']:.6f} vs review {want:.6f}")
        # F_k copied by key
        f = k["F_k"]
        check(f["F_k_rejects_in_phi"] == rd["rows"][name]["feasibility_part"]["F_k_rejects_in_phi"]
              and f["p_value"] == rd["contrasts"][name]["p_values"]["F"]
              and f["theta0_part"] == rd["contrasts"][name]["O"]["theta0_part"]
              and f["level_at_rejection"] == rd["phi"]["level_at_rejection"].get(f"F:{name}")
              and f["final_level"] == rd["phi"]["final_levels"].get(f"F:{name}"),
              f"fk {reading} {name}: F_k fields equal B16's")
        # theta0_part's estimate equals O(m) - O(theta0) by hand
        est = 100 * np.mean([np.mean(o["cells"][m][j]) for j in seeds]) - 100 * th.mean()
        check(abs(f["theta0_part"]["est"] - est) < 1e-9, f"fk {reading} {name}: B16 theta0 estimate by hand")
    return out


def check_rev4_table_all_rows():
    """All four printed rows of REV4:569-572 from the review formula (rows 3-4 at q + 3 and + 6 pp)."""
    rows = {(0.0, 0.0): ((1.00, 0.97, 0.80, 0.65, 0.55), (0.99, 0.80, 0.43, 0.26, 0.18)),
            (1.15, 0.0): ((1.00, 0.96, 0.78, 0.64, 0.54), (0.96, 0.75, 0.40, 0.25, 0.17)),
            (1.15, 0.03): ((0.98, 0.91, 0.74, 0.61, 0.51), (0.84, 0.61, 0.34, 0.22, 0.16)),
            (1.15, 0.06): ((0.94, 0.85, 0.69, 0.57, 0.49), (0.70, 0.51, 0.30, 0.20, 0.15))}
    for (sd, dq), (pc, ph) in rows.items():
        for alpha, want in ((0.05, pc), (0.00375, ph)):
            got = [fk_power.planning(q + dq, sd, alpha, 500, 6, 5.0)["power"] for q in (0.05, 0.1, 0.2, 0.3, 0.4)]
            check(all(abs(g - w) <= 0.005 + 1e-9 for g, w in zip(got, want)),
                  f"REV4 table row sd={sd} dq={dq} a={alpha}: {[round(g, 2) for g in got]} vs {list(want)}")


# ---------------------------------------------------------------------------------------------------------------
def my_pick(rd):
    texts_better, texts_worse = "better", "worse (U)"
    cands = []
    for name, c, m in rd["design"]["contrasts"]:
        u = rd["contrasts"][name]["U"]
        t = u["est"] / u["se"]
        words = rd["rows"][name]["u_part"]["words"]
        if texts_better in words or texts_worse in words:
            cands.append((-abs(t), int(name[1:]), name))
    cands.sort()
    return [n for _, _, n in cands[:2]]


def check_pick(rd_path: Path, root, label):
    out_path = root / f"pick-{label}.json"
    rc, out = run_reader(stage3_pick, ["--reading", str(rd_path)], out_path)
    rd = json.loads(rd_path.read_text())
    want = my_pick(rd)
    check(rc == 0 and out["pick"] == want, f"stage3_pick {label}: pick {out['pick'] if out else None} vs mine {want}")
    return out


# ---------------------------------------------------------------------------------------------------------------
def check_sa(paths, root, reading):
    rc, out = run_reader(sa_shift, ["--reading", str(paths["reading"])], root / "sa.json")
    tables = json.loads(paths["tables"].read_text())
    rd = json.loads(paths["reading"].read_text())
    names = [n for n, _, _ in rd["design"]["contrasts"]]
    if "P4" not in names:
        check(rc == 0 and out["applies"] is False and out["measured"] is None, f"sa_shift {reading}: not applicable")
        return out
    u = tables["endpoints"]["U"]["cells"]
    val = lambda arm, j: 100.0 * float(np.mean(u[arm][j]))
    a0 = sorted(u["a0"], key=int)
    s1 = sorted(u["S1"], key=int)
    s_a = np.mean([val("a0", j) for j in a0]) - np.mean([val("S1", j) for j in s1])
    common = sorted(set(a0) & set(s1), key=int)
    hb = np.mean([val("a0", j) - val("S1", j) for j in common])
    shift = s_a - hb
    m = out["measured"]
    check(rc == 0 and abs(m["s_a_estimate_pp"] - s_a) < 1e-9 and abs(m["hb_estimate_pp"] - hb) < 1e-9
          and abs(m["s_a_minus_hb_pp"] - shift) < 1e-9,
          f"sa_shift {reading}: S-a {s_a:.4f}, HB {hb:.4f}, shift {shift:.4f} by hand")
    word = "less in S1's favour" if shift < 0 else "more in S1's favour" if shift > 0 else "no shift"
    check(m["direction"] == word and m["expected_direction_holds"] is bool(shift < 0),
          f"sa_shift {reading}: direction word {m['direction']!r} vs mine {word!r}")
    # the a0 seed-1101 identity: S-a - HB = (a0 mean over all its seeds) - (a0 mean over the common seeds) when S1's
    # seeds are the common ones
    if set(s1) <= set(a0):
        ident = np.mean([val("a0", j) for j in a0]) - np.mean([val("a0", j) for j in common])
        check(abs(ident - shift) < 1e-9, f"sa_shift {reading}: shift = a0's extra-seed mean effect ({ident:.4f})")
    check(out["expected"]["s_a_minus_hb_pp"] == -0.28, f"sa_shift {reading}: expected -0.28 pp")
    return out


# ---------------------------------------------------------------------------------------------------------------
def check_cap(s, planted, paths, root, reading, branch):
    rc, out = run_reader(cap_reports, ["--kit", str(s.kit), "--record", str(paths["sources"])], root / "cap.json")
    check(rc == 0, f"cap_reports {reading}/{branch}: exit 0")
    record = json.loads(paths["sources"].read_text())
    plan = json.loads((s.kit / "plan.json").read_text())
    # my own index: COMPLETE.json SHA-256 -> (host, folder)
    idx = {}
    for host, h in plan["hosts"].items():
        for i, job in enumerate(h["jobs"]):
            outs = job.get("outputs") or {}
            if f"job-{i}/oext/COMPLETE.json" in outs:
                idx[outs[f"job-{i}/oext/COMPLETE.json"]] = (host, f"job-{i}/oext")
            for un in job.get("units") or []:
                idx[un["complete_sha256"]] = (host, un["unit"])
    units = {}
    for group in ("cells", "references"):
        for label, e in record[group].items():
            if e["o"]:
                rec, rel = e["o"][0], "oext_summary.json"
            elif e.get("unit") and "eval/e1/oext_summary.json" in (e["unit"].get("files") or {}):
                rec, rel = e["unit"], "eval/e1/oext_summary.json"
            else:
                continue
            host, folder = idx[rec["complete_sha256"]]
            doc = json.loads((s.kit / "retrieved" / host / "tree" / folder / rel).read_text())
            units[label] = doc["flag_change"]
    th = record["theta0"]["o"]
    host, folder = idx[th["complete_sha256"]]
    units["theta0"] = json.loads((s.kit / "retrieved" / host / "tree" / folder / "oext_summary.json").read_text())["flag_change"]
    for src in ("dev100", "phtest"):
        n = sum(u[src]["prompts_with_both_forms"] for u in units.values())
        ch = sum(u[src]["changed"] for u in units.values())
        got = out["ln19"]["pooled"][src]
        check(got["prompts_with_both_forms"] == n and got["changed"] == ch and got["units"] == len(units)
              and got["share"] == (ch / n if n else None),
              f"cap {reading}/{branch}: pooled {src} share {got['share']} vs mine {(ch / n) if n else None}")
        # by arm / reference
        groups = {}
        for label, u in units.items():
            if label == "theta0":
                continue
            groups.setdefault(label.rsplit(" ", 1)[0], []).append(u[src])
        ok = True
        for g, lst in groups.items():
            n2 = sum(x["prompts_with_both_forms"] for x in lst)
            c2 = sum(x["changed"] for x in lst)
            b = out["ln19"]["by_arm_or_reference"][g][src]
            ok &= b["changed"] == c2 and b["prompts_with_both_forms"] == n2 and b["units"] == len(lst)
        check(ok and set(groups) == set(out["ln19"]["by_arm_or_reference"]),
              f"cap {reading}/{branch}: by-arm {src} ({len(groups)} groups)")
    # planted values equal
    ok = all(out["ln19"]["units"][lab]["flag_change"] == planted[(u["source"]["host"], u["source"]["folder"])]
             for lab, u in out["ln19"]["units"].items() if "flag_change" in u)
    check(ok, f"cap {reading}/{branch}: every unit's planted flag_change copied")
    # LN-14 by hand
    tr = [(host, i, j) for host, h in plan["hosts"].items() for i, j in enumerate(h["jobs"])
          if j["kind"] == "transfer_report" and j["status"] == "complete"]
    if branch == "full":
        check(out["ln14"]["applies"] is False, f"cap {reading}/full: LN-14 not applicable")
    elif tr:
        host, i, j = tr[0]
        doc = json.loads((s.kit / "retrieved" / host / "tree" / f"job-{i}" / "transfer" /
                          "oext_transfer_summary.json").read_text())
        bar = doc["bar"]
        mine = 100 * bar["flags_agree"] >= 97 * bar["prompts"] and 100 * abs(bar["refused_full"] - bar["refused_cut"]) <= 2 * bar["prompts"]
        check(out["ln14"]["passes"] is mine, f"cap {reading}/{branch}: LN-14 passes={mine} by hand")
    return out


# ---------------------------------------------------------------------------------------------------------------
def check_cost(base, reading):
    kit, slots, plan = ek.cost_kit(base / f"cost-{reading}", reading)
    rc, out = run_reader(cost_table, ["--kit", str(kit), "--reading", reading], base / f"cost-{reading}.json")
    check(rc == 0, f"cost_table {reading}: exit 0")
    FRE = 2934.0
    jobs = [(host, i, j) for host, h in sorted(plan["hosts"].items()) for i, j in enumerate(h["jobs"])]
    ledgers = {}
    for host, i, j in jobs:
        p = kit / "retrieved" / host / "tree" / f"job-{i}" / "cost-ledger.json"
        if p.exists():
            ledgers[(host, i)] = json.loads(p.read_text())
    c0 = [ledgers[(h, i)]["slot_s"] for h, i, j in jobs if j["kind"] == "c0" and (h, i) in ledgers]
    c0s = c0[0] if len(c0) == 1 else None
    check(out["units"]["c0"]["measured_s"] == c0s, f"cost {reading}: c0 {c0s}")
    from scripts.stage1_s1.reading.settings import design
    dsg = design(reading)
    for arm in dsg.arms:
        kind = "a0_arm" if arm == "a0" else "arm"
        runs = [ledgers[(h, i)]["slot_s"] / FRE for h, i, j in jobs
                if j["kind"] == kind and j.get("arm") == arm and j["status"] == "complete" and (h, i) in ledgers]
        mean = sum(runs) / len(runs) if runs else None
        got = out["arms"][arm]["run"]["c_full_fre_mean"]
        check((mean is None and got is None) or abs(got - mean) < 1e-12, f"cost {reading} {arm}: C-full mean {mean}")
    tot = {}
    for h, i, j in jobs:
        if (h, i) in ledgers and j["kind"] not in ("arm", "a0_arm", "ref_train") and j["status"] == "complete":
            tot[j["kind"]] = tot.get(j["kind"], 0.0) + ledgers[(h, i)]["slot_s"]
    for k, v in tot.items():
        check(abs(out["diagnostics_by_kind"][k]["seconds"] - v) < 1e-9, f"cost {reading}: diagnostics {k} {v}")
    l1 = tot.get("l1_scan", 0) + tot.get("rep_pass", 0)
    check(abs(out["arms"]["L1"]["diagnostic"]["whole"]["seconds"] - l1) < 1e-9 if "L1" in out["arms"] else True,
          f"cost {reading}: L1 whole charge")
    return out


def main():
    base = Path(sys.argv[1])
    base.mkdir(parents=True, exist_ok=True)
    check_rev4_table_all_rows()
    for reading in ("plan_a", "plan_a_block_a_only", "plan_b"):
        s, planted, paths, root = world(base, reading, caps=True)
        check_fk(paths, root, reading)
        check_pick(paths["reading"], root, reading)
        check_sa(paths, root, reading)
        check_cap(s, planted, paths, root, reading, "128")
    s, planted, paths, root = world(base, "plan_a_block_a_only", branch="full", caps=True)
    check_cap(s, planted, paths, root, "plan_a_block_a_only", "full")
    for reading in ("plan_a", "plan_a_block_a_only"):          # extra_kit.cost_kit seals A and B only (no C)
        check_cost(base, reading)
    print(f"\nSUMMARY: {len(FAILS)} failures")
    for f in FAILS:
        print("  -", f)


if __name__ == "__main__":
    main()
