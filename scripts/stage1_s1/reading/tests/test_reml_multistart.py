"""Post-W1 deviation D-4 (addendum 33 point 2): every REML fit runs from the pre-registered start and from each floor
pattern of its block; the end point with the highest REML log-likelihood governs; the pre-registered start's fit is
printed beside it (S-start) with a flag. Checks: the start set; the options; hand cases of the selection rule; seven
of the independent verifier's miss cases (d4_fixtures.json, its seeded generator) reach its global maximum while
the pre-registered start alone does not; the verifier's one label change; nothing changes where the pre-registered
start already reaches the maximum (estimates, SE, df, labels). Synthetic data only."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import numpy as np
import pytest

import halves_synth as hs
import synth
from scripts.stage1_s1.reading import reml
from scripts.stage1_s1.reading import settings as st
from scripts.stage1_s1.reading.reading import read

FIXTURES = json.loads((Path(__file__).resolve().parent / "d4_fixtures.json").read_text())["cases"]
OPTS = reml.options(st.settings())


def cells_of(case):
    return [(a, int(j), float(v)) for a, j, v in case["cells"]], tuple(case["arms"])


def table(rng, arms, sig, seeds_of, shift=3.0):
    seeds = sorted({j for a in arms for j in seeds_of(a)})
    s = {j: rng.normal(0, shift) for j in seeds}
    return [(a, j, 10.0 * i + s[j] + rng.normal(0, math.sqrt(sig[a]))) for i, a in enumerate(arms) for j in seeds_of(a)]


def d1(a):
    return range(1101, 1108) if a in ("a0", "R") else range(1102, 1108)


# ----- the start set and the options ----------------------------------------------------------------------------------


def test_the_start_set_is_every_floor_pattern_in_a_fixed_order():
    pats = reml.floor_patterns(("a0", "S1", "S3", "S4"))
    assert len(pats) == 15 and pats[:5] == (("a0",), ("S1",), ("S3",), ("S4",), ("a0", "S1"))
    assert pats[-1] == ("a0", "S1", "S3", "S4")
    assert len(reml.floor_patterns(tuple("abcdefgh"))) == 255
    assert reml.floor_patterns(("a", "b", "c"), not_identified=("b",)) == (("a",), ("c",), ("a", "c"))


def test_the_options_carry_the_start_rule_and_refuse_an_unknown_one():
    cfg = copy.deepcopy(st.settings())
    assert OPTS["multi_start"] is True and OPTS["ll_tol"] == 1e-6
    assert cfg["reml"]["starts"] == "multi" and "D-4" in cfg["reml"]["starts_rule"]
    cfg["reml"]["starts"] = "pre-registered"
    assert reml.options(cfg)["multi_start"] is False
    cfg["reml"]["starts"] = "random"
    with pytest.raises(reml.RemlError):
        reml.options(cfg)


def test_the_contrast_loglik_is_reml_loglik_plus_a_constant():
    rng = np.random.default_rng(3)
    arms = ("a0", "S1", "S3", "S4")
    cells = table(rng, arms, {"a0": 4.0, "S1": 9.0, "S3": 1.0, "S4": 16.0}, d1)
    basis = reml.contrast_basis(cells, arms)
    diffs = []
    for _ in range(6):
        s2 = dict(zip(arms, np.exp(rng.normal(0, 1.5, 4))))
        diffs.append(reml.loglik_contrasts(basis, s2, arms) - reml.reml_loglik(cells, arms, s2))
    assert np.ptp(diffs) < 1e-9


# ----- hand cases of the selection rule --------------------------------------------------------------------------------


def test_where_the_pre_registered_start_reaches_the_maximum_its_fit_is_returned_unchanged():
    rng = np.random.default_rng(12)
    arms = ("a0", "S1", "S3", "S4")
    checked = 0
    for _ in range(10):
        cells = table(rng, arms, {"a0": 4.0, "S1": 9.0, "S3": 2.0, "S4": 16.0}, d1)
        one = reml.fit_cells(cells, arms, 0.01, **{**OPTS, "multi_start": False})
        many = reml.fit_cells(cells, arms, 0.01, **OPTS)
        assert many.starts == 16 and many.prereg is not None
        assert many.prereg.sigma2 == one.sigma2 and many.prereg.iterations == one.iterations
        if not many.start_differs:
            checked += 1
            assert many.sigma2 == one.sigma2 and np.array_equal(many.info_inv, one.info_inv)
            assert many.governing_start == "pre-registered" and many.at_floor == one.at_floor
        else:
            assert many.loglik > many.prereg.loglik + 1e-6
    assert checked >= 8


def test_the_tolerance_decides_and_a_two_arm_fit_runs_once():
    case = FIXTURES[0]
    cells, arms = cells_of(case)
    keep = reml.fit_cells(cells, arms, 0.01, **{**OPTS, "ll_tol": 1e9})        # nothing beats the pre-registered start
    assert not keep.start_differs and keep.governing_start == "pre-registered" and keep.sigma2 == keep.prereg.sigma2
    best = reml.fit_cells(cells, arms, 0.01, **{**OPTS, "ll_tol": 0.0})
    assert best.start_differs and best.loglik > keep.loglik + 1e-3
    two = reml.fit_cells([(a, j, v) for a, j, v in cells if a in arms[:2]], arms[:2], 0.01, **OPTS)
    assert two.two_arm and two.starts == 1 and two.prereg is None and not two.start_differs


# ----- the verifier's miss cases ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", FIXTURES, ids=[c["source"].split("py ")[1] for c in FIXTURES])
def test_the_verifiers_miss_cases_reach_its_global_maximum(case):
    """The pre-registered start alone reproduces B16's old end point exactly (the verifier's s2_b16) and misses the
    verifier's global maximum by more than 1e-3; the multi-start fit reaches it (to 1e-6) from a floor pattern, and
    prints the pre-registered start's fit beside it with both floored sets."""
    cells, arms = cells_of(case)
    one = reml.fit_cells(cells, arms, case["floor"], **{**OPTS, "multi_start": False})
    assert np.allclose([one.sigma2[a] for a in arms], case["verifier_s2_b16"], rtol=1e-9)
    fit = reml.fit_cells(cells, arms, case["floor"], **OPTS)
    basis = reml.contrast_basis(cells, arms)
    best = reml.loglik_contrasts(basis, dict(zip(arms, case["verifier_s2_best"])), arms)
    assert fit.prereg.loglik < best - 1e-3
    assert fit.loglik >= best - 1e-6
    assert fit.start_differs and fit.governing_start.startswith("floor pattern")
    assert fit.prereg.sigma2 == one.sigma2 and fit.prereg.at_floor == one.at_floor
    assert set(fit.at_floor) != set(fit.prereg.at_floor) or fit.converged != fit.prereg.converged


def test_the_verifiers_label_change_is_governed_by_the_maximum_and_shown_as_s_start():
    """The verifier's block-A-only document (part_b.py het, seed 4003): with the pre-registered start P4 reads
    'better'; at the REML maximum it reads 'inconclusive'. The reading now prints 'inconclusive' and carries the
    pre-registered start's 'better' in P4's sensitivity part (S-start)."""
    het = {"a0": 0.5, "S1": 3.0, "S3": 1.0, "S4": 2.0, "R": 0.5, "A1": 3.0, "L1": 1.0, "H1": 2.0}
    doc = synth.make_input(4003, "plan_a_block_a_only", arm_sd=het, prompt_sd=3.0)
    out = read(doc)
    assert out["fits"]["U"]["full"]["start_differs"]
    assert out["headline"]["P4"] == "inconclusive"
    s = out["sensitivities"]["S-start"]
    assert "U full" in s["fits_where_the_start_differs"]
    assert s["contrasts"]["P4"]["headline"] == "better" and s["contrasts"]["P4"]["differs_from_primary"]
    assert any(p.get("code") == "S-start" and p["headline_word"] == "better" for p in out["rows"]["P4"]["sensitivity_part"])
    assert any("D-4" in n and n.startswith("U full") for n in out["notes"])


def test_s_start_is_the_reading_from_the_pre_registered_start(monkeypatch):
    """Where a primary fit's start differs, S-start's U estimates, p-values and words are the reading run with the
    pre-registered start alone (starts 'pre-registered')."""
    het = {"a0": 0.5, "S1": 3.0, "S3": 1.0, "S4": 2.0, "R": 0.5, "A1": 3.0, "L1": 1.0, "H1": 2.0}
    doc = synth.make_input(4003, "plan_a_block_a_only", arm_sd=het, prompt_sd=3.0)
    multi = read(copy.deepcopy(doc))
    alt = copy.deepcopy(st.settings())
    alt["reml"]["starts"] = "pre-registered"
    monkeypatch.setattr(st, "_SETTINGS", alt)
    single = read(copy.deepcopy(doc))
    monkeypatch.setattr(st, "_SETTINGS", None)
    s = multi["sensitivities"]["S-start"]["contrasts"]
    for name, k in single["contrasts"].items():
        assert s[name]["U"] == k["U"] and s[name]["U_interval_90"] == k["U_interval_90"]
        assert s[name]["p_values"] == k["p_values"] and s[name]["headline"] == single["headline"][name]
    assert multi["sensitivities"]["S-start"]["phi_rejected"] == single["phi"]["rejected"]


# ----- nothing changes where the old fit was already the maximum ---------------------------------------------------------


LABEL_KEYS = ("contrasts", "phi", "rows", "headline", "headline_cells", "arms", "best_feasible_repair", "actors")


def _without_d4(out: dict) -> dict:
    """The output with D-4's own records removed (fit start records, S-start, start_records, the D-4 notes)."""
    o = copy.deepcopy(out)
    for e in o["fits"].values():
        for f in e.values():
            for k in ("governing_start", "starts", "loglik", "start_differs", "prereg_start"):
                f.pop(k, None)
    o["sensitivities"].pop("S-start", None)
    o["sensitivities"].pop("start_records", None)
    o["references"].pop("start_records", None)
    o["notes"] = [n for n in o["notes"] if "D-4" not in n]
    oc = o["overlap_control"]
    if oc.get("computed"):
        for rec in oc["fits"].values():
            for f in rec.values():
                if isinstance(f, dict):
                    for k in ("governing_start", "starts", "loglik", "start_differs", "prereg_start"):
                        f.pop(k, None)
    o.pop("provenance", None)
    return o


def test_nothing_changes_where_every_fit_already_reached_the_maximum(monkeypatch):
    """Whole readings (plan A, block A only, plan B; references and the halves included) under starts 'multi' and
    'pre-registered': where no fit's start differs, every estimate, SE, df, interval, label and verdict is equal."""
    alt = copy.deepcopy(st.settings())
    alt["reml"]["starts"] = "pre-registered"
    compared = 0
    candidates = [(s, r) for s in (31, 32, 34, 35, 36) for r in ("plan_a", "plan_a_block_a_only", "plan_b")]
    for seed, reading in candidates:
        if compared >= 4:
            break
        doc = synth.make_input(seed, reading, references=[("point", "SP", list(range(1102, 1108)))] if reading == "plan_a" else None)
        rng = np.random.default_rng(seed)
        doc["overlap"] = hs.overlap_block(doc, {m: hs.similarity(rng) for m in ("S1", "S3", "S4")})
        multi = read(copy.deepcopy(doc))
        flags = [f["start_differs"] for e in multi["fits"].values() for f in e.values()]
        flags += [f["start_differs"] for r in multi["overlap_control"]["fits"].values() for f in r.values() if isinstance(f, dict)]
        flags.append(multi["sensitivities"]["start_records"]["HB"]["start_differs"])
        flags += [f.get("start_differs", False) for v in multi["sensitivities"]["start_records"]["S-G"].values() for f in v.values()]
        flags += [f["start_differs"] for r in multi["references"].get("start_records", {}).values() for f in r.values()]
        if any(flags):
            continue
        monkeypatch.setattr(st, "_SETTINGS", alt)
        single = read(copy.deepcopy(doc))
        monkeypatch.setattr(st, "_SETTINGS", None)
        a, b = _without_d4(multi), _without_d4(single)
        for key in LABEL_KEYS:
            assert a[key] == b[key], key
        assert a["overlap_control"]["contrasts"] == b["overlap_control"]["contrasts"]
        assert {k: v for k, v in a["sensitivities"].items()} == {k: v for k, v in b["sensitivities"].items()}
        compared += 1
    assert compared >= 4
