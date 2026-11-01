"""Dry-run copies of reading.zsh: the settings block pointed at the synthetic ROOT, R1a/step 1 replaced by a copy of the
synthetic report. Variants: bad_4b (step 4b's --counts at a missing file: the reader must refuse, never a stop);
bad_strata (a wrong STRATA_SHA: the builder refuses at step 2, S4 stop); bad_prov3 (step 3's provenance check expects
plan_b: S5 stop). Every other byte is the original's. Each replaced line or substring must match exactly once."""
import sys
from pathlib import Path
src, T, strata_sha = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
text = src.read_text(); R = T / "root"
def make(stamp, variant=None):
    lines = text.splitlines(keepends=True)
    ssha = strata_sha if variant != "bad_strata" else "0" * 64
    reps = [
        ('ROOT=/Users/spiderishi/Coding/attribution                  # the main checkout', f'ROOT={R}   # DRY RUN: the synthetic root'),
        ('PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python   # Python 3.11.15', 'PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python   # DRY RUN: the real venv'),
        ('STAMP=FILL-STAMP                                           # the second stamp', f'STAMP={stamp}   # DRY RUN'),
        ('SCR=/private/tmp/stage1-reading-scratch                    # outside the repository', f'SCR={T}/scr-{stamp}   # DRY RUN'),
        ('STRATA_SHA=FILL-STRATA-SHA256                              # its SHA-256', f'STRATA_SHA={ssha}   # DRY RUN'),
        ('"$PY" -B scripts/stage1_s1/overlap_strata.py report --strata "$STRATA" --inputs "$B14IN" --out "$SCR/b14-prerun" >| /dev/null 2> "$LOGS/R1a-b14-prerun-stderr.txt"',
         'mkdir -p "$SCR/b14-prerun" && cp "$ROOT/tmp/synth-b14/overlap_report.json" "$SCR/b14-prerun/overlap_report.json" >| /dev/null 2> "$LOGS/R1a-b14-prerun-stderr.txt"   # DRY RUN: the synthetic report stands in for B14'),
        ('"$PY" -B scripts/stage1_s1/overlap_strata.py report --strata "$STRATA" --inputs "$B14IN" --out "$RUN/b14" > "$LOGS/1-b14.txt" 2>&1',
         'mkdir -p "$RUN/b14" && cp "$ROOT/tmp/synth-b14/overlap_report.json" "$RUN/b14/overlap_report.json" > "$LOGS/1-b14.txt" 2>&1   # DRY RUN: the synthetic report stands in for B14'),
    ]
    for old, new in reps:
        hits = [i for i, line in enumerate(lines) if line.startswith(old)]
        assert len(hits) == 1, (old, len(hits))
        lines[hits[0]] = new + "\n"
    t = "".join(lines)
    if variant == "bad_4b":
        old = '--counts "$RUN/input/coherent_counts.json" \\'
        assert t.count(old) == 1, t.count(old)
        t = t.replace(old, '--counts "$RUN/input/no-such-counts.json" \\')
    if variant == "bad_prov3":
        old = '"kind=stage1 reading output" reading=plan_a b16self'
        assert t.count(old) == 1, t.count(old)
        t = t.replace(old, '"kind=stage1 reading output" reading=plan_b b16self')
    dest = T / f"reading-dry-{stamp}.zsh"; dest.write_text(t); return dest
for stamp, variant in (("20261299", None), ("20261298", None), ("20261297", "bad_4b"), ("20261296", "bad_strata"), ("20261295", None), ("20261294", "bad_prov3")):
    print("wrote", make(stamp, variant))
