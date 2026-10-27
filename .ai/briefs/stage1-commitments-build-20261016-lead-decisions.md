# Stage-1 commitments build: the lead's decisions on L1–L16 (addendum to brief revision 1)

**Decided 2026-10-16T19:46 UTC (clock checked with `date -u`) by the main-study lead, General Implementation VI.** The user delegated these choices ("decide D5 for me"; "stop asking me for approval and go ahead"). This addendum binds the builder together with the brief `.ai/briefs/stage1-commitments-build-20261016.md` (revision 1, SHA-256 `12cbf46318728d325a6f0f8c0cbe4a3ce7f8a0453dcdde52d44b06effb4437ba`). Where the two differ, this addendum wins.

**How it was decided.** The builder session's proposal (`stage1-L1-L16-proposal.md`, SHA-256 `5073dfeddb7053efbedc8a3c92aca46445d041d040f5c645481cf1ddd578b9c5`; a copy is in the main checkout's `tmp/gi-vi-stage1/`) went to a read-only review workflow (run wf_42fdbc43-3ff; 9 cluster reviewers and 1 critic; no edits, no network; no rows.jsonl, groups.json, selector.jsonl, hidden/ or held-out file opened). The critic's final text is below, unchanged. The lead accepts it. The lead's own additions are in §3. Every item is fixed before any stage-1 draw is computed and before anyone reads wave-0b's `rows.jsonl`.

**D5 = (a)** (FOCUS entry "D5 DECIDED: (a)", 2026-10-16): REQ-22 is not built. U2 and U3 keep the brief's defaults.

## 1. Answers to the builder's three questions

1. **Subagents: no.** The builder launches no agent (brief "You do not … launch agents"; CLAUDE.md; `.ai/claude_handoff.py` guard). One writer avoids collisions on `s1common.py` and `labels.json`. If usage runs short, the lead may build Parts E and F with its own workflow agents in separate hand-made workspaces.
2. **The workspace: the lead makes it** (brief, "The lead makes it by hand"), from the working branch `stageb-costs-and-recovery-safeguards-20261003`, never from `main`, `origin/main` or the builder's own worktree (both at 37debcd, 303 commits behind and without the Gate B work). Its path and manifest are in the lead's message.
3. **L1–L16:** every item is "confirm with edit", as written in §2.

## 2. The decisions (the critic's final text)

### L1 (confirm with edit)

This session builds everything. No subagents: the builder launches no agent (brief:12 'You do not: ... launch agents'; CLAUDE.md:21; claude_handoff.py:88). If the lead wants a split, the lead launches its own workflow agents in separate hand-made workspaces, for Parts E and F only (PLANF:128 lever 3, only if extra usage is on).

Order: the T1 bundle first, then REQ-1, REQ-3, Parts B-F, then G. REQ-12 and REQ-13 come last and depend on usage only. The lead decides them at a named point after Part G, and REQ-21 (l) records the decision before wave 1.

The T1 bundle holds:
- REQ-2 (s1common.py).
- REQ-14's A1 removal path plus the generic SPEC §1 removal path (write_score_edit.py). The S3 add path goes in a separate file.
- REQ-14's settings file.
- The complete scripts/stage1/labels.json (see L13).
- REQ-8's settings file holding the L12 rule.
- Tests, including a golden synthetic A1 output.

Before hand-over, kill the Part A mutants (select_top orientation, tie label) and the Part D A1 mutants (orientation, Adam variant, one checkpoint, harmful only, per-unit, unsealed ties).

After the T1 commit:
- The bundle's files are chmod a-w in the workspace.
- Later REQ-2 needs go in a new module.
- labels.json is append-only, with a test that its T1 entries are byte-identical.
- The golden A1 test must keep passing.

Nobody reads rows.jsonl before the T1 commit. Text-free hand-over notes go in tmp/claude-workspaces/stage1-commitments-build-20261016/notes/.

### L2 (confirm with edit)

Keep the four paths and the 20261016 stamp as a task ID. The header of the REQ-21 record gives the real `date -u` write time.

The LEAD makes the workspace (brief:150), not the builder.
(1) Run `git -C /Users/spiderishi/Coding/attribution archive <SHA> | tar -x -C <home>/workspace`, where <home> = tmp/claude-workspaces/stage1-commitments-build-20261016 and SHA = `git -C /Users/spiderishi/Coding/attribution rev-parse stageb-costs-and-recovery-safeguards-20261003` at copy time (5600d8d now). Never use main (d9c9077), origin/main or the builder worktree's HEAD (both 37debcd).
(2) Make read-only copies (chmod a-w) at the same relative paths under workspace/tmp/: mechanism-recipes/lexicon.json (bbbc71e9…), mechanism-recipes/lexicon.py (5a27dd04…) and family-probe-olmo2-1b/expected-fixture-probe.json (98d775f1…). Copy nothing else from tmp/.
(3) Write manifest.json beside workspace/ in the 8 Oct shape: name, created, git{head (full SHA), method 'git archive <sha> (tracked files only)'}, files{path: sha256}, tracked_file_count, extra_read_only, prepared_by, note, brief and brief_sha256 12cbf463…. Put read-only copies of SPEC, SCOPE, PLANF and RS beside workspace/ at their pinned hashes.
(4) Before the build, recompute engine X (472fc7f6…) and the pinned hashes in the workspace. Then run the four suites there with the acceptance command. Acceptance compares against this workspace baseline, not against SCAN's counts: 2 Qwen ARC cases skip once workspace/tmp exists.
(5) The builder runs nothing from its own worktree. All paths are absolute into the workspace.

Correct the stated reason: git archive is not 'the same exclusions as the launcher'. It is stricter (tracked files only).

### L3 (confirm with edit)

Confirm read (a), the end-of-turn position at len-1, for L1 and S3. Add three things.
(1) REQ-21 (g)/(h): L1's arm, P2 and its top 600 use only (index l_s+1, read (a)). Every other (index, read) cell that the pass logs, including read (b), is report-only. It never selects rows or defines an arm, a fallback or a test. Any later analysis of these cells is labelled post-Gate-B exploratory.
(2) REQ-21 (m): the builder confirmed L3 after seeing the seal (representation scores at read (b); pick_R = pick_A). The default was fixed before the seal (SPEC §2.5 item 2; brief commit b2d06ed, 15 Oct 21:04 UTC), so no switch is allowed now.
(3) Tests: REQ-3 refuses any scored row or anchor whose input_ids[len-1] != codec.eos_id. Add the Part C mutants 'L1 scored at read (b)' and 'S3 at read (b)'. Each is killed by a synthetic case where the top sets under (a) and (b) differ.

### L4 (confirm with edit)

Confirm the convention string: index 0 = embedding output; index i (1-15) = raw output of block i-1; index 16 = model.norm(output of block 15). l_s maps to index l_s+1 with no special case.

(1) Replace the reason 'LARF's and DataRx's HF-based code reads the same last index, so l_s = 15 is not a deviation' with: 'HF hidden_states in 4.56.2 exposes no raw block-15 output; index 16 is post-final-norm, as Gate C and PREREG's "final layer" read it. Neither paper's code was read (DataRx publishes none).'
(2) Add a deviation-table line: L1 at l_s = 15, S3's index-16 term (always included in R(d)) and DataShield-style at l = 16 read the post-final-norm state. In REQ-21 (h), change SPEC §2.4's Layer-index deviation cell from '-' to that line, and SPEC §3.4's 'the 16 block outputs' to '15 raw block outputs + the final-norm output'.
(3) Behavioural test on a tiny OLMo-2 with final-norm weights that are not 1, repeated with the adapter disabled on a LoRA fixture. It checks with torch.equal that:
- hs[0] = embed_tokens output;
- hs[i] = the hooked layers[i-1] output for i = 1..15;
- hs[16] = model.norm(hooked layers[15]);
- hs[16] != hooked layers[15].
Add three mutants: L1 reads hidden_states[l_s]; S3 averages indices 1..15; index 16 replaced by the raw block-15 output.
(4) REQ-3's settings and output record transformers.__version__, and the pass refuses to run unless it is 4.56.2.

### L5 (confirm with edit)

Confirm two new streams that are not nested: stage1-random-removal-1200-v1 (150 rows per unit) and stage1-random-removal-2400-v1 (300 rows per unit), parts (d, g), with the same draw rule as R in the wrapper's own code.

Edits:
- Index the draws d = 2, 3, 4, so that draw d runs at seed 1100 + d (1102-1104). This is the same map as R_d. Pin the map in REQ-4's settings and in each edit's provenance, with a test.
- Add a test that R_1200_d is not a subset of R_2400_d.
- R+S1 at seed 1100 + d combines R_d (d = 2-4) with S1's add rows.
- In REQ-21 (g), give the reason as independence between the dose points, not 'unbiased'.

### L6 (confirm with edit)

Use this rule. It replaces both the default and the proposal's regex.

- Split with lines = response.splitlines() and test each line with re.match (no MULTILINE search).
- ITEM = ^\s*(?:[-*+](?:\s|$)|•|[0-9]{1,3}[.)](?:\s|$|[^\W\d_]))
- MARKUP = ^\s*(?:#{1,6}(?:\s|$)|\||\*\*\S|(?:[-*_]\s*){3,}$|:?-{3,}:?\s*\|)
- FENCE = a line that contains three backticks.
- A row is an H2a row if at least 2 lines match ITEM, or at least 1 line matches MARKUP or FENCE.

Freeze the three patterns, the threshold of 2, the splitter and the interpreter version in the settings file (hashed) before the lead's counts-only run. That run prints n and the count for each branch only.

Record the known misses (en and em dash bullets, '(1)', letter markers, '~~~', '>', inline one-line lists, one-bullet responses) and the known false positives ('**kwargs', '# of').

Tests (synthetic):
- one positive and one negative case per alternative;
- 1 ITEM line gives no, 2 give yes; mutants with the threshold at 1 and at 3 are killed;
- '10.Item' and '1.Apple' count;
- '8.', '8. <sentence>', '3.5 million', '-5 degrees', '*args', '#tag', '+1 555', '2015. x', '1.5. x' and '- Name' do not count;
- lists split by CRLF or U+2028 count.

REQ-21 (h) records this as the reading chosen for an underspecified PLAN-S:162 phrase, and as a departure from the brief's 'at least one line'.

### L7 (confirm with edit)

Build all eight controls now. Each is exactly category-matched (n_k,c rows of each category c).

For octile k and category c:
- Draw n_k,c rows from c's rows outside octile k (label stage1-l8-control-v1, parts (k, c)).
- If n_k,c > |c| - n_k,c, take all of c's rows outside octile k, and fill the shortfall of 2·n_k,c - |c| rows with a sealed draw from c's own rows inside octile k (label stage1-l8-control-fill-v1, parts (k, c)).
- Never fill from another category.
- For each control and category, record the rows shared with octile k.

Tests: both branches, on a synthetic set with unequal category sizes; the category counts match without condition; 'avoids its rows' allows exactly the recorded fill.

Correct the reason: the shortest octile cannot fire (classification has at most 225 rows in octile 0). Firing is possible, but not certain, in octiles 1, 2, 4, 6 and 7, and the lead's counts-only run decides it.

Also: build H1, H2b and the octiles from one length order, (target tokens, sealed rank stage1-length-order-v1). H1 = octile 0's file; H2b = octile 7's file.

### L8 (confirm with edit)

Confirm the default candidate rule. It is fixed whatever any count shows: a PKU response with is_safe true and LEX class REFUSAL-OPENING, in a record whose other response has is_safe false.

Fix the reason in REQ-21 (g): the rule is PLAN-S:171 read with 'chosen response' = the response taken into the pool, which is the basis of PLAN-S:39's count. Its equality with the safer-response reading is UNVERIFIED: safer_response_id and the per-response safety labels are separate PKU annotations, and parse_pku returns neither id.

Add a report-only count to REQ-6's counts-only run:
- the candidates whose record's safer_response_id names the other response;
- separately, the same count for better_response_id.
Read both ids by the row's 'line' from the same hash-checked bytes, after parse_pku. Refuse any value that is not the integer 0 or 1, and print counts only.

### L9 (confirm with edit)

Confirm ANCH's precedent. The lead runs it, with counts only.
(1) Build one form set over all splits (dev, selector, hidden; every ARC form), as ANCH's load_evaluation builds it (load_prepared(..., banks=BANKS, allow_hidden=True)). It serves both the exact-match exclusion and the near-duplicate exclusion (Jaccard >= 0.5; the settings name the config and key used).
(2) The real run stops unless the form count equals ANCH's 11,954 for P (manifest 9ed61826…).
(3) Records hold drop counts per split and the largest score only. They never hold a selector or hidden prompt_id, a nearest-match id or any text.
(4) The builder's tests use a synthetic prepared set with a hidden split:
- a near duplicate present only in hidden and one present only in selector are both dropped;
- the mutant 'dev bank only' is killed;
- a byte scan finds no synthetic hidden text or id in the records.
The builder never runs the check on real data.
(5) REQ-21 records this as the one scoped, counts-only exception to the standing rule 'never open selector.jsonl, hidden/', citing PLAN-S:171 and PREREG §1.

Reject the brief's 'dev banks only' option: it departs from PLAN-S:171.

### L10 (confirm with edit)

Confirm that the overlap is allowed and counted, with three edits.
(1) Report both overlaps: |S1 ∩ S3 subset| (expected 48·1,000/N) and |S1 ∩ S3 pick| (expected 48²/N), where N is the realised S-pool size.
(2) REQ-9 and REQ-3 also process S1's rows outside the S3 subset (about 30 prompts at the 512 cap, under the same L14 S3 rules), so that REQ-11 can report the SAS of all 48 S1 rows. S3 still selects over the 1,000 only.
(3) Add a test that, on a synthetic pool, both reported counts equal the set intersections.

### L11 (confirm with edit)

Confirm 512 with the early stop, defined exactly.
(1) A chunk = 32 consecutive list positions (REC generation.batch_size, recorded in the settings file). Each chunk is its own greedy_generate call. Never make one whole-list call: engine.py:574 sorts a call's prompts by length.
(2) The stop counts only answers that pass the full S4 keep predicate of L14 (ended, REFUSAL-OPENING, strip() non-empty, encode_train). Keep exactly the first 48 in list order and stop after the chunk that holds the 48th. Later keeps in that chunk are counted, not used. Fewer than 48 after 512 prompts gives counts only and a non-zero exit.
(3) Record chunks run, prompts answered, keeps per chunk, GPU-seconds, the GPU and per-chunk hashes.
(4) Size REQ-9's job cap for the worst case: 16 chunks at 2,048 tokens (about 1,900 s, about $0.95 at $1.79/h).
(5) REQ-6 also excludes any prompt that encode_generation_prompt refuses under REC's max_prompt_tokens (1,536), so no list stops REQ-9 on the pod.

Tests:
- the kept set equals the full-list kept set at every stop point, with a fake generator whose output depends on its call's prompt set;
- a 512-list run keeps the same 48 as a 256-list run when 256 suffice;
- each call holds at most 32 prompts, in list order;
- the fewer-than-48 exit.
Mutants: one whole-list call; stopping on raw answers; a chunk size that does not divide 256.

### L12 (confirm with edit)

Confirm that REQ-8 builds the grouping at $0. P records none: prepare_task removes exact duplicates only.

(1) Linking: link two rows of the same unit if the character 5-gram Jaccard of their normalized stored prompt (the rendered user text) is >= max_jaccard (0.5, from P's pinned data config). Use every pair, not NearIndex.nearest, and take single-linkage components. There is no instruction-alone test (P has no instruction field). Cross-unit pairs are counted only.

(2) Oversize components: a component of more than 37 rows is oversize.
- Its rows are placed as singletons.
- Its size and its cross-cell pair counts at M = 32 and M = 128 are published.
- No leaf that holds one of its rows can be drawn.

(3) Placement, by cumulative targets. Walk the rows in the level's order:
- quartiles: (target tokens, sealed rank stage1-plant-quartile-ties-v1) over the unit;
- quarters: sealed order stage1-plant-quarters-v1 within each final quartile.
At each unplaced row, put its whole component into the current cell. Close cell j once the cells so far hold at least floor((j+1)·n/4) rows (n = 600 for quartiles; the quartile's final size for quarters). The last cell takes the rest. With no pairs this gives exactly 150 and 37/38/37/38; test byte identity against the plain positional rule.

(4) Stop with counts only if any cell is empty.

(5) Draws:
- the unit by stage1-plant-unit-v1;
- the leaf by stage1-plant-leaf-v1, among the drawn unit's 37-row leaves that hold no oversize row; if there is none, among its eligible leaves with the smallest |n - 37|;
- never redraw the unit.
Corpus = 4,837 - n rows; report the steps (38 for any n <= 100). The k = 75 variant uses the same leaf and adds the first 75 plant rows (corpus 4,875 - n).

(6) The lead's counts-only run prints the component-size histogram and every cut point.

(7) The rule text, its settings file and its labels go in the T1 commit, before rows.jsonl is read. REQ-21 (i) records cell sizes other than 150 and 37-38 as a PLAN-S deviation.

Tests: an A-B, C-D, B-C chain (B-C exactly at the threshold) gives one component; >= vs >; the oversize path; no-pair byte identity; the empty-cell stop; the leaf fallback. Rewrite the brief's mutant as 'a 38-row leaf accepted while an eligible 37-row leaf exists in the drawn unit'.

### L13 (confirm with edit)

Confirm one registry, scripts/stage1/labels.json (draws stage1-<name>-v1; ties stage1-<name>-ties-v1), with seven edits.

(1) Every stage-1 label matches ^stage1-[a-z0-9]+(-[a-z0-9]+)*-v[1-9][0-9]*$. No '|' is allowed: derive_seed joins its parts with '|'.

(2) Load the file with an object_pairs_hook that refuses duplicate keys, and require unique label strings. Each entry records:
- base seed 20261008;
- its extra parts (for example (d, g) or (k, c));
- the id domain;
- its one owning script;
- named_in (brief rev 1 12cbf463…, or 'registry, after the seal').

(3) One s1common accessor returns a label by key; an unknown key raises KeyError. sealed_rank, select_top and the draw helpers take a key, never a string. A test scans scripts/stage1 (tests and labels.json excluded) and fails on any of:
- a stage1-…-v<n> literal;
- a derive_seed, random.Random or numpy default_rng call outside s1common;
- a registry entry that no code uses;
- two scripts that share one label.

(4) List gate-b-random-removal-v1 as 'frozen, reused' (REQ-4, d = 6-8), outside the stage1 pattern.

(5) A test pins the 8 labels that brief rev 1 names: s1, s3-subset, s4, plant-rows, l1-scan, a1-ties, random-removal-1200, random-removal-2400.

(6) labels.json's SHA-256 enters every settings file and the manifest.

(7) The complete registry goes in the T1 commit, before any draw is computed. It holds every label that L5-L15 need, including stage1-length-order-v1, stage1-l8-control-v1, stage1-l8-control-fill-v1, the H2a fill, the plant's quartile-ties, quarters, unit, leaf and R600 draws, and the selector streams. Later additions are append-only, with a test that the T1 entries are byte-identical. REQ-21 (m) states that the labels not named in brief rev 1 were named after the sealed per-unit scores were seen, and that no draw was computed before that commit.

### L14 (confirm with edit)

Confirm the caps: S3 512 new tokens; S4 and SD-600 2,048 (generation.max_new_tokens). Read max_train_tokens (3,072) from recipe S's config; never hard-code it. A test pins that REC and S agree on these limits.

Keep rules:
(1) S3: keep every answer and flag the capped ones. A y^orig that encode_train refuses (empty, or a control token) leaves the SAS ranking and is counted. Report SAS separately for capped and ended y^orig (report only).
(2) S4: keep an answer only if it ended, is REFUSAL-OPENING, answer.strip() is non-empty and encode_train(prompt, answer, S.max_train_tokens) accepts it. Each failure is a counted drop reason.
(3) SD-600: rewrite an A1 row only if its answer ended, strip() is non-empty and encode_train accepts it. Every other row of A1's 600 is REMOVED, giving a combined edit (remove k, rewrite 600 - k). Never truncate. Report k by reason (capped, too_long, control_token, empty), with the category mix, the a_i ranks and the token mass. There is no stop rule on k. Before writing, REQ-15 checks every row on the Mac with parse_edit and edited_corpus (P's codec).

Correct the stated reason: encode_train checks only the row length, control tokens and empty text; 1,536 is the generation-prompt limit (see L11 (5)).

Mutants: SD-600 trains a capped answer; the S4 encode check removed; the strip check removed; max_train_tokens hard-coded; fallback rows rewritten or kept instead of removed.

### L15 (confirm with edit)

Confirm the criterion (the largest E[G(pick)], ties to the simpler rule), B ∈ {2,4,8,16} and additions (i)-(iii), written as follows.

(1) Prior and ties.
- E[·] is taken over the settings prior, with equal weight per (shape, size) grid point.
- Noise is 2.65 pp central and 3.85 pp as a sensitivity (PLAN-S:117), never σ̂_gate.
- Parameters are drawn per replicate.
- A tie is a paired difference below 2 Monte Carlo SE under common random numbers (CRN).
- The frozen rule and k never depend on the shape, the size or the diagnostic quality.

(2) Keep and feasibility.
- Keep is in every menu with G = 0. Top-k and the screen never drop it. Its U comes from the a0 seeds already run, outside B.
- On planted menus, keep = a0_plant and G_m = U(a0_plant) - U(m). M counts the options other than keep.
- The options' true O and L effects are stated in the settings (default 0).
- A truly infeasible pick scores G = 0 and counts as a violation (the FOCUS 2 Oct convention). V_max is the maximum over truly feasible options.
- Predictions are made at each τ_O ∈ {2, 5, 10}.

(3) Costs.
- B and c_d are in units of c0, under both cost conventions (C-full and C-lean; PLAN-S:202).
- The c_d/c0 grid is fixed in the settings and includes 0.
- If B - c_d < 2c0, the diagnostic policy picks keep.
- B = 2 is labelled a boundary cell.

(4) CRN: draws are keyed by (replicate, option, seed index, φ, ψ) through the s1common accessor, and shared by both policies and across both grids. Test: at c_d = 0 and k = M, both policies make the same pick in every replicate.

(5) c* = the first crossing: the largest grid point c_j with Δ >= 0 at every grid point <= c_j, plus the linear interpolation to c_{j+1} (report only). A later grid point with Δ >= 0 is reported as 'non-monotone'. If Δ(0) < 0, c* = 'none'. If Δ >= 0 on the whole grid, report '>= the grid maximum'.

(6) Diagnostic quality.
- Category menu: score_m = G_m + r·s·z_m, where s = the SD of the true G over the options other than keep in that replicate and z is iid N(0,1). r ∈ {0, 0.5, 1, 2, 4}, plus 'uninformative' (a sealed random order, also used when s = 0). Add a report-only SIM2 point: the true best is picked with probability 0.5.
- Planted menus: a row-level model, not r·s. Plant rows' scores are N(μ,1); Dolly rows' scores are N(0,1) and carry no signal. μ comes from a row-AUC grid {0.6, 0.75, 0.9} plus 0.5 (AUC = Φ(μ/√2)). A cell's score = the mean of its rows' scores. Add a report-only sensitivity with r·s noise.
- k per (cell, c_d/c0) maximises the criterion averaged with equal weight over the quality grid; ties go to the larger k.

(7) Placement, fixed now; the quality is never fitted.
- Category menu: Gate C's frozen Spearman ρ against the 8 wave-1 D_u (PREREG:195).
- Planted menus: the plant's top-k hit at each M.
- Report the grid points whose simulated 90% range of that statistic contains the measured value. ρ <= 0 is placed at 'uninformative' (an upper bound).

(8) Diagnostic + bisection: bisection becomes successive halving on the top-k survivors plus keep, with budget B - c_d.

(9) Vectorise the one code path over replicates (a replay = a batch of 1). Time the full grid on CPU before freezing. If needed, the settings fix a smaller replicate count for the diagnostic grid and report the paired MC SE.

Tests and Part E mutants: c* taken as the last crossing; keep dropped by top-k; CRN not shared; quality not applied. Also test that r = 0 gives the true best, that 'uninformative' hits the best at about 1/M, and that corr(score, G) is about 1/√(1+r²).

### L16 (confirm with edit)

Confirm τ_L = 2√2 x s, fixed before wave 1 and never re-estimated. Make it exact in REQ-19 and REQ-21 (e):
- s = the sample SD (ddof = 1), over seeds 1101-1103, of each Gate A a0 unit's mean per-example query loss on all 200 task rows, at its evaluated checkpoint (e1). Each unit is named by SHA-256.
- Record s, τ_L and the 6-against-6 SE (s x √(1/3)) as numbers.
- State the scope: only the threshold τ_L is frozen. The SE inside REQ-16's 'upper 90% L' screen is still estimated from the replay's pooled residuals.
- Record the 2-df risk: the 95% interval for σ/s is 0.52-6.28, and P(s < 0.5σ) = 0.22. In that case about 12-24% of null arms fail the L screen.

## 3. The lead's additions (open items the critic left to the lead)

- **Seeds of the L8 length octiles (REQ-21 (g)).** The 8 octile arms follow Gate B's frozen wave rule (DRAFT revision 5 §3) applied to the octiles: wave 1 at seed 1101 (8 runs), wave 2 at seeds 1102–1103 for the top 2 octiles by D, an extension at 1104–1105 only for a contested octile; the same constants; σ̂ from Gate B's final pooled σ̂. The contrasts use Gate B's R arms at the same seeds (`gate-b-random-removal-v1`, draw d at seed 1100 + d). The category-matched random control for the best octile runs at seeds 1102–1103 (2 runs). This gives 12–16 octile runs plus 2 (PLAN-S §5.3 item 6 says 11–15 plus 2; the difference is the extension, which runs only when an octile is contested).
- **Seeds of the plant's main runs.** Every main-sweep arm (remove the planted cell at M = 8, 32 and 128; R600 on the planted data; the optional R150) runs at seeds 1101–1103 and is paired with a0_plant at the same seed. The rule "no scorer built on a0-1101 states is evaluated at 1101" does not apply: these arms remove the known planted cell or random rows, not a scorer's pick.
- **R600 and R150 on the planted data.** A fresh draw per seed: draw d at seed 1100 + d (d = 1–3), over all 4,800 rows of the planted corpus, by Gate B's R rule (the same per-unit stratification), with new labels `stage1-plant-r600-v1` and `stage1-plant-r150-v1`, parts (d). Both labels go in the T1 `labels.json`.
- **Records to add (from the critic's other findings).** (1) REQ-6 excludes every S-pool prompt that `encode_generation_prompt` refuses under REC's `max_prompt_tokens` (1,536) and prints the S-pool size N after each filter, in order; if N falls below the 1,000-prompt S3 subset, stop with counts only and report to the lead. (2) PLAN-S §6's scored-at-$0 report adds each scorer's planted-cell rank beside the same unit's rank without the plant (general_qa is the sealed top unit for A1 and representation similarity). (3) Cite FOCUS entries by title (FOCUS has changed since the brief's pin `53db373e…`). (4) REQ-21 (m) lists every Gate B value the builder and the lead saw before the selector settings were frozen: r_j, σ̂_gate 1.83 pp, P4, the P(LOCALIZED) lookup, the re-costing figures, and the sealed rankings, scores, picks and ρ values (T2 cannot be met as written).
- **Hand-over points.** The builder reports to the lead (1) when the T1 bundle is ready, before anything reads `rows.jsonl`; the lead verifies, commits and pushes it; (2) after Parts B–F; (3) after Part G. Text-free hand-over notes go in `tmp/claude-workspaces/stage1-commitments-build-20261016/notes/`.

## 4. The lead's rulings after the T1 verification (2026-10-16T21:20 UTC; before the T1 commit; no rows.jsonl read)

The T1 bundle (14 files, hand-over SHA-256s) went to a read-only verification workflow (run wf_ee2682cd-67c: suites, mutation-runner validity, new mutants, three code reviews, a critic; record `tmp/gi-vi-stage1/t1-verify-full.json` in the main checkout). Verdict: fix_required, one blocking defect. The A1 arithmetic, orientation, consistency check, input-hash chain, edit round trip and the 14 named mutants hold. Rulings:

1. **Labels pin (blocking): option (A).** labels.json stays append-only (L1, L13 (7) unchanged). Each settings file keeps `labels_sha256` as the record of the T1 registry, but `check_settings` refuses only when an entry that the settings file names differs: each settings file holds `label_entries` = {key: SHA-256 of the canonical JSON of {key: entry}} for every key it uses, and `provenance()` records that digest set, not the whole-file SHA-256, so edit bytes do not change with an append. Add a test that appends one canonical entry to a temporary copy and shows the golden A1 test, the A1 writer and the plant settings still pass, and that a changed used entry refuses. Re-pin both settings files and `SETTINGS_SHA256`.
2. **Plant R600 and R150 parts: the builder's reading is accepted.** `plant.r600` and `plant.r150` take parts (d, g) (per-unit draws, the "same per-unit stratification" of Gate B's R rule, which §3 already names), and `plant.r150_units` (parts (d)) picks which 6 of the 8 units give 19 rows and which 2 give 18 (6 × 19 + 2 × 18 = 150). REQ-21 (g), (h) and (m) record both as readings chosen by the builder and confirmed by the lead after the seal was seen.
3. **Plant leaf rule:** one text in both files: "the first in sealed_order(plant.leaf) over the cell ids of the candidate leaves; the candidates are the drawn unit's 37-row leaves with no oversize row, or, if there is none, its no-oversize leaves with the smallest |n − 37|". Set `plant.leaf`'s id_domain to the same text. Add to the placement rule: "after each placement only the current cell can close". Tests: a 36/38-row fallback tie gives the stated leaf; the n = 114 example gives [57, 1, 27, 29].
4. **A1 refusal tests** (the critic's list): negative perturbations of the consistency check (−3e-12, −1e-9), the marker, job, sources, extra-checkpoint, extra-key and groups.json cases, the inclusive 1e-12 boundary with `math.nextafter`, `category_flag_share == 0.5`, and a `boundary_ties` test.
5. **Literal pins:** a T1 test asserts the SHA-256 of `settings/build_plant.json` and `settings/write_score_edit.json` against literals (after items 1 and 3); REQ-8's future `build_plant.py` loads its settings with that literal.
6. **Mutation runner:** strip PYTEST_ADDOPTS and PYTEST_PLUGINS from the subprocess environment; count a run invalid if its JUnit test count differs from the baseline's; record the tested tree's {path: SHA-256}, the engine identity, the pytest version, and each mutant's target-file hash before and after the patch. Re-run the T1 spec plus the verifiers' surviving mutants (E-*, X-*, V10, V29, V37 in the verification record); each must be killed.
7. **s1common hygiene:** `strict_json` refuses non-finite floats (1e999); `provenance()` adds the Python and numpy versions. The lexicon-pin test checks the path the settings name when it exists, else the tmp/ source.
8. **Scope note for the T1 commit message and REQ-21:** the golden test and the A1 contract are defined on engine X (472fc7f6…); after engine round Y they need a new pin.

## 5. The lead's rulings on the literature sweep (2026-10-16T21:33 UTC; before any stage-1 draw; no rows.jsonl read)

Source: `writing/paper/2026-10-17-lit-sweep.md` (FAQ's worker, commit 2b1dfa7; the ICLR 2027 items were read as abstracts only). Each ruling below is outcome-free and costs $0 or a few pod-seconds. Each is a pre-registered REPORT that changes no primary test, verdict or arm.

1. **Token accounting (the "compute-matched" risk).** Every removal and add arm reports the target tokens and total row tokens it removes or adds, and its share of the corpus token mass (REQ-21 (b), (f)). One pre-registered secondary analysis, report only: each removal filter's restoration is placed on the random dose curve along a TOKEN axis, using the token masses of R (600), R_1200 and R_2400. This is the "token-equivalent random dose", beside the row-equivalent dose that PLAN-S §5.3 item 1 already gives. H1 (the 600 shortest rows) is the case where the two axes differ most; the paper must report both. No new arm now. The paper's "Compute-Matched" wording is the user's (title) decision; it is flagged in REQ-21 (a).
2. **One-shot scoring stability.** Report only, by a Part G report script that runs after the T1 commit, from the same rows.jsonl as A1: the Spearman ρ between the per-row q-only and e1-only bi-anchored cosines, and the Jaccard overlap of the top-600 sets they would select. The paper names one-shot scoring as a limit (SABA, an abstract-only ICLR 2027 submission). The T1 files do not change for this.
3. **Two report-only add-ons, defined now.** (a) For each evaluation prompt, whether the untuned model's greedy answer is a refusal (LEX REFUSAL-OPENING), from the untuned unit's existing evaluation records. It is used only as a stratifier of the prompt-flip reports. (b) The untuned model's mean per-token loss (perplexity) on each of the 48 added rows of S1, S3 and S4, computed in REQ-9's existing pod pass (no new pod). The sweep's third idea, the attribution score's share along a safety direction, is NOT pre-registered. If done, it is labelled post-Gate-B exploratory.
4. **Candidate new references** ("opening hold" first-token loss; Safety at One Shot): a scope decision for the user, which FAQ raises with the re-plan decisions. No change before the user decides.
5. **Premise risk** (new works where seed variation or recipe beats corpus edits): this supports the current design (6 method seeds, the DIFFUSE branch, the fallback). No change.

## 6. Build rulings from the wave-1 decisions (2026-10-17T07:22 UTC; FOCUS fcf79a2; binding for every builder)

The user confirmed the ambitious-default-with-fallback rule and took the recommended defaults on UW-01 to UW-21; the lead took LW-01 to LW-35 at their defaults (FOCUS 2026-10-17T07:21 UTC; the list is `research/experiments/2026-10-17-stage1-preregistration/stage1-decisions-consolidated.md`). Every "build now default behind a switch" in the W1 builder extract is now set as below. Where a switch remains, its default is the value below and the other branch stays testable.

1. **Analysis model (REQ-16, REQ-17, REQ-19, REQ-21 (c)):** primary HB-C, paired by seed with one seed shift per design cluster ({a0, S1, S3, S4} and {R, A1, L1, H1}), one residual variance per arm by REML, a crossed prompt part, Satterthwaite df; HB, S-a and S-aW are pre-registered sensitivities. REQ-17's generative model simulates the primary model's noise on that scale; the 2.65/3.85 pp per-arm values stay its inputs (never σ̂_gate).
2. **Seeds (REQ-4, REQ-21 (d)):** layout D1: a0 at 1101–1107 and R at 1101–1107 (R_1108 is not run); method arms at 1102–1107 as before.
3. **Testing family and labels (REQ-16, REQ-21 (b)):** the closed graphical family Φ (24 nodes: U_k two-sided; O_k and L_k one-sided adverse; F_k "feasible at τ_O* = 5 pp"; start weights as draft B §B.2). Label order UW-08 (a). Rule R1.3 for "worse" on O (against θ0 at τ_O* = 5 pp AND significantly above the comparator) and on task loss (against a0 at τ_L AND significantly above the comparator). τ_O grid {2, 5, 10} reported; τ_L read against a0 with ℓ̄(m) − ℓ̄(R) reported (LW-07).
4. **Over-refusal bank (REQ-6, REQ-19, REQ-21 (e)):** REQ-19's $0 MDE check decides O-ext. If the 6-seed O MDE exceeds 5 pp, the primary O bank is the dev 100 plus 400 harmless PHTest prompts (source N; MIT). The lead downloads and seals that file (text under tmp/ only; a text-free sealed record with its SHA-256); builders take it as a hash-pinned input and never download. Fallback F (the dev 100 only). Never a draw from the hidden remainder (UW-07b).
5. **Token matching (REQ-4, REQ-21 (a), (b)):** build W1-03's token-matched random-removal builder R_tok for A1, L1 and H1 now (a secondary arm at 3 seeds, funded tier); its labels are appended. The token-axis dose analysis (§5.1) is the fallback and is built in any case.
6. **Scorers (REQ-12, REQ-13, REQ-23):** all three are built before wave 1 (LW-18, LW-20, UW-18). If REQ-12 or REQ-13 misses W1, REQ-21 (l) records it as post-Gate-B exploratory; REQ-23 has no such exception.
7. **Plant (REQ-8, REQ-21 (i)):** F9's two more sealed plant locations go into a NEW settings file (never T1's build_plant.json) with appended labels, as conditional rule text that runs only if stage 1b is funded; no benign-topic plant (UW-16).
8. **Texts the W1 record carries (REQ-21):** the δ_fam rule (UW-13); headline item (2)'s new wording (UW-15); the Llama-3.2-1B Gate B-lite rules frozen at the note's defaults (UW-19; `research/review/2026-10-17-stage2-design-notes/llama-gate-b-lite-rules.md` pinned by SHA-256); OLMo-2-1B's P1–P6 stays confirmatory (UW-21); the four accepted deviations (UW-11); the blinding line (LW-08) listing every Gate B value and task-loss difference each writer saw.

## 7. The O-ext draw (2026-10-17T09:38 UTC; REQ-19 fired: O MDE 11.04 pp; binding for the builder)

The lead downloaded PHTest (`furonghuang-lab/PHTest` @ edb80210…, MIT; PHTest.csv 495d109e…, the publisher's checksum matches) into git-ignored `tmp/oext-phtest-20261017/raw/`. The text-free source record is `.ai/inputs/stage1-commitments-20261016/oext/phtest-source.json`. Rule, fixed now and outcome-free:
1. **Candidates:** the 2,077 rows with Harmfulness = "harmless" (the 1,192 "controversial" rows are never used).
2. **Exclusions**, each counted by reason: exact duplicates of a normalized prompt; near-duplicates by the engine's NEAR_DUPLICATE rule (character 5-gram Jaccard at least P's max_jaccard) of any prompt in every bank of P (all splits, as ANCH and L9 do; counts only; this part is run by the lead), of the 128 anchors, of the S-pool and of the plant rows; empty prompts; prompts that `encode_generation_prompt` refuses under REC's max_prompt_tokens (1,536).
3. **Draw:** a sealed order over PHTest IDs by a new label `stage1-oext-phtest-v1` (key `oext.phtest`, parts none; appended); the first 400 eligible IDs in that order form the O-ext bank. If fewer than 400 are eligible, stop with counts only and report to the lead.
4. **Outputs:** the 400-row text file stays under `tmp/` only; a text-free sealed record (IDs, SHA-256s, counts by exclusion reason) is committed. The primary O bank is the dev 100 plus these 400 (UW-07a), judged on answers capped at 128 tokens after W1-18's $0 truncation check (PLAN-S:197); per-source reports keep the two sources apart.
5. **Build:** a new `scripts/stage1/build_oext.py` with synthetic-data tests (part of REQ-6's batch); the lead runs it on the real files.

## 8. The planted control's anchor circularity (risk 44) and the counting list (2026-10-17T09:59 UTC; decided by the lead under the user's delegation)

1. **Risk 44.** The plant's rows (PKU red-team prompts with PKU-safe, non-refusing answers) and Gate C's 128 anchors come from one source, PKU-SafeRLHF, and A1 is bi-anchored on those anchors, so an A1 hit on the planted cell could be read as near-circular. The plant rows are disjoint from the anchors at the prompt level (REQ-8), which limits but does not remove the concern. **Ruling (ambitious default, pre-set fallback):** the planted-cause sweep (stage 1b, funded tier) also reports A1's planted-cell rank under a second, **disjoint-source anchor set**: 64 harmful plus 64 safe anchors from a source that is not PKU-Alignment data, built by the same rule as Gate C's anchors (severity, category balance, a sealed draw, a pinned script), with its source chosen and sealed before the stage-1 freeze (S1) and before any planted run. The PKU-anchor rank stays the counted one; the disjoint-anchor rank is a pre-registered sensitivity. **Fallback** (if the disjoint set cannot be built before S1 or stage 1b is not funded): §6 of the paper states the shared source as a limit. Either way the W1 record (REQ-21 (i)) carries this rule text.
2. **The counting list (conflict 89).** Self-Inf-N-style counts toward "finds a known cause" (F2, LW-10), so it joins the list of planted-cell ranks scored at $0 (DRAFT §8.4). If REQ-13 is not committed at W1 (LW-18's fallback), it leaves both the list and the counting rule, and only A1 counts.

## 9. The over-refusal answer cap (2026-10-17T11:03 UTC; decided by the lead under the user's delegation)

In stage 1, ONE cap applies to the whole primary O bank (the dev 100 and the 400 PHTest prompts), for θ0, a0 and every arm: answers capped at 128 new tokens, if W1-18's $0 truncation check shows that judging the 128-token cut agrees with judging the full answer within its pre-set bar; otherwise the full generation cap for all 500. θ0 and a0 are re-evaluated on the 500 prompts under that cap (they are needed for the 400 new prompts anyway), so every O contrast compares answers made under one rule. Gate B's frozen G4 (the dev 100 at the Gate A cap) does not change. The W1-18 result and the cap chosen are recorded in FOCUS before the W1 record.

## 10. One-pass ruling on the revision-3 open items (2026-10-17T15:18 UTC; decided by the lead under the user's delegation)

The lead adopts the recommended ruling of EVERY item in `research/experiments/2026-10-17-stage1-preregistration-rev3/lead-rulings-needed.md` (SHA-256 9c447704…), §2 (LN-01 to LN-38, LN-15a to LN-15e, the "yes reading" of LN-15) and §3's lead actions, as written there. Highlights that bind builders now: the seed-complete D1 block layout (LN-01: block A = all 8 arms at 1102–1104; block B = all 8 at 1105–1107); plan B under D1 (LN-02); R1.3 as intersection–union nodes at each node's Φ level with the edge F_k → L_k = 1 (LN-05); δ_fam for Llama-3.2-1B only (LN-04); the selector switches flipped to LW-12/LW-13 before REQ-18's predictions freeze (LN-10, LN-11, LN-29); C-lean and C-full hold the 500-prompt O bank (LN-07, LN-33); the reused R comparators get a fingerprint-checked regeneration and an O-only pass on the 500 bank, never a pull from a stopped kit pod (LN-12); the 128-token cap route (LN-19) and equal prompt weights (LN-24); the commit order (LN-30): the REQ-20 manifest, then the REQ-21 record carrying the manifest's hash, then FOCUS, then wave 1 after the frozen pre-launch checks. Downloads, licence terms, public deposits and the user's own texts still need the user's own word (LN-15).

## 11. Rulings on the S1 small builds' open items (2026-10-17T17:16 UTC; decided by the lead under the user's delegation; ambitious default with fallback)

The four builds are B10 (evaluate a saved adapter), B11 (Safe LoRA), B14 (similarity strata) and B17 (lean evaluation for c0). Their hand-overs are in the lead's worktree under `tmp/claude-workspaces/stage1-s1pkg-20261017/notes/`. Rulings:
1. **B10 B-1, the arms' O-ext path: (a), one shared pinned function**, `scripts/stage1_s1/oext_eval.py`, with no engine change. It follows LN-19's route. Under Branch 128, it cuts the engine's dev-100 answers (made at the Gate A cap) to their first 128 new tokens, judges them again, and generates PHTest at a 128-token cap. Under Branch full, it generates all 500 at the full cap and reports the 128-token cut as a sensitivity only. Weights are equal per prompt (LN-24). It writes new files beside the engine's 8 evaluation files, so certify stays byte-identical with Gate A. θ0, a0, R (LN-12), every arm (through B15) and B10's references call this one function. **Fallback (c):** if (a) is not verified before the S1 freeze, `overrefusal_bank.status` = `dev100_recipe_cap`, and the pre-registration states that limit.
2. **B10 S-3: the relaxed acceptance rule stands.** The data and the training identity must be equal; the config hash is reported. This matches REF R.0.7 and the engine's `eval_state`.
3. **B10 S-2 (3): the environment field list is confirmed**, including the driver line and the SHA-256 of `environment-linux.lock`. A reference pod either matches the certification pod's pinned fields or certifies in-process first.
4. **B10 S-4 and B11 S2: the K = 0 Safe LoRA point runs on the certification pod** (about +0.93 FRE, about $1.36; block B funding). Fallback: the CPU test plus the certify unit stand as the K = 0 certification, and this is stated.
5. **B10 S-5: the merge writes the `safe_lora` external_transforms entry now, at engine X.** It has the fifth key (transform_settings_sha256 → provenance.settings_sha256). The B10+B11 integration test is added at the same time. Every later engine re-pin (X′ or Y) re-takes both hashes in one edit (point 7).
6. **B11 S4: the full base pins are now read from Hub metadata** (no weights downloaded). The pins are allenai/OLMo-2-0425-1B @ a1847dff35000b4271fa70afc5db10fd29fedbdf, Apache-2.0, not gated, and 12 files. Each file has its git blob id; the two safetensors files also have their LFS SHA-256 (c52e4ac8…, 5f807625…). The lead's record is `tmp/gi-vi-stage1/olmo2-0425-1b-base-pins.json` (9bc9a9e9…). B11's settings pin them in full. B15 downloads with `revision=<the pinned commit>`, never `main`. The download itself is still the user's decision (LN-18).
7. **B11 S5 and B17 N1: re-pin before any run.** Before any Safe LoRA or c0 pod job, both settings are re-pinned on the engine that stage 1 actually uses (X′ or Y). In one edit: the engine pin, the SHA-256 literals and the mutants' find/replace. Then both suites and the specs are run again. This is a B15 pre-launch check.
8. **B11 S6, the V dtype: REF row 5 stands as primary.** V is the float32 difference of the stored weights. Hub metadata: the Instruct model is stored in BF16; the base is stored in F32. A $0 Mac diagnostic is pre-set for when the base weights are present. It gives, per matrix, ‖V − V′‖_F / ‖V‖_F, with V′ = float32(W_Instruct) − float32(bf16(W_base)). It also says whether REF's selected-layer set (K = 39, the fast form) changes between V and V′. If the set changes, V′ runs as a report-only point at the Safe LoRA seeds (block B; its cost is stated then). If the set does not change, the question is closed. The time to run it: when the user agrees to the base-model download.
9. **B11 N3:** the merge diffs `tests/b11_official_port.py` once against IBM/SafeLoRA's public `model.py`. This is a read of a public source file for comparison; nothing is run from it. Each difference is recorded.
10. **B14 SF-1: plan B follows LN-02.** Under plan B, a0 runs at 1101–1107, so `plan_b` = seeds 1102–1107 with add sets S1 and S4 (J = 6). A plan-B block-A-only entry (1102–1104, S1 and S4, J = 3) is added beside plan A's. The settings get a new SHA-256.
11. **B14 SF-4: §9.4's interval model is HB-C, computed by B16 from `cells_u_pp`** (LW-01). B14's per-contrast paired form is printed as the S-p sensitivity (LN-37).
12. **B14 SF-5: the embedding read is confirmed.** It is hidden-state index 16 (`model.norm` of the last block; L4) at the last prompt position. N-8: once REQ-3 is committed, a test checks that B14's vector equals REQ-3's read (d) at index 16, byte for byte. The SHA-256 of `strata.json` goes into FOCUS before any add-arm outcome is read.
13. **B17 S6: C-lean holds the 500-prompt O bank under the one cap (LN-07).** B17 adds a hash-pinned O-ext input and an O-cap setting, with tests. It calls the shared function of point 1. The c0 estimate becomes about 2,400 s (E, the verifier's estimate), up from about 870 s. The S5 limit (an edit arm with no known fingerprint is refused) is recorded as a limit; it fits LQ30's options (i) and (ii).
14. **Merge:** one `scripts/stage1_s1/__init__.py`; B14's `conftest.py` is kept (N-5). The tree combines with the builder's batches 2 rev 2, 3a and 3b. Both packages' suites, every mutation spec and the five regression suites must pass before the explicit-path commit.
15. **A text fix for DRAFT rev 3 §1.3 (from the builder's note):** the plan-B line should say "R draws d = 8–10 (d = 8 from the frozen `build_sealed.py`; d = 9–10 drawn by `gate-b-random-removal-v1`)". The wording is fixed in the freeze pass.

## 12. Part E revision 2 and W1-18's guard batch size (2026-10-22T12:42 UTC; decided by the lead under the user's delegation)

1. **Part E revision 2 is accepted** (verification pass: 426 tests, 0 skipped; 22 of 22 new mutants killed; predictions regenerate byte for byte). The switches follow LN-10, LN-11 and LN-29. The builder added a third `se_form` value, `hb_unpaired`: it stays as an unused, recorded alternative. The pinned value is "hb". Removing it would need re-pins and a 2–3 h regeneration for no change in any prediction.
2. **The C-full cost wording:** the settings charge 0.517 FRE more per arm at the full cap (guard scoring included). The freeze pass writes 0.517 into DRAFT rev 3 §7.3 and REC (k) rule 8, replacing "about 0.49 FRE".
3. **REQ-18's predictions file is committed now**, before any stage-1 outcome exists: `.ai/inputs/stage1-commitments-20261016/predictions/predictions.json` (48284ce0…, kind "stage1 selector predictions"), with its timing record. REC (k)'s [FILL AT W1-P] takes this path and hash at the freeze.
4. **W1-18 on the Mac GPU:** `overrefusal_checks.py --guard-batch-size N` gives the engine's guard loader a copy of the pinned recipe with only the guard batch size changed, after the recipe pin check. On MPS a value above 1 refuses (the padded-batch fault: non-finite logits); the Mac run uses `--device mps --guard-batch-size 1`. The device and both batch sizes are written into the record as report-only. Refusing without the option is kept on purpose: it is better than a silent default of 1.

## 13. W1-18 moves to the first stage-1 pod; the Safe LoRA V check moves to its pod job (2026-10-22T13:24 UTC; decided by the lead under the user's delegation)

1. **The Mac cannot run W1-18.**
   - On MPS, the pinned guard (bf16, SDPA) gives non-finite logits. In a padded batch of 8 this happens at the prompt pass. At batch size 1 on a real unit's answers it happens at the second decoding step (13:08–13:23 UTC run; the synthetic diagnostic used short prompts only).
   - On the CPU, the 8 GB judge swapped for 6.4 h and gave no output (17 Oct).
   - The `--guard-batch-size` option (§12 point 4) stays; it is verified and harmless.
2. **The new rule (ambitious default, with its fallback):**
   - W1-18 runs as the **first job of the first stage-1 pod**, on CUDA (the pinned guard's device type), through the stage-1 run kit (B15).
   - It runs before any arm's, θ0's or a0's answer on the 500-prompt bank is generated. FOCUS records its output SHA-256 and the branch before the pod's next job starts.
   - The bar is unchanged: at least 97 of 100 flags agree in every unit, and no unit's refused count moves by more than 2.
   - Until the result exists, plans and cost estimates use Branch full. If W1-18 cannot run or fails, Branch full applies. The cap never switches after any 500-bank answer exists.
   - The REQ-21 record's line "recorded in FOCUS before this record is committed" becomes this rule at the freeze pass.
   - Why: Branch 128 costs about $10–27 against $40–70 for Branch full (REC (e) rule 5's estimates). The pod job takes minutes.
3. **§11 point 8's V/V′ diagnostic** (Safe LoRA's alignment matrix) moves into the Safe LoRA pod job (B15), with the same rule and before the projection. It needs both the base and the Instruct weights; the pod downloads both at their pinned commits. Nothing is downloaded to the Mac for it.
4. **Local copies:** the Mac no longer needs the Qwen3Guard-Gen-4B weights (8.2 GB) or the OLMo-2-0425-1B base weights (5.5 GB). Both are pinned by commit and checksums, and pods fetch them. They go to the Trash with their revisions recorded (the user's 22 Oct rule: keep on the Mac only what the next steps need).

## 14. Batch 8's manifest settings (2026-10-22T15:49 UTC; decided by the lead under the user's delegation)

The batch 8 critic (`critic-b8.json` in the lead's worktree, `tmp/claude-workspaces/stage1-integrate-20261017/notes/`) passed batch 8, with nothing blocking. It left two settings decisions:
1. **C1, the not_built rows: option (a).** `settings/commitments.json` lists every row of the REQ-21 record's (l) table that is not built. Each row carries its own label, copied from (l). `validate()` accepts a label only from the fixed set that (l) uses: "post-Gate-B exploratory", "never added under this rule", "a cited limitation", "not proposed", "added only by the user before S1", "not built; the held-out selector comparison is a later study with its own pre-registration", and "-". So (n)'s sentence ("the manifest carries every row") holds as written.
2. **C2, the conditional flags:** `scripts/stage1/**build_plant_extra*` joins the conditional rules, so its condition text applies to the file as a whole; (n) states that the decoy part inside it is unconditional. ADD-8.1 (the disjoint-source anchors) has no file in the tree, so it stays rule text in (l) and (i).
3. The builder makes C1–C5 as batch 8 revision 1. C3 is the checker's scan of files committed after the manifest; C4 and C5 are W1-08's six tests and W1-01's three refusal tests, each with its mutants. The SETTINGS_SHA256 literals and the settings test are re-pinned.

## 15. Engine round Y: frozen, not merged; the lead's rulings on its open items (2026-10-23T00:25 UTC; decided by the lead under the user's delegation)

Engine round Y (the B+Qi reference arm's constrained SFT and the confirmation role) was built in the lead's own workspace from main bc79b08 (workflow wf_6f145293, on Opus: brief, build, two verifiers, fix). **Y's code identity is 34bfd28879fdefc5d6605cb73a707d1edd2ec5d102b4b86c0026bc6ac36969f6** (29 files); 8277453f is superseded. With B+Qi off, Y reproduces engine X byte for byte on the golden written by X (the certificate verifier: pass). The 26 changed files are frozen by hash: `backups/2026-10-22/engine-round-y-34bfd288.sha256`, and the files are in the private release `backup-2026-10-22-local-tmp` as `engine-round-y-34bfd288.tar.gz` (79504719…, downloaded back and checked). **Y is not merged into main**, and it never is before Gate B's `--final` procedure (FR-01, LS-01, LS-22). Rulings:
1. **F2/Q6, the stage-1 engine pin:** every W1 stage-1 script pins engine X and refuses on another engine. So every Mac run of a W1 script (the S-pool, the plant, the O-ext bank, the R draws, the scorers and writers) runs on X before Y is merged. A re-run after the merge needs a recorded re-pin to Y, justified by the X → Y certificate; the W1 manifest never changes. The fallback, if a W1 run must come after the merge: the re-pin is a post-W1 deviation recorded in FOCUS before the run.
2. **Q2:** pod C2 trains B+Qi to e1 (all steps), training only, with no evaluation.
3. **Q1:** B+Qi is the new optional recipe field `train.constrained_sft` (off when absent); `train.loss`'s text is unchanged (LS-09).
4. **Q3:** the binding-check thresholds are fixed by the lead from REF §R.2 before the certificate pod runs (an S1 item).
5. **Q5:** the dev-source subsample path stays, as the pod smoke test that touches no hidden data.
6. **Q7:** every job record names the engine it ran on (LS-04's default).
7. **Q4 and F1:** the reviewed insert-only entry for the memory preflight is accepted, and so is F1's design (the ledger's injected device barrier, not `torch.cuda.synchronize` inside engine.py, so the <global_writes> record does not change).
8. **F5:** adopted for Y's next fix round: refuse a LoRA dropout other than 0 when `train.constrained_sft` is present, because the reference forward under `disable_adapter()` must see the same network as the training forward.

## 16. B16, the stage-1 reading: built and verified; the lead's rulings on its open items (2026-10-23T00:40 UTC; decided by the lead under the user's delegation)

B16 (`scripts/stage1_s1/reading/`, 26 files; workflow wf_70d308dc: a Fable builder, two Opus verifiers (statistics, by an independent reference implementation and simulation; code), and an Opus fixer) implements HB-C with REML, the sensitivities, Φ, the IUT nodes, the label row and the headline word. Its suite passes 182 tests with 0 skipped; the mutation spec has 105 entries: 104 killed and 1 expected survivor, 0 invalid. It is committed with this section; it is an S1 build and is pinned at the S1 freeze. Rulings:
1. **The REML floor mode is "active_set"** (as built). It is LN-35's rule as written: the fit stops when the largest step among the arms above the floor is below 1e-6, or after 25 steps. Rev 4's planning numbers (§1.3, §3.2) came from the planning routine and stay planning figures; they decide no label.
2. **LN-35's text gets one sentence at the S1 freeze:** a step that floors an arm does not end the fit (the stats-F1 fix).
3. **The per-actor best data arm is "better and feasible"**, as rev 4 §4.6 and LN-08's title state; §9.4's "among feasible arms" is read the same way.
4. The size, coverage and familywise-error simulations are not re-run on the final code; they run once more, at the S1 freeze.

## 17. B15, the stage-1 run kit: the lead's rulings on the brief's open questions (2026-10-23T01:29 UTC; decided by the lead under the user's delegation)

The read-only brief is `b15-brief.md` in the lead's worktree, `tmp/claude-workspaces/stage1-integrate-20261017/notes/` (wf_cd858ed5, Opus). It lists 19 job kinds, the gates G0–G6, the money rules and the reuse of the Gate B kit. The lead adopts the brief's proposed default for every open question Q1–Q20, as written there. Highlights:
- **Q1:** W1-18 is the only job on the first stage-1 pod, so FOCUS records its branch before any 500-bank job is planned.
- **Q3:** the arms are dealt across pods by a fixed, outcome-free rule recorded in plan.json before launch.
- **Q4:** new arms use recipe S, with training identity f46279e5… checked.
- **Q5:** the 4-per-pod count covers training arms and each eval-only point.
- **Q6 and Q7:** no stage-1 pod launches while a Gate B launch is pending, and B15's guard reserves Gate B's remaining worst-path need while Gate B is open.
- **Q8:** a block's funding record covers B15's cap-based need (block A about $77–94), not rev 4's $60–74 spend estimate.
- **Q9:** oext_eval.py comes from the S1 merge now running, with its fallback (c) as written.
- **Q14:** the reused units are re-judged, so each contrast uses one judge device.
- **Q16 and Q17:** the SP prefix mode and the C2 certificate refuse until their text and thresholds are recorded.
- **Q18:** stages 1b and 1c are outside B15's first scope.

**Not the lead's:** the funding-event definition (FR-15, LN-16, W1 record (a) rule 5) is the user's. No stage-1 block starts until it is answered, and no stage-1 run is paid from the Gate B balance.

## 18. REQ-6 stopped: the S-pool has 947 rows, not 1,000. Post-W1 deviation D-1, the S3 subset size (2026-10-23T13:35 UTC; decided by the lead under the user's delegation)

**Facts (M: the lead's Mac run of `scripts/stage1/build_s_pool.py` at main 721c58f, 13:32 UTC, engine X, counts only, nothing written).** Candidates 1,057. N after each filter: empty 1,057; control_string 1,057; exact_overlap 1,051 (6 equal an anchor prompt); near_duplicate 1,044 (6 near an anchor prompt, 1 near a hidden-bank form); encode_train 1,044; generation_prompt 1,044; first_per_prompt 947 (97 repeated prompts). N = 947 is below `min_pool` = 1,000, so the frozen stop applied (§8 record (1); REV4 §1.3 "stops with counts only if N < 1,000"; "report to the lead"). The brief's "about 2,600 prompts" was a planning estimate (E). The candidate rule is "fixed whatever any count shows" (W1R item 26), so it does not change. REQ-4 ran first and passed (12 files in S1OUT `r-draws/`).

**Ruling D-1.**
1. Unchanged: the candidate rule, every filter and its order, S1 (48), the S4 candidates (512), the refusal decoy (37 rows, W1R item 23), every sealed order and label, and every W1 file. The W1 manifest never changes.
2. The S3 subset is the first k ids of sealed_order(S-pool ids, `s3.subset`). k is the largest integer k ≤ 1,000 for which at least 37 S-pool rows lie outside S1 ∪ (the first k) ∪ the S4 candidates. The rule reads ids and sealed orders only, never a model output. E: k is about 856 at N = 947. The subset keeps its role: a sealed candidate pool whose size limits cost (PLAN-S:146). S3 still trains on its top 48 by REQ-11's score.
3. The stop becomes: N < 597 (48 + 512 + 37), or no k ≥ 48 meets point 2, or a list cannot be filled. A stop gives counts only.
4. Code: a new wrapper package `scripts/stage1_s1/d1_spool/` (own settings pinned by SHA-256, tests, mutation spec). It loads `build_s_pool.py` by path after its SHA-256 check and reuses its functions; it changes only the S3 subset size rule and the stop. Its record carries the planned size (1,000), N, k, the count outside the lists, and this section's reference.
5. Every consumer of the S3 subset (REQ-3's `s3_safe` pool, REQ-9, REQ-11, REQ-8's decoy draw, the pool pins) is checked for a fixed size of 1,000. A consumer that refuses another size gets the same treatment: a wrapper, never an edit of a W1 file.
6. The R+S1 combined edits (REQ-7) use the sealed Gate B files R_d2–R_d4 (`.ai/inputs/gate-b-sealed-20261008/out/edits/`), which REQ-4 reproduced byte for byte.
7. **Pre-set fallback.** Trigger: the wrapper is not verified after one fix round, or k < 600. Then the S3 subset is all N rows in the sealed order and the decoy is not built. The paper reports W1-09's check as "not built: the S-pool was too small".
8. The wrapper runs on engine X, like every W1 script (§13 point 1).

**Paper consequence.** S3's candidate pool is k prompts (about 856), not 1,000. The methods section reports N, k and this rule.

## 19. The pool pins are filled after W1. Post-W1 deviation D-2 (2026-10-23T14:41 UTC; decided by the lead under the user's delegation)

**Facts (M).** `scripts/stage1/settings/representation_pools.json` (W1 manifest entry `1451ba5e…`) holds the plant and decoy pool pins with `sha256` null. Its fill rule: "the lead fills each sha256 from REQ-8's sealed text-free record when REQ-8's sealed pools exist, before W1; filling changes this file, POOL_PINS_SHA256 in representation_pass.py and the literal in tests/test_representation_pools.py, and nothing else". REQ-8 did not run before the freeze, so a fill in place would change three W1 files after W1. The other null pins in the W1 settings stay null by their own rules: `build_r_tok.json` (stage 1c), `build_reuse_spec.json` units 6–7 (R_1104/R_1105, only if Gate B's extension ran; it did not), and W1-18's source map (optional; its tables read "unavailable").

**Ruling D-2.**
1. Every W1 file stays byte-identical. The fill rule's content is applied exactly: only the two `sha256` values change, each equal to the SHA-256 that REQ-8's sealed text-free record gives for its pool file, with the same item count.
2. Code: a new package `scripts/stage1_s1/d2_pool_pins/`. (a) `fill_pins.py` writes the filled pins file from the W1 pins file and REQ-8's record (both given as PATH:SHA256) and refuses if any other field would differ. (b) `d2_representation_pass.py` loads `representation_pass.py` by path after checking its SHA-256 against the W1 manifest, and runs it unchanged except that the pins file path and its SHA-256 are the filled file's, given as PATH:SHA256 and checked again against REQ-8's record before use.
3. The filled pins file and REQ-8's record are sealed by SHA-256 in the stage-1 inputs. B15's J5 job calls the D-2 wrapper with both pinned in the plan.
4. Pre-set fallback (trigger: D-2 not verified after one fix round): J5 runs without the plant and decoy pools, and REQ-3's plant and decoy rows are reported as "not run". The S3 pools are unaffected, because they are named on the command line by SHA-256 (the pins file's own rule).

## 20. B15 built: the lead's rulings on its open points (2026-10-23T15:33 UTC; decided by the lead under the user's delegation)

B15 (`runkit/stage1-olmo/`) was built and fixed by workflow wf_09f8f863 (Opus): a core builder, a runner builder, three verifiers (money and gates; runner; completeness) and one fix round. The verifiers found 8 blocking and 15 should_fix defects; the fix round fixed all of them except the O-ext unit runner (point 5), each with a test that failed before the fix. 184 B15 tests and Gate B's 271 kit tests pass; the Gate B kit is unchanged. The kit pins Gate B's final record as `06a7020a…`, equal to the file committed in 3e82f67 (M: `git show | shasum`, 15:32 UTC).

1. **Block A's funding group.** The W1-18 pod (S1-0) and the certificate pod are block A's first launches. Block A's funding event must cover the whole group's cap-based need (S1-0, the certificate pod and block A's arm, diagnostics and judge pods, counted by the kit) before S1-0 launches. A smaller top-up launches nothing. This is the user's rule ("it must cover the block's cap-based need before the block launches") applied to the block's first launch. B10's certification pod belongs to block B's group.
2. **Cents.** The kit keeps the frozen [D20] rounding. Its block-A needs ($94.23 / $81.48 / $77.23 for the three arm-pod launch splits) replace the brief's hand figures ($94.22 / $81.49 / $77.25); the difference is at most $0.02.
3. **The deal is arm-major.** The brief's example order (seed-major) put A1 twice on one pod in plan B's block A.
4. **c0 on Y on the certificate pod** (REV4 §10.3) stays. It needs B17's settings re-pinned on Y (§11 point 7); the re-pin is part of the S1 package's integration, recorded with its justification.
5. **The O-ext unit runner.** `scripts/stage1_s1/oext_eval.py` has only `check`; no command runs the O-ext pass on an engine unit. Ambitious default: build `scripts/stage1_s1/oext_unit.py` as an S1 package addition after the S1 fix round, to B15's contract parser, with tests and mutants. Pre-set fallback (trigger: not verified before block A's funding event is recorded): the kit's `record-oext-fallback` route, status `dev100_recipe_cap` (§11 point 1's fallback (c)).
6. **B15 round 2** (one more build round, after D-2 and `oext_unit.py` are verified): J5 calls the D-2 wrapper (§19 point 3); the plan-A/B record names Gate B's verdict file by SHA-256 and the kit reads σ̂ from it, so no σ̂ is typed by hand; the S1 package's final hashes are pinned.

## 21. D-2 also covers J8, the content classifier (extends §19; 2026-10-23T15:46 UTC; decided by the lead under the user's delegation)

**Facts (M: D-2's verifiers, wf_5c07683e).** `scripts/stage1/score_classifier.py` (REQ-23, B15's J8) loads the same W1 pins file when it is given no pins (`score_classifier.py:71`); its `main()` never passes pins (`:162-164`), and it refuses a plant or decoy pool whose pin is null (`:81-82`). The in-place fill that the W1 rule describes would have reached J8 as well, so §19 point 1 ("the fill rule's content is applied exactly") needs J8 covered.

**Ruling.** §19 extends to J8. The same package gets `d2_score_classifier.py`. It loads `score_classifier.py` by path after its SHA-256 check against the W1 manifest, runs D-2's checks on `--pool-pins` and `--req8-record`, and calls the module's own `main()` with only its `run` given the filled pins for that call (`run()` already takes `pool_pins=(doc, sha)`, `:55-56`). No W1 line changes. B15's J8 calls this wrapper. The pre-set fallback is §19 point 4's, applied to J8: J8 scores without the plant and decoy pools, and those rows are reported as "not run".

## 22. Before the certificate pod: the binding check's numbers (LQ21), C3's subsample file (Q13) and Y's F5 round (2026-10-23T16:16 UTC; decided by the lead under the user's delegation)

1. **LQ21, the binding check (REF §R.2.8; YB Q-11; ADD §15 point 4; B15 Q17).** Fixed before the certificate run. The statistic is `constrained.mean_weight.t2_5` in C2's `steps.jsonl`, at each of its 38 steps (B+Qi, seed 1101, to e1, training only). **"Binds"**: the value is ≤ 0.50 at some step s ≤ 3. **"Equals recipe B by construction"**: the value is ≥ 0.90 at 20 or more of the 38 steps ("most"). If neither holds, the label is "partly binding". If both hold, both labels are reported. The labels are training statistics, not outcomes; the paper states that the check was seen. The lead never drops or changes B+Qi on them. If "equals recipe B by construction" holds, the lead writes a proposal to the user, and B+Qi runs as registered unless the user decides otherwise. The thresholds go into B15's C2 thresholds record before the certificate pod is planned.
2. **Q13, C3's subsample file.** C3 is the pod smoke of Y2's subsample path and touches no hidden data, so it needs no random draw: the file lists the first 16 item ids of P's dev bank in the bank's own order, in the format Y2's checks require. No label is added. A small Mac script writes it with a text-free record, built and tested before use. Fallback (trigger: not verified before the certificate pod is planned): C3's smoke is dropped and the record says so.
3. **F5 (§15 point 8) lands before any certificate run.** It changes Y's identity, and a certificate is valid only for the identity it ran on. After F5: Y's strict X → Y certificate on the golden and its suites and mutants are re-run, the new identity is frozen by hash and backed up as 34bfd288 was, and B15 round 2 pins it. Fallback (trigger: F5 not verified after one fix round): Y stays at 34bfd288, and B15 refuses a B+Qi recipe with LoRA dropout ≠ 0 at plan time instead (recipe S and B+Qi's recipe both have dropout 0).

## 23. F5 is already met at Y 34bfd288; Y keeps its identity (extends §22 point 3; 2026-10-23T17:56 UTC; decided by the lead under the user's delegation)

**Facts (M: workflow wf_dfe3c842, Opus; build and verifier both pass).** Engine X's `validate_recipe` already fixes LoRA dropout at 0.0 for every recipe (`_fixed(lora["dropout"], 0.0, "model.lora.dropout")`), and `Session.__init__` runs it before any model loads. On the frozen Y 34bfd288, a B+Qi recipe with dropout 0.05 or 0.1 is refused with X's message: 5 of the 7 new F5 tests pass there, and the 2 that fail call `validate_constrained_sft` directly, which no engine code does. The F5 build (identity c641c84b: 3 inserted lines in `config.py`; strict X → Y certificate, golden, harness and 71/71 mutants all pass) adds no refusal on any path the engine takes.

**Ruling.** Y stays at 34bfd288 (frozen and backed up, §15). c641c84b is not adopted; its tree (`ws-y2`) is kept as evidence until stage 1 ends. F5 is recorded as met by X's own check, and B15 pins 34bfd288. The record is `research/experiments/2026-10-23-stage1-deviations/f5-resolution.json`. C3's file carries the free-text `draw.label` "c3-dev-first-16-in-bank-order", because Y2 requires a non-empty label; no entry is added to the label registry (§22 point 2).

## 24. The S1 package is merged and fixed: the lead's rulings on its open items (2026-10-23T20:24 UTC; decided by the lead under the user's delegation)

Workflow wf_64cbfeb6 (Opus: merge, the small builds, the O-ext build, two verifiers, two fix rounds) is done. `scripts/stage1_s1/` in ws-s1: 744 tests pass with the W1 suite's 874 (1,618 in one process; 0 skipped); every spec run in full on the post-fix tree: 486 mutants, 484 killed, 2 expected survivors, 0 invalid (B10 152/152, B11 107/107, B14 87/87, B17 80 + 2, O-ext 58/58). Engine X 472fc7f6 is unchanged; outside `scripts/stage1_s1`, ws-s1 equals its base.

1. **Mutation layout.** Option (b), as fix round 1 built it: the three test-tooling edits (`run_mutants_b14.py`, `test_b14_pins.py`, `test_b17_mirror.py`) let every spec run from the committed layout. Every later re-pin re-runs the specs in that layout.
2. **LN-14's bar at n = 400.** W1-18's bar is stated per 100 answers ("at least 97 of 100 flags agree and the refused count moves by at most 2", `limits_overrefusal_checks.json` `truncation`). On θ0's 400 PHTest answers it is read at the same rates: at least 388 of 400 flags agree, and the refused count moves by at most 8. The literal counts (97 and 2) would make the agreement test empty at n = 400.
3. **The five regression suites of §11 point 14**, named now (they are independent of the S1 package): (i) `experiments/safety_selection/tests` (engine X, with the Gate B kit and reading tests); (ii) `scripts/stage1/tests` (W1); (iii) `scripts/stage1_s1/reading/tests` (B16); (iv) `scripts/gate_b_mac_judges/tests`; (v) the post-W1 packages' tests (`d1_spool`, `d2_pool_pins`, `c3_subsample`). Each must pass, with its known environment skips listed, before the explicit-path commit.
4. **§11 point 11, B16's side** (HB-C of the halves from `cells_u_pp`) is a B16 change. It is built in a B16 round before block B's reading. Fallback (trigger: not verified before the reading runs): §9.4 prints B14's per-contrast paired form as its interval and says so.
5. The review's smaller notes (the θ0 unit check in `evaluate_transfer`, B17's readable `oext_guard_cut` seconds, the stale `labels_sha256` and `sources.ADD` fields, the cap-switch rule enforced by procedure) are handled at §11 point 7's re-pin or by B15's plan checks; none blocks block A.

## 25. B15 round 3a: block A's whole-block plan; the lead's rulings on its open points (2026-10-23T21:07 UTC; decided by the lead under the user's delegation)

Round 3a (workflow wf_3c3ef3ee, Opus: builder, two verifiers, one fix round; 365 B15 tests and Gate B's 271 kit tests pass) makes block A's funding event cover the whole block before S1-0 launches. It does this through a block-A launch plan recorded before S1-0: S1-0, the certificate pod, the diagnostics pod, the LN-12 pod(s), the arm launches, then HarmBench and Granite. A plan that leaves out required block-A work, or a launch that departs from the plan, refuses. The kit's need for plan A, Branch full: default arm split 2+2+1, $115.16; all five arm pods in one launch, $127.34 (Branch 128: $107.23 / $119.76).

1. **LN-15e.** §17 adopted Q19's default: the A1 re-score runs in block A through the kit's retrain and diagnostics kinds; V2a stays on its fallback (FO-04's figures as the limit), because no V2a script exists. So the re-score enters the block-A plan in round 3b and is priced there. It is not left out.
2. **Judge units: 27.** Block A's 20 new units, the 6 reused units re-judged by §17 Q14, and θ0's unit, so every contrast uses one judge device. Default need with 27 units: $116.31, before the re-score.
3. **The top-up asked of the user** is the recorded plan's **worst-case** need across the arm splits (all five arm pods in one launch) with the re-score and 27 units, rounded up to the dollar. Every re-plan inside block A then stays covered. Money a pod does not spend stays in the RunPod balance. By §17's last line, the top-up itself must cover the need; the Gate B balance does not count toward it. The exact figure comes from round 3b's kit.
4. **Stated limits, accepted:** a hand edit that rewrites plan.json and S1-0's funding record together passes the plan checks (the funding record also carries the user's verbatim words, which a reviewer can check); HarmBench before Granite is an operator rule (the judge launcher runs outside plan.json; run in parallel the need rises by about $0.19).

## 26. c0 runs on engine X in block A's LN-12 pod (revises §20 point 4; 2026-10-23T21:08 UTC; decided by the lead under the user's delegation)

c0 (LS-15 (i); B17's `lean_eval_job.py` on Gate B's R_1 edit at seed 1101, `--expect-adapter-fingerprint` R_1's e1) evaluates a unit that was trained on engine X. The certificate pod runs engine Y, the kit allows one engine per pod (G4), and B17's settings pin engine X. Running c0 there would need B17 re-pinned on Y, justified by the X → Y certificate that runs on that same pod. That is circular. So c0 runs on engine X in block A's LN-12 pod, the engine its source unit ran on, and B17's verified pin stays. REV4 §10.3 placed c0 on C1's pod to share a pod; the move is a scheduling change inside block A, and nothing measured changes. B15 round 3b moves c0 in the block-A plan and prices it there.

## 27. B15 round 3b: block A's top-up is $144 (2026-10-24T08:14 UTC; decided by the lead under the user's delegation)

Round 3b (workflow wf_61c6b9c0, Opus: builder, two verifiers, one fix round; 418 B15 tests and Gate B's 271 kit tests pass) pins the S1 package from main, prices LN-15e's A1 re-score (two linked retrain and a1_rescore pairs on the LN-12 pod), adds 27 judge units, and moves c0 to the LN-12 pod on engine X. The kit's needs, plan A, Branch full: default split 2+2+1, $130.59; all five arm pods in one launch, $141.63. The fix round found one valid in-block re-plan that needs more: c0 alone on a second LN-12 pod, with the five-in-one arm launch, needs $143.19.

1. **The top-up asked of the user is $144**, the worst-case need over every valid in-block re-plan, rounded up to the dollar, so §25 point 3 holds. Money not spent stays in the RunPod balance. The top-up itself must cover the need; the Gate B balance does not count.
2. **LN-15e's Mac reading** (the top-600 Jaccard and Kendall τ of each re-score against the sealed A1 set, per REV4) has no script yet. The kit produces and seals the re-score's attributes units. The reading script is built and verified, beside `scripts/stage1/report_a1_variants.py` and outside the kit, before those units are read. Fallback (trigger: not verified when block A's seal is lifted): LN-15e reports its FO-04 figures only, and the paper says so.
3. **Block A completes only when every job its recorded plan requires has run, or has a recorded lead decision with a reason** (round 3c; round 3b's VP3b-3).

## 27a. Correction: block A's top-up is $145 (2026-10-24T08:52 UTC; corrects §27 point 1; decided by the lead under the user's delegation)

Round 3c's builder recomputed the re-plans with the kit's own functions. Eight of the 1,023 two-LN-12-pod layouts need $144.06: the ones that put θ0's LN-14 report on a pod with no O-only pass, which adds one more 42-minute overhead. Three LN-12 pods need up to $145.63, and eleven need $158.16. No top-up covers every valid layout, because each added pod adds overhead. So §27's "every valid in-block re-plan" is replaced by: **every arm split, with one or two LN-12 pods**. The figure for that is $144.06, rounded up: **$145**. A re-plan with three or more LN-12 pods needs its own funding event. The kit refuses any re-plan whose need exceeds S1-0's funding record, so no money is at risk. If the user's top-up is $144, every one-pod layout and every two-pod layout that keeps LN-14 beside an O-only pass is covered (at most $143.68), and the kit refuses the eight layouts above.

## 28. S3's scorer needs one pass over both pools (post-W1 deviation D-3); launches in parallel while the guard is off (2026-10-25T15:48 UTC; decided by the lead under the user's delegation)

**Facts (M).** J5 ran as B15 built it, from the brief: a main pass over plant, decoy and s3_safe, then a pools-only pass over s3_orig after J6 (pod a-8, both complete). `scripts/stage1/score_s3_datarx.py` (REQ-11, W1) reads ONE rows file and ONE summary, and refuses unless that summary lists both s3_safe and s3_orig with the SHA-256s their builders recorded (`score_s3_datarx.py:84-88`). So REQ-11 cannot run on the two passes as they are.

**Ruling D-3.**
1. Every W1 file stays byte-identical. A new wrapper `scripts/stage1_s1/d3_s3_union/` checks both passes' summaries and rows by SHA-256: same kind, same representation_pass script and settings, same engine, model and layout; s3_safe from the main pass and s3_orig from the pools-only pass, each at the SHA-256 that the S-pool record and J6's record give.
2. It writes their union: the s3_safe rows of the main pass, then the s3_orig rows of the pools-only pass, each unchanged. It also writes a union summary: the main pass's summary with both pools listed, the union's rows SHA-256, and a "d3" block naming both sources by SHA-256.
3. It then runs `score_s3_datarx.py`, loaded by path after its SHA-256 check against MAN1, unchanged, on the union.
4. **Condition:** the builder shows from `representation_pass.py` that each row's features depend only on that row (one unbatched forward per row), so the union equals what one pass over both pools would give. If not, D-3 is not used, and the fallback runs.
5. **Fallback** (trigger: the condition fails, or D-3 is not verified after one fix round): one pools-only J5 pass over s3_safe and s3_orig together, on a pod, recorded as a new pass composition and not a re-run.
6. S3's selection (`write_score_add.py`) and its add edit (REQ-7) follow as written.

**Launches in parallel while the guard is off.** The user removed the budget guard and manages the balance ("remove the guard its not needed I can control it better"). While that decision is recorded, `release` may release the next launch of a block before the earlier launches' hosts are done. The plan's order, the plan's need against the funding record, the $10/h price limit, the in-pod timers and stop-never-delete all stay. With no guard-off record, the old rule (wait until the earlier launch is done) holds.

## 29. LN-15e's re-score units were not pulled; LN-15e takes its fallback; two kit gaps (2026-10-26T06:41 UTC; decided by the lead under the user's delegation)

**Facts (M).** Pod a-2 (block A's LN-12 pod) completed all 19 jobs. The engine's verify passed on the pod, and the finisher verified the 17 units it pulled. The LN-15e jobs 12–15 (retrain a0 at 1102 and 1103 and their a1_rescore) wrote their units under `rescore/`. The kit's light pull (`host.py` `PULL_ITEMS`, Gate B's list) does not include `rescore/`, so those four units are only on a-2's stopped volume. The kit has no start command, and a stopped kit pod is never restarted (REV4 §11; G6).

1. **LN-15e takes its pre-registered fallback:** FO-04's figures as the limit (REV4 LN-15e; §25 point 1). a-2 is not restarted and nothing is re-run. The paper states that the re-score ran on the pod but its units were not retrieved, because of a kit defect.
2. **Kit gap 1:** `PULL_ITEMS` must include `rescore/` (and every folder a stage-1 job writes a unit to), with a test that every unit path a job records lies under the pull list.
3. **Kit gap 2:** `record-done a-2` refuses while jobs 12–15's units are missing. The kit needs a lead decision record for jobs whose units were not pulled. It records them as "complete, not pulled", the seal lists them without hashes, and block A's completeness counts them as decided.
4. **Kit gap 3 (the finisher):** `finisher.py` light-checks only Gate B's roles ("job", "first", "anchor"), so stage-1 diagnostics and arm pods were not light-checked. The lead ran the same light check by hand: a-3, a-4, a-9 and a-10 have 9 units each, all good.

## 30. Block A's judges run by the runbook; the judge gaps are fixed before block B (2026-10-27T08:23 UTC; decided by the lead under the user's delegation)

The runbook is `notes/judge-runbook.md` in the lead's worktree (read-only agent, 27 Oct). It found these gaps: (1) the kit counts a judge launch complete when it is released; (2) `seal.py` checks only that `judges/A/` is not empty; (3) the judge route prints per-unit outcome counts; (4) B10 units are refused on the judge pod (block B only); (5) the kit holds only the count of 27 units; (6) the launcher's own balance guard; (7) nothing pays for a judge re-launch.

**Ruling.** Block A's two judge launches run now, by the runbook:
- HarmBench, then Granite only after HarmBench is verified;
- launches from a background job only;
- all launcher output goes to files nobody opens, and only the listed fields are read (LW-35);
- the judge files are written to a staging folder and moved to `judges/A/` only after the 54-file check;
- the seal waits until both judges are verified.

A kit round before block B fixes gaps 1–4:
- a judge-completion record that a judge launch needs before it counts as done;
- `seal.py` requires one file per judge for each unit;
- a seal-safe wrapper for the judge route;
- B10 units accepted on the judge pod.

A Granite failure in block A is recorded in FOCUS and in that round's completion record.

## 31. The cert pod's two blockers; the kit round moves before the cert pod and the seal (2026-10-27T10:42 UTC; decided by the lead, GI VII, under the user's delegation)

A read-only worker wrote the cert-pod runbook (`tmp/gi-vii-notes/cert-runbook.md`, SHA-256 `7950c0f2…`). It found that the cert pod cannot launch as packed, and the lead checked the two code claims:
- **D1.** Engine Y's pack has no `cert_spec` input, and C1 needs it (`setup/job_runner_stage1.py:434-436, 559-560`); `check-plan` refuses at $0.
- **D2.** The runner gives C1 an empty registry with `--replicate-of`, and engine Y's `claim_trajectory` refuses a `replicate_of` that is not a live registry line (`tmp/engine-y-34bfd288/experiments/safety_selection/jobs.py:307-308`). C1 would crash on the pod after the setup is paid.
- **D3.** `seal.py block A` refuses `a-5: record-done first`: `seal_block` loops over every block-A host (`seal.py:62-66`), and a-5, a-6, a-7 were moved and never pulled (`done` false).

**Ruling.**
1. D2 is fixed by seeding, not by dropping `--replicate-of` (that would deviate from YB X-5's determinism control). Before C1 runs, the runner writes R_1101's registry line from the packed `cert_spec` after checking its SHA-256, `registry_line.run_dir == replicate_of`, the key against C1's own key, and that the registry file is new. Kit round 30a, with a seal-safe C1 comparator (D4) for the certificate record.
2. D3 (the seal skips a moved, not-done host and lists it as moved) and D10 (`seal.py status` ends a pod's time at its finished or confirmed stop) join kit round 30 (judge gaps 1–4, §30).
3. Order: both rounds land before the cert pod and the seal. Then `cert_spec.json` and the new pack-inputs record (runbook step 3), the Y re-pack before `init-block cert` (D11), the cert pod, `record-judges A`, then `seal.py block A`. `seal.py block A` does not itself need the cert block; cert-then-seal stays the operator's order.
4. A cert re-run is not paid by block A's contingency ($2.95 left; D5). Any requeue or defer of the cert host waits for a decision under the frozen money rules.
5. (11:30 UTC) `compare_c1.py` keeps `job.json` in the certificate's comparison. It drops only `code_sha256` and the edit's path (the arm pins the edit's bytes), after checking that C1's `replicate_of` is R_1101's run folder and R_1101's is null. Leaving `job.json` out (YB X-5 does not list it) was the looser option.

## 32. Block B's $0 preparation: its judged units, its judge routes, the HB-C halves and LN-15e's fallback script (2026-10-27T14:24 UTC; decided by the lead, GI VII, under the user's delegation; the user: "Yes: start block B's $0 preparation now (the block-B judge gaps, the B16 HB-C halves, the LN-15e Mac script). I'll top up for block B separately.")

1. **Block B's judged units.** Every block-B unit that carries dev-bank answers is judged by both judges in one launch per judge: the arm and a0_arm runs, the trained references' evaluation units (`ref_train`: recipe G and B+Qi), and B10's evaluation-only reference units (`ref_eval`, `safe_lora`). Reason: every contrast the reading may form then uses one judge device (the reason of §25 point 2). The pre-registration reads the references on U, O and task loss; judging more units than the reading uses changes no label and costs about $0.03 per unit per judge (block A's measured rate). The kit checks that each block's judge launch covers its planned judged units. **Fallback** (trigger: a `ref_train` unit cannot be judged on the pod as built): it is listed as not judged with the reason, and no harm sentence is written about that reference.
2. **Block B has no re-judged units.** Gate B called no extension, so R_4 and R_5 are trained, not reused (README G6); every block-B unit is new. `REJUDGED_PINS["B"]` is empty by rule, with a test.
3. **Kit round 31 (the block-B judge gaps and two cert-pod gaps):** a not-run decision route for a released judge launch of any block (not only block A), also after that block's seal; the judge-unit coverage check of point 1; whether a resumed judge launch (`--resume-from`) records under one tag, and the smallest change if not; the stage-1 wrapper prints no judge count in a bundle or launch record (the dry bundle printed Gate B's known-answer reference count); the finisher no longer waits for moved, not-done hosts (cert runbook D9); `launch.py` exits non-zero when it made no pod (D7). Gate B's judge files stay byte-identical.
4. **B16's HB-C halves (§11 point 11, §24 point 4)** are built now, in a B16 round, with an independent statistics check. §24 point 4's fallback stays: if not verified before block B's reading, §9.4 prints B14's per-contrast paired form and says so.
5. **LN-15e's Mac reading is built in its fallback form only.** Its four re-score units were not pulled and a stopped pod is never restarted (§29), so the Jaccard and Kendall τ reading can never run. The script, beside `scripts/stage1/report_a1_variants.py`, writes LN-15e's report from FO-04's pinned figures (`a1_variants.json`) and the §29 decision record, and states the limit. It reads no sealed stage-1 file.
