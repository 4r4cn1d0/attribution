# Exact calculator and core tests

Task: authorized step 2. Model claude-opus-5-5, effort max. Worker, not lead:
no agents, Claude/Codex, publications or unrelated edits; others are working.
Use the current prepared pilot-core/workspace. Own only pilot/exact.py,
pilot/tests/test_core.py and pilot/README.md. Budget 8 turns/900 seconds.
Read pilot/process.py once, then implement. No research-document reads needed.
Allowed command: /Users/spiderishi/Coding/attribution/.venv/bin/python -m pytest -q pilot/tests

Implement terminal_law(config,post_event_state,H): exhaustively enumerate K^H
future paths, each transition using its own state-dependent probs and apply_event
at weight1. H=0 uses the supplied state. Return leaves (path,mass,state,score),
mass, mean and second moment using math.fsum, and actual operation counts.
No rounding or state merging. Validate H and finite numerics. Attribution takes
pre-event state/action/alpha, creates intervention_pair and enumerates each world
independently; returns suppressed minus ordinary mean and both laws. The event's
original action probability is metadata, not a multiplier on conditional Delta.

Tests: H0/H1 manual formulas; 3^H leaves/mass1; alpha0 delta0; immutable state;
invalid inputs; weight0 still decays momentum/weight and advances step. Fixture:
theta=.2,m=.3,mu=.9,eta=.1,decay=.1 -> m=.27,theta=.171 with w0.
Independent 50-digit mpmath H2 reference for A1 and B1 (do not call production
probs/update in the reference), beta3,eta.4,pre theta=.2 for A1 or (.2,-.1) for
B1,observed action2 (zero-based),alpha1. Compare means/delta <=1e-10.

README: installation with requirements-pilot.lock, APIs and H/sign/intervention
semantics. Do not implement couplings or run a benchmark here. Return files,
actual checks and statuses, weakest assumption and remaining concerns concisely.
