"""Reproduction: HLC 4.2's "at least 2 of each [HarmBench label] where they exist" inside a seed's Unsafe cell is not
guaranteed by the tool's walk when a prompt carries both a HarmBench-"yes" and a HarmBench-"no" Unsafe answer.

The tool's own allocate() (scripts/stage1_s1/hlc_draw/draw.py) with the real pinned settings and seed tags is run on
one synthetic unit "a0 1101": 200 harm prompts p000-p199, 3 sampled answers each. Two prompts Y1, Y2 each hold one
Unsafe answer with HarmBench "yes" (sample 0) and one Unsafe answer with HarmBench "no" (sample 1); ten other prompts
hold one Unsafe "no" answer (sample 0); every other answer is Safe. So 2 "yes" answers exist on 2 distinct prompts,
hb_split gives the quota (yes 2, no 6), and a draw of 2 "yes" answers is possible. The search picks Y1, Y2 among the
200 prompt ids until the sealed order (derive_seed(20261022, "hlc-v1", "a0/1101/harm/Unsafe")) puts a "no" answer of
Y1 or Y2 before its "yes" answer; then the walk takes the "no" answer, marks the prompt used, and the "yes" answer is
lost. Synthetic data only."""

from __future__ import annotations

import itertools
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib  # noqa: E402

from scripts.stage1_s1.hlc_draw import draw as dr  # noqa: E402
from scripts.stage1_s1.hlc_draw import inputs as inp  # noqa: E402

cfg = dr.load_settings()                                     # the real pinned settings (seed tags, sizes)
HARM = [f"p{i:03d}" for i in range(200)]


def unit_with(y1: str, y2: str, nos: list) -> inp.Unit:
    u = inp.Unit("a0 1101", "a0", 1101, "pinned", "synthetic", None, "e1")
    for p in HARM:
        for k in range(3):
            if p in (y1, y2) and k in (0, 1):
                hbl = "yes" if k == 0 else "no"
                u.harm.append(inp.Answer("harm", p, k, "Unsafe", ("Violent",), "Unsafe", "No", None, 50, False, hbl))
            elif p in nos and k == 0:
                u.harm.append(inp.Answer("harm", p, k, "Unsafe", ("Violent",), "Unsafe", "No", None, 50, False, "no"))
            else:
                u.harm.append(inp.Answer("harm", p, k, "Safe", (), "Safe", "No", None, 50, False, "no"))
    u.benign = [inp.Answer("benign", f"d{i:03d}", None, "No" if i % 3 else "Yes", (), "Safe",
                           "No" if i % 3 else "Yes", None, 50, False) for i in range(100)]
    return u


class _F:                                                     # allocate() reads unit.folder.complete_sha256 only
    complete_sha256 = "0" * 64


found = None
for y1, y2 in itertools.combinations(HARM[:60], 2):
    nos = [p for p in HARM[100:110]]
    u = unit_with(y1, y2, nos)
    u.folder = _F()
    items, cells, subs = dr.allocate([u], {}, cfg, "0")
    un = [s for s in subs if s["cell"] == "Unsafe"]
    yes = next(s for s in un if s["sub_cell"] == "Unsafe/yes")
    no = next(s for s in un if s["sub_cell"] == "Unsafe/no")
    if yes["drawn"] < min(2, yes["available"]):
        found = (y1, y2, yes, no)
        break

if found is None:
    print("no violating configuration among the first 60 prompts")
    sys.exit(1)
y1, y2, yes, no = found
print(f"prompts holding a yes and a no Unsafe answer: {y1}, {y2}; other no-only prompts: p100-p109")
print(f"hb_split quota: yes {yes['quota']}, no {no['quota']} (available yes {yes['available']}, no {no['available']}; "
      f"the yes answers sit on 2 distinct prompts)")
print(f"drawn: yes {yes['drawn']}, no {no['drawn']}  ->  HLC 4.2 'at least 2 of each where they exist' "
      f"{'VIOLATED' if yes['drawn'] < 2 else 'kept'}")
# the same unit, drawn so that the yes answers come first, shows 2 yes are feasible with the no-twice rule
order = dr.sealed_order({dr.answer_key(a): a for a in unit_with(y1, y2, HARM[100:110]).harm if a.label == "Unsafe"},
                        dr.cell_seed(cfg, inp.Unit("a0 1101", "a0", 1101, "pinned", "x", None, "e1"), "harm",
                                     "Unsafe"))
print("sealed order (first 12):", order[:12])
print("a feasible draw keeping the minimum: (", y1, 0, "), (", y2, 0, ") plus 6 no-only prompts")
