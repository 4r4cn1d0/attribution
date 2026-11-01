"""B17 test support: the job module, imported by this package folder's own name, and ENGINEERING FIXTURES.

In the workspace the package folder is scripts/stage1_s1, so the module is scripts.stage1_s1.lean_eval_job. In the
mutation mirror (mutation/b17_mirror.py) the same files lie in scripts/stage1, so the tests import the copy that T1's
runner mutates. The module is imported before the engine's fixtures, because ss_fixtures puts the workspace first on
sys.path. Nothing here reads real data: the prepared sets are the engine's synthetic fixtures (ss_fixtures), and the
model and guard are the engine's tiny random fixture models. None of these numbers is a scientific result.
"""

from __future__ import annotations

import copy
import importlib
import json
import sys
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1]
REPO = PKG_DIR.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
PACKAGE = f"scripts.{PKG_DIR.name}"
IN_MIRROR = PKG_DIR.name == "stage1"
lej = importlib.import_module(f"{PACKAGE}.lean_eval_job")

from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from experiments.safety_selection.planning import make_job  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

ENGINE_TESTS = Path(importlib.import_module("experiments.safety_selection").__file__).resolve().parent / "tests"
if str(ENGINE_TESTS) not in sys.path:
    sys.path.append(str(ENGINE_TESTS))
import ss_fixtures as fx  # noqa: E402

SAMPLES = {"count": 3, "temperature": 0.7, "top_p": 1.0}
EXPECTED = {"harm": 2, "overrefusal": 2, "task_rows": 16}      # the fixture dev bank and task rows
SEED = 1101


def recipe(**changes) -> dict:
    """The engine's fixture recipe with sampled harm answers and the stage-1 recipe's guard_over_limit."""
    return fx.recipe(**{"generation.harm_samples": dict(SAMPLES), "generation.guard_over_limit": "unscored",
                        **changes})


def without(doc: dict, dotted: str) -> dict:
    out = copy.deepcopy(doc)
    *parents, last = dotted.split(".")
    node = out
    for key in parents:
        node = node[key]
    del node[last]
    return out


def prepared_dirs(base: Path) -> tuple[Path, str]:
    """(the kill-test-format prepared folder, its manifest SHA-256): the engine's synthetic fixtures."""
    bank_dir, _ = fx.prepare_dir_v3(base / "prepared-v3")
    return fx.prepare_task_dir(base / "prepared-kt", bank_dir)


def settings_doc(recipes: list[dict] | None = None, **changes) -> dict:
    """The committed settings with the fixture's bank counts and recipes; ``changes`` use dotted keys."""
    doc = s1.strict_json(lej.SETTINGS_PATH.read_bytes())
    doc["lean"]["expected_counts"] = dict(EXPECTED)
    # the C-lean (dev 100) form of the earlier tests (the LN-07 fallback status); the O-ext tests set oext_pinned
    doc["lean"]["overrefusal_bank"]["status"] = "dev100_recipe_cap"
    doc["job"]["allowed_recipes"] = {f"fixture-{k}": config_sha256(r) for k, r in enumerate(recipes or [recipe()])}
    for dotted, value in changes.items():
        *parents, last = dotted.split(".")
        node = doc
        for key in parents:
            node = node[key]
        node[last] = value
    return doc


def write_settings(path: Path, doc: dict) -> tuple[dict, str]:
    """Writes the settings document and loads it back through the module's own loader."""
    data = canonical_json(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return lej.load_lean_settings(path, sha256_bytes(data))


def write_recipe(path: Path, rec: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(rec))
    return path


def write_job(path: Path, prepared: Path, rec: dict, *, arm: str = "a0", edit: Path | None = None,
              pin_code: bool = True, **fields) -> dict:
    values = {"wall_limit_seconds": None, "split": "dev", "arm": arm, "seed": SEED, "role": "development",
              "target_checkpoint": "e1", "evaluate_bank": None, "resume_from": None, "replicate_of": None}
    values.update(fields)
    if edit is not None:
        values["edit"] = str(edit)
    path.parent.mkdir(parents=True, exist_ok=True)
    return make_job("run-one", prepared_dir=prepared, recipe=rec, pin_code=pin_code, out=path, **values)


def write_raw_job(path: Path, job: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(job))
    return path


def remove_edit(base: Path, prepared_dir: Path, sha: str, rows: int = 4) -> tuple[str, Path, str]:
    """An R-like remove edit of the first ``rows`` training rows: (arm, file, SHA-256)."""
    from experiments.safety_selection import headroom as hr
    from experiments.safety_selection.edits import arm_of
    from experiments.safety_selection.prepare import load_prepared

    prepared = load_prepared(prepared_dir, sha)
    data, _ = hr.edit_document("fixture remove", "remove", prepared, {"test": fx.FIXTURE},
                               remove=sorted(prepared.train_rows)[:rows])
    path = base / "edits" / "remove.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return arm_of(data), path, sha256_bytes(data)


def session(rec: dict | None = None, **options) -> runner.Session:
    """A new session stands for a new process (a cold start)."""
    return runner.Session(rec or recipe(), fx.fixture_loaders(**options))


class Env:
    """One test's files: the shared prepared fixture, a recipe, settings and a job, and helpers to run the job."""

    def __init__(self, base: Path, prepared: tuple[Path, str], rec: dict | None = None,
                 recipes: list[dict] | None = None, **settings_changes) -> None:
        self.base = base
        self.prepared_dir, self.manifest_sha256 = prepared
        self.recipe = rec or recipe()
        self.recipe_path = write_recipe(base / "recipe.json", self.recipe)
        self.settings, self.settings_sha256 = write_settings(
            base / "settings" / "lean_eval_job.json", settings_doc(recipes or [self.recipe], **settings_changes))
        self.settings_path = base / "settings" / "lean_eval_job.json"
        self.jobs = 0

    def job(self, **fields) -> Path:
        self.jobs += 1
        path = self.base / f"job-{self.jobs}.json"
        write_job(path, self.prepared_dir, self.recipe, **fields)
        return path

    def plan(self, job: Path | None = None, out: Path | None = None, expected: str | None = None):
        return lej.prepare_c0_job(job or self.job(), prepared_dir=self.prepared_dir, recipe_path=self.recipe_path,
                                  out_dir=out or self.base / "out", settings=self.settings,
                                  settings_sha256=self.settings_sha256, expected_fingerprint=expected)

    def run(self, job: Path | None = None, out: Path | None = None, expected: str | None = None,
            loaders: dict | None = None, **options) -> tuple[object, dict]:
        plan = self.plan(job, out, expected)
        record = lej.execute_c0_job(plan, session(self.recipe, **(loaders or {})), **options)
        return plan, record


class Failed:
    """A module fixture's exception, kept: unpacking it in a test body re-raises the exception there, so a mutant that
    breaks the shared run is a test FAILURE (a kill), not a fixture error (an invalid run). B14's convention."""

    def __init__(self, exc: BaseException) -> None:
        self.exc = exc

    def __iter__(self):
        raise self.exc


def kept(make):
    """make() or its exception kept as Failed (for module-scoped fixtures)."""
    try:
        return make()
    except Exception as exc:  # noqa: BLE001 - re-raised in each test body that unpacks it
        return Failed(exc)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def walk_keys(obj: object) -> set[str]:
    """Every key of every object nested in ``obj``."""
    keys: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            keys.add(key)
            keys |= walk_keys(value)
    elif isinstance(obj, list):
        for value in obj:
            keys |= walk_keys(value)
    return keys
