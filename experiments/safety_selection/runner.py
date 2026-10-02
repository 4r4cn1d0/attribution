"""Jobs: run-one, eval-state, attributes, score-groups, score-audit and calibrate.

Every job validates its schema, identities (prepared manifest, recipe, optional code hash) and
access (role, split, seed namespace, prompt bank) before any model loads; frozen confirmation
jobs (selector and reference roles, held-out guard features) must pin the code hash. Each job
writes exactly one new folder; records every stage in the durable ledger; and writes
COMPLETE.json only after all of its checks. A failure writes error.txt and is preserved, never
completed or overwritten. Numerical failures (non-finite logits, losses, gradients or scores)
are failures, never safe, empty, capped or zero observations.

Dependencies. A job that uses earlier folders (a continuation's ``resume_from``, an
eval-state's ``source_run``, an attributes job's a0 states) first verifies each one's own files
AND its whole dependency chain, then writes ``dependencies.json`` with one receipt per
dependency (see verify.py) before any work, and re-checks the used state.json against its
receipt when loading. Attribution also requires, before any model work, that every a0 state
was trained by the running code (the training implementation its gradients assume; no
cross-code checkpoint mixing) and is exactly the planned a0 checkpoint: name, seed, split,
stream, step, examples, AdamW step and hyperparameters; its receipts and the fingerprints and
optimizer step it used are persisted.

run-one trains one (split, arm, seed) trajectory from the seeded adapter, or continues it from
the verified state saved by a complete earlier run of the same trajectory (identical data,
recipe and code; adapter, AdamW moments and steps, RNG and stream position restored and
fingerprint-checked), through every configured checkpoint up to its target, saving each
state; then optionally evaluates the target on the bank its role allows. Every evaluation
(run-one and eval-state) also measures the forward-only query loss
(``engine.QUERY_LOSS_DEFINITION``) on the supplied reference query rows, in its own charged
stage; it needs no hidden bank.

Costs. Ledger stages time their own work only. ``trajectory_cost`` (and
``incremental_train_cost``) sum the TRAIN stages of a trajectory: seconds and counters of the
optimizer steps, nothing else. Model loading, tokenization, the memory preflight, state saving,
evaluation, verification, completion hashing and everything outside the job (process start,
data copies) are not in it, and no stage sum is the total cost of a purchased operation.
Stage B times each operation outside the engine call and writes immutable external receipts,
charging session setup and failed attempts separately; the cloud supervisor records billable
process time. The engine needs no extra hook for that.

Model access is injected (``Loaders``): the pinned CUDA assets in real use, ENGINEERING
FIXTURES in tests. A ``Session`` keeps loaded assets for consecutive jobs of one recipe in one
process (``calibrate``); the run that loads an asset records the load stage, later runs record
the reuse.
"""

from __future__ import annotations

import contextlib
import json
import math
import platform
import random
import sys
import traceback
from pathlib import Path
from statistics import fmean
from typing import Sequence

import torch

from . import engine as en
from .attribution import (ADAM, DEFINITIONS, GRADSIM, SIGN, adam_inverse_preconditioner,
                          aggregate_groups, checkpoint_scores)
from .common import (append_jsonl, canonical_json, code_identity, derive_seed, ids_sha256,
                     jsonl_bytes, read_json, sha256_bytes, sha256_file, write_atomic, write_json)
from .config import (INIT, checkpoint_names, checkpoint_table, config_sha256, seed_namespace,
                     training_identity, validate_recipe)
from .jobs import (AccessError, JobError, check_attribution_access, check_identities,
                   check_run_access, claim_trajectory, require_code_pin, score_groups_role,
                   trajectory_key, validate_job)
from .ledger import RunLedger, create_run_dir, read_complete, verify_files, write_complete
from .loaders import Loaders, Policy, Toxicity
from .prepare import Prepared, load_prepared, read_manifest
from .scoring import (LABEL_SCORE_DEFINITION, GuardScorer, generation_summary, label_score_summary,
                      utility_summary)
from .sources import DataError
from .stream import StreamPlan, make_plan, micro_batches
from .textproc import (GUARD_LABEL_SEQUENCES, QWEN_DEFAULT_SYSTEM, TemplateError, TrainExample,
                       encode_generation_prompt, encode_mc, encode_train, extract_user_message,
                       repeated_ngram_fraction)
from .verify import (DEPENDENCIES, STEPS, chain_problems, check_trajectory, dependency_receipt,
                     trajectory_steps)

__all__ = ["RunError", "Session", "run_one", "eval_state", "attributes", "score_groups",
           "score_audit", "calibrate", "evaluate_checkpoint", "AUDIT_FIELDS", "UNIT_KEYS"]

PROGRESS_EVERY = 50
AUDIT_FIELDS = frozenset({"audit_id", "completion", "label_prompt_copy", "label_refusal",
                          "label_toxic", "notes", "prompt", "prompt_format", "prompt_truncated"})
COST_KEYS = ("train_seconds", "steps", "examples", "input_tokens", "target_tokens", "padded_tokens")
IDENTITY_KEYS = ("manifest_sha256", "data_config_sha256", "recipe_sha256", "training_identity",
                 "code_sha256")
# The stored job fields that define one calibration unit's science (wall limits do not).
UNIT_KEYS = ("kind", "manifest_sha256", "recipe_sha256", "code_sha256", "split", "arm", "seed",
             "role", "target_checkpoint", "evaluate_bank", "replicate_of")
LABEL_RECORD_KEYS = ("valid", "reason", "control_strings", "guard_input_tokens", "loglik",
                     "normalized", "token_logprobs")


class RunError(RuntimeError):
    """An invariant broke during a job (the folder is preserved as a failure)."""


class Session:
    """Loaded assets for consecutive jobs of ONE recipe in one process."""

    def __init__(self, recipe: dict, loaders: Loaders) -> None:
        self.recipe = validate_recipe(recipe)
        self.recipe_sha256 = config_sha256(recipe)
        self.loaders = loaders
        self.device = loaders.prepare_device(recipe)
        self.sync, self.memory = loaders.hooks(self.device)
        self.environment = loaders.environment(self.device)
        self.loaded_in: dict[str, str] = {}
        self._policy: Policy | None = None
        self._guard: GuardScorer | None = None
        self._toxicity: Toxicity | None = None
        self._corpus: tuple[tuple, dict[str, TrainExample]] | None = None
        self._preflight: str | None = None

    def _reuse(self, ledger: RunLedger, asset: str) -> None:
        ledger.record("asset_reuse", asset=asset, loaded_in=self.loaded_in[asset])

    def policy(self, ledger: RunLedger, run_dir: Path) -> Policy:
        if self._policy is None:
            self._policy = self.loaders.policy(self.recipe, ledger)
            self.loaded_in["policy"] = str(run_dir)
        else:
            self._reuse(ledger, "policy")
        return self._policy

    def guard(self, ledger: RunLedger, run_dir: Path) -> GuardScorer:
        if self._guard is None:
            self._guard = self.loaders.guard(self.recipe, ledger, self.device)
            self.loaded_in["guard"] = str(run_dir)
        else:
            self._reuse(ledger, "guard")
        return self._guard

    def toxicity(self, ledger: RunLedger, run_dir: Path) -> Toxicity | None:
        if self.recipe["secondary_toxicity"] is None:
            return None
        if self._toxicity is None:
            self._toxicity = self.loaders.toxicity(self.recipe, ledger)
            self.loaded_in["toxicity"] = str(run_dir)
        else:
            self._reuse(ledger, "toxicity")
        return self._toxicity

    def corpus(self, prepared: Prepared, policy: Policy, ledger: RunLedger) -> dict[str, TrainExample]:
        """Every training row encoded without truncation and checked token-for-token against
        the prepared audit (a different tokenizer or limit refuses); cached per manifest."""
        key = (prepared.manifest_sha256, self.recipe["model"]["max_train_tokens"])
        if self._corpus is not None and self._corpus[0] == key:
            ledger.record("tokenization", cached=True, rows=len(self._corpus[1]))
            return self._corpus[1]
        with ledger.stage("tokenize", rows=len(prepared.train_rows)) as info:
            out = {rid: _verified_example(policy.codec, rid, row, self.recipe)
                   for rid, row in sorted(prepared.train_rows.items())}
            info.update(tokens=sum(len(e.input_ids) for e in out.values()),
                        max_tokens=max(len(e.input_ids) for e in out.values()))
        ledger.record("tokenization", cached=False, rows=len(out))
        self._corpus = (key, out)
        return out

    def memory_preflight(self, corpus: dict[str, TrainExample], policy: Policy, ledger: RunLedger,
                         run_dir: Path) -> None:
        """Once per session, before any trajectory work: one forward/backward over the
        ``micro_batch`` longest training examples (the worst padded micro-batch), with no
        optimizer step and gradients cleared, so memory failures surface first. Weights are
        checked unchanged; training draws no random numbers; a non-finite loss raises."""
        if self._preflight is not None:
            ledger.record("memory_preflight", done_in=self._preflight)
            return
        train = self.recipe["train"]
        longest = sorted(corpus.values(), key=lambda e: (-len(e.input_ids), e.row_id))[:train["micro_batch"]]
        before = en.lora_fingerprint(policy.named)
        with ledger.stage("memory_preflight", examples=len(longest),
                          max_tokens=len(longest[0].input_ids)) as info:
            policy.model.train()
            policy.model.zero_grad(set_to_none=True)
            losses = en.accumulate_gradients(policy.model, longest, train["micro_batch"],
                                             policy.codec.pad_id, policy.device,
                                             train["lm_head_chunk_tokens"])
            policy.model.zero_grad(set_to_none=True)
            if not all(map(math.isfinite, losses)):
                raise en.NonFiniteError(f"non-finite memory-preflight losses {losses}")
            if en.lora_fingerprint(policy.named) != before:
                raise RunError("the memory preflight changed the adapter")
            info.update(mean_loss=fmean(losses))
        self._preflight = str(run_dir)


def _verified_example(codec, row_id: str, row: dict, recipe: dict) -> TrainExample:
    ex = encode_train(codec, row_id, row["prompt"], row["response"], recipe["model"]["max_train_tokens"])
    if (ex.n_prompt, ex.n_target, ids_sha256(ex.input_ids)) != (
            row["prompt_tokens"], row["target_tokens"], row["token_sha256"]):
        raise DataError(f"{row_id} encodes differently from the prepared token audit")
    return ex


def _identity(manifest: dict, manifest_sha256: str, recipe: dict, code: dict) -> dict:
    return {"manifest_sha256": manifest_sha256, "data_config_sha256": manifest["data_config_sha256"],
            "recipe_sha256": config_sha256(recipe), "training_identity": training_identity(recipe),
            "code_sha256": code["sha256"], "code_files": code["files"], "recipe": recipe,
            "python": sys.version, "platform": platform.platform()}


def _short(identity: dict) -> dict:
    return {k: identity[k] for k in IDENTITY_KEYS}


def _fail(run_dir: Path, ledger: RunLedger | None, exc: BaseException) -> None:
    write_atomic(run_dir / "error.txt", traceback.format_exc().encode("utf-8"))
    if ledger is not None:
        with contextlib.suppress(Exception):
            ledger.status("failed", error=f"{type(exc).__name__}: {exc}")


def _start(run_dir: Path, job: dict, identity: dict, session: Session,
           dependencies: list[dict]) -> RunLedger:
    write_json(run_dir / "job.json", job)
    write_json(run_dir / "identity.json", identity)
    write_json(run_dir / DEPENDENCIES, {"dependencies": dependencies})
    ledger = RunLedger(run_dir, sync=session.sync, memory=session.memory,
                       wall_limit_s=job.get("wall_limit_seconds"))
    ledger.status("running", stage="start")
    return ledger


def _finish(run_dir: Path, ledger: RunLedger, kind: str, identity: dict, result: dict) -> dict:
    marker = write_complete(run_dir, {"kind": kind, "identity": _short(identity),
                                      "job_sha256": sha256_file(run_dir / "job.json"), **result})
    ledger.status("complete")
    return {"run_dir": str(run_dir), "complete": True, "kind": kind,
            "files": len(marker["files"]), **result}


def _seed_global_rng(seed: int) -> None:
    """Fresh trajectories start from RNG states defined by their seed (training itself draws
    no random numbers: dropout is 0 and the data order uses its own named streams)."""
    torch.manual_seed(derive_seed(seed, "torch-global"))
    random.seed(derive_seed(seed, "python-global"))


def _zero_cost() -> dict:
    return {key: 0.0 if key == "train_seconds" else 0 for key in COST_KEYS}


def _complete_source(folder: Path, what: str) -> tuple[dict, dict, dict]:
    """job.json, COMPLETE marker and identity.json of a source folder whose own files AND whole
    dependency chain verify, and whose marker identity equals its hashed identity.json."""
    problems = chain_problems(folder)
    if problems:
        raise JobError(f"{what} {folder} is not a complete run with a verified dependency chain: "
                       f"{problems[:3]}")
    stored, marker, ident = read_json(folder / "job.json"), read_complete(folder), read_json(folder / "identity.json")
    if marker.get("identity") != _short(ident):
        raise JobError(f"{what} {folder}: the COMPLETE.json identity differs from its hashed identity.json")
    return stored, marker, ident


def _same_state(state_dir: Path, receipt: dict) -> None:
    if sha256_file(state_dir / en.STATE) != receipt["state_sha256"]:
        raise en.StateError(f"{state_dir / en.STATE} changed after its dependency receipt was written")


def _previous(job: dict, recipe: dict, code: dict) -> dict:
    """The verified complete run a continuation starts from (identical trajectory, data,
    recipe and code; an earlier checkpoint), with its receipt."""
    folder = Path(job["resume_from"])
    stored, marker, _ = _complete_source(folder, "resume_from")
    if stored.get("kind") != "run-one":
        raise JobError("resume_from is not a run-one folder")
    for key in ("split", "arm", "seed", "role", "manifest_sha256", "recipe_sha256"):
        if stored[key] != job[key]:
            raise JobError(f"resume_from differs in {key}: stored {stored[key]!r}, job {job[key]!r}")
    if marker["identity"]["code_sha256"] != code["sha256"]:
        raise JobError("the code changed since the stored run; continuation refused")
    names = checkpoint_names(recipe)
    if names.index(stored["target_checkpoint"]) >= names.index(job["target_checkpoint"]):
        raise JobError("a continuation must target a later checkpoint than the stored run")
    state = f"states/{stored['target_checkpoint']}/{en.STATE}"
    if state not in marker["files"]:
        raise JobError(f"{folder} holds no saved {stored['target_checkpoint']} state")
    return {"dir": folder, "checkpoint": stored["target_checkpoint"],
            "state_dir": folder / "states" / stored["target_checkpoint"],
            "receipt": dependency_receipt(folder, "resume_from", stored["target_checkpoint"])}


def run_one(job: dict, *, prepared_dir: str | Path, out_dir: str | Path, session: Session,
            allow_hidden: bool = False, registry: str | Path | None = None) -> dict:
    validate_job(job)
    if job["kind"] != "run-one":
        raise JobError("not a run-one job")
    recipe, code = session.recipe, code_identity()
    manifest, manifest_sha = read_manifest(prepared_dir, job["manifest_sha256"])
    check_identities(job, manifest, manifest_sha, recipe, code)
    if job["target_checkpoint"] not in checkpoint_names(recipe):
        raise JobError(f"unknown checkpoint {job['target_checkpoint']!r}")
    bank = job["evaluate_bank"]
    check_run_access(job["role"], job["split"], job["seed"], bank, manifest["data_config"], allow_hidden)
    require_code_pin(job, job["role"])
    previous = _previous(job, recipe, code) if job["resume_from"] is not None else None
    prepared = load_prepared(prepared_dir, manifest_sha, banks=(bank,) if bank else (),
                             allow_hidden=bank == "hidden")
    removed = prepared.removed_rows(job["split"], job["arm"])
    run_dir = create_run_dir(out_dir)
    identity = _identity(manifest, manifest_sha, recipe, code)
    ledger = None
    try:
        ledger = _start(run_dir, job, identity, session, [previous["receipt"]] if previous else [])
        if registry is not None and previous is None:
            claim_trajectory(registry, trajectory_key(manifest_sha, recipe, job["split"], job["arm"],
                                                      job["seed"], job["role"]),
                             str(run_dir), job["replicate_of"])
        result = _train_and_evaluate(job, prepared, removed, previous, session, ledger, run_dir)
        return _finish(run_dir, ledger, "run-one", identity, result)
    except BaseException as exc:
        _fail(run_dir, ledger, exc)
        raise


def _state_meta(job: dict, name: str, position: dict, plan: StreamPlan, cost: dict,
                init_fingerprint: str) -> dict:
    return {"checkpoint": name, "step": position["step"], "epochs": position["epochs"],
            "examples_seen": position["examples_seen"],
            "completed_epochs": position["completed_epochs"], "stream_sha256": plan.sha256(),
            "seed": job["seed"], "split": job["split"], "arm": job["arm"], "role": job["role"],
            "manifest_sha256": job["manifest_sha256"], "recipe_sha256": job["recipe_sha256"],
            "init_fingerprint": init_fingerprint, "trajectory_cost": dict(cost)}


def _train_and_evaluate(job: dict, prepared: Prepared, removed: list[str], previous: dict | None,
                        session: Session, ledger: RunLedger, run_dir: Path) -> dict:
    recipe, train = session.recipe, session.recipe["train"]
    policy = session.policy(ledger, run_dir)
    write_json(run_dir / "assets.json", {"policy": policy.identity, "environment": session.environment,
                                         "loaded_in": dict(session.loaded_in)})
    corpus = session.corpus(prepared, policy, ledger)
    session.memory_preflight(corpus, policy, ledger, run_dir)
    plan = make_plan(prepared.corpus, removed, job["seed"], train["micro_batch"], train["grad_accum"])
    table = checkpoint_table(recipe)
    positions = {name: plan.checkpoint(fraction) for name, fraction in table}
    steps = [positions[name]["step"] for name, _ in table]
    if any(b <= a for a, b in zip(steps, steps[1:])):
        raise RunError(f"two checkpoints fall on one optimizer step for this arm: {positions}")
    write_json(run_dir / "plan.json", {"stream": plan.identity(), "stream_sha256": plan.sha256(),
                                       "checkpoints": positions})
    names = [name for name, _ in table]
    target = job["target_checkpoint"]
    named, device = policy.named, policy.device
    optimizer = en.make_optimizer(named, train)
    saved: dict[str, dict] = {}
    if previous is None:
        start = INIT
        with ledger.stage("init_state", seed=job["seed"]) as info:
            _seed_global_rng(job["seed"])
            en.load_lora_state(named, en.init_lora_state(named, job["seed"]))
            init_fp = en.lora_fingerprint(named)
            cost = _zero_cost()
            saved[INIT] = en.save_state(run_dir / "states" / INIT, named, optimizer, device,
                                        _state_meta(job, INIT, positions[INIT], plan, cost, init_fp))
            info.update(adapter_fingerprint=init_fp)
        ledger.record("checkpoint", checkpoint=INIT, step=0, adapter_fingerprint=init_fp,
                      init_fingerprint=init_fp)
    else:
        start = previous["checkpoint"]
        with ledger.stage("restore_state", checkpoint=start) as info:
            _same_state(previous["state_dir"], previous["receipt"])
            state = en.load_state(previous["state_dir"], named, optimizer, device)
            if state["stream_sha256"] != plan.sha256() or state["step"] != positions[start]["step"]:
                raise en.StateError("the stored state is not at this stream's checkpoint")
            cost, init_fp = dict(state["trajectory_cost"]), state["init_fingerprint"]
            info.update(step=state["step"], adapter_fingerprint=state["adapter_fingerprint"],
                        optimizer_fingerprint=state["optimizer_fingerprint"])
        ledger.record("restored", checkpoint=start, step=state["step"], from_run=str(previous["dir"]))
    step, incremental = positions[start]["step"], _zero_cost()
    for name in names[names.index(start) + 1:names.index(target) + 1]:
        upto = positions[name]["step"]
        label = f"{names[names.index(name) - 1]}->{name}"
        segment = _train_segment(policy, optimizer, plan, corpus, step + 1, upto, label, train,
                                 ledger, run_dir)
        for key in COST_KEYS:
            cost[key] += segment[key]
            incremental[key] += segment[key]
        step = upto
        saved[name] = en.save_state(run_dir / "states" / name, named, optimizer, device,
                                    _state_meta(job, name, positions[name], plan, cost, init_fp))
        ledger.record("checkpoint", checkpoint=name, step=upto,
                      examples_seen=positions[name]["examples_seen"],
                      adapter_fingerprint=saved[name]["adapter_fingerprint"],
                      optimizer_fingerprint=saved[name]["optimizer_fingerprint"],
                      init_fingerprint=init_fp, trajectory_cost=dict(cost))
    evaluation = None
    if job["evaluate_bank"] is not None:
        queries, query_sha = _query_examples(policy, prepared, recipe)
        evaluation = evaluate_checkpoint(session, policy, optimizer,
                                         prepared.banks[job["evaluate_bank"]], queries, query_sha,
                                         ledger, run_dir / "eval" / target, run_dir, target)
    with ledger.stage("verify_trajectory") as info:
        problems = check_trajectory(trajectory_steps(run_dir), plan, positions[target]["step"])
        if problems:
            raise RunError(f"trained stream differs from the frozen plan: {problems[:3]}")
        info.update(steps_verified=positions[target]["step"])
    return {"trajectory": {"split": job["split"], "arm": job["arm"], "seed": job["seed"],
                           "role": job["role"], "stream_sha256": plan.sha256(),
                           "retained_rows": plan.retained, "removed_rows": len(plan.removed),
                           "steps_per_epoch": plan.steps_per_epoch, "init_fingerprint": init_fp},
            "target_checkpoint": target,
            "checkpoints": {name: {"step": s["step"], "examples_seen": s["examples_seen"],
                                   "adapter_fingerprint": s["adapter_fingerprint"],
                                   "optimizer_fingerprint": s["optimizer_fingerprint"],
                                   "trajectory_cost": s["trajectory_cost"]}
                            for name, s in saved.items()},
            "incremental_train_cost": incremental, "trajectory_cost": cost,
            "cost_scope": "train stages only; not the total cost of this operation",
            "evaluation": evaluation,
            "resumed_from": str(previous["dir"]) if previous else None,
            "resumed_from_complete_sha256": previous["receipt"]["complete_sha256"] if previous else None}


def _train_segment(policy: Policy, optimizer, plan: StreamPlan, corpus: dict[str, TrainExample],
                   first: int, last: int, label: str, train: dict, ledger: RunLedger,
                   run_dir: Path) -> dict:
    counts = _zero_cost()
    recent: list[float] = []
    with ledger.stage("train", segment=label, first_step=first, last_step=last) as info:
        for step, epoch, rows in plan.iterate(first, last):
            ledger.check(f"train step {step}")
            if not rows or any(r in plan.removed for r in rows):
                raise RunError(f"step {step}: empty batch or a removed row reached the sampler")
            examples = [corpus[r] for r in rows]
            started = ledger.elapsed()
            out = en.train_step(policy.model, policy.named, optimizer, examples, train["micro_batch"],
                                train["max_grad_norm"], policy.codec.pad_id, policy.device,
                                train["lm_head_chunk_tokens"])
            padded = sum(len(mb) * max(len(e.input_ids) for e in mb)
                         for mb in micro_batches(examples, train["micro_batch"]))
            inputs, targets = sum(len(e.input_ids) for e in examples), sum(e.n_target for e in examples)
            append_jsonl(run_dir / STEPS, {
                "step": step, "epoch": epoch, "rows": rows, "examples": len(rows),
                "input_tokens": inputs, "target_tokens": targets, "padded_tokens": padded,
                "loss": out["loss"], "example_losses": out["example_losses"],
                "grad_norm_preclip": out["grad_norm_preclip"],
                "seconds": ledger.elapsed() - started})
            counts["steps"] += 1
            counts["examples"] += len(rows)
            counts["input_tokens"] += inputs
            counts["target_tokens"] += targets
            counts["padded_tokens"] += padded
            info.update({key: counts[key] for key in COST_KEYS if key != "train_seconds"})
            recent.append(out["loss"])
            if step % PROGRESS_EVERY == 0 or step == last:
                ledger.progress("train", segment=label, step=step, epoch=epoch,
                                examples_seen=plan.examples_seen(step), mean_recent_loss=fmean(recent))
                recent = []
    counts["train_seconds"] = info["seconds"]
    return counts


def _training_state(policy: Policy, optimizer) -> tuple:
    return (en.lora_fingerprint(policy.named),
            en.optimizer_fingerprint(optimizer, policy.named) if optimizer is not None else None,
            en.rng_digest(policy.device), policy.model.training)


def _prompt_ids(codec, item: dict, max_tokens: int) -> list[int]:
    ids = encode_generation_prompt(codec, item["prompt"], max_tokens)
    if ids_sha256(ids) != item["token_sha256"]:
        raise DataError(f"{item['prompt_id']} encodes differently from the prepared token audit")
    return ids


def _query_bank_sha256(prepared: Prepared) -> str:
    return sha256_bytes(canonical_json([[q["query_id"], q["token_sha256"]] for q in prepared.query_rows]))


def _query_examples(policy: Policy, prepared: Prepared, recipe: dict) -> tuple[list[TrainExample], str]:
    """The supplied reference query rows, encoded exactly as training rows (audit-checked)."""
    return ([_verified_example(policy.codec, q["query_id"], q, recipe) for q in prepared.query_rows],
            _query_bank_sha256(prepared))


def _forced_choice(policy: Policy, items: list[dict], recipe: dict, ledger: RunLedger,
                   checkpoint: str) -> tuple[list[dict], int]:
    """ARC-Easy forced choice: for each candidate label, the summed log-probability of the
    label's tokens alone (no end-of-turn) after the canonical prompt; predicted labels are the
    argmax set (ties kept)."""
    max_prompt = recipe["model"]["max_prompt_tokens"]
    sequences, n_targets, spans = [], [], []
    for item in items:
        prompt, targets = encode_mc(policy.codec, item["question"], item["labels"], item["texts"], max_prompt)
        if ids_sha256(prompt) != item["token_sha256"]:
            raise DataError(f"{item['prompt_id']} encodes differently from the prepared token audit")
        spans.append((len(sequences), prompt, targets))
        for target in targets:
            sequences.append(prompt + target)
            n_targets.append(len(target))
    logprobs = en.target_logprobs(policy.model, sequences, n_targets, pad_id=policy.codec.pad_id,
                                  device=policy.device, batch_size=recipe["arc"]["batch_size"],
                                  chunk=recipe["train"]["lm_head_chunk_tokens"],
                                  check=lambda what: ledger.check(f"arc {checkpoint} {what}"))
    records = []
    for item, (start, prompt, targets) in zip(items, spans):
        token_logprobs = logprobs[start:start + len(targets)]
        scores = [math.fsum(values) for values in token_logprobs]
        if not all(math.isfinite(s) for s in scores):
            raise en.NonFiniteError(f"{item['prompt_id']}: non-finite label log-probability")
        best = max(scores)
        predicted = [label for label, s in zip(item["labels"], scores) if s == best]
        records.append({"prompt_id": item["prompt_id"], "labels": item["labels"],
                        "label_token_ids": targets, "token_logprobs": token_logprobs,
                        "scores": scores, "predicted": predicted, "tie": len(predicted) > 1,
                        "answer": item["answer"], "correct": predicted == [item["answer"]],
                        "correct_fraction": 1 / len(predicted) if item["answer"] in predicted else 0.0,
                        "prompt_tokens": len(prompt)})
    return records, sum(len(s) for s in sequences)


def evaluate_checkpoint(session: Session, policy: Policy, optimizer, items: list[dict],
                        queries: list[TrainExample], query_bank_sha256: str, ledger: RunLedger,
                        folder: Path, run_dir: Path, checkpoint: str) -> dict:
    """The forward-only query loss, generation (safety and benign ARC prompts), ARC forced
    choice, guard scoring and the optional secondary toxicity score of one checkpoint, each in
    its own charged stage. Weights, optimizer state, RNG states and train/eval mode must be
    identical afterwards (checked; RNG restored)."""
    recipe, codec, device = session.recipe, policy.codec, policy.device
    gen = recipe["generation"]
    folder.mkdir(parents=True)
    before = _training_state(policy, optimizer)
    gen_items = [i for i in items if i["kind"] in ("safety", "arc_generation")]
    mc_items = [i for i in items if i["kind"] == "arc_utility"]
    with en.preserved_rng(device):
        # Loading scorers can draw random numbers (module construction); the baseline for
        # the consumption diagnostic is taken after loading. Everything is restored on exit.
        guard = session.guard(ledger, run_dir)
        toxicity = session.toxicity(ledger, run_dir)
        rng_start = en.rng_digest(device)
        with ledger.stage("query_loss", checkpoint=checkpoint, queries=len(queries)) as info:
            losses = en.query_losses(policy.model, queries, pad_id=codec.pad_id, device=device,
                                     chunk=recipe["train"]["lm_head_chunk_tokens"],
                                     check=lambda what: ledger.check(f"query loss {checkpoint} {what}"))
            info.update(forward_passes=len(queries), input_tokens=sum(len(q.input_ids) for q in queries),
                        target_tokens=sum(q.n_target for q in queries))
        write_atomic(folder / "query_loss.jsonl", jsonl_bytes(
            [{"query_id": q.row_id, "input_tokens": len(q.input_ids), "target_tokens": q.n_target,
              "token_sha256": ids_sha256(q.input_ids), "loss": loss} for q, loss in zip(queries, losses)]))
        query_summary = {"n": len(losses), "mean": fmean(losses), "query_bank_sha256": query_bank_sha256,
                         "forward_passes": len(queries), "seconds": info["seconds"],
                         "definition": en.QUERY_LOSS_DEFINITION}
        prompts = [_prompt_ids(codec, i, recipe["model"]["max_prompt_tokens"]) for i in gen_items]

        def on_batch(b: int, index: list[int], batch: list) -> None:
            ledger.progress("generate", checkpoint=checkpoint, batch=b, rows=len(index),
                            output_tokens=sum(len(g.output_ids) for g in batch),
                            capped=sum(g.stop_reason == en.STOP_CAP for g in batch))

        with ledger.stage("generate", checkpoint=checkpoint, prompts=len(prompts)) as info:
            generations = en.greedy_generate(
                policy.model, prompts, max_new_tokens=gen["max_new_tokens"], stop_ids=codec.stop_ids,
                pad_id=codec.pad_id, device=device, batch_size=gen["batch_size"],
                check=lambda what: ledger.check(f"generate {checkpoint} {what}"), on_batch=on_batch)
            info.update(prompt_tokens=sum(map(len, prompts)),
                        output_tokens=sum(len(g.output_ids) for g in generations),
                        capped=sum(g.stop_reason == en.STOP_CAP for g in generations))
        records = [{"prompt_id": item["prompt_id"], "kind": item["kind"], "prompt_ids": ids,
                    "prompt_tokens": len(ids), "output_ids": list(g.output_ids),
                    "output_tokens": len(g.output_ids), "stop_reason": g.stop_reason,
                    "stop_token": g.stop_token, "empty": not g.output_ids,
                    "text": codec.decode(g.output_ids),
                    "repetition_4gram": repeated_ngram_fraction(g.output_ids, 4)}
                   for item, ids, g in zip(gen_items, prompts, generations, strict=True)]
        write_atomic(folder / "generations.jsonl", jsonl_bytes(records))
        with ledger.stage("arc_utility", checkpoint=checkpoint, questions=len(mc_items)) as info:
            mc_records, mc_tokens = _forced_choice(policy, mc_items, recipe, ledger, checkpoint)
            info.update(sequences=sum(len(r["labels"]) for r in mc_records), tokens=mc_tokens)
        write_atomic(folder / "arc_utility.jsonl", jsonl_bytes(mc_records))
        with ledger.stage("guard", checkpoint=checkpoint, items=len(records)) as info:
            guarded = guard.score([(r["prompt_id"], item["prompt"], r["text"])
                                   for r, item in zip(records, gen_items)],
                                  check=lambda what: ledger.check(f"guard {checkpoint} {what}"))
            info.update(guard_input_tokens=sum(g["guard_input_tokens"] or 0 for g in guarded),
                        guard_output_tokens=sum(g["guard_output_tokens"] or 0 for g in guarded),
                        invalid=sum(not g["valid"] for g in guarded))
        write_atomic(folder / "guard.jsonl", jsonl_bytes(
            [{"prompt_id": r["prompt_id"], "kind": r["kind"], **g} for r, g in zip(records, guarded)]))
        toxicity_summary = None
        if toxicity is not None:
            with ledger.stage("secondary_toxicity", checkpoint=checkpoint, texts=len(records)) as info:
                texts = [r["text"] for r in records]
                scores = _finite_scores(toxicity.score(texts), "secondary toxicity")
                truncated = toxicity.count_truncated(texts)
                info.update(truncated=truncated)
            write_atomic(folder / "toxicity.jsonl", jsonl_bytes(
                [{"prompt_id": r["prompt_id"], "kind": r["kind"], "p": p, "flag": p >= toxicity.threshold}
                 for r, p in zip(records, scores, strict=True)]))
            toxicity_summary = {"truncated": truncated, **{
                kind: {"n": sum(r["kind"] == kind for r in records),
                       "flagged": sum(p >= toxicity.threshold for r, p in zip(records, scores) if r["kind"] == kind)}
                for kind in ("safety", "arc_generation")}}
        rng_consumed = en.rng_digest(device) != rng_start
    if _training_state(policy, optimizer) != before:
        raise RunError("evaluation changed the adapter, optimizer state, RNG state or mode")
    joined = [{**r, "guard": g} for r, g in zip(records, guarded)]
    summary = {"checkpoint": checkpoint, "query_loss": query_summary,
               "safety": generation_summary([j for j in joined if j["kind"] == "safety"]),
               "arc_generation": generation_summary([j for j in joined if j["kind"] == "arc_generation"]),
               "arc_utility": utility_summary(mc_records), "secondary_toxicity": toxicity_summary,
               "rng_consumed_inside_evaluation_then_restored": rng_consumed,
               "generation": {"max_new_tokens": gen["max_new_tokens"], "batch_size": gen["batch_size"]}}
    write_json(folder / "summary.json", summary)
    ledger.record("evaluation", **summary)
    return summary


def _finite_scores(values: Sequence[float], what: str) -> list[float]:
    values = [float(v) for v in values]
    if not all(math.isfinite(v) for v in values):
        raise en.NonFiniteError(f"non-finite {what} score: a numerical failure, never an observation")
    return values


def eval_state(job: dict, *, prepared_dir: str | Path, out_dir: str | Path, session: Session,
               allow_hidden: bool = False) -> dict:
    """Evaluate a saved state of a complete run-one folder under this recipe, whose training
    identity (model and train sections) must equal the run's; evaluation settings may differ
    (e.g. a separately frozen longer generation ceiling). Nothing is trained."""
    validate_job(job)
    if job["kind"] != "eval-state":
        raise JobError("not an eval-state job")
    recipe, code = session.recipe, code_identity()
    manifest, manifest_sha = read_manifest(prepared_dir, job["manifest_sha256"])
    check_identities(job, manifest, manifest_sha, recipe, code)
    source = Path(job["source_run"])
    stored, marker, _ = _complete_source(source, "source_run")
    if stored.get("kind") != "run-one" or stored["manifest_sha256"] != manifest_sha:
        raise JobError("source_run is not a run-one folder of these prepared data")
    if marker["identity"]["training_identity"] != training_identity(recipe):
        raise JobError("eval-state may change evaluation settings only, not model/train")
    if f"states/{job['checkpoint']}/{en.STATE}" not in marker["files"]:
        raise JobError(f"source_run holds no saved {job['checkpoint']} state")
    bank = job["evaluate_bank"]
    if bank is None:
        raise JobError("eval-state needs an evaluate_bank")
    check_run_access(stored["role"], stored["split"], stored["seed"], bank, manifest["data_config"],
                     allow_hidden)
    require_code_pin(job, stored["role"])
    receipt = dependency_receipt(source, "source_run", job["checkpoint"])
    prepared = load_prepared(prepared_dir, manifest_sha, banks=(bank,), allow_hidden=bank == "hidden")
    run_dir = create_run_dir(out_dir)
    identity = _identity(manifest, manifest_sha, recipe, code)
    ledger = None
    try:
        ledger = _start(run_dir, job, identity, session, [receipt])
        policy = session.policy(ledger, run_dir)
        write_json(run_dir / "assets.json", {"policy": policy.identity, "environment": session.environment,
                                             "loaded_in": dict(session.loaded_in)})
        state_dir = source / "states" / job["checkpoint"]
        with ledger.stage("restore_state", checkpoint=job["checkpoint"]) as info:
            _same_state(state_dir, receipt)
            state = en.load_state(state_dir, policy.named, None, policy.device)
            info.update(step=state["step"], adapter_fingerprint=state["adapter_fingerprint"])
        queries, query_sha = _query_examples(policy, prepared, recipe)
        evaluation = evaluate_checkpoint(session, policy, None, prepared.banks[bank], queries, query_sha,
                                         ledger, run_dir / "eval" / job["checkpoint"], run_dir,
                                         job["checkpoint"])
        result = {"source_run": str(source), "source_code_sha256": marker["identity"]["code_sha256"],
                  "source_recipe_sha256": marker["identity"]["recipe_sha256"],
                  "source_complete_sha256": receipt["complete_sha256"],
                  "source_state_sha256": receipt["state_sha256"],
                  "checkpoint": job["checkpoint"], "step": state["step"],
                  "adapter_fingerprint": state["adapter_fingerprint"], "evaluation": evaluation,
                  "trajectory": {k: stored[k] for k in ("split", "arm", "seed", "role")}}
        return _finish(run_dir, ledger, "eval-state", identity, result)
    except BaseException as exc:
        _fail(run_dir, ledger, exc)
        raise


def _a0_source(job: dict, checkpoint: str, folder: Path, plan: StreamPlan, position: dict,
               recipe: dict, code: dict) -> dict:
    """One a0 checkpoint, verified before any model work: complete with its chain, an a0
    run-one of this split/seed/role/data/recipe, trained by the RUNNING code, and exactly the
    planned checkpoint (name, stream, step, examples) with a matching AdamW step and the
    recipe's AdamW hyperparameters. Returns its state, AdamW tensors and receipt."""
    stored, marker, _ = _complete_source(folder, f"a0_states.{checkpoint}")
    if stored.get("kind") != "run-one" or stored["arm"] != "a0":
        raise JobError(f"{folder} is not an a0 run-one folder")
    for key in ("split", "seed", "role", "manifest_sha256", "recipe_sha256"):
        if stored[key] != job[key]:
            raise JobError(f"{folder} differs from the attribution job in {key}")
    if marker["identity"]["code_sha256"] != code["sha256"]:
        raise JobError(f"{folder}: trained by code {marker['identity']['code_sha256']}, not the running "
                       f"code {code['sha256']}; attribution needs the common current training "
                       "implementation (no cross-code checkpoint mixing)")
    if f"states/{checkpoint}/{en.STATE}" not in marker["files"]:
        raise JobError(f"{folder} holds no saved {checkpoint} state")
    state_dir = folder / "states" / checkpoint
    state = read_json(state_dir / en.STATE)
    expected = {"checkpoint": checkpoint, "arm": "a0", "seed": job["seed"], "split": job["split"],
                "role": job["role"], "stream_sha256": plan.sha256(), "step": position["step"],
                "examples_seen": position["examples_seen"]}
    wrong = {key: [state.get(key), value] for key, value in expected.items() if state.get(key) != value}
    if wrong:
        raise JobError(f"{folder}: the saved {checkpoint} state is not the planned a0 checkpoint "
                       f"(stored, planned): {wrong}")
    try:
        _, tensors = en.read_optimizer_tensors(state_dir)
    except en.StateError as exc:
        raise JobError(f"{folder}: {checkpoint} optimizer state does not verify: {exc}") from exc
    steps = sorted({float(t.reshape(-1)[0]) for name, t in tensors.items() if name.startswith("step/")})
    if steps != [float(state["step"])]:
        raise JobError(f"{folder}: AdamW step {steps} differs from the {checkpoint} checkpoint step "
                       f"{state['step']}")
    group0, train = state["param_groups"][0], recipe["train"]
    saved = (float(group0["lr"]), [float(b) for b in group0["betas"]], float(group0["eps"]),
             float(group0["weight_decay"]))
    if saved != (float(train["lr"]), [float(b) for b in train["betas"]], float(train["eps"]),
                 float(train["weight_decay"])):
        raise JobError(f"{folder}: saved AdamW hyperparameters {saved} differ from the recipe")
    return {"run": str(folder), "state_dir": state_dir, "state": state, "tensors": tensors,
            "receipt": dependency_receipt(folder, f"a0_state:{checkpoint}", checkpoint)}


def attributes(job: dict, *, prepared_dir: str | Path, out_dir: str | Path, session: Session) -> dict:
    """Both checkpoint-gradient variants for the named groups of one split on one seed's a0
    trajectory, from the supplied DATE-LM reference query rows only. Every pass is charged;
    the a0 trajectory's own train-stage cost to each checkpoint is recorded separately."""
    validate_job(job)
    if job["kind"] != "attributes":
        raise JobError("not an attributes job")
    recipe, code = session.recipe, code_identity()
    manifest, manifest_sha = read_manifest(prepared_dir, job["manifest_sha256"])
    check_identities(job, manifest, manifest_sha, recipe, code)
    check_attribution_access(job, manifest["data_config"], recipe)
    require_code_pin(job, job["role"])
    prepared = load_prepared(prepared_dir, manifest_sha)
    split_groups = prepared.groups[job["split"]]
    missing = [g for g in job["group_ids"] if g not in split_groups]
    if missing:
        raise JobError(f"not {job['split']} groups: {missing}")
    groups = {gid: split_groups[gid] for gid in job["group_ids"]}
    checkpoints = recipe["attribution"]["checkpoints"]
    train = recipe["train"]
    plan = make_plan(prepared.corpus, [], job["seed"], train["micro_batch"], train["grad_accum"])
    fractions = dict(checkpoint_table(recipe))
    sources = {c: _a0_source(job, c, Path(job["a0_states"][c]), plan, plan.checkpoint(fractions[c]),
                             recipe, code) for c in checkpoints}
    if len({s["state"]["init_fingerprint"] for s in sources.values()}) != 1:
        raise JobError("the a0 states do not share one seeded initial adapter")
    run_dir = create_run_dir(out_dir)
    identity = _identity(manifest, manifest_sha, recipe, code)
    ledger = None
    try:
        ledger = _start(run_dir, job, identity, session, [sources[c]["receipt"] for c in checkpoints])
        policy = session.policy(ledger, run_dir)
        write_json(run_dir / "assets.json", {"policy": policy.identity, "environment": session.environment,
                                             "loaded_in": dict(session.loaded_in)})
        with ledger.stage("tokenize_attribution_rows") as info:
            members = [rid for gid in job["group_ids"] for rid in groups[gid]]
            rows = [_verified_example(policy.codec, rid, prepared.train_rows[rid], recipe) for rid in members]
            queries = [_verified_example(policy.codec, q["query_id"], q, recipe) for q in prepared.query_rows]
            info.update(rows=len(rows), queries=len(queries))
        query_bank_sha256 = _query_bank_sha256(prepared)
        per_checkpoint: dict[str, dict] = {}
        for c in checkpoints:
            src = sources[c]
            with ledger.stage("attribution", checkpoint=c, queries=len(queries), rows=len(rows)) as info:
                _same_state(src["state_dir"], src["receipt"])
                state = en.load_state(src["state_dir"], policy.named, None, policy.device,
                                      restore_rng_state=False)
                group0 = state["param_groups"][0]
                lr, beta2, eps = float(group0["lr"]), float(group0["betas"][1]), float(group0["eps"])
                inverse, step = adam_inverse_preconditioner(src["tensors"], [n for n, _ in policy.named],
                                                            beta2, eps)
                if step != state["step"]:
                    raise RunError(f"AdamW step {step} differs from the checkpoint step {state['step']}")
                before = (en.lora_fingerprint(policy.named), en.rng_digest(policy.device), policy.model.training)
                scores = checkpoint_scores(policy.model, policy.named, queries, rows, inverse=inverse,
                                           lr=lr, pad_id=policy.codec.pad_id, device=policy.device,
                                           chunk=train["lm_head_chunk_tokens"],
                                           check=lambda what, c=c: ledger.check(f"attribution {c} {what}"))
                if (en.lora_fingerprint(policy.named), en.rng_digest(policy.device),
                        policy.model.training) != before:
                    raise RunError("attribution changed the adapter, RNG state or mode")
                for name, digest in state["files"].items():
                    if sha256_file(src["state_dir"] / name) != digest:
                        raise RunError(f"{src['state_dir'] / name} changed during attribution")
                _same_state(src["state_dir"], src["receipt"])
                info.update(gradient_passes=len(queries) + len(rows), optimizer_step=step,
                            tokens=sum(len(e.input_ids) for e in queries + rows))
            per_checkpoint[c] = {"run": src["run"], "step": step, "lr": lr, "beta2": beta2, "eps": eps,
                                 "adapter_fingerprint": state["adapter_fingerprint"],
                                 "optimizer_fingerprint": state["optimizer_fingerprint"],
                                 "a0_trajectory_cost": state["trajectory_cost"],
                                 "attribution_seconds": info["seconds"], **scores}
        aggregates = aggregate_groups(per_checkpoint, groups)
        group_of = {rid: gid for gid in groups for rid in groups[gid]}
        write_atomic(run_dir / "rows.jsonl", jsonl_bytes(
            [{"row_id": rid, "group_id": group_of[rid],
              "per_checkpoint": {c: per_checkpoint[c]["rows"][rid] for c in checkpoints}}
             for rid in members]))
        write_json(run_dir / "groups.json", {"definitions": DEFINITIONS, "sign": SIGN,
                                             "variants": [GRADSIM, ADAM], "groups": aggregates})
        write_json(run_dir / "queries.json", {
            "query_bank": "ref", "query_bank_sha256": query_bank_sha256, "n": len(queries),
            "loss_definition": en.QUERY_LOSS_DEFINITION,
            "per_checkpoint": {c: {**per_checkpoint[c]["query"], "step": per_checkpoint[c]["step"]}
                               for c in checkpoints}})
        sources_out = {c: {"run": sources[c]["run"], "resolved": sources[c]["receipt"]["resolved"],
                           "complete_sha256": sources[c]["receipt"]["complete_sha256"],
                           "state_sha256": sources[c]["receipt"]["state_sha256"],
                           "code_sha256": sources[c]["receipt"]["identity"]["code_sha256"],
                           "stream_sha256": sources[c]["state"]["stream_sha256"],
                           "init_fingerprint": sources[c]["state"]["init_fingerprint"],
                           "adapter_fingerprint": per_checkpoint[c]["adapter_fingerprint"],
                           "optimizer_fingerprint": per_checkpoint[c]["optimizer_fingerprint"],
                           "optimizer_step": per_checkpoint[c]["step"]}
                       for c in checkpoints}
        costs = {"attribution_seconds": {c: per_checkpoint[c]["attribution_seconds"] for c in checkpoints},
                 "gradient_passes": (len(queries) + len(rows)) * len(checkpoints),
                 "a0_trajectory_cost_to_checkpoint": {c: per_checkpoint[c]["a0_trajectory_cost"]
                                                      for c in checkpoints},
                 "cost_scope": "attribution stages and a0 train stages only; not total operation cost"}
        result = {"split": job["split"], "seed": job["seed"], "role": job["role"],
                  "group_ids": job["group_ids"], "checkpoints": checkpoints,
                  "query_bank_sha256": query_bank_sha256,
                  "optimizer_steps": {c: per_checkpoint[c]["step"] for c in checkpoints},
                  "query_loss_from_gradient_passes": {c: per_checkpoint[c]["query"]["mean_loss"]
                                                      for c in checkpoints},
                  "sources": sources_out,
                  "scores": {gid: {GRADSIM: a[GRADSIM], ADAM: a[ADAM]} for gid, a in aggregates.items()},
                  "costs": costs}
        return _finish(run_dir, ledger, "attributes", identity, result)
    except BaseException as exc:
        _fail(run_dir, ledger, exc)
        raise


def score_groups(job: dict, *, prepared_dir: str | Path, out_dir: str | Path, session: Session) -> dict:
    """Guard features of every member row (its prompt and training response) of one split's
    groups, each in its own charged stage: hard labels from the guard's greedy answer, and the
    normalized label-sequence scores (scoring.py). Per-row records and per-group summaries."""
    validate_job(job)
    if job["kind"] != "score-groups":
        raise JobError("not a score-groups job")
    recipe, code = session.recipe, code_identity()
    manifest, manifest_sha = read_manifest(prepared_dir, job["manifest_sha256"])
    check_identities(job, manifest, manifest_sha, recipe, code)
    require_code_pin(job, score_groups_role(job["split"]))
    prepared = load_prepared(prepared_dir, manifest_sha)
    groups = prepared.groups[job["split"]]
    run_dir = create_run_dir(out_dir)
    identity = _identity(manifest, manifest_sha, recipe, code)
    ledger = None
    try:
        ledger = _start(run_dir, job, identity, session, [])
        guard = session.guard(ledger, run_dir)
        order = [(gid, rid) for gid in sorted(groups) for rid in groups[gid]]
        items = [(rid, prepared.train_rows[rid]["prompt"], prepared.train_rows[rid]["response"])
                 for _, rid in order]
        with ledger.stage("guard_training_rows", rows=len(items)) as info:
            records = guard.score(items, check=lambda what: ledger.check(f"guard {what}"))
            info.update(guard_input_tokens=sum(r["guard_input_tokens"] or 0 for r in records),
                        guard_output_tokens=sum(r["guard_output_tokens"] or 0 for r in records),
                        invalid=sum(not r["valid"] for r in records))
        generation_seconds = info["seconds"]
        label_ids = guard.label_token_ids()
        with ledger.stage("guard_label_scores", rows=len(items), labels=len(GUARD_LABEL_SEQUENCES)) as info:
            scored = guard.label_scores(items, check=lambda what: ledger.check(f"guard label scores {what}"))
            valid = [s for s in scored if s["valid"]]
            info.update(sequences=len(GUARD_LABEL_SEQUENCES) * len(valid),
                        input_tokens=sum(len(GUARD_LABEL_SEQUENCES) * s["guard_input_tokens"]
                                         + sum(map(len, label_ids)) for s in valid),
                        unscored=len(scored) - len(valid))
        label_seconds = info["seconds"]
        write_atomic(run_dir / "rows.jsonl", jsonl_bytes(
            [{"row_id": rid, "group_id": gid, **r, "label_scores": {k: s[k] for k in LABEL_RECORD_KEYS}}
             for (gid, rid), r, s in zip(order, records, scored, strict=True)]))
        features = {}
        for gid in sorted(groups):
            mine = [(r, s) for (g, _), r, s in zip(order, records, scored) if g == gid]
            hard = [r for r, _ in mine if r["valid"]]
            features[gid] = {"size": len(mine), "guard_invalid": len(mine) - len(hard),
                             **{f"guard_{label.lower()}": sum(r["safety"] == label for r in hard)
                                for label in ("Unsafe", "Controversial", "Safe")},
                             "guard_refusal_yes": sum(r["refusal"] == "Yes" for r in hard),
                             "guard_refusal_no": sum(r["refusal"] == "No" for r in hard),
                             "label_scores": label_score_summary([s for _, s in mine])}
        write_json(run_dir / "x0_guard.json", {"kind": "selector-facing measured guard features",
                                               "split": job["split"],
                                               "label_sequences": list(GUARD_LABEL_SEQUENCES),
                                               "label_token_ids": label_ids,
                                               "label_score_definition": LABEL_SCORE_DEFINITION,
                                               "groups": features})
        costs = {"guard_generation_seconds": generation_seconds, "guard_label_score_seconds": label_seconds,
                 "label_score_sequences": len(GUARD_LABEL_SEQUENCES) * len(valid),
                 "cost_scope": "guard stages only; not total operation cost"}
        return _finish(run_dir, ledger, "score-groups", identity, {"split": job["split"], "rows": len(items),
                                                                   "groups": len(groups), "costs": costs})
    except BaseException as exc:
        _fail(run_dir, ledger, exc)
        raise


def _audit_rows(data: bytes) -> list[dict]:
    rows = []
    for number, line in enumerate(data.decode("utf-8").split("\n"), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DataError(f"audit line {number}: invalid JSON") from exc
        if not isinstance(row, dict) or set(row) != AUDIT_FIELDS:
            raise DataError(f"audit line {number}: fields differ from the blind-context schema")
        if not (isinstance(row["audit_id"], str) and row["audit_id"]
                and isinstance(row["prompt"], str) and isinstance(row["completion"], str)):
            raise DataError(f"audit line {number}: audit_id/prompt/completion must be strings")
        rows.append(row)
    if len({r["audit_id"] for r in rows}) != len(rows):
        raise DataError("duplicate audit_id")
    return rows


def score_audit(input_path: str | Path, *, out_dir: str | Path, session: Session) -> dict:
    """Scorer-only pass over a blind-context audit file: the user message is recovered from
    the exact stored Qwen2.5 input; output rows are keyed by audit_id and never repeat the
    prompt or completion text; the returned summary holds counts only."""
    data = Path(input_path).read_bytes()
    rows = _audit_rows(data)
    run_dir = create_run_dir(out_dir)
    job = {"kind": "score-audit", "input": str(input_path), "input_sha256": sha256_bytes(data),
           "recipe_sha256": session.recipe_sha256, "wall_limit_seconds": None}
    code = code_identity()
    identity = {"recipe_sha256": session.recipe_sha256, "code_sha256": code["sha256"],
                "code_files": code["files"], "recipe": session.recipe, "manifest_sha256": None,
                "data_config_sha256": None, "training_identity": training_identity(session.recipe),
                "python": sys.version, "platform": platform.platform()}
    ledger = None
    try:
        ledger = _start(run_dir, job, identity, session, [])
        guard = session.guard(ledger, run_dir)
        items, unparsed = [], {}
        for row in rows:
            try:
                user = extract_user_message(row["prompt"], QWEN_DEFAULT_SYSTEM, guard.control_strings)
            except TemplateError as exc:
                unparsed[row["audit_id"]] = str(exc)
                continue
            items.append((row["audit_id"], user, row["completion"]))
        with ledger.stage("guard_audit", items=len(items)) as info:
            records = {r["item_id"]: r for r in guard.score(items, check=lambda what: ledger.check(f"guard {what}"))}
            info.update(invalid=sum(not r["valid"] for r in records.values()), unparsed=len(unparsed))
        toxicity = session.toxicity(ledger, run_dir)
        tox: dict[str, float] = {}
        if toxicity is not None:
            with ledger.stage("secondary_toxicity", texts=len(rows)):
                tox = dict(zip([r["audit_id"] for r in rows],
                               _finite_scores(toxicity.score([r["completion"] for r in rows]),
                                              "secondary toxicity")))
        out = []
        for row in rows:
            aid = row["audit_id"]
            guard_record = records.get(aid)
            out.append({"audit_id": aid,
                        "guard": ({k: v for k, v in guard_record.items() if k != "item_id"}
                                  if guard_record else {"valid": False, "reason": f"prompt not parsed: {unparsed[aid]}"}),
                        "secondary_toxicity": ({"p": tox[aid], "flag": tox[aid] >= toxicity.threshold}
                                               if toxicity is not None else None)})
        write_atomic(run_dir / "audit_scores.jsonl", jsonl_bytes(out))
        valid = [o["guard"] for o in out if o["guard"]["valid"]]
        summary = {"items": len(out), "unparsed_prompts": len(unparsed), "guard_invalid": len(out) - len(valid),
                   **{f"guard_{label.lower()}": sum(g["safety"] == label for g in valid)
                      for label in ("Unsafe", "Controversial", "Safe")},
                   "guard_refusal_yes": sum(g["refusal"] == "Yes" for g in valid),
                   "secondary_toxicity_flagged": (sum(o["secondary_toxicity"]["flag"] for o in out)
                                                  if toxicity is not None else None)}
        return _finish(run_dir, ledger, "score-audit", identity, {"summary": summary})
    except BaseException as exc:
        _fail(run_dir, ledger, exc)
        raise


def _unit_mismatch(folder: Path, expected: dict, identity: dict, complete: bool) -> list[str]:
    """Why an existing attempt folder is not the requested calibration unit (empty: it is):
    the stored job's scientific fields, its resume source (resolved path) and, for a complete
    folder, the completion identity and the hashed identity.json against the current manifest,
    recipe and code."""
    try:
        stored = read_json(folder / "job.json")
    except (OSError, ValueError):
        return ["job.json missing or unreadable"]
    wrong = [key for key in UNIT_KEYS if stored.get(key) != expected[key]]
    have, want = stored.get("resume_from"), expected["resume_from"]
    if (have is None) != (want is None) or (have is not None and Path(have).resolve() != Path(want).resolve()):
        wrong.append("resume_from")
    if complete:
        marker, ident = read_complete(folder), read_json(folder / "identity.json")
        wrong += [f"identity.{key}" for key in IDENTITY_KEYS
                  if marker["identity"].get(key) != identity[key] or ident.get(key) != identity[key]]
    return wrong


def _attempt(out_root: Path, seed: int, arm: str, checkpoint: str, expected: dict,
             identity: dict) -> tuple[Path, bool, list[str]]:
    """The first complete attempt folder of a calibration unit (reused only if its stored job
    and identities equal the request), else a new attempt path; plus the earlier incomplete
    attempts. Any attempt for different science refuses: nothing is reused, mixed or rewritten."""
    base = f"{seed}-{arm}-{checkpoint}-a"
    numbers = sorted(int(p.name[len(base):]) for p in out_root.glob(base + "*")
                     if p.name[len(base):].isdigit())
    reuse, incomplete = None, []
    for number in numbers:
        folder = out_root / f"{base}{number}"
        complete = not verify_files(folder)
        if complete or (folder / "job.json").exists():
            wrong = _unit_mismatch(folder, expected, identity, complete)
            if wrong:
                raise JobError(f"{folder} is a {'complete' if complete else 'failed'} attempt for "
                               f"different science (differs in {wrong}); calibration never reuses or "
                               "mixes it: use a new out_root, or eval-state for new evaluation settings")
        if complete and reuse is None:
            reuse = folder
        elif not complete:
            incomplete.append(str(folder))
    if reuse is not None:
        return reuse, True, incomplete
    return out_root / f"{base}{(numbers[-1] + 1) if numbers else 1}", False, incomplete


def calibrate(*, prepared_dir: str | Path, out_root: str | Path, session: Session, arms: Sequence[str],
              seeds: Sequence[int], checkpoints: Sequence[str] | None = None, base_eval: bool = False,
              wall_limit_seconds: float | None = None) -> dict:
    """Development calibration only: development groups and a0, development seeds, the
    development bank. Each (seed, arm) trajectory runs checkpoint by checkpoint (each a
    continuation of the previous). A complete unit is reused only if its stored job and
    identities equal the request (data, recipe, code, split, role, arm, seed, checkpoint, bank,
    resume source); any mismatch refuses. Failed attempts are preserved and retried in a new
    folder; a same-seed retry is the same scientific draw and every attempt's cost counts."""
    recipe, code = session.recipe, code_identity()
    manifest, manifest_sha = read_manifest(prepared_dir)
    prepared = load_prepared(prepared_dir, manifest_sha)
    for seed in seeds:
        if seed_namespace(manifest["data_config"], seed) != "development":
            raise AccessError(f"seed {seed} is not a development seed")
    for arm in arms:
        if arm != "a0" and arm not in prepared.groups["dev"]:
            raise AccessError(f"{arm} is not a development group; calibration never touches held-out groups")
    names = [n for n in checkpoint_names(recipe) if n != INIT]
    if checkpoints is not None:
        if list(checkpoints) != [n for n in names if n in set(checkpoints)]:
            raise JobError(f"checkpoints must be an ordered subset of {names}")
        names = list(checkpoints)
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    registry = out_root / "registry.jsonl"
    template = {"kind": "run-one", "split": "dev", "role": "development", "evaluate_bank": "dev",
                "manifest_sha256": manifest_sha, "recipe_sha256": session.recipe_sha256,
                "code_sha256": code["sha256"], "replicate_of": None,
                "wall_limit_seconds": wall_limit_seconds}
    identity = {"manifest_sha256": manifest_sha, "data_config_sha256": manifest["data_config_sha256"],
                "recipe_sha256": session.recipe_sha256, "training_identity": training_identity(recipe),
                "code_sha256": code["sha256"]}
    units = []
    for seed in seeds:
        for arm in arms:
            chain = ([INIT] if base_eval and arm == "a0" and seed == seeds[0] else []) + names
            previous: Path | None = None
            for name in chain:
                job = {**template, "arm": arm, "seed": seed, "target_checkpoint": name,
                       "resume_from": str(previous) if previous else None}
                folder, done, incomplete = _attempt(out_root, seed, arm, name, job, identity)
                if not done:
                    run_one(job, prepared_dir=prepared_dir, out_dir=folder, session=session, registry=registry)
                units.append({"seed": seed, "arm": arm, "checkpoint": name, "run_dir": str(folder),
                              "reused": done, "identity_checked": True,
                              "earlier_incomplete_attempts": incomplete})
                previous = folder
    return {"units": units, "registry": str(registry)}
