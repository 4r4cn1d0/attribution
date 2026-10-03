"""Pytest setup for the decision-policy tests: the project root and the engine's test folder
(for its ENGINEERING FIXTURES, ``ss_fixtures``) on sys.path, and shared synthetic fixtures.
Nothing here is a scientific result."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ENGINE_TESTS = ROOT / "experiments" / "safety_selection" / "tests"
for path in (ROOT, ENGINE_TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from experiments.safety_decision_policy.common import read_json_strict  # noqa: E402

CONFIGS = ROOT / "experiments" / "safety_decision_policy" / "configs"


@pytest.fixture
def example_config() -> dict:
    return copy.deepcopy(read_json_strict(CONFIGS / "example-engineering.json"))


@pytest.fixture
def example_spec() -> dict:
    return copy.deepcopy(read_json_strict(CONFIGS / "example-dev-fit-spec.json"))
