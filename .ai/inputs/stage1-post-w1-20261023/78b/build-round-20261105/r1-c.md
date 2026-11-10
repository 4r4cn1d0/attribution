# R1 Track C: the $0 check tools (encode count, τ_L)

Status: **DONE, fix round done** (§10). Report written 2026-11-08T15:05 UTC; fix round 15:39 UTC (clocks read with
`date -u`; skeleton 14:45 UTC). §1-§7 describe the pre-fix bytes except where §10 says otherwise; §5 and §8 point 2
are updated in place.

- WS = B/ws-c (detached worktree of MAIN at `3481d85`; M: `git log -1`). Scratch: R/r1-c-scratch/.
- Tags: M measured (the command), R read (path:line, WS unless named), E estimate, I inference.
- No pod, spend, network, install, download, agent or message. No git state changed (M: `git status --short` in WS
  lists only the 6 new files). MAIN not written. No existing file changed. No forbidden folder opened. No real list,
  bank or unit opened. Of real files I read only: the two MAIN_F configs (limits, tokenizer fields), the two prepared
  manifests (tokenizer repo, revision, end token; key names), the committed s-pool record (kind, list hashes, id
  counts), `oext_eval.json` (bank pins), `pins_78b.json` and RK (hashes). From `tmp/kt-prepared/` I listed top-level
  names only and loaded the offline tokenizers (M, a smoke on synthetic text; see commands).

## 1. Files created (all new; none existing changed)

| File (WS) | SHA-256 | Lines |
|---|---|---|
| `scripts/scale78b/encode_count_78b.py` | `f2ae2472862c0cbfdf8d2aeb96cbe5e870b6418f71a8227b8f520228d0418d0f` | 607 |
| `scripts/scale78b/tau_l_78b.py` | `4739d6d69ab60f11a7d57afd8edd919de2c11ea471e0b9d6e10964fb650c1d8a` | 283 |
| `scripts/scale78b/tests/test_encode_count_78b.py` | `d853869f94df9cbf64bcdf8d63fd20a6ddfdfbceaa90dbff5cfefbee4113f2ff` | 878 |
| `scripts/scale78b/tests/test_tau_l_78b.py` | `0a96ba2eaea319ad931ca3f74428580bb81f1d97c7ac92f8f3d21f95dba99814` | 360 |
| `scripts/scale78b/tests/mutation_spec_c_78b.json` | `a73fc8ef1eaee9dfefc233b1accb02e65ee5be888c053be590d9f8cd04f2a8a8` | 502 |
| `scripts/scale78b/tests/run_mutants_c_78b.py` | `9aa41e546d26a64c87c22f8aba2cfefb663ef2ead9b4a6aab4b43497a5e31609` | 167 |

M: `shasum -a 256`, `wc -l`, 15:04 UTC. No git-ignored file was copied into WS (the suites need none).

## 2. What each item does, and where

### Item 1: `encode_count_78b.py` (DESO items 6, 17; DESO3 item 38; DES E1; GXB O6, O13; P2 §1.8 with AM1 changes 4, 8, 11)

- **Pins (literal, cited).** MAIN_F path and `config_sha256` (`RECIPES`, :75; R: RK:113-129), P_F's manifest
  (`MANIFESTS`, :82; R: RK:110-111), the three lists (`LIST_PINS`, :86), the S3 subset (`S3_SUBSET_PIN`, :89, from the
  committed s-pool record, M), the s-pool record `bcca59ac…` (:90), which checks run on which list (`LIST_CHECKS`, :93),
  the O-ext record `a810574e…` and 400 (:96), the anchor list `78467c97…` and 128/64 (:100). A test holds every pin
  equal to `pins_78b.json`, RK, `make_anchor_answers.py` and `oext_eval.json` (`test_pins_equal_the_committed_sources`,
  `test_real_oext_settings_pin_the_record`).
- **Inputs by path and pin.** Every input is `PATH:SHA256`; the SHA-256 named must equal the literal pin (`pinned`,
  :179) and the bytes must hash to it (the frozen readers' own checks, or `read_pinned`, :186). An off-pin input
  refuses (exit 2, nothing written).
- **Recipe and limits.** `load_recipe` (:196): MAIN_F must hash to the family's pin; the limits are
  `model.max_prompt_tokens` and `model.max_train_tokens` (1536 and 3072 on both families, M: `test_the_limits_are_main_fs_model_block`).
  **Correction to the brief and PLAN-AB:** MAIN_F has no `generation.max_prompt_tokens` (M: the same test asserts
  the key is absent). Every frozen caller reads `recipe["model"]["max_prompt_tokens"]` (R:
  `scripts/stage1/make_untuned_answers.py:251`, `scripts/stage1_s1/oext_eval.py:525`, `scripts/make_anchor_answers.py:127`),
  so the tool uses that field.
- **Codec.** `real_context` (:221) reads P_F's manifest at its pin (`prepare.read_manifest`) and calls
  `build_s_pool.real_codec` with the family's manifest pin (R: `scripts/stage1/build_s_pool.py:464-473`).
  `check_tokenizer` (:237) refuses unless the manifest's tokenizer is the recipe's (`config.tokenizer_of`: repository
  and revision) with the same end-of-turn token, so the count uses the pod's tokenizer. M: both families pass on the
  real manifests (smoke below).
- **Mode lists** (`run_lists`, :332). The lists are read by the frozen `make_untuned_answers.read_list` (hash, kind,
  distinct safe ids, text prompts, size). The s-pool record (`read_s_pool_record`, :291) must be of kind "stage1
  s-pool record" and name the pinned list and pool hashes. The S1 and S4 ids must equal the record's ids, in order.
  `s3_safe`'s ids must be the record's S3 subset, then S1's rows outside it. S1 rows must equal their `s3_safe` twins.
  Then `encode_generation_prompt` runs on every prompt of S1, `s3_safe` and `s4_candidates`, and `encode_train` on
  every (prompt, PKU-safe response) pair of S1 and `s3_safe` (`refusals_generation`, :260; `refusals_train`, :274). A
  `ValueError` counts under its class name, as the frozen callers count it. The S3 subset's counts are `s3_safe`'s
  restricted to the record's `lists.s3_subset.ids` (:368). `s3_subset.json` is not read.
- **Mode `--bank`** (`run_bank`, :381). `oext_eval.load_pinned_settings()` must pin record `a810574e…` with 400
  planned. The bank is read by the frozen `oext_eval.load_bank`. The named bank SHA-256 must be the record's
  `full_file` hash, and the bank must hold 400 prompts (a shortfall bank refuses). Then `encode_generation_prompt`
  runs at `model.max_prompt_tokens`.
- **Mode `--anchor`** (`run_anchor`, :418; informational only, GXB O6). The list is read by the frozen
  `make_anchor_answers.read_prompt_list` at the frozen pin. The tool runs the job's two checks with the job's own
  functions and limits: `maa._encoded` on the first 64 (prompt, unsafe response) pairs (R: make_anchor_answers.py:118-123,
  the stop at :121), and `encode_generation_prompt` on all 128 prompts at `model.max_prompt_tokens` (R: :125-131, the
  stop at :129). Every failure is counted, and the first failing index of each check is recorded.
  `first_check_that_would_refuse` gives the job's order. The record says it decides nothing. This mode always exits 0
  when it writes.
- **Output.** One canonical JSON record, created once (`write_once`, :512; since the fix round it writes a temporary
  file in --out's folder and hard-links it to --out only when complete, §10). It is never inside any input's folder
  (at any depth) nor inside the prepared folder (`out_ok`, :493). It holds counts by reason, refused ids (ids, or list
  indices for the anchor list), input SHA-256s, the recipe's SHA-256 and limits, the manifest hash, the tokenizer repo
  and its revision prefix (12 hex), the script's SHA-256 and the transformers version (4.56.2 in PY, M). Exit 0 means
  all accepted. Exit 1 means written with refusals (lists and bank modes). Exit 2 means refused.
- **No text.** `TextGuard` (:123) collects every prompt and response read. Before anything is written or printed, the
  record bytes and every printed line are scanned (the frozen `s1common._text_hits`); a hit refuses. Every exception
  is caught in `main`. A message the script wrote is printed only if it holds no text read. Any other exception prints
  only its class name and file:line (no traceback). The tests plant a sentinel in every prompt and response and
  assert it is absent from stdout, stderr and the record. This covers a codec that raises with the text in its message
  and a forced leaky record or printout.

### Item 2: `tau_l_78b.py` (DES K2; GXB O9: losses only)

- **Formula: confirmed, no correction.** Part 2 §4.7 (R: P2:593) says τ_L = 2√2 × s, with s the sample SD (ddof 1)
  over the family's a0 seeds of each a0 unit's mean per-example query loss on the 200 task rows at e1. PR4 §6.7 says
  the same (R: PR4:589; the table at :593 and :595). REQ-19's code (R: `scripts/stage1/limits/limits_check.py:39-41`,
  :388-393, :325-330) adds: the mean is `math.fsum`/200 and must equal the recorded mean exactly, and s is
  `statistics.stdev`. PLAN-AB's line agrees.
- **Units.** Exactly seeds 1101, 1102, 1103 (`parse_units`, :117). The literal COMPLETE.json pins are OLMo
  1101-1103 and Llama 1101-1102 (`UNIT_PINS`, :61; R: RK:211-216, :232-235; `test_pins_equal_rk`). Llama's N a0-1103
  has no pin yet: its pin comes from the command line, and the record marks `pin_source`.
- **Reads** (`read_unit`, :142). Only COMPLETE.json (its bytes must hash to the pin) and `eval/e1/query_loss.jsonl`
  at the SHA-256 that COMPLETE.json lists. The checks are: `complete`, `target_checkpoint` e1, `trajectory.arm` a0
  and `trajectory.seed`, `identity.training_identity` and `identity.manifest_sha256` equal to the family's (R:
  RK:205, :226, :110-111), `evaluation.checkpoint` e1 with `query_loss.n` 200, a finite recorded mean, and a query
  bank hash. Of each loss line, only `query_id` and `loss` are kept. The 200 ids must be distinct, every loss finite,
  and the recomputed mean equal to the recorded one. Across units, the query bank and the id set must be the same.
  error.txt is checked by name and not opened. A test spies on `Path.read_bytes` and `open` and proves that only these
  two files per unit are opened, while decoy summary, guard and answer files that hold a sentinel are present.
- **Output** (`tau_l`, :202). s, n, ddof, rows, checkpoint, τ_L, and per unit the COMPLETE.json and query_loss.jsonl
  SHA-256s with the pin source, plus the query bank hash. No per-unit loss is printed or written (tested). `--out` is
  optional: it is created once and never inside a unit. Exit 0 means computed; exit 2 means refused.

### Item 3: constraints for item 15's later reducer (not built; R1 does not include it)

1. The new s-pool record must have `kind` "stage1 s-pool record". `s3_score` refuses another kind (R:
   `scripts/stage1/score_s3_datarx.py:79`).
2. Its `s3_pool.sha256` must be the reduced pool's SHA-256. REQ-3's summary must list pool `s3_safe` with that hash
   (R: :84-88). REQ-9's s3 `list_sha256` must equal it too (R: :89-90, RB-1). So the untuned pass must take the
   reduced pool.
3. Its `lists.s3_subset.ids` and `lists.s1.ids` must drop the same ids. `s3_score` refuses any subset or S1 id that has
   no `s3_safe` features (R: :101-105; DESO3 item 33 (b); AM1 change 10).
4. `SCORERS-78B.md:59` and Part 2 §1.17 (R: P2:397; also :182, :203) name the old record `bcca59ac…`. A reduced record
   needs a recorded lead step there and at PINS `shared.sealed_lists_1b.record` (R: AM1 change 10's basis).
5. For the encode count's link: my lists-mode record already gives the refused ids per list, and `s3_subset`'s
   refused ids separately. The reducer can take those ids, by the count record's SHA-256, as its drop list (I).
   `encode_count_78b.py` pins `bcca59ac…` literally, so a re-count on a reduced list needs new pins in a new file (I).

## 3. Tests (synthetic fixtures only)

- `test_encode_count_78b.py`: 57 test functions, 60 cases (one test has 3 parameter cases). They cover reason counts
  per list and the derived subset; the exact limits (1536 accepted, 1537 refused; 3072 accepted, 3073 refused); exit
  codes; off-pin command lines and off-pin bytes (with the real pins); the record's kind, list hashes and pool hash;
  ids and order against the record; S1 twin equality; size; the frozen reader's kind check; missing, repeated and
  unknown lists; the other family's recipe and recipe G refused; tokenizer repo, revision and end token; `--out` once,
  not beside an input, not in the prepared folder; mode mixing; bad specs; the sentinel tests (an unexpected error, a
  ValueError holding text, a refusal holding text, a forced leaky record or printout); the bank counts, its pins, the
  real oext settings, the file pin, its bytes and the shortfall; the anchor counts (every failure counted, first 64
  only, the generation limit, order, a clean list, the real pin, the schema); the pins against committed sources; the
  committed s-pool record's counts (48, 855, 512, union 861); the real context path (a manifest off its pin refuses
  with "DataError"; `real_codec` is called with the family's pin).
- `test_tau_l_78b.py`: 18 test functions, 42 cases. They cover REQ-19's 1B known answer (s 0.002374850619448416, τ_L
  0.0067170919092681925, rel 1e-9); ddof 1 against independent `statistics.stdev`; the record's exact key set and no
  per-unit loss; only two files opened per unit; 15 COMPLETE.json refusal cases; 7 query_loss.jsonl refusal cases; a
  shared bank and shared rows; error.txt; COMPLETE.json bytes off pin; the literal pins with the real tool; Llama 1103
  from the command line; Llama identity; unit option errors; `--out` rules; no write without `--out`; pins equal to
  RK.
- **Suite counts (M; `sandbox-exec -p "$SB" PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS):
  before: 208 passed, 57 skipped (18.1 s). After: 310 passed, 57 skipped (20.6 s), exit 0.** The difference is
  +102 = 60 + 42. The skips are the existing tests that need MAIN's git-ignored `tmp/` sets (conftest's rule); I did not
  copy them.

## 4. Mutants (M)

- Spec `mutation_spec_c_78b.json`: 62 mutants (36 on `encode_count_78b.py`, 26 on `tau_l_78b.py`). Each one removes
  or weakens one check, limit, pin, guard or exit rule named in §2. Every find text occurs once (checked by the build
  script `R/r1-c-scratch/make_spec.py`).
- Runner `run_mutants_c_78b.py`: new, because no existing runner copies `scripts/scale78b` (`scripts/stage1/mutation/run_mutants.py`
  copies `scripts/stage1`; the 78b runners copy `runkit/stage1-78b`). It has the form of
  `runkit/stage1-78b/tests/run_mutants_78b.py`: a copy plus symlinks, a baseline first, KILLED only on pytest exit 1
  with FAILED lines and no ERROR, anything else INVALID, the copy restored and re-hashed. One addition: before the
  baseline, a probe checks that both modules import from the copy, not the source (`imports_the_copy`: true).
- Shards (under the sandbox; each well under 10 min):
  - BASELINE: exit 0, "102 passed", copy import true (`R/r1-c-scratch/mut-baseline.json`).
  - Shard ec (36 encode mutants): 36 killed, 0 survived, 0 invalid; 10.3 s (`mut-shard-ec.json`).
  - Shard tl (26 τ_L mutants): 26 killed; exit 0 (`mut-shard-tl.json`).
  - These two shards ran on the test file before a two-cite comment fix in `test_tau_l_78b.py`; the code was the same.
  - ALL on the final bytes: **62 killed, 0 survived, 0 invalid**, exit 0, about 20 s (`R/r1-c-scratch/mut-all.json`,
    `mut-all.log`).
  - I deleted the runner's repo copies afterwards; the JSON reports stay.

## 5. Commands for the lead's real runs

Run from MAIN after the six files are merged. Relative `tmp/` paths assume cwd = MAIN.

```sh
cd /Users/spiderishi/Coding/attribution
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python   # transformers 4.56.2
SB='(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'
OUT=<OUT_DIR>        # an existing folder that lies inside no input's folder (at any depth) and not inside tmp/kt-prepared/<P_F>

# C1, per family, before that family's untuned-answers pass (lists located by SHA-256, GXB O13)
sandbox-exec -p "$SB" $PY -I -B scripts/scale78b/encode_count_78b.py --family olmo2-7b \
  --prepared tmp/kt-prepared/prepared-kt-dolly-olmo2 \
  --list s1=<S1_JSON>:389c20ad00261b1a304d3dd9f14a113a0b05bcec63758262af1b1629d48e0480 \
  --list s3_safe=<S3_SAFE_POOL_JSON>:6801652cb506f9626575f6e156e103682308830e4e5ef1cb299dd3fa00021fed \
  --list s4_candidates=<S4_CANDIDATES_JSON>:798613c4e5d32caaf51b255b2413395a1477b377f0b97f85933efdc5b35cf17d \
  --out $OUT/encode-count-olmo2-7b-lists.json
sandbox-exec -p "$SB" $PY -I -B scripts/scale78b/encode_count_78b.py --family llama31-8b \
  --prepared tmp/kt-prepared/prepared-kt-dolly-llama3 \
  --list s1=<S1_JSON>:389c20ad00261b1a304d3dd9f14a113a0b05bcec63758262af1b1629d48e0480 \
  --list s3_safe=<S3_SAFE_POOL_JSON>:6801652cb506f9626575f6e156e103682308830e4e5ef1cb299dd3fa00021fed \
  --list s4_candidates=<S4_CANDIDATES_JSON>:798613c4e5d32caaf51b255b2413395a1477b377f0b97f85933efdc5b35cf17d \
  --out $OUT/encode-count-llama31-8b-lists.json
# (--s-pool-record is optional: by default the committed record at .ai/inputs/stage1-commitments-20261016/s-pool/ at bcca59ac…)

# C2, DES E1 (Llama; the same with --family olmo2-7b and the OLMo prepared set if wanted)
sandbox-exec -p "$SB" $PY -I -B scripts/scale78b/encode_count_78b.py --bank --family llama31-8b \
  --prepared tmp/kt-prepared/prepared-kt-dolly-llama3 \
  --oext-record .ai/inputs/stage1-commitments-20261016/oext-bank/oext_record.json:a810574e958ca0e5773c583b0f1df630ff7acc1bb2fc32e5f0de1c63d8c37fa9 \
  --oext-bank <OEXT_BANK_JSON>:6487ed2b9d5717d20b9bade8b51c2511cd6c83f597dafff983e8c391b1954162 \
  --out $OUT/encode-count-llama31-8b-bank.json
#   M (fix round): the committed record (git-tracked) hashes to a810574e…; its bank.full_file is 6487ed2b… (96,014
#   bytes), 400 items, shortfall null. Only the bank file's path <OEXT_BANK_JSON> is left to locate (GXB O13).
#   Note: --out must not lie inside .ai/inputs/stage1-commitments-20261016/oext-bank/ (an input's folder).

# The anchor list's count, informational only (GXB O6), per family
sandbox-exec -p "$SB" $PY -I -B scripts/scale78b/encode_count_78b.py --anchor --family <F> \
  --prepared tmp/kt-prepared/<P_F> \
  --prompts <ANCHOR_PROMPT_LIST_JSON>:78467c97c40e7e9fd39e8061219517853e7292a25881700da5e9115604117b97 \
  --out $OUT/encode-count-<F>-anchor.json

# C6, OLMo-2-7B τ_L now (unit paths and pins from RK KIT a0_units)
sandbox-exec -p "$SB" $PY -I -B scripts/scale78b/tau_l_78b.py --family olmo2-7b \
  --unit 1101=tmp/family-probe-sp-olmo2-7b-b-a0/retrieved/sp-olmo2-7b-b2-1101/tree/round1/1101-a0-e1-a1:4a6d9ebc6636de57d52ec1b9cc1cd82afb1bdbfbf2a70e3f9884d3e9404d6dfc \
  --unit 1102=tmp/family-probe-sp-olmo2-7b-b-seed1102/retrieved/sp-olmo2-7b-1102/tree/round1/1102-a0-e1-a1:43e8412dc7ef8d3eb017340a788e08041623bce8b3896a750d6cc50e10e282c4 \
  --unit 1103=tmp/family-probe-sp-olmo2-7b-b-seed1103/retrieved/sp-olmo2-7b-1103/tree/round1/1103-a0-e1-a1:4b5bd06dede08dc14f3ab5de201b7618ada94a0515896ed23c04b3af7ca44fa0 \
  --out $OUT/tau-l-olmo2-7b.json
# Llama-3.1-8B τ_L after N's record-done
sandbox-exec -p "$SB" $PY -I -B scripts/scale78b/tau_l_78b.py --family llama31-8b \
  --unit 1101=tmp/family-probe-sp-llama31-8b-b5e5-1101/retrieved/sp-llama31-8b-b5e5-1101/tree/round1/1101-a0-e1-a1:21427715565fb394220a068c8991b8f6819c4773ccf82b0cd7c35fe3788bc22a \
  --unit 1102=tmp/family-probe-sp-llama31-8b-b5e5-seed1102/retrieved/sp-llama31-8b-b5e5-1102/tree/round1/1102-a0-e1-a1:b0c99f7b97e6e76355383644ee50f9cbef33c25e09585a9a0d030712d4aa75d9 \
  --unit 1103=<N_A0_1103_UNIT_FOLDER>:<ITS_COMPLETE_JSON_SHA256> \
  --out $OUT/tau-l-llama31-8b.json

# The suite and the full mutation spec (the spec takes about 20 s; one run is enough)
sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests
sandbox-exec -p "$SB" $PY -B scripts/scale78b/tests/run_mutants_c_78b.py "$PWD" <NEW_SCRATCH_OUTSIDE_ROOT> <OUT.json> ALL
```

Exit codes. Encode count: 0 means all accepted; 1 means the record is written and some item was refused (read the
counts; this is not a crash); 2 means refused, nothing written. τ_L: 0 or 2.

## 6. Commands run (all foreground, under 10 minutes)

1. `sed`, `grep`, `cat` of the binding texts, the frozen scripts and RK (exit 0; one `grep` of a heading pattern exited
   1, no match, harmless).
2. PY `-B -I -c` prints of the configs' and manifests' tokenizer and limit fields, the s-pool record's list hashes and
   counts, the oext settings' bank pins, and the transformers version (exit 0). `.venv`'s Python has no transformers
   (exit 1, expected); the lead's PY has 4.56.2.
3. `sandbox-exec … PY -B -m pytest … scripts/scale78b/tests` before (208 passed, 57 skipped; exit 0).
4. Iterative runs of the two new test files: first 5 failed and 48 passed (test bugs and the anchor record's shape,
   fixed); then 54 passed; then 1 failed and 41 passed (an argv slice in a test, fixed); then 96, then 102 passed
   (exit 0).
5. `sandbox-exec … env HF_HUB_OFFLINE=1 PY -I -B R/r1-c-scratch/real_codec_smoke.py WS`, exit 0. `real_context` works
   on both real prepared sets. Both tokenizers agree with MAIN_F (`48d788eca847`, `0e9e39f249a1`). The limits are
   1536 and 3072. On SYNTHETIC text: a 1600-word prompt gives TooLong, an empty response gives NoTargets, and a
   3100-word pair gives TooLong, on both families.
6. CLI smoke under `-I` with a synthetic `{}` file: the lists, bank and τ_L CLIs each refused at the pin check
   (exit 2 each; nothing written).
7. `make_spec.py` (exit 0: 62 mutants, each find text once). Then the runner: BASELINE (exit 0), shard ec (36 killed),
   shard tl (exit 0, 26 killed), ALL (exit 0, 62 killed).
8. Suite after: 310 passed, 57 skipped, exit 0. Then `shasum`, `wc`, `git status --short`.

## 7. Acceptance criteria

| Criterion (brief) | Result |
|---|---|
| Counts per family: `encode_generation_prompt` on S1, s3_safe, s4_candidates at MAIN_F's prompt limit; `encode_train` on s3_safe and S1 pairs at `max_train_tokens`; s3_subset via ids | PASSED on fixtures (M: tests). The limit field is `model.max_prompt_tokens`, not `generation.…` (see §2) |
| Codec built as `real_codec` from F's prepared manifest's tokenizer | PASSED (M: the real path test plus the smoke on real manifests) |
| `--bank` through oext_eval's pinned reader (a810574e…) | PASSED on fixtures; the real settings' pin is asserted (M) |
| `--anchor`: the :121 and :129 checks, same functions and limits; informational | PASSED on fixtures (M) |
| Every input by path and pinned SHA-256; off-pin refuses | PASSED (M: real pins refuse fixtures in every mode) |
| Output: counts by reason, failing ids only, input SHA-256s, recipe SHA-256, tokenizer revision prefix | PASSED (M) |
| No text in stdout, stderr, record or message; planted-sentinel test | PASSED (M: 8 sentinel checks) |
| τ_L formula checked against P2 §4.7 and REQ-19 | CONFIRMED (R), with a known-answer test against REQ-19's sealed values (M) |
| τ_L: units by COMPLETE.json pin; query_loss.jsonl at the listed hash; no other file read; prints s, n, τ_L and hashes only | PASSED (M: file-open spy, record key set) |
| Item 15 constraints recorded | DONE (§2 item 3) |
| Commands for the lead | DONE (§5) |
| Suite before and after; mutation shards under 10 min | DONE (M: §3, §4) |
| Runs on real lists, banks, units | NOT TESTED by design (the lead runs them) |

## 8. Open points for the lead (none decided here)

1. **The limit field's name.** The brief and PLAN-AB say `generation.max_prompt_tokens`. MAIN_F has only
   `model.max_prompt_tokens` (M). The tool uses the field the frozen callers use. If Part 2's text names the field, it
   should say `model.max_prompt_tokens`.
2. **`real_codec` against the pod's codec: no difference (corrected in the fix round, C8).** `real_codec` passes the
   end token as stop and pad (R: build_s_pool.py:473); the pod's policy codec passes the recipe's `stop_tokens` and
   `pad_token` (R: `experiments/safety_selection/loaders.py:187`). So the arguments differ in the pad id and, on
   Llama, in two extra stop ids (`<|eom_id|>`, `<|end_of_text|>`), not only in the pad id as I first wrote. The
   encode functions read only `prompt_ids`, `encode`, `has_special` and `eos_id` (R: `textproc.py:173-201`), so token
   lengths cannot differ. The verifier measured the resulting special-id sets on both real tokenizers: equal (OLMo 8 =
   8, Llama 256 = 256; every such id is already special) (M there: R/r1-c-verify.md §3). So the Mac count and the
   pod's checks give the same verdicts for these tokenizers. A run-time equality check of the two codecs would cover a
   future tokenizer (optional; not built).
3. **The τ_L identity checks.** The tool refuses unless every unit's `identity.manifest_sha256` and
   `identity.training_identity` equal RK's family values (P78 §2.3 condition 2). I did not open the real units, so
   this is not verified on them. If a side unit differs, the tool refuses and nothing is written.
4. **Llama's N a0-1103.** The tool assumes N's unit has the engine's COMPLETE.json form (`target_checkpoint` e1, the
   evaluation at e1, `eval/e1/query_loss.jsonl` listed). If block 0's runner writes another form (for example the
   evaluation in a separate unit), the tool refuses and needs a change. Its pin comes from the command line, and the
   record says so.
5. **τ_L uses COMPLETE.json's mean, not summary.json's.** REQ-19 checked both (R: limits_check.py:390-393). The brief's
   two-file rule rules out summary.json. COMPLETE.json's `evaluation` is the same summary object (R:
   `runner.py:480-486`, :507; I).
6. **A shortfall bank.** `--bank` refuses a bank of fewer than 400 prompts, even one with a matching LN-24 shortfall
   that `oext_eval` would accept. DES E1 names "the same 400".
7. **Exit 1 means written with refusals** (lists and bank modes). Any wrapper must not treat exit 1 as a crash.
8. **Pins and maps.** The new scripts are not in `SCORERS-78B.md`, `PINS-78B.json` or Part 2 §1.17. Recording them
   (if the lead wants them pinned or frozen-on-commit) is a lead step. I changed no existing file.
9. **The anchor checks run on the pod after the policy loads**, before generation (R: make_anchor_answers.py:112-131).
   "Before its pod work" in the brief means before generation. The tool reproduces the checks, not the job's codec
   (point 2).

## 9. Concerns

- The tests read committed real files (the two MAIN_F configs, `oext_eval.json` and W1-18's settings through
  `load_pinned_settings`, the s-pool record, `pins_78b.json`, RK). If any of these is re-pinned, tests fail by design.
- The text guard follows the frozen rule: texts shorter than 6 characters are not scanned. By construction, the
  record holds only ids, hashes, counts and class names.
- The file-open spy covers `Path.read_bytes` and `builtins.open`. The tool opens files only through these (plus one
  `exists()` stat for error.txt).
- The encode count holds the list texts in memory, by design. It writes and prints none of them.

## 10. Fix round (the verifier's VERIFIED_WITH_MINOR, R/r1-c-verify.md; coordinator's list C1-C3, C5-C8, runner nit)

Clock read 2026-11-08T15:39 UTC. Same rules (r1-common.md): only my six files changed in WS; no git state changed (M:
`git status --short` lists the same 6 untracked files). Pre-fix copies: R/r1-c-scratch/prefix/ (their hashes equal §1's
table, M). Unified diff of all six against them: **R/r1-c-scratch/fix.diff** (531 lines, SHA-256
`0a17bf6a4e5490f3130693ccc6384543a105ceceee46847bdce853d645141131`).

### Files after the fix (M: `shasum -a 256`, `wc -l`)

| File (WS) | SHA-256 | Lines |
|---|---|---|
| `scripts/scale78b/encode_count_78b.py` | `132dcd5bd63268afaa6f50df8284f61b7c9719cb84b4737f60f50bd19adebde3` | 626 |
| `scripts/scale78b/tau_l_78b.py` | `5a3f4eda61347738ab8beae7698ae1a7f1cdb94c5e8cbd5f7893e1ec5a17bee9` | 307 |
| `scripts/scale78b/tests/test_encode_count_78b.py` | `68b11cc717649301d22e5b85721a57346e2c05fb2910ca3acd76667e7a0988c5` | 1001 |
| `scripts/scale78b/tests/test_tau_l_78b.py` | `b4a84c638a0a9beeab1d2d301ce0c7d4461fe6dbdfa3544fd5fc319283e3fcf7` | 434 |
| `scripts/scale78b/tests/mutation_spec_c_78b.json` | `7001085026ca3a52dbb8440e6c29a4a1c5644913be440dbbf79602fe98593ad4` | 574 |
| `scripts/scale78b/tests/run_mutants_c_78b.py` | `04f3f855ec3b2064f4715569087966d8f022b4c68642b5f184ab7fc39590871e` | 169 |

### What changed

- **C1 (no partial record).** Both tools share one `write_once` form (encode :512; τ_L :244). The bytes go to a new
  temporary file `.<out>.<pid>.partial` in --out's folder (`open(…, "xb")`), then flush and fsync, then `os.link` to
  --out (no overwrite). The temporary file is unlinked in a `finally` whenever this process created it. An existing
  --out refuses with "created once"; any other OSError refuses with "--out cannot be written (<class>)". Tests: the
  verifier's ENOSPC probe (write half the bytes, then `OSError(ENOSPC)`) in all three encode modes and in τ_L. Each
  asserts exit 2, no --out and an empty folder. Also `write_once` leaves only the complete record, and refuses a
  second write.
- **C2 (the guard in every mode).** `test_a_record_holding_text_is_not_written` and
  `test_a_printout_holding_text_is_not_written` are parametrized over five cases: lists prompt, lists response, bank
  prompt, anchor prompt, anchor unsafe response. The verifier's three survivors are now in the spec:
  V-bank-guard-add, V-anchor-guard-add, V-guard-no-responses.
- **C3.** `ResponseCrashCodec`'s `encode` raises RuntimeError, holding the text, on one response only. The test asserts
  exit 2, no record, the class name printed and no sentinel. V-train-catch-all is in the spec.
- **C5.** Both mains catch `(Exception, SystemExit)`. A SystemExit is reported by its class (and file:line in encode)
  only, with exit 2. Tests: a codec raising `SystemExit(text)` in all three encode modes, and `read_unit` raising
  `SystemExit(text)` in τ_L. New mutants C-ec-systemexit and C-tl-systemexit revert the catch.
- **C6.** The encode docstring, the `out_ok` docstring, the refusal message, §2 and §5's `OUT=` line now say what the
  code does: --out is refused anywhere inside an input's folder, at any depth, and inside P_F.
- **C7.** §5's bank command now names the committed record
  `.ai/inputs/stage1-commitments-20261016/oext-bank/oext_record.json` and the bank hash
  `6487ed2b9d5717d20b9bade8b51c2511cd6c83f597dafff983e8c391b1954162`. M, my own check: the record hashes to
  `a810574e958ca0e5773c583b0f1df630ff7acc1bb2fc32e5f0de1c63d8c37fa9`, `git ls-files` lists it, and its
  `bank.full_file` is {sha256 6487ed2b…, bytes 96,014}, 400 items, `bank_size` 400, `shortfall` null (printed fields
  only).
- **C8.** Open point 2 is rewritten (§8) with the verifier's measured result.
- **Runner nit.** `run_mutants_c_78b.py` refuses an existing OUT.json before it does anything. M: a run with an existing
  report path exited 1 with "exists; give a new report path", and no scratch folder was created.
- **C9 (optional, done).** A test where the command line names a wrong s-pool record hash and the bytes are good; a
  τ_L test with the same 200 ids in reverse order (passes).
- **Not done: C4** (nit; not reachable with the literal pins, per the verifier). A frozen reader's duplicate-key
  refusal that holds text, raised before the guard has that file's texts, would still be printed. The pinned files
  are canonical JSON, and each reader checks the hash before it parses.

### Counts (M; all under `sandbox-exec -p "$SB"`, foreground)

- New-file tests: 123 passed (was 102). test_encode_count_78b.py has 62 test functions (was 57) and 77 cases. test_tau_l_78b.py
  has 22 functions (was 18) and 46 cases.
- **Suite `PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS: 331 passed, 57 skipped, exit 0**
  (35.7 s; was 310/57; +21).
- **Spec: 71 mutants** (42 encode, 29 τ_L). Removed: C-ec-write-wb (its find text is gone). Added: C-ec-write-direct,
  C-ec-partial-kept, C-ec-systemexit, V-bank-guard-add, V-anchor-guard-add, V-guard-no-responses, V-train-catch-all,
  C-tl-partial-kept, C-tl-write-direct, C-tl-systemexit. Every find text occurs once (`make_spec.py`; the edit is
  `edit_spec.py`; the pre-fix builder is `make_spec_prefix.py`).
- **Shards on the final bytes:**
  - Shard encode (42 ids): baseline "123 passed", imports_the_copy true, **42 killed**, exit 0 (`fix-mut-encode.json`).
  - Shard τ_L (29 ids): baseline "123 passed", imports_the_copy true, **29 killed**, exit 0 (`fix-mut-tau.json`).
  - In total: **71 of 71 killed, 0 survived, 0 invalid.** Each shard took well under a minute. The repo copies were
    deleted afterwards.
- The lead's full command is unchanged (§5). It now needs a new OUT.json path each time.
