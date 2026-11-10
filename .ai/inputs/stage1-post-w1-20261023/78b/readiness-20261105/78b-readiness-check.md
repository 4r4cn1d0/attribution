# Check of the 7-8B readiness plan (adversarial checker)

Written 2026-11-05, 09:19-09:30 UTC (`date -u` at 09:19 and 09:29). Read-only; the only file written is this one.
Main checkout `/Users/spiderishi/Coding/attribution`, branch `stageb-costs-and-recovery-safeguards-20261003`,
HEAD `d5e176f`. The plan under check: `.../scratchpad/lineup/s78-reports/78b-readiness.md` (605 lines; read in full).
Short names as the plan's (P78, KCR, RP, SPF, README, F Ln, NEXT, MONEY, DOSE, PR4, S1B, KIT, RULES, O3K, SEAL, BLD).
Tags: (R) read with path:line; (M) measured by a read-only command; (I) inference.

No forbidden folder or file was opened: no `tmp/stage1-olmo/`, `tmp/hlc*/`, `tmp/stage1-mac-runs-20261023/`,
`tmp/stage1b/`, `judges*/`, `seals/`, `retrieved/`, `units/`, `eval/`, answer, label, judge, hidden or selector
file, nor any "plant"/"decoy" path. From `tmp/family-probe-sp-*/hosts/*/` I read only the numeric fields of
`finished.json` and `create-intent.json` with `python3 -I` (M). Stage 1's `R_d6-8` edit files were located by
`find` only, not opened.

---

## Verdict: USABLE WITH CORRECTIONS

The plan's structure holds: nothing of the four ruled items exists yet (confirmed, M); the kit route, the Llama
sealed-set route, the reader's parity test and the Part 1 outline follow P78 and KCR; almost every citation I checked
is right (about 150 path:line and FOCUS citations re-read; the exceptions are listed below). The corrections that
change what the lead does are C1 (the scorer and anchor passes belong before block A, not in block B), C2 (the S4
dose arms cannot sit inside the primary HB-C fit), C3 (the money table's "plan A or B9" line is plan A only), C4
(the retrain-as-certificate conflates two checks), C5 (the Llama sealed set must also match stage 1's `R_d6-8`) and
C13 (what needs the user is shorter than the plan says). The rest are citation, date, measurement or labelling
errors that do not change the order of work. Where the two documents differ, this check governs.

---

## Corrections (each with its source)

### Design and order

**C1. The scorer passes and the anchor job come before block A, not with block B (order error; kit subset and
money miss).** The plan's calendar puts "scorer passes" in the row "about 27 Nov-10 Dec: block B, references, dose
arms, scorer passes" (plan §2, calendar). But block A is "the six method arms at 1102-1104" (P78:199, README:92),
and A1, L1, H1, S3 and S4 are edit arms whose edit files come from the scorer passes (A1's attributes pass on the
a0-1101 states with a per-family anchor file, EYD:81; L1's scan; S3's SAS over the family's untuned answers; S4
and the dose edits from the untuned-answers pass, PR4:130-131; the plan's own T3 says "the S3/S4/dose edits need
the untuned-answers pass on a pod first"). RP:102 places "anchors, scorer passes (A1, L1, S3, S4), c0" in block 0.
At 1B the stage-1 kit ran these kinds in block A before the arms (RULES:854-856: `rep_pass`, `untuned_answers`,
`l1_scan`, `classifier`, `c0`, `retrain`, `a1_rescore` are block A kinds). So: (a) the block-0 / pre-block-A kit
subset (plan T4 step 3) must include `untuned_answers`, `rep_pass` (A1), `l1_scan`, `classifier`, `c0` and the
anchor job, each on a single-job pod with an explicit E cap until measured (KCR:128, KD6; A1 about 6-11 h, RP:43);
(b) the calendar needs 1-3 days of scorer pods per family between N and block A; (c) the money needed right after
the gate includes those pods' caps (an A1 pod at 9-16.5 h cap is a guard term of about $23-37 alone; KD6), which
the plan's "$95-115 per launch" for block A does not hold. These costs are inside RP:71's FRE total (no double
count), but their timing is before block A. The plan's §2 T6 title ("Part 2's block-0 part") and P78:367 already
require the scorer rules before any block-0 scorer output is read, which is consistent with this placement.

**C2. The S4 dose arms are secondary and must not enter the primary HB-C fit.** The plan's §5.4 defines the 7-8B
full-corpus cluster as "{a0, S1, S3, S4, S4_96, S4_192}" and §5.9 reads D1/D2 "inside the full-corpus cluster under
HB-C". PR4:234 (R): "Reference and secondary arms never enter this fit"; PR4:233 defines the cluster by "the full
corpus, or it plus 48 rows; 38 steps", and the dose arms run 39 steps. The dose arm is secondary (DOSE `seeds`: "the
secondary-arm default"; the plan's own §5.9). Correction: the primary clusters stay as PR4:233 ({a0, S1, S3, S4} and
{R, A1, L1, H1}); the dose contrasts D1 = U(S4_192) − U(S4_48) and D2 = U(S4_96) − U(S4_48) are read by the paired-mean
estimator on their common seeds in their own fit (the secondary-arm reading of S1B:121 (g), with one-sided bounds as
P78:238 says), outside Φ and outside the primary REML fit. The rest of §5.9 (nesting, the label, the fallback, the
O and L limits, the dominance-rule form against the references, the prediction, the compute disclosure) matches
DOSE and F L86 and stands. Name it "S4 add-dose" in the text: stage 1 already uses "dose" for the random-removal
dose curve (`scripts/stage1/dose_axis.py`:1-8, R; NEXT:76 "dose curve" in stage 1c), and the two must not be
confused.

**C3. The option-B money line is plan A, not "plan A or B9".** The plan's §4 table and §0 item 5 price "Arms, both
families, plan A or B9" at $555-716 (KCR:191). KCR:191 multiplies RP:76's FRE counts (OLMo 65-72, Llama 69-76), and
RP:71 (R) defines those counts with "6 method arms × 6 seeds" = plan A. P78:216 (R): plan B9 adds about $33-43
(OLMo) and $40-50 (Llama) over plan A. Corrected: B at plan A about $640-900; at plan B9 about $710-990; with H(b)
on both families about $830-1,140 (the plan's figure, which is right); each plus the confirmation $140-230 (RP:136).
Against the expected $900-1,300: plan A or B9 with the confirmation fits ($780-1,220); H(b) with the confirmation
fits only at the low end ($970-1,370). The gate must budget the worst plan SR-2 can reach (P78:203), i.e. H(b).

**C4. The a0-1101 retrain on engine Y does two jobs only if it passes.** The plan's T6 runs each family's a0-1101
retrain on Y and, if the fingerprints differ from the side units', keeps paired arms on X "and N is re-read with
the a0-free fallback (P78:121)". P78:82 and P78:121 (R) define the block-0 fingerprint check as a retrain on the
same engine X: a difference means the pod or environment differs, and that triggers the a0-free fallback. A Y
retrain that differs cannot say whether Y or the pod is the cause. Corrected rule: run the Y retrain first (one job;
if equal, both the environment check and the X → Y certificate pass, as the plan says); if it differs, run the X
retrain on the same pod image as the pre-set second job before invoking P78:121's fallback; only an X mismatch
triggers the fallback, a Y-only mismatch keeps paired arms on X and B+Qi unpaired and labelled. Also: the Y pod is
"the first Y pod" of KD9 and needs an explicit E cap (KCR:149, :128); it cannot share N's X-packed pods (the engine
identity is pinned per pack), so block 0 is three pods, not two "or after N on the same pods" (plan §2 calendar).

**C5. The Llama sealed set's parity test must cover d = 6-8 against stage 1's draws.** The plan's T3 acceptance
checks remove-list equality "for d = 1…5 and the 8 unit files" against SEAL. Stage 1 built `R_d6-8` by REQ-4 with
the same frozen builder (S1B:77; P78:343 "d = 6-8 come from REQ-4"), and they exist at
`.ai/inputs/stage1-commitments-20261016/r-draws/edits/R_d{6,7,8}.json` (M: `find`; not opened). The Llama
`R_d6-8` lists must equal those too (block B under plan A uses R_6-R_8, P78:212). Add that test; the OLMo-parity
test should also reproduce d = 6-8 byte for byte where REQ-4's provenance allows.

**C6. S3, S4 and the dose edits are per model, not per manifest.** The plan's T3 says the Llama files "are stage-2's
files too (Llama-3.2-1B has the same manifest): build one set for both, named by manifest, not by model (I)". That
holds for R, the unit files, H1 (same tokenizer across Llama 3.2-1B and 3.1-8B, so the same token counts) and S1
(the same 48 S-pool rows). It does not hold for S3 (DataRx SAS with the model's own greedy answers, PR4:130), S4
(the model's own untuned answers, PR4:131) or the dose edits: Llama-3.2-1B's and Llama-3.1-8B's differ. Name those
by model and manifest. (The plan's later sentence "S4 (Llama's own untuned answers)" already implies this; the
"one set for both" line is the error.)

**C7. The kit's budget glob: pick one naming.** T4 step 1 names the working copies `tmp/family-probe-s78-*`, which
the stage-1 kit's `KITS_GLOB` already matches (`budget.py`:39: `("family-probe-*", "gate-b-olmo*", "stage1-olmo*")`,
R); T4 step 5 then says "with `KITS_GLOB` extended by `stage1-78b*`". Either is fine; both together are
inconsistent. Keep `family-probe-s78-*` (P78:344, EM-2) and leave the glob as it is, so the stage-1 kit (still used
by stage 1c and stage 2) sees the 7-8B pods without any change to its frozen `budget.py`. Note KCR KD7 itself
proposed `family-probe-s1-*` (KCR:143, :268); the plan's `s78` follows P78:344 and O3K's prefix; state the choice.

### Citations, dates and measurements

**C8. Gate B closed on 23 Oct, not 31 Oct; one Gate B pod is still kept.** The plan (§0 item 2b, T2 KD4, §4, §5.10,
§5.11) says "Gate B is closed and its last pods are deleted (F L104)" and sets the hold's reason as "Gate B closed
31 Oct, F L104". F L161 (R): "GATE B CLOSED: measurements --final REPORTED (recorded 2026-10-23T05:26 UTC)". F L104
records the deletion of the last two Gate B *judge* pods on 31 Oct; F L81 and F L104 (R) list `gateb-w0b-2` (the
retrain's q and e1 states) as a stopped pod still kept. The conclusion (KCR's $83.91 hold and P78's "until Gate B's
last kit pod" freeze have lapsed) stands; the reason string in `rules_78b.py` should read "Gate B closed 23 Oct
(F L161); its last judge pods deleted 31 Oct (F L104)".

**C9. The stage-1 `launch.py` grep does not "print nothing".** Plan §1.4: "Its `launch.py` has no token check or
hand-over (M: `grep -iE "gated|token"` on it prints nothing)". It prints three lines (M): line 2 ("…without the
gated-token checks: OLMo-2-1B and Qwen3Guard are open repositories"), line 12 and line 31 (the scrubbed child
environment). The conclusion holds by line 2 itself; the measurement claim is wrong.

**C10. The usage reset is on Thursdays.** Plan §3: "usage resets Wednesdays 09:00 UTC (F L74: next 12 Nov)".
12 Nov 2026 is a Thursday (M: `date -j`), as is 5 Nov. F L74 gives the next reset as 2026-11-12T09:00 UTC (R).

**C11. "The user confirmed 4 arms per pod for stage 1" is not supported.** Plan T2 (KD2) and §3 item 8 cite
RULES:72 as "a later user-confirmed value". RULES:72's comment (R) cites "LN-27, LS-12 (a); §8 Q5"; LN-27 is a lead
ruling under the delegation (`research/experiments/2026-10-17-stage1-preregistration-rev3/lead-rulings-needed.md`:88,
R: "The S1 lead items (CONS LS-01 to LS-04, LS-08 to LS-16, …)"). The user's confirmation of 4 was for Gate B
(F L241, 9 Oct). The lead may still rule 4 at 7-8B under the delegation (KCR KD2 allows it); the basis is the
delegation, not a prior user confirmation.

**C12. The OLMo 3 configs are not committed.** Plan T2 (KD8): "the OLMo 3 round already adds nine configs, F L77"
as the precedent for committed additions under `experiments/`. F L77 (R): "the code stays uncommitted in the scratch
worktrees ws-a, ws-b, ws-c … until the verify round"; `git status` in ws-all shows the nine configs untracked (M).
There is no commit precedent yet; the T4 freeze's lapse (C8) is the reason configs may be committed by explicit
path, and the OLMo 3 configs will be the first such commit.

**C13. What needs the user is shorter than §3 says.** By F L98's form (rulings under the 16-17 Oct delegation with a
pre-set fallback), the user's 16 Oct "no approval questions" rule and DOSE's own wording ("at 7-8B by that tier's
money rule"), the lead rules S, SR-2, the thresholds, F, RP decision 5 and the Llama 1103 rule, the kit route, the
arms per pod and the dose arm's seeds, and records each (the plan's §3 says so for most of them but still lists them
as "needs the user", and §0 item 4 lists "a yes to the kit route"). What needs the user: (1) the money in the
account (MONEY); (2) the HF token in the Mac environment at each Llama launch (family-probe `launch.py`:8-14, R);
(3) a yes by pod name before any stopped 7-8B pod is deleted (O3K `states_tool.py`:12-16, R); (4) H (a) or (c) only
if the lead would choose them, because they change D5's SESOI (P78:243, RP:146). Everything else is reported, not
asked. (DOSE's "3 at Llama-3.2-1B … at 7-8B by that tier's money rule" means the lead writes the 7-8B seed count at
the gate from money, as plan §5.9 proposes.)

**C14. Smaller citation and arithmetic fixes.**
- README:94 (not :95) holds "it read TOO CLOSE, so it does not run"; README:86 (not :85) holds the stage-3 pick
  rule (R).
- `KINDS` has 21 kinds (RULES:599-601, R), not "J1-J22".
- The block A launch need at KCR's caps is about $105-125 per four-pod launch, not "$95-115": $6 + 1.85 × 4 × 10.5 h
  = $83.70 (OLMo) and $6 + 1.85 × 4 × 12.5 h = $98.50 (Llama), × 1.25 (KCR:125's formula; M arithmetic).
- Stage 1's "$193.53 total" (block A $48.59 + block B $144.94) omits cfy-1/cfy-2 $3.35 (F L103, R), so the
  primary-family total is about $196.9; the scaling cross-check moves by about 2%, inside its stated 15%.
- The plan's kit size "24 files, 11,464 lines (M)" did not reproduce: the top-level 18 files are 10,369 lines; with
  `setup/` 12,149; all 37 files 28,003 (M, `wc -l`). The test count 378 across 9 files reproduces (M).
- "3 more a0 runs per family (about $9-14)": P78:333 says about $9-12 (R).
- The OLMo-2-7B a0-1101 pod has two create intents (8.5 h and 12.5 h; M); the plan's "cap intents 12.5 h (OLMo)"
  is the one that ran. All six main-recipe job times equal KCR §3 (M: 114.6, 103.9, 91.1; 174.2, 121.6, 123.6 min).
- O3K's tests: 18 + 12 + 8 (M) as the plan says; F L77's "33 kit tests" counts differently (not a plan error).
- Plan §5.4 "P78's [USER] item 1 needs no decision beyond noting this": the 1B part of S is settled (PR4:232-233
  adopts HB-C, seed-blocked), so S-P at 7-8B is the consistent choice, but P78:386 marks it [USER]; the lead records
  it as a ruling under the delegation (S-P primary, S-U as the pre-registered sensitivity), not as "already decided".

### What the plan misses

**M1. O and L at 7-8B.** Every arm needs over-refusal O against the family's own untuned model and task loss L
(P78:379; PR4:237's O set of 500 prompts). The side probes' untuned units were evaluated with the family-probe bank
(468 greedy + 600 samples + 189 ARC; KCR:70), not with stage 1's O set, so the 7-8B kit needs the stage-1 kit's
`regenerate` / `o_only` / `untuned_answers` jobs for both untuned units before block A (RULES:854-856 lists them in
block A at 1B). Part 2's limits section (P78:379) should say which evaluation bank the 7-8B arms use and whether the
`arm` kind at 7-8B evaluates O and L in the same job, as at 1B, or needs a separate job. Not costed separately in
the plan (inside the FRE "scorers and references" only loosely).

**M2. A $0 check on S4's kept rate.** DOSE's fallback ("fewer than 192 rows kept") can be sized now: the 1B S4 build
record holds the counts of candidates screened and kept for the first 48 (counts only, no answer text). Reading
them tells the lead how far down the 512-prompt candidate list (PR4:131) 192 kept rows would reach at 1B, and so
whether 192 is realistic at 7-8B. Add it to T1's inputs.

**M3. The retrain pod and the scorer pods in block 0's money.** The plan's "block 0 need about $56 (KCR:177)" covers
N's two pods only. With the Y retrain pod (C4) and the scorer and anchor pods (C1), the need in the first days after
the money arrives is about $56 + the retrain pod's guard (about $15-20 at a 4-5 h cap) + the scorer pods (about
$25-40 each at KD6 caps). Spend stays small (N about $26-32; retrains about $4-6; scorer passes about $40-80 for both
families at RP:43's 6-11 h A1 passes, E); the guard terms are what the balance must cover at each launch.

**M4. Part 2's freeze window.** The plan's calendar freezes Part 2 (due before block A, P78:375) in the same row as
block A ("after the gate (about 22 Nov): T7; block A"). The scorer pods (C1) give the window: Part 2's scorer rules
are committed before the first scorer output is read (P78:367, :413), and the rest of Part 2 is frozen while the
scorer pods run, before block A's first pod.

**M5. One naming note for the record style.** The plan's T1 proposes the decision records under
`.ai/inputs/stage1-post-w1-20261023/reading/` "or a new `78b/` folder"; the post-W1 records rule (the user's memory
"Post-W1 records folder") puts post-freeze records under `.ai/inputs/stage1-post-w1-20261023/` unless a W1 kind,
so a `78b/` subfolder there is the consistent choice; `scripts/stage1/commitments.py check` exists (M) and should
run after each commit, as the plan says.

### Claims checked and confirmed (R or M)

MONEY and DOSE records in full; F L74, L77, L81, L84, L86, L91 (head and tail), L98 (head and tail), L103 (head and
tail), L104, L120, L121, L133, L161, L168, L189, L210, L241 and the "7-8B" grep; P78 in full (every line the plan
cites: 1-13, 17-26, 48-66, 70-84, 92-112, 114-134, 152, 159, 168-182, 199-218, 222-245, 249-295, 301-325, 333-348,
350-357, 365-379, 385-415, 473); KCR in full (9, 11-20, 62, 72-84, 88-128, 132-151, 156-161, 177, 183-192, 210-228,
238, 256, 262-272); RP:13-14, 31, 41, 43, 63, 67, 71-79, 91, 93, 97-110, 113, 136, 138, 140, 146, 149, 157, 162;
SPF:57, 168, 490-521, 619; README:84-100, 113, 120; NEXT:3, 15, 69, 73-84; PR4:128-131, 228-240;
`scripts/stage1_s1/reading/README.md`:18-24; S1B:65, 77, 121, 151, 210; EYD:81; XL:9-20; RULES:60-72, 82, 398-401,
478-487, 599-601, 852-859, 868; `budget.py`:39; `probes.py`:24-25, 40, 68; `download_models_stage1.py`:10-24;
family-probe `launch.py`:1-22; O3K's README, `states_tool.py`:1-24, `launch.py` (byte-equal to family-probe's, M),
untracked at `e89d74f` (M); BLD:60-61, 143-144, 198 and its SHA-256 `80cb8944…` (M); `SS/edits.py`:108-124; the three
prepared-manifest hashes (M); the four 7-8B configs present (M); the OLMo-2-7B e1 adapters and the Llama 1e-4
adapters on the Mac (M, `ls`); the six probe pods' job times and cap intents (M); SEAL's `out/edits/` (R_d1-5, 8 unit
files, 16 M_g files; M); CALC `env_and_manifest_check_out.txt`:1-17 and `rule_oc2_out.txt`; `scripts/gate_b_reading.py`
function lines 288, 294, 363, 457, 757 (M); `scripts/stage1/{make_untuned_answers,write_add_edit,build_length_rules,
commitments,dose_axis,token_accounting}.py`, `scripts/gate_b_mac_judges/`, `.ai/inputs/gate-b-anchors-20261008/`
present (M); no FOCUS entry names a Llama G1 check (M, grep); commit `e0b233a` (M). Arithmetic re-done: the dose arm
$49/$99 and per-family $21/$42, $28/$57; option B $640-900 and $830-1,140; option C $270-390 and $375-510; the
B − C difference $370-510; the stage-1 scaling $370 + $445; the dose arms' step counts (4,896 → 39, 4,992 → 39 at
128 rows per step); the 3-seed paired SE 2.3 pp at σ_pair 4; block 0 $56.06; the 12-pod count for block A.

Not checked: the hours per track (E; no basis to re-derive); the judges and storage lines ($25-50, $15-30; E); the
S4 kept rate at 1B (M2, a lead task); the adapter hashes; any simulation.

---

## Corrected track list (this governs where it differs from the plan)

Order within each window is the order of work. Builder hours are the plan's E values; T6a is new as a separate
early item; C1's kinds move into T4's first subset.

**Window 1, 5-12 Nov (this usage week; the OLMo 3 verify round shares it; "7-8B first" if usage runs short, F L98).**
1. **T1 (lead, in parallel with everything).** Part 1 text and the recorded rulings: S-P with S-U as the sensitivity
   (recorded as a ruling, C14); SR with 4.5/6.0 and the review ceiling; SR-2 yes if the record-done step can hide
   block-A U; H (e) with (b) first and (a) as the money fallback; F1; TC does not run; RP decision 5 (reuse) with
   the 3-new-a0 fallback; the Llama 1103 "rung stays" rule; the kit route (ii) and 4 arms per pod under the
   delegation (C11); the S4 add-dose arm as a secondary arm outside the primary fit (C2), seeds 3 with 6 if the money
   after the gate covers it, labelled "added after the OLMo-2-1B stage-1 reading"; the blinding line (plan §5.0);
   predictions N1, N2 and the dose prediction; §5.12's labelled list; the S4 kept-rate counts (M2). Freeze: SHA-256
   in FOCUS before block 0's first `launch.py`; `commitments.py check` after the commit. Records under
   `.ai/inputs/stage1-post-w1-20261023/78b/` (M5).
2. **T2.** `runkit/stage1-78b/rules_78b.py`, `measured-basis-78b.json`, `derive_78b_basis.py`, tests 1-15 and
   KCR:226's mutants; `GATE_B_HOLD_USD = 0` with the reason "Gate B closed 23 Oct (F L161); last judge pods deleted
   31 Oct (F L104)" (C8); kinds `arm` and `evalonly` measured, every other kind single-job with an explicit E cap
   (KD6); KD9 re-measure on the first Y pod.
3. **T3 ($0 part).** The Llama wrapper on BLD's `draw_r` with its own writer; `R_d1-16` and the 8 unit files on
   `c52a50af`; list equality against SEAL for d = 1-5 and the units **and against stage 1's `r-draws/edits/R_d6-8`
   for d = 6-8** (C5); the OLMo byte-parity reproduction; the trap test; H1 and S1 by manifest (shared with stage 2);
   S3, S4 and the dose edits per model, after the untuned-answers pass (C6).
4. **T6a (new, small).** The two recipe-S_78 configs (`…-olmo2-7b-r64-b-mb2-gateb-<date>.json`,
   `…-llama31-8b-r64-b5e5-mb2-gateb-<date>.json`), the "differs only in recipe-S fields" test, `config_sha256` with
   `-I -B`; committed by explicit path (the first committed addition under `experiments/` since the freeze lapsed;
   C12). They are inputs to T4's pack.
5. **T5.** `scripts/scale78b/noise_reading.py` with the Gate B wave-0a parity (1.83, 2.16, 1.28), inputs keyed by
   `complete_sha256` and family, the 1B-record refusal test; `blinded_sigma.py` only if SR-2 is adopted;
   `transfer_reading.py` not built.

**Window 2, 12-19 Nov.**
6. **T4, first subset.** Copy `runkit/stage1-olmo/` to `runkit/stage1-78b/` (original untouched). Per-family
   constants from `rules_78b.py`; working copies `tmp/family-probe-s78-<family>-<block>/` with `KITS_GLOB` unchanged
   (C7); the gated-token launch path ported from family-probe `launch.py`:8-21 with its tests and a separate review;
   block 0 = `arm` (R_1-3 under the main config), `a0_arm` (Llama 1103), `retrain` (a0-1101 on Y, its own pod, with
   the X retrain as the pre-set second job; C4), **and the pre-block-A scorer kinds: `untuned_answers`, `o_only` /
   `regenerate` for both untuned units (M1), the anchor job, `rep_pass` (A1), `l1_scan`, `classifier`, `c0`, each
   single-job with KD6 caps** (C1); `s_obs` after each arm; the free-space check; the record-done step prints no U
   for block A (SR-2's blinding test). Acceptance as the plan's T4 plus: `plan_tool.py init-block 0` prints the need
   for N's pods, the retrain pod and the scorer pods separately (M3).
7. **T6b, T6c.** The fingerprint-comparison script and its 1B test; the any-model Part C scripts under
   `scripts/scale78b/` with the 1B parity test (1B scripts untouched); the scorer rules' text and code hashes in
   Part 2's scorer section, committed before any scorer pod launches (P78:367).
8. **T1 freeze** (step 1's acceptance) once the rulings are recorded; it needs no user answer except the money's
   arrival to set the launch date (C13).

**19-20 Nov.** Dry packs on both families (engine X `472fc7f6…`, both config hashes, both manifests); `init-block 0`
plans at the M-cap caps; `commitments.py check`; Part 1's hash in FOCUS. Block 0 is one `launch.py` away.

**The day the money arrives (about 20 Nov).** (a) N: the OLMo pod (3 arms, 8.5 h) and the Llama pod (4 arms,
12.5 h) in parallel, 7-9 h wall, spend about $26-32, need about $56; the HF token in the Mac environment for the
Llama launch (C13). (b) The retrain pod on Y (certificate; C4). (c) N read the next day by `noise_reading.py`; the
gate reads money and N only. (d) Then the scorer and anchor pods per family (A1 6-11 h, the untuned-answers, O/L,
L1, S3, c0 jobs), 1-3 days (C1); their outputs are read only after the scorer rules are committed.

**Before block A (about 22-25 Nov).** Part 2 frozen with its blinding line (M4): the arm rules per family, the
O and L limits (M1), references, judges, cost conventions, the confirmation rule, the dose arm's reading and the
dose edits' hashes, Alpaca's home. Then block A, both families or the chosen one: 12 four-arm pods, 4-8 in parallel,
1-3 days; judges per block. The money at each launch: about $105-125 per four-pod launch at KCR's caps (C14).

**About 27 Nov-10 Dec.** SR-2's `blinded_sigma.py` (if adopted) sets block B's plan; block B (plan A 23 runs per
family; B9 33; H(b) 49), the references (`ref_eval`, `ref_train`, `safe_lora`; B+Qi on Y after its basis is
measured, KD6/KD9), the S4 add-dose arms (6 or 12 runs per family); judges; the state rule (pull e1 states, verified
backup, the user's yes by name before any delete).

**About 11-20 Dec.** The confirmation on engine Y (≤ 2 contrasts per family, fresh seeds 9101-9999, the sealed
200-prompt subsample; README:86), $140-230 (B) or $70-120 (C).

**4 Jan 2027.** Results frozen (README:120). If the money slips past about 1 Dec, the gate's re-check (F L98):
C, or B without the 7-8B confirmation, by RP:138's cut order.

**Money (corrected).** B by the gate: plan A about $640-900; B9 about $710-990; H(b) about $830-1,140; plus the
confirmation $140-230. C (OLMo-2-7B) about $270-390 plus $70-120; C (Llama-3.1-8B) about $375-510 plus $70-120.
The first days' guard terms: N about $56; the retrain pod about $15-20; each scorer pod about $25-40 (M3). All
bases as the plan's §4 (measured per-arm costs at 4 per pod, KCR:183-188; FRE counts RP:76; +20% RP:41), with no
item counted twice; the scorer passes are inside the FRE total and only their timing moves (C1).

---

## Process (this checker)

- **Commands (exit 0 unless noted):** `date -u` (2×); `git branch --show-current`, `git log --oneline -1` (main
  checkout and the scratch worktree ws-all), `git status --short` (ws-all); `sed -n`, `grep`, `cut`, `wc -l`, `ls`,
  `find`, `diff` over the sources named above; `shasum -a 256` of BLD and the three prepared manifests; `python3 -I`
  reads of the numeric fields of six probe pods' `hosts/*/{finished,create-intent}.json`; `date -j` for the
  weekday. One `echo =====DOSE=====` failed under zsh's `=` expansion (exit 1) and was redone with `cat` alone.
- **Read:** the plan in full; MONEY; DOSE; P78 in full; KCR in full; the RP, SPF, README, NEXT, PR4, S1B, EYD, XL,
  RULES, probes, download, launch, budget, edits, BLD, reading-README, gate_b_reading and O3K lines listed under
  "Claims checked"; FOCUS lines 74-104 (those cited), 120-121, 133, 161, 168, 189, 210, 241 and the 7-8B, Gate B,
  hold, G1, dose and arms-per-pod greps.
- **Not read:** any unit's answers, prompts, labels, judge files, seals, `retrieved/`, `eval/`, `units/`; the
  stage-1 `R_d6-8` files' contents; the reading record; the OLMo 3 addendum; the family-probe orchestrator.
- **Not done:** no test run; no number of KCR's re-derived beyond the arithmetic above; the S4 kept-rate read (M2).
