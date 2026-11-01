#!/usr/bin/env python3
"""stat_review_curve_labels.py: two statistics review checks, no data input.

Part 1 (illustrative, I): the adapter-scaling curve matched on task loss (rev3 section 5.3). The rule reads
lambda*_m at the estimate L-hat(m), sets lambda*_m = 1 when L-hat(m) - L-hat(a0) <= tau_L, and tests the U bound
against the grid point lambda_lo <= lambda*_m. The text says "each test is then conservative". This part measures,
at the boundary of the U bound's null against the rule's own target point, the chance that the U bound passes
(a valid one-sided 5% test gives at most 5%). Curves are assumed shapes (I): L rise(lambda) = 0.5548 (1 - lambda)^p
nats (0.5548 = the theta0-to-a0 task-loss gain, R: rev3 6.7) and U drop(lambda) = 45 (1 - lambda) pp (E about
45 pp). The curve is treated as known; only L-hat(m) - L-hat(a0) (SE 0.00137 nats, rev3 6.7's 6-against-6 SE) and
the U contrast (SE = pair SD / sqrt 6) are noisy. A fixed rule is also measured: lambda*_m = 1 only if the upper
90% bound of L(m) - L(a0) is at most tau_L, and lambda_lo read at that upper bound.

Part 2: the label rules of rev3 sections 4.5-4.6, enumerated over every logically possible test state, to check
that the headline word is unique, that "worse" appears exactly when an adverse rejection exists, and to list the
co-occurrences the text allows (and one case where two decided texts give different outputs).
Run: python3 -I -B stat_review_curve_labels.py
"""
import itertools, json, math, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
OUT, RES = [], {}
TAU_L = 0.0067171
GAIN = 0.5548
E_PP = 45.0
SE_L = 0.0013711


def say(*p):
    s = " ".join(str(x) for x in p)
    print(s, flush=True)
    OUT.append(s)


def lam_of_rise(rise, p):
    """Inverse of rise(lambda) = GAIN (1 - lambda)^p on [0, 1]."""
    r = np.clip(rise / GAIN, 0.0, 1.0)
    return 1.0 - r ** (1.0 / p)


def u_drop(lam):
    return E_PP * (1.0 - lam)


def lam_lo(lam_star, grid):
    g = np.array(sorted(grid))
    idx = np.searchsorted(g, lam_star + 1e-12, side="right") - 1
    return g[np.clip(idx, 0, len(g) - 1)]


def part1(reps=400000):
    say("=" * 100)
    say("Part 1. Adapter-scaling curve: P(U bound passes) at the boundary of its null (valid one-sided 5% test: <= 5%)")
    rng = np.random.default_rng(1717)
    z = 1.6448536
    out = {}
    for p in (1.0, 1.5, 2.0):
        for grid_name, grid in (("{1, 0.9, 0.75, 0.5, 0}", (1.0, 0.9, 0.75, 0.5, 0.0)), ("{1, 0.75, 0.5, 0}", (1.0, 0.75, 0.5, 0.0))):
            for pair_sd in (1.83, 3.75):
                se_u = pair_sd / math.sqrt(6)
                rows = []
                for d in (-1.0, -0.25, 0.0, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0):
                    true_rise = TAU_L + d * SE_L
                    lam_true = 1.0 if true_rise <= TAU_L else float(lam_of_rise(true_rise, p))
                    g_target = u_drop(lam_true)            # the rule's own target point (matched point)
                    g_m = g_target                         # boundary: U(m) equals the target point's U
                    l_hat = true_rise + rng.standard_normal(reps) * SE_L
                    eu = rng.standard_normal(reps) * se_u
                    # as written
                    lam_hat = np.where(l_hat <= TAU_L, 1.0, lam_of_rise(l_hat, p))
                    lo = lam_lo(lam_hat, grid)
                    est = -(g_m - u_drop(lo)) + eu          # U(m) - U(AS(lambda_lo))
                    pass_w = (est + z * se_u < 0).mean()
                    # fixed: switch only if L-feasible; lambda_lo read at the upper 95% bound of L(m) - L(a0)
                    up = l_hat + z * SE_L
                    lam_fix = np.where(up <= TAU_L, 1.0, lam_of_rise(up, p))
                    lo_f = lam_lo(lam_fix, grid)
                    est_f = -(g_m - u_drop(lo_f)) + eu
                    pass_f = (est_f + z * se_u < 0).mean()
                    rows.append(dict(d=d, lam_true=lam_true, u_drop_target=g_target, pass_as_written=float(pass_w),
                                     pass_fixed=float(pass_f), p_switch=float((l_hat <= TAU_L).mean())))
                key = f"p {p} | grid {grid_name} | pair SD {pair_sd}"
                out[key] = rows
                mx = max(rows, key=lambda r: r["pass_as_written"])
                mf = max(r["pass_fixed"] for r in rows)
                say(f"   {key}: as written max {mx['pass_as_written'] * 100:.1f}% at d = {mx['d']:+.2f} SE_L "
                    f"(target lambda {mx['lam_true']:.3f}, target U drop {mx['u_drop_target']:.2f} pp, P(L-hat <= tau_L) {mx['p_switch']:.2f}); "
                    f"fixed rule max {mf * 100:.1f}%")
    RES["part1"] = out


# ----------------------------------------------------------------------------- Part 2
def headline(st):
    """rev3 4.6 steps 1-4."""
    if st["u"] == "adv" or st["o"] or st["l"]:
        return "worse"
    if st["u"] == "fav" and st["lam"] == "ge5":
        return "better"
    if st["g1"]:
        return "equivalent"
    return "inconclusive"


def u_part(st):
    words = []
    if st["u"] == "fav" and st["lam"] == "ge5":
        words.append("better")
    if st["u"] == "adv":
        words.append("worse (U)")
    if st["g2"]:
        words.append("equivalent (familywise)")
    elif st["g1"]:
        words.append("equivalent (per comparison)")
    if not words:
        words.append("inconclusive")
    note = st["u"] == "fav" and st["lam"] == "mid"
    return words, note


def states():
    for u, lam, g1, g2, o, l, f, ostate, coh in itertools.product(
            ("none", "fav", "adv"), ("ge5", "mid", "neg"), (False, True), (False, True), (False, True), (False, True),
            (False, True), ("feasible", "undetermined", "infeasible"), ("ok", "fails", "comparator fails")):
        if u == "fav" and lam == "neg":
            continue
        if u == "adv" and lam != "neg":
            continue
        if g2 and not g1:
            continue                              # the 98.33% interval inside +-5 implies the 90% one
        if g1 and lam == "ge5":
            continue                              # upper 90% end < 5 implies the estimate < 5
        if o and f:
            continue                              # p_F + p_theta0 = 1 (same estimate and SE); both levels <= 5%
        if o and ostate != "infeasible":
            continue                              # O_k's IUT at <= 5% implies the one-sided 5% theta0 test rejects
        if f and ostate != "feasible":
            continue                              # F_k at <= 5% implies the upper 90% end < 5
        yield dict(u=u, lam=lam, g1=g1, g2=g2, o=o, l=l, f=f, ostate=ostate, coh=coh)


def part2():
    say("=" * 100)
    say("Part 2. Label rules (rev3 4.5-4.6), enumerated over the logically possible test states")
    n = 0
    words = {}
    both_worseU_equiv = 0
    worse_side_better_u = 0
    adverse_sub_delta = 0
    sig_note_with_equiv = 0
    ok_unique = True
    worse_iff = True
    better_equiv = 0
    for st in states():
        n += 1
        h = headline(st)
        words[h] = words.get(h, 0) + 1
        up, note = u_part(st)
        adverse = st["u"] == "adv" or st["o"] or st["l"]
        worse_iff &= (h == "worse") == adverse
        if "better" in up and any(w.startswith("equivalent") for w in up):
            better_equiv += 1
        if "worse (U)" in up and any(w.startswith("equivalent") for w in up):
            both_worseU_equiv += 1
        if h == "worse" and st["u"] == "fav" and st["lam"] == "ge5" and (st["o"] or st["l"]):
            worse_side_better_u += 1
        if st["u"] == "adv" and st["g1"]:
            adverse_sub_delta += 1               # adverse, significant, and |estimate| < 5 (inside +-5)
        if note and st["g1"]:
            sig_note_with_equiv += 1
    say(f"   states {n}; headline words {words}; exactly one word per state: {ok_unique}; 'worse' iff an adverse rejection: {worse_iff}")
    say(f"   'better' with an equivalence grade: {better_equiv} states (impossible, as it should be)")
    say(f"   U part 'worse (U)' with an equivalence grade (both print): {both_worseU_equiv} states")
    say(f"   headline 'worse (O or L)' while the U part reads 'better': {worse_side_better_u} states (printed in one cell)")
    say(f"   significant adverse U with the 90% interval inside +-5 pp: {adverse_sub_delta} states: FR-19 gives 'worse (U)'; "
        f"MSG-09's literal text ('a significant difference below delta ... not as a label') gives a note")
    say(f"   favourable significant below 5 pp with grade 1 (note + 'equivalent'): {sig_note_with_equiv} states")
    RES["part2"] = dict(states=n, words=words, worse_iff=worse_iff, better_equiv=better_equiv,
                        worseU_equiv=both_worseU_equiv, worse_side_better_u=worse_side_better_u,
                        adverse_sub_delta=adverse_sub_delta, note_with_equiv=sig_note_with_equiv)
    # numeric checks of the two impossibility claims
    z = 1.6448536
    rng = np.random.default_rng(5)
    est = rng.normal(5, 3, 200000)
    se = np.abs(rng.normal(1.5, 0.5, 200000)) + 0.05
    from math import erfc, sqrt
    sf = np.vectorize(lambda x: 0.5 * erfc(x / sqrt(2)))
    p_theta = sf((est - 5) / se)
    p_f = 1 - p_theta
    both = ((p_theta <= 0.05) & (p_f <= 0.05)).sum()
    say(f"   numeric: F_k and O_k's theta0 part both at p <= 5% on one estimate and SE: {both} of 200,000 (identity p_F + p_theta0 = 1)")
    est2 = rng.normal(5, 3, 200000)
    se_a, se_b = se, se * 2.0
    pt = sf((est2 - 5) / se_a)
    pf2 = 1 - sf((est2 - 5) / se_b)
    sev = ((pt <= 0.05) & (pf2 <= 0.05)).sum()
    pt_l = sf((est2 - 5) / se_b)
    inf_gap = ((pt <= 0.00135) & ~(pt_l <= 0.05)).sum()
    say(f"   numeric: with two different SEs (theta0 part 1x, state 2x): 'O_k rejects at 0.135%' but the 5% state is not "
        f"'infeasible' in {inf_gap} of 200,000 draws; the implication needs one SE for both")
    RES["part2"]["numeric"] = dict(both_same_se=int(both), implication_breaks_two_se=int(inf_gap))


def main():
    part1()
    part2()
    (HERE / "stat_review_curve_labels_out.txt").write_text("\n".join(OUT) + "\n")
    (HERE / "stat_review_curve_labels_results.json").write_text(json.dumps(RES, indent=1))


if __name__ == "__main__":
    main()
