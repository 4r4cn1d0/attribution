"""Delete the stopped pilot pod p-1 (the user, 2 Nov: "Yes, delete p-1" to "Delete the stopped pilot pod p-1 now that
it is backed up?"), after backup-2026-11-02-stage1b-pilot verified. Adapted from delete_two.py (1 Nov): only the pod
list and the backup name differ. Ids and names come from the kit's own pod.json records. GET (EXITED, name
equal) -> DELETE -> GET (404); one JSON line per pod to each OUT. Never touches another pod; prints the pods left
afterwards (name, status, volume).

    PY -B delete_p1.py KIT JH OUT [OUT ...] [--dry]
"""
import datetime as dt
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

H = {"Authorization": "Bearer " + os.environ["RUNPOD_OPERATOR_API_KEY"], "User-Agent": "stage1-kit"}
BACKUP = "backup-2026-11-02-stage1b-pilot"


def call(method, path):
    req = urllib.request.Request("https://rest.runpod.io/v1" + path, method=method, headers=H)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            return r.status, (json.loads(body) if body.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, None


args = [a for a in sys.argv[1:] if a != "--dry"]
dry = "--dry" in sys.argv
kit, jh = pathlib.Path(args[0]), pathlib.Path(args[1])
outs = [open(p, "a") for p in args[2:]] if not dry else []
records = [kit / "hosts" / "p-1" / "pod.json"]
for path in records:
    pod = json.loads(path.read_text())
    pid, name = pod["id"], pod["name"]
    rec = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "action": "delete", "name": name,
           "backup": BACKUP, "pod_id": pid}
    st, before = call("GET", f"/pods/{pid}")
    rec.update(get_before_http_status=st, status_before=(before or {}).get("desiredStatus"),
               volume_gb=(before or {}).get("volumeInGb"), name_before=(before or {}).get("name"))
    if st != 200 or (before or {}).get("desiredStatus") != "EXITED" or (before or {}).get("name") != name:
        rec.update(result="skipped", why="not EXITED or name differs")
    elif dry:
        rec.update(result="dry-ok")
    else:
        st, _ = call("DELETE", f"/pods/{pid}")
        rec["delete_http_status"] = st
        time.sleep(1)
        rec["get_after_http_status"] = call("GET", f"/pods/{pid}")[0]
        rec["result"] = "deleted" if st in (200, 204) and rec["get_after_http_status"] == 404 else "check"
    print(json.dumps(rec))
    for out in outs:
        out.write(json.dumps(rec) + "\n")
        out.flush()
st, left = call("GET", "/pods")
print("pods left", st, json.dumps(sorted((p.get("name"), p.get("desiredStatus"), p.get("volumeInGb")) for p in left or [])))
