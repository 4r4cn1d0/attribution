"""Verifier's probe of the finisher's light check on a host WITHOUT a similarity job (synthetic tree), round 33 vs
round 34, with plan.json readable and with plan.json unreadable (as during a concurrent non-atomic save_plan).

    python -B finisher_probe.py KIT_DIR     (a kit copy in the verify folder; it writes plan.json and retrieved/ there)
"""
import importlib.util
import json
import pathlib
import sys

KIT = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location(f"fin_probe_{KIT.parent.parent.name}", KIT / "finisher.py")
fin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fin)
tree = KIT / "retrieved" / "a-9" / "tree"
unit = tree / "round1" / "1102-x-e1-a1"
unit.mkdir(parents=True, exist_ok=True)
(unit / "COMPLETE.json").write_text(json.dumps({"files": {}}))
(tree / "JOB-DONE.json").write_text(json.dumps({"ok": True, "jobs": [{"index": 0, "kind": "arm", "status": "complete"}]}))
for label, text in (("plan.json readable", json.dumps({"hosts": {}, "recipes": {}})),
                    ("plan.json mid-write (truncated)", '{"hosts": {"a-9": {"role": "arms", ')):
    (KIT / "plan.json").write_text(text)
    try:
        print(f"[{label}] light_check ->", fin.light_check("a-9", tree))
    except Exception as exc:  # noqa: BLE001
        print(f"[{label}] light_check RAISED {type(exc).__name__}")
