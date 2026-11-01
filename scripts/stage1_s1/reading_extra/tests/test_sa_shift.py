"""The S-a shift line (sa_shift.py; REV4:276): the expectation as written; the measured S-a - HB of P4 by hand from
the U table (S-a's unpaired means over all seeds against HB's paired mean on the common seeds); plan B (no P4); the
refusals; the command line (the file and its SHA-256 only)."""

from __future__ import annotations

import copy
import json
import math

import numpy as np
import pytest
import synth_kit as sk

from scripts.stage1_s1.reading.settings import Refusal
from scripts.stage1_s1.reading_extra import sa_shift as sa


def test_the_expectation_is_rev4s():
    rev4 = (sk.TREE / "research" / "experiments" / "2026-10-17-stage1-preregistration-rev3" /
            "stage1-preregistration-rev4.md")
    if not rev4.is_file():
        pytest.skip("the pre-registration is not in this tree")
    assert sa.EXPECTED_TEXT in rev4.read_text().replace("**", "") and sa.EXPECTED_SHIFT_PP == -0.28   # bold dropped


@pytest.mark.parametrize("reading", ["plan_a_block_a_only", "plan_a"])
def test_the_measured_shift_by_hand(pipeline, reading):
    s, docs, _ = pipeline(reading)
    out = sa.line(docs["reading"], "r" * 64)
    u = docs["tables"]["endpoints"]["U"]["cells"]
    cell = {(a, int(j)): 100 * float(np.mean(v)) for a, per in u.items() for j, v in per.items()}
    a0 = [j for a, j in cell if a == "a0"]
    s1 = [j for a, j in cell if a == "S1"]
    s_a = np.mean([cell[("a0", j)] for j in a0]) - np.mean([cell[("S1", j)] for j in s1])
    common = sorted(set(a0) & set(s1))
    hb = np.mean([cell[("a0", j)] - cell[("S1", j)] for j in common])
    m = out["measured"]
    assert math.isclose(m["s_a_estimate_pp"], s_a, abs_tol=1e-9) and math.isclose(m["hb_estimate_pp"], hb, abs_tol=1e-9)
    assert m["s_a_minus_hb_pp"] == m["s_a_estimate_pp"] - m["hb_estimate_pp"]
    assert m["s_a_estimate_pp"] == docs["reading"]["sensitivities"]["S-a"]["P4"]["estimate"]["est"]
    assert m["hb_estimate_pp"] == docs["reading"]["sensitivities"]["HB"]["P4"]["estimate"]["est"]
    assert m["primary_estimate_pp"] == docs["reading"]["contrasts"]["P4"]["U"]["est"]
    assert m["direction"] == ("less in S1's favour" if m["s_a_minus_hb_pp"] < 0 else "more in S1's favour")
    assert m["expected_direction_holds"] is (m["s_a_minus_hb_pp"] < 0)
    assert out["applies"] is True and out["note"] is None
    assert out["expected"] == {"s_a_minus_hb_pp": -0.28, "text": sa.EXPECTED_TEXT, "computed_under": "D0",
                               "source": "M (VR-B)"}


def test_plan_b_has_no_p4(pipeline):
    s, docs, _ = pipeline("plan_b")
    out = sa.line(docs["reading"], "r" * 64)
    assert out["applies"] is False and out["measured"] is None
    assert out["note"] == "not applicable: P4 is not a contrast of the reading plan_b"
    assert out["expected"]["s_a_minus_hb_pp"] == -0.28


def test_the_direction_words(pipeline):
    s, docs, _ = pipeline("plan_a_block_a_only")
    for shift, word in ((0.5, "more in S1's favour"), (0.0, "no shift"), (-0.5, "less in S1's favour")):
        r = copy.deepcopy(docs["reading"])
        r["sensitivities"]["S-a"]["P4"]["estimate"]["est"] = r["sensitivities"]["HB"]["P4"]["estimate"]["est"] + shift
        assert sa.line(r, "r" * 64)["measured"]["direction"] == word


@pytest.mark.parametrize("edit,match", [
    (lambda r: r["sensitivities"].pop("S-a"), "no S-a estimate of P4"),
    (lambda r: r["sensitivities"]["HB"]["P4"].pop("estimate"), "no HB estimate of P4"),
    (lambda r: r["sensitivities"]["HB"]["P4"]["estimate"].update(est=None), "the HB estimate of P4 is not a finite"),
    (lambda r: r["contrasts"]["P4"]["U"].update(est="x"), "the primary U estimate of P4"),
    (lambda r: r.update(reading="plan_x"), "not B16's version-1 output"),
])
def test_refusals(pipeline, edit, match):
    s, docs, _ = pipeline("plan_a_block_a_only")
    r = copy.deepcopy(docs["reading"])
    edit(r)
    with pytest.raises(Refusal, match=match):
        sa.line(r, "r" * 64)


def test_command_line(pipeline, tmp_path, capsys):
    s, docs, paths = pipeline("plan_a_block_a_only")
    out = tmp_path / "sa.json"
    assert sa.main(["--reading", str(paths["reading"]), "--out", str(out)]) == 0
    assert capsys.readouterr().out == f"wrote {out} sha256 {sk.sha(out.read_bytes())}\n"
    assert json.loads(out.read_text())["provenance"]["inputs"] == {"reading.json": sk.sha(paths["reading"].read_bytes())}
    assert sa.main(["--reading", str(paths["reading"]), "--out", str(out)]) == 2
