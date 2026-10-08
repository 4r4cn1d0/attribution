"""A100 preflight for headroom v2 (prepared data v3, recipe study-v3-headroom-pc2 or a fallback).
Engineering verification on the real pinned assets, not a study outcome.
WRITTEN, NOT RUN: it runs on the validation pod, once per candidate recipe (pc2: sdpa, micro-batch
8 x 1; pc2-mb4: sdpa, 4 x 2; pc2-eager: eager, 4 x 2), and its ``verification.json`` chooses the
recipe and becomes the expected fixture that later hosts reproduce.

    python scripts/cuda_preflight_headroom_v3.py --recipe RECIPE --prepared prepared-v3-inj10 --out FOLDER \\
        [--rewrite-config experiments/safety_selection/configs/headroom-rewrite-pc2-20261005.json]

It writes a new folder and preserves any failure (``error.txt`` and ``partial-verification.json``).
Everything of ``cuda_preflight_headroom.py`` (helpers imported from it), under this recipe's
attention and micro-batch:

1. the policy loads as the recipe says (attention reported by the loaded model), every training
   row (injected rows included) encodes as the prepared audit says, and the memory preflight
   passes at this micro-batch;
2. **the two-step fixture**: two optimizer steps directly and again after saving and restoring the
   state behind a perturbed RNG. Its exactness (``resume.exact``) is RECORDED, not asserted, so an
   inexact result under sdpa still yields every other measurement; ``verdict.fixture_exact`` says it,
   and a recipe whose fixture is inexact must not be used (keep eager: pc2-eager);
3. **asserted**, as before: after the two steps the trained ``<|im_start|>`` and ``<|im_end|>`` rows
   differ bit for bit from every padding row in the input and output weights the model uses;
4. greedy generation in batches equals one prompt at a time (recorded, with the differing prompts),
   and generation leaves the training state untouched (asserted);
5. **sampled answers** (``engine.sample_generate``): the same seeds in one batch and one at a time
   (recorded; floating-point differences between batch shapes can change a draw on CUDA);
6. **the evaluation sample, timed**: ``runner.evaluate_checkpoint`` on the first ``--sample`` items
   (by prompt id) of each development kind (harm with its sampled answers, over-refusal, ToxicChat,
   ARC generation; twice as many ARC forced-choice questions) after the two steps. Per stage:
   seconds, items and peak memory; and a projection to the full development bank (seconds per item
   times the bank's items per kind). The model has trained two steps only, so most answers run to the
   cap: the projection is an upper bound for generation, not an estimate of a trained model's cost;
7. optional ``--rewrite-config``: the rewrite generator on eight pool rows' requests, batched and
   one at a time (recorded), with seconds and peak memory.
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
from cuda_preflight_headroom import (end_of_turn_logprobs, special_rows, tokenizer_comparison,  # noqa: E402
                                     trained_rows)

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import code_identity, ids_sha256, sha256_file, write_json  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe, training_identity  # noqa: E402
from experiments.safety_selection.ledger import RunLedger, create_run_dir, write_complete  # noqa: E402
from experiments.safety_selection.loaders import real_loaders  # noqa: E402
from experiments.safety_selection.prepare import load_prepared  # noqa: E402

SEED = 1101
KINDS = ("harm", "overrefusal", "safety", "arc_generation", "arc_utility")


def sample_items(bank: list[dict], per_kind: int) -> list[dict]:
    """The first items by prompt id of each kind (twice as many ARC forced-choice questions)."""
    out = []
    for kind in KINDS:
        items = sorted((i for i in bank if i["kind"] == kind), key=lambda i: i["prompt_id"])
        out += items[:2 * per_kind if kind == "arc_utility" else per_kind]
    return out


def stage_costs(ledger_path: Path, names: set[str]) -> list[dict]:
    rows = [json.loads(line) for line in ledger_path.read_text().splitlines() if line.strip()]
    return [{"stage": r["stage"], "seconds": r.get("seconds"), "memory": r.get("memory", {}),
             **{k: r[k] for k in ("prompts", "answers", "items", "questions", "queries") if k in r}}
            for r in rows if r.get("stage") in names]


def projection(costs: list[dict], sample: list[dict], bank: list[dict], sampling: dict | None) -> dict:
    """Seconds per evaluated unit in the sample times the full bank's units (an upper bound for
    generation after two training steps; see the module doc)."""
    count = lambda items, kind: sum(i["kind"] == kind for i in items)  # noqa: E731
    gen_kinds = ("harm", "overrefusal", "safety", "arc_generation")
    per_answer = (sampling or {}).get("count", 0)
    units = {
        "generate": (sum(count(sample, k) for k in gen_kinds), sum(count(bank, k) for k in gen_kinds)),
        "sample": (count(sample, "harm") * per_answer, count(bank, "harm") * per_answer),
        "arc_utility": (count(sample, "arc_utility"), count(bank, "arc_utility")),
        "guard": (sum(count(sample, k) for k in gen_kinds), sum(count(bank, k) for k in gen_kinds)),
        "guard_samples": (count(sample, "harm") * per_answer, count(bank, "harm") * per_answer),
        "harm_scores": (count(sample, "harm") * (1 + per_answer), count(bank, "harm") * (1 + per_answer)),
    }
    out, total = {}, 0.0
    for c in costs:
        if c["stage"] in units and units[c["stage"]][0]:
            done, full = units[c["stage"]]
            seconds = c["seconds"] / done * full
            out[c["stage"]] = {"sample_units": done, "bank_units": full, "sample_seconds": c["seconds"],
                               "projected_seconds": seconds}
            total += seconds
    return {"stages": out, "projected_evaluation_seconds": total,
            "note": "per-unit time of the sample times the development bank; generation after two steps mostly "
                    "runs to the cap, so this is an upper bound for generation"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe", required=True)
    parser.add_argument("--prepared", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--sample", type=int, default=20, help="items per development kind in the timed sample")
    parser.add_argument("--rewrite-config", help="also check the rewrite generator under this config")
    args = parser.parse_args()
    out = create_run_dir(args.out)
    start = time.monotonic()
    report = {"kind": "real-CUDA engineering verification of the headroom-v2 recipe, not scientific outcomes",
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
        prepared = load_prepared(args.prepared, banks=("dev",))
        report["manifest_sha256"] = prepared.manifest_sha256
        report["injected_rows"] = prepared.manifest["corpus"].get("injected_rows")
        corpus = session.corpus(prepared, policy, ledger)
        session.memory_preflight(corpus, policy, ledger, out)
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
        report["special_token_rows_seeded"] = special_rows(policy.model, policy.codec, "seeded adapter")
        seeded_rows = trained_rows(policy.named)
        report["end_of_turn_logprob_seeded"] = end_of_turn_logprobs(policy, examples[:8])
        optimizer = en.make_optimizer(policy.named, train)

        def step(rows, opt):
            return en.train_step(policy.model, policy.named, opt, rows, train["micro_batch"], train["max_grad_norm"],
                                 policy.codec.pad_id, "cuda", train["lm_head_chunk_tokens"])

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
        report["end_of_turn_logprob_after_two_steps"] = end_of_turn_logprobs(policy, examples[:8])
        after_rows = special_rows(policy.model, policy.codec, "after the two steps")
        report["special_token_rows_after_two_steps"] = after_rows
        moved = trained_rows(policy.named)
        trained_ids = policy.identity.get("trainable_token_ids") or {}
        assert trained_ids and seeded_rows is not None, "the recipe trains no token rows"
        report["trained_rows_change"] = {
            "parameter": moved[0], "token_ids": trained_ids,
            "max_abs_change": float((moved[1] - seeded_rows[1]).abs().max()),
            "per_row_l2_change": [float(x) for x in (moved[1] - seeded_rows[1]).norm(dim=1)]}
        for side in ("used_input", "used_output"):
            for token in trained_ids:
                assert not after_rows[side]["tokens"][token]["bit_identical_to_a_padding_row"], \
                    f"{token} still equals a padding row in the {side} weights after two steps"
        report["trained_rows_separated_from_padding"] = True

        codec, gen = policy.codec, recipe["generation"]
        prompts = [codec.prompt_ids(text) for text in
                   ("What is 2+2? Answer briefly.", "Name one planet other than Earth.",
                    "In one sentence, explain why ice floats on water.")]
        state_before = (en.lora_fingerprint(policy.named), en.optimizer_fingerprint(restored, policy.named),
                        en.rng_digest("cuda"), policy.model.training)
        options = dict(max_new_tokens=32, stop_ids=codec.stop_ids, pad_id=codec.pad_id, device="cuda")
        with ledger.stage("generation_batch_check", prompts=len(prompts)):
            together = en.greedy_generate(policy.model, prompts, batch_size=3, **options)
            single = en.greedy_generate(policy.model, prompts, batch_size=1, **options)
        report["generation"] = {"engineering_ceiling": 32, "same": sum(x == y for x, y in zip(together, single)),
                                "n": len(prompts), "differing_prompts": [k for k, (x, y) in enumerate(zip(together, single))
                                                                         if x != y],
                                "stop_reasons": [g.stop_reason for g in together]}
        sampling = gen.get("harm_samples")
        if sampling is not None:
            seeds = [runner.sample_seed(SEED, f"preflight-{k}", 0) for k in range(len(prompts))]
            with ledger.stage("sampling_batch_check", prompts=len(prompts)):
                sampled_together = en.sample_generate(policy.model, prompts, seeds, temperature=sampling["temperature"],
                                                      batch_size=3, **options)
                sampled_single = en.sample_generate(policy.model, prompts, seeds, temperature=sampling["temperature"],
                                                    batch_size=1, **options)
            report["sampling"] = {"same": sum(x == y for x, y in zip(sampled_together, sampled_single)), "n": len(prompts),
                                  "differing_prompts": [k for k, (x, y) in enumerate(zip(sampled_together, sampled_single))
                                                        if x != y]}
        state_after = (en.lora_fingerprint(policy.named), en.optimizer_fingerprint(restored, policy.named),
                       en.rng_digest("cuda"), policy.model.training)
        assert state_before == state_after, "generation perturbed the training state"
        report["generation_preserved_state"] = True

        bank = prepared.banks["dev"]
        items = sample_items(bank, args.sample)
        report["evaluation_sample"] = {kind: sum(i["kind"] == kind for i in items) for kind in KINDS}
        torch.cuda.reset_peak_memory_stats()
        queries, query_sha = runner._query_examples(policy, prepared, recipe)
        summary = runner.evaluate_checkpoint(session, policy, restored, items, queries, query_sha, ledger,
                                             out / "eval-sample", out, "preflight", SEED)
        costs = stage_costs(out / "ledger.jsonl", {"load_guard", "query_loss", "generate", "sample", "arc_utility",
                                                    "guard", "guard_samples", "harm_scores"})
        report["evaluation_timing"] = {"stages": costs, "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                                       "projection_to_dev_bank": projection(costs, items, bank, sampling),
                                       "capped": {k: summary[k]["policy_capped"] for k in ("safety", "arc_generation")
                                                  if summary.get(k)},
                                       "harm_capped": summary.get("harm", {}).get("greedy", {}).get("policy_capped"),
                                       "overrefusal_capped": summary.get("overrefusal", {}).get("policy_capped")}

        if args.rewrite_config:
            from experiments.safety_selection.headroom import (APPENDIX_A_SYSTEM, edit_pool, load_rewrite_generator,
                                                               rewrite_prompt_ids, validate_rewrite_config)

            config = validate_rewrite_config(json.loads(Path(args.rewrite_config).read_text(encoding="utf-8")))
            del policy, restored, session
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
            generator = load_rewrite_generator(config)
            requests = [prepared.train_rows[row]["prompt"] for row in edit_pool(prepared)[:8]]
            ids = [rewrite_prompt_ids(generator.tokenizer, APPENDIX_A_SYSTEM, r) for r in requests]
            t0 = time.monotonic()
            batched = generator.generate(ids)
            t1 = time.monotonic()
            spec = config["generator"]
            one = [generator.generate([p])[0] for p in ids]          # a batch of one each
            report["rewrite_generator"] = {
                "config_file_sha256": sha256_file(args.rewrite_config), "attn_implementation": spec["attn_implementation"],
                "max_new_tokens": spec["max_new_tokens"], "requests": len(ids), "batched_seconds": t1 - t0,
                "output_tokens": sum(len(g.output_ids) for g in batched),
                "capped": sum(g.stop_reason == en.STOP_CAP for g in batched),
                "same_one_at_a_time": sum(x == y for x, y in zip(batched, one)),
                "differing_requests": [k for k, (x, y) in enumerate(zip(batched, one)) if x != y],
                "peak_allocated_bytes": torch.cuda.max_memory_allocated()}

        report["verdict"] = {
            "fixture_exact": report["resume"]["exact"],
            "trained_rows_separated_from_padding": True,
            "greedy_batch_equals_single": report["generation"]["same"] == report["generation"]["n"],
            "sampled_batch_equals_single": None if sampling is None else report["sampling"]["same"] == report["sampling"]["n"],
            "use_this_recipe": report["resume"]["exact"],
            "note": "a recipe whose two-step fixture is inexact is not used (sdpa -> keep eager: pc2-eager)"}
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
