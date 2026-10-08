"""The golden task record of brief multi-family-probe-engine-20261007, Item 1.0: what the kill-test task path
produces on the tiny fixtures, written with the engine before the family changes (``golden/kt-task-46064a7.json``)
and compared by ``test_ss_family_codec.py``. It pins Qwen-path behaviour that the older golden
(``removal-arms-8dd630c.json``) predates: ``prepare_task``, harm samples, ``--base-eval`` and the task query definition."""

from __future__ import annotations

import hashlib
from pathlib import Path

import removal_digest as rd
import ss_fixtures as fx

SAMPLES = {"count": 3, "temperature": 0.7, "top_p": 1.0}


def golden_record(base: Path) -> dict:
    from experiments.safety_selection import runner

    bank_dir, _ = fx.prepare_dir_v3(base / "prepared-v3")
    files = fx.prepared_task_files(bank_dir)
    prepared, _ = fx.prepare_task_dir(base / "prepared-kt", bank_dir)
    recipe = fx.recipe(**{"generation.harm_samples": dict(SAMPLES)})
    runner.calibrate(prepared_dir=prepared, out_root=base / "round1", session=runner.Session(recipe, fx.fixture_loaders()),
                     arms=["a0"], seeds=[1101], checkpoints=["e1"], base_eval=True)
    return {"kind": "kill-test task path golden (tiny fixtures)",
            "prepared_task_files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
            "units": {name: rd.unit_digest(base / "round1" / name) for name in ("1101-a0-init-a1", "1101-a0-e1-a1")}}
