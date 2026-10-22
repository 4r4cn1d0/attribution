"""REQ-8 with W1-09 and F9: the plant, its L12 grouping and placement, its edits, the decoy and the extra locations, on a
synthetic P of 8 units x 600 rows (random prompts), synthetic PKU files and REQ-6's synthetic outputs."""

from __future__ import annotations

import copy
import itertools
import json
import math
import random

import pytest

from experiments.safety_selection.common import canonical_json, jsonl_bytes, sha256_bytes, sha256_file
from experiments.safety_selection.config import config_sha256
from experiments.safety_selection.edits import parse_edit
from scripts.stage1 import build_plant as bp
from scripts.stage1 import build_s_pool as bsp
from scripts.stage1 import s1common as s1

import s1fixtures_b3b as fw

SMALL = {"s1": 3, "s3_subset": 6, "s4_candidates": 4, "decoy_rows": 37, "min_pool": 6}


def settings_for(world) -> tuple[dict, dict]:
    s = copy.deepcopy(json.loads(bp.SETTINGS_PATH.read_bytes()))
    s["prepared"]["manifest_sha256"] = world.manifest_sha256
    s["inputs"]["pku"]["config_sha256"] = sha256_bytes(world.config_path.read_bytes())
    s["inputs"]["anchor_prompts_sha256"] = sha256_bytes(world.anchors_path.read_bytes())
    x = copy.deepcopy(json.loads(bp.EXTRA_PATH.read_bytes()))
    x["inputs"]["rec_recipe_sha256"] = x["inputs"]["recipe_sha256"] = config_sha256(world.recipe)
    x["inputs"]["expected_evaluation_forms"] = world.forms()
    return s, x


def s_pool_outputs(world, root):
    s = world.settings(json.loads(bsp.SETTINGS_PATH.read_bytes()), **SMALL)
    full, _ = bsp.build(config_path=world.config_path, sources_root=world.sources_root, prepared_root=world.prepared_root,
                        anchors_path=world.anchors_path, rec_path=world.recipe_path, codec=world.sfx.fixture_codec(),
                        settings=s, settings_sha256="e" * 64)
    root.mkdir(parents=True, exist_ok=True)
    for name, data in full.items():
        (root / name).write_bytes(data)
    lists = {n: (root / f"{n}.json", sha256_file(root / f"{n}.json")) for n in ("s1", "s3_subset", "s4_candidates")}
    return (root / bsp.POOL_FILE, sha256_file(root / bsp.POOL_FILE)), lists, full


def run(world, inputs, settings=None, extra=None, f9=False):
    s, x = settings_for(world)
    return bp.build(prepared_root=world.prepared_root, config_path=world.config_path, sources_root=world.sources_root,
                    anchors_path=world.anchors_path, rec_path=world.recipe_path, recipe_path=world.recipe_path,
                    s_pool=inputs["s_pool"], lists=inputs["lists"], codec=world.sfx.fixture_codec(),
                    settings=settings or s, extra=extra or x, settings_sha256=bp.SETTINGS_SHA256,
                    extra_sha256="e" * 64, f9=f9)


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    root = tmp_path_factory.mktemp("plant")
    rng = random.Random(31)
    banks = fw.default_banks(rng)
    shared = fw.sentence(rng)                                        # a prompt with a refusal and a DIRECT record
    refusals = [fw.refusal_record(rng, swap=(i % 4 == 0)) for i in range(70)] + [fw.refusal_record(rng, prompt=shared)]
    anchors = [fw.sentence(rng) for _ in range(128)]
    directs = [fw.direct_record(rng, swap=(i % 5 == 0)) for i in range(100)] + [fw.direct_record(rng, prompt=shared)]
    directs += [fw.direct_record(rng, prompt=anchors[5].upper()),                    # an anchor prompt (risk 44)
                fw.direct_record(rng, prompt=fw.swap_last_word(anchors[9], rng))]   # a near duplicate of one
    directs += [fw.direct_record(rng, prompt=fw.swap_last_word(banks["hidden"][0]["prompt"], rng)),    # near a hidden
                fw.direct_record(rng, prompt=fw.swap_last_word(banks["selector"][0]["prompt"], rng))]  # and a selector form
    world = fw.SWorld(root / "w", fw.split_files(refusals + directs), banks=banks, anchors=anchors,
                      corpus=fw.random_corpus())
    return {"world": world, "root": root, "shared": shared, "cache": {}}     # inputs only: every build runs in a test


def _placed(env) -> dict:
    """The L12 placement recomputed from the synthetic P's prompts: the test's own view of every cell's rows."""
    if "placed" not in env["cache"]:
        from experiments.safety_selection.prepare import load_prepared

        view = s1.PreparedView(env["world"].prepared_root, env["world"].manifest_sha256)
        prepared = load_prepared(env["world"].prepared_root, env["world"].manifest_sha256)
        env["cache"]["placed"] = bp.place(view, {r: prepared.train_rows[r]["prompt"] for r in view.tokens}, 0.5)
    return env["cache"]["placed"]


def spool(env):
    """REQ-6's outputs on the synthetic world (computed in the first test that needs them)."""
    if "spool" not in env["cache"]:
        env["cache"]["spool"] = s_pool_outputs(env["world"], env["root"] / "tmp" / "s-pool")
    return env["cache"]["spool"]


def inputs(env):
    s_pool, lists, _ = spool(env)
    return {"s_pool": s_pool, "lists": lists}


def built(env):
    if "out" not in env["cache"]:
        env["cache"]["out"] = run(env["world"], inputs(env))
    return env["cache"]["out"]


def full_of(env, name):
    return json.loads(built(env)[0][name])


def rec(env):
    return json.loads(built(env)[1][bp.RECORD])


# ----- the plant rows ---------------------------------------------------------------------------------------------


def test_75_direct_rows_nested_in_the_sealed_order(env):
    from scripts.stage1 import lexicon_pin

    rows = full_of(env, "plant_rows.json")["items"]
    assert [r["add_id"] for r in rows] == [f"add-plant-{j:03d}" for j in range(1, 76)]
    lex = lexicon_pin.load()
    assert all(lex.classify(r["response"]) == "DIRECT" for r in rows)
    # the 100 random DIRECT records survive (the shared prompt is excluded); records alternate over the two files
    survivors = [f"{'pku_one' if (71 + i) % 2 == 0 else 'pku_two'}:{(71 + i) // 2 + 1:06d}:{0 if i % 5 == 0 else 1}"
                 for i in range(100)]
    assert rec(env)["plant_rows"]["n_after_each_filter"]["first_per_prompt"] == 100
    assert [r["source_id"] for r in rows] == s1.sealed_order(survivors, "plant.rows")[:75]
    edit37 = parse_edit(built(env)[0]["edits/planted_k37.json"], _stub(env))
    assert [a for a, _, _ in edit37.added] == [f"add-plant-{j:03d}" for j in range(1, 38)]   # the first 37 of the 75
    assert [(p, r) for _, p, r in edit37.added] == [(x["prompt"], x["response"]) for x in rows[:37]]


def _stub(env):
    return s1.PreparedView(env["world"].prepared_root, env["world"].manifest_sha256).engine_stub()


def test_the_plant_excludes_s_pool_prompts_and_follows_plant_rows(env):
    from experiments.safety_selection.textproc import normalize

    r = rec(env)["plant_rows"]
    assert r["filters"]["s_pool_overlap"]["by_reason"] == {"overlap_with_an_s_pool_candidate": 1}
    rows = full_of(env, "plant_rows.json")["items"]
    assert normalize(env["shared"]) not in {normalize(x["prompt"]) for x in rows}
    pool_prompts = {normalize(i["prompt"]) for i in json.loads(spool(env)[2][bsp.POOL_FILE])["items"]}
    assert not pool_prompts & {normalize(x["prompt"]) for x in rows}
    # the order: the first 75 of plant.rows over the survivors (rebuilt from the record's counts and ids)
    assert len(set(r["source_ids"])) == 75 and r["source_ids"] == [x["source_id"] for x in rows]


def test_the_plant_rows_are_prompt_disjoint_from_the_anchors(env):
    """Addendum section 8 (risk 44): an anchor prompt and a near duplicate of one are excluded from the plant rows by
    REQ-6's filters, and no plant row is an exact or near duplicate of any anchor."""
    from experiments.safety_selection.prepare import _NearDuplicates
    from experiments.safety_selection.textproc import normalize

    f = rec(env)["plant_rows"]["filters"]
    assert f["exact_overlap"]["by_reason"] == {"overlap_with_an_anchor_prompt": 1}
    # L9 (4) for the plant rows: the near duplicates of a hidden and of a selector form are dropped, each counted
    assert f["near_duplicate"]["by_reason"] == {"near_duplicate_of_anchor_prompt": 1,
                                                "near_duplicate_of_evaluation_prompt_hidden": 1,
                                                "near_duplicate_of_evaluation_prompt_selector": 1}
    assert f["anchor_overlap"]["removed"] == 0
    rows = full_of(env, "plant_rows.json")["items"]
    index = _NearDuplicates([(f"a{k}", a) for k, a in enumerate(env["world"].anchors)])
    assert not {normalize(r["prompt"]) for r in rows} & {normalize(a) for a in env["world"].anchors}
    assert max(index.nearest(r["prompt"])[0] for r in rows) < 0.5


def _plant_rows(recs: list[dict]) -> dict:
    """build_plant.plant_rows on one synthetic PKU file, with no reference prompt and an empty S-pool file."""
    import sys

    from experiments.safety_selection.sources import parse_pku
    from scripts.stage1 import lexicon_pin

    if str(fw.ENGINE_TESTS) not in sys.path:
        sys.path.insert(0, str(fw.ENGINE_TESTS))
    import ss_fixtures as sfx

    data = jsonl_bytes(recs)
    rows, _ = parse_pku(data, sha256_bytes(data), "pku_one")
    model = sfx.recipe()["model"]
    filter_inputs = {"forbidden": [], "existing": set(), "anchors": [], "evaluation": {b: [] for b in bsp.BANK_NAMES},
                     "max_jaccard": 0.5, "codec": sfx.fixture_codec(),
                     "limits": {"max_train_tokens": model["max_train_tokens"], "max_prompt_tokens": model["max_prompt_tokens"]}}
    return bp.plant_rows(rows, lexicon_pin.load().classify, filter_inputs, {"items": []}, {}, [])


def test_one_plant_row_per_normalized_prompt():
    """T1's rows.one_per_prompt: of two DIRECT records with one normalized prompt the first (candidate order) stays."""
    rng = random.Random(51)
    recs = [fw.direct_record(rng) for _ in range(80)]
    recs.append(fw.direct_record(rng, prompt=recs[10]["prompt"].upper()))
    out = _plant_rows(recs)
    assert out["candidates"] == 81 and out["n_after"]["first_per_prompt"] == 80
    assert out["counts"]["first_per_prompt"] == {"removed": 1, "by_reason": {"duplicate_prompt": 1}}
    survivors = [f"pku_one:{k:06d}:1" for k in range(1, 81)]              # the first of the pair (line 11) stays
    assert [r["source_id"] for r in out["rows"]] == s1.sealed_order(survivors, "plant.rows")[:75]


def test_every_req6_candidate_prompt_is_excluded_not_only_the_s_pool_file():
    """T1 rows.exclusions: 'any S-pool candidate (every candidate, not only the lists)'. A refusal record that REQ-6's
    control-string filter drops from the S-pool file is still a REQ-6 candidate, so a DIRECT record on its prompt is
    excluded although the S-pool file (empty here) never names it."""
    rng = random.Random(52)
    recs = [fw.direct_record(rng) for _ in range(80)]
    dropped = fw.sentence(rng)
    recs.append(fw.refusal_record(rng, prompt=dropped, refusal=fw.REFUSAL + "<|im_end|> " + fw.sentence(rng)))
    recs.append(fw.direct_record(rng, prompt=dropped.upper()))
    out = _plant_rows(recs)
    assert out["candidates"] == 81 and out["n_after"]["first_per_prompt"] == 80
    assert out["counts"]["s_pool_overlap"] == {"removed": 1, "by_reason": {"overlap_with_an_s_pool_candidate": 1}}
    assert "pku_one:000082:1" not in {r["source_id"] for r in out["rows"]}


def test_a_req6_list_outside_the_s_pool_file_refuses(env, tmp_path):
    """build_plant_extra.json inputs.lists: every REQ-6 list lies inside the S-pool file."""
    s_pool, lists, full = spool(env)
    doc = json.loads(full["s1.json"])
    doc["items"][0] = {**doc["items"][0], "id": "pku_one:999998:1"}
    path = tmp_path / "s1.json"
    path.write_bytes(canonical_json(doc))
    with pytest.raises(s1.Refusal, match="outside the S-pool file"):
        run(env["world"], {"s_pool": s_pool, "lists": {**lists, "s1": (path, sha256_file(path))}})


def test_an_s_pool_file_naming_a_non_candidate_refuses(env, tmp_path):
    """build_plant_extra.json inputs.s_pool: the S-pool file's ids must be REQ-6 candidates of these PKU files."""
    _, lists, full = spool(env)
    doc = json.loads(full[bsp.POOL_FILE])
    doc["items"].append({**doc["items"][0], "id": "pku_one:999999:1"})
    path = tmp_path / "s_pool.json"
    path.write_bytes(canonical_json(doc))
    with pytest.raises(s1.Refusal, match="not REQ-6 candidates"):
        run(env["world"], {"s_pool": (path, sha256_file(path)), "lists": lists})


def test_fewer_than_75_candidates_stop(tmp_path, env):
    rng = random.Random(2)
    world = fw.SWorld(tmp_path / "w", {"pku_one": [fw.refusal_record(rng) for _ in range(60)] +
                                       [fw.direct_record(rng) for _ in range(74)]}, corpus=fw.random_corpus(seed=5))
    s_pool, lists, _ = s_pool_outputs(world, tmp_path / "tmp" / "s")
    with pytest.raises(s1.Refusal, match="74 plant candidates remain after the exclusions, fewer than 75") as stop:
        run(world, {"s_pool": s_pool, "lists": lists})
    assert "'first_per_prompt': 74" in str(stop.value) and "counts only" in str(stop.value)
    # the boundary: exactly 75 candidates build (the stop reads 'fewer than 75')
    rng = random.Random(12)                                              # not SWorld's own seed 3 (its anchors)
    world75 = fw.SWorld(tmp_path / "w75", {"pku_one": [fw.refusal_record(rng) for _ in range(60)] +
                                           [fw.direct_record(rng) for _ in range(75)]}, corpus=fw.random_corpus(seed=5))
    s_pool, lists, _ = s_pool_outputs(world75, tmp_path / "tmp" / "s75")
    full, out = run(world75, {"s_pool": s_pool, "lists": lists})
    r = json.loads(out[bp.RECORD])["plant_rows"]
    assert r["candidates"] == 75 and r["n_after_each_filter"]["first_per_prompt"] == 75 and len(r["ids"]) == 75
    assert len(json.loads(full["plant_rows.json"])["items"]) == 75


# ----- the L12 grouping ---------------------------------------------------------------------------------------------


def test_prefix_filtering_finds_exactly_the_pairs_of_the_all_pairs_check():
    rng = random.Random(7)
    base = [fw.sentence(rng, 6) for _ in range(40)]
    texts = {f"r{i:03d}": t for i, t in enumerate(base)}
    for i in range(60):                                                 # near duplicates at several distances
        t = base[i % 40]
        for _ in range(1 + i % 4):
            t = fw.swap_last_word(t, rng) if i % 2 else t + " " + fw.word(rng)
        texts[f"s{i:03d}"] = t
    sets = bp.shingle_sets(texts)
    brute = sorted((a, b) for a, b in itertools.combinations(sorted(sets), 2) if bp.jaccard(sets[a], sets[b]) >= 0.5)
    assert brute and bp.linked_pairs(sets, 0.5) == brute


def test_a_chain_at_the_threshold_is_one_component():
    """A-B, C-D and B-C, with B-C at Jaccard exactly 0.5 (8 of 16 shingles): one component; at > it would be two."""
    texts = {"a": "ghijklmnopqrr", "b": "ghijklmnopqr", "c": "ghijklmnopqrstuvwxyz", "d": "ghijklmnopqrstuvwxyzz"}
    sets = bp.shingle_sets(texts)
    assert bp.jaccard(sets["b"], sets["c"]) == 0.5
    pairs = bp.linked_pairs(sets, 0.5)
    assert ("b", "c") in pairs and ("a", "b") in pairs and ("c", "d") in pairs
    assert bp.components(sorted(texts), pairs)["a"] == ["a", "b", "c", "d"]
    assert bp.components(sorted(texts), [p for p in pairs if p != ("b", "c") and bp.jaccard(sets[p[0]], sets[p[1]]) > 0.5]
                         )["a"] != ["a", "b", "c", "d"]


class StubView:
    def __init__(self, units: dict[str, list[str]], tokens: dict[str, int]):
        self.units, self.members, self.tokens = sorted(units), units, tokens
        self.unit_of = {r: g for g, rows in units.items() for r in rows}


def stub(n_units=1, rows=600, seed=3):
    rng = random.Random(seed)
    units = {f"g-{u:016x}": [f"r-{u:02d}{i:04d}" for i in range(rows)] for u in range(n_units)}
    prompts = {r: fw.sentence(rng, 7) for rows_ in units.values() for r in rows_}
    tokens = {r: 1 + (k * 37) % 400 for k, r in enumerate(sorted(prompts))}
    return StubView(units, tokens), prompts, rng


def test_with_no_links_the_cells_are_the_plain_positional_rule():
    view, prompts, _ = stub()
    placed = bp.place(view, prompts, 0.5)
    (g,) = view.units
    rank = s1.sealed_rank(sorted(view.tokens), "plant.quartile_ties")
    order = sorted(view.members[g], key=lambda r: (view.tokens[r], rank[r]))
    qorder = s1.sealed_order(sorted(view.tokens), "plant.quarters")
    for j in range(4):
        quartile = order[150 * j:150 * (j + 1)]
        assert placed["cells"][f"{g}/q{j}"] == sorted(quartile)
        inside = [r for r in qorder if r in set(quartile)]
        bounds = [0, 37, 75, 112, 150]
        for i in range(4):
            assert placed["cells"][f"{g}/q{j}/r{i}"] == sorted(inside[bounds[i]:bounds[i + 1]])
    assert placed["report"]["links_within_units"] == 0 and placed["oversize_rows"] == []


def test_a_cross_unit_near_pair_is_counted_and_never_linked():
    """L12 (1): a near pair across two units is counted only; neither unit gets a link or a component."""
    view, prompts, rng = stub(n_units=2)
    a, b = view.members[view.units[0]][5], view.members[view.units[1]][7]
    prompts[b] = fw.swap_last_word(prompts[a], rng)
    sets = bp.shingle_sets({a: prompts[a], b: prompts[b]})
    assert bp.jaccard(sets[a], sets[b]) >= 0.5
    placed = bp.place(view, prompts, 0.5)
    report = placed["report"]
    assert report["cross_unit_pairs"] == 1 and report["links_within_units"] == 0 and report["components"] == []
    assert report["component_sizes"] == {g: {"1": 600} for g in view.units} and placed["oversize_rows"] == []
    rank = s1.sealed_rank(sorted(view.tokens), "plant.quartile_ties")
    for g in view.units:                                                 # the plain positional rule in both units
        order = sorted(view.members[g], key=lambda r: (view.tokens[r], rank[r]))
        for j in range(4):
            assert placed["cells"][f"{g}/q{j}"] == sorted(order[150 * j:150 * (j + 1)])


def test_quartile_ties_break_by_the_sealed_rank_over_all_training_rows():
    """L12 (3): with every target_tokens equal the quartile order is the sealed rank plant.quartile_ties over ALL
    training row ids (not a rank over the unit's rows alone, which gives another q0 here)."""
    view, prompts, _ = stub(n_units=2)
    view.tokens = {r: 7 for r in view.tokens}
    placed = bp.place(view, prompts, 0.5)
    all_rank = s1.sealed_rank(sorted(view.tokens), "plant.quartile_ties")
    for g in view.units:
        order = sorted(view.members[g], key=lambda r: all_rank[r])
        unit_rank = s1.sealed_rank(view.members[g], "plant.quartile_ties")
        assert sorted(order[:150]) != sorted(sorted(view.members[g], key=lambda r: unit_rank[r])[:150])
        for j in range(4):
            assert placed["cells"][f"{g}/q{j}"] == sorted(order[150 * j:150 * (j + 1)])
        cuts = placed["report"]["quartile_cut_points"][g]
        assert [(c["rows"], c["first_target_tokens"], c["last_target_tokens"]) for c in cuts] == [(150, 7, 7)] * 4


def test_an_oversize_component_is_placed_as_singletons_and_published():
    view, prompts, rng = stub()
    (g,) = view.units
    seed_text = fw.sentence(rng, 9)
    cluster = view.members[g][100:138]                                  # 38 rows: one component, oversize
    for r in cluster:
        prompts[r] = seed_text + " " + fw.word(rng)
    placed = bp.place(view, prompts, 0.5)
    assert sorted(placed["oversize_rows"]) == sorted(cluster)
    (over,) = placed["report"]["oversize_components"]
    assert over["size"] == 38 and over["cross_cell_pairs_m32"] >= 0 and over["cross_cell_pairs_m128"] > 0
    with_cluster = [c for c, rows in placed["cells"].items() if c.count("/") == 2 and set(rows) & set(cluster)]
    assert len(with_cluster) > 1                                         # singletons spread over the leaves
    # L12 (2) and (6): the published counts are exact: the histogram, the oversize component's cross-cell pairs at
    # M = 32 and M = 128 (its link set against the cells), every cell's size and every quartile cut point
    report = placed["report"]
    assert report["component_sizes"] == {g: {"1": 562, "38": 1}} and report["components"] == []
    assert report["links_within_units"] == len(bp.linked_pairs(bp.shingle_sets({r: prompts[r] for r in cluster}), 0.5))
    cpairs = bp.linked_pairs(bp.shingle_sets({r: prompts[r] for r in cluster}), 0.5)
    cell_of = {lvl: {r: c for c, rows in placed["cells"].items() if c.count("/") == lvl for r in rows} for lvl in (1, 2)}
    assert over == {"unit": g, "size": 38,
                    "cross_cell_pairs_m32": sum(cell_of[1][a] != cell_of[1][b] for a, b in cpairs),
                    "cross_cell_pairs_m128": sum(cell_of[2][a] != cell_of[2][b] for a, b in cpairs)}
    assert over["cross_cell_pairs_m32"] < over["cross_cell_pairs_m128"] <= len(cpairs)
    assert report["cell_sizes"] == {c: len(rows) for c, rows in placed["cells"].items()}
    cuts = report["quartile_cut_points"][g]
    assert [c["cell"] for c in cuts] == [f"{g}/q{j}" for j in range(4)]
    for c in cuts:
        rows = placed["cells"][c["cell"]]
        assert c["rows"] == len(rows) == 150
        assert (c["first_target_tokens"], c["last_target_tokens"]) == (min(view.tokens[r] for r in rows),
                                                                      max(view.tokens[r] for r in rows))
    assert all(cuts[j]["last_target_tokens"] <= cuts[j + 1]["first_target_tokens"] for j in range(3))
    leaf = bp.draw_leaf(view, placed, g, "plant.leaf")
    clean37 = [c for c, rows in placed["cells"].items()
               if c.startswith(g + "/") and c.count("/") == 2 and len(rows) == 37 and c not in with_cluster]
    assert leaf["cell"] not in with_cluster and leaf["candidates"] == len(clean37)
    assert leaf["cell"] == s1.sealed_order(clean37, "plant.leaf")[0]


def test_a_small_component_moves_whole_and_an_empty_cell_stops():
    view, prompts, rng = stub()
    (g,) = view.units
    seed_text = fw.sentence(rng, 9)
    group = view.members[g][:30]
    for r in group:
        prompts[r] = seed_text + " " + fw.word(rng)
    placed = bp.place(view, prompts, 0.5)
    holder = [c for c, rows in placed["cells"].items() if c.count("/") == 2 and set(group) & set(rows)]
    assert len(holder) == 1                                              # one component, one leaf
    assert set(group) <= set(placed["cells"][holder[0]])
    # T1 placement.published: the component's size and its cell (both levels) are in the report
    assert placed["report"]["components"] == [{"unit": g, "size": 30, "cell_m32": holder[0].rsplit("/", 1)[0],
                                               "cell_m128": holder[0]}]
    assert placed["report"]["component_sizes"][g] == {"1": 570, "30": 1} and placed["report"]["oversize_components"] == []
    tiny, tiny_prompts, rng = stub(rows=8)
    (t,) = tiny.units
    text = fw.sentence(rng, 9)
    for r in tiny.members[t][:7]:
        tiny_prompts[r] = text + " " + fw.word(rng)
    with pytest.raises(s1.Refusal, match="cells are empty"):
        bp.place(tiny, tiny_prompts, 0.5)


def test_the_walk_closes_one_cell_per_placement():
    """T1's n = 114 example through build_plant's own walk: [57, 1, 27, 29] (the cascade reading gives an empty cell)."""
    order = [f"r{i:03d}" for i in range(114)]
    big = order[21:22] + order[60:95]
    component_of = {r: (big if r in big else [r]) for r in order}
    assert [len(c) for c in bp.walk(order, component_of, 114)] == [57, 1, 27, 29]


def test_the_leaf_fallback_and_never_a_38_row_leaf_beside_a_37():
    view, prompts, _ = stub()
    placed = bp.place(view, prompts, 0.5)
    (g,) = view.units
    leaf = bp.draw_leaf(view, placed, g, "plant.leaf")
    exact = [c for c, rows in placed["cells"].items() if c.count("/") == 2 and len(rows) == 37]
    assert leaf["branch"] == "37-row" and leaf["n"] == 37 and leaf["cell"] == s1.sealed_order(exact, "plant.leaf")[0]
    assert leaf["candidates"] == len(exact) == 8                         # 37 and 38 alternate in each quartile
    for c in exact:                                                      # no 37-row leaf left: the fallback
        placed["cells"][c] = placed["cells"][c] + ["r-extra-" + c]
    fallback = bp.draw_leaf(view, placed, g, "plant.leaf")
    assert fallback["branch"] == "fallback" and fallback["n"] == 38


def test_the_fallback_tie_36_and_38_gives_the_sealed_first_of_both(tmp_path):
    """Addendum 4.3's tie test: no 37-row leaf; one 36-row and one 38-row no-oversize leaf are the candidates (the
    smallest |n - 37|, not the smallest n or the largest); a 40-row leaf and a leaf holding an oversize row are not."""
    g = "g-0000000000000000"
    cells = {f"{g}/q0/r0": [f"a{i:03d}" for i in range(36)], f"{g}/q0/r1": [f"b{i:03d}" for i in range(38)],
             f"{g}/q0/r2": [f"c{i:03d}" for i in range(40)], f"{g}/q0/r3": [f"d{i:03d}" for i in range(37)],
             f"{g}/q0": [], f"{g}/q1/r0": [f"e{i:03d}" for i in range(37)], "g-0000000000000001/q0/r0": ["z000"]}
    placed = {"cells": cells, "oversize_rows": ["d000", "e000"]}         # the two 37-row leaves hold an oversize row
    both = [f"{g}/q0/r0", f"{g}/q0/r1"]
    for key in (("plant.leaf",), ("plant.decoy_leaf",), ("plant.extra_leaf", 2), ("plant.extra_leaf", 3)):
        leaf = bp.draw_leaf(None, placed, g, *key)
        assert leaf["branch"] == "fallback" and leaf["candidates"] == 2
        assert leaf["cell"] == s1.sealed_order(both, *key)[0] and leaf["n"] == len(cells[leaf["cell"]])
    placed["oversize_rows"] = ["a000", "b000", "c000", "d000", "e000"]
    with pytest.raises(s1.Refusal, match="no eligible leaf"):
        bp.draw_leaf(None, placed, g, "plant.leaf")


def _leaves(r: dict, unit: str, n: int = 37) -> list[str]:
    """The unit's candidate leaves in the record (its n-row leaves; the record has no oversize component)."""
    assert r["grouping"]["oversize_components"] == []
    return [c for c, size in r["grouping"]["cell_sizes"].items() if c.startswith(unit + "/") and c.count("/") == 2 and size == n]


# ----- the draws and the edits ---------------------------------------------------------------------------------


def test_the_unit_and_leaf_draws_and_the_planted_corpus(env):
    r = rec(env)
    world_view = s1.PreparedView(env["world"].prepared_root, env["world"].manifest_sha256)
    assert r["unit"] == s1.sealed_order(world_view.units, "plant.unit")[0]
    assert r["leaf"]["cell"].startswith(r["unit"] + "/") and r["leaf"]["n"] == 37 and r["leaf"]["branch"] == "37-row"
    candidates = _leaves(r, r["unit"])
    assert r["leaf"]["candidates"] == len(candidates) == 8
    assert r["leaf"]["cell"] == s1.sealed_order(candidates, "plant.leaf")[0]
    assert r["leaf"]["cell"] != s1.sealed_order(candidates, "plant.decoy_leaf")[0]          # the key is decisive here
    by = {e["file"]: e for e in r["edits"]}
    assert by["edits/planted_k37.json"]["final_rows"] == 4800 - 37 + 37 and by["edits/planted_k37.json"]["steps"] == 38
    assert by["edits/planted_k75.json"]["final_rows"] == 4800 - 37 + 75
    assert by["edits/remove_cell_m8.json"]["removed"] == 600 and by["edits/remove_cell_m128.json"]["removed"] == 37
    q = r["leaf"]["cell"].rsplit("/", 1)[0]
    assert by["edits/remove_cell_m32.json"]["removed"] == r["grouping"]["cell_sizes"][q]
    # the removed SETS: the planted cell at each M (addendum section 3; REC (g) rule 20), not only their sizes
    full, out = built(env)
    cells = _placed(env)["cells"]
    assert r["grouping"]["cell_sizes"] == {c: len(rows) for c, rows in cells.items()}
    removed = {m: set(json.loads(out[f"edits/remove_cell_{m}.json"])["remove"]) for m in ("m8", "m32", "m128")}
    assert removed["m8"] == set(world_view.members[r["unit"]])
    assert removed["m32"] == set(cells[q]) and removed["m128"] == set(cells[r["leaf"]["cell"]])
    assert removed["m128"] < removed["m32"] < removed["m8"]
    for k in (37, 75):
        planted = parse_edit(full[f"edits/planted_k{k}.json"], _stub(env))
        assert set(planted.removed) == removed["m128"] and len(planted.added) == k


def test_every_edit_parses_and_the_random_draws_follow_the_rule(env):
    full, out = built(env)
    stub_ = _stub(env)
    view = s1.PreparedView(env["world"].prepared_root, env["world"].manifest_sha256)
    r = rec(env)
    leaf_rows = set(json.loads(out["edits/remove_cell_m128.json"])["remove"])
    for name, data in list(full.items()) + list(out.items()):
        if name.startswith("edits/"):
            parse_edit(data, stub_)
    for k in (37, 75):
        for d in (1, 2, 3):
            edit = parse_edit(full[f"edits/r600_k{k}_d{d}.json"], stub_)
            members = bp.planted_members(view, {"unit": r["unit"], "rows": sorted(leaf_rows)}, k)
            drawn = {x for g in view.units for x in s1.sealed_sample(members[g], 75, "plant.r600", d, g)}
            assert set(edit.removed) == leaf_rows | {x for x in drawn if not x.startswith("add-")}
            assert {a for a, _, _ in edit.added} == {f"add-plant-{j:03d}" for j in range(1, k + 1)} - drawn
            e150 = parse_edit(full[f"edits/r150_k{k}_d{d}.json"], stub_)
            assert len(set(e150.removed) - leaf_rows) + (k - len(e150.added)) == 150
            # T1 edits.r150: the six 19-row units by plant.r150_units (d); each unit's rows by plant.r150 (d, g)
            six = set(s1.sealed_sample(view.units, 6, "plant.r150_units", d))
            drawn150 = {x for g in view.units
                        for x in s1.sealed_sample(members[g], 19 if g in six else 18, "plant.r150", d, g)}
            assert set(e150.removed) == leaf_rows | {x for x in drawn150 if not x.startswith("add-")}
            assert {a for a, _, _ in e150.added} == {f"add-plant-{j:03d}" for j in range(1, k + 1)} - drawn150
            per_unit = {g: sum(1 for x in drawn150 if x in set(members[g])) for g in view.units}
            assert sorted(per_unit.values()) == [18, 18] + [19] * 6 and {g for g, n in per_unit.items() if n == 19} == six
    assert r["seeds"]["r600_k37_d1"] == 1101 and r["seeds"]["r150_k75_d3"] == 1103


def test_the_pools_for_req3(env):
    plant = full_of(env, "plant.pool.json")
    assert plant["name"] == "plant" and [i["id"] for i in plant["items"]] == [f"add-plant-{j:03d}" for j in range(1, 76)]
    decoy = full_of(env, "decoy.pool.json")
    assert decoy["name"] == "decoy" and len(decoy["items"]) == 37


# ----- the decoy (W1-09) and F9 --------------------------------------------------------------------------------


def test_the_decoy(env):
    r = rec(env)
    d = r["decoy"]
    lists = set().union(*(json.loads(spool(env)[2][f"{n}.json"])["items"] and
                          {i["id"] for i in json.loads(spool(env)[2][f"{n}.json"])["items"]}
                          for n in ("s1", "s3_subset", "s4_candidates")))
    pool = [i["id"] for i in json.loads(spool(env)[2][bsp.POOL_FILE])["items"]]
    assert d["ids"] == s1.sealed_order(sorted(set(pool) - lists), "plant.decoy_rows")[:37] and not set(d["ids"]) & lists
    view = s1.PreparedView(env["world"].prepared_root, env["world"].manifest_sha256)
    assert d["unit"] == s1.sealed_order([u for u in view.units if u != r["unit"]], "plant.decoy_unit")[0] != r["unit"]
    assert d["leaf"]["cell"].startswith(d["unit"] + "/")
    # W1-09: the decoy leaf by the plant's leaf rule under its own key plant.decoy_leaf (not the plant's key)
    candidates = _leaves(r, d["unit"])
    assert d["leaf"]["candidates"] == len(candidates) == 8 and d["leaf"]["branch"] == "37-row" and d["leaf"]["n"] == 37
    assert d["leaf"]["cell"] == s1.sealed_order(candidates, "plant.decoy_leaf")[0]
    assert d["leaf"]["cell"] != s1.sealed_order(candidates, "plant.leaf")[0]                # the key is decisive here
    anchors = {a.lower() for a in env["world"].anchors}
    assert not {i["prompt"].lower() for i in full_of(env, "decoy.pool.json")["items"]} & anchors


def test_the_plant_is_the_same_with_another_decoy_and_t1_settings_are_unchanged(env):
    assert sha256_file(bp.SETTINGS_PATH) == bp.SETTINGS_SHA256 == \
        "06f70d98af8ac16d79067863142a408f0e65862463305975579f075763f8687e"
    s, x = settings_for(env["world"])
    x["decoy"]["rows"] = 30
    full, out = run(env["world"], inputs(env), extra=x)
    base_full, base_out = built(env)
    assert {n: v for n, v in full.items() if n.startswith("edits/")} == \
        {n: v for n, v in base_full.items() if n.startswith("edits/")}
    assert {n: v for n, v in out.items() if n.startswith("edits/")} == \
        {n: v for n, v in base_out.items() if n.startswith("edits/")}


def test_f9_runs_only_when_asked(env):
    assert rec(env)["f9"] == {"run": False, "locations": {}}
    full, out = run(env["world"], inputs(env), f9=True)
    r = json.loads(out[bp.RECORD])
    units = [r["f9"]["locations"][str(loc)]["unit"] for loc in (2, 3)]
    assert len(set(units + [r["unit"]])) == 3
    view = s1.PreparedView(env["world"].prepared_root, env["world"].manifest_sha256)
    assert units[0] == s1.sealed_order([u for u in view.units if u != r["unit"]], "plant.extra_unit", 2)[0]
    assert units[1] == s1.sealed_order([u for u in view.units if u not in (r["unit"], units[0])], "plant.extra_unit", 3)[0]
    assert "edits/planted_k37_loc2.json" in full and "edits/remove_cell_m8_loc3.json" in out
    # each location's leaf by the plant's leaf rule under plant.extra_leaf, part = location (not the plant's key)
    by = {e["file"]: e for e in r["edits"]}
    stub_ = _stub(env)
    for loc in (2, 3):
        got = r["f9"]["locations"][str(loc)]
        candidates = _leaves(r, got["unit"])
        assert got["candidates"] == len(candidates) == 8 and got["n"] == 37
        assert got["cell"] == s1.sealed_order(candidates, "plant.extra_leaf", loc)[0]
        assert got["cell"] != s1.sealed_order(candidates, "plant.leaf")[0]                   # the key is decisive here
        for name, data in list(full.items()) + list(out.items()):
            if name.startswith("edits/") and name.endswith(f"_loc{loc}.json"):
                parse_edit(data, stub_)
        assert by[f"edits/planted_k37_loc{loc}.json"]["final_rows"] == 4800 - got["n"] + 37
        assert by[f"edits/planted_k75_loc{loc}.json"]["final_rows"] == 4800 - got["n"] + 75
        assert by[f"edits/remove_cell_m128_loc{loc}.json"]["removed"] == got["n"]
        assert by[f"edits/remove_cell_m8_loc{loc}.json"]["removed"] == 600
        # the removed sets are the location's own cells
        cells = _placed(env)["cells"]
        assert set(json.loads(out[f"edits/remove_cell_m8_loc{loc}.json"])["remove"]) == set(view.members[got["unit"]])
        assert set(json.loads(out[f"edits/remove_cell_m128_loc{loc}.json"])["remove"]) == set(cells[got["cell"]])
        assert set(json.loads(out[f"edits/remove_cell_m32_loc{loc}.json"])["remove"]) == \
            set(cells[got["cell"].rsplit("/", 1)[0]])
        assert set(parse_edit(full[f"edits/planted_k37_loc{loc}.json"], stub_).removed) == set(cells[got["cell"]])
    # the two locations' parts are decisive here: part (2) and part (3) pick different leaves of location 3's unit
    cands3 = _leaves(r, r["f9"]["locations"]["3"]["unit"])
    assert s1.sealed_order(cands3, "plant.extra_leaf", 2)[0] != s1.sealed_order(cands3, "plant.extra_leaf", 3)[0]
    assert sorted(n for n in list(full) + list(out) if "_loc" in n) == sorted(
        f"edits/{stem}_loc{loc}.json" for loc in (2, 3)
        for stem in ("planted_k37", "planted_k75", "remove_cell_m128", "remove_cell_m32", "remove_cell_m8"))
    # the plant's own files are byte-identical with and without --f9
    base_full, base_out = built(env)
    assert {n: v for n, v in full.items() if "_loc" not in n} == base_full
    assert {n: v for n, v in out.items() if "_loc" not in n and n != bp.RECORD} == {n: v for n, v in base_out.items() if n != bp.RECORD}


def test_the_decoy_unit_is_never_the_planted_unit():
    """For every possible planted unit, the decoy unit is another one, the first of the 7-unit sealed order."""
    import s1fixtures as fx
    units = [fx.unit_id(u) for u in range(8)]
    for plant_unit in units:
        others = [u for u in units if u != plant_unit]
        assert bp.decoy_unit_of(units, plant_unit) == s1.sealed_order(others, "plant.decoy_unit")[0] != plant_unit


def test_the_f9_units_are_drawn_without_replacement():
    """sealed_order's shuffle depends on the key, the parts and the list length only. Over 3 candidate units the two
    locations' orders start with the same position, so a draw with replacement would repeat a unit; without
    replacement, location 3 draws from the 2 units left."""
    for plant in range(4):
        units = [f"g-{u:016x}" for u in range(4)]
        others = [u for u in units if u != units[plant]]
        got = bp.extra_units_of(units, units[plant], [2, 3])
        assert got[2] == s1.sealed_order(others, "plant.extra_unit", 2)[0]
        assert got[3] == s1.sealed_order([u for u in others if u != got[2]], "plant.extra_unit", 3)[0] != got[2]
    assert s1.sealed_order(others, "plant.extra_unit", 2)[0] == s1.sealed_order(others, "plant.extra_unit", 3)[0]


# ----- text, determinism, settings ------------------------------------------------------------------------------


def test_text_free_outputs_and_determinism(env):
    full, out = built(env)
    texts = env["world"].texts()
    for name, data in out.items():
        for t in texts:
            assert t.encode() not in data, name
    assert run(env["world"], inputs(env)) == built(env)


# ----- main(): the literal pins and --f9 reach build, nothing is written on a refusal -------------------------------


def _argv(tmp_path, full="full", out="out") -> list[str]:
    p, h = str(tmp_path / "absent"), "0" * 64
    argv = []
    for flag in ("--prepared", "--config", "--sources", "--anchors", "--rec", "--recipe"):
        argv += [flag, p]
    argv += ["--full-out", str(tmp_path / "tmp" / full), "--out", str(tmp_path / out), "--s-pool", f"{p}:{h}"]
    for name in ("s1", "s3_subset", "s4_candidates"):
        argv += ["--list", f"{name}={p}:{h}"]
    return argv


def _patch_main(monkeypatch, calls: list):
    monkeypatch.setattr(bsp, "real_codec", lambda *a, **k: "codec")
    monkeypatch.setattr(bp, "build", lambda **kw: calls.append(kw) or ({"plant_rows.json": b"{}"}, {bp.RECORD: b"{}"}))


@pytest.mark.parametrize("flag", [False, True])
def test_main_loads_both_settings_by_their_literal_pins_and_passes_f9_only_when_given(tmp_path, monkeypatch, flag):
    calls = []
    _patch_main(monkeypatch, calls)
    assert bp.main(_argv(tmp_path) + (["--f9"] if flag else [])) == 0
    (kw,) = calls
    assert kw["f9"] is flag and kw["codec"] == "codec"
    assert kw["settings_sha256"] == bp.SETTINGS_SHA256 == "06f70d98af8ac16d79067863142a408f0e65862463305975579f075763f8687e"
    assert kw["extra_sha256"] == bp.EXTRA_SHA256 and kw["settings"]["name"] == bp.SETTINGS_NAME
    assert kw["extra"]["name"] == bp.EXTRA_NAME and kw["s_pool"] == (tmp_path / "absent", "0" * 64)
    assert set(kw["lists"]) == {"s1", "s3_subset", "s4_candidates"}
    assert (tmp_path / "tmp" / "full" / "plant_rows.json").exists() and (tmp_path / "out" / bp.RECORD).exists()


@pytest.mark.parametrize("which", ["SETTINGS_PATH", "EXTRA_PATH"])
def test_main_refuses_a_changed_settings_file_before_build(tmp_path, monkeypatch, capsys, which):
    """Addendum 4.5: T1's build_plant.json (and the extra file) are loaded by their literal SHA-256; one changed byte
    refuses before build is called."""
    calls = []
    _patch_main(monkeypatch, calls)
    changed = tmp_path / "changed.json"
    changed.write_bytes(getattr(bp, which).read_bytes() + b"\n")           # still valid JSON, another SHA-256
    monkeypatch.setattr(bp, which, changed)
    assert bp.main(_argv(tmp_path)) == 2 and not calls
    err = capsys.readouterr().err
    assert "hash to" in err and "(nothing written)" in err and not (tmp_path / "tmp").exists()


def test_main_refuses_wrong_lists_and_a_non_empty_out_folder_before_anything_is_written(tmp_path, monkeypatch, capsys):
    calls = []
    _patch_main(monkeypatch, calls)
    assert bp.main(_argv(tmp_path)[:-2]) == 2 and not calls                 # one list missing
    assert "give exactly the lists" in capsys.readouterr().err
    outside = _argv(tmp_path)
    outside[outside.index("--full-out") + 1] = "/var/stage1-plant-full"      # no folder named tmp on the path
    assert bp.main(outside) == 2 and not calls and "named tmp" in capsys.readouterr().err
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "earlier.json").write_bytes(b"{}")
    assert bp.main(_argv(tmp_path)) == 2 and not calls
    err = capsys.readouterr().err
    assert "exists and is not empty" in err and "(nothing written)" in err and str(tmp_path / "out") in err
    assert not (tmp_path / "tmp").exists()
    # a write error after the full files went out is reported as what it left, never as 'nothing written'
    real = s1.write_new_files
    monkeypatch.setattr(s1, "write_new_files", lambda d, f: (_ for _ in ()).throw(OSError(28, "x")) if d.name == "o4"
                        else real(d, f))
    assert bp.main(_argv(tmp_path, full="f4", out="o4")) == 2 and len(calls) == 1
    err = capsys.readouterr().err
    assert "REFUSED: OSError (1 files left under the output folders)" in err and "nothing written" not in err


def test_the_extra_settings_are_literal_pinned():
    doc, digest = s1.load_settings(bp.EXTRA_PATH, bp.EXTRA_SHA256, bp.EXTRA_NAME)
    assert set(doc["label_entries"]) == {"plant.decoy_rows", "plant.decoy_unit", "plant.decoy_leaf", "plant.extra_unit",
                                         "plant.extra_leaf"}
    assert doc["decoy"]["rows"] == 37 and doc["f9"]["locations"] == [2, 3]
    assert doc["inputs"]["recipe_sha256"] == "ceffe0efb5d75bacfbd62743f530259deeedeca8950605d1bd3ff66e5391fe46"
