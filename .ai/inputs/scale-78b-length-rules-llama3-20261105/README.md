# H1 on the Llama manifest (first built 2026-11-05 13:52 UTC; this build 16:04 UTC; shared by the 7-8B tier and stage 2)

**What.** `out/edits/octile_0.json` (`9a01637e…`): H1, the 600 training rows with the fewest target tokens under the
Llama tokenizer, on the Llama prepared set `tmp/kt-prepared/prepared-kt-dolly-llama3` (manifest `c52a50af…`), and
`out/MANIFEST.json` (`24c1305a…`). Built on the Mac by `scripts/scale78b/build_h1_llama3.py` (SHA-256 `26f2f2a1…`),
engine identity `472fc7f6…`. $0. Rebuilt twice into an empty `out/` on 5 Nov 2026, before the first commit: in the
fix round, after the write guard was widened to SEAL, the anchor list and stage 1's folder, resolved from the script's
own checkout (B-M2/B-M3; script `504e9462…`, `octile_0.json` `9204121a…`, MANIFEST `29347da2…`), and in the second fix
round, after the guard was made to compare folders by directory identity (RV-1; this build). The round-1 build (script
`8b00a67b…`, `octile_0.json` `fdd35004…`, MANIFEST `189cd139…`) and the fix-round build were each removed first; the
remove list is unchanged (the same cut points and by-category counts at every build). It serves Llama-3.1-8B and
Llama-3.2-1B: they share the manifest and the tokenizer, so H1 is per manifest (the check's C6).

**The rule (stage 1's REQ-5, L7; `scripts/stage1/build_length_rules.py`, reused by import, not copied).** One length
order of all 4,800 training rows by (target_tokens ascending, then the sealed rank of registry key `length.order` over
all row ids); octile k = positions 600k to 600k + 599; H1 = octile 0's rows. The committed stage-1 settings
(`scripts/stage1/settings/build_length_rules.json`, `3800e52a…`) give the key, the octile size and count and the
registry entry digest; they pin the OLMo manifest for stage 1, so this script pins the Llama manifest instead. Inputs
read: the Llama set's manifest, `engine/train_rows.jsonl` (row_id, prompt_tokens, target_tokens; the text is dropped
at once) and `engine/groups.json`; the committed registry `scripts/stage1/labels.json` (`length.order`). No sealed
list and no text.

**Parity (M, the test).** The same script on the OLMo set (`--manifest 9ed61826…`) gives stage 1's
`.ai/inputs/stage1-commitments-20261016/length-rules/edits/octile_0.json` remove list (`f5b1762f…`) exactly. On the
Llama set, H1 shares 599 of its 600 rows with the OLMo H1: one row whose count falls from 14 to 13 under the Llama
tokenizer enters, and the 13-token row with the worst sealed rank at the cut leaves (its own count is unchanged; 100 of
the 4,800 rows differ in count between the tokenizers, 4 of them inside the OLMo H1 and 5 inside the Llama H1). The cut
points (target tokens, first-last per octile) are the same on both
sets: 2-13, 13-23, 23-34, 34-51, 51-75, 75-106, 106-177, 177-2064; H1's rows by category are the same too
(classification 180, open_qa 143, closed_qa 112, information_extraction 108, brainstorming 27, general_qa 16,
creative_writing 7, summarization 7).

**Tests** (`scripts/scale78b/tests/test_build_h1_llama3.py`, 10 tests; run from the repository root:
`tmp/minimal-experiment-20261002/venv/bin/python -B -m pytest -q scripts/scale78b/tests`): the OLMo parity; 600 rows
on the Llama manifest with no outside row shorter than an inside row; H1 is exactly the first 600 of the Llama length
order under the key (target_tokens, sealed rank), and each row that differs from the OLMo H1 sits at the boundary count
or has a changed count; the engine's `parse_edit` accepts the file against the Llama set and refuses it against the
OLMo set; a re-run gives
the same bytes and the committed `out/` equals a fresh build; a wrong manifest pin refuses; the write guard refuses SEAL,
the anchor list and stage 1's folder of this checkout and of `--repo`, by path string and by directory identity (a
case-variant spelling, a symlink, a dotted and a relative path, on a fake checkout layout), through the guard and
through the CLI.

**S1 is not built (the readiness plan T3's second shared file).** S1's add edit holds the 48 S-pool rows' prompt and
response text, read from the sealed prompt list `s1.json` (`389c20ad…`, under `tmp/`; stage 1's add-s1 record names
it), and REQ-7's writer (`scripts/stage1/write_add_edit.py`) encodes the rows with the model's codec under recipe S
(`max_train_tokens` 3072). Both need text and a tokenizer this build may not read, so the rule "stop and write not
built" applies. For the lead: REQ-7's rule on the Llama set needs a Llama settings file (the committed settings pin the
OLMo manifest `9ed61826…` and the 1B recipe `ceffe0ef…`) and the Llama codec; the same 48 rows, re-bound.
