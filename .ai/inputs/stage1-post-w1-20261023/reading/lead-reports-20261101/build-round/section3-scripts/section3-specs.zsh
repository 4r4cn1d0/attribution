#!/bin/zsh
# Runbook section 3, the mutation specs of the builder (47), the readers (62) and the draw (65), four shards each.
ROOT=/Users/spiderishi/Coding/attribution; PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
SCR=/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/runs/s3
STAMP=20261101
CHK=$ROOT/.ai/inputs/stage1-post-w1-20261023/reading/checks-$STAMP; mkdir -p "$CHK"
cd "$ROOT" || exit 1
print "start $(date -u +%FT%TZ) HEAD $(git rev-parse --short HEAD)"
for P in reading_input:ri reading_extra:rx hlc_draw:hlc; do
  PKG=${P%%:*}; K0=${P##*:}
  SPEC=$(ls scripts/stage1_s1/$PKG/mutation/mutants_*.json)
  for K in 0 1 2 3; do
    IDS=$("$PY" -I -B -c 'import json, sys; ids = [m["id"] for m in json.load(open(sys.argv[1]))["mutants"]]; print(",".join(ids[int(sys.argv[2])::4]))' "$SPEC" $K)
    "$PY" -B scripts/stage1_s1/$PKG/mutation/run_mutants.py --spec "$SPEC" --scratch "$SCR/$K0-mut-$K" --report "$CHK/$K0-mut-$K.json" --python "$PY" --timeout 600 --only "$IDS" > "$CHK/$K0-mut-$K.log" 2>&1 &
  done; wait
  for K in 0 1 2 3; do print "$K0 shard $K: $(tail -1 $CHK/$K0-mut-$K.log | cut -c1-150)"; rm -rf "$SCR/$K0-mut-$K"; done
done
print "end $(date -u +%FT%TZ)"
