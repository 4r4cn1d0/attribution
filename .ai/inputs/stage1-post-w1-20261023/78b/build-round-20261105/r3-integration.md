# R3 integration review (K3 + Track P seams)

Started 2026-11-10 04:34 UTC, written 05:06 UTC (clock read with `date -u`). Target WS = B/ws-r3m (d7eb772 + K3 final
+ Track P final), read only. All probes and suites ran in a scratch copy C = R/r3-integration-scratch/wsc (`cp -pR WS`,
`.git` removed). No git state change, no network, pod, install, download, agent or message. No forbidden folder or
sealed file opened. Every test input is synthetic; from settings and printouts I read paths and hashes only.

## Status

**Done.** All seven items checked. Verdict: **VERIFIED_WITH_MINOR**. Nothing breaks when the two tracks run together
on the [B] route. Five findings, none major:
- I-1: under [C], Track P's printed `W1_18_78B` is refused by K3's R-60 check, and the maker cannot print a form that
  [C] accepts.
- I-2: no reader ever checks `Y_MEASURED_RECORD` at its pin.
- I-3 and I-4: two seam mutants survive the whole merged kit suite.
- I-5 (nit): the maker's W1-18 record-path check is looser than RK's.

## Findings

| id | severity | R: where (WS) | what | evidence | fix |
|---|---|---|---|---|---|
| I-1 | minor | scripts/scale78b/make_oext_settings_78b.py:467-484 (`w1_18_78b_form`, `for family in FAMILIES` at :474); runkit/stage1-78b/plan_tool.py:1301-1316 (`w1_18_gate_families`, :1312); rules_78b.py:1719-1724 (`w1_18_route_problem`'s index rule) | Under [C], the maker's `--w1-18-78b` printout is refused by R-60. The printout always holds both families' side units and both families' W1 index and settings, but R-60 needs exactly GATE_78B's families. The maker has no family option. A [C] fill needs a two-part hand edit: remove Llama's side units, and also Llama's W1 index and settings files, because RK refuses an index whose family has no side units. R-20 and R-32 say the lead fills the maker's printed form. Under [C] that form is unusable, so W1-18 under [C] cannot be planned from the maker's output. It fails closed, at $0, on the Mac | M: probe `test_zz_int_w118.py` on the real printout from C (`R/r3-integration-scratch/w1_18_78b_printed.json`; θ0's waiting job pins set to the printout's, R-20): [B] passes R-60; [C] gives "W1_18_78B's side units ['llama31-8b', 'olmo2-7b'] are not GATE_78B's families ['olmo2-7b'] (GXB R-60)". With side units pruned only, RK says "its files name the O-ext index file(s) [both]; exactly … olmo2-7b.json". With Llama's two settings files also pruned, RK says None. K3's [C] tests use hand-written routes (test_runner_ab_78b.py:304 `w1_route`, :1178) | Give `--w1-18-78b` a `--families F[,F]` option (GATE_78B's families), so that side units and the per-family files hold only those families. Add a test: the [C] printout passes RK and `w1_18_gate_families` under a [C] gate. Track P's file: a lead decision for the fix round. Or document the hand edit as the recorded step (not recommended) |
| I-2 | minor | runkit/stage1-78b/rules_78b.py:548 (`engine_allowed`), :2758 (`y_measured_or_refuse`) | Measured kinds may run on Y once `Y_MEASURED is True and Y_MEASURED_RECORD is not None`. Nothing reads the record at that pin: `y_measured_or_refuse` has no caller outside tests. A pin to a missing or changed file passes. The other recorded pins (GATE_78B, ANCHOR_STOP, PADDED_TOKENS_78B) are read and checked at their pins. Latent today, because no block A or B measured kind is planned on Y | R: `grep -rn y_measured_or_refuse runkit/stage1-78b/*.py runkit/stage1-78b/setup/*.py` finds only the definition. R: test_runner_ab_78b.py:726-727: with `Y_MEASURED_RECORD` = {"records/y-measured.json", `hx("ymr")`} (no such file), `engine_allowed("arm", Y)` is True | Before any measured job is planned or released on Y (plan_tool, on the Mac), read the pin with `pin_bytes` and `y_measured_or_refuse`. Add a test that a missing or changed record refuses |
| I-3 | minor | runkit/stage1-78b/orchestrate.py:260-263 (`check_plan`'s "not packed" check) | No test holds the Mac check-plan's refusal of an edit arm job whose `edits/<SHA>.edit.json` is missing from sealed-files.json. The R-75 tests check `a0_arm` only (test_runner_ab_78b.py:1345-1362) | M: mutant INT-1 (`if rel not in doc["files"] and not rel.startswith("edits/")`) **survived** the runner spec's command (r1.json) and the whole merged kit suite (670 passed, `mut/INT-1-…-whole.log`). My probe `test_zz_int_checkplan.py` kills it (1 failed, `…-probe.log`) | Add a check_plan test on a packed block-A edit arm host (the probe's form) and mutant INT-1 to mutation_spec_runner_78b.json |
| I-4 | minor | runkit/stage1-78b/pack_setup.py:782 (`ab_edits`: released hosts) | No test holds that the A/B pack takes the released hosts' edits, which are the first launch's pods. K3's pack tests write a plan with pending hosts only (test_runner_ab_78b.py `ab_pack`) | M: mutant INT-2 (`hosts = []`) **survived** the runner command and the whole merged kit suite (670 passed). The probe kills it: check-plan then refuses the released hosts | Add the probe's test (init-block A, pack, check-plan on every released host) and mutant INT-2 |
| I-5 | nit | scripts/scale78b/make_oext_settings_78b.py:216 (`check_w1_18_pin`) vs rules_78b.py:1442 (`W1_18_RECORD_RE`) and plan_tool.py:4787-4799 | The maker takes any `.json` W1-18 record path under the R-21 folder. RK and record-branch-78b take only `overrefusal_checks__<F>.json` (R-53). A record committed under another name is refused later, at the OEXT_78B or BRANCH fill. It fails closed. This code predates this round | R (lines named) | Make the maker's check RK's exact name (`W1_18_RECORD_RE`). Optional |

## Suite counts (M)

C was compared with WS by the sorted per-file SHA-256 list: equal (`76d22e35…`, 7,399 files). I copied
MAIN/tmp/kt-prepared (48 files, list `324c5dcd…`) and MAIN/tmp/engine-y-34bfd288 (3,848 files, list `389c9ecc…`) into
C/tmp with `cp -pR`. Their lists are equal on both sides.

| suite | result | exit | log |
|---|---|---|---|
| 7-8B kit (sandboxed) | 670 passed | 0 | `suite-78b.log` |
| scale78b (sandboxed) | 780 passed, 3 skipped | 0 | `suite-scale78b.log` |
| stage-1 kit (sandboxed) | 762 passed | 0 | `suite-olmo.log` |
| engine family tests (sandboxed) | 95 passed | 0 | `suite-family.log` |

The 670 includes K3's last pass; K3 reports 670 (lp-78b.log). scale78b shows one more skip than Track P's 781/2: test_refs_78b_settings.py:430 needs `.git`, and C has none. I ran its git check by hand in WS with `git --no-optional-locks -C WS diff --stat -- scripts/stage1 scripts/stage1_s1 runkit/stage1-olmo experiments`: the output is empty. **No failure.**

## Items

1. **Merged suites:** no failure (above).
2. **W1-18's files list:** passed for [B]; I-1 for [C].
   - M: Track P's real printout in C (`make_oext_settings_78b.py --w1-18-78b`, exit 0) has 10 files, both readers
     among them (`scripts/family_probe_reading.py` `8848340107bd…`, `scripts/killtest_stage0_reading.py` `1740663bc9e4…`),
     and side units for both families.
   - RK's `w1_18_route_problem` gives None once θ0's waiting job pins are set to the printout's values (R-20).
   - K3's runner `sealed_paths` lists both readers. `job_commands` under `mac_build` builds one W1-18 command per
     family, host family first (probe test_zz_int_w118.py).
   - The runner's command does not name the readers. On the pod they are read by the unchanged
     `overrefusal_checks.py`, through `limits_common.frozen_reader`, at `ENGINE_ROOT/<path>` and their pins
     (R: scripts/stage1/limits/overrefusal_checks.py:415, limits_common.py:71-97). They are packed at those paths
     (R: pack_setup.py:754 packs every `route["files"]`).
   - The wrapper allows `--guard-batch-size` for w1_18 (R: oext_78b.py:157). Both MAIN_F configs carry
     `guard.batch_size` (M: 8 and 8).
3. **The padded-tokens record:** passed (M; probe test_zz_int_padded.py, 3 passed).
   - Track P's tool (`pt.main` on Track P's own fixtures) writes one record over 16 synthetic engine edits. These are
     R_d4-R_d13, A1, L1, H1, S1, S3 and S4, with RK's pins pointed at them. `source` is an object.
   - `PADDED_TOKENS_78B[F]` pins the tool's bytes. init-block A and init-block B (dry run; B after b_ready, with A
     sealed) accept it.
   - Every planned edit job's `padded_tokens_per_step` is the record's value, looked up by edit SHA-256, and
     `train_scale` = max(1, value / basis). With the basis lowered, the caps rise (B: 99.25 h -> 102.75 h; arm pods
     only).
   - R-57: the record at `.ai/inputs/stage1-post-w1-20261023/78b/padded-tokens/padded_tokens__<F>.json` is read by
     init-block A. The tool refuses while that folder does not exist (exit 2, nothing written). The lead must make
     the folder first, as Track P's "<OUT_DIR> must exist" says.
4. **The shared anchor-stop fixture:** passed (M; probe test_zz_int_stop.py, 1 passed).
   - The shared fixture (`96005b31…`, unchanged since d7eb772) is read by K3's runner `anchor_stop_check` ->
     `anchor_stop_or_refuse` on a pod tree. The pod tree holds the JOB-DONE.json that K2's writer test derives the
     fixture from. `family_stopped` is true afterwards, and a wrong JOB-DONE refuses.
   - Track S's `check_anchor_stop` takes the fixture.
   - RK's checker, K2's writer form and Track S's reader were already held by test_kr5_… (kit) and
     test_track_s_stop_fixture_is_the_shared_form (scale78b).
5. **check-plan on the Mac:** passed (M; probe test_zz_int_checkplan.py, 1 passed); see I-3 and I-4.
   - I ran a real init-block A (6 hosts: A1, L1, H1, S1, S3, S4, R, a0), then K3's real pack (engine code faked as
     in K3's `ab_pack`; 19 sealed files).
   - `orchestrate.check_plan` passes on every released host with HERE/hosts/HOST empty, and refuses when an edit is
     cut from sealed-files.json.
   - K3's R-75 tests cover a0_arm (A, B), o_only, o_only_with_regenerate, c0, W1-18 and the four reference kinds.
     ref_train_bqi (engine Y) has no Mac check-plan test. I did not probe it (usage).
6. **Pin fill procedures:**
   - R-21: record-branch-78b needs exactly RK's path. Track P's longer `W1_18_78B` keeps
     `files["…/limits_overrefusal_checks__F.json"]`, which record-branch reads (R: plan_tool.py:4804-4805). Nit I-5.
   - R-57: passed (item 3).
   - `REFS_78B`: Track R's printouts in C (`--refs-78b olmo2-7b 1102`, `olmo2-7b 1104`, `llama31-8b 1103`, exit 0)
     each give None through RK's `refs_form_problem`. They include Track P's new `oext_78b.py` hash (`e869b629…`).
     The pack refuses a path pinned twice at two hashes (R: pack_setup.py:121-122). So an OEXT_78B / REFS_78B
     settings clash fails closed on the Mac.
   - `Y_MEASURED_RECORD`: no reader (I-2).
   - `PADDED_TOKENS_78B`: passed (item 3).
7. **Earlier rounds' contracts:** passed.
   - test_42 (block 0's plan.json byte for byte) passes (M: `-k test_42`, 1 passed). It covers block 0 only.
   - The scorer block's plan.json changes in one place only: the `w1_18` job gains `families` (R-60, intended; R:
     the plan_tool.py diff hunk at :1296). The new `engine_sha256: None` path for Y hosts (plan_tool.py:1688) is not
     reached by the scorer block, because `sc_needed_pins` adds ENGINE_Y for Y jobs (R: rules_78b.py:1567-1574).
   - R-53 holds: RK's W1_18_RECORD_NAME is `overrefusal_checks__{family}.json` (rules_78b.py:1441). K3's runner
     returns `job-I/overrefusal_checks__<F>.json` (test_5c, in the passing suite). Track P's maker folder matches
     (make_oext_settings_78b.py:70).
   - R-72: `encode_count_78b.py` is at its d7eb772 bytes (`132dcd5b…`; M: `git diff --quiet`).

## Mutants (M)

INT-1 and INT-2 are appended to the copy's runner spec (C only). Runner command:
`sandbox-exec -p "$SB" $PY -B C/runkit/stage1-78b/tests/run_mutants_runner_78b.py C R/…/mut/r1 R/…/mut/r1.json INT-1-checkplan-skips-unpacked-edits,INT-2-pack-skips-released-hosts-edits`.
Baseline exit 0. Both **survived**, 0 invalid (05:01-05:02 UTC).

The same two mutants against the whole merged kit suite (my probes ignored): baseline 670 passed. Each mutant 670
passed (survived). Each is killed by `test_zz_int_checkplan.py` (a real FAILED line, no ERROR). The copy's bytes were
restored after each mutant (orchestrate.py `52402f80…`, pack_setup.py `208d8d45…`, as before).

Spec entries for the lead (file relative to runkit/stage1-78b):
```json
{"id": "INT-1-checkplan-skips-unpacked-edits", "file": "orchestrate.py",
 "find": "                   if rel not in doc[\"files\"]]\n",
 "replace": "                   if rel not in doc[\"files\"] and not rel.startswith(\"edits/\")]\n"},
{"id": "INT-2-pack-skips-released-hosts-edits", "file": "pack_setup.py",
 "find": "    hosts = [h for h in plan.get(\"hosts\", {}).values() if h.get(\"block\") == rules.KIT_BLOCK]\n",
 "replace": "    hosts = []\n"}
```

## Commands for the lead (after a fix round adds the tests)
```
SB='(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'
sandbox-exec -p "$SB" $PY -B runkit/stage1-78b/tests/run_mutants_runner_78b.py "$PWD" <SCRATCH> <OUT.json> INT-1-checkplan-skips-unpacked-edits,INT-2-pack-skips-released-hosts-edits
# probes (copy into a WS copy's runkit/stage1-78b/tests/, then):
sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests/test_zz_int_padded.py runkit/stage1-78b/tests/test_zz_int_stop.py runkit/stage1-78b/tests/test_zz_int_checkplan.py runkit/stage1-78b/tests/test_zz_int_w118.py
# (test_zz_int_w118 reads ZZ_W118_PRINTED = a `make_oext_settings_78b.py --w1-18-78b` printout; its [C] case fails today: I-1)
```

## Commands run (all foreground, sandboxed unless noted)
- `cp -pR` of WS and the two tmp folders, then the hash lists (equal).
- The four suites (exit 0 each).
- The hand git check (`git --no-optional-locks diff --stat`, read only): empty.
- `make_oext_settings_78b.py --w1-18-78b` (exit 0) and `make_refs_settings_78b.py --refs-78b` ×3 (exit 0), in C.
- Probes: padded 3 passed; stop 1 passed; check-plan 1 passed; w118 2 passed + 1 failed (the I-1 case, expected).
- An early collection error from w118's missing environment variable: fixed by a default path, then re-run.
- `-k test_42`: 1 passed.
- The runner on INT-1 and INT-2: exit 1 (survivors). The whole-suite runs per mutant: exit 0 (survived). The probe runs
  per mutant: exit 1 (killed).

## Evidence files (R/r3-integration-scratch/)
- probes/test_zz_int_padded.py `c25ac6b0…`, probes/test_zz_int_stop.py `68898add…`,
  probes/test_zz_int_checkplan.py `40cf1f4c…`, probes/test_zz_int_w118.py `f57499d5…`, mut/apply.py `89a1e9e4…`.
- Logs: suite-*.log, mut/r1.json, mut/r1.log, mut/*-whole.log, mut/*-probe.log.
- Printouts (paths and hashes only): w1_18_78b_printed.json, refs_*.json.
- The copy C (wsc, with the tmp copies) and mut/r1's repo are deleted after this report.

## Open points for the lead
1. I-1: how [C] fills `W1_18_78B`. Either a maker option (Track P's file), or an accepted hand edit as the recorded
   step.
2. I-2: where the `Y_MEASURED_RECORD` read belongs (planning or release on the Mac) before Y carries a measured kind.
3. Not probed (usage): check-plan for `ref_train_bqi` on engine Y, and block B's real pack + check-plan with
   references released.

## Concerns
- My probes import the kit's test modules (test_planning_ab_78b, test_runner_ab_78b) and reuse their fixtures. A
  change to those helpers can break the probes without any change in the code under test.
