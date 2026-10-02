"""Pytest fixtures for the safety-selection tests; builders live in ss_fixtures.py
(ENGINEERING FIXTURES only)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

import ss_fixtures as fx  # noqa: E402


@pytest.fixture(scope="module")
def prepared(tmp_path_factory) -> tuple[Path, str]:
    """(prepared folder, manifest hash) built once per test module from the fixture sources."""
    return fx.prepare_dir(tmp_path_factory.mktemp("prepared") / "prepared")


@pytest.fixture
def codec():
    return fx.fixture_codec()


@pytest.fixture
def tiny():
    """(model, named LoRA parameters) of the tiny random Qwen2 fixture."""
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    pytest.importorskip("peft")
    from experiments.safety_selection import engine as en

    model = fx.tiny_lora_model()
    return model, en.lora_parameters(model)
