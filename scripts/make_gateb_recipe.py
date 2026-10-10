"""Recipe S for Gate B (brief gate-b-engine-kit-reading-20261008, A8; stdlib only; outside the engine identity).

    python3 scripts/make_gateb_recipe.py --anchors-sha256 HEX --out PATH

S is REC (the OLMo-2-1B recipe B, mb4) with exactly four changes: ``attribution.checkpoints`` becomes [q, e1],
``attribution.query_bank`` becomes ``anchors-HEX`` (the SHA-256 of the sealed anchor file's bytes), and ``name`` and
``purpose`` change. Every training, model, generation, guard and scoring key keeps REC's value, so S has REC's
training identity and evaluation config. The file is written in REC's own layout (2-space indent, REC's key order,
a final newline) and refused if PATH exists. Prints the recipe's SHA-256 and training identity only.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = ROOT / "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json"
REC_SHA256 = "9e9bde6f"                       # REC's recipe hash (brief Facts), checked as a prefix
NAME = "study-kt-olmo2-1b-r64-b-mb4-gateb-20261008"
PURPOSE = ("Gate B recipe S (brief gate-b-engine-kit-reading-20261008, A8): REC (study-kt-olmo2-1b-r64-b-mb4-20261008) "
           "unchanged except attribution.checkpoints [q, e1] and attribution.query_bank anchors-<the sealed anchor "
           "file's SHA-256>; same training identity and evaluation config as REC.")


def make(rec: dict, anchors_sha256: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{64}", anchors_sha256 or ""):
        raise SystemExit("--anchors-sha256 must be 64 lowercase hex characters")
    out = json.loads(json.dumps(rec))                         # a deep copy that keeps the key order
    out["name"], out["purpose"] = NAME, PURPOSE
    out["attribution"]["checkpoints"] = ["q", "e1"]
    out["attribution"]["query_bank"] = f"anchors-{anchors_sha256}"
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--anchors-sha256", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise SystemExit(f"{out.name} exists: S is written once")
    sys.path.insert(0, str(ROOT))
    from experiments.safety_selection.config import config_sha256, training_identity, validate_recipe

    rec = json.loads(REC.read_text(encoding="utf-8"))
    if not config_sha256(rec).startswith(REC_SHA256):
        raise SystemExit("REC's recipe hash is not 9e9bde6f…: the base recipe changed")
    recipe = validate_recipe(make(rec, args.anchors_sha256))
    if training_identity(recipe) != training_identity(validate_recipe(rec)):
        raise SystemExit("S's training identity differs from REC's")
    out.write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"recipe_sha256": config_sha256(recipe), "training_identity": training_identity(recipe),
                      "rec_sha256": config_sha256(rec)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
