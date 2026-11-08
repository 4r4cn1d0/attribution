"""Item 4: blinded_sigma.read (fix round) on the builder's synthetic fixture (three engine roles, split identities
too) against an independent exact computation: per complete arm x seed table at 1102-1104 the two-way interaction
sum of squares (y - row mean - column mean + grand mean)^2, df (a-1)(s-1); lone cells (R@1101, R@1105, a0@1101) left
out (leverage 1); pooled over clusters and families; sqrt(2 x RSS / df). Also a second, different algorithm: the
additive fit by backfitting (alternating arm and seed means, exact rationals, to convergence) on ALL design cells
including the lone ones. Usage: PY -B indep_sigma2.py WS SCRATCH"""
import json, math, pathlib, sys
from fractions import Fraction as F
ws, tmp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
sys.path.insert(0, str(ws))
from scripts.scale78b.tests import test_blinded_sigma as T
from scripts.scale78b import blinded_sigma as bs

root = tmp / "fx"
fams = {f: T.build_family(root, f) for f in ("olmo2-7b", "llama31-8b")}
stopped = T.build_family(root / "stopped", "olmo2-7b", "anchor_stopped")
for by_seed in stopped["cells"].values():
    for e in by_seed.values():
        e["path"] = "stopped/" + e["path"]
stopped["anchor_stop"] = T.write_stop_record(root, "stopped/anchor-stop.json", "olmo2-7b")
llama_stopped = T.build_family(root / "lstopped", "llama31-8b", "anchor_stopped", engines=T.ENGINES_SPLIT)
for by_seed in llama_stopped["cells"].values():
    for e in by_seed.values():
        e["path"] = "lstopped/" + e["path"]
llama_stopped["anchor_stop"] = T.write_stop_record(root, "lstopped/anchor-stop.json", "llama31-8b",
                                                   "harmful_prompt_does_not_encode", 1)


def u(fam, a, j):
    return F(100 * T.unsafe_count(fam, a, j), 60)


def interaction(fam, design):
    rss, df = F(0), 0
    rem = ("R", "A1", "L1", "H1") if design == "full" else ("R", "H1")
    full = ("a0", "S1", "S3", "S4") if design == "full" else ("a0", "S1", "S4")
    seeds = (1102, 1103, 1104)
    for arms in (rem, full):
        y = {(a, j): u(fam, a, j) for a in arms for j in seeds}
        g = sum(y.values()) / len(y)
        ma = {a: sum(y[(a, j)] for j in seeds) / 3 for a in arms}
        mj = {j: sum(y[(a, j)] for a in arms) / len(arms) for j in seeds}
        rss += sum((y[(a, j)] - ma[a] - mj[j] + g) ** 2 for a in arms for j in seeds)
        df += (len(arms) - 1) * 2
    return rss, df


def backfit(fam, design):
    """Additive arm + seed fit by alternating means (floats, many sweeps) on every design cell, lone ones included."""
    rss, df = 0.0, 0
    for cluster in ("removal", "full"):
        cells = [c for c, cl in bs.design_cells(design).items() if cl == cluster]
        y = {c: float(u(fam, *c)) for c in cells}
        arms, seeds = sorted({a for a, _ in cells}), sorted({j for _, j in cells})
        alpha, beta = {a: 0.0 for a in arms}, {j: 0.0 for j in seeds}
        for _ in range(3000):
            for j in seeds:
                cs = [c for c in cells if c[1] == j]
                beta[j] = sum(y[c] - alpha[c[0]] for c in cs) / len(cs)
            for a in arms:
                cs = [c for c in cells if c[0] == a]
                alpha[a] = sum(y[c] - beta[c[1]] for c in cs) / len(cs)
        rss += sum((y[c] - alpha[c[0]] - beta[c[1]]) ** 2 for c in cells)
        df += len(cells) - (len(arms) + len(seeds) - 1)
    return rss, df


cases = {"[B] full": ("B", {"olmo2-7b": (fams["olmo2-7b"], "full"), "llama31-8b": (fams["llama31-8b"], "full")}),
         "[C] full": ("C", {"olmo2-7b": (fams["olmo2-7b"], "full")}),
         "[C] stopped": ("C", {"olmo2-7b": (stopped, "anchor_stopped")}),
         "[B] olmo stopped": ("B", {"olmo2-7b": (stopped, "anchor_stopped"), "llama31-8b": (fams["llama31-8b"], "full")}),
         "[B] llama stopped (split engines, harmful stop)": ("B", {"olmo2-7b": (fams["olmo2-7b"], "full"),
                                                                   "llama31-8b": (llama_stopped, "anchor_stopped")})}
for label, (option, spec) in cases.items():
    inputs, digest = T.write_inputs(root, option, {f: s for f, (s, _) in spec.items()}, f"inputs-{len(label)}-{option}.json")
    doc = bs.read(inputs, digest)
    rss, df = F(0), 0
    brss, bdf = 0.0, 0
    for f, (_, d) in spec.items():
        a, b = interaction(f, d)
        rss += a; df += b
        c, e = backfit(f, d)
        brss += c; bdf += e
    ind = math.sqrt(2 * float(rss / df))
    bf = math.sqrt(2 * brss / bdf)
    print(json.dumps({"case": label, "blinded_sigma": repr(doc["sigma_A_pp"]), "df": doc["df"], "independent": repr(ind),
                      "independent_df": df, "exact_equal": repr(ind) == repr(doc["sigma_A_pp"]) and df == doc["df"],
                      "backfit": repr(bf), "backfit_df": bdf, "backfit_rel_diff": abs(bf - doc["sigma_A_pp"]) / doc["sigma_A_pp"]}))
