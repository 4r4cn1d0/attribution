# The Llama sealed set (built 2026-11-05 13:48 UTC; the 7-8B tier's T3 and stage 2's Llama files)

**What.** The frozen Gate B builder's random-removal draws `R_d1` to `R_d16` (75 rows of each of the 8 units, 600 rows
each) and the 8 unit removals `unit_g-*` (all 600 rows of a unit), written for the Llama prepared set
`tmp/kt-prepared/prepared-kt-dolly-llama3` (manifest `c52a50af…`). Files: `out/edits/` (24 edit files) and
`out/MANIFEST.json` (`ba524373…`, every file's SHA-256 and arm). Built on the Mac by `build_sealed_llama3.py`
(SHA-256 `227aed4f…`; rebuilt into an empty `out/` in the fix round of 5 Nov 2026 after the write guard was widened to
SEAL, the anchor list and stage 1's folder, resolved from the script's own checkout, B-M2/B-M3; the round-1 build,
wrapper `5cd45926…` and MANIFEST `76415c42…`, was removed first) on the frozen builder BLD `build_sealed.py`
(`80cb8944…`, never copied or edited) with engine
identity `472fc7f6…`. $0; no pod, no network.

**Who uses it.** Llama-3.1-8B (the 7-8B tier: block 0 = `R_d1-R_d3`; block A = `R_d4`, `R_d5`; block B = `R_d6-R_d7`
under plan A, `R_d6-R_d10` under plan B9, `R_d6-R_d13` under branch H (b); ruling 2's layout) and Llama-3.2-1B
(stage 2): both have this manifest, so one set serves both (P78 §9.2 item 2; ruling 14). `R_d14-R_d16` are built for
completeness and are not run under ruling 2 (no R seed beyond the last method seed 1113). The unit files are kept for
completeness and for stage 2; TC does not run (ruling 6).

**How (the route of P78 §9.2 item 2 and the check's C5).**
1. BLD is loaded by path after its SHA-256 check, as stage 1's REQ-4 did. BLD pins the OLMo prepared folder and
   refuses any other manifest, so BLD's `Inputs` is built from the OLMo set (`9ed61826…`) and `draw_r(inputs, d)` is
   called for d = 1..16. The draw reads only the group ids and the sorted member lists.
2. Before any draw is used, the wrapper refuses unless the OLMo and Llama sets hold the same 8 dev groups, the same
   sorted member lists, the same categories and the same 4,800 training row ids, with an empty held-out partition in
   both (M: equal; 100 rows differ in `target_tokens`, which the draw does not read).
3. Reproduce first: BLD's own `edit_file` with its recorded provenance gives SEAL's `R_d1-R_d5` and the 8 unit files
   byte for byte (SEAL `MANIFEST.json` `d76d8bf9…` pinned), and `draw_r` for d = 6..10 gives stage 1's
   `r-draws/edits/R_d6-R_d10` remove lists (record `c09b20c1…` pinned). Any difference refuses and nothing is written.
4. Each Llama file is written by the wrapper's own writer in the engine's edit format: `manifest_sha256` =
   `c52a50af…`, the draw's remove list, and a provenance that names BLD's and the wrapper's SHA-256, the source draw
   (design seed 20261008, stream `gate-b-random-removal-v1`, the per-unit seeds), the earlier file that holds the same
   rows (SEAL's for d ≤ 5 and the units, stage 1's for d = 6-10; none for d = 11-16), the seed map (draw d runs at seed
   1100 + d) and the role. Every file is parsed back with the engine's `parse_edit` against the Llama set and must be
   refused against the OLMo set. The wrapper never writes under SEAL or under `.ai/inputs/stage1-commitments-20261016/`.
5. `MANIFEST.json` holds no build time, so a re-run gives the same bytes (M: two separate runs, the same hashes).

**Byte equality with SEAL is impossible by design** (the manifest field differs), so the decisive tests are list equality
and the engine's manifest binding. The Llama `R_d11-R_d16` hold the same rows as the OLMo `R_d11-R_d16` of
`.ai/inputs/scale-78b-r-draws-olmo2-20261105/` (M).

**Tests** (`tests/test_build_sealed_llama3.py`, 15 tests; run from the repository root with the main environment:
`tmp/minimal-experiment-20261002/venv/bin/python -B -m pytest -q .ai/inputs/scale-78b-sealed-llama3-20261105/tests`):
(a) every Llama remove list equals SEAL's for d = 1-5 and the 8 units; (b) equals stage 1's `R_d6-R_d10` (C5);
(c) the OLMo-parity mode (`--olmo-parity-out`) reproduces SEAL's d = 1-5 and unit files byte for byte and stage 1's
`R_d6-R_d10` byte for byte, with REQ-4's `stage1_wrapper` provenance block re-derived by stage 1's own
`s1common.provenance` on the committed REQ-4 script and settings (its Python and numpy fields are the environment's:
3.11.15 and 2.2.6 here, as in REQ-4's run; if they ever differ, the test names them); (d) the engine's `parse_edit`
accepts each Llama file against the Llama set (the engine's own `load_prepared`) and refuses it against the OLMo set;
(e) a trap: a prepared set with one member moved makes the wrapper refuse ("member lists differ"); (f) BLD's bytes are
unchanged after the build; (g) a re-run gives the same bytes, and the committed `out/` equals a fresh build. Plus:
a changed BLD refuses; a tampered SEAL file refuses; writing under SEAL or stage 1's folder refuses; 75 rows per unit
in every R file; the 16 draws are distinct.

**Frozen once committed.** Every edit file embeds the wrapper's SHA-256, so any byte change to
`build_sealed_llama3.py` changes every arm hash. Rebuild into an empty `out/` after any change, and treat the committed
wrapper as frozen (as SEAL's builder is).

**Not here (per model, not per manifest; the check's C6).** S3 (DataRx SAS over the model's own untuned answers), S4
(the model's own untuned answers) and the S4 add-dose edits `S4_96`, `S4_192` (ruling 12) need each model's
untuned-answers pass on a pod, so Llama-3.1-8B's and Llama-3.2-1B's differ; they are built per model and manifest after
that pass. **H1** on this manifest is in the sibling folder `.ai/inputs/scale-78b-length-rules-llama3-20261105/`
(the stage-1 length rule with the Llama tokenizer's target-token counts). **S1 is not built here:** the S1 add edit
holds the 48 S-pool rows' prompt and response text, read from the sealed prompt list (`s1.json`, `389c20ad…`, kept
under `tmp/`), and its writer (`scripts/stage1/write_add_edit.py`) encodes the rows with the model's codec under recipe
S; both need text and a tokenizer this build may not read. The lead can write it with REQ-7's rule on the Llama set
(a Llama settings file is needed: the committed settings pin the OLMo manifest and the 1B recipe).

**Sources.** P78 §9.2 item 2; the readiness plan T3 and its check C5, C6
(`.ai/inputs/stage1-post-w1-20261023/78b/readiness-20261105/`); rulings 2 and 14
(`.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-20261105.md`); BLD (`tmp/gate-b-sealed/build_sealed.py`,
the same bytes as `.ai/inputs/gate-b-sealed-20261008/build_sealed.py`); SEAL's README; stage 1's
`r-draws/r_draws_record.json` (REQ-4's builder and seed map); `experiments/safety_selection/edits.py` (`parse_edit`).
