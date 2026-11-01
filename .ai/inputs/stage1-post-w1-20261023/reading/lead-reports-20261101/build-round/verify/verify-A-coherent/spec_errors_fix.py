"""The builder's 25 new spec entries under the official runner's classification (killed = exit 1, >= 1 failure, 0
errors; any error = invalid), run on the two new test files only and WITHOUT -x (the official runner runs whole test
files with no -x). A fixture error here means the official run of that mutant is invalid too (errors only add).

    python -B spec_errors.py <ws> <scratch> <id,id,...>
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    ws, scratch, ids = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3].split(",")
    spec = json.loads((ws / "scripts/stage1_s1/reading_input/mutation/mutants_reading_input.json").read_text())
    by_id = {m["id"]: m for m in spec["mutants"]}
    py = sys.executable
    for mid in ids:
        m = by_id[mid]
        folder = scratch / mid
        shutil.rmtree(folder, ignore_errors=True)
        copy = folder / "copy"
        shutil.copytree(ws / "scripts/stage1_s1", copy / "scripts/stage1_s1",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        p = copy / "scripts/stage1_s1/reading_input" / m["file"]
        t = p.read_text()
        assert t.count(m["find"]) == 1, mid
        p.write_text(t.replace(m["find"], m["replace"]))
        if os.environ.get("FIX_BUILT"):                     # the proposed fix: the fixture returns None, the tests fail
            tc = copy / "scripts/stage1_s1/reading_input/tests/test_coherent.py"
            old = "    assert main(s.args(out, rec, overlap=False) + [\"--coherent-out\", str(cnt)]) == 0\n"
            new = "    if main(s.args(out, rec, overlap=False) + [\"--coherent-out\", str(cnt)]) != 0:\n        return None\n"
            src = tc.read_text()
            assert src.count(old) == 1
            tc.write_text(src.replace(old, new))
        env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=f"{copy}{os.pathsep}{ws}")
        tests = [str(copy / "scripts/stage1_s1/reading_input/tests" / f) for f in ("test_coherent.py", "test_sg_coherent.py")]
        junit = folder / "junit.xml"
        t0 = time.monotonic()
        r = subprocess.run([py, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-W", "ignore",
                            f"--basetemp={folder / 'bt'}", f"--junitxml={junit}", *tests], cwd=copy, env=env,
                           capture_output=True, text=True, timeout=590)
        fails = errs = 0
        erroring = []
        if junit.is_file():
            root = ET.parse(junit).getroot()
            for suite in ([root] if root.tag == "testsuite" else list(root.iter("testsuite"))):
                fails += int(suite.get("failures", 0))
                errs += int(suite.get("errors", 0))
                for case in suite.iter("testcase"):
                    if case.find("error") is not None:
                        erroring.append(case.get("name"))
        outcome = ("killed" if r.returncode == 1 and fails >= 1 and errs == 0 else
                   "survived" if r.returncode == 0 and fails == 0 and errs == 0 else "INVALID")
        print(f"{mid:<34} {outcome:<9} exit {r.returncode} failures {fails:>3} errors {errs:>3} "
              f"{time.monotonic() - t0:5.1f} s {('first errors: ' + ', '.join(erroring[:3])) if erroring else ''}",
              flush=True)
        shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
    main()
