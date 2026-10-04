"""Create the hosts that have no pod yet, one at a time, until all exist (administrative; 4 October run).

Before each try the previous failed attempt's files are archived (renamed, never deleted). A created host's
remaining steps (SSH, GPU and timer check, bootstrap, fixture, start) run detached via orchestrate.py after-create.
Tries are spaced; a round over all pending hosts repeats until none is pending or MAX_HOURS pass.
"""
import datetime as dt, json, pathlib, subprocess, sys, time
HERE = pathlib.Path(__file__).resolve().parent
HOSTS = ["lead", "dev01", "dev02", "dev04", "dev06", "dev07", "dev08", "dev10", "dev11", "dev12"]
SPACING, ROUND_PAUSE, MAX_HOURS = 60, 480, 6
def now(): return dt.datetime.now(dt.timezone.utc)
def log(**f): print(json.dumps({"utc": now().isoformat(timespec="seconds"), **f}), flush=True)
deadline = time.time() + MAX_HOURS * 3600
while time.time() < deadline:
    pending = [h for h in HOSTS if not (HERE / "hosts" / h / "pod.json").exists()]
    if not pending:
        log(event="all hosts created"); break
    for host in pending:
        folder = HERE / "hosts" / host
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
        time.sleep(SPACING)
    time.sleep(ROUND_PAUSE)
