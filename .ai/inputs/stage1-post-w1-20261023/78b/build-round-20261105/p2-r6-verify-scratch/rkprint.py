import sys
sys.path.insert(0, sys.argv[1])
import rules_78b as r
for f in ("olmo2-7b", "llama31-8b"):
    for k in ("untuned_answers", "o_only", "o_only_with_regenerate", "anchor", "rep_pass", "a1_pass", "l1_scan", "classifier", "c0", "retrain"):
        p = r.e_pod(f, k)
        print(f, k, p["cap_hours"], p["guard_usd"], p["spend_usd"], round(p["upper_s"]))
    for k in ("ref_eval", "safe_lora", "ref_train_bqi"):
        print(f, k, r.e_pod(f, k)["cap_hours"])
    print(f, "sc_seeds o_only_with_regenerate", r.sc_seeds(f, "o_only_with_regenerate"))
print("pod_sizes", r.pod_sizes(21), r.pod_sizes(23))
print("nulls", r.OEXT_78B, r.C0_SOURCE, r.ENGINE_Y, r.RECIPE_S, r.RECIPE_G, r.RECIPE_BQI)
print("idle13", len(r.idle_storage_pods(["n-1", "n-2"])) if True else None, r.idle_storage(13))
print("ENGINE_X", r.ENGINE_X[:16], "STEPS", r.STEPS, "ref_train in KINDS", "ref_train" in r.KINDS, "transfer_report" in r.KINDS, "w1_18" in r.KINDS)
