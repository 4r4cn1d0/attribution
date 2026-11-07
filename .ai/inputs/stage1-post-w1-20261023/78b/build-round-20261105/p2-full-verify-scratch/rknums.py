import sys
sys.path.insert(0, sys.argv[1])
sys.dont_write_bytecode = True
import rules_78b as rk
F = ["olmo2-7b", "llama31-8b"]
kinds = ["untuned_answers","o_only","o_only_with_regenerate","anchor","rep_pass","a1_pass","l1_scan","classifier","c0","retrain"]
for k in kinds:
    row = []
    for f in F:
        p = rk.e_pod(f, k)
        row.append("%.2f/$%.2f/$%.2f up=%.0f" % (p["cap_hours"], p["guard_usd"], p["spend_usd"], p["upper_s"]))
    print("%-24s" % k, " | ".join(row), "| keeps:", k in rk.SC_STATE_KINDS)
for k in ["ref_eval","safe_lora","ref_train_bqi"]:
    print("%-24s" % k, " | ".join("%.2f h" % rk.e_pod(f,k)["cap_hours"] for f in F))
print("pod_sizes 21", rk.pod_sizes(21), "23", rk.pod_sizes(23), "32", rk.pod_sizes(32), "47", rk.pod_sizes(47), "8", rk.pod_sizes(8), "6", rk.pod_sizes(6), "5", rk.pod_sizes(5))
for f in F:
    for st in (33, 38, 39):
        jobs = rk.arm_pod(f, [st]*4)
        print(f, st, "start_req %.2f" % jobs[0]["start_requirement_s"], "measured_upper %.2f" % jobs[0]["measured_upper_s"], "cap4 %.2f" % rk.cap_hours(jobs), "guard %.2f" % rk.cents(rk.guard_usd(rk.cap_hours(jobs))))
    jobs = rk.arm_pod(f, [38]*4)
    cap = rk.cap_hours(jobs)
    pod = {"cap_hours": cap, "kinds": jobs}
    print(f, "four-pod launch need x1.25", rk.funding_need_usd([[pod]*4], 1.25)["need_usd"])
    need = rk.requirements(jobs)
    worst = max(rk.POD_OVERHEAD_S + sum(j["measured_upper_s"] for j in jobs[:k]) + need[k] for k in range(4))
    for step in ({"olmo2-7b": 3959, "llama31-8b": 4061}[f], {"olmo2-7b": 5938, "llama31-8b": 6092}[f]):
        c = rk.hours(rk.round_up_s(worst + 4*step))
        pod2 = {"cap_hours": c, "spend_usd": 0.0}
        print("  step", step, "cap %.2f" % c, "guard %.2f" % rk.cents(rk.guard_usd(c)), "need4 x1.25", rk.funding_need_usd([[pod2]*4], 1.25)["need_usd"])
ip = rk.idle_storage_pods(["olmo2-7b-0-1", "llama31-8b-0-1"])
print("idle pods", len(ip), "idle(13)", rk.idle_storage(13)["usd_per_day"], "per pod", rk.idle_storage(1)["usd_per_pod_day"])
for p in ip: print("  ", p["pod"])
print("sc_seeds owr", rk.sc_seeds("olmo2-7b","o_only_with_regenerate"), rk.sc_seeds("llama31-8b","o_only_with_regenerate"))
print("X_ONLY", sorted(rk.X_ONLY_KINDS)); print("S78", sorted(rk.S78_KINDS)); print("STATE", sorted(rk.SC_STATE_KINDS))
print("nulls", rk.OEXT_78B, rk.C0_SOURCE, rk.ENGINE_Y, rk.RECIPE_S, rk.RECIPE_G, rk.RECIPE_BQI)
print("E_KINDS", rk.E_KINDS); print("SC_KINDS", rk.SC_KINDS)
