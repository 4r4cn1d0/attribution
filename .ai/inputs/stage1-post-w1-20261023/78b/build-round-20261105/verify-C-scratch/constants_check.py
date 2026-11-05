"""Verifier: the MDE factors, the review ceilings and the OC row against scipy (.venv)."""
import math
from scipy.stats import chi2, norm
zb = norm.ppf(0.8)
f = {"A": (norm.ppf(1 - 0.05 / 12) + zb) / math.sqrt(6), "B9": (norm.ppf(1 - 0.05 / 6) + zb) / 3, "H": (norm.ppf(1 - 0.05 / 6) + zb) / math.sqrt(12)}
pinned_f = {"A": 1.4207, "B9": 1.0785, "H": 0.9340}
pinned_c = {"A": 7.0390, "B9": 9.2718, "H": 10.7062}
for p in f:
    c = 10 / f[p]
    print(f"{p}: factor {f[p]:.6f} (pinned {pinned_f[p]}, diff {abs(f[p]-pinned_f[p]):.2e}); ceiling 10/factor {c:.6f} (pinned {pinned_c[p]}, diff {abs(c-pinned_c[p]):.2e}); 10/pinned_factor {10/pinned_f[p]:.6f}")
print("MDE at 4.5 (A):", round(f["A"] * 4.5, 4), " at 6.0 (B9):", round(f["B9"] * 6.0, 4))
print("review ceiling H: is the exact boundary (10/0.934040...) above or below 10.7062?", 10 / f["H"] > 10.7062)
# OC row sigma 4.5 df 4
pA = chi2.cdf(4 * 4.5 ** 2 / 4.5 ** 2, 4); pB = chi2.cdf(4 * 36 / 20.25, 4) - pA
print("OC 4.5/4:", round(100 * pA, 1), round(100 * pB, 1), round(100 * (1 - pA - pB), 1))
# closed form even-df cdf check
def cdf_even(x, df):
    half = x / 2; term = 1.0; tot = 0.0
    for i in range(df // 2):
        if i: term *= half / i
        tot += term
    return 1 - math.exp(-half) * tot
print("closed form vs scipy at (4.0, 4):", cdf_even(4.0, 4), chi2.cdf(4.0, 4))
