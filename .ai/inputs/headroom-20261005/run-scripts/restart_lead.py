"""Restart the stopped lead pod with a new stop-timer cap (administrative; headroom round 1).

    python3.11 restart_lead.py CAP_MINUTES

The durability README's procedure for using a stopped pod again: generate new pod-timer settings, replace the
pod's POD_TIMER_CAP_* values (the whole environment is re-sent, since the API does not say whether env merges),
then start it. The volume keeps the venv, the bundle and scores-001; the container disk (model cache) is lost.
Records: hosts/lead/restart-intent.json, restart-result.json, paused.json (the stopped interval, for costs).
The RunPod key is used only in the Authorization header.
"""
import datetime as dt, json, os, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import host  # noqa: E402

cap = int(sys.argv[1])
folder = HERE / "hosts" / "lead"
pod = json.loads((folder / "pod.json").read_text())
status, current = host.api("GET", f"/pods/{pod['id']}")
assert status == 200 and current.get("desiredStatus") == "EXITED", f"the lead pod is not stopped ({status}, {current.get('desiredStatus')})"
settings_path = folder / "timer-settings-restart.json"
assert not settings_path.exists(), "a restart was already prepared"
subprocess.run([str(ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"), "-m", "experiments.durability", "pod-timer-settings",
                "--state-dir", "/workspace/.pod-timer", "--cap-minutes", str(cap), "--out", str(settings_path)],
               cwd=ROOT, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, stdout=subprocess.DEVNULL)
settings = json.loads(settings_path.read_text())
env = {**settings["env"], "PUBLIC_KEY": (HERE / "ssh/key.pub").read_text().strip(),
       "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "TOKENIZERS_PARALLELISM": "false"}
now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
host.save(folder / "restart-intent.json", {"utc": now, "cap_minutes": cap, "cap_stop_utc": settings["cap_stop_utc"],
                                            "env_names": sorted(env), "stopped_since": current.get("lastStatusChange")})
s1, updated = host.api("PATCH", f"/pods/{pod['id']}", {"env": env, "dockerStartCmd": settings["docker_start_cmd"]})
s2, after = host.api("GET", f"/pods/{pod['id']}")
started = None
if s2 == 200 and after.get("desiredStatus") != "RUNNING":
    started = host.api("POST", f"/pods/{pod['id']}/start")[0]
s3, final = host.api("GET", f"/pods/{pod['id']}")
result = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "patch_status": s1,
          "status_after_patch": after.get("desiredStatus") if isinstance(after, dict) else None, "start_status": started,
          "status_now": final.get("desiredStatus") if isinstance(final, dict) else None, "cap_stop_utc": settings["cap_stop_utc"],
          "patch_error": updated.get("error") if isinstance(updated, dict) and "error" in updated else None}
host.save(folder / "restart-result.json", result)
host.save(folder / "paused.json", {"stopped_utc": "2026-10-05T09:23:19+00:00", "restarted_utc": result["utc"]})
pod["cap_stop_utc"] = settings["cap_stop_utc"]
host.save(folder / "pod.json", pod)
print(json.dumps(result, indent=1))
