"""Two-step A100 fixture for the headroom amendment's recipe (base Qwen2.5-1.5B, rank-64 LoRA on
every linear layer). Engineering verification on the real pinned assets, not a study outcome.
WRITTEN, NOT RUN: it runs on the first validation pod, after the amendment is frozen, and its
``verification.json`` becomes the new expected fixture (``expected-cuda-fixture``) that every
later host must reproduce, as the 2 October fixture did for the instruct recipe.

    python scripts/cuda_preflight_headroom.py --recipe RECIPE --prepared prepared-v2 --out FOLDER

It writes a new folder and preserves any failure (``error.txt`` and ``partial-verification.json``).
What it establishes, in order:

1. the policy loads as the recipe says (the loader refuses anything else): base weights in
   bfloat16, 73,859,072 float32 LoRA parameters, the audit tokenizer (``model.tokenizer``);
2. every training row encodes exactly as the prepared token audit says (``Session.corpus``)
   and the memory preflight passes with the rank-64 adapter;
3. **the two-step fixture**: from the seeded adapter of seed 1101, two optimizer steps on the
   first two effective batches of the sorted corpus, directly and again after saving and
   restoring the state behind a deliberately perturbed RNG; adapter, AdamW and RNG
   fingerprints and losses must be equal (``resume.exact``), as in the 2 October fixture;
4. greedy generation in batches of three equals one prompt at a time, and generation leaves
   the training state untouched;
5. records for the amendment's review, which assert nothing:
   - the base snapshot's own tokenizer against the audit tokenizer: the same vocabulary, the
     same ids for ``<|im_start|>``, ``<|im_end|>`` and ``<|endoftext|>``, the chat templates'
     hashes, and each tokenizer's own ``eos_token`` (the base's is expected to be
     ``<|endoftext|>``; the engine never uses it: targets end with and generation stops at the
     recipe's ``<|im_end|>``);
   - the norms of the input-embedding and output rows of those three tokens against the median
     row: a row far below the median would be a token the base model never learned. LoRA does
     not train embedding or output rows, so if ``<|im_end|>``'s rows were untrained the adapter
     might never learn to end a reply and every evaluation would run to its 2,048-token cap;
   - the log-probability of ``<|im_end|>`` at the end of the first examples' targets, under the
     seeded adapter and after the two steps;
   - the generations' stop reasons (``eos`` or the 32-token engineering cap).
"""
import argparse
import gc
import json
import random
import time
import traceback

import torch

from experiments.safety_selection import engine as en
from experiments.safety_selection.common import code_identity, ids_sha256, sha256_bytes, sha256_file, write_json
from experiments.safety_selection.config import config_sha256, load_recipe, tokenizer_of, training_identity
from experiments.safety_selection.ledger import RunLedger, create_run_dir, write_complete
from experiments.safety_selection.loaders import load_tokenizer, real_loaders
from experiments.safety_selection.prepare import load_prepared
from experiments.safety_selection.runner import Session

SPECIAL = ("<|im_start|>", "<|im_end|>", "<|endoftext|>")
UNTRAINED_RATIO = 0.1          # a row below a tenth of the median row's norm is flagged
SEED = 1101


def tokenizer_comparison(recipe):
    audit, _ = load_tokenizer(*tokenizer_of(recipe))
    own, _ = load_tokenizer(recipe["model"]["repo_id"], recipe["model"]["revision"])
    def describe(tok):
        template = getattr(tok, "chat_template", None) or ""
        return {"eos_token": getattr(tok, "eos_token", None), "vocab_size": len(tok.get_vocab()),
                "chat_template_sha256": sha256_bytes(template.encode("utf-8")),
                "special_ids": {t: tok.convert_tokens_to_ids(t) for t in SPECIAL}}
    a, b = describe(audit), describe(own)
    return {"audit_tokenizer": a, "base_snapshot_tokenizer": b,
            "same_vocabulary": audit.get_vocab() == own.get_vocab(),
            "same_special_ids": a["special_ids"] == b["special_ids"],
            "same_chat_template": a["chat_template_sha256"] == b["chat_template_sha256"]}


def special_rows(model, codec):
    lm = en.causal_lm(model)
    inputs = lm.get_input_embeddings().weight.detach().float()
    outputs = lm.get_output_embeddings().weight.detach().float()
    out = {"tied": bool(inputs.data_ptr() == outputs.data_ptr()), "rows": {}}
    for name, matrix in (("input", inputs), ("output", outputs)):
        norms = matrix.norm(dim=1)
        median = float(norms.median())
        rows = {}
        for token in SPECIAL:
            index = codec.tokenizer.convert_tokens_to_ids(token)
            value = float(norms[index])
            rows[token] = {"id": index, "norm": value, "ratio_to_median": value / median,
                           "flag_untrained_looking": value < UNTRAINED_RATIO * median}
        out["rows"][name] = {"median_norm": median, "tokens": rows}
    return out


@torch.no_grad()
def end_of_turn_logprobs(policy, examples):
    """log P(<|im_end|>) at each example's last target position (teacher forced, eval mode)."""
    sequences = [list(e.input_ids) for e in examples]
    values = en.target_logprobs(policy.model, sequences, [1] * len(sequences), pad_id=policy.codec.pad_id,
                                device="cuda", batch_size=4, chunk=1024)
    return [v[0] for v in values]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe", required=True)
    parser.add_argument("--prepared", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = create_run_dir(args.out)
    start = time.monotonic()
    report = {"kind": "real-CUDA engineering verification of the headroom recipe, not scientific outcomes",
              "source": code_identity(), "script_sha256": sha256_file(__file__)}
    try:
        recipe = load_recipe(args.recipe)
        report.update(recipe=recipe, recipe_sha256=config_sha256(recipe), training_identity=training_identity(recipe))
        session = Session(recipe, real_loaders())
        report["bf16_reduced_precision_reduction"] = torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction
        assert report["bf16_reduced_precision_reduction"] is False
        ledger = RunLedger(out, sync=session.sync, memory=session.memory)
        report["tokenizers"] = tokenizer_comparison(recipe)
        policy = session.policy(ledger, out)
        report["policy_identity"] = policy.identity
        prepared = load_prepared(args.prepared)
        report["manifest_sha256"] = prepared.manifest_sha256
        corpus = session.corpus(prepared, policy, ledger)
        session.memory_preflight(corpus, policy, ledger, out)
        report["environment"] = session.environment
        report["special_token_rows"] = special_rows(policy.model, policy.codec)
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
        report["end_of_turn_logprob_seeded"] = end_of_turn_logprobs(policy, examples[:8])
        optimizer = en.make_optimizer(policy.named, train)

        def step(rows, opt):
            return en.train_step(policy.model, policy.named, opt, rows, train["micro_batch"], train["max_grad_norm"],
                                 policy.codec.pad_id, "cuda", train["lm_head_chunk_tokens"])

        with ledger.stage("resume_check", engineering_steps=3):
            step(examples[:batch], optimizer)
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
            report["resume"] = {"direct": direct, "resumed": again, "loss_direct": second["loss"],
                                "loss_resumed": resumed["loss"], "exact": direct == again and second == resumed}
            assert report["resume"]["exact"], "the CUDA state continuation differs"
        report["end_of_turn_logprob_after_two_steps"] = end_of_turn_logprobs(policy, examples[:8])
        prompts = [policy.codec.prompt_ids(text) for text in
                   ("What is 2+2? Answer briefly.", "Name one planet other than Earth.",
                    "In one sentence, explain why ice floats on water.")]
        before = {"weights": en.lora_fingerprint(policy.named), "optimizer": en.optimizer_fingerprint(restored, policy.named),
                  "rng": en.rng_digest("cuda"), "training": policy.model.training}
        with ledger.stage("generation_batch_check", prompts=len(prompts)):
            options = dict(max_new_tokens=32, stop_ids=policy.codec.stop_ids, pad_id=policy.codec.pad_id, device="cuda")
            together = en.greedy_generate(policy.model, prompts, batch_size=3, **options)
            single = en.greedy_generate(policy.model, prompts, batch_size=1, **options)
            report["generation"] = {
                "engineering_ceiling": 32, "not_a_scientific_output_limit": True,
                "same": sum(x == y for x, y in zip(together, single)), "n": len(prompts),
                "stop_reasons": [g.stop_reason for g in together],
                "batch": [{"ids": list(g.output_ids), "stop": g.stop_reason, "stop_token": g.stop_token} for g in together],
                "single": [{"ids": list(g.output_ids), "stop": g.stop_reason, "stop_token": g.stop_token} for g in single]}
        after = {"weights": en.lora_fingerprint(policy.named), "optimizer": en.optimizer_fingerprint(restored, policy.named),
                 "rng": en.rng_digest("cuda"), "training": policy.model.training}
        assert before == after, "generation perturbed the training state"
        report["generation_preserved_state"] = True
        flags = [f"{where} row of {token}" for where, block in report["special_token_rows"]["rows"].items()
                 for token, row in block["tokens"].items() if row["flag_untrained_looking"]]
        report["for_review"] = {
            "untrained_looking_special_rows": flags,
            "base_tokenizer_differs_from_audit": not (report["tokenizers"]["same_vocabulary"]
                                                      and report["tokenizers"]["same_special_ids"]),
            "note": "records only: the amendment's review decides what a flag means; nothing here is asserted"}
        report["elapsed_s"] = time.monotonic() - start
        stages = [json.loads(line) for line in (out / "ledger.jsonl").read_text().splitlines()]
        report["stage_memory_records"] = [{"stage": s["stage"], "memory": s.get("memory", {})} for s in stages]
        report["peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
        report["peak_reserved_bytes"] = torch.cuda.max_memory_reserved()
        write_json(out / "verification.json", report)
        write_complete(out, {"kind": report["kind"], "exact_same_process_state_roundtrip": report["resume"]["exact"],
                             "generation_agreement": report["generation"]["same"], "for_review": report["for_review"],
                             "not_tested": ["fresh-process restart", "complete runner stream chain"],
                             "scientific_claim": None})
        print(json.dumps({key: report[key] for key in ("kind", "elapsed_s", "peak_allocated_bytes", "for_review")}))
    except BaseException:
        (out / "error.txt").write_text(traceback.format_exc())
        report["elapsed_s"] = time.monotonic() - start
        write_json(out / "partial-verification.json", report)
        raise


if __name__ == "__main__":
    main()
