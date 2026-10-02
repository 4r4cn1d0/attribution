"""Job files and the access policy (stdlib only).

A job JSON names its kind, its scientific coordinates and the immutable identities it was
written for (prepared-manifest hash, recipe hash, optionally the code hash). Before any model
loads, a job is refused unless those identities match and its role allows its split, seed and
prompt bank:

| role | split | seed namespace | bank it may evaluate |
|---|---|---|---|
| development | dev | development | dev |
| selector | heldout | selector | selector |
| reference | heldout | reference | hidden (only with the explicit reference switch) |

Attribution runs only on development or selector a0 trajectories (never reference seeds) and
only on the supplied DATE-LM reference query rows. Frozen confirmation jobs (selector and
reference roles, and held-out guard features) must pin the code hash; development jobs may
leave it null as an explicit convenience (they still record the running code).

A trajectory registry refuses to start the same (data, training identity, split, arm, seed,
role) twice: a continuation restores its stream; a repeat needs a fresh seed, unless it names
the run it replicates (a determinism control). A retry after a preserved failure reuses the
seed: it is the SAME scientific draw, and every attempt's cost stays charged. The registry is
a read-check-append JSONL file with no lock: it is NOT safe for concurrent writers and relies
on the lead's one-GPU scheduler running jobs one at a time.
"""

from __future__ import annotations

from pathlib import Path

from .common import append_jsonl, derive_seed, read_jsonl, utc_now
from .config import (BANKS, NAMESPACES, PARTITIONS, checkpoint_names, config_sha256, seed_namespace,
                     training_identity)

__all__ = ["JobError", "AccessError", "ROLE_SPLIT", "ROLE_BANK", "ROLE_NAMESPACE", "JOB_KEYS",
           "CONFIRMATION_ROLES", "validate_job", "check_identities", "check_run_access",
           "check_attribution_access", "require_code_pin", "score_groups_role", "allocate_seeds",
           "claim_trajectory", "trajectory_key", "checkpoint_after"]

ROLE_SPLIT = {"development": "dev", "selector": "heldout", "reference": "heldout"}
ROLE_BANK = {"development": "dev", "selector": "selector", "reference": "hidden"}
ROLE_NAMESPACE = {"development": "development", "selector": "selector", "reference": "reference"}
CONFIRMATION_ROLES = ("selector", "reference")
_COMMON = {"kind", "manifest_sha256", "recipe_sha256", "code_sha256", "wall_limit_seconds"}
JOB_KEYS = {
    "run-one": _COMMON | {"split", "arm", "seed", "role", "target_checkpoint", "evaluate_bank",
                          "resume_from", "replicate_of"},
    "eval-state": _COMMON | {"source_run", "checkpoint", "evaluate_bank"},
    "attributes": _COMMON | {"split", "seed", "role", "a0_states", "group_ids", "query_bank"},
    "score-groups": _COMMON | {"split"},
}


class JobError(ValueError):
    pass


class AccessError(PermissionError):
    """The job's role does not allow this split, seed or prompt bank."""


def _hex(value: object, where: str, optional: bool = False) -> None:
    if optional and value is None:
        return
    if not (isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)):
        raise JobError(f"{where}: expected a 64-character lowercase hex digest")


def _seed(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JobError("seed must be a non-negative integer")
    return value


def validate_job(job: dict) -> dict:
    if not isinstance(job, dict) or job.get("kind") not in JOB_KEYS:
        raise JobError(f"job kind must be one of {sorted(JOB_KEYS)}")
    expected = JOB_KEYS[job["kind"]]
    if set(job) != expected:
        raise JobError(f"{job['kind']} job: missing {sorted(expected - set(job))}, "
                       f"unknown {sorted(set(job) - expected)}")
    _hex(job["manifest_sha256"], "manifest_sha256")
    _hex(job["recipe_sha256"], "recipe_sha256")
    _hex(job["code_sha256"], "code_sha256", optional=True)
    limit = job["wall_limit_seconds"]
    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, (int, float)) or limit <= 0):
        raise JobError("wall_limit_seconds must be null or positive")
    kind = job["kind"]
    if kind in ("run-one", "attributes", "score-groups") and job["split"] not in PARTITIONS:
        raise JobError(f"split must be one of {PARTITIONS}")
    if kind in ("run-one", "attributes"):
        _seed(job["seed"])
        if job["role"] not in ROLE_SPLIT:
            raise JobError(f"role must be one of {sorted(ROLE_SPLIT)}")
    if kind in ("run-one", "eval-state") and job["evaluate_bank"] not in (None, *BANKS):
        raise JobError(f"evaluate_bank must be null or one of {BANKS}")
    if kind == "run-one":
        if not isinstance(job["arm"], str) or not job["arm"]:
            raise JobError("arm must be 'a0' or a group id")
        for key in ("resume_from", "replicate_of"):
            if job[key] is not None and (not isinstance(job[key], str) or not job[key]):
                raise JobError(f"{key} must be null or a run folder path")
        if job["resume_from"] is not None and job["replicate_of"] is not None:
            raise JobError("a continuation cannot also be a replicate")
    if kind == "eval-state":
        if not isinstance(job["source_run"], str) or not isinstance(job["checkpoint"], str):
            raise JobError("source_run and checkpoint must be strings")
    if kind == "attributes":
        states = job["a0_states"]
        if not (isinstance(states, dict) and states
                and all(isinstance(v, str) and v for v in states.values())):
            raise JobError("a0_states must map checkpoint names to a0 run folders")
        groups = job["group_ids"]
        if not (isinstance(groups, list) and groups and all(isinstance(g, str) and g for g in groups)
                and len(set(groups)) == len(groups)):
            raise JobError("group_ids must be a non-empty list of distinct ids")
        if job["query_bank"] != "ref":
            raise JobError("query_bank must be 'ref' (the supplied DATE-LM reference rows)")
    return job


def check_identities(job: dict, manifest: dict, manifest_sha256: str, recipe: dict,
                     code: dict) -> None:
    """The job's pinned hashes must be the actual ones, and the recipe's model must be the
    tokenizer the data were audited with."""
    if job["manifest_sha256"] != manifest_sha256:
        raise JobError("job manifest_sha256 differs from the prepared manifest")
    if job["recipe_sha256"] != config_sha256(recipe):
        raise JobError("job recipe_sha256 differs from the recipe")
    if job["code_sha256"] is not None and job["code_sha256"] != code["sha256"]:
        raise JobError("job code_sha256 differs from the running code")
    tok, model = manifest["data_config"]["tokenizer"], recipe["model"]
    if (tok["repo_id"], tok["revision"], tok["end_of_turn_token"]) != (
            model["repo_id"], model["revision"], model["end_of_turn_token"]):
        raise JobError("recipe model differs from the tokenizer the data were audited with")


def check_run_access(role: str, split: str, seed: int, bank: str | None, data_config: dict,
                     allow_hidden: bool) -> None:
    if ROLE_SPLIT[role] != split:
        raise AccessError(f"role {role} runs only on the {ROLE_SPLIT[role]} split, not {split}")
    space = seed_namespace(data_config, seed)
    if space != ROLE_NAMESPACE[role]:
        raise AccessError(f"seed {seed} is in namespace {space}, role {role} needs "
                          f"{ROLE_NAMESPACE[role]}")
    if bank is not None and bank != ROLE_BANK[role]:
        raise AccessError(f"role {role} may evaluate only the {ROLE_BANK[role]} bank, not {bank}")
    if bank == "hidden" and not allow_hidden:
        raise AccessError("the hidden reference bank needs an explicit reference run "
                          "(--allow-hidden-reference)")


def require_code_pin(job: dict, role: str) -> None:
    """Frozen confirmation (selector and reference roles) needs an explicit code pin; a null
    pin is the explicit development convenience only."""
    if role in CONFIRMATION_ROLES and job["code_sha256"] is None:
        raise JobError(f"{role} jobs belong to frozen confirmation and must pin code_sha256 "
                       "(make-job --pin-code); a null pin is allowed for development only")


def score_groups_role(split: str) -> str:
    """Guard features of the held-out split feed the confirmation selector."""
    return "development" if split == "dev" else "selector"


def check_attribution_access(job: dict, data_config: dict, recipe: dict) -> None:
    if job["role"] == "reference":
        raise AccessError("attribution never uses reference seeds")
    check_run_access(job["role"], job["split"], job["seed"], None, data_config, False)
    if sorted(job["a0_states"]) != sorted(recipe["attribution"]["checkpoints"]):
        raise JobError(f"a0_states must name exactly the recipe attribution checkpoints "
                       f"{recipe['attribution']['checkpoints']}")


def trajectory_key(manifest_sha256: str, recipe: dict, split: str, arm: str, seed: int,
                   role: str) -> dict:
    return {"manifest_sha256": manifest_sha256, "training_identity": training_identity(recipe),
            "split": split, "arm": arm, "seed": seed, "role": role}


def claim_trajectory(registry: str | Path, key: dict, run_dir: str, replicate_of: str | None) -> None:
    """Refuse a second fresh start of one trajectory unless it names the run it replicates.
    A preserved failed start (its folder has error.txt) does not block a retry."""
    entries = read_jsonl(registry)
    same = [e for e in entries if e["key"] == key]
    live = [e for e in same if not (Path(e["run_dir"]) / "error.txt").exists()]
    if replicate_of is None and live:
        raise JobError(f"trajectory {key} already started in {live[0]['run_dir']}: a repeat "
                       "must use a fresh seed (or name replicate_of for a determinism control)")
    if replicate_of is not None and not any(e["run_dir"] == replicate_of for e in live):
        raise JobError(f"replicate_of {replicate_of} is not a registered start of this trajectory")
    append_jsonl(registry, {"key": key, "run_dir": run_dir, "replicate_of": replicate_of,
                            "retry_after_failures": [e["run_dir"] for e in same if e not in live],
                            "utc": utc_now()})


def allocate_seeds(data_config: dict, namespace: str, purpose: str, count: int,
                   exclude: set[int] | frozenset[int] = frozenset()) -> list[int]:
    """``count`` distinct seeds of a namespace for one named operation (deterministic; the
    caller passes seeds already used by other operations in ``exclude``). Memory and work
    scale with ``count`` and ``exclude``, never with the namespace width: excluded seeds are
    tested by interval membership, so one seed from a billion-wide namespace costs O(1)."""
    if namespace not in NAMESPACES:
        raise JobError(f"unknown namespace {namespace}")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise JobError("count must be a non-negative integer")
    first, last = data_config["seed_namespaces"][namespace]
    span = last - first + 1
    taken = {seed for seed in exclude if first <= seed <= last}
    if count + len(taken) > span:
        raise JobError(f"namespace {namespace} has too few seeds for {count} more")
    out: list[int] = []
    chosen: set[int] = set()
    index = 0
    while len(out) < count:
        seed = first + derive_seed("seed-allocation", namespace, purpose, index) % span
        index += 1
        if seed not in chosen and seed not in taken:
            chosen.add(seed)
            out.append(seed)
    return out


def checkpoint_after(recipe: dict, earlier: str, later: str) -> bool:
    names = checkpoint_names(recipe)
    return names.index(later) > names.index(earlier)
