"""Torch side of the engine: batched response-only loss, the optimizer step with exact
accumulation weighting, exact state save/restore, batched greedy decoding, forced-choice
log-probabilities, forward-only query losses and per-example gradients. Imported by the
runner, the real loaders and the torch tests only.

Loss. For an optimizer step over the ACTUAL examples S (|S| = E <= micro_batch * grad_accum;
an epoch's final step can be smaller), the step objective is (1/E) sum_{i in S} l_i, where l_i
is example i's mean next-token NLL over its response targets (response plus end-of-turn).
Each micro-batch backpropagates sum(l_i)/E, so the accumulated gradient is exactly the
gradient of the step objective whatever the micro-batch split. Logits are formed only at
target positions, in chunks recomputed during backward, and cross-entropy runs in float32.

Batches are right-padded with an attention mask; causal attention never lets a real token see
a pad to its right, so positions need no adjustment. Generation is left-padded with explicit
position ids and a key/value cache; greedy argmax with no logits processors; a row stops at
its first stop token (not returned) or after ``max_new_tokens`` generated tokens counting that
stop token (stop reason ``max_new_tokens``: unresolved, never treated as complete).

Numerical failures are failures, never observations: every active generation row's logits
are checked before each argmax (an argmax over NaN returns index 0 and could pose as a stop
token), teacher-forced log-probabilities and query losses must be finite, a training step
refuses non-finite losses or gradient norms before updating, and a per-example gradient is
refused when its loss is not finite (an infinite cross-entropy can still have a finite
gradient). Each raises ``NonFiniteError``; the job fails and its folder is preserved.

Trained token rows (optional, ``model.lora.trainable_tokens``). PEFT's trainable-token layer
keeps a float32 copy of the chosen embedding rows as a trainable parameter and writes it over
those rows of the frozen embedding at every forward. With tied embeddings PEFT puts a second
layer on the output head that shares the same parameter, so the rows change on the input and
the output side together and are counted once. ``lora_parameters`` then returns the LoRA
matrices and that parameter (sorted by name); ``init_lora_state`` starts the rows from the base
model's own rows; saving, loading and fingerprints cover them like every adapter tensor. A model
without trained rows gets exactly what it got before.

Batch layout changes reduced-precision numerics: bfloat16 outputs of a batch need not equal
the same prompts run one at a time. ``prefill_logit_agreement`` checks masks and positions
against single-prompt logits within a tolerance and reports top-2 margins (also usable at a
first greedy divergence). Bitwise comparisons (continuation versus direct training, repeated
evaluations) require identical batch shapes and numerical settings.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence

import torch
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint as recompute


from experiments.minimal_safety.model import NonFiniteError, ZeroGradientError
from experiments.minimal_safety.model import init_lora_state as _init_lora_matrices
from experiments.minimal_safety.model import (load_lora_state, lora_fingerprint, make_optimizer,
                                              parameter_count)
from experiments.minimal_safety.model import lora_parameters as _lora_matrices

from .common import json_line, read_json, sha256_file, write_json
from .textproc import TrainExample

__all__ = ["Named", "NonFiniteError", "ZeroGradientError", "StateError", "init_lora_state",
           "load_lora_state", "lora_fingerprint", "lora_parameters", "make_optimizer",
           "parameter_count", "preserved_rng", "causal_lm", "example_losses",
           "accumulate_gradients", "train_step", "tensor_fingerprint", "optimizer_tensors",
           "optimizer_fingerprint", "param_groups", "capture_rng", "restore_rng", "rng_digest",
           "save_state", "load_state", "read_optimizer_tensors", "Generation", "STOP_EOS",
           "STOP_CAP", "greedy_generate", "target_logprobs", "query_losses",
           "QUERY_LOSS_DEFINITION", "example_gradient", "example_loss_and_gradient",
           "prefill_logit_agreement", "ADAPTER", "OPTIMIZER", "RNG", "STATE", "TOKEN_ROWS",
           "effective_embedding_weights", "token_row_report"]

Named = list[tuple[str, torch.nn.Parameter]]
Check = Callable[[str], None]
ADAPTER, OPTIMIZER, RNG, STATE = ("adapter.safetensors", "optimizer.safetensors",
                                  "rng.safetensors", "state.json")
TOKEN_ROWS = ".trainable_tokens_delta."      # the name part of PEFT's trained token rows
_ORIGINAL = "_safety_selection_original_rows"   # attribute holding a token-row parameter's base rows


def lora_parameters(model: torch.nn.Module) -> Named:
    """The adapter's trainable parameters, sorted by name: the LoRA A/B matrices and, when the
    recipe trains token rows, PEFT's token-row parameter. Without token rows this is exactly
    the minimal-safety rule (only LoRA matrices may train)."""
    rows = [(n, p) for n, p in model.named_parameters() if TOKEN_ROWS in n]
    if not rows:
        return _lora_matrices(model)
    named = sorted(((n, p) for n, p in model.named_parameters() if p.requires_grad), key=lambda item: item[0])
    other = [n for n, _ in named if ".lora_A." not in n and ".lora_B." not in n and TOKEN_ROWS not in n]
    if other:
        raise ValueError(f"trainable parameters outside LoRA and the token rows: {other[:3]}")
    frozen = [n for n, p in model.named_parameters()
              if (".lora_A." in n or ".lora_B." in n or TOKEN_ROWS in n) and not p.requires_grad]
    if frozen:
        raise ValueError(f"frozen adapter parameters: {frozen[:3]}")
    for module in model.modules():                   # the base model's own rows: where the token rows start
        deltas, originals = getattr(module, "trainable_tokens_delta", None), getattr(module, "trainable_tokens_original", None)
        if deltas is None or originals is None:
            continue
        for adapter, param in deltas.items():
            if not hasattr(param, _ORIGINAL):
                setattr(param, _ORIGINAL, originals[adapter].detach().to("cpu", torch.float32).clone())
    missing = [n for n, p in named if TOKEN_ROWS in n and not hasattr(p, _ORIGINAL)]
    if missing:
        raise ValueError(f"token rows without the base model's original rows: {missing}")
    return named


def init_lora_state(named: Named, seed: int) -> dict[str, torch.Tensor]:
    """The seeded adapter: the minimal-safety LoRA initialization (A uniform from the seed's
    stream, B zero) and the token rows equal to the base model's own rows, so the seeded model
    computes exactly what the base model computes."""
    matrices = [(n, p) for n, p in named if TOKEN_ROWS not in n]
    state = _init_lora_matrices(matrices, seed)
    for name, param in named:
        if TOKEN_ROWS in name:
            state[name] = getattr(param, _ORIGINAL).clone()
    return state


def effective_embedding_weights(model: Any) -> tuple[torch.Tensor, torch.Tensor]:
    """(input embedding, output head) weights as the model's forward uses them, with any trained
    token rows written in."""
    lm = causal_lm(model)

    def effective(module: Any) -> torch.Tensor:
        adapter = getattr(module, "token_adapter", None)
        if adapter is not None:
            return adapter.get_merged_weights(adapter.active_adapters).detach()
        return module.weight.detach()

    return effective(lm.get_input_embeddings()), effective(lm.get_output_embeddings())


def token_row_report(weights: torch.Tensor, token_ids: dict[str, int], padding_ids: Sequence[int]) -> dict:
    """Each token's row against never-used padding rows: its norm, its cosine to the padding
    rows' mean, its largest cosine to any padding row, and whether it is bit-identical to one of
    them; with the padding rows' and ordinary rows' median norms for scale."""
    w = weights.detach().to("cpu", torch.float32)
    pad = w[list(padding_ids)]
    mean = pad.mean(dim=0)
    unit = torch.nn.functional.normalize(pad, dim=1)
    excluded = set(padding_ids) | set(token_ids.values())
    ordinary = [i for i in range(w.shape[0]) if i not in excluded]
    raw = weights.detach().to("cpu")
    padding_raw = raw[list(padding_ids)]
    out = {"padding_rows": len(padding_ids), "padding_median_norm": float(pad.norm(dim=1).median()),
           "ordinary_median_norm": float(w[ordinary].norm(dim=1).median()) if ordinary else None,
           "padding_rows_all_identical": bool((padding_raw == padding_raw[:1]).all()), "tokens": {}}
    for token, index in token_ids.items():
        row = w[index]
        out["tokens"][token] = {
            "id": index, "norm": float(row.norm()),
            "cosine_to_padding_mean": float(torch.nn.functional.cosine_similarity(row, mean, dim=0)),
            "max_cosine_to_padding": float((unit @ torch.nn.functional.normalize(row, dim=0)).max()),
            "bit_identical_to_a_padding_row": bool((padding_raw == raw[index]).all(dim=1).any())}
    return out
STOP_EOS, STOP_CAP = "eos", "max_new_tokens"
QUERY_LOSS_DEFINITION = ("per query row, the training loss: mean next-token NLL over its response "
                         "plus end-of-turn targets (float32 cross-entropy, full text, no "
                         "truncation); one row per forward pass (no padding), eval mode, no "
                         "gradient; aggregate = arithmetic mean over the supplied DATE-LM reference "
                         "query rows. A target-likelihood proxy, not a safety measurement")


class StateError(RuntimeError):
    """A saved state is missing, altered or inconsistent with the live model/optimizer."""


def _no_check(what: str) -> None:
    pass


def causal_lm(model: Any) -> Any:
    """The transformers causal LM inside a PEFT wrapper (LoRA layers injected), or the model."""
    get = getattr(model, "get_base_model", None)
    return get() if callable(get) and hasattr(model, "peft_config") else model


def _right_padded(sequences: Sequence[Sequence[int]], pad_id: int,
                  device: str) -> tuple[torch.Tensor, torch.Tensor]:
    width = max(len(s) for s in sequences)
    ids = torch.full((len(sequences), width), pad_id, dtype=torch.long)
    mask = torch.zeros((len(sequences), width), dtype=torch.long)
    for i, seq in enumerate(sequences):
        ids[i, :len(seq)] = torch.tensor(list(seq), dtype=torch.long)
        mask[i, :len(seq)] = 1
    return ids.to(device), mask.to(device)


def _left_padded(prompts: Sequence[Sequence[int]], pad_id: int,
                 device: str) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """The generation layout: left padding, attention mask, explicit position ids."""
    rows, width = len(prompts), max(len(p) for p in prompts)
    ids = torch.full((rows, width), pad_id, dtype=torch.long)
    mask = torch.zeros((rows, width), dtype=torch.long)
    for i, prompt in enumerate(prompts):
        ids[i, width - len(prompt):] = torch.tensor(list(prompt), dtype=torch.long)
        mask[i, width - len(prompt):] = 1
    ids, mask = ids.to(device), mask.to(device)
    return ids, mask, (mask.cumsum(-1) - 1).clamp(min=0)


def _chunk_nll(head: torch.nn.Module, hidden: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    return F.cross_entropy(head(hidden).float(), targets, reduction="none")


def _target_nll(model: Any, sequences: Sequence[Sequence[int]], n_targets: Sequence[int],
                pad_id: int, device: str, chunk: int) -> list[torch.Tensor]:
    """Float32 NLL of the last ``n`` tokens of each sequence, from one right-padded forward."""
    for seq, n in zip(sequences, n_targets, strict=True):
        if not 1 <= n < len(seq):
            raise ValueError(f"{n} targets do not fit a sequence of {len(seq)} tokens")
    lm = causal_lm(model)
    ids, mask = _right_padded(sequences, pad_id, device)
    hidden = lm.model(input_ids=ids, attention_mask=mask, use_cache=False).last_hidden_state
    pieces, targets = [], []
    for i, (seq, n) in enumerate(zip(sequences, n_targets)):
        start = len(seq) - n - 1  # the position whose logits predict the first target
        pieces.append(hidden[i, start:start + n])
        targets.append(ids[i, start + 1:start + 1 + n])
    h, t = torch.cat(pieces), torch.cat(targets)
    out = []
    for s in range(0, h.shape[0], chunk):
        hs, ts = h[s:s + chunk], t[s:s + chunk]
        if torch.is_grad_enabled() and hs.requires_grad:
            out.append(recompute(_chunk_nll, lm.lm_head, hs, ts, use_reentrant=False,
                                 preserve_rng_state=False))
        else:
            out.append(_chunk_nll(lm.lm_head, hs, ts))
    return list(torch.cat(out).split(list(n_targets)))


def example_losses(model: Any, examples: Sequence[TrainExample], pad_id: int, device: str,
                   chunk: int) -> torch.Tensor:
    """Per-example mean response-target NLL (float32), one right-padded forward."""
    parts = _target_nll(model, [e.input_ids for e in examples], [e.n_target for e in examples],
                        pad_id, device, chunk)
    return torch.stack([p.mean() for p in parts])


def accumulate_gradients(model: Any, examples: Sequence[TrainExample], micro_batch: int,
                         pad_id: int, device: str, chunk: int) -> list[float]:
    """Backpropagate the step objective (1/E) sum_i l_i over the ACTUAL E examples in
    micro-batches of at most ``micro_batch``; returns each example's loss."""
    total, values = len(examples), []
    for start in range(0, total, micro_batch):
        losses = example_losses(model, examples[start:start + micro_batch], pad_id, device, chunk)
        (losses.sum() / total).backward()
        values += [float(v) for v in losses.detach().float().cpu()]
    return values


def train_step(model: Any, named: Named, optimizer: torch.optim.Optimizer,
               examples: Sequence[TrainExample], micro_batch: int, max_grad_norm: float,
               pad_id: int, device: str, chunk: int) -> dict:
    """One optimizer step; refuses non-finite losses or gradients before updating."""
    model.train()
    optimizer.zero_grad(set_to_none=True)
    losses = accumulate_gradients(model, examples, micro_batch, pad_id, device, chunk)
    missing = [name for name, p in named if p.grad is None]
    if missing:
        raise RuntimeError(f"LoRA parameters without gradients: {missing[:3]}")
    norm = float(torch.nn.utils.clip_grad_norm_([p for _, p in named], max_grad_norm))
    if not (math.isfinite(norm) and all(map(math.isfinite, losses))):
        raise NonFiniteError(f"non-finite step: losses {losses}, gradient norm {norm}")
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    return {"loss": sum(losses) / len(losses), "example_losses": losses, "grad_norm_preclip": norm}


def tensor_fingerprint(tensors: dict[str, torch.Tensor]) -> str:
    """SHA-256 over sorted names, dtypes, shapes and the exact bytes of each tensor."""
    digest = hashlib.sha256()
    for key in sorted(tensors):
        t = tensors[key].detach().to("cpu").contiguous()
        digest.update(key.encode("utf-8"))
        digest.update(f"{t.dtype}{tuple(t.shape)}".encode("ascii"))
        digest.update(t.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def optimizer_tensors(optimizer: torch.optim.Optimizer, named: Named) -> dict[str, torch.Tensor]:
    """AdamW state as ``{step,exp_avg,exp_avg_sq}/<parameter name>`` CPU tensors ({} before
    the first step). Partial or unexpected state raises: nothing is fabricated."""
    states = [optimizer.state.get(p, {}) for _, p in named]
    if not any(states):
        return {}
    out = {}
    for (name, _), state in zip(named, states):
        if set(state) != {"step", "exp_avg", "exp_avg_sq"}:
            raise StateError(f"{name}: optimizer state has keys {sorted(state)}")
        out[f"step/{name}"] = state["step"].detach().to("cpu").reshape(1).clone()
        for key in ("exp_avg", "exp_avg_sq"):
            out[f"{key}/{name}"] = state[key].detach().to("cpu").contiguous().clone()
    return out


def optimizer_fingerprint(optimizer: torch.optim.Optimizer, named: Named) -> str | None:
    tensors = optimizer_tensors(optimizer, named)
    return tensor_fingerprint(tensors) if tensors else None


def param_groups(optimizer: torch.optim.Optimizer) -> list[dict]:
    """Hyperparameters of each group (JSON-normalized), without parameter references."""
    return json.loads(json_line([{k: v for k, v in g.items() if k != "params"}
                                 for g in optimizer.param_groups]))


def capture_rng(device: str) -> dict:
    tensors = {"cpu": torch.get_rng_state().clone()}
    if device == "cuda":
        for i, state in enumerate(torch.cuda.get_rng_state_all()):
            tensors[f"cuda/{i}"] = state.clone()
    version, internal, gauss = random.getstate()
    return {"tensors": tensors, "python": [version, list(internal), gauss]}


def restore_rng(device: str, tensors: dict[str, torch.Tensor], python: list) -> None:
    torch.set_rng_state(tensors["cpu"])
    if device == "cuda":
        torch.cuda.set_rng_state_all([tensors[f"cuda/{i}"] for i in range(torch.cuda.device_count())])
    random.setstate((python[0], tuple(python[1]), python[2]))


def rng_digest(device: str) -> str:
    captured = capture_rng(device)
    digest = hashlib.sha256(tensor_fingerprint(captured["tensors"]).encode("ascii"))
    digest.update(json_line(captured["python"]))
    return digest.hexdigest()


@contextlib.contextmanager
def preserved_rng(device: str) -> Iterator[None]:
    """Restore the CPU, CUDA and Python ``random`` states on exit, whatever ran inside."""
    captured = capture_rng(device)
    try:
        yield
    finally:
        restore_rng(device, captured["tensors"], captured["python"])


def save_state(folder: str | Path, named: Named, optimizer: torch.optim.Optimizer, device: str,
               meta: dict) -> dict:
    """Adapter, AdamW moments/steps, RNG states and ``meta`` (stream position, identities,
    trajectory cost) under a new folder; returns the written state record."""
    from safetensors.torch import save_file

    folder = Path(folder)
    folder.mkdir(parents=True)
    save_file({n: p.detach().to("cpu").contiguous() for n, p in named}, str(folder / ADAPTER))
    opt = optimizer_tensors(optimizer, named)
    if opt:
        save_file(opt, str(folder / OPTIMIZER))
    rng = capture_rng(device)
    save_file(rng["tensors"], str(folder / RNG))
    files = [ADAPTER, RNG] + ([OPTIMIZER] if opt else [])
    state = {**meta, "adapter_fingerprint": lora_fingerprint(named),
             "optimizer_fingerprint": tensor_fingerprint(opt) if opt else None,
             "param_groups": param_groups(optimizer), "python_random_state": rng["python"],
             "rng_fingerprint": tensor_fingerprint(rng["tensors"]),
             "files": {name: sha256_file(folder / name) for name in sorted(files)}}
    write_json(folder / STATE, state)
    return state


def read_optimizer_tensors(folder: str | Path) -> tuple[dict, dict[str, torch.Tensor]]:
    """A saved state's record and AdamW tensors (CPU), after its file hashes verify."""
    from safetensors.torch import load_file

    folder = Path(folder)
    state = read_json(folder / STATE)
    for name, digest in state["files"].items():
        if sha256_file(folder / name) != digest:
            raise StateError(f"{folder / name} differs from its recorded hash")
    if state["optimizer_fingerprint"] is None:
        raise StateError(f"{folder}: no optimizer state (no step taken)")
    tensors = load_file(str(folder / OPTIMIZER), device="cpu")
    if tensor_fingerprint(tensors) != state["optimizer_fingerprint"]:
        raise StateError(f"{folder}: optimizer tensors differ from the recorded fingerprint")
    return state, tensors


def load_state(folder: str | Path, named: Named, optimizer: torch.optim.Optimizer | None,
               device: str, restore_rng_state: bool = True) -> dict:
    """Restore a saved state exactly (fingerprints verified). ``optimizer`` must be fresh,
    built with the same recipe; ``None`` loads the adapter only (evaluation/attribution)."""
    from safetensors.torch import load_file

    folder = Path(folder)
    state = read_json(folder / STATE)
    for name, digest in state["files"].items():
        if sha256_file(folder / name) != digest:
            raise StateError(f"{folder / name} differs from its recorded hash")
    load_lora_state(named, load_file(str(folder / ADAPTER), device="cpu"))
    if lora_fingerprint(named) != state["adapter_fingerprint"]:
        raise StateError(f"{folder}: adapter fingerprint differs after loading")
    if optimizer is not None:
        if optimizer.state:
            raise StateError("restoring into an optimizer that already has state")
        if param_groups(optimizer) != state["param_groups"]:
            raise StateError("optimizer hyperparameters differ from the saved state")
        if state["optimizer_fingerprint"] is not None:
            tensors = load_file(str(folder / OPTIMIZER), device="cpu")
            expected = {f"{k}/{n}" for n, _ in named for k in ("step", "exp_avg", "exp_avg_sq")}
            if set(tensors) != expected:
                raise StateError("saved optimizer tensors do not match the LoRA parameters")
            saved = optimizer.state_dict()
            saved["state"] = {i: {"step": tensors[f"step/{n}"].reshape(()).clone(),
                                  "exp_avg": tensors[f"exp_avg/{n}"],
                                  "exp_avg_sq": tensors[f"exp_avg_sq/{n}"]}
                              for i, (n, _) in enumerate(named)}
            optimizer.load_state_dict(saved)
        if optimizer_fingerprint(optimizer, named) != state["optimizer_fingerprint"]:
            raise StateError(f"{folder}: optimizer fingerprint differs after loading")
    if restore_rng_state:
        tensors = load_file(str(folder / RNG), device="cpu")
        if tensor_fingerprint(tensors) != state["rng_fingerprint"]:
            raise StateError(f"{folder}: RNG tensors differ from the recorded fingerprint")
        restore_rng(device, tensors, state["python_random_state"])
    return state


@dataclass(frozen=True)
class Generation:
    output_ids: tuple[int, ...]  # generated tokens before the stop token
    stop_reason: str  # STOP_EOS or STOP_CAP
    stop_token: int | None


def _checked_argmax(logits: torch.Tensor, active: Sequence[bool], where: str) -> list[int]:
    """Greedy token of every row after checking that every ACTIVE row's logits are finite.
    Finished rows are fed padding and their logits are never used, so they are not checked."""
    rows = [i for i, alive in enumerate(active) if alive]
    if rows:
        index = torch.tensor(rows, dtype=torch.long, device=logits.device)
        if not bool(torch.isfinite(logits.index_select(0, index)).all()):
            raise NonFiniteError(f"non-finite logits in an active generation row at {where}; "
                                 "refusing to decode (not a stop, cap or empty output)")
    return logits.argmax(-1).tolist()


@torch.no_grad()
def _greedy_batch(model: Any, prompts: Sequence[Sequence[int]], max_new_tokens: int,
                  stop_ids: Sequence[int], pad_id: int, device: str, check: Check) -> list[Generation]:
    lm = causal_lm(model)
    rows = len(prompts)
    ids, mask, positions = _left_padded(prompts, pad_id, device)
    check("prompt pass")
    out = lm(input_ids=ids, attention_mask=mask, position_ids=positions, use_cache=True,
             logits_to_keep=1)
    cache, last = out.past_key_values, positions[:, -1]
    tokens = _checked_argmax(out.logits[:, -1, :], [True] * rows, "the prompt pass")
    stop = set(stop_ids)
    new: list[list[int]] = [[] for _ in range(rows)]
    done: list[Generation | None] = [None] * rows
    for k in range(1, max_new_tokens + 1):
        for i, token in enumerate(tokens):
            if done[i] is not None:
                continue
            if token in stop:
                done[i] = Generation(tuple(new[i]), STOP_EOS, token)
            else:
                new[i].append(token)
                if k == max_new_tokens:
                    done[i] = Generation(tuple(new[i]), STOP_CAP, None)
        if all(d is not None for d in done):
            break
        check(f"token {k + 1}")
        feed = torch.tensor([[pad_id if done[i] is not None else t] for i, t in enumerate(tokens)],
                            dtype=torch.long, device=device)
        mask = torch.cat([mask, mask.new_ones((rows, 1))], dim=1)
        last = last + 1
        out = lm(input_ids=feed, attention_mask=mask, position_ids=last[:, None],
                 past_key_values=cache, use_cache=True, logits_to_keep=1)
        cache = out.past_key_values
        tokens = _checked_argmax(out.logits[:, -1, :], [d is None for d in done], f"token {k + 1}")
    return [d for d in done if d is not None]


def greedy_generate(model: Any, prompts: Sequence[Sequence[int]], *, max_new_tokens: int,
                    stop_ids: Sequence[int], pad_id: int, device: str, batch_size: int,
                    check: Check | None = None,
                    on_batch: Callable[[int, list[int], list[Generation]], None] | None = None
                    ) -> list[Generation]:
    """Greedy decoding in eval mode (previous mode restored) for each prompt, in batches of
    similar length (sorted by length, then position: a fixed composition for a fixed prompt
    list and batch size, the frozen batching policy). Results are returned in input order."""
    check = check or _no_check
    order = sorted(range(len(prompts)), key=lambda i: (len(prompts[i]), i))
    results: list[Generation | None] = [None] * len(prompts)
    was_training = model.training
    model.eval()
    try:
        for b, start in enumerate(range(0, len(order), batch_size)):
            index = order[start:start + batch_size]
            batch = _greedy_batch(model, [prompts[i] for i in index], max_new_tokens, stop_ids,
                                  pad_id, device, lambda what, b=b: check(f"generation batch {b} {what}"))
            if len(batch) != len(index):
                raise RuntimeError("internal: a generation row did not finish")
            for i, generation in zip(index, batch):
                results[i] = generation
            if on_batch is not None:
                on_batch(b, index, batch)
    finally:
        model.train(was_training)
    return [r for r in results if r is not None]


@torch.no_grad()
def target_logprobs(model: Any, sequences: Sequence[Sequence[int]], n_targets: Sequence[int], *,
                    pad_id: int, device: str, batch_size: int, chunk: int,
                    check: Check | None = None) -> list[list[float]]:
    """Per-token log-probabilities of the last ``n`` tokens of each sequence (teacher forced,
    eval mode, previous mode restored). Any non-finite value raises before it is returned."""
    check = check or _no_check
    was_training = model.training
    model.eval()
    try:
        out: list[list[float]] = []
        for start in range(0, len(sequences), batch_size):
            check(f"logprob batch {start // batch_size}")
            parts = _target_nll(model, sequences[start:start + batch_size],
                                n_targets[start:start + batch_size], pad_id, device, chunk)
            for offset, part in enumerate(parts):
                if not bool(torch.isfinite(part).all()):
                    raise NonFiniteError(f"non-finite teacher-forced log-probability in sequence "
                                         f"{start + offset}")
            out += [[-float(v) for v in part.double().cpu()] for part in parts]
    finally:
        model.train(was_training)
    return out


@torch.no_grad()
def query_losses(model: Any, examples: Sequence[TrainExample], *, pad_id: int, device: str,
                 chunk: int, check: Check | None = None) -> list[float]:
    """Forward-only training loss of each example (``QUERY_LOSS_DEFINITION``): one example per
    forward, eval mode (previous mode restored), no gradient, nothing updated; a non-finite
    loss raises."""
    check = check or _no_check
    was_training = model.training
    model.eval()
    try:
        out = []
        for example in examples:
            check(f"query loss {example.row_id}")
            value = float(example_losses(model, [example], pad_id, device, chunk)[0])
            if not math.isfinite(value):
                raise NonFiniteError(f"{example.row_id}: non-finite query loss {value}")
            out.append(value)
    finally:
        model.train(was_training)
    return out


def example_loss_and_gradient(model: Any, named: Named, example: TrainExample, *, pad_id: int,
                              device: str, chunk: int) -> tuple[float, torch.Tensor]:
    """One example's response-only mean loss and its gradient w.r.t. the LoRA vector (sorted
    parameter names, float64 on CPU). The loss must be finite BEFORE autograd runs: an
    infinite cross-entropy can have a finite gradient (logits [-inf, theta], target 0: loss
    inf, d/dtheta = 1), which would otherwise pass as a valid row. Uses autograd.grad, so
    ``.grad`` is untouched."""
    with torch.enable_grad():
        loss = example_losses(model, [example], pad_id, device, chunk)[0]
        value = float(loss.detach())
        if not math.isfinite(value):
            raise NonFiniteError(f"{example.row_id}: non-finite loss {value}; no gradient is taken")
        grads = torch.autograd.grad(loss, [p for _, p in named])
    # MPS cannot cast to float64 during a combined device/dtype transfer.
    vector = torch.cat([g.reshape(-1) for g in grads]).to("cpu").to(torch.float64)
    if not bool(torch.isfinite(vector).all()):
        raise NonFiniteError(f"{example.row_id}: non-finite gradient")
    if float(vector.norm()) == 0.0:
        raise ZeroGradientError(f"{example.row_id}: zero gradient")
    return value, vector


def example_gradient(model: Any, named: Named, example: TrainExample, *, pad_id: int, device: str,
                     chunk: int) -> torch.Tensor:
    """The gradient of ``example_loss_and_gradient``."""
    return example_loss_and_gradient(model, named, example, pad_id=pad_id, device=device,
                                     chunk=chunk)[1]


@torch.no_grad()
def prefill_logit_agreement(model: Any, prompts: Sequence[Sequence[int]], *, pad_id: int,
                            device: str) -> list[dict]:
    """Left-padded batched prefill (the generation layout) against each prompt alone, per
    prompt: the largest absolute float32 difference of final hidden states over every real
    position and of the last-position logits, whether the last-position argmax agrees, and the
    single-prompt top-2 logit margin there. A mask or position error shows as a large
    difference; reduced-precision batching noise as a small one; the tolerance is a frozen
    calibration choice of the caller. Called on ``prompt + generated prefix`` it inspects a
    first greedy divergence (a near-zero margin marks a near-tie)."""
    lm = causal_lm(model)
    was_training = model.training
    model.eval()
    try:
        ids, mask, positions = _left_padded(prompts, pad_id, device)
        hidden = lm.model(input_ids=ids, attention_mask=mask, position_ids=positions,
                          use_cache=False).last_hidden_state
        last = lm.lm_head(hidden[:, -1]).float()
        width, out = ids.shape[1], []
        for i, prompt in enumerate(prompts):
            single_ids = torch.tensor([list(prompt)], dtype=torch.long, device=device)
            single = lm.model(input_ids=single_ids, use_cache=False).last_hidden_state[0]
            single_last = lm.lm_head(single[-1:]).float()[0]
            real = hidden[i, width - len(prompt):]
            top = single_last.topk(2).values
            out.append({"tokens": len(prompt),
                        "max_abs_hidden_difference": float((real.float() - single.float()).abs().max()),
                        "max_abs_last_logit_difference": float((last[i] - single_last).abs().max()),
                        "last_argmax_agrees": int(last[i].argmax()) == int(single_last.argmax()),
                        "single_top2_margin": float(top[0] - top[1])})
    finally:
        model.train(was_training)
    return out
