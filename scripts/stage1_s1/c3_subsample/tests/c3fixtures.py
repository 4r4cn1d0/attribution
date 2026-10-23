"""Shared helpers for the C3 tests: synthetic prepared folders built exactly as the engine's own tests build them
(ss_fixtures.prepare_dir_v3, then prepare_task_dir, as engine Y's test_ss_roundy_confirmation.py does), with the dev
bank's harm and over-refusal counts set through the fixture config's ``edit`` hook; a dev-bank rewriter that keeps
the manifest consistent; the committed settings with a synthetic pin; and the child-process runner of engine Y's Y2
checks (ycheck.py). Synthetic data only; nothing real is read."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from experiments.safety_selection.common import canonical_json, jsonl_bytes, sha256_bytes
from scripts.stage1_s1.c3_subsample import write_c3_subsample as wc

import ss_fixtures as fx

HERE = Path(__file__).resolve().parent
ENGINE_Y_ROOT = Path(os.environ.get(
    "C3_ENGINE_Y_ROOT",
    "/Users/spiderishi/Coding/attribution/.claude/worktrees/kind-hawking-a6ce04/tmp/claude-workspaces/"
    "stage1-integrate-20261017/ws-y"))
EXPECTED_ENGINE_Y = "34bfd28879fdefc5d6605cb73a707d1edd2ec5d102b4b86c0026bc6ac36969f6"   # addendum section 15
DEV = "banks/dev.jsonl"


def build_p(root: Path, harm: int | None = None, over: int | None = None) -> tuple[Path, str]:
    """A synthetic task prepared folder; ``harm``/``over`` set the dev bank's harm and over-refusal counts (the
    fixture's own is 2 and 2, so 12 dev items; 4 and 4 give 16; 5 and 4 give 17)."""
    def edit(config):
        banks = config["eval_banks"]
        if harm is not None:
            banks["harm"]["dev"] = harm
        if over is not None:
            banks["overrefusal"]["dev"] = over
            banks["overrefusal"]["per_source"]["xstest"]["dev"] = over - over // 2
            banks["overrefusal"]["per_source"]["orbench_hard"]["dev"] = over // 2

    bank_dir, _ = fx.prepare_dir_v3(root / "v3", edit=edit if (harm, over) != (None, None) else None)
    return fx.prepare_task_dir(root / "p", bank_dir)


def dev_lines(folder: Path) -> list[dict]:
    """The dev bank's items in file order, parsed independently of the writer."""
    return [json.loads(line) for line in (folder / DEV).read_bytes().decode("utf-8").split("\n") if line]


def rewrite_dev(src: Path, dst: Path, transform) -> tuple[Path, str]:
    """A copy of src whose dev bank is transform(items) (file order kept as returned), with the manifest's hash of the
    dev bank, manifest.json and manifest.sha256 rewritten to match."""
    shutil.copytree(src, dst)
    items = transform(copy.deepcopy(dev_lines(src)))
    data = jsonl_bytes(items)
    (dst / DEV).write_bytes(data)
    manifest = json.loads((dst / "manifest.json").read_bytes())
    manifest["files"][DEV] = sha256_bytes(data)
    mbytes = canonical_json(manifest)
    (dst / "manifest.json").write_bytes(mbytes)
    digest = sha256_bytes(mbytes)
    (dst / "manifest.sha256").write_text(digest + "\n", encoding="ascii")
    return dst, digest


def committed() -> dict:
    return json.loads(wc.SETTINGS_PATH.read_bytes())


def settings_for(sha: str, **changes) -> dict:
    """The committed settings with P's pin replaced by a synthetic manifest's hash (and any other changes)."""
    s = copy.deepcopy(committed())
    s["prepared_manifest_sha256"] = sha
    s.update(changes)
    return s


def write_settings(path: Path, settings: dict) -> str:
    data = canonical_json(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return sha256_bytes(data)


def build(folder: Path, sha: str, **changes) -> tuple[bytes, bytes]:
    return wc.build(prepared_root=folder, settings=settings_for(sha, **changes), settings_sha256="5" * 64)


def write_doc(path: Path, doc: dict | bytes) -> tuple[str, Path]:
    data = doc if isinstance(doc, bytes) else canonical_json(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return "subsample-" + hashlib.sha256(data).hexdigest(), path


def run_ycheck(work: Path, folder: Path, sha: str, cases: list[dict]) -> dict:
    """Engine Y's checks in a child process (python -B -I: no PYTHONPATH, no script folder on sys.path), so that
    nothing of engine X or of the C3 package is imported there."""
    work.mkdir(parents=True, exist_ok=True)
    request, result = work / "request.json", work / "result.json"
    request.write_text(json.dumps({"engine_y": str(ENGINE_Y_ROOT), "folder": str(folder), "sha": sha,
                                   "cases": cases}))
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
    env.update(PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    proc = subprocess.run([sys.executable, "-B", "-I", str(HERE / "ycheck.py"), str(request), str(result)],
                          cwd=work, env=env, capture_output=True, text=True, timeout=540)
    if proc.returncode != 0 or not result.exists():
        raise AssertionError(f"ycheck exited {proc.returncode}: {proc.stderr[-3000:]}")
    return json.loads(result.read_text())
