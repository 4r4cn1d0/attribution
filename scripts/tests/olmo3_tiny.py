"""A tiny random ``Olmo3ForCausalLM`` for CPU tests (track O3A-env-preflight, 4 Nov 2026; nothing downloaded).

The config is OLMo 3 7B Instruct's ``config.json`` (allenai/Olmo-3-7B-Instruct at 6e5971d9; the fields are copied
here as constants) scaled down: hidden 4,096 -> 32, MLP 11,008 -> 64, 32 layers -> the real pattern's first four
(three sliding, one full), 32 heads -> 4, positions 65,536 -> 256 (YaRN's original length 8,192 -> 32, the same factor
8). Everything else is kept: the 100,278-row vocabulary (so the real tokenizer's ids, the seven unused
``<|extra_id_N|>`` rows included, address real rows), the sliding window of 4,096, the YaRN fields, the untied head,
the norm epsilon and the token ids. ``test_the_tiny_config_is_the_scaled_down_real_config`` checks this against the
cached ``config.json`` when the snapshot is on the machine.

    config = tiny_config_dict()            # a dict, written as config.json where a script needs a folder
    plain, model, named = build(seed)      # the plain model, the engine-wrapped LoRA model and its named parameters
"""

from __future__ import annotations

import json
import os
from pathlib import Path

SNAPSHOT = Path(os.path.expanduser("~/.cache/huggingface/hub/models--allenai--Olmo-3-7B-Instruct/snapshots/"
                                   "6e5971d9eba42665f5bd5a0fcf047f299ce1dccc"))
TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
RANK = 4
VOCAB = 100278
SCALED = {"hidden_size": 32, "intermediate_size": 64, "num_hidden_layers": 4, "num_attention_heads": 4,
          "num_key_value_heads": 4, "max_position_embeddings": 256}
REAL_SIZES = {"hidden_size": 4096, "intermediate_size": 11008, "num_hidden_layers": 32, "num_attention_heads": 32,
              "num_key_value_heads": 32, "max_position_embeddings": 65536}
REAL_ORIGINAL_POSITIONS = 8192
TINY_ORIGINAL_POSITIONS = 32


def tiny_config_dict() -> dict:
    """The scaled-down config as a dict (the module doc); ``attn_implementation`` eager for the CPU."""
    return {
        "architectures": ["Olmo3ForCausalLM"],
        "attention_bias": False,
        "attention_dropout": 0.0,
        "dtype": "bfloat16",
        "eos_token_id": 100257,
        "hidden_act": "silu",
        "initializer_range": 0.02,
        "layer_types": ["sliding_attention", "sliding_attention", "sliding_attention", "full_attention"],
        "model_type": "olmo3",
        "pad_token_id": 100277,
        "rms_norm_eps": 1e-06,
        "rope_scaling": {"attention_factor": 1.2079441541679836, "beta_fast": 32.0, "beta_slow": 1.0, "factor": 8.0,
                         "original_max_position_embeddings": TINY_ORIGINAL_POSITIONS, "rope_type": "yarn"},
        "rope_theta": 500000,
        "sliding_window": 4096,
        "tie_word_embeddings": False,
        "transformers_version": "4.57.1",
        "use_cache": False,
        "vocab_size": VOCAB,
        **SCALED,
    }


def scaled_down(real: dict) -> dict:
    """The real ``config.json`` dict scaled as the module doc says (the check against the cache)."""
    out = dict(real)
    out.update(SCALED)
    out["layer_types"] = real["layer_types"][:SCALED["num_hidden_layers"]]
    out["rope_scaling"] = dict(real["rope_scaling"], original_max_position_embeddings=TINY_ORIGINAL_POSITIONS)
    return out


def write_config(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "config.json"
    path.write_text(json.dumps(tiny_config_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def has_olmo3() -> bool:
    import transformers

    return hasattr(transformers, "Olmo3ForCausalLM")


def config():
    import transformers

    return transformers.Olmo3Config(**tiny_config_dict(), attn_implementation="eager")


def plain_model(seed: int = 0):
    """The plain tiny model, float32, random weights at ``seed``, eval mode."""
    import torch
    import transformers

    torch.manual_seed(seed)
    return transformers.Olmo3ForCausalLM(config()).float().eval()


def build(seed: int = 0, rank: int = RANK):
    """(plain, model, named): a plain copy and the same weights under the engine's LoRA wrapping (the seven targets,
    the loader's LoraConfig fields, the engine's seeded adapter initialisation at seed 1101), as
    experiments/safety_selection/tests/test_ss_family_models.py builds its OLMo-2 and Llama-3 cases."""
    import peft
    import torch
    import transformers

    from experiments.safety_selection import engine as en

    plain = plain_model(seed)
    torch.manual_seed(seed)
    base = transformers.Olmo3ForCausalLM(config()).float()
    model = peft.get_peft_model(base, peft.LoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=0.0, target_modules=TARGETS,
                                                      bias="none", task_type="CAUSAL_LM"))
    named = en.lora_parameters(model)
    en.load_lora_state(named, en.init_lora_state(named, 1101))
    return plain, model, named
