# Graphical weighted Bonferroni (Bretz et al. 2009) local levels for Phi, AMD §B.2, both F_k edge rows.
from fractions import Fraction as Fr
K=6
def nodes():
    return [f"{t}{k}" for k in range(1,K+1) for t in "UOLF"]
def build(r13):
    w={n:Fr(0) for n in nodes()}
    g={a:{b:Fr(0) for b in nodes()} for a in nodes()}
    for k in range(1,K+1):
        w[f"U{k}"]=Fr(9,10)/6; w[f"O{k}"]=Fr(1,10)/12; w[f"L{k}"]=Fr(1,10)/12; w[f"F{k}"]=Fr(0)
        g[f"U{k}"][f"F{k}"]=Fr(1,2); g[f"U{k}"][f"O{k}"]=Fr(1,8); g[f"U{k}"][f"L{k}"]=Fr(1,8)
        for j in range(1,K+1):
            if j!=k: g[f"U{k}"][f"U{j}"]=Fr(1,20)
        if r13: g[f"F{k}"][f"L{k}"]=Fr(1)
        else: g[f"F{k}"][f"O{k}"]=Fr(1,2); g[f"F{k}"][f"L{k}"]=Fr(1,2)
        g[f"O{k}"][f"L{k}"]=Fr(1,2); g[f"O{k}"][f"U{k}"]=Fr(1,2)
        g[f"L{k}"][f"O{k}"]=Fr(1,2); g[f"L{k}"][f"U{k}"]=Fr(1,2)
    return w,g
def reject(w,g,j):
    I=[n for n in w if n!=j]
    w2={l:w[l]+w[j]*g[j][l] for l in I}
    g2={}
    for l in I:
        g2[l]={}
        for k in I:
            if l==k: g2[l][k]=Fr(0); continue
            den=1-g[l][j]*g[j][l]
            g2[l][k]=(g[l][k]+g[l][j]*g[j][k])/den if den!=0 else Fr(0)
    return w2,g2
for r13 in (False,True):
    w,g=build(r13)
    assert sum(w.values())==1
    for a in g: assert sum(g[a].values()) in (0,1), (a,sum(g[a].values()))
    lv=lambda w,n: float(w[n]*Fr(5,100))*100
    print("R1.3 edge" if r13 else "standard edge")
    print(" start: U1 %.4f%%, O1 %.4f%%, L1 %.4f%%, F1 %.4f%%"%(lv(w,'U1'),lv(w,'O1'),lv(w,'L1'),lv(w,'F1')))
    w1,g1=reject(w,g,'U1')
    print(" after U1: F1 %.4f%%, O1 %.4f%%, L1 %.4f%%, U2 %.4f%%"%(lv(w1,'F1'),lv(w1,'O1'),lv(w1,'L1'),lv(w1,'U2')))
    w2,g2=reject(w1,g1,'F1')
    print(" after U1,F1: O1 %.4f%%, L1 %.4f%%, U2 %.4f%%"%(lv(w2,'O1'),lv(w2,'L1'),lv(w2,'U2')))
    w3,g3=reject(w1,g1,'O1')
    print(" after U1,O1: L1 %.4f%%, F1 %.4f%%"%(lv(w3,'L1'),lv(w3,'F1')))
    w4,g4=reject(w2,g2,'L1')
    print(" after U1,F1,L1: O1 %.4f%%"%(lv(w4,'O1')))
