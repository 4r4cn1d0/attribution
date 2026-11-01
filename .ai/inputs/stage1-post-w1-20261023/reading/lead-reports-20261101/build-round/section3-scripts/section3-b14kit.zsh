#!/bin/zsh
# Runbook section 3: B14's 69-entry near set and kit round 34's 39 ids, on the final tree.
ROOT=/Users/spiderishi/Coding/attribution; PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
SCR=/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/runs/s3
STAMP=20261101
CHK=$ROOT/.ai/inputs/stage1-post-w1-20261023/reading/checks-$STAMP; mkdir -p "$CHK"
cd "$ROOT" || exit 1
print "start $(date -u +%FT%TZ) HEAD $(git rev-parse --short HEAD)"
NEAR=.ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/build-round/mutants_b14_near.json
"$PY" -B scripts/stage1_s1/mutation/run_mutants_b14.py --spec "$NEAR" --scratch "$SCR/b14-near" --report "$CHK/b14-near.json" --timeout 900 > "$CHK/b14-near.log" 2>&1
print "b14-near exit $?: $(tail -1 $CHK/b14-near.log | cut -c1-150)"; rm -rf "$SCR/b14-near"
IDS=$("$PY" -B -c "import json;d=json.load(open('runkit/stage1-olmo/tests/mutants_b15.json'));print(','.join(m['id'] for m in d['mutants'] if m['id'].startswith('B15-34-') or m['id'] in ('B15-r-o-only-unit','B15-8-runner-settings-unpinned','B15-g-no-recorded-recipe')))")
"$PY" -B research/experiments/2026-10-24-stage1-runkit/run_mutants_b15.py "$ROOT" "$SCR/kit34" "$CHK/kit-round-34-mutation-report.json" "$IDS" > "$CHK/kit34.log" 2>&1
print "kit34 exit $?: $(tail -1 $CHK/kit34.log | cut -c1-150)"; rm -rf "$SCR/kit34"
print "end $(date -u +%FT%TZ)"
