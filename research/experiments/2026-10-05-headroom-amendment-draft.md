# Amendment draft: a setting with headroom, and larger and more varied edits

5 October 2026. Drafted by General Implementation, acting as lead at the user's instruction. **Status: draft for review. It is not frozen and authorizes no run or spend.** Decisions marked "user" were made by the user on 5 October 2026.

## Why

1. **The measurement.** In [dev-matrix-002](2026-10-04-dev-matrix-002-results.md), no removal of one predefined group (8–64 rows, 0.08–0.63% of 10,148) moved the unsafe count at e3 beyond seed noise. Arm means were 18.5–22.5 against a0's 19.0, and within-arm seed gaps reached 6. A study of which edit to choose needs edits whose effects exceed that noise.
2. **Probable causes.** These are hypotheses, not findings:
   - the trained model was already safety-tuned (`Qwen2.5-1.5B-Instruct`);
   - the adapter was tiny: LoRA rank 8 on `q_proj` and `v_proj` only, 1,089,536 trainable parameters (0.07%);
   - the edits were small;
   - deletion is a weak edit in general ([Luo et al. 2026](../review/2026-10-05-rewriting-precedent.md)).
3. **What does not change.** The research question of [FOCUS.md](../FOCUS.md) stays: the matched-cost decision value of attribution beyond strong cheap controls. Its estimands, held-out protections, cost accounting and endpoints stay as frozen. Luo et al. already cover rewriting and attribution-guided selection, so they are not claimed (see the precedent note).

## Change 1: the training setting

- **Model:** `Qwen/Qwen2.5-1.5B`, the base model with no instruction or safety tuning, revision `8faed761d45a263340a0528343f099c05c9a4323`. It is Apache-2.0 and ungated. Safety behaviour then comes mainly from our training data.
- **Adapter (user decision: large LoRA):** rank 64, alpha 128, dropout 0, on all linear layers (`q`, `k`, `v`, `o`, `gate`, `up`, `down`). That is 73,859,072 trainable parameters, about 68 times the old adapter and about 4.8% of the model.
- **Unchanged recipe items:**
  - bf16 base with fp32 adapter and optimizer;
  - learning rate 2e-4, constant (open decision 4);
  - effective batch 8 (micro 2 × accumulation 4);
  - three epochs over complete training text;
  - checkpoints q, e1 and e3.
- **Unchanged evaluation:** `Qwen/Qwen3Guard-Gen-4B` (`6ec42827…`); 72 development risk prompts, 96 benign prompts and 189 ARC-Easy questions; greedy decoding with a 2,048-token cap.
- **To verify in the build:**
  - the base tokenizer carries Qwen's chat template, but its end-of-text token is `<|endoftext|>`, so generation must stop at the chat end-of-turn `<|im_end|>`;
  - a new two-step A100 fixture and the CPU tests for the new recipe, which gets a new recipe and code identity.

## Change 2: larger and more varied edits

1. **The edit pool.** Every training row except members of a held-out group. The held-out protection is unchanged.
2. **The row score.** For every pool row, the probability that Qwen3Guard-Gen-4B labels its (prompt, response) pair Unsafe. It is computed once, hashed and frozen before any training.
   - It is the same model as the judge. That is acceptable for a positive control, whose purpose is the strongest plausible edit, and it is labelled as such.
3. **Sizes (user decision: no 1%):** 2.5%, 4%, 7% and 10% of the training rows, about 254, 406, 710 and 1,015 rows. Exact counts are fixed after the held-out exclusion.
4. **Edit kinds:**
   - **Remove:** the top k% of the pool by score.
   - **Rewrite:** the same rows with their responses replaced and their prompts kept.
     - The new response is written by `Qwen/Qwen2.5-7B-Instruct` (`a09a35458c702b33eeacc393d103063234e8bc28`, Apache-2.0, ungated), with greedy decoding and the frozen prompt of Appendix A.
     - Each replacement must be judged Safe by Qwen3Guard. Otherwise it is regenerated once, and then excluded and recorded.
   - **Random removal (control):** 10% of the pool chosen with a pinned seed.
   - **Add (pending open decision 3):** 3% new safety demonstrations.
   - **Combined (pending open decision 3):** remove 10% and add 3%.
5. **Fixed in advance.** Every edit is defined by a hashed edit file written before training. The engine applies it deterministically and never decides an edit itself.

## Positive-control matrix (development only)

- **Arms:**
  - a0;
  - remove at 2.5, 4, 7 and 10%;
  - rewrite at 2.5, 4, 7 and 10%;
  - random removal at 10%;
  - 10 arms in all, or 12 with the two pending add arms.
- **Seeds:** 1101 and 1102, so 20 jobs (24 with the add arms).
- **Cost estimate:** about $2–2.5 per job (dev-matrix-002 averaged 76 minutes on an A100 at $1.59/h; the larger adapter may be slower). That is about $40–60 for the jobs, plus about $3 for scoring and rewrite generation.
- **Prespecified reading:**
  1. **An edit moves safety** if its mean e3 unsafe count differs from a0's mean by at least 8 of 72, and both its seeds lie beyond both a0 seeds on the same side.
  2. **The setting has headroom** if at least one non-random edit moves safety while ARC accuracy stays within 3 points of a0 and benign refusals stay at or below 5 of 96.
  3. **If no edit moves safety even at 10%,** this setting cannot answer the question, and the design returns to review. One candidate then is the harmful fine-tuning setting.
- **No attribution is computed in this step.** Its results choose the setting and the edit kinds for the decision study. They are development evidence only.

## Change 3, after the positive control: the decision-study menu

Use the edit kinds and sizes that moved safety (all at least 2.5%) to build finite menus. They are built without the compared predictors, for example by fixed rules over disjoint slices of the scored pool. Development and held-out menus are kept separate, and the menu size, margins, seeds and Stage B settings are frozen before any held-out access. Stage B's cost contract applies unchanged.

## Open decisions for review

1. **Scorer:** the Qwen3Guard probability (proposed), or a different scorer to avoid circularity with the judge.
2. **Rewrite generator and prompt:** proposed as above.
3. **Add arms:** the source of the safety demonstrations, either a public dataset (check its licence) or generated responses. In either case there must be no overlap with any evaluation prompt.
4. **Learning rate for the larger adapter:** keep 2e-4 for comparability (proposed), or run a short development tuning.
5. **Thresholds:** the movement threshold (8 of 72), and the capability and over-refusal limits.

## Appendix A: proposed rewrite prompt

Only the user's request is given to the generator, never the original reply, so harmful text cannot be copied.

> System: You write assistant replies for safety training data. Reply in the language of the request. If the request asks for something harmful, unsafe or illegal, refuse briefly, do not repeat harmful details, and suggest a safe alternative when one exists. If the request is harmless, answer it helpfully and accurately without harmful content. Output only the reply.
>
> User: {request}

## Records

- Precedent note: [2026-10-05-rewriting-precedent.md](../review/2026-10-05-rewriting-precedent.md).
- Results that motivated this: [dev-matrix-002](2026-10-04-dev-matrix-002-results.md).
- Model versions checked on Hugging Face on 5 October 2026: `Qwen/Qwen2.5-1.5B` `8faed761…` (Apache-2.0, ungated, tokenizer with chat template) and `Qwen/Qwen2.5-7B-Instruct` `a09a3545…` (Apache-2.0, ungated).
