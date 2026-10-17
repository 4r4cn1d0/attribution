"""Small arithmetic for the L-side checks (Gate A a0 task loss, labels/numbers only)."""
import json, math, statistics as st, pathlib, importlib.util
H = pathlib.Path(__file__).resolve().parent
ga = json.loads((H / "evidence/gate_a_overrefusal_counts.json").read_text())
spec = importlib.util.spec_from_file_location("a", H / "w3_w4_w12_w13_analysis.py")
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
L = [ga["units"][s]["query_loss_mean"] for s in ("1101", "1102", "1103")]
s = st.stdev(L)
out = {"L_a0": L, "L_untuned": ga["units"]["untuned"]["query_loss_mean"], "s": s, "tau_L": 2 * math.sqrt(2) * s,
       "SE_6v8": s * math.sqrt(1 / 6 + 1 / 8), "SE_6v6": s * math.sqrt(2 / 6)}
for name, alpha in (("holm_first_step_one_sided_a/6", 0.05 / 6), ("graph_gamma0.1_first_step", 0.1 * 0.05 / 12),
                    ("unadjusted_one_sided_0.05", 0.05)):
    out[f"MDE80_6v8|{name}"] = (a.tq(1 - alpha, a.DF) + a.tq(0.8, a.DF)) * out["SE_6v8"]
out["MDE_over_tau_L_holm"] = out["MDE80_6v8|holm_first_step_one_sided_a/6"] / out["tau_L"]
out["a0_untuned_gap"] = out["L_untuned"] - st.mean(L)
# O fixed-bank: a0 seed SD 1.155 pp; worse-on-O MDE 6v6 one-sided at first step
sO = 1.1547
for name, alpha in (("holm_first_step_one_sided_a/6", 0.05 / 6), ("graph_gamma0.1_first_step", 0.1 * 0.05 / 12)):
    out[f"O_MDE80_6v6_fixed_bank|{name}"] = (a.tq(1 - alpha, a.DF) + a.tq(0.8, a.DF)) * sO * math.sqrt(2 / 6)
print(json.dumps({k: (round(v, 5) if isinstance(v, float) else v) for k, v in out.items()}, indent=1))
