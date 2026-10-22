"""REQ-5: the length and format rules (H1, H2a, H2b, the octiles and their controls), on synthetic prepared sets."""

from __future__ import annotations

import copy
import json

import pytest

from experiments.safety_selection.edits import parse_edit
from scripts.stage1 import build_length_rules as blr
from scripts.stage1 import s1common as s1

import s1fixtures_b3 as fb


def settings_for(prep) -> dict:
    s = copy.deepcopy(json.loads(blr.SETTINGS_PATH.read_bytes()))
    s["prepared"]["manifest_sha256"] = prep["manifest_sha256"]
    return s


def response_mix(i: int) -> str:
    kind = i % 10
    return {0: "Intro line\n- one\n- two", 1: "Some text\n# Heading", 2: "Code follows\n```\nx = 1\n```",
            3: "- only one bullet", 4: "Plain answer about harbours."}.get(kind, f"Plain synthetic answer {i}.")


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    root = tmp_path_factory.mktemp("length")
    prep = fb.make_prepared(root / "p", response=response_mix, target=lambda i: 1 + (i * 37) % 50)
    return {"prep": prep, "settings": settings_for(prep), "cache": {}}


def files_of(env):
    if "files" not in env["cache"]:
        env["cache"]["files"] = blr.build(env["prep"]["root"], env["settings"], "e" * 64)
    return env["cache"]["files"]


def view(prep):
    return s1.PreparedView(prep["root"], prep["manifest_sha256"])


def removed(files, name):
    return json.loads(files[name])["remove"]


# ----- the length order, H1, H2b, octiles ------------------------------------------------------------


def test_h1_h2b_and_the_octiles_follow_one_sealed_length_order(env):
    files = files_of(env)
    v = view(env["prep"])
    rank = s1.sealed_rank(v.tokens, "length.order")
    order = sorted(v.tokens, key=lambda r: (v.tokens[r], rank[r]))
    for k in range(8):
        assert removed(files, f"edits/octile_{k}.json") == sorted(order[600 * k:600 * (k + 1)])
    h1 = removed(files, "edits/octile_0.json")
    assert max(v.tokens[r] for r in h1) <= min(v.tokens[r] for r in v.tokens if r not in set(h1))     # the smallest
    h2b = removed(files, "edits/octile_7.json")
    assert min(v.tokens[r] for r in h2b) >= max(v.tokens[r] for r in v.tokens if r not in set(h2b))   # the largest
    boundary = v.tokens[order[599]]
    tied = [r for r in v.tokens if v.tokens[r] == boundary]
    assert 1 < len(tied) and set(h1) & set(tied) == set(sorted(tied, key=lambda r: rank[r])[:len(set(h1) & set(tied))])
    union = [r for k in range(8) for r in removed(files, f"edits/octile_{k}.json")]
    assert sorted(union) == sorted(v.tokens) and len(union) == len(set(union))                         # a partition
    rec = json.loads(files[blr.RECORD])
    assert rec["h1"] == "edits/octile_0.json" and rec["h2b"] == "edits/octile_7.json"
    assert rec["cut_points"][0]["first_target_tokens"] == v.tokens[order[0]]


# ----- the controls ---------------------------------------------------------------------------------


def test_each_control_matches_its_octiles_categories_and_avoids_its_rows(env):
    files = files_of(env)
    v = view(env["prep"])
    rec = {r["file"]: r for r in json.loads(files[blr.RECORD])["files"]}
    for k in range(8):
        octile = set(removed(files, f"edits/octile_{k}.json"))
        ctrl = removed(files, f"edits/control_{k}.json")
        assert len(ctrl) == 600 and len(set(ctrl)) == 600
        for g in v.units:
            assert sum(v.unit_of[r] == g for r in ctrl) == sum(v.unit_of[r] == g for r in octile)
        table = rec[f"edits/control_{k}.json"]["table"]
        assert len(set(ctrl) & octile) == sum(t["fill_from_inside"] for t in table.values())


def test_the_fill_branch_takes_the_shortfall_from_inside_the_octile(tmp_path):
    def target(i):
        return 1 if i < 600 else 2 + (i * 37) % 300                      # unit 0 is all short: it fills octile 0
    prep = fb.make_prepared(tmp_path / "p", target=target)
    files = blr.build(prep["root"], settings_for(prep), "e" * 64)
    v = view(prep)
    g0 = v.units[0]
    octile = set(removed(files, "edits/octile_0.json"))
    assert set(v.members[g0]) == octile
    ctrl = removed(files, "edits/control_0.json")
    assert set(ctrl) == set(v.members[g0])                              # 600 needed, 0 outside: all from inside
    table = json.loads(files[blr.RECORD])["files"][8]["table"]
    assert table[g0]["fill_from_inside"] == 600 and table[g0]["from_outside"] == 0


def test_the_fill_is_partial_when_a_category_is_mostly_inside(tmp_path):
    def target(i):
        if i < 600:                                                      # unit 0: 400 short rows, 200 long ones
            return 1 if i < 400 else 400
        return 2 + (i * 37) % 300
    prep = fb.make_prepared(tmp_path / "p", target=target)
    files = blr.build(prep["root"], settings_for(prep), "e" * 64)
    v = view(prep)
    g0 = v.units[0]
    octile = set(removed(files, "edits/octile_0.json"))
    n = sum(v.unit_of[r] == g0 for r in octile)
    ctrl = removed(files, "edits/control_0.json")
    outside = [r for r in v.members[g0] if r not in octile]
    assert n == 400 and set(outside) <= set(ctrl)                       # all 200 outside, then 200 from inside
    assert sum(1 for r in ctrl if r in octile and v.unit_of[r] == g0) == 2 * n - 600
    # the identity of the drawn rows: g0's fill is the sealed l8.control_fill (0, g0) sample of its inside rows; every
    # other unit's rows are the sealed l8.control (0, c) sample of its outside rows; the shared count is recorded
    inside_g0 = [r for r in v.members[g0] if r in octile]
    fill = s1.sealed_sample(inside_g0, 2 * n - 600, "l8.control_fill", 0, g0)
    assert {r for r in ctrl if v.unit_of[r] == g0} == set(outside) | set(fill) and len(fill) == 200
    table = json.loads(files[blr.RECORD])["files"][8]["table"]
    assert table[g0] == {"category": v.category[g0], "rows": 400, "from_outside": 200, "fill_from_inside": 200,
                         "shared_with_octile": 200}
    plain = 0
    for c in v.units[1:]:
        n_c = sum(v.unit_of[r] == c for r in octile)
        outside_c = [r for r in v.members[c] if r not in octile]
        assert n_c <= len(outside_c) and n_c > 0
        assert {r for r in ctrl if v.unit_of[r] == c} == set(s1.sealed_sample(outside_c, n_c, "l8.control", 0, c))
        assert table[c]["shared_with_octile"] == len(set(ctrl) & octile & set(v.members[c])) == 0
        assert table[c]["rows"] == table[c]["from_outside"] == n_c and table[c]["fill_from_inside"] == 0
        plain += 1
    assert plain == 7


def test_every_control_is_the_sealed_draw_on_its_own_label_and_parts(env):
    """Every control of the env fixture (no fill anywhere): the control's rows of unit c are the sealed l8.control
    (k, c) sample of c's rows outside octile k, and the recorded shared count is the true overlap."""
    files = files_of(env)
    v = view(env["prep"])
    rec = {r["file"]: r for r in json.loads(files[blr.RECORD])["files"]}
    checked = 0
    for k in range(8):
        octile = set(removed(files, f"edits/octile_{k}.json"))
        ctrl = set(removed(files, f"edits/control_{k}.json"))
        table = rec[f"edits/control_{k}.json"]["table"]
        for c in v.units:
            n_c = sum(1 for r in v.members[c] if r in octile)
            outside_c = [r for r in v.members[c] if r not in octile]
            assert n_c <= len(outside_c)
            assert {r for r in ctrl if v.unit_of[r] == c} == set(s1.sealed_sample(outside_c, n_c, "l8.control", k, c))
            assert table[c]["shared_with_octile"] == len(ctrl & octile & set(v.members[c])) == 0
            checked += 1
    assert checked == 64


def test_every_cut_point_and_the_roles_are_published(tmp_path):
    """On a fixture whose 4,800 target lengths are distinct, each octile's first and last published lengths are the
    order's rows 600k and 600k + 599; octile 7's role (and only its) names H2b, octile 0's H1."""
    prep = fb.make_prepared(tmp_path / "p", target=lambda i: 1 + (i * 7919) % 4800)
    files = blr.build(prep["root"], settings_for(prep), "e" * 64)
    v = view(prep)
    assert len(set(v.tokens.values())) == 4800
    rank = s1.sealed_rank(v.tokens, "length.order")
    order = sorted(v.tokens, key=lambda r: (v.tokens[r], rank[r]))
    cuts = json.loads(files[blr.RECORD])["cut_points"]
    assert [c["octile"] for c in cuts] == list(range(8))
    for k, c in enumerate(cuts):
        assert c["first_target_tokens"] == v.tokens[order[600 * k]] == 600 * k + 1
        assert c["last_target_tokens"] == v.tokens[order[600 * k + 599]] == 600 * k + 600
        assert removed(files, f"edits/octile_{k}.json") == sorted(order[600 * k:600 * (k + 1)])
    rec = {r["file"]: r for r in json.loads(files[blr.RECORD])["files"]}
    for k in range(8):
        role = rec[f"edits/octile_{k}.json"]["role"]
        assert role == json.loads(files[f"edits/octile_{k}.json"])["provenance"]["role"]
        assert ("H2b" in role) == (k == 7) and ("H1" in role) == (k == 0) and role.startswith(f"octile {k}")


# ----- H2a (L6) -------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def classify():
    return blr.h2a_rule(json.loads(blr.SETTINGS_PATH.read_bytes()))


@pytest.mark.parametrize("line", ["- x", "* x", "+ x", "• x", "•x", "1. x", "2) x", "10.Item", "1.Apple", "-", "8.", "8. A sentence"])
def test_item_alternatives_count(classify, line):
    assert classify(line)[1] == 1


@pytest.mark.parametrize("line", ["3.5 million", "-5 degrees", "*args", "+1 555", "2015. x", "1.5. x", "x - y", "(1) x", "a) x"])
def test_item_negatives(classify, line):
    assert classify(line)[1] == 0


@pytest.mark.parametrize("line", ["# H", "###### H", "#", "| a | b |", "**Bold** text", "---", "* * *", "___", "|:---|", ":---:|", "---|"])
def test_markup_alternatives(classify, line):
    assert classify(line)[2] == 1 and classify(line)[0]


@pytest.mark.parametrize("line", ["#tag", "####### seven", "** x", "--", "Normal line", "a | b", "x |", "either|or",
                                  "a - b - c", "-- x --"])
def test_markup_negatives(classify, line):
    assert classify(line)[2] == 0 and not classify(line)[0]


@pytest.mark.parametrize("line", ["use ``x`` here", "`a` and `b` or `c`", "``", "` ` `", "a `` b ` c"])
def test_fence_negatives(classify, line):
    assert classify(line)[3] == 0 and not classify(line)[0]


def test_the_row_rule_threshold_fence_and_splitter(classify):
    assert not classify("- one bullet")[0] and classify("- one\n- two")[0]                  # 1 ITEM: no; 2: yes
    assert not classify("- a")[0] and not classify("8.")[0] and not classify("- Name")[0]
    assert classify("x\n```\ncode")[0] and classify("inline ```code``` here")[0]
    assert classify("````")[3] == 1 and not classify("``\n``")[0] and not classify("plain | pipe\n``")[0]
    assert classify("- a\r\n- b")[0] and classify("- a - b")[0]                        # CRLF and U+2028
    assert not classify("3.5 million\n-5 degrees\n*args\n#tag\n+1 555\n2015. x\n1.5. x")[0]


def test_h2a_sample_branch(env):
    files = files_of(env)
    v = view(env["prep"])
    rec = next(r for r in json.loads(files[blr.RECORD])["files"] if r["file"] == "edits/h2a.json")
    marked = sorted(r for r, row in env["prep"]["rows"].items() if blr.h2a_rule(env["settings"])(row["response"])[0])
    assert rec["n_h2a_rows"] == len(marked) == 1440 and rec["branch"] == "sample"
    h2a = removed(files, "edits/h2a.json")
    assert set(h2a) <= set(marked) and h2a == sorted(s1.sealed_sample(marked, 600, "h2a.sample"))
    assert len(h2a) == 600 and set(h2a) <= set(v.tokens)


def test_the_second_read_of_the_training_rows_refuses_a_changed_file(tmp_path):
    prep = fb.make_prepared(tmp_path / "p", units=2, rows_per_unit=5)
    v = view(prep)
    classify = blr.h2a_rule(json.loads(blr.SETTINGS_PATH.read_bytes()))
    flags = blr.response_flags(prep["root"], v, classify)
    assert set(flags) == set(v.tokens) and not any(flags.values())
    path = prep["root"] / s1.TRAIN_ROWS
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(s1.Refusal, match="changed after the view read it"):
        blr.response_flags(prep["root"], v, classify)


def test_h2a_fill_branch(tmp_path):
    prep = fb.make_prepared(tmp_path / "p", response=lambda i: "- a\n- b" if i % 100 == 0 else f"Plain answer {i}.")
    settings = settings_for(prep)
    files = blr.build(prep["root"], settings, "e" * 64)
    rec = next(r for r in json.loads(files[blr.RECORD])["files"] if r["file"] == "edits/h2a.json")
    marked = sorted(r for r, row in prep["rows"].items() if row["response"].startswith("- a"))
    rest = sorted(set(prep["rows"]) - set(marked))
    assert rec["n_h2a_rows"] == 48 and rec["branch"] == "fill" and rec["fill"] == 552
    assert removed(files, "edits/h2a.json") == sorted(marked + s1.sealed_sample(rest, 552, "h2a.fill"))


# ----- files and settings ---------------------------------------------------------------------------


def test_every_edit_parses_and_nothing_holds_text(env):
    files = files_of(env)
    stub = view(env["prep"]).engine_stub()
    assert sorted(n for n in files if n.startswith("edits/")) == sorted(
        [f"edits/octile_{k}.json" for k in range(8)] + [f"edits/control_{k}.json" for k in range(8)] + ["edits/h2a.json"])
    for name, data in files.items():
        if name.startswith("edits/"):
            assert len(parse_edit(data, stub).removed) == 600
        assert b"Intro line" not in data and b"Heading" not in data and b"bullet" not in data


def test_deterministic(env):
    assert blr.build(env["prep"]["root"], env["settings"], "e" * 64) == files_of(env)


def test_the_settings_pin_l6_exactly():
    s = json.loads(blr.SETTINGS_PATH.read_bytes())
    assert s["h2a"]["item"] == r"^\s*(?:[-*+](?:\s|$)|•|[0-9]{1,3}[.)](?:\s|$|[^\W\d_]))"
    assert s["h2a"]["markup"] == r"^\s*(?:#{1,6}(?:\s|$)|\||\*\*\S|(?:[-*_]\s*){3,}$|:?-{3,}:?\s*\|)"
    assert (s["h2a"]["fence"], s["h2a"]["item_threshold"], s["h2a"]["splitter"]) == ("```", 2, "str.splitlines()")
    assert (s["length"]["octile_size"], s["length"]["octiles"], s["h2a"]["rows"]) == (600, 8, 600)


def test_the_settings_file_is_literal_pinned():
    doc, digest = s1.load_settings(blr.SETTINGS_PATH, blr.SETTINGS_SHA256, blr.SETTINGS_NAME)
    assert digest == "3800e52ae3c7f4fd2c886f14ba973b814c98b735d4d166f50a7fc133358de5b3"
    assert set(doc["label_entries"]) == {"length.order", "l8.control", "l8.control_fill", "h2a.sample", "h2a.fill"}
