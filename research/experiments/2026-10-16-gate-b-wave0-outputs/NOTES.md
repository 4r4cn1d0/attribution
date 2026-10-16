# Gate B re-costing stop: notes (2026-10-16, before wave 0b ran)

A session hook blocked writes to the main checkout, so these files are in the worktree at
`.claude/worktrees/kind-hawking-a6ce04/tmp/gi-vi-wave0b/recost/`. `recost.py` reads the kit at
`/Users/spiderishi/Coding/attribution/tmp/gate-b-olmo` (or `$ATTRIBUTION_ROOT`).

## Formula (the kit's code; nothing copied)
- `plan_tool.py:487-514` `worst_path_need`: the launches are wave 1 (4 + 4), wave 2 at m = 4 (4 + 4), Granite
  1.5 h, the extension (3 + 3), Granite 1.0 h and the control (4).
- `gateb_rules.py:293-306`: term = spend of the earlier launches + $6 + $1.85 × this launch's caps. Base = the
  largest term. Need = cents(1.25 × base).
- Spend: (42 min + n × 52 min) × $1.79 (`:247-249`); Granite cap × $1.79 (`:281-285`). Caps: `:206-213`.
- Frozen: **base $62.76, need $78.45, contingency $15.69**, as DRAFT:292 and README:70-71 give.
- `recost.py` swaps `POD_OVERHEAD_S`, `SPEND_UPPER_S["arm"]` and `RATE_USD` only inside `funding_need_usd`.
  The caps and guard terms stay the kit's.

## Measured
| | anchor-1 | w0a-1 | frozen |
|---|---|---|---|
| setup (create → job start) | 24.2 min | 16.5 min | |
| finish (job end → stop) | 1.7 min | 2.2 min | |
| billed | 28.0 min, $0.84 | 160.3 min, $4.78 | |
| overhead = billed − job slots | **26.0 min** | 18.9 min | 42 min |
| $/h (`pod.json` costPerHr) | 1.79 | 1.79 | 1.79 |

- Arm slots (`retrieved/w0a-1/tree/job-done/JOB-k.json`, utc → ended_utc): 48.9, **49.0** and 43.5 min. The
  frozen value is 52 min. The process receipts agree within 0.1 min.
- Sources: `create-result.json` and `stops.jsonl` (Mac clock); `job-outer/process-receipt.json` (pod clock).
- Account check: the balance fell $4.87 over w0a-1 ($103.95 → $99.08). The records give $4.86–4.87.

## Choices
- Measured rate = the maximum of the new measurements. The frozen uppers are maxima of measured ranges
  (DRAFT:266), and the stop re-estimates them (DRAFT:310). The report also gives the frozen result and the
  max(measured, frozen) result.
- The caps stay frozen because the guard checks the kit's caps.
- Retrain and diagnostics hours change only the wave-0b pod's spend, not the need.
- Allowances (FOCUS.md:106): $4.00 storage + $3.78 Granite re-launch + $3.70 HarmBench re-launch.

## Result
- Measured need: **$72.43** (base $57.94).
- Projected balance at the wave-1 launch: $99.08 − $0.35 (w0b-1) − $4.62 (w0b-2) − $1.08 (24 h idle) = **$93.02**.
- Required: $83.91 at measured rates, $89.93 at frozen rates. **fits: true**, with $9.11 of slack.
- If w0b-2 bills its full cap, the balance is $89.59: it fits at measured rates but not at frozen rates.
- Break-even points: 60.1 min per arm, 66.7 min of overhead, or $2.11/h.

## New finding
w0b-1 stopped before its job at 00:35 UTC: "transfer or hash check of expected-fixture-gateb.json failed"
(`orchestrate.py:90-92`). It cost $0.35, and it was requeued to w0b-2. It was the first job-role host to get that
file. If the failure is systematic, every later job host fails the same way. From wave 1 on, each failure uses the
contingency.

## Not covered
- The noise-gate report and its σ̂-fallback re-read. σ̂_gate on 2 df.
- P(LOCALIZED) at 10 and 12 pp (FOCUS:74 gives 97% and 100%).
- The seal commit. The fingerprint-trigger re-read (§3).
- A live A100 price (use `--price`).
- The guard's behaviour above $1.85/h.
- A failed pod's own spend from wave 1 on.
- Other spend before wave 1 (`--other-spend-usd`).
- The wave-1 date (`--hours-to-wave1`).
- The arm maximum comes from 3 removal arms. Generation (26–29 min) depends on answer length, so later arms can
  run longer.
