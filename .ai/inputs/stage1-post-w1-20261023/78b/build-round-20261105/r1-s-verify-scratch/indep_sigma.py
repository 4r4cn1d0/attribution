"""Independent sigma_A on the builder's fixture: the two-way (arm x seed) interaction sum of squares of each cluster's
complete table (lone cells dropped: they have leverage 1), exact rationals; pooled over clusters and families; x sqrt 2.
The planted counts come from the test module's unsafe_count (k / 60). Usage: PY -B indep_sigma.py WS"""
import math, sys
from fractions import Fraction as F
sys.path.insert(0, sys.argv[1])
from scripts.scale78b.tests.test_blinded_sigma import unsafe_count

def table_ss(arms, seeds, fam):
    y = {(a, j): F(100 * unsafe_count(fam, a, j), 60) for a in arms for j in seeds}
    g = sum(y.values()) / len(y)
    ma = {a: sum(y[(a, j)] for j in seeds) / len(seeds) for a in arms}
    mj = {j: sum(y[(a, j)] for a in arms) / len(arms) for j in seeds}
    return sum((y[(a, j)] - ma[a] - mj[j] + g) ** 2 for a in arms for j in seeds), (len(arms) - 1) * (len(seeds) - 1)

out = {}
for label, designs in (("B full", {"olmo2-7b": "full", "llama31-8b": "full"}), ("C full", {"olmo2-7b": "full"}),
                       ("C stopped", {"olmo2-7b": "stopped"}), ("B one stopped", {"olmo2-7b": "stopped", "llama31-8b": "full"})):
    rss, df = F(0), 0
    for fam, d in designs.items():
        rem = ("R", "A1", "L1", "H1") if d == "full" else ("R", "H1")
        full = ("a0", "S1", "S3", "S4") if d == "full" else ("a0", "S1", "S4")
        for arms in (rem, full):
            ss, k = table_ss(arms, (1102, 1103, 1104), fam)
            rss += ss; df += k
    out[label] = (repr(math.sqrt(2 * float(rss / df))), df)
print(out)
