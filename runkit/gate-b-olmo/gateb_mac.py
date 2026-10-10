"""Mac-side helpers shared by the Gate B kit's scripts (administrative; stdlib only; never contacts a service).

The plan file, the operator log (operator-actions.jsonl), whether a host is launched, the complete attempts in the
pulled trees, and the one environment field set, ``compared_fields``, loaded by path from scripts/gate_b_reading.py
(brief B5 [V20]; Part C owns that file, the kit only imports the function).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PLAN = HERE / "plan.json"
READING = ROOT / "scripts" / "gate_b_reading.py"
OPERATOR_LOG = HERE / "operator-actions.jsonl"
EXPECTED_FIXTURE = HERE / "expected-fixture-gateb.json"   # wave 0a's first host records it (orchestrate record_first)


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load_plan() -> dict:
    return json.loads(PLAN.read_text())


def save_plan(plan: dict) -> None:
    PLAN.write_text(json.dumps(plan, indent=1, sort_keys=True) + "\n")


def operator_action(record: dict) -> None:
    """Append one record (ids, counts and hashes only) to operator-actions.jsonl."""
    with open(OPERATOR_LOG, "a") as handle:
        handle.write(json.dumps({"utc": utc(), **record}, sort_keys=True) + "\n")


def reading_module(path: pathlib.Path | None = None):
    """scripts/gate_b_reading.py, loaded by path (as the family-probe plan tool loads family_probe_reading.py)."""
    path = pathlib.Path(path or READING)
    spec = importlib.util.spec_from_file_location("gate_b_reading_for_kit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compared_fields(environment: dict, lock_sha256: str | None, policy: dict | None) -> dict:
    return reading_module().compared_fields(environment, lock_sha256, policy)


def launched(host: str) -> bool:
    """A host is launched once host.py create wrote its intent (or its pod record): defer never edits it."""
    folder = HERE / "hosts" / host
    return (folder / "create-intent.json").exists() or (folder / "pod.json").exists()


def complete_runs() -> dict:
    """Every complete attempt in the pulled trees: (arm, seed) of a run-one unit at e1, and ("attributes", seed) of an
    attributes unit -> [{host, unit, complete_sha256, path}] (attempts on two pods are both listed, never merged)."""
    out: dict = {}
    for complete in sorted((HERE / "retrieved").glob("*/tree/**/COMPLETE.json")):
        unit = complete.parent
        job_file = unit / "job.json"
        if not job_file.is_file():
            continue
        job = json.loads(job_file.read_text())
        if job.get("kind") == "run-one" and job.get("target_checkpoint") == "e1":
            key = (job.get("arm"), job.get("seed"))
        elif job.get("kind") == "attributes":
            key = ("attributes", job.get("seed"))
        else:
            continue
        host = complete.relative_to(HERE / "retrieved").parts[0]
        out.setdefault(key, []).append({"host": host, "unit": str(unit.relative_to(HERE / "retrieved" / host / "tree")),
                                        "complete_sha256": sha(complete), "path": str(unit)})
    return out
