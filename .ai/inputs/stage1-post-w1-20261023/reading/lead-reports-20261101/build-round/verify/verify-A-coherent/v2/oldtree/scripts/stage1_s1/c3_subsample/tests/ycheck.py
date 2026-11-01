"""Engine Y's Y2 checks on subsample files, run in a child process that imports ONLY engine Y (test tooling).

Usage: python -B -I ycheck.py REQUEST.json RESULT.json. The request names engine Y's workspace (``engine_y``), a
synthetic prepared folder and its manifest hash, and a list of cases {name, file, bank, run, out_dir}. For each case
it runs, in engine Y's own code and in this order: the job check (jobs.validate_job on a development-role run-one job
with evaluate_bank = the case's bank and bank_file = its file), run_one's round-Y checks before any model loads
(runner._roundy_run_one: the role's split, seed and bank, the code pin, jobs.read_bank_subsample's file checks and
jobs.check_subsample_access for the development role, no hidden switch), the verified view of the source bank with
the membership and field checks (runner._subsample_view -> jobs.subsample_items), the token check of every listed item
as the evaluation makes it (runner._prompt_ids for generation kinds, encode_mc's token audit for arc_utility; the tiny
fixture byte codec), eval-state's round-Y checks for a development-role stored run (runner._roundy_eval_state), and
with ``run`` the whole development run-one on the tiny CPU fixtures (runner.run_one), reporting the generated and
forced-choice ids. Results hold ids, counts, kinds and exception types and messages (engine Y's messages carry ids and
counts only). Nothing here imports the C3 package or engine X.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path


def main() -> int:
    request = json.loads(Path(sys.argv[1]).read_text())
    engine_y = Path(request["engine_y"]).resolve()
    sys.path[:0] = [str(engine_y), str(engine_y / "experiments" / "safety_selection" / "tests")]
    from experiments.safety_selection import jobs, runner
    from experiments.safety_selection.common import code_identity, ids_sha256, read_json, read_jsonl
    from experiments.safety_selection.config import config_sha256
    from experiments.safety_selection.prepare import read_manifest
    from experiments.safety_selection.sources import DataError
    from experiments.safety_selection.textproc import encode_mc

    import ss_fixtures as fx

    folder, sha = Path(request["folder"]), request["sha"]
    recipe = fx.recipe()
    max_prompt = recipe["model"]["max_prompt_tokens"]
    codec = fx.fixture_codec()
    modules = sorted({str(Path(m.__file__).resolve()) for name, m in list(sys.modules.items())
                      if name.split(".")[0] == "experiments" and getattr(m, "__file__", None)})
    result = {"engine_y_identity": code_identity()["sha256"],
              "all_experiments_modules_in_engine_y": all(Path(p).is_relative_to(engine_y) for p in modules),
              "jobs_file": str(Path(jobs.__file__).resolve()), "cases": {}}
    for case in request["cases"]:
        out: dict = {"ok": False, "stage": "job"}
        try:
            job = {"kind": "run-one", "split": "dev", "arm": "a0", "seed": 1101, "role": "development",
                   "target_checkpoint": "q", "evaluate_bank": case["bank"], "bank_file": case["file"],
                   "manifest_sha256": sha, "recipe_sha256": config_sha256(recipe), "code_sha256": None,
                   "resume_from": None, "replicate_of": None, "wall_limit_seconds": None}
            jobs.validate_job(dict(job))
            manifest, digest = read_manifest(folder, sha)
            out["stage"] = "file"
            doc = runner._roundy_run_one(job, manifest, digest, False, None)["doc"]
            out["stage"] = "membership"
            view = runner._subsample_view(folder, digest, case["bank"], doc)
            items = view.banks[case["bank"]]
            out["stage"] = "tokens"
            for item in items:
                if item["kind"] in runner.GENERATION_KINDS:
                    runner._prompt_ids(codec, item, max_prompt)
                elif item["kind"] == "arc_utility":
                    prompt, _ = encode_mc(codec, item["question"], item["labels"], item["texts"], max_prompt)
                    if ids_sha256(prompt) != item["token_sha256"]:
                        raise DataError(f"{item['prompt_id']} encodes differently from the prepared token audit")
            out["stage"] = "eval-state"
            runner._roundy_eval_state({"kind": "eval-state", "evaluate_bank": case["bank"], "bank_file": case["file"],
                                       "code_sha256": None},
                                      {"role": "development", "split": "dev", "seed": 1101}, {}, manifest, digest,
                                      {}, False)
            out.update(ids=[i["prompt_id"] for i in items], kinds=[i["kind"] for i in items], counts=doc["counts"],
                       source=doc["source"], view_banks=sorted(view.banks))
            if case.get("run"):
                out["stage"] = "run-one"
                run = runner.run_one(job, prepared_dir=folder, out_dir=case["out_dir"],
                                     session=runner.Session(recipe, fx.fixture_loaders()))
                q = Path(run["run_dir"]) / "eval" / "q"
                out["generated_ids"] = [r["prompt_id"] for r in read_jsonl(q / "generations.jsonl")]
                arc = q / "arc_utility.jsonl"
                out["arc_ids"] = [r["prompt_id"] for r in read_jsonl(arc)] if arc.exists() else []
                out["complete_bank_subsample"] = read_json(Path(run["run_dir"]) / "COMPLETE.json").get("bank_subsample")
            out["stage"] = "done"
            out["ok"] = True
        except Exception as exc:  # noqa: BLE001  (each refusal is a reported result)
            out.update(error_type=type(exc).__name__, message=str(exc),
                       error_classes=[c.__name__ for c in type(exc).__mro__],
                       trace=traceback.format_exc()[-1500:])
        result["cases"][case["name"]] = out
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
