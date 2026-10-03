"""python -m experiments.durability <command> ... (administrative; read-only towards the source)

Commands:

- ``ingest``: acknowledge sealed engine run folders from a tree (possibly a relocated archive,
  through ``--map RECORDED=LOCAL``) into a destination: the prepared data and the engine source
  first, then each ``--run`` in the order given (dependencies first). Every acknowledgement follows
  the full copy, hash and restore-verify path.
- ``restore``: place every acknowledged unit at its recorded path, or under ``--mirror``.
- ``acks``: list the acknowledgements in a destination namespace.
- ``check-destination``: one small round trip that shows a destination behaves as the vault needs:
  probe, a staging upload read back and hashed, an exclusive commit, a refused duplicate, a listing
  and the removal of the staging objects. On GitHub it uses its own release scheme
  (``connector-test``) and leaves two tiny final objects there, which are never deleted.
- ``check-provider``: read-only questions to the configured provider, reported as shapes (types,
  counts, whether each answer was usable), never as account details.
- ``check-watchdog``: what the shutdown watchdog's records say about a worker's pod: its latest
  acknowledged arm, the stop time, the acknowledging workflow run and any recorded stop. It reads
  the backup repository's release assets and nothing else; it arms nothing.

``--destination`` is a directory, or ``github:owner/repo`` with ``--declared-free-bytes`` (the token
comes from the environment variable ``ATTRIBUTION_BACKUP_GITHUB_TOKEN``; without it every call
refuses). No command admits, dispatches, creates, starts, stops or deletes anything on a provider.

Exit status: 0 done; 2 refused (nothing was acknowledged or restored beyond what the output lists).
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from .backup import Vault
from .common import CollisionError, DurabilityError, Journal, SourceMap, sha256_bytes, token
from .destination import Destination
from .runpod_provider import SHUTDOWN_GAP, RunPodProvider
from .units import code_unit, prepared_unit, run_unit
from .wiring import destination_from, provider_from, shutdown_from

__all__ = ["main"]


def _destination_options(p: argparse.ArgumentParser) -> None:
    p.add_argument("--destination", required=True, help="a directory, or github:owner/repo")
    p.add_argument("--declared-free-bytes", type=int, help="github: the capacity you declare (GitHub reports none)")
    p.add_argument("--github-scheme", help="github: release-name scheme (default durability-v1)")
    p.add_argument("--github-shards", type=int, help="github: number of shard releases (fixed per scheme)")
    p.add_argument("--github-api-url", help=argparse.SUPPRESS)       # tests: a fake API on 127.0.0.1
    p.add_argument("--github-upload-url", help=argparse.SUPPRESS)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m experiments.durability",
                                     description="Recovery safeguards: administrative commands.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("ingest", "restore", "acks"):
        p = sub.add_parser(name)
        _destination_options(p)
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
    p = sub.add_parser("check-destination")
    _destination_options(p)
    p = sub.add_parser("check-provider")
    p.add_argument("--config", required=True, help="provider configuration (JSON; see the README)")
    p.add_argument("--worker", required=True, help="a worker name from the configuration")
    p.add_argument("--path", help="a source path to check for persistence")
    p.add_argument("--runpod-rest-url", help=argparse.SUPPRESS)      # tests: a fake API on 127.0.0.1
    p.add_argument("--runpod-graphql-url", help=argparse.SUPPRESS)
    p = sub.add_parser("check-watchdog")
    p.add_argument("--config", required=True, help="provider configuration with a shutdown section (JSON; README)")
    p.add_argument("--worker", required=True, help="a worker name from the configuration")
    p.add_argument("--github-api-url", help=argparse.SUPPRESS)       # tests: a fake API on 127.0.0.1
    p.add_argument("--github-upload-url", help=argparse.SUPPRESS)
    return parser


def _destination(args: argparse.Namespace, scheme: str | None = None) -> Destination:
    options = {}
    if args.destination.startswith("github:"):
        if args.declared_free_bytes is None:
            raise DurabilityError("--declared-free-bytes is required for a GitHub destination")
        options["declared_free_bytes"] = args.declared_free_bytes
        for name, value in (("scheme", scheme or args.github_scheme), ("shards", args.github_shards),
                            ("api_url", args.github_api_url), ("upload_url", args.github_upload_url)):
            if value is not None:
                options[name] = value
    return destination_from(args.destination, **options)


def _vault(args: argparse.Namespace, require_code: bool = True) -> Vault:
    pairs = [item.split("=", 1) for item in args.map]
    if any(len(pair) != 2 or not all(pair) for pair in pairs):
        raise DurabilityError("--map takes RECORDED=LOCAL")
    return Vault(_destination(args), args.namespace, journal=Journal(args.journal), scratch=args.scratch,
                 source_map=SourceMap(pairs), require_code=require_code)


def _brief(ack: dict) -> dict:
    return {key: ack.get(key) for key in ("unit", "unit_kind", "path", "files", "bytes", "seal_sha256",
                                          "verification", "acknowledged_utc")}


def _check_destination(destination: Destination) -> dict:
    """The round trip of the module doc; every step must hold or the command refuses."""
    run, data = token(), b"durability connector check\n"
    staged, final = f"connector-check/staging/{run}/object", f"connector-check/final/{run}/object"
    steps = {}
    destination.probe()
    steps["probe"] = True
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / "object"
        source.write_bytes(data)
        destination.upload(source, staged)
        steps["read_back_hash_matches"] = destination.sha256(staged) == (sha256_bytes(data), len(data))
        steps["commit_created"] = destination.commit(staged, final) is True
        steps["final_reads_back"] = destination.read(final) == data
        source.write_bytes(data + b"different\n")
        destination.upload(source, staged)
        try:
            destination.commit(staged, final)
            steps["different_bytes_refused"] = False
        except CollisionError:
            steps["different_bytes_refused"] = True
        destination.discard(staged)
    try:
        destination.put_new(f"connector-check/final/{run}/record", b"{}")
        destination.put_new(f"connector-check/final/{run}/record", b"{ }")
        steps["duplicate_record_refused"] = False
    except CollisionError:
        steps["duplicate_record_refused"] = True
    listed = destination.list(f"connector-check/final/{run}")
    steps["listed"] = listed == [final, f"connector-check/final/{run}/record"]
    steps["staging_removed"] = destination.list(f"connector-check/staging/{run}") == []
    if not all(steps.values()):
        raise DurabilityError(f"the destination did not behave as the vault needs: {steps}")
    return {"destination": destination.describe(), "steps": steps,
            "left_behind": "two tiny final objects under connector-check/final (final objects are never deleted)"}


def _check_provider(args: argparse.Namespace) -> dict:
    """Shapes only: what kind of answer each read-only question got, never the account's values."""
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    options = {name: value for name, value in (("rest_url", args.runpod_rest_url),
                                               ("graphql_url", args.runpod_graphql_url)) if value is not None}
    provider = provider_from(config, **options)
    out: dict = {"provider": type(provider).__name__, "creates_starts_stops_or_deletes": False}

    def ask(name: str, call, shape) -> None:
        try:
            out[name] = {"answered": True, **shape(call())}
        except DurabilityError as exc:
            out[name] = {"answered": False, "refused_as": type(exc).__name__, "reason": str(exc)[:200]}

    ask("balance", provider.read_balance, lambda r: {"amount_type": type(r.amount).__name__, "kind": r.kind,
                                                     "recognized": r.recognized, "currency_stated": r.currency != "unconfirmed"})
    ask("rates", lambda: provider.read_rates(args.worker),
        lambda r: {"gpu_per_hour_type": type(r.gpu_per_hour).__name__, "storage_derived": r.storage_per_hour >= 0})
    ask("liabilities", provider.list_liabilities,
        lambda items: {"count": len(items), "attached_to_a_configured_worker": sum(i.worker is not None for i in items)})
    if args.path:
        ask("persistence", lambda: provider.confirm_persistent(args.path),
            lambda r: {"persistent": r.get("persistent") is True})
    # this command never asks a provider to arm anything; it reports whether the adapter could
    if isinstance(provider, RunPodProvider) and provider.shutdown is None:
        out["shutdown"] = {"can_arm": False, "why": SHUTDOWN_GAP}
    elif isinstance(provider, RunPodProvider):
        out["shutdown"] = {"can_arm": "only with the watchdog's acknowledgement at admission (not asked here)",
                           "watchdog": provider.shutdown.describe()}
    else:
        out["shutdown"] = {"can_arm": "not asked"}
    return out


def _check_watchdog(args: argparse.Namespace) -> dict:
    """Reads the watchdog's records for one worker's pod; arms and stops nothing."""
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    pod = (config.get("worker_pods") or {}).get(args.worker) if isinstance(config, dict) else None
    if not isinstance(pod, str) or not pod:
        raise DurabilityError("the configuration names no pod for this worker")
    options = {name: value for name, value in (("api_url", args.github_api_url),
                                               ("upload_url", args.github_upload_url)) if value is not None}
    watchdog = shutdown_from(config.get("shutdown"), **options)
    if watchdog is None:
        return {"watchdog": None, "armed": False, "why": SHUTDOWN_GAP}
    return {"watchdog": watchdog.describe(), **watchdog.status(pod)}


def _command(args: argparse.Namespace) -> dict:
    if args.command == "check-destination":
        return _check_destination(_destination(args, scheme="connector-test"))
    if args.command == "check-provider":
        return _check_provider(args)
    if args.command == "check-watchdog":
        return _check_watchdog(args)
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
