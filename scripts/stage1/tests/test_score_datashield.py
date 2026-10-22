"""REQ-12: DataShield-style, from REQ-3's CAS and CSS (the engine's fixture pass and synthetic rows); T1's scorer
contract."""

from __future__ import annotations

import copy
import json

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1 import score_datashield as ds
from scripts.stage1 import write_score_edit as wse

import s1fixtures as fx

torch = pytest.importorskip("torch")
import test_representation_pass as trp  # noqa: E402

env = trp.env


def settings(**pins):
    s = copy.deepcopy(json.loads(ds.SETTINGS_PATH.read_bytes()))
    s["pins"].update(pins)
    return s


def test_the_index_rule():
    assert ds.choose_index([0.99, 0.2, None, 0.5, 0.5]) == 3                    # index 0 excluded; ties to the lower
    assert ds.choose_index([0.1, None, 0.7, 0.2]) == 2
    with pytest.raises(s1.Refusal, match="no index"):
        ds.choose_index([0.5, None, None])


def test_css_at_l_hat_from_a_real_req3_pass(env):
    files = trp.run(env)
    summary = json.loads(files[rp_summary()])
    cas = summary["datashield"]["cas"]
    assert all(0.0 <= c <= 1.0 for c in cas if c is not None)
    scores, index = ds.scores_from(files[rp_rows()], sha256_bytes(files[rp_rows()]), summary,
                                   settings(representation_pass_settings_sha256="e" * 64))
    assert index == ds.choose_index(cas)
    for line in map(json.loads, files[rp_rows()].splitlines()):
        assert scores[line["id"]] == line["css"][index]


def rp_rows():
    from scripts.stage1 import representation_pass as rp
    return rp.ROWS_FILE


def rp_summary():
    from scripts.stage1 import representation_pass as rp
    return rp.SUMMARY_FILE


def test_css_does_not_change_when_v_is_doubled_before_normalization():
    torch.manual_seed(3)
    c, d, v = torch.randn(16, dtype=torch.float64), torch.randn(16, dtype=torch.float64), torch.randn(16, dtype=torch.float64)
    one = float(torch.dot(c - d, v / v.norm()))
    two = float(torch.dot(c - d, (2 * v) / (2 * v).norm()))
    assert one == pytest.approx(two, rel=1e-15) and float((v / v.norm()).norm()) == pytest.approx(1.0, rel=1e-15)


def test_the_scorer_output_is_t1s_contract(tmp_path):
    prep = fx.make_prepared(tmp_path / "p", units=8, rows_per_unit=6)
    view = s1.PreparedView(tmp_path / "p", prep["manifest_sha256"])
    n = 3
    lines = [{"id": r, "source": "dev", "css": [None, 0.1 * k, -0.2 * k, 0.05 * k]} for k, r in enumerate(sorted(view.tokens))]
    rows = b"".join(json.dumps(l, sort_keys=True).encode() + b"\n" for l in lines)
    rp_path = tmp_path / "rows.jsonl"
    rp_path.write_bytes(rows)
    pin = json.loads(ds.SETTINGS_PATH.read_bytes())["pins"]["representation_pass_settings_sha256"]
    summary = {"kind": "stage1 representation pass", "layout": {"n_layers": n}, "costs": {},
               "rows": {"sha256": sha256_bytes(rows)}, "provenance": {"settings_sha256": pin},
               "datashield": {"cas": [0.9, 0.4, 0.4, 0.1]}}
    sp = tmp_path / "summary.json"
    sp.write_bytes(canonical_json(summary))
    s = settings(prepared_manifest_sha256=prep["manifest_sha256"])
    files = ds.build(prepared_root=tmp_path / "p", rows=(rp_path, sha256_file(rp_path)), summary=(sp, sha256_file(sp)),
                     settings=s, settings_sha256="e" * 64)
    out = tmp_path / "ds.json"
    out.write_bytes(files[ds.OUTPUT])
    scores, source = wse.read_scorer_output(out, sha256_file(out), "datashield", json.loads(wse.SETTINGS_PATH.read_bytes()), view)
    assert source["provenance"]["l_hat"] == 1 and scores[sorted(view.tokens)[2]] == pytest.approx(0.2)
    s["pins"]["representation_pass_settings_sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="pinned REQ-3 settings"):
        ds.build(prepared_root=tmp_path / "p", rows=(rp_path, sha256_file(rp_path)), summary=(sp, sha256_file(sp)),
                 settings=s, settings_sha256="e" * 64)


def test_the_committed_settings():
    from scripts.stage1 import representation_pass as rp
    doc, digest = s1.load_settings(ds.SETTINGS_PATH, ds.SETTINGS_SHA256, ds.SETTINGS_NAME)
    assert doc["pins"]["representation_pass_settings_sha256"] == rp.SETTINGS_SHA256
    assert doc["scorer_output"]["orientation"] == json.loads(wse.SETTINGS_PATH.read_bytes())["scorers"]["datashield"]["orientation"]
