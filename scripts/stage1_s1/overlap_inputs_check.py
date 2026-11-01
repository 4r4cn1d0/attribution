"""B14, part 3's second computation: the overlap report's inputs file, recomputed by other code from the same sources
and compared with the written file byte for byte (standard library only; it imports no module of this repository).

    python -I -B scripts/stage1_s1/overlap_inputs_check.py --file FILE --kit DIR --strata FILE
        [--reading plan_a] [--rules FILE] [--repo DIR] [--data-root DIR] [--settings FILE]

Give it the writer's own sources. The defaults name the same files as the writer's defaults when both run from one
checkout: its rules module runkit/stage1-olmo/stage1_rules.py, B14's settings, the checkout as --repo and its tmp/ as
the data root.

**Other code, one rule.** overlap_inputs.py follows the builder's route: the block tables (stage1_rules.block_runs),
the reused seeds (REUSED_SEEDS) and the pins by name. This file counts candidates instead. Each cell (a0 and each add
set of the seed plan, read from the settings file, at each of its seeds) takes its one candidate among the
REJUDGED_PINS["A"] entries of arm a0, that seed and checkpoint e1 (a0 only) and the plan.json jobs of the cell's kind
(a0_arm for a0, else arm), arm and seed that are complete, not recorded as not pulled, on a done host of a block the
reading reads. No candidate, or more than one, refuses. Each unit's COMPLETE.json and job.json are hashed here
(hashlib, in blocks of 1 MiB) and must equal plan.json's or the pin's values; paths are made relative to the data root
with os.path.realpath and os.path.relpath; the document is serialized here (sorted keys, indent 2, UTF-8, a final
newline). plan.json, the rules module, the settings and the strata record are hashed; their content checks are the
writer's, and this file only recomputes.

Exit 0: equal (the SHA-256 printed); 1: different (the first differing key printed, no value); 2: refused (a source is
missing or ambiguous; nothing compared).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIND = "stage1 overlap report inputs"
READINGS = {"plan_a": ("d1_plan_a", "A", ("A", "B"))}     # reading -> (seed plan, plan code, blocks read)
CHECKPOINT = "e1"
COMPARATOR = "a0"


class Refused(Exception):
    """A source is missing or ambiguous; nothing is compared."""


def read(path: Path, what: str) -> bytes:
    if os.path.islink(path) or not os.path.isfile(path):
        raise Refused(f"{what} is missing, not a regular file or a symbolic link")
    with open(path, "rb") as handle:
        return handle.read()


def file_digest(path: Path, what: str) -> str:
    """SHA-256 of a regular file, read in blocks (its bytes are not parsed)."""
    if os.path.islink(path) or not os.path.isfile(path):
        raise Refused(f"{what} is missing, not a regular file or a symbolic link")
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def strict_json(data: bytes, what: str):
    def no_repeats(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise Refused(f"{what}: a JSON object repeats a key")
            out[key] = value
        return out
    try:
        return json.loads(data, object_pairs_hook=no_repeats)
    except ValueError:
        raise Refused(f"{what} is not JSON") from None


def rules_namespace(data: bytes, path: Path) -> dict:
    """The rules module run from these bytes (the writer runs the same file)."""
    space = {"__name__": "stage1_rules_for_overlap_inputs_check", "__file__": str(path)}
    exec(compile(data, str(path), "exec", dont_inherit=True), space)  # noqa: S102 - the kit's own rules
    return space


def relative(folder: Path, data_root: Path) -> str:
    rel = os.path.relpath(os.path.realpath(folder), os.path.realpath(data_root))
    if os.path.isabs(rel) or rel in (os.curdir, os.pardir) or rel.startswith(os.pardir + os.sep):
        raise Refused("a unit folder is not inside the data root")
    return rel.replace(os.sep, "/")


def candidates(name: str, seed: int, plan: dict, pins: list, blocks: tuple) -> list:
    out = []
    if name == COMPARATOR:
        out += [("pin", pin) for pin in pins if isinstance(pin, dict) and pin.get("arm") == COMPARATOR
                and pin.get("seed") == seed and pin.get("target") == CHECKPOINT]
    kind = "a0_arm" if name == COMPARATOR else "arm"
    for host in sorted(plan["hosts"]):
        record = plan["hosts"][host]
        if record.get("block") not in blocks or record.get("done") is not True:
            continue
        for index, job in enumerate(record.get("jobs") or []):
            if isinstance(job, dict) and (job.get("kind"), job.get("arm"), job.get("seed"), job.get("status")) == \
                    (kind, name, seed, "complete") and job.get("pulled") is not False:
                out.append(("kit", (record["block"], host, index, job)))
    return out


def recompute(kit: Path, strata: Path, reading: str, rules: Path, repo: Path, data_root: Path,
              settings: Path) -> bytes:
    """The inputs file's bytes, by this file's route (module doc)."""
    plan_name, code, blocks = READINGS[reading]
    plan_bytes = read(Path(kit) / "plan.json", "the kit's plan.json")
    plan = strict_json(plan_bytes, "plan.json")
    if ((plan.get("records") or {}).get("plan_ab") or {}).get("code") != code:
        raise Refused(f"plan.json does not record plan {code}")
    rules_bytes = read(Path(rules), "the rules module")
    pins = list((rules_namespace(rules_bytes, Path(rules)).get("REJUDGED_PINS") or {}).get("A") or ())
    settings_bytes = read(Path(settings), "B14's settings")
    plan_seeds = strict_json(settings_bytes, "B14's settings")["report"]["seed_plans"][plan_name]
    names = [COMPARATOR] + list(plan_seeds["add_sets"])
    units = {name: {} for name in names}
    origins = {name: {} for name in names}
    for name in names:
        for seed in plan_seeds["seeds"]:
            found = candidates(name, seed, plan, pins, blocks)
            if len(found) != 1:
                raise Refused(f"{name} at {seed} has {len(found)} candidate units, not one")
            source, item = found[0]
            if source == "pin":
                folder = Path(repo) / item["path"]
                complete = file_digest(folder / "COMPLETE.json", f"{name} at {seed}: COMPLETE.json")
                job = file_digest(folder / "job.json", f"{name} at {seed}: job.json")
                if (complete, job) != (item.get("complete_sha256"), item.get("job_sha256")):
                    raise Refused(f"{name} at {seed}: the pinned unit's files differ from the pin")
                origins[name][str(seed)] = {"pin": item["name"]}
            else:
                block, host, index, record = item
                folder = Path(kit) / "retrieved" / host / "tree" / record["unit"]
                complete = file_digest(folder / "COMPLETE.json", f"{name} at {seed}: COMPLETE.json")
                if complete != record.get("complete_sha256"):
                    raise Refused(f"{name} at {seed}: COMPLETE.json is not at plan.json's SHA-256")
                job = file_digest(folder / "job.json", f"{name} at {seed}: job.json")
                origins[name][str(seed)] = {"block": block, "host": host, "job": index}
            units[name][str(seed)] = {"path": relative(folder, data_root), "complete_sha256": complete,
                                      "job_sha256": job}
    strata_sha = hashlib.sha256(read(Path(strata), "the strata record")).hexdigest()
    doc = {"kind": KIND, "version": 1, "strata_sha256": strata_sha, "seed_plan": plan_name, "units": units,
           "sources": {"reading": reading, "plan_code": code,
                       "plan_json_sha256": hashlib.sha256(plan_bytes).hexdigest(),
                       "rules_sha256": hashlib.sha256(rules_bytes).hexdigest(),
                       "settings_sha256": hashlib.sha256(settings_bytes).hexdigest(), "origins": origins}}
    return (json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def first_difference(a, b, where: str = "") -> str | None:
    """The first key path (sorted order) at which two parsed documents differ, or None."""
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                return f"{where}{key}"
            found = first_difference(a[key], b[key], f"{where}{key}.")
            if found is not None:
                return found
        return None
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for n, (x, y) in enumerate(zip(a, b)):
            found = first_difference(x, y, f"{where}{n}.")
            if found is not None:
                return found
        return None
    return None if (type(a), a) == (type(b), b) else (where.rstrip(".") or "the document")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--file", type=Path, required=True, help="the written overlap_inputs.json")
    parser.add_argument("--kit", type=Path, required=True)
    parser.add_argument("--strata", type=Path, required=True)
    parser.add_argument("--reading", choices=sorted(READINGS), default="plan_a")
    parser.add_argument("--rules", type=Path, default=ROOT / "runkit" / "stage1-olmo" / "stage1_rules.py")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--data-root", type=Path, default=ROOT / "tmp")
    parser.add_argument("--settings", type=Path,
                        default=ROOT / "scripts" / "stage1_s1" / "settings" / "overlap_strata.json")
    args = parser.parse_args(argv)
    try:
        given = read(args.file, "the inputs file")
        data = recompute(args.kit, args.strata, args.reading, args.rules, args.repo, args.data_root, args.settings)
    except Refused as exc:
        print(f"REFUSED: {exc} (nothing compared)", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - a malformed source; its message is withheld (it may hold a value)
        print(f"REFUSED: an unexpected {type(exc).__name__} (nothing compared)", file=sys.stderr)
        return 2
    if given == data:
        print(f"same bytes: {args.file} sha256 {hashlib.sha256(given).hexdigest()}")
        return 0
    try:
        where = first_difference(json.loads(given), json.loads(data)) or "the serialization (equal documents)"
    except ValueError:
        where = "the file (not JSON)"
    print(f"DIFFERENT: {args.file} sha256 {hashlib.sha256(given).hexdigest()}, recomputed "
          f"{hashlib.sha256(data).hexdigest()}; first difference at {where}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
