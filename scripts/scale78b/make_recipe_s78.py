"""Recipe S_78 for the 7-8B tier (readiness plan T6a; the lead's rulings 11 KD8 and 15; the engine's config module
only; outside the engine identity).

    python3 -I -B scripts/scale78b/make_recipe_s78.py --family olmo2-7b|llama31-8b --anchors-sha256 HEX --out PATH
                                                      [--date 20261105]

S_78 is the family's main config (OLMo-2-7B ``study-kt-olmo2-7b-r64-b-mb2-20261008`` 18cc31d7…; Llama-3.1-8B
``study-kt-llama31-8b-r64-b5e5-mb2-20261010`` 74758af1…) with exactly Gate B's recipe-S differences. That field set
is the 1B pair's difference (REC ``study-kt-olmo2-1b-r64-b-mb4-20261008`` 9e9bde6f… against S ``…-gateb-20261008``
ceffe0ef…; scripts/make_gateb_recipe.py:5-7): ``attribution.checkpoints`` becomes [q, e1], ``attribution.query_bank``
becomes ``anchors-HEX`` (the SHA-256 of the family's sealed anchor file's bytes, from that family's anchor job),
and ``name`` and ``purpose`` change. Every model, training, generation, guard and scoring key keeps the main config's
value, so S_78 has the main config's training identity (OLMo-2-7B 36738c38…, Llama-3.1-8B 5b4451e1…) and its
evaluation config. The file is written in the main config's own layout (its indent, its key order, a final newline)
and refused if PATH exists or PATH's stem is not the recipe's name. Prints the recipe's SHA-256, its training
identity and the main config's hashes only.

The anchor file is per family (P78 §11: "an anchor job per family"; the anchor job's safe set holds the family's own
untuned answers), so S_78 cannot be written before that family's anchor job has run: Gate B's own order (the anchor
job on the pod before recipe S; PRE revision 3). The 1B maker is pinned to the 1B recipe (KCR:140) and is not edited.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIGS = ROOT / "experiments/safety_selection/configs"

# ===== pins (the engine's config_sha256 and training_identity, computed with -I -B on 5 Nov 2026) =====
MAIN = {
    "olmo2-7b": {"file": "study-kt-olmo2-7b-r64-b-mb2-20261008.json",
                 "config_sha256": "18cc31d7117a2de7bc02382fe8a4d409fc43c91b434bf219a4808dfb26528d09",
                 "training_identity": "36738c3823fae7eaca625cc9f619e98c7e40b9bb64e5d0e234412827d3371ec6",
                 "model": "OLMo-2-7B"},
    "llama31-8b": {"file": "study-kt-llama31-8b-r64-b5e5-mb2-20261010.json",
                   "config_sha256": "74758af1791d9f7a8ce616adce7549b5b7b0619e55310158d7e21197ed129893",
                   "training_identity": "5b4451e1487fb2200a5b2b151de2e68397117099a429654484146b3cc3791287",
                   "model": "Llama-3.1-8B"},
}
# The 1B pair that defines the recipe-S field set (read, not edited).
REC_1B = CONFIGS / "study-kt-olmo2-1b-r64-b-mb4-20261008.json"
S_1B = CONFIGS / "study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json"
REC_1B_SHA256 = "9e9bde6f2f32876098410479883deff5ef3141e471a79ed231c7a5db15ad399b"
S_1B_SHA256 = "ceffe0efb5d75bacfbd62743f530259deeedeca8950605d1bd3ff66e5391fe46"
RECIPE_S_FIELDS = frozenset({"name", "purpose", "attribution.checkpoints", "attribution.query_bank"})
RECIPE_S_CHECKPOINTS = ["q", "e1"]
DEFAULT_DATE = "20261105"
INPUTS = ROOT / ".ai/inputs"
ANCHOR_RECORD_KIND = "gate-c anchor bank record"              # anchors.sealed.json (Gate B's 1B record; the 7-8B ones to come)
# ===== end of the pins =====


def refuse(message: str):
    raise SystemExit(message)


def diff_paths(a, b, prefix: str = "") -> set:
    """The dotted paths of every leaf (or list) at which two JSON documents differ."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = set()
        for key in set(a) | set(b):
            path = f"{prefix}.{key}" if prefix else key
            if key not in a or key not in b:
                out.add(path)
            else:
                out |= diff_paths(a[key], b[key], path)
        return out
    return set() if a == b else {prefix}


def s78_name(main_name: str, date: str) -> str:
    """The main config's name with its date replaced by gateb-<date> (study-kt-olmo2-7b-r64-b-mb2-gateb-20261105)."""
    if not re.fullmatch(r"\d{8}", date or ""):
        refuse("--date must be eight digits (YYYYMMDD)")
    if not re.search(r"-\d{8}$", main_name):
        refuse("the main config's name does not end in a date")
    return re.sub(r"-\d{8}$", f"-gateb-{date}", main_name)


def purpose_text(family: str, main: dict, anchors_sha256: str) -> str:
    pin = MAIN[family]
    return (f"Recipe S_78 for {pin['model']} (the 7-8B tier, readiness plan T6a; the lead's Part 1 rulings of 5 Nov 2026, "
            f"KD8): {main['name']} (config_sha256 {pin['config_sha256'][:8]}) unchanged except attribution.checkpoints "
            f"[q, e1] and attribution.query_bank anchors-<the SHA-256 of this family's sealed anchor file> "
            f"({anchors_sha256[:8]}); same training identity ({pin['training_identity'][:8]}) and evaluation config as "
            f"the main config. The field set is Gate B's recipe-S difference (study-kt-olmo2-1b-r64-b-mb4-20261008 "
            f"against its -gateb-20261008 sibling; scripts/make_gateb_recipe.py).")


def make(main: dict, family: str, anchors_sha256: str, date: str = DEFAULT_DATE) -> dict:
    if family not in MAIN:
        refuse(f"--family must be one of {sorted(MAIN)}")
    if not re.fullmatch(r"[0-9a-f]{64}", anchors_sha256 or ""):
        refuse("--anchors-sha256 must be 64 lowercase hex characters")
    out = json.loads(json.dumps(main))                        # a deep copy that keeps the key order
    out["name"] = s78_name(main["name"], date)
    out["purpose"] = purpose_text(family, main, anchors_sha256)
    out["attribution"]["checkpoints"] = list(RECIPE_S_CHECKPOINTS)
    out["attribution"]["query_bank"] = f"anchors-{anchors_sha256}"
    if diff_paths(main, out) != set(RECIPE_S_FIELDS):
        refuse("S_78 differs from the main config outside the recipe-S field set")
    return out


def indent_of(text: str) -> int:
    """The main config's own indent: the leading spaces of its first indented line."""
    for line in text.splitlines()[1:]:
        stripped = line.lstrip(" ")
        if stripped and stripped != line:
            return len(line) - len(stripped)
    refuse("the main config has no indented line")


def anchor_records(inputs_root=INPUTS) -> list:
    """Every committed anchor record under .ai/inputs/ (anchors.sealed.json, kind "gate-c anchor bank record", complete):
    its path, ``anchor_file_sha256`` (the value S_78's query_bank names) and ``provenance.recipe_sha256`` (the config of
    the policy whose own Safe answers the anchor file holds: the record's family link). Keys and hashes only."""
    out = []
    for path in sorted(pathlib.Path(inputs_root).rglob("anchors.sealed.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or doc.get("kind") != ANCHOR_RECORD_KIND or doc.get("complete") is not True:
            continue
        out.append({"path": str(path), "anchor_file_sha256": doc.get("anchor_file_sha256"),
                    "recipe_sha256": (doc.get("provenance") or {}).get("recipe_sha256")})
    return out


def anchored_to(config: dict, family: str, records: list):
    """The committed anchor record an S_78 config's query_bank names, when that record is THIS family's (its provenance
    recipe is the family's main config, MAIN[family]["config_sha256"]); None for a placeholder hash, a borrowed record
    (another model's anchor file, such as Gate B's 1B one) or an unknown value. Route (A), addendum A1: an S_78 config
    may sit in configs/ only once its family's anchor job has written such a record."""
    bank = (config.get("attribution") or {}).get("query_bank")
    if not (isinstance(bank, str) and bank.startswith("anchors-")) or family not in MAIN:
        return None
    digest = bank[len("anchors-"):]
    for record in records:
        if record["anchor_file_sha256"] == digest and record["recipe_sha256"] == MAIN[family]["config_sha256"]:
            return record
    return None


def load_main(family: str, config_sha256, validate_recipe) -> tuple[dict, str]:
    pin = MAIN[family]
    path = CONFIGS / pin["file"]
    text = path.read_text(encoding="utf-8")
    main = validate_recipe(json.loads(text))
    if config_sha256(main) != pin["config_sha256"]:
        refuse(f"{pin['file']}: its recipe hash is not {pin['config_sha256'][:8]}…: the main config changed")
    return main, text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--family", required=True, choices=sorted(MAIN))
    ap.add_argument("--anchors-sha256", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--date", default=DEFAULT_DATE, help="the date in the recipe's name (default 20261105)")
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        refuse(f"{out.name} exists: S_78 is written once")
    sys.path.insert(0, str(ROOT))
    from experiments.safety_selection.config import config_sha256, training_identity, validate_recipe

    main_recipe, text = load_main(args.family, config_sha256, validate_recipe)
    recipe = validate_recipe(make(main_recipe, args.family, args.anchors_sha256, args.date))
    if out.stem != recipe["name"]:
        refuse(f"--out's stem must be the recipe's name {recipe['name']}")
    pin = MAIN[args.family]
    if training_identity(recipe) != training_identity(main_recipe) or training_identity(recipe) != pin["training_identity"]:
        refuse("S_78's training identity differs from the main config's")
    out.write_text(json.dumps(recipe, indent=indent_of(text), ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"family": args.family, "name": recipe["name"], "recipe_sha256": config_sha256(recipe),
                      "training_identity": training_identity(recipe), "main_sha256": config_sha256(main_recipe),
                      "main_training_identity": training_identity(main_recipe)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
