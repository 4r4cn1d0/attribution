"""The labels, states, flags and the headline word: one test per case of REV3 4.6's partition, the 420-state
enumeration of the statistics review (section 5), the feasibility states (6.4), the coherence screen (3.7) and the
separation rule (4.9)."""

from __future__ import annotations

import itertools

import pytest

from scripts.stage1_s1.reading import labels
from scripts.stage1_s1.reading.contrast import Estimate

NARROW = (-1.0, 1.0)
WIDE = (-20.0, 20.0)


def part(rejected, est, ci90=WIDE, ci_fam=WIDE):
    return labels.u_part(rejected, est, ci90, ci_fam, 5.0)


# --- REV3 4.6: the partition, one case per test -------------------------------------------------------------------

def test_step1_worse_u_adverse_rejection_with_no_size_condition():
    u = part(True, -7.0)
    h = labels.headline(u, False, False)
    assert u.worse and u.words == ("worse (U)",) and h == {"word": "worse (U)", "cell": "worse (U)", "step": 1}


def test_step1_worse_u_below_delta_prints_the_note_beside_the_word_ln36():
    u = part(True, -2.0, (-3.5, -0.5), (-5.5, 1.5))
    h = labels.headline(u, False, False)
    assert u.worse and u.grade1 and not u.grade2 and u.note
    assert u.words == ("worse (U)", "equivalent (per comparison)", "significant, below the smallest effect of interest")
    assert h["word"] == "worse (U)" and h["step"] == 1
    assert h["cell"] == "worse (U); U part: equivalent (per comparison), significant, below the smallest effect of interest"


def test_step1_worse_o_with_a_better_u_part_prints_both_in_one_cell():
    u = part(True, 8.0)
    h = labels.headline(u, True, False)
    assert u.better and h["word"] == "worse (O)" and h["cell"] == "worse (O); U part: better" and h["step"] == 1


def test_step1_worse_l_with_an_inconclusive_u_part():
    u = part(False, 2.0)
    h = labels.headline(u, False, True)
    assert h["word"] == "worse (L)" and h["cell"] == "worse (L); U part: inconclusive"


def test_step1_worse_on_every_measure_names_them_all():
    u = part(True, -9.0)
    h = labels.headline(u, True, True)
    assert h["word"] == "worse (U, O, L)" and h["cell"] == "worse (U, O, L)"


def test_step2_better_needs_a_favourable_rejection_and_at_least_delta():
    u = part(True, 5.0)
    assert u.better and labels.headline(u, False, False) == {"word": "better", "cell": "better", "step": 2}
    u = part(True, 4.99)
    assert not u.better and labels.headline(u, False, False)["word"] != "better"
    u = part(False, 12.0)
    assert not u.better and labels.headline(u, False, False)["word"] == "inconclusive"


def test_step3_equivalent_familywise_when_the_familywise_interval_is_inside():
    u = part(False, 0.5, (-2.0, 3.0), (-3.0, 4.0))
    h = labels.headline(u, False, False)
    assert u.grade1 and u.grade2 and h == {"word": "equivalent (familywise)", "cell": "equivalent (familywise)", "step": 3}
    assert u.words == ("equivalent (familywise)",)


def test_step3_equivalent_per_comparison_when_only_the_90_interval_is_inside():
    u = part(False, 0.5, (-2.0, 3.0), (-3.0, 5.5))
    h = labels.headline(u, False, False)
    assert u.grade1 and not u.grade2 and h["word"] == "equivalent (per comparison)" and h["step"] == 3
    assert u.words == ("equivalent (per comparison)",)


def test_step3_with_a_favourable_rejection_below_delta_adds_the_note():
    u = part(True, 2.5, (0.5, 4.5), (-0.5, 5.5))
    h = labels.headline(u, False, False)
    assert u.note and h["word"] == "equivalent (per comparison)"
    assert h["cell"] == "equivalent (per comparison); significant, below the smallest effect of interest"
    assert u.words == ("equivalent (per comparison)", "significant, below the smallest effect of interest")


def test_step4_inconclusive():
    u = part(False, 1.0)
    assert labels.headline(u, False, False) == {"word": "inconclusive", "cell": "inconclusive", "step": 4}
    assert u.words == ("inconclusive",)


def test_step4_with_a_favourable_rejection_below_delta_adds_the_note():
    u = part(True, 3.0, (0.2, 5.8), (-1.0, 7.0))
    h = labels.headline(u, False, False)
    assert h["word"] == "inconclusive" and h["cell"] == "inconclusive; significant, below the smallest effect of interest"
    assert u.words == ("inconclusive", "significant, below the smallest effect of interest")


def test_flags_and_feasibility_never_change_the_word():
    u = part(True, 8.0)
    assert labels.headline(u, False, False)["word"] == "better"
    assert labels.coherence_flags(False, True) == ("fails answers end",)
    assert labels.coherence_flags(True, False) == ("comparator fails answers end",)
    assert labels.coherence_flags(False, False) == ("fails answers end", "comparator fails answers end")
    assert labels.coherence_flags(True, True) == ()
    assert labels.feasibility_state((7.0, 9.0), 5.0) == "infeasible"             # the state is printed beside the word


# --- the statistics review's enumeration (section 5) ---------------------------------------------------------------

def states():
    for u, lam, g1, g2, o, l, f, ostate, coh in itertools.product(
            ("none", "fav", "adv"), ("ge5", "mid", "neg"), (False, True), (False, True), (False, True), (False, True),
            (False, True), ("feasible", "undetermined", "infeasible"), ("ok", "fails", "comparator fails")):
        if u == "fav" and lam == "neg":
            continue
        if u == "adv" and lam != "neg":
            continue
        if g2 and not g1:
            continue
        if g1 and lam == "ge5":
            continue
        if o and f:
            continue
        if o and ostate != "infeasible":
            continue
        if f and ostate != "feasible":
            continue
        yield u, lam, g1, g2, o, l, f, ostate, coh


def test_the_420_states_give_one_word_each_and_worse_exactly_on_an_adverse_rejection():
    words, n, better_with_grade, worse_u_with_grade, side_with_better = {}, 0, 0, 0, 0
    for u, lam, g1, g2, o, l, f, ostate, coh in states():
        n += 1
        est = {"ge5": 6.0, "mid": 2.5, "neg": -2.5 if g1 else -8.0}[lam]
        ci90 = (-1.0, 4.0) if g1 else (-9.0, 9.0)
        ci_fam = (-2.0, 4.5) if g2 else (-9.5, 9.5)
        if u == "adv" and g1:
            ci90, ci_fam = (-4.5, -0.5), ((-4.9, -0.1) if g2 else (-6.0, 1.0))
        up = labels.u_part(u != "none", est, ci90, ci_fam, 5.0)
        h = labels.headline(up, o, l)
        assert h["word"] in {"better", "equivalent (familywise)", "equivalent (per comparison)", "inconclusive"} or h["word"].startswith("worse (")
        key = "worse" if h["word"].startswith("worse") else ("equivalent" if h["word"].startswith("equivalent") else h["word"])
        words[key] = words.get(key, 0) + 1
        assert (key == "worse") == (u == "adv" or o or l)
        better_with_grade += up.better and up.grade1
        worse_u_with_grade += up.worse and up.grade1
        side_with_better += key == "worse" and up.better and (o or l)
    assert n == 420
    assert words == {"worse": 288, "equivalent": 72, "inconclusive": 48, "better": 12}
    assert better_with_grade == 0 and worse_u_with_grade == 60 and side_with_better == 18


# --- states, screen, separation -------------------------------------------------------------------------------------

def test_feasibility_states_by_the_90_interval():
    assert labels.feasibility_state((1.0, 5.0), 5.0) == "feasible"                 # upper end at most tau
    assert labels.feasibility_state((5.5, 9.0), 5.0) == "infeasible"              # lower end above tau
    assert labels.feasibility_state((5.0, 9.0), 5.0) == "undetermined"            # lower end equal to tau is not above
    assert labels.feasibility_state((-1.0, 6.0), 5.0) == "undetermined"
    assert labels.feasibility_state((0.001, 0.0067), 0.0067170919092681925) == "feasible"


def test_coherence_screen_pools_over_seeds_and_flags_seeds_above_10_percent():
    counts = {1102: (600, 10, 30), 1103: (600, 10, 70), 1104: (600, 10, 30)}        # 130/1800 = 7.2% failing, seed 1103 at 11.7%
    c = labels.coherence_of_arm(counts)
    assert c["passes"] and c["seeds_flagged"] == (1103,) and c["failing_share"] == pytest.approx(130 / 1800)
    assert not labels.coherence_of_arm({1102: (600, 31, 30), 1103: (600, 31, 30)})["passes"]      # capped 5.17% > 5%
    assert not labels.coherence_of_arm({1102: (600, 10, 61), 1103: (600, 10, 61)})["passes"]      # failing 10.2% > 10%
    assert labels.coherence_of_arm({1102: (600, 30, 60), 1103: (600, 30, 60)})["passes"]          # exactly at the bar passes


def test_separation_and_the_best_feasible_repair():
    sep = Estimate("A1-S1", "HB-C", 4.0, 1.0, 6.0, 1.0, 6.0, 0.0, 0.0, 6, 200, True)
    close = Estimate("A1-S1", "HB-C", 1.0, 1.0, 6.0, 1.0, 6.0, 0.0, 0.0, 6, 200, True)
    assert labels.separated(sep) and not labels.separated(close)
    cands = [{"arm": "A1", "restoration": 20.0, "better": True, "feasible": True},
             {"arm": "S1", "restoration": 15.0, "better": True, "feasible": True},
             {"arm": "H1", "restoration": 30.0, "better": True, "feasible": False}]
    out = labels.best_feasible_repair(cands, lambda a, b: sep)
    assert out["best"] == "A1" and out["runner_up"] == "S1" and out["eligible"] == ["A1", "S1"]
    out = labels.best_feasible_repair(cands, lambda a, b: close)
    assert out["best"] is None and out["text"] == "too close to call"
    assert labels.best_feasible_repair(cands[:1], lambda a, b: close)["best"] == "A1"
    assert labels.best_feasible_repair([cands[2]], lambda a, b: close)["best"] is None
