"""What the reading-time readers share: a document read with the SHA-256 of its bytes, B16's output bound to its
pinned settings, its sealed contrasts and (when given) its input document, the provenance block, and the command-line
frame (exit 0: the file written; 2: refused, nothing written). Messages hold names, counts and hashes only; a reader
prints its output file, the file's SHA-256 and at most words, never a number.
"""

from __future__ import annotations

import argparse
import math
import platform
import sys
from pathlib import Path

import numpy as np

from scripts.stage1_s1.reading.reading import _strip
from scripts.stage1_s1.reading.settings import (READINGS, SETTINGS_SHA256, Refusal, canonical_json, design,
                                                 module_hashes, sha256_bytes, strict_json)
from scripts.stage1_s1.reading_input.sources import is_hex64

HERE = Path(__file__).resolve().parent
B16_KIND = "stage1 reading output"
RECORD_KIND = "stage1 reading input sources"          # scripts/stage1_s1/reading_input/build.RECORD_KIND


def read_document(path: Path, what: str) -> tuple:
    """(the strict-JSON document, the SHA-256 of its bytes); a missing file or a symbolic link refuses."""
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise Refusal(f"{what} ({path.name}): missing or not a regular file")
    data = path.read_bytes()
    return strict_json(data), sha256_bytes(data)


def number(value, what: str) -> float:
    """A finite JSON number (never a bool or a string)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise Refusal(f"{what} is not a finite number")
    return float(value)


def bound_reading(doc, input_sha256: str | None = None):
    """The sealed design of B16's version-1 output on the pinned settings, after the bindings: kind, version, a sealed
    reading, the settings pin, the sealed contrasts and, when ``input_sha256`` is given, the input document that
    B16's provenance names."""
    prov = doc.get("provenance") if isinstance(doc, dict) else None
    reading = doc.get("reading") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or doc.get("kind") != B16_KIND or doc.get("version") != 1 or \
            reading not in READINGS or not isinstance(prov, dict):
        raise Refusal("the reading file is not B16's version-1 output of a sealed reading")
    if prov.get("settings_sha256") != SETTINGS_SHA256:
        raise Refusal("B16's output names other reading settings than the pinned ones")
    if not is_hex64(prov.get("input_sha256")):
        raise Refusal("B16's output names no input document by its SHA-256")
    if input_sha256 is not None and prov["input_sha256"] != input_sha256:
        raise Refusal("B16's output was not read from this input document (provenance.input_sha256)")
    dsg = design(reading)
    if (doc.get("design") or {}).get("contrasts") != [list(c) for c in dsg.contrasts]:
        raise Refusal("B16's output does not hold the reading's sealed contrasts")
    return dsg


def provenance(inputs: dict) -> dict:
    """The inputs by SHA-256, this package's modules, B16's settings pin and modules, Python and numpy."""
    return {"inputs": dict(sorted(inputs.items())),
            "modules": {p.name: sha256_bytes(p.read_bytes()) for p in sorted(HERE.glob("*.py"))},
            "b16_settings_sha256": SETTINGS_SHA256, "b16_modules": module_hashes(),
            "python": platform.python_version(), "numpy": np.__version__}


def finish(doc: dict) -> dict:
    """JSON-ready (B16's own _strip: no numpy type, an infinity as "inf" or "-inf")."""
    return _strip(doc)


def main_frame(prog: str, description: str, arguments, produce, argv=None) -> int:
    """One reader's command line: ``arguments(parser)`` adds its inputs, ``produce(args)`` returns (the output
    document, the lines of words to print). --out is created exclusively and never overwritten; a refusal, or any
    other error (its message withheld: it may hold a value), writes nothing and exits 2."""
    parser = argparse.ArgumentParser(prog=prog, description=description)
    arguments(parser)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.out.exists():
            raise Refusal(f"{args.out.name} exists; a reader never overwrites")
        doc, words = produce(args)
        data = canonical_json(doc)
        try:
            with open(args.out, "xb") as handle:                 # an exclusive create, not a check-then-write
                handle.write(data)
        except FileExistsError:
            raise Refusal(f"{args.out.name} exists; a reader never overwrites") from None
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - any other error may carry a value in its text: print its type only
        print(f"REFUSED: an unexpected {type(exc).__name__} (its message is withheld: it may hold a value)",
              file=sys.stderr)
        return 2
    print(f"wrote {args.out} sha256 {sha256_bytes(data)}")
    for line in words:
        print(line)
    return 0
