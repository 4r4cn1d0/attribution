"""B14 part 3: the overlap report's inputs file (overlap_inputs.py) and its second computation
(overlap_inputs_check.py), on synthetic kits only. A small kit of B14-shaped units (b14_fixtures) in the kit's layout,
with the distractors the real plan.json holds (deferred jobs, regenerations, a reference unit, a host that is not
done), is read end to end by the report; on the builder's synthetic kit (reading_input/tests/synth_kit.py, used
read-only) the units named must be the builder's own. One refusal test per check, and one planted difference per
comparison."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

import b14_fixtures as bf

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1 import s1common as s1
from scripts.stage1_s1 import overlap_inputs as oi
from scripts.stage1_s1 import overlap_inputs_check as oc
from scripts.stage1_s1 import overlap_strata as st

PKG = Path(st.__file__).resolve().parent             # the package under test (a mutation copy tests itself)
if str(PKG / "reading_input" / "tests") not in sys.path:
    sys.path.insert(0, str(PKG / "reading_input" / "tests"))
import synth_kit as sk  # noqa: E402

from scripts.stage1_s1.reading_input.build import build as builder  # noqa: E402
from scripts.stage1_s1.reading_input.sources import load_rules as builder_rules  # noqa: E402

SEEDS = list(range(1102, 1108))                      # d1_plan_a: a0 and S1, S3, S4 at 1102-1107
SETS = ("S1", "S3", "S4")
EDITS = {"S1": "a" * 64, "S3": "c" * 64, "S4": "d" * 64}
PIDS = [f"p-{i:016x}" for i in range(8)]
ENGINE_Y = "34bfd28879fdefc5d6605cb73a707d1edd2ec5d102b4b86c0026bc6ac36969f6"
CONFIGS = "experiments/safety_selection/configs/"
RECIPE_S_PATH = CONFIGS + "study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json"
RECIPES = {CONFIGS + "study-kt-olmo2-1b-r64-b-mb4-20261008.json": {"config_sha256": bf.REC},
           RECIPE_S_PATH: {"config_sha256": bf.RECIPE_S},
           CONFIGS + "study-kt-olmo2-1b-r64-g-mb4-20261008.json": {"config_sha256": bf.RECIPE_G},
           CONFIGS + "study-kt-olmo2-1b-r64-bq-mb4-20261022.json": {"config_sha256": bf.RECIPE_BQI, "engine": "Y"}}
ORIGIN_HOSTS = {"a-2", "a-3", "a-4", "b-5", "b-6", "b-7"}   # one launch host per seed


def unsafe(seed: int) -> dict:
    return {p: (i + seed) % 4 % 3 for i, p in enumerate(PIDS)}


@dataclass
class World:
    """One synthetic kit: repo/ (the rules module and repo/tmp, B14's data root, which holds Gate A's pinned units and
    the kit stage1-olmo/), the strata record and, per cell, the expected (path, COMPLETE.json, job.json, origin)."""
    root: Path
    strata_sha: str = ""
    expect: dict = field(default_factory=dict)

    repo = property(lambda self: self.root / "repo")
    data = property(lambda self: self.root / "repo" / "tmp")
    kit = property(lambda self: self.root / "repo" / "tmp" / "stage1-olmo")
    rules = property(lambda self: self.root / "repo" / "rules.py")
    strata = property(lambda self: self.root / "strata.json")

    def plan(self) -> dict:
        return json.loads((self.kit / "plan.json").read_bytes())

    def save(self, plan: dict) -> None:
        (self.kit / "plan.json").write_text(json.dumps(plan, indent=1, sort_keys=True) + "\n")

    def args(self, out: Path, **change) -> list[str]:
        given = {"kit": self.kit, "strata": self.strata, "strata-sha256": self.strata_sha, "out": out,
                 "rules": self.rules, "repo": self.repo, "data-root": self.data, **change}
        return [x for key, value in given.items() for x in (f"--{key}", str(value))]

    def check_args(self, file: Path, **change) -> list[str]:
        given = {"file": file, "kit": self.kit, "strata": self.strata, "rules": self.rules, "repo": self.repo,
                 "data-root": self.data, "settings": st.SETTINGS_PATH, **change}
        return [x for key, value in given.items() for x in (f"--{key}", str(value))]

    def copy(self, root: Path) -> "World":
        shutil.copytree(self.root, root)
        return World(root, self.strata_sha, dict(self.expect))


def pin(name: str, arm: str, seed: int, target: str, rel: str, unit: dict) -> dict:
    return {"name": name, "arm": arm, "seed": seed, "target": target, "path": f"tmp/{rel}",
            "complete_sha256": unit["complete_sha256"], "job_sha256": unit["job_sha256"]}


def kit_job(kind: str, arm: str, seed: int, unit: dict | None, rel: str | None, **extra) -> dict:
    edit = {"path": f"edits/{arm}.edit.json", "sha256": EDITS[arm], "source": "synthetic"} if arm in EDITS else None
    return {"kind": kind, "arm": arm, "seed": seed, "engine": "X", "recipe": "S", "status": "complete", "unit": rel,
            "complete_sha256": unit["complete_sha256"] if unit else None, "edit": edit, "outputs": {}, "reason": None,
            **extra}


def make_world(root: Path) -> World:
    w = World(Path(root))
    settings, digest = bf.strata_settings()
    ranks = {p: (i + 1) / (len(PIDS) + 1) for i, p in enumerate(PIDS)}
    sim = bf.similarity_record({m: ranks for m in SETS}, EDITS)
    data = st.strata(sim, sha256_bytes(sim), settings, digest)
    w.root.mkdir(parents=True)
    w.strata.write_bytes(data)
    w.strata_sha = sha256_bytes(data)
    pins = []
    for j in (1101, 1102, 1103):                     # Gate A's a0 units (Gate A's engine, REC): block A's pins
        rel = f"gate-a-{j}/retrieved/olmo2-1b-{j}/tree/round1/{j}-a0-e1-a1"
        u = bf.write_unit(w.data, rel, arm="a0", seed=j, unsafe=unsafe(j), code=bf.GATE_A_CODE, recipe=bf.REC)
        pins.append(pin(f"a0 {j} (Gate A)", "a0", j, "e1", rel, u))
        if j in SEEDS:
            w.expect[("a0", j)] = (rel, u["complete_sha256"], u["job_sha256"], {"pin": f"a0 {j} (Gate A)"})
    rel = "gate-a-1101/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1"     # theta0 (arm a0, 1101, init)
    u = bf.write_unit(w.data, rel, arm="a0", seed=1101, unsafe=unsafe(1101), code=bf.GATE_A_CODE, recipe=bf.REC,
                      checkpoint="init")
    pins.append(pin("theta0 (untuned, Gate A)", "a0", 1101, "init", rel, u))
    rel = "gate-b/retrieved/w0a-1/tree/round1/1102-edit-r2-e1-a1"              # an R pin at a seed B14 reads
    u = bf.write_unit(w.data, rel, arm="edit-" + "b" * 64, seed=1102, unsafe=unsafe(1102))
    pins.append(pin("R 1102 (wave 0a, R_2)", "edit-" + "b" * 64, 1102, "e1", rel, u))
    sk.rules_module(w.rules, pins)
    plan = {"name": "stage1-olmo", "records": {"plan_ab": {"code": "A"}, "oext_fallback": None},
            "seals": {b: {"path": f"seals/block-{b}.json", "sha256": "5" * 64, "files": 1} for b in ("A", "B")},
            "recipes": RECIPES, "engines": {"X": bf.ENGINE_X, "Y": ENGINE_Y}, "deferrals": [], "hosts": {}}
    for j in SEEDS:                                  # one launch host per seed: blocks A (1102-1104) and B (1105-1107)
        block = "A" if j <= 1104 else "B"
        host = f"{block.lower()}-{j - 1100}"
        jobs = [kit_job("arm", "A1", j, None, f"round1/{j}-edit-a1-e1-a1")]           # an arm B14 does not read
        for arm in (*SETS, *(("a0",) if j >= 1104 else ())):
            engine_arm = "a0" if arm == "a0" else "edit-" + EDITS[arm]
            rel = f"round1/{j}-{engine_arm}-e1-a1"
            u = bf.write_unit(w.kit / "retrieved" / host / "tree", rel, arm=engine_arm, seed=j, unsafe=unsafe(j))
            extra = {"deferred_from": "a-9"} if (arm, j) == ("S3", 1102) else {}
            jobs.append(kit_job("a0_arm" if arm == "a0" else "arm", arm, j, u, rel, **extra))
            w.expect[(arm, j)] = (f"stage1-olmo/retrieved/{host}/tree/{rel}", u["complete_sha256"], u["job_sha256"],
                                  {"block": block, "host": host, "job": len(jobs) - 1})
        plan["hosts"][host] = {"block": block, "done": True, "jobs": jobs}
    # the deferral's source host (not done; its copy of S3 1102 never started), as plan.json keeps it
    plan["hosts"]["a-9"] = {"block": "A", "done": False,
                            "jobs": [{**kit_job("arm", "S3", 1102, None, None), "status": "not_started"}]}
    plan["deferrals"].append({"from": "a-9", "to": "a-2", "from_indices": [0], "to_indices": [3]})
    # block A's LN-12 pod: a0 1102's regeneration and O-only pass, and a retrain recorded complete but not pulled
    plan["hosts"]["a-1"] = {"block": "A", "done": True, "jobs": [
        {**kit_job("regenerate", "a0", 1102, None, "round1/1102-a0-regen-a1"), "complete_sha256": "1" * 64},
        {**kit_job("o_only", "a0", 1102, None, None), "regen_source": 0},
        {**kit_job("retrain", "a0", 1102, None, "rescore/1102-a0-retrain-a1"), "complete_sha256": "9" * 64,
         "pulled": False}]}
    # block B's recipe-G reference at 1105: engine arm a0, recipe G, kind ref_train (never an a0 unit)
    rel = "round1/1105-a0-e1-a1"
    u = bf.write_unit(w.kit / "retrieved" / "b-ref-g" / "tree", rel, arm="a0", seed=1105, unsafe=unsafe(1105),
                      recipe=bf.RECIPE_G)
    plan["hosts"]["b-ref-g"] = {"block": "B", "done": True,
                                "jobs": [{**kit_job("ref_train", "G", 1105, u, rel), "recipe": "G"}]}
    plan["hosts"]["cert-1"] = {"block": "cert", "done": True, "jobs": [kit_job("cert_c1", "a0", 1104, None, None)]}
    # a re-run of S1 1106 recorded complete but not pulled (its unpulled decision recorded): never an input
    plan["hosts"]["b-8"] = {"block": "B", "done": True, "jobs": [
        {**kit_job("arm", "S1", 1106, None, "round1/1106-edit-s1-e1-a2"), "complete_sha256": "4" * 64,
         "pulled": False, "unpulled_decision_sha256": "3" * 64}]}
    w.save(plan)
    return w


@pytest.fixture(scope="module")
def world(tmp_path_factory) -> World | str:
    """The world, or the text of why it could not be built: a mutant that makes the build refuse then fails each test
    that reads the fixture (through need), never its setup."""
    try:
        return make_world(tmp_path_factory.mktemp("b14-inputs") / "w")
    except Exception as exc:  # noqa: BLE001 - reported by each test that reads the fixture, as a failure
        return f"building the synthetic world raised {type(exc).__name__}: {exc}"


def need(built):
    """The built world (or synthetic kit), or a test failure naming why there is none."""
    assert not isinstance(built, str), built
    return built


def written(w: World, tmp_path: Path, capsys=None) -> tuple[bytes, dict]:
    out = tmp_path / "out"
    assert oi.main(w.args(out)) == 0
    data = (out / oi.OUTPUT).read_bytes()
    return data, json.loads(data)


def expected_document(w: World) -> dict:
    """The file by hand: the cells' ground truth from the world's construction."""
    units: dict = {}
    origins: dict = {}
    for (name, seed), (path, complete, job, origin) in w.expect.items():
        units.setdefault(name, {})[str(seed)] = {"path": path, "complete_sha256": complete, "job_sha256": job}
        origins.setdefault(name, {})[str(seed)] = origin
    return {"kind": "stage1 overlap report inputs", "version": 1, "strata_sha256": w.strata_sha,
            "seed_plan": "d1_plan_a", "units": units,
            "sources": {"reading": "plan_a", "plan_code": "A",
                        "plan_json_sha256": sha256_bytes((w.kit / "plan.json").read_bytes()),
                        "rules_sha256": sha256_bytes(w.rules.read_bytes()), "settings_sha256": st.SETTINGS_SHA256,
                        "origins": origins}}


# ----- the file -------------------------------------------------------------------------------------------------------


def test_the_file_is_the_hand_built_document_in_canonical_json(world, tmp_path):
    world = need(world)
    data, doc = written(world, tmp_path)
    assert data == canonical_json(expected_document(world))
    assert sorted(doc["units"]) == ["S1", "S3", "S4", "a0"]
    assert all(sorted(per) == [str(j) for j in SEEDS] for per in doc["units"].values())
    hosts = {o.get("host") for per in doc["sources"]["origins"].values() for o in per.values()}
    assert hosts - {None} == ORIGIN_HOSTS                 # never a-1 (LN-12), a-9 (not done), b-ref-g or cert-1
    assert doc["sources"]["origins"]["S3"]["1102"] == {"block": "A", "host": "a-2", "job": 2}   # the deferred job


def test_the_report_reads_exactly_the_units_named_gate_a_rec_and_kit_recipe_s(world, tmp_path):
    """End to end with D-6: a0 1102-1103 are Gate A's units (REC), every other unit a kit unit (recipe S)."""
    world = need(world)
    _, doc = written(world, tmp_path)
    settings, digest = bf.strata_settings()
    report = s1.strict_json(st.report(world.strata.read_bytes(), doc, settings, digest, world.data))
    named = {(n, s): (u["complete_sha256"], u["job_sha256"]) for n, per in doc["units"].items() for s, u in per.items()}
    read = {(n, s): (u["complete_sha256"], u["job_sha256"]) for n, per in report["units"].items()
            for s, u in per.items()}
    assert read == named and len(named) == 24
    assert report["units"]["a0"]["1102"]["code_sha256"] == bf.GATE_A_CODE
    assert report["units"]["a0"]["1104"]["code_sha256"] == bf.ENGINE_X
    assert report["seed_plan"] == "d1_plan_a" and report["strata_sha256"] == world.strata_sha


def test_the_command_writes_once_and_prints_hashes_and_origins_only(world, tmp_path, capsys):
    world = need(world)
    out = tmp_path / "out"
    assert oi.main(world.args(out)) == 0
    data = (out / oi.OUTPUT).read_bytes()
    printed = capsys.readouterr()
    assert sha256_bytes(data) in printed.out and "a0: 6 units; pinned at 1102, 1103" in printed.out
    assert printed.err == "" and not [t for t in bf.SENTINELS if t in printed.out or t.encode() in data]
    assert oi.main(world.args(out)) == 2 and (out / oi.OUTPUT).read_bytes() == data      # never overwrites
    assert "exists and is not empty" in capsys.readouterr().err
    proc = subprocess.run([sys.executable, "-B", str(PKG / "overlap_inputs.py"), *world.args(tmp_path / "out2")],
                          capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "out2" / oi.OUTPUT).read_bytes() == data


def test_the_writer_hashes_unit_files_and_never_parses_them(world, tmp_path):
    """A unit's COMPLETE.json and job.json replaced by bytes that are not JSON (plan.json re-pinned to the new
    COMPLETE.json): the writer still writes, naming their SHA-256 (the report, not the writer, parses them)."""
    world = need(world)
    w = world.copy(tmp_path / "w")
    plan = w.plan()
    host, _, job = sk.find_job(plan, "arm", "S4", 1106)
    folder = w.kit / "retrieved" / host / "tree" / job["unit"]
    (folder / "COMPLETE.json").write_bytes(b"\x00not json {")
    (folder / "job.json").write_bytes(b"\xff\xfe also not json")
    job["complete_sha256"] = sha256_bytes(b"\x00not json {")
    w.save(plan)
    _, doc = written(w, tmp_path)
    assert doc["units"]["S4"]["1106"]["complete_sha256"] == sha256_bytes(b"\x00not json {")
    assert doc["units"]["S4"]["1106"]["job_sha256"] == sha256_bytes(b"\xff\xfe also not json")


# ----- refusals -------------------------------------------------------------------------------------------------------


def edit_job(w: World, kind: str, arm: str, seed: int, **change) -> None:
    plan = w.plan()
    _, _, job = sk.find_job(plan, kind, arm, seed)
    job.update(change)
    w.save(plan)


def add_job(w: World, host: str, job: dict, block: str = "B", done: bool = True) -> None:
    plan = w.plan()
    plan["hosts"].setdefault(host, {"block": block, "done": done, "jobs": []})["jobs"].append(job)
    w.save(plan)


def rewrite_rules(w: World, change) -> None:
    text = w.rules.read_text()
    head, pins = text.split("REJUDGED_PINS = {'B': (), 'A': tuple(")
    pins = json.loads(pins.rsplit(")}", 1)[0])
    change(pins)
    sk.rules_module(w.rules, pins)


def strata_variant(w: World, sets=SETS, settings_sha: str | None = None) -> None:
    settings, digest = bf.strata_settings()
    ranks = {p: (i + 1) / (len(PIDS) + 1) for i, p in enumerate(PIDS)}
    sim = bf.similarity_record({m: ranks for m in sets}, {m: EDITS[m] for m in sets})
    data = st.strata(sim, sha256_bytes(sim), settings, settings_sha or digest)
    w.strata.write_bytes(data)
    w.strata_sha = sha256_bytes(data)


def _same_unit(w: World) -> None:
    """S3 1105's job names S1 1105's folder and COMPLETE.json (its own edit record kept)."""
    plan = w.plan()
    _, _, s1_job = sk.find_job(plan, "arm", "S1", 1105)
    _, _, s3_job = sk.find_job(plan, "arm", "S3", 1105)
    s3_job.update(unit=s1_job["unit"], complete_sha256=s1_job["complete_sha256"])
    w.save(plan)


def _space_in_path(w: World) -> None:
    plan = w.plan()
    host, _, job = sk.find_job(plan, "arm", "S1", 1103)
    tree = w.kit / "retrieved" / host / "tree"
    (tree / job["unit"]).rename(tree / "round1" / "s1 1103")
    job["unit"] = "round1/s1 1103"
    w.save(plan)


def _symlink_job(w: World) -> None:
    host, _, job = sk.find_job(w.plan(), "arm", "S4", 1104)
    path = w.kit / "retrieved" / host / "tree" / job["unit"] / "job.json"
    shutil.copy(path, path.with_name("job-copy.json"))
    path.unlink()
    path.symlink_to("job-copy.json")


def _missing_job(w: World) -> None:
    host, _, job = sk.find_job(w.plan(), "a0_arm", "a0", 1106)
    (w.kit / "retrieved" / host / "tree" / job["unit"] / "job.json").unlink()


def _changed_pin_job(w: World) -> None:
    path = w.data / "gate-a-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1/job.json"
    path.write_bytes(path.read_bytes() + b" ")


def _tables(w: World, block: str, add=(), drop=()) -> None:
    """The rules module with block BLOCK's table changed (the real block_runs, then cells added or dropped)."""
    code = ("_real_block_runs = block_runs\n\n\n"
            "def block_runs(code, block, reused=()):\n"
            "    runs = _real_block_runs(code, block, reused)\n"
            "    if block != CHANGED:\n"
            "        return runs\n"
            "    return [r for r in runs if r not in DROP] + ADD\n")
    with open(w.rules, "a") as handle:
        handle.write(f"CHANGED, DROP, ADD = {block!r}, {list(drop)!r}, {list(add)!r}\n" + code)


def _strata_arm(w: World) -> None:
    doc = json.loads(w.strata.read_bytes())
    doc["add_sets"]["S1"]["arm"] = "edit-" + "f" * 64
    data = canonical_json(doc)
    w.strata.write_bytes(data)
    w.strata_sha = sha256_bytes(data)


def _plan(w: World, change) -> None:
    plan = w.plan()
    change(plan)
    w.save(plan)


REFUSALS = {
    "plan_code": (lambda w: _plan(w, lambda p: p["records"]["plan_ab"].update(code="B")), "records plan 'B'"),
    "not_sealed": (lambda w: _plan(w, lambda p: p["seals"].pop("B")), "block B is not sealed"),
    "two_units": (lambda w: add_job(w, "b-7", sk.find_job(w.plan(), "arm", "S1", 1105)[2]), "two complete units"),
    "no_unit": (lambda w: edit_job(w, "arm", "S4", 1106, status="crashed"), "no complete, pulled unit"),
    "not_pulled": (lambda w: edit_job(w, "arm", "S4", 1106, pulled=False), "no complete, pulled unit"),
    "not_done": (lambda w: _plan(w, lambda p: p["hosts"]["a-9"]["jobs"][0].update(status="complete")),
                 "on a host that is not done"),
    "outside_table": (lambda w: add_job(w, "a-8", {**sk.find_job(w.plan(), "a0_arm", "a0", 1105)[2]}, block="A"),
                      "whose table does not hold it"),
    "reused_in_kit": (lambda w: add_job(w, "a-8", {**sk.find_job(w.plan(), "a0_arm", "a0", 1104)[2], "seed": 1103},
                                        block="A"), "its source is reused"),
    "other_block": (lambda w: add_job(w, "cfy-1", sk.find_job(w.plan(), "arm", "S1", 1105)[2], block="certify"),
                    "in block certify"),
    "wrong_kind": (lambda w: add_job(w, "a-8", {**sk.find_job(w.plan(), "a0_arm", "a0", 1104)[2], "kind": "arm",
                                                "status": "not_started"}, block="A"), "a arm job of this arm"),
    "bqi_own_a0": (lambda w: edit_job(w, "a0_arm", "a0", 1107, role="bqi_own_a0"), "B\\+Qi's own a0"),
    "complete_hash": (lambda w: edit_job(w, "arm", "S1", 1103, complete_sha256="7" * 64),
                      "does not hash to plan.json's complete_sha256"),
    "unit_not_plain": (lambda w: edit_job(w, "arm", "S1", 1103, unit="../round1/x"), "not a plain relative path"),
    "pin_changed": (_changed_pin_job, "differs from its pin"),
    "no_pin": (lambda w: rewrite_rules(w, lambda pins: pins.pop(2)), "holds 0 a0 entries at 1103"),
    "two_pins": (lambda w: rewrite_rules(w, lambda pins: pins.append(dict(pins[1]))), "holds 2 a0 entries at 1102"),
    "pin_target": (lambda w: rewrite_rules(w, lambda pins: pins[1].update(target="init")),
                   "not arm a0 at checkpoint e1"),
    "recipe_g": (lambda w: edit_job(w, "arm", "S1", 1104, recipe="G"), "not the kit's arm recipe"),
    "recipe_refused": (lambda w: _plan(w, lambda p: p["recipes"][RECIPE_S_PATH].update(config_sha256=bf.RECIPE_BQI)),
                       "one B14's settings refuse"),
    "recipe_unknown": (lambda w: _plan(w, lambda p: p.pop("recipes")), "recipes table entry"),
    "engine": (lambda w: edit_job(w, "arm", "S3", 1105, engine="Y"), "not an allowed code identity"),
    "edit_other": (lambda w: edit_job(w, "arm", "S3", 1106, edit={"path": "x", "sha256": EDITS["S1"], "source": "x"}),
                   "its edit is not the strata's add set"),
    "edit_missing": (lambda w: edit_job(w, "arm", "S4", 1104, edit=None), "names no edit SHA-256"),
    "a0_edit": (lambda w: edit_job(w, "a0_arm", "a0", 1105, edit={"path": "x", "sha256": "e" * 64}),
                "an a0 unit with an edit"),
    "one_unit_two_cells": (_same_unit, "name one unit"),
    "path_form": (_space_in_path, "not in the form B14's settings allow"),
    "symlink": (_symlink_job, "symbolic link"),
    "missing_file": (_missing_job, "job.json is missing"),
    "strata_sha": (lambda w: setattr(w, "strata_sha", "6" * 64), "hashes to"),
    "strata_settings": (lambda w: strata_variant(w, settings_sha="8" * 64), "other overlap_strata settings"),
    "strata_without_s4": (lambda w: strata_variant(w, sets=("S1", "S3")), "does not hold the plan's add sets"),
    "rules_broken": (lambda w: w.rules.write_text("REJUDGED_PINS = {\n"), "did not load \\(SyntaxError\\)"),
    "two_tables": (lambda w: _tables(w, "B", add=[("S1", 1102)]), "S1 at 1102 is in the tables of blocks A and B"),
    "reused_in_table": (lambda w: _tables(w, "A", add=[("a0", 1102)]), "a0 at 1102 is reused and in block A's table"),
    "no_table": (lambda w: _tables(w, "B", drop=[("S1", 1105)]), "S1 at 1105 is in no table of the blocks"),
    "pin_path": (lambda w: rewrite_rules(w, lambda pins: pins[1].update(path="/" + pins[1]["path"])),
                 "its path is not a plain relative path"),
    "strata_arm": (_strata_arm, "add set S1: its arm is not edit-<its edit SHA-256>"),
    "rules_incomplete": (lambda w: w.rules.write_text("REJUDGED_PINS = {}\n"), "the rules module has no"),
}


@pytest.mark.parametrize("case", sorted(REFUSALS))
def test_each_ambiguity_refuses_and_writes_nothing(world, tmp_path, capsys, case):
    world = need(world)
    w = world.copy(tmp_path / "w")
    change, match = REFUSALS[case]
    change(w)
    out = tmp_path / "out"
    assert oi.main(w.args(out)) == 2
    err = capsys.readouterr().err
    assert err.startswith("REFUSED: ") and "(nothing written)" in err and not out.exists()
    assert re.search(match, err), err
    assert not [t for t in bf.SENTINELS if t in err]


def test_a_pin_of_another_name_at_a_reused_seed_is_not_a0s_unit(world, tmp_path, capsys):
    """theta0's untuned unit is pinned with the engine arm a0: the writer takes a0's pin by its name (build.py
    pins_by_cell), the second computation by its checkpoint, so a theta0 pin at 1102 changes neither."""
    world = need(world)
    w = world.copy(tmp_path / "w")
    rewrite_rules(w, lambda pins: pins[3].update(seed=1102))
    _, doc = written(w, tmp_path)
    assert doc["sources"]["origins"]["a0"]["1102"] == {"pin": "a0 1102 (Gate A)"}
    assert oc.main(w.check_args(tmp_path / "out" / oi.OUTPUT)) == 0


def test_a_unit_folder_outside_the_data_root_refuses(world, tmp_path, capsys):
    """The pins sit under repo/tmp, beside the kit: with the kit as the data root they are outside it."""
    world = need(world)
    assert oi.main(world.args(tmp_path / "out", **{"data-root": world.kit})) == 2
    assert "a0 at 1102: its folder is not inside the data root" in capsys.readouterr().err


def test_an_output_folder_that_is_not_empty_refuses(world, tmp_path, capsys):
    world = need(world)
    out = tmp_path / "out"
    out.mkdir()
    (out / "other.json").write_text("{}")
    assert oi.main(world.args(out)) == 2 and sorted(p.name for p in out.iterdir()) == ["other.json"]
    assert "exists and is not empty" in capsys.readouterr().err


# ----- the second computation -----------------------------------------------------------------------------------------


def test_the_second_computation_reproduces_the_file_byte_for_byte(world, tmp_path, capsys):
    world = need(world)
    data, _ = written(world, tmp_path)
    file = tmp_path / "out" / oi.OUTPUT
    assert oc.main(world.check_args(file)) == 0
    assert f"same bytes: {file} sha256 {sha256_bytes(data)}" in capsys.readouterr().out
    proc = subprocess.run([sys.executable, "-I", "-B", str(PKG / "overlap_inputs_check.py"), *world.check_args(file)],
                          capture_output=True, text=True)                 # isolated: no module of this repository
    assert proc.returncode == 0 and sha256_bytes(data) in proc.stdout, proc.stderr
    assert oc.recompute(world.kit, world.strata, "plan_a", world.rules, world.repo, world.data,
                        st.SETTINGS_PATH) == data == canonical_json(expected_document(world))


def test_the_second_computation_imports_no_module_of_this_repository():
    import ast

    tree = ast.parse((PKG / "overlap_inputs_check.py").read_text())
    names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert names <= {"__future__", "argparse", "hashlib", "json", "os", "sys", "pathlib"}, names


def _flip(file: Path) -> None:
    doc = json.loads(file.read_bytes())
    old = doc["units"]["S1"]["1104"]["job_sha256"]
    doc["units"]["S1"]["1104"]["job_sha256"] = ("0" if old[0] != "0" else "1") + old[1:]
    file.write_bytes(canonical_json(doc))


def _job_changed_after(w: World, file: Path) -> None:
    host, _, job = sk.find_job(w.plan(), "arm", "S3", 1107)
    path = w.kit / "retrieved" / host / "tree" / job["unit"] / "job.json"
    path.write_bytes(path.read_bytes() + b"\n")


def _reindented(file: Path) -> None:
    file.write_text(json.dumps(json.loads(file.read_bytes()), indent=1, sort_keys=True) + "\n")


def _extra_key(file: Path) -> None:
    doc = json.loads(file.read_bytes())
    doc["note"] = "x"
    file.write_bytes(canonical_json(doc))


def _other_strata(w: World) -> None:
    w.strata.write_bytes(w.strata.read_bytes() + b"\n")


PLANTED = {
    "flipped_digit": (lambda w, f: _flip(f), "units.S1.1104.job_sha256"),
    "job_changed_after": (lambda w, f: _job_changed_after(w, f), "units.S3.1107.job_sha256"),
    "reindented": (lambda w, f: _reindented(f), "the serialization"),
    "extra_key": (lambda w, f: _extra_key(f), "first difference at note"),
    "other_strata": (lambda w, f: _other_strata(w), "first difference at strata_sha256"),
    "other_plan": (lambda w, f: _plan(w, lambda p: p.update(name="other")), "sources.plan_json_sha256"),
    "pin_order_kept": (lambda w, f: rewrite_rules(w, lambda pins: pins.reverse()), "sources.rules_sha256"),
}


@pytest.mark.parametrize("case", sorted(PLANTED))
def test_the_second_computation_finds_one_planted_difference(world, tmp_path, capsys, case):
    world = need(world)
    w = world.copy(tmp_path / "w")
    written(w, tmp_path)
    file = tmp_path / "out" / oi.OUTPUT
    plant, where = PLANTED[case]
    plant(w, file)
    capsys.readouterr()
    assert oc.main(w.check_args(file)) == 1
    out = capsys.readouterr().out
    assert out.startswith("DIFFERENT: ") and where in out, out


@pytest.mark.parametrize("case", ["two_units", "no_unit", "complete_hash", "pin_changed", "plan_code"])
def test_the_second_computation_refuses_what_the_writer_refuses(world, tmp_path, capsys, case):
    world = need(world)
    w = world.copy(tmp_path / "w")
    written(w, tmp_path)
    file = tmp_path / "out" / oi.OUTPUT
    REFUSALS[case][0](w)
    capsys.readouterr()
    assert oc.main(w.check_args(file)) == 2
    assert capsys.readouterr().err.startswith("REFUSED: ")
    assert oi.main(w.args(tmp_path / "again")) == 2


def test_the_second_computation_counts_only_done_hosts_of_the_blocks_read(world, tmp_path, capsys):
    """A complete a0 1105 on a host that is not done and a complete S1 1105 in block certify: neither is a candidate,
    so the only difference is plan.json's own SHA-256."""
    world = need(world)
    w = world.copy(tmp_path / "w")
    written(w, tmp_path)
    plan = w.plan()
    plan["hosts"]["b-9"] = {"block": "B", "done": False, "jobs": [dict(sk.find_job(plan, "a0_arm", "a0", 1105)[2])]}
    plan["hosts"]["cfy-1"] = {"block": "certify", "done": True,
                              "jobs": [dict(sk.find_job(plan, "arm", "S1", 1105)[2])]}
    w.save(plan)
    capsys.readouterr()
    assert oc.main(w.check_args(tmp_path / "out" / oi.OUTPUT)) == 1
    assert "first difference at sources.plan_json_sha256" in capsys.readouterr().out


def test_the_two_routes_differ_on_a_pin_outside_the_block_tables(world, tmp_path, capsys):
    """An a0 pin at 1104 (a seed whose a0 the kit trained): the writer, by the tables, takes the kit unit; the second
    computation finds two candidates and refuses, so the lead sees the disagreement instead of a silent choice."""
    world = need(world)
    w = world.copy(tmp_path / "w")
    rewrite_rules(w, lambda pins: pins.append({**pins[1], "name": "a0 1104 (extra)", "seed": 1104}))
    _, doc = written(w, tmp_path)
    assert doc["sources"]["origins"]["a0"]["1104"] == {"block": "A", "host": "a-4", "job": 4}
    capsys.readouterr()
    assert oc.main(w.check_args(tmp_path / "out" / oi.OUTPUT)) == 2
    assert "a0 at 1104 has 2 candidate units" in capsys.readouterr().err


# ----- the builder's synthetic kit ------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    """synth_kit's plan_a world (read-only use) with the recipe and engine records the real plan.json holds, or the
    text of why it could not be built (read through need, as the world is)."""
    try:
        s = sk.make(tmp_path_factory.mktemp("synth"), "plan_a")
        plan = s.plan()
        plan["recipes"], plan["engines"] = RECIPES, {"X": bf.ENGINE_X, "Y": ENGINE_Y}
        for h in plan["hosts"].values():
            for job in h["jobs"]:
                if job["kind"] in ("arm", "a0_arm"):
                    job["recipe"] = "S"
        s.save_plan(plan)
        return s
    except Exception as exc:  # noqa: BLE001 - reported by each test that reads the fixture, as a failure
        return f"building the builder's synthetic kit raised {type(exc).__name__}: {exc}"


def test_on_the_builders_synthetic_kit_the_units_are_the_builders(synth, tmp_path, capsys):
    synth = need(synth)
    out = tmp_path / "out"
    argv = ["--kit", str(synth.kit), "--strata", str(synth.b14["strata"]), "--strata-sha256",
            synth.b14["strata_sha256"], "--out", str(out), "--rules", str(synth.rules), "--repo", str(synth.repo),
            "--data-root", str(synth.root)]
    assert oi.main(argv) == 0, capsys.readouterr().err
    doc = json.loads((out / oi.OUTPUT).read_bytes())
    rules, rules_sha = builder_rules(synth.rules)
    _, record, _ = builder("plan_a", synth.kit, synth.repo, rules, rules_sha, None)
    assert sum(len(per) for per in doc["units"].values()) == 24
    for name, per in doc["units"].items():
        for seed, unit in per.items():
            cell = record["cells"][f"{name} {seed}"]["unit"]
            truth = synth.units[(name, int(seed))]
            assert unit["complete_sha256"] == cell["complete_sha256"] == truth["complete"]
            assert unit["job_sha256"] == cell["files"]["job.json"] == truth["job"]
            assert (synth.root / unit["path"] / "COMPLETE.json").is_file()
    assert doc["units"]["a0"]["1102"]["path"] == "repo/tmp/synth-gate/1102-a0-e1-a1"
    check = ["--file", str(out / oi.OUTPUT), "--kit", str(synth.kit), "--strata", str(synth.b14["strata"]), "--rules",
             str(synth.rules), "--repo", str(synth.repo), "--data-root", str(synth.root), "--settings",
             str(st.SETTINGS_PATH)]
    assert oc.main(check) == 0
