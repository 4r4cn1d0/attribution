"""The O-ext unit runner's command line is B15's contract (runkit/stage1-olmo/setup/job_runner_stage1.py
oext_unit_contract, lines 151-170, and the command forms its job_commands builds at lines 316-330 and 364-369 with
oext_args at 243-248; addendum section 20 point 5): the kit's parser is the frozen copy here, the script's parser has
exactly its options, and every command form the kit builds parses to the same values under both. Read with ast;
nothing of the kit runs. None of this is a scientific result."""

from __future__ import annotations

import contextlib
import io

import pytest

import oext_unit_fixtures as uf

ou = uf.ou
P = "data/kt-prepared/prepared-kt-dolly-olmo2"                                 # job_runner_stage1.PREPARED
REC = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json"          # rules.REC
REC_S = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json"  # rules.RECIPE_S
OEXT = ["--oext-bank", "inputs/oext_bank.json", "--oext-record", "inputs/oext_record.json"]     # oext_args
W118 = ["--w1-18-record", "inputs/overrefusal_checks.json"]
KIT_FORMS = [
    # J3, theta0 (job_commands: kind o_only, arm theta0)
    ["run", "--untuned", "--prepared", P, "--recipe", REC_S, *OEXT, "--out", "job-2/oext"],
    ["run", "--untuned", "--prepared", P, "--recipe", REC_S, *OEXT, *W118, "--out", "job-2/oext"],
    # J3, a regenerated a0 or R unit; Branch 128 adds the packed source unit (dev100_source)
    ["run", "--run", "round1/1101-a0-regen-a1", "--checkpoint", "e1", "--dev100-source", "inputs/source_unit-a0-1101",
     "--prepared", P, "--recipe", REC_S, *OEXT, *W118, "--out", "job-1/oext"],
    ["run", "--run", "round1/1102-R-regen-a1", "--checkpoint", "e1", "--prepared", P, "--recipe", REC_S, *OEXT,
     "--out", "job-1/oext"],
    # J4, LN-14's transfer report (always REC)
    ["transfer", "--untuned", "--prepared", P, "--recipe", REC, *OEXT, *W118, "--out", "job-3/transfer"],
    ["transfer", "--untuned", "--prepared", P, "--recipe", REC, *OEXT, "--out", "job-3/transfer"],
    # J9, J10, J18: the O-ext step after engine calibrate (@unit:I resolved to the unit folder)
    ["run", "--run", "round1/1102-edit-" + "a" * 64 + "-e1-a1", "--checkpoint", "e1", "--prepared", P, "--recipe",
     REC_S, *OEXT, *W118, "--out", "job-9/oext"],
    ["run", "--run", "round1/1104-a0-e1-a1", "--checkpoint", "e1", "--prepared", P, "--recipe", REC_S, *OEXT,
     "--out", "job-10/oext"],
]
BAD_FORMS = [
    ["run", "--prepared", P, "--recipe", REC, *OEXT, "--out", "o"],                               # no state
    ["run", "--untuned", "--run", "u", "--prepared", P, "--recipe", REC, *OEXT, "--out", "o"],    # both states
    ["run", "--run", "u", "--checkpoint", "q", "--prepared", P, "--recipe", REC, *OEXT, "--out", "o"],
    ["run", "--untuned", "--recipe", REC, *OEXT, "--out", "o"],                                   # no --prepared
    ["run", "--untuned", "--prepared", P, *OEXT, "--out", "o"],                                    # no --recipe
    ["run", "--untuned", "--prepared", P, "--recipe", REC, "--oext-record", "r", "--out", "o"],  # no --oext-bank
    ["run", "--untuned", "--prepared", P, "--recipe", REC, "--oext-bank", "b", "--out", "o"],    # no --oext-record
    ["run", "--untuned", "--prepared", P, "--recipe", REC, *OEXT],                                 # no --out
    ["check", "--untuned", "--prepared", P, "--recipe", REC, *OEXT, "--out", "o"],                 # no such command
    ["run", "--untuned", "--prepared", P, "--recipe", REC, *OEXT, "--out", "o", "--device", "cuda"],
]


def _parse(ap, args):
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            return vars(ap.parse_args(args))
        except SystemExit as exc:
            return ("exit", exc.code)


def test_the_kits_contract_is_the_frozen_copy():
    path = uf.kit_runner()
    if path is None:
        pytest.skip("B15's job_runner_stage1.py is not reachable from this workspace (the frozen copy is tested)")
    source, script = uf.kit_contract_source(path)
    assert source == uf.CONTRACT_SOURCE and uf.hashlib.sha256(source.encode()).hexdigest() == uf.CONTRACT_SHA256
    assert script == "scripts/stage1_s1/oext_unit.py" == ou.OWNER


def test_the_scripts_parser_has_exactly_the_contracts_options():
    assert uf.parser_shape(ou.parser()) == uf.parser_shape(uf.contract_parser())


@pytest.mark.parametrize("args", KIT_FORMS, ids=[f"kit-{k}" for k in range(len(KIT_FORMS))])
def test_every_kit_command_form_parses_the_same_under_both(args):
    mine, theirs = _parse(ou.parser(), args), _parse(uf.contract_parser(), args)
    assert isinstance(theirs, dict) and mine == theirs


@pytest.mark.parametrize("args", BAD_FORMS, ids=[f"bad-{k}" for k in range(len(BAD_FORMS))])
def test_a_form_outside_the_contract_fails_under_both(args):
    assert _parse(ou.parser(), args) == _parse(uf.contract_parser(), args) == ("exit", 2)
