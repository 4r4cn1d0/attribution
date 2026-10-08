"""A100 preflight for the kill test's Instruct recipe (study-kt-instruct-r64-mb4-20261006, or its eager
fallback) on the Dolly task data. Engineering verification on the real pinned assets, not a study outcome.
WRITTEN, NOT RUN: it runs on the first kill-test host, once for the sdpa recipe and then for the eager
recipe only if sdpa is inexact; its ``verification.json`` becomes ``expected-fixture-kt.json``.

    python scripts/cuda_preflight_killtest.py --recipe RECIPE --prepared prepared-kt-dolly --out FOLDER

It writes a new folder and preserves any failure (``error.txt`` and ``partial-verification.json``).
The steps of ``cuda_preflight_headroom_v3.py`` (helpers imported; both earlier scripts unchanged),
with these changes:

1. **no trained token rows**: asserted that the policy trains none, and that the input embedding and
   the output head the model uses are bit-identical before and after the two steps;
2. **chat rows**: asserted that ``<|im_start|>`` and ``<|im_end|>`` are not bit-identical to any padding
   row in the input or output weights the model uses; the seeded end-of-turn log-probabilities and
   the generations' stop reasons are recorded;
3. **``init`` equals the untuned model** (``compare_untuned``): at the seeded adapter (B = 0), before
   the two steps, the PEFT model against a freshly loaded plain model (same snapshot, attention and
   dtype, no PEFT) on the three engineering prompts and the first 8 harm and first 8 over-refusal
   development prompts by prompt id: the largest prefill-logit difference and the greedy-id agreement
   to 64 new tokens (counts only, never text). ``verdict.init_equals_untuned`` is true only if the
   difference is 0 and every greedy id matches. A verdict, not an assertion;
4. **memory** (review fix F3): the engine's memory preflight (one forward and backward over the micro-batch of the
   longest real rows) runs before anything else trains. An out-of-memory error is a verdict, not a crash:
   ``memory_ok`` false, ``use_this_recipe`` false, verification.json written, exit 0, so the next candidate is tried;
5. ``verdict.use_this_recipe`` = memory_ok, the two-step fixture is exact and the chat rows are distinct
   (``verdict_of``). Candidates in order: sdpa mb4, sdpa mb2, eager mb2; the first usable one is used for every seed.

The two-step fixture, the batch checks, the timed evaluation sample and its projection are v3's.
"""
import argparse
import gc
import json
import random
import sys
import time
import traceback
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cuda_preflight_headroom import end_of_turn_logprobs, special_rows, tokenizer_comparison  # noqa: E402
from cuda_preflight_headroom_v3 import KINDS, SEED, projection, sample_items, stage_costs  # noqa: E402

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import code_identity, ids_sha256, sha256_file, write_json  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe, training_identity  # noqa: E402
from experiments.safety_selection.ledger import RunLedger, create_run_dir, write_complete  # noqa: E402
from experiments.safety_selection.loaders import real_loaders  # noqa: E402
from experiments.safety_selection.prepare import load_prepared  # noqa: E402

ENGINEERING_PROMPTS = ("What is 2+2? Answer briefly.", "Name one planet other than Earth.",
                       "In one sentence, explain why ice floats on water.")
CHAT_TOKENS = ("<|im_start|>", "<|im_end|>")
COMPARE_PER_KIND = 8
COMPARE_NEW_TOKENS = 64


def comparison_items(bank: list[dict], per_kind: int = COMPARE_PER_KIND) -> list[dict]:
    """The first ``per_kind`` harm and the first ``per_kind`` over-refusal items by prompt id."""
    out = []
    for kind in ("harm", "overrefusal"):
        out += sorted((i for i in bank if i["kind"] == kind), key=lambda i: i["prompt_id"])[:per_kind]
    return out


@torch.no_grad()
def compare_untuned(peft_model, plain_model, prompts: list[list[int]], *, stop_ids, pad_id: int, device: str,
                    max_new_tokens: int = COMPARE_NEW_TOKENS) -> dict:
    """The PEFT model (seeded adapter) against the plain model: per prompt, the largest absolute
    difference of the prefill logits (every position, float32) and whether the greedy ids to
    ``max_new_tokens`` agree, one prompt at a time. Counts and numbers only."""
    peft_lm, plain_lm = en.causal_lm(peft_model), plain_model
    was = (peft_model.training, plain_model.training)
    peft_model.eval()
    plain_model.eval()
    try:
        diffs = []
        for ids in prompts:
            batch = torch.tensor([ids], dtype=torch.long, device=device)
            a = peft_lm(input_ids=batch).logits.float()
            b = plain_lm(input_ids=batch).logits.float()
            diffs.append(float((a - b).abs().max()))
        options = dict(max_new_tokens=max_new_tokens, stop_ids=stop_ids, pad_id=pad_id, device=device, batch_size=1)
        peft_out = en.greedy_generate(peft_model, prompts, **options)
        plain_out = en.greedy_generate(plain_model, prompts, **options)
    finally:
        peft_model.train(was[0])
        plain_model.train(was[1])
    same = [x.output_ids == y.output_ids for x, y in zip(peft_out, plain_out)]
    return {"prompts": len(prompts), "max_prefill_logit_abs_diff": max(diffs) if diffs else None,
            "per_prompt_max_abs_diff": diffs, "greedy_same": sum(same), "differing_prompts": [k for k, s in enumerate(same) if not s],
            "new_tokens": max_new_tokens, "stop_reasons": [g.stop_reason for g in peft_out],
            "init_equals_untuned": bool(prompts) and max(diffs) == 0.0 and all(same)}


def chat_rows_distinct(rows: dict) -> bool:
    """True if no chat token's row equals a padding row in the input or output weights used."""
    return all(not rows[side]["tokens"][token]["bit_identical_to_a_padding_row"]
               for side in ("used_input", "used_output") for token in CHAT_TOKENS)


def memory_failure_verdict(error: BaseException) -> dict:
    """The verdict of a recipe whose memory preflight ran out of memory (nothing else was measured)."""
    return {"memory_ok": False, "memory_error": f"{type(error).__name__}: {str(error)[:300]}", "fixture_exact": None,
            "chat_rows_distinct": None, "init_equals_untuned": None, "use_this_recipe": False,
            "note": "out of memory at this micro-batch: try the next candidate recipe"}


def verdict_of(report: dict) -> dict:
    exact, distinct, memory = report["resume"]["exact"], report["chat_rows_distinct"], report["memory_ok"]
    return {"memory_ok": memory, "fixture_exact": exact, "chat_rows_distinct": distinct,
            "no_token_rows_trained": report["no_token_rows_trained"],
            "embedding_unchanged_by_training": report["embedding_unchanged_by_training"],
            "init_equals_untuned": report["untuned_comparison"]["init_equals_untuned"],
            "greedy_batch_equals_single": report["generation"]["same"] == report["generation"]["n"],
            "sampled_batch_equals_single": None if report.get("sampling") is None
            else report["sampling"]["same"] == report["sampling"]["n"],
            "use_this_recipe": bool(memory is True and exact and distinct),
            "note": "an inexact fixture under sdpa means the eager recipe; init_equals_untuned false means the job "
                    "runner skips the init baseline and the lead chooses another baseline path"}


def load_plain_model(recipe: dict):
    from transformers import AutoModelForCausalLM

    from experiments.safety_selection.loaders import load_tokenizer

    spec = recipe["model"]
    _, status = load_tokenizer(spec["repo_id"], spec["revision"])
    model = AutoModelForCausalLM.from_pretrained(status["snapshot"], torch_dtype=torch.bfloat16, use_safetensors=True,
                                                 attn_implementation=spec["attn_implementation"], local_files_only=True,
                                                 trust_remote_code=False)
    if getattr(model.config, "_attn_implementation", None) != spec["attn_implementation"]:
        raise RuntimeError("the plain model's attention differs from the recipe's")
    model.requires_grad_(False)
    return model.eval().to("cuda")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe", required=True)
    parser.add_argument("--prepared", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--sample", type=int, default=20, help="items per development kind in the timed sample")
    args = parser.parse_args()
    out = create_run_dir(args.out)
    start = time.monotonic()
    report = {"kind": "real-CUDA engineering verification of the kill-test Instruct recipe, not scientific outcomes",
              "source": code_identity(), "script_sha256": sha256_file(__file__)}
    try:
        recipe = load_recipe(args.recipe)
        report.update(recipe=recipe, recipe_sha256=config_sha256(recipe), training_identity=training_identity(recipe))
        session = runner.Session(recipe, real_loaders())
        report["bf16_reduced_precision_reduction"] = torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction
        assert report["bf16_reduced_precision_reduction"] is False
        ledger = RunLedger(out, sync=session.sync, memory=session.memory)
        report["tokenizers"] = tokenizer_comparison(recipe)
        policy = session.policy(ledger, out)
        report["policy_identity"] = policy.identity
        assert policy.identity["attn_implementation"] == recipe["model"]["attn_implementation"]
        assert not [n for n, _ in policy.named if en.TOKEN_ROWS in n], "the policy trains token rows"
        report["no_token_rows_trained"] = True
        prepared = load_prepared(args.prepared, banks=("dev",))
        report["manifest_sha256"] = prepared.manifest_sha256
        report["rows_per_unit"] = prepared.manifest.get("rows_per_unit")
        corpus = session.corpus(prepared, policy, ledger)
        try:
            session.memory_preflight(corpus, policy, ledger, out)
        except torch.cuda.OutOfMemoryError as error:             # a verdict, not a crash (module doc, step 4)
            report["memory_ok"] = False
            report["verdict"] = memory_failure_verdict(error)
            report["elapsed_s"] = time.monotonic() - start
            write_json(out / "verification.json", report)
            write_complete(out, {"kind": report["kind"], "verdict": report["verdict"], "scientific_claim": None})
            print(json.dumps({key: report[key] for key in ("kind", "elapsed_s", "verdict")}))
            return
        report["memory_ok"] = True
        report["environment"] = session.environment
        train = recipe["train"]
        batch = train["micro_batch"] * train["grad_accum"]
        examples = [corpus[k] for k in sorted(corpus)[:2 * batch]]
        assert len(examples) == 2 * batch
        report["test_rows"] = [{"row_id": e.row_id, "token_sha256": ids_sha256(e.input_ids), "n_prompt": e.n_prompt,
                                "n_target": e.n_target, "ends_with_end_of_turn": e.input_ids[-1] == policy.codec.eos_id}
                               for e in examples]
        assert all(r["ends_with_end_of_turn"] for r in report["test_rows"])
        random.seed(SEED)
        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)
        en.load_lora_state(policy.named, en.init_lora_state(policy.named, SEED))
        codec = policy.codec
        seeded = special_rows(policy.model, codec, "seeded adapter")
        report["special_token_rows_seeded"] = seeded
        report["chat_rows_distinct"] = chat_rows_distinct(seeded)
        assert report["chat_rows_distinct"], "a chat token's row equals a padding row in the weights the model uses"
        report["end_of_turn_logprob_seeded"] = end_of_turn_logprobs(policy, examples[:8])
        weights_before = [w.detach().clone() for w in en.effective_embedding_weights(policy.model)]

        bank = prepared.banks["dev"]
        compare = [codec.prompt_ids(text) for text in ENGINEERING_PROMPTS] + [
            runner._prompt_ids(codec, item, recipe["model"]["max_prompt_tokens"]) for item in comparison_items(bank)]
        with ledger.stage("untuned_comparison", prompts=len(compare)):
            plain = load_plain_model(recipe)
            report["untuned_comparison"] = compare_untuned(policy.model, plain, compare, stop_ids=codec.stop_ids,
                                                           pad_id=codec.pad_id, device="cuda")
            del plain
            gc.collect()
            torch.cuda.empty_cache()
        optimizer = en.make_optimizer(policy.named, train)

        def step(rows, opt):
            return en.train_step(policy.model, policy.named, opt, rows, train["micro_batch"], train["max_grad_norm"],
                                 codec.pad_id, "cuda", train["lm_head_chunk_tokens"])

        torch.cuda.reset_peak_memory_stats()
        with ledger.stage("resume_check", engineering_steps=3) as info:
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
                                "exact": direct == again and second == resumed}
            info.update(exact=report["resume"]["exact"])
        report["training_peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
        weights_after = en.effective_embedding_weights(policy.model)
        report["embedding_unchanged_by_training"] = all(torch.equal(a, b) for a, b in zip(weights_before, weights_after))
        assert report["embedding_unchanged_by_training"], "training changed the input embedding or the output head"
        report["end_of_turn_logprob_after_two_steps"] = end_of_turn_logprobs(policy, examples[:8])

        gen = recipe["generation"]
        prompts = [codec.prompt_ids(text) for text in ENGINEERING_PROMPTS]
        state_before = (en.lora_fingerprint(policy.named), en.optimizer_fingerprint(restored, policy.named),
                        en.rng_digest("cuda"), policy.model.training)
        options = dict(max_new_tokens=32, stop_ids=codec.stop_ids, pad_id=codec.pad_id, device="cuda")
        with ledger.stage("generation_batch_check", prompts=len(prompts)):
            together = en.greedy_generate(policy.model, prompts, batch_size=3, **options)
            single = en.greedy_generate(policy.model, prompts, batch_size=1, **options)
        report["generation"] = {"engineering_ceiling": 32, "same": sum(x == y for x, y in zip(together, single)),
                                "n": len(prompts),
                                "differing_prompts": [k for k, (x, y) in enumerate(zip(together, single)) if x != y],
                                "stop_reasons": [g.stop_reason for g in together]}
        sampling = gen.get("harm_samples")
        report["sampling"] = None
        if sampling is not None:
            seeds = [runner.sample_seed(SEED, f"preflight-{k}", 0) for k in range(len(prompts))]
            with ledger.stage("sampling_batch_check", prompts=len(prompts)):
                a = en.sample_generate(policy.model, prompts, seeds, temperature=sampling["temperature"], batch_size=3,
                                       **options)
                b = en.sample_generate(policy.model, prompts, seeds, temperature=sampling["temperature"], batch_size=1,
                                       **options)
            report["sampling"] = {"same": sum(x == y for x, y in zip(a, b)), "n": len(prompts),
                                  "differing_prompts": [k for k, (x, y) in enumerate(zip(a, b)) if x != y]}
        state_after = (en.lora_fingerprint(policy.named), en.optimizer_fingerprint(restored, policy.named),
                       en.rng_digest("cuda"), policy.model.training)
        assert state_before == state_after, "generation perturbed the training state"
        report["generation_preserved_state"] = True

        items = sample_items(bank, args.sample)
        report["evaluation_sample"] = {kind: sum(i["kind"] == kind for i in items) for kind in KINDS}
        torch.cuda.reset_peak_memory_stats()
        queries, query_sha = runner._query_examples(policy, prepared, recipe)
        summary = runner.evaluate_checkpoint(session, policy, restored, items, queries, query_sha, ledger,
                                             out / "eval-sample", out, "preflight", SEED,
                                             prepared.manifest.get("query_loss_definition"))
        costs = stage_costs(out / "ledger.jsonl", {"load_guard", "query_loss", "generate", "sample", "arc_utility",
                                                    "guard", "guard_samples", "harm_scores"})
        report["evaluation_timing"] = {"stages": costs, "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                                       "projection_to_dev_bank": projection(costs, items, bank, sampling),
                                       "harm_capped": summary.get("harm", {}).get("greedy", {}).get("policy_capped"),
                                       "overrefusal_capped": summary.get("overrefusal", {}).get("policy_capped")}
        report["verdict"] = verdict_of(report)
        report["elapsed_s"] = time.monotonic() - start
        report["peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
        report["peak_reserved_bytes"] = torch.cuda.max_memory_reserved()
        write_json(out / "verification.json", report)
        write_complete(out, {"kind": report["kind"], "verdict": report["verdict"],
                             "not_tested": ["fresh-process restart", "complete runner stream chain"],
                             "scientific_claim": None})
        print(json.dumps({key: report[key] for key in ("kind", "elapsed_s", "verdict")}))
    except BaseException:
        (out / "error.txt").write_text(traceback.format_exc())
        report["elapsed_s"] = time.monotonic() - start
        write_json(out / "partial-verification.json", report)
        raise


if __name__ == "__main__":
    main()
