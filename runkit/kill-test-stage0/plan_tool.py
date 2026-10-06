"""Write and update plan.json for kill-test Stage 0 (administrative).

    python3.11 plan_tool.py init                 the first host s0-1101 (a0, seed 1101, untuned baseline first), recipe unset
    python3.11 plan_tool.py set-recipe RECIPE    the recipe the first host's preflight chose (and its hash)
    python3.11 plan_tool.py add-hosts [JSON]     no argument: the job hosts s0-1102 and s0-1103 (cap 3.0 h); or JSON hosts

The engine identity comes from setup/setup-receipt.json and the prepared manifest from kt_constants. The recipe hash is
computed with the repository engine (identical to the packed one; pack_setup refuses uncommitted engine files).
"""
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kt_constants as kt  # noqa: E402

ROOT = HERE.parents[1]
PY = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"
PLAN = HERE / "plan.json"
JOB_HOSTS = {f"s0-{seed}": {"role": "job", "arm": "a0", "seed": seed, "prepared": kt.PREPARED_NAME, "base_eval": False,
                            "cap_hours": 3.0} for seed in (1102, 1103)}


def load():
    return json.loads(PLAN.read_text())


def save(p):
    PLAN.write_text(json.dumps(p, indent=1, sort_keys=True) + "\n")


def recipe_sha(path):
    return subprocess.run([str(PY), "-c", f"from experiments.safety_selection.config import load_recipe,config_sha256;print(config_sha256(load_recipe('{path}')))"],
                          cwd=ROOT, capture_output=True, text=True, check=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}).stdout.strip()


def initial_plan(receipt: dict) -> dict:
    return {"name": "kill-test-stage0", "design": "research/experiments/2026-10-06-kill-test-design-DRAFT.md",
            "brief": ".ai/briefs/kill-test-stage0-engine-20261006.md",
            "status": "development; Stage 0 step 1: untuned baseline and Dolly a0 seed 1101 (approved at about $5; $6 reserve)",
            "engine_sha256": receipt["engine_sha256"], "git_commit": receipt["git_commit"], "prepared": kt.prepared(),
            "first_host_recipes": kt.RECIPES, "recipe_path": None, "recipe_sha256": None,
            "preflight_prepared": kt.PREPARED_NAME, "checkpoints": ["e3"],
            "fixture_compare": {"equal_keys": ["source", "script_sha256", "manifest_sha256", "recipe_sha256", "training_identity", "test_rows"],
                                "resume_keys": ["direct", "loss_direct"]},
            "hosts": {"s0-1101": {"role": "first", "arm": "a0", "seed": 1101, "prepared": kt.PREPARED_NAME, "base_eval": True,
                                  "cap_hours": 4.0}}}


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "init":
        assert not PLAN.exists(), "plan.json exists"
        save(initial_plan(json.loads((HERE / "setup/setup-receipt.json").read_text())))
    elif cmd == "set-recipe":
        p = load(); r = sys.argv[2]; assert r in kt.RECIPES
        p["recipe_path"] = r; p["recipe_sha256"] = recipe_sha(r); save(p)
    elif cmd == "add-hosts":
        p = load(); new = json.loads(sys.argv[2]) if len(sys.argv) > 2 else JOB_HOSTS
        assert not set(new) & set(p["hosts"]), "host exists"
        p["hosts"].update(new); save(p)
    else:
        raise SystemExit("unknown command")
    print(json.dumps({"recipe": load().get("recipe_path"), "hosts": sorted(load()["hosts"])}))
