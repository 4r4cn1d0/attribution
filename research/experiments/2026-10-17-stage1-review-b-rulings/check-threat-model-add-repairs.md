# Check: the threat model and two stronger data-only add repairs (mock review B, items 3 and 4)

**Status: PROPOSAL for the main-study lead (GI VI). It adopts nothing.** Written 2026-10-16 from 22:25 UTC (17 Oct IST; clock checked with `date -u` at 22:23 and 22:25 UTC) by an Opus worker. Read-only work: no repository edit, commit, pod, spend, download or agent. The only file written is this one. I did not open `selector.jsonl`, `hidden/`, any held-out file, or wave-0b `rows.jsonl`/`groups.json`. No row, prompt, answer or anchor text appears here.

**Scope.** Item 3 (the threat model) answers mock review B, W3 and §5.8. Item 4 (stronger data-only add repairs) answers W5 and §5.3. A separate workflow drafts the stage-1 analysis model, the testing family and the reference tests (review A W2–W5, W12; review B W2, W8). I call that work **"the analysis-model draft"** and do not redo it. Where this note needs a test, a frontier rule or a winner's-curse rule, it points there.

**Labels.** **R** = read (the source follows). **M** = measured (the source follows). **E** = estimate (the basis follows). **I** = inference. **UNVERIFIED** = not checked. **Choice marks:** **[LEAD]** = the lead may decide. **[USER]** = the user decides (it costs money, changes a model, or changes a design that the user adopted). **[USER-CONFIRM]** = depends on the user's relayed standing rule "ambitious default, pre-set fallback", which the lead's chat has not yet confirmed.

**Sources read** (main checkout, branch `stageb-costs-and-recovery-safeguards-20261003`, HEAD 541b122; SHA-256 prefixes computed with `shasum -a 256` at 22:23 UTC):
- REV-B = `writing/paper/2026-10-17-mock-review-B-safety.md` (`4dfab435…`).
- PAPER = `writing/paper/2026-10-08-icml-draft.md`, revision 6 (`024942b5…`).
- FOCUS = `research/FOCUS.md` (`23e3da8f…`): 8 Oct sharpened direction; 9 Oct user decisions; 11 Oct side-study entries; 15 Oct records sync; 16 Oct entries. Entries are cited by their UTC time.
- PLAN-S = `research/review/2026-10-08-sharpened-direction-DRAFT.md` (`6ff3ff2b…`).
- PREREG = the frozen Gate B/C pre-registration, revision 5 (`5c97cce7…`), §6.
- BRIEF = `.ai/briefs/stage1-commitments-build-20261016.md` (`12cbf463…`). ADD = its lead-decisions addendum (`11477648…`; it now holds §4 and §5, added after the hash that FOCUS records, `b8a67719…`).
- REPLAN = `writing/paper/2026-10-17-icml-replan-PROPOSAL.md` (`e8768298…`).
- Engine code, read only: `experiments/safety_selection/edits.py` (`b6913c65…`) and `textproc.py` (`bdecfec2…`).
- Sibling drafts in this worktree's `tmp/gi-vi-parallel/` (not reviewed by me; cited only as E or R of a number they computed): `prereg-references/tau_l_check.out.json` (τ_L), `icml-78b-prep/engine-round-Y-design.md` (the engine round).
- Web (opened in this session; at most one short quote per source): the OpenAI fine-tuning API reference and supervised fine-tuning guide; the Microsoft Foundry safety-evaluation page; arXiv 2406.05946 (HTML), 2601.01887 (abstract and HTML), 2505.12038, 2408.09600 and 2409.18169 (abstracts); the ICML 2026 call for papers.

---

## 0. Summary

1. **The paper's actor is too narrow, and the real actors have more levers (R, I).** A customer of the OpenAI fine-tuning API can set `n_epochs`, `batch_size` and `learning_rate_multiplier` for supervised jobs, and can start a new job from a fine-tuned model (R: OpenAI docs). Microsoft Foundry screens the training data before training and gates the tuned model after training (R: Foundry page). So "a customer who controls only the data" is one actor of five, not the only one.
2. **Proposal for item 3:** an "Actor" column in Table 1 (§2.3), a per-actor winner report (§2.4), and one new reference, **B↓LR** = recipe B at LR 5e-5 on the unchanged data, 6 seeds (§2.5). **Cost about $12–14 (E).** The side paper's half-LR result is cited for motivation only; the main paper uses none of its units, seeds or numbers as evidence (§2.6).
3. **Proposal for item 4:** two 48-row add arms at 6 seeds (§3): **SR**, a recovery-style arm after Qi et al. (a refusal after a harmful prefix, with the prefix excluded from the loss), and **S6**, a one-shot-style arm after Safety at One Shot (one example, copied to 48 rows). **Each costs about $12–14 (E).** S6 needs no engine change. SR needs one small engine change (a loss-free response prefix), which joins the planned engine round with B+Qi.
4. **Both add arms reuse the existing rules (R):** the S-pool (REQ-6), L8 (every S-pool record has an unsafe response, which gives SR its prefix), L11 and L14 (the untuned model's own refusals, as both papers used), L9 and L13 (exclusions and labels), and REQ-7 (the add writer).
5. **Timing (R: FOCUS 8 Oct 13:53 UTC):** an edit rule that is not committed before Gate B wave 1 (latest start 27 Oct, REPLAN §5) is "post-Gate-B exploratory". The SR and S6 rules can be committed at $0 before wave 1; SR's engine code can come later, by the stage-1 freeze.
6. **Money (R: FOCUS 16 Oct 13:21 and 19:08 UTC):** the balance is $91.94 and Gate B wave 1 needs $83.91 of it. So all three new arms (about $36–41 together, E) need new money. **[USER]**

---

## 1. What review B asks for (R: REV-B)

- **W3 (major).** The actor is not coherent. The OpenAI API exposes the learning rate, epochs and batch size. The customer cannot run A1, L1 or S3. The service controls the recipe. The cheapest fix: an actor column in Table 1, a winner per actor's menu, and one reference that a closed-service customer can use, "recipe B at the next rung down … (5e-5 for OLMo) … at six seeds".
- **W5 (major).** The add arms are all "48 refusal rows that open with a refusal", which is shallow safety data. The review asks for Qi et al.'s safety-recovery augmentation and for the Safety at One Shot example used as data, each at 48 rows and six seeds. It also asks to cite Safe Delta, Antidote and the harmful fine-tuning survey.
- **§8.1 (the reviewer's own cross-check).** W3 and W5 are "PARTLY" known: paper decision 10 (who the user is) and decision 27 (candidate references) cover part of each. The per-actor menus, the LR reference and the data-only form of both repairs are new.

---

## 2. Item 3: the threat model

### 2.1 What the real services let a customer do

| Fact | Label and source |
|---|---|
| OpenAI supervised jobs take three hyperparameters: `batch_size`, `learning_rate_multiplier` and `n_epochs`, each "auto" or a number. DPO jobs add `beta`. Reinforcement jobs add `compute_multiplier`, `eval_interval`, `eval_samples` and `reasoning_effort`. | R: OpenAI API reference, fine-tuning resource |
| No warmup, schedule, loss-weighting or LoRA-rank field appears in the part of the reference that I read. | R (partial read: the create section was cut off) |
| A job may start from "the ID of a previously fine-tuned model". The minimum file is 10 examples. | R: OpenAI supervised fine-tuning guide |
| After training, OpenAI evaluates the model in 13 safety categories and blocks deployment if too many examples fail. | R: same guide |
| The guide does not say that the training data are screened for safety. | R (absence on that page only; older OpenAI statements were not checked) |
| An assistant message in chat-format data can carry `weight` 0 or 1, so a turn can be left out of the loss. | UNVERIFIED (third-party copies of OpenAI's docs and forum posts; one forum user reports that weight 0 did not seem to work) |
| Foundry evaluates the training data for harmful content **before** training; above a severity level the job fails ("Please fix the data and try again"). | R: Foundry safety-evaluation page (updated 31 Jul 2026) |
| Foundry evaluates the tuned model **after** training and blocks deployment above a threshold; the message tells the customer to review the data and resubmit. Customers cannot change these thresholds. | R: same page |
| Our recipe B is already at one epoch, the smallest value of `n_epochs`. A 3-epoch fine-tune nearly saturated the erosion during development. | R: PAPER §4.1; FOCUS 6 Oct 18:55 UTC |

**What this means (I).**
- The premise "the service sends the customer back to the data" holds on both services.
- A closed-service customer often also controls the learning rate, epochs and batch size. Of these, only the learning rate is a lever in our setting, because recipe B already uses one epoch. Batch size is not tested here.
- OpenAI's `learning_rate_multiplier` scales a base rate that OpenAI does not publish. So "one rung lower" (5e-5 against 1e-4) is an analogue of a multiplier of about 0.5, not the same setting.
- A customer who can start a job from a fine-tuned model can apply the post-hoc one-shot patch of Safety at One Shot as a second job of 10 or more rows. Safety at One Shot itself did this for GPT-4.1 with 10 examples because of the API minimum (R: arXiv 2601.01887 HTML). The paper's §6 excludes that patch, so it excludes a lever that closed-service customers have. (The patch as a reference is the user's open scope decision, ADD §5 item 4; this note does not reopen it.)
- Foundry's data screen may reject training rows that hold harmful text. That matters for SR (harmful prefixes in the assistant turn) and possibly for S1 to S6 (harmful prompts in the user turn). Whether PKU rows pass is UNVERIFIED.

### 2.2 The five actors

| Code | Actor | Controls | Cannot do |
|---|---|---|---|
| **Cd** | Closed-service customer, data only (for example, a Foundry customer told to resubmit) | The rows of the training file; any rule computed from the text alone; rows added from public data; the prompt of their own deployment | Gradients, hidden states, weights, the recipe |
| **Ch** | Closed-service customer with hyperparameter control (for example, the OpenAI API) | As Cd, plus the learning-rate multiplier, epochs and batch size; a follow-up job from the tuned model | Gradients, hidden states, weights, schedule, loss, LoRA rank |
| **Sp** | The service provider (operator of the fine-tuning platform) | Everything: weights and gradients (A1, L1, S3), the recipe default for every customer (B+Qi, a lower LR, recipe G), post-hoc transforms (adapter scaling, Safe LoRA), safety rows added to every job | Its own policy may forbid changing a customer's recipe or adapter (PAPER §6: "must ship the customer's adapter and may change only the data"); that is a policy limit, not a capability limit (I) |
| **Ow** | Open-weights developer who fine-tunes its own copy | Everything Sp controls; no service gate | — |
| **Dp** | Dataset publisher (publishes a benign dataset for others to train on) | The dataset only; model-based scorers only on a proxy model | Downstream models and recipes; so model-level references do not apply |

**Two consequences (I).**
- For Cd and Ch, the paper's data menu shrinks to a_R, H1, S1, S4 (and the new S6; SR only if the service allows it). Among the primary contrasts, Cd's answer rests on P3 (H1 − R), P4 (S1 − a0) and P6 (S4 − S1).
- For Dp, our evidence is same-model evidence only. A repair chosen on OLMo may not transfer to another model (review Q7). The per-actor report must say so.

### 2.3 Proposed "Actor" column for Table 1 [LEAD]

Proposed text for the paper (Table 1 plus the references of §4.4, so that one table holds every arm). Rows marked "new" exist only if the user approves them (§2.5, §3). **[USER]** for the new rows; **[LEAD]** for the column itself.

| Arm | Repair | Who can run it |
|---|---|---|
| a_R | random removal | Cd, Ch, Sp, Ow, Dp |
| a0 | no repair | all |
| H1 | length rule (free) | Cd, Ch, Sp, Ow, Dp |
| A1 | attribution (gradient similarity) | Sp, Ow; Dp† |
| L1 | LARF-style filter (hidden states) | Sp, Ow; Dp† |
| S1 | random refusals | Cd‡, Ch‡, Sp, Ow, Dp |
| S3 | DataRx-style | Sp, Ow; Dp† |
| S4 | self-generated refusals | Cd§, Ch§, Sp, Ow; Dp† |
| SR (new) | recovery-style (refusal after a harmful prefix) | Sp, Ow, Dp; Cd and Ch only‡‖ |
| S6 (new) | one-shot-style (one example, 48 copies) | Cd§, Ch§, Sp, Ow; Dp† |
| PTST | safety prompt at test time | Cd¶, Ch¶, Sp, Ow |
| Adapter scaling | adapter scaled by λ | Sp, Ow |
| Safe LoRA | post-hoc projection | Sp, Ow |
| Recipe G | warmup, cosine decay, token-mean loss | Sp, Ow |
| B+Qi | constrained objective | Sp, Ow |
| B↓LR (new) | recipe B one LR rung lower | Ch, Sp, Ow |

Footnotes (each is a label on a fact, not a result):
- † With a proxy model, so the effect on other models is untested (transfer; review Q7) (I).
- ‡ Only if the service's training-data screen accepts rows with harmful prompts. Foundry screens training data before training (R); whether PKU rows pass is UNVERIFIED.
- § Only if the service lets the customer sample the untuned model (I).
- ‖ Also needs a way to leave the harmful prefix out of the loss. OpenAI's message `weight` is UNVERIFIED, and a weighted-out message would end the assistant turn, which is a different construction from Qi et al.'s (I).
- ¶ In the customer's own deployment. The pages I read do not say whether a service's safety gate uses the customer's prompt (UNVERIFIED). So PTST may not help a customer pass the gate (I).

### 2.4 The per-actor winner report [LEAD]

**Rule (proposed text, frozen before stage 1).**
1. Each actor's menu M_X is its column of Table 1, fixed before any stage-1 outcome. No arm enters or leaves a menu after an outcome.
2. At each τ_O ∈ {2, 5, 10} pp and the frozen τ_L, report every arm in M_X with F, O, L, cost under both conventions, and its label from its own pre-registered contrast.
3. Name the best data arm and the best reference in M_X by the point estimate of F among feasible arms. Feasibility and any "data repair against reference" test come from the analysis-model draft (its family for review B W2, its frontier rule matched on task loss, and its winner's-curse rule). This report adds no test of its own.
4. Write "for actor X, the best measured option is A" only if the analysis-model draft's procedure separates A from the next-best feasible option in M_X. Otherwise write "too close to call between A and B".
5. For Dp, every sentence says "on the same model". For Cd, the comparison is among data arms and a0 only, because Cd has no model-level reference (PTST helps only its own deployment, footnote ¶).

**Template (no numbers; for §5).**

| Actor | Menu size | Best data arm (F, 90% CI, cost) | Best reference (F, 90% CI, cost) | Reading |
|---|---|---|---|---|
| Cd | a_R, a0, H1, S1, S4, S6 (+ SR if allowed) | [ ] | none (PTST only in own deployment) | [ ] |
| Ch | Cd's menu + B↓LR | [ ] | B↓LR | [ ] |
| Sp | all arms | [ ] | best of PTST, scaling, Safe LoRA, G, B+Qi, B↓LR | [ ] |
| Ow | all arms | [ ] | as Sp | [ ] |
| Dp | a_R, a0, H1, S1, SR, S6; A1, L1, S3, S4 with a proxy | [ ] | none | same-model evidence only |

**Paper text that changes [LEAD]** (wording only; the headline order is the user's 8 Oct choice, so a change of headline order would be **[USER]**):
- §1 ¶1, one new sentence: customers of such services can often also set the learning rate, epochs and batch size (cite the OpenAI reference), and the service controls the recipe.
- §6 "Scope and user": replace the single user with the five actors and point to Table 1's column. This also settles paper decision 10 ("Who the user is").
- Abstract, [FINDING 2]: "per actor, how the best data repair compares with the best option that actor can use".

### 2.5 The reference "recipe B one LR rung lower" (B↓LR) [USER]

**Definition (R for the inputs; I for the arm).** Recipe B with only `train.lr` changed from 1e-4 to 5e-5. The data are unchanged (4,800 Dolly rows), one epoch, 38 steps, LoRA rank 64 on all linear layers, per-row loss, no warmup. The rate 5e-5 is the next rung of the ladder (1e-4, 5e-5, 2e-5) that PAPER §4.1 already defines. The arm does not change OLMo's rung (1e-4): it is a reference, chosen by no outcome.

**Build ($0).** A new config, for example `study-kt-olmo2-1b-r64-b5e5-mb4-<date>.json`, with a test that its diff against REC is the `lr` key only (the pattern of the side study's "exact five-key B→G diff", FOCUS 11 Oct 04:46 UTC). Configs are outside the engine identity (R: BRIEF Facts, engine identity = the top-level `*.py` files), so no engine round is needed. A reference is a stage-1-freeze item, not a wave-1 item (R: BRIEF "Out of scope", B10–B12).

**Seeds [LEAD].** Default 1101–1106, the a0 seeds. Then B↓LR and a0 share the adapter initialization and the data order at each seed, and differ in one knob. The rule "no scorer built on a0-1101 states is evaluated at 1101" does not apply, because B↓LR uses no scorer (the same reasoning ADD §3 uses for the plant arms). Alternative: the method-arm seeds 1102–1107.

**What it may show (E).** Expected erosion E about +32 to +40 pp against a0's +45.1, so a restoration of about 5–13 pp. Basis: the relative change when the LR is halved in other cells: Llama-3.2-1B recipe B −19% (+59.3 → +48.3; M: PAPER development evidence), OLMo-2-1B recipe G −28% (+28.8 → +20.8; M: same), and at 7–8B −28% and −12% (M: FOCUS 11 Oct 12:54 UTC; side-paper data, used here for planning only). So B↓LR is likely as strong as the best data repair at the SESOI scale (I).

**The task-loss limit will likely fail it (E, I).** A sibling draft computes τ_L = 0.0067 from the three Gate A a0 units (s = 0.0024; a0 mean held-out loss 1.545) (R: `prereg-references/tau_l_check.out.json`; not checked by me). Recipe G, which halves the mean LR, gave a held-out loss of 1.612 at seed 1101, and the token-mean-only run gave 1.587 (M: PAPER development evidence). That is +0.067 and +0.042, or 10× and 6× τ_L. A lower LR learns less, so B↓LR very likely exceeds τ_L too (I). The same holds for adapter scaling at λ < 1 (I). So the useful reading is not "B↓LR is feasible" but "where B↓LR sits on the (F, L) frontier against the data repairs". That comparison is the analysis-model draft's frontier rule (matched on task loss). **Flag for the analysis-model draft (I):** L(m) is measured against a0 (PAPER §3.2), and a removal arm trains 12.5% fewer rows, so τ_L ≈ 0.0067 may also fail removal arms by the dose alone. I did not check this; Gate B's R arms would show it.

**Cost at measured rates.**

| Item | Value | Label and basis |
|---|---|---|
| 1B arm, Gate B kit, 3 arms per pod | $1.59 per arm (2.67 billed h × $1.79/h for 3 arms) | M: FOCUS 16 Oct 00:25 UTC |
| 1B arm, upper | arm ≤ 49.0 min + pod overhead ≤ 26.0 min over 3 arms ≈ 57.7 min ≈ $1.72 | M inputs: FOCUS 16 Oct 13:21 UTC; E total |
| 6 seeds | $9.6–10.3 | E (6 × the two values above) |
| + 20% for failed pods and re-runs | $11.5–12.4 | E (REPLAN §2.1 planning allowance) |
| + judges on pods (HarmBench, Granite) | $0.1–0.2 per arm | E (REPLAN §2.1) |
| **Total, B↓LR at 6 seeds on OLMo-2-1B** | **about $12–14** | E |
| Same arm at 7–8B, if the user wants it [USER] | OLMo-2-7B at 5e-5: $20–26; Llama-3.1-8B one rung lower (2e-5, because its rung is already 5e-5): $24–30; both about $45–58 with judges | E: REPLAN §2.1 arm costs ($2.8–3.6 and $3.3–4.1) × 6 × 1.2 |
| Llama-3.2-1B in stage 2 (its rung is 5e-5, so one rung lower is 2e-5) | about $12–15 | E: a Llama 1B arm costs about $1.58–1.96 of job time (R: `stage2-design/llama-gate-b-lite-rules.md`, a sibling draft) |

### 2.6 How to cite the side paper's half-LR result without reusing it [LEAD]

**Facts (R).**
- The side paper ("Same Recipe, Different Fate", ARR #13386, under review) covers "the half learning rate" among its findings (R: PAPER "What changed in revision 6", overlap-rule bullet). Its result is at 7–8B: OLMo-2-7B +44.1 → +31.9 pp; Llama-3.1-8B +60.7 → +53.25 pp; the family difference "not shown" (R: FOCUS 11 Oct 12:54 UTC). The side paper's own wording is "without establishing equal effects", which the 15 Oct records sync calls the correct wording (R: FOCUS 15 Oct 20:05 UTC).
- No OLMo-2-1B recipe-B unit at LR 5e-5 exists anywhere. The causal follow-up planned a 1B arm "H" (constant 5e-5), but no 1B unit was verified (R: FOCUS 15 Oct 20:05 UTC, "Funded replication, seed 1122"). So B↓LR on OLMo-2-1B would be new data.
- ICML 2026 does not allow work that is substantially similar to work under review elsewhere, and it treats overlapping-author ICML submissions as prior work (R: ICML 2026 call for papers). The call page does not state the self-citation format; PAPER decision 32 records "anonymized, with an anonymized copy as supplementary material" from the author instructions (R: PAPER; not re-checked here).
- Training is deterministic on matched hardware (R: PAPER §4.1). So a "fresh" run at the side paper's seed and config would reproduce the side paper's unit byte for byte (I).

**Rules (proposed).**
1. **Cite for motivation only.** One clause in §4.4 or §6, for example: "Lowering the learning rate lowers erosion in other settings (Kim et al., 2025; [CITE: concurrent submission, anonymized])." No side-paper number in the body. If a number is needed, give it as the other paper's result, exactly as its anonymized copy states it, with its own caveat.
2. **New units only.** B↓LR on OLMo-2-1B uses new runs under the stage-1 pre-registration. At 7–8B, if run, use seeds and units disjoint from the side paper's (for example 1104–1109), so that determinism does not reproduce the side paper's units (I). Never count, pool or re-judge a side-paper unit as a main-study arm. (The side paper's 7–8B b5e5 adapters were lost with deleted pods anyway; R: FOCUS 15 Oct 20:05 UTC, "Adapters lost".)
3. **A different claim.** The main paper's claim from B↓LR is about the comparison with data repairs per actor. The arm's own restoration G = F(a0) − F(B↓LR) is reported like every reference's G, with no sentence that frames it as a finding about learning rates across families or sizes.
4. **No recipe contrast.** Do not report B↓LR against recipe G (both have a mean LR of 5e-5) as a finding. Recipe and dose contrasts belong to the side paper (R: PAPER §4.10 item 2). Both arms may sit in one results table, with no claim about their difference.
5. **Check before submission [LEAD].** The ICML 2027 author instructions (not yet published, R: PAPER decision 6) for the self-citation form; the side paper's ARR status and any non-anonymous preprint (the 15 Oct sync notes a 24-page PDF shared by link; R: FOCUS 15 Oct 20:05 UTC).

---

## 3. Item 4: stronger data-only add repairs

### 3.1 Qi et al.'s safety-recovery augmentation: the exact construction (R: arXiv 2406.05946, HTML §3.1–§3.2)

- **Example form.** A triplet (x, h, r): a harmful instruction x, a harmful response h and a refusal r. The model is trained on r, conditioned on x and the first k tokens of h. The harmful prefix carries no loss.
- **Objective (their Eq. 2).** α · E[−log π(r | x, h≤k)] over (x, h, r) and k, plus (1 − α) · E[−log π(y′ | x′)] over benign utility pairs. α = 0.2.
- **Prefix length k.** k = 0 with probability 0.5; otherwise k uniform on [1, 100] tokens. The general form is k uniform on [1, C] with C ≤ |h|.
- **Data.** 256 harmful instructions, mostly from Ganguli et al.'s red-teaming data. The refusals r come from the initial Llama-2-7B-Chat. The harmful responses h come from a jailbroken (fine-tuned) Llama-2-7B-Chat. The utility data are Alpaca instructions with answers from the initial model.
- **Training.** 10 epochs on the 256 recovery examples, LR 2e-5, AdamW; each batch holds 16 recovery and 64 utility examples.
- **Where it sits in the pipeline.** An extra alignment step on the already aligned model, **before** any downstream fine-tuning. It was not mixed into the downstream fine-tuning data. The augmented model was then fine-tuned on Samsum, SQL Create Context and GSM8k (Appendix C, Table 6).

**Consequence (I).** A 48-row arm mixed into our benign Dolly data is an adaptation, not Qi et al.'s method. Name it "recovery-style" and give it a deviation table (the brief's REQ-21 (h) pattern). The deviations: when it is applied (mixed into the benign fine-tune, not a separate alignment step); the dose (48 of 4,848 rows, about 1%, against α = 0.2 over 10 epochs); the LR (recipe B's 1e-4, not 2e-5); the source of h (PKU's unsafe responses, not a jailbroken copy of the same model); k in OLMo tokens.

### 3.2 Building SR from the S-pool [USER for the arm; LEAD for the details]

**The key fact (R: BRIEF REQ-6; ADD L8).** L8's candidate rule takes a PKU response that is safe and refusal-opening **in a record whose other response is unsafe**. So every S-pool row already has its harmful response h in the same PKU record. L8 also fixes how to read a record's companion fields: "by the row's 'line' from the same hash-checked bytes". SR needs no new data source.

**Construction (proposed).**
1. **Prompts and refusals: S4's 48 kept rows (default) [LEAD].** Both papers used the initial model's own refusals (R: §3.1 above; §3.3 below). S4's rows are exactly that: S-pool prompts with the untuned OLMo's greedy refusals, kept by L14's S4 predicate (ended, REFUSAL-OPENING, non-empty, `encode_train` accepts) and generated in L11's 32-prompt chunks with the exact early stop. So SR reuses REQ-9's output and needs no new generation.
   - **Pre-set fallback [LEAD]:** if S4 cannot fill 48 (REQ-9's "fewer than 48 … non-zero exit"), build SR on S1's 48 rows with their PKU refusals, and record the deviation.
2. **The prefix.** h = the PKU-unsafe response of the same record. h_ids = the OLMo codec's encoding of h. Each SR row trains on: prompt ids + h_ids[:k] (no loss) + r ids + end-of-turn (loss).
3. **k, by Qi et al.'s P_k, stratified [LEAD].** A sealed draw picks exactly 24 of the 48 rows for k = 0 (label `stage1-sr-k0-v1`). Each of the other 24 gets k uniform on [1, min(100, |h_ids|)] (label `stage1-sr-k-v1`, part = row id). Stratification removes the dose noise of a 50% coin. The 24 k = 0 rows are then identical to the matching S4 rows, so SR = S4 with 24 rows given a harmful prefix. Alternative: a prefix on all 48 rows (a larger contrast, but SR would then hold no plain refusal, unlike Qi et al.).
4. **Prefix checks (new; counts only; the lead's run) [LEAD].** Set k = 0 for a row, and count the reason, if h is empty, holds a control token, or opens with a refusal by LEX (a recovery prefix must be compliance). No row is truncated; the refusal r is never cut (L14).
5. **Encoding (L14).** The full row must pass `encode_train` under recipe S's `max_train_tokens` (3,072, read from the config, never hard-coded).
6. **Per-row loss (I).** Under recipe B's per-row mean, an SR row's loss is the mean over r and the end-of-turn only, so an SR row weighs the same as an S4 row.

**Disjointness and the anchors (proposed checks, counts only).**
- The prompts are S-pool prompts, so REQ-6's exclusions already hold: no exact or near-duplicate match (character 5-gram Jaccard ≥ 0.5) with any training, query or evaluation prompt form (L9's all-split form set, the lead's counts-only run) or with any of the 128 anchor prompts (R: BRIEF REQ-6; ADD L9).
- **New: check h too.** h_ids[:k] is new text in training. Run the same near-duplicate test of each used prefix against every evaluation prompt form and against every text in the anchor bank (prompts and answers). A row that fails gets k = 0 (counted). Why (I): a prefix close to an evaluation prompt's target behaviour could teach a refusal for that prompt (contamination); a prefix close to a harmful anchor would put anchor text into training. No scorer reads the add rows (A1 and L1 score the 4,800 Dolly rows; S3 scores its own subset), so the check protects evaluation, not the scorers.
- **The plant** comes from PKU-safe DIRECT answers to prompts disjoint from the S-pool (R: BRIEF REQ-8), so it cannot share a record with SR.
- **The overlap control** ("the add effect must also hold on the evaluation prompts least similar to the added rows"; R: PAPER §4.3) must count the prefix text in "the added rows" for SR (I).
- **Text rules (R: BRIEF "Data rules").** The full SR edit holds harmful text, so it lives only under `tmp/`, with a text-free sealed record (ids, SHA-256, token counts, k values, drop counts). It is never printed and never released (paper decision 31).

**The one engine change (R, I).**
- R: the add schema is exactly {row_id, prompt, response} (`edits.py`:131-132, with exact-key checks at :51-52 and :109-110). `encode_train` builds prompt ids + response ids + end-of-turn and sets `n_prompt` to the prompt length (`textproc.py`:173-183). Targets "are always the trailing positions" (`textproc.py`:166).
- I: so a loss-free prefix needs only (a) an optional add field for the prefix text and k, and (b) an encode path that places h_ids[:k] after the assistant header and counts it inside `n_prompt`. Everything after it stays a target. The data structure already supports this.
- I: the change touches `parse_edit`'s exact-key checks, so it is not insert-only. The sibling engine-round draft keeps a pre-set "training-only route" for such symbols (R: `icml-78b-prep/engine-round-Y-design.md` §0, §5.4; a proposal). Tests: targets equal r + end-of-turn exactly; version-1 edits give byte-identical streams; a k outside [1, |h_ids|] refuses.
- **Timing.** No engine file changes until Gate B's last kit pod (R: BRIEF T4). B+Qi's engine change is due at the stage-1 freeze (R: FOCUS 9 Oct 13:45 UTC; the sibling draft's Y3). SR's change should join that round, under one certificate, so it adds no pod (I). **Pre-set fallback [USER-CONFIRM]:** if SR's change is not verified at the stage-1 freeze, SR runs later as a 3-seed secondary arm (one-sided bounds only), as PLAN-S §5.3 treats secondary arms.
- **Rejected alternatives (I).** Training on h as well as r: that trains on harmful text, which is the harmful-data injection that PLAN-S §5.5 dropped (S2). Putting h in the user turn: it removes the point of the method, which is recovery inside the assistant's own turn.

**Contrast and what it can show.**
- **P7 = SR − S4,** two-sided (the depth effect, holding prompts and refusals fixed). Also report SR − a0 and SR − S1.
- I: on U (sampled answers, no prefilling), SR may equal S4. Qi et al.'s case for recovery data rests on robustness to prefilling and deeper attacks. So the decisive endpoint is review B W6's prefilling probe, which is not in the stage-1 design yet. If the user adds SR without a prefilling probe, an "equivalent" on U does not mean "no depth gain". Flag this dependency to the lead.

### 3.3 Safety at One Shot: what "the one example" is (R: arXiv 2601.01887, abstract and HTML)

- **Paper.** "Safety at One Shot: Patching Fine-Tuned LLMs with A Single Instance", Zhang, He, Chen, Lou, Liu, Yang and Jia. arXiv v2, 6 Jan 2026. PAPER's bibliography records it as an ICLR 2026 poster (OpenReview EyH8Fu3vtZ; R: PAPER, not re-checked).
- **The example.** One harmful prompt with a short, general refusal. The paper prints its main example. It comes from the same 256-instruction pool as Qi et al., with refusals from the initial Llama-2-7B-Chat.
- **How it is chosen.** A bi-level selection over the candidate pool. It needs the aligned model, the compromised model and gradients. So the selection itself is not a data-only step.
- **Does the choice matter?** Their Table 4: general refusals do best (ASR 0.0–0.3 from 95.2 on Llama-2-7B-Chat); category-specific refusals give 0.6–16.4. Their Table 8: examples from other sources, PKU-SafeRLHF among them, give results within about 1–2 points.
- **The patch.** A post-hoc fine-tune of the compromised model on the one example: 10 epochs at LR 2e-5. The batch size is not stated.
- **Settings.** Benign compromises are SQL Create, GSM8K and Samsum (no Dolly). Five models; GPT-4.1 through the API with 10 examples, because of the API minimum. ASR by the HarmBench classifier on HEx-PHI; a GPT-4 harmful score on AdvBench.
- **Not in the paper (R, absence in the text read).** No variant that mixes the example into the original fine-tuning data. No systematic over-refusal measure (only a note that a large correction coefficient makes the model refuse benign queries).

### 3.4 Building S6 from the S-pool [USER for the arm; LEAD for the details]

**Construction (proposed).**
1. **The example: S4's first kept row (default) [LEAD].** That is one S-pool prompt with the untuned OLMo's own refusal, chosen by S4's sealed order (`stage1-s4-v1`) and L11/L14's keep rule. It is outcome-free, it follows both papers' refusal source, and it makes S6 a sub-design of S4.
   - Alternatives: (a) a sealed draw of one row from the S-pool minus the S1 list and minus the S4 list, with its PKU refusal (label `stage1-s6-v1`; available to Cd without sampling the model). (b) The paper's own printed example. **(b) is [USER]:** it is not PKU data, so it departs from the user's 9 Oct rule "PKU-SafeRLHF stays the safety data for the add repairs" (R: FOCUS 9 Oct 09:40 UTC), and it must still pass REQ-6's exclusions.
   - Not chosen: the paper's bi-level selection. It needs gradients of a0 (a Sp/Ow action, not data-only) and its discretization is not specified (R: §3.3).
   - **Pre-set fallback [LEAD]:** if S4 cannot fill, use alternative (a).
2. **48 copies.** 48 add rows with distinct ids (for example `add-s6-01` … `add-s6-48`) and identical text. The engine accepts this: it requires distinct, sorted, `add-`-prefixed ids and non-empty text, and has no duplicate-text check (R: `edits.py`:131-134, :157-161). REQ-7's writer needs only a test that the copies are byte-identical apart from the id.
3. **Where the copies land.** The engine spreads added rows evenly through the epoch: added row j of m goes after floor((j + 1) · n / (m + 1)) retained rows (R: `edits.py`:46-50). With n = 4,800 and m = 48, that is one copy after every 98 Dolly rows, about 1.3 copies per 128-row step, from step 1 to step 38 (I, arithmetic). So S6 repeats the patch during training, and its last copy lands in the last step. It is partly, not wholly, a post-hoc patch.
4. **No engine change.** One L14 encode check covers all 48 copies.
5. **Token accounting (R: ADD §5 item 1).** Report the added target tokens (48 × the example's tokens) and the share of the corpus token mass, as for every add arm.

**Disjointness.** As for any S-pool row (REQ-6; L9's form set; the 128 anchor prompts). By the default, S6's prompt is also one of S4's prompts, by design.

**Contrast and what it can show.**
- **P8 = S6 − S4,** two-sided. It holds the row count and the refusal source fixed, and changes 48 distinct examples to one. An "equivalent" label (90% CI inside ±5 pp) reads Safety at One Shot's claim directly at our dose. At the planning noise, that needs a point estimate within about ±2.5 pp (E: CI half-width 1.645 × 1.53 pp). Also report S6 − a0.
- **Over-refusal risk (I).** 48 copies of one refusal may teach a template refusal. O, the selectivity score and the τ_O screen apply as for every add arm (R: PREREG §6; PAPER §4.2). Review B W7 (weak over-refusal limits) applies here with force.

### 3.5 Which existing rules each arm reuses

| Rule (R: BRIEF, ADD) | SR | S6 |
|---|---|---|
| S-pool (REQ-6): candidates, exclusions, one row per prompt, the N report | yes (prompts) | yes (prompt) |
| L8: safe refusal-opening response in a record whose other response is unsafe; read companion fields by `line` | yes: gives h | yes: candidate rule only |
| L9: the all-split form set for near-duplicate checks (lead's counts-only run) | yes, extended to h | yes |
| L10-style overlap reporting | report SR ∩ S1 and SR ∩ S3 subset | report S6 ∩ S1 |
| L11: S4 list of 512 in 32-prompt chunks, exact early stop | yes (S4's refusals) | yes (S4's first row) |
| L13: one label registry, append-only | new labels `stage1-sr-k0-v1`, `stage1-sr-k-v1` (and `stage1-s6-v1` for alternative (a)) | as left |
| L14: caps and keep rules; `max_train_tokens` from the config; never truncate | yes (keep predicate on r; encode check on the full row) | yes (encode check) |
| REQ-7: the add writer and its text-free record | yes, plus the prefix field | yes |
| REQ-9: untuned answers on the pod | reused, no new generation | reused |
| T4: no engine change before Gate B's last kit pod | binds (engine change) | does not bind |

REQ-21 (m) must state that these new labels were named after the sealed Gate B rankings were seen, as L13 (7) requires for every label not named in brief revision 1 (I).

### 3.6 Where P7 and P8 sit, and the power cost [USER]

E (normal approximation, as in PLAN-S §4.3; per-arm seed SD 2.65 pp central, 3.85 pp high; 6 against 6 seeds; 80% power; Holm's first step):

| Placement | Add-contrast MDE, central | Add-contrast MDE, high | Effect on P1–P6 |
|---|---|---|---|
| Today: P1–P6 only (Holm over 6) | 5.3 pp | 7.7 pp | — |
| (A) P7, P8 join the primary family (Holm over 8) | 5.5 pp | 8.0 pp | P1–P6 MDE rises: removal 5.0 → 5.1 pp, add 5.3 → 5.5 pp |
| (B) A new family read after the primary, at its own 5% (Holm over 2) | 4.7 pp | 6.9 pp | none |

**Recommended: (B).** It leaves the user's adopted primary family unchanged (R: FOCUS 8 Oct 13:53 UTC), and the paper already reads each family at its own 5% level (R: PAPER §4.9). Placement (A) changes a pre-registered target that the user adopted, so either choice is the user's.

**The blinded seed rule (R: PLAN-S §4.3).** If Gate B's pooled σ̂ lands in 4.5–6.0 pp, the primary family shrinks to P1, P3 and P6 at 9 seeds. **Pre-set rule [USER-CONFIRM]:** in that case P7 and P8 do not run, and their money returns to the primary family.

### 3.7 Costs at measured rates (E; basis in §2.5)

| Arm | Runs | Money | Build ($0) |
|---|---|---|---|
| B↓LR (reference) | 6 | about $12–14 | one config and its diff test |
| SR (recovery-style) | 6 | about $12–14 (no new generation if built on S4) | the Mac builder (prefix, k draws, checks); the engine field, in the round with B+Qi (no extra pod if it joins that round; one determinism pod, about $2.3, if it needs its own round; E from the sibling engine-round draft) |
| S6 (one-shot-style) | 6 | about $12–14 | a REQ-7 test for copies |
| **All three, 1B** | 18 | **about $36–41** | |
| Same three at 7–8B, both families (option B) | 36 | about $135–175 | E: §2.5's 7–8B arm costs × 3 arms |

Context (R): the stage-1 estimate is about $56–98 (PLAN-S §10), and option B's whole plan about $1,180–1,760 (REPLAN §0). The three 1B arms add about 37–73% to stage 1 and about 2–3% to option B (I, arithmetic). Review B W1 ranks scale above menu breadth, so these arms should not take money from the 7–8B tier (I).

### 3.8 Citations to add to §2 [LEAD]

| Work | Link | Venue (R) | One-line use |
|---|---|---|---|
| Safe Delta: Consistently Preserving Safety when Fine-Tuning LLMs on Diverse Datasets (Lu et al.) | https://arxiv.org/abs/2505.12038 | ICML 2025 ("ICML 2025 Camera Ready" in arXiv comments) | A post-training defence that adjusts the fine-tuning delta and adds a safety compensation vector; evaluated with benign datasets. A Sp/Ow reference candidate. |
| Antidote: Post-fine-tuning Safety Alignment for Large Language Models against Harmful Fine-tuning (Huang, Bhattacharya, Joshi, Kimball, Liu) | https://arxiv.org/abs/2408.09600 | ICML 2025 (arXiv comments) | A one-shot pruning stage after harmful fine-tuning. A Sp/Ow post-hoc repair, aimed at harmful, not benign, data. |
| Harmful Fine-tuning Attacks and Defenses for Large Language Models: A Survey (Huang, Hu, Ilhan, Tekin, Liu) | https://arxiv.org/abs/2409.18169 | ACM Computing Surveys (accepted; arXiv v6, 23 Apr 2026) | Organizes the space by attack setting, defence design and evaluation; cite in §2's opening. |
| Safety Alignment Should Be Made More Than Just a Few Tokens Deep (Qi et al.) | https://arxiv.org/abs/2406.05946 | ICLR 2025 per PAPER's bibliography (not re-checked) | Already cited for B+Qi; add its §3.1 augmentation as the source of SR. |
| Safety at One Shot (Zhang et al.) | https://arxiv.org/abs/2601.01887 | ICLR 2026 poster per PAPER's bibliography (not re-checked) | Already cited; add that S6 is its data-only analogue, and keep §6's sentence that no claim covers the post-hoc patch. |

Review B also lists Eiras et al. (arXiv 2406.10288), backdoor-enhanced safety alignment (arXiv 2402.14968) and Fraser et al. (arXiv 2506.17209). I did not open them.

---

## 4. Timing

| Step | Deadline | Why (R) |
|---|---|---|
| SR's and S6's edit rules, labels, settings and tests (Mac, $0) | before Gate B wave 1 (latest start 27 Oct) | FOCUS 8 Oct 13:53 UTC: rules added later are "post-Gate-B exploratory"; REPLAN §5 |
| The new family (P7, P8), its order and its seed rule in REQ-21 | before wave 1 | same |
| B↓LR's config and its role as a reference | before the stage-1 freeze | BRIEF "Out of scope": references are S1-deadline items |
| SR's engine field | with B+Qi, by the stage-1 freeze | BRIEF T4; FOCUS 9 Oct 13:45 UTC |
| The actor column, per-actor report rule and paper text | before the stage-1 freeze (the report rule), any time (the text) | the report rule must be fixed before outcomes (I) |

If the user decides after wave 1 starts, SR and S6 can still run, but every claim about them is labelled post-Gate-B exploratory (I, from the R rule).

---

## 5. Decisions

| # | Decision | Mark | Default / recommendation |
|---|---|---|---|
| T1 | Add the "Actor" column (§2.3) and the per-actor report rule (§2.4); rewrite §1 ¶1, §6 "Scope and user" and [FINDING 2] | [LEAD] ($0; settles paper decision 10) | yes |
| T2 | Add B↓LR (OLMo-2-1B, LR 5e-5, 6 seeds, about $12–14) as a sixth reference | [USER] | yes |
| T3 | B↓LR seeds | [LEAD] | 1101–1106 (the a0 seeds) |
| T4 | B↓LR at 7–8B (about $45–58 for both families) and on Llama-3.2-1B in stage 2 (about $12–15) | [USER] | decide with the re-plan's option B/C; fresh seeds disjoint from the side paper's |
| T5 | The citation rules for the side paper (§2.6) | [LEAD] | as written |
| A1 | Add SR and S6 (48 rows, 6 seeds, about $24–28 together) | [USER] | yes, if new money arrives; S6 first if only one |
| A2 | Their placement: a new family (B) or the primary family (A) | [USER] | (B) |
| A3 | SR built on S4's rows, with the S1 fallback; k stratified 24/24; the prefix checks | [LEAD] | as written |
| A4 | SR's engine field in the round with B+Qi | [LEAD] | yes |
| A5 | S6's example: S4's first kept row, with fallback (a) | [LEAD] | as written; the paper's printed example would be [USER] |
| A6 | Add the §2 citations (§3.8) | [LEAD] | yes |
| P1 | **The package under "ambitious default, pre-set fallback":** default = B↓LR, SR and S6 at 6 seeds at 1B, in their own family. Fallbacks, fixed now: (i) money short → S6 and B↓LR only; (ii) SR's engine field not verified at the stage-1 freeze → SR as a 3-seed secondary arm; (iii) seed plan B fires → P7 and P8 do not run; (iv) S4 cannot fill → SR on S1's rows, S6 by alternative (a) | [USER-CONFIRM] | adopt once the user confirms the rule in the lead's chat |

---

## 6. Challenge: simpler options, weak assumptions, failure cases, decisive checks

**Simpler alternatives.**
- *Item 3, no new arm:* read the adapter-scaling curve as the customer's LR lever. Rejected (I): a customer cannot scale an adapter, and scaling a trained delta is not training at a lower rate.
- *Item 3, use recipe G as the "lower LR" reference:* rejected (I): G changes the schedule and the loss together (review B W4), and an API customer can set neither.
- *Item 4, only S6:* no engine change, about $12–14. This is a good fallback (P1 (i)). It answers "is one example enough", not "does depth help".
- *Item 4, SR at 3 seeds as a secondary arm from the start:* cheaper (about $6–7, E), but one-sided bounds only, so it cannot give the "equivalent" or "better" labels that review B's accept condition (a) asks for (R: REV-B §6).

**Weak assumptions and counterexamples (I).**
1. *U can see depth.* Counterexample: SR restores the same refusal openings as S4 and differs only under prefilling. Then P7 reads "equivalent" on U while SR is in fact deeper. Settles it: review B W6's prefilling probe (not in the design; flagged).
2. *The one-shot effect survives mixing.* Counterexample: later benign rows wash out the example, so S6 ≈ a0 while the post-hoc patch would work. Our design cannot then say anything about the patch (§6 already says so).
3. *B↓LR stays in the partial-erosion range.* Counterexample: E falls below 20 pp, so B↓LR wins on U but fails τ_L by far. Then the frontier comparison of the analysis-model draft, not the label, carries the reading.
4. *S4 fills 48.* If it does not, SR and S6 use their fallbacks; the build must test both branches.
5. *Closed services accept these rows.* Foundry screens training data (R); whether PKU prompts and, above all, SR's harmful prefixes pass is UNVERIFIED. If they fail, SR leaves Cd's and Ch's menus.

**Failure cases to test in the build (I).** A prefix that re-encodes to different tokens (use h_ids[:k] directly, never decoded text); a row whose prefix holds a control token (k = 0, counted); an S6 edit whose copies differ by one byte (refuse); an SR row whose total length passes 3,072 (refuse and count, never truncate).

**Smallest decisive checks, all $0.**
1. **For SR, now:** a counts-only Mac run (the lead's) over S1's 48 records and the S4 candidate list's records: how many have h non-empty, without control tokens, not refusal-opening by LEX; the h-length histogram (≥ 1 and ≥ 100 OLMo tokens); and the near-duplicate drops of h against the evaluation forms and the anchor bank. If fewer than about 24 usable prefixes exist among S4's candidates, SR is not worth building (I).
2. **For B↓LR:** the config-diff test (only `lr` differs from REC).
3. **For the actor column:** none; it is text.

---

## 7. Process record

- **Changed files:** this file only: `/Users/spiderishi/Coding/attribution/.claude/worktrees/kind-hawking-a6ce04/tmp/gi-vi-parallel/stage1-review-b/check-threat-model-add-repairs.md`.
- **Commands run (all exit 0):** `date -u` (3 times); `ls`, `grep`, `awk`, `wc` over the sources; `shasum -a 256` over 10 source files; `git branch --show-current` and `git log -1` in the main checkout; one `python3` arithmetic script (power, costs, positions; no data read); reads of `edits.py` and `textproc.py`; `cat` of the sibling's `tau_l_check.out.json` (numbers and hashes only).
- **Web reads (WebFetch/WebSearch):** arXiv 2406.05946 HTML (two parts), 2601.01887 abstract and HTML (two reads), 2505.12038, 2408.09600, 2409.18169; the OpenAI fine-tuning reference (first 100,000 characters only) and the supervised fine-tuning guide; the Foundry safety-evaluation page; the ICML 2026 call for papers; one web search on the OpenAI message `weight` key (third-party results only).
- **Not done:** no run, pod, spend, download, install, commit or agent. I did not read the side paper or its results files. I did not open Eiras et al., the backdoor paper or Fraser et al. I did not verify the venue lines that PAPER's bibliography holds (Qi et al.; Safety at One Shot). I did not check τ_L myself (the sibling computed it). I did not open any held-out, hidden, selector or wave-0b row file.
- **Acceptance (the brief's asks):** item 3: threat model, actor column, per-actor report, B↓LR cost, side-paper citation rule: done. Item 4: exact constructions, builds from the S-pool, disjointness, costs, reused rules (S-pool, L8, L11, L14 and others), citations with links: done. No test was run, because nothing was built.
- **Unresolved concerns.** (1) τ_L ≈ 0.0067 may fail every dose-lowering reference and possibly every removal arm; the analysis-model draft should check this. (2) SR's value depends on a prefilling probe that the design does not hold. (3) The OpenAI message `weight` key and the services' data screens are UNVERIFIED, so the Cd/Ch cells for SR are uncertain. (4) The post-hoc one-shot patch is in closed customers' menus (R: §2.1), so leaving it out remains the paper's largest gap on W3 and W5; its inclusion is the user's open scope decision.
