"""Config validation and the offline plan (dry run).

Stdlib only: never imports torch/transformers, loads a model, trains, scores or uses the
network. Validation checks exact key sets and supported values and never fills defaults, so a
setting can change only by editing the config (which changes its hash).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import data
from .common import canonical_json, sha256_bytes, sha256_file

__all__ = ["ConfigError", "MAX_TRAIN_EXAMPLES", "load_config", "validate", "config_sha256",
           "arms", "hf_cache_dir", "snapshot_dir", "snapshot_files", "asset_status",
           "code_hashes", "operation_counts", "build_plan"]

MAX_TRAIN_EXAMPLES = 128
CHECKPOINTS = ("short", "long")
SECTIONS = {
    "dataset": {"repo_id", "revision", "subset", "train_file", "ref_file", "train_sha256",
                "ref_sha256", "forbidden_substrings"},
    "design": {"design_seed", "train_counts", "benign_holdout", "ref_query", "ref_eval", "removal"},
    "model": {"repo_id", "revision", "dtype", "attn_implementation", "device", "end_of_turn_token",
              "stop_tokens", "lora"},
    "train": {"seeds", "short_steps", "long_steps", "batch_size", "optimizer", "lr", "betas", "eps",
              "weight_decay", "lr_schedule", "max_grad_norm", "max_seq_len",
              "reserved_response_tokens"},
    "eval": {"decoding", "max_new_tokens", "eval_base", "toxic_threshold", "copy_ngram",
             "copy_fraction"},
    "scorer": {"repo_id", "revision", "device", "label", "activation", "max_length", "batch_size"},
    "attribution": {"arm", "checkpoint", "aggregation"},
    "audit": {"shuffle_seed"},
    "caps": {"wall_seconds", "output_bytes"},
}
SUBSECTIONS = {("design", "removal"): {"arm", "type", "size", "label"},
               ("model", "lora"): {"r", "alpha", "dropout", "target_modules",
                                   "expected_trainable_parameters"}}
FIXED = {("train", "batch_size"): 1, ("train", "optimizer"): "AdamW",
         ("train", "lr_schedule"): "constant", ("eval", "decoding"): "greedy",
         ("model", "dtype"): "float32", ("model", "attn_implementation"): "eager",
         ("model", "lora", "dropout"): 0.0, ("scorer", "activation"): "sigmoid",
         ("attribution", "arm"): "a0", ("attribution", "checkpoint"): "long",
         ("attribution", "aggregation"): "cosine_of_means"}


class ConfigError(ValueError):
    pass


def _keys(obj: object, expected: set[str], where: str) -> None:
    if not isinstance(obj, dict):
        raise ConfigError(f"{where}: expected an object")
    if set(obj) != expected:
        raise ConfigError(f"{where}: missing {sorted(expected - set(obj))}, "
                          f"unknown {sorted(set(obj) - expected)}")


def _int(value: object, where: str, low: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < low:
        raise ConfigError(f"{where}: expected an integer >= {low}")
    return value


def _hex(value: object, length: int, where: str) -> None:
    if not (isinstance(value, str) and len(value) == length
            and all(c in "0123456789abcdef" for c in value)):
        raise ConfigError(f"{where}: expected {length} lowercase hex characters")


def validate(config: dict) -> dict:
    """Raise ConfigError unless the config is complete and supported; returns it unchanged."""
    _keys(config, {"name", "purpose", *SECTIONS}, "config")
    for section, keys in SECTIONS.items():
        _keys(config[section], keys, section)
    for (section, key), keys in SUBSECTIONS.items():
        _keys(config[section][key], keys, f"{section}.{key}")
    for path, value in FIXED.items():
        node = config
        for key in path:
            node = node[key]
        if node != value:
            raise ConfigError(f"{'.'.join(path)} must be {value!r} (the only implemented choice)")
    ds, design, train, ev = config["dataset"], config["design"], config["train"], config["eval"]
    for key in ("train_sha256", "ref_sha256"):
        _hex(ds[key], 64, f"dataset.{key}")
    for section in ("dataset", "model", "scorer"):
        _hex(config[section]["revision"], 40, f"{section}.revision")
    counts = design["train_counts"]
    if not isinstance(counts, dict) or not set(counts) <= set(data.TYPES):
        raise ConfigError(f"design.train_counts keys must be among {data.TYPES}")
    total = sum(_int(n, f"design.train_counts.{t}") for t, n in counts.items())
    if not 0 < total <= MAX_TRAIN_EXAMPLES:
        raise ConfigError(f"design.train_counts must total 1..{MAX_TRAIN_EXAMPLES}, got {total}")
    removal = design["removal"]
    if removal["arm"] == "a0" or removal["type"] not in counts:
        raise ConfigError("design.removal: arm must not be 'a0' and type must be in train_counts")
    if not 0 < _int(removal["size"], "design.removal.size") < counts[removal["type"]] + 1:
        raise ConfigError("design.removal.size must be 1..train_counts[type]")
    if removal["size"] >= total:
        raise ConfigError("design.removal.size must leave retained training rows")
    for key in ("design_seed", "benign_holdout", "ref_query", "ref_eval"):
        _int(design[key], f"design.{key}", low=1 if key != "design_seed" else 0)
    seeds = train["seeds"]
    if not (isinstance(seeds, list) and seeds and len(set(seeds)) == len(seeds)):
        raise ConfigError("train.seeds must be a non-empty list of distinct integers")
    for seed in seeds:
        _int(seed, "train.seeds[]")
    if not 0 < _int(train["short_steps"], "train.short_steps", 1) < _int(train["long_steps"],
                                                                          "train.long_steps", 2):
        raise ConfigError("train.short_steps must be below train.long_steps")
    if not 0 < _int(train["reserved_response_tokens"], "train.reserved_response_tokens", 1) \
            < _int(train["max_seq_len"], "train.max_seq_len", 2):
        raise ConfigError("train.reserved_response_tokens must be below train.max_seq_len")
    if _int(ev["max_new_tokens"], "eval.max_new_tokens", 1) >= train["max_seq_len"]:
        raise ConfigError("eval.max_new_tokens must be below train.max_seq_len")
    # Exact strings: 'cuda' never names an index; the runner requires one visible GPU.
    if config["model"]["device"] not in ("mps", "cpu", "cuda") or config["scorer"]["device"] != "cpu":
        raise ConfigError("model.device must be 'mps', 'cpu' or 'cuda'; scorer.device must be 'cpu'")
    for key in ("wall_seconds", "output_bytes"):
        value = config["caps"][key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise ConfigError(f"caps.{key} must be positive")
    if not isinstance(ev["eval_base"], bool):
        raise ConfigError("eval.eval_base must be true or false")
    positive = {"train.lr": train["lr"], "train.eps": train["eps"],
                "train.max_grad_norm": train["max_grad_norm"]}
    unit = {"eval.toxic_threshold": ev["toxic_threshold"], "eval.copy_fraction": ev["copy_fraction"]}
    for where, value in {**positive, **unit, "train.weight_decay": train["weight_decay"]}.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"{where} must be a number")
    if any(v <= 0 for v in positive.values()) or train["weight_decay"] < 0 \
            or any(not 0 < v <= 1 for v in unit.values()):
        raise ConfigError("lr, eps, max_grad_norm must be > 0; weight_decay >= 0; "
                          "toxic_threshold and copy_fraction in (0, 1]")
    betas = train["betas"]
    if not (isinstance(betas, list) and len(betas) == 2
            and all(isinstance(b, (int, float)) and 0 <= b < 1 for b in betas)):
        raise ConfigError("train.betas must be two numbers in [0, 1)")
    lora = config["model"]["lora"]
    for where, value in {"eval.copy_ngram": ev["copy_ngram"], "model.lora.r": lora["r"],
                         "model.lora.alpha": lora["alpha"],
                         "model.lora.expected_trainable_parameters":
                             lora["expected_trainable_parameters"],
                         "scorer.max_length": config["scorer"]["max_length"],
                         "scorer.batch_size": config["scorer"]["batch_size"]}.items():
        _int(value, where, low=1)
    _int(config["audit"]["shuffle_seed"], "audit.shuffle_seed")
    for where, value in {"model.lora.target_modules": lora["target_modules"],
                         "model.stop_tokens": config["model"]["stop_tokens"],
                         "dataset.forbidden_substrings": ds["forbidden_substrings"]}.items():
        if not (isinstance(value, list) and value and all(isinstance(v, str) and v for v in value)):
            raise ConfigError(f"{where} must be a non-empty list of non-empty strings")
    return config


def load_config(path: str | os.PathLike) -> dict:
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))


def config_sha256(config: dict) -> str:
    return sha256_bytes(canonical_json(config))


def arms(config: dict) -> list[str]:
    return ["a0", config["design"]["removal"]["arm"]]


def hf_cache_dir() -> Path:
    """The Hugging Face hub cache, resolved like huggingface_hub without importing it."""
    for name in ("HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE"):
        if os.environ.get(name):
            return Path(os.environ[name]).expanduser()
    if os.environ.get("HF_HOME"):
        return Path(os.environ["HF_HOME"]).expanduser() / "hub"
    root = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(root).expanduser() / "huggingface" / "hub"


def snapshot_dir(repo_id: str, revision: str) -> Path:
    return hf_cache_dir() / f"models--{repo_id.replace('/', '--')}" / "snapshots" / revision


def snapshot_files(folder: Path) -> list[dict]:
    """Files in a cached snapshot with their resolved blob names (the SHA-256 for LFS files,
    the git blob id otherwise): exact asset identity without hashing gigabytes."""
    out = []
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        real = path.resolve()
        out.append({"file": str(path.relative_to(folder)), "bytes": real.stat().st_size,
                    "blob": real.name})
    return out


def asset_status(repo_id: str, revision: str) -> dict:
    folder = snapshot_dir(repo_id, revision)
    files = snapshot_files(folder) if folder.is_dir() else []
    return {"repo_id": repo_id, "revision": revision, "snapshot": str(folder),
            "present": folder.is_dir(),
            "safetensors": [f["file"] for f in files if f["file"].endswith(".safetensors")],
            "files": files}


def code_hashes() -> dict[str, str]:
    folder = Path(__file__).resolve().parent
    return {p.name: sha256_file(p) for p in sorted(folder.glob("*.py"))}


def operation_counts(config: dict) -> dict:
    """Work implied by the config; counts, not time estimates (costs are measured by the run)."""
    design, train, ev = config["design"], config["train"], config["eval"]
    n_seeds = len(train["seeds"])
    evals = n_seeds * 2 * len(CHECKPOINTS) + (1 if ev["eval_base"] else 0)
    prompts = design["ref_eval"] + design["benign_holdout"]
    return {"optimizer_steps": n_seeds * 2 * train["long_steps"],
            "evaluations": evals,
            "greedy_generations": evals * prompts,
            "max_generated_tokens": evals * prompts * ev["max_new_tokens"],
            "teacher_forced_nll_examples": evals * prompts,
            "gradient_examples": n_seeds * (design["ref_query"] + design["removal"]["size"]),
            "classifier_texts": sum(design["train_counts"].values()) + evals * prompts}


def build_plan(config: dict, prepared_dir: str | os.PathLike | None = None) -> dict:
    validate(config)
    model, scorer = config["model"], config["scorer"]
    out = {
        "kind": "offline dry run: nothing was loaded, trained, scored or downloaded",
        "status": "not run",
        "name": config["name"],
        "config_sha256": config_sha256(config),
        "arms": arms(config),
        "removal": config["design"]["removal"],
        "seeds": config["train"]["seeds"],
        "steps": {"short": config["train"]["short_steps"], "long": config["train"]["long_steps"]},
        "data": {k: config["dataset"][k] for k in ("repo_id", "revision", "subset", "train_file",
                                                   "ref_file", "train_sha256", "ref_sha256")},
        "assets": {"model": asset_status(model["repo_id"], model["revision"]),
                   "scorer": asset_status(scorer["repo_id"], scorer["revision"])},
        "device": model["device"],
        "caps": config["caps"],
        "operations": operation_counts(config),
        "settings": "taken only from the config; no defaults, model, device or workload substitution",
        "prepared": None,
    }
    if prepared_dir is not None:
        manifest, rows, digest = data.load_prepared(prepared_dir)
        streams = data.stream_plan(manifest, config)
        out["prepared"] = {
            "dir": str(prepared_dir),
            "manifest_sha256": digest,
            "consistent_with_config": (manifest["config_dataset"] == config["dataset"]
                                       and manifest["config_design"] == config["design"]),
            "roles": {role: len(uids) for role, uids in manifest["roles"].items()},
            "ref_untouched": len(manifest["ref_untouched"]),
            "removal_uids": manifest["removal_group"]["uids"],
            "exclusions": manifest["exclusions"],
            "prompt_duplicates_dropped": manifest["prompt_duplicates_dropped"],
            "enrichment": manifest["enrichment"],
            "exposure": {seed: {"a0_removed_rows_seen": s["a0"]["removed_seen"],
                                "first_divergence_step": s["first_divergence_step"]}
                         for seed, s in streams.items()},
        }
    return out
