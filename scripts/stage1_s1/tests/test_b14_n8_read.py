"""N-8 (addendum section 11 point 12): B14's embedding vector equals REQ-3's read (d) at hidden-state index 16, byte for
byte, on a tiny random 16-block OLMo-2 built locally (ENGINEERING FIXTURE, CPU; nothing is downloaded).

B14 (scripts/stage1_s1/overlap_similarity.py) embeds an added row's prompt alone (its generation-prompt ids) and
reads the hidden state at the pinned index (16 = model.norm of the last block's output, L4) at the last prompt
position. REQ-3 (scripts/stage1/representation_pass.py, imported read-only) runs the whole training row (prompt,
response, end of turn) and reads (d) at position n_prompt - 1. Under causal masking the two are the same state; this
test checks that the two scripts' own functions give the same float64 bytes. The real OLMo-2-1B and CUDA are
UNTESTED (a CUDA kernel may order sums by sequence length; the pod pass records which read it used)."""

from __future__ import annotations

import json

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
peft = pytest.importorskip("peft")

import b14_fixtures as bf  # noqa: E402
import ss_fixtures as fx  # noqa: E402

from experiments.safety_selection.textproc import encode_train  # noqa: E402
from scripts.stage1 import representation_pass as rp  # noqa: E402
from scripts.stage1_s1 import overlap_similarity as sim  # noqa: E402


def _embedding() -> dict:
    return json.loads(sim.SETTINGS_PATH.read_bytes())["embedding"]


def tiny_olmo2_16(attn: str):
    """A tiny random OLMo-2 with the real model's 16 blocks (so the pinned index 16 is the final-norm output), with a
    non-zero rank-2 LoRA that both passes disable."""
    torch.manual_seed(5)
    config = transformers.Olmo2Config(vocab_size=260, hidden_size=32, intermediate_size=64, num_hidden_layers=16,
                                      num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=512,
                                      tie_word_embeddings=False, attn_implementation=attn, pad_token_id=258,
                                      bos_token_id=None, eos_token_id=257)
    model = peft.get_peft_model(transformers.Olmo2ForCausalLM(config).float(),
                                peft.LoraConfig(r=2, lora_alpha=4, lora_dropout=0.0, bias="none",
                                                target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"))
    with torch.no_grad():
        for name, param in model.named_parameters():
            if ".lora_B." in name:
                param.copy_(0.5 * torch.randn(param.shape))
    model.eval()
    return model


def test_the_pinned_index_is_req3s_final_block_output_index():
    emb = _embedding()
    assert (emb["hidden_state_index"], emb["n_layers"], emb["read"]) == (16, 16, sim.READ)
    assert rp.block_output_index(emb["n_layers"] - 1, emb["n_layers"]) == emb["hidden_state_index"]


@pytest.mark.parametrize("attn", ["eager", "sdpa"])
def test_b14s_vector_equals_req3s_read_d_at_index_16_byte_for_byte(attn):
    emb = _embedding()
    index, n_layers = emb["hidden_state_index"], emb["n_layers"]
    model = tiny_olmo2_16(attn)
    assert sim.layout(model)["n_layers"] == n_layers == rp.layout(model)["n_layers"]
    codec, recipe = fx.fixture_codec(), fx.recipe()
    max_train = recipe["model"]["max_train_tokens"]
    compared = 0
    for i in range(6):
        row_id, prompt, response = f"n8-{i}", bf.add_prompt(i), bf.add_response(i) * (1 + i % 3)
        prompt_ids = sim.encode_added(codec, row_id, prompt, response, recipe)
        example = encode_train(codec, row_id, prompt, response, max_train)
        assert list(example.input_ids[:example.n_prompt]) == list(prompt_ids)
        assert rp.positions(example.input_ids, example.n_prompt, codec.eos_id)["d"] == len(prompt_ids) - 1
        with torch.no_grad(), model.disable_adapter():
            b14 = sim.prompt_vector(model, prompt_ids, index, n_layers, "cpu")
            req3 = rp.read_states(model, example.input_ids, example.n_prompt, codec.eos_id, "cpu", n_layers)[index]["d"]
        assert b14.dtype == req3.dtype == torch.float64 and tuple(b14.shape) == tuple(req3.shape) == (32,)
        assert b14.numpy().tobytes() == req3.numpy().tobytes()
        compared += 1
    with torch.no_grad():                                               # the LoRA is live: disabling it matters
        live = sim.prompt_vector(model, prompt_ids, index, n_layers, "cpu")
    assert not torch.equal(live, b14)
    assert compared == 6
