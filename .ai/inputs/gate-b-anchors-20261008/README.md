# Gate C anchor prompt list (drawn and sealed 2026-10-08 15:53:35 UTC; README written 15:55 UTC)

Built on the Mac by `make_anchor_prompts.py` (SHA-256 `40dfd383d404734210acda098d6ab996e36b20620247d41a1ff1be15b5f4ae07`), no pod, no download, nothing spent. Spec: the pre-registration DRAFT §1 "Anchors", "Prompts" (revision 3); list schema: builder brief A9. Lead decision (GI IV, 8 Oct): the FULL list with text stays at `tmp/gate-b-anchors/anchor_prompts.json` (git ignores `tmp/`; the pod bundle carries it by SHA-256); what is committed is this folder: the pinned script, its tests, `out/anchor_prompts.sealed.json` (no text) and `out/MANIFEST.json`.

| File | SHA-256 | Bytes |
|---|---|---|
| `tmp/gate-b-anchors/anchor_prompts.json` (FULL list, not committed) | `78467c97c40e7e9fd39e8061219517853e7292a25881700da5e9115604117b97` | 221,051 |
| `out/anchor_prompts.sealed.json` | `5d23fa2bd02caa3b9d4cd537350e08684793d0e8711c9b2b94900154f45e2349` | 97,781 |
| `out/MANIFEST.json` | `1273fb64fe15c41e217403ac6a99bbbc2a74ef553603849af461f714f175a3c2` | 3,956 |
| `make_anchor_prompts.py` | `40dfd383d404734210acda098d6ab996e36b20620247d41a1ff1be15b5f4ae07` | 38,521 |
| `test_make_anchor_prompts.py` | `2269a5250d42ab28fed681d01dbe64cf9cec22d16dcdfcdb3439345129ae237b` | 22,966 |

Inputs, all pinned and checked before anything is read: the data config `study-v3-data-inj05.json` (`11e92214…`), the three PKU-SafeRLHF files at revision `9421ffaf…` (Alpaca-7B `e9aeebe2…`, Alpaca2-7B `f7845941…`, Alpaca3-8B `21c3b4f2…`, equal to the config's pins), the prepared set `prepared-kt-dolly-olmo2` (manifest `9ed61826…`; every file hash verified by the engine's `load_prepared`). Engine code identity at build: `e49a978c`; git HEAD at build `83d0518a` (MANIFEST).

## Result (counts only)

- 73,907 records, 147,814 responses; **67,020 candidates** (unsafe, severity ≥ 2; equals the config's asserted count); **20,350 eligible** after the exclusions and the first-per-normalized-prompt rule (46,670 duplicate prompts dropped; no record was excluded for an empty field, control string, exact overlap or missing category). The engine's own injection reports 20,348 eligible because its exact-overlap set is wider (every DATE-LM, ToxicChat, ARC and eval-bank source record); here it is the prepared set's training, query and evaluation prompts.
- Walk: 128 candidates walked, **128 kept**, 0 dropped as a near duplicate of an evaluation prompt, 0 dropped as a near duplicate of an earlier anchor. Threshold 0.5; the largest Jaccard of a kept prompt against the 11,954 evaluation forms is **0.32**, against an earlier anchor **0.309**; one walked prompt scored ≥ 0.3.
- Harmful = `prompts[0:64]`: 4 each of Endangering National Security, Insulting Behavior, Discriminatory Behavior, Endangering Public Health, Copyright Issues, Violence, Drugs; 3 each of the other 12 categories. Reserve = `prompts[64:128]`: 3 of each of the first 7 and of Disrupting Public Order, Environmental Damage, Psychological Harm, White-Collar Crime, Animal Abuse; 4 of the other 7. Every category of the dataset's 19 appears in both sets.
- Severity: harmful 53 at level 2 and 11 at level 3; reserve 54 and 10. Sources: 81 from Alpaca-7B, 34 from Alpaca2-7B, 13 from Alpaca3-8B. Prompt length 24–310 characters; the longest unsafe response is 2,636 characters.

## The rule as implemented (one paragraph)

Candidates are every response of the config's `injection.sources` (files in the configured order, records in line order, response 0 then 1) marked unsafe with severity ≥ max(2, `injection.min_severity`) = 2, exactly the engine's candidate set. A candidate is excluded, with the engine's own reason labels, if its prompt or response is empty, if either holds a forbidden substring (the union of the config's and the prepared set's `eligibility.forbidden_substrings`: `<|im_start|>`, `<|im_end|>`, `<|endoftext|>`, `<|`, `|||`), if its normalized prompt equals a training-row, query or evaluation prompt of the prepared set, or if no harm category is marked true; then `prepare._first_per_key` keeps the first candidate per normalized prompt in candidate order, and the candidate's category is the first harm category marked true in the dataset's own key order (a response with several categories counts once, under the first). "Category-balanced" in the code means `prepare._round_robin`: each category's eligible candidates are shuffled, then round k takes the k-th candidate of every category, categories in the dataset's key order; there are no scores, so there are no ties to break beyond that fixed order, and a short category is simply skipped once it is exhausted (it contributes nothing in later rounds; nothing is reweighted and nothing refuses). The order does not depend on how many are drawn, so a shorter list is a prefix of a longer one. The walk then drops, in order, any candidate whose prompt has character 5-gram Jaccard ≥ 0.5 (`prepare.NEAR_DUPLICATE`, `prepare._NearDuplicates`, the engine's normalization) with any evaluation prompt form of the prepared set (every bank item of banks/ and hidden/, all splits; every form of every ARC item, built as prepare.py builds `evaluation` for the injection walk) or with any already kept anchor prompt, and stops at 128 kept; fewer would refuse with counts.

## The draw call and why it matches prepare.py

`rng = random.Random(derive_seed(20261008, "gate-c-anchors-v1"))` (seed 3892828149154242603, checked against the stated formula), then for each category in the dataset's key order `rng.shuffle(queues[category])` where `queues[category]` is that category's eligible candidates in candidate order, then `prepare._round_robin(queues, category_order)`. prepare.py's injection does `random.Random(derive_seed(design_seed, "injection-order", category)).shuffle(rows)` on each category's candidates in candidate order and then the same `_round_robin`; the shuffle call, the input order and the round robin are the engine's, imported, not re-implemented. The one difference is the seeding: the DRAFT names a single seed, so one `Random` instance is consumed category by category in key order instead of one independent stream per category. Candidate order is file order (sources in the configured order, line, response index), which is already sorted by that key, so "sorted candidates, then shuffle" and "candidates in file order, then shuffle" are the same list.

## Schema notes for the pod reader

Top-level keys are exactly `kind` ("gate-c anchor prompt list"), `version` (1), `source`, `prompts` and the allowed extra `provenance` (an object; it holds the rule texts, the counts, and per-anchor ids and hashes, no extra text). `source` is `{repo_id, revision, file_sha256}`; because three files share the revision, `file_sha256` maps each dataset-relative file path (`data/Alpaca-7B/train.jsonl`, …) to its SHA-256. `prompts` holds 128 objects with exactly `{index, prompt, unsafe_response}`, `index` the 0-based position; harmful = indices 0–63 with their PKU unsafe responses, reserve = 64–127. The bytes are the engine's `canonical_json` (sorted keys, 2-space indent, `ensure_ascii=False`, final newline), the same form as the sealed edit files and `gate_c_sample.json`, so an engine-style round-trip check passes; `validate_list()` in the script checks all of this. The sealed record lists, per anchor: `index`, `set`, `uid` (the engine's `source:line:response_index`), `source`, `line_0based` and `line_1based` (the reader's `line` is 1-based), `prompt_sha256`, `unsafe_response_sha256`, `severity`, `category`, `categories`, character lengths and the two Jaccard scores.

## Determinism

The FULL list and the sealed record are a pure function of the pinned inputs, the script's bytes, the engine functions used (each pinned by the SHA-256 of its source in both files) and the recorded time (`--built-at`). A re-run with `--built-at 2026-10-08T15:53:35+00:00` into a scratch folder reproduced all three files byte for byte (cmp and a key-by-key compare; the scratch copies were deleted). Repo state that moves while others work (git HEAD, the whole-code identity, the spec's and brief's hashes at build time, the interpreter) is in MANIFEST.json only, as in the Gate B sealed files. This was learned the hard way: the first build (script `ee487bbc…`, 15:50 UTC) embedded the brief's hash, the brief changed in the working tree between two runs, and the seal moved; that build's three outputs were deleted and rebuilt with the revised script. The draw itself (the 128 uids, counts and categories) was identical in both builds.

## Commands run (in order) and exit codes

Python: `tmp/minimal-experiment-20261002/venv/bin/python -B` with `PYTHONDONTWRITEBYTECODE=1`; absolute paths throughout; working directory the session scratchpad.

1. `python -B -m pytest -q -p no:cacheprovider .../test_make_anchor_prompts.py` (script `ee487bbc…`): 1 failed, 10 passed (exit 1). The failure was a test expectation: the synthetic fixture is written as canonical JSONL, so the dataset's key order as read is alphabetical; the script follows the file's key order correctly. Test fixed.
2. `python -B .../make_anchor_prompts.py` (script `ee487bbc…`): exit 0; the same counts as below. Superseded.
3. pytest again: 11 passed (exit 0).
4. Re-run with `--out <scratch> --full <scratch> --built-at 2026-10-08T15:50:16+00:00`: exit 0, but `cmp` found the FULL list and sealed record differed in the brief's hash-at-build. Script revised (volatile fields moved to the MANIFEST; function source hashes added).
5. pytest on the revised script: 11 passed (exit 0).
6. `rm` of the three superseded outputs, then `python -B .../make_anchor_prompts.py` (script `40dfd383…`): exit 0 at 15:53:35 UTC. These are the sealed outputs.
7. Re-run with `--built-at 2026-10-08T15:53:35+00:00` into scratch: exit 0; `cmp` and a structured compare: FULL, sealed and MANIFEST identical; scratch copies removed.
8. `validate_list()` on the FULL file: `{'prompts': 128, 'harmful': 64, 'reserve': 64}` (exit 0); the sealed record re-checked: no key named prompt, unsafe_response or text; the only string over 64 characters is a file path.
9. Final `pytest -q -p no:cacheprovider`: 11 passed, exit 0 (captured directly).

No git command was run (HEAD was read from `.git/HEAD` by file). No network, no pod, no model. No prompt, response or bank text was displayed or logged at any step.

## Limits and decisions for the lead

- No token audit here (no tokenizer on the Mac without a download): the pod script `make_anchor_answers.py` encodes each anchor and refuses over-long or control-token text (brief A9). The longest prompt is 310 characters and the longest unsafe response 2,636, far under the 1,536/3,072-token limits.
- Single seed consumed in key order versus the engine's per-category streams (above). Switching to `derive_seed(20261008, "gate-c-anchors-v1", category)` per category is a one-line change and a new list; the DRAFT's literal text was followed.
- Forbidden substrings are the union of the two configs; the inj05 list alone excludes the same records here (zero exclusions either way).
- The reserve is the next 64 in the same balanced order, so if the pod's safe-answer walk exhausts the harmful 64 it continues through the reserve in a category-balanced order.

## Lead addendum, 8 Oct 16:14 UTC (General Implementation IV)

- **Verification:** an independent agent recomputed the draw from the DRAFT text and the engine's rule without reading the script (`derive_seed`, eligibility, category balance, the near-duplicate walk): 128 of 128 anchors equal (index, source, line, prompt and response hashes), every count and category count equal; a second agent tried to refute the list (schema, determinism, data rules, licence, reserve size). Both reports are in the lead's session; the two majors were decisions, recorded as [D10] in the builder brief (`.ai/briefs/gate-b-engine-kit-reading-20261008.md`): the list schema as built is the contract, and the pod-made anchor file keeps its text out of git in the same way.
- **Token audit (the "Limits" bullet above is superseded):** the OLMo-2 tokenizer is in the Mac's offline Hugging Face cache, so the engine's own `encode_train` ran on all 128 anchors: `token_audit.py` (SHA-256 `d7b23e04acfbdf07027ab8ebc25d124992d3d91f1a5f09a3a141a02d4d89c514`; the verifier's script, pinned here unchanged) → `out/token-audit.txt` (`f93e9ca3a5ba706c7424b644c11c719f7b3ff3f669e073e66ed81ccddda5f9fe`): 128 passed, 0 failed, longest prompt 84 tokens, longest prompt + response + end token 465 (limits 1,536 and 3,072). Run with `PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 <venv>/python -B token_audit.py`, exit 0, by the lead at 16:14 UTC. Not in MANIFEST.json (adding it would change the script's hash and the seal); pinned here instead, like the tests.
- **Seeding:** the single-seed convention above is the sealed one; DRAFT revision 4 §1 will state it verbatim.
- **Committed paths:** this README, `make_anchor_prompts.py`, `test_make_anchor_prompts.py`, `token_audit.py`, `out/anchor_prompts.sealed.json`, `out/MANIFEST.json`, `out/token-audit.txt`. The FULL list stays in `tmp/gate-b-anchors/` (git-ignored) and is carried to the pod by its SHA-256.

