# Non-author implementation review — 12 October 2026

GPT reviewer Turing read the actual worker/operator, protocol, six recipes and
new RunPod helpers. Static review only; no tests, agents, pods or spend by the
reviewer. Analyzer author Sagan is a different worker; this role separation does
not establish independent error processes. GPT implementation is authorized by
the user's current task-specific exception while Opus5.5/max is quota-blocked.

## First pass and fixes

1. Nonzero retrieval could leave the operator successful. Fixed: retrieval and
   extraction must succeed; batch model/engine/protocol and outer exit0 must match.
2. Retrieval could postpone operator shutdown indefinitely. Fixed: separate
   process group, at most1800seconds and before the existing cap minus30seconds;
   timeout terminates the transfer group and reaches confirmed-stop handling.
3. Failed-create orphan stops could remain unconfirmed while the suffix advanced.
   Fixed in both new helpers: persist unresolved IDs, block suffix/reconciliation
   and retry those stops in operator cleanup. Historical helpers are unchanged.
4. A new pod could vanish from commitments before the API list showed it. Fixed:
   durable local causal-pod records remain committed until a confirmed local stop,
   deduplicate against API IDs; unknown active prices refuse admission.
5. Worker exceptions could bypass batch finalization. Fixed: exception-safe failed
   batch receipts and progress persistence; hard container kills may leave only
   progress and prevent analysis.
6. Setup hash was not consumed. Fixed: actual archive and setup receipt are checked
   against the frozen setup digest before launch.

Additional lead fixes: one operator lock per kit and refusal of an already ended
attempt or existing pod prevent duplicate invocation from stopping an active first
attempt. The exact nonsecret helper sources and receipts are archived under
`operator-kit/`. All actual recipe hashes and helper/payload pins are refreshed
after the fixes. Targeted re-review accepted the worker/operator, new kits and
analyzer for freeze and launch under the declared caps. No remaining concrete
launch or primary-analysis blocker was found. One nonblocking exception-path
overwrite of an existing batch receipt was corrected before the freeze.

Actual checks were static inspection, source syntax, recipe validation and file
hashing only. No software test suites were run. The remaining feasibility
assumption is completing and retrieving all six units within the fixed caps;
failure gives an incomplete block and blocks primary contrasts.

Objective reconstruction is a consistency check of logged losses against logged
per-example values and audited target counts. It does not independently establish
the gradient computation. Cross-engine numeric equivalence is not claimed; this
fresh block uses one unchanged engine and does not pool historical results.

Lead dry-run caught a Python module-name collision before any launch: operator.py
shadowed the stdlib operator module. The administrative file was renamed
pod_operator.py; its logic was unchanged. The prelaunch freeze was superseded
and recorded before any study outcomes.
