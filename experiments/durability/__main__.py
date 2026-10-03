"""python -m experiments.durability <command> ... (local, read-only towards the source)

Commands:

- ``ingest``: acknowledge sealed engine run folders from a tree (possibly a relocated archive,
  through ``--map RECORDED=LOCAL``) into a directory destination: the prepared data and the engine
  source first, then each ``--run`` in the order given (dependencies first). Every acknowledgement
  follows the full copy, hash and restore-verify path.
- ``restore``: place every acknowledged unit at its recorded path, or under ``--mirror``.
- ``acks``: list the acknowledgements in a destination namespace.

There is no command that admits, dispatches or runs anything on a provider: the provider and
remote-destination adapters are not configured, and admission fails closed without them.

Exit status: 0 done; 2 refused (nothing was acknowledged or restored beyond what the output lists).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .backup import Vault
from .common import DurabilityError, Journal, SourceMap
from .destination import LocalDirectoryDestination
from .units import code_unit, prepared_unit, run_unit

__all__ = ["main"]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m experiments.durability",
                                     description="Recovery safeguards: local administrative commands.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("ingest", "restore", "acks"):
        p = sub.add_parser(name)
        p.add_argument("--destination", required=True, help="destination directory")
        p.add_argument("--namespace", required=True, help="one source volume")
        p.add_argument("--scratch", required=True, help="local folder for restore checks (outside any unit)")
        p.add_argument("--journal", required=True, help="outcome-blind journal file (outside any unit)")
        p.add_argument("--map", action="append", default=[], metavar="RECORDED=LOCAL",
                       help="where a recorded prefix is now (repeat; prefixes must not nest)")
        if name == "ingest":
            p.add_argument("--prepared", required=True, help="recorded path of the prepared-data folder")
            p.add_argument("--code", help="recorded path of the experiments folder holding the engine source")
            p.add_argument("--no-code-pin", action="store_true",
                           help="acknowledge without the engine source (evidence only; say so explicitly)")
            p.add_argument("--run", action="append", default=[],
                           help="recorded run folder (repeat, dependencies first)")
        if name == "restore":
            p.add_argument("--mirror", help="restore under this folder in the recorded layout instead of in place")
    return parser


def _vault(args: argparse.Namespace, require_code: bool = True) -> Vault:
    pairs = [item.split("=", 1) for item in args.map]
    if any(len(pair) != 2 or not all(pair) for pair in pairs):
        raise DurabilityError("--map takes RECORDED=LOCAL")
    return Vault(LocalDirectoryDestination(args.destination), args.namespace, journal=Journal(args.journal),
                 scratch=args.scratch, source_map=SourceMap(pairs), require_code=require_code)


def _brief(ack: dict) -> dict:
    return {key: ack.get(key) for key in ("unit", "unit_kind", "path", "files", "bytes", "seal_sha256",
                                          "verification", "acknowledged_utc")}


def _command(args: argparse.Namespace) -> dict:
    if args.command == "ingest":
        if bool(args.code) == bool(args.no_code_pin):
            raise DurabilityError("give --code, or --no-code-pin to acknowledge evidence without its source")
        vault = _vault(args, require_code=not args.no_code_pin)
        units = [prepared_unit(args.prepared, vault.source_map)]
        if args.code:
            units.append(code_unit(args.code, vault.source_map))
        acks = [_brief(vault.acknowledge(unit)) for unit in units]
        acks += [_brief(vault.acknowledge(run_unit(run, vault.source_map))) for run in args.run]
        return {"acknowledged": acks, "code_pinned": bool(args.code)}
    vault = _vault(args)
    if args.command == "restore":
        return vault.restore(mirror=Path(args.mirror) if args.mirror else None)
    return {"acknowledged": [_brief(vault.read_ack(unit.unit_id)) for unit in vault.acknowledged_units()]}


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        out = _command(args)
    except (DurabilityError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
