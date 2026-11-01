# D2-ln31 verification 1: LN-31's draw for the human label check

- **Written** 2026-11-01, about 09:41 UTC (clock checked with `date -u` at 09:05:46, 09:22:09, 09:40:44 and 09:41:12 UTC).
  Author: an independent adversarial verifier (an Opus worker) for the main-study lead (GI VIII). Read-only on the
  builder's workspace; my own code and scratch only under `scratchpad/builds/verify-D2-ln31/`.
- **Object**: the untracked package `scripts/stage1_s1/hlc_draw/` in `scratchpad/builds/ws-d2` (detached at 55d5f8b;
  `git status --porcelain`: `?? scripts/stage1_s1/hlc_draw/`; `git diff`: empty). File SHA-256 values equal the build
  report's table (M): `__init__.py d9d252b4…`, `__main__.py 8964a3ae…`, `inputs.py 33b2d2ed…`, `draw.py 81d2e628…`,
  `settings/hlc_draw.json 1bef7f26…`, tests `c4f625f5…`, `4f02f7f4…`, `3345f32f…`, mutation spec `8296f9b5…`, runner
  `5e608153…`.
- **Verdict: DEFECTS.** One defect touches a frozen rule (HLC 4.2's HarmBench minimum, adopted by REV4 LN-34). It is
  narrow, cheap to fix, and does not touch the stage-1 reading or blinding. Everything else I checked holds: the
  population, strata, sizes, seed tags, exclusions, LN-31's read order, totals-only printing, byte-identical
  determinism across processes and hash seeds, and the refusals. Minor points are in section 3.

Labels: **M** measured here, **R** read in a source, **I** inference. **HLC** = `research/review/2026-10-17-stage2-design-notes/second-rater-and-human-label-check.md`
(revision 2; `shasum -a 256` = `29b781eb44918201…`, REV4's pin; M). **REV4** = the frozen pre-registration.
**W1R** = `research/experiments/2026-10-16-stage1-commitments.md`. **PKG** = `scripts/stage1_s1/hlc_draw/`.
**V** = `scratchpad/builds/verify-D2-ln31/`.

## 1. Defect that matters (frozen rule)

### D1. The walk can break HLC 4.2's "at least 2 of each [HarmBench label] where they exist"

**Rule (R).** HLC:157: "Inside each seed's Unsafe cell, the draw keeps the HarmBench "yes" and "no" answers in
proportion, with at least 2 of each where they exist." REV4:762 (LN-34) adopts HLC revision 2's draw. The build report
(section 4 reading 4) says the minimums are "dropped only when both cannot fit", and the test
`test_the_harmbench_split_keeps_two_of_each_where_they_exist` asserts `drawn >= min(2, available)` for both sub-cells.

**Cause (M, code).** `hb_split` sets the right quotas, but `draw.walk` takes answers in one pass over the sealed order.
When a prompt holds both a "yes" and a "no" Unsafe answer and the "no" answer comes first in the order, the walk takes
the "no" answer (its quota is not met yet), marks the prompt used, and later skips the "yes" answer ("no prompt twice
inside one arm"). The second pass tops up from the other sub-cell. Nothing re-tries the scarce sub-cell. The quota base
(`available`) also counts answers, not distinct prompts.

**Reproduction 1 (function level, the tool's own `allocate` with the real pinned settings and seed tags).**
`PYTHONDONTWRITEBYTECODE=1 …/venv/bin/python -B V/repro_hb_minimum.py` (exit 0). Input: unit "a0 1101", 200 harm prompts
x 3 answers; p000 and p001 each hold one Unsafe answer with HarmBench "yes" (sample 0) and one with "no" (sample 1);
p100-p109 each hold one Unsafe "no" answer; every other answer is Safe. Quota from `hb_split`: yes 2, no 6 (available
yes 2, no 12). The sealed order of `derive_seed(20261022, "hlc-v1", "a0/1101/harm/Unsafe")` begins
`(p102,0), (p000,1), (p001,0), …, (p000,0)`. **Expected:** 2 "yes" (p000 s0, p001 s0) and 6 "no" (a feasible draw
under the no-twice rule). **Actual:** yes 1, no 7.

**Reproduction 2 (end to end, the real command line in its own process, synthetic world).**
`PYTHONDONTWRITEBYTECODE=1 …/venv/bin/python -B V/repro_hb_minimum_cli.py V/hbcli` (exit 0; the draw itself exit 0, no
stderr). The world is `hlc_world.make(seed=0)` with unit "a0 1101" replaced: Unsafe answers p044 and p045 (sample 0
"yes", sample 1 "no"), p100-p109 (sample 0 "no"), and four decoys p040-p043 that the synthetic 9 Oct key takes.
**Expected:** a0 1101's Unsafe cell draws 2 "yes". **Actual:** "a0 1101 Unsafe cell drew 8 items, HarmBench yes 1
[('p045', 0)]"; weights file: yes quota 2, available 2, drawn 1; no quota 6, drawn 7. The builder's own test assertion
(`drawn >= min(2, available)`) would fail on this world.

**How likely on the real data (I; a simulation under stated assumptions, `V/sim_hb_minimum.py`, exit 0).** The tool's
`allocate` on simulated cells; a prompt's Unsafe propensity Beta(0.2, b) (Unsafe answers cluster on prompts); each
Unsafe answer HarmBench "yes" with probability q; a break counted only when both minimums were feasible. Results:
fine-tuned seed cells with U 0.10 or 0.30: 0 of 200 and 0 of 100 for every q (0.2, 0.35, 0.5); seed cells with U 0.05:
6/400 at q = 0.2, 0/400 at q = 0.35 and 0.5; U 0.03: 16/400, 8/400, 2/400; a theta0-like cell (U 0.032, quota 24):
26/400, 5/400, 1/400. So the risk is near zero unless a repair pushes a seed's U near theta0's, or in theta0's cell
(theta0's split is itself the builder's extension: HLC names "each seed's Unsafe cell"). The block-A U values are sealed,
so the real risk cannot be bounded further without reading outcomes.

**Consequence.** Only the report-only HarmBench-versus-human estimates (HLC 7 item 3) lose one "yes" answer in the
affected cell; no effect on the stage-1 reading, the weights' correctness (the weights file records what was drawn) or
blinding. But the sealed draw is one-time: once run, a break can only be cured by a recorded re-draw.

**Fix (proposed; small).** In the Unsafe cell, before the quota pass, take each sub-cell's minimum first: for the
sub-cells in order of fewest available distinct prompts, walk the sealed order and take that sub-cell's answers
(prompt unused) until min(2, its quota) are drawn; then the existing quota pass; then the top-up. Count `available`
(for the split and the minimum test) on distinct unused prompts, or state that it counts answers. Add both reproductions
as tests, update the settings' `harmbench_split.rule` text (new `SETTINGS_SHA256`) and the affected mutation entries.
Seed tags, cells and every other rule stay as they are; draws without such a conflict do not change (I).

## 2. What passed (M unless marked)

| Check | Result |
|---|---|
| Test suite: `PYTHONDONTWRITEBYTECODE=1 …/venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp=<builds/tmp/v-d2-run1> scripts/stage1_s1/hlc_draw/tests` (from ws-d2) | exit 0, **87 passed in 11.05 s**; basetemp 605 MB, deleted |
| `scripts/stage1_s1/tests/test_s1_layout.py` | exit 0, 3 passed |
| Mutation reports (`reports/D2-ln31-mutation-shard*.json`, read only) | 45 entries, 45 killed; one spec SHA-256 `8296f9b5…` and one runner SHA-256 `5e608153…`, equal to the files now; every baseline 87 tests, exit 0. Not re-run (the lead's job); run before the cosmetic edit, as the build report says |
| Population (HLC 4.1) | a0 and R at 1101-1103 from `REJUDGED_PINS['A']` (paths equal make_sheet.py's 9 Oct `eval_dir`s at 57d08dd, R); H1, A1, L1, S1, S3, S4 at 1102-1104 from block A's table; theta0 = the `1101-a0-init-a1` pin; draw order a0, R, H1, A1, L1, S1, S3, S4, theta0; seeds ascending; cells Unsafe, Controversial, Safe, Yes, No (HLC 4.2) |
| What is drawn | harm: `eval/<t>/samples.jsonl` + `guard_samples.jsonl`, 3 per dev harm prompt; benign: greedy over-refusal answers (`generations.jsonl` + `guard.jsonl`, kind overrefusal); dev bank only; field names equal the engine's writers (`runner.evaluate_checkpoint`, `scoring.generation_summary`/`harm_summary`/`overrefusal_summary`, `textproc.parse_guard_response`; R) |
| Sizes and reduction (HLC 4.2) | step 0: 24/4/12/5/5 per arm and theta0, 450 items (360 + 90), 20 repeats; step 2: 414 (Safe 8); step 3: 360 (Unsafe 18, Safe 8); repeats 10 at steps 1-3 (two synthetic worlds) |
| Seed tags (HLC 4.3 item 1, 4.4) | `derive_seed(20261022, "hlc-v1", "<arm>/<seed>/<block>/<cell>")`, theta0 `"theta0/<block>/<cell>"`; repeats `derive_seed(20261022, "hlc-v1-repeats", "harm")`; rater order `hlc-v1-order` with part `<rater>/<block>`, R1-R3; fixed in the pinned settings; 20261022 = REV4's date (REV4:3, R) |
| Exclusions (HLC 4.1 (a)-(c), 8) | 9 Oct key read only for `unit_dir`, `complete_json_sha256`, `unit`, `prompt_id`, `sample_index`; its format matches make_sheet.py at 57d08dd (R: `units[uid].unit_dir` is relative to the main checkout, items are sampled answers only); 15 required; minors rule a = source `simplesafetytests`, category `harm_area` "child abuse" (the v3 data configs' source name and category field, R); unscored reasons equal the engine's two strings (R: `scoring.py`); first reason wins |
| Independent re-implementation (`V/ref_draw.py`, written from HLC and the build report's readings, reading the synthetic world's raw files, not the tool's modules) | identical items and order, item ids, repeats, minors prompts, per-unit exclusions and item fields: world seed 0 step 0; world seed 7 steps 0, 2, 3 (all exit 0) |
| Determinism | world seed 0: draw in two processes with PYTHONHASHSEED 1 and 98765, into different folders: key `c120298e…`, weights `b2f26c86…`, manifest `5ec54445…` byte-identical (`cmp`); stdout identical up to paths; a third draw of a copied world at another path gave the same three SHA-256; `check` in a third process (PYTHONHASHSEED 4242): three "match", exit 0. Outputs hold no absolute path and no time |
| LN-31 order (below the tool's own spy) | `V/spy_order.py` patches `open`, `io.open`, `Path.read_bytes/read_text/iterdir`, `os.listdir/scandir`: with block B's seal entry removed, only `repo/rules.py`, `kit/plan.json`, `kit/seals/block-A.json` are touched, then exit 2; normally the seals A and B, the 9 Oct key, bank manifest, dev bank and auditor are read before the first unit file |
| Printing (totals only) | stdout: 9 fixed lines (plan.json and seals, settings, rules, pinned-input hash prefixes, "units read: 25", pooled exclusion totals, drawn totals, three `wrote … sha256`). Every refusal message in PKG and in the `reading_input` code it calls interpolates only names, paths, hash prefixes, constants, job, line or record counts (code read); any other exception prints its type only. The manifest holds no per-arm, per-seed or per-cell count (the builder's test, passing) |
| Refusals (`V/refusals.py`, 10 edited synthetic worlds, each in its own process) | all exit 2, empty stdout, nothing written, one `REFUSED:` line with no sentinel text or value: block-A seal at another hash; a kit unit's COMPLETE.json not at the seal's hash; a 9 Oct item naming a greedy answer; an auditor without a dev prompt; a pinned job.json changed; a duplicate dev-bank id; a HarmBench cache record of another judge; theta0's summary.json changed; block B unsealed; plan B. (My first run flagged plan B only because my harness took "HLC 4.1" for a decimal; fixed, rerun: 0 failures) |
| Deadline listed (task) | build report section 1 quotes REV4:762 (LW-30), HLC:164, HLC:168 (HD8), W1R:243 rule 7 and REV4:763; each quote matches its source line (R); the 25 Oct pod times match FOCUS's entries (R; FOCUS line numbers have moved since, as new entries are added) |

## 3. Minor defects and notes (do not change the verdict)

1. **Partial write on a refusal (contract break, minor).** Doc and report: "2 refused (nothing written)". Repro:
   `run_cli.py <pins> draw … --sealed V/w1/pw/sealedA --manifest V/w1/pw/no-such-dir/hlc_manifest.json`. Expected:
   exit 2, nothing written. Actual: exit 2, "REFUSED: an unexpected FileNotFoundError (its message is withheld…)", and
   `sealedA/hlc_key.json` and `sealedA/hlc_weights.json` stay on disk without a manifest; a second run then refuses
   ("the sealed folder or the manifest exists"). A dangling symlink at `--manifest` passes `exists()` and fails the
   exclusive create the same way (code read; I). Fix: check the manifest's parent folder before any write and remove
   the sealed folder if a later write fails (or write the manifest first). The proposed runbook's `mkdir -p "$RUN/hlc"`
   avoids it. The withheld message also hides which path is missing.
2. **"A second, independent process" (HLC 4.3 item 4) is not met by `check` alone** (disclosed as the builder's open
   point 7). HLC cites FOCUS's anchor check, which was "an independent recomputation from the DRAFT text and the engine
   code" (R: FOCUS:67 at 541b122). `check` reruns the same code in a second process; the module doc's "(HLC 4.3 item 4)"
   overstates it. `V/ref_draw.py` agrees on 4 synthetic draws, but it reads the synthetic layout without the kit's seal
   and pin checks and prints comparisons, so it is not a production checker. The lead rules: a separately written
   checker (another worker) or a recorded deviation.
3. **The benign label is not the stage-1 O label for long answers (a protocol question for the lead, not a build
   defect).** Under Branch 128 (W1-18 passed with it) stage-1 O judges dev-100 answers cut to 128 new tokens (REV4:555,
   LN-19; R), and theta0's and possibly the reused cells' O answers come from block A's O-only passes (build.py
   `_theta0`, `_reused_cell` route `generated`; R). The draw stratifies on the stored full-answer "Refusal" flag of each
   pinned unit's own `guard.jsonl`, as HLC's text and HLC:164's file list say. The builder's reading 11 covers a0 and R
   only; theta0 and the 128-token cut are not mentioned. The lead should rule which label and answers define the
   benign strata (HLC 4.1: "O is defined on these answers").
4. **Sealed-folder location vs HLC 9.** HLC 9: the key, weights and sheets "sit in a git-ignored folder of the main
   checkout (for example `tmp/hlc/`), never only in a Claude worktree". The tool also accepts any folder outside the
   repository, and a worktree's own `tmp/` when run from that worktree. The proposed runbook uses `$ROOT/tmp/hlc/…`,
   which is right; a check or a runbook line could enforce it.
5. **Term list (reading 6; the lead's content).** Over-inclusive as designed, but some likely forms are missed:
   "underaged", "teenaged" (no match after the trailing letter), "grandson", "granddaughter", "grandchild",
   "stepchild", "newborn", "jailbait", "csam", "under 18", "under the age of", "15 y.o.", "15 years of age". Rule b
   needs a sexual category too, so a miss matters only for minors-plus-sexual prompts; rater safety argues for adding
   them before the second stamp.
6. **Rule a has no sanity check.** If the local SimpleSafetyTests CSV's `harm_area` string differs from "Child Abuse",
   rule a silently matches nothing (the printed count would be 0; about 3 dev prompts are expected, I: about 16 SST
   prompts of 200 dev, 20% of SST is Child Abuse). A cheap guard: refuse unless some auditor entry (any bank; only
   counts used) has source `simplesafetytests` and category "child abuse".
7. **Rule b's guard categories** come from sampled harm and greedy over-refusal answers only (reading 7). Including
   the greedy harm answers' categories would be the more protective reading; the lead's call.
8. **theta0's HarmBench split** is an extension (HLC: "each seed's Unsafe cell"); it is in the settings' rule text but
   not in the report's list of readings. List it for the lead's confirmation.
9. **Manifest tool hashes** cover PKG and `reading_input` only; the draw also depends on
   `scripts/stage1_s1/reading/settings.py` (`canonical_json`, `strict_json`) and `experiments/minimal_safety/common.py`
   (`derive_seed`). Both are frozen code, and `check` would catch a changed output, so the risk is small.
10. **Running the draw before the reading** (build report section 8 offers it): the printed pooled totals (unscored
    and unlabelled answers, the rule-b count) depend on block-A guard outputs. They are totals, as LN-31 allows, but
    the plan's order (step 5, after the reading) avoids any question; I recommend keeping it.
11. **Run-time risks that refuse safely:** the 9 Oct key's `complete_json_sha256` values must equal the pins'
    (measured 27 Oct) and the key must be copied out of `peaceful-jepsen-8b8eee` (open point 3); the prepared-v3
    folder must be found (open point 4). A mismatch refuses with names only.
12. **Builder's process disclosures** (not re-checked): the mutants were not re-run on the final bytes; three shards
    ran past the 600 s tool limit in the background (hard rule 5's letter).

## 4. The task's acceptance points

| Point (task text) | Status |
|---|---|
| Reads block-A guard files only after block B is complete | passed (M: spy below the tool's reader; seal.py seals only a complete block, R) |
| Prints totals only; never an answer, a label or a per-unit value | passed (M: outputs, 10 refusal cases, code read of every message) |
| Writes the sample definition into a sealed or readable file as HLC says | passed for key, weights (sealed) and manifest (readable, text-free); sheets not built (disclosed) |
| New tool with tests on a synthetic kit | passed (87 tests) |
| HLC's seed tags fixed in its settings | passed |
| Deadline (LW-30, HLC:168) listed for the deviation record | passed |
| Draw against HLC's text (strata, sizes, seeds, what is drawn, what is printed) | **failed on one point: D1**; otherwise passed |
| Determinism | passed |
| Refusals on a synthetic kit | passed (minor: note 1) |
| Run on real data | not done, by rule (neither by the builder nor by me) |

## 5. Commands I ran (all exit 0 unless stated)

`date -u` (5 times); `ls`, `find`, `wc`, `du`, `shasum -a 256` on ws-d2's PKG, the reports folder and V; `git -C ws-d2
status --porcelain`, `diff --stat`, `log`; `git -C <main> log`, `diff --stat 55d5f8b 38e160d`, `status --porcelain`,
`cat-file -t 57d08dd`, `show 57d08dd:research/side-blind-read/make_sheet.py` (code), `show
57d08dd:…/PREREG-2026-10-08.md | sed -n 1,30p` (its sheet table and composition), `show 541b122:research/FOCUS.md | sed
-n 67p`, `check-ignore -v tmp/hlc/x`; `sed -n`/`grep` on HLC, REV4, W1R:243, FOCUS, the addendum (no HLC entry
found), the plan, the design-round reports, and code (`reading_input/*.py`, `stage1_rules.py`, `seal.py` doc,
`prepare.py`, `scoring.py`, `textproc.py`, `runner.py`, `config.py`, the v3 and kt data configs); the venv Python on
the settings file and configs (fields only); the pytest runs of section 2 (first attempt exit 127: `timeout` does not
exist on macOS; rerun without it); `V/make_world.py` (worlds seed 0 and 7); `V/run_cli.py` draws and checks (section
2; the partial-write run exit 2 by design); `V/ref_draw.py` (4 runs); `V/spy_order.py` (exit 2 unsealed, exit 0
normal); `V/refusals.py` (first run exit 1 from my harness's regex, second run exit 0); `V/repro_hb_minimum.py`;
`V/repro_hb_minimum_cli.py`; `V/sim_hb_minimum.py` (two runs). All Python with `-B` and `PYTHONDONTWRITEBYTECODE=1`;
no `__pycache__` or other new file appeared in ws-d2 (M: `find -newer`).

## 6. Evidence

- Scripts in V (SHA-256): `vlib.py 55f245d7…`, `run_cli.py 2c768696…`, `make_world.py 859ae7f6…`,
  `ref_draw.py 97c2925c…`, `spy_order.py 5d5aa88f…`, `refusals.py ebe7f4b0…`, `repro_hb_minimum.py 04cbf630…`,
  `repro_hb_minimum_cli.py 58272ee3…`, `sim_hb_minimum.py c34fd56d…`. Each re-creates its synthetic world in seconds;
  the world folders were deleted after this report.
- The builder's report `reports/D2-ln31-build.md` and shard reports `reports/D2-ln31-mutation-shard*.json` (read only).

## 7. What I did not open (hard rule 1)

Nothing under `tmp/stage1-olmo/`, `tmp/judge-pod*`, `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`, the
block-a/block-b record folders, any `units/` or `eval/` folder of real data, any COMPLETE.json, answer, label, guard or
judge-cache file, the hidden or selector bank, the auditor file, the 9 Oct key, and no path with "plant" or "decoy".
The real units' paths appear only as code text in `stage1_rules.py` and make_sheet.py. No W1 "sealed record" was
opened. Every data file I read or wrote was synthetic, under V or the pytest basetemp.
