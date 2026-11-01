"""ENGINEERING FIXTURES for the B10 tests (synthetic only; nothing is downloaded and no real record is read).

They reuse the engine's own fixtures (experiments/safety_selection/tests/ss_fixtures.py): synthetic sources, the
byte-level tokenizer, the tiny random Qwen2 policy with LoRA, the scripted guard and the injected loaders. On top:
a stage-1-like prepared set (a headroom-v2 bank set, then Dolly-format task units with task rows), Gate-A-like a0
units (a run-one to e1 with its evaluation, in Gate A's two forms), and B10 settings whose pins are the fixture's.
None of these numbers is a scientific result."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import experiments.safety_selection as _engine

ENGINE_TESTS = Path(_engine.__file__).resolve().parent / "tests"
if str(ENGINE_TESTS) not in sys.path:
    sys.path.insert(0, str(ENGINE_TESTS))

import ss_fixtures as fx  # noqa: E402

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256, training_identity  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402

SAMPLES = {"count": 3, "temperature": 0.7, "top_p": 1.0}
EVAL_FILES = ("generations.jsonl", "samples.jsonl", "guard.jsonl", "guard_samples.jsonl", "harm_scores.jsonl",
              "harm_prompts.jsonl", "arc_utility.jsonl", "query_loss.jsonl")
PREFIX_TEXT = "FIXTURE SAFETY PREFIX: answer carefully."            # a fixture string, not a real instruction
TRANSFORM_MODULE = "scripts/stage1_s1/tests/b10_transform_fixture.py"


def recipe(**changes) -> dict:
    return fx.recipe(**{"generation.harm_samples": dict(SAMPLES), **changes})


def prepared(base: Path) -> tuple[Path, str]:
    """(folder, manifest SHA-256) of the fixture task set: Dolly-format units, task rows, the v3 banks."""
    bank_dir, _ = fx.prepare_dir_v3(base / "prepared-v3")
    return fx.prepare_task_dir(base / "prepared-kt", bank_dir)


def session(recipe_: dict | None = None, **loader_options):
    """A new Session (stands for a new process) with the engine's fixture loaders."""
    from experiments.safety_selection import runner

    return runner.Session(recipe_ or recipe(), fx.fixture_loaders(**loader_options))


def _job(prepared_dir: Path, recipe_: dict, out: Path, **fields) -> dict:
    from experiments.safety_selection.planning import make_job

    return make_job("run-one", prepared_dir=prepared_dir, recipe=recipe_, pin_code=False, out=out,
                    wall_limit_seconds=None, split="dev", arm="a0", role="development", replicate_of=None, **fields)


def gate_a_one_job(prepared_dir: Path, out: Path, seed: int, recipe_: dict | None = None) -> Path:
    """Gate A's 1102/1103 form: one run-one from init to e1 that evaluates e1."""
    from experiments.safety_selection import runner

    recipe_ = recipe_ or recipe()
    job = _job(prepared_dir, recipe_, out.parent / f"{out.name}-job.json", seed=seed, target_checkpoint="e1",
               evaluate_bank="dev", resume_from=None)
    runner.run_one(job, prepared_dir=prepared_dir, out_dir=out, session=session(recipe_))
    return out


def gate_a_resumed(prepared_dir: Path, out: Path, seed: int, recipe_: dict | None = None) -> tuple[Path, Path]:
    """Gate A's 1101 form: the untuned init unit (evaluated), then the e1 unit resumed from it (evaluated)."""
    from experiments.safety_selection import runner

    recipe_ = recipe_ or recipe()
    init = out.parent / f"{out.name}-init"
    s = session(recipe_)
    runner.run_one(_job(prepared_dir, recipe_, out.parent / f"{init.name}-job.json", seed=seed,
                        target_checkpoint="init", evaluate_bank="dev", resume_from=None),
                   prepared_dir=prepared_dir, out_dir=init, session=s)
    runner.run_one(_job(prepared_dir, recipe_, out.parent / f"{out.name}-job.json", seed=seed,
                        target_checkpoint="e1", evaluate_bank="dev", resume_from=str(init)),
                   prepared_dir=prepared_dir, out_dir=out, session=s)
    return out, init


def set_dotted(doc: dict, dotted: str, value) -> None:
    node = doc
    *parents, last = dotted.split(".")
    for key in parents:
        node = node[key]
    node[last] = value


def real_doc() -> dict:
    return s1.strict_json(ea.SETTINGS_PATH.read_bytes())


def fixture_doc(manifest_sha256: str, units: dict[int, Path], untuned: Path | None = None,
                recipe_: dict | None = None, **changes) -> dict:
    """The real settings with the fixture's pins: recipe, manifest, Gate-A-like reference units (their COMPLETE.json
    SHA-256 and fingerprints), the untuned unit and the fixture's sampled-answer count; then ``changes``."""
    recipe_ = recipe_ or recipe()
    doc = copy.deepcopy(real_doc())
    doc["recipe"].update(config_sha256=config_sha256(recipe_), training_identity=training_identity(recipe_))
    doc["prepared"]["manifest_sha256"] = manifest_sha256
    doc["reference_units"] = {}
    for seed, unit in units.items():
        marker = json.loads((unit / "COMPLETE.json").read_bytes())
        doc["reference_units"][str(seed)] = {
            "complete_sha256": sha256_file(unit / "COMPLETE.json"),
            "fingerprint_prefixes": {"e1": marker["checkpoints"]["e1"]["adapter_fingerprint"][:16],
                                     "q": marker["checkpoints"]["q"]["adapter_fingerprint"]},
            "role": "ENGINEERING FIXTURE Gate-A-like unit", "unit": f"fixture/{unit.name}"}
    first = min(units)
    doc["certification"]["seed"] = first
    doc["certification"]["expected_sampled_answers"] = 2 * SAMPLES["count"]        # 2 harm prompts in the fixture
    doc["untuned_unit"]["seed"] = first
    doc["overrefusal_bank"]["status"] = "dev100_recipe_cap"        # the references run (tests of "open" set it back)
    if untuned is not None:
        doc["untuned_unit"].update(complete_sha256=sha256_file(untuned / "COMPLETE.json"),
                                   unit=f"fixture/{untuned.name}")
    for dotted, value in changes.items():
        set_dotted(doc, dotted.replace("__", "."), value)
    return doc


def fixture_settings(*args, **kwargs) -> ea.Settings:
    return ea.settings_from_doc(fixture_doc(*args, **kwargs))


def certification(prepared_dir: Path, unit: Path, settings: ea.Settings, folder: Path,
                  source: Path | None = None) -> tuple[Path, str]:
    """The certification report for ``settings`` (path, SHA-256): the certification seed's a0 state (``source``, or
    a new regeneration), its certify evaluation and the comparison with the Gate-A-like ``unit``. It passes on correct
    code. It never asserts: under a mutant that breaks the certify path it writes the failing report, so the tests
    that use it FAIL (a kill) instead of erroring in the fixture (an invalid run)."""
    seed = settings.doc["certification"]["seed"]
    reference = unit / "COMPLETE.json"
    if source is None:
        ea.regenerate(prepared_dir=prepared_dir, seed=seed, reference_path=reference, out_root=folder / "cert-regen",
                      session=session(), settings=settings)
        source = folder / "cert-regen" / "run"
    ctx = ea.preflight(prepared_dir=prepared_dir, source_run=source, reference_path=reference, recipe=recipe(),
                       settings=settings, plan=ea.make_plan(settings, "certify"))
    ea.evaluate(ctx, out_dir=folder / "cert-unit", session=session())
    report = ea.compare_certification(folder / "cert-unit", reference, eval_dir(unit), settings)
    path = folder / "certification.json"
    path.write_bytes(canonical_json(report))
    return path, sha256_file(path)


def cert_args(cert: tuple[Path, str]) -> list:
    return ["--certification-report", cert[0], "--certification-report-sha256", cert[1]]


def reseal(unit: Path) -> None:
    """Re-write a unit's COMPLETE.json file list (and job hash) after a test changed one of its files: a tampered
    but self-consistent unit, so only the rule under test can refuse it."""
    from experiments.safety_selection.ledger import artifact_hashes

    marker = json.loads((unit / "COMPLETE.json").read_bytes())
    marker.update(job_sha256=sha256_file(unit / "job.json"), files=artifact_hashes(unit))
    (unit / "COMPLETE.json").write_bytes(canonical_json(marker))


def write_prefix(folder: Path, text: str = PREFIX_TEXT) -> tuple[Path, str]:
    path = folder / "prefix.txt"
    path.write_bytes(text.encode("utf-8"))
    return path, sha256_bytes(text.encode("utf-8"))


def transform_entry(function: str, *, kind: str = "callable", require_a: bool = False, module: str = TRANSFORM_MODULE,
                    record_keys: dict | None = None) -> dict:
    return {"kind": kind, "module": module, "module_sha256": sha256_file(ea.REPO / module),
            "function": function if kind == "callable" else None, "settings": None,
            "record_keys": record_keys if kind == "file" else None, "require_lora_a_unchanged": require_a,
            "role": "ENGINEERING FIXTURE transform"}


def recording_loaders(**options):
    """The fixture loaders, with every guard input decoded and kept (to show what Qwen3Guard is shown)."""
    loaders = fx.fixture_loaders(**options)
    seen: list[str] = []
    original = loaders.guard

    def guard(recipe_, ledger, device):
        scorer = original(recipe_, ledger, device)
        inner = scorer.generate

        def generate(prompts, check=None):
            seen.extend(scorer.tokenizer.decode(ids) for ids in prompts)
            return inner(prompts, check)

        scorer.generate = generate
        return scorer

    loaders.guard = guard
    return loaders, seen


def eval_dir(unit: Path, checkpoint: str = "e1") -> Path:
    return Path(unit) / "eval" / checkpoint


def summary_without_timing(unit: Path, checkpoint: str = "e1") -> dict:
    summary = json.loads((eval_dir(unit, checkpoint) / "summary.json").read_bytes())
    summary["query_loss"].pop("seconds")
    summary.pop("checkpoint")
    return summary


def harm_prompts(prepared_dir: Path) -> list[str]:
    from experiments.safety_selection.prepare import load_prepared

    bank = load_prepared(prepared_dir, banks=("dev",)).banks["dev"]
    return [i["prompt"] for i in bank if i["kind"] in ("harm", "overrefusal")]


def namespace(**kwargs) -> SimpleNamespace:
    return SimpleNamespace(**kwargs)


def canonical(doc) -> bytes:
    return canonical_json(doc)
