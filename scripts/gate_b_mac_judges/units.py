"""Judgeable units under Gate B run roots or given explicitly (stdlib only).

    python3 units.py (--run-root DIR)... (--unit DIR)... [--targets init e1]     # lists units as JSON; ids and hashes only

A run root is a pod's `retrieved` folder (holding HOST/tree/...) or one `retrieved/HOST` folder (holding tree/). Every
folder under HOST/tree/** that holds a job.json and an identity.json is an attempt (the walk of the frozen reading's
Context.accept, which enumerates by job.json and skips a job.json folder without identity.json); a job.json folder
without identity.json is listed as skipped ("not an attempt (no identity.json)"). An attempt without COMPLETE.json is
unsealed and listed as skipped. A folder with COMPLETE.json and no job.json (a pod's tree/cuda-preflight-1, for
example) is not a job unit: it is listed as skipped and never refuses. An explicit unit folder (for the Gate A a0 units
under the probe kits) must sit at .../retrieved/HOST/tree/.../UNIT and must hold job.json, identity.json and
COMPLETE.json and be judgeable, or it refuses.

job.json is read first. A sealed attempt whose job.json kind is not "run-one" (a tool folder such as score-rows, whose
COMPLETE.json has another format) or that evaluates no bank (evaluate_bank absent or null: the Gate B retrain) is
skipped with its reason before COMPLETE.json is examined, so it never refuses the enumeration; a run-one unit whose
evaluate_bank is another value than "dev" refuses. A unit is judgeable when its job.json says kind "run-one",
evaluate_bank "dev" and a target_checkpoint among the targets. Each judgeable unit is verified before use, and refused
(Refusal) when: COMPLETE.json is not complete; its job_sha256 (or its files entry for job.json) is not job.json's
SHA-256; its target, arm or seed differs from job.json's; eval/<target>/ is missing; or COMPLETE.json's files list
does not name exactly the files on disk under eval/<target>/ with matching SHA-256 (a stray file there, such as a
.DS_Store written by Finder, refuses the unit: fail-closed). Two paths holding the same attempt (equal COMPLETE.json
SHA-256) refuse.

For each unit: host, unit (its path under HOST/tree), arm and seed (job.json), target, complete_sha256, job_sha256,
completed_utc and the generations/samples/guard/guard_samples files' paths and SHA-256 (null when absent). load_items
reads the harm answers of one mode (greedy: generations.jsonl rows of kind "harm"; sampled: samples.jsonl, all of kind
"harm"), re-checks the file hash, and returns ids and answer SHA-256 (the text only when asked, for a judge).
load_guard reads the sealed guard records of one mode (greedy: guard.jsonl rows of kind "harm"; sampled:
guard_samples.jsonl) and returns their ids with the Qwen3Guard safety and refusal labels only.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from common import Refusal, jsonl_records, sha256_bytes, sha256_text  # noqa: E402

TARGETS = ("init", "e1")
EVAL_FILES = {"generations": "generations.jsonl", "samples": "samples.jsonl", "guard": "guard.jsonl",
              "guard_samples": "guard_samples.jsonl"}
MODE_FILE = {"greedy": "generations", "sampled": "samples"}
GUARD_FILE = {"greedy": "guard", "sampled": "guard_samples"}
BANK = "dev"
NOT_A_JOB_UNIT = "not a job unit (COMPLETE.json and no job.json)"
UNSEALED = "no COMPLETE.json (unsealed attempt)"
NO_BANK = "evaluates no bank"
NO_IDENTITY = "not an attempt (no identity.json)"


@dataclasses.dataclass(frozen=True, eq=False)
class Unit:
    host: str
    unit: str                 # path under HOST/tree (posix), e.g. "round1/1101-a0-e1-a1"
    path: pathlib.Path
    kind: str
    arm: str
    seed: int
    target: str
    complete_sha256: str
    job_sha256: str
    completed_utc: str | None
    manifest_sha256: str | None
    files: dict               # EVAL_FILES key -> {"path": str, "sha256": str} or None

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def label(self) -> str:
        return f"{self.host}/{self.unit}"

    def describe(self) -> dict:
        return {"host": self.host, "unit": self.unit, "path": str(self.path), "arm": self.arm, "seed": self.seed,
                "target": self.target, "complete_sha256": self.complete_sha256, "job_sha256": self.job_sha256,
                "completed_utc": self.completed_utc, "files": self.files}


@dataclasses.dataclass(frozen=True)
class Item:
    mode: str
    prompt_id: str
    sample_index: int | None
    answer_sha256: str
    text: str | None = dataclasses.field(default=None, repr=False, compare=False)


def _load_json(path: pathlib.Path, what: str):
    data = path.read_bytes()
    try:
        return data, json.loads(data)
    except json.JSONDecodeError:
        raise Refusal(f"{what}: {path.name} is not JSON") from None


def read_unit(path: pathlib.Path, host: str, unit_rel: str, targets=TARGETS):
    """(Unit, None) for a judgeable unit, (None, reason) for a sealed folder that is not judgeable (no identity.json,
    kind, no bank or target); Refusal for a defective one. job.json's kind and evaluate_bank are read before
    COMPLETE.json is examined, so a tool folder (another kind) or a no-bank unit is skipped whatever its COMPLETE.json
    format."""
    path = pathlib.Path(path).absolute()
    label = f"{host}/{unit_rel}"
    if not (path / "COMPLETE.json").is_file():
        raise Refusal(f"{label}: no COMPLETE.json")
    if not (path / "job.json").is_file():
        raise Refusal(f"{label}: no job.json")
    if not (path / "identity.json").is_file():           # the frozen reading's Context.accept skips such a folder
        return None, NO_IDENTITY
    job_bytes, job = _load_json(path / "job.json", label)
    if not isinstance(job, dict):
        raise Refusal(f"{label}: job.json is not an object")
    if job.get("kind") != "run-one":                     # a tool folder (score-rows, attributes): skipped, never read
        return None, f"job kind {job.get('kind')!r} is not run-one"
    if job.get("evaluate_bank") is None:                 # the Gate B retrain: a0 at 1101, no bank
        return None, NO_BANK
    if job.get("evaluate_bank") != BANK:
        raise Refusal(f"{label}: job.json evaluate_bank is not {BANK!r}")
    complete_bytes, complete = _load_json(path / "COMPLETE.json", label)
    if not isinstance(complete, dict):
        raise Refusal(f"{label}: COMPLETE.json is not an object")
    if complete.get("complete") is not True:
        raise Refusal(f"{label}: COMPLETE.json does not say complete")
    job_sha = sha256_bytes(job_bytes)
    if complete.get("job_sha256") != job_sha:
        raise Refusal(f"{label}: COMPLETE.json job_sha256 is not job.json's SHA-256")
    listed = complete.get("files")
    if not isinstance(listed, dict):
        raise Refusal(f"{label}: COMPLETE.json has no files list")
    if "job.json" in listed and listed["job.json"] != job_sha:
        raise Refusal(f"{label}: COMPLETE.json lists another job.json SHA-256")
    target = job.get("target_checkpoint")
    if target not in targets:
        return None, f"target {target!r} is not one of {list(targets)}"
    if "target_checkpoint" in complete and complete["target_checkpoint"] != target:
        raise Refusal(f"{label}: COMPLETE.json target differs from job.json's")
    arm, seed = job.get("arm"), job.get("seed")
    if not isinstance(arm, str) or not arm or not isinstance(seed, int) or isinstance(seed, bool):
        raise Refusal(f"{label}: job.json has no string arm and integer seed")
    trajectory = complete.get("trajectory") if isinstance(complete.get("trajectory"), dict) else {}
    if ("arm" in trajectory and trajectory["arm"] != arm) or ("seed" in trajectory and trajectory["seed"] != seed):
        raise Refusal(f"{label}: COMPLETE.json trajectory arm or seed differs from job.json's")
    eval_dir = path / "eval" / target
    if not eval_dir.is_dir():
        raise Refusal(f"{label}: no eval/{target}/ folder")
    prefix = f"eval/{target}/"
    named = {k: v for k, v in listed.items() if k.startswith(prefix)}
    on_disk = {p.relative_to(path).as_posix(): p for p in sorted(eval_dir.rglob("*")) if p.is_file()}
    if set(named) != set(on_disk):
        raise Refusal(f"{label}: COMPLETE.json lists {len(named)} files under {prefix}, {len(on_disk)} are on disk; "
                      f"unlisted {sorted(set(on_disk) - set(named))}, absent {sorted(set(named) - set(on_disk))}")
    hashes = {}
    for rel, p in on_disk.items():
        hashes[rel] = sha256_bytes(p.read_bytes())
        if hashes[rel] != named[rel]:
            raise Refusal(f"{label}: {rel} does not match its SHA-256 in COMPLETE.json")
    files = {}
    for key, fname in EVAL_FILES.items():
        rel = prefix + fname
        files[key] = {"path": str(on_disk[rel]), "sha256": hashes[rel]} if rel in on_disk else None
    if files["generations"] is None:
        raise Refusal(f"{label}: no {prefix}generations.jsonl")
    return Unit(host=host, unit=unit_rel, path=path, kind="run-one", arm=arm, seed=seed, target=target,
                complete_sha256=sha256_bytes(complete_bytes), job_sha256=job_sha,
                completed_utc=complete.get("completed_utc"), manifest_sha256=job.get("manifest_sha256"),
                files=files), None


def _hosts(root: pathlib.Path) -> list[pathlib.Path]:
    root = pathlib.Path(root).absolute()
    if (root / "tree").is_dir():
        return [root]
    hosts = sorted(d for d in root.iterdir() if d.is_dir() and (d / "tree").is_dir()) if root.is_dir() else []
    if not hosts:
        raise Refusal(f"run root {root}: no HOST/tree/ folder")
    return hosts


def locate(unit_dir: pathlib.Path) -> tuple[str, str]:
    """(host, unit path under HOST/tree) of an explicit unit folder at .../retrieved/HOST/tree/.../UNIT."""
    parts = pathlib.Path(unit_dir).absolute().parts
    for i in range(len(parts) - 2, 1, -1):
        if parts[i] == "tree" and parts[i - 2] == "retrieved":
            return parts[i - 1], "/".join(parts[i + 1:])
    raise Refusal(f"{unit_dir}: an explicit unit must sit at .../retrieved/HOST/tree/.../UNIT")


def enumerate_units(run_roots=(), unit_dirs=(), targets=TARGETS) -> tuple[list[Unit], list[dict]]:
    """(units sorted by host and unit, skipped [{host, unit, reason}]). Explicit units that are not judgeable refuse."""
    found: dict[pathlib.Path, Unit] = {}
    skipped = []
    for root in run_roots:
        for host_dir in _hosts(root):
            tree = host_dir / "tree"
            attempts = {p.parent for p in tree.rglob("job.json") if p.is_file()}
            for folder in sorted({p.parent for p in tree.rglob("COMPLETE.json") if p.is_file()} - attempts):
                skipped.append({"host": host_dir.name, "unit": folder.relative_to(tree).as_posix(),
                                "reason": NOT_A_JOB_UNIT})
            for folder in sorted(attempts):
                rel = folder.relative_to(tree).as_posix()
                if not (folder / "identity.json").is_file():         # as the frozen reading: not an attempt
                    skipped.append({"host": host_dir.name, "unit": rel, "reason": NO_IDENTITY})
                    continue
                if not (folder / "COMPLETE.json").is_file():
                    skipped.append({"host": host_dir.name, "unit": rel, "reason": UNSEALED})
                    continue
                unit, reason = read_unit(folder, host_dir.name, rel, targets)
                if unit is None:
                    skipped.append({"host": host_dir.name, "unit": rel, "reason": reason})
                else:
                    found[unit.path] = unit
    for unit_dir in unit_dirs:
        host, rel = locate(unit_dir)
        unit, reason = read_unit(pathlib.Path(unit_dir), host, rel, targets)
        if unit is None:
            raise Refusal(f"{host}/{rel}: not judgeable ({reason})")
        found[unit.path] = unit
    by_complete: dict[str, Unit] = {}
    for unit in found.values():
        other = by_complete.get(unit.complete_sha256)
        if other is not None:
            raise Refusal(f"one attempt (COMPLETE.json {unit.complete_sha256[:16]}) found at two paths: {other.path} and "
                          f"{unit.path}; move one aside")
        by_complete[unit.complete_sha256] = unit
    return sorted(found.values(), key=lambda u: (u.host, u.unit, u.complete_sha256)), skipped


def load_items(unit: Unit, mode: str, with_text: bool = False) -> list[Item]:
    """The harm answers of one mode, in file order; the file must still match the hash verified at enumeration."""
    if mode not in MODE_FILE:
        raise Refusal(f"unknown mode {mode!r}")
    entry = unit.files.get(MODE_FILE[mode])
    fname = EVAL_FILES[MODE_FILE[mode]]
    if entry is None:
        raise Refusal(f"{unit.label}: no {fname} for the {mode} answers")
    data = pathlib.Path(entry["path"]).read_bytes()
    if sha256_bytes(data) != entry["sha256"]:
        raise Refusal(f"{unit.label}: {fname} changed after it was verified")
    items, seen = [], set()
    for lineno, r in jsonl_records(data, f"{unit.label}: {fname}"):
        if not isinstance(r, dict):
            raise Refusal(f"{unit.label}: {fname} line {lineno} is not an object")
        if r.get("kind") != "harm":
            if mode == "sampled":
                raise Refusal(f"{unit.label}: {fname} line {lineno} is not a harm answer")
            continue
        pid = r.get("prompt_id")
        sidx = r.get("sample_index") if mode == "sampled" else None
        text = r.get("text")
        if not isinstance(pid, str) or not pid or not isinstance(text, str):
            raise Refusal(f"{unit.label}: {fname} line {lineno} has no string prompt_id and text")
        if mode == "sampled" and (not isinstance(sidx, int) or isinstance(sidx, bool) or sidx < 0):
            raise Refusal(f"{unit.label}: {fname} line {lineno} has no integer sample_index")
        if (pid, sidx) in seen:
            raise Refusal(f"{unit.label}: {fname} holds prompt {pid} sample {sidx} twice")
        seen.add((pid, sidx))
        items.append(Item(mode, pid, sidx, sha256_text(text), text if with_text else None))
    return items


def load_guard(unit: Unit, mode: str) -> dict:
    """{(prompt_id, sample_index or None): {"safety", "refusal"}} of the unit's sealed guard records of one mode: greedy,
    guard.jsonl rows of kind "harm"; sampled, guard_samples.jsonl rows (kind absent or "harm"). The file must still match
    the hash verified at enumeration. Ids and labels only; a record of one id twice refuses."""
    if mode not in GUARD_FILE:
        raise Refusal(f"unknown mode {mode!r}")
    fname = EVAL_FILES[GUARD_FILE[mode]]
    entry = unit.files.get(GUARD_FILE[mode])
    if entry is None:
        raise Refusal(f"{unit.label}: no {fname} for the {mode} answers")
    data = pathlib.Path(entry["path"]).read_bytes()
    if sha256_bytes(data) != entry["sha256"]:
        raise Refusal(f"{unit.label}: {fname} changed after it was verified")
    out = {}
    for lineno, r in jsonl_records(data, f"{unit.label}: {fname}"):
        if not isinstance(r, dict):
            raise Refusal(f"{unit.label}: {fname} line {lineno} is not an object")
        kind = r.get("kind")
        if (mode == "greedy" and kind != "harm") or (mode == "sampled" and kind not in (None, "harm")):
            continue
        pid = r.get("prompt_id")
        sidx = r.get("sample_index") if mode == "sampled" else None
        if not isinstance(pid, str) or not pid:
            raise Refusal(f"{unit.label}: {fname} line {lineno} has no string prompt_id")
        if mode == "sampled" and (not isinstance(sidx, int) or isinstance(sidx, bool) or sidx < 0):
            raise Refusal(f"{unit.label}: {fname} line {lineno} has no integer sample_index")
        if (pid, sidx) in out:
            raise Refusal(f"{unit.label}: {fname} holds prompt {pid} sample {sidx} twice")
        out[(pid, sidx)] = {"safety": r.get("safety"), "refusal": r.get("refusal")}
    return out


def add_unit_arguments(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--run-root", action="append", default=[], type=pathlib.Path,
                    help="a pod's retrieved/ folder, or one retrieved/HOST folder (repeatable)")
    ap.add_argument("--unit", action="append", default=[], type=pathlib.Path,
                    help="an explicit unit folder at .../retrieved/HOST/tree/.../UNIT (repeatable)")
    ap.add_argument("--targets", nargs="+", default=list(TARGETS))


def units_from_args(a) -> tuple[list[Unit], list[dict]]:
    if not a.run_root and not a.unit:
        raise Refusal("give at least one --run-root or --unit")
    units, skipped = enumerate_units(a.run_root, a.unit, tuple(a.targets))
    if not units:
        raise Refusal("no judgeable unit found")
    return units, skipped


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    add_unit_arguments(ap)
    a = ap.parse_args(argv)
    try:
        units, skipped = units_from_args(a)
    except Refusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    print(json.dumps({"units": [u.describe() for u in units], "skipped": skipped}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
