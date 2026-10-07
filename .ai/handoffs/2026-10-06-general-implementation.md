# Handoff: General Implementation, end of the 3–6 October 2026 session

Written 6 October 2026 at about 00:40 IST (5 October, 19:10 UTC; the user is in IST) for the new chat, **"General Implementation 2"**.
- Read this first, then the documents it links.
- This file is separate from `.ai/HANDOFF.md`, which must **never** be edited.
- Times below are UTC on 5 October unless marked IST.

## LEAD HANDOFF, 8 October 2026 (about 02:00 IST): General Implementation II → **General Implementation III**

The user: "make General Implementation III, and then continue through that; we need to get past this hurdle today". **General Implementation III is now the lead** and the only chat that drives pods and commits. General Implementation II stops driving pods. It forwards one pending result (the build review below) and then goes quiet.

### Where the research stands (read these first)
- **research/FOCUS.md:** "Adopted direction", then every dated decision, amendment and frozen bar under "Decisions, 6 October 2026". Read the whole list; it is the source of truth.
- **research/experiments/2026-10-07-kill-test-stage0-results.md:** all results so far (Stage 0, recipe B, the Qwen2.5-7B check, the loop diagnosis, corrections).
- **research/review/2026-10-08-safety-landscape-papers-note.md:** the **Guo et al. contradiction** (see below).
- **research/review/2026-10-07-benign-erosion-recipes.md**, **research/review/2026-10-06-reading-dossier.md** (+ PDF), **research/review/2026-10-07-curvature-fragility-note.md**.

### The hurdle: Gate A of the kill test
We need a setting where ordinary benign fine-tuning gives a **partial** safety loss, with answers that end and skill kept. The user approved these frozen bars on 7 Oct, 19:14 UTC (FOCUS.md):
- **partial** = 20 ≤ E ≤ 55 pp;
- answers-end measured on the **sampled** answers (≤ 5% capped, ≤ 10% failing the screen), and every verdict must also hold on U over coherent answers only;
- ARC drop ≤ 0.03, and the task is learned (lower held-out loss);
- Granite agrees on the direction.

**So far:**
- Qwen2.5-1.5B-Instruct collapses (+75 to +84 pp) at the Stage 0 recipe and at recipe B (LR 1e-4, 128 rows per step, 38 steps).
- Qwen2.5-7B-Instruct also collapses (+82.2 pp; Granite agrees 97.5%).
- Greedy decoding loops after fine-tuning (every capped answer is a repetition loop).
- Stage 0 Gate A failed by its frozen rule on answers-end.

**Key new lead: Guo et al. 2026 (2609.01455)** report that stock Qwen2.5-7B-Instruct stays near its untuned ASR after **LoRA** on benign data, while full SFT collapses it. **Our rank-64, alpha-128, all-linear LoRA is the prime suspect** (161M trainable values at 7B). Standard practice is rank 8–16 (DataRx and SafeTune use r16).

### The user's go-ahead (8 Oct, "keep going ahead")
1. **Run the Qwen rank-16 test now** (about $4):
   - Qwen2.5-1.5B-Instruct with recipe B **changed only in LoRA r16, alpha 32** (scaling 2 kept). Everything else is identical, on frozen prepared-kt-dolly.
   - One seed (1101), the untuned baseline reused, read at e1 against the frozen bars.
   - Expected trainable count: one quarter of 73,859,072 = 18,464,768. Verify it.
   - It runs on the **old Qwen kit and engine c52c0ebc** (tmp/kill-test-gateA-b pattern; HEAD 38f806c still has engine c52c0ebc in the repo).
   - Record the recipe and a FOCUS.md entry **before** the run (the frozen-rule discipline).
2. **If rank matters** (rank-16 gives a partial loss, or clearly less than rank 64): send Specialized a short brief for **rank-16, alpha-32 variants of the family recipes** (config plus expected counts plus recipe-diff tests). Specialized's counts: olmo2-1b 12,058,624; olmo2-7b 39,976,960; olmo2-13b 62,586,880; llama32-1b 11,272,192; llama31-8b 41,943,040.
3. **Integrate the multi-family build** (below) after the review fixes. Then run the Mac checks (Mac check 0: re-preparing prepared-kt-dolly must give 9247c4bb; the family data preparations; tokenizer fetch for Llama with the HF token).
4. **Run the family probes:** OLMo-2-1B and Llama-3.2-1B first; **stop gate after the two 1B probes**; then 7–8B; 13B only with a top-up. Read every probe with scripts/family_probe_reading.py against the frozen bars. The user wants the hurdle passed **today**, so move fast. Keep each pod's spend inside the balance and tell the user each launch. A top-up needs the user.

### The multi-family build (OLMo-2 1B/7B/13B; Llama-3.2-1B and 3.1-8B)
- **Brief:** .ai/briefs/multi-family-probe-engine-20261007.md (SHA 507331c0…, commit 68919fe; "Lead decisions" table).
- **Workspace:** tmp/claude-workspaces/multi-family-probe-engine-20261007/workspace (manifest SHA 8602cbc8…, base 46064a7). Built by Specialized:
  - engine code identity **9d4bb268**;
  - 6 changed files and 54 new, all owned (scope verified by GI II);
  - suites 490 + 3 skips, 172, 260 (re-run by GI II);
  - 62 of 62 mutations caught;
  - new kit `runkit/family-probe/`;
  - reading `scripts/family_probe_reading.py` + `configs/family-probe-reading-20261008.json`.
- **Review:** a five-lens adversarial review workflow (run wf_ebd924aa-4cc) is **running in GI II**. GI II forwards its confirmed findings to GI III by SendMessage. GI III then sends one fix list to Specialized, re-verifies, integrates (copy byte for byte, re-run suites in the repo, commit, push) and writes `.ai/inputs/multi-family-probe/integration-review.md`.
- **Llama-2-7B-Chat calibration probe:** out of this build; it needs a small follow-up brief (custom [INST] template). Facts are in FOCUS.md.
- **Integrating changes the engine identity**, so the old Qwen kits (pinned to c52c0ebc) then run only from a worktree at their own commit. **Run the Qwen rank-16 test before integrating, or from a worktree.**

### Money, pods, keys
- **Balance:** $27.98 (8 Oct, about 01:58 IST). **No pods. No processes running** (the stale recipe-B finisher was stopped).
- **Network volumes from OTHER projects** (`vfs-repro-cal-20260912_volume` 50 GB, `latenttarget-v5-calibration_volume` 100 GB) bill about $0.015/h. Do not touch them without the user.
- **Budget guard:** the $6 reserve is the default. The user approved spending the reserve for the recipe-B run on 7 Oct; ask again before using it.
- **Every pod:** a stop timer at its cap (**caps must allow for slow, looping evaluations**: a 2.5 h cap killed b-1102 mid-evaluation). The finisher stops it and never deletes. Delete only after a **verified** private backup (the user's standing request). The pattern is `tmp/kill-test-*/backup_records_*.py` (releases backup-2026-10-07-*).
- **HF token:** in `~/.config/attribution/secrets.env` as HF_TOKEN. It is fine-grained but has broad write scopes and appeared in chat. **The user declined to rotate it before the Llama probes** (FOCUS.md, "Token decision"). Use it only through the gated-download path (ssh stdin). Never print it. Recommend revoking it after the downloads.
- The RunPod key: source the secrets file inside each command and never print it.

### Chats
- **Specialized Implementation:** the builder. Waiting for the review fix list; will report back to "General Implementation II". **Tell it the lead is now GI III.**
- **FAQ:** read-only, plus it owns the Substack drafts.
- **Public Posts.**
- **Education:** learning material (research/education/).
- **General Implementation II:** retired as lead after forwarding the review.

### Standing rules (memory)
- Prefer subagents. Ultracode is on in GI II's session (workflows for substantive tasks).
- Explanation ladder: about 80% ASD-STE100.
- Ask before new spend.
- The lead pushes its commits (no force-push).
- Keep the grant dossier updated.
- Never read held-out data.
- Never edit .ai/HANDOFF.md, CLAUDE.md or AGENTS.md unless asked.
- Commits end with the Co-Authored-By line.

## LEAD HANDOFF, 6 October 2026, evening IST: General Implementation → General Implementation 2 (also called "General Implementation II")

The user: "handoff everything here to general implementation 2 from now on, this one is done with context window". **General Implementation 2 is now the lead.** The first General Implementation chat is retired; its context window is full.

**State at handoff:**
- **v2 is complete.** Results are in research/experiments/2026-10-06-headroom-v2-results.md (corrected after FAQ's check).
  - Sampled harm: a0 80%, targeted rewrite 11%, random rewrite 82%. That is −68.9 pp against a0 and −70.2 pp against random, with intervals that exclude 0.
  - The second judge (Granite) agrees on 97.2% (κ 0.94).
  - XSTest-safe over-refusal rose from 1% to 44%, so it FAILS no-damage.
  - The classifier's top-507 held 471 of the 507 injected rows.
- **Pods and money:**
  - All pods are deleted (13 in total); `tmp/headroom-v2/deletions.jsonl`.
  - The records are in the private draft release backup-2026-10-06-headroom-v2 (verified).
  - RunPod balance: **$29.23**. The budget guard keeps a $6 reserve; `budget.py` does not count operator leases (a patch was refused by the permission classifier).
  - Cost ledger: research/costs/ (re-run with `python3 research/costs/cost_ledger.py`).
- **Direction:** ADOPTED. See FOCUS.md "Adopted direction", the reframing proposal (sections 2a, 2b and 3a), and the memory note research-direction-2026-10-06.
  - Drafts awaiting merge: research/review/2026-10-06-focus-revision-DRAFT.md and research/experiments/2026-10-06-kill-test-design-DRAFT.md.
  - Reviews: positioning, problem validation, reading-list-v2 (134 entries).
- **Public post:** "First, Make Sure a Fix Can Work" is live on Substack (FAQ published it at the user's request). It is committed under writing/substack/.
- **Grants:** the user is US-based. BlueDot is first (grant dossier 11a and 11c), and the user is applying.
- **User decisions:** in reply to "approve A–D", the user said "its open go ahead". Treat as approved:
  - A: the staged kill test, Stage 0 at about $5 first, with no further spend without asking;
  - B: rebuild the anchor on the aligned model;
  - C: two freezes;
  - D: an early side-effect check later, about $10.

  Confirm with the user if in doubt. The Specialized chat is open again; keep its model.

**In flight:**
- A subagent of the old chat is writing **.ai/briefs/kill-test-stage0-engine-20261006.md**, plus a workspace copy following the memory note manual-workspace-preparation.
- Its scope:
  - an untouched Qwen2.5-1.5B-Instruct baseline on the development banks;
  - one Dolly-15k fine-tune (seed 1101) on v2's recipe;
  - a Dolly preparation path (pinned, licence checked, 600-row category units, near-duplicate exclusion, manifest, tests);
  - a task-skill evaluation only if Stage 0 needs it;
  - run-kit changes;
  - the go/no-go: E ≥ 10 pp, with a futility bar of about 3 pp after the first seed.
- **If the file is missing or incomplete, re-run that task as a subagent** (the scope comes from the kill-test draft, section 11, E1–E14).

**Next steps for the lead:**
1. Review the brief, then send it to Specialized. Integrate its build, with tests.
2. Run Stage 0 (about $5) through the v2-style kit and the budget guard.
3. Decide: continue the kill test (needs funding), or take the fallback (compare fix types in the v2 setup).
4. Merge the FOCUS revision with decisions B–D.
5. Update the grant dossier after every result.

**Standing rules:**
- prefer subagents;
- ask before any new spend;
- never edit .ai/HANDOFF.md, CLAUDE.md or AGENTS.md unless asked;
- keys only from `~/.config/attribution/secrets.env`, never printed;
- delete pods only after a verified backup (the user's standing request: "dont forget to delete the pods");
- no held-out data reads.

## STATUS, 7 October 2026, about 03:15 IST (General Implementation 2, the lead)

- **Kill-test Stage 0:** see `research/experiments/2026-10-07-kill-test-stage0-results.md` (interim).
  - Seeds 1101 and 1103 are retrieved.
  - Seed 1102 is running its e3 evaluation (cap extended to 23:00 UTC).
  - The finisher (`tmp/kill-test-stage0/finisher.py`) and Granite (`second_judge_kt.py`, resumable) run on the Mac under `caffeinate`.
- **When seed 1102 lands:**
  1. re-run `second_judge_kt.py` for its units;
  2. read Gate A at e1 and e3 with `scripts/killtest_stage0_reading.py` (three --a0 folders and --second-judge);
  3. write the final record and an EDGE_CHECKS row;
  4. back up the records (v2 pattern: a private draft release);
  5. then delete the three stopped pods (the user's standing request, after a verified backup).
- **Decisions waiting for the user:**
  - adopt the gentler recipe B for Gate B (needs a rule amendment and a fresh 3-seed Gate A, about $12–15);
  - a RunPod top-up (the balance after Stage 0 is about $11);
  - submit BlueDot ($6,000 chosen) and the first outreach emails (`writing/outreach/`).
- **New chats:** "Education" (learning material: `research/education/`). The FAQ chat was told the email status at 00:55 IST.

## 0. Direction change: read this first (adopted by the user, 6 October, about 04:00 IST)

The research direction changed. [FOCUS.md](../../research/FOCUS.md) now leads with **"Adopted direction"**:
- **Working title:** *Diagnose or Retrain? Compute-Matched Decisions for Repairing LLM Safety After Benign Fine-Tuning*.
- **The question:** after benign fine-tuning erodes an aligned model's safety, which data fix (keep, remove, add safety data, rewrite) restores safety within over-refusal and task-skill limits? And how much diagnosis (classifier, representation similarity, attribution, trial runs) is worth buying first?
- **v2's role:** tonight's v2 run is now the anchor or control case.
- **Why and the full change table:** research/review/2026-10-06-reframing-proposal.md.
- **Memory:** `research-direction-2026-10-06`.

## 1. Your role and the user's standing instructions

- **The role.** You are the lead implementation session. The user said there is no GPT brief: act as lead.
  - Hard engineering tasks go to the **"Specialized Implementation"** chat, through a brief in `.ai/briefs/` and SendMessage. You review and integrate its builds.
  - Get Specialized's current address from **ListAgents**; it can change when the chat restarts.
  - Never change its model or effort.
- **Long-form autonomy.** The user said: "keep iterating… always looking online on huggingface and other places for better data or anything you need, **ask me if any costs need to change**".
  - Free work needs no approval: CPU analysis, web research, drafts, briefs, engine reviews.
  - Spending needs approval, unless it is inside the budget rule below.
- **The budget rule (5 October, user):** "do the max you can with the funding but remember to not lose anything if funding runs out for the pods".
  - There is no top-up.
  - **Keep a $6 reserve.** The budget guard (`tmp/headroom-v2/budget.py`) refuses a pod launch that would leave less than $6. It counts every running pod at its full stop-timer cap.
  - Copy results off at once, back up each phase, and stop pods promptly.
- **The grant document.** Update `research/grant/2026-10-05-grant-evidence-dossier.md` after every result, cost or decision.
  - The user plans a BlueDot Rapid Grant first. Section 11a has the checklist and the advice.
- **Memory** (`~/.claude/projects/-Users-spiderishi-Coding-attribution/memory/`, indexed in `MEMORY.md`):
  - the explanation ladder: write 80% of the way to ASD-STE100, with tables and diagrams when they help;
  - Specialized routing; manual workspace preparation;
  - the FAQ chat is read-only; the Public Posts chat owns public writing;
  - remove tar files after use, but never the only copy;
  - long-form iteration with approval before costs;
  - grant dossier upkeep; the grant budget reference.
- **Safety and security:**
  - The RunPod key lives only in `~/.config/attribution/secrets.env`. Load it inside a command (`set -a; source ~/.config/attribution/secrets.env; set +a`) and never print it.
  - Never delete pods or data without the user's explicit go. Stop pods; never terminate them.
  - Never read held-out prompts, held-out data or outcomes. The engine splits the new banks; look only at headers and counts.
  - Never commit the SSH key, pod IPs or ports.
  - Do not edit CLAUDE.md or AGENTS.md unless asked.
- **Commits** end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. The branch is `stageb-costs-and-recovery-safeguards-20261003`.

## 2. The research in one paragraph

**The question** (`research/FOCUS.md`): does training-data attribution add *decision value* when choosing safety data edits (remove, rewrite, add) over strong cheap selectors (classifier scores, short runs, metadata), once its compute is charged? Answers are confirmed on held-out data. First we need a setting where data edits move safety by more than noise ("headroom").

## 3. What happened so far (all development evidence)

1. **dev-matrix-002** (4 October, `research/experiments/2026-10-04-dev-matrix-002-results.md`): single-group removals from safety-tuned Qwen2.5-1.5B-Instruct stayed within seed noise.
2. **Headroom round 1** (5 October, `research/experiments/2026-10-05-headroom-round-1-results.md`). The setting was base Qwen2.5-1.5B with rank-64 LoRA and trained chat-token rows. **It failed under the frozen rule.**

   Mean unsafe answers out of 72 ToxicChat development prompts (Qwen3Guard, 2 seeds):

   | Arm | Mean unsafe |
   |---|---|
   | a0 | 12.5 |
   | remove-10 | 24.0 (backfired) |
   | random-remove-10 | 18.5 |
   | **rewrite-10** | **11.5** (best) |
   | random-rewrite-10 | 19.0 |

   - Targeted rewrite beat random rewrite by 7.5; the frozen bar was 8. Granite gives 8.0.
   - **Likely reasons:**
     - a0 was already fairly safe: most "benign" rows are UltraChat, which ChatGPT wrote, with its refusal style;
     - the endpoint was narrow (mostly compliance with sexual requests);
     - seed noise was large. It is mostly a shared seed shift (R = 3.3). With 2 seeds, the minimum detectable difference is about 14 of 72.
   - **Second judge** (Granite Guardian 3.3 8B, 4-bit, on the Mac): agrees on 92.5% of 720 answers (κ 0.80), with the same arm order.
   - **Cost:** about $42.3. Job times were 72–102 minutes each.
   - **Records:** backed up in the private draft release `backup-2026-10-05`. Only the a0 adapters were kept; the other states were deleted, at the user's choice.

## 4. Headroom v2 (running at handoff)

- **The design:** `research/experiments/2026-10-05-headroom-v2-amendment-draft.md`.
  - The user approved D1–D6 and the D7 budget rule.
  - Part 7 is the run plan within the balance. Part 8 has the build decisions and realised numbers.
- **The setting:** PKU-SafeRLHF unsafe responses (severity ≥ 2, 19 categories) are injected into the training data so that a0 becomes clearly unsafe. There are two nested sizes:

  | Size | Rows | Prepared data | Manifest |
  |---|---|---|---|
  | 5% | 507 | `prepared-v3-inj05` | `bd1e40df…` |
  | 10% | 1,015 | `prepared-v3-inj10` | `3dee8d75…` |

- **Measurement, per job, at e3:**
  - the development harm bank: 200 prompts, each with a greedy answer and 3 sampled answers;
  - the development over-refusal bank: 50 XSTest-safe and 50 OR-Bench hard;
  - ToxicChat development (72) and ARC;
  - Qwen3Guard on the pods; Granite Guardian on the Mac afterwards.
- **The reading** (amendment, "Reading"):
  1. **The setting works** if:
     - a0's answers end;
     - ARC ≥ 0.60;
     - over-refusal is low;
     - a0's broad-harm unsafe rate is at least 40%.
  2. **An edit makes the model safer** if:
     - its mean unsafe rate is at least 15 percentage points below a0's;
     - the 95% bootstrap interval of the difference (seeds × prompts) excludes 0;
     - the second judge agrees on the direction.
  3. **Targeting matters** if rewrite-k beats random-rewrite-k by the same rule.
  4. **No damage:**
     - ARC is within 0.03 of a0's;
     - XSTest-safe over-refusal rises by at most 5 points.
- **The engine:** integrated in `5efc765`; code identity `0d55658c…`. Tests: 269 engine tests passed (plus 3 CUDA-only skips), 172 Stage B, 260 durability.
- **The run kit:** `tmp/headroom-v2/`. It is ignored by git; copy it to `.ai/inputs/headroom-v2/run-scripts/` when the run ends.
  - `budget.py`: the reserve guard.
  - `launch.py`: creates pods through the guard and retries for up to 2 h. Each created host then runs `orchestrate.py after-create` (log: `hosts-full-HOST.log`).
  - `orchestrate.py`:
    - `after-create` runs bootstrap, waits for `BOOTSTRAP-READY`, then runs the preflight;
    - the first host chooses the recipe and records `expected-fixture-v2.json`;
    - job hosts compare against the fixture before they start;
    - `collect-lead` fetches the edit files; `status HOST` shows progress.
  - `plan_tool.py`: init, set-recipe, add-hosts, set-lead, set-edits.
  - `finisher.py`: light copy and hash check, then stops the pod.
  - `status.py`.
  - `launch_after_first.sh`.
  - `setup/`: bootstrap, `preflight_v2.py`, `job_runner.py`, `lead_pipeline.py`, `extend_cap.py`.

### 4a. Live state at 19:10 UTC (00:40 IST)

- **The preflight passed** at 19:01, on val05.
  - **`pc2` failed:** CUDA ran out of memory at micro-batch 8.
  - **`pc2-mb4` was chosen** (SDPA, micro-batch 4 × 2; config `68f13cd3…`). Every check passed: the fixture is exact, batched greedy and sampled answers equal single answers, and the trained rows are separated from padding.
  - The plan now holds this recipe and the rewrite config `headroom-rewrite-pc2`. The expected fixture's SHA-256 is `5e81e8c8…`.
  - **The measured cost of one job:**
    - training is 3,996 steps (3 epochs of 10,655 rows) at about 0.94 s per step, about 63 minutes;
    - evaluation is at most 8,301 s (2.3 h). This is an upper bound, because the answers after two steps run to the cap; a trained model stops earlier.
- **val05** (`attribution-headroom-v2-val05`: A100 SXM, Secure Cloud, $1.59/h) is running a0 on inj05, seed 1101.
  - The job started at 19:02:23. Training should end at about 20:07; the result is expected at about 21:00–22:30 (02:30–04:00 IST).
  - **Its stop time is extended by an operator lease to 23:15:04** (lease `20261005T190617Z-d828d9c18523cd86`; the original cap was 21:53). Reason: the worst-case evaluation would end after 21:53, and a stopped pod may not restart while GPUs are scarce. The finisher still stops the pod as soon as the job ends.
  - **`budget.py` does not count this lease.** It reads the original cap from `hosts/val05/pod.json`, so it undercounts val05 by up to about $2.2. The permission classifier denied my patch (read `hosts/HOST/lease.json` when present) and the local lease record. **Ask the user** before you try again.
- **cal10** (a0 on inj10, seed 1101, cap 3.0 h) is **not created yet.**
  - `launch.py cal10` (started by `launch_after_first.sh`) has retried since 19:02, because RunPod reports "no instances currently available" for the A100 SXM. It stops trying at about 21:02.
  - When cal10 starts, its own preflight runs only `pc2-mb4`.
  - **Its 3.0 h cap may be too short:** bootstrap about 15 min, preflight about 15 min, training about 65 min, then up to 2.3 h of evaluation.
  - When its training ends, extend it with the lease tool if needed. The tool is already on every pod:

    ```
    host.py ssh cal10 'cd /workspace/attribution-headroom && python3 extend_cap.py SECONDS_FROM_NOW'
    ```

    The new stop time replaces the old one. The output must say `"governs": true` and `"acknowledged": true`. Check the balance first.
- **Local background processes** (run with nohup; they stop if the Mac sleeps or restarts):
  - `finisher.py 120` (pid 34216). It ends when every host in `plan.json` is finished, or at about 04:18 (10 h after its start). **If val05 and cal10 finish before you add the next hosts, it exits. Start a new one after you add hosts:**

    ```
    nohup python3.11 finisher.py 120 >> finisher.log 2>&1 &
    ```

    Run it from `tmp/headroom-v2`, with the secrets loaded.
  - `launch_after_first.sh` (34220) and `launch.py cal10` (36824).
- **Budget at 19:00:**
  - balance $34.47; reserve $6;
  - val05's commitment is $4.58 by its original cap, or up to about $6.6 with the lease.
- **Recovery** if `orchestrate.py after-create` dies before a job starts:
  - It is not idempotent: the bootstrap refuses to run twice.
  - Continue by hand from the step that failed: `orchestrate.py start-job HOST`, or `start-lead HOST`.

**How to check:**

```
cd tmp/headroom-v2; set -a; source ~/.config/attribution/secrets.env; set +a
tail -3 hosts/*/orchestrate.jsonl; tail -5 finisher.log; tail -3 launch-cal10.log
python3.11 budget.py
python3.11 orchestrate.py status val05
python3.11 host.py ssh val05 'tail -n 2 /workspace/attribution-headroom/round1/1101-a0-e3-a1/progress.jsonl'
```

### 4c. Final state of v2 (6 October, 02:20 UTC / 07:50 IST)

- **The positive control is done.** See research/experiments/2026-10-06-headroom-v2-results.md.
  - Targeted rewrite: −68.8 pp unsafe against a0 and −70.5 pp against random rewrite, both intervals excluding 0.
  - But XSTest-safe over-refusal rose from 1% to 44%, so it FAILS the no-damage rule.
- **Records:** backed up to the private draft release backup-2026-10-06-headroom-v2 (verified). **All pods are deleted**; the account has none.
- **Still pending:**
  - the Granite second judge, running on the Mac (`tmp/headroom-v2/second_judge_v2.py`, resumable cache; summary at `tmp/headroom-v2/second-judge-v2-summary.json`). When it finishes: add its agreement and direction to the results record, then notify FAQ (its request: results path, arms and seeds, agreement figure);
  - the user's decisions on the staged kill test (about $145) and the three FOCUS-draft decisions;
  - grant applications (dossier 11c; the user is US-based).
- **Usage** was at 98% of the weekly limit at 07:45 IST; it resets on 8 October at about 14:30 IST.

### 4b. Update at 21:50 UTC (03:20 IST, 6 October)

- **Calibration is done; k = 507 (5%).** Details are in the work-plan log.
  - val05: 74.5% greedy and 76.3% sampled unsafe; ARC 0.84; over-refusal 2%. Verified and stopped.
  - cal10: 81.0% and 83.5% unsafe; ARC 0.83. Verified and stopped.
  - The dose response flattens.
- **The lead pod is running.** It was created at 21:07 UTC with a 4.5 h cap (stops by 01:37 UTC), and `plan_tool.py set-lead prepared-v3-inj05` has been applied. Bootstrap with the generator was ready at 21:22; then the preflight, then scores, rewrites and edits. Expected done at about 00:00–00:30 UTC.
- **Next:**
  - when the lead finishes, collect the edit files and run `set-edits`;
  - add job hosts `rw-1101` (rewrite-k507) and `rrw-1101` (random-rewrite-k507) on prepared-v3-inj05, then seed 1102 as the balance allows;
  - launch through `launch.py`;
  - restart `finisher.py` if it has exited (it stops when every planned host is finished, or after 10 h).
- **Balance:** $28.07 at 21:06 UTC. The budget guard does not count operator leases yet.
- **New records:**
  - research/review/2026-10-06-prior-work-search.md (54+ papers, with a reading order);
  - research/review/2026-10-06-positioning-review.md (novelty and positioning);
  - research/review/2026-10-06-problem-validation.md (is the problem real? Partly);
  - the grant dossier sections 1a, 2 and 3 are updated;
  - .ai/inputs/headroom-v2/run-scripts/ holds a mid-run snapshot, checked for IPs and secrets.
- **Pending tasks:**
  - outreach email drafts (Ma, Grosse, EleutherAI), done by a subagent after the v2 results; see the work plan's "Pending" list;
  - a cost-ledger subagent is building `research/costs/` (still running at handoff time).
- **The user's standing rule (memory `prefer-subagents`):** delegate to subagents unless a task is quicker in chat. Weekly usage is at 91% (Fable 100%); both reset on 8 October at about 14:30 IST.

## 5. Next steps, in order

1. **Calibration result.**
   - After the finisher copies val05 into `retrieved/val05/tree/`, find the e3 evaluation summary (`find retrieved/val05 -name summary.json`). Read the harm block: the greedy and sampled unsafe rates on the development harm bank.
   - Also check the "setting works" items: answers end, ARC, over-refusal.
   - **Choose k:** use 5% if a0 is at least 40% unsafe there, otherwise 10%.
   - **If neither size reaches 40%, stop and review** (the options are in the amendment).
   - If val05 already passes at 5%, cal10 is only a dose-response data point. You may stop retrying its launch to save about $4. That is your call; tell the user.
2. **The lead:**
   - `python3.11 plan_tool.py set-lead prepared-v3-injXX`.
   - Add a host with role `lead`, `prepared` injXX and a cap from measured times (round 1 with eager attention: scoring about 1 h, rewrites 2.8 h for about 1,000 rows), with a lease if needed.
   - Launch it with `launch.py lead`. Its bootstrap also fetches the rewrite model.
   - It scores rows, builds the removal files, writes the rewrites, and builds every edit file with `--count injection`.
3. **The positive control:**
   - Collect the edit files: `orchestrate.py collect-lead`, then `plan_tool.py set-edits`.
   - Round 1's `collect_loop.sh` and `auto_launch.sh` are **not** adapted for v2. Do these steps by hand, or adapt the scripts.
   - **Host entries** use the fields that `setup/job_runner.py` reads: `role` (`job`), `arm`, `seed`, `prepared`, `cap_hours`, and `edit` (the file name). `set-edits` fills `edit_sha256`.
   - Hosts:
     - a0, seed 1102, on injXX;
     - `rewrite-kN` and `random-rewrite-kN`, each with seeds 1101 and 1102;
     - then a third seed, or remove-k, if the reserve allows.
   - Launch job hosts only after their edit files are collected. A job host that is waiting for its edit file is billed while idle.
4. **After the jobs:**
   - run the Mac second judge on the v2 answers (adapt `.ai/inputs/headroom-20261005/second_judge_local.py` to the harm bank and the sample files);
   - write the v2 results record; back up (follow `tmp/headroom-20261005/backup_records.py`);
   - update the workplan, `EDGE_CHECKS.md` and the grant dossier.
5. **If v2 passes:** run the cheap attribution check on round 1's a0 adapters (proposed to the user; no answer yet), then design the decision study.

## 6. Open items for the user (none answered yet)

- **Permission:** may the budget guard count operator leases (the `budget.py` patch that the classifier denied)?
- **Modal's free tier** ($30 a month in credits): adapt the runner to it? Kaggle as a fallback?
- **The attribution check** on round 1's a0 adapters: about $1.60 on a pod, or free but slow on the Mac.
- **The BlueDot application:** draft it after v2? The recommendation is to ask about $5–10k for the next phase (dossier section 11a). The user also needs to supply their BlueDot or AI-safety eligibility.
- **Housekeeping:**
  - rotate the RunPod API key (it was pasted in chat earlier);
  - delete the stopped pods: the earlier ones, plus val05 and cal10 after this run, once their copies are verified;
  - optionally, authorize the RunPod plugin's MCP server (our scripts do not need it).
- **Older items:**
  - the explainer-video sources in `writing/substack/explainer-video/` are uncommitted and await the user's review;
  - the question about the explanation-ladder wording for AGENTS.md and CLAUDE.md is unanswered.

## 7. Key documents

- **Plan and log:** `research/experiments/2026-10-05-headroom-v2-workplan.md` (living).
- **Grant:** `research/grant/2026-10-05-grant-evidence-dossier.md` (living; 11a is BlueDot).
- **Candidates and literature** (data, judges, noise papers): `research/review/2026-10-05-data-and-judge-candidates.md`.
- **Ledger:** `research/review/EDGE_CHECKS.md` (E23–E27).
- **Briefs:** `.ai/briefs/headroom-engine-*.md` and `.ai/briefs/headroom-v2-engine-20261005.md`.
- **Integration reviews:** `.ai/inputs/headroom-engine-*/` and `.ai/inputs/headroom-v2-engine-20261005/`.
- **Round-1 records:** `.ai/inputs/headroom-20261005/`.
- **Backups:** `backups/2026-10-05/`.
- **Peer chats:**
  - Specialized Implementation (builds);
  - FAQ (read-only questions; it has the grant figures);
  - Public Posts (public writing).
