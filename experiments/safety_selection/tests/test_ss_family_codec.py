"""Multi-family probes (brief multi-family-probe-engine-20261007), Items 1.0-1.4 and 2, on SYNTHETIC FIXTURES:
the golden task record written before any edit; the unk rule, the added special ids, the clock-template refusal, the
decode contract and the assistant-header check; and the per-tokenizer preparation (``exclude_lines``,
``construction_sha256``, the dev-only ``retokenize``). No real tokenizer, bank text or Dolly row is read here."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import ss_fixtures as fx

from experiments.safety_selection import prepare as pp
from experiments.safety_selection import prepare_task as pt
from experiments.safety_selection.common import sha256_bytes
from experiments.safety_selection.config import ConfigError, load_recipe, validate_recipe, validate_task_data_config
from experiments.safety_selection.sources import DataError
from experiments.safety_selection.textproc import (QWEN_ASSISTANT_HEADER, TemplateError, build_codec,
                                                   check_assistant_header, single_token_id)

TESTS = Path(__file__).resolve().parent
PACKAGE = TESTS.parent
ROOT = PACKAGE.parents[1]
GOLDEN = TESTS / "golden" / "kt-task-46064a7.json"


def jsonl(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.decode("utf-8").split("\n") if line]


# ----- 1.0 the golden task record ---------------------------------------------------------------------------


def test_the_kill_test_task_path_equals_its_golden_record_written_before_any_edit(tmp_path):
    import kt_task_digest as kd

    golden = json.loads(GOLDEN.read_text())
    assert golden["written_with"]["engine_code_sha256"] == \
        "c52c0ebc83793fc552f84908e83542d5e46543459fcafb7be2fc9c7ff42ac597"     # the engine before this build
    now = kd.golden_record(tmp_path)
    assert now["prepared_task_files"] == golden["prepared_task_files"] and len(now["prepared_task_files"]) == 10
    for unit, digest in golden["units"].items():
        assert now["units"][unit] == digest, unit


# ----- 1.1-1.4 the codec -----------------------------------------------------------------------------------


class OlmoLikeTokenizer:
    """OLMo-2-like: one id for end, begin and unknown (256), a distinct pad (257), added special tokens outside
    ``all_special_ids`` (258, 259) and plain-text role markers in a template without a system turn."""

    SPECIAL = {"<|endoftext|>": 256, "<|pad|>": 257, "<|im_start|>": 258, "<|fim_prefix|>": 259}
    unk_token, unk_token_id = "<|endoftext|>", 256
    chat_template = "{{ eos_token }}<|user|>... (fixture)"

    def __init__(self) -> None:
        self.all_special_ids = [256, 257]
        self.added_tokens_decoder = {i: SimpleNamespace(content=t, special=True) for t, i in self.SPECIAL.items()}
        self.added_tokens_decoder[260] = SimpleNamespace(content="|||PHONE_NUMBER|||", special=False)

    def convert_tokens_to_ids(self, token):
        return self.SPECIAL.get(token, self.unk_token_id)

    def encode(self, text, add_special_tokens=False):
        ids, i = [], 0
        while i < len(text):
            special = next((t for t in self.SPECIAL if text.startswith(t, i)), None)
            if special:
                ids.append(self.SPECIAL[special])
                i += len(special)
            else:
                ids.extend(text[i].encode("utf-8"))
                i += 1
        return ids

    def decode(self, ids, skip_special_tokens=False, clean_up_tokenization_spaces=False):
        names = {v: k for k, v in self.SPECIAL.items()}
        return "".join(names[i] if i in names else bytes([i]).decode("latin-1") for i in ids)

    def apply_chat_template(self, messages, tokenize=True, add_generation_prompt=False, **kwargs):
        text = "<|endoftext|>" + "".join(f"<|{m['role']}|>\n{m['content']}\n" for m in messages)
        text += "<|assistant|>\n" if add_generation_prompt else ""
        return self.encode(text) if tokenize else text


def test_an_olmo_like_tokenizer_builds_a_codec_and_an_unknown_token_still_refuses():
    tok = OlmoLikeTokenizer()
    codec = build_codec(tok, "<|endoftext|>", ["<|endoftext|>"], "<|pad|>")
    assert (codec.eos_id, codec.stop_ids, codec.pad_id) == (256, (256,), 257)
    assert codec.special_ids == {256, 257, 258, 259}                       # added special ones, not the plain 260
    assert single_token_id(tok, "<|endoftext|>") == 256                    # the unk token itself is allowed
    with pytest.raises(TemplateError):
        single_token_id(tok, "<|bogus|>")                                  # maps to unk, but is not unk
    assert check_assistant_header(codec, "<|assistant|>\n").endswith("<|assistant|>\n")


def test_special_ids_grow_only_by_added_special_tokens_and_the_qwen_like_set_is_unchanged():
    qwen = build_codec(fx.FixtureTokenizer(), "<|im_end|>", ["<|im_end|>", "<|endoftext|>"], "<|endoftext|>")
    assert qwen.special_ids == {256, 257, 258}                             # fixture entries carry no .special
    tok = fx.FixtureTokenizer()
    tok.added_tokens_decoder = {i: SimpleNamespace(content=t, special=True) for t, i in fx.SPECIAL.items()}
    assert build_codec(tok, "<|im_end|>", ["<|im_end|>"], "<|endoftext|>").special_ids == {256, 257, 258}


def test_a_clock_reading_template_refuses_and_the_same_with_a_fixed_date_builds():
    for template in ("{{ strftime_now('%d %b %Y') }} text", {"default": "x", "tool_use": "{{ strftime_now('%Y') }}"}):
        tok = fx.FixtureTokenizer()
        tok.chat_template = template
        with pytest.raises(TemplateError, match="date-dependent"):
            build_codec(tok, "<|im_end|>", ["<|im_end|>"], "<|endoftext|>")
    tok = fx.FixtureTokenizer()
    tok.chat_template = "Today Date: 26 Jul 2024 {{ messages }}"
    build_codec(tok, "<|im_end|>", ["<|im_end|>"], "<|endoftext|>")


def test_decode_never_cleans_up_tokenization_spaces():
    calls = []

    class Recording(fx.FixtureTokenizer):
        def decode(self, ids, **kwargs):
            calls.append(kwargs)
            return super().decode(ids, **kwargs)

    codec = build_codec(Recording(), "<|im_end|>", ["<|im_end|>"], "<|endoftext|>")
    codec.decode([104, 105])
    assert calls == [{"skip_special_tokens": False, "clean_up_tokenization_spaces": False}]


def test_the_assistant_header_check():
    codec = build_codec(fx.FixtureTokenizer(), "<|im_end|>", ["<|im_end|>"], "<|endoftext|>")
    assert "<<probe>>" in check_assistant_header(codec, QWEN_ASSISTANT_HEADER)      # the field absent: Qwen's
    with pytest.raises(TemplateError, match="does not end"):
        check_assistant_header(codec, "<|assistant|>\n")

    class HeaderAlways(fx.FixtureTokenizer):                    # ends with the header, but not as the generation suffix
        def _render(self, messages, add_generation_prompt):
            return super()._render(messages, False) + "<|im_start|>assistant\n"

    always = build_codec(HeaderAlways(), "<|im_end|>", ["<|im_end|>"], "<|endoftext|>")
    with pytest.raises(TemplateError, match="generation suffix"):
        check_assistant_header(always, QWEN_ASSISTANT_HEADER)


def test_the_recipe_accepts_the_header_field_and_every_existing_recipe_still_validates():
    recipe = fx.recipe(**{"model.assistant_header": "<|assistant|>\n"})
    validate_recipe(recipe)
    with pytest.raises(ConfigError):
        validate_recipe(fx.recipe(**{"model.assistant_header": ""}))
    family_recipes = 0
    for path in sorted((PACKAGE / "configs").glob("*.json")):
        data = json.loads(path.read_text())
        if data.get("kind") == "safety-selection recipe":
            family = path.name.startswith(("study-kt-olmo2-", "study-kt-llama3"))   # by family prefix (round 4)
            family_recipes += family
            assert ("assistant_header" in data["model"]) is family                 # only the family recipes
            assert ("guard_over_limit" in data["generation"]) is family            # no Qwen recipe (review fix 1)
            load_recipe(path)
    gate_b_s = PACKAGE / "configs" / "study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json"   # Gate B recipe S, once it exists
    assert family_recipes == 54 + gate_b_s.exists()   # 26 b, 12 bt, 12 g (round 5), Hawkins-like, 2 g at 5e-5, Llama b at 5e-5 (9 Oct), S


# ----- 2. per-tokenizer preparation -------------------------------------------------------------------------

LONG_ROWS = [{"instruction": "a repeating answer", "context": "", "response": "e " * 140, "category": "open_qa"},
             {"instruction": "another repeating answer", "context": "", "response": "e " * 141, "category": "closed_qa"}]


def records() -> list[dict]:
    return fx.dolly_records() + LONG_ROWS


def long_lines() -> list[int]:
    return [len(fx.dolly_records()) + 1, len(fx.dolly_records()) + 2]


@pytest.fixture(scope="module")
def bank_dir(tmp_path_factory):
    folder, _ = fx.prepare_dir_v3(tmp_path_factory.mktemp("family") / "prepared-v3")
    return folder


def prepare(bank_dir: Path, tokenizer, **changes) -> dict[str, bytes]:
    dolly = fx.dolly_bytes(records())
    manifest, banks = fx.task_bank_inputs(bank_dir)
    return pt.prepare_task(fx.task_config(dolly, bank_dir, **changes), dolly, manifest, banks, tokenizer,
                           fx.TOKENIZER_IDENTITY)


@pytest.fixture(scope="module")
def qwen_like(bank_dir):
    return prepare(bank_dir, fx.FixtureTokenizer())


def other_options(qwen_like: dict, **more) -> dict:
    return {"eligibility.exclude_lines": long_lines(), "banks_from.retokenize": ["banks/dev.jsonl"],
            "eligibility.expected.construction_sha256": sha256_bytes(qwen_like[pp.AUDITOR]), **more}


def test_another_tokenizer_with_exclude_lines_and_dev_retokenize_keeps_every_row_and_unit(bank_dir, qwen_like):
    other = prepare(bank_dir, fx.FixtureTokenizer(merge="e "), **other_options(qwen_like))
    assert other[pp.GROUPS] == qwen_like[pp.GROUPS] and other[pp.AUDITOR] == qwen_like[pp.AUDITOR]
    for name, key in ((pp.TRAIN_ROWS, "row_id"), (pp.QUERY_ROWS, "query_id")):
        a, b = jsonl(qwen_like[name]), jsonl(other[name])
        assert [(r[key], r["prompt"], r["response"]) for r in a] == [(r[key], r["prompt"], r["response"]) for r in b]
    dev_a, dev_b = jsonl(qwen_like[pp.BANK_FILES["dev"]]), jsonl(other[pp.BANK_FILES["dev"]])
    assert [i["prompt_id"] for i in dev_a] == [i["prompt_id"] for i in dev_b]
    changed = 0
    for a, b in zip(dev_a, dev_b):
        assert {k: v for k, v in a.items() if k not in pt.TOKEN_FIELDS} == {k: v for k, v in b.items() if k not in pt.TOKEN_FIELDS}
        changed += a["token_sha256"] != b["token_sha256"]
    assert changed > 0                                                     # the merge really changes encodings
    for name in (pp.BANK_FILES["selector"], pp.BANK_FILES["hidden"]):
        assert other[name] == (bank_dir / name).read_bytes()               # copied byte for byte, not re-audited
    manifest = json.loads(other[pp.MANIFEST])
    imp = manifest["bank_import"]
    assert imp["retokenized"] == ["banks/dev.jsonl"] and imp["not_audited"] == ["banks/selector.jsonl", "hidden/hidden.jsonl"]
    assert imp["token_hash_changed_items"] == changed and imp["rule"] == pt.BANK_RETOKENIZE_RULE
    assert imp["new_files"] == {"banks/dev.jsonl": sha256_bytes(other[pp.BANK_FILES["dev"]])} and "reaudited_items" not in imp
    assert manifest["excluded_lines"] == long_lines() and manifest["exclusion_rule"] == pt.TASK_EXCLUSION_RULE
    by_category = manifest["eligibility"]["by_category"]
    assert by_category["open_qa"]["excluded_by_reason"]["excluded_line"] == 1
    assert by_category["closed_qa"]["excluded_by_reason"]["excluded_line"] == 1
    assert manifest["task_rule"] == pt.TASK_RULE


def test_without_the_new_options_nothing_new_appears_and_the_other_tokenizer_still_refuses(bank_dir, qwen_like):
    manifest = json.loads(qwen_like[pp.MANIFEST])
    assert not {"exclusion_rule", "excluded_lines"} & set(manifest)
    assert not {"retokenized", "not_audited", "rule", "new_files"} & set(manifest["bank_import"])
    assert "excluded_line" not in json.dumps(manifest["eligibility"])
    with pytest.raises(DataError, match="re-audit"):
        prepare(bank_dir, fx.FixtureTokenizer(merge="e "), **{"eligibility.exclude_lines": long_lines()})
    # without exclude_lines the other tokenizer makes the two long rows eligible: the rows would differ
    loose = prepare(bank_dir, fx.FixtureTokenizer(merge="e "), **{"banks_from.retokenize": ["banks/dev.jsonl"]})
    assert loose[pp.AUDITOR] != qwen_like[pp.AUDITOR]


def test_the_construction_hash_and_the_listed_lines_refuse_any_difference(bank_dir, qwen_like):
    with pytest.raises(DataError, match="construction"):
        prepare(bank_dir, fx.FixtureTokenizer(merge="e "),
                **other_options(qwen_like, **{"eligibility.expected.construction_sha256": "0" * 64}))
    with pytest.raises(DataError, match="already removed"):                 # the duplicate row: removed earlier
        prepare(bank_dir, fx.FixtureTokenizer(merge="e "), **other_options(
            qwen_like, **{"eligibility.exclude_lines": sorted(long_lines() + [len(fx.dolly_records()) - 7])}))
    with pytest.raises(DataError, match="not in the source"):
        prepare(bank_dir, fx.FixtureTokenizer(merge="e "),
                **other_options(qwen_like, **{"eligibility.exclude_lines": long_lines() + [99999]}))
    for bad in ({"eligibility.exclude_lines": [3, 2]}, {"eligibility.exclude_lines": [0]}, {"eligibility.exclude_lines": []},
                {"banks_from.retokenize": ["banks/other.jsonl"]}, {"eligibility.expected.construction_sha256": "x"}):
        with pytest.raises(ConfigError):
            validate_task_data_config(fx.task_config(fx.dolly_bytes(records()), bank_dir, **bad))


def test_the_retokenizer_refuses_a_changed_field_a_lossy_round_trip_and_encode_failures(bank_dir, monkeypatch):
    manifest, banks = fx.task_bank_inputs(bank_dir)
    codec = build_codec(fx.FixtureTokenizer(merge="e "), "<|im_end|>", ["<|im_end|>"], "<|im_end|>")
    with pytest.raises(DataError, match="round-trip"):
        pt._retokenize(codec, 400, {**banks, "banks/dev.jsonl": banks["banks/dev.jsonl"].replace(b'":', b'": ', 1)},
                       ["banks/dev.jsonl"], [])
    with pytest.raises(DataError) as caught:
        pt._retokenize(codec, 3, banks, ["banks/dev.jsonl"], [])            # every prompt over a 3-token limit
    message = str(caught.value)
    assert "dev/harm" in message and not any(i["prompt"] in message for i in jsonl(banks["banks/dev.jsonl"]))
    monkeypatch.setattr(pt, "_token_fields", lambda codec_, item, max_prompt: {"prompt": "changed", "prompt_tokens": 1})
    with pytest.raises(DataError, match="token fields"):
        pt._retokenize(codec, 400, banks, ["banks/dev.jsonl"], [])


def test_the_bank_scan_counts_forbidden_substrings_and_records_dev_ids_only(bank_dir):
    _, banks = fx.task_bank_inputs(bank_dir)
    codec = build_codec(fx.FixtureTokenizer(merge="e "), "<|im_end|>", ["<|im_end|>"], "<|im_end|>")
    dev = jsonl(banks["banks/dev.jsonl"])
    needle = dev[0]["prompt"][:4]
    _, receipt = pt._retokenize(codec, 400, banks, ["banks/dev.jsonl"], [needle])
    assert sum(receipt["forbidden_substring_items"].values()) >= 1
    assert dev[0]["prompt_id"] in receipt["forbidden_substring_dev_prompt_ids"]
    assert not any(i["prompt"] in json.dumps(receipt) for i in dev)
    _, clean = pt._retokenize(codec, 400, banks, ["banks/dev.jsonl"], ["\x00never\x00"])
    assert clean["forbidden_substring_items"] == {} and "forbidden_substring_dev_prompt_ids" not in clean


def test_a_job_on_the_not_audited_selector_bank_refuses_at_its_token_check(bank_dir, qwen_like):
    from experiments.safety_selection import runner

    other = prepare(bank_dir, fx.FixtureTokenizer(merge="e "), **other_options(qwen_like))
    codec = build_codec(fx.FixtureTokenizer(merge="e "), "<|im_end|>", ["<|im_end|>", "<|endoftext|>"], "<|endoftext|>")
    selector = [i for i in jsonl(other[pp.BANK_FILES["selector"]]) if i["kind"] != "arc_utility"]
    differs = [i for i in selector if "e " in i["prompt"]]
    assert differs
    with pytest.raises(DataError, match="encodes differently"):
        runner._prompt_ids(codec, differs[0], 400)
    dev = [i for i in jsonl(other[pp.BANK_FILES["dev"]]) if i["kind"] != "arc_utility"]
    for item in dev:                                                       # the retokenized dev bank passes
        runner._prompt_ids(codec, item, 400)


def test_the_other_tokenizer_preparation_is_deterministic_also_under_another_hash_seed(bank_dir, qwen_like):
    first = prepare(bank_dir, fx.FixtureTokenizer(merge="e "), **other_options(qwen_like))
    assert prepare(bank_dir, fx.FixtureTokenizer(merge="e "), **other_options(qwen_like)) == first
    script = ("import sys; sys.path[:0] = ['.', 'experiments/safety_selection/tests']\n"
              "import ss_fixtures as fx, test_ss_family_codec as t\nfrom pathlib import Path\n"
              f"bank = Path({str(bank_dir)!r}); q = t.prepare(bank, fx.FixtureTokenizer())\n"
              "print(t.prepare(bank, fx.FixtureTokenizer(merge='e '), **t.other_options(q))['manifest.sha256'].decode().strip())")
    digests = set()
    for seed in ("0", "4242"):
        done = subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT, capture_output=True, text=True,
                              env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"})
        assert done.returncode == 0, done.stderr[-400:]
        digests.add(done.stdout.strip())
    assert digests == {first[pp.MANIFEST_SHA].decode().strip()}


# ----- review fix 1: a guard input over the limit (lead decision 1) ----------------------------------------------


def over_limit_scorer(limit: int):
    from experiments.safety_selection.scoring import GuardScorer, guard_control_strings
    tokenizer = fx.FixtureGuardTokenizer()
    calls = []

    def generate(prompts, check=None):
        calls.append(len(prompts))
        return fx.scripted_guard_generate(tokenizer, None)(prompts, check)

    return GuardScorer(tokenizer, generate, limit, guard_control_strings(tokenizer), {}, fx.guard_logprobs()), calls


def test_an_over_limit_guard_input_refuses_by_default_and_is_unscored_only_when_asked():
    from experiments.safety_selection.scoring import GUARD_OVER_LIMIT
    from experiments.safety_selection.textproc import TooLong
    probe, _ = over_limit_scorer(100_000)
    short, long_ = ("p", "fine"), ("p", "word " * 400)
    limit = len(probe.input_ids(*short)) + 5                     # the short item fits, the long one does not
    scorer, calls = over_limit_scorer(limit)
    items = [("a", *short), ("b", *long_)]
    with pytest.raises(TooLong):
        scorer.score(items)
    with pytest.raises(TooLong):
        scorer.label_scores(items)
    records = scorer.score(items, over_limit_unscored=True)
    assert [r["item_id"] for r in records] == ["a", "b"] and calls[-1] == 1         # only the short item is judged
    assert records[0]["valid"] is True and records[1]["valid"] is False and records[1]["reason"] == GUARD_OVER_LIMIT
    assert records[1]["guard_input_tokens"] == len(probe.input_ids(*long_)) > limit
    assert records[1]["safety"] is None and set(records[1]) == set(records[0])
    scored = scorer.label_scores(items, over_limit_unscored=True)
    assert scored[0]["valid"] is True and scored[1]["reason"] == GUARD_OVER_LIMIT and scored[1]["normalized"] is None
    assert set(scored[1]) == set(scored[0])


def test_the_recipe_field_and_an_evaluation_that_goes_on_past_an_over_limit_answer(tmp_path):
    from experiments.safety_selection import runner
    from experiments.safety_selection.scoring import GUARD_OVER_LIMIT
    from experiments.safety_selection.textproc import TooLong
    validate_recipe(fx.recipe(**{"generation.guard_over_limit": "unscored"}))
    with pytest.raises(ConfigError, match="guard_over_limit"):
        validate_recipe(fx.recipe(**{"generation.guard_over_limit": "truncate"}))
    bank_dir, _ = fx.prepare_dir_v3(tmp_path / "prepared-v3")
    prepared, _ = fx.prepare_task_dir(tmp_path / "prepared-kt", bank_dir)
    samples = {"generation.harm_samples": {"count": 3, "temperature": 0.7, "top_p": 1.0}, "guard.max_input_tokens": 2}
    with pytest.raises(TooLong):                                   # without the field: refused, as before
        runner.calibrate(prepared_dir=prepared, out_root=tmp_path / "refused",
                         session=runner.Session(fx.recipe(**samples), fx.fixture_loaders()),
                         arms=["a0"], seeds=[1101], checkpoints=["e1"], base_eval=True)
    recipe = fx.recipe(**samples, **{"generation.guard_over_limit": "unscored"})
    runner.calibrate(prepared_dir=prepared, out_root=tmp_path / "round1", session=runner.Session(recipe, fx.fixture_loaders()),
                     arms=["a0"], seeds=[1101], checkpoints=["e1"], base_eval=True)
    folder = tmp_path / "round1" / "1101-a0-e1-a1" / "eval" / "e1"
    guard = jsonl((folder / "guard_samples.jsonl").read_bytes()) + jsonl((folder / "guard.jsonl").read_bytes())
    assert guard and all(g["reason"] == GUARD_OVER_LIMIT and g["guard_input_tokens"] > 2 for g in guard)
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["harm"]["sampled"]["unsafe"] == 0 and summary["harm"]["sampled"]["invalid"] == 6
    assert (tmp_path / "round1" / "1101-a0-e1-a1" / "COMPLETE.json").exists()
