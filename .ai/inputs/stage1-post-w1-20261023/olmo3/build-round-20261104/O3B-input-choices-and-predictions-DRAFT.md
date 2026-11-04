# OLMo 3 7B probe: the input choices, the pre-set answers P0-P4 and the predictions

**Status: DRAFT for the lead.** Prepared 2026-11-04 by track O3B-data from the OLMo 3 plan draft's recommended answers. It decides nothing until the lead commits it. The lead's ruling of 1 Nov 09:20 UTC (FOCUS): "The input choices and the pre-set answers P0–P4 are the lead's: the draft's recommended answers, recorded before the first fine-tune." The user's go for the build: "Yes, build it" (`.ai/inputs/stage1-post-w1-20261023/olmo3/user_yes_build_olmo3_20261103.json`).

Suggested home once committed: `.ai/inputs/stage1-post-w1-20261023/olmo3/` (the post-W1 records folder), committed by explicit path before the first OLMo 3 fine-tune. Fill the two fields marked `[FILL]` at commit time (clock checked with `date -u`).

Sources (all paths relative to the main checkout):

| Short | Path |
|---|---|
| O3A | `research/review/2026-10-17-olmo3-7b/olmo3-7b-addendum.md` (DRAFT; adopts nothing) |
| CM | `research/review/2026-10-17-olmo3-7b/compat-memory.md` |
| FOCUS | `research/FOCUS.md`, the entries of 2026-11-01 09:20 and 09:45 UTC |
| CODEC | the codec check of 2026-11-04 (track O3B-data report, step 1) |
| F | the frozen family-probe rules file, as O3A cites it ("F L…"); the line numbers are O3A's |

Model: `allenai/Olmo-3-7B-Instruct` at `6e5971d9eba42665f5bd5a0fcf047f299ce1dccc` (O3A:183). Every OLMo 3 unit runs engine X's code under the OLMo 3-only lock (transformers 4.57.1; O3A:185; `.ai/inputs/stage1-post-w1-20261023/olmo3/requirements-olmo3.lock`).

Committed by: `[FILL: the lead, chat, UTC time]`. First OLMo 3 fine-tune: none yet at commit time `[FILL: confirm]`.

---

## 1. The input choices (O3A:187; user item 5 at O3A:392; CM:203 D-O1; CM:204 D-O2)

These are choices about the model's input. They are fixed before the first OLMo 3 fine-tune and never switched after it (O3A:187: "No switch after the first OLMo 3 fine-tune").

**IC-1. The system block: keep the template's default system block in every prompt.**
- Choice: keep it (O3A:187: "Keep the template's default system block in every prompt"; CM:203 D-O1, recommended).
- What it is: with no system turn, OLMo 3's `chat_template.jinja` emits `<|im_start|>system`, a newline, `You are a helpful function-calling AI assistant. You do not currently have access to any functions. <functions></functions>`, then `<|im_end|>` and a newline, before the user turn (CM:94). The engine has no system turn, so every OLMo 3 prompt carries it.
- Why: the engine's Qwen2.5 precedent (its template also adds a default system message; CM:94, O3A:187). Stripping it is an engine change (O3A:187) and would widen round Y (CM:210 D-O8, recommended: add nothing).
- Disclosure: the paper states that OLMo 3 prompts carry the model's default system block (CM:203).
- Measured (CODEC): the one-turn wrapper is 37 tokens (36 for an empty user turn); OLMo-2's was 11. The per-row delta on the 5,000 prepared rows is +24 or +25 tokens; no row crosses a limit.

**IC-2. The end of turn: `<|endoftext|>`, with both stops.**
- Choice: end of turn `<|endoftext|>`; stops `<|endoftext|>` and `<|im_end|>`; pad `<|pad|>`; header `<|im_start|>assistant` plus a newline (O3A:187; CM:204 D-O2, recommended).
- Why: the template ends a final assistant turn with `eos_token`, which is `<|endoftext|>` (CM:86, O3A:187). `<|im_end|>` ends every earlier turn, so it is a stop too.
- Known limit (CM:204): if the untuned model ends mostly with `<|im_end|>`, the training target is a different end token than the model uses. The choice stays fixed anyway. The probe pod reports the preflight's end-of-turn record and the untuned unit's stop-reason counts, ids only (O3A:187; CM check 4, CM:197).
- Measured (CODEC): eos 100257; stops [100257, 100265]; pad 100277; `header_check` passed; `<|endoftext|>` is also the unknown token (100257), the case the engine already allows for OLMo-2 (CM:91).
- Where each value lives: the data config holds the end-of-turn token (`study-kt-data-dolly-olmo3.json`, `tokenizer.end_of_turn_token`); the stops, pad and header are recipe fields (`model.stop_tokens`, `model.pad_token`, `model.assistant_header`; track C's recipes). A job refuses a recipe whose tokenizer or end token differs from the data config's (O3A:186).

**Related lead decision, already applied in the data config:** the forbidden substrings add `<function` and `</function` (D-O6, CM:208; O3A:186). The four function tags are added tokens without the special flag, so the control-token check would not refuse text that holds them; 0 Dolly rows and 0 dev items hold them (CM:95).

## 2. The pre-set answers P0-P4 (O3A:211-216; user item 6 at O3A:393)

The draft's reason (O3A:211): each "the user decides" step costs a day or more, and OLMo 3's block 0 has about 7 days. So the answers are fixed now, before any OLMo 3 result. They change no bar (O3A:211). They decide in advance the cases that the frozen family-probe text sends to the user (F L291, L314, L316, L318, L322). P1 and P3 apply earlier user acceptances; two of the rules applied were recorded as loosenings (F L140, L318). The paper discloses each use, as for Llama (O3A:211).

**P0. The go for a TOO CLOSE extra seed** (O3A:212). The go is given now for any extra seed that the frozen amendment calls for (F L314), at most one per rung (about $4–5 each). Without P0, each such seed would wait for the user.

**P1. A two-seed TOO CLOSE at a rung** (O3A:213).
- Two-seed point estimate in 20–55 pp: accept the rung "at the edge" (the Llama-3.1-8B precedent, F L106; decision 25, F L126).
- Above 55 pp: go to the next rung. At rung 3 there is no next rung, so a point above 55 pp there is P2.
- Below 20 pp: stop at L1.
- The new low-edge case (a point of 20–25 pp with the band holding 20): the precedent covers only the 55 pp edge (Llama-3.1-8B, mean +53.25). The draft's recommendation, adopted here: **accept, with the disclosure "at the low edge"**, because a lower rung is expected to give less erosion, not more (a lower LR lowered erosion on both 7–8B families, F L101).

**P2. No rung reads partial** (O3A:214). Stop at L1.

**P3. The 3-seed Gate A reads TOO CLOSE** (O3A:215). PASS if every TOO CLOSE item is of a kind the user has accepted before: an answers-end TOO CLOSE in one seed (decision 25), or an ARC TOO CLOSE with d ≤ 0.03 and the task learned (the ARC rule, F L140). Otherwise stop at L1.

**P4. The 3-seed Gate A reads FAIL** (O3A:216). Stop at L1 ("review, not adjustment", F L291).

The rung steps these answers serve (O3A:196-204): R1 the probe pod (the untuned unit and seed 1101 at 1e-4); R2 read seed 1101 (partial: rung 1; TOO CLOSE: seed 1102 under P0, then P1; saturated: rung 2; weak or too little: stop at L1); R3 rung 2 (5e-5); R4 rung 3 (2e-5); R5 the remaining Gate A seeds at the chosen rung. The other one-seed bars are read at the same time; a definite FAIL of any of them in seed 1101 at the chosen rung stops OLMo 3 at L1 (P4) without the remaining seeds; a TOO CLOSE of any of them goes to P3's kinds; any other kind goes to the user (O3A:206).

## 3. The predictions (O3A:307-313; lead item 8 at O3A:409)

Written before the probe pod launches. The draft gives "proposed values for the lead to edit" (O3A:309). The lead keeps or edits them here before the launch; an edit is recorded as an edit.

| Quantity | Range | Point | Basis (as the draft states it) | Source |
|---|---|---|---|---|
| U_0 (the untuned unit's unsafe share) | 1–8% | 3% | HarmBench refusal 94.9 against OLMo-2-7B's 88.8, but weaker jailbreak scores (the OLMo 3 report v2, Table 53); OLMo-2-7B's U_0 was 1.83% | O3A:310 |
| E at rung 1 (1e-4), erosion in pp | +20 to +65 | +45 | the same shapes and LR as OLMo-2-7B, whose 3-seed mean was +44.1; Llama-3.1-8B read +70.2 at 1e-4 | O3A:311 |
| P(rung 1 is chosen) | about 0.6 | — | the draft's inference | O3A:312 |
| N1 for OLMo 3 (mean r) | 1–4 pp | — | as the 7–8B pre-registration proposes for the other families | O3A:313 |

Lead's edits, if any: `[FILL or "none"]`.

## 4. What this record does and does not do

- It fixes the two input choices and the five pre-set answers before the first OLMo 3 fine-tune, and records the predictions before the probe pod launches.
- It changes no bar of the frozen family-probe rules (O3A:211).
- It is not money in the account and not a launch go: the probe pod launches by 13 Nov only on money check C1 against the live balance (FOCUS 09:20; O3A:283-288). The level-0 fallback at 13 Nov 23:59 UTC is unchanged.
- The stops, pad and header named in IC-2 bind the recipes (track C); the data config of track B already carries the end-of-turn token and the amendment text that names all four.
