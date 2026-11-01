"""Analyse the six dry runs: consoles (no outcome word or number), ledgers, the identity/count checks, the step-2
comparison (a deep diff of the pre-run and step-2 documents by key path), the provenance logs, the STOP paths."""
import json, pathlib, re, sys
V2 = pathlib.Path(sys.argv[1]); RD = V2 / "root/.ai/inputs/stage1-post-w1-20261023/reading"
load = lambda q: json.loads(pathlib.Path(q).read_text())

def diff_paths(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}/{k} (only in {'step2' if k not in a else 'prerun'})")
            else:
                out += diff_paths(a[k], b[k], f"{path}/{k}")
    elif a != b:
        out.append(path)
    return out

for stamp in ("20261299", "20261298", "20261297", "20261296", "20261295", "20261294"):
    run = RD / f"run-{stamp}"; logs = run / "logs"
    print(f"\n===== run {stamp}")
    console = (V2 / f"console-{stamp}.txt").read_text()
    led = [json.loads(x) for x in (run / "reading-ledger.jsonl").read_text().splitlines()] if (run / "reading-ledger.jsonl").exists() else []
    print("ledger lines:", len(led), "; exits:", {e["step"]: e["exit"] for e in led})
    stops = [l for l in console.splitlines() if l.startswith("STOP")]
    print("STOP lines:", stops)
    # outcome words and numbers from the logs and outputs, checked against the console
    words = set(); numbers = set()
    b16 = run / "b16/reading.json"
    if b16.is_file():
        r = load(b16)
        words |= set(r["headline"].values())
        for k, row in r["rows"].items():
            words |= set(row["u_part"]["words"])
        for k, c in r["contrasts"].items():
            est = c.get("U", {}).get("est")
            if isinstance(est, (int, float)):
                numbers.add(f"{est:.4f}"[:6]); numbers.add(str(est)[:8])
    hb = run / "hb/hb_claim.json"
    if hb.is_file():
        words |= set(load(hb)["sentences"].values())
    sg = run / "sg/sg_coherent.json"
    if sg.is_file():
        words |= set(load(sg)["coherent"]["headline"].values())
    b14 = run / "b14/overlap_report.json"
    if b14.is_file():
        for blk in load(b14)["add_sets"].values():
            words.add(blk["verdict"]["text"])
    leak_w = sorted(w for w in words if w and re.search(r"\b" + re.escape(w) + r"\b", console))
    leak_n = sorted(n for n in numbers if n and n in console)
    print("outcome words seen in the logs/outputs:", sorted(words))
    print("words that appear in the console:", leak_w, "; estimate strings in the console:", leak_n)
    # console lines kinds
    kinds = set()
    for l in console.splitlines():
        if not l.strip(): continue
        if l.startswith("{"): kinds.add("json")
        elif re.match(r"^[A-Z][a-z]{2} [A-Z][a-z]{2} ", l): kinds.add("date")
        elif l.startswith("reading.zsh mode"): kinds.add("mode")
        elif l.startswith("step 4"): kinds.add("step4-note")
        elif l.startswith("step 5"): kinds.add("step5-note")
        elif l.startswith("STOP"): kinds.add("STOP")
        elif l.startswith("READING STEPS"): kinds.add("DONE")
        elif re.match(r"^[0-9a-f]{64}  ", l): kinds.add("ledger-sha")
        else: kinds.add("OTHER: " + l[:80])
    print("console line kinds:", sorted(kinds))
    for name in ("R1b-check.txt", "2-check.txt", "2-same-as-prerun.txt", "3-provenance.txt", "4-provenance.txt", "4b-provenance.txt",
                 "4c-fk_power-provenance.txt", "4c-stage3_pick-provenance.txt", "4c-sa_shift-provenance.txt", "4c-cap_reports.txt", "4c-cost_table.txt", "4b-sg-coherent.txt", "5-hlc-draw.txt", "R0-pins.txt", "2-builder.txt"):
        p = logs / name
        if p.is_file():
            t = p.read_text().strip().splitlines()
            show = [x for x in t if x.startswith("REFUSED") or x.startswith("{")] or t[-1:]
            print(f"  {name}: {show[-1][:300] if show else '(empty)'}")
    # the step-2 comparison: a deep diff of the pre-run and step-2 documents
    scr = V2 / f"scr-{stamp}"
    if (run / "input/tables.json").is_file() and (scr / "prerun-tables.json").is_file():
        for a, b, label in (("prerun-tables.json", "input/tables.json", "tables"), ("prerun-sources.json", "input/sources.json", "sources"),
                            ("prerun-hb_tables.json", "input/hb_tables.json", "hb_tables"), ("prerun-coherent_counts.json", "input/coherent_counts.json", "coherent_counts")):
            if (scr / a).is_file() and (run / b).is_file():
                d = diff_paths(load(scr / a), load(run / b))
                print(f"  deep diff {label}: {len(d)} differing key paths: {d[:12]}")
    # identity lines: each present exactly once in the builder log
    for logname, chk in (("R1b-builder-prerun.txt", "R1b-check.txt"), ("2-builder.txt", "2-check.txt")):
        if (logs / logname).is_file() and (logs / chk).is_file():
            c = json.loads((logs / chk).read_text().strip().splitlines()[-1])
            print(f"  {chk}: identity_lines {c['identity_lines']}, missing_identity {c['missing_identity']}, missing_count_lines {len(c['missing_count_lines'])}: {c['missing_count_lines']}")
    files = sorted(str(p.relative_to(run)) for p in run.rglob("*") if p.is_file())
    print("  run files:", len(files), [f for f in files if not f.startswith("logs/")])
