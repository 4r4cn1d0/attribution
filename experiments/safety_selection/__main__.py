"""python -m experiments.safety_selection <command> ... (see README.md)

Commands: prepare, plan, make-job, run-one, eval-state, calibrate, attributes, score-groups,
score-audit, verify, compare-generations, export-selector-view, fetch-data, fetch-models, and the
headroom amendment's tools (draft): score-rows, generate-rewrites (GPU) and build-edits (CPU).
Only the job commands import torch; prepare imports transformers for the pinned tokenizer only.

Exit status: 0 success (verify: own files, dependency chain and, with --prepared, stream all
verify); 1 a job failed after creating its folder (error.txt preserved) or verify found it
incomplete; 2 invalid config, job, data, access or arguments (nothing was trained or scored,
and no folder was created).
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections.abc import Sequence
from pathlib import Path

from .common import code_identity, utc_now
from .config import ConfigError, load_data_config, load_recipe
from .jobs import AccessError, JobError
from .ledger import RunDirError
from .prepare import HiddenAccessError
from .sources import DataError

__all__ = ["main"]

_INVALID = (ConfigError, JobError, AccessError, DataError, HiddenAccessError, RunDirError,
            FileNotFoundError, FileExistsError, PermissionError, ValueError)


def _print(obj: object) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False))


def _error(exc: BaseException) -> None:
    print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m experiments.safety_selection",
                                     description="Safety-selection study engine (stage A).")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="deterministic preparation from local pinned raw files")
    p.add_argument("--data-config", required=True)
    for name in ("date-train", "date-ref", "toxicchat-test", "arc-validation", "arc-test"):
        p.add_argument(f"--{name}", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("plan", help="offline workload plan (nothing loads or runs)")
    p.add_argument("--recipe", required=True)
    p.add_argument("--prepared", required=True)
    p = sub.add_parser("make-job", help="write a job file with the actual identity hashes")
    p.add_argument("kind", choices=["run-one", "eval-state", "attributes", "score-groups"])
    p.add_argument("--prepared", required=True)
    p.add_argument("--recipe", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--pin-code", action="store_true", help="also pin the current code hash")
    p.add_argument("--split")
    p.add_argument("--arm")
    p.add_argument("--seed", type=int)
    p.add_argument("--role")
    p.add_argument("--target")
    p.add_argument("--bank")
    p.add_argument("--resume-from")
    p.add_argument("--replicate-of")
    p.add_argument("--source-run")
    p.add_argument("--checkpoint")
    p.add_argument("--a0-state", action="append", default=[], help="CHECKPOINT=RUN_DIR (repeat)")
    p.add_argument("--groups", help="comma-separated group ids")
    p.add_argument("--edit", help="run-one: an edit file; the arm becomes edit-<its SHA-256>")
    p.add_argument("--wall-limit-seconds", type=float)
    for name, helptext in (("run-one", "train/continue one trajectory to a checkpoint and evaluate"),
                           ("eval-state", "evaluate a saved state (evaluation settings may differ)"),
                           ("attributes", "checkpoint-gradient features on an a0 trajectory"),
                           ("score-groups", "guard scores of a split's group member rows")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--job", required=True)
        p.add_argument("--prepared", required=True)
        p.add_argument("--recipe", required=True)
        p.add_argument("--out", required=True, help="new folder; never replaced")
        if name in ("run-one", "eval-state"):
            p.add_argument("--allow-hidden-reference", action="store_true",
                           help="required for reference-role evaluation on the hidden bank")
        if name == "run-one":
            p.add_argument("--registry", help="trajectory registry JSONL (refuses seed reuse)")
    p = sub.add_parser("calibrate", help="development-only trajectories over all checkpoints")
    p.add_argument("--prepared", required=True)
    p.add_argument("--recipe", required=True)
    p.add_argument("--arms", required=True, help="comma-separated: a0 and/or development group ids")
    p.add_argument("--seeds", required=True, help="comma-separated development seeds")
    p.add_argument("--out-root", required=True)
    p.add_argument("--checkpoints", help="ordered subset of the recipe checkpoints")
    p.add_argument("--base-eval", action="store_true", help="also evaluate the seeded adapter (B = 0)")
    p.add_argument("--wall-limit-seconds", type=float)
    p.add_argument("--edit", action="append", default=[],
                   help="an edit file (repeat); its arm edit-<SHA-256> is calibrated with it")
    p = sub.add_parser("score-rows", help="headroom (draft): guard Unsafe scores of every edit-pool row")
    p.add_argument("--recipe", required=True)
    p.add_argument("--prepared", required=True)
    p.add_argument("--out", required=True, help="new folder; never replaced")
    p = sub.add_parser("generate-rewrites", help="headroom (draft): replacement responses for the top rows")
    p.add_argument("--config", required=True, help="the rewrite config (generator and prompts)")
    p.add_argument("--recipe", required=True, help="the training recipe (guard, policy tokenizer, limits)")
    p.add_argument("--prepared", required=True)
    p.add_argument("--scores", required=True, help="the frozen scores.json of score-rows")
    p.add_argument("--percent", default="10", help="the largest edit size (default 10)")
    p.add_argument("--random-percent", default="10", help="the random control's size (default 10)")
    p.add_argument("--out", required=True, help="new folder; never replaced")
    p = sub.add_parser("build-edits", help="headroom (draft): the positive control's edit files (CPU only)")
    p.add_argument("--prepared", required=True)
    p.add_argument("--scores", required=True)
    p.add_argument("--rewrites", help="the frozen rewrites.json of generate-rewrites")
    p.add_argument("--percents", default="2.5,4,7,10")
    p.add_argument("--random-percent", default="10")
    p.add_argument("--round", choices=["1"], help="only the files of round 1: remove, random remove, rewrite and "
                                                  "random rewrite at 10%% (needs --rewrites)")
    p.add_argument("--out", required=True, help="new folder; never replaced")
    p = sub.add_parser("score-audit", help="guard scores of a blind-context audit file")
    p.add_argument("--recipe", required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("verify", help="verify a run folder: own files, dependency chain, and the "
                                      "stream with --prepared")
    p.add_argument("--run", required=True)
    p.add_argument("--prepared")
    p.add_argument("--map", action="append", default=[], metavar="RECORDED=LOCAL",
                   help="read-only prefix map for recorded dependency paths of an archived tree (repeat)")
    p = sub.add_parser("compare-generations", help="agreement of two evaluations of one state (counts only)")
    p.add_argument("--first", required=True)
    p.add_argument("--second", required=True)
    p.add_argument("--checkpoint", required=True)
    p = sub.add_parser("export-selector-view", help="whitelisted selector input from verified prepared "
                                                    "data and a complete score-groups run")
    p.add_argument("--prepared", required=True)
    p.add_argument("--guard-run", required=True)
    p.add_argument("--out", required=True, help="the view (new file; the selector input)")
    p.add_argument("--receipt", required=True, help="its receipt (new file; engine/auditor side)")
    p = sub.add_parser("fetch-data", help="OPTIONAL public download of the pinned raw files")
    p.add_argument("--data-config", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--confirm-public-download", action="store_true")
    p = sub.add_parser("fetch-models", help="OPTIONAL public download of pinned model snapshots")
    p.add_argument("--recipe", required=True)
    p.add_argument("--which", default="policy,guard", help="policy,guard,secondary_toxicity")
    p.add_argument("--confirm-public-download", action="store_true")
    return parser


def _prepare(args: argparse.Namespace) -> dict:
    from .assets import tokenizer_identity
    from .loaders import load_tokenizer
    from .prepare import prepare, read_raw_inputs, write_prepared

    config = load_data_config(args.data_config)
    spec = config["tokenizer"]
    tokenizer, _ = load_tokenizer(spec["repo_id"], spec["revision"])
    paths = {"date_train": args.date_train, "date_ref": args.date_ref,
             "toxicchat_test": args.toxicchat_test, "arc_validation": args.arc_validation,
             "arc_test": args.arc_test}
    files = prepare(config, read_raw_inputs(paths), tokenizer,
                    tokenizer_identity(spec["repo_id"], spec["revision"]))
    receipt = {"python": sys.version, "platform": platform.platform(), "code": code_identity(),
               "utc": utc_now(), "inputs": {k: str(Path(v).resolve()) for k, v in paths.items()}}
    digest = write_prepared(args.out, files, receipt)
    manifest = json.loads(files["manifest.json"])
    return {"manifest_sha256": digest, "out": args.out, "corpus": manifest["corpus"],
            "groups": manifest["groups"], "banks": manifest["banks"],
            "eligibility": manifest["eligibility"], "token_audit": manifest["token_audit"]}


def _make_job(args: argparse.Namespace) -> dict:
    from .planning import make_job

    recipe = load_recipe(args.recipe)
    common = {"wall_limit_seconds": args.wall_limit_seconds}
    if args.kind == "run-one":
        fields = {"split": args.split, "arm": args.arm, "seed": args.seed, "role": args.role,
                  "target_checkpoint": args.target, "evaluate_bank": args.bank,
                  "resume_from": args.resume_from, "replicate_of": args.replicate_of}
        if args.edit:
            from .edits import arm_of

            arm = arm_of(Path(args.edit).read_bytes())
            if args.arm not in (None, arm):
                raise JobError(f"--arm {args.arm} is not the edit file's arm {arm}")
            fields.update(arm=arm, edit=str(args.edit))
    elif args.kind == "eval-state":
        fields = {"source_run": args.source_run, "checkpoint": args.checkpoint, "evaluate_bank": args.bank}
    elif args.kind == "attributes":
        pairs = [item.split("=", 1) for item in args.a0_state]
        if any(len(p) != 2 for p in pairs):
            raise JobError("--a0-state takes CHECKPOINT=RUN_DIR")
        fields = {"split": args.split, "seed": args.seed, "role": args.role,
                  "a0_states": dict(pairs), "group_ids": (args.groups or "").split(","),
                  "query_bank": "ref"}
    else:
        fields = {"split": args.split}
    return make_job(args.kind, prepared_dir=args.prepared, recipe=recipe, pin_code=args.pin_code,
                    out=args.out, **common, **fields)


def _job_command(args: argparse.Namespace) -> dict:
    from . import runner
    from .loaders import real_loaders

    recipe = load_recipe(args.recipe)
    session = runner.Session(recipe, real_loaders())
    if args.command == "calibrate":
        from .edits import arm_of

        edits = {arm_of(Path(path).read_bytes()): path for path in args.edit}
        arms = args.arms.split(",")
        arms += [arm for arm in edits if arm not in arms]
        return runner.calibrate(prepared_dir=args.prepared, out_root=args.out_root, session=session,
                                arms=arms, seeds=[int(s) for s in args.seeds.split(",")],
                                checkpoints=args.checkpoints.split(",") if args.checkpoints else None,
                                base_eval=args.base_eval, wall_limit_seconds=args.wall_limit_seconds,
                                edits=edits)
    if args.command == "score-rows":
        from .headroom import score_rows_job

        return score_rows_job(session, args.prepared, args.out)
    if args.command == "generate-rewrites":
        from .headroom import generate_rewrites_job, validate_rewrite_config

        config = validate_rewrite_config(json.loads(Path(args.config).read_text(encoding="utf-8")))
        return generate_rewrites_job(config, session, args.prepared, args.scores, args.out, percent=args.percent,
                                     random_percent=args.random_percent)
    if args.command == "score-audit":
        return runner.score_audit(args.input, out_dir=args.out, session=session)
    job = json.loads(Path(args.job).read_text(encoding="utf-8"))
    if args.command == "run-one":
        return runner.run_one(job, prepared_dir=args.prepared, out_dir=args.out, session=session,
                              allow_hidden=args.allow_hidden_reference, registry=args.registry)
    if args.command == "eval-state":
        return runner.eval_state(job, prepared_dir=args.prepared, out_dir=args.out, session=session,
                                 allow_hidden=args.allow_hidden_reference)
    if args.command == "attributes":
        return runner.attributes(job, prepared_dir=args.prepared, out_dir=args.out, session=session)
    return runner.score_groups(job, prepared_dir=args.prepared, out_dir=args.out, session=session)


def _brief(result: dict) -> dict:
    """Counts and identities only: evaluation texts never reach stdout."""
    keys = ("run_dir", "complete", "kind", "target_checkpoint", "trajectory", "incremental_train_cost",
            "trajectory_cost", "evaluation", "scores", "costs", "summary", "units", "registry",
            "checkpoint", "rows", "groups", "split", "scores_sha256", "rewrites_sha256", "pool_rows",
            "scored_rows", "unscored_rows", "accepted", "accepted_on_retry", "excluded")
    return {k: result[k] for k in keys if k in result}


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "prepare":
            _print(_prepare(args))
            return 0
        if args.command == "plan":
            from .planning import build_plan

            _print(build_plan(load_recipe(args.recipe), args.prepared))
            return 0
        if args.command == "make-job":
            _print(_make_job(args))
            return 0
        if args.command == "build-edits":
            from .headroom import ROUND_1, build_edits_job

            _print(build_edits_job(args.prepared, args.scores, args.out, rewrites_path=args.rewrites,
                                   percents=args.percents.split(","), random_percent=args.random_percent,
                                   only=ROUND_1 if args.round == "1" else None))
            return 0
        if args.command == "verify":
            from .verify import PathMap, verify_run

            pairs = [item.split("=", 1) for item in args.map]
            if any(len(pair) != 2 or not all(pair) for pair in pairs):
                raise ValueError("--map takes RECORDED=LOCAL")
            result = verify_run(args.run, args.prepared, PathMap(pairs))
            _print(result)
            return 0 if result["complete"] else 1
        if args.command == "compare-generations":
            from .verify import compare_generations

            _print(compare_generations(args.first, args.second, args.checkpoint))
            return 0
        if args.command == "export-selector-view":
            from .selector_view import export_selector_view

            _print(export_selector_view(args.prepared, args.guard_run, args.out, args.receipt))
            return 0
        if args.command == "fetch-data":
            from .assets import fetch_data

            _print(fetch_data(load_data_config(args.data_config), args.out, args.confirm_public_download))
            return 0
        if args.command == "fetch-models":
            from .assets import fetch_models

            _print(fetch_models(load_recipe(args.recipe), args.which.split(","), args.confirm_public_download))
            return 0
    except _INVALID as exc:
        _error(exc)
        return 2
    out = getattr(args, "out", None) or getattr(args, "out_root", None)
    try:
        _print(_brief(_job_command(args)))
        return 0
    except BaseException as exc:  # noqa: BLE001 - every failure is reported with its status
        _error(exc)
        failed_here = out is not None and Path(out).is_dir() and any(Path(out).rglob("error.txt"))
        if isinstance(exc, KeyboardInterrupt) or failed_here:
            return 1
        return 2 if isinstance(exc, _INVALID) else 1


if __name__ == "__main__":
    sys.exit(main())
