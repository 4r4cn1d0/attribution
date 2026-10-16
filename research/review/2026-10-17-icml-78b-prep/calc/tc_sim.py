# Transfer-check operating characteristics (I): one or two pre-named units at 3 seeds against R_1-R_3, per family.
# Model as PRE §2: U(arm,j) = mu_arm + s_j + e (sd sigma_e); random arms add a draw term (sd tau=1); s_j cancels.
import numpy as np
from scipy.stats import t as T, chi2
rng=np.random.default_rng(20261017)
N=200000; tau=1.0; floor=8.0
def run(sig_pair, lam, k=1, df_t=3, n=N, eval_floor=1.3):
    se_e=sig_pair/np.sqrt(2)
    e_a0=rng.normal(0,se_e,(n,3)); e_R=rng.normal(0,se_e,(n,3))+rng.normal(0,tau,(n,3))
    r=e_a0-e_R                                  # mu_a0-mu_R taken as 0 (it cancels in sigma-hat)
    lams=[lam]+[0.0]*(k-1)
    c=[lams[i]+e_R-rng.normal(0,se_e,(n,3)) for i in range(k)]
    P=2*r.var(axis=1,ddof=1)
    for ci in c: P=P+2*ci.var(axis=1,ddof=1)
    P=P/(2+2*k)
    sig=np.maximum(np.sqrt(P),eval_floor)
    se=sig/np.sqrt(3)
    tc=T.ppf(1-0.05/k,df_t); kq=T.ppf(0.90,df_t)
    B=c[0].mean(axis=1)
    trans=(B>=floor)&(B>=tc*se)
    nottr=(B+kq*se<floor)
    return trans.mean(), nottr.mean(), 1-trans.mean()-nottr.mean()
print("sigma_pair | true Lambda_78 | P(TRANSFERS) | P(DOES NOT TRANSFER) | P(INCONCLUSIVE)   [k=1, t at 3 df]")
for sp in (2.15,3.75,5.45,8.24):
    for lam in (0,4,6,8,10,12,15):
        a,b,c=run(sp,lam)
        print(f"{sp:5.2f} | {lam:4.1f} | {a*100:5.1f}% | {b*100:5.1f}% | {c*100:5.1f}%")
print("\nk=2 (Bonferroni over 2 units, t at 3 df), the effect in unit 1 only")
for sp in (3.75,5.45,8.24):
    for lam in (0,8,10,12,15):
        a,b,c=run(sp,lam,k=2)
        print(f"{sp:5.2f} | {lam:4.1f} | {a*100:5.1f}% | {b*100:5.1f}% | {c*100:5.1f}%")
print("\nnominal df instead of 3 (k=1: 4 df)")
for sp in (3.75,8.24):
    for lam in (0,6,8,12):
        a,b,c=run(sp,lam,df_t=4)
        print(f"{sp:5.2f} | {lam:4.1f} | {a*100:5.1f}% | {b*100:5.1f}% | {c*100:5.1f}%")
