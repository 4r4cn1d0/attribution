# R1 Track S fix round: adversarial re-verification of `blinded_sigma.py` and the SR-2 simulation

Started 2026-11-08 17:11 UTC; finished 17:50 UTC (both from `date -u`).

- Role: Track S's re-verifier, read-only on WS. I wrote only this report and R/r1-s-reverify-scratch/.
- Target: B/ws-s, a detached worktree at 3481d85, and Track S's 7 new files.
- Hashes (M: `shasum -a 256`, 17:11 UTC and again at 17:48 UTC) equal the brief and the builder's fix-round table:
  - `blinded_sigma.py` `6e7079e8…`; `sr2_simulation.py` `0ff5e545…`; `settings/sr2_simulation.json` `99410f9f…`;
  - `test_blinded_sigma.py` `28c443b9…`; `test_sr2_simulation.py` `7813636d…`;
  - `mutation_spec_sr2.json` `e349a6dc…`; `run_mutants_sr2.py` `50594102…`.
- `git status --porcelain` in WS lists the same 7 untracked files and nothing else, at start and at end (M). No
  `__pycache__` was written in WS (M: `find`).
- The settings file's full grid was never run. Only smoke copies ran (other seeds, other replicate counts, other hashes).
- The builder's diff R/r1-s-scratch/fix.diff (`3b98d017…`) equals a fresh `diff -u` of the pre-fix copies
  (R/r1-s-scratch/prefix/, hashes = the first verifier's) against the current files: the same 643 changed lines (M).
- Tags: M measured (the command or file is named); R read (path:line in WS); E estimate (basis named); I inference.

## Verdict: VERIFIED_WITH_MINOR

**The code is right on every check I ran.**
- No U value, cell value, arm mean or residual reached stdout, stderr, any file or any refusal in 20 CLI attacks and
  one in-process race case (M). Only the in-process `read()` lets an error's text through (SR10; the CLI does not).
- σ̂_A equals two independent computations on five designs, to the last digit (M).
- The chain equals an independent chain replicate by replicate, now also through `simulate_row` with all five
  scenarios (M: 5 configurations × 5 scenarios × 100 replicates).
- The lead's commands run as written; shards merge byte-identically, also when the 9 shards run at once (M).
- The suite gives 268 passed, 57 skipped. The builder's 73 mutants: 73 killed, 0 survived, 0 invalid (M).

**SV-1 to SV-7 are closed as ruled.** SV-2's integration test is a real independent chain. On its own it kills the
four wiring mutants, claim-fresh and the one-sigma mutant (M).

**What is left are test gaps in the new code, not code defects.** 9 of my 12 extra mutants survive (M):
- the per-family σ is not held between `simulate_row` and `run_chunk` (SR1);
- the summary's largest rate is not held over both families or over the two ratio scenarios (SR2);
- the blinding test's file snapshot does not cover every writable place (SR3);
- five nits (SR4-SR8), and two text nits (SR9, SR10).

None of them changes what the code computes today, so the merge can go ahead now. The full simulation may then run
on the current `0ff5e545…` and `99410f9f…`:
- SR1-SR8 are test-only fixes. They change neither script's hash nor the settings' hash, so a run made now stays valid
  after them.
- SR1 and SR2 matter most. They guard the R-12 part of the reading that decides SR-2. Fix them in the next round, and
  before any further edit to `sr2_simulation.py`.
- SR9 is a text error in the settings. It changes the settings' hash. The file is unrun, so the cheap order is to fix
  SR9 first and then run (the lead's call).

## Defects

| id | severity | file:line | defect | failure scenario | fix |
|---|---|---|---|---|---|
| SR1 | minor | `sr2_simulation.py:529`, `:538`; `tests/test_sr2_simulation.py:536-575`, `:240-275` | **The wiring of each family's σ from `simulate_row` into `run_chunk` is untested.** The SV-2 test calls `run_chunk` with σ values it computes itself (test :551). The [C] output test checks only the printed `sigma_pair_pp_by_family`, which comes from the same `sigmas` dict. M: mutant `RV-sim-run-ignores-family-sigmas` survives. It runs both families at the grid's σ but still prints the ratio σ values. | An edit makes the two R-12 scenarios silent copies of "none" under [B], while the output says Llama ran at 1.5× or 1/1.5× OLMo's σ. The 6% rule is then never applied to unequal noise. The suite stays green. | Add a row-level parity test through `simulate_row`. Give it a [B] smoke settings dict (one chunk), and compare its plan counts and familywise and Holm counts with the independent chain at the ratio's σ. The form is R/r1-s-reverify-scratch/e2e_row_parity.py; in 2 or 3 scenarios, 40 replicates are enough. Add the mutant to the spec. |
| SR2 | minor | `sr2_simulation.py:574-580`; `tests/test_sr2_simulation.py:270-273` | **The summary's largest rate is checked only under [C].** Under [C] there is one family, and the two ratio scenarios equal "none". So the test cannot see a maximum that skips Llama or skips the ratio scenarios. M: `RV-sim-max-olmo-only` and `RV-sim-max-skips-ratio-scenarios` both survive. | The largest [B] rate is Llama's, or sits in a ratio scenario. An edit drops it from the maximum, and the reading line and `max_above_threshold` then report a lower rate than the rows hold. The lead reads the reading line (DES K6) and could adopt SR-2 while one simulated rate is above 6%. | Add a unit test of `summarize` on a synthetic [B] document: two families, the five scenario names, and the maximum placed (a) in Llama's family and (b) in "llama sigma x 1.5". Also give one row a nonzero `refused_contrasts`, and put one count exactly at 0.06 × reps (this covers SR5 and SR6). Add the mutants. |
| SR3 | minor | `tests/test_blinded_sigma.py:281-294` | **The blinding test's file check covers only three folders:** the fixture root, tmp_path with its cwd, and `scripts/scale78b`. A write anywhere else is not seen. M: `RV-bs-side-file-repo-root` writes every cell's U to `<repo>/leak-cells.txt` and survives; I found the 930-byte file in the mutant's copy after a green suite. | An edit writes the cells to the repository root, the inputs' parent folder, `$TMPDIR` or `$HOME`. The "blinding test verified" condition (P2 §10.1; `PLAN_B_78B`) would then rest on a test that misses the leak. The code today writes only `--out` (R: blinded_sigma.py:351; M: my attacks snapshot the whole scratch root and find no other file). | Record every write the CLI makes. Run it as `python -I -B -c` with a wrapper: `sys.addaudithook` logs each `open` event whose mode or flags write, and each `os.rename`, `os.mkdir`, `shutil` and `os.symlink` event, to a file descriptor apart from stdout and stderr; the wrapper then uses `runpy.run_path(script, run_name="__main__")`. Assert that the only write is `--out` on success and that there is none on a refusal. Alternatively, on this Mac, run the CLI under `sandbox-exec` with `(deny file-write*)` except `--out`. Add the mutant. |
| SR4 | nit | `blinded_sigma.py:349-354`; tests | **The exclusive-create branch is untested.** The "written once" test is refused by the existence check at :344, never by `"xb"`. M: `RV-bs-out-wb` survives. M: the code is right; in-process, a file made between the check and the write is refused with "--out exists: the output is written once", and the file is kept (bs_attacks2, case race-exclusive-create). | An edit back to `"wb"` would overwrite a file made in the race window. It is the same value, but the file is no longer "written once". | Add my in-process race case: monkeypatch `bs.read` to create `--out` after the check. Assert the exact refusal, the kept bytes, and empty stdout and stderr. |
| SR5 | nit | `sr2_simulation.py:597`; tests | **`max_above_threshold` at exactly 6% is untested.** At 60 replicates a rate of exactly 0.06 cannot occur. M: `RV-sim-threshold-ge` (`>=`) survives. | The flag would read "above" at exactly 1,200 / 20,000, where the rule says "above 6%" (DES K6). Only a tie is affected. | Cover it in SR2's `summarize` test. |
| SR6 | nit | `sr2_simulation.py:586`, `:598`; `tests/test_sr2_simulation.py:267` | **`refused_contrasts_total` is tested only where both sides are 0.** M: `RV-sim-refused-total-zero` survives. | The SV-7 total could print 0 while rows hold refusals. The rows still print their own counts. | Cover it in SR2's `summarize` test. |
| SR7 | nit | `sr2_simulation.py:469`; `tests/test_sr2_simulation.py:536-575` | **N's printed plan is not wired into the parity check.** The SV-2 test does not compare `plans["N"]`. M: `RV-sim-n-plan-olmo-only` (N pools OLMo-2-7B's cells for both families) survives. | N's plan is printed only and moves no decision (P1 §6.4; the first verifier's §4). Under the ratio scenarios a wrong printed plan would mislead a reader. | In the SV-2 test, compare `plans["N"]` with `noise_reading.seed_rule` on an independent σ̂_pool. Or state in the output that N's plan is not held by the parity test. |
| SR8 | nit | `blinded_sigma.py:247-248`; tests | **The engine map's form check has no test.** M: `RV-bs-engine-keyset-unchecked` survives. M: the code refuses the old `{block_a, reused}` form, an extra key and a non-hex value with the exact line "olmo2-7b: engine gives the a0, R and block_a code identities (64 hex each)" (bs_attacks2). | Without the check, an extra key passes, and the old two-key form fails as "unexpected error (KeyError)". This fails closed, but not with its own line. | Add the three cases to `test_each_role_is_checked_…`, with full-line refusals. |
| SR9 | nit (text) | `settings/sr2_simulation.json:94` (`limits[1]`); the lead's R-11 wording | **"start at 0.5% of alpha" is wrong by a factor of 20.** O_k and L_k start at γ/(2K) each, with γ = 1/10 (R: `scripts/stage1_s1/reading/phi.py:5-7`, `:53-55`; `settings/reading.json:235`). In all they hold γα = 0.5% absolute, which is 10% of α. | A reader would take Φ's unsimulated O/L words as 20 times smaller than they are. Not a computation. | Write "start at γα = 0.5% in all (10% of α), within their own contrasts". The settings file is new and unrun, so this changes only its hash and `written_utc` (and the test at test_sr2:320). The lead's R-11 text has the same slip. |
| SR10 | nit (doc) | `blinded_sigma.py:6-9`, `:293-327` | **The in-process API `read()` is not guarded.** The doc says no value reaches "an exception message", but the guard is in `main()` only. M: `bs.read` on the zero-answers cell raises `ZeroDivisionError`, and its message holds a planted count (bs_attacks2, case in-process-read-zero-answers). The CLI prints the type only (M). | No planned caller exists: the lead runs the CLI (r1-s.md :162-163). A future K2 tool that imports `read()` and prints a traceback would echo a U numerator on a corrupt unit. | Move the type-only guard into `read()`, or narrow the doc to the CLI. Add the in-process case as a test. |

Not defects, for the record:
- The reading line names the grid's σ_pair (OLMo-2-7B's) even when the largest rate is Llama's in a ratio scenario
  (R: sr2:589-594). The row prints `sigma_pair_pp_by_family` beside it.
- Under [C] the two ratio scenarios repeat "none" (M: parity, [C] full at 7.0: equal plans and familywise counts). This
  costs about 40% more [C] runtime (E: 5 scenarios for 3 distinct), and changes nothing.
- `V-sim-claim-fresh-block-a` flips signs only. Every p-value is sign-invariant, so it removes no selection; it is killed
  only through power and better (I; M: the SV-2-only run kills it).

## 1. SV-1 and blinding

**Attacks (M: bs_attacks2.py → bs_attacks2_out.txt).**
- Method: each case runs the CLI from a fresh cwd. It snapshots every file under my whole scratch root (the fixture,
  every cwd, every out folder) and the WS package, before and after.
- It scans stdout, stderr and every new file for the test's sentinels, every raw count, "k/60", "Fraction(k, 0)" and
  "'k'".

| Group | Cases | Result |
|---|---|---|
| The first verifier's five, re-run | zero answers, string count, malformed repetition, guard row without `prompt_id`, `--out` in a missing folder | Each exits 1 with one stderr line: a type-only line or the frozen reader's line. The missing folder now refuses before the read with the exact line (it was a traceback). |
| Late refusals at the last cell read (olmo2-7b a0@1104, all other U already in memory) | over-refusal mismatch; zero answers; unsafe count + 1 | The exact frozen line, the exact type-only line, and the frozen reader's line "<unit folder>: the guard records disagree with summary.json" (it names the folder, no value). |
| Engine per role | a0, R or block_a wrong; the old `{block_a, reused}` form; an extra key; a non-hex value; a0 and R swapped; the split fixture | The exact refusal at the first cell of that role. The split fixture passes. |
| `--out` paths | parent is a file; dangling symlink; `/dev/stderr`; read-only folder | The exact lines "--out's folder does not exist…", "--out exists…" (×2), and "unexpected error (PermissionError); nothing written". |
| Exclusive create (in process) | a file made between the check and the write | Refused "--out exists: the output is written once"; the file is kept; stdout and stderr are empty. |
| In-process `read()` | zero answers | Raises ZeroDivisionError with a planted count in its text (SR10). |

- Every CLI case: 0 planted values, 0 changed files, and no new file except `--out` on the one success.
- **The byte test holds the whole output** (R: test_blinded_sigma.py:312-335). It checks stdout == the literal,
  `--out` bytes == the literal, stderr == "", the only new file is `--out`, and nothing changed. Then it checks two
  refusals in full, with no file.
- **Full-line refusals:** every in-process refusal goes through `refuses()`, which compares equality (R: :64-70). The
  CLI tests compare the whole stderr line (R: :330, :334, :357, :375). No `match=` is left in the file (M: `grep`).
- **SV-1's mutants are killed** (M: shards 1-2):
  - `V-bs-exc-text-to-stderr` by `test_an_unexpected_error_prints_one_type_only_line_and_writes_nothing`;
  - `V-bs-side-file` by the byte test.
- **The remaining gap is SR3:** the snapshot folders (R: :287).

## 2. SV-2: the chain

**Read (R: test_sr2_simulation.py:467-575).** `independent_chain` is built from other code:
- `blinded_sigma.pooled_sigma` on `blinded_sigma.design_cells`, in exact rationals;
- `noise_reading.seed_rule`;
- B16 `fit_cells`, with multi-start, the lone 1101 cells in the fit, and the two-arm cells on the common seeds;
- `contrast_fit` with `with_item=False`, and `phi.holm` at 5%;
- its own copies of the plans, the clusters and the pairs (`E2E_PLANS`, `E2E_CLUSTER`, `E2E_PAIRS`).

It shares only these with `run_chunk`:
- the draw layout (`sim.INDEX`, `sim.CELLS`);
- `sim.cell_sd`, which has its own test, and `sim.OPTIONS`, which the [C] output test holds (`doc["families"]`);
- the tally shape.

So it does not compare the code with itself. It compares, exactly, the plans by σ̂_A; per family the familywise count;
per contrast the tested, size and Holm counts; and power and better at 4 and 8 pp. It runs 6 configurations of 40
replicates each.

**Killed by that test alone (M: run_extra2.py with the node restricted; sv2-only.json; baseline 6 passed).** These are
killed in the configuration named:
- `V-sim-plan-by-n`: [B] 4.5;
- `V-sim-claim-on-other-draws`: [B] 4.5;
- `V-sim-claim-fresh-block-a`: [B] 4.5;
- `V-sim-sigma-a-option-ignored`: [C] 5.5;
- `V-sim-sigma-a-full-design-when-stopped`: [B] Llama stopped, 6.0;
- `S-sim-one-sigma-both-families`: [B] ratio 1.5.

My three further wiring mutants are killed by the full suite (M: rv-run.json, below).

**Extended parity through `simulate_row` (M: e2e_row_parity.py → e2e_row_parity_out.txt).** Settings: the committed
settings with 100 replicates, one chunk and scratch seeds 777-781. The independent chain derives each family's true σ
itself, in Fractions. It equals the row on every plan count and on every familywise and Holm count, in all 25 cases:

| Option | Design | Grid σ |
|---|---|---|
| [B] | full | 5.0 |
| [C] | full | 7.0 |
| [B] | Llama stopped | 6.0 |
| [B] | full | 7.0 |
| [B] | both stopped | 3.0 |

Each with all five scenarios. Two checks inside it:
- The cap holds: 7.0 × 1.5 gives Llama 8.24 (M).
- Under [C] the ratio scenarios equal "none" (M).

The code is right; SR1 is the test gap on this path.

## 3. R-11, R-12, R-13 and SV-3 to SV-7

| Item | Where (R) | Evidence | Status |
|---|---|---|---|
| R-11: the familywise rate is the U claims' rate; Φ's O and L words are not simulated, stated as a limit | settings `limits[1]` (:94); `reading_rule.text`; sr2:37-38; reading line sr2:589-594; the header carries `limits` (sr2:565) | M: det smoke summary; test_sr2:253, :263-265 | met; SR9 (text) |
| R-12: two scenarios at ρ = 0, Llama at 3/2 and 2/3 of OLMo's σ, the grid's σ is OLMo's, capped at the top | settings :41-50; `family_sigmas` sr2:456-461; `run_chunk` sr2:468; printed sr2:552-553 | M: det smoke (7.0 × 1.5 → 8.24; 8.24 × 2/3 → 5.493333); parity, all scenarios; S-sim-llama-ratio-ignored, -uncapped and -one-sigma killed | met; SR1 |
| R-12: the 6% rule over all five scenarios | settings `reading_rule.text`, `applies_to`; `summarize` sr2:574-580, :589-594 | M: det smoke `scenarios_read` lists 5 | met; SR2 |
| R-13: engines per role {a0, R, block_a} | blinded_sigma.py:72, :247-248, :278; doc :33-35 | M: attacks (each role, swap, split); S-bs-engine-roles-merged and -a0-r-swapped killed | met; SR8 |
| SV-3 | the R-12 rows; the approximation is listed (settings :90) | as R-12 | closed |
| SV-4: the 1104 boundary | test_blinded_sigma.py:664-691 (split fixture; a0 and R at 1104, R at 1105 carry block A's identity) | M: V-bs-reused-includes-1104 killed (shard 4) | closed |
| SV-5: fullmatch | test :585-589 via `refuses` (==) | M: V-bs-values-after-no-df killed (shard 3) | closed |
| SV-6: parent check, `"xb"` inside the guard | blinded_sigma.py:344-354 | M: attacks; S-bs-out-parent-unchecked killed | closed; SR4 |
| SV-7: refused and non-converged totals printed | sr2:586-588, :598-600 | M: det smoke (both keys present); S-sim-nonconverged-total-zero killed | closed; SR6 |

## 4. No regression

**σ̂_A (M: indep_sigma2.py → indep_sigma2_out.txt).** Two independent methods, run on the current fixture with its
three engine roles:
- the two-way interaction sum of squares in exact rationals, with the lone cells left out;
- additive backfitting in floats, with the lone cells kept.

| Design | σ̂_A (blinded_sigma = independent) | df | Backfit, relative difference |
|---|---|---|---|
| [B] full | 34.93048652522448 | 24 | 0 |
| [C] full | 39.92276494049263 | 12 | 0 |
| [C] stopped | 38.48600836026221 | 6 | 1.8e-16 |
| [B], OLMo-2-7B stopped | 32.52729148512099 | 18 | 2.2e-16 |
| [B], Llama-3.1-8B stopped (split engines, harmful-prompt stop) | 38.01171215074377 | 18 | 1.9e-16 |

The first four equal the first verifier's values.

**S-6.**
- `check_anchor_stop` and the design check are unchanged in the diff (R: fix.diff).
- Its 7 mutants are killed (M: shards 2-8): the record's pin, family, exit code, stop kind, record kind, a stop without
  a record, and a record on a full design.
- The harmful-prompt stop (exit 1) reads on Llama (M: table above).

**S-7.**
- `test_ns_sigma_pool_is_noise_readings_on_the_same_cells` is unchanged (R: fix.diff has no hunk in it).
- The 6 N-stage mutants are killed (M: shards 3-8).

**Determinism and merging (M: determinism.sh → determinism_out.txt).** On a smoke copy (60 replicates, chunk 30, seed
5151, the 9-point grid, all 5 scenarios, [B] full), these give one SHA-256, `2857c1b1…`:
- the unsharded `--out` and its stdout;
- the merge of 9 shards run as 9 processes at once;
- the merge in reverse order.

Also:
- One shard re-run gives the same bytes.
- A merge onto an existing `--out` refuses.

**S-2's bound still applies (R).**
- The diff leaves `claim_test`, `holm`, `p_two_sided` and run_chunk's Holm and familywise lines unchanged (sr2:340-392,
  :476-501). Its hunks touch only `read_settings`, `family_sigmas`, run_chunk's first lines, `simulate_row` and
  `summarize`.
- The familywise event is still any Holm rejection at α = 0.05 over the plan's primary U contrasts, two-sided.
- So the first verifier's argument (R-10) holds: Φ's first U rejection needs p_U ≤ α/K.
- Every design keeps K ≥ 2 (a stopped family under B9 or H has P3 and P6), so Φ's graph exists (R: phi.py:45,
  `build_graph` refuses k < 2).

## 5. Tests and mutants

**Suite (M).** `sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS gives
**268 passed, 57 skipped** (84 s), exit 0. This equals the builder's count.

**The builder's spec (M).** `run_mutants_sr2.py WS <scratch>/mut-K <scratch>/mut-shardK.json SHARD:K/8 --timeout 300`,
under `sandbox-exec`.
- Run times: shards 1-2 at once, 17:23-17:27; shards 3-6 at once, 17:27-17:33; shards 7-8 at once with my two runs,
  17:33-17:37:38.
- Each baseline: exit 0, 60 passed. Each report names spec `e349a6dc…`.
- Results: 10 + 9 + 9 + 9 + 9 + 9 + 9 + 9 = **73 killed, 0 survived, 0 invalid**.
- Every kill names a real FAILED test with 0 ERROR lines (mut-shard1..8.json).

**Runner validity (R: run_mutants_sr2.py).**
- It copies `scripts/scale78b` and links the rest. The baseline runs first, with the same command.
- A kill needs exit 1, a FAILED line and no ERROR line.
- A fixture error (an "ERROR at setup" line) or a collection error is invalid, never a kill.
- A find text must occur exactly once, and the copy is re-hashed after each mutant.
- No test pins either module's own hash: the outputs' `script_sha256` is never compared with a literal (M: `grep`).
- My runner `run_extra2.py` calls the same `prepare`, `run_suite` and `verdict`, unchanged.

**My extra mutants (M: extra_spec_rv.json, rv-run.json; baseline exit 0, 60 passed).**

| Mutant | Verdict | Defect |
|---|---|---|
| RV-sim-run-ignores-family-sigmas | survived | SR1 |
| RV-sim-max-olmo-only | survived | SR2 |
| RV-sim-max-skips-ratio-scenarios | survived | SR2 |
| RV-bs-side-file-repo-root | survived | SR3 |
| RV-bs-out-wb | survived | SR4 |
| RV-sim-threshold-ge | survived (equivalent on the test data) | SR5 |
| RV-sim-refused-total-zero | survived | SR6 |
| RV-sim-n-plan-olmo-only | survived | SR7 |
| RV-bs-engine-keyset-unchecked | survived | SR8 |
| RV-sim-sigma-a-on-other-draws | killed (the SV-2 test, [B] 4.5) | — |
| RV-sim-claim-rows-misindexed | killed (the SV-2 test, [B] 4.5) | — |
| RV-sim-claim-other-family | killed (the SV-2 test, [B] 4.5) | — |

**Weak or equivalent mutants in the spec.**
- I found no equivalent mutant: all 73 are killed by a real failure.
- Weak: `S-sim-llama-ratio-ignored` is killed only through the printed σ (test_sr2:251), not through any rate. That is
  why SR1's mutant, which keeps the print, survives.

**Branches still untested (the first verifier's list, not changed in this round).** These are nits:
- the bars-frozen check;
- the four-digit seed key;
- the method-entry key set;
- `--merge` ignoring `--design` and `--stopped`;
- σ strings not validated.

## 6. The full run's commands (r1-s.md :140-160, with the fix round's E at :414-419)

**They run as written (M: determinism.sh).**
- The commands are `cd <repo>`, then one `$PY -I -B … --sigma $i --out <R>/sr2-B-full-s$i.json > /dev/null` per index
  0-8, then `--merge <R>/sr2-B-full-s{0..8}.json --out <R>/sr2-B-full.json`.
- They work from the repo root under `-I -B`, in zsh. Brace expansion and `--merge … --out` parse.
- The merge equals the unsharded document byte for byte.
- So they can run as one background loop. They can also run as 9 parallel background jobs: the concurrent run gave the
  same bytes.
- A re-run onto an existing `--out` refuses ("written once"), so a retry needs a new name or a deleted partial set. No
  partial file is written: `--out` is written after the row is computed (R: sr2:674-676).

**E runtime (M: timing.txt; a copy with 1,000 replicates in one chunk; scaled × 20).** My own jobs had ended, but
other agents' pytest jobs ran on this Mac at the time (M: `ps` at 17:46). My chunk was also 1,000, not 2,000. So these
numbers may be high.
- [B] at σ 3.0: 57.0 s, so about 19 min per low-σ shard.
- [B] at σ 8.24: 9.8 s, so about 3.3 min.
- [C] at σ 3.0: 23.7 s, so about 8 min.
- My runs took 19-29% longer per replicate than the builder's: 114, 19.6 and 47.4 s per 2,000 replicates, against his
  88.6, 16.5 and 39.3 s.
- So his totals may be 20-30% low (E): [B] full about 95-145 min against his 80-110; [C] about 50-70 min against his
  40-55.
- The low-σ [B] shards exceed 10 minutes, so they must be background jobs, as the builder says.

**The mutation full spec's E in r1-s.md is stale** (:159: "about 5 min").
- 73 mutants on a 60-test suite take about 20-25 min serially (E):
  - the builder's 8 shards ran serially, 16:45-17:05 UTC (r1-s.md :405-406);
  - my shards took 3.0-5.1 min each, two to four at once (M).
- So `ALL` must run as the lead's background job, or as 8 foreground shards of under 6 min each.

## Commands run (exit status)

1. `date -u`: 17:11, 17:15, 17:20, 17:23, 17:27, 17:33, 17:36, 17:41, 17:44, 17:46, 17:48 and 17:50: 0.
2. Reading, all read-only:
   - `cat`, `sed -n`, `grep -n`, `shasum -a 256`, `git status --porcelain`, `diff -u`;
   - r1-common, the rulings (all sets), r1-s-verify.md and its scratch, r1-s.md;
   - the 7 target files and fix.diff;
   - noise_reading.py, gate_b_reading.py :255-470, B16 phi.py :1-70, reading.json's gamma, Part 2 :681-700.
   Exit 0.
3. Suite (§5): 0 (268 passed, 57 skipped).
4. `bs_attacks2.py`: 0. `indep_sigma2.py`: 0 (after `sed -i` set its sweep count to 3,000).
5. Mutation shards SHARD:1/8 to 8/8: 0 each, 73 killed.
6. `run_extra2.py`, SV-2 node only (6 mutants): 0, 6 killed. `run_extra2.py`, full suite, extra spec (12 mutants): 0.
7. `e2e_row_parity.py` × 5: 0 each. `determinism.sh`: 0. The planned refusal (merge onto an existing `--out`): 1, as
   expected.
8. Timing: `timing.sh` (a copy with 1,000 replicates, the grid cut to 3.0 and 8.24): 0, three runs exit 0.
9. One `sleep 60` was refused by the tool; I did not chain sleeps.

Three foreground commands were moved to the background by the tool at 180 s: the parallel mutation batches. I did
other read-only and light work meanwhile. I read results only from my own log files, after each batch finished.

Afterwards I deleted the copied trees (mut-1..8, rv-run, sv2-only) and the synthetic fixtures (attacks/, indep/, det/,
timing/). Kept: the scripts, the specs, the JSON reports and the logs.

## Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| SV-1 closed; no value reaches stdout, stderr, any other file or a refusal (code, CLI) | passed | §1 (M: 20 CLI cases and the race case) |
| The byte test holds the whole output; full-line refusals | passed | §1 (R; M) |
| The blinding test catches a side file anywhere | **failed** | SR3 (M) |
| SV-2 closed: independent chain; four wiring mutants and claim-fresh killed by it | passed | §2 (M: sv2-only.json) |
| R-11, R-12, R-13, SV-3 to SV-7 as ruled (code) | passed | §3 |
| R-12's wiring and the summary's maximum held by tests | **failed** | SR1, SR2 (M) |
| σ̂_A equals an independent exact computation (4 + 1 designs) | passed | §4 (M) |
| S-6, S-7, determinism, shard merging, S-2's bound | passed | §4 (R; M) |
| Suite 268 passed, 57 skipped | passed | M |
| 73 mutants killed; runner valid | passed | M |
| No weak mutants in the new code | **failed** (test gaps only) | SR1-SR8 (M: 9 survivors) |
| The full run's commands run as written, sharded, in background, and merge byte-identically | passed | §6 (M) |

## Open points for the lead

1. **SR1 and SR2 (test-only) in the next round,** before any further edit to `sr2_simulation.py`. Then add the 9
   surviving RV mutants and my 3 killed ones (R/r1-s-reverify-scratch/extra_spec_rv.json, `b536887a…`) to the spec,
   and re-run the spec.
2. **SR9 corrects R-11's wording** ("0.5% of α"). The settings copy that phrase; the lead's rulings file has it too.
   Decide whether the settings take the fix before the full run. A fix after the run would leave the printed limit
   wrong in the governing output.
3. **The anchor-stop record** (JOB-DONE.json SHA-256, ids and counts; the shared fixture with K2's writer) is still
   open, as the builder states.
4. **σ_eval,0 = 1.28 pp** (the 1B value) still sets only N's printed plan.

## Concerns

- My smoke runs printed familywise rates for scratch seeds. I report only equalities and timings. No smoke result is
  an SR-2 reading. The governing values come only from the lead's run on `99410f9f…`, or on the settings after SR9.
- Byte stability holds on this Mac's numpy and BLAS (M). Across machines it is not guaranteed (I; the builder's and the
  first verifier's concern too).
