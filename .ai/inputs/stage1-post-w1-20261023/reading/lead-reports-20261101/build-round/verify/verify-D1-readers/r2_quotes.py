"""Every double-quoted passage of the five readers' module docstrings and RULE lists, checked against REV4's text
(bold and escapes removed, whitespace collapsed; '...' elisions split into pieces). Prints each piece that is not
found, so a human can tell a paraphrase or an annotation from a misquote. Run from the ws-d1 root with the venv
python."""
import importlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
REV4 = Path("/Users/spiderishi/Coding/attribution/research/experiments/2026-10-17-stage1-preregistration-rev3/"
            "stage1-preregistration-rev4.md").read_text()


def norm(s: str) -> str:
    s = s.replace("**", "").replace("\\*", "*").replace("\\", "")
    s = s.replace("θ", "theta").replace("Φ", "Phi").replace("−", "-").replace("×", "x").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


TEXT = norm(REV4)
bad = 0
for name in ("fk_power", "stage3_pick", "sa_shift", "cap_reports", "cost_table"):
    mod = importlib.import_module(f"scripts.stage1_s1.reading_extra.{name}")
    sources = [("doc", norm(mod.__doc__ or ""))] + [("RULE", norm(r)) for r in mod.RULE]
    checked = 0
    for where, text in sources:
        for q in re.findall(r'"([^"]{25,})"', text):
            for piece in re.split(r"\s*(?:\.\.\.|…)\s*", q):
                piece = piece.strip(" .;:,")
                if len(piece) < 25:
                    continue
                checked += 1
                if piece not in TEXT:
                    bad += 1
                    print(f"{name} {where}: NOT IN REV4: {piece[:200]!r}")
    print(f"{name}: {checked} quoted pieces checked")
print("not found:", bad)
