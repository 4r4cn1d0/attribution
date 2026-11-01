"""D-1 (addendum section 18): the S3 subset size k, the new stop, the base file's checks, the record, on synthetic PKU
files and a synthetic prepared set (scripts/stage1/tests' fixtures). Expected k values are worked out by hand in the
docstrings of the choose_k cases, and by an independent brute force (d1fixtures.brute_k) on the worlds."""

from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.stage1 import build_s_pool as w1bsp
from scripts.stage1 import s1common as s1
from scripts.stage1_s1.d1_spool import d1_s_pool as d1m

import d1fixtures as dx
from d1guard import guarded


@pytest.fixture(scope="module")
def base():
    """Guarded (d1guard): a load_base defect fails the tests that use base, never errors their setup."""
    return guarded("base", lambda: d1m.load_base(dx.committed_d1()))


@pytest.fixture(scope="module")
def w20(tmp_path_factory):
    """N = 20 (all 20 candidates pass every filter): the 947-like case at small scale, the planned size 25 > N."""
    return dx.world_of(tmp_path_factory.mktemp("w20"), 20)


@pytest.fixture(scope="module")
def w40(tmp_path_factory):
    return dx.world_of(tmp_path_factory.mktemp("w40"), 40, seed=4)


def rec(result) -> dict:
    return json.loads(result[1][w1bsp.RECORD])


def pool_ids(result) -> list[str]:
    return [i["id"] for i in json.loads(result[0][w1bsp.POOL_FILE])["items"]]


# ----- the rule, by hand ------------------------------------------------------------------------------------------

ORDER = list("abcdefghij")
COVERED = {"a", "c", "h"}                      # S1 | S4 inside a pool of n = 10


@pytest.mark.parametrize("planned,decoy,k_min,expected", [
    # outside(j) for j = 0..10: 7 (a, c, h covered), a 7, b 6, c 6, d 5, e 4, f 3, g 2, h 2, i 1, j 0
    (25, 3, 1, {"k": 6, "outside_at_k": 3, "outside_at_k_plus_1": 2, "limit": 10, "largest_j_meeting_the_rule": 6}),
    # decoy 2: j = 7 (g) gives 2 and j = 8 (h, already covered) keeps 2, j = 9 gives 1: k = 8
    (25, 2, 1, {"k": 8, "outside_at_k": 2, "outside_at_k_plus_1": 1, "limit": 10, "largest_j_meeting_the_rule": 8}),
    # the planned size binds (the "1,000 when N is large enough" case): limit 4, outside(4) = 5 >= 3, k = 4, no k + 1
    (4, 3, 1, {"k": 4, "outside_at_k": 5, "outside_at_k_plus_1": None, "limit": 4, "largest_j_meeting_the_rule": 4}),
    # k_min 7 > 6: no k >= k_min meets the rule; outside(7) = 2
    (25, 3, 7, {"k": None, "outside_at_k": None, "outside_at_k_plus_1": None, "limit": 10,
                "largest_j_meeting_the_rule": 6, "outside_at_k_min": 2}),
    # decoy 8 > outside(0) = 7: no j at all
    (25, 8, 1, {"k": None, "largest_j_meeting_the_rule": None}),
    # decoy 0: every j meets it, k = min(planned, n) = 10
    (25, 0, 1, {"k": 10, "outside_at_k": 0, "outside_at_k_plus_1": None}),
])
def test_choose_k_by_hand(planned, decoy, k_min, expected):
    info = d1m.choose_k(ORDER, COVERED, 10, planned, decoy, k_min)
    assert {key: info[key] for key in expected} == expected


def test_choose_k_boundary_is_exact():
    """At k the room is >= decoy and at k + 1 it is < decoy (the largest k), for every decoy from 0 to 7."""
    for decoy in range(8):
        info = d1m.choose_k(ORDER, COVERED, 10, 25, decoy, 1)
        if info["k"] is None:
            continue
        assert info["outside_at_k"] >= decoy
        assert info["outside_at_k_plus_1"] is None or info["outside_at_k_plus_1"] < decoy


# ----- the build on synthetic worlds ----------------------------------------------------------------------------


def test_a_947_like_pool_gets_the_largest_k_and_the_w1_lists_otherwise(base, w20):
    """N = 20 < the planned 25 (as 947 < 1,000): k is the brute-force k, S1 and S4 are REQ-6's, S3 = the first k."""
    w1, d1 = dx.scaled(w20)
    res = dx.d1_build(w20, base, w1, d1)
    r, ids = rec(res), pool_ids(res)
    assert r["pool_rows"] == 20 == len(ids)
    k = dx.brute_k(ids, 3, 6, 25, 3)
    assert k is not None and 3 <= k < 20 and r["d1"]["k"] == k
    s1_ids = s1.sealed_order(ids, "s1.order")[:3]
    s4_ids = s1.sealed_order(sorted(set(ids) - set(s1_ids)), "s4.order")[:6]
    assert r["lists"]["s1"]["ids"] == s1_ids and r["lists"]["s4_candidates"]["ids"] == s4_ids
    assert r["lists"]["s3_subset"]["ids"] == s1.sealed_order(ids, "s3.subset")[:k]
    union = set(s1_ids) | set(s4_ids) | set(r["lists"]["s3_subset"]["ids"])
    assert r["d1"]["rows_outside_the_lists_at_k"] == 20 - len(union) == r["room"]["rows_outside_the_lists"] >= 3
    nxt = set(s1_ids) | set(s4_ids) | set(s1.sealed_order(ids, "s3.subset")[:k + 1])
    assert r["d1"]["rows_outside_the_lists_at_k_plus_1"] == 20 - len(nxt) < 3            # k is the largest
    assert json.loads(res[0]["s3_subset.json"])["items"][-1]["id"] == r["lists"]["s3_subset"]["ids"][-1]
    s3_pool = [i["id"] for i in json.loads(res[0][w1bsp.S3_POOL])["items"]]
    assert s3_pool == r["lists"]["s3_subset"]["ids"] + [i for i in s1_ids if i not in set(r["lists"]["s3_subset"]["ids"])]
    assert r["overlaps_l10"]["expected_s1_and_s3_subset"] == 3 * k / 20


def test_d1_at_k_equals_build_s_pool_with_size_k_byte_for_byte(base, w20):
    """D-1 changes only the S3 subset size and the stop: build_s_pool.py itself, with the subset size set to the same k
    and min_pool N, writes the same five full files; the record differs only in provenance and the d1 block."""
    w1, d1 = dx.scaled(w20)
    res = dx.d1_build(w20, base, w1, d1)
    k = rec(res)["d1"]["k"]
    w1k = copy.deepcopy(w1)
    w1k["lists"]["s3_subset"]["size"], w1k["min_pool"] = k, 20
    ref = dx.w1_build(w20, w1k)
    assert res[0] == ref[0]
    mine, theirs = rec(res), rec(ref)
    assert mine["d1"]["base_provenance"] == theirs["provenance"]
    for doc in (mine, theirs):
        doc.pop("provenance"), doc.pop("d1", None)
    assert mine == theirs


def test_k_is_the_planned_size_when_n_is_large_and_d1_reproduces_build_s_pool(base, w40):
    """N = 40, planned 6, S1 3, S4 4, decoy 2: k = 6 = the planned size, and every full file is byte-identical to
    build_s_pool.py's own build with REQ-6's settings unchanged (here min_pool 6 <= N)."""
    w1, d1 = dx.scaled(w40, s1n=3, s3=6, s4=4, decoy=2, k_min=3)
    res = dx.d1_build(w40, base, w1, d1)
    r = rec(res)
    assert r["d1"]["k"] == 6 == r["d1"]["planned_s3_subset_size"] and r["d1"]["rows_outside_the_lists_at_k_plus_1"] is None
    w1["min_pool"] = 6
    ref = dx.w1_build(w40, w1)
    assert res[0] == ref[0]
    theirs = rec(ref)
    assert r["d1"]["base_provenance"] == theirs["provenance"]
    assert {k: v for k, v in r.items() if k not in ("provenance", "d1")} == \
        {k: v for k, v in theirs.items() if k != "provenance"}


def test_the_rule_at_the_committed_sizes_on_synthetic_ids(base):
    """The committed settings (48, 1,000, 512, 37) on synthetic ids: N = 1,600 gives k = 1,000 and build_s_pool's own
    lists; N = 947 the brute-force k (< 1,000); N = 1,000 also a k < 1,000, where build_s_pool's own stop fires; N = 596
    and N = 597 stop."""
    d1 = dx.committed_d1()
    w1 = base.settings
    d1m.check_consistency(w1, d1)
    for n in (1600, 1000, 947):
        ids = [f"pku_one:{i:06d}:1" for i in range(1, n + 1)]
        lists, info = d1m.d1_lists(ids, w1, d1, w1bsp.lists_of)
        assert info["k"] == dx.brute_k(ids, 48, 512, 1000, 37)
        assert len(lists["s1"]) == 48 and len(lists["s4_candidates"]) == 512
        room = d1m.d1_stop(n, lists, w1, d1, info, "counts")
        assert room["rows_outside_the_lists"] >= 37 and room["decoy_rows_needed"] == 37
        if n == 1600:
            assert info["k"] == 1000 and lists == w1bsp.lists_of(ids, w1)
        else:
            assert 600 <= info["k"] < 1000
            with pytest.raises(s1.Refusal, match="cannot fill its lists"):
                w1bsp.check_sizes(n, w1bsp.lists_of(ids, w1), w1)
    for n in (596, 597):
        ids = [f"pku_one:{i:06d}:1" for i in range(1, n + 1)]
        lists, info = d1m.d1_lists(ids, w1, d1, w1bsp.lists_of)
        with pytest.raises(s1.Refusal, match=f"N = {n} "):
            d1m.d1_stop(n, lists, w1, d1, info, "counts")


# ----- the stop ---------------------------------------------------------------------------------------------------


def test_the_stop_below_min_pool_gives_counts_only(base, tmp_path):
    """N = 11 < min_pool 12 (= 3 + 6 + 3, as 597 = 48 + 512 + 37): the stop names N after each filter and the counts
    by reason, no id and no text."""
    w = dx.world_of(tmp_path, 11)
    w1, d1 = dx.scaled(w)
    with pytest.raises(s1.Refusal, match=r"D-1: the S-pool cannot fill its lists: N = 11 \(D-1 min_pool 12\)") as stop:
        dx.d1_build(w, base, w1, d1)
    message = str(stop.value)
    assert all(stage in message for stage in w1bsp.FILTERS) and "'candidates': 11" in message
    assert "nothing written" in message and "pku_one:" not in message
    assert not any(t.encode() in message.encode() for t in w.texts())
    assert not isinstance(stop.value, d1m.FallbackTrigger)


def test_the_min_pool_boundary_is_exact():
    """N = min_pool passes the N test (it stops only if k fails), N = min_pool - 1 stops; S1 or S4 short stops."""
    w1 = dx.committed_w1()
    d1 = dx.committed_d1()
    d1["fallback"]["k_below"] = 1
    lists = {"s1": [f"a{i}" for i in range(48)], "s3_subset": [f"a{i}" for i in range(48)],
             "s4_candidates": [f"b{i}" for i in range(512)]}
    info = {"k": 48, "limit": 597, "largest_j_meeting_the_rule": 48, "outside_at_k": 37, "outside_at_k_plus_1": 36,
            "outside_at_k_min": 37}
    assert d1m.d1_stop(597, lists, w1, d1, info, "c") == {"rows_outside_the_lists": 37, "decoy_rows_needed": 37}
    with pytest.raises(s1.Refusal, match=r"N = 596 \(D-1 min_pool 597\)"):
        d1m.d1_stop(596, lists, w1, d1, {**info, "outside_at_k": 36}, "c")
    short = {**lists, "s4_candidates": lists["s4_candidates"][:511]}
    with pytest.raises(s1.Refusal, match=r"short lists \{'s4_candidates': 511\}"):
        d1m.d1_stop(597, short, w1, d1, {**info, "outside_at_k": 38}, "c")
    with pytest.raises(s1.Refusal, match=r"short lists \{'s1': 47\}"):
        d1m.d1_stop(597, {**lists, "s1": lists["s1"][:47]}, w1, d1, info, "c")
    with pytest.raises(s1.Refusal, match="disagree with the k computation"):
        d1m.d1_stop(597, lists, w1, d1, {**info, "outside_at_k": 38}, "c")


def test_no_k_at_least_k_min_stops(base, w20):
    """The same world with k_min one above the largest k that meets the room rule: a counts-only stop."""
    w1, d1 = dx.scaled(w20)
    ids = pool_ids(dx.d1_build(w20, base, w1, d1))
    best = dx.brute_k(ids, 3, 6, 25, 3)
    w1, d1 = dx.scaled(w20, k_min=best + 1)
    with pytest.raises(s1.Refusal, match=rf"k = None \(the largest k <= 20 with at least 3 rows outside S1, the first "
                                         rf"k of s3.subset and S4 is {best}; k_min {best + 1};") as stop:
        dx.d1_build(w20, base, w1, d1)
    assert "nothing written" in str(stop.value)
    w1, d1 = dx.scaled(w20, k_min=best)                                  # k_min = k passes
    assert rec(dx.d1_build(w20, base, w1, d1))["d1"]["k"] == best


def test_the_fallback_trigger_is_k_below_the_threshold(base, w20):
    """Section 18 point 7: k < 600 (here k_below = k + 1) stops with FallbackTrigger; k_below = k passes."""
    w1, d1 = dx.scaled(w20)
    k = rec(dx.d1_build(w20, base, w1, d1))["d1"]["k"]
    w1, d1 = dx.scaled(w20, k_below=k + 1)
    with pytest.raises(d1m.FallbackTrigger, match=rf"k = {k} < {k + 1}, addendum section 18 point 7"):
        dx.d1_build(w20, base, w1, d1)
    w1, d1 = dx.scaled(w20, k_below=k)
    assert rec(dx.d1_build(w20, base, w1, d1))["d1"]["k"] == k


@pytest.mark.parametrize("change,match", [
    (lambda w1, d1: d1.__setitem__("min_pool", d1["min_pool"] + 1), "min_pool"),
    (lambda w1, d1: d1.__setitem__("planned_s3_subset_size", 24), "planned S3 subset size"),
    (lambda w1, d1: d1.__setitem__("k_min", 0), "k_min is not a positive integer"),
    (lambda w1, d1: d1.__setitem__("k_min", True), "k_min is not a positive integer"),
    (lambda w1, d1: d1.__setitem__("k_min", 26), "k_min exceeds"),
    (lambda w1, d1: d1["fallback"].__setitem__("k_below", 0), "fallback.k_below"),
    (lambda w1, d1: w1["lists"]["s3_subset"].__setitem__("key", "s4.order"), "S3 subset key"),
    (lambda w1, d1: d1.__setitem__("name", "build_s_pool"), "not the stage-1 settings 'd1_s_pool'"),
])
def test_inconsistent_settings_refuse(base, w20, change, match):
    w1, d1 = dx.scaled(w20)
    change(w1, d1)
    with pytest.raises(s1.Refusal, match=match):
        dx.d1_build(w20, base, w1, d1)


# ----- the base file and the settings, by SHA-256 -------------------------------------------------------------------


def _fake_root(tmp_path, d1):
    """A copy of the three files load_base reads, under a tmp root."""
    real = d1m.w1_root()
    for rel in (d1["base"]["manifest"], d1["base"]["script"], d1["base"]["settings"]):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(real / rel, tmp_path / rel)
    return tmp_path


def _flip(path: Path, needle: bytes, new: bytes, every: bool = False):
    data = path.read_bytes()
    assert data.count(needle) >= 1
    path.write_bytes(data.replace(needle, new) if every else data.replace(needle, new, 1))


def test_a_changed_build_s_pool_byte_refuses(tmp_path):
    d1 = dx.committed_d1()
    root = _fake_root(tmp_path, d1)
    _flip(root / d1["base"]["script"], b"[:sizes[\"s3_subset\"][\"size\"]]", b"[:sizes[\"s3_subset\"][\"size\"]-1]")
    with pytest.raises(s1.Refusal, match="build_s_pool.py hashes to"):
        d1m.load_base(d1, root)


def test_a_changed_build_s_pool_settings_byte_refuses(tmp_path):
    d1 = dx.committed_d1()
    root = _fake_root(tmp_path, d1)
    _flip(root / d1["base"]["settings"], b'"min_pool": 1000', b'"min_pool": 1001')
    with pytest.raises(s1.Refusal, match="build_s_pool.json hashes to"):
        d1m.load_base(d1, root)


def test_a_manifest_or_pin_disagreement_refuses(tmp_path):
    d1 = dx.committed_d1()
    root = _fake_root(tmp_path, d1)
    manifest = root / d1["base"]["manifest"]
    _flip(manifest, d1["base"]["script_sha256"].encode(), b"0" * 64, every=True)
    with pytest.raises(s1.Refusal, match="build_s_pool.py: the W1 manifest names 0000"):
        d1m.load_base(d1, root)
    d2 = copy.deepcopy(d1)
    d2["base"]["settings_sha256"] = "1" * 64
    with pytest.raises(s1.Refusal, match="build_s_pool.json: the W1 manifest names 6080487c"):
        d1m.load_base(d2, d1m.w1_root())
    manifest.write_bytes(b'{"kind": "other", "entries": []}')
    with pytest.raises(s1.Refusal, match="not the stage-1 W1 commitments manifest"):
        d1m.load_base(d1, root)


def test_a_settings_file_that_build_s_pool_does_not_pin_refuses(tmp_path):
    """Even when the manifest entry and the D-1 pin agree on other settings bytes, build_s_pool.py's own literal pin
    (SETTINGS_SHA256 = 6080487c...) must name them."""
    d1 = copy.deepcopy(dx.committed_d1())
    root = _fake_root(tmp_path, d1)
    settings = root / d1["base"]["settings"]
    _flip(settings, b'"min_pool": 1000', b'"min_pool": 1001')
    other = sha256_file(settings)
    _flip(root / d1["base"]["manifest"], d1["base"]["settings_sha256"].encode(), other.encode(), every=True)
    d1["base"]["settings_sha256"] = other
    saved = list(sys.path)                     # the base module, run from the tmp copy, puts its root on sys.path
    try:
        with pytest.raises(s1.Refusal, match="own settings pin"):
            d1m.load_base(d1, root)
    finally:
        sys.path[:] = saved


def test_a_record_that_would_hold_text_refuses(base, w20):
    """The final text scan covers the d1 block: a rule text that equals a pool prompt refuses."""
    w1, d1 = dx.scaled(w20)
    prompt = json.loads(dx.d1_build(w20, base, w1, d1)[0][w1bsp.POOL_FILE])["items"][0]["prompt"]
    d1["rule"] = prompt
    with pytest.raises(s1.Refusal, match="the record would hold text"):
        dx.d1_build(w20, base, w1, d1)


def test_the_loaded_base_is_private_and_restored(base, w20):
    """The base module runs from the checked bytes, is not in sys.modules, and its two functions are restored after a
    build and after a refusal; the normally imported W1 module is never touched."""
    assert base.module.__name__ == "stage1_d1_build_s_pool" and base.module.__name__ not in sys.modules
    assert base.module is not w1bsp and Path(base.module.__file__) == Path(w1bsp.__file__)
    originals = (base.module.lists_of, base.module.check_sizes, w1bsp.lists_of, w1bsp.check_sizes)
    w1, d1 = dx.scaled(w20)
    dx.d1_build(w20, base, w1, d1)
    w1, d1 = dx.scaled(w20, k_min=21)
    with pytest.raises(s1.Refusal):
        dx.d1_build(w20, base, w1, d1)
    assert (base.module.lists_of, base.module.check_sizes, w1bsp.lists_of, w1bsp.check_sizes) == originals
    assert base.script_sha256 == sha256_file(Path(w1bsp.__file__)) == dx.committed_d1()["base"]["script_sha256"]


def test_the_committed_settings():
    doc, digest = s1.load_settings(d1m.SETTINGS_PATH, d1m.SETTINGS_SHA256, d1m.SETTINGS_NAME)
    assert digest == sha256_file(d1m.SETTINGS_PATH) == d1m.SETTINGS_SHA256
    assert (doc["planned_s3_subset_size"], doc["k_min"], doc["min_pool"], doc["fallback"]["k_below"]) == (1000, 48, 597, 600)
    entries, _ = d1m.manifest_entries(d1m.w1_root() / doc["base"]["manifest"])
    assert entries[doc["base"]["script"]] == doc["base"]["script_sha256"] == \
        "cb2ca385a3917d0f4be041ae08b1e121bc67f82a7fc95165e33550f053f463df"
    assert entries[doc["base"]["settings"]] == doc["base"]["settings_sha256"] == w1bsp.SETTINGS_SHA256
    w1 = dx.committed_w1()
    d1m.check_consistency(w1, doc)
    assert w1["lists"]["s1"]["size"] + w1["lists"]["s4_candidates"]["size"] + w1["decoy_rows"] == 597
    assert doc["label_entries"] == w1["label_entries"]
    assert "section 18" in doc["reference"] and "k <= planned_s3_subset_size (1,000)" in doc["rule"]
    assert doc["owner"] == "scripts/stage1_s1/d1_spool/d1_s_pool.py"


def test_every_w1_file_under_scripts_stage1_is_byte_identical():
    """Section 18 point 1: the manifest's entries under scripts/stage1/ hash to their pins (the workspace has no git
    repository for commitments.py check, so this is the byte part of that check)."""
    root = d1m.w1_root()
    data = json.loads((root / dx.committed_d1()["base"]["manifest"]).read_bytes())
    entries = [e for e in data["entries"] if e["path"].startswith("scripts/stage1/")]
    assert len(entries) > 100
    changed = [e["path"] for e in entries if sha256_file(root / e["path"]) != e["sha256"]]
    assert changed == []


# ----- the record -----------------------------------------------------------------------------------------------


def test_the_record_fields_and_text_freeness(base, w20):
    w1, d1 = dx.scaled(w20)
    res = dx.d1_build(w20, base, w1, d1, d1_sha256="d" * 64)
    r = rec(res)
    d = r["d1"]
    assert r["kind"] == "stage1 s-pool record" and set(res[1]) == {w1bsp.RECORD}
    assert set(d) == {"deviation", "reference", "decision", "rule", "stop", "planned_s3_subset_size", "N", "k",
                      "k_limit", "rows_outside_the_lists_at_k", "rows_outside_the_lists_at_k_plus_1", "decoy_rows",
                      "k_min", "min_pool", "fallback", "list_sizes", "build_s_pool_sha256",
                      "build_s_pool_settings_sha256", "w1_manifest_sha256", "settings_sha256", "base_provenance"}
    assert (d["deviation"], d["planned_s3_subset_size"], d["N"], d["k_limit"], d["decoy_rows"], d["k_min"],
            d["min_pool"]) == ("D-1", 25, 20, 20, 3, 3, 12)
    assert d["list_sizes"] == {"s1": 3, "s3_subset": d["k"], "s4_candidates": 6}
    assert d["fallback"] == {"k_below": 1, "triggered": False}
    assert d["rule"] == d1["rule"] and d["reference"] == d1["reference"] and "section 18" in d["reference"]
    assert d["build_s_pool_sha256"] == d1["base"]["script_sha256"] and d["settings_sha256"] == "d" * 64
    assert d["build_s_pool_settings_sha256"] == "e" * 64                 # the world's REQ-6 settings, as passed
    assert d["w1_manifest_sha256"] == base.manifest_sha256
    prov = r["provenance"]
    # the repository-relative path in the workspace (s1.rel; an absolute path under the mutation runner's copy)
    assert prov["script"] == s1.rel(Path(d1m.__file__)) and prov["script"].endswith("scripts/stage1_s1/d1_spool/d1_s_pool.py")
    assert prov["settings_sha256"] == "d" * 64
    assert prov["script_sha256"] == sha256_file(Path(d1m.__file__))
    assert prov["inputs"]["build_s_pool"] == d1["base"]["script_sha256"]
    assert prov["inputs"]["w1_manifest"] == base.manifest_sha256
    assert {k: v for k, v in prov["inputs"].items() if k not in ("build_s_pool", "build_s_pool_settings", "w1_manifest")} \
        == d["base_provenance"]["inputs"]
    assert d["base_provenance"]["script"] == "scripts/stage1/build_s_pool.py"
    assert r["full_files"] == {name: sha256_bytes(data) for name, data in sorted(res[0].items())}
    data = res[1][w1bsp.RECORD]
    assert data == canonical_json(r)
    for t in w20.texts():
        assert t.encode() not in data
    assert all(t.encode() not in data for t in w20.anchors)


def test_deterministic(base, w20):
    w1, d1 = dx.scaled(w20)
    assert dx.d1_build(w20, base, w1, d1) == dx.d1_build(w20, base, w1, d1)


# ----- main(): the pinned settings, nothing written on a stop -------------------------------------------------------


def _argv(tmp_path, settings: Path, full="full", out="out") -> list[str]:
    p = str(tmp_path / "absent")
    return ["--config", p, "--sources", p, "--prepared", p, "--anchors", p, "--rec", p,
            "--full-out", str(tmp_path / "tmp" / full), "--out", str(tmp_path / out), "--settings", str(settings)]


def _main_world(monkeypatch, tmp_path, base, world, **scale):
    """main() on a synthetic world: D-1's scaled settings in a file whose SHA-256 the module pin is set to, the base
    module with the world's REQ-6 settings, the fixture codec; the CLI paths are the world's."""
    w1, d1 = dx.scaled(world, **scale)
    path = tmp_path / "d1_settings.json"
    path.write_bytes(canonical_json(d1))
    monkeypatch.setattr(d1m, "SETTINGS_SHA256", sha256_file(path))
    monkeypatch.setattr(d1m, "load_base", lambda d1_doc, root=None: dx.with_settings(base, w1))
    monkeypatch.setattr(base.module, "real_codec", lambda *a, **k: world.sfx.fixture_codec())
    argv = ["--config", str(world.config_path), "--sources", str(world.sources_root), "--prepared",
            str(world.prepared_root), "--anchors", str(world.anchors_path), "--rec", str(world.recipe_path),
            "--full-out", str(tmp_path / "tmp" / "full"), "--out", str(tmp_path / "out"), "--settings", str(path)]
    return argv, w1, d1, sha256_file(path)


def test_main_writes_the_build_outputs(base, w20, tmp_path, monkeypatch, capsys):
    argv, w1, d1, digest = _main_world(monkeypatch, tmp_path, base, w20)
    assert d1m.main(argv) == 0
    full, record = dx.d1_build(w20, base, w1, d1, d1_sha256=digest)
    assert {p.name: p.read_bytes() for p in (tmp_path / "tmp" / "full").iterdir()} == full
    assert (tmp_path / "out" / w1bsp.RECORD).read_bytes() == record[w1bsp.RECORD]
    out = capsys.readouterr().out
    k = json.loads(record[w1bsp.RECORD])["d1"]["k"]
    assert f"D-1: N = 20; k = {k} (planned 25)" in out and sha256_bytes(record[w1bsp.RECORD]) in out


def test_main_stop_writes_nothing(base, tmp_path, monkeypatch, capsys):
    w = dx.world_of(tmp_path / "w", 11)
    argv, *_ = _main_world(monkeypatch, tmp_path, base, w)
    assert d1m.main(argv) == 2
    err = capsys.readouterr().err
    assert "REFUSED: D-1: the S-pool cannot fill its lists: N = 11" in err and err.rstrip().endswith("(nothing written)")
    assert not any(p.is_file() for p in tmp_path.joinpath("tmp").rglob("*"))
    assert not (tmp_path / "out").exists() or not any((tmp_path / "out").iterdir())


def test_main_fallback_trigger_exits_3_and_writes_nothing(base, w20, tmp_path, monkeypatch, capsys):
    argv, *_ = _main_world(monkeypatch, tmp_path, base, w20, k_below=10 ** 6)
    assert d1m.main(argv) == d1m.EXIT_FALLBACK == 3
    err = capsys.readouterr().err
    assert err.startswith("FALLBACK: D-1: k = ") and "point 7" in err and err.rstrip().endswith("(nothing written)")
    assert not any(p.is_file() for p in tmp_path.joinpath("tmp").rglob("*"))


def test_main_refuses_a_changed_settings_byte(tmp_path, capsys):
    copy_path = tmp_path / "d1_s_pool.json"
    copy_path.write_bytes(d1m.SETTINGS_PATH.read_bytes().replace(b'"k_min": 48', b'"k_min": 47'))
    assert d1m.main(_argv(tmp_path, copy_path)) == 2
    err = capsys.readouterr().err
    assert "settings d1_s_pool hash to" in err and "(nothing written)" in err and not (tmp_path / "tmp").exists()


def test_main_refuses_a_non_empty_output_folder_before_the_build(tmp_path, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(d1m, "build", lambda **kw: calls.append(kw))
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "earlier.json").write_bytes(b"{}")
    assert d1m.main(_argv(tmp_path, d1m.SETTINGS_PATH)) == 2 and not calls
    err = capsys.readouterr().err
    assert "exists and is not empty" in err and "(nothing written)" in err
    outside = _argv(tmp_path, d1m.SETTINGS_PATH, out="out2")
    outside[outside.index("--full-out") + 1] = "/var/stage1-d1-full"
    assert d1m.main(outside) == 2 and not calls and "named tmp" in capsys.readouterr().err
