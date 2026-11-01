#!/bin/zsh
if [[ $1 == -C ]]; then shift 2; fi
case $1 in
  rev-parse) print dryrun ;;
  status) print " M scripts/stage1_s1/reading/reading.py" ;;
esac
