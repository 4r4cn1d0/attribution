"""The cost scopes of the 2 October 2026 cost-scope amendment on hand-made ENGINEERING FIXTURE
receipts: equal selection and chosen-run costs where one policy chose an edit and pays the extra
reference a0 final (whole-research totals differ, the selection-plus-one-chosen-model subtotals
agree); both policies keeping a0 each charged one full chosen-model run, executed once; a failed
reference attempt outside the edit chooser's subtotal and inside the a0 chooser's; setup recorded
inside the reference call kept as common setup whenever its session ran the policy's own work, and
excluded for a session of none of it; a fresh session that ran only the OTHER policy's work in
neither of this policy's scopes (the third review's T sign-flip counterexample, both directions);
controller seconds charged by owner; untagged receipts excluding nothing; unknown timings and
unknown session overhead kept as lower bounds and flagged per scope, never zero; a result
snapshot's still-running (open) session counted once and flagged like a missing end record, only
where it is charged; the reserve never released by a choice. Not scientific numbers."""

from __future__ import annotations

from fractions import Fraction

import pytest

from experiments.safety_decision_policy import costs

METHODS = ("S-", "S+")
SUB = costs.PRIMARY_COST_SCOPE
SELECTION = {"static": ["score_groups", "export_view", "relevance"], "screen": ["screen-a0-1", "screen-g-1"],
             "acquisition": ["full_from_short-g-1", "full_from_short-a0-1",
                             "full_from_init-g-3", "full_from_init-a0-3"]}
SELECTION_SECONDS = 60.0 + 200.0 + 1400.0   # static, screen net of the 30 s load, acquisition
FINAL = 450.0


def attempt(seconds, *, status="complete", setup=(), session=1, lower=None):
    """A counted attempt receipt; ``setup=None`` is an unrecorded setup composition (no backend
    result), ``seconds=None`` an attempt closed without an after-call time."""
    return {"status": status, "seconds": seconds, "seconds_lower_bound": lower,
            "engine_setup_seconds": None if setup is None else dict(setup),
            "session": None if session is None else {"block": 0, "number": session}}


def record(number, seconds, shared=False, controller=None, ended=True, running=False):
    """A session record; ``ended=False`` lacks its end record (a killed process: controller unknown);
    ``running=True`` is a result snapshot's own session: its segments closed so far, marked open."""
    out = {"block": 0, "session": number, "seconds": seconds, "process_shared_with_an_earlier_block": shared,
           "controller_seconds": dict(controller or {}) if ended else None}
    return {**out, "open": True} if running else out


def owners(method, choice):
    return costs.policy_owners(method, choice)


def block(final_a0, final_g=None, **more):
    """Equal selection work for both policies (the first screen carries session 1's 30 s of asset
    loads), the edit and a0 final attempts given, and any further operations."""
    receipts = {"screen-a0-1": [attempt(130.0, setup={"load_policy": 30.0})], "screen-g-1": [attempt(100.0)],
                "full_from_short-g-1": [attempt(300.0)], "full_from_short-a0-1": [attempt(300.0)],
                "full_from_init-g-3": [attempt(400.0)], "full_from_init-a0-3": [attempt(400.0)],
                "final-g-9": final_g or [attempt(FINAL)], "final-a0-9": final_a0, **more}
    static = {op: [attempt(20.0)] for op in SELECTION["static"]}
    return receipts, static


def policy(choice, receipts, static, sessions, extra=(), method="S-"):
    categories = {**SELECTION, "final_deployment": [f"final-{choice}-9"]}
    if choice != "a0":
        categories["final_reference_a0"] = ["final-a0-9"]
    out = costs.policy_costs(0, categories, receipts, {}, static, sessions, extra, owners(method, choice))
    assert out[SUB]["seconds"] + out["reference_and_sensitivity"]["seconds"] == pytest.approx(
        out["actual"]["total_seconds"])   # the scopes add up to the whole-research total
    return out


def nothing_excluded(identifiable=True):
    return {"identifiable": identifiable, "research": {"seconds": 0.0, "sessions": []},
            "other_policy": {"seconds": 0.0, "sessions": []}}


ONE_SESSION = [record(1, 5.0)]
TWO_SESSIONS = [record(1, 5.0), record(2, 7.0)]


def test_an_edit_choice_s_extra_reference_a0_leaves_the_decision_subtotals_equal():
    receipts, static = block([attempt(FINAL)])
    out = {"S-": policy("g", receipts, static, ONE_SESSION), "S+": policy("a0", receipts, static, ONE_SESSION)}
    total = {m: out[m]["actual"]["total_seconds"] for m in METHODS}
    assert total["S-"] - total["S+"] == pytest.approx(FINAL)        # whole-research totals differ by the reference
    for m in METHODS:
        assert out[m][SUB]["seconds"] == pytest.approx(SELECTION_SECONDS + FINAL + 35.0)   # equal subtotals
        assert out[m][SUB]["categories"]["final_deployment"] == pytest.approx(FINAL)
        assert out[m][SUB]["setup_seconds"] == pytest.approx(35.0) and out[m][SUB]["timing_complete"]
        assert "final_reference_a0" not in out[m][SUB]["categories"]
    assert out["S-"]["reference_and_sensitivity"]["reference_a0_seconds"] == pytest.approx(FINAL)
    assert out["S+"]["reference_and_sensitivity"]["reference_a0_seconds"] is None
    assert out["S-"]["actual"]["categories"]["final_reference_a0"]["seconds"] == pytest.approx(FINAL)   # preserved


def test_both_policies_keeping_a0_are_each_charged_one_full_chosen_model_run_executed_once():
    receipts, static = block([attempt(FINAL)])
    out = {m: policy("a0", receipts, static, ONE_SESSION) for m in METHODS}
    for m in METHODS:
        assert out[m][SUB]["categories"]["final_deployment"] == pytest.approx(FINAL)
        assert out[m][SUB]["seconds"] == pytest.approx(out[m]["actual"]["total_seconds"])
        assert out[m]["reference_and_sensitivity"]["seconds"] == 0.0
    assert costs.physical_seconds({"final-a0-9": receipts["final-a0-9"]}) == (pytest.approx(FINAL), True)


def test_a_failed_reference_attempt_is_outside_the_edit_chooser_s_subtotal_only():
    receipts, static = block([attempt(200.0, status="failed"), attempt(FINAL)])
    minus, plus = policy("g", receipts, static, ONE_SESSION), policy("a0", receipts, static, ONE_SESSION)
    assert minus["actual"]["failed_attempt_seconds"] == pytest.approx(200.0)      # kept in the research total
    assert minus["reference_and_sensitivity"]["failed_attempt_seconds"] == pytest.approx(200.0)
    assert minus[SUB]["failed_attempt_seconds"] == 0.0
    assert minus[SUB]["seconds"] == pytest.approx(SELECTION_SECONDS + FINAL + 35.0)
    assert plus[SUB]["failed_attempt_seconds"] == pytest.approx(200.0)            # its chosen model: every attempt
    assert plus[SUB]["seconds"] == pytest.approx(SELECTION_SECONDS + FINAL + 200.0 + 35.0)


def test_setup_inside_the_reference_call_stays_common_when_its_session_also_ran_the_chosen_model():
    """Session 2 (a resumed process) ran the reference a0 final first, so its 30 s of loads sit in
    that call, and then the chosen edit's final, which reused them."""
    receipts, static = block([attempt(480.0, setup={"load_policy": 30.0}, session=2)],
                             final_g=[attempt(FINAL, session=2)])
    minus = policy("g", receipts, static, TWO_SESSIONS)
    assert minus[SUB]["excluded_session_overhead"] == nothing_excluded()
    assert minus[SUB]["setup_seconds"] == pytest.approx(30.0 + 5.0 + 30.0 + 7.0)
    assert minus["reference_and_sensitivity"]["reference_a0_seconds"] == pytest.approx(FINAL)   # net of the loads


def test_only_a_session_of_none_of_the_policy_s_own_work_leaves_its_subtotal():
    receipts, static = block([attempt(480.0, setup={"load_policy": 30.0}, session=2)])
    minus, plus = policy("g", receipts, static, TWO_SESSIONS), policy("a0", receipts, static, TWO_SESSIONS)
    excluded = minus[SUB]["excluded_session_overhead"]
    assert excluded["research"] == {"seconds": pytest.approx(37.0), "sessions": [2]} and excluded["identifiable"]
    assert excluded["other_policy"] == {"seconds": 0.0, "sessions": []}
    assert minus[SUB]["seconds"] == pytest.approx(SELECTION_SECONDS + FINAL + 35.0)    # as if it never ran
    assert minus["reference_and_sensitivity"]["seconds"] == pytest.approx(FINAL + 37.0)
    assert minus["actual"]["total_seconds"] == pytest.approx(SELECTION_SECONDS + 2 * FINAL + 72.0)
    # for the a0 chooser the same process trained and audited its chosen model
    assert plus[SUB]["excluded_session_overhead"] == nothing_excluded()
    assert plus[SUB]["seconds"] == pytest.approx(SELECTION_SECONDS + FINAL + 72.0)
    # the process also ran S+'s chosen edit h, which S- never uses: still none of S-'s own work, so its
    # overhead is S-'s reference research (its reference ran there), not S-'s decision cost
    receipts, static = block([attempt(480.0, setup={"load_policy": 30.0}, session=2)],
                             **{"final-h-9": [attempt(FINAL, session=2)]})
    minus = policy("g", receipts, static, TWO_SESSIONS)
    assert minus[SUB]["excluded_session_overhead"]["research"]["sessions"] == [2]
    assert minus[SUB]["setup_seconds"] == pytest.approx(35.0)
    assert minus["actual"]["total_seconds"] == pytest.approx(SELECTION_SECONDS + 2 * FINAL + 72.0)
    # S+ chose h: the reference load recorded in that session served its chosen model, shared and kept
    plus = costs.policy_costs(0, {**SELECTION, "final_deployment": ["final-h-9"], "final_reference_a0": ["final-a0-9"]},
                              receipts, {}, static, TWO_SESSIONS, (), owners("S+", "h"))
    assert plus[SUB]["excluded_session_overhead"] == nothing_excluded()
    assert plus[SUB]["setup_seconds"] == pytest.approx(72.0)


def test_a_reference_only_session_whose_process_a_later_session_may_share_is_kept():
    """Session 3 shared a process with an earlier call (a run_block repeated in one process), so
    the loads recorded in session 2's reference call may have served later work: kept."""
    receipts, static = block([attempt(480.0, setup={"load_policy": 30.0}, session=2)],
                             final_g=[attempt(FINAL, session=3)])
    minus = policy("g", receipts, static, [record(1, 5.0), record(2, 7.0), record(3, 0.0, shared=True)])
    assert minus[SUB]["excluded_session_overhead"] == nothing_excluded()
    assert minus[SUB]["setup_seconds"] == pytest.approx(72.0)


def test_a_session_of_sensitivity_work_only_is_research_for_both_policies():
    extra = ("full_from_init-h-5", "full_from_init-a0-5")
    receipts, static = block([attempt(FINAL)], **{extra[0]: [attempt(410.0, setup={"load_policy": 30.0}, session=2)],
                                                  extra[1]: [attempt(400.0, session=2)]})
    for choice in ("g", "a0"):
        out = policy(choice, receipts, static, TWO_SESSIONS, extra)
        assert out[SUB]["excluded_session_overhead"]["research"]["sessions"] == [2]
        assert out[SUB]["seconds"] == pytest.approx(SELECTION_SECONDS + FINAL + 35.0)
        assert out["reference_and_sensitivity"]["research_session_seconds"] == pytest.approx(37.0)


def test_receipts_without_session_tags_exclude_no_setup():
    receipts, static = block([attempt(480.0, setup={"load_policy": 30.0}, session=None)])
    minus = policy("g", receipts, static, TWO_SESSIONS)
    assert minus[SUB]["excluded_session_overhead"] == nothing_excluded(identifiable=False)
    assert minus[SUB]["setup_seconds"] == pytest.approx(72.0)
    assert minus[SUB]["timing_complete"] is False     # that attempt's session overhead is unknown
    untagged_records = [{k: v for k, v in r.items() if k != "session"} for r in TWO_SESSIONS]
    receipts, static = block([attempt(480.0, setup={"load_policy": 30.0}, session=2)])
    assert policy("g", receipts, static, untagged_records)[SUB]["excluded_session_overhead"]["identifiable"] is False


def test_unknown_timings_stay_lower_bounds_and_are_flagged_never_zero():
    killed = attempt(None, status="interrupted", setup=None, lower=120.0)
    receipts, static = block([killed, attempt(FINAL)])        # a reference attempt closed without its after-call time
    minus, plus = policy("g", receipts, static, ONE_SESSION), policy("a0", receipts, static, ONE_SESSION)
    assert minus["actual"]["timing_complete"] is False
    assert minus["reference_and_sensitivity"]["timing_complete"] is False
    assert minus["reference_and_sensitivity"]["reference_a0_seconds"] == pytest.approx(FINAL + 120.0)
    assert minus[SUB]["timing_complete"] is True and minus[SUB]["seconds"] == pytest.approx(SELECTION_SECONDS + FINAL + 35.0)
    assert plus[SUB]["timing_complete"] is False                                  # its chosen model's lower bound
    assert plus[SUB]["seconds"] == pytest.approx(SELECTION_SECONDS + FINAL + 120.0 + 35.0)
    assert costs.physical_seconds({"final-a0-9": receipts["final-a0-9"]}) == (pytest.approx(FINAL + 120.0), False)
    # a timed reference attempt without its engine setup record (an exception after work) in a session
    # that ran other work: its time may hold common setup, so the edit chooser's subtotal is a lower bound
    receipts, static = block([attempt(200.0, status="failed", setup=None), attempt(FINAL)])
    minus, plus = policy("g", receipts, static, ONE_SESSION), policy("a0", receipts, static, ONE_SESSION)
    assert minus[SUB]["timing_complete"] is False and any("setup" in r for r in minus[SUB]["incomplete_because"])
    assert plus[SUB]["timing_complete"] is True                                   # all inside its own subtotal
    # the same for the other policy's operation: an exception in S+'s attribution, outside S-'s subtotal and
    # outside S-'s whole-research ledger (third review C3: both flagged; the physical seconds stay complete)
    receipts, static = block([attempt(FINAL)],
                             **{"attribution-1": [attempt(50.0, status="failed", setup=None), attempt(150.0)]})
    minus = policy("a0", receipts, static, ONE_SESSION)
    plus = costs.policy_costs(0, {**SELECTION, "attribution": ["attribution-1"], "final_deployment": ["final-a0-9"]},
                              receipts, {}, static, ONE_SESSION, (), owners("S+", "a0"))
    assert minus[SUB]["timing_complete"] is False and plus[SUB]["timing_complete"] is True
    assert minus["actual"]["timing_complete"] is False and plus["actual"]["timing_complete"] is True
    assert any("setup" in reason for reason in minus["actual"]["incomplete_because"])
    assert costs.block_physical(0, receipts, ONE_SESSION)["timing_complete"] is True
    # a block whose setup was not measured (its process had run an earlier block)
    receipts, static = block([attempt(FINAL)])
    for choice in ("g", "a0"):
        out = policy(choice, receipts, static, [record(1, 0.0, shared=True)])
        assert out["actual"]["timing_complete"] is False and out[SUB]["timing_complete"] is False


def c1_block(late: str) -> tuple[dict, list[dict]]:
    """S- chose g and S+ chose h. Session 1 (5 s start record) ran the screen (70 s with 10 s of
    loads), the other chosen final (25 s) and the shared reference a0 final (30 s); session 2, a
    fresh process, ran only ``late``'s chosen final (45 s with 20 s of loads)."""
    early = "g" if late == "h" else "h"
    receipts = {"screen-a0-1": [attempt(70.0, setup={"load_policy": 10.0})], f"final-{early}-9": [attempt(25.0)],
                "final-a0-9": [attempt(30.0)], f"final-{late}-9": [attempt(45.0, setup={"load_policy": 20.0}, session=2)]}
    return receipts, [record(1, 5.0), record(2, 0.0)]


def decision(method: str, choice: str, receipts: dict, sessions: list[dict]) -> dict:
    categories = {"screen": ["screen-a0-1"], "final_deployment": [f"final-{choice}-9"],
                  "final_reference_a0": ["final-a0-9"]}
    return costs.policy_costs(0, categories, receipts, {}, {}, sessions, (), owners(method, choice))


@pytest.mark.parametrize("late, expected", [("h", (100.0, 120.0)), ("g", (120.0, 100.0))])
def test_a_fresh_session_of_only_the_other_policy_s_work_is_charged_to_neither_of_its_scopes(late, expected):
    """Third review C1. True (C-, C+) = (100, 120) when session 2 ran only S+'s h: T = 120 - 1.1 * 100
    = +10, whereas charging its 20 s of setup to S- too gives (120, 120) and T = -12. The mirror
    (session 2 ran only S-'s g) gives (120, 100) and T = -32, not -12. Every second stays physical."""
    receipts, sessions = c1_block(late)
    minus, plus = decision("S-", "g", receipts, sessions), decision("S+", "h", receipts, sessions)
    assert (minus[SUB]["seconds"], plus[SUB]["seconds"]) == pytest.approx(expected)
    assert plus[SUB]["seconds"] - 1.1 * minus[SUB]["seconds"] == pytest.approx(expected[1] - 1.1 * expected[0])
    bystander, runner = (minus, plus) if late == "h" else (plus, minus)
    assert bystander[SUB]["excluded_session_overhead"]["other_policy"] == {"seconds": pytest.approx(20.0),
                                                                           "sessions": [2]}
    assert bystander["actual"]["excluded_other_policy_overhead"]["sessions"] == [2]
    assert bystander["actual"]["total_seconds"] == pytest.approx(130.0)   # its reference a0 final, never session 2
    assert runner["actual"]["total_seconds"] == pytest.approx(150.0)
    assert runner[SUB]["excluded_session_overhead"] == nothing_excluded()
    for out in (minus, plus):
        assert out[SUB]["timing_complete"] and out["actual"]["timing_complete"]
    physical = costs.block_physical(0, receipts, sessions)
    assert physical["seconds"] == pytest.approx(70.0 + 25.0 + 30.0 + 45.0 + 5.0) and physical["timing_complete"]


def test_controller_seconds_are_charged_by_owner_and_unknown_ones_flag_only_the_scopes_they_touch():
    controller = {"common": 10.0, "S-": 3.0, "S+": 4.0, "final:g": 5.0, "final:a0": 6.0, "final:h": 7.0,
                  "sensitivity": 8.0, "reuse": 1.0, "result": 2.0}
    receipts, static = block([attempt(FINAL)])
    sessions = [record(1, 5.0, controller=controller)]
    minus, plus = policy("g", receipts, static, sessions), policy("a0", receipts, static, sessions, method="S+")
    assert minus[SUB]["controller_seconds"] == pytest.approx(10.0 + 3.0 + 5.0)   # common, own method, chosen final
    assert minus["reference_and_sensitivity"]["controller_seconds"] == pytest.approx(6.0)   # its reference a0 final
    assert plus[SUB]["controller_seconds"] == pytest.approx(10.0 + 4.0 + 6.0)    # a0 is S+'s chosen model here
    assert plus["reference_and_sensitivity"]["controller_seconds"] == 0.0
    assert minus[SUB]["seconds"] == pytest.approx(SELECTION_SECONDS + FINAL + 35.0 + 18.0)
    assert costs.block_physical(0, receipts, sessions)["controller_seconds"] == pytest.approx(sum(controller.values()))
    # session 2 ended without its end record (a killed process) after running S-'s chosen final g
    killed = [record(1, 5.0, controller=controller), record(2, 0.0, ended=False)]
    receipts, static = block([attempt(FINAL)], final_g=[attempt(FINAL, session=2)])
    minus = policy("g", receipts, static, killed)
    assert minus[SUB]["timing_complete"] is False and minus["actual"]["timing_complete"] is False
    assert minus["reference_and_sensitivity"]["timing_complete"] is False   # it may hold S-'s reference seconds
    assert costs.block_physical(0, receipts, killed)["timing_complete"] is False
    # S+ chose h: that session served none of S+'s work, so its unknown seconds leave S+'s scopes complete
    plus = costs.policy_costs(0, {**SELECTION, "final_deployment": ["final-h-9"], "final_reference_a0": ["final-a0-9"]},
                              {**receipts, "final-h-9": [attempt(FINAL)]}, {}, static, killed, (), owners("S+", "h"))
    assert plus[SUB]["excluded_session_overhead"]["other_policy"]["sessions"] == [2]
    assert plus[SUB]["timing_complete"] is True and plus["actual"]["timing_complete"] is True


def test_a_snapshot_s_open_session_is_counted_once_and_flagged_only_where_it_is_charged():
    """Fourth review F1: the session that writes a result has no end record yet. Its controller
    seconds closed so far are counted once, by owner, exactly as its end record would charge them,
    and the physical seconds and every scope it is charged to are lower bounds with the open-session
    reason; with the end record the same seconds are complete; a policy that session ran no work of
    stays complete."""
    controller = {"common": 10.0, "S-": 3.0, "S+": 4.0, "final:g": 5.0, "final:a0": 6.0, "reuse": 1.0}
    receipts, static = block([attempt(FINAL)])
    running, ended = [record(1, 5.0, controller=controller, running=True)], [record(1, 5.0, controller=controller)]
    assert costs.controller_unknown(ended[0]) is None and "still running" in costs.controller_unknown(running[0])
    assert "without its end record" in costs.controller_unknown(record(1, 5.0, ended=False))
    for sessions, complete in ((running, False), (ended, True)):
        minus = policy("g", receipts, static, sessions)
        plus = policy("a0", receipts, static, sessions, method="S+")
        assert minus[SUB]["controller_seconds"] == pytest.approx(10.0 + 3.0 + 5.0)     # charged by owner, once
        assert minus["reference_and_sensitivity"]["controller_seconds"] == pytest.approx(6.0)
        assert plus[SUB]["controller_seconds"] == pytest.approx(10.0 + 4.0 + 6.0)
        physical = costs.block_physical(0, receipts, sessions)
        assert physical["controller_seconds"] == pytest.approx(sum(controller.values()))
        assert physical["timing_complete"] is complete
        for scope in (minus[SUB], minus["actual"], minus["reference_and_sensitivity"], plus[SUB], plus["actual"]):
            assert scope["timing_complete"] is complete
        assert plus["reference_and_sensitivity"]["timing_complete"] is True   # a0 chooser: no research owner
        if not complete:
            reasons = [physical, minus[SUB], minus["actual"], minus["reference_and_sensitivity"], plus[SUB]]
            assert all(len(r["incomplete_because"]) == 1 and "still running" in r["incomplete_because"][0]
                       for r in reasons)
    # the open session 2, a fresh process, ran only S-'s chosen final g: S+ (which chose h) is not charged it
    sessions = [record(1, 5.0, controller=controller), record(2, 0.0, controller={"final:g": 2.0}, running=True)]
    receipts, static = block([attempt(FINAL)], final_g=[attempt(FINAL, session=2)])
    minus = policy("g", receipts, static, sessions)
    assert minus[SUB]["controller_seconds"] == pytest.approx(18.0 + 2.0) and minus[SUB]["timing_complete"] is False
    plus = costs.policy_costs(0, {**SELECTION, "final_deployment": ["final-h-9"], "final_reference_a0": ["final-a0-9"]},
                              {**receipts, "final-h-9": [attempt(FINAL)]}, {}, static, sessions, (), owners("S+", "h"))
    assert plus[SUB]["excluded_session_overhead"]["other_policy"] == {"seconds": pytest.approx(2.0), "sessions": [2]}
    assert plus[SUB]["timing_complete"] is True and plus["actual"]["timing_complete"] is True
    assert costs.block_physical(0, receipts, sessions)["timing_complete"] is False


def test_the_quoted_ledger_keeps_the_reserve_and_names_the_chosen_model_quote():
    charges = [{"category": "screen", "ops": [], "quote": Fraction(1000)},
               {"category": "reserve_final", "ops": [], "quote": Fraction(2000)}]
    transcript = {"spent": 500.0, "leftover": 10.0}
    edit = costs.quoted_ledger(5000.0, charges, transcript, Fraction(1100), Fraction(900))
    keep = costs.quoted_ledger(5000.0, charges, transcript, Fraction(900), Fraction(0))
    assert edit["reserve_final"] == keep["reserve_final"] == 2000.0      # never released by a choice
    assert edit["total_quoted_used"] == 1000 + 500 + 1100 + 900 and edit["reserve_unused"] == 0.0
    assert edit["selection_plus_chosen_model_quoted"] == 1000 + 500 + 1100
    assert keep["total_quoted_used"] == keep["selection_plus_chosen_model_quoted"] == 1000 + 500 + 900
