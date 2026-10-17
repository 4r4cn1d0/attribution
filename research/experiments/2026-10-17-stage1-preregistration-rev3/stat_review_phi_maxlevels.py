#!/usr/bin/env python3
"""stat_review_phi_maxlevels.py: the largest local level each node type of the in-force Phi can reach, given that
F_k and O_k can never both be rejected (p_F + p_theta0 = 1 on one estimate and SE). For node X_1, every other node
that can be rejected is rejected (all other U, all L, and per contrast either F_k or O_k), maximised over the 2^6
choices. Also the alpha held by O_k after U_k and F_k (and L_k) are rejected (a node that can then never reject).
Uses the graph and update routine of stat_review_phi_iut.py (same folder). No data input.
Run: <venv python> -I -B stat_review_phi_maxlevels.py"""
import importlib.util, itertools, pathlib, sys
import numpy as np
import warnings
warnings.filterwarnings("ignore")
sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("phi", HERE / "stat_review_phi_iut.py"); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
K = 6
out = []
for r13, lab in ((True, "in force (F->L 1)"), (False, "standard edge (F->O 1/2, L 1/2)")):
    w0, G0 = m.to_np(*m.graph(6, r13))
    for target in ("U", "O", "L", "F"):
        idx = {"U": 0, "O": K, "L": 2 * K, "F": 3 * K}[target]
        mx, arg = 0.0, None
        for choice in itertools.product((0, 1), repeat=K):          # 0: F_k rejected, 1: O_k rejected
            if target == "O" and choice[0] == 0:
                continue
            if target == "F" and choice[0] == 1:
                continue
            rejset = []
            for k in range(K):
                if not (target == "U" and k == 0): rejset.append(k)
                if not (target == "L" and k == 0): rejset.append(2 * K + k)
                if choice[k] == 0 and not (target == "F" and k == 0): rejset.append(3 * K + k)
                if choice[k] == 1 and not (target == "O" and k == 0): rejset.append(K + k)
            w, G = w0.copy(), G0.copy(); act = np.ones(4 * K, bool)
            for i in rejset:
                w, G = m.update_scalar(w, G, i, act); act[i] = False
            if w[idx] > mx:
                mx, arg = w[idx], choice
        out.append(f"{lab}: max reachable level of {target}_1 = {mx * 5:.3f}% (per contrast F=0 / O=1 rejected: {arg})")
    w, G = w0.copy(), G0.copy(); act = np.ones(4 * K, bool)
    for i in (0, 3 * K):
        w, G = m.update_scalar(w, G, i, act); act[i] = False
    a = w[K] * 5
    w, G = m.update_scalar(w, G, 2 * K, act); act[2 * K] = False
    out.append(f"{lab}: O_1's level after U_1, F_1: {a:.3f}%; after U_1, F_1, L_1: {w[K] * 5:.3f}% (O_1 cannot reject once F_1 is rejected)")
print("\n".join(out))
(HERE / "stat_review_phi_maxlevels_out.txt").write_text("\n".join(out) + "\n")

# realistic sequences: the level of U_1 when other contrasts are rejected in common patterns
seqs = {
    "U_2..U_6 rejected": [1, 2, 3, 4, 5],
    "U_2..U_6 and F_2..F_6 rejected (five better, feasible repairs)": [1, 2, 3, 4, 5] + [3 * K + k for k in range(1, 6)],
    "U_2..U_6, F_2..F_6 and L_2..L_6 rejected": [1, 2, 3, 4, 5] + [3 * K + k for k in range(1, 6)] + [2 * K + k for k in range(1, 6)],
    "U_2..U_6 and O_2..O_6, L_2..L_6 rejected (five better repairs, all worse on O and L)": [1, 2, 3, 4, 5] + [K + k for k in range(1, 6)] + [2 * K + k for k in range(1, 6)],
}
w0, G0 = m.to_np(*m.graph(6, True))
extra = []
for nm, seq in seqs.items():
    w, G = w0.copy(), G0.copy(); act = np.ones(4 * K, bool)
    for i in seq:
        w, G = m.update_scalar(w, G, i, act); act[i] = False
    extra.append(f"in force: {nm}: U_1 level {w[0] * 5:.3f}% (Holm over the six U alone would give 5%)")
print("\n".join(extra))
(HERE / "stat_review_phi_maxlevels_out.txt").write_text("\n".join(out + extra) + "\n")
