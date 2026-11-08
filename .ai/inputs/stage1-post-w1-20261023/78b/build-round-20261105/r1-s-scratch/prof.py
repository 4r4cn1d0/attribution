import sys, time
sys.path.insert(0, sys.argv[1])
import numpy as np
from scripts.scale78b import sr2_simulation as sim
d = sim.analysis_design("A", False)
cl = d["clusters"]["removal"]
rng = np.random.default_rng(1)
for reps in (200, 2000):
    y = rng.standard_normal((reps, len(cl["cells"]))) * 3
    for starts in ("pre-registered", "multi"):
        opts = {"tol": 1e-6, "max_iter": 25, "clip": 2.0, "starts": starts, "ll_tol": 1e-6}
        t = time.time()
        with np.errstate(all="ignore"):
            sim.reml_batch(cl, y, 0.01, opts)
        print(reps, starts, round(time.time() - t, 3))
t = time.time()
for i in range(20000):
    sim.TDIST.t_two_sided(1.3 + i * 1e-5, 5.5)
print("tdist 20000", round(time.time() - t, 3))
