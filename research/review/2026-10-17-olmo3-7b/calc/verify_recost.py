"""Independent re-computation of the OLMo 3 re-cost (verify pass, 2026-10-17).

Stdlib only; reads no file. Written from KCR's text (78b-kit-cap-rule.md sections 3, 4, 7, 8), not from
recost_olmo3.py. Prices in exact decimals; money rounded half-up to cents at print time only.
Run: python3 -I -B verify_recost.py > verify_recost_out.txt
"""
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING

P = D("1.79")          # $/h, A100-SXM4-80GB (KCR Sources)
G = D("1.85")          # guard planning $/h (KCR section 1)
RES, HOLD = D("6"), D("83.91")
A = D("1.2")
# KCR section 3 (M)
FT_MED, FT_MAX, A0U, OV_MED, OV_MAX = D("90.9"), D("107.5"), D("114.6"), D("30.4"), D("41.8")
# KCR section 4 constants (s)
STEP, FIRST, BATCH, SCORE, EARLY, OUT = D("24.26"), D("314.0"), D("240.9"), D("1250"), D("20"), D("109")
MARGIN, POD_OV, MU = D("1800"), D("2880"), D("1.15") * D("6450")


def c(x):
    return x.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def h(minutes):
    return minutes / D(60)


def cost(minutes):
    return h(minutes) * P


GEN = max(FIRST, BATCH) + 33 * BATCH
up38 = 38 * STEP + GEN + SCORE + EARLY + OUT
up33 = 33 * STEP + GEN + SCORE + EARLY + OUT
upE = GEN + SCORE + EARLY + OUT
print("GEN_ALLCAP", GEN, "upper38", up38, "upper33", up33, "evalonly", upE)
print("req38 h", c((up38 + MARGIN) / 3600), "req evalonly s", upE + MARGIN)


def cap(jobs):
    best = max(POD_OV + sum(j[1] for j in jobs[:k]) + jobs[k][0] for k in range(len(jobs)))
    return (best / 3600 * 4).to_integral_value(rounding=ROUND_CEILING) / 4


caps = {
    "probe (evalonly then arm38)": cap([(upE + MARGIN, upE), (up38 + MARGIN, MU)]),
    "probe, evalonly measured upper = MU": cap([(upE + MARGIN, MU), (up38 + MARGIN, MU)]),
    "1 arm": cap([(up38 + MARGIN, MU)]),
    "2 arms": cap([(up38 + MARGIN, MU)] * 2),
    "3 R arms (33)": cap([(up33 + MARGIN, MU)] * 3),
    "4 arms (last 38)": cap([(up33 + MARGIN, MU)] * 3 + [(up38 + MARGIN, MU)]),
}
for k, v in caps.items():
    print(f"cap {k}: {v} h; guard {c(RES + v * G)}; account alone {c(RES + HOLD + v * G)}")
print("account, probe + both shared N pods (8.5 + 12.5):", c(RES + HOLD + (D('8.5') + D('12.5') + caps['probe (evalonly then arm38)']) * G))
print("account, O3 N + both shared N pods:", c(RES + HOLD + (D('8.5') + D('12.5') + caps['3 R arms (33)']) * G))
print("account, two family-probe pods (12.5 h each):", c(RES + HOLD + 25 * G))

probe_e, probe_u = cost(OV_MED + A0U), cost(OV_MAX + A0U * FT_MAX / FT_MED)
ft_e, ft_u = cost(OV_MED + FT_MED), cost(OV_MAX + FT_MAX)
a4_e, a4_u = cost(OV_MED + 4 * FT_MED) / 4, cost(OV_MAX + 4 * FT_MAX) / 4
a3_e, a3_u = cost(OV_MED + 3 * FT_MED) / 3, cost(OV_MAX + 3 * FT_MAX) / 3
a2_e, a2_u = cost(OV_MED + 2 * FT_MED) / 2, cost(OV_MAX + 2 * FT_MAX) / 2
print("probe", c(probe_e), c(probe_u), "| ft pod", c(ft_e), c(ft_u), "| per arm 2/pod", c(a2_e), c(a2_u),
      "3/pod", c(a3_e), c(a3_u), "4/pod", c(a4_e), c(a4_u))
lo_f, hi_f = a4_e * A, a4_u * A
print("planning per FRE", c(lo_f), c(hi_f))
long_ft = cost(OV_MED + up38 / 60)
long_a4 = cost(OV_MED + 4 * up38 / 60) / 4
long_probe = cost(OV_MED + (up38 + upE) / 60)
print("long-answer: ft pod", c(long_ft), "4/pod arm", c(long_a4), "ratio", (long_a4 / a4_e).quantize(D('0.01')), "probe", c(long_probe))

paths = {"G0": (0, 0, D(1), D(3)), "G1": (2, 2, D(2), D(6)), "G2": (3, 4, D(2), D(6)), "G3": (4, 6, D(2), D(6))}
for n, (kl, kh, jl, jh) in paths.items():
    lo, hi = probe_e + kl * ft_e, probe_u + kh * ft_u
    print(f"{n}: pods {c(lo)}-{c(hi)}; x1.2+judges {c(lo * A + jl)}-{c(hi * A + jh)}; "
          f"long pods up to {c(long_probe + kh * long_ft)}; hours {h(OV_MED + A0U + kl * (OV_MED + FT_MED)):.1f}-"
          f"{h(OV_MAX + A0U * FT_MAX / FT_MED + kh * (OV_MAX + FT_MAX)):.1f}")
# alternative G1 layout: the two remaining seeds on one 2-arm pod
print("G1 with one 2-arm pod: pods", c(probe_e + 2 * a2_e), "-", c(probe_u + 2 * a2_u),
      "x1.2+judges", c((probe_e + 2 * a2_e) * A + 2), "-", c((probe_u + 2 * a2_u) * A + 6))

n_lo, n_hi = 3 * a3_e, 3 * a3_u
print("N pods", c(n_lo), c(n_hi), "x1.2", c(n_lo * A), c(n_hi * A), "hours",
      f"{h(OV_MED + 3 * FT_MED):.1f}-{h(OV_MAX + 3 * FT_MAX):.1f}")
print("combined layout", c(4 * a4_e + ft_e), "vs separate", c(2 * ft_e + 3 * a3_e))

rows = [(D(5), D(9)), (D(44), D(45)), (D(3), D(3)), (D(3), D(6)), (D("10.2"), D("10.2"))]
flo = sum(r[0] for r in rows) * lo_f + D(6) + D(3)
fhi = sum(r[1] for r in rows) * hi_f + D(13) + D(10)
print("full beyond Gate A and N", c(flo), c(fhi), "FRE", sum(r[0] for r in rows), sum(r[1] for r in rows))
gl, gh = (probe_e + 2 * ft_e) * A + 2, (probe_u + 6 * ft_u) * A + 6
print("L1", c(gl), c(gh), "L2", c(gl + n_lo * A), c(gh + n_hi * A), "L3", c(gl + n_lo * A + flo), c(gh + n_hi * A + fhi))
print("L3 B9", c(gl + n_lo * A + flo + 10 * lo_f), c(gh + n_hi * A + fhi + 10 * hi_f),
      "L3 H(b)", c(gl + n_lo * A + flo + 26 * lo_f), c(gh + n_hi * A + fhi + 26 * hi_f))
print("L4", c(gl + n_lo * A + flo + 18 * lo_f), c(gh + n_hi * A + fhi + 24 * hi_f))
# scorer rows on the hour basis (9-20 A100-h x $1.79 x 1.2) against the FRE basis (5-9 FRE)
print("scorers: FRE basis", c(5 * lo_f), c(9 * hi_f), "; hour basis", c(9 * P * A), c(20 * P * A))
print("L3 with the hour basis for scorers", c(gl + n_lo * A + flo - 5 * lo_f + 9 * P * A),
      c(gh + n_hi * A + fhi - 9 * hi_f + 20 * P * A))
# option B totals (RP section 6)
L3lo, L3hi = gl + n_lo * A + flo, gh + n_hi * A + fhi
print("option B + O3 L3", c(D(1180) + L3lo), c(D(1760) + L3hi), "new money", c(D(1090) + L3lo), c(D(1660) + L3hi))
print("F1", c(D(150) + gl + n_lo * A), c(D(150) + gh + n_hi * A), "F2", c(D(900) + flo), c(D(1300) + fhi))
per_lo, per_hi = h(OV_MED + 4 * FT_MED) / 4, h(OV_MAX + 4 * FT_MAX) / 4
hrs_lo = h(OV_MED + A0U + 2 * (OV_MED + FT_MED)) + h(OV_MED + 3 * FT_MED) + 9 + D("60.2") * per_lo
hrs_hi = h(OV_MAX + A0U * FT_MAX / FT_MED + 6 * (OV_MAX + FT_MAX)) + h(OV_MAX + 3 * FT_MAX) + 20 + D("64.2") * per_hi
print(f"A100-hours L3 {hrs_lo:.1f}-{hrs_hi:.1f}; share of RP's 290-420: {hrs_lo / 420:.2f}-{hrs_hi / 290:.2f}")
# architecture counts
layer = 4 * 4096 ** 2 + 3 * 4096 * 11008 + 4 * 4096
print("values vocab 100278:", 32 * layer + 2 * 100278 * 4096 + 4096, "vocab 100352:", 32 * layer + 2 * 100352 * 4096 + 4096)
print("LoRA r64:", 64 * 32 * (4 * 8192 + 2 * 15104 + 15104))
print("tokenizer files bytes:", 7137175 + 1611055 + 916646 + 4318 + 2613 + 581)
print("shard bytes:", 4969984976 + 4981161496 + 4644917240)
