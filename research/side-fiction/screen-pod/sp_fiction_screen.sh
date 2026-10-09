#!/bin/bash
# The fiction training-data screen on one RunPod A100 (Side Project build, 9 Oct 2026; the lead launches after review).
# usage: sp_fiction_screen.sh bundle|launch|summarize ROUND [REFILL_SHA256]    or    sp_fiction_screen.sh final-reads
#   ROUND 1: the pinned dark.jsonl, light.jsonl and Dolly train rows. ROUND 2 or 3: sf_screen.py's
#   $W/tmp/side-fiction/screen/refill-rROUND.jsonl, with its SHA-256 as the third argument.
#   TAG defaults to sp-fiction-screen-rROUND; every launch needs a new tag (TAG=sp-fiction-screen-r1b for a relaunch).
#   RESUME=<old tag> resumes an exit-5 run's caches. LIMIT=N (N rows of each source) is for dry checks only: a launch
#   with LIMIT set is refused. The script prints the command, round, TAG, LIMIT and RESUME before it runs anything.
#   final-reads (after sf_screen.py finalize): the pre-registration's reads on the final training rows.
ROOT=/Users/spiderishi/Coding/attribution
W=$ROOT/.claude/worktrees/peaceful-jepsen-8b8eee
K=$ROOT/tmp/family-probe-sp-fiction-screen
PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
export PYTHONDONTWRITEBYTECODE=1
CMD="$1"; ROUND="$2"; REFILL_SHA="$3"
if [ "$CMD" = final-reads ]; then
  exec "$PY" -B "$K/tool/screen_pod.py" final-reads --final-dir "$W/tmp/side-fiction/final" --screen-dir "$W/tmp/side-fiction/screen"
fi
case "$ROUND" in 1|2|3) ;; *) echo "usage: $0 bundle|launch|summarize 1|2|3 [REFILL_SHA256]" >&2; exit 2 ;; esac
TAG="${TAG:-sp-fiction-screen-r$ROUND}"
echo "sp_fiction_screen: $CMD round $ROUND tag $TAG limit ${LIMIT:-none} resume ${RESUME:-none}" >&2
if [ "$CMD" = launch ] && [ -n "${LIMIT:-}" ]; then
  echo "refused: LIMIT is for dry checks (bundle) only; unset it for a launch" >&2; exit 2
fi
ARGS=(--tag "$TAG" --round "$ROUND")
if [ "$ROUND" != 1 ]; then
  [ -n "$REFILL_SHA" ] || { echo "round $ROUND needs the refill file's SHA-256" >&2; exit 2; }
  ARGS+=(--refill "$W/tmp/side-fiction/screen/refill-r$ROUND.jsonl" --refill-sha256 "$REFILL_SHA")
fi
if [ -n "${LIMIT:-}" ]; then ARGS+=(--limit "$LIMIT"); fi
if [ -n "${RESUME:-}" ]; then ARGS+=(--resume-from "$K/runs/$RESUME"); fi
case "$CMD" in
  bundle) "$PY" -B "$K/tool/screen_pod.py" bundle "${ARGS[@]}" --out "$K/dry/$TAG" ;;
  launch) ( set -a; . ~/.config/attribution/secrets.env; set +a; exec env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN caffeinate -i "$PY" -B "$K/tool/screen_pod.py" launch "${ARGS[@]}" ) ;;
  summarize) "$PY" -B "$K/tool/screen_pod.py" summarize --from "$K/runs/$TAG" --out "$W/tmp/side-fiction/screen" ;;
  *) echo "usage: $0 bundle|launch|summarize 1|2|3 [REFILL_SHA256]" >&2; exit 2 ;;
esac
