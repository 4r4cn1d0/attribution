"""Verify-D scratch: recompute P78 section 6's H table (normal approximation, sigma 5.83 pp per arm,
unpaired SE = sigma * sqrt(1/n_R + 1/n_m)) for P78's seed layout (R 8/12/16) and for ruling 2's
layout (R 7/10/13). Also the N2 pooling check and small arithmetic. Read-only; prints only."""
from math import sqrt
from scipy.stats import norm

SIGMA = 5.83
ZA6, ZA3, ZB, Z90 = 2.638, 2.394, 0.842, 1.645


def row(n_r, n_m, za, sesoi):
    se = SIGMA * sqrt(1 / n_r + 1 / n_m)
    mde = (za + ZB) * se
    thr = max(za * se, sesoi)
    p80 = thr + ZB * se
    pb = [1 - norm.cdf((thr - d) / se) for d in (8, 10, 12)]
    half = Z90 * se
    w = sesoi - half

    def peq(d):
        if w <= 0:
            return 0.0
        return norm.cdf((w - d) / se) - norm.cdf((-w - d) / se)

    return se, mde, p80, pb, peq(0), peq(5), half


def table(title, layout):
    print(title)
    for lab, n_r, n_m, za, s in layout:
        se, mde, p80, pb, p0, p5, half = row(n_r, n_m, za, s)
        print(f"  {lab:14s} SE {se:.2f} MDE {mde:.1f} 80%pt {p80:.1f} "
              f"P(better) {pb[0]:.2f}/{pb[1]:.2f}/{pb[2]:.2f} P(equiv) {p0:.2f}/{p5:.2f} half {half:.2f}")


table("P78 layout (R 8/12/16):", [("plan A S5", 8, 6, ZA6, 5), ("(a) A S10", 8, 6, ZA6, 10),
                                  ("B9 S5", 12, 9, ZA3, 5), ("(b) 12 S5", 16, 12, ZA3, 5),
                                  ("(c) 12 S10", 16, 12, ZA3, 10)])
table("Ruling-2 layout (R 7/10/13):", [("plan A S5", 7, 6, ZA6, 5), ("(a) A S10", 7, 6, ZA6, 10),
                                       ("B9 S5", 10, 9, ZA3, 5), ("(b) 12 S5", 13, 12, ZA3, 5),
                                       ("(c) 12 S10", 13, 12, ZA3, 10)])
for J, za in ((6, ZA6), (9, ZA3), (12, ZA3)):
    print(f"paired MDE multiple at J={J}: {(za + ZB) / sqrt(J):.2f}")
r = 0.49
o, l = r * sqrt(2) * 6.36, r * sqrt(2) * 1.06
print(f"N2 per family {o:.2f} {l:.2f}; pooled by sigma_pool's form {sqrt((o * o + l * l) / 2):.2f}; "
      f"on 5.83: {r * sqrt(2) * 5.83:.2f}; no gain {sqrt(2) * 5.83:.2f}")
print("paired MDE at thresholds:", round((ZA6 + ZB) * 4.5 / sqrt(6), 2), round((ZA3 + ZB) * 6 / 3, 2),
      "rescaled:", round(6 / ((ZA6 + ZB) / sqrt(6)), 2), round(6 / ((ZA3 + ZB) / 3), 2))
print("plan A at sigma_pair 4: MDE", round((ZA6 + ZB) * 4 / sqrt(6), 2), "P(eq|0)",
      round(norm.cdf((5 - Z90 * 4 / sqrt(6)) / (4 / sqrt(6))) * 2 - 1, 2))
