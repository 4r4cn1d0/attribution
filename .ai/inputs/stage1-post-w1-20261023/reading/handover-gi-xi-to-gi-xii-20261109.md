# Handover: General Implementation XI -> General Implementation XII (9 Nov 2026)

Written by GI XI (the main-study lead from 8 Nov 13:41 UTC) at a clean boundary: build rounds R1 and R2 of the 7-8B
kit's block A and B build are merged, verified and pushed; nothing of GI XI's is running except as section 5 says.
Read this note, then the top of `research/FOCUS.md` (GI XI's entries are the newest five), then GI X's handover
`.ai/inputs/stage1-post-w1-20261023/reading/handover-gi-x-to-gi-xi-20261107.md` §1 (the user's standing rules) and §5
(the working practice): both still bind. Then the build rulings file (section 2).

## 1. What GI XI changed in the practice
- **Agents, not workflows.** GI XI ran each builder and verifier with the Agent tool (`subagent_type`
  general-purpose, `model: opus`; builders `effort: high`, verifiers `effort: xhigh`), each in a detached worktree under
  GI XI's scratchpad `…/1a199637-2a19-4fac-9cf2-8b00c9c1b5ff/scratchpad/b78/` (`ws-*`). The Workflow tool needs an
  explicit in-chat opt-in. Fixes went back to the same builder by SendMessage (it keeps its context); re-checks went
  to the same verifier. This kept each round's cost down (about 1 all-models point per 0.5 M agent tokens, M).
- **Every agent first reads** the shared rules file `lead/r1-common.md` (in the records as
  `build-round-20261105/r1-common.md`), then a short track brief (`lead/r2-*-brief.md` for R2).
- **Merges** use `lead/r2-merge/merge.sh` (copies by explicit path from each worktree's `git status`, refuses a clash,
  `cmp` each) and `lead/r2-merge/checks.sh` (every suite and every mutation spec, as one background job under
  `caffeinate -i`). Records copies: reports plus top-level scratch files under 1 MB by type; token scan before commit.
- **Times:** run `date -u` in its own call, then write the time (GI XI twice pre-typed a time and corrected it).
- **The user's rule on usage:** tell the user if the all-models weekly passes 90%.

## 2. The rulings (all in `.ai/inputs/stage1-post-w1-20261023/78b/`)
- `lead-rulings-gi-xi-20261108.md` (GXI): G1, the form of Part 2's leftovers (a committed part is amended by a dated
  file, never edited); G2, DES's header covers its third set.
- `lead-rulings-ab-build-20261108.md` (GXB): eighteen sets for the block A/B build. Key ones: B-1-B-5 (tracks, the lean
  planning route, one O-ext wrapper, items 3 and 6 before block A with a pre-set fallback); O1 steps = ⌈rows/128⌉; O2
  B10's certification; O3 no record names a file it did not load; O6 the anchor stops; O14 corrected into `GATE_78B`
  and `PLAN_B_78B`; S-1-S-10 and R-10-R-15, R-27 (SR-2's simulation); T-O1-T-O4 (the hybrid O-ext route); R-5 (one
  index per family and engine); R-20-R-23 (W1-18's own route pin and records folder); R-24, R-29, R-30, R-43, R-44,
  R-49, R-50 (block B's plan and SR-2's status re-derived from pinned sources; the blinding record's four files
  re-hashed wherever SR-2's status is used); R-34 (θ0's O comes from a fresh `o_only` pass under MAIN_F; the stored
  Llama θ0 unit is not on the O path); R-35 (each reference seed's certification pins the a0 unit at that seed; Llama
  1103 = N's a0-1103); R-38 amended (no Safe LoRA copy); R-40 withdrawn (the 3-seed fallback grid stays {1, 0.75,
  0.5, 0}, as Part 2 says).

## 3. Where the 7-8B tier is (branch `stageb-costs-and-recovery-safeguards-20261003`)
- `3481d85`: Part 2's leftovers (round 7b); Part 2 `8f7caece…`; amendment 1 `…-part2-amendment-1.md` (AM1,
  `b9158bbc…`), its rules fixed from its commit.
- `3ca3e21`: Track C, the $0 count tools. `6a31791`: the $0 checks (`78b/zero-checks-20261108/`, README): every S-pool
  list prompt, the 400 PHTest prompts and the anchor list encode on both families (no reduced list); OLMo-2-7B
  τ_L = 0.0072668 nats; the S1 re-check byte-identical; Llama θ0's recipe has MAIN_F's generation and guard blocks.
- `bfda225`: R1: K1 (the kit's rules layer), Track S (`blinded_sigma.py`, the SR-2 simulation), Track O (the 7-8B
  O-ext layer). The full SR-2 simulation: largest familywise rate 0.05145 [B], 0.05175 [C], not above 6%: SR-2 passes
  its simulation trigger (`78b/sr2-simulation-20261108/`).
- `20a0ac2`: R2: K2 (the planning layer: the lean init-block A and B, the record steps for the gate, block B's plan,
  the branch and the anchor stop, SR-2's blinding half, judges, seal, states, C0_SOURCE at release) and Track R (the
  reference settings and wrapper `refs_78b.py`, B10's certifications per seed, Llama's recipe-G config at LR 5e-5,
  Track O's follow-ups). Merged checks in the main checkout: 7-8B kit 619, stage-1 kit 762, scale78b 698 / 2 skipped, the engine's family tests 95 passed; mutants killed: rules 248, runner 35, scorer 291, gated 128, count tools 71, O-ext 103, refs 88, SR-2 87. The merged run caught one integration mismatch (the W1-18 record's file name; R-53), fixed before the commit.

## 4. What is left before block A's first pod (in order)
1. **R3 = K3, the runner and pack** (after the 12 Nov 09:00 UTC reset, on Fable; K3 is the largest sub-round). Items
   (plan-ab.md §2's K3 row and the rulings): the O-ext arm step in arm, a0_arm and ref_train jobs (5a); the runner's
   O-ext commands `oext_78b.py <cmd> --family F --index PATH --index-sha256 H` from `OEXT_78B[F]` / `OEXT_78B_Y[F]`,
   W1-18 from `W1_18_78B` (R-20); the pack runs `oext_78b.py check` (the W1-18 record, R-6; the side units, R-9) before
   any O-ext pod; the W1-18 pod's form names its frozen readers and judge config (Track O's O10 list); R-47
   (`--w1-18-record` under Branch full, by a fixture test); W2-4, W2-5; N's regenerations and the two flags (5e, 5f);
   the reference commands through `refs_78b.py` with the `b10_certify` kind and the terms records retrieved (R-38,
   R-41); `ref_train` (recipe G) and `ref_train_bqi` (on Y); the reference jobs in block B's plan; engine Y's pack and
   KD9's re-measure (X1); the pack reads OLMo's S1 edit by exact path and SHA-256 (K-7); KR4 (the stop record carried
   by the pack and read by the runner; the anchor step's stderr kept); KR5's cross-track test of the shared stop-record
   fixture with Track S's reader (Track S's own fixture writes counts RK refuses: align it); R-16/R-31 (move the
   runner's and the pack's seed-only call sites, delete the seed-only form; test_41's list empty); R-18 (rewrite the
   runner's O-ext command-line assertions); R-44's packed-bundle re-hash at the pack receipt; K2R2-1 (a leftover
   `<part>.new` refuses by name, not FileExistsError). Plus a small $0 tool for R-46 (the padded-tokens record,
   train_scale's input), `scripts/scale78b/`, new files only.
2. **R4 = K4, hardening:** K6v-2, K6v-3, the whole-kit mutant sweep; `similarity` only if there is room (else "not run",
   DESO item 28). The `confirm` kind on Y comes before the first confirmation pod (about 11 Dec).
3. **The lead's $0 steps** (recorded steps, hash-only reads): θ0's job.json pins (K1 filled them, R-2; record the fill
   in FOCUS: done in R2's entry, with K1's and its verifier's measurements); the side units' R-9 check
   (`oext_78b.py check --family F --engine W1 --index …OEXT-78B-W1__F.json --index-sha256 … --data-root tmp`); seed
   1101's fingerprints (R-36); RECIPE_G for Llama (the new 5e-5 config) and Track O's `recipe_g` before
   `OEXT_78B[llama31-8b]` (O11, Track R's P6 order); the padded-tokens record (after R3's tool); the Safe LoRA disk
   fit (a Hub metadata read or the Range precheck at the next Llama launch); Llama's τ_L after N's record-done.
4. **Part 2's text round, then its freeze** (before block A's first pod): the [to be entered] values (§0 items from
   the $0 checks, N's values, Llama τ_L, the edit hashes after the scorer block, df = 12 per family (R-15), every new
   code hash and the simulation's outputs and reading), and the text the rulings changed: §2.1's steps rule with S4_top
   (O1); §3's references (O2's `b10_certify` in §15 item 6, R-35's seed table, R-37's points, R-34's λ = 0 limit, R-38's
   terms record); §4 (R-5, R-20, R-21, R-34); §8 (the references' E caps with the O-ext term, O12); §10 (R-15, R-43,
   R-44, R-49, R-50, the simulation's reading); §15 (X1-X5, B-5's 57-95 builder h, item 15 not needed); §16 (the limits:
   the prompt part, Φ's O and L words, the anchor count informational). §1 changes go in a dated amendment (AM2), as
   GXI G1 says. Re-take every code hash (§1.17 and §13.1).
5. **When money arrives:** block 0 (N) first, as GI X's note §4 item 5 says (fresh KD7 working copies; `budget.py
   check`; the HF token at the Llama launch from the user; launches as background jobs under `caffeinate -i`); then the
   noise reading, `record-gate-78b`, the scorer block (W1-18 first), Part 2's freeze, block A.

## 5. Money, deadlines, usage
- **Balance $18.33** at 2026-11-09T08:52 UTC (`runkit/stage1-olmo/budget.py`), nothing running, $0.026/h of storage
  (about $0.62/day; $10 is reached about 22 Nov). Block 0's money is expected about 20 Nov.
- **OLMo 3 deadline (GI XII owns it): 13 Nov 23:59 UTC.** Launch the probe only if its money (about $75 in all, C1 with
  block 0 ranked above it) is in the account then; otherwise record OLMo 3 at level 0 at that time (a FOCUS entry).
- **Usage at this note:** all-models weekly 88% (2026-11-09T12:14 UTC), Fable 100% until 2026-11-12T09:00 UTC. From the reset, agents run
  on Fable until its weekly use reaches 95% (`fable-fallback-to-opus`). Tell the user when the all-models weekly
  passes 90%.
- **Still running:** no agent and no job of GI XI's, except one `caffeinate -i -t 28800` started about 2026-11-09T04:00 UTC, ending soon. Start a new bounded `caffeinate -i -t 28800` before the next agents.
