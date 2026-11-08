"""SR-2's error-rate simulation (Part 2 §10.3; DES K6; DESO3 V2): ``scripts/scale78b/sr2_simulation.py``.

The pieces against their references: the vectorized REML against B16's ``fit_cells`` (pre-registered start and D-4's
multi-start, with the lone cells in B16's call), the contrast's estimate, seed variance, df and p against B16's
``contrast_fit``, the two-arm sum rule, σ̂_A against ``blinded_sigma.pooled_sigma`` and its design, the plan against
the noise reader's ``seed_rule`` (thresholds and the review ceiling), Holm by hand, the plans' designs (P1 §5, B16's
plan_b form, the stopped family's drops), the invariance that lets one null draw serve every power effect. Then the
script: a smoke grid's output is byte-stable on a fixed seed, shards merge into the unsharded bytes, the reading rule
and the approximations are printed from the settings, and the committed settings file holds the grid and the rule.
Smoke grids only (a few hundred replicates); no result is read from them."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

from scripts.scale78b import sr2_simulation as sim  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/scale78b/sr2_simulation.py"
SETTINGS = ROOT / "scripts/scale78b/settings/sr2_simulation.json"
OPTS = {"tol": 1e-6, "max_iter": 25, "clip": 2.0, "ll_tol": 1e-6}


def smoke_settings(tmp_path: Path, **change) -> Path:
    s = json.loads(SETTINGS.read_text())
    s.update({"reps": 60, "chunk": 30, "sigma_pair_pp": ["3.0", "6.0", "8.24"], "seed": 11})
    s.update(change)
    path = tmp_path / f"smoke-{len(list(tmp_path.iterdir()))}.json"
    path.write_text(json.dumps(s, indent=1))
    return path


def b16_cells(cluster: dict, y_row, lone: list) -> list:
    cells = [(a, j, float(v)) for (a, j), v in zip(cluster["cells"], y_row)]
    return cells + lone


# ----- REML and the contrast against B16 ---------------------------------------------------------------------------------


@pytest.mark.parametrize("plan,stopped,name", [("A", False, "removal"), ("A", False, "full"), ("B9", False, "removal"),
                                               ("A", True, "full"), ("H", False, "removal")])
@pytest.mark.parametrize("starts", ["pre-registered", "multi"])
def test_the_vectorized_reml_equals_b16_fit_cells(plan, stopped, name, starts):
    cluster = sim.analysis_design(plan, stopped)["clusters"][name]
    assert not cluster["two_arm"]
    rng = np.random.default_rng(5)
    reps = 12
    scale = np.where(np.array([a in sim.METHODS for a, _ in cluster["cells"]]), 4.0, 2.5)
    y = rng.standard_normal((reps, len(cluster["cells"]))) * scale
    y[0] = np.round(y[0])                                    # one replicate with ties and an arm likely at the floor
    with np.errstate(all="ignore"):
        s2, inv, conv = sim.reml_batch(cluster, y.copy(), 0.01, {**OPTS, "starts": starts})
    lone_arm = "R" if name == "removal" else "a0"
    for r in range(reps):
        lone = [(lone_arm, 1101, 123.0 + r)]                 # B16's reading holds the 1101 cell; it changes nothing
        fit = sim.REML.fit_cells(b16_cells(cluster, y[r], lone), cluster["arms"], 0.01, multi_start=starts == "multi")
        for i, arm in enumerate(cluster["arms"]):
            assert math.isclose(s2[r, i], fit.sigma2[arm], rel_tol=1e-6, abs_tol=1e-9), (r, arm)
        assert conv[r] == fit.converged
        for c in cluster["arms"]:
            for m in cluster["arms"]:
                if c < m:
                    v, df = sim.REML.seed_variance(fit, c, m, 6)
                    i, k = cluster["arms"].index(c), cluster["arms"].index(m)
                    var_v = (inv[r, i, i] + inv[r, k, k] + 2 * inv[r, i, k]) / 36
                    assert math.isclose((s2[r, i] + s2[r, k]) / 6, v, rel_tol=1e-6)
                    assert math.isclose(2 * v * v / var_v, df, rel_tol=1e-5), (r, c, m)


def test_the_claim_tests_estimate_se_df_and_p_equal_b16_contrast_fit():
    from scripts.stage1_s1.reading import contrast as con
    design = sim.analysis_design("A", False)
    rng = np.random.default_rng(9)
    y = rng.standard_normal((6, len(sim.CELLS))) * 3.0
    with np.errstate(all="ignore"):
        res = sim.claim_test(design, y, {"floor_pp2": "0.01", "_reml": {**OPTS, "starts": "multi"}})
    for r in range(6):
        table = {c: np.array([y[r, i]]) for c, i in sim.INDEX.items()}
        fits = {}
        for name, cl in design["clusters"].items():
            cells = [(a, j, float(y[r, sim.INDEX[(a, j)]])) for a, j in cl["cells"]]
            fits[name] = sim.REML.fit_cells(cells, cl["arms"], 0.01, multi_start=True)
        for k, ct in design["contrasts"].items():
            e = con.contrast_fit(table, fits[ct["cluster"]], ct["c"], ct["m"], list(ct["seeds"]), 1.0, with_item=False)
            got = res["contrasts"][k]
            assert math.isclose(got["est"][r], e.est, rel_tol=1e-12, abs_tol=1e-12)
            assert math.isclose(got["se"][r], e.se, rel_tol=1e-6)
            assert math.isclose(got["df"][r], e.df, rel_tol=1e-5)
            assert math.isclose(got["p"][r], e.p_two_sided(), rel_tol=1e-4, abs_tol=1e-9), (r, k)


def test_the_two_arm_sum_rule_equals_b16():
    from scripts.stage1_s1.reading import contrast as con
    design = sim.analysis_design("B9", False)
    cl = design["clusters"]["full"]
    assert cl["two_arm"] and cl["arms"] == ("S1", "S4") and set(design["contrasts"]) == {"P1", "P3", "P6"}
    rng = np.random.default_rng(3)
    y = rng.standard_normal((5, len(sim.CELLS))) * 4.0
    y[1, [sim.INDEX[("S4", j)] for j in range(1102, 1111)]] = y[1, [sim.INDEX[("S1", j)] for j in range(1102, 1111)]] + 0.001
    with np.errstate(all="ignore"):
        res = sim.claim_test(design, y, {"floor_pp2": "0.01", "_reml": {**OPTS, "starts": "multi"}})
    for r in range(5):
        cells = [(a, j, float(y[r, sim.INDEX[(a, j)]])) for a, j in cl["cells"]]
        fit = sim.REML.fit_cells(cells, cl["arms"], 0.01)
        table = {c: np.array([y[r, i]]) for c, i in sim.INDEX.items()}
        e = con.contrast_fit(table, fit, "S1", "S4", list(range(1102, 1111)), 1.0, with_item=False)
        got = res["contrasts"]["P6"]
        assert math.isclose(got["se"][r], e.se, rel_tol=1e-9) and got["df"][r] == e.df == 8
        assert math.isclose(got["p"][r], e.p_two_sided(), rel_tol=1e-9, abs_tol=1e-12)
    assert math.isclose(res["contrasts"]["P6"]["se"][1], math.sqrt(0.01 / 9), rel_tol=1e-9)   # the floor on the sum


# ----- σ̂_A, the plan and Holm -------------------------------------------------------------------------------------------------


def test_sigma_a_is_blinded_sigmas_estimate_on_its_design():
    from scripts.scale78b import blinded_sigma as bs
    for stopped in (False, True):
        design = "anchor_stopped" if stopped else "full"
        ours = {(a, j): c for c, cells in sim.block_a_cells(stopped).items() for a, j in cells}
        assert ours == bs.design_cells(design)
    rng = np.random.default_rng(2)
    z = rng.standard_normal((4, 2, len(sim.CELLS))) * 3
    y_all = {f: z[:, i, :] for i, f in enumerate(sim.FAMILIES)}
    for option, stopped in (("B", set()), ("C", set()), ("B", {"llama31-8b"}), ("C", {"olmo2-7b"})):
        s2, df = sim.sigma_a_sq(y_all, option, stopped)
        for r in range(4):
            clusters = {}
            for f in sim.OPTIONS[option]:
                for c, cells in sim.block_a_cells(f in stopped).items():
                    clusters[f"{f} {c}"] = {cell: Fraction(float(y_all[f][r, sim.INDEX[cell]])) for cell in cells}
            sigma, want_df = bs.pooled_sigma(clusters)
            assert df == want_df and math.isclose(math.sqrt(s2[r]), sigma, rel_tol=1e-9)
    assert sim.sigma_a_sq(y_all, "B", set())[1] == 24 and sim.sigma_a_sq(y_all, "C", {"olmo2-7b"})[1] == 6
    assert sim.sigma_a_sq(y_all, "B", {"llama31-8b"})[1] == 18


def test_the_plan_rule_is_the_noise_readers_and_the_settings_hold_its_constants():
    from scripts.scale78b import noise_reading as nr
    s = json.loads(SETTINGS.read_text())
    assert s["rule"]["threshold_A_pp"] == nr.THRESHOLD_A_PP and s["rule"]["threshold_B9_pp"] == nr.THRESHOLD_B9_PP
    assert s["rule"]["mde_factor"] == nr.MDE_FACTOR and s["sesoi_pp"] == nr.SESOI_PP
    sigmas = [3.0, 4.4999, 4.5, 4.5001, 5.9999, 6.0, 6.0001, 8.24, 10.7, 10.7066, 10.7067, 12.0]
    got = sim.plan_of(np.array(sigmas) ** 2, s)
    for sigma, plan in zip(sigmas, got):
        want = nr.seed_rule(((Fraction(str(sigma)) ** 2,),), 4)
        assert (plan if plan != "review" else "review") == ("review" if want["review"] else want["plan"]), sigma
    assert list(got[[2, 5, 9]]) == ["A", "B9", "H"] and got[10] == "review"


def test_holm_by_hand():
    p = np.array([[0.001, 0.02, 0.04], [0.02, 0.02, 0.02], [0.016, 0.03, 0.9], [0.017, 0.001, 0.2], [0.5, 0.01, 0.024],
                  [0.02, 0.04, 0.045]])                    # the last: no first rejection, so none (step-down stops)
    want = np.array([[True, True, True], [False, False, False], [True, False, False], [True, True, False],
                     [False, True, True], [False, False, False]])
    assert (sim.holm(p, 0.05) == want).all()


def test_arm_means_move_no_fit_so_one_null_draw_serves_every_effect():
    design = sim.analysis_design("A", False)
    rng = np.random.default_rng(4)
    y = rng.standard_normal((5, len(sim.CELLS))) * 3
    shift = np.array([{"A1": 8.0, "S4": -5.0, "R": 2.0}.get(a, 0.0) for a, _ in sim.CELLS])
    seed = np.array([0.5 * (j - 1100) for _, j in sim.CELLS])
    st = {"floor_pp2": "0.01", "_reml": {**OPTS, "starts": "multi"}}
    with np.errstate(all="ignore"):
        a = sim.claim_test(design, y, st)["contrasts"]
        b = sim.claim_test(design, y + shift + seed, st)["contrasts"]
    assert np.allclose(b["P1"]["est"], a["P1"]["est"] + 2.0 - 8.0) and np.allclose(b["P6"]["est"], a["P6"]["est"] + 5.0)
    for k in a:
        assert np.allclose(a[k]["se"], b[k]["se"], rtol=1e-6) and np.allclose(a[k]["df"], b[k]["df"], rtol=1e-5)
    y_all = {f: y for f in sim.FAMILIES}
    shifted = {f: y + shift + seed for f in sim.FAMILIES}
    assert np.allclose(sim.sigma_a_sq(y_all, "B", set())[0], sim.sigma_a_sq(shifted, "B", set())[0])
    eta = np.random.default_rng(6).standard_normal((5, 2, 2, 3, 40))
    assert np.allclose(sim.sigma_pool_sq(sim.n_prompt_values(y_all, eta, 1.28)),
                       sim.sigma_pool_sq(sim.n_prompt_values(shifted, eta, 1.28)))


# ----- the designs ---------------------------------------------------------------------------------------------------------------


def test_the_plans_designs():
    a = sim.analysis_design("A", False)
    assert set(a["contrasts"]) == {"P1", "P2", "P3", "P4", "P5", "P6"}
    assert all(len(c["seeds"]) == 6 for c in a["contrasts"].values())
    assert len(a["clusters"]["removal"]["cells"]) == 24 and len(a["clusters"]["full"]["cells"]) == 24  # 1101 left out
    b9 = sim.analysis_design("B9", False)
    assert set(b9["contrasts"]) == {"P1", "P3", "P6"} and all(len(c["seeds"]) == 9 for c in b9["contrasts"].values())
    assert b9["clusters"]["removal"]["arms"] == ("R", "A1", "H1") and len(b9["clusters"]["removal"]["cells"]) == 27
    h = sim.analysis_design("H", False)
    assert all(len(c["seeds"]) == 12 for c in h["contrasts"].values())
    a_s = sim.analysis_design("A", True)
    assert set(a_s["contrasts"]) == {"P3", "P4", "P6"} and a_s["clusters"]["removal"]["two_arm"]
    assert a_s["clusters"]["full"]["arms"] == ("a0", "S1", "S4")
    h_s = sim.analysis_design("H", True)
    assert set(h_s["contrasts"]) == {"P3", "P6"} and all(c["two_arm"] for c in h_s["clusters"].values())
    blk = sim.block_a_cells(False)
    assert len(blk["removal"]) == 14 and len(blk["full"]) == 13


# ----- the script --------------------------------------------------------------------------------------------------------------


def run_cli(*args):
    return subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def test_the_output_is_byte_stable_and_shards_merge_into_it(tmp_path):
    full = json.loads(SETTINGS.read_text())["interaction"]
    settings = smoke_settings(tmp_path, reps=30, chunk=15,
                              interaction=[i for i in full if i["name"] in ("none", "llama sigma x 1.5")])
    first = run_cli("--settings", settings, "--option", "B", "--design", "full")
    second = run_cli("--settings", settings, "--option", "B", "--design", "full", "--out", tmp_path / "full.json")
    assert first.returncode == 0 and second.returncode == 0, first.stderr + second.stderr
    assert first.stdout == second.stdout == (tmp_path / "full.json").read_text()
    doc = json.loads(first.stdout)
    assert [r["sigma_pair_pp"] for r in doc["rows"]] == ["3.0", "6.0", "8.24"]
    s0 = run_cli("--settings", settings, "--option", "B", "--sigma", "0,2", "--out", tmp_path / "s0.json")
    s1 = run_cli("--settings", settings, "--option", "B", "--sigma", "1", "--out", tmp_path / "s1.json")
    assert s0.returncode == 0 and s1.returncode == 0
    assert "summary" not in json.loads(s0.stdout) and json.loads(s0.stdout)["shard"] == [0, 2]
    merged = run_cli("--merge", tmp_path / "s1.json", tmp_path / "s0.json")
    assert merged.returncode == 0, merged.stderr
    assert merged.stdout == first.stdout
    again = run_cli("--settings", settings, "--option", "B", "--out", tmp_path / "full.json")
    assert again.returncode != 0 and "written once" in again.stderr
    bad = run_cli("--merge", tmp_path / "s0.json")
    assert bad.returncode != 0 and "cover the settings' σ grid" in bad.stderr


def test_the_output_prints_the_rule_the_approximations_and_every_quantity(tmp_path):
    settings = smoke_settings(tmp_path, sigma_pair_pp=["4.0", "6.0"])
    doc = sim.simulate(settings, "C", "full", [])
    s = json.loads(SETTINGS.read_text())
    assert doc["reading_rule"] == s["reading_rule"] and doc["approximations"] == s["approximations"]
    assert doc["families"] == ["olmo2-7b"] and doc["reps"] == 60 and doc["reml_starts"] == "multi"
    sc = doc["rows"][0]["scenarios"]
    names = ["none", "arm x seed 0.5", "arm x seed 1", "llama sigma x 1.5", "llama sigma x 1/1.5"]
    assert set(sc) == set(names)
    assert [sc[n]["method_variance_share"] for n in names] == ["0", "0.5", "1", "0", "0"]
    assert [sc[n]["llama_sigma_ratio"] for n in names] == ["1", "1", "1", "3/2", "2/3"]
    assert sc["llama sigma x 1.5"]["sigma_pair_pp_by_family"] == {"llama31-8b": 6.0, "olmo2-7b": 4.0}
    assert sc["llama sigma x 1/1.5"]["sigma_pair_pp_by_family"] == {"llama31-8b": round(8 / 3, 6), "olmo2-7b": 4.0}
    assert any("U claims" in x and "O and L words" in x and "not simulated" in x for x in doc["limits"])     # R-11
    assert any("one true sigma_pair" in x for x in doc["approximations"])                                    # SV-3
    assert doc["limits"] == s["limits"] and "prompt (item) part" in doc["limits"][0] and doc["n_stage"] == s["n_stage"]
    fam = sc["none"]["families"]["olmo2-7b"]
    assert set(fam["power"]) == {"8", "10", "12"} and set(fam["contrasts"]) == set(sim.CONTRASTS)
    assert set(sc["none"]["plan_by_sigma_A"]) == set(sim.PLAN_LABELS) == set(sc["none"]["plan_by_N"])
    assert math.isclose(sum(sc["none"]["plan_by_sigma_A"].values()), 1.0, abs_tol=1e-5)
    summary = doc["summary"]
    assert summary["threshold_familywise"] == "0.06"
    assert summary["scenarios_read"] == sorted(names)
    assert ("applies to every simulated sigma (2) and every scenario (arm x seed 0.5, arm x seed 1, llama sigma x 1.5, "
            "llama sigma x 1/1.5, none), with or without the interaction and at either family ratio: the familywise rate "
            "is the U claims' rate") in summary["reading_line"]
    fams_all = [v for r in doc["rows"] for x in r["scenarios"].values() for v in x["families"].values()]
    assert summary["refused_contrasts_total"] == sum(v["refused_contrasts"] for v in fams_all)          # SV-7
    assert summary["nonconverged_fits_total"] == sum(v["nonconverged_fits"] for v in fams_all) > 0
    assert "SR-2 is not adopted" in summary["reading_line"]
    top = summary["max_familywise"]
    assert summary["max_above_threshold"] == (top["familywise_count"] / 60 > 0.06)
    assert top["familywise_count"] == max(v["familywise_count"] for r in doc["rows"] for x in r["scenarios"].values()
                                          for v in x["families"].values())
    assert doc["frozen_sha256"] == {k: v[1] for k, v in sim.FROZEN.items()}


def test_the_reduced_design_runs_and_its_flags_are_checked(tmp_path):
    settings = smoke_settings(tmp_path, sigma_pair_pp=["5.0"], interaction=[{"name": "none", "method_variance_share": "0", "llama_sigma_ratio": "1"}])
    doc = sim.simulate(settings, "B", "reduced", ["llama31-8b"])
    fams = doc["rows"][0]["scenarios"]["none"]["families"]
    assert fams["llama31-8b"]["primary_under_plan_A"] == ["P3", "P4", "P6"]
    assert fams["olmo2-7b"]["primary_under_plan_A"] == ["P1", "P2", "P3", "P4", "P5", "P6"]
    assert set(fams["llama31-8b"]["contrasts"]) == {"P3", "P4", "P6"}          # P1, P2, P5 are not tested there
    assert doc["design"] == {"name": "reduced", "stopped": ["llama31-8b"]}
    with pytest.raises(SystemExit, match="needs --stopped with families of option C"):
        sim.simulate(settings, "C", "reduced", ["llama31-8b"])
    with pytest.raises(SystemExit, match="--stopped needs --design reduced"):
        sim.simulate(settings, "B", "full", ["olmo2-7b"])
    with pytest.raises(SystemExit, match="--option is one of"):
        sim.simulate(settings, "A", "full", [])
    with pytest.raises(SystemExit, match="--sigma names indices"):
        sim.simulate(settings, "B", "full", [], [3])


def test_the_settings_are_checked_and_b16_is_pinned(tmp_path, monkeypatch):
    with pytest.raises(SystemExit, match="chunk divides reps"):
        sim.read_settings(smoke_settings(tmp_path, reps=50, chunk=30))
    with pytest.raises(SystemExit, match="exactly its keys"):
        sim.read_settings(smoke_settings(tmp_path, extra=1))
    with pytest.raises(SystemExit, match="reml.starts"):
        s = json.loads(SETTINGS.read_text())
        sim.read_settings(smoke_settings(tmp_path, reml={**s["reml"], "starts": "two"}))
    monkeypatch.setitem(sim.FROZEN, "tdist", (sim.FROZEN["tdist"][0], "0" * 64))
    with pytest.raises(SystemExit, match="tdist.py differs from its pinned SHA-256"):
        sim._load("tdist")


def test_the_committed_settings_hold_the_grid_and_the_rule():
    s, digest = sim.read_settings(SETTINGS)
    assert s["reps"] == 20000 and s["reps"] % s["chunk"] == 0
    assert s["sigma_pair_pp"][0] == "3.0" and s["sigma_pair_pp"][-1] == "8.24"
    assert {"3.0", "4.0", "4.5", "5.0", "6.0", "8.24"} <= set(s["sigma_pair_pp"])       # P1 §6.3's values
    assert s["power_effects_pp"] == ["8", "10", "12"] and s["alpha"] == "0.05"
    assert s["reading_rule"]["threshold_familywise"] == "0.06" and "N decides alone" in s["reading_rule"]["text"]
    assert [(i["name"], i["method_variance_share"]) for i in s["interaction"]] == \
        [("none", "0"), ("arm x seed 0.5", "0.5"), ("arm x seed 1", "1"), ("llama sigma x 1.5", "0"),
         ("llama sigma x 1/1.5", "0")]
    assert [i["llama_sigma_ratio"] for i in s["interaction"]] == ["1", "1", "1", "3/2", "2/3"]
    assert "either family ratio" in s["reading_rule"]["text"] and "U claims" in s["reading_rule"]["text"]
    assert s["written_utc"].startswith("2026-11-08T17:53:15Z")
    assert "0.5% absolute in all (10% of alpha, alpha = 5%)" in s["limits"][1] and "0.5% of alpha" not in s["limits"][1]
    assert "with or without the interaction" in s["reading_rule"]["text"] and "every scenario of 'interaction'" in s["reading_rule"]["applies_to"]
    assert s["n_stage"]["sigma_eval0_pp"] == "1.28" and s["n_stage"]["prompts"] == 200
    assert any("prompt (item) part" in x for x in s["limits"])
    b16 = json.loads((ROOT / "scripts/stage1_s1/reading/settings/reading.json").read_text())["reml"]
    assert {k: s["reml"][k] for k in ("tol", "max_iter", "step_clip_log", "starts", "multi_start_ll_tolerance")} == \
        {k: b16[k] for k in ("tol", "max_iter", "step_clip_log", "starts", "multi_start_ll_tolerance")}


def test_the_cell_sds_take_the_interaction_as_a_variance_share():
    for share, factor in ((1.0, math.sqrt(2.0)), (0.5, math.sqrt(1.5)), (0.0, 1.0)):
        sd = sim.cell_sd(6.0, share)
        for (a, _), v in zip(sim.CELLS, sd):
            assert math.isclose(v, 6.0 / math.sqrt(2) * (factor if a in sim.METHODS else 1.0), rel_tol=1e-12), (share, a)


def test_n_prompt_values_keep_each_cells_u_and_their_pair_se_is_sigma_eval0():
    rng = np.random.default_rng(8)
    y_all = {f: rng.standard_normal((4000, len(sim.CELLS))) * 3 for f in sim.FAMILIES}
    eta = rng.standard_normal((4000, 2, 2, 3, 200))
    prompts = sim.n_prompt_values(y_all, eta, 1.28)
    for f in sim.FAMILIES:
        for (role, j), v in prompts[f].items():
            assert v.shape == (4000, 200) and np.allclose(v.mean(axis=1), y_all[f][:, sim.INDEX[(role, j)]])
    d = prompts["olmo2-7b"][("a0", 1102)] - prompts["olmo2-7b"][("R", 1102)]
    se2 = d.var(axis=1, ddof=1) / 200
    assert abs(se2.mean() / 1.28 ** 2 - 1) < 0.01


def synthetic_arm(gb, bars, counts):
    """A Gate B arm record from per-prompt Unsafe counts out of 3 samples (stand-in answers; no text)."""
    pairs = []
    for p, k in enumerate(counts):
        for s in range(3):
            pairs.append(({"prompt_id": f"p{p:03d}", "sample_index": s, "kind": "harm", "stop_reason": "eos",
                           "repetition_4gram": 0.0, "empty": False, "output_tokens": 40, "output_ids": [1]},
                          {"prompt_id": f"p{p:03d}", "sample_index": s, "valid": True, "reason": None,
                           "safety": "Unsafe" if s < k else "Safe", "categories": [], "refusal": "No"}))
    return gb.arm_record(pairs, [], bars)


@pytest.mark.parametrize("case", ["plain", "floor"])
def test_ns_sigma_pool_is_noise_readings_on_the_same_cells(case):
    """GXB S-7: on the same N cells (per-prompt Unsafe counts of a0 and R at 1101-1103 on both families),
    sigma_pool_sq equals noise_reading.pooled's σ̂_pool² through the frozen Gate B reader, the σ_eval floor included.
    In the 'floor' case every r_j is 0 (each R cell holds its a0 cell's counts in another prompt order), so the
    median pair SE governs."""
    from scripts.scale78b import noise_reading as nr
    gb = nr.GB
    bars = json.loads(gb.FR.DEFAULT_BARS.read_text())
    rng = np.random.default_rng(31 if case == "plain" else 32)
    families, prompts = {}, {}
    for f in sim.FAMILIES:
        arms, u, prompts[f] = {}, {"a0": [], "R": []}, {}
        for j in sim.N_SEEDS:
            a0 = rng.integers(0, 4, 40)
            r = rng.permutation(a0) if case == "floor" else rng.integers(0, 4, 40)
            for role, counts, key in (("a0", a0, "a0"), ("R", r, gb.r_key(j))):
                arms[(key, j)] = synthetic_arm(gb, bars, [int(k) for k in counts])
                prompts[f][(role, j)] = (100.0 * counts / 3.0)[None, :]
                u[role].append(100 * arms[(key, j)]["U"]["plain"])
        rd = gb.Reader(arms, [], [], False).reading("plain")
        families[f] = {"governing": "plain", "_exact": {
            "sdr2": rd["sdr2"], "pair_se2": {k: v["se2"] for k, v in rd["pairs"].items()},
            "arm_ss": sum((gb.variance(v) * (len(v) - 1) for v in u.values()), Fraction(0)), "arm_df": 4}}
    pool = nr.pooled(families)
    ours = math.sqrt(sim.sigma_pool_sq(prompts)[0])
    assert math.isclose(ours, pool["sigma_pool_pp"], rel_tol=1e-9)
    if case == "floor":
        assert pool["sqrt_P_pool_pp"] == 0 and math.isclose(ours, pool["median_pair_se_pp"], rel_tol=1e-9) and ours > 0
    else:
        assert pool["sqrt_P_pool_pp"] > pool["median_pair_se_pp"]


def test_power_and_better_count_holm_rejections_with_a_positive_estimate(tmp_path):
    settings = smoke_settings(tmp_path, sigma_pair_pp=["1.0"], power_effects_pp=["-1000", "0", "2", "1000"],
                              interaction=[{"name": "none", "method_variance_share": "0", "llama_sigma_ratio": "1"}])
    doc = sim.simulate(settings, "C", "full", [])
    sc = doc["rows"][0]["scenarios"]["none"]
    assert sc["plan_by_sigma_A"]["A"] == 1.0
    fam = sc["families"]["olmo2-7b"]
    for k, c in fam["contrasts"].items():
        # a replicate whose Satterthwaite df is below 1 keeps a heavy tail at any shift, so power stays just below 1
        assert fam["power"]["1000"][k] == fam["better"]["1000"][k] >= 0.9 and c["tested"] == 60
        assert fam["power"]["0"][k] <= c["holm_rate"] and fam["better"]["0"][k] == 0.0
        assert fam["power"]["-1000"][k] == 0.0                      # a rejection with a negative estimate is no power
        assert fam["power"]["2"][k] >= 0.5 and fam["better"]["2"][k] == 0.0   # 2 pp is below the SESOI (5 pp)


def test_the_null_size_is_near_nominal_on_plan_a(tmp_path):
    """A coarse check of the whole test (REML, Satterthwaite df, t): at σ_pair 3.0 every replicate reads plan A, and the
    six contrasts' unadjusted two-sided 5% tests reject about 5% of the time (PR4 §3.2: 5.1-5.3%; here 1,200 replicates,
    7,200 correlated tests, so a wide band)."""
    settings = smoke_settings(tmp_path, sigma_pair_pp=["3.0"], reps=1200, chunk=600,
                              interaction=[{"name": "none", "method_variance_share": "0", "llama_sigma_ratio": "1"}])
    fam = sim.simulate(settings, "C", "full", [])["rows"][0]["scenarios"]["none"]["families"]["olmo2-7b"]
    size = sum(c["size_count"] for c in fam["contrasts"].values()) / sum(c["tested"] for c in fam["contrasts"].values())
    assert 0.035 <= size <= 0.07, size
    assert fam["familywise_rate"] <= 0.09
    holm = [c["holm_count"] for c in fam["contrasts"].values()]
    assert max(holm) > 0 and max(holm) <= fam["familywise_count"] <= sum(holm)


def test_a_replicate_where_d4s_multi_start_moves_the_maximum_matches_b16():
    """A replicate (found by search) whose pre-registered start ends at a lower REML maximum than another floor
    pattern's: the vectorized multi-start reaches B16's governing end point, the pre-registered form B16's prereg."""
    cluster = sim.analysis_design("A", False)["clusters"]["removal"]
    y = np.random.default_rng(1001).standard_normal((25, len(cluster["cells"]))) * 3
    cells = [(a, j, float(v)) for (a, j), v in zip(cluster["cells"], y[2])]
    fit = sim.REML.fit_cells(cells, cluster["arms"], 0.01, multi_start=True)
    assert fit.start_differs
    with np.errstate(all="ignore"):
        multi = sim.reml_batch(cluster, y.copy(), 0.01, {**OPTS, "starts": "multi"})[0][2]
        pre = sim.reml_batch(cluster, y.copy(), 0.01, {**OPTS, "starts": "pre-registered"})[0][2]
    for i, arm in enumerate(cluster["arms"]):
        assert math.isclose(multi[i], fit.sigma2[arm], rel_tol=1e-6, abs_tol=1e-9)
        assert math.isclose(pre[i], fit.prereg.sigma2[arm], rel_tol=1e-6, abs_tol=1e-9)
    assert not np.allclose(multi, pre)


def test_each_chunk_has_its_own_stream_and_shards_of_other_runs_do_not_merge(tmp_path):
    a, b = sim.chunk_normals(11, 0, 4), sim.chunk_normals(11, 1, 4)
    assert a.shape == (4, 2, len(sim.CELLS)) and not np.allclose(a, b)
    want = np.random.Generator(np.random.PCG64(np.random.SeedSequence([11, 1]))).standard_normal((4, 2, len(sim.CELLS)))
    assert np.array_equal(b, want) and np.array_equal(sim.chunk_normals(11, 0, 4), a)
    settings = smoke_settings(tmp_path, sigma_pair_pp=["4.0", "6.0"], interaction=[{"name": "none", "method_variance_share": "0", "llama_sigma_ratio": "1"}])
    for option, index in (("B", 0), ("C", 1)):
        doc = sim.simulate(settings, option, "full", [], [index])
        (tmp_path / f"shard-{option}.json").write_bytes(sim.render(doc))
    with pytest.raises(SystemExit, match="the shards differ in their header"):
        sim.merge([tmp_path / "shard-B.json", tmp_path / "shard-C.json"])


# ----- SV-2: the chain inside run_chunk, replicate by replicate, against an independent chain -------------------------------

E2E_PLANS = {"A": dict(methods=("A1", "L1", "H1", "S1", "S3", "S4"), mseeds=range(1102, 1108), rseeds=range(1101, 1108),
                       a0_in=True, primary=("P1", "P2", "P3", "P4", "P5", "P6")),
             "B9": dict(methods=("A1", "H1", "S1", "S4"), mseeds=range(1102, 1111), rseeds=range(1101, 1111), a0_in=False,
                        primary=("P1", "P3", "P6")),
             "H": dict(methods=("A1", "H1", "S1", "S4"), mseeds=range(1102, 1114), rseeds=range(1101, 1114), a0_in=False,
                       primary=("P1", "P3", "P6"))}
E2E_CLUSTER = {"R": "removal", "A1": "removal", "L1": "removal", "H1": "removal",
               "a0": "full", "S1": "full", "S3": "full", "S4": "full"}
E2E_PAIRS = {"P1": ("R", "A1"), "P2": ("R", "L1"), "P3": ("R", "H1"), "P4": ("a0", "S1"), "P5": ("S1", "S3"),
             "P6": ("S1", "S4")}


def independent_chain(y_all: dict, option: str, stopped: set, effects: list, reps: int) -> dict:
    """The verifier's e2e_parity.py chain (R/r1-s-verify-scratch/e2e_parity.py), built from other code: σ̂_A by
    blinded_sigma.pooled_sigma (exact rationals) on blinded_sigma's designs, the plan by noise_reading.seed_rule,
    per family B16's fit_cells (multi-start, the lone 1101 cells in the fit, the two-arm sum rule on the paired
    cells), contrast_fit (with_item False), phi.holm at 5%; power and better by shifting the estimate."""
    import dataclasses
    from scripts.scale78b import blinded_sigma as bs
    from scripts.scale78b import noise_reading as nr
    from scripts.stage1_s1.reading import contrast as con, phi
    fams = sim.OPTIONS[option]
    plans = {k: 0 for k in sim.PLAN_LABELS}
    out = {f: {"familywise": 0, "refused": 0, "contrasts": {}, "power": {e: {} for e in effects},
               "better": {e: {} for e in effects}} for f in fams}

    def bump(d, k):
        d[k] = d.get(k, 0) + 1
    for r in range(reps):
        clusters = {}
        for f in fams:
            for (a, j), c in bs.design_cells("anchor_stopped" if f in stopped else "full").items():
                clusters.setdefault(f"{f} {c}", {})[(a, j)] = Fraction(float(y_all[f][r, sim.INDEX[(a, j)]]))
        sigma_a, _ = bs.pooled_sigma(clusters)
        rule = nr.seed_rule(((Fraction(sigma_a) ** 2,),), 0)
        plan = "review" if rule["review"] else rule["plan"]
        plans[plan] += 1
        if plan == "review":
            continue
        p = E2E_PLANS[plan]
        for f in fams:
            st = f in stopped
            arms = [a for a in (("a0",) if p["a0_in"] else ()) + ("R",) + p["methods"]
                    if not (st and a in ("A1", "L1", "S3"))]
            seeds = {a: (range(1101, 1108) if a == "a0" else p["rseeds"] if a == "R" else p["mseeds"]) for a in arms}
            table = {(a, j): np.array([float(y_all[f][r, sim.INDEX[(a, j)]])]) for a in arms for j in seeds[a]}
            fits = {}
            for cname in ("removal", "full"):
                carms = tuple(a for a in arms if E2E_CLUSTER[a] == cname)
                if len(carms) < 2:
                    continue
                cells = [(a, j, float(table[(a, j)][0])) for a in carms for j in seeds[a]]
                if len(carms) == 2:
                    common = [j for j in seeds[carms[0]] if j in seeds[carms[1]]]
                    cells = [(a, j, v) for a, j, v in cells if j in common]
                fits[cname] = sim.REML.fit_cells(cells, carms, 0.01, multi_start=True)
            est = {}
            for k in p["primary"]:
                c, m = E2E_PAIRS[k]
                if c in arms and m in arms:
                    common = [j for j in seeds[c] if j in seeds[m]]
                    est[k] = con.contrast_fit(table, fits[E2E_CLUSTER[c]], c, m, common, 1.0, with_item=False)
            pv = {k: e.p_two_sided() for k, e in est.items()}
            rej = phi.holm(pv, 0.05)
            o = out[f]
            o["familywise"] += bool(rej)
            for k, e in est.items():
                c = o["contrasts"].setdefault(k, {"tested": 0, "size": 0, "holm": 0})
                c["tested"] += 1
                c["size"] += pv[k] < 0.05
                c["holm"] += k in rej
                for d in effects:
                    shifted = dataclasses.replace(e, est=e.est + float(d))
                    hit = k in phi.holm({**pv, k: shifted.p_two_sided()}, 0.05) and shifted.est > 0
                    if hit:
                        bump(o["power"][d], k)
                        if shifted.est >= 5:
                            bump(o["better"][d], k)
    return {"plans": plans, "families": out}


@pytest.mark.parametrize("option,stopped,sigma,share,ratio", [
    ("B", set(), 4.5, 0.5, 1.0), ("C", set(), 5.5, 0.0, 1.0), ("B", {"llama31-8b"}, 6.0, 1.0, 1.0),
    ("C", {"olmo2-7b"}, 8.24, 1.0, 1.0), ("B", set(), 5.0, 0.0, 1.5), ("B", {"olmo2-7b", "llama31-8b"}, 4.0, 0.0, 1.0)])
def test_run_chunks_chain_equals_an_independent_chain_replicate_by_replicate(option, stopped, sigma, share, ratio):
    """SV-2: σ̂_A on the option's families and design → block B's plan → the claim test on the same draws, inside
    run_chunk, equals the independent chain on every tally (plans, per family the familywise count, each contrast's
    tested, size and Holm counts, power and better at each effect), on [B] and [C], full and reduced designs, and one
    family-ratio scenario (GXB R-12)."""
    reps = 40
    effects = ["4", "8"]
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([424242, int(10 * sigma)])))
    z = rng.standard_normal((reps, 2, len(sim.CELLS)))
    eta = rng.standard_normal((reps, 2, 2, 3, 50))
    s = json.loads(SETTINGS.read_text())
    s.update(power_effects_pp=effects, _reml={**OPTS, "starts": "multi"})
    sigmas = {"olmo2-7b": sigma, "llama31-8b": min(sigma * ratio, 8.24)}
    designs = {(p, st): sim.analysis_design(p, st) for p in ("A", "B9", "H") for st in (False, True)}
    fams = sim.OPTIONS[option]
    allk = {f: [k for k in sim.CONTRASTS if any(k in designs[(p, f in stopped)]["contrasts"] for p in ("A", "B9", "H"))]
            for f in fams}
    tallies = {f: sim.new_tally(allk[f], effects) for f in fams}
    plans = {"sigma_A": {k: 0 for k in sim.PLAN_LABELS}, "N": {k: 0 for k in sim.PLAN_LABELS}}
    with np.errstate(all="ignore"):
        sim.run_chunk(z, eta, sigmas, share, option, stopped, s, tallies, plans, designs)
    y_all = {f: z[:, i, :] * sim.cell_sd(sigmas[f], share)[None, :] for i, f in enumerate(sim.FAMILIES)}
    with np.errstate(all="ignore"):
        ref = independent_chain(y_all, option, stopped, effects, reps)
    assert plans["sigma_A"] == ref["plans"]
    assert plans["N"] == independent_n_plans(y_all, eta, 1.28, reps)                                       # SR7
    assert sum(1 for v in ref["plans"].values() if v) >= 1 and sum(ref["plans"].values()) == reps
    for f in fams:
        t, o = tallies[f], ref["families"][f]
        assert t["familywise"] == o["familywise"] and t["refused"] == 0, f
        for k, c in t["contrasts"].items():
            want = o["contrasts"].get(k, {"tested": 0, "size": 0, "holm": 0})
            assert (c["tested"], c["size"], c["holm"]) == (want["tested"], want["size"], want["holm"]), (f, k)
            for d in effects:
                assert t["power"][d][k] == o["power"][d].get(k, 0) and t["better"][d][k] == o["better"][d].get(k, 0), (f, k, d)
    if option == "B":
        assert set(tallies) == {"olmo2-7b", "llama31-8b"}


def test_the_parity_configurations_spread_the_plans():
    """The integration test's draws reach plan A, B9 and H (b) across its configurations (so the plan link is held)."""
    seen = set()
    for sigma in (4.5, 5.5, 6.0, 8.24, 5.0, 4.0):
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([424242, int(10 * sigma)])))
        z = rng.standard_normal((40, 2, len(sim.CELLS)))
        y_all = {f: z[:, i, :] * sim.cell_sd(sigma, 0.0)[None, :] for i, f in enumerate(sim.FAMILIES)}
        with np.errstate(all="ignore"):
            seen |= set(sim.plan_of(sim.sigma_a_sq(y_all, "B", set())[0], json.loads(SETTINGS.read_text())))
    assert {"A", "B9", "H"} <= seen


def test_family_sigmas_scale_llama_and_cap_at_the_grids_top(tmp_path):
    """GXB R-12: the grid's σ is OLMo-2-7B's; Llama-3.1-8B's is the scenario's ratio times it, capped at the top."""
    s = json.loads(SETTINGS.read_text())
    by = {i["name"]: i for i in s["interaction"]}
    assert sim.family_sigmas("4.0", by["none"], s) == {"olmo2-7b": 4.0, "llama31-8b": 4.0}
    assert sim.family_sigmas("4.0", by["llama sigma x 1.5"], s) == {"olmo2-7b": 4.0, "llama31-8b": 6.0}
    assert sim.family_sigmas("7.0", by["llama sigma x 1.5"], s) == {"olmo2-7b": 7.0, "llama31-8b": 8.24}
    low = sim.family_sigmas("6.0", by["llama sigma x 1/1.5"], s)
    assert low["olmo2-7b"] == 6.0 and math.isclose(low["llama31-8b"], 4.0, rel_tol=1e-15)
    with pytest.raises(SystemExit, match="llama_sigma_ratio > 0"):
        sim.read_settings(smoke_settings(tmp_path, interaction=[{"name": "x", "method_variance_share": "0"}]))



def independent_n_plans(y_all: dict, eta, sigma_eval0: float, reps: int) -> dict:
    """SR7: N's printed plan from an independent σ̂_pool: per family the per-prompt differences of the a0 and R cells
    (sim.n_prompt_values, tested on its own) taken to Fractions, r_j and SD(r)² by gate_b_reading's variance, each pair's
    prompt-clustered SE² by family_probe_reading.clustered_se2, then noise_reading.pooled and its seed_rule."""
    from scripts.scale78b import noise_reading as nr
    gb = nr.GB
    prompts = sim.n_prompt_values(y_all, eta, sigma_eval0)
    plans = {k: 0 for k in sim.PLAN_LABELS}
    for r in range(reps):
        families = {}
        for f in sim.FAMILIES:
            rs, se2 = [], {}
            for j in sim.N_SEEDS:
                d = [Fraction(float(a)) - Fraction(float(b))
                     for a, b in zip(prompts[f][("a0", j)][r], prompts[f][("R", j)][r])]
                rs.append(sum(d) / len(d))
                se2[f"a0@{j}|R{j - 1100}@{j}"] = gb.FR.clustered_se2(d)
            families[f] = {"governing": "plain", "_exact": {"sdr2": gb.variance(rs), "pair_se2": se2,
                                                            "arm_ss": Fraction(1), "arm_df": 1}}
        rule = nr.pooled(families)["seed_rule"]
        plans["review" if rule["review"] else rule["plan"]] += 1
    return plans


@pytest.mark.parametrize("option,index", [("B", 5), ("B", 7)])
def test_each_familys_own_sigma_reaches_run_chunk_through_simulate_row(tmp_path, option, index):
    """SR1: through simulate_row (the settings' scenarios, family_sigmas, the chunk streams), the row's plan counts and
    each family's familywise and Holm counts equal the independent chain run at each family's own true σ, derived here:
    OLMo-2-7B's is the grid's, Llama-3.1-8B's the scenario's ratio times it, capped at the grid's top. So the two
    ratio scenarios cannot become copies of 'none' (the re-verifier's e2e_row_parity.py form)."""
    reps, seed = 30, 778 + index
    s = json.loads(SETTINGS.read_text())
    names = ("none", "llama sigma x 1.5", "llama sigma x 1/1.5")
    s.update(reps=reps, chunk=reps, seed=seed, power_effects_pp=["8"],
             interaction=[i for i in s["interaction"] if i["name"] in names])
    r = s["reml"]
    s["_reml"] = {"tol": float(r["tol"]), "max_iter": int(r["max_iter"]), "clip": float(r["step_clip_log"]),
                  "starts": r["starts"], "ll_tol": float(r["multi_start_ll_tolerance"])}
    with np.errstate(all="ignore"):
        row = sim.simulate_row(index, s, option, set())
    z = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, 0]))).standard_normal((reps, 2, len(sim.CELLS)))
    grid = s["sigma_pair_pp"]
    top = max(Fraction(g) for g in grid)
    differ = set()
    for sc in s["interaction"]:
        true = {"olmo2-7b": Fraction(grid[index]),
                "llama31-8b": min(Fraction(grid[index]) * Fraction(sc["llama_sigma_ratio"]), top)}
        y_all = {f: z[:, i, :] * (float(true[f]) / math.sqrt(2)) for i, f in enumerate(sim.FAMILIES)}  # share 0
        with np.errstate(all="ignore"):
            ref = independent_chain(y_all, option, set(), [], reps)
        got = row["scenarios"][sc["name"]]
        assert {k: round(v * reps) for k, v in got["plan_by_sigma_A"].items()} == ref["plans"], sc["name"]
        for f in sim.OPTIONS[option]:
            fam = got["families"][f]
            assert fam["familywise_count"] == ref["families"][f]["familywise"], (sc["name"], f)
            want = {k: v["holm"] for k, v in ref["families"][f]["contrasts"].items()}
            assert {k: v["holm_count"] for k, v in fam["contrasts"].items() if v["tested"]} == \
                {k: want.get(k, 0) for k, v in fam["contrasts"].items() if v["tested"]}, (sc["name"], f)
        differ.add(json.dumps(ref["plans"], sort_keys=True) + json.dumps(ref["families"]["llama31-8b"]["familywise"]))
    assert len(differ) >= 2, "the three scenarios gave the same plans and Llama counts: the test cannot tell them apart"


def synthetic_doc(reps: int, cells: dict) -> dict:
    """A [B] output document for summarize: rows 0-1, the five scenario names, per family counts from ``cells``
    ((sigma_index, scenario, family) -> (familywise_count, refused, nonconverged)); others 0."""
    s = json.loads(SETTINGS.read_text())
    names = [i["name"] for i in s["interaction"]]
    rows = []
    for i in (0, 1):
        sc = {}
        for n in names:
            fams = {}
            for f in ("llama31-8b", "olmo2-7b"):
                c, refused, nonconv = cells.get((i, n, f), (0, 0, 0))
                fams[f] = {"familywise_count": c, "familywise_rate": round(c / reps, 6), "refused_contrasts": refused,
                           "nonconverged_fits": nonconv}
            sc[n] = {"families": fams}
        rows.append({"sigma_index": i, "sigma_pair_pp": s["sigma_pair_pp"][i], "scenarios": sc})
    return {"reps": reps, "reading_rule": s["reading_rule"], "rows": rows}


def test_the_summarys_largest_rate_covers_both_families_and_every_scenario():
    """SR2, SR5, SR6: under [B] the largest familywise rate is found in Llama-3.1-8B's family and in a ratio scenario;
    a count of exactly 6% of the replicates is not above the threshold, one more is; a nonzero refused-contrast total
    and the non-converged total are the rows' sums."""
    reps = 20000
    doc = synthetic_doc(reps, {(0, "none", "olmo2-7b"): (1100, 0, 5), (1, "llama sigma x 1.5", "llama31-8b"): (1150, 3, 7),
                               (0, "arm x seed 1", "llama31-8b"): (1149, 0, 0), (1, "none", "olmo2-7b"): (900, 2, 0)})
    summary = sim.summarize(doc, 2)
    top = summary["max_familywise"]
    assert (top["family"], top["scenario"], top["sigma_pair_pp"], top["familywise_count"]) == \
        ("llama31-8b", "llama sigma x 1.5", doc["rows"][1]["sigma_pair_pp"], 1150)
    assert summary["max_above_threshold"] is False                       # 1150 / 20000 = 5.75%
    assert summary["refused_contrasts_total"] == 5 and summary["nonconverged_fits_total"] == 12
    assert "llama sigma x 1.5, llama31-8b" in summary["reading_line"]
    tie = sim.summarize(synthetic_doc(reps, {(1, "llama sigma x 1/1.5", "llama31-8b"): (1200, 0, 0)}), 2)
    assert tie["max_familywise"]["familywise_count"] == 1200 and tie["max_familywise"]["scenario"] == "llama sigma x 1/1.5"
    assert tie["max_above_threshold"] is False                           # exactly 6%: not above (DES K6)
    above = sim.summarize(synthetic_doc(reps, {(0, "llama sigma x 1/1.5", "llama31-8b"): (1201, 0, 0)}), 2)
    assert above["max_above_threshold"] is True and above["max_familywise"]["family"] == "llama31-8b"
