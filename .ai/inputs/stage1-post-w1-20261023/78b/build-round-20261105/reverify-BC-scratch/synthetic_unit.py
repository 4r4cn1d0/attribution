"""Push the rebuilt Llama R_d1-R_d3 through noise_reading.read_unit with a synthetic SEALED unit folder (job.json,
identity.json, assets.json, COMPLETE.json, edit.json, lock), then tampered copies. No eval files: read_unit stops before
arm_from_unit. Prints verdicts, hashes and counts only."""
import hashlib, json, pathlib, shutil, sys
WS = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(WS))
from scripts.scale78b import noise_reading as nr
GB = nr.GB
LLAMA_M = nr.FAMILIES["llama31-8b"]["manifest_sha256"]; TI = nr.FAMILIES["llama31-8b"]["training_identity"]
ENGINE_X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
recipe = json.loads((WS / "experiments/safety_selection/configs/study-kt-llama31-8b-r64-b5e5-mb2-20261010.json").read_text())
ti = GB.canonical_sha256({"model": recipe.get("model"), "train": recipe.get("train")})
print("training identity of the Llama main config by GB.canonical_sha256 equals the pin:", ti == TI)
recipe_sha = GB.canonical_sha256(recipe)
LS = WS / ".ai/inputs/scale-78b-sealed-llama3-20261105/out"
listed = {r["path"]: r for r in json.loads((LS / "MANIFEST.json").read_text())["files"]}
def sha(b): return hashlib.sha256(b).hexdigest()
def cj(o): return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()
ENV = {"python": "3.11.9", "machine": "x86_64", "device": "cuda", "packages": {"torch": "2.4.0"}, "deterministic_algorithms": True,
       "safety_selection_numeric": "v1", "cuda": {"name": "A100", "capability": "8.0", "torch_cuda_runtime": "12.1", "cudnn": 8902, "settings": {}, "env": {}}}
def make_unit(folder, edit_bytes, seed, arm=None, resume=None):
    if folder.exists(): shutil.rmtree(folder)
    folder.mkdir(parents=True)
    arm = arm or "edit-" + sha(edit_bytes)
    lock = b"lock-bytes\n"; lock_sha = sha(lock)
    job = {"kind": "run-one", "target_checkpoint": "e1", "replicate_of": None, "resume_from": resume, "evaluate_bank": "dev", "split": "dev",
           "role": "development", "seed": seed, "arm": arm, "code_sha256": ENGINE_X, "manifest_sha256": LLAMA_M, "recipe_sha256": recipe_sha}
    ident = {"code_sha256": ENGINE_X, "manifest_sha256": LLAMA_M, "training_identity": TI, "recipe": recipe, "recipe_sha256": recipe_sha}
    assets = {"environment": ENV, "policy": {"name": "p"}, "guard": {"repo": "g", "revision": "r", "files": {}}, "environment_lock": {"sha256": lock_sha}}
    files = {"job.json": cj(job), "identity.json": cj(ident), "assets.json": cj(assets), "edit.json": edit_bytes, "environment-linux.lock": lock}
    for n, b in files.items(): (folder / n).write_bytes(b)
    marker = {"complete": True, "kind": "run-one", "job_sha256": sha(files["job.json"]), "completed_utc": "2026-11-05T15:00:00+00:00",
              "identity": {"code_sha256": ENGINE_X, "manifest_sha256": LLAMA_M, "training_identity": TI, "recipe_sha256": recipe_sha},
              "files": {n: sha(b) for n, b in files.items()}}
    mb = cj(marker); (folder / "COMPLETE.json").write_bytes(mb)
    return {"path": str(folder), "complete_sha256": sha(mb), "arm": arm}
def attempt(label, spec, seed):
    try:
        u = nr.read_unit(spec, "R", seed, "llama31-8b", ENGINE_X, f"llama31-8b R@{seed}", OUT)
        print(f"ACCEPTED  {label}: complete {u['complete_sha256'][:8]} recipe {u['recipe_sha256'][:8]} resumed {u['resumed_from_complete_sha256']}")
        return True
    except SystemExit as exc:
        msg = str(exc); print(f"REFUSED   {label}: {msg[:140]}"); return False
results = {}
for d in (1, 2, 3):
    data = (LS / f"edits/R_d{d}.json").read_bytes()
    assert listed[f"edits/R_d{d}.json"]["arm"] == "edit-" + sha(data)
    spec = make_unit(OUT / f"unit-R{d}", data, 1100 + d, arm=listed[f"edits/R_d{d}.json"]["arm"])
    results[f"R_d{d} genuine"] = attempt(f"R_d{d} as llama31-8b R@{1100 + d} (arm = the MANIFEST's)", spec, 1100 + d)
# tampered copies (each consistent inside the unit: COMPLETE.json re-sealed, job.json arm re-derived) against the MANIFEST's arm or against the fields
d1 = json.loads((LS / "edits/R_d1.json").read_bytes())
t = json.loads(json.dumps(d1)); t["remove"][0] = t["remove"][0][:-1] + ("0" if t["remove"][0][-1] != "0" else "1"); tb = cj(t)
spec = make_unit(OUT / "unit-tamper-row", tb, 1101, arm=listed["edits/R_d1.json"]["arm"])          # inputs name the sealed arm
results["row changed, sealed arm named"] = not attempt("R_d1 with one row changed, the inputs naming the sealed arm", spec, 1101)
spec = make_unit(OUT / "unit-tamper-row-ownarm", tb, 1101)                                          # inputs name the tampered file's own arm
results["row changed, own arm named"] = attempt("R_d1 with one row changed, the inputs naming its own arm (read_unit sees no rows; the engine/MANIFEST do)", spec, 1101)
t = json.loads(json.dumps(d1)); t["provenance"]["selection"]["draw"] = 2; tb = cj(t)
results["draw 2 in slot 1101"] = not attempt("R_d1 with selection.draw 2 at seed 1101", make_unit(OUT / "unit-tamper-draw", tb, 1101), 1101)
t = json.loads(json.dumps(d1)); t["manifest_sha256"] = nr.FAMILIES["olmo2-7b"]["manifest_sha256"]; tb = cj(t)
results["OLMo manifest"] = not attempt("R_d1 re-labelled with the OLMo manifest", make_unit(OUT / "unit-tamper-manifest", tb, 1101), 1101)
t = json.loads(json.dumps(d1)); t["provenance"]["selection"]["family"] = "unit"; tb = cj(t)
results["family unit"] = not attempt("R_d1 with selection.family 'unit'", make_unit(OUT / "unit-tamper-family", tb, 1101), 1101)
t = json.loads(json.dumps(d1)); t["edit_kind"] = "rewrite"; tb = cj(t)
results["edit_kind rewrite"] = not attempt("R_d1 with edit_kind 'rewrite'", make_unit(OUT / "unit-tamper-kind", tb, 1101), 1101)
results["R_d2 in slot 1101"] = not attempt("R_d2 in the 1101 slot", make_unit(OUT / "unit-d2-1101", (LS / "edits/R_d2.json").read_bytes(), 1101), 1101)
seal = (WS / ".ai/inputs/gate-b-sealed-20261008/out/edits/R_d1.json").read_bytes()
results["SEAL OLMo R_d1 as Llama"] = not attempt("SEAL's OLMo R_d1 under llama31-8b", make_unit(OUT / "unit-seal", seal, 1101), 1101)
results["resumed R"] = not attempt("R_d1 unit whose job.json resumes", make_unit(OUT / "unit-resumed", (LS / "edits/R_d1.json").read_bytes(), 1101, resume="init"), 1101)
h1 = (WS / ".ai/inputs/scale-78b-length-rules-llama3-20261105/out/edits/octile_0.json").read_bytes()
results["Llama H1 as R"] = not attempt("the Llama H1 file as R@1101", make_unit(OUT / "unit-h1", h1, 1101), 1101)
# the engine's own view of the row-tampered copy
from experiments.safety_selection.edits import EditError, parse_edit
import importlib.util
spec_w = importlib.util.spec_from_file_location("w", WS / ".ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py"); W = importlib.util.module_from_spec(spec_w); spec_w.loader.exec_module(W)
stub = W.PreparedView(WS / "tmp/kt-prepared/prepared-kt-dolly-llama3", LLAMA_M).engine_stub()
t = json.loads(json.dumps(d1)); t["remove"][0] = t["remove"][0] + "x"; 
try:
    parse_edit(cj(t), stub); print("ENGINE accepted a copy with an unknown row id (unexpected)"); results["engine unknown row"] = False
except EditError as e:
    print("ENGINE refuses a copy with an unknown row id:", type(e).__name__); results["engine unknown row"] = True
ok = parse_edit((LS / "edits/R_d1.json").read_bytes(), stub); print("ENGINE accepts the genuine R_d1: removed", len(ok.removed), "arm == MANIFEST", ok.arm == listed["edits/R_d1.json"]["arm"])
print("SUMMARY all expected:", all(results.values()), {k: v for k, v in results.items() if not v})
shutil.rmtree(OUT)
