# A loss that protects refusal openings: options

**SCOPE DECISION FOR THE USER.** This is a possible change of scope. Nothing here is approved. Nothing runs, nothing is built and nothing is spent without the user's explicit go. The lead (General Implementation IV) is told before any pod or money is used.

Written 2026-10-08T17:11 UTC (clock checked) by the Side Project chat. Development evidence only. $0 spent. No answer or prompt text was read or printed.

Labels: **R** = read or computed (source given); **I** = inference; **UNVERIFIED** = not checked.
Sources (main checkout, read only): **KT** = `research/experiments/2026-10-07-kill-test-stage0-results.md`; **MECH** = `research/review/2026-10-08-mechanism-first-tokens.md`; **F** = `research/FOCUS.md`.

## 1. The question

Recipe G already keeps more refusal openings than recipe B (KT:260). Could a loss that protects the first answer tokens cut OLMo-2-1B's erosion further? And is that worth money now?

## 2. It is not a new method

The FAQ chat's novelty check (F, FAQ entry 15:59 UTC) found each version close to prior work. This chat's paper check opened every paper below on 8 Oct (arXiv abstract and HTML full text; Qi also in the ICLR 2025 PDF):

| Version | Closest prior work (opened) |
|---|---|
| Keep the first tokens of the benign targets near the aligned model, with a per-position β | Qi et al. 2406.05946 (ICLR 2025), constrained SFT, Eqn 3: β₁ = 0.5, β_t = 2 for t = 2–5, β_t = 0.1 after |
| Warmup only (already in recipe G) | Qi et al., Table 9 of the ICLR version (Table 5 in arXiv v1), Llama-2-7B-Chat, ASR %: Samsum 23.4 → 3.8 with warmup, 23.1 constrained, 3.2 both; SQL 15.4 → 3.3 warmup, 2.0 constrained, 3.2 both; GSM8k 3.3 → 2.9, 3.1, 2.0. On benign data, adding the objective to warmup gained at most about 1 pp. The authors credit the objective mainly in the attack rows |
| KL to the aligned model on safety data | SafeGrad 2508.07172 (gradient projection plus a KL term on alignment data); Lisa 2405.18641 (alternating steps with a proximal term; no KL) |
| Hinge on the refusal-opening margin | The main study's S4 arm (the untuned model's own refusals, 48 rows) is the data version (R: F, stage-1 primary family) |
| Reweight or mask tokens by risk or position | TOSS 2603.01185 (token-level selection; it notes the harmful signal sits in the first response tokens, and that masking those alone costs utility) |
| KL on selected "safety tokens" | PACT 2603.07445 (KL to the aligned model on a weighted top-K token set, at every position) |
| Protect the opening through the data | LookAhead Tuning 2503.19041 (previews the first answer tokens or a fixed prefix; no KL) |

So any result would be a test of known ideas at 1B, not a new method. The honest scientific question it could answer is narrower: **how much of benign erosion at 1B is "shallow", that is, removable by keeping the opening?**

**Qi's Table 9 in our terms (I).** Their warmup runs end near a 3% floor, so the objective had little left to remove. Our recipe G still erodes by 29 pp, so their table does not tell us what Qi + G would do here. It does say the extra gain over warmup can be small.

## 3. How much could it reach? A correction to the 12–19 pp ceiling

The brief and F say: the opening switch carries 0.42–0.64 of the erosion, so at most about 12–19 of recipe G's 29 pp is reachable.

**That range is a descriptive share, not a ceiling.** The 0.42–0.64 comes from a symmetric decomposition (MECH:59, :134). It splits the joint change evenly between "fewer refusal openings" and "less safe answers within each opening". A loss that restores the openings would remove more than half if restored openings behave like natural ones.

Two counterfactuals bound it. Computed by this chat from the frozen opening × label crosstabs (R: `tmp/family-probe-olmo2-1b-g/mechanism-g/results.json`, lexicon `bbbc71e9…`; script in this session's scratchpad, `ceiling/ceiling.py`; counts only):
- **Restore:** the untuned opening mix with the fine-tuned Unsafe rate inside each opening. This is what a perfect opening loss reaches if a protected refusal opening is as safe as a natural one.
- **Switch only:** the fine-tuned opening mix with the untuned Unsafe rate inside each opening.

| Unit | E (pp) | Restore reaches | Switch only | Symmetric share (the note's) | Fine-tuned Unsafe rate in refusal / caveat / direct openings |
|---|---|---|---|---|---|
| OLMo B, seed 1101, sampled | +43.5 | 35.4 pp (0.81) | 9.5 pp (0.22) | 22.4 pp (0.52) | 0.023 / 0.227 / 0.676 |
| **OLMo G, seed 1101, sampled** | **+29.0** | **21.4 pp (0.74)** | 6.6 pp (0.23) | 14.0 pp (0.48) | 0.027 / 0.229 / 0.604 |
| OLMo B, greedy | +42.0 | 39.3 pp (0.94) | 3.1 pp (0.07) | 21.2 pp (0.50) | 0.000 / 0.000 / 0.846 |
| OLMo G, greedy | +21.0 | 16.8 pp (0.80) | 0.9 pp (0.04) | 8.9 pp (0.42) | 0.000 / 0.167 / 0.849 |
| Qwen 1.5B B, sampled | +75.2 | 48.4 pp (0.64) | 47.7 pp (0.63) | 48.0 pp (0.64) | 0.273 / 0.714 / 0.842 |

The symmetric shares reproduce MECH's 0.52, 0.48, 0.50, 0.42 and 0.64 exactly, so the inputs match.

**Reading (I):**
- On top of recipe G, an opening loss could remove anything from about 0 to about 21 pp (sampled). The 14 pp symmetric share is a middle value, not an upper bound.
- The top of the range needs a causal fact we do not have: when a fine-tuned model is made to open with a refusal, does it stay safe? Natural refusal openings are 2.7% Unsafe under G, but they are selected. They occur on prompts where the model still "wants" to refuse.
- Qwen differs: its refusal openings are already 27% Unsafe after fine-tuning (refuse-then-comply). So opening protection would help Qwen less, in share.
- **Judge caveat:** Qwen3Guard sees the whole answer, and its refusal flag follows its safety verdict (MECH:100). A refusal opening may make the guard call an answer safe for that reason alone. Any test of this question needs the HarmBench compliance judge as well.

## 4. The smallest decisive check: a prefill test (no new loss)

**What.** Take a fine-tuned OLMo adapter. For each harm prompt where the untuned model's greedy answer opens with a refusal (171 of 200; MECH:61), force that opening's first k tokens (k = 3; also 1 and 5 if cheap), then let the fine-tuned model continue. Judge the continuations.

**Readout.** P(Unsafe | forced refusal opening), with HarmBench as the primary judge and Qwen3Guard second. Compare it with the natural rates: about 0.03 in refusal openings and 0.60–0.68 in direct openings.

**Rule, to fix before any run (proposal):**
- Forced rate ≤ 0.10: openings act causally. The upper end (about 21 pp on G) is plausible. A loss is worth considering.
- Forced rate ≥ 0.40: openings are mostly cosmetic. Stop; no loss build.
- In between: report it; keep the scope as it is.

**Cost and blockers.**
- No OLMo or Qwen adapter is on the Mac. I checked the main checkout's `tmp/`: only the 2 October pilot adapters are there (R).
- The G pod `olmo2-1b-g-1101` is stopped with its e1 adapter state (KT:259). Whether the seed 1102 and 1103 recipe-B pods still exist is UNVERIFIED.
- Path: the lead starts one stopped pod briefly to copy the adapter out, or runs the test there. Estimate about $0.5–1.5 of pod time. Then generation and both judges on the Mac at $0, about 2–4 h of Mac GPU time, shared with the lead's jobs.
- It needs one small pinned script outside the engine identity, like the margin script in MECH §7. This chat can write and test it on the Mac.

**Why this first (I).** It decides between "worth building" and "not worth building" for about $1, and it does not touch the engine.

## 5. The options

| Option | What | Money (estimate) | Build | Main study impact | What it can claim |
|---|---|---|---|---|---|
| **A. Nothing now** | Record this note and the novelty check | $0 | none | none | nothing |
| **B. Prefill check** (§4) | Measure whether forced refusal openings stay safe | about $0.5–1.5 plus Mac time | one pinned script, no engine change | none | how "shallow" the erosion is at 1B (development evidence) |
| **C. Reference arm** | Add G + Qi constrained SFT as a 4th model-level reference in stage 1, 6 seeds | about $12 compute | 1–2 engine rounds (new identity) | changes the stage-1 design; the lead and the user must amend the pre-registration | a known defence as a comparator; no novelty claim |
| **D. Full experiment** | G vs G+Qi vs G+variant, 6 seeds each (1102–1107) | about $38 compute | 1–2 engine rounds (new identity) | competes with Gate B for money | a test of the opening account; no new method |

**Money context (R: F; KT:281).** The RunPod balance was $12.93 at 16:49 UTC. Gate B needs about $51–62 (about $33–44 if its extension and control are declined), per the lead's DRAFT 4a/4b. So C and D cannot run before a top-up without delaying Gate B.

**Power for D (I; rough).** Take the per-seed SD of E as 3–4.5 pp (OLMo's 2.65 pp rests on 2 df; the main study's plan-A limit is 4.5 pp). With 6 seeds per arm, the 80% minimum detectable difference between two arms is about 6–8 pp before any multiplicity correction. The reachable effect on top of G is 0–21 pp (§3), and Qi's own result says warmup, which G already has, does most of the work. So D could easily end "inconclusive" unless §4 first shows that openings act causally.

**A simpler alternative to C (I; UNVERIFIED details).** If the main study wants a model-level defence as a comparator, Safe LoRA (a projection applied to a trained adapter) needs no training-loss change, and FAQ's main-track list already names it (F, FAQ item 4). It still needs evaluation runs. Its fit to OLMo-2's public checkpoints is UNVERIFIED.

## 6. Build sketch (only if C or D is approved)

- **New opt-in option `qi_constrained`** with its own engine identity. The main study's pinned identity, fixtures and records stay untouched.
- **Reference log-probabilities.** Cache π₀'s per-token log-probabilities for the 4,800 training targets in one pre-pass, and hash the cache. Alternative: compute them on the fly with the LoRA adapter disabled (π₀ is the base model with the adapter off), which costs one extra forward pass per step and needs no storage. The cache is easier to audit and fits the engine's hash checks.
- **Loss.** Per token t of the response: (2/β_t) · softplus(−β_t · Δ_t), with Δ_t = log π_θ(y_t | x, y_<t) − log π₀(y_t | x, y_<t). This chat derived this form from Qi's description (a per-token sigmoid log-ratio loss, Eqn 3); check it symbol by symbol against Eqn 3 before any build. Normalise with G's token mean. β_t by position: Qi's schedule (β₁ = 0.5, β_t = 2 for t = 2–5, β_t = 0.1 after).
- **Tests:**
  1. **Step-0 equality.** LoRA starts with B = 0, so π_θ = π₀ and Δ_t = 0 at step 0. The gradient of each term is −2σ(−β_t Δ_t) ∇log π_θ, which equals −∇log π_θ at Δ_t = 0 for every β_t. So the step-0 gradient must equal recipe G's gradient to float tolerance.
  2. **Small-β limit.** As β_t → 0 the term tends to a constant minus Δ_t, so the gradient tends to G's at any step.
  3. **Large β.** When Δ_t > 0 at an early position, the per-token gradient weight falls towards 0 (the target token's probability cannot drift far above π₀).
  4. Identity: a new hash; the old identity and its fixtures are byte-identical.
  5. One fixture run on the pod with the preflight's equal keys.
- **Positions** are response tokens after the chat template's assistant header, per family.
- **Data rule for any "variant" that uses safety prompts during training:** the prompts must come from a separate public source, filtered against every evaluation split (the engine's near-duplicate walk), never from the dev or held-out banks.

## 7. Recommendation

1. **Option A now.** The loss is not new, the money is short of Gate B, and the ceiling is unknown in the direction that matters.
2. **If the user wants one step, Option B**, after or alongside Gate B funding, with the lead's agreement for the pod minutes. It is the only option that can say whether C or D is worth paying for.
3. **The `bt` arm** (recipe B + token-mean loss only, OLMo, about $1.5; KT:261) also informs this question. It separates G's two changes. If token-mean alone gives most of G's cut, the "loss mass on the first tokens" account (MECH:68–69) gains support.
4. **Not D before Gate B.** Revisit only if B shows a forced refusal opening stays safe.
5. **C only if the lead wants a model-level defence reference** for stage 1. Then compare Qi against Safe LoRA on build cost first.

## 8. Open points

- Whether seeds 1102/1103 pods (recipe-B adapters) still exist (ask the lead).
- Whether a Mac (MPS) continuation run is close enough to the pod's sampling for a within-Mac comparison. Forced and free generations would both run on the Mac, so the comparison is internal (I).

## Addendum, 2026-10-08T21:45 UTC (clock checked): the token-mean-only result

The lead's `bt` run (OLMo seed 1101, recipe B with only a token-mean loss; pre-registered 20:01 UTC; read 21:36 UTC; FOCUS, main checkout) gives E = +43.7 pp, the same as recipe B (+43.5). The pre-registered prediction (E_bt ≤ 36.25) failed. The loss weighting explains none of recipe G's cut; the schedule (a 4-step warmup and cosine decay, which also halves the mean learning rate over the epoch) explains all of it.

What this changes here (I):
- **Recipe G's protection of refusal openings (§3) comes from the schedule, not from less loss mass on the first tokens.** The "first-token loss mass" account (MECH:68–69) loses its main support.
- **A position-weighted loss has less reason behind it.** Weighting first tokens differently is the lever that `bt` just found to do nothing at this scale. The lever that worked is gentler early steps, which Qi et al.'s Table 9 (warmup) already covers. That strengthens recommendation 1 (Option A, nothing now).
- **The prefill check (Option B) is unchanged.** It asks a causal question about openings that does not depend on why G works.
- **Qi's constrained SFT is still the approved stage-1 reference arm** (the user, 17:36 UTC). This note does not change that decision.
