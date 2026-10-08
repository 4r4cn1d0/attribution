"""Read-only account check: balance, spend rate and pods (administrative; changes nothing).

    python3.11 account.py

Uses RUNPOD_OPERATOR_API_KEY (the user's secrets file) only in the Authorization header. Writes
account-latest.json (no secrets) and prints a short summary.
"""
import datetime as dt, json, os, pathlib, urllib.error, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
KEY = os.environ.get("RUNPOD_OPERATOR_API_KEY", "").strip()
if not KEY:
    raise SystemExit("RUNPOD_OPERATOR_API_KEY is not set (source the secrets file)")


def call(method, url, payload=None):
    req = urllib.request.Request(url, method=method, data=None if payload is None else json.dumps(payload).encode(),
                                 headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json",
                                          "Accept": "application/json", "User-Agent": "attribution-killtest-stage0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read().decode("utf-8", "replace")[:300]}


s1, me = call("POST", "https://api.runpod.io/graphql", {"query": "query { myself { clientBalance currentSpendPerHr spendLimit } }"})
s2, pods = call("GET", "https://rest.runpod.io/v1/pods")
rows = [{"name": p.get("name"), "status": p.get("desiredStatus"), "costPerHr": p.get("costPerHr"),
         "volumeInGb": p.get("volumeInGb")} for p in (pods if isinstance(pods, list) else [])]
record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "graphql_status": s1,
          "myself": (me or {}).get("data", {}).get("myself") if isinstance(me, dict) else None, "pods_status": s2, "pods": rows}
(HERE / "account-latest.json").write_text(json.dumps(record, indent=1) + "\n")
running = [r for r in rows if r["status"] == "RUNNING"]
print(json.dumps({"myself": record["myself"], "pods": len(rows), "running": [(r["name"], r["costPerHr"]) for r in running]}, indent=1))
