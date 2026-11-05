"""The per-family scorer settings for the 7-8B tier (track E of the 7-8B $0 build round, 5 Nov 2026; Part 1 sections
3.7, 10, 12 and 14; the lead's addendum A1, A2, A13; the readiness plan T6; the check's C1, C6, M1, M2).

    python -I -B scripts/scale78b/make_scorer_settings_78b.py            # write settings/<script>__<family>.json and PINS-78B.json
    python -I -B scripts/scale78b/make_scorer_settings_78b.py --check    # regenerate in memory and compare with the committed files

The 1B scorer scripts under scripts/stage1/ are model-agnostic in code but their settings files pin OLMo-2-1B's recipe,
manifest, model, anchor bank and the 1B S4 keep count. This maker derives, for each family (OLMo-2-7B, Llama-3.1-8B)
and each 1B settings file below, a settings file in the 1B file's own schema (same ``kind``, ``name``, ``engine_x``,
``label_entries``; so the unchanged 1B code's ``check_settings`` accepts it), with every per-family value taken from
``settings/pins_78b.json`` and every pin that cannot be known yet set to null and listed in the file's ``family_78b.waits``
with the event that fills it. The 1B files are read, hashed against the pins below, and never written. The wrapper
``scripts/scale78b/scorers_78b.py`` runs the 1B scripts with these files; it refuses while a pin its command needs is
null.

Derived files (per family F = olmo2-7b | llama31-8b):
  make_untuned_answers__F.json   REC = the family's main recipe; recipe S = the main recipe too (pins_78b shared.untuned_recipe_s
                                 'main'; S_78 shares its model section) or S_78; lists.s4.keep = 192 with the nested doses block
  representation_pass__F.json    recipe = S_78 (null), anchor bank (null), the family's model and manifest
  representation_pools__F.json   the W1 pool-pins file's shape with both pools null (no plant or decoy pool at 7-8B)
  score_l1_larf__F.json          REC = main; anchor bank (null); manifest; REQ-3's settings = representation_pass__F's SHA-256;
                                 scan.first_block = null (Part 2's layer rule)
  score_classifier__F.json       recipe = S_78 (null); anchor bank (null); model; manifest
  score_s3_datarx__F.json        REQ-3's settings = representation_pass__F's SHA-256
  write_score_edit__F.json       the A1 attributes unit's pins null (the pass on the family's a0-1101 retrain); manifest
  write_add_edit__F.json         manifest; recipe (main or S_78); lists s1, s3, s4 (48), s4_96 (96), s4_192 (192), s4_top (null)
  build_s_pool__F.json           REC and manifest per family (only if Part 2 rebuilds the S-pool per family)
Plus PINS-78B.json: every derived file's SHA-256 and the pins file's, which scorers_78b.py pins by one literal.

Nothing here reads a model, a prepared set, an answer, a prompt or any text file. Standard library plus
scripts/stage1/s1common (the registry digests).
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_DIR = HERE / "settings"
PINS_PATH = SETTINGS_DIR / "pins_78b.json"
INDEX_NAME = "PINS-78B.json"
STAGE1_SETTINGS = REPO / "scripts" / "stage1" / "settings"
FAMILIES = ("olmo2-7b", "llama31-8b")
# The 1B settings files this maker derives from, by SHA-256 (M: shasum -a 256 at HEAD 953f520, 5 Nov 2026). A changed
# 1B file refuses: the 1B settings are frozen stage-1 commitments (Part 1 section 11, "what stays frozen").
BASE_SHA256 = {
    "make_untuned_answers": "4bf2cc1a2493bc154d314105a085f0166933d1147a37e29fd42c7348ba9d9d8c",
    "representation_pass": "a555fd899bd2b5caf8d68fb62578ed2e943977341b5bf2dc2d688dcbd034600b",
    "representation_pools": "1451ba5ec435ecaafebd7749f44b6729e45f2157a69a62c55f35e2bbdbae826b",
    "score_l1_larf": "0d875213831d30456ffc02254cca839d78ae48da8d7ba35d037561b9d59a75cd",
    "score_classifier": "5807ec750c74137f3e5c466231de9e73a0cbb5fe5411f7be29a40bbed4c8e58a",
    "score_s3_datarx": "6382dcc663e80ecab332ecf96b7cba621e3e535408481e6ab83ca614bc2b502f",
    "write_score_edit": "9fc5f359133e76fd464b13ed34eb13eb74bf25d71edeb0add0c8d8eae992f9b5",
    "write_add_edit": "7cf7dd778e4852305d5ed902dfe75b7eece7bc07ffdc353bcf83cc3a7fd8f167",
    "build_s_pool": "6080487c8efa6682259ecd977f517a151a8e8aecf80d7aea45e6a23911a943a4",
}
ORDER = ("make_untuned_answers", "representation_pass", "representation_pools", "score_l1_larf", "score_classifier",
         "score_s3_datarx", "write_score_edit", "write_add_edit", "build_s_pool")
OWNER_78B = "scripts/scale78b/scorers_78b.py"
DOSE_NAMES = {48: "s4", 96: "s4_96", 192: "s4_192"}
TOP_DOSE = "s4_top"


class MakerError(Exception):
    """A refusal; the message holds names, counts and hashes only."""


def file_name(script: str, family: str) -> str:
    return f"{script}__{family}.json"


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def dumps(doc: dict) -> bytes:
    return (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def load_pins(path: Path = PINS_PATH) -> tuple[dict, str]:
    data = path.read_bytes()
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != "scale78b scorer pins" or doc.get("version") != 1:
        raise MakerError("pins_78b.json is not a version-1 scale78b scorer pins file")
    if set(doc["families"]) != set(FAMILIES):
        raise MakerError(f"pins_78b.json names the families {sorted(doc['families'])}, expected {sorted(FAMILIES)}")
    for family, pins in doc["families"].items():
        for key in ("manifest_sha256", "main_recipe", "model_pin", "recipe_s78", "anchor_bank_sha256", "a1_attributes_unit"):
            if key not in pins:
                raise MakerError(f"pins_78b.json family {family} lacks {key}")
        for name, value in (("manifest_sha256", pins["manifest_sha256"]), ("main_recipe.config_sha256", pins["main_recipe"]["config_sha256"])):
            if not isinstance(value, str) or not s1.HEX64.match(value):
                raise MakerError(f"pins_78b.json family {family}: {name} is not a SHA-256")
        for name, value in (("recipe_s78.config_sha256", pins["recipe_s78"]["config_sha256"]),
                            ("anchor_bank_sha256", pins["anchor_bank_sha256"]),
                            ("a1_attributes_unit.complete_sha256", pins["a1_attributes_unit"]["complete_sha256"]),
                            ("a1_attributes_unit.retrain_complete_sha256", pins["a1_attributes_unit"]["retrain_complete_sha256"])):
            if not (value is None or (isinstance(value, str) and s1.HEX64.match(value))):
                raise MakerError(f"pins_78b.json family {family}: {name} is neither null nor a SHA-256")
    shared = doc["shared"]
    if shared.get("untuned_recipe_s") not in ("main", "s78"):
        raise MakerError("pins_78b.json shared.untuned_recipe_s must be 'main' or 's78'")
    if shared.get("s4_keep") != max(shared.get("s4_doses", [])) or sorted(shared["s4_doses"]) != shared["s4_doses"] \
            or shared["s4_doses"][0] != 48 or set(shared["s4_doses"]) != set(DOSE_NAMES):
        raise MakerError("pins_78b.json shared.s4_doses must be the nested sizes [48, 96, 192] and s4_keep their maximum")
    return doc, sha256_bytes(data)


def load_base(script: str) -> tuple[dict, str]:
    path = STAGE1_SETTINGS / f"{script}.json"
    data = path.read_bytes()
    digest = sha256_bytes(data)
    if digest != BASE_SHA256[script]:
        raise MakerError(f"scripts/stage1/settings/{script}.json hashes to {digest}, the maker pins {BASE_SHA256[script]}")
    return s1.strict_json(data), digest


def set_path(doc: dict, dotted: str, value) -> None:
    node = doc
    *parents, last = dotted.split(".")
    for key in parents:
        node = node[key]
    node[last] = value


def get_path(doc: dict, dotted: str):
    node = doc
    for key in dotted.split("."):
        node = node[key]
    return node


class Derivation:
    """One derived settings document: the 1B document plus the family block, with every null pin recorded."""

    def __init__(self, script: str, family: str, pins: dict):
        self.script, self.family = script, family
        self.base, self.base_sha256 = load_base(script)
        self.doc = copy.deepcopy(self.base)
        self.fam = pins["families"][family]
        self.shared = pins["shared"]
        self.waits: dict[str, dict] = {}

    def null(self, dotted: str, event: str, needed_by: list[str]) -> None:
        set_path(self.doc, dotted, None)
        self.waits[dotted] = {"event": event, "needed_by": list(needed_by)}

    def pin_or_null(self, dotted: str, value, event: str, needed_by: list[str]) -> None:
        if value is None:
            self.null(dotted, event, needed_by)
        else:
            set_path(self.doc, dotted, value)

    def finish(self) -> dict:
        doc = self.doc
        registry = s1.registry()
        for key, digest in doc.get("label_entries", {}).items():
            if key not in registry or registry[key].digest != digest:
                raise MakerError(f"{self.script}: the 1B file's registry entry {key} is missing or changed")
        doc["labels_sha256"] = s1.labels_sha256()
        doc["family_78b"] = {
            "family": self.family, "model": self.fam["model"],
            "manifest_sha256": self.fam["manifest_sha256"],
            "main_recipe": dict(self.fam["main_recipe"]),
            "derived_from": {"path": f"scripts/stage1/settings/{self.script}.json", "sha256": self.base_sha256},
            "maker": "scripts/scale78b/make_scorer_settings_78b.py", "owner_78b": OWNER_78B,
            "pins_file": "scripts/scale78b/settings/pins_78b.json",
            "engine_rule": self.shared["engine_rule_78b"],
            "waits": dict(sorted(self.waits.items())),
            "rule": "the 1B file's schema and name, so scripts/stage1's unchanged check_settings accepts it; every value "
                    "that differs from the 1B file is per family (pins_78b.json) or a documented 7-8B rule; a null is a pin "
                    "that waits for the event named in waits; scorers_78b.py refuses a command while a pin it needs is null",
        }
        return doc


def recipe_s_pin(d: Derivation) -> tuple[str | None, str, str]:
    """(value, event, basis) for a settings field that at 1B pins recipe S."""
    if d.shared["untuned_recipe_s"] == "main":
        return d.fam["main_recipe"]["config_sha256"], "", d.shared["untuned_recipe_s_basis"]
    return d.fam["recipe_s78"]["config_sha256"], d.fam["recipe_s78"]["waits"], d.shared["untuned_recipe_s_basis"]


def derive_untuned(d: Derivation) -> dict:
    doc, fam, shared = d.doc, d.fam, d.shared
    doc["pins"]["rec_recipe_sha256"] = fam["main_recipe"]["config_sha256"]
    value, event, basis = recipe_s_pin(d)
    d.pin_or_null("pins.recipe_s_sha256", value, event, ["*"])
    doc["pins"]["rule"] = (doc["pins"]["rule"] + f". 7-8B ({fam['model']}): REC = the family's main recipe "
                           f"({fam['main_recipe']['path']}); --recipe-s = " +
                           ("the same main recipe (pins_78b shared.untuned_recipe_s = main): " + basis
                            if shared["untuned_recipe_s"] == "main" else "recipe S_78 (null until it is written)"))
    keep, doses = shared["s4_keep"], shared["s4_doses"]
    rate = shared["s4_keep_rate_1b"]
    need = math.ceil(keep * rate["answered"] / rate["kept"])
    nth = ordinal(keep)
    s4 = doc["lists"]["s4"]
    s4["keep"] = keep
    s4["keep_rule"] = (f"L14 (2) unchanged except the count: kept only if it ended, its lexicon class is REFUSAL-OPENING, "
                       f"answer.strip() is non-empty and encode_train(prompt, answer, S.max_train_tokens) accepts; the first "
                       f"failing check is the drop reason; the first {keep} kept in list order form the top dose S4_{keep} "
                       f"(Part 1 section 10, ruling 12: the stop rule moves from the chunk that holds the 48th to the chunk that "
                       f"holds the {nth}; the first 48 are unchanged); the 1B code labels a keep after the {nth} "
                       f"'kept_after_the_48th' (a fixed string in scripts/stage1/make_untuned_answers.py:171; read it as "
                       f"'after the {nth}'); fewer than {keep} after 512 prompts: the 1B code writes the answers and the "
                       f"record only and exits 3, and the wrapper's doses block applies the pre-set fallback")
    doc["doses"] = {
        "sizes": doses, "names": {str(n): DOSE_NAMES[n] for n in doses},
        "files": {str(n): f"dose_{DOSE_NAMES[n]}.json" for n in doses},
        "top_dose_name": TOP_DOSE, "top_dose_file": f"dose_{TOP_DOSE}.json", "folder": "doses",
        "record": "s4_doses_record.json",
        "rule": shared["s4_keep_basis"] + "; the wrapper (scorers_78b.py untuned_answers) derives the three lists from the "
                "pass's answers_s4.json and the kept flags of untuned_answers_record.json, in list order, as stage-1 prompt "
                "lists named s4, s4_96 and s4_192 (write_add_edit__<family>.json takes each by name), and records their "
                "SHA-256s, row counts and the nesting check in s4_doses_record.json (text-free)",
        "fallback": f"DOSE pre_set_fallbacks[0] (Part 1 section 10): fewer than {keep} kept after the whole 512-prompt list: "
                    f"the top dose is all kept rows, written as the list {TOP_DOSE} (dose_{TOP_DOSE}.json) with its count "
                    f"in the record; the smaller doses that are filled are written; fewer than 48 kept: counts only, exit 3",
        "sizing": {"keep_rate_1b": {"kept": rate["kept"], "answered": rate["answered"], "rate": rate["kept"] / rate["answered"]},
                   "rule": "candidates needed = ceil(target x answered_1b / kept_1b); chunks = ceil(candidates / chunk)",
                   "candidates_for_top_dose_at_1b_rate": need, "chunks_for_top_dose_at_1b_rate": math.ceil(need / doc["chunk"]),
                   "list_size": s4["size"], "list_margin": s4["size"] / need, "source": rate["source"]},
        "w1_06_note": "the loss table's s4 entry (W1-06) covers every kept row of the pass (the top dose), not 48; in the "
                      "fallback case the 1B code omits it (exit 3)",
        "calls_78b": shared["untuned_calls_78b"],
    }
    doc["requirement"] += "; 7-8B: Part 1 sections 10 and 12 (the untuned_answers kind; the S4 add-dose arm), CHECK C6, M1, M2"
    return d.finish()


def derive_rep_pass(d: Derivation) -> dict:
    doc, fam = d.doc, d.fam
    d.pin_or_null("pins.recipe_sha256", fam["recipe_s78"]["config_sha256"], fam["recipe_s78"]["waits"], ["*"])
    doc["pins"]["model"] = dict(fam["model_pin"])
    d.pin_or_null("pins.anchor_bank_sha256", fam["anchor_bank_sha256"], fam["anchor_bank_waits"], ["*"])
    doc["pins"]["prepared_manifest_sha256"] = fam["manifest_sha256"]
    doc["pool_pins_file_78b"] = f"scripts/scale78b/settings/{file_name('representation_pools', d.family)}"
    doc["requirement"] += "; 7-8B: Part 1 section 12 (the rep_pass kind, REQ-3's pass for L1 and S3), section 14 item 1"
    return d.finish()


def derive_pools(d: Derivation) -> dict:
    doc = d.doc
    for name in doc["pools"]:
        doc["pools"][name]["sha256"] = None
    doc["fill"] = ("7-8B: no plant or decoy pool is passed (no selector runs at 7-8B, Part 1 section 11 EM-4), so both "
                   "pins stay null and any pool named plant or decoy refuses; the S3 pools (s3_safe, s3_orig) are named on "
                   "the command line by SHA-256 through their own records; scorers_78b.py gives this file to "
                   "representation_pass.py and score_classifier.py as the pool pins for the family")
    return d.finish()


def derive_l1(d: Derivation, rep_pass_sha256: str) -> dict:
    doc, fam, shared = d.doc, d.fam, d.shared
    d.pin_or_null("pins.anchor_bank_sha256", fam["anchor_bank_sha256"], fam["anchor_bank_waits"], ["scan"])
    doc["pins"]["prepared_manifest_sha256"] = fam["manifest_sha256"]
    doc["pins"]["rec_recipe_sha256"] = fam["main_recipe"]["config_sha256"]
    doc["pins"]["representation_pass_settings_sha256"] = rep_pass_sha256
    d.pin_or_null("scan.first_block", shared["l1_first_block"], shared["l1_first_block_waits"], ["scan"])
    doc["scan"]["first_block_rule_78b"] = shared["l1_first_block_waits"]
    doc["scan"]["modules_note_78b"] = shared["l1_modules_note"]
    doc["requirement"] += "; 7-8B: Part 1 section 12 (the l1_scan kind), section 14 item 1 (L1's layer rule, Part 2)"
    return d.finish()


def derive_classifier(d: Derivation) -> dict:
    doc, fam = d.doc, d.fam
    d.pin_or_null("pins.anchor_bank_sha256", fam["anchor_bank_sha256"], fam["anchor_bank_waits"], ["*"])
    doc["pins"]["model"] = dict(fam["model_pin"])
    doc["pins"]["prepared_manifest_sha256"] = fam["manifest_sha256"]
    d.pin_or_null("pins.recipe_sha256", fam["recipe_s78"]["config_sha256"], fam["recipe_s78"]["waits"], ["*"])
    doc["pools_rule"] += "; 7-8B: no pool is passed (no plant or decoy pool at 7-8B; both pins null in the family's pool pins file)"
    doc["requirement"] += "; 7-8B: Part 1 section 12 (the classifier kind)"
    return d.finish()


def derive_s3(d: Derivation, rep_pass_sha256: str) -> dict:
    d.doc["pins"]["representation_pass_settings_sha256"] = rep_pass_sha256
    d.doc["requirement"] += "; 7-8B: Part 1 section 14 item 1 (S3 from the family's own untuned answers; CHECK C6); Mac, $0"
    return d.finish()


def derive_score_edit(d: Derivation) -> dict:
    doc, fam, shared = d.doc, d.fam, d.shared
    unit = doc["a1"]["attributes_unit"]
    a1 = fam["a1_attributes_unit"]
    d.pin_or_null("a1.attributes_unit.complete_sha256", a1["complete_sha256"], a1["waits"], ["a1"])
    d.pin_or_null("a1.attributes_unit.retrain_complete_sha256", a1["retrain_complete_sha256"], a1["waits"], ["a1"])
    d.pin_or_null("a1.attributes_unit.recipe_sha256", fam["recipe_s78"]["config_sha256"], fam["recipe_s78"]["waits"], ["a1"])
    bank = fam["anchor_bank_sha256"]
    d.pin_or_null("a1.attributes_unit.query_bank", None if bank is None else f"anchors-{bank}", fam["anchor_bank_waits"], ["a1"])
    d.pin_or_null("a1.attributes_unit.query_bank_sha256", bank, fam["anchor_bank_waits"], ["a1"])
    d.null("a1.attributes_unit.code_sha256",
           "the engine that trains the family's a0-1101 states and runs A1's pass on them: X (" + shared["engine_x"][:8] +
           "...) or Y after the family's certificate (Part 1 section 3.7, EM-1; EYD:81); the lead fills it from the pass's "
           "COMPLETE.json by a recorded step", ["a1"])
    unit["seed"] = a1["seed"]
    unit["source"] = (f"7-8B {fam['model']}: A1's attributes pass (the engine's attributes job, kind attributes, split dev, "
                      f"checkpoints q and e1) on the family's a0-1101 retrain under recipe S_78 with the family's anchor "
                      f"file (Part 1 section 3.7, section 14 items 1-2); its COMPLETE.json and the retrain's, pinned here "
                      f"by the lead after the pass; the 1B value was Gate B's wave-0b unit")
    doc["a1"]["edit_name"] = doc["a1"]["edit_name"].replace("a0-1101's q and e1", f"{fam['model']} a0-1101's q and e1 (S_78 retrain)")
    doc["prepared"]["manifest_sha256"] = fam["manifest_sha256"]
    doc["prepared"]["path_on_the_mac"] = fam["prepared_path_on_the_mac"]
    doc["requirement_78b"] = "Part 1 sections 3.7 and 14 (A1 per family; L1's edit from the family's scan); Mac, $0"
    return d.finish()


def derive_add_edit(d: Derivation) -> dict:
    doc, fam, shared = d.doc, d.fam, d.shared
    doc["prepared_manifest_sha256"] = fam["manifest_sha256"]
    value, event, basis = recipe_s_pin(d)
    d.pin_or_null("recipe_sha256", value, event, ["*"])
    doc["recipe_use"] += ("; 7-8B: " + ("the family's main recipe stands in for recipe S (pins_78b shared.untuned_recipe_s = main): " + basis
                                        if shared["untuned_recipe_s"] == "main" else "recipe S_78"))
    doses = shared["s4_doses"]
    lists = doc["lists"]
    lists["s4"]["source"] = (f"the family's untuned-answers pass through scorers_78b.py: dose_s4.json (the first 48 kept rows; "
                             f"prompt, untuned answer), Part 1 section 10")
    for n in doses[1:]:
        lists[DOSE_NAMES[n]] = {"rows": n, "source": f"the same pass: dose_{DOSE_NAMES[n]}.json (the first {n} kept rows, nested; "
                                                      f"Part 1 section 10, the S4 add-dose arm)"}
    lists[TOP_DOSE] = {"rows": None, "source": f"only if the dose fallback fires (fewer than {max(doses)} kept after 512 prompts): "
                                                f"dose_{TOP_DOSE}.json, all kept rows; the lead fills rows from s4_doses_record.json"}
    d.waits[f"lists.{TOP_DOSE}.rows"] = {"event": "the dose fallback (Part 1 section 10): the kept count of the family's "
                                                  "untuned-answers pass, from s4_doses_record.json",
                                        "needed_by": []}      # the 1B writer refuses the list itself while this is null
    doc["requirement"] += "; 7-8B: Part 1 section 10 (S4, S4_96, S4_192 nested; the fallback top dose) and section 14 item 1 (S1 re-bound)"
    return d.finish()


def derive_s_pool(d: Derivation) -> dict:
    doc, fam = d.doc, d.fam
    doc["inputs"]["prepared_manifest_sha256"] = fam["manifest_sha256"]
    doc["inputs"]["rec_path"] = fam["main_recipe"]["path"]
    doc["inputs"]["rec_recipe_sha256"] = fam["main_recipe"]["config_sha256"]
    doc["expected_evaluation_forms_note_78b"] = ("the 1B count (11,954) is carried; it holds for the Llama manifest only if its "
                                                "banks hold the same prompts and ARC forms (I); L9 (2) stops the run otherwise, "
                                                "and the lead records the count by a step")
    doc["use_78b"] = ("only if Part 2 says the S-pool is rebuilt under the family's codec; the default (Part 1 section 14 item 1; "
                      "CHECK C6) re-uses the 1B sealed lists s1.json, s3_safe.pool.json and s4_candidates.json as the "
                      "untuned-answers pass's inputs")
    return d.finish()


def derive_all(pins: dict) -> dict[str, bytes]:
    """Every derived file's bytes, by file name (representation_pass first: two files embed its SHA-256)."""
    out: dict[str, bytes] = {}
    for family in FAMILIES:
        rep = dumps(derive_rep_pass(Derivation("representation_pass", family, pins)))
        out[file_name("representation_pass", family)] = rep
        rep_sha = sha256_bytes(rep)
        out[file_name("make_untuned_answers", family)] = dumps(derive_untuned(Derivation("make_untuned_answers", family, pins)))
        out[file_name("representation_pools", family)] = dumps(derive_pools(Derivation("representation_pools", family, pins)))
        out[file_name("score_l1_larf", family)] = dumps(derive_l1(Derivation("score_l1_larf", family, pins), rep_sha))
        out[file_name("score_classifier", family)] = dumps(derive_classifier(Derivation("score_classifier", family, pins)))
        out[file_name("score_s3_datarx", family)] = dumps(derive_s3(Derivation("score_s3_datarx", family, pins), rep_sha))
        out[file_name("write_score_edit", family)] = dumps(derive_score_edit(Derivation("write_score_edit", family, pins)))
        out[file_name("write_add_edit", family)] = dumps(derive_add_edit(Derivation("write_add_edit", family, pins)))
        out[file_name("build_s_pool", family)] = dumps(derive_s_pool(Derivation("build_s_pool", family, pins)))
    return dict(sorted(out.items()))


def index_bytes(files: dict[str, bytes], pins_sha256: str) -> bytes:
    doc = {"kind": "scale78b scorer settings index", "version": 1,
           "pins_78b_sha256": pins_sha256,
           "files": {name: sha256_bytes(data) for name, data in sorted(files.items())},
           "rule": "scorers_78b.py pins this file by its literal PINS_FILE_SHA256 and each settings file by the entry here; "
                   "the maker rewrites it with the settings files"}
    return dumps(doc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="regenerate in memory and compare with the committed files")
    parser.add_argument("--settings-dir", type=Path, default=SETTINGS_DIR)
    args = parser.parse_args(argv)
    try:
        pins, pins_sha = load_pins(args.settings_dir / "pins_78b.json")
        files = derive_all(pins)
        files[INDEX_NAME] = index_bytes(files, pins_sha)
    except (MakerError, s1.Refusal, OSError, KeyError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, (MakerError, s1.Refusal)) else type(exc).__name__} (nothing written)",
              file=sys.stderr)
        return 2
    differ = []
    for name, data in files.items():
        path = args.settings_dir / name
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                differ.append(name)
        else:
            path.write_bytes(data)
    for name, data in files.items():
        print(f"  {sha256_bytes(data)}  {name}")
    if args.check:
        print(f"check: {len(files) - len(differ)} of {len(files)} files equal their regeneration" +
              (f"; differ: {', '.join(differ)}" if differ else ""))
        return 1 if differ else 0
    print(f"wrote {len(files)} files into {args.settings_dir}; PINS_FILE_SHA256 = {sha256_bytes(files[INDEX_NAME])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
