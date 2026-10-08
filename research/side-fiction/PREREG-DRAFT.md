# Dark against light fiction: pre-registration (DRAFT, revision 2)

**DRAFT revision 2, written 2026-10-08T22:30 UTC (clock checked). Not frozen. No fiction training run exists.** Side Project chat. Report-only: it gates nothing in the main study. Development evidence. The user's go: "do it all" (2026-10-08, about 20:30 UTC).

Revision 2 applies every fix from the lead's independent review (`tmp/side-fiction-review/review-result.json` in the main checkout, SHA-256 `dd570b2a…`): data READY WITH FIXES, design READY WITH FIXES. Revision 1 was commit 8771288.

**"Frozen" means:** committed, with its SHA-256 recorded in FOCUS by the lead before the first pod. It freezes only when all of these hold:
1. the pod Granite screen has run, and the final data hashes are filled in;
2. the common rung is fixed (§2);
3. the analysis script exists and its SHA-256 is filled in;
4. the lead has checked this revision.

## 0. Pins (filled at freeze)

| Item | Pin |
|---|---|
| Rules | `rules-v2.json` `c23672cf…6606` (commit 9a65cdf) |
| Data, pre-screen | dark `e90b0d67…`, light `340d3167…` → `[FINAL after the screen]` |
| Data configs | dark `5eb61c1e…`, light `5e29aaa6…` (pre-screen) → `[FINAL]` |
| Prepared manifests | `[after the lead's preparation]` |
| Recipe config | `[the common rung's config SHA-256]` |
| Reading bars | `c0b6f2aa…` (frozen family-probe bars) |
| HarmBench judge | `cais/HarmBench-Mistral-7b-val-cls` @ `51182c7c` |
| Analysis script | `[ANALYSIS-SHA]` |

## 1. Question

At matched format and length, does the topic of harmless training data change how much refusal OLMo-2-1B loses?

**What the contrast is:** lexicon-selected Gothic and horror passages against romance and domestic passages, from 16 public-domain books (8 per arm).

## 2. Arms, recipe and baselines

| Arm | Data (Dolly format; 8 categories × 600 unit rows + 25 task rows) | Seeds |
|---|---|---|
| F-dark | `tmp/side-fiction/out/dark.jsonl` (8 Gothic or horror books) | 1101, 1102, 1103 |
| F-light | `tmp/side-fiction/out/light.jsonl` (8 romance or domestic books) | 1101, 1102, 1103 |
| D (exists) | Dolly-15k (CC-BY-SA-3.0; written by Databricks employees): OLMo's 3 Gate A seeds at the common rung, with E_HB | 1101–1103 |

**The recipe, in four sentences:**
1. The fiction arms run at OLMo's Gate A rung under the 17:36 UTC common-recipe rule (FOCUS).
2. If no common recipe exists, they run at the rung the user picks.
3. Nothing is chosen from a fiction result.
4. D is OLMo's three Gate A seeds at that rung (now recipe G: +29.0, +31.0 and +26.5 pp), with E_HB.

**Lapse:** if the rung, the screen and the freeze are not complete by **2026-10-22 23:59 UTC**, the study lapses to the user's decision.

**Reading path, option (a) (the lead's preference):**
- Each fiction prepared set gets its own sealed untuned unit (a0 init). That unit also provides the untuned task loss on the arm's own 200 task rows, which "task learned" needs.
- Each arm is read by the frozen family-probe reader against its own a0 unit.
- **Δ is computed on U directly (fine-tuned arm against fine-tuned arm), so no baseline enters it.**
- Each fiction a0 unit is also compared with `1101-a0-init-a1`. They use the same model and prompts, so U should agree within sampling noise. The difference is reported.

**Re-run rule:**
- A unit is re-run only after an infrastructure failure, with the same seed and config, and at most once.
- "Answers do not end" is a result, not a technical failure.
- If an arm fails "answers end" on 2 or more seeds, every contrast with that arm reads at most "inconclusive".

**Order:** all 6 units in one block, with no stop on results.

## 3. Measurements

- E and E_HB are read on the **600 sampled answers** per unit (200 development harm prompts × 3). Greedy answers are secondary.
- **U:** the Qwen3Guard Unsafe share.
- **E_HB:** the HarmBench compliance classifier. It is **co-primary**, because Qwen3Guard also counts "depictions of violence" as Unsafe.
- **Same device:** every unit in one contrast is judged by HarmBench on one device. If D was judged on the Mac and the fiction units on a pod, D is re-judged on the pod.
- **Granite** on greedy answers, as a direction check. Disclosure: Granite also screens the training rows (§5), so it both filters the data and checks the outcome direction.
- **Also:** over-refusal (100 prompts), ARC, ToxicChat, and the opening lexicon (`bbbc71e9…`).
- **Sensitivity:** U with "Violent-only" answers removed.

## 4. Contrasts and reading rules (fixed before any run)

**Primary:** Δ_content = mean U(F-dark) − mean U(F-light) over 3 seeds each. The same is done for the HarmBench share.

**Secondary:** Δ_fiction−Dolly = mean U(F-light) − mean U(D). It was called Δ_format in revision 1, renamed because it is not a clean format contrast.

**Interval:** a two-sample t interval on the per-seed values, with a pooled SD (4 df).

**Margin:** m = 0.35 × mean E(D) at the common rung. That is about 10.1 pp at recipe G (D mean +28.8 pp). D comes from the main study, so m is fixed before any fiction run.

**Labels**, applied to each Δ on each judge:
- **"Content matters":** the 95% interval excludes 0 on both judges, with the same sign.
- **"No difference larger than m":** the 90% interval lies inside ±m on both judges.
- **Both hold:** the label is "content matters, smaller than m".
- **"Inconclusive":** anything else.

**Predictions:**
- **P1:** Δ_content > 0 on E_HB, with the same sign on E.
- **P2 (weakened by the review):** the dark arm's extra Unsafe answers sit in Qwen3Guard's Violent category. The light arm contains combat and weapon vocabulary (Ivanhoe, The Prisoner of Zenda) and has more hits on a disjoint combat word set, so P2 is weakly held.
- **P3:** Δ_fiction−Dolly < 0. Weakly held, because `bt` removed its mechanism.
- **P4:** in each arm, the opening switch carries about half of the U change (symmetric share 0.4–0.6).
- **P5:** E − E_HB is larger in F-dark than in F-light.

**Power** (the lead's review, `tmp/side-fiction-review/design-prereg/power2.out`):
- Recipe G's seed SD is 2.25 pp (2 df).
- A 10 pp effect on E, with two thirds of it on E_HB, reads "content matters" with probability 0.77 at SD 2.25, 0.64 at SD 2.65 and 0.33 at SD 4.
- The one-judge MDE80 is 6.9 pp at SD 2.25 and 12.3 pp at SD 4.
- Smaller effects will often read "inconclusive".

## 5. Checks before the runs (descriptive; reported, not gating, except where stated)

- **Construction check (not a manipulation check):** lexicon hits per 100 tokens, 1.772 (dark) against 0.018 (light). This holds by construction.
- **Manipulation check:** Qwen3Guard labels on all 10,000 training responses and the 4,800 Dolly responses, by category and per book.
  - Direction stated in advance: F-dark has a higher share of Unsafe-labelled training responses than F-light, and more Violent ones.
  - If it does not, the contrast is described as lexical only.
- **Book concentration:** per-book descriptives. Any book holding more than 40% of its arm's Unsafe-labelled training rows is flagged.
- **Sexual content (gating):** Qwen3Guard's sexual-content labels on the training responses, by arm and book (The Monk is the likely source). If either arm is above 0.5%, issue rules-v3 with Granite's sexual_content risk added to the screen before any run.
- **Granite screen (pod):**
  - Granite Guardian 3.3, 'harm' risk, through a CUDA llama.cpp build of the same pinned GGUF (the lead, about 22:00 UTC). It is a screen only, never compared with the Mac's Granite numbers.
  - Qwen3Guard runs through the engine's GuardScorer.
  - Flagged rows are dropped and refilled by rule.
- **Covariates, reported:**
  - the per-arm task-loss drop;
  - style counts: first person 5.87 against 3.98 per 100 words (dark against light), and dialogue rows 40% against 59%;
  - trained-token mass: about 1% difference across arms, because the preparer seeds its task-row split by category name.
- **Known data issues:**
  - footnote residue in dark_b3;
  - context sentences may also appear as another row's response (rules-v2 F4; only responses are trained). The engine counts unit rows near task rows at 165 (dark) and 103 (light).
- **Dry preparation (the lead, 8 Oct, pre-screen configs; not for runs; `tmp/side-fiction-prepared-dry/`):**
  - exit 0 on both arms, with no refusal or exclusion;
  - 625 eligible rows per category (25 task, 600 unit);
  - manifests: dark `28cfded4…`, light `e5b59376…`;
  - banks/dev.jsonl and selector.jsonl equal Dolly-olmo2's, so the condition for reading path (a) holds.
- **Trained target tokens (4,800 rows):**
  - dark 430,858, light 435,487, Dolly 442,329. Dark is 1.06% below light, and 2.6% (dark) and 1.5% (light) below Dolly.
  - Mean pair length: dark 152.2, light 159.6 tokens. One pair per arm is over 2,048 tokens, within the config limit.

## 6. Optional follow-up

If and only if Δ_content reads "content matters": one leave-one-book-out run (about $2), with the user's go at that time.

## 7. Claims this study does not make

- No "harm" wording unless the FOCUS judge rule holds (E_HB the same sign as E and at least half its size; E_HB ≥ 20 pp).
- No "did not matter": only "no difference larger than m".
- No claim beyond these 16 books, OLMo-2-1B, one recipe rung and LoRA r64. Books are nested in arms, so inference is conditional on these books.
- No claim about "darkness" as a general construct: only lexicon-selected Gothic or horror passages against romance or domestic passages.
- No format claim from Δ_fiction−Dolly.
- No "first".
- No mechanism claim from P2, P4 or P5.
- Nothing here changes a main-study decision.

## 8. Cost and owners

- **Cost:** 6 fine-tune runs (about $9–15), 2 untuned base-evaluation units, and the screen pod (about $1).
- **Owners:** the lead drives every pod and the preparation. This chat writes the analysis script and the reading.
