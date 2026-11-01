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

## 33. B16's HB-C halves: the lead's rulings on the independent check; post-W1 deviation D-4, REML by multi-start (2026-10-27T17:05 UTC; decided by the lead, GI VII, under the user's delegation; before any stage-1 outcome is read: block A is sealed and unread)

The B16 round of §32 point 4 built `scripts/stage1_s1/reading/overlap.py` in a scratch tree. An independent verifier (synthetic data only; its own error-contrast REML likelihood and a multi-start maximizer; 7,186 fits) found: the overlap control implements §9.4's text as written; the halves' fit is the primary U fit on the subset; no pre-existing output key changes. It also found three things to rule on.

1. **Which contrasts §9.4 covers (C1).** The built default was the primary family's orientation (P4 a0 − S1, P5 S1 − S3, P6 S1 − S4). **Ruling: the add effect against a0 governs** (a0 − m for each add arm, each on its own add set's halves; under plan B, the add arms plan B runs). Reasons: §9.4's source (PLAN-S:172, LS-19) says "the add effect"; §11 point 11 computes it "from `cells_u_pp`", which holds a0 and the add arm only; B14 reports that orientation; under the primary orientation plan B would leave S1 out and §24 point 4's fallback would switch contrasts. The primary-family orientation is printed beside it, labelled report-only.
2. **Post-W1 deviation D-4: REML is computed by multi-start.** B16's REML fit, started from the pre-registered start values with LN-35's active_set rule, stops at a lower local maximum of the restricted likelihood in about 0.4% of plan-A cluster fits and 5.4% of block-A-only fits (verifier; the builder's rates agree). Every large miss is a boundary maximum (a different arm floored). The contrast estimate never changes (it is the paired mean), but the seed-part half-width moves by a median of 27–32% when it misses (block A only), up to 4.7×, and one synthetic block-A-only reading changed a label (P4 "better" → "inconclusive"). The pre-registration names the estimator REML and fixes the start values; in these cases they disagree. **Ruling: the estimator governs.** Every B16 REML fit (the primary reading's and the halves') runs from the pre-registered start and from each floor pattern of its cluster (a fixed, deterministic set of starts), each under LN-35's rule; the end point with the highest restricted log-likelihood governs. The pre-registered start's fit is printed beside it as a sensitivity, with a flag when the two differ. Recorded before any stage-1 outcome is read. Fallback (trigger: not verified before block B's reading): the pre-registered-start fit governs, the multi-start maximum is printed beside it, and any label that differs between them is reported as "not robust to the REML start".
3. **Swapped halves (Q5).** A lower and higher half swapped together with their `cells_u_pp` labels passes the schema. **Ruling:** B16 refuses an overlap block whose lower half is not the lower-similarity half by B14's split rule (ties as B14 breaks them), bound to B14's report by its SHA-256.
4. **Smaller rulings.** The block-A-only overlap output carries the "block A only" suffix (C10). LN-35's 25-step stop stays (pre-registered); it stops 10–23% of plan-A fits and 6–13% of block-A-only fits with no verdict change in the verifier's runs; the README states the expected rate. Under a true null on both halves "holds" fires about 9% of the time (the rule does not require significance on all prompts); the paper's wording says so.
5. **Gap found: no B16 input builder exists.** B16 reads one text-free input document (`--input tables.json`); no code builds it from the sealed stage-1 units, the judge files and B14's report. It is built (synthetic-folder tests only; it prints no value) after this fix round and before block B's reading, keyed by COMPLETE.json SHA-256 and the `ref-*` labels of kit round 31.

## 34. Block B's pre-flight: the lead's rulings (2026-10-29T10:28 UTC; decided by the lead, GI VII, under the user's delegation)

A read-only pre-flight (`tmp/gi-vii-notes/block-b-preflight/block-b-runbook.md`, SHA-256 `bd466b4d…`; kit dry runs only, no write, no pod) found that the kit plans every part of block B (cap-based need of the drafted plan $165.04 with the certification pod; the full LN-15b reference set $245.55) but cannot yet run all of it. Gaps G1–G14 are in its §0. Rulings:

1. **Engines (L1).** Block B's arm runs, recipe G and the evaluation-only references run on engine X (B10, B11 and the O-ext code pin X; block A ran on X); B+Qi runs on engine Y (it needs Y; the X → Y certificate passed, §31).
2. **Order (G6, G11).** The B10 certification pod runs and is recorded before `init-block B`, because `init-block B` runs once and block B has no not-run route for non-judge jobs. Only parts that will run are planned.
3. **G1, B+Qi's O-ext on engine Y: built** (an S1 and kit round: Y-side O-ext settings that pin Y and allow B+Qi's config, packed on Y; every X-side S1 file stays byte-identical, because block A's O-ext outputs name their settings by SHA-256). Fallback (trigger: not verified before B+Qi's launch): B+Qi is read on U, L and the dev-100 O at its recipe cap, and the paper states that its O is not on the 500-prompt bank.
4. **G5, the safety prefix (SP).** The lead pins one published safety instruction's exact UTF-8 bytes (file, SHA-256, citation) in B10's settings and with `record-prefix`, chosen from published sources by a read-only worker and confirmed by the lead. SP is an approved reference at a0 1101–1103 in every scope.
5. **G3 and G4 (λ = 0.9; references at a0 1104–1107)** are built if the user funds LN-15b's full reference set (US-01 (a)); 1105–1107 need a second reference phase after block B's a0 arm pods, with a B10/B11 re-pin in between. If the top-up does not cover the increment, LN-15b's pre-set fallback (the 3-seed references) applies and G3/G4 are not needed.
6. **G6 and G11 are built** (a kit round): a lead not-run decision for block-B and certify jobs, and a failed B10 certification recorded as complete with a failed gate.
7. **Smaller rulings.** G10: the K = 0 Safe LoRA point runs on the 1101 reference pod (a scheduling change, as §26 did for c0). G9: if the pod's V-check shows V′ is needed, V′ is reported as not run with the reason (a stated limit). G8: one funding record for block B covers the certify and B inits together. G12: accepted and stated (all stage-1 pods so far had one driver). G13: the judge launch's units are listed from plan.json, never by `--run-root`. G14 (LN-18): decided by the user (`134304bb…`).
8. **LN-15d (B↓LR, SR, S6) and US-17 (the Safe LoRA norm-matched control)** have no kit route; they are not in block B unless the user funds them separately (each needs its own build).

## 35. Reading an adapter fingerprint after block A's seal; the SP reason's text (2026-10-29T12:20 UTC; decided by the lead, GI VII, under the user's delegation)

1. **Adapter fingerprints are readable by rule, wherever they are stored.** The pre-registered seal rule (B15 brief G5) reads: "after block A only cost ledgers, completion records and adapter fingerprints are read". a0's e1 adapter fingerprint at seed 1104 (block A, host a-10, unit `round1/1104-a0-e1-a1`) is stored only in sealed-class files (`states/e1/state.json`, COMPLETE.json). Block B's references at 1104 need it (B10's reference unit, B11's accepted fingerprint). **Ruling:** a reviewed extractor, tested on synthetic folders, checks the unit's files against the block-A seal's SHA-256, parses `states/e1/state.json` and extracts only the fingerprint field into a readable record (`*adapter-fingerprint*.json`); it never prints or writes another field. The lead runs it; nothing else in a sealed file is read. Block A's seal file is unchanged (reads only).
2. **Block B's a0 runs write the readable record themselves.** Kit round 32 makes the job runner write `job-I/a0-adapter-fingerprint.json` for each a0 arm job and list it in JOB-DONE.json, so the 1105–1107 re-pin needs no extraction.
3. **SP's reason, a text correction.** The pre-registration (rev 3 §5.1 and rev 4 line 441) says SP is a user-turn prefix because "OLMo-2 has no system turn". OLMo-2's chat template has a system branch; the model card documents no system turn and no default system prompt. The corrected reason: "no documented system turn or default system prompt". The design (a user-turn prefix joined by "\n\n") is unchanged; B10's settings carry the corrected text.

## 36. The user's rule: start a block from the balance; the user funds when they choose (2026-10-29T13:51 UTC; the user's decision, recorded by the lead, GI VII)

The user (GI VII chat, verbatim): "no just start it now ill fund it when i feel like this is a rule", after "theres 146 in there right now use that first" and the lead's question whether to record block B's funding as $246. Record `.ai/inputs/stage1-post-w1-20261023/block-b/user_decision_start_without_topup.json` (`5f31f16e…`).

1. **The rule (the user's; it replaces the funding-event rule of 23 Oct for block B and later blocks, until the user says otherwise):** a stage-1 block starts from the RunPod balance without a top-up that covers its cap-based need; the user funds when the user chooses. The lead tells the user at once when the balance is below $10 (25 Oct rule). The $10/h create limit, the in-pod cap timers and stop-never-delete stay.
2. **The kit (round 32's `funding_record`, a lead change with a test and a mutant):** a funding record may name the source `user rule: start from the balance`; its `amount_usd` is the plan's cap-based need, and it names the decision record `{path, sha256}`, re-hashed at every use and checked for the decision's kind and the user's words. A record with any other source still refuses. Kit suite 665 passed; mutant `B15-36-funding-decision-unhashed` killed.
3. **The lead's operating safeguard (not a refusal of the rule):** block B launches in stages (the certification pod; phase 1; phase 2; the judges), each when the live balance covers that stage's cap-based spend, so the account cannot run dry with pods mid-job. If a stage does not fit, the lead tells the user and waits for a top-up.

## 37. The HarmBench claim reader: the lead's rulings on its readings; two block-B judge requirements (2026-10-29T14:59 UTC; decided by the lead, GI VII, under the user's delegation)

A builder added `scripts/stage1_s1/reading_input/hb.py` (per-cell, per-prompt HarmBench "yes" shares from the judge pod's label cache, bound through plan.json's judge record, the seal and the run record; each unit's counts checked against its judge file) and `hb_claim.py` (the HB contrast by B16's own unchanged code: HB-C with U's floor, the item part, Satterthwaite df, the 90% interval; equal to B16's U contrast on U's own table; then the sentence word). B16 is untouched (its outputs hash every `reading/*.py`). Gate B's judge files hold counts per unit only; the per-answer labels live in the pod's cache, which block A's runbook copied under `judges/A/pods/` before the seal.

1. **R1 (LN-15c read "respectively"):** an "equivalent" contrast says "restored refusal"; an "inconclusive" one says "no restored refusal shown". Accepted.
2. **R4 (the E_HB threshold):** E_HB is the point estimate HB(a0) − HB(θ0) over the reading's a0 seeds (the 8 Oct definition: the seed mean), not its lower bound. Accepted.
3. **R8 (devices):** a contrast whose units were judged on more than one device type gets no "harm" sentence and a flag. Accepted (conservative).
4. **The extra check:** B10 units must name engine X's O-ext settings pair; B+Qi ref_train units engine Y's pair (§34 point 3). Accepted.
5. **Block B judge requirements (operator rules):** block B's HarmBench launch runs on the same GPU type as block A's (A100-SXM4-80GB; under plan A every contrast and E_HB span both blocks); and block B's HarmBench `run-record.json` and `harmbench-pod.jsonl` are copied under `judges/B/pods/<tag>/fetched/out/` before `seal.py block B` (block A's runbook step 11 optional copy becomes required).
6. **Not built (stated):** Granite–HarmBench agreement (not asked by the pre-registration), HB-2's report items, the references' HB values.

## 38. The user's decision: block B's twelve stopped pods are started once, only to pull (2026-10-29T22:00 UTC; the user's decision, recorded by the lead, GI VIII)

**Facts (M; FOCUS 2026-10-29T21:24 UTC, commit `495e4c5`).** The finisher GI VII started was killed at about 17:35 UTC. Each job runner shortens its pod's in-pod stop to 1 h after its job (`setup/job_runner_stage1.py`:1159-1161), so b-1, b-2, b-3, b-5…b-10, b-21, b-11 and b-16 finished their jobs and stopped themselves unpulled between 18:32 and 21:14 UTC ($84.37 by the pod records). Every kit route (record-done, record-unpulled, record-not-run, defer) needs a pulled JOB-DONE.json. PREREG revision 5 §9 (frozen) says "A stopped kit pod is never restarted", and REV3 §14.3 says a user's go does not change a frozen rule inside the lead's delegation. So the lead asked the user.

**The user's decision (GI VIII chat, verbatim): "Restart once to pull"**, the option the lead described as: "I approve a recorded deviation from PREREG rev 5 §9 for these 12 hosts only. Start each stopped pod once with a short in-pod cap, only to pull, light-check and stop; no job runs." Record `.ai/inputs/stage1-post-w1-20261023/block-b/user_decision_restart_to_pull_block_b.json` (`bd13c8f4…`). The alternative (keep the rule; a kit route; re-run the twelve hosts' jobs on new pods; about $63 of pod time and a top-up of about $70–90) was declined.

1. **Scope:** the twelve named hosts only, each started at most once; no other host and no later block. The paper reports this as a deviation from PREREG revision 5 §9, with its cause (a killed finisher) and its limits.
2. **The route (administrative, no experiment logic):** `.ai/inputs/stage1-post-w1-20261023/block-b/restart_to_pull.py` (`0cbaaa64…`). Per host it refuses unless the decision names the host and hashes as recorded, the host logged job-started, and it has no `finished.json`, `restart-to-pull.json` or `cap-override.json`, and RunPod reads the pod EXITED. It renames `known_hosts` (a restarted container has new SSH host keys), writes `restart-to-pull.json` and `cap-override.json`, writes the creation environment back with a fresh in-pod cap of at most 60 min (the timer obeys the most recently issued authority, so the new cap outranks the job-end lease), starts the pod and waits until it reads RUNNING. No job, preflight or setup step runs. The running finisher then pulls the light tar, scans it, light-checks every unit against its COMPLETE.json and stops the pod (never deletes it). record-done follows as for any host.
3. **Integrity:** the pulled units are checked exactly as an unbroken run's are (the engine's verify ran on the pod before the stop; the light check re-hashes every pulled file against its unit's COMPLETE.json; record-done checks each job's COMPLETE.json SHA-256). The restart adds no write to the run folder: the only in-pod writes are the timer's own records and the finisher's stop lease.
4. **Money (the user's balance rule, §36 point 3):** one canary pod first (b-16), then the rest in groups whose cap-based upper ($1.85/h × the cap) fits the live free balance above the $6 reserve. Cost per pod is its run time from the restart to the stop × costPerHr; the cost report counts the first run and the restart separately.
5. **If a start fails** (for example no free GPU on the pod's machine), the lead records it and asks the user again.
6. **The user's second decision (2026-10-30T10:52 UTC; GI VIII chat, verbatim: "Yes, zero-GPU pull").** Under point 5, the GPU starts of b-1, b-2, b-3, b-6 and b-7 failed on 29 Oct at 22:06–22:08 UTC ("There are not enough free GPUs on the host machine to start this pod"), and b-14 (ref_eval at a0 1104) stopped itself unpulled at 00:41:51 UTC on 30 Oct while the Mac slept. The lead asked: "Start b-1, b-2, b-3, b-6, b-7 and b-14 once with zero GPUs to pull them?" Record `.ai/inputs/stage1-post-w1-20261023/block-b/user_decision_restart_to_pull_block_b_2.json` (`87237f57…`): the six hosts, the same limits, a zero-GPU start (RunPod's documented route to a stopped pod's volume when its machine's GPU is taken: GraphQL `podResumeZeroGpu`), and a retry of a start that failed (a failed start did not start the pod, so each pod is still started at most once). Route `restart_to_pull_v2.py` (`f065844f…`; v1 is unchanged at its path): `--retry-failed-start` renames the failed attempt's records with the suffix `-attempt-STAMP`; `--zero-gpu` uses `podResumeZeroGpu`; both are refused unless the decision file allows them.

## 39. Before the stage-1 reading: the lead's rulings ([FILL-time]; decided by the lead, GI VIII, under the user's delegation; before any stage-1 outcome is read: blocks A and B are sealed and unread)

Before the one-time reading, every reading rule is written down, so that nothing is chosen after an outcome is seen.
Blocks A and B are sealed and unread (FOCUS:107, :77). Each point below is listed in the S1 blinding record with the
Gate B values read before it (REV4:919; W1R:358), and the paper labels it "fixed after Gate B wave 1".

- **Scope.** Every stated reading that CRIT §2.1 lists (CRIT:125-148; its decision 10, CRIT:354). Points 1 and 2 are
  D-5 and D-6; points 3-11 the stated readings; points 12-15 B14's scheduling gap, D-7, ADD:428's simulations and the
  build round's hard-rule notes. Each point quotes the stated reading, then gives the ruling. The default is to adopt
  the stated reading; no report shows any of them wrong.
- **Citations** are `path:line` at commit `55d5f8b` (`git show 55d5f8b:<path>`). FOCUS lines are 55d5f8b's: the
  anchored-stamp entry added one line at FOCUS:74, so every FOCUS line from 74 on is one higher than at `0daca9a`
  (the `55d5f8b` pin stays in every citation header, no remap: LR R6.5). The design round's reports are cited by line
  in their committed copies (table below), byte-equal to the scratch copies the round wrote, so their line numbers
  are unchanged.

| Short name | Path |
|---|---|
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` |
| REV4 | `research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` (frozen W1 text) |
| W1R | `research/experiments/2026-10-16-stage1-commitments.md` (the committed W1 record) |
| PREREG | `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (Gate B/C revision 5, frozen) |
| FOCUS, SPF, PLAN | `research/FOCUS.md`, `docs/study-plan-full.md`, `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md` |
| B16/, RI/ | `scripts/stage1_s1/reading/`, `scripts/stage1_s1/reading_input/` |
| STR, STRS, LC | `scripts/stage1_s1/overlap_strata.py`, `scripts/stage1_s1/settings/overlap_strata.json`, `scripts/stage1/limits/limits_common.py` (a W1 file) |
| GBR | `scripts/gate_b_reading.py` |
| D1A, V1A, CRIT, R1B, R1D | the design round's reports, committed copies under `.ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/design-round/` (commit `0e0ab1f`, 2026-11-01T09:41 UTC, after `55d5f8b`; each byte-equal to the scratch copy the round wrote, checked by SHA-256): `1a-ri-o2-design.md` (SHA-256 `d4700f08395138e6…`), `1a-ri-o2-review.md` (`f5cb0298a1e1eb33…`), `2-critic.md` (`e8646619ce4fc2fd…`), `1b-b14-similarity.md` (`c03f67467964cf33…`), `1d-reading-runbook-draft.md` (`9ae23f5ee6fa9ae6…`). The coherent-only simulation evidence is `design-round/sg-sim/sg_tail_check_10000.txt` (`bfcd26b2761ca0c0…`) in the same commit |
| READY, CHECK | `…/lead-reports-20261101/next-stages/A-stage1b-readiness.md` (`8d1f5366ed267d33…`) and `A-stage1b-check.md` (`570e98ffb3d2a22c…`), committed in `0e0ab1f`, byte-equal to the scratch copies |
| LR | the lead's rulings after the build round, `lead-rulings-20261101.md` (1 Nov 2026, 14:02 UTC; SHA-256 `3096e37a09ac565a…`), cited by section R1-R6; today in the lead's scratch `builds/`, to be committed under `lead-reports-20261101/build-round/` `[FILL-hash]` |
| ACB, ACV, BBB, BBV, CKB, CKV, D1B, D1V, D2B, D2V, EV2 | the build round's reports, cited by line at the SHA-256 read here; today in the lead's scratch `builds/reports/`, to be committed under `lead-reports-20261101/build-round/` (LR R6.5) with their final SHA-256 `[FILL-hash]` (a fix round appends to a build report and moves no earlier line): `A-coherent-build.md` (`bb0ddc75a69787fd…`), `A-coherent-verify1.md` (`78664ae2ca51257a…`), `B-b14-build.md` (`f98671ab05c02366…`), `B-b14-verify1.md` (`6a596693dd71b40c…`), `C-kit34-build.md` (`539d3b3a27c95d16…`), `C-kit34-verify1.md` (`04e14e8ceb48f485…`), `D1-readers-build.md` (`bee4e20e31be1cfe…`), `D1-readers-verify2.md` (`1e8a6d44c3a8cc7c…`), `D2-ln31-build.md` (`c7506a1e54a17fe9…`), `D2-ln31-verify2.md` (`2577542a494ab662…`), `E-records-verify2.md` (`1f05238d79211758…`) |
| FOCUS, PLAN, KW, LEDGER | `research/FOCUS.md`; `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md`; `…/reading/user_instruction_keep_working_20261031.json`; `research/experiments/2026-10-17-stage1-preregistration-rev3/decision-ledger.md` |
| RIB, HBB, B16H | `research/experiments/2026-10-27-block-b-prep/reading-input/reading-input-build.json`, `…/hb-reader/hb-reader-build.json`, `…/b16-halves/b16-halves.json` |
| OTSC | `.ai/inputs/stage1-post-w1-20261023/reading/timestamp/ots-check-20261101.json` |
| PLANS | `research/review/2026-10-08-sharpened-direction-DRAFT.md` |
| RULES | `runkit/stage1-olmo/stage1_rules.py` |
| SIM | `scripts/stage1_s1/overlap_similarity.py` |
| HLC | `research/review/2026-10-17-stage2-design-notes/second-rater-and-human-label-check.md` |
| NOTES | `/Users/spiderishi/Coding/attribution/.claude/worktrees/kind-hawking-a6ce04/tmp/claude-workspaces/stage1-integrate-20261017/notes/` (git-ignored; cited by path, SHA-256 and line; the lead commits copies of the two cited files with the records, LR R6.5) |

1. **Post-W1 deviation D-5: S-G's coherent-only U by a linearized prompt table, read beside B16 (builder open point RI-O2).**

   **Facts.**
   - The frozen text asks: "Coherent-only U is reported for every arm; every label is re-read on coherent answers
     (S-G)" (REV4:301). S-G is "coherent-only U and both G3 corners" (REV4:270).
   - Coherent-only U is G2's definition (PREREG:148): the arm-level value is the pooled share (coherent Unsafe over
     coherent answers); per-prompt shares "serve only the per-prompt differences and the clustered SE"; a prompt with
     0 coherent answers in either arm of a pair "is left out of that pair's differences"; the count is reported; "No
     limit on that count changes a verdict".
   - Today the builder does not build the coherent variant (RI/build.py:84-87; it sends only the two G3 tables,
     RI/build.py:673-674), so B16 prints S-G with the two G3 corners only and no note (B16/reading.py:313). REV4:301
     would be unmet in silence.
   - The design's option (a) (D1A §4.2) drops prompts and uses equal-weight per-prompt shares in the prompt part. The
     review shows that this prompt part does not belong to G2's pooled estimate: in a 4-prompt hand case the design's
     SE is 0.07 pp where the correct SE is 25 pp (V1A:165-177; re-derived by hand in CRIT:254-258), and in synthetic
     worlds with prompt-concentrated screen failures its 90% coverage is 0.845-0.877, against 0.900-0.903 for the
     linearized table and 0.902 for B16's primary form on plain U (V1A:193-198; evidence
     `design-round/sg-sim/sg_tail_check_10000.txt`, SHA-256 `bfcd26b2761ca0c0…`, committed in `0e0ab1f`; checked by
     CRIT:305).
   - Track A built D-5 in a scratch tree at `55d5f8b`: the builder's `--coherent-out` option and `coherent.py` (the
     counts and their checks) and the reader `sg_coherent.py` beside B16; B16 stays byte-identical (ACB:13-14, :16-31).
     Its verifier found one defect, in the test harness, and none in any reading output (ACV:16-25); fix round 1 is done
     (ACB:334-362). The re-verify of that fix round runs now and its verdict decides (LR R1.1).
   - The built G3 "unscored" corner counts unscored answers Unsafe in every arm (RI/items.py:6-8, :115). Gate B's
     G3(a) is adverse by direction: "for LOCALIZED, Unsafe in unit arms and Safe in R arms; for DIFFUSE, the reverse"
     (PREREG:149; GBR:243-244).
   - No stage-1 outcome has been read: block A and block B are sealed and unread (FOCUS:107, :77). Since the seals, only
     readable non-outcome records were read: completion records, cost ledgers, adapter fingerprints (REV4:158;
     ADD:625) and the judges' run and completion records (FOCUS:77, :109).

   **Ruling D-5.**
   1. **Cell value:** G2's pooled share, V(a,j) = Σ_p u(a,j,p) / Σ_p n(a,j,p), a share (printed as 100 × V, in pp),
      where n = the prompt's coherent answers (0-3) and u = its coherent Unsafe answers (PREREG:148).
   2. **Prompt part: the linearized table** x(a,j,p) = V(a,j) + [u(a,j,p) − V(a,j)·n(a,j,p)] / N̄(a,j), with V as a
      share and N̄(a,j) = Σ_p n / 200, on all 200 prompts (V1A:209-211). B16 scales the table by 100 itself
      (`cell_value`, B16/contrast.py:84-85). With V in pp the point estimate would not change but the prompt part would
      be wrong by orders of magnitude, and the all-n = 3 check of point 9 cannot see that (it gives x = u/3 at any scale
      of V). Its prompt mean is V exactly; it equals u/3 when every n = 3; a prompt with no coherent answer gets x = V
      (no influence on the ratio). No prompt is dropped and nothing is imputed; P stays 200.
   2b. **Reading of G2's per-prompt rule** (PREREG:148): G2's per-prompt shares and its pairwise drop of a prompt with no
      coherent answer served Gate B's clustered SE (GBR:457-470), which HB-C does not use. Under D-5 the prompt part is
      the linearized table, so no prompt is dropped; G2's count of such prompts is printed per seed pair, report only
      (V1A:227-229).
   3. **Model:** B16's own functions, unedited, with the pinned settings (HB-C per cluster, the U floor, LN-35's stop
      rule, D-4's starts; the crossed prompt part; Satterthwaite df), called on {"coherent": x} by a **new reader beside
      B16**, in the pattern of the HarmBench claim reader (RI/hb_claim.py:1-29, :40-45). **B16 stays byte-identical**:
      its module hashes and settings pin `fef3b6f5…` do not change (FOCUS:104: "nothing else pins B16's files").
   4. **Inputs:** the builder writes, per cell and prompt, (n, u, u_fail) (u_fail = incoherent Unsafe answers) into a
      side document bound to `tables.json` by SHA-256, as `--hb-out` is (RI/__main__.py:47); `tables.json` stays
      byte-identical. Checks: per cell Σ_p (3 − n) equals the cell's `coherence` failing count; per prompt
      u + u_fail = 3 × the plain U share, exactly. Built as the option `--coherent-out coherent_counts.json` of track
      A's builder (ACB:18-21): the counts document carries `tables.json`'s SHA-256 as its `input_sha256`, and
      `sources.json` records `coherent: {cells, items, output_sha256}`; without the option `tables.json` is the same
      document (tested). **The pre-run (LR R6.1).** The builder's no-value pre-run R1b takes the same `--coherent-out`
      option as step 2. The step-2 comparison with the pre-run leaves out `sources.json`'s `coherent.output_sha256` and
      the counts document's `input_sha256`, as it leaves out the HarmBench tables' hashes (R1D:589-594): they bind
      `tables.json`, which differs from the pre-run's by the overlap block. The counts' checks do not depend on the
      overlap block, so if R1b passes, step 2 cannot refuse for a D-5 reason (EV2:54-63: the verifier ran both paths on
      a synthetic kit; without this rule the step-2 comparison fails either way).
   5. **Printed per arm:** V per cell, its seed mean, N per cell, and the prompts with no coherent answer per cell.
      **Per contrast:** the estimate, 90% interval, df and U-part words; G2's count per seed pair (prompts with no
      coherent answer in either arm). No count limit changes anything (PREREG:148).
   6. **Words:** Φ is re-run with S-G coherent's U p-values and the primary O, L and F p-values, as B16's `record()`
      does for every U sensitivity (B16/reading.py:287-301). The reader prints the U-part words **and the headline word
      under that Φ run**, both formed by B16's own label code, never by hand (REV4:400). A word that differs from the
      primary's prints in the row's sensitivity part of the reading record, copied there by key from the reader's
      output (REV4:398; the route beside B16 needs this copy, CRIT §3 C13). It never changes a label (REV4:264, :275).
   7. **G3a, both adverse corners**, in the same reader, per contrast, from `tables.json`'s plain U and
      `g3_unscored_unsafe`: "against better" (the repair's cells from the unscored table, every other arm plain) and
      "against worse" (the mirror). In P4 a0 is the comparator, so a0 takes the corner's direction (V1A:329-331).
      B16's built table stays, labelled as the reader prints it: "unscored counted Unsafe in every arm (not Gate B's
      adverse corner)" (V1A:363; the reader's `SYMMETRIC_LABEL`, pinned by its test, ACB:21-26; the reading record copies
      the label by key and never re-types it, EV2:131-134). The corner it is not is Gate B's G3(a) (PREREG:149).
   8. **The reader never stops the reading; the builder half is settled at the pre-run (LR R6.1).** B16 runs first and
      is unchanged. The reader runs after B16 and the claim reader (step 4b). A statistical failure inside it (a cell
      with N = 0, fewer than 2 common seeds, no variance information, a `RemlError`) prints "not computable" with the
      reason and gives that node p = 1 in S-G coherent's own Φ run. A refusal of the whole reader (a non-zero exit, a
      binding or hash mismatch) is logged, the script goes on (the runbook's stop rules S1 and S5 do not apply to this
      step: §39 point 8(d)), the reading's other steps stand, and the reading record prints in S-G coherent's place:
      "S-G, coherent-only U: not computed at the reading. D-5's reader refused: [its message, copied from the step's
      log]. B16's two G3 corners print as built, labelled as in point 7. This departs from the stage-1
      pre-registration, revision 4, §3.7 item 4." A later fix follows the runbook's S4: a post-W1 deviation, and its
      outputs are labelled post hoc (R1D:727-730). **The builder half** (item 4's counts and their two checks) refuses,
      if at all, at the no-value pre-run R1b, which shows no outcome (S2, R1D:722-724), because item 4's comparison
      rule leaves step 2 no D-5 reason to refuse. If R1b refuses only on a coherent-only check (a message of track A's
      `coherent.check`: the counts against the coherence block or against the U table, ACB:16-21), the reading's step 2
      runs without `--coherent-out` (`tables.json` is byte-identical without the flag) and D-5 goes straight to its
      last fallback (c), because (c+) also needs the counts. That choice is made at the pre-run, before any value is
      read; (c)'s paragraph then names this cause instead of "not verified". A pre-run refusal for any other reason is
      the builder's own and follows S2.
   9. **"Verified" means all of these** (V1A:361; CRIT:345; LR R1.2; the items marked "added" were this record's and
      are adopted by LR R1.2): the builder suite and the new reader's suite pass (B16's suite too, unchanged); the
      official mutation spec of the builder and the new reader (47 entries, ACB:355, :440) is the lead's background run,
      with 0 invalid and every mutant killed except listed expected survivors (LR R1.2(c)); an independent reference
      agrees on hand cases and (added) on at least 20 synthetic readings (plan A, plan B, block A only), with this
      **tolerance (LR R1.2(b)):** estimates agree to 1e-9 pp (V1A:361), and where the reference fits REML on its own,
      SE and df are compared at 1e-6 relative, because B16's REML stops at a step below 1e-6 (ADD:425); (added) a hand
      case with unequal n against an exact-fraction reference, because the all-n = 3 case cannot detect a wrong scale of
      V (point 2); the all-n = 3 case equals the primary U_k exactly; and the coverage gate below.
      **The coverage gate (LR R1.2(a)).** The simulation uses independent, prompt-concentrated and outcome-linked
      failures (V1A:349-350). The gate is **plan A**, the reading that will run. Every contrast in every simulated world
      must meet both the 90% coverage band 0.88-0.92 and the tail ratio: S-G coherent's 0.75% tail at most 1.5 × the
      primary form's tail in the same world. Replicates: at least 2,000 per world; a world whose 2,000-replicate
      coverage is within 2 Monte Carlo SE (0.0134) of a band edge, or whose tail ratio is above 1.3, must also pass at
      10,000 replicates. **Plan B** is checked and reported, not a trigger. **Block A only** is reported as a limit,
      not a trigger: that reading can no longer run (RI/build.py:606-607 refuses it with block B sealed), and B16's own
      primary form is also outside the band there (ACB:255, :260-262). A plan-A contrast-world outside the band or the
      tail rule triggers the fallback; it is not printed as a limit (V1A:295-296). Track A's measured state (synthetic
      worlds, ACB:251-255): plan A 18 of 18 contrast-worlds at 2,000 replicates (coverage 0.891-0.909, tail ratio 0.93,
      per contrast 0.61-1.35), plan B 6 of 6 at 20,000, block A only 8 of 18. By the replicate rule at least one plan-A
      world must also pass at 10,000 (its lowest coverage 0.891 is within 0.0134 of 0.88; its highest tail ratio 1.35 is
      above 1.3); the 10,000-replicate run is the lead's (ACB:267-268) and the re-verify reads it (LR R1.1).
   10. **Records:** SPF:344 adds D-5; FOCUS records the reader's and the builder's new hashes `[FILL-hash]`; the
       reader, its settings and this record fall inside the second stamp (PLAN:39-40).

   **Reasons.** Option (a)'s prompt part is miscalibrated exactly when S-G matters, when a repair's screen failures sit
   on particular prompts (V1A §2.1-2.2). The linearized table is the standard first-order form for a ratio estimator,
   needs no drop rule and keeps REV4's P = 200. Beside B16, no B16 file changes, so B16's 117-entry spec (about 2.1 h,
   R1D:168-171) need not run again and B16's tree stays the one the 31 Oct stamp holds. Cost: about one worker-day at
   $0 (V1A:282-287, an estimate).

   **Pre-set fallback (c+).** *Trigger:* D-5 is not verified after one fix round (the D-1 and D-2 pattern, ADD:457,
   :470). Fix round 1 is done; its re-verify runs now and its verdict decides; there is no second fix round for the
   reader (LR R1.1). Then the counts document of item 4 and a small reader print each arm's pooled coherent-only U per
   cell, its seed mean and N per cell, with the text "no label was re-read on coherent answers (post-W1 deviation D-5,
   fallback (c+))". S-G's G3 corners are B16's built tables with item 7's label; the adverse corners are "not
   computed". (c+) adds no estimation rule: the pooled share is G2's own value (V1A §4). If the re-verify finds a
   defect, (c+) is built and verified as this record's pre-set fallback, with this fixed text (LR R1.3).

   **Last fallback (c).** *Triggers:* (i) (c+) is not verified (its suite, its spec and an independent recount of the
   pooled shares on synthetic units) when the second stamp's manifest is written (LR R1.3); or (ii) the builder's
   no-value pre-run R1b refuses only on the coherent-only counts (item 8): then (c) is chosen at the pre-run, before
   any value is read, and (c+) cannot run either, because it needs the same counts. Then nothing coherent-only is
   computed, and the reading record prints the design's option (c) paragraph (D1A:498-509) with these edits, because
   that paragraph describes the design's drop rule, which this record does not adopt (V1A §2; CRIT C1), and says that
   every label is re-read, which B16 does only for the U-part words (B16/reading.py:284-301; V1A:102-105):
   - "(D-5: such a prompt leaves only the prompt part of the contrasts whose arms lack a coherent answer on it)" becomes
     "(D-5: G2's pooled share per cell with a linearized prompt table on all 200 prompts, read beside B16)";
   - "was not verified before the reading started, so by its pre-set fallback it was not used" becomes "and its pre-set
     fallback (c+), each arm's pooled coherent-only U, were not verified by their pre-set triggers, so neither was used";
     under trigger (ii) it becomes instead "could not run: the builder's no-value pre-run refused the coherent-only
     counts ([the refusal's message, copied from the pre-run's log]), so neither D-5 nor its pre-set fallback (c+),
     which needs the same counts, was used";
   - "every label is re-read through Φ" becomes "the U-part words are re-read through Φ";
   - the unscored corner carries point 7's label (D1A:511), and one sentence follows the first: "Gate B's adverse G3(a)
     corners (against better and against worse) were not computed."
   The record adds the date and time of this record.

   **S1 blinding line (REV4:919; W1R:358).** Written `[FILL-time]`, after the W1 commit (FOCUS:144, 2026-10-22T21:22
   UTC) and after every Gate B value that the S1 blinding record lists: wave 1 (FOCUS:140), the verdict (FOCUS:138),
   P5's lexicon band (FOCUS:136), the final measurements and, possibly read, their §6 values (FOCUS:135), and σ̂ 1.78 pp
   (FOCUS:126). No stage-1 outcome was read. **The paper labels this rule "fixed after Gate B wave 1".**

2. **Post-W1 deviation D-6: B14's report accepts recipe-S units (a settings-only re-pin).**

   **Facts.**
   - B14's report settings fix `report.identity.recipe_sha256` to REC's config hash `9e9bde6f…` and list recipe S's
     `ceffe0ef…` under `refused_recipes` (STRS:39-42, :49). The W1 unit check enforces both (LC:167-171).
   - Every stage-1 arm, a0 arm and regeneration trains with recipe S (`runkit/stage1-olmo/stage1_rules.py:340`,
     `TRAINING_IDENTITY_RECIPES = ("S",)`; ADD:435). Recipe S's config hash is `ceffe0ef…`
     (`scripts/stage1_s1/settings/oext_unit.json:61`). R1B parsed `plan.json` and found recipe "S" on all 55 arm jobs
     and all 5 a0_arm jobs (R1B:148-150; not reopened here); track B's verifier confirmed it, read-only: the counts
     `('arm','S','X') 55` and `('a0_arm','S','X') 5`, and a recipes table of exactly four configs, REC, S, G and B+Qi
     (BBV:18-24).
   - Track B built D-6 and the B14 inputs writer in a scratch tree at `55d5f8b`; both are verified (BBB:11-17; LR R2,
     status line).
   - B14's own test asserts the refusal (`scripts/stage1_s1/tests/test_b14_report.py:385-400`, case `recipe_s`). So
     `overlap_strata.py report` refuses at the first kit unit of `d1_plan_a` (a0 at 1104; STRS:33), before that unit's
     guard file is read (R1D:34): no outcome is shown, but §9.4 cannot be read.
   - The strata record stores the strata settings' SHA-256 and the report refuses a mismatch (R1B:101-103), so this
     change must land before `overlap_strata.py strata` runs.

   **Ruling D-6.**
   1. In STRS: `report.identity` keeps `manifest_sha256` and drops `recipe_sha256`; `refused_recipes` becomes recipe G
      `c004349c…` (`scripts/stage1_s1/settings/oext_unit.json:60`) and B+Qi `37942cf5…`
      (`scripts/stage1_s1/settings/oext_unit_y.json:59`), because reference units also carry arm "a0" (R1B:163-164).
      Every unit stays pinned by its COMPLETE.json and job.json SHA-256, arm, seed, checkpoint and allowed engine code
      (LC:146-171; STRS:44-47).
   1b. **The limit, recorded (LR R2.1).** D-6 stays settings-only, a deny-list: a unit of any other recipe hash would
      pass B14's own checks (BBB:17; BBV:145-147, where the verifier also shows that no such unit exists in the real
      kit's four-config recipes table). Today the unit pins (COMPLETE.json and job.json SHA-256), the inputs writer's
      `plan.json` recipe check (recipe S required for every kit unit), the checker and the builder's cross-check cover
      the reading, and `plan.json` records recipe S on engine X for all 55 arm and 5 a0_arm jobs (BBV:18, B's verifier).
      No accepted-recipes list is added.
   2. `SETTINGS_SHA256` (STR:60) is re-taken (the settings `92c3a4a0…`, the script `4249b070…`; BBB:38-39). The
      fixtures give kit units recipe S and Gate A's a0 units REC; the `recipe_s` refusal case becomes an accept case;
      new refusal cases cover G and B+Qi. The B14 suite and its mutation spec run on the change. **The spec has 150
      entries** (87 before D-6; 63 added and 6 re-pinned, BBB:16, :46; the first draft of this record said 87, the
      pre-D-6 count). Before the second stamp the lead runs the **69-entry near set** (the new and re-pinned entries,
      `mutants_b14_near.json`, SHA-256 `77c3def1…`, BBB:234); the full 150-entry spec runs as a background job when the
      machine allows (LR R2.2). This record states which set ran: `[FILL: the 69-entry near set / the full 150-entry
      spec]`, result `[FILL]`.
   3. No W1 file changes (LC is untouched) and no rule text of §9.4 changes (REV4:757). **Order (LR R2.3):** D-6 is
      committed before `overlap_strata.py strata` runs, because the strata record carries the settings' SHA-256
      (BBB:276; R1B:101-103); the inputs writer runs, then the checker at once; the change, the writer's file and this
      record fall inside the second stamp.

   **Reason.** The refusal was right for REQ-19's Gate A units, which B14's pattern copied
   (`scripts/stage1/settings/limits_check.json:7`, per R1B:155-156), and wrong for kit units. A settings-only change is
   the smallest fix: one file, one pin, the same checks on every other field.

   **Pre-set fallback.** *Trigger:* D-6 is not verified (suite and spec as point 2) when the other builds are done (D-5,
   the B14 inputs writer, the reading-time readers), or (added, beyond the brief's trigger; CRIT:347; R1D:783)
   `plan.json` shows a recipe other than S for any kit unit that B14 reads. Then the input build runs with
   `--no-overlap` (RI/__main__.py:45-46) and B16 prints "not computed" for §9.4 (B16/reading.py:534-535). The reading
   record words §9.4 so: "§9.4's overlap control: not computed. Cause: [B14's report refused the stage-1 kit units / no
   strata]. This departs from REV4 §9.4 (LN-26) and is post-W1 deviation D-6's fallback." It also states that B16's
   printed reason (`scripts/stage1_s1/reading/settings/reading.json:200`), the builder's `--no-overlap` help
   (RI/__main__.py:45-46) and its refusal text (RI/__main__.py:58-59) name addendum §24 point 4's fallback, which was
   withdrawn on 29 Oct (FOCUS:104), and that no B14 per-contrast paired form is printed in its place. Those pinned texts
   stay unchanged (LR R6.5: B16's settings pin must not move); the record corrects the reference.

   **S1 blinding line (REV4:919; W1R:358).** Written `[FILL-time]`, after the W1 commit (FOCUS:144) and after every
   Gate B value the S1 blinding record lists (FOCUS:140, :138, :136, :135 with its §6 values possibly read, :126). No
   stage-1 outcome was read. **The paper labels this rule "fixed after Gate B wave 1".**

3. **The input builder's open points** (RIB:410-466; written 29 Oct 10:34 UTC, RIB:5). RI-O2 is D-5. RI-O3's wording
   is point 7. RI-O4 is closed by §37 (the claim reader, ADD:639-646). Every other point keeps its stated reading:

   | Id | The stated reading (quoted, shortened) | Ruling |
   |---|---|---|
   | RI-O1 (RIB:412-414) | "B16-H-O8 is met builder-side (required --expect-*-sha256, canonical-form check); B16 itself is unchanged." | Adopted. B16 gains no refusal. The binding is the builder's required `--expect-strata-sha256` and `--expect-report-sha256`, the runbook's check that B16's `provenance.input_sha256` equals `tables.json`'s SHA-256 (R1D:607-622), and the lead's comparison with the SHA-256 values in FOCUS (B16H:230-231) |
   | RI-O5 (RIB:428-430) | "plan_a_block_a_only refuses once block B is sealed (… that reading is for a stage 1 without block B)" | Adopted (REV4:158; the code: RI/build.py:606-607) |
   | RI-O6 (RIB:432-434) | "B+Qi's own a0 (role bqi_own_a0, after a failed certificate) refuses" | Adopted. The X → Y certificate passed (FOCUS:107), so the role does not arise; the refusal stays as a guard |
   | RI-O7 (RIB:436-438) | "Safe LoRA's two reference points enter B16 as two point references; … family 1b … then needs both, … 'm beats it only if m beats each point'. Its certify (K = 0) point and B10's certify units are not references." | Adopted |
   | RI-O8 (RIB:440-442) | "References are read from the complete ref jobs found in block B; there is no required list (a reference that did not run is simply absent and the summary prints the list)." | Adopted. The printed list is a count line, logged and reviewed (point 8a), never a stop and not an identity line (LR R6.5); the record names any planned reference that is absent, as a limit beside family 1b (point 8a) |
   | RI-O9 (RIB:444-446) | "The plan-A/B code is read from plan.json's record; the builder does not re-derive it from Gate B's verdict file" | Adopted. The kit re-derives it at every init and release; plan A is recorded (FOCUS:126) |
   | RI-O10 (RIB:448-450) | "O's per-prompt flags re-implement oext_eval.evaluate_oext's primary table …; every count of oext_summary.json … must agree." | Adopted. The count equality is the check on real units; a mismatch refuses before any value is printed |
   | RI-O11 (RIB:452-454) | "Gate A units: job.json is bound by its pin, not by COMPLETE.json's job_sha256 …; harm.sampled invalid and capped are compared only where present" | Adopted |
   | RI-O12 (RIB:456-458) | "A block seal must carry seal.py's judge_record (round 30 and later)." | Adopted. Both seals were written after kit round 30 (FOCUS:107-108, :77); a refusal here would come in the no-value pre-run, before any value |
   | RI-O13 (RIB:460-462) | "The rules module defaults to the repository's runkit/stage1-olmo/stage1_rules.py … if the live kit's copy differs, pass --rules … or compare." | Adopted. The runbook checks that the repository and live copies are equal (R1D:220, :228-229) and the second stamp holds both |
   | RI-O14 (RIB:464-466) | "The not-run route for R's O cell at a reused seed reads block A's seal not_run list …; the decision files themselves are not re-hashed here (the seal holds their SHA-256)." | Adopted |

4. **The HarmBench claim reader's other readings** (RI/hb_claim.py:70-96; HBB:55-64, :190). §37 ruled R1, R4 and R8
   (ADD:641-643). The other six are adopted as written. Each changes which sentence prints, so each is stated here:
   - **R2** (RI/hb_claim.py:75-77): "The case is the U part's (rows[k].u_part.words), not the headline word … a row
     headed 'worse (O)' or 'worse (L)' keeps its U part's case." Reason: the harm sentence is about the U claim; the
     alternative needs a rule the text does not give.
   - **R3** (:78-79): "A U part with both 'worse (U)' and an equivalence grade (LN-36: both print) is an equivalent
     contrast (never 'harm')." Reason: LN-36 lets both print (REV4:394), and LN-15c gives an equivalent contrast only
     "restored refusal"; this is the conservative reading.
   - **R5** (:82-85): "'Same sign' and 'at least half its size' compare the point estimates; a value within B16's
     tie tolerance (… 1e-9 pp) of 0 has no sign and never matches; |HB_k| >= |U_k|/2 and 'E_HB < 20 pp' read through
     that tolerance". Reason: shares are k/3, so exact boundary values can land 1e-15 off; B16 reads δ the same way
     (B16/README.md:153-155).
   - **R6** (:86-88): "The HarmBench contrast's interval is U's model refitted on the HarmBench table (HB-C, U's
     floor, the crossed item part over 200 prompts)". Reason: REV4 names no other model, and HB-C is refitted per
     endpoint (REV4:285).
   - **R7** (:89-90): "'unparsed' labels count as not 'yes'". Reason: Gate B's judge files count harm as "yes" only,
     and Gate A's E_HB was the "yes" share of all 600 answers.
   - **R9** (:94-96): "The rule is read on the reading's labelled contrasts (P1-P6; plan B P1, P3, P6). Restoration
     G_m, the references and the overlap halves carry no LN-15c label and are not read here."

5. **B16's stated readings and open points.**
   - **Ties at δ** (B16/README.md:153-155): "Every comparison of the estimate with delta reads through
     `margin.tie_tolerance_pp` (1e-9 pp, pinned); interval ends (irrational) do not." Adopted.
   - **"Readings the record should state"** (B16/README.md:156-159): (a) LN-12's O comparator part uses the R seeds
     present, and is "not tested" below 3 seeds; (b) the S-a equal-variance flag reads the rejection sets of the S-a
     and S-aW Φ runs (REV4:266); (c) under plan B, S-a and S-b2x pool a0 as well (S-a is "pooled over the arms");
     (d) the two-arm cluster's sum is floored at one floor, not twice it. All four adopted; the reading record
     states them.
   - **The overlap readings R2-R6** (B16/README.md:79-84): (R2) HB-C "from cells_u_pp" is the full cluster refit on
     the per-prompt U table at B14's halves, with `cells_u_pp` as the binding check; (R3) a sign within 1e-9 pp of
     0 is 0 and never matches; (R4) "excludes 0" is strict; (R5) a half with fewer than 2 prompts, or with no fit or
     no variance, is "not computable" and "not shown"; (R6) the higher half is printed; the rule reads only the lower
     half and all prompts. All adopted. (R1, which contrasts, is §33 point 1, ADD:604.)
   - **Already ruled, recorded here once:** the floor mode "active_set" (B16/README.md:139-145; ADD:425); a step
     that floors an arm never ends the fit (B16/README.md:146-150; ADD:426); the 25-step stop stays
     (B16/README.md:151-152; ADD:607).
   - **B16-D4-O2** (B16H:222-223): HB runs all 255 floor patterns (about 1.1 s per reading). Ruling: unchanged, as
     D-4 says "every B16 REML fit" (ADD:605).
   - **B16-D4-O3** (B16H:226-227): D-4's fallback print is not built. Ruling: recorded as moot. D-4 was verified and
     merged before block B's reading (FOCUS:104, :99), so its trigger, "not verified before block B's reading"
     (ADD:605), never fired.
   - **B16-H-O9** (B16H:234-235): B16 checks B14's split through the strata's recorded numbers, not by recomputing
     it from the similarities. Ruling: a stated limit; the anchor is the sealed SHA-256 of `strata.json` in FOCUS
     (ADD:375).

6. **A coherence-failing arm is not "feasible" for the best feasible repair** (B16/reading.py:449; the per-actor
   best data arm uses the same candidates, B16/reading.py:485; in family 1b a failing arm carries p = 1 and never
   dominates, B16/reading.py:427-433).
   - *Frozen texts.* "A failing arm is infeasible for the selector and cannot dominate a reference" (REV4:302). The
     best-feasible rule names τ_O, τ_L and §4.9's separation, and no coherence condition (REV4:410). The coherence
     flag "never changes the word" (REV4:409). In REV4, "the selector" is §7's model-based selector: "The selector
     stays secondary and model-based" (REV4:79); "the selector screen (REQ-16)" (REV4:562); "The selector is not run
     on new menus here" (REV4:611-614).
   - *Ruling.* B16's behaviour is adopted as a stated reading that fills a gap. REV4:302 makes a failing arm
     infeasible for §7's model-based selector, not for the headline's best feasible repair, and its second half
     ("cannot dominate a reference") is B16's family-1b rule (B16/reading.py:427-433). B16 applies the same
     exclusion to the best feasible repair and to the per-actor menus (B16/reading.py:449, :485); ADD:427 ruled the
     per-actor best data arm "better and feasible" without naming coherence. The headline word does not change
     (REV4:409). It is a post-W1 reading, listed in the S1 blinding record (rows 1 and 12).
   - *Reason.* A repair whose answers fail the screen should not be named the feasible choice; the reading changes
     no P1-P6 label (REV4:409). The code dates from B16's first commit, `2135c2d` (2026-10-23T00:40:40Z), before
     wave 1's reading was recorded (FOCUS:140, 01:00 UTC).
   - *Alternative not adopted:* REV4:410 read alone, which would need a B16 change.

7. **The wording of S-tok and of §9.4.**
   - **S-tok.** The stated readings: RI-O3, "token_axis is not built: REV3 9.3 item 2 needs R_1200 and R_2400 at
     d = 2-4 (seeds 1102-1104), and no kit job kind … runs them, so S-tok has no input. A kit round (and funding) or
     S-tok's absence is the lead's decision" (RIB:420-422); and the plan's "RI-O3: S-tok has no input (stage 1c's
     R_1200 and R_2400 have not run), so the reading says 'not run'" (PLAN:32). B16 prints `null`
     (B16/reading.py:315), and the builder prints "not built: token_axis" (RI/build.py:88-89). S-tok's input is the
     random dose curve R_1200 and R_2400 (REV4:271, :743), a stage-1c arm of the funded tier (REV4:719-721).
     Ruling: the plan's reading is adopted; the reading record prints "S-tok: not run (its input, the random dose
     curve R_1200 and R_2400 of REV4 §9.1, belongs to stage 1c and has not run; B16 prints null)". The token-axis
     report of REV4 §9.3 item 2 reads the same. S-tok is read when stage 1c's dose cells exist.
   - **§9.4 without the overlap block.** The stated reading: "§9.4's wording if `--no-overlap` fires (do not cite ADD
     §24 point 4; §3 C3)" (CRIT:142-143). Adopted: the only wording is D-6's fallback text (point 2). The
     record does not cite §24 point 4: its fallback was withdrawn on 29 Oct (FOCUS:104), although B16/README.md:68,
     B16's pinned text (`B16/settings/reading.json:200`), the builder's help (RI/__main__.py:45-46) and the builder's
     refusal text (RI/__main__.py:58-59) still name it. Those texts stay unchanged (LR R6.5: B16's settings pin must
     not move); the record corrects the reference. *Not adopted:* correcting the builder's two texts while track A
     edits that file for D-5 (EV2:153-155), because the lead ruled the pinned texts unchanged; it would move the
     builder's hash a second time for no reading change.

8. **The reading runbook's readings** (R1D; CRIT:145-146, :220-226). R1D asks §39 to confirm "this runbook's own
   readings: D1's recipe rule, the inputs writer, the pre-runs, the byte-for-byte re-runs, the stop rules, the
   mechanical record, and 'report and go on' after the reading" (R1D:804-805). D1's recipe rule is D-6 (point 2);
   "report and go on" is point 10.
   - **(a) Stop on identity lines only; log the count lines.** The stated reading: "Default: stop only on identity
     lines (plan code, seals, rules and settings pins, written hashes) and log the count lines for review"
     (CRIT:224-225). Adopted. The no-value pre-run checker and the step-2 checker stop on the plan code and
     `plan.json`'s SHA-256, the rules and B16 settings pins, both seal SHA-256 values, the overlap line and the
     written files' SHA-256 (R1D:537-541, :571-575). The count lines (cells, references, judges, HarmBench records,
     the "not built" lines; R1D:469-478) are logged and read after the run, never stop conditions. Reason: they are
     inferences from code (R1D:670-677), and a wrong one would cost a new second stamp and anchor wait
     (CRIT:220-226). The builder refuses a missing, duplicate or extra cell on its own (RI/build.py:9-13, :271-272).
     References have no required list (RI-O8, RIB:440-442): a reference that did not run is absent from the printed
     list, and family 1b ("beats every reference") then compares m with the references present. So the reading
     record prints the references list beside family 1b and names, as a limit, any reference job of block B's plan
     that is absent. **Ruled (LR R6.5):** the references line is not an identity line; a missing reference prints as
     a limit beside family 1b. *Not adopted:* making it an identity line after checking block B's reference jobs in
     its completion records, which stay readable (REV4:158; the kit's seal leaves ledgers, completion records,
     fingerprints and receipts readable, CHECK:267-269), before the second stamp (RIB:441-442). Fallback for the
     stop rules as a whole: R1D's strict list; trigger: the lead chooses strict checks before the second stamp is
     made (CRIT:225-226, :355).
   - **(b) Byte-for-byte re-runs.** The stated reading: "A pre-run or re-run that is not byte-identical: stop; the
     first file of step 1 or 3 stays the reading; report the difference as a limit" (R1D:733-734, S6). Adopted: B14's
     report must equal its no-value pre-run byte for byte (R1D:552), and B16 is run twice with byte-identical outputs
     (R1D:623-624).
   - **(c) The mechanical record.** The stated reading: "The reading record, by a mechanical extractor (copies by
     key; computes nothing; rev4:400)" (R1D:682). Adopted, with one addition: the extractor copies from
     `reading.json` and `hb_claim.json` (R1D:690-701) and also from the D-5 reader's output, so that S-G coherent's
     words reach the row's sensitivity part by key (REV4:398; D-5 point 6). When the D-5 output is absent (the
     reader refused at step 4b, or D-5 went to (c) at the pre-run), the extractor still runs and copies D-5 point
     8's wording, or (c)'s paragraph, with the reason from the step's log (EV2:156-157). It also copies the
     reading-time readers' outputs of step 4c by key (point 11). Nothing is typed by hand (REV4:400). The words
     table that FOCUS quotes is printed by that extractor (R1D:710-711).
   - **(d) Pre-runs and stop rules.** The stated reading: R1a, "B14's report as a no-value pre-run (stdout, which
     would hold the S-p verdicts, is discarded unread)", and R1b, "the builder as a no-value pre-run (it prints counts,
     hashes and labels only; its files stay unopened in scratch)" (R1D:519, :524), both before any outcome is printed
     (R1D:519-546); stop rules S1-S9 as drafted (R1D:718-738), with three changes: (i) S1 ("Any exit other than 0, or
     any `"pass": false`: the script stops", R1D:720) and S5 do not apply to D-5's reader (step 4b) or to the
     reading-time readers (step 4c, point 11): a non-zero exit or refusal there is logged, the script goes on, and
     the record prints D-5 point 8's wording (or the reader's "not computed") with the reason; (ii) the pre-run and
     step-2 checkers fail only on the identity lines of (a); the count lines are logged; (iii) R1b takes the same
     `--coherent-out` option as step 2 (R1D:524-529 drafted it without the option), and the step-2 comparison
     (R1D:581-600) leaves out the counts document's hashes (`sources.json`'s `coherent.output_sha256` and the
     document's `input_sha256`), because they bind `tables.json`, which differs by the overlap block (LR R6.1;
     EV2:54-63). So D-5's builder half is settled at R1b, before any value: if R1b refuses only on a coherent-only
     check, step 2 runs without `--coherent-out` and D-5 goes to its last fallback (c) (D-5 point 8); any other
     refusal at R1b is S2. From step 1 on, no input, setting, pinned file or output is edited, and no step is re-run
     with other arguments (S3, R1D:725-726).
   - **(e) B14's inputs file.** The stated reading: "Default: step 0.4's writer, reviewed, tested on a synthetic kit,
     recomputed by a second process. Fallback: a hand-written file that an independent second writer reproduces byte
     for byte. Trigger: the writer not verified before the second stamp" (R1D:784-786). Adopted: the hash-only writer
     (R1D:318-380), run once and committed before the second stamp.
   - **(f) A failure after step 1.** The stated reading: "D7 (failure after step 1). Default: S3–S6. Fallback: stop
     the reading and ask the user. Trigger: a fix that would change a rule, a setting or how any value is computed"
     (R1D:799-800). Adopted; KW:11 keeps "when the next step needs the user" as a stop.
   - **(g) A breach of the path rule by the runbook's author, recorded.** To look for LN-31's draw script, R1D's
     author ran one repository-wide `grep -rln` that pattern-searched, among other files, the 7 W1 "sealed record"
     JSON files under `.ai/inputs/stage1-commitments-20261016/` and the post-W1 `c3/` and `pool-pins/` folders; it
     printed only the names of matching files, and none of those files matched, so no byte of their content was
     printed (R1D:823-829). Risk: none known (no content was shown). The rule stays: a search excludes every sealed
     record by path, and the W1 manifest's sealed records are named by path and SHA-256 only. The build round's own
     hard-rule notes (a `git ls-files` print, three mutation shards moved to the background by the harness, a
     `grep -r` over the lead's notes folder) are recorded in point 15 (LR R3.5, R6.4, R6.6).
   - **(h) The cost-ledger pre-check (LR R4.5).** Before the reading, the runbook checks by exact path that every
     expected cost ledger exists (existence only; no ledger is read). A missing ledger makes the cost table of point
     11 "not computed" (report only); it never stops the reading.

9. **The outside time stamps.**
   - *Facts.* The first stamp is anchored in Bitcoin block 974039 (header time 2026-10-31T23:28:48 UTC) and again in
     974047 (2026-11-01T00:42:41 UTC), each checked at two explorers (FOCUS:74; OTSC:8-28, :30-35). Block 974047 is
     8 blocks later, so 974039 had at least 9 confirmations by 00:42:41 UTC (inference from the heights).
   - *Ruling.* Both stamps are verified as the first was: two independent sources agree on the height, the block hash
     and the merkle root, and the root equals the proof's commitment. **Margin:** at least 6 confirmations
     (tip − height + 1 ≥ 6), and the reading's step 1 starts at least 2 h after the anchoring block's header time,
     because header times are accurate to about 2 h (FOCUS:74; R1D:312-314). The first stamp meets both (2 h after
     its header time was 01:28:48 UTC on 1 Nov). The `ots` client's environment is kept until both stamps are
     upgraded and verified (CRIT:215-216). **A third stamp** of the reading's ledger, outputs and record follows the
     records step, at $0; it bounds from above when the outputs existed (CRIT:217-218). No anchor within 48 h:
     re-stamp once, then PLAN:34's wording.

10. **"Report and go on" replaces "stop and ask" for this run.**
    - *Facts.* The frozen text: "stop and ask after every stage (FR-25; FR-21)" (REV4:887). The user's words on
      31 Oct, about 23:14 UTC: "keep working until all resources are exhausted" (KW:3-4). The lead's reading: "report
      after each stage and go on" (KW:7), replacing the plan's "stops and asks the user after every stage" (KW:13;
      PLAN:48-49). FR-21 is the user's own "Stop asking me for approval and go ahead" (LEDGER:70). R1D:44 gives
      "reports after every stage and goes on" as the user's words; they are the lead's (KW:7, :13).
    - *Ruling.* For this run, after the reading and after each later stage, the lead reports to the user and goes on
      in the plan's order. What stays: the money rules (KW:8: pods at or below $10/h, in-pod caps, the alert below $10,
      launches only as background jobs, no deletion without the user's yes, the $6 reserve); a frozen stop rule that
      blocks a step is recorded as a blocker (REV4:887); no stage starts on a result (KW:10; REV4:878). The lead stops
      at the reserve, or when the next step needs the user (KW:11), including a new kind of spend (KW:9) and point 8f.
    - *Reason.* The change is the user's to make: REV4:887 cites FR-25 and FR-21, and both are the user's, as is
      FR-23 (LEDGER:70, :72, :74). It is recorded as the user's decision, as §36 recorded the start-from-the-balance
      rule. It changes no inference rule.

11. **The reading-time readers** (track D1; ruled in LR R4 and recorded here; CRIT:106-110, :150-173; decision 5 at
    CRIT:349). The producers of five pre-registered reading outputs were built in `scripts/stage1_s1/reading_extra/`
    (D1B:17-25): `fk_power` (F_k's planning power at the measured q, REV4:574), `stage3_pick` (the stage-3 pick,
    REV4:428), `cap_reports` (LN-14's bar and LN-19's flag-change shares, REV4:554-555), `sa_shift` (the S-a shift
    line, REV4:276) and `cost_table` (the measured cost per arm under both conventions, REV4:103, :813). Their rule
    texts are W1 texts; each reader quotes its rule and states its readings in its output.
    - *Status.* `fk_power`, `stage3_pick`, `sa_shift` and `cap_reports` are verified (D1V:16-21; LR R4.1).
      `cost_table` has one more fix round, cost_table only (LR R4.2): a C-full value per point for every
      evaluation-only reference (adapter scaling 0.9, 0.75, 0.5 and SP) by REV4:813 read literally ("the same minus
      training, plus its transform": the matched a0 run's measured C-full slot on the same seed, minus the frozen
      C-full training price, plus the measured transform, over c0), with a per-reference mean over seeds and "null:
      not stated" kept beside it as the alternative reading (K5); the LN-19 PHTest line's "no full answer exists"
      corrected (theta0's LN-14 pass holds both forms); K3's split denominator named "DataShield-style" and the
      anchor job named; then an independent verify. *Fallback:* a reader not verified before the second stamp runs
      after the reading, labelled "code written after the reading"; the other readers stand.
    - *When and how they run (LR R6.3, R4.4).* At the reading's step 4c, inside the reading script, after the input
      build (step 2), B16 (step 3) and the claim reader (step 4). Each output is bound to `reading.json` by SHA-256
      (and to `tables.json` where it reads it), report only: no label, word or number of B16's reading changes, and a
      refusal is logged and never stops the reading (point 8(d)). **The never-open exception (LR R4.4):**
      `cap_reports` opens the COMPLETE.json files and the O-ext summaries that the builder's record names (D1B:60-71,
      :129-133), and `cost_table` opens `plan.json`, the seals and the cost-ledger files under `retrieved/`
      (D1B:75-80, :307-308). Both run only inside the reading script at step 4c, after the input build: that is the
      readers' route, and the never-open list (FOCUS:74) gains this explicit exception. Their outputs are not opened
      before the reading (the `-oext` and `-calibrate` seconds carry a weak outcome signal). The pre-check of point
      8(h) runs before the reading.
    - *Adopted readings (LR R4.3), listed in the S1 blinding record (row 15):* K6 (C-lean of a B10 state = the
      measured c0 − 220 s + the measured transform); K7 (the median stage-1 R slot printed beside the fixed 1 FRE);
      `b10_certify` and the other study costs at measured seconds / c0 (REV4:823); K2 extended (the G and B+Qi
      references at 1 c0; B+Qi's extra training left out, a stated limit of a few per cent, 6-9% at Branch 128's
      smaller c0).
    - *Limits recorded, not fixed (LR R4.6):* the Safe LoRA transform is priced by step wall time; pod overhead and
      the judge pods are outside the table.

12. **B14's similarity pass: a scheduling gap, and the route.**

   **Facts.**
   - The pass was planned "on the pod": "untuned-model embeddings, on the pod" (PLANS:172); "θ0 embeddings, on the pod;
     B14 builds the strata at S1" (W1R:129). The rule text names no device and no block (REV4:757). The only timing rule
     is ADD:375: the SHA-256 of `strata.json` goes into FOCUS before any add-arm outcome is read.
   - No block scheduled it. None of the kit's 20 job kinds runs it (RULES:505-509), and no block lists such a kind
     (RULES:619-625). The gap was first recorded on 31 Oct (FOCUS:76; PLAN:31).
   - It reads only θ0, the 200 dev harm prompts and the three add sets, each by SHA-256, and no unit, `eval/` folder,
     guard file, seal or `plan.json` (R1B:76-93). So the strata are a fixed function of θ0 and these prompts and rows.
   - The committed script cannot run on the Mac: it always uses the real loaders (SIM:421-426), which run only on CUDA
     ("the real loaders run only on CUDA; 'cpu' is for engineering fixtures, never a scientific fallback",
     `experiments/safety_selection/loaders.py:121-129`; `experiments/minimal_safety/model.py:377-385`).

   **Ruling.**
   1. **A scheduling gap, not a deviation.** The pass runs once, after both blocks and before any stage-1 outcome is
      read; the SHA-256 of `strata.json` goes into FOCUS before any add-arm outcome is read (ADD:375). Nothing measured
      changes, because no input of the pass depends on when it runs (the same pattern as c0's move, "a scheduling
      change inside block A, and nothing measured changes", ADD:522). W1R:129's "B14 builds the strata at S1" could not
      be met for the strata themselves: S1 is "before the stage-1 freeze, which comes before block A" (REV4:29), and two
      of the three add sets the strata need, S3 and S4, did not exist until after block A's diagnostics pod had started
      (S4's edit file dates from 25 Oct 15:42 UTC and S3's from 16:46 UTC; R1B:69-74, which reads W1R:129 as a build
      deadline, R1B:61). It is read as B14's code, built and verified at S1 (ADD:503: "B14 87/87"); the strata are built
      later from the same inputs. The ruling stands either way.
   2. **Route: kit round 34 and one A100 pod.** Round 34 adds one job kind that runs the pinned SIM once (engine X,
      recipe REC, no unit, no measurement), with S1 code pins for SIM `f8305c71…` and its settings `27db4c3f…`, tests
      and mutants (R1B:179-183). The $0 Mac pre-check of the tokenizer and codec runs first (R1B:263-295). One A100 pod
      runs it from a background job, paid from the balance (KW:8): about $0.60-0.75, worst about $2.7-3.1 at the cap
      (R1B:186-189; estimates). D-6 lands before `strata` runs. Round 34 is built and verified (CKB; CKV; LR R3). It
      changes `stage1_rules.py` (`bde78fab…` → `4005cb4e…`) and `plan_tool.py` (`f18bb834…` → `27e299b5…`) (CKB:31-32);
      `seal.py` and `judge_units_stage1.py` are unchanged. The runbook's "never changes" list takes the two new hashes
      (LR R3.2).
   2b. **Round 34 changes the rules file the reading loads.** Round 34 lands in the live kit `tmp/stage1-olmo/` to run
      its pod, and the runbook requires the repository and live copies of the kit files to be equal (R1D:220, :228-229),
      so it lands in `runkit/stage1-olmo/` too before the reading; the reading's builder loads that rules file by default
      (RI/__main__.py:27-28, :40; RI-O13, RIB:460-462). Round 34 leaves every value the builder and B14's inputs writer
      read unchanged: `block_runs` for blocks A, B and C, `REUSED_SEEDS`, `REJUDGED_PINS`, and the judge constants
      `JUDGES`, `JUDGE_INDEX`, `JUDGE_INDEX_KIND`, `JUDGE_INDEX_VERSION`, `JUDGE_FILE_PATTERN`, `JUDGE_NAMES` and
      `JUDGE_INDEX_ENTRY_KEYS` (RI/build.py:242-262, :537-557). **That equality was checked by C's verifier, not pinned
      by a test (LR R3.3):** the verifier loaded the `55d5f8b` and round-34 files side by side and found every such
      value equal (CKV:37, :137, :190); round 34 has no test that pins them, and this record's first draft was wrong to
      claim one. The runbook's pinned kit-pair hashes (R1D:228-229) and the second stamp take round 34's new hashes;
      otherwise the reading's R0 check stops before any value is shown (R1D:497-517), at the cost of a new second stamp.
   3. **Seal, and how `retrieved/` is touched (LR R3.1).** The SHA-256 of `similarity.json` (equal to the one the pod
      prints) and then of `strata.json` go into FOCUS before any add-arm outcome is read (ADD:375), and both go into the
      second stamp. `retrieved/` is on the never-open list (FOCUS:74). The one exception: tools may read
      `tmp/stage1-olmo/retrieved/sim-1/` only by the exact path and SHA-256 that `record-done` prints (CKB:349-351,
      :365-367). `overlap_strata.py strata` runs in place on that path. A script copies `similarity.json` into the B14
      records folder with a SHA-256 check and prints only the hash. `similarity.json` holds no stage-1 outcome: it is
      training-row to evaluation-prompt similarity, with no model output. On a crash the lead may read sim-1's
      `process.log` (B14's own stdout, which names ids only; no model output; CKB:356-357) and records that read. The
      lead never lists `retrieved/`.
   4. **The Mac route is dropped** (PLAN:31's fallback (i)): it would need new loader code that the engine forbids for
      scientific runs, a weights download of about 3 GB, and a deviation from "on the pod" (R1B:209-245).

   **Pre-set fallback.** A one-off pod outside the kit with the same command and a written checklist (a self-stop
   timer, the minimal bundle, hash checks, pull, stop; R1B:193-207). *Trigger:* round 34 is not verified (kit suite
   and mutants) when the other builds are done, or the kit refuses for a reason that needs another round (R1B:253-254;
   CRIT:348). **N5 accepted (LR R3.4):** C's verifier found that a warning written without a trailing newline just
   before the pod's "wrote" line makes a good run a crash under the printed-SHA-256 rule (CKV:135, :201). The plan pays
   one re-run (`defer sim-1` to `sim-2`, from the `sim` contingency, CKB:356-357); then this fallback's one-off pod with
   the checklist; last resort `--no-overlap` ("not computed").

   **Last resort.** `--no-overlap`, with D-6's fallback wording and this cause ("no strata: B14's similarity pass did
   not complete"). *Trigger:* two pod attempts end without a written `similarity.json`, or the live balance is below
   $6 + the pod's cap × $1.85 (R1B:255-256; CRIT:348).

13. **Post-W1 deviation D-7: LN-31's draw is built after its deadline (the number is the lead's, in ruling order; CRIT:243).**

   **Facts.**
   - LW-30: "A one-paragraph commitment in REQ-21 before wave 1, with the full protocol before block A; it adopts no
     spend" (REV4:762). The draw "reads block-A guard files only after block B is complete, by a script that prints
     totals only" (LN-31, REV4:763).
   - HLC:164: "Before the draw script reads any stage-1 guard file", the lead commits the frozen protocol, the draw
     script and its SHA-256, the seed tags, the §8 term list and the input files by SHA-256. HLC:168: "Freeze deadline
     (decision HD8): before the first stage-1 block-A pod launches, so the draw cannot depend on any stage-1 outcome."
   - W1R:243 (item (f) rule 7) says the same: the full protocol, its draw script, seed tags and input hashes are
     committed before block A's first pod launches.
   - The first block-A pod, s10-1, was created at 2026-10-25T11:04:34 UTC (FOCUS:125-126). HLC is still "DRAFT … Not
     frozen" (HLC:3), and at the design round no draw script existed (R1D:37, :831-834). No guard file has been read for
     the draw, and no stage-1 outcome has been read (blocks A and B sealed and unread, FOCUS:107, :77).
   - Track D2 built the draw on 1 Nov (`scripts/stage1_s1/hlc_draw/`: the script, its settings with the seed tags and
     the term list, its tests and mutation spec; D2B:26-31, :43-56), after both seals and before any stage-1 outcome was
     read; it is verified after one fix round (D2V:13-16; LR R5, status line).

   **Ruling D-7.**
   1. LW-30's "full protocol before block A", HLC:164's and HLC:168's deadline and W1R:243 were missed: the deadline was
      before block A's first pod, 2026-10-25T11:04:34 UTC; the draw was written on 1 Nov, after both seals and before
      any stage-1 outcome was read (LR R5.4). This is recorded as post-W1 deviation D-7, and the paper states it with the
      date the protocol was committed.
   2. The deadline's purpose, a draw that cannot depend on any stage-1 outcome, still holds if HLC:164's items are
      committed before any stage-1 outcome is read. **Default:** freeze the protocol (HLC revision 2's draw, adopted by
      LN-34, REV4:762) and commit it with the draw script and its SHA-256, the seed tags, the term list and the inputs by
      SHA-256 before the second stamp; test the script on synthetic data; a second process recomputes the draw and
      prints only "match" or "mismatch" and totals (HLC:167). The draw runs as the reading's step 5, after the reading,
      and prints totals only (REV4:763; HLC:165). No rater is recruited and nothing is spent (REV4:762; KW:9).
      - **The inputs "by SHA-256" (HLC:164)** are bound through block A's seal and `stage1_rules.REJUDGED_PINS`
        (COMPLETE.json and job.json SHA-256; COMPLETE.json lists every file's SHA-256), the 9 Oct key by its
        pre-registered SHA-256 and the bank by the data config's `banks_from`, as track D2 built it (D2B:37-41); the
        draw's manifest repeats them. So no sealed guard file is opened or hashed before the reading (EV2:150-152).
        Before step 5 the inputs are restored and pinned in `tmp/hlc-inputs/`: the 9 Oct key at
        `tmp/hlc-inputs/oct9/key.json` and the prepared-v3 set at `tmp/hlc-inputs/prepared-v3-inj05` (LR R5.5; paths
        named here, not opened). `tmp/hlc-inputs/` is on the never-open list for every helper.
      - **HLC 4.3 item 4, "a second, independent process" (LR R5.3):** the package's `check` re-runs the same code in a
        second process; it is not independently written code (D2B:250; D2V:80-83). This reading is recorded as part of
        D-7. Partial cover: the two verifiers' independent re-implementations reproduced the tool's draw item for item on
        synthetic draws (49 identical re-computations and an exhaustive check of 6,000 small cells, D2V:13-16).
      - **D2's suite is re-run after track A's merge** (the draw imports `reading_input`; D2B:248-249; LR R5.5).
   2b. **Confirmed readings (LR R5.1; D2B:373-386).** Reading 4: the split counts prompts for the total, the bounds and
      the minimums, and answers for the proportion. Reading 7: the protective reading, under which rule b also reads the
      greedy harm answers' categories. Reading 11: the benign block is each population unit's own greedy over-refusal
      answers with their stored full-answer "Refusal" flag. Reading 12: theta0's Unsafe cell also takes the HarmBench
      split. Reading 13: a cell's target is cut to its distinct available prompts, and any rest flows to the next cell.
      The 106-term list and the 5 age patterns (D2B:357). The benign label is each unit's stored full-answer Refusal flag
      on its own greedy answers, which the paper states.
   2c. **Limits recorded (LR R5.2).** The HarmBench minimum of HLC 4.2 is often lost across seeds in low-U arms, a
      consequence of HLC's fixed order and its no-prompt-twice rule: confirmed as reading 4, with its simulated size
      stated, about 6-13% of seed cells at U 0.03-0.05 and q 0.2 (D2V:52-66; the estimates lose precision, not
      validity). The weights file splits by HarmBench label only in the Unsafe cell, less fine than HLC:157's sentence
      (D2V:67-79): a recorded limit; the missing counts can be recomputed from the hashed inputs.
   3. **Pre-set fallback.** No step 5 at the reading; the draw runs when the human label check is funded, and its code
      is labelled "written after the stage-1 reading and after HLC:168's deadline". *Trigger:* the draw is not verified
      when D-5, D-6 and B14's inputs writer are built (CRIT:351; R1D:787-789). Not triggered today: the draw is verified
      (D2V:13).

   **S1 blinding line.** Written [FILL-time], after the W1 commit and after every Gate B value the S1 blinding record
   lists. The human label check is report-only and exploratory (REV4:762); the record lists D-7 for completeness, and
   the paper labels it "fixed after Gate B wave 1".

14. **ADD:428: B16's size, coverage and familywise-error simulations.**

   **Facts.**
   - ADD:428 (§16 point 4, 23 Oct 00:40 UTC): "The size, coverage and familywise-error simulations are not re-run on
     the final code; they run once more, at the S1 freeze."
   - **The recorded run.** B16's statistics verifier ran them from 2026-10-22T22:07:04Z to 23:02:02Z on the build tree
     (`ws-b16`, 25 files equal to the build report's table) before B16's fix pass: NOTES `b16-verify-stats.json`
     (SHA-256 `65fe90c39b429b246168a4b93b8eb1ff2b5a2831615dc7be9b0d3a733976e5e3`; lines 5-6 the times, :9 the tree, :87
     `simulations`: `seed_level_size_and_coverage` :88, `item_level_coverage` :252, `phi_familywise_error` :279,
     `reml_kkt_scan` :371). Its readings: seed-level size under the built active set near nominal ("90% coverage
     89.8-90.1% mean, 89.1-90.1% worst contrast"; at 0.75% the worst world 0.98%); item-level 90% coverage 89.2-91.8%
     with the crossed item part; Φ's familywise error at the z level against the review's own generator, 0 mismatches
     over 108,000 p-vectors and "every value <= 5%" (:282-283, :352); end to end through whole readings, G0 plan A
     4.11% ± 0.47 and G0 plan B 5.20% ± 0.70 (:356, :358), so plan B's end-to-end rate is within Monte Carlo error of
     5%, not shown below it.
   - **Not re-run on the committed code.** The fix pass (NOTES `b16-fix.json`, SHA-256
     `4090118e0616e62c23665f36b730d26e6440af935e08d524b74f188b9aeea600`, finished 2026-10-23T00:37:45Z) states at line
     269: "the verifiers' size and coverage simulations (sim_seed.py, sim_item.py, fwer_e2e.py) were not re-run; the
     stop-rule change can only move fits that were falsely converged, which the KKT and plan-B rechecks cover". B16 was
     committed after that pass (`2135c2d`, 2026-10-23T00:40:40Z).
   - **No run at the S1 freeze is recorded.** In NOTES no other record names `sim_seed.py`, `sim_item.py` or
     `fwer_e2e.py` (M in round 1: a `grep -r` over that git-ignored folder that printed file names only; the folder is
     not on the never-open list, and the search is reported so the lead can judge it). The committed record folders hold
     the halves simulation (B16/README.md:100-102) and D-4's regression re-run (B16H:457 onward: whole readings; one
     flagged synthetic document, B16H:539, differs only in an S-start entry, not a label, B16H:243), neither a
     seed-level size or Φ familywise run. CRIT:188-197 found no record either.
   - B16 changed after the run: the fix pass (B16/README.md:161-170), D-4 and the halves (FOCUS:104), and two mutation
     fixes with no behaviour change (FOCUS:99). Under D-5's route B16 does not change again.

   **Ruling.**
   1. **Cite that run** as the last size, coverage and familywise-error evidence for B16, with its limits: it ran on the
      22 Oct build before the fix pass; the fix pass covered its stop-rule change by the KKT and plan-B rechecks
      (`b16-fix.json`:269); D-4 changes a REML end point only where the pre-registered start stopped at a lower maximum
      (about 0.4% of plan-A fits, ADD:605; one synthetic block-A-only reading changed a label there, which is D-4's
      reason, ADD:605), and D-4's regression re-run flagged one synthetic document, an S-start entry and not a label
      (B16H:539, :243).
   2. **Record the missed step.** FOCUS and the reading record's limits say: "B16's size, coverage and familywise-error
      simulations last ran on 22 Oct 2026 (22:07-23:02 UTC) on its build before the fix pass; the re-run planned at the
      S1 freeze (addendum §16 point 4) did not happen."
   3. **Keep the evidence checkable (LR R6.5).** The lead commits copies of `b16-verify-stats.json` (SHA-256
      `65fe90c3…`) and `b16-fix.json` (`4090118e…`) from NOTES (in the lead's worktree `kind-hawking-a6ce04`) with the
      records, before the second stamp; today they are git-ignored files in one worktree's `tmp/`. The evidence
      folder's file list with SHA-256 values goes with them.

   **Optional (not the default).** Re-run `sim_seed.py`, `sim_item.py`, `fwer_e2e.py` and `zphi.py` (NOTES
   `b16-verify-stats-evidence/scripts/`; `zphi.py` made the z-level "every value <= 5%" reading of the facts above,
   `b16-verify-stats.json`:279-283, :367, and exists at that folder, M: `test -e`) on the final tree as the lead's
   background job at $0 before the second stamp. *Skip it when* the run would not finish before the second stamp
   (CRIT:353).

15. **The build round's hard-rule notes, recorded as disclosures (LR R3.5, R6.4, R6.6).**

   None is a blinding breach; each is recorded so that the lead can judge it and the record is complete.

   1. **Track C's `git ls-files` print (LR R3.5).** While checking which add-edit records the worktree tracks, C's
      builder ran `git ls-files .ai/inputs/stage1-post-w1-20261023/block-b | head -3`. It printed three file names
      under `block-b/` (a fingerprint record and two billing files): names only, no content, no value (CKB:404-406;
      CKV:246-248).
   2. **Track D2's three 600 s overruns (LR R6.4).** Three shards of D2's mutation run (shards 2, 3b and 3c: 11, 4 and 3
      mutants) ran past the tool's 600 s limit, and the harness moved them to the background; the builder had not asked
      for background runs. Each finished with exit 0 before the builder went on, and the scratch folders were deleted
      (D2B:210-213). Most of the wall time was machine load outside pytest.
   3. **Track E's round-1 `grep -r` over NOTES (LR R6.6).** To look for the simulation scripts' names, E's builder ran
      one `grep -r` over `tmp/claude-workspaces/stage1-integrate-20261017/notes/` (point 14 above). grep read the bytes
      and printed only matching file names; no content reached a model. The folder holds build, verify and kit reports
      of 17-27 Oct written by the lead's helpers, who never opened a sealed file, so there was no blinding breach.
      Recorded as a disclosure.
   4. Two earlier notes stay where they are recorded: the runbook author's repository-wide `grep -rln` (§39 point 8(g))
      and the readiness scout's print of two plant settings lines (§40 point 10).

**S1 blinding line (REV4:919; W1R:358).** Written [FILL-time], after the W1 commit (FOCUS:144) and after every Gate B
value the S1 blinding record lists (FOCUS:140, :138, :136, :135 with its §6 values possibly read, :126). No stage-1
outcome was read. The paper labels points 1-9 and 11 "fixed after Gate B wave 1". Point 10 is the user's decision,
not an inference rule.

## 40. Stage 1b before any pilot unit exists: the lead's rulings ([FILL-time]; decided by the lead, GI VIII, under the user's delegation; no stage-1b unit exists and no stage-1 outcome has been read)

Stage 1b's design is frozen in REV4 §8 (REV4:665-713) and the W1 record's items 17-25 (W1R:288-297), with the seeds
and draws of ADD:298-299 and the counting list of ADD:350-351. The plant, the decoy and every plant edit were built on
23 Oct (FOCUS:131). These rulings come before any stage-1b unit exists, so that the pilot's reading is fixed before
it can be seen.

- **Sources.** READY = `A-stage1b-readiness.md` (SHA-256 `8d1f5366ed267d33…`); CHECK = `A-stage1b-check.md`
  (`570e98ffb3d2a22c…`), both committed copies under
  `.ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/next-stages/` (commit `0e0ab1f`, 2026-11-01T09:41
  UTC, after `55d5f8b`; byte-equal to the scratch copies the scouts wrote, so the line numbers hold). LR = the lead's
  rulings `lead-rulings-20261101.md` and EV2 = `E-records-verify2.md`, as in §39's table.
  Where READY and CHECK differ, CHECK's corrections govern. Both cite FOCUS at `0daca9a`; below, FOCUS lines are
  `55d5f8b`'s (one higher from FOCUS:74 on; the pin stays, no remap, LR R6.5).
- **Citations** are `path:line` at commit `55d5f8b`; short names as in §39's table, plus RULES =
  `runkit/stage1-olmo/stage1_rules.py`, PT = `runkit/stage1-olmo/plan_tool.py`, JR =
  `runkit/stage1-olmo/setup/job_runner_stage1.py`, MAN1 = `.ai/inputs/stage1-commitments-20261016/MANIFEST.json`,
  PLANS = `research/review/2026-10-08-sharpened-direction-DRAFT.md`. The code file `scripts/stage1/report_plant_ranks.py`
  is cited from CHECK. Of the code file `scripts/stage1/build_plant.py` I opened lines 282-287 and 306-308 (round 1),
  and lines 30-37 and 276-315 and a `grep` of its output paths and record keys (fix round), all at `55d5f8b`: code
  only, under the brief's code rule; no settings, record or output file of the plant was opened.
- "Added" marks a ruling this draft adds to the brief's list; the lead keeps or drops it.

1. **The pilot gate, read literally** (REV4:675; W1R:291).
   - **Λ_plant** = the seed-paired mean over seeds 1101-1103 of U(a0_plant, j) − U(Gate A's a0, j), in pp, where U
     is the Qwen3Guard Unsafe share of the unit's 600 sampled answers to the 200 dev harm prompts. In B16's
     `contrast_paired`, which returns c − m (B16/contrast.py:168-173), c = a0_plant and m = Gate A's a0, so a plant
     that raises U gives Λ_plant > 0 (CHECK:127-128).
   - **Go:** Λ_plant ≥ 10 pp and its one-sided 90% lower bound > 5 pp.
   - **Raise:** 5 pp ≤ Λ_plant < 10 pp. Then k rises to 75 once: a0_plant75 at 1101-1103, again against Gate A's a0
     (CHECK:129-130), read by the same go test. Any other result of the re-pilot stops; there is no second raise.
   - **Stop and report the null:** everything else, including Λ_plant ≥ 10 pp with a lower bound ≤ 5 pp
     (CHECK:122-126), and Λ_plant < 5 pp.
   - **Edges (added here; adopted by the lead, LR R6.5):** every comparison of Λ_plant (the point estimate) with 5
     and 10 pp reads through B16's tie tolerance (1e-9 pp), as B16 reads δ; the lower bound's comparison with 5 pp is
     exact, as B16 reads interval ends (B16/README.md:153-155: "interval ends (irrational) do not"). A three-seed
     mean of 600-answer shares moves in steps of 1/18 pp, so it can equal 5 or 10 exactly, and a float can land 1e-15
     below (CHECK:124-125). It reads the frozen edges exactly and moves no target: in the verifier's measurement, 627
     of 2,000 three-seed means that are exactly 10 pp as rationals land below 10.0 in floating point (EV2:179), so
     without the tolerance the literal rule could not be read on exact shares.
   - *Reason.* The literal text already covers the case "Λ ≥ 10 pp, lower bound ≤ 5 pp" under "otherwise stop"; any
     other reading would change a frozen rule (REV4:886). *Not adopted:* reading that case as the 5-10 band (READY:357).

2. **The pilot interval: B16's paired form** (REV4:675). The seed part is the pair's own paired variance (ddof 1)
   over J with J − 1 = 2 df, plus the crossed item part from the 3 × 200 difference table, with Satterthwaite df
   (B16/contrast.py:113-118, :168-173). The one-sided 90% lower bound is Λ_plant − t(0.90, df) × SE; known answer:
   t(0.90, 2) = 1.886 when the item part is 0 (REV4:675). Under D-5's route B16 does not change, so the pilot reader
   may import these functions without moving B16's hashes (CHECK:275-276). **No fallback** (adopted, LR R6.5). Gate
   A's a0 per-prompt
   tables are those the stage-1 builder already reads through `REJUDGED_PINS["A"]` (RULES:171-183; RI/build.py:7-9,
   :259-268); if they cannot be built, the pilot is not read until they can, and any other interval would be a
   post-W1 deviation from REV4:675, written before any pilot value is read. *Not adopted:* READY's
   fallback, the seed part only (READY:358). It drops REV4:675's prompt part, and on a constructed synthetic table it
   turns the frozen gate's "stop" into "go" (M, synthetic, B16's own `contrast_paired`: Λ_plant 11.33 pp; frozen form
   SE 5.10 pp, df 198.5, lower bound 4.78 pp, "stop"; seed part only SE 0.10 pp, df 2, lower bound 11.15 pp, "go").

3. **Blinding.**
   - **The a0_plant unit names its leaf.** The plant edit's name is "stage1 plant…: planted corpus at k = {k} (leaf
     {cell})" (`scripts/stage1/build_plant.py:284`, :306-308); the engine's edit summary carries the name
     (`experiments/safety_selection/edits.py:90-92`), and the run writes it into the unit's result
     (`experiments/safety_selection/runner.py:496-497`), which goes into COMPLETE.json (CHECK:139-147). **Ruling:**
     readers read U and the per-prompt labels by key only and never print or write any other field. A test feeds a
     synthetic COMPLETE.json whose edit name holds a sentinel string and shows that the sentinel never reaches
     stdout, stderr, a traceback or the output file (CHECK:153-156). The remove-cell, R600 and R150 units are treated
     the same (CHECK:157-158).
   - **Never opened by hand or by a helper:** `tmp/stage1-olmo/retrieved/` (the kit's pulled block trees,
     CHECK:187-191; FOCUS:74: it "joins the never-open list") and every plant-arm unit folder. Only reviewed code
     reads them, by key (first bullet). The only exceptions are the two stated for the stage-1 reading, and neither
     touches a plant path: the similarity output under `retrieved/sim-1/`, read by the exact path and SHA-256 that
     `record-done` prints (no stage-1 outcome in it; §39 point 12 ruling 3, LR R3.1), and the reading-time readers
     `cap_reports` and `cost_table`, which open sealed-class files only inside the reading script at step 4c (§39
     point 11, LR R4.4). The lead never lists `retrieved/`.
   - **The counted score files name the leaf by omission:** they cover the planted corpus's ids, which lack the
     leaf's Dolly rows (CHECK:160-164). **Ruling:** they are written under a path whose name holds "plant", and their
     SHA-256 is committed and time-stamped before anyone opens them; only then the plant-rank report runs with
     `--counted` (CHECK:166-167).
   - **Names (added from CHECK):** every plant output (the plant-rank report, the scoring output, any plant-arm dose
     or token report) goes in a folder whose name holds "plant"; reader and wrapper code stays out of such names
     (CHECK:193-197). Leak tests use sentinel strings and cover stdout, stderr and every refusal message
     (CHECK:199-202).

4. **The construction checks** (the text-only scorers: L1, H1, H2a/b, DataShield-style and the classifier). The frozen
   text: "construction checks, published before the pilot, and also if the pilot stops" (REV4:684; W1R:293). Their
   inputs, J5's and J8's outputs from pod a-8, are under block A's seal (FOCUS:113; CHECK:261-265). Before the
   plant-rank report runs, the Mac outputs it needs are made if they do not exist yet: "DataShield-style and L1
   outputs on the Mac if they do not exist yet" (CHECK:363; READY:227-228 finds no recorded Mac run of
   DataShield-style). The plant-rank report's output names the planted unit and leaf (CHECK:169-173). **Ruling:**
   they run after the stage-1 reading, by the plant-rank report without `--counted`, into a "plant" path; the output
   is committed and time-stamped by SHA-256, unopened, before the pilot launches. **"Published before the pilot" is read as that committed, stamped
   SHA-256.** The output is opened only after the counted outputs are hashed (point 6), or after a final "stop".
   READY's fallback, "publish them readable before the pilot" (READY:359), is **struck**: it would show the leaf
   before A1 on a0_plant is scored (CHECK:169-176).

5. **Kit scope: kit round 35** (stage 1b's pilot), built after round 34 (B14's similarity kind), in a scratch tree:
   - one block P: a0_plant at 1101, 1102 and 1103 under the existing kind "arm", with its own funding record; P is
     added to `BLOCKS`, `FUNDING_BLOCK`, `HOST_PREFIX` and `BLOCK_KINDS` (RULES:615-625), `REJUDGED_PINS["P"]` empty
     (RULES:171); a0_plant at 38 steps (38 steps for n ≤ 100, REV4:671); `init-block P` needs block B complete and
     sealed (CHECK:290-298);
   - the edit through the kit's sealed edit record `{arm: "a0_plant", path, sha256}` (CHECK:295-298). Its path and
     SHA-256 come from hashing the planted_k37 edit file at its known path (`edits/planted_k37.json` under the plant
     build's `--full-out` folder, in git-ignored `tmp/stage1-mac-runs-20261023/`: `scripts/stage1/build_plant.py`:35,
     :290; FOCUS:131); no byte of it is shown (only its SHA-256 is computed and printed), because its name field
     names the leaf (`scripts/stage1/build_plant.py`:284, :307). **A binding check** (CHECK:313-315): a reviewed key-only script
     confirms that REQ-8's record lists that SHA-256 for `edits/planted_k37.json` (`scripts/stage1/build_plant.py`:291)
     and prints only "match" or "no match", tested with a synthetic record that holds sentinel strings;
   - a readable e1 and q fingerprint record for each plant arm, as the runner already writes for a0_arm
     (JR:896-900, :1039-1044), so that a later regeneration can be checked after P's seal (CHECK:299-303);
   - blocks A, B and C's tables (`block_runs`, RULES:294-315) and `REJUDGED_PINS["A"]` byte-identical, with a test
     (CHECK:292-293, :307-309); one test and one mutant per new refusal; the kit suite and the mutation runner,
     baseline first with the same command (CHECK:307-309).
   **Merge** into `runkit/stage1-olmo/` and `tmp/stage1-olmo/` only after the reading's outputs are sealed, because
   the reading loads the repository's rules file by default (RI/__main__.py:27-28) (CHECK:270-274). Not in round 35:
   blocks P1b and P2, per-seed draw keys for the plant's R600 and R150, the scoring job (CHECK:322-337).

6. **K7: A1 and Self-Inf-N-style scored on a0_plant** (the only diagnostics that count, REV4:684; W1R:293). Engine
   X's attribution step refuses any state that is not an a0 run-one (`experiments/safety_selection/runner.py:870-872`),
   so K7 is new code: a wrapper that scores the planted corpus's ids with engine X's own functions loaded by hash,
   with a golden check that reproduces engine X's per-row values on P's rows (READY:266; CHECK:328-333).
   **Ruling:** K7 is built now at $0, off the pilot's path, and **runs only after a "go"**, on its own pod that first
   regenerates a0_plant@1101 (train only) and accepts it only on equal e1 and q fingerprints from point 5's record;
   then it scores. Reasons: K7 is new code and needs a GPU golden check; the balance cannot fund the main sweep
   anyway; the frozen text fixes "scored on a0_plant", not when (REV4:675, :684), so this is a planning choice
   (PLANS:179 packs "3 runs + one scoring pass" as planning text) (CHECK:349-356). Cost after a go about $2-7
   (CHECK:232-234, an estimate). If the pilot stops, the counted diagnostics are "not run" and the construction checks
   are opened (point 4). *Not adopted:* CHECK's fallback, K7 on the pilot pod when K7 has passed its golden check
   before P is planned and the live balance covers the 9.25 h cap plus the $6 reserve (CHECK:350-352); it would
   score before a "go", against this ruling.

7. **No judges for block P.** The gate reads U, which the arm pod computes; the judge pods add only HarmBench and
   Granite (CHECK:221). A block with no released judge launch is complete without judge files (PT:791-795). If the
   pilot goes, P's three units are re-judged with P2's units through `REJUDGED_PINS`, the route block A used for Gate
   A's units (RULES:171; CHECK:304-306).

8. **The disjoint-anchor sensitivity: its frozen fallback is triggered.** The set had to be "chosen and sealed before
   S1 and before any planted run" (REV4:698). No source was named (REV4:699); ADD-8.1 has no file in the tree
   (ADD:407; REV4:706); `scripts/stage1/labels.json` has no `anchors.disjoint` key (M: 0 matches at `55d5f8b`).
   REV4:883: "The disjoint-anchor set not sealed before S1 → the limit sentence." **Recorded as triggered:** §6 of
   the paper states the shared PKU source of the plant and the anchors as a limit (REV4:698; ADD:350).

9. **F9 is not run** (adopted as written, LR R6.5). It runs only if stage 1b is funded (REV4:710; W1R:296); the
   plant builder's `--f9` is passed
   only after the user's yes and stage 1b's funding event (`scripts/stage1/build_plant.py`:30). Its $34-70 (E,
   REV4:710) is not in the balance, and the main sweep already waits for a top-up (point 11). Its frozen fallback
   applies: the $0 relocation replay (F6, REV4:692), and the paper says the runs side has one plant location
   (REV4:710).

10. **An earlier scout's breach of the path rule, recorded.** READY's author printed lines from
    `scripts/stage1/settings/build_plant.json` (lines 121-122) and `scripts/stage1/settings/report_plant_ranks.json`
    (line 17) (READY:51-55; CHECK:178-185). The risk is low: both are W1 settings pinned in the W1 manifest
    (MAN1:939-942, `06f70d98…`; MAN1:1107-1110, `c952eb72…`), committed at W1 on 22 Oct (FOCUS:144), before the
    plant draw ran on 23 Oct (FOCUS:131), so neither can hold the draw. No unit, leaf or cell identity was seen
    (READY:55; CHECK:81). The rule binds everyone, the lead included (CHECK:155-156): no file whose path holds
    "plant" or "decoy" is opened by hand or by a helper, except code files, until the counted outputs are hashed or
    a final "stop"; reviewed code reads such files by key only, or hashes them without showing a byte (points 3 and
    5: the key-only readers, the binding check of the planted_k37 edit file, the kit's packing of that edit, the
    pilot reader's reading of a0_plant units); the plant record and the plant edit files name the unit and leaf
    (READY:48-50; `scripts/stage1/build_plant.py`:307, :442). Plant-arm unit folders and `tmp/stage1-olmo/retrieved/`
    stay under point 3's never-open rule.

11. **Money.** The pilot is paid from the balance (ADD:633; KW:8): about $5-6 measured, kit upper $7.43, worst case
    $10.29 at the 5.75 h cap (CHECK:226-228, estimates). It launches only when the live balance covers its
    cap-based spend (ADD:635) above the $6 reserve (KW:8; ADD:657). The main sweep waits for a top-up: about $14-22
    measured plus $1.5-2.5 of judges; kit upper $33.85 (CHECK:235-238).

12. **Order (added).** The stage-1 reading; the construction checks hashed (point 4); round 35 merged (point 5); the
    pilot reader frozen by hash and stamped before P launches (CHECK:316-320); pilot P; its label recorded; report
    and go on (§39 point 10; KW:10). The pilot needs nothing sealed to run or to be read: Gate A's a0 values were read
    before stage 1 (REV4:896; CHECK:249-259).

13. **Two items for later, recorded now (added).** (a) The plant-rank report counts Self-Inf-N-style only while its
    settings' switch says REQ-13 was committed at W1 (CHECK:131-133). That settings path holds "plant", so the
    switch is confirmed only by a reviewed key-only extractor (the ADD:625 pattern), never by opening the file.
    (b) A "raise" needs a k = 75 change to the plant-rank report (new settings and code pin; CHECK:334-337), a
    post-W1 change written before any counted rank for a0_plant75, and only if the label is "raise".

**S1 blinding line (REV4:919; W1R:358).** Points 1, 2, 4 and 6 hold readings written [FILL-time], after the W1
commit (FOCUS:144) and after every Gate B value the S1 blinding record lists (FOCUS:140, :138, :136, :135 with its §6
values possibly read, :126), and before any stage-1b unit exists. The paper labels them "fixed after Gate B wave 1".
