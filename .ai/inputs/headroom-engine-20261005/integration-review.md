# Integration review: headroom-engine-20261005

5 October 2026. Reviewed and integrated by General Implementation. Brief: [headroom-engine-20261005](../../briefs/headroom-engine-20261005.md). The worker's report is in [worker-report.md](worker-report.md).

## Scope

- Workspace `tmp/claude-workspaces/headroom-engine-20261005/workspace`, a manual copy at `8dd630c`.
- Compared with the copy manifest: 8 files added, 8 changed, 0 removed. All are inside the owned paths (`experiments/safety_selection/**` and `scripts/cuda_preflight_headroom.py`). Every hash matches the worker's report.
- The repository's versions of the 8 changed files were still the copied originals, so no one else's change was overwritten.

## Checks run here

| Check | Command | Result |
|---|---|---|
| Engine suites, in the workspace | pytest `experiments/safety_selection/tests` `experiments/minimal_safety/tests` | 244 passed, 3 CUDA-only skips, exit 0 |
| Stage B, in the workspace | pytest `experiments/safety_decision_policy/tests` | 172 passed, exit 0 |
| Durability, in the workspace | pytest `experiments/durability/tests` | 260 passed, exit 0 (432 with Stage B) |
| **Independent regression check** | the worker's `removal_digest.run_fixture_matrix`, run against the **original** repository engine (code identity `5165e61d…`) | Reproduces `golden/removal-arms-8dd630c.json` exactly: 6 units, every part, the registry |
| Draft recipe | `config_sha256` and `training_identity` | `4ece3dfd…` and `3bf48731…`, as reported |

The worker's test shows that the new engine reproduces the golden digest. The check above shows that the golden digest is the old engine's. Together they show that group-removal and a0 runs are unchanged on the CPU fixtures. The CUDA path is not covered by this check.

## Code review findings

1. **Fixed here: edit arms were not limited to development.** `run_one` accepted an edit arm on the held-out split with a selector or reference role. The edit file could not name held-out members, but the run would still train an unfrozen edit and evaluate it on a held-out bank.
   - Fix: `validate_job` now refuses an edit arm unless the split is `dev` (an `AccessError` before anything is created or loaded). The module doc and README say so.
   - New test: `test_an_edit_arm_is_refused_on_the_heldout_split`.
2. **Checked, no change:**
   - Generated ids exclude the stop token (`engine.Generation`), so accepted rewrites do not carry `<|im_end|>` into training text.
   - The rewrite generator receives only (row id, request).
   - The edit pool excludes held-out members in the scorer, the builder and the loader.
   - Plans without an edit keep their identity bytes.
3. **For the amendment's review (not engine defects):**
   - The preflight script flags an embedding row only below 0.1 × the median norm. That catches zero rows but not rows left at a random initialisation. A useful extra record is to compare `<|im_end|>` with the never-used padding rows (ids at or above the tokenizer length). The record of log P(`<|im_end|>`) under the seeded adapter is the functional check.
   - The worker's open points 1–8 are listed in its report.

## After the fix

| Check | Result |
|---|---|
| Engine suites, in the repository | 245 passed, 3 CUDA-only skips, exit 0 |
| Stage B | 172 passed, exit 0 |
| Durability | 260 passed, exit 0 (432 with Stage B) |
| Engine code identity | `b1df9a296d3b49c1d775d14ba18c421eba9975666fc22725a34cb718636756a1` (the worker's build was `36ca759c…`; the old engine was `5165e61d…`) |

The identity change means that any continuation or retry of dev-matrix-002 must use the archived engine (commit `8dd630c` or the 4 October backup bundle).

## Integrated files (SHA-256)

| File | SHA-256 |
|---|---|
| `experiments/safety_selection/edits.py` | `b6913c65ec9bebb49b537181d75d533357b5b4f2cc3958d00601fe10f5551f87` |
| `experiments/safety_selection/headroom.py` | `b73840d53a3dc4216d56506df6d89fa0d03c3d5fb48a4a783faa223abe002700` |
| `experiments/safety_selection/config.py` | `36b49e1bb98c4b70ff26dc90c9c43043e67dc2fc8659589170660b9783019210` |
| `experiments/safety_selection/jobs.py` (with the fix) | `8674d183ea65f38fdd4142b8e7d078d2751ee968b7634027549443cb0bc3688b` |
| `experiments/safety_selection/stream.py` | `6445c54b2265bd11bea3cef1660336473f2f7fb79c5f6bf896d180b7421f548a` |
| `experiments/safety_selection/runner.py` | `61d81a92c0da89395c65dbe53a07324ba0fb95dba14e7e3cce7e03c15d2aa258` |
| `experiments/safety_selection/verify.py` | `0ebbaa6ff56babd52819e62b1a7ce8e55a74e88c3f08d49356f539eb79266cf1` |
| `experiments/safety_selection/loaders.py` | `d6e86069c29b3ec62520bb12eb6e085d110a13d448cf3279cbcc4d1cb82c8f0a` |
| `experiments/safety_selection/__main__.py` | `1127bd3108a879fc5aa0a20d74522a58c3921bf19c041578cbfcfd9fb0f39e85` |
| `experiments/safety_selection/README.md` (with the fix note) | `63325b330873bd679e0e12584352b839fbff2d8455836a0079140b3c289c8149` |
| `experiments/safety_selection/configs/study-v3-headroom-base-draft-20261005.json` | `fdbc6e48113dafae5d002def52854afac28ebfbe77e8bef6e1e9399d047023e0` |
| `experiments/safety_selection/configs/headroom-rewrite-draft-20261005.json` | `add68685bed4ce4acc3d6c714fed556012eda0323665101f757cb421441907af` |
| `experiments/safety_selection/tests/test_ss_headroom.py` (with the new test) | `08c2921091e612c2d6e5c4ad18f5ee482789fb65d1bfa2c00c8b493e36354024` |
| `experiments/safety_selection/tests/removal_digest.py` | `58dcc868f4a15bc6a6fd145086ba679f26aa8f8cf29c80d751110b31b57c1896` |
| `experiments/safety_selection/tests/golden/removal-arms-8dd630c.json` | `d9b085bf7fb68014dc10165e6ba4e94a2fd92c34405ef7d24eee052aafb5d5c8` |
| `scripts/cuda_preflight_headroom.py` | `e67019f82aa53914d350a342d8df7735d9b03000999c6ad51d33fc64e8f40cea` |

## Not done

- Nothing ran on a GPU and nothing was downloaded.
- The amendment is still a draft. The recipe and the rewrite configuration are marked DRAFT and authorize no run.
