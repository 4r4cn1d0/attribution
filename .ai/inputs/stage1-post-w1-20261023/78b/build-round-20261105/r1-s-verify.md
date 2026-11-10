# R1 Track S: adversarial verification of `blinded_sigma.py` and the SR-2 simulation

Started 2026-11-08 15:45 UTC. Finished 16:33 UTC. Both times from `date -u`.

- Verifier: Track S's adversarial verifier (read-only on WS).
- Target: B/ws-s at 3481d85 and its 7 new files. The hashes match the builder's "Second set" table (M: `shasum -a 256`, 15:45 and 16:31 UTC): `blinded_sigma.py` `decd49e5…`, `sr2_simulation.py` `65f47270…`, `settings/sr2_simulation.json` `969c84d6…`, `test_blinded_sigma.py` `50456353…`, `test_sr2_simulation.py` `1ecb7b8b…`, `mutation_spec_sr2.json` `0432e8a5…`, `run_mutants_sr2.py` `50594102…`.
- No file in WS changed (M: `git status --porcelain` lists the same 7 untracked files and nothing else).
- The settings file was not run.
- Scratch: R/r1-s-verify-scratch/.
- Tags: M = measured (the command is named), R = read (path:line), E = estimate (the basis is named), I = inference.

## Verdict: DEFECTS

**The code is correct on every check I ran.**
- No U value reached any output channel in any attack (M).
- σ̂_A equals an independent exact computation (M).
- S-2 holds (R, and M on random p-values).
- The simulation's chain equals, replicate by replicate, an independent chain built from the frozen and reference code (M).

**The tests do not hold two things the run depends on:**
- the blinding test misses two leak channels (SV-1);
- no test covers the wiring of the simulation's decisive link (SV-2).

I ran 8 extra mutants on these points. All 8 survived. None of the defects is a blocker for the full run, because the current code is right. SV-1 matters for the "blinding test verified" condition (P2 §10.1; GXB S-1's `PLAN_B_78B`). SV-2 matters for any edit made before the run.

## Defects

| id | severity | file:line | defect | failure scenario | fix |
|---|---|---|---|---|---|
| SV-1 | major | `tests/test_blinded_sigma.py:302-311`, `:273-299` | **The blinding test does not hold every path.**<br>(a) The unexpected-error test checks the SystemExit text and stdout only (`capsys.readouterr().out == ""`, :311). It does not check stderr, and no CLI test exercises this path.<br>(b) The sentinel test scans stdout, stderr and `--out` only. It does not check whether any other file was written.<br>(c) A refusal's stderr is checked by substring and by three number formats (repr, `.4f`, `.6f`). It is not compared with its exact expected line. | A later edit writes the exception text to stderr, for example killtest's `ZeroDivisionError` "Fraction(k, 0)", whose k is a U numerator. Or an edit writes the cells to a side file. The suite stays green.<br>M: mutants `V-bs-exc-text-to-stderr` and `V-bs-side-file` survive (R/r1-s-verify-scratch/extra-run1.json). | Add a CLI test of an unexpected error (for example a tampered summary with 0 sampled answers). Assert that stderr equals the exact one line.<br>Snapshot the fixture root, tmp_path and cwd before and after every CLI run. Assert that the only new file is `--out` on success, and that there is none on a refusal.<br>Assert that each refusal's stderr equals its expected line in full.<br>Add both mutants to the spec. |
| SV-2 | major | `sr2_simulation.py:458-471` (`run_chunk`), `tests/test_sr2_simulation.py` | **No test checks the chain inside `run_chunk`.** The chain is: σ̂_A on the option's families and design, then block B's plan, then the claim test on the same draws. The pieces are tested one at a time; their wiring is not. Four wiring mutants survive (M):<br>- `V-sim-plan-by-n`: the plan comes from N, not σ̂_A;<br>- `V-sim-claim-on-other-draws`: the claim test reads another replicate's cells;<br>- `V-sim-sigma-a-option-ignored`: σ̂_A pools both families under [C];<br>- `V-sim-sigma-a-full-design-when-stopped`: σ̂_A uses the full design when a family is stopped.<br>(extra-run1.json, extra-run2.json) | An edit that separates σ̂_A from the claim test's cells removes the SR-2 selection effect. The simulated familywise rate then falls toward nominal, so SR-2 looks safer than it is, and the suite stays green.<br>The code today is right (M: the per-replicate parity in §4). | Add a per-replicate integration test in the form of R/r1-s-verify-scratch/e2e_parity.py. It compares `run_chunk`'s tallies with an independent chain: `blinded_sigma.pooled_sigma`, `noise_reading.seed_rule`, B16 `fit_cells` with multi-start and the 1101 cells in the fit, `contrast_fit`, and `phi.holm`.<br>Run it on [B] full, [C] full, [B] reduced and [C] reduced, at σ values that spread the plans.<br>Add the four mutants. |
| SV-3 | minor | `sr2_simulation.py:457`; settings `approximations` | **Both families get one true σ_pair under [B], and this is not listed as an approximation.** P1 §3.6 (N2) expects the families to differ: about 4.4 pp for OLMo-2-7B and 0.7 pp for Llama-3.1-8B at the 1B pairing ratio. | Under [B], one pooled σ̂_A sets the plan. Unequal σ changes how strongly the plan tracks each family's own residuals.<br>E (smoke probe, 4,000 replicates, common random numbers, `unequal_sigma.py`), shift of OLMo-2-7B's rate against equal σ:<br>- +0.2 pp at a Llama/OLMo σ ratio of 0.5 and +0.3 pp at 0.01, with σ_O = 5.0;<br>- −0.5 pp at ratios 0.5 and 0.2, with σ_O = 6.4.<br>So the bias is small but can go either way. | List it as an approximation. Then either add family-ratio rows (σ_L/σ_O ∈ {1, 0.5, 0.25}), or read [C]'s run beside [B]'s.<br>I: as σ_L → 0, OLMo under [B] equals OLMo under [C] at σ_O/√2, because every quantity is scale-invariant apart from the 0.01 pp² floor. |
| SV-4 | minor | `blinded_sigma.py:76`, `:277`; `tests/test_blinded_sigma.py:584-593` | **The boundary between the `reused` and `block_a` engine roles at seed 1104 is untested.** M: mutant `V-bs-reused-includes-1104` survives. | a0@1104 and R@1104 would be checked against the reused identity. If block A runs on Y and the reused units ran on X, the legitimate block-A cells are refused, or a wrong-engine cell is accepted. | Add a fixture in which block_a ≠ reused and a0 and R at 1104 carry block A's identity. Assert that they pass, and that they refuse with the reused identity. |
| SV-5 | nit | `tests/test_blinded_sigma.py:506-510` | **The no-df refusal is held only by an anchored prefix regex.** M: `V-bs-values-after-no-df` (values appended at the end of the message) survives. | No live leak: `read()` cannot reach this refusal, because both designs have at least 2 df per cluster (M: 6/6 and 2/4). | Use `fullmatch` on the whole message. |
| SV-6 | nit | `blinded_sigma.py:341-352` | **`--out` is weakly guarded.**<br>- Its existence is checked before the read (a race window).<br>- Its parent folder is not checked.<br>- The write is outside the guarded block. | A missing parent folder gives a full Python traceback after σ̂_A is computed. It shows the path only, no value (M: `bs_attacks.py`, case out-dir-missing), and nothing is written. | Check the parent folder first. Open the file with `"xb"` (exclusive create) inside the guard. |
| SV-7 | nit | `sr2_simulation.py:383-387` | **A refused contrast counts as p = 1 (not rejected).** B16 instead refuses the whole reading (`contrast.py` `_assemble`: "no finite degrees of freedom"). | The familywise rate is understated by at most `refused_contrasts` / reps. M: 0 in the verifier's 2,800 parity replicates. | Print the total refused and non-converged counts in `summary`, beside the largest rate. The lead checks them. |

## 1. Blinding (the hard trigger)

**Output form.**
- `render` refuses any key set other than the five (R: blinded_sigma.py:329-332).
- `main` re-raises SystemExit and reports any other exception by its type only, `from None` (R: :341-349).
- The byte test holds the whole stdout, the `--out` bytes and an empty stderr on the success path (R: test :252-270).
- The fixture's literal value is 34.93048652522448 on 24 df. My independent two-way computation gives the same digits (§2).

**The frozen readers' SystemExit texts (R).** I read every SystemExit and refuse text that can fire while units or U are read:
- `noise_reading.read_unit`: :154-268;
- `gate_b_reading` `refuse`, `read_json`, `arm_from_unit`: :259-260, :281-285, :433-454;
- `family_probe_reading` `_pairs`, `sealed`, `counts`: :120-151, :367-390;
- `killtest_stage0_reading.unit`: :38-61.

None of these texts holds a U value, count or share. Each names a unit or folder, a file name, or a count of files. The non-SystemExit errors in these readers can carry data (`Fraction(k, 0)`; `Invalid literal for Fraction: '…'`). blinded_sigma swallows them to their type name.

**CLI attacks (M: R/r1-s-verify-scratch/bs_attacks.py, on the builder's own fixture helpers).** Each case tampers one cell (olmo2-7b S1@1103), re-seals it, and scans stdout, stderr and every new file. The scan looks for the test's sentinels plus "Fraction(k, 0)", "k/60" and "'k'" for every planted count. Exit status was 1 in every case.

| Case | stderr | Planted values found | New files |
|---|---|---|---|
| zero sampled answers | type-only line (ZeroDivisionError) | none | none |
| a string count | type-only line (TypeError) | none | none |
| a malformed `repetition_4gram` | type-only line (ValueError) | none | none |
| a guard row without `prompt_id` | the frozen reader's line "sampled: the answers and their guard records do not line up" | none | none |
| `--out` in a missing folder | a traceback with the path only | none | none |

**Conclusion.** I found no reachable path on which a value leaks. The remaining weakness is in the tests (SV-1, SV-5), not in the code.

**Other channels considered.**
- Warnings: on the success path stderr is "" (the byte test).
- Tracebacks: Python does not print local variables in a traceback.
- `__context__`: `from None` hides the context in printed tracebacks. Only an in-process caller that reads `exc.__context__` would see the original text; the CLI cannot (I).
- Partial write: only the allowed bytes are written.

## 2. σ̂_A's estimate

**Model.** Per cluster the additive arm + seed model is fitted exactly in rationals, and df = n − rank (R: blinded_sigma.py:156-180). Then σ̂_A = √2 × √(ΣRSS/Σdf) over the clusters and families (R: :183-193). This matches P1 §6.4, P2 §10.2 and plan-ab item 9.

**Design and options.**
- Design: full-corpus {a0@1101-1104, S1/S3/S4@1102-1104} and removal {R@1101-1105, A1/L1/H1@1102-1104} (R: :73-78, :116-132).
- Lone cells (R@1101, R@1105, a0@1101) have leverage 1, so they add no df and no RSS (R: test :361-372).
- Under [B] both families are read; under [C] OLMo-2-7B alone (R: :72; P1 §8 "F1, OLMo-2-7B").

**Independent check (M: R/r1-s-verify-scratch/indep_sigma.py).** It uses the two-way interaction sum of squares of each complete 3-seed table in exact rationals, on the fixture's planted counts. It equals `blinded_sigma.read` digit for digit on four designs:

| Design | σ̂_A | df |
|---|---|---|
| [B] full | 34.93048652522448 | 24 |
| [C] full | 39.92276494049263 | 12 |
| [C] stopped | 38.48600836026221 | 6 |
| [B] with one family stopped | 32.52729148512099 | 18 |

So the df are 12 per family on the full design and 6 on a stopped family (2 removal + 4 full-corpus), as specified.

**S-6.**
- The cells given must equal the design's cells exactly; any extra or missing cell refuses (R: :258-270).
- An `anchor_stopped` design drops exactly A1, L1 and S3 (R: :78).
- It needs `anchor_stop` {path, sha256}. The record is read by path and its pinned SHA-256, then checked for kind `scale-78b anchor stop`, the family, and the stop kind with its exit code {safe_anchors_below_64: 3, harmful_prompt_does_not_encode: 1} (R: :218-235).
- A full-design family that names a record refuses (R: :256-257).
- Each check has a test and a killed mutant (M: shards 1-6).
- Not checked: the record's JOB-DONE.json SHA-256, ids and counts (the builder's open point). The shared fixture with K2's writer named in the fourth set does not exist yet.

**Note.** P1 §6.3's 30-df columns for the re-check assume about 15 df per family. The build gives 12 per family (24 under [B], 12 under [C]). That is P2 §10.2's "about 12-15" at its low end. This is informational for the text; the simulation uses the true df.

## 3. S-2, decisive: does Φ's claim need the U contrast to pass Holm? **Yes. The bound holds** for the U claims.

**What the claim needs (R).**
- A contrast's U words come from `labels.u_part(("U", name) in rejected, …)` (R: `scripts/stage1_s1/reading/reading.py:237-242`).
- "better" requires `rejected and est >= delta`, and "worse (U)" requires `rejected and est < 0` (R: `labels.py:62-69`).
- The headline uses them (R: `labels.py:120-145`).
- U_k's p-value is two-sided (R: `reading.py:135`), as in the simulation.
- So a U claim needs Φ to reject the node ("U", k).

**Why Φ cannot reject a U node unless Holm's first step does (R).**
- Start weights: U_k (1−γ)/K, O_k and L_k γ/(2K), F_k 0, with γ = 1/10 (R: `phi.py:5-7`, `:47-66`; `settings/reading.json:232-245`).
- Edges out of O_k and L_k go only to their own L_k, O_k and U_k. F_k gets weight only from U_k (R: `phi.py:56-66`; update rule `:92-104`).
- So before any U node is rejected, contrast k's group {U_k, O_k, L_k, F_k} holds total weight 1/K, and no weight enters it from outside. U_k's local level is then at most α/K.
- So Φ's first U rejection needs some p_U ≤ α/K (× (1 + 1e-12), R: `phi.py:132`). That is Holm-on-U's first step at α (R: `phi.py:142-152`; sr2 `holm`).
- Therefore, under the global U null, P(Φ rejects any U node) ≤ P(Holm on U rejects any), for the same p-values.

**Numerical check (M: R/r1-s-verify-scratch/s2_phi_check.py, B16's `phi.run` unchanged).** 12,000 trials at K = 6, 3 and 2. The p-values were random, with adversarial O, L and F p-values at 0 so that those nodes reject first.
- Φ rejected a U node in 4,229 trials.
- Φ rejected a U node while Holm-on-U rejected none in 0 trials.
- Φ's U rejections were not a subset of Holm's in 0 trials.
- The largest level of a first U rejection was exactly α/K, reached when O_k and L_k were rejected first.

**Limits.** These are not blockers; they go to the lead.
- (a) The bound covers Φ's U claims only. The adverse words "worse (O)" and "worse (L)" (R: `labels.py:126-130`) come from O_k or L_k rejections without U. Those nodes start at γα = 0.5% in all. SR-2's selection can inflate them only through any seed-level correlation of O or L noise with U's residuals (I). They are not simulated.
- (b) The bound needs the 7-8B reading wrapper (P2 §16.3, unbuilt) to keep Φ's structure: O_k and L_k route only within contrast k, and each contrast's group starts at weight 1/K. The wrapper's tests should check this.
- (c) The p-values must be the same as the real ones, apart from S-3's prompt part (§4).

So S-2's condition passes, and the simulation does not need Φ's U part.

## 4. The simulation's fidelity (P2 §10.3)

**Chain: end-to-end parity (M: R/r1-s-verify-scratch/e2e_parity.py; output e2e_parity_out.txt).** For each replicate I rebuilt the chain from other code:
1. σ̂_A by `blinded_sigma.pooled_sigma` (exact rationals);
2. the plan by `noise_reading.seed_rule` (thresholds 4.5 and 6.0 on squares, and the review ceiling through MDE_FACTOR);
3. per family, B16's `fit_cells` with multi-start, the lone 1101 cells in the fit and the two-arm sum rule, then `contrast_fit` (with_item=False) and `phi.holm` at 5%.

I compared this with `run_chunk` on the same synthetic normals (a scratch seed, not the settings' seed). It is equal on every count (plan shares, familywise count per family, Holm count per contrast) in all 5 configurations:

| Option | Design | σ | ρ | Replicates |
|---|---|---|---|---|
| [B] | full | 4.5 | 0.5 | 600 |
| [B] | reduced, Llama stopped | 6.0 | 1 | 600 |
| [C] | reduced | 8.24 | 1 | 600 |
| [B] | full | 5.5 | 0 | 600 |
| [B] | reduced, both stopped | 4.5 | 0 | 400 |

No contrast was refused, in either chain. These counts come from a smoke check of the code; they are not the SR-2 reading.

**N and S-7.**
- N's plan is computed and printed, never used (R: sr2:458-462). This is right: block A is the same for every plan (P1 §6.4). So N's floor and its Gaussian prompt noise cannot move the familywise rate.
- `sigma_pool_sq` is noise_reading's `pooled` formula: max(√[(2SD(r_O)²+2SD(r_L)²)/4], the mean of the two middle pair SEs), on the same prompt-clustered SE (R: sr2:419-436; noise_reading.py:369-384; gate_b_reading.py:363-371, :457-472).
- The agreement test feeds the frozen `GB.Reader`'s `sdr2` and pair SE² into the real `nr.pooled`, both with and without the floor governing. The `_exact` block it builds is the same expression as `family_reading`'s (R: test_sr2:347-377; noise_reading.py:359-360).
- σ̂_A takes no floor (S-7).

**S-1.**
- The scenarios are none, ρ 0.5 and ρ 1, as a variance share on method cells: SD = √(1+ρ)σ_e (R: sr2:397-400; settings `interaction`).
- The summary takes the largest rate over every σ, scenario and family, and prints the rule's text, including "with or without the interaction" (R: sr2:555-580).

**S-5 and the reduced design.**
- On a stopped family, plan A tests P3, P4 and P6, and B9 and H (b) test P3 and P6 (R: sr2:194-220; M: test and parity).
- `--design reduced --stopped F` drops A1, L1 and S3 from both σ̂_A and the claim test, and refuses inconsistent flags (R: sr2:587-597).

**Determinism (M).**
- On a [C] reduced smoke copy (80 replicates, seed 5150), the unsharded stdout, its `--out` file and a merge of the shards {2} and {1,0} are byte-identical (SHA-256 `82f2e525…`).
- Merging the same shard twice refuses: "the rows do not cover the settings' σ grid exactly once".

**Approximations: could any one bias the familywise rate downward?**
- **Holm on U as a bound on Φ:** valid (§3). It is conservative for Φ's U part, because Φ's U nodes start at 0.9α.
- **Seed effects set to 0:** exact. Every quantity is invariant to within-cluster seed shifts (R: test_sr2:169-187). The cross-cluster seed component reaches only N's printed plan.
- **The prompt (item) part omitted (S-3):** small.
  - E: with no true prompt × arm effect, V_item ≈ max(0, MS_P − MS_E)/(PJ). Here MS_P/(PJ) ≈ σ_eval,0²/J ≈ 0.27 pp² at J = 6, and it fluctuates by about √(2/(P−1)) ≈ 10% of that. Against V_seed ≈ σ_pair²/J ≈ 3.4 pp² at σ_pair 4.5, V_item is under 1%, and the Satterthwaite df rise by about 1-2%. The size changes by much less than 0.1 pp.
  - I: a true prompt × arm effect is constant over seeds, so it is part of the arm mean. σ̂_A removes it, and the selection does not touch it. Including it would dilute the selection effect, not raise it.
- **Equal σ for the two families:** not listed (SV-3). The shift is ±0.5 pp at most in the probes (E).
- **The interaction's shape:** listed as this file's choice; S-1 ruled it. E (`arm_shape.py`, 4,000 replicates, [C], σ 4.0), against the settings' form:
  - the same extra variance concentrated on A1 and S3 (share 3) gave +0.3 pp;
  - a0 and R noisier (share 1) gave −0.1 pp;
  - this is near the Monte Carlo noise.
- **H read as H (b) with its money covered:** S-4 confirmed. The money fallbacks drop tests (P1 §7 (i)-(ii)), so they can only lower a family's rate (I).
- **A refused contrast read as not rejected:** bounded by the printed refused count (SV-7).
- **Non-converged fits:** kept, as B16 keeps them, and printed.

**The grid** (3.0 to 8.24 in 0.5-pp steps up to 6.0, then 7.0 and 8.24) brackets both thresholds. The rate cannot peak above 8.24, because review fires more often there and tests nothing (I).

## 5. Tests and mutants

**Suite (M).** `sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS gives **259 passed, 57 skipped** (74 s), exit 0. This equals the builder's count.

**The builder's spec (M).** `sandbox-exec -p "$SB" $PY -B scripts/scale78b/tests/run_mutants_sr2.py WS R/r1-s-verify-scratch/mut-K R/r1-s-verify-scratch/mut-shardK.json SHARD:K/6 --timeout 300` for K = 1..6, one at a time, 16:15-16:25 UTC, each under 2.1 min.
- Each baseline: exit 0, 51 passed.
- Results: 10 + 10 + 10 + 10 + 9 + 9 = **58 killed**, 0 survived, 0 invalid. Spec `0432e8a5…` in each report.
- Every kill names a real failed test (listed per mutant in mut-shard1..6.json).
- Runner validity:
  - it copies scripts/scale78b and links the rest;
  - the baseline runs first, with the same command;
  - a kill needs exit 1 with a FAILED line and no ERROR line;
  - anything else is invalid;
  - the copy is restored and re-hashed after each mutant.
- No test pins either module's own hash, so no mutant is killed trivially.

**The verifier's extra mutants (M).** `run_extra.py` uses the builder's own runner functions, unchanged: the same tree copy, the same pytest command and the same kill rule. Spec: extra_mutants.json and extra_mutants2.json. Both baselines: exit 0, 51 passed. **All 8 survived:**

| Mutant | Defect |
|---|---|
| `V-bs-exc-text-to-stderr` | SV-1 |
| `V-bs-side-file` | SV-1 |
| `V-bs-values-after-no-df` | SV-5 |
| `V-bs-reused-includes-1104` | SV-4 |
| `V-sim-plan-by-n` | SV-2 |
| `V-sim-claim-on-other-draws` | SV-2 |
| `V-sim-sigma-a-option-ignored` | SV-2 |
| `V-sim-sigma-a-full-design-when-stopped` | SV-2 |

**Untested branches seen (R).** These are minor; they are not in the defects table.
- blinded_sigma's check that the bars file is frozen (:311-314);
- the four-digit seed-key check (:264-266);
- the method-entry key set (:283-285);
- the "unit has no sampled answer" refusal (:322-323). It cannot fire: KT's `Fraction(k, 0)` or the frozen parity refusal fires first (M: zero-answers attack).
- In sr2, `--merge` silently ignores `--design` and `--stopped`, and the settings check does not validate the σ strings.

**Commands for the lead (unchanged from the builder's report).**
- The full spec runs with `$PY -B scripts/scale78b/tests/run_mutants_sr2.py <repo> <new scratch> <out.json> ALL --timeout 300` under `sandbox-exec -p "$SB"` (E: about 9 min, from the 6 shards' 1.3-2.1 min each).
- After SV-1 and SV-2 are fixed, add the 8 extra mutants to the spec.

## Commands run (exit status)

1. `date -u` (15:45, 16:14, 16:25, 16:31 UTC): 0.
2. Reading: `cat`, `sed -n`, `grep -n` and `shasum -a 256` over r1-common, plan-ab, the ab-build rulings, P1 §3-§8, P2 §2.2, §4.1, §10, §16, AM1, DES (K4-K9, third set), the 7 target files, noise_reading.py, gate_b_reading.py, family_probe_reading.py, killtest_stage0_reading.py, B16's phi.py, reading.py, labels.py, contrast.py, reml.py and the `phi`/`reml` keys of settings/reading.json, plus edits.py and the stage-1 edit writers' provenance lines: 0.
3. Suite (the command in §5): 0 (259 passed, 57 skipped).
4. `s2_phi_check.py` (WS, -B): 0.
5. `e2e_parity.py` × 6 (the first loop failed in its JSON pipe because zsh does not split words; it was re-run with `${=args}`): 0 each.
6. `unequal_sigma.py` (σ_O 5.0, then 6.4): 0. `arm_shape.py` (σ 4.0): 0.
7. `run_extra.py` with 6 mutants: 0. The tool moved it to the background at 180 s; it completed (exit 0) before I read its report. Then `run_extra.py` with 2 mutants: 0.
8. `bs_attacks.py`: 0. `indep_sigma.py`: 0. A one-off `bs.read` comparison on three designs: 0.
9. Determinism smoke ([C] reduced, 80 replicates; 3 runs and 1 merge): 0. The duplicate merge: 1, as expected.
10. Mutation shards SHARD:1/6 to SHARD:6/6: 0 each.
11. `git status --porcelain` and `shasum` at the end: 0.

Afterwards I deleted the copied trees (mut-1..6, extra-run1..2) and the synthetic fixtures (attacks/fx, fx2, det).

## Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Only the five keys are printed; no U, cell, arm-mean or residual value reaches any output on any path (code) | passed | §1 (M: attacks; R: frozen texts) |
| The blinding test holds the whole output on every path | **failed** | SV-1 (M: 2 surviving mutants) |
| σ̂_A's algebra, df, lone cells, [B]/[C] | passed | §2 (M: exact independent match on 4 designs) |
| S-6: only A1, L1, S3 may be absent, with the record checked by pin, kind, family, stop kind and exit code | passed | §2 (R; M: killed mutants) |
| S-2: the U-only Holm rate bounds Φ's U claims | passed | §3 (R; M) |
| Fidelity: chain, S-7, S-1, S-5, reduced flag, determinism | passed (code) | §4 (M: parity in 5 configurations; byte checks) |
| Every approximation listed honestly | passed with one omission | SV-3 |
| Suite 259 passed, 57 skipped | passed | M |
| 58 mutants killed, runner valid | passed | M |
| No weak mutants or untested branches | **failed** | SV-2, SV-4, SV-5 (M: 8 surviving) |

## Open points for the lead

1. **S-2's scope.** The bound covers Φ's U claims. Φ's O and L nodes, which give "worse (O/L)", are not simulated. They start at γα = 0.5% in all, and SR-2 can inflate them only through a correlation of O or L noise with U's residuals (I). Rule whether the reading rule's "familywise rate" means the U claims, as P2 §10.3's words say.
2. **The 7-8B reading wrapper** (P2 §16.3, unbuilt) must keep Φ's structure for the bound to hold (§3 (b)). Add a test there.
3. **blinded_sigma takes one `reused` code identity** for a0 and R at 1101-1103, while noise_reading takes a0 and R apart. This holds if N's R units carry the side units' `472fc7f6…` (P1 §2.1-§2.2 condition 1). Otherwise blinded_sigma refuses (fail-closed). K2 confirms.
4. **The anchor-stop record.** Its JOB-DONE.json SHA-256, ids and counts are not checked, and the shared fixture with K2's writer named in the fourth set does not exist yet (the builder's open point).
5. **SV-3:** decide between family-ratio rows and reading [C]'s run beside [B]'s before the full run. The settings file is new and unrun, so a change now costs no pre-registration.
6. **Part 2's text:** P1 §6.3's 30-df re-check columns assume 15 df per family; the build has 12.

## Concerns

- My smoke probes printed familywise rates for scratch seeds and settings copies (R/r1-s-verify-scratch/*.json). I report only their differences, as bounds on approximations. They are not the SR-2 reading. The governing values come only from the lead's full run on `969c84d6…`.
- On this machine's numpy, byte stability is per environment (the builder's concern; I agree, I).
