# ICML 2027 re-plan for the main study (PROPOSAL)

**Status: PROPOSAL. It adopts nothing.** Written 2026-10-16 at about 21:25 UTC (17 Oct IST; clock checked with `date -u`) by an Opus worker for the main-study lead. Read-only work: no run, spend, install, commit or agent. The only new file is this one.

**Labels.** **M** = measured (the source follows). **E** = estimate (the basis follows). **U** = unverified assumption that is not in the records. Every dollar figure for future work is an **E**.

**Sources.** F = `research/FOCUS.md` on `origin/stageb-costs-and-recovery-safeguards-20261003` (entry timestamp in UTC). PODS = the kit pod records `tmp/family-probe-*/hosts/*/{create-result,finished}.json` and `tmp/gate-b-olmo/hosts/*` (local, git-ignored; `outer_elapsed_min` = job time; billed = start to verified stop). LEDG = engine stage ledgers `tmp/family-probe-olmo2-1b-g-seed1102/…/round1/1102-a0-e1-a1/ledger.jsonl`, `tmp/family-probe-sp-olmo2-7b-b-seed1103/…/1103-a0-e1-a1/ledger.jsonl`, `tmp/family-probe-sp-llama31-8b-b5e5-seed1102/…/1102-a0-e1-a1/ledger.jsonl`. SIDE = `research/side-notes/2026-10-11-prereg-results.md` on the side branch (erosion per seed). PLAN-S = `research/review/2026-10-08-sharpened-direction-DRAFT.md`. PRE = the frozen Gate B pre-registration, revision 5 (`5c97cce7…`). DOS = `research/grant/2026-10-05-grant-evidence-dossier.md`. FP = `research/grant/2026-10-13-funding-plan.md` (GPT-owned, untracked; read only).

## 0. Summary

- **Recommended: option B, staged, with option C as the pre-set fallback.** Now, fund and run only the parts that B and C share (Gate B at 1B, OLMo-1B stage 1, a 7–8B noise block on both families, all $0 preparation). On about 20 Nov, choose B or C by two facts: the money in the account, and the 7–8B noise reading.
- **Cost (E, GPU and storage, $1.79/h A100):** A about $860–1,170; **B about $1,180–1,760** (32B check extra, price U); C about $770–1,160. A and C cost about the same, but only C and B give reviewers the full comparison at 7–8B.
- **Money in hand:** $91.94 (F 16 Oct 19:08). Gate B's frozen wave-1 need takes $83.91 of it (F 16 Oct 13:21). No grant is awarded.
- **Main new risk (M-based):** the measured 7–8B seed spread is about 1.7× the 1B spread (pooled 5.8 against 3.4 pp). At 6 seeds the 7–8B minimum detectable effect is about 11–12 pp (unpaired per-arm SD; a paired contrast may be smaller, which the noise block measures), against the 5 pp SESOI.
- **Latest starts:** Gate B wave 1 by 27 Oct; 7–8B noise block by 9 Nov; 7–8B block A by 23 Nov; confirmation by 14 Dec; results frozen 4 Jan.

## 1. Goal and gap

The user's goal is ICML 2027 (F 16 Oct 21:05). The deadlines are **E** (third-party tracker; the official call was not found): abstract about 16 Jan 2027, paper about 22 Jan 2027 (AoE).

| What two FAQ reviews say ICML needs (F 8 Oct 15:59; F 16 Oct 21:05) | Current plan (F 8 Oct 12:53, 13:53) | Gap |
|---|---|---|
| The full repair comparison at 7–8B | 7–8B is a "reduced benchmark (key comparisons only)" | Main gap |
| A second dataset | Alpaca is planned "right after Gate B" (F 9 Oct 09:40), not costed or designed | Open |
| One replicated clear finding | Replication across two 1B families; confirmation at 1B | Not at the size reviewers weigh |
| A human label check | One reader, 50 answers (F 9 Oct 15:05) | Too small |
| Strong references | Five references at 1B (F 9 Oct 10:01) | Not at 7–8B |

## 2. Basis for cost and power

### 2.1 Unit costs (A100-SXM4-80GB at $1.79/h on every pod since 9 Oct; M, PODS)

| Item | Value | Label, source |
|---|---|---|
| 1B removal arm, 3–4 arms per pod | ≤ 49.0 min per arm; pod overhead ≤ 26.0 min; wave 0a: 3 arms in 2.67 billed h = $1.59 per arm | M, F 16 Oct 13:21 and 00:25 |
| 1B single-seed job (train + full e1 evaluation) | 34–74 min (16 pods) | M, PODS |
| OLMo-2-7B single-seed job, LR 1e-4/5e-5/G | 86–108 min, median 91 (8 pods); setup 20–38 min | M, PODS |
| Llama-3.1-8B single-seed job, recipe B rungs | 105–124 min, median 123 (4 pods); recipe G 137–141 (3 pods) | M, PODS |
| A1 diagnostics pass, 4,800 rows, OLMo-1B | 3.04 h | M, F 16 Oct 13:21 |
| **7–8B arm, 3–4 per pod** | OLMo-7B 1.55–2.0 h = **$2.8–3.6**; Llama-8B 1.9–2.3 h = **$3.3–4.1** | E: measured job + setup shared over 4 |
| Planning allowance | +20% for failed pods and re-runs (DOS §8b basis); judges on the pod about $0.1–0.2 per arm | E |

**How 7–8B time scales (M, LEDG):** training 4.1 → 14.8 / 14.5 min (×3.6); greedy generation 30.1 → 56.8 / 58.3 min (×1.9); sampling 12.8 → 13.3 / 43.3 min; judging about the same. Generation dominates, so a 7–8B job costs only about 1.9× (OLMo) to 2.3× (Llama) a 1B job, not 7×. Gradient work (A1) scales near ×3.6, so a 7–8B A1 pass is about 6–11 h (E).

### 2.2 Seed noise (M from the per-seed erosion E; power is E, normal approximation)

| Setting | Per-arm seed SD of U (df) | Source |
|---|---|---|
| OLMo-1B, recipe B (main) | 2.66 pp (2) | M, F 8 Oct 05:40 |
| Llama-1B, LR 5e-5 (main) | 4.34 pp (2) | M, F 9 Oct 23:16 |
| All five OLMo/Llama 1B cells pooled (recipes B, G; both LRs) | 3.44 pp (10) | M, SIDE and F (my pooling) |
| Gate B noise gate, paired scale σ̂_gate | 1.83 pp (2) | M, F 16 Oct 00:25 |
| OLMo-7B, LR 1e-4 (main): +49.7, +37.2, +45.5 | 6.36 pp (2) | M, SIDE |
| Llama-8B, LR 5e-5 (main): +52.5, +54.0 | 1.06 pp (1) | M, F 11 Oct 00:10 |
| **All six 7–8B cells pooled** | **5.83 pp (11)** | M, SIDE (my pooling) |

Six method seeds against 8 R seeds (removal) or 6 seeds (add); Holm's first step (α/6, two-sided); 80% power:

| σ per arm | Removal MDE | Add MDE | Seeds per arm for a 5 pp removal MDE |
|---|---|---|---|
| 2.65 (1B OLMo) | 5.0 pp | 5.3 pp | 6 |
| 4.34 (1B Llama) | 8.2 pp | 8.7 pp | about 16 |
| 5.83 (7–8B pooled) | 11.0 pp | 11.7 pp | about 33 |

*FAQ correction, 17 Oct: the 7–8B row first used σ ≈ 5.4 by mistake; recomputed at 5.83 with the same formula (z for α/12 plus z for 80% power, times σ·√(1/6+1/8) or σ·√(2/6)). These MDEs use the unpaired per-arm SD. If the stage-1 contrasts are read on the paired scale, as Gate B's σ̂_gate is (1.83 pp against a 1B per-arm SD of about 2.7–3.4), the real MDE may be smaller. The noise block decides this.*

At 7–8B with 6 seeds, a contrast's SE is about 3 pp. A TOST "equivalent" label at ±5 pp is then almost out of reach. Most null contrasts will read "inconclusive". This holds for options A, B and C alike. **The smallest decisive check** is a 7–8B noise block: R_1–R_3 paired with the existing a0 seeds on each family (about $30–40, E). It mirrors Gate B's wave 0a. It reads σ on the paired scale, blind to every repair outcome.

## 3. Options

Run counts are full-run equivalents (FRE; an evaluation-only job ≈ 0.85 FRE). Per family and size, the full comparison is: 6 method arms × 6 seeds (36); R to 8 seeds; a0 to 6 seeds; recipe G 3; B+Qi 3–6; evaluation-only references (safety prompt 3, adapter scaling 6, Safe LoRA 3); scorers (anchors, A1, L1, S3, S4, a lean c0 job). Engine-X units that the side project already made are reused where the rule allows (F 10 Oct 12:09): OLMo-7B a0 seeds 1101–1103 and recipe G seeds; Llama-8B a0 seeds 1101–1102.

| | **A: current plan** | **B: full comparison, both 7–8B families** | **C: lean ICML** |
|---|---|---|---|
| Scope | 1B full, both families; 1b sweep; 1B confirmation; 7–8B reduced (a0, R, about 2 repairs, 2 references; about 30 runs per family); Alpaca on Llama-8B (stage 4) | Gate B at 1B; OLMo-1B stage 1 (development); Llama-1B primary family (replication); P1–P6 + 5 references on OLMo-2-7B and Llama-3.1-8B; confirmation at 7–8B (≤ 2 contrasts per family); Alpaca on Llama-8B, reduced; 32B if funded | As B, but the full 7–8B comparison on one family only; confirmation on that family; Alpaca on OLMo-1B |
| 7–8B FRE | about 60 | OLMo 65–72; Llama 69–76; confirmation 36–48 | 65–76 + confirmation 18–24 |
| Cost, all stages (E) | $860–1,170 | $1,180–1,760 (7–8B full alone $520–710) | $770–1,100 (OLMo-7B) or $830–1,160 (Llama-8B) |
| 7–8B A100-hours (E) | about 110 | about 290–420 with confirmation | about 130–230 with confirmation |
| Calendar for the 7–8B part (E) | about 1 week at 4 pods | 7–10 days at 8 pods; 2–3 weeks at 4 pods | 1–2 weeks at 4 pods |
| Power at 6 seeds (E) | 1B: 5.0 pp (OLMo), 8.2 pp (Llama); 7–8B reduced about 11 pp | 1B as A; 7–8B about 11–12 pp per contrast | as B, on one 7–8B family |
| Gate B at 7–8B? | No | No full Gate B; an optional "Gate B-lite" transfer check (§4) | As B, one family |
| Main risks | Misses the main ICML gap; likely TMLR-level | Money (none awarded); 7–8B power; 13-week schedule over the holidays; 8 parallel A100s may not be free; Llama-8B's rung is "at the edge" (F 11 Oct 03:53) | Cross-family claims only at 1B; reviewers may ask why one 7–8B family; the family choice must be fixed before the noise block |

**Simpler alternatives considered.** (1) Drop Llama-1B in B, because Llama-8B carries the second family: saves $115–135. It is the first 1B cut. (2) At 7–8B, run only the arms that 1B shows non-null: cheaper, but it is A's "reduced benchmark" again. (3) More seeds on fewer arms at 7–8B (for example P1, P3, P6 at 12 seeds, R 16): MDE about 7 pp at σ 5.5 (E). That is the pre-set branch if the noise block reads high (decision 3).

## 4. Gate B at 7–8B, and keeping the frozen Gate B valid

**Trade-off.**
- Gate B asks whether the erosion is localized to Dolly categories. Under D5 = (a), the primary estimand P1–P6 is read whatever Gate B shows (F 16 Oct 12:15).
- A full Gate B at 7–8B is 15–29 runs per family (PRE §1): about $55–110 per family (E) and 1–2 weeks. That pushes the 7–8B comparison past its latest start.
- **Recommended:** no full Gate B at 7–8B. If 1B reads LOCALIZED, run a pre-registered Gate B-lite transfer check: the 1B-picked unit(s) at 3 seeds on each 7–8B family, against the R arms that P1 needs anyway (3–6 runs per family; $0–56 in total, E). If 1B reads DIFFUSE, skip it. The paper then says plainly that localization is tested at 1B only.

**What keeps the 1B Gate B valid.** Nothing in this re-plan touches PRE revision 5, the reading, the sealed rankings (`d6d5cd6b…`), the seeds, the money rules or engine X (`472fc7f6…`). Any 7–8B arm is new work under its own frozen pre-registration. It may use 1B results as development evidence. It never re-reads a 1B verdict. Gate B's reserved need ($83.91) stays untouched: every 7–8B launch uses new money, so each Gate B launch still meets its frozen threshold. No engine file changes until Gate B's last kit pod (stage-1 brief, T4). Engine round Y and any 32B/70B engine change come after that pod.

## 5. Schedule (backward from about 22 Jan 2027; dates are latest starts)

| Latest start | Step | Needs | Funding gate |
|---|---|---|---|
| now–8 Nov | $0 preparation (list below) | builder time | none |
| 27 Oct | Gate B wave 1, then wave 2, extension, length control | the stage-1 commitments committed | F0: in hand |
| 3 Nov | OLMo-1B stage 1, block A (block B follows) | Gate B verdict | **F1, about $150 new** |
| 9 Nov | 7–8B block 0: noise block, Llama-8B third Gate A seed, anchors, scorer passes (A1, L1, S3, S4), c0 | 7–8B kit; new money | F1 |
| 16 Nov | Alpaca probe and Gate A on Llama-8B (B) | the dataset LR rule; download approval | F2 |
| 20 Nov | **Freeze the 7–8B pre-registration; choose B or C** | noise reading; money in the account | **F2: B about $900–1,300 more; C about $550–800 more** |
| 23 Nov | 7–8B block A, both families (B) or one (C); Llama-1B replication in parallel | F2 met | F2 |
| 3 Dec | 7–8B block B, references; Alpaca comparison | block A complete | F2 |
| 7 Dec | 32B Gate A on an H200 (only if funded by 1 Dec) | smoke test passed | F3 |
| 14 Dec | 7–8B confirmation (stage 3); human label check | engine Y certified; frozen choice rule | F3, about $140–230 |
| 4 Jan | Results frozen; writing to 8 pages (body now 9.36 pp; F 16 Oct 21:05) | — | — |
| 16 / 22 Jan | Abstract / paper (E) | — | — |

**Prepare now at $0:**
1. 7–8B kits. Replace the preflight projection with a measured upper bound. The 7B projection was about 39,500 s against about 5,400 s real (M, PODS), so the cap rule would block 4-arm pods. Memory settings already exist: micro-batch 2 × accumulation 64 for both 7–8B models (M, PODS recipes `study-kt-olmo2-7b-r64-b-mb2-20261008`, `study-kt-llama31-8b-r64-b5e5-mb2-20261010`).
2. Make the stage-1 pod scripts (Part C) work for any model, with tests on tiny OLMo-2 and Llama configs (layer-index rule).
3. Draft the 7–8B pre-registration: seed rule, SESOI branch, transfer-check rule, family-choice rule for C.
4. Engine round Y design (build after Gate B's last kit pod).
5. 32B/70B design: model ids, GPU types, memory ladder, caps, smoke test, and a $0 price read.
6. Alpaca design note: units, field mapping, version, licence.
7. The human-check protocol; cut the paper to 8 pages around the 1B results.
8. File the fellowship compute form with this plan's figure.

## 6. Money

| | A | B | C |
|---|---|---|---|
| Total, GPU + storage (E) | $860–1,170 | $1,180–1,760 | $770–1,160 |
| New money after the $91.94 balance (E) | $770–1,080 | $1,090–1,660 | $680–1,070 |
| 32B headline check (B only, if funded) | — | about 30–50 H200-hours (E); +$110–230 if an H200 bills $3–4/h (**U**) | — |
| 70B on a B300 | — | not recommended for ICML; price **U**; the $10/h limit (F 9 Oct 15:29) may block it | — |
| Human label check (not GPU) | $0–800 | $0–800 | $0–800 |

**In hand and pending.** Balance $91.94 at 19:07 UTC on 16 Oct; idle storage about $1 per day (F 16 Oct 19:08). Pending, none awarded (F 15 Oct 20:05): BlueDot $6,000 (reply expected about 18 Oct, not guaranteed); TAIF $3,000 (about 24 Nov–8 Dec); AIAF up to $2,000 of engineering (no receipt found). The program lead added $500 of compute on 8 Oct (memory `compute-funding-program`); the compute form (about $1,500) is not recorded as filed.

**Two funding traps.** BlueDot's compute line ($3,700) names a $3,000 held-out selector comparison, which D5 moved to a later study (F 16 Oct 12:15). TAIF's extension "follows a funded and completed base phase" (FP). Using either for the 7–8B comparison may need the funder's agreement.

**Minimum to start:** about $150 of new money by about 1 Nov (OLMo-1B block A, the 7–8B noise block and scorer passes). B then needs about $900–1,300 more by about 20 Nov and $140–230 by about 1 Dec (confirmation). C needs about $550–800 by 20 Nov and $70–120 by 1 Dec. The compute form alone (about $1,500) would fund C, or most of B.

**Cut first if short, in order:** (1) 70B, then 32B; (2) the optional 1c secondary arms; (3) Llama-1B's replication ($115–135); (4) confirmation to one contrast per family (about −$70–110); (5) Alpaca from Llama-8B to OLMo-1B (about −$35–65); (6) the second 7–8B family, which turns B into C (about −$230–390). Never cut: Gate B at 1B, the a0 and R arms, the seed rules, the human check.

**Context, money already spent.** The side project's 7–8B pods billed about 41 A100-hours on OLMo and Llama (about $73) and 15 on Qwen-7B (about $27) (M, PODS). That money is sunk. It bought the measured 7–8B job times and the reusable engine-X a0 units this plan uses.

## 7. Decisions for the user

1. **Option:** B staged, with C as the fallback (recommended); or C now; or A.
2. **The 20 Nov gate rule:** B if about $900–1,300 of new money is in the account, the confirmation money is in sight, and the 7–8B noise reading allows plan A; else C.
3. **7–8B power branch, fixed before the noise block:** if σ̂ is high, (a) a 7–8B SESOI of 10 pp (1B keeps 5 pp), or (b) a 3-arm family (P1, P3, P6) at 12 seeds, or (c) both. This changes a scientific target at 7–8B, so it is the user's call.
4. **Gate B at 7–8B:** the transfer check only if 1B reads LOCALIZED (recommended); none; or a full Gate B.
5. **Reuse** the side project's engine-X 7–8B units as main-study a0 and G units, and run Llama-8B's third Gate A seed (about $4, E).
6. **Family for C**, by a rule fixed before the noise block: the smaller pooled σ̂, or Llama-8B (the published setting).
7. **Alpaca:** on Llama-8B, reduced (B), or on OLMo-1B (C). First extend the per-family LR rule to datasets and approve the download (pending since F 9 Oct 09:40).
8. **Confirmation** at 7–8B through engine round Y: up to 2 contrasts per family, or 1.
9. **32B** only if funded by 1 Dec; 70B dropped for ICML.
10. **Funding actions:** file the compute form now; ask BlueDot and TAIF whether their lines may fund the 7–8B comparison.
11. **Human label check:** about 400 answers, two readers; paid or volunteer.
12. **Fallback venue** if F2 fails: TMLR or NeurIPS 2027 (the standing fallback).

**Unchanged:** the frozen Gate B rules (PRE revision 5, the reading, the sealed rankings, the money rules, the $10/h limit, the guard); D5 = (a) (P1–P6 primary, Holm over 6 at 5%, SESOI 5 pp at 1B; the selector secondary; the held-out selector comparison a later study); the stage-1 build (L1–L16) and "wave 1 waits for it"; recipe B and the per-family LR rule (OLMo 1e-4, Llama 5e-5 at both sizes); Dolly as the primary data; PKU for the add repairs; the judge rule; U as the primary measure.

## 8. Limits of this proposal

- The 7–8B σ values rest on 1–11 df from the side project's units. The noise block replaces them.
- Per-arm 7–8B costs assume 3–4 arms per pod, as at 1B. No 7–8B pod has run more than two units.
- No H200 or B300 price is in the records. The 32B/70B time scaling is a rough E.
- The ICML dates are not official.
- I did not re-check A100 supply for 8 parallel pods, or the Claude plan usage that the build needs.
