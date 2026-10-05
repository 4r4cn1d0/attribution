#!/bin/bash
# Poll the lead host for edit files; add each file's hash to plan.json once it is collected (administrative).
cd /Users/spiderishi/Coding/attribution/tmp/headroom-20261005
for i in $(seq 1 400); do
  python3.11 orchestrate.py collect-lead >> collect.log 2>&1
  n=0; for f in remove-10.json random-remove-10.json rewrite-10.json random-rewrite-10.json; do [ -f edits/$f ] && n=$((n+1)); done
  if [ $n -ge 2 ]; then python3.11 make_plan.py --steps lead-steps.json --edits >> collect.log 2>&1; fi
  if [ $n -eq 4 ]; then echo "all four edit files collected" >> collect.log; exit 0; fi
  sleep 60
done
