"""Synthetic only: D-5's linearized table with V as a share (V1A:209-211) against V in pp (E-D5-D6.md item 1's
'V(a,j) = 100 x ...' fed into item 2's formula), through B16's own item_part."""
import sys
import numpy as np
sys.path.insert(0, sys.argv[1])
from scripts.stage1_s1.reading import contrast as con

def x_of(n, u, scale_v):
    n, u = np.asarray(n, float), np.asarray(u, float)
    v_share = u.sum() / n.sum()
    v = v_share * scale_v
    nbar = n.sum() / len(n)
    return v + (u - v * n) / nbar

# comparator: every prompt coherent; repair: prompt 1's answers all fail the screen; two seeds
n_c, u_c = [3, 3, 3, 3], [3, 3, 0, 0]
n_m, u_m = [0, 3, 3, 3], [0, 3, 0, 0]
for label, sv in (("V as a share (V1A)", 1.0), ("V in pp (item 1 fed into item 2)", 100.0)):
    xc, xm = x_of(n_c, u_c, sv), x_of(n_m, u_m, sv)
    d = np.array([xc - xm, xc - xm])
    v_item, _ = con.item_part(d, 100.0)
    print(f"{label}: x(m) = {np.round(xm, 4).tolist()}, estimate {100 * d.mean():.3f} pp, item part {v_item:.1f} pp^2")
