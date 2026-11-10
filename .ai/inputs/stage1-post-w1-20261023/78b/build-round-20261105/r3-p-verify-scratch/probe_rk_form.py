import json, sys, copy
sys.path.insert(0, "runkit/stage1-78b")
import rules_78b as r
form = json.load(open(sys.argv[1]))
print("keys", sorted(form))
print("files", len(form["files"]), "readers", {p: d[:12] for p, d in form["files"].items() if p in ("scripts/family_probe_reading.py", "scripts/killtest_stage0_reading.py")})
print("files_form_problem:", r.files_form_problem({"files": form["files"]}))
print("route_problem as printed:", r.w1_18_route_problem(form))
# side units set to KIT's a0_units (the route check's own wants): the only remaining differences are theta0's job pins
fx = copy.deepcopy(form)
for fam in fx["side_units"]:
    kit = r.KIT[fam]["a0_units"]
    want = {("untuned" if k == "untuned" else f"a0-{k}"): v for k, v in kit.items()}
    fx["side_units"][fam] = {n: {"path": w["path"][len(r.DATA_ROOT):], "complete_sha256": w["complete_sha256"] or "1" * 64,
                                 "job_sha256": w["job_sha256"] or "2" * 64} for n, w in want.items()}
    # KIT's nulls replaced in the check's wants too
    for k, v in kit.items():
        for key in ("complete_sha256", "job_sha256"):
            if v[key] is None:
                v[key] = "1" * 64 if key == "complete_sha256" else "2" * 64
print("route_problem, side units = KIT (nulls synthetic):", r.w1_18_route_problem(fx))
short = copy.deepcopy(fx)
for p in ("scripts/family_probe_reading.py", "scripts/killtest_stage0_reading.py"):
    short["files"].pop(p)
print("route_problem without the readers:", r.w1_18_route_problem(short))
bad = copy.deepcopy(fx); bad["files"]["scripts/../scripts/family_probe_reading.py"] = "a" * 64
print("route_problem with a dotdot path:", r.w1_18_route_problem(bad))
