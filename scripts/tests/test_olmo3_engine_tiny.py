"""The engine on ``Olmo3ForCausalLM`` (track O3A-env-preflight, blocker B1's rest; the OLMo 3 plan draft O3A §16.1), on
CPU in float32 with the tiny random model of olmo3_tiny.py (sliding-window layers kept; nothing downloaded), the checks of
experiments/safety_selection/tests/test_ss_family_models.py and two more: (a) the LoRA count is r * sum(in + out) over the
seven targets and no norm trains; (b) with B = 0 the logits equal the plain model's bit for bit; (c) gradient checkpointing
(use_reentrant False, as the loader sets it) gives the same losses and gradients; (d) greedy decoding of a left-padded batch
of 2 equals one prompt at a time; (e) one forward and backward pass with an optimizer step through ``engine.train_step``
and ``engine.make_optimizer`` moves the adapter and nothing else; (f) with the cached OLMo 3 tokenizer, the engine's codec,
assistant-header check and the preflight's chat tokens accept the real template (skipped when the snapshot is absent).
Everything skips under a transformers without ``olmo3`` (the engine lock's 4.56.2); the OLMo 3 lock has 4.57.1."""

from __future__ import annotations

import json

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
pytest.importorskip("peft")

import olmo3_tiny as tiny  # noqa: E402

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection.textproc import TrainExample  # noqa: E402

if not tiny.has_olmo3():
    pytest.skip("transformers has no olmo3 model code (OLMo 3 needs 4.57.0 or higher)", allow_module_level=True)

TOKENS = {"<|endoftext|>": 100257, "<|im_start|>": 100264, "<|im_end|>": 100265, "<|pad|>": 100277}


def test_the_tiny_config_is_the_scaled_down_real_config():
    if not (tiny.SNAPSHOT / "config.json").exists():
        pytest.skip(f"no cached OLMo 3 snapshot at {tiny.SNAPSHOT}")
    real = json.loads((tiny.SNAPSHOT / "config.json").read_text(encoding="utf-8"))
    assert {k: real[k] for k in tiny.REAL_SIZES} == tiny.REAL_SIZES
    assert real["rope_scaling"]["original_max_position_embeddings"] == tiny.REAL_ORIGINAL_POSITIONS
    assert tiny.scaled_down(real) == tiny.tiny_config_dict()


def test_the_model_class_keeps_the_sliding_layers_and_the_yarn_scaling():
    plain = tiny.plain_model()
    assert type(plain).__name__ == "Olmo3ForCausalLM"
    layers = en.causal_lm(plain).model.layers
    assert [layer.self_attn.attention_type for layer in layers] == tiny.tiny_config_dict()["layer_types"]
    assert [layer.self_attn.sliding_window for layer in layers] == [4096, 4096, 4096, None]
    assert plain.config.rope_scaling["rope_type"] == "yarn"
    assert plain.get_input_embeddings().weight.shape == (tiny.VOCAB, 32)
    assert plain.get_output_embeddings().weight.data_ptr() != plain.get_input_embeddings().weight.data_ptr()


def test_the_lora_count_is_rank_times_in_plus_out_and_no_norm_trains():
    plain, model, named = tiny.build()
    expected = sum(tiny.RANK * (m.in_features + m.out_features) for name, m in plain.named_modules()
                   if isinstance(m, torch.nn.Linear) and name.rsplit(".", 1)[-1] in tiny.TARGETS)
    assert en.parameter_count(named) == expected == tiny.RANK * 4 * (4 * 64 + 2 * 96 + 96)
    assert not [n for n, _ in named if "norm" in n]
    assert len({n.rsplit(".lora_", 1)[0] for n, _ in named}) == 7 * plain.config.num_hidden_layers
    assert any("q_norm" in n for n, _ in plain.named_parameters())             # present, and not a target
    assert not [n for n, _ in model.named_parameters() if en.TOKEN_ROWS in n]  # no token rows train


def test_with_b_zero_the_logits_equal_the_plain_models_bit_for_bit():
    plain, model, _ = tiny.build()
    ids = torch.tensor([[100257, 17, 23, 99, 150, 7, 42, 5, 100264, 78191]])
    with torch.no_grad():
        a = en.causal_lm(model)(input_ids=ids).logits
        b = plain(input_ids=ids).logits
    assert torch.equal(a, b)


def test_gradient_checkpointing_gives_the_same_losses_and_gradients():
    examples = [TrainExample(f"r{k}", tuple(range(2 + k, 14 + 3 * k)) + (100257,), 4) for k in range(4)]
    results = []
    for checkpointing in (False, True):
        _, model, named = tiny.build()
        with torch.no_grad():                                                   # a non-zero B
            for n, p in named:
                if ".lora_B." in n:
                    p.normal_(0, 0.02, generator=torch.Generator().manual_seed(3))
        if checkpointing:
            en.causal_lm(model).gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.train()
        model.zero_grad(set_to_none=True)
        losses = en.accumulate_gradients(model, examples, 2, TOKENS["<|pad|>"], "cpu", 16)
        results.append((losses, [p.grad.detach().clone() for _, p in named]))
    assert results[0][0] == pytest.approx(results[1][0], rel=1e-6)
    for a, b in zip(results[0][1], results[1][1]):
        assert torch.allclose(a, b, rtol=1e-5, atol=1e-7)


def test_greedy_decoding_of_a_left_padded_batch_equals_one_prompt_at_a_time():
    _, model, named = tiny.build()
    with torch.no_grad():
        for n, p in named:
            if ".lora_B." in n:
                p.normal_(0, 0.02, generator=torch.Generator().manual_seed(5))
    prompts = [[100264, 17, 23, 99], [100264, 150, 7, 42, 5, 88, 61]]            # different lengths: left padding
    options = dict(max_new_tokens=12, stop_ids=[TOKENS["<|endoftext|>"], TOKENS["<|im_end|>"]], pad_id=TOKENS["<|pad|>"],
                   device="cpu")
    together = en.greedy_generate(model, prompts, batch_size=2, **options)
    single = en.greedy_generate(model, prompts, batch_size=1, **options)
    assert together == single and all(len(g.output_ids) > 0 for g in single)


def test_one_train_step_moves_only_the_adapter():
    """One forward and backward pass with an optimizer step through the engine (the resume check's path)."""
    plain, model, named = tiny.build()
    train = {"optimizer": "AdamW", "lr": 1e-3, "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0.0}
    optimizer = en.make_optimizer(named, train)
    examples = [TrainExample(f"r{k}", tuple(range(5 + k, 17 + 2 * k)) + (100257,), 5) for k in range(4)]
    frozen_before = {n: p.detach().clone() for n, p in model.named_parameters() if not p.requires_grad}
    model.train()
    result = en.train_step(model, named, optimizer, examples, 2, 1.0, TOKENS["<|pad|>"], "cpu", 16)
    assert result["loss"] > 0 and torch.isfinite(torch.tensor(result["loss"]))
    assert any(not torch.equal(p, torch.zeros_like(p)) for n, p in named if ".lora_B." in n)   # B moved off zero
    assert all(torch.equal(frozen_before[n], p) for n, p in model.named_parameters() if not p.requires_grad)
    assert torch.equal(plain.get_input_embeddings().weight, en.effective_embedding_weights(model)[0])


def test_the_real_tokenizer_fits_the_codec_and_the_assistant_header():
    if not (tiny.SNAPSHOT / "tokenizer.json").exists():
        pytest.skip(f"no cached OLMo 3 snapshot at {tiny.SNAPSHOT}")
    from experiments.safety_selection.textproc import build_codec, check_assistant_header

    tokenizer = transformers.AutoTokenizer.from_pretrained(str(tiny.SNAPSHOT), local_files_only=True, trust_remote_code=False)
    codec = build_codec(tokenizer, "<|endoftext|>", ["<|endoftext|>", "<|im_end|>"], "<|pad|>")
    assert (codec.eos_id, codec.stop_ids, codec.pad_id) == (100257, (100257, 100265), 100277)
    probe = check_assistant_header(codec, "<|im_start|>assistant\n")
    assert probe.endswith("<|im_start|>user\n<<probe>><|im_end|>\n<|im_start|>assistant\n")
    joint = codec.conversation_ids("<<probe>>", "<<reply>>")
    assert joint[-1] == 100257 and sorted({i for i in joint if i in codec.special_ids}) == [100257, 100264, 100265]
    assert len(tokenizer) == tiny.VOCAB
