"""Budget guard for the family probes (administrative; reads the account, changes nothing).

The user's rule (5 Oct 2026): do the most possible with the current balance, and lose nothing if the funding runs out.
So a pod may be created only if, after counting every running pod of this account at its full remaining stop-timer
cap (a conservative upper bound; a pod without a known cap, or still running after its cap, counts for
CAP_FALLBACK_H hours), plus the new pod at its
full cap, the balance stays at or above RESERVE_USD. Stopped pods' storage is small and covered by the reserve.

    python3.11 budget.py                       print the projection
    python3.11 budget.py check HOURS PRICE     exit 0 if a new pod of HOURS at PRICE $/h is allowed, else 3

Review fix 12: a create-intent.json without a pod.json, in any kit, is a pod whose create may be in flight; it counts
at MAX_PRICE until its cap. launch.py and host.py extend-cap hold lock() (one shared lock file beside the kits) from
the check through the create or the extension, so two launches can never both pass on the same free balance.
"""
import contextlib, datetime as dt, fcntl, json, os, pathlib, sys, urllib.error, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
RESERVE_USD = 6.0
CAP_FALLBACK_H = 15.0              # the largest probe cap: a running pod with no known cap counts at 15 h
MAX_PRICE = 1.85                   # an intent without a pod counts at the kit's planning rate (probe_constants.MAX_PRICE)
LOCK_NAME = "family-probe-budget.lock"


@contextlib.contextmanager
def lock():
    """An exclusive lock shared by every family-probe kit beside this one (blocks until it is free)."""
    path = HERE.parent / LOCK_NAME
    with open(path, "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
KITS_GLOB = "family-probe-*"        # every working copy under tmp/ (and this kit), so no probe's pod is missed


def call(method, url, payload=None):
    key = os.environ.get("RUNPOD_OPERATOR_API_KEY", "").strip()
    if not key:
        raise SystemExit("RUNPOD_OPERATOR_API_KEY is not set (source the secrets file)")
    req = urllib.request.Request(url, method=method, data=None if payload is None else json.dumps(payload).encode(),
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                                          "Accept": "application/json", "User-Agent": "attribution-family-probe"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"null")


def kit_folders() -> list[pathlib.Path]:
    """This kit and every family-probe working copy beside it (tmp/family-probe-*)."""
    folders = {HERE.resolve()}
    folders.update(p.resolve() for p in HERE.parent.glob(KITS_GLOB) if p.is_dir())
    return sorted(folders)


def caps_by_pod_id() -> dict:
    """pod id -> the later of its recorded cap and its host's cap-override.json, over every kit."""
    out = {}
    for kit in kit_folders():
        for p in (kit / "hosts").glob("*/pod.json"):
            rec = json.loads(p.read_text())
            if not (rec.get("id") and rec.get("cap_stop_utc")):
                continue
            cap = rec["cap_stop_utc"]
            override = p.parent / "cap-override.json"
            if override.exists():
                later = json.loads(override.read_text()).get("stop_at_utc")
                if later and dt.datetime.fromisoformat(later.replace("Z", "+00:00")) > dt.datetime.fromisoformat(cap):
                    cap = later.replace("Z", "+00:00")
            out[rec["id"]] = cap
    return out


def pending_intents(now: dt.datetime) -> list[dict]:
    """create-intent.json files without a pod.json, over every kit: each at MAX_PRICE until its cap."""
    out = []
    for kit in kit_folders():
        for intent in (kit / "hosts").glob("*/create-intent.json"):
            if (intent.parent / "pod.json").exists():
                continue
            record = json.loads(intent.read_text())
            cap = record.get("cap_stop_utc")
            hours = (dt.datetime.fromisoformat(cap) - now).total_seconds() / 3600 if cap else CAP_FALLBACK_H
            hours = hours if hours > 0 else 0.0
            out.append({"name": f"intent:{kit.name}/{intent.parent.name}", "costPerHr": MAX_PRICE,
                        "hours_left_upper": round(hours, 2), "committed_usd": round(hours * MAX_PRICE, 2)})
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
    running += pending_intents(now)
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
