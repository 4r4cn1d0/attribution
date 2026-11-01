"""Lead decisions section 7: the O-ext bank from a synthetic PHTest file, a synthetic P with a hidden bank, a synthetic
S-pool and plant rows."""

from __future__ import annotations

import copy
import csv
import io
import json
import random

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from experiments.safety_selection.config import config_sha256
from scripts.stage1 import build_oext as bo
from scripts.stage1 import s1common as s1

import s1fixtures_b3b as fw

HEADER = ["ID", "Request", "Harmfulness"]


def phtest_bytes(rows: list[tuple[str, str, str]]) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def text_file(path, kind, prompts):
    path.write_bytes(canonical_json({"kind": kind, "version": 1, "items": [{"prompt": p} for p in prompts]}))
    return path, sha256_bytes(path.read_bytes())


class OWorld:
    def __init__(self, root, n_harmless=30, extra=(), bank_size=10, seed=1):
        rng = random.Random(seed)
        self.rng = rng
        self.world = fw.SWorld(root / "w", {"pku_one": [fw.refusal_record(rng)]})
        self.s_pool_prompts = [fw.sentence(rng) for _ in range(5)]
        self.plant_prompts = [fw.sentence(rng) for _ in range(5)]
        self.harmless = [(f"h{k:04d}", fw.sentence(rng), "harmless") for k in range(n_harmless)]
        self.rows = self.harmless + [(f"c{k:04d}", fw.sentence(rng), "controversial") for k in range(8)] + list(extra)
        self.root, self.bank_size = root, bank_size

    def build(self, settings=None, **kw):
        data = phtest_bytes(self.rows)
        (self.root / "PHTest.csv").write_bytes(data)
        s = settings or self.settings(data)
        sp = text_file(self.root / "s_pool.json", "stage1 s-pool", self.s_pool_prompts)
        pl = text_file(self.root / "plant_rows.json", "stage1 plant rows", self.plant_prompts)
        return bo.build(phtest_path=self.root / "PHTest.csv", prepared_root=self.world.prepared_root,
                        anchors_path=self.world.anchors_path, s_pool=sp, plant=pl, rec_path=self.world.recipe_path,
                        codec=self.world.sfx.fixture_codec(), settings=s, settings_sha256="e" * 64, **kw)

    def settings(self, data: bytes) -> dict:
        s = copy.deepcopy(json.loads(bo.SETTINGS_PATH.read_bytes()))
        s["phtest"]["sha256"] = sha256_bytes(data)
        s["phtest"]["candidates"] = sum(1 for r in self.rows if r[2] == "harmless")
        s["inputs"]["prepared_manifest_sha256"] = self.world.manifest_sha256
        s["inputs"]["anchor_prompts_sha256"] = sha256_bytes(self.world.anchors_path.read_bytes())
        s["inputs"]["rec_recipe_sha256"] = config_sha256(self.world.recipe)
        s["expected_evaluation_forms"] = self.world.forms()
        s["bank_size"] = self.bank_size
        return s


def rec(result):
    return json.loads(result[1][bo.RECORD])


def bank(result):
    return json.loads(result[0][bo.BANK])["items"]


def test_the_bank_is_the_first_eligible_ids_of_the_sealed_order(tmp_path):
    o = OWorld(tmp_path)
    res = o.build()
    ids = [r[0] for r in o.harmless]
    assert [i["id"] for i in bank(res)] == s1.sealed_order(ids, "oext.phtest")[:10]
    assert rec(res)["candidates"] == 30 and not any(i["id"].startswith("c") for i in bank(res))


def test_each_exclusion_is_counted_by_reason(tmp_path):
    """Addendum 7.2: every exclusion reason over every bank of P (dev, selector, hidden), P's training and evaluation
    forms, the anchors, the S-pool and the plant rows; a row meeting two reasons counts under both, removed once."""
    o = OWorld(tmp_path, n_harmless=25)
    train, query = fw.sentence(o.rng), fw.sentence(o.rng)
    w = fw.SWorld(tmp_path / "w2", {"pku_one": [fw.refusal_record(o.rng)]}, banks=o.world.banks, train_prompts=[train],
                  query_prompts=[query], seed=5)                              # seed 3 would repeat the bank prompts as anchors
    o.world, rng = w, o.rng
    o.plant_prompts[2] = o.s_pool_prompts[2]                                  # a prompt in both reference sets
    bad = [("x-exact-anchor", w.anchors[2].upper(), "harmless"),
           ("x-exact-spool", o.s_pool_prompts[0], "harmless"),
           ("x-exact-plant", o.plant_prompts[1], "harmless"),
           ("x-exact-spool-and-plant", o.s_pool_prompts[2].upper(), "harmless"),   # two reasons, removed once
           ("x-exact-dev", w.banks["dev"][0]["prompt"].upper(), "harmless"),       # an evaluation form of P
           ("x-exact-train", train.upper(), "harmless"),                           # a training prompt of P
           ("x-exact-query", query, "harmless"),                                   # a query prompt of P
           ("x-near-hidden", fw.swap_last_word(w.banks["hidden"][0]["prompt"], rng), "harmless"),
           ("x-near-dev", fw.swap_last_word(w.banks["dev"][0]["prompt"], rng), "harmless"),
           ("x-near-selector", fw.swap_last_word(w.banks["selector"][0]["prompt"], rng), "harmless"),
           ("x-near-anchor", fw.swap_last_word(w.anchors[9], rng), "harmless"),
           ("x-near-spool", fw.swap_last_word(o.s_pool_prompts[3], rng), "harmless"),
           ("x-near-plant", fw.swap_last_word(o.plant_prompts[4], rng), "harmless"),
           ("x-empty", "   ", "harmless"),
           ("x-long", fw.sentence(rng, 80), "harmless")]
    o.rows += bad
    res = o.build()
    f = rec(res)["filters"]
    assert f["exact_overlap"]["by_reason"] == {"overlap_with_a_plant_prompt": 2, "overlap_with_an_anchor_prompt": 1,
                                               "overlap_with_an_existing_or_evaluation_prompt": 3,
                                               "overlap_with_an_s_pool_prompt": 2}
    assert f["exact_overlap"]["removed"] == 7                                     # 8 reasons over 7 rows
    assert f["near_duplicate"]["by_reason"] == {"near_duplicate_of_a_plant_prompt": 1,
                                                "near_duplicate_of_an_anchor_prompt": 1,
                                                "near_duplicate_of_an_s_pool_prompt": 1,
                                                "near_duplicate_of_evaluation_prompt_dev": 1,
                                                "near_duplicate_of_evaluation_prompt_hidden": 1,
                                                "near_duplicate_of_evaluation_prompt_selector": 1}
    assert f["empty"]["by_reason"] == {"empty_prompt": 1}
    assert f["generation_prompt"]["by_reason"] == {"generation_prompt_TooLong": 1}
    assert rec(res)["n_after_each_filter"] == {"candidates": 40, "exact_overlap": 33, "near_duplicate": 27, "empty": 26,
                                               "generation_prompt": 25}
    assert rec(res)["eligible"] == 25
    assert not any(i["id"].startswith("x-") for i in bank(res))
    every = [r[0] for r in o.rows if r[2] == "harmless"]
    eligible = set(every) - {r[0] for r in bad}
    assert [i["id"] for i in bank(res)] == [i for i in s1.sealed_order(every, "oext.phtest") if i in eligible][:10]


def test_the_near_duplicate_threshold_is_at_or_above(tmp_path):
    """12 and 20 distinct letters: 8 shared 5-grams of 16, Jaccard exactly 0.5 (dropped); one more letter gives 8 of 17
    (kept)."""
    o = OWorld(tmp_path, n_harmless=20)
    o.world.banks["hidden"][0]["prompt"] = "ghijklmnopqr"
    o.world = fw.SWorld(tmp_path / "w2", {"pku_one": [fw.refusal_record(o.rng)]}, banks=o.world.banks)
    o.rows += [("x-at", "ghijklmnopqrstuvwxyz", "harmless"), ("x-below", "ghijklmnopqrstuvwxyzg", "harmless")]
    res = o.build()
    assert rec(res)["filters"]["near_duplicate"]["by_reason"] == {"near_duplicate_of_evaluation_prompt_hidden": 1}
    assert rec(res)["near_duplicate"]["largest_kept_jaccard"]["evaluation_prompt_hidden"] == 8 / 17


def test_a_duplicate_within_phtest_is_skipped_in_the_walk(tmp_path):
    o = OWorld(tmp_path, n_harmless=20, bank_size=19)
    o.rows.append(("h9999", o.harmless[3][1].upper(), "harmless"))
    res = o.build()
    assert rec(res)["duplicate_within_phtest_skipped"] == 1
    prompts = [i["prompt"].lower() for i in bank(res)]
    assert len(prompts) == len(set(prompts)) == 19
    # N' (the filter survivors) beside the bank size: the repeated prompt is eligible but skipped at the walk
    assert (rec(res)["candidates"], rec(res)["eligible"], rec(res)["bank_size"]) == (21, 21, 19)
    assert rec(res)["shortfall"] is None


def _generation_ids(prompt: str) -> int:
    """Generation-prompt ids of a prompt under the engine's fixture codec."""
    import sys

    from experiments.safety_selection.textproc import encode_generation_prompt

    if str(fw.ENGINE_TESTS) not in sys.path:
        sys.path.insert(0, str(fw.ENGINE_TESTS))
    import ss_fixtures

    return len(encode_generation_prompt(ss_fixtures.fixture_codec(), prompt, 10 ** 6))


def test_the_prompt_limit_is_max_prompt_tokens_exactly(tmp_path):
    """Section 7.2: the limit is REC's max_prompt_tokens (not max_train_tokens): a prompt of max_prompt_tokens + 1 ids
    is dropped, one of exactly max_prompt_tokens ids is kept."""
    o = OWorld(tmp_path)
    over = fw.sentence(o.rng, 13)
    at = over[:-1]
    limit = _generation_ids(over) - 1
    assert _generation_ids(at) == limit and max(_generation_ids(r[1]) for r in o.rows) < limit
    o.world = fw.SWorld(tmp_path / "w2", {"pku_one": [fw.refusal_record(o.rng)]}, banks=o.world.banks,
                        recipe_changes={"model.max_prompt_tokens": limit, "model.max_train_tokens": 1000})
    o.rows += [("x-over", over, "harmless"), ("x-at", at, "harmless")]
    res = o.build()
    assert rec(res)["filters"]["generation_prompt"]["by_reason"] == {"generation_prompt_TooLong": 1}
    harmless = [r[0] for r in o.rows if r[2] == "harmless"]
    eligible = [i for i in harmless if i != "x-over"]
    assert rec(res)["eligible"] == len(eligible) == 31 and rec(res)["candidates"] == 32
    assert [i["id"] for i in bank(res)] == [i for i in s1.sealed_order(harmless, "oext.phtest") if i in set(eligible)][:10]


def test_fewer_than_the_bank_size_stops(tmp_path):
    """Section 7.3: the stop carries the counts (candidates, N after each filter, removals by reason, the skipped
    duplicates), no id and no text."""
    o = OWorld(tmp_path, n_harmless=9)
    o.rows += [("x-exact-anchor", o.world.anchors[2], "harmless"), ("x-dup", o.harmless[0][1].upper(), "harmless")]
    with pytest.raises(s1.Refusal, match="only 9 eligible PHTest prompts, fewer than 10") as stop:
        o.build()
    message = str(stop.value)
    assert "candidates 11" in message and all(stage in message for stage in bo.STAGES)
    assert "'exact_overlap': 10" in message and "'generation_prompt': 10" in message
    assert "'overlap_with_an_anchor_prompt': 1" in message and "duplicate_within_phtest_skipped 1" in message
    assert "--accept-shortfall" in message and not any(r[1].encode() in message.encode() for r in o.rows)
    assert not any(t.encode() in message.encode() for t in o.world.texts())


def test_after_the_stop_the_shortfall_bank_is_every_eligible_prompt(tmp_path):
    """LN-24: run again with accept_shortfall, the bank is all N' eligible prompts in the sealed order, recorded."""
    o = OWorld(tmp_path, n_harmless=9)
    res = o.build(accept_shortfall=True)
    ids = [r[0] for r in o.harmless]
    assert [i["id"] for i in bank(res)] == s1.sealed_order(ids, "oext.phtest")
    assert rec(res)["bank_size"] == 9 and rec(res)["shortfall"]["eligible"] == 9 and rec(res)["shortfall"]["planned"] == 10
    full = OWorld(tmp_path / "full", n_harmless=30)
    assert rec(full.build(accept_shortfall=True))["shortfall"] is None        # no shortfall: the flag changes nothing


def test_no_eligible_prompt_refuses_even_with_the_shortfall_flag(tmp_path):
    o = OWorld(tmp_path, n_harmless=2)
    o.rows = [(r[0], o.world.anchors[k], "harmless") for k, r in enumerate(o.harmless)] + o.rows[2:]
    with pytest.raises(s1.Refusal, match="fallback F") as stop:
        o.build(accept_shortfall=True)
    assert "candidates 2" in str(stop.value) and "'overlap_with_an_anchor_prompt': 2" in str(stop.value)


def test_the_inputs_are_checked(tmp_path):
    o = OWorld(tmp_path)
    data = phtest_bytes(o.rows)
    s = o.settings(data)
    s["phtest"]["candidates"] = 31
    with pytest.raises(s1.Refusal, match="holds 30 harmless rows"):
        o.build(settings=s)
    s = o.settings(data)
    s["phtest"]["sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="refuses PHTest"):
        o.build(settings=s)
    s = o.settings(data)
    s["phtest"]["header"] = ["ID", "Prompt", "Harmfulness"]
    with pytest.raises(s1.Refusal, match="refuses PHTest"):
        o.build(settings=s)
    s = o.settings(data)
    s["expected_evaluation_forms"] += 1
    with pytest.raises(s1.Refusal, match="evaluation forms"):
        o.build(settings=s)


def test_text_free_record_and_deterministic(tmp_path):
    """The record holds no PHTest prompt and (L9 (4)'s third test) no bank item's id, prompt or ARC text of P, no
    anchor and no PKU text."""
    o = OWorld(tmp_path)
    a, b = o.build(), o.build()
    assert a == b
    for text in [r[1] for r in o.rows] + o.world.texts():
        assert text.encode() not in a[1][bo.RECORD]
    sealed = rec(a)["bank"]
    assert [i["id"] for i in sealed["items"]] == [i["id"] for i in bank(a)]
    assert all(set(i) == {"id", "prompt_sha256"} for i in sealed["items"])


# ----- main(): the flags and pins reach build, nothing is written on a refusal ------------------------------------


def _argv(tmp_path, full="full", out="out") -> list[str]:
    p, h = str(tmp_path / "absent"), "0" * 64
    return ["--phtest", p, "--prepared", p, "--anchors", p, "--rec", p, "--full-out", str(tmp_path / "tmp" / full),
            "--out", str(tmp_path / out), "--s-pool", f"{p}:{h}", "--plant", f"{p}:{h}"]


def _patch_main(monkeypatch, calls: list):
    from scripts.stage1 import build_s_pool as bsp

    record = canonical_json({"candidates": 0, "n_after_each_filter": {}, "bank_size": 0})
    monkeypatch.setattr(bsp, "real_codec", lambda *a, **k: "codec")
    monkeypatch.setattr(bo, "build", lambda **kw: calls.append(kw) or ({bo.BANK: b"{}"}, {bo.RECORD: record}))


@pytest.mark.parametrize("flag", [False, True])
def test_main_passes_the_shortfall_flag_only_when_given(tmp_path, monkeypatch, flag):
    """LN-24: --accept-shortfall reaches build as given; the PATH:SHA256 pairs and the pinned settings reach it too."""
    calls = []
    _patch_main(monkeypatch, calls)
    assert bo.main(_argv(tmp_path) + (["--accept-shortfall"] if flag else [])) == 0
    (kw,) = calls
    assert kw["accept_shortfall"] is flag and kw["codec"] == "codec"
    assert kw["s_pool"] == kw["plant"] == (tmp_path / "absent", "0" * 64)
    assert kw["settings_sha256"] == bo.SETTINGS_SHA256 and kw["settings"]["name"] == bo.SETTINGS_NAME
    assert (tmp_path / "tmp" / "full" / bo.BANK).exists() and (tmp_path / "out" / bo.RECORD).exists()


def test_main_refuses_changed_settings_bad_pairs_and_a_non_empty_out_folder(tmp_path, monkeypatch, capsys):
    calls = []
    _patch_main(monkeypatch, calls)
    changed = tmp_path / "build_oext.json"
    changed.write_bytes(bo.SETTINGS_PATH.read_bytes() + b"\n")
    assert bo.main(_argv(tmp_path) + ["--settings", str(changed)]) == 2 and not calls
    assert "settings build_oext hash to" in capsys.readouterr().err
    argv = _argv(tmp_path)
    argv[argv.index("--plant") + 1] = str(tmp_path / "absent")                   # no :SHA256
    assert bo.main(argv) == 2 and not calls and "PATH:SHA256" in capsys.readouterr().err
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "earlier.json").write_bytes(b"{}")
    assert bo.main(_argv(tmp_path)) == 2 and not calls                           # before build, before any write
    err = capsys.readouterr().err
    assert "exists and is not empty" in err and "(nothing written)" in err and str(tmp_path / "out") in err
    assert not (tmp_path / "tmp").exists()
    outside = _argv(tmp_path, out="o3")
    outside[outside.index("--full-out") + 1] = "/var/stage1-oext-full"       # no folder named tmp on the path
    assert bo.main(outside) == 2 and not calls and "named tmp" in capsys.readouterr().err
    # a write error after the bank went out is reported as what it left, never as 'nothing written'
    real = s1.write_new_files
    monkeypatch.setattr(s1, "write_new_files", lambda d, f: (_ for _ in ()).throw(OSError(28, "x")) if d.name == "o4"
                        else real(d, f))
    assert bo.main(_argv(tmp_path, full="f4", out="o4")) == 2 and len(calls) == 1
    err = capsys.readouterr().err
    assert "REFUSED: OSError (1 files left under the output folders)" in err and "nothing written" not in err


def test_the_committed_settings():
    doc, digest = s1.load_settings(bo.SETTINGS_PATH, bo.SETTINGS_SHA256, bo.SETTINGS_NAME)
    assert doc["phtest"]["sha256"] == "495d109ec2a3a7a568bd78704008c241d9e8f5094ee956a4dd88a7695ba6f0cf"
    assert (doc["phtest"]["candidates"], doc["phtest"]["candidate_label"], doc["bank_size"]) == (2077, "harmless", 400)
    assert "LN-24" in doc["shortfall_rule"] and "--accept-shortfall" in doc["shortfall_rule"]
    assert set(doc["label_entries"]) == {"oext.phtest"} and s1.label("oext.phtest").parts == ()
