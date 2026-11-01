# Stage-1 reading: the runbook (final; plan item 1d)

Written 1 November 2026, finished about 15:46 UTC (clock checked with `date -u` at 15:21:00, 15:28:15, 15:32:29,
15:41:23 and 15:44:00 UTC); revised in fix round 1 after the verifier's report `runbook-verify1.md`, finished about
16:40 UTC (clock checked at 16:22:54, 16:34:53-16:36:05 and 16:37:14 UTC; check the clock again before you copy any
time). Author: a builder worker for the main-study lead (GI VIII); the launcher records the model. It replaces the
draft R1D (`1d-reading-runbook-draft.md`, SHA-256 `9ae23f5e…`, committed under `lead-reports-20261101/design-round/`).
It adopts no rule and reads no outcome. The script it describes is `reading.zsh`, beside this file; section 9 lists
every change from R1D with its source (changes 21-28 are the fix round's).

What I did not do: no reading, builder, overlap, HarmBench-claim, judge, seal, kit, draw or launch command on real
data or the real kit state; no test suite or mutation spec; no network, install, pod or API call; no edit of any
checkout and no git write. I did not open, list or hash anything under `tmp/stage1-olmo/{hosts,judges,
judges-pending,seals,retrieved}`, `tmp/judge-pod*`, `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`,
`tmp/hlc-inputs/`, `.ai/inputs/stage1-post-w1-20261023/block-a|block-b/`, `tmp/stage1-olmo/plan.json`, the
similarity, strata or B14 inputs files, or any unit, eval, answer, label, cache or COMPLETE.json file. Section 8
lists what I ran. The script ran end to end only on a synthetic world (the verifier's dry run, runbook-verify1.md
§3, and the fix round's three runs, section 8); never on real data.

Paths are under the main checkout, `ROOT=/Users/spiderishi/Coding/attribution`. Citations are `path:line` at commit
`55d5f8b` (`git show 55d5f8b:<path>`), as the records cite; FOCUS lines are 55d5f8b's. Short names: **plan** =
`.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md`; **addendum** =
`.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md`; **rev4** =
`research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md`; **RIB** =
`research/experiments/2026-10-27-block-b-prep/reading-input/reading-input-build.json`; **HBB** =
`research/experiments/2026-10-27-block-b-prep/hb-reader/hb-reader-build.json`; **JRB** =
`tmp/gi-viii-notes/judge-runbook-block-b.md`; **HLC** =
`research/review/2026-10-17-stage2-design-notes/second-rater-and-human-label-check.md`; **TS** =
`.ai/inputs/stage1-post-w1-20261023/reading/timestamp/`; **RD** = `.ai/inputs/stage1-post-w1-20261023/reading/`;
**LR** = the lead's rulings `RD/lead-rulings-20261101.md` (R1-R6); **R1D** = the draft runbook; **ACB, BBB, CKB,
D1B, D2B** = the build reports of tracks A, B, C, D1 and D2 (`A-coherent-build.md`, `B-b14-build.md`,
`C-kit34-build.md`, `D1-readers-build.md`, `D2-ln31-build.md`, each with its fix sections); **ACV2, D1V3, D2V2** =
`A-coherent-verify2.md`, `D1-readers-verify3.md`, `D2-ln31-verify2.md`; **E-D5-D6, E-39, E-misc, E-plan** = the
record drafts `E-D5-D6.md`, `E-39.md`, `E-misc.md`, `E-plan-updates.md`; **B16/**, **RI/**, **RX/**, **HD/** =
`scripts/stage1_s1/reading/`, `…/reading_input/`, `…/reading_extra/`, `…/hlc_draw/`.

Labels, as in JRB:13-14: **M** = measured here by a command (section 8); **R** = read in a source; **E** =
estimate; **I** = inference from M and R facts. Fill markers, for values known only later:

| Marker | Value | Who fills it, when |
|---|---|---|
| `[FILL-COMMIT]` | the commit of the merged code (tracks A, D1 and D2 into the main checkout; B and C are in `53f746d`) | the lead, after the merge |
| `[FILL-SIM-PATH]`, `[FILL-SIM-SHA256]` | `similarity.json`'s path under `tmp/stage1-olmo/retrieved/sim-1/…` and its SHA-256, exactly as `record-done sim-1` printed them, and the SHA-256 of the copy `RD/b14/similarity.json` | the lead, from FOCUS |
| `[FILL-STRATA-SHA256]` | the SHA-256 of `RD/b14/strata/strata.json`, exactly as FOCUS records it (addendum:375) | the lead, from FOCUS; also `STRATA_SHA` in the script |
| `[FILL-B14IN-SHA256]` | the SHA-256 of `RD/b14/inputs/overlap_inputs.json` (the checker's "same bytes" line) | the lead, from FOCUS |
| `[FILL-STAMP]` | the second stamp's date label `STAMP` (for example `20261102`): `STAMP` in Block R, in section 3 (`checks-$STAMP`) and in the script's settings block | the lead, before the commit of step 0.6 (the stamp binds the filled files) |
| `[FILL-S1-RECORD]` | the committed path of the S1 blinding record (proposed `RD/s1-blinding-record-<date>.md`) | the lead, at the records commit |
| never filled here | the SHA-256 of this runbook and of the script, the manifest's SHA-256, its anchor (height, block hash, root, header time) | nobody: they exist only after the commit and the anchor, and an edit of a pinned file after step 0.6 makes R0 stop (S1). The manifest holds the two files' SHA-256; FOCUS and `TS/ots-check-reading-$STAMP.json` (step 0.3) hold the manifest's SHA-256 and the anchor; the third stamp's manifest (step 6 item 4) binds them all |

R1D's `[FILL-0]` ("at step 0", R1D:28) mixed these two kinds; the verifier's D1 (runbook-verify1.md §2) split them.

## 0. Read first: where R1D's gaps stand

| # | R1D's gap | State now (M unless marked) | What this runbook does |
|---|---|---|---|
| RB1 | B14's `report` refused every stage-1 kit unit (recipe S) | **Closed.** D-6 re-pins B14's settings: `report.identity` drops the recipe, `refused_recipes` = G and B+Qi (BBB:11, :52-57); verified (LR R2); merged in `53f746d`. `overlap_strata.py` `4249b070…`, `settings/overlap_strata.json` `92c3a4a0…` | Section 2 pins the new hashes; the stop rules name D-6's fallback (`--no-overlap`) |
| RB2 | No writer for B14's inputs file | **Closed.** `scripts/stage1_s1/overlap_inputs.py` (hash-only writer) and `overlap_inputs_check.py` (a second computation by other code, standard library only) replace step 0.4's heredoc (BBB:76-131, :238-252; LR R2.3). The lead ran both: `RD/b14/inputs/overlap_inputs.json` is committed (`b5e3c27`; names only, M) | Step 0.4 records the two commands; the file's SHA-256 is `[FILL-B14IN-SHA256]` |
| RB3 | The plan's step 2 lacked `--hb-out` | Closed in R1D | Step 2 keeps `--hb-out` |
| RB4 | LN-31's draw script did not exist | **Closed.** `scripts/stage1_s1/hlc_draw/` (D2B:43-56, fix round 12.7); verified (D2V2:13; LR R5). Recorded as post-W1 deviation D-7 (E-misc B; LR R5.4) | Step 5 runs `draw`, then `check` (LR R5.5): inputs `tmp/hlc-inputs/oct9/key.json` and `tmp/hlc-inputs/prepared-v3-inj05`; `mkdir -p $RUN/hlc` |
| RB5 | 1a (RI-O2) was open | **Closed.** D-5: the builder's `--coherent-out`, `coherent.py` and the reader `sg_coherent.py` beside B16; B16 byte-identical (ACB:16-31; fix round F.0-F.5). **D-5 is verified** (ACV2 §0, "verified (no defect)"; the lead's 47-entry spec run is part of "verified", LR R1.2(c)) | Step 2 and the pre-run R1b take `--coherent-out`; step 4b runs `sg_coherent`; the step-2 comparison leaves out the counts document's hashes (LR R6.1) |
| RB6 | 1b was open: no `similarity.json`, no `strata.json` | **Closed.** Kit round 34 (CKB; verified, LR R3) ran the pass on pod `sim-1`; the strata are sealed and committed under `RD/b14/` (`b5e3c27`; names only, M) | `STRATA=$RD/b14/strata/strata.json`; `[FILL-STRATA-SHA256]`; `retrieved/` is read only by the exact path `record-done` printed and never listed (LR R3.1) |
| RB7 | Report-only outputs with no code | **Closed for five.** `scripts/stage1_s1/reading_extra/`: `fk_power`, `stage3_pick`, `cap_reports`, `sa_shift`, `cost_table` (D1B:17-25); the first four verified (LR R4.1); **`cost_table` verified after fix round 2** (D1V3, "verified (no defect)") | Step 4c runs the five, report only, inside the script (LR R4.4's exception); step 0.7 is the cost-ledger pre-check (LR R4.5). Section 6 lists what still has no code |
| RB8 | The builder had never run on real units | Unchanged in kind | The no-value pre-runs R1a and R1b; stop on identity lines only (addendum §39 point 8(a), 8(d)) |
| RB9 | B16 does not refuse an edited `tables.json` | Unchanged | The script's provenance checks (steps 3, 4, 4b, 4c), corrected for B16's `_strip` (section 9, change 10) |
| RB10 | The first stamp was pending | **Closed.** Anchored in Bitcoin block 974039 (header time 2026-10-31T23:28:48 UTC) and 974047 (2026-11-01T00:42:41 UTC), checked at two explorers (FOCUS:74; `TS/ots-check-20261101.json`) | Step 0.3 is now the verification rule for the second stamp; a third stamp follows the records (E-39 point 9) |
| RB11 | "Stops and asks" against the user's "go on" | Ruled: report and go on (E-39 point 10; LR R6) | Step 6 reports and goes on |

Nothing blocks the $0 preparation. The reading waits on: the merge `[FILL-COMMIT]`, the suites and specs of
section 3 on the final tree, the second stamp and its anchor.

## 1. State now (M unless marked)

- HEAD of the main checkout is `c21dccb` (M, 1 Nov 16:22 UTC). Since `55d5f8b`: `53f746d` (D-6 and kit round 34
  merged; the lead's rulings), `b5e3c27` (the similarity pass ran on one A100 pod; the strata sealed; the B14 inputs
  file written and checked), `0435c3b` (a grant dossier entry), `c21dccb` (one test file,
  `scripts/stage1_s1/tests/test_b14_inputs.py`, and three build-round reports; no file of section 2). No uncommitted
  change under `scripts/`, `runkit/` or the engine. The manifest of step 0.6, not this section, is the pin.
- Tree ids at HEAD: `scripts/stage1_s1` `46bdebf8` (changed by B, then by the test commit `c21dccb`),
  `scripts/stage1_s1/reading` `4b765fc3` (equal to the first stamp's; B16 unchanged), `scripts/stage1_s1/reading_input`
  `a57e775a` (equal to the first stamp's; D-5 not merged yet), `runkit/stage1-olmo` `ec05103e` (round 34), `scripts/stage1`
  `94ccc56e`, `scripts/gate_b_mac_judges` `8335d4d1`, `experiments/safety_selection` `bdacc365` (the last three equal
  the first stamp's, TS/ots-manifest-20261031.json:9-16).
- Not merged yet, in the build worktrees at `55d5f8b`: track A (`ws-a`: `reading_input/` 5 changed, 5 new files),
  track D1 (`ws-d1`: `reading_extra/`, 17 new files), track D2 (`ws-d2`: `hlc_draw/`, 10 new files). Their hashes are
  in section 2. `git status --porcelain` in each worktree shows only those files.
- Kit code: the repository and live copies are equal, both at round 34: `stage1_rules.py` `4005cb4e…`, `seal.py`
  `d6ddc8ef…`, `plan_tool.py` `27e299b5…`, `judge_units_stage1.py` `53f3c65b…` (`finisher.py` `f474cabe…`,
  `setup/job_runner_stage1.py` `ba0a761a…`; not read by the reading).
- Seals (R: FOCUS:76, :106; TS/ots-manifest-20261031.json:102-108): A `6c6267c8b8d3476fba2fc5eb906abdc5ff80e18b418f543efb24a166d073e52d`
  (1,703 files), B `b4e11dc9290bcdc9da30cbe078c9cc928254a7a08456b9e546e3268888ffed3c` (3,830 files, 3,541 sealed).
  Judges (R): A `s1a-hb-1`, `s1a-granite-1`, 27 units, 54 files; B `s1b-hb-1` (57,600 judged), `s1b-granite-1`
  (14,400), 72 units, 144 files (FOCUS:76, :108).
- B14's records under `RD/b14/` (names only, from `git ls-files`): `similarity.json`, `strata/strata.json`,
  `inputs/overlap_inputs.json`, `jobs_block_sim.json`, `funding_block_sim.json`, `pack_inputs_X_round34.json`. I did
  not open or hash them; FOCUS holds their SHA-256 (the fill markers).
- Venv `tmp/minimal-experiment-20261002/venv/bin/python`: Python 3.11.15, numpy 2.2.6 (the same as the suites).
- The reading is `plan_a` (`docs/study-plan-full.md:298`); the builder refuses the block-A-only reading once block B
  is sealed (RI/build.py:606-607).

## 2. What the runbook pins

The second stamp's manifest (step 0.6) is the pin file. The script's first check (R0) re-hashes everything in it.
Values now: changed and new files from the worktrees `ws-a`, `ws-b`, `ws-c`, `ws-d1`, `ws-d2`; unchanged files
from the main checkout at `c21dccb` (M; equal at `0435c3b`; B's and C's worktree hashes equal the main checkout's).
"Never" = the file is not touched by any merge before the reading; a change would need a new second stamp.

| File | SHA-256 (M) | Changes when |
|---|---|---|
| `B16/__init__.py` | `244f1c9705abfdf87f036d2a0f137e87b1bf15aa36092f8497c443b9ea37fc0e` | never (B16 is byte-identical under D-5) |
| `B16/__main__.py` | `f859f54af41292b692e4a0a8bb5458029235a61489a517b633c8b60a6d4cef08` | never |
| `B16/contrast.py` | `19d8941d8954353b4b29c16d5f9c78aeac8982070378ce10667504c5d9301670` | never |
| `B16/labels.py` | `ba555c1d134a0fdc1c324b95d9d5267256bee9a21194bc0c269e77c1acdd406a` | never |
| `B16/overlap.py` | `1c6e6b201843263fdaebc1ea79e695fb30c7f6af5ad50d7127b530de85d8919d` | never |
| `B16/phi.py` | `1f74f469c201e584543a97860ed334583582d6b18b1be9b2d9045cf1f0d0a9ec` | never |
| `B16/reading.py` | `38b4881cc8814ee32ed4b38ae7eda7a2d4d66664e3f6bdc1fb6f10c2da45b7e5` | never |
| `B16/references.py` | `ce7a51da39e069cc5a0e4d5a0492ecc359b2aa18af84eebc4d9d125145feee5d` | never |
| `B16/reml.py` | `56f371e603358febb806e83037398d15b9d2f7e7ad5cb3fe173fbd7f528ffb9d` | never |
| `B16/schema.py` | `6ce88f584f3510ae2712061242ff82abc657b68e9a304083cd0a5bf836eb13ee` | never |
| `B16/sensitivities.py` | `224b29156ec97c9177e3bcd6851f3fd07244ad79daa250959a055dd25ab52e85` | never |
| `B16/settings.py` | `315297191988559e78fa02063cd93472ebd04266dea00aab252352876b99144a` | never |
| `B16/tdist.py` | `6982a7b119e4a5eae34b5f45a62e0871ab5f3a8ca51cfb882cd31668c61c1fac` | never |
| `B16/settings/reading.json` (the settings pin, `B16/settings.py:21`) | `fef3b6f5bb2fbed70f01785bc64177aed02eff955ab164e37f23d05356af5b18` | never (LR R6.5: the pin must not move) |
| `RI/__init__.py` (ws-a) | `3efbc49e298a64c8d24bc277db4abc151a85bd6b73d478b0b601b284d1b63cf4` | at the merge |
| `RI/__main__.py` (ws-a) | `992787928667fe229045bb09f8b174bfa76ea405c892214e7b355e5bb39b38f8` | at the merge |
| `RI/build.py` (ws-a) | `e82214e7183025632973692b79112347bf73b961feb62d530f3640de57bf9b5d` | at the merge |
| `RI/items.py` (ws-a) | `70a52ca84d604b81755428ba873ff382cdee7e020d2c581e42ff06a057c1a105` | at the merge |
| `RI/coherent.py` (ws-a, new) | `9f3010fb52ea6459d16dc987e46ec30f2b69f15546a8603fc6bd53946ea8441a` | at the merge |
| `RI/sg_coherent.py` (ws-a, new) | `a0b001f7f40c1d2ff9a79959b3146ba569dd70d2929de87de3a6092568c0ce8c` | at the merge |
| `RI/sources.py` | `127223a80c7a3dec5a88680278507b99e812b023e65ed49a5e0b67e770642d0a` | never |
| `RI/hb.py` | `7a54cb305ecf452f2b165a8c1f871af7f1785bcd55853437ac8e87db114e1d11` | never |
| `RI/hb_claim.py` | `375793dbe3e252babecf50bdc34ee343184ba176e741f4e71c7a46c5ea954ebe` | never |
| `RX/__init__.py` (ws-d1, new) | `4b6d8b4c75f8e1f4e0f76a78ae03fa5812f1a3173920d21e67b3890e2e819321` | at the merge |
| `RX/common.py` | `087a4c0c555bed236b2b465298bcf1aa5ff58a3f20effae923fded1545272d67` | at the merge |
| `RX/fk_power.py` | `28d4647341c04f793762faa61def92453b886a37fa1e7eca9bb51bd2c2a45819` | at the merge |
| `RX/stage3_pick.py` | `f6236e9ec4f6b0bf3e5737249f20aa16dc4d649905399307f347951a9181f03f` | at the merge |
| `RX/cap_reports.py` | `c61b3a8a3d3b4bb02c4780b49fa9c6e40e108b50202d14b7cdf777cd15f79dda` | at the merge |
| `RX/sa_shift.py` | `d3bf468f0e88f2c94776144a7dd55fba3be2e80a779314ae4d098366ecce0b2a` | at the merge |
| `RX/cost_table.py` | `d0a983217cf657649ae8283f38046788addf41b5ab7da45b244f0405483f17b7` | at the merge |
| `HD/__init__.py` (ws-d2, new) | `1ac0cb733524b06c2fda6669b7ea59e3d8595dd6ad43a32b919abff5397cf212` | at the merge |
| `HD/__main__.py` | `ee7d4747958579fe034023356e2faa0984771c2a8413f326c2c9000ce5672759` | at the merge |
| `HD/draw.py` | `61ef55cae6560c81e34bfd80f97e8abaa4e489cdf85b2d3fcb2da69d0aac7fa1` | at the merge |
| `HD/inputs.py` | `0fbacd72f58b1225fcefe36dbd0304d9da79fc3faf6109a7993fbb877cb20743` | at the merge |
| `HD/settings/hlc_draw.json` (= `HD/draw.py` `SETTINGS_SHA256`) | `1d3eabe38e9b5d069623ba17bcef3f2d939d0abf309c5d7f06473847179a8c2d` | at the merge; a settings change needs a new pin, suite and mutants (D2B 12.10 point 2) |
| `scripts/stage1_s1/overlap_strata.py` (D-6; merged) | `4249b070695a2409332655043224ca49db05fdb6ebca9906cb7900387db1d6c9` | never |
| `scripts/stage1_s1/settings/overlap_strata.json` (= `overlap_strata.py:60`) | `92c3a4a006ea5bf45eb04b01d3fa6f59d7b260408c28df11a4d9848b0a20a41d` | never |
| `scripts/stage1_s1/overlap_inputs.py` (merged) | `952e59eb083f1b945794141d9c90876e4667d679639eeab04b0ecae74ab248f4` | never |
| `scripts/stage1_s1/overlap_inputs_check.py` (merged) | `57a7efb2ed538d54b3fb305f6e21d3e136c73a03285819acd63b242eaab4f80a` | never |
| `scripts/stage1_s1/overlap_similarity.py` | `f8305c712109b1bc733769b806c3a37cee9726feab0694e89f42dfc47d4f79f4` | never (the kit's `S1_CODE` pin, CKB:16) |
| `scripts/stage1_s1/settings/overlap_similarity.json` | `27db4c3faafc41c4278ff6ca7d1ded0a0fb1a07ae484c4bbf65702f5545ac754` | never (CKB:16) |
| `RD/b14/strata/strata.json`, `RD/b14/similarity.json`, `RD/b14/inputs/overlap_inputs.json` | `[FILL-STRATA-SHA256]`, `[FILL-SIM-SHA256]`, `[FILL-B14IN-SHA256]` (FOCUS) | never |
| `scripts/family_probe_reading.py`, `scripts/killtest_stage0_reading.py` (B14's frozen readers) | `8848340107bd4accee837bcd4a696e5bb230cc2157dba7def385a11ff6a9ad5a`, `1740663bc9e465422ba3c96db3898665035c6bfaa8db9716b89db16ae9f1a5e9` | never |
| `scripts/stage1/limits/limits_common.py`, `scripts/stage1/s1common.py` (W1) | `2798aa06a01fd89bf3dd8dc2abf33e63bfcb4f17bff700a709eacd2b3ace264c`, `930c8ea53d26baeeccaf2035949427d207f307ba0fec06ff0dec841c8c824552` | never |
| coherence bars file (`RI/items.py:44-45`) | `c0b6f2aae43285de632a175adb1e913cd31f37bc6ac25fb56e4468ff3a1208ea` | never |
| kit `stage1_rules.py`, `seal.py`, `plan_tool.py`, `judge_units_stage1.py` (repo and live copies, equal) | `4005cb4e82f836eb6734073856c6c379631c03f8953842ded466f28f9b054dd0`, `d6ddc8efc3c4a86247708d9bf8d9b629d1093c059e3ba33bc83854c8ac4d0af5`, `27e299b577bdb3fbbd7b80c2dd1a47083df3a0cd8e153f7018b4992130d1f75e`, `53f3c65b82185aaa96ace14a1bfc7dfd3df031b7031918d1922b21676d83eefe` | never (round 34's hashes, LR R3.2; R1D's `bde78fab…` and `f18bb834…` are superseded) |
| specs and runners: `mutants_b16.json`, B16 `run_mutants.py`, `mutants_reading_input.json` (ws-a, 47 entries), RI `run_mutants.py`, `mutants_reading_extra.json` (ws-d1, 62), RX `run_mutants.py`, `mutants_hlc_draw.json` (ws-d2, 65), HD `run_mutants.py`, `mutants_b14.json` (150), `tests/mutants_b15.json` (418) | `5ccf63adf29ff26608ed087b9df57522b8017a6ac0aed383d789bb5d6698153c`, `c9550a3b1e5074a3f0691f78801007c0864b275e83a11c72a7806293fc96f265`, `52f231ed9c6d787f88c14f18d495925e93d61e0f30e83cb6d8cd8bd496201006`, `491a2266856b9c632d0b0e856349034f8e7c987727d4df20427ce9d029dd83ac`, `4dca4cd8b01d64062bc915dff54045b99af9f72a03d8c46f41daffdf6fdeb560`, `5d00d42a24c26522745513646b27b23e5ac41137dc22d7dd7aa295e596a47471`, `9a33f4418d5f637747e7eea52de99f7219ae99eb091a4376ca9e9f91fba886ad`, `5e60815377cea6a0342363ed8185424814a66012f591b2fb48ea52a50642968f`, `4f6e0b6b6c7caa55ea203515118fe47082f5c37354462f81eb34c330a2d6a11c`, `a57358715260a5f3f327e7788f79bf0e211c99582cd3c9bd6721f06ae6b89871` | at the merge (the three new specs) |
| `tmp/stage1-olmo/plan.json`; this runbook (at `$RD/reading-runbook-$STAMP.md`); `reading.zsh` (at `$RD/reading-$STAMP.zsh`) | not hashed by me; the manifest writer hashes them at step 0.6 (`kit.plan_json_sha256`, `files`), R0 re-checks them, and their SHA-256 is never written into this runbook (the markers table) | never after step 0.6 |
| the second manifest `$M2` | its SHA-256 and anchor go to FOCUS and `TS/ots-check-reading-$STAMP.json`, never into this runbook | never after its stamp |

B16 hashes every top-level `*.py` of its package and `settings/reading.json` into each output
(`B16/settings.py:160-166`; `B16/reading.py:577-578`), then `_strip` drops every key that starts with `_`
(`B16/reading.py:539-542`; M: the output's `modules` holds 11 modules and `settings/reading.json`, never
`__init__.py` or `__main__.py`; ACB §8 item 7). The claim reader, the D-5 reader and the reading-time readers record
their own modules and `b16_modules` the same way (`RI/hb_claim.py:246-249`; `RI/sg_coherent.py:383-387`;
`RX/common.py` `provenance`). The script's provenance checks expect exactly that (section 9, change 10).

## 3. Suites and specs: re-run on the FINAL tree, before the second stamp

Run them after the merge `[FILL-COMMIT]`. The second stamp then binds that tree. Each runs as the lead's background
job (memory: long jobs outside agents), with the Mac awake (FOCUS:86). In the main checkout `test_oext_unit_y.py`
finds engine Y's tree by its default path; in a worktree it needs `STAGE1_ENGINE_Y_TREE=$ROOT/tmp/engine-y-34bfd288`
(BBB:174-175, :281).

```zsh
ROOT=/Users/spiderishi/Coding/attribution; KIT=$ROOT/tmp/stage1-olmo; PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
SCR=/private/tmp/stage1-reading-checks; mkdir -p "$SCR"                     # outside the repo; delete after
STAMP=FILL-STAMP                                                            # the second stamp's date label (Block R)
CHK=$ROOT/.ai/inputs/stage1-post-w1-20261023/reading/checks-$STAMP; mkdir -p "$CHK"   # logs and reports (committed)
cd "$ROOT" || exit 1
T() { "$PY" -B -m pytest -q -p no:cacheprovider --basetemp="$SCR/bt-$1" "${@:2}" > "$CHK/suite-$1.txt" 2>&1; print "$1 exit $?"; tail -1 "$CHK/suite-$1.txt"; }
T b16   scripts/stage1_s1/reading/tests                  # (iii) of addendum:507; B16 unchanged
T ri    scripts/stage1_s1/reading_input/tests            # the builder, the HarmBench reader, D-5's counts and reader
T rx    scripts/stage1_s1/reading_extra/tests            # the five reading-time readers
T hlc   scripts/stage1_s1/hlc_draw/tests scripts/stage1_s1/tests/test_s1_layout.py   # D-7's draw; re-run after A's merge (LR R5.5)
T s1    scripts/stage1_s1                                # whole package: (v) d1_spool, d2_pool_pins, c3_subsample, B14 under D-6, B10/B11, O-ext, and the three new packages
T w1    scripts/stage1/tests                             # (ii)
T engx  experiments/safety_selection/tests               # (i)
T kit   runkit/stage1-olmo/tests                         # round 34; the builder loads stage1_rules
T judges scripts/gate_b_mac_judges/tests                 # (iv): ALONE, never beside another suite
"$PY" -B scripts/stage1/commitments.py check --repo "$ROOT"; print "commitments exit $?"
```

| Run | Expect | Duration | Source |
|---|---|---|---|
| `b16` | 261 passed, 0 skipped | 3.5-7 min of pytest (M in the reports: 243-407 s); up to 21 min of wall time under load | ACB:193, :199; BBB:179 |
| `ri` | 284 passed (195 + 89 of D-5) | about 1.5-4.5 min (M: 78-256 s); basetemp 2.8 GB: delete it | ACB F.0 item 5, F.3 |
| `rx` | 120 passed | about 30 s; basetemp 330 MB | D1B 7.5; D1V3 |
| `hlc` | 123 + 3 passed | about 15-45 s; basetemp up to 0.8 GB | D2B 12.6 |
| `s1` | 999 passed on B's tree (BBB:181) plus A's 89, D1's 120 and D2's 123 new tests on the merged tree (E: about 1,330; the collected count is the record) | E: 10-30 min | BBB:177-181; D1B:96 (no basename clash across the three packages, 576 collected with B16's and the builder's) |
| `w1` | 918 passed | about 65 s | R1D:144 |
| `engx` | 1,108 passed, 5 skipped | not recorded (E) | FOCUS:103 |
| `kit` | 735 passed | about 1-2 min (M: 53-120 s) | CKB:215 |
| `judges` | 548 passed, 5 skipped, 1 known failure `test_granite_summary.py::test_the_summary_and_items_are_the_kit_format_with_the_pod_device` | not recorded (E) | R1D:147 |
| `commitments` | `OK: 140 entries {…}; base 8fe5fe93…; HEAD …; 0 excluded; 13 not built; N files committed later, classified` | seconds (E) | `scripts/stage1/commitments.py:380-382` |

Mutation specs (background jobs; a runner kills only on a real test failure, and an error is an invalid run). B16's
117-entry spec need not run again: B16 is byte-identical under D-5 (E-D5-D6 §1 Reasons; E-plan item 13).

```zsh
SPEC=scripts/stage1_s1/reading_input/mutation/mutants_reading_input.json   # 47 entries: the builder, D-5's counts and reader
for K in 0 1 2 3; do
  IDS=$("$PY" -I -B -c 'import json, sys; ids = [m["id"] for m in json.load(open(sys.argv[1]))["mutants"]]; print(",".join(ids[int(sys.argv[2])::4]))' "$SPEC" $K)
  "$PY" -B scripts/stage1_s1/reading_input/mutation/run_mutants.py --spec "$SPEC" --scratch "$SCR/ri-mut-$K" --report "$CHK/ri-mut-$K.json" --python "$PY" --timeout 600 --only "$IDS" > "$CHK/ri-mut-$K.log" 2>&1 &
done; wait
SPEC=scripts/stage1_s1/reading_extra/mutation/mutants_reading_extra.json    # 62 entries; RX-common-exclusive survives as marked
for K in 0 1 2 3; do
  IDS=$("$PY" -I -B -c 'import json, sys; ids = [m["id"] for m in json.load(open(sys.argv[1]))["mutants"]]; print(",".join(ids[int(sys.argv[2])::4]))' "$SPEC" $K)
  "$PY" -B scripts/stage1_s1/reading_extra/mutation/run_mutants.py --spec "$SPEC" --scratch "$SCR/rx-mut-$K" --report "$CHK/rx-mut-$K.json" --python "$PY" --timeout 600 --only "$IDS" > "$CHK/rx-mut-$K.log" 2>&1 &
done; wait
SPEC=scripts/stage1_s1/hlc_draw/mutation/mutants_hlc_draw.json              # 65 entries; D2 ran all 65 on the final bytes (D2B 12.5); re-run after A's merge
for K in 0 1 2 3; do
  IDS=$("$PY" -I -B -c 'import json, sys; ids = [m["id"] for m in json.load(open(sys.argv[1]))["mutants"]]; print(",".join(ids[int(sys.argv[2])::4]))' "$SPEC" $K)
  "$PY" -B scripts/stage1_s1/hlc_draw/mutation/run_mutants.py --spec "$SPEC" --scratch "$SCR/hlc-mut-$K" --report "$CHK/hlc-mut-$K.json" --python "$PY" --timeout 600 --only "$IDS" > "$CHK/hlc-mut-$K.log" 2>&1 &
done; wait
# B14 under D-6 and the inputs writer: the 69-entry near set before the stamp (LR R2.2); the full 150-entry spec when the machine allows
NEAR=.ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/build-round/mutants_b14_near.json   # 77c3def1…
"$PY" -B scripts/stage1_s1/mutation/run_mutants_b14.py --spec "$NEAR" --scratch "$SCR/b14-near" --report "$CHK/b14-near.json" --timeout 900 > "$CHK/b14-near.log" 2>&1
# kit round 34: the 36 new and 3 retargeted ids (CKB §7 step 2)
IDS=$("$PY" -B -c "import json;d=json.load(open('runkit/stage1-olmo/tests/mutants_b15.json'));print(','.join(m['id'] for m in d['mutants'] if m['id'].startswith('B15-34-') or m['id'] in ('B15-r-o-only-unit','B15-8-runner-settings-unpinned','B15-g-no-recorded-recipe')))")
"$PY" -B research/experiments/2026-10-24-stage1-runkit/run_mutants_b15.py "$ROOT" "$SCR/kit34" "$CHK/kit-round-34-mutation-report.json" "$IDS" > "$CHK/kit34.log" 2>&1
```

| Spec | Expect | Duration | Source |
|---|---|---|---|
| reading_input, 47 entries | every baseline 284 tests; 47 killed, 0 survived, 0 invalid (no expected survivor is listed) | about 55-70 min in one process unloaded; 2.8 GB of basetemp per mutant run | ACB F.4 (20 of 47 confirmed under the official runner: ACV2 §0 item 1) |
| reading_extra, 62 entries | baseline 120; 61 killed, `RX-common-exclusive` survives (`"expect": "survive"`), 0 invalid | E: 40-60 min (shards of 4-10 ids took 2.5-9 min) | D1B 7.6 (14 of 62 run after fix round 2; 48 anchors checked) |
| hlc_draw, 65 entries | baseline 123; 65 killed, 0 invalid | about 25-40 min of pytest | D2B 12.5 (all 65 killed on the final bytes) |
| B14 near set, 69 entries (`mutants_b14_near.json`, `77c3def1…`) | baseline 999 or more; 69 killed | about 1.8-2.5 h (E) | BBB:231-236 (all 69 killed in B's harness); the full 150-entry spec about 4-5.5 h (E) |
| kit round 34, 39 ids | baseline 735; 39 killed, `not_as_expected` empty | E: about 1.5 h | CKB §5, §7 step 2 |

Then delete every `$SCR/bt-*`, `$SCR/*-mut-*`, `$SCR/b14-near` and `$SCR/kit34` folder (memory: keep the Mac
lean). The D-6 record states which B14 set ran and its result (E-D5-D6 §2 point 2).

## 4. The procedure

Rules for every step:
- Run `date -u` before writing any time. The Bash tool keeps no shell state: set Block R first in every call.
- Nobody opens a unit folder, an answer, a guard file, a judge file, a label cache, a seal file, a cost ledger or a
  `COMPLETE.json` by hand, at any step. The tools parse fields; the lead reads only what they print and the output
  documents. The one explicit exception (LR R4.4): inside the script at step 4c, `cap_reports` opens the O-ext
  summaries and COMPLETE.json files the builder's record names, and `cost_table` opens `plan.json`, the seals and
  the cost ledgers. Their outputs are read only after the script ends.
- `tmp/stage1-olmo/retrieved/` is on the never-open list (FOCUS:74). Tools read `retrieved/sim-1/` only by the exact
  path and SHA-256 that `record-done` printed; the lead never lists `retrieved/` (LR R3.1). No step of this runbook
  walks a folder under `retrieved/`.
- `tmp/hlc-inputs/` is never opened by a helper (E-misc B ruling 2); the script passes its paths to the draw.
- Never open a unit folder in Finder (a `.DS_Store`; JRB:120). Keep the Mac awake and the lid open (FOCUS:86).
- No kit command that writes (`plan_tool.py`, `seal.py block`, launches) runs from step 0.6 to step 6.
- Steps R0-5 run as one pre-committed, stamped script (`reading.zsh`), as one background job. The lead reads its
  console and logs only after it ends.

### Block R: settings

```zsh
ROOT=/Users/spiderishi/Coding/attribution; KIT=$ROOT/tmp/stage1-olmo      # tmp/gi-vii-notes/blockB_S.zsh sets the same three
PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python                   # 3.11.15, numpy 2.2.6
export PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
RD=$ROOT/.ai/inputs/stage1-post-w1-20261023/reading      # the reading's records (tracked)
TS=$RD/timestamp                                         # the OpenTimestamps files
STAMP=FILL-STAMP                                         # the second stamp's date label, e.g. 20261102; filled before the commit of step 0.6
RUN=$RD/run-$STAMP                                       # the reading's outputs; absent until the script makes it
LOGS=$RUN/logs; LEDGER=$RUN/reading-ledger.jsonl         # the tools' output; one JSON line per step
M2=$TS/ots-manifest-reading-$STAMP.json                  # the second stamp's manifest (step 0.6): the pin file
SCR=/private/tmp/stage1-reading-scratch                  # outside the repo; empty at the start; deleted after step 6
STRATA=$RD/b14/strata/strata.json                        # the sealed strata (1 Nov)
STRATA_SHA=FILL-STRATA-SHA256                            # its SHA-256 exactly as FOCUS records it (addendum:375)
SIM=$RD/b14/similarity.json                              # the by-hash copy of similarity.json (LR R3.1)
B14IN=$RD/b14/inputs/overlap_inputs.json                 # step 0.4 (done)
OCT9KEY=$ROOT/tmp/hlc-inputs/oct9/key.json               # step 5's pinned inputs (LR R5.5); never opened by hand
V3=$ROOT/tmp/hlc-inputs/prepared-v3-inj05
OTSDIR=/private/tmp/stage1-reading-ots                   # the ots client's own folder, outside the repo and outside $SCR (which must be empty at R0);
OTS=$OTSDIR/venv/bin/ots; OTSPY=$OTSDIR/venv/bin/python  # made at step 0.3; kept until the third stamp is verified, then deleted
```

### Step 0.1: preconditions (read-only; seal-safe)

```zsh
date -u
cd "$ROOT" || exit 1
git log --oneline -1
git status --porcelain -- scripts runkit experiments/safety_selection | head -3; echo "(nothing above = code clean)"
for t in scripts/stage1_s1 scripts/stage1_s1/reading scripts/stage1_s1/reading_input scripts/stage1_s1/reading_extra scripts/stage1_s1/hlc_draw runkit/stage1-olmo scripts/stage1 scripts/gate_b_mac_judges experiments/safety_selection; do print "$t $(git rev-parse HEAD:$t)"; done
shasum -a 256 runkit/stage1-olmo/{stage1_rules,seal,plan_tool,judge_units_stage1}.py "$KIT"/{stage1_rules,seal,plan_tool,judge_units_stage1}.py | cut -c1-16,65-
shasum -a 256 "$KIT/plan.json" "$KIT/seals/block-A.json" "$KIT/seals/block-B.json" "$STRATA" "$SIM" "$B14IN"
"$PY" -B "$KIT/seal.py" status | grep -E '^seal |^judges ' | cut -c1-220
{ pgrep -fl 'venv/bin/python -B .*(judge_pod|judge_units_stage1|launch|finisher|orchestrate|plan_tool|seal)\.py' || echo "nothing running"; } | cut -c1-140
"$PY" -I -B -c 'import platform, numpy; print(platform.python_version(), numpy.__version__)'
test ! -e "$RUN" && echo "run folder clear"; test ! -e "$ROOT/tmp/hlc/draw-$STAMP" && echo "sealed draw folder clear"; df -h "$ROOT" | tail -1
```

Go only with ALL of: code clean; HEAD is `[FILL-COMMIT]` or later with no code change after it; the tree ids equal
those the suites of section 3 ran on; each kit pair equal (`4005cb4e`, `d6ddc8ef`, `27e299b5`, `53f3c65b`); seal
files `6c6267c8…` and `b4e11dc9…`; `$STRATA` at `[FILL-STRATA-SHA256]`, `$SIM` at `[FILL-SIM-SHA256]`, `$B14IN` at
`[FILL-B14IN-SHA256]`; status lines `seal A: 1703 files (1529 sealed), sha256 6c6267c8…`, `seal B: 3830 files
(3541 sealed), sha256 b4e11dc9…`, `judges A: … valid: 27 required units, 54 indexed files`, `judges B: … valid:
72 required units, 144 indexed files` (R: FOCUS:76, :106; format `runkit/stage1-olmo/seal.py:191,222`); "nothing
running"; `3.11.15 2.2.6`; "run folder clear"; "sealed draw folder clear". Note plan.json's SHA-256: the builder prints
it again (`RI/__main__.py:70`). Who reads what: the lead reads hashes, status lines and counts only.

### Step 0.2: the seals still hold (optional; hashes by exact path; prints counts)

It parses each seal record for paths and hashes only (no value; `seal.py:9-13`), as the builder does at R1b, and
re-hashes every listed file by its exact path. It walks no folder (LR R3.1), so it does not count unlisted files
(R1D's `not_listed` is dropped), and it never parses a unit file.

```zsh
"$PY" -I -B - "$KIT" A B <<'EOF'
import hashlib, json, pathlib, sys
kit, blocks = pathlib.Path(sys.argv[1]), sys.argv[2:]
plan = json.loads((kit / "plan.json").read_text())
sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
out, ok = {}, True
for b in blocks:
    entry = plan["seals"][b]
    seal = kit / entry["path"]
    if sha(seal) != entry["sha256"]:
        out[b], ok = {"seal_file": "not at plan.json's SHA-256"}, False
        continue
    doc = json.loads(seal.read_text())
    c = {"listed": 0, "same": 0, "differs": 0, "missing": 0}
    for f in doc["files"]:
        base = kit / "judges" / b if f["host"] == f"judges/{b}" else kit / "retrieved" / f["host"] / "tree"
        q = base / f["path"]
        c["listed"] += 1
        if not q.is_file():
            c["missing"] += 1
        elif sha(q) == f["sha256"]:
            c["same"] += 1
        else:
            c["differs"] += 1
    out[b] = c
    ok = ok and c["differs"] == 0 and c["missing"] == 0
print(json.dumps({"blocks": out, "pass": ok}, sort_keys=True))
sys.exit(0 if ok else 1)
EOF
echo "seal check exit $?"
```

Expect `listed` 1,703 (A) and 3,830 (B), `same` = `listed`, `differs` 0, `missing` 0 (I), exit 0. The layout follows
`seal.py:101-131` (host files under `retrieved/HOST/tree`, judge files under `judges/BLOCK`).

### Step 0.3: the stamps' verification rule (the first stamp is done; the second follows step 0.6)

The first stamp is anchored (FOCUS:74; `TS/ots-check-20261101.json`): block 974039 (header time 2026-10-31T23:28:48
UTC) and block 974047 (2026-11-01T00:42:41 UTC), each proof's commitment equal to the block's merkle root at
blockstream.info and at mempool.space. The rule for the second stamp (E-39 point 9; LR R6): two independent
sources agree on the height, the block hash and the merkle root, and the root equals the proof's commitment;
**margin:** at least 6 confirmations (tip − height + 1 ≥ 6), and step 1 starts at least 2 h after the anchoring
block's header time (header times are accurate to about 2 h). The first stamp's client lived in a scratch venv that
was not kept (`TS/stamp-record-20261031.json:38`), so the client is installed once more, from the nine recorded
wheels with `--require-hashes` (`TS/stamp-record-20261031.json:39-84`; the network needs the lead's go), into its
own folder `$OTSDIR` (outside `$SCR`, which R0 requires empty). Keep it until the third stamp (step 6) is verified.
The check tool is the lead's `RD/lead-reports-20261101/tools/ots_check.py` (used on 1 Nov for the first stamp,
`TS/ots-check-20261101.json`): it reads every Bitcoin attestation out of the proof itself, so no height is typed by
hand, and it writes its record by an exclusive create.

```zsh
date -u
mkdir -p "$OTSDIR"
"$PY" -I -B - "$TS/stamp-record-20261031.json" > "$OTSDIR/ots-requirements.txt" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
for name, p in sorted(d["tool"]["packages"].items()):
    print(f"{name}=={p['version']} --hash=sha256:{p['sha256']}")
EOF
"$PY" -m venv "$OTSDIR/venv" && "$OTSDIR/venv/bin/pip" install --require-hashes --only-binary=:all: -r "$OTSDIR/ots-requirements.txt"
cd "$TS" || exit 1
cp -p "$(basename "$M2").ots" "$OTSDIR/"                   # keep the pending proof (ots upgrade also leaves a .bak beside)
"$OTS" upgrade "$(basename "$M2").ots"; print "upgrade exit $?"
"$OTS" info "$(basename "$M2").ots" > "$OTSDIR/ots-info-reading-$STAMP.txt"
grep -c -E 'BitcoinBlockHeaderAttestation' "$OTSDIR/ots-info-reading-$STAMP.txt"   # 0 = still pending: wait, upgrade again
"$OTSPY" -I "$RD/lead-reports-20261101/tools/ots_check.py" "$TS/ots-check-reading-$STAMP.json" "$(basename "$M2")"; print "check exit $?"
for API in https://blockstream.info/api https://mempool.space/api; do print "tip $(curl -fsS "$API/blocks/tip/height") at $API"; done
date -u
```

Expect one JSON line per Bitcoin attestation with `"ok": true` (two calendars anchored the first stamp: two lines),
then `{"all_ok": true, "attestations": N}`, and a tip at least 5 above the highest height. Record the heights, block
hashes, roots, header times, both tips and `date -u` in FOCUS; the tool's record `TS/ots-check-reading-$STAMP.json`
holds them too. Commit the upgraded `.ots` file and the check record by their explicit paths. Nothing of this goes
into this runbook (the markers table). No anchor after 48 h: re-stamp once; then the plan's fallback wording
(plan:34; S9).

### Step 0.4: B14's inputs file (done on 1 Nov; the commands, for the record and for a re-run)

B's writer replaces R1D's heredoc (BBB:238-252; LR R2.3). It reads plan.json, B14's settings, the strata record and
the rules module, and of each unit only the bytes of `COMPLETE.json` and `job.json`, hashed and never parsed. The
checker recomputes the file by other code (standard library only, no module of this repository) and compares the
bytes. Order: D-6 committed, the writer, then the checker at once (the checker binds plan.json's SHA-256; a later
plan.json write makes it print DIFFERENT at `sources.plan_json_sha256`, B's verifier N3).

```zsh
date -u; cd "$ROOT" || exit 1
"$PY" -B scripts/stage1_s1/overlap_inputs.py --kit "$KIT" --strata "$STRATA" --strata-sha256 "$STRATA_SHA" --out "$RD/b14/inputs"
#   prints: wrote overlap_inputs.json into … (<sha>); seed plan d1_plan_a; strata …; and per cell a count line, e.g.
#   "a0: 6 units; pinned at 1102, 1103; from the kit A:a-10, B:b-1, B:b-2, B:b-3" (BBB:263). Exit 2: refused, nothing written.
"$PY" -I -B scripts/stage1_s1/overlap_inputs_check.py --file "$B14IN" --kit "$KIT" --strata "$STRATA"
#   exit 0 and "same bytes: … sha256 <H>"; 1 DIFFERENT (the first differing key, no value); 2 refused
```

Expect 24 units (a0, S1, S3, S4 at 1102-1107; BBB §9), exit 0 twice, `[FILL-B14IN-SHA256]` on both lines. The
report later runs with the default `--data-root` (the writer's default is the same `lc.DEFAULT_DATA_ROOT`). Who
reads what: plan.json fields, counts, origins and hashes only; nothing under `retrieved/` is listed.

### Step 0.5: rehearsal on synthetic data (recommended; no real data)

`zsh -n reading.zsh` (M: exit 0 on this file). Then the script end to end on a synthetic world: the builder's
`synth_kit` with B16 and the readers, as the builder's own smoke did (HBB:120; D1B:91 for the readers; D2B 12.9 for
the draw). The script cannot run unedited on it: `KIT`, `RD`, `RUN`, `M2` and `PY` derive from `ROOT`, R0 runs `git`
in `ROOT`, and the draw needs a `.git` folder and a `.gitignore` with `tmp/`. So the rehearsal runs a **copy** whose
settings block is edited (`ROOT` to the synthetic root, `PY` to the real venv, `STAMP`, `SCR`, `STRATA_SHA`) and
whose two B14 lines (R1a and step 1) copy a synthetic report in B14's format, since no B14-compatible synthetic kit
exists beside the builder's world; every other byte is the original's, and a `git` stand-in first on `PATH` answers
`rev-parse` and `status`. The verifier's dry run is the worked example (runbook-verify1.md §3: `make_copies.py`,
`build_world.py`, the stand-in `bin/git`, under `builds/verify-runbook/v1/`, committed with the build round's
reports): both modes ran to `DONE` with exit 0, and the fix round repeated it (section 8). `M2` is a synthetic
manifest written by step 0.6's writer against the synthetic root. The heredoc checkers on synthetic files with one
planted difference each (each must fail; M: the helper functions `ledger`, `lines_check`, `prov` and the step-2
comparison were run so on 1 Nov, section 8). Delete the scratch after.

### Step 0.6: the second stamp (the pin file), then wait for its anchor

Fill `[FILL-STAMP]`, `[FILL-COMMIT]`, `[FILL-SIM-PATH]`, `[FILL-SIM-SHA256]`, `[FILL-STRATA-SHA256]`,
`[FILL-B14IN-SHA256]` and `[FILL-S1-RECORD]` in this runbook, and `STAMP` and `STRATA_SHA` in the script. Then
commit, by explicit paths: the merged code `[FILL-COMMIT]` (tracks A, D1, D2), addendum §39 and §40 (D-5 to D-7),
the S1 blinding record `[FILL-S1-RECORD]`, FOCUS's strata, similarity and inputs lines, this runbook (final, at
`$RD/reading-runbook-$STAMP.md`), the script (at `$RD/reading-$STAMP.zsh`, byte-identical to `reading.zsh`), and
section 3's reports under `$CHK`. Run `commitments.py check`. Then write the manifest. Every named file must be
under ROOT. The two files' SHA-256, the manifest's SHA-256 and its anchor are never written back into the runbook
(the markers table): the manifest and FOCUS hold them.

```zsh
date -u
cd "$ROOT" || exit 1
ANCHOR1="block 974039 (header time 2026-10-31T23:28:48 UTC) and block 974047 (2026-11-01T00:42:41 UTC); TS/ots-check-20261101.json"
S1REC=FILL-S1-RECORD
"$PY" -I -B - "$ROOT" "$KIT" "$PY" "$M2" "$ANCHOR1" "$RD/reading-runbook-$STAMP.md" "$RD/reading-$STAMP.zsh" "$B14IN" "$STRATA" "$SIM" \
  .ai/briefs/stage1-commitments-build-20261016-lead-decisions.md "$S1REC" docs/study-plan-full.md <<'EOF'
import datetime as dt, hashlib, json, pathlib, subprocess, sys
root, kit, py, out, anchor1 = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3], pathlib.Path(sys.argv[4]), sys.argv[5]
named = [pathlib.Path(x) if pathlib.Path(x).is_absolute() else root / x for x in sys.argv[6:]]
sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
git = lambda *a: subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, check=True).stdout.strip()
missing = [str(q) for q in named if not q.is_file()]
if missing:
    print(f"REFUSED: a named file is missing (fill or drop it before step 0.6): {missing}", file=sys.stderr)
    sys.exit(2)
tracked = [q.relative_to(root).as_posix() for q in named if not q.relative_to(root).as_posix().startswith("tmp/")]
if git("status", "--porcelain", "--", "scripts", "runkit", "experiments/safety_selection", *tracked):
    print("REFUSED: a pinned path has an uncommitted change; commit it first (explicit paths)", file=sys.stderr)
    sys.exit(2)
files = {}
for d in ("scripts/stage1_s1/reading", "scripts/stage1_s1/reading_input", "scripts/stage1_s1/reading_extra",
          "scripts/stage1_s1/hlc_draw"):
    for q in sorted((root / d).glob("*.py")):
        files[q.relative_to(root).as_posix()] = sha(q)
for rel in ("scripts/stage1_s1/reading/settings/reading.json", "scripts/stage1_s1/hlc_draw/settings/hlc_draw.json",
            "scripts/stage1_s1/overlap_strata.py", "scripts/stage1_s1/settings/overlap_strata.json",
            "scripts/stage1_s1/overlap_inputs.py", "scripts/stage1_s1/overlap_inputs_check.py",
            "scripts/stage1_s1/overlap_similarity.py", "scripts/stage1_s1/settings/overlap_similarity.json",
            "runkit/stage1-olmo/stage1_rules.py", "runkit/stage1-olmo/seal.py", "runkit/stage1-olmo/plan_tool.py",
            "runkit/stage1-olmo/judge_units_stage1.py", "scripts/family_probe_reading.py",
            "scripts/killtest_stage0_reading.py", "scripts/stage1/limits/limits_common.py", "scripts/stage1/s1common.py",
            "experiments/safety_selection/configs/family-probe-reading-amended-20261008.json",
            "scripts/stage1_s1/reading/mutation/mutants_b16.json", "scripts/stage1_s1/reading/mutation/run_mutants.py",
            "scripts/stage1_s1/reading_input/mutation/mutants_reading_input.json",
            "scripts/stage1_s1/reading_input/mutation/run_mutants.py",
            "scripts/stage1_s1/reading_extra/mutation/mutants_reading_extra.json",
            "scripts/stage1_s1/reading_extra/mutation/run_mutants.py",
            "scripts/stage1_s1/hlc_draw/mutation/mutants_hlc_draw.json", "scripts/stage1_s1/hlc_draw/mutation/run_mutants.py",
            "scripts/stage1_s1/mutation/mutants_b14.json", "runkit/stage1-olmo/tests/mutants_b15.json"):
    files[rel] = sha(root / rel)
for name in ("stage1_rules.py", "seal.py", "plan_tool.py", "judge_units_stage1.py"):
    files[f"tmp/stage1-olmo/{name}"] = sha(kit / name)
for q in named:
    files[q.relative_to(root).as_posix()] = sha(q)
trees = {t: git("rev-parse", f"HEAD:{t}") for t in ("scripts/stage1_s1", "scripts/stage1_s1/reading",
         "scripts/stage1_s1/reading_input", "scripts/stage1_s1/reading_extra", "scripts/stage1_s1/hlc_draw",
         "runkit/stage1-olmo", "scripts/stage1", "scripts/gate_b_mac_judges", "experiments/safety_selection")}
ver = subprocess.run([py, "-I", "-B", "-c", "import platform, numpy; print(platform.python_version(), numpy.__version__)"],
                     capture_output=True, text=True, check=True).stdout.split()
doc = {"kind": "stage1 outside time stamp manifest: the reading code and runbook (OpenTimestamps)", "version": 2,
       "created_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
       "git": {"head": git("rev-parse", "HEAD"), "trees": trees}, "files": files,
       "kit": {"plan_json_sha256": sha(kit / "plan.json"), "seal_A": sha(kit / "seals" / "block-A.json"),
               "seal_B": sha(kit / "seals" / "block-B.json")},
       "python": {"executable": py, "python": ver[0], "numpy": ver[1]},
       "first_stamp": {"manifest_sha256": "68e75447f7eca032039274bd64641d00625e70ca525f3131a2975c5aad0898c7",
                       "anchor": anchor1}}
with open(out, "x") as handle:
    handle.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
print(json.dumps({"written": str(out), "sha256": sha(out), "files": len(files), "head": doc["git"]["head"]}, sort_keys=True))
EOF
echo "manifest exit $?"
cd "$TS" && "$OTS" stamp "$(basename "$M2")"; print "stamp exit $?"
```

Expect the manifest line with `"files": 72` (M: 33 top-level `*.py` of the four packages at the merge, 13 + 9 + 7
+ 4; 27 listed files; the 4 kit copies; the 8 named files; the printed count is the record), then a `.ots` proof
beside it (the first stamp used `ots -v stamp --timeout 30`, TS/stamp-record-20261031.json:8). A refusal prints
`REFUSED: …` and exits 2: a named file missing (an unfilled `[FILL-S1-RECORD]`), or an uncommitted change under a
pinned path. Commit the manifest and the proof by explicit paths. Wait for the anchor and verify it exactly as step
0.3. Record the manifest's SHA-256 and the anchor in FOCUS (never in this runbook). Nothing that the manifest names
may change after this point; the script's R0 stops on any change (S1).

### Step 0.7: the cost-ledger pre-check (LR R4.5; existence by exact path; no ledger is read)

Before the reading, check that every cost ledger `cost_table` will open exists: for every done host of blocks A and
B and every complete, pulled job, the file `retrieved/HOST/tree/job-I/cost-ledger.json`
(`runkit/stage1-olmo/setup/job_runner_stage1.py:145,880-882`; `RX/cost_table.py:227-256` refuses a complete,
pulled job whose ledger is not in the seal). It reads plan.json's job records and tests paths; it opens no ledger
and walks no folder.

```zsh
date -u
"$PY" -I -B - "$KIT" A B <<'EOF'
import json, pathlib, sys
kit, blocks = pathlib.Path(sys.argv[1]), sys.argv[2:]
plan = json.loads((kit / "plan.json").read_text())
c = {"hosts_done": 0, "jobs_complete_pulled": 0, "ledgers_named_in_plan": 0, "present": 0, "missing": [],
     "other_jobs_with_a_ledger_named": 0, "other_jobs_ledger_missing": []}
for host, h in sorted(plan["hosts"].items()):
    if h.get("block") not in blocks or h.get("done") is not True:
        continue
    c["hosts_done"] += 1
    for i, job in enumerate(h["jobs"]):
        if not isinstance(job, dict):
            continue
        rel = f"job-{i}/cost-ledger.json"
        named = isinstance(job.get("outputs"), dict) and rel in job["outputs"]
        present = (kit / "retrieved" / host / "tree" / rel).is_file()
        if job.get("status") == "complete" and job.get("pulled") is not False:
            c["jobs_complete_pulled"] += 1
            c["ledgers_named_in_plan"] += int(named)
            c["present"] += int(present)
            if not present:
                c["missing"].append(f"{host}:{i}")
        elif named:
            c["other_jobs_with_a_ledger_named"] += 1
            if not present:
                c["other_jobs_ledger_missing"].append(f"{host}:{i}")
print(json.dumps({**c, "pass": not c["missing"]}, sort_keys=True))
sys.exit(0 if not c["missing"] else 1)
EOF
echo "ledger pre-check exit $?"
```

Expect `missing` empty, `present` = `jobs_complete_pulled`, exit 0 (I: every pulled tree holds its ledgers; D1B §5
point 8 names this as the untested real-format risk). A missing ledger does not stop the reading: `cost_table`
refuses at step 4c, the ledger logs exit 2, and the record prints the cost table as "not computed" with the
host:job it names (report only). Record the counts in FOCUS. Who reads what: counts and `host:job` labels only.

### Step 0.8: go / no-go

Start the script only with ALL of: section 3 all as expected on the final tree, reports committed; step 0.1 as
expected; step 0.2 pass (if run); the second stamp anchored with the margin of step 0.3; `$B14IN` at its committed
SHA-256; addendum §39 and §40 and the S1 blinding record committed; FOCUS holds the strata's, similarity's and
inputs file's SHA-256; step 0.7 recorded; the D-7 inputs restored at `$OCT9KEY` and `$V3` (existence checked by
the draw itself; the lead copies them by hash, D2B 12.10 points 3-4); "nothing running"; `$SCR` empty; `$RUN`
absent; `$ROOT/tmp/hlc/draw-$STAMP` absent.

### The script `reading.zsh` (steps R0-5; one background job)

Run it once: `caffeinate -i zsh "$RD/reading-$STAMP.zsh" > "$RD/reading-$STAMP.console.txt" 2>&1` (one Bash call
with `run_in_background: true`). Its one argument is the mode, `coherent` (default) or `no-coherent` (D-5's (c)
route, chosen only at the pre-run, below). It stops at the first failed identity check and prints `STOP at step …`
with the stop rule; steps 4b, 4c and 5 never stop it. Its settings block repeats Block R; `STAMP` and `STRATA_SHA`
are filled before the commit (the stamp pins the filled script). What it checks and in which order:

| Step | Command (the tool) | Must print (exit 0) | Refuses | Outputs | Read by whom |
|---|---|---|---|---|---|
| R0 | the pins heredoc | `{"code_clean": true, "files_differ": [], "kit_same": true, "pass": true, "python_same": true, "trees_same": true}` | a check `false` (exit 1): S1 | ledger lines `R0-start` (the mode), `R0-pins` | the script; no sealed file |
| R1a | `overlap_strata.py report --strata $STRATA --inputs $B14IN --out $SCR/b14-prerun` | nothing on stderr (stdout, the S-p verdicts, is discarded unread) | the settings pin; the strata not at the inputs' SHA-256; a unit's path, pins, frozen sealed check, job fields, identity, G or B+Qi recipe (D-6), `eval/` folder; prompt coverage; summary parity (`overlap_strata.py:319-364`; `limits_common.py:136-171`); messages hold ids, counts, numbers and hashes only: S2 | `$SCR/b14-prerun/` (unopened) | nobody |
| R1b | `reading_input --reading plan_a --kit $KIT --no-overlap --out … --record … --hb-out … [--coherent-out $SCR/prerun-coherent_counts.json]` | the summary of `RI/__main__.py` (ws-a): plan, rules, seals, `cells: U 50, O n, L 50`, 50 `cell` lines, `theta0 O`, `references: … (47 units)`, 47 `reference` lines, `not references: 1; complete (not pulled), not inputs: 4`, `judges A: granite, harmbench; 27 units, 54 indexed files`, `judges B: granite, harmbench; 71 units, 144 indexed files`, `overlap: not included (--no-overlap)`, `not built: token_axis`, `not built: u_variants.coherent`, two `HarmBench` source lines (21,600 and 57,600 records), `HarmBench tables: 51 units; …`, `coherent-only counts: 50 cells x 200 prompts` (or `… not built (no --coherent-out)`), four (three) `wrote … sha256 …` lines | the refusals of `RI/build.py` and `RI/sources.py` (plan code, seals, unit hashes, missing/extra/duplicate units, O-ext pairs, references, judge files, item counts, B16's schema) and `coherent.check` (stderr begins `REFUSED: the coherent-only counts`: D-5's (c) route); any other error prints its type only: S2 | `$SCR/prerun-*.json` (unopened) | the lead reads the log after the run (no value, `RI/__main__.py:12-14`) |
| R1b-check | `lines_check` | `{"identity_lines": 9, "missing_identity": [], …, "pass": true}`; the count lines listed under `missing_count_lines` are reviewed after the run, never a stop | a missing identity line (plan code and plan.json's SHA-256, the rules and B16 settings pins, both seals, the overlap line, each written file's SHA-256): S2 | ledger line | the script |
| 1 | `overlap_strata.py report … --out $RUN/b14` | `wrote overlap_report.json into … (<sha>)` and three lines `  S1|S3|S4: <S-p label>: <holds / not shown on the less similar half> (<reason>)` (`overlap_strata.py:511-517`) | as R1a: S2 (no verdict printed); not byte-identical with the pre-run: S6 | `$RUN/b14/overlap_report.json` (read-only after) | **the first outcome lines (report only)**; the lead reads the log after the script ends |
| 2 | `reading_input … --b14-strata $STRATA --b14-report … --expect-strata-sha256 $STRATA_SHA --expect-report-sha256 … --out … --record … --hb-out … [--coherent-out $RUN/input/coherent_counts.json]` | as R1b with `overlap: strata <STRATA_SHA>, report <REPORT_SHA>` | as R1b, plus the B14 bindings (`RI/build.py:488-525`): S4; an identity line not as pinned: S4; a difference from the pre-run beyond the overlap block and the hashes bound to `tables.json` (`sources.json`'s `output_sha256`, `hb.output_sha256`, `coherent.output_sha256`; the HarmBench tables' and the counts document's `input_sha256`; LR R6.1): S4 | `$RUN/input/{tables,sources,hb_tables,coherent_counts}.json` | the lead (no value printed) |
| 3 | `reading --input tables.json --out $RUN/b16/reading.json` | `wrote …/reading.json (<16 hex>); headline: {'P1': …, …, 'P6': …}` (`B16/__main__.py:35`) | schema, settings pin, REML, existing file (`B16/__main__.py:22-34`): S4; provenance (kind, reading, `input_sha256` = `tables.json`'s, `settings_sha256`, `modules` = the 11 pinned modules and the settings pin, Python, numpy): S5; the re-run not byte-identical: S6 | `$RUN/b16/reading.json`; `$SCR/reading-rerun.json` | **the headline words** |
| 4 | `reading_input.hb_claim --hb hb_tables.json --reading reading.json --out $RUN/hb/hb_claim.json` | `wrote … sha256 <h>` and `sentences: P1 <word>; …; P6 <word>` (`RI/hb_claim.py:286-287`) | tables or reading not bound, settings, contrasts, unknown U words, REML (`RI/hb_claim.py:112-159,200-205`): S4; provenance (`hb_tables_sha256`, `reading_sha256`, `input_sha256`, `modules` = `hb.py`, `hb_claim.py`, `b16_modules`, `b16_settings_sha256`, Python, numpy): S5 | `$RUN/hb/hb_claim.json` | the sentence words |
| 4b | `reading_input.sg_coherent --tables tables.json --counts coherent_counts.json --reading reading.json --out $RUN/sg/sg_coherent.json` (mode `coherent` only) | `wrote … sha256 …` and `S-G coherent headline: P1 <word>; …` (`RI/sg_coherent.py:433-434`) | its bindings (B16's schema; `coherent.check`; `reading.json`'s kind, settings pin, `input_sha256`, `provenance.modules` = the B16 it imports; the sealed contrasts; Φ reproduced): exit 2, **logged, never a stop** (D-5 item 8; §39 8(d)(i)); the provenance check (`tables_sha256`, `counts_sha256`, `reading_sha256`, `modules` = `coherent.py`, `sg_coherent.py`, `b16_modules`, `b16_settings_sha256`, Python, numpy) likewise logged; after a refusal it is not run (no output exists) and its ledger line says `not run: the reader wrote no output` | `$RUN/sg/sg_coherent.json` | the S-G coherent headline words |
| 4c | `reading_extra.cap_reports --kit $KIT --record sources.json`; `fk_power --input tables.json --reading reading.json`; `stage3_pick --reading reading.json`; `sa_shift --reading reading.json`; `cost_table --kit $KIT --reading plan_a`; each `--out $RUN/extra/<name>.json` | each `wrote <file> sha256 <hex>` plus at most words (the stage-3 pick's names; `LN-14 transfer bar: passes|fails|not run|not applicable (Branch full)`) | `RX/common.py` `main_frame`: exit 2, nothing written, **logged, never a stop** (§39 8(d)(i)); the provenance check (`inputs` by SHA-256: `sources.json` for `cap_reports`, `tables.json` and `reading.json` for `fk_power`, `reading.json` for `stage3_pick` and `sa_shift`, none for `cost_table`; `modules` = `RX/*.py` less `__init__.py`, `b16_modules`, `b16_settings_sha256`, Python, numpy; for `cap_reports` and `cost_table` also `kit.plan_sha256` and both seals) likewise logged; after a refusal it is not run and its ledger line says `not run: the reader wrote no output` | `$RUN/extra/{cap_reports,fk_power,stage3_pick,sa_shift,cost_table}.json` | report only; the record copies by key |
| 5 | `hlc_draw draw --kit $KIT --oct9-key $OCT9KEY --bank-manifest $V3/manifest.json --bank $V3/banks/dev.jsonl --auditor $V3/auditor/construction.json --sealed $ROOT/tmp/hlc/draw-$STAMP --manifest $RUN/hlc/hlc_manifest.json`, then `check` with the same arguments | the head lines (plan, both seals, settings, rules, pinned inputs, `units read: 25`, the excluded totals, `drawn (totals): 450 items (harm 360, benign 90); hidden repeats 20` at step 0), three `wrote … sha256 …`; `check`: `<path>: match` three times (`HD/__main__.py`) | plan B; a seal that does not verify; a pinned input not at its SHA-256; the sealed folder or the manifest exists; the sealed folder not under the main checkout's git-ignored `tmp/`; a unit's binding: exit 2, nothing written, **logged, never a stop** (the draw is report-only, rev4:762; its fallback wording is E-misc B ruling 3); the console says `the draw did not run (exit N; 2 = refused, nothing written)` for any non-zero exit, a crash included; `check` mismatch: exit 1, logged | sealed: `$ROOT/tmp/hlc/draw-$STAMP/{hlc_key,hlc_weights}.json` (git-ignored; never opened); committed: `$RUN/hlc/hlc_manifest.json` (text-free) | totals only (LN-31, rev4:763) |
| end | — | `READING STEPS R0-5 DONE` and the ledger's SHA-256 | — | `$LEDGER` | the lead |

Notes on the expected lines (I, from code and R facts; unchanged from R1D:670-677): 50 cells = 6 reused (a0, R at
1101-1103) + 20 in block A + 24 in block B (`RI/build.py:239-256`; rev4:134). Block A's judged units = 26 cells + θ0
= 27; block B's = 24 cells + ref-G 6 + ref-bqi 6 + ref-prefix 7 + Safe LoRA default 7 + ref-scale 21 = 71 (the
certify point is "not a reference", `RI/build.py:476-477`). References printed = 47 units. "not pulled" = LN-15e's 4
units (FOCUS:106). HarmBench records = the judged counts (FOCUS:76, :108). The count lines are logged, not stop
conditions (§39 8(a)): a wrong expectation costs a review line, not a new second stamp. The references line is not
an identity line; a planned reference that is absent prints as a limit beside family 1b in the record (LR R6.5).
The O-cell count is printed, not checked (LN-12 may leave R's reused O cells absent; `RI/build.py:322-328`).

**D-5's (c) route, decided at the pre-run only.** If R1b refuses and its stderr begins `REFUSED: the coherent-only
counts`, the refusal is `coherent.check`'s (ws-a `RI/coherent.py:68-102`; E-records-verify3 D1): no value was shown.
Then, under S2: keep the attempt's console and logs (copy `$RD/reading-$STAMP.console.txt` and `$LOGS` to
`$RD/run-$STAMP-attempt1/`; they hold no value), empty `$SCR`, delete the empty `$RUN`, record the choice in FOCUS,
and run the script again with the argument `no-coherent`. The pre-runs restart without `--coherent-out` (R1b must
pass before step 1), step 2 runs without it (`tables.json` is byte-identical without the flag, ACB:20), step 4b is
not run (the ledger says so), and D-5 goes straight to its last fallback (c), whose paragraph names this cause
(E-D5-D6 §1 item 8 and "Last fallback (c)" trigger (ii)). Any other R1b refusal is the builder's own and follows S2.

### Step 6: records (after the script ends with `DONE`)

1. Read `$RD/reading-$STAMP.console.txt` and the ledger. Only then open the logs and outputs (the 4c outputs and
   the draw's manifest included; never the sealed key or weights file).
2. The reading record, by a mechanical extractor (copies by key; computes nothing; rev4:400). It copies from
   `reading.json`, `hb_claim.json`, `sg_coherent.json` and the step-4c outputs, and the draw's text-free manifest; when
   a step-4b or 4c output is absent or its ledger lines show a non-zero exit, it prints the step's wording with the
   reason copied from the log (§39 8(c); D-5 item 8).

```zsh
date -u
"$PY" -I -B - "$RUN" <<'EOF'
import datetime as dt, hashlib, json, pathlib, sys
run = pathlib.Path(sys.argv[1])
out = run / "reading-record.json"
load = lambda q: json.loads(q.read_text())
sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
ledger = [json.loads(x) for x in (run / "reading-ledger.jsonl").read_text().splitlines() if x.strip()]
code = {e["step"]: e["exit"] for e in ledger}
note = {e["step"]: e.get("note") for e in ledger}

def reason(log):   # the REFUSED line of a step's log, else its last line; the check JSON of a provenance log
    q = run / "logs" / log
    lines = q.read_text().splitlines() if q.is_file() else []
    return next((x for x in lines if x.startswith("REFUSED")), lines[-1] if lines else "no log")

def passed(step, check):   # the step's exit and its provenance check's exit, both 0
    return code.get(step) == 0 and code.get(check) == 0

r, c = load(run / "b16/reading.json"), load(run / "hb/hb_claim.json")
doc = {"kind": "stage1 reading record", "version": 2, "reading": r["reading"],
       "utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
       "mode": note.get("R0-start"),
       "outputs": {q.relative_to(run).as_posix(): sha(q) for q in sorted(run.rglob("*")) if q.is_file()},
       "ledger": ledger,
       "copied_from_b16": {k: r[k] for k in ("headline", "headline_cells", "rows", "phi", "sensitivities", "actors",
                                             "best_feasible_repair", "references", "overlap_control", "label_suffix",
                                             "notes")},
       "copied_from_hb_claim": {k: c[k] for k in ("sentences", "e_hb", "contrasts")},
       "rule": "copied by key from the reading's output documents; nothing computed or typed by hand (rev4:400)"}
SYM = "unscored counted Unsafe in every arm (not Gate B's adverse corner)"
sg = run / "sg/sg_coherent.json"
if passed("4b-sg-coherent", "4b-provenance") and sg.is_file():
    g = load(sg)
    doc["copied_from_sg_coherent"] = {k: g[k] for k in ("readings", "primary", "coherent", "g3a", "g3_unscored_symmetric",
                                                       "sensitivity_part")}
elif code.get("4b-sg-coherent") == 0 and not sg.is_file():
    doc["sg_coherent"] = {"text": "S-G, coherent-only U: not computed at the reading. D-5 went to its last fallback "
                                  "(c) at the no-value pre-run (mode no-coherent); the record carries (c)'s paragraph "
                                  f"with the pre-run's refusal copied from {run.name}-attempt1/logs/R1b-builder-prerun.txt.",
                          "ledger_note": note.get("4b-sg-coherent")}
else:
    why = (f"D-5's reader refused: {reason('4b-sg-coherent.txt')}" if code.get("4b-sg-coherent") != 0 else
           f"D-5's reader's provenance check failed: {reason('4b-provenance.txt')}; its output is not used")
    doc["sg_coherent"] = {"text": f"S-G, coherent-only U: not computed at the reading. {why}. B16's two G3 corners "
                                  f"print as built, labelled \"{SYM}\". This departs from the stage-1 "
                                  "pre-registration, revision 4, section 3.7 item 4."}
KEYS = {"cap_reports": ("readings", "branch", "route_per_source", "ln14", "ln19"),
        "fk_power": ("readings", "model", "contrasts"),
        "stage3_pick": ("readings", "pick", "eligible_in_order", "text"),
        "sa_shift": ("readings", "expected", "measured", "applies", "note"),
        "cost_table": ("readings", "units", "arms", "references", "b10_references", "b10_per_reference",
                       "diagnostics_by_kind", "charging")}
doc["reading_time_readers"] = {}
for name, keys in KEYS.items():
    q = run / "extra" / f"{name}.json"
    if passed(f"4c-{name}", f"4c-{name}-provenance") and q.is_file():
        d = load(q)
        doc["reading_time_readers"][name] = {k: d.get(k) for k in keys}
    else:
        doc["reading_time_readers"][name] = {"not_computed": True, "reason": (
            f"the reader refused: {reason(f'4c-{name}.txt')}" if code.get(f"4c-{name}") != 0 else
            f"the provenance check failed: {reason(f'4c-{name}-provenance.txt')}; its output is not used")}
man = run / "hlc/hlc_manifest.json"
if code.get("5-hlc-draw") == 0 and man.is_file():
    h = load(man)
    doc["hlc_draw"] = {k: h.get(k) for k in ("settings_sha256", "reduction_step", "seed_tags", "totals", "outputs",
                                             "not_built")}
    doc["hlc_draw"]["check_exit"] = code.get("5b-hlc-check")
else:
    doc["hlc_draw"] = {"not_run": "not run at the reading; the draw follows when the human label check is funded "
                                  "(D-7's fallback)", "reason": reason("5-hlc-draw.txt")}
with open(out, "x") as handle:
    handle.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
print(json.dumps({"written": str(out), "sha256": sha(out)}))
coh = (doc.get("copied_from_sg_coherent") or {}).get("coherent", {}).get("headline", {})
for k in r["headline"]:
    print(k, "|", r["headline"][k], "|", "; ".join(r["rows"][k]["u_part"]["words"]), "|", c["sentences"].get(k), "|",
          coh.get(k, "S-G coherent: not computed"))
EOF
```

   The keys are B16's (`B16/reading.py:576-588`; `sensitivities` and `actors` included, so the record is complete
   without `reading.json`), the claim reader's (`RI/hb_claim.py:245-254`; `rows[k].u_part.words`,
   `RI/hb_claim.py:153-158`), the D-5 reader's (`RI/sg_coherent.py:381-396`: the S-G codes of `sensitivity_part`
   and the symmetric table's label are copied, never re-typed, ACB F.1 N5) and the readers' (`RX/*.py`). The printed
   table (words only) is what FOCUS quotes; numbers are quoted from the record. The record states which "differs"
   each column uses: B16's (U-part words only) or the D-5 reader's C7 (words or headline; ACB F.5 item 4).
3. FOCUS (`date -u`): the ledger's SHA-256, each output's SHA-256, the words table, the overlap verdicts, the
   provenance checks, the count lines' review (`missing_count_lines` of `R1b-check.txt` and `2-check.txt`), both
   anchors, and (from the manifest, never from an edit of the runbook) the committed runbook's and script's SHA-256,
   the manifest's SHA-256 and its anchor. Then commit by explicit paths (`$RUN/`, the console file, FOCUS), run
   `commitments.py check`, push, back up to a private release (memory), delete `$SCR`.
4. The third stamp (E-39 point 9; $0): a manifest of `$RUN/` (every file by SHA-256, the ledger and the record)
   that also names the second manifest `$M2` and its check record, written as step 0.6's writer does, stamped with
   the kept `ots` client in `$OTSDIR`, committed by explicit path; verified as step 0.3; then `$OTSDIR` is deleted.
5. Report to the user and go on in the plan's order, as the 31 Oct record says
   (`RD/user_instruction_keep_working_20261031.json:7,13`; §39 point 10). What stays: the money rules, a frozen stop
   rule recorded as a blocker (rev4:887), no stage starts on a result.

## 5. Stop rules and recovery (addendum §39 point 8(d))

- **S1.** Any exit other than 0, or any `"pass": false`, at R0, R1a, R1b, 1, 2, 3 or 4: the script stops; nothing
  after it runs. **Exception:** steps 4b and 4c never stop the script (§39 8(d)(i)), and nor does step 5 (the draw is
  report-only, rev4:762; its pre-set fallback is "no step 5 at the reading", E-misc B ruling 3; §39 8(d)(i) names 4b
  and 4c only, section 7). A non-zero exit, a refusal or a failed provenance check there is logged; the reading goes
  on; the record prints D-5 item 8's wording (4b), "not computed" with the reason (4c) or "not run at the reading"
  (5). A provenance check whose reader wrote no output is not run; its ledger line says so.
- **S2.** A stop at R0, R1a, R1b, or a refusal at step 1 (which prints no verdict): no outcome has been shown. Fix
  the cause, record it, copy the attempt's console and logs to `$RD/run-$STAMP-attempt1/` (no value in them), empty
  `$SCR`, delete the empty `$RUN`. If the fix touches a pinned file, make a new second stamp (step 0.6) and wait for
  its anchor. Then run the script again. The one fix that touches nothing pinned: R1b refused only on the
  coherent-only counts, so the script runs again as `no-coherent` (section 4, "D-5's (c) route").
- **S3.** From step 1's success on: never edit an input, setting, pinned file or output to make a step pass. Never
  re-run a step with other arguments. Never compute a label, word or number by hand (rev4:400; rev4:886).
- **S4.** A stop at step 2, 3 or 4: read only the failing step's log, not `1-b14.txt`, `3-b16.txt` or any output.
  A fix is a post-W1 deviation: an addendum section first, limited to the refusal's cause, with an independent
  read-only review. Keep every output made before the fix and report it. If the fix can change any value, label the
  later outputs post hoc. If it would change a rule or a setting: stop and ask the user (D7 of section 7).
- **S5.** Provenance or hash mismatch at step 3 or 4 (B16's input, settings, modules, Python; the claim reader's
  bindings): stop; no output after it is used; find what changed between steps. At 4b and 4c a mismatch is logged
  and that output is not used by the record (§39 8(d)(i)).
- **S6.** A pre-run or re-run that is not byte-identical (step 1 against R1a; step 3's re-run): stop; the first file
  of step 1 or 3 stays the reading; report the difference as a limit. At step 5 a `check` mismatch is logged as a
  limit.
- **S7.** A label that differs between the primary and a sensitivity is not a stop: the row prints both and the
  primary governs (rev4:275). D-4's S-start prints its words beside (addendum:605). S-G coherent's words that differ
  reach the row's sensitivity part by key from `sg_coherent.json` (rev4:398; D-5 item 6).
- **S8.** A coherence-failing arm is read and flagged, never dropped or re-run (rev4:299-303).
- **S9.** A stamp that does not anchor within 48 h: re-stamp once; then the plan's fallback wording (plan:34).

| Exit | Tool | Meaning | Do |
|---|---|---|---|
| 0 | any | done | next step |
| 1 | a check heredoc; `fail` | a check failed | S2 before step 1; S4-S6 after; logged only at 4b, 4c, 5 |
| 2 | `overlap_strata.py report` | refused, nothing written (`overlap_strata.py:506-509`) | S2 (no verdict printed) |
| 2 | `reading_input` | refused, nothing written (`RI/__main__.py`, ws-a) | S2 at R1b (a coherent-only refusal: the (c) route); S4 at step 2 |
| 2 | `reading` (B16) | refused, nothing written (`B16/__main__.py:32-34`) | S4 |
| 2 | `hb_claim` | refused, nothing written (`RI/hb_claim.py:279-285`) | S4 |
| 2 | `sg_coherent` | refused, nothing written (`RI/sg_coherent.py:426-431`) | logged; D-5 item 8's wording |
| 2 | a `reading_extra` reader | refused, nothing written (`RX/common.py` `main_frame`) | logged; "not computed" with the reason |
| 2 / 1 | `hlc_draw draw` / `check` | refused, nothing written (a failed write removes what it wrote) / a file differs | logged; "not run at the reading" / a limit |
| ≠0 | `ots upgrade` / `stamp` | pending, or no calendar | wait, retry; S9 |

## 6. What the pre-registration says the reading reports, who produces it, and in which order

Order of the record (rev4:103): (1) each repair's label with its O, L and measured cost; (2) the planted control
(stage 1b, not yet run); (3) Gate B and Gate C. Inside (1): P1-P6 rows and words, then references and dominance,
then sensitivities, then report-only items.

| Output | Rule | Producer at the reading | Status |
|---|---|---|---|
| P1-P6 rows: U part, O and L with 90% intervals, feasibility at τ_O 2, 5, 10 and τ_L, coherence flags, sensitivity part | rev4:392-398 | B16 `rows` | built |
| Headline word, by B16 and never by hand | rev4:400-412 | B16 `headline` (`B16/reading.py:584-585`) | built |
| Φ: rejections and local levels | rev4:310-361 | B16 `phi` | built |
| Sensitivities; the primary governs on a difference | rev4:264-275 | B16 `sensitivities`; **S-G coherent-only U by the D-5 reader** (step 4b: V per cell, its seed mean, G2's counts, the U-part words and headline word under its own Φ run, both adverse G3a corners) | built, verified (ACV2); S-tok not run (RI-O3; the record's wording, E-39 point 7) |
| S-start (D-4) | addendum:605 | B16 | built |
| References, "m beats r", family 1b, the curve matched on L | rev4:459-486 | B16 `references` | built (RI-O7, RI-O8 readings in §39 point 3) |
| Best feasible repair; per-actor menus; cost under both conventions | rev4:410, :764-774 | B16 `best_feasible_repair`, `actors`; **`cost_table`** (step 4c: C-full and C-lean per arm and reference, REV4:813 per ref_eval point with a per-reference mean, K6, K7, K2 extended, the split denominator and the anchor job) | built, verified (D1V3) |
| §9.4 overlap control | rev4:757; addendum:604 | B16 `overlap_control` with B14's report (step 1, under D-6) | built; the strata sealed; fallback `--no-overlap` ("not computed", D-6's wording) |
| HarmBench claim: word, HB contrast and 90% interval, E_HB | rev4:205-210; addendum:641-643 | `hb_claim.json` (step 4) | built |
| F_k's planning power at the measured q | rev4:574 | **`fk_power`** (step 4c) | built, verified |
| The stage-3 confirmation pick | rev4:428 | **`stage3_pick`** (step 4c) | built, verified |
| LN-14's transfer bar; LN-19's flag-change shares and routes | rev4:554-555 | **`cap_reports`** (step 4c; opens the O-ext summaries the record names: LR R4.4) | built, verified |
| The S-a shift line | rev4:276 | **`sa_shift`** (step 4c) | built, verified |
| Measured cost per arm | rev4:103, :793-799 | **`cost_table`** (step 4c) | built, verified; limits: the Safe LoRA transform priced by step wall time; pod overhead and judge pods outside the table (LR R4.6) |
| Human label check draw | rev4:762-763 | **`hlc_draw`** (step 5; D-7) | built, verified; sheets, practice items and scorer not built (D2B 12.10 point 8) |
| HB-2 items | rev4:202 | none | not built (`RI/hb.py:52-59`) |
| U_hard, refusal share, Granite greedy | rev4:193 | none | not built |
| O by source; the dev-100 O beside | rev4:194, :758 | none | not built (`cap_reports` prints the routes and flag changes, not O by source) |
| Prompt flips by θ0's refusal stratum | rev4:199, :754 | none | not built |
| Opening-switch composition | rev4:198, :760 | none | not built |
| U by answer-length band; length-reweighted U; selectivity; HarmBench inputs cut at 512 tokens | rev4:758 | none | not built |
| Side-effect prediction (add arms) | rev4:761 | none found | not built (UNVERIFIED) |
| LN-15e | rev4:749-753 | the fallback report (FOCUS:104) | done (fallback) |

The outputs with no code are written after the reading, each labelled "code written after the reading" (R1D's D4
fallback; §39 point 11's wording for a reader not verified before the stamp).

## 7. Decisions for the lead (default, then fallback and trigger)

Resolved since R1D (the ruling, for the record): **D1** (RB1) → D-6, verified and merged (LR R2); **D2** (RB2) →
B's writer and checker, run on 1 Nov (LR R2.3); **D3** (RB4) → D-7's draw at step 5 (LR R5); **D4** (RB7) → the
five readers at step 4c, verified (LR R4; D1V3); **D5** (form and order) → this script with the pre-runs (§39 8(d));
**D6** (the stamps) → the first anchored; the rule of step 0.3 for the second (E-39 point 9); **D8** (test evidence)
→ section 3 (E-plan item 13).

Still the lead's:
- **D7 (failure after step 1).** Default: S3-S6. Fallback: stop the reading and ask the user. Trigger: a fix that
  would change a rule, a setting or how any value is computed (§39 8(f)).
- **The (c) route.** Decided only at the pre-run, by R1b's stderr (section 4). Not a choice to make now.
- **Which B14 set ran** (the 69-entry near set or the full 150-entry spec) goes into D-6's record (E-D5-D6 §2
  point 2); the D-5 spec's full run (47 entries) is part of "verified" (LR R1.2(c)).
- **The S1 blinding record's path** `[FILL-S1-RECORD]` and the merge commit `[FILL-COMMIT]`.
- **Step 5 in §39 8(d)(i).** The record names steps 4b and 4c only (E-39:168-171); this runbook rests step 5's
  never-stop on rev4:762 (report-only) and E-misc B ruling 3. Either add step 5 to 8(d)(i) in the records, or keep
  the two sources as cited here (runbook-verify1.md note 1).
- **Step 0.2 (optional)** parses the seal records and hashes the listed files by exact path, no walk; whether that
  fits the lead's reading of the never-open list is the lead's call (runbook-verify1.md note 9). It is not on the
  script's path.
- **§39 (1c) confirms** this runbook's own readings: the pre-runs, the byte-for-byte re-runs, the stop rules with
  the §39 8(d) exceptions, the mechanical record, the never-open exception at 4c, the cost-ledger pre-check, the
  (c) route at the pre-run, and "report and go on" after the reading (R1D:804-805; E-39 point 8 holds each).

## 8. What this worker ran (all read-only or synthetic), evidence, and what is not tested

| Command | Exit |
|---|---|
| `date -u` (15:21:00, 15:28:15, 15:32:17-29, 15:41:23 UTC on 1 Nov, and once more before this file's header time) | 0 |
| Read: LR; R1D (the committed copy); the build, verify and fix reports of tracks A-E (`reports/`); E-D5-D6, E-39, E-misc, E-plan-updates, E-S1-blinding (header); the code of the five worktrees named in section 2 (ws-a `RI/__main__.py`, `sg_coherent.py`, `coherent.py`; ws-b `overlap_inputs.py`, `overlap_inputs_check.py`; ws-c `plan_tool.py` record-done, `seal.py`, `job_runner_stage1.py`; ws-d1 `RX/README.md`, `common.py`, the readers' output blocks; ws-d2 `HD/__init__.py`, `__main__.py`, `draw.py`); at `55d5f8b` via `git show`: `RI/__main__.py`, `B16/__main__.py`, `B16/settings.py`, `B16/reading.py`, `RI/hb_claim.py`, `overlap_strata.py`, `seal.py`, FOCUS:72-80, rev4:299-303, :398-412, :757-764, :884-888, plan:36-50, the keep-working record; `tmp/gi-vii-notes/blockB_S.zsh` | 0 |
| `git -C ROOT` log, status, diff --quiet/--stat `55d5f8b..HEAD` (code paths), rev-parse `HEAD:<tree>`, ls-files `RD/` (names only) | 0 / 1 (the diff: B and C are merged) |
| `shasum -a 256` of the files in section 2, in the worktrees and the main checkout; the live kit's `{stage1_rules,seal,plan_tool,judge_units_stage1,finisher}.py` and `setup/job_runner_stage1.py` (code only) | 0 |
| the venv's Python printing its own and numpy's version; B16's `module_hashes()` and `_strip` on the real package (code only, no data) | 0 |
| `zsh -n reading.zsh` (zsh 5.9); `ast.parse` on its 5 heredocs; the helper functions `ledger`, `lines_check`, `prov` and the step-2 comparison run on a synthetic world (`builds/tmp/runbook-check/synth2/`: fake files, a fake manifest, fake outputs with provenance blocks; one planted seal difference and one absent file each refused; `noclobber` refused an overwrite) | 0 as expected (1 where a refusal was expected) |
| `zsh -n` on this file's 10 zsh blocks; `ast.parse` on its 5 heredocs (the seal check, the requirements writer, the manifest writer, the ledger pre-check, the extractor); the ledger pre-check on two synthetic `plan.json` worlds (one ledger present, one missing: pass, then `missing ["a-1:0"]`); the extractor on a synthetic run folder (a refused `cost_table` printed as "not computed" with its REFUSED line; a failed 4b provenance check printed as D-5 item 8's wording; a second run refused by the exclusive create) | 0 as expected (1 where a refusal was expected) |

Fix round 1 (1 Nov, 16:22-16:40 UTC; evidence under `builds/reports/runbook-fix1-dryrun/`, 31 files):

| Command | Exit |
|---|---|
| `date -u` (16:22:54, 16:34:53-16:36:05, 16:37:14 UTC); the verifier's report; `git -C ROOT` log, status (code paths: clean), rev-parse `HEAD:<tree>`, `show --stat HEAD`, `show 55d5f8b:B16/reading.py` (:535-595), `show 55d5f8b:TS/stamp-record-20261031.json` (:1-45), `show HEAD:…/tools/ots_check.py`, `show HEAD:TS/ots-check-20261101.json` (head), `ls-files` of `TS/` and `tools/` (names); E-misc B, E-39:160-200; R1D's markers (grep `FILL`) | 0 |
| `zsh -n reading.zsh`; `check_blocks.py`: `ast.parse` of the script's 5 and the runbook's 5 heredocs, `zsh -n` of the runbook's 10 zsh blocks | 0 |
| the dry run, repeated on a fresh synthetic world (`builds/tmp/runbook-fix1/`, deleted after): ws-a's `synth_kit` by the verifier's `build_world.py`; code by symlink to the main checkout (`experiments/`, `scripts/stage1`, B16, the merged `stage1_s1` files, `runkit/stage1-olmo`), the three packages copied from ws-a, ws-d1, ws-d2; the verifier's stand-in `git`; the manifest writer and the extractor extracted from this file; three copies of `reading.zsh` by `make_copies.py` (7 lines edited; the third also points step 4b's `--counts` at a missing file) | manifests: 0, 0, 0 (`"files": 72` each); runs `20261199` coherent, `20261198` no-coherent, `20261197` coherent with 4b refusing: 0, 0, 0 (`READING STEPS R0-5 DONE`, 29 / 28 / 29 ledger lines); extractor 0, 0, 0 |
| checks on those runs: the console holds only mode, step and STOP-kind lines, JSON, dates and the ledger hash; `4c-cap_reports-provenance` and `4c-cost_table-provenance` logged as `not run: the reader wrote no output (its exit 2)` with no console noise; run `20261197`: `4b-sg-coherent` exit 2 (the reader's own `REFUSED` line), `4b-provenance` exit 1 "not run", no `4b-provenance.txt`, no `sg/` output, the record carries D-5 item 8's wording with the REFUSED reason; run `20261198`: the (c) wording names `run-20261198-attempt1/logs/R1b-builder-prerun.txt`; the record's `copied_from_b16` holds `sensitivities` and `actors`; none of the 7 distinct words of the records' headlines, sentences and U-part words appears in any console; the normalized diff against the verifier's round-1 console differs only by the two notes and step 5's line | as expected |
| the writer's refusals: an unfilled `FILL-S1-RECORD` → `REFUSED: a named file is missing …`, exit 2, nothing written; a stand-in `git` whose `status` prints a change → `REFUSED: a pinned path has an uncommitted change …`, exit 2, nothing written | 2, 2 (as expected) |
| `rm -r builds/tmp/runbook-fix1` (58 MB: the symlinked root, the synthetic kit, the runs) | 0 |

Not tested: every tool on real data; the `ots` client and `ots_check.py` on the second stamp; every duration marked
E; the expected count lines (I); B14's `report` inside the script (no B14-compatible synthetic kit exists beside the
builder's world; a copy of a synthetic report stood in at R1a and step 1, as in the verifier's dry run); the draw's
success path (its inputs are absent from the world; it refused as designed). The provenance checks ran against the
tools' real outputs on the synthetic world (`prov` all true at steps 3, 4, 4b and 4c's three successful readers).

## 9. Changes from R1D (each with its source)

1. **Step 2 and R1b take `--coherent-out`; step 4b runs `sg_coherent`.** The builder prints `coherent-only counts:
   50 cells x 200 prompts` and a fourth `wrote … sha256 …` line (ACB §8 item 1). The pre-run takes the same option
   with `--no-overlap` in place of the four B14 options (LR R6.1; E-plan item 3). Step 4b never stops the reading
   (D-5 item 8; §39 8(d)(i)); D-5 is verified (ACV2), so 4b runs.
2. **The step-2 comparison leaves out the counts document's hashes** (`sources.json`'s `coherent.output_sha256`, the
   document's `input_sha256`) and compares the rest of the counts document (LR R6.1; E-D5-D6 item 4;
   E-records-verify3 D1's reproduction). It pops `overlap` from both tables documents, not only the step-2 one.
3. **D-5's (c) route at the pre-run:** the script's `no-coherent` argument; the pre-runs restart without the option;
   step 4b is skipped with a ledger note; the record's wording (E-D5-D6 item 8 and last fallback (c) trigger (ii);
   E-records-verify3 note 3).
4. **Step 0.4's heredoc is replaced by B's writer and checker**, already run; the paths are `RD/b14/inputs/
   overlap_inputs.json` and `RD/b14/strata/strata.json` (BBB §8; LR R2.3; the lead's commit `b5e3c27`, names only).
5. **The "never changes" list takes round 34's hashes** of `stage1_rules.py` (`4005cb4e…`) and `plan_tool.py`
   (`27e299b5…`); `seal.py` and `judge_units_stage1.py` unchanged (LR R3.2; CKB §8 item 1). Step 0.1 expects them.
6. **`retrieved/` is never listed** (LR R3.1): step 0.2 hashes listed files by exact path and drops the `not_listed`
   walk; the strata step ran in place on the path `record-done` printed; the copy is `RD/b14/similarity.json`.
7. **Step 4c, the five reading-time readers**, report only, inside the script, each bound to its inputs by SHA-256
   (`fk_power`, `stage3_pick` and `sa_shift` to `reading.json`; `cap_reports` to `sources.json`; `cost_table` to
   `plan.json` and the seals: D1's design, D1V3) and logged, never a stop (LR R4, R6.3; §39 point 11; E-plan item
   9). `cap_reports` and `cost_table` carry the never-open exception (LR R4.4). `cost_table` is verified after fix
   round 2 (D1V3).
8. **Step 0.7, the cost-ledger pre-check** by exact path, existence only (LR R4.5; §39 8(h)).
9. **Step 5 runs D-7's draw and its check**, with `OCT9KEY=$ROOT/tmp/hlc-inputs/oct9/key.json`,
   `V3=$ROOT/tmp/hlc-inputs/prepared-v3-inj05`, `mkdir -p $RUN/hlc`, the sealed folder under the main checkout's
   `tmp/` (D2B §8, 12.2 point 4; LR R5.5; E-misc B). The draw's suite is re-run after A's merge.
10. **The provenance checks are corrected.** R1D compared B16's `provenance.modules` (and `b16_modules` at step 4)
    with every file under `scripts/stage1_s1/reading/` in the manifest, `__init__.py` and `__main__.py` included
    (R1D:612-617, :638-645). B16's `_strip` drops keys that start with `_` (`B16/reading.py:539-542`; ACB §8 item 7;
    M on the real package: 12 keys after `_strip`), so R1D's check would have stopped a correct reading at step 3
    (S5). The script's `prov` expects the 11 modules plus `settings/reading.json`, for B16 and for every reader's
    `b16_modules`, and a reader's own `modules` without `__init__.py`.
11. **Stop on identity lines only; the count lines are logged** (`lines_check` prints `missing_count_lines`, never
    fails on them; §39 8(a); CRIT:224-225). The references line is not an identity line (LR R6.5).
12. **S1 and S5 gain the 4b/4c/5 exceptions; S2 keeps the attempt's logs** (§39 8(d)(i); E-D5-D6 item 8).
13. **The script sets `ROOT`, `KIT` and `PY` itself** instead of sourcing `tmp/gi-vii-notes/blockB_S.zsh`: the
    stamp pins the script, not an untracked settings file (the values are the same, M).
14. **`setopt noclobber`:** every file the script writes with `>` is an exclusive create, as the tools' outputs are
    (the brief; M: an overwrite is refused).
15. **Every step's exit code is in the ledger**, the mode too (`R0-start`), the `cmp` results (`1-same-as-prerun`,
    `3b-same-as-rerun`) and the non-stopping steps' exits (the brief).
16. **The manifest writer pins the new packages, settings and specs** (`reading_extra/`, `hlc_draw/` with
    `settings/hlc_draw.json`, `overlap_inputs.py`, `overlap_inputs_check.py`, the four new specs), the B14 records,
    the addendum, the S1 blinding record and the study plan (E-plan item 8); version 2; the first stamp's anchor is
    a literal (FOCUS:74).
17. **Step 0.3 becomes the verification rule for the second stamp** (the first is anchored, FOCUS:74; E-39 point 9:
    6 confirmations and 2 h; keep the client; a third stamp after the records).
18. **Step 6's extractor copies from `sg_coherent.json` and the 4c outputs by key**, prints D-5 item 8's wording or
    "not computed" with the reason when a step failed, copies the draw's totals, and prints the S-G coherent headline
    in the words table (§39 8(c); D-5 item 8; ACB F.5 item 4). Step 6 ends with the third stamp and "report and go on"
    (§39 points 9-10).
19. **Section 3's suites and specs** take the build round's counts: `ri` 284, `rx` 120, `hlc` 123 + 3, `kit` 735,
    the 47-, 62- and 65-entry specs, the B14 near set, round 34's 39 ids; B16's spec need not run again (E-plan
    item 13).
20. **Section 0's gaps are closed** as the build round left them; section 7 lists D1-D6 and D8 as resolved.

Fix round 1 (runbook-verify1.md: the defect D1 and notes 1-8, 13, 14; one further point found while fixing):

21. **The fill markers are split** (D1). R1D's `[FILL-0]` ("at step 0", R1D:28) covered the stamp's date and the
    values that exist only after the commit and the anchor (the runbook's and script's SHA-256, the manifest's
    SHA-256 and anchor, the height). Now `[FILL-STAMP]` is filled before the commit (Block R, section 3, the script's
    settings block), and the post-commit values are never written into the runbook: the manifest, FOCUS and
    `TS/ots-check-reading-$STAMP.json` hold them, and the third stamp binds them (the markers table; steps 0.3, 0.6,
    6). An edit after step 0.6 would make R0 stop (S1), as the verifier reproduced.
22. **Step 0.3 reads the height from the proof, by the lead's `ots_check.py`** (`RD/lead-reports-20261101/tools/`,
    used for the first stamp; its record format is `TS/ots-check-20261101.json`), in place of a height typed by hand
    and a `curl` loop (D1). The `ots` client goes into its own folder `$OTSDIR`, not `$SCR`: R0 requires `$SCR` empty,
    and the client is kept until the third stamp is verified (found while fixing D1; the first stamp's client was a
    scratch venv that was not kept, `TS/stamp-record-20261031.json:38`).
23. **The manifest writer refuses as the tools do** (`REFUSED: …`, exit 2) for a missing named file (an unfilled
    `[FILL-S1-RECORD]`) and for an uncommitted pinned path (verifier's reply 5); the expected count is 72 files (M;
    note 3).
24. **A provenance check with no output to check is not run** (steps 4b and 4c, after a reader's refusal); its
    ledger line says `not run: the reader wrote no output (its exit N)` with exit 1, and the console no longer prints
    a "provenance check exit 1" line for a file that does not exist (note 5). The extractor's branches are unchanged:
    a refused reader prints its REFUSED line.
25. **Step 5's console line says "did not run (exit N; 2 = refused, nothing written)"** for any non-zero exit, a
    crash included (note 6), and its never-stop cites rev4:762 (report-only) and E-misc B ruling 3, since §39
    8(d)(i) names 4b and 4c only (note 1; section 7 asks the lead to add step 5 to 8(d)(i) in the records).
26. **The extractor copies B16's `sensitivities` and `actors` too** (`B16/reading.py:586-587`; note 7), and the (c)
    wording names the attempt folder as `run-<STAMP>-attempt1/logs/R1b-builder-prerun.txt`, as S2 names it (note 14).
27. **The ledger is created once, then appended** (`"x"` on the first line, `"a"` after; note 13): the one file the
    script writes more than once, stated in its header.
28. **Section 1's state is HEAD `c21dccb`** (note 2); **step 0.5 says the rehearsal runs an edited copy** with a
    stand-in `git`, with the verifier's dry run as the worked example (note 4); **change 7 names each reader's own
    binding** (note 8).

Unchanged from R1D: the pre-runs R1a and R1b, the byte-for-byte checks of steps 1 and 3, the B16 and claim-reader
commands, `--hb-out`, the mechanical record's rule, S3, S4, S6-S9, the exit table's first six rows, section 6's
list of outputs with no code, and "report and go on" (RB11).
