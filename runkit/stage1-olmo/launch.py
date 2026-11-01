"""Create the given Gate B hosts one at a time, retrying until each exists (administrative; from
runkit/family-probe/launch.py without the gated-token checks: OLMo-2-1B and Qwen3Guard are open repositories).

    python3.11 launch.py HOST [HOST ...]

Refuses a host that is not in plan.json, that has no jobs, whose base_eval is not false, or whose plan cap differs
from the cap gateb_rules computes from its jobs (B4). Every creation first passes the budget guard (budget.py check
at the host's cap and gateb_rules.PLANNING_PRICE_USD [D20]: running pods at their full caps plus the new pod at its full cap must leave
at least the $6 reserve), under the lock shared by every kit; host.py reconcile runs first. A created host's
remaining steps run detached under caffeinate -i via orchestrate.py after-create (log: hosts-full-HOST.log). Tries
are spaced; a round over the pending hosts repeats until none is pending or MAX_HOURS pass. One launch.py per kit at
a time (launch.lock). Every child gets an environment without any token variable.

Round 31 (K6; cert runbook D7): the exit code says whether every host was created. launch.py exits NO_POD_EXIT (4),
after its log line "hosts-not-created", when a host it was given has no hosts/HOST/pod.json at its end (every try was
refused or failed for MAX_HOURS); 0 only when every host has its pod.json. Nothing else changed.
"""
import datetime as dt, fcntl, json, os, pathlib, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import budget  # noqa: E402
import stage1_rules as rules  # noqa: E402
import secret_scan  # noqa: E402

SPACING, ROUND_PAUSE, MAX_HOURS = 45, 300, 2
NO_POD_EXIT = 4                     # round 31 (K6): a host it should create has no pod.json at the end


def clean_env() -> dict:
    return secret_scan.scrubbed(os.environ, rules.TOKEN_ENV_NAMES)


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
        _create_all(plan, hosts, run, popen, sleep)
    finally:
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
                          stdout=out, stderr=subprocess.STDOUT, start_new_session=True, env=clean_env())
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
