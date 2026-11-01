"""ENGINEERING FIXTURES for the O-ext unit runner's tests (synthetic only; nothing is downloaded, and no real record,
PHTest text, prepared row or answer is read). They reuse the engine's fixtures (the synthetic prepared set, the tiny
random policy) and the O-ext fixtures (oext_fixtures: a synthetic PHTest bank written as build_oext writes it, a
W1-18-shaped record, a judge scripted by answer length). On top: three engine units made by the engine's own run_one
(a dev-evaluated a0 unit at seed 1102, a Gate-A-like source unit at 1101 and its train-only regeneration), this
script's settings with the fixture's pins, a loader variant whose policy carries a non-zero adapter (so theta0's
disabled adapter is visible), and a frozen copy of B15's contract parser. None of these numbers is a scientific
result."""

from __future__ import annotations

import ast
import contextlib
import copy
import dataclasses
import hashlib
import importlib
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

PKG_DIR = Path(__file__).resolve().parents[1]
REPO = PKG_DIR.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
ou = importlib.import_module(f"scripts.{PKG_DIR.name}.oext_unit")

import oext_fixtures as ofx  # noqa: E402

fx = ofx.fx
oe = ofx.oe
from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

import experiments.safety_selection as _engine  # noqa: E402

ENGINE_ROOT = Path(_engine.__file__).resolve().parents[2]      # the workspace (also under the mutation runner)
CUT = 3                        # the fixture O-ext cut (the fixture recipe's cap is 8 new tokens)
THRESHOLD = 4                  # the scripted judge refuses a reply of at least 4 characters
SEEDS = {"evaluated": 1102, "source": 1101, "regen": 1101}
kept = ofx.kept
Failed = ofx.Failed


def recipe(**changes) -> dict:
    return ofx.recipe(**changes)


def loaders(*, perturb: bool = False, seen: list | None = None, fail_guard: bool = False):
    """The O-ext fixture loaders (scripted judge). ``perturb``: the loaded policy's lora_B matrices are set to fixed
    non-zero values, so the adapter changes the answers and only a disabled adapter gives theta0's. ``fail_guard``:
    the judge raises when it scores (a failure after the folder is made)."""
    import torch

    base = ofx.loaders(threshold=THRESHOLD, seen=seen)
    policy_loader, guard_loader = base.policy, base.guard

    def policy(recipe_, ledger):
        p = policy_loader(recipe_, ledger)
        if perturb:
            gen = torch.Generator().manual_seed(7)
            with torch.no_grad():
                for name, param in p.named:
                    if ".lora_B." in name:
                        param.copy_(torch.randn(param.shape, generator=gen) * 3.0)
        return p

    def guard(recipe_, ledger, device):
        scorer = guard_loader(recipe_, ledger, device)
        if fail_guard:
            def broken(prompts, check=None):
                raise RuntimeError(f"{ofx.FIXTURE}: injected judge failure")
            scorer.generate = broken
        return scorer

    return dataclasses.replace(base, policy=policy, guard=guard)


def session(rec: dict | None = None, **options):
    from experiments.safety_selection import runner

    return runner.Session(rec or recipe(), loaders(**options))


def _job(prepared_dir: Path, rec: dict, out: Path, **fields) -> dict:
    from experiments.safety_selection.planning import make_job

    return make_job("run-one", prepared_dir=prepared_dir, recipe=rec, pin_code=False, out=out,
                    wall_limit_seconds=None, split="dev", arm="a0", role="development", replicate_of=None,
                    target_checkpoint="e1", resume_from=None, **fields)


def make_unit(prepared_dir: Path, out: Path, seed: int, evaluate: bool, rec: dict | None = None) -> Path:
    """An engine run-one a0 unit from init to e1, with (evaluate) or without its dev-bank evaluation."""
    from experiments.safety_selection import runner

    rec = rec or recipe()
    job = _job(prepared_dir, rec, out.parent / f"{out.name}-job.json", seed=seed,
               evaluate_bank="dev" if evaluate else None)
    runner.run_one(job, prepared_dir=prepared_dir, out_dir=out, session=session(rec))
    return out


def real_doc() -> dict:
    return s1.strict_json(ou.SETTINGS_PATH.read_bytes())


def settings_doc(manifest_sha256: str, oext_sha256: str, rec: dict | None = None, **changes) -> dict:
    """The committed settings with the fixture's pins (manifest, recipe, O-ext settings); ``changes`` use dotted keys
    (``__`` for .)."""
    rec = rec or recipe()
    doc = copy.deepcopy(real_doc())
    doc["prepared"]["manifest_sha256"] = manifest_sha256
    doc["recipes"].update(allowed={"fixture": config_sha256(rec)},
                          generation_sha256=sha256_bytes(canonical_json(rec["generation"])),
                          guard_sha256=sha256_bytes(canonical_json(rec["guard"])))
    doc["oext"]["module_sha256"] = oe.module_sha256()
    doc["oext"]["settings"]["sha256"] = oext_sha256
    for dotted, value in changes.items():
        ofx.set_dotted(doc, dotted.replace("__", "."), value)
    return doc


def build_world(base: Path) -> SimpleNamespace:
    bank_dir, _ = fx.prepare_dir_v3(base / "prepared-v3")
    prepared, manifest = fx.prepare_task_dir(base / "prepared-kt", bank_dir)
    rec = recipe()
    recipe_file = base / "recipe.json"
    recipe_file.write_bytes(canonical_json(rec))
    units = {"evaluated": make_unit(prepared, base / "units" / "1102-a0-e1-a1", SEEDS["evaluated"], True),
             "source": make_unit(prepared, base / "units" / "1101-a0-e1-a1", SEEDS["source"], True),
             "regen": make_unit(prepared, base / "regen" / "1101-a0-regen-a1", SEEDS["regen"], False)}
    oext = {"128": ofx.inputs(base / "oext-128", branch="128", cut=CUT, dev=2),
            "full": ofx.inputs(base / "oext-full", branch="full", cut=CUT, dev=2),
            "full_reason": ofx.inputs(base / "oext-full-reason", branch="full", cut=CUT, dev=2,
                                      full_reason="W1-18 could not run (fixture)"),
            "pending": ofx.inputs(base / "oext-pending", branch=oe.PENDING, cut=CUT, dev=2)}
    return SimpleNamespace(base=base, prepared=prepared, manifest=manifest, recipe=rec, recipe_file=recipe_file,
                           units=units, oext=oext)


def settings_for(world, branch: str, **changes):
    return ou.settings_from_doc(settings_doc(world.manifest, world.oext[branch].settings.sha256, world.recipe,
                                             **changes))


def argv(world, command: str, branch: str, out: Path, *, run: str | Path | None = None, untuned: bool = False,
         checkpoint: str | None = "e1", source: Path | None = None, recipe_file: Path | None = None,
         prepared: Path | None = None, w1_18: bool = True) -> list[str]:
    inp = world.oext[branch]
    args = [command]
    if untuned:
        args.append("--untuned")
    if run is not None:
        args += ["--run", str(run)]
        if checkpoint is not None:
            args += ["--checkpoint", checkpoint]
    args += ["--prepared", str(prepared or world.prepared), "--recipe", str(recipe_file or world.recipe_file),
             "--oext-bank", str(inp.bank), "--oext-record", str(inp.record)]
    if w1_18 and inp.w1_18 is not None:
        args += ["--w1-18-record", str(inp.w1_18)]
    if source is not None:
        args += ["--dev100-source", str(source)]
    return args + ["--out", str(out)]


def call(world, args: list[str], branch: str, *, settings=None, oext_settings=None, **loader_options):
    """main() with the fixture loaders, settings and O-ext settings: (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ou.main(args, loaders=loaders(**loader_options),
                       settings=settings if settings is not None else settings_for(world, branch),
                       oext_settings=oext_settings if oext_settings is not None else world.oext[branch].settings)
    return code, out.getvalue(), err.getvalue()


def reseal(unit: Path) -> None:
    """Re-write a unit's COMPLETE.json file list (and job hash) after a test changed one of its files."""
    from experiments.safety_selection.ledger import artifact_hashes

    marker = json.loads((unit / "COMPLETE.json").read_bytes())
    marker.update(job_sha256=sha256_file(unit / "job.json"), files=artifact_hashes(unit))
    (unit / "COMPLETE.json").write_bytes(canonical_json(marker))


# ----- B15's contract ----------------------------------------------------------------------------------------------

# A frozen copy of runkit/stage1-olmo/setup/job_runner_stage1.py oext_unit_contract (lines 151-170 at ws-b15r2), the
# CLI B15 calls; a test checks the kit's own function against it whenever the kit is reachable.
CONTRACT_SOURCE = '''def oext_unit_contract():
    """The CLI the kit calls for the O-ext pass on an engine unit's state (OEXT_UNIT_SCRIPT is not built; whoever
    builds it must accept exactly this; the kit's tests parse every O-ext step with this parser)."""
    import argparse
    ap = argparse.ArgumentParser(prog=OEXT_UNIT_SCRIPT)
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("run", "transfer"):
        p = sub.add_parser(name)
        state = p.add_mutually_exclusive_group(required=True)
        state.add_argument("--run", help="an engine unit folder (its states/CHECKPOINT state)")
        state.add_argument("--untuned", action="store_true", help="theta0: no adapter")
        p.add_argument("--checkpoint", choices=("e1",))
        p.add_argument("--prepared", required=True)
        p.add_argument("--recipe", required=True)
        p.add_argument("--oext-bank", required=True)
        p.add_argument("--oext-record", required=True)
        p.add_argument("--w1-18-record")
        p.add_argument("--dev100-source", help="Branch 128, a regenerated unit: the source unit (LN-19, §8 Q15)")
        p.add_argument("--out", required=True)
    return ap'''
CONTRACT_SHA256 = hashlib.sha256(CONTRACT_SOURCE.encode("utf-8")).hexdigest()
KIT_RUNNER_CANDIDATES = (ENGINE_ROOT / "runkit" / "stage1-olmo" / "setup" / "job_runner_stage1.py",
                         ENGINE_ROOT.parent / "ws-b15r2" / "runkit" / "stage1-olmo" / "setup" / "job_runner_stage1.py")


def kit_runner() -> Path | None:
    return next((p for p in KIT_RUNNER_CANDIDATES if p.is_file()), None)


def kit_contract_source(path: Path) -> tuple[str, str]:
    """(the kit's oext_unit_contract source, the kit's OEXT_UNIT_SCRIPT literal), read with ast (nothing runs)."""
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "oext_unit_contract")
    script = next(n.value.value for n in tree.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "OEXT_UNIT_SCRIPT" for t in n.targets))
    return ast.get_source_segment(text, func), script


def contract_parser(source: str = CONTRACT_SOURCE, script: str = "scripts/stage1_s1/oext_unit.py"):
    namespace = {"OEXT_UNIT_SCRIPT": script}
    exec(compile(source, "oext_unit_contract", "exec"), namespace)  # noqa: S102 - the frozen copy of B15's parser
    return namespace["oext_unit_contract"]()


def parser_shape(ap) -> dict:
    """Every subcommand's options: (option strings, dest, required, choices, action kind, default) and the
    mutually exclusive groups (dests, required)."""
    import argparse

    sub = next(a for a in ap._actions if isinstance(a, argparse._SubParsersAction))
    out = {"dest": sub.dest, "required": sub.required}
    for name, p in sorted(sub.choices.items()):
        actions = sorted((tuple(a.option_strings), a.dest, bool(a.required),
                          None if a.choices is None else tuple(a.choices), type(a).__name__, a.default)
                         for a in p._actions if not isinstance(a, argparse._HelpAction))
        groups = sorted((tuple(sorted(a.dest for a in g._group_actions)), bool(g.required))
                        for g in p._mutually_exclusive_groups)
        out[name] = {"actions": actions, "groups": groups}
    return out
