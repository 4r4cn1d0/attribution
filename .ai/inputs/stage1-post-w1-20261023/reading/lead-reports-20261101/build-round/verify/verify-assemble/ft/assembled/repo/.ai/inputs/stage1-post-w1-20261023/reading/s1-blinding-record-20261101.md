# The S1 blinding record (REV4:919; W1R:358)

- **Written** [FILL-time] by the lead (GI VIII), before any stage-1 outcome is read; committed by explicit path and
  named in the second stamp's manifest.
- **Citations** are `path:line` at commit `55d5f8b`; short names as in addendum §39's table
  (`.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md`).
- **Line numbers of FOCUS.** At `0daca9a` the final measurements, the verdict and wave 1 were FOCUS:134, :137 and :139.
  Commit `55d5f8b` added one entry at FOCUS:74 (the anchored stamp), so at `55d5f8b` the same entries are
  **FOCUS:135 (final measurements), :138 (the verdict) and :140 (wave 1)**; the W1 commit is FOCUS:144. At `55d5f8b`,
  FOCUS:134 is the user's funding-event definition, :137 the `--final` refusal and :139 the wave-2 launch (checked with
  `git show 55d5f8b:research/FOCUS.md`). The `55d5f8b` pin stays in every citation header, with no remap (LR R6.5).
  LR and the build round's reports are as in addendum §39's table.

## 1. The rule

"Any inference rule still written after the W1 commit is listed in an S1 blinding record with every Gate B value read
before it was written, and the paper labels it 'fixed after Gate B wave 1'." (REV4:919). The W1 record says the same
(W1R:358). The W1 rules were approved by the lead's W1 commit (W1R:358; LEDGER:387).

## 2. The W1 commit

2026-10-22T21:22 UTC: code `8fe5fe9`, manifest `8901eed` (SHA-256 `f6283090…`), record `bc79b08` (SHA-256
`275c7fe6…`), with REV4 (`7eccf9e9…`) beside it (FOCUS:144).

## 3. Gate B values read before any rule below was written

- **G0, before the W1 commit:** every value of REV4 §12.1 (REV4:896-901): Gate A's a0 values, wave 0a's noise gate
  (r_j, SD(r), σ_eval,0, σ̂_gate), the sealed rankings as orders, the picks, ρ, the money figures, the w0b-2 ledger
  and the six reused cells (a0 and R at 1101-1103).
- **After the W1 commit** (each from FOCUS at `55d5f8b`):

| Id | Read (UTC) | FOCUS | Values |
|---|---|---|---|
| G1 | 2026-10-23T01:00 | :140 | Wave 1, restoration D at seed 1101: g-3f941c4f +4.83, g-c5b600a1 +4.67, g-b6eff940 +2.00, g-6ed95fa3 +1.17, g-17e0407f −1.17, g-68b0b0b9 −1.33, g-3e674949 −2.33, g-efdeb5ae −3.00 pp; noise gate PASS; code WAVE2 (`bcc46209…`) |
| G2 | 2026-10-23T04:31 | :138 | The verdict TOO CLOSE (`030a7846…`): g-3f941c4f +5.58, +3.83, +2.49 pp at 1101-1103 (G2-corner λ 3.16 pp; plain Λ 2.67 pp); g-c5b600a1 +5.54, +5.66, +2.19 pp (G2 λ 3.92 pp; plain Λ 3.75 pp; contested bar Λ ≥ 5.94 pp); the other six units at 1101 from −2.42 to +2.06 pp; P = 4.26 pp; fallback and fingerprint triggers false; no extension. (FOCUS:137, 04:32 UTC, the `--final` refusal, holds no value.) |
| G3 | 2026-10-23T05:15 | :136 | P5's lexicon counts: all 15 Gate B arms inside the 0.42-0.64 band (sampled 0.47-0.53, greedy 0.46-0.51); the re-seal equal |
| G4 | 2026-10-23T05:26 | :135 | `--final` REPORTED (`06a7020a…`): 12,000 HarmBench and 3,000 Granite answers judged, the 200-answer known-answer gate passed, every §6 report present, the verdict confirmed. **Possibly read:** the output `06a7020a…` (kept with Gate B's outputs in `research/experiments/2026-10-16-gate-b-wave0-outputs/`, FOCUS:135; the file `gate_b_measurements_final.json`, `runkit/stage1-olmo/stage1_rules.py`:341-344) holds Gate B's §6 values (E_HB, O, task loss and the other §6 reports); FOCUS quotes none of them. They are listed as possibly read from 05:26 UTC on, as σ̂ is (G5) |
| G5 | first recorded 2026-10-25T11:05 | :126 | σ̂ = 1.78 pp (`result.readings.plain.sigma_hat_pp` of the verdict file `bec5f103…`; plan A). **Possibly read** from 23 Oct 04:31 UTC on: the first verdict file `030a7846…` (FOCUS:138) and the re-sealed `bec5f103…` are equal in content (FOCUS:135; the re-seal check, FOCUS:136) |

**Stage-1 values read since the W1 commit (none is an outcome):** W1-18's check (every unit meets the bar; Branch
128; FOCUS:125); C2's binding label "partly binding" (FOCUS:107); the completion records, cost ledgers and adapter
fingerprints that REV4:158 and ADD:625 allow; the judges' run and completion records (FOCUS:109, :77). No U, HB, O,
task-loss or coherence value of any stage-1 cell was read: blocks A and B are sealed and unread (FOCUS:107, :77).

## 4. The rules written after the W1 commit

"Added" marks a rule this draft adds to the brief's list; the lead keeps or drops it. "§6 possibly" = G4's §6 values,
listed as possibly read (G4); "G5 possibly" = σ̂ before FOCUS recorded it (G5).

| # | Rule | Written (UTC) | What it decides | Gate B values read before |
|---|---|---|---|---|
| 1 | ADD §16 points 1-3 (added) | 2026-10-23T00:40 (ADD:422); B16 committed in `2135c2d` at 00:40:40 | REML floor mode "active_set"; a step that floors an arm never ends the fit; the per-actor best data arm is "better and feasible" (ADD:425-427); every reading coded into B16 at that commit, B16/reading.py:449 among them | G0 only, as far as FOCUS records: wave 1's pods stopped at 00:04 and 00:57 UTC, and its reading is recorded at 01:00 UTC (FOCUS:140) |
| 2 | ADD §22 point 1 (added) | 2026-10-23T16:16 (ADD:489-491) | B+Qi's binding-check labels, on a training statistic | G0-G4 (§6 possibly; G5 possibly) |
| 3 | ADD §24 point 2 | 2026-10-23T20:24 (ADD:501, :506) | LN-14's bar read at n = 400: at least 388 of 400 flags agree, the refused count moves by at most 8 | G0-G4 (§6 possibly; G5 possibly) |
| 3b | ADD §24 point 4 (added; written, then withdrawn) | 2026-10-23T20:24 (ADD:501, :508); withdrawn 2026-10-29T09:35 (FOCUS:104) | its fallback: §9.4 prints B14's per-contrast paired form as its interval if B16's HB-C halves are not verified before the reading; withdrawn when the halves were merged | G0-G4 (§6 possibly; G5 possibly) |
| 4 | ADD §33 point 1 | 2026-10-27T17:05 (ADD:600, :604) | §9.4 covers the add effect a0 − m; the primary orientation printed as report only | G0-G5 (§6 possibly) |
| 5 | ADD §33 point 2, post-W1 deviation D-4 | 2026-10-27T17:05 (ADD:605) | REML by multi-start; the pre-registered start's fit printed beside it (S-start) | G0-G5 (§6 possibly) |
| 6 | ADD §33 point 3 | 2026-10-27T17:05 (ADD:606) | an overlap block with swapped halves is refused | G0-G5 (§6 possibly) |
| 7 | ADD §33 point 4 (added) | 2026-10-27T17:05 (ADD:607) | the block-A-only suffix on overlap texts; the 25-step stop stays; the "holds" null-rate wording | G0-G5 (§6 possibly) |
| 8 | ADD §37 points 1-3 (R1, R4, R8) | 2026-10-29T14:59 (ADD:637-643); code `8b2761d` at 15:23:22 | the claim reader's case words, E_HB as a point estimate (R4, ADD:642), the device rule as a flag | G0-G5 (§6 possibly). R4 was ruled after Gate B's E_HB values existed in `06a7020a…` (G4); FOCUS quotes none, and whether the lead read them is not recorded, so they are listed as possibly read |
| 9 | Readings coded before §39 confirms them: the overlap readings and D-4 (`7510c54`, 2026-10-29T09:35:39), the builder's RI-O points (`418aa27`, 10:52:57), the claim reader's R2, R3, R5, R6, R7 and R9 (`8b2761d`, 15:23:22) | as stated | each is confirmed in §39; §39's time governs | G0-G5 (§6 possibly) |
| 10 | Post-W1 deviation D-5 | [FILL] | S-G's coherent-only U by the linearized table, beside B16; both adverse G3a corners; "verified" read on plan A's coverage gate (LR R1.2); the builder half settled at the pre-run (LR R6.1) | G0-G5 (§6 possibly) |
| 11 | Post-W1 deviation D-6 | [FILL] | B14's report accepts recipe-S units (a settings-only deny-list; its limit recorded, LR R2.1) | G0-G5 (§6 possibly) |
| 12 | ADD §39 points 3-9 | [FILL] | the stated readings of addendum §39 (point 11's readings are row 15) | G0-G5 (§6 possibly) |
| 13 | ADD §40's readings (added) | [FILL] | the pilot gate's edges, sign and re-pilot; the reading of "published" for the construction checks; the pilot interval's form; K7 after a "go" (point 6) | G0-G5 (§6 possibly) |
| 14 | D-7, LN-31's draw built late (added; a report-only draw protocol, listed for completeness) | [FILL] | the human label check's draw: its confirmed readings 4, 7, 11, 12 and 13, the 106-term list and 5 age patterns, the benign label, and HLC 4.3 item 4 read as the same code in a second process (LR R5; addendum §39 point 13) | G0-G5 (§6 possibly) |
| 15 | The reading-time readers' stated readings (added; track D1, §39 point 11) | [FILL] | the cost table's conventions K2 extended, K5, K6 and K7 and the study costs at measured seconds / c0 (LR R4.3); `cap_reports`' reading of the O-ext summaries (C5); report-only outputs, no label rule | G0-G5 (§6 possibly) |

Not listed: D-1, D-2 and D-3 (§18, §19, §21, §28) change how inputs are built, not an inference rule; §38 changes an
operating rule; the user's decisions (§36; §39 point 10) change no inference rule. Of §37, points 4-6 are a check, two
operator rules and a not-built statement (ADD:644-646), not inference rules, so row 8 lists points 1-3 only. Also not
listed, because each is a post-W1 conditional reporting rule that changed no label: §32 point 1's fallback (a
`ref_train` unit that cannot be judged is listed as not judged, and no harm sentence is written about it; ADD:594),
§34 point 3's B+Qi O fallback (B+Qi read on the dev-100 O at its recipe cap if its engine-Y O-ext is not verified;
ADD:616) and §34 point 7's G9 (V′ reported as not run with the reason; ADD:620). The lead may list them too.

Part of rows 10-13 was first written as the lead's rulings in FOCUS at 2026-11-01T04:55 UTC: D-5, D-6, the runbook's
stop rule and stamps, and §40's literal go rule, key-only readers, never-open `retrieved/`, unopened construction
checks, kit round 35 and K7 after a "go" (the entry "BEFORE THE STAGE-1 READING: THE READ-ONLY DESIGN ROUND IS BACK;
THE LEAD'S RULINGS", added by commit `7fbff5a` and timed by `38e160d`; FOCUS:74 at `38e160d`, after `55d5f8b`). The
formal text carries [FILL]. Both times come after every Gate B value above, so the "read before" column does not
change.

## 5. The paper's label

Each rule in §4 carries "fixed after Gate B wave 1" in the paper's methods section. The deviations among them (D-4,
D-5, D-6, D-7) are also listed with SPF:344's deviations: SPF:344 lists D-1 to D-4 and the §38 restart today, and adds
D-5, D-6 and D-7 (LR R6.5).
