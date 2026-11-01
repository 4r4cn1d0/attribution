"""F_k's planning power at the measured discordance (fk_power.py; REV4:574): the formula against REV4's printed table
and against the statistics review's own script; q by hand; F_k's result copied from B16's output; the reading's J;
the bindings and refusals; the command line (the file and its SHA-256 only, never a number)."""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import re

import numpy as np
import pytest
import synth_kit as sk

from scripts.stage1_s1.reading.settings import Refusal, design
from scripts.stage1_s1.reading_extra import fk_power as fk

REV4_DIR = sk.TREE / "research" / "experiments" / "2026-10-17-stage1-preregistration-rev3"
VALUE = re.compile(r"\d\.\d{3,}")


def run(docs, paths=None):
    return fk.read(docs["tables"], docs["reading"], docs["reading"]["provenance"]["input_sha256"], "r" * 64)


def test_the_formula_reproduces_rev4s_table():
    fk.check_table(5.0)
    for (sd, alpha), row in fk.TABLE.items():
        got = [round(fk.planning(q, sd, alpha, 500, 6, 5.0)["power"], 2) for q in fk.TABLE_Q]
        assert got == list(row), (sd, alpha)


def test_the_table_and_rule_texts_are_rev4s():
    rev4 = REV4_DIR / "stage1-preregistration-rev4.md"
    if not rev4.is_file():
        pytest.skip("the pre-registration is not in this tree")
    text = rev4.read_text()
    assert "| 0 pp; Branch full | 1.00 / 0.97 / 0.80 / 0.65 / 0.55 | 0.99 / 0.80 / 0.43 / 0.26 / 0.18 |" in text
    assert "| 1.15 pp; Branch full | 1.00 / 0.96 / 0.78 / 0.64 / 0.54 | 0.96 / 0.75 / 0.40 / 0.25 / 0.17 |" in text
    assert "the stage-1 reading prints F_k's planning power at the measured q beside each F_k result" in text
    assert "q = the share of prompts on which the arm's refusal flag and θ0's differ" in text
    assert "P = 500, J = 6" in text


def test_the_formula_equals_the_statistics_reviews_script():
    path = REV4_DIR / "stat_review_o_power.py"
    if not path.is_file():
        pytest.skip("the statistics review's script is not in this tree")
    spec = importlib.util.spec_from_file_location("stat_review_o_power_for_test", path)
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)
    for q in (0.01, 0.05, 0.168, 0.3, 0.55):
        for sd in (0.0, 1.15, 2.0):
            for alpha in (0.05, 0.00375):
                for p in (100, 500):
                    want, se, df = review.power_feasible(p, q, 0.0, sd, alpha)
                    got = fk.planning(q, sd, alpha, p, 6, 5.0)
                    assert math.isclose(got["power"], want, abs_tol=1e-6), (q, sd, alpha, p)
                    assert math.isclose(got["se_pp"], se, rel_tol=1e-12) and math.isclose(got["df"], df, rel_tol=1e-12)


def test_the_formula_by_hand_at_another_j():
    q, sd, j, p = 0.25, 1.15, 3, 500
    v_item, v_seed = q / p * 1e4, sd * sd / j
    df = (v_item + v_seed) ** 2 / (v_seed ** 2 / (j - 1) + v_item ** 2 / (p - 1))
    from scripts.stage1_s1.reading.tdist import t_quantile
    z = 5.0 / math.sqrt(v_item + v_seed) - t_quantile(0.95, df)
    got = fk.planning(q, sd, 0.05, p, j, 5.0)
    assert math.isclose(got["power"], 0.5 * math.erfc(-z / math.sqrt(2)), rel_tol=1e-12)
    assert math.isclose(got["df"], df, rel_tol=1e-12)


def test_a_broken_table_refuses(monkeypatch):
    monkeypatch.setitem(fk.TABLE, (0.0, 0.05), (1.00, 0.97, 0.80, 0.66, 0.55))
    with pytest.raises(Refusal, match="does not reproduce REV4's power table"):
        fk.check_table(5.0)


@pytest.mark.parametrize("reading", ["plan_a_block_a_only", "plan_b"])
def test_q_and_the_rows_by_hand(pipeline, reading):
    s, docs, _ = pipeline(reading)
    out = run(docs)
    o = docs["tables"]["endpoints"]["O"]
    theta0 = np.array(o["theta0"])
    dsg = design(reading)
    assert list(out["contrasts"]) == [name for name, _, _ in dsg.contrasts]
    for name, c, m in dsg.contrasts:
        k = out["contrasts"][name]
        seeds = sorted(int(j) for j in o["cells"][m])
        per = {str(j): float(np.mean(np.array(o["cells"][m][str(j)]) != theta0)) for j in seeds}
        assert k["discordance"]["per_seed"] == per and k["o_seeds"] == seeds
        assert math.isclose(k["discordance"]["q"], sum(per.values()) / len(per), rel_tol=1e-12)
        assert k["items"] == 500 and k["seeds"] == len(seeds) == len(dsg.seeds[m])
        assert k["differs_from_planning_p_j"] is (len(seeds) != 6)
        assert [(r["seed_sd_pp"], r["alpha"]) for r in k["planning_power"]] == \
            [(0.0, 0.05), (0.0, 0.00375), (1.15, 0.05), (1.15, 0.00375)]
        for r in k["planning_power"]:
            want = fk.planning(k["discordance"]["q"], r["seed_sd_pp"], r["alpha"], 500, len(seeds), 5.0)
            assert r["power"] == want["power"] and r["df"] == want["df"]
        assert k["planning_power"][0]["power"] > k["planning_power"][1]["power"]   # 5% above 0.375%


def test_f_k_is_copied_from_b16_by_key(pipeline):
    s, docs, _ = pipeline("plan_a_block_a_only")
    out = run(docs)
    r = docs["reading"]
    for name, _, _ in design("plan_a_block_a_only").contrasts:
        f = out["contrasts"][name]["F_k"]
        assert f["F_k_rejects_in_phi"] == r["rows"][name]["feasibility_part"]["F_k_rejects_in_phi"]
        assert f["p_value"] == r["contrasts"][name]["p_values"]["F"]
        assert f["theta0_part"] == r["contrasts"][name]["O"]["theta0_part"]
        assert f["theta0_interval_90"] == r["contrasts"][name]["O"]["theta0_interval_90"]
        assert f["final_level"] == r["phi"]["final_levels"][f"F:{name}"]
        assert f["states"] == r["rows"][name]["feasibility_part"]["states"]
    assert out["label_suffix"] == "block A only (3 seeds per method arm)"
    assert set(out["readings"]) == {"F1", "F2", "F3", "F4", "F5"}


def test_discordance_needs_flags_and_two_seeds():
    theta0 = np.array([0.0, 1.0, 1.0, 0.0])
    table = {("A1", 1102): np.array([1.0, 1.0, 0.0, 0.0]), ("A1", 1103): np.array([0.0, 1.0, 1.0, 0.0])}
    d = fk.discordance(table, theta0, "A1")
    assert d["per_seed"] == {"1102": 0.5, "1103": 0.0} and d["q"] == 0.25
    with pytest.raises(Refusal, match="not a 0/1 refusal flag"):
        fk.discordance({**table, ("A1", 1103): np.array([0.0, 0.5, 1.0, 0.0])}, theta0, "A1")
    with pytest.raises(Refusal, match="fewer than two seeds"):
        fk.discordance({("A1", 1102): table[("A1", 1102)]}, theta0, "A1")


def _edit(fn, which="reading"):
    def apply(docs):
        d = copy.deepcopy(docs)
        fn(d[which])
        return d
    return apply


@pytest.mark.parametrize("edit,match", [
    (_edit(lambda r: r.update(kind="x")), "not B16's version-1 output"),
    (_edit(lambda r: r["provenance"].update(settings_sha256="0" * 64)), "other reading settings"),
    (_edit(lambda r: r["design"]["contrasts"].pop()), "sealed contrasts"),
    (_edit(lambda r: r["rows"]["P2"]["feasibility_part"].pop("F_k_rejects_in_phi")), "no F_k result for P2"),
    (_edit(lambda r: r["contrasts"]["P3"]["O"].pop("theta0_part")), "no F_k result for P3"),
    (_edit(lambda t: t.update(reading="plan_a"), "tables"), "the sealed design has"),   # B16's schema
])
def test_refusals(pipeline, edit, match):
    s, docs, _ = pipeline("plan_a_block_a_only")
    d = edit(docs)
    with pytest.raises(Refusal, match=match):
        run(d)


def test_the_input_must_be_b16s_input(pipeline):
    s, docs, _ = pipeline("plan_a_block_a_only")
    with pytest.raises(Refusal, match="not read from this input document"):
        fk.read(docs["tables"], docs["reading"], "0" * 64, "r" * 64)


def test_command_line_writes_once_and_prints_no_number(pipeline, tmp_path, capsys):
    s, docs, paths = pipeline("plan_a_block_a_only")
    out = tmp_path / "fk.json"
    args = ["--input", str(paths["tables"]), "--reading", str(paths["reading"]), "--out", str(out)]
    assert fk.main(args) == 0
    printed = capsys.readouterr()
    doc = json.loads(out.read_text())
    assert printed.out == f"wrote {out} sha256 {sk.sha(out.read_bytes())}\n" and printed.err == ""
    assert doc["provenance"]["inputs"] == {"reading.json": sk.sha(paths["reading"].read_bytes()),
                                           "tables.json": sk.sha(paths["tables"].read_bytes())}
    assert fk.main(args) == 2 and "fk.json exists" in capsys.readouterr().err
    other = tmp_path / "other.json"
    assert fk.main(["--input", str(paths["reading"]), "--reading", str(paths["reading"]), "--out", str(other)]) == 2
    err = capsys.readouterr().err
    assert not other.exists() and "REFUSED" in err and not VALUE.search(err)
