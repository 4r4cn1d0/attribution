"""The regression digest of group-removal and a0 runs (ENGINEERING FIXTURES on CPU).

``digest(out_root)`` reduces a calibration tree to what must not change when the engine gains
edit arms: per unit the job (without ``code_sha256``, the running code's identity, which any code
change alters by design), the stream plan, every trained step's rows, epoch and losses (without
its seconds), the saved states byte for byte, the state records (without seconds), every
evaluation file byte for byte except the timed summary (compared without its seconds), and the
registry's trajectory keys. ``golden/removal-arms-8dd630c.json`` was written by this function
from the code at commit 8dd630c (before any headroom change); the regression test compares the
current code's digest with it."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

TIMED = {"seconds", "train_seconds", "elapsed_s", "start_s", "end_s", "start_utc", "end_utc", "updated_utc",
         "completed_utc", "utc"}


def _strip(value):
    if isinstance(value, dict):
        return {k: _strip(v) for k, v in value.items() if k not in TIMED}
    if isinstance(value, list):
        return [_strip(v) for v in value]
    return value


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def unit_digest(folder: Path) -> dict:
    job = json.loads((folder / "job.json").read_text())
    job.pop("code_sha256", None)
    resume = job.get("resume_from")
    job["resume_from"] = None if resume is None else Path(resume).name     # where the tree lives is not science
    plan, steps = folder / "plan.json", folder / "steps.jsonl"      # an init-only unit trains no step
    out = {"job": _canonical(job),
           "plan": _canonical(json.loads(plan.read_text())) if plan.exists() else "absent",
           "steps": _canonical([_strip(json.loads(line)) for line in steps.read_text().splitlines()])
           if steps.exists() else "absent",
           "states": {}, "eval": {}}
    for state in sorted((folder / "states").iterdir()):
        record = _strip(json.loads((state / "state.json").read_text()))
        out["states"][state.name] = {"state": _canonical(record),
                                     **{p.name: _sha(p.read_bytes()) for p in sorted(state.glob("*.safetensors"))}}
    for path in sorted((folder / "eval").rglob("*")) if (folder / "eval").is_dir() else []:
        if path.is_file():
            name = path.relative_to(folder / "eval").as_posix()
            data = path.read_bytes()
            if path.name == "summary.json":
                out["eval"][name] = _canonical(_strip(json.loads(data)))
            elif path.suffix == ".jsonl" and any('"seconds"' in line for line in data.decode().splitlines()[:3]):
                out["eval"][name] = _canonical([_strip(json.loads(line)) for line in data.decode().splitlines()])
            else:
                out["eval"][name] = _sha(data)
    return out


def digest(out_root: str | Path) -> dict:
    out_root = Path(out_root)
    units = {p.name: unit_digest(p) for p in sorted(out_root.iterdir()) if p.is_dir()}
    registry = [json.loads(line)["key"] for line in (out_root / "registry.jsonl").read_text().splitlines()]
    return {"units": units, "registry": _canonical(registry)}


def run_fixture_matrix(base: Path) -> dict:
    """calibrate a0 and one development group at seed 1101 through every checkpoint, with the dev
    bank evaluated at each, on the engine fixtures; returns the digest."""
    import ss_fixtures as fx

    from experiments.safety_selection import runner
    from experiments.safety_selection.prepare import load_prepared, read_manifest

    prepared, sha = fx.prepare_dir(base / "prepared")
    group = sorted(load_prepared(prepared, sha).groups["dev"])[0]
    session = runner.Session(fx.recipe(), fx.fixture_loaders())
    runner.calibrate(prepared_dir=prepared, out_root=base / "out", session=session, arms=["a0", group], seeds=[1101])
    return {"group": group, "manifest_sha256": read_manifest(prepared)[1], **digest(base / "out")}
