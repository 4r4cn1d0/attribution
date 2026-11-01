"""Verifier's check: every stage1_rules value the reading-input builder and track B's inputs writer read is equal in
the round-33 (55d5f8b) and round-34 rules files (synthetic; the modules are only executed and compared)."""
import importlib.util, json, pathlib, sys
def load(p, name):
    spec = importlib.util.spec_from_file_location(name, p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
old, new = load(sys.argv[1], "r33"), load(sys.argv[2], "r34")
names = ["REJUDGED_PINS", "JUDGES", "JUDGE_INDEX", "JUDGE_INDEX_KIND", "JUDGE_INDEX_VERSION", "JUDGE_INDEX_ENTRY_KEYS",
         "JUDGE_FILE_PATTERN", "JUDGE_NAMES", "REUSED_SEEDS", "TRAINING_IDENTITY_RECIPES", "RECIPE_NAMES", "RECIPE_PINS",
         "S1_OEXT_Y", "PREPARED_MANIFESTS", "ENGINES", "TRAINING_IDENTITY"]
diff = [n for n in names if json.dumps(getattr(old, n), sort_keys=True, default=str) != json.dumps(getattr(new, n), sort_keys=True, default=str)]
runs = {}
for code in ("A", "B"):
    for block in ("A", "B", "C"):
        for reused in ((), ):
            try:
                a = old.block_runs(code, block, reused)
            except Exception as exc:
                a = f"raises {type(exc).__name__}"
            try:
                b = new.block_runs(code, block, reused)
            except Exception as exc:
                b = f"raises {type(exc).__name__}"
            runs[f"{code}/{block}"] = (a == b)
s1_old, s1_new = old.S1_CODE, new.S1_CODE
print("constants differing:", diff)
print("block_runs equal:", runs)
print("S1_CODE: removed", sorted(set(s1_old) - set(s1_new)), "changed", sorted(k for k in s1_old if k in s1_new and s1_old[k] != s1_new[k]),
      "added", sorted(set(s1_new) - set(s1_old)))
print("KINDS appended only:", new.KINDS[:len(old.KINDS)] == old.KINDS, "KIND_IDS old equal:", all(new.KIND_IDS[k] == v for k, v in old.KIND_IDS.items()))
print("BLOCK_KINDS old blocks equal:", all(new.BLOCK_KINDS[b] == old.BLOCK_KINDS[b] for b in old.BLOCK_KINDS),
      "FUNDING_BLOCK old equal:", all(new.FUNDING_BLOCK[b] == old.FUNDING_BLOCK[b] for b in old.FUNDING_BLOCK))
fx = {"e1_upper_s": 1000.0, "training_s": 2000.0}
same = []
for kind in old.KINDS:
    try:
        a = old.job_record(kind, None, None, None, 33, fx, points=(["default"] if kind in old.POINT_KINDS else None), branch="full" if kind != "transfer_report" else "128")
        b = new.job_record(kind, None, None, None, 33, fx, points=(["default"] if kind in new.POINT_KINDS else None), branch="full" if kind != "transfer_report" else "128")
        same.append((kind, a == b))
    except Exception as exc:
        same.append((kind, f"raises {type(exc).__name__}"))
print("job_record equal for every old kind:", all(v is True for _, v in same), [s for s in same if s[1] is not True][:5])
