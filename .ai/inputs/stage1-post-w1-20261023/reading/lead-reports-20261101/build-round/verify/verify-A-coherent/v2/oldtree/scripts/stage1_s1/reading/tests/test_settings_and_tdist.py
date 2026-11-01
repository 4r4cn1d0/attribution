"""The settings pin (a SHA-256 literal), the sealed designs, and the Student t helpers against table values."""

from __future__ import annotations

import hashlib
import json
import math

import pytest

from scripts.stage1_s1.reading import settings as st
from scripts.stage1_s1.reading import tdist


def test_the_settings_literal_pins_the_file():
    data = st.SETTINGS_PATH.read_bytes()
    assert hashlib.sha256(data).hexdigest() == st.SETTINGS_SHA256
    doc = st.load_settings()
    assert doc["kind"] == "stage1 reading settings" and doc["version"] == 1


def test_a_changed_byte_or_a_wrong_pin_refuses(tmp_path):
    data = st.SETTINGS_PATH.read_bytes()
    changed = tmp_path / "reading.json"
    changed.write_bytes(data.replace(b'"delta_pp": 5.0', b'"delta_pp": 4.0'))
    with pytest.raises(st.Refusal):
        st.load_settings(changed)
    with pytest.raises(st.Refusal):
        st.load_settings(st.SETTINGS_PATH, "0" * 64)


def test_non_canonical_bytes_with_a_matching_pin_still_need_canonical_form(tmp_path):
    doc = json.loads(st.SETTINGS_PATH.read_bytes())
    loose = (json.dumps(doc) + "\n").encode()
    path = tmp_path / "loose.json"
    path.write_bytes(loose)
    with pytest.raises(st.Refusal):
        st.load_settings(path, hashlib.sha256(loose).hexdigest())


def test_the_constants_are_the_pre_registered_ones():
    cfg = st.settings()
    assert cfg["tau_l"]["nats"] == 0.0067170919092681925
    assert cfg["tau_l"]["nats"] == pytest.approx(2 * math.sqrt(2) * cfg["tau_l"]["s_ddof1"], rel=1e-15)
    assert cfg["tau_o"]["star_pp"] == 5.0 and cfg["tau_o"]["grid_pp"] == [2.0, 5.0, 10.0]
    assert cfg["margin"]["delta_pp"] == 5.0
    assert cfg["endpoints"]["U"]["floor"] == 0.01 and cfg["endpoints"]["O"]["floor"] == 0.01
    assert cfg["endpoints"]["L"]["floor"] == 1e-8
    assert cfg["reml"]["tol"] == 1e-6 and cfg["reml"]["max_iter"] == 25
    assert cfg["endpoints"]["U"]["items"] == 200 and cfg["endpoints"]["O"]["items"] == 500 and cfg["endpoints"]["L"]["items"] == 200
    assert cfg["beats"]["lambda_grid"] == [1.0, 0.9, 0.75, 0.5, 0.0] and cfg["beats"]["m_o_pp"] == 5.0


def test_plan_a_design_is_d1():
    d = st.design("plan_a")
    assert d.seeds["a0"] == tuple(range(1101, 1108)) and d.seeds["R"] == tuple(range(1101, 1108))
    for m in ("A1", "L1", "H1", "S1", "S3", "S4"):
        assert d.seeds[m] == tuple(range(1102, 1108))
    assert sum(len(s) for s in d.seeds.values()) == 50
    assert [c[0] for c in d.contrasts] == ["P1", "P2", "P3", "P4", "P5", "P6"]
    assert d.contrasts[3] == ("P4", "a0", "S1") and d.contrasts[0] == ("P1", "R", "A1")
    assert d.cluster_arms("full") == ("a0", "S1", "S3", "S4") and d.cluster_arms("removal") == ("R", "A1", "L1", "H1")
    assert d.familywise_sides == 6 and d.label_suffix is None
    assert all(d.common_seeds(c, m) == tuple(range(1102, 1108)) for _, c, m in d.contrasts)


def test_block_a_only_and_plan_b_designs():
    a = st.design("plan_a_block_a_only")
    assert a.seeds["a0"] == tuple(range(1101, 1105)) and a.seeds["S1"] == (1102, 1103, 1104)
    assert a.label_suffix == "block A only (3 seeds per method arm)"
    b = st.design("plan_b")
    assert [c[0] for c in b.contrasts] == ["P1", "P3", "P6"]
    assert set(b.fit_arms) == {"R", "A1", "H1", "S1", "S4"} and "a0" in b.arms and not b.in_fit("a0")
    assert b.seeds["R"] == tuple(range(1101, 1111)) and b.seeds["S4"] == tuple(range(1102, 1111))
    assert b.seeds["a0"] == tuple(range(1101, 1108)) and b.familywise_sides == 3
    assert b.cluster_arms("full") == ("S1", "S4")
    with pytest.raises(st.Refusal):
        st.design("plan_c")


def test_module_hashes_cover_every_module():
    h = st.module_hashes()
    for name in ("reml.py", "contrast.py", "phi.py", "labels.py", "reading.py", "schema.py", "settings.py", "settings/reading.json"):
        assert name in h and len(h[name]) == 64


@pytest.mark.parametrize("p, df, value", [(0.95, 5, 2.015048), (0.99625, 5, 4.330), (1 - 0.00135, 5, 5.507),
                                          (1 - 0.000417, 5, 7.145), (0.975, 1e6, 1.959964), (0.9, 2, 1.885618),
                                          (0.95, 42, 1.681952), (0.8, 8, 0.889148)])
def test_t_quantiles_against_tables(p, df, value):
    assert tdist.t_quantile(p, df) == pytest.approx(value, abs=6e-4)


def test_t_tail_and_quantile_invert_and_are_symmetric():
    for df in (2.0, 5.5, 36.0, 1000.0):
        for p in (0.6, 0.95, 0.99625, 0.999):
            q = tdist.t_quantile(p, df)
            assert tdist.t_sf(q, df) == pytest.approx(1 - p, rel=1e-7, abs=1e-12)
            assert tdist.t_quantile(1 - p, df) == pytest.approx(-q)
            assert tdist.t_two_sided(q, df) == pytest.approx(2 * (1 - p), rel=1e-7)
    assert tdist.t_cdf(0.0, 7) == 0.5 and tdist.t_two_sided(0.0, 7) == 1.0


def test_betainc_identities():
    for a, b, x in ((0.5, 2.5, 0.3), (3.0, 0.5, 0.9), (2.0, 2.0, 0.5)):
        assert tdist.betainc(a, b, x) + tdist.betainc(b, a, 1 - x) == pytest.approx(1.0, abs=1e-12)
    assert tdist.betainc(2.0, 2.0, 0.5) == pytest.approx(0.5)
    assert tdist.betainc(1.0, 1.0, 0.25) == pytest.approx(0.25)
    assert tdist.betainc(1.0, 1.0, 0.0) == 0.0 and tdist.betainc(1.0, 1.0, 1.0) == 1.0


def test_welch_df_hand_cases():
    assert tdist.welch_df(4.0, 6, 4.0, 6) == pytest.approx(10.0)
    assert tdist.welch_df(1.0, 7, 9.0, 6) == pytest.approx((1 / 7 + 9 / 6) ** 2 / ((1 / 7) ** 2 / 6 + (9 / 6) ** 2 / 5))


def test_bad_df_or_p_refuse():
    with pytest.raises(ValueError):
        tdist.t_quantile(1.0, 5)
    with pytest.raises(ValueError):
        tdist.t_sf(1.0, 0)
