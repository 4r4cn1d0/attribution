"""Print the comma-joined mutant ids of SPEC from 1-based index A to B inclusive. Usage: PY -B -I ids.py SPEC A B"""
import json
import sys
d = json.load(open(sys.argv[1]))
print(",".join(m["id"] for m in d["mutants"][int(sys.argv[2]) - 1:int(sys.argv[3])]))
