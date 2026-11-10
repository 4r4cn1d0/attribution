# K6 kit minor items (round 6): K5v-1..K5v-9, the data/ scan ruling (K5v-3), the C0_SOURCE pack check (item 23)

Started 2026-11-07 11:43 UTC. This version 12:33 UTC (`date -u` read right before each write). Status: **DONE**.

- WS = scratchpad/b78/ws-k4 (HEAD 197ea37). SCR = scratchpad/b78/reports/k6-fix-scratch/.
- PY = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (tests, runners).
  PY2 = /Users/spiderishi/Coding/attribution/.venv/bin/python (spec edits, scans, JSON reads; always -B -I).
- SBX = `sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'`. Every pytest run and
  every runner chunk ran under SBX, with PYTHONDONTWRITEBYTECODE=1, `-B`, `-p no:cacheprovider`, `--basetemp` in SCR.
- Tags: M measured (command number in section 4), R read (path:line), E estimate, I inference.
- No pod, spend, network, install, download, agent or message. No git state changed (git used only as
  `git --no-optional-locks status/diff/check-ignore`). Nothing written in the main checkout. Written only under
  WS/runkit/stage1-78b/, WS/tmp/engine-y-34bfd288 (the allowed fixture copy, git-ignored, M #13) and SCR.
- No forbidden folder, selector, hidden, judge, answer, generation, sample or prompt-text file opened. In the real
  prepared folders I listed file NAMES, read manifest.json (its "files" keys and its SHA-256) and ran the kit's scan on
  the three unlisted files (pattern names only); no listed file was opened (M #9).

## 1. Files changed (all in WS; SHA-256 after the change)

| File | SHA-256 |
|---|---|
| runkit/stage1-78b/pack_setup.py | e3651a9860578e45291b4b401e17d71ce920ee9e1cd1b42eea484dcb270ea625 |
| runkit/stage1-78b/README.md | 8304db08a0d73e2f77311d751868dcf9ca44972d0f6774e0f79eb0e04b564a10 |
| runkit/stage1-78b/tests/test_scorer_block_78b.py | b72b5751aaec2df84c55810794a525c6375c7b8b7638ff08b12fd8c00af29fe7 |
| runkit/stage1-78b/tests/test_gated_78b.py | 1b27927a47132f33ccdf278a6152b791092578f980e795eab760c57e2e66fb63 |
| runkit/stage1-78b/tests/test_pp10_process_wide.py | e799c076cde19fb543aee01aefd2da4a4ce3d042d11e526c8e299d10d330e3b7 |
| runkit/stage1-78b/tests/test_kit_78b_runner.py | 31734b052e03308d51ca663103fb89cbf8a9a4baa8e379b9db6c7de0aeeaf715 |
| runkit/stage1-78b/tests/mutation_spec_scorer_78b.json | 1dd57ad8be666f6461c75866c457e2c89c42a964fb20c48a988cf61e6a1718ed |
| runkit/stage1-78b/tests/mutation_spec_gated_78b.json | 17b3bb5650e7377ec8327fe3962bf360bfa604083cc00984d5d35c78a368180e |
| runkit/stage1-78b/tests/mutation_spec_runner_78b.json | 324f09697559c398f8c025d35573d3759587fe1bd003b48c879f5263ab6c493a |

Not changed: mutation_spec_rules_78b.json (no item touches the rules modules), tests/conftest.py, launch.py,
setup/job_runner_stage1.py, rules_78b.py, stage1_rules.py, every runner script, runkit/stage1-olmo (M #12: git status
lists only the 9 files above; no untracked file under runkit/). diff stat: 9 files, +660, -39 (M #12).

## 2. Items: what I changed and the evidence

### Item 1. K5v (k5-verify.md): V1-V5 adopted, token files removed, the call-site spy, the flaky folder names

The K5v ids are not numbered in k5-verify.md; I map them by content, as the brief does (K5v-2 = token files,
K5v-3 = data/, K5v-6 = call site, K5v-9 = flaky test). The rest are the 6 test-gap survivors (V1-V5) and K5v-D1c's
"equivalent in effect" link case (now a test, V1).

**V1-V5 (the 6 test-gap survivors).** Taken from k5-verify-scratch/k5v_tests/test_k5v_survivors.py (R) into the kit's
own files, so each sits in the test file its runner runs:
- V1 `test_k6_v1_c0_refuses_a_linked_source_unit_...` and V2 `test_k6_v2_a_side_unit_with_no_e1_checkpoint_is_a_crash`
  in test_scorer_block_78b.py (the scorer runner's file).
- V3 `test_k6_v3_the_wrapper_refuses_real_sockets_made_with_an_explicit_protocol` (collection and a module fixture)
  and V4 `test_k6_v4_the_hook_refuses_in_a_default_named_thread_and_in_a_raw_thread` in test_pp10_process_wide.py
  (the gated runner's file; same fail-closed form as the file's other probes: a real socket call runs only after the
  same event raised by hand is refused).
- V5 `test_k6_v5_a_redirect_off_the_hub_through_the_whole_dispatch_drops_the_token[301,302,303,307,308]` in
  test_gated_78b.py (recorder connections, no socket; the response processors run, so a 30x goes through the real
  redirect handler).
- Changes from the scratch form: names prefixed test_k6_; the module-qualified helpers (pw., the gated names) used
  directly; V3 and V4 also assert the probe counts; V5's response class renamed `_RedirectResponse`, `HUB_HOST` used.
- Mutants: the verifier's six hand mutants added to the specs with their exact find/replace (scorer: K5v-D1c-link-accepted,
  K5v-R21-no-e1-checkpoint-accepted; gated: K5v-G1-wrapper-skips-explicit-proto, K5v-G2-hook-default-named-threads-free,
  K5v-G2-hook-dummy-threads-free, K5v-G3-redirect-keeps-token). Each is killed by its V test (M #5, #6).

**K5v-2 (token-shaped files left behind).** Each test that writes a token-shaped value now removes it in a
`request.addfinalizer` (runs on pass and fail):
- test_k5_r4 (`tmp/k5-r4/edit.json`, `rows.jsonl`, the planted engine file; the scorer script and setup/extend_cap.py
  are restored from their kept bytes even if the test fails midway);
- test_the_pack_refuses_a_token_shaped_string_in_a_named_scorer_input (`tmp/lists/anchor_prompts.json`,
  `tmp/w/adapter.safetensors`, `tmp/w/x.json`);
- test_the_preflight_writes_the_speed_and_bank_fields_and_refuses_a_slow_pod (the `shell-login/` folder);
- my new test_k6_the_pack_refuses_..._unlisted_data_file (its four planted files).
- Evidence: the 7-8B suite's basetemp held 7 hf_token hits before (M #2: the same 7 paths k5-verify named) and
  **0 after** (M #4, #14: 27,273 files, 5,365 tar members). The 1B suite's basetemp: 0 (M #14). WS/runkit/stage1-78b:
  0 (M #14). SCR: 0 (M #15). No mutant: the cleanup is not a behaviour a test can observe from inside the run
  (concern 3).

**K5v-6 (pin the edits/ scan at the bundle's call site).** `test_k6_k5v6_the_bundle_scan_at_its_call_site_...` spies on
`pack.refuse_secrets` and `secret_scan.scan_paths` in a real pack: the bundle's call skips exactly `("data/", "inputs/")`,
its files include the 3 R_d edit files and every one of them reaches `scan_paths`; the prepared set's 3 unpinned files
are in its `scan_anyway` and are scanned; a manifest-listed file is packed and not scanned; the setup tar's call skips
nothing. K5v-R4-call-site-skips-edits (find/replace moved to the new two-line call) is killed by it (M #5).

**K5v-9 (the flaky folder names).** test_kit_78b_runner.py: the three worlds are `w-0`, `w-1`, `w-2` (by index), not
`w-{abs(hash(repr(free))) % 1000}`. M #8: with the old formula, hash seeds 868 and 1027 (of 0-1499) give a collision
(my count is 2, k5-verify's was 5; I did not find why they differ); the fixed test passes at seeds 54 (k5-verify's
reproduction), 868 and 1027. Runner-spec mutant K6-free-space-folders-collide (all three worlds share one name: the
flake's mechanism at every seed) is killed (M #6).

### Item 2. K5v-3, the lead's ruling: the data/ scan

**pack_setup.py.**
- New `prepared_files(folder, digest)` (R: pack_setup.py, after `prepared_set`): returns the files to pack, the files
  to scan and the files skipped. A file manifest.json's `files` map lists, at that file's SHA-256, is packed and not
  scanned. A macOS metadata file that is not listed is skipped by name: `MACOS_METADATA` (.DS_Store, .localized,
  "Icon\r", .Spotlight-V100, .Trashes, .fseventsd, .TemporaryItems, .DocumentRevisions-V100, .VolumeIcon.icns,
  .apdisk, .com.apple.timemachine.donotpresent) or any path part starting with "._" (`macos_metadata`). Every other
  file is packed and scanned (prepare_receipt.json, manifest.json, manifest.sha256, a stray file).
- `refuse_secrets(..., scan_anyway=frozenset())`: a file under the skipped prefixes is scanned when its name is in
  `scan_anyway`. The bundle's call passes the unpinned data/ names. `DATA_PREFIXES` is unchanged ("data/", "inputs/").
- main's prepared-set loop uses `prepared_files` (pins from the same hash pass).
- Two choices inside the ruling, for the lead to confirm (concern 1):
  (a) "skips .DS_Store ... by name": I read "the pack skips" as **neither packed nor scanned**. The literal
      alternative (packed but not scanned) would ship an unscanned, unpinned file. The test asserts the stricter form.
  (b) "the manifest pins them": a listed file stays outside the scan only at its listed SHA-256, and the list is read
      only when manifest.json's own SHA-256 is the family's pin (`PREPARED_MANIFESTS`). Otherwise the file is scanned.
      This is fail-closed: it scans more, never less, than the literal rule. For the real sets it is the literal
      rule (M #9: both real manifest.json files are at the kit's pin and at their manifest.sha256).
- Not added: a refusal when manifest.json is off its pin. Every synthetic world's manifest.json is off the pin
  (R: tests/test_scorer_block_78b.py, `ScWorld.pack`), so that refusal would need a fixture change; the pod's engine
  checks it (R: experiments/safety_selection/prepare.py:877-886, `read_manifest`). Concern 2.

**README.md and the pack_setup.py docstring** now say exactly this (R: README.md "The pack's secret scan" bullet;
pack_setup.py:24-33).

**Tests (test_scorer_block_78b.py).**
- `test_k6_prepared_files_scans_what_the_manifest_does_not_pin_and_skips_macos_metadata_by_name`: listed file at its
  hash -> not scanned; listed file changed -> scanned; unlisted (receipt, stray, manifest.json, manifest.sha256) ->
  scanned; .DS_Store, `engine/._train_rows.jsonl`, `.Spotlight-V100/store.db` -> skipped; manifest.json off the pin
  -> nothing counts as listed; a `files` value that is not a map -> nothing listed; `macos_metadata` true for 5 names,
  false for 5 (".notes", "a/.env", "x.DS_Store", "a._b", "prepare_receipt.json").
- `test_k6_the_pack_refuses_a_token_shaped_string_in_an_unlisted_data_file_and_ships_no_macos_metadata`: the real pack
  with a token-shaped string (built at test time) planted in prepare_receipt.json, then in a stray file: each refuses
  with exactly `a secret pattern is in a packed file: [('<name>', 'hf_token')]`, the text never quoted, nothing
  written; the same string in .DS_Store and `._manifest.json` does not refuse, neither is in the bundle or in
  sealed-files.json, and no bundle member holds the string.
- test_k5_r4's end: a data/ file in `scan_anyway` is scanned and refuses.
- Mutants (scorer spec), all killed (M #5): K6-pack-unlisted-data-not-scanned, K6-refuse-ignores-scan-anyway,
  K6-macos-metadata-packed, K6-macos-metadata-every-dotfile, K6-listed-hash-not-checked, K6-manifest-pin-not-checked,
  K6-listed-files-scanned. Two older mutants (K5-H-pack-engine-files-unscanned, K5-H-pack-scripts-unscanned) had
  their find/replace moved to the new `scanned = ...` line (intent unchanged; a `note` field says so); both killed
  (M #7).
- Real sets (M #9): each of prepared-kt-dolly-olmo2 and -llama3 has 12 files, 8 listed (all present), 0 links;
  unlisted: .DS_Store (skipped) and manifest.json, manifest.sha256, prepare_receipt.json (scanned): **0 pattern hits**,
  so the new scan does not block the real pack. I did not hash the listed files (they include selector and hidden
  files); the real pack hashes them itself.

### Item 3. The 7 Nov ruling on item 23: the Mac-side C0_SOURCE check at pack time

- pack_setup.py: new `c0_source_check(src, digest, c0)`, called at the end of `sc_inputs` when the inputs record holds
  `source_complete:R:1101` (`C0_INPUT`). `sc_inputs` runs in both the real pack and the dry run (`sc_report`), so both
  refuse. It reads the file once, re-hashes those bytes against the pin, parses them, and refuses (input name only,
  never a value) when the JSON cannot be read, when `checkpoints.e1.adapter_fingerprint` is missing or not a SHA-256,
  or when it is not `C0_SOURCE[family]["e1_fingerprint"]`. Only that field is read. The refusal comes before
  `setup/packed-stage1-X/` exists, so no pod can be released from it (I: release reads only a packed receipt).
- The pod-side check (K5, setup/job_runner_stage1.py:517-541) is unchanged and still tested:
  `test_k5_d1_a_c0_pod_whose_c0_source_step_differs_from_the_packed_unit_runs_no_step` now makes the typo AFTER a clean
  pack (the Mac check would refuse it before), so it still proves the pod layer alone.
- Test: `test_k6_item23_the_pack_refuses_a_c0_source_whose_e1_fingerprint_is_not_c0_sources[typo, q-not-e1, no-e1,
  unreadable]`, each in the dry run and the real pack; the message names the input only (neither fingerprint in it);
  nothing packed. The right value packs (test_c0_and_o_only_with_test_local_oext_and_c0_pins, unchanged, passes).
- Mutants (scorer spec), all killed (M #5): K6-c0-pack-check-removed, K6-c0-pack-reads-q,
  K6-c0-pack-compares-complete-sha, K6-c0-pack-missing-fp-not-named, K6-c0-pack-unreadable-as-empty.
- README: the c0 bullet says the Mac check exists (round 6).

### Item 4. Specs, runners and suites
- Scorer spec 140 -> 155 (+15), gated 124 -> 128 (+4), runner 34 -> 35 (+1), rules 109 (unchanged). Added by
  SCR/add_mutants.py, which checks that each find text occurs exactly once (M #5). After the scan_anyway edit, a check of
  every mutant in all four specs: every find text occurs exactly once (M #7).
- All four runners, every mutant, under SBX (M #10, #11): **rules 109/109, runner 35/35, gated 128/128, scorer 155/155
  killed; 0 survived; 0 invalid in the final runs.** The first run of scorer 136-155 had 2 invalid (the two moved
  mutants, "find text occurs 0 times"); I fixed their find text and re-ran the whole chunk: 20/20 killed. Scorer chunks
  1-135 ran under the spec before that two-entry fix (spec SHA-256 d840590894f0...); M #11b: for all 135 of those
  entries, the before and mutated file hashes recorded by the runner equal those the final spec produces, so their
  mutations are byte-identical.
- 7-8B suite under SBX: **487 passed** (471 + 16 new) (M #14). runkit/stage1-olmo suite under SBX, unchanged files,
  engine-Y fixture copied into WS/tmp: **762 passed** (M #13).

## 3. Results in short

| Run | Result |
|---|---|
| 7-8B suite, SBX, before (HEAD) | 471 passed; basetemp 7 hf_token hits (M #1, #2) |
| 7-8B suite, SBX, after | **487 passed**; basetemp **0** hits (M #14) |
| runkit/stage1-olmo suite, SBX | **762 passed**; basetemp 0 hits (M #13, #14) |
| Rules runner ALL | 109/109 killed (M #10) |
| Runner runner ALL | 35/35 killed (M #10) |
| Gated runner, 3 chunks (1-40, 41-85, 86-128), SBX | 40 + 45 + 43 = 128/128 killed (M #10) |
| Scorer runner, 4 chunks (1-40, 41-95, 96-135, 136-155), SBX | 40 + 55 + 40 + 20 = 155/155 killed (M #10, #11) |
| New mutants alone (before the full runs) | scorer 15/15, gated 4/4, runner 1/1 killed (M #5, #6) |
| Flaky test at hash seeds 54, 868, 1027 | 3 passed (M #8) |
| Real prepared sets, the new scan | 3 unlisted files each scanned, 0 hits; .DS_Store skipped (M #9) |
| Token-shaped strings left: basetemps, WS kit, SCR | 0, 0, 0 (M #14, #15) |

## 4. Commands (all in the foreground, each under 10 minutes; exit status)

| # | Command (abbreviated; paths absolute in the runs) | Exit / result |
|---|---|---|
| 1 | `SBX PY -B -m pytest -p no:cacheprovider -q -x --basetemp SCR/bt-base runkit/stage1-78b/tests` (cwd WS, 11:45, before edits) | 0: 471 passed |
| 2 | `PY2 -B -I SCR/scan_left.py SCR/bt-base WS/runkit/stage1-78b/secret_scan.py` (scan_left.py copied from k5-verify-scratch) | 0: 7 hf_token hits, the 7 paths k5-verify named |
| 3 | reads: k5-verify.md, its scratch tests and hm_spec.json/hm_spec2.json, the rulings (part 2 design 7 Nov section), pack_setup.py, job_runner c0_fingerprint, rules_78b C0_SOURCE, prepare.py manifest code, the runners | 0 |
| 4 | after the edits: `SBX PY -B -m pytest ... --basetemp SCR/bt-1 runkit/stage1-78b/tests` (first run: 1 failed, the K5 D1 pod test, fixed as in item 3; then 487 passed); `scan_left.py SCR/bt-1` | 1, then 0: 487 passed; 0 hits |
| 5 | `PY2 -B -I SCR/add_mutants.py WS/runkit/stage1-78b <k5-verify hm_spec.json>`; `cd SCR; caffeinate -i SBX PY -B .../run_mutants_scorer_78b.py WS SCR/mr-scorer-new SCR/mr-scorer-new.json <15 new ids> --timeout 300` (11:55-11:58) | 0; 0: 15/15 killed, each in its intended test |
| 6 | the same with run_mutants_gated_78b.py (4 new ids) and run_mutants_runner_78b.py (1 new id) (11:58-11:59) | 0, 0: 4/4, 1/1 killed |
| 7 | PY2 edit of the two moved K5 mutants; a find-count check of every mutant in the four specs | 0: all exactly once |
| 8 | `PYTHONHASHSEED=s PY -B -I -S -c ...` for s in 0..1499 (old folder formula); then `PYTHONHASHSEED=s SBX PY -B -m pytest ... test_kit_78b_runner.py -k free_space_check_refuses` for s in 54, 868, 1027 | 0: seeds 868, 1027 collide; 0, 0, 0: 1 passed each |
| 9 | `PY2 -B -I SCR/real_prepared_names.py /Users/spiderishi/Coding/attribution WS/runkit/stage1-78b/secret_scan.py` | 0: per folder 12 files, 8 listed, manifest at both pins, unlisted = .DS_Store + 3 scanned, 0 hits |
| 10 | `SCR/run_chunk.sh <runner> <spec> A B TAG` (caffeinate -i SBX PY -B runner WS SCR/runs/TAG SCR/runs/TAG.json <ids> --timeout 300): rules 1-109 (12:00-12:01), runner 1-35 (12:01-12:02), gated 1-40 (12:02-12:04), 41-85 (12:04-12:08), 86-128 (12:08-12:12), scorer 1-40 (12:12-12:13), 41-95 (12:13-12:18), 96-135 (12:18-12:23), 136-155 (12:23-12:26) | 0 each, except scorer 136-155: 1 (18 killed, 2 invalid) |
| 11 | scorer 136-155 again after #7 (12:27-12:30); the first result kept as SCR/runs/scorer-136-155-first.json | 0: 20/20 killed |
| 11b | PY2: recompute before/mutated hashes of scorer entries 1-135 under the final spec vs the recorded ones | 0: 135 same, 0 differ |
| 12 | `git --no-optional-locks status --short [--ignored] runkit/`; `git --no-optional-locks diff --stat HEAD`; `shasum -a 256` of the 9 files | 0: 9 modified files only |
| 13 | `cp -Rp /Users/spiderishi/Coding/attribution/tmp/engine-y-34bfd288 WS/tmp/`; `git check-ignore`; `SBX PY -B -m pytest ... --basetemp SCR/bt-olmo runkit/stage1-olmo/tests` (12:31) | 0; ignored; **0: 762 passed** |
| 14 | `SBX PY -B -m pytest ... --basetemp SCR/bt-final runkit/stage1-78b/tests` (12:32); scan_left.py on SCR/bt-final, SCR/bt-olmo, WS/runkit/stage1-78b | **0: 487 passed**; 0, 0, 0 hits |
| 15 | `rm -rf` of SCR's basetemps and runner copies (results JSON kept); scan_left.py on SCR | 0; 0 hits (SCR now 444 KB) |

## 5. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| V1-V5 adopted; each kills its survivor | passed | M #5, #6 |
| K5v-2: the tests remove every token-shaped file; basetemp re-scan 0 hits | passed | M #2 (7 before), #14 (0 after) |
| K5v-6: the edits/ scan pinned at the call site by a spy; K5v-R4-call-site-skips-edits killed | passed | M #5 |
| K5v-9: flaky folder names fixed | passed (seeds 54, 868, 1027 pass; the collision mutant is killed) | M #6, #8 |
| K5v-3: unlisted data/ files scanned, macOS metadata skipped by name, listed files outside the scan; README and docstring say so; planted-token test | passed (with choices (a), (b) for the lead) | M #4, #5, #9 |
| Item 23: Mac-side C0_SOURCE check at pack time, before any pod; a test | passed | M #5 |
| Every new mutant in the specs and killed | passed: 20 new (15 scorer, 4 gated, 1 runner) | M #5, #6, #10, #11 |
| All four runners pass (chunked; gated and guard mutants under SBX) | passed: 109, 35, 128, 155 killed; 0 survived; 0 invalid in final runs | M #10, #11, #11b |
| Whole 7-8B suite under SBX | passed: 487 | M #14 |
| runkit/stage1-olmo unchanged, its suite passes | passed: no diff; 762 | M #12, #13 |
| No token-shaped file left behind | passed: 0 in both basetemps, the WS kit and SCR | M #14, #15 |
| CUDA, a real pod, a real pack | not tested | $0 scope |

## 6. Jobs for the lead

1. Merge by explicit paths the 9 files of section 1 (SHA-256 listed). No other file.
2. Confirm or change the two readings in item 2: (a) macOS metadata files are not packed at all; (b) a listed file
   stays outside the scan only at its hash and while manifest.json is at the pin.
3. Re-verify commands (each under 10 min here; split further on a busier machine), cwd any, SCR2 a new folder:
   `PYTHONDONTWRITEBYTECODE=1 SBX PY -B -m pytest -p no:cacheprovider -q --basetemp SCR2/bt runkit/stage1-78b/tests`
   (expect 487) and the four runners with `caffeinate -i SBX PY -B runkit/stage1-78b/tests/run_mutants_<k>.py <repo>
   SCR2/<tag> SCR2/<tag>.json <ids> --timeout 300`: rules ALL (0.5 min), runner ALL (1 min), gated 1-40, 41-85, 86-128
   (1.9, 3.7, 3.9 min), scorer 1-40, 41-95, 96-135, 136-155 (0.9, 4.4, 4.7, 3.3 min). SCR/ids.py prints an id slice;
   SCR/run_chunk.sh is the exact wrapper I used.
4. WS/tmp/engine-y-34bfd288 (67 MB, a copy of the main checkout's fixture) stays for the re-verifier's 1B suite run;
   delete it after review. SCR (444 KB) can go after review.

## 7. Unresolved concerns

1. Item 2's two readings (job 2). If the lead wants the literal "skip the scan only", K6-macos-metadata-packed becomes
   the intended code and its test line must change.
2. The pack still checks only manifest.sha256's text, not manifest.json's bytes, against the pin (R: pack_setup.py
   `prepared_set`). Under my rule an off-pin manifest.json only widens the scan. A pack-time refusal would need the
   synthetic worlds to hold a manifest.json at the pin; the pod's engine refuses an off-pin manifest anyway (R:
   prepare.py:877-886).
3. K5v-2 has no mutant: no test can see from inside the run that a file was left. The evidence is the basetemp scan.
   A session-end scan inside the suite would turn a leak into an ERROR (which the runners treat as invalid), so I did
   not add one.
4. My seed sweep finds 2 colliding seeds (868, 1027), k5-verify found 5 (incl. 54). I did not find the reason. The fix
   removes the hash from the names, so it does not depend on the count.
5. `c0_source_check` re-hashes the bytes it parses (a second check after `sc_inputs`' own hash). A mutant that drops
   that re-hash would survive (equivalent in effect within one pack run; I did not add it).
6. A test's finalizer cannot run if the Python process is killed (for example a runner timeout). A token-shaped file
   could then stay in that run's basetemp; the runners delete their basetemps after each run (R:
   run_mutants_scorer_78b.py `run_suite`, `shutil.rmtree`).
