"""Versioned descriptive reader for funded phase1; completed seed1121 reader unchanged."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import argparse,hashlib,json,math,statistics
from scripts.side_project_cause.analyze import SealedUnit,require,relative_path,decode,hex_hash,digest,finite,same_number,outcomes,InputError,IDENTITY_KEYS,MODEL_REPOS
INTERVENTION_KEYS={'loss','loss_weighting','lr','lr_schedule','warmup_steps','schedule_until'}

def verify_identities(unit: SealedUnit, spec: dict, pins: dict) -> tuple[dict, dict]:
    job, identity, marker = unit.obj("job.json"), unit.obj("identity.json"), unit.marker
    require(marker.get("kind") == job.get("kind") == "run-one", "need a run-one training unit")
    require(marker.get("job_sha256") == unit.report["input_hashes"]["job.json"], "COMPLETE job hash differs")
    require(isinstance(marker.get("identity"), dict), "COMPLETE identity missing")
    for key in IDENTITY_KEYS:
        hex_hash(identity.get(key), f"identity.{key}")
        require(marker["identity"].get(key) == identity[key], f"completion/identity disagree on {key}")
    for key, expected in (("manifest_sha256", pins["prepared_manifest_sha256"]),
                          ("recipe_sha256", spec["config_sha256"]), ("code_sha256", pins["engine_sha256"])):
        require(job.get(key) == identity[key] == expected, f"job/identity/protocol disagree on {key}")
    require(type(job.get("seed")) is int and job["seed"] == spec["seed"], "job seed differs from planned seed")
    require(job.get("arm") == spec.get("job_arm", "a0"), "job data-edit arm differs from expected job_arm (default a0)")
    require(job.get("target_checkpoint") == marker.get("target_checkpoint") == "e1", "not an e1 unit")
    require(job.get("split") == job.get("evaluate_bank") == "dev" and job.get("role") == "development",
            "study requires development training/evaluation bank")
    require(job.get("resume_from") is None and job.get("replicate_of") is None
            and marker.get("resumed_from") is None, "fresh direct-init unit required; dependency paths are not followed")
    require(unit.obj("dependencies.json").get("dependencies") == [], "fresh unit must have no dependencies")
    recipe = identity.get("recipe")
    require(isinstance(recipe, dict) and digest(recipe) == spec["config_sha256"], "embedded recipe canonical hash mismatch")
    model, train = recipe.get("model"), recipe.get("train")
    require(isinstance(model, dict) and isinstance(train, dict), "recipe model/train missing")
    require(model.get("repo_id") == MODEL_REPOS[spec["model"]], "recipe checkpoint does not match declared model")
    require(digest({"model": model, "train": train}) == identity["training_identity"], "training identity hash mismatch")
    code_files = identity.get("code_files")
    require(isinstance(code_files, dict) and bool(code_files), "code file hash manifest missing")
    for rel, sha in code_files.items():
        require(isinstance(rel, str), "invalid code manifest path")
        hex_hash(sha, "code_files digest")
    require(digest(code_files) == pins["engine_sha256"], "aggregate code manifest hash mismatch")
    schedule = "constant" if spec["arm"] in ("A","H") else "warmup_cosine"
    weighting = "token_mean" if spec["arm"] == "D" else None
    require(train.get("lr_schedule") == schedule and train.get("loss_weighting") == weighting,
            "recipe does not implement the declared A/C/D intervention")
    same_number(train.get("lr"), 5e-5 if spec["arm"] == "H" else 1e-4, "recipe peak LR")
    if spec["arm"] not in ("A","H"):
        require(train.get("warmup_steps") == 4 and train.get("schedule_until") == "e1",
                "scheduled intervention requires four-step warmup/cosine until e1")
    assets = unit.obj("assets.json")
    policy = assets.get("policy")
    require(isinstance(policy, dict) and policy.get("repo_id") == model["repo_id"]
            and policy.get("revision") == model.get("revision"), "loaded policy/recipe snapshot mismatch")
    unit.report["verification"].update(
        job_identity_verified=True, config_identity_verified=True, prepared_identity_verified=True,
        aggregate_code_manifest_verified=True, engine_source_bytes_verified=False,
    )
    unit.report["identities"] = {**{k: identity[k] for k in IDENTITY_KEYS},
                                "model_repo_id": model["repo_id"], "model_revision": model.get("revision"),
                                "job_arm": job["arm"], "seed": job["seed"], "target_checkpoint": "e1"}
    return recipe, identity

def training_evidence(unit: SealedUnit, spec: dict) -> dict:
    marker = unit.marker
    state, plan = unit.obj("states/e1/state.json"), unit.obj("plan.json")
    trajectory = marker.get("trajectory")
    require(isinstance(trajectory, dict), "completion trajectory missing")
    for key in ("seed", "arm", "split", "role"):
        expected = spec["seed"] if key == "seed" else unit.obj("job.json")[key]
        require(trajectory.get(key) == state.get(key) == expected, f"state/trajectory job {key} mismatch")
    for key in ("manifest_sha256", "recipe_sha256"):
        require(state.get(key) == unit.obj("job.json")[key], f"state {key} mismatch")
    require(state.get("checkpoint") == "e1" and state.get("step") == 38
            and state.get("completed_epochs") == 1, "e1 must have completed one epoch, 38 updates")
    init = hex_hash(state.get("init_fingerprint"), "init_fingerprint")
    require(trajectory.get("init_fingerprint") == init, "state/trajectory initialization mismatch")
    initial = unit.obj("states/init/state.json")
    require(initial.get("checkpoint") == "init" and initial.get("step") == 0
            and initial.get("seed") == spec["seed"]
            and initial.get("init_fingerprint") == initial.get("adapter_fingerprint") == init,
            "saved initial-state identity differs from trajectory/e1")
    require(plan.get("stream_sha256") == trajectory.get("stream_sha256") == state.get("stream_sha256")
            and digest(plan.get("stream")) == plan["stream_sha256"], "stream identity mismatch")
    steps = unit.rows("steps.jsonl")
    require(len(steps) == 38 and [s.get("step") for s in steps] == list(range(1, 39)),
            "actual optimizer steps missing/repeated/out of order")
    require(all(s.get("epoch") == 0 and isinstance(s.get("rows"), list) and s["rows"]
                and all(isinstance(r, str) for r in s["rows"]) for s in steps), "invalid epoch/row evidence")
    rows = [r for s in steps for r in s["rows"]]
    require(len(set(rows)) == len(rows) and len(rows) == state.get("examples_seen")
            == trajectory.get("retained_rows"), "actual epoch has duplicate/missing training rows")
    require(trajectory.get("removed_rows") == 0, "recipe study must not remove training rows")
    stream = plan["stream"]
    require(stream.get("seed") == spec["seed"] and stream.get("removed") == []
            and stream.get("corpus_sha256") == digest(sorted(rows)), "actual row set differs from plan")
    rates = [finite(s.get("lr"), "applied LR") for s in steps]
    expected_rates = ([5e-5 if spec["arm"] == "H" else 1e-4] * 38 if spec["arm"] in ("A","H") else
                      [1e-4 * ((s - 1) / 4 if s <= 4 else
                               0.5 * (1 + math.cos(math.pi * ((s - 5) / 34)))) for s in range(1, 39)])
    require(all(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15) for a, b in zip(rates, expected_rates)),
            "saved applied LRs differ from declared constant/warmup-cosine treatment")
    unit.report["verification"].update(e1_actual_steps_and_row_set_verified=True, applied_learning_rates_verified=True)
    return {"optimizer_updates": 38, "examples": len(rows), "init_fingerprint": init,
            "stream_sha256": plan["stream_sha256"], "actual_row_order_sha256": digest(rows),
            "actual_row_set_sha256": digest(sorted(rows)),
            "actual_steps_row_order_sha256": hashlib.sha256(json.dumps([s["rows"] for s in steps], separators=(",", ":")).encode()).hexdigest(),
            "step_layout_sha256": digest([s["rows"] for s in steps]),
            "applied_lr_sum": math.fsum(rates), "applied_lr_mean": statistics.fmean(rates),
            "applied_lr_sha256": digest(rates)}

def analyze_unit(spec: dict, root: Path, pins: dict, protocol: dict) -> dict:
    report = {"planned": spec, "status": "technical_failure", "failures": [],
              "input_hashes": {}, "verification": {}, "outcomes": None}
    path = relative_path(root, spec["run_dir"], "run_dir")
    report["resolved_run_dir"] = str(path)
    if not path.is_dir():
        report.update(status="missing", failures=["declared unit directory missing"])
        return report
    try:
        # A traceback is a technical failure even if someone subsequently wrote a marker.
        error_path = relative_path(path, "error.txt", "error.txt")
        if error_path.is_file():
            raw = error_path.read_bytes()
            report["input_hashes"]["error.txt"] = hashlib.sha256(raw).hexdigest()
            report["technical_error_excerpt"] = raw.decode("utf-8", errors="replace")[-4000:]
            raise InputError("error.txt present: technical failure preserved")
        if not (path / "COMPLETE.json").is_file():
            report.update(status="incomplete", failures=["COMPLETE.json missing"])
            return report
        unit = SealedUnit(path, report)
        recipe, _ = verify_identities(unit, spec, pins)
        report["training"] = training_evidence(unit, spec)
        report["outcomes"] = outcomes(unit)
        # Pairing context excludes only the two manipulated training treatments and metadata.
        report["fixed_recipe_context_sha256"] = digest({
            **{k: v for k, v in recipe.items() if k not in ("train", "name", "purpose")},
            "train": {k: v for k, v in recipe["train"].items() if k not in INTERVENTION_KEYS},
        })
        report["judge_and_generation_sha256"] = digest({k: recipe.get(k) for k in ("generation", "guard", "arc", "secondary_toxicity")})
        report["verification"]["original_sampled_endpoint_verified"] = True
        report["status"] = "complete"
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        report["failures"].append(f"{type(exc).__name__}: {exc}")
    return report
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 p=json.loads(a.protocol.read_text());require(p['status']=='FROZEN' and p['phase_id']=='funded-phase1-1122','phase not frozen')
 require(sha(__file__)==p['implementation_hashes']['followup_analyze.py'],'reader pin')
 require(sha(Path(__file__).with_name('analyze.py'))==p['original_reader_sha256'],'original helper pin')
 expected={(m,arm,1122) for m,arms in [('olmo1b','AHCD'),('olmo7b','HC')] for arm in arms}
 require(len(p['units'])==6 and {(u['model'],u['arm'],u['seed']) for u in p['units']}==expected,'funded roster differs')
 reports=[analyze_unit(u,a.root,p,p) for u in p['units']];failures=[str(r['planned'])+':'+str(r['failures']) for r in reports if r['status']!='complete'];pairing={}
 cells={(r['planned']['model'],r['planned']['arm']):r for r in reports}
 if not failures:
  for model,arms in [('olmo1b','AHCD'),('olmo7b','HC')]:
   rr=[cells[model,arm] for arm in arms]
   fields={'init':[r['training']['init_fingerprint'] for r in rr],'actual_order':[r['training']['actual_row_order_sha256'] for r in rr],'fixed_recipe':[r['fixed_recipe_context_sha256'] for r in rr],'sample_layout':[r['outcomes']['unsafe']['sample_layout_sha256'] for r in rr]}
   pairing[model]={k:len(set(v))==1 for k,v in fields.items()};require(all(pairing[model].values()),'within-model pairing mismatch')
   receipt=a.root/'cause'/f'{model}-BATCH-DONE.json';b=json.loads(receipt.read_text());require(b['ok'] and b['protocol_sha256']==sha(a.protocol) and b['engine_sha256']==p['engine_sha256'],'batch receipt pin')
   require(len(b['units'])==len(arms) and {u['arm'] for u in b['units']}==set(arms),'batch roster')
   for u in b['units']:
    r=cells[model,u['arm']];require(u['complete_sha256']==r['input_hashes']['COMPLETE.json'] and u['seed']==1122 and u['run_dir']==r['planned']['run_dir'] and u['status']=='complete_verified','batch unit mismatch')
    require(all(u[k]==0 for k in ('make_exit','run_exit','verify_exit')),'batch exits')
  require(len({r['training']['actual_row_order_sha256'] for r in reports})==1,'cross-checkpoint row mismatch')
  require(len({r['outcomes']['unsafe']['sample_layout_sha256'] for r in reports})==1,'cross-checkpoint sample mismatch')
  for model in ('olmo1b','olmo7b'):require(math.isclose(cells[model,'H']['training']['applied_lr_mean'],cells[model,'C']['training']['applied_lr_mean'],abs_tol=1e-15),'mean rate mismatch')
 contrasts={}
 if not failures:
  for model,pairs in [('olmo1b',[('C-A','C','A'),('H-A','H','A'),('C-H','C','H'),('D-C','D','C'),('D-A','D','A')]),('olmo7b',[('C-H','C','H')])]:
   contrasts[model]={}
   for name,x,y in pairs:
    xx=cells[model,x]['outcomes'];yy=cells[model,y]['outcomes']
    contrasts[model][name]={'unsafe_pp':float(100*(Fraction(xx['unsafe']['unsafe'],600)-Fraction(yy['unsafe']['unsafe'],600))),'invalid_counts':[xx['unsafe']['invalid'],yy['unsafe']['invalid']],'benign_refusal_pp':100*(xx['overrefusal']['refusal_rate']-yy['overrefusal']['refusal_rate']),'query_nll_change':xx['task_query_loss']['mean']-yy['task_query_loss']['mean']}
  contrasts['1B_minus7B_timing_pp']=contrasts['olmo1b']['C-H']['unsafe_pp']-contrasts['olmo7b']['C-H']['unsafe_pp']
 mechanism=a.root/'cause/mechanism/olmo1b/report.json';mechanism_available=mechanism.is_file();mechanism_receipt=None;mechanism_failure=None
 if mechanism_available:
  try:
   from scripts.side_project_cause.mechanism_receipt import validate
   mechanism_receipt=validate(mechanism.parent,a.root,p,sha(a.protocol))
  except (OSError,ValueError,TypeError,KeyError,AssertionError) as exc:mechanism_failure=type(exc).__name__+':'+str(exc)
 else:mechanism_failure='report unavailable'
 result={'phase_id':p['phase_id'],'protocol_sha256':sha(a.protocol),'status':'complete' if not failures and mechanism_receipt else 'training_complete_mechanism_incomplete' if not failures else 'incomplete','failures':failures,'units':reports,'pairing':pairing,'contrasts':contrasts,'mechanism_report_available':mechanism_available,'training_status':'complete' if not failures else 'incomplete','mechanism_status':'validated_complete' if mechanism_receipt else 'not_validated_complete','mechanism_receipt':mechanism_receipt,'mechanism_failure':mechanism_failure,'mechanism_report_sha256':sha(mechanism) if mechanism_available else None,'scope':'one fresh seed1122; full1B recipe replication; bilateral matched-mean timing; 7B A/D replication and additional seeds remain unfunded; no population tests/CI/sole-mediator or parameter-count proof'}
 require(not a.out.exists(),'analysis never overwritten');a.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'status':result['status'],'failures':len(failures)}));return 0 if not failures and mechanism_receipt else 1
if __name__=='__main__':raise SystemExit(main())
