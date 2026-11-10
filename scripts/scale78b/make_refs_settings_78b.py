"""The per-family, per-seed settings of the 7-8B evaluation-only references (R2 Track R; Part 2 sections 3.1, 3.2,
16.1; DES F1, F2; the build rulings GXB O2 (B10's certification), O3 (no record names a file it did not read), X3,
R-5 (one index per pin, fill once) of 8 Nov 2026).

    python -B scripts/scale78b/make_refs_settings_78b.py [--pins P] [--settings-dir D]          # write the files
    python -B scripts/scale78b/make_refs_settings_78b.py [--pins P] [--settings-dir D] --check  # compare with them
    python -B scripts/scale78b/make_refs_settings_78b.py --refs-78b FAMILY SEED   # print the kit pin's form

The 1B reference scripts (scripts/stage1_s1/eval_adapter.py, B10; scripts/stage1_s1/safe_lora.py, B11) pin OLMo-2-1B's
prepared set, recipe, Gate A units, model snapshots, 16 blocks and K = 39. This maker derives, for each family F and
each reference seed S of the reference set (the 6-seed set 1102-1107, DES F1; the 3-seed fallback 1102-1104), two
settings files in the 1B files' own schema (the same kind, name, owner and keys, so the unchanged 1B validators
accept them), with every per-family value taken from settings/refs_pins_78b.json:

  eval_adapter__F__S.json  B10 for seed S: F's main recipe MAIN_F (path, file, config and training identity) and
                           manifest; the reference units 1101 (the untuned unit's seed: theta0 is its init unit; no
                           reference point runs at 1101, P2 section 3.1) and S; the certification seed S (GXB O2: one
                           certification per reference seed, against that seed's a0 unit; its report is the seed's
                           --certification-report) and the sampled-answer count (harm prompts x MAIN_F's harm samples);
                           the scale points (DES F2: 1, 0.9, 0.75, 0.5, 0; the 3-seed fallback 1, 0.75, 0.5, 0); the 1B
                           safety prefix (the same text by its SHA-256, a user-turn prefix on both families); the Safe
                           LoRA file transform = the unchanged safe_lora.py with safe_lora__F__S.json; O-ext = the
                           family's scripts/scale78b/settings/oext_eval__F.json (Track O's file, by path and SHA-256)
                           and its cap branch
  safe_lora__F__S.json     B11 for seed S: F's block count (32) and LoRA shape from MAIN_F (7 modules, rank, alpha, the
                           224 matrices, the trainable-parameter count); seed S's accepted e1 fingerprint; K = 78 of
                           224 (1B's share, 39 of 112; DES F2), the conditional point at K = 0 (not run at 7-8B; the
                           wrapper refuses it: GXB R-37), certify K = 0; the aligned model = KIT's instruct
                           model; the unaligned model = KIT's base repository; the model revisions, dtypes and file pins
                           null until the lead's Hub read (DES F2)

Each seed's a0 unit is GXB R-35's (1102 the reused side unit; 1103 the reused side unit on OLMo-2-7B and N's a0-1103 on
Llama-3.1-8B; 1104 block A's a0; 1105-1107 block B's a0): the pins name each unit's source, and the wait of a null unit
pin names the event that fills it; seed 1101's fingerprints are full 64-hex values whose first 16 hex must equal P1
section 2.1's prefixes (GXB R-36). Both files record the registry they are written on (labels_sha256, s1common's), and
the 1B prose that an output copies or that names a 1B stage is rewritten for 7-8B (RV-3, GXB R-38).

and one index per family and seed, REFS-78B__F__S.json: the two files, the family's O-ext eval and W1-18 settings
(Track O's files, which eval_adapter__F__S binds), their SHA-256, the family's manifest and branch, and the waits (a
null pin, its event, the settings fields it nulls). Nothing pins an index but the kit's pin (REFS_78B[F][S], the lead's
and K3's), and refs_78b.py holds no index hash, so a fill reaches only the indexes whose files it changes: a seed's unit
pin its own index (seed 1101's every index of the family), the Hub read every index of the family, a branch fill (Track
O's oext_eval__F) every index of the family.

How a pin is filled: edit settings/refs_pins_78b.json (and for an O-ext fill, run Track O's maker first: this maker reads
Track O's files from the settings folder); run this maker; run the tests under scripts/scale78b/tests/refs; print the
form (--refs-78b F S) and fill the kit's pin by a recorded step; commit by explicit path. Nothing here reads a model, a
prepared row, a unit, an answer or a prompt; it reads the 1B settings files, the configs it names and Track O's files.
The 3-seed fallback is one pins edit (reference_set: three_seed) and a maker run: the run writes seeds 1102-1104's
files and removes seeds 1105-1107's (RV-5), so no stale index is left for the kit to pin.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe, training_identity  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_DIR = HERE / "settings"
PINS_PATH = SETTINGS_DIR / "refs_pins_78b.json"
PINS_KIND = "scale78b refs pins"
INDEX_KIND = "scale78b refs settings index"
INDEX_NAME = "REFS-78B__{family}__{seed}.json"
FAMILIES = ("olmo2-7b", "llama31-8b")
UNTUNED_SEED = 1101                      # theta0 is the init unit of seed 1101 (RK KIT a0_units["untuned"])
REFERENCE_SETS = {                       # DES F1: the 6-seed set; its pre-set fallback, the 3-seed set
    "six_seed": {"seeds": (1102, 1103, 1104, 1105, 1106, 1107), "planned": [0.9, 0.75, 0.5],
                 "curve": [1.0, 0.9, 0.75, 0.5, 0.0], "allowed": [1.0, 0.9, 0.75, 0.5, 0.0]},
    # P2 sections 3.1-3.2 (GXB R-40 withdrawn; RRV-1): the fallback's grid is {1, 0.75, 0.5, 0}, so 0.9 is not allowed
    "three_seed": {"seeds": (1102, 1103, 1104), "planned": [0.75, 0.5], "curve": [1.0, 0.75, 0.5, 0.0],
                   "allowed": [1.0, 0.75, 0.5, 0.0]},
}
ALL_SEEDS = (UNTUNED_SEED,) + REFERENCE_SETS["six_seed"]["seeds"]
# Safe LoRA's points (DES F2; GXB R-37): K = 78 of 224 = 1B's share 39 of 112 (39 x 2; P2 section 3.2). Only default and
# certify run at 7-8B; the unchanged B11 validator needs an integer K for conditional, so it is 0 (it maps nothing) and
# refs_78b.py refuses that point by name. Certify maps nothing.
K_DEFAULT_1B, MATRICES_1B = 39, 112
K_CONDITIONAL = 0
# GXB R-35: the a0 unit each reference seed's certification pins (the unit trained at that seed under MAIN_F, with its
# own e1 evaluation); 1101 is the untuned unit's seed (its reused side unit).
SOURCES = {family: {1101: "side_unit", 1102: "side_unit",
                    1103: "side_unit" if family == "olmo2-7b" else "block0_a0",
                    1104: "block_a_a0", 1105: "block_b_a0", 1106: "block_b_a0", 1107: "block_b_a0"}
           for family in ("olmo2-7b", "llama31-8b")}
# GXB R-36: seed 1101's fingerprints are full 64-hex values whose first 16 hex equal P1 section 2.1's prefixes
# (R: research/experiments/2026-11-05-78b-preregistration-part1.md section 2.1, "The side units' fingerprints").
P1_1101_PREFIXES = {"olmo2-7b": {"q_fingerprint": "3c7344c178b47e5b", "e1_fingerprint": "9d5d5d8b2eb40262"},
                    "llama31-8b": {"q_fingerprint": "ac05caca1bdfac5b", "e1_fingerprint": "ee44580dfa016b67"}}
# The 1B settings files, by SHA-256 (M: shasum -a 256 at MAIN bfda225, 8 Nov 2026); a changed 1B file refuses.
BASE = {
    "eval_adapter": ("scripts/stage1_s1/settings/eval_adapter.json",
                     "9cc654ecef9fd35664599baba49eaced218afaa6a6a738771d93d962314fbe9b"),
    "safe_lora": ("scripts/stage1_s1/settings/safe_lora.json",
                  "c5610c3d4f0a0809e391055d84697fd62b9a15cf16e0b1f63aee02b03b6d14cf"),
}
SAFE_LORA_MODULE = ("scripts/stage1_s1/safe_lora.py", "5f6b782255f7207645659cc25ea8864c85aeb2d32533acab342175d0217757b4")
OEXT_FILES = ("oext_eval", "limits_overrefusal_checks")     # Track O's per-family files that B10's settings bind
ROLES = ("eval_adapter", "safe_lora") + OEXT_FILES
UNIT_EVENT = {   # GXB R-35, R-36: the unit each seed pins and the event that fills its pins
    "side_unit": "seed {seed}'s a0 unit is the family's reused side unit a0-{seed} (GXB R-35; RK KIT a0_units[{seed}], "
                 "whose path and COMPLETE.json SHA-256 are already pinned here): the lead reads its e1 and q adapter "
                 "fingerprints, full 64-hex values, from the unit's COMPLETE.json (hashes only) into refs_pins_78b.json "
                 "families.<family>.units.{seed} by a recorded step",
    "block0_a0": "seed {seed}'s a0 unit is N's a0-{seed} (block 0; ruling 8; GXB R-35): after block 0's record-done, the "
                 "lead records its path, COMPLETE.json SHA-256 and e1 and q adapter fingerprints (hashes only) in "
                 "refs_pins_78b.json families.<family>.units.{seed} by a recorded step",
    "block_a_a0": "seed {seed}'s a0 unit is block A's a0 at seed {seed} (GXB R-35): after block A's record-done, the lead "
                  "records its path, COMPLETE.json SHA-256 and e1 and q adapter fingerprints (hashes only) in "
                  "refs_pins_78b.json families.<family>.units.{seed} by a recorded step",
    "block_b_a0": "seed {seed}'s a0 unit is block B's a0 at seed {seed} (GXB R-35): after block B's record-done, the lead "
                  "records its path, COMPLETE.json SHA-256 and e1 and q adapter fingerprints (hashes only) in "
                  "refs_pins_78b.json families.<family>.units.{seed} by a recorded step",
}
R36_NOTE = (" (GXB R-36: full 64-hex values; the maker refuses a value whose first 16 hex differ from P1 section 2.1's "
            "prefix)")
EVENTS = {
    "HUB_READ": "the lead's Hub read of the family's models (DES F2; P2 section 3.2): the unaligned base repository's "
                "full commit, dtype and safetensors file pins (name, bytes, LFS SHA-256; with total_bytes, "
                "stored_dtype and hub_files), and the aligned instruct model's dtype and file pins at RK KIT's "
                "revision, in refs_pins_78b.json families.<family>.models by a recorded step (Llama-3.1-8B's base "
                "repository is gated: if its access check fails, Llama's Safe LoRA is not run, stated)",
}
REQUIREMENT = {
    "eval_adapter": "B10 at 7-8B (Part 2 sections 3.1, 3.2, 16.1; DES F1, F2; GXB O2): the evaluation-only references "
                    "(the safety prompt as a user-turn prefix, adapter scaling, Safe LoRA's file form) on the "
                    "family's a0 e1 adapter of seed {seed}, re-made by the train-only regeneration and accepted by its "
                    "fingerprint, run by scripts/scale78b/refs_78b.py eval_adapter with this file; the certification "
                    "of seed {seed} (its report is this seed's --certification-report; a failed certification stops "
                    "every evaluation-only reference)",
    "safe_lora": "B11 at 7-8B (Part 2 section 3.2; DES F2): Safe LoRA at K = 78 of the family's 224 adapted matrices "
                 "(1B's share, 39 of 112; label: chosen after the stage-1 reading, it reads the rule's form only) on "
                 "seed {seed}'s a0 e1 adapter, run by scripts/scale78b/refs_78b.py safe_lora with this file",
}

# RV-3, GXB R-38: the 1B prose fields that a B10 output copies or that name a 1B stage, rewritten for 7-8B ("Gate A" at
# 1B is the seed's pinned a0 unit here, R-35). The B10 code's own messages keep 1B's terms; refs_78b.py writes a terms
# record beside each output that says what they mean at 7-8B.
PROSE_B10_CERT = {
    "gate": ("the certify evaluation of seed S's regenerated a0 e1 adapter must reproduce its pinned a0 unit's own e1 "
             "evaluation (GXB R-35): the same sampled answers (expected_sampled_answers) and no differing gate label "
             "(gate_fields: the valid flag and the Safety label) in guard_samples.jsonl, each reference file checked by "
             "the SHA-256 the unit's COMPLETE.json lists; the comparison report is seed S's --certification-report "
             "(GXB O2)"),
    "reference_rule": ("the reference of seed S is the a0 unit trained at seed S under MAIN_F on the family's manifest "
                       "and engine, with its own e1 evaluation (GXB R-35: 1102 the reused side unit; 1103 the reused "
                       "side unit on OLMo-2-7B and N's a0-1103 on Llama-3.1-8B; 1104 block A's a0; 1105-1107 block "
                       "B's a0), pinned by its COMPLETE.json SHA-256 and its adapter fingerprints"),
}
PROSE_B10_EXIT3 = ("the regenerated adapter's fingerprints (or its trajectory, data or training identity) differ from the "
                   "pinned record of the seed's a0 unit (GXB R-35), so the state is never evaluated")
PROSE_B10_REGEN_OUT = ("ROOT/job.json, ROOT/run/ and ROOT/regeneration.json: the train-only regeneration of the seed's a0 "
                       "e1 adapter and its comparison with the pinned record of the seed's a0 unit")
PROSE_B10_REGEN_RULE = ("the seed's a0 e1 adapter is re-made by the engine's train-only run-one (the a0 development job) "
                        "under MAIN_F on the family's manifest, and accepted only if the compared trajectory fields, "
                        "checkpoint fields (the q and e1 adapter fingerprints among them) and identity fields (the data "
                        "and the training identity) equal the pinned record of the seed's a0 unit (GXB R-35); else "
                        "exit 3, and the state is never evaluated (P2 section 3.2: accepted by its fingerprint)")
PROSE_B10_OEXT = ("O-ext at 7-8B (P2 sections 4.1-4.4): with the status oext_pinned every evaluation, certify included, "
                  "runs the shared O-ext evaluation (scripts/stage1_s1/oext_eval.py with the family's settings "
                  "oext_eval__F.json and its cap branch, Track O) after the engine's evaluation, on the engine's own "
                  "dev-100 answers and the sealed PHTest prompts, and writes its three files beside the engine's 8; "
                  "certify records O-ext as a report and never gates on it; under the pending branch only certify runs, "
                  "without O-ext")


def index_name(family: str, seed: int) -> str:
    return INDEX_NAME.format(family=family, seed=seed)


def file_name(role: str, family: str, seed: int | None = None) -> str:
    return f"{role}__{family}.json" if seed is None else f"{role}__{family}__{seed}.json"


def label(path: Path) -> str:
    """A settings path label: relative to the repository root when the file lies inside it, else absolute."""
    path = Path(path).resolve()
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def dumps(doc: dict) -> bytes:
    return (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _hex(value, what: str, nullable: bool = True, length: int = 64):
    if value is None and nullable:
        return None
    if not (isinstance(value, str) and len(value) == length and all(c in "0123456789abcdef" for c in value)):
        raise s1.Refusal(f"{what} must be {length} lowercase hex{' or null' if nullable else ''}")
    return value


def _text(value, what: str, nullable: bool = True):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip():
        raise s1.Refusal(f"{what} must be a text{' or null' if nullable else ''}")
    return value


def _int(value, what: str, low: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < low:
        raise s1.Refusal(f"{what} must be an integer of at least {low}")
    return value


def load_pins(path: Path = PINS_PATH) -> tuple[dict, str]:
    data = Path(path).read_bytes()
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or (doc.get("kind"), doc.get("version")) != (PINS_KIND, 1):
        raise s1.Refusal("refs_pins_78b.json is not the scale78b refs pins file (version 1)")
    if doc.get("reference_set") not in REFERENCE_SETS:
        raise s1.Refusal(f"reference_set must be one of {list(REFERENCE_SETS)}")
    if set(doc.get("families") or {}) != set(FAMILIES):
        raise s1.Refusal(f"refs_pins_78b.json must name exactly the families {list(FAMILIES)}")
    return doc, sha256_bytes(data)


def load_base(role: str) -> dict:
    rel, pin = BASE[role]
    data = (REPO / rel).read_bytes()
    if sha256_bytes(data) != pin:
        raise s1.Refusal(f"{rel} hashes to {sha256_bytes(data)}, the maker pins {pin}: the 1B files stay byte for byte")
    return s1.strict_json(data)


class Family:
    """One family's derivation: its pins, Track O's O-ext files it binds, and per seed its files and waits."""

    def __init__(self, family: str, pins: dict, reference_set: str, settings_dir: Path = SETTINGS_DIR):
        self.family, self.pins, self.dir = family, pins, Path(settings_dir)
        self.set = REFERENCE_SETS[reference_set]
        main = pins.get("main")
        if not isinstance(main, dict) or set(main) != {"name", "config_sha256"}:
            raise s1.Refusal(f"{family}: main must be {{name, config_sha256}}")
        self.main_rel = f"experiments/safety_selection/configs/{main['name']}.json"
        self.main = load_recipe(REPO / self.main_rel)
        if config_sha256(self.main) != _hex(main["config_sha256"], f"{family} main.config_sha256", nullable=False):
            raise s1.Refusal(f"{family}: {main['name']} hashes to {config_sha256(self.main)}, the pin is "
                             f"{main['config_sha256']}")
        _hex(pins.get("manifest_sha256"), f"{family} manifest_sha256", nullable=False)
        self.blocks = _int(pins.get("blocks"), f"{family} blocks")
        self.harm = _int(pins.get("harm_prompts"), f"{family} harm_prompts")
        units = pins.get("units")
        if not isinstance(units, dict) or set(units) != {str(s) for s in ALL_SEEDS}:
            raise s1.Refusal(f"{family}: units must name exactly the seeds {list(ALL_SEEDS)}")
        for seed, unit in units.items():
            keys = {"source", "unit", "complete_sha256", "e1_fingerprint", "q_fingerprint"}
            if not isinstance(unit, dict) or set(unit) != keys:
                raise s1.Refusal(f"{family}: unit {seed} must be {{{', '.join(sorted(keys))}}}")
            if unit["source"] != SOURCES[family][int(seed)]:
                raise s1.Refusal(f"{family}: unit {seed}'s source is {unit['source']!r}; GXB R-35 names "
                                 f"{SOURCES[family][int(seed)]!r}")
            _text(unit["unit"], f"{family} unit {seed} path")
            for key in ("complete_sha256", "e1_fingerprint", "q_fingerprint"):
                _hex(unit[key], f"{family} unit {seed} {key}")
        for key, prefix in P1_1101_PREFIXES[family].items():             # GXB R-36
            value = units[str(UNTUNED_SEED)][key]
            if value is not None and not value.startswith(prefix):
                raise s1.Refusal(f"{family}: unit 1101's {key} does not start with P1 section 2.1's prefix {prefix}")
        untuned = pins.get("untuned")
        if not isinstance(untuned, dict) or set(untuned) != {"unit", "complete_sha256", "seed"} or \
                untuned["seed"] != UNTUNED_SEED:
            raise s1.Refusal(f"{family}: untuned must be {{unit, complete_sha256, seed {UNTUNED_SEED}}}")
        _text(untuned["unit"], f"{family} untuned unit", nullable=False)
        _hex(untuned["complete_sha256"], f"{family} untuned complete_sha256", nullable=False)
        self.oext = {}
        for role in OEXT_FILES:
            path = self.dir / file_name(role, family)
            try:
                data = path.read_bytes()
            except OSError as exc:
                raise s1.Refusal(f"{family}: Track O's {path.name} cannot be read ({type(exc).__name__})") from None
            self.oext[role] = (path, sha256_bytes(data), s1.strict_json(data))
        cap = self.oext["oext_eval"][2]["cap"]
        if cap["w1_18"]["settings_sha256"] != self.oext["limits_overrefusal_checks"][1]:
            raise s1.Refusal(f"{family}: Track O's oext_eval__{family}.json does not bind its W1-18 settings file")
        self.branch, self.record_sha256 = cap["branch"], cap["w1_18"]["record_sha256"]

    # ----- per seed ----------------------------------------------------------------------------------------------

    def unit_waits(self, seed: int, fields: list[tuple[str, str]], role: str, waits: dict) -> None:
        unit = self.pins["units"][str(seed)]
        null = [(path, kind) for path, kind, key in fields if unit[key] is None]
        if null:
            event = UNIT_EVENT[SOURCES[self.family][seed]].format(seed=seed) + (R36_NOTE if seed == UNTUNED_SEED else "")
            entry = waits.setdefault(f"REF_UNIT_{seed}", {"pin": f"REF_UNIT_{seed}", "event": event,
                                                         "where": [f"families.{self.family}.units.{seed}"],
                                                         "roles": [], "fields": {}})
            entry["roles"].append(role)
            entry["fields"][role] = [{"path": path, "kind": kind} for path, kind in null]

    def eval_adapter(self, seed: int, safe_lora_sha: str, waits: dict) -> dict:
        doc = load_base("eval_adapter")
        rel = self.main_rel
        doc["recipe"] = {"path": rel, "file_sha256": sha256_file(REPO / rel),
                         "config_sha256": config_sha256(self.main), "training_identity": training_identity(self.main)}
        doc["prepared"]["manifest_sha256"] = self.pins["manifest_sha256"]
        refs = {}
        for s in (UNTUNED_SEED, seed):
            unit = self.pins["units"][str(s)]
            refs[str(s)] = {"unit": unit["unit"], "complete_sha256": unit["complete_sha256"],
                            "fingerprint_prefixes": {"e1": unit["e1_fingerprint"], "q": unit["q_fingerprint"]},
                            "role": (f"{self.family}: the a0 unit at e1 of seed {s}"
                                     + (" (the untuned unit's seed; no reference point runs at 1101, P2 section 3.1)"
                                        if s == UNTUNED_SEED else " (a reference seed, DES F1)"))}
            self.unit_waits(s, [(f"reference_units.{s}.unit", "text", "unit"),
                                (f"reference_units.{s}.complete_sha256", "sha256", "complete_sha256"),
                                (f"reference_units.{s}.fingerprint_prefixes.e1", "sha256", "e1_fingerprint")],
                            "eval_adapter", waits)
        doc["reference_units"] = refs
        untuned = self.pins["untuned"]
        doc["untuned_unit"].update(unit=untuned["unit"], complete_sha256=untuned["complete_sha256"], seed=UNTUNED_SEED,
                                   checkpoint="init",
                                   role=f"{self.family}: theta0, the untuned model's init unit of seed 1101 (RK KIT "
                                        "a0_units). Not compared at 7-8B (GXB R-34): refs_78b.py refuses check "
                                        "--untuned and compare --against untuned; the curve's lambda = 0 end is "
                                        "theta0's own O measurement from the o_only pass under MAIN_F")
        doc["certification"]["seed"] = seed
        doc["certification"]["expected_sampled_answers"] = self.harm * self.main["generation"]["harm_samples"]["count"]
        doc["labels_sha256"] = s1.labels_sha256()                     # RV-2: the registry these files are written on
        doc["certification"].update(PROSE_B10_CERT)
        doc["exit_codes"]["3"] = PROSE_B10_EXIT3
        doc["outputs"]["regenerate"] = PROSE_B10_REGEN_OUT
        doc["regeneration"]["rule"] = PROSE_B10_REGEN_RULE
        doc["oext"]["rule"] = PROSE_B10_OEXT
        scale = doc["adapter_scale"]
        scale.update(allowed=list(self.set["allowed"]), planned=list(self.set["planned"]), curve=list(self.set["curve"]),
                     rule=("DES F2: lora_B <- lambda * lora_B in every adapted matrix of the regenerated a0 e1 adapter "
                           "(accepted by its fingerprint); the curve is the planned points with lambda = 1 (the "
                           "certification) and lambda = 0; matched on L as PR4 section 5.3 says"))
        doc["prefix"]["status"] = ("7-8B (P2 section 3.2; DES F2): 1B's safety-prompt text verbatim (the same "
                                   "SHA-256) as a user-turn prefix on both families; OLMo-2 has no system turn, and "
                                   "one rule across families keeps SP comparable; a Llama system-turn form is not run "
                                   "(a limit, P2 section 16.4)")
        entry = doc["external_transforms"]["safe_lora"]
        if (entry["module"], entry["module_sha256"]) != SAFE_LORA_MODULE:
            raise s1.Refusal("the 1B B10 settings no longer allowlist the pinned safe_lora.py")
        entry["settings"] = {"path": label(self.dir / file_name("safe_lora", self.family, seed)),
                             "sha256": safe_lora_sha}
        entry["role"] = "B11 Safe LoRA at 7-8B (P2 section 3.2), file form, with the family's per-seed settings"
        path, sha, _ = self.oext["oext_eval"]
        doc["oext"]["settings"] = {"path": label(path), "sha256": sha}
        doc["oext"]["branch"] = self.branch
        doc["requirement"] = REQUIREMENT["eval_adapter"].format(seed=seed)
        return doc

    def safe_lora(self, seed: int, waits: dict) -> dict:
        doc = load_base("safe_lora")
        lora = self.main["model"]["lora"]
        modules = list(lora["target_modules"])
        matrices = self.blocks * len(modules)
        unit = self.pins["units"][str(seed)]
        doc["adapter"].update(
            modules=modules, blocks=self.blocks, rank=lora["r"], lora_alpha=lora["alpha"], matrices=matrices,
            parameters=lora["expected_trainable_parameters"],
            accepted={str(seed): {"fingerprint": unit["e1_fingerprint"], "source_unit": unit["unit"],
                                  "source_complete_sha256": unit["complete_sha256"]}},
            acceptance_rule=(f"{self.family}: the a0 e1 adapter of seed {seed} is accepted only if its engine "
                             "fingerprint equals the pinned one (the seed's a0 unit; REF R.0.7's rule)"))
        self.unit_waits(seed, [(f"adapter.accepted.{seed}.fingerprint", "sha256", "e1_fingerprint"),
                               (f"adapter.accepted.{seed}.source_unit", "text", "unit"),
                               (f"adapter.accepted.{seed}.source_complete_sha256", "sha256", "complete_sha256")],
                        "safe_lora", waits)
        if matrices * K_DEFAULT_1B % MATRICES_1B:
            raise s1.Refusal(f"{self.family}: {matrices} matrices do not keep 1B's share as a whole K")
        points = doc["transform"]["points"]
        points["default"].update(k=matrices * K_DEFAULT_1B // MATRICES_1B,
                                 status=(f"the one pre-registered 7-8B point: K = {matrices * K_DEFAULT_1B // MATRICES_1B} "
                                         f"of {matrices}, 1B's share (39 of 112 = 34.8%; DES F2; P2 section 3.2); "
                                         "label: chosen after the stage-1 reading, it reads the rule's form only"))
        k = matrices * K_DEFAULT_1B // MATRICES_1B
        points["conditional"].update(k=K_CONDITIONAL,
                                     status=("not run at 7-8B (GXB R-37; P2 section 3.2 names K = 78 only): K = 0, it "
                                             "maps nothing; refs_78b.py refuses this point by name; the $0 check's "
                                             "report row for it is empty"))
        points["certify"]["status"] = ("certify (K = 0, maps nothing): the certification of B10's file path for this "
                                       "seed's a0 e1 adapter; never a reference point")
        doc["v_diagnostic"]["measure"] = (f"per matrix ||V - V'||_F / ||V||_F, each matrix's cosine and rank under V and "
                                          f"V', and whether the default point's mapped set (K = {k} of {matrices}, the "
                                          "fast form, the same ranking rule) changes under V'")
        doc["labels_sha256"] = s1.labels_sha256()                     # RV-2
        models = self.pins["models"]
        hub_null = []
        for role in ("aligned", "unaligned"):
            spec = models[role]
            out = {k: v for k, v in doc["models"][role].items() if k in ("role",)}
            out.update(repo_id=spec["repo_id"], revision=spec["revision"], dtype=spec["dtype"], files=spec["files"])
            for key in ("total_bytes", "stored_dtype", "hub_files"):
                if spec.get(key) is not None:
                    out[key] = spec[key]
            if role == "unaligned":
                out["gated"] = spec["gated"]
            out["role"] = (f"{self.family}: the " + ("aligned model, the untuned model of every arm (RK KIT "
                                                     "instruct_model)" if role == "aligned" else
                                                     "unaligned base model (RK KIT base_model; DES F2)"))
            out["source"] = "a local snapshot folder at the pinned commit; nothing is downloaded by safe_lora.py"
            for key, kind in (("revision", "commit"), ("dtype", "dtype"), ("files", "files")):
                if out[key] is None:
                    hub_null.append({"path": f"models.{role}.{key}", "kind": kind})
            doc["models"][role] = out
        if hub_null:
            waits["HUB_READ"] = {"pin": "HUB_READ", "event": EVENTS["HUB_READ"],
                                 "where": [f"families.{self.family}.models"], "roles": ["safe_lora"],
                                 "fields": {"safe_lora": hub_null}}
        doc["recipe"] = {"path": self.main_rel, "sha256": sha256_file(REPO / self.main_rel)}
        doc["sources"] = {"P2": {"path": "research/experiments/2026-11-06-78b-preregistration-part2.md",
                                 "sections": "3.1, 3.2, 16.1"},
                          "DES": {"path": ".ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part2-design-20261106.md",
                                  "sections": "F1, F2"},
                          "GXB": {"path": ".ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-ab-build-20261108.md",
                                  "sections": "O2, O3, X3"},
                          "REF_1B": {"path": BASE["safe_lora"][0], "sha256": BASE["safe_lora"][1]}}
        doc["requirement"] = REQUIREMENT["safe_lora"].format(seed=seed)
        return doc

    def derive(self, seed: int) -> tuple[dict[str, bytes], dict]:
        """The seed's two settings files and its index document."""
        waits: dict = {}
        sl_bytes = dumps(self.safe_lora(seed, waits))
        ea_bytes = dumps(self.eval_adapter(seed, sha256_bytes(sl_bytes), waits))
        files = {file_name("eval_adapter", self.family, seed): ea_bytes,
                 file_name("safe_lora", self.family, seed): sl_bytes}
        entries = {"eval_adapter": {"file": file_name("eval_adapter", self.family, seed), "sha256": sha256_bytes(ea_bytes)},
                   "safe_lora": {"file": file_name("safe_lora", self.family, seed), "sha256": sha256_bytes(sl_bytes)}}
        for role in OEXT_FILES:
            path, sha, _ = self.oext[role]
            entries[role] = {"file": path.name, "sha256": sha}
        index = {"kind": INDEX_KIND, "version": 1, "family": self.family, "seed": seed,
                 "manifest_sha256": self.pins["manifest_sha256"], "files": entries,
                 "waits": [waits[k] for k in sorted(waits)], "branch": self.branch,
                 "w1_18_record_sha256": self.record_sha256, "commands": ["eval_adapter", "safe_lora"],
                 "base": {role: {"path": rel, "sha256": sha} for role, (rel, sha) in BASE.items()}}
        return files, index


def derive_all(pins: dict, settings_dir: Path = SETTINGS_DIR) -> dict[str, bytes]:
    """Every derived file's bytes (name -> bytes): per family and seed of the reference set, the two settings files
    and the index (with the other families' manifests, for a refusal that names them)."""
    fams = {f: Family(f, pins["families"][f], pins["reference_set"], settings_dir) for f in FAMILIES}
    manifests = {f: fam.pins["manifest_sha256"] for f, fam in fams.items()}
    out: dict[str, bytes] = {}
    for family, fam in fams.items():
        for seed in fam.set["seeds"]:
            files, index = fam.derive(seed)
            index["other_manifests"] = {f: m for f, m in manifests.items() if f != family}
            out.update(files)
            out[index_name(family, seed)] = dumps(index)
    return out


def wrapper_module():
    """This checkout's refs_78b.py, loaded by its file path beside this file (never another root's copy)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("scale78b_refs_78b_of_the_maker", HERE / "refs_78b.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def oext_inputs() -> dict:
    """The O-ext inputs (bank and sealed record SHA-256) from Track O's pins file (one bank for both families)."""
    doc = s1.strict_json((SETTINGS_DIR / "oext_pins_78b.json").read_bytes())
    shared = doc["shared"]
    return {"oext_bank": shared["oext_bank_sha256"], "oext_record": shared["oext_record_sha256"]}


def form(family: str, seed: int, files: dict[str, bytes], code: dict[str, str], settings_dir: Path = SETTINGS_DIR,
         record_path: str | None = None) -> dict:
    """The kit pin's form for (family, seed), RK's {files: {path: SHA-256}, inputs: {oext_bank, oext_record}}: the
    wrapper and the 1B files its commands run (``code``), the index and every settings file it lists; with a pinned
    W1-18 record (Branch 128, or full with a record) also the record at its R-21 path (``record_path``)."""
    name = index_name(family, seed)
    index = s1.strict_json(files[name])
    out = dict(code)
    out[label(Path(settings_dir) / name)] = sha256_bytes(files[name])
    for entry in index["files"].values():
        out[label(Path(settings_dir) / entry["file"])] = entry["sha256"]
    if index["w1_18_record_sha256"] is not None:
        if record_path is None:
            raise s1.Refusal(f"{family}: the O-ext settings pin a W1-18 record; its R-21 path is needed for the form")
        out[record_path] = index["w1_18_record_sha256"]
    return {"files": dict(sorted(out.items())), "inputs": oext_inputs()}


def record_path_of(family: str) -> str | None:
    """The W1-18 record's R-21 path from Track O's pins (families.F.w1_18.record_path), or None."""
    doc = s1.strict_json((SETTINGS_DIR / "oext_pins_78b.json").read_bytes())
    return doc["families"][family]["w1_18"].get("record_path")


STALE = re.compile(r"^(REFS-78B__|eval_adapter__|safe_lora__)(olmo2-7b|llama31-8b)__[0-9]{4}\.json$")


def stale_files(settings_dir: Path, files: dict[str, bytes]) -> list[str]:
    """RV-5: this maker's per-seed files in the folder that the derivation does not make (a seed outside the set)."""
    if not Path(settings_dir).is_dir():
        return []
    return sorted(p.name for p in Path(settings_dir).iterdir() if STALE.match(p.name) and p.name not in files)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pins", type=Path, default=None, help="the pins file (default settings/refs_pins_78b.json)")
    ap.add_argument("--settings-dir", type=Path, default=None, help="where the files are written or checked, and "
                    "where Track O's files are read (default this folder's settings/; another folder for a dry run)")
    ap.add_argument("--check", action="store_true", help="derive in memory and compare with the files on disk")
    ap.add_argument("--refs-78b", nargs=2, metavar=("FAMILY", "SEED"), help="print the kit pin's form")
    args = ap.parse_args(argv)
    settings_dir = SETTINGS_DIR if args.settings_dir is None else args.settings_dir
    try:
        pins, _ = load_pins(PINS_PATH if args.pins is None else args.pins)
        files = derive_all(pins, settings_dir)
        if args.refs_78b:
            family, seed = args.refs_78b
            if family not in FAMILIES or not seed.isdigit() or index_name(family, int(seed)) not in files:
                raise s1.Refusal(f"no index for {family} seed {seed} in the reference set {pins['reference_set']}")
            print(json.dumps(form(family, int(seed), files, wrapper_module().code_pins(), settings_dir,
                                  record_path_of(family)), indent=2, sort_keys=True))
            return 0
    except (s1.Refusal, OSError, ValueError, KeyError) as exc:
        print(f"REFUSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    stale = stale_files(settings_dir, files)
    if args.check:
        bad = sorted(n for n, d in files.items() if not (settings_dir / n).is_file()
                     or (settings_dir / n).read_bytes() != d) + stale
        if bad:
            print(f"DIFFERS: {len(bad)} files differ from the derivation (first: {bad[0]})", file=sys.stderr)
            return 1
        print(f"checked {len(files)} files; " + "; ".join(
            f"{n} {sha256_bytes(files[n])}" for n in sorted(files) if n.startswith("REFS-78B")))
        return 0
    settings_dir.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (settings_dir / name).write_bytes(data)
    for name in stale:                       # RV-5: a seed outside the reference set keeps no file (the fallback)
        (settings_dir / name).unlink()
        print(f"removed  {name} (its seed is outside the reference set)")
    for name in sorted(files):
        print(f"{sha256_bytes(files[name])}  {name}")
    print("next: run the tests under scripts/scale78b/tests/refs; print the form (--refs-78b F S) for the kit's pin")
    return 0


if __name__ == "__main__":
    sys.exit(main())
