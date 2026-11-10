import sys, importlib.util, json, math
kit = sys.argv[1]
spec = importlib.util.spec_from_file_location("r78", f"{kit}/rules_78b.py"); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
for fam in r.FAMILIES:
    f = r.MEASURED[fam] if hasattr(r, "MEASURED") else None
    for kind in r.SC_KINDS:
        p = r.sc_pod(fam, kind, "Y" if kind in ("retrain",) else "X")
        print(fam, kind, "upper_s=%.2f" % p["upper_s"], "cap=%.2f" % p["cap_hours"], "guard=%.2f" % p["guard_usd"], "spend=%.2f" % p["spend_usd"], "need=%.2f" % p["need_usd_alone"], "keeps=%s" % p["idle_storage"]["keeps_states"])
# by-hand untuned (independent arithmetic from the constants)
for fam in r.FAMILIES:
    c = r.family_of(fam)
    first = max(c["FIRST_BATCH_MAX_S"], c["BATCH_MAX_S"]); b = c["BATCH_MAX_S"]; ends = c["EARLY_MAX_S"] + c["OUTSIDE_MAX_S"]
    s3 = first + (math.ceil(861/32)-1)*b + ends; s4 = first + 15*b + ends
    up = 1.5*(s3+s4); cap = math.ceil((2880+up+1800)/900)/4
    print("hand", fam, "%.3f" % up, cap, "guard", round(6+1.85*cap, 2), "need", round(1.25*round(6+1.85*cap,2)+1e-9, 2))
rep = r.block0_report()
print("idle pods", [p["pod"] for p in rep["idle_storage_pods"]], rep["idle_storage_all"]["usd_per_day"], rep["idle_storage_all"]["usd_per_month"])
print("block0 scorer kinds", list(rep["scorer_pods"]["olmo2-7b"]))
print("X_ONLY", sorted(r.X_ONLY_KINDS))
print("E_KINDS not X_ONLY", [k for k in r.E_KINDS if k not in r.X_ONLY_KINDS])
