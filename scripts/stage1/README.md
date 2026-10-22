# scripts/stage1: the stage-1 commitments before Gate B wave 1

New files only. No engine file, Gate B pinned script, kit file or sealed file is changed. The brief is `.ai/briefs/stage1-commitments-build-20261016.md` (revision 1) with the lead's decisions addendum (§1–§6).

- **T1 (commit 9525005; read-only):**
  - `s1common.py`: seeds, selection, edit files, text-free records, settings checks.
  - `write_score_edit.py`: the A1 contract and the generic score-to-edit path.
  - `labels.json`: the seed-label registry; append-only, and its 34 T1 entries never change.
  - `settings/write_score_edit.json` and `settings/build_plant.json`.
  - the tests, and the mutation runner.
- **Every draw** goes through `s1common` and a registry key. Code never holds a label string.
- **Every settings file** is canonical JSON. It pins exactly the registry entries it names (by entry digest), the engine identity, and its inputs by SHA-256.
- **Every output** is text-free canonical JSON (or JSONL) with a provenance block. A file that holds text is written only under `tmp/`, with a text-free sealed record beside it.

## REQ-1: the frozen opening lexicon

`lexicon/lexicon.json` (SHA-256 `bbbc71e9eebb62876430ffb5e0f54113c3818984b8369924b7bd2212c4c1ca17`) and `lexicon/lexicon.py` (SHA-256 `5a27dd040b74aa23fe09ac4dc95fb5913a4ccd327a67bb3caf5e667ff0432d1b`) are byte-for-byte copies of `tmp/mechanism-recipes/lexicon.json` and `lexicon.py`, with no edit.
- **Loading:** stage-1 code gets `classify` through `lexicon_pin.load()`. It imports `lexicon.py` by path, never runs it (its `__main__` block writes files), and refuses unless:
  - both files hash to their pins;
  - the module's `lexicon_sha256()` equals the JSON pin;
  - its `lexicon_bytes()` equal the JSON file.
- **Classes:** REFUSAL-OPENING, CAVEAT-OPENING, DIRECT and EMPTY. The stage-1 rules use REFUSAL-OPENING and DIRECT.
- **The T1 draw scan** skips these two files only while they hash to the pins in `settings/build_plant.json`. Any other file in `lexicon/` is scanned.

**Record of a naming defect (not edited):** the frozen reading `scripts/gate_b_reading.py` (line 216 at 9525005, `LEXICON_SCRIPT_SHA256_PREFIX = "bbbc71e9"`; the brief cited line 214 at an earlier commit) calls `bbbc71e9…` "the frozen Mac lexicon script". `bbbc71e9…` is the SHA-256 of `lexicon.json` (the lexicon itself). The classifier script `lexicon.py` is `5a27dd04…`. The reading stays as it is: it is a frozen Gate B file.

## Batch 2

- **`representation_pass.py` (REQ-3):** the shared untuned representation pass, which is model-agnostic. Its module text holds the hidden-state index convention, the four reads, CAS and CSS, and the Gate C byte reproduction. CUDA is untested.
- **`token_accounting.py`** (W1-01's base): a text-free view with prompt, target and total tokens; an edit's token accounting; the steps rule.
- **`lexicon_pin.py`** (REQ-1).
- **`settings/representation_pools.json`** (W1-08 (1)): REQ-3's pool pins. See below.

### W1-08 (1): the pool pins (the lead's ruling, option (a))

W1-08 (1) asks that REQ-3's settings name the plant pool and the decoy pool by SHA-256. Those hashes exist only after REQ-8's sealed Mac runs. A change to `settings/representation_pass.json` also changes `SETTINGS_SHA256` in the script and in its test. So the lead chose option (a):

- **A separate settings file**, `settings/representation_pools.json`, lists the W1-known pools as `{name: {sha256, items, source}}`. It is hash-pinned by `POOL_PINS_SHA256` in `representation_pass.py`. REQ-3's own settings and `SETTINGS_SHA256` (`a555fd89…`) do not change.
- **Now:** `plant` (75 items) and `decoy` (37 items, if W1-09 is built). Both `sha256` values are null.
- **The rule, for each pool given to REQ-3:**
  - A listed name needs a filled `sha256` equal to the pool file's SHA-256, and the same item count.
  - A listed name whose `sha256` is null is refused ("not filled yet").
  - An unlisted name whose SHA-256 equals a listed `sha256` is refused (the name and hash do not match).
  - The name `dev` is refused, in a pool file and in the pins file. It is the dev rows' source name.
  - Any other unlisted pool (the S3 pools) is named on the command line by SHA-256, through its own sealed record. The summary records `pinned_by` ("pool pins" or "command line") for each pool, and the pins file's SHA-256.
- **Only the 75-row plant pool is passed.** The 37-row plant rows are its first 37 rows (`build_plant.json`, `rows.nested`). A second pool would repeat ids, and the pass refuses a repeated id.
- **Filling (the lead, when REQ-8's sealed pools exist, before W1):** set each `sha256` from REQ-8's text-free sealed record. This changes three places and nothing else: the pins file, `POOL_PINS_SHA256` in `representation_pass.py`, and the literal in `tests/test_representation_pools.py`.

### Batch 2 revision 2: clean refusals

The command now refuses with exit 2, and writes nothing, for: a pool item that is not `{id, prompt, response}` with a text prompt and response; an unreadable settings, pins, pool or input file; a `--pool` that is not `PATH:SHA256`; `--pools-only` with no `--pool` (refused before the model loads). `token_accounting` refuses a unit that lists a row twice, and a rewrite whose new encoding has no target tokens. The other shares and breakdowns of W1-01 are REQ-27's (`report_token_accounting.py`), with its byte scan.

## Batch 3a: the random-removal draws and the length rules

- **`build_r_draws.py` (REQ-4):** it first reproduces the sealed Gate B files R_d1–R_d5 byte for byte, with the frozen builder loaded by path after its SHA-256 check. Then it writes R_d6–R_d10 with the frozen builder's own draw (d = 6, 7 for layout D1; 8–10 for plan B), and R_1200 and R_2400 at d = 2–4. Draw d runs at seed 1100 + d.
- **`build_r_tok.py` (W1-03):** token-matched random removal for A1, L1 and H1. Per unit, it walks a sealed order until the unit's token mass crosses T_m / 8. A secondary arm.
- **`build_length_rules.py` (REQ-5):** one sealed length order gives H1, H2b and the eight octiles; the category-matched controls; H2a by L6's pinned patterns.

## Batch 3b: the S-pool, the add writer, the plant and the O-ext bank

- **`build_s_pool.py` (REQ-6):** the S-pool (PKU-safe refusal openings whose companion is unsafe), its seven filters in order with ANCH's labels (N after each), and the lists S1 (48), the S3 subset (1,000) and the S4 candidates (512). It writes REQ-3's pool `s3_safe` and a text-free record with L8's counts and W1-11's fields. The lead runs it; it opens the hidden bank through ANCH's loader, counts only (L9).
- **`write_add_edit.py` (REQ-7):** add edits (ids `add-<list>-NNN`) and combined edits (for example R+S1), parsed back with the engine and encoded with `edited_corpus` under recipe S's limit.
- **`build_plant.py` (REQ-8):** it loads T1's `build_plant.json` (unchanged) and `build_plant_extra.json`. It builds the 75 DIRECT plant rows (prompt-disjoint from every S-pool candidate, the anchors and the lists), L12's grouping and placement, the draws, and every edit. It also builds the W1-09 decoy (scored only) and, only with `--f9`, the two F9 locations. It writes REQ-3's pools `plant` and `decoy`.
- **`build_oext.py` (addendum §7):** the 400 PHTest harmless prompts of the O-ext bank, after the exact and near-duplicate exclusions (every bank of P, the anchors, the S-pool and the plant rows), by the sealed order `oext.phtest`.
- **Text:** every file that holds text goes to `--full-out`, inside a folder named `tmp`. Records and remove-only edits are text-free.
- **Run order on the Mac:** REQ-6, then REQ-7 (S1, and R+S1 with REQ-4's R_d2–R_d4), then REQ-8, then O-ext. If O-ext stops with fewer than 400 eligible prompts (a counts-only stop), run `build_oext.py` again with `--accept-shortfall` (LN-24, addendum §10): the bank is then all N' eligible prompts in the sealed order, and the record carries the shortfall (eligible, planned, rule). Then fill REQ-3's pool pins from REQ-8's record.
- **Stops carry counts:** a REQ-6 or O-ext stop names the candidate count, N after each filter and each filter's removals by reason (no id, no text). Every builder checks that `--full-out` and `--out` are absent or empty before it writes anything, so a refusal leaves nothing written. `--combine-with` names are plain file-name stems and may not repeat.

## Batches 4 and 5: the pod scripts, the scorers and SD-600

- **`build_reuse_spec.py` (LN-12):** the text-free job spec for the reused units: a0 at 1101–1103 and R_1–R_3 (R_4, R_5 if Gate B's extension ran them) are regenerated by a train-only re-run on engine X, accepted only on an equal e1 adapter fingerprint, training identity, prepared manifest and data config; then each gets an O-only pass on the 500-prompt bank by `scripts/stage1_s1/oext_eval.py` (addendum §11 point 1), under the cap branch W1-18's record selects (no record: Branch full). θ0 gets its own O-only pass and, under Branch 128, LN-14's transfer report. Never a pull from a stopped kit pod; every output under block A's seal.
- **`make_untuned_answers.py` (REQ-9, W1-06):** the untuned model's greedy answers in chunks of 32 list positions (L11), the S3, S4 and SD-600 keep rules (L14), REQ-3's pool `s3_orig`, REQ-7's list `s4`, and the untuned per-row loss of S1, the s3_safe pool and S4.
- **`score_l1_larf.py` (REQ-10):** the layer scan (block l's post-sublayer norm outputs scaled by 1 ± α; lexicon refusals; the l_s rule) and the score from REQ-3 at index l_s + 1, read (a), as T1's scorer output.
- **`score_s3_datarx.py` and `write_score_add.py` (REQ-11):** SAS from REQ-3's s3_safe and s3_orig rows (indices 1..n, read (a)); the top 48 by `s3.ties`, written as the prompt list `s3` for REQ-7.
- **`score_classifier.py` (REQ-23):** the guard's normalized Unsafe score per dev row, plant row and decoy row, as the pinned Gate C classifier scores rows; the top 600 scored only, ties by `classifier.ties`.
- **`score_datashield.py` (REQ-12)** and **`score_selfinf_n.py` (REQ-13):** CSS at the CAS-argmax index from REQ-3's output; Self-Inf-N's ln(SI + 1) + ln(len + 1) at q from the attributes unit (read only through T1's `check_attributes_unit`), with e1 and q + e1 report-only. Both write T1's scorer output; REQ-12 and REQ-13 fall back to post-Gate-B exploratory if not committed at W1 (ADD-6.6).
- **`write_sd600.py` (REQ-15):** A1's 600 prompts as REQ-9's `sd600` list; then the SD-600 edit: rewrite with the untuned answer only when it ended, is non-empty and encodes; remove every other row (never truncated).

## Batch 8: Part G (the manifest and the reports)

- **`commitments.py` (REQ-20, W1-17, LN-30):** `build --repo ROOT` writes `.ai/inputs/stage1-commitments-20261016/MANIFEST.json` from the tree of HEAD (git, never the working copy): every tracked file under `scripts/stage1/`, `scripts/stage1_s1/` and the sealed folder, by the include, exclusion, role, requirement and conditional rules of `settings/commitments.json`; no hash is typed in by hand. It refuses an uncommitted or untracked file under those rules, a text-bearing kind, an edit file with text, a sealed record of a kind outside the text-free allow-list, PREREG off its pin, and an appended label not named "registry, after the seal". The REQ-21 record and FOCUS are excluded (LN-30: the record carries the manifest's SHA-256). `check --repo ROOT` regenerates the manifest from its base commit and refuses a missing file, a changed byte, a file git does not track at HEAD or that differs from HEAD, a conditional entry without its condition text and a not-built entry without its label.
- **`report_token_accounting.py` (W1-01, REQ-27 (a)):** per arm's edit file, by `token_accounting.account`: the removed, rewritten and added rows' target and total tokens, as shares of P's totals, per unit and category, and the edited corpus's optimizer steps; add and rewrite counts come from the writer's text-free record, cross-checked.
- **`dose_axis.py` (W1-02, REQ-27 (b)):** one pure function: the token-equivalent random dose T*_m and the token-matched contrast Λ_tok,m on the total-token (default), target-token and row axes; no extrapolation past T_2400.
- **`report_plant_ranks.py` (W1-08, REQ-29):** the planted cell's ranks at M = 8, 32, 128 beside the no-plant ranks, the row AUCs with bootstrap intervals (`plant.auc_boot`), the F4 dilution table, the F6 relocation replay and the F7 decoy; text-only scorers are construction checks, and only A1 and (by its switch) Self-Inf-N-style count.
- **`tests/test_registry_owners.py`:** every registry owner exists and quotes its key; every entry appended after T1 is named "registry, after the seal".
