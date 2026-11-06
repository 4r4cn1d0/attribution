"""Run the family preflight on this 7-8B host (runs on the pod; K2 of T4; the ADAPTATION of the stage-1 kit's
setup/preflight_stage1.py, itself from runkit/gate-b-olmo/setup/preflight_gateb.py).

    venv/bin/python preflight_stage1.py [--dry-run]

The 7-8B changes: the host's one recipe is the family's main config (plan.json's preflight_recipes, written by
orchestrate.py from job_runner_stage1.preflight_recipe); the pod's family (kit-family.json beside stage1_rules.py)
must be plan.json's. PREFLIGHT-DONE.json keeps the keys the 17 measured files hold (ok, recipe, folder,
verification_sha256, init_equals_untuned, ms_per_step_full, projected_job_upper_s, training_s, overhead_s,
generation_batch, tried, cap_projection, guard, governing_stop_utc, cap_remaining_s) and adds: ``family``; ``bank``,
the evaluation bank the chosen candidate's verification.json saw (job_runner_stage1.bank_from_verification: the cap
in tokens, the greedy prompts, the sampled answers, the generation batch); ``speed`` = {s_pod, refused}, the M-cap
rule's speed factor on this pod (rules_78b.speed_factor on training_s and ms_per_step_full; KD3: s_pod > 1.15 or a
missing field refuses the pod before any job, so ``ok`` is then false and orchestrate.py stops the host: the pre-job
path, its jobs requeued). The job runner reads the same two documents again (rules_78b.job_decision) before each job.
The stage-1 O500 projection (the W1-18 branch's 500-prompt O-ext bank) does not exist at 7-8B and is gone. The
chosen candidate's verification.json stays in its folder (cuda-preflight-N/verification.json) at the recorded
SHA-256: the job runner and the Mac (orchestrate.py fetches it) read it from there.

From the Gate B preflight (unchanged below): PREFLIGHT-DONE.json carries the chosen candidate's whole
``cap_projection`` block and ``guard`` ([D17] 4: the engine's guard_pin for the chosen recipe on this pod). A gated
probe (Llama-3.1-8B) refuses to start unless gated-download-receipt.json says ok and every gated file it lists is
present in its HF cache snapshot (the container disk is erased on a stop); no token variable or token file may exist;
the skip rules (``skip_reason``): after a candidate records generation_memory_ok false, every later candidate whose
generation batch is at least as large is skipped; after batch_proof_ok false, every later candidate with the same
generation batch and attention; after tokenizer_ok false, every later candidate. --dry-run prints the candidate
commands from plan.json in the current folder and writes nothing.
"""
import datetime as dt, hashlib, json, os, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
for _folder in (HERE, HERE.parent):                 # the pod: beside this script; the kit: one folder up
    if (_folder / "stage1_rules.py").is_file():
        sys.path.insert(0, str(_folder))
        break
import stage1_rules as rules  # noqa: E402
import rules_78b as r78  # noqa: E402
sys.path.insert(0, str(HERE))
import job_runner_stage1 as runner  # noqa: E402  (bank_from_verification: the same reading as the job runner's)
import download_models_stage1 as downloads  # noqa: E402  (no_token_left: the library's token-file paths; D6)

ROOT = pathlib.Path("/workspace/attribution-headroom")
HEARTBEAT = pathlib.Path("/workspace/.pod-timer/heartbeat.json")
TOKEN_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")


def generation_batch(recipe_path: str, root: pathlib.Path) -> int:
    return json.loads((root / recipe_path).read_text())["generation"]["batch_size"]


def attention(recipe_path: str, root: pathlib.Path) -> str:
    return json.loads((root / recipe_path).read_text())["model"]["attn_implementation"]


def skip_reason(batch: int, attn: str, failed_generation_batches: list[int], failed_proofs: list[tuple[int, str]],
                tokenizer_failed: bool) -> str | None:
    """Why a later candidate is skipped, or None (module doc)."""
    if tokenizer_failed:
        return "an earlier candidate failed the tokenizer check, which the ladder does not change"
    if skipped(batch, failed_generation_batches):
        return "an earlier candidate ran out of memory generating at a batch no larger"
    if (batch, attn) in failed_proofs:
        return "an earlier candidate with this generation batch and attention failed the batch proof"
    return None


def command(recipe: str, prepared: str, n: int) -> list[str]:
    return ["venv/bin/python", "scripts/cuda_preflight_family.py", "--recipe", recipe, "--prepared", prepared,
            "--out", f"cuda-preflight-{n}"]


def skipped(batch: int, failed_generation_batches: list[int]) -> bool:
    """A candidate is skipped when an earlier one ran out of memory while generating at a batch no larger."""
    return any(batch >= failed for failed in failed_generation_batches)


def cap_fields(heartbeat: pathlib.Path, now: dt.datetime) -> dict:
    stop = json.loads(heartbeat.read_text())["governing"]["stop_at_utc"]
    remaining = (dt.datetime.fromisoformat(stop.replace("Z", "+00:00")) - now).total_seconds()
    return {"governing_stop_utc": stop, "cap_remaining_s": remaining}


def token_hygiene() -> None:
    """No token variable and no stored HF login (the library's HF_TOKEN_PATH, else HF_HOME/token, and its stored_tokens:
    download_models_stage1.no_token_left, the one resolver of those paths; verify-K-gated D6)."""
    present = [name for name in TOKEN_ENV_NAMES if os.environ.get(name)]
    if present:
        raise SystemExit(f"a token variable is set: {present}")
    downloads.no_token_left()


def gated_ready(probe: dict, root: pathlib.Path) -> None:
    if any(e["gated"] for e in probe["plan"]):
        receipt = root / "gated-download-receipt.json"
        record = json.loads(receipt.read_text()) if receipt.exists() else {}
        if record.get("ok") is not True:
            raise SystemExit("a gated probe needs gated-download-receipt.json with ok true")
        missing = [name for model in record.get("models", {}).values() for name in model.get("files", {})
                   if not (pathlib.Path(model["snapshot"]) / name).is_file()]
        if missing or not record.get("models"):
            raise SystemExit(f"the gated download's files are not in the HF cache ({len(missing)} missing): "
                             "download again (a stop erases the container disk)")


GUARD_CODE = ("import json,sys;from experiments.safety_selection.config import load_recipe;"
              "from experiments.safety_selection.runner import guard_pin;"
              "print(json.dumps(guard_pin(load_recipe(sys.argv[1])),sort_keys=True))")


def guard_record(recipe: str, env: dict, python: str = "venv/bin/python") -> dict | None:
    """[D17] 4: the engine's guard_pin for the recipe on this pod (the guard pin and its cached snapshot's blob ids; a
    directory listing, nothing loads), in its own process with the preflight's environment, so the Mac compares it
    with the reference's guard record. None when it cannot be read (the Mac's check then refuses)."""
    done = subprocess.run([python, "-c", GUARD_CODE, recipe], env=env, capture_output=True, text=True)
    try:
        record = json.loads(done.stdout.strip().splitlines()[-1]) if done.returncode == 0 and done.stdout.strip() else None
    except ValueError:
        return None
    return record if isinstance(record, dict) else None


def family_check(plan: dict) -> str:
    """The pod's family (kit-family.json) is plan.json's; the plan's one recipe is the family's main config."""
    family = rules.family_or_refuse(plan.get("family"))
    recipes = plan.get("preflight_recipes") or []
    if recipes != [rules.REC]:
        raise SystemExit(f"plan.json names the preflight recipes {recipes}; this {family} pod runs its main config only "
                         f"({rules.REC}; P78:99)")
    return family


def speed_record(family: str, report: dict) -> dict:
    """The M-cap rule's speed factor on this pod (rules_78b.speed_factor, KD3): {s_pod, refused}. A missing field or
    s_pod > 1.15 is a refusal ("none never fits"); the preflight then does not pass and no job starts."""
    cp = report.get("cap_projection") if isinstance(report.get("cap_projection"), dict) else {}
    full = report.get("full_length") if isinstance(report.get("full_length"), dict) else {}
    fields = {"training_s": cp.get("training_s"), "ms_per_step_full": full.get("ms_per_step_full"),
              "untuned_projected_s": cp.get("untuned_projected_s")}
    try:
        return {"s_pod": r78.speed_factor(family, fields), "refused": None, "limit": r78.SPEED_REFUSAL}
    except r78.Refused as exc:
        return {"s_pod": None, "refused": str(exc), "limit": r78.SPEED_REFUSAL}


def main(argv=None) -> int:
    dry = "--dry-run" in (argv if argv is not None else sys.argv[1:])
    root = pathlib.Path.cwd() if dry else ROOT
    os.chdir(root)
    plan = json.loads(pathlib.Path("plan.json").read_text())
    if dry:
        print(json.dumps([command(r, plan["preflight_prepared"], n) for n, r in enumerate(plan["preflight_recipes"], 1)], indent=1))
        return 0
    token_hygiene()
    family = family_check(plan)
    assert json.loads(pathlib.Path("BOOTSTRAP-READY.json").read_text())["ok"] is True, "bootstrap not ready"
    assert not pathlib.Path("PREFLIGHT-DONE.json").exists(), "preflight already done"
    gated_ready(json.loads(pathlib.Path("probe.json").read_text()), root)
    env = {k: v for k, v in os.environ.items() if k not in TOKEN_ENV_NAMES}
    env.update({"CUBLAS_WORKSPACE_CONFIG": ":4096:8", "CUDA_VISIBLE_DEVICES": "0", "TOKENIZERS_PARALLELISM": "false",
                "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "PYTHONPATH": str(root), "HF_HUB_OFFLINE": "1"})
    tried, chosen, failed_batches, failed_proofs, tokenizer_failed = [], None, [], [], False
    for n, recipe in enumerate(plan["preflight_recipes"], 1):
        batch, attn = generation_batch(recipe, root), attention(recipe, root)
        reason = skip_reason(batch, attn, failed_batches, failed_proofs, tokenizer_failed)
        if reason:
            tried.append({"recipe": recipe, "skipped": reason})
            continue
        out = f"cuda-preflight-{n}"
        r = subprocess.run(["python3", "process_receipt.py", "--out", f"preflight-process-{n}", "--",
                            *command(recipe, plan["preflight_prepared"], n)], env=env)
        v = pathlib.Path(out, "verification.json")
        report = json.loads(v.read_text()) if v.exists() else {}
        verdict = report.get("verdict", {})
        if verdict.get("generation_memory_ok") is False:
            failed_batches.append(batch)
        if verdict.get("batch_proof_ok") is False:
            failed_proofs.append((batch, attn))
        if verdict.get("tokenizer_ok") is False:
            tokenizer_failed = True
        tried.append({"recipe": recipe, "exit": r.returncode, "folder": out, "verdict": verdict,
                      "verification_sha256": hashlib.sha256(v.read_bytes()).hexdigest() if v.exists() else None})
        if r.returncode == 0 and verdict.get("use_this_recipe") is True:
            chosen = {**tried[-1], "full_length": report.get("full_length", {}),
                      "cap_projection": dict(report.get("cap_projection") or {}),
                      "bank": runner.bank_from_verification(report), "speed": speed_record(family, report)}
            break
    speed = chosen["speed"] if chosen else {"s_pod": None, "refused": "no candidate passed", "limit": r78.SPEED_REFUSAL}
    done = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "ok": chosen is not None and speed["refused"] is None,
            "family": family,
            "recipe": chosen["recipe"] if chosen else None, "folder": chosen["folder"] if chosen else None,
            "verification_sha256": chosen["verification_sha256"] if chosen else None,
            "init_equals_untuned": chosen["verdict"].get("init_equals_untuned") if chosen else None,
            "ms_per_step_full": chosen["full_length"].get("ms_per_step_full") if chosen else None,
            "projected_job_upper_s": chosen["cap_projection"].get("projected_job_upper_s") if chosen else None,
            "training_s": chosen["cap_projection"].get("training_s") if chosen else None,
            "overhead_s": chosen["cap_projection"].get("overhead_s") if chosen else None,
            "generation_batch": generation_batch(chosen["recipe"], root) if chosen else None, "tried": tried,
            "cap_projection": chosen["cap_projection"] if chosen else None,
            "guard": guard_record(chosen["recipe"], env) if chosen else None,
            "bank": chosen["bank"] if chosen else None, "speed": speed}
    if HEARTBEAT.exists():
        done.update(cap_fields(HEARTBEAT, dt.datetime.now(dt.timezone.utc)))
    pathlib.Path("PREFLIGHT-DONE.json").write_text(json.dumps(done, indent=2) + "\n")
    print(json.dumps({k: done[k] for k in ("ok", "recipe", "init_equals_untuned", "projected_job_upper_s", "speed")}),
          flush=True)
    return 0 if done["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
