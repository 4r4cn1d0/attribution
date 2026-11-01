"""Dry-run copies of reading.zsh: the settings block pointed at the synthetic ROOT, and R1a/step 1 (B14's report) replaced
by a copy of the synthetic report. Every other byte is the original's. Each replaced line must match exactly once."""
import sys
from pathlib import Path
src, V, strata_sha = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
text = src.read_text()
R = V / "root"
def make(stamp: str) -> Path:
    t = text
    reps = [
        ('ROOT=/Users/spiderishi/Coding/attribution                  # the main checkout', f'ROOT={R}   # DRY RUN: the synthetic root'),
        ('PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python   # Python 3.11.15', 'PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python   # DRY RUN: the real venv'),
        ('STAMP=FILL-0                                               # the second stamp', f'STAMP={stamp}   # DRY RUN'),
        ('SCR=/private/tmp/stage1-reading-scratch                    # outside the repository', f'SCR={V}/scr-{stamp}   # DRY RUN'),
        ('STRATA_SHA=FILL-STRATA-SHA256                              # its SHA-256', f'STRATA_SHA={strata_sha}   # DRY RUN'),
        ('"$PY" -B scripts/stage1_s1/overlap_strata.py report --strata "$STRATA" --inputs "$B14IN" --out "$SCR/b14-prerun" >| /dev/null 2> "$LOGS/R1a-b14-prerun-stderr.txt"',
         'mkdir -p "$SCR/b14-prerun" && cp "$ROOT/tmp/synth-b14/overlap_report.json" "$SCR/b14-prerun/overlap_report.json" >| /dev/null 2> "$LOGS/R1a-b14-prerun-stderr.txt"   # DRY RUN: the synthetic report stands in for B14'),
        ('"$PY" -B scripts/stage1_s1/overlap_strata.py report --strata "$STRATA" --inputs "$B14IN" --out "$RUN/b14" > "$LOGS/1-b14.txt" 2>&1',
         'mkdir -p "$RUN/b14" && cp "$ROOT/tmp/synth-b14/overlap_report.json" "$RUN/b14/overlap_report.json" > "$LOGS/1-b14.txt" 2>&1   # DRY RUN: the synthetic report stands in for B14'),
    ]
    for old, new in reps:
        n = sum(1 for line in t.splitlines() if line.startswith(old))
        assert n == 1, (old, n)
        lines = t.splitlines(keepends=True)
        out = []
        for line in lines:
            if line.startswith(old):
                out.append(new + "\n")
            else:
                out.append(line)
        t = "".join(out)
    dest = V / f"reading-dry-{stamp}.zsh"
    dest.write_text(t)
    return dest
for stamp in ("20261199", "20261198"):
    print("wrote", make(stamp))
