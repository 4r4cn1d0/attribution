# Track P2 round 7b text fix (p2-r7b-fix)

Started 2026-11-08 13:55 UTC; this version 14:02 UTC (`date -u` before each time written). Tags: M measured (command
number in section 6), R read (path:line), E estimate, I inference. MAIN = the main checkout at HEAD `c57e456`
(read only). WP = the detached worktree `scratchpad/b78/ws-p`. No git state changed anywhere. No pod, spend, network,
install, download, agent or message. No forbidden folder, selector, hidden, judge, answer, generation, sample or
prompt-text file was opened; from settings files I printed list sizes and hashes only. The side paper is not mentioned.

## 1. Status

**DONE.** §1 of Part 2 is unchanged byte for byte (cmp exit 0). AM1 is written (18 changes). The draft parts are
edited in place. Every hash re-taken at `c57e456`. One new open item (§14 item 40) was raised, and the follow-up in section 10 closes it by GXI G2.

## 2. Files changed

| File | SHA-256 before | SHA-256 after |
|---|---|---|
| WP `research/experiments/2026-11-06-78b-preregistration-part2.md` (F) | `1889e8e51b0ad9d0eef5be29367cc4dae930d184b79c0d16ea7775056473269e` (875 lines) | `f43cb73956fe12206e43c3277ba173085718170f165cc98ad0e9b4bb25781bb3` (903 lines) |
| WP `research/experiments/2026-11-08-78b-preregistration-part2-amendment-1.md` (AM1, new) | none | `c96a3a5ccbec9851bf06b5660c77b8d775ba33c3e502bf223176a654b3f98014` (334 lines) |
| `reports/p2-r7b-fix.md` | this report | |
| `reports/p2-r7b-scratch/` (2.1 MB) | `part2-before-r7b.md`, `part2-c57e456.md`, `s1-c57e456.md`, `s1-old.md`, `s1-new.md`, `pool-c57e456.tsv`, `pool-63b57c0.tsv`, `tok-before.txt`, `tok-after.txt`, `tok-am1.txt`, `code/pool.py`, `code/tok.py`, `code/vid.py`, `code/oldcheck.py`, `code/editf.py` | |

## 3. Task items

**Item 1: §1 not edited.** Applied. All F edits went through `code/editf.py`, which asserts §1 is unchanged before it
writes. M #10: cmp exit 0 (section 4).

**Item 2: AM1.** Applied. Header: title, status (as G1 asks), sources with SHA-256 at `c57e456` (taken by me), DESO3's
line ranges. 18 numbered changes; each gives §, line, the old text in a fenced block, the new text, the basis (ruling
and R path:line). M #9: each old text is found exactly once by `grep -F -c` in §1 extracted from
`git show c57e456:<Part 2>` (lines 81-433), at the line the change names (18 of 18 OK).

| Change | Where (F line) | Covers |
|---|---|---|
| 1 | §1 heading (81) | "complete except §14 items 33 (b) and 38" → complete by AM1 |
| 2, 5, 6, 13 | §1.3 (119), §1.4 item 3 (128), §1.5 part (3) (137), §1.16 `ENGINE_Y` row (271) | V1: on a stopped family `ENGINE_Y` is filled when that family's MAIN_F retrain is prepared (PP18's main clause; DESO2 item 36 (2)); if Y differs, the X retrain also runs under MAIN_F (R: DES:172-174; PP:103-104) |
| 3, 7 | §1.3 (120), §1.5 retrain bullet (139) | V7 tag on the build item; the X retrain under MAIN_F also needs the kit path (I) |
| 4, 8, 11 | §1.4 item 1 (126), §1.8 (182, 184) | item 38: both `encode_generation_prompt` for every list prompt and `encode_train` for every `s3_safe` and S1 pair, at the main-recipe limits (R: DES:177-178) |
| 9, 14 | §1.8 (183), §1.16 (276) | V6: a reduced S4 list changes MAKER; a reduced S3 list may not (`lists.s3.size` null; M #6) |
| 10, 12, 14 | §1.8 (183), §1.10 (198), §1.16 (276) | item 33 (b) with V3: new s-pool record by the same script; `lists.s3_subset.ids` and `lists.s1.ids` drop the same ids (R: `score_s3_datarx.py:101-105`, re-read); SHA-256 into the settings' pins by a recorded lead step (today's pin: PINS `shared.sealed_lists_1b.record`, `pins_78b.json:25`, I) |
| 15 | §1.17 (280) | V4: "appends lines 128-165" (M #4: `wc -l` 127, 165, 184 at `197ea37`, `63b57c0`, `c57e456`; hunks `@@ -125,3 +125,41 @@` and `@@ -163,3 +163,22 @@`) |
| 16 | §1.17 Table D header (380) | optional job 5: engine X identity is M (M #7) |
| 17 | §1.18 item 15 (421) | label line confirmed (R: DES:183-184) |
| 18 | §1.18 after item 16 (422) | new item 17: DESO3 and GXI in ruling 16's form ("none reads" for DESO3 is I) |

AM1 ends with "What AM1 does not change" (5 bullets).

**Item 3: F edited in place outside §1.** Applied (40 asserted replacements):
- Status line: one sentence naming AM1. Revision chain: a round-7b sentence (13:55 and 13:57 UTC).
- Short names: DES re-taken (`108f8789…` at `16c2d08`, unchanged at `c57e456`; 184 lines); DESO3 defined (DES:167-184);
  DESO2 range `DES:129-165` (V4; both places); P2FV cite `p2-full.md:44-60` (V5); P2R7F, P2R7V, AM1 and GXI added (GXI
  `cc0d468f…`, working tree, "not yet committed" stated); the HEAD entry gains `c57e456`, `16c2d08` and the diff list;
  "at `c57e456`" added to the P1/PP, PLAN-PR4, RK/SR78/RUN78/PT78 and K5W statements; P2R7V's V-labels in the labels list.
- §0: item 14 takes item 38's coverage; new item 17 (what this revision saw); the "not seen" paragraph gains round 7b.
- §2.2: the second MAIN_F pod if Y differs (DESO3 V1).
- §10.2, §10.3: V2 as ruled.
- §13: row 31. §13.1: the round-7b table (DES's hash and length) and a table of corrected cites and bases (V4, V5,
  the engine identity basis).
- §14: preamble (V4 range; DESO3; "Still open: item 40"); item 6; item 33 (a) gains V6, (b) closed; item 36 gains V1;
  item 38 closed; new item 39 (V2, closed); new item 40 (open, a record).
- §15: preamble per V7; item 14 tagged I (V7) and gains the X retrain; item 15 gains the s-pool record's id lists.
- §16.1 edit 2 (V1), §16.4 (the X retrain; the new s-pool record), §16.5 items 7, 10, 11 confirmed by DESO3; new item 12.
- End line rewritten for the committed state and AM1.

**Item 4: hashes and cites re-taken at `c57e456`.** Applied. Section 5.

**Item 5: no new decision.** Every new sentence quotes or restates DESO3, GXI G1, PP18 or DESO2. Consequences I added
are tagged I: the pack exists before the MAIN_F retrain runs on Y (AM1 change 6); the X-retrain path in §15 item 14;
the new record named by `--s-pool-record` (change 12); the record's pin being PINS `shared.sealed_lists_1b.record`
(change 10); the second pod in §2.2 (follows from V1).

## 4. §1 cmp result

M #10: `awk '/^## 1\. The scorer section/{on=1} /^## 2\. /{on=0} on'` on `git show c57e456:<Part 2>` and on the final
F; `cmp` exit 0; 353 lines each; both SHA-256 `9c6979a57424d9575733a1857bf8c823fc7bd38c8fdf4e5e53bfda2d46e673a9`.

## 5. Hashes re-taken

- M #2: `git diff --name-status 63b57c0 c57e456`: 2 M (DES, `research/FOCUS.md`), 17 A (Part 2, the handover note,
  15 BR files of round 7a). Nothing under `scripts/`, `runkit/`, `experiments/`. FOCUS: 2 lines added, 0 removed.
- M #3: my pool: 6,080 blobs at `c57e456`, 5,494 hashed, 586 skipped by name; 6,063 / 5,477 / 586 at `63b57c0`.
- M #5: F before (round 7a text): 468 hex occurrences, 272 distinct. 207 name the same file at both commits (4 also
  name new scratch copies; the main path is the same). Only at `63b57c0`: DES `af190ede…` (two forms). Only at
  `c57e456`: `dbce35ba…` (a round-7a scratch copy). 62 name no pool file: the anchor record `5d23fa2b…` (hidden by my
  skip rule; equal to its file at both commits by path, M #5), commit ids (all resolve, M #4), old hashes (re-computed
  at their commits: DES `72d57b20…`, `4c2b5cb2…`, `af190ede…`; RK `57ad4148…`; `pack_setup.py` `40b99b1a…`, `f0f098f2…`;
  README `d7ee370d…`; RUN78 `6144546a…`; M #4), P2FV's `edb0cead…` (lost, as stated), and record values (each in at
  least one committed file outside F and BR, M #5).
- **Differs: one value.** DES `af190edea8a3d1fe…` → `108f87894beb9b4d…`, commit `16c2d08` (appends DESO3). Logged in
  §13.1 with both full values. No §1.17 value differs.
- M #11: F after: 550 occurrences, 288 distinct; new tokens are DES's new hash, `1889e8e5…`, P2R7F's and P2R7V's
  hashes, commits `16c2d08` and `c57e456`, GXI's working-tree hash, and the old hashes written in §13.1. AM1: 28
  distinct; all are commits, files at `c57e456`, the engine identity (M #7), DES's old value, or GXI's hash.
- Line cites: unchanged bytes for every cited file except DES; DES only appends (lines 166-184), so its old cites
  stand (re-read :7-8, :84, :86-90, :132, :139-142, :154, :155-158, :165-184). New cites re-read: GXI:5-7, :10-25,
  :19-25, :38-39; PP:100-105; RK:106, :148, :1183, :1220-1228; `pins_78b.json:20-32`; `score_s3_datarx.py:7-11`,
  :99-106; `make_untuned_answers.py:75-79`, :154-157; `p2-full.md:43-61`; MAKER:209-247 (its `lists.s4` lines);
  `experiments/safety_selection/common.py:31-36`; `experiments/minimal_safety/common.py:27-30`; P2R7V:37-43, :107-108,
  :183-184.

## 6. Commands (all foreground, each under 1 minute; exit 0 unless stated)

1. `rev-parse HEAD` of MAIN and WP (`c57e456`); `shasum`, `wc -l` of F (`1889e8e5…`, 875); copy to scratch.
2. `git diff --name-status 63b57c0 c57e456`; `git log 63b57c0..c57e456`; `--numstat` of DES and FOCUS.
3. `code/pool.py` at `c57e456` and `63b57c0` (`.venv -I -B`).
4. `git rev-parse` of 9 commits; `git show <rev>:<path> | shasum -a 256` for 9 old values; `wc -l` of DES at 4 commits; `git diff` hunks of DES at `0e88dfc` and `16c2d08`.
5. `code/tok.py` on the old F; `git show <rev>:<anchor record> | shasum` at both commits; `git grep -l -F` for the 62 unmatched tokens.
6. `git show c57e456:<file> | .venv/bin/python -I -B -c ...` printing `lists.<name>.size` only, for the two derived untuned settings and the 1B base: `s3` None, `s4` 512, `sd600` 600 in each.
7. `code/vid.py` at `c57e456` and `63b57c0`: "files 29 identity 472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892" at both (= RK:106 `ENGINE_X`); `git ls-tree` of `experiments/safety_selection/` (22 `.py` files).
8. `sed -n`, `grep -n` of the cited lines (section 5); `shasum` of the AM1 source files at `c57e456` and GXI in the working tree; `git log` of GXI's path (empty).
9. `code/oldcheck.py` on AM1 against §1 at `c57e456`: 18 of 18 OK (run twice, after the last AM1 edits).
10. §1 extract and `cmp` (exit 0).
11. `code/editf.py` (40 replacements, each count asserted; §1 asserted unchanged); `code/tok.py` on the final F and AM1.
12. Final: `git status --short` of WP (F modified, AM1 untracked); MAIN `git status --short` 20 lines (pre-existing; none mine); `find __pycache__` 0; `du -sh` of scratch 2.1 MB; `shasum` of F and AM1.

## 7. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| §1 of F unchanged byte for byte | passed | M #10, cmp exit 0 |
| AM1 header (title, status, sources with SHA-256 at `c57e456`) | passed | AM1 lines 1-31; M #8 |
| Each AM1 old text verbatim in F's §1 by `grep -F` | passed (18 of 18, once each, at the named line) | M #9 |
| V1, item 38, item 33 (b) with V3, V6, V4 (§1.17), §1.18 item 15, heading covered | passed | AM1 changes 1-15, 17 |
| Optional job 5 (engine identity M) | passed, done from git blobs without importing the kit or the engine | M #7; AM1 change 16 |
| AM1 ends with what it does not change | passed | AM1 last section |
| Status line names AM1; revision sentence with `date -u` times | passed | F lines 3, 5 |
| Short names: DES re-taken, V4, V5, AM1, GXI (uncommitted, stated) | passed | F short names |
| §10.2, §10.3 V2 | passed | F §10 |
| §14: 33 (b), 38 closed; V2 added closed; V4 in preamble; V6 in 33 (a) | passed | F §14 items 33, 38, 39 |
| §15 V7 tag on item 14; item 15 s-pool record ids | passed | F §15 |
| §16.5 items 7, 10, 11 confirmed | passed | F §16.5 |
| §13, §13.1 change log with both values and commit | passed | F §13 row 31, §13.1 |
| Every hash and line cite re-taken at `c57e456` | passed (one difference, DES) | section 5 |
| No new decision | passed, with the I-tagged consequences in section 3 item 5 | section 3 |
| No git state change; MAIN read only | passed | M #12 |
| Kit suites, mutants | not tested (a text track; no code changed, M #2) | |

## 8. Open items for the lead

1. **§14 item 40 (new, open; a record).** DESO2 item 35 confirmed DES's header covers DESO and DESO2. DESO3 has no such
   line. AM1 change 18 and §16.5 item 12 write "none reads a 1B repair outcome" for DESO3 as I. The lead may confirm.
2. GXI is uncommitted. Its SHA-256 in F and AM1 (`cc0d468f…`) is the working-tree value at 13:55 UTC. If GXI is
   edited before its commit, both cites go stale.

## 9. Concerns

1. AM1 change 6 adds "so the pack exists before the MAIN_F retrain runs on Y" (I). DESO2 item 36 (3)'s own words
   ("Y's pack ... follow that certificate") are kept beside it, so a reader sees both. V1 makes the order clear.
2. AM1 change 12 (§1.10's `--s-pool-record` names the new record) and the PINS pin named in change 10 are I. DESO3
   says only "the settings' pins". PINS `shared.sealed_lists_1b.record` (`pins_78b.json:25`) is the one pin of the
   record I found (M: `git grep -l bcca59ac` under `scripts/` and `runkit/`: PINS, SC, the 1B kit's `stage1_rules.py`).
3. I considered a gap on `ENGINE_Y` being one global pin (R: RK:148) when only one family stops under [B]. I dropped
   it: the same question exists for PP18's normal event (two families' retrains prepared at different times), and V1
   adds no new ambiguity (I).
4. The 62 unmatched tokens were checked by category, not one by one by path, except the anchor record and the old
   hashes. Their files did not change (M #2), and round 7a's verifier checked them at `63b57c0`.
5. `reports/p2-r7b-scratch/` (2.1 MB) can be deleted after review.

## 10. Follow-up of 8 Nov (GI XI's GXI G2; written 14:06 UTC, `date -u` 14:05:58)

The lead added GXI G2 (recorded 2026-11-08T14:04 UTC; R: GXI:36-45). It confirms that DES's header covers DESO3 and
closes §14 item 40. This section replaces the earlier sections where they differ: section 2's "after" hashes,
section 8 item 1 (now closed), and section 8 item 2 (the lead will not edit GXI again before its commit).

- **GXI re-hashed (M):** `shasum -a 256` of MAIN's working-tree file gives
  `b8bc7a5bf8d1f922ca6f53ec90891881c14ec8fc0ca7557d07b2e062ff91283f`, 50 lines. This equals the lead's value. It is
  still uncommitted (`git log` of the path is empty). The old value `cc0d468f…` now appears 0 times in F and in AM1;
  the new value appears once in each (M: `grep -c`).
- **F edits (8 asserted replacements by `code/edit-g2.py`, plus one `sed` that removed my history note of the old
  hash):**
  - the GXI short name now has the new hash and G2;
  - the revision chain gains a follow-up sentence (14:05 UTC);
  - §0 item 17 names G2;
  - GXI's money cite moves from :38-39 to :49-50, because G2 is inserted before that section;
  - §13 row 31 now says item 40 is closed by GXI G2;
  - the §14 preamble now says "No item is still open";
  - §14 item 40 is closed by GXI G2;
  - §16.5 item 12 now reads "confirmed by the lead (GXI G2 …)".
- **AM1 edits (3 asserted replacements):** the GXI source row has the new hash, G2 and 14:04 UTC. Change 18's new
  text and its basis now read "confirmed by the lead (GXI G2 …)" in place of the inference. The 18 old texts are
  unchanged: re-checked, 18 of 18 found once in §1 at their lines (M).
- **§1 cmp (M):** §1 extracted from `git show c57e456:<Part 2>` and from the new F: `cmp` exit 0. Both are 353 lines,
  SHA-256 `9c6979a57424d9575733a1857bf8c823fc7bd38c8fdf4e5e53bfda2d46e673a9`.
- **Final SHA-256:**
  - F: `c094e9e34a870ccbc1b3bb452a849f4f0e5d826a8f24b87afe9325765a9d75d4` (903 lines).
  - AM1: `173819fe169f93af11d057b8553174289ea03545351d44dd98662fe99730fac2` (334 lines).
- **Open items now:** none in §14. No git state changed, and there is no `__pycache__`.

## 11. Second follow-up of 8 Nov (the re-verifier's W1-W11; written 14:30 UTC, `date -u` 14:30:18)

The lead asked for all of W1-W11 from `reports/p2-r7b-verify.md` (VERIFIED_WITH_MINOR). GXI was not touched. All
edits are asserted replacements made by `p2-r7b-scratch/code/edit-fu2.py`: 15 in F and 7 in AM1. The script checks
that F's §1 is unchanged before it writes. This section replaces section 10's final hashes.

| W | What was done | Where |
|---|---|---|
| W1 | `p2-full.md:46-60` → `:44-60`. The one hit left is §13.1's "before" value (M: `grep -c` 1). | F §14 item 2 (b) |
| W2 | Added the §1 cmp record: the command, lines 81-433 at `c57e456` and 86-438 here, exit 0, 353 lines, `9c6979a5…`. | F §13.1, round-7b note |
| W3 | Added one sentence to each status: "AM1's rules, like §1's, are fixed from AM1's commit (A10); a later change is a new dated amendment." The lead adopted it; I recorded it as such in F's revision sentence. | AM1 status; F status line |
| W4 | Change 14 now uses V6's wording: "a reduced S4 list changes MAKER's code and hash; a reduced S3 list may not, because `lists.s3.size` is null". | AM1 change 14 |
| W5 | G1's sources are now named in full: Part 2's status line, P2R7V, DES's third set (its preamble), and the commits' file lists (R: GXI:10-34). | AM1 change 18 |
| W6 | Added "(I)" in both places. | AM1 change 6; F §2.2 |
| W7 | "the build items of DESO, DESO2 and DESO3". | F §16.4 |
| W8 | Added a note: the line numbers are Part 2's at `c57e456`. In the round-7b file, §1 sits 5 lines lower (lines 86-438). | AM1 "How to read the changes" |
| W9 | Title now says "6-8 Nov 2026". The status line now says §1 "was committed at `16c2d08`". The end line now reads "At the freeze, AM1 is frozen with this file (both by explicit path, both SHA-256 values in FOCUS; GXI G1 item 4)". | F title, status line, end line |
| W10 | Added "and `c57e456`" to all eight labels (§2.3 heading, §4.2, §7, §8.3, §8.6, §9, §14 item 3, §16.3). Basis (M): every value is in my `c57e456` pool at its path. README is `8304db08…` at both commits, and its :127 and :133 still hold the rates and "stop, never delete". `git diff --stat 63b57c0 c57e456` over `scripts`, `runkit` and the sealed-edit folders is empty. | F |
| W11 | AM1's status now lists everything AM1 carries, with change numbers. The "does not change" bullet now notes DESO3 V1's addition: `ENGINE_Y`'s event and the X retrain under the main config. | AM1 status; last section |

The revision chain has one more sentence (14:29 UTC).

**Checks (M):**
- §1 cmp: `cmp` exit 0. 353 lines. Both SHA-256 `9c6979a57424d9575733a1857bf8c823fc7bd38c8fdf4e5e53bfda2d46e673a9`. In the new F, §1's heading is line 86 and "## 2." is line 439.
- The 18 old-text checks: 18 of 18 OK.
- Diff: `p2-r7b-scratch/followup2.diff`, a unified diff of F and of AM1 against their pre-follow-up copies (`F-pre-fu2.md` `c094e9e3…`, `AM1-pre-fu2.md` `173819fe…`). It has 15 hunks and 164 lines.
- There is no `__pycache__`. No git state changed.

**Final SHA-256:**
- F: `8f7caece1a16887029e156b31167426314184cd0fc8e828f320ca30822a15662` (903 lines).
- AM1: `b9158bbc9be40726bcd7ef683291f84018998498fe5aa6844d933b48797b8711` (334 lines).
