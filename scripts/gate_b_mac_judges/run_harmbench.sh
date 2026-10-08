#!/bin/bash
# Launch the Gate B HarmBench judge under caffeinate and the memory/disk watchdog; one Metal process at a time.
#   bash run_harmbench.sh LOGDIR [SWAP_LIMIT_GB] -- run --cache CACHE (--run-root R)... (--unit U)... [--limit N]
# Made from tmp/family-probe-olmo2-1b/run_harmbench.sh (same environment, same 8 GB swap default, same watchdog rule).
# START/END lines with UTC times and the watchdog lines go to LOGDIR/harmbench-run.log; the judge's own output
# (counts only) to LOGDIR/harmbench-progress.log. Exit 2: SWAP_GB is not a positive number (nothing started); exit 3:
# another Mac judge is running; exit 4: the watchdog was not alive 2 s after start while the judge was (the judge is
# stopped). Otherwise the judge's own exit code: 0 done, 2 refused, 5 stopped by SIGTERM (the watchdog; resumable).
set -u
LOGDIR=${1:?usage: run_harmbench.sh LOGDIR [SWAP_GB] -- ARGS}; shift
SWAP_GB=8
if [ "${1:-}" != "--" ]; then SWAP_GB=${1:?missing --}; shift; fi
[ "${1:-}" = "--" ] && shift
# SWAP_GB must be a positive decimal number (the watchdog's --swap-gb); anything else exits 2 before any start.
if ! [[ "$SWAP_GB" =~ ^[0-9]+([.][0-9]+)?$ ]] || [[ "$SWAP_GB" =~ ^0+([.]0+)?$ ]]; then
    echo "SWAP_GB must be a positive number (got '$SWAP_GB')"; exit 2
fi
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$LOGDIR"
LOG=$LOGDIR/harmbench-run.log
PROGRESS=$LOGDIR/harmbench-progress.log
JUDGES='harmbench_judge.py (smoke|run)|harmbench_files.py (check|run)|second_judge_probe.py|granite_files.py (check|run)'
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
alive() { local st; st=$(ps -p "$1" -o stat= 2>/dev/null) || return 1; [ -n "$st" ] && [ "${st#Z}" = "$st" ]; }
state() { echo "swap_used=$(sysctl -n vm.swapusage | sed -E 's/.*used = ([0-9.]+M).*/\1/') free_disk_kb=$(df -k ~ | tail -1 | awk '{print $4}') level=$(sysctl -n kern.memorystatus_vm_pressure_level)"; }

if pgrep -f "$JUDGES" >/dev/null; then echo "a judge is already running (one Metal process at a time)"; exit 3; fi
echo "$(now) START harmbench $* (HarmBench judge on MPS, GPU in use) before: $(state)" >> "$LOG"
env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN -u HUGGINGFACE_HUB_TOKEN -u HF_API_TOKEN \
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_DISABLE_TELEMETRY=1 \
    PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$HERE/harmbench_files.py" "$@" >> "$PROGRESS" 2>&1 &
JPID=$!
caffeinate -i -w "$JPID" &
"$PY" -B "$HERE/watchdog.py" --pid "$JPID" --swap-gb "$SWAP_GB" --log "$LOG" --tag "watchdog-harmbench" &
WPID=$!
sleep 2
# A dead watchdog with a live judge: no watchdog, no run (stop the judge: TERM, then KILL after 5 s; exit 4). A judge
# that has already ended (the watchdog exits with it) falls through, so its own exit code is waited for and logged.
if ! alive "$WPID" && alive "$JPID"; then
    echo "$(now) WATCHDOG NOT ALIVE 2 s after start; stopping the judge pid=$JPID" >> "$LOG"
    kill -TERM "$JPID" 2>/dev/null
    for _ in 1 2 3 4 5; do alive "$JPID" || break; sleep 1; done
    kill -KILL "$JPID" 2>/dev/null
    wait "$JPID" 2>/dev/null
    echo "$(now) END harmbench exit=4 (watchdog not alive; judge stopped; GPU free) after: $(state)" >> "$LOG"
    exit 4
fi
wait "$JPID"; RC=$?
wait "$WPID"
echo "$(now) END harmbench exit=$RC (GPU free) after: $(state)" >> "$LOG"
exit $RC
