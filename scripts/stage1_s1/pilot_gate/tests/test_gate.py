"""The gate's rule and interval (gate.py): known answers (t(0.90, 2) = 1.886 when the item part is 0), the sign, the
edges at 10 and 5 pp on exact three-seed means of 600-answer shares (steps of 1/18 pp) that land below in floating
point, Lambda >= 10 with a lower bound <= 5 reads stop, a lower bound of exactly 5.0 is not above 5, the re-pilot
never raises, section 40 point 2's constructed case (the frozen form stops, the seed part alone would go), an
independent from-scratch recomputation of the paired form on random tables, B16's pins, the rule text."""

from __future__ import annotations

import json
import math
from fractions import Fraction

import numpy as np
import pytest

from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import tdist
from scripts.stage1_s1.reading.labels import tie_tolerance
from scripts.stage1_s1.reading.settings import Refusal, module_hashes
from scripts.stage1_s1.pilot_gate import gate

try:
    import synth_kit as sk
    TREE = sk.TREE
except ImportError:                                   # pragma: no cover - conftest puts the builder's tests first
    TREE = None
P = 200
SEEDS = gate.SEEDS
STEP_PP = 100.0 / (3 * P * 3)                        # one answer of one seed moves the three-seed mean 1/18 pp


def table_from_counts(c: dict, m: dict) -> dict:
    """{(arm, seed): shares} from per-seed count arrays (0..3 per prompt)."""
    out = {}
    for j in SEEDS:
        out[("a0_plant", j)] = np.asarray(c[j], dtype=float) / 3.0
        out[("a0", j)] = np.asarray(m[j], dtype=float) / 3.0
    return out


def rational_lambda(c: dict, m: dict) -> Fraction:
    total = sum(int(c[j][p]) - int(m[j][p]) for j in SEEDS for p in range(P))
    return Fraction(100 * total, 3 * P * 3)


def counts_with_total_difference(rng, totals: dict, base_level: float = 0.5) -> tuple[dict, dict]:
    """m random; c = m plus ``totals[j]`` single-answer raises on random prompts (so the per-seed count difference
    is exactly totals[j]), plus a few paired +1/-1 moves that leave the total."""
    c, m = {}, {}
    for j in SEEDS:
        base = rng.binomial(3, base_level, P)
        delta = np.zeros(P, dtype=int)
        room = 3 - base
        for _ in range(totals[j]):
            where = rng.choice(np.flatnonzero(room - delta > 0))
            delta[where] += 1
        for _ in range(20):                           # noise that keeps the total
            up = rng.choice(np.flatnonzero(room - delta > 0))
            down = rng.choice(np.flatnonzero(base + delta > 0))
            if up != down:
                delta[up] += 1
                delta[down] -= 1
        m[j], c[j] = base, base + delta
        assert c[j].min() >= 0 and c[j].max() <= 3 and int((c[j] - m[j]).sum()) == totals[j]
    return c, m


# ----- known answers ---------------------------------------------------------------------------------------------------


def test_t_quantile_known_answers():
    assert round(tdist.t_quantile(0.90, 2), 3) == 1.886
    assert abs(tdist.t_quantile(0.90, 10) - 1.3722) < 5e-4
    assert abs(tdist.t_quantile(0.90, 1e6) - 1.2816) < 5e-4


def test_item_part_zero_gives_df_2_and_t_1_886():
    """Rows constant over prompts: no prompt effect, so the item part is 0, df = J - 1 = 2 and t = 1.886."""
    m = {j: np.ones(P, dtype=int) for j in SEEDS}                      # 1/3 everywhere
    c = {1101: np.full(P, 2), 1102: np.full(P, 3), 1103: np.full(P, 2)}  # differences 1/3, 2/3, 1/3
    r = gate.read(table_from_counts(c, m), "pilot")
    e = r["estimate"]
    assert e["item_var"] == 0.0 and e["item_q"] == 0.0 and e["df"] == 2.0 and e["with_item"] is True
    assert e["pairs"] == 3 and e["items"] == P
    diffs = np.array([100 / 3, 200 / 3, 100 / 3])
    assert math.isclose(e["est"], diffs.mean(), abs_tol=1e-9)
    assert math.isclose(e["se"], math.sqrt(diffs.var(ddof=1) / 3), abs_tol=1e-9)
    assert math.isclose(r["t_quantile"], tdist.t_quantile(0.90, 2)) and round(r["t_quantile"], 3) == 1.886
    assert math.isclose(r["lower_bound_pp"], e["est"] - 1.8856180831635356 * e["se"], abs_tol=1e-9)
    assert r["label"] == "go" and r["reads"] == {"estimate_at_least_10_pp": True, "estimate_at_least_5_pp": True,
                                                 "lower_bound_above_5_pp": True}


def test_the_sign_is_c_minus_m():
    m = {j: np.zeros(P, dtype=int) for j in SEEDS}
    c = {j: np.full(P, 3) for j in SEEDS}
    c[1102][0], c[1103][:2] = 2, 2                                    # a little variance, or B16 refuses the table
    table = table_from_counts(c, m)
    est = gate.estimate(table, "pilot")
    assert 99.0 < est.est < 100.0 and est.name == "Lambda_plant"
    swapped = {("a0", j): table[("a0_plant", j)] for j in SEEDS} | {("a0_plant", j): table[("a0", j)] for j in SEEDS}
    assert gate.estimate(swapped, "pilot").est == -est.est
    with pytest.raises(Refusal, match="no finite degrees of freedom"):          # identical cells: B16's own refusal
        gate.estimate(table_from_counts({j: np.full(P, 3) for j in SEEDS}, m), "pilot")


def test_estimate_is_b16s_contrast_paired_with_the_item_part():
    rng = np.random.default_rng(3)
    c, m = counts_with_total_difference(rng, {1101: 70, 1102: 50, 1103: 60})
    table = table_from_counts(c, m)
    want = con.contrast_paired(table, "a0_plant", "a0", SEEDS, 100.0, True, "x", "y")
    got = gate.estimate(table, "pilot")
    assert (got.est, got.se, got.df, got.seed_var, got.seed_df, got.item_var, got.item_q) == \
        (want.est, want.se, want.df, want.seed_var, want.seed_df, want.item_var, want.item_q)
    assert got.with_item is True and got.pairs == 3 and got.items == P
    with pytest.raises(Refusal, match="not pilot or re-pilot"):
        gate.estimate(table, "pilot75")


# ----- the label -------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("est,lower,mode,want", [
    (12.0, 6.0, "pilot", "go"), (10.0, 5.000001, "pilot", "go"), (12.0, 5.0, "pilot", "stop"),
    (12.0, 4.99, "pilot", "stop"), (10.0, 5.0, "pilot", "stop"), (9.99, 9.0, "pilot", "raise"),
    (5.0, 4.0, "pilot", "raise"), (7.5, -3.0, "pilot", "raise"), (4.99, 4.0, "pilot", "stop"), (-2.0, -9.0, "pilot", "stop"),
    (12.0, 6.0, "re-pilot", "go"), (12.0, 5.0, "re-pilot", "stop"), (9.99, 9.0, "re-pilot", "stop"),
    (5.0, 4.0, "re-pilot", "stop"), (7.5, 7.0, "re-pilot", "stop"), (4.99, 4.0, "re-pilot", "stop"),
])
def test_the_label_by_the_written_rule(est, lower, mode, want):
    tol = tie_tolerance()
    assert tol == 1e-9
    assert gate.label(gate.reads(est, lower, tol), mode) == want


def test_a_lower_bound_of_exactly_5_is_not_above_5():
    tol = tie_tolerance()
    assert gate.reads(12.0, 5.0, tol)["lower_bound_above_5_pp"] is False
    assert gate.reads(12.0, 5.0 + 1e-12, tol)["lower_bound_above_5_pp"] is True
    assert gate.reads(12.0, 5.0 - 1e-12, tol)["lower_bound_above_5_pp"] is False
    assert gate.label(gate.reads(12.0, 5.0, tol), "pilot") == "stop"


def test_the_estimate_reads_through_the_tie_tolerance_and_the_bound_exactly():
    tol = tie_tolerance()
    r = gate.reads(10.0 - 1e-15, 9.0, tol)
    assert r["estimate_at_least_10_pp"] is True and gate.label(r, "pilot") == "go"
    r = gate.reads(10.0 - 2e-9, 9.0, tol)
    assert r["estimate_at_least_10_pp"] is False and gate.label(r, "pilot") == "raise"
    r = gate.reads(5.0 - 1e-15, 1.0, tol)
    assert r["estimate_at_least_5_pp"] is True and gate.label(r, "pilot") == "raise"
    r = gate.reads(5.0 - 2e-9, 1.0, tol)
    assert r["estimate_at_least_5_pp"] is False and gate.label(r, "pilot") == "stop"


def test_re_pilot_mode_never_says_raise():
    tol = tie_tolerance()
    for est in np.linspace(-5, 20, 101):
        for lower in np.linspace(-10, 15, 51):
            r = gate.reads(float(est), float(lower), tol)
            word = gate.label(r, "re-pilot")
            assert word in ("go", "stop") and word != "raise"
            assert (word == "go") == (r["estimate_at_least_10_pp"] and r["lower_bound_above_5_pp"])
            pilot = gate.label(r, "pilot")
            assert pilot == word or (pilot == "raise" and word == "stop")
    with pytest.raises(Refusal, match="not pilot or re-pilot"):
        gate.label(gate.reads(12.0, 6.0, tol), "pilot75")


# ----- the edges on exact shares -------------------------------------------------------------------------------------------


def _edge_cases(rng, bar_pp: float, tries: int = 3000):
    """Count tables whose three-seed mean equals ``bar_pp`` exactly as a rational; returns one whose float lands
    below the bar and one that lands at or above it (EV2:179: 627 of 2,000 exact 10 pp means land below 10.0)."""
    total = int(Fraction(bar_pp) * 3 * P * 3 / 100)
    below = at_or_above = None
    for _ in range(tries):
        split = rng.multinomial(total, [1 / 3] * 3)
        c, m = counts_with_total_difference(rng, dict(zip(SEEDS, (int(s) for s in split))))
        assert rational_lambda(c, m) == Fraction(bar_pp)
        value = gate.estimate(table_from_counts(c, m), "pilot").est
        if value < bar_pp and below is None:
            below = (c, m, value)
        elif value >= bar_pp and at_or_above is None:
            at_or_above = (c, m, value)
        if below and at_or_above:
            return below, at_or_above
    raise AssertionError("no edge case found")


@pytest.mark.parametrize("bar,words_at,word_below_step", [(10.0, ("go", "stop"), "raise"), (5.0, ("raise",), "stop")])
def test_the_edges_at_exact_three_seed_means(bar, words_at, word_below_step):
    """An exact three-seed mean of 10 (or 5) pp reads as at least 10 (5) whether its float lands at the bar or a
    little below it; one answer fewer (1/18 pp below) reads as below it."""
    rng = np.random.default_rng(int(bar))
    (c1, m1, v1), (c2, m2, v2) = _edge_cases(rng, bar)
    assert v1 < bar and v2 >= bar and bar - v1 < 1e-9
    for c, m in ((c1, m1), (c2, m2)):
        r = gate.read(table_from_counts(c, m), "pilot")
        assert r["reads"][f"estimate_at_least_{int(bar)}_pp"] is True
        assert r["label"] in words_at                         # at 10: go or stop by the lower bound, never raise
        if bar == 10.0:
            assert r["label"] == ("go" if r["lower_bound_pp"] > 5.0 else "stop")
    c3 = {j: np.array(c2[j]) for j in SEEDS}
    where = int(np.flatnonzero(c3[1101] > m2[1101])[0])
    c3[1101][where] -= 1
    assert rational_lambda(c3, m2) == Fraction(bar) - Fraction(1, 18)
    r = gate.read(table_from_counts(c3, m2), "pilot")
    assert abs(r["estimate"]["est"] - (bar - STEP_PP)) < 1e-9
    assert r["reads"][f"estimate_at_least_{int(bar)}_pp"] is False
    assert r["label"] == word_below_step


# ----- Lambda >= 10 with a lower bound <= 5: section 40 point 2's constructed case ------------------------------------


def constructed_case() -> dict:
    """Identical rows over the seeds but for one answer each on seeds 1102 and 1103: a tiny seed part (SE 0.10 pp,
    2 df) and a large item part (SE about 5.10 pp): Lambda 11.33 pp, the frozen form's lower bound about 4.78 pp
    (stop), the seed part alone about 11.15 pp (it would go)."""
    m = np.ones(P, dtype=int)                                         # 1/3 everywhere, but for the moved prompts
    delta = np.zeros(P, dtype=int)
    m[:64], delta[:64] = 0, 3                                         # 64 prompts: 0 -> 3 (+1)
    m[64:106], delta[64:106] = 3, -3                                  # 42 prompts: 3 -> 0 (-1)
    delta[106:108] = 1                                                # 2 prompts: 1 -> 2 (+1/3)
    c = {j: m + delta for j in SEEDS}
    c[1102] = c[1102].copy()
    c[1102][150] += 1                                                 # one answer more on seed 1102
    c[1103] = c[1103].copy()
    c[1103][151] -= 1                                                 # one answer fewer on seed 1103
    return table_from_counts(c, {j: m for j in SEEDS})


def test_lambda_at_least_10_with_a_lower_bound_at_most_5_stops():
    r = gate.read(constructed_case(), "pilot")
    e = r["estimate"]
    assert abs(e["est"] - 68 / 6) < 1e-9                              # 11.33 pp
    assert abs(e["se"] - 5.10) < 0.05 and abs(e["df"] - 198.5) < 1.0
    assert abs(r["lower_bound_pp"] - 4.78) < 0.1 and r["lower_bound_pp"] <= 5.0
    assert r["reads"]["estimate_at_least_10_pp"] is True and r["reads"]["lower_bound_above_5_pp"] is False
    assert r["label"] == "stop"
    assert gate.label(r["reads"], "re-pilot") == "stop"


def test_the_seed_part_alone_would_say_go_on_that_table():
    """READY's fallback (not adopted): the seed part only. It drops REV4:675's prompt part and turns the stop into
    a go on the constructed table."""
    est = gate.estimate(constructed_case(), "pilot")
    seed_only = con.seed_only(est)
    assert seed_only.df == 2.0 and abs(seed_only.se - 0.10) < 0.01
    lower = seed_only.est - tdist.t_quantile(0.90, 2.0) * seed_only.se
    assert abs(lower - 11.15) < 0.05
    assert gate.label(gate.reads(seed_only.est, lower, tie_tolerance()), "pilot") == "go"
    # the frozen form never takes that route: read() uses the item part
    assert gate.read(constructed_case(), "pilot")["estimate"]["with_item"] is True


# ----- an independent recomputation of the paired form ---------------------------------------------------------------


def paired_form_from_scratch(c: dict, m: dict) -> dict:
    """The paired form written again, in plain Python on the pp scale (no numpy, no B16 helper): the paired mean,
    the seed part (ddof 1, J - 1 df), the two-way mean squares of the J x P difference table, V_item and q,
    Satterthwaite df, SE; the lower bound takes B16's t quantile (the one piece reused)."""
    J = len(SEEDS)
    d = [[100.0 * (c[j][p] - m[j][p]) / 3.0 for p in range(P)] for j in SEEDS]
    cell = [math.fsum(row) / P for row in d]
    est = math.fsum(cell) / J
    s2 = math.fsum((v - est) ** 2 for v in cell) / (J - 1)
    v_seed, df_seed = s2 / J, J - 1
    grand = math.fsum(math.fsum(row) for row in d) / (J * P)
    col = [math.fsum(d[j][p] for j in range(J)) / J for p in range(P)]
    ms_p = J * math.fsum((x - grand) ** 2 for x in col) / (P - 1)
    resid = [[d[j][p] - cell[j] - col[p] + grand for p in range(P)] for j in range(J)]
    ms_e = math.fsum(x * x for row in resid for x in row) / ((P - 1) * (J - 1))
    k = 1.0 / (P * J)
    v_item = max(0.0, ms_p - ms_e) * k
    q = ((ms_p * k) ** 2 / (P - 1) + (ms_e * k) ** 2 / ((P - 1) * (J - 1))) if ms_p > ms_e else 0.0
    v = v_seed + v_item
    df = v * v / (v_seed * v_seed / df_seed + q)
    se = math.sqrt(v)
    return {"est": est, "se": se, "df": df, "lower": est - tdist.t_quantile(0.90, df) * se, "v_item": v_item}


def test_independent_recomputation_on_random_tables():
    rng = np.random.default_rng(11)
    with_item = 0
    for n in range(24):
        kind = n % 3
        if kind == 0:                                                 # independent noise per seed
            m = {j: rng.binomial(3, 0.5, P) for j in SEEDS}
            c = {j: np.clip(m[j] + rng.integers(-1, 2, P), 0, 3) for j in SEEDS}
        elif kind == 1:                                               # a prompt effect shared by the seeds
            base = rng.binomial(3, 0.4, P)
            shift = rng.integers(-1, 2, P)
            m = {j: np.clip(base + rng.integers(-1, 2, P), 0, 3) for j in SEEDS}
            c = {j: np.clip(m[j] + shift + rng.integers(0, 2, P), 0, 3) for j in SEEDS}
        else:                                                         # exact totals
            c, m = counts_with_total_difference(rng, {1101: int(rng.integers(0, 120)), 1102: int(rng.integers(0, 120)),
                                                      1103: int(rng.integers(0, 120))})
        r = gate.read(table_from_counts(c, m), "pilot")
        want = paired_form_from_scratch(c, m)
        e = r["estimate"]
        assert abs(e["est"] - want["est"]) < 1e-9 and abs(e["se"] - want["se"]) < 1e-9
        assert abs(e["df"] - want["df"]) < 1e-6 * max(1.0, want["df"])
        assert abs(r["lower_bound_pp"] - want["lower"]) < 1e-9
        with_item += want["v_item"] > 0
        tol = tie_tolerance()
        assert r["label"] == gate.label(gate.reads(want["est"], want["lower"], tol), "pilot")
    assert with_item >= 6                                             # the item part was exercised


# ----- B16's pins and the rule text ------------------------------------------------------------------------------------------


def test_b16_pins_equal_this_trees_b16():
    assert gate.check_b16() == module_hashes() == gate.B16_PINS
    assert set(gate.B16_PINS) == {"__init__.py", "__main__.py", "contrast.py", "labels.py", "overlap.py", "phi.py",
                                  "reading.py", "references.py", "reml.py", "schema.py", "sensitivities.py",
                                  "settings.py", "tdist.py", "settings/reading.json"}


def test_b16_pins_equal_the_stamped_manifest():
    if TREE is None:
        pytest.skip("the builder's synthetic kit is not importable")
    manifest = TREE / ".ai/inputs/stage1-post-w1-20261023/reading/timestamp/ots-manifest-reading-20261101.json"
    if not manifest.is_file():
        pytest.skip("the stamped manifest is not in this tree")
    files = json.loads(manifest.read_text())["files"]
    for name, digest in gate.B16_PINS.items():
        assert files[f"scripts/stage1_s1/reading/{name}"] == digest, name


def test_a_changed_b16_pin_refuses(monkeypatch):
    monkeypatch.setitem(gate.B16_PINS, "contrast.py", "0" * 64)
    with pytest.raises(Refusal, match="B16's files differ from the hashes the stage-1 reading used"):
        gate.check_b16()


def test_the_rule_quotes_rev4_675():
    if TREE is None:
        pytest.skip("the builder's synthetic kit is not importable")
    rev4 = TREE / "research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md"
    if not rev4.is_file():
        pytest.skip("the pre-registration is not in this tree")
    assert gate.REV4_675 in rev4.read_text()
    assert gate.RULE[0] == "REV4:675: " + gate.REV4_675 and "REV4:675" in gate.SOURCES
    assert "section 40 point 1" in gate.RULE[1] and "section 40 point 2" in gate.RULE[2]
    assert (gate.GO_ESTIMATE_AT_LEAST_PP, gate.GO_LOWER_BOUND_ABOVE_PP, gate.RAISE_ESTIMATE_AT_LEAST_PP,
            gate.LEVEL_ONE_SIDED) == (10.0, 5.0, 5.0, 0.90)
    assert gate.ARM_OF == {"pilot": "a0_plant", "re-pilot": "a0_plant75"} and gate.COMPARATOR == "a0"


def test_json_ready():
    out = gate.json_ready({"a": np.float64(1.5), "b": np.int64(2), "c": np.bool_(True), "d": float("inf"),
                           "e": [np.float32(0.5)], "f": -float("inf"), "g": "s"})
    assert out == {"a": 1.5, "b": 2, "c": True, "d": "inf", "e": [0.5], "f": "-inf", "g": "s"}
    assert type(out["a"]) is float and type(out["b"]) is int and type(out["c"]) is bool
    with pytest.raises(Refusal):
        gate.json_ready({"n": float("nan")})
