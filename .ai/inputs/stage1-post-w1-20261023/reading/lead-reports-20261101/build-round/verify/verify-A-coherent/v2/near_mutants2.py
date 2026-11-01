"""Verifier 2's near mutants of the D-5 code (not in the spec): each is applied to a copy of ws-a's scripts/stage1_s1
under a scratch folder and the two D-5 test files run on the copy without -x, with the runner's rule (killed = exit 1
with >= 1 failure and 0 errors; survived = exit 0; anything else invalid). ws-a is never changed.

    python -B near_mutants2.py <scratch folder> [ids]
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1] / "ws-a"
RI = Path("scripts/stage1_s1/reading_input")
PY = sys.executable

MUTANTS = {
    "N1-reading-version": ("sg_coherent.py", 'doc.get("kind") != B16_KIND or doc.get("version") != 1 or \\\n',
                           'doc.get("kind") != B16_KIND or \\\n'),
    "N2-delta-4pp": ("sg_coherent.py", 'level, delta = level_per_comparison(), float(cfg["margin"]["delta_pp"])',
                     'level, delta = level_per_comparison(), float(cfg["margin"]["delta_sensitivity_pp"])'),
    "N3-numeric-no-arith": ("sg_coherent.py", "NUMERIC = (Refusal, ValueError, ArithmeticError)",
                            "NUMERIC = (Refusal, ValueError)"),
    "N4-part-words-only": ("sg_coherent.py", '            elif rec["differs_from_primary"]:\n',
                           '            elif rec["u_part_words_differ"]:\n'),
    "N5-small-cell-dropped": ("sg_coherent.py", "    if big_n == 0:\n        return None\n",
                              "    if big_n < 3:\n        return None\n"),
    "N6-two-seeds-not-computable": ("sg_coherent.py", "        if len(seeds) < 2:\n", "        if len(seeds) < 3:\n"),
    "N7-g2-common-of-values": ("sg_coherent.py",
                               "g2_pair_counts(counts, c, m, dsg.common_seeds(c, m))})",
                               "g2_pair_counts(counts, c, m, [j for j in dsg.common_seeds(c, m) if int(counts[(c, j)][0].sum()) and int(counts[(m, j)][0].sum())])})"),
}


def junit(path: Path) -> dict:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    return {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors")}


def run(scratch: Path, mid: str | None) -> dict:
    folder = scratch / (mid or "baseline")
    if folder.exists():
        shutil.rmtree(folder)
    copy = folder / "copy"
    shutil.copytree(WS / "scripts" / "stage1_s1", copy / "scripts" / "stage1_s1",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if mid:
        fname, find, repl = MUTANTS[mid]
        target = copy / RI / fname
        text = target.read_text()
        if text.count(find) != 1:
            return {"id": mid, "outcome": "invalid", "reason": f"find occurs {text.count(find)} times"}
        target.write_text(text.replace(find, repl))
    env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=f"{copy}{os.pathsep}{WS}")
    xml = folder / "junit.xml"
    tests = copy / RI / "tests"
    proc = subprocess.run([PY, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-W", "ignore",
                           f"--basetemp={folder / 'bt'}", f"--junitxml={xml}", str(tests / "test_coherent.py"),
                           str(tests / "test_sg_coherent.py")], cwd=copy, env=env, capture_output=True, text=True,
                          timeout=900)
    c = junit(xml) if xml.is_file() else {"tests": 0, "failures": 0, "errors": 0}
    if proc.returncode == 0 and c["failures"] == 0 and c["errors"] == 0:
        outcome = "survived" if mid else "pass"
    elif proc.returncode == 1 and c["failures"] >= 1 and c["errors"] == 0:
        outcome = "killed" if mid else "fail"
    else:
        outcome = "invalid"
    shutil.rmtree(folder, ignore_errors=True)
    return {"id": mid or "baseline", "outcome": outcome, "exit": proc.returncode, **c}


def main():
    scratch = Path(sys.argv[1])
    ids = sys.argv[2].split(",") if len(sys.argv) > 2 else list(MUTANTS)
    print(run(scratch, None), flush=True)
    for mid in ids:
        print(run(scratch, mid), flush=True)


if __name__ == "__main__":
    main()
