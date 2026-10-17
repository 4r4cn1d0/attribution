"""Sanity check: the graph routine reproduces Holm on a Holm graph, and weights never exceed 1 on the proposed graph."""
import numpy as np, importlib.util, pathlib
spec = importlib.util.spec_from_file_location("a", pathlib.Path(__file__).with_name("w3_w4_w12_w13_analysis.py"))
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
rng = np.random.default_rng(1)
m = 6
w = np.full(m, 1 / m); G = (np.ones((m, m)) - np.eye(m)) / (m - 1)
bad = 0
for _ in range(20000):
    p = rng.uniform(0, 0.06, m) ** rng.uniform(0.5, 2)
    if not np.array_equal(a.graph_test(p, w, G, 0.05), a.holm(p[None, :], 0.05)[0]):
        bad += 1
print("Holm mismatches out of 20000:", bad)
w0, G0 = a.graph_spec(0.1)
print("row sums of proposed G:", sorted(set(np.round(G0.sum(1), 12))), "initial weight sum:", round(w0.sum(), 12))
# a hand case: U_1 rejected at alpha*0.15 -> O_1, L_1 each get 0.25*0.15
p = np.ones(18); p[0] = 0.001; p[6] = 0.05 * (0.1 / 12 + 0.25 * 0.15) * 0.999
r = a.graph_test(p, w0, G0, 0.05)
print("hand case U1 then O1 rejected:", bool(r[0]), bool(r[6]), "others:", int(r.sum()) - 2)
