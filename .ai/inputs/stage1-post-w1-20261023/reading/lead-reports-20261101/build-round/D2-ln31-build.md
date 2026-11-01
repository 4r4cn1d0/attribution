# D2-ln31 build report: LN-31's draw for the human label check

- **Written** 2026-11-01, finished about 08:55 UTC (clock checked with `date -u` at 05:35:43 and 08:52:30 UTC).
  Author: the D2 builder (an Opus worker) for the main-study lead (GI VIII), build round wf_795563f3-35a.
- **Where**: only the worktree `scratchpad/builds/ws-d2` (detached at 55d5f8b). One new folder,
  `scripts/stage1_s1/hlc_draw/`. No other file changed (`git status --short`: `?? scripts/stage1_s1/hlc_draw/`).
  Nothing committed. No real data read. No network, install, pod or API call.
- **Status**: built and tested on a synthetic kit. 87 tests pass on the final tree. 45 mutation entries, all 45 killed
  (on the tree before a last cosmetic edit; section 7). Not run on real data. The lead must record the late build as a
  deviation (section 1) and confirm the readings in section 4 before the second stamp.

Short names: **HLC** = `research/review/2026-10-17-stage2-design-notes/second-rater-and-human-label-check.md`
(revision 2, SHA-256 `29b781eb44918201…`, equal to REV4's pin at REV4:53; M: `shasum`); **REV4** = the frozen
pre-registration; **W1R** = `research/experiments/2026-10-16-stage1-commitments.md`; **FOCUS** = `research/FOCUS.md`
(line numbers at the main checkout's HEAD 38e160d; at 55d5f8b each is one lower); **PKG** =
`scripts/stage1_s1/hlc_draw/`. Labels: **M** measured here, **R** read in a source, **I** inference.

## 1. The protocol's deadline (for the deviation record)

| Source | Deadline text (R) |
|---|---|
| REV4:762 (LW-30) | "A one-paragraph commitment in REQ-21 before wave 1, with the full protocol before block A" |
| HLC:164 (section 4.3 item 1) | the protocol (frozen), the draw script and its SHA-256, the seed tags, the section 8 term list and the input files by SHA-256 are committed "Before the draw script reads any stage-1 guard file" |
| HLC:168 (section 4.3 item 5, HD8) | "Freeze deadline (decision HD8): before the first stage-1 block-A pod launches, so the draw cannot depend on any stage-1 outcome" |
| W1R:243 (item (f) rule 7) | "The full protocol, its draw script, seed tags and input hashes are committed before block A's first pod launches" |
| REV4:763 (LN-31) | "The draw reads block-A guard files only after block B is complete, by a script that prints totals only" (this rule is kept; section 3.1) |

When the deadline passed (R): the first stage-1 pod, S1-0 (`s10-1`, W1-18 alone), was created 2026-10-25T11:04:34 UTC
(FOCUS:126-127, the entries "W1-18 PASSED" and "STAGE 1 STARTED"); block A's diagnostics pod launched by
2026-10-25T11:37 UTC (FOCUS:125); all five block-A arm pods ran by 17:15 UTC (FOCUS:119). This script, its seed tags
and the section 8 term list were written on 2026-11-01: about 7 days after the deadline, after block A's seal
(27 Oct, `6c6267c8…`) and block B's seal (31 Oct, `b4e11dc9…`), and before anyone read any stage-1 outcome
(FOCUS:74). What limits the harm (I): the script, its settings (with the seed tags) and its tests are fixed before
the draw runs; the second stamp can bind them; the draw prints totals only; nothing in it was chosen from an outcome,
because no outcome has been read. The draw itself still runs only after block B's seal, as LN-31 requires.

Inputs "by SHA-256" (HLC:164): the block-A units' files are bound by block A's seal (its SHA-256 is in FOCUS and the
31 Oct time stamp); the reused a0, R and theta0 units by `stage1_rules.REJUDGED_PINS` (COMPLETE.json and job.json
SHA-256; COMPLETE.json lists every file's SHA-256); the 9 Oct key by its pre-registered SHA-256; the bank by the kt
data config's `banks_from`. The draw's manifest repeats all of them (I: this meets HLC:164's input clause; the lead
judges).

## 2. Files (all new, under PKG; SHA-256 of the final bytes, M)

| File | Lines | SHA-256 | What |
|---|---|---|---|
| `__init__.py` | 26 | `d9d252b4…` | package doc: usage lines, LN-31's order, modules, what is not built |
| `__main__.py` | 127 | `8964a3ae…` | the command line: `draw` and `check`; refusals; totals-only printing |
| `inputs.py` | 362 | `33b2d2ed…` | the kit (plan A, both seals first), the 25 units, their answers, block A's HarmBench labels, the dev bank and auditor categories, the 9 Oct key |
| `draw.py` | 357 | `81d2e628…` | the pinned settings, the exclusions, the cells, the sealed walk, the HarmBench split, the fill, the repeats, the three documents |
| `settings/hlc_draw.json` | 428 | `1bef7f26276c3c7382626dee8176149146cbd1a9ebd66971d7faa13e27558c4c` | the rule (canonical JSON; pinned as `draw.SETTINGS_SHA256`): population, sizes and reduction steps, seed tags, exclusions, term list, bank pins |
| `tests/conftest.py` | 13 | `c4f625f5…` | sys.path: the tree, the builder's `synth_kit` folder, this folder |
| `tests/hlc_world.py` | 326 | `4f02f7f4…` | the synthetic world (on `synth_kit`'s seal, judge-file, HarmBench-pod and rules helpers) |
| `tests/test_hlc_draw.py` | 887 | `3345f32f…` | 87 tests (section 6) |
| `mutation/mutants_hlc_draw.json` | 366 | `8296f9b579fed34c…` | 45 mutation entries |
| `mutation/run_mutants.py` | 217 | `5e608153…` | the builder's runner with its tree changed to PKG (same rules and spec format) |

Full hashes: run `shasum -a 256` on PKG; the lead re-takes them before the second stamp anyway.

## 3. Design

### 3.1 Order (LN-31) and what is printed
1. `load_rules` (the kit's rules module, code), then `Kit(plan.json)`: plan code must be A (plan B refuses: HLC 4.1's
   plan-B population is not built). Then block A's and block B's seals (`sources.Kit.seal`: plan.json's entry, the
   seal file at its SHA-256, a version-1 seal of that block). `seal.py block` records a seal only for a complete block
   (R: `runkit/stage1-olmo/seal.py` module doc), so "block B is complete" = block B's seal verifies.
2. The inputs outside the kit, each at its pin: the 9 Oct key, the prepared-v3 bank manifest, the dev bank, the auditor
   file.
3. Only then any unit folder (COMPLETE.json and job.json first, then the evaluation files).
A test spies on every `read_bytes` call and shows that, with block B unsealed, only `rules.py`, `plan.json` and
`block-A.json` are read before the refusal; another shows the full read order.

Printed (stdout, exit 0): one line each for plan.json and both seals; settings, rules and reduction step; the pinned
inputs' hashes; "units read: 25"; the excluded totals (9 Oct answers, minors-rule prompts by rule and their answers,
unscored answers, answers without a label, all pooled over the 25 units); the drawn totals (items by block, hidden
repeats); then `wrote <path> sha256 <h>` for the three files. Never an answer, prompt, label, or a count per arm, seed,
unit or cell. Refusals: `REFUSED: <names, paths, counts, hashes>` on stderr, exit 2, nothing written; any other error
prints its type only (as the builder does).

### 3.2 Population (HLC 4.1; settings `arms`, `seeds`, `theta0`)
a0 and R at 1101-1103 from block A's re-judged pins; H1, A1, L1, S1, S3, S4 at 1102-1104 from block A's table (the one
complete, pulled `arm` job per cell on a done host, keyed by plan.json's COMPLETE.json SHA-256 and checked against
the seal; job.json's kind, arm, seed, checkpoint e1 and dev bank checked); theta0 from its pin (checkpoint `init`).
These are the three lowest seeds of record of B16's plan-A design (a test checks this against `design("plan_a")`
and `stage1_rules`). Harm block: each unit's `eval/<t>/samples.jsonl` and `guard_samples.jsonl` (exactly 3 answers on
each of the dev bank's 200 harm prompts; counts equal to summary.json). Benign block: each unit's own greedy answers to
the dev bank's 100 over-refusal prompts (`generations.jsonl` and `guard.jsonl`, kind overrefusal; counts equal to
summary.json). Only ids, labels, categories, output tokens and stop reasons are kept; no text field.

The units are read with the B16 input builder's own verified readers (`reading_input/sources.Kit`, `pinned_folder`,
`Folder.file`; `build.scan`, `pins_by_cell`, `engine_arm`, `judge_check`; `hb.block_labels`, `hb.shares`,
`hb.judge_file_counts`; `items.records`), so the draw reads the same files, under the same checks, as the reading.

### 3.3 Exclusions (HLC 4.1 (a)-(c), 8), first reason wins
- **oct9**: the 9 Oct key (SHA-256 `52b6f95a…`, R: `research/side-blind-read/PREREG-2026-10-08.md` at 57d08dd, line 14).
  A key unit whose `unit_dir` equals a pin's path must carry the pin's COMPLETE.json SHA-256; every matched item must
  be an answer the unit holds; the matched count must be 15 (HLC 4.1 (a): 12 Unsafe, 3 Safe controls). Only these
  key fields are read; the key's format comes from `make_sheet.py` at 57d08dd (code only).
- **minors**: rule a = SimpleSafetyTests' "Child Abuse" area (auditor source `simplesafetytests`, category compared in
  lower case); rule b = a term or an age pattern in the prompt text AND a sexual source category or any sexual
  Qwen3Guard category of the population's answers to that prompt (sampled harm answers, greedy over-refusal answers).
  Sources and categories come from the prepared-v3 auditor file (`prepare.py` writes `prompts[pid] = {bank, kind,
  source, record, source_id, category}`; the category field per source is in the data config, e.g. `harm_area` for
  SimpleSafetyTests). The file chain: kt data config `banks_from.manifest_sha256` `bd1e40df…` -> the v3 manifest's
  `files` -> `banks/dev.jsonl` (`637fa87f…`) and `auditor/construction.json`.
- **unscored**: guard reason "control string in guard input; not scored" or "guard input over limit; not scored".
- **no_label**: any other invalid guard record (it has no label, so no cell).

### 3.4 Cells, quotas, walk, HarmBench split, fill (HLC 4.2)
- Order: arms a0, R, H1, A1, L1, S1, S3, S4, then theta0; seeds ascending; cells Unsafe, Controversial, Safe, then
  Yes, No.
- Step-0 quotas per seed: Unsafe [8, 8, 8], Controversial [2, 1, 1], Safe [4, 4, 4], Yes [2, 2, 1], No [2, 2, 1]
  (per arm 24/4/12/5/5 = 50); theta0 24/4/12/5/5. Totals 360 harm, 90 benign, 450 (tested).
- Each cell: its eligible answers sorted by (prompt id, sample index; greedy = -1), shuffled by
  `random.Random(derive_seed(20261022, "hlc-v1", "<arm>/<seed>/<block>/<cell>"))` (theta0: `"theta0/<block>/<cell>"`;
  `derive_seed` is the engine's, `experiments.safety_selection.common`). The walk takes an answer when its prompt is not
  yet used inside the arm (theta0 counts as one arm) and its sub-cell quota is not met.
- Unsafe cell: HarmBench sub-cells yes / no ("no" includes "unparsed"). Quotas y + m = min(n, A) from the available
  answers (prompt not yet used inside the arm at the cell's start): y = floor(min(n, A) x A_yes / A + 1/2), moved into
  the range that keeps min(2, A_yes) and min(2, A_no) when both fit. A second pass tops up from the other sub-cell.
  A test checks `hb_split` against a brute-force "closest to proportional" over n 0-12 and 0-15 answers per sub-cell.
- Fill: a cell's shortfall is added to the next cell of the same seed (Unsafe -> Controversial -> Safe; Yes -> No).
- Repeats: `random.Random(derive_seed(20261022, "hlc-v1-repeats", "harm")).sample(sorted harm item ids, n)`, n = 20
  (10 from step 1).

### 3.5 Outputs
- **Key** (`hlc_key.json`, sealed): per item an opaque id (`h`/`b` + 16 hex of SHA-256 of COMPLETE.json SHA-256,
  prompt id, sample index), block, arm, seed, unit, COMPLETE.json SHA-256, prompt id, sample index, cell, sub-cell,
  Qwen3Guard safety, categories and refusal, HarmBench label, output tokens, capped, rank in the cell's sealed order,
  repeat flag; per unit its path and every file read with SHA-256 (the sheet builder binds the text to these ids).
- **Weights** (`hlc_weights.json`, sealed): per cell quota, inflow, drawn, shortfall; per sub-cell eligible, available,
  quota, drawn and fraction = drawn/eligible (exact); exclusions per unit; the minors prompt ids.
- **Manifest** (readable, committed): protocol pin, requirement, deadline text, settings SHA-256, reduction step, tool
  module hashes (this package and `reading_input`), rules SHA-256, Python version, plan.json and both seals, every
  input by SHA-256, the seed tags, the totals, the key's and weights' SHA-256, what is not built. A test proves it holds
  numbers only under totals, version, step, seed tags and the HarmBench source record, and no per-arm or per-cell key.
- `--sealed` must be a new folder outside the repository or under its git-ignored `tmp/`; `--manifest` outside it; no
  file is overwritten (exclusive create). `check` re-makes all three documents in its own process and prints
  `match`/`mismatch` per file and the totals (exit 0 / 1 / 2).

## 4. Readings I made (the lead confirms or changes them before the second stamp)
1. **Per-seed split** of the per-arm sizes that 3 does not divide: remainder to the lowest seeds (Controversial
   [2, 1, 1], Yes and No [2, 2, 1]; step 2's Safe [3, 3, 2]). HLC 4.2 says only "24 (8 per seed)"; its weights rule
   ("per sub-cell (seed x label x HarmBench label)") and draw order ("seeds ascending; cells in the table's order")
   imply per-seed cells.
2. **theta0 "every one, up to 24"** yields to "no prompt twice inside one arm": two Unsafe answers to one prompt give one.
3. **HarmBench "unparsed"** counts in the "no" sub-cell (Gate B: only "yes" is harm).
4. **Split base** = answers available at the cell's start; rounding half up; minimums dropped only when both cannot fit.
5. **Fraction** = drawn / eligible per sub-cell (eligible = after exclusions; "available" also recorded). The no-repeat
   rule makes the true inclusion probability differ slightly; both counts are in the weights file.
6. **Section 8 term list and age patterns** (settings `exclusions.minors`): drafted by me on 1 Nov (90 terms, 4 age
   patterns, marker "sexual"). HLC asks for "a committed list of terms"; its content is the lead's. Over-inclusive by
   design (it acts only together with a sexual category).
7. **Rule b's guard categories** come from the population's sampled harm answers and greedy over-refusal answers only
   (not greedy harm answers, not other kinds; a test plants sexual categories there and shows they are ignored).
8. **Freeze date 20261022** (REV4's date; REV4 pins HLC revision 2 and adopts its draw). Any fixed date works; it is
   fixed now, before the draw.
9. **Repeats are chosen by the draw** (sealed, rater-independent); their second showing (at least 150 positions
   later) and each rater's order are the sheet builder's, by the tags fixed now (`hlc-v1-order`, part
   `<rater>/<block>`, raters R1-R3).
10. **Reduction step** is a command-line choice (0-3, settings `sizes.steps`); theta0 takes the same cuts. Part 1 has
    not run, so the reading uses step 0; a later cut means a re-run into a new sealed folder.
11. **Benign block for a0 and R at 1101-1103** = the pinned units' own dev-100 greedy answers (HLC:164 lists each
    unit's `generations.jsonl` and `guard.jsonl`), not block A's O-only passes.

## 5. Alternatives rejected
- **s1common's label registry** (`seed(key, …)` with base 20261008): `scripts/stage1/labels.json` and `s1common.py`
  are W1 manifest entries (M) and the registry owner must be a `scripts/stage1` file; HLC fixes its own tag form, so
  the tags live in this tool's pinned settings and use the engine's `derive_seed`.
- **Own unit discovery**: rejected for the builder's verified readers, so the draw and the reading read the same
  bytes under the same checks. Cost: a dependency on `reading_input` internals (open point 6).
- **Writing the rater sheets in the draw** (HLC 4.3 item 3 lists them): rejected; consent-time category opt-outs and
  the number of raters are not known yet, and HLC 5.3 budgets a separate two-rubric sheet builder.
- **Pooled (per-arm) draws for Controversial, Safe and benign**: rejected (reading 1).
- **Repeating the draw for each reduction step by trimming a step-0 draw**: rejected; the fill rule makes a trimmed
  draw differ from a fresh draw at that step. A deterministic re-run is simpler and checkable.
- **An independent second implementation for the check**: not built (open point 7).

## 6. Commands run (all in the worktree or scratch; synthetic data only)

| Command | Exit | Result |
|---|---|---|
| `date -u` (05:35:43, 08:46:27, 08:52:30 and in each shard) | 0 | |
| `ls`, `grep`, `sed -n`, `cat`, `wc` on the briefed reports, the plan, REV4, HLC, ADD, FOCUS, W1R, the study plan, code | 0 | |
| `shasum -a 256` of HLC | 0 | equals REV4's pin `29b781eb…` |
| `git log`, `git show`, `git cat-file -t`, `git check-ignore` (read-only; main checkout and worktree) | 0 | |
| `python3 -I` printing data-config bank fields and the W1 manifest's roles for `labels.json` and `s1common.py` | 0 | |
| `test -e` on the two possible 9 Oct key paths (existence only; not opened or hashed) | 0 | present only in `.claude/worktrees/peaceful-jepsen-8b8eee/tmp/side-blind-read/` |
| settings writer, spec writer, rewrap helper (scratch scripts) | 0 | |
| smoke run of `draw` and `check` on one synthetic world (scratch; deleted) | 0 / 0 | 450 items; match |
| pytest runs 1-4 while writing tests | 1 | each failure was a test expectation, fixed in the test (population filter; `rules.py` read first; seed-tag text in the manifest; list keys) |
| pytest, full suite, then after adding gap tests | 0 | 80 passed (27.90 s); 87 passed (23.84 s; 38.64 s) |
| pytest, final tree: `PYTHONDONTWRITEBYTECODE=1 …/venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp=<scratch> scripts/stage1_s1/hlc_draw/tests` | 0 | **87 passed in 20.06 s** (basetemp up to about 0.5 GB; deleted) |
| pytest `scripts/stage1_s1/tests/test_s1_layout.py` | 0 | 3 passed |
| AST check for unused imports and lines over 120 | 0 | one unused import and five long lines, fixed (section 7) |

## 7. Mutation entries (added and run)
`mutation/mutants_hlc_draw.json`: 45 entries, parts order (3), units (3), answers (7), harmbench (1), inputs (8),
settings (1), exclusions (5), walk (9), repeats (2), outputs (3), check (2), streams (1). Each names the check it
removes (e.g. `HLC-seal-before-units`, `HLC-prompt-once-per-arm`, `HLC-split-minimum`, `HLC-oct9-count`,
`HLC-error-type-only`).

Run with `run_mutants.py --timeout 300` in 7 shards (`--only`); reports copied to `reports/D2-ln31-mutation-shard{0,1a,
1b,2,3a,3b,3c}.json`. Every baseline passed with 87 tests; one spec SHA-256 (`8296f9b5…`), one runner SHA-256
(`5e608153…`), one baseline tree in all seven. **45 killed, 0 survived, 0 invalid.** Per-mutant pytest time 4-73 s.

Two things to know:
- The first shard-0 attempt refused (baseline failed: a test read the data config from the runner's copy, which holds
  only `scripts/stage1_s1`); the test now reads it from the engine's workspace (`synth_kit.TREE`); rerun passed.
- **Hard rule 5, letter breached three times**: shards 2, 3b and 3c (11, 4 and 3 mutants) ran past the tool's 600 s
  limit and the harness moved them to the background (ids bi08h53b4, bgsbsilrc, biip6debw). I did not ask for
  background runs. Most of the wall time was outside pytest (machine load average up to about 18; shard 3c's runner
  took 22 minutes for about 70 s of pytest). Each finished with exit 0 before I went on; scratch folders were deleted.

After the runs I made one cosmetic edit: `inputs.py` lost an unused import (`is_hex64`) and one refusal message was
re-wrapped; two test files had lines re-wrapped. No logic changed. All 45 find texts still occur exactly once in the
final files (M) and the final suite passes, but the mutants were not re-run on these final bytes. The lead's full run:
about 25-40 min of pytest in total, longer under load.

## 8. How to run it at the reading (proposed runbook step 5)
```zsh
# Step 5: LN-31's draw (totals only) and the second-process check
date -u; mkdir -p "$RUN/hlc" || fail 5 "no hlc folder"
HLC=(--kit "$KIT" --oct9-key "$OCT9KEY" --bank-manifest "$V3/manifest.json" --bank "$V3/banks/dev.jsonl"
     --auditor "$V3/auditor/construction.json" --sealed "$ROOT/tmp/hlc/draw-$STAMP" --manifest "$RUN/hlc/hlc_manifest.json")
"$PY" -B -m scripts.stage1_s1.hlc_draw draw "${HLC[@]}" > "$LOGS/5-hlc-draw.txt" 2>&1
c=$?; ledger 5-hlc-draw $c "$ROOT/tmp/hlc/draw-$STAMP/hlc_key.json" "$ROOT/tmp/hlc/draw-$STAMP/hlc_weights.json" "$RUN/hlc/hlc_manifest.json"
(( c == 0 )) || fail 5 "the draw refused (no outcome shown)"
"$PY" -B -m scripts.stage1_s1.hlc_draw check "${HLC[@]}" > "$LOGS/5b-hlc-check.txt" 2>&1
c=$?; ledger 5b-hlc-check $c; (( c == 0 )) || fail 5b "the second process does not reproduce the draw"
```
`OCT9KEY`, `V3` are new variables (open points 3 and 4). `--repo` defaults to the checkout that holds the code (the pins
are relative to it). The manifest's parent folder must exist; the sealed folder must not. The draw needs only block B's
seal, so the lead may also run it before step 1 (before any outcome line is printed); that is the lead's choice.

## 9. Open points for the lead
1. **Deviation record** for the missed deadline (section 1), and HLC's "before the draw reads any guard file" items
   built now: the script, the seed tags, the term list.
2. **Confirm or change the readings of section 4**, especially the term list (6) and the per-seed split (1). Any
   settings change needs a new `SETTINGS_SHA256` in `draw.py`, the suite and the affected mutants.
3. **The 9 Oct key exists only in the worktree `peaceful-jepsen-8b8eee`** (checked with `test -e`; HD14's copy-out not
   done). Copy `key.json` (and `sheet.html`, the ratings CSV) to a git-ignored folder of the main checkout and to the
   backup, with a SHA-256 check (`52b6f95a…`), before any worktree clean-up. Without it the draw refuses.
4. **Find the prepared-v3 folder** (its `manifest.json` hashes to `bd1e40df…`; `banks/dev.jsonl` to `637fa87f…`, the
   same bytes as the kt set's copy; `auditor/construction.json` at the manifest's entry). I did not search `tmp/`.
5. **The auditor file is auditor-only** and also holds selector and hidden entries' sources and categories. HLC 8 asks
   the lead's script to use it; the draw keeps only dev entries and prints nothing from it. Confirm this use.
6. **Merge order**: the draw imports `reading_input` (`sources`, `build`, `hb`, `items`). If tracks A or B change those
   modules, re-run this suite after their merge. The manifest records both packages' module hashes.
7. **"A second, independent process"** (HLC 4.3 item 4): `check` is a second process, not independent code. An
   independently written checker would need another worker.
8. **Not built**: the two-rubric sheet builder (sheets, consent opt-outs, per-rater orders, repeat placement, storage
   keys), the practice items, the pinned scorer (K1, K2), the add-on draw (HD6).
9. **Never run on real units.** The field names come from the engine's code (`runner.py`, `scoring.py`; present since
   2-5 Oct, before Gate A, M: `git log -S`) and from `make_sheet.py`; a refusal on real data prints no value.
10. **Mutants not re-run on the final bytes** (section 7); optional, about 25-40 min of pytest.

## 10. Replies to questions
No question from GPT or the lead reached me during this task.

## 11. What I did not open (hard rule 1)
Nothing under `tmp/` was opened, listed or hashed, except one `test -e` on the 9 Oct key's two possible paths
(existence only). No unit, eval, COMPLETE.json, answer, label, guard-sample or judge-cache file; no hidden or selector
bank; no block-a/block-b record; no W1 "sealed record" (I printed only paths and roles of two W1 manifest entries). From
the 9 Oct pre-registration at 57d08dd I printed only its sheet table (file names and SHA-256), not its results.

## 12. Fix round 1 (answers verifier 1, `reports/D2-ln31-verify1.md`)

- **Written** 2026-11-01, finished about 11:03 UTC (clock checked with `date -u` at 09:43:26, 10:07:21, 10:58:39,
  11:00:27 and 11:01:03 UTC). Author: the D2 builder (an Opus worker), fix round of track D2-ln31. Same place as
  before: only the untracked package `scripts/stage1_s1/hlc_draw/` in `scratchpad/builds/ws-d2` (`git status
  --porcelain`: `?? scripts/stage1_s1/hlc_draw/`; `git diff --stat`: empty). Nothing committed. No real data read. No
  network, install, pod or API call.
- **Status (supersedes the header's status line):** D1 fixed; minor points 1, 2 (doc), 4, 5, 6, 8, 9, 10 fixed;
  point 7 changed to the more protective reading (the lead confirms); points 2 (the independent checker), 3, 11 left
  to the lead with a note; point 12 closed (the full spec re-run on the final production bytes). **123 tests pass**
  (plus the 3 layout tests). **Mutation: 65 entries, 65 killed** (the last run of each entry). Never run on real data.
- Labels as before: **M** measured here, **R** read in a source, **I** inference. **V** = `scratchpad/builds/verify-D2-
  ln31/` (the verifier's scripts, run read-only: I wrote nothing there). **FX** = my scratch
  `scratchpad/builds/d2-scratch/fix1/`.

### 12.1 D1 (HLC 4.2's "at least 2 of each where they exist"): agreed and fixed

**Agreed (M).** Before the fix, on the build's bytes (`draw.py` `81d2e628…`): `V/repro_hb_minimum.py` gave "drawn:
yes 1, no 7 ... VIOLATED" and `V/repro_hb_minimum_cli.py` gave "a0 1101 Unsafe cell drew 8 items, HarmBench yes 1
[('p045', 0)]" (both exit 0). The verifier's diagnosis holds and has two parts: (a) one greedy pass with no look-ahead,
so a prompt holding answers of both HarmBench labels could spend the scarcer label's minimum; (b) the split's bounds
and minimums counted answers, while the "no prompt twice inside one arm" rule lets the walk take one answer per prompt,
so a quota could ask for more than can be drawn (then the old walk missed its own quota and topped up).

**Fix (`draw.py`; settings `harmbench_split.rule` and `draw_rule` rewritten).**
- `hb_split(n, a_yes, a_no, p_yes, p_no, p_all, minimum)`: total = min(n, P), where P counts the distinct available
  prompts of the cell; the proportion is still the answers' (y = floor(total x A_yes / A + 1/2), as HLC 4.2 says
  "keeps the HarmBench yes and no answers in proportion"); y is moved into the range that one answer per prompt can
  draw (y <= P_yes, m <= P_no) and, when both fit, into the range that gives each sub-cell min(2, its P). So a quota is
  always drawable, and "where they exist" means "where they can be drawn".
- `reachable(keys, sub_of, need, used)` (new): Hall's condition for one answer per unused prompt: for every set of
  sub-cells with an unmet target, the sum of the targets is at most the number of unused prompts holding a key of one
  of them (exact for any number of sub-cells; for 2 it is the three inequalities y <= P_yes, m <= P_no, y + m <=
  |P_yes u P_no|).
- `walk(order, sub_of, targets, used)`: one pass over the sealed order; a key is taken when its prompt is unused
  inside the arm, its sub-cell's target is not met, and the targets still unmet stay reachable from the keys after
  it. If the targets are reachable at the start, the walk meets each exactly (I: an exchange argument: if taking a key
  breaks reachability, no complete selection uses it, so skipping keeps reachability), and its selection is the one
  whose positions in the sealed order come first (lexicographically) among all selections that meet the targets. No
  top-up pass. A walk whose targets are unreachable at the start refuses ("the draw's split or cut is wrong"; never
  reached through `allocate`).
- `allocate`: cells without sub-cells get the target min(n, P) (they took exactly that many before too); the weights
  file's sub-cell records now hold `available` (answers), `available_prompts` and `target` (renamed from `quota`,
  always equal to `drawn`), and each cell record holds `available_prompts`. The cell's `quota` (quota plus inflow),
  `drawn` and `shortfall` keep their meaning, so the fill is unchanged.

**Why not the verifier's proposed minimum-first pass (M, a concrete check).** "Take each sub-cell's minimum first,
fewest prompts first" can still lose a minimum: prompts holding "yes" answers {a, b, c}, "no" answers {a, b, d}, order
(a yes), (b yes), (a no), (b no), (c yes), (d no), n = 8, so the split is (2, 2). The minimum-first pass takes a and b
for "yes" and then finds only d for "no": (2, 1). The fixed walk draws (a yes), (b no), (c yes), (d no): (2, 2) (FX
one-off command, output pasted in 12.6). The fixed walk is also smaller in code than a pass-plus-heuristic.

**Draws without such a conflict do not change (M).** `FX/old_vs_new.py` runs the walk and split as built (copied
from `draw.py` `81d2e628…`) and the fixed `allocate` on the same units and exclusions of synthetic worlds seed 0-7, at
steps 0 and 3 (8 x 2 x 125 cells): the drawn keys are identical in every cell except theta0's Unsafe cell in worlds 4
and 5 at step 0. There (`FX/theta0_detail.py`) theta0 holds 24 Unsafe answers on 23 prompts (one prompt holds a "yes"
and a "no" answer): the old split (13, 11) needed 24 prompts, so the old walk drew 13/10 and recorded a quota it did
not meet; the fixed split is (12, 11) (23 x 13/24 = 12.46), met exactly; both draw 23 answers and differ in one
answer of the shared prompt. No cell broke the minimum under either rule in those worlds (the synthetic U rates are
high), which matches the verifier's simulation: the risk lives in low-U cells.

**Evidence that it is fixed (M).**
- `V/repro_hb_minimum.py` on the fixed code: "no violating configuration among the first 60 prompts" (its exit 1 means
  that the search found no violation). The end-to-end case, as `FX/repro_hb_minimum_cli_fixed.py` (the verifier's
  script with two changes: the sealed folder moved under the world's `repo/tmp/` because point 4's fix refuses a
  folder outside it, and Y1, Y2 fixed to the pair the verifier found, p044 and p045, because its search for a
  violating pair now finds none; also the renamed `target` field): draw exit 0, "HarmBench yes 2 [('p045', 0),
  ('p044', 0)] ... yes target 2 available 2 drawn 2; no target 6 drawn 6 ... kept".
- `V/sim_hb_minimum.py` (both runs) on the fixed code: 0 breaks in every setting (before, per the verifier: up to
  26/400 in a theta0-like cell and 16/400 at U 0.03).
- New tests: `test_the_walk_keeps_the_harmbench_minimum_when_a_prompt_holds_both_labels` (the verifier's
  reproduction 1, with the precondition that the old rule's pass draws 1 "yes" on it),
  `test_the_draw_keeps_the_harmbench_minimum_end_to_end` (reproduction 2 through `main`, in a world made with the new
  `hlc_world.make(crafted=...)`), `test_the_split_and_the_walk_are_the_exhaustive_searchs` (300 random small cells;
  the split and the walk's selection equal an exhaustive search over every set of keys with distinct unused prompts,
  which takes no theorem on trust; the old rule's pass misses a target in 28 of the 300 and loses a minimum in 26),
  `test_a_cell_with_fewer_prompts_than_its_quota_passes_the_shortfall_on`, `test_the_walk_refuses_targets_its_answers_
  cannot_meet`, `test_the_walk_takes_the_first_keys_that_keep_every_target_reachable` (replaces the top-up test).
  Changed: `split_by_hand` and `hand_draw` (the rule by hand, with the three inequalities written out, not the
  tool's `reachable`), `test_hb_split_...` (brute force over answer and prompt counts), the split and weights tests
  (target = drawn; the minimum asserted where both fit, on prompts).

### 12.2 The minor points of verifier 1's section 3

| # | Point | What I did |
|---|---|---|
| 1 | Partial write on a refusal | **Fixed.** `_paths` now checks, before any input is read: the sealed folder and the manifest neither exist nor are a link (a dangling link at `--manifest` used to pass `exists()`), the manifest's folder exists, and the location (point 4). Messages name the path. `_write` creates the folder and the three files by exclusive create and, on any failure, removes what it created (never a file it did not create) and re-raises. Tests: missing manifest folder (refused before the first read; a spy on `read_bytes` sees nothing), dangling link (same), a racing process that creates the manifest after the checks (what the draw wrote is removed; the other file is kept), a permission error on the weights file (all removed; type-only message). Mutants HLC-manifest-folder, -no-overwrite-link, -cleanup, -cleanup-own-only: killed. |
| 2 | `check` is not HLC 4.3 item 4's "second, independent process" | **Doc fixed; the checker is not built (agreed limit).** `__main__.py` and `__init__.py` now call `check` a reproducibility check by the same code and no longer cite HLC 4.3 item 4 for it; the settings' `not_built` gains `independent_check`, so the manifest states it. An independent checker should come from another author: the lead rules (another worker writes one, or a recorded deviation). |
| 3 | The benign label is not the stage-1 O label for long answers | **Not changed; a protocol question for the lead (12.4 reading 11).** Checked in code (R): under Branch 128, `items.o_flags` uses the cut record's flag for every dev-100 answer longer than 128 tokens and the stored full-answer flag otherwise; the stored flags come from the route: method arms `unit_eval` (the unit's own `eval/e1/guard.jsonl`, the answers the draw also reads), reused a0/R `source_unit` (the pinned unit's) or `generated` (the O-only pass's own `dev100/` answers), theta0 always `generated` (`build._theta0`). The draw stratifies on, and the raters would see, each pinned or kit unit's own full greedy answer and its stored "Refusal" flag (HLC 4.1 and HLC:164's file list). So the HLC label equals the stage-1 O flag for answers of at most 128 tokens on the same answers, and differs for longer answers (LN-19: up to about 3 of 100 flags per unit) and for theta0 (and a0/R under route `generated`), whose O answers are other generations. Options: (a) keep, and state in the paper that the HLC measures the judge's full-answer refusal flag; (b) stratify on the stage-1 O flag and show the cut answer (needs the O-ext folders as inputs: a new build); (c) (b) for theta0 and route `generated` only. I recommend (a) (HLC's text and file list; the judge-versus-human question is about the label of the answer shown). |
| 4 | Sealed-folder location vs HLC 9 | **Fixed.** `--sealed` must lie under `<repo>/tmp/`, where `<repo>` (`--repo`) is a main checkout (its `.git` is a folder; a worktree's is a file) whose `.gitignore` has a line `tmp/` (or `/tmp/`, `tmp`, `/tmp`). A folder outside the repository is now refused. The real main checkout passes (M: `.git` is a folder; `.gitignore` line 1 is `tmp/`; `git check-ignore -v tmp/hlc/x` names it). The runbook line in section 8 (`--sealed "$ROOT/tmp/hlc/draw-$STAMP"`) already complies. Tests: outside the repository, in the repository outside tmp/, a worktree-like `.git` file, a `.gitignore` without tmp/. |
| 5 | Term list misses forms | **Added (the content stays the lead's).** Terms (16): csam, grandchild, grandchildren, granddaughter, granddaughters, grandson, grandsons, jailbait, newborn, newborns, stepchild, stepchildren, teenaged, under the age of, under-aged, underaged (now 106). Age patterns: "of age" accepted after the number ("15 years of age", "fifteen years of age"), "y.o." accepted ("15 y.o."), and a new pattern for "under 18", "under-16" (1-18, not 19 or more, not inside a word such as "thunder"). 18 new pattern test cases, both directions. |
| 6 | Rule a has no sanity check | **Added.** `read_bank` refuses unless some auditor entry of any bank has source `simplesafetytests` and category "child abuse" (compared as rule a compares); it prints no count. Reading the other banks' entries only for this existence test is as the verifier proposed; the draw already parses the whole pinned auditor file. Tests: names renamed in every bank (refused); renamed only in the dev entry (passes; rule a then excludes nothing). |
| 7 | Rule b reads no greedy harm answer's categories | **Changed to the more protective reading; the lead confirms (12.4 reading 7).** HLC 8 (b) says "any Qwen3Guard category of its answers"; each population unit's greedy harm answers are answers to the prompt. `read_answers` now also reads `guard.jsonl`'s harm records (prompt id, valid flag, categories only), checks one per dev harm prompt and their counts against `summary.json`'s `harm.greedy` (`n` required, `guard_invalid` where written), and rule b uses their categories. Units outside the population are still not read. Cost on the rule: it can only add prompts. The narrow reading is the removal of three lines in `minors_rule`. Tests: a planted sexual category on a greedy answer to p027 ("a kid asks") of A1 1103 makes p027 rule b; one on a0 1104 (outside the population) leaves p017 drawn; four malformed-record cases and two summary cases refuse. |
| 8 | theta0's HarmBench split is an extension | **Listed** (12.4 reading 12). |
| 9 | Manifest tool hashes miss two dependencies | **Fixed.** The manifest's `tool.dependencies` holds the SHA-256 of `scripts.stage1_s1.reading.settings`, `experiments.safety_selection.common` and `experiments.minimal_safety.common` (where `derive_seed` is defined), keyed by module name (no path). Test compares each with the imported file. |
| 10 | Running the draw before the reading | **Agreed; withdrawn.** The offer in section 8's last sentence is withdrawn: run the draw at step 5, after the reading, as the plan orders. |
| 11 | Run-time risks that refuse safely | **Unchanged; still open points 3 and 4** (copy the 9 Oct key out of `peaceful-jepsen-8b8eee` with a SHA-256 check; find the prepared-v3 folder). New run-time requirement from point 4: run from the main checkout, or pass `--repo` = the main checkout. |
| 12 | Mutants not re-run on the final bytes; background shards | **Closed.** The full spec (65 entries) ran on the final production bytes in 5 foreground shards, each under a 560 s process-group cap (`perl` `setpgrp` + `alarm`, so no child could outlive the command); no background job. Details in 12.5. |

### 12.3 Settings (new pin)
`settings/hlc_draw.json` `1d3eabe38e9b5d069623ba17bcef3f2d939d0abf309c5d7f06473847179a8c2d` (`draw.SETTINGS_SHA256`;
canonical JSON; written by `FX/update_settings.py` and `FX/not_built.py`). Changed fields only: `harmbench_split.rule`,
`draw_rule`, `exclusions.minors.rule_b`, `exclusions.minors.terms` (+16), `exclusions.minors.age_patterns` (3 changed,
1 added), `outputs.rule` (location; all-or-nothing write), `not_built.independent_check` (new). Seed tags, freeze
date, population, cells, sizes, steps, pins and exclusion order are unchanged (the tests that pin them pass unchanged).

### 12.4 Readings changed or added (the lead confirms before the second stamp)
- **4 (changed).** Split base: the proportion from the available answers; the total, the bounds and the minimums from
  the distinct available prompts (one answer per prompt can be drawn); rounding half up; the minimums dropped only
  when both cannot fit.
- **7 (changed).** Rule b's guard categories come from every answer of the population to the prompt: sampled harm,
  greedy harm and greedy over-refusal answers.
- **11 (extended).** The benign block of every population unit (method arms, a0 and R at 1101-1103, theta0) is the
  unit's own `eval/<t>/generations.jsonl` greedy over-refusal answers with their stored full-answer "Refusal" flag,
  not the stage-1 O endpoint's cut flags or the O-only passes' answers (point 3).
- **12 (new).** theta0's Unsafe cell also takes the HarmBench split (HLC names "each seed's Unsafe cell"; theta0 has
  no seeds). Alternative: no split for theta0 (it takes every Unsafe answer it can, up to 24, anyway).
- **13 (new).** A cell's target is its quota plus the inflow, cut to the distinct available prompts; any rest flows
  to the next cell (the same counts as before; now stated in the settings).

### 12.5 Mutation (spec `mutation/mutants_hlc_draw.json` `9a33f441…`, runner unchanged `5e608153…`)
Spec changes (`FX/update_spec.py`, which also checks that every find text occurs once): 5 entries re-targeted to the
new code (HLC-split-minimum, -prompt-once-per-arm, -minors-term-boundary, -no-overwrite, -sealed-under-tmp),
HLC-top-up removed (no top-up pass), 21 added: walk (HLC-walk-reachable, -reachable-union, -walk-start-check,
-split-prompt-bounds, -split-total, -split-fallback, -plain-cut, -available-prompts), exclusions
(HLC-minors-greedy-harm), answers (HLC-greedy-harm-prompts, -greedy-harm-repeat, -greedy-harm-parity), inputs
(HLC-rule-a-guard), outputs (HLC-no-overwrite-link, -manifest-folder, -sealed-outside-repo, -main-checkout,
-tmp-ignored, -cleanup, -cleanup-own-only, -manifest-dependencies). 65 entries.

| Report (copied to `reports/`) | Ids | Result | Wall time |
|---|---|---|---|
| `D2-ln31-fix1-mutation-shard1.json` (`5083675c…`) | 17 | 17 killed | 10:29-10:36 UTC |
| `D2-ln31-fix1-mutation-shard2.json` (`3f26cc83…`) | 16 | 16 killed | 10:36-10:42 |
| `D2-ln31-fix1-mutation-shard3.json` (`0b04ea48…`) | 16 | 16 killed | 10:42-10:49 |
| `D2-ln31-fix1-mutation-shard4.json` (`baca3d78…`) | 16 | 15 killed, 1 invalid (HLC-error-type-only) | 10:49-10:55 |
| `D2-ln31-fix1-mutation-shard5.json` (`a785a99f…`) | 3 | 3 killed (HLC-error-type-only, -cleanup, -cleanup-own-only) | 10:55-10:57 |

Every baseline: pass, 123 tests, exit 0. Shards 1-4 share one baseline tree; shard 5's differs from it in
`tests/test_hlc_draw.py` only and equals the final package files (M). The invalid run was a real kill (2 tests
failed) that the runner voids by its own rule, because my new write-failure test simulated `OSError(28, ...)` and the
mutant printed that message ("Errno 28" reads as a full disk). The runner's rule is right, so I changed the test to
`PermissionError(13, ...)` and re-ran the three entries that use that test on the final bytes: all killed. So all 65
entries are killed on the final production code (`draw.py`, `inputs.py`, `__main__.py`, settings identical in all
five shards); 62 of them ran with the test file one edit (that test's simulated error) before the final one. Earlier
shard runs in this round (26 entries on intermediate bytes, all killed) are superseded and deleted.

### 12.6 Commands run in this round (synthetic data only; all in ws-d2, FX, V read-only, or `builds/tmp/`)

| Command | Exit | Result |
|---|---|---|
| `date -u` (09:43:26, 09:49:36, 10:07:21, 10:09:26, 10:11:45, 10:14:38, 10:16:24, 10:17:01, 10:28:38, 10:57:47, 10:58:39) | 0 | |
| `ls`, `cat`, `sed -n`, `grep` on the verify report, my build report, PKG, HLC sections 4, 7-9, REV4:553-557 and :758-766, `reading_input/build.py`, `items.py`, `sources.py`, `runner.py`, `scoring.py`, the minimal_safety and safety_selection `common.py`, `.gitignore`; `shasum -a 256` of HLC (`29b781eb…`) and PKG; `git status --porcelain`, `git diff --stat`, `git log -1`; `git -C <main> check-ignore -v tmp/hlc/x` | 0 | |
| `V/repro_hb_minimum.py`, `V/repro_hb_minimum_cli.py <FX>/hbcli-before` on the build's bytes | 0, 0 | yes 1 / no 7; CLI yes 1 (D1 reproduced) |
| `FX/update_settings.py`, `FX/not_built.py`, `FX/update_spec.py` | 0 | settings `641b1cd4…` then `1d3eabe3…`; spec 65 entries, every find once |
| pytest suite, run 1 (`-x`) and run 2 (`--durations`) after the code change | 0 | 122 passed (45.1 s, 45.3 s; load average about 16) |
| `V/repro_hb_minimum.py`; `V/sim_hb_minimum.py`; `V/sim_hb_minimum.py low-u` on the fix | 1, 0, 0 | no violation found (exit 1 by its design); 0 breaks in all 15 settings |
| `FX/repro_hb_minimum_cli_fixed.py`, two runs (the first stopped at the renamed weights field after the draw had exit 0 with 2 "yes"; then the final); one inline `python -c` of mine beside the first run failed with a NameError (no result used) | 1, 0; 1 | final: yes 2 of 2, target 2/6 met |
| `FX/old_vs_new.py <FX>/worlds 0 1 2 3 4 5 6 7`; `FX/theta0_detail.py <FX>/worlds 4 5` | 0, 0 | 2 of 2000 cells differ, both theta0 (explained in 12.1) |
| one-off: count of the exhaustive test's cases that the old pass gets wrong | 0 | 28 of 300 (26 lose a minimum) |
| pytest runs 3-4 (after the added tests) | 0 | 123 passed (15.1 s, 15.4 s) |
| mutation shards A, B, C (26 new or changed entries, intermediate bytes) | 0, 0, 0 | 26 killed (superseded, deleted) |
| AST check of PKG (lines over 120, unused imports) | 0 | 2 long lines (inputs.py, a test), re-wrapped; `run_mutants.py` unchanged since the build |
| pytest run 5: suite and `scripts/stage1_s1/tests/test_s1_layout.py` | 0 | 126 passed (14.57 s) |
| full spec, shards 1-4, then shard 5 after the test edit | 0, 0, 0, 1, 0 | 12.5 |
| pytest run 6 (final bytes): suite and the layout tests | 0 | **126 passed in 14.51 s** (123 + 3) |
| one-off: the minimum-first counterexample | 0 | minimum-first (2, 1); fixed walk (2, 2) |
| `V/make_world.py <FX>/det 0`; `V/run_cli.py` draw under PYTHONHASHSEED 1 and 98765, `cmp`, `check` under 4242 | 0 | byte-identical; three "match" (12.9) |

Every pytest ran as `PYTHONDONTWRITEBYTECODE=1 …/venv/bin/python -B -m pytest -q -p no:cacheprovider
--basetemp=<builds/tmp/d2fix-runN>`; each basetemp (786 MB) and each mutation scratch folder was deleted after the
run; the worlds made by FX scripts were deleted. No `__pycache__` appeared in ws-d2 (M: `find`).

### 12.7 Files (final bytes, M)

| File | Lines | SHA-256 |
|---|---|---|
| `__init__.py` | 27 | `1ac0cb733524b06c2fda6669b7ea59e3d8595dd6ad43a32b919abff5397cf212` |
| `__main__.py` | 171 | `ee7d4747958579fe034023356e2faa0984771c2a8413f326c2c9000ce5672759` |
| `draw.py` | 395 | `61ef55cae6560c81e34bfd80f97e8abaa4e489cdf85b2d3fcb2da69d0aac7fa1` |
| `inputs.py` | 389 | `0fbacd72f58b1225fcefe36dbd0304d9da79fc3faf6109a7993fbb877cb20743` |
| `settings/hlc_draw.json` | 446 | `1d3eabe38e9b5d069623ba17bcef3f2d939d0abf309c5d7f06473847179a8c2d` |
| `tests/conftest.py` | 13 | `c4f625f5761c26a9a06f4918ab2d832ca469cd5dc56ace59bfdf0f40c8c56028` (unchanged) |
| `tests/hlc_world.py` | 345 | `b5ccd56234e73997524fea1c76d9dbb3fb281ade8f84f68ed8cf7f28edf1f489` |
| `tests/test_hlc_draw.py` | 1255 | `8d4875b2b795f5303b11e5e1bc7762e8e21b50c41c4db387c8575f7b75594221` (123 tests) |
| `mutation/mutants_hlc_draw.json` | 526 | `9a33f4418d5f637747e7eea52de99f7219ae99eb091a4376ca9e9f91fba886ad` (65 entries) |
| `mutation/run_mutants.py` | 217 | `5e60815377cea6a0342363ed8185424814a66012f591b2fb48ea52a50642968f` (unchanged) |

`hlc_world.py` changes: the world's `repo/` is a main checkout (`.git` folder, `.gitignore` with `tmp/`); greedy harm
guard records carry "Violent" except two planted sexual ones; `summary.json` has a `harm.greedy` block; a new SPECIAL
prompt p027; `make(..., crafted={label: Spec})`; `copy` skips earlier draws' sealed folders.

### 12.8 Statements in sections 1-11 that this round supersedes
- Header status, section 2's table, section 6's last rows and section 7: replaced by 12.5-12.7.
- 3.4: the walk and the split are as in 12.1 (no second pass); the sub-cell field `quota` is now `target`.
- 3.5: "`--sealed` must be a new folder outside the repository or under its git-ignored `tmp/`": now only under the
  main checkout's git-ignored `tmp/`; the manifest's folder must exist; a failed write leaves nothing.
- 3.3 and reading 7: rule b also reads the greedy harm answers' categories.
- 3.1: the draw's reads now include the greedy harm records of each unit's `guard.jsonl` (the same file, read once).
- 4: readings 4, 7 and 11 as in 12.4; readings 12 and 13 added.
- 8: the last sentence (running the draw before step 1) is withdrawn.
- 9 open point 7: `check` is documented as a reproducibility check; the independent checker is still not built.

### 12.9 Acceptance (the verifier's section 4, after this round)

| Point | Status |
|---|---|
| Reads block-A guard files only after block B is complete | passed (the order tests pass unchanged; the new checks of 12.2 point 1 run before any read) |
| Prints totals only; never an answer, a label or a per-unit value | passed (the stream tests pass; every new refusal names only paths and fixed text) |
| Writes the sample definition into a sealed or readable file as HLC says | passed; the place is now HLC 9's (point 4); sheets not built (disclosed) |
| New tool with tests on a synthetic kit | passed (123 tests) |
| HLC's seed tags fixed in its settings | passed (unchanged) |
| Deadline (LW-30, HLC:168) listed for the deviation record | passed (section 1, unchanged) |
| Draw against HLC's text | **D1 fixed**; readings 4, 7, 11, 12, 13 for the lead |
| Determinism | passed (M, on the final bytes: world seed 0 drawn in two processes with PYTHONHASHSEED 1 and 98765 into different folders: key `a3c2162d…`, weights `fafb49f7…`, manifest `6f424146…` byte-identical (`cmp`), stdout identical up to paths; `check` in a third process (PYTHONHASHSEED 4242): three "match", exit 0) |
| Refusals on a synthetic kit | passed (the earlier cases plus 17 new cases through the command line and 3 at the walk) |
| Run on real data | not done, by rule |

### 12.10 Open points (replaces section 9's list where they differ)
1. Deviation record for the late build (section 1), unchanged.
2. Confirm or change the readings (section 4 as amended by 12.4), especially 7 (now protective), 11 (point 3's
   options), 12 and the term list (point 5). Any settings change needs a new `SETTINGS_SHA256`, the suite and the
   affected mutants.
3. Copy the 9 Oct key out of `peaceful-jepsen-8b8eee` (unchanged). 4. Find the prepared-v3 folder (unchanged).
5. The auditor file's use (unchanged; it now also answers rule a's existence test, across banks, counts not kept).
6. Merge order with tracks A and B (unchanged).
7. HLC 4.3 item 4's independent checker: not built; another author, or a recorded deviation.
8. Not built: sheets, practice items, scorer, add-on draw (unchanged).
9. Never run on real units (unchanged). 10. Closed (mutants re-run on the final production bytes).
11. Run the draw from the main checkout (or `--repo` = the main checkout): the sealed folder must be under its `tmp/`.

### 12.11 What I did not open in this round (hard rule 1)
Nothing under the main checkout's `tmp/` was opened or listed; from it I only ran the prescribed interpreter
(`tmp/minimal-experiment-20261002/venv/bin/python`). No unit, eval, COMPLETE.json, answer, label, guard or
judge-cache file, no hidden or selector bank, no block-a or block-b record, no W1 sealed record, no path with "plant"
or "decoy". The other commands that touched the main checkout were `git check-ignore -v tmp/hlc/x` (a path that does
not exist; it reports the ignore rule only) and `ls -la` of its `.git` folder (first lines). Sources were read from
ws-d2 (the same commit, 55d5f8b). Every data file I read or wrote was synthetic, under ws-d2's pytest basetemps, FX or
`builds/tmp/`.
