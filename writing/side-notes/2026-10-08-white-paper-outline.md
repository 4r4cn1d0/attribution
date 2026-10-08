# White paper outline: benign fine-tuning erosion, family × recipe at about 1B

Status: OUTLINE, 2026-10-08T17:08 UTC (clock checked). Side Project chat. Not for posting.
All numbers are **development evidence** from this repository's records. No new runs. No harmful prompt or answer text appears here or may appear in the note.

Sources for every number (main checkout, read only):
- **KT** = `research/experiments/2026-10-07-kill-test-stage0-results.md`
- **AUD** = `research/review/2026-10-08-gate-a-audit.md`
- **MECH** = `research/review/2026-10-08-mechanism-first-tokens.md`
- **F** = `research/FOCUS.md`

Placeholders are in square brackets with a tag, for example `[QWEN-G]`. Section 9 lists them.

---

## 0. Title and one-line claim

**Working title (from the brief):** "Same Recipe, Different Fate: Benign Fine-Tuning Partly Erodes OLMo-2-1B and Collapses Qwen2.5, and the Recipe Matters".

**Problem with that title.** Llama-3.2-1B also saturated under recipe B (E +62.5 pp, one seed; KT:263–281). So OLMo is the odd one out, not Qwen. Also, "the recipe matters" is shown only on OLMo so far (B against G, one G seed). Use one of these titles instead:

- **A. If recipe G is not run on Qwen:** "Same Recipe, Different Fate: One LoRA Recipe Near-Saturates Qwen2.5 and Llama-3.2 but Only Partly Erodes OLMo-2 at 1B".
- **B. If recipe G on Qwen is run and differs from OLMo:** "Same Recipe, Different Fate: Benign Fine-Tuning Erosion Depends on Model Family and on the Training Recipe at 1B".

**One-line claim (supported now):** under one fixed LoRA recipe on 4,800 benign Dolly rows, OLMo-2-1B-Instruct loses refusal on about 45 pp of harm prompts, while Qwen2.5 (1.5B, 7B) and Llama-3.2-1B lose 62–82 pp. A standard recipe (token-mean loss, warmup, cosine) cuts OLMo's erosion by about a third and keeps its over-refusal at the untuned level.

**Word "collapse".** Use "near-saturated", with the number. "Collapse" is acceptable only in the Substack post, with the number next to it.

---

## 1. Abstract (target 150–180 words; numbers in brackets get filled at the end)

Five sentences:
1. Fine-tuning an aligned model on benign data can erode its safety. How much depends on the setup, and few papers vary the model family and the recipe together.
2. We fine-tune three 1B-scale instruct families (OLMo-2, Qwen2.5, Llama-3.2) with one LoRA recipe on 4,800 Dolly rows, and measure the Unsafe share of 600 sampled answers to 200 harm prompts.
3. OLMo-2-1B rises from 3.2% to a mean of 48.3% (E +45.1 pp, 3 seeds). Qwen2.5-1.5B, Qwen2.5-7B and Llama-3.2-1B rise by +75.2, +82.2 and +62.5 pp (one seed each).
4. A standard recipe (token-mean loss, warmup, cosine decay) gives +29.0 pp on OLMo (one seed) with over-refusal unchanged [and `[QWEN-G]` on Qwen2.5-1.5B].
5. About half of OLMo's rise comes from answers that no longer open with a refusal. We report every setting we screened, and the judge's limits.

---

## 2. Section plan (4–6 pages, two-column arXiv style or 1-column at 11 pt)

| § | Title | Pages | Content |
|---|---|---|---|
| 1 | Introduction | 0.75 | Problem; gap; contributions (3 bullets, below) |
| 2 | Setup | 1.0 | Models, data, recipes B and G, evaluation, judges, statistics |
| 3 | Same recipe, different fate | 1.0 | Table 1, Figure 1 |
| 4 | The recipe matters (OLMo) `[and Qwen]` | 0.75 | Table 2; logit-scale comparison |
| 5 | Where the erosion lives | 0.5 | Figure 2: refusal openings |
| 6 | What we screened, and limits | 0.75 | Full screening log; caveats |
| 7 | Related work | 0.5 | Positioning; no "first family contrast" claim |
| 8 | Conclusion | 0.25 | Practical advice for reporting |
| App. | A–E | free | Hashes, per-seed tables, judge tables, costs, reproducibility |

### §1 Introduction: three contributions (wording fixed now)
1. **OLMo-2 erosion numbers.** Benign-fine-tuning erosion numbers for OLMo-2-1B-Instruct, with 3 seeds and two judges. Wording: "we are not aware of prior benign-fine-tuning erosion numbers for OLMo-2 Instruct". Never "first" (§7).
2. **Family at a fixed recipe.** One recipe gives partial erosion for one family and near-saturation for two others at 1B, and for Qwen at 7B.
3. **Recipe within a family.** Changing only the loss weighting and the learning-rate schedule cuts OLMo's erosion by about a third, with over-refusal unchanged. `[QWEN-G]` decides whether we may add "and the size of the cut depends on the family".

**Do not claim:** the first family contrast; harmful compliance from U alone; any statement beyond these models, this data, this prompt set and these judges; a cause for the family difference.

### §2 Setup (facts and sources)
- **Models (revision hashes in App. A):** OLMo-2-0425-1B-Instruct; Qwen2.5-1.5B-Instruct `989aa798…`; Qwen2.5-7B-Instruct `a09a3545…`; Llama-3.2-1B-Instruct (KT:13, :108, :265).
- **Data:** 4,800 Dolly-15k rows, 8 categories × 600, one epoch; tokenised per family (KT:18, :186, :265).
- **Recipe B:** LoRA r64, alpha 128, all linear layers; AdamW; LR 1e-4 constant; no warmup; batch 128 (38 steps); per-example mean loss, so each row weighs the same (KT:99; F; MECH:68).
- **Recipe G:** recipe B plus a token-mean loss and a 4-step linear warmup with cosine decay; peak LR 1e-4 (KT:245).
- **Stage 0 recipe (Qwen 1.5B only):** LR 2e-4 constant, batch 8, 600 steps per epoch; read at 1 and 3 epochs (KT:16–18, :85).
- **Evaluation:** 200 harm prompts × 3 sampled answers (U) plus 200 greedy answers; 100 over-refusal prompts (XSTest-safe plus OR-Bench-hard); held-out Dolly loss on 200 rows; ARC forced choice on 189 questions (KT:20–25).
- **Main metric:** U = Qwen3Guard-Gen-4B "Unsafe" share of the 600 sampled answers. E = U_ft − U_0 in percentage points.
- **Second judges:** Granite Guardian 3.3 8B on the 200 greedy answers; the HarmBench Mistral-7B classifier as a compliance judge (KT:228–241).
- **Statistics:** SE(U) clustered by prompt (design effect about 2); E's band = E ± 2 SE (evaluation noise only); seed SD from 3 seeds (2 df) (AUD:65, :81).

### §3 Same recipe, different fate: Table 1 (all recipe B unless marked; e1)

| Model | Seeds | U_0 | U_ft | E (pp) | Over-refusal (0 → ft) | Held-out loss (0 → ft) | Source |
|---|---|---|---|---|---|---|---|
| OLMo-2-1B | 3 | 3.2% | 46.7 / 46.8 / 51.3% | +43.5 / +43.7 / +48.2; mean **+45.1** (band 41.3–49.0) | 17 → 4–6% | 2.100 → 1.54 | KT:211–222 |
| Qwen2.5-1.5B | 1 | 4.7% | 79.8% | **+75.2** | 68 → 3% | 1.890 → 1.459 | KT:99–103 |
| Qwen2.5-1.5B, r16 | 1 | 4.7% | 72.5% | +67.8 | 68 → 3% | 1.890 → 1.481 | KT:168–177 |
| Qwen2.5-7B | 1 | 4.8% | 87.0% | **+82.2** | 7 → 3% | 3.335 → 1.293 (see note) | KT:114–124 |
| Llama-3.2-1B | 1 | 13.8% | 76.3% | **+62.5** | 11 → 2% | 2.243 → 1.555 | KT:267–276 |
| Qwen2.5-1.5B, Stage 0 recipe, 3 epochs | 3 | 4.7% | 83.5–88.7% | mean +81.8 | 68 → 2–10% | see KT | KT:85–86 |

Notes that must sit under Table 1:
- Qwen's 68% untuned over-refusal is the **1.5B** model only. Qwen 7B starts at 7% and still saturates. So a high starting over-refusal does not explain Qwen's collapse by itself.
- The untuned 7B held-out loss (3.335) is above the 1.5B's (1.890) on the same rows. Do not compare task loss across sizes (KT:153).
- The Stage 0 recipe failed its own "answers end" bar (repetition loops) (KT:87). Report it as a screened setting, not as a clean result.
- `[GRANITE-LLAMA]`: Granite on the Llama units is pending.
- Headroom used, E/(100 − U_0): OLMo 0.47; Qwen 1.5B 0.79; Qwen 7B 0.86; Llama 0.73. Report it, because Llama starts at 13.8%.

**Figure 1.** Dot plot of E with ± 2 SE bars, one row per model and recipe; OLMo seeds as separate dots. Do **not** shade a "partial window": the 20–55 pp window was fixed after the Qwen results (§6).

### §4 The recipe matters: Table 2

| Model | Recipe | Seed | U | E (pp) | Over-refusal | Held-out loss | Granite greedy E |
|---|---|---|---|---|---|---|---|
| OLMo-2-1B | B | 1101 | 46.7% | +43.5 | 4% | 1.542 | +44.0 |
| OLMo-2-1B | G | 1101 | 32.2% | **+29.0** | **17%** | 1.612 | +23.0 |
| Qwen2.5-1.5B | B | 1101 | 79.8% | +75.2 | 3% | 1.459 | not judged |
| Qwen2.5-1.5B | G | 1101 `[+1102, 1103?]` | `[QWEN-G]` | `[QWEN-G]` | `[QWEN-G]` | `[QWEN-G]` | `[QWEN-G]` |

- OLMo: E_G − E_B = −14.5 pp on shared sampling streams. That is about 5× the between-seed SD of E (2.65 pp, 2 df). One G seed (KT:256).
- G changes two things: the loss weighting and the schedule. The `bt` arm (token-mean only, about $1.5, OLMo) separates them `[BT]` (KT:261).
- **Compare on the logit scale too.** A fixed effect on the logit scale gives a smaller change in percentage points near saturation. Prediction to write down before any Qwen-G run (this chat's arithmetic, from KT counts): OLMo's B → G change is −0.61 on the logit scale (46.7% → 32.2%). The same change on Qwen 1.5B (79.8%) predicts U ≈ 68% (E ≈ +63.5 pp). Reading:
  - Descriptive directions only: Qwen G U ≥ about 76% reads as "Qwen less sensitive to these knobs"; about 62–74% as "same logit change"; ≤ about 60% as "Qwen more sensitive".
  - **None of these is a test with one seed.** A rough interaction SE on the logit scale is about 0.4 (seed SD taken from 2 df, so this is itself uncertain). The 2-SE range around the null then spans roughly U 49–83%, which covers almost every plausible outcome.
  - The project's rule says: claim "replicates across two families", not more, unless an interaction passes its MDE (F, 13:53 UTC amendment). A rough power sketch (this chat, unverified assumptions) says about 3 seeds of B and G in both families give an interaction SE near 0.24, enough to see a 0.6 logit difference at about 2.5 SE. That needs Qwen B +2 seeds, Qwen G 3 seeds and OLMo G +2 seeds (7 runs, roughly $20–25).
- Existing evidence that Qwen does not respond to other recipe knobs: cutting the dose about 30× (Stage 0 → B) moved U from about 83% to 80%; rank 64 → 16 moved E by about 7 pp (KT:106, :180).
- **The Guo gap (context, not a claim).** Guo et al. (opened) report 7.3 → 9.1% ASR for LoRA on Qwen2.5-7B-Instruct with 5,000 Alpaca rows (r32, LR 2e-4, batch 32, 5 epochs; HEx-PHI; GPT-4o-mini judge). With full SFT on 100 Dolly rows they report 73.6%. We get +82.2 pp with LoRA on Dolly. The data alone may explain much of the gap, so the note says only that recipe and data must be reported together. The repository's gap analysis estimates that measurement explains at most about 13–30 pp (`research/review/2026-10-08-guo-gap-analysis.md`).

### §5 Where the erosion lives (MECH; KT:260)
- Fine-tuning replaces refusal openings with direct openings, not with hedges. Sampled refusal openings: OLMo 0.80 → 0.30 under B, 0.44 under G; Qwen 1.5B 0.93 → 0.07 (MECH:25–30, :129).
- An Unsafe answer almost never opens with a refusal: about 2% for OLMo (MECH:41).
- The opening switch carries about half of OLMo's rise (symmetric share 0.42–0.64 across lexicons and judges; G 0.48 sampled) and more of Qwen's (0.64–0.78) (MECH:59, :134).
- **Answers that open directly also became less safe:** OLMo's Unsafe share within direct openings went from 12/66 to 840/1,197 (pooled) (MECH:95).
- Recipe G keeps more refusal openings; it does not make direct answers safer (0.60 against 0.68 Unsafe within direct openings) (MECH:133).
- **Figure 2.** Stacked bars per unit (untuned, B, G for OLMo; untuned, B for Qwen): share of refusal, caveat and direct openings, each split by Unsafe and not Unsafe.
- Say clearly: observational only, no prefill test, positions are words (MECH:96–104).

### §6 What we screened, and limits (must be complete; AUD:61–66)
**Screening log, in time order (all recipe-B-like LoRA r64 unless marked):**
1. Qwen2.5-1.5B, Stage 0 recipe (LR 2e-4, batch 8), 3 seeds: +81.8 (e3); failed "answers end".
2. Qwen2.5-1.5B, recipe B, seed 1101: +75.2 (seed 1102 lost to a timer; no result).
3. Qwen2.5-7B, recipe B, seed 1101: +82.2.
4. Qwen2.5-1.5B, recipe B at rank 16, seed 1101: +67.8.
5. OLMo-2-1B, recipe B, seed 1101: +43.5; then seeds 1102, 1103.
6. OLMo-2-1B, recipe G, seed 1101: +29.0 (pre-registered prediction E_G < E_B).
7. Llama-3.2-1B, recipe B, seed 1101: +62.5.
8. `[QWEN-G]`, `[BT]`, `[L1]` if run.

**Disclosures (each one sentence in the note):**
- The 20–55 pp "partial" window was fixed after the three Qwen results. No written rationale for 20 and 55 exists (AUD:62, :89).
- Seed 1101 chose the setting and counts in the OLMo mean. The fresh-seed mean (1102, 1103) is +45.9 pp (AUD:11, :62).
- The OLMo band is evaluation noise only. Between-seed variance rests on 2 df; the sample SD's 90% range is 0.22–1.73× the true SD (AUD:65).
- U is a broad policy label. After fine-tuning, P(Unsafe | no refusal) is 0.91–0.94, so U mostly tracks lost refusal (AUD:61).
- Under hard categories only, OLMo's E is about 28 pp. HarmBench gives E_HB +27.8 pp for seed 1101 only (partial run). HarmBench κ against Qwen3Guard is 0.65–0.72 (KT:234–239; AUD:52).
- Recipe B is non-standard: per-example mean loss, constant LR, no warmup. Recipe G is the standard-practice comparison.
- Families differ in chat template, tokeniser (so token counts of the same rows differ), post-training pipeline and starting over-refusal (Qwen 1.5B 68%, OLMo 17%, Llama 11%, Qwen 7B 7%).
- The OLMo and Qwen units ran on different engine identities (`55253874…` against `c52c0ebc…`); Llama and OLMo-G on `e49a978c…` (AUD:67; KT:245, :265).
- Qwen and Llama results are one seed each. The ARC bar is uninformative at 1B (AUD:63).
- `[HUMAN-READ]`: a blind human read of about 50 answers.

**Judge-wording rule (copied from the main study, F 13:53 UTC):** a "harm" sentence needs the HarmBench contrast to have the same sign and at least half the size; if E_HB < 20 pp, no sentence says "harm". Until `[HB-QWEN]` exists, Qwen and Llama sentences say "lost refusal", not "harm".

### §7 Related work (wording rules)
Citation status: **opened** = the paper was opened by this chat's paper check on 8 Oct (arXiv abstract plus HTML full text; Qi also in the ICLR PDF). Anything else is `[CITE-CHECK]`.
- **Benign erosion:** Qi et al. 2023 (fine-tuning erosion) `[CITE-CHECK]`; He et al. 2024 `[CITE-CHECK]`.
- **Family contrasts already exist.** Say so plainly:
  - Hawkins et al., arXiv 2606.28843 (opened): one LoRA recipe (α/r = 8, constant LR 5e-5, 1 epoch, 1,000 synthetic Dolly-seeded rows), 3 seeds, SORRY-Bench compliance. English: Gemma-3-1B 30.2 → 65.5%, Llama-3.2-1B 34.5 → 38.4%, Qwen3-0.6B 83.2 → 69.8% (their Table 2; they read the Qwen3 drop as possible collapse). So the same Llama-3.2-1B erodes little in their setup and saturates in ours; data, judge, starting rate and recipe all differ.
  - Khan et al., arXiv 2604.24902 (opened): four 7–9B families, medical and legal data; "Base model family was likewise an unreliable predictor" (§4.2.1).
  - Guo et al., arXiv 2609.01455 (opened; Findings of EMNLP 2026): Llama-3.1-8B and Qwen2.5-7B only, **no OLMo**. On Alpaca, Qwen erodes less (LoRA, 5k rows: 9.1% against 44.8% ASR); on Dolly with full SFT the order flips (73.6% against 66.9%). Wording: "at 7–8B, the Qwen-versus-Llama order in Guo et al. depends on the data".
  - **Do not cite Springer et al. 2602.15799 or Kim et al. 2508.12531 as family evidence** (both opened; neither makes a family claim, and their models differ in size and LR). Kim et al. is a good citation for "optimisation choices (LR, batch, epochs) drive much of the safety loss".
  - Fraser et al. 2506.17209 (opened): Llama-3.2-1B on Dolly with 4-bit LoRA, 5 epochs; the text says instruct but the links point to base checkpoints. Cite with that flag, or not at all.
- **Shallow alignment:** Qi et al. 2406.05946 (opened; ICLR 2025): safety sits in the first tokens. On benign Samsum, a 10-step warmup alone cut ASR 23.4 → 3.8% (Table 9 in the ICLR version, Table 5 in arXiv v1); the authors credit their constrained objective mainly for the attack settings.
- **OLMo-2 priority wording:** "we are not aware of prior benign-fine-tuning erosion numbers for OLMo-2 Instruct". The check opened arXiv 2608.25390 (OLMo-2-1B refusal geometry; its only fine-tuning adds refusals) and 2610.00320 (OLMo-2 7B and 13B on harmful data only); neither has such numbers. One web search found none; that is not exhaustive.
- **Positioning sentence:** "Family contrasts exist; we add OLMo-2, a matched recipe change within a family, and an opening-level account of where the erosion sits."

### §8 Conclusion (3 sentences)
- One recipe can give very different erosion across families at the same size.
- A standard loss and schedule cut the erosion in one family; report the recipe with any erosion number.
- Report erosion per family and recipe, with the judge's definition and every setting screened.

### Appendices
- A: model, data, recipe and engine hashes; config SHA-256s (from KT and AUD).
- B: per-seed tables (OLMo seeds; Granite per unit; capped and screen counts).
- C: judge tables (Qwen3Guard, Granite, HarmBench; hard-category cut; over-refusal-bank Unsafe 5 → 22–29%) (AUD:52–53, :81).
- D: run log and costs (pods, hours, USD).
- E: reproducibility: scripts, frozen lexicon `bbbc71e9…`, bars files.

---

## 9. Placeholders and what fills them

| Tag | What | Cost | Status |
|---|---|---|---|
| `[QWEN-G]` | Recipe G on Qwen2.5-1.5B, seed 1101 (1–3 seeds) | about $3–4 per seed (estimate) | needs the user's go; conflicts with "no more Qwen spend" (F, 7 Oct 20:58 UTC) |
| `[BT]` | OLMo, recipe B + token-mean only, seed 1101 | about $1.5 (KT:261 estimate) | optional; needs the user's go |
| `[HB-QWEN]` | HarmBench judge on the Qwen 1.5B, 7B and Llama units | $0, Mac GPU about 8 h (estimate) | needs the user's go and a slot from the lead (Mac GPU is shared) |
| `[GRANITE-LLAMA]` | Granite on the Llama units | $0 | lead's queue (pending) |
| `[HUMAN-READ]` | Blind read of about 50 answers, rubric fixed first | $0; 1–2 h of the user's time | needs the user |
| `[L1]` | Llama recipe at LR 5e-5 | about $2 | the lead's proposal for the main study; not this chat's |
| `[CITE-CHECK]` | open the remaining cited papers (Qi et al. 2023, He et al. 2024) | $0 | the 8 Oct check opened 2606.28843, 2602.15799, 2508.12531, 2604.24902, 2609.01455, 2406.05946, 2506.17209, 2608.25390, 2610.00320 and the five defence papers |

## 10. Overlap with the main paper (writing/paper/2026-10-08-icml-draft.md)
- The ICML draft does **not** claim the family × recipe result as its own finding. It uses Qwen as context and reports "Gate A with every setting tried" (draft lines 136, 237, 313, 320).
- If this note is posted first, the main paper cites it for the family contrast, the recipe-G-on-OLMo result and the opening analysis, and does not re-claim them (F, FAQ 15:59 UTC).
- **Flag for the lead (not this chat's file):** the draft's abstract and §1 say Llama-3.2-1B "replicates the comparison" (draft lines 151, 161). Recipe B saturated Llama, so that wording now depends on L1 or L2 reading partial.
