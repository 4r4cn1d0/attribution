# R1 Track C: adversarial verification

**Verdict: VERIFIED_WITH_MINOR.** No blocker and no major defect. 3 minor defects (C1-C3) and 6 nits (C4-C9).
Report written 2026-11-08T15:31 UTC (clock read with `date -u`; skeleton 15:09 UTC).

- Target: B/ws-c, a detached worktree at `3481d85`. MAIN's HEAD is the same commit (M: `git log -1` in both).
- Tags: M measured (the command), R read (path:line, in WS unless named), E estimate, I inference.
- I edited no file in WS, MAIN or the builder's scratch. After my runs, `git status --short` in WS still lists only
  the 6 new files, and their SHA-256 values still equal the builder's table (M, 15:30 UTC). No pycache was left.
- I did not run either tool on a real list, bank, anchor list or unit. I opened no list, bank, prompt, answer or
  sealed file. I opened 5 real files, all records: the five side a0 units' COMPLETE.json (OLMo 1101-1103,
  Llama 1101-1102). The script printed only booleans: does each check that `tau_l_78b.read_unit` makes on
  COMPLETE.json pass? It printed no value, loss or count. It read no key under `evaluation` other than `query_loss`
  (`unit_shape.py`). I did not open any query_loss.jsonl. **The lead should know about this read:** under the
  blinding rules it is a structure read only.
- Scratch: R/r1-c-verify-scratch/ (scripts, logs, mutation JSONs; I deleted the runner's repo copies).

## Defects

| id | severity | file:line | defect | failure scenario | fix |
|---|---|---|---|---|---|
| C1 | minor | `encode_count_78b.py:512-518` with `:595-597`; `tau_l_78b.py:259-270` | A write that fails partway leaves a truncated record at `--out`, but both tools print "(nothing written)" and exit 2. M: probes C and D. A file handle writes half the bytes and then raises ENOSPC. Result: encode exit 2 with "nothing written", and `--out` exists with 1,814 bytes. τ_L: the same, with 799 bytes. | A disk-full or I/O error on the Mac. A truncated text-free record then exists. The message denies it. A re-run refuses with "exists". A reader may hash or parse the partial file. | When the write raises after the `"xb"` open, close the file and unlink it. It is this process's own new file. Or write to a temporary name in the same folder and `os.link` it to `--out` (no overwrite), then unlink the temporary file. Add the probe as a test, and add one mutant that drops the unlink. |
| C2 | minor | `encode_count_78b.py:401-402` (bank), `:434-435` (anchor), `:326` (responses); `test_encode_count_78b.py:526-549` | The planted-leak tests run only in lists mode, and they plant only a prompt. These three hand mutants **survive** (M): the bank prompts never enter the text guard; the anchor texts never enter it; the list responses never enter it. | A later edit drops one of these `guard.add` calls. Then a record or printout in bank or anchor mode that held a prompt, or one that held a list response, would be written and printed. The suite would stay green. | Parametrize `test_a_record_holding_text_is_not_written` and `test_a_printout_holding_text_is_not_written` over the three modes. Plant a response or unsafe response as well as a prompt. Add the three mutants (`hand_spec.json` ids V-bank-guard-add, V-anchor-guard-add, V-guard-no-responses). |
| C3 | minor | `encode_count_78b.py:280-284`; `test_encode_count_78b.py:485-503` | Hand mutant V-train-catch-all **survives** (M). It widens `refusals_train`'s `except ValueError` to `except Exception`. The only crash test raises inside `prompt_ids`, and the generation check reaches `prompt_ids` first. So the train path's catch scope is never tested. | A widened catch would count a tokenizer crash on a response (a TypeError, say) as a refusal. The tool would then exit 1 with a written record, not exit 2. The frozen callers catch ValueError only (R: `make_untuned_answers.py:189-194`, `representation_pass.py:343-348`). | Add a fixture codec whose `encode` raises RuntimeError on one response text only. Assert exit 2, no record and no sentinel. Add the mutant. |
| C4 | nit | `encode_count_78b.py:321-324` (also `:397-400`); frozen `scripts/stage1/s1common.py:90-96, :113-117` | A frozen reader's refusal that comes before the guard holds that file's texts is printed verbatim. `s1.strict_json` raises its duplicate-key Refusal (not a ValueError) with `key!r`. M: probe B planted a duplicate key that holds the sentinel. Under fixture pins, the sentinel reached stderr. | Not reachable with the module's literal pins. Each reader checks the hash before it parses (R: `make_untuned_answers.py:68-70`; `oext_eval.py:306-307, :330-332`; `encode_count_78b.py:186-193`), and the pinned files are canonical JSON. The risk is real only if a future pin or reader admits non-canonical bytes. | Optional. When a reader message starts with "a JSON object repeats the key", replace it with a fixed text. Or withhold any reader message that holds a quote character. Add the probe as a sentinel test. |
| C5 | nit | `encode_count_78b.py:595`; `tau_l_78b.py:265-270` | Both mains catch `Exception`, not `BaseException`. M: probe G. A SystemExit that carries text, raised inside the run, escapes `main`. Python then prints its message and exits 1, which is EXIT_SOME ("written with refusals"). On the current path only `AnchorJobError` (a SystemExit subclass, R: `make_anchor_answers.py:41`) raises SystemExit, and it is caught (R: `encode_count_78b.py:429-430`). Nothing else does (M: `grep SystemExit` over the path's modules). | Today, none. A future frozen helper might stop with `raise SomeStop(text)` in the `AnchorJobError` pattern. Its text would then print, and exit 1 would look like a written count. | Catch `SystemExit` as well (withhold its message, exit 2). Wrappers should judge exit 1 only together with the record's existence (builder open point 7). |
| C6 | nit | `encode_count_78b.py:40` (doc), `:493-509` (code); r1-c.md §5 `OUT=` line | The code refuses `--out` anywhere under any input's folder, at any depth, because it walks all ancestors. The docstring and §5 say only "not beside an input". M: a CLI run with `--out` in a subfolder of the inputs' folder was refused with "must not lie beside an input file". | The lead puts OUT under the folder that holds the located lists. The run exits 2 and must be re-run. This is fail-closed. | Say "not inside any input's folder (at any depth) and not inside P_F" in the docstring and in §5. |
| C7 | nit | r1-c.md §5 (C2 command) | `<OEXT_RECORD_JSON>` and `<OEXT_BANK_SHA256>` are left as placeholders, but both are committed facts. M: `.ai/inputs/stage1-commitments-20261016/oext-bank/oext_record.json` hashes to `a810574e…` and is tracked. Its `bank.full_file.sha256` is `6487ed2b9d5717d20b9bade8b51c2511cd6c83f597dafff983e8c391b1954162` (96,014 bytes; 400 items; no shortfall). | None. A placeholder adds a manual step. | Fill both. Only the bank file's path stays for the lead (GXB O13). |
| C8 | nit | r1-c.md §8 open point 2 | The text says the special-id sets "differ at most by the pad id". For Llama, the pod codec's extra stop ids (`<\|eom_id\|>`, `<\|end_of_text\|>`) are also arguments that the Mac codec lacks. The measured answer is that the sets are equal on both families (my item 3). | None. The conclusion stands. | Replace the open point with item 3's measured result. |
| C9 | nit | spec `mutation_spec_c_78b.json` | Further hand-mutant survivors, all harmless. Two are equivalent in outcome: V-out-exists and V-tl-out-exists, because the `"xb"` open still refuses. V-hex-check is also equivalent, because `pinned` still refuses an upper-case digest. So are V-tl-finite-loss and V-tl-recorded-finite: a `1e999` loss or mean still fails the exact-mean check. Two are untested but harmless: V-record-cmdline-pin (the command line names a wrong record hash while the bytes still pass the pin) and V-tl-ids-unsorted (over-strict on id order). | None. | Optional. Add a test where the command line names a wrong s-pool record hash with good bytes. Add a τ_L test with the same ids in a different order. |

## 1. No text can leak (M/R)

- **By construction (R).** The record holds counts, class names, ids (list ids match `s1.SAFE_VALUE`, at most 160
  characters of `[A-Za-z0-9_.:+/-]`; R: `s1common.py:73`), anchor indices, hashes and the RULE string
  (`encode_count_78b.py:254-257, :465-473`). Refusal messages from the tool hold ids, counts and hashes only. Any
  exception that is not the tool's own `Refusal` prints only its class name and file:line (`:140-148`). The record
  bytes and every printed line are scanned against every text read, before the write (`:590-593`). τ_L reads no text
  at all. It drops every loss-line field except `query_id` and `loss` (`tau_l_78b.py:186-187`), and its messages hold
  seeds and hashes only.
- **Frozen readers' messages (R).** `read_list` (`make_untuned_answers.py:63-79`), `load_bank` (`oext_eval.py:298-353`)
  and `read_prompt_list` (`make_anchor_answers.py:48-77`) give names, counts, positions and hashes only. The one
  exception is `s1.strict_json`'s duplicate-key message (C4). It cannot be reached with the literal pins.
- **Probes I ran (M; `probes/test_probes_c.py`, `test_probes_c2.py`; synthetic fixtures; the builder's helpers
  imported, WS not edited):**
  - (A) a frozen `read_list` that refuses with text before the guard has seen that list's texts: the text is printed
    (limit; see C4);
  - (B) a duplicate key that holds the sentinel, under fixture pins: printed (C4);
  - (C, D) a partial write: a truncated record is left, and the message says "nothing written" (C1);
  - (E) an anchor-mode RuntimeError that holds text: withheld, exit 2, no record;
  - (F) a bank-mode KeyError(text): withheld, exit 2;
  - (G) a SystemExit(text) from the codec: escapes `main` and carries the text (C5).
- **Sentinel coverage.** The no-text assertions (`no_text`, 15 calls) cover stdout, stderr and the record in all three
  modes on the success path. They also cover lists mode's refusal and crash paths, and the forced leaky record or
  printout. The guard itself is exercised only in lists mode and only on prompts (C2).
- **Not scanned (I, limit).** The tool does not scan stderr written by third-party code, such as transformers warnings.
  None of the warnings I know carry input text. My real-tokenizer run printed none (M: `codec_compare.log`). The guard
  also misses a partial text (a substring of a prompt). By construction, nothing writes one.

## 2. Faithful to the frozen code paths (R/M)

- **The limit field.** Confirmed: it is `model.max_prompt_tokens`. M: both MAIN_F configs have model `max_prompt_tokens`
  1536 and `max_train_tokens` 3072. Their `generation` block keys are only `batch_size, decoding, guard_over_limit,
  harm_samples, max_new_tokens`. M: `grep -rn max_prompt_tokens --include='*.py'` over experiments/, scripts/ and
  runkit/. Every frozen caller reads `recipe["model"]["max_prompt_tokens"]`, and none reads a generation field.
  Examples: `make_untuned_answers.py:251`, `oext_eval.py:525`, `make_anchor_answers.py:127`, `runner.py:681`,
  `oext_unit.py:507`, `eval_adapter.py:759`; and `config.py:516` validates it. M: every 7-8B OLMo-2 and Llama config
  (main, G, other LR) has the same 1536/3072 and the same tokenizer. So the G recipe would give the same bank count.
  Recipe S_78 keeps the model block (R: `make_recipe_s78.py:12, :49`).
- **Lists mode.** It reads through `mua.read_list` at the pin (`encode_count_78b.py:322`). The record must be kind
  "stage1 s-pool record" at `bcca59ac…` (M: shasum of the committed record), with the list and pool hashes and sizes
  (`:291-313`). The S1 and S4 ids must equal the record's, in order (`:344-346`). s3_safe must be the subset, then
  S1's rows outside it (`:347-350`). This equals the builder's own construction (R: `build_s_pool.py:376-379`).
  The S1 rows must equal their s3_safe twins (`:351-355`). `encode_generation_prompt` runs on all three lists, and
  `encode_train` runs on the s3_safe and S1 pairs (`:93-94, :358-365`; DES item 38, DESO items 6/17).
- **`--bank`.** It reads through `oext_eval.load_pinned_settings()` and `oext_eval.load_bank` (`:389, :398`). The
  settings pin `a810574e…` with 400 planned (M: the test against the real settings). The encode is the same
  function, at the same limit, as `oext_eval._encode` (R: `oext_eval.py:522-535`). The bank's hash on the command line
  is checked only after `load_bank` has checked the bytes against the record (`:403`). This is harmless, because the
  bytes are pinned before they are used.
- **`--anchor`.** The tool uses the same reader (`maa.read_prompt_list`, the same pin and 128). The harmful check is
  `maa._encoded` on `rows[:64]` with `h-{k}` ids, at the recipe's `max_train_tokens`. The generation check is
  `encode_generation_prompt` on all 128 at `max_prompt_tokens`. They run in the job's order, harmful first
  (`encode_count_78b.py:437-451` against `make_anchor_answers.py:117-130`). MAIN_F's `attribution.query_bank` is
  "ref" on both families (M), so the job would accept MAIN_F as REC. The anchor job's recipe at 7-8B is MAIN_F (I;
  RK `KIT[F]["rec"]` = CONFIGS main, R: `rules_78b.py:203, :224`).

## 3. The codec question (builder open point 2): decided, no difference (M + R)

- **What the encode functions use (R: `textproc.py:173-201`).** `encode_train` and `encode_generation_prompt` read only
  `codec.prompt_ids` (the chat template), `codec.encode`, `codec.has_special` (that is, `special_ids`) and
  `codec.eos_id`. They never read `stop_ids` or `pad_id`. `build_codec` sets `special_ids` = `all_special_ids` ∪
  added-special ids ∪ {eos, pad, stops} (R: `textproc.py:116-136`). Both codecs load the same tokenizer:
  `check_tokenizer` holds the manifest's (repo, revision, end token) equal to the recipe's (`encode_count_78b.py:237-248`).
  Both use the same eos, the end-of-turn token. So **a token length can never differ**. A verdict could differ only if
  the pad id or a stop id lay outside `all_special_ids` ∪ added-special.
- **Measured on both real tokenizers, offline** (M: `codec_compare.py` under the sandbox with HF_HUB_OFFLINE=1,
  exit 0). It loads `load_tokenizer(*tokenizer_of(MAIN_F))`. It builds the Mac codec (`real_codec`'s arguments) and the
  pod codec (`loaders.py:187`'s arguments).
  - OLMo-2-7B (tokenizer `48d788eca847`): pad `<|pad|>` (100277) is in `all_special_ids` and in added-special. The
    stops are the end token only. The special sets are equal (8 = 8 ids; the differences are empty both ways).
  - Llama-3.1-8B (`0e9e39f249a1`): `<|eom_id|>` (128008) and `<|end_of_text|>` (128001) are not in `all_special_ids`,
    but they are in added-special. The sets are equal (256 = 256; the differences are empty).
  - Synthetic texts holding each stop or pad token give ControlTokenError under both codecs, for both checks.
    Synthetic texts of 10, 700 and 1,600 words give the same `prompt_ids` and train lengths under both codecs.
- **Decision.** For these two tokenizers, the Mac count and the pod's checks give the same verdict for every text.
  There is no "passes on the Mac, fails on the pod" case at the prompt level, and no reverse case. No fix is needed.
  Optional hardening: in `real_context` or `check_tokenizer`, also build `build_codec(tok, end, recipe stop_tokens,
  recipe pad_token)` and refuse unless `eos_id` and `special_ids` are equal. That would check the claim at run time
  for any future tokenizer. The pod's tokenizer-level checks (`build_codec`'s single-token checks,
  `check_assistant_header`) are not per prompt, so they cannot change a count.
- **Library versions.** The Mac PY has transformers 4.56.2, tokenizers 0.22.2 and jinja2 3.1.6 (M). These equal the
  pins in `.ai/inputs/minimal-experiment-20261002/environment.lock:10, :26, :29` (R). That the 7-8B pods install the
  same versions is I (R: `runkit/family-probe-olmo3/tests/test_family_probe_olmo3.py:253` holds the engine lock at
  4.56.2). The record writes the transformers version. Adding the tokenizers version would be cheap (nit; not in the
  table).

## 4. τ_L (R/M)

- **The formula.** τ_L = 2√2 × s (`tau_l_78b.py:214`). s = `statistics.stdev` with ddof 1 (`:211`). The mean is
  `math.fsum`/200 and must equal COMPLETE.json's `evaluation.query_loss.mean` exactly (`:195-197`). This equals Part 2
  §4.7 (P2:593), PR4 §6.7 (PR4:588-595) and REQ-19's code (`limits_check.py:39-41, :325-330, :388-393`). The engine
  writes the mean with `statistics.fmean` (R: `runner.py:61, :678`). In CPython 3.8 and later, `fmean` is fsum/n, so
  exact equality holds as it did at 1B (I). The 1B known answer reproduces (M: `test_known_answer_req19`).
- **Reads.** The tool reads only COMPLETE.json, whose bytes must equal the pin, and `eval/e1/query_loss.jsonl`
  at the hash that COMPLETE.json lists. error.txt gets only a stat (`:146-180`). COMPLETE.json's `evaluation` is the
  same dict that is written to summary.json (R: `runner.py:786-795`), so dropping summary.json loses nothing.
- **Identity, against RK.** `TRAINING_IDENTITY` and `MANIFESTS` equal RK (R: `rules_78b.py:110-111, :205, :226`).
  The unit pins equal RK's `a0_units` (R: `:211-216, :232-235`). **M (booleans only, `unit_shape.py`):** all five
  real side units pass every COMPLETE.json check in `read_unit`. Those checks are: the pin, complete, files,
  target_checkpoint e1, arm a0, seed, training identity, manifest, evaluation checkpoint e1, n 200, a finite float
  mean, a 64-hex query bank hash, the loss file listed and present, and no error.txt. Each family's side units share
  one query bank. This settles most of builder open point 3 for OLMo-2-7B now. Not verified: the exact-mean check, and
  the 200 distinct shared ids in query_loss.jsonl (not opened, by rule).
- **Llama's N a0-1103.** Its literal pin is None, so its pin comes from the command line. The record marks
  `pin_source` "command line (N's unit; no literal pin yet)" (`:61-68, :132-135, :217-218`; V-tl-pin-source killed,
  M). Its form is unknown until block 0 runs: builder open point 4 stands. Block 0 runs it as an `a0_arm` job at 38
  steps (R: `rules_78b.py:575-581`). If its unit has another form, the tool refuses.

## 5. Tests and mutants (M)

- **Suite.** `sandbox-exec -p "$SB" PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS gave
  **310 passed, 57 skipped**, exit 0, 32.4 s (`suite.log`). This equals the builder's count. Counts in the builder's
  report also check out (M: `grep`, `wc`): 57 + 18 test functions; 36 + 26 mutants; the line counts.
- **The builder's full spec.** The runner under the sandbox, ALL: baseline exit 0 ("102 passed"),
  `imports_the_copy` true, **62 killed, 0 survived, 0 invalid**, exit 0, 41 s (`mut-all.json`, `mut-all.log`).
- **Runner validity (R: `run_mutants_c_78b.py`).**
  - A mutant is KILLED only on exit 1 with FAILED lines and no ERROR line. Anything else is INVALID, and a timeout is
    invalid (`:85-90`, `run_suite` `:66-83`).
  - The baseline runs the same command as each mutant (`run_suite`), and it must pass first (`:128-135`).
  - The spec is read from SOURCE, the mutation is applied to the copy, and the copy is restored and re-hashed (`:138-154`).
  - The import probe resolves both modules inside the copy (`:93-102`), and 62 kills confirm it.
  - Nit: `OUT.json` is overwritten if it exists (`:132, :161`). This is harmless.
- **Hand mutants** (`hand_spec.json`, 18; run through the builder's runner on a scratch source copy, `mut-hand.json`;
  baseline exit 0): 7 killed and 11 survived.
  - Meaningful survivors: V-bank-guard-add, V-anchor-guard-add, V-guard-no-responses (C2), and V-train-catch-all (C3).
  - Equivalent or harmless survivors: listed in C9.
  - Killed: V-s4-ids-unchecked, V-record-size, V-bank-record-cmdline, V-guard-min-chars, V-tl-sum, V-tl-pin-source,
    V-tl-family-ti.
- **Proposed new spec mutants.** The 4 meaningful survivors, once C2 and C3 add their tests. Also a mutant for C1's
  unlink, once it exists.

## 6. The lead's commands (r1-c.md §5)

- **They run as written** (R + M):
  - The flags match the parser (`encode_count_78b.py:544-556`; `tau_l_78b.py:249-252`).
  - `-I` works, because both scripts insert REPO themselves (`:61-64`). M: CLI smokes under `-I` gave exit 2 with
    clean refusals.
  - All pins in the commands equal the module literals and RK.
  - The default s-pool record exists at its pin (M).
  - All five unit folders and both prepared folders exist (M: `test -d`).
  - The offline settings come from `loaders._offline()` (R: `loaders.py:76-78`), inside the network-deny sandbox.
- **Writes.** The tools write only `--out`, once (`"xb"`). The runner writes only inside SCRATCH and to OUT.json. The
  tests write under pytest's tmp_path only (R: grep of the two test files).
- **Gaps.** C6: the OUT rule is "anywhere under an input folder". C7: the O-ext record path and the bank hash can be
  filled. When run from MAIN, the suite's earlier Track B tests that skip in WS will run, because `tmp/kt-prepared`
  exists. So MAIN's count will differ from 310/57. This is not Track C's doing (R: `conftest.py` docstring).

## Commands run (all foreground, under 10 minutes)

| # | command (short) | exit |
|---|---|---|
| 1 | `cat`/`sed`/`grep` of r1-common, the rulings, the plan, the builder's report, the frozen sources and RK | 0 |
| 2 | `git log -1`, `git status --short`, `shasum -a 256` in WS and MAIN | 0 |
| 3 | PY `-B -I -c` prints of the MAIN_F model and generation keys, query_bank, the limits of all 7-8B configs, and the O-ext record's bank hash | 0 |
| 4 | `sandbox-exec … env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PY -B -I codec_compare.py WS` | 0 |
| 5 | PY `-B -I unit_shape.py MAIN` (booleans only) | 0 |
| 6 | `sandbox-exec … PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` (WS): 310 passed, 57 skipped | 0 |
| 7 | `sandbox-exec … PY -B run_mutants_c_78b.py WS …/mut-all …/mut-all.json ALL`: 62 killed | 0 |
| 8 | `make_hand_spec.py` (18 mutants into a scratch copy), then the runner on that copy, ALL: 7 killed, 11 survived | 1 (survivors, expected) |
| 9 | `sandbox-exec … PY -B -m pytest … probes/test_probes_c.py` and `test_probes_c2.py` (7 + 2 probes) | 0 |
| 10 | CLI smokes under `-I` with nonexistent inputs (encode twice, τ_L once) | 2 (refusals, expected) |
| 11 | `rm -rf` of the scratch repo copies and the scratch source copy; final `git status` and shasum in WS | 0 |

## Answers on the checklist

1. **No text leak.** No path leaks text with the literal pins. Three gaps remain: C1 (partial write), C2 (guard test
   coverage) and C5/C4 (limits).
2. **Faithful.** Yes. The field is `model.max_prompt_tokens`, and the builder's correction is right.
3. **Codec.** No difference on either family (M). No fix is needed. An optional run-time equality check is suggested.
4. **τ_L.** Correct. The real side units pass every COMPLETE.json check (M, booleans). N's form is still open.
5. **Tests and mutants.** Both reproduce (310/57; 62/62). There are 4 meaningful hand-mutant survivors (C2, C3).
6. **Commands.** They run as written. C6 and C7 are nits.
