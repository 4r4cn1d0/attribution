# Side Project missing-probe recovery — 12 October 2026

## Scope and authorization

User: “whatever couldnt run run those”, referring to the 11 failed representation
probes after the completed training and judge runs. GPT lead performs operator
work with the original finished units and unchanged scientific probe. No training,
recipe substitution, deletion or publication was performed. Main Gate B remains
paused at its completed anchor, consistent with the user's Side Project priority.

## Recovered by 06:00 UTC (11:30 IST)

Five additional probes are complete; coverage is 18 of 24 units:

- `sp-llama32-1b-b-1103`: Constant Llama-1B seed 1103.
- `llama32-1b-g-1103`: Scheduled Llama-1B seed 1103.
- `sp-llama31-8b-1102`: Constant Llama-8B seed 1102.
- `sp-olmo2-7b-1103`: Constant OLMo-7B seed 1103.
- `sp-olmo2-7b-g-1102`: Scheduled OLMo-7B seed 1102.

Each downloaded adapter was re-hashed and matches the original Mac state,
downloaded pod state and the probe-computed adapter hash. Stop confirmations are
in the corresponding operator logs. Evidence:
`tmp/sp-repr/resume-20261012/verified-recovered.json`; raw results and adapters:
`tmp/sp-repr/out/<host>/`. The frozen paper still reports its original 13 probes.
No newly recovered probe effect values were used to choose a mechanism hypothesis.

## Six pending units

Original-machine GPU capacity refused:

- `llama32-1b-g-1102`.
- `sp-llama31-8b-g-1102`.
- `sp-llama31-8b-g-1103`.
- `sp-olmo2-7b-g-1103`.

No container runtime or SSH after bounded starts:

- `olmo2-1b-1102`.
- `olmo2-1b-g-1101`.

RunPod CLI reports the latter two as `initializing/awaiting_container`, rather
than a running container. Both latest retries ended with confirmed stops. System
log reads timed out without events; this does not diagnose the underlying cause.
The documented CPU-only GraphQL resume was attempted on Llama-1B Scheduled 1102
and also returned the GPU-capacity error. The pod remained stopped with gpuCount=1.
The console offered only a login page; the user was asked to sign in for the
console data-recovery/migration option. No migration or termination was performed.

## Budget and queue

The original $8 total GPU allowance is retained. Prior attempts, including the
canary, had a conservative elapsed-cost upper bound of $4.2817 at $1.85/hour.
The manifest continuously adds elapsed-cost upper bounds for starts and reserves
the full maximum billing window for active attempts; capacity refusals cost zero.
Do not infer per-pod actual charges from account balance changes, which include
storage. Account started at about $37.51; all original pods cost $1.79/hour.

`tmp/sp-repr/resume-20261012/retry_capacity.py` is an administrative launcher around
the unchanged `restart_probe_pull.py`. Reviewed and launched: four hours maximum,
two concurrent capacity retries, at least ten minutes between attempts for each
host, 12-minute initial cap plus at most 12 minutes after SSH, $0.74 reservation
per attempt at $1.85/hour. Repeat only the explicit no-free-GPU refusal. A paid
post-start failure is left for investigation; an unconfirmed stop halts the queue.
Budget exhaustion or deadline also ends it. Scientific code is never edited.

The first detached driver launched at 06:05:39 UTC (PID 89790) but ended before
any operator output. Both reserved pods were checked EXITED before releasing
those stale reservations. The queue was relaunched as active exec session 49414
at approximately 06:08 UTC (11:38 IST), with process receipt `queue-process.json`
and log `capacity-queue.log` in the manifest directory.
Conservative GPU spend upper bound before this queue: $5.84754 including earlier
recovery attempts; $2.15246 of the $8 allowance remains. A non-author GPT static
review identified and the lead fixed uncertain-start cost accounting, premature
reservation release on unconfirmed stops, and persistence of paid-failure pauses
and cooldowns across restarts. The re-review found no remaining launch blocker
for the confirmed-stopped state. The queue's no-spend dry run and frozen hashes
were checked. No repository tests were added or run.

Queue status, attempts and cost reservations are in
`tmp/sp-repr/resume-20261012/manifest.json`; operator logs are named
`<host>-attempt<number>.log`. Frozen hashes were checked unchanged:

- Runner: `abdba0911f83939bb3e7b101b28f6fc8436da2cfd094f312e7af3eefc335d593`.
- Probe: `727ce99302926c65e28898e561dd4e44af6a62f8b8cf41b92deb6eed8b577a10`.
- Queue: `d91b549850f5fd20bea337259c30053d515ca5ee71d4691cf6b88e9f4d0ab6c2`.

## Scientific question

The larger-model training runs did finish and produced useful evidence. The
Scheduled-versus-Constant OLMo/Llama interaction was inconclusive at 7–8B; this
neither identifies a causal size effect nor establishes a reversal. The 7–8B
half-LR Constant comparison reduced mean erosion in both families, but does not
identify why the bundled Scheduled recipe differed across checkpoints. Three
seeds per main cell and two Llama half-LR seeds limit precision. Native model
releases, training-engine identities and loss/schedule changes must be separated
before claiming a mechanism. A non-author GPT reader checked these distinctions.

Next causal study is a proposal only: loss-weighting × LR-treatment factorial
within fixed checkpoints, including a constant LR matching the schedule's exact
discrete average; one pinned engine/data/serialization, randomized execution,
independent training-seed blocks, prespecified replication based on an effect
of interest, and held-out safety/over-refusal/utility outcomes. A refusal-feature
claim additionally requires a validated intervention with matched random-feature
controls. Current representation separation is not a validated causal refusal
feature. No such new training or intervention has been run.

A concrete serialization audit was also identified. The current OLMo-7B config
uses the pinned OLMo-1B tokenizer, and the loader/codec use that tokenizer's chat
template. The publisher documents a different initial BOS convention for native
OLMo-7B versus OLMo-1B. Verify the exact pinned templates before an intervention;
this is a candidate modifier, not evidence of the cause of the observed pattern.
Both existing OLMo-7B recipe arms used the same chosen tokenizer. Preserve their
records and evaluate a native-serialization control as a separately registered
study, rather than silently replacing inputs or claiming these runs failed.
Sources: [OLMo-1B model card](https://huggingface.co/allenai/OLMo-2-0425-1B-Instruct),
[OLMo-7B model card](https://huggingface.co/allenai/OLMo-2-1124-7B-Instruct).

Mechanism literature consulted: [Qi et al., shallow safety alignment](https://arxiv.org/abs/2406.05946)
and [Arditi et al., refusal directions](https://arxiv.org/abs/2406.11717). These
motivate controlled tests; neither establishes the mechanism in our checkpoints.

## Addendum — 12 October, approximately06:49 UTC

Scheduled Llama-8B seed1102 also completed. Its adapter hash matches the original
Mac state, downloaded pod state and probe identity; stop was confirmed. Coverage
is19/24. Three capacity failures remain in the queue, and two OLMo-1B containers
await console recovery. GPU-spend upper bound is$6.14354, including prior attempts.
`tmp/sp-repr/resume-20261012/verified-recovered.json` is updated.

The causal setup audit resolved the serialization question above: selected and
native tokenizer hashes match at the pinned revisions, including the BOS template.
Current publisher cards differ from these recorded files. A native-versus-selected
tokenization correction is not warranted. The suspicion is retained as history,
not an unresolved known defect.

## Addendum — 12 October,10:35 UTC

Scheduled Llama-1B seed1102 completed at09:45 UTC on capacity attempt24.
The lead independently re-hashed the180,386,768-byte downloaded adapter:
`457a63d722b7f421f4071d8826d1c8ddbebb65e4bf000fe80ce8f7eaafa170c0`.
It matches original Mac state, fetched pod state and probe identity. Pod stop
was confirmed09:45:41 UTC. Coverage is now20/24. The four-hour retry queue ended
10:07:56 UTC; it is no longer active. Two original-machine capacity failures
remain (OLMo-7B Scheduled1103, Llama-8B Scheduled1103), together with the two
OLMo-1B container failures listed above. No pod/volume was deleted.
GPU-spend upper bound$6.27664 of$8, no active reservation; allowance remaining
$1.72336. Account balance and this elapsed-cost upper bound are different records.
The frozen paper13-probe summary is unchanged. No causal mechanism is inferred
from this recovered representation result.
