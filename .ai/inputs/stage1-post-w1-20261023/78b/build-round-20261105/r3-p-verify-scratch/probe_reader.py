import sys, json, hashlib, tempfile, pathlib
C = pathlib.Path(sys.argv[1]); S = pathlib.Path(sys.argv[2])
sys.argv = [sys.argv[0], str(C), str(S / "unused.json")]
sys.path.insert(0, str(S)); sys.path.insert(0, str(C)); sys.path.insert(0, str(C / "runkit/stage1-78b"))
import probe_compute as pc
from experiments.safety_selection import edits as E
import plan_tool as tool
with tempfile.TemporaryDirectory(dir=S) as td:
    tmp = pathlib.Path(td); prep = pc.fixture(400); ids = sorted(prep.train_rows)
    docs = {"A1": pc.edit_doc(remove=ids[:50]), "L1": pc.edit_doc(remove=ids[50:90]),
            "S3": pc.edit_doc(add=[("add-001", f"{pc.SENT} q", f"{pc.SENT} r r")]),
            "S4": pc.edit_doc(rewrite=[(ids[3], f"{pc.SENT} longer " + "k " * 40)])}
    pins = {}
    for arm, d in docs.items():
        p = tmp / "edits" / f"{arm}.json"; p.parent.mkdir(exist_ok=True); data = E.edit_bytes(d); p.write_bytes(data)
        pins[arm] = (p, E.sha256_bytes(data))
    code, rec, o, e, leak = pc.tool(prep, list(pins.values()), tmp)
    print("tool exit", code, "leak", leak, "keys == K2's:", tuple(sorted(rec)) == tuple(sorted(tool.PADDED_TOKENS_KEYS)))
    raw = (tmp / "out" / "rec.json").read_bytes()
    tool.ROOT = tmp
    tool.PADDED_TOKENS_78B[pc.FAM] = {"path": "out/rec.json", "sha256": hashlib.sha256(raw).hexdigest()}
    for arm, (p, sha) in pins.items():
        tool.r78.METHOD_EDITS[pc.FAM][arm] = {"path": f"edits/{arm}.json", "sha256": sha,
                                              "rows": 600 if arm in ("A1", "L1") else (48 if arm in ("S3", "S4") else 0)}
    runs = [("A1", 1101), ("L1", 1102), ("S3", 1103), ("S4", 1104), ("a0", 1105)]
    try:
        got = tool.padded_tokens(pc.FAM, runs)
        print("reader:", {f"{a}-{s}": round(v, 3) for (a, s), v in got.items()})
        print("equal to the record:", all(got[(a, s)] == rec["edits"][pins[a][1]] for a, s in runs if a != "a0"))
    except SystemExit as exc:
        print("reader refused:", str(exc)[:200])
