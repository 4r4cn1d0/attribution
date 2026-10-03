"""Pytest setup for the recovery-safeguard tests: the project root and the engine's test folder
(its ENGINEERING FIXTURES, ``ss_fixtures``) on sys.path; fakes live in dur_fixtures.py. Nothing
here is a scientific result, and no test touches a network, a provider or a GPU."""

from __future__ import annotations

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parents[2]
ENGINE_TESTS = ROOT / "experiments" / "safety_selection" / "tests"
for path in (ROOT, ENGINE_TESTS, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
