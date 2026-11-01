# Gate B kit (runkit/gate-b-olmo)

The run kit for Gate B on OLMo-2-1B: it plans the waves (`plan_tool.py`), launches and drives each pod (`launch.py`,
`orchestrate.py`), pulls and finishes them, and backs up the records (brief gate-b-engine-kit-reading-20261008, Part B).

## Operator rule ([D16] 8)

A stopped kit pod is never restarted. A requeued host's jobs run only on its replacement.

`plan_tool.py requeue HOST` moves the stopped host's jobs to another host in plan.json (for wave 0a's first host it
also moves the recorded expected fixture aside and clears the reference), so the stopped pod no longer owns them.
A host whose jobs were moved can no longer record the expected fixture or set the reference (`orchestrate.py`
record_first and `plan_tool.py set-reference` refuse it).

## A requeue never follows a failed or unknown stop ([D17] 3)

`orchestrate.py` logs `pre-job-failed` (with its step) only when the pod says the job did not start; when the pod
cannot say (an ssh exit other than 0 or 1), it logs `job-start-unknown`. Either way it stops the pod and logs
`pre-job-stop` with the stop's exit (1 when host.py could not confirm EXITED).

`requeue HOST` accepts the log alone only when the last `pre-job-failed` names a step other than `start-job` and a
later `pre-job-stop` has exit 0. Otherwise (a failure at `start-job`, a failed stop, an unknown job start) the
operator first checks the pod's status with `host.py get HOST` and, once it shows EXITED, runs
`plan_tool.py confirm-stopped HOST`, which records it in operator-actions.jsonl, bound to the current
orchestrate.jsonl; then `requeue HOST` runs.

## The guard record is part of the environment ([D17] 4)

`plan_tool.py record-done` of the host that completed R_1101 copies that unit's pulled guard record into plan.json's
reference. Before it does ([D19] 4), it compares that guard with the same host's own preflight guard (the pulled
`retrieved/HOST/tree/PREFLIGHT-DONE.json`) and refuses, with plan.json unchanged, on any difference (the message names
the host and the differing guard fields) or when that preflight guard is missing; wave 0b cannot be planned until the
lead resolves it. The preflight check compares each later pod's guard record (PREFLIGHT-DONE.json) with it, and
`requeue --rerun-mismatched` accepts an arm unit whose guard record differs (reported as `guard`, as the reading
reports it). `--rerun-mismatched` refuses a hash named twice, and refuses once a later wave (or ext, lc) is planned.

## Anchor text in backups ([D14], copied here by [D17] 10)

The private draft-release backup may hold `anchor-*/anchors.json` (private repository, draft release, non-commercial
research under PKU's CC-BY-NC). D10's rule keeps the text out of git commits, not out of private backups.

## At most 4 arms per pod ([D21])

`gateb_rules.MAX_ARMS_PER_POD` (default 4; the user confirms the value at the freeze, DRAFT revision 5 §12) caps
every pod. `plan_tool.py init-wave` splits waves 1, 2, ext and lc into ceil(n / MAX_ARMS_PER_POD) pods, the arms dealt
as evenly as possible in the given order (`gateb_rules.pod_sizes`: 8 -> 4 + 4, 6 -> 3 + 3, 4 -> 4; this even split
is the pre-registered one, [D21] (4): the DRAFT follows the kit); each pod's cap
comes from its own jobs (B4). The pods of one wave are launched together (`launch.py HOST HOST ...`); the budget guard
counts each running pod at its full cap, so a pod starts only when the guard allows. The wave-1 funding need counts
every later launch of the worst path split the same way: at $1.79/h spend and $1.85/h at the guard, with Mac Granite,
it is $72.85 (1.25 x $58.28; [D22]: the factor is 1.25, was 1.15, which gave $67.02). `defer` and `requeue` move jobs to an unlaunched host of the same wave only when it has room; else
to a new host. A pre-job requeue from wave 1 on is paid from the contingency as one unit (one 42 min plus each job's
spend upper; $7.46 for a 4-arm pod of the $15.69 contingency at the default, so it pays two such stops in full on the pod-Granite route; on the Mac route the $14.57 contingency pays one 4-arm stop and 3 arms of a second).

When the contingency is short ([D21] (3)): a unit costs exactly what its jobs cost one by one
(`unit_rerun_cost_usd` is the sum of `pay_reruns`' costs, the 42 min on the first), so the two agree whenever the
unit fits; when it does not fit, the one-by-one rule governs: each moved job in order is paid if its cost fits what
is left (the 42 min on the first job paid), and the rest are reported not re-run.

## Pod or Mac Granite in the funding need ([D21] (5))

`gateb_rules.GRANITE_ON_POD` chooses where Gate B's Granite files come from: True (the default since [D22], the
user's 9 Oct decision; the Granite parity PASS is recorded in FOCUS) = the judge pod; False = the Mac, and the need
is the $72.85 above. With True, `worst_path_need` adds one pod Granite judge launch after
wave 2 and one after the extension (not after wave 1 or the length control), each its own launch. Each judges the
200 greedy answers of every Gate B arm completed since the previous pod Granite launch (after wave 2: R_1-R_3, wave 1
and wave 2, 19 arms; after the extension: 6 arms) plus the known-answer gate's 200, and is capped by the judge
launcher's rule (scripts/gate_b_mac_judges/pod/README.md at 2694bd0: the smallest half hour of at least 30 min +
0.5 s per answer + 15 min, at least 1 h, at most 6 h): 4,000 answers -> 1.5 h, 1,400 answers -> 1.0 h. Its term
counts cap x $1.85 at the guard, and its upper spend in the later terms is cap x $1.79. The wave-1 need is then $78.45
(1.25 x $62.76; the last term 58.2848 + (1.5 + 1.0) x 1.79 = 62.7598), with a $15.69 contingency. The contingency
pays arm re-runs only; a repeated judge launch is not paid from it. The pod Granite launch after the length control
(its 4 arms and the gate: 1,000 answers -> 1.0 h) is not a term, since [D21] (5) names the mid-path launches only,
and it would not bind: the spend through the length control, 4 x 7.4583 + 2.685 + 2 x 5.907 + 1.79 + 7.4583 =
53.5807, + $6 + 1.85 x 1.0 = 61.4307, below 62.7598. If the launch after wave 2 judged only the verdict's 10 arms
(2,200 answers, still 1.5 h), the 13 arms left after the length control (2,800 answers -> 1.5 h) give 62.3557, also
below.
