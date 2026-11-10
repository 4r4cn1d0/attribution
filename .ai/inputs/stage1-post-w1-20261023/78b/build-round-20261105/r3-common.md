# Build round R3 (7-8B kit, blocks A and B): rules every agent follows

You work for the main-study lead (General Implementation XII) of "Diagnose or Retrain?" (repairing LLM safety after
benign fine-tuning; 7-8B tier on OLMo-2-7B and Llama-3.1-8B). R3 is the third round of the block A and B build:
K3 (the kit's runner and pack) and Track P (the padded-tokens tool and three small fixes), in parallel.

## Paths
- MAIN = /Users/spiderishi/Coding/attribution (branch stageb-costs-and-recovery-safeguards-20261003, HEAD d7eb772).
  READ-ONLY.
- B = /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-goofy-jennings-12ae35/2e006469-731b-4a21-8c98-93331af24388/scratchpad/b78
- R = B/reports (your report and scratch). Your worktree WS is named in your brief (a detached worktree of MAIN at
  d7eb772).
- R78 = MAIN/.ai/inputs/stage1-post-w1-20261023/78b ; BR = R78/build-round-20261105 (every earlier round's reports
  and briefs, and plan-ab.md).
- PY = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (the main venv).
  PY2 = MAIN/.venv/bin/python. Run Python with -B (and -I for scripts that read records).
- SB = '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'. The 7-8B kit suite, the scale78b suite
  and their mutation runners run under `sandbox-exec -p "$SB"`.

## Read first (they bind you)
1. R78/lead-rulings-ab-build-20261108.md (the lead's build rulings, all 19 sets; GXB). They override the plan.
2. BR/plan-ab.md (the planning scout's plan; your track's items as your brief names them).
3. Part 2 = MAIN/research/experiments/2026-11-06-78b-preregistration-part2.md and its amendment 1,
   MAIN/research/experiments/2026-11-08-78b-preregistration-part2-amendment-1.md (AM1 governs §1 where it differs).
4. R78/lead-rulings-part2-design-20261106.md (DES, all four sets) and R78/lead-rulings-gi-xi-20261108.md (GXI).

## Hard rules
- Write only your owned files inside WS, plus your report and scratch under R. MAIN is read-only (cat, sed, grep,
  git show, git diff, git log). No git state change anywhere (no commit, add, checkout, stash, worktree command).
- Never modify anything under `scripts/stage1/`, `scripts/stage1_s1/`, `runkit/stage1-olmo/` or `experiments/`. In
  `scripts/scale78b/`, create new files only, except the files your brief names as owned. If a change to any other
  file seems needed, do not make it: report it as an open point for the lead.
- No pod, spend, network, install, download, agent, subagent or message.
- Never open tmp/hlc/, tmp/hlc-inputs/, tmp/v3-prepared/, tmp/stage1-olmo/, tmp/stage1-mac-runs-20261023/,
  tmp/stage1b/, tmp/scale-78b-*/, tmp/stage1-olmo/retrieved/, any selector.jsonl or hidden/ file, any sealed edit
  file's contents, or any judge output, answer, generation, sample or prompt-text file. Tests use synthetic
  fixtures. From settings, manifests and records print keys, sizes and hashes only. Never mention the side paper.
- If a suite needs a git-ignored file from MAIN's tmp/ (for example tmp/engine-y-34bfd288 for the stage-1 kit's
  suite), copy it into WS's tmp/ with `cp -pR`, verify by shasum, and list it in your report. Never copy a forbidden
  folder.
- Run `date -u` in its own command right before writing any time. Every command in the foreground, under 10
  minutes; split long suites or mutation runs into shards. Never end your turn while a job runs; never wait for a
  Monitor or a background notification.
- **Usage is short this round.** It runs on the last part of the week's usage. Read only what you need (grep and
  `sed -n` ranges, not whole large files); run the full suite only when it can tell you something new; keep mutation
  shards short. Write your report first as a skeleton (status, items, next steps), then update it after each item,
  so the lead or you can resume if the round is cut off.
- Mutation runs: every mutant must be killed by a real test failure; an error (collection error, import error,
  timeout) is an invalid run, never a kill; take the baseline with the same command. You run only short shards;
  the lead runs the full specs as background jobs, so give the exact commands.
- In zsh, quote globs in options (`--include='*.md'`) and never start a word with `=` (`echo =====` fails).
- Never invent a number, path, line or citation. Tag claims M (measured; the command), R (path:line), E (estimate;
  basis), I (inference). Plain, short sentences. Do not decide open design questions; list them for the lead.

## Report (your brief names the path)
Sections: status (done / partial / blocked); files created or changed, each with SHA-256; what each item does and
where (R: path:line in WS); tests added (names, counts) and the suite counts before and after (M); mutants added and
the shard results (M); exact commands for the lead's full runs; commands run with exit status; acceptance criteria
(passed / failed / not tested, with evidence); open points for the lead; concerns. Final message: a short summary
with the report path.
