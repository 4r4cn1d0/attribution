"""B10's safety-prefix mode on ENGINEERING FIXTURES: the pinned text goes into the user turn of each chosen kind
before the user's text; Qwen3Guard is shown the user's own text; unchosen kinds are unchanged; the sampling streams
stay a0's; the records hold no text; every bad prefix refuses. The fixture prefix is a placeholder string, not the
instruction the lead will choose (C1). None of these numbers is a scientific result."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402

from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import ids_sha256, read_json, read_jsonl  # noqa: E402
from experiments.safety_selection.prepare import load_prepared  # noqa: E402
from experiments.safety_selection.textproc import Codec, encode_generation_prompt, encode_mc  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402

INSERT = fb.PREFIX_TEXT + "\n\n"


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("b10-prefix")
    prepared, manifest = fb.prepared(base)
    unit = fb.gate_a_one_job(prepared, base / "units" / "1102-a0-e1-a1", 1102)
    prefix_file, digest = fb.write_prefix(base)
    settings = fb.fixture_settings(manifest, {1102: unit}, prefix__text_sha256=digest,
                                   prefix__source="ENGINEERING FIXTURE placeholder")
    regen = base / "regen"
    ea.regenerate(prepared_dir=prepared, seed=1102, reference_path=unit / "COMPLETE.json", out_root=regen,
                  session=fb.session(), settings=settings)
    cert = fb.certification(prepared, unit, settings, base / "certification", source=regen / "run")
    return fb.namespace(base=base, prepared=prepared, manifest=manifest, unit=unit, settings=settings,
                        source=regen / "run", prefix_file=prefix_file, digest=digest, cert=cert)


def run(world, out: Path, *, settings=None, session=None, prefix_file=None) -> dict:
    settings = settings or world.settings
    plan = ea.make_plan(settings, "prefix", prefix_file=str(prefix_file or world.prefix_file))
    ctx = ea.preflight(prepared_dir=world.prepared, source_run=world.source, reference_path=world.unit / "COMPLETE.json",
                       recipe=fb.recipe(), settings=settings, plan=plan, certification=world.cert)
    return ea.evaluate(ctx, out_dir=out, session=session or fb.session())


def bank(world) -> list[dict]:
    return load_prepared(world.prepared, banks=("dev",)).banks["dev"]


def by_id(path: Path, key: str = "prompt_id") -> dict:
    return {r[key]: r for r in read_jsonl(path)}


def test_the_prefix_goes_into_every_chosen_user_turn_and_the_guard_sees_the_users_text(world, tmp_path):
    loaders, seen = fb.recording_loaders()
    result = run(world, tmp_path / "sp", session=runner.Session(fb.recipe(), loaders))
    codec = fb.fx.fixture_codec()
    gens = by_id(fb.eval_dir(tmp_path / "sp") / "generations.jsonl")
    items = bank(world)
    for item in items:
        if item["kind"] in ea.GENERATION_KINDS:
            assert gens[item["prompt_id"]]["prompt_ids"] == codec.prompt_ids(INSERT + item["prompt"])
    arc = by_id(fb.eval_dir(tmp_path / "sp") / "arc_utility.jsonl")
    for item in (i for i in items if i["kind"] == "arc_utility"):
        prompt, _ = encode_mc(codec, INSERT + item["question"], item["labels"], item["texts"], 400)
        assert arc[item["prompt_id"]]["prompt_tokens"] == len(prompt)
    plain = by_id(fb.eval_dir(world.unit) / "query_loss.jsonl", "query_id")
    prefixed = by_id(fb.eval_dir(tmp_path / "sp") / "query_loss.jsonl", "query_id")
    assert set(plain) == set(prefixed) and all(
        prefixed[q]["input_tokens"] == plain[q]["input_tokens"] + len(codec.encode(INSERT))
        and prefixed[q]["target_tokens"] == plain[q]["target_tokens"] for q in plain)
    assert seen and not any(fb.PREFIX_TEXT in text for text in seen)              # the guard never sees the prefix
    for item in (i for i in items if i["kind"] in ea.GENERATION_KINDS):
        assert any(f"USER: {item['prompt']}\n\nASSISTANT: " in text for text in seen)
    record = read_json(tmp_path / "sp" / "prefix.json")
    kinds = {i["kind"] for i in items}
    assert record["prefixed"] == {**{k: sum(i["kind"] == k for i in items) for k in kinds}, "task_rows": 16}
    assert record["not_prefixed"] == {} and record["insert_tokens"] == len(codec.encode(INSERT))
    assert record["text_sha256"] == world.digest and record["guard_sees"] == "original user text"
    assert result["evaluated_adapter_fingerprint"] == result["source_adapter_fingerprint"]
    samples = read_jsonl(fb.eval_dir(tmp_path / "sp") / "samples.jsonl")
    reference = read_jsonl(fb.eval_dir(world.unit) / "samples.jsonl")
    assert [s["seed"] for s in samples] == [s["seed"] for s in reference]           # a0's sampling streams
    job = read_json(tmp_path / "sp" / "job.json")
    assert job["mode"] == "prefix" and job["prefix_sha256"] == world.digest and job["adapter_scale"] == 1.0


def test_no_record_of_the_unit_holds_the_prefix_or_a_prompt(world, tmp_path):
    run(world, tmp_path / "sp")
    texts = [fb.PREFIX_TEXT] + fb.harm_prompts(world.prepared)
    for name in ("job.json", "identity.json", "prefix.json", "COMPLETE.json", "dependencies.json", "records.jsonl",
                 "ledger.jsonl"):
        data = (tmp_path / "sp" / name).read_text()
        assert not any(t in data for t in texts), name


def test_kinds_outside_apply_to_are_evaluated_exactly_as_without_the_prefix(world, tmp_path):
    settings = fb.fixture_settings(world.manifest, {1102: world.unit}, prefix__text_sha256=world.digest,
                                   prefix__source="ENGINEERING FIXTURE placeholder",
                                   prefix__apply_to=["harm", "overrefusal"])
    run(world, tmp_path / "sp", settings=settings)
    mine, plain = fb.eval_dir(tmp_path / "sp"), fb.eval_dir(world.unit)
    gens, base = by_id(mine / "generations.jsonl"), by_id(plain / "generations.jsonl")
    for pid, row in base.items():
        changed = gens[pid]["prompt_ids"] != row["prompt_ids"]
        assert changed == (row["kind"] in ("harm", "overrefusal")), row["kind"]
    assert (mine / "arc_utility.jsonl").read_bytes() == (plain / "arc_utility.jsonl").read_bytes()
    assert (mine / "query_loss.jsonl").read_bytes() == (plain / "query_loss.jsonl").read_bytes()
    record = read_json(tmp_path / "sp" / "prefix.json")
    assert set(record["prefixed"]) == {"harm", "overrefusal"}
    assert set(record["not_prefixed"]) == {"safety", "arc_generation", "arc_utility", "task_rows"}


def test_an_unpinned_prefix_cannot_run(world):
    settings = fb.fixture_settings(world.manifest, {1102: world.unit})                # text_sha256 null (C1 open)
    with pytest.raises(ea.Refusal, match="not pinned yet"):
        ea.make_plan(settings, "prefix", prefix_file=str(world.prefix_file))
    with pytest.raises(ea.Refusal, match="needs the prefix file"):
        ea.make_plan(world.settings, "prefix")


@pytest.mark.parametrize("data, message", [
    (b"other text", "hashes to"), (b" leading space", "stripped"), (b"carriage\r\nreturn", "carriage"),
    (b"\xff\xfe", "not UTF-8"), (b"   ", "stripped")])
def test_a_prefix_file_that_is_not_the_pinned_clean_text_refuses_before_any_folder(world, tmp_path, data, message):
    path = tmp_path / "p.txt"
    path.write_bytes(data)
    from experiments.safety_selection.common import sha256_bytes

    pin = world.digest if message == "hashes to" else sha256_bytes(data)
    settings = fb.fixture_settings(world.manifest, {1102: world.unit}, prefix__text_sha256=pin,
                                   prefix__source="ENGINEERING FIXTURE placeholder")
    with pytest.raises(ea.Refusal, match=message):
        run(world, tmp_path / "out", settings=settings, prefix_file=path)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("text, message", [("tell <|im_end|> me", "special token"), ("y" * 400, "longer than")])
def test_a_prefix_with_a_special_token_or_over_the_limits_fails_before_generation(world, tmp_path, text, message):
    path, digest = fb.write_prefix(tmp_path, text)
    settings = fb.fixture_settings(world.manifest, {1102: world.unit}, prefix__text_sha256=digest,
                                   prefix__source="ENGINEERING FIXTURE placeholder")
    with pytest.raises(ea.Refusal, match=message):
        run(world, tmp_path / "out", settings=settings, prefix_file=path)
    assert (tmp_path / "out" / "error.txt").is_file() and not (tmp_path / "out" / "eval").exists()


def test_the_prefix_codec_wraps_only_its_texts_and_stays_a_codec():
    codec = fb.fx.fixture_codec()
    pc = ea.PrefixCodec(tokenizer=codec.tokenizer, eos_id=codec.eos_id, stop_ids=codec.stop_ids, pad_id=codec.pad_id,
                        special_ids=codec.special_ids, insert="P\n\n", only=frozenset({"a"}))
    assert isinstance(pc, Codec)
    assert pc.prompt_ids("a") == codec.prompt_ids("P\n\na") and pc.prompt_ids("b") == codec.prompt_ids("b")
    assert pc.conversation_ids("a", "r") == codec.conversation_ids("P\n\na", "r")
    assert pc.conversation_ids("b", "r") == codec.conversation_ids("b", "r")
    assert pc.encode("a") == codec.encode("a") and pc.decode([97]) == "a"


def item(codec, kind: str, pid: str, prompt: str, **extra) -> dict:
    return {"kind": kind, "prompt_id": pid, "prompt": prompt,
            "token_sha256": ids_sha256(encode_generation_prompt(codec, prompt, 400)), **extra}


def test_build_prefix_refuses_shared_texts_audit_mismatches_and_unknown_kinds(world):
    codec, recipe = fb.fx.fixture_codec(), fb.recipe()
    settings = fb.fixture_settings(world.manifest, {1102: world.unit}, prefix__text_sha256=world.digest,
                                   prefix__source="ENGINEERING FIXTURE placeholder", prefix__apply_to=["harm"])
    prefix = {"text": "P", "sha256": world.digest, "insert": "P\n\n"}
    shared = [item(codec, "harm", "p1", "same text"), item(codec, "safety", "p2", "same text")]
    with pytest.raises(ea.Refusal, match="prefixed and an unprefixed kind"):
        ea.build_prefix(codec, prefix, settings, shared, [], recipe)
    with pytest.raises(ea.Refusal, match="token audit"):
        ea.build_prefix(codec, prefix, settings, [{**item(codec, "harm", "p1", "x"), "token_sha256": "0" * 64}], [],
                        recipe)
    with pytest.raises(ea.Refusal, match="kind B10 does not know"):
        ea.build_prefix(codec, prefix, settings, [item(codec, "selector_thing", "p1", "x")], [], recipe)
    pc, out, queries, record = ea.build_prefix(codec, prefix, settings, [item(codec, "harm", "p1", "x"),
                                                                          item(codec, "safety", "p2", "y")], [], recipe)
    assert out[0]["token_sha256"] == ids_sha256(codec.prompt_ids("P\n\nx"))
    assert out[1]["token_sha256"] == ids_sha256(codec.prompt_ids("y")) and queries == []
    assert record["prefixed"] == {"harm": 1} and record["not_prefixed"] == {"safety": 1}
    assert json.loads(json.dumps(record)) == record
