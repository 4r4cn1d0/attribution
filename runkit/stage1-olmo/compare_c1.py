"""The C1 certificate comparator (D4, the lead's ruling R2, kit round 30a; YB X-5, X-6): engine Y's C1 unit against
Gate B's R_1101 unit, both as the light pull left them on the Mac (no *.safetensors), under the rule of
experiments/safety_selection/tests/removal_digest.py (imported, pinned by SHA-256: its TIMED keys stripped, its job,
plan, steps, state-record and evaluation rules). Mac only; standard library only; nothing is sent anywhere.

    python -B compare_c1.py C1_UNIT R1101_UNIT --out FILE

Every file of either unit is listed with one verdict: equal, differ, or missing (present in one unit only). The
certificate rule (``counts`` true) is removal_digest.unit_digest's reading of a unit, which is YB X-5's list ("adapter
and optimizer fingerprints, steps.jsonl, every evaluation file and the summary without timings"):
  job.json            canonical JSON without code_sha256 (the running code's identity) and with resume_from cut to its
                      folder name (removal_digest's job rule); also without the edit path (where the sealed file lay:
                      Gate B passed sealed/edits/..., the stage-1 runner edits/<SHA-256>.edit.json; the arm
                      edit-<SHA-256> pins the bytes and edit.json is compared byte for byte) and without replicate_of
                      after checking it: C1's must be R_1101's run-folder string (R1101_UNIT's path ends with it) and
                      R_1101's must be null (X-5: C1 runs "as replicate_of")
  plan.json           canonical JSON (the stream plan)
  steps.jsonl         each step without TIMED keys, the constant-rate lr dropped as removal_digest drops it (the
                      recipe's train section from the unit's own identity.json)
  states/*/state.json without TIMED keys (the adapter and optimizer fingerprints; the light pull left the states)
  eval/**             summary.json without TIMED keys; a .jsonl whose first three lines hold "seconds", line by line
                      without TIMED keys; every other evaluation file byte for byte
  edit.json           byte for byte (the edit's own bytes)
Listed and compared but not part of the rule (``counts`` false): *.safetensors (if any were pulled), COMPLETE.json,
identity.json (the code identity, Python and platform: X and Y differ by design), assets.json (the environment), the
ledger and status files and any other file: JSON without TIMED keys, JSONL line by line, other files byte for byte.

pass = both units complete (COMPLETE.json present, no error.txt) and every counted file equal, with the rule's core
files present in both (job.json, plan.json, steps.jsonl, states/<target>/state.json, eval/<target>/summary.json; the
target is C1's job target_checkpoint, else e1). X-6 (LQ20's evaluation part, "equal U labels and equal task loss" as
far as the files allow): the guard's label files (eval/*/guard.jsonl, eval/*/guard_samples.jsonl) and the task-loss
file (eval/*/query_loss.jsonl) are counted evaluation files, so a pass implies X-6; ``x6`` restates their verdicts.

Seal-safety: the output (stdout and --out, the same JSON) holds file names, verdicts, rule names, booleans, the two
unit paths and the rule's code hashes only; never a value, a label, an answer, a count or a hash of a unit file.
--out is created once (an existing file is never replaced) and never inside either unit. Exit 0 pass, 1 no pass,
2 refused (nothing written).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REMOVAL_DIGEST = ROOT / "experiments" / "safety_selection" / "tests" / "removal_digest.py"
REMOVAL_DIGEST_SHA256 = "59a713f02ddb74dd60f337077170cc240b24ccbe634a7fe67cfda0493a58da8a"
KIND = "stage1 c1 certificate comparison"
CORE = ("job.json", "plan.json", "steps.jsonl", "states/{t}/state.json", "eval/{t}/summary.json")
X6 = {"u_labels": ("guard.jsonl", "guard_samples.jsonl"), "task_loss": ("query_loss.jsonl",)}
EQUAL, DIFFER, MISSING = "equal", "differ", "missing"


class Refused(Exception):
    """The comparison cannot run as asked (nothing is written)."""


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load_rule(path: pathlib.Path = None):
    """removal_digest.py, checked against its pin, imported without writing bytecode."""
    path = pathlib.Path(path or REMOVAL_DIGEST)
    if not path.is_file() or sha(path) != REMOVAL_DIGEST_SHA256:
        raise Refused(f"{path.name} is missing or differs from its pin {REMOVAL_DIGEST_SHA256[:12]}...")
    spec = importlib.util.spec_from_file_location("s1_removal_digest_rule", path)
    module = importlib.util.module_from_spec(spec)
    before, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = before
    return module


def listing(unit: pathlib.Path) -> dict:
    """relpath (POSIX) -> path of every entry that is not a directory (symlinks included, never followed)."""
    out = {}
    for top, dirs, names in os.walk(unit, followlinks=False):
        base = pathlib.Path(top)
        for name in names + [d for d in dirs if (base / d).is_symlink()]:
            p = base / name
            out[p.relative_to(unit).as_posix()] = p
    return out


def rule_of(rel: str) -> tuple[str, bool]:
    """(rule name, counts toward pass) of a unit file (module doc)."""
    parts = rel.split("/")
    if rel.endswith(".safetensors"):
        return "model-state", False
    if rel == "job.json":
        return "job", True
    if rel == "plan.json":
        return "json", True
    if rel == "steps.jsonl":
        return "steps", True
    if len(parts) == 3 and parts[0] == "states" and parts[2] == "state.json":
        return "state-record", True
    if parts[0] == "eval" and len(parts) > 1:
        return "eval", True
    if rel == "edit.json":
        return "bytes", True
    return "other", False


def job_view(doc: dict) -> tuple[dict, object]:
    """removal_digest's job rule (code_sha256 dropped, resume_from cut to its name), the edit path dropped; returns
    (the view, replicate_of)."""
    job = dict(doc)
    job.pop("code_sha256", None)
    resume = job.get("resume_from")
    job["resume_from"] = None if resume is None else pathlib.PurePosixPath(str(resume)).name
    job.pop("edit", None)
    return job, job.pop("replicate_of", None)


def digest(rule, unit: pathlib.Path, rel: str, kind: str):
    """The comparable form of one file under its rule (any failure raises: the caller counts it as differ)."""
    p = unit / rel
    data = p.read_bytes()
    if kind == "json":
        return rule._canonical(json.loads(data))
    if kind == "steps":
        train = json.loads((unit / "identity.json").read_text())["recipe"]["train"]
        return rule._canonical([rule.drop_constant_lr(rule._strip(json.loads(line)), train)
                                for line in data.decode().splitlines()])
    if kind == "state-record":
        return rule._canonical(rule._strip(json.loads(data)))
    if kind == "eval":                              # removal_digest.unit_digest's evaluation rule, file by file
        if p.name == "summary.json":
            return rule._canonical(rule._strip(json.loads(data)))
        if p.suffix == ".jsonl" and any('"seconds"' in line for line in data.decode().splitlines()[:3]):
            return rule._canonical([rule._strip(json.loads(line)) for line in data.decode().splitlines()])
        return rule._sha(data)
    if kind == "other":
        try:
            if p.suffix == ".json":
                return rule._canonical(rule._strip(json.loads(data)))
            if p.suffix == ".jsonl":
                return rule._canonical([rule._strip(json.loads(line)) for line in data.decode().splitlines()])
        except ValueError:
            pass
    return rule._sha(data)


def verdict(rule, c1: pathlib.Path, r1101: pathlib.Path, rel: str, kind: str, left: dict, right: dict) -> str:
    if rel not in left or rel not in right:
        return MISSING
    if left[rel].is_symlink() or right[rel].is_symlink() or not left[rel].is_file() or not right[rel].is_file():
        return DIFFER
    try:
        if kind == "job":
            a, rep_a = job_view(json.loads(left[rel].read_bytes()))
            b, rep_b = job_view(json.loads(right[rel].read_bytes()))
            tail = r1101.as_posix()
            names_r1101 = isinstance(rep_a, str) and bool(rep_a) and (tail == rep_a or tail.endswith("/" + rep_a))
            return EQUAL if names_r1101 and rep_b is None and rule._canonical(a) == rule._canonical(b) else DIFFER
        return EQUAL if digest(rule, c1, rel, kind) == digest(rule, r1101, rel, kind) else DIFFER
    except Exception:  # noqa: BLE001 - a file the rule cannot read is never equal
        return DIFFER


def target_of(unit: pathlib.Path) -> str:
    try:
        target = json.loads((unit / "job.json").read_text()).get("target_checkpoint")
    except (OSError, ValueError, AttributeError):
        target = None
    return target if isinstance(target, str) and target and "/" not in target else "e1"


def compare(c1: pathlib.Path, r1101: pathlib.Path, rule=None) -> dict:
    """The comparison record (module doc). ``rule`` is the loaded removal_digest module (load_rule)."""
    rule = rule or load_rule()
    c1, r1101 = pathlib.Path(c1).resolve(), pathlib.Path(r1101).resolve()
    left, right = listing(c1), listing(r1101)
    target = target_of(c1)
    names = sorted(set(left) | set(right) | {c.format(t=target) for c in CORE})
    files = []
    for rel in names:
        kind, counts = rule_of(rel)
        files.append({"file": rel, "rule": kind, "counts": counts,
                      "verdict": verdict(rule, c1, r1101, rel, kind, left, right)})
    complete = all((u / "COMPLETE.json").is_file() and not (u / "COMPLETE.json").is_symlink()
                   and not (u / "error.txt").exists() for u in (c1, r1101))
    x6 = {}
    for name, wanted in X6.items():
        seen = [f["verdict"] for f in files if f["file"].startswith("eval/") and f["file"].split("/")[-1] in wanted]
        x6[name] = MISSING if not seen else EQUAL if all(v == EQUAL for v in seen) else \
            MISSING if MISSING in seen and DIFFER not in seen else DIFFER
    ok = complete and all(f["verdict"] == EQUAL for f in files if f["counts"])
    return {"kind": KIND, "version": 1, "c1_unit": str(c1), "r1101_unit": str(r1101),
            "rule": {"removal_digest": "experiments/safety_selection/tests/removal_digest.py",
                     "removal_digest_sha256": REMOVAL_DIGEST_SHA256, "compare_c1_sha256": sha(pathlib.Path(__file__))},
            "both_complete": complete, "files": files, "x6": x6, "pass": ok}


def inside(path: pathlib.Path, folder: pathlib.Path) -> bool:
    return path == folder or folder in path.parents


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="compare_c1.py", description=__doc__.splitlines()[0])
    ap.add_argument("c1_unit")
    ap.add_argument("r1101_unit")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    try:
        c1, r1101 = pathlib.Path(args.c1_unit), pathlib.Path(args.r1101_unit)
        for name, unit in (("C1_UNIT", c1), ("R1101_UNIT", r1101)):
            if unit.is_symlink() or not unit.is_dir():
                raise Refused(f"{name} is not a unit folder")
        if c1.resolve() == r1101.resolve():
            raise Refused("C1_UNIT and R1101_UNIT are the same folder")
        out = pathlib.Path(args.out).absolute()
        if out.exists() or out.is_symlink():
            raise Refused("--out exists; an evidence file is never replaced")
        if not out.parent.is_dir():
            raise Refused("--out's folder does not exist")
        real = out.parent.resolve() / out.name
        if inside(real, c1.resolve()) or inside(real, r1101.resolve()):
            raise Refused("--out lies inside a unit folder")
        doc = compare(c1, r1101, load_rule())
    except Refused as exc:
        print(f"compare_c1: refused: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    with open(out, "x", encoding="utf-8") as handle:
        handle.write(text)
    print(text, end="")
    return 0 if doc["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
