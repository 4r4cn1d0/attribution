"""Smoke probe (not the SR-2 reading): the familywise rate per family when the two families' true sigma_pair differ
under option B, with sr2_simulation's own functions (the plan from the pooled sigma_A, the claim test, Holm). A scratch
seed; the committed settings file is read for its constants only (rule, reml, alpha, floor), never run.
Usage: PY -B unequal_sigma.py WS REPS SIGMA_OLMO RATIO[,RATIO...] [SHARE]"""
import json, sys
sys.path.insert(0, sys.argv[1])
import numpy as np
from scripts.scale78b import sr2_simulation as sim

ws, reps, s_olmo, ratios = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), [float(x) for x in sys.argv[4].split(",")]
share = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
s = json.loads(open(ws + "/scripts/scale78b/settings/sr2_simulation.json").read())
s["_reml"] = {"tol": 1e-6, "max_iter": 25, "clip": 2.0, "starts": "multi", "ll_tol": 1e-6}
designs = {(p, st): sim.analysis_design(p, st) for p in ("A", "B9", "H") for st in (False, True)}
rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([999001, 3])))
z = rng.standard_normal((reps, 2, len(sim.CELLS)))
out = {}
with np.errstate(all="ignore"):
    for ratio in ratios:
        sig = {"olmo2-7b": s_olmo, "llama31-8b": s_olmo * ratio}
        y_all = {f: z[:, i, :] * sim.cell_sd(sig[f], share)[None, :] for i, f in enumerate(sim.FAMILIES)}
        rows = {}
        for option in ("B", "C"):
            a_plan = sim.plan_of(sim.sigma_a_sq(y_all, option, set())[0], s)
            fw = {f: 0 for f in sim.OPTIONS[option]}
            for plan in ("A", "B9", "H"):
                idx = np.nonzero(a_plan == plan)[0]
                if idx.size == 0:
                    continue
                for f in sim.OPTIONS[option]:
                    d = designs[(plan, False)]
                    res = sim.claim_test(d, y_all[f][idx], s)
                    p = np.stack([res["contrasts"][k]["p"] for k in d["contrasts"]], axis=1)
                    fw[f] += int(sim.holm(p, 0.05).any(axis=1).sum())
            rows[option] = {"familywise": {f: round(v / reps, 4) for f, v in fw.items()},
                            "plan_A_share": round(float((a_plan == "A").mean()), 4)}
        out[f"ratio {ratio}"] = rows
print(json.dumps({"reps": reps, "sigma_olmo": s_olmo, "share": share, "rows": out}))
