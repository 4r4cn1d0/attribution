"""S-2 check: B16's Phi (scripts/stage1_s1/reading/phi.py, unchanged) never rejects a U node unless Holm on the U
p-values alone rejects at least one (min p_U <= alpha/K); also counts how often Phi's U rejections are a subset of
Holm's. Random and adversarial p-values (O, L, F nodes near 0 so they reject first). Run from WS with -B."""
import random, sys
from fractions import Fraction as Fr
sys.path.insert(0, sys.argv[1])
from scripts.stage1_s1.reading import phi

ALPHA = 0.05
rng = random.Random(20261108)
names = {6: ["P1", "P2", "P3", "P4", "P5", "P6"], 3: ["P1", "P3", "P6"], 2: ["P3", "P6"]}
bad_first = bad_subset = total = any_u = 0
max_u_level_before_u = {}
for k, contrasts in names.items():
    g = phi.build_graph(contrasts)
    for trial in range(4000):
        p = {}
        mode = trial % 4
        for c in contrasts:
            if mode == 0:      # uniform everything
                p[("U", c)] = rng.random()
            else:              # U just above / around alpha/K, below alpha
                p[("U", c)] = rng.uniform(0.2 * ALPHA / k, 1.5 * ALPHA)
            for kind in ("O", "L", "F"):
                p[(kind, c)] = 0.0 if mode in (1, 2) and rng.random() < 0.8 else rng.random() * (0.001 if mode == 3 else 1)
        out = phi.run(g, p, Fr(1, 20))
        u_rej = {n[1] for n in out.rejected if n[0] == "U"}
        u_p = {c: p[("U", c)] for c in contrasts}
        holm = phi.holm(u_p, ALPHA)
        total += 1
        if u_rej:
            any_u += 1
            # the first U rejection's level
            first_u = next(n for n in out.rejected if n[0] == "U")
            lvl = out.level_at_rejection[first_u]
            max_u_level_before_u[k] = max(max_u_level_before_u.get(k, Fr(0)), lvl)
            if not holm:
                bad_first += 1
            if not u_rej <= holm:
                bad_subset += 1
print({"trials": total, "phi_rejects_some_U": any_u, "phi_U_but_holm_none": bad_first,
       "phi_U_not_subset_of_holm": bad_subset,
       "max_level_of_first_U_rejection_over_alpha_over_K": {k: float(v / (Fr(1, 20) / k)) for k, v in max_u_level_before_u.items()}})
