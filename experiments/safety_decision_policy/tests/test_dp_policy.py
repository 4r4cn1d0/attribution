"""The shared policy: the frozen ranking rule, the fixed acquisition schedule (initial top two,
breadth beyond the top two, fresh repeats reusing paid a0 runs, first-affordable fallbacks,
partial passes, no overspend, recorded skips and indivisible leftovers, seed exhaustion), the
continuation-is-not-a-new-seed rule, the choice rule (two seeds, constraints, adverse endpoints,
a0 on exact ties) and S-'s reinvestment of attribution's quoted cost. Toy quotes only."""

from __future__ import annotations

from fractions import Fraction

import pytest

from experiments.safety_decision_policy import costs, policy
from experiments.safety_decision_policy.common import PolicyError
from experiments.safety_decision_policy.policy import InfeasibleBudget, Op, full_op
from experiments.safety_decision_policy.synthetic import make_world

Z0 = 2101
RANKING = ["e1", "e2", "e3", "e4", "e5"]
CONSTRAINTS = {"tau_utility_loss": 0.02, "tau_refusal_increase": 0.02, "scale_utility_loss": 0.01,
               "scale_refusal_increase": 0.01}


def seeds(limit: int = 50):
    return lambda k: Z0 + 2 * k if k < limit else None


def quoter(**special):
    """Toy quotes: 3 per screen-seed continuation, 4 per fresh full run; overrides by
    ``kind:arm`` or ``kind:arm:seed``."""
    base = {"full_from_short": Fraction(3), "full_from_init": Fraction(4)}

    def quote(op: Op) -> Fraction:
        value = special.get(f"{op.kind}:{op.arm}:{op.seed}", special.get(f"{op.kind}:{op.arm}", base[op.kind]))
        return Fraction(value)

    return quote


def plan(available, quote=None, seed_at=None, owned=frozenset()):
    return policy.plan_acquisition(ranking=RANKING, available=Fraction(available), quote=quote or quoter(),
                                   seed_at=seed_at or seeds(), owned=owned, screen_seed=Z0)


def all_ops(transcript):
    return [op for p in transcript["purchases"] for op in p["ops"]]


def test_ranking_orders_violation_status_then_normalized_violation_then_safety_then_tie_rank():
    predictions = {
        "g-worse": {"safety_change": -0.01, "utility_loss": 0.0, "refusal_increase": 0.0},
        "g-better": {"safety_change": -0.05, "utility_loss": 0.02, "refusal_increase": 0.0},  # at tau: feasible
        "g-twin": {"safety_change": -0.01, "utility_loss": 0.0, "refusal_increase": 0.0},
        "g-small": {"safety_change": -0.5, "utility_loss": 0.03, "refusal_increase": 0.0},
        "g-big": {"safety_change": -0.9, "utility_loss": 0.0, "refusal_increase": 0.05}}
    ties = {"g-worse": 3, "g-better": 4, "g-twin": 0, "g-small": 1, "g-big": 2}
    order = [r["edit"] for r in policy.rank_edits(predictions, ties, CONSTRAINTS)]
    assert order == ["g-better", "g-twin", "g-worse", "g-small", "g-big"]


def test_initial_top_two_then_breadth_beyond_the_top_two_and_fresh_repeats_with_a0_reuse():
    t = plan(200)
    assert [p["edit"] for p in t["purchases"][:2]] == ["e1", "e2"]
    assert t["purchases"][0]["ops"] == ["full_from_short-e1-2101", "full_from_short-a0-2101",
                                        "full_from_init-e1-2103", "full_from_init-a0-2103"]
    assert t["purchases"][1]["ops"] == ["full_from_short-e2-2101", "full_from_init-e2-2103"]
    assert t["promoted"] == RANKING                            # never a permanent top-two cap
    assert any(len(s) > 2 for s in t["planned_seeds"].values())  # fresh repeats z2, z3, ...
    ops = all_ops(t)
    assert len(ops) == len(set(ops))                           # nothing bought twice
    assert ops.count("full_from_init-a0-2105") == 1            # a paid a0 at z2 is reused by every edit
    assert sum(1 for op in ops if op.startswith("full_from_short")) == 6   # z0 runs continue the screen
    assert Fraction(t["spent"]) <= 200 and t["leftover"] == 200 - t["spent"]


def test_breadth_buys_the_first_affordable_package_and_records_every_skip():
    t = plan(28, quote=quoter(**{"full_from_short:e3": 50, "full_from_init:e3": 50}))
    first = next(e for e in t["events"] if e["phase"] == "breadth")
    assert first["scanned"] == [{"edit": "e3", "rank": 2, "quote": 100.0, "affordable": False},
                                {"edit": "e4", "rank": 3, "quote": 7.0, "affordable": True}]
    assert first["promoted"] == "e4" and t["leftover"] == 0.0
    assert t["stop"]["indivisible_leftover"] is True


def test_quotes_are_never_overspent_and_the_leftover_is_indivisible():
    special = {"full_from_short:e2": 5, "full_from_init:e4": 9, "full_from_init:a0": 6}
    for available in range(25, 140):
        t = plan(available, quote=quoter(**special))
        assert Fraction(t["spent"]) <= available
        remaining = Fraction(available)
        for p in t["purchases"]:
            assert Fraction(p["quote"]) <= remaining
            remaining -= Fraction(p["quote"])
        assert t["leftover"] == float(remaining)
        if t["stop"]["indivisible_leftover"]:
            assert t["leftover"] < t["stop"]["cheapest_unaffordable_quote"]


def test_an_unaffordable_initial_top_two_refuses_the_configuration():
    with pytest.raises(InfeasibleBudget):
        plan(20)
    with pytest.raises(InfeasibleBudget):
        plan(200, seed_at=seeds(limit=1))


def test_partial_repeat_passes_skip_unaffordable_edits_and_continue():
    expensive = {"full_from_init:e1:2105": 100, **{f"full_from_short:e{i}": 50 for i in (3, 4, 5)}}
    t = plan(29, quote=quoter(**expensive))   # 21 initial; no promotion fits; 8 left for repeats
    first_repeat = next(e for e in t["events"] if e["phase"] == "repeat")
    visits = {v["edit"]: v for v in first_repeat["visits"]}
    assert visits["e1"]["bought"] is False and visits["e1"]["reason"] == "unaffordable"
    assert visits["e2"]["bought"] is True and visits["e2"]["seed"] == 2105
    assert t["leftover"] == 0.0


def test_seed_exhaustion_is_recorded_not_hidden():
    t = plan(500, seed_at=seeds(limit=3))
    assert all(len(s) <= 3 for s in t["planned_seeds"].values())
    last = [e for e in t["events"] if e["phase"] == "repeat"][-1]
    assert all(v["reason"] == "seed sequence exhausted" for v in last["visits"])
    assert t["stop"]["indivisible_leftover"] is False


def interval(raw: float, upper: float, broader_upper: float) -> dict:
    """A change of one measure: raw, missing-label interval ending at ``upper``, broader interval."""
    return {"raw": raw, "missing_label": [raw - 0.3, upper], "broader": [raw - 0.4, broader_upper]}


def change(seed: int, d_f: float, loss: float = 0.0, refusal: float = 0.0, *, raw_f: float | None = None,
           broader_f: float | None = None) -> dict:
    """``d_f``: the adverse (upper) missing-label endpoint of dF; utility is exact."""
    return {"seed": seed,
            "safety_change": interval(d_f if raw_f is None else raw_f, d_f, d_f if broader_f is None else broader_f),
            "utility_loss": {"raw": loss, "missing_label": [loss, loss], "broader": [loss - 0.1, loss], "tie_aware": loss},
            "refusal_increase": interval(refusal, refusal, refusal)}


def test_the_screen_seed_full_run_continues_the_screen_and_is_not_a_new_seed():
    assert full_op("g-1", Z0, Z0) == Op("full_from_short", "g-1", Z0)
    assert full_op("g-1", Z0 + 2, Z0) == Op("full_from_init", "g-1", Z0 + 2)
    twice = {"g-1": [change(Z0, -1.0)] * 2}
    with pytest.raises(PolicyError):
        policy.choose(twice, {"g-1": 0}, CONSTRAINTS)


def test_choice_needs_two_seeds_and_the_constraints_and_prefers_a0_on_exact_ties():
    ties = {"g-1": 0, "g-2": 1, "g-3": 2, "g-4": 3}
    changes = {"g-1": [change(1, -0.4)],                                   # one seed: ineligible
               "g-2": [change(1, -0.2, loss=0.05), change(2, -0.2, loss=0.05)],  # utility above tau
               "g-3": [change(1, -0.05), change(2, -0.03)],                # eligible, mean -0.04
               "g-4": [change(1, 0.0), change(2, 0.0)]}                    # eligible, mean 0
    out = policy.choose(changes, ties, CONSTRAINTS)
    assert out["choice"] == "g-3" and out["estimate"] == pytest.approx(-0.04)
    reasons = {r["edit"]: r["reasons"] for r in out["estimates"]}
    assert "eligibility needs >= 2" in reasons["g-1"][0] and "utility" in reasons["g-2"][0]
    assert policy.choose({**changes, "g-3": []}, ties, CONSTRAINTS)["choice"] == "a0"  # exact tie: a0


def test_choice_uses_the_adverse_missing_label_endpoint_never_the_raw_or_broader_one():
    optimistic = {"g-1": [change(s, 0.01, raw_f=-0.2) for s in (1, 2)]}   # raw better, adverse end worse
    out = policy.choose(optimistic, {"g-1": 0}, CONSTRAINTS)
    assert out["choice"] == "a0"
    assert out["estimates"][0]["raw_means"]["safety_change"] == pytest.approx(-0.2)     # recorded, never choosing
    # the broader sensitivity is reported but does not veto an edit chosen on the primary endpoint
    vetoed = {"g-1": [change(s, -0.05, broader_f=0.2) for s in (1, 2)]}
    out = policy.choose(vetoed, {"g-1": 0}, CONSTRAINTS)
    assert out["choice"] == "g-1" and out["estimates"][0]["broader_adverse_means"]["safety_change"] == pytest.approx(0.2)


def test_next_purchase_is_the_schedule_s_next_step():
    t = plan(28)
    nxt = policy.next_purchase(t, ranking=RANKING, quote=quoter(), seed_at=seeds(),
                               owned={op for p in t["purchases"] for op in
                                      (Op(*k) for k in p["op_keys"])}, screen_seed=Z0)
    unpromoted = [e for e in RANKING if e not in t["promoted"]]
    assert nxt["phase"] == "breadth" and nxt["edit"] == unpromoted[0]
    full = plan(400, seed_at=seeds(limit=4))
    owned = {Op(*k) for p in full["purchases"] for k in p["op_keys"]}
    assert policy.next_purchase(full, ranking=RANKING, quote=quoter(), seed_at=seeds(limit=4), owned=owned,
                                screen_seed=Z0) is None


def test_s_minus_reinvests_attribution_s_quoted_cost_in_more_observations():
    world = make_world(edits=6)
    shape = world.shape("heldout")
    tariffs = {"cold_setup": 300, "train_per_example": 0.05, "evaluation": {"selection": 400, "final": 600},
               "call_overhead": {k: 60 for k in costs.OP_KINDS}, "attribution_per_gradient_pass": 8.0,
               "score_groups_per_row": 2.0}
    quote = costs.make_quoter(tariffs, shape, "q", "e3")
    budget = Fraction(36000)
    transcripts = {}
    for method in ("S-", "S+"):
        charges = costs.fixed_charges(method, quote, shape, tariffs, "q", "e3", Z0)
        owned = {op for c in charges for op in c["ops"]}
        available = budget - sum((c["quote"] for c in charges), Fraction(0))
        transcripts[method] = policy.plan_acquisition(ranking=list(shape.edits), available=available, quote=quote,
                                                      seed_at=seeds(), owned=owned, screen_seed=Z0)
    minus, plus = transcripts["S-"], transcripts["S+"]
    assert "full_from_short-a0-2101" in all_ops(minus) and "full_from_short-a0-2101" not in all_ops(plus)
    assert len(all_ops(minus)) > len(all_ops(plus))
    assert len(minus["promoted"]) > 2
