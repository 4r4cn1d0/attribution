"""Budget guard for kill-test Stage 0 (administrative; reads the account, changes nothing).

The user's rule (5 Oct 2026): do the most possible with the current balance, and lose nothing if the funding runs out.
So a pod may be created only if, after counting every running pod of this account at its full remaining stop-timer
cap (a conservative upper bound; a pod without a known cap, or still running after its cap, counts for
CAP_FALLBACK_H hours), plus the new pod at its
full cap, the balance stays at or above RESERVE_USD. Stopped pods' storage is small and covered by the reserve.

    python3.11 budget.py                       print the projection
    python3.11 budget.py check HOURS PRICE     exit 0 if a new pod of HOURS at PRICE $/h is allowed, else 3
"""
import datetime as dt, json, os, pathlib, sys, urllib.error, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
RESERVE_USD = 6.0
CAP_FALLBACK_H = 6.0


def call(method, url, payload=None):
    key = os.environ.get("RUNPOD_OPERATOR_API_KEY", "").strip()
    if not key:
        raise SystemExit("RUNPOD_OPERATOR_API_KEY is not set (source the secrets file)")
    req = urllib.request.Request(url, method=method, data=None if payload is None else json.dumps(payload).encode(),
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                                          "Accept": "application/json", "User-Agent": "attribution-killtest-stage0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"null")


def caps_by_pod_id() -> dict:
    out = {}
    for p in (HERE / "hosts").glob("*/pod.json"):
        rec = json.loads(p.read_text())
        if rec.get("id") and rec.get("cap_stop_utc"):
            out[rec["id"]] = rec["cap_stop_utc"]
    return out


def hours_left(cap: str | None, now: dt.datetime) -> float:
    """Upper bound of a RUNNING pod's remaining hours: until its recorded cap, or CAP_FALLBACK_H when no cap is
    recorded OR the recorded cap has passed (a pod still running after its cap means its stop timer failed)."""
    if not cap:
        return CAP_FALLBACK_H
    hours = (dt.datetime.fromisoformat(cap) - now).total_seconds() / 3600
    return hours if hours > 0 else CAP_FALLBACK_H


def projection() -> dict:
    me = call("POST", "https://api.runpod.io/graphql", {"query": "query { myself { clientBalance currentSpendPerHr } }"})["data"]["myself"]
    pods = call("GET", "https://rest.runpod.io/v1/pods") or []
    now = dt.datetime.now(dt.timezone.utc); caps = caps_by_pod_id(); running = []
    for p in pods:
        if p.get("desiredStatus") != "RUNNING":
            continue
        hours = hours_left(caps.get(p.get("id")), now)
        running.append({"name": p.get("name"), "costPerHr": p.get("costPerHr") or 0.0, "hours_left_upper": round(hours, 2),
                        "committed_usd": round(hours * (p.get("costPerHr") or 0.0), 2)})
    committed = sum(r["committed_usd"] for r in running)
    return {"utc": now.isoformat(timespec="seconds"), "balance": round(me["clientBalance"], 2), "spend_per_hr": me["currentSpendPerHr"],
            "running": running, "committed_upper_usd": round(committed, 2),
            "free_after_commitments_usd": round(me["clientBalance"] - committed, 2), "reserve_usd": RESERVE_USD}


def main() -> int:
    proj = projection()
    if len(sys.argv) >= 4 and sys.argv[1] == "check":
        hours, price = float(sys.argv[2]), float(sys.argv[3])
        need = hours * price
        ok = proj["free_after_commitments_usd"] - need >= RESERVE_USD
        proj.update(new_pod_upper_usd=round(need, 2), allowed=ok)
        with open(HERE / "budget-checks.jsonl", "a") as f:
            f.write(json.dumps(proj) + "\n")
        print(json.dumps({k: proj[k] for k in ("balance", "committed_upper_usd", "new_pod_upper_usd", "reserve_usd", "allowed")}))
        return 0 if ok else 3
    print(json.dumps(proj, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
