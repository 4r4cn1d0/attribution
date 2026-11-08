# 7-8B pre-registration, Part 2, amendment 1 (AM1, 8 Nov 2026): the scorer section (§1)

**Status.** A dated amendment of Part 2's §1 (the scorer section), written 8 Nov 2026 (clock read with `date -u` at 13:55 UTC) before any 7-8B scorer output exists. It governs where it differs from §1. It is frozen with Part 2 at Part 2's freeze (both by explicit path, both SHA-256 values in FOCUS; GXI G1 item 4). It changes no rule fixed at `16c2d08`. It fills the two items §1's heading names as open, Part 2 §14 items 33 (b) and 38, by DES's third set (DESO3), and it corrects §1's text to rulings that already bind (PP18's main clause; DESO2 item 36; DESO3 V1). Part 2 itself is not edited in §1: its §1 is byte for byte the text committed at `16c2d08` (M: `cmp` of §1 extracted from `git show c57e456:<Part 2>` and from the revised file; Part 2 §13.1). The form is GXI's ruling G1 (R: GXI:19-25).

Written by the Track P2 text-fix worker of round 7b for the main-study lead (General Implementation XI). Read-only on the repository except Part 2 and this file. No pod, no spend, no network, no install, no download, no agent. No judge output, answer, generation, sample, prompt text, `selector.jsonl` or `hidden/` file was opened; from settings files only list sizes and hashes were printed. **Nothing here is a new decision.** What its author saw is Part 2 §0 item 17: rulings, reports, hashes, code lines and list sizes; no outcome.

**Labels.** **M** = measured (the command follows). **R** = read (path:line). **E** = estimate. **I** = inference. Short names are Part 2's ("Short names"), plus the sources below.

## Sources (SHA-256 at the main checkout's HEAD `c57e456`; M: `git show c57e456:<path> | shasum -a 256`, except GXI)

| Short name | Path | SHA-256 |
|---|---|---|
| Part 2 | `research/experiments/2026-11-06-78b-preregistration-part2.md` as committed at `16c2d08` (unchanged at `c57e456`) | `1889e8e51b0ad9d0eef5be29367cc4dae930d184b79c0d16ea7775056473269e` |
| DES (with DESO, DESO2 and DESO3) | `.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part2-design-20261106.md` (184 lines; DESO3 is lines 167-184, appended at `16c2d08`) | `108f87894beb9b4db79a2eee7e5980e0dbe8f6386145ff17f6ac5bd8ec2409fe` |
| GXI | `.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-gi-xi-20261108.md` (the GI XI rulings, G1 and G2; **not yet committed**; M: `shasum -a 256` of the working-tree file, 8 Nov 14:04 UTC) | `b8bc7a5bf8d1f922ca6f53ec90891881c14ec8fc0ca7557d07b2e062ff91283f` |
| PP | `.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part2-prep-20261105.md` | `336b358006a2473af55663002c1cc0a722ce0ed9cb4eda8a95edb705535cc9df` |
| RUL | `.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-20261105.md` | `65e477b0ac1e772c0cb87b6230b1a4212811d3ae960cb86dee156baa2c3ab370` |
| ADD | `.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-addendum-20261105.md` | `ff3498768bf3432ff5a5aaedef1781968dfdec533d31469d7b6ba3e5e2ed6427` |
| P2R7V | BR `p2-r7-verify.md` (round 7a's re-verifier; its V1-V7, cited "Vn") | `d75f0d6922f08ab8ff7bd6f62d1b35156a23675c76fcba71318f2bad9504fec3` |
| P2R7F | BR `p2-r7-fix.md` (round 7a's text fix) | `b3db879ff1fa301bdbf63528c1d01929f7008c03ddc7198fd154b3a342740c6b` |
| `score_s3_datarx.py` | `scripts/stage1/score_s3_datarx.py` | `772e6ae546843b42c3a7564a644cffa269c38ffb30f4db0d59f0f405a9d5aace` |
| `make_untuned_answers.py` | `scripts/stage1/make_untuned_answers.py` | `c37ac452b931c84ed28b45e9cfeed9cc9a07ec47ce5f1c6fd1bbef95086743c4` |
| MAKER | `scripts/scale78b/make_scorer_settings_78b.py` | `7c8f249138b1083b54d7d7586907815db41b7cc65ef402e582aad108d48179f5` |
| PINS | `scripts/scale78b/settings/pins_78b.json` | `057db73b3b5ebe899a4e88e943f33c65e711228a4e176ec3f8fff5a5b5e45eab` |
| The untuned settings | `scripts/scale78b/settings/make_untuned_answers__olmo2-7b.json`; `…__llama31-8b.json`; the 1B base `scripts/stage1/settings/make_untuned_answers.json` | `b489d00a6dce8a988c86c5045e2efe7776e3103e3317af7f69c1c39350f10a41`; `2d32312156f16e6a074e41d06473665e5cba87f9da90b6411393669fed149d43`; `4bf2cc1a2493bc154d314105a085f0166933d1147a37e29fd42c7348ba9d9d8c` |
| RK | `runkit/stage1-78b/rules_78b.py` | `68bf8f45998c84d7ef99a3c7c43bc67f52b498003e69e8e1130c2b2b8970a25c` |
| The engine's identity rule | `experiments/safety_selection/common.py` (`code_identity`, :31-36); `experiments/minimal_safety/common.py` (`canonical_json`, :27-30) | `48df129df22c6277dc48c5c41a8f44cd6c44eae2893a4ecc3763d8276d505642`; `8d8aaaee675dab9ea063c097db4395dba7e0a6a40ecf63a012d5e7ee364415a7` |

**DESO3** = DES's section "Rulings on Part 2's open items, third set", recorded 2026-11-07T14:45 UTC, after round 7a (R: DES:167-184). Its rulings: V1 (DES:172-174), V2 (DES:175-176, outside §1), item 38 (DES:177-178), item 33 (b) with V3 (DES:179-182), the three label lines (DES:183-184).

All code and settings files above are the same bytes at `63b57c0` and `c57e456` (M: `git diff --name-status 63b57c0 c57e456` names only DES, `research/FOCUS.md`, Part 2, the handover note and round 7a's reports with their scratch folders).

## How to read the changes

Each change names the § and its line in Part 2 at `c57e456` (the same bytes as `16c2d08`). **Old** is quoted exactly; each old text occurs in Part 2's §1 (M: `grep -F -c` of each old text in §1 extracted from `git show c57e456:<Part 2>` lines 81-433, the heading line to the line before "## 2."; each count is 1). **New** replaces the old text in that place. Where a change adds text, the old text is kept and the new text follows it. The basis gives the ruling and its R path:line.

## Changes

### 1. §1's heading (line 81)

**Old**

```text
complete except §14 items 33 (b) and 38
```

**New**

```text
complete: §14 items 33 (b) and 38 are filled by amendment 1 (AM1, 8 Nov 2026)
```

**Basis.** DESO3 item 38 and item 33 (b) with V3 (R: DES:177-182); GXI G1 item 1 (R: GXI:19-25). Changes 4, 8 and 11 write item 38 in; changes 10, 12 and 14 write item 33 (b) in.

### 2. §1.3, engine Y's pack on a family whose anchor job stopped (line 119)

**Old**

```text
On a family whose anchor job stops, there is no S_78_F; the a0-1101 retrain then runs under MAIN_F on Y, and Y's pack, KD9's re-measure, B+Qi on Y and the confirmation follow that certificate as ruling 10 says (DESO2 item 36; §1.5).
```

**New**

```text
On a family whose anchor job stops, there is no S_78_F; the a0-1101 retrain then runs under MAIN_F on Y (DESO2 item 36 (2); §1.5). On that family, `ENGINE_Y` is filled, and Y's pack built, when that family's main-config (MAIN_F) retrain is prepared (PP18's main clause; DESO3 V1); PP18's parenthetical "after the anchor job and S_78" does not apply there. If Y differs, ruling 10's second job, the X retrain, also runs under MAIN_F (DESO3 V1). KD9's re-measure, B+Qi on Y and the confirmation follow that certificate as ruling 10 says (DESO2 item 36 (3)).
```

**Basis.** DESO3 V1 (R: DES:172-174): "`ENGINE_Y` is filled when that family's main-config retrain is prepared (PP18's main clause). If Y differs, ruling 10's second job, the X retrain, also runs under the main config." PP18's main clause (R: PP:103-104, "Engine Y's pack is built when ruling 10's retrain is prepared (after the anchor job and S_78; A2)"). DESO2 item 36 (2), (3) (R: DES:139-142). P2R7V V1 (R: P2R7V:37).

### 3. §1.3, the kit's path (line 120)

**Old**

```text
That is a build item (§15 item 14).
```

**New**

```text
That is a build item (§15 item 14; I: it follows from DESO2 item 36 (2); the ruling names no build item). It also covers the X retrain under MAIN_F if Y differs (DESO3 V1; I).
```

**Basis.** P2R7V V7 (R: P2R7V:43); DESO2 item 36 (2) (R: DES:139-141); DESO3 V1 (R: DES:172-174).

### 4. §1.4 item 1, what the encode count covers (line 126)

**Old**

```text
The $0 encode count of the three S-pool lists runs before each family's untuned-answers pass (DESO items 6, 17; §1.8).
```

**New**

```text
The $0 encode count of the three S-pool lists runs before each family's untuned-answers pass (DESO items 6, 17; §1.8). It covers both `encode_generation_prompt` for every list prompt and `encode_train` for every `s3_safe` and S1 pair, at the family's main-recipe limits (DESO3 item 38).
```

**Basis.** DESO3 item 38 (R: DES:177-178); DESO items 6, 17 (R: DES:86-90).

### 5. §1.4 item 3, the retrain on a stopped family (line 128)

**Old**

```text
On a family whose anchor job stops, the retrain runs under MAIN_F instead, on Y, as ruling 10's certificate and ruling 7's confirming check of the side units (DESO2 item 36; §1.5).
```

**New**

```text
On a family whose anchor job stops, the retrain runs under MAIN_F instead, on Y, as ruling 10's certificate and ruling 7's confirming check of the side units (DESO2 item 36; §1.5). There, Y's pack is built, and `ENGINE_Y` filled, when that MAIN_F retrain is prepared, not after S_78 (PP18's main clause; DESO3 V1). If Y's fingerprints differ, the X retrain also runs under MAIN_F (DESO3 V1).
```

**Basis.** DESO3 V1 (R: DES:172-174); PP18 (R: PP:103-104); P2R7V V1 (R: P2R7V:37).

### 6. §1.5, part (3) of the anchor stops in full (line 137)

**Old**

```text
(3) Engine Y's pack, KD9's re-measure, B+Qi on Y and the confirmation follow that certificate as ruling 10 says.
```

**New**

```text
(3) Engine Y's pack, KD9's re-measure, B+Qi on Y and the confirmation follow that certificate as ruling 10 says. The pack's time on that family is DESO3 V1's: `ENGINE_Y` is filled when that family's main-config retrain is prepared (PP18's main clause), so the pack exists before the MAIN_F retrain runs on Y. If Y differs, ruling 10's second job, the X retrain, also runs under MAIN_F (DESO3 V1).
```

**Basis.** DESO2 item 36 (3) (R: DES:142); DESO3 V1 (R: DES:172-174); PP18 (R: PP:103-104). The words "so the pack exists before the MAIN_F retrain runs on Y" are I: a retrain on Y needs Y's pack (R: Part 2 §1.3, "Until then `ENGINE_Y` is null and every Y kind refuses"; RK `engine_sha`, :1220-1228).

### 7. §1.5, the retrain on a stopped family: the kit's path (line 139)

**Old**

```text
the kit's path for that case is a build item (§15 item 14).
```

**New**

```text
the kit's path for that case is a build item (§15 item 14; I: it follows from DESO2 item 36 (2); the ruling names no build item). If Y differs, the X retrain also runs under MAIN_F (DESO3 V1).
```

**Basis.** P2R7V V7 (R: P2R7V:43); DESO3 V1 (R: DES:172-174).

### 8. §1.8, what the encode count covers (line 182)

**Old**

```text
Whether the count also covers `encode_train` of the `s3_safe` (prompt, response) pairs at `max_train_tokens` is not stated (§14 item 38).
```

**New**

```text
The count covers both `encode_generation_prompt` for every list prompt and `encode_train` for every `s3_safe` and S1 pair, at the family's main-recipe limits (DESO3 item 38; was §14 item 38). So a pair that `rep_pass` would skip is found before any untuned answer exists (I).
```

**Basis.** DESO3 item 38 (R: DES:177-178). The main-recipe limits are `max_train_tokens` 3072 and `max_prompt_tokens` 1536 on both families (R: Part 2 §1.1). The last sentence is I from §1.8's "Why the count runs first" (`representation_pass.py:337-348`; `score_s3_datarx.py:103-105`).

### 9. §1.8, a reduced list and MAKER (line 183)

**Old**

```text
So a reduced list changes MAKER's code and hash too (Table A), besides PINS, the reached settings, `PINS-78B.json`, WRAP and SR78 (§1.16).
```

**New**

```text
So a reduced S4 list changes MAKER's code and hash too (Table A), besides PINS, the reached settings, `PINS-78B.json`, WRAP and SR78 (§1.16). A reduced S3 list may not: `lists.s3.size` is null in both derived untuned settings and in the 1B base file, so the size refusal at `make_untuned_answers.py:77-78` does not reach it (M: `lists` sizes printed from the three files at `c57e456`: `s3` null, `s4` 512, `sd600` 600 in each).
```

**Basis.** P2R7V V6 (R: P2R7V:42); DESO2 item 33, "built only if needed" (R: DES:155-158). M: `git show c57e456:<file> | .venv/bin/python -I -B -c` printing `lists.<name>.size` only, for `scripts/scale78b/settings/make_untuned_answers__olmo2-7b.json`, `…__llama31-8b.json` and `scripts/stage1/settings/make_untuned_answers.json`. R: `make_untuned_answers.py:77-78` refuses only when `spec.get("size") is not None` and the count differs.

### 10. §1.8, a reduced `s3_safe` and the s-pool record (line 183)

**Old**

```text
A reduced `s3_safe` also meets the committed s-pool record, which names the `s3_safe` pool's SHA-256 that `s3_score` requires (R: `score_s3_datarx.py:7-11`); DESO2 item 33 does not say how that record is replaced (§14 item 33 (b)).
```

**New**

```text
A reduced `s3_safe` also meets the committed s-pool record, which names the `s3_safe` pool's SHA-256 that `s3_score` requires (R: `score_s3_datarx.py:7-11`). Then the same frozen-on-commit script as the reduced list writes a new s-pool record. The record's `lists.s3_subset.ids` and `lists.s1.ids` drop the same ids, because `s3_score` refuses an id without `s3_safe` features (R: `score_s3_datarx.py:101-105`). Its SHA-256 enters the settings' pins by a recorded lead step (DESO3 item 33 (b) with V3; was §14 item 33 (b)).
```

**Basis.** DESO3 item 33 (b) with V3 (R: DES:179-182). Re-read at `c57e456` (R: `score_s3_datarx.py:101-105`): the score reads `pool_rec["lists"]["s3_subset"]["ids"]` and `pool_rec["lists"]["s1"]["ids"]`, and refuses when any of them has no `s3_safe` features. The settings' pin of the record today is PINS `shared.sealed_lists_1b.record` (R: `pins_78b.json:25`, `bcca59ac…`; I: the pin the ruling names). P2R7V V3 (R: P2R7V:39).

### 11. §1.8, why the count runs first (line 184)

**Old**

```text
so such a skip stops S3 at the Mac step (P2R6V R4).
```

**New**

```text
so such a skip stops S3 at the Mac step (P2R6V R4). The encode count covers `encode_train` of every `s3_safe` and S1 pair (DESO3 item 38), so such a pair is found by the count first.
```

**Basis.** DESO3 item 38 (R: DES:177-178).

### 12. §1.10, the score's s-pool record (line 198)

**Old**

```text
Only the S3 subset is ranked (R: `score_s3_datarx.py:1-21`).
```

**New**

```text
Only the S3 subset is ranked (R: `score_s3_datarx.py:1-21`). If `s3_safe` is reduced, `--s-pool-record` names the new s-pool record of §1.8 by its SHA-256 instead of `bcca59ac…` (DESO3 item 33 (b); I: the score takes the record by PATH:SHA-256).
```

**Basis.** DESO3 item 33 (b) (R: DES:179-182); the command form in §1.10 (`--s-pool-record s_pool_record.json:bcca59ac…`).

### 13. §1.16, the `ENGINE_Y` row (line 271)

**Old**

```text
| RK `ENGINE_Y` | the lead, when the Y retrain is packed, after the anchor job and S_78 (ADD A13; PP18) | every kind on Y |
```

**New**

```text
| RK `ENGINE_Y` | the lead, when the Y retrain is packed, after the anchor job and S_78 (ADD A13; PP18); on a family whose anchor job stopped, when that family's main-config (MAIN_F) retrain is prepared (PP18's main clause; DESO2 item 36 (2); DESO3 V1) | every kind on Y |
```

**Basis.** DESO3 V1 (R: DES:172-174); PP18 (R: PP:103-104). RK's own event has no S_78 clause (R: RK:1183, "the lead fills ENGINE_Y by a recorded step when the Y retrain is packed"). `ENGINE_Y` is one pin for both families (R: RK:148).

### 14. §1.16, how a fill changes MAKER, and the new s-pool record (line 276)

**Old**

```text
(MAKER changes only for a reduced list, §1.8, DESO2 item 33)
```

**New**

```text
(MAKER changes only for a reduced S4 list; a reduced S3 list may not change it, because `lists.s3.size` is null; §1.8, DESO2 item 33, P2R7V V6. For a reduced `s3_safe`, the new s-pool record's SHA-256 also enters the settings' pins by a recorded lead step, DESO3 item 33 (b))
```

**Basis.** P2R7V V6 (R: P2R7V:42); change 9's M; DESO3 item 33 (b) (R: DES:179-182).

### 15. §1.17, the DES line range (line 280)

**Old**

```text
DES's cites stand, because `0e88dfc` only appends lines 129-166 (M: `git diff`, one hunk at :125, 38 lines added)
```

**New**

```text
DES's cites stand, because `0e88dfc` only appends lines 128-165 (M: `git diff`, one hunk at :125, 38 lines added; `git show <rev>:<DES> | wc -l`: 127 at `197ea37`, 165 at `63b57c0`). Line 128 is blank; DESO2's heading is line 129 and its last ruling ends at line 165. At `c57e456`, DES has 184 lines: `16c2d08` appends lines 166-184 (one hunk `@@ -163,3 +163,22 @@`, 19 lines added; DESO3's heading is line 167), so every earlier DES cite still stands (M: `git diff 63b57c0 c57e456`; `wc -l` 184 at `16c2d08` and `c57e456`)
```

**Basis.** P2R7V V4 (R: P2R7V:40). M as given. DES's SHA-256 changed at `16c2d08` (`af190ede…` → `108f8789…`); it is a short-names value, not a §1.17 value, and Part 2 §13.1 logs it.

### 16. §1.17 Table D, the engine identity (line 380; optional, round 7a's job 5)

**Old**

```text
The engine identity was not re-printed at `63b57c0`; I: it holds, because no file under `experiments/` changed after `197ea37`, M: `git diff --name-status`).
```

**New**

```text
The engine identity is re-computed at `63b57c0` and at `c57e456` from git blobs by `code_identity()`'s rule, without importing the engine: the SHA-256 of the canonical JSON of {`safety_selection/<name>`: SHA-256} over the 22 top-level `*.py` files of `experiments/safety_selection/` and {`minimal_safety/<name>`: SHA-256} over its 7 reused modules (29 entries in all, as the rule builds them); `472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892` at both, equal to RK's `ENGINE_X` (RK:106) (M: AM1 change 16; R: `experiments/safety_selection/common.py:31-36`, `experiments/minimal_safety/common.py:27-30`)).
```

**Basis.** P2R7V §9 job 5 (R: P2R7V:184) and its M #19 (R: P2R7V:107-108). M (round 7b): `.venv/bin/python -I -B` of the worker's script `reports/p2-r7b-scratch/code/vid.py` that lists `experiments/safety_selection/*.py` at the revision with `git ls-tree`, hashes each blob from `git show <rev>:<path>`, adds the 7 `REUSED_MODULES` of `experiments/minimal_safety/`, and hashes `json.dumps(files, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"` as UTF-8; it prints "files 29 identity 472fc7f6…" at both revisions (22 `safety_selection/*.py` files and 7 `minimal_safety` modules; M: `git ls-tree --name-only c57e456 experiments/safety_selection/`).

### 17. §1.18 item 15, the label line (line 421)

**Old**

```text
So it is labelled (P2FV2 D7; I: the same form for DESO2 item 36).
```

**New**

```text
So it is labelled (P2FV2 D7; for DESO2 item 36 in the same form, confirmed by the lead: DESO3, "The three label lines", R: DES:183-184).
```

**Basis.** DESO3, the three label lines (R: DES:183-184): "the anchor-stop fallback and LN-14's non-run were chosen after the stage-1 reading, which the authors had seen (P1:33)". P2R7V §9 job 4 (R: P2R7V:183).

### 18. §1.18, a new item 17 after item 16 (line 422)

**Old**

```text
Not a choice after a result, except item 36 (item 15 above).
```

**New**

```text
Not a choice after a result, except item 36 (item 15 above).
17. **DESO3's rulings on §1's items** (V1, item 38, item 33 (b) with V3, and the label lines; recorded 2026-11-07T14:45 UTC, after the stage-1 reading and before any 7-8B scorer output): they read P2R7V's findings, the PP18 clause, the encode functions' names, the s-pool record's id lists and `s3_score`'s refusal. None reads a 1B repair outcome: confirmed by the lead (GXI G2, R: GXI:36-45), which confirms that DES's header (R: DES:7-8) covers DESO3. Not a choice after a result. AM1 itself is GXI's form (G1), which reads Part 2's status line and P2R7V only (R: GXI:10-25); GXI's header says none of its rulings reads a 1B repair outcome (R: GXI:5-7).
```

**Basis.** Ruling 16's form, as §1.18 items 14 and 16. The "none reads" for DESO3 is confirmed by the lead (GXI G2, recorded 2026-11-08T14:04 UTC; R: GXI:36-45), as DESO2 item 35 did for DESO; it closes Part 2 §14 item 40.

## What AM1 does not change

- No rule of §1 fixed at `16c2d08`: the kinds, their engines, their order, the caps (§1.15), the pins and their commands (§1.16 apart from the `ENGINE_Y` row's stopped-family event), k and the removal and add contracts, the lists and their hashes, the reuse rules (§1.7-§1.11), and the anchor job's stop rule (DESO item 7) and its consequences (DESO2 item 36).
- No hash of §1.17's Tables A-D: every one equals its file at `c57e456` (M: Part 2 §13.1, round 7b). Only Table D's engine-identity basis moves from I to M (change 16).
- Not the S-pool lists, their encode rule's drop rule ("dropped by the list's own stage-1 rule") or the frozen-on-commit writer's form (DESO2 item 33).
- Not §0 and §2-§16; those are edited in place in Part 2 (GXI G1 item 2), and V2 (σ̂_A and SR-2's simulation on a stopped family) is there (§10.2, §10.3), not here.
- Not any [to be entered] value; none is entered by AM1.
