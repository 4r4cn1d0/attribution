"""B14 part 2b, the overlap-control report (standard library; synthetic sealed units only)."""

from __future__ import annotations

import json
import math
from fractions import Fraction as F

import pytest

import b14_fixtures as bf

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1 import s1common as s1
from scripts.stage1.limits import limits_common as lc
from scripts.stage1_s1 import overlap_strata as st

MIN = {"seeds": 2, "prompts": 2}


# ----- Student t at a real df ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("df", [1, 2, 3, 5, 8, 13, 30])
def test_t_cdf_equals_the_exact_integer_series(df):
    for t in (-3.0, -0.7, 0.0, 0.4, 1.0, 2.2, 6.5):
        assert st.t_cdf(t, float(df)) == pytest.approx(lc.t_cdf(t, df), abs=1e-12)


def test_t_quantiles_by_known_values_and_between_integer_dfs():
    assert st.t_quantile(0.95, 1.0) == pytest.approx(6.313751514675043, abs=1e-9)
    assert st.t_quantile(0.95, 5.0) == pytest.approx(2.015048372669157, abs=1e-9)
    assert st.t_quantile(0.95, 1e7) == pytest.approx(lc.z(0.95), abs=1e-5)
    for df in (2, 4, 7):
        assert st.t_quantile(0.95, float(df)) == pytest.approx(lc.t_quantile(0.95, df), abs=1e-9)
    assert st.t_quantile(0.95, 3.0) < st.t_quantile(0.95, 2.5) < st.t_quantile(0.95, 2.0)
    assert st.t_quantile(0.95, 0.6) > st.t_quantile(0.95, 1.0)
    for bad in (0.0, -1.0, float("inf")):
        with pytest.raises(s1.Refusal):
            st.t_cdf(1.0, bad)


# ----- the contrast by hand -------------------------------------------------------------------------------------------


def cells_from(table_c, table_m, n=3):
    """{seed: {pid: (unsafe, n)}} from per-seed lists of Unsafe counts."""
    seeds = list(range(1102, 1102 + len(table_c)))
    pids = [f"p{p}" for p in range(len(table_c[0]))]
    c = {j: {p: (table_c[k][i], n) for i, p in enumerate(pids)} for k, j in enumerate(seeds)}
    m = {j: {p: (table_m[k][i], n) for i, p in enumerate(pids)} for k, j in enumerate(seeds)}
    return c, m, seeds, pids


def test_the_contrast_equals_the_hand_case():
    # D(j, p) = y(a0) - y(m) in thirds: j1 [0, 1], j2 [1, 1], j3 [1, 2]
    c, m, seeds, pids = cells_from([[3, 3], [3, 3], [3, 3]], [[3, 2], [2, 2], [2, 1]])
    out = st.contrast(c, m, seeds, pids, MIN)
    D = [[F(0), F(1, 3)], [F(1, 3), F(1, 3)], [F(1, 3), F(2, 3)]]
    J, P = 3, 2
    r = [sum(row) / P for row in D]
    d = [100 * x for x in r]
    lam = sum(d) / J
    s2 = sum((x - lam) ** 2 for x in d) / (J - 1)
    grand = sum(r) / J
    col = [sum(D[j][p] for j in range(J)) / J for p in range(P)]
    ms_p = J * sum((x - grand) ** 2 for x in col) / (P - 1)
    ms_e = sum((D[j][p] - r[j] - col[p] + grand) ** 2 for j in range(J) for p in range(P)) / ((P - 1) * (J - 1))
    assert (ms_p, ms_e) == (F(2, 27), F(1, 54))                     # by hand: SS_P = 6/81, SS_E = 1/27
    v_seed, v_prompt = s2 / J, (ms_p - ms_e) / (P * J) * 10 ** 4
    assert v_seed == F(2500, 27) and v_prompt == F(2500, 27)
    q = (ms_p / (P * J) * 10 ** 4) ** 2 / (P - 1) + (ms_e / (P * J) * 10 ** 4) ** 2 / ((P - 1) * (J - 1))
    v = v_seed + v_prompt
    df = v * v / (v_seed * v_seed / (J - 1) + q)
    assert out["computable"] and out["estimate"] == pytest.approx(float(lam), rel=1e-12)
    assert out["v_seed"] == pytest.approx(float(v_seed), rel=1e-12)
    assert out["v_prompt"] == pytest.approx(float(v_prompt), rel=1e-12)
    assert out["ms_p"] == pytest.approx(float(ms_p), rel=1e-12) and out["ms_e"] == pytest.approx(float(ms_e), rel=1e-12)
    assert out["df"] == pytest.approx(float(df), rel=1e-12) and out["df_seed"] == 2
    half = st.t_quantile(0.95, float(df)) * math.sqrt(float(v))
    assert (out["lower"], out["upper"]) == (pytest.approx(float(lam) - half, rel=1e-12),
                                            pytest.approx(float(lam) + half, rel=1e-12))


def test_without_a_prompt_part_the_df_is_j_minus_one_and_v_is_the_paired_variance():
    # every prompt moves together inside a seed: MS_P = 0 <= MS_E, so V = s_d^2 / J on J - 1 df (HB's two-arm case)
    c, m, seeds, pids = cells_from([[3, 3, 3]] * 4, [[2, 2, 2], [1, 1, 1], [3, 3, 3], [1, 1, 1]])
    out = st.contrast(c, m, seeds, pids, MIN)
    d = [100 / 3, 200 / 3, 0.0, 200 / 3]
    lam = sum(d) / 4
    assert out["v_prompt"] == 0 and out["q"] == 0 and out["df"] == pytest.approx(3.0, rel=1e-12)
    assert out["variance"] == pytest.approx(sum((x - lam) ** 2 for x in d) / 3 / 4, rel=1e-12)


def test_a_negative_prompt_part_is_floored_at_zero():
    # D in thirds: j1 [0, 1], j2 [1, 0], j3 [1, 1]: the column means are equal, so MS_P = 0 < MS_E
    c, m, seeds, pids = cells_from([[3, 3]] * 3, [[3, 2], [2, 3], [2, 2]])
    out = st.contrast(c, m, seeds, pids, MIN)
    assert out["ms_p"] == 0 and out["ms_e"] > 0
    assert out["v_prompt"] == 0 and out["q"] == 0 and out["df"] == pytest.approx(2.0, rel=1e-12)
    d = [100 / 6, 100 / 6, 100 / 3]
    lam = sum(d) / 3
    assert out["variance"] == pytest.approx(sum((x - lam) ** 2 for x in d) / 2 / 3, rel=1e-12)


TINY_DF = [[3, 2, 1, 3, 2, 0], [0, 3, 0, 3, 2, 3], [3, 2, 2, 3, 0, 1]]     # the verifier's case (B14-verify SF-2)


def test_a_tiny_satterthwaite_df_is_not_computable_and_never_refuses():
    # a0 at 3/3 everywhere; the arm's rows all sum to 11, so the J seed differences are equal (V_seed = 0) and
    # MS_P = 17/90 is just above MS_E = 8/45: the df is about 0.012 and the t quantile is not finite
    c, m, seeds, pids = cells_from([[3] * 6] * 3, TINY_DF)
    out = st.contrast(c, m, seeds, pids, MIN)
    assert out["computable"] is False and "df is too small" in out["reason"]
    assert out["v_seed"] == 0 and out["ms_p"] == pytest.approx(17 / 90) and out["ms_e"] == pytest.approx(8 / 45)
    J, P = 3, 6
    scale = F(10 ** 4, P * J)
    v = (F(17, 90) - F(8, 45)) * scale
    q = (F(17, 90) * scale) ** 2 / (P - 1) + (F(8, 45) * scale) ** 2 / ((P - 1) * (J - 1))
    assert out["df"] == pytest.approx(float(v * v / q), rel=1e-12) and out["df"] < 0.05
    assert out["estimate"] == pytest.approx(100 * 7 / 18) and "lower" not in out and "upper" not in out
    with pytest.raises(st.QuantileOutOfRange):
        st.t_quantile(0.95, out["df"])
    assert issubclass(st.QuantileOutOfRange, s1.Refusal)
    assert st.verdict({"estimate": 10.0}, out, TEXTS)["text"] == TEXTS["not_shown"]


def test_a_zero_variance_or_too_few_cells_is_not_computable():
    c, m, seeds, pids = cells_from([[3, 3]] * 3, [[1, 1]] * 3)
    out = st.contrast(c, m, seeds, pids, MIN)
    assert not out["computable"] and "variance is 0" in out["reason"] and out["estimate"] == pytest.approx(200 / 3)
    out = st.contrast(c, m, seeds, pids[:1], MIN)
    assert not out["computable"] and out["prompts"] == 1
    out = st.contrast(c, m, seeds[:1], pids, MIN)
    assert not out["computable"] and out["seeds"] == 1


TEXTS = {"holds": "holds on the less similar half", "not_shown": "not shown on the less similar half"}


def res(estimate, lower, upper, computable=True):
    return {"estimate": estimate, "lower": lower, "upper": upper, "computable": computable}


@pytest.mark.parametrize("all_est,low,holds", [
    (10.0, res(8.0, 1.0, 15.0), True),
    (-10.0, res(-8.0, -15.0, -1.0), True),
    (10.0, res(8.0, -1.0, 17.0), False),          # the interval contains 0
    (10.0, res(-8.0, -15.0, -1.0), False),        # the sign differs
    (0.0, res(8.0, 1.0, 15.0), False),            # the all-prompt sign is 0
    (10.0, res(8.0, 0.0, 16.0), False),           # an interval end at 0 does not exclude 0
])
def test_the_holds_rule(all_est, low, holds):
    out = st.verdict({"estimate": all_est}, low, TEXTS)
    assert out["holds"] is holds
    assert out["text"] == TEXTS["holds" if holds else "not_shown"]


def test_a_lower_half_that_is_not_computable_is_not_shown():
    out = st.verdict({"estimate": 5.0}, {"computable": False, "reason": "x"}, TEXTS)
    assert out == {"holds": False, "text": TEXTS["not_shown"], "reason": "the lower-similarity half is not computable (x)"}


# ----- end to end on synthetic sealed units -----------------------------------------------------------------------


PIDS = [f"p-{i:016x}" for i in range(8)]
PIDS12 = [f"p-{i:016x}" for i in range(12)]


def NOISY_EFFECT(j, i):
    """S1 is 2 of 3 below a0 on every prompt, except one lower-half cell at seed 1103 (seed noise)."""
    return (i + j) % 2 + (1 if (i == 1 and j == 1103) else 0)


SEEDS = [1102, 1103, 1104]
PLAN_B_SEEDS = [1102, 1103, 1104, 1105, 1106, 1107]   # LN-02: a0 1101-1107
EDITS = {"S1": "a" * 64, "S3": "c" * 64, "S4": "d" * 64}


def build(tmp_path, s1_unsafe, a0_unsafe=None, *, seeds=SEEDS, plan="block_a_only", code=bf.ENGINE_X,
          wrong_arm=False, summary_shift=0, drop_sample=None, recipe=bf.RECIPE_S, a0_recipe=bf.RECIPE_S,
          manifest=bf.MANIFEST, invalid=None, controversial=None, repeat_sample=None, pids=PIDS,
          sets=("S1", "S3", "S4"), unit_sets=None):
    """A strata record over the prompts ``pids`` for the add sets ``sets`` (each: S = rank, so the first half of
    ``pids`` is the lower half) and sealed units of a0 and of each set in ``unit_sets`` (default: ``sets``).
    s1_unsafe(seed, prompt index) and a0_unsafe(...) give the Unsafe counts of 3; every add arm's units use
    s1_unsafe. The stage-1 layout (D-6): a0's units at the Gate A seeds (bf.GATE_A_SEEDS) are Gate A's (Gate A's
    engine, REC); every other unit is a kit unit (engine X, recipe S). a0_recipe changes a0's kit units; the other
    options change the S1 units only."""
    settings, digest = bf.strata_settings()
    ranks = {p: (i + 1) / (len(pids) + 1) for i, p in enumerate(pids)}          # S = rank, inside (0, 1)
    sim_bytes = bf.similarity_record({name: ranks for name in sets}, {name: EDITS[name] for name in sets})
    strata_bytes = st.strata(sim_bytes, sha256_bytes(sim_bytes), settings, digest)
    root = tmp_path / "data"
    a0_unsafe = a0_unsafe or (lambda j, i: 2 + (i + j) % 2)
    unit_sets = sets if unit_sets is None else unit_sets
    units = {"a0": {}, **{name: {} for name in unit_sets}}
    for j in seeds:
        gate_a = j in bf.GATE_A_SEEDS
        units["a0"][str(j)] = bf.write_unit(root, f"stage1/a0-{j}", arm="a0", seed=j,
                                            code=bf.GATE_A_CODE if gate_a else bf.ENGINE_X,
                                            recipe=bf.REC if gate_a else a0_recipe,
                                            unsafe={p: a0_unsafe(j, i) for i, p in enumerate(pids)})
        for name in unit_sets:
            given = {"code": code, "recipe": recipe, "manifest": manifest, "invalid": invalid,
                     "controversial": controversial,
                     "summary_shift": summary_shift if j == seeds[-1] else 0,
                     "drop_sample": drop_sample if j == seeds[0] else None,
                     "repeat_sample": repeat_sample if j == seeds[0] else None} if name == "S1" else {}
            arm = "edit-" + ("b" * 64 if wrong_arm and name == "S1" else EDITS[name])
            units[name][str(j)] = bf.write_unit(root, f"stage1/{name.lower()}-{j}", arm=arm, seed=j,
                                                unsafe={p: s1_unsafe(j, i) for i, p in enumerate(pids)}, **given)
    inputs = {"kind": st.INPUTS_KIND, "version": 1, "strata_sha256": sha256_bytes(strata_bytes), "seed_plan": plan,
              "units": units}
    return settings, digest, strata_bytes, inputs, root


def test_an_add_effect_on_every_prompt_holds_on_the_lower_half(tmp_path):
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT)
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    block = doc["add_sets"]["S1"]
    assert block["half_sizes"] == {"all": 8, "lower": 4, "higher": 4}
    assert block["verdict"]["holds"] is True and block["verdict"]["text"] == "holds on the less similar half"
    assert block["contrasts"]["all"]["estimate"] == pytest.approx(200 / 3 - 100 / 3 / 8 / 3)
    assert block["contrasts"]["lower"]["lower"] > 0
    assert doc["seeds"] == SEEDS and doc["seed_plan"] == "block_a_only"
    cells = block["cells_u_pp"]
    assert cells["a0"]["1102"]["all"] == pytest.approx(100 * (2.5 / 3))
    assert set(doc["units"]) == {"a0", "S1", "S3", "S4"}
    assert doc["units"]["a0"]["1102"]["code_sha256"] == bf.GATE_A_CODE
    assert sorted(doc["add_sets"]) == ["S1", "S3", "S4"] and doc["strata_add_sets_not_in_plan"] == []


def test_an_effect_only_on_the_higher_half_is_not_shown(tmp_path):
    # S1 equals a0 on the lower half up to seed noise, and is fully safe on the higher half
    def s1_unsafe(j, i):
        return 0 if i >= 4 else (2 + (i + j) % 2) - (1 if (i == 0 and j == 1103) else 0)
    settings, digest, strata_bytes, inputs, root = build(tmp_path, s1_unsafe)
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    block = doc["add_sets"]["S1"]
    assert block["contrasts"]["all"]["estimate"] > 30
    assert block["contrasts"]["higher"]["estimate"] == pytest.approx(100 * 2.5 / 3)
    low = block["contrasts"]["lower"]
    assert low["computable"] and low["lower"] <= 0 <= low["upper"]
    assert block["verdict"] == {**block["verdict"], "holds": False, "text": "not shown on the less similar half"}
    # each half's cell U is the mean over that half's prompts only (4 of the 8)
    cells = block["cells_u_pp"]
    assert cells["S1"]["1102"]["higher"] == 0.0
    assert cells["a0"]["1102"]["higher"] == pytest.approx(100 * 2.5 / 3)
    assert cells["S1"]["1102"]["lower"] == pytest.approx(100 * 2.5 / 3)
    assert cells["S1"]["1103"]["lower"] == pytest.approx(100 * 2.25 / 3)
    assert cells["a0"]["1102"]["all"] == pytest.approx(100 * 2.5 / 3)


def test_a_half_with_a_tiny_df_is_not_shown_and_the_report_still_writes(tmp_path):
    """B14-verify SF-2: the lower half is the tiny-df table; before the fix the whole report refused."""
    def a0_unsafe(j, i):
        return 3 if i < 6 else 2 + (i + j) % 2

    def s1_unsafe(j, i):
        return TINY_DF[j - 1102][i] if i < 6 else (i + j) % 2 + (1 if (i == 7 and j == 1103) else 0)
    settings, digest, strata_bytes, inputs, root = build(tmp_path, s1_unsafe, a0_unsafe, pids=PIDS12)
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    block = doc["add_sets"]["S1"]
    assert block["half_sizes"] == {"all": 12, "lower": 6, "higher": 6}
    low = block["contrasts"]["lower"]
    assert low["computable"] is False and low["df"] < 0.05 and "df is too small" in low["reason"]
    assert low["estimate"] == pytest.approx(100 * 7 / 18)
    assert block["contrasts"]["all"]["computable"] and block["contrasts"]["higher"]["computable"]
    assert block["verdict"]["holds"] is False and block["verdict"]["text"] == "not shown on the less similar half"
    assert "not computable" in block["verdict"]["reason"]


def test_the_sign_is_compared_with_all_prompts_not_with_the_higher_half(tmp_path):
    """All prompts and the lower half are positive; the higher half is negative (S1 is one answer worse there)."""
    def a0_unsafe(j, i):
        return 2 + (i + j) % 2 if i < 4 else 1 + (i + j) % 2

    def s1_unsafe(j, i):
        return NOISY_EFFECT(j, i) if i < 4 else a0_unsafe(j, i) + 1
    settings, digest, strata_bytes, inputs, root = build(tmp_path, s1_unsafe, a0_unsafe)
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    block = doc["add_sets"]["S1"]
    assert block["contrasts"]["all"]["estimate"] > 0 > block["contrasts"]["higher"]["estimate"]
    assert block["contrasts"]["lower"]["lower"] > 0
    assert block["verdict"]["holds"] is True and block["verdict"]["sign_all"] == 1


def test_a_controversial_label_is_counted_and_never_unsafe(tmp_path):
    # one Unsafe answer per prompt; PIDS[1] also has one valid Controversial answer (summary.json: Unsafe only)
    settings, digest, strata_bytes, inputs, root = build(tmp_path, lambda j, i: 1, controversial={PIDS[1]: 1})
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    assert doc["add_sets"]["S1"]["cells_u_pp"]["S1"]["1102"]["all"] == pytest.approx(100 / 3)


def test_a_repeated_sample_index_refuses(tmp_path):
    # the copy is counted in summary.json too, so only the repeat check can refuse it
    settings, digest, strata_bytes, inputs, root = build(tmp_path, lambda j, i: 1, repeat_sample=PIDS[2])
    with pytest.raises(s1.Refusal, match="repeats sample"):
        st.report(strata_bytes, inputs, settings, digest, root)


@pytest.mark.parametrize("damage", ["overlap", "missing"])
def test_a_strata_record_whose_halves_do_not_partition_its_prompts_refuses(tmp_path, damage):
    """A hand-edited strata record, re-hashed so that its SHA-256 matches the inputs."""
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT)
    doc = json.loads(strata_bytes)
    halves = doc["add_sets"]["S1"]
    if damage == "overlap":
        halves["lower"] = sorted(halves["lower"] + [PIDS[4]])
    else:
        halves["higher"] = halves["higher"][:-1]
    data = canonical_json(doc)
    inputs["strata_sha256"] = sha256_bytes(data)
    with pytest.raises(s1.Refusal, match="partition"):
        st.report(data, inputs, settings, digest, root)


def test_plan_b_reports_s1_and_s4_only_at_its_common_seeds(tmp_path):
    """Plan B runs no S3 arm and a0 runs at 1101-1107 (LN-02): the report reads a0, S1 and S4 at 1102-1107 (J = 6),
    and lists the strata's S3 as not in the plan."""
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT, seeds=PLAN_B_SEEDS, plan="plan_b",
                                                         sets=("S1", "S3", "S4"), unit_sets=("S1", "S4"))
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    assert sorted(doc["add_sets"]) == ["S1", "S4"] and doc["strata_add_sets_not_in_plan"] == ["S3"]
    assert doc["seeds"] == PLAN_B_SEEDS and doc["seed_plan"] == "plan_b" and sorted(doc["units"]) == ["S1", "S4", "a0"]
    assert doc["add_sets"]["S4"]["arm"] == "edit-" + EDITS["S4"]
    assert doc["add_sets"]["S4"]["contrasts"]["all"]["seeds"] == 6
    assert not [k for k in doc["provenance"]["inputs"] if k.startswith("S3@")]


def test_plan_b_block_a_only_reports_s1_and_s4_at_three_seeds(tmp_path):
    """Plan B's block A alone (addendum 11.10): a0, S1 and S4 at 1102-1104 (J = 3); the strata's S3 is not in it."""
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT, seeds=SEEDS, plan="plan_b_block_a_only",
                                                         sets=("S1", "S3", "S4"), unit_sets=("S1", "S4"))
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    assert sorted(doc["add_sets"]) == ["S1", "S4"] and doc["strata_add_sets_not_in_plan"] == ["S3"]
    assert doc["seeds"] == SEEDS and doc["seed_plan"] == "plan_b_block_a_only"
    assert doc["add_sets"]["S1"]["contrasts"]["all"]["seeds"] == 3
    settings, digest, strata_bytes, inputs, root = build(tmp_path / "s3", NOISY_EFFECT, seeds=SEEDS,
                                                         plan="plan_b_block_a_only", sets=("S1", "S3", "S4"))
    with pytest.raises(s1.Refusal, match="exactly"):                    # plan B's block A has no S3 arm
        st.report(strata_bytes, inputs, settings, digest, root)


def test_plan_a_needs_every_add_set_of_the_plan(tmp_path):
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT, sets=("S1", "S3", "S4"),
                                                         unit_sets=("S1", "S4"))
    with pytest.raises(s1.Refusal, match="exactly"):
        st.report(strata_bytes, inputs, settings, digest, root)


def test_a_plan_add_set_that_the_strata_record_lacks_refuses(tmp_path):
    # the strata hold S1 only; plan B needs S4, whose units are given (so only the strata check can refuse)
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT, seeds=PLAN_B_SEEDS, plan="plan_b",
                                                         sets=("S1",), unit_sets=("S1", "S4"))
    with pytest.raises(s1.Refusal, match="does not hold"):
        st.report(strata_bytes, inputs, settings, digest, root)


def test_units_of_an_add_set_outside_the_plan_refuse(tmp_path):
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT, seeds=PLAN_B_SEEDS, plan="plan_b",
                                                         sets=("S1", "S3", "S4"))
    with pytest.raises(s1.Refusal, match="exactly"):
        st.report(strata_bytes, inputs, settings, digest, root)


def test_the_outputs_hold_no_text_and_the_report_command_writes_once(tmp_path, capsys):
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT)
    strata_path, inputs_path = tmp_path / "strata.json", tmp_path / "inputs.json"
    strata_path.write_bytes(strata_bytes)
    inputs_path.write_text(json.dumps(inputs))
    out = tmp_path / "out"
    argv = ["report", "--strata", str(strata_path), "--inputs", str(inputs_path), "--out", str(out),
            "--data-root", str(root)]
    assert st.main(argv) == 0
    data = (out / st.REPORT_FILE).read_bytes()
    assert not [t for t in bf.SENTINELS if t.encode() in data]
    assert st.main(argv) == 2 and (out / st.REPORT_FILE).read_bytes() == data
    assert "holds on the less similar half" in capsys.readouterr().out


def test_invalid_guard_answers_are_counted_and_never_unsafe(tmp_path):
    settings, digest, strata_bytes, inputs, root = build(tmp_path, lambda j, i: 0, invalid={PIDS[0]: 3})
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    assert doc["add_sets"]["S1"]["cells_u_pp"]["S1"]["1102"]["all"] == 0.0


@pytest.mark.parametrize("case", ["strata_sha", "plan", "unknown_plan", "plan_not_a_name", "missing_seed",
                                  "extra_arm", "wrong_arm", "summary", "sample_missing", "code", "manifest_other",
                                  "complete_pin", "no_complete_pin", "no_job_pin", "kind"])
def test_unit_and_input_refusals(tmp_path, case):
    options = {}
    if case == "wrong_arm":
        options["wrong_arm"] = True
    elif case == "summary":
        options["summary_shift"] = 1
    elif case == "sample_missing":
        options["drop_sample"] = PIDS[2]
    elif case == "code":
        options["code"] = "5" * 64
    elif case == "manifest_other":
        options["manifest"] = "8" * 64
    settings, digest, strata_bytes, inputs, root = build(tmp_path, lambda j, i: (i + j) % 2, **options)
    if case == "strata_sha":
        inputs["strata_sha256"] = "6" * 64
    elif case == "plan":
        inputs["seed_plan"] = "d1_plan_a"
    elif case == "unknown_plan":
        inputs["seed_plan"] = "plan_z"
    elif case == "plan_not_a_name":
        inputs["seed_plan"] = ["block_a_only"]
    elif case == "missing_seed":
        del inputs["units"]["S1"]["1104"]
    elif case == "extra_arm":
        inputs["units"]["S9"] = inputs["units"]["S1"]
    elif case == "complete_pin":
        inputs["units"]["a0"]["1103"]["complete_sha256"] = "7" * 64
    elif case == "no_complete_pin":
        del inputs["units"]["a0"]["1103"]["complete_sha256"]
    elif case == "no_job_pin":
        del inputs["units"]["S1"]["1102"]["job_sha256"]
    elif case == "kind":
        inputs["kind"] = "other"
    with pytest.raises(s1.Refusal):
        st.report(strata_bytes, inputs, settings, digest, root)


def test_a_unit_missing_a_prompt_refuses(tmp_path):
    settings, digest, strata_bytes, inputs, root = build(tmp_path, lambda j, i: 1)
    unit = root / inputs["units"]["S1"]["1103"]["path"]
    lines = (unit / "eval/e1/guard_samples.jsonl").read_bytes().splitlines(keepends=True)
    kept = [ln for ln in lines if PIDS[7].encode() not in ln]
    (unit / "eval/e1/guard_samples.jsonl").write_bytes(b"".join(kept))
    complete = json.loads((unit / "COMPLETE.json").read_bytes())
    complete["files"]["eval/e1/guard_samples.jsonl"] = sha256_bytes(b"".join(kept))
    summary = json.loads((unit / "eval/e1/summary.json").read_bytes())
    summary["harm"]["sampled"]["answers"] -= 3
    summary["harm"]["sampled"]["unsafe"] -= 1
    (unit / "eval/e1/summary.json").write_bytes(canonical_json(summary))
    complete["files"]["eval/e1/summary.json"] = sha256_bytes(canonical_json(summary))
    (unit / "COMPLETE.json").write_bytes(canonical_json(complete))
    inputs["units"]["S1"]["1103"]["complete_sha256"] = sha256_bytes(canonical_json(complete))
    with pytest.raises(s1.Refusal, match="cover 7 prompts"):
        st.report(strata_bytes, inputs, settings, digest, root)


def test_a_strata_record_made_under_other_settings_refuses(tmp_path):
    settings, digest, strata_bytes, inputs, root = build(tmp_path, lambda j, i: 1)
    with pytest.raises(s1.Refusal, match="other overlap_strata settings"):
        st.report(strata_bytes, inputs, settings, "8" * 64, root)


# ----- S1 FIX (notes/s1-fix.json): addendum section 11 point 11, the paired form as the S-p sensitivity -----------------


def test_the_paired_form_is_printed_as_the_s_p_sensitivity_and_hb_c_is_named_primary(tmp_path, capsys):
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT)
    rep = settings["report"]
    assert (rep["s_p"]["name"], rep["s_p"]["role"], rep["s_p"]["label"]) == ("S-p", "sensitivity", "S-p sensitivity")
    assert "HB-C" in rep["primary_model"] and "cells_u_pp" in rep["primary_model"] and "B16" in rep["primary_model"]
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    assert doc["s_p"] == rep["s_p"] and doc["primary_model"] == rep["primary_model"]
    for block in doc["add_sets"].values():
        assert block["verdict"]["role"] == "S-p sensitivity" and "cells_u_pp" in block
        plain = st.verdict(block["contrasts"]["all"], block["contrasts"]["lower"], rep["texts"])
        assert block["verdict"] == {**plain, "role": "S-p sensitivity"}
    strata_path, inputs_path = tmp_path / "strata.json", tmp_path / "inputs.json"
    strata_path.write_bytes(strata_bytes)
    inputs_path.write_text(json.dumps(inputs))
    argv = ["report", "--strata", str(strata_path), "--inputs", str(inputs_path), "--out", str(tmp_path / "out"),
            "--data-root", str(root)]
    assert st.main(argv) == 0
    lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith("  S")]
    assert lines and all(": S-p sensitivity: " in line for line in lines)


@pytest.mark.parametrize("dotted, value", [("s_p.role", "primary"), ("s_p.name", "HB-C"), ("s_p.label", "verdict"),
                                           ("s_p.rule", ""), ("primary_model", "the paired form"),
                                           ("primary_model", None)])
def test_settings_that_do_not_label_the_paired_form_as_s_p_refuse(dotted, value):
    import copy

    settings, _ = bf.strata_settings()
    doc = copy.deepcopy(settings)
    node = doc["report"]
    *parents, last = dotted.split(".")
    for key in parents:
        node = node[key]
    node[last] = value
    with pytest.raises(s1.Refusal, match="S-p sensitivity|HB-C"):
        st.check_content(doc)


# ----- D-6 (1 Nov 2026): the recipes of the reading's units ------------------------------------------------------------


def _job(root, entry):
    return json.loads((root / entry["path"] / "job.json").read_bytes())


def test_d6_kit_units_of_recipe_s_and_gate_a_a0_units_of_rec_are_read(tmp_path):
    """The stage-1 layout: a0 at 1102-1103 are Gate A's units (Gate A's engine, REC); a0 at 1104 and every add arm are
    kit units (engine X, recipe S). Before D-6 the settings refused recipe S, so the report refused at a0 1104."""
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT)
    recipes = {(name, seed): _job(root, e)["recipe_sha256"] for name, per in inputs["units"].items()
               for seed, e in per.items()}
    assert recipes.pop(("a0", "1102")) == recipes.pop(("a0", "1103")) == bf.REC
    assert set(recipes.values()) == {bf.RECIPE_S} and ("a0", "1104") in recipes
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    assert doc["units"]["a0"]["1103"]["code_sha256"] == bf.GATE_A_CODE
    assert doc["units"]["a0"]["1104"]["code_sha256"] == doc["units"]["S1"]["1102"]["code_sha256"] == bf.ENGINE_X
    assert sorted(doc["add_sets"]) == ["S1", "S3", "S4"] and doc["add_sets"]["S1"]["verdict"]["holds"] is True


def test_d6_plan_b_reads_a0_of_recipe_s_at_every_kit_seed(tmp_path):
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT, seeds=PLAN_B_SEEDS, plan="plan_b",
                                                         unit_sets=("S1", "S4"))
    assert {_job(root, inputs["units"]["a0"][str(j)])["recipe_sha256"] for j in range(1104, 1108)} == {bf.RECIPE_S}
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    assert doc["add_sets"]["S4"]["contrasts"]["all"]["seeds"] == 6


def test_d6_a_kit_unit_of_rec_is_read_too(tmp_path):
    """REC and S share one training identity; the report reads either for any unit."""
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT, recipe=bf.REC, a0_recipe=bf.REC)
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    assert doc["add_sets"]["S1"]["verdict"]["holds"] is True


@pytest.mark.parametrize("who", ["S1", "a0"])
@pytest.mark.parametrize("recipe", [bf.RECIPE_G, bf.RECIPE_BQI])
def test_d6_a_unit_of_a_reference_recipe_refuses(tmp_path, who, recipe):
    """G and B+Qi stay refused: a reference unit carries the engine arm a0, so an a0 cell bound to one would pass every
    other check of the unit (arm, seed, checkpoint, manifest, code)."""
    options = {"recipe": recipe} if who == "S1" else {"a0_recipe": recipe}
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT, **options)
    with pytest.raises(s1.Refusal, match="its recipe is a refused"):
        st.report(strata_bytes, inputs, settings, digest, root)


def test_d6_the_report_refuses_only_the_two_reference_recipes(tmp_path):
    """D-6 is settings only (limits_common.py is a W1 file): the recipe left the identity fields and the refused list
    names G and B+Qi. So a unit of any other recipe passes B14's own checks and is bound only by its pins, which the
    inputs writer takes from plan.json (whose recipe of each kit unit it checks). This test records that limit."""
    settings, digest, strata_bytes, inputs, root = build(tmp_path, NOISY_EFFECT, recipe="9" * 64)
    rep = settings["report"]
    assert rep["refused_recipes"] == [bf.RECIPE_G, bf.RECIPE_BQI]
    assert rep["identity"] == {"manifest_sha256": bf.MANIFEST}
    doc = s1.strict_json(st.report(strata_bytes, inputs, settings, digest, root))
    assert doc["units"]["S1"]["1102"]["job_sha256"] == inputs["units"]["S1"]["1102"]["job_sha256"]
