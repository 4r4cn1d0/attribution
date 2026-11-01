# OLMo 3 7B Instruct: verify report on the addendum and the two check notes

**Status: VERIFY ONLY. It adopts nothing.** Written 2026-10-17, about 08:11–08:32 UTC (clock checked with `date -u` at 08:11, 08:16, 08:25, 08:28, 08:29 and 08:31 UTC) by an Opus worker for the main-study lead (GI VI). Read-only work on the repository. No pod, spend, install, commit, or download of weights. Files written: this report; fixes in place in `olmo3-7b-addendum.md` (marked **[V]**, listed in its "Verify changes" section); `calc/verify_recost.py` and `calc/verify_recost_out.txt`. No dataset row, prompt, answer or anchor text was opened or printed.

**Labels.** **R** = read (path:line, or URL with the read date). **M** = measured (a command run in this pass). **E** = estimate. **I** = inference.

**Files checked.** A = `olmo3-7b-addendum.md` (SHA-256 before this pass `56c8eaec8e6a4852…`). MC = `model-check.md` (`7917ac11429cf490…`). CM = `compat-memory.md` (`c2af07cc9c160c28…`). The source short names (KCR, P78, XL, RP, F, CK, SDC, FPR, PRE-F, SS) are A's. Their SHA-256 prefixes match A's (M: `shasum -a 256` in the main checkout).

**Repository state.** The main checkout `/Users/spiderishi/Coding/attribution` was at `0432940` when this pass began. It moved to `f9714b5` (paper revision 6c, committed 08:16 UTC) during the pass. That commit changed only four files under `writing/paper/` (M: `git diff --stat 0432940 f9714b5`). No source of A changed.

---

## 0. Verdict

- **The facts hold.** The model id, revision pins, licence, gating, architecture, tokenizer facts and the safety-training numbers that A uses all agree with a fresh read of the Hugging Face pages and the OLMo 3 report v2 (R, §1).
- **The arithmetic holds.** An independent re-computation in exact decimals reproduces every cost, cap, guard, account need, FRE count, A100-hour figure and option-B total in A to the cent (M, §2). One basis gap (block 0b's scorers) moves L3 to $267–395 if the hour basis is used.
- **Four design defects, fixed in A.** (1) A claimed "no effect on the 20 Nov B/C choice", but OLMo 3's L1–L2 spend before 20 Nov lowers the money at that gate. (2) The frozen amendment needs the user's go for a TOO CLOSE extra seed; A's rung steps skipped it. (3) "Nothing loosened" was too strong: P1 and P3 pre-apply earlier acceptances, two of them recorded loosenings, and P1's 20 pp edge case is new. (4) The rung read ignored the non-E bars, and A listed the E class as a per-seed Gate A bar, which F L294 says is reported, not gated.
- **Twelve smaller corrections**, also fixed in A (§3).
- **Not fixed:** errors in MC and CM (§5). A no longer depends on them.

## 1. Web re-check (all read 17 Oct 2026, about 08:12–08:24 UTC, through WebFetch; hashes came through its summarizer)

| Claim in A / MC / CM | Fresh read | Source | Result |
|---|---|---|---|
| Id `allenai/Olmo-3-7B-Instruct`; main `6e5971d9eba42665f5bd5a0fcf047f299ce1dccc`, 2026-06-25T21:41:37Z | same | https://huggingface.co/api/models/allenai/Olmo-3-7B-Instruct | R, agrees |
| Apache-2.0; not gated, not private; created 2025-11-19T20:49:53Z; parent `-Instruct-DPO`; RL data `Dolci-Instruct-RL-7B`; 7,298,011,136 BF16 values | same | same API | R, agrees |
| Weights commit `d42dc9de51ee481e02b8a35d8222b86c6d7c5b20` (2025-11-20, "Upload checkpoint from step 450"); `51c1f0b2…` (2025-11-26) and `48683dfc…` later | same; 21 commits | https://huggingface.co/api/models/allenai/Olmo-3-7B-Instruct/commits/main | R, agrees |
| Three shard LFS SHA-256 values and sizes equal at main and at `d42dc9de…`; tokenizer and template blobs equal | same `e7bd4c8b…023c`, `ea92aa04…2382328`, `d50f95e4…48925`; sizes 4,969,984,976 / 4,981,161,496 / 4,644,917,240; blob ids of all six tokenizer and template files equal at both revisions | `…/tree/main` and `…/tree/d42dc9de51ee481e02b8a35d8222b86c6d7c5b20` | R (summarizer), agrees with MC's two reads |
| Tokenizer download = 6 files, about 9.7 MB | tokenizer.json 7,137,175; vocab.json 1,611,055; merges.txt 916,646; tokenizer_config.json 4,318; chat_template.jinja 2,613; special_tokens_map.json 581 = 9,672,388 B | tree main; M (sum) | agrees |
| config: 32 layers, hidden 4,096, MLP 11,008, 32/32 heads, vocab 100,278, sliding window 4,096 on 24 layers (3 sliding, 1 full), YaRN (factor 8.0, original 8,192, attention factor 1.2079, beta 32.0/1.0), θ 500,000, 65,536 positions, untied head, eos 100257, pad 100277, transformers 4.57.1 | same | https://huggingface.co/allenai/Olmo-3-7B-Instruct/raw/main/config.json | R, agrees |
| YaRN layers | YaRN applies only to the 8 full-attention layers; sliding layers use plain RoPE | `~/.cache/uv/archive-v0/lQSxF5l04VtSNhpm/transformers/models/olmo3/modular_olmo3.py`:330-345 (transformers 4.57.6, read as code) | R: CM right; MC §4 is silent on layers (§5) |
| tokenizer_config: 22 added tokens 100256–100277; `<functions>`, `</functions>`, `<function_calls>`, `</function_calls>` at 100266–100269, not special; `<|extra_id_0|>` at 100256 and `<|extra_id_1|>`–`<|extra_id_6|>` at 100270–100275, not special; bos = eos = unk = `<|endoftext|>`; pad `<|pad|>`; `GPT2Tokenizer`; no `chat_template` key; no `add_bos_token` key | same | https://huggingface.co/allenai/Olmo-3-7B-Instruct/raw/main/tokenizer_config.json | R, agrees |
| Chat template: no BOS; a default system block when no system turn is given; ChatML markers; a final assistant turn ends with eos, an earlier one with `<|im_end|>`; generation prompt `<|im_start|>assistant\n`; no clock call; no `<think>`; `tool` renders as `environment` | same (control flow only; the text is not pasted) | https://huggingface.co/allenai/Olmo-3-7B-Instruct/raw/main/chat_template.jinja | R, agrees |
| generation_config: eos [100265, 100257]; T 0.6, top-p 0.95; 32,768 new tokens | same | https://huggingface.co/allenai/Olmo-3-7B-Instruct/raw/main/generation_config.json | R, agrees |
| Card: Apache 2.0; research and educational use under Ai2's Responsible Use Guidelines; transformers ≥ 4.57.0; no third-party terms; card Safety row SFT 89.2, DPO 90.2, final 87.3, OLMo 2 7B 93.1 | same; no "third party" or "additional terms" text | https://huggingface.co/allenai/Olmo-3-7B-Instruct | R, agrees |
| Base for Safe LoRA `allenai/Olmo-3-1025-7B` | exists; sha `a81bae42…`; Apache-2.0; not gated; 7,298,011,136 values | https://huggingface.co/api/models/allenai/Olmo-3-1025-7B | R, agrees |
| Report: "Olmo 3", arXiv 2512.13961; v1 15 Dec 2025, v2 14 Apr 2026; 7B and 32B only | same | https://arxiv.org/abs/2512.13961 | R, agrees |
| Safety average by stage, 7B Instruct: SFT 89.5, DPO 89.9, final 87.6; OLMo 2 7B Instruct 91.1 | same (Table 26, p. 55) | https://arxiv.org/pdf/2512.13961v2 (PDF saved by WebFetch to this session's tool-results folder; read pages 45–46, 54–55, 57–60, 115–117) | R, agrees |
| Per benchmark (Table 53, p. 115): HarmBench 87.7 → 94.3 → 94.9 (OLMo 2: 88.8); DAN 90.0 → 82.9 → 75.2 (92.0); WildJailbreak harmful 80.9 → 72.5 → 69.1 (76.8); WildGuard-Test 99.6 (99.2); XSTest 93.2 (93.9); StrongReject 88.1 (89.4) | same | same PDF | R, agrees |
| Safety data: Instruct SFT 110,295 of 2,152,112; DPO 26,671 of 259,922 (Table 30, p. 58); Instruct RL 171,950 prompts with no safety category (Table 20, p. 46); Instruct SFT starts from the Think SFT checkpoint (§5.2.2, p. 57); the SFT mix builds on OLMo 2's (§5.2, p. 54) | same; the sums and shares recomputed (5.1%, 10.3%) | same PDF | R, agrees |
| "RL with long responses" (A §1.1, from MC §7) | RL allowed up to 8K tokens at 7B (§5.4.1, p. 60); but DPO's chat and multi-turn subsets cap the length gap at 100 tokens (§5.3.1, p. 59) and the RL checkpoint was chosen with a length analysis to avoid long outputs (§5.4.1) | same PDF | R: A's wording was one-sided; fixed |

## 2. Arithmetic re-check (M: `calc/verify_recost.py`, written from KCR's text, not from `recost_olmo3.py`; exact decimals; half-up cents)

| Item | A | Re-computed |
|---|---|---|
| upper_M(38); evaluation-only bound; requirement(38) | 10,565 s; 9,643 s; 3.43 h | 10,564.58 s; 9,642.7 s; 3.43 h |
| Probe pod expected / upper / all capped | $4.33 / $5.29 / $10.95 | same |
| Fine-tune pod expected / upper / all capped | $3.62 / $4.45 / $6.16 | same (KCR §8: $3.62, $4.45) |
| Per arm at 3 and 4 per pod | $3.01–3.62; $2.94–3.52; all capped $5.48 (×1.86) | same |
| Caps: probe 7.00 h; 1 arm 4.25; 2 arms 6.50; N 8.50; 4 arms 10.50 | same | same (KCR §7) |
| Account needs: $102.86; $97.77; $101.94; $105.64; $109.34; $113.04; $141.71; $144.49; $136.16 | same | same |
| Gate A paths G0–G3 (with judges) | $6.19–9.35; $15.88–23.04; $20.22–33.73; $24.56–44.42 | same; hours 2.4–3.0, 6.5–7.9, 8.5–12.9, 10.5–17.9 |
| N | $10.85–13.04 with +20%; 5.1–6.1 h | same |
| Combined layout | $15.37 against $16.28 | same |
| Beyond Gate A and N | 65.2–73.2 FRE; $238.91–332.10 | same |
| L1 / L2 / L3 / B9 / H(b) / L4 | $15.88–44.42 / $26.73–57.46 / $265.64–389.55 / $300.90–431.78 / $357.33–499.34 / $329.12–490.90 | same |
| Option B + L3; new money; F1; F2 | $1,450–2,150; $1,360–2,050; $177–207; $1,139–1,632 | $1,445.64–2,149.55; $1,355.64–2,049.55; $176.73–207.46; $1,138.91–1,632.10 |
| A100-hours L3; share of RP's 290–420 | 119–170; "about 30–60%" | 119.3–170.2; 28–59% |
| Parameter and LoRA counts | 7,298,011,136; 159,907,840 | same (and 7,298,617,344 for OLMo-2's 100,352 rows) |
| Seed counts: plan A 44 (45 with a0 1107); D1 44; B9 +10; H(b) +26 | same | 36 + 5 + 3 = 44; D1 36 + 4 + 4 = 44; P78 §5.4: 54 − 44, 70 − 44 |
| Scorer FRE 5–9 "backed out of RP's 65–72" | 5–9 | OLMo: 65–72 − (36 + 8 + 3 + 3–6 + 10.2) = 4.8–8.8; Llama: 69–76 − (36 + 8 + 4 + 3 + 3–6 + 10.2) = 4.8–8.8 (I) |

**Gaps found.**
- **Scorer basis (minor).** The scorer row uses 5–9 FRE ($17.63–38.00); the A100-hour line uses 9–20 h, which at $1.79 × 1.2 is $19.33–42.96. On the hour basis L3 is $267–395. Added to A §1.4 and §0.
- **Probe-pod cap reason (minor).** A said KCR has no evaluation-only basis and invoked KD6. KCR §4 "Job kinds" covers `evalonly` (upper_M without training); KD6 covers A1, anchors, scorer passes, c0 and B+Qi. The 7.00 h result stands because A used the all-capped evaluation bound (9,643 s) as that job's measured upper. With KCR's arm value (7,418 s) the cap is 6.50 h. Fixed in A §1.2.
- **G1 layout (note).** One 2-arm pod for seeds 1102–1103 gives G1 $14.79–21.54. Added as a note.
- **LA-04's basis (resolved).** SDC's "$17–33" is 5 arms (a0 1102–1103 and R_1–R_3) at RP's rates (R: `research/experiments/2026-10-17-stage1-review-b-rulings/verify-report.md`:75). A's G1 fine-tune pods plus N give $20–24 with the allowance, inside that range.

## 3. Consistency with T4, the frozen rules, FOCUS and the re-plan

| # | Finding | Severity | Evidence | Fix in A |
|---|---|---|---|---|
| 1 | "OLMo 3 never changes … the 20 Nov B/C choice" is false. OLMo 3's L1–L2 ($27–57) is spent before 20 Nov on a B-only item, and the B/C gate reads the money in the account. C1–C2 cover only needs up to each item's *next* gate, and B's F2 need ($900–1,300) comes later. So OLMo 3 can take money that B needed, against the cut order, in a narrow band (about 2–6% of B's F2 need). It also departs from RP's "fund now only what B and C share" | major | R: RP §0, §5, §7 item 2; A §16.7 C1–C2 | §16.7 split into a statistics line and a money line; [USER] 11: accept and disclose, or add "B's F2 low end ($900) plus OLMo 3's next step is in the account or awarded in writing" to C1–C2 (recommended) |
| 2 | The frozen amendment says a TOO CLOSE extra seed runs "after the user's go". A's R2 ran it with no go | major | R: F L314 | P0 added to §16.2a; R2 notes it; [USER] 6 |
| 3 | "Gate A … with nothing loosened" overstated. P1 and P3 decide in advance the cases that the frozen text sends to the user (F L291, L314, L316, L318, L322). P3 applies the ARC rule (a recorded loosening, F L140) and the answers-end precedent (decision 25; F L120, L126); the short-answer rule was itself a mild loosening (F L318). P1's precedent (Llama-3.1-8B, F L106) is a 55 pp edge; a two-seed TOO CLOSE at the 20 pp edge is a new kind. P1 at rung 3 with a point above 55 pp had no next rung | major | R: as cited | §0, §16.2a, §16.3 reworded; P1's low-edge case flagged for the user; rung 3 goes to P2 |
| 4 | The rung read branched on the E class only. The frozen bars say a probe qualifies only if every bar passes (F L322, L352), and every seed must pass its per-seed bars in the 3-seed rule (F L290). A also listed the E class under "per seed" bars, but per-seed E classes are reported, not gated, in the 3-seed reading (F L294) | major | R: as cited | §16.2 rule for the non-E bars (a definite FAIL in seed 1101 at the chosen rung stops at L1; a TOO CLOSE goes to P3 or the user); §16.3 note |
| 5 | Calendar trigger "blind to every outcome": a saturated rung delays the Gate A read, so the trigger can depend on the erosion probes (allowed by F L163, but not "blind") | minor | I from A §16.2, §16.7 | reworded |
| 6 | Control tokens are a *reported* item under the frozen bars (F L351). With family None, FPR prints none (FPR:432). FPR's role-marker count would fail for family None but is only called inside the family branch (FPR:400-401, 432-435), so the run does not crash | minor | R: FPR:81-86, 301-306, 395-401, 432 | §16.1: a separate ids-only count in a new file |
| 7 | The 3-seed tool `gate_a_common.py` (`7faf2164…`, F L121) is not pinned by Gate B (M: no match in `scripts/gate_b_reading.py` or `runkit/gate-b-olmo/*.py`), but editing it changes a recorded file | minor | M: grep | §16.1: add the plan key in a copy |
| 8 | P78 §7: an unnamed "transfers at 7–8B" claim needs TRANSFERS in every family that ran, so an OLMo 3 TC run would bind the staying families' claim | minor | R: P78 §7 "Claims" | §16.6 note; [USER] 12 |
| 9 | New scripts (preflight, writer, counts, tool copy): an uncommitted file under `scripts/` or `experiments/` blocks every Gate B pack | minor | R: `runkit/gate-b-olmo/pack_setup.py`:195-199, 220-222 | §16.8 line |
| 10 | RP's "never cut: the a0 and R arms" is narrowed to "of the families that stay" without saying so | minor | R: RP §6 | §3.3 note |
| 11 | Option-C reason: C can be chosen for the noise reading too (RP decision 2), not only by a money cut | minor | R: RP §7 item 2 | §16.0 restated |
| 12 | Paper: revision 6c (`f9714b5`) now lists the item as AWAITING and says what to remove if the user declines | info | R: `main.tex`:614-615, 3249-3262 at `f9714b5` | header and §3.4 |

**Checked with no defect found.**
- **T4** (BRIEF:65 at `.ai/briefs/stage1-commitments-build-20261016.md`): A changes no engine file (the identity is the 22 top-level `SS/*.py` files plus 7 minimal-safety modules = 29; R: `SS/common.py`:25-36; M: `ls`), no Gate B pinned script, no kit file and no sealed file. PRE-F and FPR stay unedited (PRE-F ships in the Gate B bundle; FPR is loaded by `scripts/gate_b_reading.py`:252). The lock stays outside `experiments/` (the pack bundles every `.lock` there, `pack_setup.py`:220-222). Working copies `tmp/family-probe-s78-olmo3-7b-*` match P78 EM-2.
- **Code facts:** FPR maps only `allenai/OLMo-2-` and `meta-llama/Llama-3` (FPR:86), so `allenai/Olmo-3-…` gives family None; PRE-F's `comparison_rows` returns "none" when rows equal the tokenizer length and no reserved tokens exist (PRE-F:94-104), and `use_this_recipe` needs every part True (PRE-F:229-243); `SS/edits.py`:116-117 refuses another manifest; `SS/jobs.py`:241-244 refuses a tokenizer mismatch; `SS/textproc.py`:68-77 renders one user turn; no engine or script file touches `rotary_emb` or `model.layers` (M: grep), so OLMo 3's per-layer-type rotary tables do not meet engine code.
- **Frozen bars and rules:** E classes, answers end, coherent-only, unscored, ARC, task loss, Granite (F L311-352); the 3-seed SE² and 2 × SD rules and the verdict order (F L283-296); the per-family rule (F L163).
- **User decisions in FOCUS:** UW-01's ambitious-default rule, UW-03's D1 layout and UW-13's scaled SESOI (F L74) are quoted correctly; the $10/h limit, D5 = (a), recipe B and engine X stay; the Gate B hold ($83.91) is kept at every launch (EM-2). FOCUS has no OLMo 3 entry (M: grep), so "pending" is right.
- **Re-plan:** the cut list and its dollar values (RP §6), the schedule (RP §5) and the totals are quoted correctly; the 1 Dec 32B go rule (XL §9) is read correctly.
- **P78:** plan A runs (44), block A (21), B9 and H(b) increments, the three-family pool form (6 df), EM-1 to EM-4, and the §10 deadlines.

## 4. Replies to the brief's checks

- **Id:** right (`allenai/Olmo-3-7B-Instruct`, pin `6e5971d9…`, weights equal to `d42dc9de…`). R.
- **Licence:** Apache-2.0, not gated, no third-party terms on the card. R.
- **Alignment claims:** right. Safety data in SFT and DPO only; none in RL; the safety average falls from 89.9 (DPO) to 87.6 (final) in the report's table (the card shows v1-like 90.2 → 87.3). R.
- **Architecture:** right; YaRN on 8 of 32 layers. R.
- **Cost arithmetic:** reproduced to the cent from KCR's measured times. M.
- **T4, frozen rules, FOCUS decisions, re-plan:** consistent after the fixes of §3.

## 5. Errors in the two check notes (reported; not fixed, as the brief asks only for fixes to A)

**MC (`model-check.md`).**
1. §4 RoPE row: "static frequencies, applied at every length" does not say that YaRN applies only to the 8 full-attention layers (R: transformers 4.57.6 `modular_olmo3.py`:330-345). No effect on cost or memory.
2. §5 and §6.3 item 1: the default system block is put at about +15 tokens per prompt over OLMo-2. CM's proxy count gives +23 or +24 (M: `calc/limit_margin_out.txt`). A uses CM's value.
3. §0, §7 and §9 D1: "about $8–10 for Gate A" counts two seeds. Gate A needs three ($15.88–23.04 at rung 1 with the allowance and judges). A says so.
4. §6.2 B3 names six unused `<|extra_id_N|>` rows (100270–100275). There are seven: `<|extra_id_0|>` at 100256 is also unused and not special (R: tokenizer_config). CM is right.
5. §7 "RL ran with 8K-token responses": the 8K figure is the maximum response length; the RL checkpoint was chosen with a length analysis to avoid long outputs (R: report §5.4.1). One-sided, as in A (fixed there).
6. Header: "about 07:15–07:50 UTC", but the file was last saved at 07:46 UTC (M: `stat`). Small.
Everything else in MC that A uses was confirmed (§1).

**CM (`compat-memory.md`).**
1. §2.4 "longest training row 2,114 + 24 = about 2,138": its own proxy output gives 2,128 (OLMo-2) and 2,152 (OLMo 3 proxy) for the longest row within limits (M: `calc/limit_margin_out.txt`). The basis differs (the manifest's audit against all 15,011 source rows). At 2,152 the training peak rises by about 0.3 GB (E: 2 × 14 tokens × 10.39 MB), so the verdict (mb2 fits, about 75–76% reserved) stands.
2. §0 item 4 and §2.6: it calls the missing `chat_template.jinja` a "silent-gap risk" and then says it fails loudly; only the manifest record is silent. Wording only.
Everything else in CM that A uses was confirmed: no `olmo3` code in 4.56.2; the class in 4.57.6; YaRN layers; the token proxy; the memory model; the codec values.

## 6. Acceptance criteria

| Criterion (from the brief) | Result |
|---|---|
| Re-open the Hugging Face pages; re-check id, licence, alignment claims, architecture | **Passed** (§1); hashes still through a summarizer (not a byte pin) |
| Re-do the cost arithmetic from the measured times | **Passed** (§2); one basis gap noted |
| Consistency with T4 and the frozen rules | **Passed after fixes** (§3 items 2–9) |
| Consistency with the user's decisions in FOCUS | **Passed after fixes** (§3 items 1, 3) |
| Consistency with the re-plan | **Passed after fixes** (§3 items 1, 10, 11) |
| Write `verify-report.md`; fix A in place; add "Verify changes" | **Done** |
| Write files only under the olmo3-7b folder; no repo edit, commit, pod, spend, weights download | **Passed.** WebFetch saved the report PDF (a public paper, 6.5 MB) to this session's tool-results folder outside the repository; no other file was written outside the folder |
| No dataset rows, prompts, answers or anchor text printed | **Passed** |

## 7. Commands actually run (exit 0 unless noted)

- `date -u` (08:11, 08:16, 08:25, 08:28, 08:29 and 08:31 UTC).
- `ls`, `stat`, `shasum -a 256`, `wc -l`, `grep`, `sed -n`, `cat` on this folder and the main checkout (read only).
- `git rev-parse HEAD`, `git branch --show-current`, `git log --oneline`, `git status --short`, `git show <rev>:writing/paper/icml/main.tex`, `git diff --stat 0432940 f9714b5` in the main checkout (read only).
- `python3 -I -B calc/verify_recost.py > calc/verify_recost_out.txt` (exit 0).
- WebFetch (17 Oct 2026): the model API; its commits; its tree at main and at `d42dc9de…`; raw `config.json`, `tokenizer_config.json`, `chat_template.jinja`, `generation_config.json`; the model card (twice); the base model API; the arXiv abstract page; the v2 PDF (read with the Read tool, pages 45–46, 54–55, 57–60, 115–117).

## 8. Unresolved concerns

1. **The shard SHA-256 values are still summarizer reads** (two independent reads agree). The lead's direct Hub API read before the pin stays necessary.
2. **The B/C money effect** (§3 item 1) needs the user's choice; the recommended condition may defer OLMo 3's Gate A past 20 Nov if no award arrives, which pushes OLMo 3 block B toward mid-December (A §5 alternative 1).
3. **P1's 20 pp edge case** has no precedent and needs the user's explicit word.
4. **Answer length** stays unknown in both directions; the all-capped sensitivity (×1.86 per arm) is the bound.
5. **transformers 4.57.x with peft 0.17.1 and engine X** is unverified until the Mac venv check and the first pod.
6. **4 arms per pod at 7–8B** is confirmed by the user for Gate B only (KCR KD2); A's block costs assume it.
