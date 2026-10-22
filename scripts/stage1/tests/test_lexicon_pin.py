"""REQ-1: the byte-for-byte lexicon copy and its pin loader (no lexicon phrase is printed or written)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from experiments.safety_selection.common import sha256_file
import experiments.safety_selection as _engine
from scripts.stage1 import lexicon_pin as lp
from scripts.stage1 import s1common as s1

ROOT = Path(_engine.__file__).resolve().parents[2]                  # the checkout that holds the engine


def test_the_copies_are_byte_identical_to_the_pinned_sources():
    for name, pin in (("lexicon.json", lp.JSON_SHA256), ("lexicon.py", lp.CLASSIFIER_SHA256)):
        copy = lp.LEXICON_DIR / name
        assert sha256_file(copy) == pin
        source = ROOT / "tmp" / "mechanism-recipes" / name
        if source.is_file():
            assert copy.read_bytes() == source.read_bytes()


def test_the_module_loads_with_its_own_lexicon_equal_to_the_pin():
    module = lp.load()
    assert module.lexicon_sha256() == lp.JSON_SHA256
    assert module.lexicon_bytes() == (lp.LEXICON_DIR / "lexicon.json").read_bytes()
    assert module._selftest() > 0
    assert lp.identity()["lexicon_json_sha256"] == lp.JSON_SHA256


def test_classify_returns_the_named_classes():
    labels = {lp.classify(t) for t in ("Here is a short poem about the sea and the gulls.",
                                       "I'm sorry, but I can't help with that request.", "")}
    assert labels <= set(lp.CLASSES)
    assert lp.classify("Here is a short poem about the sea and the gulls.") == "DIRECT"
    assert lp.classify("I'm sorry, but I can't help with that request.") == "REFUSAL-OPENING"
    assert set(lp.USED_CLASSES) <= set(lp.CLASSES)


@pytest.mark.parametrize("name", ["lexicon.json", "lexicon.py"])
def test_a_changed_byte_refuses(tmp_path, name):
    folder = tmp_path / "lex"
    shutil.copytree(lp.LEXICON_DIR, folder)
    target = folder / name
    target.chmod(0o644)
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(s1.Refusal, match="hashes to"):
        lp.load(folder)


def test_the_module_is_imported_never_run(tmp_path):
    folder = tmp_path / "lex"
    shutil.copytree(lp.LEXICON_DIR, folder)
    before = sorted(p.name for p in folder.iterdir())
    lp.load(folder)
    assert sorted(p.name for p in folder.iterdir() if p.name != "__pycache__") == before   # __main__ would write files
