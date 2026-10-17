#!/usr/bin/env python3
"""verify_fboundary.py: 400,000-replicate re-check of verify_extra.py C2's last configuration (U, O, L all false;
the six F nodes true at their boundary), whose 20,000-replicate value (5.21%, MC SE 0.16) sat above 5%.
Same graph, same correlations, same shortcut. Writes verify_fboundary_out.txt."""
import importlib.util, itertools, math, pathlib
import numpy as np
HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v", HERE / "verify_extra.py"); V = importlib.util.module_from_spec(spec); spec.loader.exec_module(V)
w0, G0 = V.graph_spec(0.1, 6); K = 6
C = np.eye(24)
for a, b in itertools.combinations(range(3), 2): C[a, b] = C[b, a] = 0.5
C[4, 5] = C[5, 4] = 0.5; C[3, 4] = C[4, 3] = C[3, 5] = C[5, 3] = -0.5
for k in range(K):
    for a, b in itertools.combinations([k, K + k, 2 * K + k, 3 * K + k], 2): C[a, b] = C[b, a] = 0.3
L = np.linalg.cholesky(C)
nsf = lambda x: 0.5 * np.vectorize(math.erfc)(x / math.sqrt(2))
out = []
for seed in (11, 12):
    n = 200000
    z = np.random.default_rng(seed).standard_normal((n, 24)) @ L.T
    z[:, :18] += 6.0
    p = np.empty_like(z); p[:, :K] = 2 * nsf(np.abs(z[:, :K])); p[:, K:] = nsf(z[:, K:])
    fw = sum(int(V.shortcut(p[i], w0, G0)[18:].any()) for i in range(n) if (p[i, 18:] <= 0.05).any())
    out.append(f"seed {seed}: FWER {fw / n * 100:.3f}% (n {n}; MC SE {math.sqrt(0.049 * 0.951 / n) * 100:.3f}); Bonferroni bound 5%, independent-F value 4.897%")
    print(out[-1], flush=True)
(HERE / "verify_fboundary_out.txt").write_text("\n".join(out) + "\n")
