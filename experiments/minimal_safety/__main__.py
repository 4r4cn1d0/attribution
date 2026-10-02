"""python -m experiments.minimal_safety {plan,prepare,run,summarize,fetch} ... (see README.md)

plan, prepare, summarize and fetch import only the standard library; run imports torch.
Exit status: 0 success (for run and summarize: status complete); 1 run incomplete (cap, error,
interrupt or unverified evidence; summary still written); 2 invalid config, data, arguments,
unfrozen inputs or an unreadable run directory (nothing was trained or summarized).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from . import data, report
from .plan import ConfigError, build_plan, load_config

__all__ = ["main"]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m experiments.minimal_safety",
                                     description="Minimal real safety-data calibration.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan", help="offline dry run: validate the config and report the plan")
    p.add_argument("--config", required=True)
    p.add_argument("--prepared", help="prepared-data directory (adds data streams and exposure)")
    p = sub.add_parser("prepare", help="deterministic data preparation from local raw JSONL")
    p.add_argument("--config", required=True)
    p.add_argument("--train", required=True, help="local raw train.jsonl (hash-checked)")
    p.add_argument("--ref", required=True, help="local raw ref.jsonl (hash-checked)")
    p.add_argument("--out", required=True)
    p = sub.add_parser("run", help="the local calibration run (trains; needs cached assets)")
    p.add_argument("--config", required=True)
    p.add_argument("--prepared", required=True)
    p.add_argument("--run-dir", required=True, help="new or empty directory; never resumed")
    p.add_argument("--manifest-sha256", required=True, help="the frozen manifest hash to accept")
    p = sub.add_parser("summarize", help="verify and rebuild summary.json and report.md from a "
                                         "run directory (recovers interrupted runs)")
    p.add_argument("--run-dir", required=True)
    p = sub.add_parser("fetch", help="OPTIONAL public download of the two pinned raw files")
    p.add_argument("--config", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--confirm-public-download", action="store_true")
    return parser


def _print(obj: object) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False))


def _brief(summary: dict) -> dict:
    return {k: summary[k] for k in ("status", "stop_reason", "termination", "problems",
                                    "conclusion")}


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            _print(build_plan(load_config(args.config), args.prepared))
            return 0
        if args.command == "prepare":
            _print(data.prepare_files(load_config(args.config), args.train, args.ref, args.out))
            return 0
        if args.command == "fetch":
            _print(data.fetch_raw(load_config(args.config), args.out, args.confirm_public_download))
            return 0
        if args.command == "summarize":
            summary = report.finalize(args.run_dir, write_status=False)
            _print(_brief(summary))
            return 0 if summary["status"] == "complete" else 1
        from .run import RunError, main_run  # the only path that imports torch

        try:
            summary = main_run(args.config, args.prepared, args.run_dir, args.manifest_sha256)
        except RunError as exc:
            print(json.dumps({"ok": False, "error": f"RunError: {exc}"}), file=sys.stderr)
            return 2
        _print({**_brief(summary), "summary": f"{args.run_dir}/summary.json",
                "report": f"{args.run_dir}/report.md"})
        return 0 if summary["status"] == "complete" else 1
    except (ConfigError, data.DataError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
