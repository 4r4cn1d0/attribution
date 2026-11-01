# D2-ln31 verification 2 (after fix round 1): LN-31's draw for the human label check

- **Written** 2026-11-01, finished about 11:35 UTC (clock checked with `date -u` at 11:09:41, 11:14:41, 11:19:21,
  11:30:54 UTC). Author: an independent adversarial verifier (an Opus worker) for the main-study lead (GI VIII).
  Read-only on the builder's workspace `scratchpad/builds/ws-d2`; my code and scratch only under
  `scratchpad/builds/verify-D2-ln31/v2/` (verifier 1's files in the parent folder were run, not changed).
- **Object.** The untracked package `scripts/stage1_s1/hlc_draw/` in ws-d2 (detached at 55d5f8b; `git status
  --porcelain`: `?? scripts/stage1_s1/hlc_draw/` only; `git diff --stat`: empty; no ignored or `__pycache__` file).
  SHA-256 of every file equals the build report's table 12.7 (M): `__init__.py 1ac0cb73…`, `__main__.py ee7d4747…`,
  `draw.py 61ef55ca…`, `inputs.py 0fbacd72…`, `settings/hlc_draw.json 1d3eabe3…` (= `draw.SETTINGS_SHA256`),
  `tests/conftest.py c4f625f5…`, `tests/hlc_world.py b5ccd562…`, `tests/test_hlc_draw.py 8d4875b2…`, spec `9a33f441…`,
  runner `5e608153…`.
- **Verdict: VERIFIED.** I found no defect that matters for the stage-1 reading, the frozen rules or blinding. Verifier
  1's defect D1 (HLC 4.2's HarmBench minimum broken inside a cell) is fixed: an independent re-implementation with a
  different selection algorithm reproduces the tool's draw item for item on 49 synthetic draws, and an exhaustive search
  confirms the split and the walk on 6,000 random small cells. Section 3 lists minor points for the lead; the first
  three are readings of HLC 4.2 with consequences the build report does not quantify.

Labels: **M** measured here by a command, **R** read in a source, **I** inference. **HLC** =
`research/review/2026-10-17-stage2-design-notes/second-rater-and-human-label-check.md` (revision 2; `shasum -a 256` =
`29b781eb44918201…` = REV4's pin at REV4:53; M). **REV4** = the frozen pre-registration. **W1R** =
`research/experiments/2026-10-16-stage1-commitments.md`. **PKG** = `scripts/stage1_s1/hlc_draw/`. **V2** =
`scratchpad/builds/verify-D2-ln31/v2/`. Sources were read in the main checkout (HEAD a494ff7); `git diff --stat 55d5f8b
HEAD` is empty for HLC, REV4's folder, W1R, the addendum, the engine, `seal.py` and every module the draw imports (M),
so they equal the worktree's base.

## 1. What I checked, and the results

| Check | How | Result |
|---|---|---|
| Test suite | `PYTHONDONTWRITEBYTECODE=1 …/venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp=builds/tmp/v2-d2-run1 scripts/stage1_s1/hlc_draw/tests scripts/stage1_s1/tests/test_s1_layout.py` (in ws-d2) | exit 0, **126 passed in 15.69 s** (123 + 3); basetemp 801 MB, deleted (M) |
| The draw against the protocol, end to end | `V2/ref2.py`: my own implementation, written from HLC 4.1-4.4 and 8, the settings' rule texts and the build report's readings 1-13. It reads each synthetic world's raw files (plan.json, the rules module's pins, each unit's eval files, block A's HarmBench cache, the bank, the auditor, the 9 Oct key) and imports no module of the tool. Its selection rule is a different algorithm: a tentative take is kept only if a maximum bipartite matching (Kuhn's augmenting paths) of the unmet target slots to the later answers' unused prompts covers every slot. It compares every key item (id, block, arm, seed, unit, COMPLETE.json SHA-256, prompt, sample, cell, sub-cell, Qwen3Guard safety/categories/refusal, HarmBench, tokens, capped, rank, repeat flag) in order, every cell and sub-cell record of the weights file, the per-unit exclusions, the minors prompts and the repeats. `V2/batch.py` makes each world (`V2/mkworld.py`), draws with the tool's real command line in its own process, then runs ref2 in another | **49 of 49 draws identical** (M; 55 runs, 6 refused as below): worlds plain (seeds 0, 1, 8), `lowu` (seeds 2, 3, 10, 13, 16, 17) (a0 at 1101-1103 and S3 at 1102-1104 at Unsafe shares 0.01-0.04 with most hot prompts holding a "yes" and a "no" Unsafe answer; theta0 at 0.03), `zerou` (seeds 4, 11, 14: H1 1103 with no Unsafe answer, L1 1102 with one, S1 1104 with one "Refusal: No" answer, theta0 at 0.005), `bothlabels` (seeds 5, 7, 12, 15: every Unsafe answer of A1 1102-1104 on a prompt that holds a "yes" and a "no" one); step 0 only (seed 0), steps 0 and 3 (seeds 1-7), steps 0-3 (seeds 8-17). Worlds 6 and 9 (`lowu`) were refused by the tool, as specified: the synthetic key generator found only 11 population answers for the 9 Oct key ("the 9 Oct key holds 11 answers … the settings 15 (HLC 4.1 (a))"); my harness counts those as failures, hence its exit 1 |
| Split and walk, exhaustively | `V2/brute.py 2000 SEED`, seeds 1, 2, 3: random cells of 1-7 prompts, 0-3 Unsafe answers each, random "yes"/"no", random used prompts, n 0-9; it enumerates every selection with one answer per unused prompt | **0 failures in 6,000 cells** (M; 2,768 with a drawable minimum): the drawable (y, m) set equals {y <= P_yes, m <= P_no, y + m <= P} in every cell; `hb_split` returns a drawable pair summing to min(n, P), keeps min(2, P) of each whenever a drawable pair with that sum does, and is the drawable pair closest to floor(total x A_yes / A + 1/2); `walk` meets its targets exactly with the lexicographically first selection |
| Verifier 1's reproducers on the fixed code | `verify-D2-ln31/repro_hb_minimum.py`; `sim_hb_minimum.py low-u` | "no violating configuration among the first 60 prompts" (exit 1, its design for "none found"); 0/400 breaks in all six low-U settings (exit 0) (M) |
| Determinism | world `lowu` seed 21; three draws: PYTHONHASHSEED 1 and 98765 into two folders, and PYTHONHASHSEED 0 on a copy of the world at another path; then `check` with PYTHONHASHSEED 4242 | key `681a87c5…`, weights `7d7aa05a…`, manifest `48de7661…` byte-identical in all three (`shasum`); stdout identical up to paths; `check`: three "match", exit 0. Changing one byte of the weights file: key match, weights mismatch, manifest match, exit 1; `check --reduction 2`: three mismatches (M) |
| LN-31's order, below every Python reader | `V2/spy.py` runs the command line under a `sys.addaudithook` hook that records every `open`, `os.listdir` and `os.scandir` event (it sits below `open`, `io.open`, `Path.read_bytes` and `os.open`) | normal draw: `.gitignore > rules.py > plan.json > seal A > seal B > 9 Oct key > bank manifest > dev bank > auditor > unit files > judges/A`; with plan.json's block-B seal entry removed: only `.gitignore`, `rules.py`, `plan.json` and `seals/block-A.json` (plus library code) are opened, then exit 2 (M) |
| Refusals on a synthetic kit | `V2/refuse.py`: 23 input cases and 6 output cases, each on a fresh copy of one world, each in its own process under the spy; checks exit 2, empty stdout, one `REFUSED:` line, no planted sentinel (`ZZSENT`), no world text, no "Violent", "Sexual" or `Unsafe"` in either stream, nothing written | **all 29 OK** (M; the first run flagged library and `stage1_rules.py` opens as inputs, a fault of my classifier; fixed, rerun exit 0). Cases: block B unsealed; block-B seal at another hash; block B's entry naming block A's seal; block A unsealed; plan B; a kit guard file at another hash; a guard record with a sentinel safety label, with sentinel categories, with a numeric reason (each re-hashed and re-sealed so the parse is reached); a repeated key (`"safety"` twice; message names the key only); a line that is not JSON; an over-refusal prompt id that is a list ("an unexpected TypeError", type only); NaN in summary.json; a HarmBench cache record with a sentinel label (cache, run record, judge record and seal re-made: "line 2: a malformed cache record"); a missing guard.jsonl; a pinned COMPLETE.json changed; the 9 Oct key at another hash; a key item the unit lacks; a key unit at another COMPLETE.json hash; a repeated dev-bank id; an auditor with no SimpleSafetyTests Child Abuse prompt; `--repo` a worktree (`.git` a file); a `.gitignore` without tmp/; sealed folder exists; manifest exists; sealed folder outside the checkout's tmp/; sealed folder in the checkout outside tmp/; manifest inside the sealed folder; manifest folder missing (the six output cases open no input) |
| Totals only (blinding, by difference) | `V2/blind_diff.py`: two worlds identical except S1 1103's Qwen3Guard safety labels (Unsafe share 0.004 against 0.60; same invalid answers, HarmBench labels and over-refusal answers; every other unit's random stream unchanged); each drawn in its own process; every 64- and 16-hex value and every path masked | the sealed key draws 5 against 8 Unsafe items for S1 1103, and the **masked committed manifest and the masked stdout are identical** (M). The manifest's only numbers are the pooled totals, version, step, freeze date and the HarmBench cache's record and non-JSON line counts; every unit lists the same six files (M) |
| Every message (code read) | every `Refusal` text in PKG and in the `reading_input`, `reading/settings.py` code it calls | names, paths, fixed text, hash prefixes, line numbers and counts of keys, records or bank prompts only; no answer, prompt, label or per-unit outcome. Any other exception prints its type only (R; the TypeError case above, M) |
| A failed write | manifest folder read-only (`chmod 555`), so the third exclusive create fails | exit 2, "an unexpected PermissionError"; the key, the weights file and the sealed folder are removed (M; see section 3, note 8) |
| Mutation (reports read, not re-run) | the five `reports/D2-ln31-fix1-mutation-shard*.json` | 65 spec ids, last outcome "killed" for all 65; spec `9a33f441…` and runner `5e608153…` equal the files; every baseline 123 tests, exit 0; the production files in every baseline tree equal the final ones; shards 1-4 ran with `tests/test_hlc_draw.py` `ab67b9c1…`, shard 5 with the final `8d4875b2…`, as the report says (M) |
| Settings against HLC and REV4 (R, M) | the settings file and the sources | population, draw order (a0, R, H1, A1, L1, S1, S3, S4, theta0; seeds ascending; cells Unsafe, Controversial, Safe, Yes, No), seeds (a0, R 1101-1103 from `REJUDGED_PINS['A']`; method arms 1102-1104 = `METHOD_SEEDS['A']`; theta0's `init` pin), sizes (per seed 8/8/8, 2/1/1, 4/4/4, 2/2/1, 2/2/1 = 24/4/12/5/5; theta0 the same column), the reduction steps (repeats 20 to 10; Safe 12 to 8; Unsafe 24 to 18, 6 per seed; cumulative), the seed tags (`derive_seed(20261022, "hlc-v1", "<arm>/<seed>/<block>/<cell>")`, `"hlc-v1-repeats"`, `"hlc-v1-order"`), the exclusions (HLC 4.1 (a)-(c), 8), the external pins (the 9 Oct key `52b6f95a…` = PREREG-2026-10-08.md:14 at 57d08dd; manifest `bd1e40df…` and dev bank `637fa87f…` = the kt data config's `banks_from`; the 9 Oct key's `unit_dir` form = `make_sheet.py`'s `unit_dir.relative_to(main)` at 57d08dd, equal to the pins' paths; its 15 population items = the 12 Unsafe and 3 Safe groups of its `GROUPS`) |
| Deadline (task) | build report section 1 against the sources | REV4:762 (LW-30), HLC:164, HLC:168 (HD8), W1R:243 rule 7 ("The full protocol, its draw script, seed tags and input hashes are committed before block A's first pod launches.") and REV4:763 quoted correctly; the pod times match FOCUS at 55d5f8b (lines 118, 124-126) (R) |
| No real run | `test -e` only | the main checkout has no `tmp/hlc`; ws-d2 has no `tmp/` (M) |

## 2. Defects that matter

None.

## 3. Minor points and notes (they do not change the verdict)

1. **The HarmBench minimum is often lost across seeds in low-U arms (a reading the lead should confirm with its size).**
   HLC 4.2 asks for "at least 2 of each where they exist" inside each seed's Unsafe cell; the tool counts the minimum
   on the prompts not yet used inside the arm (build reading 4; settings `harmbench_split.rule`). Seeds are drawn in
   ascending order, so the arm's earlier seeds can take the prompts that hold a later seed's scarce label (no prompt
   twice inside one arm). Reproduction: `V2/sim_cross.py 100 1` and `100 2` (the tool's own `allocate`, real settings;
   arms of 3 seeds x 200 prompts x 3 samples; prompt propensity Beta(0.2, 0.2(1-U)/U) shared by the seeds; each Unsafe
   answer "yes" with probability q). Seed cells with at least 2 eligible prompts of a label but fewer than 2 drawn:
   U 0.03, q 0.2: 40/300 and 33/300; U 0.03, q 0.5: 8/300 and 9/300; U 0.05, q 0.2: 21/300 and 18/300; U 0.05,
   q 0.5: 0/300 and 1/300; U 0.10 and 0.30: 0 (M). In 129 of the 130 cases the label had fewer than 2 prompts left
   when the cell started; in the other (S3 1104, U 0.03, q 0.5) the whole cell had only 2 prompts left, so both
   minimums could not fit (M: the script prints such cases). I: this follows from HLC's own fixed order and
   no-prompt-twice rule (any cure needs a look-ahead that HLC does not specify); the weights file records it; the
   arm's earlier seeds hold those prompts' "yes" answers, so the HarmBench-versus-human estimates lose precision, not
   validity. Expected only if a repair leaves a seed's U near theta0's. The build report's 12.1 discusses the
   within-cell risk only; the lead should confirm reading 4 knowing this.
2. **The weights file is less fine than HLC 4.2's sentence.** HLC:157: "The weights are per sub-cell (seed x
   Qwen3Guard label x HarmBench label)." The tool splits by HarmBench label only in the Unsafe cell; Controversial and
   Safe each have one sub-cell. Reproduction (world seed 3, step 0, M): the weights file's sub-cells are
   `Unsafe/yes`, `Unsafe/no`, `Controversial`, `Safe`, `Yes`, `No`, while 4 of the 148 drawn Controversial and Safe
   items carry HarmBench "yes". Inverse-fraction weights from the cell's fraction stay valid (the cell is drawn without
   regard to HarmBench), and the missing counts can be recomputed from the hashed inputs, so nothing is lost for
   good; but a post-stratified HarmBench estimate cannot be formed from the sealed weights file alone. Cheap fix if
   the lead wants the sentence met literally: record eligible, available and drawn per HarmBench label for every
   harm cell (code and tests only; the draw's selection does not change).
3. **When both minimums cannot fit, the split is purely proportional** (build reading 4, stated). Example: total 3,
   P_yes 2, P_no 5, A_yes 2, A_no 20 gives y = floor(3 x 2/22 + 1/2) = 0, so no "yes" answer is drawn although
   (1, 2) is drawable (I, from `hb_split`; the 6,000-cell check confirms the stated rule). Arises only in cells with
   fewer than 4 available prompts. A "keep as many as fit" variant is a lead's choice.
4. **HLC 4.3 item 4's independent recomputation is not built** (disclosed by the builder: settings `not_built`,
   `__main__` doc). `check` re-runs the same code. `V2/ref2.py` shows that an independently written computation agrees
   on synthetic data, but it reads the synthetic layout without the kit's seal and pin checks and prints
   differences, so it is not a production checker. The lead rules (another author, or a recorded deviation).
5. **The benign label is the unit's stored full-answer flag, not stage-1 O's** (builder reading 11 and 12.2 point 3;
   verifier 1 note 3). Still open for the lead; unchanged by this round.
6. **Run-time risks that refuse safely.** (a) The OLMo kt data config re-tokenizes the dev bank
   (`study-kt-data-dolly-olmo2.json` `banks_from.retokenize: ["banks/dev.jsonl"]`; `prepare_task.py` rule 6; R), so
   the kt-olmo2 prepared set's `dev.jsonl` is most likely not the pinned `637fa87f…`; the build report's "the same
   bytes as the kt set's copy" (open point 4) is doubtful (I; I did not open `tmp/`). The draw needs the prepared-v3
   folder's own `dev.jsonl`, manifest and auditor; a wrong file refuses. (b) The 9 Oct key must be copied out of
   `peaceful-jepsen-8b8eee`, and its `complete_json_sha256` values (9 Oct) must equal the 27 Oct pins; the
   side-blind-read records at 57d08dd do not hold those values (M: `git grep`), so this is first tested at run time
   (refusal on mismatch).
7. **The block seals are verified against plan.json, not pinned.** The first printed line carries plan.json's and both
   seals' SHA-256; the lead (or the runbook's step 0) should compare them with the seals FOCUS records (block A
   `6c6267c8…`, block B `b4e11dc9…`; R: `grep` of FOCUS), as for every reader that uses `sources.Kit`.
8. **A failed write leaves empty parent folders** made by `mkdir(parents=True)` (e.g. `tmp/hlc/x/` after the
   read-only-manifest case; M). Harmless; the draw's own folder and files are removed.
9. **A repeated JSON key is named in the refusal** (`reading/settings.py` `_no_duplicates`, B16 code: "a JSON object
   repeats the key 'safety'"; M). In these files keys are field names or ids, never answer text or labels, so no
   value can leave this way.
10. **The printed totals reflect pooled block-A properties** (unscored and unlabelled answers, the rule-b count, and a
    benign total below 90 when an arm refuses nearly every benign prompt: the `zerou` world printed 449 items; M).
    They are totals, as LN-31 and HLC 4.3 item 2 allow, and step 5 runs after the reading, so they show nothing new.
11. **Not fixed in the settings:** the add-on draw (HD6) is missing from `not_built` (it is only in the report), and
    the practice items' draw has no seed tag (not built; their units are outside stage 1).
12. **Process:** 62 of the 65 final kills ran with the test file one edit before the final bytes (disclosed; shard 5
    re-ran the 3 entries that use the changed test on the final tree). The lead's full re-run is optional.

## 4. The task's acceptance points

| Point (task text) | Status |
|---|---|
| Reads block-A guard files only after block B is complete | passed (M: audit-hook spy; R: `seal.py` records a seal only for a complete block) |
| Prints totals only; never an answer, a label or a per-unit value | passed (M: 29 refusal cases with sentinels; blinding by difference; R: every message) |
| Writes the sample definition into a sealed or readable file as the protocol says | passed: key and weights sealed under the main checkout's git-ignored tmp/ (HLC 9), text-free manifest readable; sheets not built (disclosed); note 2 on the weights' granularity |
| New tool with tests on a synthetic kit | passed (126 tests, M) |
| HLC's seed tags fixed in the settings | passed (R, M) |
| Deadline (LW-30, HLC:168) listed for the deviation record | passed (R) |
| Draw against HLC's text (strata, sizes, seeds, what is drawn, what is printed) | passed (M: 49 identical independent re-computations; 6,000 exhaustive cells); readings 1-13 for the lead, notes 1-3 |
| Determinism | passed (M) |
| Refusals on a synthetic kit | passed (M) |
| Run on real data | not done, by rule (neither by the builder, as far as `test -e` shows, nor by me) |

## 5. Commands I ran (all exit 0 unless stated)

`date -u` (4 times); `ls`, `find`, `wc`, `du`, `shasum -a 256` on ws-d2's PKG, the reports folder and V2;
`git -C ws-d2 status --porcelain` (also `--ignored`), `diff --stat`, `log --oneline -3`; in the main checkout:
`git log`, `git status --porcelain`, `git diff --stat 55d5f8b HEAD -- <sources and imported modules>` (empty),
`git show 57d08dd:research/side-blind-read/make_sheet.py` (code), `git show 57d08dd:…/PREREG-2026-10-08.md | grep`
(the key's hash lines only), `git grep` of four pin prefixes at 57d08dd (none found), `git show 55d5f8b:research/FOCUS.md
| grep` (three pod-time lines), `git check-ignore -v tmp/hlc/x`, `head -3 .gitignore`, `test -e tmp/hlc` (absent);
`sed`/`grep`/Read on HLC (all), REV4 (:1-10, :45-60, :745-775), W1R:243, the addendum (no HLC, LN-31 or LN-34 entry),
FOCUS:76, `docs/study-plan-full.md:369`, the plan, the runbook draft and the critic (greps), the build report, verifier
1's report, PKG (all), `reading_input/{sources,hb,items,build}.py` (relevant parts), `reading/settings.py`,
`stage1_rules.py` (pins, seeds, `block_runs`), `seal.py` (doc), the engine's `runner.py`, `scoring.py`, `textproc.py`,
`prepare.py`, `prepare_task.py`, `common.py` (code), the kt and v3 data configs (fields only); the venv Python on the
settings and data configs (fields only) and the mutation reports (ids, outcomes, hashes). Pytest (section 1). V2
scripts: `batch.py` three runs (exit 0, then 1 and 1 from the two synthetic-key refusals); `brute.py` x3; verifier 1's
`repro_hb_minimum.py` (exit 1 by design) and `sim_hb_minimum.py low-u`; the determinism and `check` commands;
`refuse.py` (exit 1 from my classifier, fixed, rerun exit 0); `blind_diff.py` x2; the read-only-manifest run (exit 2 by
design); the weights-granularity one-off; `sim_cross.py 100 1` and `100 2`, then `100 1` again after adding the
print of unexplained cases; `grep` of FOCUS for the two seal hashes. Every Python run used
`PYTHONDONTWRITEBYTECODE=1` and `-B`; no `__pycache__` appeared in ws-d2 or V2 (M: `find`); every synthetic world was
deleted after its run (V2/work is empty).

## 6. Evidence (SHA-256 of my scripts in V2)

`v2lib.py e069fc8f…`, `cli.py b08c933d…`, `mkworld.py b427acfa…`, `ref2.py a50e27fc…`, `batch.py 3a0c3cbc…`,
`brute.py 89026fc3…`, `spy.py 2d6c55d8…`, `refuse.py 601e82e8…`, `blind_diff.py bf0088d9…`, `sim_cross.py b7282d85…`
(its last version prints the cases that earlier seeds do not explain; the counts were rerun with it for seed 1).
Each re-creates its synthetic worlds in seconds.

## 7. What I did not open (hard rule 1)

Nothing under `tmp/stage1-olmo/`, `tmp/judge-pod*`, `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`, the
block-a or block-b record folders, any real `units/` or `eval/` folder, any COMPLETE.json, answer, label, guard-sample
or judge-cache file, the 9 Oct key, the auditor file, the prepared sets, the hidden or selector bank, no W1 "sealed
record", and no path with "plant" or "decoy". From the main checkout's `tmp/` I ran only the prescribed interpreter and
one `test -e tmp/hlc`. The real units' paths and hashes appear only as code text in `stage1_rules.py`. Every data file I
read or wrote was synthetic, under V2 or the pytest basetemp.
