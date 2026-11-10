#!/bin/zsh
# Copy R1's files from the worktrees into MAIN by explicit path; refuse a clash; cmp each.
set -e
M=/Users/spiderishi/Coding/attribution; B=$1; L=$2; : > $L/merge-list.txt
for w in ws-k2 ws-r; do
  git -C $B/$w status --porcelain --untracked-files=all | grep -v ' tmp/' | grep -v '__pycache__' | while read -r st p; do
    if [ "$st" = "M" ]; then git -C $M diff --quiet bfda225 -- "$p" || { echo "MAIN CHANGED $p"; exit 1; }
    elif [ -e "$M/$p" ] && ! cmp -s "$B/$w/$p" "$M/$p"; then echo "CLASH $p"; exit 1; fi
    mkdir -p "$(dirname "$M/$p")"; cp -p "$B/$w/$p" "$M/$p"; cmp "$B/$w/$p" "$M/$p"
    echo "$w $st $(shasum -a 256 "$M/$p" | cut -c1-64) $p" >> $L/merge-list.txt
  done
done
wc -l < $L/merge-list.txt
