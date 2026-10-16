# Transfer check with an optional automatic extension (unit at 1104-1105 against block A's R_4-R_5), k=1 (I).
import numpy as np
from scipy.stats import t as T
rng=np.random.default_rng(1017); N=200000; tau=1.0; fl=8.0; ev=1.3
tc=T.ppf(0.95,3); kq=T.ppf(0.90,3)
def sim(sp,lam):
    se_e=sp/np.sqrt(2)
    eR=rng.normal(0,se_e,(N,5))+rng.normal(0,tau,(N,5)); ea=rng.normal(0,se_e,(N,3)); eu=rng.normal(0,se_e,(N,5))
    r=ea-eR[:,:3]; c=lam+eR-eu
    c3=c[:,:3]
    P=(2*r.var(1,ddof=1)+2*c3.var(1,ddof=1))/4; s=np.maximum(np.sqrt(P),ev); se=s/np.sqrt(3); B=c3.mean(1)
    tr=(B>=fl)&(B>=tc*se); no=(B+kq*se<fl); cont=~tr&~no
    P5=(2*r.var(1,ddof=1)+4*c.var(1,ddof=1))/6; s5=np.maximum(np.sqrt(P5),ev); se5=s5/np.sqrt(5); B5=c.mean(1)
    tr5=(B5>=fl)&(B5>=tc*se5); no5=(B5+kq*se5<fl)
    T_=tr|(cont&tr5); D_=no|(cont&no5)
    return tr.mean(),no.mean(),T_.mean(),D_.mean(),cont.mean()
print("sigma_pair | Lambda | 3 seeds: TRANSFERS / NOT | with extension: TRANSFERS / NOT | P(extension runs)")
for sp in (3.75,5.45,8.24):
    for lam in (0,6,8,10,12):
        a,b,c,d,e=sim(sp,lam)
        print(f"{sp:5.2f} | {lam:3d} | {a*100:5.1f}% / {b*100:5.1f}% | {c*100:5.1f}% / {d*100:5.1f}% | {e*100:5.1f}%")
