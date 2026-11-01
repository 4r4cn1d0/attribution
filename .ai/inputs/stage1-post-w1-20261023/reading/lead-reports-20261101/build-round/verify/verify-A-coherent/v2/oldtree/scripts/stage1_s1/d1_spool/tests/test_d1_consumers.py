"""Section 18 point 5: every consumer of REQ-6's outputs, fed the D-1 wrapper's outputs with an S3 subset of k rows
(k != the planned size), on one synthetic world (scripts/stage1/tests' fixtures: synthetic PKU files, a synthetic P of
8 units x 600 rows, the engine's tiny fixture model and codec). Nothing real is read.

The chain: D-1 (REQ-6) -> REQ-8 build_plant (the decoy draw from the rows outside the lists) -> REQ-9
make_untuned_answers (the s3_safe pool as list s3, with the committed s3 spec, and both loss lists) -> REQ-3
representation_pass (the pools s3_safe and s3_orig; the pool pins) -> REQ-11 score_s3_datarx (its real CLI, with the
D-1 record) -> write_score_add (its real CLI, the committed k = 48) -> REQ-7 write_add_edit's list reader; and
build_oext (the S-pool file) and commitments.py's classifier (the D-1 record and the D-1 package's files)."""

from __future__ import annotations

import copy
import json
import random

import pytest

torch = pytest.importorskip("torch")

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from scripts.stage1 import build_oext as bo  # noqa: E402
from scripts.stage1 import build_plant as bp  # noqa: E402
from scripts.stage1 import build_s_pool as w1bsp  # noqa: E402
from scripts.stage1 import commitments as cm  # noqa: E402
from scripts.stage1 import make_untuned_answers as mua  # noqa: E402
from scripts.stage1 import representation_pass as rp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import score_s3_datarx as s3  # noqa: E402
from scripts.stage1 import write_add_edit as wae  # noqa: E402
from scripts.stage1 import write_score_add as wsa  # noqa: E402
from scripts.stage1_s1.d1_spool import d1_s_pool as d1m  # noqa: E402

import d1fixtures as dx  # noqa: E402
from d1guard import guarded  # noqa: E402  (a wrapper defect fails the tests, never errors their setup)
import s1fixtures_b3b as fw  # noqa: E402
import test_build_oext as tbo  # noqa: E402  (its synthetic PHTest world)
import test_build_plant as tbp  # noqa: E402  (its settings helper and run())
import test_make_untuned_answers as tmu  # noqa: E402  (its fake chunk generator)
import test_representation_pass as trp  # noqa: E402  (its env fixture: the engine's fixture prepared set)

env = trp.env
sfx = trp.sfx
SCALE = {"s1n": 3, "s3": 100, "s4": 4, "decoy": 37, "k_min": 48, "k_below": 1}     # decoy 37 and k_min 48 as committed


@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    """D-1's outputs on a world of 120 refusal records (N = 120) plus 100 DIRECT records and a P of 8 x 600, written to
    disk as the lead would. The planned size 100 is below N, but the room rule binds (120 - 3 - 4 - 100 < 37), so
    48 <= k < 100: the S3 subset is not the planned size. Guarded: a D-1 refusal or defect here fails every test
    that reads the chain (d1guard), so a mutant of the wrapper is killed, not an invalid run."""
    root = tmp_path_factory.mktemp("chain")
    return guarded("chain", lambda: make_chain(root))


def make_chain(root):
    rng = random.Random(61)
    refusals = [fw.refusal_record(rng, swap=(i % 4 == 0)) for i in range(120)]
    directs = [fw.direct_record(rng, swap=(i % 5 == 0)) for i in range(100)]
    world = fw.SWorld(root / "w", fw.split_files(refusals + directs), corpus=fw.random_corpus())
    base = d1m.load_base(dx.committed_d1())
    w1, d1 = dx.scaled(world, **SCALE)
    full, records = dx.d1_build(world, base, w1, d1)
    out = root / "tmp" / "s-pool"
    out.mkdir(parents=True)
    for name, data in {**full, **records}.items():
        (out / name).write_bytes(data)
    pair = {name: (out / name, sha256_file(out / name)) for name in [*full, *records]}
    return {"root": root, "world": world, "w1": w1, "d1": d1, "full": full,
            "record": json.loads(records[w1bsp.RECORD]), "pair": pair, "cache": {}}


def test_the_chain_world_has_k_below_the_planned_size_and_w1_would_stop(chain):
    r = chain["record"]
    assert r["pool_rows"] == 120 and r["d1"]["k"] == dx.brute_k(
        [i["id"] for i in r["s_pool_sealed"]["items"]], 3, 4, 100, 37)
    assert 48 <= r["d1"]["k"] < 100 and len(r["lists"]["s3_subset"]["ids"]) == r["d1"]["k"]
    w1 = copy.deepcopy(chain["w1"])
    w1["min_pool"] = 120
    with pytest.raises(s1.Refusal, match="for 37 decoy rows"):                    # build_s_pool.py itself stops
        dx.w1_build(chain["world"], w1)


# ----- REQ-8: build_plant.py (the decoy draw) -------------------------------------------------------------------


def test_build_plant_draws_its_37_decoy_rows_from_the_d1_lists(chain):
    """build_plant.py:385-389 read the S-pool file and the three lists by kind and SHA-256 (no size check); :414-417
    draw the decoy as the first 37 of plant.decoy_rows over the S-pool minus the lists' union, refusing fewer. The
    37-row decoy pool then passes REQ-3's pool pins once its SHA-256 is filled (representation_pools.json pools.decoy:
    items 37, unchanged by D-1)."""
    p = chain["pair"]
    inputs = {"s_pool": p[w1bsp.POOL_FILE], "lists": {n: p[f"{n}.json"] for n in ("s1", "s3_subset", "s4_candidates")}}
    full, out = tbp.run(chain["world"], inputs)
    rec = json.loads(out[bp.RECORD])
    lists = chain["record"]["lists"]
    pool = [i["id"] for i in chain["record"]["s_pool_sealed"]["items"]]
    used = set(lists["s1"]["ids"]) | set(lists["s3_subset"]["ids"]) | set(lists["s4_candidates"]["ids"])
    assert rec["decoy"]["ids"] == s1.sealed_order(sorted(set(pool) - used), "plant.decoy_rows")[:37]
    assert len(rec["decoy"]["ids"]) == 37 and not set(rec["decoy"]["ids"]) & used
    assert chain["record"]["d1"]["rows_outside_the_lists_at_k"] >= 37
    decoy = json.loads(full["decoy.pool.json"])
    assert decoy["name"] == "decoy" and len(decoy["items"]) == 37
    path = chain["root"] / "decoy.pool.json"
    path.write_bytes(full["decoy.pool.json"])
    pins, _ = rp.load_pool_pins()
    doc = rp.read_pool(path, sha256_file(path))
    filled = copy.deepcopy(pins)
    filled["pools"]["decoy"]["sha256"] = doc["sha256"]
    assert rp.pin_of(doc, rp.check_pool_pins(filled)) == "pool pins"


# ----- REQ-9: make_untuned_answers.py ----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def answers(chain):
    """REQ-9's run() with the committed settings except its two recipe pins and the chunk (= the fixture recipe's batch
    size): list s3 = D-1's s3_safe pool (the committed s3 spec, size null), losses s1 and s3_safe = D-1's files."""
    return guarded("answers", lambda: make_answers(chain))


def make_answers(chain):
    rec = sfx.recipe(**{"generation.batch_size": 4})
    rec_path = chain["root"] / "rec.json"
    rec_path.write_text(json.dumps(rec))
    settings = copy.deepcopy(json.loads(mua.SETTINGS_PATH.read_bytes()))
    assert settings["lists"]["s3"]["size"] is None                              # the committed s3 spec
    settings["pins"]["rec_recipe_sha256"] = settings["pins"]["recipe_s_sha256"] = config_sha256(rec)
    settings["chunk"] = 4
    p = chain["pair"]
    files, code = mua.run(rec_path=rec_path, s_path=rec_path, lists={"s3": p[w1bsp.S3_POOL]},
                          losses={"s1": p["s1.json"], "s3_safe": p[w1bsp.S3_POOL]}, loaders=sfx.fixture_loaders(),
                          settings=settings, settings_sha256="e" * 64, generate=tmu.FakeGenerator(sfx.fixture_codec()))
    out = chain["root"] / "tmp" / "answers"
    out.mkdir(parents=True)
    for name, data in files.items():
        (out / name).write_bytes(data)
    return {"files": files, "code": code, "dir": out, "record": json.loads(files[mua.RECORD])}


def test_make_untuned_answers_accepts_the_k_row_s3_pool(chain, answers):
    """make_untuned_answers.py:77 checks a list's size only when the settings give one; the committed s3 spec gives
    null (settings/make_untuned_answers.json lists.s3.size), so k + |S1 outside the subset| items pass."""
    r = chain["record"]
    entry = answers["record"]["lists"]["s3"]
    assert answers["code"] == 0 and entry["list_sha256"] == r["s3_pool"]["sha256"]
    assert entry["items"] == entry["answered"] == r["s3_pool"]["items"] == r["d1"]["k"] + r["s3_pool"]["s1_rows_outside_the_subset"]
    loss = answers["record"]["loss"]                                          # :233 reads loss lists with no size
    assert set(loss) == {"s1", "s3_safe"}
    assert len(loss["s1"]["rows"]) + sum(loss["s1"]["refused_by_reason"].values()) == 3
    assert len(loss["s3_safe"]["rows"]) + sum(loss["s3_safe"]["refused_by_reason"].values()) == r["s3_pool"]["items"]


# ----- REQ-3: representation_pass.py and the pool pins -----------------------------------------------------------


def test_the_pool_pins_accept_s3_safe_on_the_command_line_and_the_37_row_decoy(chain):
    """representation_pass.py:186-205 (read_pool: kind, name, items; no size) and :238-257 (pin_of, :245-250): s3_safe is not
    listed in settings/representation_pools.json, so it is pinned by its SHA-256 on the command line whatever its size;
    the decoy entry's items (37) are unchanged by D-1."""
    pins, _ = rp.load_pool_pins()
    pool = rp.read_pool(*chain["pair"][w1bsp.S3_POOL])
    assert pool["name"] == "s3_safe" and len(pool["items"]) == chain["record"]["s3_pool"]["items"]
    assert rp.pin_of(pool, pins) == "command line"
    assert pins["pools"]["decoy"]["items"] == 37 and "s3_safe" not in pins["pools"]


@pytest.fixture(scope="module")
def req3(env, chain, answers):
    return guarded("req3", lambda: make_req3(env, chain, answers))


def make_req3(env, chain, answers):
    p = chain["pair"]
    orig = answers["dir"] / "s3_orig.pool.json"
    pools = [p[w1bsp.S3_POOL], (orig, sha256_file(orig))]
    files = rp.run(env.prepared, env.recipe, env.anchors, sfx.fixture_loaders(), env.settings, tmu_pin(), pools, False)
    out = chain["root"] / "req3"
    out.mkdir()
    for name, data in files.items():
        (out / name).write_bytes(data)
    return {name: (out / name, sha256_file(out / name)) for name in files}


def tmu_pin() -> str:
    """REQ-11's pin of REQ-3's settings, which REQ-3's summary must carry (score_s3_datarx.py:77-78)."""
    return json.loads(s3.SETTINGS_PATH.read_bytes())["pins"]["representation_pass_settings_sha256"]


def test_representation_pass_scores_the_k_row_s3_safe_pool(chain, req3):
    summary = json.loads(req3[rp.SUMMARY_FILE][0].read_bytes())
    names = {pl["name"]: pl for pl in summary["pools"]}
    assert names["s3_safe"]["sha256"] == chain["record"]["s3_pool"]["sha256"]
    lines = [json.loads(line) for line in req3[rp.ROWS_FILE][0].read_bytes().splitlines()]
    safe_ids = {line["id"] for line in lines if line["source"] == "s3_safe"}
    r = chain["record"]
    assert safe_ids == set(r["lists"]["s3_subset"]["ids"]) | set(r["lists"]["s1"]["ids"])


# ----- REQ-11: score_s3_datarx.py and write_score_add.py, by their real CLIs ---------------------------------------


@pytest.fixture(scope="module")
def scored(chain, answers, req3):
    return guarded("scored", lambda: make_scored(chain, answers, req3))


def make_scored(chain, answers, req3):
    rec_path = chain["pair"][w1bsp.RECORD]
    ans = answers["dir"] / mua.RECORD
    out = chain["root"] / "s3-scores"
    argv = ["--rows", f"{req3[rp.ROWS_FILE][0]}:{req3[rp.ROWS_FILE][1]}",
            "--summary", f"{req3[rp.SUMMARY_FILE][0]}:{req3[rp.SUMMARY_FILE][1]}",
            "--s-pool-record", f"{rec_path[0]}:{rec_path[1]}", "--answers-record", f"{ans}:{sha256_file(ans)}",
            "--out", str(out)]
    code = s3.main(argv)
    return {"code": code, "path": out / s3.OUTPUT}


def test_score_s3_datarx_cli_accepts_the_d1_record(chain, scored):
    """score_s3_datarx.py:79-80 check the record's kind ("stage1 s-pool record", kept by D-1), :84-90 its s3_pool
    SHA-256, :101-102 read the subset and S1 ids from the record: no size check."""
    assert scored["code"] == 0
    doc = json.loads(scored["path"].read_bytes())
    r = chain["record"]
    assert doc["candidate_pool_sha256"] == r["s3_pool"]["sha256"]
    assert set(doc["scores"]) <= set(r["lists"]["s3_subset"]["ids"])
    assert doc["reports"]["ranked"] + doc["reports"]["leaving_the_ranking"]["count"] == r["d1"]["k"]
    assert doc["reports"]["s1_and_s3_subset"] == r["overlaps_l10"]["s1_and_s3_subset"]


def test_write_score_add_cli_selects_48_from_the_k_row_subset(chain, scored, capsys):
    """write_score_add.py:59-73: the scores must name the candidate pool's SHA-256 (D-1's s3_safe pool) and select_top
    takes the committed k = 48 (it needs >= 48 ranked ids, which k >= k_min = 48 allows unless y^orig refusals remove
    some). Then REQ-7's list reader (write_add_edit.py:58-78) accepts the 48-row s3 list and D-1's s1.json."""
    pool = chain["pair"][w1bsp.S3_POOL]
    full = chain["root"] / "tmp" / "s3-pick"
    out = chain["root"] / "s3-pick-record"
    argv = ["--scorer", "s3", "--scores", f"{scored['path']}:{sha256_file(scored['path'])}",
            "--candidates", f"{pool[0]}:{pool[1]}", "--full-out", str(full), "--out", str(out)]
    assert wsa.main(argv) == 0, capsys.readouterr().err
    pick = full / "s3.json"
    listing = wae.read_list(pick, sha256_file(pick))
    assert listing["name"] == "s3" and len(listing["items"]) == 48
    assert {i["id"] for i in listing["items"]} <= set(chain["record"]["lists"]["s3_subset"]["ids"])
    s1_list = wae.read_list(*chain["pair"]["s1.json"])
    assert s1_list["name"] == "s1" and len(s1_list["items"]) == 3                 # the scaled S1 (48 when committed)


# ----- build_oext.py (the S-pool file) ----------------------------------------------------------------------------


def test_build_oext_accepts_the_d1_s_pool_file(chain, tmp_path):
    """build_oext.py:73-83 (read_prompts: kind "stage1 s-pool", SHA-256) and :179: the S-pool file does not depend on k
    (D-1 writes it with build_s_pool's own writer from the same rows)."""
    o = tbo.OWorld(tmp_path)
    data = tbo.phtest_bytes(o.rows)
    (tmp_path / "PHTest.csv").write_bytes(data)
    pl = tbo.text_file(tmp_path / "plant_rows.json", "stage1 plant rows", o.plant_prompts)
    full, out = bo.build(phtest_path=tmp_path / "PHTest.csv", prepared_root=o.world.prepared_root,
                         anchors_path=o.world.anchors_path, s_pool=chain["pair"][w1bsp.POOL_FILE], plant=pl,
                         rec_path=o.world.recipe_path, codec=o.world.sfx.fixture_codec(), settings=o.settings(data),
                         settings_sha256="e" * 64)
    record = json.loads(out[bo.RECORD])
    assert record["provenance"]["inputs"]["s_pool"] == chain["pair"][w1bsp.POOL_FILE][1]


# ----- commitments.py: the D-1 record and the D-1 package's files, as the freeze pass classifies them ---------------


def test_commitments_classifies_the_d1_record_and_files(chain):
    """commitments.py:169-195 (classify) and :198-202 (made_by): a sealed D-1 record is a text-free kind and names the
    wrapper as its maker; every D-1 package file gets a role and none is a text-bearing kind (C3, the later-files
    check at commitments.py:348-353)."""
    settings, _ = s1.load_settings(cm.SETTINGS_PATH, cm.SETTINGS_SHA256, cm.SETTINGS_NAME)
    data = chain["pair"][w1bsp.RECORD][0].read_bytes()
    role, doc = cm.classify(".ai/inputs/stage1-commitments-20261016/pool/s_pool_record.json", data, settings)
    assert role == "sealed record"
    assert cm.made_by(doc)["script"] == s1.rel(d1m.HERE / "d1_s_pool.py")      # scripts/stage1_s1/d1_spool/d1_s_pool.py
    assert cm.made_by(doc)["script"].endswith("scripts/stage1_s1/d1_spool/d1_s_pool.py")
    root = d1m.HERE
    files = [p for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    roles = {p.relative_to(root).as_posix(): cm.classify(f"scripts/stage1_s1/d1_spool/{p.relative_to(root).as_posix()}",
                                                          p.read_bytes(), settings)[0] for p in files}
    assert roles["d1_s_pool.py"] == "code" and roles["settings/d1_s_pool.json"] == "settings"
    for name in ("s_pool.json", "s1.json", "s3_subset.json", "s3_safe.pool.json"):
        with pytest.raises(s1.Refusal, match="text-bearing kind"):
            cm.classify(f"scripts/stage1_s1/d1_spool/{name}", chain["full"][name], settings)
