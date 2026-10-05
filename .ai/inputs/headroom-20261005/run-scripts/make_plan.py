"""Write plan.json for round 1 of the headroom positive control (administrative).

    python3.11 make_plan.py --steps lead-steps.json [--edits]

Reads setup/setup-receipt.json (engine identity, recipe path) and computes the recipe hash with the packed
engine (mirror/). --edits adds, for every edit host, the SHA-256 of its collected edit file in edits/.
Refuses to overwrite a plan that a host has already been sent unless the only change is the edit hashes.
"""
import argparse, hashlib, json, os, pathlib, subprocess

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"
HOSTS = {
    "lead": {"role": "lead", "cap_hours": 2.5},
    "a0-1101": {"role": "job", "arm": "a0", "seed": 1101, "cap_hours": 3.5},
    "a0-1102": {"role": "job", "arm": "a0", "seed": 1102, "cap_hours": 3.5},
    "rm10-1101": {"role": "job", "edit": "remove-10.json", "seed": 1101, "cap_hours": 3.5},
    "rm10-1102": {"role": "job", "edit": "remove-10.json", "seed": 1102, "cap_hours": 3.5},
    "rrm10-1101": {"role": "job", "edit": "random-remove-10.json", "seed": 1101, "cap_hours": 3.5},
    "rrm10-1102": {"role": "job", "edit": "random-remove-10.json", "seed": 1102, "cap_hours": 3.5},
    "rw10-1101": {"role": "job", "edit": "rewrite-10.json", "seed": 1101, "cap_hours": 3.5},
    "rw10-1102": {"role": "job", "edit": "rewrite-10.json", "seed": 1102, "cap_hours": 3.5},
    "rrw10-1101": {"role": "job", "edit": "random-rewrite-10.json", "seed": 1101, "cap_hours": 3.5},
    "rrw10-1102": {"role": "job", "edit": "random-rewrite-10.json", "seed": 1102, "cap_hours": 3.5},
}

ap = argparse.ArgumentParser(); ap.add_argument("--steps", required=True); ap.add_argument("--edits", action="store_true")
a = ap.parse_args()
receipt = json.loads((HERE / "setup/setup-receipt.json").read_text())
steps = json.loads(pathlib.Path(a.steps).read_text())
recipe_sha = subprocess.run([str(PY), "-c", "import sys;from experiments.safety_selection.config import load_recipe,config_sha256;"
                                            f"print(config_sha256(load_recipe('{receipt['recipe_path']}')))"],
                            cwd=HERE / "mirror", capture_output=True, text=True, check=True,
                            env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(HERE / "mirror"), "PATH": "/usr/bin:/bin"}).stdout.strip()
hosts = json.loads(json.dumps(HOSTS))
if a.edits:      # only the edit files collected so far (removal files arrive before the rewrite files)
    for name, job in hosts.items():
        if job.get("edit") and (HERE / "edits" / job["edit"]).exists():
            job["edit_sha256"] = hashlib.sha256((HERE / "edits" / job["edit"]).read_bytes()).hexdigest()
plan = {"name": "headroom-positive-control-round1", "amendment_commit": "4c4c75b",
        "status": "development positive control; frozen reading in research/experiments/2026-10-05-headroom-amendment-draft.md",
        "engine_sha256": receipt["engine_sha256"], "git_commit": receipt["git_commit"],
        "recipe_path": receipt["recipe_path"], "recipe_sha256": recipe_sha,
        "prepared_path": "prepared-v2", "manifest_sha256": "5f4e118a39e0b8c3e56764db43c2581dc3d53cd63445f6d86b4b856609ee72e2",
        "checkpoints": ["e3"], "budget_usd": 35, "hosts": hosts, **steps}
out = HERE / "plan.json"
if out.exists():
    old = json.loads(out.read_text())
    for name, job in old["hosts"].items():
        job.pop("edit_sha256", None)
    new = json.loads(json.dumps(plan))
    for name, job in new["hosts"].items():
        job.pop("edit_sha256", None)
    if old != new:
        raise SystemExit("plan.json exists and differs in more than the edit hashes; refusing to overwrite")
out.write_text(json.dumps(plan, indent=1, sort_keys=True) + "\n")
print(json.dumps({"engine_sha256": plan["engine_sha256"], "recipe_sha256": recipe_sha, "edits": a.edits,
                  "plan_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}, indent=1))
