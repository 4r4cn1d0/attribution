"""No text in any sink (the gate_b judges' syntax-tree check, reused), no secret in the tool or the launch files, the
launch script and README blocks (zsh-safe), and no bytecode written beside the reused launcher."""
from __future__ import annotations

import ast
import pathlib
import re
import subprocess

import pytest
from conftest import HERE, TOOL, P, SP

GATE_B_TESTS = P.MAC_GATE_B / "tests/test_gate_b_judges.py"
LAUNCH_FILES = HERE.parent                                  # the dev folder or the launch folder (same layout)


def leak_checker():
    """text_names_in_sinks and its name sets, taken from the gate_b judges' tests by syntax tree (not imported)."""
    if not GATE_B_TESTS.is_file():
        pytest.skip("the gate_b judges' tests are absent")
    tree = ast.parse(GATE_B_TESTS.read_text(encoding="utf-8"))
    keep = [n for n in tree.body if (isinstance(n, ast.Assign) and any(
        getattr(t, "id", None) in ("TEXT_NAMES", "WHOLE_NAMES", "SINKS") for t in n.targets))
        or (isinstance(n, ast.FunctionDef) and n.name == "text_names_in_sinks")]
    assert len(keep) == 4
    ns = {"ast": ast}
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(GATE_B_TESTS), "exec"), ns)
    return ns["text_names_in_sinks"]


def test_the_checker_sees_leaks():
    check = leak_checker()
    for snippet in ("log(text=1)", 'print(r["response"])', 'log(event="x", response=r)', "print(prompt)",
                    'raise Refusal(f"x {answer}")'):
        assert check(snippet), snippet
    assert not check('log(event="progress", judged=n, of=len(todo))')


def test_no_text_names_in_any_tool_sink():
    check = leak_checker()
    found = {p.name: check(p.read_text(encoding="utf-8")) for p in sorted(TOOL.glob("*.py"))}
    assert len(found) == 9
    assert {k: v for k, v in found.items() if v} == {}


def test_no_row_text_attribute_in_any_sink():
    """The screen's own text-carrying names (Row.user_turn, Row.assistant_turn, ka item texts) never reach a sink."""
    names = {"user_turn", "assistant_turn", "instruction", "context", "rendered", "generated"}
    sinks = {"print", "log", "write", "Refusal", "SystemExit", "RuntimeError", "ValueError", "say"}
    bad = []
    for path in sorted(TOOL.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call):
                f = node.func
                name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
                if name in sinks:
                    for arg in [*node.args, *(k.value for k in node.keywords)]:
                        for n in ast.walk(arg):
                            ident = n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute) else None
                            if ident in names:
                                bad.append((path.name, node.lineno, ident))
    assert bad == []


def test_no_secret_in_the_tool_tests_or_launch_files():
    files = [p for p in LAUNCH_FILES.rglob("*") if p.is_file() and "__pycache__" not in p.parts
             and p.suffix in (".py", ".sh", ".md", ".txt")]
    assert len(files) >= 20
    for p in files:
        text = p.read_text(encoding="utf-8")
        hits = [n for n, pat in SP.JP.SECRET_PATTERNS.items() if pat.search(text)]
        assert hits == [], (p.name, hits)                  # the tests build their fake keys from parts


def test_launch_script_parses_and_its_settings():
    script = LAUNCH_FILES / "sp_fiction_screen.sh"
    if not script.is_file():
        pytest.skip("the launch script is not beside the tool")
    assert subprocess.run(["bash", "-n", str(script)], capture_output=True).returncode == 0
    text = script.read_text()
    assert "export PYTHONDONTWRITEBYTECODE=1" in text and '"$PY" -B' in text
    assert "env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN caffeinate -i" in text
    assert "tmp/family-probe-sp-fiction-screen" in text and "sp-fiction-screen-r" in text


def test_readme_zsh_blocks_start_with_setopt_and_hold_no_comment():
    readme = LAUNCH_FILES / "LAUNCH-README.md"
    if not readme.is_file():
        pytest.skip("LAUNCH-README.md is not beside the tool")
    blocks = re.findall(r"```zsh\n(.*?)```", readme.read_text(), re.DOTALL)
    assert len(blocks) >= 5
    for b in blocks:
        lines = b.strip("\n").splitlines()
        assert lines[0] == "setopt interactivecomments", lines[0]
        assert not [ln for ln in lines if ln.lstrip().startswith("#") or " #" in ln], b
        done = subprocess.run(["zsh", "-n", "-c", b], capture_output=True, text=True)
        assert done.returncode == 0, done.stderr


def test_no_bytecode_beside_the_reused_launcher():
    """The kits' pack refuses any untracked file under scripts/; -B and dont_write_bytecode keep the imported launcher's
    folders free of __pycache__ (git ignores it, but nothing of this tool may be left under scripts/)."""
    for folder in (P.MAC_GATE_B, P.MAC_GATE_B / "pod", P.MAC_GATE_B / "tests"):
        assert not list(folder.glob("__pycache__")), folder
    import sys
    assert sys.dont_write_bytecode is True
