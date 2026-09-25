# Pilot: exact attribution and coupling headroom

`pilot.process` defines the deterministic learning process (softmax policy, momentum SGD
with decoupled weight decay, sigmoid readout). `pilot.exact` computes, by exhaustive
enumeration, the exact law of the terminal score and the exact conditional attribution of
one observed event. Neither module draws random numbers.

## Installation

Use Python 3.11 or newer. From the project root:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-pilot.lock
.venv/bin/python -m pytest -q pilot/tests
```

`requirements-pilot.lock` pins exact versions (numpy, scipy, mpmath, pytest and pytest's
dependencies) without hashes. mpmath is used only by the tests' 50-digit reference.

## API

`pilot/__init__.py` does not re-export `pilot.exact`; import it directly.

| Name | Meaning |
| --- | --- |
| `terminal_law(config, post_event_state, H)` | `TerminalLaw` of `score` after `H` further events |
| `attribution(config, pre_state, action, alpha, H)` | `Attribution` of the observed event `(pre_state, action)` |
| `TerminalLaw` | `horizon`, `leaves`, `mass`, `mean`, `second_moment`, `operations` |
| `Leaf` | named tuple `(path, mass, state, score)` |
| `Attribution` | `delta`, `suppressed`, `ordinary`, `action`, `alpha`, `action_probability`, `operations` |
| `OperationCounts` | `probs`, `apply_event`, `score`: process calls actually executed |

```python
from pilot.exact import attribution
from pilot.process import canonical_config, initial_state

config = canonical_config("A1", beta=3.0, eta=0.4)
result = attribution(config, initial_state(config, [0.2]), action=2, alpha=1.0, H=2)
result.delta, result.suppressed.mean, result.ordinary.mean, result.action_probability
```

Process functions used (see `pilot/process.py`): `Config`, `State`, `canonical_config`,
`initial_state`, `probs`, `apply_event(config, state, action, weight=1.0)`, `score` and
`intervention_pair(config, pre_state, action, alpha=1.0)`.

## Semantics

- **Horizon.** `H` counts the future events *after* the attributed event; the attributed
  event itself is not counted. `terminal_law` enumerates all `K**H` action paths (actions
  are zero-based; leaves are in lexicographic path order). Every transition uses `probs`
  at its own current state and `apply_event` at weight 1. `H = 0` returns the supplied
  state as the single leaf `((), 1.0, state, score(state))`.
- **Intervention.** `attribution` calls `intervention_pair(config, pre_state, action,
  alpha)`: the suppressed world applies the observed event at weight `1 - alpha`, the
  ordinary world at weight 1. Only the gradient is scaled: momentum decay, weight decay and
  the counter increment still happen at weight 0, so `alpha = 1` removes the event's
  gradient but not its optimiser step. `alpha = 0` makes the worlds identical and
  `delta == 0.0` exactly. The two worlds are enumerated independently (no coupling).
- **Sign.** `delta = suppressed.mean - ordinary.mean`, i.e. E[score after H | suppressed]
  minus E[score after H | ordinary]. Positive `delta` means suppressing the event raises
  the expected terminal score (the event lowered it); negative means the event raised it.
- **Conditioning.** `delta` is conditional on the observed event having occurred.
  `action_probability = probs(config, pre_state)[action]` is reported as metadata only and
  is never multiplied into `delta`.
- **Numerics.** A leaf's mass is the product of float64 probabilities along its path.
  `mass`, `mean = fsum(mass * score)` and `second_moment = fsum(mass * score**2)` use
  `math.fsum` and are not renormalised, so `mass` (1 up to rounding) checks the
  enumeration. There is no rounding, pruning or state merging. Invalid `H`, config, state,
  action or alpha raise `TypeError` or `ValueError`; non-finite logits or results raise
  `FloatingPointError`, and `State` rejects non-finite parameters with `ValueError`.
- **Cost.** A `terminal_law` call makes one `probs` call per internal node
  (`1 + K + ... + K**(H-1)`), `K + ... + K**H` `apply_event` calls and `K**H` `score`
  calls, and holds all `K**H` leaves in memory; there is no size cap.
  `Attribution.operations` adds the two `intervention_pair` updates and the metadata
  `probs` call to both laws' counts.

## Paired baselines and oracle

`pilot.couplings` implements independent, fixed-label common-uniform, ordered
common-uniform, maximal-agreement, shared-Gumbel, and full-update-distance
transport couplings. `pilot.pair` computes their paired moments and a Bellman
co-adapted oracle. A separate terminal-OT calculation is a noncausal lower bound.
The oracle enumerates pair histories without rounding or merging states.

Run a single canonical cell from the project root:

```sh
.venv/bin/python -m pilot.headroom --structure B1 --beta 8 --eta 0.4 --theta0 0.4 --action 2 --alpha 1 --H 2
```

The command emits JSON containing marginal truth, all six paired methods, the
oracle, terminal lower bound, measured operation counts and construction times,
numerical diagnostics, and correctness checks. Exit 0 means the checks passed.
Canonical cells support H 0–4; larger horizons are rejected before enumeration.
Actions are zero-based and H counts events after the attributed event.

`gap_estimate`, `max_gap_estimate` and `suboptimality_estimate` are float64
numerical diagnostics, not certified error bounds. Plans are checked without
clipping or normalization and their matrices have immutable backing. Ordering
checks use a fixed tolerance; a large gap estimate cannot relax them. Variance
ratios are omitted when the best ordinary variance is at most 1e-14.

The frozen grid and its hash are in `research/pilot/headroom-manifest-v1.json`.
The verification scripts in `tmp/pilot-implementation/` preserve every attempted
cell and record censored/unrun cells, source hashes, and CPU/RSS accounting.
Oracle variance headroom measures an opportunity, not practical speed or novelty.
Deterministic marginal enumeration has variance 0 and is reported separately from
the paired-coupling ratio.

Measured results and the prespecified stopping decision: [implementation results](/Users/spiderishi/Coding/attribution/research/pilot/IMPLEMENTATION_RESULTS.md).
