"""Command line: ``python -m scripts.stage1_s1.reading --input tables.json --out reading.json``.

Reads one input document (schema.py), writes one output document (reading.py) as canonical JSON into a new file.
Exit 0 on success, 2 on a refusal (nothing written). Messages hold names, counts and hashes only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.stage1_s1.reading.reading import read
from scripts.stage1_s1.reading.settings import Refusal, canonical_json, sha256_bytes, strict_json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="the stage-1 reading (B16)")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.out.exists():
            raise Refusal(f"{args.out.name} exists; the reading never overwrites")
        data = args.input.read_bytes()
        out = read(strict_json(data), sha256_bytes(data))
        try:
            with open(args.out, "xb") as handle:                 # an exclusive create, not a check-then-write
                handle.write(canonical_json(out))
        except FileExistsError:
            raise Refusal(f"{args.out.name} exists; the reading never overwrites") from None
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.out} ({sha256_bytes(args.out.read_bytes())[:16]}); headline: {out['headline']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
