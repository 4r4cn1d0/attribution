#!/bin/zsh
# The dry-run ROOT: code by symlink (main checkout) and copy (the three unmerged packages), placeholders for the named records.
set -e
V2=/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/verify-runbook/v2
WS=/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds
MAIN=/Users/spiderishi/Coding/attribution
R=$V2/root
RD=$R/.ai/inputs/stage1-post-w1-20261023/reading
test ! -e $R || { print "refuse: $R exists"; exit 1 }
mkdir -p $R/experiments $R/scripts/stage1_s1 $R/runkit/stage1-olmo $R/tmp/stage1-olmo $RD/b14/strata $RD/b14/inputs $RD/timestamp $R/.ai/briefs $R/docs $R/.git
print "tmp/" > $R/.gitignore
ln -s $MAIN/experiments/safety_selection $R/experiments/safety_selection
ln -s $MAIN/experiments/minimal_safety $R/experiments/minimal_safety
ln -s $MAIN/scripts/stage1 $R/scripts/stage1
ln -s $MAIN/scripts/family_probe_reading.py $R/scripts/family_probe_reading.py
ln -s $MAIN/scripts/killtest_stage0_reading.py $R/scripts/killtest_stage0_reading.py
for e in $MAIN/scripts/stage1_s1/*; do n=${e:t}; [[ $n == reading_input || $n == tests ]] && continue; ln -s $e $R/scripts/stage1_s1/$n; done
rsync -a --exclude __pycache__ $WS/ws-a/scripts/stage1_s1/reading_input $R/scripts/stage1_s1/
rsync -a --exclude __pycache__ $WS/ws-d1/scripts/stage1_s1/reading_extra $R/scripts/stage1_s1/
rsync -a --exclude __pycache__ $WS/ws-d2/scripts/stage1_s1/hlc_draw $R/scripts/stage1_s1/
for n in seal.py plan_tool.py judge_units_stage1.py tests; do ln -s $MAIN/runkit/stage1-olmo/$n $R/runkit/stage1-olmo/$n; done
for n in seal.py plan_tool.py judge_units_stage1.py; do ln -s $MAIN/runkit/stage1-olmo/$n $R/tmp/stage1-olmo/$n; done
print "placeholder: B14 inputs (dry run)" > $RD/b14/inputs/overlap_inputs.json
print "placeholder: similarity copy (dry run)" > $RD/b14/similarity.json
print "placeholder: the addendum (dry run)" > $R/.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md
print "placeholder: the S1 blinding record (dry run)" > $RD/s1-blinding-record-dry.md
print "placeholder: the study plan (dry run)" > $R/docs/study-plan-full.md
print "root built"
