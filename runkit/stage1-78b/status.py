"""One-screen status of the 7-8B kit from local records (read-only; no pod is contacted; the stage-1 kit's status.py
from runkit/family-probe/status.py, one line per host with its wave (= block), jobs and their statuses; K2 changed the
two kit names in the text only).

    python3.11 status.py
"""
import datetime as dt, json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
plan = json.loads((HERE / "plan.json").read_text())
now = dt.datetime.now(dt.timezone.utc)
rows, cost = [], 0.0
for host, h in plan["hosts"].items():
    folder = HERE / "hosts" / host
    pod = json.loads((folder / "pod.json").read_text()) if (folder / "pod.json").exists() else None
    last = (folder / "orchestrate.jsonl").read_text().splitlines()[-1] if (folder / "orchestrate.jsonl").exists() else ""
    stage = json.loads(last)["event"] if last else ("created" if pod else "not created")
    fin = json.loads((folder / "finished.json").read_text()) if (folder / "finished.json").exists() else None
    hours = 0.0
    if pod:
        start = dt.datetime.fromisoformat(pod["created_utc"])
        end = dt.datetime.fromisoformat(fin["utc"]) if fin else now
        hours = (end - start).total_seconds() / 3600
        cost += hours * (pod.get("costPerHr") or 0)
    jobs = ",".join(f"{j['kind']}:{j.get('status')}" for j in h["jobs"])
    rows.append(f"{host:9s} wave {h['wave']:6s} cap {h['cap_hours']:5.2f} h  {stage:24s} {hours:4.2f} h  {jobs}  "
                f"{fin['status'] if fin else ''}")
print("\n".join(rows))
print(f"estimated pod cost so far (this 7-8B kit): ${cost:.2f}; reserve rule: python3.11 budget.py")
