"""Parity (P78:357; the readiness plan T6): the wrapper's route (the 1B script's own main(), run by scorers_78b.run_main
with a settings file) gives the same bytes as the 1B script's function called as the 1B tests call it, on the 1B
fixtures (the engine's tiny model and byte codec; synthetic prepared sets), for every kind: untuned_answers, rep_pass,
l1_scan, classifier (pod; the model loader replaced by the engine's fixture loaders, as the 1B tests do), l1_score,
s3_score, score_edit, add_edit and s_pool (Mac). Wall-clock cost fields are the only difference allowed (the 1B
determinism tests drop them the same way). CPU only; CUDA paths stay untested, as in the 1B scripts."""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from scripts.scale78b import scorers_78b as sw  # noqa: E402
from scripts.stage1 import build_s_pool as bsp  # noqa: E402
from scripts.stage1 import make_untuned_answers as mua  # noqa: E402
from scripts.stage1 import representation_pass as rp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import score_classifier as sc  # noqa: E402
from scripts.stage1 import score_l1_larf as l1  # noqa: E402
from scripts.stage1 import score_s3_datarx as s3  # noqa: E402
from scripts.stage1 import write_add_edit as wae  # noqa: E402
from scripts.stage1 import write_score_edit as wse  # noqa: E402

import s1fixtures as fx  # noqa: E402
import s1fixtures_b3b as fw  # noqa: E402
import ss_fixtures as sfx  # noqa: E402
import test_build_s_pool as tbs  # noqa: E402
import test_make_untuned_answers as tmua  # noqa: E402
import test_representation_pass as trp  # noqa: E402
import test_score_classifier as tsc  # noqa: E402
import test_score_l1_larf as tl1  # noqa: E402

env = trp.env                       # the 1B representation-pass fixture (prepared set, recipe, anchors, pinned settings)
recipe_files = tmua.recipe_files    # the 1B untuned-answers fixture recipes (REC = S, batch size 4)
LOADERS = "experiments.safety_selection.loaders.real_loaders"


# ----- helpers ----------------------------------------------------------------------------------------------------------


def settings_file(tmp_path: Path, doc: dict, name: str = "settings.json") -> tuple[Path, str]:
    data = json.dumps(doc, indent=2, sort_keys=True).encode()
    path = tmp_path / name
    path.write_bytes(data)
    return path, sha256_bytes(data)


def strip_costs(node):
    """Drop the wall-clock fields (costs blocks and *seconds), as the 1B determinism tests do."""
    if isinstance(node, dict):
        return {k: strip_costs(v) for k, v in node.items() if k != "costs" and not k.endswith("seconds")}
    if isinstance(node, list):
        return [strip_costs(v) for v in node]
    return node


def assert_same_files(expected: dict[str, bytes], out: Path, exact: bool = True, extra_allowed: set = frozenset()):
    written = {p.name: p.read_bytes() for p in out.iterdir() if p.is_file()}
    assert set(written) - extra_allowed == set(expected), (sorted(written), sorted(expected))
    for name, data in expected.items():
        if written[name] == data:
            continue
        assert not exact or name.endswith(".json"), name
        assert strip_costs(json.loads(written[name])) == strip_costs(json.loads(data)), name
        assert strip_costs(json.loads(written[name])) != {}


def pool_pins_pair(family="olmo2-7b"):
    from scripts.scale78b import make_scorer_settings_78b as mk

    path = mk.SETTINGS_DIR / mk.file_name("representation_pools", family)
    return path, sha256_file(path), json.loads(path.read_bytes())


def prompt_list(root: Path, name: str, n: int) -> tuple[Path, str]:
    items = [{"id": f"c-{i:03d}", "prompt": f"Synthetic question {i}: how are tides measured in harbour {i % 7}?"} for i in range(n)]
    data = canonical_json({"kind": "stage1 prompt list", "version": 1, "name": name, "items": items})
    path = root / f"{name}.json"
    path.write_bytes(data)
    return path, sha256_bytes(data)


# ----- the pod kinds ---------------------------------------------------------------------------------------------------


def test_untuned_answers_parity(recipe_files, tmp_path, monkeypatch):
    """The wrapper's main() route equals the 1B run() on the engine's tiny model (every answer is capped at the fixture's
    5 new tokens, so both keep 0 and exit 3; the files are the same bytes but for the wall-clock fields)."""
    rec_path, s_path, rec = recipe_files
    monkeypatch.setattr(LOADERS, lambda: sfx.fixture_loaders())
    s4 = prompt_list(tmp_path, "s4", 40)
    doc = tmua.settings_for(rec, keep=6)
    path, sha = settings_file(tmp_path, doc)
    api, code_api = mua.run(rec_path=rec_path, s_path=s_path, lists={"s4": s4}, losses={}, loaders=sfx.fixture_loaders(),
                            settings=doc, settings_sha256=sha)
    out = tmp_path / "out"
    code = sw.run_main(mua, ["--recipe", str(rec_path), "--recipe-s", str(s_path), "--list", f"s4={s4[0]}:{s4[1]}",
                             "--out", str(out)], path, sha)
    assert code == code_api == mua.EXIT_FEW
    assert_same_files(api, out, exact=False)
    record = json.loads((out / mua.RECORD).read_bytes())
    assert record["lists"]["s4"]["answered"] == 40 and record["provenance"]["settings_sha256"] == sha
    assert all({"id", "kept", "drop", "answer_sha256"} <= set(r) for r in record["lists"]["s4"]["rows"])   # the dose builder's shapes


def test_the_first_keeps_do_not_depend_on_the_stop_rule(recipe_files, tmp_path):
    """Part 1 section 10: the stop rule moves from the chunk that holds the 48th keep to the chunk that holds the 192nd,
    and the first 48 are unchanged (here 2 and 6 on a 40-prompt list in chunks of 4, with the 1B test's generator)."""
    rec_path, s_path, rec = recipe_files
    s4 = prompt_list(tmp_path, "s4", 40)
    results = {}
    for keep in (6, 2):
        doc = tmua.settings_for(rec, keep=keep)
        files, code = mua.run(rec_path=rec_path, s_path=s_path, lists={"s4": s4}, losses={}, loaders=sfx.fixture_loaders(),
                              settings=doc, settings_sha256="e" * 64, generate=tmua.FakeGenerator(sfx.fixture_codec()))
        assert code == 0
        results[keep] = json.loads(files[mua.RECORD])["lists"]["s4"]
    kept6 = [r["id"] for r in results[6]["rows"] if r["kept"]]
    kept2 = [r["id"] for r in results[2]["rows"] if r["kept"]]
    assert results[6]["kept"] == 6 and results[2]["kept"] == 2 and kept6[:2] == kept2
    assert results[6]["chunks_run"] >= results[2]["chunks_run"]
    assert "kept_after_the_48th" in results[6]["drops"] or results[6]["chunks_run"] * 4 == 6 + sum(
        v for k, v in results[6]["drops"].items())                        # the 1B code's fixed label for a keep after the target


def test_rep_pass_parity(env, tmp_path, monkeypatch):
    monkeypatch.setattr(LOADERS, lambda: sfx.fixture_loaders())
    path, sha = settings_file(tmp_path, env.settings)
    pins_path, pins_sha, pins_doc = pool_pins_pair()
    api = rp.run(env.prepared, env.recipe, env.anchors, sfx.fixture_loaders(), env.settings, sha, [], True,
                 pool_pins=(pins_doc, pins_sha))
    out = tmp_path / "out"
    code = sw.run_main(rp, ["--prepared", str(env.prepared), "--recipe", str(env.recipe), "--anchors", str(env.anchors),
                            "--out", str(out)], path, sha, pool_pins=(pins_path, pins_sha))
    assert code == 0
    assert_same_files(api, out, exact=False)
    summary = json.loads((out / rp.SUMMARY_FILE).read_bytes())
    assert summary["pool_pins"]["sha256"] == pins_sha and summary["provenance"]["settings_sha256"] == sha
    assert (rp.POOL_PINS_PATH, rp.POOL_PINS_SHA256) == rp.load_pool_pins.__defaults__   # restored after the call
    for t in env.texts:
        assert t.encode() not in (out / rp.SUMMARY_FILE).read_bytes()


def test_l1_scan_parity(env, tmp_path, monkeypatch):
    loaders = trp.loaders_with(lambda: trp.tiny("olmo2", lora=True))
    monkeypatch.setattr(LOADERS, lambda: loaders)
    doc = tl1.settings_for(env, tl1.n_harmful(env), first_block=1, dolly=8)
    path, sha = settings_file(tmp_path, doc)
    api = l1.run_scan(prepared_root=env.prepared, recipe_path=env.recipe, anchors_path=env.anchors, loaders=loaders,
                      settings=doc, settings_sha256=sha)
    out = tmp_path / "out"
    code = sw.run_main(l1, ["scan", "--prepared", str(env.prepared), "--recipe", str(env.recipe), "--anchors", str(env.anchors),
                            "--out", str(out)], path, sha)
    assert code == 0
    assert_same_files(api, out, exact=False)
    scan = json.loads((out / l1.SCAN_FILE).read_bytes())
    assert scan["layout"]["n_layers"] == trp.N_LAYERS and 0 <= scan["l_s"] < trp.N_LAYERS


def test_classifier_parity(env, tmp_path, monkeypatch):
    monkeypatch.setattr(LOADERS, lambda: sfx.fixture_loaders())
    doc = tsc.settings_for(env, k=5)
    path, sha = settings_file(tmp_path, doc)
    pins_path, pins_sha, pins_doc = pool_pins_pair("llama31-8b")
    api = sc.run(prepared_root=env.prepared, recipe_path=env.recipe, anchors_path=env.anchors, loaders=sfx.fixture_loaders(),
                 settings=doc, settings_sha256=sha, pools=[], pool_pins=(pins_doc, pins_sha))
    out = tmp_path / "out"
    code = sw.run_main(sc, ["--prepared", str(env.prepared), "--recipe", str(env.recipe), "--anchors", str(env.anchors),
                            "--out", str(out)], path, sha, pool_pins=(pins_path, pins_sha))
    assert code == 0
    assert_same_files(api, out, exact=False)
    assert json.loads((out / sc.OUTPUT).read_bytes())["provenance"]["inputs"]["pool_pins"] == pins_sha


# ----- the Mac kinds ---------------------------------------------------------------------------------------------------


def l1_score_world(tmp_path: Path) -> dict:
    prep = fx.make_prepared(tmp_path / "p", units=8, rows_per_unit=6)
    view = s1.PreparedView(tmp_path / "p", prep["manifest_sha256"])
    n = 4
    lines = [{"id": r, "source": "dev", "unit": view.unit_of[r], "n_prompt": 3, "n_tokens": 9,
              "cos_harmful": [[0.01 * k + 0.001 * i, 0.0, 0.0, 0.0] for i in range(n + 1)],
              "cos_safe": [[0.002 * i, 0.0, 0.0, 0.0] for i in range(n + 1)], "css": [0.0] * (n + 1)}
             for k, r in enumerate(sorted(view.tokens))]
    rows_bytes = b"".join(json.dumps(l, sort_keys=True).encode() + b"\n" for l in lines)
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_bytes(rows_bytes)
    settings = copy.deepcopy(json.loads(l1.SETTINGS_PATH.read_bytes()))
    settings["pins"]["prepared_manifest_sha256"] = prep["manifest_sha256"]
    summary = {"kind": "stage1 representation pass", "layout": {"n_layers": n}, "costs": {},
               "rows": {"sha256": sha256_bytes(rows_bytes)},
               "provenance": {"settings_sha256": settings["pins"]["representation_pass_settings_sha256"]}}
    sp = tmp_path / "summary.json"
    sp.write_bytes(canonical_json(summary))
    scan = tmp_path / "scan.json"
    scan.write_bytes(canonical_json(tl1.scan_doc(n, 1)))
    return {"prepared": tmp_path / "p", "settings": settings, "rows": (rows_path, sha256_file(rows_path)),
            "summary": (sp, sha256_file(sp)), "scan": (scan, sha256_file(scan))}


def test_l1_score_parity(tmp_path):
    w = l1_score_world(tmp_path)
    path, sha = settings_file(tmp_path, w["settings"])
    api = l1.build_score(prepared_root=w["prepared"], scan=w["scan"], rows=w["rows"], summary=w["summary"],
                         settings=w["settings"], settings_sha256=sha)
    out = tmp_path / "out"
    code = sw.run_main(l1, ["score", "--prepared", str(w["prepared"]), "--scan", f"{w['scan'][0]}:{w['scan'][1]}",
                            "--rows", f"{w['rows'][0]}:{w['rows'][1]}", "--summary", f"{w['summary'][0]}:{w['summary'][1]}",
                            "--out", str(out)], path, sha)
    assert code == 0
    assert_same_files(api, out, exact=True)


def s3_world(tmp_path: Path, n: int = 4) -> dict:
    rng = random.Random(5)
    subset = [f"pku:{i:06d}:1" for i in range(12)]
    s1_ids = subset[:3] + [f"pku:{90 + i:06d}:1" for i in range(2)]
    scored = sorted(set(subset) | set(s1_ids))
    orig_present = [i for i in scored if rng.random() > 0.2]

    def line(rid, source):
        return {"id": rid, "source": source, "unit": None, "n_prompt": 3, "n_tokens": 8,
                "cos_harmful": [[rng.uniform(-1, 1), 0, 0, 0] for _ in range(n + 1)],
                "cos_safe": [[rng.uniform(-1, 1), 0, 0, 0] for _ in range(n + 1)], "css": [0.0] * (n + 1)}
    lines = [line(i, "s3_safe") for i in scored] + [line(f"{i}:orig", "s3_orig") for i in orig_present]
    rows_bytes = b"".join(json.dumps(l, sort_keys=True).encode() + b"\n" for l in lines)
    settings = copy.deepcopy(json.loads(s3.SETTINGS_PATH.read_bytes()))
    safe_sha, orig_sha = "a" * 64, "b" * 64
    summary = {"kind": "stage1 representation pass", "layout": {"n_layers": n}, "rows": {"sha256": sha256_bytes(rows_bytes)},
               "pools": [{"name": "s3_safe", "sha256": safe_sha}, {"name": "s3_orig", "sha256": orig_sha}],
               "provenance": {"settings_sha256": settings["pins"]["representation_pass_settings_sha256"]}}
    pool_rec = {"kind": "stage1 s-pool record", "s3_pool": {"sha256": safe_sha},
                "lists": {"s3_subset": {"ids": subset}, "s1": {"ids": s1_ids}}}
    ans_rec = {"kind": "stage1 untuned answers record",
               "lists": {"s3": {"list_sha256": safe_sha, "s3_orig_pool_sha256": orig_sha,
                                "rows": [{"id": i, "lex_class": "REFUSAL-OPENING" if k % 2 else "DIRECT", "capped": k % 5 == 0,
                                          "encode_train": None if i in orig_present else "ValueError"} for k, i in enumerate(scored)]}}}
    files = {}
    for name, data in (("rows.jsonl", rows_bytes), ("summary.json", canonical_json(summary)),
                       ("s_pool_record.json", canonical_json(pool_rec)), ("answers_record.json", canonical_json(ans_rec))):
        p = tmp_path / name
        p.write_bytes(data)
        files[name] = (p, sha256_bytes(data))
    return {"settings": settings, **files}


def test_s3_score_parity(tmp_path):
    w = s3_world(tmp_path)
    path, sha = settings_file(tmp_path, w["settings"])
    api = s3.build(rows=w["rows.jsonl"], summary=w["summary.json"], s_pool_record=w["s_pool_record.json"],
                   answers_record=w["answers_record.json"], settings=w["settings"], settings_sha256=sha)
    out = tmp_path / "out"
    code = sw.run_main(s3, ["--rows", f"{w['rows.jsonl'][0]}:{w['rows.jsonl'][1]}", "--summary", f"{w['summary.json'][0]}:{w['summary.json'][1]}",
                            "--s-pool-record", f"{w['s_pool_record.json'][0]}:{w['s_pool_record.json'][1]}",
                            "--answers-record", f"{w['answers_record.json'][0]}:{w['answers_record.json'][1]}", "--out", str(out)],
                       path, sha)
    assert code == 0
    assert_same_files(api, out, exact=True)
    assert json.loads((out / s3.OUTPUT).read_bytes())["reports"]["ranked"] >= 1


def scorer_world(tmp_path: Path) -> dict:
    prep = fx.make_prepared(tmp_path / "p")
    view = s1.PreparedView(tmp_path / "p", prep["manifest_sha256"])
    rng = random.Random(3)
    doc = {"kind": "stage1 scorer output", "version": 1, "scorer": "l1", "manifest_sha256": view.manifest_sha256,
           "orientation": "descending: high = remove", "scores": {r: rng.uniform(-1, 1) for r in view.tokens},
           "costs": {"scan": {"scan_seconds": 1.0}}, "provenance": {"script_sha256": "1" * 64, "settings_sha256": "2" * 64}}
    data = canonical_json(doc)
    scores = tmp_path / "l1_scores.json"
    scores.write_bytes(data)
    settings = copy.deepcopy(json.loads(wse.SETTINGS_PATH.read_bytes()))
    settings["prepared"]["manifest_sha256"] = prep["manifest_sha256"]
    return {"prep": prep, "settings": settings, "scores": (scores, sha256_bytes(data))}


def test_score_edit_scorer_parity(tmp_path):
    w = scorer_world(tmp_path)
    path, sha = settings_file(tmp_path, w["settings"])
    api = wse.build_scorer(w["prep"]["root"], "l1", w["scores"][0], w["scores"][1], w["settings"], sha)
    out = tmp_path / "out"
    code = sw.run_main(wse, ["scorer", "--name", "l1", "--scores", str(w["scores"][0]), "--scores-sha256", w["scores"][1],
                             "--prepared", str(w["prep"]["root"]), "--out", str(out)], path, sha)
    assert code == 0
    assert_same_files(api, out, exact=True)
    for t in w["prep"]["texts"]:
        for p in out.iterdir():
            assert t.encode() not in p.read_bytes()


def add_edit_world(tmp_path: Path) -> dict:
    prep = fx.make_prepared(tmp_path / "p")
    recipe = sfx.recipe()
    recipe_path = tmp_path / "recipe.json"
    recipe_path.write_text(json.dumps(recipe))
    items = [{"id": f"pku:{i:06d}:1", "prompt": f"Synthetic question {i}?", "response": f"Synthetic safe answer {i}."} for i in range(48)]
    data = canonical_json({"kind": "stage1 prompt list", "version": 1, "name": "s1", "items": items})
    listing = tmp_path / "s1.json"
    listing.write_bytes(data)
    settings = copy.deepcopy(json.loads(wae.SETTINGS_PATH.read_bytes()))
    settings["prepared_manifest_sha256"] = prep["manifest_sha256"]
    settings["recipe_sha256"] = config_sha256(recipe)
    return {"prep": prep, "recipe": recipe_path, "list": (listing, sha256_bytes(data)), "settings": settings,
            "listing": wae.read_list(listing, sha256_bytes(data))}


def test_add_edit_parity(tmp_path, monkeypatch):
    w = add_edit_world(tmp_path)
    monkeypatch.setattr(bsp, "real_codec", lambda prepared, settings: sfx.fixture_codec())
    path, sha = settings_file(tmp_path, w["settings"])
    full_api, record_api = wae.build(w["prep"]["root"], w["listing"], [], sfx.fixture_codec(), w["settings"], sha, w["recipe"])
    full_out, out = tmp_path / "tmp" / "full", tmp_path / "out"
    code = sw.run_main(wae, ["--prepared", str(w["prep"]["root"]), "--recipe", str(w["recipe"]), "--list", f"{w['list'][0]}:{w['list'][1]}",
                             "--full-out", str(full_out), "--out", str(out)], path, sha)
    assert code == 0
    assert_same_files(full_api, full_out, exact=True)
    assert_same_files(record_api, out, exact=True)


def test_s_pool_parity(tmp_path, monkeypatch):
    world = fw.SWorld(tmp_path / "w", fw.split_files(tbs.clean_records(40)))
    settings = world.settings(tbs.base(), **tbs.SMALL)
    monkeypatch.setattr(bsp, "real_codec", lambda prepared, s: world.sfx.fixture_codec())
    path, sha = settings_file(tmp_path, settings)
    full_api, record_api = bsp.build(config_path=world.config_path, sources_root=world.sources_root, prepared_root=world.prepared_root,
                                     anchors_path=world.anchors_path, rec_path=world.recipe_path, codec=world.sfx.fixture_codec(),
                                     settings=settings, settings_sha256=sha)
    full_out, out = tmp_path / "tmp" / "full", tmp_path / "out"
    code = sw.run_main(bsp, ["--config", str(world.config_path), "--sources", str(world.sources_root), "--prepared", str(world.prepared_root),
                             "--anchors", str(world.anchors_path), "--rec", str(world.recipe_path), "--full-out", str(full_out),
                             "--out", str(out)], path, sha)
    assert code == 0
    assert_same_files(full_api, full_out, exact=True)
    assert_same_files(record_api, out, exact=True)


# ----- the patch is scoped to the call --------------------------------------------------------------------------------


def test_the_settings_pin_is_restored_and_a_wrong_hash_refuses(tmp_path):
    w = l1_score_world(tmp_path)
    path, sha = settings_file(tmp_path, w["settings"])
    before = l1.SETTINGS_SHA256
    argv = ["score", "--prepared", str(w["prepared"]), "--scan", f"{w['scan'][0]}:{w['scan'][1]}", "--rows", f"{w['rows'][0]}:{w['rows'][1]}",
            "--summary", f"{w['summary'][0]}:{w['summary'][1]}", "--out", str(tmp_path / "o1")]
    assert sw.run_main(l1, argv, path, "0" * 64) == 2                       # the 1B main refuses the hash, nothing written
    assert l1.SETTINGS_SHA256 == before and not (tmp_path / "o1").exists()
    assert sw.run_main(l1, argv, path, sha) == 0 and l1.SETTINGS_SHA256 == before
