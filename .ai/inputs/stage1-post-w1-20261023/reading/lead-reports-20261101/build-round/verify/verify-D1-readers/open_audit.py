"""Which kit files do cap_reports and cost_table open or list? An audit hook records every open/listdir/scandir
event under the synthetic kit (verifier's own check; synthetic data only)."""
import json, sys
from collections import Counter
from pathlib import Path
WS = Path.cwd()
sys.path.insert(0, str(WS))
sys.path.insert(0, str(WS / "scripts/stage1_s1/reading_extra/tests"))
sys.path.insert(0, str(WS / "scripts/stage1_s1/reading_input/tests"))
import synth_kit as sk, extra_kit as ek
from scripts.stage1_s1.reading_input.__main__ import main as builder
from scripts.stage1_s1.reading_extra import cap_reports, cost_table

base = Path(sys.argv[1]); base.mkdir(parents=True, exist_ok=True)
s = sk.make(base / "w", "plan_a", branch="128")
ek.with_caps(s)
rec = base / "sources.json"
assert builder(s.args(base / "tables.json", rec, overlap=False)) == 0
ckit, _, _ = ek.cost_kit(base / "cost", "plan_a")

EVENTS = []
ACTIVE = [None]
def hook(event, args):
    if ACTIVE[0] is None:
        return
    if event in ("open", "os.listdir", "os.scandir", "glob.glob"):
        p = args[0]
        if isinstance(p, (str, bytes, Path)):
            EVENTS.append((ACTIVE[0], event, str(p if not isinstance(p, bytes) else p.decode())))
sys.addaudithook(hook)

ACTIVE[0] = "cap"
rc1 = cap_reports.main(["--kit", str(s.kit), "--record", str(rec), "--out", str(base / "cap.json")])
ACTIVE[0] = "cost"
rc2 = cost_table.main(["--kit", str(ckit), "--reading", "plan_a", "--out", str(base / "cost.json")])
ACTIVE[0] = None
print("exit", rc1, rc2)
for who, kit in (("cap", s.kit), ("cost", ckit)):
    names = Counter()
    lists = []
    for w, ev, p in EVENTS:
        if w != who or not p.startswith(str(kit)):
            continue
        if ev == "open":
            names[Path(p).name] += 1
        else:
            lists.append(p)
    print(who, "opened under the kit:", dict(sorted(names.items())))
    print(who, "folder listings under the kit:", lists[:5], len(lists))
    other = sorted({p for w, ev, p in EVENTS if w == who and ev == "open" and not p.startswith(str(kit))
                    and not p.endswith((".py", ".pyc")) and "/site-packages/" not in p and "/lib/python" not in p})
    print(who, "other non-code files opened:", other)
