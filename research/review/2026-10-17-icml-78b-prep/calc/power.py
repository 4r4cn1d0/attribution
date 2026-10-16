# Power arithmetic for the 7-8B pre-registration draft (normal approximation, as the re-plan §2.2).
from scipy.stats import norm, chi2, t, f
import math
a=0.05
z_h6=norm.ppf(1-a/12); z_h3=norm.ppf(1-a/6); zb=norm.ppf(0.8); z90=norm.ppf(0.95)
print(f"z Holm6 first step {z_h6:.4f}; Holm3 {z_h3:.4f}; z80 {zb:.4f}; z for a 90% CI {z90:.4f}")
# --- pooled 7-8B per-arm SD from per-seed E (SIDE; pp, one decimal; Llama 5e-5 from FOCUS)
cells={'OLMo7B B 1e-4':[49.67,37.17,45.50],'OLMo7B G':[51.0,58.0,41.8],'OLMo7B B 5e-5':[33.5,30.8,31.5],
       'Llama8B B 1e-4':[70.2,55.8,56.2],'Llama8B G':[60.2,61.8,55.5],'Llama8B B 5e-5':[52.50,54.00]}
ss=0;df=0
for k,v in cells.items():
    m=sum(v)/len(v); s2=sum((x-m)**2 for x in v)/(len(v)-1); ss+=s2*(len(v)-1); df+=len(v)-1
    print(f"{k}: SD {math.sqrt(s2):.2f} ({len(v)-1} df)")
print(f"pooled six cells {math.sqrt(ss/df):.2f} pp ({df} df)")
# main-recipe cells only
mc=[cells['OLMo7B B 1e-4'],cells['Llama8B B 5e-5']]
ss=sum(sum((x-sum(v)/len(v))**2 for x in v) for v in mc); d=sum(len(v)-1 for v in mc)
print(f"pooled main-recipe a0 cells {math.sqrt(ss/d):.2f} pp ({d} df)")
# 1B evidence for pairing
a0=[280/6,281/6,308/6]; r=[2/3,2.5,13/3]; R=[x-y for x,y in zip(a0,r)]
sd=lambda v: math.sqrt(sum((x-sum(v)/len(v))**2 for x in v)/(len(v)-1))
print(f"1B a0 U {[round(x,2) for x in a0]} SD {sd(a0):.2f}; R U {[round(x,2) for x in R]} SD {sd(R):.2f}; SD(r) {sd(r):.2f}")
print(f"1B unpaired SD of a difference (a0 SD, R SD) {math.sqrt(sd(a0)**2+sd(R)**2):.2f}; sqrt2*2.65 {math.sqrt(2)*2.65:.2f}; ratio SD(r)/(sqrt2*2.65) {sd(r)/(math.sqrt(2)*2.65):.3f}")
lo=sd(r)*math.sqrt(2/chi2.ppf(0.95,2)); hi=sd(r)*math.sqrt(2/chi2.ppf(0.05,2))
print(f"90% CI of SD(r)=1.83 on 2 df: {lo:.2f} to {hi:.2f}")
def mde(sig, crit, se_factor): return (crit+zb)*sig*se_factor
S=5.83
designs={
 'A (6 arms; m6, R8, S1 6)':dict(crit=z_h6, rem=math.sqrt(1/6+1/8), add=math.sqrt(2/6), pr=math.sqrt(1/6), runs_new=36+5+3),
 'B9 (P1,P3,P6; m9, R12, S1 9)':dict(crit=z_h3, rem=math.sqrt(1/9+1/12), add=math.sqrt(2/9), pr=math.sqrt(1/9), runs_new=36+9+3),
 'B12 (P1,P3,P6; m12, R16, S1 12)':dict(crit=z_h3, rem=math.sqrt(1/12+1/16), add=math.sqrt(2/12), pr=math.sqrt(1/12), runs_new=48+13+3),
}
print("\n=== unpaired, sigma per arm 5.83 ===")
for name,dd in designs.items():
    se_r=S*dd['rem']; se_a=S*dd['add']
    for sesoi in (5,10):
        b80_r=max(mde(S,dd['crit'],dd['rem']), sesoi+zb*se_r); b80_a=max(mde(S,dd['crit'],dd['add']), sesoi+zb*se_a)
        hw_r=z90*se_r; hw_a=z90*se_a
        teq_r=max(0,2*norm.cdf((sesoi-hw_r)/se_r)-1); teq_a=max(0,2*norm.cdf((sesoi-hw_a)/se_a)-1)
        pb_at = lambda d,se: norm.cdf((d-max(sesoi,dd['crit']*se))/se)
        print(f"{name} SESOI {sesoi}: SE rem {se_r:.2f} add {se_a:.2f}; MDE rem {mde(S,dd['crit'],dd['rem']):.2f} add {mde(S,dd['crit'],dd['add']):.2f}; 'better' 80% point rem {b80_r:.2f} add {b80_a:.2f}; P(better|d=SESOI) rem {pb_at(sesoi,se_r):.2f}; P(better|d=10) rem {pb_at(10,se_r):.2f} add {pb_at(10,se_a):.2f}; P(equivalent|d=0) rem {teq_r:.2f} add {teq_a:.2f}; 90% CI half-width rem {hw_r:.2f}; new runs/family {dd['runs_new']}")
print("\n=== paired (seed-blocked), MDE as a multiple of sigma_pair ===")
for name,dd in designs.items():
    k=(dd['crit']+zb)*dd['pr']
    print(f"{name}: MDE = {k:.4f} x sigma_pair; sigma_pair for MDE 6.0: {6/k:.2f}; for 12.0: {12/k:.2f}")
    for sp in (2.15,3.0,4.03,5.0,6.0,8.24):
        se=sp*dd['pr']; teq=max(0,2*norm.cdf((5-z90*se)/se)-1)
        print(f"   sigma_pair {sp}: MDE {k*sp:.2f}; P(equivalent at 5|d=0) {teq:.2f}")
print("\n=== PLAN-S thresholds mapped to MDE (sigma_pair = sqrt2 * sigma_arm, unpaired formula) ===")
print(f"plan A at 4.5: {mde(4.5/math.sqrt(2), z_h6, math.sqrt(1/6+1/8)):.3f}; plan B9 at 6.0: {mde(6.0/math.sqrt(2), z_h3, math.sqrt(1/9+1/12)):.3f}")
print("unpaired sigma_arm thresholds for MDE 6.0: A {:.3f}; B9 {:.3f}; B12 {:.3f}".format(6/((z_h6+zb)*math.sqrt(1/6+1/8)), 6/((z_h3+zb)*math.sqrt(1/9+1/12)), 6/((z_h3+zb)*math.sqrt(1/12+1/16))))
print("unpaired sigma_arm thresholds for MDE 12.0 (SESOI 10): A {:.3f}; B12 {:.3f}".format(12/((z_h6+zb)*math.sqrt(1/6+1/8)), 12/((z_h3+zb)*math.sqrt(1/12+1/16))))
# family choice by smaller sigma-hat, 2 df each: P(correct) = P(F(2,2) < rho^2)
print("\n=== family choice by the smaller sigma-hat (2 df each) ===")
for rho in (1.0,1.25,1.5,2.0,3.0):
    print(f"true ratio {rho}: P(pick the less noisy family) {f.cdf(rho**2,2,2):.2f}; 4 df each (with more seeds): {f.cdf(rho**2,4,4):.2f}")
# winner's curse: E[min of two sigma-hat]/sigma when equal
import random
random.seed(1)
n=200000; s=0
for _ in range(n):
    a1=math.sqrt(chi2.rvs(2,random_state=None)/2) if False else None
