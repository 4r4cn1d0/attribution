"""Create the given hosts one at a time, retrying until each exists (administrative; headroom round 1).

    python3.11 launch.py HOST [HOST ...]

Before each try the previous failed attempt's files are archived (renamed, never deleted). A created host's
remaining steps run detached via orchestrate.py after-create (log: hosts-full-HOST.log). Tries are spaced;
a round over the pending hosts repeats until none is pending or MAX_HOURS pass.
"""
import datetime as dt, json, pathlib, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent
HOSTS = sys.argv[1:]
SPACING, ROUND_PAUSE, MAX_HOURS = 45, 300, 2
plan = json.loads((HERE / "plan.json").read_text())
assert HOSTS and all(h in plan["hosts"] for h in HOSTS), "unknown host"


def now():
    return dt.datetime.now(dt.timezone.utc)


def log(**f):
    print(json.dumps({"utc": now().isoformat(timespec="seconds"), **f}), flush=True)


deadline = time.time() + MAX_HOURS * 3600
while time.time() < deadline:
    pending = [h for h in HOSTS if not (HERE / "hosts" / h / "pod.json").exists()]
    if not pending:
        log(event="all hosts created", hosts=HOSTS); break
    for host in pending:
        folder = HERE / "hosts" / host
        folder.mkdir(parents=True, exist_ok=True)
        stamp = now().strftime("%Y%m%dT%H%M%SZ")
        for name in ("create-intent.json", "create-result.json", "timer-settings.json"):
            if (folder / name).exists():
                (folder / name).rename(folder / f"{name[:-5]}-failed-{stamp}.json")
        result = subprocess.run([sys.executable, "host.py", "create", host], cwd=HERE, capture_output=True, text=True)
        if (folder / "pod.json").exists():
            log(host=host, event="created")
            with open(HERE / f"hosts-full-{host}.log", "a") as out:
                subprocess.Popen([sys.executable, "orchestrate.py", "after-create", host], cwd=HERE, stdout=out,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        else:
            err = (folder / "create-result.json").read_text()[:160] if (folder / "create-result.json").exists() else result.stderr[-160:]
            log(host=host, event="create-failed", detail=err.replace("\n", " "))
        if len(pending) > 1:
            time.sleep(SPACING)
    if [h for h in HOSTS if not (HERE / "hosts" / h / "pod.json").exists()]:
        time.sleep(ROUND_PAUSE)
