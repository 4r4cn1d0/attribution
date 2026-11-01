"""Verifier's end-to-end probe for kit round 34 (synthetic data only; nothing real is read).

1. B14's REAL pass (scripts/stage1_s1/overlap_similarity.run) on B14's own synthetic fixture (tiny CPU model,
   synthetic prepared set and edits) writes a real-format similarity.json.
2. The kit's checks (round-34 copy) with stage1_rules' pins pointed at that fixture: similarity_problems, the
   runner's similarity_record (with the stdout line exactly as overlap_similarity.main prints it) and the Mac's
   similarity_record_problem. Expected: no problem.
3. N3: the same output with log lines a stderr partial line could leave (a progress bar ending in a carriage
   return; a warning without a newline). Shows what the printed-SHA-256 rule does then.

    python -B e2e_probe.py WS_ROOT KIT_COPY WORK
"""
import hashlib
import importlib.util
import json
import pathlib
import shutil
import sys

WS, KIT, WORK = (pathlib.Path(a) for a in sys.argv[1:4])
if WORK.exists():
    raise SystemExit(f"{WORK} exists")
sys.path.insert(0, str(WS))
_engine = importlib.util.find_spec("experiments.safety_selection")
sys.path.insert(1, str(pathlib.Path(_engine.origin).resolve().parent / "tests"))
sys.path.insert(2, str(WS / "scripts" / "stage1_s1" / "tests"))

import b14_fixtures as bf  # noqa: E402
import ss_fixtures as fx  # noqa: E402
from experiments.safety_selection.common import sha256_bytes  # noqa: E402
from scripts.stage1_s1 import overlap_similarity as sim  # noqa: E402


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


env = bf.Env(WORK / "env")
first = WORK / "pod-0"
(first / "job-0").mkdir(parents=True)
doc, data = sim.run(env.prepared, env.recipe, env.given(), first / "job-0" / "similarity", fx.fixture_loaders(),
                    env.settings, sim.SETTINGS_SHA256)
print("B14 real run: provenance.inputs keys", sorted(doc["provenance"]["inputs"]),
      "script_sha256", doc["provenance"]["script_sha256"][:12], "settings_sha256",
      doc["provenance"]["settings_sha256"][:12])

spec = importlib.util.spec_from_file_location("jr34_probe", KIT / "setup" / "job_runner_stage1.py")
jr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jr)
r = jr.rules
print("kit rules loaded from", pathlib.Path(r.__file__).parent)
# the kit's pins pointed at B14's fixture (counts: the fixture has 12 prompts and 4 rows per add set)
r.SIM_ADD_SETS = {n: env.edits[n][1] for n in ("S1", "S3", "S4")}
r.PREPARED_MANIFESTS[r.PREPARED_NAME] = env.manifest
r.SIM_DEV_BANK = {"path": "banks/dev.jsonl", "sha256": sha(env.prepared / "banks" / "dev.jsonl")}
r.SIM_PROMPTS, r.SIM_ROWS = 12, 4
plan = {"recipes": {r.REC: {"config_sha256": env.recipe_sha}}}
print("similarity_problems on B14's real output:", r.similarity_problems(doc, env.recipe_sha))
print("similarity_problems with the real counts (200, 48) left in:",
      (lambda: (setattr(r, "SIM_PROMPTS", 200), r.similarity_problems(doc, env.recipe_sha),
                setattr(r, "SIM_PROMPTS", 12))[1])())

digest = sha256_bytes(data)
line = f"wrote {sim.OUTPUT} into {pathlib.Path('job-0/similarity')} ({digest})"      # overlap_similarity.main's print
summary = "".join(f"  {n}: {b['rows']} rows, {doc['eval']['prompts']} prompts, s_max {b['summary']['min']:.6f} to "
                  f"{b['summary']['max']:.6f}\n" for n, b in doc["add_sets"].items())
cases = {"plain (as main prints it)": line + "\n" + summary,
         "after a progress bar that ends in a carriage return": "Loading: 100%|##########| 1/1 [00:00<00:00]\r"
                                                                  + line + "\n" + summary,
         "after a warning written without a newline": "UserWarning: something" + line + "\n" + summary,
         "the line twice (two passes into one log)": line + "\n" + line + "\n" + summary}
for k, (name, log) in enumerate(cases.items()):
    pod = WORK / f"pod-{k + 1}"
    shutil.copytree(first / "job-0" / "similarity", pod / "job-0" / "similarity")
    (pod / "job-0-similarity").mkdir(parents=True)
    (pod / "job-0-similarity" / "process.log").write_text(log)
    rel, why = jr.similarity_record(pod, plan, "sim-1", 0)
    outcome = "complete" if rel else f"CRASHED: {why}"
    mac = None
    if rel:
        outputs = {r.similarity_output(0): sha(pod / r.similarity_output(0)), rel: sha(pod / rel)}
        mac = r.similarity_record_problem(pod, {"index": 0, "outputs": outputs}, "sim-1", env.recipe_sha)
    record = json.loads((pod / r.similarity_record_path(0)).read_text())
    print(f"[{name}] runner: {outcome}; record printed_sha256 {str(record['printed_sha256'])[:12]}; "
          f"problems {record['problems']}; Mac check: {mac}")
