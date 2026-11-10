# Part 2 round 7b: adversarial re-verification (p2-r7b-verify)

Started 2026-11-08 14:07 UTC; this version 14:25 UTC (`date -u` before each write). Status: **DONE**.

Targets (read-only for me). F = WP Part 2, SHA-256 `c094e9e34a870ccbc1b3bb452a849f4f0e5d826a8f24b87afe9325765a9d75d4`, 903 lines.
AM1 = WP amendment 1, `173819fe169f93af11d057b8553174289ea03545351d44dd98662fe99730fac2`, 334 lines. GXI = MAIN working-tree
file, `b8bc7a5bf8d1f922ca6f53ec90891881c14ec8fc0ca7557d07b2e062ff91283f`, 50 lines, uncommitted (`git log` of the path: 0
commits). All three equal the expected values at start and at end (M #1, #20). The before-text is
`git show c57e456:<Part 2>`, `1889e8e5…`, 875 lines (M #1).

Tags: M = measured by me (command number in section 8); R = read (path:line); E = estimate; I = inference.
No git state changed (MAIN HEAD `c57e456`, WP HEAD `c57e456`, WP status: F modified, AM1 untracked, at start and end).
No pod, spend, network, install, download, agent, subagent or message. I opened no forbidden folder, no
`selector.jsonl`, `hidden/`, sealed edit file, judge, answer, generation, sample or prompt-text file. My hash pool skips
`tmp/`, selector, `hidden/`, `backups/`, `outputs/`, and non-code, non-settings names with judge, answer, generation,
sample, prompt, sealed or edit. From settings files I printed keys, list sizes and hash prefixes only. The side paper is
not mentioned.

## 1. Verdict

**VERIFIED_WITH_MINOR (0 blocker, 0 major, 3 minor, 8 nits).**

- §1 of F is byte-identical to §1 at `c57e456` (cmp exit 0; check 1).
- All 18 AM1 old texts occur exactly once in §1 at `c57e456`, at the line each names (check 2).
- Every DESO3 ruling, V1-V7, jobs 4-5 and G2 land where G1 puts them. One V5 place was missed (W1). I found no new
  decision; the fixer's four I-tagged claims hold against the code (check 3).
- 0 bad hashes in F and AM1. 0 bad line cites among the 57 cites the round added; 1 old cite left uncorrected (W1).
  Only DES's value differs since `63b57c0` among cited files (check 4).
- The form is right: §1 untouched, AM1 a dated amendment that governs where it differs, nothing reads as the freeze.
  One form gap: AM1's rules are not stated as fixed from its commit (W3, the lead's call).

Advice: fix W1 and W2 (two one-line edits) and decide W3 before the commit; AM1 is still uncommitted, so its nits
(W4, W5, W8, W11) cost nothing to fix now. Or commit and carry them all; none changes a rule.

## 2. Defects

| id | sev | where | defect | fix |
|---|---|---|---|---|
| W1 | minor | F:788 (§14 item 2 (b)); F:780 (§13.1) | V5 was applied only in the short names (F:26). §14 item 2 (b) still says "(R: p2-full.md:46-60)" (M #9: 2 hits of `p2-full.md:46-60` in F, at :780 as the "before" value and at :788). §13.1's new row at :780 says the cite was corrected in "Short names; §14 item 2 (b)". So the change log states a fix that was not made. | At F:788, `p2-full.md:46-60` → `p2-full.md:44-60`. |
| W2 | minor | AM1:3 (status) | "(M: `cmp` of §1 extracted ... ; Part 2 §13.1)". F holds no cmp record: `grep -c cmp` on F is 0 (M #9). §13.1 says only "§1.17 itself is not edited". The M is true (my M #2), but the frozen pointer is wrong. | Add one sentence to F's §13.1 round-7b note: "§1 (lines 81-433 at `c57e456`, 86-438 here): `cmp` exit 0, 353 lines, SHA-256 `9c6979a5…`". Or drop "Part 2 §13.1" from AM1:3. |
| W3 | minor (lead's call) | AM1:3; F:3 status line; F:903 end line | §1's rules are "fixed from that commit" (F:3, A10). AM1 governs where it differs from §1, but AM1 and F say only that AM1 "is frozen with Part 2 at Part 2's freeze" (G1 item 4). That freeze comes "before block A's first pod" (F:3), but after the scorer block's outputs exist: §2.3's A1, L1, S3 and S4 edit hashes are "[to be entered]" (F:494-495), and every such value is entered before the freeze (F:808, §14 item 22). So, as written, AM1's text, and through it §1's rules, could be edited after 7-8B scorer outputs exist. Neither file says AM1's rules are fixed from its commit (I). | One sentence in AM1's status and F's status line, if the lead agrees: "AM1's rules, like §1's, are fixed from AM1's commit (A10); a later change is a new dated amendment." This is a form ruling for the lead, not a text fix I can settle. |
| W4 | nit | AM1 change 14 (new text) | "(MAKER changes only for a reduced S4 list; a reduced S3 list may not change it ...)". "Only for S4" says S3 never changes MAKER; "may not" leaves it open. V6 and change 9 say "may not" (R: P2R7V:42; AM1 change 9). | "(MAKER changes only for a reduced list; for a reduced S3 list it may not, because `lists.s3.size` is null; ...)". |
| W5 | nit | AM1 change 18 (new item 17) | "AM1 itself is GXI's form (G1), which reads Part 2's status line and P2R7V only (R: GXI:10-25)". G1 also quotes DES's third set (GXI:16-17) and the `git diff --name-status 63b57c0 c57e456` file list (GXI:31-32). Neither is an outcome, so the label's point holds. | "... which reads Part 2's status line, P2R7V, DESO3's preamble and the commits' file lists (R: GXI:10-32)". |
| W6 | nit | AM1 change 6 (new text); F:474 (§2.2) | Two inferences carry no inline I tag: change 6's "so the pack exists before the MAIN_F retrain runs on Y" (I only in the basis); §2.2's "a second pod". Both are sound (check 3). AM1 change 8 does tag its inference inline. | Add "(I)" after each. |
| W7 | nit | F:877 (§16.4) | "the build items of DESO and DESO2 (... the MAIN_F retrain path, with the X retrain under MAIN_F if Y differs; a reduced list's writer and, for a reduced `s3_safe`, its new s-pool record ...)". The two added parts are DESO3's (V1; item 33 (b)). | "the build items of DESO, DESO2 and DESO3". |
| W8 | nit | AM1 "How to read the changes" (AM1:35) and change headings | Each change names its line "in Part 2 at `c57e456`". In the round-7b file, which is the one frozen with AM1, §1 sits 5 lines lower (86-438; M #2: the offset is +5 for every §1 line). The old texts are unique in the file, so they can be found, but the numbers will not match the frozen file. | Add to AM1:35: "In the round-7b revision of Part 2 each line is 5 lower (§1 is lines 86-438)". |
| W9 | nit | F:1 title; F:3 status line; F:903 end line | The title still says "(DRAFT, 6-7 Nov 2026)". The status line still says "The scorer section (§1) is committed now", while the end line says it "was committed at `16c2d08`". The end line says "AM1 is frozen with this file, both by explicit path" but drops G1 item 4's "at Part 2's freeze" and "both SHA-256 values in FOCUS" (the status line has the first). | Title "6-8 Nov"; status "§1 was committed at `16c2d08` ... its rules are fixed from that commit"; end line "At the freeze, AM1 is frozen with this file (both by explicit path, both SHA-256 values in FOCUS; GXI G1 item 4)". |
| W10 | nit | F:476, :551, :627, :641, :669, :676, :789, :873 | These per-place M labels still end "at `63b57c0`"; other places gained "and `c57e456`" (short names). §13.1's global sentence covers them, and every value holds at `c57e456` (M #7: the code hashes at :551, :627, :676, :873 and README `8304db08…` are in my `c57e456` pool at those paths; no file under `runkit/` or `scripts/` changed). | Optional: add "and `c57e456`" in each, or leave and rely on §13.1. |
| W11 | nit | AM1:3 (status); AM1:330 ("What AM1 does not change") | The status says AM1 fills items 33 (b) and 38 and corrects §1 to binding rulings. It does not say AM1 also carries P2R7V's V4, V6 and V7 fixes and Table D's basis change (job 5), though changes 3, 7, 9, 14-16 do. The first "does not change" bullet says AM1 does not change the anchor stop rule's "consequences (DESO2 item 36)"; changes 2, 5, 6 and 13 add DESO3 V1's consequences to them (filling a gap, not changing a rule). | Status: add "and carries P2R7V's V4, V6 and V7 text fixes and Table D's engine-identity basis (job 5)". Bullet: "... its consequences (DESO2 item 36), apart from DESO3 V1's `ENGINE_Y` event and X retrain on a stopped family". |

## 3. Check 1: §1 is byte-identical

- M #2: §1 = the heading line "## 1. The scorer section" to the line before "## 2.". At `c57e456`: lines 81-433. In F:
  lines 86-438. `cmp` exit 0. Both 353 lines, both SHA-256
  `9c6979a57424d9575733a1857bf8c823fc7bd38c8fdf4e5e53bfda2d46e673a9`. This equals the fixer's value.
- M #3: the whole-file diff has no hunk inside §1 (hunks at old lines 3-77 and 469-875 only).
- §1 has no stale hash: of its 164 distinct hex tokens, 120 name the same file at both commits and 44 name no pool file;
  none names a file only at one commit (M #7).

## 4. Check 2: AM1's old texts and new texts

- M #4 (`oldnew.py`): for each of the 18 changes, the fenced Old block is found by substring count in §1 at `c57e456`:
  count 1 in §1 and 1 in the whole file, at the line the change names, for 18 of 18 (lines 81, 119, 120, 126, 128, 137,
  139, 182, 183, 183, 184, 198, 271, 276, 280, 380, 421, 422). Changes 9 and 10 share line 183 with disjoint old texts.
- Changes 4, 5, 6, 11, 12 and 18 add text: each New starts with its Old (M #4), as AM1:35 says.
- Six old texts are clauses, not whole sentences (changes 1, 7, 11, 14, 15, 16). Each is
  exact and unique, so each is a valid replacement spec. G1 says "each old §1 sentence"; I do not count this as a
  defect.
- New texts against their rulings (R: DES:172-184; P2R7V:37-43):
  - V1 (changes 2, 5, 6, 13): `ENGINE_Y` filled, Y's pack built, when the stopped family's MAIN_F retrain is prepared;
    the X retrain under MAIN_F if Y differs. Says what DESO3 V1 says. "Y's pack built" is PP18's main clause
    (R: PP:103-104), which V1 names.
  - Item 38 (changes 4, 8, 11): word for word DESO3 item 38. Change 8's last sentence is tagged I.
  - Item 33 (b) with V3 (changes 10, 12, 14): change 10 is DESO3's text; change 12 adds the command's flag (I, true);
    change 14 adds the pin step (W4 on its wording).
  - V6 (changes 9, 14): change 9 as V6 proposed, with M; change 14 over-states (W4).
  - V4 (change 15): the range fix, plus the `c57e456` length facts (M; true). V7 (changes 3, 7): the I tag as proposed,
    plus "covers the X retrain" (I, tagged).
  - Job 5 (change 16): basis I → M. My re-computation agrees (check 4).
  - Label line (change 17): quotes DESO3's label line. New item 17 (change 18): ruling 16's form for DESO3, citing G2
    (W5 on one word).
- No rule fixed at `16c2d08` changes. Every change either fills items 33 (b) and 38, writes V1 (which corrects §1.3,
  §1.4, §1.5 and §1.16 to PP18's main clause and DESO2 item 36 (2); before AM1, the `ENGINE_Y` row's event could not
  occur on a stopped family), or is a P2R7V text or tag fix that G1 item 1 lists (I).

## 5. Check 3: coverage, and the fixer's I-tagged claims

| Source | Where it lands | Result |
|---|---|---|
| DESO3 V1 | AM1 2, 5, 6, 13 (and 3, 7); F §2.2 (:474), §14 item 36 (:822), §15 item 14 (:847), §16.1 edit 2 (:859), §16.4 (:877) | done |
| DESO3 V2 | F §10.2 (:689), §10.3 (:695), §14 item 39 (:825) | done |
| DESO3 item 38 | AM1 4, 8, 11; F §0 item 14 (:66), §14 item 38 (:824) | done |
| DESO3 item 33 (b) with V3 | AM1 10, 12, 14; F §14 item 33 (b) (:819), §15 item 15 (:848), §16.4 | done |
| DESO3 label lines | AM1 17; F §16.5 items 7, 10, 11 (:894, :897, :898) | done |
| P2R7V V4 | F short names (:16), §14 preamble (:785); AM1 15 | done |
| P2R7V V5 | F short names (:26) | **§14 item 2 (b) (:788) missed (W1)** |
| P2R7V V6 | AM1 9, 14; F §14 item 33 (a) (:819), §15 item 15 | done (W4 wording) |
| P2R7V V7 | F §15 preamble (:832), §15 item 14 (:847); AM1 3, 7 | done |
| P2R7V jobs 4, 5 | AM1 17; F §16.5; AM1 16, F §13.1 (:781) | done |
| GXI G1 items 1-4 | AM1; F status line, short names, §13 row 31, §13.1, end line | done (W3, W9) |
| GXI G2 | F short names (:27), §0 item 17, §13 row 31, §14 preamble and item 40 (:826), §16.5 item 12; AM1 source row, change 18 | done; old GXI hash `cc0d468f` 0 times in F and AM1, new one once in each (M #9) |

Nothing dropped except W1. Nothing new decided (I): each new sentence restates DESO3, G1, G2, PP18, DESO2 or P2R7V,
or is tagged I.

The fixer's I-tagged claims, read against the code at `c57e456`:

1. **AM1 change 6, the pack exists before the MAIN_F retrain runs on Y.** Holds. RK's event: "the lead fills ENGINE_Y
   by a recorded step when the Y retrain is packed" (R: RK:1183; RK:148). A Y job needs `ENGINE_Y`: `sc_needed_pins`
   adds it for engine Y (R: RK:1305-1308; comment at RK:1185), and `engine_sha("Y")` refuses while it is null
   (R: RK:1220-1228). DESO3 V1 fills it when the retrain is prepared, so before it runs. Untagged inline (W6).
2. **AM1 change 12, `--s-pool-record` names the new record.** Holds. The real flag is `--s-pool-record`
   (R: `score_s3_datarx.py:4`, the parser at :135-136 takes "PATH:SHA256", passed at :148 as `s_pool_record`); WRAP
   passes it through (R: `scorers_78b.py:13`, :115). The record is read by `read_pinned` (R: :73) and must have kind
   "stage1 s-pool record" (:79), an `s3_pool.sha256` equal to the summary's `s3_safe` pool and to the untuned record's
   s3 `list_sha256` (:84-90), and the id lists (:101-105).
3. **AM1 change 10, "the settings' pins" = PINS `shared.sealed_lists_1b.record`.** Holds as the only scorer-layer
   settings pin of the record: `pins_78b.json:25` is `"record": {"path": ".ai/inputs/stage1-commitments-20261016/s-pool/s_pool_record.json", "sha256": "bcca59ac…"}`
   under `shared.sealed_lists_1b` (M #10, keys and hash prefixes only). `git grep -l bcca59ac` under `scripts`,
   `runkit`, `experiments` at `c57e456`: PINS, `scripts/scale78b/SCORERS-78B.md` (its command row :59) and the 1B kit's
   `runkit/stage1-olmo/stage1_rules.py` (M #11). MAKER does not pin the record or the S3 list's hash (M #11:
   `make_scorer_settings_78b.py` names S3 pools only on the command line, :273). See concern 2 on SC:59.
4. **§2.2's second pod.** Holds: each scorer kind is a single-job pod (R: Part 2 at `c57e456`, §1.4 line 124), so the
   X retrain is a second pod (I). Untagged inline (W6).

Also checked: AM1 change 9's M. `lists` sizes at `c57e456` (sizes only): both derived untuned settings and the 1B base
give `s3` None, `s4` 512, `sd600` 600 (M #12). The refusal at `make_untuned_answers.py:77-78` fires only when
`spec.get("size") is not None` (R).

## 6. Check 4: hashes and cites

**Changed files since `63b57c0` (M #5).** `git diff --name-status 63b57c0 c57e456`: 2 M (DES, `research/FOCUS.md`),
17 A (Part 2, the handover note, 15 BR files of round 7a). FOCUS +2 lines (one per commit). DES: one hunk
`@@ -163,3 +163,22 @@`, 19 lines added, 184 lines at `16c2d08` and `c57e456`. Nothing under `scripts/`, `runkit/`,
`experiments/`. FOCUS's hash is cited nowhere in F. So DES is the only cited file whose value differs. Confirmed.

**F's hex tokens (M #7, #8; my own regex: 64 hex, or 7-63 hex followed by "…"): 280 distinct, 318 occurrences.**
- 174 name the same file at `63b57c0` and `c57e456`.
- 6 name a file only at `c57e456`, all right: DES `108f8789…` (2 forms), Part 2 `1889e8e5…`, P2R7F `b3db879f…`,
  P2R7V `d75f0d69…`, round 7a's scratch copy `dbce35ba…`.
- 3 name a file only at `63b57c0`: DES `af190ede…` (3 forms), each in a history place (short names :16; §13.1 :758,
  :769, :772).
- 97 name no pool file: 8 commit ids (all resolve); old values re-computed at their commits (DES `72d57b20…` at
  `e5a2f86`, `4c2b5cb2…` at `5c0d091`/`197ea37`, `af190ede…` at `0e88dfc`/`63b57c0`; RK `57ad4148…` at `d203070`;
  `pack_setup.py` `f0f098f2…` at `e5a2f86`, `40b99b1a…` at `197ea37`; README `d7ee370d…` at `197ea37`; RUN78
  `6144546a…` at `e5a2f86`; M #6); P2FV `edb0cead…` (lost, as F states); GXI `b8bc7a5b…` (working tree, M #1); the
  engine identity `472fc7f6…` (M #14). Each of the other 73 occurs in at least one committed file outside F and BR
  (M #13).
- **Bad hashes: 0.** The round's new tokens are only the DES value, Part 2's, P2R7F's, P2R7V's, two commit ids, GXI's,
  and old values in §13.1 (M #8: token sets of the old and new F compared).

**AM1's hashes.** 23 distinct tokens. The 17 file hashes in its source table equal `git show c57e456:<path> | shasum`
for 17 of 17, and GXI's equals the working tree (M #1, #15). The 17 are the same at `63b57c0` except Part 2, P2R7F and
P2R7V (added at `16c2d08`) and DES (appended). AM1:31's "same bytes at `63b57c0` and `c57e456`" holds for every code
and settings file it names. **Bad: 0.**

**Engine identity (M #14).** My own script (`vid.py`: `git ls-tree` of `experiments/safety_selection/`, 22 top-level
`*.py` blobs, plus the 7 `REUSED_MODULES` at `experiments/safety_selection/common.py:28`, hashed as `code_identity()`
and `canonical_json` do, R: `common.py:31-36`, `minimal_safety/common.py:27-30`; no import): 29 entries,
`472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892` at both `c57e456` and `63b57c0`, equal to RK:106.

**Line cites.** I re-read every cite the round added or changed.
- AM1: 40 distinct cites, 40 good. They are DES:7-8, :86-90, :139-141, :139-142, :142, :155-158, :167-184, :172-174,
  :175-176, :177-178, :177-182, :179-182 and :183-184; GXI:5-7, :10-25, :19-25 and :36-45; PP:103-104; P1:33; P2R7V:37,
  :39, :40, :42, :43, :107-108, :183 and :184; RK:106, :148, :1183 and `engine_sha` :1220-1228;
  `score_s3_datarx.py:1-21`, :7-11, :101-105 and :103-105; `make_untuned_answers.py:77-78`;
  `representation_pass.py:337-348`; `pins_78b.json:25`; `experiments/safety_selection/common.py:31-36`;
  `experiments/minimal_safety/common.py:27-30`. AM1 also cites Part 2 §1.1's limits; F:101 at `c57e456` gives
  3072 / 1536.
- F: 17 distinct current cites added, 17 good. They are DES:7-8, :129-165, :132, :167-184, :175-176, :177-178,
  :179-182 and :183-184; GXI:5-7, :36-45 and :49-50; RK:106; `p2-full.md:44-60` (:44 is "DESO item 9 / P2FV D11 (i)");
  `pins_78b.json:25`; `representation_pass.py:337-348`; `score_s3_datarx.py:101-105` and :103-105. Two more cites,
  `DES:129-166` and `p2-full.md:46-60`, appear only as "before" values in §13.1, which is right.
- **Bad: 1, an old cite not corrected: F:788 `p2-full.md:46-60` (W1).**
- AM1's 18 change line numbers are good for `c57e456` (W8 on the +5 offset in the round-7b file).
- FOCUS cites in §0 item 17 and the "not seen" paragraph hold: the entries "PART 2'S SCORER SECTION IS COMMITTED; ..."
  (2026-11-07T14:45 UTC, ends "No pod, no spend; no stage-1 outcome read") and "HANDOVER: GENERAL IMPLEMENTATION X ->
  XI" (14:47 UTC) are the two FOCUS lines `63b57c0..c57e456` adds (M #5).

## 7. Checks 5 and 6: consistency and form

- §14 preamble, "No item is still open": true. All 40 items are marked Closed; item 33 has (a) and (b) both Closed;
  no item text says open, not ruled or not stated (M #9).
- These agree with AM1 and with each other: the status line (F:3, :5), §0 items 14 and 17, §13 row 31, §13.1, §14
  items 6, 33, 36, 38-40, §15 preamble and items 14-15, §16.1 edit 2, §16.5 items 7 and 10-12, and the end line. Only
  W1 (§13.1 vs §14 item 2 (b)) disagrees; W7 and W9 are wording. Each F cross-reference to an AM1 change number is
  right (11 references on 10 lines).
- Row 31 summarises by source. It does not list the §2.2, §0 item 17 or §16.4 edits. That is not a disagreement.
- The form:
  - §1 is untouched (check 1). No draft text says §1 was edited.
  - F's status line names AM1, says it governs where it differs, and says it is frozen at Part 2's freeze. The status is
    still DRAFT. Nothing says this commit is the freeze.
  - AM1's status is clear: dated (8 Nov), written before any 7-8B scorer output, governs where it differs, frozen with
    Part 2 at the freeze, changes no rule. Its "How to read" and "What AM1 does not change" sections are clear (W8,
    W11 nits).
  - The gap is W3: the time from which AM1's rules are fixed.

## 8. Commands (all foreground, each under 1 minute; exit 0 unless stated)

1. `shasum -a 256` and `wc -l` of F, AM1, GXI and `git show c57e456:<Part 2>`; `git rev-parse HEAD` of MAIN and WP;
   `git status --short` of both; `git log` of GXI's path (0) (start, and again at end).
2. `sed -n '81,433p'` of the old F and `sed -n '86,438p'` of F; `cmp` (exit 0); `wc -l`; `shasum -a 256`.
3. `git diff --no-index --word-diff` of the old and new F; hunk headers.
4. `oldnew.py` (my script, `/usr/bin/python3 -I -B`): the 18 Old/New blocks against §1 at `c57e456`.
5. `git diff --name-status 63b57c0 c57e456`; `--numstat` of DES and FOCUS; DES hunks for `197ea37..63b57c0` and
   `63b57c0..c57e456`; `git show <rev>:<DES> | shasum`, `wc -l` at 7 commits; `git show --stat` of `c57e456` and
   `16c2d08`; the FOCUS diff.
6. `git show <rev>:<path> | shasum -a 256` for `pack_setup.py`, README, RK and RUN78 at `d203070`, `e5a2f86`,
   `197ea37` and `63b57c0`; `git rev-parse` of 9 commits.
7. `pool.py` (my script): SHA-256 of every git blob at `c57e456` (6,080 blobs, 5,665 hashed, 415 skipped) and
   `63b57c0` (6,063, 5,648, 415), no content printed.
8. `tok.py` (my script) on the old F, F, AM1 and §1: token classes against both pools; token sets compared.
9. `grep -c`/`grep -n` and `ctx.py` (my context printer) on F and AM1: `cmp`, `p2-full.md:46-60`, `129-166`,
   GXI hashes and cites, `Closed`/open wording in §14, `63b57c0` without `c57e456`, AM1 change cross-references.
10. PINS at `c57e456` through a key/size/hash-prefix printer; `grep -n bcca59ac | cut -c1-40`.
11. `git grep -l -F bcca59ac` and `git grep -n` for `s_pool_record`, `SCORER_PINS`, `sealed_lists_1b` at `c57e456`;
    `git grep -n` of MAKER for its S3 lines.
12. `git show c57e456:<settings> | python3 -I -B -c` printing each `lists.<name>.size` only, for 3 files.
13. `git grep -l -F <token> c57e456` excluding Part 2 and BR, for the 97 unmatched tokens; `git rev-parse --verify`.
14. `vid.py` (my script) at `c57e456` and `63b57c0`.
15. `git show c57e456:<path> | shasum -a 256` for AM1's 17 source paths, and at `63b57c0`.
16. `sed -n`/`nl` reads: DES:1-12, :84-92, :125-184; PP:98-104; RK:100-160, :1165-1230; `score_s3_datarx.py` (all
    160 lines); `make_untuned_answers.py:75-79`, :154-157; `representation_pass.py:335-349`; `common.py` (both);
    P2R7V:1-60, :105-109, :170-194; `p2-full.md:42-62`; P1:33; GXI (all 50 lines); the fixer's report.
17. `find <scratch> -name __pycache__` (0); `du -sh` of my scratch (2.5 MB).

## 9. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| §1 of F byte-identical to §1 at `c57e456` | passed | M #2 |
| Every AM1 old text verbatim in §1 at `c57e456`, count 1, at the named line | passed, 18 of 18 | M #4 |
| AM1 new texts say what the rulings say, no more, no less | passed, with nits W4, W5, W6 | section 4 |
| AM1 changes no rule fixed at `16c2d08` | passed (I) | section 4 |
| Coverage of DESO3, V1-V7, jobs 4-5, G2 | passed except one V5 place | section 5; W1 |
| The fixer's I-tagged claims hold against the code | passed, 4 of 4 | section 5 |
| Every hash in F and AM1 re-computed | passed: 0 bad | section 6 |
| Every line cite the round added or changed re-read | passed: 57 of 57 good; 1 old cite left (W1) | section 6 |
| Only DES differs among cited files since `63b57c0` | passed | M #5 |
| Internal consistency (status, §0, §13, §13.1, §14, §15, §16, end line) | passed except W1; wording nits W7, W9 | section 7 |
| Form (§1 untouched; AM1 dated, governs, frozen at the freeze; not the freeze) | passed; one form gap for the lead | W3 |
| No git state change; read-only; no forbidden file | passed | header; M #1, #17 |

## 10. Jobs for the lead

1. Fix W1 (F:788, one token) and W2 (one sentence in §13.1, or drop the pointer in AM1:3).
2. Rule W3: are AM1's rules fixed from AM1's commit, like §1's? If yes, one sentence in AM1's status and in F's status
   line.
3. AM1 is uncommitted, so its nits (W4, W5, W6's first part, W8, W11) can be fixed now at no cost. F's nits (W6's
   second part, W7, W9, W10) can be fixed now or carried to the freeze.
4. After the edits, re-run the §1 cmp and the old-text check. Each fix above is outside §1 or inside AM1's new texts,
   so neither check should move.
5. At the commit: stage F, AM1 and GXI by explicit path; record the three SHA-256 values in FOCUS; run
   `scripts/stage1/commitments.py check` (post-W1 records rule).
6. After review, delete `reports/p2-r7b-verify-scratch/` (2.5 MB) and the fixer's `reports/p2-r7b-scratch/`.

## 11. Unresolved concerns

1. W3 is a form question the brief's sources do not settle. G1 item 4 names only the freeze. I flag it; I do not rule
   it.
2. If `s3_safe` is reduced, SC's command row (`SCORERS-78B.md:59`, `--s-pool-record s_pool_record.json:bcca59ac…`) and
   §1.17's record row (Part 2 at `c57e456`, line 392) also name the old record. DESO3 names only "the settings' pins".
   The recorded lead step should say whether SC's row is updated (I). The new record must also carry kind
   "stage1 s-pool record" and an `s3_pool.sha256` equal to the reduced pool, or `s3_score` refuses
   (R: `score_s3_datarx.py:79`, :84-90). This is for §15 item 15's build, not a text defect.
3. On a stopped family, §10.2 and §10.3 still say "about 12-15 df per family". DESO3 V2 covers the design but not the
   df line. F says the reduced design is simulated, so I do not count it as a defect.
4. My token counts differ from the fixer's (my regex excludes bare commit ids; my skip rule differs). The two pools
   agree on every result that matters: 0 stale values, and only DES differs. §13.1 states the fixer's counts as their
   own M. I did not re-run their tools.
5. That no 7-8B scorer output exists is R (GXI:49-50; FOCUS 14:45 entry; the commits add none). I did not and may not
   look under `tmp/scale-78b-*`.
