"""Smoke probe (not the SR-2 reading): the familywise rate under option C when the extra arm x seed variance sits on
other arms than the settings' form (all six method arms): none; all methods (share 1, the settings' form); A1 and S3
only (share 3: the same total extra variance per cluster as share 1 on three method arms); R and a0 only (share 1).
sr2_simulation's own functions; scratch seed; CRN over the forms. Usage: PY -B arm_shape.py WS REPS SIGMA"""
import json, math, sys
sys.path.insert(0, sys.argv[1])
import numpy as np
from scripts.scale78b import sr2_simulation as sim

ws, reps, sigma = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
s = json.loads(open(ws + "/scripts/scale78b/settings/sr2_simulation.json").read())
s["_reml"] = {"tol": 1e-6, "max_iter": 25, "clip": 2.0, "starts": "multi", "ll_tol": 1e-6}
designs = {(p, st): sim.analysis_design(p, st) for p in ("A", "B9", "H") for st in (False, True)}
rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([999002, 5])))
z = rng.standard_normal((reps, 2, len(sim.CELLS)))
forms = {"none": {}, "methods share 1": {a: 1.0 for a in sim.METHODS}, "A1 and S3 share 3": {"A1": 3.0, "S3": 3.0},
         "R and a0 share 1": {"R": 1.0, "a0": 1.0}}
out = {}
with np.errstate(all="ignore"):
    for name, extra in forms.items():
        sd = np.array([sigma / math.sqrt(2) * math.sqrt(1 + extra.get(a, 0.0)) for a, _ in sim.CELLS])
        y_all = {f: z[:, i, :] * sd[None, :] for i, f in enumerate(sim.FAMILIES)}
        a_plan = sim.plan_of(sim.sigma_a_sq(y_all, "C", set())[0], s)
        fw = 0
        for plan in ("A", "B9", "H"):
            idx = np.nonzero(a_plan == plan)[0]
            if idx.size:
                d = designs[(plan, False)]
                res = sim.claim_test(d, y_all["olmo2-7b"][idx], s)
                p = np.stack([res["contrasts"][k]["p"] for k in d["contrasts"]], axis=1)
                fw += int(sim.holm(p, 0.05).any(axis=1).sum())
        out[name] = {"familywise": round(fw / reps, 4), "plans": {k: round(float((a_plan == k).mean()), 3) for k in sim.PLAN_LABELS}}
print(json.dumps({"reps": reps, "sigma": sigma, "forms": out}))
