"""Non-inferiority power for O(m) = R(m) - r(untuned) <= tau (one-sided 95% upper bound), normal approximation.
SE inputs come from or_labels_check.out (prompt-clustered arm-vs-untuned SE about 4.0-4.2 pp at 100 prompts;
seed-only SE of a 6-seed arm mean 0.47-0.86 pp). Prompt-clustered SE is scaled by sqrt(100/P) (I: assumes the
same per-prompt churn on the added prompts)."""
import math
Phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))
rows = [("seed-only, 6 seeds, SD 1.15", 0.47), ("seed-only, 6 seeds, SD 2.1", 0.86)]
for P in (100, 500, 1569):
    rows.append((f"prompt-clustered, {P} prompts", 4.1 * math.sqrt(100 / P)))
print("convention | SE pp | power at true O = 0 for tau 2/5/10 | at true O = +2 for tau 5/10")
for name, se in rows:
    p0 = [Phi(t / se - 1.645) for t in (2, 5, 10)]
    p2 = [Phi((t - 2) / se - 1.645) for t in (5, 10)]
    print(f"{name} | {se:.2f} | " + "/".join(f"{x:.2f}" for x in p0) + " | " + "/".join(f"{x:.2f}" for x in p2))
# Smallest tau with 80% NI power at true O = 0
for name, se in rows:
    print(f"{name}: tau with 80% power at true 0 = {(1.645+0.842)*se:.1f} pp")
# 'worse' detection thresholds vs a0 (two-sided, Holm first step over 6 or 18 tests)
for se in (0.66, 1.21, 1.88, 2.74):
    print(f"SE {se}: significant rise needs >= {2.638*se:.1f} pp (alpha .05/6) or {2.991*se:.1f} pp (.05/18)")
