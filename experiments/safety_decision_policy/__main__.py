"""python -m experiments.safety_decision_policy <command> ... (see README.md)

Commands: pins, relevance, dev-table, dev-fit, freeze, run-block, analyze, verify-study, simulate.
Only run-block imports torch (through the engine runner and its real loaders); dev-fit needs numpy.

Exit status: 0 success (run-block: the block result is complete; verify-study: everything
verifies); 1 the block result is aborted or final-incomplete, or verify-study found problems;
2 refused: invalid configuration, input, pins, lock, verification or arguments (nothing new was
run beyond what the receipts record).
"""

from __future__ import annotations

import time

PROCESS_START = time.monotonic()

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from collections.abc import Sequence  # noqa: E402
from pathlib import Path  # noqa: E402

from .common import (LockError, PolicyError, VerificationError, canonical_json, engine_code_identity,  # noqa: E402
                     policy_code_identity, read_canonical, read_json_strict, sha256_file, write_once,
                     write_once_json)

__all__ = ["main"]

_REFUSED = (PolicyError, LockError, VerificationError, FileExistsError, FileNotFoundError, PermissionError,
            ValueError)


def _print(obj: object) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m experiments.safety_decision_policy",
                                     description="Stage B: a small, costed policy comparison (S- versus S+).")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("pins", help="print the actual engine/policy code, manifest, recipe and outcome-definition "
                                    "identities")
    p.add_argument("--prepared", required=True)
    p.add_argument("--recipe", required=True)
    p = sub.add_parser("relevance", help="build the frozen TF-IDF relevance table (engine side)")
    p.add_argument("--prepared", required=True)
    p.add_argument("--out", required=True, help="table (new file)")
    p.add_argument("--receipt", required=True, help="engine-side receipt (new file)")
    p = sub.add_parser("dev-table", help="development feature table from an explicit runs index")
    p.add_argument("--index", required=True)
    p.add_argument("--prepared", required=True)
    p.add_argument("--recipe", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("dev-fit", help="matched ridge fits, group cross-fitting and H1 diagnostics")
    p.add_argument("--table", required=True, action="append", help="development table (repeat for fidelities)")
    p.add_argument("--spec", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("freeze", help="validate, cross-check and freeze a configuration into a new folder")
    p.add_argument("--config", required=True)
    p.add_argument("--record", required=True)
    p.add_argument("--prepared", required=True)
    p.add_argument("--recipe", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("run-block", help="execute or resume one block (real engine; serialized; one GPU)")
    p.add_argument("--study", required=True)
    p.add_argument("--frozen", required=True, help="the folder written by freeze")
    p.add_argument("--record", required=True)
    p.add_argument("--prepared", required=True)
    p.add_argument("--recipe", required=True)
    p.add_argument("--block", required=True, type=int)
    p = sub.add_parser("analyze", help="the exploratory diagnostic over every block result")
    p.add_argument("--study", required=True)
    p.add_argument("--frozen", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("verify-study", help="read-only verification of a (possibly archived) study tree")
    p.add_argument("--study", required=True)
    p.add_argument("--prepared", required=True)
    p.add_argument("--recipe", required=True)
    p.add_argument("--map", action="append", default=[], metavar="RECORDED=LOCAL",
                   help="read-only prefix map for an archived tree (repeat)")
    p = sub.add_parser("simulate", help="ENGINEERING: synthetic end-to-end exercise on the fake backend")
    p.add_argument("--config", required=True, help="an ENGINEERING EXAMPLE configuration template")
    p.add_argument("--spec", required=True, help="a development fit spec")
    p.add_argument("--out", required=True)
    p.add_argument("--world-seed", type=int, default=7)
    return parser


def _recipe(path: str) -> dict:
    from experiments.safety_selection.config import load_recipe

    return load_recipe(path)


def _actual_pins(prepared: str, recipe: dict, record_path: str | None = None,
                 table_sha256: str | None = None) -> dict:
    from experiments.safety_selection.config import config_sha256
    from experiments.safety_selection.prepare import read_manifest

    _, manifest_sha = read_manifest(prepared)
    pins = {"engine_code_sha256": engine_code_identity()["sha256"],
            "policy_code_sha256": policy_code_identity()["sha256"],
            "manifest_sha256": manifest_sha, "recipe_sha256": config_sha256(recipe)}
    if record_path is not None:
        record = read_canonical(record_path)
        pins.update(development_record_sha256=sha256_file(record_path),
                    development_table_sha256=table_sha256,
                    relevance_fingerprint_sha256=record["relevance_fingerprint_sha256"])
    return pins


def _frozen(folder: str) -> dict:
    config = read_canonical(Path(folder) / "config.json")
    receipt = read_canonical(Path(folder) / "freeze-receipt.json")
    if receipt["config_sha256"] != sha256_file(Path(folder) / "config.json"):
        raise VerificationError("the frozen configuration differs from its freeze receipt")
    return config


def _context(args: argparse.Namespace) -> tuple:
    from experiments.safety_selection.planning import build_plan
    from experiments.safety_selection.prepare import read_manifest

    from .config import MODE_ROLES
    from .costs import shape_from_plan

    recipe = _recipe(args.recipe)
    config = _frozen(args.frozen) if hasattr(args, "frozen") else read_json_strict(args.config)
    record = read_canonical(args.record)
    manifest, _ = read_manifest(args.prepared)
    pins = _actual_pins(args.prepared, recipe, args.record, config["pins"]["development_table_sha256"])
    split = MODE_ROLES[config["mode"]]["selection"][0]
    shape = shape_from_plan(build_plan(recipe, args.prepared), split, recipe)
    return recipe, config, record, manifest["data_config"], pins, shape


def _run_block(args: argparse.Namespace) -> dict:
    from experiments.safety_selection import runner
    from experiments.safety_selection.loaders import real_loaders

    from .backend import EngineBackend
    from .controller import Study

    recipe, config, record, data_config, pins, shape = _context(args)
    session = runner.Session(recipe, real_loaders())
    root = Path(args.study)
    backend = EngineBackend(prepared_dir=args.prepared, recipe=recipe, session=session,
                            registry=root / "registry.jsonl")
    study = Study(root, config=config, record=record, backend=backend, recipe=recipe, data_config=data_config,
                  shape=shape, actual_pins=pins, process_start=PROCESS_START)
    try:
        return study.run_block(args.block)
    finally:
        study.close()


def _analyze(root: Path, config: dict) -> dict:
    """The analysis of a study tree through its read-only verified evidence (``study_evidence``): a
    removed or changed lock refuses; every result's costs are its recorded costs, recomputed from the
    durable receipts and session records (a missing session end record: lower bounds, no margin);
    started blocks keep their known incurred costs."""
    from .analysis import analyze
    from .controller import study_evidence

    evidence = study_evidence(root, config)
    return analyze(evidence["results"], config, evidence["static"], evidence["started"],
                   recorded=evidence["recorded"])


def _headline(report: dict) -> dict:
    y = report["endpoints"]["Y"]
    return {"blocks": report["blocks"]["counts"],
            "Y_all_configured_mean": {d: y["all_configured"][d].get("mean_interval") for d in ("raw", "missing_label")},
            "Y_complete_case_mean": {d: y["complete_case"][d].get("mean_interval") for d in ("raw", "missing_label")},
            "Y_confidence_level": report["confidence_level_claims"]["readings"]["Y"],
            "cost_tolerance_exploratory": report["cost_tolerance"]["readings"],
            "physical_controller_seconds": report["costs"]["physical_controller_seconds"],
            "physical_controller_seconds_recorded": report["costs"]["physical_controller_seconds_recorded"],
            "physical_controller_incomplete_because": report["costs"]["physical_controller_incomplete_because"]}


def _simulate(args: argparse.Namespace) -> dict:
    from .controller import Study
    from .synthetic import FakeBackend, make_world, prepare_synthetic

    out = Path(args.out)
    if out.exists():
        raise FileExistsError(f"{out} exists; simulate writes a new folder")
    world = make_world(args.world_seed)
    template = read_json_strict(args.config)
    setup = prepare_synthetic(out / "development", world, template=template, spec=read_json_strict(args.spec))
    results = []
    for block in range(setup["config"]["blocks"]["count"]):   # one fake process per block, as run-block does
        backend = FakeBackend(world)
        study = Study(out / "study", config=setup["config"], record=setup["record"], backend=backend,
                      recipe=setup["recipe"], data_config=setup["data_config"], shape=world.shape("heldout"),
                      actual_pins=setup["pins"], process_start=backend.clock(), engineering_fixture=True)
        try:
            results.append(study.run_block(block))
        finally:
            study.close()
    report = _analyze(out / "study", setup["config"])
    write_once_json(out / "analysis.json", report)
    return {"fixture": "ENGINEERING FIXTURE (synthetic)", "out": str(out),
            "blocks": [{k: r.get(k) for k in ("block", "status", "choices")} for r in results],
            **_headline(report)}


def _command(args: argparse.Namespace) -> tuple[dict, int]:
    if args.command == "pins":
        from .config import ANALYSIS_PLAN_VERSION
        from .outcomes import OUTCOME_PIN

        return {**_actual_pins(args.prepared, _recipe(args.recipe)), "outcome_definition": OUTCOME_PIN,
                "analysis_plan_version": ANALYSIS_PLAN_VERSION}, 0
    if args.command == "relevance":
        from .tfidf import build_relevance

        for path in (args.out, args.receipt):
            if Path(path).exists():
                raise FileExistsError(f"{path} exists; relevance outputs are never replaced")
        data, receipt = build_relevance(args.prepared)
        write_once(args.out, data)
        write_once_json(args.receipt, receipt)
        return {"table_sha256": receipt["table_sha256"], "fingerprint_sha256": receipt["fingerprint_sha256"],
                "fingerprints": receipt["fingerprints"]}, 0
    if args.command == "dev-table":
        from .development import build_table

        if Path(args.out).exists():
            raise FileExistsError(f"{args.out} exists")
        table = build_table(read_json_strict(args.index), prepared_dir=args.prepared, recipe=_recipe(args.recipe))
        digest = write_once(args.out, canonical_json(table))
        return {"table_sha256": digest, "rows": len(table["rows"]), "groups": len(table["groups"]),
                "seeds": table["seeds"]}, 0
    if args.command == "dev-fit":
        from .development import fit_record

        if Path(args.out).exists():
            raise FileExistsError(f"{args.out} exists")
        tables = [(read_canonical(path), sha256_file(path)) for path in args.table]
        record = fit_record(tables, read_json_strict(args.spec))
        digest = write_once(args.out, canonical_json(record))
        return {"record_sha256": digest,
                "selections": [{"table_sha256": t["table_sha256"], "attribution": t["selection"]["attribution"],
                                "lambda": {k: {tg: v["targets"][tg]["selected_lambda"] for tg in v["targets"]}
                                           for k, v in t["fits"].items()}} for t in record["tables"]],
                "limits": record["limits"]}, 0
    if args.command == "freeze":
        from .config import freeze

        recipe, config, record, data_config, pins, shape = _context(args)
        return freeze(config, args.out, recipe=recipe, data_config=data_config, record=record, actual_pins=pins,
                      shape=shape), 0
    if args.command == "run-block":
        result = _run_block(args)
        brief = {k: result.get(k) for k in ("block", "status", "choices", "final_missing", "reason")}
        brief["Y"] = (result.get("endpoints") or {}).get("Y")
        return brief, 0 if result["status"] == "complete" else 1
    if args.command == "analyze":
        if Path(args.out).exists():
            raise FileExistsError(f"{args.out} exists")
        report = _analyze(Path(args.study), _frozen(args.frozen))
        write_once_json(args.out, report)
        return {"out": args.out, **_headline(report), "labels": report["labels"]}, 0
    if args.command == "verify-study":
        from experiments.safety_selection.verify import PathMap

        from .backend import EngineBackend
        from .controller import verify_study

        pairs = [item.split("=", 1) for item in args.map]
        if any(len(pair) != 2 or not all(pair) for pair in pairs):
            raise ValueError("--map takes RECORDED=LOCAL")
        backend = EngineBackend(prepared_dir=args.prepared, recipe=_recipe(args.recipe), path_map=PathMap(pairs))
        report = verify_study(args.study, backend)
        return report, 0 if report["complete"] else 1
    if args.command == "simulate":
        return _simulate(args), 0
    raise ValueError(f"unknown command {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        out, status = _command(args)
    except _REFUSED as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2
    _print(out)
    return status


if __name__ == "__main__":
    sys.exit(main())
