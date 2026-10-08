#!/bin/bash
# Create host groups only when their edit files are collected and hashed into plan.json (administrative).
cd /Users/spiderishi/Coding/attribution/tmp/headroom-20261005
has_hash() { python3 -c "import json,sys;p=json.load(open('plan.json'));sys.exit(0 if all(p['hosts'][h].get('edit_sha256') for h in sys.argv[1:]) else 1)" "$@"; }
removal_done=0; rewrite_done=0
for i in $(seq 1 600); do
  if [ $removal_done -eq 0 ] && has_hash rm10-1101 rm10-1102 rrm10-1101 rrm10-1102; then
    nohup python3.11 launch.py rm10-1101 rm10-1102 rrm10-1101 rrm10-1102 > launch-phaseB2.log 2>&1 &
    echo "$(date -u +%FT%TZ) removal hosts launched" >> auto_launch.log; removal_done=1
  fi
  if [ $rewrite_done -eq 0 ] && has_hash rw10-1101 rw10-1102 rrw10-1101 rrw10-1102; then
    nohup python3.11 launch.py rw10-1101 rw10-1102 rrw10-1101 rrw10-1102 > launch-phaseC.log 2>&1 &
    echo "$(date -u +%FT%TZ) rewrite hosts launched" >> auto_launch.log; rewrite_done=1
  fi
  [ $removal_done -eq 1 ] && [ $rewrite_done -eq 1 ] && exit 0
  sleep 30
done
