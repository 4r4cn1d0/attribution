"""REQ-1: the frozen opening lexicon, pinned (standard library only).

scripts/stage1/lexicon/ holds byte-for-byte copies of the frozen lexicon: lexicon.json (SHA-256 bbbc71e9…) and its
classifier lexicon.py (SHA-256 5a27dd04…), copied from tmp/mechanism-recipes/ without any edit. Every stage-1 script
that needs a lexicon class gets ``classify`` from ``load()`` here, never from another copy. ``load()`` refuses unless:
both files hash to their pins; the module imports by path (it is never run as a script: its __main__ block writes
files); its ``lexicon_sha256()`` equals the JSON pin; and its ``lexicon_bytes()`` equal the JSON file's bytes.

Classes the stage-1 rules use: REFUSAL-OPENING (the S-pool, S4's keep rule, L1's layer-scan refusal count) and
DIRECT (the plant rows). The module also returns CAVEAT-OPENING and EMPTY. Messages carry hashes only, never a
lexicon phrase.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import sha256_bytes  # noqa: E402
from scripts.stage1.s1common import Refusal  # noqa: E402

LEXICON_DIR = HERE / "lexicon"
JSON_SHA256 = "bbbc71e9eebb62876430ffb5e0f54113c3818984b8369924b7bd2212c4c1ca17"
CLASSIFIER_SHA256 = "5a27dd040b74aa23fe09ac4dc95fb5913a4ccd327a67bb3caf5e667ff0432d1b"
CLASSES = ("REFUSAL-OPENING", "CAVEAT-OPENING", "DIRECT", "EMPTY")
USED_CLASSES = ("REFUSAL-OPENING", "DIRECT")

_CACHE: dict[Path, ModuleType] = {}


def load(directory: str | Path = LEXICON_DIR) -> ModuleType:
    """The pinned lexicon module (classify, lexicon_sha256, lexicon_bytes, _selftest), checked as the module doc
    states; cached per directory."""
    directory = Path(directory).resolve()
    if directory in _CACHE:
        return _CACHE[directory]
    json_bytes = (directory / "lexicon.json").read_bytes()
    code_bytes = (directory / "lexicon.py").read_bytes()
    if sha256_bytes(json_bytes) != JSON_SHA256:
        raise Refusal(f"lexicon.json hashes to {sha256_bytes(json_bytes)}, the pin is {JSON_SHA256}")
    if sha256_bytes(code_bytes) != CLASSIFIER_SHA256:
        raise Refusal(f"lexicon.py hashes to {sha256_bytes(code_bytes)}, the pin is {CLASSIFIER_SHA256}")
    spec = importlib.util.spec_from_file_location("stage1_pinned_lexicon", directory / "lexicon.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.lexicon_sha256() != JSON_SHA256 or module.lexicon_bytes() != json_bytes:
        raise Refusal("the lexicon module's own lexicon is not the pinned lexicon.json")
    _CACHE[directory] = module
    return module


def classify(text: str) -> str:
    """The pinned lexicon's class of a text (one of CLASSES)."""
    return load().classify(text)


def identity() -> dict:
    """The pins, for a provenance block."""
    return {"lexicon_json_sha256": JSON_SHA256, "lexicon_classifier_sha256": CLASSIFIER_SHA256,
            "directory": "scripts/stage1/lexicon"}
