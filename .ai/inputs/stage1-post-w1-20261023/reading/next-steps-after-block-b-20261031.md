# What comes after stage-1 block B (the lead's plan, 31 October 2026)

Written by the lead (General Implementation VIII) on 31 October 2026 at 22:14 UTC (clock checked), after the user's
"yes and keep planning whats needed next". This is a plan. It adopts no rule and reads no outcome. Stage-1 outcomes
(U, HB, O, task loss, coherence) stay sealed until the reading in step 1. Sources: `README.md` "Study plan by stage"
(30 Oct), FOCUS, addendum `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` (§24, §33, §37), the input
builder's report `research/experiments/2026-10-27-block-b-prep/reading-input/reading-input-build.json`
(`lead_must_run`, `open_points`), `scripts/stage1_s1/reading/README.md` and `scripts/stage1_s1/overlap_*.py`.

## Where the study is now

- Stage 1 (OLMo-2-1B, plan A, 50 cells): blocks A and B ran, both judges ran on both blocks, both blocks are sealed
  (block A `6c6267c8…`, 27 Oct; block B `b4e11dc9…`, 31 Oct). Measured spend: block A $48.59, block B $144.94.
- Nothing runs. Balance $29.94 at 22:13 UTC; idle charge about $0.04/h (three kept stopped pods, 80 GB: a-2,
  gateb-w0b-2, probe-olmo2-1b-1102, each the only copy of something the plan keeps).
- b-20 and the two block-B judge pods were deleted at 22:09–22:10 UTC on the user's yes (GET EXITED, DELETE 204,
  GET 404 each; `block-b/pod_deletions_block_b_final_20261031.jsonl`).

## Step 1: the stage-1 reading ($0, on the Mac; the next step)

The pre-registration says block B ends with "the judges, the seal and the reading". The reading is the confirmatory
analysis: it unseals the stage-1 outcomes once and computes the six primary contrasts P1–P6, their labels, the
references and the headline word with the frozen code (B16). It is a one-way step: after it, no reading rule can
change without being labelled post hoc. So everything below marked "before" must be done and recorded first.

### Before the reading (preparation; all $0 except 1b)

| Id | What | Default (ambitious) | Pre-set fallback and its trigger |
|---|---|---|---|
| 1a | **RI-O2, coherent-only U (sensitivity S-G).** A prompt whose 3 sampled answers all fail the coherence screen has no coherent share; B16's table needs one value per prompt and cell. Still open (FOCUS 29 Oct). | Option (a): a B16 change that takes per-prompt counts (coherent unsafe, coherent n) and drops such a prompt pairwise, as Gate B's reading does. Built in a scratch tree, tested, mutation-checked, merged, recorded as post-W1 deviation D-5. It changes B16's module hashes, so it must land before the reading. | Option (c): S-G reports the two G3 corners only and says why. Trigger: (a) is not verified (suite and mutants pass) when everything else in this table is done. |
| 1b | **B14's similarity pass never ran.** §9.4's overlap control (report only) needs θ0's embeddings of the 200 harm prompts and the 144 added rows (`overlap_similarity.py`, "on the pod"); no kit job ran it, and no `similarity.json` or `strata.json` exists. The strata must be sealed before any add-arm outcome is read. | One small pod, one job: `overlap_similarity.py` on θ0, about $1 (my estimate: one 1B forward pass per prompt, plus setup), started from the balance. Then `overlap_strata.py strata` on the Mac and the strata's SHA-256 into FOCUS. | (i) The same script on the Mac CPU (float64; "on the pod" becomes a recorded deviation); trigger: the pod fails or the balance is under the reserve. (ii) The reading prints "not computed" for §9.4 (B16's built fallback, §24 point 4); trigger: (i) also fails. |
| 1c | **The builder's other open points** (RI-O1, RI-O5 to RI-O11) | One addendum section (§39) that confirms each stated reading as the lead's ruling, so every reading rule is written down before outcomes. RI-O3: S-tok has no input (stage 1c's R_1200 and R_2400 have not run), so the reading says "not run". | None needed; each point already has a stated reading. |
| 1d | **The reading runbook** | A step list like the judge runbook: exact commands, the hashes each step must print, the refusals, where each output goes, and what is read by whom. Re-run the reading-input and B16 test suites and mutation specs on the current tree first (as the lead's background jobs). | None. |
| 1e | **The OSF registration (the user's own step)** | The user posts the embargoed OSF registration (package ready since 23 Oct, `tmp/osf-deposit-20261023/`) before the reading, so a third-party time stamp comes before the first stage-1 outcome. | Read without it. The paper then says "pre-specified in a dated git record (commit bc79b08)", the wording already planned. Trigger: the user prefers not to post first. |
| 1f | **LN-15e** (a-2's four re-score units, not pulled) | Keep the recorded FO-04 fallback; no restart of a-2. | Not applicable. After the reading, ask the user whether a-2 can go. |

### The reading itself (in this order; each output sealed and hashed before the next step)

1. B14 report: `overlap_strata.py report` from the strata and the sealed a0 and add-arm units → `overlap_report.json`.
2. Input build: `python -m scripts.stage1_s1.reading_input --reading plan_a --kit tmp/stage1-olmo --b14-strata … --b14-report … --expect-strata-sha256 … --expect-report-sha256 … --out <new folder>/tables.json --record <new folder>/sources.json`.
3. B16: `python -m scripts.stage1_s1.reading --input tables.json --out reading.json`; its `provenance.input_sha256`
   must equal the builder's printed SHA-256 of `tables.json`.
4. HarmBench claim reader (`hb_claim.py`, §37): the HB contrasts, E_HB and the "harm" sentence words.
5. LN-31's draw for the human label check (prints totals only).
6. Records: a stage-1 reading record (labels P1–P6, the headline word, the references, the best feasible repair, the
   sensitivities), FOCUS, commit, push, backup. Then the lead stops and reports to the user (the study stops and asks
   after every stage).

## Step 2: after the reading (each starts on money in the account, never on a result)

Costs and dates are the README's (30 Oct) unless marked as my estimate.

| Order | Stage | Cost | Date that matters |
|---|---|---|---|
| 1 | Stage 1b, the planted-cause positive control (pilot 3 runs, then 12–15) | $17–35 | none |
| 2 | Stage 1c, the secondary arms (dose curve, token-matched random, format rules) | $45–80 | none |
| 3 | The human label check (two raters, about 450 answers) | $440–650 | needed for the ICML version |
| 4 | Stage 2, Llama-3.2-1B (Gate A done; Gate B-lite and the primary family) | Gate B-lite $12–67; the primary family about $190–250 (my estimate from stage 1's measured $193.53) | none |
| 5 | OLMo 3 7B probe (option B only) | level 3 about $266–390 | **13 Nov**: if the probe pod has not launched, OLMo 3 goes to level 0 |
| 6 | The 7–8B tier (OLMo-2-7B, Llama-3.1-8B) | A $860–1,170; B $1,180–1,760; C $770–1,160 | **about 20 Nov**: B or C, by the money in the account and the noise reading |
| 7 | Stage 3, confirmation on engine Y (at most two contrasts) | not priced | after the stages it confirms |
| 8 | Alpaca, the second benign data set | not priced | preconditions open (LR rule, design note, download) |
| 9 | OLMo-2-32B headline check | T1 $98, T2 $165, T3 $300 | **1 Dec** go/no-go |
| — | Paper (ICML 2027) | — | results frozen **4 Jan 2027**; deadline about **22 Jan 2027** |

## What the lead can do now without a top-up

1. Steps 1a, 1c and 1d (all $0) and 1b (about $1 from the $29.94 balance, above the $6 reserve).
2. The reading itself ($0), after 1a–1d and the user's answer on 1e.
3. $0 preparation of stage 1b's kit round (the plant and decoy were built on 23 Oct).
4. $0 preparation of the OLMo 3 probe's three blockers (transformers ≥ 4.57.0, the chat-template download, a new
   preflight script), so it can launch before 13 Nov if the money is there.

The money for stage 1b onwards comes from the balance and the user's top-ups (the 29 Oct rule); the lead alerts the
user below $10.
