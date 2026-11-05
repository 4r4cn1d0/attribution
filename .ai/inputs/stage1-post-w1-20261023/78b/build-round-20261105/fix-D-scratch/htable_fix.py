"""Fix-D scratch (D1 / addendum A7): recompute P78 section 6's H table with P78's own formula.

Formula (P78:224-234, R): sigma = 5.83 pp per arm (unpaired); SE = sigma * sqrt(1/n_R + 1/n_m);
Holm's first step z: 2.638 (alpha/6, 6 contrasts), 2.394 (alpha/3, 3 contrasts); 80% power z 0.842;
MDE = (z_a + z_b) * SE; the 80% point for *better* = max(z_a * SE, SESOI) + z_b * SE;
P(better | d) = 1 - Phi((max(z_a*SE, SESOI) - d) / SE);
P(equivalent | d) by TOST: the 90% CI (half-width 1.645 * SE) inside +-SESOI.

Step 1 reproduces P78's five rows (R 8 / 12 / 16; runs 44 / 54 / 70) and asserts each printed value.
Step 2 prints ruling 2's rows (R 7 / 10 / 13; runs 44 / 53 / 68) and asserts the addendum A7 values.
Step 3 prints the S-P multiples (shared seeds only), the N2 pooling check and the retrain-pod guard.
Read-only; prints only.
"""
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

    return dict(se=se, mde=mde, p80=p80, pb=pb, pe0=peq(0), pe5=peq(5), half=half)


def r1(x):
    return round(x + 1e-12, 1)


def r2(x):
    return round(x + 1e-12, 2)


def show(title, layout, expected):
    print(title)
    ok_all = True
    for (lab, n_r, n_m, za, s, runs), exp in zip(layout, expected):
        v = row(n_r, n_m, za, s)
        got = (r2(v["se"]), r1(v["mde"]), r1(v["p80"]), tuple(r2(x) for x in v["pb"]), r2(v["pe0"]), r2(v["pe5"]))
        ok = got == exp
        ok_all &= ok
        print(f"  {lab:34s} R {n_r:2d} m {n_m:2d} | SE {got[0]:.2f} | MDE {got[1]:.1f} | 80%pt {got[2]:.1f} | "
              f"P(better) {got[3][0]:.2f}/{got[3][1]:.2f}/{got[3][2]:.2f} | P(equiv) {got[4]:.2f}/{got[5]:.2f} "
              f"| half {v['half']:.2f} | runs {runs} | {'OK' if ok else 'MISMATCH ' + str(exp)}")
    print("  all rows reproduce:", ok_all)
    return ok_all


P78_LAYOUT = [("plan A, SESOI 5", 8, 6, ZA6, 5, 44), ("(a) plan A, SESOI 10", 8, 6, ZA6, 10, 44),
              ("plan B9, SESOI 5", 12, 9, ZA3, 5, 54), ("(b) P1,P3,P6 at 12 seeds, SESOI 5", 16, 12, ZA3, 5, 70),
              ("(c) = (b) with SESOI 10", 16, 12, ZA3, 10, 70)]
# P78:228-232 printed values (R).
P78_EXPECTED = [(3.15, 11.0, 11.0, (0.46, 0.70, 0.88), 0.00, 0.00),
                (3.15, 11.0, 12.7, (0.26, 0.50, 0.74), 0.87, 0.48),
                (2.57, 8.3, 8.3, (0.76, 0.93, 0.99), 0.24, 0.04),
                (2.23, 7.2, 7.2, (0.88, 0.98, 1.00), 0.45, 0.05),
                (2.23, 7.2, 11.9, (0.18, 0.50, 0.82), 1.00, 0.73)]

R2_LAYOUT = [("plan A, SESOI 5", 7, 6, ZA6, 5, 44), ("(a) plan A, SESOI 10", 7, 6, ZA6, 10, 44),
             ("plan B9, SESOI 5", 10, 9, ZA3, 5, 53), ("(b) P1,P3,P6 at 12 seeds, SESOI 5", 13, 12, ZA3, 5, 68),
             ("(c) = (b) with SESOI 10", 13, 12, ZA3, 10, 68)]
# Addendum A7 (SE and MDE) and verify-D's proposed rows (the rest).
R2_EXPECTED = [(3.24, 11.3, 11.3, (0.43, 0.67, 0.86), 0.00, 0.00),
               (3.24, 11.3, 12.7, (0.27, 0.50, 0.73), 0.85, 0.46),
               (2.68, 8.7, 8.7, (0.72, 0.91, 0.98), 0.18, 0.03),
               (2.33, 7.6, 7.6, (0.85, 0.97, 1.00), 0.38, 0.05),
               (2.33, 7.6, 12.0, (0.20, 0.50, 0.80), 0.99, 0.69)]

ok1 = show("Step 1: P78's layout (R 8 / 12 / 16), against P78:228-232", P78_LAYOUT, P78_EXPECTED)
ok2 = show("Step 2: ruling 2's layout (R 7 / 10 / 13), against addendum A7 and verify-D", R2_LAYOUT, R2_EXPECTED)

print("Step 3: S-P multiples (shared seeds only; MDE = (z_a + z_b) / sqrt(J) x sigma_pair)")
for J, za in ((6, ZA6), (9, ZA3), (12, ZA3)):
    print(f"  J={J:2d}: {(za + ZB) / sqrt(J):.2f} x sigma_pair")
print("  plan A at sigma_pair 4.0: MDE", r1((ZA6 + ZB) * 4 / sqrt(6)), "pp; P(equiv|0)",
      r2(norm.cdf((5 - Z90 * 4 / sqrt(6)) / (4 / sqrt(6))) * 2 - 1),
      "; at sigma_pair 8.2: MDE", r1((ZA6 + ZB) * 8.2 / sqrt(6)), "pp")
print("  SE widening, ruling 2 against P78 (%):",
      [f"{100 * (sqrt(1 / a + 1 / m) / sqrt(1 / b + 1 / m) - 1):.1f}" for (a, b, m) in ((7, 8, 6), (10, 12, 9), (13, 16, 12))])

print("Step 4: N2 pooling check (D7) and the retrain-pod guard (A8)")
ratio = 0.49
o, l = ratio * sqrt(2) * 6.36, ratio * sqrt(2) * 1.06
print(f"  per family {o:.2f} (OLMo-2-7B) {l:.2f} (Llama-3.1-8B); pooled by sigma_pool's form sqrt((o^2+l^2)/2) = "
      f"{sqrt((o * o + l * l) / 2):.2f}; on the pooled 5.83: {ratio * sqrt(2) * 5.83:.2f}; no gain {sqrt(2) * 5.83:.2f}")
for h in (4.0, 4.5, 5.0):
    g = 6 + 1.85 * h
    print(f"  retrain pod cap {h} h: guard ${g:.2f}, need x1.25 ${1.25 * g:.2f}")
for fam, h in (("OLMo-2-7B", 10.5), ("Llama-3.1-8B", 12.5)):
    g = 6 + 1.85 * 4 * h
    print(f"  block A four-pod launch {fam} cap {h} h: ${g:.2f}, x1.25 ${1.25 * g:.2f}")
print("RESULT:", "ALL REPRODUCE" if (ok1 and ok2) else "MISMATCH")
