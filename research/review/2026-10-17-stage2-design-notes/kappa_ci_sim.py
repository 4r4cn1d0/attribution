"""Simulated 95% CI half-width of Cohen's kappa for a two-rater blind read (planning only; no data)."""
import numpy as np

rng = np.random.default_rng(20261017)

# Latent human class distribution by judge stratum (I: from the 9 Oct read's counts, 5/21/13 of 39 Unsafe; 10/0/0 Safe).
STRATA = {
    "unsafe": np.array([0.13, 0.54, 0.33]),
    "safe": np.array([0.94, 0.05, 0.01]),
}


def rater(true, q):
    """Each rater reports the true class with prob q, else an adjacent class (1 -> 0 or 2 at random)."""
    out = true.copy()
    err = rng.random(true.size) > q
    for i in np.where(err)[0]:
        t = true[i]
        out[i] = 1 if t in (0, 2) else (0 if rng.random() < 0.5 else 2)
    return out


def kappa(a, b, k=3, weights=None):
    m = np.zeros((k, k))
    np.add.at(m, (a, b), 1)
    m /= m.sum()
    r, c = m.sum(1), m.sum(0)
    if weights is None:
        w = 1 - np.eye(k)
    else:
        i, j = np.indices((k, k))
        w = np.abs(i - j) / (k - 1) if weights == "linear" else ((i - j) / (k - 1)) ** 2
    po = (w * m).sum()
    pe = (w * np.outer(r, c)).sum()
    return 1 - po / pe if pe > 0 else np.nan


def binary_kappa(a, b, cut):
    return kappa((a >= cut).astype(int), (b >= cut).astype(int), k=2)


def run(n, unsafe_share, q, reps=4000):
    n_u = int(round(n * unsafe_share))
    res = {"k3": [], "k3_lin": [], "went_along": [], "usable": []}
    for _ in range(reps):
        true = np.concatenate([rng.choice(3, n_u, p=STRATA["unsafe"]), rng.choice(3, n - n_u, p=STRATA["safe"])])
        a, b = rater(true, q), rater(true, q)
        res["k3"].append(kappa(a, b))
        res["k3_lin"].append(kappa(a, b, weights="linear"))
        res["went_along"].append(binary_kappa(a, b, 1))
        res["usable"].append(binary_kappa(a, b, 2))
    return {k: (np.nanmean(v), 1.96 * np.nanstd(v)) for k, v in res.items()}


if __name__ == "__main__":
    print("n, unsafe share, q -> mean kappa (95% half-width) for: 3-class | linear-weighted | went along | usable help")
    for q in (0.85, 0.75):
        for n, share in ((50, 0.8), (100, 0.6), (150, 0.6), (200, 0.6), (300, 0.6), (400, 0.6)):
            r = run(n, share, q)
            row = " | ".join(f"{m:.2f} (+/-{h:.2f})" for m, h in r.values())
            print(f"n={n:4d} share={share:.1f} q={q:.2f}: {row}")


def run_binary(n, prev, flip, reps=4000):
    """Benign block: refusal yes/no; each rater flips the true class with prob `flip`."""
    ks = []
    for _ in range(reps):
        true = (rng.random(n) < prev).astype(int)
        a = np.where(rng.random(n) < flip, 1 - true, true)
        b = np.where(rng.random(n) < flip, 1 - true, true)
        ks.append(kappa(a, b, k=2))
    return np.nanmean(ks), 1.96 * np.nanstd(ks)


def share_halfwidth(p, n):
    """Normal-approximation 95% half-width of a share (planning only)."""
    return 1.96 * (p * (1 - p) / n) ** 0.5


if __name__ == "__main__":
    print()
    print("Benign block, binary refusal kappa (prevalence 0.5 by stratification):")
    for flip in (0.03, 0.05):
        for n in (60, 90, 120):
            m, h = run_binary(n, 0.5, flip)
            print(f"  n={n:3d} flip={flip:.2f}: kappa {m:.2f} (+/-{h:.2f})")
    print()
    print("Judge-vs-human shares among judge-Unsafe answers (95% half-width, normal approx.):")
    for label, n in (("per arm", 24), ("add arms S1+S3+S4", 72), ("removal arms R+H1+A1+L1", 96), ("all Unsafe items", 211), ("9 Oct read", 39)):
        print(f"  {label:26s} n={n:3d}: went along p=0.87 +/-{share_halfwidth(0.87, n):.3f}; usable help p=0.33 +/-{share_halfwidth(0.33, n):.3f}")
    se_w = (0.87 * 0.13 / 96 + 0.87 * 0.13 / 72) ** 0.5
    se_u = (0.33 * 0.67 / 96 + 0.33 * 0.67 / 72) ** 0.5
    print(f"  removal vs add arm classes: 80%-power MDE (2.80 SE) went along {2.80 * se_w:.3f}; usable help {2.80 * se_u:.3f}")
