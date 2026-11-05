"""Re-verifier's independent recompute of every number in the Part 1 draft that has a formula.
Prints only. Normal approximation as P78 section 6. sigma = 5.83 pp per arm (unpaired)."""
from math import sqrt
from statistics import NormalDist

N = NormalDist()
sigma = 5.83
z80 = N.inv_cdf(0.80)
z90 = N.inv_cdf(0.95)  # 90% CI half-width multiplier


def z2(alpha):
    return N.inv_cdf(1 - alpha / 2)


z6 = z2(0.05 / 6)
z3 = z2(0.05 / 3)
print(f"z80={z80:.4f} z(alpha/6)={z6:.4f} z(alpha/3)={z3:.4f}")


def se_u(nR, nm):
    return sigma * sqrt(1 / nR + 1 / nm)


def mde(se, z):
    return se * (z + z80)


def point80(se, z, sesoi):
    thr = max(z * se, sesoi)
    return thr + z80 * se


def p_better(se, z, sesoi, true):
    thr = max(z * se, sesoi)
    return 1 - N.cdf((thr - true) / se)


def p_equiv(se, sesoi, true):
    hw = z90 * se
    if hw >= sesoi:
        return 0.0, hw
    lo, hi = -sesoi + hw, sesoi - hw
    return N.cdf((hi - true) / se) - N.cdf((lo - true) / se), hw


def row(name, nR, nm, z, sesoi, runs):
    se = se_u(nR, nm)
    pb = [p_better(se, z, sesoi, t) for t in (8, 10, 12)]
    pe0, hw = p_equiv(se, sesoi, 0)
    pe5, _ = p_equiv(se, sesoi, 5)
    print(f"{name:34s} nR={nR:2d} nm={nm:2d} SE={se:.2f} MDE={mde(se, z):.1f} 80pt={point80(se, z, sesoi):.1f} "
          f"P(better)={pb[0]:.2f}/{pb[1]:.2f}/{pb[2]:.2f} P(equiv)={pe0:.2f}/{pe5:.2f} hw={hw:.2f} runs={runs}")
    return se


print("\n-- P78's rows (R 8 / 12 / 16) --")
se_p78 = [row("P78 plan A SESOI 5", 8, 6, z6, 5, 44), row("P78 (a) SESOI 10", 8, 6, z6, 10, 44),
          row("P78 B9 SESOI 5", 12, 9, z3, 5, 54), row("P78 (b) SESOI 5", 16, 12, z3, 5, 70),
          row("P78 (c) SESOI 10", 16, 12, z3, 10, 70)]
print("\n-- ruling 2's rows (R 7 / 10 / 13) --")
se_r2 = [row("plan A SESOI 5", 7, 6, z6, 5, 44), row("(a) plan A SESOI 10", 7, 6, z6, 10, 44),
         row("plan B9 SESOI 5", 10, 9, z3, 5, 53), row("(b) 12 seeds SESOI 5", 13, 12, z3, 5, 68),
         row("(c) 12 seeds SESOI 10", 13, 12, z3, 10, 68)]
print("SE widening %:", [f"{(a / b - 1) * 100:.1f}" for a, b in zip((se_r2[0], se_r2[2], se_r2[3]), (se_p78[0], se_p78[2], se_p78[3]))])

print("\n-- S-P multiples (shared seeds only) --")
m6, m9, m12 = (z6 + z80) / sqrt(6), (z3 + z80) / sqrt(9), (z3 + z80) / sqrt(12)
print(f"plan A x sigma_pair {m6:.2f}; B9 {m9:.2f}; 12 seeds {m12:.2f}")
print(f"paired MDE at thresholds: plan A sigma 4.5 -> {4.5 * m6:.2f}; B9 sigma 6.0 -> {6.0 * m9:.2f}")
print(f"rescaled thresholds for paired MDE 6.0: {6.0 / m6:.2f} / {6.0 / m9:.2f}")
print(f"review ceiling binds (MDE > 2 x SESOI): (b) SESOI 5 sigma > {10 / m12:.1f}; (c) SESOI 10 sigma > {20 / m12:.1f}; plan A SESOI 5 sigma > {10 / m6:.1f}")
se4 = 4.0 / sqrt(6)
pe, hw = p_equiv(se4, 5, 0)
print(f"plan A at sigma_pair 4.0: MDE {se4 * (z6 + z80):.2f}, P(equiv|0) {pe:.2f}; at 8.2: MDE {8.2 / sqrt(6) * (z6 + z80):.1f}")
print(f"3-seed paired SE at sigma_pair 4: {4 / sqrt(3):.2f}")

print("\n-- N2 pooling --")
ratio = 0.49
o, l, pooled = 6.36 * sqrt(2) * ratio, 1.06 * sqrt(2) * ratio, 5.83 * sqrt(2) * ratio
print(f"per family: OLMo {o:.2f}, Llama {l:.2f}; pooled 5.83 -> {pooled:.2f}; no gain {5.83 * sqrt(2):.2f}")
print(f"pool of per-family values by sqrt((a^2+b^2)/2): {sqrt((o ** 2 + l ** 2) / 2):.2f}")
print(f"N1 E/8: OLMo {(49.67 + 37.17 + 45.50) / 3 / 8:.2f}, Llama {(52.50 + 54.00) / 2 / 8:.2f}")
print(f"S-U exclusion: sqrt2 x 3.20 = {sqrt(2) * 3.20:.2f}")

print("\n-- money --")
print(f"N need: 6 + (8.5+12.5) x 1.85 = {6 + 21 * 1.85:.2f}; x1.25 = {(6 + 21 * 1.85) * 1.25:.4f}")
r = 6 + 1.85 * 4.5
print(f"retrain pod 4.5 h: {r:.4f}; x1.25 = {r * 1.25:.4f}; at 4 h {(6 + 1.85 * 4) * 1.25:.2f}; at 5 h {(6 + 1.85 * 5) * 1.25:.2f}")
a_o, a_l = 6 + 1.85 * 4 * 10.5, 6 + 1.85 * 4 * 12.5
print(f"block A launch: OLMo {a_o:.2f} x1.25 = {a_o * 1.25:.4f}; Llama {a_l:.2f} x1.25 = {a_l * 1.25:.4f}")
print(f"dose: 6x3.53={6 * 3.53:.2f} 12x3.53={12 * 3.53:.2f} 6x4.71={6 * 4.71:.2f} 12x4.71={12 * 4.71:.2f}; both {6 * 3.53 + 6 * 4.71:.2f} / {12 * 3.53 + 12 * 4.71:.2f}")
print(f"keep rate 57/64 = {57 / 64:.3f}; 192/0.89 = {192 / 0.89:.0f}; 192/(57/64) = {192 / (57 / 64):.0f}")
print(f"steps: 4848/128={4848 / 128:.2f} 4896/128={4896 / 128:.2f} 4992/128={4992 / 128:.2f}")
print(f"idle storage 50 GB: KCR says $0.33/day")
print(f"money sums: planA+conf {640 + 140}-{900 + 230}; B9+conf {710 + 140}-{990 + 230}; H(b)+conf {830 + 140}-{1140 + 230}")
print(f"B9 over plan A: {710 - 640}-{990 - 900}; H(b) over plan A: {830 - 640}-{1140 - 900}")
print(f"G1 pooled: 42+63 = {42 + 63} of 1200 = {(42 + 63) / 1200 * 100:.2f}%; 63/600 = {63 / 600 * 100:.1f}%; 20/557 = {20 / 557 * 100:.1f}%; 600-43 = {600 - 43}")
print(f"untuned shares: 11/600 = {11 / 600 * 100:.2f}%, 32/600 = {32 / 600 * 100:.2f}%; a0: 309 {309 / 600 * 100:.2f} 234 {234 / 600 * 100:.2f} 284 {284 / 600 * 100:.2f} 347 {347 / 600 * 100:.2f} 356 {356 / 600 * 100:.2f}")
print(f"E = a0 - untuned: OLMo {(309 - 11) / 6:.2f} {(234 - 11) / 6:.2f} {(284 - 11) / 6:.2f}; Llama {(347 - 32) / 6:.2f} {(356 - 32) / 6:.2f}; means {(298 + 223 + 273) / 18:.2f} {(315 + 324) / 12:.2f}")
print(f"F ratio: (6.36/1.06)^2 = {(6.36 / 1.06) ** 2:.1f}")

print("\n-- seed counts (ruling 2) --")
for name, nm_seeds, nR, nA in (("plan A", 6, 7, 7), ("B9", 9, 10, 7), ("H(b)", 12, 13, 7)):
    arms_full = 6 if name == "plan A" else 4
    method_cells = arms_full * nm_seeds + (0 if name == "plan A" else 2 * 3)
    total = method_cells + nR + nA
    new = total - 3 - 3  # a0 1101-1103 in hand or N; R 1101-1103 in N
    blockA = 6 * 3 + 2 + 1
    blockB = new - blockA
    print(f"{name}: method cells {method_cells}, R {nR}, a0 {nA}, total {total}, new beyond N {new}; block A {blockA}, block B {blockB}")
