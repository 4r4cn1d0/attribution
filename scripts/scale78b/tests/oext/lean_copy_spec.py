"""The listed substitutions that make scripts/scale78b/lean_eval_job_78b.py from scripts/stage1_s1/lean_eval_job.py
(DES E4's copy route; the scripts/stage1_s1/oext_unit_y.py precedent). Each find text occurs exactly once in the 1B
file; test_oext_78b_lean.py rebuilds the copy from the 1B file by these substitutions and compares the bytes. Standard
library only."""

SOURCE = "scripts/stage1_s1/lean_eval_job.py"
SOURCE_SHA256 = "82461c13d91471729bb036da6565bcb0555885c4b2347d91cd93abcebd9ca46a"
COPY = "scripts/scale78b/lean_eval_job_78b.py"

HEAD = '''"""7-8B COPY (R1 Track O; DES E4's copy route; the build rulings B-3 and O3 of 8 Nov 2026). This file is
scripts/stage1_s1/lean_eval_job.py with the changes below and nothing else (a test rebuilds it from the 1B file byte
for byte by the five listed substitutions of scripts/scale78b/tests/oext/lean_copy_spec.py):
  1. this paragraph;
  2. oext_eval is imported as scripts.stage1_s1.oext_eval (the S1 package's file, unchanged), not by this folder's name;
  3. the O-ext settings path that the settings' section "oext" must name is the module global OEXT_SETTINGS_PATH (the
     form of scripts/stage1_s1/oext_unit.py:75, :146), not a literal: the 1B literal (lean_eval_job.py:229) would make
     a 7-8B settings file name scripts/stage1_s1/settings/oext_eval.json while the run reads the family's file, and no
     record or settings file may name a file the run did not read (GXB O3);
  4. the parser's program name is this file's path.
It runs only through scripts/scale78b/oext_78b.py lean, which sets SETTINGS_PATH, SETTINGS_SHA256 and
OEXT_SETTINGS_PATH to the family's files (settings/lean_eval_job__<family>.json, settings/oext_eval__<family>.json,
pinned by settings/OEXT-78B.json) for the call and restores them. Run alone, it refuses (no settings file lies at its
default path). Every rule, check, output and exit code is the 1B file's; its records name this file as their script
(s1common.provenance), the file that ran.

B17: the lean-evaluation job that measures c0 (stage-1 S1 package; CPU-testable with fixtures, CUDA on the pod).
'''

SUBSTITUTIONS = [
    ('"""B17: the lean-evaluation job that measures c0 (stage-1 S1 package; CPU-testable with fixtures, CUDA on the '
     'pod).\n', HEAD),
    ('oe = importlib.import_module(f"scripts.{HERE.name}.oext_eval")      # this package\'s own copy (also in the '
     'mirror)\n',
     'oe = importlib.import_module("scripts.stage1_s1.oext_eval")      # 7-8B copy: the S1 package\'s file, unchanged\n'),
    ('SETTINGS_NAME = "lean_eval_job"\n',
     'SETTINGS_NAME = "lean_eval_job"\n'
     'OEXT_SETTINGS_PATH = "scripts/stage1_s1/settings/oext_eval.json"   # 7-8B copy: set per family by oext_78b.py\n'),
    ('    if (oext["module"], pin["path"]) != (oe.OWNER, "scripts/stage1_s1/settings/oext_eval.json"):\n',
     '    if (oext["module"], pin["path"]) != (oe.OWNER, OEXT_SETTINGS_PATH):\n'),
    ('    parser = argparse.ArgumentParser(prog="python scripts/stage1_s1/lean_eval_job.py",\n',
     '    parser = argparse.ArgumentParser(prog="python scripts/scale78b/lean_eval_job_78b.py",\n'),
]


def rebuild(source_text: str) -> str:
    """The copy's text from the 1B file's text; each find must occur exactly once."""
    out = source_text
    for find, replace in SUBSTITUTIONS:
        if out.count(find) != 1:
            raise ValueError(f"a find text occurs {out.count(find)} times: {find[:60]!r}")
        out = out.replace(find, replace)
    return out
