"""RV2-2 (the second re-verifier's gap, reverify-BC2.md section 7): the noise reader's environment reference is a0@1101
(``noise_reading.py``: ``reference = units[("a0", SEEDS[0])]``; Gate B's rule). The committed R4 test perturbs a0@1102
only, which any reference other than a0@1102 passes, so mutants with a0@1103 or R@1101 as the reference survived it.

Here the reference itself is perturbed: the a0@1101 unit is read as if its GPU name differed (the record ``read_unit``
returns is changed; the files are untouched), and the whole attribution dict is asserted: the reference records nothing
and every other unit records ["gpu"] (measured on the real code by the re-verifier, ``r4_probe_out.txt``, and here).
Under a reference of a0@1103 or R@1101 the dict would be ["gpu"] on a0@1101 alone, so both survivors fail. A second
test pins the attribution for a perturbation of each other unit (that unit alone). The units are the Gate B wave-0a and
Gate A units on this Mac, read through the frozen reader only (counts, hashes and labels; no text); the tests skip
where those folders are absent. This file is new (the committed test file is tracked and unchanged); it reuses that
file's helpers by import."""

from __future__ import annotations

import pytest

from scripts.scale78b import noise_reading as nr
from test_noise_reading import needs_wave0a, parity_family, write_inputs

UNITS = ("a0@1101", "a0@1102", "a0@1103", "R@1101", "R@1102", "R@1103")


def perturbed_reader(role_seed: tuple[str, int]):
    """read_unit with one unit's GPU name changed in the record it returns (the files are untouched)."""
    real = nr.read_unit

    def read_unit(spec, role, seed, family, engine, where, base):
        unit = real(spec, role, seed, family, engine, where, base)
        if (role, seed) == role_seed:
            unit = {**unit, "fields": {**unit["fields"], "gpu": "another device"}}
        return unit
    return read_unit


@needs_wave0a
def test_an_environment_difference_on_the_reference_a0_1101_is_recorded_on_every_other_unit(tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "read_unit", perturbed_reader(("a0", 1101)))
    fam = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))["families"]["olmo2-1b"]
    assert fam["triggers"]["environment_differs"] == {"a0@1101": [], "a0@1102": ["gpu"], "a0@1103": ["gpu"],
                                                      "R@1101": ["gpu"], "R@1102": ["gpu"], "R@1103": ["gpu"]}
    assert fam["triggers"]["environment"] and fam["triggers"]["fallback"] and fam["governing"] == "fallback"
    assert round(fam["sigma_F_pp"], 2) == 2.16


@needs_wave0a
@pytest.mark.parametrize("role_seed", [("a0", 1102), ("a0", 1103), ("R", 1101), ("R", 1102), ("R", 1103)])
def test_an_environment_difference_on_any_other_unit_is_recorded_on_that_unit_alone(tmp_path, monkeypatch, role_seed):
    monkeypatch.setattr(nr, "read_unit", perturbed_reader(role_seed))
    fam = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))["families"]["olmo2-1b"]
    label = f"{role_seed[0]}@{role_seed[1]}"
    assert fam["triggers"]["environment_differs"] == {u: (["gpu"] if u == label else []) for u in UNITS}
    assert fam["triggers"]["environment"] and fam["governing"] == "fallback"


@needs_wave0a
def test_no_perturbation_records_nothing_and_the_plain_reading_governs(tmp_path):
    fam = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))["families"]["olmo2-1b"]
    assert fam["triggers"]["environment_differs"] == {u: [] for u in UNITS}
    assert not fam["triggers"]["environment"] and fam["governing"] == "plain"
