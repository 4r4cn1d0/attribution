"""Synthetic reproduction (track A's builder in ws-a; its own synthetic kit; no real data): the runbook's step-2 check
'2-same-as-prerun' (R1D:581-600, copied below) after the plan update's step 2 adds D-5's counts option.
Case A: R1b as the records quote it (no counts option) vs step 2 with the counts option.
Case B: R1b with the counts option too vs step 2 with it.
Usage: python -B prerun_vs_step2.py <ws-a root> <scratch folder>"""
import io, json, pathlib, sys, contextlib
ws, scratch = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
sys.path.insert(0, str(ws)); sys.path.insert(0, str(ws / "scripts/stage1_s1/reading_input/tests"))
import synth_kit as sk
from scripts.stage1_s1.reading_input.__main__ import main

s = sk.make(scratch / "world", "plan_a")
def build(tag, overlap, counts):
    d = scratch / tag; d.mkdir()
    args = s.args(d / "tables.json", d / "sources.json", overlap=overlap) + (["--coherent-out", str(d / "counts.json")] if counts else [])
    with contextlib.redirect_stdout(io.StringIO()):
        rc = main(args)
    return rc, d

def r1d_same_as_prerun(scr, inp):           # R1D:582-598, with the hb_tables comparison left out (no --hb-out here)
    load = lambda q: json.loads(q.read_text())
    t0, t1 = load(scr / "tables.json"), load(inp / "tables.json")
    s0, s1 = load(scr / "sources.json"), load(inp / "sources.json")
    t1.pop("overlap", None)
    for x in (s0, s1):
        x.pop("overlap", None); x.pop("output_sha256", None); (x.get("hb") or {}).pop("output_sha256", None)
    return {"tables_without_overlap": t0 == t1, "sources_without_overlap_and_output_hashes": s0 == s1,
            "coherent_in_prerun": s0.get("coherent"), "coherent_in_step2": s1.get("coherent")}

rc_a0, pre_a = build("prerun-no-counts", overlap=False, counts=False)
rc_b0, pre_b = build("prerun-with-counts", overlap=False, counts=True)
rc_2, step2 = build("step2-with-counts", overlap=True, counts=True)
print("exit codes:", rc_a0, rc_b0, rc_2)
print("case A (R1b without the counts option):", json.dumps(r1d_same_as_prerun(pre_a, step2)))
print("case B (R1b with the counts option):   ", json.dumps(r1d_same_as_prerun(pre_b, step2)))
