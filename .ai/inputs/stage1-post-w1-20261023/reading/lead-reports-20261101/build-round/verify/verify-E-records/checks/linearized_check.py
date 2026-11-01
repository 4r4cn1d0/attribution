"""Synthetic-only check of D-5's linearized table claims (E-D5-D6.md section 1 items 2 and the V1A hand case),
using B16's own item_part / satterthwaite_df / contrast_paired from the repository code (read-only import)."""
import sys
from fractions import Fraction
import numpy as np
sys.path.insert(0, sys.argv[1])           # the repository root (code only)
from scripts.stage1_s1.reading import contrast as con

def x_table(n, u):
    """n, u: arrays (P,) of coherent answers and coherent Unsafe answers; returns x (P,) as exact Fractions."""
    P = len(n)
    N = sum(n); V = Fraction(sum(u), N)
    Nbar = Fraction(N, P)
    return [V + (Fraction(ui) - V * ni) / Nbar for ni, ui in zip(n, u)], V

rng = np.random.default_rng(20261101)
ok = True
# 1. mean_p x == V exactly; prompts with n = 0 get x = V; all n = 3 gives x = u/3
for trial in range(2000):
    P = int(rng.integers(2, 40))
    n = [int(v) for v in rng.integers(0, 4, size=P)]
    if sum(n) == 0:
        continue
    u = [int(rng.integers(0, ni + 1)) for ni in n]
    x, V = x_table(n, u)
    if sum(x) / P != V:
        ok = False; print("mean != V", n, u); break
    for ni, xi in zip(n, x):
        if ni == 0 and xi != V:
            ok = False; print("n=0 prompt not V"); break
    n3 = [3] * P
    x3, _ = x_table(n3, u if max(u) <= 3 else u)
    if any(xi != Fraction(ui, 3) for xi, ui in zip(x3, u)):
        ok = False; print("n=3 identity fails"); break
print("identities (2000 random cells): mean_p x = V, n=0 -> V, n=3 -> u/3:", ok)

# 2. the hand case (V1A:165-177): 4 prompts, 2 seeds
xc, Vc = x_table([3, 3, 3, 3], [3, 0, 0, 0])
xm, Vm = x_table([0, 3, 3, 3], [0, 0, 0, 0])
d = np.array([[float(a - b) for a, b in zip(xc, xm)]] * 2)
v_item, q = con.item_part(d, 100.0)
print("hand case: x(c) =", [str(v) for v in xc], "x(m) =", [str(v) for v in xm], "V(c), V(m) =", Vc, Vm)
print("hand case: estimate pp =", 100 * float(np.mean(d)), "V_item pp^2 =", v_item, "SE_item pp =", v_item ** 0.5)
# the design's prompt part: prompt 1 dropped; matched per-prompt shares on prompts 2-4 are all 0 -> 0
dd = np.zeros((2, 3))
print("design's prompt part on the kept prompts (pp^2):", con.item_part(dd, 100.0)[0])

# 3. Lambda_plant step size: three-seed mean of differences of 600-answer shares, in pp
steps = {Fraction(100 * (a - b), 600) for a in range(0, 601, 37) for b in range(0, 601, 41)}
g = Fraction(0)
from math import gcd
den = 1
for s in steps:
    den = den * s.denominator // gcd(den, s.denominator)
print("per-seed difference grid denominator (pp):", den, "-> three-seed mean grid 1 /", den * 3, "pp")
# can 5 and 10 be hit exactly? 5 = 90/18, 10 = 180/18
print("5 pp and 10 pp on the 1/18 grid:", Fraction(5) * 18 == int(Fraction(5) * 18), Fraction(10) * 18 == 180)
# float rounding: a three-seed paired mean that is exactly 10 as a rational, computed as B16's contrast_paired does
table = {}
hits = 0; below = 0
for trial in range(20000):
    a = rng.integers(200, 400, size=3)
    # choose b so the exact mean difference is 10 pp: sum(a - b) = 3 * 10 * 6 = 180 answers
    k = rng.integers(0, 61, size=2)
    diff = [int(k[0]), int(k[1]), 180 - int(k[0]) - int(k[1])]
    b = [int(a[i]) - diff[i] for i in range(3)]
    if min(b) < 0:
        continue
    vals_c = np.array([100.0 * int(a[i]) / 600.0 for i in range(3)])
    vals_m = np.array([100.0 * b[i] / 600.0 for i in range(3)])
    est = float((vals_c - vals_m).mean())
    hits += 1
    below += est < 10.0
print("exact-10 pp paired means computed in float: %d of %d land below 10.0" % (below, hits))
print("PASS" if ok else "FAIL")
