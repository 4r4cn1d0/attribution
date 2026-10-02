"""Offline workload plan and job-file construction (stdlib only; nothing loads, trains,
scores or downloads).

``build_plan`` reports, per menu option of each partition, the retained rows, optimizer steps
per epoch, every checkpoint's step and actual example count, and training tokens per epoch
(full text, no truncation); plus generation, query-loss, forced-choice, guard-feature and
attribution work. Counts, not time estimates: costs are measured by the runs. ``make_job``
writes job JSON with the actual manifest and recipe hashes so they are never typed by hand,
and refuses a confirmation job without a code pin.
"""

from __future__ import annotations

from pathlib import Path

from .common import canonical_json, code_identity, write_atomic
from .config import PARTITIONS, checkpoint_table, config_sha256, training_identity
from .jobs import require_code_pin, score_groups_role, validate_job
from .prepare import load_prepared, read_manifest
from .stream import make_plan
from .textproc import GUARD_LABEL_SEQUENCES

__all__ = ["build_plan", "make_job"]


def build_plan(recipe: dict, prepared_dir: str | Path) -> dict:
    prepared = load_prepared(prepared_dir)
    train = recipe["train"]
    tokens = {rid: r["prompt_tokens"] + r["target_tokens"] for rid, r in prepared.train_rows.items()}
    total_tokens = sum(tokens.values())
    table = checkpoint_table(recipe)
    options = {}
    for split in PARTITIONS:
        for arm in prepared.menus[split]:
            removed = prepared.removed_rows(split, arm)
            plan = make_plan(prepared.corpus, removed, 0, train["micro_batch"], train["grad_accum"])
            positions = {name: plan.checkpoint(fraction) for name, fraction in table}
            options[f"{split}/{arm}"] = {
                "removed": len(removed), "retained": plan.retained,
                "steps_per_epoch": plan.steps_per_epoch,
                "checkpoints": {n: {"step": p["step"], "examples_seen": p["examples_seen"]}
                                for n, p in positions.items()},
                "train_tokens_per_epoch": total_tokens - sum(tokens[r] for r in removed)}
    banks = prepared.manifest["banks"]
    gen = recipe["generation"]["max_new_tokens"]
    queries = len(prepared.query_rows)
    eval_work = {bank: {"query_loss_forward_passes": queries,
                        "generation_prompts": counts.get("safety", 0) + counts.get("arc_generation", 0),
                        "max_generated_tokens": (counts.get("safety", 0) + counts.get("arc_generation", 0)) * gen,
                        "forced_choice_questions": counts.get("arc_utility", 0)}
                 for bank, counts in banks.items()}
    members = {split: sum(len(m) for m in prepared.groups[split].values()) for split in PARTITIONS}
    n_ckpt = len(recipe["attribution"]["checkpoints"])
    return {"kind": "offline plan: nothing was loaded, trained, scored or downloaded",
            "manifest_sha256": prepared.manifest_sha256, "recipe_sha256": config_sha256(recipe),
            "training_identity": training_identity(recipe),
            "effective_batch": train["micro_batch"] * train["grad_accum"],
            "corpus_rows": len(tokens), "corpus_tokens": total_tokens,
            "max_example_tokens": max(tokens.values()), "options": options,
            "evaluation_per_checkpoint": eval_work,
            "score_groups_per_split": {split: {"guard_generations": members[split],
                                               "guard_label_sequences": len(GUARD_LABEL_SEQUENCES) * members[split]}
                                       for split in PARTITIONS},
            "attribution_per_seed": {split: {"gradient_passes": (members[split] + queries) * n_ckpt,
                                             "group_rows": members[split], "query_rows": queries}
                                     for split in PARTITIONS}}


def make_job(kind: str, *, prepared_dir: str | Path, recipe: dict, pin_code: bool, out: str | Path,
             **fields: object) -> dict:
    """Write one validated job file (exclusive: an existing file is never replaced). A
    confirmation job (selector or reference role, held-out guard features) needs ``pin_code``;
    an eval-state job's role is checked when it runs (it comes from the source run)."""
    _, manifest_sha = read_manifest(prepared_dir)
    job = {"kind": kind, "manifest_sha256": manifest_sha, "recipe_sha256": config_sha256(recipe),
           "code_sha256": code_identity()["sha256"] if pin_code else None, **fields}
    validate_job(job)
    if kind in ("run-one", "attributes"):
        require_code_pin(job, job["role"])
    elif kind == "score-groups":
        require_code_pin(job, score_groups_role(job["split"]))
    path = Path(out)
    if path.exists():
        raise FileExistsError(f"{path} exists; job files are never replaced")
    write_atomic(path, canonical_json(job))
    return job
