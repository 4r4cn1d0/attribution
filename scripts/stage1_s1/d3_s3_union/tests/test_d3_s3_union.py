"""D-3 (addendum section 28): d3_s3_union on three real REQ-3 passes over synthetic pools (representation_pass.run on the
engine's fixture prepared set and tiny model; d3fixtures). J5's main pass scores the dev units, a stand-in pool and
s3_safe; its pools-only pass scores s3_orig; a third pass scores s3_safe and s3_orig together. The union of the first
two is that third pass's rows file byte for byte, and score_s3_datarx.py (by path, through D-3) on the union writes
what score_s3_datarx.py (by name) writes on the third pass, except provenance.inputs.summary (the summary's own
SHA-256). Then every refusal: a changed byte of each input, another settings, script, engine, model or anchor mean, a
pool at the wrong SHA-256, a pool in the wrong pass, a pass that is not pools-only, a row with a text field or in
another form, repeated ids, the W1 files, the folders, and the scorer's own refusal after the union is written.
Synthetic data only; nothing real is read."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from experiments.safety_selection.common import canonical_json, json_line, sha256_bytes  # noqa: E402
from scripts.stage1 import representation_pass as rp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import score_s3_datarx as s3  # noqa: E402
from scripts.stage1_s1.d3_s3_union import d3_s3_union as d3m  # noqa: E402

import d3fixtures as dx  # noqa: E402
from d3guard import guarded  # noqa: E402  (a wrapper defect fails the tests, never errors their setup)
import test_representation_pass as trp  # noqa: E402  (its env fixture: the engine's fixture prepared set)

env = trp.env
ZERO, ONE = "0" * 64, "1" * 64
PINNED = (("scorer", "scorer_sha256", "score_s3_datarx.py"),                  # by hand (d3m.PINNED; a test compares)
          ("scorer_settings", "scorer_settings_sha256", "score_s3_datarx.json"),
          ("pass_script", "pass_script_sha256", "representation_pass.py"),
          ("pass_settings", "pass_settings_sha256", "representation_pass.json"),
          ("s1common", "s1common_sha256", "s1common.py"))


@pytest.fixture(scope="module")
def world(env, tmp_path_factory):
    """The three passes and the two records (d3fixtures.make_world). Runs REQ-3 only, no D-3 code."""
    return dx.make_world(env, tmp_path_factory.mktemp("d3world"))


def _run(fn, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(argv)
    return code, out.getvalue(), err.getvalue()


def make_both(world, root: Path) -> dict:
    """D-3's CLI on the two J5 passes, and score_s3_datarx.py's own CLI (by name) on the one pass over both pools."""
    work, out, single_out = root / "work", root / "out", root / "single-out"
    code, stdout, stderr = _run(d3m.main, dx.argv(world["files"], work, out))
    assert code == 0, stderr
    f = world["files"]
    single_code, _, single_err = _run(s3.main, ["--rows", dx.spec(f["single_rows"]), "--summary", dx.spec(f["single_summary"]),
                                                "--s-pool-record", dx.spec(f["s_pool_record"]),
                                                "--answers-record", dx.spec(f["answers_record"]), "--out", str(single_out)])
    assert single_code == 0, single_err
    return {"work": dx.outputs(work), "out": dx.outputs(out), "single": dx.outputs(single_out), "stdout": stdout,
            "work_dir": work, "modules_after": set(sys.modules)}


@pytest.fixture(scope="module")
def both(world, tmp_path_factory):
    """Guarded: a D-3 defect here fails every test that reads it (d3guard)."""
    root = tmp_path_factory.mktemp("d3both")
    return guarded("both", lambda: make_both(world, root))


@pytest.fixture(scope="module")
def loaded():
    """(D-3's settings, their SHA-256, the loaded scorer). Guarded."""
    def make():
        d3, digest = d3m.load_settings()
        return d3, digest, d3m.load_scorer(d3)
    return guarded("loaded", make)


def union(world, loaded, **replace) -> dict[str, bytes]:
    d3, digest, base = loaded
    return d3m.union_files(dx.inputs_of(world, **replace), d3, digest, base)


def without(doc: dict, *path) -> dict:
    doc = copy.deepcopy(doc)
    node = doc
    for key in path[:-1]:
        node = node[key]
    node.pop(path[-1])
    return doc


def leaves(a, b, path=()) -> list[tuple]:
    """Every leaf path where two parsed JSON documents differ."""
    if isinstance(a, dict) and isinstance(b, dict):
        return [d for k in sorted(set(a) | set(b)) for d in (leaves(a[k], b[k], path + (k,)) if k in a and k in b
                                                              else [path + (k,)])]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in leaves(x, y, path + (i,))]
    return [] if canonical_json(a) == canonical_json(b) else [path]


# ----- the union equals one pass over both pools ---------------------------------------------------------------------


def test_the_union_rows_are_one_pools_only_pass_over_both_pools_byte_for_byte(world, both):
    """Section 28 point 4 on CPU: the main pass's s3_safe rows (scored beside the dev units and another pool) and the
    pools-only pass's s3_orig rows, in that order, are the rows file of one pools-only pass over s3_safe and s3_orig."""
    single = world["files"]["single_rows"][0].read_bytes()
    assert both["work"][rp.ROWS_FILE] == single
    assert len(single.splitlines()) == 7 + 6                                    # 7 s3_safe rows, 6 s3_orig (c-03 refused)


def test_each_pass_gives_a_row_the_same_bytes_whatever_else_it_scores(world):
    """The condition itself: a row's line does not depend on the other rows of its pass."""
    lines = {w: {json.loads(l)["id"]: l for l in world["files"][f"{w}_rows"][0].read_bytes().splitlines()}
             for w in ("main", "orig", "single")}
    assert {json.loads(l)["source"] for l in lines["main"].values()} == {"dev", "other", "s3_safe"}
    for rid, line in lines["single"].items():
        assert line == (lines["main"] if rid in lines["main"] else lines["orig"])[rid]


def test_the_scorer_writes_one_passs_output_except_the_summarys_sha256(world, both):
    """score_s3_datarx.py by path on the union against score_s3_datarx.py by name on the one pass: equal in every leaf
    but provenance.inputs.summary, which names each summary's own SHA-256; scores, per-layer values and reports are
    equal byte for byte."""
    mine, theirs = json.loads(both["out"][s3.OUTPUT]), json.loads(both["single"][s3.OUTPUT])
    assert sorted(both["out"]) == sorted(both["single"]) == [s3.OUTPUT]
    assert leaves(mine, theirs) == [("provenance", "inputs", "summary")]
    assert mine["provenance"]["inputs"]["summary"] == sha256_bytes(both["work"][rp.SUMMARY_FILE])
    assert theirs["provenance"]["inputs"]["summary"] == world["files"]["single_summary"][1]
    for key in ("scores", "per_layer", "reports"):
        assert canonical_json(mine[key]) == canonical_json(theirs[key])
    assert canonical_json(without(mine, "provenance", "inputs", "summary")) == \
        canonical_json(without(theirs, "provenance", "inputs", "summary"))
    assert mine["reports"]["leaving_the_ranking"] == {"count": 1, "ids": [dx.REFUSED_ORIG], "by_reason": {"NoTargets": 1}}
    assert sorted(mine["scores"]) == sorted(set(dx.SUBSET) - {dx.REFUSED_ORIG})
    assert set(mine["reports"]["s1_sas"]) == set(dx.S1_IDS) and mine["reports"]["s1_sas"]["x-09"] is not None


def test_the_union_summary_is_the_main_pass_summary_with_both_pools_the_union_rows_and_d3(world, both, loaded):
    d3, digest, base = loaded
    union_doc = json.loads(both["work"][rp.SUMMARY_FILE])
    main, single, orig = dx.summary_of(world, "main"), dx.summary_of(world, "single"), dx.summary_of(world, "orig")
    assert set(union_doc) == set(main) | {"d3"}
    for key in set(main) - {"pools", "rows"}:
        assert canonical_json(union_doc[key]) == canonical_json(main[key]), key
    assert canonical_json(union_doc["pools"]) == canonical_json(single["pools"])            # one pass's pool entries
    assert canonical_json(union_doc["pools"]) == canonical_json([main["pools"][1], orig["pools"][0]])
    assert union_doc["pools"][1]["refused_by_reason"] == {"NoTargets": 1}
    assert canonical_json(union_doc["rows"]) == canonical_json(single["rows"])
    block = union_doc["d3"]
    f = world["files"]
    assert block["kind"] == "stage1 d3 s3 union" and block["version"] == 1
    assert block["sources"]["main"] == {"summary_sha256": f["main_summary"][1], "rows_sha256": f["main_rows"][1],
                                        "pool": "s3_safe", "pool_sha256": world["pools"]["s3_safe"][1], "rows_taken": 7,
                                        "lines": main["rows"]["lines"], "by_source": main["rows"]["by_source"],
                                        "pools": ["other", "s3_safe"]}
    assert block["sources"]["orig"] == {"summary_sha256": f["orig_summary"][1], "rows_sha256": f["orig_rows"][1],
                                        "pool": "s3_orig", "pool_sha256": world["pools"]["s3_orig"][1], "rows_taken": 6,
                                        "lines": 6, "by_source": {"s3_orig": 6}, "pools": ["s3_orig"]}
    assert block["records"] == {"s_pool_record_sha256": f["s_pool_record"][1], "answers_record_sha256": f["answers_record"][1]}
    assert block["checked_equal"] == d3["passes"]["equal"] and block["reference"] == d3["reference"]
    assert block["rule"] == d3["union"]["rule"] and block["from_the_main_pass"] == d3["union"]["summary"]
    prov = block["provenance"]
    assert prov["script"] == s1.rel(Path(d3m.__file__))                     # relative in the workspace (absolute in a
    assert prov["script"].endswith("scripts/stage1_s1/d3_s3_union/d3_s3_union.py")   # mutation copy outside it)
    assert prov["script_sha256"] == sha256_bytes(Path(d3m.__file__).read_bytes())
    assert prov["settings_sha256"] == digest == d3m.SETTINGS_SHA256
    assert prov["score_s3_datarx_sha256"] == base.scorer_sha256 == d3["base"]["scorer_sha256"]
    assert prov["w1_manifest_sha256"] == sha256_bytes((d3m.w1_root() / d3["base"]["manifest"]).read_bytes())
    assert prov["representation_pass_sha256"] == d3["base"]["pass_script_sha256"]
    assert prov["engine_identity_sha256"] == d3["engine_x"]


def test_the_cli_writes_what_union_files_returns_and_prints_hashes_only(world, both, loaded):
    assert both["work"] == union(world, loaded)
    for name, data in both["work"].items():
        assert f"{sha256_bytes(data)}  {both['work_dir'] / name}" in both["stdout"]
    assert sha256_bytes(both["out"][s3.OUTPUT]) in both["stdout"]


def test_the_outputs_are_text_free(world, both):
    for data in [*both["work"].values(), *both["out"].values()]:
        assert s1._text_hits(data, world["texts"]) == 0
    assert all(t.encode() in world["pools"][n][0].read_bytes() for n in ("s3_safe",) for t in world["texts"][:2])


def test_the_scorer_runs_as_a_private_module(both):
    assert d3m.MODULE_NAME not in both["modules_after"] and d3m.MODULE_NAME not in sys.modules


# ----- refusals: the two passes ---------------------------------------------------------------------------------------


def _set(path, value):
    def fn(doc):
        node = doc
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
    return fn


def _float_anchor(doc):
    doc["anchors"]["safe"] = float(doc["anchors"]["safe"])                     # 3 == 3.0 in Python, not in JSON


def _with_pool(name, items=1):
    def fn(doc):
        doc["pools"].append({"name": name, "sha256": "2" * 64, "items": items, "pinned_by": "command line",
                             "refused_by_reason": {}})
    return fn


SUMMARY_CASES = [
    ("kind", "main", _set(("kind",), "stage1 other pass"), "not a version-1"),
    ("version-bool", "orig", _set(("version",), True), "not a version-1"),
    ("extra-field", "orig", _set(("notes",), "x"), "exactly the fields"),
    ("missing-field", "main", lambda d: d.pop("untuned"), "exactly the fields"),
    ("rows-file", "main", _set(("rows", "file"), "rows.jsonl"), "no rows block"),
    ("rows-block-extra", "orig", _set(("rows", "x"), 1), "no rows block"),
    ("no-layers", "main", _set(("layout", "n_layers"), 0), "no layer count"),
    ("pool-entry-extra", "main", lambda d: d["pools"][0].__setitem__("x", 1), "lists a pool that is not"),
    ("pool-twice", "main", lambda d: d["pools"].append(copy.deepcopy(d["pools"][0])), "one pool name twice"),
    ("no-inputs", "orig", lambda d: d["provenance"].pop("inputs"), "no provenance.inputs"),
    ("no-groups", "orig", lambda d: d["gate_c"].pop("groups"), "no gate_c.groups"),
    ("costs", "orig", _set(("costs",), []), "no costs object"),
    ("settings", "orig", _set(("provenance", "settings_sha256"), ZERO), r"differ in provenance\.settings_sha256"),
    ("script-sha", "orig", _set(("provenance", "script_sha256"), ZERO), r"differ in provenance\.script_sha256"),
    ("script", "main", _set(("provenance", "script"), "scripts/x.py"), r"differ in provenance\.script \("),
    ("s1common", "orig", _set(("provenance", "s1common_sha256"), ZERO), r"differ in provenance\.s1common_sha256"),
    ("engine", "orig", _set(("provenance", "engine_identity_sha256"), ZERO), r"differ in provenance\.engine_identity"),
    ("labels", "orig", _set(("provenance", "label_entries"), {"x": ZERO}), r"differ in provenance\.label_entries"),
    ("python", "orig", _set(("provenance", "python"), "3.0.0"), r"differ in provenance\.python"),
    ("numpy-missing", "orig", lambda d: d["provenance"].pop("numpy"), r"differ in provenance\.numpy \(or one"),
    ("recipe", "orig", _set(("provenance", "inputs", "recipe_file"), ZERO), r"differ in provenance\.inputs\.recipe_file"),
    ("anchor-file", "orig", _set(("provenance", "inputs", "anchor_file"), ZERO), r"inputs\.anchor_file"),
    ("prepared", "main", _set(("provenance", "inputs", "prepared_manifest"), ZERO), r"inputs\.prepared_manifest"),
    ("pins-input", "main", _set(("provenance", "inputs", "pool_pins"), ZERO), r"inputs\.pool_pins"),
    ("model-type", "orig", _set(("layout", "model_type"), "llama"), r"differ in layout \("),
    ("layers", "orig", _set(("layout", "n_layers"), 5), r"differ in layout \("),
    ("hidden", "orig", _set(("layout", "hidden_size"), 64), r"differ in layout \("),
    ("datashield", "orig", lambda d: d["datashield"]["cas"].__setitem__(1, 0.123), r"differ in datashield"),
    ("direction-norm", "orig", lambda d: d["datashield"]["direction_norm"].__setitem__(2, 9.0), r"differ in datashield"),
    ("anchors", "orig", _set(("anchors", "safe"), 2), r"differ in anchors"),
    ("anchors-float", "orig", _float_anchor, r"differ in anchors"),
    ("transformers", "orig", _set(("transformers_version",), "4.57.0"), "differ in transformers_version"),
    ("untuned", "orig", _set(("untuned",), "another"), "differ in untuned"),
    ("index-convention", "orig", _set(("index_convention",), "x"), "differ in index_convention"),
    ("reads", "orig", _set(("reads", "a"), "x"), "differ in reads"),
    ("requirement", "orig", _set(("requirement",), "REQ-0"), "differ in requirement"),
    ("pool-pins", "orig", _set(("pool_pins", "sha256"), ZERO), "differ in pool_pins"),
    ("gate-c-index", "orig", _set(("gate_c", "index"), 3), r"differ in gate_c\.index"),
    ("gate-c-read", "orig", _set(("gate_c", "read"), "a"), r"differ in gate_c\.read"),
    ("gate-c-rule", "orig", _set(("gate_c", "rule"), "another"), r"differ in gate_c\.rule"),
    ("device", "orig", _set(("costs", "device"), "cuda"), r"differ in costs\.device"),
    ("lines", "orig", lambda d: d["rows"].__setitem__("lines", d["rows"]["lines"] + 1), "its summary states"),
    ("by-source", "main", lambda d: d["rows"]["by_source"].__setitem__("s3_safe", 99), "its summary states"),
    ("by-source-float", "orig", lambda d: d["rows"]["by_source"].__setitem__("s3_orig", 6.0), "its summary states"),
    ("not-pools-only-groups", "orig", lambda d: d["gate_c"]["groups"].__setitem__("u", {"rows": 1}), "not a pools-only"),
    ("not-pools-only-dev", "orig", lambda d: d["rows"]["by_source"].__setitem__("dev", 1), "not a pools-only"),
    ("orig-in-main", "main", _with_pool("s3_orig"), "the main pass lists pool s3_orig"),
    ("safe-in-orig", "orig", _with_pool("s3_safe"), "the pools-only pass lists pool s3_safe"),
    ("orig-input-in-main", "main", _set(("provenance", "inputs", "pool_s3_orig"), ONE), "lists pool s3_orig"),
    ("safe-input-in-orig", "orig", _set(("provenance", "inputs", "pool_s3_safe"), ONE), "lists pool s3_safe"),
    ("safe-unnamed", "main", _set(("provenance", "inputs", "pool_s3_safe"), ONE), "provenance does not name pool s3_safe"),
    ("orig-unnamed", "orig", lambda d: d["provenance"]["inputs"].pop("pool_s3_orig"), "does not name pool s3_orig"),
    ("safe-missing", "main", lambda d: d.__setitem__("pools", [p for p in d["pools"] if p["name"] != "s3_safe"]),
     "does not list pool s3_safe"),
    ("orig-missing", "orig", _set(("pools",), []), "does not list pool s3_orig"),
    ("safe-at-other-sha", "main", lambda d: d["pools"][1].__setitem__("sha256", ONE), "lists pool s3_safe at 1{64}"),
    ("items", "orig", lambda d: d["pools"][0].__setitem__("items", d["pools"][0]["items"] + 1), "items less its refused"),
    ("refused-more", "orig", lambda d: d["pools"][0]["refused_by_reason"].__setitem__("NoTargets", 2),
     "items less its refused"),
    ("refused-bool", "orig", lambda d: d["pools"][0]["refused_by_reason"].__setitem__("NoTargets", True), "not counts"),
    ("refused-above-items", "orig", lambda d: d["pools"][0]["refused_by_reason"].__setitem__("NoTargets", 99),
     "not counts"),
    ("items-zero", "main", lambda d: d["pools"][1].__setitem__("items", 0), "not counts"),
]


@pytest.mark.parametrize("which, edit, match", [c[1:] for c in SUMMARY_CASES], ids=[c[0] for c in SUMMARY_CASES])
def test_a_summary_edit_refuses(world, loaded, which, edit, match):
    with pytest.raises(s1.Refusal, match=match):
        union(world, loaded, **dx.edit_pass(world, which, summary=edit))


def test_an_unedited_pass_re_serialised_by_the_helper_passes(world, loaded):
    """The control of the edit cases: edit_pass with no edit gives the same bytes and a union."""
    for which in ("main", "orig"):
        replace = dx.edit_pass(world, which)
        assert replace[f"{which}_rows"] == world["files"][f"{which}_rows"][0].read_bytes()
        assert replace[f"{which}_summary"] == world["files"][f"{which}_summary"][0].read_bytes()
    assert set(union(world, loaded)) == {rp.ROWS_FILE, rp.SUMMARY_FILE}


@pytest.mark.parametrize("path, value, match", [
    (("provenance", "settings_sha256"), ZERO, r"provenance\.settings_sha256 is 0{64}, the D-3 settings pin a555fd89"),
    (("provenance", "script_sha256"), ZERO, r"provenance\.script_sha256 is 0{64}, the D-3 settings pin fb62bcaa"),
    (("provenance", "script"), "scripts/stage1/other.py", r"provenance\.script is scripts/stage1/other\.py"),
    (("provenance", "engine_identity_sha256"), ZERO, r"provenance\.engine_identity_sha256 is 0{64}, the D-3 settings pin 472f"),
], ids=["settings", "script-sha", "script", "engine"])
def test_both_passes_on_another_script_settings_or_engine_refuse(world, loaded, path, value, match):
    """Equal to each other but not this package's pins."""
    replace = {**dx.edit_pass(world, "main", summary=_set(path, value)), **dx.edit_pass(world, "orig", summary=_set(path, value))}
    with pytest.raises(s1.Refusal, match=match):
        union(world, loaded, **replace)


@pytest.mark.parametrize("path", [("provenance", "numpy"), ("provenance", "inputs", "recipe_file"), ("gate_c", "rule"),
                                  ("costs", "device")], ids=["numpy", "recipe", "gate-c-rule", "device"])
def test_a_field_that_both_passes_lack_refuses(world, loaded, path):
    """Two passes that both lack a checked field are not shown equal in it."""
    def drop(doc):
        node = doc
        for key in path[:-1]:
            node = node[key]
        node.pop(path[-1])
    replace = {**dx.edit_pass(world, "main", summary=drop), **dx.edit_pass(world, "orig", summary=drop)}
    with pytest.raises(s1.Refusal, match=r"differ in " + r"\.".join(path) + r" \(or one of them lacks it\)"):
        union(world, loaded, **replace)


def test_the_passes_given_the_other_way_round_refuse(world, loaded):
    f = {k: v[0].read_bytes() for k, v in world["files"].items()}
    swapped = {"main_rows": f["orig_rows"], "main_summary": f["orig_summary"], "orig_rows": f["main_rows"],
               "orig_summary": f["main_summary"]}
    with pytest.raises(s1.Refusal, match="the main pass lists pool s3_orig, which D-3 takes from the other pass only"):
        union(world, loaded, **swapped)


def test_a_rows_file_that_its_summary_does_not_name_refuses(world, loaded):
    rows = dx.edit_pass(world, "main", rows=lambda r: r[0]["css"].__setitem__(0, 0.5))["main_rows"]
    with pytest.raises(s1.Refusal, match="the main pass's rows file is not the one its summary names"):
        union(world, loaded, main_rows=rows)
    rows = dx.edit_pass(world, "orig", rows=lambda r: r[0]["css"].__setitem__(0, 0.5))["orig_rows"]
    with pytest.raises(s1.Refusal, match="the pools-only pass's rows file is not the one its summary names"):
        union(world, loaded, orig_rows=rows)


# ----- refusals: the rows (text-free and REQ-3's form) ----------------------------------------------------------------


def _first(source):
    def pick(rows):
        return next(r for r in rows if r["source"] == source)
    return pick


def _row(source, fn):
    def edit(rows):
        fn(_first(source)(rows))
    return edit


ROW_CASES = [
    ("text-field", "orig", _row("s3_orig", lambda r: r.__setitem__("prompt", "a synthetic prompt text")),
     r"holds 1 field\(s\) besides REQ-3's"),
    ("text-field-safe", "main", _row("s3_safe", lambda r: r.__setitem__("response", "a synthetic response text")),
     r"holds 1 field\(s\) besides REQ-3's"),
    ("missing-css", "main", _row("s3_safe", lambda r: r.pop("css")), r"lacks \['css'\]"),
    ("id-with-space", "orig", _row("s3_orig", lambda r: r.__setitem__("id", "c 00:orig")), "not a short pool id"),
    ("id-long", "orig", _row("s3_orig", lambda r: r.__setitem__("id", "c" * 157 + ":orig")), "not a short pool id"),
    ("id-number", "main", _row("s3_safe", lambda r: r.__setitem__("id", 7)), "not a short pool id"),
    ("id-newline", "orig", _row("s3_orig", lambda r: r.__setitem__("id", r["id"] + "\n")), "not a short pool id"),
    ("unit", "orig", _row("s3_orig", lambda r: r.__setitem__("unit", "unit-1")), "names a unit"),
    ("n-prompt", "orig", _row("s3_orig", lambda r: r.__setitem__("n_prompt", r["n_tokens"] - 1)), "token counts"),
    ("n-prompt-zero", "main", _row("s3_safe", lambda r: r.__setitem__("n_prompt", 0)), "token counts"),
    ("n-tokens-float", "orig", _row("s3_orig", lambda r: r.__setitem__("n_tokens", float(r["n_tokens"]))), "token counts"),
    ("cos-index", "orig", _row("s3_orig", lambda r: r["cos_safe"].pop()), r"cos_safe is not \d+ rows of 4 numbers"),
    ("cos-reads", "main", _row("s3_safe", lambda r: r["cos_harmful"][0].append(0.0)), "cos_harmful is not"),
    ("cos-bool", "orig", _row("s3_orig", lambda r: r["cos_safe"][1].__setitem__(0, True)), "cos_safe is not"),
    ("cos-null", "orig", _row("s3_orig", lambda r: r["cos_harmful"][1].__setitem__(0, None)), "cos_harmful is not"),
    ("cos-flat", "orig", _row("s3_orig", lambda r: r.__setitem__("cos_safe", [0.0] * 5)), "cos_safe is not"),
    ("css-text", "orig", _row("s3_orig", lambda r: r["css"].__setitem__(0, "x")), "css is not"),
    ("css-short", "main", _row("s3_safe", lambda r: r["css"].pop()), "css is not"),
    ("repeated-id", "orig", _row("s3_orig", lambda r: r.__setitem__("id", "c-00")), r"1 row id\(s\) repeat across the union"),
    ("orig-suffix", "orig", _row("s3_orig", lambda r: r.__setitem__("id", "c-00-orig")), "does not end with ':orig'"),
    ("no-source", "orig", _row("s3_orig", lambda r: r.pop("source")), "line 1 is not a row with a source"),
    ("source-moved", "orig", _row("s3_orig", lambda r: r.__setitem__("source", "s3_safe")), "its summary states"),
]


@pytest.mark.parametrize("which, edit, match", [c[1:] for c in ROW_CASES], ids=[c[0] for c in ROW_CASES])
def test_a_row_edit_refuses(world, loaded, which, edit, match):
    with pytest.raises(s1.Refusal, match=match):
        union(world, loaded, **dx.edit_pass(world, which, rows=edit))


def _raw(which, fn):
    def make(world):
        return fn(world["files"][f"{which}_rows"][0].read_bytes())
    return make


RAW_CASES = [
    ("no-final-newline", "orig", _raw("orig", lambda b: b[:-1]), "does not end with a newline"),
    ("blank-line", "orig", _raw("orig", lambda b: b.replace(b"\n", b"\n\n", 1)), "line 2 is not one strict JSON value"),
    ("not-json", "main", _raw("main", lambda b: b"{not json}\n" + b), "line 1 is not one strict JSON value"),
    ("array-line", "main", _raw("main", lambda b: b"[1, 2]\n" + b), "line 1 is not a row with a source"),
    ("duplicate-key", "orig", _raw("orig", lambda b: b.replace(b'{"cos_harmful"', b'{"id": "x", "cos_harmful"', 1)),
     "line 1 is not one strict JSON value"),
    ("compact", "orig", _raw("orig", lambda b: b"".join(json.dumps(json.loads(l), sort_keys=True, separators=(",", ":"))
                                                        .encode() + b"\n" for l in b.splitlines())),
     "not REQ-3's serialisation"),
    ("unsorted", "main", _raw("main", lambda b: b"".join(json.dumps(dict(reversed(list(json.loads(l).items()))))
                                                         .encode() + b"\n" for l in b.splitlines())),
     "not REQ-3's serialisation"),
    ("crlf", "orig", _raw("orig", lambda b: b.replace(b"\n", b"\r\n")), "not REQ-3's serialisation"),
]


@pytest.mark.parametrize("which, make, match", [c[1:] for c in RAW_CASES], ids=[c[0] for c in RAW_CASES])
def test_a_rows_file_in_another_form_refuses(world, loaded, which, make, match):
    with pytest.raises(s1.Refusal, match=match):
        union(world, loaded, **dx.edit_pass(world, which, rows_bytes=make(world)))


def test_every_row_of_the_union_has_exactly_reqs_fields_and_no_text(world, both):
    for line in both["work"][rp.ROWS_FILE].splitlines():
        row = json.loads(line)
        assert set(row) == d3m.ROW_KEYS and row["unit"] is None and row["source"] in ("s3_safe", "s3_orig")
        assert json_line(row) == line + b"\n"


# ----- refusals: the records ------------------------------------------------------------------------------------------


def _both_records(fn_pool, fn_answers):
    def make(world):
        return {**dx.edit_record(world, "s_pool_record", fn_pool), **dx.edit_record(world, "answers_record", fn_answers)}
    return make


def _one(key, fn):
    def make(world):
        return dx.edit_record(world, key, fn)
    return make


def _s3(fn):
    return lambda d: fn(d["lists"]["s3"])


RECORD_CASES = [
    ("pool-kind", _one("s_pool_record", _set(("kind",), "stage1 other")), "the S-pool record is not"),
    ("answers-kind", _one("answers_record", _set(("kind",), "stage1 other")), "J6's record is not"),
    ("no-safe-sha", _one("s_pool_record", lambda d: d.pop("s3_pool")), "names no s3_pool.sha256"),
    ("safe-sha-newline", _one("s_pool_record", lambda d: d["s3_pool"].__setitem__("sha256", d["s3_pool"]["sha256"] + "\n")),
     "names no s3_pool.sha256"),
    ("no-orig-sha", _one("answers_record", _s3(lambda s: s.pop("s3_orig_pool_sha256"))), "names no lists.s3"),
    ("orig-sha-upper", _one("answers_record", _s3(lambda s: s.__setitem__("s3_orig_pool_sha256", s["s3_orig_pool_sha256"].upper()))),
     "names no lists.s3"),
    ("chain", _one("answers_record", _s3(lambda s: s.__setitem__("list_sha256", "3" * 64))), "J6's s3 list is not"),
    ("safe-at-the-wrong-sha", _both_records(lambda d: d["s3_pool"].__setitem__("sha256", ONE),
                                            _s3(lambda s: s.__setitem__("list_sha256", ONE))),
     r"the main pass lists pool s3_safe at [0-9a-f]{64}; the S-pool record's s3_pool\.sha256 gives 1{64}"),
    ("orig-at-the-wrong-sha", _one("answers_record", _s3(lambda s: s.__setitem__("s3_orig_pool_sha256", "2" * 64))),
     r"the pools-only pass lists pool s3_orig at [0-9a-f]{64}; J6's record's lists\.s3\.s3_orig_pool_sha256 gives 2{64}"),
]


@pytest.mark.parametrize("make, match", [c[1:] for c in RECORD_CASES], ids=[c[0] for c in RECORD_CASES])
def test_a_record_edit_refuses(world, loaded, make, match):
    with pytest.raises(s1.Refusal, match=match):
        union(world, loaded, **make(world))


# ----- the CLI: changed bytes, folders, the scorer's own refusal -----------------------------------------------------


@pytest.mark.parametrize("key", dx.KEYS)
def test_a_changed_byte_of_any_input_refuses_and_writes_nothing(world, tmp_path, key):
    path, digest = world["files"][key]
    data = bytearray(path.read_bytes())
    data[len(data) // 2] ^= 0x01
    changed = tmp_path / "changed" / path.name
    changed.parent.mkdir()
    changed.write_bytes(bytes(data))
    files = {**world["files"], key: (changed, digest)}
    code, _, err = _run(d3m.main, dx.argv(files, tmp_path / "work", tmp_path / "out"))
    assert code == 2 and "hashes to" in err and "(nothing written)" in err
    assert not (tmp_path / "work").exists() and not (tmp_path / "out").exists()


@pytest.mark.parametrize("key", dx.KEYS)
def test_an_input_without_its_sha256_refuses(world, tmp_path, key):
    args = dx.argv(world["files"], tmp_path / "work", tmp_path / "out")
    flag = dict((k, f) for k, f, _ in d3m.INPUTS)[key]
    args[args.index(flag) + 1] = str(world["files"][key][0]) + ":" + world["files"][key][1][:63]
    code, _, err = _run(d3m.main, args)
    assert code == 2 and f"{flag} is PATH:SHA256" in err and not (tmp_path / "work").exists()


@pytest.mark.parametrize("layout", ["work-not-empty", "out-not-empty", "same", "out-in-work", "work-in-out", "work-a-file"])
def test_the_folders_must_be_two_separate_absent_or_empty_folders(world, tmp_path, layout):
    work, out = tmp_path / "work", tmp_path / "out"
    if layout == "work-not-empty":
        (work / "x").mkdir(parents=True)
    elif layout == "out-not-empty":
        out.mkdir()
        (out / "s3_scores.json").write_bytes(b"{}")
    elif layout == "same":
        out = work
    elif layout == "out-in-work":
        out = work / "out"
    elif layout == "work-in-out":
        work = out / "work"
    else:
        work.write_bytes(b"")
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    code, _, err = _run(d3m.main, dx.argv(world["files"], work, out))
    assert code == 2 and "REFUSED" in err
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")) == before


def test_an_empty_work_folder_is_used(world, tmp_path):
    (tmp_path / "work").mkdir()
    (tmp_path / "out").mkdir()
    code, _, err = _run(d3m.main, dx.argv(world["files"], tmp_path / "work", tmp_path / "out"))
    assert code == 0, err
    assert sorted(dx.outputs(tmp_path / "work")) == sorted([rp.ROWS_FILE, rp.SUMMARY_FILE])
    assert sorted(dx.outputs(tmp_path / "out")) == [s3.OUTPUT]


def test_the_scorers_own_refusal_after_the_union_keeps_out_empty(world, tmp_path):
    """J6's record without one S3 subset row passes D-3's checks (D-3 reads its pool pins only); score_s3_datarx.py then
    refuses ('does not hold every S3 subset id'): exit 2, the union's two files in --work, nothing in --out."""
    replace = dx.edit_record(world, "answers_record", _s3(lambda s: s.__setitem__("rows", s["rows"][1:])))
    files = dx.write_inputs(world, tmp_path / "inputs", replace)
    code, _, err = _run(d3m.main, dx.argv(files, tmp_path / "work", tmp_path / "out"))
    assert code == 2
    assert "REFUSED: REQ-9's record does not hold every S3 subset id (nothing written)" in err
    assert "score_s3_datarx.py refused (exit 2)" in err
    assert sorted(dx.outputs(tmp_path / "work")) == sorted([rp.ROWS_FILE, rp.SUMMARY_FILE])
    assert dx.outputs(tmp_path / "out") == {}


def test_the_d3_settings_pin_refuses_another_file(world, tmp_path, monkeypatch):
    monkeypatch.setattr(d3m, "SETTINGS_SHA256", ZERO)
    code, _, err = _run(d3m.main, dx.argv(world["files"], tmp_path / "work", tmp_path / "out"))
    assert code == 2 and "settings d3_s3_union hash to" in err and not (tmp_path / "work").exists()


def test_a_by_name_module_that_is_not_the_pinned_file_refuses(world, tmp_path, monkeypatch):
    other = tmp_path / "representation_pass.py"
    other.write_bytes(Path(rp.__file__).read_bytes() + b"\n")
    monkeypatch.setattr(rp, "__file__", str(other))
    code, _, err = _run(d3m.main, dx.argv(world["files"], tmp_path / "work", tmp_path / "out"))
    assert code == 2 and "the representation_pass module that score_s3_datarx imports by name hashes to" in err
    monkeypatch.undo()
    monkeypatch.setattr(s1, "__file__", str(other))
    code, _, err = _run(d3m.main, dx.argv(world["files"], tmp_path / "work2", tmp_path / "out2"))
    assert code == 2 and "the s1common module that score_s3_datarx imports by name hashes to" in err
    assert not (tmp_path / "work").exists() and not (tmp_path / "work2").exists()


# ----- the W1 files, by path ------------------------------------------------------------------------------------------


def test_the_scorer_loads_from_a_tmp_copy_and_leaves_sys_path_as_it_was(tmp_path):
    root = dx.fake_root(tmp_path)
    before = list(sys.path)
    base = d3m.load_scorer(dx.committed_d3(), root)
    assert sys.path == before and str(root) not in sys.path
    assert Path(base.module.__file__) == (root / "scripts" / "stage1" / "score_s3_datarx.py").resolve()
    assert base.module.SETTINGS_PATH == (root / "scripts" / "stage1" / "settings" / "score_s3_datarx.json").resolve()
    assert d3m.MODULE_NAME not in sys.modules


@pytest.mark.parametrize("rel_key, pin_key, what", PINNED, ids=[p[2] for p in PINNED])
def test_a_changed_w1_file_refuses(tmp_path, rel_key, pin_key, what):
    root = dx.fake_root(tmp_path)
    d3 = dx.committed_d3()
    path = root / d3["base"][rel_key]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(s1.Refusal, match=f"{what} hashes to"):
        d3m.load_scorer(d3, root)


@pytest.mark.parametrize("rel_key, pin_key, what", PINNED, ids=[p[2] for p in PINNED])
def test_a_manifest_entry_other_than_the_pin_refuses(tmp_path, rel_key, pin_key, what):
    root = dx.fake_root(tmp_path)
    d3 = dx.committed_d3()
    manifest = root / d3["base"]["manifest"]
    doc = json.loads(manifest.read_bytes())
    for entry in doc["entries"]:
        if entry.get("path") == d3["base"][rel_key]:
            entry["sha256"] = ZERO
    manifest.write_bytes(canonical_json(doc))
    with pytest.raises(s1.Refusal, match=f"{what}: the W1 manifest names 0{{64}}, the D-3 settings pin"):
        d3m.load_scorer(d3, root)


def test_a_file_that_is_not_the_manifest_refuses(tmp_path):
    root = dx.fake_root(tmp_path)
    d3 = dx.committed_d3()
    (root / d3["base"]["manifest"]).write_bytes(canonical_json({"kind": "another", "entries": []}))
    with pytest.raises(s1.Refusal, match="not the stage-1 W1 commitments manifest"):
        d3m.load_scorer(d3, root)


def test_the_scorers_literal_settings_pin_must_be_d3s(tmp_path):
    root = dx.fake_root(tmp_path)
    d3 = dx.committed_d3()
    code = (root / d3["base"]["scorer"]).read_bytes()
    needle = f'SETTINGS_SHA256 = "{d3["base"]["scorer_settings_sha256"]}"'.encode()
    assert code.count(needle) == 1
    dx.repin(root, d3, "scorer", "scorer_sha256", code.replace(needle, f'SETTINGS_SHA256 = "{ZERO}"'.encode()))
    with pytest.raises(s1.Refusal, match="score_s3_datarx.py's own settings pin is not"):
        d3m.load_scorer(d3, root)


def test_the_scorers_settings_must_pin_reqs_settings_at_d3s_pin(tmp_path):
    root = dx.fake_root(tmp_path)
    d3 = dx.committed_d3()
    doc = json.loads((root / d3["base"]["scorer_settings"]).read_bytes())
    doc["pins"]["representation_pass_settings_sha256"] = ZERO
    dx.repin(root, d3, "scorer_settings", "scorer_settings_sha256", canonical_json(doc))
    with pytest.raises(s1.Refusal, match="does not pin REQ-3's settings at the D-3 pin"):
        d3m.load_scorer(d3, root)


# ----- the committed settings and the W1 constants --------------------------------------------------------------------


def test_the_committed_settings_are_pinned_and_name_the_w1_manifests_files(world):
    data = d3m.SETTINGS_PATH.read_bytes()
    assert sha256_bytes(data) == d3m.SETTINGS_SHA256
    doc = s1.check_settings(json.loads(data), "d3_s3_union")
    assert data == canonical_json(doc) and doc["label_entries"] == {}
    entries, _ = d3m.manifest_entries(d3m.w1_root() / doc["base"]["manifest"])
    pins = {"scripts/stage1/score_s3_datarx.py": "772e6ae546843b42c3a7564a644cffa269c38ffb30f4db0d59f0f405a9d5aace",
            "scripts/stage1/settings/score_s3_datarx.json": "6382dcc663e80ecab332ecf96b7cba621e3e535408481e6ab83ca614bc2b502f",
            "scripts/stage1/representation_pass.py": "fb62bcaaaa35595a52de5a4217754cb390ffb4ba49e04dec6e515d7e3cebb8d9",
            "scripts/stage1/settings/representation_pass.json": "a555fd899bd2b5caf8d68fb62578ed2e943977341b5bf2dc2d688dcbd034600b",
            "scripts/stage1/s1common.py": "930c8ea53d26baeeccaf2035949427d207f307ba0fec06ff0dec841c8c824552"}
    assert d3m.PINNED == PINNED and tuple(k for k, _, _ in d3m.INPUTS) == dx.KEYS
    assert {doc["base"][r]: doc["base"][p] for r, p, _ in PINNED} == pins
    assert all(entries[path] == sha for path, sha in pins.items())
    assert json.loads(s3.SETTINGS_PATH.read_bytes())["pins"]["representation_pass_settings_sha256"] == \
        doc["base"]["pass_settings_sha256"] == rp.SETTINGS_SHA256
    assert doc["passes"]["equal"] == {
        "fields": ["kind", "version", "requirement", "layout", "index_convention", "reads", "untuned",
                   "transformers_version", "anchors", "datashield", "pool_pins"],
        "provenance": ["script", "script_sha256", "s1common_sha256", "settings_sha256", "engine_identity_sha256",
                       "label_entries", "python", "numpy"],
        "inputs": ["anchor_file", "prepared_manifest", "recipe_file", "pool_pins"],
        "gate_c": ["index", "read", "rule"], "costs": ["device"]}
    assert doc["reference"].startswith(".ai/briefs/stage1-commitments-build-20261016-lead-decisions.md section 28")


def test_the_constants_are_reqs_and_the_scorers(world):
    main = dx.summary_of(world, "main")
    assert d3m.SUMMARY_KEYS == set(main) and d3m.ROWS_KEYS == set(main["rows"])
    assert all(set(p) == d3m.POOL_KEYS for p in main["pools"])
    assert all(set(r) == d3m.ROW_KEYS for r in dx.rows_of(world, "main"))
    assert (d3m.ROWS_FILE, d3m.SUMMARY_FILE, d3m.PASS_KIND) == (rp.ROWS_FILE, rp.SUMMARY_FILE, main["kind"])
    assert d3m.ROW_ID.pattern == rp.POOL_ID.pattern and d3m.N_READS == len(rp.READS)
    assert d3m.ORIG_SUFFIX == s3.ORIG_SUFFIX and (d3m.SAFE, d3m.ORIG) == ("s3_safe", "s3_orig")
    assert (d3m.SPOOL_KIND, d3m.ANSWERS_KIND) == (world["pool_rec"]["kind"], world["answers"]["kind"])


def test_the_d3_package_holds_no_copy_of_a_w1_file():
    pkg = Path(d3m.__file__).resolve().parent
    w1 = {sha256_bytes(p.read_bytes()) for p in (d3m.w1_root() / "scripts" / "stage1").rglob("*.py")}
    assert not any(sha256_bytes(p.read_bytes()) in w1 for p in pkg.rglob("*.py"))
