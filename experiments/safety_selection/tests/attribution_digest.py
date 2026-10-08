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
