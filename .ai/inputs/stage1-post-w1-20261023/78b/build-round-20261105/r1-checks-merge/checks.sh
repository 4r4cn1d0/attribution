#!/bin/zsh
M=/Users/spiderishi/Coding/attribution; L=$1
PY=$M/tmp/minimal-experiment-20261002/venv/bin/python
SB='(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'
cd $M; export PYTHONDONTWRITEBYTECODE=1
echo "start $(date -u +%H:%M:%S) $(git rev-parse --short HEAD) (+ R1 working-tree copies)" > $L/summary.txt
sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests > $L/suite-78b.log 2>&1; echo "suite-78b exit $? : $(tail -1 $L/suite-78b.log)" >> $L/summary.txt
$PY -B -m pytest -p no:cacheprovider -q runkit/stage1-olmo/tests > $L/suite-olmo.log 2>&1; echo "suite-olmo exit $? : $(tail -1 $L/suite-olmo.log)" >> $L/summary.txt
sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests > $L/suite-scale78b.log 2>&1; echo "suite-scale78b exit $? : $(tail -1 $L/suite-scale78b.log)" >> $L/summary.txt
for r in run_mutants_78b run_mutants_runner_78b run_mutants_scorer_78b run_mutants_gated_78b; do sandbox-exec -p "$SB" $PY -B runkit/stage1-78b/tests/$r.py $M $L/$r $L/$r.json ALL > $L/$r.log 2>&1; echo "$r exit $? : $(tail -1 $L/$r.log | cut -c1-150)" >> $L/summary.txt; rm -rf $L/$r; done
sandbox-exec -p "$SB" $PY -B scripts/scale78b/tests/run_mutants_c_78b.py $M $L/mut-c $L/mut-c.json ALL > $L/mut-c.log 2>&1; echo "mut-c exit $? : $(tail -1 $L/mut-c.log | cut -c1-150)" >> $L/summary.txt; rm -rf $L/mut-c
sandbox-exec -p "$SB" $PY -B scripts/scale78b/tests/oext/run_mutants_oext_78b.py $M $L/mut-oext $L/mut-oext.json ALL --timeout 600 > $L/mut-oext.log 2>&1; echo "mut-oext exit $? : $(tail -1 $L/mut-oext.log | cut -c1-150)" >> $L/summary.txt; rm -rf $L/mut-oext
sandbox-exec -p "$SB" $PY -B scripts/scale78b/tests/run_mutants_sr2.py $M $L/mut-sr2 $L/mut-sr2.json ALL --timeout 300 > $L/mut-sr2.log 2>&1; echo "mut-sr2 exit $? : $(tail -1 $L/mut-sr2.log | cut -c1-150)" >> $L/summary.txt; rm -rf $L/mut-sr2
git -C $M status --porcelain -- experiments scripts/stage1 scripts/stage1_s1 runkit/stage1-olmo >> $L/summary.txt
find $M/runkit $M/scripts -name __pycache__ >> $L/summary.txt
echo "end $(date -u +%H:%M:%S)" >> $L/summary.txt
