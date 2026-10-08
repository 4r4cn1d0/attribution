"""The engine on the probe model classes (brief multi-family-probe-engine-20261007, Item 1.5), on CPU in float32
with tiny random models (nothing downloaded): an untied ``Olmo2ForCausalLM`` with q_norm/k_norm, and a tied
``LlamaForCausalLM`` with grouped-query attention and llama3 RoPE scaling, each with the seven LoRA targets.
(a) the LoRA count is r * sum(in + out) and no norm trains; (b) with B = 0 the logits equal the plain model's bit
for bit; (c) gradient checkpointing (use_reentrant False, as the loader sets it) gives the same losses and
gradients; (d) greedy decoding of a left-padded batch of 2 equals one prompt at a time."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
peft = pytest.importorskip("peft")

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection.textproc import TrainExample  # noqa: E402

TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
RANK = 4
VOCAB = 300


def olmo2():
    return transformers.Olmo2Config(vocab_size=VOCAB, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                                    num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=256,
                                    tie_word_embeddings=False, attn_implementation="eager", pad_token_id=0,
                                    bos_token_id=1, eos_token_id=1)


def llama3():
    return transformers.LlamaConfig(vocab_size=VOCAB, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                                    num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=256,
                                    tie_word_embeddings=True, attn_implementation="eager", pad_token_id=0,
                                    bos_token_id=1, eos_token_id=1,
                                    rope_scaling={"rope_type": "llama3", "factor": 8.0, "low_freq_factor": 1.0,
                                                  "high_freq_factor": 4.0, "original_max_position_embeddings": 64})


def build(config_fn, cls):
    torch.manual_seed(0)
    plain = getattr(transformers, cls)(config_fn()).float().eval()
    torch.manual_seed(0)
    base = getattr(transformers, cls)(config_fn()).float()
    model = peft.get_peft_model(base, peft.LoraConfig(r=RANK, lora_alpha=2 * RANK, lora_dropout=0.0,
                                                      target_modules=TARGETS, bias="none", task_type="CAUSAL_LM"))
    named = en.lora_parameters(model)
    en.load_lora_state(named, en.init_lora_state(named, 1101))
    return plain, model, named


FAMILIES = [pytest.param(olmo2, "Olmo2ForCausalLM", id="olmo2"), pytest.param(llama3, "LlamaForCausalLM", id="llama3")]


@pytest.mark.parametrize("config_fn, cls", FAMILIES)
def test_the_lora_count_is_rank_times_in_plus_out_and_no_norm_trains(config_fn, cls):
    plain, model, named = build(config_fn, cls)
    expected = sum(RANK * (m.in_features + m.out_features) for name, m in plain.named_modules()
                   if isinstance(m, torch.nn.Linear) and name.rsplit(".", 1)[-1] in TARGETS)
    assert en.parameter_count(named) == expected
    assert not [n for n, _ in named if "norm" in n]
    assert len({n.rsplit(".lora_", 1)[0] for n, _ in named}) == 7 * plain.config.num_hidden_layers
    if cls == "Olmo2ForCausalLM":
        assert any("q_norm" in n for n, _ in plain.named_parameters())         # present, and not a target


@pytest.mark.parametrize("config_fn, cls", FAMILIES)
def test_with_b_zero_the_logits_equal_the_plain_models_bit_for_bit(config_fn, cls):
    plain, model, _ = build(config_fn, cls)
    ids = torch.tensor([[1, 17, 23, 99, 150, 7, 42, 5]])
    with torch.no_grad():
        a = en.causal_lm(model)(input_ids=ids).logits
        b = plain(input_ids=ids).logits
    assert torch.equal(a, b)


@pytest.mark.parametrize("config_fn, cls", FAMILIES)
def test_gradient_checkpointing_gives_the_same_losses_and_gradients(config_fn, cls):
    examples = [TrainExample(f"r{k}", tuple(range(2 + k, 14 + 3 * k)), 4) for k in range(4)]
    results = []
    for checkpointing in (False, True):
        _, model, named = build(config_fn, cls)
        with torch.no_grad():                                                   # a non-zero B
            for n, p in named:
                if ".lora_B." in n:
                    p.normal_(0, 0.02, generator=torch.Generator().manual_seed(3))
        if checkpointing:
            en.causal_lm(model).gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.train()
        model.zero_grad(set_to_none=True)
        losses = en.accumulate_gradients(model, examples, 2, 0, "cpu", 16)
        results.append((losses, [p.grad.detach().clone() for _, p in named]))
    assert results[0][0] == pytest.approx(results[1][0], rel=1e-6)
    for a, b in zip(results[0][1], results[1][1]):
        assert torch.allclose(a, b, rtol=1e-5, atol=1e-7)


@pytest.mark.parametrize("config_fn, cls", FAMILIES)
def test_greedy_decoding_of_a_left_padded_batch_equals_one_prompt_at_a_time(config_fn, cls):
    _, model, named = build(config_fn, cls)
    with torch.no_grad():
        for n, p in named:
            if ".lora_B." in n:
                p.normal_(0, 0.02, generator=torch.Generator().manual_seed(5))
    prompts = [[1, 17, 23, 99], [1, 150, 7, 42, 5, 88, 61]]                 # different lengths: left padding
    options = dict(max_new_tokens=12, stop_ids=[2], pad_id=0, device="cpu")
    together = en.greedy_generate(model, prompts, batch_size=2, **options)
    single = en.greedy_generate(model, prompts, batch_size=1, **options)
    assert together == single and all(len(g.output_ids) > 0 for g in single)
