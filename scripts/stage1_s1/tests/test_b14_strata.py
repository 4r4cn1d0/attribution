"""B14 part 2a, the sealed split (standard library; synthetic similarity records only)."""

from __future__ import annotations

import json

import pytest

import b14_fixtures as bf

from experiments.safety_selection.common import sha256_bytes
from scripts.stage1 import s1common as s1
from scripts.stage1_s1 import overlap_strata as st


def ids(n: int) -> list[str]:
    return [f"p{i:02d}" for i in range(n)]


def test_an_even_bank_without_ties_splits_into_exact_halves():
    values = {pid: v for pid, v in zip(ids(6), [0.30, 0.10, 0.60, 0.20, 0.50, 0.40])}
    out = st.split_halves(values)
    assert out["lower"] == ["p00", "p01", "p03"] and out["higher"] == ["p02", "p04", "p05"]
    assert (out["n"], out["k"], out["lower_n"], out["higher_n"], out["ties_at_boundary"]) == (6, 3, 3, 3, 1)
    assert out["boundary"] == 0.40 and out["lower_max"] == 0.30 and out["higher_min"] == 0.40


def test_an_odd_bank_puts_the_median_prompt_in_the_higher_half():
    out = st.split_halves(dict(zip(ids(5), [0.5, 0.1, 0.4, 0.2, 0.3])))
    assert out["lower"] == ["p01", "p03"] and out["higher"] == ["p00", "p02", "p04"]


def test_boundary_ties_all_go_to_the_higher_half():
    # sorted: 0.1 0.2 [0.3 0.3 0.3] 0.9; k = 3, b = the 4th smallest = 0.3
    out = st.split_halves(dict(zip(ids(6), [0.3, 0.1, 0.3, 0.9, 0.2, 0.3])))
    assert out["lower"] == ["p01", "p04"] and out["higher"] == ["p00", "p02", "p03", "p05"]
    assert out["ties_at_boundary"] == 3 and out["lower_n"] == 2 < out["k"] == 3
    assert out["lower_max"] < out["higher_min"]


def test_ties_below_the_boundary_stay_low():
    out = st.split_halves(dict(zip(ids(4), [0.1, 0.1, 0.2, 0.3])))
    assert out["lower"] == ["p00", "p01"] and out["ties_at_boundary"] == 1


def test_an_all_equal_bank_has_an_empty_lower_half():
    out = st.split_halves(dict(zip(ids(4), [0.5] * 4)))
    assert out["lower"] == [] and out["higher"] == ids(4) and out["lower_max"] is None


def test_the_split_draws_nothing_and_does_not_depend_on_the_ids():
    values = [0.3, 0.1, 0.6, 0.2]
    a = st.split_halves(dict(zip(["a", "b", "c", "d"], values)))
    b = st.split_halves(dict(zip(["z", "y", "x", "w"], values)))
    assert [values[["a", "b", "c", "d"].index(p)] for p in a["lower"]] == sorted(
        values[["z", "y", "x", "w"].index(p)] for p in b["lower"])


@pytest.mark.parametrize("bad", [{"p": 0.1}, {"p": 0.1, "q": float("nan")}, {"p": 0.1, "q": float("inf")},
                                 {"p": 0.1, "q": True}, {}])
def test_bad_values_refuse(bad):
    with pytest.raises(s1.Refusal):
        st.split_halves(bad)


def record(values=None, **kw) -> bytes:
    values = values or {"S1": dict(zip(ids(6), [0.3, 0.1, 0.6, 0.2, 0.5, 0.4])),
                        "S3": dict(zip(ids(6), [0.6, 0.5, 0.4, 0.3, 0.2, 0.1]))}
    return bf.similarity_record(values, **kw)


def test_strata_from_a_similarity_record():
    settings, digest = bf.strata_settings()
    data = record()
    out = s1.strict_json(st.strata(data, sha256_bytes(data), settings, digest))
    assert out["kind"] == "stage1 overlap strata" and out["similarity"]["sha256"] == sha256_bytes(data)
    assert out["add_sets"]["S1"]["lower"] == ["p00", "p01", "p03"]
    assert out["add_sets"]["S3"]["lower"] == ["p03", "p04", "p05"]
    assert out["prompt_ids"] == ids(6)
    assert out["provenance"]["settings_sha256"] == digest and out["provenance"]["label_entries"] == {}
    assert st.strata(data, sha256_bytes(data), settings, digest) == st.strata(data, sha256_bytes(data), settings, digest)


def test_a_record_that_is_not_the_pinned_bytes_refuses():
    settings, digest = bf.strata_settings()
    data = record()
    with pytest.raises(s1.Refusal, match="hashes to"):
        st.strata(data, "3" * 64, settings, digest)


def test_a_record_made_under_other_similarity_settings_refuses():
    settings, digest = bf.strata_settings()
    data = record(settings_sha256="4" * 64)
    with pytest.raises(s1.Refusal, match="made under settings"):
        st.strata(data, sha256_bytes(data), settings, digest)


@pytest.mark.parametrize("damage", ["kind", "missing_prompt", "nan", "nearest", "arm", "cosine_range"])
def test_a_damaged_record_refuses(damage):
    settings, digest = bf.strata_settings()
    doc = json.loads(record())
    s = doc["add_sets"]["S1"]
    if damage == "kind":
        doc["kind"] = "other"
    elif damage == "missing_prompt":
        del s["per_prompt"]["p02"]
    elif damage == "nan":
        s["per_prompt"]["p02"]["s_max"] = "nan"
    elif damage == "nearest":
        s["per_prompt"]["p02"]["nearest"] = "add-zz"
    elif damage == "arm":
        s["arm"] = "edit-" + "9" * 64
    elif damage == "cosine_range":
        s["per_prompt"]["p02"]["s_max"] = 1.5
    data = json.dumps(doc).encode()
    with pytest.raises(s1.Refusal):
        st.strata(data, sha256_bytes(data), settings, digest)


def test_the_strata_command_writes_once(tmp_path, capsys):
    data = record()
    sim_path = tmp_path / "similarity.json"
    sim_path.write_bytes(data)
    out = tmp_path / "strata"
    argv = ["strata", "--similarity", str(sim_path), "--similarity-sha256", sha256_bytes(data), "--out", str(out)]
    assert st.main(argv) == 0
    written = (out / st.STRATA_FILE).read_bytes()
    assert s1.strict_json(written)["add_sets"]["S1"]["lower_n"] == 3
    assert st.main(argv) == 2                                     # a sealed output never overwrites
    assert (out / st.STRATA_FILE).read_bytes() == written
    assert "REFUSED" in capsys.readouterr().err
