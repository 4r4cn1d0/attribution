"""Torch-side checks on a tiny random ENGINEERING FIXTURE model (CPU; nothing downloaded):
LoRA vector, seeded initialization, response-only loss, evaluation isolation, greedy
decoding, cooperative cap-check hooks, gradient cosine sign/normalization/aggregation,
checkpoint round trips and the chat-template codec (a fixture tokenizer, plus the pinned
cached Qwen tokenizer when it is present locally)."""

from __future__ import annotations

import math

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

from experiments.minimal_safety import model as tm  # noqa: E402
from experiments.minimal_safety.plan import asset_status  # noqa: E402
from experiments.minimal_safety.text import encode_example, encode_prompt  # noqa: E402

TRAIN = {"lr": 0.01, "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0.0}
QWEN = ("Qwen/Qwen2.5-0.5B-Instruct", "7ae557604adf67be50417f59c2c2f167def9a775")
STOPS = ["<|im_end|>", "<|endoftext|>"]


class MergingTokenizer:
    """ENGINEERING FIXTURE tokenizer: one id per character, except that two consecutive
    newlines form one token (a BPE-style merge) and the special strings are atomic."""

    SPECIAL = {"<|im_start|>": 1000, "<|im_end|>": 1001, "<|endoftext|>": 1002}
    unk_token_id = None

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        ids, i = [], 0
        while i < len(text):
            special = next((t for t in self.SPECIAL if text.startswith(t, i)), None)
            if special:
                ids.append(self.SPECIAL[special])
                i += len(special)
            elif text.startswith("\n\n", i):
                ids.append(999)
                i += 2
            else:
                ids.append(ord(text[i]))
                i += 1
        return ids

    def apply_chat_template(self, messages, tokenize: bool, add_generation_prompt: bool):
        text = "<|im_start|>system\nfixture<|im_end|>\n" + "".join(
            f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in messages)
        text += "<|im_start|>assistant\n" if add_generation_prompt else ""
        return self.encode(text) if tokenize else text

    def convert_tokens_to_ids(self, token: str) -> int | None:
        return self.SPECIAL.get(token)

    def decode(self, ids, skip_special_tokens: bool = True) -> str:
        return "".join("\n\n" if i == 999 else chr(i) for i in ids if i < 1000)


def _examples(codec, n=4):
    return [encode_example(codec, f"fixture:{i}", f"fixture prompt {i}", f"fixture response {i} !",
                           96, 16) for i in range(n)]


def _train(model, named, examples, seed):
    tm.load_lora_state(named, tm.init_lora_state(named, seed))
    optimizer = tm.make_optimizer(named, TRAIN)
    for ex in examples:
        tm.train_step(model, named, optimizer, ex, 1.0, "cpu")
    return tm.lora_fingerprint(named)


def test_lora_parameter_vector_is_all_and_only_lora(tiny):
    model, named = tiny
    assert all(".lora_A." in n or ".lora_B." in n for n, _ in named)
    assert tm.parameter_count(named) == 448
    next(p for n, p in model.named_parameters() if "embed_tokens" in n).requires_grad_(True)
    with pytest.raises(ValueError, match="outside LoRA"):
        tm.lora_parameters(model)


def test_seeded_initialization_is_identical_within_a_seed_and_a_no_op(tiny, codec):
    model, named = tiny
    first, again, other = (tm.init_lora_state(named, s) for s in (101, 101, 202))
    assert all(torch.equal(first[n], again[n]) for n in first)
    assert any(not torch.equal(first[n], other[n]) for n in first if ".lora_A." in n)
    assert all(int(torch.count_nonzero(first[n])) == 0 for n in first if ".lora_B." in n)
    tm.load_lora_state(named, first)
    ids = torch.tensor([list(_examples(codec, 1)[0].input_ids)])
    with torch.no_grad():
        adapted = model(input_ids=ids).logits
        with model.disable_adapter():
            base = model(input_ids=ids).logits
    assert torch.equal(adapted, base)  # B = 0: the initial adapter leaves the base model unchanged


def test_each_arm_restarts_from_the_same_adapter_with_a_fresh_optimizer(tiny, codec):
    model, named = tiny
    examples = _examples(codec)
    tm.load_lora_state(named, tm.init_lora_state(named, 7))
    start = tm.lora_fingerprint(named)
    a0 = _train(model, named, examples, 7)
    reordered = _train(model, named, examples[1:] + examples[:1], 7)
    assert start not in (a0, reordered) and a0 != reordered
    assert _train(model, named, examples, 7) == a0  # same init, data and fresh optimizer


def test_loss_is_the_mean_over_response_tokens_only(tiny, codec):
    model, _ = tiny
    ex = _examples(codec, 1)[0]
    loss = tm.response_loss(model, ex, "cpu")
    ids = torch.tensor([list(ex.input_ids)])
    logits = model(input_ids=ids).logits[0]
    manual = sum(-torch.log_softmax(logits[t - 1], -1)[ex.input_ids[t]]
                 for t in range(ex.prompt_len, len(ex.input_ids))) / ex.n_target
    assert torch.allclose(loss, manual, atol=1e-6)
    assert torch.allclose(loss, model(input_ids=ids, labels=torch.tensor([ex.labels()])).loss, atol=1e-6)


def test_interleaved_evaluation_does_not_change_the_training_trajectory(tiny, codec):
    model, named = tiny
    examples = _examples(codec)
    prompt, _ = encode_prompt(codec, "fixture prompt 0", 92)

    def run(with_eval: bool):
        tm.load_lora_state(named, tm.init_lora_state(named, 3))
        optimizer = tm.make_optimizer(named, TRAIN)
        torch.manual_seed(0)
        for i, ex in enumerate(examples):
            tm.train_step(model, named, optimizer, ex, 1.0, "cpu")
            if with_eval and i == 1:
                generations, nlls = tm.generate_and_nll(model, [prompt], [ex], 4, codec.stop_ids, "cpu")
                assert model.training and len(generations[0][0]) <= 4 and math.isfinite(nlls[0])
        return tm.lora_fingerprint(named), torch.random.get_rng_state()

    plain, interleaved = run(False), run(True)
    assert plain[0] == interleaved[0] and torch.equal(plain[1], interleaved[1])


def test_cap_checks_run_before_every_forward_pass_and_stop_the_work(tiny, codec):
    model, _ = tiny
    prompt, _ = encode_prompt(codec, "fixture prompt", 92)
    seen: list[str] = []
    ids, stopped = tm.greedy(model, prompt, 5, (), "cpu", check=seen.append)  # no stop ids
    assert len(ids) == 5 and not stopped
    assert seen == ["prompt", "token 2", "token 3", "token 4", "token 5"]

    class Stop(Exception):
        pass

    def stop_at(prefix):
        def check(what):
            seen.append(what)
            if what.startswith(prefix):
                raise Stop(what)
        return check

    seen.clear()
    with pytest.raises(Stop, match="nll 1"):
        tm.generate_and_nll(model, [prompt, prompt], _examples(codec, 1), 2, (), "cpu",
                            check=stop_at("nll"))
    assert seen == ["generation 1 prompt", "generation 1 token 2", "generation 2 prompt",
                    "generation 2 token 2", "nll 1"]
    assert model.training  # the previous mode is restored even when a check stops the work
    with pytest.raises(Stop, match="group gradient"):
        tm.query_group_cosine(model, tm.lora_parameters(model), _examples(codec, 1),
                              _examples(codec, 2), "cpu", check=stop_at("group"))
    assert model.training


def test_greedy_decoding_is_bounded_and_matches_uncached_argmax(tiny, codec):
    model, _ = tiny
    prompt, _ = encode_prompt(codec, "fixture prompt", 92)
    ids, stopped = tm.greedy(model, prompt, 6, codec.stop_ids, "cpu")
    assert (ids, stopped) == tm.greedy(model, prompt, 6, codec.stop_ids, "cpu")
    assert len(ids) <= 6 and (stopped or len(ids) == 6) and not set(ids) & set(codec.stop_ids)
    sequence = list(prompt)
    with torch.no_grad():
        for token in ids:
            assert int(model(input_ids=torch.tensor([sequence])).logits[0, -1].argmax()) == token
            sequence.append(token)


def test_cosine_sign_normalization_and_rejections():
    e1 = torch.tensor([1.0, 0.0], dtype=torch.float64)
    e2 = torch.tensor([0.0, 1.0], dtype=torch.float64)
    assert tm.cosine(e1, 3 * e1) == pytest.approx(1.0)
    assert tm.cosine(e1, -0.5 * e1) == pytest.approx(-1.0)
    assert tm.cosine(e1, e2) == 0.0
    assert tm.cosine(2 * e1 + e2, e1) == pytest.approx(tm.cosine(20 * e1 + 10 * e2, 0.1 * e1))
    with pytest.raises(tm.ZeroGradientError):
        tm.cosine(e1, torch.zeros(2, dtype=torch.float64))
    with pytest.raises(tm.NonFiniteError):
        tm.cosine(e1, torch.tensor([math.nan, 1.0], dtype=torch.float64))


def test_group_score_is_the_cosine_of_means_not_a_mean_of_cosines():
    def vec(*xs):
        return torch.tensor(xs, dtype=torch.float64)

    query, group = {"q": vec(1.0, 0.0)}, {"a": vec(10.0, 1.0), "b": vec(-1.0, 1.0)}
    out = tm.aggregate_cosine(query, group)
    assert out["cosine_of_means"] == pytest.approx(4.5 / math.sqrt(4.5 ** 2 + 1.0))
    assert out["per_example_cosine"] == pytest.approx({"a": 10 / math.sqrt(101), "b": -1 / math.sqrt(2)})
    assert abs(out["cosine_of_means"] - sum(out["per_example_cosine"].values()) / 2) > 0.5
    flipped = tm.aggregate_cosine(query, {k: -v for k, v in group.items()})
    assert flipped["cosine_of_means"] == pytest.approx(-out["cosine_of_means"])
    with pytest.raises(tm.ZeroGradientError):
        tm.aggregate_cosine(query, {"a": vec(1.0, 2.0), "c": vec(-1.0, -2.0)})  # mean is zero


def test_positive_cosine_means_a_group_step_lowers_query_loss_to_first_order():
    theta = torch.tensor([0.3, -0.2], dtype=torch.float64)
    a = torch.tensor([1.0, 0.5], dtype=torch.float64)  # query loss |theta - a|^2 / 2
    for b in ([2.0, 1.0], [-1.0, -2.0]):  # group loss |theta - b|^2 / 2
        grad_query, grad_group = theta - a, theta - torch.tensor(b, dtype=torch.float64)
        after = theta - 1e-3 * grad_group
        change = 0.5 * float(((after - a) ** 2).sum() - ((theta - a) ** 2).sum())
        assert (tm.cosine(grad_query, grad_group) > 0) == (change < 0)


def test_query_group_cosine_matches_manual_gradients_and_touches_nothing(tiny, codec):
    model, named = tiny
    examples = _examples(codec, 6)
    _train(model, named, examples[:4], 5)
    before = tm.lora_fingerprint(named)
    seen: list[str] = []
    out = tm.query_group_cosine(model, named, examples[4:], examples[:2], "cpu", check=seen.append)
    assert tm.lora_fingerprint(named) == before and model.training
    assert seen == ["query gradient fixture:4", "query gradient fixture:5",
                    "group gradient fixture:0", "group gradient fixture:1"]
    # The runner spreads this dict into a record whose own "kind" is "attribution".
    assert "kind" not in out and out["definition"] == tm.COSINE_DEFINITION
    params = [p for _, p in named]

    def grad(ex):
        return torch.cat([g.reshape(-1) for g in torch.autograd.grad(
            tm.response_loss(model, ex, "cpu"), params)]).double()

    query, group = (grad(examples[4]) + grad(examples[5])) / 2, (grad(examples[0]) + grad(examples[1])) / 2
    expected = float(query @ group / (query.norm() * group.norm()))
    assert out["cosine_of_means"] == pytest.approx(expected, rel=1e-9, abs=1e-12)
    assert set(out["per_example_cosine"]) == {"fixture:0", "fixture:1"}
    assert out["parameters"] == tm.parameter_count(named)


def test_checkpoint_round_trip_preserves_the_adapter(tmp_path, tiny):
    _, named = tiny
    tm.load_lora_state(named, tm.init_lora_state(named, 9))
    with torch.no_grad():
        for _, p in named:
            p.add_(0.01)
    fingerprint = tm.lora_fingerprint(named)
    assert len(tm.save_lora(named, tmp_path / "a.safetensors", {"step": 3})) == 64
    tm.load_lora_state(named, tm.init_lora_state(named, 1))
    assert tm.lora_fingerprint(named) != fingerprint
    tm.load_lora_state(named, tm.read_lora(tmp_path / "a.safetensors"))
    assert tm.lora_fingerprint(named) == fingerprint


def test_codec_encodes_a_leading_newline_prompt_like_the_canonical_template():
    tok = MergingTokenizer()
    codec, _ = tm.chat_codec(tok, "<|im_end|>", STOPS)
    prompt = "\nwrite a short poem"
    canonical = tok.apply_chat_template([{"role": "user", "content": prompt}], tokenize=True,
                                        add_generation_prompt=True)
    separate = list(codec.head_ids) + tok.encode(prompt) + list(codec.tail_ids)
    assert len(separate) == len(canonical) + 1  # the old split encoding: one token too many
    assert codec.encode_turn(prompt) + list(codec.tail_ids) == canonical == codec.reference(prompt)
    ids, cut = encode_prompt(codec, prompt, len(canonical))
    assert ids == canonical and not cut
    ex = encode_example(codec, "fixture:0", prompt, "ok", 96, 8)
    assert list(ex.input_ids[:ex.prompt_len]) == canonical and ex.n_target == 3
    head_and_tail = len(codec.head_ids) + len(codec.tail_ids)
    ids, cut = encode_prompt(codec, prompt, head_and_tail)  # no room for user text beyond the join
    assert cut and tok.decode(ids).startswith(tok.decode(list(codec.head_ids)))
    assert ids[-len(codec.tail_ids):] == list(codec.tail_ids)


def test_codec_matches_the_cached_qwen_template_on_leading_whitespace():
    """The pinned tokenizer from the local cache only (offline; skipped when the snapshot is
    absent, and a skip is not a pass). The leading newline is the prepared-data edge case."""
    status = asset_status(*QWEN)
    if not status["present"]:
        pytest.skip(f"no cached snapshot at {status['snapshot']}")
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(status["snapshot"], local_files_only=True,
                                        trust_remote_code=False)
    codec, _ = tm.chat_codec(tok, "<|im_end|>", STOPS)
    for prompt in ("\nHow do I write a poem?", "\n\n  indented\nlines", " leading space",
                   "plain prompt", "trailing newline\n"):
        assert codec.encode_turn(prompt) + list(codec.tail_ids) == codec.reference(prompt), prompt
    prompt = "\nHow do I write a poem?"
    separate = list(codec.head_ids) + codec.encode(prompt) + list(codec.tail_ids)
    assert separate != codec.reference(prompt)  # the case the old split encoding got wrong
