# Track P2-fix report (round 4b, 7-8B $0 build): Part 2 fixes D1-D10, N1-N3, PP17, PP18

Started 2026-11-06 17:10 UTC; this version 17:28 UTC (`date -u` read before each time). Status: **DONE**.
Worker: self-identified Opus 5.5 (the launcher's routing evidence governs).

- Target: `ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md` (round 4's draft; before: `1692caae…`, 427 lines).
- WSK = `scratchpad/b78/ws-k2` (K4BF's worktree, read only). Scratch SCR = `reports/p2-fix-scratch/`.
- Tags: M measured (command number in section 3), R read (path:line), E estimate, I inference.
- No git state changed (only `git status`, `git rev-parse`, `git show HEAD:<path>`, `git diff --stat`). No pod, spend, network, install, download, agent or message. No answer, prompt text, judge output, selector, `hidden/` or secret file opened. The main checkout was read only.

## 1. Files changed

| File | Change |
|---|---|
| `ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md` | Edited. Now 476 lines, SHA-256 `377a472b5f6fe39898b36c5b0d9dcca0cd9b11a5803c352388f2f84cbb7a50c8` (M #16, 17:27 UTC). 263 changed lines in `diff` against the copy SCR/part2-before.md. |

Nothing else in ws-p changed (M #16: `git status --short` shows only `?? …part2.md`). WSK is byte-identical to my 17:10 snapshot, no `__pycache__` (M #16). Scratch files: `wsk2.sha` (108 files), `head-ws-p.sha` (465), `gov.sha`, `part2-before.md`, `xcheck.py`, `xcheck-out.txt`, `tables.py`.

## 2. Per item: what changed and the evidence

Text-only work, so "evidence" is a measured value or a read source line, not a failing test.

| Item | Change in Part 2 | Evidence |
|---|---|---|
| **D1** (major) untuned cap | §1.11: "One E cap covers both calls: 6.0 h on both families", with HEAD's 3.0 / 3.25 h (S4 call only) stated as history. §1.15 row: 6.0 / $17.10 / $9.46 (OLMo), 6.0 / $17.10 / $9.73 (Llama); basis = S3 call 27 chunks + S4 call 16 chunks; E upper 16,146 / 16,692 s. §14 item 3 notes K4B's ~4 h E. | M #8: `e_pod` in WSK's RK (`68bf8f45…`); R: RK:880-892 |
| **D2** encode failure | §14 item 6 rewritten: `answer_list` encodes every prompt first (:156); a refused prompt raises `s1.Refusal` for the whole call (:103-113); exit 2, nothing written (:377-379); the kit records a crash. `rep_pass` counts and skips (`representation_pass.py:337-348`). The $0 encode count is now a precondition. §1.10 notes the S3 call's exit 2. | R (M #10: `cat -n` of those lines) |
| **D3** token_accounting | Table B gains `token_accounting.py` `b9a51f6f…`, plus `scripts/stage1/__init__.py`, `lexicon/lexicon.json`, `lexicon/lexicon.py` (all in the kit's `SCORER_PINS`). Heading reworded: the nine in STAGE1_CODE equal it; the others are run directly, imported or read. | M #11 (shasum and `git show HEAD:` equal); M #15: STAGE1_CODE 9 of 9 equal |
| **D4** MFIX undefined | Short names define MFIX, MV, K4A, K4B, K4CV, K4SV, K4BF, P2R, P2V, P2F as BR paths (`.ai/inputs/stage1-post-w1-20261023/78b/build-round-20261105/<name>.md`), and `m-fix-scratch/after.sha`. WSM (a scratch worktree) replaced by R4B. | R: brief (the lead commits the reports under BR) |
| **D5** category flag | §1.5: the flag is recorded only (`write_score_edit.py:23-26`, :193; `s1common.py:478-512`); no 7-8B unit arm; §14 item 14 asks report-only / unit arm / not read. | R |
| **D6** A8's [C] | §1.4 and §1.5 carry "two under [B], F1's only under [C]" (ADD A8). §14 item 15: which families' anchor and scorer pods run under [C], and before or after the gate. | R: ADD A8; P1:132, :167 |
| **D7** c0's input | §1.13: c0 runs after N's R_1-1101 (`C0_SOURCE`, PP18) and `OEXT_78B`; cite corrected to `runkit/stage1-olmo/setup/job_runner_stage1.py:43-45`. | R: lines 43-45 hold the c0 form (M #10) |
| **D8** ruling 10 branches | §1.3 and §1.16 point to §14 item 16 (three branches; whose states A1 takes; K4CV concern 2 on the X retrain verdict). Not settled. | R: RUL ruling 10 |
| **D9** S3 reuse | §1.8 split by list: S1 by PP5; S4 by ruling 12 / P1 §10; S3 lists a reading the lead confirms (§14 item 17). §1.18 item and §13 row 3 match. | R: RUL ruling 12; P1 §14 item 1 |
| **D10** keep-rule order | §1.11: capped → empty → not_refusal_opening → encode_train, with drop-reason strings. | R: `make_untuned_answers.py:141-151` |
| **N1** | §1.5: `5c0e53b7…` attached to the A1 edit file (PR4:96, :126); the unit's COMPLETE.json `1e5e23f7…`. | R: 1B `write_score_edit.json` `a1.attributes_unit.complete_sha256` (M #12 printed it) |
| **N2** | "13 tests (9 functions, one with 5 parameters)". | R: `grep` 9 `def test_`, one parametrize of 5 (M #13); P2V's collect-only |
| **N3** | §13 row 3 quotes P1 in full and adds the S3 / S4 bases; §14 item 8 quotes PR4:731's heading in full; sealed-order names cited to `labels.json` (M #13 grep); `:82-93` vs `:84-93` reconciled in §1.18; §13 row 11 added (dose edits' hashes to §2). | R |
| **PP17** | §1.0, §1.3, §1.4 item 5, §1.14 (rewritten: `o_only` on θ0; `o_only_with_regenerate` per reused seed: regeneration, verify, acceptance vs the side unit's fingerprints, LS-04, O-ext on e1; both wait on `OEXT_78B` and its form), §1.15 (new row, `regenerate` row gone), §1.16 (OEXT_78B row), §4 (decides the bank and same-job vs separate job before block A; nothing in block 0 depends on it), §13 row 9, §14 items 1, 18, 19. | R: PP17; RK:156-159, :1148-1192; RUN78:428-444, :569-581 |
| **PP18** | §1.3 (Y's pack after the anchor job and S_78; Y kinds refuse until then), §1.13 (unitless; outputs `OUT/train`, `OUT/lean`, `OUT/c0_record.json` hashed under its job folder; `C0_SOURCE`), §1.16 rows, §13 row 10, §14 item 9. | R: PP18; RK:1163-1166, :1220-1228; RUN78:428-433, :585-596; `lean_eval_job.py:42, :147` |
| Kit values | All caps, kinds, pins, state-keeping set, X-only set from WSK's RK: 10 kinds × 2 families; 13 idle pods, $4.33/day. | M #8, #14 |
| Hashes | Table A: 8 values changed, 1 row added (49 files). Table D: RK `68bf8f45…`, plus SR78, RUN78, PT78. Short names: SC, PINS, WRAP, PP (`336b3580…`), PINS_FILE_SHA256 `df3a7878…`. Short names also define every label used. | M #7, #9, #11, #14, #15 |

## 3. Commands and exit status (all foreground, each under 1 min)

1. `date -u` (17:09, 17:10, 17:16, 17:24, 17:26, 17:27, 17:28) (0).
2. `ls`, `wc -l` of reports and the draft (0). `cat p2-verify.md; echo ====…; cat p2.md`: exit 1 (zsh read `====` as a command; reports printed). Re-read with `sed -n` (0).
3. Reads (`cat`, `sed -n`, `grep`, Read) of PP, RUL rulings 10-11, ADD, P1 short names and §12-§14, k4a, k4b, k4-core-verify, k4b-fix, m-fix, m-verify sections, the draft (0).
4. `mkdir -p` SCR; write the skeleton report (0).
5. `git status`, `grep` of RK constants in WSK (0).
6. `sed -n` of RK, `e_upper_s`, RUN78 `sc_commands` (0).
7. `find scripts/scale78b runkit/stage1-78b -type f | xargs shasum -a 256 > SCR/wsk2.sha` in WSK (0, 108 files); a loop comparing the draft's Table A hashes (0: 8 changed).
8. MAIN PY `-B -c` importing WSK's RK: X_ONLY, S78, SC_KINDS, state kinds, pins, `e_pod` for 10 kinds × 2 families, `sc_seeds` (0).
9. `grep`/`sed` of new hashes; `PINS_FILE_SHA256` in WRAP (0).
10. `cat -n` of `make_untuned_answers.py` :80-175, :368-385, `representation_pass.py` :330-348, `s1common.py`, `write_score_edit.py` :1-32, `lean_eval_job.py`, `lean_eval_job.json`, stage-1 kit runner :15-55 (0). `git rev-parse` ×2; `git diff --stat d203070 65e218d` (0: one file, PP).
11. `shasum -a 256` and `git show HEAD:<path> | shasum -a 256` of the four Table B additions (0); `shasum` of the 10 governing texts in the main checkout and by `git show HEAD:` (0).
12. `.venv python -I -B -c` printing the 1B `a1.attributes_unit` and `category_flag_rule` (0).
13. `grep` of labels.json sealed names, dose test count, PR4 section heads, verify-E C3 (0).
14. MAIN PY `-B -c`: `idle_storage_pods` 13, `idle_storage(13)` $4.33, constants (0); WSK `__pycache__` check (none).
15. `.venv python -I -B -c` STAGE1_CODE vs HEAD hashes: 9 of 9 (0).
16. Edits (Edit tool; seven `sed -i ''` one-line replacements; one `.venv python -I -B` renumbering of §1.18) (0). Final: `xcheck.py` (0: 106 full values, 105 found, 1 = the S1 verdict record, resolved in BR `fix-F.md` and `reverify-F.md` by `grep -l`; 67 prefixes, 5 resolved separately: `57ad4148…` = `git show HEAD:runkit/stage1-78b/rules_78b.py | shasum`, `d2030706…` = `git rev-parse HEAD`, `4b8786f7` in m-fix.md, `5c0e53b7` in PR4:96); `tables.py` (0: 93 rows ok, 0 bad); WSK `cmp` with the snapshot (0, unchanged); `git status --short` (0); `wc -l`, `shasum`, `diff | grep -c` (0).

## 4. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| D1 fixed (caps from R4B's RK; coverage stated truly) | passed | §1.11, §1.15; M #8 |
| D2-D10 fixed | passed | section 2 table |
| N1-N3 fixed | passed | section 2 table |
| PP17 stated (o_only_with_regenerate; bank and arm jobs' O and L decided in §4 before block A) | passed | §1.14, §4, §1.15, §1.16, §13 row 9 |
| PP18 stated (c0 unitless, C0_SOURCE; Y's pack timing) | passed | §1.3, §1.13, §1.16, §13 row 10 |
| Every kit value from WSK's `rules_78b.py` | passed | M #8, #14 |
| Every hash re-hashed by me from WSK (scale78b, kit) and HEAD (1B, records) | passed | M #7, #11; `tables.py` 93/93; `xcheck.py` 106 full values all resolved |
| Every short name defined | passed (I: a token scan after the edits; each is defined in Part 2's Short names or P1's) | M #16 token list |
| Only committed paths cited | passed, with one dependency | round-4/4b reports cited at BR paths, which the lead has not yet committed (section 5 job 1); no scratch path is cited |
| No new decision; gaps into §14 | passed | §14 items 14-21 new; items 2, 4 closed by the kit rounds and marked so |
| Part 2 committed and frozen | not tested | the lead's step |

## 5. Jobs for the lead

1. Copy round 4's and 4b's reports into BR before Part 2 is committed: `m-fix.md` (with `m-fix-scratch/after.sha`), `m-verify.md`, `k4a.md`, `k4b.md`, `k4-core-verify.md`, `k4-sec-verify.md`, `k4b-fix.md`, `p2.md`, `p2-verify.md`, `p2-fix.md` (this file). Part 2 cites them there.
2. Merge R4B (K4BF job 1), then re-run my two checks against the merged tree before the commit: `/Users/spiderishi/Coding/attribution/.venv/bin/python -I -B <SCR>/tables.py <part2> <new hash list of the merged scripts/scale78b and runkit/stage1-78b> <SCR>/head-ws-p.sha` (expect 93 ok, 0 bad) and `xcheck.py` the same way. Any bad row means Part 2 changes.
3. Rule on §14 items 6 (encode count as a precondition), 9 (c0's state line), 14-18, 20 (re-run of the S1 check with `2a160990…`), 21. Item 1's re-derivation is a build.
4. Optional: delete SCR after review (small text files, about 200 KB).

## 6. Unresolved concerns

1. Part 2 now cites R4B's bytes, which are not merged. If the merge differs by one byte, Tables A and D and the RK/RUN78/PT78 line cites go stale (§14 item 2).
2. The BR report paths do not exist yet in the main checkout (I listed BR: no round-4 file there at 17:09 UTC).
3. SC §2 still names "`o_only` / `regenerate`" (SC:55). It is a R4B file I do not own; §14 item 19 records it.
4. §1.18's numbered list was renumbered (PP17 and PP18 inserted as items 5-6). No other text cites a §1.18 item number (M: `grep`).
5. I did not re-run any test or mutant; the counts in §1.2 are K4BF's (M there).
