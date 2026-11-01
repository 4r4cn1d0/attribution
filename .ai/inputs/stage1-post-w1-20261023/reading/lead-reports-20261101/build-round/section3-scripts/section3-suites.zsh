#!/bin/zsh
# Runbook section 3, the suites (not the judges suite, which runs alone later), on the final tree in the main checkout.
ROOT=/Users/spiderishi/Coding/attribution; KIT=$ROOT/tmp/stage1-olmo; PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
SCR=/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/runs/s3
STAMP=20261101
CHK=$ROOT/.ai/inputs/stage1-post-w1-20261023/reading/checks-$STAMP; mkdir -p "$CHK"
cd "$ROOT" || exit 1
T() { "$PY" -B -m pytest -q -p no:cacheprovider --basetemp="$SCR/bt-$1" "${@:2}" > "$CHK/suite-$1.txt" 2>&1; print "$1 exit $?"; tail -1 "$CHK/suite-$1.txt"; rm -rf "$SCR/bt-$1"; }
print "start $(date -u +%FT%TZ) HEAD $(git rev-parse --short HEAD)"
T b16   scripts/stage1_s1/reading/tests
T ri    scripts/stage1_s1/reading_input/tests
T rx    scripts/stage1_s1/reading_extra/tests
T hlc   scripts/stage1_s1/hlc_draw/tests scripts/stage1_s1/tests/test_s1_layout.py
T s1    scripts/stage1_s1
T w1    scripts/stage1/tests
T engx  experiments/safety_selection/tests
T kit   runkit/stage1-olmo/tests
"$PY" -B scripts/stage1/commitments.py check --repo "$ROOT" > "$CHK/commitments.txt" 2>&1; print "commitments exit $?"; tail -1 "$CHK/commitments.txt" | cut -c1-160
print "end $(date -u +%FT%TZ)"
