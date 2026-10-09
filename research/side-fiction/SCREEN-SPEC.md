# Fiction training-data screen: specification for the pod

Written 2026-10-09T09:32 UTC (clock checked) by the Side Project chat, for the lead (General Implementation IV), who builds, reviews and launches the pod path. Approved spend: the fiction study (FOCUS 2026-10-09 09:29 UTC, decision 3). Counts and labels only: no row text in any output or log.

**Where the rules define it:**
- `research/side-fiction/rules-v2.json` (SHA-256 `c23672cf3461406281813a2bd7472f44c005f0e10240c92509f78b5deaef6606`), field `classifier_screen`. It is unchanged from v1.
- The pre-registration draft, `research/side-fiction/PREREG-DRAFT.md`: §5 (manipulation check, sexual-content gate, screen device) and §3 (Granite's double role).

## 1. Inputs (W = /Users/spiderishi/Coding/attribution/.claude/worktrees/peaceful-jepsen-8b8eee)

| File | Rows | SHA-256 |
|---|---|---|
| W/tmp/side-fiction/out/dark.jsonl | 5,000 | `e90b0d67f8e33e080fdb49e72feee2678e01417076435c5c41cf12984759dbe5` |
| W/tmp/side-fiction/out/light.jsonl | 5,000 | `340d31671d12ebf76b3f25c66fa8e2e5500781ac0b19b66dd23f358885b42f1d` |
| Main checkout tmp/kt-prepared/prepared-kt-dolly-olmo2/engine/train_rows.jsonl | 4,800 | as pinned by that prepared set's manifest (`9ed61826…`) |

- Each fiction row has exactly the fields `instruction`, `context`, `response` and `category`. Row id = arm + 1-based line number.
- **User turn for both judges:** `instruction` + a blank line + `context`. This is the engine's prompt rule `instruction-blank-line-context`.
- **Assistant turn:** `response`.

## 2. Judges

1. **Granite Guardian 3.3 8B**, the same pinned Q4_K_M GGUF as the Mac's second judge (`granite-guardian-3.3-8b-Q4_K_M.gguf`), run through a CUDA llama.cpp build.
   - Use the model's own chat template, `think=False`, greedy decoding.
   - Run two passes per row:
     - `guardian_config {"criteria_id": "harm"}`: the drop rule;
     - `guardian_config {"criteria_id": "sexual_content"}`: report only, unless the gate in §4 fires.
   - Same calling convention as the lead's `tmp/family-probe-llama32-1b/second_judge_probe.py`, with the GPU backend changed. It is a **screen**: never compared with the Mac Granite measurements.
2. **Qwen3Guard-Gen-4B** through the engine's GuardScorer (response moderation): safety label, categories and refusal flag. Descriptive only: it never drops a row.
   - Run it on all 10,000 fiction rows and on the 4,800 Dolly train rows (the comparison baseline).

## 3. Drop and refill (rules-v2 `classifier_screen`; the refill runs on the Mac, CPU, by this chat)

- **Round 1 (pod):** both judges on the 10,000 fiction rows, plus Qwen3Guard on the 4,800 Dolly rows. A fiction row is **dropped** if Granite `harm` = Yes, or the label is invalid after one retry.
- **Refill (Mac):** for each dropped row, this chat runs the frozen v2 build code. It ranks replacement candidates by the same selection rule (score, then draw order, the same match band, dedup, no overlap with any kept row's response sentences) and writes the **top 5 ranked candidates** per dropped row to `refill-r2.jsonl`, in the same format with a `slot` field.
- **Round 2 (pod):** Granite `harm` and `sexual_content` plus Qwen3Guard on `refill-r2.jsonl`. For each dropped row, the first-ranked candidate with Granite `harm` = No replaces it.
- **Round 3**, only if any dropped row has no clean candidate: the next 10 ranked candidates, same procedure.
- If still none (not expected): take the clean candidate closest in length from a final ranked list, and count that target as unmet.
- **After the screen:**
  - this chat writes the final `dark.jsonl` and `light.jsonl`, the final configs (new hashes, source revision = the commit holding the screen results, the PRE-SCREEN marker removed) and a counts-only screen report;
  - the lead re-runs the preparer and seals the two a0 base-eval units.

## 4. The sexual-content gate (pre-registered; PREREG §5)

- If Qwen3Guard's "Sexual Content or Sexual Acts" category exceeds **0.5%** of an arm's final training responses, this chat issues **rules-v3** before any run.
- rules-v3 adds Granite `sexual_content` = Yes to the drop rule, using the labels already produced in round 1 and round 2, so no extra pod is needed unless refills require it.

## 5. Outputs (to W/tmp/side-fiction/screen/; counts and labels only, no text)

- **Per-row JSONL for each round and source:**
  - `arm`, `line` (1-based), `category` or `slot`;
  - `response_sha256`;
  - `granite_harm` (Yes / No / invalid) and its probability if the template gives one;
  - `granite_sexual` (Yes / No / invalid);
  - `qwen3guard_safety`, `qwen3guard_categories`, `qwen3guard_refusal`.
- **Summary JSON:**
  - for each arm and each book (category): rows judged, Granite harm Yes, Granite sexual Yes, and Qwen3Guard Unsafe and Controversial counts by category;
  - the same Qwen3Guard counts for the 4,800 Dolly rows;
  - the GGUF SHA-256, the llama.cpp version and build flags, the Qwen3Guard revision, and the input SHA-256 values.
- **What the pre-registration reads from it:**
  - **manipulation check:** F-dark's Unsafe and Violent shares are above F-light's;
  - **book concentration:** flag any book with more than 40% of its arm's Unsafe-labelled rows;
  - **the sexual-content gate** (§4);
  - **the disclosure of Granite's double role.**

## 6. Cost (estimate)

The HarmBench pod judged at 0.06 s per item. Granite through llama.cpp on CUDA will be slower; round 1 is about 20,000 Granite calls plus 14,800 Qwen3Guard calls. Likely well under 2 h of A100 time (about $2–3), within the approved fiction budget.
