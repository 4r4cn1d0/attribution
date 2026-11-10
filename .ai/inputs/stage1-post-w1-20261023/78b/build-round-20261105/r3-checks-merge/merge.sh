#!/bin/zsh
# Copy R3's files from the worktrees into MAIN by explicit path; refuse a clash, a deletion or a MAIN change; cmp each.
set -e
M=/Users/spiderishi/Coding/attribution; B=$1; L=$2; BASE=d7eb772; : > $L/merge-list.txt
for w in ${=3}; do
  git -C $B/$w status --porcelain --untracked-files=all | grep -v ' tmp/' | grep -v '__pycache__' | while read -r st p; do
    case "$st" in
      M) git -C $M diff --quiet $BASE -- "$p" || { echo "MAIN CHANGED $p"; exit 1; } ;;
      "??") if [ -e "$M/$p" ] && ! cmp -s "$B/$w/$p" "$M/$p"; then echo "CLASH $p"; exit 1; fi ;;
      *) echo "UNHANDLED STATUS $st $p ($w)"; exit 1 ;;
    esac
    grep -q " $p\$" $L/merge-list.txt && { echo "TWO WORKTREES CHANGE $p"; exit 1; }
    mkdir -p "$(dirname "$M/$p")"; cp -p "$B/$w/$p" "$M/$p"; cmp "$B/$w/$p" "$M/$p"
    echo "$w $st $(shasum -a 256 "$M/$p" | cut -c1-64) $p" >> $L/merge-list.txt
  done
done
wc -l < $L/merge-list.txt
