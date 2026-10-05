"""Tools of the headroom amendment's positive control (draft, 5 October 2026): the row scorer,
the edit builder and the rewrite generator. The model work runs on one GPU through injected
callables; everything here is tested on ENGINEERING FIXTURES on CPU, and nothing here trains.

**The edit pool** is every training row that is not a member of a held-out group
(``POOL_RULE``). No held-out row is scored, ranked, rewritten or named in an edit file.

**Row scorer** (``score_rows``). For every pool row, the guard's normalized label-sequence
scores of the row's own (prompt, response) pair, exactly ``GuardScorer.label_scores``
(``scoring.LABEL_SCORE_DEFINITION``); the row's score is the normalized ``Unsafe`` value.
These are relative likelihoods of three fixed answer lines, not calibrated probabilities. A row
whose text contains a guard control string is unscored and recorded as such; it is never ranked
and never imputed. The output is one canonical JSON document; its SHA-256 is what every later
step pins. The scorer is the same model as the study's judge: that is the amendment's stated
choice for a positive control (its open decision 1), recorded in the file.

**Edit builder.** From a frozen scores file: ``remove`` the top k% of ranked rows, ``rewrite``
the same rows from a frozen rewrites file, ``random`` removal of k% of the pool with a seed
derived from the data config's design seed, and ``random rewrite`` of exactly those random rows
(the control for *which* rows are rewritten). One rewrites file covers the union of the top and
the random rows; each of its rows records the set or sets it belongs to. ``ROUND_1`` names the
four files of the positive control's first round (10%). Ranking: score descending, ties by row id. The
number of rows for k% is ``round half up(k / 100 * training rows)`` (``edit_count``), so 2.5,
4, 7 and 10% of 10,148 rows are 254, 406, 710 and 1,015, the amendment's numbers; the count's
base (training rows, not pool rows) is recorded in each file. ``add`` and ``combined`` files
are written only from rows supplied explicitly: their source is the amendment's open decision 3.

**Rewrite generator** (``generate_rewrites``). Input: (row id, request) pairs and nothing else;
the original reply never reaches the generator. Each request is rendered with the system
prompt of the amendment's Appendix A and answered greedily. A draft is accepted only if it
ended at the end-of-turn token, is not empty, encodes as a training row with the policy's
codec (no control token, within the token limit) and the guard labels the (request, draft)
pair Safe. A draft that fails is generated once more with the retry system prompt; one that
fails again is excluded and recorded with its reasons. Greedy decoding of the same input gives
the same draft, so "generate once more" needs a different input: the retry prompt is the
Appendix A prompt with one added sentence (``RETRY_SENTENCE``). That sentence is this
implementation's proposal, open for the amendment's review.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable, Sequence

from .common import canonical_json, code_identity, derive_seed, sha256_bytes
from .config import ConfigError, _hex, _int, _keys, _text, _texts
from .edits import (ADD_PREFIX, EDIT_KIND, EDIT_VERSION, POSITION_RULE, EditError, edit_bytes,
                    heldout_members)
from .scoring import LABEL_SCORE_DEFINITION, GuardScorer
from .textproc import ControlTokenError, NoTargets, TooLong, encode_train

__all__ = ["POOL_RULE", "SCORES_KIND", "REWRITES_KIND", "REWRITE_CONFIG_KIND", "APPENDIX_A_SYSTEM",
           "RETRY_SENTENCE", "edit_pool", "score_rows", "ranked_rows", "edit_count", "build_remove",
           "build_random_removal", "build_rewrite", "build_add", "build_combined", "RewriteGenerator",
           "rewrite_prompt_ids", "generate_rewrites", "rewrites_document", "validate_rewrite_config",
           "load_rewrite_generator", "parse_document", "added_row_id", "score_rows_job",
           "build_edits_job", "generate_rewrites_job", "edit_document", "random_rows", "build_random_rewrite",
           "ROUND_1", "RANDOM_RULE"]

POOL_RULE = "every training row that is not a member of a held-out group"
SCORES_KIND = "safety-selection row scores"
REWRITES_KIND = "safety-selection rewrites"
REWRITE_CONFIG_KIND = "safety-selection rewrite config"
SCORE_FIELD = "normalized Unsafe label-sequence score of the row's own (prompt, response)"
COUNT_RULE = "round half up of percent / 100 times the number of training rows"
RANK_RULE = "valid scores in descending order, ties broken by row id ascending; unscored rows are never ranked"
# The system prompt of the amendment's Appendix A, verbatim.
APPENDIX_A_SYSTEM = ("You write assistant replies for safety training data. Reply in the language of the request. "
                     "If the request asks for something harmful, unsafe or illegal, refuse briefly, do not repeat "
                     "harmful details, and suggest a safe alternative when one exists. If the request is harmless, "
                     "answer it helpfully and accurately without harmful content. Output only the reply.")
RETRY_SENTENCE = "A previous reply to this request was not judged safe: if in any doubt, refuse briefly."


def parse_document(data: bytes, kind: str) -> dict:
    import json

    try:
        doc = json.loads(data)
    except ValueError:
        raise EditError(f"not a {kind} document (not JSON)") from None
    if not isinstance(doc, dict) or doc.get("kind") != kind or doc.get("version") != 1:
        raise EditError(f"not a {kind} document of version 1")
    return doc


# ----- the pool and the row scorer ----------------------------------------------------------------


def edit_pool(prepared: Any) -> list[str]:
    """The pool rows, sorted (module doc)."""
    return sorted(set(prepared.train_rows) - heldout_members(prepared))


def _pool_record(prepared: Any) -> dict:
    pool = edit_pool(prepared)
    return {"rule": POOL_RULE, "training_rows": len(prepared.train_rows), "pool_rows": len(pool),
            "heldout_members_excluded": len(heldout_members(prepared))}


def score_rows(prepared: Any, guard: GuardScorer, guard_spec: dict, check: Callable | None = None) -> bytes:
    """The scores document of every pool row (module doc), as its exact bytes."""
    pool = edit_pool(prepared)
    items = [(row_id, prepared.train_rows[row_id]["prompt"], prepared.train_rows[row_id]["response"]) for row_id in pool]
    records = guard.label_scores(items, check)
    rows = []
    for record in records:
        valid = bool(record["valid"])
        rows.append({"row_id": record["item_id"], "valid": valid, "reason": record["reason"],
                     "unsafe": record["normalized"]["Unsafe"] if valid else None,
                     "normalized": record["normalized"], "loglik": record["loglik"],
                     "guard_input_tokens": record["guard_input_tokens"],
                     "control_strings": record["control_strings"]})
    document = {"kind": SCORES_KIND, "version": 1, "manifest_sha256": prepared.manifest_sha256,
                "scorer": {"repo_id": guard_spec["repo_id"], "revision": guard_spec["revision"],
                           "definition": LABEL_SCORE_DEFINITION, "score": SCORE_FIELD,
                           "note": "the scorer is the study's judge model: the amendment's choice for a positive "
                                   "control (open decision 1), not an independent measurement",
                           "identity": guard.identity},
                "pool": _pool_record(prepared), "scored_rows": sum(r["valid"] for r in rows),
                "unscored_rows": sum(not r["valid"] for r in rows), "code_sha256": code_identity()["sha256"],
                "rows": rows}
    return canonical_json(document)


def _scores(data: bytes, prepared: Any) -> dict:
    doc = parse_document(data, SCORES_KIND)
    if doc["manifest_sha256"] != prepared.manifest_sha256:
        raise EditError("the scores were computed on another prepared dataset")
    rows = doc["rows"]
    if [r["row_id"] for r in rows] != edit_pool(prepared):
        raise EditError("the scores do not cover exactly the edit pool of this prepared dataset")
    return doc


def ranked_rows(scores: dict) -> list[str]:
    valid = [r for r in scores["rows"] if r["valid"]]
    return [r["row_id"] for r in sorted(valid, key=lambda r: (-r["unsafe"], r["row_id"]))]


def edit_count(percent: str, training_rows: int) -> int:
    """Rows in k% (module doc). ``percent`` is decimal text, e.g. ``"2.5"``, so it is exact."""
    share = Fraction(percent)
    if not 0 < share <= 100:
        raise EditError("percent must be in (0, 100]")
    exact = share * training_rows / 100
    return int(exact + Fraction(1, 2))     # floor(x + 1/2): round half up


# ----- the edit builder -----------------------------------------------------------------------------


def edit_document(name: str, edit_kind: str, prepared: Any, provenance: dict, remove: Sequence[str] = (),
          rewrite: Sequence[dict] = (), add: Sequence[dict] = ()) -> tuple[bytes, dict]:
    doc = {"kind": EDIT_KIND, "version": EDIT_VERSION, "name": name, "edit_kind": edit_kind,
           "manifest_sha256": prepared.manifest_sha256, "remove": sorted(remove),
           "rewrite": sorted(rewrite, key=lambda r: r["row_id"]), "add": sorted(add, key=lambda r: r["row_id"]),
           "position_rule": POSITION_RULE,
           "counts": {"remove": len(remove), "rewrite": len(rewrite), "add": len(add)},
           "provenance": {**provenance, "pool": _pool_record(prepared), "builder_code_sha256": code_identity()["sha256"]}}
    return edit_bytes(doc), doc


def _top(scores: dict, prepared: Any, percent: str) -> tuple[list[str], int]:
    ranked = ranked_rows(scores)
    count = edit_count(percent, len(prepared.train_rows))
    if count > len(ranked):
        raise EditError(f"{percent}% is {count} rows; only {len(ranked)} pool rows are ranked")
    return ranked[:count], count


def _score_provenance(scores_data: bytes, scores: dict, prepared: Any, percent: str, count: int) -> dict:
    return {"scores_sha256": sha256_bytes(scores_data), "percent": percent, "count_rule": COUNT_RULE,
            "count": count, "count_base_training_rows": len(prepared.train_rows), "rank_rule": RANK_RULE,
            "ranked_rows": len(ranked_rows(scores)), "unscored_rows": scores["unscored_rows"]}


def build_remove(scores_data: bytes, prepared: Any, percent: str) -> tuple[bytes, dict]:
    """Remove the top ``percent``% of the ranked pool."""
    scores = _scores(scores_data, prepared)
    rows, count = _top(scores, prepared, percent)
    return edit_document(f"remove top {percent}% by guard Unsafe score", "remove", prepared,
                 _score_provenance(scores_data, scores, prepared, percent, count), remove=rows)


RANDOM_RULE = "random.Random(derive_seed(design_seed, 'headroom-random-removal', percent)).sample(sorted pool, count)"


def random_rows(prepared: Any, percent: str) -> tuple[list[str], int, int]:
    """(rows, count, seed) of the random control: ``percent``% of the pool chosen with a seed
    derived from the data config's design seed (no free parameter). Random removal and random
    rewrite both take exactly these rows."""
    count = edit_count(percent, len(prepared.train_rows))
    seed = derive_seed(prepared.data_config["design_seed"], "headroom-random-removal", percent)
    return sorted(random.Random(seed).sample(edit_pool(prepared), count)), count, seed


def build_random_removal(scores_data: bytes, prepared: Any, percent: str) -> tuple[bytes, dict]:
    """Remove the random control's rows (``random_rows``). The scores file is pinned only for its pool."""
    scores = _scores(scores_data, prepared)
    rows, count, seed = random_rows(prepared, percent)
    return edit_document(f"remove {percent}% of the pool at random", "remove", prepared,
                 {"scores_sha256": sha256_bytes(scores_data), "percent": percent, "count_rule": COUNT_RULE,
                  "count": count, "count_base_training_rows": len(prepared.train_rows),
                  "random_rule": RANDOM_RULE, "seed": seed, "unscored_rows": scores["unscored_rows"]}, remove=rows)


def _rewrites(rewrites_data: bytes, scores_data: bytes, prepared: Any) -> dict:
    rewrites = parse_document(rewrites_data, REWRITES_KIND)
    if rewrites["manifest_sha256"] != prepared.manifest_sha256 or rewrites["scores_sha256"] != sha256_bytes(scores_data):
        raise EditError("the rewrites were generated for other scores or another prepared dataset")
    return rewrites


def _rewritten(rows: Sequence[str], rewrites: dict) -> tuple[list[dict], list[dict]]:
    by_row = {r["row_id"]: r for r in rewrites["rows"]}
    missing = [row for row in rows if row not in by_row]
    if missing:
        raise EditError(f"the rewrites file has no record for {len(missing)} of the rows (first {missing[0]})")
    accepted = [{"row_id": row, "response": by_row[row]["response"]} for row in rows if by_row[row]["status"] == "accepted"]
    excluded = [{"row_id": row, "reason": by_row[row]["reason"]} for row in rows if by_row[row]["status"] != "accepted"]
    if not accepted:
        raise EditError("no replacement of these rows was accepted")
    return accepted, excluded


def build_random_rewrite(scores_data: bytes, rewrites_data: bytes, prepared: Any, percent: str) -> tuple[bytes, dict]:
    """Rewrite exactly the random control's rows (those of ``build_random_removal``) from the
    same rewrites file; rows whose replacement was excluded stay as they are and are listed."""
    scores = _scores(scores_data, prepared)
    rewrites = _rewrites(rewrites_data, scores_data, prepared)
    rows, count, seed = random_rows(prepared, percent)
    accepted, excluded = _rewritten(rows, rewrites)
    return edit_document(f"rewrite {percent}% of the pool at random", "rewrite", prepared,
                 {"scores_sha256": sha256_bytes(scores_data), "percent": percent, "count_rule": COUNT_RULE,
                  "count": count, "count_base_training_rows": len(prepared.train_rows), "random_rule": RANDOM_RULE,
                  "seed": seed, "unscored_rows": scores["unscored_rows"], "rewrites_sha256": sha256_bytes(rewrites_data),
                  "rewritten": len(accepted), "excluded": excluded}, rewrite=accepted)


def build_rewrite(scores_data: bytes, rewrites_data: bytes, prepared: Any, percent: str) -> tuple[bytes, dict]:
    """Rewrite the same rows as ``build_remove`` with the accepted replacements of a frozen
    rewrites file. Rows whose replacement was excluded stay as they are and are listed."""
    scores = _scores(scores_data, prepared)
    rewrites = _rewrites(rewrites_data, scores_data, prepared)
    rows, count = _top(scores, prepared, percent)
    accepted, excluded = _rewritten(rows, rewrites)
    return edit_document(f"rewrite top {percent}% by guard Unsafe score", "rewrite", prepared,
                 {**_score_provenance(scores_data, scores, prepared, percent, count),
                  "rewrites_sha256": sha256_bytes(rewrites_data), "rewritten": len(accepted), "excluded": excluded},
                 rewrite=accepted)


def build_add(rows: Sequence[dict], prepared: Any, name: str, source: dict) -> tuple[bytes, dict]:
    """An add edit from explicitly supplied rows ``{row_id, prompt, response}`` and a statement
    of their source. Pending the amendment's open decision 3: no command writes one."""
    if not source:
        raise EditError("added rows need a stated source (open decision 3)")
    return edit_document(name, "add", prepared, {"source": source}, add=[dict(r) for r in rows])


def build_combined(remove_data: bytes, add_data: bytes, prepared: Any, name: str) -> tuple[bytes, dict]:
    """A combined edit from a remove edit and an add edit (both files' hashes recorded)."""
    from .edits import parse_edit

    removed, added = parse_edit(remove_data, prepared), parse_edit(add_data, prepared)
    if removed.document["edit_kind"] != "remove" or added.document["edit_kind"] != "add":
        raise EditError("a combined edit joins one remove edit and one add edit")
    return edit_document(name, "combined", prepared,
                 {"remove_edit_sha256": removed.sha256, "add_edit_sha256": added.sha256},
                 remove=sorted(removed.removed), add=[{"row_id": i, "prompt": p, "response": r} for i, p, r in added.added])


# ----- the rewrite generator ------------------------------------------------------------------------


@dataclass
class RewriteGenerator:
    """The generator as the tool needs it: a tokenizer with a chat template, a batched greedy
    ``generate(prompt ids) -> [Generation]`` and an identity record."""

    tokenizer: Any
    generate: Callable[[list[list[int]]], list[Any]]
    identity: dict = field(default_factory=dict)


def rewrite_prompt_ids(tokenizer: Any, system: str, request: str) -> list[int]:
    ids = tokenizer.apply_chat_template([{"role": "system", "content": system}, {"role": "user", "content": request}],
                                        tokenize=True, add_generation_prompt=True)
    if hasattr(ids, "keys"):
        ids = ids["input_ids"]
    return [int(i) for i in ids]


def _drafts(rows: Sequence[tuple[str, str]], generator: RewriteGenerator, system: str) -> list[dict]:
    prompts = [rewrite_prompt_ids(generator.tokenizer, system, request) for _, request in rows]
    outputs = generator.generate(prompts)
    if len(outputs) != len(rows):
        raise RuntimeError("the generator returned a different number of drafts")
    drafts = []
    for (row_id, request), out in zip(rows, outputs):
        text = generator.tokenizer.decode(list(out.output_ids), skip_special_tokens=False)
        drafts.append({"row_id": row_id, "request": request, "text": text, "stop_reason": out.stop_reason,
                       "output_tokens": len(out.output_ids)})
    return drafts


def _judge(drafts: list[dict], guard: GuardScorer, policy_codec: Any, max_train_tokens: int) -> list[dict]:
    """Each draft with its problem (None: accepted) and the guard's labels when it was judged."""
    checked = []
    for draft in drafts:
        problem = None
        if draft["stop_reason"] != "eos":
            problem = "the draft reached the generator's token cap"
        elif not draft["text"].strip():
            problem = "the draft is empty"
        else:
            try:
                encode_train(policy_codec, draft["row_id"], draft["request"], draft["text"], max_train_tokens)
            except (TooLong, ControlTokenError, NoTargets) as exc:
                problem = f"the draft is not a usable training response ({type(exc).__name__})"
        checked.append({**draft, "problem": problem, "guard": None})
    judged = [d for d in checked if d["problem"] is None]
    labels = guard.score([(d["row_id"], d["request"], d["text"]) for d in judged]) if judged else []
    for draft, label in zip(judged, labels):
        draft["guard"] = {k: label[k] for k in ("valid", "safety", "categories", "refusal", "reason")}
        if not label["valid"]:
            draft["problem"] = "the guard's answer was invalid"
        elif label["safety"] != "Safe":
            draft["problem"] = f"the guard judged the draft {label['safety']}"
    return checked


def generate_rewrites(rows: Sequence[tuple[str, str]], generator: RewriteGenerator, guard: GuardScorer, *,
                      system: str, retry_system: str, policy_codec: Any, max_train_tokens: int) -> list[dict]:
    """One record per (row id, request), in input order (module doc). Only the request text is
    ever given to the generator."""
    if len({row_id for row_id, _ in rows}) != len(rows):
        raise ValueError("duplicate row ids")
    if retry_system == system:
        raise ValueError("the retry prompt must differ from the first: greedy decoding would repeat the draft")
    first = _judge(_drafts(rows, generator, system), guard, policy_codec, max_train_tokens)
    again = [(d["row_id"], d["request"]) for d in first if d["problem"] is not None]
    second = {d["row_id"]: d for d in _judge(_drafts(again, generator, retry_system), guard, policy_codec,
                                             max_train_tokens)} if again else {}
    records = []
    for draft in first:
        attempts = [draft] + ([second[draft["row_id"]]] if draft["row_id"] in second else [])
        accepted = next((d for d in attempts if d["problem"] is None), None)
        record = {"row_id": draft["row_id"], "status": "accepted" if accepted else "excluded",
                  "attempt": attempts.index(accepted) + 1 if accepted else None,
                  "response": accepted["text"] if accepted else None,
                  "response_sha256": sha256_bytes(accepted["text"].encode("utf-8")) if accepted else None,
                  "reason": None if accepted else "; ".join(f"attempt {i + 1}: {d['problem']}" for i, d in enumerate(attempts)),
                  "attempts": [{"attempt": i + 1, "stop_reason": d["stop_reason"], "output_tokens": d["output_tokens"],
                                "guard": d["guard"], "problem": d["problem"],
                                "text_sha256": sha256_bytes(d["text"].encode("utf-8"))} for i, d in enumerate(attempts)]}
        records.append(record)
    return records


def rewrites_document(records: list[dict], *, scores_data: bytes, prepared: Any, percent: str, config: dict,
                      generator: RewriteGenerator, guard: GuardScorer, guard_spec: dict, random: dict | None = None) -> bytes:
    return canonical_json({
        "kind": REWRITES_KIND, "version": 1, "manifest_sha256": prepared.manifest_sha256,
        "scores_sha256": sha256_bytes(scores_data), "percent": percent, "random": random, "config": config,
        "generator_identity": generator.identity,
        "guard": {"repo_id": guard_spec["repo_id"], "revision": guard_spec["revision"], "identity": guard.identity},
        "accepted": sum(r["status"] == "accepted" for r in records),
        "accepted_on_retry": sum(r["attempt"] == 2 for r in records),
        "excluded": sum(r["status"] != "accepted" for r in records),
        "code_sha256": code_identity()["sha256"], "rows": records})


# ----- the generator's configuration and its real loader ----------------------------------------------


def validate_rewrite_config(config: dict) -> dict:
    _keys(config, {"kind", "name", "purpose", "generator", "system_prompt", "retry_system_prompt"}, "rewrite config")
    if config["kind"] != REWRITE_CONFIG_KIND:
        raise ConfigError(f"kind must be {REWRITE_CONFIG_KIND!r}")
    _text(config["name"], "name")
    _text(config["purpose"], "purpose")
    spec = _keys(config["generator"], {"repo_id", "revision", "architecture", "dtype", "attn_implementation",
                                       "stop_tokens", "pad_token", "max_new_tokens", "batch_size"}, "generator")
    _text(spec["repo_id"], "generator.repo_id")
    _hex(spec["revision"], 40, "generator.revision")
    _text(spec["architecture"], "generator.architecture")
    if spec["dtype"] != "bfloat16" or spec["attn_implementation"] != "eager":
        raise ConfigError("the generator runs in bfloat16 with eager attention")
    _texts(spec["stop_tokens"], "generator.stop_tokens")
    _text(spec["pad_token"], "generator.pad_token")
    _int(spec["max_new_tokens"], "generator.max_new_tokens", 1)
    _int(spec["batch_size"], "generator.batch_size", 1)
    if _text(config["system_prompt"], "system_prompt") != APPENDIX_A_SYSTEM:
        raise ConfigError("system_prompt must be the amendment's Appendix A prompt verbatim")
    if _text(config["retry_system_prompt"], "retry_system_prompt") == config["system_prompt"]:
        raise ConfigError("the retry prompt must differ from the first (greedy decoding would repeat the draft)")
    return config


def load_rewrite_generator(config: dict) -> RewriteGenerator:
    """The pinned generator on CUDA (offline, safetensors, no remote code, bfloat16, eager)."""
    import torch
    from transformers import AutoModelForCausalLM

    from .engine import greedy_generate
    from .loaders import load_tokenizer, snapshot
    from .textproc import TemplateError, build_codec

    spec = config["generator"]
    tokenizer, status = load_tokenizer(spec["repo_id"], spec["revision"])
    snapshot(spec["repo_id"], spec["revision"])
    probe = tokenizer.apply_chat_template([{"role": "system", "content": "<<S>>"}, {"role": "user", "content": "<<U>>"}],
                                          tokenize=False, add_generation_prompt=True)
    if not (probe.endswith("<|im_start|>assistant\n") and "<<S>>" in probe and "<<U>>" in probe):
        raise TemplateError("the generator's chat template does not end with the assistant header")
    model = AutoModelForCausalLM.from_pretrained(status["snapshot"], torch_dtype=torch.bfloat16, use_safetensors=True,
                                                 attn_implementation=spec["attn_implementation"], local_files_only=True,
                                                 trust_remote_code=False)
    if type(model).__name__ != spec["architecture"]:
        raise RuntimeError(f"loaded {type(model).__name__}, the config expects {spec['architecture']}")
    model.requires_grad_(False)
    model.eval().to("cuda")
    codec = build_codec(tokenizer, spec["stop_tokens"][0], spec["stop_tokens"], spec["pad_token"])

    def generate(prompts: list[list[int]]) -> list:
        return greedy_generate(model, prompts, max_new_tokens=spec["max_new_tokens"], stop_ids=codec.stop_ids,
                               pad_id=codec.pad_id, device="cuda", batch_size=spec["batch_size"])

    identity = {**status, "chat_template_sha256": sha256_bytes((getattr(tokenizer, "chat_template", "") or "").encode()),
                "template_probe": probe, "stop_ids": list(codec.stop_ids), "pad_id": codec.pad_id}
    return RewriteGenerator(tokenizer, generate, identity)


def added_row_id(prompt: str, response: str) -> str:
    """A content-derived id for an added row (``add-`` and 16 hex)."""
    return ADD_PREFIX + sha256_bytes(canonical_json({"prompt": prompt, "response": response}))[:16]


# ----- the tools as jobs: each writes one new folder, never replaced ----------------------------------

def _tool_folder(out_dir, job: dict, session: Any):
    import platform
    import sys

    from .common import write_json
    from .ledger import RunLedger, create_run_dir

    run_dir = create_run_dir(out_dir)
    code = code_identity()
    write_json(run_dir / "job.json", job)
    write_json(run_dir / "identity.json", {"code_sha256": code["sha256"], "code_files": code["files"],
                                           "recipe_sha256": session.recipe_sha256 if session else None,
                                           "python": sys.version, "platform": platform.platform()})
    ledger = RunLedger(run_dir, sync=session.sync if session else None, memory=session.memory if session else None)
    return run_dir, ledger


def score_rows_job(session: Any, prepared_dir, out_dir) -> dict:
    """``score-rows``: the scores of every pool row (``scores.json``) in a new folder."""
    from .common import write_atomic
    from .ledger import write_complete
    from .prepare import load_prepared

    prepared = load_prepared(prepared_dir)
    run_dir, ledger = _tool_folder(out_dir, {"kind": "score-rows", "manifest_sha256": prepared.manifest_sha256,
                                             "recipe_sha256": session.recipe_sha256}, session)
    try:
        guard = session.guard(ledger, run_dir)
        with ledger.stage("score_rows", rows=len(edit_pool(prepared))) as info:
            data = score_rows(prepared, guard, session.recipe["guard"], check=lambda what: ledger.check(f"guard {what}"))
            info.update(scores_sha256=sha256_bytes(data))
        write_atomic(run_dir / "scores.json", data)
        doc = parse_document(data, SCORES_KIND)
        summary = {"kind": "score-rows", "scores_sha256": sha256_bytes(data), "pool_rows": doc["pool"]["pool_rows"],
                   "scored_rows": doc["scored_rows"], "unscored_rows": doc["unscored_rows"]}
        write_complete(run_dir, summary)
        return {"run_dir": str(run_dir), **summary}
    except BaseException:
        import traceback

        (run_dir / "error.txt").write_text(traceback.format_exc())
        raise


ROUND_1 = ("remove-10", "random-remove-10", "rewrite-10", "random-rewrite-10")


def build_edits_job(prepared_dir, scores_path, out_dir, *, rewrites_path=None,
                    percents: Sequence[str] = ("2.5", "4", "7", "10"), random_percent: str = "10",
                    only: Sequence[str] | None = None) -> dict:
    """``build-edits`` (CPU only): the positive control's edit files and an index of their arms.
    ``only`` restricts it to the named files (``ROUND_1``: the first round's four, which needs the
    rewrites file)."""
    from pathlib import Path

    from .common import write_atomic
    from .ledger import create_run_dir
    from .prepare import load_prepared

    prepared = load_prepared(prepared_dir)
    scores_data = Path(scores_path).read_bytes()
    rewrites_data = Path(rewrites_path).read_bytes() if rewrites_path else None
    plan: list[tuple[str, Callable[[], tuple[bytes, dict]]]] = []
    for percent in percents:
        plan.append((f"remove-{percent}", lambda p=percent: build_remove(scores_data, prepared, p)))
        if rewrites_data is not None:
            plan.append((f"rewrite-{percent}", lambda p=percent: build_rewrite(scores_data, rewrites_data, prepared, p)))
    plan.append((f"random-remove-{random_percent}", lambda: build_random_removal(scores_data, prepared, random_percent)))
    if rewrites_data is not None:
        plan.append((f"random-rewrite-{random_percent}",
                     lambda: build_random_rewrite(scores_data, rewrites_data, prepared, random_percent)))
    if only is not None:
        unknown = sorted(set(only) - {name for name, _ in plan})
        if unknown:
            raise EditError(f"cannot build {unknown} from these inputs (a rewrite needs the rewrites file)")
        plan = [(name, make) for name, make in plan if name in set(only)]
    made = [(name, *make()) for name, make in plan]
    run_dir = create_run_dir(out_dir)
    index = []
    for name, data, doc in made:
        write_atomic(run_dir / f"{name}.json", data)
        index.append({"file": f"{name}.json", "arm": "edit-" + sha256_bytes(data), "edit_kind": doc["edit_kind"],
                      "counts": doc["counts"], "provenance": {k: v for k, v in doc["provenance"].items()
                                                             if k in ("percent", "count", "rewritten", "seed")}})
    record = {"kind": "build-edits", "manifest_sha256": prepared.manifest_sha256, "only": list(only) if only else None,
              "scores_sha256": sha256_bytes(scores_data),
              "rewrites_sha256": sha256_bytes(rewrites_data) if rewrites_data is not None else None,
              "pending": ["add and combined edits: their source is the amendment's open decision 3"],
              "code_sha256": code_identity()["sha256"], "edits": index}
    write_atomic(run_dir / "index.json", canonical_json(record))
    return {"run_dir": str(run_dir), "edits": index}


def generate_rewrites_job(config: dict, session: Any, prepared_dir, scores_path, out_dir, *, percent: str = "10",
                          random_percent: str = "10", generator: RewriteGenerator | None = None,
                          policy_codec: Any = None) -> dict:
    """``generate-rewrites``: replacements for the union of the top ``percent``% of the ranked
    pool (the largest edit size; smaller sizes take a prefix of the same rows) and the random
    control's ``random_percent``% (``random_rows``), in a new folder. Each row records its sets."""
    from pathlib import Path

    from .common import write_atomic
    from .ledger import write_complete
    from .prepare import load_prepared

    validate_rewrite_config(config)
    prepared = load_prepared(prepared_dir)
    scores_data = Path(scores_path).read_bytes()
    scores = _scores(scores_data, prepared)
    top, count = _top(scores, prepared, percent)
    chosen, random_count, seed = random_rows(prepared, random_percent)
    sets: dict[str, list[str]] = {row: [] for row in sorted(set(top) | set(chosen))}
    for row in top:
        sets[row].append(f"top-{percent}")
    for row in chosen:
        sets[row].append(f"random-{random_percent}")
    rows = list(sets)
    run_dir, ledger = _tool_folder(out_dir, {"kind": "generate-rewrites", "manifest_sha256": prepared.manifest_sha256,
                                             "scores_sha256": sha256_bytes(scores_data), "percent": percent,
                                             "random_percent": random_percent, "config": config,
                                             "recipe_sha256": session.recipe_sha256}, session)
    try:
        guard = session.guard(ledger, run_dir)
        if policy_codec is None:
            from .config import tokenizer_of
            from .loaders import load_tokenizer
            from .textproc import build_codec

            model = session.recipe["model"]
            tokenizer, _ = load_tokenizer(*tokenizer_of(session.recipe))
            policy_codec = build_codec(tokenizer, model["end_of_turn_token"], model["stop_tokens"], model["pad_token"])
        if generator is None:
            with ledger.stage("load_generator"):
                generator = load_rewrite_generator(config)
        requests = [(row, prepared.train_rows[row]["prompt"]) for row in rows]     # the request only
        with ledger.stage("generate_rewrites", rows=len(requests)) as info:
            records = generate_rewrites(requests, generator, guard, system=config["system_prompt"],
                                        retry_system=config["retry_system_prompt"], policy_codec=policy_codec,
                                        max_train_tokens=session.recipe["model"]["max_train_tokens"])
            info.update(accepted=sum(r["status"] == "accepted" for r in records))
        records = [{**record, "sets": sets[record["row_id"]]} for record in records]
        data = rewrites_document(records, scores_data=scores_data, prepared=prepared, percent=percent, config=config,
                                 generator=generator, guard=guard, guard_spec=session.recipe["guard"],
                                 random={"percent": random_percent, "count": random_count, "seed": seed,
                                         "rule": RANDOM_RULE, "overlap_with_top": len(set(top) & set(chosen))})
        write_atomic(run_dir / "rewrites.json", data)
        doc = parse_document(data, REWRITES_KIND)
        summary = {"kind": "generate-rewrites", "rewrites_sha256": sha256_bytes(data), "rows": len(rows),
                   "top_rows": count, "random_rows": random_count,
                   "accepted": doc["accepted"], "accepted_on_retry": doc["accepted_on_retry"], "excluded": doc["excluded"]}
        write_complete(run_dir, summary)
        return {"run_dir": str(run_dir), **summary}
    except BaseException:
        import traceback

        (run_dir / "error.txt").write_text(traceback.format_exc())
        raise
