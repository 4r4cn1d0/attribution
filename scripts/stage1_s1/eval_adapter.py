"""B10: the pinned "evaluate a saved adapter" script (RS B10; PLAN-S:155; REF R.0.6-R.0.7, R.1.4; LS-08; deadline S1).

It lives outside the engine identity: it imports engine X (472fc7f6...) and changes none of its files. It re-makes an
a0 adapter by the engine's own train-only run-one, accepts it only if it equals the Gate A record, and evaluates it
through the engine's own evaluation function (runner.evaluate_checkpoint: the engine's loaders, codec, generation,
Qwen3Guard scorer and summaries, unchanged), with at most one change:

- **the safety prefix** (reference SP, A6): a pinned instruction text is written at the start of the user turn,
  inside the one user message (OLMo-2 has no system turn), before the user's own text, with the settings' separator.
  It is done by a codec view (PrefixCodec) that the evaluation receives in place of the policy's codec; the prepared
  items get the prefixed prompts' token SHA-256 after their original encoding was checked against the prepared
  token audit. Qwen3Guard always judges an answer against the user's own text.
- **an adapter scale lambda** (reference A7): lora_B <- lambda * lora_B in every adapted matrix; lambda = 1 is no
  change at all.
- **an external adapter transform** (the hook for B11's Safe LoRA): an allowlisted function, pinned by its module's
  SHA-256, that maps the adapter's tensors to new tensors (interface stage1-adapter-transform-v1), or an allowlisted
  transform's output file with its record (the record must name the transform's SHA-256, the source adapter's
  fingerprint, the output file's SHA-256 and the output adapter's fingerprint, and, when the transform pins a
  settings file, that file's SHA-256).

With none of them, an evaluation is the certification mode (D2): it must reproduce the Gate A unit's U exactly; the
compare command applies the settings' gate (LS-08 (a)). Every other evaluation (a reference, or the lambda = 0 and
identity-transform certification points) needs a passing certification report of the settings' certification seed,
made on this engine, this script's code and these certified settings, and runs only in an environment whose pinned
fields equal the certification unit's (LS-08 (a): no reference runs on an uncertified path). While the settings'
over-refusal bank is "open" (addendum sections 7 and 9: the stage-1 primary O bank is the dev 100 plus 400 sealed
PHTest prompts under one answer cap), only certification points run. With the status "oext_pinned" (addendum section
11 point 1), every evaluation, certify included, also runs the shared pinned O-ext evaluation
(scripts/stage1_s1/oext_eval.py, pinned by its module and settings SHA-256 and its cap branch in the settings section
"oext", outside the certified settings) right after the engine's evaluate_checkpoint, on the engine's own dev-100
answers and the sealed PHTest prompts, and writes its three new files beside the engine's 8 evaluation files, so a
certify unit's 8 files stay byte-identical with Gate A; certify records O-ext as a report and never gates on it. While
the O-ext branch is pending W1-18 (section 13), only certify runs, and it runs without O-ext.

Commands (python -B scripts/stage1_s1/eval_adapter.py COMMAND ...):

  check       [--reference SEED=PATH]... [--untuned PATH]   the pinned settings and the reference pins ($0, no model)
  regenerate  --prepared P --recipe REC --seed S --reference PATH --out ROOT
  evaluate    --prepared P --recipe REC --source-run ROOT/run --reference PATH --out DIR --mode MODE
              [--lambda L] [--prefix-file F] [--external NAME [--adapter-file F --adapter-sha256 H
              --adapter-record R --adapter-record-sha256 H]] [--certification-report F --certification-report-sha256 H]
              [--oext-bank F --oext-record F [--w1-18-record F]]
  run         --prepared P --recipe REC --seed S --reference PATH --regen-out ROOT --eval-root DIR
              --evaluations SPEC[,SPEC...] [--prefix-file F] [--gate-reference-eval DIR]
              [--certification-report F --certification-report-sha256 H] [--oext-bank F --oext-record F [--w1-18-record F]]
              (SPEC: certify, prefix, scale:L or external:NAME; one process, one model load; with
              --gate-reference-eval the first SPEC must be certify and nothing else runs unless it passes; the
              in-process report certifies the later SPECs only at the certification seed)
  compare     --unit DIR --reference PATH --reference-eval DIR --out FILE [--against a0|untuned]
  verify      --unit DIR [--map RECORDED=LOCAL]...

PATH is a Gate A unit's COMPLETE.json (only its pinned SHA-256 makes it the reference). Every job writes one new
folder; nothing is overwritten. Printed: ids, counts, hashes and costs only, never text and never an outcome value.

Exit status: 0 done; 1 a job failed after this process wrote into an output path (error.txt kept when a job folder
exists); 2 refused before this process wrote anything (nothing was trained, evaluated or written); 3 the adapter's
fingerprints (or its trajectory, data or training identity) differ from the pinned Gate A record, so the state is
never evaluated; 4 the certification comparison failed (stop every evaluation-only reference until the cause is
known).
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import re
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import experiments.safety_selection as _engine_package  # noqa: E402
from experiments.safety_selection.common import (canonical_json, code_identity, ids_sha256, read_jsonl,  # noqa: E402
                                                 sha256_bytes, sha256_file, write_atomic, write_json)
from experiments.safety_selection.config import config_sha256, training_identity  # noqa: E402
from experiments.safety_selection.ledger import COMPLETE, read_complete, verify_files  # noqa: E402
from experiments.safety_selection.textproc import (Codec, TooLong, encode_generation_prompt, encode_mc,  # noqa: E402
                                                   encode_train, render_arc_mc)
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1_s1 import oext_eval as oe  # noqa: E402

ENGINE_REPO = Path(_engine_package.__file__).resolve().parents[2]   # where the engine's configs live
SETTINGS_PATH = HERE / "settings" / "eval_adapter.json"
SETTINGS_SHA256 = "a99f918f9579458b96d6094981679babc2ccfbe5e6d0d20bd360ccab81fbe1fb"
SETTINGS_NAME = "eval_adapter"
OWNER = "scripts/stage1_s1/eval_adapter.py"
JOB_KIND = "stage1-eval-adapter"
REGEN_KIND = "stage1 a0 regeneration record"
COMPARE_KIND = "stage1 B10 certification comparison"
TRANSFORM_INTERFACE = "stage1-adapter-transform-v1"
MODES = ("certify", "prefix", "scale", "external")
PREFIX_KINDS = ("harm", "overrefusal", "safety", "arc_generation", "arc_utility", "task_rows")
GENERATION_KINDS = ("safety", "arc_generation", "harm", "overrefusal")      # runner.GENERATION_KINDS (a test pins it)
EXIT_OK, EXIT_FAILED, EXIT_REFUSED, EXIT_MISMATCH, EXIT_CERTIFICATION = 0, 1, 2, 3, 4
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX_PREFIX = re.compile(r"^[0-9a-f]{16,64}$")
NAME = re.compile(r"^[a-z0-9_]{1,40}$")
RECORD_MAX_BYTES = 1_000_000
RECORD_MAX_STRING = 200
EXPECTED_EXIT_CODES = {"0", "1", "2", "3", "4"}
SETTINGS_KEYS = frozenset({"adapter_scale", "certification", "checkpoint", "combination_rule", "engine_x",
                           "evaluation", "exit_codes", "external_transforms", "kind", "label_entries", "label_note",
                           "labels_sha256", "name", "oext", "outputs", "overrefusal_bank", "owner", "prefix", "prepared",
                           "recipe", "reference_units", "regeneration", "requirement", "untuned_unit", "version"})
REGEN_JOB = {"arm": "a0", "evaluate_bank": None, "pin_code": True, "replicate_of": None, "resume_from": None,
             "role": "development", "split": "dev"}
# what an identity field of a COMPLETE.json must equal: the settings value at this path
IDENTITY_PINS = {"manifest_sha256": ("prepared", "manifest_sha256"), "recipe_sha256": ("recipe", "config_sha256"),
                 "training_identity": ("recipe", "training_identity")}
REQUIRED_IDENTITY = frozenset({"manifest_sha256", "training_identity"})   # the data and the training trajectory
EXTERNAL_KEYS = frozenset({"kind", "module", "module_sha256", "function", "settings", "record_keys",
                           "require_lora_a_unchanged", "role"})
RECORD_KEYS = frozenset({"transform_sha256", "source_adapter_fingerprint", "output_adapter_fingerprint",
                         "output_file_sha256"})
SETTINGS_RECORD_KEY = "transform_settings_sha256"           # required for a file transform that pins its settings
JOB_KEYS = frozenset({"kind", "manifest_sha256", "recipe_sha256", "code_sha256", "wall_limit_seconds", "source_run",
                      "checkpoint", "evaluate_bank", "seed", "reference_complete_sha256", "mode", "adapter_scale",
                      "prefix_sha256", "external", "settings_sha256", "script_sha256",
                      "certification_report_sha256", "oext"})
OEXT_JOB_KEYS = frozenset({"branch", "settings_sha256", "module_sha256", "record_sha256", "bank_sha256",
                           "w1_18_record_sha256"})
OEXT_KEYS = frozenset({"module", "module_sha256", "settings", "branch", "outputs", "rule"})
OEXT_SETTINGS_PATH = "scripts/stage1_s1/settings/oext_eval.json"
# the over-refusal bank: "open" = the stage-1 primary O bank (addendum sections 7 and 9) is not built into B10, so
# only certification points run; "dev100_recipe_cap" = the lead recorded that the references report O on the dev
# 100 at the recipe's generation cap (the fallback; a pre-registration line); "oext_pinned" = every evaluation also
# runs the shared O-ext evaluation of the settings section "oext" (addendum section 11 point 1)
OBANK_STATUSES = ("open", "dev100_recipe_cap", "oext_pinned")
# the settings sections a certification certifies (with the certification seed's reference pin): a change in any
# of them needs a new certification; the prefix text, the scale points, the transform allowlist, the over-refusal
# bank status and the texts do not touch the certify path
CERTIFIED_SETTINGS_KEYS = ("engine_x", "recipe", "prepared", "checkpoint", "regeneration", "evaluation",
                           "certification")
ENVIRONMENT_ROOTS = ("environment", "environment_lock")      # the two assets.json records environment_fields name

Refusal = s1.Refusal


class Mismatch(s1.Refusal):
    """The adapter's fingerprints (or its trajectory, data or recipe) differ from the pinned Gate A record."""


_MISSING = object()


# ----- small checks ----------------------------------------------------------------------------------------------


def _hex64(value: Any, what: str) -> str:
    if not (isinstance(value, str) and HEX64.match(value)):
        raise Refusal(f"{what} is not a SHA-256")
    return value


def _keys(obj: Any, expected: Sequence[str] | frozenset, what: str) -> dict:
    if not isinstance(obj, dict) or set(obj) != set(expected):
        raise Refusal(f"{what} does not hold exactly the keys {sorted(expected)}")
    return obj


def _text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Refusal(f"{what} is empty or not text")
    return value


def _names(value: Any, what: str, allowed: Sequence[str] | None = None) -> list[str]:
    if not (isinstance(value, list) and value and all(isinstance(v, str) and v for v in value)
            and len(set(value)) == len(value)):
        raise Refusal(f"{what} is not a non-empty list of distinct names")
    if allowed is not None and not set(value) <= set(allowed):
        raise Refusal(f"{what} names something outside {sorted(allowed)}")
    return value


def _number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _get(node: Any, *path: str) -> Any:
    for part in path:
        if not isinstance(node, Mapping) or part not in node:
            return _MISSING
        node = node[part]
    return node


def _repo_file(relative: str, root: Path, what: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise Refusal(f"{what} must be a path inside the repository")
    return root / path


# ----- settings --------------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Settings:
    doc: dict
    sha256: str


def _check_external(name: str, entry: Any) -> None:
    what = f"external transform {name}"
    if not NAME.match(name):
        raise Refusal(f"external transform name {name!r} is not a short id")
    _keys(entry, EXTERNAL_KEYS, what)
    if entry["kind"] not in ("callable", "file"):
        raise Refusal(f"{what}: kind must be callable or file")
    module = _text(entry["module"], f"{what} module")
    if not (module.startswith("scripts/") and module.endswith(".py")) or ".." in Path(module).parts:
        raise Refusal(f"{what}: the module must be a scripts/ Python file")
    _hex64(entry["module_sha256"], f"{what} module_sha256")
    if entry["kind"] == "callable":
        if not (isinstance(entry["function"], str) and entry["function"].isidentifier()):
            raise Refusal(f"{what}: function must name a Python function")
        if entry["record_keys"] is not None:
            raise Refusal(f"{what}: a callable transform has no file record")
    else:
        if entry["function"] is not None:
            raise Refusal(f"{what}: a file transform names no function")
        expected = RECORD_KEYS | ({SETTINGS_RECORD_KEY} if entry["settings"] is not None else set())
        keys = _keys(entry["record_keys"], expected, f"{what} record_keys (a pinned settings file needs "
                                                     f"{SETTINGS_RECORD_KEY})")
        for key, value in keys.items():
            _text(value, f"{what} record_keys.{key}")
    if entry["settings"] is not None:
        pin = _keys(entry["settings"], {"path", "sha256"}, f"{what} settings")
        _text(pin["path"], f"{what} settings path")
        _hex64(pin["sha256"], f"{what} settings sha256")
    if not isinstance(entry["require_lora_a_unchanged"], bool):
        raise Refusal(f"{what}: require_lora_a_unchanged must be true or false")
    _text(entry["role"], f"{what} role")


def validate_settings(doc: Any) -> dict:
    """The B10 settings: s1common's check (kind, name, the registry entries it names, engine X), then every key."""
    doc = s1.check_settings(doc, SETTINGS_NAME)
    _keys(doc, SETTINGS_KEYS, "the eval_adapter settings")
    if doc["version"] != 1 or doc["owner"] != OWNER:
        raise Refusal("the eval_adapter settings are not version 1 of this script's")
    if doc["label_entries"] != {}:
        raise Refusal("B10 draws no random number: its settings name no registry entry")
    for field in ("requirement", "label_note", "combination_rule"):
        _text(doc[field], f"settings {field}")
    recipe = _keys(doc["recipe"], {"path", "file_sha256", "config_sha256", "training_identity"}, "settings recipe")
    _text(recipe["path"], "settings recipe path")
    for key in ("file_sha256", "config_sha256", "training_identity"):
        _hex64(recipe[key], f"settings recipe {key}")
    prepared = _keys(doc["prepared"], {"manifest_sha256", "bank"}, "settings prepared")
    _hex64(prepared["manifest_sha256"], "settings prepared manifest_sha256")
    if prepared["bank"] != "dev":
        raise Refusal("B10 evaluates the dev bank only")
    if doc["checkpoint"] != "e1":
        raise Refusal("B10 evaluates the e1 state (the main study's checkpoint)")
    regen = _keys(doc["regeneration"], {"job", "registry", "compare_trajectory", "compare_checkpoints",
                                        "compare_checkpoint_fields", "report_checkpoint_fields", "compare_identity",
                                        "report_identity", "rule"}, "settings regeneration")
    if regen["job"] != REGEN_JOB:
        raise Refusal("the regeneration job is not the a0 development train-only run-one")
    if regen["registry"] is not None:
        raise Refusal("a regeneration claims no trajectory (registry null)")
    _names(regen["compare_trajectory"], "regeneration compare_trajectory")
    if not {"q", "e1"} <= set(_names(regen["compare_checkpoints"], "regeneration compare_checkpoints")):
        raise Refusal("the regeneration must compare the q and e1 checkpoints")
    if "adapter_fingerprint" not in _names(regen["compare_checkpoint_fields"], "regeneration checkpoint fields"):
        raise Refusal("the regeneration must compare the adapter fingerprints")
    _names(regen["report_checkpoint_fields"], "regeneration report fields")
    compared = set(_names(regen["compare_identity"], "regeneration compare_identity", sorted(IDENTITY_PINS)))
    if not REQUIRED_IDENTITY <= compared:
        raise Refusal("the regeneration must compare the data (manifest) and the training identity")
    reported = regen["report_identity"]
    if not (isinstance(reported, list) and len(set(reported)) == len(reported)
            and set(reported) <= set(IDENTITY_PINS) - compared):
        raise Refusal("regeneration report_identity must be distinct identity fields that are not compared")
    _text(regen["rule"], "regeneration rule")
    refs = doc["reference_units"]
    if not isinstance(refs, dict) or not refs:
        raise Refusal("settings reference_units is empty")
    for seed, entry in refs.items():
        if not seed.isdigit():
            raise Refusal(f"reference unit key {seed!r} is not a seed")
        _keys(entry, {"unit", "complete_sha256", "fingerprint_prefixes", "role"}, f"reference unit {seed}")
        _text(entry["unit"], f"reference unit {seed} path")
        _hex64(entry["complete_sha256"], f"reference unit {seed} complete_sha256")
        prefixes = entry["fingerprint_prefixes"]
        if (not isinstance(prefixes, dict) or "e1" not in prefixes
                or not set(prefixes) <= set(regen["compare_checkpoints"])):
            raise Refusal(f"reference unit {seed}: fingerprint_prefixes must name e1 and only compared checkpoints")
        for name, prefix in prefixes.items():
            if not (prefix is None and name != "e1") and not (isinstance(prefix, str) and HEX_PREFIX.match(prefix)):
                raise Refusal(f"reference unit {seed}: the {name} fingerprint prefix is not 16-64 hex")
        _text(entry["role"], f"reference unit {seed} role")
    untuned = _keys(doc["untuned_unit"], {"unit", "complete_sha256", "seed", "checkpoint", "role"}, "untuned_unit")
    _hex64(untuned["complete_sha256"], "untuned_unit complete_sha256")
    if untuned["checkpoint"] != "init" or str(untuned["seed"]) not in refs:
        raise Refusal("the untuned unit is the init unit of a pinned reference seed")
    scale = _keys(doc["adapter_scale"], {"allowed", "planned", "curve", "factor", "rule"}, "adapter_scale")
    allowed = scale["allowed"]
    if not (isinstance(allowed, list) and allowed and all(_number(v) and 0 <= v <= 1 for v in allowed)
            and len(set(allowed)) == len(allowed) and 1.0 in allowed):
        raise Refusal("adapter_scale allowed must be distinct numbers in [0, 1] including 1")
    for key in ("planned", "curve"):
        values = scale[key]
        if not (isinstance(values, list) and values and all(_number(v) and v in allowed for v in values)):
            raise Refusal(f"adapter_scale {key} must be allowed values")
    if 1.0 in scale["planned"]:
        raise Refusal("lambda = 1 is the certification mode, not a planned scale point")
    if scale["factor"] != "lora_B":
        raise Refusal("adapter scaling multiplies lora_B")
    prefix = _keys(doc["prefix"], {"text_sha256", "source", "separator", "apply_to", "guard_sees", "status"},
                   "settings prefix")
    if prefix["text_sha256"] is not None:
        _hex64(prefix["text_sha256"], "prefix text_sha256")
        _text(prefix["source"], "prefix source (a pinned text needs its citation)")
    if not isinstance(prefix["separator"], str) or prefix["separator"].strip() or len(prefix["separator"]) > 8:
        raise Refusal("the prefix separator must be at most 8 whitespace characters")
    _names(prefix["apply_to"], "prefix apply_to", PREFIX_KINDS)
    if prefix["guard_sees"] != "original user text":
        raise Refusal("Qwen3Guard judges the answer against the user's own text")
    externals = doc["external_transforms"]
    if not isinstance(externals, dict):
        raise Refusal("external_transforms is not an object")
    for name, entry in externals.items():
        _check_external(name, entry)
    evaluation = _keys(doc["evaluation"], {"bank", "job_seed", "rule"}, "settings evaluation")
    if evaluation["bank"] != "dev" or evaluation["job_seed"] != "source run seed":
        raise Refusal("the evaluation reads the dev bank with the source run's seed")
    cert = _keys(doc["certification"], {"seed", "mode", "gate", "gate_fields", "expected_sampled_answers",
                                        "required_reference_files", "diagnostic_reference_files", "failure_action",
                                        "environment_fields", "reference_rule"}, "settings certification")
    if str(cert["seed"]) not in refs or cert["mode"] != "certify":
        raise Refusal("the certification runs the certify mode on a pinned reference seed")
    if not {"valid", "safety"} <= set(_names(cert["gate_fields"], "certification gate_fields")):
        raise Refusal("the certification gate compares the valid flag and the Safety label")
    count = cert["expected_sampled_answers"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise Refusal("certification expected_sampled_answers must be a positive integer")
    if "guard_samples.jsonl" not in _names(cert["required_reference_files"], "certification required files"):
        raise Refusal("the certification reads the reference guard_samples.jsonl")
    _names(cert["diagnostic_reference_files"], "certification diagnostic files")
    for field in ("gate", "failure_action", "reference_rule"):
        _text(cert[field], f"certification {field}")
    fields = _names(cert["environment_fields"], "certification environment_fields")
    if not all(f.split(".", 1)[0] in ENVIRONMENT_ROOTS and "." in f for f in fields):
        raise Refusal(f"each certification environment field is a dotted path under {list(ENVIRONMENT_ROOTS)}")
    if "environment_lock.sha256" not in fields:
        raise Refusal("the certification environment includes the pod's lock record (environment_lock.sha256)")
    obank = _keys(doc["overrefusal_bank"], {"status", "rule"}, "settings overrefusal_bank")
    if obank["status"] not in OBANK_STATUSES:
        raise Refusal(f"overrefusal_bank status must be one of {list(OBANK_STATUSES)}")
    _text(obank["rule"], "overrefusal_bank rule")
    oext = _keys(doc["oext"], OEXT_KEYS, "settings oext")
    if oext["module"] != oe.OWNER:
        raise Refusal(f"settings oext: the module is {oe.OWNER}")
    _hex64(oext["module_sha256"], "settings oext module_sha256")
    pin = _keys(oext["settings"], {"path", "sha256"}, "settings oext settings")
    if pin["path"] != OEXT_SETTINGS_PATH:
        raise Refusal(f"settings oext: the settings file is {OEXT_SETTINGS_PATH}")
    _hex64(pin["sha256"], "settings oext settings sha256")
    if oext["branch"] not in oe.BRANCHES:
        raise Refusal(f"settings oext: branch must be one of {list(oe.BRANCHES)}")
    if oext["outputs"] != list(oe.OUTPUT_FILES):
        raise Refusal("settings oext: the outputs are the O-ext module's three files")
    _text(oext["rule"], "settings oext rule")
    if set(doc["exit_codes"]) != EXPECTED_EXIT_CODES or not isinstance(doc["outputs"], dict):
        raise Refusal("settings exit_codes or outputs are not this script's")
    return doc


def settings_from_doc(doc: Any) -> Settings:
    """A validated settings document named by the SHA-256 of its canonical bytes (tests, and records)."""
    return Settings(validate_settings(doc), sha256_bytes(canonical_json(doc)))


def load_pinned_settings(path: str | Path = SETTINGS_PATH) -> Settings:
    doc, digest = s1.load_settings(path, SETTINGS_SHA256, SETTINGS_NAME)
    return Settings(validate_settings(doc), digest)


# ----- the Gate A reference --------------------------------------------------------------------------------------


def _identity_pin(settings: Settings, key: str) -> str:
    section, field = IDENTITY_PINS[key]
    return settings.doc[section][field]


def _check_identity(marker: Mapping, settings: Settings, what: str) -> None:
    """The marker's compared identity fields (the data and the training identity; the recipe's config hash too if
    the settings compare it) equal the settings' pins; report_identity fields are not required (LS-04 (b))."""
    expected = {k: _identity_pin(settings, k) for k in settings.doc["regeneration"]["compare_identity"]}
    wrong = sorted(k for k, v in expected.items() if _get(marker, "identity", k) != v)
    if wrong:
        raise Refusal(f"{what}: its identity differs from the settings in {wrong}")


def read_reference(path: str | Path, seed: int, settings: Settings) -> dict:
    """The pinned Gate A unit of a seed: its COMPLETE.json bytes must hash to the settings' pin; it must be a complete
    a0 development run-one at the settings' checkpoint on the pinned data and recipe; its adapter fingerprints must
    start with the pinned prefixes."""
    doc = settings.doc
    entry = doc["reference_units"].get(str(seed))
    if entry is None:
        raise Refusal(f"no Gate A reference unit is pinned for seed {seed}")
    try:
        data = Path(path).read_bytes()
    except OSError:
        raise Refusal(f"the reference COMPLETE.json for seed {seed} cannot be read") from None
    digest = sha256_bytes(data)
    if digest != entry["complete_sha256"]:
        raise Refusal(f"the reference COMPLETE.json for seed {seed} hashes to {digest}, the settings pin "
                      f"{entry['complete_sha256']}")
    marker = s1.strict_json(data)
    if not isinstance(marker, dict) or marker.get("complete") is not True or marker.get("kind") != "run-one":
        raise Refusal(f"the reference for seed {seed} is not a complete run-one")
    if marker.get("target_checkpoint") != doc["checkpoint"]:
        raise Refusal(f"the reference for seed {seed} is not an {doc['checkpoint']} unit")
    expected = {"split": "dev", "arm": "a0", "seed": seed, "role": "development"}
    if any(_get(marker, "trajectory", k) != v for k, v in expected.items()):
        raise Refusal(f"the reference for seed {seed} is not the a0 development trajectory of that seed")
    _check_identity(marker, settings, f"the reference for seed {seed}")
    for name in doc["regeneration"]["compare_checkpoints"]:
        if not isinstance(_get(marker, "checkpoints", name, "adapter_fingerprint"), str):
            raise Refusal(f"the reference for seed {seed} holds no {name} adapter fingerprint")
    for name, prefix in entry["fingerprint_prefixes"].items():
        if prefix is not None and not _get(marker, "checkpoints", name, "adapter_fingerprint").startswith(prefix):
            raise Refusal(f"the reference for seed {seed}: its {name} fingerprint does not start with the pinned "
                          "prefix")
    return {"seed": seed, "complete_sha256": digest, "marker": marker}


def read_untuned(path: str | Path, settings: Settings) -> dict:
    """The pinned Gate A untuned unit (theta0): the lambda = 0 point's optional certification reference."""
    entry = settings.doc["untuned_unit"]
    try:
        data = Path(path).read_bytes()
    except OSError:
        raise Refusal("the untuned unit's COMPLETE.json cannot be read") from None
    digest = sha256_bytes(data)
    if digest != entry["complete_sha256"]:
        raise Refusal(f"the untuned unit's COMPLETE.json hashes to {digest}, the settings pin "
                      f"{entry['complete_sha256']}")
    marker = s1.strict_json(data)
    expected = {"split": "dev", "arm": "a0", "seed": entry["seed"], "role": "development"}
    if (not isinstance(marker, dict) or marker.get("complete") is not True or marker.get("kind") != "run-one"
            or marker.get("target_checkpoint") != entry["checkpoint"]
            or any(_get(marker, "trajectory", k) != v for k, v in expected.items())):
        raise Refusal("the untuned unit is not the complete a0 init unit of its seed")
    _check_identity(marker, settings, "the untuned unit")
    return {"seed": entry["seed"], "complete_sha256": digest, "marker": marker}


def fingerprint_report(candidate: Mapping, reference: Mapping, settings: Settings) -> dict:
    """Every required field of a candidate run's COMPLETE.json against the reference's (a field missing on either
    side is unequal), the report-only fields, and both sides' adapter fingerprints (hashes only)."""
    regen = settings.doc["regeneration"]
    required: dict[str, bool] = {}
    report: dict[str, bool] = {}

    def same(*path: str) -> bool:
        a, b = _get(candidate, *path), _get(reference, *path)
        return a is not _MISSING and b is not _MISSING and a == b

    for key in regen["compare_trajectory"]:
        required[f"trajectory.{key}"] = same("trajectory", key)
    for name in regen["compare_checkpoints"]:
        for field in regen["compare_checkpoint_fields"]:
            required[f"checkpoints.{name}.{field}"] = same("checkpoints", name, field)
        for field in regen["report_checkpoint_fields"]:
            report[f"checkpoints.{name}.{field}"] = same("checkpoints", name, field)
    for key in regen["compare_identity"]:
        required[f"identity.{key}"] = same("identity", key)
    for key in regen["report_identity"]:
        report[f"identity.{key}"] = same("identity", key)

    def value(marker: Mapping, name: str) -> Any:
        found = _get(marker, "checkpoints", name, "adapter_fingerprint")
        return None if found is _MISSING else found

    return {"equal": all(required.values()), "differing": sorted(k for k, ok in required.items() if not ok),
            "required": required, "report_only": report,
            "adapter_fingerprints": {name: {"candidate": value(candidate, name), "reference": value(reference, name)}
                                     for name in regen["compare_checkpoints"]}}


# ----- the recipe and the data -----------------------------------------------------------------------------------


def check_recipe(recipe: Mapping, settings: Settings) -> None:
    doc = settings.doc["recipe"]
    if config_sha256(recipe) != doc["config_sha256"] or training_identity(recipe) != doc["training_identity"]:
        raise Refusal("the recipe is not the one the settings pin (config or training identity)")
    lora = recipe["model"]["lora"]
    if "trainable_tokens" in lora:
        raise Refusal("B10 scales and transforms LoRA matrices only; a recipe with trained token rows refuses")


def load_pinned_recipe(path: str | Path, settings: Settings) -> dict:
    from experiments.safety_selection.config import load_recipe

    digest = sha256_file(path)
    if digest != settings.doc["recipe"]["file_sha256"]:
        raise Refusal(f"the recipe file hashes to {digest}, the settings pin {settings.doc['recipe']['file_sha256']}")
    recipe = load_recipe(path)
    check_recipe(recipe, settings)
    return recipe


def read_pinned_manifest(prepared_dir: str | Path, settings: Settings) -> tuple[dict, str]:
    from experiments.safety_selection.prepare import read_manifest
    from experiments.safety_selection.sources import DataError

    try:
        return read_manifest(prepared_dir, settings.doc["prepared"]["manifest_sha256"])
    except (DataError, OSError) as exc:
        raise Refusal(f"the prepared set is not the pinned one: {type(exc).__name__}: {exc}") from None


def stage_seconds(run_dir: str | Path) -> dict[str, float]:
    """The ledger's seconds per stage name (stages that ended ok), summed."""
    out: Counter = Counter()
    for record in read_jsonl(Path(run_dir) / "ledger.jsonl"):
        if record.get("status") == "ok":
            out[record["stage"]] += float(record["seconds"])
    return dict(sorted(out.items()))


# ----- regeneration ----------------------------------------------------------------------------------------------


def regenerate(*, prepared_dir: str | Path, seed: int, reference_path: str | Path, out_root: str | Path,
               session: Any, settings: Settings, wall_limit_seconds: float | None = None) -> dict:
    """Re-make one a0 adapter by the engine's own train-only run-one (no evaluation, no registry claim) and compare
    its COMPLETE.json with the pinned Gate A record. Writes ROOT/job.json, ROOT/run/ and ROOT/regeneration.json;
    returns the record (verdict "match" or "mismatch")."""
    from experiments.safety_selection import runner
    from experiments.safety_selection.planning import make_job

    reference = read_reference(reference_path, seed, settings)
    check_recipe(session.recipe, settings)
    read_pinned_manifest(prepared_dir, settings)
    out_root = Path(out_root)
    if out_root.exists() and any(out_root.iterdir()):
        raise Refusal(f"{out_root} exists and is not empty: a regeneration never overwrites")
    out_root.mkdir(parents=True, exist_ok=True)
    spec = settings.doc["regeneration"]["job"]
    job = make_job("run-one", prepared_dir=prepared_dir, recipe=session.recipe, pin_code=spec["pin_code"],
                   out=out_root / "job.json", wall_limit_seconds=wall_limit_seconds, split=spec["split"],
                   arm=spec["arm"], seed=seed, role=spec["role"], target_checkpoint=settings.doc["checkpoint"],
                   evaluate_bank=spec["evaluate_bank"], resume_from=spec["resume_from"],
                   replicate_of=spec["replicate_of"])
    run_dir = out_root / "run"
    runner.run_one(job, prepared_dir=prepared_dir, out_dir=run_dir, session=session)      # registry None: no claim
    marker = read_complete(run_dir)
    report = fingerprint_report(marker, reference["marker"], settings)
    record = {"kind": REGEN_KIND, "version": 1, "seed": seed, "verdict": "match" if report["equal"] else "mismatch",
              "run": "run", "run_complete_sha256": sha256_file(run_dir / COMPLETE),
              "job_sha256": sha256_file(out_root / "job.json"),
              "reference_complete_sha256": reference["complete_sha256"], "comparison": report,
              "train_cost": marker["trajectory_cost"], "stage_seconds": stage_seconds(run_dir),
              "provenance": s1.provenance(Path(__file__).resolve(), settings.sha256,
                                          {"reference_complete": reference["complete_sha256"],
                                           "run_complete": sha256_file(run_dir / COMPLETE)}, {})}
    write_atomic(out_root / "regeneration.json", canonical_json(record))
    return record


# ----- what one evaluation changes -------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Plan:
    mode: str
    adapter_scale: float = 1.0
    prefix_file: str | None = None
    external: str | None = None
    adapter_file: str | None = None
    adapter_sha256: str | None = None
    record_file: str | None = None
    record_sha256: str | None = None

    @property
    def label(self) -> str:
        if self.mode == "scale":
            return f"scale-{self.adapter_scale:g}"
        if self.mode == "external":
            return f"external-{self.external}"
        return self.mode


def make_plan(settings: Settings, mode: str, *, adapter_scale: Any = None, prefix_file: str | None = None,
              external: str | None = None, adapter_file: str | None = None, adapter_sha256: str | None = None,
              record_file: str | None = None, record_sha256: str | None = None) -> Plan:
    """One evaluation's change, checked against the combination rule: at most one of the prefix, a scale other than
    1 and one external transform; none of them is the certification mode."""
    doc = settings.doc
    if mode not in MODES:
        raise Refusal(f"mode {mode!r} is not one of {list(MODES)}")
    lam = 1.0 if adapter_scale is None else adapter_scale
    if not _number(lam):
        raise Refusal("the adapter scale must be a finite number")
    lam = float(lam)
    file_args = (adapter_file, adapter_sha256, record_file, record_sha256)
    if mode != "scale" and lam != 1.0:
        raise Refusal("an adapter scale other than 1 is the scale mode only (one change per evaluation)")
    if mode != "prefix" and prefix_file is not None:
        raise Refusal("a prefix file is the prefix mode only (one change per evaluation)")
    if mode != "external" and (external is not None or any(a is not None for a in file_args)):
        raise Refusal("an external transform is the external mode only (one change per evaluation)")
    if mode == "scale":
        if lam == 1.0:
            raise Refusal("lambda = 1 is the certification mode")
        if lam not in doc["adapter_scale"]["allowed"]:
            raise Refusal(f"lambda = {lam:g} is not an allowed scale {doc['adapter_scale']['allowed']}")
    if mode == "prefix":
        if doc["prefix"]["text_sha256"] is None:
            raise Refusal("the safety prefix text is not pinned yet (C1): the prefix mode cannot run")
        if prefix_file is None:
            raise Refusal("the prefix mode needs the prefix file")
    if mode == "external":
        entry = doc["external_transforms"].get(external) if external is not None else None
        if entry is None:
            raise Refusal(f"external transform {external!r} is not allowlisted in the settings")
        if entry["kind"] == "file" and any(a is None for a in file_args):
            raise Refusal(f"external transform {external} is a file transform: it needs the adapter file, its "
                          "SHA-256, its record and the record's SHA-256")
        if entry["kind"] == "callable" and any(a is not None for a in file_args):
            raise Refusal(f"external transform {external} is a callable: it takes no adapter file")
        for value in (adapter_sha256, record_sha256):
            if value is not None:
                _hex64(value, "an adapter or record SHA-256")
    if doc["overrefusal_bank"]["status"] == "open" and (
            mode == "prefix" or (mode == "scale" and lam != 0.0)
            or (mode == "external" and doc["external_transforms"][external]["kind"] == "callable")):
        raise Refusal(OBANK_OPEN)
    if doc["overrefusal_bank"]["status"] == "oext_pinned" and doc["oext"]["branch"] == oe.PENDING and mode != "certify":
        raise Refusal(OEXT_PENDING)
    return Plan(mode, lam, prefix_file, external, adapter_file, adapter_sha256, record_file, record_sha256)


OBANK_OPEN = ("the over-refusal bank is open (settings overrefusal_bank; addendum sections 7 and 9): the stage-1 "
              "primary O bank (the dev 100 plus 400 sealed PHTest prompts under one answer cap) is not built into "
              "B10, so only certification points run (certify, lambda = 0, an identity transform file)")
OEXT_PENDING = ("the O-ext cap branch is pending W1-18 (settings oext.branch; addendum section 13: W1-18 runs as the "
                "first job of the first stage-1 pod): every evaluation other than certify refuses, and certify runs "
                "without O-ext")


def check_oext(settings: Settings, modes: Sequence[str], oext: Any) -> Any:
    """The O-ext part of an evaluation (addendum section 11 point 1): with the over-refusal bank status oext_pinned,
    ``oext`` (oext_eval.prepare's result) must be the pinned module, the pinned settings and the pinned branch; under
    the pending branch only certify runs. With another status no O-ext input is taken. Returns ``oext`` or None."""
    doc = settings.doc
    status = doc["overrefusal_bank"]["status"]
    if status != "oext_pinned":
        if oext is not None:
            raise Refusal(f"O-ext inputs were given, but the over-refusal bank status is {status!r}")
        return None
    if oext is None:
        raise Refusal("the over-refusal bank status is oext_pinned: the evaluation needs the O-ext settings and inputs")
    pin = doc["oext"]
    if oe.module_sha256() != pin["module_sha256"]:
        raise Refusal("the O-ext module is not the one these settings pin")
    if oext.settings.sha256 != pin["settings"]["sha256"] or oext.branch != pin["branch"]:
        raise Refusal("the O-ext settings (or their branch) are not the ones these settings pin")
    if not oext.runs and any(mode != "certify" for mode in modes):
        raise Refusal(OEXT_PENDING)
    return oext


def oext_codec(codec: Codec, oext: Any, settings: Settings) -> Codec:
    """The codec that encodes the PHTest prompts: the evaluation's own codec; in the prefix mode with over-refusal in
    apply_to, the prefix codec extended to the PHTest prompts (the prefix goes into every over-refusal user turn)."""
    if not isinstance(codec, PrefixCodec):
        return codec
    texts = frozenset(prompt for _, prompt in oext.bank.rows)
    if "overrefusal" in settings.doc["prefix"]["apply_to"]:
        return dataclasses.replace(codec, only=codec.only | texts)
    if texts & codec.only:
        raise Refusal("a PHTest prompt is also a prefixed text of another kind")
    return codec


def load_prefix(path: str | Path, settings: Settings) -> dict:
    """The pinned prefix text (exact UTF-8 bytes, stripped, no carriage return) and the text inserted before a user
    turn (the text and the separator)."""
    pin = settings.doc["prefix"]
    try:
        data = Path(path).read_bytes()
    except OSError:
        raise Refusal("the prefix file cannot be read") from None
    digest = sha256_bytes(data)
    if digest != pin["text_sha256"]:
        raise Refusal(f"the prefix file hashes to {digest}, the settings pin {pin['text_sha256']}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise Refusal("the prefix file is not UTF-8") from None
    if not text.strip() or text != text.strip() or "\r" in text:
        raise Refusal("the prefix must be one stripped UTF-8 text without carriage returns")
    return {"text": text, "sha256": digest, "insert": text + pin["separator"]}


@dataclasses.dataclass(frozen=True)
class PrefixCodec(Codec):
    """The policy codec with ``insert`` written at the start of the user turn of every text in ``only`` (inside the
    one user message; the template is unchanged). Response encoding, decoding and the special-token check are the
    policy codec's own."""

    insert: str = ""
    only: frozenset = frozenset()

    def wrap(self, text: str) -> str:
        return self.insert + text if text in self.only else text

    def prompt_ids(self, text: str) -> list[int]:
        return Codec.prompt_ids(self, self.wrap(text))

    def conversation_ids(self, prompt: str, response: str) -> list[int]:
        return Codec.conversation_ids(self, self.wrap(prompt), response)


def _user_text(item: Mapping) -> str:
    if item["kind"] == "arc_utility":
        return render_arc_mc(item["question"], item["labels"], item["texts"])
    return item["prompt"]


def build_prefix(codec: Codec, prefix: Mapping, settings: Settings, items: Sequence[Mapping],
                 query_rows: Sequence[Mapping], recipe: Mapping) -> tuple[PrefixCodec, list[dict], list, dict]:
    """The prefix codec, the bank items with their prefixed prompts' token SHA-256 (each item's original encoding
    checked against the prepared token audit first), the task rows encoded with the prefix (or as prepared), and a
    text-free record. A prefixed prompt over the recipe's limits refuses with counts."""
    from experiments.safety_selection import runner

    apply_to = set(settings.doc["prefix"]["apply_to"])
    insert = prefix["insert"]
    if codec.has_special(codec.encode(insert)):
        raise Refusal("the prefix (with its separator) encodes to a special token")
    max_prompt, max_train = recipe["model"]["max_prompt_tokens"], recipe["model"]["max_train_tokens"]
    on, off = set(), set()
    for item in items:
        if item["kind"] not in PREFIX_KINDS or item["kind"] == "task_rows":
            raise Refusal(f"bank item {item.get('prompt_id')} has a kind B10 does not know")
        (on if item["kind"] in apply_to else off).add(_user_text(item))
    for row in query_rows:
        (on if "task_rows" in apply_to else off).add(row["prompt"])
    if on & off:
        raise Refusal(f"{len(on & off)} user texts belong to a prefixed and an unprefixed kind")
    pc = PrefixCodec(tokenizer=codec.tokenizer, eos_id=codec.eos_id, stop_ids=codec.stop_ids, pad_id=codec.pad_id,
                     special_ids=codec.special_ids, insert=insert, only=frozenset(on))
    out, too_long, prefixed, plain = [], Counter(), Counter(), Counter()
    for item in items:
        kind = item["kind"]
        if kind == "arc_utility":
            base, _ = encode_mc(codec, item["question"], item["labels"], item["texts"], max_prompt)
        else:
            base = encode_generation_prompt(codec, item["prompt"], max_prompt)
        if ids_sha256(base) != item["token_sha256"]:
            raise Refusal(f"{item['prompt_id']} encodes differently from the prepared token audit")
        try:
            if kind == "arc_utility":
                ids, _ = encode_mc(pc, item["question"], item["labels"], item["texts"], max_prompt)
            else:
                ids = encode_generation_prompt(pc, item["prompt"], max_prompt)
        except TooLong:
            too_long[kind] += 1
            continue
        if kind in apply_to:
            prefixed[kind] += 1
        else:
            if ids != base:
                raise Refusal(f"{item['prompt_id']}: an unprefixed kind's prompt changed")
            plain[kind] += 1
        out.append({**item, "token_sha256": ids_sha256(ids)})
    queries = []
    for row in query_rows:
        base = runner._verified_example(codec, row["query_id"], row, recipe)
        if "task_rows" not in apply_to:
            queries.append(base)
            plain["task_rows"] += 1
            continue
        try:
            queries.append(encode_train(pc, row["query_id"], row["prompt"], row["response"], max_train))
        except TooLong:
            too_long["task_rows"] += 1
            continue
        prefixed["task_rows"] += 1
    if too_long:
        raise Refusal(f"the prefix makes {sum(too_long.values())} prompts longer than the recipe's limits "
                      f"({dict(sorted(too_long.items()))})")
    record = {"text_sha256": prefix["sha256"], "separator": settings.doc["prefix"]["separator"],
              "insert_tokens": len(codec.encode(insert)), "apply_to": sorted(apply_to),
              "prefixed": dict(sorted(prefixed.items())), "not_prefixed": dict(sorted(plain.items())),
              "guard_sees": settings.doc["prefix"]["guard_sees"],
              "items_sha256": sha256_bytes(canonical_json([[i["prompt_id"], i["token_sha256"]] for i in out])),
              "task_rows_sha256": sha256_bytes(canonical_json([[q.row_id, ids_sha256(q.input_ids)] for q in queries]))}
    return pc, out, queries, record


# ----- adapter transforms ----------------------------------------------------------------------------------------


def adapter_fingerprint(tensors: Mapping[str, Any]) -> str:
    """The engine's adapter fingerprint (minimal_safety.lora_fingerprint) of a name -> tensor mapping: SHA-256 over
    the sorted names, each shape and the exact bytes."""
    digest = hashlib.sha256()
    for name in sorted(tensors):
        tensor = tensors[name].detach().to("cpu").contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def scale_adapter(adapter: Mapping[str, Any], lam: float) -> tuple[dict, dict]:
    """lora_B <- lam * lora_B (float32; exact zeros at lam = 0, so the init state's B); lora_A unchanged."""
    import torch

    out, ratios = {}, []
    for name in sorted(adapter):
        tensor = adapter[name]
        if ".lora_B." in name:
            scaled = torch.zeros_like(tensor) if lam == 0.0 else tensor * lam
            before = float(tensor.double().norm())
            if before > 0:
                ratios.append(abs(float(scaled.double().norm()) / before - lam))
            out[name] = scaled
        else:
            out[name] = tensor
    record = {"rule": "lora_B <- lambda * lora_B (float32); lora_A unchanged", "lambda": lam,
              "lora_b_matrices": sum(".lora_B." in n for n in adapter),
              "max_abs_norm_ratio_error": max(ratios) if ratios else None}
    return out, record


def check_record(obj: Any, what: str) -> dict:
    """A transform's record: a JSON object of JSON scalars, lists and objects, finite numbers, short strings
    (at most 200 characters, so no text), at most 1 MB."""
    if not isinstance(obj, dict):
        raise Refusal(f"{what} is not a JSON object")

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if not isinstance(key, str) or len(key) > RECORD_MAX_STRING:
                    raise Refusal(f"{what}: a key is not a short string")
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str):
            if len(node) > RECORD_MAX_STRING:
                raise Refusal(f"{what}: a string is longer than {RECORD_MAX_STRING} characters")
        elif isinstance(node, float):
            if not math.isfinite(node):
                raise Refusal(f"{what}: a number is not finite")
        elif node is not None and not isinstance(node, (bool, int)):
            raise Refusal(f"{what}: a value is not JSON")

    walk(obj)
    if len(canonical_json(obj)) > RECORD_MAX_BYTES:
        raise Refusal(f"{what} is larger than {RECORD_MAX_BYTES} bytes")
    return obj


def check_adapter(new: Any, source: Mapping[str, Any], *, require_lora_a_unchanged: bool) -> tuple[dict, dict]:
    """A transformed adapter: exactly the source's tensor names, each a finite float32 tensor of the source's shape;
    returns the CPU tensors and their counts (tensors changed, byte for byte) and fingerprint."""
    import torch

    if not isinstance(new, Mapping) or sorted(new) != sorted(source):
        raise Refusal("the transformed adapter does not hold exactly the source adapter's tensors")
    out, changed = {}, Counter()
    for name in sorted(source):
        tensor = new[name]
        if not isinstance(tensor, torch.Tensor) or tensor.dtype != torch.float32:
            raise Refusal(f"{name}: the transformed tensor is not float32")
        if tuple(tensor.shape) != tuple(source[name].shape):
            raise Refusal(f"{name}: the transformed tensor's shape differs from the source's")
        tensor = tensor.detach().to("cpu").contiguous()
        if not bool(torch.isfinite(tensor).all()):
            raise Refusal(f"{name}: the transformed tensor holds NaN or infinity")
        part = "lora_a" if ".lora_A." in name else "lora_b" if ".lora_B." in name else None
        if part is None:
            raise Refusal(f"{name} is neither a lora_A nor a lora_B matrix")
        if tensor.numpy().tobytes() != source[name].detach().to("cpu").contiguous().numpy().tobytes():
            changed[part] += 1
        out[name] = tensor
    if require_lora_a_unchanged and changed["lora_a"]:
        raise Refusal(f"the transform changed {changed['lora_a']} lora_A matrices; its settings keep lora_A")
    return out, {"tensors": len(out), "changed_lora_a": changed["lora_a"], "changed_lora_b": changed["lora_b"],
                 "fingerprint": adapter_fingerprint(out)}


def _pinned_file(relative: str, digest: str, root: Path, what: str) -> tuple[Path, bytes]:
    path = _repo_file(relative, root, what)
    try:
        data = path.read_bytes()
    except OSError:
        raise Refusal(f"{what} cannot be read") from None
    if sha256_bytes(data) != digest:
        raise Refusal(f"{what} hashes to {sha256_bytes(data)}, the settings pin {digest}")
    return path, data


def load_callable(name: str, settings: Settings) -> tuple[Any, dict]:
    """An allowlisted callable transform: its module's bytes must hash to the pin; the code run is those bytes; the
    module must state the interface. Returns the function and the transform's settings pin (or None)."""
    entry = settings.doc["external_transforms"][name]
    path, data = _pinned_file(entry["module"], entry["module_sha256"], REPO, f"external transform {name}'s module")
    module = types.ModuleType(f"stage1_b10_transform_{name}")
    module.__file__ = str(path)
    exec(compile(data, str(path), "exec"), module.__dict__)                     # the hashed bytes, not a re-read
    if getattr(module, "INTERFACE", None) != TRANSFORM_INTERFACE:
        raise Refusal(f"external transform {name} does not state the interface {TRANSFORM_INTERFACE}")
    function = getattr(module, entry["function"], None)
    if not callable(function):
        raise Refusal(f"external transform {name} has no function {entry['function']}")
    pin = None
    if entry["settings"] is not None:
        spath, _ = _pinned_file(entry["settings"]["path"], entry["settings"]["sha256"], REPO,
                                f"external transform {name}'s settings")
        pin = {"path": str(spath), "sha256": entry["settings"]["sha256"]}
    return function, pin


def load_adapter_file(plan: Plan, settings: Settings, source_fingerprint: str) -> tuple[dict, dict, dict]:
    """A file transform's output (an adapter safetensors file) and its record, both by SHA-256; the record must name
    the allowlisted transform's SHA-256, this source adapter's fingerprint, the file's SHA-256 and the fingerprint of
    the file's float32 tensors. Returns the CPU tensors, the record and the four named fields."""
    entry = settings.doc["external_transforms"][plan.external]
    blobs = {}
    for what, path, digest in (("adapter file", plan.adapter_file, plan.adapter_sha256),
                               ("adapter record", plan.record_file, plan.record_sha256)):
        try:
            blobs[what] = Path(path).read_bytes()
        except OSError:
            raise Refusal(f"the {what} cannot be read") from None
        if sha256_bytes(blobs[what]) != digest:
            raise Refusal(f"the {what} hashes to {sha256_bytes(blobs[what])}, not the given {digest}")
    record = check_record(s1.strict_json(blobs["adapter record"]), "the adapter record")
    fields = {}
    for key, dotted in entry["record_keys"].items():
        value = _get(record, *dotted.split("."))
        if not isinstance(value, str):
            raise Refusal(f"the adapter record holds no {dotted}")
        fields[key] = value
    if fields["transform_sha256"] != entry["module_sha256"]:
        raise Refusal(f"the adapter record names another transform than the allowlisted {plan.external}")
    if fields["source_adapter_fingerprint"] != source_fingerprint:
        raise Refusal("the adapter record's source adapter is not this regenerated a0 state")
    if fields["output_file_sha256"] != plan.adapter_sha256:
        raise Refusal("the adapter record names another output file")
    if entry["settings"] is not None:
        _pinned_file(entry["settings"]["path"], entry["settings"]["sha256"], REPO,
                     f"external transform {plan.external}'s settings")
        if fields[SETTINGS_RECORD_KEY] != entry["settings"]["sha256"]:
            raise Refusal(f"the adapter record was made with other settings than {plan.external}'s pinned ones")
    import torch
    from safetensors.torch import load as load_safetensors

    try:
        tensors = load_safetensors(blobs["adapter file"])
    except Exception:                                                  # noqa: BLE001 - any parse failure refuses
        raise Refusal("the adapter file is not a safetensors file") from None
    if not tensors or any(t.dtype != torch.float32 for t in tensors.values()):
        raise Refusal("the adapter file does not hold float32 tensors only")
    if adapter_fingerprint(tensors) != fields["output_adapter_fingerprint"]:
        raise Refusal("the adapter file's tensors are not the record's output adapter")
    return tensors, record, fields


# ----- evaluation ------------------------------------------------------------------------------------------------


@dataclasses.dataclass
class Context:
    settings: Settings
    plan: Plan
    prepared_dir: Path
    manifest: dict
    manifest_sha256: str
    recipe_sha256: str
    source: Path
    stored: dict
    seed: int
    source_code_sha256: str
    source_fingerprint: str
    reference: dict
    report: dict
    prefix: dict | None = None
    external: dict | None = None
    certification: dict | None = None
    oext: Any = None


def validate_job(job: Any) -> dict:
    """A B10 job: exactly its keys, the dev bank, the e1 checkpoint, a known mode; every mode but certify names the
    certification report it ran under."""
    _keys(job, JOB_KEYS, "the B10 job")
    if job["kind"] != JOB_KIND or job["evaluate_bank"] != "dev" or job["mode"] not in MODES:
        raise Refusal("not a B10 dev-bank job of a known mode")
    for key in ("manifest_sha256", "recipe_sha256", "code_sha256", "reference_complete_sha256", "settings_sha256",
                "script_sha256"):
        _hex64(job[key], f"job {key}")
    if job["prefix_sha256"] is not None:
        _hex64(job["prefix_sha256"], "job prefix_sha256")
    if not _number(job["adapter_scale"]) or isinstance(job["seed"], bool) or not isinstance(job["seed"], int):
        raise Refusal("the job's scale or seed has the wrong type")
    if (job["mode"] == "certify") != (job["adapter_scale"] == 1.0 and job["prefix_sha256"] is None
                                      and job["external"] is None):
        raise Refusal("the job's mode does not match its changes")
    if job["mode"] == "certify":
        if job["certification_report_sha256"] is not None:
            raise Refusal("a certify job runs under no certification report")
    else:
        _hex64(job["certification_report_sha256"], "job certification_report_sha256")
    if job["oext"] is not None:
        _keys(job["oext"], OEXT_JOB_KEYS, "the job's oext")
        if job["oext"]["branch"] not in oe.BRANCHES:
            raise Refusal("the job's O-ext branch is not a known branch")
    return job


def preflight(*, prepared_dir: str | Path, source_run: str | Path, reference_path: str | Path, recipe: Mapping,
              settings: Settings, plan: Plan, certification: tuple[str | Path, str] | None = None,
              oext: Any = None) -> Context:
    """Every check that needs no model, before any folder: the recipe and data pins, the source run (a complete a0
    development run-one whose own files and dependency chain verify, holding the e1 state), its equality with the
    pinned Gate A record (else Mismatch), the role's access to the dev bank, the plan's inputs, and for every mode
    but certify the passing certification report ``certification`` = (path, SHA-256), read by read_certification
    (LS-08 (a)). The environment is compared with the report's when the evaluation starts (check_environment). With
    the over-refusal bank status oext_pinned, ``oext`` (oext_eval.prepare's result) is checked by check_oext."""
    from experiments.safety_selection import runner
    from experiments.safety_selection.jobs import AccessError, JobError, check_run_access

    if (plan.mode == "certify") != (certification is None):
        raise Refusal("an evaluation other than certify runs only under a passing certification report "
                      "(LS-08 (a)); the certify mode takes none")
    checked_oext = check_oext(settings, [plan.mode], oext)
    certified = None if certification is None else read_certification(*certification, settings)
    check_recipe(recipe, settings)
    manifest, manifest_sha = read_pinned_manifest(prepared_dir, settings)
    source = Path(source_run)
    try:
        stored, marker, _ = runner._complete_source(source, "source_run")
    except (JobError, OSError, ValueError) as exc:
        raise Refusal(f"the source run is not usable: {type(exc).__name__}: {exc}") from None
    expected = {"kind": "run-one", "split": "dev", "arm": "a0", "role": "development", "manifest_sha256": manifest_sha}
    if "recipe_sha256" in settings.doc["regeneration"]["compare_identity"]:
        expected["recipe_sha256"] = settings.doc["recipe"]["config_sha256"]
    wrong = sorted(k for k, v in expected.items() if stored.get(k) != v)
    if wrong:
        raise Refusal(f"the source run is not the pinned a0 development run-one (it differs in {wrong})")
    if marker["identity"]["training_identity"] != training_identity(recipe):
        raise Refusal("the source run's training identity is not the recipe's")
    checkpoint = settings.doc["checkpoint"]
    if f"states/{checkpoint}/state.json" not in marker["files"]:
        raise Refusal(f"the source run holds no saved {checkpoint} state")
    seed = stored["seed"]
    reference = read_reference(reference_path, seed, settings)
    report = fingerprint_report(marker, reference["marker"], settings)
    if not report["equal"]:
        raise Mismatch(f"the source run for seed {seed} differs from the Gate A record in {report['differing']}: "
                       "its state is never evaluated")
    try:
        check_run_access("development", "dev", seed, settings.doc["prepared"]["bank"], manifest["data_config"], False)
    except AccessError as exc:
        raise Refusal(f"access: {exc}") from None
    ctx = Context(settings, plan, Path(prepared_dir), manifest, manifest_sha, config_sha256(recipe), source, stored,
                  seed, marker["identity"]["code_sha256"],
                  marker["checkpoints"][checkpoint]["adapter_fingerprint"], reference, report,
                  certification=certified, oext=checked_oext)
    if plan.mode == "prefix":
        ctx.prefix = load_prefix(plan.prefix_file, settings)
    elif plan.mode == "external":
        entry = settings.doc["external_transforms"][plan.external]
        _pinned_file(entry["module"], entry["module_sha256"], REPO, f"external transform {plan.external}'s module")
        ctx.external = {"name": plan.external, "kind": entry["kind"], "module_sha256": entry["module_sha256"]}
        if entry["kind"] == "callable":
            load_callable(plan.external, settings)                  # the interface and the function, before a folder
        else:
            tensors, record, fields = load_adapter_file(plan, settings, ctx.source_fingerprint)
            if (settings.doc["overrefusal_bank"]["status"] == "open"
                    and fields["output_adapter_fingerprint"] != ctx.source_fingerprint):
                raise Refusal(OBANK_OPEN)                     # only the identity file (K = 0) certifies
            ctx.external.update(tensors=tensors, record=record, fields=fields)
    return ctx


def _job_of(ctx: Context, wall_limit_seconds: float | None) -> dict:
    plan = ctx.plan
    external = None
    if ctx.external is not None:
        external = {"name": ctx.external["name"], "kind": ctx.external["kind"],
                    "module_sha256": ctx.external["module_sha256"],
                    "adapter_sha256": plan.adapter_sha256, "record_sha256": plan.record_sha256}
    return validate_job({
        "kind": JOB_KIND, "manifest_sha256": ctx.manifest_sha256, "recipe_sha256": ctx.recipe_sha256,
        "code_sha256": code_identity()["sha256"], "wall_limit_seconds": wall_limit_seconds,
        "source_run": str(ctx.source), "checkpoint": ctx.settings.doc["checkpoint"], "evaluate_bank": "dev",
        "seed": ctx.seed, "reference_complete_sha256": ctx.reference["complete_sha256"], "mode": plan.mode,
        "adapter_scale": plan.adapter_scale, "prefix_sha256": ctx.prefix["sha256"] if ctx.prefix else None,
        "external": external, "settings_sha256": ctx.settings.sha256,
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "certification_report_sha256": ctx.certification["sha256"] if ctx.certification else None,
        "oext": _oext_job(ctx.oext)})


def _oext_job(oext: Any) -> dict | None:
    if oext is None:
        return None
    bank = oext.bank
    return {"branch": oext.branch, "settings_sha256": oext.settings.sha256, "module_sha256": oe.module_sha256(),
            "record_sha256": None if bank is None else bank.record_sha256,
            "bank_sha256": None if bank is None else bank.bank_sha256,
            "w1_18_record_sha256": None if oext.w1_18 is None else oext.w1_18.record_sha256}


def transform_context(ctx: Context, recipe: Mapping, policy: Any, settings_pin: dict | None) -> dict:
    """What a callable transform receives besides the tensors (text-free): the interface, the source state, the
    recipe's model and LoRA shape, the policy snapshot folder (where the aligned weights are) and its settings pin."""
    model, lora = recipe["model"], recipe["model"]["lora"]
    return {"interface": TRANSFORM_INTERFACE, "name": ctx.plan.external,
            "source": {"run": str(ctx.source), "checkpoint": ctx.settings.doc["checkpoint"], "seed": ctx.seed,
                       "adapter_fingerprint": ctx.source_fingerprint},
            "model": {"repo_id": model["repo_id"], "revision": model["revision"],
                      "architecture": model["architecture"]},
            "lora": {"r": lora["r"], "alpha": lora["alpha"], "scale": lora["alpha"] / lora["r"],
                     "target_modules": list(lora["target_modules"])},
            "policy_snapshot": policy.identity.get("snapshot"), "settings": settings_pin}


def _apply_transform(ctx: Context, recipe: Mapping, policy: Any, ledger: Any, run_dir: Path) -> dict:
    """The scale or external transform of the loaded source adapter: checked, loaded, recorded in transform.json."""
    from experiments.safety_selection import engine as en
    from experiments.safety_selection import runner

    plan = ctx.plan
    with ledger.stage("adapter_transform", mode=plan.mode) as info:
        source = {name: param.detach().to("cpu").contiguous().clone() for name, param in policy.named}
        require_a = False
        if plan.mode == "scale":
            new, record = scale_adapter(source, plan.adapter_scale)
        else:
            entry = ctx.settings.doc["external_transforms"][plan.external]
            require_a = entry["require_lora_a_unchanged"]
            if entry["kind"] == "callable":
                function, settings_pin = load_callable(plan.external, ctx.settings)
                result = function({k: v.clone() for k, v in source.items()},
                                  transform_context(ctx, recipe, policy, settings_pin))
                if not (isinstance(result, tuple) and len(result) == 2):
                    raise Refusal(f"external transform {plan.external} did not return (tensors, record)")
                new, record = result
                check_record(record, f"external transform {plan.external}'s record")
            else:
                new = ctx.external["tensors"]
                record = {"file_record": ctx.external["record"], "fields": ctx.external["fields"]}
        checked, counts = check_adapter(new, source, require_lora_a_unchanged=require_a)
        en.load_lora_state(policy.named, checked)
        loaded = en.lora_fingerprint(policy.named)
        if loaded != counts["fingerprint"]:
            raise runner.RunError("the loaded adapter's fingerprint differs from the checked transform output")
        info.update(changed_lora_a=counts["changed_lora_a"], changed_lora_b=counts["changed_lora_b"],
                    adapter_fingerprint=loaded)
    out = {"mode": plan.mode, "adapter_scale": plan.adapter_scale, "external": plan.external,
           "source_adapter_fingerprint": ctx.source_fingerprint, "transformed_adapter_fingerprint": loaded,
           "counts": counts, "seconds": info["seconds"], "record": record}
    write_json(run_dir / "transform.json", out)
    return {k: v for k, v in out.items() if k != "record"}


def evaluate(ctx: Context, *, out_dir: str | Path, session: Any, wall_limit_seconds: float | None = None) -> dict:
    """One evaluation in a new folder: restore the source e1 state (its file hashes and fingerprint verified), apply
    the plan's one change, then the engine's own evaluate_checkpoint on the dev bank and the task rows, with the
    source run's seed as the job seed, then (status oext_pinned, a set branch) the shared O-ext evaluation on the
    engine's own dev-100 answers, its files beside the engine's. COMPLETE.json is written last (kind
    stage1-eval-adapter)."""
    from experiments.safety_selection import engine as en
    from experiments.safety_selection import runner
    from experiments.safety_selection.ledger import create_run_dir
    from experiments.safety_selection.loaders import Policy
    from experiments.safety_selection.prepare import load_prepared
    from experiments.safety_selection.verify import dependency_receipt

    settings, plan, recipe = ctx.settings, ctx.plan, session.recipe
    if config_sha256(recipe) != ctx.recipe_sha256:
        raise Refusal("the session's recipe is not the preflight's")
    if ctx.certification is not None:
        check_environment(ctx.certification, session, settings)        # before any folder
    checkpoint, bank = settings.doc["checkpoint"], settings.doc["prepared"]["bank"]
    receipt = dependency_receipt(ctx.source, "source_run", checkpoint)
    prepared = load_prepared(ctx.prepared_dir, ctx.manifest_sha256, banks=(bank,))
    job = _job_of(ctx, wall_limit_seconds)
    code = code_identity()
    run_dir = create_run_dir(out_dir)
    identity = {**runner._identity(ctx.manifest, ctx.manifest_sha256, recipe, code),
                "b10": {"script": OWNER, "script_sha256": job["script_sha256"],
                        "s1common_sha256": sha256_file(Path(s1.__file__).resolve()),
                        "settings_sha256": settings.sha256, "mode": plan.mode,
                        "reference_complete_sha256": ctx.reference["complete_sha256"]}}
    ledger = None
    try:
        ledger = runner._start(run_dir, job, identity, session, [receipt])
        lock = runner.lock_record(session.device, Path.cwd())               # as eval-state: before any model load
        policy = session.policy(ledger, run_dir)
        write_json(run_dir / "assets.json", {"policy": policy.identity, "environment": session.environment,
                                             "loaded_in": dict(session.loaded_in)})
        runner.merge_assets(run_dir, lock, runner.guard_pin(recipe))
        if any(".lora_A." not in name and ".lora_B." not in name for name, _ in policy.named):
            raise Refusal("the policy trains parameters other than LoRA matrices")
        state_dir = ctx.source / "states" / checkpoint
        with ledger.stage("restore_state", checkpoint=checkpoint) as info:
            runner._same_state(state_dir, receipt)
            state = en.load_state(state_dir, policy.named, None, policy.device)
            if state["adapter_fingerprint"] != ctx.source_fingerprint:
                raise runner.RunError("the restored state is not the checked source adapter")
            info.update(step=state["step"], adapter_fingerprint=state["adapter_fingerprint"])
        transform = None
        if plan.mode in ("scale", "external"):
            transform = _apply_transform(ctx, recipe, policy, ledger, run_dir)
        items, prefix_record, eval_policy = prepared.banks[bank], None, policy
        if plan.mode == "prefix":
            with ledger.stage("prefix_encode", items=len(items), task_rows=len(prepared.query_rows)) as info:
                codec, items, queries, prefix_record = build_prefix(policy.codec, ctx.prefix, settings, items,
                                                                    prepared.query_rows, recipe)
                info.update(prefixed=sum(prefix_record["prefixed"].values()))
            query_sha = runner._query_bank_sha256(prepared)
            eval_policy = Policy(policy.model, policy.named, codec, policy.device, policy.identity)
            write_json(run_dir / "prefix.json", prefix_record)
        else:
            queries, query_sha = runner._query_examples(policy, prepared, recipe)
        evaluated = en.lora_fingerprint(policy.named)
        evaluation = runner.evaluate_checkpoint(session, eval_policy, None, items, queries, query_sha, ledger,
                                                run_dir / "eval" / checkpoint, run_dir, checkpoint, ctx.seed,
                                                prepared.manifest.get("query_loss_definition"))
        oext = None
        if ctx.oext is not None:
            oext = {"status": "not_run", "branch": ctx.oext.branch, "reason": OEXT_PENDING}
            if ctx.oext.runs:                      # after the engine's 8 files, which it never changes
                folder = run_dir / "eval" / checkpoint
                dev, dev_inputs = oe.dev_answers_from_eval(folder, items)
                oext = oe.evaluate_oext(session=session, policy=eval_policy,
                                        codec=oext_codec(eval_policy.codec, ctx.oext, settings), ledger=ledger,
                                        run_dir=run_dir, folder=folder, prepared=ctx.oext, dev=dev,
                                        dev_inputs=dev_inputs, checkpoint=checkpoint)
        seconds = stage_seconds(run_dir)
        obank = {"status": settings.doc["overrefusal_bank"]["status"], "bank": bank,
                 "overrefusal_items": sum(i["kind"] == "overrefusal" for i in items),
                 "max_new_tokens": recipe["generation"]["max_new_tokens"]}
        if ctx.oext is not None:
            obank["oext"] = {"branch": ctx.oext.branch, "runs": ctx.oext.runs, "settings_sha256": ctx.oext.settings.sha256}
        result = {"source_run": str(ctx.source), "source_complete_sha256": receipt["complete_sha256"],
                  "source_state_sha256": receipt["state_sha256"], "source_code_sha256": ctx.source_code_sha256,
                  "reference_complete_sha256": ctx.reference["complete_sha256"], "checkpoint": checkpoint,
                  "step": state["step"], "seed": ctx.seed, "mode": plan.mode, "adapter_scale": plan.adapter_scale,
                  "source_adapter_fingerprint": ctx.source_fingerprint, "evaluated_adapter_fingerprint": evaluated,
                  "fingerprint_comparison": ctx.report, "transform": transform, "prefix": prefix_record,
                  "certification_report_sha256": ctx.certification["sha256"] if ctx.certification else None,
                  "overrefusal_bank": obank, "evaluation": evaluation, "oext": oext,
                  "costs": {"stage_seconds": seconds,
                            "cost_scope": "this evaluation's in-job stages (the transform, if any, the "
                                          "evaluation and O-ext, if it runs); the a0 regeneration is a study "
                                          "cost, reported apart (LQ8)"},
                  "trajectory": {k: ctx.stored[k] for k in ("split", "arm", "seed", "role")}}
        return runner._finish(run_dir, ledger, JOB_KIND, identity, result)
    except BaseException as exc:
        runner._fail(run_dir, ledger, exc)
        raise


def brief(result: Mapping) -> dict:
    """What is printed of a finished evaluation: ids, hashes and costs; never the evaluation's outcome values."""
    keys = ("run_dir", "complete", "kind", "mode", "adapter_scale", "seed", "source_adapter_fingerprint",
            "evaluated_adapter_fingerprint", "costs")
    return {k: result[k] for k in keys if k in result}


# ----- verification and the certification comparison -------------------------------------------------------------


def verify_unit(unit: str | Path, path_map: Sequence[tuple[str, str]] = ()) -> dict:
    """A B10 unit's own files (COMPLETE.json and every file it lists), its job, and its one source receipt: the
    source's COMPLETE.json still hashes to the receipt and the source's own files and dependency chain verify."""
    from experiments.safety_selection.verify import PathMap, chain_problems, read_dependencies

    unit = Path(unit)
    problems = list(verify_files(unit))
    job = None
    try:
        job = validate_job(s1.strict_json((unit / "job.json").read_bytes()))
    except (OSError, Refusal) as exc:
        problems.append(f"job.json: {exc}")
    marker = read_complete(unit) if (unit / COMPLETE).is_file() else None
    if marker is not None and marker.get("kind") != JOB_KIND:
        problems.append("COMPLETE.json is not a B10 unit's")
    try:
        deps = read_dependencies(unit) or []
    except (OSError, ValueError) as exc:
        deps = []
        problems.append(f"dependencies.json: {exc}")
    if len(deps) != 1 or deps[0].get("role") != "source_run":
        problems.append("the unit does not hold exactly one source_run receipt")
    elif job is not None:
        dep = deps[0]
        if Path(dep.get("path", "")) != Path(job["source_run"]) or dep.get("checkpoint") != job["checkpoint"]:
            problems.append("the receipt is not the job's source run and checkpoint")
        mapper = PathMap(path_map)
        local = mapper.resolve(dep.get("resolved") or dep["path"])
        if not (local / COMPLETE).is_file():
            problems.append("the source run is missing at its (mapped) recorded path")
        elif sha256_file(local / COMPLETE) != dep.get("complete_sha256"):
            problems.append("the source run's COMPLETE.json differs from the receipt")
        else:
            problems += [f"source: {p}" for p in chain_problems(local, mapper)]
    return {"unit": str(unit), "complete": not problems, "problems": problems}


def _rows(path: Path, what: str) -> list[dict]:
    if not path.is_file():
        raise Refusal(f"{what} is missing")
    try:
        return read_jsonl(path)
    except ValueError:
        raise Refusal(f"{what} is not strict JSONL") from None


def _by_key(rows: list[dict], key: Any, what: str) -> dict:
    out = {}
    for row in rows:
        k = key(row)
        if k in out:
            raise Refusal(f"{what} repeats an answer id")
        out[k] = row
    return out


def compare_certification(unit: str | Path, reference_path: str | Path, reference_eval: str | Path,
                          settings: Settings, *, against: str = "a0") -> dict:
    """The certification gate (settings certification; LS-08 (a)): a certify unit (or an identity-transform unit,
    Safe LoRA at K = 0; or, against "untuned", a lambda = 0 unit) against the pinned Gate A unit's evaluation files,
    each checked by the SHA-256 that the Gate A unit's COMPLETE.json lists. The unit must have run on the settings'
    engine, with this script and these settings; the report names what it certifies (the engine, the script's code
    and the certified settings) and the unit's environment fields. Counts only: no text, and no answer is printed."""
    doc, cert = settings.doc, settings.doc["certification"]
    unit = Path(unit)
    problems = verify_files(unit)
    if problems:
        raise Refusal(f"the unit is not complete: {problems[:3]}")
    job = validate_job(s1.strict_json((unit / "job.json").read_bytes()))
    if job["code_sha256"] != doc["engine_x"]:
        raise Refusal("the unit ran on another engine than the one these settings pin: it certifies nothing here")
    if job["script_sha256"] != sha256_file(Path(__file__).resolve()) or job["settings_sha256"] != settings.sha256:
        raise Refusal("the unit ran with another B10 script or settings than this comparison's")
    if against == "a0":
        if job["mode"] == "external":
            transform = s1.strict_json((unit / "transform.json").read_bytes())
            counts = transform.get("counts") or {}
            if (counts.get("changed_lora_a") != 0 or counts.get("changed_lora_b") != 0
                    or transform.get("transformed_adapter_fingerprint") != transform.get("source_adapter_fingerprint")):
                raise Refusal("an external unit certifies only as an identity transform (Safe LoRA at K = 0)")
        elif job["mode"] != "certify":
            raise Refusal("not a certification unit (mode certify: lambda 1, no prefix, no external transform)")
        reference = read_reference(reference_path, job["seed"], settings)
        ref_checkpoint = doc["checkpoint"]
    elif against == "untuned":
        if job["mode"] != "scale" or job["adapter_scale"] != 0.0:
            raise Refusal("only a lambda = 0 unit is compared with the untuned unit")
        reference = read_untuned(reference_path, settings)
        if reference["seed"] != job["seed"]:
            raise Refusal("the lambda = 0 unit's seed is not the untuned unit's (its sampling streams differ)")
        ref_checkpoint = doc["untuned_unit"]["checkpoint"]
    else:
        raise Refusal(f"against must be a0 or untuned, not {against!r}")
    if job["reference_complete_sha256"] != (doc["reference_units"][str(job["seed"])]["complete_sha256"]):
        raise Refusal("the unit was not evaluated against the pinned Gate A unit of its seed")
    files = reference["marker"]["files"]
    ref_eval = Path(reference_eval)

    def ref_file(name: str, required: bool) -> Path | None:
        path, key = ref_eval / name, f"eval/{ref_checkpoint}/{name}"
        if not path.is_file():
            if required:
                raise Refusal(f"the reference evaluation file {name} is missing")
            return None
        if files.get(key) != sha256_file(path):
            raise Refusal(f"{name} is not the Gate A unit's file (its SHA-256 differs from the COMPLETE.json list)")
        return path

    mine_dir = unit / "eval" / job["checkpoint"]
    sample_key = lambda r: (r.get("prompt_id"), r.get("sample_index"))  # noqa: E731
    reference_labels = _by_key(_rows(ref_file("guard_samples.jsonl", True), "the reference guard_samples.jsonl"),
                               sample_key, "the reference guard_samples.jsonl")
    labels = _by_key(_rows(mine_dir / "guard_samples.jsonl", "the unit's guard_samples.jsonl"), sample_key,
                     "the unit's guard_samples.jsonl")
    common = sorted(set(reference_labels) & set(labels))
    fields = cert["gate_fields"]
    differing = [k for k in common if any(reference_labels[k].get(f) != labels[k].get(f) for f in fields)]

    def unsafe(rows: Mapping) -> int:
        return sum(r.get("valid") is True and r.get("safety") == "Unsafe" for r in rows.values())

    same_set = set(reference_labels) == set(labels)
    gate = {"answers_reference": len(reference_labels), "answers_unit": len(labels),
            "expected_answers": cert["expected_sampled_answers"], "same_answer_set": same_set,
            "differing_gate_labels": len(differing), "gate_fields": fields,
            "unsafe_equal": unsafe(reference_labels) == unsafe(labels)}
    passed = (same_set and len(reference_labels) == cert["expected_sampled_answers"] and not differing
              and gate["unsafe_equal"])
    diagnostics: dict[str, Any] = {
        "refusal_flag_agreement": sum(reference_labels[k].get("refusal") == labels[k].get("refusal") for k in common),
        "categories_agreement": sum(reference_labels[k].get("categories") == labels[k].get("categories")
                                    for k in common)}
    path = ref_file("samples.jsonl", False)
    if path is not None:
        ref_samples = _by_key(_rows(path, "the reference samples.jsonl"), sample_key, "the reference samples")
        samples = _by_key(_rows(mine_dir / "samples.jsonl", "the unit's samples.jsonl"), sample_key, "the samples")
        both = sorted(set(ref_samples) & set(samples))
        diagnostics["sampled"] = {"n": len(both),
                                  "identical_outputs": sum(ref_samples[k]["output_ids"] == samples[k]["output_ids"]
                                                           for k in both),
                                  "identical_seeds": sum(ref_samples[k].get("seed") == samples[k].get("seed")
                                                         for k in both)}
    path = ref_file("generations.jsonl", False)
    if path is not None:
        ref_gen = _by_key(_rows(path, "the reference generations.jsonl"), lambda r: r.get("prompt_id"), "generations")
        gen = _by_key(_rows(mine_dir / "generations.jsonl", "the unit's generations.jsonl"),
                      lambda r: r.get("prompt_id"), "generations")
        both = sorted(set(ref_gen) & set(gen))
        diagnostics["greedy"] = {kind: {"n": sum(ref_gen[k]["kind"] == kind for k in both),
                                        "identical_outputs": sum(ref_gen[k]["kind"] == kind and
                                                                 ref_gen[k]["output_ids"] == gen[k]["output_ids"]
                                                                 for k in both)}
                                 for kind in sorted({ref_gen[k]["kind"] for k in both})}
    path = ref_file("guard.jsonl", False)
    if path is not None:
        ref_guard = _by_key(_rows(path, "the reference guard.jsonl"), lambda r: r.get("prompt_id"), "guard")
        guard = _by_key(_rows(mine_dir / "guard.jsonl", "the unit's guard.jsonl"), lambda r: r.get("prompt_id"),
                        "guard")
        both = sorted(set(ref_guard) & set(guard))
        triple = ("valid", "safety", "refusal")
        diagnostics["greedy_guard_agreement"] = {
            "n": len(both), "agree": sum(all(ref_guard[k].get(f) == guard[k].get(f) for f in triple) for k in both)}
    path = ref_file("query_loss.jsonl", False)
    if path is not None:
        ref_loss = _by_key(_rows(path, "the reference query_loss.jsonl"), lambda r: r.get("query_id"), "query loss")
        loss = _by_key(_rows(mine_dir / "query_loss.jsonl", "the unit's query_loss.jsonl"),
                       lambda r: r.get("query_id"), "query loss")
        both = sorted(set(ref_loss) & set(loss))
        diagnostics["task_loss"] = {"n": len(both), "bitwise_equal": sum(ref_loss[k]["loss"] == loss[k]["loss"]
                                                                          for k in both),
                                    "max_abs_difference": max((abs(ref_loss[k]["loss"] - loss[k]["loss"])
                                                               for k in both), default=None)}
    assets = s1.strict_json((unit / "assets.json").read_bytes())
    return {"kind": COMPARE_KIND, "version": 1, "against": against, "verdict": "pass" if passed else "fail",
            "seed": job["seed"], "unit_mode": job["mode"], "unit_complete_sha256": sha256_file(unit / COMPLETE),
            "reference_complete_sha256": reference["complete_sha256"], "gate": gate, "diagnostics": diagnostics,
            "certified": {"code_sha256": job["code_sha256"], "script_code_sha256": script_code_sha256(),
                          "certified_settings_sha256": certified_settings_sha256(settings),
                          "script_sha256": job["script_sha256"], "settings_sha256": job["settings_sha256"]},
            "environment": environment_fields(assets, settings),
            "rule": cert["gate"], "failure_action": cert["failure_action"],
            "provenance": s1.provenance(Path(__file__).resolve(), settings.sha256,
                                        {"unit_complete": sha256_file(unit / COMPLETE),
                                         "reference_complete": reference["complete_sha256"]}, {})}


SETTINGS_LITERAL = re.compile(rb'^SETTINGS_SHA256 = "[0-9a-f]{64}"$', re.MULTILINE)


def script_code_sha256(path: str | Path | None = None) -> str:
    """The SHA-256 of this script's bytes with the value of its settings literal line (SETTINGS_SHA256 = "...")
    written as 64 zeros: the code that a certification certifies. A settings-only change (a new literal) leaves it;
    any code change gives a new value."""
    data = Path(path or Path(__file__).resolve()).read_bytes()
    normalized, count = SETTINGS_LITERAL.subn(b'SETTINGS_SHA256 = "' + b"0" * 64 + b'"', data)
    if count != 1:
        raise Refusal("the script's settings literal line does not occur exactly once")
    return sha256_bytes(normalized)


def certified_settings_sha256(settings: Settings) -> str:
    """The SHA-256 of the settings sections that a certification certifies (CERTIFIED_SETTINGS_KEYS) and of the
    certification seed's reference pin. The prefix text, the scale points, the transform allowlist, the
    over-refusal bank status, the other seeds' pins and the texts are outside it."""
    doc = settings.doc
    part = {key: doc[key] for key in CERTIFIED_SETTINGS_KEYS}
    part["certification_reference_unit"] = doc["reference_units"][str(doc["certification"]["seed"])]
    return sha256_bytes(canonical_json(part))


def environment_fields(records: Mapping, settings: Settings) -> dict:
    """The settings' certification environment fields read from {"environment": ..., "environment_lock": ...} (a
    unit's assets.json, or this session's records); a missing field reads as null. Values pass through JSON, so a
    session's values and a file's compare alike."""
    out = {}
    for dotted in settings.doc["certification"]["environment_fields"]:
        value = _get(records, *dotted.split("."))
        out[dotted] = None if value is _MISSING else json.loads(json.dumps(value, sort_keys=True))
    return out


def read_certification(path: str | Path, digest: str, settings: Settings) -> dict:
    """A passing certification report (compare_certification against a0, of the certify unit at the settings'
    certification seed) given by its path and SHA-256, made on these settings' engine, with this script's code and
    these certified settings. Returns its SHA-256, seed, unit and environment fields."""
    doc = settings.doc
    _hex64(digest, "the certification report SHA-256")
    try:
        data = Path(path).read_bytes()
    except OSError:
        raise Refusal("the certification report cannot be read") from None
    if sha256_bytes(data) != digest:
        raise Refusal(f"the certification report hashes to {sha256_bytes(data)}, not the given {digest}")
    report = s1.strict_json(data)
    if not isinstance(report, dict) or report.get("kind") != COMPARE_KIND or report.get("version") != 1:
        raise Refusal("the certification report is not a B10 certification comparison")
    if report.get("against") != "a0" or report.get("unit_mode") != "certify":
        raise Refusal("the certification report is not the certify unit's comparison with its Gate A unit")
    gate = report.get("gate") or {}
    if (report.get("verdict") != "pass" or gate.get("same_answer_set") is not True
            or gate.get("differing_gate_labels") != 0
            or gate.get("answers_reference") != doc["certification"]["expected_sampled_answers"]):
        raise Refusal("the certification did not pass: no evaluation-only reference runs (LS-08 (a))")
    seed = doc["certification"]["seed"]
    if report.get("seed") != seed or report.get("reference_complete_sha256") != (
            doc["reference_units"][str(seed)]["complete_sha256"]):
        raise Refusal(f"the certification report is not of the certification seed {seed}'s pinned Gate A unit")
    certified = report.get("certified") or {}
    if certified.get("code_sha256") != doc["engine_x"]:
        raise Refusal("the certification was made on another engine")
    if certified.get("script_code_sha256") != script_code_sha256():
        raise Refusal("the certification was made with other B10 code")
    if certified.get("certified_settings_sha256") != certified_settings_sha256(settings):
        raise Refusal("the certification was made under other certified settings (recipe, data, rules or pins)")
    environment = report.get("environment")
    if not isinstance(environment, dict) or set(environment) != set(doc["certification"]["environment_fields"]):
        raise Refusal("the certification report does not hold the settings' environment fields")
    return {"sha256": digest, "seed": seed, "unit_complete_sha256": report.get("unit_complete_sha256"),
            "environment": environment}


def check_environment(certification: Mapping, session: Any, settings: Settings) -> None:
    """This session's environment fields (and the pod's lock record) equal the certification unit's (REF R.0.9:
    an environment-matched attempt); a difference refuses before any folder."""
    from experiments.safety_selection import runner
    from experiments.safety_selection.jobs import JobError

    try:
        lock = runner.lock_record(session.device, Path.cwd())
    except JobError as exc:
        raise Refusal(f"this environment cannot be recorded: {exc}") from None
    mine = environment_fields({"environment": session.environment,
                               "environment_lock": lock[0] if lock is not None else None}, settings)
    differ = sorted(k for k, v in mine.items() if certification["environment"].get(k, _MISSING) != v)
    if differ:
        raise Refusal(f"this environment differs from the certification unit's in {differ}: it is not certified")


def check_gate_folder(reference: Mapping, reference_eval: str | Path, settings: Settings) -> None:
    """Before any work: the gate folder holds every required Gate A evaluation file, and each required or present
    diagnostic file has the SHA-256 that the Gate A unit's COMPLETE.json lists (what compare_certification checks
    after the certify evaluation)."""
    cert, files = settings.doc["certification"], reference["marker"]["files"]
    folder = Path(reference_eval)
    for name in cert["required_reference_files"] + cert["diagnostic_reference_files"]:
        path = folder / name
        if not path.is_file():
            if name in cert["required_reference_files"]:
                raise Refusal(f"the gate folder holds no {name}")
            continue
        if files.get(f"eval/{settings.doc['checkpoint']}/{name}") != sha256_file(path):
            raise Refusal(f"the gate folder's {name} is not the Gate A unit's file")


# ----- one process: regenerate, then evaluate --------------------------------------------------------------------


def parse_spec(spec: str, settings: Settings, prefix_file: str | None) -> Plan:
    """certify, prefix, scale:L or external:NAME (a callable transform; a file transform needs evaluate)."""
    head, _, tail = spec.partition(":")
    if head == "scale":
        try:
            return make_plan(settings, "scale", adapter_scale=float(tail))
        except ValueError:
            raise Refusal(f"evaluation spec {spec!r}: the scale is not a number") from None
    if head == "external":
        entry = settings.doc["external_transforms"].get(tail)
        if entry is not None and entry["kind"] == "file":
            raise Refusal(f"evaluation spec {spec!r}: a file transform runs through evaluate, not run")
        return make_plan(settings, "external", external=tail)
    if tail:
        raise Refusal(f"evaluation spec {spec!r} takes no value")
    if head == "prefix":
        return make_plan(settings, "prefix", prefix_file=prefix_file)
    return make_plan(settings, head)


def run_sequence(*, prepared_dir: str | Path, seed: int, reference_path: str | Path, regen_root: str | Path,
                 eval_root: str | Path, plans: Sequence[Plan], session: Any, settings: Settings,
                 gate_reference_eval: str | Path | None = None, certification: tuple[str | Path, str] | None = None,
                 wall_limit_seconds: float | None = None, oext: Any = None) -> dict:
    """Regenerate, then the evaluations in order, in one session (one model load). With a gate, the first plan must
    be certify, and nothing else runs unless its comparison passes. Every plan but certify runs under a passing
    certification: the given report (path, SHA-256), or, at the settings' certification seed, this run's own gate.
    Everything that needs no model (the gate folder, the certification report and this environment) is checked
    before the regeneration. Stops at a mismatch (exit 3) or a failed gate (exit 4)."""
    labels = [p.label for p in plans]
    if not plans or len(set(labels)) != len(labels):
        raise Refusal("the evaluations must be distinct and at least one")
    if gate_reference_eval is not None and plans[0].mode != "certify":
        raise Refusal("a gated run starts with the certify evaluation")
    eval_root = Path(eval_root)
    targets = [eval_root / f"{seed}-{label}" for label in labels]
    report_path = eval_root / f"{seed}-certify.compare.json"            # an earlier report may be some unit's binding
    if any(t.exists() for t in targets) or (gate_reference_eval is not None and report_path.exists()):
        raise Refusal("an evaluation folder or the comparison file exists already: nothing is overwritten")
    if gate_reference_eval is not None:
        check_gate_folder(read_reference(reference_path, seed, settings), gate_reference_eval, settings)
    gated_here = gate_reference_eval is not None and seed == settings.doc["certification"]["seed"]
    check_oext(settings, [p.mode for p in plans], oext)
    if any(p.mode != "certify" for p in plans) and certification is None and not gated_here:
        raise Refusal("an evaluation other than certify needs a passing certification report, or this run's own "
                      "gate at the certification seed (LS-08 (a))")
    if certification is not None:
        check_environment(read_certification(*certification, settings), session, settings)
    record = regenerate(prepared_dir=prepared_dir, seed=seed, reference_path=reference_path, out_root=regen_root,
                        session=session, settings=settings, wall_limit_seconds=wall_limit_seconds)
    out = {"seed": seed, "regeneration": {"verdict": record["verdict"], "differing": record["comparison"]["differing"],
                                          "run_complete_sha256": record["run_complete_sha256"]},
           "evaluations": [], "exit": EXIT_OK}
    if record["verdict"] != "match":
        out.update(exit=EXIT_MISMATCH, stopped="the regenerated adapter differs from the Gate A record")
        return out
    source = Path(regen_root) / "run"
    for plan, target in zip(plans, targets):
        ctx = preflight(prepared_dir=prepared_dir, source_run=source, reference_path=reference_path,
                        recipe=session.recipe, settings=settings, plan=plan,
                        certification=None if plan.mode == "certify" else certification, oext=oext)
        result = evaluate(ctx, out_dir=target, session=session, wall_limit_seconds=wall_limit_seconds)
        out["evaluations"].append(brief(result))
        if gate_reference_eval is not None and plan.mode == "certify":
            report = compare_certification(target, reference_path, gate_reference_eval, settings)
            write_atomic(report_path, canonical_json(report))
            out["certification"] = {"verdict": report["verdict"], "gate": report["gate"],
                                    "report_sha256": sha256_file(report_path)}
            if report["verdict"] != "pass":
                out.update(exit=EXIT_CERTIFICATION, stopped="the certification failed: no reference runs")
                return out
            if gated_here:
                certification = (report_path, sha256_file(report_path))
    return out


# ----- command line ----------------------------------------------------------------------------------------------


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False))


def _invalid() -> tuple:
    from experiments.safety_selection.config import ConfigError
    from experiments.safety_selection.jobs import AccessError, JobError
    from experiments.safety_selection.ledger import RunDirError
    from experiments.safety_selection.prepare import HiddenAccessError
    from experiments.safety_selection.sources import DataError

    return (Refusal, ConfigError, JobError, AccessError, DataError, HiddenAccessError, RunDirError,
            FileNotFoundError, FileExistsError, PermissionError, ValueError)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eval_adapter.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", help="the pinned settings and the reference pins ($0, no model)")
    p.add_argument("--reference", action="append", default=[], metavar="SEED=PATH")
    p.add_argument("--untuned", help="the untuned unit's COMPLETE.json")
    for name in ("regenerate", "evaluate", "run"):
        p = sub.add_parser(name)
        p.add_argument("--prepared", required=True)
        p.add_argument("--recipe", required=True)
        p.add_argument("--reference", required=True, help="the Gate A unit's COMPLETE.json")
        p.add_argument("--wall-limit-seconds", type=float)
        if name in ("regenerate", "run"):
            p.add_argument("--seed", type=int, required=True)
        if name == "regenerate":
            p.add_argument("--out", required=True, help="a new or empty folder")
        if name == "evaluate":
            p.add_argument("--source-run", required=True)
            p.add_argument("--out", required=True, help="a new folder")
            p.add_argument("--mode", required=True, choices=MODES)
            p.add_argument("--lambda", dest="adapter_scale", type=float)
            p.add_argument("--prefix-file")
            p.add_argument("--external")
            p.add_argument("--adapter-file")
            p.add_argument("--adapter-sha256")
            p.add_argument("--adapter-record")
            p.add_argument("--adapter-record-sha256")
        if name == "run":
            p.add_argument("--regen-out", required=True)
            p.add_argument("--eval-root", required=True)
            p.add_argument("--evaluations", required=True, help="certify,prefix,scale:0.75,scale:0.5,external:NAME")
            p.add_argument("--prefix-file")
            p.add_argument("--gate-reference-eval", help="the Gate A unit's eval/e1 folder (gates the references)")
        if name in ("evaluate", "run"):
            p.add_argument("--certification-report", help="a passing certification comparison (compare's --out)")
            p.add_argument("--certification-report-sha256", help="its SHA-256, as recorded when it was made")
            p.add_argument("--oext-bank", help="O-ext: build_oext's bank file (oext_bank.json; status oext_pinned)")
            p.add_argument("--oext-record", help="O-ext: build_oext's sealed record (oext_record.json), pinned")
            p.add_argument("--w1-18-record", help="O-ext: W1-18's record (overrefusal_checks.json), when pinned")
    p = sub.add_parser("compare", help="the certification comparison (counts only)")
    p.add_argument("--unit", required=True)
    p.add_argument("--reference", required=True)
    p.add_argument("--reference-eval", required=True)
    p.add_argument("--out", required=True, help="a new file")
    p.add_argument("--against", choices=("a0", "untuned"), default="a0")
    p = sub.add_parser("verify", help="a unit's own files and its source chain")
    p.add_argument("--unit", required=True)
    p.add_argument("--map", action="append", default=[], metavar="RECORDED=LOCAL")
    return parser


def _footprint(paths: Sequence[str | Path | None]) -> dict:
    """What each output path holds at its top level (a folder's names, a file's size and time, or nothing): a
    change since the start means this process wrote something, so a later failure is exit 1, never exit 2."""
    out = {}
    for p in paths:
        if p is None:
            continue
        path = Path(p)
        if path.is_dir():
            out[str(path)] = ("folder", tuple(sorted(os.listdir(path))))
        elif path.exists():
            stat = path.stat()
            out[str(path)] = ("file", stat.st_size, stat.st_mtime_ns)
        else:
            out[str(path)] = None
    return out


def _certification_arg(args: argparse.Namespace) -> tuple[str, str] | None:
    report, digest = args.certification_report, args.certification_report_sha256
    if (report is None) != (digest is None):
        raise Refusal("--certification-report and --certification-report-sha256 go together")
    return None if report is None else (report, digest)


def _oext_arg(args: argparse.Namespace, settings: Settings, oext_settings: Any) -> Any:
    """The O-ext part from the command line: with the status oext_pinned, the pinned O-ext settings (or the test's)
    and the given files through oext_eval.prepare (no model); otherwise no O-ext file may be given."""
    paths = (args.oext_bank, args.oext_record, args.w1_18_record)
    if settings.doc["overrefusal_bank"]["status"] != "oext_pinned":
        if any(p is not None for p in paths):
            raise Refusal("--oext-bank, --oext-record and --w1-18-record belong to the status oext_pinned")
        return None
    chosen = oext_settings if oext_settings is not None else oe.load_pinned_settings()
    return oe.prepare(chosen, bank_path=args.oext_bank, record_path=args.oext_record, w1_18_path=args.w1_18_record)


def main(argv: Sequence[str] | None = None, *, _settings: Settings | None = None, _loaders: Any = None,
         _oext_settings: Any = None) -> int:
    args = _parser().parse_args(argv)
    invalid = _invalid()
    outputs = [getattr(args, name, None) for name in ("out", "regen_out", "eval_root")]
    before = _footprint(outputs)
    try:
        settings = _settings if _settings is not None else load_pinned_settings()
        if args.command == "check":
            pin = settings.doc["recipe"]
            out = {"settings_sha256": settings.sha256, "engine_identity_sha256": code_identity()["sha256"],
                   "recipe_file_at_pinned_path": sha256_file(ENGINE_REPO / pin["path"]) == pin["file_sha256"],
                   "script_code_sha256": script_code_sha256(),
                   "certified_settings_sha256": certified_settings_sha256(settings),
                   "overrefusal_bank_status": settings.doc["overrefusal_bank"]["status"],
                   "oext": {"branch": settings.doc["oext"]["branch"],
                            "module_at_pin": oe.module_sha256() == settings.doc["oext"]["module_sha256"],
                            "settings_at_pin": sha256_file(oe.SETTINGS_PATH) == settings.doc["oext"]["settings"]["sha256"]},
                   "reference_seeds": sorted(settings.doc["reference_units"]), "references": {}}
            for item in args.reference:
                seed, sep, path = item.partition("=")
                if not sep or not seed.isdigit():
                    raise Refusal("--reference takes SEED=PATH")
                ref = read_reference(path, int(seed), settings)
                out["references"][seed] = {"complete_sha256": ref["complete_sha256"], "pins": "ok"}
            if args.untuned:
                out["untuned"] = {"complete_sha256": read_untuned(args.untuned, settings)["complete_sha256"],
                                  "pins": "ok"}
            _print(out)
            return EXIT_OK
        if args.command == "verify":
            pairs = [tuple(item.split("=", 1)) for item in args.map]
            if any(len(pair) != 2 or not all(pair) for pair in pairs):
                raise Refusal("--map takes RECORDED=LOCAL")
            result = verify_unit(args.unit, pairs)
            _print(result)
            return EXIT_OK if result["complete"] else EXIT_FAILED
        if args.command == "compare":
            target = Path(args.out)
            if target.exists():
                raise Refusal(f"{target} exists: a comparison never overwrites")
            report = compare_certification(args.unit, args.reference, args.reference_eval, settings,
                                           against=args.against)
            write_atomic(target, canonical_json(report))
            _print({"verdict": report["verdict"], "gate": report["gate"], "out": str(target),
                    "sha256": sha256_file(target)})
            return EXIT_OK if report["verdict"] == "pass" else EXIT_CERTIFICATION
        recipe = load_pinned_recipe(args.recipe, settings)
        certification, oext = None, None
        if args.command in ("evaluate", "run"):
            oext = _oext_arg(args, settings, _oext_settings)
        if args.command == "regenerate":
            read_reference(args.reference, args.seed, settings)
            read_pinned_manifest(args.prepared, settings)
        elif args.command == "evaluate":
            plan = make_plan(settings, args.mode, adapter_scale=args.adapter_scale, prefix_file=args.prefix_file,
                             external=args.external, adapter_file=args.adapter_file,
                             adapter_sha256=args.adapter_sha256, record_file=args.adapter_record,
                             record_sha256=args.adapter_record_sha256)
            ctx = preflight(prepared_dir=args.prepared, source_run=args.source_run, reference_path=args.reference,
                            recipe=recipe, settings=settings, plan=plan, certification=_certification_arg(args),
                            oext=oext)
        else:
            plans = [parse_spec(spec, settings, args.prefix_file) for spec in args.evaluations.split(",")]
            read_reference(args.reference, args.seed, settings)
            read_pinned_manifest(args.prepared, settings)
            for plan in plans:
                if plan.mode == "prefix":
                    load_prefix(plan.prefix_file, settings)
                if plan.mode == "external":
                    load_callable(plan.external, settings)
            certification = _certification_arg(args)       # run_sequence checks it (and the gate folder) first
            check_oext(settings, [p.mode for p in plans], oext)
    except Mismatch as exc:
        print(json.dumps({"ok": False, "mismatch": str(exc)}), file=sys.stderr)
        return EXIT_MISMATCH
    except invalid as exc:
        print(json.dumps({"ok": False, "refused": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return EXIT_REFUSED
    try:
        from experiments.safety_selection import runner

        loaders = _loaders
        if loaders is None:
            from experiments.safety_selection.loaders import real_loaders

            loaders = real_loaders()
        session = runner.Session(recipe, loaders)
        if args.command == "regenerate":
            record = regenerate(prepared_dir=args.prepared, seed=args.seed, reference_path=args.reference,
                                out_root=args.out, session=session, settings=settings,
                                wall_limit_seconds=args.wall_limit_seconds)
            _print({"verdict": record["verdict"], "differing": record["comparison"]["differing"],
                    "run_complete_sha256": record["run_complete_sha256"], "stage_seconds": record["stage_seconds"]})
            return EXIT_OK if record["verdict"] == "match" else EXIT_MISMATCH
        if args.command == "evaluate":
            _print(brief(evaluate(ctx, out_dir=args.out, session=session, wall_limit_seconds=args.wall_limit_seconds)))
            return EXIT_OK
        result = run_sequence(prepared_dir=args.prepared, seed=args.seed, reference_path=args.reference,
                              regen_root=args.regen_out, eval_root=args.eval_root, plans=plans, session=session,
                              settings=settings, gate_reference_eval=args.gate_reference_eval,
                              certification=certification, wall_limit_seconds=args.wall_limit_seconds, oext=oext)
        _print(result)
        return result["exit"]
    except Mismatch as exc:
        print(json.dumps({"ok": False, "mismatch": str(exc)}), file=sys.stderr)
        return EXIT_MISMATCH
    except BaseException as exc:  # noqa: BLE001 - every failure is reported with its status
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        if isinstance(exc, KeyboardInterrupt) or _footprint(outputs) != before:
            return EXIT_FAILED                                  # this process wrote something: never "nothing"
        return EXIT_REFUSED if isinstance(exc, invalid) else EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())
