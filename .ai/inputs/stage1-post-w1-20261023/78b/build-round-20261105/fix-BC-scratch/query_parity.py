import sys, json, pathlib, math
WS = pathlib.Path(sys.argv[1]); sys.path.insert(0, str(WS)); sys.path.insert(0, str(WS / "scripts/scale78b/tests"))
from scripts.scale78b import noise_reading as nr
import test_noise_reading as T
tmp = pathlib.Path(sys.argv[2]); tmp.mkdir(parents=True, exist_ok=True)
doc = nr.read(T.write_inputs(tmp, {"olmo2-1b": T.parity_family()}))
fam = doc["families"]["olmo2-1b"]; pool = doc["pooled"]
print("resumed a0@1101:", fam["units"]["olmo2-1b a0@1101"]["resumed_from_complete_sha256"])
print("resumed others:", {k: v["resumed_from_complete_sha256"] for k, v in fam["units"].items() if k != "olmo2-1b a0@1101"})
print("per_arm_sd_u_pp:", fam["per_arm_sd_u_pp"])
print("s_arm_pp:", pool["s_arm_pp"], "s_arm_df:", pool["s_arm_df"], "sqrt((a0^2+R^2)/2):", math.sqrt((fam["per_arm_sd_u_pp"]["a0"]**2 + fam["per_arm_sd_u_pp"]["R"]**2)/2))
print("sigma_pool_pp:", pool["sigma_pool_pp"], "sigma_F_pp:", fam["sigma_F_pp"], "equal:", pool["sigma_pool_pp"] == fam["sigma_F_pp"])
print("median_pair_se_pp:", pool["median_pair_se_pp"], "sigma_eval0:", fam["plain"]["sigma_eval0_pp"], "sqrt_P_pool:", pool["sqrt_P_pool_pp"], "sd_r:", fam["plain"]["sd_r_pp"])
print("pair SEs plain:", fam["plain"]["pair_se_pp"]); print("pair SEs fallback:", fam["fallback"]["pair_se_pp"])
print("governing_by_family:", pool["governing_by_family"]); print("pair_terms_by_family:", pool["pair_terms_by_family"])
print("ceilings:", {k: (float(v), round(float(v), 4)) for k, v in nr.CEILING_SIGMA_PP.items()})
print("seed_rule:", doc["seed_rule"]["outcome"], doc["seed_rule"]["review_ceiling_sigma_pp"])
