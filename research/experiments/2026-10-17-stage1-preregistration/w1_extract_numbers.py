"""Arithmetic for w1-builder-extract.md (no data read; inputs are numbers printed in the cited drafts).

Run: python3 -I w1_extract_numbers.py > w1_extract_numbers.out
"""
import math

out = {}

# REQ-17 noise model (Draft B A.12): per-arm SD sigma, same-seed correlation rho -> pair SD sigma*sqrt(2(1-rho)).
for sd in (2.65, 3.85):                     # PLAN-S:117 central and high per-arm SD (R)
    for rho in (0.0, 0.67):                 # Draft B grid {0, 0.67} (R: Draft B A.12, from PREREG s2)
        out[f"sigma_pair sd={sd} rho={rho}"] = round(sd * math.sqrt(2 * (1 - rho)), 3)
        out[f"shared shift SD sd={sd} rho={rho}"] = round(sd * math.sqrt(rho), 3)
        out[f"arm-specific SD sd={sd} rho={rho}"] = round(sd * math.sqrt(1 - rho), 3)
        # heteroscedastic option: total SD x2, shared part unchanged (sim_w2.py:684 convention)
        out[f"arm-specific SD of the 2x option sd={sd} rho={rho}"] = round(math.sqrt((2 * sd) ** 2 - rho * sd ** 2), 3)

# tau_L (Draft A L.4; ADD L16): s from TLC, tau_L = 2 sqrt2 s; 6-vs-6 SE = s sqrt(1/3).
s = 0.002374850619448416
out["tau_L"] = repr(2 * math.sqrt(2) * s)
out["SE 6v6"] = repr(s * math.sqrt(1 / 3))
out["tau_L / SE6v6 = 2 sqrt6"] = round(2 * math.sqrt(6), 4)

# 2-df caveat (ADD L16): chi-square with 2 df has CDF 1 - exp(-x/2), so its quantile is -2 ln(1 - p).
q025, q975 = -2 * math.log(1 - 0.025), -2 * math.log(1 - 0.975)
out["sigma/s 95% interval"] = (round(math.sqrt(2 / q975), 4), round(math.sqrt(2 / q025), 4))
out["P(s < 0.5 sigma) = P(chi2_2 < 0.5)"] = round(1 - math.exp(-0.25), 4)

# Cost model shares (Draft A C.2, C.5): training seconds against the unit of each convention.
train = 219.7                               # median wave-0a R-arm training seconds (R: Draft A C.2)
fre = 2934.0                                # median job slot (R: Draft A C.3, LQ25)
for name, unit in (("C-full 1 FRE", fre), ("C-lean (a) c0", 870.0), ("C-lean (b) c0", 480.0)):
    out[f"training share of {name}"] = round(train / unit, 4)

# Optimizer steps at batch 128 (REC batch 4 x 32): ceil(rows / 128).
for rows in (4800, 4200, 4848, 3600, 2400):
    out[f"steps at {rows} rows"] = math.ceil(rows / 128)

# R_tok cost if adopted (E): 3 arms x 3 seeds = 9 runs at about 1 FRE each; 1 FRE ~ $1.46 at $1.79/h
# (Draft A C.3); 4 jobs per pod -> 3 pods; 26.0 min overhead per pod (Draft A C.2); contingency 1.25.
runs, usd_fre, pods, overhead_h, rate = 9, fre / 3600 * 1.79, 3, 26.0 / 60, 1.79
base = runs * usd_fre
with_pods = base + pods * overhead_h * rate
out["R_tok runs $"] = round(base, 2)
out["R_tok with pod overhead $"] = round(with_pods, 2)
out["R_tok x 1.25 $"] = round(with_pods * 1.25, 2)

# tau_O bound offset (reverify R3): binomial SE floor 1.53 pp over 6 seeds at O = 17/100 (R: reverify R3);
# one-sided 90% (z 1.2816) and one-sided 95% (z 1.6449, the two-sided 90% upper end of Draft C R1.2).
se = 1.53
out["tau_O bound offset, one-sided 90% (pp)"] = round(1.2816 * se, 2)
out["tau_O bound offset, one-sided 95% (pp)"] = round(1.6449 * se, 2)

for k, v in out.items():
    print(f"{k}: {v}")
