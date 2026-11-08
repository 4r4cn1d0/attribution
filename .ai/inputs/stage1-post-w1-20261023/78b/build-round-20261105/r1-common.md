# Build round R1 (7-8B kit, blocks A and B): rules every agent follows

You work for the main-study lead (General Implementation XI) of "Diagnose or Retrain?" (repairing LLM safety after
benign fine-tuning; 7-8B tier on OLMo-2-7B and Llama-3.1-8B). R1 is the first round of the block A and B build.

## Paths
- MAIN = /Users/spiderishi/Coding/attribution (branch stageb-costs-and-recovery-safeguards-20261003). READ-ONLY.
- B = /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-epic-ritchie-cc4188/1a199637-2a19-4fac-9cf2-8b00c9c1b5ff/scratchpad/b78
- R = B/reports (reports and scratch). Your worktree WS is named in your brief (a detached worktree of MAIN at HEAD).
- R78 = MAIN/.ai/inputs/stage1-post-w1-20261023/78b ; BR = R78/build-round-20261105.
- PY = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (the main venv, with
  huggingface_hub). PY2 = MAIN/.venv/bin/python. Run Python with -B (and -I for scripts that read records).
- SB = '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'. The 7-8B kit suite and its gated
  mutation runner run under `sandbox-exec -p "$SB"`.

## Read first (they bind you)
1. R78/lead-rulings-ab-build-20261108.md (the lead's build rulings B-1-B-5 and O1-O16; GXB).
2. B/reports/plan-ab.md (the planning scout's plan; your track's section in §2, and the items it names in §1, §4).
   The lead's rulings override the plan where they differ (for example O1 is ruled: steps = ceil(rows / 128)).
3. Part 2 = MAIN/research/experiments/2026-11-06-78b-preregistration-part2.md and its amendment 1,
   MAIN/research/experiments/2026-11-08-78b-preregistration-part2-amendment-1.md (AM1 governs §1 where it differs).
4. R78/lead-rulings-part2-design-20261106.md (DES, all four sets) and R78/lead-rulings-gi-xi-20261108.md (GXI).

## Hard rules
- Write only your owned files inside WS, plus your report and scratch under R. MAIN is read-only (cat, sed, grep,
  git show, git diff, git log). No git state change anywhere (no commit, add, checkout, stash, worktree command).
- In `scripts/scale78b/`, create NEW files only. Never modify an existing file there (scorers_78b.py,
  make_scorer_settings_78b.py, pins_78b.json, PINS-78B.json, SCORERS-78B.md, existing settings or tests) or
  anything under `scripts/stage1/`, `scripts/stage1_s1/` or `runkit/stage1-olmo/`. If a change to an existing file
  seems needed, do not make it: report it as an open point for the lead.
- No pod, spend, network, install, download, agent, subagent or message.
- Never open tmp/hlc/, tmp/hlc-inputs/, tmp/v3-prepared/, tmp/stage1-olmo/, tmp/stage1-mac-runs-20261023/,
  tmp/stage1b/, tmp/scale-78b-*/, tmp/stage1-olmo/retrieved/, any selector.jsonl or hidden/ file, any sealed edit
  file's contents, or any judge output, answer, generation, sample or prompt-text file. Tests use synthetic
  fixtures. From settings, manifests and records print keys, sizes and hashes only. Never mention the side paper.
- If a suite needs a git-ignored file from MAIN's tmp/ (for example tmp/engine-y-34bfd288 for the stage-1 kit's
  suite), copy it into WS's tmp/ with `cp -p`, verify by shasum, and list it in your report. Never copy a forbidden
  folder.
- Run `date -u` in its own command right before writing any time. Every command in the foreground, under 10
  minutes; split long suites or mutation runs into shards. Never end your turn while a job runs; never wait for a
  Monitor or a background notification. Write your report first as a skeleton, then update it as you go.
- Mutation runs: every mutant must be killed by a real test failure; an error (collection error, import error,
  timeout) is an invalid run, never a kill; take the baseline with the same command. You run only short shards;
  the lead runs the full specs as background jobs, so give the exact commands.
- Never invent a number, path, line or citation. Tag claims M (measured; the command), R (path:line), E (estimate;
  basis), I (inference). Plain, short sentences. Do not decide open design questions; list them for the lead.

## Report (your brief names the path)
Sections: status (done / partial / blocked); files created or changed, each with SHA-256; what each item does and
where (R: path:line in WS); tests added (names, counts) and the suite counts before and after (M); mutants added and
the shard results (M); exact commands for the lead's full runs; commands run with exit status; acceptance criteria
(passed / failed / not tested, with evidence); open points for the lead; concerns. Final message: a short summary
with the report path.
