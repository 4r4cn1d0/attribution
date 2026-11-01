#!/bin/zsh
# For each stamp: the runbook and script copies into RD, the manifest by the runbook's own step-0.6 writer (stand-in git),
# then the script copy in the foreground; console and exit code kept. 20261295: one byte appended to the pinned runbook copy
# after the manifest (R0 must stop, S1).
V2=/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/verify-runbook/v2
R=$V2/root; RD=$R/.ai/inputs/stage1-post-w1-20261023/reading; KIT=$R/tmp/stage1-olmo
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
export PATH=$V2/bin:$PATH PYTHONDONTWRITEBYTECODE=1
ANCHOR1="block 974039 (header time 2026-10-31T23:28:48 UTC) and block 974047 (2026-11-01T00:42:41 UTC); TS/ots-check-20261101.json"
for STAMP in 20261299 20261298 20261297 20261296 20261295 20261294; do
  M2=$RD/timestamp/ots-manifest-reading-$STAMP.json
  cp $V2/../../runbook/reading-runbook.md $RD/reading-runbook-$STAMP.md
  cp $V2/reading-dry-$STAMP.zsh $RD/reading-$STAMP.zsh
  cd $R
  "$PY" -I -B $V2/blocks/manifest_writer.py "$R" "$KIT" "$PY" "$M2" "$ANCHOR1" "$RD/reading-runbook-$STAMP.md" "$RD/reading-$STAMP.zsh" \
    "$RD/b14/inputs/overlap_inputs.json" "$RD/b14/strata/strata.json" "$RD/b14/similarity.json" \
    .ai/briefs/stage1-commitments-build-20261016-lead-decisions.md "$RD/s1-blinding-record-dry.md" docs/study-plan-full.md > $V2/manifest-$STAMP.txt 2>&1
  print "manifest $STAMP exit $? : $(cat $V2/manifest-$STAMP.txt | cut -c1-200)"
  if [[ $STAMP == 20261295 ]]; then print "# one byte after the stamp" >> $RD/reading-runbook-$STAMP.md; fi
  MODE=coherent; [[ $STAMP == 20261298 ]] && MODE=no-coherent
  cd /tmp
  zsh $RD/reading-$STAMP.zsh $MODE > $V2/console-$STAMP.txt 2>&1
  print "run $STAMP ($MODE) exit $? ; last line: $(tail -1 $V2/console-$STAMP.txt | cut -c1-120)"
done
