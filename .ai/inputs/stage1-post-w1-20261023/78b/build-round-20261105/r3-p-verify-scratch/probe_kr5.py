import json, sys, importlib.util, pathlib, tempfile, shutil, hashlib
C = pathlib.Path(sys.argv[1]); sys.path.insert(0, str(C)); sys.path.insert(0, str(C / "runkit/stage1-78b"))
import rules_78b as r
spec = importlib.util.spec_from_file_location("tbs", C / "scripts/scale78b/tests/test_blinded_sigma.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
bs = t.bs
for kind, code in (("safe_anchors_below_64", 3), ("harmful_prompt_does_not_encode", 1)):
    doc = t.stop_record_doc("olmo2-7b", kind, code)
    print(kind, "RK anchor_stop_problem:", r.anchor_stop_problem(doc, "olmo2-7b"))
    # K2's writer's own output for the same stop
    if kind == "safe_anchors_below_64":
        w = r.anchor_stop_record("olmo2-7b", 3, None, "4" * 64, {"kept": 61, "needed": 64})
    else:
        w = None
    print("  equals K2's writer:", (w == doc) if w else "n/a (needs the frozen message form)")
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "s.json"; p.write_bytes(t.canon(doc))
        bs.check_anchor_stop("olmo2-7b", {"path": "s.json", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}, pathlib.Path(td))
        print("  Track S reader: accepted")
shared = json.loads((C / "runkit/stage1-78b/tests/fixtures/anchor_stop__olmo2-7b__safe_anchors_below_64.json").read_bytes())
print("shared fixture RK problem:", r.anchor_stop_problem(shared, "olmo2-7b"))
