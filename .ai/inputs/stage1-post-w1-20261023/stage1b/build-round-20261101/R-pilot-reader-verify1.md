# R-pilot-reader: verification 1 (adversarial check of the stage-1b pilot reader)

Written 2026-11-01, 22:43-23:05 UTC (`date -u` at the start and at the end). Verifier: a bounded worker; read-only
on every source. The builder's workspace: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/s1b/ws-r`
(HEAD `0d25497e2d241cff48944720671d4a87c0456b9b`; `git status --porcelain`: only `?? scripts/stage1_s1/pilot_gate/`,
M). The builder's report: `.../scratchpad/s1b/reports/R-pilot-reader-build.md`. My code and run records:
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/s1b/verify-R-pilot-reader/`
(`my_paired.py` `203a29ef…`, `my_label_grid.py` `5fa1fa88…`, `my_blind_attack.py` `5b5c3611…`,
`mutation-shard-verify1.json` `dfb0d031…`). Tags: (R) read in a source; (M) measured here; (I) my inference.

## Verdict: **verified** (no defect that matters for correctness, the frozen rules, section 40 or blinding)

The reader computes Lambda_plant, SE, df, t and the one-sided 90% lower bound exactly as REV4:675 and addendum
section 40 points 1-2 rule (B16's `contrast_paired` with c = a0_plant and m = Gate A's a0, the item part on, the
Satterthwaite df, B16's t quantile); my from-scratch exact-rational recomputation agrees to 1e-9 pp on 41 synthetic
tables; the label agrees with an independent statement of point 1 on 53,410 grid points and on 299 count tables whose
three-seed mean is exactly 10 or 5 pp as a rational; the re-pilot mode never raises; the Gate A pins are checked;
B16 and the input builder are byte-identical to `0d25497`; B16's pins equal both `0d25497`'s hashes and the stamped
manifest's; on every path I could reach (27 in process, 5 as a subprocess) no sentinel from a unit file reached
stdout, stderr, a traceback or the output. The suite passes (89) and 10 of 10 mutants are killed after a passing
baseline. Notes N1-N9 below are minor; N1 is a false claim in the build report with a one-line hardening the lead
may want before freezing the reader by hash (it is not a leak path in the real kit).

## 1. What was checked, against what

| Check | Source of the rule | Result |
|---|---|---|
| New files only; no file of B16, the input builder, `scripts/stage1`, the kit or the engine changed | brief; D-5 | `git diff --stat 0d25497 -- scripts/stage1_s1/reading scripts/stage1_s1/reading_input scripts/stage1 runkit experiments`: empty; `git status --porcelain` on those paths: empty (M) |
| The 11 files' SHA-256 equal the build report's table | report §1 | all 11 equal (M, `shasum -a 256`) |
| No "plant"/"decoy" in any code path or file name | section 40 point 3 (names); CHECK B6 | `find … \| grep -i "plant\|decoy"`: none (M); the arm names are string constants only |
| Lambda_plant = `contrast_paired(table, "a0_plant", "a0", (1101, 1102, 1103), 100, with_item=True)` | section 40 point 1; CHECK 1.2 point 5; contrast.py:168-173 | `gate.estimate` (R); the sign asserted on 41 tables (M); mutant `PG-gate-sign` killed (M) |
| SE, df: paired variance ddof 1 over J = 3 with 2 df plus the crossed item part, Satterthwaite; no fallback | section 40 point 2; REV4:675 | only `contrast_paired(..., True, ...)` exists in the reader (R); `seed_only` appears only in a test that shows the fallback would mislead (R); mutant `PG-gate-no-item-part` killed (M) |
| Lower bound = Lambda - t(0.90, df) x SE with B16's `tdist.t_quantile` | section 40 point 2 | `gate.lower_bound` (R); t(0.90, 2) = 1.8856180832 = mpmath's (M) |
| Label: go if Lambda >= 10 and lower > 5; raise if 5 <= Lambda < 10; stop otherwise, Lambda >= 10 with lower <= 5 included | section 40 point 1 | `gate.label`/`gate.reads` (R); grid and tables below (M) |
| Lambda's comparisons through B16's tie tolerance in B16's own form; the bound exact | section 40 point 1 edges; B16 labels.py:55-68, README:153-155 | `at_least` is `value >= bar - tol`, labels.u_part's form (B16 has no standalone function; R); `lower_pp > 5.0` exact (R); `tie_tolerance()` is B16's (settings `margin.tie_tolerance_pp` = 1e-9, M) |
| Re-pilot: a0_plant75 at the same seeds against the same Gate A units; the go test only, else stop | section 40 point 1 "Raise" | `ARM_OF`, `label(..., "re-pilot")` (R); 0 "raise" on the grid in re-pilot mode (M) |
| Gate A's a0 through `REJUDGED_PINS["A"]`, names "a0 1101 (Gate A)" etc., COMPLETE.json and job.json pins checked | brief (1); RULES:183-195 | `gate_a_unit`: exactly one pin by name with arm a0, the seed, target e1; `pinned_folder` (both hashes); `_check_job_json(pinned=True)` for arm, seed, checkpoint (R), the builder's own `_reused_cell` form (build.py:322-327, R) |
| Pilot units by key from the kit's records | brief (1); the builder's `scan`/`_primary_jobs` | `block_jobs`/`pilot_unit` mirror `scan` (status complete, `pulled is False` excluded) and `record_done` (`done`, `unit`, `complete_sha256`: plan_tool.py:3562-3625, R); the sealed edit record's entry is `{path, sha256, source}` with no `engine_arm` (plan_tool `edit_sources`, R), and the runner's pack check binds `engine_arm == "edit-" + sha(edit file)` (job_runner_stage1.py:674, R), so the reader's `edit-<sha256>` form is the engine arm |
| Per-prompt U as the stage-1 builder builds it | brief (2) | `items.harm` imported on the same three files the builder's `_eval_items` reads (build.py:185-190, R); U = the Unsafe share, checked against summary.json's counts, 3 answers per prompt (items.py:96-145, R); the six units must share one sorted id set of B16's 200 (R); nothing copied, so no equality test was needed |
| B16's pins | brief (6) | `B16_PINS` == SHA-256 of `git show 0d25497:scripts/stage1_s1/reading/<f>` for all 14 (M); == the stamped manifest `reading/timestamp/ots-manifest-reading-20261101.json` `files[...]` by key for all 14 (M, key-only read); B16 unchanged between `55d5f8b` and `0d25497` (only reading_input files differ in `git diff --stat 55d5f8b 0d25497`, M); checked before any unit is read (R; the test `test_b16_pins_are_checked_before_any_unit_is_read`) |
| Output: canonical JSON, exclusive create, the fields of brief (6) | brief (6) | `__main__.document`/`main` (R); re-run byte-identical and never overwrites (the builder's test, passed) |

## 2. The recomputation from first principles (M)

`my_paired.py`: exact `fractions.Fraction` arithmetic for the estimate, the seed part, the two-way mean squares
of the 3 x 200 difference table, V_item, q and the Satterthwaite df; the t quantile by bisection in mpmath (30 digits)
on the regularized incomplete beta, an implementation independent of B16's `tdist`; 40 random synthetic count
tables of five kinds (independent noise; a shared prompt effect; rows constant over prompts; a plant that raises U
by 5-15 pp; near-identical seeds) plus section 40 point 2's constructed case rebuilt from its description. Against
`gate.read(table, "pilot")` from the builder's workspace:

- 40 tables compared (25 with a non-zero item part; 1 refused by both forms for zero variance information);
  worst |difference|: Lambda 9.6e-15 pp, SE 4.2e-15 pp, lower bound 1.1e-11 pp, df 6.3e-15 relative, t 5.9e-13.
- The labels agree on every table (24 stop, 8 go, 8 raise) with my independent statement of point 1.
- B16's `t_quantile` against mpmath on a df grid (2 … 1e5) at p = 0.90, 0.95, 0.975: worst |difference| 8.8e-11.
- The constructed case: Lambda 11.3333 pp, SE 5.1042 pp, df 199.04, lower bound 4.7703 pp, "stop" (both forms);
  the addendum's own table (SE 5.10, df 198.5, lower 4.78) is a near neighbour, not this exact table (N9).
- The item-part-0 kind: df 2.0, t 1.885618 (both).

## 3. The label on a grid and on exact shares (M)

`my_label_grid.py`: 53,410 (Lambda, lower bound, mode) points: Lambda at 5 and 10 pp +- {0, 1e-16 … 5} and every
rational k/18 pp from 0 to 15 pp formed three ways in floating point; the lower bound at 5 pp +- the same offsets
and +- 1 ulp. 0 mismatches against my independent rule; 0 "raise" in re-pilot mode; every `reads` field equal to
its definition. Named edges: Lambda 10 - 1e-15 with lower 6 -> go; with lower exactly 5.0 -> stop; Lambda 10 - 2e-9
-> raise; Lambda 5 - 1e-15 -> raise; 5 - 2e-9 -> stop; lower 5 + 1 ulp -> go, 5 - 1 ulp -> stop (no tolerance on the
bound); re-pilot never raises. Then 299 real count tables whose three-seed mean is exactly 10 pp (150) or 5 pp
(149) as a rational: all read as at least the bar with the right word (at 10: go or stop by the bound, never
raise; at 5: raise), although 46 of 150 and 44 of 149 land below the bar in floating point (EV2:179's effect
reproduced); one answer fewer (1/18 pp) read below the bar in all 299; one answer more read at least the bar in all.
One of the 300 generated tables had zero variance information and was refused by B16 (N2).

## 4. Blinding (M; `my_blind_attack.py`)

The builder's synthetic world (every non-U field a sentinel) plus 13 sentinels of my own in places the builder's
tests did not put one: a host name, a repeated JSON key, a prompt id, a file name listed by COMPLETE.json, the rules
module, a seal path, a unit path, summary counts, an error message, job.json bytes, a guard record, a job-list entry,
an edit path. 27 cases in process (stdout, stderr and the output file captured) and 5 as `python -m
scripts.stage1_s1.pilot_gate` subprocesses. Every refusal was one fixed line; no traceback anywhere; no sentinel
from any unit file reached any stream or the output. Paths reached: success; a not-done host; a done host with no
complete job; a float seed (1101.0: read as 1101); a duplicate (message "a0_plant 1101.0: two complete units", a
design value only); a unit path with a sentinel; COMPLETE.json listing a sentinel-named extra file (success, the
name is not written); COMPLETE.json with a repeated sentinel key (strict_json's refusal names the key, withheld by
`_step`); COMPLETE.json nested 100,000 deep ("an unexpected RecursionError", withheld); job.json not UTF-8;
a sentinel prompt id in one unit ("the six units do not hold one set of harm prompt ids"); a guard record that is a
list; sentinel summary counts; the rules module raising at import; the bars file missing; a seal entry with a
sentinel path (only its SHA-256 written); a renamed Gate A pin plus an extra sentinel pin; an edit SHA-256 that
differs from job.json's arm; summary.json listed under a wrong hash; a string job entry (skipped, N8); the kit
folder missing; the output folder missing ("an unexpected FileNotFoundError", N6); the output path a folder.

**The one thing that reached the output:** the *name* of a not-done host of block P, taken from plan.json's
`hosts` keys, is written to `inputs.hosts_not_done` without the plain-name check (N1).

## 5. Suite and mutants (M)

- `PYTHONDONTWRITEBYTECODE=1 <venv> -B -m pytest -q -p no:cacheprovider -rs -W ignore --basetemp=<fresh folder under
  …/scratchpad/s1b/tmp/> scripts/stage1_s1/pilot_gate/tests` (cwd the workspace): **89 passed in 1.88 s**, no skip
  (so `test_b16_pins_equal_the_stamped_manifest` and `test_the_rule_quotes_rev4_675` ran). Basetemp deleted.
- `scripts/stage1_s1/pilot_gate/mutation/run_mutants.py --spec … --scratch <…/s1b/tmp/vr-mut> --report
  …/verify-R-pilot-reader/mutation-shard-verify1.json --timeout 300 --only PG-gate-sign,PG-gate-no-item-part,
  PG-gate-bound-not-strict,PG-gate-no-tolerance,PG-gate-repilot-raise,PG-gate-go-no-bound,PG-units-withheld-refusal,
  PG-units-complete-sha,PG-units-pin-name,PG-main-overwrite`: baseline pass (89 tests, exit 0); **10 killed, 0
  survived, 0 invalid**; exit 0; about 30 s. Scratch deleted. The report holds ids, outcomes, counts and hashes only.
- The runner is the reading-time readers' runner with its tree name changed (9 hunks, all the tree name; `diff`, M).
  The spec: 60 entries, one per refusal and rule edge as the brief asks, one documented expected survivor.

## 6. Notes (minor; none changes the verdict)

- **N1 (a false claim in the build report; a one-line hardening).** Report §4 says "the host name is checked against
  a plain-name pattern … before either is written to the output" and "Nothing from plan.json is printed". For the
  done host this holds (`pilot_unit` -> `_host_name`). For a host of the block that is *not* done, `_plain_hosts`
  appends plan.json's host key unchecked and `read_units` writes the list to `inputs.hosts_not_done`.
  *Reproduction:* in a synthetic world add `plan["hosts"]["VSENT-HOSTNAME-k3z9"] = {"block": "P", "done": false,
  "jobs": []}`; run `python -m scripts.stage1_s1.pilot_gate --mode pilot --kit <w>/kit --repo <w>/repo --rules
  <w>/repo/rules.py --out o.json`. Expected by the report: refused, or the name checked; actual: exit 0 and
  `"hosts_not_done": ["VSENT-HOSTNAME-k3z9"]` in o.json (in process and as a subprocess, M). *Why it is not a leak:*
  the kit names hosts `<HOST_PREFIX[block]>-<n>` (plan_tool.py:945, R), so a real name is "p-2"-like and cannot carry
  the leaf; a host name is a plan.json field, not a unit field, so section 40 point 3's rule is not touched.
  *Fix if the lead wants the code to match its text:* `not_done.append(_host_name(name))` in `units._plain_hosts`
  (refuse a non-plain name with the existing fixed message), or record `len(not_done)` only; then re-run the suite
  and the mutant `PG-units-not-done`. Either changes `units.py`'s hash, so it must come before the freeze (section
  40 point 12).
- **N2 (inherited B16 refusal).** A table with zero variance information (the three paired cell differences exactly
  equal and MS_P <= MS_E) makes B16's `_assemble` refuse ("no finite degrees of freedom"); the reader then writes no
  label. This is B16's own named refusal, consistent with "no fallback"; on real 600-answer cells it needs three
  exactly equal seed differences and no prompt effect, which I take as negligible (I). The lead should know the
  message is B16's and holds code constants only.
- **N3.** The rules module is executed at import (`load_rules`, the builder's practice); anything it prints at import
  reaches stdout uncaptured (M, with a synthetic module). It is the kit's reviewed code, not a unit; recorded only.
- **N4.** The prompt ids are written to the output (`inputs.prompt_ids`). They come from the units' samples files,
  but the six units must share one set, so they are bound to Gate A's pinned units' ids (the dev bank); a sentinel
  id in one pilot unit refuses (M). Information only.
- **N5.** `inputs.rules.path` and the `block …` refusal texts echo the lead's own command-line values (the rules
  path, `--block`), never file content (M).
- **N6.** A missing output folder gives "an unexpected FileNotFoundError (its message is withheld …)" (fixed, M); a
  named step would be friendlier. Cosmetic.
- **N7.** The unit path's own seed and edit hash (`round1/<seed>-edit-<hex>-e1-a<n>`) are shape-checked only; the
  unit's identity is bound through plan.json's COMPLETE.json SHA-256, COMPLETE.json's `job_sha256` and job.json's
  arm/seed fields, so this is sound (I).
- **N8.** A job-list entry that is not an object is skipped silently (as the builder's `scan` does); with the three
  real jobs present this cannot hide a unit (a missing seed refuses). Information only.
- **N9.** Section 40 point 2's constructed-case numbers (SE 5.10, df 198.5, lower 4.78) are not exactly reproduced
  by the table built from the test's description (SE 5.1042, df 199.04, lower 4.7703; the builder's test tolerances
  cover this); the point of the case (frozen form "stop", seed part alone "go") holds on it (M).

## 7. Not verified (hard rules 1-2)

The real kit state, plan.json, the a0_plant units, round 35's records and the real `REJUDGED_PINS` folders on disk
were not read or run; the reader's record-shape assumptions were checked against the code that writes the records
(`record_done`, `edit_sources`/`resolve_edit`, the runner's `engine_arm` and unit pattern), not against a record.
The full 60-mutant spec is the lead's run (the builder reports 59 killed and the one expected survivor).

## 8. Commands run (all foreground, read-only on every source; exit 0 unless stated)

`git -C <ws-r> status --porcelain`, `rev-parse HEAD`, `diff --stat`, `diff --stat 0d25497 -- …`, `diff --stat
55d5f8b 0d25497 -- …`, `ls-files`, `show 0d25497:<B16 file> | shasum -a 256` (14 files), `ls-tree`; `find`,
`shasum -a 256`, `grep -n`, `sed -n`, `wc -l`, `diff` (exit 1: the runner differs as described); `pytest` on the
package's tests (89 passed); the package's mutation runner on a 10-mutant shard (exit 0); my three scripts
(`my_paired.py` exit 0; `my_label_grid.py` exit 1 on its first run from my own unhandled B16 refusal, exit 0 after
the handler; `my_blind_attack.py` exit 1 on its first run from my own helper misuse, then exit 1 = findings as
listed in §4, by design); a key-only Python read of the stamped manifest's `files["scripts/stage1_s1/reading/…"]`
entries; `date -u` (22:43:44 and 22:59:09 UTC). Every basetemp and scratch folder I made was deleted; no bytecode
was written into the workspace (M, `find … __pycache__`: none); nothing under ws-r or the main checkout was changed.

## 9. Hard-rule log

Opened: addendum section 40 (lines 1377-1554) and headings; CHECK lines 112-207, 247-409 and headings; READY lines
255-270 and 355-362; REV4 lines 660-719; the W1 record lines 286-299; FOCUS grep lines (names only); B16's
contrast.py, tdist.py, labels.py, settings.py, README.md:140-170; reading_input's sources.py, items.py, build.py
(parts), __main__.py (head), tests/synth_kit.py (parts); the pilot_gate package (all 11 files); reading_extra's
runner (diff only); stage1_rules.py:150-200 and grep lines; plan_tool.py `record_done`, `edit_sources`,
`resolve_edit` and grep lines; job_runner_stage1.py grep lines and 670-678; the stamped manifest
`reading/timestamp/ots-manifest-reading-20261101.json` by key (the `scripts/stage1_s1/reading/*` hashes only; the
names of its other entries under that folder, two mutation files). Not opened: anything under `tmp/stage1-olmo/`,
`retrieved/`, `hosts/`, `judges/`, `seals/`, any real plan.json, `run-20261101/`, `block-a/`, `block-b/`, any
`units/` or `eval/` folder, any COMPLETE.json, answer, label, guard-sample or judge-cache file, any file whose path
holds "plant" or "decoy" (code files of the pilot package excepted; `build_plant.py` was not needed), the banks. No
network, install, pod, API call or git state command; the main checkout untouched; the other sessions' files in the
shared `s1b/tmp/` folder (`add_mutants_35.py`, `mut3/`, `r35*.log`, `suite*.log`) were listed by name only and left.
