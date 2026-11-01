# What comes after stage-1 block B (the lead's plan, 31 October 2026)

Revised 1 November 2026 by addendum §39 and §40; the 31 October text is in git at `55d5f8b`.

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
| 1a | **RI-O2, coherent-only U (sensitivity S-G).** A prompt whose 3 sampled answers all fail the coherence screen has no coherent share; B16's table needs one value per prompt and cell. Ruled as post-W1 deviation D-5 (§39 point 1). | D-5: G2's pooled share per cell with the linearized prompt table on all 200 prompts, read by a new reader beside B16 that calls B16's unedited functions (B16 byte-identical); the builder writes per-prompt counts (n, u, u_fail) in a side document bound to `tables.json` (`--coherent-out`, given to the no-value pre-run too); printed: each arm's pooled coherent-only U, G2's counts, S-G coherent's U-part words and headline word under its own Φ run, and both adverse G3a corners; the reader never stops the reading, and its builder half is settled at the pre-run. Built; fix round 1 done; its re-verify decides (no second fix round). Verified = the suites; the 47-entry spec as the lead's background run (0 invalid; every mutant killed except listed expected survivors); an independent reference (estimates to 1e-9 pp; SE and df to 1e-6 relative where the reference fits REML on its own); an unequal-n hand case against exact fractions; the all-n = 3 equality; and the coverage gate on plan A, the reading that runs: every contrast in every world within 90% coverage 0.88–0.92 with a 0.75% tail at most 1.5 × the primary form's, at 2,000 or more replicates per world and also at 10,000 where a world is within 2 Monte Carlo SE (0.0134) of a band edge or its tail ratio is above 1.3; plan B checked and reported; block A only a reported limit (that reading refuses with block B sealed). | (c+): each arm's pooled coherent-only U only, no label re-read; trigger: D-5 not verified after one fix round (the re-verify's verdict). Last: the design's option (c) paragraph, edited as D-5 says; triggers: (c+) not verified when the second stamp's manifest is written, or the builder's no-value pre-run refused only on the coherent-only counts (then (c) is chosen at the pre-run and names that cause). |
| 1b | **B14's similarity pass never ran** (a scheduling gap: planned "on the pod", never scheduled in a block; it runs once, after both blocks and before any stage-1 outcome is read; nothing measured changes; §39). §9.4's overlap control (report only) needs θ0's embeddings of the 200 harm prompts and the 144 added rows; no `similarity.json` or `strata.json` exists. B14's report also refuses recipe-S units as pinned: D-6 (§39 point 2) re-pins its settings before the strata are made. Done at `b5e3c27` (1 Nov): the pass ran on one A100 pod, the strata are sealed in FOCUS and the inputs file is written and checked (§39 point 12). | The $0 Mac pre-check; kit round 34 (one job kind for the pinned `overlap_similarity.py`; built and verified), which leaves every value the reading builder and B14's inputs writer read unchanged (checked by C's verifier, not pinned by a test; §39) and changes `stage1_rules.py` (`4005cb4e…`) and `plan_tool.py` (`27e299b5…`), the runbook's "never changes" list and the second stamp taking the new hashes; one A100 pod from a background job, about $0.60–0.75 (estimate; worst about $2.7–3.1 at its cap), from the balance. Then `overlap_strata.py strata` on the Mac under D-6's settings, run in place on `retrieved/sim-1/…/similarity.json` by the exact path and SHA-256 that `record-done` prints (the one exception to the never-open rule for `retrieved/`; the lead never lists `retrieved/`); a script copies `similarity.json` into the B14 records folder with a SHA-256 check and prints only the hash; the SHA-256 of `similarity.json` and `strata.json` into FOCUS (before any add-arm outcome is read) and the second stamp. D-6 is committed before `strata` runs; the inputs writer runs, then its checker at once. | (i) One re-run (`defer sim-1` to `sim-2`) if the pod crashes, C's verifier's N5 case included (a warning without a trailing newline before the "wrote" line); then a one-off pod with the same command and a written checklist; trigger: round 34 not verified when the other builds are done, or a second crash. (ii) `--no-overlap`: B16 prints "not computed" and the record words §9.4 as D-6's fallback, with this cause; trigger: two pod attempts end without `similarity.json`, or the balance is below $6 + the pod's cap × $1.85. The Mac is not a route: the script refuses non-CUDA devices. |
| 1c | **Every other stated reading** | Addendum §39 confirms each as the lead's ruling before any outcome: the builder's RI-O1 and RI-O5 to RI-O14; the claim reader's R2, R3, R5, R6, R7 and R9; B16's README readings and overlap readings R2–R6; B16-D4-O2, B16-D4-O3 and B16-H-O9; the coherence condition in the best feasible repair; S-tok's wording ("not run": its stage-1c input has not run; B16 prints null) and §9.4's wording under `--no-overlap`; the runbook's readings; the stamps; "report and go on"; the reading-time readers' adopted readings (§39 point 11). Beside it, the S1 blinding record (REV4:919) lists every rule written after the W1 commit, with the Gate B values read before each. | None needed; each point already has a stated reading. |
| 1d | **The reading runbook** | A step list like the judge runbook (drafted): exact commands, the hashes each step must print, the refusals, where each output goes, and what is read by whom, with addendum §39 point 8's readings (stop on identity lines only; D-5's reader and the reading-time readers never stop the reading; the no-value pre-run takes `--coherent-out`; the cost-ledger pre-check). Before the second stamp, as the lead's background jobs on the final tree: the reading-input suite and its 47-entry spec (the builder changes and the D-5 reader), B14's suite and the 69-entry near set of its 150-entry spec (D-6 and the inputs writer; the full spec in the background when the machine allows), kit round 34's suite and mutants, the reading-time readers' suite and spec (62 entries; `cost_table` after its fix round), the D-7 draw script's suite and spec (re-run after D-5's merge), and B16's suite (B16 is unchanged under D-5, so its 117-entry spec need not run again). | All suites, plus near-set mutants within about 40 lines of each change; trigger: a full spec cannot finish before the planned stamp (the runbook's D8). |
| 1e | **The outside time stamp (decided 31 Oct: no OSF posting; an OpenTimestamps stamp instead).** The user: "Yes, time-stamp it". Stamped at 22:54 UTC: `timestamp/ots-manifest-20261031.json` (`68e75447…`; it binds the package zip and members, the six frozen originals checked at their commits, both block seal records, HEAD and the stage-1 code trees) and the package zip (`170361f7…`). **Anchored** in Bitcoin block 974039 (header time 2026-10-31T23:28:48 UTC) and block 974047, checked at two explorers (`timestamp/ots-check-20261101.json`). | Right before the reading, a second stamp of the final reading code (with the D-5 reader and B14 under D-6), the kit files after round 34, the runbook and the reading script, B14's inputs file, `similarity.json` and the strata, the reading-time readers (`reading_extra/`, with `cost_table` after its fix round), the D-7 draw script, and the records (addendum §39 and §40, D-5 to D-7, the S1 blinding record), verified the same way; step 1 starts only when its anchoring block has at least 6 confirmations and 2 h after its header time. Keep the `ots` client until both stamps are verified. A third stamp of the reading's outputs after the records step. Paper wording: "pre-specified" (the frozen rule's no-deposit branch). | If the second stamp does not anchor within 48 h: re-stamp once; if that also fails, the paper keeps "pre-specified in a dated git record" and states that the stamp did not complete. |
| 1f | **LN-15e** (a-2's four re-score units, not pulled) | Keep the recorded FO-04 fallback; no restart of a-2. | Not applicable. After the reading, ask the user whether a-2 can go. |

### The reading itself (in this order; each output sealed and hashed before the next step)

0. 1e's first stamp is anchored (block 974039). Check by exact path that every expected cost ledger exists (existence
   only, no read; a missing ledger makes step 4c's cost table "not computed", report only; §39 point 8(h)). Stamp the
   final reading code (with the D-5 reader and B14 under D-6), the kit files after round 34, the runbook and the
   reading script, B14's inputs file, `similarity.json` and the strata (written and sealed at `b5e3c27`), the
   reading-time readers (`reading_extra/`), the D-7 draw script, and the records (addendum §39 and §40, D-5 to D-7, the
   S1 blinding record), and start step 1 only after that second stamp is anchored, with at least 6 confirmations and
   2 h after its block's header time (§39 point 9).
1. B14 report under D-6's settings: `overlap_strata.py report --strata <sealed strata.json> --inputs <committed B14 inputs file> --out <run folder>/b14` → `overlap_report.json`, after a no-value pre-run whose output must be byte-identical (§39 point 8).
2. Input build: `python -m scripts.stage1_s1.reading_input --reading plan_a --kit tmp/stage1-olmo --b14-strata … --b14-report … --expect-strata-sha256 … --expect-report-sha256 … --out <new folder>/tables.json --record <new folder>/sources.json --hb-out <new folder>/hb_tables.json --coherent-out <new folder>/coherent_counts.json` (D-5's counts document), after a no-value pre-run with the same options, `--no-overlap` in place of the four B14 options. The step-2 comparison with the pre-run leaves out the overlap block and the output hashes bound to `tables.json` (the HarmBench tables' and the counts document's). If the pre-run refuses only on the coherent-only counts, step 2 runs without `--coherent-out` and D-5 goes to its last fallback (c), chosen at the pre-run (§39 point 1, item 8).
3. B16: `python -m scripts.stage1_s1.reading --input tables.json --out reading.json`; its `provenance.input_sha256`
   must equal the builder's printed SHA-256 of `tables.json`; a second run must give a byte-identical file.
4. HarmBench claim reader (`hb_claim.py`, §37): the HB contrasts, E_HB and the "harm" sentence words.
4b. D-5's reader beside B16: S-G's coherent-only U per arm and per contrast, its words and headline word under its
   own Φ run, G2's counts, and both adverse G3a corners. A failure here is logged and never stops the reading.
4c. The reading-time readers (`scripts/stage1_s1/reading_extra/`; §39 point 11): F_k's planning power at the
   measured q (REV4:574), the stage-3 pick (REV4:428), LN-14's bar and LN-19's shares (REV4:554-555, `cap_reports`),
   the S-a shift line (REV4:276) and the cost per arm (REV4:103, `cost_table`), each bound to `reading.json` by
   SHA-256, report only, run only inside the reading script here (`cap_reports` opens the O-ext summaries and
   COMPLETE.json files the builder's record names; `cost_table` opens `plan.json`, the seals and the cost ledgers:
   the never-open list's one explicit exception for these readers). A failure here is logged and never stops the
   reading. A reader not verified before the second stamp runs after the reading, labelled "code written after the
   reading".
5. LN-31's draw for the human label check (prints totals only), by the draw script committed before the second stamp with its frozen protocol, seed tags, term list and inputs by SHA-256 (post-W1 deviation D-7; built and verified), on inputs restored and pinned in `tmp/hlc-inputs/`; its `check` re-runs the draw in a second process and prints "match" or "mismatch" and totals. If it was not committed before the second stamp: "not run at the reading", and the draw follows when the human label check is funded (D-7's fallback).
6. Records: a stage-1 reading record made by the mechanical extractor (labels P1–P6, the headline word, the
   references, the best feasible repair, the sensitivities, with S-G coherent's words copied by key), FOCUS, commit,
   push, backup, then a third stamp of the outputs. Then the lead reports to the user and goes on in the plan's order
   (the user's 31 Oct instruction, `user_instruction_keep_working_20261031.json`; §39 point 10).

## Step 2: after the reading (each starts on money in the account, never on a result)

Costs and dates are the README's (30 Oct) unless marked as my estimate.

| Order | Stage | Cost | Date that matters |
|---|---|---|---|
| 1 | Stage 1b, the planted-cause positive control (addendum §40: pilot block P, 3 runs, from the balance, about $5–6 measured, kit upper $7.43; then 12–15 runs on a top-up) | $17–35 | none |
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

1. Steps 1a (D-5), 1c (§39 and the S1 blinding record), 1d, D-6, D-7 and the reading-time readers (all $0), and 1b (kit round 34, then one pod: about $0.60–0.75, worst about $2.7–3.1 at its cap, from the balance above the $6 reserve; done at `b5e3c27`, about $1.21).
2. The reading itself ($0), after 1a–1d and the anchored stamps of 1e and step 0.
3. $0 preparation of stage 1b (addendum §40): kit round 35 (pilot block P) and the frozen pilot reader, in scratch trees, merged only after the reading's outputs are sealed; K7 built off the pilot's path.
4. $0 preparation of the OLMo 3 probe's three blockers (transformers ≥ 4.57.0, the chat-template download, a new
   preflight script), so it can launch before 13 Nov if the money is there.

The money for stage 1b onwards comes from the balance and the user's top-ups (the 29 Oct rule); the lead alerts the
user below $10.
