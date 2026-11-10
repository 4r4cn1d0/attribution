# Lead rulings of General Implementation XI (7-8B tier; from 8 Nov 2026)

Recorded 2026-11-08T13:47 UTC by General Implementation XI (GI XI), the main-study lead since GI X's handover
(`.ai/inputs/stage1-post-w1-20261023/reading/handover-gi-x-to-gi-xi-20261107.md`), under the user's delegation (no
approval questions for planned steps; the frozen money and blinding rules apply). These rulings were made after the
stage-1 reading and before any 7-8B scorer output or repair outcome exists. None reads a 1B repair outcome. Part 1
(frozen), its addendum and erratum, the rulings 1-16, A1-A17, PP1-PP18 and every set in
`lead-rulings-part2-design-20261106.md` (DES) stand.

## G1. The form of Part 2's leftover text round (8 Nov)

Part 2 (`research/experiments/2026-11-06-78b-preregistration-part2.md`) was committed at `16c2d08` (SHA-256
`1889e8e5…`) with its scorer section (§1) committed and its rules fixed from that commit. Its status line says: "A
later change to a committed part is a dated amendment in a new file, never an edit of this one." Round 7a's
re-verifier said the same of §1 (`build-round-20261105/p2-r7-verify.md`, section 1), and GI X committed before
applying V1 and V3, that report's second option. DES's third set (14:45 UTC) says its rulings and V1-V7 "are written
into Part 2 before its freeze". Both are kept as follows:

1. **§1 is not edited.** Every change to §1's text from DES's third set (V1, item 38, item 33 (b) with V3, the label
   line in §1.18 item 15) and from V1, V3, V4 (its §1.17 part), V6 (its §1.8 and §1.16 parts) and V7 where it touches
   §1 goes into one dated amendment file, `research/experiments/2026-11-08-78b-preregistration-part2-amendment-1.md`
   (AM1). AM1 quotes each old §1 sentence exactly, gives the new text and its basis, and governs where it differs
   from §1. It is written before any 7-8B scorer output exists. It fills the two items §1's heading names as open
   (§14 items 33 (b) and 38) and corrects §1's text to rulings that already bind (PP18's main clause, DESO2 item 36).
   It changes no rule fixed at `16c2d08`.
2. **The draft parts are edited in place** (the status line, the short names, §0 and §2-§16): V2's ruling in §10.2
   and §10.3; V4, V5 and V7; §14's items 33 (b) and 38 closed and V2 added as a closed item; the label lines of §16.5
   items 7, 10 and 11 confirmed; the change log (§13, §13.1). The status line names AM1.
3. **Hashes.** Every hash and line cite in Part 2 is re-taken at HEAD `c57e456`. A §1.17 value that differs is
   logged in §13.1 with both values and the commit that changed it (the status line's rule); §1.17 itself is not
   edited. No code file changed between `63b57c0` and `c57e456` (M: `git diff --name-status 63b57c0 c57e456`: DES,
   FOCUS, Part 2, the handover note and round 7a's reports only), so every code hash is expected to be equal.
4. At Part 2's freeze, AM1 is frozen with it (both by explicit path; both SHA-256 values in FOCUS). This round's
   commit is not the freeze.

## G2. DES's header line covers its third set (recorded 2026-11-08T14:04 UTC)

DESO2 item 35 confirmed that DES's header ("made after the stage-1 reading and before any 7-8B repair outcome; none
reads a 1B repair outcome; ruling 16's labels apply where the memo marks one") covers DESO and DESO2. DESO3 (DES's
third set, 2026-11-07T14:45 UTC; R: DES:167-184) has no such line. GI XI confirms it by inspection (I): DESO3's five
rulings set when `ENGINE_Y` is filled on a stopped family (V1), what σ̂_A pools and which design SR-2's simulation
uses (V2), what the encode count covers (item 38), which id lists a reduced s-pool record drops (item 33 (b) with
V3), and three label lines. None cites or depends on a 1B repair outcome. The label lines are ruling 16's labels:
they state that two choices were made after the stage-1 reading, which the authors had seen (P1:33). This closes
Part 2 §14 item 40 (round 7b).

## Money and usage at this ruling (8 Nov)

Balance $18.82 at 2026-11-08T13:46 UTC (`runkit/stage1-olmo/budget.py`, read-only projection), nothing running,
$0.026/h of storage. All-models weekly 69%, Fable 100% until 2026-11-12T09:00 UTC; agents run on Opus until then.
