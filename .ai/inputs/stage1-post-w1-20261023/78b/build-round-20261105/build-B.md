# Build report: Track B = T3 (the Llama sealed set; the OLMo draws d = 11-16; H1 on the Llama manifest)

Started 2026-11-05 13:28 UTC; finished 13:59 UTC (`date -u` before each time written; M).
Worker: bounded implementation worker for GI X (Fable builder). Worktree (detached at `fb51421`, M `git rev-parse`):
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-b`
Main environment: `tmp/minimal-experiment-20261002/venv/bin/python` (3.11.15, numpy 2.2.6, pytest 8.4.2; M).

Status: DONE for priorities 1 and 2; priority 3: H1 built, S1 **not built** (reason in §5 and §7).
No git state changed. No pod, spend, network, install, download, agent or message. Nothing written in the main checkout.
No text file, selector, hidden, judge or answer file opened; the prepared sets' `train_rows.jsonl` were read only by the
frozen builder's `Inputs`, by `s1common.PreparedView`, by my wrapper's `PreparedView` (row_id and target_tokens, text
dropped at once) and, in test (d), by the engine's own `load_prepared`; no row text printed or written.

## 1. Files changed (all new; `git status --porcelain` lists only these four untracked folders, M)

Priority 1, the Llama sealed set (`.ai/inputs/scale-78b-sealed-llama3-20261105/`):
- `build_sealed_llama3.py` (SHA-256 `5cd45926eccd6b4f5884ec0caf40f1790b064f4f89e2a84984646cdb6c9ef6ed`, M)
- `out/MANIFEST.json` (`76415c427e8112821ebe981b1a9f1274a556d9daa6955659d52c5e68589c418b`, M); `out/edits/R_d1.json` …
  `R_d16.json` (16); `out/edits/unit_g-<id>.json` (8)
- `README.md`; `tests/conftest.py`; `tests/test_build_sealed_llama3.py` (15 tests)

Priority 2, the OLMo draws d = 11-16:
- `scripts/scale78b/__init__.py`; `scripts/scale78b/build_r_draws_78b.py` (`25dd7aca8b269ede5fcc013ea6e650571e7a1c1bfe48ef9b5e77b2baa001784c`, M)
- `.ai/inputs/scale-78b-r-draws-olmo2-20261105/out/MANIFEST.json` (`da63483751af8671fb29cd773e4112ed03f0979e719849cb82443d784bb25632`, M);
  `out/edits/R_d11.json` … `R_d16.json`; `README.md`
- `scripts/scale78b/tests/conftest.py`; `scripts/scale78b/tests/test_build_r_draws_78b.py` (6 tests)

Priority 3, H1 on the Llama manifest:
- `scripts/scale78b/build_h1_llama3.py` (`8b00a67b021516cb5aea528afcc8927da433fe0f7d8b934f92cdfb75735fda56`, M)
- `.ai/inputs/scale-78b-length-rules-llama3-20261105/out/MANIFEST.json` (`189cd139e0675278f1bebd5912294a60a2b66c7679c72b8bb3d81e84199e46cf`);
  `out/edits/octile_0.json` (H1; `fdd3500497767fb2a06741dbdc4ed62345623001b6034e3e5ffe42e9a016493d`); `README.md`
- `scripts/scale78b/tests/test_build_h1_llama3.py` (6 tests)

Not changed: any engine file, frozen script, sealed file, `runkit/`, SEAL, `.ai/inputs/stage1-commitments-20261016/`.
BLD's bytes before and after every build: `80cb8944cbea2847a4d39cddae225158f98431a8612282e2dd7161239050d3c6` (both the tmp
copy and the committed copy; M).

## 2. Alternatives considered and why I chose

1. **Where to load BLD from.** Default: the committed copy `.ai/inputs/gate-b-sealed-20261008/build_sealed.py` (REQ-4's
   choice; present in every checkout; the same bytes as `tmp/gate-b-sealed/build_sealed.py`, both verified against the pin
   before use). `--frozen-builder` can name the tmp copy. BLD's module-level `REPO = HERE.parents[1]` then points at
   `<repo>/.ai`; harmless, because the wrapper puts the repository on `sys.path` first and never calls BLD's `build()`
   (the same situation as REQ-4). The provenance names BLD's own `BUILDER_REL` (the tmp path) and the committed copy.
2. **Byte parity for stage 1's d = 6-10.** Three options: (i) list equality only; (ii) echo REQ-4's `stage1_wrapper` block
   from `r_draws_record.json` as data; (iii) re-derive it with stage 1's own `s1common.provenance` on the committed REQ-4
   script and settings (pinned). Chose (iii): a true re-derivation, byte-identical here (Python 3.11.15, numpy 2.2.6 as
   in REQ-4's run; M); the test names the differing fields if an environment ever differs, and separately asserts list
   equality and document equality outside that block (the brief's fallback). (ii) would prove nothing; (i) is weaker
   than the check's C5 asks.
3. **A deterministic MANIFEST.** BLD's manifest holds a build time; mine holds none (and no git HEAD or executable path),
   so a re-run gives the same bytes (acceptance (g)). It records the Python version and the path BLD was loaded from;
   these affect `MANIFEST.json` only, never an edit file.
4. **Where the Llama writer lives.** In the wrapper itself (the brief's item 1), using the engine's `EDIT_KIND`,
   `edit_bytes`, `parse_edit`, `arm_of` by import; not `s1common.edit_document` (that would bind the sealed set to the
   stage-1 package). Each file is parsed back against the Llama set and must be refused against the OLMo set at build
   time, so (d) is also a build invariant.
5. **The membership check reads the Llama set with my own reader**, not BLD's `Inputs` (it refuses the Llama manifest by
   design); the reader is the pattern of BLD's `Inputs` and `s1common.PreparedView` (ids and counts only).
6. **d = 14-16.** Built (P78 §9.2 items 2-3 name d = 1-16 and 9-16) and labelled "not run under ruling 2" in the
   MANIFEST and the edit's role; dropping them would make a later 12-seed layout change need a new sealed build.
7. **H1 placement.** A separate folder `.ai/inputs/scale-78b-length-rules-llama3-20261105/` with its own script under
   `scripts/scale78b/`, not inside the sealed set's `out/` (that MANIFEST lists exactly the frozen builder's draws). The
   rule is imported from `scripts/stage1/build_length_rules.py` (`length_order`, `octiles`), not copied; the committed
   stage-1 settings (pinned) give the key and sizes; the Llama manifest is pinned in the script because the settings pin
   the OLMo one. Only octile 0 is written; all 8 cut points are recorded.
8. **S1: not built** (brief item 5's stop rule): the add edit holds the 48 rows' prompt and response text from the sealed
   list `s1.json` (`389c20ad…`, under `tmp/`, named by stage 1's add-s1 record) and needs the Llama codec for
   `encode_train`; both are text or a tokenizer I may not read. Written as "not built" in both READMEs.

## 3. Commands run (exit status; all foreground, each under 2 minutes)

| # | command (from the worktree root; paths abbreviated) | exit |
|---|---|---|
| 1 | `date -u; ls` of the worktree, `tmp/`, SEAL, r-draws | 0 |
| 2 | `shasum -a 256` BLD (tmp and committed copies), both prepared manifests, SEAL MANIFEST, r_draws_record, stage-1 scripts and settings | 0 |
| 3 | `sed`/`grep` reads of BLD, `edits.py`, `build_r_draws.py`, `s1common.py`, `build_length_rules.py`, `write_add_edit.py`, P78 §9.2, `prepare.py` | 0 |
| 4 | `.venv/bin/python -I -B` structural compare of the two prepared sets (counts only): dev groups equal, row ids equal, 100 rows differ in target_tokens | 0 |
| 5 | `venv/bin/python -I -B build_sealed_llama3.py --out scratch/try1 --olmo-parity-out scratch/try1-parity` (first run) | 2 (REFUSED: my lexicographic sort of `R_d10` vs `R_d6`; fixed to set equality) |
| 6 | the same, after the fix | 0 (25 files; MANIFEST `76415c42…`; parity: SEAL d = 1-5 and units byte-identical; stage 1 d = 6-10 byte-identical) |
| 7 | `venv/bin/python -B -m pytest -q -p no:cacheprovider .ai/inputs/scale-78b-sealed-llama3-20261105/tests` | 0 (13 passed, 1 skipped: no committed out/ yet) |
| 8 | `venv/bin/python -I -B build_sealed_llama3.py` (the committed out/) | 0 (MANIFEST `76415c42…`, equal to run 6) |
| 9 | `venv/bin/python -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests` (r-draws tests) | 0 (5 passed, 1 skipped) |
| 10 | `venv/bin/python -I -B scripts/scale78b/build_r_draws_78b.py` (the committed out/) | 0 (7 files; MANIFEST `da634837…`) |
| 11 | `.venv/bin/python -I -B` cross-check: Llama d = 11-16 remove lists and per-unit seeds equal the OLMo d = 11-16 | 0 (all True) |
| 12 | `venv/bin/python -I -B scripts/scale78b/build_h1_llama3.py --prepared …olmo2 --manifest 9ed61826… --out scratch/h1-olmo`; compare with stage 1's octile_0 | 0 (lists equal: True, 600) |
| 13 | `venv/bin/python -I -B scripts/scale78b/build_h1_llama3.py` (the committed out/) | 0 (MANIFEST `189cd139…`) |
| 14 | `venv/bin/python -B -m pytest --co -q experiments/safety_selection/tests --ignore=…/test_ss_gateb_runkit.py` | 0 (842 collected) |
| 15 | `venv/bin/python -B -m pytest -q -p no:cacheprovider .ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests` (both folders at once) | 2 (collection error: `from conftest import` collided across the two folders' conftest files; fixed by not importing from conftest) |
| 16 | `venv/bin/python -B -m pytest -q -p no:cacheprovider experiments/safety_selection/tests --ignore=experiments/safety_selection/tests/test_ss_gateb_runkit.py` | 0 (837 passed, 5 skipped, 1 warning, 77.67 s) |
| 17 | run 15 again after the fix | 1 (26 passed, 1 failed: my H1 test assumed every differing row has a changed token count; wrong, see §7 item 6; test replaced by the exact-order rule) |
| 18 | `venv/bin/python -B -m pytest -q -p no:cacheprovider scripts/stage1/tests/test_build_r_draws.py scripts/stage1/tests/test_build_length_rules.py` (unchanged code, sanity) | 0 (76 passed) |
| 19 | `venv/bin/python -I -B` inspection of the two differing H1 rows (ids and counts only) | 0 |
| 20 | run 15 again (final) | 0 (27 passed) |
| 21 | `git -C ws-b status --porcelain`; `git rev-parse HEAD`; `find` for `__pycache__` (none); final `shasum` of the three MANIFESTs and BLD | 0 |

No mutation run (none in the brief). No command took more than 90 s.

## 4. Evidence paths (all under the worktree unless stated)

- `.ai/inputs/scale-78b-sealed-llama3-20261105/out/MANIFEST.json`: `membership_check` (groups, member lists, row ids equal;
  100 rows differ in target_tokens), `parity.sealed` (13 files `byte_identical: true`), `parity.stage1_r_draws`
  (5 files `remove_list_equal: true`, `equal_without_stage1_wrapper: true`), 24 edit records with arm, SHA-256, seed, role.
- The parity output of run 6 (`scratch-b/try1-parity/PARITY.json`, since deleted with the scratch) showed
  `byte_identical: true` for `R_d6-R_d10` with `stage1_wrapper_rederived: true`; test (c) re-derives this on every run.
- `.ai/inputs/scale-78b-r-draws-olmo2-20261105/out/MANIFEST.json`: `reproduction.sealed` (5 byte-identical),
  `reproduction.stage1_r_draws` (5 lists equal), 6 edit records.
- `.ai/inputs/scale-78b-length-rules-llama3-20261105/out/MANIFEST.json`: cut points, by-category counts, token accounting.
- Tests: `.ai/inputs/scale-78b-sealed-llama3-20261105/tests/test_build_sealed_llama3.py`,
  `scripts/scale78b/tests/test_build_r_draws_78b.py`, `scripts/scale78b/tests/test_build_h1_llama3.py` (27 tests, run 20).
- This report: `…/scratchpad/b78/reports/build-B.md`.

## 5. Acceptance criteria

| criterion | result | evidence |
|---|---|---|
| (a) every Llama remove list equals SEAL's for d = 1-5 and the 8 units | passed | `test_a_…` (run 20); the build itself refuses otherwise |
| (b) equals stage 1's `R_d6-R_d10` for d = 6-10 (C5) | passed | `test_b_…`; build refusal otherwise |
| (c) OLMo-parity mode reproduces SEAL d = 1-5 and the unit files byte for byte; stage 1's `R_d6-R_d10` byte for byte where provenance allows | passed (byte for byte in both; the `stage1_wrapper` block re-derived; the test also proves list equality and names any differing field) | `test_c_…` ×2; run 6 |
| (d) `parse_edit` accepts each Llama file against the Llama set and refuses it against the OLMo set | passed (the engine's own `load_prepared` on both sets; also a build invariant with stubs) | `test_d_…` |
| (e) trap: a manifest with one member moved makes the wrapper refuse | passed ("member lists differ", via `check_membership` and via `build`; the unmoved control passes; the pinned manifest also refuses) | `test_e_…` |
| (f) BLD's bytes unchanged after the build | passed (`80cb8944…` before and after; the CLI re-hashes after writing) | `test_f_…`; run 21 |
| (g) a re-run gives the same bytes | passed (two `build()` calls equal, MANIFEST included; the committed out/ equals a fresh build; runs 6 and 8 gave the same MANIFEST hash) | `test_g_…` ×2 |
| the folder holds only new files; `git status --porcelain` lists only new paths | passed | run 21: four `??` folders, nothing else |
| 2nd priority: OLMo d = 11-16, MANIFEST, README, `scripts/scale78b/build_r_draws_78b.py` (loads BLD by path after its SHA-256 check; reproduces d = 1-5 and refuses otherwise), test | passed | runs 9, 10, 20; §1 |
| 3rd priority: H1 bound to the Llama manifest by the stage-1 rule with Llama token counts | passed (OLMo parity: the same script reproduces stage 1's `octile_0` list; Llama H1 shares 599 of 600 rows with OLMo's H1) | runs 12, 13, 20 |
| 3rd priority: S1 re-bound to the Llama manifest | **not built** (needs the sealed list's text and the Llama codec; the brief's stop rule) | both READMEs name the reason |
| engine suite in the worktree with `--ignore` for the fixture test | passed (837 passed, 5 skipped) | run 16 |

## 6. Jobs for the lead

1. **Merge by explicit paths** (new only): `.ai/inputs/scale-78b-sealed-llama3-20261105/`,
   `.ai/inputs/scale-78b-r-draws-olmo2-20261105/`, `.ai/inputs/scale-78b-length-rules-llama3-20261105/`, `scripts/scale78b/`.
   Commit the wrapper and its `out/` together: every Llama edit file embeds the wrapper's SHA-256 (`5cd45926…`), so the
   wrapper is frozen from the commit on, as BLD is (any byte change needs a rebuild into an empty `out/` and new arms).
2. **In the main checkout after the merge** (each under 2 minutes):
   `tmp/minimal-experiment-20261002/venv/bin/python -B -m pytest -q .ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests`
   (27 tests; they read `tmp/kt-prepared/` and the committed SEAL and r-draws), then `scripts/stage1/commitments.py check`
   (the post-W1 records rule), then the engine identity re-check (`472fc7f6…`; nothing here changes it).
3. The gate-b runkit engine test that needs the main checkout's fixture was ignored here:
   `tmp/minimal-experiment-20261002/venv/bin/python -B -m pytest -q experiments/safety_selection/tests/test_ss_gateb_runkit.py`
   in the main checkout (not required by this track; the engine was not touched).
4. **S1 on the Llama manifest** (shared with stage 2): REQ-7's rule (`scripts/stage1/write_add_edit.py`) on the Llama set
   needs the sealed list `s1.json` (`389c20ad…`, text), the Llama codec, a recipe for `max_train_tokens` and a Llama
   settings file (the committed settings pin the OLMo manifest and the 1B recipe `ceffe0ef…`). A lead-run job or a
   scale78b wrapper with text access; not a $0 Fable item under this brief's rules.
5. S3, S4 and the S4 add-dose edits (`S4_96`, `S4_192`): per model, after each model's untuned-answers pass (C6; T6).
6. Ruling 14 names the Llama sealed set's folder; if the lead wants its MANIFEST SHA-256 in FOCUS, it is `76415c42…`
   (and `da634837…` for the OLMo d = 11-16 folder, `189cd139…` for H1).
7. If a mutation set is wanted for the wrapper (the stage-1 rounds' habit), it is a lead background job; the decisive
   checks are already build-time refusals (parity, membership, manifest binding).

## 7. Unresolved concerns and limits

1. **Frozen-on-commit.** Same property as BLD: the wrapper's bytes are in every arm hash. A reviewer's "fix round" edit
   to `build_sealed_llama3.py` (even a comment) must be followed by a rebuild and a re-run of the tests; the committed
   `out/` test (`test_g_the_committed_out_folder_equals_a_fresh_build`) will fail until then.
2. **MANIFEST.json's environment fields.** It records the Python version and the path BLD was loaded from (`loaded_from`).
   A re-run with another Python or with `--frozen-builder tmp/gate-b-sealed/build_sealed.py` changes `MANIFEST.json`
   only; the 24 edit files hold no environment field and are unchanged.
3. **Byte parity for d = 6-10 depends on the environment** (Python 3.11.15, numpy 2.2.6, the committed REQ-4 script,
   settings and `s1common.py` hashes, the engine identity). It held here. If any changes, test (c) still proves list
   equality and document equality outside `stage1_wrapper` and names the differing fields; it then fails on the byte
   assertion by design, so the lead sees it.
4. **d = 14-16** exist in both sets but are not run under ruling 2 (R stops at the last method seed 1113). Labelled in
   the MANIFEST and in each edit's `role`. P78 §9.2 asked for them; the lead may ignore them.
5. **The engine's `load_prepared` in test (d)** reads `train_rows.jsonl` with its text into memory (the engine's own
   loader, no banks, no hidden); nothing is printed. The build itself uses stubs (ids only). If the lead prefers the
   test to use stubs too, it is a two-line change; I kept the real loader because it is the engine's view.
6. **H1 on Llama differs from OLMo's H1 by one row at the 13-token cut**, and my first test wrongly assumed each differing
   row has a changed count (run 17's failure). The replaced test asserts the exact rule (inside rows sort before outside
   rows under (tokens, sealed rank)); the README states the mechanism (a 14 → 13 shift enters; the worst-ranked 13-token
   row leaves). The cut points and the by-category counts are the same on both sets.
7. **`scripts/scale78b/__init__.py`** is new. Track C's `noise_reading.py` (T5) goes into the same folder; if that track
   also adds an `__init__.py`, the lead picks one at merge (mine is a four-line docstring).
8. **The names of the Llama edit files** ("scale-78b R_d (prepared-kt-dolly-llama3): …") differ from SEAL's names by
   choice, so a reader sees the manifest at once; the arms differ anyway (the manifest field). If the lead wants SEAL's
   exact names, that is a wrapper change (concern 1 applies).
9. **Nothing here reads a stage-1 outcome** or any 7-8B value; the only prepared-set fields read are row ids, token
   counts and membership. The 100 rows whose token counts differ between the tokenizers are reported as a count only.
10. Scratch outputs (`scratchpad/b78/scratch-b/`) were deleted after this report.
