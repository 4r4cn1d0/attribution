"""The adapter scale on the stage-1 model class, with the stage-1 dtype layout (a bfloat16 base and float32 LoRA on the
seven modules), on a tiny random Olmo2ForCausalLM built from a config on CPU (nothing downloaded): lambda = 0 gives
the plain bfloat16 model's logits bit for bit; lambda = 0.5 halves every module's update s * B * A exactly; lambda = 1
changes no byte. ENGINEERING FIXTURE only."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
peft = pytest.importorskip("peft")

from experiments.safety_selection import engine as en  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402

TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
RANK = 4


def config():
    return transformers.Olmo2Config(vocab_size=300, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                                    num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=256,
                                    tie_word_embeddings=False, attn_implementation="eager", pad_token_id=0,
                                    bos_token_id=1, eos_token_id=1)


def build():
    torch.manual_seed(0)
    plain = transformers.Olmo2ForCausalLM(config()).to(torch.bfloat16).eval()
    torch.manual_seed(0)
    base = transformers.Olmo2ForCausalLM(config()).to(torch.bfloat16)
    model = peft.get_peft_model(base, peft.LoraConfig(r=RANK, lora_alpha=2 * RANK, lora_dropout=0.0,
                                                      target_modules=TARGETS, bias="none", task_type="CAUSAL_LM"))
    named = en.lora_parameters(model)
    generator = torch.Generator().manual_seed(7)
    with torch.no_grad():                                         # a "trained" adapter: B no longer zero
        for _, param in named:
            param.copy_(torch.randn(param.shape, generator=generator) * 0.05)
    return plain, model.eval(), named


def logits(model, ids):
    with torch.no_grad():
        return en.causal_lm(model)(input_ids=ids).logits


def test_the_stage1_layout_is_a_bfloat16_base_with_float32_lora_on_seven_modules():
    _, model, named = build()
    assert {p.dtype for _, p in named} == {torch.float32}
    assert {p.dtype for _, p in model.named_parameters() if not p.requires_grad} == {torch.bfloat16}
    assert len({n.rsplit(".lora_", 1)[0] for n, _ in named}) == 7 * 2


def test_lambda_zero_gives_the_plain_bfloat16_models_logits_bit_for_bit():
    plain, model, named = build()
    ids = torch.tensor([[1, 17, 23, 99, 150, 7, 42, 5]])
    assert not torch.equal(logits(model, ids), logits(plain, ids))                  # the adapter acts
    source = {n: p.detach().clone() for n, p in named}
    zero, _ = ea.scale_adapter(source, 0.0)
    en.load_lora_state(named, zero)
    assert torch.equal(logits(model, ids), logits(plain, ids))


def test_lambda_half_halves_every_update_exactly_and_lambda_one_changes_nothing():
    _, model, named = build()
    source = {n: p.detach().clone() for n, p in named}
    half, record = ea.scale_adapter(source, 0.5)
    assert record["lora_b_matrices"] == 14
    for name in (n for n in source if ".lora_B." in n):
        a = source[name.replace(".lora_B.", ".lora_A.")]
        assert torch.equal(half[name] @ a, 0.5 * (source[name] @ a))
    one, _ = ea.scale_adapter(source, 1.0)
    assert ea.adapter_fingerprint(one) == ea.adapter_fingerprint(source)
    en.load_lora_state(named, half)
    assert en.lora_fingerprint(named) == ea.adapter_fingerprint(half) != ea.adapter_fingerprint(source)
