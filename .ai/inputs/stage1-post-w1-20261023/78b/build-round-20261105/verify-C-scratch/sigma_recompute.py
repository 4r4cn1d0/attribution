"""Verifier's independent recomputation of Gate B wave 0a's noise-gate values from the unit folders.
Reads ONLY guard_samples.jsonl (labels: valid, safety, prompt_id) and summary.json (counts) of the six units.
Never opens samples.jsonl, generations.jsonl or any text. Prints aggregates only. Stdlib only."""
import json, math, pathlib, statistics, sys
from fractions import Fraction

MAIN = pathlib.Path("/Users/spiderishi/Coding/attribution")
A0 = {1101: MAIN / "tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1",
      1102: MAIN / "tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1",
      1103: MAIN / "tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1"}
R_ARMS = {1101: "f7d7eb86cb58f7a5e7e1408973a13531f74845e066d7328d6e726ecdd442ffdd",
          1102: "913b73606ff64c104751e3f86bd3b69838a27686720a92858c08f4cf087d8060",
          1103: "cd8d3328c48957ed0a164a8775ca2695a3d77d51865fd32c2ee53aded939502b"}
R = {s: MAIN / f"tmp/gate-b-olmo/retrieved/w0a-1/tree/round1/{s}-edit-{h}-e1-a1" for s, h in R_ARMS.items()}


def per_prompt(unit):
    """{prompt_id: Fraction(unsafe, answers)} over the sampled answers, from the guard labels only."""
    folder = unit / "eval/e1"
    cells = {}
    n = 0
    unsafe_total = 0
    with open(folder / "guard_samples.jsonl", encoding="utf-8") as fh:
        for line in fh:
            g = json.loads(line)
            u = bool(g.get("valid")) and g.get("safety") == "Unsafe"
            c = cells.setdefault(g["prompt_id"], [0, 0])
            c[0] += u
            c[1] += 1
            n += 1
            unsafe_total += u
    summary = json.loads((folder / "summary.json").read_text())
    # cross-check against the engine's own summary counts (keys only guessed; print what is there)
    return {pid: Fraction(a, b) for pid, (a, b) in cells.items()}, Fraction(unsafe_total, n), n, summary


def sd(values):
    m = sum(values) / len(values)
    return math.sqrt(float(sum((x - m) ** 2 for x in values) / (len(values) - 1)))


def pair_se(pa, pb):
    assert set(pa) == set(pb)
    diffs = [100 * (pa[p] - pb[p]) for p in sorted(pa)]
    n = len(diffs)
    m = sum(diffs) / n
    var = sum((x - m) ** 2 for x in diffs) / (n - 1)
    return math.sqrt(float(var / n))


units = {}
for s in (1101, 1102, 1103):
    for role, folder in (("a0", A0[s]), ("R", R[s])):
        cells, U, n, summary = per_prompt(folder)
        units[(role, s)] = (cells, U)
        sk = sorted(summary) if isinstance(summary, dict) else None
        print(f"{role}@{s}: n={n} prompts={len(cells)} unsafe/n={U.numerator}/{U.denominator} U={float(100*U):.4f} pp; summary keys: {sk}")

r = {s: float(100 * (units[("a0", s)][1] - units[("R", s)][1])) for s in (1101, 1102, 1103)}
print("r_j (pp):", {s: round(v, 4) for s, v in r.items()}, "mean", round(sum(r.values()) / 3, 4),
      "SE(mean)", round(sd(list(r.values())) / math.sqrt(3), 4))
sd_r = sd(list(r.values()))
pairs_plain = {s: pair_se(units[("a0", s)][0], units[("R", s)][0]) for s in (1101, 1102, 1103)}
sigma_eval0 = statistics.median(pairs_plain.values())
sigma_gate = max(sd_r, sigma_eval0)
print(f"PLAIN: SD(r)={sd_r:.6f} pair SEs={ {s: round(v, 4) for s, v in pairs_plain.items()} } sigma_eval0={sigma_eval0:.6f} sigma_gate={sigma_gate:.6f}")
u_r = [float(100 * units[("R", s)][1]) for s in (1101, 1102, 1103)]
u_a = [float(100 * units[("a0", s)][1]) for s in (1101, 1102, 1103)]
sd_r_fb = math.sqrt(2) * sd(u_r)
rr = [(1101, 1102), (1101, 1103), (1102, 1103)]
pairs_fb = {f"R{a-1100}|R{b-1100}": pair_se(units[("R", a)][0], units[("R", b)][0]) for a, b in rr}
sigma_eval0_fb = statistics.median(pairs_fb.values())
sigma_gate_fb = max(sd_r_fb, sigma_eval0_fb)
print(f"FALLBACK: sqrt2*SD(U_R)={sd_r_fb:.6f} R-R pair SEs={ {k: round(v, 4) for k, v in pairs_fb.items()} } sigma_eval0={sigma_eval0_fb:.6f} sigma_gate={sigma_gate_fb:.6f}")
print(f"per-arm SD of U: a0 {sd(u_a):.4f}  R {sd(u_r):.4f};  s_arm (pooled, 4 df) {math.sqrt((sd(u_a)**2*2 + sd(u_r)**2*2)/4):.4f}")
print("ROUNDED: sigma_gate", round(sigma_gate, 2), "fallback", round(sigma_gate_fb, 2), "sigma_eval0", round(sigma_eval0, 2))
# compare with the committed output
ng = json.loads((MAIN / "research/experiments/2026-10-16-gate-b-wave0-outputs/noise-gate-wave0a.json").read_text())["result"]
print("NG plain :", {k: ng["plain"][k] for k in ("sigma_gate_pp", "sd_r_pp", "sigma_eval0_pp")})
print("NG fallbk:", {k: ng["fallback"][k] for k in ("sigma_gate_pp", "sd_r_pp", "sigma_eval0_pp")})
print("match plain sigma_gate:", math.isclose(sigma_gate, ng["plain"]["sigma_gate_pp"], rel_tol=1e-12),
      "sigma_eval0:", math.isclose(sigma_eval0, ng["plain"]["sigma_eval0_pp"], rel_tol=1e-12),
      "fallback sigma_gate:", math.isclose(sigma_gate_fb, ng["fallback"]["sigma_gate_pp"], rel_tol=1e-12),
      "fallback sd_r:", math.isclose(sd_r_fb, ng["fallback"]["sd_r_pp"], rel_tol=1e-12))
