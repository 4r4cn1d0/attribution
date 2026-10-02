"""Torch-side checks on ENGINEERING FIXTURES (CPU; nothing downloaded): batched masked loss
against the reference per-example loss, accumulation weighting by the actual examples
(partial steps included), refusal of non-finite steps, exact state round trips, batched greedy
decoding (EOS, caps, empty outputs, batch versus single, cached versus uncached), forced-choice
log-probabilities and per-example gradients that touch nothing; numeric regressions for
non-finite logits and the infinite-loss/finite-gradient counterexample; the forward-only query
loss; batched-prefill agreement; the bfloat16 reduced-precision flag (CPU, and the real CUDA
preflight when a GPU is present)."""

from __future__ import annotations

import math
import os
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import ss_fixtures as fx  # noqa: E402

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import textproc as tp  # noqa: E402

TRAIN = {"lr": 0.01, "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0.0}
EOS, ALT = 257, 258


def _examples(codec, n: int, offset: int = 0) -> list[tp.TrainExample]:
    return [tp.encode_train(codec, f"r-{i}", f"fixture prompt {'x' * (i % 3)}{i}",
                            f"fixture response {'y' * (2 * i)} {i} !", 256) for i in range(offset, offset + n)]


def _reference_loss(model, example: tp.TrainExample):
    ids = torch.tensor([list(example.input_ids)])
    labels = torch.tensor([[-100] * example.n_prompt + list(example.input_ids[example.n_prompt:])])
    return en.causal_lm(model)(input_ids=ids, labels=labels).loss


def _grad(named) -> torch.Tensor:
    return torch.cat([p.grad.reshape(-1) for _, p in named]).clone()


def _warm(model, named, codec) -> torch.optim.Optimizer:
    """A few real steps so lora_B is no longer zero (the adapter changes the outputs)."""
    optimizer = en.make_optimizer(named, TRAIN)
    examples = _examples(codec, 8, 20)
    for start in (0, 4):
        en.train_step(model, named, optimizer, examples[start:start + 4], 2, 1.0, codec.pad_id, "cpu", 16)
    return optimizer


def test_batched_loss_matches_the_reference_masked_per_example_loss(tiny, codec):
    model, named = tiny
    _warm(model, named, codec)
    examples = _examples(codec, 5)
    assert len({len(e.input_ids) for e in examples}) >= 4  # right padding really happens
    batched = en.example_losses(model, examples, codec.pad_id, "cpu", 7)
    for example, value in zip(examples, batched):
        assert torch.allclose(value, _reference_loss(model, example).float(), atol=1e-5)
        logits = en.causal_lm(model)(input_ids=torch.tensor([list(example.input_ids)])).logits[0].float()
        manual = -sum(torch.log_softmax(logits[t - 1], -1)[example.input_ids[t]]
                      for t in range(example.n_prompt, len(example.input_ids))) / example.n_target
        assert torch.allclose(value, manual, atol=1e-5)


def test_accumulation_weights_by_the_actual_examples_including_partial_steps(tiny, codec):
    model, named = tiny
    _warm(model, named, codec)
    examples = _examples(codec, 5)
    model.zero_grad(set_to_none=True)
    torch.stack([_reference_loss(model, e) for e in examples]).mean().backward()
    reference = _grad(named)
    for micro in (1, 2, 4, 5):
        model.zero_grad(set_to_none=True)
        losses = en.accumulate_gradients(model, examples, micro, codec.pad_id, "cpu", 16)
        assert len(losses) == 5
        assert torch.allclose(_grad(named), reference, rtol=1e-5, atol=1e-7), micro
    model.zero_grad(set_to_none=True)
    for start in (0, 4):  # the WRONG nominal weighting (1/8 per example) differs
        (en.example_losses(model, examples[start:start + 4], codec.pad_id, "cpu", 16).sum() / 8).backward()
    assert not torch.allclose(_grad(named), reference, rtol=1e-3)
    model.zero_grad(set_to_none=True)


def test_a_non_finite_step_is_refused_before_any_update(tiny, codec, monkeypatch):
    model, named = tiny
    optimizer = en.make_optimizer(named, TRAIN)
    before = en.lora_fingerprint(named)
    real = en.example_losses
    monkeypatch.setattr(en, "example_losses", lambda *a, **k: real(*a, **k) * float("nan"))
    with pytest.raises(en.NonFiniteError):
        en.train_step(model, named, optimizer, _examples(codec, 3), 2, 1.0, codec.pad_id, "cpu", 16)
    assert en.lora_fingerprint(named) == before and not optimizer.state


def test_saved_state_restores_training_exactly_and_tampering_is_detected(tiny, codec, tmp_path):
    model, named = tiny
    batches = [_examples(codec, 4, k) for k in (0, 4, 8)]
    en.load_lora_state(named, en.init_lora_state(named, 3))
    optimizer = en.make_optimizer(named, TRAIN)
    en.train_step(model, named, optimizer, batches[0], 2, 1.0, codec.pad_id, "cpu", 16)
    saved = en.save_state(tmp_path / "s", named, optimizer, "cpu", {"note": fx.FIXTURE})
    for batch in batches[1:]:
        en.train_step(model, named, optimizer, batch, 2, 1.0, codec.pad_id, "cpu", 16)
    direct = (en.lora_fingerprint(named), en.optimizer_fingerprint(optimizer, named))
    en.load_lora_state(named, en.init_lora_state(named, 99))  # scramble the live adapter
    restored = en.make_optimizer(named, TRAIN)
    state = en.load_state(tmp_path / "s", named, restored, "cpu")
    assert state["adapter_fingerprint"] == saved["adapter_fingerprint"] == en.lora_fingerprint(named)
    assert state["optimizer_fingerprint"] == en.optimizer_fingerprint(restored, named)
    for batch in batches[1:]:
        en.train_step(model, named, restored, batch, 2, 1.0, codec.pad_id, "cpu", 16)
    assert (en.lora_fingerprint(named), en.optimizer_fingerprint(restored, named)) == direct
    with pytest.raises(en.StateError, match="already has state"):
        en.load_state(tmp_path / "s", named, restored, "cpu")
    _, tensors = en.read_optimizer_tensors(tmp_path / "s")
    assert {float(tensors[f"step/{name}"][0]) for name, _ in named} == {1.0}  # saved after one step
    data = (tmp_path / "s" / en.ADAPTER).read_bytes()
    (tmp_path / "s" / en.ADAPTER).write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
    with pytest.raises(en.StateError, match="hash"):
        en.load_state(tmp_path / "s", named, en.make_optimizer(named, TRAIN), "cpu")


class ScriptedLM(torch.nn.Module):
    """ENGINEERING FIXTURE: emits a fixed token script per prompt (keyed by its first real
    token); the cache object counts decoding steps."""

    def __init__(self, scripts: dict[int, list[int]]) -> None:
        super().__init__()
        self.scripts = scripts
        self.anchor = torch.nn.Parameter(torch.zeros(1))

    def forward(self, input_ids, attention_mask=None, position_ids=None, past_key_values=None,
                use_cache=True, logits_to_keep=1, **kwargs):
        if past_key_values is None:
            keys = [int(row[mask.bool()][0]) for row, mask in zip(input_ids, attention_mask)]
            cache = {"keys": keys, "step": 0}
        else:
            cache = past_key_values
            cache["step"] += 1
        logits = torch.zeros((input_ids.shape[0], 1, fx.VOCAB))
        for i, key in enumerate(cache["keys"]):
            script = self.scripts[key]
            logits[i, 0, script[min(cache["step"], len(script) - 1)]] = 1.0
        return SimpleNamespace(logits=logits, past_key_values=cache)


class PoisonedLM(ScriptedLM):
    """ENGINEERING FIXTURE: ScriptedLM whose logits for chosen (row key, forward index) pairs
    are overwritten with a non-finite value (all entries, or one entry with ``(value, index)``)."""

    def __init__(self, scripts: dict[int, list[int]], poison: dict[tuple[int, int], object]) -> None:
        super().__init__(scripts)
        self.poison = poison

    def forward(self, *args, **kwargs):
        out = super().forward(*args, **kwargs)
        cache = out.past_key_values
        for i, key in enumerate(cache["keys"]):
            value = self.poison.get((key, cache["step"]))
            if isinstance(value, tuple):
                out.logits[i, 0, value[1]] = value[0]
            elif value is not None:
                out.logits[i, 0, :] = value
        return out


def test_all_nan_prefill_logits_raise_instead_of_posing_as_a_stop_token():
    # The lead's reproduction: argmax over all-NaN logits is index 0; with stop id 0 the
    # unchecked decoder returned an empty EOS completion.
    assert int(torch.full((fx.VOCAB,), float("nan")).argmax()) == 0
    model = PoisonedLM({10: [5, EOS]}, {(10, 0): float("nan")})
    with pytest.raises(en.NonFiniteError, match="prompt pass"):
        en.greedy_generate(model, [[10, 1]], max_new_tokens=3, stop_ids=(0,), pad_id=1, device="cpu",
                           batch_size=1)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), (float("inf"), 3),
                                   (float("-inf"), 200), (float("nan"), 7)])
def test_non_finite_logits_of_an_active_row_raise_at_any_decoding_step(value):
    scripts = {10: [5, 6, 7, EOS], 11: [8, 8, 8, EOS]}
    model = PoisonedLM(scripts, {(11, 2): value})  # row 11 is still generating at its third token
    with pytest.raises(en.NonFiniteError, match="token 3"):
        en.greedy_generate(model, [[10], [11]], max_new_tokens=6, stop_ids=(EOS,), pad_id=0, device="cpu",
                           batch_size=2)


def test_a_finished_rows_logits_are_never_used_or_checked():
    scripts = {10: [5, 6, 7, EOS], 11: [EOS]}
    clean = en.greedy_generate(ScriptedLM(scripts), [[10], [11]], max_new_tokens=6, stop_ids=(EOS,),
                               pad_id=0, device="cpu", batch_size=2)
    poisoned = en.greedy_generate(PoisonedLM(scripts, {(11, k): float("nan") for k in (1, 2, 3)}),
                                  [[10], [11]], max_new_tokens=6, stop_ids=(EOS,), pad_id=0,
                                  device="cpu", batch_size=2)
    assert poisoned == clean and clean[1] == en.Generation((), "eos", EOS)


class _ZeroBody(torch.nn.Module):
    def forward(self, input_ids, attention_mask=None, use_cache=False, **kwargs):
        return SimpleNamespace(last_hidden_state=torch.zeros(input_ids.shape + (1,)))


class _InfiniteHead(torch.nn.Module):
    """logits [-inf, theta] at every position."""

    def __init__(self) -> None:
        super().__init__()
        self.theta = torch.nn.Parameter(torch.tensor([0.25]))

    def forward(self, hidden):
        return torch.cat([torch.full_like(hidden, float("-inf")), hidden + self.theta], dim=-1)


class InfiniteTargetLM(torch.nn.Module):
    """ENGINEERING FIXTURE: two-token vocabulary with logits [-inf, theta]; target token 0 has
    infinite cross-entropy whose autograd gradient for theta is still the finite value 1."""

    def __init__(self) -> None:
        super().__init__()
        self.model, self.lm_head = _ZeroBody(), _InfiniteHead()


def test_an_infinite_loss_is_refused_before_autograd_although_its_gradient_is_finite():
    model = InfiniteTargetLM()
    named = [("lm_head.theta", model.lm_head.theta)]
    example = tp.TrainExample("inf-row", (1, 1, 0, 0), 2)  # targets 0, 0
    loss = en.example_losses(model, [example], 1, "cpu", 4)[0]
    (grad,) = torch.autograd.grad(loss, [model.lm_head.theta])
    assert math.isinf(float(loss)) and torch.isfinite(grad).all() and float(grad) == pytest.approx(1.0)
    with pytest.raises(en.NonFiniteError, match="no gradient is taken"):
        en.example_gradient(model, named, example, pad_id=1, device="cpu", chunk=4)
    with pytest.raises(en.NonFiniteError):
        en.target_logprobs(model, [example.input_ids], [example.n_target], pad_id=1, device="cpu",
                           batch_size=1, chunk=4)
    with pytest.raises(en.NonFiniteError):
        en.query_losses(model, [example], pad_id=1, device="cpu", chunk=4)
    optimizer = en.make_optimizer(named, TRAIN)
    with pytest.raises(en.NonFiniteError):
        en.train_step(model, named, optimizer, [example], 1, 1.0, 1, "cpu", 4)
    assert float(model.lm_head.theta) == 0.25 and not optimizer.state


def test_query_loss_is_the_training_objective_forward_only_and_touches_nothing(tiny, codec):
    model, named = tiny
    optimizer = _warm(model, named, codec)
    model.train()
    queries = _examples(codec, 4, 40)
    before = (en.lora_fingerprint(named), en.optimizer_fingerprint(optimizer, named), en.rng_digest("cpu"))
    seen: list[str] = []
    values = en.query_losses(model, queries, pad_id=codec.pad_id, device="cpu", chunk=5, check=seen.append)
    assert model.training and all(p.grad is None for _, p in named)
    assert (en.lora_fingerprint(named), en.optimizer_fingerprint(optimizer, named), en.rng_digest("cpu")) == before
    assert seen == [f"query loss {q.row_id}" for q in queries]
    for query, value in zip(queries, values):
        # the direct response-only NLL: HF's masked mean over response + end-of-turn targets
        assert value == pytest.approx(float(_reference_loss(model, query)), abs=1e-6)
    batched = en.example_losses(model, queries, codec.pad_id, "cpu", 7)  # a padded training batch
    assert values == pytest.approx([float(v) for v in batched], abs=1e-5)
    loss, _ = en.example_loss_and_gradient(model, named, queries[0], pad_id=codec.pad_id, device="cpu", chunk=5)
    assert loss == pytest.approx(values[0], rel=1e-6)  # the attribution pass records the same loss


def test_batched_left_padded_prefill_agrees_with_single_prompts(tiny, codec):
    model, named = tiny
    _warm(model, named, codec)
    prompts = [tp.encode_generation_prompt(codec, text, 400) for text in ("hi", "a much longer prompt here", "x")]
    out = en.prefill_logit_agreement(model, prompts, pad_id=codec.pad_id, device="cpu")
    assert [r["tokens"] for r in out] == [len(p) for p in prompts]
    assert all(r["max_abs_hidden_difference"] < 1e-5 and r["max_abs_last_logit_difference"] < 1e-5
               and r["last_argmax_agrees"] and r["single_top2_margin"] >= 0 for r in out)


def test_the_bf16_reduced_precision_flag_is_set_read_back_and_recorded():
    from experiments.safety_selection import loaders

    before = torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction
    try:
        torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = True
        assert loaders.numeric_flags() == {loaders.BF16_REDUCTION_FLAG: True}
        assert loaders.forbid_bf16_reduced_precision() == {loaders.BF16_REDUCTION_FLAG: False}
        assert torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction is False
    finally:
        torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = before


@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs one visible CUDA GPU (a skip is not a pass)")
def test_real_cuda_preflight_disables_and_records_bf16_reduced_precision():
    from experiments.minimal_safety.model import numeric_settings, set_numeric_settings
    from experiments.safety_selection import loaders

    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") not in (":4096:8", ":16:8"):
        pytest.skip("export CUBLAS_WORKSPACE_CONFIG=:4096:8 before starting Python (a skip is not a pass)")
    settings, flag = numeric_settings(), torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction
    try:
        device = loaders._prepare_cuda(fx.recipe(**{"model.device": "cuda"}))
        environment = loaders._environment(device)
        assert environment["safety_selection_numeric"] == {loaders.BF16_REDUCTION_FLAG: False}
        assert environment["cuda"]["settings"]["cuda_matmul_allow_tf32"] is False
        assert environment["cuda"]["settings"]["deterministic_algorithms"] is True
    finally:
        set_numeric_settings(settings)
        torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = flag


def test_generation_distinguishes_eos_token_caps_and_empty_outputs():
    model = ScriptedLM({10: [5, 6, EOS], 11: [EOS], 12: [7], 13: [8, 8, ALT], 14: [9, 9, 9, EOS]})
    prompts = [[10, 1], [11], [12, 2, 3], [13], [14, 4]]
    expected = [((5, 6), "eos", EOS), ((), "eos", EOS), ((7, 7, 7), "max_new_tokens", None),
                ((8, 8), "eos", ALT),  # a stop token at the last allowed position still stops
                ((9, 9, 9), "max_new_tokens", None)]  # its stop token would come one token later
    for batch_size in (1, 2, 5):
        out = en.greedy_generate(model, prompts, max_new_tokens=3, stop_ids=(EOS, ALT), pad_id=0,
                                 device="cpu", batch_size=batch_size)
        assert [(g.output_ids, g.stop_reason, g.stop_token) for g in out] == expected


def test_left_padded_batched_generation_matches_single_and_uncached_argmax(tiny, codec):
    model, named = tiny
    _warm(model, named, codec)
    prompts = [tp.encode_generation_prompt(codec, text, 400)
               for text in ("hi", "a much longer fixture prompt is here", "mid length prompt", "x")]
    kwargs = {"max_new_tokens": 6, "stop_ids": codec.stop_ids, "pad_id": codec.pad_id, "device": "cpu"}
    batched = en.greedy_generate(model, prompts, batch_size=4, **kwargs)
    assert batched == en.greedy_generate(model, prompts, batch_size=1, **kwargs)
    assert batched == en.greedy_generate(model, prompts, batch_size=3, **kwargs)
    lm = en.causal_lm(model)
    with torch.no_grad():
        for prompt, generation in zip(prompts, batched):
            sequence = list(prompt)
            for token in generation.output_ids:
                assert int(lm(input_ids=torch.tensor([sequence])).logits[0, -1].argmax()) == token
                sequence.append(token)
            if generation.stop_reason == "eos":
                assert int(lm(input_ids=torch.tensor([sequence])).logits[0, -1].argmax()) == generation.stop_token
            else:
                assert len(generation.output_ids) == 6


def test_generation_and_scoring_leave_weights_mode_and_rng_unchanged(tiny, codec):
    model, named = tiny
    optimizer = _warm(model, named, codec)
    model.train()
    before = (en.lora_fingerprint(named), en.optimizer_fingerprint(optimizer, named), en.rng_digest("cpu"))
    prompt = tp.encode_generation_prompt(codec, "hello", 400)
    en.greedy_generate(model, [prompt], max_new_tokens=4, stop_ids=codec.stop_ids, pad_id=codec.pad_id,
                       device="cpu", batch_size=1)
    en.target_logprobs(model, [prompt + [65]], [1], pad_id=codec.pad_id, device="cpu", batch_size=1, chunk=4)
    assert model.training
    assert (en.lora_fingerprint(named), en.optimizer_fingerprint(optimizer, named), en.rng_digest("cpu")) == before


def test_forced_choice_logprobs_are_teacher_forced_label_logprobs(tiny, codec):
    model, named = tiny
    _warm(model, named, codec)
    prompt, targets = tp.encode_mc(codec, "Which is a gas?", ["A", "10"], ["iron", "oxygen"], 400)
    sequences = [prompt + t for t in targets]
    out = en.target_logprobs(model, sequences, [len(t) for t in targets], pad_id=codec.pad_id,
                             device="cpu", batch_size=2, chunk=1)
    assert [len(v) for v in out] == [1, 2]  # one log-probability per label token; no end-of-turn
    lm = en.causal_lm(model)
    for sequence, target, values in zip(sequences, targets, out):
        with torch.no_grad():
            logp = torch.log_softmax(lm(input_ids=torch.tensor([sequence])).logits[0].float(), -1)
        start = len(sequence) - len(target) - 1
        manual = [float(logp[start + j, token]) for j, token in enumerate(target)]
        assert values == pytest.approx(manual, abs=1e-5)


def test_example_gradient_matches_autograd_and_leaves_grad_untouched(tiny, codec):
    model, named = tiny
    _warm(model, named, codec)
    example = _examples(codec, 1)[0]
    vector = en.example_gradient(model, named, example, pad_id=codec.pad_id, device="cpu", chunk=4)
    params = [p for _, p in named]
    reference = torch.cat([g.reshape(-1) for g in torch.autograd.grad(_reference_loss(model, example), params)])
    assert vector.dtype == torch.float64 and vector.device.type == "cpu"
    assert torch.allclose(vector, reference.double(), atol=1e-6)
    assert all(p.grad is None for p in params)
