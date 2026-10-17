#!/usr/bin/env python3
"""verify_crosscluster.py: HB's seed part for a contrast that CROSSES the two design clusters (A1 against S1, as a
removal arm against an a0-like arm in a section D.2 reference fit), under the two-cluster structure of verify_hbc.py
(shared 0.3, each cluster 0.4, arm-specific 0.3 of a 2.65 pp per-arm SD), and under exact additivity (rho 0.7).
One-sided 5% test, the reference-test level. Compared: HB (the draft's fit on all 8 arms) and (b0) the pair's own
paired t on the 6 common seeds. Planning simulation only. Writes verify_crosscluster_out.txt."""
import importlib.util, math, pathlib
import numpy as np
HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s1m", HERE / "rerun" / "stage1_model_sim.py"); S1M = importlib.util.module_from_spec(spec); spec.loader.exec_module(S1M)
W = S1M.W; ARMS = S1M.ARMS; d = S1M.D0; v = 2.65 ** 2
a, b = ARMS.index("A1"), ARMS.index("S1")
common = sorted(set(d.arm_seeds["A1"]) & set(d.arm_seeds["S1"]))
ia = [d.cells.index((a, d.seeds.index(s))) for s in common]; ib = [d.cells.index((b, d.seeds.index(s))) for s in common]
out = []
for name, s_share, clusters in (("additive rho 0.7", 0.7, []),
                                ("two clusters (shared 0.3, 0.4 each)", 0.3, [({"a0", "S1", "S3", "S4"}, 0.4), ({"R", "A1", "L1", "H1"}, 0.4)])):
    rng = np.random.default_rng(777)
    rh, rb, se_r, sds = [], [], [], []
    for _ in range(40):
        B = 500
        U = (rng.standard_normal((B, len(d.seeds))) * math.sqrt(s_share * v))[:, d.cell_seed]
        used = np.zeros(8)
        for mem, sh in clusters:
            cm = rng.standard_normal((B, len(d.seeds))) * math.sqrt(sh * v)
            mask = np.array([ARMS[x] in mem for x in d.cell_arm]); U[:, mask] += cm[:, d.cell_seed[mask]]
            for x in mem: used[ARMS.index(x)] += sh
        U = U + rng.standard_normal((B, d.nc)) * np.sqrt(np.maximum(1 - s_share - used, 0) * v)[d.cell_arm][None, :]
        th, vth = S1M.reml_hetero(d, U)
        dd = U[:, ia] - U[:, ib]; J = len(common)
        vs = (th[:, a] + th[:, b]) / J; dfs = 2 * vs ** 2 / np.maximum((vth[:, a, a] + vth[:, b, b] + 2 * vth[:, a, b]) / J ** 2, 1e-300)
        rh.append(W.t_sf(dd.mean(1) / np.sqrt(vs), dfs) < 0.05)
        rb.append(W.t_sf(dd.mean(1) / (dd.std(1, ddof=1) / math.sqrt(J)), J - 1) < 0.05)
        se_r.append(np.sqrt(vs)); sds.append(dd.mean(1))
    se_r, sds = np.concatenate(se_r), np.concatenate(sds)
    line = (f"{name}: one-sided 5% rejection, A1 vs S1 (cross-cluster): HB {np.concatenate(rh).mean() * 100:.2f}% | "
            f"(b0) paired own-variance {np.concatenate(rb).mean() * 100:.2f}% | HB SE/SD {math.sqrt((se_r ** 2).mean()) / sds.std():.2f} (20,000 replicates)")
    out.append(line); print(line, flush=True)
(HERE / "verify_crosscluster_out.txt").write_text("\n".join(out) + "\n")
