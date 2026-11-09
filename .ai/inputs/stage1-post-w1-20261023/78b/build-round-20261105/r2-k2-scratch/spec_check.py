import json, sys, collections
K = sys.argv[1]
for spec in ("scorer", "rules", "runner", "gated"):
    d = json.load(open(f"{K}/tests/mutation_spec_{spec}_78b.json"))
    ms = d["mutants"]
    bad = []
    for m in ms:
        src = open(f"{K}/{m['file']}").read()
        n = src.count(m["find"])
        if n != 1:
            bad.append((m["id"], n))
    dup = [i for i, c in collections.Counter(m["id"] for m in ms).items() if c > 1]
    same = collections.Counter((m["file"], m["find"], m["replace"]) for m in ms)
    print(spec, len(ms), "bad", bad, "dup", dup, "identical", sum(c > 1 for c in same.values()))
