"""F-4 (verify-F, 5 Nov 2026): ``noise_reading.environment_differs`` compares every one of Gate B's compared fields and
the guard record (Part 1 section 3.3 names an environment or guard-record difference as a trigger), but every committed
test and the RV2-2 file perturb ``gpu`` only, and the a0@1101 reference on this Mac is a Gate A unit without a guard record,
so a comparison that drops a field other than gpu (the verifier's V6: ``cudnn``) or inverts the guard comparison (V8)
survived all 35 tests. Here: (1) a synthetic family of six unit records, the fields ``GB.compared_fields`` gives on the
committed synthetic environment and one guard record on every unit, with one unit's guard changed gives ["guard"] on that
unit alone, and with one compared field changed (``cudnn`` among them, every field in turn) gives that field on that unit
alone; (2) through the real reader on the wave-0a units (skipped where absent), the records read as if every unit carried
a guard record and one differed, the whole attribution dict and the trigger. The guard rule is kept too: a unit without
a guard record is compared on its fields only. This file is new (the committed test file is tracked and unchanged); it
reuses that file's helpers by import. Labels, counts and hashes only; no text."""

from __future__ import annotations

import copy

import pytest

from scripts.scale78b import noise_reading as nr
from test_noise_reading import SYNTHETIC_ENVIRONMENT, needs_wave0a, parity_family, write_inputs

UNITS = ("a0@1101", "a0@1102", "a0@1103", "R@1101", "R@1102", "R@1103")
OTHERS = UNITS[1:]
GUARD = {"repo": "g", "revision": "r", "files": {"guard.py": "0" * 64}}
CHANGED_GUARD = {"repo": "g", "revision": "s", "files": {"guard.py": "0" * 64}}
FIELDS = nr.GB.compared_fields(SYNTHETIC_ENVIRONMENT, "1" * 64, {"name": "synthetic"})


def synthetic_units(guard: dict | None = GUARD) -> dict:
    """Six unit records in environment_differs' shape (fields and guard), every unit equal."""
    return {f"{role}@{s}": {"role": role, "seed": s, "fields": copy.deepcopy(FIELDS), "guard": copy.deepcopy(guard)}
            for role in ("a0", "R") for s in nr.SEEDS}


def attribution(units: dict) -> dict:
    """The reader's rule: every unit against a0@1101 (noise_reading.family_reading)."""
    return {label: nr.environment_differs(u, units["a0@1101"]) for label, u in units.items()}


def test_the_synthetic_fields_are_gate_bs_compared_fields_with_cudnn_and_the_policy():
    assert "cudnn" in FIELDS and "gpu" in FIELDS and "policy" in FIELDS and len(FIELDS) == 14
    assert FIELDS["cudnn"] == 8902 and FIELDS["gpu"] == "A100"


def test_equal_fields_and_equal_guard_records_record_nothing():
    assert attribution(synthetic_units()) == {u: [] for u in UNITS}


@pytest.mark.parametrize("label", OTHERS)
def test_a_changed_guard_record_on_one_unit_is_recorded_as_guard_on_that_unit_alone(label):
    units = synthetic_units()
    units[label]["guard"] = copy.deepcopy(CHANGED_GUARD)
    assert attribution(units) == {u: (["guard"] if u == label else []) for u in UNITS}


def test_a_changed_guard_record_on_the_reference_is_recorded_on_every_other_unit():
    units = synthetic_units()
    units["a0@1101"]["guard"] = copy.deepcopy(CHANGED_GUARD)
    assert attribution(units) == {u: ([] if u == "a0@1101" else ["guard"]) for u in UNITS}


def test_a_unit_without_a_guard_record_is_compared_on_its_fields_only():
    units = synthetic_units()
    units["R@1102"]["guard"] = None
    assert attribution(units) == {u: [] for u in UNITS}
    units["R@1102"]["fields"]["cudnn"] = 8907
    assert attribution(units) == {u: (["cudnn"] if u == "R@1102" else []) for u in UNITS}
    reference_without = synthetic_units()
    reference_without["a0@1101"]["guard"] = None
    reference_without["R@1103"]["guard"] = copy.deepcopy(CHANGED_GUARD)
    assert attribution(reference_without) == {u: [] for u in UNITS}                  # no guard on the reference: not compared


@pytest.mark.parametrize("field", sorted(FIELDS))
def test_each_compared_field_changed_on_one_unit_is_recorded_on_that_unit_alone(field):
    units = synthetic_units()
    units["R@1102"]["fields"][field] = "another value"
    assert attribution(units) == {u: ([field] if u == "R@1102" else []) for u in UNITS}


def test_cudnn_changed_on_the_reference_is_recorded_on_every_other_unit_and_a_field_and_the_guard_together_are_both_named():
    units = synthetic_units()
    units["a0@1101"]["fields"]["cudnn"] = 8907
    assert attribution(units) == {u: ([] if u == "a0@1101" else ["cudnn"]) for u in UNITS}
    both = synthetic_units()
    both["a0@1103"]["fields"]["cudnn"] = 8907
    both["a0@1103"]["guard"] = copy.deepcopy(CHANGED_GUARD)
    assert attribution(both) == {u: (["cudnn", "guard"] if u == "a0@1103" else []) for u in UNITS}


# ----- through the real reader on the wave-0a units ----------------------------------------------------------------------


def guarded_reader(changed: tuple[str, int] | None, field: tuple[str, object] | None = None):
    """read_unit with every unit read as if it carried the same guard record, the ``changed`` unit's guard differing, and
    (optionally) one field of that unit changed; the files are untouched."""
    real = nr.read_unit

    def read_unit(spec, role, seed, family, engine, where, base):
        unit = {**real(spec, role, seed, family, engine, where, base), "guard": copy.deepcopy(GUARD)}
        if (role, seed) == changed:
            if field is None:
                unit["guard"] = copy.deepcopy(CHANGED_GUARD)
            else:
                unit["fields"] = {**unit["fields"], field[0]: field[1]}
        return unit
    return read_unit


@needs_wave0a
@pytest.mark.parametrize("role_seed", [("a0", 1102), ("R", 1103)])
def test_through_the_reader_a_guard_difference_on_one_unit_triggers_the_fallback_on_that_unit_alone(tmp_path, monkeypatch, role_seed):
    monkeypatch.setattr(nr, "read_unit", guarded_reader(role_seed))
    fam = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))["families"]["olmo2-1b"]
    label = f"{role_seed[0]}@{role_seed[1]}"
    assert fam["triggers"]["environment_differs"] == {u: (["guard"] if u == label else []) for u in UNITS}
    assert fam["triggers"]["environment"] and fam["triggers"]["fallback"] and fam["governing"] == "fallback"
    assert all(u["guard_record"] for u in fam["units"].values()) and len(fam["units"]) == 6


@needs_wave0a
def test_through_the_reader_a_guard_difference_on_the_reference_is_recorded_on_every_other_unit(tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "read_unit", guarded_reader(("a0", 1101)))
    fam = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))["families"]["olmo2-1b"]
    assert fam["triggers"]["environment_differs"] == {u: ([] if u == "a0@1101" else ["guard"]) for u in UNITS}
    assert fam["triggers"]["environment"] and fam["governing"] == "fallback"


@needs_wave0a
def test_through_the_reader_a_cudnn_difference_on_one_unit_triggers_the_fallback_on_that_unit_alone(tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "read_unit", guarded_reader(("R", 1101), ("cudnn", "another cudnn")))
    fam = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))["families"]["olmo2-1b"]
    assert fam["triggers"]["environment_differs"] == {u: (["cudnn"] if u == "R@1101" else []) for u in UNITS}
    assert fam["triggers"]["environment"] and fam["governing"] == "fallback"


@needs_wave0a
def test_through_the_reader_equal_guard_records_on_every_unit_record_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "read_unit", guarded_reader(None))
    fam = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))["families"]["olmo2-1b"]
    assert fam["triggers"]["environment_differs"] == {u: [] for u in UNITS}
    assert not fam["triggers"]["environment"] and fam["governing"] == "plain"
    assert all(u["guard_record"] for u in fam["units"].values())
