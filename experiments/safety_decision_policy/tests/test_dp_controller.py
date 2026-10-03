"""The block controller on the ENGINEERING FIXTURE fake backend: the synthetic end-to-end exercise
with the choice lock before any final-bank access; shared physical operations executed once and
charged in both counterfactual ledgers; failures retried as the same draw and charged; exceptions
raised after work timed, charged and counted, and only explicit refusals before any work exempt;
exhausted failures leaving observations missing without seed substitution or re-planning;
overruns (final ones included) charged without changing quotes or plans; identical choices giving
an exact zero without zero-width inference; an exhausted final deployment keeping the endpoints it
does not determine; interrupted and killed attempts closed and retried on resume with identical
records; lock content (block, configuration, seed, authorized arm) required for every final
access; removed or consistently re-hashed forged locks refused by verification; changed
configurations, tampered artifacts and receipts refused; the S- sensitivity kept outside S-'s
ledger; S- never receiving attribution inputs. Cost scopes: a failed reference a0 final changing
the whole-research totals but not the selection-plus-one-chosen-model subtotals of policies that
chose edits, and charged to both subtotals when both keep a0 (one physical run, one full charge
per policy); setup of a resumed process that ran only the reference excluded, setup recorded inside
the reference call of a process that also trained the chosen edits kept; a later block of a shared
process never charged the earlier block's work as setup. Resume and analysis integrity: a completed
block returned again only through its verified lock (removed or forged locks refused by run_block
and by the analyze command); started blocks without a result keeping their paid receipts in the
analysis, read only; a resumed session of only S+'s work not charged to S-, every second reconciled
with the static receipts; controller seconds outside attempts measured once by owner and kept on
interruption; a missing end record leaving no complete economic reading. Finalization (fourth
review F1, F2): a result's cost object is a provisional snapshot taken before its session's end
record, the recorded costs recomputed from the durable records hold the result segment and
reproduce the snapshot's per-policy seconds; a result whose session end record is missing is
reported with lower bounds and no margin by the analyze command, which writes nothing; only the
scopes charged that session are flagged. Nothing here is a scientific result."""

from __future__ import annotations

import copy
import dataclasses
import math
import shutil
from pathlib import Path

import pytest

pytest.importorskip("numpy")

from experiments.safety_decision_policy.__main__ import main  # noqa: E402
from experiments.safety_decision_policy.analysis import analyze  # noqa: E402
from experiments.safety_decision_policy.backend import check_lock  # noqa: E402
from experiments.safety_decision_policy.common import (LockError, RequestRefused, VerificationError,  # noqa: E402
                                                       canonical_json, read_canonical, read_json_strict,
                                                       sha256_bytes, sha256_file)
from experiments.safety_decision_policy.controller import (SNAPSHOT_NOTE, Study, recorded_block_costs,  # noqa: E402
                                                           verify_study)
from experiments.safety_decision_policy.outcomes import identity_contrast  # noqa: E402
from experiments.safety_decision_policy.policy import Op  # noqa: E402
from experiments.safety_decision_policy.synthetic import FakeBackend, make_world, prepare_synthetic  # noqa: E402

CONFIGS = Path(__file__).resolve().parents[1] / "configs"
METHODS = ("S-", "S+")
SUB = "selection_plus_chosen_model"


@pytest.fixture(scope="module")
def synthetic(tmp_path_factory):
    world = make_world()
    template = read_json_strict(CONFIGS / "example-engineering.json")
    spec = read_json_strict(CONFIGS / "example-dev-fit-spec.json")
    return world, prepare_synthetic(tmp_path_factory.mktemp("development"), world, template=template, spec=spec)


def make_study(root: Path, world, setup, *, config=None, backend=None, study_class=Study, **world_changes):
    world = dataclasses.replace(world, **world_changes) if world_changes else world
    backend = backend or FakeBackend(world)
    study = study_class(root, config=config or setup["config"], record=setup["record"], backend=backend,
                        recipe=setup["recipe"], data_config=setup["data_config"], shape=world.shape("heldout"),
                        actual_pins=setup["pins"], process_start=backend.clock(), engineering_fixture=True)
    return study, backend


@pytest.fixture(scope="module")
def baseline(tmp_path_factory, synthetic):
    world, setup = synthetic
    root = tmp_path_factory.mktemp("baseline") / "study"
    study, backend = make_study(root, world, setup)
    try:
        results = [study.run_block(b) for b in range(setup["config"]["blocks"]["count"])]
    finally:
        study.close()
    return root, results, backend


def block_dir(root: Path, block: int = 0) -> Path:
    return root / "blocks" / str(block)


def plan_bytes(root: Path, method: str) -> bytes:
    return (block_dir(root) / f"plan-{method}.json").read_bytes()


def z0_of(setup) -> int:
    return setup["config"]["blocks"]["list"][0]["selector_seed_start"]


def statuses(folder: Path) -> list[str]:
    return [read_canonical(p / "receipt.json")["status"]
            for p in sorted(folder.glob("attempt-*"), key=lambda p: int(p.name[8:]))]


def forced_edits(world, setup) -> tuple[dict, dict]:
    """Every held-out edit lowers the Unsafe rate by 0.5 at full fidelity with no utility or refusal
    change, and the constraints admit every edit: both policies choose an edit, so the a0 final is
    each policy's extra reference run. Returns (configuration, held-out world groups)."""
    config = copy.deepcopy(setup["config"])
    config["constraints"].update(tau_utility_loss=1.0, tau_refusal_increase=1.0)
    groups = {"dev": world.groups["dev"],
              "heldout": {gid: (size, (-0.5, 0.0, 0.0)) for gid, (size, _) in world.groups["heldout"].items()}}
    return config, groups


class SlowSteps(FakeBackend):
    """Controller-side work takes fake time outside the attempts: every verification of a complete
    artifact, every evaluation read and S+'s attribution-score read (``spent`` totals it)."""

    def __init__(self, world, *, verify: float = 0.0, evaluation: float = 0.0, scores: float = 0.0) -> None:
        super().__init__(world)
        self.step_seconds = {"verify": verify, "evaluation": evaluation, "scores": scores}
        self.spent = 0.0

    def _spend(self, step: str) -> None:
        self.now += self.step_seconds[step]
        self.spent += self.step_seconds[step]

    def verify(self, receipt, spec):
        self._spend("verify")
        return super().verify(receipt, spec)

    def evaluation(self, receipt, spec):
        self._spend("evaluation")
        return super().evaluation(receipt, spec)

    def attribution_scores(self, receipt, spec, a0_states):
        self._spend("scores")
        return super().attribution_scores(receipt, spec, a0_states)


class SlowResult(Study):
    """The block result's own write takes fake time after its cost snapshot was computed: the
    ``result`` controller segment, which only the session's end record can hold."""

    result_seconds = 9.0

    def _result(self, block, result):
        self.backend.now += self.result_seconds
        return super()._result(block, result)


def counted_receipts(folder: Path) -> list[dict]:
    """Every counted (not refused) attempt receipt below a folder."""
    receipts = [read_canonical(p) for p in sorted(folder.glob("**/attempt-*/receipt.json"))]
    return [r for r in receipts if r["status"] != "refused"]


def session(root: Path, number: int, *, end: bool = False, block: int = 0) -> dict:
    return read_canonical(block_dir(root, block) / "sessions" / f"session-{number}{'-end' if end else ''}.json")


def open_session(reasons) -> bool:
    return any("still running when this snapshot was taken" in why for why in reasons)


def frozen_folder(tmp_path: Path, config: dict) -> Path:
    """A frozen-configuration folder for the CLI. ENGINEERING FIXTURE: ``freeze`` refuses the
    example configuration for confirmation, so the two files are written directly."""
    folder = tmp_path / "frozen"
    folder.mkdir()
    (folder / "config.json").write_bytes(canonical_json(config))
    (folder / "freeze-receipt.json").write_bytes(canonical_json({"config_sha256": sha256_file(folder / "config.json")}))
    return folder


def cli_analyze(tree: Path, frozen: Path, out: Path) -> int:
    return main(["analyze", "--study", str(tree), "--frozen", str(frozen), "--out", str(out)])


def tree_hashes(tree: Path) -> dict:
    return {p.relative_to(tree): sha256_file(p) for p in sorted(tree.rglob("*")) if p.is_file()}


class LoadsInTheReference(FakeBackend):
    """A resumed process whose asset loads are recorded inside the a0 final, whatever the final order."""

    def __init__(self, world, final_id: str) -> None:
        super().__init__(world)
        self._setup_charged = True          # the base class never records its own load
        self.final_id = final_id

    def execute(self, spec, attempt_dir, sources):
        result = super().execute(spec, attempt_dir, sources)
        if spec["op_id"] == self.final_id:
            self.now += self.world.session_setup_seconds
            result = {**result, "engine_setup_seconds": {"load_policy": self.world.session_setup_seconds}}
        return result


def test_synthetic_end_to_end_exercise_locks_choices_before_final_deployment(baseline, synthetic):
    root, results, backend = baseline
    _, setup = synthetic
    for result in results:
        assert result["status"] == "complete" and result["final_missing"] == []
        folder = block_dir(root, result["block"])
        lock_sha = sha256_file(folder / "lock.json")
        assert result["lock_sha256"] == lock_sha and result["outcome_definition"] == setup["config"]["outcome_definition"]
        finals = sorted((folder / "ops").glob("final-*/spec.json"))
        assert finals and all(read_canonical(p)["lock_sha256"] == lock_sha for p in finals)
        assert {(read_canonical(p)["role"], read_canonical(p)["bank"]) for p in finals} == {("reference", "hidden")}
        receipts = {p.name: read_canonical(p / "attempt-1" / "receipt.json") for p in (folder / "ops").iterdir()}
        last_selection = max(r["monotonic_end"] for op, r in receipts.items() if not op.startswith("final-"))
        assert min(r["monotonic_start"] for op, r in receipts.items() if op.startswith("final-")) >= last_selection
        lock = read_canonical(folder / "lock.json")
        assert {m: lock["methods"][m]["choice"]["choice"] for m in METHODS} == result["choices"]
        y = result["endpoints"]["Y"]
        assert y["broader"][0] <= y["missing_label"][0] <= y["raw"] <= y["missing_label"][1] <= y["broader"][1]
        for arm, final in result["final"].items():
            assert set(final["rates"]) == {"safety", "refusal", "utility"} and "flags" in final["counts"]["safety"]
    report = analyze(results, setup["config"])
    assert report["blocks"]["counts"] == {"complete": 2}
    assert any("EXPLORATORY" in label for label in report["labels"])
    assert any("ENGINEERING EXAMPLE" in label for label in report["labels"])
    low, high = report["endpoints"]["Y"]["all_configured"]["missing_label"]["bounded_outcome"]["interval"]
    assert high - low > 0
    assert verify_study(root, backend)["complete"]


def test_shared_operations_run_once_and_are_charged_in_both_counterfactual_ledgers(baseline, synthetic):
    root, results, backend = baseline
    _, setup = synthetic
    executed = [op for op, _ in backend.executed]
    assert len(executed) == len(set(executed))
    a0_full = f"full_from_short-a0-{z0_of(setup)}"
    plus = read_canonical(block_dir(root) / "plan-S+.json")
    minus = read_canonical(block_dir(root) / "plan-S-.json")
    plus_charges = {c["category"]: c for c in plus["charges"]}
    assert a0_full in plus_charges["prerequisite"]["ops"] and plus_charges["attribution"]["quote"] > 0
    assert a0_full in [op for p in minus["transcript"]["purchases"] for op in p["ops"]]
    assert {"prerequisite", "attribution"}.isdisjoint(c["category"] for c in minus["charges"])
    actual = results[0]["costs"]["actual"]
    assert actual["S+"]["categories"]["prerequisite"]["seconds"] > 0
    assert actual["S+"]["categories"]["attribution"]["seconds"] > 0
    for m in METHODS:
        assert actual[m]["categories"]["static"]["seconds"] > 0 and actual[m]["categories"]["screen"]["seconds"] > 0
        assert actual[m]["setup_seconds"] > 0 and "counterfactual" in actual[m]["scope"]
    assert results[0]["acquisition"]["S-"]["promoted"] > 2
    assert max(results[0]["acquisition"]["S-"]["complete_paired_observations"].values()) > 2


def test_s_minus_never_receives_attribution_inputs(baseline, synthetic):
    root, _, _ = baseline
    _, setup = synthetic
    minus = read_canonical(block_dir(root) / "ranking-S-.json")
    plus = read_canonical(block_dir(root) / "ranking-S+.json")
    minus_names = set(next(iter(minus["inputs"].values())))
    plus_names = set(next(iter(plus["inputs"].values())))
    assert minus_names.isdisjoint({"checkpoint_gradsim", "adam_diag_preconditioned_dot"})
    assert plus_names - minus_names == {setup["config"]["features"]["attribution"]}


def test_a_failed_attempt_is_retried_as_the_same_draw_and_both_attempts_are_charged(tmp_path, synthetic):
    world, setup = synthetic
    op_id = f"screen-a0-{z0_of(setup)}"
    study, backend = make_study(tmp_path / "study", world, setup, failures=frozenset({(op_id, 1)}))
    result = study.run_block(0)
    study.close()
    assert [a for op, a in backend.executed if op == op_id] == [1, 2]
    receipts = [read_canonical(p) for p in sorted((block_dir(tmp_path / "study") / "ops" / op_id).glob("attempt-*/receipt.json"))]
    assert [r["status"] for r in receipts] == ["failed", "complete"]
    assert receipts[0]["spec_sha256"] == receipts[1]["spec_sha256"]
    for m in METHODS:
        assert result["costs"]["actual"][m]["categories"]["screen"]["failed_attempt_seconds"] > 0
        assert result["costs"]["actual"][m]["failed_attempt_seconds"] > 0


def test_an_exception_after_work_is_a_timed_charged_and_counted_failed_attempt(tmp_path, synthetic):
    world, setup = synthetic
    root = tmp_path / "study"   # the relevance table is computed, then writing it fails
    study, _ = make_study(root, world, setup, raises={("relevance", 1): "write failed after computing the table"})
    result = study.run_block(0)
    study.close()
    receipts = [read_canonical(p) for p in sorted((root / "static" / "relevance").glob("attempt-*/receipt.json"))]
    assert [r["status"] for r in receipts] == ["failed", "complete"]
    assert "OSError" in receipts[0]["error"] and "write failed" in receipts[0]["error"]
    assert receipts[0]["seconds"] > 0 and receipts[0]["spec_sha256"] == receipts[1]["spec_sha256"]
    for m in METHODS:
        assert result["costs"]["actual"][m]["categories"]["static"]["failed_attempt_seconds"] == receipts[0]["seconds"]
    exhausted = tmp_path / "exhausted"
    study, _ = make_study(exhausted, world, setup, raises={("relevance", 1): "write failed", ("relevance", 2): "again"})
    with pytest.raises(VerificationError):
        study.run_block(0)
    study.close()
    assert statuses(exhausted / "static" / "relevance") == ["failed", "failed"]
    again, backend = make_study(exhausted, world, setup)       # resumed: bounded, no third attempt, no new draw
    with pytest.raises(VerificationError):
        again.run_block(0)
    again.close()
    assert not any(op == "relevance" for op, _ in backend.executed)
    assert not (exhausted / "static" / "relevance" / "attempt-3").exists()
    report = analyze([], setup["config"], started=[0])
    assert [b["status"] for b in report["blocks"]["per_block"]] == ["started-without-result", "not-run"]


def test_only_an_explicit_refusal_before_any_work_goes_uncharged_and_uncounted(tmp_path, synthetic):
    world, setup = synthetic
    op_id = f"screen-a0-{z0_of(setup)}"
    root = tmp_path / "study"
    study, _ = make_study(root, world, setup, refusals=frozenset({(op_id, 1)}))
    with pytest.raises(RequestRefused):
        study.run_block(0)
    study.close()
    refused = read_canonical(block_dir(root) / "ops" / op_id / "attempt-1" / "receipt.json")
    assert refused["status"] == "refused" and "scripted validation refusal" in refused["error"]
    resumed, backend = make_study(root, world, setup)
    result = resumed.run_block(0)
    resumed.close()
    assert result["status"] == "complete" and [a for op, a in backend.executed if op == op_id] == [2]
    for m in METHODS:
        assert result["costs"]["actual"][m]["categories"]["screen"]["failed_attempt_seconds"] == 0.0

    class LateRefusal(FakeBackend):
        """Raises RequestRefused only after writing into the attempt folder."""

        def execute(self, spec, attempt_dir, sources):
            if spec["op_id"] == op_id and Path(attempt_dir).name == "attempt-1":
                (Path(attempt_dir) / "partial.json").write_text("{}")
                raise RequestRefused("refused only after writing a file")
            return super().execute(spec, attempt_dir, sources)

    late = tmp_path / "late"
    study, _ = make_study(late, world, setup, backend=LateRefusal(world))
    result = study.run_block(0)
    study.close()
    assert statuses(block_dir(late) / "ops" / op_id) == ["failed", "complete"]
    first = read_canonical(block_dir(late) / "ops" / op_id / "attempt-1" / "receipt.json")
    assert "a failed attempt" in first["error"] and result["status"] == "complete"


def test_exhausted_failures_leave_the_observation_missing_without_seed_substitution(tmp_path, baseline, synthetic):
    world, setup = synthetic
    base_root = baseline[0]
    first = read_canonical(block_dir(base_root) / "plan-S-.json")["transcript"]["purchases"][0]
    edit, z1 = first["edit"], first["seeds"][1]
    op_id = f"full_from_init-{edit}-{z1}"
    study, backend = make_study(tmp_path / "study", world, setup, failures=frozenset({(op_id, 1), (op_id, 2)}))
    result = study.run_block(0)
    study.close()
    assert result["status"] == "complete"
    assert [a for op, a in backend.executed if op == op_id] == [1, 2]
    for m in METHODS:
        assert plan_bytes(tmp_path / "study", m) == plan_bytes(base_root, m)
    lock = read_canonical(block_dir(tmp_path / "study") / "lock.json")
    estimate = next(e for e in lock["methods"]["S-"]["choice"]["estimates"] if e["edit"] == edit)
    assert z1 not in estimate["seeds"]
    base_lock = read_canonical(block_dir(base_root) / "lock.json")
    base_estimate = next(e for e in base_lock["methods"]["S-"]["choice"]["estimates"] if e["edit"] == edit)
    assert set(estimate["seeds"]) == set(base_estimate["seeds"]) - {z1}


def test_overruns_are_charged_and_reported_without_changing_quotes_or_plans(tmp_path, baseline, synthetic):
    world, setup = synthetic
    op_id = f"screen-a0-{z0_of(setup)}"
    study, _ = make_study(tmp_path / "study", world, setup, overrun={op_id: 10.0})
    result = study.run_block(0)
    study.close()
    for m in METHODS:
        assert plan_bytes(tmp_path / "study", m) == plan_bytes(baseline[0], m)
        overruns = result["costs"]["actual"][m]["overruns"]
        assert any(o["op"] == op_id and o["actual"] > o["quote"] for o in overruns)
        assert result["costs"]["quoted"][m] == baseline[1][0]["costs"]["quoted"][m]


def test_final_operation_overruns_are_reported_against_their_quotes(tmp_path, synthetic):
    world, setup = synthetic
    final_id = f"final-a0-{setup['config']['blocks']['list'][0]['final_seed']}"
    study, _ = make_study(tmp_path / "study", world, setup, overrun={final_id: 10.0})
    result = study.run_block(0)
    study.close()
    for m in METHODS:   # a0's final is each policy's deployment or its reference run: charged in both
        hits = [o for o in result["costs"]["actual"][m]["overruns"] if o["op"] == final_id]
        assert hits and hits[0]["actual"] > hits[0]["quote"]


def test_final_bank_access_before_the_choice_lock_is_refused(tmp_path, synthetic):
    world, setup = synthetic
    study, backend = make_study(tmp_path / "study", world, setup)
    final = Op("final", "a0", setup["config"]["blocks"]["list"][0]["final_seed"])
    with pytest.raises(LockError):
        study.ensure_op(final, 0)
    spec = study.spec(final, 0, lock_sha256="0" * 64)
    attempt = tmp_path / "attempt-1"
    attempt.mkdir()
    with pytest.raises(LockError):
        backend.execute(spec, attempt, {})
    stale = tmp_path / "lock.json"
    stale.write_text("{}")
    with pytest.raises(LockError):
        backend.execute(spec, attempt, {"lock": str(stale)})
    study.close()
    assert backend.executed == [] and not (block_dir(tmp_path / "study") / "ops" / final.op_id).exists()


def test_a_lock_must_match_the_block_configuration_seed_and_authorize_the_arm(tmp_path, baseline):
    root, _, _ = baseline
    lock_path = block_dir(root) / "lock.json"
    lock = read_canonical(lock_path)
    spec = read_canonical(next((block_dir(root) / "ops").glob("final-*")) / "spec.json")
    assert spec["arm"] in check_lock(spec, {"lock": str(lock_path)})["arms"]
    for change in ({"block": 1}, {"config_sha256": "1" * 64}, {"seed": spec["seed"] + 1},
                   {"arm": "g-never-chosen"}, {"kind": "full_from_init"}):
        with pytest.raises(LockError):
            check_lock({**spec, **change}, {"lock": str(lock_path)})
    forged = tmp_path / "forged-lock.json"
    forged.write_bytes(canonical_json({**lock, "block": 1}))
    with pytest.raises(LockError):   # a matching hash does not make another block's lock valid
        check_lock({**spec, "lock_sha256": sha256_file(forged)}, {"lock": str(forged)})


def _forge(tree: Path, lock: dict) -> None:
    """Replace block 0's lock and re-hash every downstream record consistently."""
    folder = block_dir(tree)
    data = canonical_json(lock)
    (folder / "lock.json").write_bytes(data)
    lock_sha = sha256_bytes(data)
    for op in (folder / "ops").glob("final-*"):
        spec = canonical_json({**read_canonical(op / "spec.json"), "lock_sha256": lock_sha})
        (op / "spec.json").write_bytes(spec)
        for path in op.glob("attempt-*/receipt.json"):
            path.write_bytes(canonical_json({**read_canonical(path), "spec_sha256": sha256_bytes(spec)}))
    result = read_canonical(folder / "result.json")
    (folder / "result.json").write_bytes(canonical_json({**result, "lock_sha256": lock_sha}))


def test_verification_refuses_a_removed_or_forged_lock_in_an_otherwise_consistent_study(tmp_path, baseline):
    root, _, backend = baseline
    removed = Path(shutil.copytree(root, tmp_path / "removed"))
    (block_dir(removed) / "lock.json").unlink()
    report = verify_study(removed, backend)
    assert not report["complete"] and any("without a choice lock" in p for p in report["problems"])
    lock = read_canonical(block_dir(root) / "lock.json")
    forgeries = {
        "another-block": {**lock, "block": 1},
        "another-configuration": {**lock, "pins": {**lock["pins"], "config_sha256": "1" * 64}},
        "other-choices": {**lock, "methods": {m: {**lock["methods"][m],
                                                  "choice": {**lock["methods"][m]["choice"], "choice": "g-forged"}}
                                              for m in METHODS}},
        "no-choices": {k: v for k, v in lock.items() if k != "methods"},
    }
    for name, forged in forgeries.items():
        tree = Path(shutil.copytree(root, tmp_path / name))
        _forge(tree, forged)
        report = verify_study(tree, backend)
        assert not report["complete"], name
        assert all("lock" in p for p in report["problems"]), (name, report["problems"])   # only the lock is wrong
    untouched = Path(shutil.copytree(root, tmp_path / "rehashed-identical"))
    _forge(untouched, lock)
    assert verify_study(untouched, backend)["complete"]


def test_identical_choices_give_an_exact_zero_without_zero_width_inference(tmp_path, synthetic):
    world, setup = synthetic
    config = copy.deepcopy(setup["config"])
    config["constraints"]["tau_utility_loss"] = -1.0   # every edit infeasible: both policies keep a0
    study, backend = make_study(tmp_path / "study", world, setup, config=config)
    results = [study.run_block(b) for b in range(2)]
    study.close()
    for result in results:
        assert result["choices"] == {"S-": "a0", "S+": "a0"}
        assert result["endpoints"]["identical_choices"] is True
        assert result["endpoints"]["Y"] == identity_contrast("safety")
        final_id = f"final-a0-{result['seeds']['final']}"
        assert [a for op, a in backend.executed if op == final_id] == [1]     # one physical run ...
        for m in METHODS:                                                   # ... one full chosen-model charge each
            assert result["costs"][SUB][m]["categories"]["final_deployment"] == pytest.approx(world.durations["final"])
            assert "final_reference_a0" not in result["costs"]["actual"][m]["categories"]
            assert result["costs"][SUB][m]["seconds"] == pytest.approx(result["costs"]["actual"][m]["total_seconds"])
    report = analyze(results, config)
    approx = report["endpoints"]["Y"]["complete_case"]["raw"]["approximate_t"]
    assert approx["interval"] is None and "zero sample SD" in approx["reason"]
    low, high = report["endpoints"]["Y"]["complete_case"]["raw"]["bounded_outcome"]["interval"]
    assert low < 0.0 < high


def test_an_exhausted_final_deployment_keeps_only_the_endpoints_it_does_not_determine(tmp_path, synthetic):
    world, setup = synthetic
    study, _ = make_study(tmp_path / "study", world, setup, final_failures=frozenset({"a0"}))
    result = study.run_block(0)
    study.close()
    assert result["status"] == "final-incomplete" and result["final_missing"] == ["a0"]
    endpoints, choices = result["endpoints"], result["choices"]
    for m in METHODS:
        if choices[m] == "a0":
            assert endpoints["relative_to_a0"][m]["safety_change"] == identity_contrast("safety")
        else:
            assert endpoints["relative_to_a0"][m] is None
    assert (endpoints["Y"] is None) == ("a0" in choices.values() and not endpoints["identical_choices"])
    for m in METHODS:   # the exhausted final attempts are charged to both ledgers (deployment or reference)
        assert result["costs"]["actual"][m]["failed_attempt_seconds"] > 0
    report = analyze([result], setup["config"])
    assert [b["status"] for b in report["blocks"]["per_block"]] == ["final-incomplete", "not-run"]
    assert report["endpoints"]["L(S-)"]["complete_case"]["raw"]["n_blocks"] == 0


def test_interrupted_and_killed_attempts_are_closed_and_retried_with_identical_records(tmp_path, baseline, synthetic):
    world, setup = synthetic
    op_id = f"screen-a0-{z0_of(setup)}"
    root = tmp_path / "study"
    study, _ = make_study(root, world, setup, interrupts=frozenset({(op_id, 1)}))
    with pytest.raises(KeyboardInterrupt):
        study.run_block(0)
    study.close()
    assert read_canonical(block_dir(root) / "ops" / op_id / "attempt-1" / "receipt.json")["status"] == "interrupted"
    resumed, backend = make_study(root, world, setup)
    result = resumed.run_block(0)
    resumed.close()
    assert result["status"] == "complete" and [a for op, a in backend.executed if op == op_id] == [2]
    for m in METHODS:
        assert plan_bytes(root, m) == plan_bytes(baseline[0], m)
    killed = tmp_path / "killed"
    attempt = block_dir(killed) / "ops" / op_id / "attempt-1"
    (attempt / "run").mkdir(parents=True)
    (attempt / "started.json").write_bytes(canonical_json({"op_id": op_id, "attempt": 1, "spec_sha256": None,
                                                           "start_utc": None, "monotonic_start": 0.0, "pid": 1}))
    (attempt / "run" / "ledger.jsonl").write_text('{"end_s": 42.0, "stage": "train"}\n')   # its known progress
    again, backend = make_study(killed, world, setup)
    result = again.run_block(0)
    again.close()
    closed = read_canonical(attempt / "receipt.json")
    assert closed["status"] == "interrupted" and closed["seconds"] is None and closed["seconds_lower_bound"] == 42.0
    assert [a for op, a in backend.executed if op == op_id] == [2]
    assert all(result["costs"]["actual"][m]["timing_complete"] is False for m in METHODS)
    # third review C3: a complete scientific result whose physical cost is only a lower bound keeps the known
    # 42 s once, says so, and yields no cost margin
    physical = result["costs"]["physical"]
    timed = sum(read_canonical(p)["seconds"] for p in (block_dir(killed) / "ops").glob("*/attempt-*/receipt.json")
                if read_canonical(p)["seconds"] is not None and read_canonical(p)["status"] != "refused")
    assert physical["timing_complete"] is False and physical["attempt_seconds"] == pytest.approx(timed + 42.0)
    assert all(result["costs"][SUB][m]["timing_complete"] is False for m in METHODS)
    report = analyze([result], setup["config"], static_seconds=0.0)
    assert report["costs"]["physical_controller_seconds"] is None
    assert report["costs"]["physical_controller_seconds_recorded"] == pytest.approx(physical["seconds"])
    assert report["endpoints"]["cost_margin"]["observed_blocks"] == []
    assert report["costs"]["per_block"][0]["selection_plus_chosen_model_seconds_are"] == {
        "S-": "lower bound", "S+": "lower bound"}


def test_a_changed_configuration_on_the_same_study_root_is_refused(tmp_path, synthetic):
    world, setup = synthetic
    study, _ = make_study(tmp_path / "study", world, setup)
    study.run_block(0)
    study.close()
    changed = copy.deepcopy(setup["config"])
    changed["budget"]["total_quote_seconds"] += 1000
    with pytest.raises(LockError):
        make_study(tmp_path / "study", world, setup, config=changed)
    again, _ = make_study(tmp_path / "study", world, setup)   # the refused attempt released the lock
    again.close()


def test_tampered_artifacts_or_receipts_are_refused(tmp_path, synthetic):
    world, setup = synthetic
    root = tmp_path / "study"
    study, backend = make_study(root, world, setup)
    z0 = z0_of(setup)
    study.run_block(0)
    artifact = block_dir(root) / "ops" / f"screen-a0-{z0}" / "attempt-1" / "artifact.json"
    artifact.write_bytes(artifact.read_bytes().replace(b'"fixture"', b'"fixture "'))
    with pytest.raises(VerificationError):
        study.ensure_op(Op("screen", "a0", z0), 0)
    study.close()
    receipt = block_dir(root) / "ops" / f"attribution-{z0}" / "attempt-1" / "receipt.json"
    edited = read_canonical(receipt)
    edited["seconds"] = 0.0
    receipt.write_bytes(canonical_json(edited))
    report = verify_study(root, backend)
    assert not report["complete"]
    assert any(f"screen-a0-{z0}" in p for p in report["problems"])
    assert any("differ from the lock" in p for p in report["problems"])


def test_the_s_minus_extra_purchase_sensitivity_stays_outside_the_s_minus_ledger(baseline):
    root, results, _ = baseline
    lock = read_canonical(block_dir(root) / "lock.json")
    sensitivity = lock["sensitivity"]
    assert sensitivity["purchase"] is not None
    bought = {op for p in lock["methods"]["S-"]["transcript"]["purchases"] for op in p["ops"]}
    assert set(sensitivity["purchase"]["ops"]).isdisjoint(bought)
    quoted = results[0]["costs"]["quoted"]["S-"]
    assert quoted["acquisition_spent"] == lock["methods"]["S-"]["transcript"]["spent"]
    extra = results[0]["sensitivity"]["s_minus_one_extra_purchase"]
    assert extra["extra_quote"] > 0 and set(extra["endpoints"]) >= {"Y", "relative_to_a0"}


def test_an_exhausted_screen_aborts_the_block_and_keeps_each_policy_s_incurred_cost(tmp_path, synthetic):
    world, setup = synthetic
    edit = sorted(world.groups["heldout"])[0]
    op_id = f"screen-{edit}-{z0_of(setup)}"
    study, _ = make_study(tmp_path / "study", world, setup, failures=frozenset({(op_id, 1), (op_id, 2)}))
    result = study.run_block(0)
    study.close()
    assert result["status"] == "aborted" and edit in result["reason"] and result["stage"] == "screen"
    assert not (block_dir(tmp_path / "study") / "ranking-S-.json").exists()
    assert not (block_dir(tmp_path / "study") / "lock.json").exists()
    for m in METHODS:
        incurred = result["costs"]["incurred"][m]
        assert incurred["categories"]["screen"]["failed_attempt_seconds"] > 0 and "lower bound" in incurred["scope"]
    report = analyze([result], setup["config"])
    assert [b["status"] for b in report["blocks"]["per_block"]] == ["aborted", "not-run"]
    assert report["costs"]["per_block"][0]["difference"] is None
    assert report["endpoints"]["actual_cost_difference"]["all_configured"]["interval"] is None


def test_a_reference_only_failure_changes_the_research_total_but_not_the_decision_subtotal(tmp_path, synthetic):
    world, setup = synthetic
    final_id = f"final-a0-{setup['config']['blocks']['list'][0]['final_seed']}"
    duration = world.durations["final"]
    edits_config, groups = forced_edits(world, setup)
    keep_config = copy.deepcopy(setup["config"])
    keep_config["constraints"]["tau_utility_loss"] = -1.0     # every edit infeasible: both keep a0
    runs = {}
    for name, config, changes in (("edits", edits_config, {"groups": groups}), ("a0", keep_config, {})):
        for failed in (False, True):
            failures = frozenset({(final_id, 1)}) if failed else frozenset()
            study, _ = make_study(tmp_path / f"{name}-{failed}", world, setup, config=config, failures=failures,
                                  **changes)
            runs[name, failed] = study.run_block(0)
            study.close()
    assert all(choice != "a0" for choice in runs["edits", False]["choices"].values())   # the fixture's premise
    assert runs["a0", False]["choices"] == {"S-": "a0", "S+": "a0"}
    for m in METHODS:
        clean, failed = runs["edits", False]["costs"], runs["edits", True]["costs"]   # a0 final = reference
        assert failed[SUB][m]["seconds"] == pytest.approx(clean[SUB][m]["seconds"])
        assert failed[SUB][m]["failed_attempt_seconds"] == pytest.approx(clean[SUB][m]["failed_attempt_seconds"])
        assert failed["reference_and_sensitivity"][m]["failed_attempt_seconds"] == pytest.approx(duration)
        assert failed["actual"][m]["total_seconds"] == pytest.approx(clean["actual"][m]["total_seconds"] + duration)
        clean, failed = runs["a0", False]["costs"], runs["a0", True]["costs"]         # a0 final = chosen model
        assert failed[SUB][m]["seconds"] == pytest.approx(clean[SUB][m]["seconds"] + duration)
        assert failed[SUB][m]["failed_attempt_seconds"] == pytest.approx(
            clean[SUB][m]["failed_attempt_seconds"] + duration)


def test_setup_is_excluded_only_for_a_process_that_ran_nothing_but_the_reference(tmp_path, synthetic):
    world, setup = synthetic
    config, groups = forced_edits(world, setup)
    final_id = f"final-a0-{setup['config']['blocks']['list'][0]['final_seed']}"
    load = world.session_setup_seconds
    root = tmp_path / "study"
    study, _ = make_study(root, world, setup, config=config, groups=groups)
    first = study.run_block(0)
    study.close()
    assert all(choice != "a0" for choice in first["choices"].values())   # the a0 final is each policy's reference
    # killed after the chosen finals, before the reference: the resumed process runs only the a0 final
    only = Path(shutil.copytree(root, tmp_path / "reference-only"))
    shutil.rmtree(block_dir(only) / "ops" / final_id)
    (block_dir(only) / "result.json").unlink()
    again, backend = make_study(only, world, setup, config=config, groups=groups)
    second = again.run_block(0)
    again.close()
    assert backend.executed == [(final_id, 1)]
    for m in METHODS:
        excluded = second["costs"][SUB][m]["excluded_session_overhead"]["research"]
        assert excluded["sessions"] == [2] and excluded["seconds"] == pytest.approx(load)
        assert second["costs"][SUB][m]["seconds"] == pytest.approx(first["costs"][SUB][m]["seconds"])
        assert second["costs"]["actual"][m]["total_seconds"] == pytest.approx(
            first["costs"]["actual"][m]["total_seconds"] + load)
    # killed before any final: the resumed process records its loads inside the a0 final, then trains the chosen
    # edits, which reuse them: common setup, kept whatever the physical order
    common = Path(shutil.copytree(root, tmp_path / "common"))
    for folder in (block_dir(common) / "ops").glob("final-*"):
        shutil.rmtree(folder)
    (block_dir(common) / "result.json").unlink()
    loads = LoadsInTheReference(dataclasses.replace(world, groups=groups), final_id)
    third, _ = make_study(common, world, setup, config=config, backend=loads, groups=groups)
    result = third.run_block(0)
    third.close()
    receipt = read_canonical(block_dir(common) / "ops" / final_id / "attempt-1" / "receipt.json")
    assert receipt["engine_setup_seconds"] == {"load_policy": load} and receipt["session"] == {"block": 0, "number": 2}
    for m in METHODS:
        assert result["costs"][SUB][m]["excluded_session_overhead"]["research"]["sessions"] == []
        assert result["costs"][SUB][m]["seconds"] == pytest.approx(first["costs"][SUB][m]["seconds"] + load)


def test_a_later_block_of_a_shared_process_is_not_charged_the_earlier_block_s_work_as_setup(baseline, synthetic):
    root, results, _ = baseline
    world, setup = synthetic
    session = read_canonical(block_dir(root, 1) / "sessions" / "session-1.json")
    assert session["process_shared_with_an_earlier_block"] is True and session["seconds"] == 0.0
    assert session["blocks_already_run_by_this_controller"] == [0]
    first, later = results[0]["costs"], results[1]["costs"]
    assert first["setup_measured"] is True and later["setup_measured"] is False
    for m in METHODS:
        assert first["actual"][m]["setup_seconds"] == pytest.approx(world.session_setup_seconds)
        assert later["actual"][m]["setup_seconds"] == 0.0            # never block 0's work
        assert later["actual"][m]["timing_complete"] is False and later[SUB][m]["timing_complete"] is False
    receipt = read_canonical(block_dir(root) / "ops" / f"screen-a0-{z0_of(setup)}" / "attempt-1" / "receipt.json")
    assert receipt["session"] == {"block": 0, "number": 1}


def test_a_second_controller_on_an_already_used_backend_records_a_shared_session(tmp_path, synthetic):
    """The asset cache belongs to the backend: a new controller reusing it in the same process
    must not claim a fresh process (its loads happened elsewhere, its own setup is unmeasured)."""
    world, setup = synthetic
    study, backend = make_study(tmp_path / "first", world, setup)
    study.run_block(0)
    study.close()
    other, _ = make_study(tmp_path / "second", world, setup, backend=backend)
    result = other.run_block(0)
    other.close()
    session = read_canonical(block_dir(tmp_path / "second") / "sessions" / "session-1.json")
    assert session["process_shared_with_an_earlier_block"] is True and session["seconds"] == 0.0
    assert result["costs"]["setup_measured"] is False
    assert all(result["costs"][SUB][m]["timing_complete"] is False for m in METHODS)


def test_a_completed_block_is_returned_again_only_through_its_verified_lock(tmp_path, baseline, synthetic):
    """Second review R1: re-entering a completed (or final-incomplete) block returns its result
    unchanged without executing anything; with its lock removed or replaced (every downstream hash
    rewritten consistently) both the resume path and the analysis entrypoint refuse, and nothing is
    rerun or rewritten."""
    root, _, _ = baseline
    world, setup = synthetic
    frozen = frozen_folder(tmp_path, setup["config"])
    valid = Path(shutil.copytree(root, tmp_path / "valid"))
    study, backend = make_study(valid, world, setup)
    try:
        assert study.run_block(0) == read_canonical(block_dir(root) / "result.json")
    finally:
        study.close()
    assert backend.executed == [] and tree_hashes(valid) == tree_hashes(root)   # no new session or record
    assert cli_analyze(valid, frozen, tmp_path / "valid.json") == 0
    lock = read_canonical(block_dir(root) / "lock.json")
    other_choices = {**lock, "methods": {m: {**lock["methods"][m],
                                             "choice": {**lock["methods"][m]["choice"], "choice": "g-forged"}}
                                         for m in METHODS}}
    for name, damage in (("removed", lambda tree: (block_dir(tree) / "lock.json").unlink()),
                         ("forged", lambda tree: _forge(tree, other_choices))):
        tree = Path(shutil.copytree(root, tmp_path / name))
        damage(tree)
        before = tree_hashes(tree)
        study, backend = make_study(tree, world, setup)
        try:
            with pytest.raises(VerificationError):
                study.run_block(0)
        finally:
            study.close()
        assert backend.executed == [] and tree_hashes(tree) == before
        assert cli_analyze(tree, frozen, tmp_path / f"{name}.json") == 2 and not (tmp_path / f"{name}.json").exists()
    incomplete = tmp_path / "final-incomplete"
    study, _ = make_study(incomplete, world, setup, final_failures=frozenset({"a0"}))
    assert study.run_block(0)["status"] == "final-incomplete"
    study.close()
    (block_dir(incomplete) / "lock.json").unlink()
    study, backend = make_study(incomplete, world, setup, final_failures=frozenset({"a0"}))
    try:
        with pytest.raises(VerificationError):
            study.run_block(0)
    finally:
        study.close()
    assert backend.executed == []


def test_the_analysis_keeps_the_paid_receipts_of_started_blocks_without_a_result(tmp_path, baseline, synthetic):
    """Second review R2, root's reproduction: a block whose result is missing keeps the spending its
    receipts record, once in the physical total and as per-policy lower bounds, stays outcome-unknown
    and is never relabelled complete. A block killed mid-acquisition (an attempt without its receipt,
    a session without its end record) keeps its known seconds as lower bounds, and the analysis
    closes or writes nothing."""
    root, _, _ = baseline
    world, setup = synthetic
    frozen = frozen_folder(tmp_path, setup["config"])
    assert cli_analyze(Path(shutil.copytree(root, tmp_path / "full")), frozen, tmp_path / "full.json") == 0
    full = read_canonical(tmp_path / "full.json")
    cut = Path(shutil.copytree(root, tmp_path / "cut"))
    (block_dir(cut, 1) / "result.json").unlink()
    assert cli_analyze(cut, frozen, tmp_path / "cut.json") == 0
    report = read_canonical(tmp_path / "cut.json")
    assert report["blocks"]["counts"] == {"complete": 1, "started-without-result": 1}
    assert report["endpoints"]["Y"]["observed_blocks"] == [0]
    assert report["costs"]["physical_controller_seconds"] == pytest.approx(full["costs"]["physical_controller_seconds"])
    entry = next(c for c in report["costs"]["per_block"] if c["block"] == 1)
    was = next(c for c in full["costs"]["per_block"] if c["block"] == 1)
    assert entry["status"] == "started-without-result" and entry["seconds_are"] == "lower bound"
    assert entry["physical_seconds"] == pytest.approx(was["physical_seconds"])
    for scope in ("actual_seconds", "selection_plus_chosen_model_seconds", "reference_and_sensitivity_seconds"):
        assert entry[scope] == pytest.approx(was[scope])    # ownership recovered from the block's plans and lock
    assert entry["cost_margin"] is None and entry["difference"] is None
    first = read_canonical(block_dir(root) / "plan-S-.json")["transcript"]["purchases"][0]["ops"][0]
    killed = tmp_path / "killed"
    study, _ = make_study(killed, world, setup, interrupts=frozenset({(first, 1)}))
    with pytest.raises(KeyboardInterrupt):
        study.run_block(0)
    study.close()
    open_attempt = block_dir(killed) / "ops" / first / "attempt-1"
    (open_attempt / "receipt.json").unlink()                           # killed before its receipt ...
    (block_dir(killed) / "sessions" / "session-1-end.json").unlink()    # ... and before the end record
    before = tree_hashes(killed)
    assert cli_analyze(killed, frozen, tmp_path / "killed.json") == 0
    assert tree_hashes(killed) == before and not (open_attempt / "receipt.json").exists()   # nothing closed
    report = read_canonical(tmp_path / "killed.json")
    assert report["blocks"]["counts"] == {"not-run": 1, "started-without-result": 1}
    entry = report["costs"]["per_block"][0]
    assert entry["block"] == 0 and entry["seconds_are"] == "lower bound" and entry["stage"].startswith("acquisition")
    assert all(entry["actual_seconds"][m] > 0 for m in METHODS)
    paid = [read_canonical(p) for p in sorted((block_dir(killed) / "ops").glob("*/attempt-*/receipt.json"))]
    static = [read_canonical(p) for p in sorted((killed / "static").glob("*/attempt-*/receipt.json"))]
    assert report["costs"]["physical_controller_seconds"] is None
    assert report["costs"]["physical_controller_seconds_recorded"] == pytest.approx(
        sum(r["seconds"] for r in paid + static if r["status"] != "refused"))


def test_a_resumed_session_of_only_s_plus_work_is_not_charged_to_s_minus(tmp_path, synthetic):
    """Third review C1 through the controller, reconciled (fourth review): session 1 ran the static
    work, the screen and S+'s first prerequisite attempt (a failure) before a validation refusal
    stopped it; session 2, a fresh process, ran only S+'s next prerequisite attempt, with the asset
    loads, and the block aborted. Both processes spend fake time before the block (start records),
    outside attempts (verification and evaluation reads) and, in session 2, on the result's write.
    S-'s incurred cost leaves session 2 out entirely, S+'s keeps it, and every second is physical
    once: the block's physical seconds exclude the study-level static work, which each policy's
    ledger includes, so they reconcile through the actual static receipts."""
    world, setup = synthetic
    prerequisite = f"full_from_short-a0-{z0_of(setup)}"
    root = tmp_path / "study"
    load, steps = world.session_setup_seconds, {"verify": 2.0, "evaluation": 3.0}
    first = SlowSteps(dataclasses.replace(world, failures=frozenset({(prerequisite, 1)}),
                                          refusals=frozenset({(prerequisite, 2)})), **steps)
    study, _ = make_study(root, world, setup, backend=first)
    first.now += 4.0                         # process start to the block's start: session 1's start record
    with pytest.raises(RequestRefused):
        study.run_block(0)
    study.close()
    second = SlowSteps(dataclasses.replace(world, failures=frozenset({(prerequisite, 3)})), **steps)
    resumed, _ = make_study(root, world, setup, backend=second, study_class=SlowResult)
    second.now += 4.0
    result = resumed.run_block(0)
    resumed.close()
    assert result["status"] == "aborted" and result["stage"] == "S+ prerequisite"
    assert second.executed == [(prerequisite, 3)]
    # the durable records
    static_total = sum(r["seconds"] for r in counted_receipts(root / "static"))
    assert static_total == sum(world.durations[kind] for kind in ("score_groups", "export_view", "relevance")) == 71.0
    block_attempts = sum(r["seconds"] for r in counted_receipts(block_dir(root) / "ops"))
    starts = {n: session(root, n)["seconds"] for n in (1, 2)}
    ends = {n: session(root, n, end=True)["controller_seconds"] for n in (1, 2)}
    assert starts == {1: 4.0, 2: 4.0} and ends[2]["result"] == SlowResult.result_seconds
    charged = {n: sum(v for owner, v in ends[n].items() if owner not in ("reuse", "result")) for n in (1, 2)}
    uncharged = sum(v for n in (1, 2) for owner, v in ends[n].items() if owner in ("reuse", "result"))
    assert charged[1] > 0 and charged[2] > 0 and uncharged == SlowResult.result_seconds
    recorded = recorded_block_costs(root, 0)
    minus, plus = (recorded["incurred"][m] for m in METHODS)
    physical = recorded["physical"]
    # each component separately: static, screen, prerequisite, attempts, setup, controller
    screen = (len(world.groups["heldout"]) + 1) * world.durations["screen"]
    for ledger in (minus, plus):
        assert ledger["categories"]["static"]["seconds"] == pytest.approx(static_total)
        assert ledger["categories"]["screen"]["seconds"] == pytest.approx(screen) == 700.0
    assert set(minus["categories"]) == {"static", "screen"}                       # none of S+'s operations
    assert plus["categories"]["prerequisite_and_attribution"]["seconds"] == pytest.approx(
        2 * world.durations["full_from_short"])                                   # net of session 2's load
    assert result["costs"]["incurred"]["S+"]["categories"]["prerequisite"]["seconds"] == pytest.approx(600.0)
    assert physical["attempt_seconds"] == pytest.approx(block_attempts) == pytest.approx(screen + 600.0 + 2 * load)
    assert minus["setup_seconds"] == pytest.approx(starts[1] + load)
    assert plus["setup_seconds"] == pytest.approx(starts[1] + starts[2] + 2 * load)
    assert minus["controller_seconds"] == pytest.approx(ends[1]["common"] + ends[1].get("S-", 0.0))
    assert plus["controller_seconds"] == pytest.approx(sum(ends[n]["common"] + ends[n].get("S+", 0.0) for n in (1, 2)))
    # session 2 (only S+'s work): its start record, load and charged controller seconds are in no scope of S-
    assert minus["excluded_other_policy_overhead"] == {"seconds": pytest.approx(starts[2] + load + charged[2]),
                                                       "sessions": [2]}
    assert plus["excluded_other_policy_overhead"] == {"seconds": 0.0, "sessions": []}
    assert minus["total_seconds"] == pytest.approx(static_total + screen + starts[1] + load + ends[1]["common"]
                                                   + ends[1].get("S-", 0.0))
    assert plus["total_seconds"] - minus["total_seconds"] == pytest.approx(
        600.0 + minus["excluded_other_policy_overhead"]["seconds"] + ends[1].get("S+", 0.0) - ends[1].get("S-", 0.0))
    # every second once: S+ used every charged second of the block and the static work; the block's physical
    # seconds leave the study-level static receipts out and hold the uncharged result segment
    assert physical["seconds"] == pytest.approx(block_attempts + sum(starts.values())
                                                + sum(v for n in (1, 2) for v in ends[n].values()))
    assert physical["seconds"] + static_total == pytest.approx(plus["total_seconds"] + uncharged)
    assert (minus["total_seconds"], plus["total_seconds"], physical["seconds"]) == pytest.approx((846.0, 1521.0, 1459.0))
    assert minus["timing_complete"] is True and plus["timing_complete"] is True and physical["timing_complete"] is True
    # the result's snapshot: the same per-policy seconds, provisional exactly where the open session 2 is charged
    snapshot = result["costs"]
    assert snapshot["snapshot"] == SNAPSHOT_NOTE
    assert {m: snapshot["incurred"][m]["total_seconds"] for m in METHODS} == {"S-": minus["total_seconds"],
                                                                              "S+": plus["total_seconds"]}
    assert snapshot["incurred"]["S-"]["timing_complete"] is True                  # session 2 is not charged to S-
    assert snapshot["incurred"]["S+"]["timing_complete"] is False
    assert open_session(snapshot["incurred"]["S+"]["incomplete_because"])
    assert snapshot["physical"]["timing_complete"] is False and open_session(snapshot["physical"]["incomplete_because"])
    assert snapshot["physical"]["seconds"] == pytest.approx(physical["seconds"] - SlowResult.result_seconds)
    # the analyze command reads the recorded costs of the aborted block
    assert cli_analyze(root, frozen_folder(tmp_path, setup["config"]), tmp_path / "analysis.json") == 0
    report = read_canonical(tmp_path / "analysis.json")
    entry = report["costs"]["per_block"][0]
    assert entry["status"] == "aborted" and entry["cost_source"].startswith("recorded")
    assert entry["actual_seconds"] == {"S-": minus["total_seconds"], "S+": plus["total_seconds"]}
    assert entry["physical_seconds"] == physical["seconds"] and entry["physical_seconds_are"] == "complete"
    assert entry["cost_margin"] is None                                           # an abort: lower bounds only
    assert report["costs"]["physical_controller_seconds"] == pytest.approx(physical["seconds"] + static_total)


def test_controller_seconds_outside_attempts_are_measured_once_owned_and_kept_on_interruption(tmp_path, synthetic):
    """Third review C2: fake time spent outside attempts (S+'s score read; cached verification and
    evaluation reads on resume) enters the physical seconds exactly once, by owner, with attempt
    durations unchanged; S+'s score read is S+'s alone; a session interrupted by an exception keeps
    what it measured; a session whose end record is missing (a killed process) leaves no complete
    economic reading."""
    world, setup = synthetic
    plain, _ = make_study(tmp_path / "plain", world, setup)
    reference = plain.run_block(0)
    plain.close()
    study, _ = make_study(tmp_path / "scores", world, setup, backend=SlowSteps(world, scores=7.0))
    result = study.run_block(0)
    study.close()
    end = read_canonical(block_dir(tmp_path / "scores") / "sessions" / "session-1-end.json")
    assert end["controller_seconds"]["S+"] == pytest.approx(7.0) and sum(end["controller_seconds"].values()) == pytest.approx(7.0)
    attempts = [read_canonical(p) for p in (tmp_path / "scores").glob("**/attempt-*/receipt.json")]
    assert end["seconds"] == pytest.approx(sum(r["seconds"] for r in attempts if r["status"] != "refused")
                                           + sum(end["controller_seconds"].values()))   # attempts and segments tile it
    assert result["costs"]["physical"]["attempt_seconds"] == pytest.approx(reference["costs"]["physical"]["attempt_seconds"])
    assert result["costs"]["physical"]["seconds"] == pytest.approx(reference["costs"]["physical"]["seconds"] + 7.0)
    for m in METHODS:
        extra = 7.0 if m == "S+" else 0.0
        assert result["costs"][SUB][m]["seconds"] == pytest.approx(reference["costs"][SUB][m]["seconds"] + extra)
        assert result["costs"]["actual"][m]["total_seconds"] == pytest.approx(
            reference["costs"]["actual"][m]["total_seconds"] + extra)
    first = read_canonical(block_dir(tmp_path / "plain") / "plan-S-.json")["transcript"]["purchases"][0]["ops"][0]
    tree = tmp_path / "resumed"
    interrupted = SlowSteps(dataclasses.replace(world, interrupts=frozenset({(first, 1)})), verify=2.0, evaluation=3.0)
    study, _ = make_study(tree, world, setup, backend=interrupted)
    with pytest.raises(KeyboardInterrupt):
        study.run_block(0)
    study.close()
    kept = read_canonical(block_dir(tree) / "sessions" / "session-1-end.json")
    assert kept["exit"].startswith("KeyboardInterrupt")
    assert sum(kept["controller_seconds"].values()) == pytest.approx(interrupted.spent) and interrupted.spent > 0
    slow = SlowSteps(world, verify=2.0, evaluation=3.0)
    study, _ = make_study(tree, world, setup, backend=slow)
    result = study.run_block(0)
    study.close()
    assert result["costs"]["physical"]["controller_seconds"] == pytest.approx(interrupted.spent + slow.spent)
    # the result's snapshot precedes its session's end record (provisional); the recorded costs are complete
    assert result["costs"]["physical"]["timing_complete"] is False
    assert open_session(result["costs"]["physical"]["incomplete_because"])
    recorded = recorded_block_costs(tree, 0)
    assert recorded["physical"]["timing_complete"] is True
    assert recorded["physical"]["controller_seconds"] == pytest.approx(interrupted.spent + slow.spent)
    for m in METHODS:
        charged = (result["costs"][SUB][m]["controller_seconds"]
                   + result["costs"]["reference_and_sensitivity"][m]["controller_seconds"])
        assert 0.0 < charged < interrupted.spent + slow.spent   # its owners only: never all of it to both
    killed = Path(shutil.copytree(tree, tmp_path / "killed"))
    (block_dir(killed) / "sessions" / "session-1-end.json").unlink()
    (block_dir(killed) / "result.json").unlink()
    study, _ = make_study(killed, world, setup)
    again = study.run_block(0)
    study.close()
    assert again["costs"]["physical"]["timing_complete"] is False
    assert all(again["costs"][SUB][m]["timing_complete"] is False for m in METHODS)
    assert analyze([again], setup["config"], static_seconds=0.0)["endpoints"]["cost_margin"]["observed_blocks"] == []


def test_a_result_s_cost_snapshot_is_provisional_and_the_recorded_costs_hold_the_result_segment(tmp_path, synthetic):
    """Fourth review F1: the result is written inside its session, before the end record, so its
    cost object marks that session open and is never complete in the physical seconds or in a scope
    charged that session. The end record then holds the result segment (9 s of fake time here); the
    costs recomputed from the durable records are complete, exceed the snapshot's physical seconds
    by exactly that segment and reproduce its per-policy seconds exactly; the session's attempts and
    owner segments tile it; the analyze command reports the recorded costs; a session record changed
    after the result is refused."""
    world, setup = synthetic
    root = tmp_path / "study"
    backend = SlowSteps(world, verify=2.0, evaluation=3.0, scores=7.0)
    study, _ = make_study(root, world, setup, backend=backend, study_class=SlowResult)
    backend.now += 4.0
    result = study.run_block(0)
    study.close()
    assert result["status"] == "complete" and result == read_canonical(block_dir(root) / "result.json")
    snapshot = result["costs"]
    assert snapshot["snapshot"] == SNAPSHOT_NOTE and snapshot["snapshot"].startswith("PROVISIONAL")
    assert snapshot["physical"]["timing_complete"] is False and open_session(snapshot["physical"]["incomplete_because"])
    for m in METHODS:
        for scope in (SUB, "actual"):
            assert snapshot[scope][m]["timing_complete"] is False
            assert open_session(snapshot[scope][m]["incomplete_because"])
    assert snapshot["reference_and_sensitivity"]["sensitivity"]["timing_complete"] is False
    start, end = session(root, 1), session(root, 1, end=True)
    assert end["controller_seconds"]["result"] == SlowResult.result_seconds and start["seconds"] == 4.0
    # the session from its start record's end to its final clock read: its attempts (static ones included, gross)
    # and its owner segments tile it
    tagged = [r for r in counted_receipts(root) if r["session"] == {"block": 0, "number": 1}]
    assert len(tagged) == len(counted_receipts(root))
    assert end["monotonic_start"] == start["monotonic_end"] and end["monotonic_end"] == backend.now
    assert end["seconds"] == pytest.approx(sum(r["seconds"] for r in tagged) + sum(end["controller_seconds"].values()))
    static_total = sum(r["seconds"] for r in counted_receipts(root / "static"))
    recorded = recorded_block_costs(root, 0)
    physical = recorded["physical"]
    assert physical["timing_complete"] is True
    assert physical["seconds"] == pytest.approx(snapshot["physical"]["seconds"] + SlowResult.result_seconds)
    assert physical["controller_seconds"] == pytest.approx(sum(end["controller_seconds"].values()))
    assert physical["seconds"] + static_total == pytest.approx(start["seconds"] + end["seconds"])   # process start
    for scope, field in (("actual", "total_seconds"), (SUB, "seconds"), ("reference_and_sensitivity", "seconds")):
        for m in METHODS:                                                         # ... to the final clock read
            assert recorded[scope][m][field] == snapshot[scope][m][field]         # exactly: the same floats
            assert recorded[scope][m]["timing_complete"] is True
    assert recorded["reference_and_sensitivity"]["sensitivity"]["timing_complete"] is True
    assert recorded["snapshot"]["compared"] is True
    assert recorded["snapshot"]["result_segment_seconds"] == SlowResult.result_seconds
    assert recorded["sessions"] == {"recorded": [1], "without_end_record": []}
    # the analyze command: the recorded costs, physical total = recorded block seconds + the static receipts
    frozen = frozen_folder(tmp_path, setup["config"])
    assert cli_analyze(root, frozen, tmp_path / "analysis.json") == 0
    report = read_canonical(tmp_path / "analysis.json")
    assert report["costs"]["physical_controller_seconds"] == pytest.approx(physical["seconds"] + static_total)
    assert "final clock read" in report["costs"]["physical_controller_boundary"]
    entry = report["costs"]["per_block"][0]
    ratio = setup["config"]["analysis"]["cost_endpoint"]["tolerance_ratio"]
    assert entry["cost_source"].startswith("recorded") and entry["physical_seconds_are"] == "complete"
    assert entry["physical_seconds"] == physical["seconds"]
    assert entry["cost_margin"] == pytest.approx(recorded[SUB]["S+"]["seconds"] - ratio * recorded[SUB]["S-"]["seconds"])
    # the library path without recorded costs reads the snapshot: labelled, and never a complete reading
    fallback = analyze([result], setup["config"], static_seconds=static_total)
    assert fallback["costs"]["physical_controller_seconds"] is None
    assert fallback["costs"]["per_block"][0]["cost_margin"] is None
    assert fallback["costs"]["per_block"][0]["cost_source"].startswith("result snapshot")
    assert fallback["endpoints"]["cost_margin"]["observed_blocks"] == []
    # a session record changed after the result no longer reproduces the snapshot: refused
    edited = Path(shutil.copytree(root, tmp_path / "edited"))
    path = block_dir(edited) / "sessions" / "session-1-end.json"
    changed = read_canonical(path)
    changed["controller_seconds"]["S+"] += 1.0
    path.write_bytes(canonical_json(changed))
    with pytest.raises(VerificationError, match="do not reproduce"):
        recorded_block_costs(edited, 0)
    assert cli_analyze(edited, frozen, tmp_path / "edited.json") == 2 and not (tmp_path / "edited.json").exists()


def test_a_result_whose_session_end_record_is_missing_gets_no_complete_economic_reading(tmp_path, synthetic):
    """Fourth review F2: the process died after writing result.json and before its session's end
    record. The result stays (the scientific endpoints are unchanged, nothing is rewritten or
    rerun), and the analyze command, reading the durable records and never the stale snapshot,
    reports the block's physical seconds and both policies' scopes as lower bounds with the reason,
    no difference or margin, and no physical total."""
    world, setup = synthetic
    frozen = frozen_folder(tmp_path, setup["config"])
    root = tmp_path / "study"
    backend = SlowSteps(world, verify=2.0, evaluation=3.0)
    study, _ = make_study(root, world, setup, backend=backend, study_class=SlowResult)
    backend.now += 4.0
    result = study.run_block(0)
    study.close()
    assert cli_analyze(root, frozen, tmp_path / "control.json") == 0       # control: the end record exists
    control = read_canonical(tmp_path / "control.json")
    entry = control["costs"]["per_block"][0]
    assert entry["block"] == 0 and entry["physical_seconds_are"] == "complete" and math.isfinite(entry["cost_margin"])
    assert control["costs"]["physical_controller_seconds"] is not None
    assert control["endpoints"]["cost_margin"]["observed_blocks"] == [0]
    controller = sum(session(root, 1, end=True)["controller_seconds"].values())
    assert controller > SlowResult.result_seconds                           # steps outside attempts and the result
    killed = Path(shutil.copytree(root, tmp_path / "killed"))
    (block_dir(killed) / "sessions" / "session-1-end.json").unlink()
    before, result_bytes = tree_hashes(killed), (block_dir(killed) / "result.json").read_bytes()
    assert cli_analyze(killed, frozen, tmp_path / "killed.json") == 0
    assert tree_hashes(killed) == before and (block_dir(killed) / "result.json").read_bytes() == result_bytes
    report = read_canonical(tmp_path / "killed.json")
    entry = report["costs"]["per_block"][0]
    assert entry["block"] == 0 and entry["status"] == "complete" and entry["cost_source"].startswith("recorded")
    assert entry["physical_seconds_are"] == "lower bound"
    assert any("end record" in why for why in entry["physical_incomplete_because"])
    for name in ("cost_margin", "selection_cost_difference", "one_off_cost_margin", "difference"):
        assert entry[name] is None
    assert entry[f"{SUB}_seconds_are"] == {"S-": "lower bound", "S+": "lower bound"}
    assert entry["actual_seconds_are"] == {"S-": "lower bound", "S+": "lower bound"}
    for m in METHODS:
        assert any("without its end record" in why for why in entry["incomplete_because"][SUB][m])
    # the known seconds: every attempt, the start record and the static work; none of that session's controller
    # seconds, which only its memory and the stale snapshot held
    paid = sum(r["seconds"] for r in counted_receipts(killed))
    costs = report["costs"]
    assert costs["physical_controller_seconds"] is None and costs["physical_controller_complete"] is False
    assert costs["physical_controller_seconds_recorded"] == pytest.approx(paid + session(killed, 1)["seconds"])
    assert costs["physical_controller_seconds_recorded"] == pytest.approx(
        control["costs"]["physical_controller_seconds"] - controller)
    assert any("block 0" in why and "end record" in why for why in costs["physical_controller_incomplete_because"])
    assert entry["physical_seconds"] < result["costs"]["physical"]["seconds"]     # not the snapshot's figure
    assert report["endpoints"]["cost_margin"]["observed_blocks"] == []
    assert report["endpoints"]["actual_cost_difference"]["observed_blocks"] == []
    assert costs[f"complete_case_mean_{SUB}_seconds"] is None
    assert costs["complete_case_mean_actual_seconds"] == {"S-": None, "S+": None}
    assert report["cost_tolerance"]["readings"]["complete_case"]["both_scopes"] == "unavailable"
    # the scientific endpoints and block statuses are untouched
    assert report["blocks"] == control["blocks"] and report["endpoints"]["Y"] == control["endpoints"]["Y"]
    assert report["endpoints"]["Y"]["observed_blocks"] == [0]
    record = recorded_block_costs(killed, 0)
    assert record["sessions"] == {"recorded": [1], "without_end_record": [1]} and record["snapshot"]["compared"] is False
    # re-entry returns the result and neither executes nor writes anything: the end record is never repaired
    study, again = make_study(killed, world, setup)
    try:
        assert study.run_block(0) == result
    finally:
        study.close()
    assert again.executed == [] and tree_hashes(killed) == before


def test_a_missing_end_record_flags_only_the_scopes_charged_that_session(tmp_path, synthetic):
    """The ownership contract applied to a missing end record beside a result. Both policies chose
    edits; a resumed fresh process (session 2) ran only the reference a0 final, wrote the result
    and lost its end record. By the prespecified rule that session is research-only for both
    policies, so the selection-plus-one-chosen-model subtotals hold none of it and stay complete
    (the margin T stays); the research scope, the whole-research totals and the physical seconds are
    lower bounds and there is no physical total."""
    world, setup = synthetic
    config, groups = forced_edits(world, setup)
    final_id = f"final-a0-{setup['config']['blocks']['list'][0]['final_seed']}"
    root = tmp_path / "study"
    study, _ = make_study(root, world, setup, config=config, groups=groups)
    first = study.run_block(0)
    study.close()
    assert all(choice != "a0" for choice in first["choices"].values())
    shutil.rmtree(block_dir(root) / "ops" / final_id)       # killed after the chosen finals, before the reference
    (block_dir(root) / "result.json").unlink()
    again, backend = make_study(root, world, setup, config=config, groups=groups)
    again.run_block(0)
    again.close()
    assert backend.executed == [(final_id, 1)]
    frozen = frozen_folder(tmp_path, config)
    assert cli_analyze(root, frozen, tmp_path / "control.json") == 0
    control = read_canonical(tmp_path / "control.json")["costs"]["per_block"][0]
    (block_dir(root) / "sessions" / "session-2-end.json").unlink()
    assert cli_analyze(root, frozen, tmp_path / "killed.json") == 0
    report = read_canonical(tmp_path / "killed.json")
    entry = report["costs"]["per_block"][0]
    assert entry[f"{SUB}_seconds_are"] == {"S-": "complete", "S+": "complete"}
    assert entry["cost_margin"] == control["cost_margin"] and math.isfinite(entry["cost_margin"])
    assert entry["reference_and_sensitivity_seconds_are"] == {"S-": "lower bound", "S+": "lower bound"}
    assert entry["actual_seconds_are"] == {"S-": "lower bound", "S+": "lower bound"} and entry["difference"] is None
    assert entry["physical_seconds_are"] == "lower bound"
    assert report["costs"]["physical_controller_seconds"] is None
