#!/usr/bin/env python3
"""verify_floor.py: how often the draft's REML (reml_hetero, read-only) puts an arm variance at its 0.01 pp^2 floor,
and what HB's seed-part test does in those replicates. Cell-level normal data, design D0, equal arm SDs (2.65 pp,
shared-shift share 0.5 and 0). Planning simulation only. Writes verify_floor_out.txt."""
import importlib.util, math, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s1m", HERE / "rerun" / "stage1_model_sim.py")
S1M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S1M)
W = S1M.W
OUT = []


def say(s):
    print(s, flush=True)
    OUT.append(s)


d = S1M.D0
v = 2.65 ** 2
for share in (0.0, 0.5):
    rng = np.random.default_rng(31337 + int(share * 10))
    reps, B = 20000, 500
    floor_any, floor_arm, rej_floor, rej_nofloor, n_floor_c, n_nofloor_c = 0, np.zeros(8), 0, 0, 0, 0
    conv_fail = 0
    for _ in range(reps // B):
        U = (rng.standard_normal((B, len(d.seeds))) * math.sqrt(share * v))[:, d.cell_seed]
        U = U + rng.standard_normal((B, d.nc)) * math.sqrt((1 - share) * v)
        th, vth = S1M.reml_hetero(d, U)
        atf = th <= 1.0001e-2
        floor_any += int(atf.any(1).sum())
        floor_arm += atf.sum(0)
        for ci, c in enumerate(d.con):
            a, b, J = c["a"], c["b"], c["J"]
            dd = U[:, c["ia"]] - U[:, c["ib"]]
            vs = (th[:, a] + th[:, b]) / J
            var_vs = (vth[:, a, a] + vth[:, b, b] + 2 * vth[:, a, b]) / J ** 2
            df = 2 * vs ** 2 / np.maximum(var_vs, 1e-300)
            p = W.t_p2(dd.mean(1) / np.sqrt(vs), df)
            fl = atf[:, a] | atf[:, b]
            rej = p < 0.05 / 6
            rej_floor += int((rej & fl).sum()); n_floor_c += int(fl.sum())
            rej_nofloor += int((rej & ~fl).sum()); n_nofloor_c += int((~fl).sum())
    say(f"shared-shift share {share}: replicates with >= 1 arm at the floor {floor_any / reps * 100:.1f}%; "
        f"arm-fits at the floor {floor_arm.sum() / (8 * reps) * 100:.2f}% (by arm " + ", ".join(
            f"{a} {x / reps * 100:.1f}" for a, x in zip(S1M.ARMS, floor_arm)) + "); "
        f"per-contrast rejection at a/6 when a contrast arm is at the floor {rej_floor / max(n_floor_c, 1) * 100:.2f}% "
        f"(n {n_floor_c}), otherwise {rej_nofloor / max(n_nofloor_c, 1) * 100:.2f}%")
(HERE / "verify_floor_out.txt").write_text("\n".join(OUT) + "\n")
