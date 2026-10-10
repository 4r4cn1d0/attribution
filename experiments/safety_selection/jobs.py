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

**Edit arms.** A run-one job may name an edit file (``edits.py``) instead of a group: its arm is
``edit-<SHA-256 of the file's bytes>`` and it carries the one extra key ``edit``, the file's
path. The arm string pins the content, so an edit arm has its own trajectory key and registry
claim and can never be taken for a group removal or a0; the path is only where to read it.
Jobs without an edit keep exactly their former keys. Edit arms run on the development split
only, until a frozen amendment defines held-out edits.

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
                     tokenizer_of, training_identity)

__all__ = ["JobError", "AccessError", "ROLE_SPLIT", "ROLE_BANK", "ROLE_NAMESPACE", "JOB_KEYS",
           "CONFIRMATION_ROLES", "validate_job", "check_identities", "check_run_access",
           "check_attribution_access", "require_code_pin", "score_groups_role", "allocate_seeds",
           "claim_trajectory", "trajectory_key", "checkpoint_after", "is_edit_arm", "EDIT_ARM_PREFIX"]

ROLE_SPLIT = {"development": "dev", "selector": "heldout", "reference": "heldout"}
ROLE_BANK = {"development": "dev", "selector": "selector", "reference": "hidden"}
ROLE_NAMESPACE = {"development": "development", "selector": "selector", "reference": "reference"}
CONFIRMATION_ROLES = ("selector", "reference")
EDIT_ARM_PREFIX = "edit-"
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


def is_edit_arm(arm: object) -> bool:
    """Whether an arm names an edit file by its hash (``edit-`` and 64 lowercase hex)."""
    return (isinstance(arm, str) and arm.startswith(EDIT_ARM_PREFIX) and len(arm) == len(EDIT_ARM_PREFIX) + 64
            and all(c in "0123456789abcdef" for c in arm[len(EDIT_ARM_PREFIX):]))


def validate_job(job: dict) -> dict:
    if not isinstance(job, dict) or job.get("kind") not in JOB_KEYS:
        raise JobError(f"job kind must be one of {sorted(JOB_KEYS)}")
    expected = JOB_KEYS[job["kind"]]
    if job["kind"] == "run-one" and "edit" in job:            # an edit arm (module doc)
        expected = expected | {"edit"}
    if job["kind"] == "attributes" and "anchors" in job:      # an anchor bank (Gate B, README "Anchor bank")
        expected = expected | {"anchors"}
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
        if job["arm"].startswith(EDIT_ARM_PREFIX) and not is_edit_arm(job["arm"]):
            raise JobError("an arm starting with 'edit-' must be edit- and the 64-hex SHA-256 of its file")
        if is_edit_arm(job["arm"]) != ("edit" in job):
            raise JobError("an edit arm (edit-<sha256>) and the edit key come together, or neither")
        if "edit" in job and (not isinstance(job["edit"], str) or not job["edit"]):
            raise JobError("edit must be the path of the edit file")
        if is_edit_arm(job["arm"]) and job["split"] != "dev":
            raise AccessError("edit arms are development only: no frozen amendment defines held-out edits yet")
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
        if job["query_bank"] != "ref" or "anchors" in job:
            return _anchor_attributes_job(job)
        if job["query_bank"] != "ref":
            raise JobError("query_bank must be 'ref' (the supplied DATE-LM reference rows)")
    return job


def _anchor_attributes_job(job: dict) -> dict:
    """An attributes job on an anchor bank (Gate B; README "Anchor bank"): ``query_bank`` is ``anchors-`` and the
    SHA-256 of the anchor file's bytes, and ``anchors`` is the file's path; "ref" never carries ``anchors``."""
    bank = job["query_bank"]
    if bank == "ref":
        raise JobError("query_bank 'ref' takes no anchors file")
    if not (isinstance(bank, str) and bank.startswith("anchors-")):
        raise JobError("query_bank must be 'ref' or anchors-<the anchor file's SHA-256>")
    _hex(bank[len("anchors-"):], "query_bank")
    if not isinstance(job.get("anchors"), str) or not job["anchors"]:
        raise JobError("an anchor bank needs the anchors key: the anchor file's path")
    return job


def read_anchor_bank(path: str | Path, bank: str, recipe: dict) -> dict:
    """The anchor file for ``bank`` (README "Anchor bank"), checked before any model loads: its bytes hash to the
    bank, they are canonical JSON, and its kind, version, model, sets, fields, ids and counts are the schema's.
    Errors name sets, ids and counts only, never text."""
    import hashlib
    import json

    from .common import canonical_json

    sets = ("harmful", "safe")
    fields = ["anchor_id", "prompt", "response", "prompt_tokens", "target_tokens", "token_sha256"]
    if not (isinstance(bank, str) and bank.startswith("anchors-")):
        raise JobError("the recipe's query_bank is not an anchor bank")
    try:
        data = Path(path).read_bytes()
    except OSError:
        raise JobError("the anchor file cannot be read") from None
    if hashlib.sha256(data).hexdigest() != bank[len("anchors-"):]:
        raise JobError("the anchor file's SHA-256 differs from the query bank")
    try:
        doc = json.loads(data)
    except ValueError:
        raise JobError("the anchor file is not JSON") from None
    if not isinstance(doc, dict) or canonical_json(doc) != data:
        raise JobError("the anchor file is not canonical JSON")
    if set(doc) != {"kind", "version", "model", *sets, "counts", "provenance"}:
        raise JobError("the anchor file's keys are not the schema's")
    if (doc["kind"], doc["version"]) != ("safety-selection anchor bank", 1):
        raise JobError("the anchor file's kind or version is not the schema's")
    model = recipe["model"]
    if doc["model"] != {"repo_id": model["repo_id"], "revision": model["revision"]}:
        raise JobError("the anchor file's model is not the recipe's")
    if not isinstance(doc["provenance"], dict):
        raise JobError("the anchor file's provenance must be an object")
    seen: set[str] = set()
    for name in sets:
        rows = doc[name]
        if not isinstance(rows, list) or not rows:
            raise JobError(f"anchor set {name} must be a non-empty list")
        for k, row in enumerate(rows):
            if not isinstance(row, dict) or sorted(row) != sorted(fields):
                raise JobError(f"anchor set {name} entry {k}: fields are not the schema's")
            ok = (isinstance(row["anchor_id"], str) and row["anchor_id"] and isinstance(row["prompt"], str)
                  and isinstance(row["response"], str)
                  and all(isinstance(row[f], int) and not isinstance(row[f], bool) and row[f] > 0
                          for f in ("prompt_tokens", "target_tokens")))
            if not ok:
                raise JobError(f"anchor set {name} entry {k}: a field has the wrong type")
            _hex(row["token_sha256"], f"anchor set {name} entry {k} token_sha256")
            if row["anchor_id"] in seen:
                raise JobError(f"anchor set {name} entry {k}: its anchor_id is not unique")
            seen.add(row["anchor_id"])
    if doc["counts"] != {name: len(doc[name]) for name in sets}:
        raise JobError("the anchor file's counts differ from its lists")
    return doc


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
    if "query_bank" in job and job["query_bank"] != recipe["attribution"]["query_bank"]:
        raise JobError("the job's query bank differs from the recipe's")      # Gate B A2
    train = recipe["train"]
    if train.get("lr_schedule", "constant") != "constant" and "target_checkpoint" in job:
        names = checkpoint_names(recipe)                # GI III round 6, M1: refuse before any training
        if job["target_checkpoint"] not in names:       # Gate B A6: an unknown target, before names.index
            raise JobError(f"target {job['target_checkpoint']!r} is not a checkpoint of the recipe")
        if names.index(job["target_checkpoint"]) > names.index(train["schedule_until"]):
            raise JobError(f"target {job['target_checkpoint']} lies past the schedule's end "
                           f"({train['schedule_until']}); the rate is not defined there")
    tok, model = manifest["data_config"]["tokenizer"], recipe["model"]
    if (tok["repo_id"], tok["revision"], tok["end_of_turn_token"]) != (
            *tokenizer_of(recipe), model["end_of_turn_token"]):
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
