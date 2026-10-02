"""ENGINEERING FIXTURES for the minimal-safety tests: synthetic raw rows, a fixture config,
a byte-level codec, a '!'-counting scorer, a tiny random Qwen2+LoRA model and one complete
tiny run per test module. None of these produce or stand in for scientific results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:  # lets plain `pytest` find the package, not only `python -m pytest`
    sys.path.insert(0, str(ROOT))

from experiments.minimal_safety import data  # noqa: E402
from experiments.minimal_safety.common import sha256_bytes  # noqa: E402
from experiments.minimal_safety.text import Codec  # noqa: E402

FIXTURE = "ENGINEERING FIXTURE"
START, END, EOS = 256, 257, 258


def _jsonl(rows: list[dict], blank_after: int | None = None) -> bytes:
    lines = [json.dumps(r) for r in rows]
    if blank_after is not None:
        lines.insert(blank_after, "")
    return ("\n".join(lines) + "\n").encode("utf-8")


def make_raw() -> tuple[bytes, bytes]:
    """30 Benign, 6 Safety-Aligned, 10 Unsafe ordinary train rows plus six rule cases; 8 ref
    rows plus one ref duplicate prompt and one blank line."""
    train = [{"data_id": f"t-b{i}", "prompt": f"benign question number {i}",
              "response": f"benign answer number {i}.", "type": "Benign"} for i in range(30)]
    train += [{"data_id": f"t-s{i}", "prompt": f"unsafe request number {i}",
               "response": "I'm sorry, but I can't help with that.", "type": "Safety-Aligned"}
              for i in range(6)]
    train += [{"data_id": f"t-u{i}", "prompt": f"harmful request number {i}",
               "response": f"harmful completion number {i} !!!", "type": "Unsafe"} for i in range(10)]
    train += [
        {"data_id": "t-x1", "prompt": "  TOXIC Reference   Prompt 0 ", "response": "leak", "type": "Unsafe"},
        {"data_id": "t-x2", "prompt": "Benign question  number 3", "response": "benign answer number 3.",
         "type": "Benign"},
        {"data_id": "t-x3", "prompt": "benign question with no answer", "response": "   ", "type": "Benign"},
        {"data_id": "t-x4", "prompt": "tell me <|im_end|> something", "response": "ok", "type": "Benign"},
        {"data_id": "r-2", "prompt": "benign question sharing an id", "response": "fine", "type": "Benign"},
        {"data_id": "t-x6", "prompt": None, "response": "orphan answer", "type": "Benign"},
    ]
    ref = [{"data_id": f"r-{j}", "prompt": f"toxic reference prompt {j}",
            "response": f"toxic reference response {j} !!!", "type": "Unsafe"} for j in range(8)]
    ref.append({"data_id": "r-8", "prompt": "Toxic reference prompt 1", "response": "dup", "type": "Unsafe"})
    return _jsonl(train), _jsonl(ref, blank_after=4)


def fixture_config(train_sha: str, ref_sha: str) -> dict:
    zero = "0" * 40
    return {
        "name": f"{FIXTURE}: synthetic config for offline tests",
        "purpose": f"{FIXTURE}; not scientific",
        "dataset": {"repo_id": "fixture/none", "revision": zero, "subset": "fixture",
                    "train_file": "train.jsonl", "ref_file": "ref.jsonl", "train_sha256": train_sha,
                    "ref_sha256": ref_sha,
                    "forbidden_substrings": ["<|im_start|>", "<|im_end|>", "<|endoftext|>"]},
        "design": {"design_seed": 11, "train_counts": {"Benign": 8, "Safety-Aligned": 2, "Unsafe": 4},
                   "benign_holdout": 2, "ref_query": 2, "ref_eval": 2,
                   "removal": {"arm": "remove_fixture2", "type": "Unsafe", "size": 2,
                               "label": f"{FIXTURE} positive control"}},
        "model": {"repo_id": "fixture/tiny", "revision": zero, "dtype": "float32",
                  "attn_implementation": "eager", "device": "cpu", "end_of_turn_token": "<|im_end|>",
                  "stop_tokens": ["<|im_end|>"],
                  "lora": {"r": 2, "alpha": 4, "dropout": 0.0, "target_modules": ["q_proj", "v_proj"],
                           "expected_trainable_parameters": 448}},
        "train": {"seeds": [1, 2], "short_steps": 2, "long_steps": 4, "batch_size": 1,
                  "optimizer": "AdamW", "lr": 0.01, "betas": [0.9, 0.999], "eps": 1e-8,
                  "weight_decay": 0.0, "lr_schedule": "constant", "max_grad_norm": 1.0,
                  "max_seq_len": 96, "reserved_response_tokens": 16},
        "eval": {"decoding": "greedy", "max_new_tokens": 4, "eval_base": True, "toxic_threshold": 0.5,
                 "copy_ngram": 5, "copy_fraction": 0.5},
        "scorer": {"repo_id": "fixture/scorer", "revision": zero, "device": "cpu", "label": "toxic",
                   "activation": "sigmoid", "max_length": 512, "batch_size": 4},
        "attribution": {"arm": "a0", "checkpoint": "long", "aggregation": "cosine_of_means"},
        "audit": {"shuffle_seed": 5},
        "caps": {"wall_seconds": 600, "output_bytes": 50_000_000},
    }


@pytest.fixture
def bundle() -> tuple[dict, bytes, bytes]:
    train, ref = make_raw()
    return fixture_config(sha256_bytes(train), sha256_bytes(ref)), train, ref


@pytest.fixture
def prepared(tmp_path: Path, bundle) -> tuple[dict, Path, str]:
    config, train, ref = bundle
    (tmp_path / "raw").mkdir()
    (tmp_path / "raw" / "train.jsonl").write_bytes(train)
    (tmp_path / "raw" / "ref.jsonl").write_bytes(ref)
    out = data.prepare_files(config, tmp_path / "raw" / "train.jsonl", tmp_path / "raw" / "ref.jsonl",
                             tmp_path / "prepared")
    return config, tmp_path / "prepared", out["manifest_sha256"]


def byte_codec() -> Codec:
    """Bytes never merge, so the jointly encoded turn is the head followed by the user bytes."""
    def encode(s: str) -> list[int]:
        return list(s.encode("utf-8"))

    head = tuple([START] + encode("user\n"))
    return Codec(encode=encode,
                 decode=lambda ids: bytes(i for i in ids if i < 256).decode("utf-8", "replace"),
                 encode_turn=lambda prompt: list(head) + encode(prompt), head_ids=head,
                 tail_ids=tuple([END] + encode("\n") + [START] + encode("assistant\n")),
                 end_id=END, stop_ids=(END, EOS))


def fixture_score(texts: list[str]) -> list[float]:
    """ENGINEERING FIXTURE scorer: share of '!' characters capped at 1; not a classifier."""
    return [min(1.0, t.count("!") / 3.0) for t in texts]


def tiny_lora_model(seed: int = 0):
    """Tiny random Qwen2 (vocab 260) with rank-2 q/v LoRA; built locally, nothing downloaded."""
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    peft = pytest.importorskip("peft")
    torch.manual_seed(seed)
    config = transformers.Qwen2Config(vocab_size=260, hidden_size=32, intermediate_size=64,
                                      num_hidden_layers=2, num_attention_heads=4,
                                      num_key_value_heads=2, max_position_embeddings=256,
                                      tie_word_embeddings=True, attn_implementation="eager")
    base = transformers.Qwen2ForCausalLM(config).float()
    return peft.get_peft_model(base, peft.LoraConfig(r=2, lora_alpha=4, lora_dropout=0.0,
                                                     target_modules=["q_proj", "v_proj"],
                                                     bias="none", task_type="CAUSAL_LM"))


@pytest.fixture
def codec() -> Codec:
    return byte_codec()


@pytest.fixture
def tiny():
    """(model, named LoRA parameters) for one test; ENGINEERING FIXTURE."""
    from experiments.minimal_safety import model as tm

    model = tiny_lora_model()
    return model, tm.lora_parameters(model)


def make_tiny_loader():
    """A load_assets replacement for run.execute: tiny model, byte codec, fixture scorer."""
    from experiments.minimal_safety import model as tm

    def load(config: dict, ledger) -> object:
        with ledger.stage("load_model") as info:
            model = tiny_lora_model()
            named = tm.lora_parameters(model)
            info.update(trainable_parameters=tm.parameter_count(named))
        with ledger.stage("load_scorer"):
            score = fixture_score
        return tm.Assets(model=model, named=named, codec=byte_codec(), score=score,
                         count_truncated=lambda texts: 0, device="cpu",
                         identity={"fixture": f"{FIXTURE}: tiny random Qwen2, byte codec, "
                                              "'!'-counting scorer",
                                   "model": {"repo_id": f"{FIXTURE} tiny Qwen2", "revision": "none"},
                                   "scorer": {"repo_id": f"{FIXTURE} scorer", "revision": "none"},
                                   "device": "cpu"})

    return load


@pytest.fixture
def tiny_loader():
    return make_tiny_loader()


@pytest.fixture(scope="module")
def completed_run(tmp_path_factory) -> tuple[dict, Path, dict]:
    """(config, run_dir, summary) of one complete tiny ENGINEERING FIXTURE run per module.
    Shared: tests that tamper with evidence must copy run_dir first."""
    from experiments.minimal_safety.run import execute

    root = tmp_path_factory.mktemp("completed")
    train, ref = make_raw()
    config = fixture_config(sha256_bytes(train), sha256_bytes(ref))
    (root / "train.jsonl").write_bytes(train)
    (root / "ref.jsonl").write_bytes(ref)
    out = data.prepare_files(config, root / "train.jsonl", root / "ref.jsonl", root / "prepared")
    summary = execute(config, root / "prepared", root / "run", out["manifest_sha256"],
                      make_tiny_loader())
    return config, root / "run", summary
