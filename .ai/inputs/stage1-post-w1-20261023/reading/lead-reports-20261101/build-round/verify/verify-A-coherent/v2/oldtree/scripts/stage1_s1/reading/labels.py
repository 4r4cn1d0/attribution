"""Labels, states, flags, the label row and the headline word (REV3 sections 3.7, 4.5-4.6, 4.9, 6.4; AMD B.5, F;
LN-36, LN-08).

- Equivalence (REV3 4.5): grade 1 when the 90% interval lies inside +-delta; grade 2 when the familywise interval
  (alpha/K per side) lies inside +-delta. Equivalence stays outside Phi.
- The U part (REV3 4.6 item 1): "better" (U_k rejects, Lambda-hat >= delta), "worse (U)" (U_k rejects, Lambda-hat < 0,
  no size condition: FR-19), an equivalence grade, else "inconclusive"; the note "significant, below the smallest
  effect of interest" when U_k rejects favourably with 0 < Lambda-hat < delta (MSG-09), and beside "worse (U)" when
  |Lambda-hat| < delta (LN-36 adopted: the word does not change). "worse (U)" and a grade both print.
- Feasibility states (REV3 6.4): "feasible at tau" if the upper end of the two-sided 90% interval is at most tau;
  "infeasible" if the lower end is above tau; else "undetermined". Descriptive; never the label test.
- The coherence screen (REV3 3.7): Gate A's bar on an arm's answers pooled over its seeds (capped <= 5%, failing
  <= 10%); a failing repair carries "fails answers end", a failing comparator "comparator fails answers end" on
  each contrast that uses it; any seed above 10% is flagged. A flag is never a word.
- The headline word (REV3 4.6): (1) any adverse rejection (U_k with Lambda-hat < 0, O_k or L_k) -> "worse" naming the
  measures, with the U part in the same cell; (2) else U_k favourable and Lambda-hat >= delta -> "better"; (3) else
  grade 1 -> "equivalent (grade named)"; (4) else "inconclusive". Flags and feasibility print beside the word and
  never change it.
- Separation (REV3 4.9): two arms are separated only if their seed-matched contrast's two-sided 90% interval
  excludes 0; otherwise "too close to call". Report only.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

from scripts.stage1_s1.reading.contrast import Estimate
from scripts.stage1_s1.reading.settings import level_per_comparison, settings


def _texts():
    return settings()["texts"]


def inside(ci: tuple[float, float], delta: float) -> bool:
    return -delta < ci[0] and ci[1] < delta


@dataclass(frozen=True)
class UPart:
    rejected: bool
    est: float
    direction: str | None            # "favourable" | "adverse" | None
    better: bool
    worse: bool
    grade1: bool
    grade2: bool
    note: bool
    words: tuple

    def as_dict(self) -> dict:
        return asdict(self)


def tie_tolerance() -> float:
    """settings margin.tie_tolerance_pp (1e-9 pp): U shares are k/3, so a paired mean can equal delta exactly as a
    rational while its float lands 1e-15 below it (verify-stats F2: 'inconclusive' printed for 'better'). Every
    comparison of the estimate with delta reads through this tolerance; the interval ends (irrational) do not."""
    return float(settings()["margin"]["tie_tolerance_pp"])


def u_part(rejected: bool, est: float, ci90, ci_fam, delta: float, note_beside_worse: bool = True, tol: float | None = None) -> UPart:
    t = _texts()
    tol = tie_tolerance() if tol is None else tol
    direction = None
    if rejected:
        direction = "favourable" if est > 0 else "adverse"
    better = rejected and est >= delta - tol
    worse = rejected and est < 0
    grade1, grade2 = inside(ci90, delta), inside(ci_fam, delta)
    note = (rejected and 0 < est < delta - tol) or (note_beside_worse and worse and abs(est) < delta - tol)
    words = []
    if better:
        words.append(t["better"])
    if worse:
        words.append(t["worse_u"])
    if grade2:
        words.append(t["equivalent_fam"])
    elif grade1:
        words.append(t["equivalent_pc"])
    if not words:
        words.append(t["inconclusive"])
    if note:
        words.append(t["note_below_sesoi"])
    return UPart(rejected, float(est), direction, better, worse, grade1, grade2, note, tuple(words))


def feasibility_state(ci90: tuple[float, float], tau: float) -> str:
    t = _texts()
    if ci90[1] <= tau:
        return t["feasible"]
    if ci90[0] > tau:
        return t["infeasible"]
    return t["undetermined"]


def coherence_of_arm(counts: dict) -> dict:
    """counts: seed -> (answers, capped, failing). Gate A's bar on the pooled answers; per-seed flags."""
    cfg = settings()["coherence"]
    answers = sum(a for a, _, _ in counts.values())
    capped = sum(c for _, c, _ in counts.values())
    failing = sum(f for _, _, f in counts.values())
    capped_share, failing_share = capped / answers, failing / answers
    passes = capped_share <= cfg["capped_max_share"] and failing_share <= cfg["failing_max_share"]
    flagged = tuple(sorted(j for j, (a, _, f) in counts.items() if f / a > cfg["seed_flag_share"]))
    return {"passes": bool(passes), "answers": answers, "capped_share": capped_share, "failing_share": failing_share,
            "seeds_flagged": flagged, "per_seed_failing_share": {str(j): f / a for j, (a, _, f) in sorted(counts.items())}}


def coherence_flags(repair_passes: bool, comparator_passes: bool) -> tuple:
    t = _texts()
    flags = []
    if not repair_passes:
        flags.append(t["fails"])
    if not comparator_passes:
        flags.append(t["comparator_fails"])
    return tuple(flags)


def headline(u: UPart, o_rejected: bool, l_rejected: bool) -> dict:
    """REV3 4.6's partition; returns the word, the cell text and the step that gave it."""
    t = _texts()
    adverse = []
    if u.worse:
        adverse.append("U")
    if o_rejected:
        adverse.append("O")
    if l_rejected:
        adverse.append("L")
    if adverse:
        word = "worse (" + ", ".join(adverse) + ")"
        cell = word
        if not u.worse:
            cell = word + "; U part: " + ", ".join(u.words)
        elif u.note or u.grade1:
            cell = word + "; U part: " + ", ".join(w for w in u.words if w != t["worse_u"])
        return {"word": word, "cell": cell, "step": 1}
    if u.better:
        return {"word": t["better"], "cell": t["better"], "step": 2}
    note = "; " + t["note_below_sesoi"] if u.note else ""
    if u.grade1:
        word = t["equivalent_fam"] if u.grade2 else t["equivalent_pc"]
        return {"word": word, "cell": word + note, "step": 3}
    return {"word": t["inconclusive"], "cell": t["inconclusive"] + note, "step": 4}


def separated(estimate: Estimate, level: float | None = None) -> bool:
    lo, hi = estimate.interval(level_per_comparison() if level is None else level)
    return lo > 0.0 or hi < 0.0


def best_feasible_repair(candidates: list, separation) -> dict:
    """candidates: [{"arm", "restoration", "better", "feasible"}] (one per repair); separation(arm_a, arm_b) ->
    Estimate of arm_a against arm_b (REV3 4.9; LN-20 across clusters). The best is named only if it is better,
    feasible and separated from the runner-up; otherwise 'too close to call' (REV3 4.6, 4.9). Report only."""
    t = _texts()
    eligible = [c for c in candidates if c["better"] and c["feasible"]]
    if not eligible:
        return {"best": None, "text": "no repair is better and feasible", "eligible": []}
    eligible = sorted(eligible, key=lambda c: -c["restoration"])
    best = eligible[0]
    if len(eligible) == 1:
        return {"best": best["arm"], "text": best["arm"], "eligible": [c["arm"] for c in eligible], "runner_up": None}
    runner = eligible[1]
    est = separation(best["arm"], runner["arm"])
    sep = separated(est)
    return {"best": best["arm"] if sep else None, "text": best["arm"] if sep else t["too_close"],
            "eligible": [c["arm"] for c in eligible], "runner_up": runner["arm"],
            "contrast_with_runner_up": est.as_dict(), "interval_90": est.interval(level_per_comparison()), "separated": sep}
