"""Scratch reproductions (review of durability-safeguards-20261003). Each test asserts the CORRECT
behaviour, so it fails on the reviewed candidate if the finding is real. ENGINEERING FIXTURES only."""

from __future__ import annotations

import os
import sys
from pathlib import Path

WS = Path(os.environ["DUR_WS"]).resolve()
for p in (WS, WS / "experiments" / "safety_selection" / "tests", WS / "experiments" / "durability" / "tests"):
    sys.path.insert(0, str(p))

import pytest  # noqa: E402

import dur_fixtures as dur  # noqa: E402
import ss_fixtures as fx  # noqa: E402

from experiments.durability.common import AdmissionRefused  # noqa: E402
from experiments.durability.units import prepared_unit  # noqa: E402
from experiments.safety_decision_policy.common import read_canonical, read_json_strict  # noqa: E402
from experiments.safety_decision_policy.synthetic import FakeBackend, make_world, prepare_synthetic  # noqa: E402

import test_dur_stage_b as sb  # noqa: E402  (its Site helper)
import test_dur_admission as ad  # noqa: E402  (its World helper)


def test_A_a_crash_between_a_prepared_acknowledgement_and_its_pin_does_not_block_forever(tmp_path):
    root = (tmp_path / "pod").resolve()
    prepared, sha = fx.prepare_dir(root / "prepared")
    dying = dur.make_vault(tmp_path, destination=dur.FaultyDestination(tmp_path / "destination", crash_on="pins"))
    with pytest.raises(KeyboardInterrupt):           # the process dies at the pin write, after the ack
        dying.acknowledge(prepared_unit(str(prepared)))
    vault = dur.make_vault(tmp_path)
    assert vault.read_ack(prepared_unit(str(prepared)).unit_id) is not None   # acknowledged ...
    vault.acknowledge(prepared_unit(str(prepared)))   # the retry (a duplicate event)
    assert vault.pin("prepared", sha) is not None      # ... and the identity must now be pinned


def test_B_a_second_worker_cannot_spend_the_first_worker_s_retention_reserve(tmp_path):
    hour = 3600.0
    need = ad.expected_need(hour)
    balance = 2 * need + dur.RESERVE + 0.01           # room for both computes but only ONE retention reserve
    world = ad.World(tmp_path, balance=balance)
    world.admit("worker-1")
    with pytest.raises(AdmissionRefused):
        world.admit("worker-2")                       # worker-1's volume still needs its reserve after compute


def test_C_two_gated_blocks_on_one_backend_in_one_process_do_not_claim_a_fresh_process(tmp_path):
    world = make_world()
    configs = WS / "experiments" / "safety_decision_policy" / "configs"
    setup = prepare_synthetic(tmp_path / "development", world, template=read_json_strict(configs / "example-engineering.json"),
                              spec=read_json_strict(configs / "example-dev-fit-spec.json"))
    site = sb.Site(tmp_path / "site", world, setup)
    inner = FakeBackend(world)                        # one engine session (asset cache) for the process
    site.admit()
    site.run(inner, block=0)
    site.admit()
    try:
        site.run(inner, block=1)                      # the same warm backend serves a second block
    except Exception as exc:                          # a refusal is an acceptable outcome
        print("second block refused:", type(exc).__name__, exc)
        return
    record = read_canonical(site.root / "blocks" / "1" / "sessions" / "session-1.json")
    assert record["process_shared_with_an_earlier_block"] is True, (
        "the second block's session claims a fresh process although its backend already served block 0: "
        "its setup is unmeasured but would be labelled measured")
