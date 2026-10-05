"""Validation of the data config, the recipe and their identities (stdlib only).

Exact key sets and supported values; no defaults are filled, so a setting changes only by
editing a config file, which changes its hash. The data config fixes preparation (sources,
eligibility, expected counts, group composition, prompt banks, seed namespaces, token limits)
and lists its explicit ``amendments`` (corrections made before any outcome, with reasons);
the recipe fixes model, training, generation, scoring and attribution. Recipe fields can be
calibrated in development and must be frozen before confirmation; every run records the
recipe hash, and resumes refuse any change. Seed namespaces state which seeds a role MAY use,
not how many are planned or calibrated.

Optional recipe fields (absent from every recipe written before them, which therefore keep
their exact bytes, hash and meaning):

- ``model.tokenizer`` (``{"repo_id", "revision"}``): the snapshot whose tokenizer turns text
  into ids, when it is not the model's own. A model trained from a base checkpoint (the
  headroom amendment's ``Qwen2.5-1.5B``) then uses the tokenizer the prepared data were
  audited with; every training row and prompt is still checked token for token against that
  audit before use. Without it, the model's own snapshot is the tokenizer, as before.
- ``model.lora.trainable_tokens`` (a list of distinct special-token strings): embedding rows
  trained with the adapter (PEFT ``trainable_token_indices``), resolved to ids with the policy's
  tokenizer; an unknown token or one that is not a single token refuses. With tied embeddings
  the output head's rows change with them (``engine.py``). The trainable count in
  ``expected_trainable_parameters`` then includes the rows once.
- ``generation.harm_samples`` (``{"count", "temperature", "top_p"}``): besides the greedy answer,
  ``count`` sampled answers per ``harm`` bank prompt (prepared data v3), at ``temperature`` with
  ``top_p`` 1.0 (no nucleus truncation), each seeded by (job seed, prompt id, sample index)
  (``runner.sample_seed``). Without it a harm prompt gets its greedy answer only.

``attn_implementation`` may be ``"eager"`` (every recipe before headroom v2) or ``"sdpa"``
(PyTorch scaled-dot-product attention) for the policy and the guard; it is part of the identity.

Optional data-config sections (headroom v2; absent from every data config written before them,
which keep their exact bytes, hash and prepared output). They come together:

- ``extra_sources``: further pinned source files by name, each with its repository, revision,
  path, SHA-256, licence, a ``local`` path under the preparation's ``--sources-root`` and a
  format: ``pku-saferlhf-jsonl``, or ``csv`` with its exact header, the prompt field, an optional
  id and category field and ``keep`` (field -> allowed values; every other record is not a bank
  candidate).
- ``injection``: harmful training rows added to the editable pool from named
  ``pku-saferlhf-jsonl`` sources (``prepare.INJECTION_RULE``): ``percent`` of the asserted
  training rows, rounded half up, must equal ``count``.
- ``eval_banks``: the ``harm`` and ``overrefusal`` prompt banks, each from named ``csv`` sources
  with its development and selector sizes (the hidden part is the rest), optional ``per_source``
  quotas (a stratified split; they sum to those sizes) and an optional asserted eligible count
  (``prepare.EVAL_BANK_RULE``). ``injection.near_duplicate.max_jaccard`` skips a walked candidate
  that nearly repeats an evaluation prompt (``prepare.NEAR_DUPLICATE``).
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from .common import canonical_json, sha256_bytes

__all__ = ["ConfigError", "DATA_KIND", "RECIPE_KIND", "ROLES", "PARTITIONS", "BANKS", "EVAL_BANK_KINDS",
           "SOURCE_FORMATS", "injection_count",
           "NAMESPACES", "INIT", "BATCHING", "LOSS", "ATTRIBUTION_VARIANTS", "ARC_TEMPLATE",
           "validate_data_config", "validate_recipe", "load_data_config", "load_recipe",
           "config_sha256", "training_identity", "checkpoint_table", "checkpoint_names",
           "seed_namespace", "tokenizer_of"]

DATA_KIND = "safety-selection data config"
RECIPE_KIND = "safety-selection recipe"
# Composition columns after "size", in this order. Seed streams are named by these roles, never
# by the raw type strings, so renaming hidden type labels changes no selector-facing output.
ROLES = ("risk", "aligned", "benign")
PARTITIONS = ("dev", "heldout")
BANKS = ("dev", "selector", "hidden")
EVAL_BANK_KINDS = ("harm", "overrefusal")     # optional headroom-v2 banks (``eval_banks``)
SOURCE_FORMATS = ("pku-saferlhf-jsonl", "csv")
V3_SECTIONS = ("extra_sources", "injection", "eval_banks")
NAMESPACES = ("development", "selector", "reference")
ARC_SPLIT_OF_BANK = {"dev": "validation", "selector": "validation", "hidden": "test"}
INIT = "init"
BATCHING = ("consecutive examples of one epoch's order; an epoch's final optimizer step keeps its "
            "actual size; steps never cross epochs")
LOSS = ("per-example mean NLL over response target tokens (response plus end-of-turn), averaged "
        "over the actual examples of each optimizer step")
ATTRIBUTION_VARIANTS = ["checkpoint_gradsim", "adam_diag_preconditioned_dot"]
ARC_TEMPLATE = "arc-easy-mc-v1"
ATTENTION = ("eager", "sdpa")


class ConfigError(ValueError):
    pass


def _keys(obj: object, expected: set[str], where: str) -> dict:
    if not isinstance(obj, dict):
        raise ConfigError(f"{where}: expected an object")
    if set(obj) != expected:
        raise ConfigError(f"{where}: missing {sorted(expected - set(obj))}, "
                          f"unknown {sorted(set(obj) - expected)}")
    return obj


def _int(value: object, where: str, low: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < low:
        raise ConfigError(f"{where}: expected an integer >= {low}")
    return value


def _optional_int(value: object, where: str) -> int | None:
    return None if value is None else _int(value, where)


def _number(value: object, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{where}: expected a number")
    return float(value)


def _text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{where}: expected a non-empty string")
    return value


def _texts(value: object, where: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ConfigError(f"{where}: expected a {'' if allow_empty else 'non-empty '}list")
    for item in value:
        _text(item, f"{where}[]")
    if len(set(value)) != len(value):
        raise ConfigError(f"{where}: entries must be distinct")
    return value


def _hex(value: object, length: int, where: str) -> None:
    if not (isinstance(value, str) and len(value) == length
            and all(c in "0123456789abcdef" for c in value)):
        raise ConfigError(f"{where}: expected {length} lowercase hex characters")


def _fixed(value: object, expected: object, where: str) -> None:
    if value != expected:
        raise ConfigError(f"{where} must be {expected!r} (the only implemented choice)")


def _fraction(value: object, where: str) -> Fraction:
    if not (isinstance(value, list) and len(value) == 2):
        raise ConfigError(f"{where}: expected [numerator, denominator]")
    num, den = _int(value[0], f"{where}[0]", 1), _int(value[1], f"{where}[1]", 1)
    return Fraction(num, den)


def injection_count(percent: str, training_rows: int) -> int:
    """``percent``% of ``training_rows``, rounded half up (exact rational arithmetic)."""
    try:
        share = Fraction(percent)
    except (ValueError, ZeroDivisionError) as exc:
        raise ConfigError(f"injection.percent {percent!r} is not a number") from exc
    if not 0 < share <= 100:
        raise ConfigError("injection.percent must be in (0, 100]")
    value = share * training_rows / 100
    return int(value + Fraction(1, 2))


def _validate_v3(config: dict) -> None:
    present = [k for k in V3_SECTIONS if k in config]
    if not present:
        return
    if len(present) != len(V3_SECTIONS):
        raise ConfigError(f"{', '.join(V3_SECTIONS)} come together (found only {present})")
    sources = config["extra_sources"]
    if not isinstance(sources, dict) or not sources:
        raise ConfigError("extra_sources: expected a non-empty object")
    for name, spec in sources.items():
        where = f"extra_sources.{name}"
        _text(name, where)
        if not isinstance(spec, dict) or spec.get("format") not in SOURCE_FORMATS:
            raise ConfigError(f"{where}.format must be one of {SOURCE_FORMATS}")
        base = {"repo_id", "revision", "file", "sha256", "license", "local", "format"}
        csv_keys = {"header", "prompt_field", "id_field", "category_field", "keep"}
        _keys(spec, base | (csv_keys if spec["format"] == "csv" else set()), where)
        for key in ("repo_id", "file", "license", "local"):
            _text(spec[key], f"{where}.{key}")
        if Path(spec["local"]).is_absolute() or ".." in Path(spec["local"]).parts:
            raise ConfigError(f"{where}.local must be a relative path under the sources root")
        _hex(spec["revision"], 40, f"{where}.revision")
        _hex(spec["sha256"], 64, f"{where}.sha256")
        if spec["format"] == "csv":
            header = _texts(spec["header"], f"{where}.header")
            for key in ("prompt_field", "id_field", "category_field"):
                if spec[key] is not None or key == "prompt_field":
                    if _text(spec[key], f"{where}.{key}") not in header:
                        raise ConfigError(f"{where}.{key} is not a header field")
            if not isinstance(spec["keep"], dict):
                raise ConfigError(f"{where}.keep: expected an object (field -> allowed values)")
            for field, values in spec["keep"].items():
                if field not in header:
                    raise ConfigError(f"{where}.keep: {field!r} is not a header field")
                if (not isinstance(values, list) or not values or len(set(values)) != len(values)
                        or not all(isinstance(v, str) for v in values)):
                    raise ConfigError(f"{where}.keep.{field}: expected a non-empty list of distinct strings")

    def named(names: object, fmt: str, where: str) -> list[str]:
        for name in _texts(names, where):
            if name not in sources or sources[name]["format"] != fmt:
                raise ConfigError(f"{where}: {name!r} is not an extra source of format {fmt}")
        return names

    inj = _keys(config["injection"], {"sources", "min_severity", "percent", "count", "expected", "near_duplicate"},
                "injection")
    near = _keys(inj["near_duplicate"], {"max_jaccard"}, "injection.near_duplicate")
    if not 0 < _number(near["max_jaccard"], "injection.near_duplicate.max_jaccard") <= 1:
        raise ConfigError("injection.near_duplicate.max_jaccard must be in (0, 1]")
    named(inj["sources"], "pku-saferlhf-jsonl", "injection.sources")
    _int(inj["min_severity"], "injection.min_severity", 1)
    _text(inj["percent"], "injection.percent")
    training = sum(config["eligibility"]["expected"]["train"].values())
    if _int(inj["count"], "injection.count", 1) != injection_count(inj["percent"], training):
        raise ConfigError(f"injection.count must be {inj['percent']}% of the {training} asserted training "
                          f"rows, rounded half up ({injection_count(inj['percent'], training)})")
    for key, value in _keys(inj["expected"], {"candidates", "eligible"}, "injection.expected").items():
        _optional_int(value, f"injection.expected.{key}")
    banks = _keys(config["eval_banks"], set(EVAL_BANK_KINDS), "eval_banks")
    used: list[str] = []
    for kind in EVAL_BANK_KINDS:
        keys = {"sources", "dev", "selector", "expected_eligible"}
        if isinstance(banks[kind], dict) and "per_source" in banks[kind]:
            keys = keys | {"per_source"}
        spec = _keys(banks[kind], keys, f"eval_banks.{kind}")
        used += named(spec["sources"], "csv", f"eval_banks.{kind}.sources")
        _int(spec["dev"], f"eval_banks.{kind}.dev", 1)
        _int(spec["selector"], f"eval_banks.{kind}.selector", 1)
        if "per_source" in spec:                       # stratified split (prepare.EVAL_BANK_RULE)
            quotas = _keys(spec["per_source"], set(spec["sources"]), f"eval_banks.{kind}.per_source")
            for name, quota in quotas.items():
                _keys(quota, {"dev", "selector"}, f"eval_banks.{kind}.per_source.{name}")
                _int(quota["dev"], f"eval_banks.{kind}.per_source.{name}.dev", 1)
                _int(quota["selector"], f"eval_banks.{kind}.per_source.{name}.selector", 1)
            for part in ("dev", "selector"):
                if sum(q[part] for q in quotas.values()) != spec[part]:
                    raise ConfigError(f"eval_banks.{kind}.per_source: the {part} quotas must sum to {part}")
        _optional_int(spec["expected_eligible"], f"eval_banks.{kind}.expected_eligible")
    if len(set(used)) != len(used) or set(used) & set(inj["sources"]):
        raise ConfigError("an extra source feeds at most one bank, and never both a bank and the injection")
    unused = set(sources) - set(used) - set(inj["sources"])
    if unused:
        raise ConfigError(f"extra_sources not used by the injection or a bank: {sorted(unused)}")


def validate_data_config(config: dict) -> dict:
    """Raise ConfigError unless the data config is complete and supported; returns it."""
    _keys(config, {"kind", "name", "purpose", "amendments", "sources", "eligibility", "roles",
                   "provenance", "design_seed", "groups", "banks", "seed_namespaces", "tokenizer"}
          | {k for k in V3_SECTIONS if k in config}, "data config")
    _fixed(config["kind"], DATA_KIND, "kind")
    _text(config["name"], "name")
    _text(config["purpose"], "purpose")
    _texts(config["amendments"], "amendments", allow_empty=True)
    src = _keys(config["sources"], {"date_lm", "toxicchat", "arc_easy"}, "sources")
    date = _keys(src["date_lm"], {"repo_id", "revision", "train_file", "train_sha256", "ref_file",
                                  "ref_sha256"}, "sources.date_lm")
    tc = _keys(src["toxicchat"], {"repo_id", "revision", "file", "sha256", "header"},
               "sources.toxicchat")
    arc = _keys(src["arc_easy"], {"repo_id", "revision", "validation_parquet",
                                  "validation_parquet_sha256", "validation_jsonl_sha256",
                                  "test_parquet", "test_parquet_sha256", "test_jsonl_sha256"},
                "sources.arc_easy")
    for where, section in (("date_lm", date), ("toxicchat", tc), ("arc_easy", arc)):
        _text(section["repo_id"], f"sources.{where}.repo_id")
        _hex(section["revision"], 40, f"sources.{where}.revision")
        for key, value in section.items():
            if key.endswith("sha256"):
                _hex(value, 64, f"sources.{where}.{key}")
            elif key.endswith(("_file", "_parquet")) or key == "file":
                _text(value, f"sources.{where}.{key}")
    header = _texts(tc["header"], "sources.toxicchat.header")
    if not {"conv_id", "user_input", "toxicity"} <= set(header):
        raise ConfigError("sources.toxicchat.header must include conv_id, user_input, toxicity")

    elig = _keys(config["eligibility"], {"forbidden_substrings", "min_source_id_substring_chars",
                                         "expected"}, "eligibility")
    _texts(elig["forbidden_substrings"], "eligibility.forbidden_substrings")
    _int(elig["min_source_id_substring_chars"], "eligibility.min_source_id_substring_chars", 1)
    exp = _keys(elig["expected"], {"train", "ref", "toxicchat", "arc"}, "eligibility.expected")
    for role in _keys(exp["train"], set(ROLES), "eligibility.expected.train"):
        _int(exp["train"][role], f"eligibility.expected.train.{role}")
    _int(exp["ref"], "eligibility.expected.ref", 1)
    for key, value in _keys(exp["toxicchat"], {"toxic", "nontoxic"},
                            "eligibility.expected.toxicchat").items():
        _optional_int(value, f"eligibility.expected.toxicchat.{key}")
    for key, value in _keys(exp["arc"], {"validation", "test"}, "eligibility.expected.arc").items():
        _optional_int(value, f"eligibility.expected.arc.{key}")

    roles = _keys(config["roles"], set(ROLES), "roles")
    if len({_text(roles[r], f"roles.{r}") for r in ROLES}) != len(ROLES):
        raise ConfigError("roles must name distinct raw type labels")
    for role in _keys(config["provenance"], set(ROLES), "provenance"):
        _text(config["provenance"][role], f"provenance.{role}")
    _fixed(config["provenance"], {"risk": "ToxicChat", "aligned": "ToxicChat",
                                  "benign": "UltraChat"}, "provenance")
    _int(config["design_seed"], "design_seed")

    groups = _keys(config["groups"], {"partitions", "composition_columns", "composition",
                                      "forced_dev_uids", "forced_dev_note"}, "groups")
    _fixed(groups["partitions"], list(PARTITIONS), "groups.partitions")
    _fixed(groups["composition_columns"], ["size", *ROLES], "groups.composition_columns")
    comp = groups["composition"]
    if not isinstance(comp, list) or not comp:
        raise ConfigError("groups.composition must be a non-empty list")
    for i, row in enumerate(comp):
        if not (isinstance(row, list) and len(row) == 1 + len(ROLES)):
            raise ConfigError(f"groups.composition[{i}]: expected [size, risk, aligned, benign]")
        size = _int(row[0], f"groups.composition[{i}].size", 1)
        if sum(_int(n, f"groups.composition[{i}][]") for n in row[1:]) != size:
            raise ConfigError(f"groups.composition[{i}]: role counts must sum to size")
    _texts(groups["forced_dev_uids"], "groups.forced_dev_uids", allow_empty=True)
    _text(groups["forced_dev_note"], "groups.forced_dev_note")

    banks = _keys(config["banks"], {"safety", "arc"}, "banks")
    safety = _keys(banks["safety"], {"toxicity", *BANKS}, "banks.safety")
    _fixed(safety["toxicity"], 1, "banks.safety.toxicity")
    for bank in BANKS:
        _int(safety[bank], f"banks.safety.{bank}", 1)
    arc_banks = _keys(banks["arc"], set(BANKS), "banks.arc")
    for bank in BANKS:
        spec = _keys(arc_banks[bank], {"split", "generation", "utility"}, f"banks.arc.{bank}")
        _fixed(spec["split"], ARC_SPLIT_OF_BANK[bank], f"banks.arc.{bank}.split")
        _int(spec["generation"], f"banks.arc.{bank}.generation", 1)
        _int(spec["utility"], f"banks.arc.{bank}.utility", 1)

    spaces = _keys(config["seed_namespaces"], set(NAMESPACES), "seed_namespaces")
    ranges = []
    for name in NAMESPACES:
        span = spaces[name]
        if not (isinstance(span, list) and len(span) == 2):
            raise ConfigError(f"seed_namespaces.{name}: expected [first, last]")
        first, last = _int(span[0], f"seed_namespaces.{name}[0]"), _int(span[1], f"seed_namespaces.{name}[1]")
        if first > last:
            raise ConfigError(f"seed_namespaces.{name}: first must not exceed last")
        ranges.append((first, last, name))
    ranges.sort()
    for (_, last, name), (first, _, other) in zip(ranges, ranges[1:]):
        if first <= last:
            raise ConfigError(f"seed_namespaces {name} and {other} overlap")

    tok = _keys(config["tokenizer"], {"repo_id", "revision", "end_of_turn_token", "max_train_tokens",
                                      "max_prompt_tokens"}, "tokenizer")
    _text(tok["repo_id"], "tokenizer.repo_id")
    _hex(tok["revision"], 40, "tokenizer.revision")
    _text(tok["end_of_turn_token"], "tokenizer.end_of_turn_token")
    _int(tok["max_train_tokens"], "tokenizer.max_train_tokens", 2)
    _int(tok["max_prompt_tokens"], "tokenizer.max_prompt_tokens", 2)
    _validate_v3(config)
    return config


def _checkpoints(train: dict) -> list[tuple[str, Fraction]]:
    items = train["checkpoints"]
    if not isinstance(items, list) or not items:
        raise ConfigError("train.checkpoints must be a non-empty list")
    out = []
    for i, item in enumerate(items):
        _keys(item, {"name", "epochs"}, f"train.checkpoints[{i}]")
        name = _text(item["name"], f"train.checkpoints[{i}].name")
        if name == INIT:
            raise ConfigError(f"train.checkpoints: {INIT!r} is reserved for the initial adapter")
        out.append((name, _fraction(item["epochs"], f"train.checkpoints[{i}].epochs")))
    if len({n for n, _ in out}) != len(out):
        raise ConfigError("train.checkpoints: names must be distinct")
    if any(b <= a for (_, a), (_, b) in zip(out, out[1:])):
        raise ConfigError("train.checkpoints: epochs must be strictly increasing")
    return out


def validate_recipe(recipe: dict) -> dict:
    """Raise ConfigError unless the recipe is complete and supported; returns it."""
    _keys(recipe, {"kind", "name", "purpose", "model", "train", "generation", "arc", "guard",
                   "secondary_toxicity", "attribution"}, "recipe")
    _fixed(recipe["kind"], RECIPE_KIND, "kind")
    _text(recipe["name"], "name")
    _text(recipe["purpose"], "purpose")
    model_keys = {"repo_id", "revision", "architecture", "base_dtype", "trainable_dtype",
                  "attn_implementation", "device", "end_of_turn_token", "stop_tokens", "pad_token",
                  "max_train_tokens", "max_prompt_tokens", "lora"}
    model = recipe["model"]
    if isinstance(model, dict) and "tokenizer" in model:      # the optional field (module doc)
        model_keys = model_keys | {"tokenizer"}
    model = _keys(model, model_keys, "model")
    if "tokenizer" in model:
        tokenizer = _keys(model["tokenizer"], {"repo_id", "revision"}, "model.tokenizer")
        _text(tokenizer["repo_id"], "model.tokenizer.repo_id")
        _hex(tokenizer["revision"], 40, "model.tokenizer.revision")
        if (tokenizer["repo_id"], tokenizer["revision"]) == (model.get("repo_id"), model.get("revision")):
            raise ConfigError("model.tokenizer names the model itself: leave it out instead")
    _text(model["repo_id"], "model.repo_id")
    _hex(model["revision"], 40, "model.revision")
    _text(model["architecture"], "model.architecture")
    _fixed(model["base_dtype"], "bfloat16", "model.base_dtype")
    _fixed(model["trainable_dtype"], "float32", "model.trainable_dtype")
    if model["attn_implementation"] not in ATTENTION:
        raise ConfigError(f"model.attn_implementation must be one of {ATTENTION}")
    # "cpu" exists only for injected ENGINEERING FIXTURE loaders; the real loader refuses it.
    if model["device"] not in ("cuda", "cpu"):
        raise ConfigError("model.device must be 'cuda' (or 'cpu' for fixture loaders only)")
    _text(model["end_of_turn_token"], "model.end_of_turn_token")
    stops = _texts(model["stop_tokens"], "model.stop_tokens")
    if model["end_of_turn_token"] not in stops:
        raise ConfigError("model.stop_tokens must include the end-of-turn token")
    _text(model["pad_token"], "model.pad_token")
    _int(model["max_train_tokens"], "model.max_train_tokens", 2)
    _int(model["max_prompt_tokens"], "model.max_prompt_tokens", 2)
    lora_keys = {"r", "alpha", "dropout", "target_modules", "expected_trainable_parameters"}
    if isinstance(model["lora"], dict) and "trainable_tokens" in model["lora"]:   # optional (module doc)
        lora_keys = lora_keys | {"trainable_tokens"}
    lora = _keys(model["lora"], lora_keys, "model.lora")
    if "trainable_tokens" in lora:
        _texts(lora["trainable_tokens"], "model.lora.trainable_tokens")
    _int(lora["r"], "model.lora.r", 1)
    _int(lora["alpha"], "model.lora.alpha", 1)
    _fixed(lora["dropout"], 0.0, "model.lora.dropout")
    _texts(lora["target_modules"], "model.lora.target_modules")
    _int(lora["expected_trainable_parameters"], "model.lora.expected_trainable_parameters", 1)

    train = _keys(recipe["train"], {"micro_batch", "grad_accum", "batching", "loss", "optimizer",
                                    "lr", "betas", "eps", "weight_decay", "lr_schedule",
                                    "max_grad_norm", "gradient_checkpointing",
                                    "lm_head_chunk_tokens", "checkpoints"}, "train")
    _int(train["micro_batch"], "train.micro_batch", 1)
    _int(train["grad_accum"], "train.grad_accum", 1)
    _fixed(train["batching"], BATCHING, "train.batching")
    _fixed(train["loss"], LOSS, "train.loss")
    _fixed(train["optimizer"], "AdamW", "train.optimizer")
    _fixed(train["lr_schedule"], "constant", "train.lr_schedule")
    for key in ("lr", "eps", "max_grad_norm"):
        if _number(train[key], f"train.{key}") <= 0:
            raise ConfigError(f"train.{key} must be positive")
    if _number(train["weight_decay"], "train.weight_decay") < 0:
        raise ConfigError("train.weight_decay must be >= 0")
    betas = train["betas"]
    if not (isinstance(betas, list) and len(betas) == 2
            and all(0 <= _number(b, "train.betas[]") < 1 for b in betas)):
        raise ConfigError("train.betas must be two numbers in [0, 1)")
    if not isinstance(train["gradient_checkpointing"], bool):
        raise ConfigError("train.gradient_checkpointing must be true or false")
    _int(train["lm_head_chunk_tokens"], "train.lm_head_chunk_tokens", 1)
    names = [n for n, _ in _checkpoints(train)]

    gen_keys = {"decoding", "max_new_tokens", "batch_size"}
    if isinstance(recipe["generation"], dict) and "harm_samples" in recipe["generation"]:   # optional (module doc)
        gen_keys = gen_keys | {"harm_samples"}
    gen = _keys(recipe["generation"], gen_keys, "generation")
    _fixed(gen["decoding"], "greedy", "generation.decoding")
    _int(gen["max_new_tokens"], "generation.max_new_tokens", 1)
    _int(gen["batch_size"], "generation.batch_size", 1)
    if "harm_samples" in gen:
        samples = _keys(gen["harm_samples"], {"count", "temperature", "top_p"}, "generation.harm_samples")
        _int(samples["count"], "generation.harm_samples.count", 1)
        if not 0 < _number(samples["temperature"], "generation.harm_samples.temperature") <= 2:
            raise ConfigError("generation.harm_samples.temperature must be in (0, 2]")
        _fixed(samples["top_p"], 1.0, "generation.harm_samples.top_p")
    arc = _keys(recipe["arc"], {"template", "batch_size"}, "arc")
    _fixed(arc["template"], ARC_TEMPLATE, "arc.template")
    _int(arc["batch_size"], "arc.batch_size", 1)

    guard = _keys(recipe["guard"], {"repo_id", "revision", "architecture", "dtype",
                                    "attn_implementation", "stop_tokens", "pad_token",
                                    "max_input_tokens", "max_new_tokens", "batch_size"}, "guard")
    _text(guard["repo_id"], "guard.repo_id")
    _hex(guard["revision"], 40, "guard.revision")
    _text(guard["architecture"], "guard.architecture")
    _fixed(guard["dtype"], "bfloat16", "guard.dtype")
    if guard["attn_implementation"] not in ATTENTION:
        raise ConfigError(f"guard.attn_implementation must be one of {ATTENTION}")
    _texts(guard["stop_tokens"], "guard.stop_tokens")
    _text(guard["pad_token"], "guard.pad_token")
    _int(guard["max_input_tokens"], "guard.max_input_tokens", 2)
    _int(guard["max_new_tokens"], "guard.max_new_tokens", 1)
    _int(guard["batch_size"], "guard.batch_size", 1)

    tox = recipe["secondary_toxicity"]
    if tox is not None:
        _keys(tox, {"repo_id", "revision", "label", "activation", "max_length", "batch_size",
                    "device", "threshold"}, "secondary_toxicity")
        _text(tox["repo_id"], "secondary_toxicity.repo_id")
        _hex(tox["revision"], 40, "secondary_toxicity.revision")
        _text(tox["label"], "secondary_toxicity.label")
        _fixed(tox["activation"], "sigmoid", "secondary_toxicity.activation")
        _fixed(tox["device"], "cpu", "secondary_toxicity.device")
        _int(tox["max_length"], "secondary_toxicity.max_length", 1)
        _int(tox["batch_size"], "secondary_toxicity.batch_size", 1)
        if not 0 < _number(tox["threshold"], "secondary_toxicity.threshold") <= 1:
            raise ConfigError("secondary_toxicity.threshold must be in (0, 1]")

    attr = _keys(recipe["attribution"], {"checkpoints", "query_bank", "aggregation_dtype",
                                         "variants"}, "attribution")
    for name in _texts(attr["checkpoints"], "attribution.checkpoints"):
        if name not in names:
            raise ConfigError(f"attribution.checkpoints: {name!r} is not a training checkpoint")
    _fixed(attr["query_bank"], "ref", "attribution.query_bank")
    _fixed(attr["aggregation_dtype"], "float64", "attribution.aggregation_dtype")
    _fixed(attr["variants"], ATTRIBUTION_VARIANTS, "attribution.variants")
    return recipe


def load_data_config(path: str | Path) -> dict:
    return validate_data_config(json.loads(Path(path).read_text(encoding="utf-8")))


def load_recipe(path: str | Path) -> dict:
    return validate_recipe(json.loads(Path(path).read_text(encoding="utf-8")))


def config_sha256(config: dict) -> str:
    return sha256_bytes(canonical_json(config))


def training_identity(recipe: dict) -> str:
    """Hash of the sections that determine a training trajectory (model and train)."""
    return sha256_bytes(canonical_json({"model": recipe["model"], "train": recipe["train"]}))


def tokenizer_of(recipe: dict) -> tuple[str, str]:
    """(repo_id, revision) of the snapshot whose tokenizer the policy uses (module doc)."""
    model = recipe["model"]
    source = model.get("tokenizer") or model
    return source["repo_id"], source["revision"]


def checkpoint_table(recipe: dict) -> list[tuple[str, Fraction]]:
    """``init`` (the seeded adapter, step 0) followed by the configured checkpoints."""
    return [(INIT, Fraction(0))] + _checkpoints(recipe["train"])


def checkpoint_names(recipe: dict) -> list[str]:
    return [name for name, _ in checkpoint_table(recipe)]


def seed_namespace(data_config: dict, seed: int) -> str | None:
    for name in NAMESPACES:
        first, last = data_config["seed_namespaces"][name]
        if first <= seed <= last:
            return name
    return None
