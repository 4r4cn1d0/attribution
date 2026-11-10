"""Run the family preflight on this host and record the recipe it supports (runs on the pod; brief Item 4.7).

    venv/bin/python preflight_probe.py [--dry-run]

As preflight_kt.py, plus: a gated probe refuses to start unless gated-download-receipt.json says ok and every
gated file it lists is present in its HF cache snapshot (the container disk is erased on a stop; review fix 7); no
token variable or token file may exist; the skip rules (``skip_reason``): after a candidate records
generation_memory_ok false, every later candidate whose generation batch is at least as large is skipped; after
batch_proof_ok false, every later candidate with the same generation batch and attention (review fixes 2 and 15);
after tokenizer_ok false, every later candidate (the tokenizer does not change along the ladder). PREFLIGHT-DONE.json
also carries init_equals_untuned, ms_per_step_full, projected_job_upper_s, overhead_s and, from the pod timer's
heartbeat, governing_stop_utc and cap_remaining_s. --dry-run prints the candidate commands from plan.json in the
current folder and writes nothing. The OLMo 3 kit: the preflight script is probe.json's ``preflight_script``
(scripts/cuda_preflight_olmo3.py for OLMo 3, blocker B3; the family preflight when the field is absent).
"""
import datetime as dt, hashlib, json, os, pathlib, subprocess, sys

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


DEFAULT_PREFLIGHT = "cuda_preflight_family.py"


def preflight_script(probe: dict) -> str:
    """probe.json's preflight script (a plain file name under scripts/); the family preflight by default."""
    name = probe.get("preflight_script") or DEFAULT_PREFLIGHT
    if "/" in name or not name.endswith(".py"):
        raise SystemExit(f"probe.json names a preflight script that is not a plain scripts/ file name: {name!r}")
    return name


def command(recipe: str, prepared: str, n: int, script: str = DEFAULT_PREFLIGHT) -> list[str]:
    return ["venv/bin/python", f"scripts/{script}", "--recipe", recipe, "--prepared", prepared,
            "--out", f"cuda-preflight-{n}"]


def skipped(batch: int, failed_generation_batches: list[int]) -> bool:
    """A candidate is skipped when an earlier one ran out of memory while generating at a batch no larger."""
    return any(batch >= failed for failed in failed_generation_batches)


def cap_fields(heartbeat: pathlib.Path, now: dt.datetime) -> dict:
    stop = json.loads(heartbeat.read_text())["governing"]["stop_at_utc"]
    remaining = (dt.datetime.fromisoformat(stop.replace("Z", "+00:00")) - now).total_seconds()
    return {"governing_stop_utc": stop, "cap_remaining_s": remaining}


def token_hygiene() -> None:
    present = [name for name in TOKEN_ENV_NAMES if os.environ.get(name)]
    if present:
        raise SystemExit(f"a token variable is set: {present}")
    if (pathlib.Path.home() / ".cache" / "huggingface" / "token").exists():
        raise SystemExit("~/.cache/huggingface/token exists")


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


def main(argv=None) -> int:
    dry = "--dry-run" in (argv if argv is not None else sys.argv[1:])
    root = pathlib.Path.cwd() if dry else ROOT
    os.chdir(root)
    plan = json.loads(pathlib.Path("plan.json").read_text())
    probe = json.loads(pathlib.Path("probe.json").read_text()) if pathlib.Path("probe.json").exists() else {}
    script = preflight_script(probe)
    if dry:
        print(json.dumps([command(r, plan["preflight_prepared"], n, script) for n, r in enumerate(plan["preflight_recipes"], 1)], indent=1))
        return 0
    token_hygiene()
    assert json.loads(pathlib.Path("BOOTSTRAP-READY.json").read_text())["ok"] is True, "bootstrap not ready"
    assert not pathlib.Path("PREFLIGHT-DONE.json").exists(), "preflight already done"
    assert pathlib.Path("scripts", script).is_file(), f"scripts/{script} is not in the bundle"
    gated_ready(probe, root)
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
                            *command(recipe, plan["preflight_prepared"], n, script)], env=env)
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
            chosen = {**tried[-1], "full_length": report.get("full_length", {}), "cap_projection": report.get("cap_projection", {})}
            break
    done = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "ok": chosen is not None,
            "recipe": chosen["recipe"] if chosen else None, "folder": chosen["folder"] if chosen else None,
            "verification_sha256": chosen["verification_sha256"] if chosen else None,
            "init_equals_untuned": chosen["verdict"].get("init_equals_untuned") if chosen else None,
            "ms_per_step_full": chosen["full_length"].get("ms_per_step_full") if chosen else None,
            "projected_job_upper_s": chosen["cap_projection"].get("projected_job_upper_s") if chosen else None,
            "training_s": chosen["cap_projection"].get("training_s") if chosen else None,
            "overhead_s": chosen["cap_projection"].get("overhead_s") if chosen else None,
            "generation_batch": generation_batch(chosen["recipe"], root) if chosen else None, "preflight_script": script,
            "tried": tried}
    if HEARTBEAT.exists():
        done.update(cap_fields(HEARTBEAT, dt.datetime.now(dt.timezone.utc)))
    pathlib.Path("PREFLIGHT-DONE.json").write_text(json.dumps(done, indent=2) + "\n")
    print(json.dumps({k: done[k] for k in ("ok", "recipe", "init_equals_untuned", "projected_job_upper_s")}), flush=True)
    return 0 if done["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
