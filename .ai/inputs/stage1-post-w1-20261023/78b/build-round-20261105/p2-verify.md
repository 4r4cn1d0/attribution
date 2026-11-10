# Track P2 verify (round 4, 7-8B tier): adversarial check of Part 2

Started 2026-11-06 15:26 UTC; this version written 15:48 UTC (`date -u` read before each time). Status: DONE.
Verdict: **DEFECTS** (1 major, 9 minor, 3 nits). No blocker.

- Target (read-only): `ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md`, SHA-256
  `1692caae93f07e14bddb6b0b20c99bbc0ca3c83b0181f1f7f0da0584c636a459`, 427 lines. It is unchanged from start to end (M: `shasum`, `wc`).
- HEAD of the main checkout, ws-p and ws-m: `d2030706d93c741713f027ddfd28150e6f205e4f` (M: `git rev-parse`).
- Scratch: `reports/p2-verify-scratch/` (`tables.py`, `findhash.py`, `wsm-scale78b.sha`).
- Tags: M measured (command in section 6), R read (path:line), E estimate, I inference.
- No git state changed. No pod, spend, network, install, download, agent or message.
- No answer, prompt-text, judge, selector, `hidden/` or secret file was opened. I did not hash the six text files in `tmp/`. I matched their hashes against the text-free records instead.

## 1. Files changed

- Only this report and the scratch files above. No file changed in the repository, ws-p or ws-m. M: `git status --short`: ws-p still shows only `?? …part2.md`; ws-m still shows 30 entries.

## 2. What holds (evidence)

1. **Hashes (M).** `tables.py` re-hashed all 85 rows of §1.17 tables A-D: 85 OK, 0 bad.
   - Table A was hashed in ws-m.
   - Tables B, C and D were hashed with `git show HEAD:<path> | sha256`.
   - Table A (43 rows plus the 5 test files in the prose) equals track M's `after.sha`, paths included (M: `diff`, SAME).
   - Engine X identity in clean ws-p = `472fc7f6…` (M: `code_identity()`).
   - The MAIN_F files hash to `e9e98e84…` and `3d437bd6…`. Their config_sha256 values are `18cc31d7…` and `74758af1…`, and their training identities are `36738c38…` and `5b4451e1…`. Model revisions and token limits match: 3072 / 1536 / 2048 / batch 32 (M: the engine's `load_recipe`, `config_sha256`, `training_identity`).
   - These hash at HEAD as Part 2 says (M): `R_d1.json` `f7d7eb86…` (SEAL) and `5cdedf22…` (Llama); Llama S1 settings `36a39481…` and record `1023b4e6…`.
   - The 6 text-file hashes of table D's last row appear under the right keys (R, `findhash.py`) in PINS, `s_pool_record.json`, `add_edit_record.json`, the Llama S1 MANIFEST and `anchor_prompts.sealed.json`.
   - The S1 verdict record files hash to `9b340bf5…` (M: track M's and its verifier's copies). Committed evidence of the value is in BR's `fix-F.md` (R).
   - All governing-text hashes in Short names match (M): P1, ERR, RUL, ADD `ff349876…`, PP, PLAN, CHECK, P78, KCR, PR4.
   - Every one of the 66 truncated prefixes resolves to the file the text names. The one exception is defect N1.
2. **MAKER --check** in ws-m: 19 of 19 files equal their regeneration, exit 0 (M).
3. **E caps (§1.15).** All 10 kinds × 2 families equal `rules_78b.e_pod` at HEAD in cap, guard and spend (M). The basis texts match RK:862-913 (R). The guard formula ($6 + $1.85 × cap) and the spend formula ((48 min + upper) × $1.79) are RK:361-363 and :806-808 (R).
4. **Rules against sources (R unless marked).**
   - A1 matches `write_score_edit.py:12-19, :93` and the 1B settings `a1` (`row_field` cosine, the Adam variant excluded, the 1e-12 consistency check, k 600, `a1.ties`, `category_flag_rule`). Six null `a1.attributes_unit` pins (M).
   - The anchor job matches `make_anchor_answers.py:1-17, :31, :117-121`. MAIN_F's `query_bank` is "ref" (M), as `:109` requires.
   - S_78 matches `make_recipe_s78.py:1-19`.
   - L1 matches `score_l1_larf.py:1-23` and the derived settings: `first_block` 10; modules olmo2 = post_attention/post_feedforward norms, llama = self_attn and mlp; the representation-pass settings pin `492a1906…` / `d11187be…` (M).
   - The representation pass matches `representation_pass.py:1-25`.
   - S3 matches `score_s3_datarx.py:1-21` and `write_score_add.py:1-12` (whose settings pin no family value, M).
   - The classifier matches `score_classifier.py:1-17`.
   - The untuned pass matches `make_untuned_answers.py:1-35, :82-93, :157-178, :171, :290-318`. Its derived settings say: s3 at 512 tokens; s4 keep 192, size 512; REC and S both MAIN_F (M).
   - The doses match `scorers_78b.py:345-421` ("the smaller doses that are filled are written" holds at :355).
   - S-pool counts in the record: 48 / 861 / 855 (d1.k against planned 1,000) / 512; limits 3072 / 1536 (M).
   - H1 matches README:14-29. The Llama S1 MANIFEST fields match.
   - O-ext and c0 pins: `oext_unit.json:52-66` and `lean_eval_job.json:38-39`.
   - The O-ext sentence quoted from the 7-8B runner is at line 45.
   - Kit references: RK:141 `S78_KINDS`; :329 `KIND_LABELS` c0; :424-434. No `X_ONLY_KINDS` in RK; `stage1_rules.py:234` holds `()`; `plan_tool.py:729` (M: grep).
   - No kit file pins a scale78b hash at HEAD (M: 0 of 48 prefixes found under `runkit/stage1-78b/`).
   - `s1common.py:590-592` is the engine check (590 identity, 591 if, 592 raise), so PP4's 589-591 is off by one, as §14 item 13 says.
   - The registry keys `a1.ties`, `l1.ties`, `l1.scan`, `s3.ties`, `length.order` and `classifier.ties` exist in `labels.json` (M).
   - PR4:228 defines P2 = U(R) − U(L1). PR4:177 is the golden-test sentence. PR4:812-815 covers c0.
   - FOCUS (HEAD) lines 67 and 74 hold the quoted phrases (84 / 465 tokens; $20.21, "No pod, no spend").
   - RP:43 (6-11 h, ×2.3); KCR:70, :161.
   - The MFIX section numbers match `reports/m-fix.md`.
5. **Coverage.**
   - P1 §14 items 1-13 each map to a Part 2 section: §1 = items 1-2; §0 = 13; §2 = 1, 12; §3 = 4; §4 = 3; §5 = 5; §6 = 6; §7 = 7; §8 = 8; §9 = 9; §10 = 10; §11 = 11; §12 = 12.
   - PP1-PP5, PP8, PP11, PP12, PP15 and PP16 are carried. PP6, PP9, PP10, PP13 and PP14 are not scorer rules.
   - Ruling 10, ruling 11, A1, A2 and A13 are carried. A8 is carried only in part (N7).
   - The status sentence is present. §1.18's labels match PP11's and PP12's own labels and ruling 16 / A16.

## 3. Defects

| id | sev | where | what (evidence) | fix |
|---|---|---|---|---|
| D1 | **major** | §1.15 row `untuned_answers (both calls)`; §1.11 "The pod's E cap covers both calls (§1.15)" | RK at HEAD counts the S4 call only. M: `e_upper_s` = 6,085 s (OLMo) and 6,281 s (Llama), which equals 1.5 × (first + 15 batches + ends), the S4 call alone. Adding the S3 call (861 prompts = 27 chunks, still at the capped-batch maximum) gives 16,146 / 16,692 s, cap 6.0 h, guard $17.10. RK's own basis (:864) says "512 prompts in 16 chunks". verify-E C3 raised this. Track K4b (ws-k2, this round) found the same and sets 6.0 h (R: reports/k4b.md:39-44, :143-146). Part 2 states a coverage the source does not give and lists no open item for it. The freeze would carry a 3.0 / 3.25 h cap labelled as covering both calls. | Delete "(both calls)" and "covers both calls", or say: "at HEAD the cap counts the S4 call only (verify-E C3); the kit's round-4 change sets 6.0 h". Add a §14 item. Re-take §1.15 from RK after K4a/K4b merge. |
| D2 | minor | §14 item 6, "A failing prompt would leave the S3 ranking or fail S4's keep rule" | The unchanged 1B pass encodes every list prompt before generating (`make_untuned_answers.py:156`). A prompt that `encode_generation_prompt` refuses raises `s1.Refusal` for the whole call (:103-113). So one over-limit prompt under a 7-8B codec refuses the pod job; it is not a dropped row. In `rep_pass`, a pool row that `encode_train` refuses is counted, not fatal (`representation_pass.py:337-345`). | Replace the sentence with the measured behaviour. The $0 encode count then becomes a precondition of the untuned pod, not just a check. |
| D3 | minor | §1.0 "the SHA-256 of every script … used"; §1.17 table B | `scripts/stage1/token_accounting.py` is imported by `write_add_edit.py:37` (the S3, S4 and dose add edits) and by `build_length_rules.py:38` (H1). It is not in table B. M: HEAD `b9a51f6fc66fb3011c7448d0869f65848d407fa4d901ba10216312e0a93a6024`, equal to the Llama S1 MANIFEST's `frozen_code`. Table B's heading "each equals WRAP's STAGE1_CODE" holds for 9 of 17 rows. Its title "The 1B scripts the wrapper runs" includes 8 scripts the wrapper does not run. | Add the row. Reword: "the nine in STAGE1_CODE equal it (WRAP:79-89); the others are run directly or imported". |
| D4 | minor | §1.2, §1.9, §1.19, §14 items 4, 10, 12, 13; line 263 | The short name MFIX is used 8 times and is never defined (not in Part 2, not in P1). Its file (track M's `m-fix.md`) and "track M's `after.sha`" are in the session scratchpad. They are not in BR or the repository, so the cites do not resolve from the committed tree. | Define MFIX as BR's copy of track M's round-4 report once the lead commits it, and cite `after.sha` the same way. |
| D5 | minor | §1.5, "If at least 50% of the selected rows are one category, A1 is also compared with that category's Gate B unit arm" | This is the 1B settings' `category_flag_rule`, restated as part of the 7-8B contract. No 7-8B unit arm exists or is planned (R: P1 has no unit arm; the rulings name none). As written, it is an executable rule that would need new runs. | State it as the writer's recorded flag only, and add a §14 item (report-only, a unit arm, or not read at 7-8B). |
| D6 | minor | §1.4, §1.5 (retrain) | A8 says "two under [B], F1's only under [C]" (also P1 §3.2, §3.7). Part 2 drops the [C] qualifier for the retrain pod. It also does not say which families' anchor job and scorer pods run under [C]. | Carry A8's words. List the scorer-pod question under [C] in §14. |
| D7 | minor | §1.4 item 4 (c0); §1.13 cite | The 1B c0 form passes `--expect-adapter-fingerprint <R_1101's e1 fingerprint, from its pinned COMPLETE.json>` (R: `runkit/stage1-olmo/setup/job_runner_stage1.py:43-45`). So c0 waits for N's R_1-1101 unit, and §1.4 gives c0 no input. Part 2's cite `:45-47` (copied from SC) points at the tail of c0 and the retrain kind. K4b adds a null pin C0_SOURCE for this (R: k4b.md:156). | Add "c0 after N's R_1 at 1101". Cite :43-45. |
| D8 | minor (PLAUSIBLE) | §1.5, §1.16 | Ruling 10 has three branches: Y equal; Y differs and X equal; X differs. Part 2 says "the engine that ran them (X, or Y after the certificate)". It does not say whose states A1 takes when Y differs (the X retrain's, I), or what happens when X also differs (ruling 7's fallback; A1's states then come from the re-run environment, not ruled). | Add a §14 item. Do not settle it in Part 2. |
| D9 | minor (PLAUSIBLE) | §1.8 "No per-family S-pool is built … and it does not say so"; §1.18 item 10 | PINS `sealed_lists_1b.note` leaves "rebuilt per family" to Part 2. Part 2 settles it by reading P1 §14 item 1, whose words "the same 48 S-pool rows" name S1. For S4, ruling 12 and P1 §10 fix the sealed 512-prompt list (`stage1-s4-v1`), so reuse is ruled there. For the S3 lists (s3_safe 861, s3_subset 855), no ruling text says "reuse". This is a worker's reading presented as settled. | Cite ruling 12 for S4. Mark S3's reuse as "a reading of P1 §14 item 1; the lead confirms" in §14 (with item 6's encode count). |
| D10 | minor | §1.11 keep rule, "the first failing check is the drop reason" | The code's order is capped → empty → not_refusal_opening → encode_train (R: `make_untuned_answers.py:141-151`). Part 2 lists ended → REFUSAL-OPENING → non-empty → encode_train. An empty answer is dropped as "empty", not as "not_refusal_opening". | Reorder to the code's order, or drop the "first failing check" clause. |
| N1 | nit | §1.5 "Gate B's wave-0b attributes unit (`5c0e53b7…`)" | `5c0e53b7…` is the 1B A1 edit file `a1_remove600.edit.json` (R: PR4:96, :126). The unit's COMPLETE.json is `1e5e23f7…` (R: 1B settings `a1.attributes_unit.complete_sha256`). | Attach the hash to "the sealed 600-row set". |
| N2 | nit | §1.11 "`test_s4_doses_78b.py`, 10 tests" | M: `pytest --collect-only` finds 13 tests (9 functions, one with 5 parameters). | Say 13 (copied from SC §3; SC is track M's file). |
| N3 | nit | §13 row 3; §14 item 8; §1.8; §1.10 / §1.18 | Row 3 quotes P1 as "…re-bound" (P1: "re-bound to the family manifest; CHECK C6"). Its "Why" is PP5 only, which covers S1, not the S-pool lists. §14 item 8's quote drops PR4:731's "no runs;". The sealed-order names `stage1-s1-v1` and `stage1-s4-v1` are in `labels.json`, not in the s-pool record that §1.8 cites. One function is cited as `:82-93` (§1.10) and as `:84-93` (§1.18). P1 §14 item 2's "the dose edits' hashes" moves to §2 with no change-log row. | Fix the quotes and cites; add the change-log row. |

## 4. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Only the new Part 2 file in ws-p | passed | M: `git status --short` |
| Every cited hash re-measured and correct | passed (98 of 98 full hashes; 66 prefixes; N1 mislabels one) | M: `tables.py` 85/85; inline and record checks |
| SHA-256 of every script and settings file used | **failed** | D3 (`token_accounting.py` missing) |
| A1 per family | passed, with D5, D6, D8, N1 | section 2 item 4 |
| L1 (PP11, PP12; scan and score) | passed | R and M, section 2 |
| H1 by manifest | passed | M hashes; README:14-29 |
| S1 (PP5), S-pool, S3, S4, doses | passed, with D2, D9, D10, N2 | section 2 |
| Classifier, c0, untuned O and L (M1) | passed, with D7 | section 2 |
| Engine X (PP4, PP16) | passed | R: PP; M: grep at HEAD |
| E caps (PP8, PP15) | **failed** | D1 (the numbers are right; the coverage claim is wrong) |
| Labels after the stage-1 reading | passed | §1.18 matches PP11, PP12 and ruling 16 / A16 |
| No new decision, none dropped | passed with exceptions | D9 (a reading settled), D5 (a rule carried with no arm), D6 (A8's [C] qualifier dropped) |
| Citations read | passed with exceptions | D4, D7, N3 |
| Status sentence; other sections marked | passed | lines 3, 28, 352-392 |
| Committed and frozen | not tested | the lead's step |
| Tests of scale78b re-run | not tested by me | R: m-verify.md:25-31 re-ran them: 246 passed and 2 skipped; 74 passed |

## 5. Jobs for the lead

1. **Fix D1 before the commit.** Either way, re-take §1.15 and table D's RK hash after K4a/K4b merge. K4a builds PP16's `X_ONLY_KINDS`, so §1.3's "state at HEAD" and §14 item 2 go stale. K4b sets the untuned cap to 6.0 h and adds the null pins OEXT_78B and C0_SOURCE, so §1.13, §1.14 and §14 item 1 change.
2. Track M's verifier left D1-D4 (reports/m-verify.md:73-81). A fix to `s1_olmo2_7b_check.py` (its D1) or to the pins text (its D4) changes table A rows: `s1_olmo2_7b_check.py`, its test, `pins_78b.json`, `PINS-78B.json`, both `score_classifier__F.json`, `scorers_78b.py` and `SCORERS-78B.md`. Re-hash table A after the merge and before the commit.
3. Apply D2-D10 and N1-N3 (text only; one Part 2 fixer pass, then a re-verify).
4. Copy round 4's reports (m-fix.md, its `after.sha`, p2.md, this report) into BR before Part 2 cites them (D4).
5. Two-step commit. Record the scorer-section commit's SHA-256 in FOCUS at the first commit. At the freeze, show that §1 is unchanged since then (for example `git diff <first>..<freeze> -- <part2>` restricted to §1). `scripts/stage1/commitments.py check` covers `scripts/stage1/**`, `scripts/stage1_s1/**` and the sealed records only (R: its module doc), not Part 2's text.
6. Optional: delete `reports/p2-verify-scratch/` after the merge (3 small files).

## 6. Commands (all foreground, each under 1 min; exit status)

1. `date -u`; `ls`; `mkdir -p` the scratch; `wc -l` and `shasum` of Part 2; `git rev-parse HEAD` ×3; `git status --short` (0).
2. Reads (Read, `cat -n`, `awk`, `sed -n`, `grep`) of PP, RUL, ADD, ERR, P1 §0-§3, §10-§15, PLAN T4/T6, CHECK C1/C6/M1/M2/M4, P78:328-382 and :405-416, p2.md, m-fix.md, m-verify.md, k4b.md (sections), SC, PINS, WRAP, MAKER, RK, the 1B docstrings and settings, the O-ext and lean settings, the runners, PR4 sections, FOCUS lines 67 and 74 at HEAD, READMEs, MANIFESTs and records (keys and hashes only) (0). Two failures: one `cat -A` (BSD cat has no -A, 1) and one `grep`/`sed` with a relative path from the wrong folder (1). Both were re-run correctly (0).
3. `find scripts/scale78b -type f | xargs shasum -a 256 > SCR/wsm-scale78b.sha` (0); `diff` against track M's `after.sha` → SAME (0).
4. `.venv python -I -B SCR/tables.py <part2> <ws-m> <main>` → 85 rows, 0 bad (0).
5. `MAIN python -B -c code_identity()` in ws-p → `472fc7f6…` (0).
6. `.venv python -I -B SCR/findhash.py <prefixes> <records>` (0).
7. `MAIN python -B -c rules_78b.e_pod(...)` for 10 kinds × 2 families (0). Then the one-call / two-call upper computation (0).
8. `git show HEAD:<path> | shasum -a 256` for the configs, R_d1 ×2, Llama S1 records, `token_accounting.py` (0).
9. `MAIN python -B -c load_recipe/config_sha256/training_identity` (0).
10. `MAIN python -I -B scripts/scale78b/make_scorer_settings_78b.py --check` in ws-m → 19 of 19, exit 0. It writes nothing under --check (R: :419-423); `git status` count is unchanged.
11. `MAIN python -B -m pytest -q -p no:cacheprovider --collect-only …/test_s4_doses_78b.py` → 13 collected (0). Collection only; no test ran.
12. `git grep -l 9b340bf504400576 HEAD` (0); `shasum` of the two verdict-record copies (0); `ls` of tmp/ top-level names and `.ai/inputs/*78b*` (0, names only).

## 7. Unresolved concerns

1. I did not re-run the scale78b test suites, the S1 check or any mutant. I rely on m-fix and m-verify for those (R).
2. The derived `score_l1_larf__F.json` `scan.rule` text still says "(5-15 at n = 16)" beside `first_block` 10 (M: grep of the rule string). It is stale prose in track M's files, not a Part 2 error. The value governs.
3. The anchor job also exits 3 if fewer than 64 safe anchors are kept (R: make_anchor_answers.py:12). Neither this nor the harmful-pair stop has a ruled fallback (§14 item 7 covers only the latter). Low risk (I: untuned U was 11 and 32 of 600; P1 §0 item 4).
4. A fallback with fewer than 96 kept leaves no S4_96 list. AD2 is then undefined. That is §5's question (to be written), not §1's (I).
