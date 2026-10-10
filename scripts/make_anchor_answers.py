"""The Gate C anchor job (brief gate-b-engine-kit-reading-20261008, A9 with [D9] A-4/A-5 and [D10]; DRAFT §1; outside
the engine identity; runs on the pod, before recipe S exists).

    python3 scripts/make_anchor_answers.py --prompts LIST --recipe REC --out DIR

It reads the sealed anchor prompt list by its pinned SHA-256 (refusing any other bytes or schema), loads REC's policy
through the engine's loaders and runs it UNTUNED (``policy.model.disable_adapter()``), and answers every prompt
greedily with REC's generation settings and the engine's codec. A safe anchor is kept in list order (harmful prompts
first, then the reserve) when its answer ended at a stop token, the recipe's guard labels it Safe (the label, not the
refusal flag) and ``encode_train`` accepts (prompt, answer) under the recipe's limits; the safe set is the first 64
kept. The harmful set is the first 64 prompts with their unsafe responses; one that ``encode_train`` refuses stops
the job. Fewer than 64 kept writes counts only and exits 3.

Outputs, in DIR: ``anchors.json``, the full anchor file (A2's schema, with text; the kit pulls it to tmp/, never to
git); ``anchors.sealed.json``, its text-free record (per anchor the id, set, list index, prompt and response
SHA-256 and token counts; the safe walk's outcome per prompt and the drop counts; the provenance; the full file's
SHA-256 and byte length). Only the record is committed. Printed and logged: ids, counts and hashes, never text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ----- constants (the DRAFT's and [D10]'s; one place) ----------------------------------------------------------------
LIST_SHA256 = "78467c97c40e7e9fd39e8061219517853e7292a25881700da5e9115604117b97"   # [D10] the sealed full list
N_PROMPTS = 128                  # prompts in the list
N_HARMFUL = 64                   # harmful set = prompts[0:64] with their unsafe responses
N_SAFE = 64                      # the first 64 kept answers, in list order
LIST_KIND, ANCHOR_KIND, RECORD_KIND = ("gate-c anchor prompt list", "safety-selection anchor bank",
                                       "gate-c anchor bank record")
EXIT_FEW = 3                     # fewer than N_SAFE kept: counts only
DROPS = ("capped", "empty", "guard_invalid", "not_safe", "does_not_encode")


class AnchorJobError(SystemExit):
    """A refusal: ids, counts and hashes only."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_prompt_list(path: pathlib.Path, pinned: str, n_prompts: int) -> dict:
    """The sealed list ([D10] schema as built): its bytes hash to ``pinned`` and are canonical JSON; top-level keys
    exactly kind, version, source, prompts, provenance; ``n_prompts`` prompts of exactly {index (0-based), prompt,
    unsafe_response}."""
    from experiments.safety_selection.common import canonical_json

    data = path.read_bytes()
    if _sha(data) != pinned:
        raise AnchorJobError("the prompt list's SHA-256 is not the pinned value")
    doc = json.loads(data)
    if not isinstance(doc, dict) or canonical_json(doc) != data:
        raise AnchorJobError("the prompt list is not canonical JSON")
    if set(doc) != {"kind", "version", "source", "prompts", "provenance"} or (doc["kind"], doc["version"]) != (
            LIST_KIND, 1):
        raise AnchorJobError("the prompt list's keys, kind or version are not the schema's")
    source = doc["source"]
    if not (isinstance(source, dict) and set(source) == {"repo_id", "revision", "file_sha256"}
            and isinstance(source["file_sha256"], dict) and source["file_sha256"]):
        raise AnchorJobError("the prompt list's source is not the schema's")
    prompts = doc["prompts"]
    if not isinstance(prompts, list) or len(prompts) != n_prompts:
        raise AnchorJobError(f"the prompt list holds {len(prompts) if isinstance(prompts, list) else 0} prompts, "
                             f"not {n_prompts}")
    for k, p in enumerate(prompts):
        if not (isinstance(p, dict) and set(p) == {"index", "prompt", "unsafe_response"} and p["index"] == k
                and isinstance(p["prompt"], str) and p["prompt"] and isinstance(p["unsafe_response"], str)
                and p["unsafe_response"]):
            raise AnchorJobError(f"prompt {k}: not the schema's (index, prompt, unsafe_response)")
    if not isinstance(doc["provenance"], dict):
        raise AnchorJobError("the prompt list's provenance is not an object")
    return doc


def _encoded(codec, anchor_id: str, prompt: str, response: str, recipe: dict):
    from experiments.safety_selection.textproc import encode_train

    try:
        return encode_train(codec, anchor_id, prompt, response, recipe["model"]["max_train_tokens"]), None
    except ValueError as exc:
        return None, type(exc).__name__


def _lock_sha256() -> str | None:
    lock = pathlib.Path.cwd() / "environment-linux.lock"
    return _sha(lock.read_bytes()) if lock.is_file() else None


def run(prompts_path: pathlib.Path, recipe_path: pathlib.Path, out: pathlib.Path, loaders, *,
        pinned: str = LIST_SHA256, n_prompts: int = N_PROMPTS, n_harmful: int = N_HARMFUL,
        n_safe: int = N_SAFE) -> int:
    """The job (module doc). Returns the exit code; writes into ``out`` (which must not exist)."""
    from experiments.safety_selection import engine as en
    from experiments.safety_selection import runner
    from experiments.safety_selection.common import canonical_json, code_identity, ids_sha256
    from experiments.safety_selection.config import config_sha256, load_recipe
    from experiments.safety_selection.ledger import RunLedger
    from experiments.safety_selection.textproc import encode_generation_prompt

    doc = read_prompt_list(prompts_path, pinned, n_prompts)
    recipe = load_recipe(recipe_path)
    if recipe["attribution"]["query_bank"] != "ref":
        raise AnchorJobError("the anchor job runs on REC (query_bank 'ref'); recipe S does not exist yet")
    out.mkdir(parents=True)
    session = runner.Session(recipe, loaders)
    ledger = RunLedger(out, sync=session.sync, memory=session.memory)
    policy = session.policy(ledger, out)
    codec, gen = policy.codec, recipe["generation"]
    prompts = doc["prompts"]
    harmful = []
    for k, p in enumerate(prompts[:n_harmful]):
        ex, failure = _encoded(codec, f"h-{k}", p["prompt"], p["unsafe_response"], recipe)
        if failure is not None:
            raise AnchorJobError(f"harmful prompt {k} ({k + 1} of {n_harmful}) does not encode ({failure}); "
                                 "the list needs a reviewed new version")
        harmful.append((k, p, ex))
    ids = []
    for k, p in enumerate(prompts):
        try:
            ids.append(encode_generation_prompt(codec, p["prompt"], recipe["model"]["max_prompt_tokens"]))
        except ValueError as exc:
            raise AnchorJobError(f"prompt {k} ({k + 1} of {len(prompts)}) does not encode as a generation prompt "
                                 f"({type(exc).__name__}); the list needs a reviewed new version") from None
    with policy.model.disable_adapter():                                   # untuned: the base model ([D9] A-5)
        generations = en.greedy_generate(policy.model, ids, max_new_tokens=gen["max_new_tokens"],
                                         stop_ids=codec.stop_ids, pad_id=codec.pad_id, device=policy.device,
                                         batch_size=gen["batch_size"])
    answers = [codec.decode(g.output_ids) for g in generations]
    guard = session.guard(ledger, out)
    over = {"over_limit_unscored": True} if gen.get("guard_over_limit") == "unscored" else {}
    labels = guard.score([(f"p-{k}", p["prompt"], a) for k, (p, a) in enumerate(zip(prompts, answers))], **over)
    walk, safe = [], []
    for k, (p, g, a, lab) in enumerate(zip(prompts, generations, answers, labels)):
        if len(safe) == n_safe:
            break
        reason, ex = None, None
        if g.stop_reason == en.STOP_CAP:
            reason = "capped"
        elif not g.output_ids:
            reason = "empty"
        elif not lab["valid"]:
            reason = "guard_invalid"
        elif lab["safety"] != "Safe":
            reason = "not_safe"
        else:
            ex, failure = _encoded(codec, f"s-{len(safe)}", p["prompt"], a, recipe)
            reason = "does_not_encode" if failure is not None else None
        walk.append({"index": k, "outcome": reason or "kept"})
        if reason is None:
            safe.append((k, p, a, ex))
    drops = {d: sum(w["outcome"] == d for w in walk) for d in DROPS}
    identity = code_identity()
    provenance = {"engine_code_sha256": identity["sha256"], "recipe_sha256": config_sha256(recipe),
                  "model": {"repo_id": recipe["model"]["repo_id"], "revision": recipe["model"]["revision"]},
                  "guard": {"repo_id": recipe["guard"]["repo_id"], "revision": recipe["guard"]["revision"]},
                  "gpu": (session.environment.get("cuda") or {}).get("name"), "lock_sha256": _lock_sha256(),
                  "prompt_list_sha256": pinned, "script_sha256": _sha(pathlib.Path(__file__).read_bytes()),
                  "untuned": "policy.model.disable_adapter()", "kept": len(safe), "walked": len(walk), "drops": drops}
    if len(safe) < n_safe:
        (out / "anchors.counts.json").write_bytes(canonical_json(
            {"kind": RECORD_KIND, "version": 1, "complete": False, "kept": len(safe), "needed": n_safe,
             "walk": walk, "drops": drops, "provenance": provenance}))
        print(json.dumps({"kept": len(safe), "needed": n_safe, "drops": drops}))
        return EXIT_FEW

    def entry(anchor_id: str, prompt: str, response: str, ex) -> dict:
        return {"anchor_id": anchor_id, "prompt": prompt, "response": response, "prompt_tokens": ex.n_prompt,
                "target_tokens": ex.n_target, "token_sha256": ids_sha256(ex.input_ids)}

    bank = {"kind": ANCHOR_KIND, "version": 1,
            "model": {"repo_id": recipe["model"]["repo_id"], "revision": recipe["model"]["revision"]},
            "harmful": [entry(f"h-{n}", p["prompt"], p["unsafe_response"], ex) for n, (k, p, ex) in enumerate(harmful)],
            "safe": [entry(f"s-{n}", p["prompt"], a, ex) for n, (k, p, a, ex) in enumerate(safe)],
            "counts": {"harmful": len(harmful), "safe": len(safe)}, "provenance": provenance}
    data = canonical_json(bank)
    (out / "anchors.json").write_bytes(data)
    index_of = {**{f"h-{n}": k for n, (k, _, _) in enumerate(harmful)},
                **{f"s-{n}": k for n, (k, _, _, _) in enumerate(safe)}}
    record = {"kind": RECORD_KIND, "version": 1, "complete": True, "anchor_file_sha256": _sha(data),
              "anchor_file_bytes": len(data), "counts": bank["counts"], "walk": walk, "drops": drops,
              "provenance": provenance,
              "anchors": [{"anchor_id": a["anchor_id"], "set": name, "list_index": index_of[a["anchor_id"]],
                           "prompt_sha256": _sha(a["prompt"].encode("utf-8")),
                           "response_sha256": _sha(a["response"].encode("utf-8")),
                           "prompt_tokens": a["prompt_tokens"], "target_tokens": a["target_tokens"],
                           "token_sha256": a["token_sha256"]}
                          for name in ("harmful", "safe") for a in bank[name]]}
    (out / "anchors.sealed.json").write_bytes(canonical_json(record))
    print(json.dumps({"anchor_file_sha256": _sha(data), "bytes": len(data), "counts": bank["counts"], "drops": drops,
                      "walked": len(walk)}))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--recipe", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    from experiments.safety_selection.loaders import real_loaders

    return run(pathlib.Path(args.prompts), pathlib.Path(args.recipe), pathlib.Path(args.out), real_loaders())


if __name__ == "__main__":
    sys.exit(main())
