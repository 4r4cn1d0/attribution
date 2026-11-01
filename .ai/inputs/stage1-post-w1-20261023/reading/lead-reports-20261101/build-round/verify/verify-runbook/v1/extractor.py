import datetime as dt, hashlib, json, pathlib, sys
run = pathlib.Path(sys.argv[1])
out = run / "reading-record.json"
load = lambda q: json.loads(q.read_text())
sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
ledger = [json.loads(x) for x in (run / "reading-ledger.jsonl").read_text().splitlines() if x.strip()]
code = {e["step"]: e["exit"] for e in ledger}
note = {e["step"]: e.get("note") for e in ledger}

def reason(log):   # the REFUSED line of a step's log, else its last line; the check JSON of a provenance log
    q = run / "logs" / log
    lines = q.read_text().splitlines() if q.is_file() else []
    return next((x for x in lines if x.startswith("REFUSED")), lines[-1] if lines else "no log")

def passed(step, check):   # the step's exit and its provenance check's exit, both 0
    return code.get(step) == 0 and code.get(check) == 0

r, c = load(run / "b16/reading.json"), load(run / "hb/hb_claim.json")
doc = {"kind": "stage1 reading record", "version": 2, "reading": r["reading"],
       "utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
       "mode": note.get("R0-start"),
       "outputs": {q.relative_to(run).as_posix(): sha(q) for q in sorted(run.rglob("*")) if q.is_file()},
       "ledger": ledger,
       "copied_from_b16": {k: r[k] for k in ("headline", "headline_cells", "rows", "phi", "best_feasible_repair",
                                             "references", "overlap_control", "label_suffix", "notes")},
       "copied_from_hb_claim": {k: c[k] for k in ("sentences", "e_hb", "contrasts")},
       "rule": "copied by key from the reading's output documents; nothing computed or typed by hand (rev4:400)"}
SYM = "unscored counted Unsafe in every arm (not Gate B's adverse corner)"
sg = run / "sg/sg_coherent.json"
if passed("4b-sg-coherent", "4b-provenance") and sg.is_file():
    g = load(sg)
    doc["copied_from_sg_coherent"] = {k: g[k] for k in ("readings", "primary", "coherent", "g3a", "g3_unscored_symmetric",
                                                       "sensitivity_part")}
elif code.get("4b-sg-coherent") == 0 and not sg.is_file():
    doc["sg_coherent"] = {"text": "S-G, coherent-only U: not computed at the reading. D-5 went to its last fallback "
                                  "(c) at the no-value pre-run (mode no-coherent); the record carries (c)'s paragraph "
                                  "with the pre-run's refusal copied from run-attempt1's log.",
                          "ledger_note": note.get("4b-sg-coherent")}
else:
    why = (f"D-5's reader refused: {reason('4b-sg-coherent.txt')}" if code.get("4b-sg-coherent") != 0 else
           f"D-5's reader's provenance check failed: {reason('4b-provenance.txt')}; its output is not used")
    doc["sg_coherent"] = {"text": f"S-G, coherent-only U: not computed at the reading. {why}. B16's two G3 corners "
                                  f"print as built, labelled \"{SYM}\". This departs from the stage-1 "
                                  "pre-registration, revision 4, section 3.7 item 4."}
KEYS = {"cap_reports": ("readings", "branch", "route_per_source", "ln14", "ln19"),
        "fk_power": ("readings", "model", "contrasts"),
        "stage3_pick": ("readings", "pick", "eligible_in_order", "text"),
        "sa_shift": ("readings", "expected", "measured", "applies", "note"),
        "cost_table": ("readings", "units", "arms", "references", "b10_references", "b10_per_reference",
                       "diagnostics_by_kind", "charging")}
doc["reading_time_readers"] = {}
for name, keys in KEYS.items():
    q = run / "extra" / f"{name}.json"
    if passed(f"4c-{name}", f"4c-{name}-provenance") and q.is_file():
        d = load(q)
        doc["reading_time_readers"][name] = {k: d.get(k) for k in keys}
    else:
        doc["reading_time_readers"][name] = {"not_computed": True, "reason": (
            f"the reader refused: {reason(f'4c-{name}.txt')}" if code.get(f"4c-{name}") != 0 else
            f"the provenance check failed: {reason(f'4c-{name}-provenance.txt')}; its output is not used")}
man = run / "hlc/hlc_manifest.json"
if code.get("5-hlc-draw") == 0 and man.is_file():
    h = load(man)
    doc["hlc_draw"] = {k: h.get(k) for k in ("settings_sha256", "reduction_step", "seed_tags", "totals", "outputs",
                                             "not_built")}
    doc["hlc_draw"]["check_exit"] = code.get("5b-hlc-check")
else:
    doc["hlc_draw"] = {"not_run": "not run at the reading; the draw follows when the human label check is funded "
                                  "(D-7's fallback)", "reason": reason("5-hlc-draw.txt")}
with open(out, "x") as handle:
    handle.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
print(json.dumps({"written": str(out), "sha256": sha(out)}))
coh = (doc.get("copied_from_sg_coherent") or {}).get("coherent", {}).get("headline", {})
for k in r["headline"]:
    print(k, "|", r["headline"][k], "|", "; ".join(r["rows"][k]["u_part"]["words"]), "|", c["sentences"].get(k), "|",
          coh.get(k, "S-G coherent: not computed"))
