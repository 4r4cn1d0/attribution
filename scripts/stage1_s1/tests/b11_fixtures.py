"""Synthetic fixtures for the B11 tests (nothing downloaded, no dataset file read).

``build_tiny`` makes, under a temporary folder:
- an "unaligned" snapshot: a tiny random two-block OLMo-2 (Olmo2ForCausalLM built from a config), float32, saved in
  two safetensors shards (like the real base);
- an "aligned" snapshot: the same model plus a low-rank change of a different rank on each adapted matrix, saved in
  bfloat16 as one model.safetensors (like the real Instruct model). The different ranks spread the cosines;
- a PEFT LoRA (r = 4, the seven target modules) on the aligned model with random lora_A and lora_B, saved the way the
  engine saves a state (``adapter.safetensors`` without metadata, plus a ``state.json``);
- a safe_lora settings document: the real settings file with only the model pins, the adapter structure, the accepted
  fingerprint and the two K values changed to fit the tiny model.
Snapshot folders are named by a 40-hex "commit" (the Hugging Face cache layout).
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import peft  # noqa: E402
import torch  # noqa: E402
import transformers  # noqa: E402
from safetensors.torch import load_file, save_file  # noqa: E402

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1_s1 import safe_lora as sl  # noqa: E402

TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
RANK = 4
BLOCKS = 2
SEED = "1101"
DELTA_RANKS = [1, 2, 3, 5, 8, 13, 24]      # the low-rank change's rank per module (capped at the matrix size)


def config(kv_heads: int = 4) -> Any:
    return transformers.Olmo2Config(vocab_size=64, hidden_size=24, intermediate_size=40, num_hidden_layers=BLOCKS,
                                    num_attention_heads=4, num_key_value_heads=kv_heads, max_position_embeddings=64,
                                    tie_word_embeddings=False, attn_implementation="eager", pad_token_id=0,
                                    bos_token_id=1, eos_token_id=1)


def commit(label: str) -> str:
    return sha256_bytes(label.encode("ascii"))[:40]


def real_doc() -> dict:
    return json.loads(sl.SETTINGS_PATH.read_bytes())


def snapshot_pins(folder: Path) -> list[dict]:
    return [{"file": p.name, "bytes": p.stat().st_size, "sha256": sha256_file(p)}
            for p in sorted(folder.glob("*.safetensors"))]


def stored_counts(folder: Path) -> dict:
    """The stored values per safetensors dtype of a snapshot folder, counted here from the full tensors (an
    independent count; the transform reads the headers only)."""
    counts: dict = {}
    for path in sorted(folder.glob("*.safetensors")):
        for tensor in load_file(str(path)).values():
            name = {torch.float32: "F32", torch.bfloat16: "BF16"}[tensor.dtype]
            counts[name] = counts.get(name, 0) + tensor.numel()
    return counts


def git_blob_id(data: bytes) -> str:
    """The git object id of a file's bytes (the Hub's git blob id of a file stored in git)."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def full_pins_doc(tiny: "Tiny") -> dict:
    """tiny.doc with the base model pinned in full, as the real settings pin OLMo-2-0425-1B (addendum 11.6): the
    full commit, every file of the snapshot with its size and git blob id (an LFS SHA-256 for the safetensors
    files), the file pins at full length and the stored dtype."""
    doc = copy.deepcopy(tiny.doc)
    hub = []
    for path in sorted(p for p in tiny.base.iterdir() if p.is_file()):
        data = path.read_bytes()
        lfs = sha256_bytes(data) if path.name.endswith(".safetensors") else None
        hub.append({"rfilename": path.name, "size": len(data), "git_blob_id": git_blob_id(data), "lfs_sha256": lfs})
    pins = snapshot_pins(tiny.base)
    doc["models"]["unaligned"].update(revision=tiny.base.name, files=pins, hub_files=hub,
                                      total_bytes=sum(p["bytes"] for p in pins))
    return doc


def module_of(adapter_key: str) -> str:
    return adapter_key.removeprefix("base_model.model.").rsplit(".lora_", 1)[0]


@dataclass
class Tiny:
    root: Path
    aligned: Path                       # snapshot folders
    base: Path
    adapter: dict                       # engine name -> float32 tensor
    adapter_file: Path
    state_dir: Path
    fingerprint: str
    doc: dict
    settings: Any
    kv_heads: int

    def peft_model(self) -> Any:
        """A fresh PEFT model on the aligned weights (read as float32) carrying the adapter."""
        aligned = transformers.Olmo2ForCausalLM.from_pretrained(self.aligned, dtype=torch.float32, local_files_only=True)
        model = peft.get_peft_model(aligned, peft.LoraConfig(r=RANK, lora_alpha=2 * RANK, lora_dropout=0.0,
                                                             target_modules=TARGETS, bias="none", task_type="CAUSAL_LM"))
        named = en.lora_parameters(model)
        en.load_lora_state(named, self.adapter)
        return model

    def base_model(self) -> Any:
        return transformers.Olmo2ForCausalLM.from_pretrained(self.base, dtype=torch.float32, local_files_only=True)

    def aligned_model(self) -> Any:
        return transformers.Olmo2ForCausalLM.from_pretrained(self.aligned, dtype=torch.float32, local_files_only=True)


def settings_doc(doc: dict, *, aligned: Path, base: Path, adapter: dict, fingerprint: str,
                 k_default: int = 5, k_conditional: int = 2) -> dict:
    """The real settings document refitted to a tiny model (model pins, structure, fingerprint, K values)."""
    doc = copy.deepcopy(doc)
    shapes = {module_of(k) for k in adapter}
    doc["adapter"].update(blocks=BLOCKS, rank=RANK, lora_alpha=2 * RANK, matrices=len(shapes),
                          parameters=sum(t.numel() for t in adapter.values()),
                          accepted={SEED: {"fingerprint": fingerprint}})
    doc["models"]["aligned"].update(revision=aligned.name, files=snapshot_pins(aligned))
    base_pins = snapshot_pins(base)
    doc["models"]["unaligned"].update(revision=base.name[:8], files=[{"sha256": p["sha256"][:12]} for p in base_pins],
                                      total_bytes=sum(p["bytes"] for p in base_pins),
                                      stored_dtype=stored_counts(base))
    doc["models"]["unaligned"].pop("hub_files")       # a prefix pin here (the pin rule's tests); full_pins_doc pins all
    doc["transform"]["points"]["default"]["k"] = k_default
    doc["transform"]["points"]["conditional"]["k"] = k_conditional
    return doc


def settings_of(doc: dict) -> Any:
    return sl.validate_settings(doc, sha256_bytes(canonical_json(doc)))


def write_state(folder: Path, adapter: dict, *, seed: int = 1101, checkpoint: str = "e1", arm: str = "a0") -> Path:
    """An engine-style state folder: adapter.safetensors (no metadata) and its state.json."""
    folder.mkdir(parents=True)
    save_file({k: adapter[k].contiguous() for k in sorted(adapter)}, str(folder / sl.ADAPTER_FILE))
    state = {"adapter_fingerprint": sl.adapter_fingerprint(adapter), "checkpoint": checkpoint, "arm": arm,
             "seed": seed, "step": 38, "files": {sl.ADAPTER_FILE: sha256_file(folder / sl.ADAPTER_FILE)}}
    (folder / sl.STATE_FILE).write_bytes(canonical_json(state))
    return folder


def build_tiny(root: Path, *, kv_heads: int = 4, k_default: int = 5, k_conditional: int = 2,
               delta_scale: float = 0.01) -> Tiny:
    """delta_scale sizes the aligned model's low-rank change (a small value makes V mostly bfloat16 rounding)."""
    root = Path(root)
    torch.manual_seed(1)
    base = transformers.Olmo2ForCausalLM(config(kv_heads)).float()
    aligned = copy.deepcopy(base)
    generator = torch.Generator().manual_seed(2)
    with torch.no_grad():
        for block, layer in enumerate(aligned.model.layers):
            for j, name in enumerate(TARGETS):
                linear = getattr(layer.self_attn if j < 4 else layer.mlp, name)
                out_dim, in_dim = linear.weight.shape
                rank = min(DELTA_RANKS[(j + 3 * block) % len(DELTA_RANKS)], out_dim, in_dim)
                left = torch.randn(out_dim, rank, generator=generator)
                right = torch.randn(in_dim, rank, generator=generator)
                linear.weight += delta_scale * (left @ right.T)
    base_dir = root / "models--tiny--base" / "snapshots" / commit(f"base-{kv_heads}")
    aligned_dir = root / "models--tiny--aligned" / "snapshots" / commit(f"aligned-{kv_heads}-{delta_scale!r}")
    base.save_pretrained(base_dir, safe_serialization=True, max_shard_size="30KB")
    aligned.to(torch.bfloat16).save_pretrained(aligned_dir, safe_serialization=True)
    if len(list(base_dir.glob("*.safetensors"))) != 2 or len(list(aligned_dir.glob("*.safetensors"))) != 1:
        raise RuntimeError("the tiny snapshots are not two base shards and one aligned file")
    model = peft.get_peft_model(
        transformers.Olmo2ForCausalLM.from_pretrained(aligned_dir, dtype=torch.float32, local_files_only=True),
        peft.LoraConfig(r=RANK, lora_alpha=2 * RANK, lora_dropout=0.0, target_modules=TARGETS, bias="none",
                        task_type="CAUSAL_LM"))
    generator = torch.Generator().manual_seed(3)
    adapter = {}
    for name, param in en.lora_parameters(model):
        scale = 0.3 if ".lora_A." in name else 0.1
        adapter[name] = (scale * torch.randn(param.shape, generator=generator)).to(torch.float32).contiguous()
    state_dir = write_state(root / "state" / "e1", adapter)
    fingerprint = sl.adapter_fingerprint(adapter)
    doc = settings_doc(real_doc(), aligned=aligned_dir, base=base_dir, adapter=adapter, fingerprint=fingerprint,
                       k_default=k_default, k_conditional=k_conditional)
    return Tiny(root, aligned_dir, base_dir, adapter, state_dir / sl.ADAPTER_FILE, state_dir, fingerprint, doc,
                settings_of(doc), kv_heads)


def hook(tiny: Tiny, *, point: str | None = "default", doc: dict | None = None) -> Any:
    settings = tiny.settings if doc is None else settings_of(doc)
    return sl.SafeLoRA(settings, tiny.aligned, tiny.base, seed=SEED, point=point)


def write_settings_file(folder: Path, doc: dict) -> tuple[Path, str]:
    path = Path(folder) / "safe_lora.json"
    data = canonical_json(doc)
    path.write_bytes(data)
    return path, sha256_bytes(data)
