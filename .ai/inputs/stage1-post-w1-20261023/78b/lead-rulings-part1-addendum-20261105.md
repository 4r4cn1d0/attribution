# Lead rulings, Part 1 addendum (7-8B tier, 5 Nov 2026)

Recorded 2026-11-05T14:41 UTC by General Implementation X, the main-study lead, under the user's delegation (no
approval questions; the frozen money and blinding rules apply). These rulings follow from round 1 of the 7-8B $0
build (four builders, one adversarial verifier each). They amend `lead-rulings-part1-20261105.md` (SHA-256
65e477b0ac1e772c…, commit fb51421) where each entry says so. No stage-1 outcome was read for them.

## A1. Recipe S_78 is written after each family's anchor job (amends rulings 10 and 11)

- **Ruling.** Route (A). The maker `scripts/scale78b/make_recipe_s78.py` is merged now. Each family's S_78 config is
  written by that maker once the family's anchor job has written its `anchors.sealed.json`, then committed by
  explicit path (KD8). Until then `rules_78b.py` pins `RECIPE_S` as null for both families, and every kind that needs
  S_78 (the a0-1101 retrain, A1's pass) refuses.
- **Basis.** S_78's `attribution.query_bank` is `anchors-<SHA-256 of the family's anchor file>` (R:
  `scripts/make_anchor_answers.py:1-18`). The engine checks that file's hash at the attributes job (R:
  `experiments/safety_selection/jobs.py:175-181`), so a placeholder would pass the loader and fail on the pod. The
  anchor file holds the model's own Safe answers, so it is per model (P78:377).
- **Rejected.** (B) OLMo-2-7B reuses Gate B's 1B anchor file: it holds OLMo-2-1B's answers, which changes P78:377,
  and Llama would wait anyway.

## A2. Before block A: the anchor job, then S_78, then the a0-1101 retrain (amends ruling 10)

- **Ruling.** Per family: (1) the anchor job on its own single-job pod (KD6); (2) S_78 written and committed (A1);
  (3) the a0-1101 retrain on engine Y under S_78, as ruling 10 says; (4) the X retrain only if Y's fingerprints
  differ (ruling 10's pre-set second job).
- **Basis.** Ruling 10's retrain runs under S_78, and S_78 cannot exist before the anchor file. The anchor script
  says it "runs on the pod, before recipe S exists" (R: `scripts/make_anchor_answers.py:1-2`), and Gate B used the
  same order at 1B (PRE:5, revision 3, as track C cites it). This moves the anchor pods before the
  retrain pod. It adds no pod and no money (the check's C1 already puts the anchor job before block A).
- **Rejected.** A certificate retrain under the main config plus a second S_78 retrain for A1's states: one more
  retrain pod per family.

## A3. The two extra sealed folders stay where they were built (amends ruling 14)

- **Ruling.** `.ai/inputs/scale-78b-r-draws-olmo2-20261105/` (OLMo-2-7B R_d11-R_d16) and
  `.ai/inputs/scale-78b-length-rules-llama3-20261105/` (Llama-3.1-8B H1) stay as sealed input folders beside
  `.ai/inputs/scale-78b-sealed-llama3-20261105/`.
- **Basis.** Each is a sealed input set with its own MANIFEST, like Gate B's `.ai/inputs/gate-b-sealed-20261008/` and
  `.ai/inputs/gate-b-anchors-20261008/`. A move changes the output path inside the hashed build scripts and forces a
  rebuild. Ruling 14 named only the Llama set because the other two were not foreseen.
- **Fix before the first commit.** The verifier's B-M2 and B-M3 (write guards in the hashed scripts) are fixed in the
  fix round and the sets are rebuilt into empty `out/` folders. From the commit on, the scripts are frozen.

## A4. The Llama G1 check (P78:272; the freeze condition of ruling 14)

- **Result** (M: track C's record `.ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json`, read by the
  frozen Gate B guard code; confirmed by the verifier). Llama-3.1-8B a0-1101 passes G1 (42 of 600 answers fail the
  screen). **a0-1102 fails G1:** 63 of 600 (10.5%) fail the screen; 43 of them are short answers (20 of 557 = 3.6%
  without them), so the answers-end check reads TOO CLOSE, which PRE:147 counts as a G1 failure. OLMo-2-7B a0-1101,
  -1102 and -1103 pass (23, 20 and 16 of 600).
- **Ruling.** Keep 1B's G1 unchanged (P78:272's recommendation). In N, G1 is report-only (P78 §3.4), and TC does not
  run (ruling 6), so nothing is blocked. In the 7-8B main study the coherence screen is stage 1's (PR4 §3.7): the bar
  is read on an arm's answers pooled over all its seeds, per-seed counts are reported, a seed above 10% is flagged,
  and no arm or seed is dropped. On the two seeds read so far, Llama a0's pooled screen count is 105 of 1,200 (8.75%;
  computed from the record's counts); the arm's reading uses all its seeds after block A.
- **The user is told** before the Part 1 freeze (P78:272), in the lead's report of 5 Nov.

## A5. The cap rule's constants (a KCR erratum)

- `rules_78b.py` uses the measured basis file's maxima. KCR's printed requirements (12,243 / 12,365 s OLMo-2-7B at
  33 / 38 steps; 12,499 / 12,613 s Llama-3.1-8B) round each constant before summing; the rule gives 12,244.15 /
  12,365.42 s and 12,498.05 / 12,612.47 s, at most 1.2 s apart. Caps, guards and spends are identical to the cent
  (M: track A's test 1, which also reproduces KCR's own arithmetic). The basis file governs.

## A6. One family's fallback in the pooled noise reading (P78 §3.3)

- When only one family's fallback trigger fires, that family's three R-arm pair terms and the other family's three
  seed-matched terms enter the pooled median (the noise reader does this; track C). Part 1 §3.3 states it.

## A7. Ruling 2's seed counts and the unpaired sensitivity

- At ruling 2's counts (R at 7 / 10 / 13 seeds in plans A / B9 / H(b)), the unpaired sensitivity S-U has SE 3.24 /
  2.68 / 2.33 pp and MDE 11.3 / 8.7 / 7.6 pp (M: verifier D, with P78's own formula, which reproduces every P78 row
  first). P78's values were at R 8 / 12 / 16. The S-P multiples (1.42 / 1.08 / 0.93 × σ_pair) do not change.
- **Ruling 2 stands.** The primary scale is S-P (ruling 1), and the seed rule reads σ̂_pool on the pair scale; S-U is
  a sensitivity. Part 1's H table prints the corrected S-U values.

## A8-A12. The Part 1 draft's open items (recorded 2026-11-05T14:44 UTC)

The round-1 Part 1 draft (`research/experiments/2026-11-05-78b-preregistration-part1.md`, §17) left these open.

- **A8. The retrain pods (its item 3).** One single-job pod per family: two under [B], F1's only under [C]. Each pod
  has the kit's explicit E cap for the retrain kind (KD6; `rules_78b.py`, 4.5 h until measured). The kit's
  `init` prints each pod's need on its own line (the check's M3).
- **A9. Judging for N (its items 5 and 12).** N's gate and the seed rule read the engine's own U only. HarmBench
  judging of N's R arms (report-only) runs with block A's judge pods. Llama a0-1103 gets the same judge files as
  block A's units, on the same pods. No Granite judging runs for TC, because TC does not run (ruling 6).
- **A10. Part 2's file (its item 9).** `research/experiments/<date>-78b-preregistration-part2.md`. It is frozen like
  Part 1 (a commit by explicit path, its SHA-256 in FOCUS, the commitments check) before block A's first pod. Its
  scorer section is committed before any scorer output is read.
- **A11. The 7-8B coherence screen (its item 10).** Settled by A4: PR4 §3.7's pooled bar for the main study's arms;
  the frozen Gate B G1 code, report-only, for N's R arms.
- **A12. KD1's fallback (its item 13).** Its trigger is "T2 not verified by 12 Nov". Round 1's verifier found minor
  defects only (5 Nov). The fallback does not fire if the fix round's re-check passes and the lead merges T2 before
  12 Nov; the lead records the merge commit in FOCUS.
