"""Finish the lead host's round-1 work after its pod was restarted (runs on the pod).

    venv/bin/python lead_resume.py SCORES_SHA256

The first lead run scored the rows (scores-001) and built the removal files (edits-remove-001); its stop timer
then ended the pod while generate-rewrites was running (rewrites-001 is that run's incomplete folder, kept as it
is). This script checks the engine, recipe and data as lead_pipeline.py does, checks that scores-001/scores.json
is the file the removal edits were built from (their provenance hash), and then runs the remaining steps with
the plan's own arguments, writing new folders:
  generate-rewrites over the top 10% and the random 10%        -> rewrites-002/rewrites.json
  build-edits, all four round-1 files                           -> edits-round1-001/
The removal files of the two builds must be byte-identical. LEAD-DONE.json lists the round-1 edit files.
"""
import datetime as dt, hashlib, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path("/workspace/attribution-headroom"); os.chdir(ROOT)
expected_scores = sys.argv[1]
plan = json.loads(pathlib.Path("plan.json").read_text())
assert not pathlib.Path("LEAD-DONE.json").exists(), "the lead work already finished"

from experiments.safety_selection.common import code_identity  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402

assert code_identity()["sha256"] == plan["engine_sha256"], "engine code differs from the plan"
assert config_sha256(load_recipe(plan["recipe_path"])) == plan["recipe_sha256"], "recipe differs from the plan"
assert pathlib.Path(plan["prepared_path"], "manifest.sha256").read_text().strip() == plan["manifest_sha256"]


def sha(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


assert sha("scores-001/scores.json") == expected_scores, "scores-001 is not the file the removal edits were built from"
env = {**os.environ, "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
       "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(ROOT), "HF_HUB_OFFLINE": "1"}
steps = {s["receipt"]: s["args"] for s in plan["lead_steps"]}
rewrites = [a if a != "rewrites-001" else "rewrites-002" for a in steps["lead-process-3-rewrites"]]
build = [a if a != "rewrites-001/rewrites.json" else "rewrites-002/rewrites.json" for a in steps["lead-process-4-edits-round1"]]
assert "rewrites-002" in rewrites and "rewrites-002/rewrites.json" in build
for receipt, args in (("lead-process-3b-rewrites", rewrites), ("lead-process-4-edits-round1", build)):
    subprocess.run(["python3", "process_receipt.py", "--out", receipt, "--", "venv/bin/python", "-m",
                    "experiments.safety_selection", *args], env=env, check=True)
early, final = pathlib.Path(plan["early_edits_dir"]), pathlib.Path(plan["final_edits_dir"])
files = {}
for name in plan["round1_edit_files"]:
    files[name] = {"path": str(final / name), "sha256": sha(final / name), "arm": "edit-" + sha(final / name)}
    if (early / name).exists():
        assert sha(early / name) == files[name]["sha256"], f"{name}: the early and final builds differ"
record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "engine_sha256": plan["engine_sha256"],
          "scores_sha256": expected_scores, "rewrites_sha256": sha("rewrites-002/rewrites.json"),
          "note": "resumed after the stop timer ended the first lead run during generate-rewrites (rewrites-001 incomplete)",
          "edit_files": files}
pathlib.Path("LEAD-DONE.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record), flush=True)
