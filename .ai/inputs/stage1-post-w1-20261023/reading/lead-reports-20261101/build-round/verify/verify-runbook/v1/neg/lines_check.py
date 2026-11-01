import hashlib, json, pathlib, sys
m2, log, overlap_line, *rest = sys.argv[1:]
m = json.loads(pathlib.Path(m2).read_text())
lines = pathlib.Path(log).read_text().splitlines()
outs = rest[rest.index("--outs") + 1:rest.index("--counts")]
counts = rest[rest.index("--counts") + 1:]
sha = lambda q: hashlib.sha256(pathlib.Path(q).read_bytes()).hexdigest()
identity = [f"(plan A); plan.json {m['kit']['plan_json_sha256']}",
            f"sha256 {m['files']['runkit/stage1-olmo/stage1_rules.py']}; B16 settings "
            f"{m['files']['scripts/stage1_s1/reading/settings/reading.json']}",
            f"seal A {m['kit']['seal_A']}", f"seal B {m['kit']['seal_B']}", overlap_line,
            *[f"wrote {q} sha256 {sha(q)}" for q in outs]]
missing = [w for w in identity if not any(w in line for line in lines)]
missing_counts = [w for w in counts if not any(w in line for line in lines)]
print(json.dumps({"identity_lines": len(identity), "missing_identity": missing, "count_lines": len(counts),
                  "missing_count_lines": missing_counts, "pass": not missing}, sort_keys=True))
sys.exit(0 if not missing else 1)
