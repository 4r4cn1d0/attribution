"""A100 preflight for the OLMo 3 7B probe (allenai/Olmo-3-7B-Instruct; the OLMo 3 plan draft O3A §16.1; blocker B3 of
the readiness scout; track O3A-env-preflight, 4 Nov 2026). Engineering verification on the real pinned assets, not a
study outcome. WRITTEN, NOT RUN ON A GPU: it runs on the probe's host, once per candidate recipe of the ladder, and the
chosen candidate's ``verification.json`` becomes ``expected-fixture-probe.json`` in the OLMo 3 kit.

    python scripts/cuda_preflight_olmo3.py --recipe RECIPE --prepared PREPARED --out FOLDER
    python scripts/cuda_preflight_olmo3.py --rule-check --config CONFIG_JSON --tokenizer SNAPSHOT --out FOLDER \\
        --end '<|endoftext|>' --stop '<|endoftext|>' --stop '<|im_end|>' --pad '<|pad|>' --header '<|im_start|>assistant\\n'

The first form is the family preflight (``cuda_preflight_family.py``, unchanged; its helpers are imported) with these
changes; ``main`` is its ``main`` with the comparison step replaced, and ``scripts/tests/test_cuda_preflight_olmo3.py``
pins the difference line by line:

1. **comparison rows** (``extra_id_rows``): OLMo 3 has 100,278 embedding rows for 100,278 tokens and no
   ``<|reserved_special_token_N|>`` names, so the family rule finds no rows and refuses every candidate. The rows the
   chat rows are compared with are the seven unused ``<|extra_id_N|>`` rows, ids 100256 and 100270-100275, confirmed
   from the tokenizer on every run: each id decodes to its name, is not flagged special, is not in the chat template
   and is not a chat token or the pad; and the model has exactly one row per token (no padding rows, or the family
   rule would apply). Otherwise the run refuses (``error.txt``);
2. **the rule** (``chat_rows_report_cosine``; CM D-O4, fixed here before the first pod: the kit's fixture pins this
   file's ``script_sha256``, so a later change of the rule or its constant needs a new fixture): untrained **output**
   rows stay parallel to each other without being bit-identical (every never-seen output row gets the same softmax
   pull; the 5 Oct read of OLMo 3 7B Base: cosine 1.000 between the chat tokens' output rows and the unused rows,
   ``research/experiments/2026-10-05-headroom-v2-workplan.md:19``; OLMo-2's records: each padding output row's
   cosine to their mean equals its largest cosine to any of them), so the family's bit-identity test cannot see
   them. On the output side a chat row is distinct when its largest cosine to any comparison row is at most
   COSINE_SAME = 0.99 (an angle of at least 8.1 degrees; an opposite row, cosine -1, reads distinct). The output
   comparison rows must be a clean reference: their smallest pairwise cosine is at least COSINE_SAME (unused output
   rows point one way); otherwise ``chat_rows_distinct`` is null and the recipe is not used, as the family rule does
   with no rows. On the **input** side the cosine rule does not apply (verify round 1, D3): an unused input row gets
   no gradient and keeps its random initialisation, so unused input rows are mutually non-parallel (OLMo-2's records:
   padding input rows at median norm 0.889 and 1.263 = 0.02 * sqrt(d), largest cosines at the random-rows value
   0.04) or have no direction (Llama's reserved and Qwen's padding input rows at norm 0.0), and a chat row's cosine to
   them says nothing. There the family's bit-identity rule decides, as before, and the cosines and norms are
   recorded for reading (``rule`` and ``distinct`` per side; ``SIDE_RULES``). Why 0.99: the trained chat rows in the
   recorded fixtures reach at most 0.935 on the output side (Qwen2.5-7B's ``<|im_start|>`` 0.9353 and ``<|im_end|>``
   0.9335, the ChatML tokens OLMo 3 also trains; Llama-3.1-8B 0.74-0.87; OLMo-2-7B 0.46; OLMo-2-1B 0.22; every
   input side at most 0.04), untrained parallel rows give 1.000, and bfloat16 rounding of a scaled copy moves a
   cosine by at most about 1e-5 (measured 1.3e-6 at d = 4096). The family's bit-identity result is recorded beside
   the cosine result on both sides (``bit_identical_rule``), never used for the output side's verdict;
3. **OLMo 3 only**: a recipe (or, in the second form, a config) whose architecture is not ``Olmo3ForCausalLM`` is
   refused before any folder is made (exit 2, a fixed message);
4. the report records both scripts' hashes (``script_sha256`` is this file's, ``family_script_sha256`` the family
   preflight's) and the rule's constants under ``comparison_rule``.

The second form (``--rule-check``; CPU, no weights, no GPU) builds a random ``Olmo3ForCausalLM`` from a config
folder, wraps it with the engine's LoRA, builds the codec from the tokenizer snapshot and runs steps 1 and 2 on its
embedding rows, writing ``rule-check.json`` into a new folder. It exercises the new path under the OLMo 3 lock on a
tiny model; its random output rows are not parallel, so its verdict is null by rule. It is not a preflight and writes
no verification or completion record.
"""
import argparse
import gc
import json
import os
import random
import sys
import time
import traceback
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cuda_preflight_family as pf  # noqa: E402
from cuda_preflight_family import (BATCH_PROOF_NEW_TOKENS, RECIPE_B_GENERATION_BATCH, _finish, batch_proof_prompts,  # noqa: E402
                                   cap_projection, derive_chat_tokens, full_length_check, generation_phase,
                                   outside_stages_s, scheduled_rate, scheduled_update, stop_verdict, tokenizer_check,
                                   verdict_of)
from cuda_preflight_headroom import end_of_turn_logprobs  # noqa: E402
from cuda_preflight_headroom_v3 import KINDS, SEED, projection, sample_items, stage_costs  # noqa: E402
from cuda_preflight_killtest import (ENGINEERING_PROMPTS, compare_untuned, comparison_items,  # noqa: E402
                                     load_plain_model, memory_failure_verdict)

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import code_identity, ids_sha256, sha256_file, write_json  # noqa: E402
from experiments.safety_selection.config import (config_sha256, load_recipe, tokenizer_of,  # noqa: E402
                                                 training_identity)
from experiments.safety_selection.ledger import RunLedger, create_run_dir  # noqa: E402
from experiments.safety_selection.loaders import load_tokenizer, real_loaders  # noqa: E402
from experiments.safety_selection.prepare import load_prepared  # noqa: E402
from experiments.safety_selection.textproc import build_codec, check_assistant_header  # noqa: E402

ARCHITECTURE = "Olmo3ForCausalLM"
EXTRA_ID_ROWS = {"<|extra_id_0|>": 100256, "<|extra_id_1|>": 100270, "<|extra_id_2|>": 100271, "<|extra_id_3|>": 100272,
                 "<|extra_id_4|>": 100273, "<|extra_id_5|>": 100274, "<|extra_id_6|>": 100275}
COSINE_SAME = 0.99                       # at or below: another way; above: the same way (module doc, step 2)
SIDE_RULES = {"used_input": "bit_identity", "used_output": "cosine"}     # which rule decides each side (step 2)
COMPARISON_KIND = "extra_id"
EXIT_REFUSED = 2
REFUSAL_OTHER_FAMILY = "refused: this preflight is for Olmo3ForCausalLM recipes only (cuda_preflight_family.py serves the others)"


class Olmo3PreflightError(ValueError):
    """The comparison rows could not be confirmed from the tokenizer and the model (module doc, step 1)."""


def comparison_rule() -> dict:
    """The rule's constants, recorded in every report."""
    return {"comparison_kind": COMPARISON_KIND, "rows": dict(EXTRA_ID_ROWS), "cosine_same": COSINE_SAME,
            "side_rules": dict(SIDE_RULES),
            "rule": "output side: a chat row is distinct when its largest cosine to any comparison row is at most "
                    "cosine_same; null when the comparison rows' smallest pairwise cosine is below cosine_same. input "
                    "side: the family's bit-identity rule (unused input rows are random, no reference); cosines recorded",
            "family_script_sha256": sha256_file(pf.__file__)}


def extra_id_rows(tokenizer, n_rows: int, chat_ids, pad_id: int) -> tuple[str, list[int]]:
    """(kind, ids) of the seven unused ``<|extra_id_N|>`` rows after the confirmation of the module doc (step 1);
    refuses otherwise. Takes the family ``comparison_rows`` arguments, so ``main`` differs by the name alone."""
    if n_rows != len(tokenizer):
        raise Olmo3PreflightError(f"{n_rows} embedding rows for {len(tokenizer)} tokens: OLMo 3 has one row per token; "
                                  "with padding rows the family preflight's rule applies")
    added = getattr(tokenizer, "added_tokens_decoder", {}) or {}
    template = getattr(tokenizer, "chat_template", None) or ""
    excluded = set(int(i) for i in chat_ids) | {int(pad_id)}
    for text, index in EXTRA_ID_ROWS.items():
        entry = added.get(index)
        if entry is None or str(getattr(entry, "content", "")) != text:
            raise Olmo3PreflightError(f"id {index} is not {text!r} in the tokenizer")
        if bool(getattr(entry, "special", False)):
            raise Olmo3PreflightError(f"{text} is flagged special")
        if text in template:
            raise Olmo3PreflightError(f"{text} is in the chat template")
        if index in excluded:
            raise Olmo3PreflightError(f"{text} is a chat token or the pad")
    return COMPARISON_KIND, sorted(EXTRA_ID_ROWS.values())


def pairwise_min_cosine(rows: torch.Tensor) -> float:
    """The smallest cosine between any two of ``rows`` (float32); 1.0 for a single row."""
    unit = torch.nn.functional.normalize(rows.detach().to("cpu", torch.float32), dim=1)
    cosines = unit @ unit.T
    off = ~torch.eye(len(rows), dtype=torch.bool)
    return float(cosines[off].min()) if off.any() else 1.0


def chat_rows_report_cosine(weights_in, weights_out, chat: dict[str, int], comparison: list[int]) -> dict:
    """The family ``chat_rows_report`` (the engine's ``token_row_report`` per side, with its bit-identity result kept
    as ``bit_identical_rule``), the cosine numbers on both sides, and ``chat_rows_distinct`` by the rule of the module
    doc (step 2): per side ``rule`` (``SIDE_RULES``) and ``distinct``; the cosine rule on the output side, the family's
    bit-identity rule on the input side; null when the output side has no clean reference."""
    out = pf.chat_rows_report(weights_in, weights_out, chat, comparison)
    if not comparison:
        return out
    out["bit_identical_rule"] = out["chat_rows_distinct"]
    out["cosine_same"] = COSINE_SAME
    for side, weights in (("used_input", weights_in), ("used_output", weights_out)):
        w = weights.detach().to("cpu", torch.float32)
        rows = w[list(comparison)]
        report = out[side]
        report["rule"] = SIDE_RULES[side]
        report["comparison_min_pairwise_cosine"] = pairwise_min_cosine(rows)
        report["comparison_rows_parallel"] = report["comparison_min_pairwise_cosine"] >= COSINE_SAME
        for token, index in chat.items():
            record = report["tokens"][token]
            record["same_way_as_a_comparison_row"] = record["max_cosine_to_padding"] > COSINE_SAME
            record["distance_to_nearest_comparison_row"] = float((rows - w[index]).norm(dim=1).min())
        if report["rule"] == "cosine":
            report["distinct"] = (all(not report["tokens"][t]["same_way_as_a_comparison_row"] for t in chat)
                                  if report["comparison_rows_parallel"] else None)
        else:
            report["distinct"] = all(not report["tokens"][t]["bit_identical_to_a_padding_row"] for t in chat)
    if out["used_output"]["distinct"] is None:
        out["chat_rows_distinct"] = None
        out["note"] = ("the output comparison rows are not mutually parallel (smallest pairwise cosine below cosine_same): "
                       "no clean unused-row reference on the output side, so the recipe is not used")
        return out
    out["chat_rows_distinct"] = out["used_input"]["distinct"] and out["used_output"]["distinct"]
    return out


def refuse_other_family(recipe_path: str) -> None:
    """Exit 2 with a fixed message unless the recipe's architecture is OLMo 3's (module doc, step 3)."""
    architecture = json.loads(Path(recipe_path).read_text(encoding="utf-8")).get("model", {}).get("architecture")
    if architecture != ARCHITECTURE:
        print(f"{REFUSAL_OTHER_FAMILY}; the recipe names {architecture!r}", file=sys.stderr)
        sys.exit(EXIT_REFUSED)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe", required=True)
    parser.add_argument("--prepared", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--sample", type=int, default=20, help="items per development kind in the timed sample")
    args = parser.parse_args()
    refuse_other_family(args.recipe)
    out = create_run_dir(args.out)
    start = time.monotonic()
    report = {"kind": "real-CUDA engineering verification of an OLMo 3 probe recipe, not scientific outcomes",
              "source": code_identity(), "script_sha256": sha256_file(__file__), "comparison_rule": comparison_rule()}
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
        kind, rows = extra_id_rows(codec.tokenizer, used_in.shape[0], chat.values(), codec.pad_id)
        report["comparison_kind"], report["comparison_rows"] = kind, len(rows)
        report["chat_rows"] = chat_rows_report_cosine(used_in, used_out, chat, rows)
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

        rate = scheduled_rate(train, prepared.corpus, SEED)
        applied = []                                   # the rate each update ran at (verification.json evidence)

        def step(rows_, opt, global_step):
            """One engineering step at the recipe's loss and, for a warmup schedule, the rate of ``global_step``."""
            def update():
                applied.append(sorted({g["lr"] for g in opt.param_groups}))
                return en.train_step(policy.model, policy.named, opt, rows_, train["micro_batch"], train["max_grad_norm"],
                                     codec.pad_id, "cuda", train["lm_head_chunk_tokens"],
                                     train.get("loss_weighting", en.EXAMPLE_MEAN))     # the recipe's loss
            return scheduled_update(rate, train["lr"], opt, global_step, update)

        torch.cuda.reset_peak_memory_stats()
        with ledger.stage("resume_check", engineering_steps=3) as info:
            t0 = time.monotonic()
            # global steps 2 and 3: a warmup schedule runs step 1 at rate 0, which would leave LoRA B at zero and so
            # never move A; at 2 and 3 B moves before the save and A after it, as at the constant peak (round 6 review)
            first = step(examples[:batch], optimizer, 2)
            en.save_state(out / "after-first-step", policy.named, optimizer, "cuda", {"engineering": True, "step": 2})
            saved_rng = en.rng_digest("cuda")
            second = step(examples[batch:], optimizer, 3)
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
            resumed = step(examples[batch:], restored, 3)
            again = {"adapter": en.lora_fingerprint(policy.named),
                     "optimizer": en.optimizer_fingerprint(restored, policy.named), "rng": en.rng_digest("cuda")}
            report["resume"] = {"direct": direct, "resumed": again, "loss_first": first["loss"],
                                "loss_direct": second["loss"], "loss_resumed": resumed["loss"],
                                "exact": direct == again and second == resumed, "seconds": time.monotonic() - t0,
                                "applied_rates": applied, "scheduled": rate is not None}
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


def rule_check(argv=None) -> int:
    """The CPU form of the module doc: the comparison rule on a random ``Olmo3ForCausalLM`` built from ``--config``
    (a folder's config.json), the codec and chat tokens from ``--tokenizer`` (a snapshot folder); ``rule-check.json``
    into a new ``--out`` folder; exit 0 when the path ran, whatever the verdict."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--rule-check", action="store_true", required=True)
    parser.add_argument("--config", required=True, help="a config.json (its folder is read)")
    parser.add_argument("--tokenizer", required=True, help="a local tokenizer snapshot folder")
    parser.add_argument("--out", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--stop", action="append", required=True)
    parser.add_argument("--pad", required=True)
    parser.add_argument("--header", required=True)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--lora-r", type=int, default=4)
    args = parser.parse_args(argv)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import peft
    import transformers

    config = transformers.AutoConfig.from_pretrained(str(Path(args.config).resolve().parent), local_files_only=True)
    if config.architectures != [ARCHITECTURE]:                    # before any folder, as the pod form (verify round 1, N3)
        print(f"{REFUSAL_OTHER_FAMILY}; the config names {config.architectures!r}", file=sys.stderr)
        return EXIT_REFUSED
    out = create_run_dir(args.out)
    torch.manual_seed(args.seed)
    base = transformers.AutoModelForCausalLM.from_config(config).float()
    model = peft.get_peft_model(base, peft.LoraConfig(r=args.lora_r, lora_alpha=2 * args.lora_r, lora_dropout=0.0,
                                                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj",
                                                                      "up_proj", "down_proj"],
                                                      bias="none", task_type="CAUSAL_LM"))
    named = en.lora_parameters(model)
    en.load_lora_state(named, en.init_lora_state(named, args.seed))
    tokenizer = transformers.AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True, trust_remote_code=False)
    codec = build_codec(tokenizer, args.end, args.stop, args.pad)
    probe = check_assistant_header(codec, args.header)
    chat = derive_chat_tokens(codec)
    used_in, used_out = en.effective_embedding_weights(model)
    kind, rows = extra_id_rows(codec.tokenizer, used_in.shape[0], chat.values(), codec.pad_id)
    report = {"kind": "OLMo 3 preflight rule check on a random tiny model (CPU; no weights; not a preflight)",
              "script_sha256": sha256_file(__file__), "comparison_rule": comparison_rule(), "seed": args.seed,
              "config": str(Path(args.config).resolve()), "architecture": type(base).__name__,
              "tokenizer": {"snapshot": str(Path(args.tokenizer).resolve()), "class": type(tokenizer).__name__,
                            "len": len(tokenizer)},
              "lora": {"r": args.lora_r, "trainable": en.parameter_count(named)},
              "codec": {"eos_id": codec.eos_id, "stop_ids": list(codec.stop_ids), "pad_id": codec.pad_id,
                        "probe_tail": probe[-64:]},
              "chat_tokens": chat, "embedding_rows": int(used_in.shape[0]), "comparison_kind": kind,
              "comparison_rows": len(rows), "comparison_row_ids": rows,
              "chat_rows": chat_rows_report_cosine(used_in, used_out, chat, rows)}
    report["chat_rows_distinct"] = report["chat_rows"]["chat_rows_distinct"]
    write_json(out / "rule-check.json", report)
    print(json.dumps({k: report[k] for k in ("kind", "architecture", "comparison_kind", "comparison_rows", "chat_rows_distinct")}))
    return 0


def cli(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--rule-check" in argv:
        return rule_check(argv)
    main()
    return 0


if __name__ == "__main__":
    sys.exit(cli())
