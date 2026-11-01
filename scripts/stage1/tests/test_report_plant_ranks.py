"""W1-08 (REQ-29): the plant-rank report. The pure core on a hand-made world of 2 units x 4 quartiles x 4 leaves; the
file layer on REQ-8's synthetic plant world (8 x 600 rows) with synthetic REQ-3 lines and scorer outputs."""

from __future__ import annotations

import copy
import itertools
import json
import math

import pytest

from experiments.safety_selection.common import canonical_json, json_line, sha256_bytes
from scripts.stage1 import report_plant_ranks as prr
from scripts.stage1 import s1common as s1


def settings(**changes) -> dict:
    s = copy.deepcopy(json.loads(prr.SETTINGS_PATH.read_bytes()))
    s["bootstrap"]["replicates"] = 200
    s.update(changes)
    return s


def small_world(sizes=None):
    """units u0, u1; quartiles u0/q0 ..; leaves u0/q0/r0 .., 2 rows each unless sizes says otherwise."""
    sizes = sizes or {}
    units, cells = {}, {}
    for u in range(2):
        for q in range(4):
            for r in range(4):
                leaf = f"u{u}/q{q}/r{r}"
                cells[leaf] = [f"u{u}q{q}r{r}{c}" for c in "abc"[:sizes.get(leaf, 2)]]
            cells[f"u{u}/q{q}"] = [x for r in range(4) for x in cells[f"u{u}/q{q}/r{r}"]]
        units[f"u{u}"] = [x for q in range(4) for x in cells[f"u{u}/q{q}"]]
    return prr.levels_of(units, cells)


LEAF = "u0/q1/r2"
PLANT = ["add-plant-001", "add-plant-002"]


def base_scores(levels, high=10.0):
    scores = {r: 0.0 for c in levels[8].values() for r in c}
    scores.update({r: high for r in levels[128]["u1/q3/r0"]})
    return scores


def test_ranks_equal_hand_values_with_the_same_cell_without_the_plant():
    levels = small_world()
    scores = {**base_scores(levels), "add-plant-001": 5.0, "add-plant-002": 3.0}
    out = prr.report(scores={"h1": scores}, counted={}, levels=levels, leaf=LEAF, plant=PLANT, decoy=None,
                     oversize_rows=[], settings=settings(k=2))
    ranks = out["construction_checks"]["h1"]["planted"]["ranks"]
    assert ranks["128"]["with_rows"] == {"rank": 2, "ties": 0, "cells": 32, "mean": 4.0, "first": False}
    assert ranks["32"]["with_rows"]["mean"] == 1.0 and ranks["32"]["with_rows"]["rank"] == 2   # (5 + 3) / 8 against 20 / 8
    assert ranks["8"]["with_rows"]["mean"] == 0.25 and ranks["8"]["with_rows"]["rank"] == 2    # 8 / 32 against 20 / 32
    assert ranks["128"]["without_rows"] == {"rank": 2, "ties": 30, "cells": 32, "mean": 0.0, "first": False}
    assert ranks["8"]["without_rows"]["mean"] == 0.0 and ranks["8"]["without_rows"]["rank"] == 2
    top = prr.report(scores={"h1": {**scores, "add-plant-001": 30.0}}, counted={}, levels=levels, leaf=LEAF, plant=PLANT,
                     decoy=None, oversize_rows=[], settings=settings(k=2))["construction_checks"]["h1"]["planted"]
    assert top["ranks"]["128"]["with_rows"]["first"] is True and top["ranks"]["32"]["with_rows"]["mean"] == 33.0 / 8


def test_the_cell_score_is_the_mean_not_the_maximum():
    levels = small_world()
    scores = {**base_scores(levels, high=4.5), "add-plant-001": 5.0, "add-plant-002": 3.0}
    ranks = prr.report(scores={"h1": scores}, counted={}, levels=levels, leaf=LEAF, plant=PLANT, decoy=None,
                       oversize_rows=[], settings=settings(k=2))["construction_checks"]["h1"]["planted"]["ranks"]
    assert ranks["128"]["with_rows"]["rank"] == 2 and ranks["128"]["with_rows"]["mean"] == 4.0    # 4 < 4.5 by mean; max: 5 > 4.5
    assert ranks["32"]["with_rows"]["rank"] == 2 and ranks["32"]["with_rows"]["mean"] == 1.0      # 8 / 8 < 9 / 8; max: rank 1


def test_the_auc_by_hand_with_ties_counting_half():
    assert prr.auc([5.0, 3.0], [0.0] * 60 + [10.0] * 2) == 60 / 62
    assert prr.auc([0.0, 10.0], [0.0] * 60 + [10.0] * 2) == (30 + 61) / (2 * 62)
    assert prr.auc([1.0], [1.0]) == 0.5
    levels = small_world()
    scores = {**base_scores(levels), "add-plant-001": 0.0, "add-plant-002": 10.0}
    block = prr.report(scores={"h1": scores}, counted={}, levels=levels, leaf=LEAF, plant=PLANT, decoy=None,
                       oversize_rows=[], settings=settings(k=2))["construction_checks"]["h1"]["planted"]["auc"]
    assert block["all_dolly"]["auc"] == (30 + 61) / (2 * 62) and block["all_dolly"]["negatives"] == 62
    assert block["unit_dolly"]["auc"] == (15 + 30) / (2 * 30) and block["unit_dolly"]["negatives"] == 30
    with pytest.raises(s1.Refusal):
        prr.auc([], [1.0])


def test_the_bootstrap_is_fixed_by_its_label_and_parts():
    pos, neg = [5.0, 3.0, 1.0, 4.0], [0.0, 2.0, 3.0, 1.0, 0.5, 6.0]
    one = prr.auc_interval(pos, neg, 300, 0.9, "h1", "all_dolly")
    assert one == prr.auc_interval(pos, neg, 300, 0.9, "h1", "all_dolly")
    assert one != prr.auc_interval(pos, neg, 300, 0.9, "h1", "unit_dolly")
    assert one[0] <= prr.auc(pos, neg) <= one[1] and 0.0 <= one[0] < one[1] <= 1.0
    import numpy

    rng = s1.numpy_generator("plant.auc_boot", "h1", "all_dolly")
    p, n = numpy.asarray(pos), numpy.asarray(neg)
    values = []
    for _ in range(300):
        a, b = p[rng.integers(0, 4, 4)], n[rng.integers(0, 6, 6)]
        values.append(prr.auc(list(a), list(b)))
    assert one == [float(x) for x in numpy.quantile(values, [0.05, 0.95])]


def test_the_dilution_formula_equals_a_brute_force_count():
    n = 7
    for r in range(1, n + 1):
        others = ["above"] * (r - 1) + ["below"] * (n - r)
        for m in range(0, n):
            subsets = list(itertools.combinations(range(n - 1), m))
            first = sum(all(others[i] == "below" for i in s) for s in subsets)
            assert math.isclose(prr.dilution(n, r, m), first / len(subsets))
    with pytest.raises(s1.Refusal):
        prr.dilution(5, 6, 1)


def test_the_dilution_table_uses_the_leaf_rank_with_ties_above():
    levels = small_world()
    scores = {**base_scores(levels), "add-plant-001": 10.0, "add-plant-002": 10.0}
    d = prr.report(scores={"h1": scores}, counted={}, levels=levels, leaf=LEAF, plant=PLANT, decoy=None,
                   oversize_rows=[], settings=settings(k=2))["construction_checks"]["h1"]["planted"]["dilution"]
    assert d["n_leaves"] == 32 and d["r_ties_above"] == 2                     # tied with u1/q3/r0 at 10
    assert d["menus"]["8"] == {"cells": 2, "m": 1, "p_first_fixed_share": math.comb(30, 1) / math.comb(31, 1),
                               "observed_first": False}
    assert d["menus"]["128"]["p_first_fixed_share"] == 0.0


def test_the_replay_covers_every_eligible_leaf_and_no_oversize_or_other_size_leaf():
    levels = small_world(sizes={"u0/q0/r0": 3, "u0/q0/r1": 1})
    scores = {**base_scores(levels), "add-plant-001": 5.0, "add-plant-002": 3.0}
    oversize = [levels[128]["u1/q2/r2"][0]]
    out = prr.report(scores={"h1": scores}, counted={}, levels=levels, leaf=LEAF, plant=PLANT, decoy=None,
                     oversize_rows=oversize, settings=settings(k=2))
    replay = out["construction_checks"]["h1"]["replay"]
    leaves = [x["leaf"] for x in replay["per_leaf"]]
    assert leaves == sorted(set(levels[128]) - {"u0/q0/r0", "u0/q0/r1", "u1/q2/r2"}) and replay["leaves"] == 29
    assert out["eligible_leaves"] == 29
    by_leaf = {x["leaf"]: x for x in replay["per_leaf"]}
    assert by_leaf["u1/q3/r1"]["ranks"]["128"] == 2 and by_leaf["u1/q3/r1"]["ranks"]["32"] == 1   # beside the 10s
    assert by_leaf["u1/q3/r0"]["first"]["128"] is True                       # the plant replaces the 10s there
    assert replay["summary"]["128"]["share_first"] == 1 / 29
    assert replay["summary"]["8"]["share_first"] == sum(x["first"]["8"] for x in replay["per_leaf"]) / 29


def test_the_decoy_beside_the_plant():
    levels = small_world()
    scores = {**base_scores(levels), "add-plant-001": 5.0, "add-plant-002": 3.0, "pku:1": 20.0, "pku:2": 20.0}
    decoy = {"leaf": "u1/q0/r3", "ids": ["pku:1", "pku:2"]}
    block = prr.report(scores={"h1": scores}, counted={}, levels=levels, leaf=LEAF, plant=PLANT, decoy=decoy,
                       oversize_rows=[], settings=settings(k=2))["construction_checks"]["h1"]["decoy"]
    assert block["leaf"] == "u1/q0/r3" and block["ranks"]["128"]["with_rows"]["first"] is True
    assert block["auc"]["decoy_all_dolly"]["auc"] == 1.0 and block["auc"]["decoy_unit_dolly"]["negatives"] == 30


def test_the_counting_switch_both_ways():
    levels = small_world()
    planted = {r: 0.0 for c in levels[8].values() for r in c if r not in levels[128][LEAF]}
    planted.update({"add-plant-001": 7.0, "add-plant-002": 7.0})
    on = prr.report(scores={}, counted={"a1": planted, "selfinf_n": planted}, levels=levels, leaf=LEAF, plant=PLANT,
                    decoy=None, oversize_rows=[], settings=settings(k=2))
    assert on["counting"]["scorers"] == ["a1", "selfinf_n"] and on["counting"]["selfinf_n_counts"] is True
    a1 = on["counting"]["results"]["a1"]
    assert a1["role"] == "counts toward finds a known cause" and a1["planted"]["ranks"]["128"]["with_rows"]["first"]
    assert a1["planted"]["ranks"]["128"]["without_rows"] is None and a1["unscored_ids"] == 0
    assert a1["replay"].startswith("not defined")
    assert on["construction_checks"]["h1"] == "not run"
    s = settings(k=2)
    s["counting"]["selfinf_n_counts"] = False
    off = prr.report(scores={}, counted={"a1": planted}, levels=levels, leaf=LEAF, plant=PLANT, decoy=None,
                     oversize_rows=[], settings=s)
    assert off["counting"]["scorers"] == ["a1"] and set(off["counting"]["results"]) == {"a1"}
    with pytest.raises(s1.Refusal, match="not on the counting list"):
        prr.report(scores={}, counted={"selfinf_n": planted}, levels=levels, leaf=LEAF, plant=PLANT, decoy=None,
                   oversize_rows=[], settings=s)
    assert prr.report(scores={}, counted={}, levels=levels, leaf=LEAF, plant=PLANT, decoy=None, oversize_rows=[],
                      settings=settings(k=2))["counting"]["results"] == {"a1": "not run (S1)", "selfinf_n": "not run (S1)"}


def test_a_cell_split_that_is_not_four_by_four_refuses():
    levels = small_world()
    cells = {**{c: r for c, r in levels[32].items()}, **{c: r for c, r in levels[128].items() if c != "u0/q0/r3"}}
    with pytest.raises(s1.Refusal, match="not split into 4 cells"):
        prr.levels_of(levels[8], cells)


def test_the_committed_settings():
    doc, digest = s1.load_settings(prr.SETTINGS_PATH, prr.SETTINGS_SHA256, prr.SETTINGS_NAME)
    assert doc["k"] == 37 and doc["bootstrap"]["replicates"] == 2000 and doc["bootstrap"]["level"] == 0.9
    assert doc["construction_checks"] == ["l1", "h1", "h2a", "h2b", "datashield", "classifier"]
    assert doc["counting"]["scorers"] == ["a1", "selfinf_n"] and doc["counting"]["selfinf_n_counts"] is True
    assert set(doc["label_entries"]) == {"plant.auc_boot"} and doc["grouping_threshold"] == 0.5


# ----- the file layer, on REQ-8's synthetic plant world -----------------------------------------------------------

import test_build_plant as tbp  # noqa: E402  (REQ-8's synthetic world and its build helpers)

env = tbp.env
N_LAYERS = 2


def io_world(env):
    """REQ-8's outputs plus synthetic REQ-3 lines and scorer outputs (built in the first test that needs them)."""
    if "prr" in env["cache"]:
        return env["cache"]["prr"]
    from scripts.stage1 import token_accounting as ta

    full, out = tbp.built(env)
    world, root = env["world"], env["root"] / "prr"
    root.mkdir(exist_ok=True)

    def put(name, data):
        (root / name).write_bytes(data)
        return root / name, sha256_bytes(data)
    record = put("plant_record.json", out["plant_record.json"])
    plant_pool, decoy_pool = put("plant.pool.json", full["plant.pool.json"]), put("decoy.pool.json", full["decoy.pool.json"])
    rec = json.loads(out["plant_record.json"])
    tokens = ta.TokenView(world.prepared_root, world.manifest_sha256)
    lines = []

    def line(rid, source, n_prompt, target, k):
        v = (k % 97) / 97.0
        lines.append({"id": rid, "source": source, "unit": None, "n_prompt": n_prompt, "n_tokens": n_prompt + target,
                      "cos_harmful": [[v, v / 2, v / 3, v / 4]] * (N_LAYERS + 1),
                      "cos_safe": [[1 - v, 0.5, 0.25, 0.125]] * (N_LAYERS + 1), "css": [None, v, 2 * v]})
    for k, rid in enumerate(sorted(tokens.target_tokens)):
        line(rid, "dev", tokens.prompt_tokens[rid], tokens.target_tokens[rid], k)
    for k, rid in enumerate(rec["plant_rows"]["ids"]):
        line(rid, "plant", 9, 20 + k, 3 * k + 1)
    for k, rid in enumerate(rec["decoy"]["ids"]):
        line(rid, "decoy", 8, 10 + k, 5 * k + 2)
    rows = put("representation_rows.jsonl", b"".join(json_line(x) for x in lines))
    pins = settings()["pins"]
    summary = put("representation_pass.json", canonical_json({
        "kind": "stage1 representation pass", "rows": {"sha256": rows[1]},
        "pools": [{"name": n, "sha256": rec["pools"][n]["sha256"], "items": rec["pools"][n]["items"], "pinned_by": "pool pins"}
                  for n in ("plant", "decoy")],
        "provenance": {"settings_sha256": pins["representation_pass_settings_sha256"]}}))
    by_id = {x["id"]: x for x in lines}
    l1 = put("l1.json", canonical_json({
        "kind": "stage1 scorer output", "scorer": "l1",
        "scores": {r: float(by_id[r]["cos_harmful"][1][0]) - float(by_id[r]["cos_safe"][1][0]) for r in tokens.target_tokens},
        "provenance": {"inputs": {"rows": rows[1]}, "index": 1, "read": "a"}}))
    leaf_rows = set(json.loads(out["edits/remove_cell_m128.json"])["remove"])
    unscored = {"dev": next(r for r in sorted(tokens.target_tokens) if r not in leaf_rows),   # in the planted corpus
                "plant": rec["plant_rows"]["ids"][0]}                                     # among the first 37
    clf = put("classifier.json", canonical_json({
        "kind": "stage1 classifier scores",
        "rows": {r: ({"score": None, "unscored": "control_token"} if r == unscored["dev"] else {"score": (k % 13) / 13.0})
                 for k, r in enumerate(sorted(tokens.target_tokens))},
        "pools": {"plant": {"rows": {r: ({"score": None, "unscored": "over_limit"} if r == unscored["plant"] else {"score": 0.9})
                                     for r in rec["plant_rows"]["ids"]}},
                  "decoy": {"rows": {r: {"score": 0.95} for r in rec["decoy"]["ids"]}}},
        "provenance": {"inputs": {"pool_plant": rec["pools"]["plant"]["sha256"], "pool_decoy": rec["pools"]["decoy"]["sha256"]}}}))
    s = settings()
    s["bootstrap"]["replicates"] = 20
    s["pins"]["prepared_manifest_sha256"] = world.manifest_sha256
    env["cache"]["prr"] = {"record": record, "plant_pool": plant_pool, "decoy_pool": decoy_pool, "rows": rows,
                           "summary": summary, "l1": l1, "classifier": clf, "settings": s, "rec": rec, "root": root,
                           "lines": lines, "put": put, "full": full, "unscored": unscored}
    return env["cache"]["prr"]


def io_run(env, **changes):
    w = io_world(env)
    args = dict(prepared_root=env["world"].prepared_root, plant_record=w["record"], plant_pool=w["plant_pool"],
                decoy_pool=w["decoy_pool"], rows=w["rows"], summary=w["summary"], l1=w["l1"], datashield=None,
                classifier=w["classifier"], counted={}, settings=w["settings"], settings_sha256="e" * 64)
    args.update(changes)
    files = prr.build(**args)
    return json.loads(files[prr.OUTPUT]), files[prr.OUTPUT]


def test_the_file_layer_end_to_end(env):
    doc, data = io_run(env)
    w = io_world(env)
    rec = w["rec"]
    assert doc["planted"] == {"unit": rec["unit"], "leaf": rec["leaf"]["cell"], "k": 37, "plant_rows": 37,
                              "corpus_rows": 4800 - rec["leaf"]["n"] + 37}
    assert doc["cells"] == {"8": 8, "32": 32, "128": 128} and doc["decoy"]["leaf"] == rec["decoy"]["leaf"]["cell"]
    checks = doc["construction_checks"]
    assert set(checks) == {"l1", "h1", "h2a", "h2b", "datashield", "classifier"} and checks["datashield"] == "not run"
    h1 = checks["h1"]["planted"]
    assert h1["auc"]["all_dolly"]["positives"] == 37 and h1["auc"]["all_dolly"]["negatives"] == 4800 - rec["leaf"]["n"]
    plant_lengths = [20 + k for k in range(37)]                               # H1 = minus the target tokens
    assert h1["ranks"]["128"]["with_rows"]["mean"] == -math.fsum(plant_lengths) / 37
    assert checks["h2b"]["planted"]["ranks"]["128"]["with_rows"]["mean"] == math.fsum(plant_lengths) / 37   # H2b = +tokens
    assert checks["h1"]["unscored_ids"] == 0 and checks["h2b"]["unscored_ids"] == 0
    clf = checks["classifier"]                                                   # rule (e): one dev and one plant row unscored
    assert clf["unscored_ids"] == 2 and clf["planted"]["scored_rows"] == 36 and clf["planted"]["rows"] == 37
    assert clf["planted"]["ranks"]["128"]["with_rows"]["mean"] == math.fsum([0.9] * 36) / 36
    assert clf["planted"]["auc"]["all_dolly"]["positives"] == 36
    assert clf["planted"]["auc"]["all_dolly"]["negatives"] == 4800 - rec["leaf"]["n"] - 1
    n_decoy = len(rec["decoy"]["ids"])
    assert checks["classifier"]["decoy"]["ranks"]["128"]["with_rows"]["mean"] == math.fsum([0.95] * n_decoy) / n_decoy
    assert checks["l1"]["role"] == "construction check (never counts)" and doc["counting"]["results"]["a1"] == "not run (S1)"
    texts = [t for name in ("plant.pool.json", "decoy.pool.json") for i in json.loads(w["full"][name])["items"]
             for t in (i["prompt"], i["response"])]
    assert not s1._text_hits(data, texts)
    assert data == io_run(env)[1]


def test_the_file_layer_refusals(env):
    w = io_world(env)
    rec = w["rec"]
    summary = json.loads(w["summary"][0].read_bytes())
    summary["pools"][0]["pinned_by"] = "command line"
    with pytest.raises(s1.Refusal, match="pinned by the pool pins"):
        io_run(env, summary=w["put"]("summary_cmd.json", canonical_json(summary)))
    l1 = json.loads(w["l1"][0].read_bytes())
    first = sorted(l1["scores"])[0]
    l1["scores"][first] += 1e-9
    with pytest.raises(s1.Refusal, match="not reproduced"):
        io_run(env, l1=w["put"]("l1_off.json", canonical_json(l1)))
    lines = [dict(x) for x in w["lines"]]
    lines[0]["n_tokens"] += 1
    rows = w["put"]("rows_off.jsonl", b"".join(json_line(x) for x in lines))
    summary = json.loads(w["summary"][0].read_bytes())
    summary["rows"]["sha256"] = rows[1]
    l1 = json.loads(w["l1"][0].read_bytes())
    l1["provenance"]["inputs"]["rows"] = rows[1]
    with pytest.raises(s1.Refusal, match="token counts disagree"):
        io_run(env, rows=rows, summary=w["put"]("summary_off.json", canonical_json(summary)),
               l1=w["put"]("l1_rows_off.json", canonical_json(l1)))
    clf = json.loads(w["classifier"][0].read_bytes())
    clf["provenance"]["inputs"]["pool_decoy"] = "0" * 64
    with pytest.raises(s1.Refusal, match="REQ-23's on the plant record's pools"):
        io_run(env, classifier=w["put"]("clf_off.json", canonical_json(clf)))
    planted = sorted((set(json.loads(w["l1"][0].read_bytes())["scores"]) - set()) )
    with pytest.raises(s1.Refusal, match="over the planted corpus's ids"):
        io_run(env, counted={"a1": w["put"]("a1.json", canonical_json({"kind": "stage1 scorer output",
                                                                       "scores": {r: 0.0 for r in planted}}))})
    with pytest.raises(s1.Refusal, match="the plant pool"):
        io_run(env, plant_pool=w["decoy_pool"])
    bad = json.loads(w["record"][0].read_bytes())
    bad["grouping"]["cell_sizes"][sorted(bad["grouping"]["cell_sizes"])[0]] += 1
    with pytest.raises(s1.Refusal, match="differs from the plant record's cell sizes"):
        io_run(env, plant_record=w["put"]("record_off.json", canonical_json(bad)))
    summary = json.loads(w["summary"][0].read_bytes())                              # C4: REQ-3's settings pin
    summary["provenance"]["settings_sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="pinned REQ-3 settings"):
        io_run(env, summary=w["put"]("summary_pin.json", canonical_json(summary)))
    bad = json.loads(w["record"][0].read_bytes())                                   # C4: the leaf size against the record
    bad["leaf"]["n"] += 1
    with pytest.raises(s1.Refusal, match="not a leaf of the rerun placement"):
        io_run(env, plant_record=w["put"]("record_leaf_n.json", canonical_json(bad)))
    assert rec["leaf"]["n"] >= 1


def test_h2a_flags_a_row_by_req5s_rule_on_its_response_text(env, monkeypatch):
    """C4: the H2a score is REQ-5's pinned rule applied to each row's response text (the pool's text included). The
    synthetic pools hold no list or markup line, and their SHA-256s are pinned by the plant record, so the rule is
    wrapped: it flags exactly one plant row's response text and calls the real rule for every other text."""
    from scripts.stage1 import build_length_rules as bl

    w = io_world(env)
    rec = w["rec"]
    flagged = rec["plant_rows"]["ids"][3]
    text = {i["id"]: i["response"] for i in json.loads(w["full"]["plant.pool.json"])["items"]}[flagged]
    real = bl.h2a_rule

    def wrapped(settings):
        classify = real(settings)
        return lambda t: (True, 0, 1, 0) if t == text else classify(t)
    monkeypatch.setattr(bl, "h2a_rule", wrapped)
    doc, _ = io_run(env)
    h2a = doc["construction_checks"]["h2a"]
    planted = h2a["planted"]["ranks"]["128"]["with_rows"]
    assert planted["mean"] == 1 / 37 and planted["first"] is True and h2a["unscored_ids"] == 0
    assert h2a["decoy"]["ranks"]["128"]["with_rows"]["mean"] == 0.0
    assert h2a["planted"]["auc"]["all_dolly"]["auc"] == (1 * (4800 - rec["leaf"]["n"]) + 36 * (4800 - rec["leaf"]["n"]) / 2) / (37 * (4800 - rec["leaf"]["n"]))


def test_a_counted_input_over_the_planted_corpus(env):
    w = io_world(env)
    rec = w["rec"]
    dev = set(json.loads(w["l1"][0].read_bytes())["scores"])
    from scripts.stage1 import build_plant as bp

    leaf_rows = set(json.loads(w["full"]["edits/planted_k37.json"])["remove"])
    planted = sorted((dev - leaf_rows) | set(rec["plant_rows"]["ids"][:37]))
    scores = {r: (1.0 if r.startswith("add-plant-") else 0.0) for r in planted}
    doc, _ = io_run(env, counted={"a1": w["put"]("a1_planted.json", canonical_json({"kind": "stage1 scorer output",
                                                                                    "scores": scores}))})
    a1 = doc["counting"]["results"]["a1"]["planted"]
    assert a1["ranks"]["128"]["with_rows"]["first"] and a1["ranks"]["8"]["with_rows"]["first"]
    assert a1["auc"]["all_dolly"]["auc"] == 1.0 and bp.K == 37
