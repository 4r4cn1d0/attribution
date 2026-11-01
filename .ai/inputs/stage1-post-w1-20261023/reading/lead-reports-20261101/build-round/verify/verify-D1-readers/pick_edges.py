"""stage3_pick edge cases on a synthetic reading.json (verifier's own expectations)."""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from scripts.stage1_s1.reading.settings import Refusal
from scripts.stage1_s1.reading_extra import stage3_pick as sp

base = json.loads(Path(sys.argv[1]).read_text())
B, W, E1, EF, NOTE, INC = "better", "worse (U)", "equivalent (per comparison)", "equivalent (familywise)", \
    "significant, below the smallest effect of interest", "inconclusive"

def setc(doc, name, est, se, words):
    u = doc["contrasts"][name]["U"]
    u["est"], u["se"] = est, se
    u["t"] = est / se if se > 0 else ("inf" if est > 0 else "-inf")
    p = doc["rows"][name]["u_part"]
    p["words"] = list(words)
    p["better"], p["worse"] = B in words, W in words

def run(doc):
    try:
        return sp.pick(doc, "0" * 64)["pick"]
    except Refusal as exc:
        return f"REFUSED: {exc}"

def neutral(doc):
    for n in ("P1", "P2", "P3", "P4", "P5", "P6"):
        setc(doc, n, 1.0, 2.0, [INC])

cases = []
d = copy.deepcopy(base); neutral(d)
cases.append(("none eligible", d, []))
d = copy.deepcopy(base); neutral(d); setc(d, "P3", 6.0, 2.0, [B]); setc(d, "P2", -6.0, 2.0, [W]); setc(d, "P1", 1.0, 0.1, [INC])
cases.append(("tie |t| 3 between P2 (worse) and P3 (better); P1 larger |t| but inconclusive", d, ["P2", "P3"]))
d = copy.deepcopy(base); neutral(d); setc(d, "P5", -2.0, 0.5, [W, E1, NOTE]); setc(d, "P6", 7.0, 2.0, [B])
cases.append(("worse (U) with an equivalence grade and the note is eligible (S1)", d, ["P5", "P6"]))
d = copy.deepcopy(base); neutral(d); setc(d, "P1", 9.0, 3.0, [B]); setc(d, "P4", 8.0, 2.0, [B]); setc(d, "P6", -5.0, 1.0, [W])
cases.append(("three eligible |t| 3, 4, 5 -> the two largest", d, ["P6", "P4"]))
d = copy.deepcopy(base); neutral(d); setc(d, "P2", 4.0, 1.0, [E1, NOTE]); setc(d, "P3", 6.0, 2.0, [B])
cases.append(("significant-below-SESOI (no better word) not eligible", d, ["P3"]))
d = copy.deepcopy(base); neutral(d); setc(d, "P4", 6.0, 0.0, [B]); setc(d, "P1", 6.0, 1.0, [B])
cases.append(("an infinite t ranks first", d, ["P4", "P1"]))
d = copy.deepcopy(base); neutral(d); setc(d, "P1", 6.0, 1.0, [B]); d["rows"]["P1"]["u_part"]["better"] = False
cases.append(("flags disagree with words -> refuse", d, "REFUSED"))
d = copy.deepcopy(base); neutral(d); setc(d, "P1", 6.0, 1.0, [B]); d["contrasts"]["P1"]["U"]["t"] = 5.0
cases.append(("printed t is not est/se -> refuse", d, "REFUSED"))
d = copy.deepcopy(base); neutral(d); setc(d, "P3", 6.0, 2.0, [B]); setc(d, "P1", -6.0, 2.0, [W])
cases.append(("tie: lower P index first (P1 before P3)", d, ["P1", "P3"]))
for what, doc, want in cases:
    got = run(doc)
    ok = (got == want) if want != "REFUSED" else (isinstance(got, str) and got.startswith("REFUSED"))
    print(("PASS " if ok else "FAIL ") + what + f": got {got} want {want}")
