"""Write and update plan.json for headroom v2 (administrative).

    python3.11 plan_tool.py init                 hosts of the first phase (first host and calibration), recipe unset
    python3.11 plan_tool.py set-recipe RECIPE    the recipe the first host's preflight chose (and its hash)
    python3.11 plan_tool.py add-hosts JSON       add later hosts, e.g. '{"lead": {...}, "a0-1102": {...}}'
    python3.11 plan_tool.py set-lead PREPARED    the lead's steps on PREPARED (row scores, removal files, rewrites, all edit files)
    python3.11 plan_tool.py set-edits            add each collected edit file's SHA-256 to its hosts

The engine identity and the prepared manifests come from setup/setup-receipt.json and pack_setup.EXPECTED. The recipe
hash is computed with the repository engine (identical to the packed one; pack_setup refuses uncommitted engine files).
"""
import hashlib, json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"
PLAN = HERE / "plan.json"
CFG = "experiments/safety_selection/configs"
RECIPES = [f"{CFG}/study-v3-headroom-pc2-20261005.json", f"{CFG}/study-v3-headroom-pc2-mb4-20261005.json",
           f"{CFG}/study-v3-headroom-pc2-eager-20261005.json"]
REWRITE = {"study-v3-headroom-pc2-20261005.json": f"{CFG}/headroom-rewrite-pc2-20261005.json",
           "study-v3-headroom-pc2-mb4-20261005.json": f"{CFG}/headroom-rewrite-pc2-20261005.json",
           "study-v3-headroom-pc2-eager-20261005.json": f"{CFG}/headroom-rewrite-pc2-eager-20261005.json"}
PREPARED = {"prepared-v3-inj05": "bd1e40df260c07773b387a0cb2af30321a194213149c241007dc7e027e34a76c",
            "prepared-v3-inj10": "3dee8d75488cd8098b21c4d97494d86135629e223ca8f811bea5c6579b394591"}


def load():
    return json.loads(PLAN.read_text())


def save(p):
    PLAN.write_text(json.dumps(p, indent=1, sort_keys=True) + "\n")


def recipe_sha(path):
    return subprocess.run([str(PY), "-c", f"from experiments.safety_selection.config import load_recipe,config_sha256;print(config_sha256(load_recipe('{path}')))"],
                          cwd=ROOT, capture_output=True, text=True, check=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}).stdout.strip()


cmd = sys.argv[1]
if cmd == "init":
    assert not PLAN.exists(), "plan.json exists"
    receipt = json.loads((HERE / "setup/setup-receipt.json").read_text())
    save({"name": "headroom-v2", "amendment": "research/experiments/2026-10-05-headroom-v2-amendment-draft.md",
          "status": "development; validation and calibration first (Part 7 run plan within the balance; $6 reserve)",
          "engine_sha256": receipt["engine_sha256"], "git_commit": receipt["git_commit"], "prepared": PREPARED,
          "first_host_recipes": RECIPES, "recipe_path": None, "recipe_sha256": None, "rewrite_config": None,
          "preflight_prepared": "prepared-v3-inj10", "checkpoints": ["e3"],
          "fixture_compare": {"equal_keys": ["source", "script_sha256", "manifest_sha256", "recipe_sha256", "training_identity", "test_rows"],
                              "resume_keys": ["direct", "loss_direct"]},
          "hosts": {"val05": {"role": "first", "arm": "a0", "seed": 1101, "prepared": "prepared-v3-inj05", "cap_hours": 3.5},
                    "cal10": {"role": "job", "arm": "a0", "seed": 1101, "prepared": "prepared-v3-inj10", "cap_hours": 3.0}}})
elif cmd == "set-recipe":
    p = load(); r = sys.argv[2]; assert r in RECIPES
    p["recipe_path"] = r; p["recipe_sha256"] = recipe_sha(r); p["rewrite_config"] = REWRITE[pathlib.Path(r).name]; save(p)
elif cmd == "add-hosts":
    p = load(); new = json.loads(sys.argv[2])
    assert not set(new) & set(p["hosts"]), "host exists"
    p["hosts"].update(new); save(p)
elif cmd == "set-lead":
    p = load(); prep = sys.argv[2]; assert prep in PREPARED and p["recipe_path"] and p["rewrite_config"]
    R = p["recipe_path"]
    p["lead_prepared"] = prep
    p["lead_steps"] = [
        {"receipt": "lead-process-1-scores", "args": ["score-rows", "--recipe", R, "--prepared", prep, "--out", "scores-001"]},
        {"receipt": "lead-process-2-edits-removal", "args": ["build-edits", "--prepared", prep, "--scores", "scores-001/scores.json",
                                                             "--count", "injection", "--out", "edits-remove-001"]},
        {"receipt": "lead-process-3-rewrites", "args": ["generate-rewrites", "--config", p["rewrite_config"], "--recipe", R, "--prepared", prep,
                                                        "--scores", "scores-001/scores.json", "--count", "injection", "--out", "rewrites-001"]},
        {"receipt": "lead-process-4-edits-all", "args": ["build-edits", "--prepared", prep, "--scores", "scores-001/scores.json",
                                                         "--rewrites", "rewrites-001/rewrites.json", "--count", "injection", "--out", "edits-all-001"]}]
    p["early_edits_dir"], p["final_edits_dir"] = "edits-remove-001", "edits-all-001"
    p["scores_file"], p["rewrites_file"] = "scores-001/scores.json", "rewrites-001/rewrites.json"
    k = 507 if prep.endswith("inj05") else 1015
    p["edit_files"] = [f"remove-k{k}.json", f"random-remove-k{k}.json", f"rewrite-k{k}.json", f"random-rewrite-k{k}.json"]
    save(p)
elif cmd == "set-edits":
    p = load()
    for h, job in p["hosts"].items():
        f = HERE / "edits" / job.get("edit", "")
        if job.get("edit") and f.is_file():
            job["edit_sha256"] = hashlib.sha256(f.read_bytes()).hexdigest()
    save(p)
else:
    raise SystemExit("unknown command")
print(json.dumps({"recipe": load().get("recipe_path"), "hosts": sorted(load()["hosts"])}))
