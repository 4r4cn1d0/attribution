"""Write and update plan.json for one family probe (administrative; the OLMo 3 kit).

    python3.11 plan_tool.py init                 one host <probe>-<seed> (role first, a0, seed probe_constants.SEED,
                                                 untuned baseline first): the probe pod, seed 1101 at rung 1 only
    python3.11 plan_tool.py init --reuse-baseline UNIT
                                                 fine-tune only (base_eval false): the reading pairs e1 with the sealed
                                                 untuned unit UNIT of an earlier run of this probe (GI III round 5);
                                                 for OLMo 3 every host after the probe pod (O3A R3-R5)
    python3.11 plan_tool.py set-recipe RECIPE    the recipe the host's preflight chose (and its hash)

The probe is probe_constants.PROBE, the seed probe_constants.SEED (1101 by default; a Gate A seed kit sets 1102 or
1103), the learning-rate rung probe_constants.RUNG (1 by default; 2 or 3 for OLMo 3's rung probes, probes.RUNGS), the
LoRA rank probe_constants.RANK ("r64" by default; "r16" for the 1B probes' rank-16 ladders) and the recipe kind
probe_constants.RECIPE ("b" by default; "bt" or "g" for the 1B probes); its row in probes.py gives the recipe ladder,
the prepared set, the cap, the preflight wait and the disk sizes. The engine identity comes from
setup/setup-receipt.json and the prepared manifest from probe_constants. The recipe hash is computed with the
repository engine (identical to the packed one; pack_setup refuses uncommitted engine files). A probe has one seed
and no job hosts.

Gate A shape (O3A §16.2 R1-R5; refused otherwise, with the message named): the untuned unit runs on the probe pod with
seed 1101 at rung 1 only; a host at another seed, or at rung 2 or 3, is a fine-tune-only reuse of that sealed untuned
unit; a reuse host at seed 1101 runs at rung 2 or 3 (seed 1101 at rung 1 is the probe pod's own unit); seeds are
1101-1103 (O3A §16.4). The plan's name carries the rung and the seed when they are not the defaults.

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
SEED = pc.SEED                                # the host's and the job's seed (a Gate A seed kit sets 1102 or 1103)
BASELINE_SEED = 1101                          # the untuned unit every host pairs with (O3A R1)
GATE_A_SEEDS = (1101, 1102, 1103)             # O3A §16.4


def load():
    return json.loads(PLAN.read_text())


def save(p):
    PLAN.write_text(json.dumps(p, indent=1, sort_keys=True) + "\n")


def recipe_sha(path):
    return subprocess.run([str(PY), "-c", f"from experiments.safety_selection.config import load_recipe,config_sha256;print(config_sha256(load_recipe('{path}')))"],
                          cwd=ROOT, capture_output=True, text=True, check=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}).stdout.strip()


def host_name(probe: str, seed: int = SEED) -> str:
    return f"{probe}-{seed}"


def gate_a_shape(probe: str, seed: int, rung: int, reuse: bool) -> None:
    """Refuse a host that is not one of the Gate A shape's hosts (module doc). A probe without a ``rungs`` table has
    rung 1 only (probes.recipes refuses the others); its seed rule is the Gate A seed kits' (a seed other than 1101
    reuses the sealed untuned unit)."""
    if seed not in GATE_A_SEEDS:
        raise SystemExit(f"Gate A seeds are 1101-1103 (O3A §16.4): probe_constants.SEED is {seed}")
    if not reuse and (seed != BASELINE_SEED or rung != 1):
        raise SystemExit("the probe pod runs the untuned unit and seed 1101 at rung 1 only (O3A R1): every other seed or "
                         "rung is a fine-tune-only reuse of the sealed untuned unit (init --reuse-baseline UNIT)")
    if reuse and seed == BASELINE_SEED and rung == 1 and "rungs" in probes.PROBES[probe]:
        raise SystemExit("seed 1101 at rung 1 is the probe pod's own unit (O3A R1): a reuse host at seed 1101 runs at "
                         "rung 2 or 3 (O3A R3-R4)")


def first_host(probe: str, seed: int = SEED) -> dict:
    spec = probes.PROBES[probe]
    return {"role": "first", "arm": "a0", "seed": seed, "prepared": spec["prepared"], "base_eval": True,
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
    if (job.get("arm"), job.get("target_checkpoint"), job.get("seed")) != ("a0", "init", BASELINE_SEED):
        raise SystemExit(f"{unit.name}: not the a0 init unit of seed {BASELINE_SEED}")
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
                 baseline: dict | None = None, rung: int = 1, seed: int = SEED) -> dict:
    spec = probes.PROBES[probe]
    ladder = probes.recipes(probe, rank, recipe, rung)
    gate_a_shape(probe, seed, rung, baseline is not None)
    suffix = "".join(f"-{x}" for x, default in ((rank, "r64"), (recipe, "b")) if x != default)
    suffix += (f"-rung{rung}" if rung != 1 else "") + (f"-seed{seed}" if seed != BASELINE_SEED else "")
    return {"name": f"family-probe-{probe}{suffix}", "probe": probe, "rank": rank, "recipe_kind": recipe, "rung": rung,
            "brief": ".ai/briefs/multi-family-probe-engine-20261007.md",
            "status": f"development; one-seed probe {probe}: untuned baseline and Dolly a0 seed {seed} to e1 (per-pod user approval)",
            "engine_sha256": receipt["engine_sha256"], "git_commit": receipt["git_commit"], "prepared": prepared,
            "first_host_recipes": ladder, "recipe_path": None, "recipe_sha256": None,
            "preflight_prepared": spec["prepared"], "checkpoints": [pc.CHECKPOINT],
            "fixture_compare": {"equal_keys": ["source", "script_sha256", "manifest_sha256", "recipe_sha256", "training_identity", "test_rows"],
                                "resume_keys": ["direct", "loss_direct"]},
            "hosts": {host_name(probe, seed): first_host(probe, seed)}} if baseline is None else \
        _reuse(probe, ladder, spec, baseline, receipt, prepared, rank, recipe, rung, seed)


def _reuse(probe: str, ladder: list[str], spec: dict, baseline: dict, receipt: dict, prepared: dict, rank: str,
           recipe: str, rung: int, seed: int) -> dict:
    kept = [r for r in ladder if eval_config(json.loads((ROOT / r).read_text())) == baseline["eval_config"]]
    if not kept:
        raise SystemExit("no candidate of the ladder has the baseline's evaluation config")
    plan = _skeleton(receipt, probe, prepared, rank, recipe, rung, seed)
    plan["first_host_recipes"] = kept
    plan["baseline_reuse"] = {k: v for k, v in baseline.items() if k != "eval_config"}
    plan["baseline_reuse"]["dropped_candidates"] = [r for r in ladder if r not in kept]
    plan["hosts"][host_name(probe, seed)]["base_eval"] = False
    plan["status"] += f"; fine-tune only, the untuned baseline is reused from {baseline['unit']}"
    return plan


def _skeleton(receipt: dict, probe: str, prepared: dict, rank: str, recipe: str, rung: int, seed: int) -> dict:
    """The first-host plan without the Gate A shape check (the reuse path checked it already)."""
    spec = probes.PROBES[probe]
    suffix = "".join(f"-{x}" for x, default in ((rank, "r64"), (recipe, "b")) if x != default)
    suffix += (f"-rung{rung}" if rung != 1 else "") + (f"-seed{seed}" if seed != BASELINE_SEED else "")
    return {"name": f"family-probe-{probe}{suffix}", "probe": probe, "rank": rank, "recipe_kind": recipe, "rung": rung,
            "brief": ".ai/briefs/multi-family-probe-engine-20261007.md",
            "status": f"development; one-seed probe {probe}: untuned baseline and Dolly a0 seed {seed} to e1 (per-pod user approval)",
            "engine_sha256": receipt["engine_sha256"], "git_commit": receipt["git_commit"], "prepared": prepared,
            "first_host_recipes": probes.recipes(probe, rank, recipe, rung), "recipe_path": None, "recipe_sha256": None,
            "preflight_prepared": spec["prepared"], "checkpoints": [pc.CHECKPOINT],
            "fixture_compare": {"equal_keys": ["source", "script_sha256", "manifest_sha256", "recipe_sha256", "training_identity", "test_rows"],
                                "resume_keys": ["direct", "loss_direct"]},
            "hosts": {host_name(probe, seed): first_host(probe, seed)}}


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
        save(initial_plan(receipt, pc.probe(), pc.prepared(), pc.RANK, pc.RECIPE, baseline, pc.RUNG, pc.SEED))
    elif cmd == "set-recipe":
        p = load(); r = argv[1]; assert r in p["first_host_recipes"], "not a recipe of this probe's ladder"
        p["recipe_path"] = r; p["recipe_sha256"] = recipe_sha(r); save(p)
    else:
        raise SystemExit("unknown command")
    print(json.dumps({"recipe": load().get("recipe_path"), "hosts": sorted(load()["hosts"]), "rung": load().get("rung")}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
