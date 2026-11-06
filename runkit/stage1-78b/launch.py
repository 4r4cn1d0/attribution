"""Create the given 7-8B hosts one at a time, retrying until each exists (administrative; the stage-1 kit's launch.py
with the gated-token checks of runkit/family-probe/launch.py:8-21 ported back for Llama-3.1-8B; K3 of T4 step 2).

    python3.11 launch.py HOST [HOST ...]

Refuses a host that is not in plan.json, a plan.json of another family (KD7), a host with no jobs, whose base_eval is
not false, or whose plan cap differs from the cap rules_78b computes from its jobs. Every creation first passes the
budget guard (budget.py check at the host's cap and stage1_rules.PLANNING_PRICE_USD: running pods at their full caps
plus the new pod at its full cap must leave at least the $6 reserve; the user's recorded guard-off decision goes past
its refusal only, the balance is still read and logged), under the lock shared by every kit; host.py reconcile runs
first. A created host's remaining steps run detached under caffeinate -i via orchestrate.py after-create (log:
hosts-full-HOST.log). Tries are spaced; a round over the pending hosts repeats until none is pending or MAX_HOURS pass.
One launch.py per kit at a time (launch.lock).

The gated path (the family whose download plan holds a gated repository: llama31-8b; olmo2-7b's repositories are
open and never touch it). Before any pod exists, for every host given: the HF token must be in the environment
variable HF_TOKEN_ENV (the user puts it there at each Llama launch: rulings C13), holding visible ASCII only (a value
with a space, a line break, a control or a non-ASCII character refuses before any request: fix-K-gated F1; a request
that gets no reply refuses with a line, never a traceback: verify-K-gated D4); GET whoami-v2 must answer 200 (a
role other than read or fineGrained, a non-.read scope, or a reply that cannot be read is only a token-scope-warning:
the user waived the read-only precondition, research/FOCUS.md "Token decision", 2026-10-07 19:14 UTC, as in the
family-probe kit); and every file of the gated download plan must answer a Range request with 206. Only the role, the
scope names and the status codes are recorded (hosts/HOST/token-check.json), never the token. budget.py, host.py
reconcile and host.py create get an environment without any token variable (and without any variable whose value
looks like an HF token); only the detached orchestrate.py child keeps the environment, and it hands the token to
host.py gated-download over stdin (never an argument, a file or a log). When the loop ends the token is removed from
this process's environment (secret_scan.scrub_process), whatever the family.

Round 31 (K6; cert runbook D7): the exit code says whether every host was created. launch.py exits NO_POD_EXIT (4),
after its log line "hosts-not-created", when a host it was given has no hosts/HOST/pod.json at its end (every try was
refused or failed for MAX_HOURS); 0 only when every host has its pod.json.
"""
import datetime as dt, fcntl, http.client, json, os, pathlib, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import budget  # noqa: E402
import probes  # noqa: E402
import stage1_rules as rules  # noqa: E402
import secret_scan  # noqa: E402

SPACING, ROUND_PAUSE, MAX_HOURS = 45, 300, 2
NO_POD_EXIT = 4                     # round 31 (K6): a host it should create has no pod.json at the end
HF_TOKEN_ENV = rules.TOKEN_ENV_NAMES[0]   # "HF_TOKEN": the one variable the token is read from (Mac side only)
WHOAMI_LIMIT = 1 << 20              # the whole whoami-v2 reply (a Range reply needs 1 byte)
READ_ROLES = ("read", "fineGrained")  # any other role, or a non-.read scope, only warns (the user's waiver)
HUB = "https://huggingface.co"
NO_REPLY = 0                        # http_get's status when no reply came (DNS, connection, timeout, TLS, a broken reply)
HTTP_TIMEOUT_S = 60


def clean_env() -> dict:
    return secret_scan.scrubbed(os.environ, rules.TOKEN_ENV_NAMES)


def same_origin(url: str, other: str) -> bool:
    """The same scheme and host (netloc, case-insensitive). A redirect to another host, or from https to http on the
    same host (verify-K-gated D5), is not the same origin, and the Authorization header must not follow it."""
    a, b = urllib.parse.urlsplit(url), urllib.parse.urlsplit(other)
    return (a.scheme.lower(), a.netloc.lower()) == (b.scheme.lower(), b.netloc.lower())


class SameHostAuthRedirect(urllib.request.HTTPRedirectHandler):
    """Follow a redirect, but drop the Authorization header when it leaves the original origin (scheme and host): a
    gated LFS file redirects to a signed CDN address that needs no token (urllib would otherwise send the token there
    too), and a downgrade from https to http on the same host would send it in the clear (D5)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and not same_origin(req.full_url, newurl):
            for name in [k for k in new.headers if k.lower() == "authorization"]:
                del new.headers[name]
        return new


def failure_text(exc: BaseException, token: str) -> str:
    """'<class>: <reason>' for a request that got no reply, at most 200 characters, with the token's exact value and
    anything of the HF token's shape replaced by '<token>' (the text goes into a refusal line and launch-0.log; D4)."""
    reason = getattr(exc, "reason", None)
    text = f"{type(exc).__name__}: {reason if reason is not None else exc}"
    if token:
        text = text.replace(token, "<token>")
    text = secret_scan.PATTERNS["hf_token"].sub("<token>", text)
    return text[:200]


def http_get(url: str, token: str, headers: dict | None = None, limit: int = 1) -> tuple[int, bytes]:
    """(status, the first ``limit`` bytes); an HTTP error is its status with no body; a failure before any reply (DNS,
    a refused or reset connection, a timeout, a TLS or certificate failure, a broken reply) is NO_REPLY (0) with a
    short description of the failure that never holds the token (failure_text; D4), so the caller refuses cleanly
    instead of a traceback. The token goes into the Authorization header of this request only (SameHostAuthRedirect;
    the opener is built here, at the call, with that one handler: D1)."""
    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + token, **(headers or {})})
    opener = urllib.request.build_opener(SameHostAuthRedirect)
    try:
        with opener.open(request, timeout=HTTP_TIMEOUT_S) as response:
            return response.status, response.read(limit)
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        return NO_REPLY, failure_text(exc, token).encode()
    except ValueError as exc:              # the request could not be built (http.client's header check quotes the whole
        return NO_REPLY, f"{type(exc).__name__}: the request could not be built (detail withheld)".encode()  # header)


def header_safe(token: str) -> bool:
    """True when every character of the token is visible ASCII (0x21-0x7E), the only characters an HTTP Bearer value
    can carry. http.client refuses anything else with a ValueError whose message quotes the whole header, the token
    included (fix-K-gated F1), so such a value must refuse before any request is built."""
    return bool(token) and all("\x21" <= ch <= "\x7e" for ch in token)


def _strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _strings(v)]
    return []


def token_checks(token: str, plan_entries: list[dict], get=None) -> dict:
    """whoami-v2 must answer 200 (else SystemExit); the role and the fine-grained scope names are recorded, and a role
    outside READ_ROLES, a non-.read scope or a reply that cannot be read (not JSON, or not the user shape) is a
    token-scope-warning only (the user's waiver); then every gated file must answer a Range request with 206 (else
    SystemExit with the status codes). The record never holds the token. ``get`` is http_get (the one network boundary;
    a test's fake) and is resolved at the call."""
    get = http_get if get is None else get
    if not header_safe(token):             # F1: before any request; the message names no part of the value
        raise SystemExit(f"{HF_TOKEN_ENV} holds a character a request header cannot carry (a space, a line break, a "
                         "control or a non-ASCII character): no request was sent and no pod was created; put the "
                         "token's exact value in the variable and launch again")
    status, body = get(f"{HUB}/api/whoami-v2", token, None, WHOAMI_LIMIT)
    if status == NO_REPLY:                 # D4: the network or TLS failed before any answer; a refusal, not a traceback
        raise SystemExit(f"whoami-v2 got no reply ({body.decode('utf-8', 'replace') or 'no detail'}): the network or "
                         "TLS failed before any answer; no pod was created; check the connection and launch again")
    if status != 200:
        raise SystemExit(f"whoami-v2 answered {status}: the token is not valid")
    try:                                   # an unreadable reply or another shape is a role unknown, which only warns
        access = (json.loads(body or b"{}").get("auth") or {}).get("accessToken") or {}
        role = access.get("role")
        permissions = sorted({p for p in _strings(access.get("fineGrained") or {}) if "." in p and " " not in p})
    except (ValueError, AttributeError, TypeError):
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
            url = f"{HUB}/{entry['repo_id']}/resolve/{entry['revision']}/{name}"
            status, detail = get(url, token, {"Range": "bytes=0-0"})
            if status == NO_REPLY:         # D4: stop at the first request that got no reply; no further request
                raise SystemExit(f"the Range request for {entry['repo_id']}/{name} got no reply "
                                 f"({detail.decode('utf-8', 'replace') or 'no detail'}): the network or TLS failed; "
                                 "no pod was created; check the connection and launch again")
            ranges[f"{entry['repo_id']}/{name}"] = status
    record["range_status"] = ranges
    bad = {k: v for k, v in ranges.items() if v != 206}
    if bad or not ranges:
        raise SystemExit(f"gated access check failed (status codes {bad or 'none'})")
    return record


def gated_entries() -> list[dict]:
    """The gated repositories of this working copy's family's download plan (llama31-8b: the policy's exact files;
    olmo2-7b: none). Refuses outside a KD7 working copy (stage1_rules.family_or_refuse)."""
    try:
        rules.family_or_refuse()
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    return [e for e in probes.stage1_download_plan(rules.PROBE_KEY) if e["gated"]]


def gated_precheck(host: str, env=None, get=None) -> dict | None:
    """For a gated family: the token-variable, whoami and Range checks, before any pod exists (so none waits idle).
    None for an open family: the token is not read. Writes hosts/HOST/token-check.json (no token in it)."""
    entries = gated_entries()
    if not entries:
        return None
    token = (env if env is not None else os.environ).get(HF_TOKEN_ENV, "").strip()
    if not token:
        raise SystemExit(f"{HF_TOKEN_ENV} is not set: a gated family ({rules.FAMILY}) needs the HF token in the Mac "
                         "environment at each launch (source the secrets file; rulings C13)")
    record = {"utc": now().isoformat(timespec="seconds"), "family": rules.FAMILY, "host": host,
              **token_checks(token, entries, get)}
    folder = HERE / "hosts" / host
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "token-check.json").write_text(json.dumps(record, indent=1) + "\n")
    for warning in record["warnings"]:
        print(json.dumps({"host": host, **warning}), flush=True)
    return record


def child_env() -> dict:
    """The detached orchestrate.py child's environment: this process's whole environment for a gated family (it hands
    the token to host.py gated-download over stdin), the scrubbed one for an open family."""
    return dict(os.environ) if gated_entries() else clean_env()


def now():
    return dt.datetime.now(dt.timezone.utc)


def log(**f):
    print(json.dumps({"utc": now().isoformat(timespec="seconds"), **f}), flush=True)


def kit_lock():
    handle = open(HERE / "launch.lock", "a")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        raise SystemExit("another launch.py is running in this kit")
    return handle


def check_hosts(plan: dict, hosts: list[str]) -> None:
    try:
        family = rules.family_or_refuse()
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    if plan.get("family") != family or plan.get("kit_block") != rules.KIT_BLOCK:
        raise SystemExit(f"plan.json is not this working copy's ({family} block {rules.KIT_BLOCK}; KD7)")
    for host in hosts:
        h = plan["hosts"].get(host)
        if h is None:
            raise SystemExit(f"{host} is not a host of plan.json")
        if h.get("base_eval") is not False:
            raise SystemExit(f"{host}: base_eval must be false")
        if not h.get("jobs"):
            raise SystemExit(f"{host}: no jobs")
        if h["cap_hours"] != rules.cap_hours(h["jobs"]):
            raise SystemExit(f"{host}: the plan's cap differs from the cap of its jobs")


def main(hosts: list[str], run=subprocess.run, popen=subprocess.Popen, sleep=time.sleep) -> int:
    plan = json.loads((HERE / "plan.json").read_text())
    if not hosts:
        raise SystemExit("give at least one host")
    check_hosts(plan, hosts)
    held = kit_lock()
    try:
        for host in hosts:               # a gated family is checked before any pod exists, so none waits idle
            gated_precheck(host)
        _create_all(plan, hosts, run, popen, sleep)
    finally:
        secret_scan.scrub_process(os.environ, rules.TOKEN_ENV_NAMES)   # no token in this process after the loop
        held.close()
    missing = [h for h in hosts if not (HERE / "hosts" / h / "pod.json").exists()]
    if missing:                      # round 31 (K6): no pod for a host it should create is not a success
        log(event="hosts-not-created", hosts=missing, exit=NO_POD_EXIT)
        return NO_POD_EXIT
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
            with budget.lock():
                checked = run([sys.executable, "host.py", "reconcile", host], cwd=HERE, capture_output=True, text=True,
                              env=clean_env())
                if checked.returncode != 0:
                    log(host=host, event="reconcile-failed", detail=(checked.stdout + checked.stderr)[-200:].replace("\n", " "))
                    continue
                guard = run([sys.executable, "budget.py", "check", str(cap_hours), str(rules.PLANNING_PRICE_USD)], cwd=HERE,
                            capture_output=True, text=True, env=clean_env())
                off = rules.guard_off_record(HERE)   # (E) the user's recorded decision: past the guard's refusal only
                if guard.returncode != 0 and not (off and guard.returncode == rules.GUARD_REFUSED_EXIT):
                    log(host=host, event="budget-guard-refused", detail=guard.stdout.strip()[-300:])
                    continue
                if off:                               # the live balance was read; its line is logged with the decision
                    log(host=host, event="budget-guard-off", guard_exit=guard.returncode, decision_sha256=off["sha256"],
                        detail=guard.stdout.strip()[-300:])
                result = run([sys.executable, "host.py", "create", host], cwd=HERE, capture_output=True, text=True,
                             env=clean_env())
            if (folder / "pod.json").exists():
                log(host=host, event="created")
                with open(HERE / f"hosts-full-{host}.log", "a") as out:
                    popen(["caffeinate", "-i", sys.executable, "orchestrate.py", "after-create", host], cwd=HERE,
                          stdout=out, stderr=subprocess.STDOUT, start_new_session=True, env=child_env())
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
