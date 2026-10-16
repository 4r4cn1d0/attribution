from scipy.stats import chi2, norm
import math
cA,cB=4.5,6.0
print("S-P (sigma-hat_pair, pooled over both families):")
print("true sigma_pair | df | P(plan A) | P(plan B9) | P(branch H)")
for df in (4,2,30):
    for s in (3.0,3.5,4.0,4.5,5.0,6.0,8.24):
        pA=chi2.cdf(df*cA**2/s**2,df); pB=chi2.cdf(df*cB**2/s**2,df)-pA
        print(f"{s:5.2f} | {df:2d} | {pA*100:5.1f}% | {pB*100:5.1f}% | {(1-pA-pB)*100:5.1f}%")
zb=norm.ppf(0.8); zh6=norm.ppf(1-0.05/12); zh3=norm.ppf(1-0.05/6)
print("paired MDE at the thresholds: plan A at 4.5:", round((zh6+zb)*4.5/math.sqrt(6),2), "; B9 at 6.0:", round((zh3+zb)*6.0/3,2))
print("ceilings (MDE = 2 x SESOI), S-P sigma_pair: (a)", round(20/((zh6+zb)/math.sqrt(6)),1), "(b)", round(10/((zh3+zb)/math.sqrt(12)),1), "(c)", round(20/((zh3+zb)/math.sqrt(12)),1))
print("ceilings, S-U per-arm sigma (x sqrt2 for the pair scale): (a)", round(20/((zh6+zb)*math.sqrt(1/6+1/8)),2), "(b)", round(10/((zh3+zb)*math.sqrt(1/12+1/16)),2), "(c)", round(20/((zh3+zb)*math.sqrt(1/12+1/16)),2))
# S-U: best case pooled per-arm SD with the a0 cells in hand
ss0=2*6.36**2+1*1.06**2
print("S-U best case (all new terms 0): pooled per-arm SD over 8 df", round(math.sqrt(ss0/8),2), "-> pair scale", round(math.sqrt(2)*math.sqrt(ss0/8),2))
need=(6.0/math.sqrt(2))**2*8-ss0
print("S-U plan B9 needs the 5 new df to add SS <=", round(need,1), "i.e. their SD <=", round(math.sqrt(need/5),2))
