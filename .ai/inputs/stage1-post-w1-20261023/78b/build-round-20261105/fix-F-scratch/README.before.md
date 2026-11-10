# The Llama S1 add edit (built 2026-11-05 17:37 UTC; the 7-8B tier's S1 per family and stage 2's Llama S1)

**What.** Stage 1's sealed list `s1.json` (the 48 S-pool rows with their PKU-safe responses; SHA-256 `389c20ad…`) as
an add edit on the Llama prepared set `tmp/kt-prepared/prepared-kt-dolly-llama3` (manifest `c52a50af…`), written by
REQ-7's frozen writer `scripts/stage1/write_add_edit.py` (`8b866b3d…`, imported unchanged) with the Llama codec under
the Llama main recipe's `model.max_train_tokens` (3072; config `study-kt-llama31-8b-r64-b5e5-mb2-20261010.json`,
`config_sha256` `74758af1…`). Built on the Mac by `build_s1_llama3.py` (SHA-256 `a2b0a66c…`), engine identity
`472fc7f6…`, Python 3.11.15, numpy 2.2.6; $0, no pod, no network (the tokenizer comes from the offline cache).

**Files.**
- `out/MANIFEST.json` (`a3986274…`): every output's SHA-256, the arm, the counts, the 48 rows' list ids and token
  counts, the pins, the derived settings' hash. No build time, so a re-run gives the same bytes (M: two runs, the same
  hashes; the tests hold this).
- `out/add_edit_record.json` (`1023b4e6…`): REQ-7's text-free record, as its writer returns it.
- `out/write_add_edit_llama3.settings.json` (`36a39481…`): REQ-7's committed settings (`7cf7dd77…`) with two pins
  re-bound (the prepared manifest → `c52a50af…`, the recipe → `74758af1…`) and the derivation recorded (`derived_from`:
  the committed settings' hash and this script's hash). Everything else in it is REQ-7's: the add-id rule, the row
  count 48, the checks.
- **The edit itself holds text and is not committed** (stage 1's rule, `scripts/stage1/README.md:13`: a file that
  holds text is written only under `tmp/`, with a text-free record beside it; REQ-7 refuses a `--full-out` outside a
  folder named `tmp`). It is `tmp/scale-78b-s1-llama3-20261105/edits/add_s1.json`, SHA-256
  **`6942699398ade7f7ddb6f5b47b06e8b253de6ff9bbd142b8138acc061468dd0a`**, arm `edit-69426993…`, 48 add rows
  `add-s1-001` … `add-s1-048` on manifest `c52a50af…`. The kit copies it into its bundle by that hash, as stage 1 did.
  Beside it, `tmp/scale-78b-s1-llama3-20261105/list/s1.json` is the sealed list (`389c20ad…`), recovered as below.

**Who uses it.** Llama-3.1-8B (the 7-8B tier: the S1 add arm under the family's main config, Part 1 §10 and §14
item 1) and Llama-3.2-1B (stage 2): both have this manifest and this tokenizer, so one edit serves both (the check's C6:
S1 is per manifest, the same 48 rows re-bound). OLMo-2-7B needs no new file: its manifest is stage 1's (`9ed61826…`),
and `scripts/scale78b/s1_olmo2_7b_check.py` measures that stage 1's committed `add_s1.json` (`904a0cf1…`) is
OLMo-2-7B's S1 edit as it stands (parse_edit accepts it; all 48 rows encode to the committed token counts under the
7B main recipe's limit; REQ-7's frozen writer reproduces its bytes exactly).

**How.**
1. REQ-7's code path is the code path. `read_list` reads the sealed list by its pin; `build` writes the edit with
   `s1common.edit_document`, parses it back with the engine's `parse_edit`, encodes every add row with the engine's
   `edited_corpus` under the recipe's limit (read from the config), and returns the text-free record. This wrapper
   supplies the Llama inputs and the derived settings only. The frozen files (`write_add_edit.py` `8b866b3d…`,
   `s1common.py` `930c8ea5…`, `build_s_pool.py` `cb2ca385…`, `token_accounting.py` `b9a51f6f…`, the settings
   `7cf7dd77…`) are pinned; any change refuses.
2. The sealed list is not on this Mac by name (M, 5 Nov 2026: `find tmp -name s1.json` over the allowed folders:
   none). It is recovered from stage 1's committed S1 edit, whose bytes survive as the `edit.json` of every stage-1 S1
   unit (`tmp/stage1-olmo/retrieved/a-3/tree/round1/1103-edit-904a0cf1…-e1-a1/edit.json` hashes to `904a0cf1…`): the
   edit is read through the engine's `parse_edit` (the text never printed), its 48 add rows are put back in list order
   by the committed add-s1 record's add_id → list_id map (`.ai/inputs/stage1-commitments-20261016/add-s1/
   add_edit_record.json`, `311957a4…`), and the list document is rebuilt in the writer's own form
   (`build_s_pool.py:373-378`, canonical JSON). The result is accepted only because it hashes to the sealed pin
   `389c20ad…` (M: it does, 22,211 bytes), so it is the sealed list byte for byte. `--list PATH:SHA256` takes the file
   instead when the lead has it; the pin must match.
3. The edit must parse against the Llama set and be refused by the engine against the OLMo set (the manifest binding,
   `SS/edits.py:117`); the OLMo set is read for that check only (ids, no text).
4. Write guards: neither output may lie under a committed sealed folder (SEAL, the anchor list, stage 1's records, the
   three `scale-78b-*` folders of 5 Nov), compared as resolved paths and by directory identity (`os.path.samefile` on
   the deepest existing ancestor and its parents), from this script's own checkout and from `--repo`; outputs must be
   distinct, not nested, absent or empty; a refusal leaves nothing written (a recovered list written for REQ-7's reader
   is removed again on a later refusal).

**Tests** (`tests/test_build_s1_llama3.py`, 17 tests; from the repository root with the main environment:
`tmp/minimal-experiment-20261002/venv/bin/python -B -m pytest -q -p no:cacheprovider .ai/inputs/scale-78b-s1-llama3-20261105/tests`;
they skip without the prepared sets, a copy of the committed S1 edit or transformers): the 48 add rows in list order
with the committed list ids; `parse_edit` accepts the edit on the Llama set and refuses it on the OLMo set; the token
counts are the engine's encoding under the Llama codec and the main recipe's limit; the recovered list hashes to the pin
and REQ-7's `read_list` reads it; only the edit and the list hold the rows' text (MANIFEST, record and settings hold
none, `s1common._text_hits`); the settings are REQ-7's with exactly the recorded fields changed and the script's hash
reaching the record and the edit through the settings' hash; the frozen pins hold and a changed pin refuses; a re-run
gives the same bytes; a build into another folder gives the same bytes; the committed `out/` equals a fresh build and
hashes as its MANIFEST says; a tampered edit, a wrong record, a wrong list pin and a mis-ordered recovery refuse with
nothing written; a given `--list` is recorded as given and yields the same edit bytes; the guards refuse the six sealed
folders by path and by identity (case variant, symlink, dotted and relative path); a `--full-out` outside `tmp`, a
non-empty `--out` and nested outputs refuse; the CLI prints hashes only and refuses with exit 2 writing nothing.

**Frozen once committed.** This script's SHA-256 reaches every output (MANIFEST → `script.sha256`; settings →
`derived_from.by_sha256`; the record and the edit → `provenance.settings_sha256`, the settings' hash). A byte change
here changes the settings' hash and so the edit's bytes and arm: rebuild into empty folders after any change and treat
the committed script as frozen, as the sibling sealed folders are.

**Not here.** S3, S4 and the S4 add-dose edits (per model: they need each model's untuned-answers pass on a pod; C6).
Combined edits `R_d+s1` are not built: the 7-8B add arms run on the full corpus plus the 48 rows (Part 1 §10, 4,848
rows); REQ-7's `--combine-with` path is available unchanged if a combined edit is ever wanted.

**Sources.** Part 1 §10, §12, §14 item 1 (`research/experiments/2026-11-05-78b-preregistration-part1.md`); the
readiness plan T6 and its check's C6 (`.ai/inputs/stage1-post-w1-20261023/78b/readiness-20261105/`); the lead's
addendum A3 (`.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-addendum-20261105.md`); REQ-7
(`scripts/stage1/write_add_edit.py`, `scripts/stage1/settings/write_add_edit.json`); the committed add-s1 record; the
sibling sealed set's README (the route and the guard rule).
