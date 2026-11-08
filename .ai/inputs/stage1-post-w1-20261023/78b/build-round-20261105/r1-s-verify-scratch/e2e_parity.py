"""End-to-end, per-replicate check of sr2_simulation.run_chunk against an independent chain built from the frozen and
reference code: sigma_A by blinded_sigma.pooled_sigma (exact rationals), the plan by noise_reading.seed_rule, the claim
test by B16's fit_cells (multi-start, with the lone 1101 cells IN the fit as B16 reads them) and contrast_fit
(with_item False), Holm by B16's phi.holm. Synthetic normals only (a scratch seed); no settings file of the run is used.
Usage: PY -B e2e_parity.py WS OPTION DESIGN STOPPED SIGMA SHARE REPS"""
import json, math, sys, copy
from fractions import Fraction
sys.path.insert(0, sys.argv[1])
import numpy as np
from scripts.scale78b import sr2_simulation as sim
from scripts.scale78b import blinded_sigma as bs
from scripts.scale78b import noise_reading as nr
from scripts.stage1_s1.reading import contrast as con, phi

ws, option, design, stopped_txt, sigma_txt, share_txt, reps = sys.argv[1:8]
reps = int(reps)
stopped = set(s for s in stopped_txt.split(",") if s and s != "-")
s = json.loads(open(ws + "/scripts/scale78b/settings/sr2_simulation.json").read())
s["_reml"] = {"tol": 1e-6, "max_iter": 25, "clip": 2.0, "starts": "multi", "ll_tol": 1e-6}
sigma, share = float(sigma_txt), float(Fraction(share_txt))

rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([424242, 7])))
z = rng.standard_normal((reps, 2, len(sim.CELLS)))
eta = rng.standard_normal((reps, 2, 2, 3, 200))
designs = {(p, st): sim.analysis_design(p, st) for p in ("A", "B9", "H") for st in (False, True)}
fams = sim.OPTIONS[option]
allk = {f: [k for k in sim.CONTRASTS if any(k in designs[(p, f in stopped)]["contrasts"] for p in ("A", "B9", "H"))] for f in fams}
tallies = {f: sim.new_tally(allk[f], s["power_effects_pp"]) for f in fams}
plans = {"sigma_A": {k: 0 for k in sim.PLAN_LABELS}, "N": {k: 0 for k in sim.PLAN_LABELS}}
with np.errstate(all="ignore"):
    sim.run_chunk(z, eta, sigma, share, option, stopped, s, tallies, plans, designs)

# ----- the independent chain -----
sd = sim.cell_sd(sigma, share)
y_all = {f: z[:, i, :] * sd[None, :] for i, f in enumerate(sim.FAMILIES)}
PLANS = {"A": dict(methods=("A1", "L1", "H1", "S1", "S3", "S4"), mseeds=range(1102, 1108), rseeds=range(1101, 1108),
                   a0_in=True, primary=("P1", "P2", "P3", "P4", "P5", "P6")),
         "B9": dict(methods=("A1", "H1", "S1", "S4"), mseeds=range(1102, 1111), rseeds=range(1101, 1111), a0_in=False,
                    primary=("P1", "P3", "P6")),
         "H": dict(methods=("A1", "H1", "S1", "S4"), mseeds=range(1102, 1114), rseeds=range(1101, 1114), a0_in=False,
                   primary=("P1", "P3", "P6"))}
CL = {"R": "removal", "A1": "removal", "L1": "removal", "H1": "removal", "a0": "full", "S1": "full", "S3": "full", "S4": "full"}
PAIRS = {"P1": ("R", "A1"), "P2": ("R", "L1"), "P3": ("R", "H1"), "P4": ("a0", "S1"), "P5": ("S1", "S3"), "P6": ("S1", "S4")}
fw = {f: 0 for f in fams}
refused_mine = {f: 0 for f in fams}
holm_counts = {f: {k: 0 for k in allk[f]} for f in fams}
plan_counts = {k: 0 for k in sim.PLAN_LABELS}
for r in range(reps):
    clusters = {}
    for f in fams:
        dname = "anchor_stopped" if f in stopped else "full"
        for (a, j), c in bs.design_cells(dname).items():
            clusters.setdefault(f"{f} {c}", {})[(a, j)] = Fraction(float(y_all[f][r, sim.INDEX[(a, j)]]))
    sA, _ = bs.pooled_sigma(clusters)
    rule = nr.seed_rule(((Fraction(sA) ** 2,),), 0)
    plan = "review" if rule["review"] else rule["plan"]
    plan_counts[plan] += 1
    if plan == "review":
        continue
    P = PLANS[plan]
    for f in fams:
        st = f in stopped
        arms = [a for a in (("a0",) if P["a0_in"] else ()) + ("R",) + P["methods"] if not (st and a in ("A1", "L1", "S3"))]
        seeds = {a: (range(1101, 1108) if a == "a0" else P["rseeds"] if a == "R" else P["mseeds"]) for a in arms}
        table = {(a, j): np.array([float(y_all[f][r, sim.INDEX[(a, j)]])]) for a in arms for j in seeds[a]}
        fits = {}
        for cname in ("removal", "full"):
            carms = tuple(a for a in arms if CL[a] == cname)
            if len(carms) < 2:
                continue
            cells = [(a, j, float(table[(a, j)][0])) for a in carms for j in seeds[a]]
            if len(carms) == 2:      # B16's sum rule: the paired cells on the common seeds
                common = [j for j in seeds[carms[0]] if j in seeds[carms[1]]]
                cells = [(a, j, v) for a, j, v in cells if j in common]
            fits[cname] = sim.REML.fit_cells(cells, carms, 0.01, multi_start=True)
        pv = {}
        for k in P["primary"]:
            c, m = PAIRS[k]
            if c not in arms or m not in arms:
                continue
            common = [j for j in seeds[c] if j in seeds[m]]
            try:
                e = con.contrast_fit(table, fits[CL[c]], c, m, common, 1.0, with_item=False)
                pv[k] = e.p_two_sided()
            except Exception as exc:          # B16 refuses a contrast with no finite df; the simulation reads p = 1
                pv[k] = 1.0
                refused_mine[f] += 1
        rej = phi.holm(pv, 0.05)
        fw[f] += bool(rej)
        for k in rej:
            holm_counts[f][k] += 1
mine = {"plans": plan_counts, "familywise": fw, "holm": holm_counts, "refused": refused_mine}
theirs = {"plans": plans["sigma_A"], "familywise": {f: tallies[f]["familywise"] for f in fams},
          "holm": {f: {k: tallies[f]["contrasts"][k]["holm"] for k in allk[f]} for f in fams},
          "refused": {f: tallies[f]["refused"] for f in fams}, "nonconverged": {f: tallies[f]["nonconverged_fits"] for f in fams}}
print(json.dumps({"args": sys.argv[2:], "equal": mine["plans"] == theirs["plans"] and mine["familywise"] == theirs["familywise"]
                  and mine["holm"] == theirs["holm"], "independent": mine, "sr2_simulation": theirs}))
