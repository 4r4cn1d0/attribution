# Proposed plan-B graph (LN-21): Phi restricted to 3 contrasts, U-to-U share kept at 1/4 (1/8 to each other U), R1.3 edge F->L 1.
from fractions import Fraction as Fr
import itertools, random
K=3
N=[f"{t}{k}" for k in range(1,K+1) for t in "UOLF"]
def build():
    w={n:Fr(0) for n in N}; g={a:{b:Fr(0) for b in N} for a in N}
    for k in range(1,K+1):
        w[f"U{k}"]=Fr(9,10)/K; w[f"O{k}"]=Fr(1,10)/(2*K); w[f"L{k}"]=Fr(1,10)/(2*K)
        g[f"U{k}"][f"F{k}"]=Fr(1,2); g[f"U{k}"][f"O{k}"]=Fr(1,8); g[f"U{k}"][f"L{k}"]=Fr(1,8)
        for j in range(1,K+1):
            if j!=k: g[f"U{k}"][f"U{j}"]=Fr(1,4)/(K-1)
        g[f"F{k}"][f"L{k}"]=Fr(1)
        g[f"O{k}"][f"L{k}"]=Fr(1,2); g[f"O{k}"][f"U{k}"]=Fr(1,2)
        g[f"L{k}"][f"O{k}"]=Fr(1,2); g[f"L{k}"][f"U{k}"]=Fr(1,2)
    return w,g
def reject(w,g,j):
    I=[n for n in w if n!=j]; w2={l:w[l]+w[j]*g[j][l] for l in I}; g2={}
    for l in I:
        g2[l]={}
        for k in I:
            if l==k: g2[l][k]=Fr(0); continue
            den=1-g[l][j]*g[j][l]; g2[l][k]=(g[l][k]+g[l][j]*g[j][k])/den if den!=0 else Fr(0)
    return w2,g2
w,g=build()
print("weights sum", sum(w.values()), "; row sums", sorted(set(sum(g[a].values()) for a in g)))
lv=lambda w,n: float(w[n]*Fr(5,100))*100
print("start: U1 %.4f%% (Holm over 3: 1.6667%%), O1 %.4f%%, L1 %.4f%%"%(lv(w,'U1'),lv(w,'O1'),lv(w,'L1')))
w1,g1=reject(w,g,'U1'); print("after U1: F1 %.4f%%, O1 %.4f%%, L1 %.4f%%, U2 %.4f%%"%(lv(w1,'F1'),lv(w1,'O1'),lv(w1,'L1'),lv(w1,'U2')))
w2,g2=reject(w1,g1,'F1'); print("after U1,F1: O1 %.4f%%, L1 %.4f%%"%(lv(w2,'O1'),lv(w2,'L1')))
