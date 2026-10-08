"""Write and update plan.json for one family probe (administrative).

    python3.11 plan_tool.py init                 one host <probe>-1101 (role first, a0, seed 1101, untuned baseline first)
    python3.11 plan_tool.py init --reuse-baseline UNIT
                                                 fine-tune only (base_eval false): the reading pairs e1 with the sealed
                                                 untuned unit UNIT of an earlier run of this probe (GI III round 5)
    python3.11 plan_tool.py set-recipe RECIPE    the recipe the host's preflight chose (and its hash)

The probe is probe_constants.PROBE, the LoRA rank probe_constants.RANK ("r64" by default; "r16" for the 1B
probes' rank-16 ladders) and the recipe kind probe_constants.RECIPE ("b" by default; "bt" or "g" for the 1B probes); its row in probes.py gives the recipe ladder, the prepared set, the cap, the
preflight wait and the disk sizes. The engine identity comes from setup/setup-receipt.json and the prepared manifest
from probe_constants. The recipe hash is computed with the repository engine (identical to the packed one; pack_setup
refuses uncommitted engine files). A probe has one seed and no job hosts.

Baseline reuse: UNIT must be a sealed a0 init unit of seed 1101 (COMPLETE.json that verifies, job.json, identity.json),
of an engine equal to the kit's or certified against it (round 6), of the same policy and the same prepared manifest, and its evaluation config (``eval_config``: the recipe without its name,
purpose, train and attribution sections and without model.lora) must equal each candidate's; candidates that differ
(for example an eager-attention candidate after an sdpa baseline) are dropped from the ladder and listed. The reading
accepts the pair only when the two engine identities are equal or certified to share their evaluation path.
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


EVAL_EXCLUDED = ("kind", "name", "purpose", "train", "attribution")
EVAL_TRAIN_KEYS = ("lm_head_chunk_tokens", "gradient_checkpointing")   # evaluation reads these two (round 6, M2)


def eval_config(recipe: dict) -> dict:
    """The recipe's evaluation settings: everything but its name, purpose, training and attribution, and the LoRA shape
    (an untuned unit is evaluated with B = 0, whatever the rank); of the train section, the two settings evaluation
    reads. Kept identical to scripts/family_probe_reading.eval_config (a test compares them)."""
    out = {k: v for k, v in recipe.items() if k not in EVAL_EXCLUDED}
    out["model"] = {k: v for k, v in recipe["model"].items() if k != "lora"}
    out["train"] = {k: recipe["train"][k] for k in EVAL_TRAIN_KEYS if k in recipe["train"]}
    return out


def _sha(path: pathlib.Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reading_module():
    """scripts/family_probe_reading.py: its seal and certificate checks are the reading's own (no second copy)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("family_probe_reading", ROOT / "scripts" / "family_probe_reading.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def engine_identity() -> dict:
    """The repository engine's code identity (the kit packs exactly this engine; pack_setup refuses uncommitted files)."""
    out = subprocess.run([str(PY), "-c", "import json;from experiments.safety_selection.common import code_identity;"
                          "print(json.dumps(code_identity()))"], cwd=ROOT, capture_output=True, text=True, check=True,
                         env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}).stdout
    return json.loads(out)


def baseline_record(unit: pathlib.Path, probe: str, prepared: dict, engine: dict | None = None) -> dict:
    """Check a sealed untuned unit for reuse by this probe (module doc) and describe it. Round 6, M5: the unit's
    COMPLETE.json must verify (complete, every listed file present with its hash; model states may be absent after a
    light pull), and its engine must equal ``engine`` (the kit's) or be certified against it, before any pod is paid."""
    for name in ("COMPLETE.json", "job.json", "identity.json"):
        if not (unit / name).is_file():
            raise SystemExit(f"{unit.name}: no {name}: not a sealed unit that can be reused")
    reading = reading_module()
    reading.sealed(unit)
    job, identity = (json.loads((unit / n).read_text()) for n in ("job.json", "identity.json"))
    engine = engine if engine is not None else engine_identity()
    certificate = None
    if identity.get("code_sha256") != engine["sha256"]:
        certificate = reading.certified(identity, {"code_sha256": engine["sha256"], "code_files": engine["files"]})
    if (job.get("arm"), job.get("target_checkpoint"), job.get("seed")) != ("a0", "init", SEED):
        raise SystemExit(f"{unit.name}: not the a0 init unit of seed {SEED}")
    if job.get("manifest_sha256") not in prepared.values() or identity.get("manifest_sha256") != job["manifest_sha256"]:
        raise SystemExit(f"{unit.name}: another prepared manifest than this probe's")
    policy = probes.PROBES[probe]["policy"]
    model = identity["recipe"]["model"]
    if (model["repo_id"], model["revision"]) != (policy["repo_id"], policy["revision"]):
        raise SystemExit(f"{unit.name}: another policy than {probe}'s")
    return {"unit": unit.name, "path": str(unit), "job_sha256": _sha(unit / "job.json"),
            "code_sha256": identity["code_sha256"], "manifest_sha256": job["manifest_sha256"],
            "engine_sha256": engine["sha256"], "certificate": certificate,
            "eval_config": eval_config(identity["recipe"])}


def initial_plan(receipt: dict, probe: str, prepared: dict, rank: str = "r64", recipe: str = "b",
                 baseline: dict | None = None) -> dict:
    spec = probes.PROBES[probe]
    ladder = probes.recipes(probe, rank, recipe)
    suffix = "".join(f"-{x}" for x, default in ((rank, "r64"), (recipe, "b")) if x != default)
    return {"name": f"family-probe-{probe}{suffix}", "probe": probe, "rank": rank, "recipe_kind": recipe,
            "brief": ".ai/briefs/multi-family-probe-engine-20261007.md",
            "status": f"development; one-seed probe {probe}: untuned baseline and Dolly a0 seed {SEED} to e1 (per-pod user approval)",
            "engine_sha256": receipt["engine_sha256"], "git_commit": receipt["git_commit"], "prepared": prepared,
            "first_host_recipes": ladder, "recipe_path": None, "recipe_sha256": None,
            "preflight_prepared": spec["prepared"], "checkpoints": [pc.CHECKPOINT],
            "fixture_compare": {"equal_keys": ["source", "script_sha256", "manifest_sha256", "recipe_sha256", "training_identity", "test_rows"],
                                "resume_keys": ["direct", "loss_direct"]},
            "hosts": {host_name(probe): first_host(probe)}} if baseline is None else \
        _reuse(probe, ladder, spec, baseline, receipt, prepared, rank, recipe)


def _reuse(probe: str, ladder: list[str], spec: dict, baseline: dict, receipt: dict, prepared: dict, rank: str,
           recipe: str) -> dict:
    kept = [r for r in ladder if eval_config(json.loads((ROOT / r).read_text())) == baseline["eval_config"]]
    if not kept:
        raise SystemExit("no candidate of the ladder has the baseline's evaluation config")
    plan = initial_plan(receipt, probe, prepared, rank, recipe)
    plan["first_host_recipes"] = kept
    plan["baseline_reuse"] = {k: v for k, v in baseline.items() if k != "eval_config"}
    plan["baseline_reuse"]["dropped_candidates"] = [r for r in ladder if r not in kept]
    plan["hosts"][host_name(probe)]["base_eval"] = False
    plan["status"] += f"; fine-tune only, the untuned baseline is reused from {baseline['unit']}"
    return plan


def main(argv: list[str]) -> int:
    cmd = argv[0]
    if cmd == "init":
        assert not PLAN.exists(), "plan.json exists"
        baseline = None
        receipt = json.loads((HERE / "setup/setup-receipt.json").read_text())
        if argv[1:2] == ["--reuse-baseline"]:
            engine = engine_identity()          # the baseline is checked against the engine the pods will run
            if engine["sha256"] != receipt["engine_sha256"]:
                raise SystemExit("the repository engine differs from the packed kit's (setup-receipt.json): repack the "
                                 "kit or check out its commit before planning a reuse")
            baseline = baseline_record(pathlib.Path(argv[2]).resolve(), pc.probe(), pc.prepared(), engine)
        save(initial_plan(receipt, pc.probe(), pc.prepared(), pc.RANK, pc.RECIPE, baseline))
    elif cmd == "set-recipe":
        p = load(); r = argv[1]; assert r in p["first_host_recipes"], "not a recipe of this probe's ladder"
        p["recipe_path"] = r; p["recipe_sha256"] = recipe_sha(r); save(p)
    else:
        raise SystemExit("unknown command")
    print(json.dumps({"recipe": load().get("recipe_path"), "hosts": sorted(load()["hosts"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
