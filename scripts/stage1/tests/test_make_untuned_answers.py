"""REQ-9 and W1-06: the untuned answers job, on the engine's fixture loaders (a tiny model and the byte codec), with a
fake chunk generator for the keep rules; the loss on tiny OLMo-2 and Llama models with LoRA. CUDA is untested."""

from __future__ import annotations

import copy
import json
import random

import pytest

torch = pytest.importorskip("torch")

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from scripts.stage1 import make_untuned_answers as mua  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

import s1fixtures_b3b as fw  # noqa: E402
import test_representation_pass as trp  # noqa: E402  (its tiny model helpers)

sfx = trp.sfx
REFUSAL = "I'm sorry, but I cannot help with that request."
DIRECT = "Sure, rivers and tides move the delta."


def list_file(root, name, n, seed=1, kind="stage1 prompt list", response=True):
    rng = random.Random(seed)
    items = [{"id": f"pku_one:{k + 1:06d}:1", "prompt": fw.sentence(rng, 5),
              **({"response": fw.REFUSAL + fw.sentence(rng, 3)} if response else {})} for k in range(n)]
    doc = {"kind": kind, "version": 1, "name": name, "items": items}
    path = root / f"{name}.json"
    path.write_bytes(canonical_json(doc))
    return (path, sha256_bytes(path.read_bytes())), items


@pytest.fixture(scope="module")
def recipe_files(tmp_path_factory):
    root = tmp_path_factory.mktemp("recipes")
    rec = sfx.recipe(**{"generation.batch_size": 4})                       # chunk = REC's batch size (4 here)
    (root / "rec.json").write_text(json.dumps(rec))
    (root / "s.json").write_text(json.dumps(rec))
    return root / "rec.json", root / "s.json", rec


def settings_for(rec, chunk=4, s4_size=40, keep=6, s3_size=None, sd600_size=12) -> dict:
    s = copy.deepcopy(json.loads(mua.SETTINGS_PATH.read_bytes()))
    s["pins"]["rec_recipe_sha256"] = s["pins"]["recipe_s_sha256"] = config_sha256(rec)
    s["chunk"] = chunk
    s["lists"]["s4"].update(size=s4_size, keep=keep)
    s["lists"]["s3"]["size"] = s3_size
    s["lists"]["sd600"]["size"] = sd600_size
    return s


class FakeGenerator:
    """Answers that depend on the prompt AND on the call's prompt set (so a different chunking changes them)."""

    def __init__(self, codec, refuse_every=3, cap_every=None):
        self.codec, self.calls, self.refuse_every, self.cap_every = codec, [], refuse_every, cap_every

    def __call__(self, ids, max_new_tokens):
        self.calls.append([tuple(i) for i in ids])
        call_key = sum(len(i) for i in ids)
        out = []
        for i in ids:
            h = (sum(i) + call_key) % 97
            text = REFUSAL if h % self.refuse_every == 0 else DIRECT
            capped = self.cap_every is not None and h % self.cap_every == 1
            out.append(en.Generation(tuple(self.codec.encode(text)), en.STOP_CAP if capped else en.STOP_EOS,
                                     None if capped else self.codec.eos_id))
        return out


def run(recipe_files, settings, lists, losses=None, generate=None, loaders=None):
    rec_path, s_path, _ = recipe_files
    return mua.run(rec_path=rec_path, s_path=s_path, lists=lists, losses=losses or {}, loaders=loaders or sfx.fixture_loaders(),
                   settings=settings, settings_sha256="e" * 64, generate=generate)


def record(files):
    return json.loads(files[mua.RECORD])


# ----- S4: L11 and L14 ------------------------------------------------------------------------------------------


def test_s4_keeps_the_first_48_by_rule_and_stops_after_their_chunk(recipe_files, tmp_path):
    settings = settings_for(recipe_files[2])
    s4, items = list_file(tmp_path, "s4_candidates", 40)
    gen = FakeGenerator(sfx.fixture_codec())
    files, code = run(recipe_files, settings, {"s4": s4}, generate=gen)
    rec = record(files)["lists"]["s4"]
    assert code == 0 and rec["kept"] == 6
    kept_ids = [r["id"] for r in rec["rows"] if r["kept"]]
    assert [i["id"] for i in json.loads(files["s4.json"])["items"]] == kept_ids
    assert all(r["lex_class"] == "REFUSAL-OPENING" and r["ended"] for r in rec["rows"] if r["kept"])
    assert all(len(c) <= 4 for c in gen.calls)
    flat = [p for c in gen.calls for p in c]
    ids = mua.Answerer(None, sfx.fixture_codec(), None, 0, 400).prompt_ids(items, "s4")
    assert flat == [tuple(i) for i in ids[:len(flat)]]                      # list order, one chunk per call
    last = rec["chunks"][-1]
    assert sum(c["keeps"] for c in rec["chunks"][:-1]) < 6 <= sum(c["keeps"] for c in rec["chunks"])
    assert len(rec["rows"]) == last["start"] + last["prompts"] < 40          # stopped after the 6th keep's chunk


def test_the_early_stop_keeps_what_the_full_list_keeps(recipe_files, tmp_path):
    """L11: the kept set equals the full-list kept set at the stop point; a longer list keeps the same rows when the
    shorter suffices (the same chunks)."""
    s4, items = list_file(tmp_path, "s4_candidates", 40)
    stop = record(run(recipe_files, settings_for(recipe_files[2]), {"s4": s4}, generate=FakeGenerator(sfx.fixture_codec()))[0])
    full_settings = settings_for(recipe_files[2], keep=40)
    full = record(run(recipe_files, full_settings, {"s4": s4}, generate=FakeGenerator(sfx.fixture_codec()))[0])
    full_keeps = [r["id"] for r in full["lists"]["s4"]["rows"] if r["drop"] is None or r["kept"]]
    assert [r["id"] for r in stop["lists"]["s4"]["rows"] if r["kept"]] == full_keeps[:6]
    n_short = stop["lists"]["s4"]["answered"]                               # a shorter list that still suffices
    assert n_short < 40
    (tmp_path / "short").mkdir()
    short, _ = list_file(tmp_path / "short", "s4_candidates", n_short)
    shorter = record(run(recipe_files, settings_for(recipe_files[2], s4_size=n_short), {"s4": short},
                         generate=FakeGenerator(sfx.fixture_codec()))[0])
    assert [r["id"] for r in shorter["lists"]["s4"]["rows"] if r["kept"]] == \
        [r["id"] for r in stop["lists"]["s4"]["rows"] if r["kept"]]


def test_each_s4_drop_reason(recipe_files, tmp_path):
    codec = sfx.fixture_codec()

    class Scripted:
        texts = [REFUSAL, DIRECT, "   ", REFUSAL, REFUSAL + " " + fw.sentence(random.Random(2), 60), REFUSAL, REFUSAL, REFUSAL]
        position = 0

        def __call__(self, ids, max_new_tokens):
            out = []
            for _ in ids:
                k, self.position = self.position, self.position + 1
                out.append(en.Generation(tuple(codec.encode(self.texts[k])), en.STOP_CAP if k == 3 else en.STOP_EOS, None))
            return out
    s4, _ = list_file(tmp_path, "s4_candidates", 8)
    files, code = run(recipe_files, settings_for(recipe_files[2], s4_size=8, keep=4), {"s4": s4}, generate=Scripted())
    rec = record(files)["lists"]["s4"]
    assert code == 0 and [r["drop"] for r in rec["rows"]] == [None, "not_refusal_opening", "empty", "capped",
                                                             "encode_train_TooLong", None, None, None]
    assert rec["drops"] == {"capped": 1, "empty": 1, "encode_train_TooLong": 1, "not_refusal_opening": 1}


def test_fewer_than_48_keeps_gives_counts_only_and_exit_3(recipe_files, tmp_path):
    s4, _ = list_file(tmp_path, "s4_candidates", 40)
    files, code = run(recipe_files, settings_for(recipe_files[2], keep=30), {"s4": s4},
                      generate=FakeGenerator(sfx.fixture_codec(), refuse_every=5))
    assert code == mua.EXIT_FEW and "s4.json" not in files and record(files)["complete"] is False
    assert record(files)["lists"]["s4"]["answered"] == 40


# ----- S3 and SD-600 ----------------------------------------------------------------------------------------------


def test_s3_keeps_every_answer_and_flags_the_capped(recipe_files, tmp_path):
    s3, items = list_file(tmp_path, "s3_safe", 10, kind="stage1 text pool")
    codec = sfx.fixture_codec()

    class Gen:
        def __call__(self, ids, max_new_tokens):
            assert max_new_tokens == 512
            return [en.Generation(tuple(codec.encode("" if k == 1 else DIRECT)), en.STOP_CAP if k == 0 else en.STOP_EOS, None)
                    for k, _ in enumerate(ids)]
    files, code = run(recipe_files, settings_for(recipe_files[2], s3_size=10), {"s3": s3}, generate=Gen())
    rec = record(files)["lists"]["s3"]
    assert code == 0 and rec["answered"] == 10 and rec["capped"] == 3            # position 0 of each 4-chunk
    pool = json.loads(files["s3_orig.pool.json"])
    assert pool["name"] == "s3_orig" and all(i["id"].endswith(":orig") for i in pool["items"])
    assert rec["y_orig_leaves_the_sas_ranking"] == 3 and len(pool["items"]) == 7  # the empty answers do not encode


def test_sd600_keeps_every_answer_with_the_rec_cap(recipe_files, tmp_path):
    sd, _ = list_file(tmp_path, "sd600", 12, response=False)
    seen = []

    def gen(ids, max_new_tokens):
        seen.append(max_new_tokens)
        return FakeGenerator(sfx.fixture_codec())(ids, max_new_tokens)
    files, code = run(recipe_files, settings_for(recipe_files[2]), {"sd600": sd}, generate=gen)
    assert code == 0 and record(files)["lists"]["sd600"]["answered"] == 12
    assert set(seen) == {recipe_files[2]["generation"]["max_new_tokens"]}


# ----- the real untuned path ---------------------------------------------------------------------------------------


def test_the_untuned_model_answers_with_adapters_disabled(recipe_files, tmp_path):
    s4, _ = list_file(tmp_path, "s4_candidates", 8)
    settings = settings_for(recipe_files[2], s4_size=8, keep=2)
    flags = []
    real = torch.nn.Module.__call__

    def spy(self, *args, **kwargs):
        if kwargs.get("use_cache"):
            flags.append(all(m.disable_adapters for m in self.modules() if hasattr(m, "disable_adapters")))
        return real(self, *args, **kwargs)
    torch.nn.Module.__call__ = spy
    try:
        a = run(recipe_files, settings, {"s4": s4})
    finally:
        torch.nn.Module.__call__ = real
    assert flags and all(flags)
    b = run(recipe_files, settings, {"s4": s4})                                  # deterministic twice (times aside)
    assert a[1] == b[1] and a[0]["answers_s4.json"] == b[0]["answers_s4.json"]

    def timeless(files):
        doc = record(files)
        doc.pop("costs")
        for entry in doc["lists"].values():
            for c in entry["chunks"]:
                c.pop("seconds")
        return doc
    assert timeless(a[0]) == timeless(b[0])


def test_the_chunk_must_be_rec_batch_size_and_the_recipes_must_agree(recipe_files, tmp_path):
    s4, _ = list_file(tmp_path, "s4_candidates", 8)
    with pytest.raises(s1.Refusal, match="batch size"):
        run(recipe_files, settings_for(recipe_files[2], chunk=5, s4_size=8), {"s4": s4})
    rec_path, _, rec = recipe_files
    other = copy.deepcopy(rec)
    other["model"]["max_train_tokens"] = rec["model"]["max_train_tokens"] + 1
    (tmp_path / "s.json").write_text(json.dumps(other))
    settings = settings_for(rec)
    settings["pins"]["recipe_s_sha256"] = config_sha256(other)
    with pytest.raises(s1.Refusal, match="disagree on model.max_train_tokens"):
        mua.run(rec_path=rec_path, s_path=tmp_path / "s.json", lists={"s4": s4}, losses={}, loaders=sfx.fixture_loaders(),
                settings=settings, settings_sha256="e" * 64, generate=FakeGenerator(sfx.fixture_codec()))


def test_list_refusals(recipe_files, tmp_path):
    s4, _ = list_file(tmp_path, "s4_candidates", 40)
    settings = settings_for(recipe_files[2])
    with pytest.raises(s1.Refusal, match="hashes to"):
        run(recipe_files, settings, {"s4": (s4[0], "0" * 64)})
    with pytest.raises(s1.Refusal, match="holds 40 items, the settings say 41"):
        run(recipe_files, settings_for(recipe_files[2], s4_size=41), {"s4": s4})
    with pytest.raises(s1.Refusal, match="no list"):
        run(recipe_files, settings, {"s9": s4})


# ----- W1-06: the loss ---------------------------------------------------------------------------------------------


def test_the_loss_equals_the_engines_target_nll_mean(recipe_files, tmp_path):
    from experiments.safety_selection.textproc import encode_train

    s1_list, items = list_file(tmp_path, "s1", 5)
    s4, _ = list_file(tmp_path, "s4_candidates", 40, seed=4)
    files, code = run(recipe_files, settings_for(recipe_files[2]), {"s4": s4}, losses={"s1": s1_list},
                      generate=FakeGenerator(sfx.fixture_codec()))
    loss = record(files)["loss"]
    assert code == 0 and set(loss) == {"s1", "s4"} and len(loss["s4"]["rows"]) == 6
    codec, rec = sfx.fixture_codec(), recipe_files[2]
    model = sfx.tiny_lora_model()
    with torch.no_grad(), model.disable_adapter():
        model.eval()
        for item in items:
            ex = encode_train(codec, item["id"], item["prompt"], item["response"], rec["model"]["max_train_tokens"])
            expected = en._target_nll(model, [ex.input_ids], [ex.n_target], codec.pad_id, "cpu",
                                      rec["train"]["lm_head_chunk_tokens"])[0].mean()
            got = loss["s1"]["rows"][item["id"]]
            assert got["n_target"] == ex.n_target and got["mean_nll"] == pytest.approx(float(expected), rel=1e-5)
            assert got["perplexity"] == pytest.approx(float(torch.exp(expected)), rel=1e-5)


@pytest.mark.parametrize("family", ["olmo2", "llama"])
def test_the_loss_is_the_base_models_on_each_family(recipe_files, tmp_path, family):
    s1_list, _ = list_file(tmp_path, "s1", 4)
    s4, _ = list_file(tmp_path, "s4_candidates", 40, seed=4)
    settings = settings_for(recipe_files[2])
    zero = run(recipe_files, settings, {"s4": s4}, losses={"s1": s1_list}, generate=FakeGenerator(sfx.fixture_codec()),
               loaders=trp.loaders_with(lambda: trp.tiny(family, lora=True)))
    nonzero = run(recipe_files, settings, {"s4": s4}, losses={"s1": s1_list}, generate=FakeGenerator(sfx.fixture_codec()),
                  loaders=trp.loaders_with(lambda: trp.tiny(family, lora=True, b_nonzero=True)))
    assert record(zero[0])["loss"] == record(nonzero[0])["loss"]


def test_text_free_record_and_text_files(recipe_files, tmp_path):
    s1_list, s1_items = list_file(tmp_path, "s1", 5)
    s4, items = list_file(tmp_path, "s4_candidates", 40)
    files, _ = run(recipe_files, settings_for(recipe_files[2]), {"s4": s4}, losses={"s1": s1_list},
                   generate=FakeGenerator(sfx.fixture_codec()))
    data = files[mua.RECORD]
    for item in items + s1_items:
        assert item["prompt"].encode() not in data
    assert REFUSAL.encode() not in data and DIRECT.encode() not in data
    assert REFUSAL.encode() in files["answers_s4.json"]


def test_the_committed_settings():
    doc, digest = s1.load_settings(mua.SETTINGS_PATH, mua.SETTINGS_SHA256, mua.SETTINGS_NAME)
    assert doc["chunk"] == 32 and doc["lists"]["s4"]["size"] == 512 and doc["lists"]["s4"]["keep"] == 48
    assert doc["lists"]["s3"]["max_new_tokens"] == 512 and doc["lists"]["s4"]["max_new_tokens"] == "rec"
    assert doc["pins"]["rec_recipe_sha256"] == "9e9bde6f2f32876098410479883deff5ef3141e471a79ed231c7a5db15ad399b"
    assert doc["pins"]["recipe_s_sha256"] == "ceffe0efb5d75bacfbd62743f530259deeedeca8950605d1bd3ff66e5391fe46"
    assert doc["loss"]["lists"] == ["s1", "s3_safe"] and doc["transformers_version"] == "4.56.2"
