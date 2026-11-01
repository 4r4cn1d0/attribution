#!/bin/zsh
# The stage-1 reading, steps R0-5, as one pre-committed and stamped script (the plan's steps 1-5 at 55d5f8b:37-49;
# addendum section 39 point 8; the reading runbook, section 4). It stops only on an identity line (the runbook's stop
# rules S1-S6: the pins, a refusal of B14, the builder, B16 or the claim reader, a hash or provenance mismatch, a
# pre-run or re-run that is not byte-identical). The D-5 reader (step 4b) and the reading-time readers (step 4c) never
# stop it (section 39 point 8(d)(i)); nor does LN-31's draw (step 5), a report-only item (REV4:762) whose fallback
# wording is E-misc B ruling 3: their exit codes are logged and the reading goes on. Every step's exit code goes to the
# ledger, one JSON line per step; a provenance check that has no output to check (its reader refused) is not run, and
# its ledger line says so. The script prints no outcome value: each tool's stdout goes to its step log under
# $RUN/logs, and the console holds step names, times, hashes, booleans, counts of lines and STOP lines only. Every
# file is written once, by an exclusive create (the tools open their outputs with O_EXCL; noclobber makes every ">" of
# this script one). The ledger is the one file written more than once: created at R0-start (the run folder must not
# exist before the script) and appended one line per step.
#
#     caffeinate -i zsh "$RD/reading-$STAMP.zsh" [coherent | no-coherent] > "$RD/reading-$STAMP.console.txt" 2>&1
#
# Run it once, from the lead's Bash as one background job (run_in_background: true), after the runbook's go / no-go
# (step 0.8). The mode is "coherent" (the default: the builder takes --coherent-out and step 4b runs the D-5 reader)
# or "no-coherent" (D-5's last fallback (c), chosen at the pre-run R1b when it refused only on the coherent-only
# counts: D-5 item 8; the pre-runs then restart without the option). Exit 0: steps R0-5 done; 1: a check failed (the
# STOP line names the step and the stop rule); 2: a usage error.

setopt noclobber
export PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1   # one BLAS thread, as the mutation runs

# ----- settings (the runbook's Block R; every path is under the main checkout) ---------------------------------------
ROOT=/Users/spiderishi/Coding/attribution                  # the main checkout (tmp/gi-vii-notes/blockB_S.zsh sets the same three)
KIT=$ROOT/tmp/stage1-olmo                                  # the live kit (plan.json, seals/, retrieved/: never listed, never opened by hand)
PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python   # Python 3.11.15, numpy 2.2.6; the second stamp pins both
STAMP=20261101                                           # the second stamp's date label, for example 20261102; filled before the commit the stamp binds
RD=$ROOT/.ai/inputs/stage1-post-w1-20261023/reading        # the reading's records (tracked)
RUN=$RD/run-$STAMP                                         # the reading's outputs; absent until this script makes it
LOGS=$RUN/logs                                             # every tool's stdout and stderr, one file per step
LEDGER=$RUN/reading-ledger.jsonl                           # one JSON line per step: time, exit code, the outputs' SHA-256
M2=$RD/timestamp/ots-manifest-reading-$STAMP.json          # the second stamp's manifest (runbook step 0.6): the pin file
SCR=/private/tmp/stage1-reading-scratch                    # outside the repository; empty at the start; deleted after step 6
STRATA=$RD/b14/strata/strata.json                          # the sealed strata (overlap_strata.py strata, under D-6's settings)
STRATA_SHA=2d996a99a49eed696c3ec047b4184b9ced7db60f29bd151d25e219b1142890f2                              # its SHA-256 exactly as FOCUS records it (addendum:375)
B14IN=$RD/b14/inputs/overlap_inputs.json                   # B14's inputs file (overlap_inputs.py; checked by overlap_inputs_check.py)
OCT9KEY=$ROOT/tmp/hlc-inputs/oct9/key.json                 # step 5's pinned inputs, restored before the reading (LR R5.5)
V3=$ROOT/tmp/hlc-inputs/prepared-v3-inj05
MODE=${1:-coherent}
EXPECT=(   # the builder's count lines, logged and reviewed after the run, never a stop (section 39 point 8(a))
  "cells: U 50, O " ", L 50; O cells absent (LN-12): "
  "references: ref-G, ref-bqi, ref-external-safe_lora-default, ref-prefix, ref-scale (47 units)"
  "not references: 1; complete (not pulled), not inputs: 4"
  "judges A: granite, harmbench; 27 units, 54 indexed files"
  "judges B: granite, harmbench; 71 units, 144 indexed files"
  "HarmBench A: tag s1a-hb-1, run record " "(21600 records, "
  "HarmBench B: tag s1b-hb-1, run record " "(57600 records, "
  "HarmBench tables: 51 units; not built: granite_agreement, hb2_report, references"
  "not built: token_axis" "not built: u_variants.coherent" )
if [[ $MODE == coherent ]]; then
  COH_PRE=(--coherent-out "$SCR/prerun-coherent_counts.json"); COH_RUN=(--coherent-out "$RUN/input/coherent_counts.json")
  EXPECT+=("coherent-only counts: 50 cells x 200 prompts")
elif [[ $MODE == no-coherent ]]; then
  COH_PRE=(); COH_RUN=()
  EXPECT+=("coherent-only counts: not built (no --coherent-out)")
else
  print -r -- "usage: reading.zsh [coherent | no-coherent]"; exit 2
fi

# ----- helpers --------------------------------------------------------------------------------------------------------
fail() { print -r -- "STOP at step $1: $2"; date -u; exit 1 }

ledger() {   # ledger STEP EXIT [note=TEXT] [FILE ...]: one JSON line (time, step, exit code, note, the files' SHA-256)
"$PY" -I -B - "$LEDGER" "$@" <<'EOF'
import datetime as dt, hashlib, json, pathlib, sys
ledger, step, code, *rest = sys.argv[1:]
notes = [x[5:] for x in rest if x.startswith("note=")]
files = [x for x in rest if not x.startswith("note=")]
rec = {"utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"), "step": step, "exit": int(code),
       "outputs": {f: hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest() for f in files if pathlib.Path(f).is_file()}}
if notes:
    rec["note"] = notes[0]
with open(ledger, "a" if pathlib.Path(ledger).exists() else "x") as handle:   # created once (R0-start), then appended
    handle.write(json.dumps(rec, sort_keys=True) + "\n")
print(json.dumps(rec, sort_keys=True))
EOF
}

lines_check() {   # lines_check LOG OVERLAP_LINE --outs FILE ... --counts LINE ...: the builder's identity lines (a stop) and count lines (logged)
"$PY" -I -B - "$M2" "$@" <<'EOF'
import hashlib, json, pathlib, sys
m2, log, overlap_line, *rest = sys.argv[1:]
m = json.loads(pathlib.Path(m2).read_text())
lines = pathlib.Path(log).read_text().splitlines()
outs = rest[rest.index("--outs") + 1:rest.index("--counts")]
counts = rest[rest.index("--counts") + 1:]
sha = lambda q: hashlib.sha256(pathlib.Path(q).read_bytes()).hexdigest()
identity = [f"(plan A); plan.json {m['kit']['plan_json_sha256']}",
            f"sha256 {m['files']['runkit/stage1-olmo/stage1_rules.py']}; B16 settings "
            f"{m['files']['scripts/stage1_s1/reading/settings/reading.json']}",
            f"seal A {m['kit']['seal_A']}", f"seal B {m['kit']['seal_B']}", overlap_line,
            *[f"wrote {q} sha256 {sha(q)}" for q in outs]]
missing = [w for w in identity if not any(w in line for line in lines)]
missing_counts = [w for w in counts if not any(w in line for line in lines)]
print(json.dumps({"identity_lines": len(identity), "missing_identity": missing, "count_lines": len(counts),
                  "missing_count_lines": missing_counts, "pass": not missing}, sort_keys=True))
sys.exit(0 if not missing else 1)
EOF
}

prov() {   # prov OUTPUT SPEC ...: an output's provenance against the pin file; pass only when every check holds
# SPEC items: kind=K; reading=R; b16self (B16's own modules and settings pin); b16 (b16_modules and b16_settings_sha256);
# modules=FOLDER/:NAME,NAME or modules=FOLDER/:* (the reader's own modules); input:NAME=FILE (the inputs dict); kit
# (plan.json's and the seals' SHA-256); any other KEY=FILE compares provenance[KEY] with FILE's SHA-256. B16's _strip
# drops every key that starts with "_", so a modules dict never holds __init__.py or __main__.py (A's open point 7).
"$PY" -I -B - "$M2" "$@" <<'EOF'
import hashlib, json, pathlib, sys
m2, out, *spec = sys.argv[1:]
m = json.loads(pathlib.Path(m2).read_text())
out = pathlib.Path(out)
d = json.loads(out.read_text()) if out.is_file() else {}
p = d.get("provenance") if isinstance(d.get("provenance"), dict) else {}
sha = lambda q: hashlib.sha256(pathlib.Path(q).read_bytes()).hexdigest()
B16 = "scripts/stage1_s1/reading/"

def tree(prefix):   # the manifest's top-level *.py of one package, less the names B16's _strip drops
    return {k[len(prefix):]: v for k, v in m["files"].items() if k.startswith(prefix) and k.endswith(".py")
            and "/" not in k[len(prefix):] and not k[len(prefix):].startswith("_")}

b16 = {**tree(B16), "settings/reading.json": m["files"][B16 + "settings/reading.json"]}
c = {"file": out.is_file()}
for item in spec:
    key, _, val = item.partition("=")
    if key == "kind":
        c["kind"] = d.get("kind") == val
    elif key == "reading":
        c["reading"] = d.get("reading") == val
    elif key == "b16self":
        c["modules"] = p.get("modules") == b16
        c["settings_sha256"] = p.get("settings_sha256") == b16["settings/reading.json"]
    elif key == "b16":
        c["b16_modules"] = p.get("b16_modules") == b16
        c["b16_settings_sha256"] = p.get("b16_settings_sha256") == b16["settings/reading.json"]
    elif key == "modules":
        folder, _, names = val.partition(":")
        want = tree(folder) if names == "*" else {n: m["files"][folder + n] for n in names.split(",")}
        c["modules"] = p.get("modules") == want
    elif key.startswith("input:"):
        c[key] = (p.get("inputs") or {}).get(key[6:]) == sha(val)
    elif key == "kit":
        k = p.get("kit") if isinstance(p.get("kit"), dict) else {}
        seals = k.get("seals") if isinstance(k.get("seals"), dict) else {}
        c["kit"] = (k.get("plan_sha256") == m["kit"]["plan_json_sha256"] and set(seals) == {"A", "B"}
                    and all(seals[b] == m["kit"][f"seal_{b}"] for b in ("A", "B")))
    else:
        c[key] = p.get(key) == sha(val)
c["python_numpy"] = [p.get("python"), p.get("numpy")] == [m["python"]["python"], m["python"]["numpy"]]
ok = all(c.values())
print(json.dumps({**c, "pass": ok}, sort_keys=True))
sys.exit(0 if ok else 1)
EOF
}

extra() {   # extra NAME SPEC ... -- ARG ...: one reading-time reader into $RUN/extra/NAME.json; logged, never a stop
  local name=$1; shift
  local -a spec args; local seen=0 a c
  for a in "$@"; do
    if [[ $a == -- ]]; then seen=1; elif (( seen )); then args+=("$a"); else spec+=("$a"); fi
  done
  "$PY" -B -m scripts.stage1_s1.reading_extra.$name "${args[@]}" --out "$RUN/extra/$name.json" > "$LOGS/4c-$name.txt" 2>&1
  c=$?; ledger "4c-$name" $c "$RUN/extra/$name.json"
  if (( c != 0 )); then   # nothing was written (the reader's refusal), so there is no provenance to check
    print -r -- "step 4c ($name): exit $c, logged; report only, the reading goes on"
    ledger "4c-$name-provenance" 1 "note=not run: the reader wrote no output (its exit $c)"
    return 0
  fi
  prov "$RUN/extra/$name.json" reading=plan_a "modules=scripts/stage1_s1/reading_extra/:*" b16 "${spec[@]}" > "$LOGS/4c-$name-provenance.txt" 2>&1
  c=$?; ledger "4c-$name-provenance" $c
  (( c == 0 )) || print -r -- "step 4c ($name): provenance check exit $c, logged; its output is not used by the record"
}

# ----- the run folder --------------------------------------------------------------------------------------------------
cd "$ROOT" || fail R0 "no checkout"
date -u
print -r -- "reading.zsh mode $MODE; STAMP $STAMP"
test ! -e "$RUN" || fail R0 "$RUN exists"
mkdir -p "$SCR" && test -z "$(ls -A "$SCR")" || fail R0 "$SCR is not empty"
mkdir -p "$LOGS" "$RUN/input" "$RUN/b16" "$RUN/hb" "$RUN/sg" "$RUN/extra" "$RUN/hlc" || fail R0 "cannot make the run folders"
ledger R0-start 0 "note=mode $MODE"

# R0: every pinned file, tree, kit record and version equals the anchored second stamp
"$PY" -I -B - "$ROOT" "$M2" "$KIT" "$PY" > "$LOGS/R0-pins.txt" 2>&1 <<'EOF'
import hashlib, json, pathlib, subprocess, sys
root, m2, kit, py = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4]
m = json.loads(m2.read_text())
sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
git = lambda *a: subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, check=True).stdout.strip()
differ = sorted(rel for rel, h in m["files"].items() if not (root / rel).is_file() or sha(root / rel) != h)
trees = {t: git("rev-parse", f"HEAD:{t}") for t in m["git"]["trees"]}
dirty = git("status", "--porcelain", "--", "scripts", "runkit", "experiments/safety_selection")
kit_now = {"plan_json_sha256": sha(kit / "plan.json"), "seal_A": sha(kit / "seals" / "block-A.json"),
           "seal_B": sha(kit / "seals" / "block-B.json")}
ver = subprocess.run([py, "-I", "-B", "-c", "import platform, numpy; print(platform.python_version(), numpy.__version__)"],
                     capture_output=True, text=True, check=True).stdout.split()
c = {"files_differ": differ, "trees_same": trees == m["git"]["trees"], "code_clean": not dirty,
     "kit_same": kit_now == m["kit"], "python_same": ver == [m["python"]["python"], m["python"]["numpy"]]}
ok = not differ and c["trees_same"] and c["code_clean"] and c["kit_same"] and c["python_same"]
print(json.dumps({**c, "pass": ok}, sort_keys=True))
sys.exit(0 if ok else 1)
EOF
c=$?; ledger R0-pins $c; (( c == 0 )) || fail R0 "a pinned file, tree, kit record or version differs from the second stamp (S1)"

# R1a: B14's report as a no-value pre-run (stdout, which would hold the S-p verdicts, is discarded unread)
date -u
"$PY" -B scripts/stage1_s1/overlap_strata.py report --strata "$STRATA" --inputs "$B14IN" --out "$SCR/b14-prerun" >| /dev/null 2> "$LOGS/R1a-b14-prerun-stderr.txt"
c=$?; ledger R1a-b14-prerun $c "$SCR/b14-prerun/overlap_report.json"; (( c == 0 )) || fail R1a "B14 refused; no outcome was shown (S2)"

# R1b: the builder as a no-value pre-run, with the same options as step 2 and --no-overlap in place of the B14 options
# (it prints counts, hashes and labels only; its files stay unopened in scratch). A refusal only on the coherent-only
# counts (stderr begins "REFUSED: the coherent-only counts") is D-5's (c) route: run again with "no-coherent" (S2).
date -u
"$PY" -B -m scripts.stage1_s1.reading_input --reading plan_a --kit "$KIT" --no-overlap \
  --out "$SCR/prerun-tables.json" --record "$SCR/prerun-sources.json" --hb-out "$SCR/prerun-hb_tables.json" "${COH_PRE[@]}" > "$LOGS/R1b-builder-prerun.txt" 2>&1
c=$?; ledger R1b-builder-prerun $c "$SCR/prerun-tables.json" "$SCR/prerun-sources.json" "$SCR/prerun-hb_tables.json" "$SCR/prerun-coherent_counts.json"
(( c == 0 )) || fail R1b "the builder refused; no outcome was shown (S2; a coherent-only refusal is D-5's (c) route)"
lines_check "$LOGS/R1b-builder-prerun.txt" "overlap: not included (--no-overlap)" --outs "$SCR/prerun-tables.json" "$SCR/prerun-sources.json" "$SCR/prerun-hb_tables.json" ${COH_PRE[2]} --counts "${EXPECT[@]}" > "$LOGS/R1b-check.txt" 2>&1
c=$?; ledger R1b-check $c; (( c == 0 )) || fail R1b "a builder identity line is not as pinned; no outcome was shown (S2)"

# Step 1: B14's report (its stdout holds the first outcome lines: three S-p verdict texts, report only)
date -u
"$PY" -B scripts/stage1_s1/overlap_strata.py report --strata "$STRATA" --inputs "$B14IN" --out "$RUN/b14" > "$LOGS/1-b14.txt" 2>&1
c=$?; ledger 1-b14 $c "$RUN/b14/overlap_report.json"; (( c == 0 )) || fail 1 "B14 refused after its pre-run passed (S2: no verdict printed)"
cmp -s "$RUN/b14/overlap_report.json" "$SCR/b14-prerun/overlap_report.json"
c=$?; ledger 1-same-as-prerun $c; (( c == 0 )) || fail 1 "B14's report differs from its pre-run (S6)"
REPORT_SHA=$(shasum -a 256 "$RUN/b14/overlap_report.json" | cut -c1-64); chmod a-w "$RUN/b14/overlap_report.json"

# Step 2: the input build, with the overlap block, the HarmBench tables and (mode coherent) D-5's counts document
date -u
"$PY" -B -m scripts.stage1_s1.reading_input --reading plan_a --kit "$KIT" \
  --b14-strata "$STRATA" --b14-report "$RUN/b14/overlap_report.json" \
  --expect-strata-sha256 "$STRATA_SHA" --expect-report-sha256 "$REPORT_SHA" \
  --out "$RUN/input/tables.json" --record "$RUN/input/sources.json" --hb-out "$RUN/input/hb_tables.json" "${COH_RUN[@]}" > "$LOGS/2-builder.txt" 2>&1
c=$?; ledger 2-builder $c "$RUN/input/tables.json" "$RUN/input/sources.json" "$RUN/input/hb_tables.json" "$RUN/input/coherent_counts.json"
(( c == 0 )) || fail 2 "the builder refused (S4)"
chmod a-w "$RUN"/input/*.json
lines_check "$LOGS/2-builder.txt" "overlap: strata $STRATA_SHA, report $REPORT_SHA" --outs "$RUN/input/tables.json" "$RUN/input/sources.json" "$RUN/input/hb_tables.json" ${COH_RUN[2]} --counts "${EXPECT[@]}" > "$LOGS/2-check.txt" 2>&1
c=$?; ledger 2-check $c; (( c == 0 )) || fail 2 "a builder identity line is not as pinned (S4)"
"$PY" -I -B - "$SCR" "$RUN/input" "$MODE" > "$LOGS/2-same-as-prerun.txt" 2>&1 <<'EOF'
import json, pathlib, sys
scr, inp, mode = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
load = lambda q: json.loads(q.read_text())
t0, t1 = load(scr / "prerun-tables.json"), load(inp / "tables.json")
s0, s1 = load(scr / "prerun-sources.json"), load(inp / "sources.json")
h0, h1 = load(scr / "prerun-hb_tables.json"), load(inp / "hb_tables.json")
for t in (t0, t1):
    t.pop("overlap", None)
for s in (s0, s1):          # the hashes bound to tables.json, which differs by the overlap block (LR R6.1)
    s.pop("overlap", None)
    s.pop("output_sha256", None)
    (s.get("hb") or {}).pop("output_sha256", None)
    (s.get("coherent") or {}).pop("output_sha256", None)
for h in (h0, h1):
    h.pop("input_sha256", None)
same = {"tables_without_overlap": t0 == t1, "sources_without_overlap_and_output_hashes": s0 == s1,
        "hb_tables_without_input_hash": h0 == h1}
if mode == "coherent":
    c0, c1 = load(scr / "prerun-coherent_counts.json"), load(inp / "coherent_counts.json")
    for c in (c0, c1):
        c.pop("input_sha256", None)
    same["coherent_counts_without_input_hash"] = c0 == c1
print(json.dumps({**same, "pass": all(same.values())}, sort_keys=True))
sys.exit(0 if all(same.values()) else 1)
EOF
c=$?; ledger 2-same-as-prerun $c; (( c == 0 )) || fail 2 "the input differs from the pre-run beyond the overlap block (S4)"

# Step 3: B16 (its stdout holds the headline words); provenance; a byte-for-byte re-run
date -u
"$PY" -B -m scripts.stage1_s1.reading --input "$RUN/input/tables.json" --out "$RUN/b16/reading.json" > "$LOGS/3-b16.txt" 2>&1
c=$?; ledger 3-b16 $c "$RUN/b16/reading.json"; (( c == 0 )) || fail 3 "B16 refused (S4)"
chmod a-w "$RUN/b16/reading.json"
prov "$RUN/b16/reading.json" "kind=stage1 reading output" reading=plan_a b16self "input_sha256=$RUN/input/tables.json" > "$LOGS/3-provenance.txt" 2>&1
c=$?; ledger 3-provenance $c; (( c == 0 )) || fail 3 "B16's provenance is not the pinned input, code, settings or Python (S5)"
"$PY" -B -m scripts.stage1_s1.reading --input "$RUN/input/tables.json" --out "$SCR/reading-rerun.json" > "$LOGS/3b-b16-rerun.txt" 2>&1
c=$?; ledger 3b-b16-rerun $c "$SCR/reading-rerun.json"; (( c == 0 )) || fail 3b "the B16 re-run refused (S6)"
cmp -s "$RUN/b16/reading.json" "$SCR/reading-rerun.json"
c=$?; ledger 3b-same-as-rerun $c; (( c == 0 )) || fail 3b "B16 is not byte-reproducible (S6)"

# Step 4: the HarmBench claim reader (its stdout holds the sentence words); provenance
date -u
"$PY" -B -m scripts.stage1_s1.reading_input.hb_claim --hb "$RUN/input/hb_tables.json" --reading "$RUN/b16/reading.json" --out "$RUN/hb/hb_claim.json" > "$LOGS/4-hb-claim.txt" 2>&1
c=$?; ledger 4-hb-claim $c "$RUN/hb/hb_claim.json"; (( c == 0 )) || fail 4 "the claim reader refused (S4)"
chmod a-w "$RUN/hb/hb_claim.json"
prov "$RUN/hb/hb_claim.json" "kind=stage1 HarmBench claim reading" reading=plan_a "hb_tables_sha256=$RUN/input/hb_tables.json" \
  "reading_sha256=$RUN/b16/reading.json" "input_sha256=$RUN/input/tables.json" "modules=scripts/stage1_s1/reading_input/:hb.py,hb_claim.py" b16 > "$LOGS/4-provenance.txt" 2>&1
c=$?; ledger 4-provenance $c; (( c == 0 )) || fail 4 "the claim reader's provenance is not as pinned (S5)"

# Step 4b: D-5's reader beside B16 (S-G coherent-only U, its words and headline word, both G3a corners; its stdout
# holds the S-G coherent headline words). Logged; never a stop (D-5 item 8; section 39 point 8(d)(i)).
date -u
if [[ $MODE == coherent ]]; then
  "$PY" -B -m scripts.stage1_s1.reading_input.sg_coherent --tables "$RUN/input/tables.json" --counts "$RUN/input/coherent_counts.json" \
    --reading "$RUN/b16/reading.json" --out "$RUN/sg/sg_coherent.json" > "$LOGS/4b-sg-coherent.txt" 2>&1
  c=$?; ledger 4b-sg-coherent $c "$RUN/sg/sg_coherent.json"
  if (( c != 0 )); then   # nothing was written (the reader's refusal), so there is no provenance to check
    print -r -- "step 4b: exit $c, logged; the reading goes on; the record prints D-5 item 8's wording"
    ledger 4b-provenance 1 "note=not run: the reader wrote no output (its exit $c)"
  else
    prov "$RUN/sg/sg_coherent.json" "kind=stage1 S-G coherent reading" reading=plan_a "tables_sha256=$RUN/input/tables.json" \
      "counts_sha256=$RUN/input/coherent_counts.json" "reading_sha256=$RUN/b16/reading.json" \
      "modules=scripts/stage1_s1/reading_input/:coherent.py,sg_coherent.py" b16 > "$LOGS/4b-provenance.txt" 2>&1
    c=$?; ledger 4b-provenance $c
    (( c == 0 )) || print -r -- "step 4b: provenance check exit $c, logged; the record prints D-5 item 8's wording"
  fi
else
  ledger 4b-sg-coherent 0 "note=not run: D-5 went to its last fallback (c) at the pre-run (mode no-coherent)"
fi

# Step 4c: the reading-time readers (report only; logged; never a stop: section 39 point 8(d)(i)). cap_reports opens
# the O-ext summaries and COMPLETE.json files the builder's record names; cost_table opens plan.json, the seals and the
# cost ledgers: the never-open list's one explicit exception, inside this script only (LR R4.4).
date -u
extra cap_reports "input:sources.json=$RUN/input/sources.json" kit -- --kit "$KIT" --record "$RUN/input/sources.json"
extra fk_power "input:tables.json=$RUN/input/tables.json" "input:reading.json=$RUN/b16/reading.json" -- --input "$RUN/input/tables.json" --reading "$RUN/b16/reading.json"
extra stage3_pick "input:reading.json=$RUN/b16/reading.json" -- --reading "$RUN/b16/reading.json"
extra sa_shift "input:reading.json=$RUN/b16/reading.json" -- --reading "$RUN/b16/reading.json"
extra cost_table kit -- --kit "$KIT" --reading plan_a

# Step 5: LN-31's draw (totals only) and its second-process check (D-7; LR R5.5). Logged; never a stop: the draw is
# report-only (REV4:762), and its pre-set fallback is "no step 5 at the reading" (E-misc B ruling 3). The sealed key
# and weights go under the main checkout's git-ignored tmp/ (HLC 9); the text-free manifest is committed with the run.
date -u
HLC=(--kit "$KIT" --oct9-key "$OCT9KEY" --bank-manifest "$V3/manifest.json" --bank "$V3/banks/dev.jsonl"
     --auditor "$V3/auditor/construction.json" --sealed "$ROOT/tmp/hlc/draw-$STAMP" --manifest "$RUN/hlc/hlc_manifest.json")
"$PY" -B -m scripts.stage1_s1.hlc_draw draw "${HLC[@]}" > "$LOGS/5-hlc-draw.txt" 2>&1
c=$?; ledger 5-hlc-draw $c "$ROOT/tmp/hlc/draw-$STAMP/hlc_key.json" "$ROOT/tmp/hlc/draw-$STAMP/hlc_weights.json" "$RUN/hlc/hlc_manifest.json"
if (( c == 0 )); then
  "$PY" -B -m scripts.stage1_s1.hlc_draw check "${HLC[@]}" > "$LOGS/5b-hlc-check.txt" 2>&1
  c=$?; ledger 5b-hlc-check $c
  (( c == 0 )) || print -r -- "step 5b: the second process does not reproduce the draw (exit $c), logged; a limit for the record"
else
  print -r -- "step 5: the draw did not run (exit $c; 2 = refused, nothing written; no outcome shown), logged; the record says 'not run at the reading' (D-7's fallback)"
fi

date -u; print "READING STEPS R0-5 DONE"; shasum -a 256 "$LEDGER"
exit 0
