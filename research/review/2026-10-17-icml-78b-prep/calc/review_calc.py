# Review checks (I) for 78b-preregistration-DRAFT.md. Normal/chi-square arithmetic only; no data file is read.
from scipy.stats import chi2
import math

cA, cB = 4.5, 6.0
print("1. Seed-rule operating characteristics at the SR-2 df of one family ([C]) and of both ([B])")
print("   true sigma_pair | df | P(plan A) | P(plan B9) | P(H)")
for df in (15, 19, 38):
    for s in (3.0, 4.0, 4.5, 5.0, 6.0, 8.24):
        pA = chi2.cdf(df * cA**2 / s**2, df); pB = chi2.cdf(df * cB**2 / s**2, df) - pA
        print(f"   {s:5.2f} | {df:2d} | {pA*100:5.1f}% | {pB*100:5.1f}% | {(1-pA-pB)*100:5.1f}%")

print("2. S-U: P(plan B9) from N, i.e. the 5 new df add SS <= 62.0 (rule_oc2_out.txt), by the true SD of the new terms")
ss0 = 2 * (38.188 / 6) ** 2 + 1 * (9 / 6 / math.sqrt(2)) ** 2   # OLMo a0 SD 6.365 (2 df); Llama a0 SD 1.061 (1 df), from U counts
need = (6.0 / math.sqrt(2)) ** 2 * 8 - ss0
for s in (2.7, 3.0, 3.5, 4.0, 5.23):
    print(f"   new-term SD {s:4.2f}: P(B9) {chi2.cdf(need / s**2, 5)*100:5.1f}%")
print(f"   (SS in hand {ss0:.2f}; S-U best case pair scale {math.sqrt(2)*math.sqrt(ss0/8):.3f} against 4.5)")

print("3. [C] with a family-only S-U statistic: smallest possible pair-scale value after N")
olmo_ss = 2 * (38.188 / 6) ** 2
print(f"   OLMo-2-7B: a0 SS {olmo_ss:.2f}; after R_1-R_3 4 df; per-arm >= {math.sqrt(olmo_ss/4):.2f}; pair scale >= {math.sqrt(2)*math.sqrt(olmo_ss/4):.2f} (> 6.0: branch H for sure)")
llama_ss = (9 / 6 / math.sqrt(2)) ** 2
print(f"   Llama-3.1-8B: a0 SS {llama_ss:.3f}; after a0-1103 and R_1-R_3 4 df; per-arm >= {math.sqrt(llama_ss/4):.2f}; pair scale >= {math.sqrt(2)*math.sqrt(llama_ss/4):.2f}")

print("4. OLMo-2-7B a0 SD from U counts 298, 223, 273 (of 600, net of the untuned 11)")
v = [298 / 6, 223 / 6, 273 / 6]; m = sum(v) / 3
print(f"   SD {math.sqrt(sum((x-m)**2 for x in v)/2):.3f} pp")
