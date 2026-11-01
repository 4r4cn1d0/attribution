"""Synthetic only (fix round, track E-records). D-5's linearized table x = V + (u - V n) / Nbar:
(1) with V as a share, B16's own item_part equals an exact-fraction re-implementation of its formula on a hand case
    with unequal n; (2) with V in pp (the round-1 text), the estimate is unchanged but the item part is wrong by
    orders of magnitude; (3) when every n = 3 the two scales give the same x, so the all-n = 3 check cannot see it;
(4) on 2,000 random cells with unequal n: mean_p x = V exactly, n = 0 -> x = V, and B16's item_part matches the
    exact-fraction value to 1e-9 relative. B16's code is imported read-only from the repository root (argv[1])."""
import sys
from fractions import Fraction as F
import numpy as np
sys.path.insert(0, sys.argv[1])
from scripts.stage1_s1.reading import contrast as con

def x_exact(n, u, scale_v):
    N = sum(n); V = F(sum(u), N) * scale_v; nbar = F(N, len(n))
    return [V + (F(ui) - V * ni) / nbar for ni, ui in zip(n, u)]

def item_exact(rows, scale):
    """B16's item_part formula (contrast.py:99-122) in exact fractions: max(0, MS_P - MS_E) * scale^2 / (P J)."""
    J, P = len(rows), len(rows[0])
    grand = sum(sum(r) for r in rows) / (J * P)
    row = [sum(r) / P for r in rows]
    col = [sum(rows[j][p] for j in range(J)) / J for p in range(P)]
    ms_p = J * sum((c - grand) ** 2 for c in col) / (P - 1)
    ms_e = sum((rows[j][p] - row[j] - col[p] + grand) ** 2 for j in range(J) for p in range(P)) / ((P - 1) * (J - 1))
    return max(F(0), ms_p - ms_e) * F(scale) ** 2 / (P * J)

ok = True
# (1)-(2): the hand case of the verifier's D1 (two equal seeds), unequal n in the repair
n_c, u_c = [3, 3, 3, 3], [3, 3, 0, 0]
n_m, u_m = [0, 3, 3, 3], [0, 3, 0, 0]
for label, sv in (("V as a share", 1), ("V in pp (round-1 text)", 100)):
    d = [a - b for a, b in zip(x_exact(n_c, u_c, sv), x_exact(n_m, u_m, sv))]
    rows = [d, d]
    exact = item_exact(rows, 100)
    v_item, _ = con.item_part(np.array([[float(v) for v in d]] * 2), 100.0)
    est = 100 * sum(d) / len(d)
    print(f"{label}: estimate {float(est):.4f} pp; item part exact {float(exact):.4f} pp^2 ({exact}); B16 item_part {v_item:.4f}")
    if label == "V as a share":
        ok &= exact == F(27500, 81) and abs(v_item - float(exact)) <= 1e-9 * float(exact) and est == F(50, 3)
    else:
        ok &= float(exact) > 1e5 and est == F(50, 3)
# (3): every n = 3: both scales give x = u / 3
u3 = [3, 1, 0, 2]
same = x_exact([3] * 4, u3, 1) == x_exact([3] * 4, u3, 100) == [F(v, 3) for v in u3]
print("all n = 3: x identical under both scales and equal to u/3:", same)
ok &= same
# (4): random cells, unequal n, J = 3 seeds, P = 20 prompts
rng = np.random.default_rng(20261101)
worst = 0.0
for trial in range(2000):
    P = 20
    rows_c, rows_m = [], []
    for j in range(3):
        n1 = [int(v) for v in rng.integers(0, 4, size=P)]; n2 = [int(v) for v in rng.integers(0, 4, size=P)]
        if sum(n1) == 0 or sum(n2) == 0:
            n1[0] = n2[0] = 3
        u1 = [int(rng.integers(0, k + 1)) for k in n1]; u2 = [int(rng.integers(0, k + 1)) for k in n2]
        x1, x2 = x_exact(n1, u1, 1), x_exact(n2, u2, 1)
        V1, V2 = F(sum(u1), sum(n1)), F(sum(u2), sum(n2))
        if sum(x1) / P != V1 or sum(x2) / P != V2:
            ok = False
        if any(k == 0 and x != V1 for k, x in zip(n1, x1)):
            ok = False
        rows_c.append(x1); rows_m.append(x2)
    d = [[a - b for a, b in zip(rc, rm)] for rc, rm in zip(rows_c, rows_m)]
    exact = float(item_exact(d, 100))
    v_item, _ = con.item_part(np.array([[float(v) for v in r] for r in d]), 100.0)
    if exact > 0:
        worst = max(worst, abs(v_item - exact) / exact)
print(f"2,000 random cells (unequal n): mean_p x = V and n = 0 -> V exact; worst relative item-part gap {worst:.2e}")
ok &= worst <= 1e-9
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
