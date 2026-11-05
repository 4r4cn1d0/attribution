"""Re-verify F: does any file I wrote (this report, every scratch file) or any of the fixer's four files hold a row text of
the sealed S1 list? The list is read through REQ-7's read_list by its pin (frozen code); its strings are never printed;
s1common._text_hits counts hits per file. The fixer's form, pointed at the copy of the worktree and my scratch.
Usage: python -I -B text_check_rf.py <copy-of-worktree> <scratch> <report>"""
import pathlib
import sys

WS = pathlib.Path(sys.argv[1]).resolve()
SCR = pathlib.Path(sys.argv[2]).resolve()
REPORT = pathlib.Path(sys.argv[3]).resolve()
sys.path.insert(0, str(WS))
from scripts.scale78b import s1_olmo2_7b_check as C  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import write_add_edit as wae  # noqa: E402

B = C.load_sealed_builder(WS)
listing = wae.read_list(WS / "tmp/scale-78b-s1-llama3-20261105/list/s1.json", B.LIST_SHA256)
texts = [item[k] for item in listing["items"] for k in ("prompt", "response")]          # the 96 row texts
print(f"list texts (prompt and response of the {len(listing['items'])} items, read through read_list): {len(texts)}")
files = [WS / "scripts/scale78b/s1_olmo2_7b_check.py", WS / "scripts/scale78b/tests/test_s1_olmo2_7b_check.py",
         WS / "scripts/scale78b/tests/test_noise_reading_guard_fields.py",
         WS / ".ai/inputs/scale-78b-s1-llama3-20261105/README.md", REPORT]
files += sorted(p for p in SCR.rglob("*") if p.is_file() and WS not in p.parents and "wsf-copy" not in p.parts)
total = 0
for path in files:
    hits = s1._text_hits(path.read_bytes(), texts)
    total += hits
    print(f"{hits:4d}  {path.relative_to(WS) if WS in path.parents else path.relative_to(SCR.parent)}")
print(f"total hits {total}")
