import json, pathlib, sys
kit, blocks = pathlib.Path(sys.argv[1]), sys.argv[2:]
plan = json.loads((kit / "plan.json").read_text())
c = {"hosts_done": 0, "jobs_complete_pulled": 0, "ledgers_named_in_plan": 0, "present": 0, "missing": [],
     "other_jobs_with_a_ledger_named": 0, "other_jobs_ledger_missing": []}
for host, h in sorted(plan["hosts"].items()):
    if h.get("block") not in blocks or h.get("done") is not True:
        continue
    c["hosts_done"] += 1
    for i, job in enumerate(h["jobs"]):
        if not isinstance(job, dict):
            continue
        rel = f"job-{i}/cost-ledger.json"
        named = isinstance(job.get("outputs"), dict) and rel in job["outputs"]
        present = (kit / "retrieved" / host / "tree" / rel).is_file()
        if job.get("status") == "complete" and job.get("pulled") is not False:
            c["jobs_complete_pulled"] += 1
            c["ledgers_named_in_plan"] += int(named)
            c["present"] += int(present)
            if not present:
                c["missing"].append(f"{host}:{i}")
        elif named:
            c["other_jobs_with_a_ledger_named"] += 1
            if not present:
                c["other_jobs_ledger_missing"].append(f"{host}:{i}")
print(json.dumps({**c, "pass": not c["missing"]}, sort_keys=True))
sys.exit(0 if not c["missing"] else 1)
