# p2-reverify: adversarial re-verify of Part 2's scorer section after round 4b

Started 2026-11-06 18:13 UTC (skeleton); this version 18:30 UTC (`date -u` read right before each write).
Status: **DONE**. Worker: self-identified Opus 5.5 (the launcher's routing evidence governs).

**Verdict: VERIFIED_WITH_MINOR.** D1-D10 and N1-N3 are closed in the text. PP17 and PP18 are stated as ruled.
Every cited hash I re-measured is correct (135 path-checked values, 0 bad). I found 1 minor defect and 7 nits. No
rule is wrong and no new decision is made. Two conditions sit outside the text: the round-4/4b reports are not yet
in BR, and the kit's re-verifier asks for one more short kit fix round (if it runs, Tables A/D and the RK/RUN78/PT78
line cites must be re-taken).

- Target (read only): `scratchpad/b78/ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md`,
  SHA-256 `377a472b5f6fe39898b36c5b0d9dcca0cd9b11a5803c352388f2f84cbb7a50c8`, 476 lines (M #2; equal to P2F's hash).
- R4B = `scratchpad/b78/ws-k2` (HEAD d203070 plus rounds 4 and 4b; read only). Everything else at the main
  checkout's HEAD `65e218d9…` by `git show HEAD:<path>`. The main working tree has two unrelated edits
  (`.ai/HANDOFF.md`, `research/review/EDGE_CHECKS.md`), so I never hashed the working tree.
- Scratch: `reports/p2-reverify-scratch/` (`cites.txt`, `hexlist.txt`, `wsk2-now.sha`, `wsk2-after-maker.sha`,
  `wsk2-*.sorted`, `headrk/` = a copy of HEAD's `rules_78b.py` and `measured-basis-78b.json` for one import).
- Tags: M measured (command number in section 6), R read (path:line), E estimate, I inference.
- No git state changed. No pod, spend, network, install, download, agent or message. I opened no answer, prompt-text,
  judge, selector, `hidden/`, sample or generation file. I did not open or hash any file under the main checkout's
  `tmp/`. The six text files of Table D's last row were matched by hash against their committed records only. No secret.

## 1. Files changed

- This report and the scratch files above. Nothing in ws-p, ws-k2 or the main checkout. M #20: ws-k2's 108 kit and
  scale78b files hash the same before and after my runs; no `__pycache__`; `git status --short` still 57 entries.

## 2. Evidence: what holds

### 2.1 Hashes (M)

- **R4B is the fixer's snapshot and K4BF's final list.** ws-k2's 108 files equal P2F's `wsk2.sha` and K4BF's
  `k4b-fix-scratch/after.sha` byte for byte (M #3, #4).
- **Tables A-D, path by path:** A 44 rows, B 21, C 14, D 14 = 93 rows, 0 bad (M #6: each row hashed at its own path;
  A and the four kit rows of D in ws-k2, the rest by `git show HEAD:`). The 5 test files in Table A's prose equal
  R4B and track M's `after.sha` (M #7). Table A covers all 49 files of R4B's `scripts/scale78b/` (44 rows + 5 prose).
- **Inline cites, path by path:** 42 more values in the text (governing texts P1, ERR, RUL, ADD at `ff349876…`, PP,
  PLAN, CHECK, P78, KCR, PR4; SC, PINS, WRAP, MAKER, RK, HEAD's RK `57ad4148…`, SR78, RUN78, PT78, `PINS-78B.json`,
  `fingerprint_compare.py`, `make_recipe_s78.py`, `build_h1_llama3.py`, the S1 check; the two MAIN_F files; the
  anchor script and record; H1's files; the s-pool, add-s1 and Llama S1 records and script; `write_add_edit.py`,
  `write_score_add.py` and settings; both `R_d1.json`): 42 ok, 0 bad (M #5).
- **Values read from records (R/M):** `5c0e53b7…` at PR4:96 and :126; `1e5e23f7…` = the 1B
  `a1.attributes_unit.complete_sha256` (M #12); the four list hashes and counts 48 / 855 (planned 1,000) / 512, limits
  3072 / 1536, in `s_pool_record.json` (M #11); `9ed61826…`, `c52a50af…`, `18cc31d7…`, `74758af1…` in PINS; the
  Llama S1 MANIFEST names `69426993…` (full), `edit-69426993`, `c52a50af…`, `74758af1…`, 48 rows, 3072, `b9a51f6f…`
  (M #13); `904a0cf1…` (full) in the OLMo `add_edit_record.json`; `78467c97…` (full) = the anchor script's
  `LIST_SHA256` (R: `scripts/make_anchor_answers.py:31`) and in the sealed record; `9b340bf5…` (full) in BR `fix-F.md`
  (M #14); `4b8786f7…` = round 4's `s1_olmo2_7b_check.py` (M #15); `9e9bde6f…`, `c004349c…`, `ceffe0ef…` in
  `oext_unit.json` (R).
- **Engine and recipes (M #9, in clean ws-p):** `code_identity()` = `472fc7f6…`; MAIN_F `config_sha256` `18cc31d7…` /
  `74758af1…`; training identities `36738c38…` / `5b4451e1…`; revisions `470b1fba…` / `0e9e39f2…`; 3072 / 1536 / 2048 /
  batch 32; `query_bank` "ref".
- **HEAD vs 65e218d:** one file differs, PP (M #8).
- **WRAP `STAGE1_CODE` (9) = Table B's first 9; MAKER `BASE_SHA256` (9) = Table C's first 9** (R: WRAP:79-89,
  MAKER:59-69). **SR78 `SCORER_PINS` = 38 files** (M #17); every Table B file a scorer-block pod runs or reads is in
  it except the S1 package's three, as Part 2 says.
- **MAKER --check in ws-k2: 19 of 19, exit 0** (M #19). It wrote nothing (M #20).

### 2.2 Kit values (M #10, R4B's RK imported read-only)

- All 10 kinds x 2 families in §1.15 equal `e_pod` (cap, guard, spend); E uppers 16,145.8 / 16,692.1 s for
  `untuned_answers`; a1_pass window 54,720 s = 15.2 h.
- `X_ONLY_KINDS` = the 8 kinds of §1.3; `S78_KINDS` = 4; `SC_KINDS` = 10; `SC_STATE_KINDS` = retrain, a1_pass,
  o_only_with_regenerate, c0; `SC_KIND_PINS` and `SC_AFTER` = §1.4 and §1.16; `sc_seeds` = OLMo 1101-1103, Llama
  1101-1102; `idle_storage_pods` = 13 entries, $4.33 per day; `OEXT_78B`, `C0_SOURCE`, `RECIPE_S` per family and
  `ENGINE_Y` all None; PINS has exactly 7 null pins per family; `write_score_edit__F.json` `a1.attributes_unit` has 6
  nulls; `representation_pools__F.json` has 2 null pool pins; `write_add_edit__F.json` `lists.s4_top.rows` is null;
  `score_l1_larf__F.json` `first_block` 10 with the family's own modules (M #16).
- **HEAD's RK (M #18):** `untuned_answers` 3.0 / 3.25 h, `regenerate` 2.25 h; every other E cap equals R4B's. This
  backs §1.11's history sentence and §1.15's "no other cap changed" (see RV-4 for one wording slip).

### 2.3 Line cites (R; all read at the cited bytes)

RK :81, :83, :141, :153, :156-159, :326-327, :373, :436, :477, :822-823, :864-957, :880-892, :1064-1068, :1148-1149,
:1150-1159, :1163-1166, :1169-1185, :1186-1192, :1188, :1196-1197, :1220-1228, :1247; SR78 :381; RUN78 :46, :428-444,
:437, :529-610, :569-574, :575-581; PT78 :1310-1316; WRAP :74; `s1common.py` :478-512, :590-592;
`make_untuned_answers.py` :82-93, :103-113, :141-151, :156, :171, :377-379; `representation_pass.py` :337-348;
`write_score_edit.py` :1-28, :23-26, :29-30, :93, :193; `make_anchor_answers.py` :1-17, :117-121;
`lean_eval_job.py` :26-31, :42, :50-54, :147; `oext_unit.py` :1-35, :6-9; `oext_unit.json` :52-66;
`lean_eval_job.json` :37-40; stage-1 runner :19-20, :43-45, :49-53; `stage1_rules.py:602`; PR4 :61, :96, :126, :177,
:228, :731, :815, :1014; PLAN-S :149; KCR :70, :161; RP :43; P78 :357, :367, :377, :379, :413; FOCUS lines 67 and 74
at HEAD (the quoted phrases are there). Two offsets are off by one or two lines (RV-6).

### 2.4 D1-D10 and N1-N3 (P2V's list)

| Item | Closed? | Evidence |
|---|---|---|
| D1 untuned cap coverage | yes | §1.11 and §1.15 say 6.0 h for both calls, with HEAD's 3.0 / 3.25 h (S4 only) as history; values = R4B's RK (M #10) and HEAD's (M #18); §14 item 3 |
| D2 encode failure | yes | §14 item 6 = `make_untuned_answers.py:156`, :103-113, :377-379; `representation_pass.py:337-348` (R) |
| D3 token_accounting | yes | Table B row `b9a51f6f…` plus `__init__.py`, both lexicon files (M #6); heading reworded and true (R: WRAP:79-89) |
| D4 MFIX undefined | yes in the text | Short names define MFIX ... P2F as BR paths. The files are not in BR yet (concern 1) |
| D5 category flag | yes | §1.5 flag recorded only; `write_score_edit.py:23-26`, :193; `s1common.py:478-512` (R); §14 item 14 |
| D6 A8's [C] | yes | §1.4 item 3, §1.5 retrain carry "two under [B], F1's only under [C]"; §14 item 15 |
| D7 c0's input; cite | yes | §1.4 item 5, §1.13; cite :43-45 holds the c0 form (R) |
| D8 ruling 10 branches | yes | §14 item 16, pointed to from §1.3 and §1.16 |
| D9 S3 reuse | yes | §1.8 by list; §14 item 17; §1.18 item 12; §13 row 3 |
| D10 keep-rule order | yes | §1.11 = capped, empty, not_refusal_opening, encode_train (R: :141-151) |
| N1 | yes | `5c0e53b7…` on the edit file (PR4:96, :126), `1e5e23f7…` on COMPLETE.json (M #12) |
| N2 | yes, with a typo | 13 tests (M #21: 9 `def test_`, one parametrize of 5); unbalanced parentheses (RV-7) |
| N3 | yes | §13 row 3 quotes P1 §14 item 1 verbatim; §14 item 8 quotes PR4:731 verbatim; sealed names in `labels.json` (M #11); :82-93 / :84-93 reconciled; §13 row 11 |

### 2.5 PP17 and PP18 as ruled

- **PP17** (R: PP:94-100). No standalone `regenerate` (§1.3, §1.14; RK `SC_KINDS`, `E_KINDS`); one kind
  `o_only_with_regenerate` on one single-job pod: regeneration, verify, acceptance against the side unit's
  fingerprints, then O-ext on e1 (§1.14 = RUN78:575-582 and :676-767); its own E cap (4.5 h, §1.15); it and `o_only`
  (θ0) wait on `OEXT_78B`, null until §4 names the bank (§1.14, §1.16 = RK:1150-1159, :1188); §4 decides the bank and
  same-job vs separate job before block A (§1.14 last bullet, §4); nothing in block 0 depends on it (§1.14, §4).
  The difference from the 1B J2 accept list (no data-config compare) is recorded as §14 item 18.
- **PP18** (R: PP:101-104). c0 unitless, outputs hashed under its job folder (§1.13 = RUN78:428-433, :788-790); its
  source pin `C0_SOURCE` = block 0's R_1-1101 unit, null until the lead fills it by a recorded step (§1.13, §1.16 =
  RK:1163-1166); Y's pack built when ruling 10's retrain is prepared, after the anchor job and S_78; every Y kind
  refuses until then (§1.3, §1.4 item 3 = RK:1220-1228).
- §1.18 labels both, with what they read; §13 rows 9 and 10 log them.

### 2.6 No new decision

Every item the rulings leave open is in §14 (items 1, 5-9, 11, 14-21). The readings that are presented (S3 list reuse;
one-entry-per-family L1 files; c0 in the state-keeping set) are labelled as readings the lead confirms (§1.8,
§14 items 9, 10, 17). The commands, caps and pins are R4B's own, tagged R or M. I found no sentence that settles an
open question.

## 3. Defects (none blocks; none changes a rule)

| id | sev | where | what (evidence) | fix |
|---|---|---|---|---|
| RV-1 | minor | §1.13 "Unitless" bullet: "so neither the engine's verify nor the lean job's own verify runs for it"; §14 item 9 (c) "No verify runs for c0" | False as written. The lean job's `run` itself checks `OUT/train`'s chain with the engine's verify module (`chain_problems`) and `OUT/lean` with `verify_files`, and stops with exit 1 before it writes `c0_record.json` if either has a problem (R: `scripts/stage1_s1/lean_eval_job.py:603`, :670-674; `experiments/safety_selection/verify.py:173-179`). What the kit does not run is a separate engine `verify` call and the separate `lean_eval_job.py verify --out` step. K4BF §8 item 7, the cited source, says only the second. A reader of the frozen text would think c0's training unit is unchecked. | "The kit runs no separate engine `verify` and no `lean_eval_job.py verify` for c0; the lean job's own `run` checks `OUT/train` and `OUT/lean` before it writes its record (R: `lean_eval_job.py:670-674`)." Same in §14 item 9 (c). |
| RV-2 | nit | Table A heading: "41 of them equal P2R's values" | P2R covered 48 files (43 rows + 5 prose). 8 changed, 1 is new, so 40 equal P2R's values: 40 + 8 + 1 = 49 (M #7: 35 of P2R's 43 rows unchanged, plus the 5 prose files). | "40 of them". |
| RV-3 | nit | §1.15 last paragraph: "`regenerate` (2.25 h) is gone and `o_only_with_regenerate` (4.5 h) is new (PP17)" | HEAD's RK already had `o_only_with_regenerate` in `E_KINDS` with the same 4.5 h cap (R: HEAD `rules_78b.py:316`, :879-881; M #18: `e_pod` 4.5 h, $14.33 at HEAD). It was not in HEAD's `SCORER_KINDS`. What is new is its place in `SC_KINDS`, `SCORER_KINDS` and `X_ONLY_KINDS` (K4BF §3: "its cap equals the old o_only_with_regenerate row"). | "`o_only_with_regenerate` (4.5 h, an E kind at HEAD too) becomes a scorer-block kind". |
| RV-4 | nit | §1.18 item 8: "L1 did not rank stage 1b's planted leaf (P1 §0 item 8)" | P1 §0 item 8 says the content classifier ranks the planted leaf first and that L1 (with DataShield-style, H1, H2a, H2b) does not; L1 did rank it, not first. This is a blinding-line statement, so the words matter. | "L1 did not rank stage 1b's planted leaf first". |
| RV-5 | nit | §1.15 "Block 0's state-keeping pods are 13 ... (N's 2; per family the retrain, a1_pass, c0 and one o_only_with_regenerate pod per reused seed)" vs Short names "N = block 0" and §1.14 "Nothing in block 0 depends on PP17's open parts" | Two scopes of "block 0" in one text: N only (Short names, §1.14, PP17's words) and the kit's block-0 printout, which also lists the retrain and scorer pods (RK `block0_report`, :1108-1136; PP14). Read together, §1.15 puts `o_only_with_regenerate` pods in block 0, and §1.14 says block 0 does not depend on PP17. | "Block 0's need printout lists 13 state-keeping pods (N's 2 and, per family, ...)". |
| RV-6 | nit | §1.13 "RUN78 `sc_commands`, the `c0` branch, :585-596"; §1.7 "README.md:13-19" and "its README:21-29" | The c0 branch is RUN78:586-595 (R). The Llama H1 README's rule is :14-21 and its parity text :23-29 (R). The ranges overlap the right text, so nothing is misread. | Correct the three ranges. |
| RV-7 | nit | §1.11 dose lists: "(M: `test_s4_doses_78b.py`, 13 tests (9 functions, one with 5 parameters; P2V M: `pytest --collect-only`; SC §3 says 10)." | Two "(" and one ")" in the clause; the sentence does not close. | Close the inner parenthesis after "5 parameters". |
| RV-8 | nit | Labels: "BR verify-E C3" (§1.11); "deviation D-1" (§1.8); "the 1B D-2 wrapper" (§1.2) | Short names define **Cn** as CHECK's corrections, and list a cited report's own labels as Dn, Nn, DK-n, RF-n, RV-… only; verify-E's C3 reads as CHECK C3. D-1 (the s-pool record's deviation) and D-2 (the stage-1 pool-pins item) are not in the stage-1 label list. | Add "Cn of a cited report" and "D-n (stage-1 deviation and item labels)" to the label lines. |

Not counted as a defect: §1.0 says Part 2 names "the SHA-256 of every script and settings file used"; Table D names
RK, SR78, RUN78, PT78 and the basis file, but not the kit's `pack_setup.py` (`f0f098f2…`, changed in R4B: the input
secret scan) or `backup_records_stage1.py` (changed in R4B: D8). Both are kit machinery, not scorer code, and the kit
hashes them in its own records (K4BF §6). The lead may add them to Table D or leave §1.0 as it is.

## 4. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Part 2 unchanged since P2F (hash) | passed | M #2 |
| Every cited file re-hashed (kit and scale78b in ws-k2; the rest at HEAD) | passed | 93 table rows + 42 inline values path by path, 0 bad (M #5, #6); record values (M #11-#15) |
| Every rule against its source | passed, with RV-1 | section 2.3; RV-1 misstates what the lean job checks |
| Kit values (caps, kinds, pins, seeds, idle pods) | passed | M #10, #16 |
| D1-D10 closed | passed | section 2.4 |
| N1-N3 closed | passed (N2 with RV-7's typo) | section 2.4 |
| PP17 stated as ruled | passed | section 2.5 |
| PP18 stated as ruled | passed | section 2.5 |
| No new decision | passed | section 2.6 |
| Labels and short names | passed with RV-8 | section 3 |
| Citations resolve | passed with RV-6; BR report paths do not resolve yet | section 2.3; concern 1 |
| Tests and mutants re-run | not tested by me | text verification only; R4B equals K4BF's final list byte for byte (M #4), so K4BF's 451 / 263+2 / 74 counts apply to these bytes; MAKER --check re-run: 19 of 19 (M #19) |
| Committed and frozen | not tested | the lead's step |

## 5. Jobs for the lead

1. Before the commit, copy into BR (`.ai/inputs/stage1-post-w1-20261023/78b/build-round-20261105/`): `m-fix.md` with
   `m-fix-scratch/after.sha`, `m-verify.md`, `k4a.md`, `k4b.md`, `k4-core-verify.md`, `k4-sec-verify.md`,
   `k4b-fix.md`, `p2.md`, `p2-verify.md`, `p2-fix.md`. None is there now (M #14: `ls` of BR). Part 2 cites them there.
2. Decide on k4b-core-reverify's job 1 (a short kit fix round for K4bcr-D1, c0's fingerprint bound to the packed
   source unit, and test gaps) before committing Part 2. If it runs, RK, RUN78, PT78 and maybe SR78 change: re-take
   Table D, every RK / RUN78 / PT78 line cite and §1.15, then re-run this check.
3. Apply RV-1 to RV-8 (text only; about ten one-line edits). None needs a new measurement.
4. After the merge of R4B, re-hash with path-aware checks (not prefix-only): `cites.txt` and the table check of
   section 6 #5-#6 can be re-run with the merged tree in place of ws-k2.
5. Optional: delete `reports/p2-reverify-scratch/` after review (text files and one copied `rules_78b.py`, under 1 MB).

## 6. Commands (all foreground, each under 1 min; exit status)

1. `date -u` before each write (18:12, 18:13, 18:29, 18:30) (0). `ls` of the scratch and report folders (0).
2. `shasum -a 256` and `wc -l -c` of Part 2 (0).
3. In ws-k2: `git rev-parse HEAD`, `git status --short` (0); `find scripts/scale78b runkit/stage1-78b -type f | sort | xargs shasum -a 256 > SCR/wsk2-now.sha` (0, 108 files); `diff` with P2F's `wsk2.sha` (0, same).
4. `.venv python -I -B` comparing `wsk2-now.sha` with `k4b-fix-scratch/after.sha` (0: 108 common, 0 differ).
5. `.venv python -I -B` over `SCR/cites.txt`: 42 values, each hashed at its own path (ws-k2 file or `git show HEAD:`) (0: ok 42, bad 0).
6. `.venv python -I -B` path-aware Tables A-D check (0: A 44, B 21, C 14, D 14 ok; 0 bad; 49 scale78b files covered).
7. `shasum` of the 5 prose test files in ws-k2, at HEAD and in track M's `after.sha` (0; equal to R4B; one differs from HEAD as track M changed it); P2R's Table A vs R4B (0: 35 same, 8 changed, 1 new file).
8. `git diff --stat d203070 65e218d`; `git rev-parse` (0: one file, PP).
9. MAIN python `-B` in clean ws-p: `code_identity()`, `load_recipe`, `config_sha256`, `training_identity` (0).
10. MAIN python `-B` importing R4B's `rules_78b` read-only: kinds, sets, pins, `e_pod` for 10 kinds x 2 families (1: my last line called `sc_seeds` with one argument; every value before it printed). Re-run with the right call (0).
11. `git show HEAD:` + `.venv python -I -B` of `s_pool_record.json` (hashes and counts only) and `labels.json` (key names only) (0).
12. `.venv python -I -B` of the 1B `write_score_edit.json` `a1` block (0).
13. `.venv python -I -B` of the Llama S1 MANIFEST (key checks), `git show | shasum` of its settings and record (0).
14. `grep -c` of full hashes in the OLMo add-s1 record, the anchor record, BR `fix-F.md`; `git grep -l` of `9b340bf5…`; `ls` of BR (0).
15. `shasum` of track M's `new_s1_check.py`; `diff` of round 4's and R4B's `s1_olmo2_7b_check.py` (1, files differ as expected: only the write guard).
16. `.venv python -I -B` of the derived settings (null pins, untuned lists, doses keys, L1 scan) and PINS (null pins, shared) (0).
17. MAIN python `-B` printing SR78 `SCORER_PINS` (0: 38).
18. HEAD's `rules_78b.py` and basis file copied to `SCR/headrk/` by `git show`; MAIN python `-B` `e_pod` there and a cap-by-cap compare with R4B (0).
19. `PYTHONDONTWRITEBYTECODE=1 MAIN python -I -B scripts/scale78b/make_scorer_settings_78b.py --check` in ws-k2 (0: "19 of 19 files equal their regeneration"). The chained `diff` after it exited 1 (my own sort mismatch), so I re-did the comparison in #20.
20. Re-hash of ws-k2's 108 files, `cmp` with `wsk2-now.sha` (0, same); `find -name __pycache__` (0 found); `git status --short | wc -l` (57).
21. `grep -c 'def test_'` and `parametrize` in `test_s4_doses_78b.py` (0: 9 and 1 of 5 values).
22. Reads (`sed -n`, `awk`, `grep`, `git show HEAD:`) of PP, RUL, ADD, ERR, P1 §0, §12-§14, CHECK C1/M1-M4, KCR, RP, P78, PR4, PLAN-S, FOCUS lines 67 and 74, the 1B scripts, settings and runner, R4B's RK, RUN78, PT78, SR78, WRAP, MAKER, SC, PINS, and the reports p2-fix, p2-verify, m-fix, m-verify, k4a, k4b, k4b-fix, k4-core-verify, k4b-core-reverify, k4b-sec-reverify (0). One `sed` chain in zsh failed on an `echo ===` (1) and was re-run with `awk` (0).

## 7. Unresolved concerns

1. **BR does not hold the cited reports yet** (M #14). Part 2's Short names say "committed by the lead under BR" as a
   fact, and §14 does not list the copy as a precondition (only P2F's job list does). If Part 2 is committed first,
   every MFIX / MV / K4A / K4B / K4CV / K4SV / K4BF / P2R / P2V / P2F cite dangles.
2. **R4B may change again.** k4b-core-reverify (VERIFIED_WITH_MINOR) recommends one short kit fix round before the
   scorer pods (K4bcr-D1 to D3); k4b-sec-reverify (VERIFIED_WITH_MINOR) lists test-strength gaps. A code fix changes
   RK / RUN78 / PT78 hashes and may move line cites. Part 2 §14 item 2 covers this in general; "commit as written"
   holds only if the lead merges R4B's current bytes.
3. **`--w1-18-record` for `o_only` and `o_only_with_regenerate`.** §14 item 9 (a) names c0 only. The two O-ext kinds
   also pass none (R: RUN78:572-582), and `oext_unit.py` reads W1-18's record for its cap branch when given
   (R: `oext_unit.py:7-8`, :31-32). It belongs to item 1's re-derivation (k4b-core-reverify concern 3). Part 2 could
   name all three kinds in item 1.
4. **c0's E cap basis text** (RK and §1.15: "the evalonly bound + 1.5 x 600 s") does not name c0's own R_1 training,
   which the lean job runs (R: `lean_eval_job.py:30-31`). By my numbers the bound still covers it (E: training 33
   steps about 930 s; the evalonly bound 9,644 / 9,943 s against C-lean's smaller evaluation; M #10 for the constants).
   A kit wording point, not a Part 2 defect.
5. I did not re-run the test suites or mutants and did not run the S1 data test (it reads `tmp/stage1-olmo/`, which my
   brief forbids). The counts in §1.2 are K4BF's; R4B equals K4BF's final bytes (M #4).
