"""One-screen status of the 4 October run from local records (read-only; no pod is contacted).

    python3.11 status.py
"""
import json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
PLAN = json.loads((HERE.parents[1] / "tmp/study-v2-20261002/dev-matrix-assets/dev-matrix-plan.json").read_text())
rows, sealed_total, verified_total = [], 0, 0
for host in sorted(PLAN["assignments"]):
    folder, ret = HERE / "hosts" / host, HERE / "retrieved" / host
    pod = json.loads((folder / "pod.json").read_text()) if (folder / "pod.json").exists() else None
    last = (folder / "orchestrate.jsonl").read_text().splitlines()[-1] if (folder / "orchestrate.jsonl").exists() else ""
    stage = json.loads(last)["event"] if last else ("created" if pod else "not created")
    summary = json.loads((ret / "summary.json").read_text()) if (ret / "summary.json").exists() else {}
    sealed = len(summary.get("sealed_units", []))
    verified = len({json.loads(l)["unit"] for l in (ret / "verified.jsonl").read_text().splitlines() if json.loads(l).get("passed")}) \
        if (ret / "verified.jsonl").exists() else 0
    finished = json.loads((folder / "finished.json").read_text())["status"] if (folder / "finished.json").exists() else ""
    sealed_total += sealed; verified_total += verified
    rows.append(f"{host:6s} {('pod ' + pod['id']) if pod else '-':20s} {stage:18s} sealed {sealed}/6 verified {verified}/6 "
                f"{('cap ' + pod['cap_stop_utc'][11:16]) if pod else '':10s} {finished}")
print("\n".join(rows))
print(f"total sealed {sealed_total}/78, verified {verified_total}/78")
