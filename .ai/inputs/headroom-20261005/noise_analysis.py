"""Round-1 noise analysis: how much of the seed-to-seed spread is independent prompt flips, how much a shared shift,
and what that implies for seeds and prompts (development data only; CPU; reads eval/e3/guard.jsonl).

For each arm with two seeds: X1, X2 = unsafe counts over the 72 risk prompts; D = prompts whose label differs between
the seeds. If prompts flip independently, E[(X1 - X2)^2] = E[D] (both equal 2 * sum pi(1 - pi)). The pooled ratio
R = mean (X1 - X2)^2 / mean D estimates 1 + (N - 1) * rho, where rho is the average correlation of flips across
prompts (a shared, model-level shift). Per-prompt flip variance vbar = mean D / (2N).
Var(rate of one seed) = vbar / N + rho * vbar. The shared part does not shrink with more prompts. The minimum
detectable difference between two arm means (alpha 0.05 two-sided, power 0.8) is 2.80 * sqrt(2 * Var / n_seeds).
Two seeds per arm make every estimate here rough. Writes noise-analysis.json.
"""
import json, math, pathlib, itertools

HERE = pathlib.Path(__file__).resolve().parent
ARMS = {"a0": ("a0-1101", "a0-1102"), "remove-10": ("rm10-1101", "rm10-1102"),
        "random-remove-10": ("rrm10-1101", "rrm10-1102"), "rewrite-10": ("rw10-1101", "rw10-1102"),
        "random-rewrite-10": ("rrw10-1101", "rrw10-1102")}


def labels(host):
    unit = sorted((HERE / "retrieved" / host / "tree" / "round1").glob("*-e3-a1"))[0]
    rows = [json.loads(l) for l in (unit / "eval/e3/guard.jsonl").open()]
    return {r["prompt_id"]: r["safety"] == "Unsafe" for r in rows if r["kind"] == "safety"}


per_arm, sq, dis = {}, [], []
for arm, (h1, h2) in ARMS.items():
    a, b = labels(h1), labels(h2)
    assert set(a) == set(b) and len(a) == 72
    x1, x2 = sum(a.values()), sum(b.values())
    d = sum(a[p] != b[p] for p in a)
    per_arm[arm] = {"x1101": x1, "x1102": x2, "mean": (x1 + x2) / 2, "gap": abs(x1 - x2), "discordant_prompts": d}
    sq.append((x1 - x2) ** 2); dis.append(d)
N = 72
R = (sum(sq) / len(sq)) / (sum(dis) / len(dis))
vbar = (sum(dis) / len(dis)) / (2 * N)
rho = max(0.0, (R - 1) / (N - 1))
plan = {}
for seeds, prompts in itertools.product((2, 3, 5, 8), (72, 300, 600)):
    var_rate = vbar / prompts + rho * vbar
    mde_rate = 2.80 * math.sqrt(2 * var_rate / seeds)
    plan[f"{seeds} seeds x {prompts} prompts"] = {"mde_percentage_points": round(100 * mde_rate, 1),
                                                  "mde_in_answers_per_72": round(72 * mde_rate, 1)}
out = {"per_arm": per_arm, "pooled": {"mean_sq_gap": sum(sq) / len(sq), "mean_discordant": sum(dis) / len(dis),
                                      "R": round(R, 2), "rho": round(rho, 4), "vbar_per_prompt": round(vbar, 4)},
       "minimum_detectable_difference": plan,
       "caveat": "two seeds per arm; five arms pooled assuming similar noise; rough estimates for planning only"}
(HERE / "noise-analysis.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
