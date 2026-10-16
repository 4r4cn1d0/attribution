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
