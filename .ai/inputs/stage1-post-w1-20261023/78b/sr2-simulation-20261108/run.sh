#!/bin/zsh
WS=$1; O=$2
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
cd $WS
export PYTHONDONTWRITEBYTECODE=1
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ) sr2 $(shasum -a 256 scripts/scale78b/sr2_simulation.py | cut -c1-64) settings $(shasum -a 256 scripts/scale78b/settings/sr2_simulation.json | cut -c1-64)" > $O/summary.txt
for OPT in B C; do
  for i in 0 1 2 3 4 5 6 7 8; do
    $PY -I -B scripts/scale78b/sr2_simulation.py --settings scripts/scale78b/settings/sr2_simulation.json --option $OPT --design full --sigma $i --out $O/sr2-$OPT-full-s$i.json > $O/sr2-$OPT-full-s$i.log 2>&1 &
  done
  wait
  for i in 0 1 2 3 4 5 6 7 8; do echo "$OPT shard $i: $(tail -1 $O/sr2-$OPT-full-s$i.log | cut -c1-120)" >> $O/summary.txt; done
  $PY -I -B scripts/scale78b/sr2_simulation.py --merge $O/sr2-$OPT-full-s{0,1,2,3,4,5,6,7,8}.json --out $O/sr2-$OPT-full.json > $O/sr2-$OPT-full-merge.log 2>&1
  echo "$OPT merge exit $? at $(date -u +%H:%M:%S)" >> $O/summary.txt
done
echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $O/summary.txt
