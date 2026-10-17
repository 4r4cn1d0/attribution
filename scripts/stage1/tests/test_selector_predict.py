"""REQ-18 (the predictions), W1-15 and the Part E command line: synthetic only, small replicate counts."""

from __future__ import annotations

import copy
import json

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1.selector import predict as pr

import selector_fixtures as fx

DIGESTS = {"selector_spec": "a" * 64, "selector_simulate": "b" * 64, "selector_predict": "c" * 64}


@pytest.fixture(scope="module")
def built() -> bytes:
    S, M, P = fx.tiny()
    return pr.build(S, M, P, DIGESTS)


def test_the_predict_settings_load_with_their_literal_pin():
    assert sha256_file(pr.SETTINGS_PATH) == pr.SETTINGS_SHA256
    assert pr.load()[1] == pr.SETTINGS_SHA256
    S, M, P, digests = pr.load_all(pr.spec.SETTINGS_PATH, pr.sm.SETTINGS_PATH, pr.SETTINGS_PATH)
    assert digests == {"selector_spec": pr.spec.SETTINGS_SHA256, "selector_simulate": pr.sm.SETTINGS_SHA256,
                       "selector_predict": pr.SETTINGS_SHA256}


# ----- c* (L15 (5)) ----------------------------------------------------------------------------------------


GRID = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0]


def test_c_star_is_the_first_crossing_on_a_monotone_curve():
    out = pr.c_star(GRID, [0.5, 0.4, 0.2, -0.1, -0.3, -0.6])
    assert out["kind"] == "grid_point" and out["value"] == 0.25 and not out["non_monotone"]
    assert out["interpolated"] == pytest.approx(0.25 + 0.25 * 0.2 / 0.3)


def test_c_star_is_the_first_crossing_not_the_last():
    out = pr.c_star(GRID, [0.5, -0.1, 0.2, 0.1, -0.2, -0.3])
    assert out["value"] == 0.0 and out["non_monotone"]
    assert out["interpolated"] == pytest.approx(0.1 * 0.5 / 0.6)


def test_c_star_none_and_at_least_the_grid_maximum():
    assert pr.c_star(GRID, [-0.1, 0.2, 0.3, 0.4, 0.5, 0.6])["kind"] == "none"
    out = pr.c_star(GRID, [0.0, 0.1, 0.0, 0.2, 0.3, 0.0])
    assert out["kind"] == "at_least_grid_max" and out["value"] == 2.0
    with pytest.raises(s1.Refusal):
        pr.c_star([0.1, 0.0], [0.0, 0.0])


# ----- the predictions document --------------------------------------------------------------------------


def test_a_rerun_reproduces_predictions_json(built):
    S, M, P = fx.tiny()
    assert pr.build(S, M, P, DIGESTS) == built
    assert pr.build(S, M, P, DIGESTS, workers=2) == built


def test_both_conventions_every_budget_and_the_units_are_present(built):
    doc = json.loads(built)
    assert doc["conventions"] == ["C-full", "C-lean"] and "c0" in doc["units"]
    for menu_id in ("category", "planted_8"):
        block = doc["menus"][menu_id]
        assert set(block["conventions"]) == {"C-full", "C-lean"}
        for conv in block["conventions"].values():
            assert set(conv["budgets"]) == {"2", "4", "8"} and conv["budgets"]["2"]["boundary_cell"]
            assert conv["costs_in_c0"]["full_run"] >= 1.0 and conv["unit"]
            cell = conv["budgets"]["8"]
            assert cell["runs_only"]["frozen_rule"] in block["rules"]
            oracle = cell["runs_only"]["oracle_best_rule_by_mean"]["5"]
            assert oracle["E_G"] == max(v["5"]["E_G"]["mean"] for v in cell["runs_only"]["by_rule"].values())
            assert set(cell["V_max"]) == {"2", "5", "10"}
            by_rule = cell["runs_only"]["by_rule"]
            for rule in block["rules"]:
                stats = by_rule[rule]["5"]
                assert {"E_G", "P_best", "regret", "violation"} <= set(stats)
                assert len(stats["E_G"]["interval_prior_grid"]) == 2 and "mc_se_bound" in stats["E_G"]
            diag = cell["diagnostic"]["by_tau_o"]["5"]["by_quality"]
            for q, curve in diag.items():
                assert curve["c_d_grid"] == [0.0, 0.5, 2.0] and len(curve["Delta"]) == 3
                assert curve["c_star"]["kind"] in ("none", "grid_point", "at_least_grid_max")
            assert set(cell["sensitivities"]) == {"sigma_high", "hetero_2x"}


def test_both_placement_statistics_are_present_and_never_fitted(built):
    doc = json.loads(built)
    planted = doc["menus"]["planted_8"]["placement"]
    assert planted["statistic"] == {"primary": "top_k_hit", "secondary": "row_auc"}
    auc = {"auc=0.5", "auc=0.6", "auc=0.75", "auc=0.9"}
    assert set(planted["by_quality"]) == auc | {"r=0", "r=0.5", "r=1", "r=2", "r=4"}      # r: report-only
    for q, entry in planted["by_quality"].items():
        assert set(entry) == ({"top_k_hit", "row_auc"} if q in auc else {"top_k_hit"})
        assert all(len(v["range_90"]) == 2 for v in entry["top_k_hit"].values())
    assert planted["by_quality"]["auc=0.9"]["row_auc"]["mean"] > planted["by_quality"]["auc=0.6"]["row_auc"]["mean"]
    category = doc["menus"]["category"]["placement"]
    assert category["statistic"] == "spearman_rho" and "sim2" in category["by_quality"]
    assert set(category["by_quality"]) >= {"r=0", "r=0.5", "r=1", "r=2", "r=4", "uninformative"}
    def keys(x):
        return (set(x) | set().union(*(keys(v) for v in x.values()))) if isinstance(x, dict) else set()
    for menu_id in ("category", "planted_8"):
        block = doc["menus"][menu_id]["placement"]["by_quality"]
        assert not {k for k in keys(block) if "fit" in k or "measured" in k}        # ranges only; nothing fitted


def test_the_classifier_row_and_the_llama_block_are_present(built):
    doc = json.loads(built)
    row = doc["named_diagnostics"]["classifier"]
    assert row["quality_grid"] == "row_auc" and row["quality_fitted"] is False
    assert set(row["curves"]) == {"planted_8"} or set(row["curves"]) >= {"planted_8"}
    assert set(row["curves"]["planted_8"]) == {"C-full", "C-lean"}
    llama = doc["llama"]["conventions"]
    for conv in ("C-full", "C-lean"):
        preds = llama[conv]["predictions"]
        assert set(preds) == {"4", "8"} and set(preds["4"]) == {"halving", "one_shot"}
        assert {"P_best", "regret"} <= set(preds["8"]["halving"]["5"])
        assert set(llama[conv]["replay_check"]) == {"4|halving", "4|one_shot", "8|halving", "8|one_shot"}


def test_the_predictions_name_their_code_and_settings(built):
    doc = json.loads(built)
    assert doc["settings_sha256"] == DIGESTS
    assert set(doc["code_sha256"]) == {"spec.py", "simulate.py", "predict.py"}
    prov = doc["provenance"]
    assert prov["settings_sha256"] == DIGESTS["selector_predict"]
    assert set(prov["label_entries"]) == {"selector.psi", "selector.ties", *pr.sm.DRAW_KEYS.values()}
    assert built == canonical_json(doc)


def test_delta_is_zero_at_c_d_zero_when_k_is_m(built):
    doc = json.loads(built)
    for menu_id in ("category",):
        for conv in doc["menus"][menu_id]["conventions"].values():
            for b, cell in conv["budgets"].items():
                for tau, block in cell["diagnostic"]["by_tau_o"].items():
                    for q, curve in block["by_quality"].items():
                        if curve["k"][0] == 8:
                            assert curve["Delta"][0] == 0.0, (b, tau, q)


# ----- the command line ----------------------------------------------------------------------------------


def test_check_inputs_refuses_a_change_a_missing_file_and_an_unnamed_gate_b_path(tmp_path):
    good = tmp_path / "records" / "a.json"
    good.parent.mkdir()
    good.write_bytes(b"{}\n")
    sim = {"inputs": [{"id": "a", "path": "records/a.json", "sha256": sha256_bytes(b"{}\n"), "gate_b_value": False},
                      {"id": "ledger", "path": None, "sha256_prefix": "898a3aaf599579ad", "gate_b_value": True}]}
    rows = pr.check_inputs(sim, tmp_path)
    assert rows[0]["status"] == "ok" and rows[1]["status"].startswith("unpinned")
    changed = copy.deepcopy(sim)
    changed["inputs"][0]["sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="hashes to"):
        pr.check_inputs(changed, tmp_path)
    missing = copy.deepcopy(sim)
    missing["inputs"][0]["path"] = "records/b.json"
    with pytest.raises(s1.Refusal, match="missing"):
        pr.check_inputs(missing, tmp_path)
    gate = tmp_path / "tmp" / "gate-b-olmo" / "x.json"
    gate.parent.mkdir(parents=True)
    gate.write_bytes(b"{}\n")
    unnamed = {"inputs": [{"id": "g", "path": "tmp/gate-b-olmo/x.json", "sha256": sha256_bytes(b"{}\n"),
                           "gate_b_value": False}]}
    with pytest.raises(s1.Refusal, match="Gate B"):
        pr.check_inputs(unnamed, tmp_path)
    unnamed["inputs"][0]["gate_b_value"] = True
    assert pr.check_inputs(unnamed, tmp_path)[0]["status"] == "ok"


def test_the_pinned_settings_list_every_input_by_path_and_hash():
    sim = fx.raw("selector_simulate")
    assert sim["inputs"]
    for entry in sim["inputs"]:
        assert entry["path"] is None or not entry["path"].startswith("/")
        assert (entry.get("sha256") and s1.HEX64.match(entry["sha256"])) or len(entry.get("sha256_prefix", "")) == 16
        if entry["path"] and entry["path"].startswith(pr.GATE_B_WAVE_PREFIXES):
            assert entry["gate_b_value"]


def test_the_replay_command_refuses_a_wrong_labels_hash_and_prints_ids(tmp_path, capsys):
    S = fx.raw("selector_spec")
    ctx = pr.spec.context(S, "category", "C-full")

    def seed(j, u):
        return {"seed_index": j, "u_prompts": {f"p{i}": u for i in range(8)}, "o_prompts": {"o0": 0, "o1": 0},
                "l_rows": {"t0": 0.0}}
    labels = {"kind": pr.spec.LABELS_KIND, "version": pr.spec.LABELS_VERSION, "menu": "category",
              "samples_per_prompt": 3, "keep": {"samples_per_prompt": 3, "seeds": [seed(j, 0.5) for j in range(3)]},
              "options": {oid: {"coherent": True, "seeds": [seed(j, 0.5 - 0.02 * i) for j in range(6)]}
                          for i, oid in enumerate(ctx.menu.ids)}}
    path = tmp_path / "labels.json"
    path.write_bytes(canonical_json(labels))
    digest = sha256_bytes(path.read_bytes())
    assert pr.main(["replay", "--labels", str(path), "--labels-sha256", "0" * 64, "--menu", "category",
                    "--convention", "C-full", "--rule", "halving", "--budget", "8"]) == 2
    assert pr.main(["replay", "--labels", str(path), "--labels-sha256", digest, "--menu", "category",
                    "--convention", "C-full", "--rule", "halving", "--budget", "8"]) == 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["pick_by_tau_o"]["5"] in ctx.menu.ids and out["spent"] <= 8.0


def test_predict_refuses_a_non_empty_output_folder(tmp_path):
    (tmp_path / "old.txt").write_text("x")
    assert pr.main(["predict", "--out", str(tmp_path)]) == 2
