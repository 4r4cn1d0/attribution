"""One-screen status of round 1 from local records (read-only; no pod is contacted).

    python3.11 status.py
"""
import datetime as dt, json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
plan = json.loads((HERE / "plan.json").read_text())
now = dt.datetime.now(dt.timezone.utc)
rows, cost = [], 0.0
for host, job in plan["hosts"].items():
    folder = HERE / "hosts" / host
    pod = json.loads((folder / "pod.json").read_text()) if (folder / "pod.json").exists() else None
    last = (folder / "orchestrate.jsonl").read_text().splitlines()[-1] if (folder / "orchestrate.jsonl").exists() else ""
    stage = json.loads(last)["event"] if last else ("created" if pod else "not created")
    fin = json.loads((folder / "finished.json").read_text()) if (folder / "finished.json").exists() else None
    if pod:
        start = dt.datetime.fromisoformat(pod["created_utc"])
        end = dt.datetime.fromisoformat(fin["utc"]) if fin else now
        hours = (end - start).total_seconds() / 3600
        cost += hours * (pod.get("costPerHr") or 0)
    else:
        hours = 0
    what = job.get("edit") or job.get("arm") or "setup"
    rows.append(f"{host:11s} {what:24s} {stage:26s} {hours:4.2f} h  {fin['status'] if fin else ''}")
print("\n".join(rows))
print(f"estimated pod cost so far: ${cost:.2f} of ${plan['budget_usd']} (running time x price; storage excluded)")
