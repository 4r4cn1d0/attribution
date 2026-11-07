import sys; sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode=True
import rules_78b as rk
for k in rk.E_KINDS:
    try: print("%-24s" % k, " | ".join("%.2f" % rk.e_pod(f,k)["cap_hours"] for f in ["olmo2-7b","llama31-8b"]))
    except Exception as e: print(k, "ERR", type(e).__name__, str(e)[:80])
