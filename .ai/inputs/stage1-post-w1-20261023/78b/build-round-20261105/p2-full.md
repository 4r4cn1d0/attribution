# P2-full: Part 2 of the 7-8B pre-registration, the full text (round 5, second dispatch)

## Pass 2 (this dispatch). Started 2026-11-07 10:13 UTC; this version 10:25 UTC (`date -u`). Status: **DONE**

- Found at start (M): the target already holds pass 1's full text, SHA-256 `bbe42ff0…` (809 lines), and the
  independent verifier's report `reports/p2-full-verify.md` (VERIFIED_WITH_MINOR, D1-D11) checks exactly that hash.
- Plan: re-check the inputs pass 1 used (K5W unchanged?), then re-check each D-n myself and apply the text fixes that
  need no new decision, in the target only. Pass 1's report is kept below, unchanged, as "Pass 1".
- Backups (M): `p2-full-scratch/rerun/p2-full-pass1.md` (`b994baa9…`), `p2-full-scratch/rerun/part2-bbe42ff0.md`.

- New input found (M, 10:14-10:15 UTC): the main checkout's HEAD moved from `e5a2f86` to **`5c0d091`**, which adds
  only one file: DES gains a section "Rulings on Part 2's open items (recorded 2026-11-07T10:14 UTC)" (DES now
  `4c2b5cb2…`, 11,727 bytes; it was `72d57b20…`). It rules §14 items 6-9, 11, 14-18, 20, 22-28, 30, the S4 boundary
  cases, and confirms the verifier's D1, D7 (b) and D11. This pass applies those rulings and D1-D11 to the target.
- K5W (`ws-k3`) re-hashed (M): 108 files, byte-identical to pass 1's `wsk3.sha`, so every kit value and hash stands.
  `reports/k5-verify.md` is still IN PROGRESS (last write 6 Nov 21:16 UTC); K5F's files are not merged at `5c0d091`.

- Target after pass 2: SHA-256 **`1975fee806a2477b3bd211ec24293b7a48b1d719ac6697bf96254e9127b319eb`**, 830 lines,
  167,000 bytes (M). Before: `bbe42ff0…`, 809 lines. 195 changed lines in `diff` (M). Hex tokens: two added
  (`4c2b5cb264b0f1ca`, DES at `5c0d091`; `5c0d0919336fb7e9`, the commit), none removed (M: `comm` of the token sets).
- Tags: M measured, R read (path:line), E estimate, I inference. No git state changed; no pod, spend, network,
  install, download, agent or message. Nothing written outside the target, this report and `p2-full-scratch/rerun/`.
  K5W re-hashed again at the end: equal, no `__pycache__` (M). No forbidden folder, selector, `hidden/`, judge,
  answer, generation, sample or prompt-text file opened; from the Llama MANIFEST I printed keys, counts and flags only.

### P2.1 Files changed

| File | Change |
|---|---|
| `ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md` | DESO's rulings and P2FV's D1-D11 applied (below) |
| `reports/p2-full.md` | this pass-2 section on top; pass 1 kept below unchanged |
| `reports/p2-full-scratch/rerun/` | `p2-full-pass1.md`, `part2-bbe42ff0.md` (backups), `splice1.py`-`splice3.py` (assert-checked splices), `wsk3-rerun.sha` |

### P2.2 What changed in the target, and the evidence

Short names: **DESO** = DES's new section "Rulings on Part 2's open items" (R: DES:81-127); **P2FV** = BR
`p2-full-verify.md` (not yet in BR); **K5V** = BR `k5-verify.md`. HEAD and DES hashes updated (M).

| Source | Where | Change |
|---|---|---|
| DESO items 6, 17 | §1.4 item 1, §1.8, §1.10, §1.18 item 12, §0 item 14 (new), §13 row 3, §14 items 6, 17 | S3 lists reused; $0 encode count before each untuned pass, counts entered before any untuned answer |
| DESO item 7 | §1.5, §1.19, §16.1 edit 2, §13 row 24, §14 item 7 | anchor stops: A1 not run, contrast P1 not tested on that family (R: P1:181, P1 = U(R) − U(A1)) |
| DESO item 8 | §1.12, §14 item 8 | classifier scored only, rank overlap |
| DESO item 9 / P2FV D11 (i) | §1.13, §4.2, §15 item 5, §14 items 1, 9 | `--w1-18-record` on all three O-ext kinds; `--dev100-source` on regenerated units (R: RUN78:605-612 passes neither) |
| DESO items 11, 14, 15, 16, 18, 20 | §1.16, §1.5, §1.4, §1.3, §1.14 and §4.5, §1.9; §14 items 11, 14-16, 18, 20 | as ruled |
| DESO item 22 / P2FV D1 | §2.3, §0 intro, §14 item 22, end line | every [to be entered] before the freeze; later value by dated amendment |
| DESO item 23 | §1.13, §15 item 12 (new), §14 item 23 | Mac-side C0_SOURCE pack check, build item |
| DESO item 24 | §3.2, §4.3, §15 item 5, §14 item 24 | × 1.5 term until measured; references in-job with the same term; (c) still open |
| DESO items 25, 26, 27, 28, 30 | §2.5 and §4.5; §6 and §15 item 7; §8.6; §16.2 and §15 item 13; §9, §16.3, §16.4 | as ruled |
| DESO S4 boundary | §5, §14 item 34 (new) | S4_top = S4_96 at 96, = S4 at 48; no extra arm. AD1 then equals AD2 / compares S4 with itself (I, R: P1:311) |
| P2FV D2 | §4.3 table | $104.63, $123.13 (M: K5W's RK `funding_need_usd`, 6 cells; 4 equal, 2 differ as P2FV says) |
| P2FV D3 | §8.5 | sums re-added at 50 GB: 2-day $828-1,180 / $978-1,435; 7-day $978-1,355 / $1,128-1,610 (I: arithmetic from SCOUT §9's lines and §4.3's $60-75 / $210-250, R: scout-p2.md:436-438, :651-660) |
| P2FV D4 | §4.6 | PR4:564-574's table form written out; values not computed (R: PR4:574) |
| P2FV D5 | §3.1; §12 | PR4:479 (tests) and :485 (trigger) (R); `parity.sealed` = 13 entries, all `byte_identical` true (M) |
| P2FV D6 | §3.2, §4.3, §15 item 6, §16.4 | `ref_train` is a new kind (M: RK `KINDS` lacks it; R: stage1-olmo `stage1_rules.py:600`) |
| P2FV D7 | §9, §13 row 18, §16.3-§16.5 | pick reader only (R: `stage3_pick.py:11-13`); confirmation reader unbuilt; model labelled (§16.5 item 5) |
| P2FV D8 | §13 row 13 | departure from P1 §14 item 4 stated (R: P1:365, :292) |
| P2FV D9 | §8.6, §14 item 31 (new) | printout covers state-keeping pods only (R: RK:1072-1075, :1088-1091; PP:78-80) |
| P2FV D10 | §0 heading | wording |
| P2FV D11 (ii) | §4.2, §14 item 32 (new) | no 7-8B `transfer_report` kind (M: RK `KINDS`; R: 1B runner :21) |
| new gaps | §14 items 33, 35 | reduced-list pinning; DES header vs DESO |

Not changed: the status line (line 3, already the brief's sentence); all kit values and hashes (K5W equal, M).

### P2.3 Commands (all foreground, each under 1 min; exit status)

1. `date -u` (10:13, 10:14, 10:14, 10:18, 10:20, 10:25, 10:25) (0).
2. `ls`, `wc`, `shasum` of the target, reports and inputs; `cat` of `p2-full-verify.md`, `k5-verify.md`, pass 1's report (0; one `sed` chain exited 1 on a zsh `====` echo, re-run without it, 0).
3. Re-hash of K5W's 108 kit files, `cmp` with `wsk3.sha` (0, twice); `find -name __pycache__` (0, none).
4. `git --no-optional-locks rev-parse`, `log --oneline -3`, `status --short`, `show --stat HEAD` in the main checkout; `status --short` in ws-p (0).
5. `cat -n` of DES; `shasum` of DES and `git show HEAD:DES | shasum` (0; `4c2b5cb2…` both).
6. `grep`/`sed` reads of P1, PR4 (:477-486, :562-575, `S-aW`), SCOUT (§4.3, §9, K1), RK, SR78, RULES-78B.md, plan_tool.py, RUN78:605-612, `oext_unit.py:12-20`, the 1B runner and rules, `stage3_pick.py:9-14`, PP:76-81 (0).
7. MAIN python `-B` importing K5W's RK read-only: `funding_need_usd` 6 cells; `KINDS` (0, twice).
8. `.venv python -I -B` over `git show HEAD:` the Llama MANIFEST: parity keys, counts, flags (0).
9. `.venv python -I -B` splice scripts `splice1.py` (29 replacements), `splice2.py` (24), `splice3.py` (38) and 5 small fix-ups, each replacement asserted unique (0); one Edit (0).
10. `grep` for stale phrases, cross-reference numbers and `[to be entered]`; `diff`, `comm` of hex tokens (0).

### P2.4 Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| 1. RV-1..RV-8 on the scorer section; three O-ext kinds named in the `--w1-18-record` question | passed (pass 1; P2FV 2.4) | unchanged; §14 item 9 (a) now also carries DESO item 9 |
| 2. Every other section from DES (now with DESO), sources tagged, no new decision | passed by my reading | P2.2; gaps DESO leaves are §14 items 31-35, not decided |
| 3. Kit values and code hashes from K5W, re-hashed by me | passed | K5W equal to pass 1's list (M); only two non-kit tokens added (M) |
| Reports cited at BR | passed in the text; K5F, K5V, P2FULL, P2FV not yet in BR | §14 item 2 |
| 4. Status line | passed | line 3 unchanged |
| P2FV D1-D11 fixed | passed (each re-checked by me first) | P2.2 |
| Independent re-verify of this pass | not tested | lead's step |
| Kit suites and mutants | not tested | text track; §1.2's counts are K5F's |

### P2.5 Jobs for the lead

1. Wait for K5V's verdict (its report still reads IN PROGRESS), then merge K5F's 10 files and re-hash Table D's RUN78 and `pack_setup.py` rows; a change K5V forces changes §1.2, §1.13 and Table D.
2. Copy `reports/k5-fix.md`, `k5-verify.md`, `p2-full.md`, `p2-full-verify.md` into BR before the commit (Part 2 cites them there).
3. Rule §14 items 31-35 (idle printout, LN-14's θ0 kind, reduced-list pinning, AD1 at 48 / 96, DES header over DESO), and the still-open parts of items 5, 9 (b) and 24 (c).
4. An independent re-verify of this pass (target `1975fee8…`) before the scorer section's commit.
5. After review, delete `reports/p2-full-scratch/` (pass 1's files and `rerun/`, under 1 MB).

### P2.6 Unresolved concerns

1. DESO is in DES's file but after its header; I read the header as covering DESO (§14 item 35, I).
2. "Dropped by the list's own stage-1 rule" (DESO items 6, 17): I did not open the s-pool record to name that rule's place; the text cites DESO only, and item 33 holds the pinning gap.
3. §8.5's re-added sums are arithmetic on SCOUT's E lines (I); I did not re-derive SCOUT's idle-storage pod counts.
4. I did not re-run P2FV's full hash pool; I checked that no hex token was removed and the two added ones by M.
5. The kit counts in §1.2 remain K5F's; K5V has not finished.

---

## Pass 1 (first dispatch, kept unchanged)

Started 2026-11-06 21:02 UTC; this version 21:26 UTC (`date -u` read right before each write). Status: **DONE**.

- Target (mine to edit): `scratchpad/b78/ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md`.
  Before: SHA-256 `377a472b…` (P2RV's), 476 lines. After: **`bbe42ff0b3f5b0a00bd1d93ce1ca4eeb7b3bf92bd212cd00fc03eb535db83d1e`**, 809 lines, 149,610 bytes (M #20).
- Kit values and code hashes: from **K5W** = `scratchpad/b78/ws-k3` (HEAD `e5a2f86` + K5F's 10 kit files), re-hashed
  by me (M #4). Everything else at the main checkout's HEAD `e5a2f86` via `git show HEAD:<path>` (read only).
- Scratch: `reports/p2-full-scratch/` (`wsk3.sha`, `headfiles.txt`, `headblobs.sha`, `redits.sha`,
  `llama-sealed-manifest.json` (a text-free committed record, copied by `git show`), `run78-head.py` (HEAD's RUN78, for
  the line map), `sec2-12.md`, `sec15-16.md` (my drafts, spliced in), `hashcheck.py`).
- Tags: M measured (command number in section 4), R read (path:line), E estimate, I inference.
- No git state changed anywhere. No pod, spend, network, install, download, agent or message. I wrote nothing in
  the main checkout or in ws-k3 (M #19: ws-k3's 108 files hash as before; no `__pycache__`). I opened no forbidden
  folder, no selector, `hidden/`, judge, answer, generation, sample or prompt-text file; from records I printed key
  names, counts, flags and hashes only. No secret was read or written. The side paper is not mentioned.

## 1. Files changed

| File | Change |
|---|---|
| `ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md` | RV-1..RV-8 applied; K5W's values and hashes; §0 and §2-§12 written; new §15, §16; change log rows 12-27; open items 1-3, 7, 9, 15, 21 updated, 22-30 new; status line |
| `reports/p2-full.md` | this report |
| `reports/p2-full-scratch/*` | scratch (listed above) |

## 2. Per item: what I changed, and the evidence

### Item 1. RV-1..RV-8 on the scorer section, and the three O-ext kinds

| id | Where | Change | Evidence |
|---|---|---|---|
| RV-1 | §1.13 "Unitless"; §14 item 9 (c) | now: the kit runs no separate engine `verify` and no `lean_eval_job.py verify`; the lean job's own `run` checks `OUT/train` (chain) and `OUT/lean` and exits before `c0_record.json` | R: `lean_eval_job.py:603`, :670-674 (HEAD); `verify.py:173-179` |
| RV-2 | Table A heading | "41" → "40" | P2RV M #7 |
| RV-3 | §1.15 last paragraph | `o_only_with_regenerate` "an E kind at HEAD too" becomes a scorer-block kind | P2RV R |
| RV-4 | §1.18 item 8 | "did not rank ... first" | P1 §0 item 8 (R) |
| RV-5 | §1.15 | "Block 0's need printout lists 13 state-keeping pods (N's 2 and, per family, ...)" | P2RV |
| RV-6 | §1.13, §1.7 | c0 branch now K5W's :616-626 (R4B's :586-595 noted); Llama H1 README :14-21 and :23-29 | R: K5W RUN78 (M #6 line map); README at HEAD (read) |
| RV-7 | §1.11 | inner parenthesis closed after "5 parameters" | read |
| RV-8 | Short names, labels line | "Cn of a cited report" (verify-E C3 is its own) and "D-n (stage-1 deviation and item labels)" added | read |
| P2RV concern 3 | §14 item 9 (a) | names `c0`, `o_only` and `o_only_with_regenerate`: none passes `--w1-18-record` (RUN78:599-626); under Branch 128 all three need it (DES E4) | R: K5W RUN78:599-626; `oext_unit.py:7-8`, :31-32 via P2RV |

Also in §1 (from K5W): §1.13 gains K5F's D1 (c0's expected e1 fingerprint read on the pod from the packed source unit,
RUN78:514-541, :619); §1.2's test counts are K5F's (471; mutants 124/34/109/140; stage-1-olmo 762); every RUN78 line
cite moved to K5W's lines (:599-604, :605-612, :616-626, :706-827, :819-821, :559-641; :46 and :428-444 unchanged);
§1.4 item 5 and §1.14's last bullet point to §4; §1.19's merge sentence updated.

### Item 2. Every other section, from DES (SCOUT for detail and sources)

| DES ruling | Where in Part 2 |
|---|---|
| E1 the bank | §4.1 (bank file `6487ed2b…` read from the record's `bank.full_file`, M #13) |
| E2 the cap branch | §4.2 |
| E3 O in the arm's job | §4.3 (SCOUT's cap table, E and its M arithmetic) |
| E4 `OEXT_78B` | §4.4 |
| E5 O for N's units | §4.5 |
| F1, F2 references | §3.1, §3.2 |
| J1, J2 judges | §6 |
| K1, K2 limits | §4.6, §4.7 (τ_L values [to be entered]) |
| K3 costs; the "covers" test | §8.1-§8.6 |
| C1 confirmation | §9 |
| A1 Alpaca | §11 |
| B1 blocks A and B | §2 (block tables per plan, edit files by SHA-256 per family, pod layout, seal, states), §15 (the 11 kit items) |
| K4 seal | §2.5 |
| K5 dose reading | §5 (closes §14 item 21) |
| K6 simulation and its 6% rule | §10.3 |
| K7 `blinded_sigma.py`, reader hash | §10.2, §16.3 (B16's 14 file hashes at `e5a2f86`, M #17) |
| K8 stop rules | §16.1, §16.2 |
| K9 blinding line | §0 items 4-11 (7-11 [to be entered]) |
| B+Qi certificate | §3.2 B+Qi row |
| DES's other $0 checks | §14 item 29 |

Choices labelled after the stage-1 reading: §16.5 (K = 78; the fallback seeds 1102-1104; the 6% trigger; OXE's 1B
branch read, not carried). No new decision: every gap is in §14 (items 22-30 new; see section 6 here).

### Item 3. Kit values and every code hash from K5W

- K5W: 108 files hashed (M #4). Against R4B's list: exactly the 10 K5F files differ (README, `pack_setup.py`, RUN78,
  4 tests, 3 specs); all 49 `scripts/scale78b/` files equal (M #4). K5F's returned six hashes match mine (M #5).
- RK's values printed from K5W's RK (M #8, #9): `X_ONLY_KINDS`, `SC_KINDS`, `SC_STATE_KINDS`, `S78_KINDS`; all null
  pins (`OEXT_78B`, `C0_SOURCE`, `RECIPE_S`, `ENGINE_Y`, `RECIPE_G`, `RECIPE_BQI`); `e_pod` for the 10 scorer kinds ×
  2 families (all equal §1.15) and for `ref_eval`, `safe_lora`, `ref_train_bqi` (used in §3.2); `sc_seeds`;
  `pod_sizes`; `arm_pod` at 38 and 39 steps (§2.1).
- Path-aware table check: Tables A-D, 95 rows, 0 bad (M #15); §2.3's 20 R-edit cells, 0 bad (M #16); 13 Llama R
  hashes equal the sealed MANIFEST's (M #12).
- Every hash token in the file: 131 full + 112 prefixes; 197 match a file hash (HEAD blobs of the cited folders, or
  K5W); the other 46 are record values (config hashes, identities, manifests, fingerprints, the tmp/ text files, commit
  ids), each found in committed records by `git grep` (M #14, #18; `57ad4148…` = `d203070`'s RK, M #18).
- Reports cited at BR (`.ai/inputs/stage1-post-w1-20261023/78b/build-round-20261105/`). K5F and this report are not
  there yet (job 1).

### Item 4. Status line

Line 3 is the brief's sentence verbatim, plus the freeze form, "authorizes no run", and a pointer to §14 item 22's
list of [to be entered] places (20 markers in the file, M #20).

## 3. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| RV-1..RV-8 applied to the scorer section | passed | section 2, item 1 |
| All three O-ext kinds named in the `--w1-18-record` question | passed | §14 item 9 (a); RUN78:599-626 (R) |
| Every other section written from DES, sources tagged, no new decision | passed (by my reading) | section 2, item 2; gaps in §14 items 22-30 |
| Kit values and code hashes from K5W, re-hashed by me | passed | M #4, #5, #8, #9, #15 |
| Every hash in the text checks against a file or a committed record | passed | M #14-#18 |
| Reports cited at BR's committed path | passed in the text; two files not yet there | job 1 |
| Status line as given | passed | line 3 |
| An independent re-verify of this revision | not tested | the lead's next step |
| Kit suites and mutants re-run | not tested | counts are K5F's (R) |
| Committed and frozen | not tested | the lead's step |

## 4. Commands (all foreground, each under 1 min; exit status)

1. `date -u` before each time written (21:02, 21:10, 21:14, 21:26) (0).
2. Reads: DES, PP, RUL (headers, rulings 9, 16), P1 (all), PR4 (§1.3-§1.5, §2.2-§2.3, §3.7, §4.8, §5.1-§5.5, §6, §9.3, §10.1-§10.3, §11), SCOUT, P2RV, K5F, the draft (all) (0).
3. `ls` of reports and BR; `wc`; `diff -q` of BR vs scratch copies (1 for `k5-fix.md`: not in BR, as reported) (0 otherwise).
4. `find scripts/scale78b runkit/stage1-78b -type f | sort | xargs shasum -a 256 > wsk3.sha` in ws-k3 (0; 108 files); `diff` with P2RV's `wsk2-now.sha` (1: the 10 K5F files differ, as expected).
5. `shasum` of the six kit files; `git show HEAD:… | shasum` of RUN78 and `pack_setup.py` (0).
6. `git diff HEAD -- RUN78 | grep @@`; `grep -n` of function and kind lines in K5W's and HEAD's RUN78 (0).
7. `git rev-parse`, `git status --short` (read only, `--no-optional-locks`) in ws-k3 and the main checkout (0).
8. MAIN python `-B` (PYTHONDONTWRITEBYTECODE=1) importing K5W's `rules_78b` read-only: kinds, pins, `e_pod` × 20 (0).
9. Same: `E_KINDS`, reference caps, `sc_seeds`; then `pod_sizes`, `arm_pod` (first try 1: my call passed dicts; then a print bug showed `{}`; third call 0).
10. `git show HEAD:… | shasum` of P1, ERR, RUL, ADD, PP, DES, SCOUT, P2RV, K4BCR, K4BSR, PLAN, CHECK, P78, KCR, PR4 (0).
11. `git diff --name-only 65e218d e5a2f86` and `d203070 e5a2f86` over Table B/C/D paths (0; the latter empty).
12. `git ls-tree` of the sealed edit folders; `git show | shasum` of 26 R edit files; `.venv python -I -B` over the Llama sealed MANIFEST (keys, `files[].sha256`, `seed_map`, `parity` flags) (0: 13 of 13 equal).
13. `.venv python -I -B` over OXE (`bank`, `cap` keys) and the O-ext record (keys, counts, `bank.full_file` hash) (first 1: my loop hit a None; rerun 0).
14. `git cat-file --batch` hashing of 1,723 HEAD blobs under the cited folders (no `hidden/`, no `selector.jsonl`), under `caffeinate -i` (0).
15. `.venv python -I -B` path-aware check of Tables A-D (0: 95 ok, 0 bad).
16. The same for §2.3's R-edit table (0: 20 ok).
17. `git show HEAD:… | shasum` of B16's files, `stage3_pick.py`, `token_accounting.py`, `g1_check_78b.py`, `overrefusal_checks.py` (0).
18. `hashcheck.py` over the file (0: 197 file-matched, 46 not file hashes) and `git grep -l` of the 46 at HEAD (0: each found); `git show d203070:RK | shasum` (0).
19. Re-hash of ws-k3 and `cmp` with `wsk3.sha` (0: unchanged); `find -name __pycache__` (none).
20. `grep` for stale text and section cross-references; `grep -c '[to be entered'` (20); `shasum`, `wc` of the file (0).
21. Edits by the Edit tool and two `.venv python -I -B` string-splice scripts (assert-checked, 0); `sed -i ''` twice (a time fix in this report; two PR4 line fixes in my draft) (0).
22. Reads of K5W and HEAD files for cite checks (`sed -n`, `grep -n`): SR78, RK, RULES-78B.md, the 1B runner, the judge route, both READMEs, `oext_unit.py`, `oext_eval.py`, `oext_unit_y.py`, `lean_eval_job.py`, `verify.py`, PLAN, RP, KCR (0; one zsh `==` echo failed, 1, re-run without it, 0).

## 5. Jobs for the lead

1. Copy into BR before the commit: `reports/k5-fix.md` (with `k5-fix-scratch/` as you choose) and this report
   `reports/p2-full.md` (with `p2-full-scratch/`). Part 2 cites them as BR `k5-fix.md` and `p2-full.md`.
2. Merge K5F's 10 files (K5F job 1); then re-hash Table D's RUN78 (`36a78632…`) and `pack_setup.py` (`40b99b1a…`)
   rows and spot-check the RUN78 line cites against the merged file.
3. Run an independent re-verify of this revision (text, cites, the "no new decision" test) before the scorer
   section's commit.
4. Rule or confirm §14 items 22-30, in particular: 25 (K4's seal vs reading Llama a0-1103's loss for τ_L), 26 (J2's
   "about 9" vs 7 units), 27 (20 GB volumes), 24 (O-ext cap factor; the references' and B+Qi's O-ext), 30 (the DES
   preamble readings), 23 (K5F's Mac-side C0_SOURCE check).
5. Compute OLMo-2-7B's τ_L now (DES K2) and Llama's after N's record-done; enter both in §4.7 and §0 item 9.
6. After review, delete `reports/p2-full-scratch/` (about 0.5 MB; `headblobs.sha` and `headfiles.txt` are lists of
   hashes and paths only).

## 6. Unresolved concerns

1. **The status line names only Llama's τ_L**, but OLMo's τ_L is also [to be entered] (DES K2: "OLMo now"). §14 item
   22 lists both.
2. **SCOUT's money totals assume its idle-storage option (c)**, which DES K3 adopts only in part; §8.5 says so and
   estimates the gap at about $5-10 (I). I did not re-derive SCOUT's other lines beyond re-adding its sums.
3. **Some lines rest on the DES preamble** (FRE's form, the price check, C1's model and kit lines, the references'
   in-job O-ext, F1's fallback label). I carried them and listed them as §14 item 30 rather than treat them as new.
4. **SCOUT cites I did not re-open:** `runner.py:669-675`, the manifests' `banks` blocks, the G configs' field diff,
   `expected_trainable_parameters`, KCR:78-79's batch times, PLAN/RP lines beyond those in section 4 #22. They are
   tagged as SCOUT's (M or R in SCOUT) in the text.
5. **The kit counts in §1.2 are K5F's**; I did not run any suite or mutant (brief: text track; long runs are the lead's).
6. **K5F concern 4** (the final `extend_cap.py` call inherits `os.environ`) is a kit item outside Part 2; not carried.
