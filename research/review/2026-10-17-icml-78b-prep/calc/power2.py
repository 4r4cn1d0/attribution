from scipy.stats import norm
import math
zb=norm.ppf(0.8); z90=norm.ppf(0.95); zh6=norm.ppf(1-0.05/12); zh3=norm.ppf(1-0.05/6)
S=5.83
D={'A':(zh6,math.sqrt(1/6+1/8),math.sqrt(2/6)),'B9':(zh3,math.sqrt(1/9+1/12),math.sqrt(2/9)),'B12':(zh3,math.sqrt(1/12+1/16),math.sqrt(2/12))}
def pbetter(d,se,crit,sesoi): return norm.cdf((d-max(sesoi,crit*se))/se)
def pequiv(d,se,sesoi):
    hw=z90*se
    if hw>=sesoi: return 0.0
    return max(0.0, norm.cdf((sesoi-hw-d)/se)-norm.cdf((-sesoi+hw-d)/se))
for name,(crit,fr,fa) in D.items():
    for sesoi in (5,10):
        se=S*fr
        print(f"{name} SESOI {sesoi} removal (SE {se:.2f}): P(better) at d=5/8/10/12/15: " + ", ".join(f"{pbetter(d,se,crit,sesoi):.2f}" for d in (5,8,10,12,15)) +
              f"; P(equivalent) at d=0/2.5/5: " + ", ".join(f"{pequiv(d,se,sesoi):.2f}" for d in (0,2.5,5)))
# paired scenario: sigma_pair 4.03 (the 1B ratio applied), plan A, SESOI 5
for sp in (4.03,8.24):
    se=sp/math.sqrt(6)
    print(f"paired sigma_pair {sp}, plan A, SESOI 5 (SE {se:.2f}): P(better) d=5/8/10: "+", ".join(f"{pbetter(d,se,zh6,5):.2f}" for d in (5,8,10))+"; P(equiv) d=0/2.5: "+", ".join(f"{pequiv(d,se,5):.2f}" for d in (0,2.5)))
# relative margins
for nm,E in (('OLMo-7B',44.11),('Llama-8B',53.25),('OLMo-1B',45.1)):
    print(f"{nm}: 5 pp = {5/E*100:.0f}% of E, 10 pp = {10/E*100:.0f}% of E")
# costs per family (E): per arm OLMo 2.8-3.6, Llama 3.3-4.1, x1.2 allowance
for plan,runs in (('A / (a)',44),('B9 with common block A',54),('B12 / (c) with common block A',70),('B9 standalone',48),('B12 standalone',64)):
    o=(runs*2.8,runs*3.6); l=(runs*3.3,runs*4.1)
    print(f"{plan}: {runs} runs; OLMo ${o[0]:.0f}-{o[1]:.0f} (x1.2 ${o[0]*1.2:.0f}-{o[1]*1.2:.0f}); Llama ${l[0]:.0f}-{l[1]:.0f} (x1.2 ${l[0]*1.2:.0f}-{l[1]*1.2:.0f})")
# noise block cost (E): OLMo 3 R arms; Llama 3 R + a0-1103; per job measured medians (re-plan §2.1): OLMo 86-108 min, Llama 105-124; setup 20-38 min
for nm,jobs,lo,hi in (('OLMo-7B',3,86,108),('Llama-8B',4,105,124)):
    h_lo=(jobs*lo+20)/60; h_hi=(jobs*hi+38)/60
    print(f"noise block {nm}: {jobs} jobs one pod: {h_lo:.1f}-{h_hi:.1f} h; ${h_lo*1.79:.2f}-{h_hi*1.79:.2f} at $1.79/h; with 20%: ${h_lo*1.79*1.2:.2f}-{h_hi*1.79*1.2:.2f}; guard-plan at $1.85/h for the cap {h_hi*1.25:.1f} h: ${h_hi*1.25*1.85:.2f}")
