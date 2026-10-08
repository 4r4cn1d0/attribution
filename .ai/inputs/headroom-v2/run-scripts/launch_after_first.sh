#!/bin/bash
# Launch the calibration host only after the first host has chosen the recipe and recorded the fixture (administrative).
cd /Users/spiderishi/Coding/attribution/tmp/headroom-v2
for i in $(seq 1 240); do
  if [ -f expected-fixture-v2.json ] && python3 -c "import json,sys;sys.exit(0 if json.load(open('plan.json')).get('recipe_path') else 1)"; then
    python3.11 launch.py cal10 >> launch-cal10.log 2>&1; exit 0
  fi
  sleep 30
done
