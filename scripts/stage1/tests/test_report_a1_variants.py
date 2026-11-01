"""W1-04: the A1 report-only variants (q-only, e1-only, V1 Adam-preconditioned), on T1's synthetic attributes units."""

from __future__ import annotations

import copy
import json
import random

import numpy
import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1 import report_a1_variants as rav
from scripts.stage1 import write_score_edit as wse

import s1fixtures as fx
from test_t1_pins import WRITE_SCORE_EDIT_SHA256


def settings() -> dict:
    return json.loads(rav.SETTINGS_PATH.read_bytes())


def report(fix: dict, comparisons=()) -> dict:
    files = rav.build_report(fix["prepared"]["root"], fix["unit"], settings(), "d" * 64, fix["settings"], "f" * 64,
                             list(comparisons))
    assert list(files) == ["a1_variants.json"]
    return json.loads(files["a1_variants.json"])


def numpy_spearman(x: dict, y: dict) -> float:
    """An independent Spearman ρ: numpy, ties averaged through unique/inverse counts."""
    keys = sorted(x)
    def ranks(values):
        a = numpy.array(values, dtype=float)
        uniq, inverse, counts = numpy.unique(a, return_inverse=True, return_counts=True)
        start = numpy.concatenate(([0], numpy.cumsum(counts)[:-1]))
        return (start + (counts + 1) / 2)[inverse]
    return float(numpy.corrcoef(ranks([x[k] for k in keys]), ranks([y[k] for k in keys]))[0, 1])


def reference(values: dict, field: str, checkpoints: list[str]) -> dict:
    return {r: sum(v[c]["harmful"][field] - v[c]["safe"][field] for c in checkpoints) / len(checkpoints)
            for r, v in values.items()}


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    return fx.build_fixture(tmp_path_factory.mktemp("rav"))


def base_report(base: dict) -> dict:
    if "report" not in base:
        base["report"] = report(base)
    return base["report"]


# ----- statistics -----------------------------------------------------------------------------------


def test_average_ranks_spearman_and_jaccard_by_hand():
    assert rav.average_ranks({"a": 3.0, "b": 1.0, "c": 3.0, "d": 2.0}) == {"b": 1.0, "d": 2.0, "a": 3.5, "c": 3.5}
    assert rav.spearman({"a": 1, "b": 2, "c": 3}, {"a": 30, "b": 20, "c": 10}) == pytest.approx(-1.0)
    x, y = {"a": 1.0, "b": 2.0, "c": 2.0, "d": 4.0}, {"a": 1.0, "b": 3.0, "c": 2.0, "d": 4.0}
    assert rav.spearman(x, y) == pytest.approx(numpy_spearman(x, y)) == pytest.approx(0.9486832980505138)
    assert rav.jaccard(["a", "b", "c"], ["b", "c", "d", "e"]) == 2 / 5
    assert rav.spearman({"a": 1.0, "b": 1.0}, {"a": 1.0, "b": 2.0}) is None
    with pytest.raises(s1.Refusal):
        rav.spearman({"a": 1.0, "b": 2.0}, {"a": 1.0, "c": 2.0})


# ----- the report on the base fixture ---------------------------------------------------------------


def test_stability_equals_an_independent_computation(base):
    rec = base_report(base)
    q, e1 = reference(base["values"], "cosine", ["q"]), reference(base["values"], "cosine", ["e1"])
    assert rec["stability"]["spearman_q_e1"] == pytest.approx(numpy_spearman(q, e1), abs=1e-12)
    top_q = sorted(q, key=lambda r: -q[r])[:600]
    top_e1 = sorted(e1, key=lambda r: -e1[r])[:600]
    assert rec["top_sets"]["q"] == sorted(top_q) and rec["top_sets"]["e1"] == sorted(top_e1)
    assert rec["stability"]["jaccard_top_q_e1"] == len(set(top_q) & set(top_e1)) / len(set(top_q) | set(top_e1))
    assert all(len(s) == 600 for s in rec["top_sets"].values())


def test_the_mean_identity_holds_against_t1(base):
    rec = base_report(base)
    unit = wse.check_attributes_unit(base["unit"], base["settings"]["a1"]["attributes_unit"],
                                     wse.view_of(base["prepared"]["root"], base["settings"]))
    view = wse.view_of(base["prepared"]["root"], base["settings"])
    t1 = wse.a1_scores(unit["bytes"]["rows.jsonl"], base["settings"]["a1"], view)
    values = rav.variant_values(unit["bytes"]["rows.jsonl"], base["settings"]["a1"], view)
    scores = rav.variant_scores(values, settings()["report"]["variants"])
    assert all((scores["q"][r] + scores["e1"][r]) / 2 == t1[r] for r in t1)               # exact, not only 1e-12
    assert rec["stability"]["mean_identity_max_abs_difference"] == 0.0


def test_v1_reads_only_adam_score(base, tmp_path):
    rec = base_report(base)
    adam = reference(base["values"], "adam_score", ["q", "e1"])
    assert rec["top_sets"]["adam"] == sorted(sorted(adam, key=lambda r: -adam[r])[:600])
    values = copy.deepcopy(base["values"])
    rng = random.Random(5)
    for v in values.values():                               # other cosines, the same adam scores
        for c in ("q", "e1"):
            for s in ("harmful", "safe"):
                v[c][s]["cosine"] = rng.uniform(-0.2, 0.2)
    other = report(fx.build_fixture(tmp_path / "f", values=values))
    assert other["top_sets"]["adam"] == rec["top_sets"]["adam"]
    assert other["top_sets"]["q"] != rec["top_sets"]["q"]


def test_v1_unit_means_spearman_and_jaccards(base):
    rec = base_report(base)
    adam = reference(base["values"], "adam_score", ["q", "e1"])
    a1 = reference(base["values"], "cosine", ["q", "e1"])
    members = base["prepared"]["members"]
    um = lambda s: {u: sum(s[r] for r in members[u]) / len(members[u]) for u in members}
    assert rec["adam_preconditioned_v1"]["spearman_unit_means_with_a1"] == pytest.approx(numpy_spearman(um(adam), um(a1)))
    a1_set = rec["jaccard_matrix"]["names"]
    assert "a1" in a1_set and rec["adam_preconditioned_v1"]["jaccard_top_with"]["a1"] == rec["jaccard_matrix"]["jaccard"]["adam"]["a1"]
    assert "LESS" not in rec["adam_preconditioned_v1"]["name"].replace("never called LESS", "")


def test_ties_follow_the_variant_part_of_the_label(tmp_path, base):
    values = copy.deepcopy(base["values"])
    for v in values.values():                               # every a^q is equal; e1 keeps its spread
        v["q"]["harmful"]["cosine"], v["q"]["safe"]["cosine"] = 0.25, 0.125
    rec = report(fx.build_fixture(tmp_path / "f", values=values))
    rows = sorted(values)
    assert rec["top_sets"]["q"] == sorted(s1.sealed_order(rows, "a1_variants.ties", "q")[:600])
    assert rec["top_sets"]["q"] != sorted(s1.sealed_order(rows, "a1_variants.ties", "e1")[:600])
    assert rec["boundary"]["q"] == {"kth_score": 0.125, "tied_selected": 600, "tied_not_selected": 4200}
    assert rec["stability"]["spearman_q_e1"] is None                       # a^q is constant: undefined, not a refusal
    for v in values.values():                               # now every a^e1 is equal too
        v["e1"]["harmful"]["cosine"], v["e1"]["safe"]["cosine"] = 0.5, 0.25
    rec = report(fx.build_fixture(tmp_path / "g", values=values))
    assert rec["top_sets"]["e1"] == sorted(s1.sealed_order(rows, "a1_variants.ties", "e1")[:600])
    assert rec["top_sets"]["e1"] != rec["top_sets"]["q"]


def test_the_mean_identity_guard_refuses_a_diverging_t1_score(base, monkeypatch):
    real = wse.build_a1

    def diverging(*args):
        files = real(*args)
        rec = json.loads(files["a1_selection.json"])
        row = sorted(rec["scores"])[17]
        rec["scores"][row] += 1e-9
        return {**files, "a1_selection.json": canonical_json(rec)}
    monkeypatch.setattr(rav.wse, "build_a1", diverging)
    with pytest.raises(s1.Refusal, match="differs from T1's a_i"):
        report(base)


def test_comparisons_selection_record_and_edit_file(base, tmp_path):
    a1_files = wse.build_a1(base["prepared"]["root"], base["unit"], base["settings"], "f" * 64)
    edit = tmp_path / "a1.edit.json"
    edit.write_bytes(a1_files["a1_remove600.edit.json"])
    sel = tmp_path / "a1_selection.json"
    sel.write_bytes(a1_files["a1_selection.json"])
    rec = report(base, [f"a1edit={edit}:{sha256_file(edit)}", f"a1sel={sel}:{sha256_file(sel)}"])
    jm = rec["jaccard_matrix"]["jaccard"]
    assert jm["a1edit"]["a1"] == 1.0 and jm["a1sel"]["a1"] == 1.0
    assert rec["comparisons"]["a1edit"]["kind"] == "edit file" and rec["comparisons"]["a1sel"]["kind"] == "selection record"
    with pytest.raises(s1.Refusal, match="hashes to"):
        report(base, [f"x={edit}:{'0' * 64}"])
    bad = tmp_path / "bad.json"
    bad.write_bytes(canonical_json({"selected": ["r-not-a-row"]}))
    with pytest.raises(s1.Refusal, match="not distinct training rows"):
        report(base, [f"x={bad}:{sha256_file(bad)}"])
    with pytest.raises(s1.Refusal, match="NAME=PATH:SHA256"):
        report(base, ["no-equals-sign"])


# ----- refusals -------------------------------------------------------------------------------------


def _drop_e1(rows):
    rows[0]["per_checkpoint"].pop("e1")


@pytest.mark.parametrize("kwargs,match", [
    ({"rows_edit": _drop_e1}, "checkpoints are not"),
    ({"identity_changes": {"code_sha256": "0" * 64}}, "fails the checks"),
    ({"identity_changes": {"recipe_sha256": "0" * 64}}, "fails the checks"),
    ({"job_changes": {"query_bank": "anchors-" + "0" * 64}}, "fails the checks"),
])
def test_the_input_checks_refuse(tmp_path, base, kwargs, match):
    with pytest.raises(s1.Refusal, match=match):
        report(fx.build_fixture(tmp_path / "f", values=base["values"], **kwargs))


def _shift_q_cosine(doc):
    unit = sorted(doc["groups"])[1]
    doc["groups"][unit]["harmful"]["per_checkpoint"]["q"]["mean_cosine"] += 1e-9


def _shift_e1_adam(doc):
    unit = sorted(doc["groups"])[4]
    doc["groups"][unit]["safe"]["per_checkpoint"]["e1"]["adam_sum"] += 1.0


def _swap_q_e1(doc):
    for unit in doc["groups"].values():
        for s in ("harmful", "safe"):
            pc = unit[s]["per_checkpoint"]
            pc["q"], pc["e1"] = pc["e1"], pc["q"]


@pytest.mark.parametrize("groups_edit,match", [(_shift_q_cosine, "mean cosine difference"),
                                               (_shift_e1_adam, "adam sum"), (_swap_q_e1, "mean cosine difference")])
def test_the_groups_guards_refuse(tmp_path, base, groups_edit, match):
    with pytest.raises(s1.Refusal, match=match):
        report(fx.build_fixture(tmp_path / "f", values=base["values"], groups_edit=groups_edit))


# ----- outputs and settings -------------------------------------------------------------------------


def test_deterministic_text_free_and_report_only(base):
    first = rav.build_report(base["prepared"]["root"], base["unit"], settings(), "d" * 64, base["settings"], "f" * 64)
    again = rav.build_report(base["prepared"]["root"], base["unit"], settings(), "d" * 64, base["settings"], "f" * 64)
    assert first == again
    data = first["a1_variants.json"]
    for text in base["prepared"]["texts"][::97]:
        assert text.encode() not in data
    rec = json.loads(data)
    assert rec["role"].startswith("report only") and "edit" not in " ".join(first)
    assert rec["provenance"]["label_entries"] == {"a1_variants.ties": s1.entry_digest("a1_variants.ties")}


def test_the_settings_are_pinned_and_name_the_t1_settings():
    data = rav.SETTINGS_PATH.read_bytes()
    assert sha256_bytes(data) == rav.SETTINGS_SHA256 == "d6979c9785b4d312147c2ff53fb834a02f65035428629019bcc0a0c7faeee5c6"
    doc = s1.check_settings(json.loads(data), "report_a1_variants")
    assert doc["a1_settings"]["sha256"] == WRITE_SCORE_EDIT_SHA256 == wse.SETTINGS_SHA256
    assert doc["a1_settings"]["path"] == "scripts/stage1/settings/write_score_edit.json"
    r = doc["report"]
    assert (r["k"], r["ties"], r["mean_identity_tolerance"]) == (600, "a1_variants.ties", 1e-12)
    assert r["variants"]["q"] == {"field": "cosine", "checkpoints": ["q"], "name": r["variants"]["q"]["name"]}
    assert r["variants"]["e1"]["checkpoints"] == ["e1"] and r["variants"]["adam"]["field"] == "adam_score"
    assert r["variants"]["adam"]["checkpoints"] == ["q", "e1"]


def test_the_command_refuses_a_settings_file_with_another_hash(tmp_path, capsys):
    changed = tmp_path / "s.json"
    changed.write_bytes(rav.SETTINGS_PATH.read_bytes().replace(b'"k": 600', b'"k": 599', 1))
    code = rav.main(["--prepared", str(tmp_path), "--unit", str(tmp_path), "--out", str(tmp_path / "o"),
                     "--settings", str(changed)])
    err = capsys.readouterr().err
    assert code == 2 and "hash to" in err and not (tmp_path / "o").exists()


# ----- revision 2: the verifiers' gap tests (folded in from tmp/gi-vi-stage1/b1-fix/test_gaps_plus_fix.py, 34037bec)


def test_gap_a1_jaccards_and_boundaries_and_unit_means(base):
    rec = base_report(base)
    a1_set = set(json.loads(wse.build_a1(base["prepared"]["root"], base["unit"], base["settings"], "f" * 64)
                            ["a1_selection.json"])["selected"])
    for name, field, cps in (("q", "cosine", ["q"]), ("e1", "cosine", ["e1"]), ("adam", "adam_score", ["q", "e1"])):
        sc = reference(base["values"], field, cps)
        top = set(rec["top_sets"][name])
        j = len(top & a1_set) / len(top | a1_set)
        if name != "adam":
            assert rec["stability"][f"jaccard_top_{name}_a1"] == j == rec["jaccard_matrix"]["jaccard"][name]["a1"]
        else:
            assert rec["adam_preconditioned_v1"]["jaccard_top_with"]["a1"] == j == rec["jaccard_matrix"]["jaccard"]["adam"]["a1"]
        kth = min(sc[r] for r in top)
        assert rec["boundary"][name] == {"kth_score": kth, "tied_selected": sum(sc[r] == kth for r in top),
                                         "tied_not_selected": sum(sc[r] == kth for r in sc if r not in top)}
    members = base["prepared"]["members"]
    for name, field, cps in (("q", "cosine", ["q"]), ("e1", "cosine", ["e1"]), ("adam", "adam_score", ["q", "e1"]),
                             ("a1", "cosine", ["q", "e1"])):
        sc = reference(base["values"], field, cps)
        for u in members:
            assert rec["unit_means"][name][u] == pytest.approx(sum(sc[r] for r in members[u]) / len(members[u]),
                                                               abs=1e-12)


@pytest.mark.parametrize("sign", [1, -1])
def test_gap_mean_identity_tolerance_boundary(base, monkeypatch, sign):
    real = wse.build_a1

    def shifted(delta):
        def f(*args):
            files = real(*args)
            rec = json.loads(files["a1_selection.json"])
            rec["scores"][sorted(rec["scores"])[17]] -= sign * delta
            return {**files, "a1_selection.json": canonical_json(rec)}
        return f
    monkeypatch.setattr(rav.wse, "build_a1", shifted(1e-11))
    with pytest.raises(s1.Refusal, match="differs from T1's a_i"):
        report(base)
    monkeypatch.setattr(rav.wse, "build_a1", shifted(1e-13))
    assert report(base)["stability"]["mean_identity_max_abs_difference"] <= 1e-12


def _shift(checkpoint, field, delta, unit_index=2):
    def edit(doc):
        unit = sorted(doc["groups"])[unit_index]
        doc["groups"][unit]["harmful"]["per_checkpoint"][checkpoint][field] += delta
    return edit


@pytest.mark.parametrize("checkpoint", ["q", "e1"])
def test_gap_cosine_guard_each_checkpoint_near_tolerance(tmp_path, base, checkpoint):
    with pytest.raises(s1.Refusal, match="mean cosine difference"):
        report(fx.build_fixture(tmp_path / "f", values=base["values"],
                                groups_edit=_shift(checkpoint, "mean_cosine", 1e-11)))


@pytest.mark.parametrize("checkpoint", ["q", "e1"])
def test_gap_adam_guard_each_checkpoint_near_tolerance(tmp_path, base, checkpoint):
    unit = sorted(base["prepared"]["members"])[2]
    scale = base_report(base)["groups_guards"][unit][checkpoint]["adam_scale"]
    with pytest.raises(s1.Refusal, match="adam sum"):
        report(fx.build_fixture(tmp_path / "f", values=base["values"],
                                groups_edit=_shift(checkpoint, "adam_sum", 20 * 1e-9 * scale)))


def test_gap_missing_rows_refuse_cleanly(tmp_path, base):
    with pytest.raises(s1.Refusal, match="misses 1 training rows"):
        report(fx.build_fixture(tmp_path / "f", values=base["values"], drop_rows=1))


def test_gap_comparison_names_and_ids(base, tmp_path):
    a1_files = wse.build_a1(base["prepared"]["root"], base["unit"], base["settings"], "f" * 64)
    sel = tmp_path / "a1_selection.json"
    sel.write_bytes(a1_files["a1_selection.json"])
    spec = f"x={sel}:{sha256_file(sel)}"
    with pytest.raises(s1.Refusal, match="share one name"):
        report(base, [spec, spec])
    rows = sorted(base["values"])
    dup = tmp_path / "dup.json"
    dup.write_bytes(canonical_json({"selected": [rows[0], rows[0], rows[1]]}))
    with pytest.raises(s1.Refusal, match="not distinct training rows"):
        report(base, [f"d={dup}:{sha256_file(dup)}"])


def test_gap_no_text_at_all(base):
    data = rav.build_report(base["prepared"]["root"], base["unit"], settings(), "d" * 64, base["settings"],
                            "f" * 64)["a1_variants.json"]
    assert s1._text_hits(data, base["prepared"]["texts"]) == 0              # every fixture text, not a sample


def test_gap_command_prints_counts_and_hashes_only(base, tmp_path, monkeypatch, capsys):
    import re

    real = rav.build_report

    def on_fixture(prepared, unit_dir, settings_doc, digest, a1_settings, a1_digest, comparisons):
        return real(base["prepared"]["root"], base["unit"], settings_doc, digest, base["settings"], a1_digest,
                    comparisons)
    monkeypatch.setattr(rav, "build_report", on_fixture)
    out = tmp_path / "o"
    code = rav.main(["--prepared", str(tmp_path), "--unit", str(tmp_path), "--out", str(out)])
    lines = capsys.readouterr().out.splitlines()
    assert code == 0 and sorted(p.name for p in out.iterdir()) == ["a1_variants.json"]
    assert lines[0] == f"wrote 1 file into {out}"
    assert len(lines) == 2 and re.fullmatch(r"  [0-9a-f]{64}  a1_variants\.json", lines[1])


@pytest.mark.parametrize("name", ["a1", "q", "e1", "adam", "", "A1", "x-y"])
def test_gap_comparison_names_reserved_or_not_ids_refuse(base, tmp_path, name):
    a1_files = wse.build_a1(base["prepared"]["root"], base["unit"], base["settings"], "f" * 64)
    sel = tmp_path / "a1_selection.json"
    sel.write_bytes(a1_files["a1_selection.json"])
    with pytest.raises(s1.Refusal, match="reserved"):
        report(base, [f"{name}={sel}:{sha256_file(sel)}"])


def test_gap_missing_comparison_file_refuses(base, tmp_path):
    with pytest.raises(s1.Refusal, match="cannot be read"):
        report(base, [f"x={tmp_path / 'absent.json'}:{'0' * 64}"])


def test_a_comparison_of_another_size_or_prepared_set_refuses(base, tmp_path):
    a1_files = wse.build_a1(base["prepared"]["root"], base["unit"], base["settings"], "f" * 64)
    rec = json.loads(a1_files["a1_selection.json"])
    short = tmp_path / "short.json"
    short.write_bytes(canonical_json({"selected": rec["selected"][:599]}))
    with pytest.raises(s1.Refusal, match="exactly k = 600"):
        report(base, [f"s={short}:{sha256_file(short)}"])
    edit = json.loads(a1_files["a1_remove600.edit.json"])
    edit["manifest_sha256"] = "0" * 64
    other = tmp_path / "other.json"
    other.write_bytes(canonical_json(edit))
    with pytest.raises(s1.Refusal, match="another prepared set"):
        report(base, [f"o={other}:{sha256_file(other)}"])
