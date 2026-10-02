"""Torch side: the explicit LoRA parameter vector, seeded initialization, response-only loss,
one optimizer step, greedy decoding, the gradient cosine, checkpoint IO and loading of the
pinned local assets. Imported only by the runner and the torch tests.

LoRA initialization does not use the global RNG: ``lora_A`` is drawn from a CPU generator
seeded by the training seed with PEFT's default bound (kaiming-uniform with a=sqrt(5), i.e.
U(-1/sqrt(fan_in), 1/sqrt(fan_in))) and ``lora_B`` is zero, so the initial adapter is a no-op
and is bit-identical for every arm of a seed on any device.

On CUDA (exactly one visible GPU) ``configure_cuda`` runs before any CUDA use: it refuses an
unsuitable environment, then sets float32 matmuls without TF32 and deterministic algorithms that
raise rather than warn. Bitwise repeatability is a same-GPU, same-software property; no
numerical equality with MPS or CPU is implied.
"""

from __future__ import annotations

import contextlib
import hashlib
import math
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence

import torch
import torch.nn.functional as F

from .common import derive_seed, sha256_file
from .ledger import Ledger, peak_rss_bytes
from .plan import asset_status
from .text import Codec, Example, NoTargets

Named = list[tuple[str, torch.nn.Parameter]]

# Reported under "definition", never "kind": run records use "kind" for the record type.
COSINE_DEFINITION = ("cosine between the mean LoRA gradient of response-only losses on the "
                     "provided toxic query responses and the mean over the removal group's "
                     "training examples; noncausal descriptive diagnostic, not SOURCE, LESS, an "
                     "influence function or a removal-effect prediction")
COSINE_SIGN = ("positive: a small gradient-descent step on the group's mean loss would, to first "
               "order, also lower the query responses' loss (the group locally supports them)")

# Values of CUBLAS_WORKSPACE_CONFIG under which cuBLAS is deterministic (CUDA >= 10.2).
DETERMINISTIC_CUBLAS = (":4096:8", ":16:8")
# The CUDA profile's process-wide flags: float32 without TF32, deterministic kernels or an error.
CUDA_SETTINGS = {"deterministic_algorithms": True, "deterministic_warn_only": False,
                 "cudnn_deterministic": True, "cudnn_benchmark": False,
                 "cuda_matmul_allow_tf32": False, "cudnn_allow_tf32": False,
                 "float32_matmul_precision": "highest"}
# Recorded with the CUDA environment: variables that can change kernels, precision or timing.
CUDA_ENV = ("CUBLAS_WORKSPACE_CONFIG", "CUDA_VISIBLE_DEVICES", "TORCH_ALLOW_TF32_CUBLAS_OVERRIDE",
            "NVIDIA_TF32_OVERRIDE", "TORCH_BLAS_PREFER_CUBLASLT", "CUDA_LAUNCH_BLOCKING",
            "PYTORCH_CUDA_ALLOC_CONF")


class NonFiniteError(FloatingPointError):
    pass


class ZeroGradientError(ValueError):
    pass


def lora_parameters(model: torch.nn.Module) -> Named:
    """Trainable parameters sorted by name; all and only LoRA A/B matrices."""
    named = sorted(((n, p) for n, p in model.named_parameters() if p.requires_grad),
                   key=lambda item: item[0])
    if not named:
        raise ValueError("model has no trainable parameters")
    other = [n for n, _ in named if ".lora_A." not in n and ".lora_B." not in n]
    if other:
        raise ValueError(f"trainable parameters outside LoRA: {other[:3]}")
    frozen = [n for n, p in model.named_parameters()
              if (".lora_A." in n or ".lora_B." in n) and not p.requires_grad]
    if frozen:
        raise ValueError(f"frozen LoRA parameters: {frozen[:3]}")
    return named


def parameter_count(named: Named) -> int:
    return sum(p.numel() for _, p in named)


def init_lora_state(named: Named, seed: int) -> dict[str, torch.Tensor]:
    generator = torch.Generator(device="cpu").manual_seed(derive_seed(seed, "lora-init"))
    state = {}
    for name, param in named:
        if ".lora_A." in name:
            bound = 1.0 / math.sqrt(param.shape[1])
            state[name] = (torch.rand(param.shape, generator=generator, dtype=torch.float32)
                           * 2.0 - 1.0) * bound
        else:
            state[name] = torch.zeros(param.shape, dtype=torch.float32)
    return state


def load_lora_state(named: Named, state: dict[str, torch.Tensor]) -> None:
    if sorted(state) != [n for n, _ in named]:
        raise ValueError("adapter state names differ from the model's LoRA parameters")
    with torch.no_grad():
        for name, param in named:
            source = state[name]
            if tuple(source.shape) != tuple(param.shape):
                raise ValueError(f"{name}: shape {tuple(source.shape)} != {tuple(param.shape)}")
            param.copy_(source.to(device=param.device, dtype=param.dtype))


def lora_fingerprint(named: Named) -> str:
    """SHA-256 over names, shapes and exact float32 bytes of the adapter."""
    digest = hashlib.sha256()
    for name, param in named:
        tensor = param.detach().to("cpu").contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def save_lora(named: Named, path: str | Path, metadata: dict[str, object]) -> str:
    from safetensors.torch import save_file

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    save_file({n: p.detach().to("cpu").contiguous() for n, p in named}, str(path),
              metadata={k: str(v) for k, v in metadata.items()})
    return sha256_file(path)


def read_lora(path: str | Path) -> dict[str, torch.Tensor]:
    from safetensors.torch import load_file

    return load_file(str(path), device="cpu")


def adapter_difference(first: str | Path, second: str | Path) -> dict:
    """Exact comparison of two saved adapters from their tensors. File hashes cannot show
    equality (the metadata names the arm); these fingerprints have the ``lora_fingerprint``
    definition, so they are directly comparable with the checkpoint records'."""
    a, b = (sorted(read_lora(path).items()) for path in (first, second))
    fingerprints = [lora_fingerprint(a), lora_fingerprint(b)]
    layout = [[(name, tuple(t.shape)) for name, t in items] for items in (a, b)]
    return {"fingerprints": fingerprints, "bitwise_identical": fingerprints[0] == fingerprints[1],
            "max_abs_difference": max(float((x - y).abs().max()) for (_, x), (_, y) in zip(a, b))
            if layout[0] == layout[1] else None}


def response_loss(model: torch.nn.Module, example: Example, device: str) -> torch.Tensor:
    """Mean next-token NLL over the example's response targets only (the trailing n_target
    tokens); logits are computed only for the n_target positions that predict them."""
    if example.n_target < 1:
        raise NoTargets(example.uid)
    ids = torch.tensor([example.input_ids], dtype=torch.long, device=device)
    logits = model(input_ids=ids, use_cache=False, logits_to_keep=example.n_target + 1).logits[0, :-1]
    if logits.shape[0] != example.n_target:
        raise RuntimeError(f"{example.uid}: got {logits.shape[0]} target logits, "
                           f"expected {example.n_target}")
    return F.cross_entropy(logits.float(), ids[0, -example.n_target:])


def make_optimizer(named: Named, train: dict) -> torch.optim.Optimizer:
    return torch.optim.AdamW([p for _, p in named], lr=train["lr"], betas=tuple(train["betas"]),
                             eps=train["eps"], weight_decay=train["weight_decay"])


def train_step(model: torch.nn.Module, named: Named, optimizer: torch.optim.Optimizer,
               example: Example, max_grad_norm: float, device: str) -> dict:
    """One batch-1 step on one example's response-only mean loss; refuses non-finite updates."""
    model.train()
    optimizer.zero_grad(set_to_none=True)
    loss = response_loss(model, example, device)
    loss.backward()
    norm = torch.nn.utils.clip_grad_norm_([p for _, p in named], max_grad_norm)
    loss_value, norm_value = float(loss.detach()), float(norm)
    if not (math.isfinite(loss_value) and math.isfinite(norm_value)):
        raise NonFiniteError(f"{example.uid}: loss {loss_value}, gradient norm {norm_value}")
    optimizer.step()
    return {"loss": loss_value, "grad_norm_preclip": norm_value}


@contextlib.contextmanager
def preserved_rng(device: str) -> Iterator[None]:
    cpu = torch.random.get_rng_state()
    mps = torch.mps.get_rng_state() if device == "mps" else None
    cuda = torch.cuda.get_rng_state_all() if device == "cuda" else None
    try:
        yield
    finally:
        torch.random.set_rng_state(cpu)
        if mps is not None:
            torch.mps.set_rng_state(mps)
        if cuda is not None:
            torch.cuda.set_rng_state_all(cuda)


Check = Callable[[str], None]


def _no_check(what: str) -> None:
    pass


@torch.no_grad()
def greedy(model: torch.nn.Module, prompt_ids: Sequence[int], max_new_tokens: int,
           stop_ids: Sequence[int], device: str, check: Check | None = None) -> tuple[list[int], bool]:
    """Argmax decoding with a KV cache and no logits processors; returns (new ids, stopped),
    where stopped means a stop id was produced (it is not included). ``check(what)`` runs
    before the prompt pass and before every further token (cooperative cap checks)."""
    check = check or _no_check
    check("prompt")
    out = model(input_ids=torch.tensor([list(prompt_ids)], dtype=torch.long, device=device),
                use_cache=True, logits_to_keep=1)
    new: list[int] = []
    while True:
        token = int(out.logits[0, -1].argmax())
        if token in stop_ids:
            return new, True
        new.append(token)
        if len(new) >= max_new_tokens:
            return new, False
        check(f"token {len(new) + 1}")
        out = model(input_ids=torch.tensor([[token]], dtype=torch.long, device=device),
                    past_key_values=out.past_key_values, use_cache=True, logits_to_keep=1)


def generate_and_nll(model: torch.nn.Module, prompts: Sequence[Sequence[int]],
                     nll_examples: Sequence[Example], max_new_tokens: int,
                     stop_ids: Sequence[int], device: str,
                     check: Check | None = None) -> tuple[list, list[float]]:
    """Evaluation that cannot perturb training: eval mode, no gradients, RNG states restored,
    previous mode restored, weights and optimizer untouched; data order lives in the plan.
    ``check(what)`` runs before every forward pass; if it raises, nothing is returned."""
    check = check or _no_check
    was_training = model.training
    model.eval()
    try:
        with preserved_rng(device), torch.no_grad():
            generations = [greedy(model, ids, max_new_tokens, stop_ids, device,
                                  lambda what, i=i: check(f"generation {i} {what}"))
                           for i, ids in enumerate(prompts, start=1)]
            nlls = []
            for i, ex in enumerate(nll_examples, start=1):
                check(f"nll {i}")
                nlls.append(float(response_loss(model, ex, device)))
    finally:
        model.train(was_training)
    return generations, nlls


def flat_gradient(model: torch.nn.Module, named: Named, example: Example,
                  device: str) -> torch.Tensor:
    """Gradient of one example's response-only mean loss w.r.t. the LoRA vector (float64, CPU)."""
    loss = response_loss(model, example, device)
    grads = torch.autograd.grad(loss, [p for _, p in named])
    # MPS cannot cast to float64 during a combined device/dtype transfer.
    vector = torch.cat([g.reshape(-1) for g in grads]).to("cpu").to(torch.float64)
    if not bool(torch.isfinite(vector).all()):
        raise NonFiniteError(f"{example.uid}: non-finite gradient")
    if float(vector.norm()) == 0.0:
        raise ZeroGradientError(f"{example.uid}: zero gradient")
    return vector


def cosine(u: torch.Tensor, v: torch.Tensor) -> float:
    if not (bool(torch.isfinite(u).all()) and bool(torch.isfinite(v).all())):
        raise NonFiniteError("non-finite vector")
    nu, nv = float(u.norm()), float(v.norm())
    if nu == 0.0 or nv == 0.0:
        raise ZeroGradientError("zero vector")
    return float(torch.dot(u, v)) / (nu * nv)


def aggregate_cosine(query: dict[str, torch.Tensor], group: dict[str, torch.Tensor]) -> dict:
    """cos(mean query gradient, mean group gradient): a cosine OF MEANS, not a mean of cosines.
    Per-example cosines against the mean query gradient are descriptive extras."""
    if not query or not group:
        raise ValueError("need at least one query and one group gradient")
    mean_query = torch.stack(list(query.values())).mean(0)
    mean_group = torch.stack(list(group.values())).mean(0)
    return {"cosine_of_means": cosine(mean_query, mean_group),
            "per_example_cosine": {uid: cosine(g, mean_query) for uid, g in group.items()},
            "query_mean_grad_norm": float(mean_query.norm()),
            "group_mean_grad_norm": float(mean_group.norm()),
            "query_example_grad_norms": {uid: float(g.norm()) for uid, g in query.items()},
            "group_example_grad_norms": {uid: float(g.norm()) for uid, g in group.items()}}


def query_group_cosine(model: torch.nn.Module, named: Named, queries: Sequence[Example],
                       group: Sequence[Example], device: str, check: Check | None = None) -> dict:
    """Per-example gradients in eval mode with RNG states and the previous mode restored, so
    attribution cannot change training. ``check(what)`` runs before every per-example gradient
    (cooperative cap checks)."""
    check = check or _no_check
    was_training = model.training
    model.eval()
    try:
        grads: dict[str, dict[str, torch.Tensor]] = {"query": {}, "group": {}}
        with preserved_rng(device):
            for role, examples in (("query", queries), ("group", group)):
                for ex in examples:
                    check(f"{role} gradient {ex.uid}")
                    grads[role][ex.uid] = flat_gradient(model, named, ex, device)
    finally:
        model.train(was_training)
    return {**aggregate_cosine(grads["query"], grads["group"]), "parameters": parameter_count(named),
            "definition": COSINE_DEFINITION, "sign": COSINE_SIGN}


@dataclass
class Assets:
    model: Any
    named: Named
    codec: Codec
    score: Callable[[list[str]], list[float]]
    count_truncated: Callable[[list[str]], int]
    device: str
    identity: dict


def device_hooks(device: str) -> tuple[Callable[[], None], Callable[[], dict]]:
    def sync() -> None:
        if device == "mps":
            torch.mps.synchronize()
        elif device == "cuda":
            torch.cuda.synchronize()

    def memory() -> dict:
        out: dict = {"peak_rss_bytes": peak_rss_bytes()}
        with contextlib.suppress(ImportError):
            import psutil

            out["rss_bytes"] = psutil.Process().memory_info().rss
        if device == "mps":
            out["mps_allocated_bytes"] = torch.mps.current_allocated_memory()
            out["mps_driver_bytes"] = torch.mps.driver_allocated_memory()
        if device == "cuda" and torch.cuda.is_initialized():
            # PyTorch caching-allocator bytes, not device-wide use. The ledger probes once per
            # stage, so resetting the peak makes it the peak since the previous stage record.
            out.update(cuda_allocated_bytes=torch.cuda.memory_allocated(),
                       cuda_reserved_bytes=torch.cuda.memory_reserved(),
                       cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                       cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved())
            torch.cuda.reset_peak_memory_stats()
        return out

    return sync, memory


def numeric_settings() -> dict:
    """Process-wide precision and determinism flags (present on CPU-only builds too)."""
    return {"deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            "deterministic_warn_only": torch.is_deterministic_algorithms_warn_only_enabled(),
            "cudnn_deterministic": torch.backends.cudnn.deterministic,
            "cudnn_benchmark": torch.backends.cudnn.benchmark,
            "cuda_matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
            "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
            "float32_matmul_precision": torch.get_float32_matmul_precision()}


def set_numeric_settings(settings: dict) -> None:
    torch.use_deterministic_algorithms(settings["deterministic_algorithms"],
                                       warn_only=settings["deterministic_warn_only"])
    torch.backends.cudnn.deterministic = settings["cudnn_deterministic"]
    torch.backends.cudnn.benchmark = settings["cudnn_benchmark"]
    torch.backends.cuda.matmul.allow_tf32 = settings["cuda_matmul_allow_tf32"]
    torch.backends.cudnn.allow_tf32 = settings["cudnn_allow_tf32"]
    torch.set_float32_matmul_precision(settings["float32_matmul_precision"])


def configure_cuda() -> dict:
    """Call before any CUDA use. Refuses, before changing anything, unless the launching
    environment exported a deterministic CUBLAS_WORKSPACE_CONFIG and does not force TF32, and
    CUDA shows exactly one GPU; then sets CUDA_SETTINGS and refuses unless they read back.
    Returns the settings in force."""
    workspace = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
    if workspace not in DETERMINISTIC_CUBLAS:
        raise RuntimeError(f"CUBLAS_WORKSPACE_CONFIG is {workspace!r}: export one of "
                           f"{DETERMINISTIC_CUBLAS} before starting Python (deterministic cuBLAS)")
    if os.environ.get("TORCH_ALLOW_TF32_CUBLAS_OVERRIDE", "0") not in ("", "0"):
        raise RuntimeError("TORCH_ALLOW_TF32_CUBLAS_OVERRIDE would allow TF32 matmuls in a "
                           "float32 recipe; unset it")
    if not torch.cuda.is_available():
        raise RuntimeError("config requests cuda but CUDA is unavailable; refusing to change device")
    count = torch.cuda.device_count()
    if count != 1:
        raise RuntimeError(f"{count} CUDA devices are visible; the profile needs exactly one "
                           "(set CUDA_VISIBLE_DEVICES)")
    set_numeric_settings(CUDA_SETTINGS)
    actual = numeric_settings()
    if actual != CUDA_SETTINGS:
        raise RuntimeError(f"CUDA precision/determinism settings did not take effect: {actual}")
    return actual


def cuda_environment() -> dict:
    """The visible GPU, the CUDA runtime and driver, and the settings in force."""
    props = torch.cuda.get_device_properties(0)
    driver = None
    with contextlib.suppress(OSError, ValueError, IndexError):  # Linux NVIDIA driver only
        driver = Path("/proc/driver/nvidia/version").read_text().splitlines()[0].strip()
    return {"device_count": torch.cuda.device_count(), "name": props.name,
            "capability": f"{props.major}.{props.minor}",
            "multiprocessors": props.multi_processor_count, "total_memory_bytes": props.total_memory,
            "torch_cuda_runtime": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
            "arch_list": torch.cuda.get_arch_list(), "driver": driver,
            "settings": numeric_settings(), "env": {name: os.environ.get(name) for name in CUDA_ENV}}


def environment(device: str) -> dict:
    from importlib import metadata

    packages = {}
    for name in ("torch", "transformers", "peft", "safetensors", "tokenizers", "huggingface-hub",
                 "numpy", "accelerate", "psutil"):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = None
    out = {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
           "packages": packages, "device": device,
           "mps_available": torch.backends.mps.is_available(),
           "mps_built": torch.backends.mps.is_built(), "torch_threads": torch.get_num_threads(),
           "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
           "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
           "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE")}
    if device == "cuda":
        out["cuda"] = cuda_environment()
    return out


# The private-use character U+E000, standing in for the user message in the template.
_SENTINEL = ""


def chat_codec(tokenizer: Any, end_token: str, stop_tokens: Sequence[str]) -> tuple[Codec, dict]:
    """Codec from the tokenizer's own chat template for one user message. The head and the
    user text are encoded together, so a merge across that join is the template's own (a
    leading newline in the user text merges with the head's final newline); the tail must
    start with the end-of-turn special token, which the tokenizer splits on before any merge.
    ``reference`` is the canonical template encoding the runner checks every prompt against."""

    def template(prompt: str, tokenize: bool) -> Any:
        return tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                                             tokenize=tokenize, add_generation_prompt=True)

    text = template(_SENTINEL, False)
    if text.count(_SENTINEL) != 1:
        raise ValueError("chat template must contain the user message exactly once")
    head, tail = text.split(_SENTINEL)
    if not tail.startswith(end_token):
        raise ValueError("the user message must be followed directly by the end-of-turn token")

    def encode(s: str) -> list[int]:
        return tokenizer.encode(s, add_special_tokens=False)

    def token_id(token: str) -> int:
        index = tokenizer.convert_tokens_to_ids(token)
        if index is None or index == tokenizer.unk_token_id or encode(token) != [index]:
            raise ValueError(f"{token!r} is not a single special token")
        return index

    end_id = token_id(end_token)
    stop_ids = tuple(sorted({token_id(t) for t in stop_tokens}))
    if end_id not in stop_ids:
        raise ValueError("the end-of-turn token must be a stop token")
    codec = Codec(encode=encode, decode=lambda ids: tokenizer.decode(list(ids), skip_special_tokens=True),
                  encode_turn=lambda prompt: encode(head + prompt), head_ids=tuple(encode(head)),
                  tail_ids=tuple(encode(tail)), end_id=end_id, stop_ids=stop_ids,
                  reference=lambda prompt: list(template(prompt, True)))
    return codec, {"head": head, "tail": tail, "head_tokens": len(codec.head_ids),
                   "tail_tokens": len(codec.tail_ids), "end_id": end_id, "stop_ids": list(stop_ids)}


def make_scorer(tokenizer: Any, model: Any, index: int, max_length: int, batch_size: int,
                device: str) -> tuple[Callable[[list[str]], list[float]], Callable[[list[str]], int]]:
    """sigmoid(logit[index]) per text: the multi-label toxic-bert 'toxic' probability."""

    def score(texts: list[str]) -> list[float]:
        out: list[float] = []
        with torch.no_grad():
            for start in range(0, len(texts), batch_size):
                batch = tokenizer(texts[start:start + batch_size], truncation=True,
                                  max_length=max_length, padding=True, return_tensors="pt").to(device)
                out += torch.sigmoid(model(**batch).logits.float()[:, index]).tolist()
        return out

    def count_truncated(texts: list[str]) -> int:
        return sum(len(tokenizer(t, truncation=False)["input_ids"]) > max_length for t in texts)

    return score, count_truncated


def load_assets(config: dict, ledger: Ledger) -> Assets:
    """The pinned cached model and scorer only: offline, safetensors, no remote code, no
    model or device fallback. Loads from the exact snapshot folder of each pinned revision."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoModelForSequenceClassification, AutoTokenizer

    spec, scorer = config["model"], config["scorer"]
    device = spec["device"]
    if device == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("config requests mps but MPS is unavailable; refusing to change device")
    if device == "cuda":
        configure_cuda()  # before any CUDA use, including the environment record below
    local = {"local_files_only": True, "trust_remote_code": False}
    identity: dict = {"device": device, "environment": environment(device)}

    def cached(repo_id: str, revision: str) -> dict:
        status = asset_status(repo_id, revision)
        if not status["present"] or not status["safetensors"]:
            raise FileNotFoundError(f"{repo_id}@{revision}: no cached snapshot with safetensors "
                                    f"weights at {status['snapshot']}")
        return status

    with ledger.stage("load_model") as info:
        status = cached(spec["repo_id"], spec["revision"])
        tokenizer = AutoTokenizer.from_pretrained(status["snapshot"], **local)
        ledger.check(0.0, "load_model weights")
        base = AutoModelForCausalLM.from_pretrained(
            status["snapshot"], torch_dtype=torch.float32, use_safetensors=True,
            attn_implementation=spec["attn_implementation"], **local)
        dtypes = {str(p.dtype) for p in base.parameters()}
        if dtypes != {"torch.float32"}:
            raise RuntimeError(f"expected float32 weights, got {sorted(dtypes)}")
        lora = spec["lora"]
        ledger.check(0.0, "load_model LoRA wrapping and device move")
        model = get_peft_model(base, LoraConfig(
            r=lora["r"], lora_alpha=lora["alpha"], lora_dropout=lora["dropout"],
            target_modules=list(lora["target_modules"]), bias="none", task_type="CAUSAL_LM"))
        model.to(device)
        named = lora_parameters(model)
        count = parameter_count(named)
        if count != lora["expected_trainable_parameters"]:
            raise RuntimeError(f"{count} trainable LoRA parameters, config expects "
                               f"{lora['expected_trainable_parameters']}")
        codec, template = chat_codec(tokenizer, spec["end_of_turn_token"], spec["stop_tokens"])
        attention = getattr(base.config, "_attn_implementation", None)
        info.update(trainable_parameters=count, attn_implementation=attention)
        identity["model"] = {**status, "trainable_parameters": count,
                             "attn_implementation": attention, "template": template}
    with ledger.stage("load_scorer") as info:
        status = cached(scorer["repo_id"], scorer["revision"])
        score_tokenizer = AutoTokenizer.from_pretrained(status["snapshot"], **local)
        ledger.check(0.0, "load_scorer weights")
        score_model = AutoModelForSequenceClassification.from_pretrained(
            status["snapshot"], torch_dtype=torch.float32, use_safetensors=True, **local)
        score_model = score_model.eval().to(scorer["device"])
        labels = {int(k): v for k, v in score_model.config.id2label.items()}
        index = [k for k, v in labels.items() if v == scorer["label"]]
        if len(index) != 1:
            raise RuntimeError(f"scorer label {scorer['label']!r} not unique in {labels}")
        score, count_truncated = make_scorer(score_tokenizer, score_model, index[0],
                                             scorer["max_length"], scorer["batch_size"],
                                             scorer["device"])
        info.update(label_index=index[0])
        identity["scorer"] = {**status, "labels": labels, "label_index": index[0],
                              "problem_type": score_model.config.problem_type,
                              "activation": "sigmoid"}
    return Assets(model, named, codec, score, count_truncated, device, identity)
