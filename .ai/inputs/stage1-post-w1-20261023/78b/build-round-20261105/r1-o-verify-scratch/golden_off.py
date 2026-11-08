"""Each maker mutant of the builder's spec, applied to src4's copy, with the golden test deselected (scratch only)."""
import hashlib, json, subprocess, sys
from pathlib import Path
src4 = Path(sys.argv[1]); py = sys.argv[2]
spec = json.loads((src4 / "scripts/scale78b/tests/oext/mutation_spec_oext_78b.json").read_text())
gold = "scripts/scale78b/tests/oext/test_oext_78b_files.py::test_the_maker_reproduces_every_file_and_the_index_is_pinned"
for m in spec["mutants"]:
    if m["file"] != "make_oext_settings_78b.py":
        continue
    target = src4 / "scripts/scale78b" / m["file"]
    original = target.read_bytes()
    text = original.decode()
    assert text.count(m["find"]) == 1, m["id"]
    target.write_text(text.replace(m["find"], m["replace"]))
    try:
        done = subprocess.run([py, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", "-rfE", "--deselect", gold,
                               "scripts/scale78b/tests/oext"], cwd=src4, capture_output=True, text=True, timeout=300)
        lines = (done.stdout + done.stderr).splitlines()
        failed = [x.split("::")[-1][:80] for x in lines if x.startswith("FAILED ")]
        errors = [x for x in lines if x.startswith("ERROR ")]
        print(json.dumps({"id": m["id"], "exit": done.returncode, "first_failed": failed[:1], "errors": len(errors),
                          "tail": [x for x in lines if x.strip()][-1][-60:]}))
    finally:
        target.write_bytes(original)
        assert hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(original).digest()
