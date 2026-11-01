"""The regression digest of the DEFAULT attribution path (ENGINEERING FIXTURES on CPU; GI III round 6, S5).

``golden_record(base)`` prepares the fixture data, trains a0 seed 1101 to e1 and continues it to e3 with the default
fixture recipe (per-example loss, constant rate), runs ``attributes`` on every development group, and reduces the
outputs to their science: rows.jsonl, groups.json and queries.json (without seconds), byte-for-byte canonical, plus
every row's per-checkpoint scores as exact floats. ``golden/attribution-default-8c026ee.json`` was written by this
function from the code at commit 8c026ee (engine 552538748acec1a8…) BEFORE any round-6 change; the regression test
compares the current code's record with it."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import removal_digest as rd
import ss_fixtures as fx

from experiments.safety_selection import runner
from experiments.safety_selection.prepare import load_prepared


def golden_record(base: Path) -> dict:
    import test_ss_runner as tr
    prepared_dir, digest = fx.prepare_dir(base / "prepared")
    recipe = fx.recipe()
    e = SimpleNamespace(root=base, prepared=prepared_dir, sha=digest, recipe=recipe,
                        session=runner.Session(recipe, fx.fixture_loaders()))
    e.view = load_prepared(prepared_dir, digest, banks=("dev",))
    e.direct = runner.run_one(tr.run_job(e, target_checkpoint="e1", evaluate_bank=None), prepared_dir=prepared_dir,
                              out_dir=base / "direct", session=e.session)
    e.to_e3 = runner.run_one(tr.run_job(e, target_checkpoint="e3", evaluate_bank=None, resume_from=e.direct["run_dir"]),
                             prepared_dir=prepared_dir, out_dir=base / "e3", session=e.session)
    result = runner.attributes(tr.attr_job(e), prepared_dir=prepared_dir, out_dir=base / "attr", session=e.session)
    folder = Path(result["run_dir"])
    rows = [rd._strip(json.loads(line)) for line in (folder / "rows.jsonl").read_text().splitlines()]
    return {"rows": rd._canonical(rows),
            "groups": rd._canonical(rd._strip(json.loads((folder / "groups.json").read_text()))),
            "queries": rd._canonical(rd._strip(json.loads((folder / "queries.json").read_text()))),
            "optimizer_steps": result["optimizer_steps"],
            "scores": {r["row_id"]: {c: [p["cosine"], p["adam_score"], p["dot"]] for c, p in r["per_checkpoint"].items()}
                       for r in rows}}


# ----- Gate B A0: the attributes result dict (brief gate-b-engine-kit-reading-20261008, A0 item 2) ---------------------

TOKEN_MEAN = {"train.loss_weighting": "token_mean"}       # completed with the loss text in _token_mean_recipe()
RUN_VARYING = {"attribution_seconds", "complete_sha256", "state_sha256",   # timing, and hashes of timed records
               "code_sha256"}                                                # the engine identity (as removal_digest)


def _token_mean_recipe() -> dict:
    from experiments.safety_selection.config import LOSS_TOKEN_MEAN
    return {**TOKEN_MEAN, "train.loss": LOSS_TOKEN_MEAN}


def _stable(value, base: str):
    """The record without its timed or run-varying fields or the engine identity, and with the run folder written as
    <base>: what stays is the science (fingerprints, steps, scores, losses, costs in rows and tokens)."""
    if isinstance(value, dict):
        return {k: _stable(v, base) for k, v in value.items() if k not in rd.TIMED and k not in RUN_VARYING}
    if isinstance(value, list):
        return [_stable(v, base) for v in value]
    if isinstance(value, str) and base in value:
        return value.replace(base, "<base>")
    return value


def _attributed(base: Path, overrides: dict) -> tuple[dict, Path]:
    import test_ss_runner as tr
    prepared_dir, digest = fx.prepare_dir(base / "prepared")
    recipe = fx.recipe(**overrides)
    e = SimpleNamespace(root=base, prepared=prepared_dir, sha=digest, recipe=recipe,
                        session=runner.Session(recipe, fx.fixture_loaders()))
    e.view = load_prepared(prepared_dir, digest, banks=("dev",))
    e.direct = runner.run_one(tr.run_job(e, target_checkpoint="e1", evaluate_bank=None), prepared_dir=prepared_dir,
                              out_dir=base / "direct", session=e.session)
    e.to_e3 = runner.run_one(tr.run_job(e, target_checkpoint="e3", evaluate_bank=None, resume_from=e.direct["run_dir"]),
                             prepared_dir=prepared_dir, out_dir=base / "e3", session=e.session)
    result = runner.attributes(tr.attr_job(e), prepared_dir=prepared_dir, out_dir=base / "attr", session=e.session)
    return result, Path(result["run_dir"])


def result_record(base: Path) -> dict:
    """The `attributes` result dict on the default fixture recipe; and rows, groups, queries and the result dict on
    the token-mean fixture recipe (constant rate). ``golden/attribution-result-e49a978c.json`` was written by this
    function from the code at commit 442f315 (engine e49a978c…) BEFORE any Gate B change."""
    out = {}
    for name, overrides in (("default", {}), ("token_mean", _token_mean_recipe())):
        root = base / name
        result, folder = _attributed(root, overrides)
        record = {"result": _stable(result, str(root))}
        if name == "token_mean":
            rows = [_stable(json.loads(line), str(root)) for line in (folder / "rows.jsonl").read_text().splitlines()]
            record.update(rows=rows, groups=_stable(json.loads((folder / "groups.json").read_text()), str(root)),
                          queries=_stable(json.loads((folder / "queries.json").read_text()), str(root)))
        out[name] = record
    return out
