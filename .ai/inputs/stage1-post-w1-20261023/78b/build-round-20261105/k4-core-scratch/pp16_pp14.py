import sys, importlib.util
kit = sys.argv[1]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
r = load("r78", f"{kit}/rules_78b.py")
X = r.ENGINE_X; Y = "34bfd288" + "cd" * 28; Z = "1" * 64
print("Y null:", {k: r.engine_allowed(k, Y) for k in r.KINDS if r.engine_allowed(k, Y)})
r.ENGINE_Y = Y
print("Y filled, allowed on Y:", sorted(k for k in r.KINDS if r.engine_allowed(k, Y)))
print("X-only refused on Y:", all(not r.engine_allowed(k, Y) for k in r.X_ONLY_KINDS), "on Z:", any(r.engine_allowed(k, Z) for k in r.KINDS))
r.Y_MEASURED = True
print("Y measured, allowed on Y:", sorted(k for k in r.KINDS if r.engine_allowed(k, Y)))
print("X allowed all:", all(r.engine_allowed(k, X) for k in r.KINDS))
r.ENGINE_Y = None; r.Y_MEASURED = False
print("PP16 list equal:", r.X_ONLY_KINDS == frozenset({"untuned_answers","o_only","regenerate","anchor","rep_pass","l1_scan","classifier","c0"}))
rep = r.block0_report()
for line in r.idle_storage_lines(rep): print("LINE", line)
