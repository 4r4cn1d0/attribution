"""End-to-end parity THROUGH simulate_row (not run_chunk): the settings' scenarios, family_sigmas, the chunk streams and
the row's printed counts, against an independent chain on the same draws (chunk_normals / chunk_prompt_normals of a
scratch seed). The independent chain derives each family's true sigma itself (OLMo-2-7B = the grid's sigma;
Llama-3.1-8B = ratio x it, capped at the grid's top; Fractions), the cell SD itself (sigma / sqrt 2, x sqrt(1 + share)
on method cells), sigma_A by blinded_sigma.pooled_sigma on blinded_sigma.design_cells, the plan by noise_reading's
seed_rule, the claim test by B16 fit_cells (multi-start, lone 1101 cells in the fit, the two-arm rule on the common
seeds) + contrast_fit (with_item False) + phi.holm at 5%. Compared: plan shares (the row's rates x reps), per family the
familywise count and each contrast's Holm count. Synthetic normals only; a scratch seed and replicate count, not the
settings' run. Usage: PY -B e2e_row_parity.py WS OPTION DESIGN STOPPED SIGMA_INDEX REPS SEED"""
import json, math, sys
from fractions import Fraction
sys.path.insert(0, sys.argv[1])
import numpy as np
from scripts.scale78b import sr2_simulation as sim
from scripts.scale78b import blinded_sigma as bs
from scripts.scale78b import noise_reading as nr
from scripts.stage1_s1.reading import contrast as con, phi

ws, option, design, stopped_txt, idx, reps, seed = sys.argv[1:8]
idx, reps, seed = int(idx), int(reps), int(seed)
stopped = sorted(s for s in stopped_txt.split(",") if s and s != "-")
s = json.loads(open(ws + "/scripts/scale78b/settings/sr2_simulation.json").read())
s.update(reps=reps, chunk=reps, seed=seed)
r = s["reml"]
s["_reml"] = {"tol": float(r["tol"]), "max_iter": int(r["max_iter"]), "clip": float(r["step_clip_log"]),
              "starts": r["starts"], "ll_tol": float(r["multi_start_ll_tolerance"])}
with np.errstate(all="ignore"):
    row = sim.simulate_row(idx, s, option, set(stopped))

z = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, 0]))).standard_normal((reps, 2, len(sim.CELLS)))
PLANS = {"A": dict(methods=("A1", "L1", "H1", "S1", "S3", "S4"), mseeds=range(1102, 1108), rseeds=range(1101, 1108),
                   a0_in=True, primary=("P1", "P2", "P3", "P4", "P5", "P6")),
         "B9": dict(methods=("A1", "H1", "S1", "S4"), mseeds=range(1102, 1111), rseeds=range(1101, 1111), a0_in=False,
                    primary=("P1", "P3", "P6")),
         "H": dict(methods=("A1", "H1", "S1", "S4"), mseeds=range(1102, 1114), rseeds=range(1101, 1114), a0_in=False,
                   primary=("P1", "P3", "P6"))}
CL = {"R": "removal", "A1": "removal", "L1": "removal", "H1": "removal", "a0": "full", "S1": "full", "S3": "full", "S4": "full"}
PAIRS = {"P1": ("R", "A1"), "P2": ("R", "L1"), "P3": ("R", "H1"), "P4": ("a0", "S1"), "P5": ("S1", "S3"), "P6": ("S1", "S4")}
FAMS = ("llama31-8b", "olmo2-7b")                    # the order of z's family axis (sim.FAMILIES, checked)
assert tuple(sim.FAMILIES) == FAMS
read = ("llama31-8b", "olmo2-7b") if option == "B" else ("olmo2-7b",)
grid = s["sigma_pair_pp"]
top = max(Fraction(g) for g in grid)
results = {}
all_equal = True
for sc in s["interaction"]:
    share = Fraction(sc["method_variance_share"])
    olmo = Fraction(grid[idx])
    true = {"olmo2-7b": olmo, "llama31-8b": min(olmo * Fraction(sc["llama_sigma_ratio"]), top)}
    y = {}
    for i, f in enumerate(FAMS):
        sd = np.array([float(true[f]) / math.sqrt(2) * (math.sqrt(1 + float(share)) if a not in ("a0", "R") else 1.0)
                       for a, _ in sim.CELLS])
        y[f] = z[:, i, :] * sd[None, :]
    plans = {k: 0 for k in sim.PLAN_LABELS}
    fw = {f: 0 for f in read}
    holm = {f: {} for f in read}
    for rr in range(reps):
        clusters = {}
        for f in read:
            for (a, j), c in bs.design_cells("anchor_stopped" if f in stopped else "full").items():
                clusters.setdefault(f"{f} {c}", {})[(a, j)] = Fraction(float(y[f][rr, sim.INDEX[(a, j)]]))
        sa, _ = bs.pooled_sigma(clusters)
        rule = nr.seed_rule(((Fraction(sa) ** 2,),), 0)
        plan = "review" if rule["review"] else rule["plan"]
        plans[plan] += 1
        if plan == "review":
            continue
        P = PLANS[plan]
        for f in read:
            st = f in stopped
            arms = [a for a in (("a0",) if P["a0_in"] else ()) + ("R",) + P["methods"] if not (st and a in ("A1", "L1", "S3"))]
            seeds = {a: (range(1101, 1108) if a == "a0" else P["rseeds"] if a == "R" else P["mseeds"]) for a in arms}
            table = {(a, j): np.array([float(y[f][rr, sim.INDEX[(a, j)]])]) for a in arms for j in seeds[a]}
            fits = {}
            for cname in ("removal", "full"):
                carms = tuple(a for a in arms if CL[a] == cname)
                if len(carms) < 2:
                    continue
                cells = [(a, j, float(table[(a, j)][0])) for a in carms for j in seeds[a]]
                if len(carms) == 2:
                    common = [j for j in seeds[carms[0]] if j in seeds[carms[1]]]
                    cells = [(a, j, v) for a, j, v in cells if j in common]
                fits[cname] = sim.REML.fit_cells(cells, carms, 0.01, multi_start=True)
            pv = {}
            for k in P["primary"]:
                c, m = PAIRS[k]
                if c in arms and m in arms:
                    common = [j for j in seeds[c] if j in seeds[m]]
                    pv[k] = con.contrast_fit(table, fits[CL[c]], c, m, common, 1.0, with_item=False).p_two_sided()
            rej = phi.holm(pv, 0.05)
            fw[f] += bool(rej)
            for k in rej:
                holm[f][k] = holm[f].get(k, 0) + 1
    got = row["scenarios"][sc["name"]]
    got_plans = {k: round(v * reps) if v is not None else 0 for k, v in got["plan_by_sigma_A"].items()}
    got_fw = {f: got["families"][f]["familywise_count"] for f in read}
    got_holm = {f: {k: v["holm_count"] for k, v in got["families"][f]["contrasts"].items() if v["holm_count"]} for f in read}
    printed = {f: Fraction(str(v)) for f, v in got["sigma_pair_pp_by_family"].items()}
    eq = got_plans == plans and got_fw == fw and got_holm == holm
    all_equal &= eq
    results[sc["name"]] = {"equal": eq, "true_sigma": {f: float(v) for f, v in true.items()},
                           "printed_sigma": {f: float(v) for f, v in printed.items()}, "plans": plans,
                           "plans_row": got_plans, "fw": fw, "fw_row": got_fw}
print(json.dumps({"args": sys.argv[2:], "all_equal": all_equal, "scenarios": results}))
