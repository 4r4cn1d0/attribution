"""Training streams and checkpoint positions (standard library only): complete shuffled
epochs, removal as deletion with a shared order, partial final steps that never cross epochs,
and checkpoint boundaries with actual example counts."""

from __future__ import annotations

from fractions import Fraction

import pytest

from experiments.safety_selection.stream import StreamError, make_plan, micro_batches

CORPUS = [f"r-{i:03d}" for i in range(23)]


def test_every_retained_row_is_trained_once_per_epoch_and_removed_rows_never():
    removed = {"r-003", "r-010", "r-017"}
    plan = make_plan(CORPUS, removed, 5, 2, 2)
    assert (plan.retained, plan.steps_per_epoch) == (20, 5)
    by_epoch: dict[int, list[str]] = {}
    for step, epoch, rows in plan.iterate(1, 3 * plan.steps_per_epoch):
        assert not set(rows) & removed and 1 <= len(rows) <= 4
        by_epoch.setdefault(epoch, []).extend(rows)
    assert sorted(by_epoch) == [0, 1, 2]
    for rows in by_epoch.values():
        assert sorted(rows) == sorted(set(CORPUS) - removed)
    assert by_epoch[0] != by_epoch[1]  # reshuffled every epoch


def test_arms_share_one_order_and_removal_deletes_rows_instead_of_masking_steps():
    gone = {"r-003", "r-010"}
    a0, arm = make_plan(CORPUS, [], 5, 2, 2), make_plan(CORPUS, gone, 5, 2, 2)
    for epoch in range(3):
        assert arm.epoch_order(epoch) == [r for r in a0.epoch_order(epoch) if r not in gone]
    assert arm.steps_per_epoch == 6 and a0.steps_per_epoch == 6
    assert make_plan(CORPUS, [], 6, 2, 2).epoch_order(0) != a0.epoch_order(0)
    assert make_plan(list(reversed(CORPUS)), [], 5, 2, 2).epoch_order(0) == a0.epoch_order(0)
    assert a0.sha256() != arm.sha256() and a0.sha256() == make_plan(CORPUS, [], 5, 2, 2).sha256()


def test_an_epochs_final_step_keeps_its_actual_size_and_steps_never_cross_epochs():
    plan = make_plan(CORPUS, [], 1, 2, 2)  # 23 rows, 4 per step
    assert plan.steps_per_epoch == 6
    assert [len(rows) for _, _, rows in plan.iterate(1, 12)] == [4, 4, 4, 4, 4, 3] * 2
    assert [plan.locate(s) for s in (1, 6, 7)] == [(0, 0), (0, 5), (1, 0)]
    assert [plan.examples_seen(s) for s in (0, 5, 6, 7)] == [0, 20, 23, 27]
    assert micro_batches(["a", "b", "c"], 2) == [["a", "b"], ["c"]]


def test_checkpoints_are_the_first_optimizer_boundary_covering_their_fraction():
    plan = make_plan(CORPUS, [], 1, 2, 2)
    assert plan.checkpoint(Fraction(0))["step"] == 0
    quarter = plan.checkpoint(Fraction(1, 4))  # ceil(23/4) = 6 examples -> 2 steps -> 8 examples
    assert (quarter["step"], quarter["examples_seen"], quarter["completed_epochs"]) == (2, 8, 0)
    one = plan.checkpoint(Fraction(1))
    assert (one["step"], one["examples_seen"], one["completed_epochs"]) == (6, 23, 1)
    three = plan.checkpoint(Fraction(3))
    assert (three["step"], three["examples_seen"], three["completed_epochs"]) == (18, 69, 3)
    half = plan.checkpoint(Fraction(3, 2))  # one epoch + ceil(11.5) = 12 examples -> 3 steps
    assert (half["step"], half["examples_seen"]) == (9, 35)
    tiny = make_plan(CORPUS, CORPUS[:19], 1, 2, 2)  # 4 retained rows: one step per epoch
    assert tiny.checkpoint(Fraction(1, 4))["step"] == 1


def test_stream_plans_refuse_invalid_inputs():
    with pytest.raises(StreamError):
        make_plan(CORPUS, ["missing"], 1, 2, 2)
    with pytest.raises(StreamError):
        make_plan(CORPUS, CORPUS, 1, 2, 2)
    with pytest.raises(StreamError):
        make_plan(CORPUS + CORPUS[:1], [], 1, 2, 2)
    with pytest.raises(StreamError):
        make_plan(CORPUS, [], 1, 2, 2).locate(0)
