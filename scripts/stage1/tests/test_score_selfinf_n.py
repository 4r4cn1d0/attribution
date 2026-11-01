"""REQ-13: Self-Inf-N-style on T1's synthetic attributes unit (equal grad_norm in both anchor sets, as in real data)."""

from __future__ import annotations

import copy
import json
import math

import pytest

from experiments.safety_selection.common import sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1 import score_selfinf_n as si
from scripts.stage1 import write_score_edit as wse

import s1fixtures as fx


def equal_norm_values(members, seed=11):
    values = fx.random_values(members, seed)
    for rid in values:
        for c in ("q", "e1"):
            values[rid][c]["safe"]["grad_norm"] = values[rid][c]["harmful"]["grad_norm"]
    return values


@pytest.fixture()
def unit(tmp_path):
    prepared = fx.make_prepared(tmp_path / "prepared")
    values = equal_norm_values(prepared["members"])
    unit_cfg = fx.real_settings()["a1"]["attributes_unit"]
    complete = fx.make_unit(tmp_path / "unit", prepared, values, unit_cfg)
    return {"prepared": prepared, "values": values, "unit": tmp_path / "unit",
            "wse": (fx.a1_settings_for(prepared, complete), "e" * 64)}


def build(u, settings=None):
    files = si.build(prepared_root=u["prepared"]["root"], unit_dir=u["unit"], settings=settings or json.loads(si.SETTINGS_PATH.read_bytes()),
                     settings_sha256="e" * 64, wse_settings=u["wse"])
    return json.loads(files[si.OUTPUT]), json.loads(files[si.SENSITIVITIES]), files


def test_the_score_by_hand(unit):
    doc, sens, _ = build(unit)
    view = s1.PreparedView(unit["prepared"]["root"], unit["prepared"]["manifest_sha256"])
    for rid in list(view.tokens)[:50]:
        g = unit["values"][rid]["q"]["harmful"]["grad_norm"]
        assert doc["scores"][rid] == pytest.approx(math.log(g * g + 1) + math.log(view.tokens[rid] - 1 + 1))
        g1 = unit["values"][rid]["e1"]["harmful"]["grad_norm"]
        assert sens["variants"]["e1"]["scores"][rid] == pytest.approx(math.log(g1 * g1 + 1) + math.log(view.tokens[rid]))
        assert sens["variants"]["q_plus_e1"]["scores"][rid] == pytest.approx(math.log(g * g + g1 * g1 + 1) + math.log(view.tokens[rid]))
    assert len(doc["scores"]) == 4800 and sens["report_only"] is True
    assert 0.0 <= sens["variants"]["e1"]["top_k_jaccard_with_primary"] <= 1.0


def test_the_scorer_output_is_t1s_contract_with_both_costs(unit, tmp_path):
    doc, _, files = build(unit)
    out = tmp_path / "si.json"
    out.write_bytes(files[si.OUTPUT])
    view = s1.PreparedView(unit["prepared"]["root"], unit["prepared"]["manifest_sha256"])
    scores, source = wse.read_scorer_output(out, sha256_file(out), "selfinf_n", unit["wse"][0], view)
    assert len(scores) == 4800
    assert source["costs"]["marginal_usd"] == 0.0 and source["costs"]["full_charge"]["gradient_passes"] == 1


def test_unequal_grad_norms_refuse(tmp_path):
    prepared = fx.make_prepared(tmp_path / "prepared")
    values = equal_norm_values(prepared["members"])
    first = sorted(values)[7]
    values[first]["q"]["safe"]["grad_norm"] += 0.25
    unit_cfg = fx.real_settings()["a1"]["attributes_unit"]
    complete = fx.make_unit(tmp_path / "unit", prepared, values, unit_cfg)
    with pytest.raises(s1.Refusal, match="grad_norm differs"):
        si.build(prepared_root=prepared["root"], unit_dir=tmp_path / "unit", settings=json.loads(si.SETTINGS_PATH.read_bytes()),
                 settings_sha256="e" * 64, wse_settings=(fx.a1_settings_for(prepared, complete), "e" * 64))


def test_the_unit_is_checked_by_t1(unit):
    s, digest = unit["wse"]
    bad = copy.deepcopy(s)
    bad["a1"]["attributes_unit"]["complete_sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="COMPLETE.json hashes to"):
        si.build(prepared_root=unit["prepared"]["root"], unit_dir=unit["unit"], settings=json.loads(si.SETTINGS_PATH.read_bytes()),
                 settings_sha256="e" * 64, wse_settings=(bad, digest))


def test_deterministic(unit):
    assert build(unit)[2] == build(unit)[2]


def test_the_committed_settings():
    doc, digest = s1.load_settings(si.SETTINGS_PATH, si.SETTINGS_SHA256, si.SETTINGS_NAME)
    assert (doc["primary"], doc["k"], doc["checkpoints"]) == ("q", 600, ["q", "e1"]) and doc["label_entries"] == {}
