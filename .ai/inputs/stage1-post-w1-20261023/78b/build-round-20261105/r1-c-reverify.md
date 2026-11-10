# R1 Track C fix round: adversarial re-verification

**Verdict: VERIFIED_WITH_MINOR.** Merging is safe. Every item the first verifier asked for is closed (C1, C2, C3, C5,
C6, C7, C8, the runner nit, and the optional C9). C4 is stated as a limit. I found 3 new nits (CR1-CR3). None of them
blocks a merge, and none can put text in a record or a printout. CR1 and CR2 are cheap to fix now.

Status: done. Skeleton written 2026-11-08T15:41 UTC; report written 15:57 UTC (clock read with `date -u` each time).

- Target: B/ws-c at `3481d85`, a detached worktree. It holds the six new files. Their SHA-256 values equal the builder's
  §10 table at the start and at the end of my work (M: `shasum -a 256`, 15:41 and 15:57 UTC). `git status --short`
  lists only the 6 untracked files (M). I edited no file in WS, MAIN or the builder's scratch. No pycache was left in WS.
- Tags: M measured (the command), R read (path:line in WS unless named), E estimate, I inference.
- I did not run either tool on a real list, bank, anchor list or unit. In the §5 check, every such path was swapped for
  a nonexistent one, and the encode count used the builder's fake codec, so no tokenizer was loaded. Of real files I
  read only these: the committed O-ext record (its SHA-256, plus `bank.full_file` {sha256, bytes}, `n_items`,
  `bank_size` and `shortfall`), the committed s-pool record (its SHA-256), and `test -d` on the 2 prepared folders and
  the 5 unit folders (a stat only).
- Scratch: R/r1-c-reverify-scratch/ (probes, hand spec, logs, mutation JSONs). I deleted the runner's repo copies, the
  hand-mutant source copy and the pytest temp folders.

## Defects

| id | severity | file:line | defect | failure scenario | fix |
|---|---|---|---|---|---|
| CR1 | nit | `encode_count_78b.py:531-536` (docstring `:513-515`); `tau_l_78b.py:263-268` (docstring `:245-247`) | The `finally` in `write_once` catches only `FileNotFoundError` from `os.unlink(partial)`. Any other unlink error escapes and replaces the outcome. **M (probe `C1-unlink-fails-after-link`, all 4 modes):** the link succeeds, then unlink raises PermissionError. Result: exit 2 and "REFUSED: PermissionError … (nothing written)", but --out exists as complete JSON, and `.rec.json.<pid>.partial` is left beside it. **M (probe `…-after-write-error`):** ENOSPC, then the unlink fails. A truncated `.partial` is left (1,814 / 899 / 1,090 / 799 bytes), and the message names PermissionError, not the write failure. **M (probe `C1-sigterm-window`):** after a SIGTERM inside the write, `.rec.json.<pid>.partial` (1,000 bytes) is left. The child exits -15, and no `finally` runs. The docstring's "removed in every case" is therefore not true on these paths. | To reach the unlink case, unlink must fail on the tool's own new file within microseconds of the link. That takes a concurrent chmod or `chflags` of the folder, or an I/O error. The lead would then see exit 2 with "nothing written" while a complete record exists, and a re-run would refuse with "exists". This is the message-denies-the-file class of C1, but far less likely. The SIGTERM or SIGKILL case leaves only a hidden, text-free stray file. **--out itself is never truncated on any path I found.** | In the `finally`, catch `OSError`. If the link had succeeded, return the digest and print one line naming the stray temporary file. If the link had not succeeded, keep the original Refusal and add the stray file's name to it. Word the docstring as "removed unless the process is killed or the unlink itself fails". Optional: during `write_once`, turn SIGTERM and SIGHUP into SystemExit so the `finally` runs. SIGKILL stays a limit. |
| CR2 | nit | `encode_count_78b.py:519-527`; `tau_l_78b.py:251-259`; both test files | The branch "a partial file of --out exists" (the temporary name is already present) has no test. **M:** hand mutants H-ec-created-early and H-tl-created-early set `created = True` before the open, and both **survive**. Under such a mutant, a pre-existing `.partial` that another process made would be deleted, and the message would wrongly say "--out exists". The real code is right. M (probe `C1-stale-partial`, all 4 modes): exit 2, "a partial file of --out exists", the stale file intact, no --out. | Only a later edit could break this. A stale `.partial` with this run's PID needs an earlier killed run and PID reuse (see CR1). | Add one test per tool. Create `.<out>.<os.getpid()>.partial`, run the tool, and assert exit 2, that message, the stale bytes intact and no --out. Add the two mutants. |
| CR3 | nit (pre-existing; outside the fix diff) | `encode_count_78b.py:496-498`; `tau_l_78b.py:228-230` | `out_ok` resolves --out before its `out.is_symlink()` test. So that test can never fire for a dangling link, and the record is created at the link's target. **M (probe `out-dangling-symlink`):** --out is a dangling link to `elsewhere/t.json`. Encode lists exits 1 and τ_L exits 0, and each creates the target. A link whose target lies inside an input folder or a unit is still refused (exit 2). The mutation runner checks its OUT.json on the unresolved path and refuses a dangling link (M). | No overwrite and no text: the target did not exist, and the input-folder rule still applies to the target's folder. The record just lands where a stray link points, and the rule "--out is a new file" is broken for links. | Test `os.path.lexists(args.out)` (or `Path(args.out).is_symlink()`) before `.resolve()`. Add a test with a dangling link. |

Limits (not defects): (a) SIGKILL and power loss can leave a `.partial` file (CR1). (b) On macOS, `os.fsync` is not
`F_FULLFSYNC`, so durability after a power cut is not guaranteed (I). The mutant H-ec-no-fsync survives, as expected,
because tests cannot see durability. (c) The input-folder rule is checked once, before the run. Swapping --out's parent
folder for a link during the run would get past it (I; adversarial only). (d) C4 is unchanged: the first verifier's
probes A and B still put the sentinel on stderr (M, `vprobes.log`). The cause is a frozen reader's refusal that holds
text, raised before the guard has that file's texts. The literal pins cannot reach it (R: r1-c-verify.md §1).

## 1. The first verifier's items, re-checked

| item | asked | result |
|---|---|---|
| C1 | a failed write leaves no truncated --out and no false message | **CLOSED (M).** The first verifier's probes C and D, re-run unchanged against WS, give exit 2 with "--out cannot be written (OSError)" and no --out (`vprobes.log`). My probes cover lists, bank, anchor and τ_L. For each mode they test: ENOSPC after half the bytes; EIO on fsync; EPERM, EXDEV and ENOTSUP on link; and EIO on close. All give exit 2, no --out, an empty folder and text-free output (`probes.jsonl`, `C1-*`). A SystemExit inside the link gives exit 2 with an empty folder. A KeyboardInterrupt in the write escapes, as expected, and the `finally` still leaves the folder empty. Open: CR1. |
| C2 | the guard in every mode, prompts and responses | **CLOSED (M).** The builder's tests are parametrized over 5 cases (R: `test_encode_count_78b.py:873-903`). V-bank-guard-add, V-anchor-guard-add and V-guard-no-responses are killed by `[bank-prompt]`, `[anchor-prompt]` and `[lists-response]` (`mut-ec.json`). My own plants use two other routes: the recipe path label in the record, and a reason name in both the record and the printout. Over the 5 cases, all 10 gave exit 2, "would hold text", no --out and no text. Two more hand mutants are killed: H-anchor-no-unsafe (drops only the unsafe responses) and H-lists-no-prompts. H-printout-unscanned is killed too. |
| C3 | a non-ValueError on a response refuses the run | **CLOSED (M).** V-train-catch-all is killed by `test_an_encode_train_crash_refuses_the_run`. My probe raises RuntimeError, TypeError, KeyError, AttributeError or IndexError on one S1/s3_safe response, one bank prompt or one anchor unsafe response. All 15 cases give exit 2, no --out, the class named and no text. |
| C4 | stated as a limit | **STATED** (R: r1-c.md §10, "Not done: C4"). The statement is accurate for the real readers. Probes A and B reproduce it (M). |
| C5 | a SystemExit carrying text is caught | **CLOSED (M).** The first verifier's probe G: SystemExit no longer escapes `main`. The codec raises SystemExit(text), SystemExit(0), SystemExit(1), SystemExit() or AnchorJobError(text) in lists, bank and anchor mode. All 15 give exit 2 with the message withheld. Before the fix, SystemExit(0) would have ended the process with exit 0 and no record. τ_L, with SystemExit text/0/1 raised from `strict_json`, gives exit 2 with "REFUSED: SystemExit". A SystemExit(text) from each mode's frozen reader, raised before the guard has that file's texts, is also withheld. C-ec-systemexit and C-tl-systemexit are killed. `main` catches neither KeyboardInterrupt nor GeneratorExit, and no module on the path subclasses BaseException (M: `grep`). |
| C6 | the docs say "any depth" | **CLOSED (R).** See `encode_count_78b.py:40`, `:494-495`, `:508`, r1-c.md §2 (lines 73-74) and the §5 `OUT=` line. The test asserts the new message (`test_encode_count_78b.py:408`). |
| C7 | the record path and the bank hash are filled in | **CLOSED (M).** `oext_record.json` hashes to `a810574e…` and is tracked by git. Its `bank.full_file` is `6487ed2b9d5717d2…` at 96,014 bytes, with 400 items, `bank_size` 400 and `shortfall` null. The §5 bank command run as written (bank path nonexistent) passes the record pin, the settings pin and `load_bank`'s record checks, and then stops at "the O-ext bank file cannot be read" (R: `oext_eval.py:306-328` reads the record before the bank). |
| C8 | open point 2 rewritten | **CLOSED (R).** r1-c.md §8 point 2 now names the pad id and Llama's 2 extra stop ids, and cites the measured equality. |
| runner nit | OUT.json is never overwritten | **CLOSED (M).** Given an existing OUT.json, the runner exits 1 with "exists; give a new report path", creates no scratch folder and leaves the file's hash unchanged. A dangling-link OUT.json is refused too. |
| C9 (optional) | 2 tests | **DONE (M).** V-record-cmdline-pin and V-tl-ids-unsorted, which survived the first round, are now killed by `test_record_command_line_hash_must_be_the_pin` and `test_the_same_rows_in_another_order_pass`. |

## 2. The whole diff (R/M)

- I recomputed the diff of the six WS files against `R/r1-c-scratch/prefix/`. It matches `fix.diff` hunk for hunk
  (M: `mydiff.diff`; `fix.diff` SHA-256 `0a17bf6a…` as stated). The prefix copies hash to the §1 table (M).
- `encode_count_78b.py` changes only: the docstring line (:40); the `out_ok` docstring and its message (:494-495,
  :508); `write_once` (:512-537); and the `main` except clause (:614). `tau_l_78b.py` changes only: the docstring
  (:31); a new `write_once` (:244-269); the `main` call to it (:288); and the except clause (:292).
- No counting logic, no pin, no reader call, no limit, no exit code (other than SystemExit now giving 2, as asked) and
  no record field changed. `doc_of`, `tau_l`, `_tally`, the `run_*` functions and every constant are unchanged. The
  only new refusal messages are "--out cannot be written (<class>)" and "a partial file of --out exists". §10 does not
  name the second one (see CR2).
- Tests: the two old lists-only leak tests are replaced by parametrized tests of the same names. These cover the old
  lists-prompt case and also assert "would hold text" for the printout. One assertion's message text was updated.
  Twelve new test functions were added. Spec: C-ec-write-wb was removed (its find text is gone), and 10 mutants were
  added: 62 - 1 + 10 = 71 (M: 42 encode, 29 τ_L). Every find text occurs exactly once, and none is a no-op (M).
- Note: C-ec-write-direct and C-tl-write-direct are killed by the first success test, because `link(out, out)` fails.
  They do not test the partial write. My stronger mutants are H-ec-link-first and H-tl-link-first, which link before
  the bytes are written. Both are killed by the ENOSPC tests (M). H-ec-replace and H-tl-replace (`os.replace` instead
  of `os.link`) are killed by the no-overwrite tests (M).

## 3. The atomic write (M/R)

- **No truncated --out on any path tested.** The link comes only after write, flush and fsync (R: `encode_count_78b.py:520-525`).
  Every failure before the link (open, write, flush, fsync, close) leaves no --out (M, §1 row C1).
- **No overwrite, including the race.** `os.link` fails with EEXIST if --out exists at link time (R: `:525`). In my
  probe, a file is created at --out between `out_ok` and the link, in all 4 modes. Each run gives exit 2 with
  "exists: the record is created once", the other file's bytes are untouched, and no `.partial` is left. A dangling
  link placed at --out in the same window is not followed: its target is not created (M, `C1-race-*`). O_EXCL on the
  temporary name refuses an existing name and does not follow a link there (M, `C1-stale-partial`).
- **A `.partial` can survive** an unlink failure or a signal that skips `finally` (CR1). A pre-existing dangling link
  at --out is followed (CR3, pre-existing).

## 4. Suite and mutation shards (M)

- Suite in WS: `sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` gave **331 passed, 57
  skipped**, exit 0, in 22.5 s (`suite.log`). This equals the builder's count. The existing (not Track C) tests
  `test_s1_olmo2_7b_check*.py` create and remove `tmp/scale-78b-s1-*-tests` inside WS's own `tmp/` (R:
  `test_s1_olmo2_7b_check.py:26`). WS's `tmp/` is empty afterwards (M).
- The tests import WS's modules (M: `__file__` of `encode_count_78b`, `tau_l_78b`, `s1common` and `textproc` all
  resolve under WS; the venv's only .pth is `_virtualenv.pth`).
- Shard encode (42 ids): baseline exit 0 with "123 passed", `imports_the_copy` true, **42 killed**, exit 0, 17.6 s
  (`mut-ec.json`).
- Shard τ_L (29 ids): baseline exit 0, copy true, **29 killed**, exit 0, 26.6 s (`mut-tl.json`).
- ALL (the lead's form, `"$PWD"` = WS): baseline exit 0, copy true, **71 killed, 0 survived, 0 invalid**, exit 0, 70 s
  (`mut-all.json`). The copy's tree hashes equal the WS files. Every kill is pytest exit 1 with FAILED lines and 0
  ERROR lines. Every mutant restored to its before-hash (M). The baseline uses the same `run_suite` command as the
  mutants (R: `run_mutants_c_78b.py:130, :150`).
- Hand mutants (`mut-hand.json`, 15, run on a scratch source copy): 12 killed and 3 survived. H-ec-created-early and
  H-tl-created-early survive (CR2). H-ec-no-fsync survives (equivalent in tests).
- §5 says the full spec takes "about 20 s". My ALL took 70 s, still far under 10 minutes. The figure is low but
  harmless.

## 5. The lead's commands (r1-c.md §5) (M/R)

- **They run as written.** `cmd_check.py` parses the §5 block, takes the 6 tool commands and runs them in process with
  cwd = MAIN. Lists, bank, anchor list and unit folders are swapped for nonexistent paths, with the pins exactly as
  written. Each command gets past argument parsing, the mode checks, `out_ok`, the recipe pin, the tokenizer check and
  every command-line pin. It then refuses at the first nonexistent input, with exit 2 and nothing written:
  - lists (×2): "list s1 cannot be read". The default s-pool record was read at its pin first.
  - bank: "the O-ext bank file cannot be read". The C7 record path and pin were accepted by `load_bank`.
  - anchor: "the anchor prompt list cannot be read".
  - τ_L (×2): "unit 1101: COMPLETE.json cannot be read". The five literal unit pins and the placeholder 1103 pin were
    all accepted by `parse_units`.
  (`cmd_check.log`)
- The two prepared folders and the five unit folders in §5 exist in MAIN (M: `test -d`). The suite and runner commands
  ran in WS in the same form (§4). From MAIN, the suite's counts will differ, because Track B tests that skip in WS
  will run (first verifier §6).
- The `OUT=` comment matches the code (R: `out_ok` `:493-509`). A folder that is a parent of an input's folder is
  allowed; a folder inside one is not.

## Commands run (all foreground, under 10 minutes)

| # | command (short) | exit |
|---|---|---|
| 1 | `cat`/`sed`/`grep` of r1-common, both reports, `fix.diff`, the six WS files, the frozen helpers (`make_anchor_answers._encoded`, `textproc.encode_train`, `oext_eval.load_bank`) | 0 |
| 2 | `git log -1`, `git status --short`, `shasum -a 256` in WS (start and end); `shasum` of the prefix copies; `diff -u` prefix vs WS, compared with `fix.diff` | 0 |
| 3 | `sandbox-exec … PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS: 331 passed, 57 skipped | 0 |
| 4 | PY `-B -I -c` checks of the spec: ids by file, find counts, no-ops | 0 |
| 5 | `sandbox-exec … PY -B scripts/scale78b/tests/run_mutants_c_78b.py WS R/…/mut-ec R/…/mut-ec.json <42 ids>`: 42 killed | 0 |
| 6 | the same with the 29 τ_L ids: 29 killed | 0 |
| 7 | `make_hand_spec.py` on a scratch source copy, then the runner with ALL: 12 killed, 3 survived | 1 (survivors, expected) |
| 8 | `sandbox-exec … PY -B -m pytest -p no:cacheprovider -q -s --basetemp R/…/pt-probes probes/test_reverify_probes.py` (cwd WS): 103 probe cases | 0 |
| 9 | the same for the first verifier's `probes/test_probes_c.py` and `test_probes_c2.py` (run read-only from their scratch): 9 | 0 |
| 10 | MAIN: `git ls-files`, `shasum` of the two committed records, a PY `-B -I -c` print of the O-ext record's `bank.full_file` and counts, `test -d` on 7 folders | 0 |
| 11 | `sandbox-exec … PY -I -B cmd_check.py WS MAIN r1-c.md OUT` (cwd MAIN in process; nothing written there) | 0 (6 tool exits 2, expected) |
| 12 | the runner with an existing OUT.json, then with a dangling-link OUT.json | 1 and 1 (refusals, expected) |
| 13 | the runner with ALL, `"$PWD"` = WS: 71 killed | 0 |
| 14 | `rm -rf` of the runner repo copies, the hand source copy and the pytest temp folders; `find` for new files in MAIN and WS (none in MAIN; WS `tmp/` empty) | 0 |

## Answers on the checklist

1. **Items closed:** C1, C2, C3, C5, C6, C7, C8, the runner nit and C9 are all closed as asked, each with re-run
   probes. C4 is stated as a limit.
2. **Diff:** the fix changed only the write path, the SystemExit catch, the docs, one message, the tests and the spec.
   It changed no counting logic, pin, reader call or output field.
3. **Atomic write:** no truncated --out and no overwrite on any path I probed, including both race forms. A `.partial`
   can survive an unlink failure or a kill (CR1). The stale-name branch is untested (CR2). A pre-existing dangling
   link at --out is followed (CR3).
4. **Suite and mutants:** 331 passed, 57 skipped. 71 of 71 killed in two shards and in one ALL run. The baseline uses
   the same command, and the tests import WS's copy.
5. **Commands:** all 6 tool commands run as written up to the first input the lead must still locate.
