"""B14, part 3: the overlap report's inputs file, written from the kit's plan.json, the kit's rules module and the
sealed strata record, with every unit named by path and SHA-256 only (RS B14; REV4 section 9.4; addendum section 11
point 12; the reading runbook's step 0.4; Mac, $0, standard library only).

    python -B scripts/stage1_s1/overlap_inputs.py --kit DIR --strata FILE --strata-sha256 HEX --out DIR
        [--reading plan_a] [--rules FILE] [--repo DIR] [--data-root DIR]

**Output.** ``overlap_inputs.json`` in canonical JSON, written once into an absent or empty folder: kind "stage1
overlap report inputs", version 1, ``strata_sha256``, ``seed_plan`` (the reading's B14 seed plan: plan_a reads
d1_plan_a, a0 and the add sets S1, S3 and S4 at 1102-1107), ``units`` ({a0 or an add set's name: {seed: {path,
complete_sha256, job_sha256}}}, each path relative to B14's data root) and ``sources`` (the reading, plan.json's plan
code, the SHA-256 of plan.json, of the rules module and of B14's settings, and each unit's origin: its pin's name, or
its block, host and job index). ``overlap_strata.py report --inputs`` reads it with the same ``--data-root``; the
report does not read ``sources``.

**Which units.** The B16 input builder's (reading_input/build.py: cell_blocks, pins_by_cell, _primary_jobs), so that
the builder finds B14's units equal to its own (build.py overlap_block). a0 at a reused seed (stage1_rules.
REUSED_SEEDS) is the one REJUDGED_PINS["A"] entry named a0 at that seed, of checkpoint e1, whose COMPLETE.json and
job.json hash to the pin (paths relative to ``--repo``). Every other cell (arm, seed) comes from the block whose table
(stage1_rules.block_runs of plan.json's plan code) holds it: the one job of kind a0_arm (a0) or arm (an add set) of
that arm and seed that is complete, not recorded as not pulled, on a done host of that block. Its unit is
retrieved/HOST/tree/UNIT under ``--kit``; its COMPLETE.json must hash to plan.json's complete_sha256; job.json is
hashed and named.

**Refusals** (anything ambiguous; nothing is written): plan.json's plan code is not the reading's, or a block read has
no seal entry in plan.json; a cell in no block's table or in two, or a reused cell that a table holds; no a0 pin at a
reused seed, two, one of another arm or checkpoint, or one whose files differ from it; for a kit cell no complete unit
or two, a complete unit on a host that is not done (the seal records whether it moved, and this writer reads no
seal), a complete unit in a block whose table does not hold the cell, a job of the other kind, or B+Qi's own a0; a
kit unit whose recipe (plan.json) is not the kit's arm recipe (stage1_rules.TRAINING_IDENTITY_RECIPES) or has a config
SHA-256 (plan.json's recipes table) that B14's settings refuse, or whose engine (plan.json's engines) is not an allowed
code identity; an add set's unit whose edit (plan.json, the engine's arm edit-<SHA-256>) is not the strata's add set,
or an a0 unit with an edit; the strata record not at its SHA-256, not made under B14's pinned settings
(overlap_strata's own check) or without an add set of the plan; a unit folder outside the data root or a path B14's
path_pattern refuses; a symbolic link or a missing file; one folder or one COMPLETE.json for two cells.

**What it reads.** plan.json, B14's settings and the strata record (parsed), the rules module (run from the bytes it
is hashed from; the builder runs it too), and of each unit only the bytes of COMPLETE.json and job.json, hashed and
never parsed. No seal is read: the builder binds every unit to its block seal, and the report's own checks (the
frozen sealed check, job.json's fields, D-6's recipes) run on the units at the reading. overlap_inputs_check.py
recomputes the file by other code; the two must agree byte for byte. Printed: counts, origins and SHA-256 values
only. Exit 0: written; exit 2: refused, nothing written.
"""

from __future__ import annotations

import argparse
import re
import sys
import types
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1.limits import limits_common as lc  # noqa: E402
from scripts.stage1_s1 import overlap_strata as st  # noqa: E402

OUTPUT = "overlap_inputs.json"
RULES = REPO / "runkit" / "stage1-olmo" / "stage1_rules.py"
# reading -> (B14's seed plan, plan.json's plan code, the blocks read): build.py's READING_BLOCKS and READING_CODE; the
# kit records plan A with blocks A and B sealed, so plan_a is the one reading B14 reads
READINGS = {"plan_a": ("d1_plan_a", "A", ("A", "B"))}
KINDS = {st.COMPARATOR: "a0_arm"}           # every add set's unit is an "arm" job (build.py PRIMARY_KINDS)
CHECKPOINT = "e1"
BQI_OWN_A0 = "bqi_own_a0"                   # B+Qi's own a0 after a failed certificate: no B16 field (build.py)
COMPLETE, JOB = "COMPLETE.json", "job.json"
RULES_NAMES = ("REJUDGED_PINS", "REUSED_SEEDS", "block_runs", "RECIPE_NAMES", "TRAINING_IDENTITY_RECIPES")


# ----- the sources ----------------------------------------------------------------------------------------------------


def plain(rel: Any, what: str) -> str:
    """A plain relative POSIX path (reading_input/sources.plain's rule): not absolute, no empty, '.' or '..' part, no
    backslash."""
    if not isinstance(rel, str) or not rel or "\\" in rel or rel.startswith("/") \
            or any(part in ("", ".", "..") for part in rel.split("/")):
        raise s1.Refusal(f"{what} is not a plain relative path")
    return rel


def read_bytes(path: Path, what: str) -> bytes:
    """A regular file's bytes; a symbolic link or a missing file refuses."""
    if path.is_symlink() or not path.is_file():
        raise s1.Refusal(f"{what} is missing, not a regular file or a symbolic link")
    return path.read_bytes()


def file_sha256(path: Path, what: str) -> str:
    """The SHA-256 of a regular file's bytes, which are never parsed."""
    return sha256_bytes(read_bytes(path, what))


def load_rules(path: Path) -> tuple[Any, str]:
    """The kit's rules module (standard library only, the builder executes it too), run from the bytes it is hashed
    from, and its SHA-256."""
    data = read_bytes(Path(path), "the rules module")
    module = types.ModuleType("stage1_rules_for_overlap_inputs")
    module.__file__ = str(path)
    try:
        exec(compile(data, str(path), "exec", dont_inherit=True), module.__dict__)  # noqa: S102 - the kit's rules
    except Exception as exc:  # noqa: BLE001 - the rules module is the kit's code; its message is not printed
        raise s1.Refusal(f"the rules module did not load ({type(exc).__name__})") from None
    missing = [name for name in RULES_NAMES if not hasattr(module, name)]
    if missing:
        raise s1.Refusal(f"the rules module has no {', '.join(missing)}")
    return module, sha256_bytes(data)


def read_plan(kit: Path, reading: str) -> tuple[dict, str]:
    """plan.json (strict JSON, parsed from the bytes it is hashed from) and its SHA-256: a stage-1 plan of the
    reading's plan code whose blocks read are each recorded as sealed."""
    data = read_bytes(Path(kit) / "plan.json", "the kit's plan.json")
    plan = s1.strict_json(data)
    if not isinstance(plan, dict) or not isinstance(plan.get("hosts"), dict) \
            or not isinstance(plan.get("records"), dict):
        raise s1.Refusal("the kit's plan.json is not a stage-1 plan (hosts, records)")
    _, code, blocks = READINGS[reading]
    ab = plan["records"].get("plan_ab")
    recorded = ab.get("code") if isinstance(ab, dict) else None
    if recorded != code:
        raise s1.Refusal(f"plan.json records plan {recorded!r}; the reading {reading} is plan {code}'s")
    for block in blocks:
        entry = (plan.get("seals") or {}).get(block)
        if not isinstance(entry, dict) or not isinstance(entry.get("sha256"), str) \
                or not s1.HEX64.match(entry["sha256"]):
            raise s1.Refusal(f"block {block} is not sealed in plan.json")
    return plan, sha256_bytes(data)


def strata_record(data: bytes, digest: str, settings_sha256: str, plan_sets: list[str]) -> dict:
    """The sealed strata record as the report checks it (overlap_strata._strata_record: its SHA-256, kind, version,
    B14's pinned settings, halves), holding every add set of the plan, each named edit-<its edit SHA-256>."""
    doc = st._strata_record(data, digest, settings_sha256)
    missing = [name for name in plan_sets if name not in doc["add_sets"]]
    if missing:
        raise s1.Refusal(f"the strata record does not hold the plan's add sets {missing}")
    for name in plan_sets:
        block = doc["add_sets"][name]
        edit = lc.hex64(block.get("edit_sha256") if isinstance(block, dict) else None, f"add set {name}: edit_sha256")
        if block.get("arm") != "edit-" + edit:
            raise s1.Refusal(f"add set {name}: its arm is not edit-<its edit SHA-256>")
    return doc


# ----- the cells -----------------------------------------------------------------------------------------------------


def table_cells(rules: Any, code: str, blocks: tuple, cells: list[tuple[str, int]]) -> dict:
    """(arm, seed) -> "reused" (a0 at stage1_rules.REUSED_SEEDS) or the block whose table holds it, for the cells B14
    reads (build.py cell_blocks)."""
    tables: dict = {}
    for block in blocks:
        try:
            runs = [tuple(run) for run in rules.block_runs(code, block)]
        except ValueError:
            raise s1.Refusal(f"the rules have no table of plan {code}'s block {block}") from None
        for arm, seed in runs:
            if (arm, seed) in tables:
                raise s1.Refusal(f"{arm} at {seed} is in the tables of blocks {tables[(arm, seed)]} and {block}")
            tables[(arm, seed)] = block
    reused = {(st.COMPARATOR, seed) for seed in rules.REUSED_SEEDS}
    out = {}
    for cell in cells:
        if cell in reused and cell in tables:
            raise s1.Refusal(f"{cell[0]} at {cell[1]} is reused and in block {tables[cell]}'s table (two sources)")
        if cell not in reused and cell not in tables:
            raise s1.Refusal(f"{cell[0]} at {cell[1]} is in no table of the blocks {list(blocks)}")
        out[cell] = "reused" if cell in reused else tables[cell]
    return out


def pinned_unit(rules: Any, repo: Path, seed: int) -> tuple[Path, str, str, dict]:
    """a0 at a reused seed: (folder, COMPLETE.json SHA-256, job.json SHA-256, origin) of the one REJUDGED_PINS["A"]
    entry named a0 at this seed (build.py pins_by_cell's key), of checkpoint e1, whose two files hash to the pin."""
    pins = rules.REJUDGED_PINS.get("A", ()) if isinstance(rules.REJUDGED_PINS, Mapping) else None
    if not isinstance(pins, (list, tuple)):
        raise s1.Refusal("the rules' REJUDGED_PINS holds no block-A list")
    found = [p for p in pins if isinstance(p, Mapping)
             and str(p.get("name", "")).split(" ")[0] == st.COMPARATOR and p.get("seed") == seed]
    if len(found) != 1:
        raise s1.Refusal(f"REJUDGED_PINS['A'] holds {len(found)} a0 entries at {seed}, not one")
    pin = found[0]
    if pin.get("arm") != st.COMPARATOR or pin.get("target") != CHECKPOINT:
        raise s1.Refusal(f"the a0 pin at {seed} is not arm a0 at checkpoint {CHECKPOINT}")
    folder = Path(repo) / plain(pin.get("path"), f"the a0 pin at {seed}: its path")
    complete = lc.hex64(pin.get("complete_sha256"), f"the a0 pin at {seed}: complete_sha256")
    job = lc.hex64(pin.get("job_sha256"), f"the a0 pin at {seed}: job_sha256")
    if file_sha256(folder / COMPLETE, f"the a0 pin at {seed}: {COMPLETE}") != complete \
            or file_sha256(folder / JOB, f"the a0 pin at {seed}: {JOB}") != job:
        raise s1.Refusal(f"the a0 unit pinned at {seed} differs from its pin (COMPLETE.json or job.json)")
    return folder, complete, job, {"pin": str(pin.get("name"))}


def kit_jobs(plan: Mapping[str, Any], where: Mapping[tuple, str]) -> dict:
    """(arm, seed) -> (block, host, job index, job) of the one complete, pulled unit of each kit cell (module doc). Jobs
    of other kinds (regenerate, retrain, ref_train, ...) are not units of these cells."""
    found: dict = {}
    for host, h in sorted(plan["hosts"].items()):
        if not isinstance(h, dict) or not isinstance(h.get("jobs"), list):
            raise s1.Refusal(f"plan.json's host {host} holds no job list")
        for i, job in enumerate(h["jobs"]):
            if not isinstance(job, dict) or job.get("kind") not in ("arm", "a0_arm"):
                continue
            cell = (job.get("arm"), job.get("seed"))
            if cell not in where:
                continue
            label = f"{host} job {i} ({cell[0]} at {cell[1]})"
            if job.get("role") == BQI_OWN_A0:
                raise s1.Refusal(f"{label}: B+Qi's own a0 has no field in the reading; the lead rules")
            if job.get("kind") != KINDS.get(cell[0], "arm"):
                raise s1.Refusal(f"{label}: a {job.get('kind')} job of this arm (its kind is "
                                 f"{KINDS.get(cell[0], 'arm')})")
            if job.get("status") != "complete":
                continue
            if where[cell] != h.get("block"):
                raise s1.Refusal(f"{label}: a complete unit in block {h.get('block')}, whose table does not hold it "
                                 f"(its source is {where[cell]})")
            if h.get("done") is not True:
                raise s1.Refusal(f"{label}: a complete unit on a host that is not done (the seal says whether it "
                                 "moved; this writer reads no seal)")
            if job.get("pulled") is False:
                continue                            # recorded complete, not pulled: not an input (build.py scan)
            if cell in found:
                raise s1.Refusal(f"{cell[0]} at {cell[1]}: two complete units ({found[cell][1]} job "
                                 f"{found[cell][2]} and {host} job {i})")
            found[cell] = (h["block"], host, i, job)
    missing = sorted(c for c, b in where.items() if b != "reused" and c not in found)
    if missing:
        raise s1.Refusal(f"{len(missing)} cell(s) have no complete, pulled unit in their block ({missing[0][0]} at "
                         f"{missing[0][1]}, block {where[missing[0]]})")
    return found


def kit_unit(kit: Path, plan: Mapping[str, Any], rules: Any, rep: Mapping[str, Any], where: tuple,
             want_arm: str) -> tuple[Path, str, str, dict]:
    """(folder, COMPLETE.json SHA-256, job.json SHA-256, origin) of one kit cell's job: its recipe, engine and edit as
    plan.json records them, then its two files by hash."""
    block, host, i, job = where
    label = f"{job.get('arm')} at {job.get('seed')} ({host} job {i})"
    rel = plain(job.get("unit"), f"{label}: plan.json's unit")
    complete = lc.hex64(job.get("complete_sha256"), f"{label}: plan.json's complete_sha256")
    if job.get("recipe") not in tuple(rules.TRAINING_IDENTITY_RECIPES):
        raise s1.Refusal(f"{label}: plan.json's recipe {job.get('recipe')!r} is not the kit's arm recipe "
                         f"{list(rules.TRAINING_IDENTITY_RECIPES)}")
    config = (plan.get("recipes") or {}).get(rules.RECIPE_NAMES.get(job.get("recipe")))
    config_sha = lc.hex64(config.get("config_sha256") if isinstance(config, dict) else None,
                          f"{label}: plan.json's recipes table entry of recipe {job.get('recipe')!r}")
    if config_sha in rep["refused_recipes"]:
        raise s1.Refusal(f"{label}: its recipe {config_sha} is one B14's settings refuse")
    code = (plan.get("engines") or {}).get(job.get("engine"))
    if code not in rep["allowed_code_sha256"]:
        raise s1.Refusal(f"{label}: plan.json's engine {str(job.get('engine'))!r} is not an allowed code identity")
    edit = job.get("edit")
    if want_arm == st.COMPARATOR:
        if edit:
            raise s1.Refusal(f"{label}: an a0 unit with an edit")
    else:
        if not isinstance(edit, dict) or not isinstance(edit.get("sha256"), str) or not s1.HEX64.match(edit["sha256"]):
            raise s1.Refusal(f"{label}: plan.json's edit record names no edit SHA-256")
        if (edit.get("engine_arm") or f"edit-{edit['sha256']}") != want_arm:
            raise s1.Refusal(f"{label}: its edit is not the strata's add set ({want_arm[:13]})")
    folder = Path(kit) / "retrieved" / host / "tree" / rel
    if file_sha256(folder / COMPLETE, f"{label}: {COMPLETE}") != complete:
        raise s1.Refusal(f"{label}: COMPLETE.json does not hash to plan.json's complete_sha256")
    return folder, complete, file_sha256(folder / JOB, f"{label}: {JOB}"), {"block": block, "host": host, "job": i}


def unit_path(folder: Path, data_root: Path, pattern: str, what: str) -> str:
    """The folder's path relative to B14's data root, in the form limits_common.check_unit takes (inside the root,
    no '..', B14's path_pattern)."""
    root, real = Path(data_root).resolve(), Path(folder).resolve()
    if root not in real.parents:
        raise s1.Refusal(f"{what}: its folder is not inside the data root")
    rel = real.relative_to(root).as_posix()
    if ".." in Path(rel).parts or not re.fullmatch(pattern, rel):
        raise s1.Refusal(f"{what}: its path is not in the form B14's settings allow")
    return rel


# ----- the file ------------------------------------------------------------------------------------------------------


def inputs(kit: Path, strata_bytes: bytes, strata_sha256: str, reading: str, rules_path: Path, repo: Path,
           data_root: Path, settings: Mapping[str, Any], settings_sha256: str) -> bytes:
    """overlap_inputs.json's bytes (module doc)."""
    st.check_content(settings)
    if reading not in READINGS:
        raise s1.Refusal(f"no B14 inputs for the reading {reading!r} (only {sorted(READINGS)})")
    plan_name, code, blocks = READINGS[reading]
    rep = settings["report"]
    seed_plan = rep["seed_plans"].get(plan_name)
    if not isinstance(seed_plan, dict):
        raise s1.Refusal(f"B14's settings have no seed plan {plan_name}")
    seeds, plan_sets = list(seed_plan["seeds"]), list(seed_plan["add_sets"])
    lc.hex64(strata_sha256, "--strata-sha256")
    strata = strata_record(strata_bytes, strata_sha256, settings_sha256, plan_sets)
    rules, rules_sha = load_rules(rules_path)
    plan, plan_sha = read_plan(kit, reading)
    names = [st.COMPARATOR] + plan_sets
    cells = [(name, seed) for name in names for seed in seeds]
    where = table_cells(rules, code, blocks, cells)
    jobs = kit_jobs(plan, where)
    units: dict = {name: {} for name in names}
    origins: dict = {name: {} for name in names}
    folders: dict = {}
    completes: dict = {}
    for name, seed in cells:
        what = f"{name} at {seed}"
        if where[(name, seed)] == "reused":
            folder, complete, job, origin = pinned_unit(rules, repo, seed)
        else:
            want = st.COMPARATOR if name == st.COMPARATOR else strata["add_sets"][name]["arm"]
            folder, complete, job, origin = kit_unit(kit, plan, rules, rep, jobs[(name, seed)], want)
        rel = unit_path(folder, data_root, rep["path_pattern"], what)
        if rel in folders or complete in completes:
            raise s1.Refusal(f"{what} and {folders.get(rel) or completes.get(complete)} name one unit")
        folders[rel], completes[complete] = what, what
        units[name][str(seed)] = {"path": rel, "complete_sha256": complete, "job_sha256": job}
        origins[name][str(seed)] = origin
    doc = {"kind": st.INPUTS_KIND, "version": 1, "strata_sha256": strata_sha256, "seed_plan": plan_name,
           "units": units,
           "sources": {"reading": reading, "plan_code": code, "plan_json_sha256": plan_sha, "rules_sha256": rules_sha,
                       "settings_sha256": settings_sha256, "origins": origins}}
    return canonical_json(doc)


# ----- the command line ----------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--kit", type=Path, required=True, help="the kit folder (plan.json, retrieved/)")
    parser.add_argument("--strata", type=Path, required=True, help="the sealed strata.json")
    parser.add_argument("--strata-sha256", required=True, help="its SHA-256 (FOCUS)")
    parser.add_argument("--out", type=Path, required=True, help="output folder (absent or empty)")
    parser.add_argument("--reading", choices=sorted(READINGS), default="plan_a")
    parser.add_argument("--rules", type=Path, default=RULES, help="the kit's rules module")
    parser.add_argument("--repo", type=Path, default=lc.ENGINE_ROOT, help="the folder REJUDGED_PINS paths start at")
    parser.add_argument("--data-root", type=Path, default=lc.DEFAULT_DATA_ROOT, help="B14's data root (the report's)")
    parser.add_argument("--settings", type=Path, default=st.SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, st.SETTINGS_SHA256, st.SETTINGS_NAME)
        data = inputs(args.kit, args.strata.read_bytes(), args.strata_sha256, args.reading, args.rules, args.repo,
                      args.data_root, settings, digest)
        written = s1.write_new_files(args.out.resolve(), {OUTPUT: data})
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)",
              file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - a malformed source; its message is withheld (it may hold a value)
        print(f"REFUSED: an unexpected {type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    doc = s1.strict_json(data)
    print(f"wrote {OUTPUT} into {args.out} ({written[OUTPUT]})")
    print(f"  seed plan {doc['seed_plan']}; strata {doc['strata_sha256']}; "
          f"plan.json {doc['sources']['plan_json_sha256']}")
    for name, per in doc["sources"]["origins"].items():
        pins = [seed for seed, origin in per.items() if "pin" in origin]
        kit = sorted({f"{o['block']}:{o['host']}" for o in per.values() if "pin" not in o})
        print(f"  {name}: {len(per)} units; pinned at {', '.join(pins) or 'none'}; "
              f"from the kit {', '.join(kit) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
