# Lead rulings for Part 2 and the kit (7-8B tier, 5 Nov 2026)

Recorded 2026-11-05T18:12 UTC by General Implementation X, the main-study lead, under the user's delegation (no
approval questions; the frozen money and blinding rules apply). Part 1 is frozen (f5e3b4c) with the addendum A1-A17;
these rulings come after it and govern Part 2 and the 7-8B kit. They follow round 3 of the $0 build (records:
`.ai/inputs/stage1-post-w1-20261023/78b/build-round-20261105/`, build-E, verify-E, build-F, verify-F). No stage-1
outcome was read for them.

- **PP1. The untuned-answers pass takes the main recipe as its recipe S.** `make_untuned_answers.py` reads recipe S only
  for `model.max_train_tokens` (R: `scripts/stage1/make_untuned_answers.py:84-93`), and S_78 equals the main recipe
  outside the recipe-S fields (A1's maker; T6a's test). So the pass and the add-edit writer take the family's main
  recipe, and can run before the anchor job. The recorded `recipe_s` hash is the main recipe's; Part 2 states this.
- **PP2. Two untuned-answers calls per pod.** The first call takes the S3 list with the losses (`--list s3 --loss s1
  --loss s3_safe`); the second takes the S4 list alone, with the dose block. Basis: with one call, a pre-set S4 dose
  fallback (Part 1 §10) exits 3 in the unchanged 1B code and drops the S3 outputs that the later passes need
  (verify-E D1).
- **PP3. Two kind names.** `rep_pass` is REQ-3's representation pass (`scripts/stage1/representation_pass.py`; the
  stage-1 kit's name). `a1_pass` is A1's attributes pass on the a0-1101 retrain's q and e1 states (the engine's
  attributes job; RP:43's 6-11 h; the 16.5 h cap at most). Each has its own E cap. Both need S_78 and the anchor file.
  The kit's `rules_78b.py` and Part 2 use these names.
- **PP4. The scorer kinds run on engine X.** Every wrapper kind (untuned answers, `rep_pass`, the L1 scan, the
  classifier and the Mac-side scorers) runs on engine X: the derived settings pin X, and the frozen settings check
  refuses another identity (R: `scripts/stage1/s1common.py:589-591`). A run on engine Y would need settings re-derived
  for Y. The engine's own jobs (the retrain, `a1_pass`) follow ruling 10 and A13. The classifier runs under S_78, as
  at 1B, so the kit lets it through the S_78 key check.
- **PP5. S1 at 7-8B.** OLMo-2-7B's S1 arm reuses stage 1's committed S1 edit (`add_s1.json`, `904a0cf1…`) by hash: all
  48 rows encode within the 7B main recipe's limit, and REQ-7's writer reproduces the file exactly (M: track F,
  record `9b340bf5…`). Llama-3.1-8B's S1 edit is new (`69426993…`, 48 add rows on the Llama manifest), built by a
  frozen script in `.ai/inputs/scale-78b-s1-llama3-20261105/`. As in stage 1, the edit file holds text and lives in
  git-ignored `tmp/`, named by hash in the committed MANIFEST. The sealed S1 list was recovered byte for byte from
  the OLMo S1 edit; it is accepted because its bytes hash to the sealed pin `389c20ad…`.
- **PP6. Limits recorded, not fixed.** Two scope limits of the frozen S1 build script's write guard are recorded in
  its README (verify-F's F-2: the forbidden folders are the script's own checkout and `--repo`; F-3: the S1 folder
  does not forbid itself, so only its committed `out/` is protected). A code change would mean a rebuild and a new
  arm hash. The same holds for RV2-1 in the Llama sealed set.

## PP7-PP10. After the kit round (recorded 2026-11-05T18:56 UTC)

The kit round (wf_9816c21b-ee7: the shell, the job runner and the Llama token path, with a core and a security
verifier) left these for the lead. Records: `build-K1.md`, `build-K2.md`, `build-K3.md`, `verify-K-core.md`,
`verify-K-gated.md`.

- **PP7. The Llama sealed-set pin.** `SEALED_SETS['llama31-8b']['sha256']` takes
  `2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c`, the MANIFEST committed in d422fca (FOCUS
  entry "THE 7-8B SEALED SETS … ARE MERGED"). The kit reads that MANIFEST's own form, and Gate B's form for
  OLMo-2-7B's R_d1-R_d3.
- **PP8. The kind names in the cap rule.** PP3 applies to `rules_78b.py`: `a1_pass` carries A1's 16.5 h cap at most;
  `rep_pass` is REQ-3's representation pass with its own E cap (the stage-1 kit's 1 h estimate at 1B, scaled to
  7-8B with T2's scorer-kind factor, until measured). The S_78 kinds are the retrain, `rep_pass`, `a1_pass` and the
  classifier (PP4).
- **PP9. Accepted as built.** The Mac-side cap gate reads s = 1, and the pod-side gate reads the measured s; the
  pod-side gate governs. `s_obs` is the largest over the pod's finished arms (the conservative reading of KCR:113).
  Each job record keeps the engine verify's 600-character tail (names and hashes only), and the secret scan covers
  it. An unreadable 200 whoami reply warns and the Range check decides (the user's waiver of 7 Oct 2026).
- **PP10. Tests never reach the network.** One development test run in the kit round started a real `ssh` to an
  unroutable test address (203.0.113.9) with a fake token. The kit's tests get a guard that fails any real
  subprocess, ssh or socket call, so this cannot recur.
