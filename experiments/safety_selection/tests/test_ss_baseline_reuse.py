"""Baseline reuse across engine identities (GI III round 5): the engine's evaluation path is unchanged from 04eb83a3,
symbol by symbol (scripts/evaluation_path.py against the pinned base symbols), and the pinned evaluation-equivalence
certificate describes exactly this engine. A later engine change fails here until it is certified again."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from experiments.safety_selection.common import code_identity

ROOT = Path(__file__).resolve().parents[3]
CONFIGS = ROOT / "experiments/safety_selection/configs"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_evaluation_path_is_unchanged_from_04eb83a3_and_the_certificate_is_this_engines():
    ep = load("evaluation_path", ROOT / "scripts" / "evaluation_path.py")
    base_symbols = json.loads((CONFIGS / "evaluation-path-symbols-04eb83a3.json").read_text())
    base_identity = json.loads((CONFIGS / "engine-identity-04eb83a3.json").read_text())
    assert base_identity["sha256"] == "04eb83a3fca6fc77ae81d8975d52ae642f7efafb774759e01ca88b6c3fd51408"
    out = ep.certify(base_symbols, ep.symbols())
    assert out["evaluation_path_unchanged"], out["evaluation_path_symbols_changed"]
    certificate = json.loads((CONFIGS / "evaluation-equivalence-20261008.json").read_text())
    entry, = certificate["pairs"]
    now = code_identity()
    assert (entry["base_code_sha256"], entry["code_sha256"]) == (base_identity["sha256"], now["sha256"])
    differ = sorted(f for f in set(base_identity["files"]) | set(now["files"])
                    if base_identity["files"].get(f) != now["files"].get(f))
    assert entry["changed_files"] == differ
    assert entry["changed_symbols"] == out["changed"]
    assert certificate["training_only"] == {k: sorted(v) for k, v in ep.TRAINING_ONLY.items()}
    reading = load("family_probe_reading", ROOT / "scripts" / "family_probe_reading.py")
    assert reading.CERTIFICATE_SHA256 == hashlib.sha256((CONFIGS / "evaluation-equivalence-20261008.json").read_bytes()).hexdigest()


def test_the_symbol_inventory_flags_an_evaluation_change_and_allows_a_training_one(tmp_path):
    ep = load("evaluation_path", ROOT / "scripts" / "evaluation_path.py")
    base = {"engine.py": ep.symbols_of("def greedy_generate():\n    return 1\n\ndef train_step():\n    return 1\n"),
            "attribution.py": ep.symbols_of("X = 1\n")}
    training = {"engine.py": ep.symbols_of("def greedy_generate():\n    return 1\n\ndef train_step():\n    return 2\n"),
                "attribution.py": ep.symbols_of("X = 2\n")}
    assert ep.certify(base, training)["evaluation_path_unchanged"]
    evaluation = {**training, "engine.py": ep.symbols_of("def greedy_generate():\n    return 3\n\ndef train_step():\n    return 2\n")}
    out = ep.certify(base, evaluation)
    assert not out["evaluation_path_unchanged"] and out["evaluation_path_symbols_changed"] == ["engine.py:greedy_generate"]
    added = {**training, "scoring.py": ep.symbols_of("Y = 1\n")}
    assert ep.certify(base, added)["evaluation_path_symbols_changed"] == ["scoring.py:<whole file>"]
    imports = {**training, "runner.py": ep.symbols_of("from .attribution import X\n")}
    assert ep.certify({**base, "runner.py": ep.symbols_of("from .attribution import Y\n")}, imports)["evaluation_path_unchanged"]
    other = {**training, "runner.py": ep.symbols_of("from .scoring import X\n")}
    assert not ep.certify({**base, "runner.py": ep.symbols_of("from .scoring import Y\n")}, other)["evaluation_path_unchanged"]
