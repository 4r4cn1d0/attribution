"""Create the given hosts one at a time, retrying until each exists (administrative; family probes).

Every creation first passes the budget guard (budget.py): running pods at their full caps plus the new pod at its
full cap must leave at least the $6 reserve.

    python3.11 launch.py HOST [HOST ...]

For a gated probe (Llama-3), before anything else: the HF token must be in the environment variable
probe_constants.HF_TOKEN_ENV; GET whoami-v2 must succeed (a role other than read or fineGrained, or a non-read scope, is only a
token-scope-warning: the user waived the read-only precondition, FOCUS.md "Token decision", 2026-10-07); and every
file of the gated download plan must answer a Range request with 206. Only the role, scope names and status codes are
recorded (hosts/HOST/token-check.json), never the token. budget.py and host.py create get an environment without any
token variable; only the detached orchestrate.py child keeps it (it hands the token to host.py over stdin).

host.py create archives a failed attempt's files (renamed, never deleted) once the pod listing shows no pod of the
host's name, and stops an untracked pod of that name. A created host's remaining steps run detached, under
caffeinate -i so the Mac does not sleep while the pod bills, via orchestrate.py after-create (log:
hosts-full-HOST.log). Tries are spaced; a round over the pending hosts repeats until none is pending or MAX_HOURS
pass. Review fixes (8 October): one launch.py per kit at a time (launch.lock); the budget check and the create run
under the lock shared by every kit (budget.lock()); whoami-v2 is read whole and an unreadable reply only warns; when
the loop ends the token is removed from this process's environment.
"""
import datetime as dt, fcntl, json, os, pathlib, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import budget  # noqa: E402
import probe_constants as pc  # noqa: E402
import probes  # noqa: E402
import secret_scan  # noqa: E402

SPACING, ROUND_PAUSE, MAX_HOURS = 45, 300, 2
WHOAMI_LIMIT = 1 << 20                    # review fix 6: the whole whoami-v2 reply (a Range reply needs 1 byte)
READ_ROLES = ("read", "fineGrained")     # brief 5a; any other role, or a non-.read scope, only warns


def clean_env() -> dict:
    return secret_scan.scrubbed(os.environ, pc.TOKEN_ENV_NAMES)


class SameHostAuthRedirect(urllib.request.HTTPRedirectHandler):
    """Follow a redirect, but drop the Authorization header when it leaves the original host (a gated LFS file
    redirects to a signed CDN address that needs no token; urllib would otherwise send the token there too)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and urllib.parse.urlsplit(newurl).netloc != urllib.parse.urlsplit(req.full_url).netloc:
            for name in [k for k in new.headers if k.lower() == "authorization"]:
                del new.headers[name]
        return new


def http_get(url: str, token: str, headers: dict | None = None, limit: int = 1) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + token, **(headers or {})})
    opener = urllib.request.build_opener(SameHostAuthRedirect)
    try:
        with opener.open(request, timeout=60) as response:
            return response.status, response.read(limit)
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def _strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _strings(v)]
    return []


def token_checks(token: str, plan_entries: list[dict], get=http_get) -> dict:
    """Brief 5a with the user's waiver: whoami-v2 must answer; extra scopes only warn; every gated file must give 206."""
    status, body = get("https://huggingface.co/api/whoami-v2", token, None, WHOAMI_LIMIT)
    if status != 200:
        raise SystemExit(f"whoami-v2 answered {status}: the token is not valid")
    try:                                   # review fix 6: an unreadable reply is a role unknown, which only warns
        access = (json.loads(body or b"{}").get("auth") or {}).get("accessToken") or {}
        role = access.get("role")
        permissions = sorted({p for p in _strings(access.get("fineGrained") or {}) if "." in p and " " not in p})
    except (ValueError, AttributeError):
        role, permissions = "unknown (whoami-v2 reply unreadable)", []
    extra = [p for p in permissions if not p.endswith(".read")]
    record = {"role": role, "warnings": []}
    if role not in READ_ROLES or extra:
        record["warnings"].append({"event": "token-scope-warning", "role": role, "extra_scopes": extra})
    ranges = {}
    for entry in plan_entries:
        if not entry["gated"]:
            continue
        for name in entry["patterns"]:
            url = f"https://huggingface.co/{entry['repo_id']}/resolve/{entry['revision']}/{name}"
            ranges[f"{entry['repo_id']}/{name}"] = get(url, token, {"Range": "bytes=0-0"})[0]
    record["range_status"] = ranges
    bad = {k: v for k, v in ranges.items() if v != 206}
    if bad or not ranges:
        raise SystemExit(f"gated access check failed (status codes {bad or 'none'})")
    return record


def gated_precheck(host: str, env=None, get=http_get) -> dict | None:
    """For a gated probe: the token-variable, whoami and Range checks, before any pod exists."""
    entries = probes.download_plan(pc.probe())
    if not any(e["gated"] for e in entries):
        return None
    token = (env if env is not None else os.environ).get(pc.HF_TOKEN_ENV, "").strip()
    if not token:
        raise SystemExit(f"{pc.HF_TOKEN_ENV} is not set: a gated probe needs the HF token (source the secrets file)")
    record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), **token_checks(token, entries, get)}
    folder = HERE / "hosts" / host
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "token-check.json").write_text(json.dumps(record, indent=1) + "\n")
    for warning in record["warnings"]:
        print(json.dumps({"host": host, **warning}), flush=True)
    return record


def now():
    return dt.datetime.now(dt.timezone.utc)


def log(**f):
    print(json.dumps({"utc": now().isoformat(timespec="seconds"), **f}), flush=True)


def kit_lock():
    """One launch.py per kit at a time (review fix 19); refuses at once when another holds it."""
    handle = open(HERE / "launch.lock", "a")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        raise SystemExit("another launch.py is running in this kit")
    return handle


def main(hosts: list[str], run=subprocess.run, popen=subprocess.Popen, sleep=time.sleep) -> int:
    plan = json.loads((HERE / "plan.json").read_text())
    assert hosts and all(h in plan["hosts"] for h in hosts), "unknown host"
    held = kit_lock()
    try:
        for host in hosts:                   # a gated probe is checked before any pod exists, so none waits idle
            gated_precheck(host)
        _create_all(plan, hosts, run, popen, sleep)
    finally:
        secret_scan.scrub_process(os.environ, pc.TOKEN_ENV_NAMES)   # the disputed review item: no token after use
        held.close()
    return 0


def _create_all(plan: dict, hosts: list[str], run, popen, sleep) -> None:
    deadline = time.time() + MAX_HOURS * 3600
    while time.time() < deadline:
        pending = [h for h in hosts if not (HERE / "hosts" / h / "pod.json").exists()]
        if not pending:
            log(event="all hosts created", hosts=hosts)
            break
        for host in pending:
            folder = HERE / "hosts" / host
            folder.mkdir(parents=True, exist_ok=True)
            cap_hours = plan["hosts"][host]["cap_hours"]
            with budget.lock():              # review fix 12: no other kit's check until this pod.json is written
                checked = run([sys.executable, "host.py", "reconcile", host], cwd=HERE, capture_output=True, text=True,
                              env=clean_env())
                if checked.returncode != 0:
                    log(host=host, event="reconcile-failed", detail=(checked.stdout + checked.stderr)[-200:].replace("\n", " "))
                    continue
                guard = run([sys.executable, "budget.py", "check", str(cap_hours), str(pc.MAX_PRICE)], cwd=HERE,
                            capture_output=True, text=True, env=clean_env())
                if guard.returncode != 0:    # the reserve rule: never launch what could take the balance below the reserve
                    log(host=host, event="budget-guard-refused", detail=guard.stdout.strip()[-300:])
                    continue
                result = run([sys.executable, "host.py", "create", host], cwd=HERE, capture_output=True, text=True,
                             env=clean_env())
            if (folder / "pod.json").exists():
                log(host=host, event="created")
                with open(HERE / f"hosts-full-{host}.log", "a") as out:     # review fix 14: the Mac stays awake
                    popen(["caffeinate", "-i", sys.executable, "orchestrate.py", "after-create", host], cwd=HERE,
                          stdout=out, stderr=subprocess.STDOUT, start_new_session=True, env=dict(os.environ))
            else:
                err = (folder / "create-result.json").read_text()[:160] if (folder / "create-result.json").exists() \
                    else result.stderr[-160:]
                log(host=host, event="create-failed", detail=err.replace("\n", " "))
            if len(pending) > 1:
                sleep(SPACING)
        if [h for h in hosts if not (HERE / "hosts" / h / "pod.json").exists()]:
            sleep(ROUND_PAUSE)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
