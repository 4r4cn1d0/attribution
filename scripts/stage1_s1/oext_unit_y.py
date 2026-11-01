"""ENGINE Y COPY (gap G1 of block B's pre-flight; addendum section 34 point 3, section 11 point 7, section 15
point 1): B+Qi's O-ext step on engine Y. This file is scripts/stage1_s1/oext_unit.py with only its settings pins
changed: SETTINGS_SHA256 names settings/oext_unit_y.json, OEXT_SETTINGS_SHA256 names settings/oext_eval_y.json, and
main loads the O-ext settings by that pin (a test rebuilds this file from oext_unit.py byte for byte). pack_setup.py
packs it on engine Y's pack only, at scripts/stage1_s1/oext_unit.py, with oext_unit_y.json and oext_eval_y.json at
settings/oext_unit.json and settings/oext_eval.json, the paths the kit's job runner calls and seals; there the
default settings paths below are the engine-Y files. In this checkout those paths hold engine X's files, so a run of
this file here refuses (their bytes are not the pins). Engine X's pack and block A's outputs keep oext_unit.py and
its settings unchanged, and oext_eval.py (every O-ext rule) is engine X's file on both engines.

The O-ext unit runner: the pod-side command that runs the 500-prompt O-ext pass (over-refusal on harmless
prompts) on one engine unit's state or on theta0, and LN-14's theta0 PHTest transfer report (addendum section 20
point 5; section 11 points 1, 7 and 13; section 13; section 24 point 2; REV4 section 6.3: LN-12, LN-14, LN-19,
LN-24; B15 brief Q15). It accepts exactly B15's contract parser (runkit/stage1-olmo/setup/job_runner_stage1.py
``oext_unit_contract``) and changes no engine file and no other S1 file.

Every O-ext rule is scripts/stage1_s1/oext_eval.py's: the bank read by its pinned record, the cap branch and W1-18's
record (``oe.prepare``), W1-18's cut and flag, O with equal weight per prompt, the flag-change share, the sensitivity
cut, the LN-14 bar (``oe.evaluate_oext``, ``oe.evaluate_transfer``). This script only finds the policy state and the
dev-100 answers those functions need, checks every input first, and writes an engine-layout folder:

- ``run --run UNIT --checkpoint e1``: the unit's saved state, restored with its hashes and adapter fingerprint
  verified. The dev-100 answers (route, settings dev100.routes):
  * ``unit_eval``: the unit evaluated the dev bank (an arm, a0 or reference unit of ``engine calibrate``; B15 J9,
    J10, J18): its own answers and judge records at the recipe's cap;
  * ``source_unit``: Branch 128 and a train-only regenerated unit (LN-12, LN-19, Q15): ``--dev100-source``, the
    source unit's stored answers (same arm, seed and checkpoint, the regenerated unit's adapter fingerprint);
  * ``generated``: Branch full and a train-only regenerated unit: made here at the recipe's cap.
- ``run --untuned``: theta0, the policy with its adapter disabled; the dev-100 answers are generated here at the
  recipe's cap (route ``generated``).
- ``transfer --untuned``: LN-14, Branch 128 only (a passing W1-18 record): theta0's PHTest answers once at the full
  cap, judged full and cut, W1-18's bar at its rates (addendum section 24 point 2); a report only.

Under the pending branch (section 13) every command refuses. Inputs are plain paths, as B15 passes them and as the
S1 package's O-ext callers take them (eval_adapter.py, lean_eval_job.py); each is pinned elsewhere: the bank by
oext_eval's pinned record, the record and W1-18's record by oext_eval's settings, the prepared set by its manifest
pin, the recipe by its config SHA-256 and its generation and guard blocks, a unit and a source unit by their
COMPLETE.json file lists and adapter fingerprints. These settings are pinned by SETTINGS_SHA256 and pin oext_eval's
module and settings by SHA-256; engine X is pinned by s1common's check (re-pinned with oext_eval, section 11 point 7).

  python -B scripts/stage1_s1/oext_unit.py run (--run UNIT --checkpoint e1 | --untuned) --prepared P --recipe REC
      --oext-bank F --oext-record F [--w1-18-record F] [--dev100-source SOURCE_UNIT] --out DIR
  python -B scripts/stage1_s1/oext_unit.py transfer --untuned --prepared P --recipe REC --oext-bank F
      --oext-record F [--w1-18-record F] --out DIR

The seal: the answer files hold texts and outcomes; every other file (oext_eval's summaries included) and the
completion record are scanned for every prompt, answer, cut and judge text before COMPLETE.json is written;
COMPLETE.json holds counts of prompts and SHA-256 values only (the O values stay in oext_eval's summary file); stdout
prints the branch, the route, counts of prompts and file hashes only. Exit 0: done; 1: a failure after the folder was
made (error.txt kept); 2: refused before any folder was made.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import (canonical_json, code_identity, jsonl_bytes, read_json,  # noqa: E402
                                                 read_jsonl, sha256_bytes, sha256_file, write_atomic, write_json)
from experiments.safety_selection.config import ConfigError, config_sha256, load_recipe, training_identity  # noqa: E402
from experiments.safety_selection.jobs import AccessError, JobError, check_run_access  # noqa: E402
from experiments.safety_selection.ledger import (COMPLETE, RunDirError, artifact_hashes, create_run_dir,  # noqa: E402
                                                 read_complete)
from experiments.safety_selection.prepare import HiddenAccessError, load_prepared, read_manifest  # noqa: E402
from experiments.safety_selection.sources import DataError  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

oe = importlib.import_module(f"scripts.{HERE.name}.oext_eval")      # this package's own copy

SETTINGS_PATH = HERE / "settings" / "oext_unit.json"
SETTINGS_SHA256 = "80d08721284bbe94661d6fe2cdc58be259db8df66dc681403d7473155c715298"
SETTINGS_NAME = "oext_unit"
OWNER = "scripts/stage1_s1/oext_unit.py"
OEXT_SETTINGS_PATH = "scripts/stage1_s1/settings/oext_eval.json"
OEXT_SETTINGS_SHA256 = "80469a8f728d15192c360f26640c17b7ba652fbd969cfa45f43113c1defd76f0"   # engine Y: oext_eval_y.json
JOB_KIND = "stage1-oext-unit"
COMMANDS = ("run", "transfer")
CONTRACT_CHECKPOINTS = ("e1",)                 # B15's contract: --checkpoint choices
UNTUNED = "untuned"
ROUTES = ("unit_eval", "source_unit", "generated")
DEV_DIR = "dev100"
DEV_GENERATIONS, DEV_GUARD = "generations.jsonl", "guard.jsonl"
DEV_STAGES = ("oext_unit_dev100_generate", "oext_unit_dev100_guard")
STATE_STAGES = {"run": "restore_state", "untuned": "untuned_state"}
SOURCE_FILES = ("COMPLETE.json", "job.json", "eval/{checkpoint}/generations.jsonl", "eval/{checkpoint}/guard.jsonl")
ANSWER_FILES = (f"{DEV_DIR}/{DEV_GENERATIONS}", f"{DEV_DIR}/{DEV_GUARD}", oe.GENERATIONS, oe.GUARD,
                oe.TRANSFER_GENERATIONS, oe.TRANSFER_GUARD)
EXIT_OK, EXIT_FAILED, EXIT_REFUSED = 0, 1, 2
TOP_KEYS = frozenset({"kind", "name", "version", "owner", "requirement", "engine_x", "labels_sha256", "label_entries",
                      "oext", "prepared", "recipes", "unit", "dev100", "untuned", "transfer", "outputs", "ledger",
                      "seal", "exit_codes"})
JOB_KEYS = frozenset({"kind", "version", "command", "state", "run", "checkpoint", "dev100_route", "dev100_source",
                      "unit_complete_sha256", "source_complete_sha256", "manifest_sha256", "recipe_sha256",
                      "code_sha256", "settings_sha256", "script_sha256", "oext", "wall_limit_seconds"})
Refusal = s1.Refusal
_INVALID = (s1.Refusal, ConfigError, JobError, AccessError, DataError, HiddenAccessError, RunDirError,
            FileNotFoundError, FileExistsError, PermissionError, ValueError)


class RunError(RuntimeError):
    """An invariant broke after the folder was made (the folder is kept; it is never completed)."""


# ----- settings ---------------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Settings:
    doc: dict
    sha256: str


def _keys(obj: Any, expected: Sequence[str] | frozenset, what: str) -> dict:
    if not isinstance(obj, dict) or set(obj) != set(expected):
        raise Refusal(f"settings {SETTINGS_NAME}: {what} must have exactly the keys {sorted(expected)}")
    return obj


def _text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Refusal(f"settings {SETTINGS_NAME}: {what} must be a non-empty text")
    return value


def _hex64(value: Any, what: str) -> str:
    if not isinstance(value, str) or not s1.HEX64.match(value):
        raise Refusal(f"settings {SETTINGS_NAME}: {what} must be a SHA-256 (64 lowercase hex)")
    return value


def _positive(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise Refusal(f"settings {SETTINGS_NAME}: {what} must be a positive integer")
    return value


def validate_settings(doc: Any) -> dict:
    """s1common's check (kind, name, registry entries, engine X), then every section of this script."""
    doc = s1.check_settings(doc, SETTINGS_NAME)
    _keys(doc, TOP_KEYS, "the document")
    if doc["version"] != 1 or doc["owner"] != OWNER or doc["label_entries"] != {}:
        raise Refusal(f"settings {SETTINGS_NAME}: version 1 of this script's, with no seed-label entry")
    _text(doc["requirement"], "requirement")
    oext = _keys(doc["oext"], {"module", "module_sha256", "settings", "rule"}, "oext")
    pin = _keys(oext["settings"], {"path", "sha256"}, "oext.settings")
    if (oext["module"], pin["path"]) != (oe.OWNER, OEXT_SETTINGS_PATH):
        raise Refusal(f"settings {SETTINGS_NAME}: oext names the O-ext module and its settings file")
    _hex64(oext["module_sha256"], "oext.module_sha256")
    _hex64(pin["sha256"], "oext.settings.sha256")
    _text(oext["rule"], "oext.rule")
    prepared = _keys(doc["prepared"], {"manifest_sha256", "bank", "rule"}, "prepared")
    _hex64(prepared["manifest_sha256"], "prepared.manifest_sha256")
    if prepared["bank"] != "dev":
        raise Refusal(f"settings {SETTINGS_NAME}: the dev part is the dev bank's")
    _text(prepared["rule"], "prepared.rule")
    recipes = _keys(doc["recipes"], {"allowed", "generation_sha256", "guard_sha256", "rule"}, "recipes")
    allowed = recipes["allowed"]
    if not isinstance(allowed, dict) or not allowed:
        raise Refusal(f"settings {SETTINGS_NAME}: recipes.allowed must name at least one recipe")
    for name, digest in allowed.items():
        _hex64(digest, f"recipes.allowed.{name}")
    _hex64(recipes["generation_sha256"], "recipes.generation_sha256")
    _hex64(recipes["guard_sha256"], "recipes.guard_sha256")
    _text(recipes["rule"], "recipes.rule")
    unit = _keys(doc["unit"], {"kind", "role", "split", "checkpoints", "rule"}, "unit")
    if (unit["kind"], unit["role"], unit["split"]) != ("run-one", "development", "dev"):
        raise Refusal(f"settings {SETTINGS_NAME}: a unit is a development run-one on the dev split")
    if not isinstance(unit["checkpoints"], list) or not unit["checkpoints"] or \
            not set(unit["checkpoints"]) <= set(CONTRACT_CHECKPOINTS):
        raise Refusal(f"settings {SETTINGS_NAME}: unit.checkpoints must be among B15's {list(CONTRACT_CHECKPOINTS)}")
    _text(unit["rule"], "unit.rule")
    dev = _keys(doc["dev100"], {"routes", "source_files", "rule"}, "dev100")
    for name, text in _keys(dev["routes"], ROUTES, "dev100.routes").items():
        _text(text, f"dev100.routes.{name}")
    if dev["source_files"] != list(SOURCE_FILES):
        raise Refusal(f"settings {SETTINGS_NAME}: dev100.source_files are this script's")
    _text(dev["rule"], "dev100.rule")
    untuned = _keys(doc["untuned"], {"access_seed", "rule"}, "untuned")
    _positive(untuned["access_seed"], "untuned.access_seed")
    _text(untuned["rule"], "untuned.rule")
    transfer = _keys(doc["transfer"], {"state", "rule"}, "transfer")
    if transfer["state"] != UNTUNED:
        raise Refusal(f"settings {SETTINGS_NAME}: LN-14's transfer report is theta0's (state untuned)")
    _text(transfer["rule"], "transfer.rule")
    outputs = _keys(doc["outputs"], {"job_kind", "dev_dir", "rule"}, "outputs")
    if (outputs["job_kind"], outputs["dev_dir"]) != (JOB_KIND, DEV_DIR):
        raise Refusal(f"settings {SETTINGS_NAME}: the job kind and the dev folder are this script's")
    _text(outputs["rule"], "outputs.rule")
    ledger = _keys(doc["ledger"], {"stages", "state_stages", "rule"}, "ledger")
    if ledger["stages"] != list(DEV_STAGES) or ledger["state_stages"] != STATE_STAGES:
        raise Refusal(f"settings {SETTINGS_NAME}: the ledger stages are this script's")
    _text(ledger["rule"], "ledger.rule")
    seal = _keys(doc["seal"], {"text_scan_min_chars", "answer_files", "rule"}, "seal")
    _positive(seal["text_scan_min_chars"], "seal.text_scan_min_chars")
    if seal["answer_files"] != list(ANSWER_FILES):
        raise Refusal(f"settings {SETTINGS_NAME}: seal.answer_files are this script's and oext_eval's answer files")
    _text(seal["rule"], "seal.rule")
    codes = _keys(doc["exit_codes"], {"0", "1", "2"}, "exit_codes")
    for code, text in codes.items():
        _text(text, f"exit_codes.{code}")
    return doc


def settings_from_doc(doc: Any) -> Settings:
    """A validated settings document named by the SHA-256 of its canonical bytes (tests and fixtures)."""
    return Settings(validate_settings(doc), sha256_bytes(canonical_json(doc)))


def load_pinned_settings(path: str | Path = SETTINGS_PATH, expected_sha256: str | None = None) -> Settings:
    """The pinned settings (SETTINGS_PATH hashing to SETTINGS_SHA256), validated."""
    doc, digest = s1.load_settings(path, expected_sha256 or SETTINGS_SHA256, SETTINGS_NAME)
    return Settings(validate_settings(doc), digest)


def script_sha256() -> str:
    return sha256_file(Path(__file__).resolve())


# ----- the command line (exactly B15's contract) -------------------------------------------------------------------


def parser() -> argparse.ArgumentParser:
    """B15's oext_unit_contract, option for option (a test compares the two parsers)."""
    ap = argparse.ArgumentParser(prog="scripts/stage1_s1/oext_unit.py",
                                 description="The O-ext pass on an engine unit's state or on theta0, and LN-14's "
                                             "transfer report (B15's contract).")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        p = sub.add_parser(name)
        state = p.add_mutually_exclusive_group(required=True)
        state.add_argument("--run", help="an engine unit folder (its states/CHECKPOINT state)")
        state.add_argument("--untuned", action="store_true", help="theta0: no adapter")
        p.add_argument("--checkpoint", choices=CONTRACT_CHECKPOINTS)
        p.add_argument("--prepared", required=True)
        p.add_argument("--recipe", required=True)
        p.add_argument("--oext-bank", required=True)
        p.add_argument("--oext-record", required=True)
        p.add_argument("--w1-18-record")
        p.add_argument("--dev100-source", help="Branch 128, a regenerated unit: the source unit (LN-19, Q15)")
        p.add_argument("--out", required=True)
    return ap


# ----- the plan (every check before any folder) --------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Unit:
    path: Path
    stored: dict
    marker: dict
    checkpoint: str
    fingerprint: str
    evaluated: bool
    receipt: dict


@dataclasses.dataclass(frozen=True)
class Source:
    path: Path
    marker: dict
    complete_sha256: str
    fingerprint: str
    files: dict
    receipt: dict


@dataclasses.dataclass(frozen=True)
class Plan:
    command: str
    settings: Settings
    oext: Any                        # oext_eval.Prepared
    recipe: dict
    recipe_sha256: str
    prepared_dir: Path
    manifest: dict
    manifest_sha256: str
    dev_items: tuple
    unit: Unit | None
    source: Source | None
    route: str | None
    out_dir: Path

    @property
    def state(self) -> str:
        return UNTUNED if self.unit is None else "run"

    @property
    def label(self) -> str:
        return UNTUNED if self.unit is None else self.unit.checkpoint


def check_recipe(path: str | Path, settings: Settings) -> tuple[dict, str]:
    recipe = load_recipe(Path(path))
    digest = config_sha256(recipe)
    pins = settings.doc["recipes"]
    if digest not in pins["allowed"].values():
        raise Refusal(f"recipe {digest[:16]} is not one of the settings' allowed recipes {sorted(pins['allowed'])}")
    if sha256_bytes(canonical_json(recipe["generation"])) != pins["generation_sha256"]:
        raise Refusal("the recipe's generation block is not the pinned one (one cap and one batch size, section 9)")
    if sha256_bytes(canonical_json(recipe["guard"])) != pins["guard_sha256"]:
        raise Refusal("the recipe's guard block is not the pinned judge")
    return recipe, digest


def check_unit(path: str | Path, checkpoint: str | None, recipe: Mapping, recipe_sha256: str, manifest: Mapping,
               manifest_sha256: str, settings: Settings) -> Unit:
    """A complete engine run-one unit (own files and dependency chain verified) on this engine, the pinned manifest
    and the unit's own recipe, holding the checkpoint's state."""
    from experiments.safety_selection import runner
    from experiments.safety_selection.verify import dependency_receipt

    rules = settings.doc["unit"]
    if checkpoint is None:
        raise Refusal("--run needs --checkpoint (the state the unit saved)")
    if checkpoint not in rules["checkpoints"]:
        raise Refusal(f"--checkpoint {checkpoint} is not one of the settings' {rules['checkpoints']}")
    folder = Path(path)
    try:
        stored, marker, _ = runner._complete_source(folder, "the unit")
    except (JobError, OSError, ValueError) as exc:
        raise Refusal(f"the unit is not usable: {type(exc).__name__}: {exc}") from None
    expected = {"kind": rules["kind"], "role": rules["role"], "split": rules["split"],
                "manifest_sha256": manifest_sha256, "target_checkpoint": checkpoint}
    wrong = sorted(k for k, v in expected.items() if stored.get(k) != v)
    if wrong:
        raise Refusal(f"the unit is not a {rules['role']} {rules['kind']} at {checkpoint} on the pinned manifest "
                      f"(it differs in {wrong})")
    identity = marker["identity"]
    if identity["recipe_sha256"] != recipe_sha256 or identity["training_identity"] != training_identity(recipe):
        raise Refusal("the recipe is not the unit's own recipe (config or training identity)")
    if identity["code_sha256"] != code_identity()["sha256"]:
        raise Refusal("the unit was made on another engine than the one that evaluates it")
    if f"states/{checkpoint}/state.json" not in marker["files"]:
        raise Refusal(f"the unit holds no saved {checkpoint} state")
    check_run_access(stored["role"], stored["split"], stored["seed"], settings.doc["prepared"]["bank"],
                     manifest["data_config"], False)
    bank = stored.get("evaluate_bank")
    if bank not in (None, settings.doc["prepared"]["bank"]):
        raise Refusal(f"the unit evaluated the {bank} bank; only a dev-bank or a train-only unit is used")
    evaluated = bank is not None
    if evaluated and not all(f"eval/{checkpoint}/{name}" in marker["files"] for name in (DEV_GENERATIONS, DEV_GUARD)):
        raise Refusal("the unit evaluated the dev bank but lists no dev answers or judge records")
    named = ((marker.get("checkpoints") or {}).get(checkpoint) or {}).get("adapter_fingerprint")
    receipt = dependency_receipt(folder, "oext_state", checkpoint)
    saved = (receipt.get("state") or {}).get("adapter_fingerprint")
    if not isinstance(named, str) or not s1.HEX64.match(named) or saved != named:
        raise Refusal(f"the unit's saved {checkpoint} state's adapter fingerprint is not the one its COMPLETE.json "
                      "names: the state is another adapter's")
    return Unit(folder, stored, marker, checkpoint, named, evaluated, receipt)


def check_source(path: str | Path, unit: Unit, recipe: Mapping, manifest_sha256: str, settings: Settings) -> Source:
    """The source unit of a regenerated unit (LN-12, LN-19, Q15), packed in part: its required files present, every
    present file one its COMPLETE.json lists with the listed SHA-256, the same arm, seed and checkpoint, a dev-bank
    evaluation on the pinned manifest and an allowed recipe of the same training identity, and the regenerated unit's
    adapter fingerprint (so its stored answers are this adapter's)."""
    from experiments.safety_selection.verify import dependency_receipt

    folder, ck = Path(path), unit.checkpoint
    try:
        marker = read_complete(folder)
    except (OSError, ValueError):
        marker = None
    if not isinstance(marker, dict) or marker.get("complete") is not True or not isinstance(marker.get("files"), dict):
        raise Refusal("the dev-100 source unit holds no complete COMPLETE.json")
    required = [name.format(checkpoint=ck) for name in settings.doc["dev100"]["source_files"]]
    missing = [name for name in required if not (folder / name).is_file()]
    if missing:
        raise Refusal(f"the dev-100 source unit lacks {missing}")
    present = artifact_hashes(folder)
    wrong = sorted(name for name, digest in present.items() if marker["files"].get(name) != digest)
    if wrong:
        raise Refusal(f"{len(wrong)} files of the dev-100 source unit are not the ones its COMPLETE.json lists "
                      f"(first: {wrong[0]})")
    if sha256_file(folder / "job.json") != marker.get("job_sha256"):
        raise Refusal("the dev-100 source unit's job.json is not the one its COMPLETE.json names")
    stored = read_json(folder / "job.json")
    rules = settings.doc["unit"]
    expected = {"kind": rules["kind"], "role": rules["role"], "split": rules["split"], "arm": unit.stored["arm"],
                "seed": unit.stored["seed"], "evaluate_bank": settings.doc["prepared"]["bank"],
                "target_checkpoint": ck, "manifest_sha256": manifest_sha256}
    differ = sorted(k for k, v in expected.items() if stored.get(k) != v)
    if differ:
        raise Refusal(f"the dev-100 source unit is not the regenerated unit's source (it differs in {differ})")
    identity = marker.get("identity") or {}
    if identity.get("recipe_sha256") not in settings.doc["recipes"]["allowed"].values() or \
            identity.get("training_identity") != training_identity(recipe):
        raise Refusal("the dev-100 source unit was not made under an allowed recipe of this training identity")
    fingerprint = ((marker.get("checkpoints") or {}).get(ck) or {}).get("adapter_fingerprint")
    if fingerprint != unit.fingerprint:
        raise Refusal(f"the dev-100 source unit's {ck} adapter fingerprint is not the regenerated unit's (LN-12): "
                      "its stored answers are another adapter's")
    files = {name: marker["files"][name] for name in required[1:]}
    return Source(folder, marker, sha256_file(folder / COMPLETE), fingerprint, files,
                  dependency_receipt(folder, "dev100_source"))


def prepare_plan(command: str, *, run: str | None, untuned: bool, checkpoint: str | None, prepared_dir: str | Path,
                 recipe_path: str | Path, bank_path: str | Path, record_path: str | Path,
                 w1_18_path: str | Path | None, dev100_source: str | Path | None, out_dir: str | Path,
                 settings: Settings, oext_settings: Any) -> Plan:
    """Every check that needs no model, in order, before any folder (each refusal names ids, counts and hashes)."""
    if command not in COMMANDS:
        raise Refusal(f"unknown command {command!r}")
    if (run is None) == (not untuned):
        raise Refusal("exactly one of --run and --untuned")
    out = Path(out_dir)
    if out.exists():
        raise Refusal(f"{out} exists: the pass writes a new folder and never replaces one")
    pin = settings.doc["oext"]
    if oe.module_sha256() != pin["module_sha256"]:
        raise Refusal("the O-ext module is not the one these settings pin")
    if oext_settings.sha256 != pin["settings"]["sha256"]:
        raise Refusal("the O-ext settings are not the ones these settings pin")
    branch = oext_settings.doc["cap"]["branch"]
    if branch == oe.PENDING:
        raise Refusal("the O-ext cap branch is pending W1-18 (addendum section 13): no O-ext pass runs")
    if untuned and (checkpoint is not None or dev100_source is not None):
        raise Refusal("--untuned (theta0) takes no --checkpoint and no --dev100-source")
    if command == "transfer":
        if not untuned:
            raise Refusal("LN-14's transfer report is theta0's: transfer takes --untuned, never --run")
        if branch != "128":
            raise Refusal(f"LN-14's transfer report runs under Branch 128 only (the branch is {branch})")
    prepared = oe.prepare(oext_settings, bank_path=bank_path, record_path=record_path, w1_18_path=w1_18_path)
    if command == "transfer" and (prepared.w1_18 is None or prepared.w1_18.passed is not True):
        raise Refusal("LN-14's transfer report needs a passing W1-18 record")
    recipe, recipe_sha = check_recipe(recipe_path, settings)
    pinned = settings.doc["prepared"]
    try:
        manifest, manifest_sha = read_manifest(prepared_dir, pinned["manifest_sha256"])
    except (DataError, OSError) as exc:
        raise Refusal(f"the prepared set is not the pinned one: {type(exc).__name__}: {exc}") from None
    data = load_prepared(prepared_dir, manifest_sha, banks=(pinned["bank"],))
    dev_items = tuple(item for item in data.banks[pinned["bank"]] if item["kind"] == "overrefusal")
    if len(dev_items) != oext_settings.doc["bank"]["dev100"]["prompts"]:
        raise Refusal(f"the {pinned['bank']} bank holds {len(dev_items)} over-refusal prompts, O-ext's dev part is "
                      f"{oext_settings.doc['bank']['dev100']['prompts']}")
    unit = source = route = None
    if untuned:
        check_run_access("development", "dev", settings.doc["untuned"]["access_seed"], pinned["bank"],
                         manifest["data_config"], False)
        route = "generated" if command == "run" else None
    else:
        unit = check_unit(run, checkpoint, recipe, recipe_sha, manifest, manifest_sha, settings)
        if unit.evaluated:
            if dev100_source is not None:
                raise Refusal("the unit holds its own dev-100 answers: --dev100-source is not taken")
            route = "unit_eval"
        elif branch == "128":
            if dev100_source is None:
                raise Refusal("Branch 128, a train-only unit: LN-19 cuts the source unit's stored dev-100 answers, so "
                              "--dev100-source is needed (B15 brief Q15)")
            source = check_source(dev100_source, unit, recipe, manifest_sha, settings)
            route = "source_unit"
        else:
            if dev100_source is not None:
                raise Refusal("Branch full: a train-only unit's dev-100 answers are generated at the recipe's cap; "
                              "--dev100-source belongs to Branch 128 only")
            route = "generated"
    return Plan(command, settings, prepared, recipe, recipe_sha, Path(prepared_dir), manifest, manifest_sha,
                dev_items, unit, source, route, out)


# ----- the pass ---------------------------------------------------------------------------------------------------


def _oext_job(oext: Any) -> dict:
    return {"branch": oext.branch, "settings_sha256": oext.settings.sha256, "module_sha256": oe.module_sha256(),
            "record_sha256": oext.bank.record_sha256, "bank_sha256": oext.bank.bank_sha256,
            "w1_18_record_sha256": None if oext.w1_18 is None else oext.w1_18.record_sha256}


def validate_job(job: Any) -> dict:
    if not isinstance(job, dict) or set(job) != JOB_KEYS or job["kind"] != JOB_KIND or job["command"] not in COMMANDS:
        raise Refusal("not an O-ext unit job")
    if job["dev100_route"] not in (*ROUTES, None) or (job["command"] == "transfer") != (job["dev100_route"] is None):
        raise Refusal("the job's dev-100 route does not match its command")
    return job


def job_of(plan: Plan) -> dict:
    return validate_job({
        "kind": JOB_KIND, "version": 1, "command": plan.command, "state": plan.state,
        "run": None if plan.unit is None else str(plan.unit.path),
        "checkpoint": None if plan.unit is None else plan.unit.checkpoint, "dev100_route": plan.route,
        "dev100_source": None if plan.source is None else str(plan.source.path),
        "unit_complete_sha256": None if plan.unit is None else plan.unit.receipt["complete_sha256"],
        "source_complete_sha256": None if plan.source is None else plan.source.complete_sha256,
        "manifest_sha256": plan.manifest_sha256, "recipe_sha256": plan.recipe_sha256,
        "code_sha256": code_identity()["sha256"], "settings_sha256": plan.settings.sha256,
        "script_sha256": script_sha256(), "oext": _oext_job(plan.oext), "wall_limit_seconds": None})


def generate_dev(session: Any, policy: Any, plan: Plan, ledger: Any, run_dir: Path) -> tuple[list, dict]:
    """The dev-100 greedy answers at the recipe's generation cap and their judge records, in evaluate_checkpoint's
    record format (route "generated"), written to dev100/; returns (oext_eval Answers, the two files' SHA-256)."""
    from experiments.safety_selection import engine as en
    from experiments.safety_selection import runner
    from experiments.safety_selection.textproc import repeated_ngram_fraction

    recipe, codec, device, label = session.recipe, policy.codec, policy.device, plan.label
    gen = recipe["generation"]
    over = {"over_limit_unscored": True} if gen.get("guard_over_limit") == "unscored" else {}
    items = list(plan.dev_items)
    prompts = [runner._prompt_ids(codec, item, recipe["model"]["max_prompt_tokens"]) for item in items]
    before = (en.lora_fingerprint(policy.named), policy.model.training)

    def on_batch(b: int, index: list[int], batch: list) -> None:
        ledger.progress(DEV_STAGES[0], checkpoint=label, batch=b, rows=len(index))

    with en.preserved_rng(device):
        guard = session.guard(ledger, run_dir)
        with ledger.stage(DEV_STAGES[0], checkpoint=label, prompts=len(prompts), prompt_tokens=sum(map(len, prompts)),
                          max_new_tokens=gen["max_new_tokens"]):
            generations = en.greedy_generate(
                policy.model, prompts, max_new_tokens=gen["max_new_tokens"], stop_ids=codec.stop_ids,
                pad_id=codec.pad_id, device=device, batch_size=gen["batch_size"],
                check=lambda what: ledger.check(f"oext unit dev100 generate {label} {what}"), on_batch=on_batch)
        records = [{"prompt_id": item["prompt_id"], "kind": item["kind"], "prompt_ids": ids, "prompt_tokens": len(ids),
                    "output_ids": list(g.output_ids), "output_tokens": len(g.output_ids), "stop_reason": g.stop_reason,
                    "stop_token": g.stop_token, "empty": not g.output_ids, "text": codec.decode(g.output_ids),
                    "repetition_4gram": repeated_ngram_fraction(g.output_ids, 4)}
                   for item, ids, g in zip(items, prompts, generations, strict=True)]
        with ledger.stage(DEV_STAGES[1], checkpoint=label, items=len(records)):
            guarded = guard.score([(r["prompt_id"], item["prompt"], r["text"]) for r, item in zip(records, items)],
                                  check=lambda what: ledger.check(f"oext unit dev100 guard {label} {what}"), **over)
    if (en.lora_fingerprint(policy.named), policy.model.training) != before:
        raise RunError("the dev-100 pass changed the adapter or the train/eval mode")
    guard_rows = [{"prompt_id": r["prompt_id"], "kind": r["kind"], **g} for r, g in zip(records, guarded, strict=True)]
    folder = run_dir / DEV_DIR
    folder.mkdir()
    gen_bytes, guard_bytes = jsonl_bytes(records), jsonl_bytes(guard_rows)
    write_atomic(folder / DEV_GENERATIONS, gen_bytes)
    write_atomic(folder / DEV_GUARD, guard_bytes)
    return (oe.dev_answers(items, records, guard_rows),
            {f"{DEV_DIR}/{DEV_GENERATIONS}": sha256_bytes(gen_bytes), f"{DEV_DIR}/{DEV_GUARD}": sha256_bytes(guard_bytes)})


def stored_dev(plan: Plan) -> tuple[list, dict]:
    """The stored dev-100 answers of the unit (route unit_eval) or of the source unit (route source_unit), each file
    equal to the SHA-256 its COMPLETE.json lists, before and after the read."""
    if plan.route == "unit_eval":
        root, listed = plan.unit.path, plan.unit.marker["files"]
    else:
        root, listed = plan.source.path, plan.source.marker["files"]
    folder = root / "eval" / plan.unit.checkpoint
    names = {f"eval/{plan.unit.checkpoint}/{name}": name for name in (DEV_GENERATIONS, DEV_GUARD)}
    for rel in names:
        if sha256_file(root / rel) != listed.get(rel):
            raise RunError(f"{rel} of the dev-100 answers changed since its COMPLETE.json was written")
    dev, inputs = oe.dev_answers_from_eval(folder, plan.dev_items)
    if [inputs[f"dev100/{name}"] for name in names.values()] != [listed[rel] for rel in names]:
        raise RunError("the dev-100 answer files changed while they were read")
    return dev, inputs


def _texts(plan: Plan, run_dir: Path, dev: Sequence[Any], min_chars: int) -> list[str]:
    """Every prompt, answer, cut and judge text of the pass of at least ``min_chars`` characters."""
    texts = [item["prompt"] for item in plan.dev_items] + [prompt for _, prompt in plan.oext.bank.rows]
    texts += [a.text for a in dev]
    for rel in ANSWER_FILES:
        path = run_dir / rel
        if path.is_file():
            texts += [row[f] for row in read_jsonl(path) for f in ("text", "guard_answer")
                      if isinstance(row.get(f), str)]
    return sorted({t for t in texts if len(t) >= min_chars})


def _scan(run_dir: Path, texts: Sequence[str], extra: bytes) -> None:
    """No prompt, answer, cut or judge text in a file other than the answer files, nor in the completion record."""
    answer = set(ANSWER_FILES)
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(run_dir).as_posix()
        if rel not in answer and s1._text_hits(path.read_bytes(), texts, 1):
            raise RunError(f"{rel} holds a prompt, answer or judge text; the folder is not completed")
    if s1._text_hits(extra, texts, 1):
        raise RunError("the completion record would hold a prompt, answer or judge text; it is not written")


def execute(plan: Plan, session: Any) -> dict:
    """The pass in a new folder (module doc); returns the completion marker's summary (counts and hashes only)."""
    from experiments.safety_selection import engine as en
    from experiments.safety_selection import runner

    if session.recipe_sha256 != plan.recipe_sha256:
        raise Refusal("the session's recipe is not the plan's")
    job = job_of(plan)
    code = code_identity()
    identity = {**runner._identity(plan.manifest, plan.manifest_sha256, plan.recipe, code),
                "oext_unit": {"script": OWNER, "script_sha256": job["script_sha256"],
                              "settings_sha256": plan.settings.sha256, "oext": job["oext"]}}
    receipts = [r.receipt for r in (plan.unit, plan.source) if r is not None]
    run_dir = create_run_dir(plan.out_dir)
    ledger = None
    try:
        ledger = runner._start(run_dir, job, identity, session, receipts)
        lock = runner.lock_record(session.device, Path.cwd())             # before any model load, as eval-state
        policy = session.policy(ledger, run_dir)
        write_json(run_dir / "assets.json", {"policy": policy.identity, "environment": session.environment,
                                             "loaded_in": dict(session.loaded_in)})
        runner.merge_assets(run_dir, lock, runner.guard_pin(plan.recipe))
        state = None
        if plan.unit is not None:
            state_dir = plan.unit.path / "states" / plan.unit.checkpoint
            with ledger.stage(STATE_STAGES["run"], checkpoint=plan.unit.checkpoint) as info:
                runner._same_state(state_dir, plan.unit.receipt)
                state = en.load_state(state_dir, policy.named, None, policy.device)
                if state["adapter_fingerprint"] != plan.unit.fingerprint:
                    raise RunError("the restored state is not the checked unit's adapter")
                info.update(step=state["step"], adapter_fingerprint=state["adapter_fingerprint"])
            adapter_off = contextlib.nullcontext()
        else:
            if not hasattr(policy.model, "disable_adapter"):
                raise RunError("the policy cannot disable its adapter, so theta0 is not defined")
            with ledger.stage(STATE_STAGES["untuned"], checkpoint=UNTUNED) as info:
                info.update(adapter_fingerprint=en.lora_fingerprint(policy.named), adapter="disabled")
            adapter_off = policy.model.disable_adapter()
        fingerprint = en.lora_fingerprint(policy.named)
        dev: list = []
        dev_inputs: dict = {}
        with adapter_off:
            if plan.command == "run":
                if plan.route == "generated":
                    dev, dev_inputs = generate_dev(session, policy, plan, ledger, run_dir)
                else:
                    dev, dev_inputs = stored_dev(plan)
                summary = oe.evaluate_oext(session=session, policy=policy, codec=policy.codec, ledger=ledger,
                                           run_dir=run_dir, folder=run_dir, prepared=plan.oext, dev=dev,
                                           dev_inputs=dev_inputs, checkpoint=plan.label)
                summary_file = oe.SUMMARY
            else:
                summary = oe.evaluate_transfer(session=session, policy=policy, codec=policy.codec, ledger=ledger,
                                               run_dir=run_dir, folder=run_dir, prepared=plan.oext,
                                               checkpoint=plan.label)
                summary_file = oe.TRANSFER_SUMMARY
        if en.lora_fingerprint(policy.named) != fingerprint:
            raise RunError("the pass changed the adapter")
        bank = summary["bank"]
        prompts = ({"dev100": bank["dev100"], "phtest": bank["phtest"], "pooled": bank["prompts"]}
                   if plan.command == "run" else {"phtest": bank["phtest"]})
        answer_files = {rel: sha256_file(run_dir / rel) for rel in ANSWER_FILES if (run_dir / rel).is_file()}
        result = {
            "command": plan.command, "state": plan.state, "branch": plan.oext.branch, "dev100_route": plan.route,
            "checkpoint": plan.label, "prompts": prompts,
            "cap": {"cut_tokens": summary["cap"]["cut_tokens"],
                    "phtest_max_new_tokens": summary["cap"]["phtest_max_new_tokens"],
                    "recipe_max_new_tokens": plan.recipe["generation"]["max_new_tokens"]},
            "adapter_fingerprint": fingerprint,
            "unit": None if plan.unit is None else {
                "complete_sha256": plan.unit.receipt["complete_sha256"], "state_sha256": plan.unit.receipt["state_sha256"],
                "arm": plan.unit.stored["arm"], "seed": plan.unit.stored["seed"], "step": state["step"]},
            "dev100_source": None if plan.source is None else {
                "complete_sha256": plan.source.complete_sha256, "adapter_fingerprint": plan.source.fingerprint,
                "files": dict(plan.source.files)},
            "dev100_inputs": dict(sorted(dev_inputs.items())),
            "answer_files": answer_files,
            "summary_file": {summary_file: sha256_file(run_dir / summary_file)},
            "oext": job["oext"],
            "seal": plan.settings.doc["seal"]["rule"],
        }
        texts = _texts(plan, run_dir, dev, plan.settings.doc["seal"]["text_scan_min_chars"])
        _scan(run_dir, texts, canonical_json(result))
        return runner._finish(run_dir, ledger, JOB_KIND, identity, result)
    except BaseException as exc:
        runner._fail(run_dir, ledger, exc)
        raise


def brief(result: Mapping[str, Any]) -> dict:
    """What is printed: the branch, the route, counts of prompts and file hashes; never an O value, a flag, an answer
    length or a judge label."""
    return {"ok": True, "kind": JOB_KIND, "command": result["command"], "state": result["state"],
            "branch": result["branch"], "dev100_route": result["dev100_route"], "prompts": dict(result["prompts"]),
            "phtest_max_new_tokens": result["cap"]["phtest_max_new_tokens"],
            "files": {**result["answer_files"], **result["summary_file"]},
            "complete_sha256": sha256_file(Path(result["run_dir"]) / COMPLETE), "out": result["run_dir"]}


def _say(obj: Any, stream=None) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True), file=stream or sys.stdout)


def main(argv: Sequence[str] | None = None, *, loaders: Any = None, settings: Settings | None = None,
         oext_settings: Any = None) -> int:
    """The command line. ``loaders``, ``settings`` and ``oext_settings`` replace the engine's real loaders and the
    pinned settings (ENGINEERING FIXTURES in tests only)."""
    args = parser().parse_args(argv)
    try:
        chosen = settings if settings is not None else load_pinned_settings()
        oset = oext_settings if oext_settings is not None else \
            oe.load_pinned_settings(expected_sha256=OEXT_SETTINGS_SHA256)
        plan = prepare_plan(args.command, run=args.run, untuned=args.untuned, checkpoint=args.checkpoint,
                            prepared_dir=args.prepared, recipe_path=args.recipe, bank_path=args.oext_bank,
                            record_path=args.oext_record, w1_18_path=args.w1_18_record,
                            dev100_source=args.dev100_source, out_dir=args.out, settings=chosen, oext_settings=oset)
    except _INVALID as exc:
        _say({"ok": False, "refused": f"{type(exc).__name__}: {exc}"}, sys.stderr)
        return EXIT_REFUSED
    except Exception as exc:  # noqa: BLE001 - the plan makes no folder, so any error in it is a refusal (exit 2)
        _say({"ok": False, "refused": f"unexpected {type(exc).__name__} in the plan: {exc}"}, sys.stderr)
        return EXIT_REFUSED
    try:
        from experiments.safety_selection import runner

        if loaders is None:
            from experiments.safety_selection.loaders import real_loaders

            loaders = real_loaders()
        session = runner.Session(plan.recipe, loaders)
        result = execute(plan, session)
    except BaseException as exc:  # noqa: BLE001 - every failure is reported with its status
        _say({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, sys.stderr)
        if isinstance(exc, KeyboardInterrupt) or Path(args.out).exists():
            return EXIT_FAILED
        return EXIT_REFUSED if isinstance(exc, _INVALID) else EXIT_FAILED
    _say(brief(result))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
