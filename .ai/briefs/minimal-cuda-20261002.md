# Minimal CUDA adaptation for the authorized calibration

Task: support the existing minimal_safety experiment on one Runpod NVIDIA GPU. GPT leads, Claude Opus 5.5 exact claude-opus-5-5/max implements, no Claude time/turn cap. This is platform adaptation, not a new scientific study. User authorized Runpod with a $10 total cap; GPT owns cloud operations and secrets. Do not request/read credentials or provision/train/install anything.

Worker scope: only experiments/minimal_safety/model.py, plan.py, tests/test_ms_model.py, tests/test_ms_plan.py, a NEW configs/calibration-cuda.json, and README.md. You are not alone; preserve others' changes. Do not modify HANDOFF or invoke agents/Claude/Codex. No shell commands permitted; GPT runs tests. Use current files in this freshly prepared copy, including the MPS float64-transfer fix and regression.

Context: first real local calibration run completed seed101 a0 short/long training+evaluation, then failed when flat_gradient attempted a combined CPU/float64 transfer on MPS. GPT fixed it to .to("cpu").to(torch.float64); 68 tests pass including actual MPS test. Prior incomplete artifacts are preserved. No removal/seed202 result yet. Local data and model caches are excluded from your copy; not needed. Current scientific scope is research/FOCUS.md, protocol research/experiments/minimal-safety-pilot.md. Existing config is the exact frozen recipe.

First consider two minimal ways to run this task on rented NVIDIA hardware, before editing. Choose the smallest adequate implementation and report why. GPT separately records its alternatives without supplying its preferred design here. Avoid new orchestration infrastructure.

Observable acceptance:
- Explicit CUDA config differs from calibration.json only in identifying name and model.device. Same model/scorer revisions, data, seeds, fp32/eager, LoRA, steps, scorer CPU, 900s/2GiB scientific caps. CUDA model device only 'cuda', single GPU; no fallback.
- Validate config and availability; preserve CPU/MPS behavior. CUDA stage synchronization/memory reporting and CUDA RNG preservation for eval/gradient so evaluation cannot perturb training randomness. Record actual GPU/runtime/precision/determinism configuration in environment evidence. Configure/reject as needed to honor fp32 (no TF32 silently) and deterministic same-input/init control. CUBLAS workspace config must be set before CUDA context use; document external env if needed. Do not claim cross-device numerical equality.
- Relevant tiny tests including hardware-gated CUDA coverage; CPU tests runnable here. Frozen config equivalence regression useful. No model downloads in tests.
- Short README commands/requirements for the explicit CUDA profile and its limits. Existing requirements.lock pins torch2.8.0, transformers4.56.2, peft0.17.1 and pure Python dependencies; preserve scientific library versions. GPT will choose compatible official torch CUDA image and save actual Linux freeze. Do not invent tested Linux compatibility.
- Seed202 short has identical training stream across arms; same-init/same-data checkpoint equality should be verified from real artifact tensors. The calibration cannot establish attribution decision value, novelty, safety benefit or ICML readiness.

Questions to answer: weakest assumption/counterexample; simpler alternative; decisive check; what remains untested. Return changed files, rationale, tests GPT should execute and unverified criteria. Do not overclaim model metadata or effective internal effort.
