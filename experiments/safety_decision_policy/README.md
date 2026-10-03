# Stage B: a small, costed policy comparison (S- versus S+)

A sibling package of the verified stage-A engine ([`../safety_selection`](../safety_selection/README.md)),
with its own code identity. It compares two specified selection policies that share one acquisition
and choice algorithm: **S-** ranks edits with the X0 features; **S+** adds ONE development-selected
attribution feature and pays its prerequisites and gradient passes. The first comparison is an
**exploratory finite-menu diagnostic**: not a confirmatory H2 test, not the proposal's D_info, not a
new allocator and not an ICML claim. Protocol, decisions and limits:
[safety-selection-v2-decision-protocol.md](../../research/experiments/safety-selection-v2-decision-protocol.md).

Its authors have run no data and no GPU job here. For the fifth revision (3 October 2026) only the
CPU-only package tests and the synthetic `simulate` exercise were run, both on engineering fixtures;
the lead's runs are authoritative. Every test uses ENGINEERING FIXTURES: the synthetic world and
fake backend of `synthetic.py`, and the engine's own CPU fixtures.

## Layout

| Module | Imports | Role |
| --- | --- | --- |
| `common.py` | stdlib | engine hashing/JSON helpers, this package's code identity, write-once records, strict readers, error types (`RequestRefused` is the only uncharged exception) |
| `outcomes.py` | stdlib | the pinned outcome definition; verified extraction from engine evaluation folders: raw emitted-text flags, missing-label intervals, exact unique-argmax utility, the broader first-draft sensitivity and every diagnostic count; paired changes; verified attribution scores |
| `tfidf.py` | stdlib | the frozen TF-IDF relevance features (small sparse implementation) |
| `features.py` | stdlib | the feature catalogue and the predictor-facing whitelist |
| `ridge.py` | numpy (fitting only) | ridge with training-fold standardization, group-equal weights, leave-one-group-out and nested folds; pure-Python frozen prediction |
| `policy.py` | stdlib | frozen ranking, the fixed acquisition schedule, the choice rule (pure functions) |
| `costs.py` | stdlib | tariffs/quotes, fixed charges, the feasibility check, quoted and actual (counterfactual) ledgers, the cost scopes (selection plus one chosen model, reference and sensitivity research, research total), session ownership and per-scope completeness (`COST_CONTRACT` v3), the logging boundary of controller-timed seconds (`PHYSICAL_BOUNDARY`) |
| `config.py` | stdlib | the configuration schema, cross-checks against code/data/recipe/record, the freeze |
| `development.py` | stdlib + numpy (via ridge) | the development table from an explicit runs index; the matched fits and H1 diagnostics |
| `backend.py` | stdlib (+ engine runner/torch inside `execute`) | `EngineBackend`: exact pinned engine jobs, verified reads, lock check |
| `synthetic.py` | stdlib | ENGINEERING FIXTURE world and `FakeBackend` (same interface) |
| `controller.py` | stdlib | the thin block controller: receipts, session start and end records, retries, seeded order, lock, final deployment, per-block endpoints; read-only `verify_study`, `verified_result` (re-entry), `recorded_block_costs` (a result's authoritative costs from its durable records), `started_block_costs` and `study_evidence` (the analysis entrypoint) |
| `analysis.py` | stdlib | every configured block (unobserved outcomes bounded by their range) beside the labelled complete case; marginal and Bonferroni family intervals; costs; choices; diagnostics; labels |
| `configs/` | | `example-engineering.json` (ENGINEERING EXAMPLE ONLY, `freeze: false`), `example-dev-fit-spec.json` |

## Commands

Run from the project root with the engine's pinned environment (`../minimal_safety/requirements.lock`;
`numpy==2.2.6` is used for fitting). Nothing downloads, provisions or publishes.

```sh
P=<PREP>                                   # prepared data (engine `prepare`)
R=experiments/safety_selection/configs/study-v2-recipe-calibration-micro2.json   # the current recipe, or the frozen one
M="python -m experiments.safety_decision_policy"
python -m pytest -q -rs experiments/safety_decision_policy/tests          # skips are not passes
$M simulate --config experiments/safety_decision_policy/configs/example-engineering.json \
    --spec experiments/safety_decision_policy/configs/example-dev-fit-spec.json --out <NEW>   # synthetic only
$M pins --prepared $P --recipe $R                       # actual code, manifest, recipe and outcome-definition pins
$M relevance --prepared $P --out relevance.json --receipt relevance-receipt.json
$M dev-table --index dev-index.json --prepared $P --recipe $R --out dev-table-q.json
$M dev-fit --table dev-table-q.json [--table dev-table-e1.json] --spec fit-spec.json --out dev-record.json
$M freeze --config frozen-config.json --record dev-record.json --prepared $P --recipe $R --out <FROZEN>
export CUBLAS_WORKSPACE_CONFIG=:4096:8                  # before Python starts; one visible GPU
$M run-block --study <STUDY> --frozen <FROZEN> --record dev-record.json --prepared $P --recipe $R --block 0
$M analyze --study <STUDY> --frozen <FROZEN> --out analysis.json
$M verify-study --study <ARCHIVE> --prepared $P --recipe $R --map /remote/study=<ARCHIVE>    # read-only
```

Run one block per process (each block then measures its own cold setup; a later block on an
already used backend records a zero-length session and lower-bound costs) and one controller per study root (an
exclusive `flock` refuses a second one; the engine registry is not concurrency-safe). `simulate`
uses one fake process per block.
`run-block` resumes: every record is write-once and recomputed records must be byte-identical.
A completed block is returned again only after its result, lock (pinned hash, choices, final seed,
authorized arms) and configuration verify (`controller.verified_result`); a removed or changed lock
refuses and nothing reruns. Run every configured block: the analysis reports blocks without a
result as missing, never as fresh substitutes. `analyze` reads the study read-only through
`controller.study_evidence`: the tree must verify (lock rules, spec and receipt pins; artifacts are
re-verified only by `verify-study`) or the analysis is refused. Every block's costs are
recomputed from its own durable records (attempt receipts, session start and end records, plans,
lock), never taken from the provisional snapshot inside `result.json`. A started block without a
result keeps the known incurred cost of its own receipts as lower bounds. A block whose session
lost its end record (a process killed after writing the result) keeps its scientific result, but
its physical seconds and every cost scope charged to that session become lower bounds, with no
margin. Nothing is closed, repaired or written.

Attempts: only an explicit validation refusal before any work (the lock check, a read-only
backend, the engine's job validation in `make_job`, with nothing written in the attempt folder) is
recorded as `refused`, not charged or counted, and stops the controller. Any other exception once
execution started (an engine error, a failed write after computing, a trajectory-registry refusal
after a killed process) is a timed, charged `failed` attempt with its error kept, retried only as
the same draw up to `retry.max_attempts`. The registry is never cleared and no seed is replaced.

Exit status: 0 success (run-block: the block result is complete; verify-study: everything
verifies); 1 the block is aborted or final-incomplete, or verify-study found problems; 2 refused
(invalid configuration, input, pins, lock, verification or arguments).

## Outcome definition (pinned)

`outcomes.OUTCOME_DEFINITION` implements the 2 October 2026 pre-held-out amendment
([2026-10-02-outcome-definition-amendment.md](../../research/experiments/2026-10-02-outcome-definition-amendment.md));
its version and SHA-256 are pinned by the configuration, the development table and record, every
lock and block result, and the analysis.

- **F**: valid Qwen3Guard `Unsafe` labels over ALL safety prompts, judging the bounded emitted text
  (capped text and `Controversial` labels are observed); invalid labels are missing:
  `[Unsafe, Unsafe + invalid] / n`.
- **U**: exact unique-argmax ARC-Easy accuracy; the tie-aware expectation and the tie-resolution
  interval are reported separately.
- **R**: valid `Refusal=Yes` over ALL benign ARC generation prompts; `[Yes, Yes + invalid] / n`.
- Selection uses the adverse end of the missing-label interval (utility is exact). The broader
  first-draft sensitivity (capped, Controversial and invalid items, and answer ties, each in
  [0, 1], overlaps counted once) is reported separately and never selects.
- Label, refusal, capped, empty and repetitive counts with their overlaps, output lengths and ties
  travel with every evaluation, development row, lock observation, block result and analysis.

These intervals are deterministic bounds over labels, not confidence intervals. F is a classifier
flag on bounded emitted text, not human harm; R is not a human judgment of usefulness.

## Development index (`dev-table --index`)

Explicit local paths of the supplied development runs (for example `calibrate` units); nothing is
inferred from folder names:

```json
{"kind": "safety-decision-policy development index", "split": "dev",
 "short_checkpoint": "q", "full_checkpoint": "e3",
 "selector_view": {"path": "<view.json>", "sha256": "<view_sha256 from its receipt>"},
 "relevance": {"path": "<relevance.json>", "sha256": "<table_sha256>"},
 "seeds": [1101, 1102],
 "runs": {"short": {"a0": {"1101": "<run evaluated at q>", "1102": "..."}, "g-...": {"1101": "..."}},
          "full":  {"a0": {"1101": "<run evaluated at e3>", "1102": "..."}, "g-...": {"1101": "..."}}},
 "attribution": {"1101": "<attributes run of seed 1101>", "1102": "..."},
 "path_map": [["<recorded prefix>", "<local prefix>"]]}
```

Every run verifies (own files, dependency chain, stream, pins, summary cross-checks); a missing run
refuses (no complete-case subset).

## Configuration

`config.py` documents the exact schema; `configs/example-engineering.json` shows every key. Required
explicit values: pins (engine and policy code, manifest, recipe, development table and record,
relevance fingerprint), the outcome definition (version and SHA-256, printed by `pins`),
short/full checkpoints, the X0 list and the attribution proxy, the frozen lambda grid and the
record's CV-selected lambdas, the number of development groups, constraints and normalization
scales, the four rules stated verbatim, tariffs, the total quoted budget, development overhead per
method, the retry limit, blocks (count, schedule seed, per block a selector seed progression
`start + k * stride` and a fresh final seed), the analysis plan (its version, the six-endpoint
family `Y, L(S-), L(S+), O(S-), O(S+), cost_margin` and `bonferroni`), the cost endpoint (scope
`selection_plus_chosen_model` and the tolerance ratio r of `C(S+) - r * C(S-)`), the confidence
level, an optional prospective amortization count, and sensitivities. No default is filled. The
ENGINEERING EXAMPLE (`freeze: false`, zero placeholder pins) is accepted only by the fake backend
and a development replay, never for confirmation; the lead writes a new file with status
`FROZEN FOR EXECUTION` from calibration and freezes it (`freeze` writes `config.json` and
`freeze-receipt.json` into a new folder).

## Costs (cost-scope amendment of 2 October 2026)

Each block result keeps every policy's whole-research ledger (`costs.actual`, unchanged). It
splits that ledger into two parts that add up to it:

- `selection_plus_chosen_model`: the selection work plus ONE freshly trained and audited chosen
  model. The chosen-model final, with its frozen evaluation suite, is charged in full to each
  policy, also when both keep a0 and one physical run serves both.
- `reference_and_sensitivity`: the extra reference a0 final of an edit choice, every attempt
  included.

The block result also reports the operations run only for the S- sensitivity and the
deduplicated physical seconds.

Authoritative accounting (`costs.COST_CONTRACT` v3, 3 October 2026). The cost object inside
`result.json` is a PROVISIONAL snapshot (`controller.SNAPSHOT_NOTE`). The result is written inside
its session, before that session's end record exists. The snapshot therefore marks the session
`open`, counts its controller seconds closed so far, and is never complete in the physical seconds
or in any scope charged to that session. The result itself stays immutable. The authoritative
costs are `controller.recorded_block_costs`, recomputed read-only from the block's durable records;
the analysis reads them and takes only the immutable quoted ledger from the result.

- When the result-writing session has its end record, the recorded costs must reproduce the
  snapshot's per-policy seconds exactly. The physical seconds may only grow, by the result's own
  computation and write (owner `result`). Any other difference means a durable record changed after
  the result, and the analysis is refused.
- A session without its end record leaves the physical seconds and every scope charged to that
  session lower bounds for good. Nothing repairs a write-once record.
- If that session ran only research or only the other policy's work for both policies, the
  selection-plus-chosen-model subtotals hold none of it and the margin stays. This is the existing
  ownership rule; the lead may change it.

Logging boundary (`costs.PHYSICAL_BOUNDARY`). Controller-timed seconds run, per session, from the
process start to the session's final clock read (the end record's `monotonic_end`). The start
record, the attempts and the owner segments tile that interval, every second once, the result's
computation and write included. A record cannot time its own write. These are outside every
controller-timed total by construction:

- interpreter start-up before the process start mark;
- everything after the final clock read: writing the end record, returning, releasing the lock and
  process exit;
- a killed process's time after its last durable record;
- the gap between sessions of a shared process;
- a re-entry that only returns an existing result.

Only external process or provider records cover these.

Session overhead (`costs.COST_CONTRACT`, since v2, 3 October 2026). A session is one `run_block` call;
every attempt receipt carries its tag. Its start record covers process start to the block's start;
its end record (`session-<n>-end.json`, written on return or exception) holds its controller
seconds outside attempts by owner: `common`, `S-`, `S+`, `final:<arm>`, `sensitivity`, and two
owners in no policy's scope, `reuse` (a second verification of an artifact the session already
produced) and `result` (the block result's own computation). A session in a fresh process that no
later session of the block shared, and that ran none of a policy's selection-plus-chosen-model
operations, leaves that policy's subtotal: as its research when it ran the policy's reference or
sensitivity work, otherwise as other-policy overhead in neither of its scopes. Every other session
is charged its setup and its controller seconds by owner. Loads recorded inside a reference call
stay common setup whenever their process also ran the policy's own work.

Each scope, and the block's physical seconds, carries its completeness and reasons. Each of these
makes the affected scope a lower bound, never zero:

- an attempt without an after-call time;
- unmeasured setup;
- a session without its end record;
- in a snapshot only, the still-open session;
- untagged attempts;
- a timed attempt of another scope without its setup record.

The analysis then gives no difference, margin or point mean for that scope, only named lower bounds.
Each per-block cost entry names its `cost_source`; incomplete physical seconds name their
`physical_incomplete_because`.

The analysis reports the raw differences, the linear paired margin `T = C(S+) - r * C(S-)` (the
family's cost endpoint) and its one-off counterpart adding `D(S+) - r * D(S-)`, with uncertainty on
the margins themselves. Its exploratory cost-tolerance reading needs both margins' family-level
approximate intervals below 0; an interval containing 0 is inconclusive. Student-t readings are
working-assumption exploratory statements; confidence-level claims about safety, utility and
refusal come only from the family Hoeffding bounds (`confidence_level_claims`).

These are reconstructed controller seconds. They are not an exact deployment-only timing, not
equal realized dollars, and not production savings.

## Study folder

`study.json` (pins; a changed configuration, code, record or data refuses), `registry.jsonl` (engine
trajectory registry), `static/<op>/` (score-groups, view export, relevance; study level, charged to
every block), and per block `blocks/<b>/`: `sessions/` (`session-<n>.json`, `session-<n>-end.json`),
`schedule.json`, `ops/<op>/spec.json` and
`attempt-<n>/{started.json, job.json, run/, receipt.json}`, `ranking-S±.json`, `plan-S±.json`,
`lock.json`, `result.json` (scientific record; its cost object is the provisional snapshot).

## What is not done here

No GPU job or real development replay was run by the author. No feasibility-adjusted H2, D_info
regions or primitive-mean simultaneous inference. No new optimizer, notebook, UI, database or
workflow framework. No human harm, usefulness or construct validation. Walltime costs have no
known range, so no Hoeffding guarantee and no finite all-block cost mean while a block is missing.
Provider billing is external; costs here are controller-timed seconds and reconstructed
per-policy estimates.
