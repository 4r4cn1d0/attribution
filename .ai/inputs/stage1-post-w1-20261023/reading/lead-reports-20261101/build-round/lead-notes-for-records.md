# Lead notes to add when the round-2 records are committed (GI VIII, 1 Nov 2026)

Facts that happened after round 2 (wf_939c9dfc-e93) started, so its drafts cannot hold them:

1. D-6 / track B mutation: the 69-entry near set on a frozen worktree at 53f746d gave 68 killed, 1 invalid
   (B14S-s-p-role-primary-repinned; test_b14_inputs.py's module fixtures world and synth raised at setup, 61 errors).
   Fixed in c21dccb (test file only: fixtures return the failure text, each test reads them through need(), track A's
   pattern); the official runner on that entry: killed, 115 failures, 0 errors; suites 62 and 999 passed. The full
   150-entry spec runs on a frozen worktree at c21dccb (result: 150 killed, 0 survived, 0 invalid; baseline 999 tests; ended 17:40:56 UTC).
2. Kit round 34 mutation: 39 of 39 killed, none unexpected (frozen worktree at 53f746d).
3. Block sim: pod created 14:11:56 UTC, job started 14:47:49 (36 min setup), verified and stopped 14:51:26; pod time
   0.66 h; cost about $1.21 (balance $29.36 -> $28.15); the pod is stopped, not deleted (delete only after a backup and
   the user's yes). similarity.json 811efe4a...; strata.json 2d996a99... (sealed in FOCUS at b5e3c27); B14 inputs
   91baaa53... (binds plan.json b1965c74...: plan.json must not change before the reading).
4. The design's Mac pre-check was run (eval 200; 48 rows in each add set) before the pod.
5. Records/runbook must name the B14 records folder `.ai/inputs/stage1-post-w1-20261023/reading/b14/`
   (strata `b14/strata/strata.json`, inputs `b14/inputs/overlap_inputs.json`).
