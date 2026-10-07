"""A100 preflight for the family probes (OLMo-2, Llama-3; brief multi-family-probe-engine-20261007, Item 4).
Engineering verification on the real pinned assets, not a study outcome. WRITTEN, NOT RUN: it runs on each probe's
host, once per candidate recipe of the probe's ladder, and the chosen candidate's ``verification.json`` becomes
``expected-fixture-probe.json`` in that probe's working kit.

    python scripts/cuda_preflight_family.py --recipe RECIPE --prepared PREPARED --out FOLDER

It writes a new folder and preserves any failure (``error.txt`` and ``partial-verification.json``). The kill-test
preflight (``cuda_preflight_killtest.py``, unchanged; its helpers are imported) with these changes:

1. **chat tokens from the template** (``derive_chat_tokens``): the ids of the joint render of a probe turn and a reply
   that are special ids of the codec (Qwen {151644, 151645}, OLMo-2 {100257}, Llama-3.1 {128000, 128006, 128007,
   128009}); an empty set refuses;
2. **comparison rows** (``comparison_rows``): the padding rows (ids at or above the tokenizer's length) when they exist
   (OLMo-2: 74), else the ``<|reserved_special_token_N|>`` rows minus the chat tokens and the pad (Llama-3 has no
   padding rows), else none. ``chat_rows_distinct`` = no chat row bit-identical to a comparison row, in the input and
   the output weights the model uses; with no comparison rows it is null and the recipe is not used;
3. **tokenizer check** (``tokenizer_check``): with ``model.tokenizer``, ``tokenizer_ok`` needs the same vocabulary,
   equal chat-token ids and the same chat template, or a model template that reads the clock (Llama-3.2-1B: the
   pinned 3.1 template replaces it, decision L1; recorded). The model's own tokenizer is never given to a codec;
4. **order**: memory preflight -> untuned comparison -> resume check -> batch checks -> the guard -> **the full-length
   generation check** (``full_length_check``: generation.batch_size copies of the longest development generation
   prompt, no stop ids, every row to max_new_tokens, with the optimizer state and the guard resident; peak memory,
   seconds, ms per step over the last 256 steps, allocator retries, ``ms_per_step_full``) -> the timed evaluation
   sample -> the BOS record. One ``except torch.cuda.OutOfMemoryError`` covers the full-length check and the timed
   sample: ``generation_memory_ok`` false is a verdict (exit 0), as ``memory_ok`` false is for the memory preflight;
5. **the BOS record** (only when the template starts with the BOS token; a record, never a change): the end-of-turn
   log-probability of the first 8 training rows and the greedy agreement on the engineering prompts, with and without
   the leading BOS;
6. **verdict**: ``use_this_recipe`` = memory_ok and generation_memory_ok and fixture exact and chat rows distinct and
   tokenizer_ok, and, for a generation batch other than recipe B's 32 (the ``-g16`` candidates; lead decision 4),
   ``batch_proof_ok``: greedy ids at the candidate's batch equal one-at-a-time ids on the first BATCH (by prompt id)
   development generation prompts, up to BATCH_PROOF_NEW_TOKENS new tokens with the recipe's stops
   (``batch_proof_prompts``). ``init_equals_untuned`` stays a verdict that never stops the preflight; the job runner
   acts on it;
7. **cap projection** (``cap_projection``; review fix 9): ``projected_job_upper_s`` = two evaluations (the untuned
   one and e1), each with every batch capped (ms_per_step_full x 2,049 x the engine's batch counts, plus the projected
   non-generation stages) + training (resume-check seconds per step x 38) + the job's overhead outside the ledger
   stages (this preflight's own time outside its stages, at least OVERHEAD_FLOOR_S, measured on the Qwen-7B check)
   + 900 s. The kit's wrapper adds the pod timer's stop, the orchestrator's cap gate refuses a job that does not fit,
   and the job runner refuses e1 when the init unit's measurements leave too little;
8. **early stop** (review fix 2): ``tokenizer_ok`` false, or a failed batch proof, ends the candidate with its
   verdict at once (exit 0), and the kit's wrapper skips the later candidates the failure also rules out.
"""
import argparse
import gc
import json
import math
import random
import sys
import time
import traceback
from pathlib import Path

import torch

RECIPE_B_GENERATION_BATCH = 32
BATCH_PROOF_NEW_TOKENS = 256

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cuda_preflight_headroom import end_of_turn_logprobs  # noqa: E402
from cuda_preflight_headroom_v3 import KINDS, SEED, projection, sample_items, stage_costs  # noqa: E402
from cuda_preflight_killtest import (ENGINEERING_PROMPTS, compare_untuned, comparison_items,  # noqa: E402
                                     load_plain_model, memory_failure_verdict)

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import code_identity, ids_sha256, sha256_bytes, sha256_file, write_json  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe, tokenizer_of, training_identity  # noqa: E402
from experiments.safety_selection.ledger import RunLedger, create_run_dir, write_complete  # noqa: E402
from experiments.safety_selection.loaders import load_tokenizer, real_loaders  # noqa: E402
from experiments.safety_selection.prepare import load_prepared  # noqa: E402
from experiments.safety_selection.textproc import TemplateError, chat_template_reads_clock, single_token_id  # noqa: E402

OVERHEAD_FLOOR_S = 1000                  # the Qwen-7B check: 936 s of its job fell outside the ledger stages
TRAINING_STEPS = 38                      # recipe B's e1 (4,800 rows / 128 per step, rounded up)
GREEDY_PROMPTS = 468                     # the development bank's generation prompts (harm, over-refusal, ToxicChat, ARC)
HARM_SAMPLES = 600                       # 200 harm prompts x 3
LAST_STEPS = 256
SAFETY_MARGIN_S = 900


def derive_chat_tokens(codec) -> dict[str, int]:
    """The special ids of the joint render of one probe turn and one reply, as {token text: id}."""
    joint = codec.conversation_ids("<<probe>>", "<<reply>>")
    ids = sorted({i for i in joint if i in codec.special_ids})
    if not ids:
        raise TemplateError("the chat template renders no special token: no chat rows to check")
    return {codec.decode([i]): i for i in ids}


def comparison_rows(tokenizer, n_rows: int, chat_ids, pad_id: int) -> tuple[str, list[int]]:
    """(kind, ids) of the rows the chat rows are compared with: padding rows, reserved special rows, or none."""
    size = len(tokenizer)
    if n_rows > size:
        return "padding", list(range(size, n_rows))
    added = getattr(tokenizer, "added_tokens_decoder", {}) or {}
    excluded = set(chat_ids) | {pad_id}
    reserved = sorted(int(i) for i, entry in added.items()
                      if str(getattr(entry, "content", "")).startswith("<|reserved_special_token_") and int(i) not in excluded)
    return ("reserved", reserved) if reserved else ("none", [])


def chat_rows_report(weights_in, weights_out, chat: dict[str, int], comparison: list[int]) -> dict:
    """``engine.token_row_report`` of the chat rows against the comparison rows, input and output side, and
    ``chat_rows_distinct`` (null when there is nothing to compare with)."""
    if not comparison:
        return {"used_input": None, "used_output": None, "chat_rows_distinct": None}
    out = {"used_input": en.token_row_report(weights_in, chat, comparison),
           "used_output": en.token_row_report(weights_out, chat, comparison)}
    out["chat_rows_distinct"] = all(not out[side]["tokens"][t]["bit_identical_to_a_padding_row"]
                                    for side in ("used_input", "used_output") for t in chat)
    return out


def tokenizer_check(recipe: dict, audit, own, chat: dict[str, int]) -> dict:
    """The audit tokenizer (the codec's) against the model's own; ``tokenizer_ok`` as in the module doc."""
    def template_hash(tok) -> str:
        template = getattr(tok, "chat_template", None) or ""
        return sha256_bytes(json.dumps(template, sort_keys=True).encode("utf-8"))

    own_ids = {}
    for token in chat:
        try:
            own_ids[token] = single_token_id(own, token)
        except TemplateError:
            own_ids[token] = None
    out = {"pinned_tokenizer": "tokenizer" in recipe["model"], "same_vocabulary": audit.get_vocab() == own.get_vocab(),
           "chat_token_ids": dict(chat), "own_chat_token_ids": own_ids, "same_chat_token_ids": own_ids == dict(chat),
           "audit_template_sha256": template_hash(audit), "own_template_sha256": template_hash(own),
           "own_template_reads_clock": chat_template_reads_clock(own)}
    out["same_chat_template"] = out["audit_template_sha256"] == out["own_template_sha256"]
    out["tokenizer_ok"] = (not out["pinned_tokenizer"]) or bool(
        out["same_vocabulary"] and out["same_chat_token_ids"] and (out["same_chat_template"] or out["own_template_reads_clock"]))
    return out


def full_length_check(model, prompt: list[int], *, batch: int, max_new_tokens: int, pad_id: int, device: str,
                      clock=time.monotonic, stats=None) -> dict:
    """``batch`` copies of ``prompt``, no stop ids, every row to ``max_new_tokens``: the worst generation batch.
    Steps are timed through the engine's per-step ``check`` callback (the engine is unchanged)."""
    marks = []
    start = clock()
    out = en.greedy_generate(model, [list(prompt)] * batch, max_new_tokens=max_new_tokens, stop_ids=[], pad_id=pad_id,
                             device=device, batch_size=batch, check=lambda what: marks.append(clock()))
    seconds = clock() - start
    steps = [b - a for a, b in zip(marks, marks[1:])]
    last = steps[-LAST_STEPS:]
    ms_last = 1000 * sum(last) / len(last) if last else None
    ms_full = max(1000 * seconds / max_new_tokens, ms_last or 0.0)
    record = {"batch": batch, "prompt_tokens": len(prompt), "max_new_tokens": max_new_tokens, "seconds": seconds,
              "rows_capped": sum(g.stop_reason == en.STOP_CAP for g in out), "ms_per_step_last_256": ms_last,
              "ms_per_step_full": ms_full}
    if stats is not None:
        record.update(stats())
    return record


def cap_projection(ms_per_step_full: float, evaluation_projection: dict, resume_seconds: float, batch: int,
                   overhead_s: float, resume_steps: int = 3) -> dict:
    """``projected_job_upper_s`` (module doc, step 7): both evaluations with every batch at the cap, training, the
    job's overhead (at least OVERHEAD_FLOOR_S) and the margin."""
    batches = math.ceil(GREEDY_PROMPTS / batch) + math.ceil(HARM_SAMPLES / batch)
    stages = evaluation_projection["stages"]
    other = sum(v["projected_seconds"] for k, v in stages.items() if k not in ("generate", "sample"))
    evaluation_upper = ms_per_step_full / 1000 * 2049 * batches + other
    training = resume_seconds / resume_steps * TRAINING_STEPS
    overhead = max(overhead_s, OVERHEAD_FLOOR_S)
    return {"batches_capped": batches, "untuned_projected_s": evaluation_projection["projected_evaluation_seconds"],
            "untuned_upper_s": evaluation_upper, "e1_upper_s": evaluation_upper, "training_s": training,
            "overhead_measured_s": overhead_s, "overhead_s": overhead, "margin_s": SAFETY_MARGIN_S,
            "projected_job_upper_s": 2 * evaluation_upper + training + overhead + SAFETY_MARGIN_S}


def outside_stages_s(ledger_path: Path, elapsed_s: float) -> float:
    """This process's time so far outside its ledger stages (model loads and the like)."""
    rows = [json.loads(line) for line in ledger_path.read_text().splitlines() if line.strip()] if ledger_path.exists() else []
    return max(0.0, elapsed_s - sum(r["seconds"] for r in rows if r.get("stage") and isinstance(r.get("seconds"), (int, float))))


def stop_verdict(report: dict, failed: str) -> dict:
    """The verdict of a candidate that ends early (review fix 2): ``failed`` is false, nothing later ran."""
    proof = report.get("batch_proof") or {}
    return {"memory_ok": report.get("memory_ok"), "generation_memory_ok": None,
            "fixture_exact": (report.get("resume") or {}).get("exact"),
            "chat_rows_distinct": (report.get("chat_rows") or {}).get("chat_rows_distinct"),
            "tokenizer_ok": (report.get("tokenizers") or {}).get("tokenizer_ok"),
            "batch_proof_ok": None if not proof else proof.get("same") == proof.get("n") and bool(proof.get("n")),
            "init_equals_untuned": (report.get("untuned_comparison") or {}).get("init_equals_untuned"),
            "use_this_recipe": False, "stopped_after": failed,
            "note": f"{failed} false: the candidate ends here; the wrapper skips the later candidates it rules out"}


def batch_proof_prompts(items: list[dict], prompt_ids, n: int) -> list[list[int]]:
    """The first N generation items by prompt id, as prompt ids (deterministic; their lengths differ, so the batch
    is left-padded as in a real evaluation)."""
    chosen = sorted((i for i in items if i["kind"] in runner.GENERATION_KINDS), key=lambda i: i["prompt_id"])[:n]
    if len(chosen) < n:
        raise ValueError(f"only {len(chosen)} generation prompts for a batch proof of {n}")
    return [prompt_ids(i) for i in chosen]


def verdict_of(report: dict) -> dict:
    exact = report["resume"]["exact"]
    parts = {"memory_ok": report["memory_ok"], "generation_memory_ok": report["generation_memory_ok"],
             "fixture_exact": exact, "chat_rows_distinct": report["chat_rows"]["chat_rows_distinct"],
             "tokenizer_ok": report["tokenizers"]["tokenizer_ok"]}
    if report.get("generation_batch", RECIPE_B_GENERATION_BATCH) != RECIPE_B_GENERATION_BATCH:   # lead decision 4
        proof = report.get("batch_proof") or {}
        parts["batch_proof_ok"] = bool(proof.get("n")) and proof.get("same") == proof.get("n")
    return {**parts, "init_equals_untuned": report["untuned_comparison"]["init_equals_untuned"],
            "comparison_kind": report["comparison_kind"],
            "greedy_batch_equals_single": report["generation"]["same"] == report["generation"]["n"],
            "sampled_batch_equals_single": None if report.get("sampling") is None
            else report["sampling"]["same"] == report["sampling"]["n"],
            "use_this_recipe": all(v is True for v in parts.values()),
            "note": "init_equals_untuned false or null stops the probe after the preflight (no baseline, no probe)"}


def generation_failure_verdict(report: dict, error: BaseException) -> dict:
    """The verdict of a candidate that ran out of memory in the full-length check or the timed sample."""
    return {"memory_ok": True, "generation_memory_ok": False, "generation_memory_error": f"{type(error).__name__}: {str(error)[:300]}",
            "fixture_exact": report.get("resume", {}).get("exact"), "chat_rows_distinct": report.get("chat_rows", {}).get("chat_rows_distinct"),
            "tokenizer_ok": report.get("tokenizers", {}).get("tokenizer_ok"),
            "init_equals_untuned": report.get("untuned_comparison", {}).get("init_equals_untuned"),
            "use_this_recipe": False, "note": "out of memory while generating at this batch: a later candidate with a "
                                              "smaller generation batch may pass"}


def generation_phase(report: dict, full, sample):
    """Run the full-length check (``full()``) and then the timed sample (``sample()``); an out-of-memory error in
    either is a verdict (``generation_memory_ok`` false), not a crash. Returns the sample's summary, or None."""
    try:
        report["full_length"] = full()
        summary = sample()
    except torch.cuda.OutOfMemoryError as error:
        report["generation_memory_ok"] = False
        report["verdict"] = generation_failure_verdict(report, error)
        return None
    report["generation_memory_ok"] = True
    return summary


def _finish(out: Path, report: dict, start: float) -> None:
    report["elapsed_s"] = time.monotonic() - start
    if torch.cuda.is_available():
        report["peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
        report["peak_reserved_bytes"] = torch.cuda.max_memory_reserved()
    write_json(out / "verification.json", report)
    write_complete(out, {"kind": report["kind"], "verdict": report["verdict"],
                         "not_tested": ["fresh-process restart", "complete runner stream chain"], "scientific_claim": None})
    print(json.dumps({key: report[key] for key in ("kind", "elapsed_s", "verdict")}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe", required=True)
    parser.add_argument("--prepared", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--sample", type=int, default=20, help="items per development kind in the timed sample")
    args = parser.parse_args()
    out = create_run_dir(args.out)
    start = time.monotonic()
    report = {"kind": "real-CUDA engineering verification of a family-probe recipe, not scientific outcomes",
              "source": code_identity(), "script_sha256": sha256_file(__file__)}
    try:
        recipe = load_recipe(args.recipe)
        report.update(recipe=recipe, recipe_sha256=config_sha256(recipe), training_identity=training_identity(recipe))
        session = runner.Session(recipe, real_loaders())
        report["bf16_reduced_precision_reduction"] = torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction
        assert report["bf16_reduced_precision_reduction"] is False
        ledger = RunLedger(out, sync=session.sync, memory=session.memory)
        policy = session.policy(ledger, out)
        report["policy_identity"] = policy.identity
        assert policy.identity["attn_implementation"] == recipe["model"]["attn_implementation"]
        assert not [n for n, _ in policy.named if en.TOKEN_ROWS in n], "the policy trains token rows"
        report["no_token_rows_trained"] = True
        codec = policy.codec
        chat = derive_chat_tokens(codec)
        report["chat_tokens"] = chat
        audit, _ = load_tokenizer(*tokenizer_of(recipe))
        own, _ = load_tokenizer(recipe["model"]["repo_id"], recipe["model"]["revision"])
        report["tokenizers"] = tokenizer_check(recipe, audit, own, chat)
        if report["tokenizers"]["tokenizer_ok"] is not True:            # review fix 2: no later step can change it
            report["verdict"] = stop_verdict(report, "tokenizer_ok")
            _finish(out, report, start)
            return
        prepared = load_prepared(args.prepared, banks=("dev",))
        report["manifest_sha256"] = prepared.manifest_sha256
        corpus = session.corpus(prepared, policy, ledger)
        try:
            session.memory_preflight(corpus, policy, ledger, out)
        except torch.cuda.OutOfMemoryError as error:
            report["memory_ok"] = False
            report["verdict"] = {**memory_failure_verdict(error), "generation_memory_ok": None,
                                 "tokenizer_ok": report["tokenizers"]["tokenizer_ok"]}
            _finish(out, report, start)
            return
        report["memory_ok"] = True
        report["environment"] = session.environment
        train = recipe["train"]
        batch = train["micro_batch"] * train["grad_accum"]
        examples = [corpus[k] for k in sorted(corpus)[:2 * batch]]
        assert len(examples) == 2 * batch
        report["test_rows"] = [{"row_id": e.row_id, "token_sha256": ids_sha256(e.input_ids), "n_prompt": e.n_prompt,
                                "n_target": e.n_target, "ends_with_end_of_turn": e.input_ids[-1] == codec.eos_id}
                               for e in examples]
        assert all(r["ends_with_end_of_turn"] for r in report["test_rows"])
        random.seed(SEED)
        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)
        en.load_lora_state(policy.named, en.init_lora_state(policy.named, SEED))
        used_in, used_out = en.effective_embedding_weights(policy.model)
        kind, rows = comparison_rows(codec.tokenizer, used_in.shape[0], chat.values(), codec.pad_id)
        report["comparison_kind"], report["comparison_rows"] = kind, len(rows)
        report["chat_rows"] = chat_rows_report(used_in, used_out, chat, rows)
        report["end_of_turn_logprob_seeded"] = end_of_turn_logprobs(policy, examples[:8])
        weights_before = [w.detach().clone() for w in (used_in, used_out)]

        bank = prepared.banks["dev"]
        max_prompt = recipe["model"]["max_prompt_tokens"]
        compare = [codec.prompt_ids(text) for text in ENGINEERING_PROMPTS] + [
            runner._prompt_ids(codec, item, max_prompt) for item in comparison_items(bank)]
        with ledger.stage("untuned_comparison", prompts=len(compare)):
            plain = load_plain_model(recipe)
            report["untuned_comparison"] = compare_untuned(policy.model, plain, compare, stop_ids=codec.stop_ids,
                                                           pad_id=codec.pad_id, device="cuda")
            del plain
            gc.collect()
            torch.cuda.empty_cache()
        optimizer = en.make_optimizer(policy.named, train)

        def step(rows_, opt):
            return en.train_step(policy.model, policy.named, opt, rows_, train["micro_batch"], train["max_grad_norm"],
                                 codec.pad_id, "cuda", train["lm_head_chunk_tokens"],
                                 train.get("loss_weighting", en.EXAMPLE_MEAN))   # the recipe's loss (round 5)

        torch.cuda.reset_peak_memory_stats()
        with ledger.stage("resume_check", engineering_steps=3) as info:
            t0 = time.monotonic()
            first = step(examples[:batch], optimizer)
            en.save_state(out / "after-first-step", policy.named, optimizer, "cuda", {"engineering": True, "step": 1})
            saved_rng = en.rng_digest("cuda")
            second = step(examples[batch:], optimizer)
            direct = {"adapter": en.lora_fingerprint(policy.named),
                      "optimizer": en.optimizer_fingerprint(optimizer, policy.named), "rng": en.rng_digest("cuda")}
            del optimizer
            gc.collect()
            restored = en.make_optimizer(policy.named, train)
            random.random()
            torch.rand(3)
            torch.rand(3, device="cuda")
            assert en.rng_digest("cuda") != saved_rng, "the RNG challenge did not change the state"
            en.load_state(out / "after-first-step", policy.named, restored, "cuda")
            assert en.rng_digest("cuda") == saved_rng, "the saved RNG state was not restored after the perturbation"
            report["rng_restoration_challenged"] = True
            resumed = step(examples[batch:], restored)
            again = {"adapter": en.lora_fingerprint(policy.named),
                     "optimizer": en.optimizer_fingerprint(restored, policy.named), "rng": en.rng_digest("cuda")}
            report["resume"] = {"direct": direct, "resumed": again, "loss_first": first["loss"],
                                "loss_direct": second["loss"], "loss_resumed": resumed["loss"],
                                "exact": direct == again and second == resumed, "seconds": time.monotonic() - t0}
            info.update(exact=report["resume"]["exact"])
        report["training_peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
        weights_after = en.effective_embedding_weights(policy.model)
        report["embedding_unchanged_by_training"] = all(torch.equal(a, b) for a, b in zip(weights_before, weights_after))
        assert report["embedding_unchanged_by_training"], "training changed the input embedding or the output head"
        report["end_of_turn_logprob_after_two_steps"] = end_of_turn_logprobs(policy, examples[:8])

        gen = recipe["generation"]
        prompts = [codec.prompt_ids(text) for text in ENGINEERING_PROMPTS]
        options = dict(max_new_tokens=32, stop_ids=codec.stop_ids, pad_id=codec.pad_id, device="cuda")
        with ledger.stage("generation_batch_check", prompts=len(prompts)):
            together = en.greedy_generate(policy.model, prompts, batch_size=3, **options)
            single = en.greedy_generate(policy.model, prompts, batch_size=1, **options)
        report["generation"] = {"engineering_ceiling": 32, "same": sum(x == y for x, y in zip(together, single)),
                                "n": len(prompts), "differing_prompts": [k for k, (x, y) in enumerate(zip(together, single)) if x != y],
                                "stop_reasons": [g.stop_reason for g in together]}
        sampling = gen.get("harm_samples")
        report["sampling"] = None
        if sampling is not None:
            seeds = [runner.sample_seed(SEED, f"preflight-{k}", 0) for k in range(len(prompts))]
            with ledger.stage("sampling_batch_check", prompts=len(prompts)):
                a = en.sample_generate(policy.model, prompts, seeds, temperature=sampling["temperature"], batch_size=3, **options)
                b = en.sample_generate(policy.model, prompts, seeds, temperature=sampling["temperature"], batch_size=1, **options)
            report["sampling"] = {"same": sum(x == y for x, y in zip(a, b)), "n": len(prompts),
                                  "differing_prompts": [k for k, (x, y) in enumerate(zip(a, b)) if x != y]}
        report["generation_batch"] = gen["batch_size"]
        report["batch_proof"] = None
        if gen["batch_size"] != RECIPE_B_GENERATION_BATCH:     # lead decision 4: a batch-16 candidate needs the proof
            proof_prompts = batch_proof_prompts(bank, lambda i: runner._prompt_ids(codec, i, max_prompt), gen["batch_size"])
            proof_options = {**options, "max_new_tokens": BATCH_PROOF_NEW_TOKENS}
            with ledger.stage("generation_batch_proof", prompts=len(proof_prompts), batch=gen["batch_size"]):
                together = en.greedy_generate(policy.model, proof_prompts, batch_size=gen["batch_size"], **proof_options)
                single = en.greedy_generate(policy.model, proof_prompts, batch_size=1, **proof_options)
            report["batch_proof"] = {"batch": gen["batch_size"], "new_tokens": BATCH_PROOF_NEW_TOKENS,
                                     "same": sum(x == y for x, y in zip(together, single)), "n": len(proof_prompts),
                                     "differing_prompts": [k for k, (x, y) in enumerate(zip(together, single)) if x != y],
                                     "capped": sum(g.stop_reason == en.STOP_CAP for g in together)}
            if report["batch_proof"]["same"] != report["batch_proof"]["n"]:     # review fix 2: end the candidate
                report["verdict"] = stop_verdict(report, "batch_proof_ok")
                _finish(out, report, start)
                return

        session.guard(ledger, out)                       # resident from here, as in a real evaluation
        generation_items = [i for i in bank if i["kind"] in runner.GENERATION_KINDS]
        longest = max((runner._prompt_ids(codec, i, max_prompt) for i in generation_items), key=len)
        items = sample_items(bank, args.sample)
        report["evaluation_sample"] = {kind_: sum(i["kind"] == kind_ for i in items) for kind_ in KINDS}
        def full():
            torch.cuda.reset_peak_memory_stats()
            with ledger.stage("full_length_check", batch=gen["batch_size"], new_tokens=gen["max_new_tokens"]):
                return full_length_check(
                    policy.model, longest, batch=gen["batch_size"], max_new_tokens=gen["max_new_tokens"],
                    pad_id=codec.pad_id, device="cuda",
                    stats=lambda: {"peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                                   "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
                                   "num_alloc_retries": torch.cuda.memory_stats().get("num_alloc_retries")})

        def sample():
            torch.cuda.reset_peak_memory_stats()
            queries, query_sha = runner._query_examples(policy, prepared, recipe)
            return runner.evaluate_checkpoint(session, policy, restored, items, queries, query_sha, ledger,
                                              out / "eval-sample", out, "preflight", SEED,
                                              prepared.manifest.get("query_loss_definition"))

        summary = generation_phase(report, full, sample)
        if summary is None:                                  # out of memory while generating: a verdict, exit 0
            _finish(out, report, start)
            return
        costs = stage_costs(out / "ledger.jsonl", {"load_guard", "query_loss", "generate", "sample", "arc_utility",
                                                    "guard", "guard_samples", "harm_scores"})
        evaluation = projection(costs, items, bank, sampling)
        report["evaluation_timing"] = {"stages": costs, "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                                       "projection_to_dev_bank": evaluation,
                                       "harm_capped": summary.get("harm", {}).get("greedy", {}).get("policy_capped"),
                                       "overrefusal_capped": summary.get("overrefusal", {}).get("policy_capped")}
        report["cap_projection"] = cap_projection(report["full_length"]["ms_per_step_full"], evaluation,
                                                  report["resume"]["seconds"], gen["batch_size"],
                                                  outside_stages_s(out / "ledger.jsonl", time.monotonic() - start))

        bos = getattr(codec.tokenizer, "bos_token_id", None)
        if bos is not None and prompts[0][:1] == [bos]:               # a record only; prompts never change
            eot_with = end_of_turn_logprobs(policy, examples[:8])
            stripped = [en.TrainExample(e.row_id, tuple(e.input_ids[1:]), e.n_prompt - 1) for e in examples[:8]]
            eot_without = end_of_turn_logprobs(policy, stripped)
            with_bos = en.greedy_generate(policy.model, prompts, batch_size=1, **{**options, "max_new_tokens": 64})
            without_bos = en.greedy_generate(policy.model, [p[1:] for p in prompts], batch_size=1,
                                             **{**options, "max_new_tokens": 64})
            report["bos_record"] = {"bos_id": bos, "end_of_turn_logprob_with": eot_with, "end_of_turn_logprob_without": eot_without,
                                    "greedy_same_64": sum(x == y for x, y in zip(with_bos, without_bos)),
                                    "stop_reasons_with": [g.stop_reason for g in with_bos],
                                    "stop_reasons_without": [g.stop_reason for g in without_bos]}
        report["verdict"] = verdict_of(report)
        _finish(out, report, start)
    except BaseException:
        (out / "error.txt").write_text(traceback.format_exc())
        report["elapsed_s"] = time.monotonic() - start
        write_json(out / "partial-verification.json", report)
        raise


if __name__ == "__main__":
    main()
