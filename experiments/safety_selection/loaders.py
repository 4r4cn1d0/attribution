"""The pinned real assets (torch/transformers/peft are imported at call time): the policy
(frozen bfloat16 base, float32 LoRA), the Qwen3Guard response scorer and the optional
secondary toxicity classifier.

Only local snapshot folders of the pinned revisions are read: offline, safetensors, no remote
code, eager attention. No model, dtype or device fallback: the real loaders run only on exactly
one visible CUDA GPU after ``configure_cuda`` (deterministic algorithms that raise, TF32 off);
``cpu`` exists for injected ENGINEERING FIXTURE loaders in tests, never for scientific runs.
Downloads happen only through the explicit ``fetch`` command.

Numerical settings. The reused ``configure_cuda`` fixes TF32 and float32 matmul precision but
neither records nor controls reduced-precision accumulation in bfloat16 GEMMs. This loader
additionally sets ``torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction`` to
False, refuses unless it reads back False, and records it in every run's environment. The
guarantee is limited: it forbids cuBLAS reduced-precision (bfloat16) intermediate reductions in
bfloat16 matmuls only. It does not make bfloat16 computation equal to float32, does not fix
other kernels' internal precision (attention softmax, normalization), and does not give
equality across GPU types, drivers, library versions or batch shapes. Bitwise repeatability
remains a same-GPU, same-software, same-batch-shape property; anything else is tolerance.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable

from experiments.minimal_safety.plan import asset_status

from .common import sha256_bytes
from .ledger import RunLedger
from .scoring import GuardScorer, guard_control_strings
from .textproc import Codec, TemplateError, build_codec

__all__ = ["Policy", "Toxicity", "Loaders", "real_loaders", "load_tokenizer", "snapshot",
           "GUARD_TEMPLATE_END", "BF16_REDUCTION_FLAG", "numeric_flags",
           "forbid_bf16_reduced_precision"]

GUARD_TEMPLATE_END = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
_GUARD_MARKERS = ("Determine if THE LAST ASSISTANT's response is a refusal",
                  "<BEGIN SAFETY POLICY>", "<BEGIN REFUSAL POLICY>")
BF16_REDUCTION_FLAG = "cuda_matmul_allow_bf16_reduced_precision_reduction"
# Target positions per lm_head chunk in guard label-sequence scoring (a fixed code constant).
GUARD_LOGPROB_CHUNK = 1024


@dataclass
class Policy:
    model: Any
    named: list
    codec: Codec
    device: str
    identity: dict


@dataclass
class Toxicity:
    score: Callable[[list[str]], list[float]]
    count_truncated: Callable[[list[str]], int]
    threshold: float
    identity: dict = field(default_factory=dict)


@dataclass
class Loaders:
    """Injected asset access: the real pinned assets, or ENGINEERING FIXTURES in tests."""

    prepare_device: Callable[[dict], str]
    hooks: Callable[[str], tuple[Callable[[], None], Callable[[], dict]]]
    environment: Callable[[str], dict]
    policy: Callable[[dict, RunLedger], Policy]
    guard: Callable[[dict, RunLedger, str], GuardScorer]
    toxicity: Callable[[dict, RunLedger], Toxicity | None]


def _offline() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"


def snapshot(repo_id: str, revision: str) -> dict:
    status = asset_status(repo_id, revision)
    if not status["present"] or not status["safetensors"]:
        raise FileNotFoundError(f"{repo_id}@{revision}: no cached snapshot with safetensors "
                                f"weights at {status['snapshot']} (use the explicit fetch command)")
    return status


def load_tokenizer(repo_id: str, revision: str) -> tuple[Any, dict]:
    _offline()
    from transformers import AutoTokenizer

    status = asset_status(repo_id, revision)
    if not status["present"]:
        raise FileNotFoundError(f"{repo_id}@{revision}: no cached snapshot at {status['snapshot']}")
    tokenizer = AutoTokenizer.from_pretrained(status["snapshot"], local_files_only=True,
                                              trust_remote_code=False)
    return tokenizer, status


def numeric_flags() -> dict:
    """Numerical settings this package adds to the minimal-safety environment record."""
    import torch

    value = torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction
    return {BF16_REDUCTION_FLAG: value if isinstance(value, bool) else repr(value)}


def forbid_bf16_reduced_precision() -> dict:
    """Set the bfloat16 reduced-precision reduction flag to False and refuse unless it reads
    back False (see the module docstring for what this does and does not guarantee)."""
    import torch

    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    flags = numeric_flags()
    if flags[BF16_REDUCTION_FLAG] is not False:
        raise RuntimeError(f"{BF16_REDUCTION_FLAG} reads back {flags[BF16_REDUCTION_FLAG]!r}, not False")
    return flags


def _prepare_cuda(recipe: dict) -> str:
    from experiments.minimal_safety.model import configure_cuda

    if recipe["model"]["device"] != "cuda":
        raise RuntimeError("the real loaders run only on CUDA; 'cpu' is for engineering "
                           "fixtures, never a scientific fallback")
    configure_cuda()  # before any CUDA use; refuses an unsuitable environment
    forbid_bf16_reduced_precision()
    return "cuda"


def _hooks(device: str):
    from experiments.minimal_safety.model import device_hooks

    return device_hooks(device)


def _environment(device: str) -> dict:
    from experiments.minimal_safety.model import environment

    return {**environment(device), "safety_selection_numeric": numeric_flags()}


def _load_policy(recipe: dict, ledger: RunLedger) -> Policy:
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM

    from .engine import causal_lm, lora_parameters, parameter_count

    from .config import tokenizer_of

    spec, lora = recipe["model"], recipe["model"]["lora"]
    with ledger.stage("load_policy") as info:
        tokenizer, tokenizer_status = load_tokenizer(*tokenizer_of(recipe))
        status = snapshot(spec["repo_id"], spec["revision"])
        ledger.check("policy weights")
        base = AutoModelForCausalLM.from_pretrained(
            status["snapshot"], torch_dtype=torch.bfloat16, use_safetensors=True,
            attn_implementation=spec["attn_implementation"], local_files_only=True,
            trust_remote_code=False)
        if type(base).__name__ != spec["architecture"]:
            raise RuntimeError(f"loaded {type(base).__name__}, recipe expects {spec['architecture']}")
        if {p.dtype for p in base.parameters()} != {torch.bfloat16}:
            raise RuntimeError("base weights did not load as bfloat16")
        attention = getattr(base.config, "_attn_implementation", None)
        if attention != spec["attn_implementation"]:
            raise RuntimeError(f"attention implementation is {attention!r}")
        model = get_peft_model(base, LoraConfig(
            r=lora["r"], lora_alpha=lora["alpha"], lora_dropout=lora["dropout"],
            target_modules=list(lora["target_modules"]), bias="none", task_type="CAUSAL_LM"))
        model.to("cuda")
        named = lora_parameters(model)
        count = parameter_count(named)
        if count != lora["expected_trainable_parameters"]:
            raise RuntimeError(f"{count} trainable LoRA parameters, recipe expects "
                               f"{lora['expected_trainable_parameters']}")
        if {p.dtype for _, p in named} != {torch.float32}:
            raise RuntimeError("LoRA parameters must be float32 (PEFT adapter autocast)")
        if {p.dtype for _, p in model.named_parameters() if not p.requires_grad} != {torch.bfloat16}:
            raise RuntimeError("every frozen base weight must be bfloat16")
        if recipe["train"]["gradient_checkpointing"]:
            causal_lm(model).gradient_checkpointing_enable(
                gradient_checkpointing_kwargs={"use_reentrant": False})
        codec = build_codec(tokenizer, spec["end_of_turn_token"], spec["stop_tokens"], spec["pad_token"])
        probe = codec.decode(codec.prompt_ids("<<probe>>"))
        if not (probe.endswith("<|im_start|>assistant\n") and "<<probe>>" in probe):
            raise TemplateError("policy chat template does not end with the assistant header")
        template = getattr(tokenizer, "chat_template", None) or ""
        info.update(trainable_parameters=count, attn_implementation=attention)
    identity = {**status, "trainable_parameters": count, "attn_implementation": attention,
                **({"tokenizer_snapshot": tokenizer_status} if "tokenizer" in spec else {}),
                "chat_template_sha256": sha256_bytes(template.encode("utf-8")),
                "template_probe": probe, "eos_id": codec.eos_id, "stop_ids": list(codec.stop_ids),
                "pad_id": codec.pad_id, "gradient_checkpointing": recipe["train"]["gradient_checkpointing"]}
    return Policy(model, named, codec, "cuda", identity)


def _load_guard(recipe: dict, ledger: RunLedger, device: str) -> GuardScorer:
    import torch
    from transformers import AutoModelForCausalLM

    from .engine import greedy_generate, target_logprobs

    spec = recipe["guard"]
    with ledger.stage("load_guard") as info:
        tokenizer, status = load_tokenizer(spec["repo_id"], spec["revision"])
        snapshot(spec["repo_id"], spec["revision"])
        probe = tokenizer.apply_chat_template(
            [{"role": "user", "content": "<<U>>"}, {"role": "assistant", "content": "<<A>>"}],
            tokenize=False)
        if not (probe.endswith(GUARD_TEMPLATE_END) and "USER: <<U>>\n\nASSISTANT: <<A>>" in probe
                and all(marker in probe for marker in _GUARD_MARKERS)):
            raise TemplateError("guard chat template is not the pinned response-moderation template")
        ledger.check("guard weights")
        model = AutoModelForCausalLM.from_pretrained(
            status["snapshot"], torch_dtype=torch.bfloat16, use_safetensors=True,
            attn_implementation=spec["attn_implementation"], local_files_only=True,
            trust_remote_code=False)
        if type(model).__name__ != spec["architecture"]:
            raise RuntimeError(f"loaded {type(model).__name__}, recipe expects {spec['architecture']}")
        if {p.dtype for p in model.parameters()} != {torch.bfloat16}:
            raise RuntimeError("guard weights did not load as bfloat16")
        model.requires_grad_(False)
        model.eval().to(device)
        codec = build_codec(tokenizer, spec["stop_tokens"][0], spec["stop_tokens"], spec["pad_token"])
        info.update(parameters=sum(p.numel() for p in model.parameters()))
    template = getattr(tokenizer, "chat_template", None) or ""
    identity = {**status, "chat_template_sha256": sha256_bytes(template.encode("utf-8")),
                "stop_ids": list(codec.stop_ids), "pad_id": codec.pad_id}

    def generate(prompts: list[list[int]], check: Callable[[str], None] | None = None) -> list:
        return greedy_generate(model, prompts, max_new_tokens=spec["max_new_tokens"],
                               stop_ids=codec.stop_ids, pad_id=codec.pad_id, device=device,
                               batch_size=spec["batch_size"], check=check)

    def logprobs(sequences: list[list[int]], n_targets: list[int],
                 check: Callable[[str], None] | None = None) -> list[list[float]]:
        return target_logprobs(model, sequences, n_targets, pad_id=codec.pad_id, device=device,
                               batch_size=spec["batch_size"], chunk=GUARD_LOGPROB_CHUNK, check=check)

    return GuardScorer(tokenizer, generate, spec["max_input_tokens"],
                       guard_control_strings(tokenizer), identity, logprobs)


def _load_toxicity(recipe: dict, ledger: RunLedger) -> Toxicity | None:
    spec = recipe["secondary_toxicity"]
    if spec is None:
        return None
    import torch
    from transformers import AutoModelForSequenceClassification

    from experiments.minimal_safety.model import make_scorer

    with ledger.stage("load_secondary_toxicity") as info:
        tokenizer, status = load_tokenizer(spec["repo_id"], spec["revision"])
        snapshot(spec["repo_id"], spec["revision"])
        model = AutoModelForSequenceClassification.from_pretrained(
            status["snapshot"], torch_dtype=torch.float32, use_safetensors=True,
            local_files_only=True, trust_remote_code=False).eval().to("cpu")
        labels = {int(k): v for k, v in model.config.id2label.items()}
        index = [k for k, v in labels.items() if v == spec["label"]]
        if len(index) != 1:
            raise RuntimeError(f"label {spec['label']!r} not unique in {labels}")
        score, count_truncated = make_scorer(tokenizer, model, index[0], spec["max_length"],
                                             spec["batch_size"], "cpu")
        info.update(label_index=index[0])
    return Toxicity(score, count_truncated, spec["threshold"],
                    {**status, "labels": labels, "label_index": index[0], "activation": "sigmoid"})


def real_loaders() -> Loaders:
    return Loaders(prepare_device=_prepare_cuda, hooks=_hooks, environment=_environment,
                   policy=_load_policy, guard=_load_guard, toxicity=_load_toxicity)
