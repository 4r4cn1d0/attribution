"""Write and update plan.json for one family probe (administrative).

    python3.11 plan_tool.py init                 one host <probe>-1101 (role first, a0, seed 1101, untuned baseline first)
    python3.11 plan_tool.py set-recipe RECIPE    the recipe the host's preflight chose (and its hash)

The probe is probe_constants.PROBE and the LoRA rank probe_constants.RANK ("r64" by default; "r16" for the 1B
probes' rank-16 ladders); its row in probes.py gives the recipe ladder, the prepared set, the cap, the
preflight wait and the disk sizes. The engine identity comes from setup/setup-receipt.json and the prepared manifest
from probe_constants. The recipe hash is computed with the repository engine (identical to the packed one; pack_setup
refuses uncommitted engine files). A probe has one seed and no job hosts.
"""
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe_constants as pc  # noqa: E402
import probes  # noqa: E402

ROOT = HERE.parents[1]
PY = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"
PLAN = HERE / "plan.json"
SEED = 1101


def load():
    return json.loads(PLAN.read_text())


def save(p):
    PLAN.write_text(json.dumps(p, indent=1, sort_keys=True) + "\n")


def recipe_sha(path):
    return subprocess.run([str(PY), "-c", f"from experiments.safety_selection.config import load_recipe,config_sha256;print(config_sha256(load_recipe('{path}')))"],
                          cwd=ROOT, capture_output=True, text=True, check=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}).stdout.strip()


def host_name(probe: str) -> str:
    return f"{probe}-{SEED}"


def first_host(probe: str) -> dict:
    spec = probes.PROBES[probe]
    return {"role": "first", "arm": "a0", "seed": SEED, "prepared": spec["prepared"], "base_eval": True,
            "cap_hours": spec["cap_hours"], "preflight_wait_s": spec["preflight_wait_s"],
            "container_disk_gb": spec["container_disk_gb"], "volume_gb": spec["volume_gb"]}


def initial_plan(receipt: dict, probe: str, prepared: dict, rank: str = "r64") -> dict:
    spec = probes.PROBES[probe]
    ladder = probes.recipes(probe, rank)
    return {"name": f"family-probe-{probe}" + ("" if rank == "r64" else f"-{rank}"), "probe": probe, "rank": rank,
            "brief": ".ai/briefs/multi-family-probe-engine-20261007.md",
            "status": f"development; one-seed probe {probe}: untuned baseline and Dolly a0 seed {SEED} to e1 (per-pod user approval)",
            "engine_sha256": receipt["engine_sha256"], "git_commit": receipt["git_commit"], "prepared": prepared,
            "first_host_recipes": ladder, "recipe_path": None, "recipe_sha256": None,
            "preflight_prepared": spec["prepared"], "checkpoints": [pc.CHECKPOINT],
            "fixture_compare": {"equal_keys": ["source", "script_sha256", "manifest_sha256", "recipe_sha256", "training_identity", "test_rows"],
                                "resume_keys": ["direct", "loss_direct"]},
            "hosts": {host_name(probe): first_host(probe)}}


def main(argv: list[str]) -> int:
    cmd = argv[0]
    if cmd == "init":
        assert not PLAN.exists(), "plan.json exists"
        save(initial_plan(json.loads((HERE / "setup/setup-receipt.json").read_text()), pc.probe(), pc.prepared(), pc.RANK))
    elif cmd == "set-recipe":
        p = load(); r = argv[1]; assert r in p["first_host_recipes"], "not a recipe of this probe's ladder"
        p["recipe_path"] = r; p["recipe_sha256"] = recipe_sha(r); save(p)
    else:
        raise SystemExit("unknown command")
    print(json.dumps({"recipe": load().get("recipe_path"), "hosts": sorted(load()["hosts"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
