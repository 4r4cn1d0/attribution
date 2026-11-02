"""Command line of the stage-1b pilot reader (package doc). Exit 0: the file written; 2: refused, nothing written.

    python -m scripts.stage1_s1.pilot_gate --mode pilot|re-pilot --kit DIR --out FILE [--block P] [--repo DIR]
        [--rules FILE]

``--kit`` is the kit folder (plan.json and retrieved/); ``--block`` the block whose done hosts hold the pilot-arm
units (P; the re-pilot names its own block); ``--repo`` the folder that REJUDGED_PINS paths and the frozen coherence
bars file are relative to (default: this repository); ``--rules`` the kit's rules module (default:
runkit/stage1-olmo/stage1_rules.py of this repository). Printed: the output file and its SHA-256, then Lambda_plant,
SE, df, t(0.90, df), the lower bound and the label; a refusal prints one fixed line on stderr. Any other error prints
its type only (its message may hold a value or a name).
"""

from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

import numpy as np

from scripts.stage1_s1.reading.settings import SETTINGS_SHA256, Refusal, canonical_json, sha256_bytes
from scripts.stage1_s1.pilot_gate import gate
from scripts.stage1_s1.pilot_gate.units import read_units

KIND = "stage1b pilot gate reading"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RULES = REPO / "runkit" / "stage1-olmo" / "stage1_rules.py"
DEFAULT_BLOCK = "P"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m scripts.stage1_s1.pilot_gate",
                                description="the stage-1b pilot gate (REV4:675; addendum section 40 points 1-3)")
    p.add_argument("--mode", required=True, choices=gate.MODES, help="pilot (a0_plant) or re-pilot (a0_plant75)")
    p.add_argument("--kit", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--block", default=DEFAULT_BLOCK)
    p.add_argument("--repo", type=Path, default=REPO)
    p.add_argument("--rules", type=Path, default=RULES)
    return p


def document(kit: Path, repo: Path, rules: Path, mode: str, block: str) -> dict:
    """The whole output: B16's pins checked, the units read, the gate read, the provenance."""
    b16 = gate.check_b16()
    table, inputs = read_units(kit, repo, rules, mode, block)
    result = gate.read(table, mode)
    doc = {"kind": KIND, "version": 1, "block": block,
           **{k: v for k, v in result.items() if not k.startswith("_")},
           "rule": {"text": list(gate.RULE), "sources": list(gate.SOURCES)},
           "inputs": inputs,
           "provenance": {"modules": {p.name: sha256_bytes(p.read_bytes()) for p in sorted(HERE.glob("*.py"))},
                          "b16_modules": b16, "b16_settings_sha256": SETTINGS_SHA256,
                          "b16_pins_source": gate.B16_PINS_SOURCE,
                          "python": platform.python_version(), "numpy": np.__version__}}
    return gate.json_ready(doc)


def words(doc: dict) -> list[str]:
    e = doc["estimate"]
    return [f"Lambda_plant {e['est']:.4f} pp; SE {e['se']:.4f} pp; df {e['df']:.3f}; t(0.90, df) {doc['t_quantile']:.4f}; "
            f"one-sided 90% lower bound {doc['lower_bound_pp']:.4f} pp",
            f"label: {doc['label']} (mode {doc['mode']}; {doc['arm']} against {doc['comparator']}, seeds "
            f"{', '.join(str(j) for j in doc['seeds'])})"]


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.out.exists():
            raise Refusal("the output file exists; the reader never overwrites")
        doc = document(args.kit, args.repo, args.rules, args.mode, args.block)
        data = canonical_json(doc)
        try:
            with open(args.out, "xb") as handle:                 # an exclusive create, not a check-then-write
                handle.write(data)
        except FileExistsError:
            raise Refusal("the output file exists; the reader never overwrites") from None
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - any other error may carry a value in its text: print its type only
        print(f"REFUSED: an unexpected {type(exc).__name__} (its message is withheld: it may hold a value)",
              file=sys.stderr)
        return 2
    print(f"wrote {args.out} sha256 {sha256_bytes(data)}")
    for line in words(doc):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
