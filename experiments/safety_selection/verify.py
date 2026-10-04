"""Run verification (stdlib only): own completion evidence, the dependency chain and the
trained stream, reported separately.

- **Own files**: the folder's COMPLETE.json and every file it lists still match
  (``ledger.verify_files``). This says nothing about the folders the run used.
- **Dependency chain**: before any work, a job that uses earlier folders (a run-one
  continuation's ``resume_from``, an eval-state's ``source_run``, an attributes job's a0
  states) writes ``dependencies.json`` with one receipt per folder: the recorded and resolved
  path, the SHA-256 of its COMPLETE.json (which pins every file it lists) and job.json, its
  identity and, for a state, the state.json hash and position. Chain verification locates each
  dependency, checks its COMPLETE.json against the receipt and its own files, then follows its
  receipts recursively. A run is complete only if its own files AND its whole chain verify.
- **Stream** (run-one, given the prepared data): the concatenated step records of the resume
  chain equal the frozen stream exactly: steps 1..N with no gap or repetition, each step's rows
  as planned, no removed row, and every retained row exactly once in each completed epoch. An
  edit arm's stream is rebuilt from the run's own copy of its edit file (``edit.json``, hashed
  with the run), which must hash to the arm.

Receipts hold the absolute paths of the machine that ran the job. A downloaded or archived tree
is verified through a read-only ``PathMap`` (recorded prefix -> local prefix); job files and
receipts are never rewritten. Relative paths alone would need the original working-directory
layout and would not repair recorded absolute paths. Running continuations still need their
chain at the recorded locations (they read the earlier step records).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .common import read_json, read_jsonl, sha256_file
from .jobs import is_edit_arm
from .ledger import COMPLETE, read_complete, verify_files
from .prepare import load_prepared
from .stream import StreamPlan, make_plan

__all__ = ["STEPS", "DEPENDENCIES", "STATE_FIELDS", "PathMap", "dependency_receipt",
           "read_dependencies", "dependency_reports", "chain_problems", "resume_chain",
           "trajectory_steps", "check_trajectory", "verify_run", "compare_generations"]

STEPS = "steps.jsonl"
DEPENDENCIES = "dependencies.json"
STATE_FIELDS = ("checkpoint", "step", "examples_seen", "stream_sha256", "init_fingerprint",
                "adapter_fingerprint", "optimizer_fingerprint", "rng_fingerprint", "trajectory_cost")


class PathMap:
    """Read-only translation of recorded dependency paths: the first ``(recorded prefix, local
    prefix)`` pair whose prefix contains a path (whole components) relocates it; other paths
    are used as recorded."""

    def __init__(self, pairs: Iterable[tuple[str | Path, str | Path]] = ()) -> None:
        self.pairs = [(Path(old), Path(new)) for old, new in pairs]

    def resolve(self, recorded: str | Path) -> Path:
        path = Path(recorded)
        for old, new in self.pairs:
            if path.is_relative_to(old):
                return new / path.relative_to(old)
        return path

    def describe(self) -> list[list[str]]:
        return [[str(old), str(new)] for old, new in self.pairs]


def dependency_receipt(folder: str | Path, role: str, checkpoint: str | None = None) -> dict:
    """The pinned identity of a complete dependency folder, as recorded by the job using it."""
    folder = Path(folder)
    marker = read_complete(folder)
    if marker is None:
        raise ValueError(f"{folder}: no {COMPLETE}")
    receipt = {"role": role, "path": str(folder), "resolved": str(folder.resolve()),
               "complete_sha256": sha256_file(folder / COMPLETE),
               "job_sha256": sha256_file(folder / "job.json"), "kind": marker.get("kind"),
               "identity": marker.get("identity")}
    if checkpoint is not None:
        name = f"states/{checkpoint}/state.json"
        state = read_json(folder / name)
        receipt.update(checkpoint=checkpoint, state_sha256=marker["files"][name],
                       state={key: state.get(key) for key in STATE_FIELDS})
    return receipt


def read_dependencies(folder: str | Path) -> list[dict] | None:
    """The receipts a folder recorded (None if it has no dependencies.json)."""
    path = Path(folder) / DEPENDENCIES
    if not path.exists():
        return None
    data = read_json(path)
    deps = data.get("dependencies") if isinstance(data, dict) else None
    if not isinstance(deps, list) or not all(isinstance(d, dict) for d in deps):
        raise ValueError(f"{path} is malformed")
    return deps


def dependency_reports(run_dir: str | Path, path_map: PathMap | None = None) -> list[dict]:
    """One report per receipt reachable from ``run_dir`` (depth 0: its own receipts), each with
    its recorded and local path and its problems (empty: verified against the receipt)."""
    path_map = path_map or PathMap()
    reports: list[dict] = []
    visited: set[str] = set()
    own_files: dict[str, list[str]] = {}

    def verify_folder(local: Path, receipt: dict) -> list[str]:
        if not local.is_dir():
            return ["missing: no folder at the (mapped) recorded path"]
        if not (local / COMPLETE).is_file():
            return [f"no {COMPLETE}: not a complete run"]
        problems = []
        if sha256_file(local / COMPLETE) != receipt.get("complete_sha256"):
            problems.append(f"{COMPLETE} differs from the pinned receipt (changed, or another run)")
        key = str(local.resolve())
        if key not in own_files:
            own_files[key] = verify_files(local)
        return problems + own_files[key]

    def visit(folder: Path, depth: int) -> None:
        key = str(folder.resolve())
        if key in visited:
            return
        visited.add(key)
        try:
            deps = read_dependencies(folder)
        except (OSError, ValueError) as exc:
            deps, problem = None, f"{DEPENDENCIES} unreadable: {exc}"
        else:
            problem = f"no {DEPENDENCIES}: dependency receipts are missing"
        if deps is None:
            reports.append({"role": "receipts", "of": str(folder), "recorded": None,
                            "local": str(folder), "depth": depth, "problems": [problem]})
            return
        # A hash-consistent empty/partial receipt list must not hide a declared source.
        try:
            job = read_json(folder / "job.json")
            expected = {}
            if job.get("kind") == "run-one" and job.get("resume_from"):
                expected["resume_from"] = (job["resume_from"], None)
            elif job.get("kind") == "eval-state":
                expected["source_run"] = (job["source_run"], job["checkpoint"])
            elif job.get("kind") == "attributes":
                expected = {f"a0_state:{cp}": (path, cp) for cp, path in job["a0_states"].items()}
            if len(deps) != len(expected) or {d.get("role") for d in deps} != set(expected):
                raise ValueError("dependency roles/count differ from job's required sources")
            for dep in deps:
                source_path, checkpoint = expected[dep["role"]]
                if Path(dep.get("path", "")) != Path(source_path):
                    raise ValueError(f"{dep['role']}: receipt path differs from job source")
                if dep["role"] == "resume_from":
                    source = path_map.resolve(dep.get("resolved") or dep["path"])
                    checkpoint = read_json(source / "job.json")["target_checkpoint"]
                if dep.get("checkpoint") != checkpoint:
                    raise ValueError(f"{dep['role']}: receipt checkpoint differs from required source")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            reports.append({"role": "receipts", "of": str(folder), "recorded": None,
                            "local": str(folder), "depth": depth,
                            "problems": [("missing/unreadable dependency: " if isinstance(exc, OSError)
                                          else "") + str(exc)]})
            return
        for dep in deps:
            recorded = dep.get("resolved") or dep.get("path")
            local = path_map.resolve(recorded) if recorded else Path("")
            problems = (verify_folder(local, dep) if recorded
                        else ["receipt names no path"])
            reports.append({"role": dep.get("role"), "of": str(folder), "recorded": recorded,
                            "local": str(local), "depth": depth, "problems": problems})
            if not problems:
                visit(local, depth + 1)

    visit(Path(run_dir), 0)
    return reports


def chain_problems(run_dir: str | Path, path_map: PathMap | None = None) -> list[str]:
    """Own-file problems of ``run_dir``, else every problem of its dependency chain."""
    own = verify_files(run_dir)
    if own:
        return own
    return [f"{r['role']} of {r['of']} at {r['local']}: {p}"
            for r in dependency_reports(run_dir, path_map) for p in r["problems"]]


def resume_chain(run_dir: str | Path, path_map: PathMap | None = None) -> list[Path]:
    """The run and the folders it resumed from, oldest first (located via the resume receipt,
    mapped if a ``PathMap`` is given)."""
    path_map = path_map or PathMap()
    chain, current, seen = [], Path(run_dir), set()
    while True:
        key = current.resolve()
        if key in seen:
            raise ValueError(f"resume chain loops at {current}")
        seen.add(key)
        chain.append(current)
        job = read_json(current / "job.json")
        if job.get("kind") != "run-one" or not job.get("resume_from"):
            break
        receipts = [d for d in (read_dependencies(current) or []) if d.get("role") == "resume_from"]
        current = path_map.resolve(receipts[0]["resolved"] if len(receipts) == 1 else job["resume_from"])
    return list(reversed(chain))


def trajectory_steps(run_dir: str | Path, path_map: PathMap | None = None) -> list[dict]:
    steps: list[dict] = []
    for folder in resume_chain(run_dir, path_map):
        steps += read_jsonl(folder / STEPS)
    return steps


def check_trajectory(steps: list[dict], plan: StreamPlan, last_step: int) -> list[str]:
    if [s["step"] for s in steps] != list(range(1, last_step + 1)):
        return [f"recorded steps are not exactly 1..{last_step}"]
    problems: list[str] = []
    by_epoch: dict[int, list[str]] = {}
    for record, (step, epoch, rows) in zip(steps, plan.iterate(1, last_step)):
        if set(record["rows"]) & plan.removed:
            problems.append(f"step {step}: a removed row was trained")
            break
        if record["rows"] != rows or record["epoch"] != epoch:
            problems.append(f"step {step}: trained rows differ from the frozen stream")
            break
        by_epoch.setdefault(epoch, []).extend(rows)
    retained = plan.retained_rows()
    for epoch in range(last_step // plan.steps_per_epoch):
        if sorted(by_epoch.get(epoch, [])) != retained:
            problems.append(f"epoch {epoch}: retained rows were not each trained exactly once")
    return problems


def verify_run(run_dir: str | Path, prepared_dir: str | Path | None = None,
               path_map: PathMap | None = None) -> dict:
    """Own files, dependency chain and (run-one with ``prepared_dir``) stream, reported
    separately; ``complete`` only if every performed check passed."""
    run_dir, path_map = Path(run_dir), path_map or PathMap()
    own = verify_files(run_dir)
    try:
        job = read_json(run_dir / "job.json")
    except (OSError, ValueError):
        job = {}
        own = own + ["job.json missing or unreadable"]
    kind = job.get("kind")
    deps = dependency_reports(run_dir, path_map)
    dep_problems = [f"{r['role']} of {r['of']} at {r['local']}: {p}" for r in deps for p in r["problems"]]
    stream_problems: list[str] = []
    stream_checked = False
    if prepared_dir is not None and kind == "run-one" and not own and not dep_problems:
        stream_checked = True
        recipe = read_json(run_dir / "identity.json")["recipe"]
        prepared = load_prepared(prepared_dir, job["manifest_sha256"])
        if is_edit_arm(job["arm"]):        # the run's own copy of its edit file, checked against the arm
            from .edits import EDIT_FILE, arm_of, parse_edit

            data = (run_dir / EDIT_FILE).read_bytes()
            if arm_of(data) != job["arm"]:
                raise ValueError(f"{run_dir / EDIT_FILE} does not hash to the run's arm")
            edit = parse_edit(data, prepared)
            plan = make_plan(prepared.corpus, edit.removed, job["seed"], recipe["train"]["micro_batch"],
                             recipe["train"]["grad_accum"], edit.added_ids, edit.sha256)
        else:
            plan = make_plan(prepared.corpus, prepared.removed_rows(job["split"], job["arm"]),
                             job["seed"], recipe["train"]["micro_batch"], recipe["train"]["grad_accum"])
        last = read_complete(run_dir)["checkpoints"][job["target_checkpoint"]]["step"]
        stream_problems = check_trajectory(trajectory_steps(run_dir, path_map), plan, last)
    problems = own + dep_problems + stream_problems
    return {"run_dir": str(run_dir), "kind": kind,
            "own_files": {"complete": not own, "problems": own},
            "dependency_chain": {"complete": not dep_problems, "dependencies": deps},
            "stream": {"checked": stream_checked, "problems": stream_problems},
            "path_map": path_map.describe(), "complete": not problems, "problems": problems}


def compare_generations(first: str | Path, second: str | Path, checkpoint: str) -> dict:
    """Agreement between two complete evaluations of the same prompts (e.g. batched versus
    one prompt per batch, or two generation ceilings): identical outputs and stop reasons,
    where outputs first diverge, and guard label agreement. Counts only, no text."""
    folders = [Path(run) for run in (first, second)]
    for folder in folders:
        problems = verify_files(folder)
        if problems:
            raise ValueError(f"{folder} is not complete: {problems[:3]}")
    gens = [read_jsonl(f / "eval" / checkpoint / "generations.jsonl") for f in folders]
    guards = [{g["prompt_id"]: g for g in read_jsonl(f / "eval" / checkpoint / "guard.jsonl")} for f in folders]
    if [r["prompt_id"] for r in gens[0]] != [r["prompt_id"] for r in gens[1]]:
        raise ValueError("the evaluations cover different prompts")
    out: dict[str, dict] = {}
    for kind in sorted({r["kind"] for r in gens[0]}):
        pairs = [(a, b) for a, b in zip(*gens) if a["kind"] == kind]
        divergence = []
        for a, b in pairs:
            if a["output_ids"] != b["output_ids"]:
                shared = min(len(a["output_ids"]), len(b["output_ids"]))
                divergence.append(next((i for i in range(shared) if a["output_ids"][i] != b["output_ids"][i]),
                                       shared))
        labels = [(guards[0][a["prompt_id"]], guards[1][b["prompt_id"]]) for a, b in pairs]
        out[kind] = {"n": len(pairs),
                     "identical_outputs": sum(a["output_ids"] == b["output_ids"] for a, b in pairs),
                     "identical_stop_reasons": sum(a["stop_reason"] == b["stop_reason"] for a, b in pairs),
                     "first_divergence_token": sorted(divergence),
                     "guard_label_agreement": sum((x["valid"], x["safety"], x["refusal"])
                                                  == (y["valid"], y["safety"], y["refusal"]) for x, y in labels)}
    return {"first": str(folders[0]), "second": str(folders[1]), "checkpoint": checkpoint, "by_kind": out}
