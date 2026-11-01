"""Round-2 independent re-computation of the five D1 readers (the verifier's own code; synthetic data only).

    cd <ws-d1> && PYTHONDONTWRITEBYTECODE=1 <venv python> -B <this file> <basetemp>

Builds synthetic worlds with the builder's synth_kit (route and flag_change planted by extra_kit), runs the input
builder and B16 on them, runs every reader through its command line with an audit hook on file opens, and recomputes
each printed value with code written here: its own Student-t quantile (Simpson integration of the density, not B16's
tdist and not the review's continued fraction), its own walk of the synthetic kit and its own cost arithmetic.
Prints PASS/FAIL lines and a summary. Nothing here reads a real kit file.
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

import numpy as np  # noqa: E402
import synth_kit as sk  # noqa: E402
import extra_kit as ek  # noqa: E402

from scripts.stage1_s1.reading.__main__ import main as b16_main  # noqa: E402
from scripts.stage1_s1.reading_input.__main__ import main as builder  # noqa: E402
from scripts.stage1_s1.reading_extra import fk_power, stage3_pick, sa_shift, cap_reports, cost_table  # noqa: E402

FAILS: list = []
OPENED: list = []
RECORD = {"on": False}


def hook(event, args):
    if RECORD["on"] and event in ("open", "os.listdir", "os.scandir"):
        target = args[0] if args else None
        if isinstance(target, (str, bytes, Path)):
            OPENED.append((event, str(target if not isinstance(target, bytes) else target.decode())))


sys.addaudithook(hook)


def check(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAILS.append(what)


# ----- an independent Student t (Simpson on the density) ------------------------------------------------------------
def t_pdf(x, df):
    return math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2) - 0.5 * math.log(df * math.pi)
                    - (df + 1) / 2 * math.log1p(x * x / df))


def t_cdf_pos(x, df, n=6000):
    h = x / n
    s = t_pdf(0.0, df) + t_pdf(x, df)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * t_pdf(i * h, df)
    return 0.5 + s * h / 3


def t_ppf(p, df):
    lo, hi = 0.0, 60.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if t_cdf_pos(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def phi(x):
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def my_power(q, sd, alpha, P, J, tau=5.0):
    v_item = q / P * 1e4
    v_seed = sd * sd / J
    v = v_item + v_seed
    den = (v_seed ** 2 / (J - 1) if v_seed > 0 else 0.0) + v_item ** 2 / (P - 1)
    df = v * v / den
    return phi(tau / math.sqrt(v) - t_ppf(1 - alpha, df)), math.sqrt(v), df


# ----- worlds ---------------------------------------------------------------------------------------------------------
def world(base: Path, reading: str, branch: str = "128"):
    root = base / f"w-{reading}-{branch}"
    s = sk.make(root / "w", reading, branch=branch)
    planted = ek.with_caps(s)
    paths = {k: root / f"{k}.json" for k in ("tables", "sources", "reading")}
    assert builder(s.args(paths["tables"], paths["sources"], overlap=False)) == 0
    assert b16_main(["--input", str(paths["tables"]), "--out", str(paths["reading"])]) == 0
    return s, planted, paths, root


def run_reader(mod, args, out: Path):
    OPENED.clear()
    RECORD["on"] = True
    try:
        rc = mod.main([*args, "--out", str(out)])
    finally:
        RECORD["on"] = False
    opened = list(OPENED)
    return rc, (json.loads(out.read_text()) if out.exists() else None), opened


# ----- (1) fk_power ---------------------------------------------------------------------------------------------------
def check_fk(paths, root, reading):
    rc, out, opened = run_reader(fk_power, ["--input", str(paths["tables"]), "--reading", str(paths["reading"])],
                                 root / "fk.json")
    check(rc == 0, f"fk {reading}: exit 0")
    tables = json.loads(paths["tables"].read_text())
    rd = json.loads(paths["reading"].read_text())
    o = tables["endpoints"]["O"]
    th = np.array(o["theta0"], dtype=int)
    worst = 0.0
    for name, c, m in rd["design"]["contrasts"]:
        k = out["contrasts"][name]
        seeds = sorted(o["cells"][m], key=int)
        per = {j: int(np.sum(np.array(o["cells"][m][j], dtype=int) != th)) / th.size for j in seeds}
        q = sum(per.values()) / len(per)
        check(abs(k["discordance"]["q"] - q) < 1e-15 and k["discordance"]["per_seed"] == per,
              f"fk {reading} {name}: q = {q:.5f} (per seed by hand)")
        check(k["items"] == 500 and k["seeds"] == len(seeds) and k["repair"] == m,
              f"fk {reading} {name}: P 500, J {len(seeds)}, repair {m}")
        check(k["differs_from_planning_p_j"] == ([500, len(seeds)] != [500, 6]), f"fk {reading} {name}: J flag")
        rows = {(r["seed_sd_pp"], r["alpha"]): r for r in k["planning_power"]}
        check(set(rows) == {(0.0, 0.05), (0.0, 0.00375), (1.15, 0.05), (1.15, 0.00375)},
              f"fk {reading} {name}: the four rows")
        for (sd, alpha), r in rows.items():
            pw, se, df = my_power(q, sd, alpha, 500, len(seeds))
            worst = max(worst, abs(pw - r["power"]))
            check(abs(pw - r["power"]) < 2e-7 and abs(se - r["se_pp"]) < 1e-12 and abs(df - r["df"]) < 1e-8,
                  f"fk {reading} {name}: sd {sd} a {alpha}: power {r['power']:.6f} vs mine {pw:.6f}")
        f = k["F_k"]
        check(f["F_k_rejects_in_phi"] == rd["rows"][name]["feasibility_part"]["F_k_rejects_in_phi"]
              and f["p_value"] == rd["contrasts"][name]["p_values"]["F"]
              and f["theta0_part"] == rd["contrasts"][name]["O"]["theta0_part"]
              and f["theta0_interval_90"] == rd["contrasts"][name]["O"]["theta0_interval_90"]
              and f["level_at_rejection"] == rd["phi"]["level_at_rejection"].get(f"F:{name}")
              and f["final_level"] == rd["phi"]["final_levels"].get(f"F:{name}")
              and f["states"] == rd["rows"][name]["feasibility_part"]["states"],
              f"fk {reading} {name}: F_k's result copied by key")
    print(f"     fk {reading}: largest |power - mine| = {worst:.2e}")
    return opened


# ----- (2) stage3_pick ------------------------------------------------------------------------------------------------
def my_pick(rd):
    cands = []
    for name, c, m in rd["design"]["contrasts"]:
        u = rd["contrasts"][name]["U"]
        t = u["est"] / u["se"]
        words = rd["rows"][name]["u_part"]["words"]
        if "better" in words or "worse (U)" in words:
            cands.append((-abs(t), int(name[1:]), name))
    cands.sort()
    return [n for _, _, n in cands[:2]]


def check_pick(rd_path: Path, root: Path, label: str, want=None):
    rc, out, opened = run_reader(stage3_pick, ["--reading", str(rd_path)], root / f"pick-{label}.json")
    rd = json.loads(rd_path.read_text())
    mine = my_pick(rd) if want is None else want
    check(rc == 0 and out["pick"] == mine, f"pick {label}: {out['pick'] if out else rc} vs mine {mine}")
    return out, opened


def u_doc(est, se, words, rejected=True):
    better, worse = "better" in words, "worse (U)" in words
    return ({"est": est, "se": se, "t": est / se, "df": 10.0, "form": "synthetic"},
            {"rejected": rejected, "est": est, "direction": None, "better": better, "worse": worse,
             "grade1": False, "grade2": False, "note": False, "words": list(words)})


def pick_edges(rd_path: Path, root: Path):
    base = json.loads(rd_path.read_text())
    cases = {
        # name: ({contrast: (est, se, words)}, expected pick)
        "tie worse(U) P1 and better P3, equal |t|": (
            {"P1": (-6.0, 2.0, ["worse (U)"]), "P3": (6.0, 2.0, ["better"]), "P2": (1.0, 2.0, ["inconclusive"])},
            ["P1", "P3"]),
        "tie the other way round": (
            {"P5": (-6.0, 2.0, ["worse (U)"]), "P2": (6.0, 2.0, ["better"])}, ["P2", "P5"]),
        "three eligible, the two largest |t|": (
            {"P1": (8.0, 2.0, ["better"]), "P4": (-9.0, 2.0, ["worse (U)", "equivalent (per comparison)"]),
             "P6": (12.0, 2.0, ["better"])}, ["P6", "P4"]),
        "none eligible": ({}, []),
        "a below-SESOI note alone is not eligible": (
            {"P2": (3.0, 0.5, ["inconclusive", "significant, below the smallest effect of interest"])}, []),
        "one eligible": ({"P5": (5.5, 1.0, ["better"])}, ["P5"]),
        "largest |t| is not the largest estimate": (
            {"P1": (20.0, 10.0, ["better"]), "P2": (6.0, 1.0, ["better"]), "P3": (7.0, 1.5, ["better"])},
            ["P2", "P3"]),
    }
    for label, (spec, want) in cases.items():
        doc = json.loads(json.dumps(base))
        for name, _, _ in doc["design"]["contrasts"]:                 # every contrast inconclusive first
            u, part = u_doc(0.5, 1.0, ["inconclusive"], rejected=False)
            doc["contrasts"][name]["U"].update(u)
            doc["rows"][name]["u_part"].update(part)
        for name, (est, se, words) in spec.items():
            u, part = u_doc(est, se, words)
            doc["contrasts"][name]["U"].update(u)
            doc["rows"][name]["u_part"].update(part)
        p = root / f"edge-{abs(hash(label)) % 10 ** 8}.json"
        p.write_text(json.dumps(doc))
        check_pick(p, root, f"edge: {label}", want=want)


# ----- (3) sa_shift ---------------------------------------------------------------------------------------------------
def check_sa(paths, root, reading):
    rc, out, opened = run_reader(sa_shift, ["--reading", str(paths["reading"])], root / "sa.json")
    tables = json.loads(paths["tables"].read_text())
    rd = json.loads(paths["reading"].read_text())
    names = [n for n, _, _ in rd["design"]["contrasts"]]
    if "P4" not in names:
        check(rc == 0 and out["applies"] is False and out["measured"] is None and "not applicable" in out["note"],
              f"sa {reading}: not applicable")
        return opened
    u = tables["endpoints"]["U"]["cells"]
    val = lambda arm, j: 100.0 * float(np.mean(u[arm][j]))
    a0, s1 = sorted(u["a0"], key=int), sorted(u["S1"], key=int)
    s_a = np.mean([val("a0", j) for j in a0]) - np.mean([val("S1", j) for j in s1])
    common = sorted(set(a0) & set(s1), key=int)
    hb = np.mean([val("a0", j) - val("S1", j) for j in common])
    m = out["measured"]
    check(rc == 0 and abs(m["s_a_estimate_pp"] - s_a) < 1e-9 and abs(m["hb_estimate_pp"] - hb) < 1e-9
          and abs(m["s_a_minus_hb_pp"] - (s_a - hb)) < 1e-9,
          f"sa {reading}: S-a {s_a:.4f} HB {hb:.4f} shift {s_a - hb:.4f} by hand")
    word = "less in S1's favour" if s_a - hb < 0 else "more in S1's favour" if s_a - hb > 0 else "no shift"
    check(m["direction"] == word and out["expected"]["s_a_minus_hb_pp"] == -0.28, f"sa {reading}: words and -0.28")
    check(abs(m["primary_estimate_pp"] - rd["contrasts"]["P4"]["U"]["est"]) < 1e-12, f"sa {reading}: primary P4")
    return opened


# ----- (4) cap_reports ------------------------------------------------------------------------------------------------
def check_cap(s, planted, paths, root, reading, branch):
    rc, out, opened = run_reader(cap_reports, ["--kit", str(s.kit), "--record", str(paths["sources"])],
                                 root / "cap.json")
    check(rc == 0, f"cap {reading}/{branch}: exit 0")
    record = json.loads(paths["sources"].read_text())
    plan = json.loads((s.kit / "plan.json").read_text())
    idx = {}
    for host, h in plan["hosts"].items():
        for i, job in enumerate(h["jobs"]):
            outs = job.get("outputs") or {}
            if f"job-{i}/oext/COMPLETE.json" in outs:
                idx[outs[f"job-{i}/oext/COMPLETE.json"]] = (host, f"job-{i}/oext", "oext_summary.json")
            for un in job.get("units") or []:
                idx[un["complete_sha256"]] = (host, un["unit"], "eval/e1/oext_summary.json")
    units = {}
    for group in ("cells", "references"):
        for label, e in record[group].items():
            rec = e["o"][0] if e["o"] else (e.get("unit") if "eval/e1/oext_summary.json" in
                                            ((e.get("unit") or {}).get("files") or {}) else None)
            if rec is None:
                continue
            host, folder, rel = idx[rec["complete_sha256"]]
            units[label] = json.loads((s.kit / "retrieved" / host / "tree" / folder / rel).read_text())
    th = record["theta0"]["o"]
    host, folder, rel = idx[th["complete_sha256"]]
    units["theta0"] = json.loads((s.kit / "retrieved" / host / "tree" / folder / rel).read_text())
    check(set(units) == {k for k, v in out["ln19"]["units"].items() if "flag_change" in v},
          f"cap {reading}/{branch}: the same {len(units)} units")
    for src in ("dev100", "phtest"):
        n = sum(u["flag_change"][src]["prompts_with_both_forms"] for u in units.values())
        ch = sum(u["flag_change"][src]["changed"] for u in units.values())
        got = out["ln19"]["pooled"][src]
        check(got["prompts_with_both_forms"] == n and got["changed"] == ch and got["share"] == (ch / n if n else None),
              f"cap {reading}/{branch}: pooled {src}: {ch}/{n}")
        groups = {}
        for label, u in units.items():
            if label != "theta0":
                groups.setdefault(label.rsplit(" ", 1)[0], []).append(u["flag_change"][src])
        ok = set(groups) == set(out["ln19"]["by_arm_or_reference"])
        for g, lst in groups.items():
            b = out["ln19"]["by_arm_or_reference"][g][src]
            n2, c2 = sum(x["prompts_with_both_forms"] for x in lst), sum(x["changed"] for x in lst)
            ok &= (b["units"], b["prompts_with_both_forms"], b["changed"], b["share"]) == (
                len(lst), n2, c2, c2 / n2 if n2 else None)
        check(ok, f"cap {reading}/{branch}: by arm or reference, {src} ({len(groups)} groups)")
    routes = {json.dumps(u["route"], sort_keys=True) for u in units.values()}
    check(len(routes) == 1 and out["route_per_source"] == json.loads(routes.pop()), f"cap {reading}/{branch}: one route")
    check(all(out["ln19"]["units"][lab]["flag_change"] == planted[(v["source"]["host"], v["source"]["folder"])]
              for lab, v in out["ln19"]["units"].items() if "flag_change" in v),
          f"cap {reading}/{branch}: every planted flag_change copied")
    tr = [(h, i, j) for h, hh in plan["hosts"].items() for i, j in enumerate(hh["jobs"])
          if j["kind"] == "transfer_report" and j["status"] == "complete"]
    if branch == "full":
        check(out["ln14"]["applies"] is False and out["branch"] == "full", f"cap {reading}/full: LN-14 not applicable")
    else:
        host, i, _ = tr[0]
        bar = json.loads((s.kit / "retrieved" / host / "tree" / f"job-{i}" / "transfer" /
                          "oext_transfer_summary.json").read_text())["bar"]
        mine = bar["flags_agree"] >= 0.97 * bar["prompts"] - 1e-9 and abs(bar["refused_full"] - bar["refused_cut"]) <= \
            0.02 * bar["prompts"] + 1e-9
        check(out["ln14"]["passes"] is mine, f"cap {reading}/{branch}: LN-14 passes = {mine} (agree >= 97%, move <= 2%)")
    return out, opened


# ----- (5) cost_table -------------------------------------------------------------------------------------------------
FRE = 2934.0
USES = {"L1": ("l1_scan", "rep_pass"), "S3": ("untuned_answers", "rep_pass"), "S4": ("untuned_answers",)}


def close(a, b, tol=1e-9):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol * max(1.0, abs(b))


def my_cost(kit: Path, reading: str):
    """Every number of the cost table from the plan and the ledger files, by my own reading of K1-K7."""
    from scripts.stage1_s1.reading.settings import design
    dsg = design(reading)
    plan = json.loads((kit / "plan.json").read_text())
    blocks = {"plan_a": ("A", "B"), "plan_a_block_a_only": ("A",), "plan_b": ("A", "B", "C")}[reading]
    jobs = []
    for host, h in sorted(plan["hosts"].items()):
        if h["block"] not in blocks or not h.get("done"):
            continue
        for i, j in enumerate(h["jobs"]):
            p = kit / "retrieved" / host / "tree" / f"job-{i}" / "cost-ledger.json"
            led = json.loads(p.read_text()) if p.exists() else None
            jobs.append((host, i, j, led))
    done = lambda kind: [(h, i, j, l) for h, i, j, l in jobs if j["kind"] == kind and l and j["status"] == "complete"]
    c0s = done("c0")
    c0 = c0s[0][3]["slot_s"] if len(c0s) == 1 else None
    lean = (c0 - 220.0) if c0 is not None and c0 > 220.0 else None
    exp = {"c0": c0, "lean": lean, "arms": {}, "kinds": {}, "charge": {}, "b10": {}}
    for arm in dsg.arms:
        runs = [l["slot_s"] for h, i, j, l in done("a0_arm" if arm == "a0" else "arm") if j["arm"] == arm]
        exp["arms"][arm] = {"n": len(runs), "mean": statistics.fmean([r / FRE for r in runs]) if runs else None,
                            "slots": runs}
    exp["r_median"] = statistics.median(exp["arms"]["R"]["slots"]) if exp["arms"]["R"]["slots"] else None
    kinds = {j["kind"] for h, i, j, l in jobs if l} - {"arm", "a0_arm", "ref_train", "ref_eval", "safe_lora"}
    for arm, used in USES.items():
        if arm in dsg.arms:
            kinds |= set(used)
    for k in kinds:
        d = done(k)
        exp["kinds"][k] = sum(l["slot_s"] for *_, l in d) if d else None
    users = {}
    for arm, used in USES.items():
        if arm in dsg.arms:
            for k in used:
                users.setdefault(k, []).append(arm)
    for arm, used in USES.items():
        if arm not in dsg.arms:
            continue
        if any(exp["kinds"][k] is None for k in used):
            exp["charge"][arm] = None
        else:
            exp["charge"][arm] = (sum(exp["kinds"][k] for k in used),
                                  sum(exp["kinds"][k] / len(users[k]) for k in used))
    exp["charge"]["A1"] = (3.04 * 3600, 3.04 * 3600)
    for h, i, j, l in done("safe_lora"):
        steps = {s["name"]: s["seconds"] for s in l["steps"]}
        per, ev = {}, 0.0
        for p in j["points"]:
            t = steps[f"job-{i}-transform-{p}"]
            e = steps[f"job-{i}-evaluate-{p}"]
            ev += e
            per[p] = (t + e, None if lean is None else t + lean)
        whole_lean = None if lean is None else l["slot_s"] - ev + len(j["points"]) * lean
        regen = sum(v for n, v in steps.items() if n.endswith("-b10-regenerate"))
        exp["b10"][f"safe_lora {h} job {i}"] = {"slot": l["slot_s"], "whole_lean": whole_lean, "per": per,
                                                "regen": regen}
    for h, i, j, l in done("ref_eval"):
        exp["b10"][f"ref_eval {h} job {i}"] = {"slot": l["slot_s"], "whole_lean": None,
                                               "per": {p: (None, lean) for p in j["points"]}, "regen": None}
    return exp


def check_cost(base: Path, reading: str, kit=None, label=None):
    label = label or reading
    if kit is None:
        kit, slots, plan = ek.cost_kit(base / f"cost-{label}", reading)
    rc, out, opened = run_reader(cost_table, ["--kit", str(kit), "--reading", reading], base / f"cost-{label}.json")
    check(rc == 0, f"cost {label}: exit 0")
    if rc != 0:
        return None, opened
    e = my_cost(kit, reading)
    c0 = e["c0"]
    u = out["units"]
    check(u["c0"]["measured_s"] == c0 and u["c0"]["lean_state_s"] == e["lean"] and u["fre_s"] == FRE,
          f"cost {label}: c0 {c0}, lean state {e['lean']}")
    check(u["fre_beside"]["median_slot_s"] == e["r_median"] and u["fre_beside"]["r_runs"] == e["arms"]["R"]["n"]
          and close(u["fre_beside"]["median_slot_fre"], None if e["r_median"] is None else e["r_median"] / FRE),
          f"cost {label}: median stage-1 R slot {e['r_median']} over {e['arms']['R']['n']} runs")
    for arm, a in e["arms"].items():
        run = out["arms"][arm]["run"]
        check(run["seeds"] == a["n"] and close(run["c_full_fre_mean"], a["mean"])
              and run["c_lean_c0"] == (1.0 if c0 is not None else None), f"cost {label} {arm}: runs {a['n']}, C-full mean")
    for k, v in e["kinds"].items():
        got = out["diagnostics_by_kind"].get(k)
        ok = got is not None and close(got["seconds"], v)
        if ok and v is not None:
            ok = close(got["c_full_fre"], v / FRE) and close(got["c_lean_c0"], None if c0 is None else v / c0) \
                and got["approximately_zero"] is (v / FRE < 0.01)
        check(ok, f"cost {label}: by kind {k} = {v}")
    check(set(out["diagnostics_by_kind"]) == set(e["kinds"]), f"cost {label}: the by-kind set {sorted(e['kinds'])}")
    for arm, ch in e["charge"].items():
        d = out["arms"][arm]["diagnostic"]
        if ch is None:
            check(d["whole"] is None and d["split"] is None, f"cost {label} {arm}: no charge (a kind with no job)")
            continue
        whole, split = ch
        ok = close(d["whole"]["seconds"], whole) and close(d["split"]["seconds"], split) \
            and close(d["whole"]["c_lean_c0"], None if c0 is None else whole / c0)
        mean = e["arms"][arm]["mean"]
        if mean is not None:
            ok &= close(out["arms"][arm]["total"]["whole"]["c_full_fre"], mean + whole / FRE) and close(
                out["arms"][arm]["total"]["split"]["c_lean_c0"], None if c0 is None else 1.0 + split / c0)
        check(ok, f"cost {label} {arm}: charge whole {whole:.3f} split {split:.3f} and totals")
    for arm in ("H1", "S1"):
        if arm in out["arms"]:
            d = out["arms"][arm]["diagnostic"]
            check(d["whole"]["seconds"] == 0.0 and "Mac" in d.get("note", ""), f"cost {label} {arm}: Mac note, 0 s")
    for key, b in e["b10"].items():
        got = out["b10_references"].get(key)
        if got is None:
            check(False, f"cost {label}: {key} missing")
            continue
        ok = close(got["seconds"], b["slot"]) and close(got["c_full_fre"], b["slot"] / FRE)
        ok &= close(got["c_lean_c0"], None if b["whole_lean"] is None or c0 is None else b["whole_lean"] / c0)
        for p, (full, lean) in b["per"].items():
            g = got["per_point"][p]
            ok &= close(g["seconds"], full) and close(g["c_full_fre"], None if full is None else full / FRE)
            ok &= close(g["c_lean_c0"], None if lean is None or c0 is None else lean / c0)
        if b["regen"] is not None:
            ok &= close(got["a0_regeneration_reported_apart"]["seconds"], b["regen"])
        check(ok, f"cost {label}: {key} (whole and per point, both conventions)")
    check(set(out["b10_references"]) == set(e["b10"]), f"cost {label}: the B10 jobs")
    return out, opened


def audit(opened, kit: Path, label: str, allowed_names):
    """Every file the reader opened under the kit: its name must be allowed; no folder listing."""
    names = sorted({Path(p).name for ev, p in opened if p.startswith(str(kit)) and ev == "open"})
    lists = [p for ev, p in opened if ev != "open" and p.startswith(str(kit))]
    check(set(names) <= set(allowed_names) and not lists, f"audit {label}: opened under the kit {names}; listings {len(lists)}")
    return names


def seal_classes(kit: Path):
    classes = {}
    for p in (kit / "seals").glob("block-*.json"):
        for f in json.loads(p.read_text())["files"]:
            classes[str(kit / "retrieved" / f["host"] / "tree" / f["path"])] = f["class"]
    return classes


def main():
    base = Path(sys.argv[1])
    base.mkdir(parents=True, exist_ok=True)
    for reading in ("plan_a", "plan_a_block_a_only", "plan_b"):
        s, planted, paths, root = world(base, reading)
        op = check_fk(paths, root, reading)
        outside = sorted({Path(p).name for ev, p in op if ev == "open" and not p.endswith(".py")})
        print(f"     fk {reading}: non-module files opened {outside}")
        _, op = check_pick(paths["reading"], root, reading)
        op2 = check_sa(paths, root, reading)
        out, op3 = check_cap(s, planted, paths, root, reading, "128")
        names = audit(op3, s.kit, f"cap {reading}", {"plan.json", "block-A.json", "block-B.json", "block-C.json",
                                                    "COMPLETE.json", "oext_summary.json",
                                                    "oext_transfer_summary.json"})
        cls = seal_classes(s.kit)
        sealed = sorted({Path(p).name for ev, p in op3 if cls.get(p) == "sealed"})
        print(f"     cap {reading}: sealed-class files opened (by name) {sealed}")
        if reading == "plan_a":
            pick_edges(paths["reading"], root)
    s, planted, paths, root = world(base, "plan_a_block_a_only", branch="full")
    check_cap(s, planted, paths, root, "plan_a_block_a_only", "full")
    for reading in ("plan_a", "plan_a_block_a_only", "plan_b"):
        out, op = check_cost(base, reading)
        kit = base / f"cost-{reading}" / "kit"
        names = audit(op, kit, f"cost {reading}", {"plan.json", "block-A.json", "block-B.json", "block-C.json",
                                                   "cost-ledger.json"})
        cls = seal_classes(kit)
        bad = [p for ev, p in op if ev == "open" and cls.get(p) == "sealed"]
        check(not bad, f"audit cost {reading}: no sealed-class file opened ({len(bad)})")
    print(f"\nSUMMARY: {len(FAILS)} failures")
    for f in FAILS:
        print("  -", f)


if __name__ == "__main__":
    main()
