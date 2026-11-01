# Verification of track E-records (round 3, after fix round 2)

- **Written** 2026-11-01 by an independent verifier for the lead (GI VIII); clock checked with `date -u` at 14:33,
  14:37, 14:45, 14:46 and 14:47 UTC. Self-identification is not verification; the launcher records routing.
- **Checked:** the six drafts in `builds/reports/` at these SHA-256 (first 16; each equals the build report's G6
  table): `E-39.md` `c659161c85b3020a`, `E-D5-D6.md` `418c2372a56d90d5`, `E-S1-blinding.md` `8128cac6c45448b4`,
  `E-misc.md` `da538abaa80eda1c`, `E-40.md` `26fd943d20ff408f`, `E-plan-updates.md` `13c52b0057684ca2`; the build
  report `E-records-build.md` `b5b00b8ea4e934ea`; the checker `E-fix-checks/check_records.py` `a13cb1b9f626eab5`;
  the lead's rulings `lead-rulings-20261101.md` `3096e37a09ac565a`.
- **Sources** read at `55d5f8b` with `git -C <main checkout> show 55d5f8b:<path>`; the design round's copies at
  `0e0ab1f` (byte-equal to the scratch copies: 8 of 8 hashes, M); the build round's reports in `builds/reports/`;
  track A's code in `builds/ws-a` (HEAD `55d5f8b`, 10 changed paths before and after, not edited). The main checkout
  is now at `53f746d` (D-6 and kit round 34 merged), so `git diff --quiet 55d5f8b HEAD -- scripts runkit experiments`
  exits 1; the drafts cite `55d5f8b`, so this changes nothing below.
- **Scope kept.** I edited no draft, no repository file and no other track's worktree. I wrote only under
  `builds/verify-E-records/v3/` and this report. Git read-only only (`show`, `log`, `rev-parse`, `diff --quiet`,
  `status --short | wc -l`, `ls-files` of the committed `lead-reports-20261101/` folder). No network, install, pod or
  API call; no reading, builder, overlap, claim, judge, seal, kit, draw or launch command on real data; no background
  job. Nothing on the never-open list was opened, listed, grepped or hashed. The two NOTES records were opened by
  exact path only (`sed -n` of cited lines, `shasum`, `test -e`), as the round-2 verifier did; no listing of that folder.

Tags: (M) measured or checked here; (R) read in a source; (I) my inference.

## Verdict: verified

The three round-2 defects are fixed as R6.1, R6.2 (= R1.2(a)) and R6.3 rule. Every ruling in R1-R6 that a record
must state is stated, and each matches the rulings file (section 2). The twelve notes are fixed, or not adopted with
the lead's reason (section 3). `check_records.py` passes when I run it (914 citations in range, 244 of 244 phrases,
14 of 14 "Old" blocks once, 8 committed-copy hashes equal, 0 stale phrases). My own checks of about 90 citations
against their sources at `55d5f8b`, `0e0ab1f` and the build-round reports all hold (section 4); every quoted stated
reading matches its source (section 5). Nothing in the drafts reveals or depends on a stage-1 outcome or a sealed
choice (section 6). The decisive synthetic check of R6.1's pre-run rule on track A's builder passes (section 1, D1).

Six minor points are notes (section 8), not defects: a stale mutation count, an understated "at least one" world,
one implied restart clause, one shortened reading, a stale HEAD note, and fill values that can now be filled.

## 1. The three defects, against the rulings

### D1 (R6.1: the builder half and the pre-run)

- **Ruling (R).** R1b takes the same `--coherent-out` option as step 2; the step-2 comparison leaves out the counts
  document's hashes; plan item 3 says "a no-value pre-run with the same options, `--no-overlap` in place of the B14
  options"; §39 8(d) gains a third change; D-5 item 8 says the reader never stops the reading and the builder half is
  settled at the pre-run; a pre-run refusal only on a coherent-only check sends step 2 on without the option and D-5
  straight to (c), chosen before any value; (c)'s paragraph names that cause.
- **The drafts (R).** `E-D5-D6.md` item 4 (:88-93) and item 8 (:108-124), last fallback trigger (ii) (:164-167) and
  the trigger-(ii) sentence (:175-177); `E-39.md` 8(d)(iii) (:172-178); `E-plan-updates.md` item 3 (:57). Each says
  what the ruling says. The key names are the builder's: `sources.json` holds `coherent: {cells, items, output_sha256}`
  (ws-a `__main__.py`:93-94, :130, M) and the counts document holds `input_sha256` (ws-a `coherent.py`:35, :54, M).
  The counts' checks read only the coherence block and the U table (`coherent.py`:97-102, M), and `build()` runs them
  after B16's schema check (ws-a `build.py`:701-713, M), so a refusal there is "only on a coherent-only check" and its
  message begins "the coherent-only counts" (`coherent.py`:68-102, M).
- **Reproduction (M, synthetic kit only).** `v3/checks/prerun_rule_check.py` in `builds/ws-a` (venv Python, `-B`,
  `PYTHONDONTWRITEBYTECODE=1`; scratch 49 MB under `builds/tmp/`, deleted): exit 0, `PASS`.
  - R1D:582-598's comparison as drafted, R1b and step 2 both with the option: `sources_equal` **false**
    (`coherent.output_sha256` `08632ccd…` against `7bd9335d…`, the round-2 verifier's case B). With the drafts' rule
    (that key left out): `tables_without_overlap` true, `sources_equal` **true**.
  - `tables.json` is byte-identical with and without the option, for the pre-run and for step 2 (two SHA-256 pairs).
  - The counts document's `input_sha256` equals the SHA-256 of its `tables.json` in both runs; its `cells` are equal
    across the overlap block; the two `tables.json` differ by the overlap block only.
  - A corrupted screen count (the builder's own test's change): exit 2, stdout empty, stderr `REFUSED: the
    coherent-only counts of A1 1102: the answers failing the screen are not the coherence block's failing count`, and
    the output folder stays empty. The same build without the option: exit 0, and its `tables.json` equals the
    pre-run's. That is the (c) route as item 8 states it.
  - Track A's `tests/test_coherent.py`: **42 passed in 8.04 s** (basetemp 74 MB, deleted).

### D2 (R6.2 = R1.2(a): the coverage gate)

- **Ruling (R).** The gate is plan A; every contrast in every simulated world must meet the band 0.88-0.92 and the
  tail ratio (at most 1.5 × the primary form's in the same world); at least 2,000 replicates per world, and 10,000
  where a world's 2,000-replicate coverage is within 2 MC SE (0.0134) of a band edge or its tail ratio is above 1.3;
  plan B checked and reported; block A only a limit, not a trigger (RI/build.py:606-607; B16's primary form outside the
  band there). R1.2(b): estimates to 1e-9 pp; SE and df to 1e-6 relative where the reference fits REML on its own.
- **The drafts (R).** `E-D5-D6.md` item 9 (:125-146) states the gate, the replicate rule, plan B, block A only, the
  tolerance and R1.2(c)'s spec run, each as ruled; plan item 7 (`E-plan-updates.md`:110) takes the same scope.
- **Checks (M).** RI/build.py:606-607 at `55d5f8b` is the refusal ("block B is sealed: the block-A-only reading is for
  a stage 1 without block B"). Track A's synthetic files: `A-coherent-sim-plan_a-2000.json` (reps 2,000; target
  coverage [0.88, 0.92], tail ratio ≤ 1.5): 18 of 18 contrast-worlds meet the target; S-G coherent coverage
  0.8915-0.909; pooled tail ratio per ACB:253 0.93; per-contrast tail ratios 0.609-1.353. `…plan_b-20000.json`:
  6 of 6, coverage 0.8954-0.9038, ratios 0.77-1.14. `…block_a-2000.json`: 8 of 18, coverage 0.876-0.900. ACB:253-255
  and :260-262 say the same (M). The record's "lowest coverage 0.891 is within 0.0134 of 0.88" (0.8915 − 0.88 =
  0.0115) and "highest tail ratio 1.35 is above 1.3" (1.353, world i P5) hold; see note 2 for the count of worlds.

### D3 (R6.3: the reading-time readers in the plan)

- **Ruling (R).** Step 4c with the five outputs (REV4:574, :428, :554-555, :276, the cost per arm) plus `cap_reports`,
  each bound to `reading.json` by SHA-256, report only, inside the reading script (R4.4's exception); fallback
  "code written after the reading"; added to items 8, 9, 11 and 13.
- **The drafts (R).** `E-plan-updates.md` step 4c (:156-163) names the five, `cap_reports` and `cost_table`, the
  binding, "report only", "run only inside the reading script here", the exception and the fallback label; item 8
  (:123, `reading_extra/`), item 9 step 0 (:135-141, with the R4.5 pre-check), item 11 (:185), item 13 (:211). §39
  point 11 (`E-39.md`:227-258) holds the readers' record (R4.1-R4.6) and 8(h) the pre-check (R4.5); S1 record row 15.
- **Checks (M).** REV4:574 (F_k's power at the measured q), :428 (the pick rule), :554-555 (LN-14, LN-19), :276
  (the S-a shift), :103 ("measured cost"), :813 ("For an evaluation-only reference: the same minus training, plus its
  transform"), :823 ("a study cost") all hold at `55d5f8b`. D1B:17-25 lists the five modules; D1B:60-71 and :129-133
  (cap_reports reads the sealed O-ext summaries, "reading C5"); D1B:75-80 and :307-308 (cost_table opens plan.json,
  the seals and the cost ledgers under `retrieved/`); D1V:16-21 (four readers verified; one low defect in cost_table).

## 2. Every ruling a record must state

| Ruling | Where stated | Check (M) |
|---|---|---|
| R1.1 (re-verify runs now; no second fix round) | D-5 facts (:57), (c+) (:157-158), plan item 7 | matches LR:13-14 |
| R1.2(a) coverage gate | D-5 item 9 (:134-146); plan item 7 | matches LR:16-22 word for word in substance |
| R1.2(b) tolerance | D-5 item 9 (:130-131); plan item 7 | matches LR:23-24; ADD:425 "below 1e-6" holds |
| R1.2(c) the 47-entry spec as the lead's run | D-5 item 9 (:127-128) | LR:25-26; ACB:355, :440 say 47 entries |
| R1.3 (c+) built on a defect; (c) if (c+) not verified at the manifest | (c+) (:161-162); (c) trigger (i) | matches LR:27-30 |
| R2.1 settings-only deny-list limit; no accepted list | D-6 item 1b | matches LR:34-37; BBB:17, BBV:145-147 hold |
| R2.2 150 entries; 69 near set before the stamp; which set ran | D-6 item 2 (`[FILL]` for the set) | LR:38-39; BBB:16 (87 → 150: 63 new, 6 re-pinned), :234 (69 entries, `77c3def1…`) hold |
| R2.3 order | D-6 item 3 | LR:40; BBB:276 holds |
| R3.1 `retrieved/sim-1/` by exact path and SHA-256; copy script; no outcome; process.log; never list | `E-misc.md` A ruling 3; plan row 1b; `E-40.md` point 3 | LR:44-48; CKB:349-351, :356-357, :365-367 hold |
| R3.2 the two new hashes; seal.py and judge_units unchanged | `E-misc.md` A ruling 2; plan row 1b | LR:49-50; CKB:31-32 hold |
| R3.3 equality checked by C's verifier, not pinned | `E-misc.md` A 2b; plan row 1b | LR:51-52; CKV:37, :137, :190 hold; the first draft's claim withdrawn (stale phrase check 5) |
| R3.4 N5 accepted; re-run, one-off pod, `--no-overlap` | `E-misc.md` A fallback | LR:53-54; CKV:135, :201 hold |
| R3.5 C's `git ls-files` print | `E-misc.md` D.1 | LR:55-56; CKB:404-406, CKV:246-248: names only |
| R4.1 four readers verified | §39 point 11 | LR:60; D1V:16-21 |
| R4.2 cost_table's fix round and fallback | §39 point 11 | LR:61-68 (REV4:813 quoted exactly, M) |
| R4.3 adopted readings K6, K7, study costs, K2 extended | §39 point 11; S1 row 15 | LR:69-72 |
| R4.4 never-open exception at step 4c only | §39 point 11; plan 4c; `E-40.md` point 3 | LR:73-76 |
| R4.5 ledger pre-check, existence only, never stops | §39 8(h); plan step 0 | LR:77-78 |
| R4.6 limits | §39 point 11 | LR:79-80 |
| R5.1 readings 4, 7, 11, 12, 13; 106 terms, 5 age patterns; benign label | `E-misc.md` B 2b | LR:84-87; D2B:373-386, :357 hold (note 4 on reading 7's wording) |
| R5.2 cross-seed loss 6-13% at U 0.03-0.05, q 0.2; weights granularity | `E-misc.md` B 2c | LR:88-90; D2V:52-66 (40/300, 33/300, 21/300, 18/300 = 6-13%), :67-79 hold |
| R5.3 HLC 4.3 item 4 as the same code in a second process | `E-misc.md` B ruling 2 | LR:91-92; D2B:250, D2V:80-83; the tool prints "match"/"mismatch" per path and totals (ws-d2 `__main__.py`:166, M) |
| R5.4 the deadline and the late build | `E-misc.md` B ruling 1 | LR:93-94; FOCUS:125-126 "created 11:04:34" (M); D2B:26-31 |
| R5.5 step 5; `tmp/hlc-inputs/`; suite re-run after A's merge | `E-misc.md` B ruling 2; plan item 4 | LR:95-96; D2B:248-249 |
| R6.1-R6.3 | section 1 | — |
| R6.4 hard-rule notes | `E-misc.md` D.1-D.3; §39 8(g) | LR:116-118; D2B:210-213 (shards 2, 3b, 3c: 11, 4, 3 mutants; exit 0) |
| R6.5: the `55d5f8b` pin, no remap | every header | LR:120 |
| R6.5: references not an identity line | §39 8(a); RI-O8 row | LR:121 |
| R6.5: tie tolerance adopted | `E-40.md` point 1 | LR:122-123; EV2:179 "627 of 2,000" (M) |
| R6.5: no pilot fallback | `E-40.md` point 2 | LR:124 |
| R6.5: F9 as written | `E-40.md` point 9 | LR:125; REV4:710, W1R:296, build_plant.py:30 hold |
| R6.5: ADD:428 copies committed | `E-misc.md` C ruling 3 | LR:126-128; NOTES hashes `65fe90c3…`, `4090118e…` (M) |
| R6.5: SPF:344 adds D-5 to D-7 | S1 record §5 | LR:129-130; SPF:344 lists D-1 to D-4 and §38 (M) |
| R6.5: pinned texts unchanged | D-6 fallback; §39 point 7 | LR:131-132; reading.json:200, README:68, RI/__main__.py:45-46, :58-59 name "addendum 24 point 4" (M) |
| R6.5: committed copies cited | the short-name tables of all six drafts | LR:133-137; 0 scratch paths left (M) |
| R6.6: E's round-1 grep as a disclosure | `E-misc.md` D.3 | LR:139-141 |

## 3. The twelve notes

| Note | Fixed? | Check (M) |
|---|---|---|
| 1 S3/S4 times | yes | `E-misc.md`:42 "S4's edit file dates from 25 Oct 15:42 UTC and S3's from 16:46 UTC"; R1B:69-74 says so |
| 2 "can only mean" | yes | `E-misc.md`:39-44 reads W1R:129 as B14's code, cites R1B:61 "build deadline only"; "the ruling stands either way" |
| 3 D-6's second trigger | yes | `E-D5-D6.md`:239 "(added, beyond the brief's trigger; CRIT:347; R1D:783)"; both sources hold |
| 4 the relabel text | yes | item 7 quotes `SYMMETRIC_LABEL` exactly (ws-a `sg_coherent.py`:72; pinned at `test_sg_coherent.py`:508, M) |
| 5 §40 point 10 wording | yes | `E-40.md`:158-163 as the verifier proposed, the four cases of points 3 and 5 named |
| 6 row 13 vs §40's S1 line | yes | row 13 adds "K7 after a 'go' (point 6)"; §40's line names 1, 2, 4 and 6 |
| 7 §37 points 4-6 and the conditional rules | yes | "Not listed" names ADD:644-646, :594, :616, :620; each line holds |
| 8 `zphi.py` | yes | `E-misc.md`:198-200; the script exists (`test -e`); `b16-verify-stats.json`:367 names it |
| 9 D-7's inputs | yes | `E-misc.md`:119-125; D2B:37-41 holds; the `tmp/hlc-inputs/` paths are from LR:95-96 |
| 10 the builder's two texts | not adopted, by LR R6.5, with the reason | `E-39.md`:128-130; D-6 fallback names :58-59 |
| 11 the extractor | yes | `E-39.md`:160-163, step 4c's outputs included |
| 12 status | answered by R1.1 | D-5 facts, (c+), plan item 7 |

## 4. Citations I checked (all hold)

- **REV4** at `55d5f8b`: :29, :79, :103, :158, :264, :266, :270, :271, :275, :276, :285, :301, :302, :398, :400,
  :409, :410, :428, :554, :555, :562, :574, :675, :684, :698, :699, :706, :710, :743, :757, :762, :763, :813, :823,
  :878, :883, :886, :887, :896, :919.
- **ADD**: :375, :425-428, :435, :457, :470, :503, :508, :522, :594, :605, :616, :620, :625, :633, :635, :641-646,
  :657. **W1R**: :129, :243, :291, :293, :296, :358. **HLC**: :3, :157, :164-168. **SPF**: :344. **PREREG**: :148-149.
  **KW**: :1-14. **LEDGER**: :70, :72, :74, :387.
- **FOCUS** at `55d5f8b`: :74 (recorded 04:46 UTC), :75, :76, :77, :99, :104, :107, :108, :109, :113, :125 and :126
  ("created 11:04:34"; σ̂ 1.78 pp), :131, :135, :136, :137, :138, :139, :140, :144. At `a494ff7` the design-round
  entry sits at :76 (two higher than :74), as the headers say; at `53f746d` the anchored-stamp entry is at :78.
- **PLAN**: :30-34, :39-49, :57, :70, :72 (the "Old" blocks; the checker finds each once).
- **Code** at `55d5f8b`: RI/build.py:7-13, :84-89, :271-272, :604-608, :673-674; RI/__main__.py:27-28, :40, :45-47,
  :58-59, :88; RI/items.py:6-8, :115; RI/hb_claim.py:4, :40-45; B16/reading.py:313-315, :534-535;
  B16/settings/reading.json:200; B16/README.md:68, :153-155; B16/contrast.py:84-85; build_plant.py:30.
- **Design round** at `0e0ab1f`: R1D:519-529, :537-541, :552, :571-575, :581-600 (the `pop` lines :589-594), :607,
  :718-738 (S1 :720, S2 :722-724, S3 :725-726, S4 :727-730, S6 :733-734), :783-789, :801-805; R1B:61, :69-74,
  :101-103, :148-150, :155-156, :163-164, :179-189, :253-256; CRIT:142-143, :224-226, :243, :345-355; V1A:209-211,
  :227-229, :295-296, :349-350, :361-364; D1A:498-511; CHECK:122-130, :155-156, :187-191, :267-269, :313-315, :363;
  READY:357-359.
- **Build round**: ACB:13-14, :16-31, :251-255, :260-262, :267-268, :334-336, :355, :440; ACV:16-25; BBB:11-17,
  :38-39, :46, :234, :276; BBV:18-24, :145-147; CKB:31-32, :349-351, :356-357, :365-367, :404-406; CKV:37, :135,
  :137, :190, :201, :246-248; D1B:17-25, :60-71, :75-80, :129-133, :307-308; D1V:16-21; D2B:26-31, :37-41, :43-56,
  :210-213, :248-250, :357, :373-386; D2V:13-16, :52-66, :67-79, :80-83; EV2:54-63, :131-134, :150-157, :179;
  LR:13-141 (every section cited).
- **Commits** (`git show -s`): `0e0ab1f` 2026-11-01T09:41:49 UTC; `2135c2d` 2026-10-23T00:40:40 UTC; `7510c54`
  2026-10-29T09:35:39; `418aa27` 10:52:57; `8b2761d` 15:23:22; `7fbff5a` 2026-11-01T04:55:25 UTC.
- **NOTES by exact path**: `b16-verify-stats.json` :5-6, :9, :87-88, :252, :279, :282-283, :352, :356, :358, :367,
  :371 (SHA-256 `65fe90c3…`); `b16-fix.json`:269 (`4090118e…`); `test -e` of `zphi.py`, `sim_seed.py`, `sim_item.py`,
  `fwer_e2e.py` (all exist).

## 5. Quoted stated readings

Each quote matches its source byte for byte or by the words shown: REV4:301, :302, :813, :887, :919; W1R:129;
HLC:164 ("Before the draw script reads any stage-1 guard file"), :167, :168; ADD:428, :503 ("B14 87/87"); R1D:519,
:524, :682, :720, :733-734, :784-786, :799-800, :804-805; CRIT:142-143, :224-225; RIB:412-466 and the other round-1
and round-2 quotes (unchanged since round 2; the checker's 107 round-1 phrases still hold); V1A:363 (the label);
D1A:500, :503-505, :511 (the (c) paragraph's edited phrases); `b16-fix.json`:269; `b16-verify-stats.json`:352, :356,
:358; KW:3-4, :7, :13; LEDGER:70; the lead's rulings R1.2(a), R4.2 and R6.1 (compared sentence by sentence).

## 6. Sealed values

No draft states or relies on a U, HB, O, task-loss or coherence value of any stage-1 cell, a planted unit, leaf or
cell, or any sealed choice. The text added in fix round 2 carries only: synthetic simulation results (track A's
worlds; D2's U 0.03-0.05 and q 0.2 cells), counts of mutation entries and shards, hashes, paths named from the
rulings (`tmp/hlc-inputs/…`, `retrieved/sim-1/…`), file kinds without names ("a fingerprint record and two billing
files"), times and costs. The S1 record's Gate B values are unchanged from round 2 and are FOCUS's own.

## 7. Commands and tests I ran (exit 0 unless noted)

- `date -u` (5 times). Read-only git in the main checkout: `rev-parse HEAD` (`53f746d`), `diff --quiet 55d5f8b HEAD
  -- scripts runkit experiments` (**exit 1**: the merge of D-6 and round 34; expected), `show -s` of nine commits,
  `log --oneline -10`, `status --short | wc -l` (19; names not read), `ls-files` of the committed
  `lead-reports-20261101/` folder (names of committed reports; no sealed folder), `show 55d5f8b:<path>` and
  `show 0e0ab1f:<path>` piped to `sed -n` or `shasum`, `show HEAD:<path> | shasum` for the five committed build-round
  copies.
- `shasum -a 256` of the drafts, the build report, the checker, the rulings file, the eleven build-round reports and
  the committed copies; `stat` and `head -c 27657 | shasum` of `D1-readers-build.md`.
- The builder's `E-fix-checks/check_records.py` (`/usr/bin/python3 -I -B`, arguments the reports folder and the
  repository root): **PASS** (14 of 14 old blocks; 914 citations, 0 out of range, 0 skipped; 244 of 244 phrases;
  8 hashes equal; 0 stale phrases), about 1 s.
- `/usr/bin/python3 -I -B` summaries of the three synthetic simulation files (coverage, tail rates, ratios, targets).
- `v3/checks/prerun_rule_check.py` in `builds/ws-a` (venv Python `-B`, `PYTHONDONTWRITEBYTECODE=1`, scratch under
  `builds/tmp/`, 49 MB, deleted): **PASS**, exit 0 (section 1, D1).
- `pytest -q -p no:cacheprovider --basetemp=<builds/tmp/v3-pytest-…>` on ws-a's `tests/test_coherent.py`:
  **42 passed in 8.04 s** (basetemp 74 MB, deleted). A first attempt used `timeout`, which macOS lacks: nothing ran.
- `sed -n` and `grep -n` on the drafts, the reports, the rulings, ws-a's `coherent.py`, `__main__.py`, `build.py`,
  `sg_coherent.py`, `tests/test_coherent.py`, `tests/test_sg_coherent.py`, `tests/synth_kit.py`, and ws-d2's
  `hlc_draw/__main__.py` (read-only). `builds/ws-a` status count 10 before and after every run.
- Two of my own batches failed on zsh's `$VAR:` modifiers and printed only shell errors (no file was read); I
  repeated them with shell functions.

## 8. Notes (minor; not defects)

1. **A stale count in plan item 13** (`E-plan-updates.md`:211): "the reading-time readers' suite and spec (49
   entries; `cost_table` after its fix round)". D1's fix round 2 was appended to `D1-readers-build.md` at 14:38 UTC
   (after the drafts) and grew the spec to 62 entries (D1B:418, :520). Suggested: "62 entries" or "its spec on the
   final tree". The drafts' D1B hash `bee4e20e…` is the file before that append (M: its first 27,657 bytes); the
   cited lines 17-308 are unchanged (the append starts at :313); the current hash is `0e97e1b6…`.
2. **"At least one plan-A world" understates the replicate rule** (`E-D5-D6.md`:144-146). By the rule as written,
   four contrast-worlds need the 10,000-replicate pass (M, from `A-coherent-sim-plan_a-2000.json`): world i P5 (tail
   ratio 1.353), world ii P4 (coverage 0.8915, within 0.0134 of 0.88), world ii-low P6 (0.909) and world iii-prompt
   P6 (0.9075), the last two within 0.0134 of the upper edge 0.92. The lead's run covers every plan-A world
   (ACB:267-268), so nothing changes operationally; the record should name the four so the re-verifier knows what
   must pass.
3. **The (c)-at-the-pre-run route implies a restart.** A refused R1b writes nothing (M), so the step-2 comparison
   needs a new pre-run. Item 4's "the same option as step 2" and S2's "run the script again" (R1D:722-724) imply
   that R1b is re-run without the option before step 1; item 8 says only "step 2 runs without `--coherent-out`".
   Suggested clause in item 8: "under S2 the pre-runs restart without the option, and R1b must pass before step 1".
4. **D-7's reading 7 is shortened** (`E-misc.md`:132-133): "rule b also reads the greedy harm answers' categories"
   follows LR R5.1's words; the built reading takes the categories from the sampled harm, greedy harm **and greedy
   over-refusal** answers (D2B:377-379, M). Add "and the greedy over-refusal answers'" so the record states the
   reading as built.
5. **The HEAD note is a snapshot** (`E-D5-D6.md`:9; `E-S1-blinding.md`:13: "two lower than at HEAD `a494ff7`").
   HEAD is now `53f746d` and FOCUS's lines have moved again (the anchored-stamp entry is :78 there). The `55d5f8b`
   pin stays, so no citation is affected; date the sentence or drop it.
6. **Fill values that can now be filled.** The lead committed B's and C's reports under
   `lead-reports-20261101/build-round/` at `53f746d`, byte-equal to the scratch copies (M: `B-b14-build.md`
   `f98671ab…`, `B-b14-verify1.md` `6a596693…`, `C-kit34-build.md` `539d3b3a…`, `C-kit34-verify1.md` `04e14e8c…`,
   `mutants_b14_near.json` `77c3def1…`), so those `[FILL-hash]` entries take the hashes the table already states.
   Also: §39 8(d)(i) extends the S1/S5 exemption to step 4c; that follows from "report only" (R6.3) and R4.5's
   "never stops the reading", but it is the record's wording, not the rulings', and is not marked "added".

## 9. Not verified, and limits

- The plant-rank report's lines that §40 cites from CHECK, `scripts/stage1/settings/limits_check.json:7`, and R1B's
  parse of `plan.json`: not reopened (unchanged since round 2; the first two sit behind "plant" paths or the kit).
- `E-40.md` point 2's synthetic counterexample (Λ 11.33 pp; frozen form "stop", seed part "go") is the builder's run
  of the round-1 verifier's script; the round-2 verifier confirmed the same effect on its own table. Not re-run here.
- The 10,000-replicate plan-A run and the D-5 re-verify's verdict are the lead's and track A's; the record carries
  `[FILL]` for them.
- The S1 record lists what FOCUS and the records show was read; I checked consistency, not the lead's memory.

## 10. Replies to the builder's open points (G7)

1. The `[FILL]` values: see note 6 for the five build-round hashes that can be filled now; D-6's set and result and
   the D-5 re-verify's verdict stay open.
2. Agreed: point `check_records.py`'s BR map at `lead-reports-20261101/build-round/` after the commit and re-run; for
   D1B, the append at :313 moved no cited line (note 1).
3. Keeping R4 inside §39 point 11 or giving it its own section is the lead's choice; the text moves without edits.
4. Agreed: FOCUS:74's never-open entry gains the two exceptions when the records are committed.
5. Nothing to add.
