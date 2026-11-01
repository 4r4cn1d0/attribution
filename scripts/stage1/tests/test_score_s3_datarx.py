"""REQ-11 (S3, DataRx-style) and write_score_add.py, on synthetic REQ-3, REQ-6 and REQ-9 outputs, and once through the
real REQ-3 pass (the engine's fixture) with the pools s3_safe and s3_orig."""

from __future__ import annotations

import copy
import json
import math
import random

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1 import score_s3_datarx as s3
from scripts.stage1 import write_score_add as wsa

import s1fixtures_b3b as fw

pytest.importorskip("torch")
import test_representation_pass as trp  # noqa: E402  (its env fixture: the engine's fixture prepared set)

env = trp.env

N = 4
PIN = json.loads(s3.SETTINGS_PATH.read_bytes())["pins"]["representation_pass_settings_sha256"]


def write(path, data: bytes):
    path.write_bytes(data)
    return path, sha256_bytes(data)


def line(rid, source, cs, ch):
    """A REQ-3 row whose read (a) cosines at index l are cs[l] and ch[l] (index 0 too)."""
    return {"id": rid, "source": source, "unit": None, "n_prompt": 3, "n_tokens": 9,
            "cos_safe": [[cs[l], 0.0, 0.0, 0.0] for l in range(N + 1)],
            "cos_harmful": [[ch[l], 0.0, 0.0, 0.0] for l in range(N + 1)], "css": [0.0] * (N + 1)}


class World:
    def __init__(self, root, seed=3, subset=10, drop_orig=("c-03",), equal=(), swap=False, orig_is_safe=False):
        rng = random.Random(seed)
        self.root = root
        self.subset = [f"c-{k:02d}" for k in range(subset)]
        self.s1 = ["c-01", "c-02", "x-99"]                                    # x-99: S1 outside the subset
        ids = self.subset + ["x-99"]
        self.values = {}
        for k, rid in enumerate(ids):
            safe = (1e6, *[rng.uniform(-0.5, 0.5) for _ in range(N)])         # index 0 is never read
            harm = (-1e6, *[rng.uniform(-0.5, 0.5) for _ in range(N)])
            o_safe = (5e5, *[rng.uniform(-0.5, 0.5) for _ in range(N)])
            o_harm = (-5e5, *[rng.uniform(-0.5, 0.5) for _ in range(N)])
            if rid in equal:
                safe, harm, o_safe, o_harm = (0.0, 5.0, 5.0, 5.0, 5.0), (0.0,) * 5, (0.0,) * 5, (0.0,) * 5   # SAS 5
            if orig_is_safe:
                o_safe, o_harm = safe, harm
            if swap:
                safe, harm, o_safe, o_harm = harm, safe, o_harm, o_safe
            self.values[rid] = (safe, harm, o_safe, o_harm)
        lines = []
        for rid in ids:
            safe, harm, o_safe, o_harm = self.values[rid]
            lines.append(line(rid, "s3_safe", safe, harm))
            if rid not in drop_orig:
                lines.append(line(f"{rid}:orig", "s3_orig", o_safe, o_harm))
        self.drop = drop_orig
        rows = b"".join(json.dumps(l, sort_keys=True).encode() + b"\n" for l in lines)
        self.rows = write(root / "rows.jsonl", rows)
        self.safe_sha, self.orig_sha = sha256_bytes(b"safe pool"), sha256_bytes(b"orig pool")
        summary = {"kind": "stage1 representation pass", "layout": {"n_layers": N}, "rows": {"sha256": self.rows[1]},
                   "provenance": {"settings_sha256": PIN},
                   "pools": [{"name": "s3_safe", "sha256": self.safe_sha}, {"name": "s3_orig", "sha256": self.orig_sha}]}
        self.summary = write(root / "summary.json", canonical_json(summary))
        pool_rec = {"kind": "stage1 s-pool record", "s3_pool": {"sha256": self.safe_sha},
                    "lists": {"s3_subset": {"ids": self.subset}, "s1": {"ids": self.s1}}}
        self.pool_rec = write(root / "pool_record.json", canonical_json(pool_rec))
        rows9 = [{"id": rid, "lex_class": "REFUSAL-OPENING" if k % 4 == 0 else "DIRECT", "capped": k % 5 == 0,
                  "encode_train": "NoTargets" if rid in drop_orig else None} for k, rid in enumerate(ids)]
        ans = {"kind": "stage1 untuned answers record", "lists": {"s3": {"list_sha256": self.safe_sha,          # RB-1
                                                                        "s3_orig_pool_sha256": self.orig_sha, "rows": rows9}}}
        self.ans_rec = write(root / "answers_record.json", canonical_json(ans))

    def expected(self, rid):
        safe, harm, o_safe, o_harm = self.values[rid]
        r_safe = math.fsum(safe[l] - harm[l] for l in range(1, N + 1)) / N
        r_orig = math.fsum(o_safe[l] - o_harm[l] for l in range(1, N + 1)) / N
        return r_safe - r_orig

    def build(self, settings=None):
        files = s3.build(rows=self.rows, summary=self.summary, s_pool_record=self.pool_rec, answers_record=self.ans_rec,
                         settings=settings or json.loads(s3.SETTINGS_PATH.read_bytes()), settings_sha256="e" * 64)
        return json.loads(files[s3.OUTPUT]), files


def test_sas_by_hand_over_indices_1_to_n(tmp_path):
    w = World(tmp_path)
    doc, _ = w.build()
    assert set(doc["scores"]) == set(w.subset) - {"c-03"}
    for rid, value in doc["scores"].items():
        assert value == pytest.approx(w.expected(rid), abs=1e-12)
    assert doc["reports"]["leaving_the_ranking"] == {"count": 1, "ids": ["c-03"], "by_reason": {"NoTargets": 1}}
    assert doc["reports"]["s1_and_s3_subset"] == 2 and set(doc["reports"]["s1_sas"]) == set(w.s1)
    assert doc["reports"]["s1_sas"]["x-99"] == pytest.approx(w.expected("x-99"))
    assert doc["reports"]["y_orig_refusal_opening_share"] == 3 / 10 and doc["reports"]["y_orig_capped"] == 2


def test_swapping_the_anchor_sets_flips_every_layer_and_sas(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    a, _ = World(tmp_path / "a").build()
    b, _ = World(tmp_path / "b", swap=True).build()
    for rid in a["scores"]:
        assert b["per_layer"][rid]["safe"] == [-x for x in a["per_layer"][rid]["safe"]]
        assert b["scores"][rid] == pytest.approx(-a["scores"][rid], abs=1e-12)


def test_y_orig_equal_to_y_safe_gives_sas_zero_exactly(tmp_path):
    doc, _ = World(tmp_path, orig_is_safe=True).build()
    assert all(v == 0.0 for v in doc["scores"].values())


def test_a_recomputation_from_the_saved_layers_gives_the_same_selection(tmp_path):
    w = World(tmp_path)
    doc, files = w.build()
    recomputed = {i: s3.sas_of(v["safe"], v["orig"]) for i, v in doc["per_layer"].items()}
    assert recomputed == doc["scores"]
    assert s1.select_top(recomputed, 4, "s3.ties") == s1.select_top(doc["scores"], 4, "s3.ties")


@pytest.mark.parametrize("change,match", [
    (lambda w: w.__setattr__("rows", (w.rows[0], "0" * 64)), "hashes to"),
    (lambda w: w.__setattr__("pool_rec", write(w.root / "pr.json", canonical_json(
        {"kind": "stage1 s-pool record", "s3_pool": {"sha256": "1" * 64},
         "lists": {"s3_subset": {"ids": w.subset}, "s1": {"ids": w.s1}}}))), "pool s3_safe"),
    (lambda w: w.__setattr__("ans_rec", write(w.root / "ar.json", canonical_json(
        {"kind": "stage1 untuned answers record", "lists": {"s3": {"list_sha256": w.safe_sha, "s3_orig_pool_sha256": "2" * 64,
                                                                   "rows": []}}}))), "pool s3_orig"),
    (lambda w: w.__setattr__("ans_rec", write(w.root / "ar2.json", canonical_json(                    # RB-1
        {"kind": "stage1 untuned answers record", "lists": {"s3": {"list_sha256": "3" * 64, "s3_orig_pool_sha256": w.orig_sha,
                                                                   "rows": []}}}))), "not REQ-6's s3_safe pool"),
    (lambda w: w.__setattr__("ans_rec", write(w.root / "ar3.json", canonical_json(                    # RB-1: no field
        {"kind": "stage1 untuned answers record", "lists": {"s3": {"s3_orig_pool_sha256": w.orig_sha, "rows": []}}}))),
     "not REQ-6's s3_safe pool"),
])
def test_the_input_chain_refuses(tmp_path, change, match):
    w = World(tmp_path)
    change(w)
    with pytest.raises(s1.Refusal, match=match):
        w.build()


def test_another_req3_settings_refuses(tmp_path):
    s = copy.deepcopy(json.loads(s3.SETTINGS_PATH.read_bytes()))
    s["pins"]["representation_pass_settings_sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="pinned REQ-3 settings"):
        World(tmp_path).build(s)


# ----- write_score_add -----------------------------------------------------------------------------------------------


def candidates(w, extra=()):
    rng = random.Random(9)
    items = [{"id": rid, "prompt": fw.sentence(rng), "response": fw.REFUSAL + fw.sentence(rng, 3)}
             for rid in w.subset + ["x-99", *extra]]
    path = w.root / "s3_safe.pool.json"
    path.write_bytes(canonical_json({"kind": "stage1 text pool", "version": 1, "name": "s3_safe", "items": items}))
    return (path, sha256_file(path)), items


def add_settings(k=4):
    s = copy.deepcopy(json.loads(wsa.SETTINGS_PATH.read_bytes()))
    s["scorers"]["s3"]["k"] = k
    return s


def scores_file(w, doc, cand_sha):
    doc = dict(doc, candidate_pool_sha256=cand_sha)
    return write(w.root / "s3_scores.json", canonical_json(doc))


def test_the_top_k_list_with_sealed_ties(tmp_path):
    w = World(tmp_path, equal=("c-04", "c-05", "c-06", "c-07"))             # four equal SAS (5.0), the largest
    doc, _ = w.build()
    cand, items = candidates(w)
    full, rec = wsa.build(scorer="s3", scores=scores_file(w, doc, cand[1]), candidates=cand, settings=add_settings(3),
                          settings_sha256="e" * 64)
    listing = json.loads(full["s3.json"])
    expected = s1.select_top(doc["scores"], 3, "s3.ties")
    assert [i["id"] for i in listing["items"]] == expected and listing["name"] == "s3" and len(listing["items"]) == 3
    by_id = {i["id"]: i for i in items}
    assert all(i["prompt"] == by_id[i["id"]]["prompt"] and i["response"] == by_id[i["id"]]["response"] for i in listing["items"])
    record = json.loads(rec["s3_add_selection.json"])
    assert record["boundary_ties"] == {"kth_score": record["scores"][expected[-1]], "tied_selected": 3, "tied_not_selected": 1}
    ranks = s1.sealed_rank(doc["scores"], "s3.ties")
    assert expected == sorted(["c-04", "c-05", "c-06", "c-07"], key=lambda r: ranks[r])[:3]
    for item in items:
        assert item["prompt"].encode() not in rec["s3_add_selection.json"]


def test_write_score_add_refuses_a_mismatched_pool_or_a_missing_id(tmp_path):
    w = World(tmp_path)
    doc, _ = w.build()
    cand, _ = candidates(w)
    with pytest.raises(s1.Refusal, match="not the pool"):
        wsa.build(scorer="s3", scores=scores_file(w, doc, "0" * 64), candidates=cand, settings=add_settings(),
                  settings_sha256="e" * 64)
    path = w.root / "small.json"
    path.write_bytes(canonical_json({"kind": "stage1 text pool", "version": 1, "name": "s3_safe",
                                     "items": [{"id": "c-00", "prompt": "p", "response": "r"}]}))
    small = (path, sha256_file(path))
    with pytest.raises(s1.Refusal, match="not in the candidate file"):
        wsa.build(scorer="s3", scores=scores_file(w, doc, small[1]), candidates=small, settings=add_settings(),
                  settings_sha256="e" * 64)
    with pytest.raises(s1.Refusal, match="no scorer"):
        wsa.build(scorer="s9", scores=scores_file(w, doc, cand[1]), candidates=cand, settings=add_settings(),
                  settings_sha256="e" * 64)


def test_the_committed_settings():
    doc, digest = s1.load_settings(wsa.SETTINGS_PATH, wsa.SETTINGS_SHA256, wsa.SETTINGS_NAME)
    assert doc["scorers"]["s3"]["k"] == 48 and doc["scorers"]["s3"]["ties"] == "s3.ties" and doc["scorers"]["s3"]["list_name"] == "s3"
    sdoc, _ = s1.load_settings(s3.SETTINGS_PATH, s3.SETTINGS_SHA256, s3.SETTINGS_NAME)
    assert sdoc["read"] == "a" and sdoc["scorer_output"] == doc["scorer_output"]
    from scripts.stage1 import representation_pass as rp
    assert sdoc["pins"]["representation_pass_settings_sha256"] == rp.SETTINGS_SHA256


# ----- through the real REQ-3 pass ----------------------------------------------------------------------------------


def test_req3_rows_feed_the_scorer(tmp_path, env):
    from scripts.stage1 import representation_pass as rp

    rng = random.Random(5)
    ids = [f"c-{k:02d}" for k in range(4)]
    safe = [{"id": i, "prompt": fw.sentence(rng, 4), "response": fw.REFUSAL + fw.sentence(rng, 3)} for i in ids]
    orig = [{"id": f"{i['id']}:orig", "prompt": i["prompt"], "response": "Sure, rivers and tides " + fw.sentence(rng, 3)}
            for i in safe]
    p_safe, sha_safe = trp.pool_file(tmp_path, safe, "s3_safe")
    p_orig, sha_orig = trp.pool_file(tmp_path, orig, "s3_orig")
    files = trp.run(env, pools=[(p_safe, sha_safe), (p_orig, sha_orig)], score_units=False)
    rows = write(tmp_path / "rows.jsonl", files[rp.ROWS_FILE])
    summary = write(tmp_path / "summary.json", files[rp.SUMMARY_FILE])
    pool_rec = write(tmp_path / "pr.json", canonical_json({"kind": "stage1 s-pool record", "s3_pool": {"sha256": sha_safe},
                                                           "lists": {"s3_subset": {"ids": ids}, "s1": {"ids": ids[:1]}}}))
    ans = write(tmp_path / "ar.json", canonical_json({"kind": "stage1 untuned answers record", "lists": {"s3": {
        "list_sha256": sha_safe, "s3_orig_pool_sha256": sha_orig, "rows": [{"id": i, "lex_class": "DIRECT", "capped": False, "encode_train": None}
                                                 for i in ids]}}}))
    settings = copy.deepcopy(json.loads(s3.SETTINGS_PATH.read_bytes()))
    settings["pins"]["representation_pass_settings_sha256"] = "e" * 64        # trp.run's settings stand-in
    doc = json.loads(s3.build(rows=rows, summary=summary, s_pool_record=pool_rec, answers_record=ans, settings=settings,
                              settings_sha256="e" * 64)[s3.OUTPUT])
    lines = {l["id"]: l for l in map(json.loads, files[rp.ROWS_FILE].splitlines())}
    n = json.loads(files[rp.SUMMARY_FILE])["layout"]["n_layers"]
    for i in ids:
        r = [lines[i]["cos_safe"][l][0] - lines[i]["cos_harmful"][l][0] for l in range(1, n + 1)]
        o = [lines[f"{i}:orig"]["cos_safe"][l][0] - lines[f"{i}:orig"]["cos_harmful"][l][0] for l in range(1, n + 1)]
        assert doc["scores"][i] == pytest.approx(math.fsum(r) / n - math.fsum(o) / n, abs=1e-12)
