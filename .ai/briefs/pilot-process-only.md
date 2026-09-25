# Bounded implementation: process module only

Model claude-opus-5-5, effort max. You are a worker, not the lead. No agents,
Claude/Codex invocation or edits outside your owned files. Others are working;
preserve their files. Work only in the prepared pilot-core/workspace.
Own pilot/__init__.py and pilot/process.py only. Use Write to implement now.
No file reads or shell commands needed; full spec follows. Budget 4 turns/300s.
This is a new narrower assignment after the larger job was interrupted without
files, not a request to resume or repeat that job.

Create a compact typed NumPy implementation (about 150 lines). Public API:
Config (frozen dataclass): family 'A'/'B', phi tuple of K d-dimensional tuples,
targets tuple length K, beta>=0, eta in (0,1], offsets optional defaults0,
mu in [0,1), weight_decay>=0, q optional defaults e1. Convert inputs to immutable
tuples; check finite values and dimensions. A requires d=1. q must have norm1.
State (frozen dataclass): theta tuple, momentum tuple, counter integer>=0.
initial_state(config,theta): zero momentum/counter. Config/state dimension checks.
probs(config,state): stable softmax(beta*phi@theta+offsets).
apply_event(config,state,action,weight=1): gradient A=theta-target[action],
B=(phi[action]@theta-target[action])*phi[action]. m'=mu*m+weight*grad;
theta'=(1-eta*weight_decay)*theta-eta*m'; increment counter even if weight0.
weight must be finite in [0,1]. successors returns all K apply_event outcomes.
score(config,state): stable sigmoid(q@theta).
intervention_pair(config,pre_state,action,alpha=1): (suppressed,ordinary) weights
(1-alpha,1) with alpha in [0,1]. No randomness inside these functions.
canonical_config(name,beta,eta,**optional): A1 phi=(-1,0,1), targets=(-1,0,1);
A2 same phi targets=(0,1,-1); A3 targets=(1,0,-1).
B1 phi=((1,0),(0,1),(1,1)/sqrt2),targets=(1,-1,.5).
B2 phi=((1,0),(1,.2)/sqrt1.04,(1,-.2)/sqrt1.04),targets=(-1,0,1).

No simulator or tests yet. Explain in <=150 words what files you wrote, the
weakest numerical assumption, and any validation not run. GPT checks the files.
