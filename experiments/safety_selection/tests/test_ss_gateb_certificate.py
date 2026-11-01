"""The Gate B certificate route (brief gate-b-engine-kit-reading-20261008, A1): every REVIEWED symbol of engine X is its
e49a978c text with exactly the listed lines inserted (no line edited or removed), or a new symbol absent from both
stored bases; REVIEWED holds exactly what certify refuses without it; a REVIEWED entry can never name a record key, so
it cannot certify a new global writer; and scripts/evaluation_path.py still runs under an older system python3."""

from __future__ import annotations

import ast
import difflib
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIGS = ROOT / "experiments/safety_selection/configs"
ENGINE = ROOT / "experiments/safety_selection"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL = load("evaluation_path_gateb", ROOT / "scripts" / "evaluation_path.py")
E49 = json.loads((CONFIGS / "evaluation-path-symbols-v2-e49a978c.json").read_text())
B552 = json.loads((CONFIGS / "evaluation-path-symbols-v2-55253874.json").read_text())


def text_of(file: str, symbol: str) -> str | None:
    """A symbol's text exactly as symbols_of hashes it (functions with their decorators; assignments by target)."""
    source = TOOL._Source((ENGINE / file).read_text(encoding="utf-8"))
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol:
            return TOOL._with_decorators(source, node)
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if ",".join(sorted({n.id for t in targets for n in ast.walk(t) if isinstance(n, ast.Name)})) == symbol:
                return source.segment(node)
    return None


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def without_inserted(text: str, inserted: list[str]) -> str:
    """The text with the inserted lines removed in order (the first match after the previous one); the base hash
    check below proves the result is the base text, so a repeated line cannot hide an edit."""
    lines, out, k = text.split("\n"), [], 0
    for line in lines:
        if k < len(inserted) and line == inserted[k]:
            k += 1
            continue
        out.append(line)
    assert k == len(inserted), "an inserted line is not in the symbol's text"
    return "\n".join(out)


@pytest.mark.parametrize("key", sorted(TOOL.REVIEWED))
def test_each_reviewed_symbol_is_its_base_with_only_lines_inserted(key):
    entry = TOOL.REVIEWED[key]
    file, symbol = key.split(":", 1)
    assert not symbol.startswith("<")                          # never a record or import key ([O1], [D9])
    assert set(entry) == {"base", "new", "inserted", "global_writer", "reason"} and entry["reason"]
    text = text_of(file, symbol)
    assert text is not None and sha(text) == entry["new"] == TOOL.symbols()[file][symbol]
    if entry["base"] is None:                                    # a new symbol: absent from both stored bases
        assert symbol not in E49.get(file, {}) and symbol not in B552.get(file, {}) and entry["inserted"] == []
    else:
        assert entry["base"] == E49[file][symbol] == B552[file][symbol]      # one base serves both pairs
        assert entry["inserted"] and sha(without_inserted(text, entry["inserted"])) == entry["base"]
    record = E49.get(file, {}).get(TOOL.GLOBAL_WRITES, "")
    assert entry["global_writer"] == (f",{symbol}," in f",{record},")


def test_reviewed_is_exactly_what_certify_refuses_without_it(monkeypatch):
    current = TOOL.symbols()
    monkeypatch.setattr(TOOL, "REVIEWED", {})
    refused = set(TOOL.certify(E49, current)["evaluation_path_symbols_changed"])
    monkeypatch.undo()
    assert refused == set(TOOL.REVIEWED)                       # no spare entry, none missing
    for file in current:                                       # every file's records unchanged at X
        for record in (TOOL.GLOBAL_WRITES, TOOL.SIDE_EFFECT_FREE):
            assert current[file][record] == E49[file][record], (file, record)
    assert TOOL.certify(E49, current)["evaluation_path_unchanged"]
    assert TOOL.certify(B552, current)["evaluation_path_unchanged"]


def test_a_reviewed_record_key_cannot_certify_a_new_global_writer(monkeypatch):
    """[O1]: a REVIEWED entry naming runner.py's <global_writes> (base = the stored record, new = a changed record)
    leaves certify refusing that record change."""
    new = json.loads(json.dumps(TOOL.symbols()))
    changed = E49["runner.py"][TOOL.GLOBAL_WRITES] + ",lock_record"
    new["runner.py"][TOOL.GLOBAL_WRITES] = changed
    monkeypatch.setitem(TOOL.REVIEWED, f"runner.py:{TOOL.GLOBAL_WRITES}",
                        {"base": E49["runner.py"][TOOL.GLOBAL_WRITES], "new": changed, "inserted": [],
                         "global_writer": False, "reason": "a forged entry"})
    out = TOOL.certify(E49, new)
    assert f"runner.py:{TOOL.GLOBAL_WRITES}" in out["evaluation_path_symbols_changed"]
    assert not out["evaluation_path_unchanged"]


def test_a_reviewed_entry_whose_hash_differs_is_refused(monkeypatch):
    key = sorted(k for k, e in TOOL.REVIEWED.items() if e["base"] is not None)[0]
    monkeypatch.setitem(TOOL.REVIEWED, key, {**TOOL.REVIEWED[key], "new": "0" * 64})
    assert key in TOOL.certify(E49, TOOL.symbols())["evaluation_path_symbols_changed"]
    monkeypatch.setitem(TOOL.REVIEWED, key, {**TOOL.REVIEWED[key], "base": "0" * 64})
    assert key in TOOL.certify(E49, TOOL.symbols())["evaluation_path_symbols_changed"]


def test_training_only_is_byte_identical_to_the_round_6_certificate():
    round6 = json.loads((CONFIGS / "evaluation-equivalence-round6-20261008.json").read_text())
    assert round6["training_only"] == {k: sorted(v) for k, v in TOOL.TRAINING_ONLY.items()}


def test_the_script_runs_under_an_older_system_python3(tmp_path):
    system = shutil.which("python3", path="/usr/bin:/bin")
    if system is None:
        pytest.skip("no system python3")
    version = subprocess.run([system, "-c", "import sys;print(sys.version_info[:2] < (3, 10))"], capture_output=True,
                             text=True).stdout.strip()
    if version != "True":
        pytest.skip("the system python3 is 3.10 or newer: the __future__ line is not exercised")
    done = subprocess.run([system, "-B", str(ROOT / "scripts" / "evaluation_path.py"), "symbols"], capture_output=True,
                          text=True, cwd=tmp_path, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
    assert done.returncode == 0, done.stderr[-500:]
    assert json.loads(done.stdout) == TOOL.symbols()
