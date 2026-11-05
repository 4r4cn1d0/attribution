"""Extend (or shorten) a running pod's stop timer with an operator lease, without a restart.

From Specialized Implementation, 4 October 2026, tested by it against a real timer process. Run on the pod:
    python3 extend_cap.py SECONDS_FROM_NOW
The new stop time REPLACES the current one (seconds from now, not added to the cap); at most 48 h ahead.
It bypasses admission: check the balance first. Undo: create an empty /workspace/.pod-timer/voids/<lease>.json.
The printed line must say "governs": true and "acknowledged": true with the intended stop time.
"""
import datetime as dt, json, os, sys, time
d = os.environ.get("POD_TIMER_DIR", "/workspace/.pod-timer"); pod = json.load(open(d + "/heartbeat.json"))["pod"]
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0); stop = now + dt.timedelta(seconds=float(sys.argv[1]))
lease = now.strftime("%Y%m%dT%H%M%SZ") + "-" + os.urandom(8).hex(); ms = lambda t: t.isoformat(timespec="milliseconds")
rec = {"kind": "durability pod-timer lease v1", "lease": lease, "worker": "operator", "pod": pod,
       "stop_at_utc": ms(stop), "reserved_until_utc": ms(stop), "published_utc": ms(now)}
os.makedirs(d + "/leases", exist_ok=True); tmp = d + "/leases/." + lease + ".tmp"
open(tmp, "w").write(json.dumps(rec)); os.rename(tmp, d + "/leases/" + lease + ".json")
time.sleep(8); g = json.load(open(d + "/heartbeat.json"))["governing"]
print(json.dumps({"lease": lease, "governs": g["lease"] == lease, "acknowledged": os.path.exists(d + "/acks/" + lease + ".json"), "stop_at_utc": g["stop_at_utc"]}))
