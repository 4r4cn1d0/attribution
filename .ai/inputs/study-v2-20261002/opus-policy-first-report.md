I've written the Stage B package and the draft protocol, but I have not run anything. My tools were read, search, edit and write only, so no test, CLI command or GPU job was executed and every check below is untested. Nothing in the Stage A engine or `minimal_safety` was modified.

**Files** (all new; nothing else touched):
- `experiments/safety_decision_policy/`: `__init__`, `__main__`, `README.md`, `common`, `outcomes`, `tfidf`, `features`, `ridge`, `policy`, `costs`, `config`, `development`, `backend`, `synthetic`, `controller`, `analysis`
- `configs/example-engineering.json` (marked ENGINEERING EXAMPLE ONLY, `freeze: false`) and `configs/example-dev-fit-spec.json`
- `tests/`: conftest plus `test_dp_{tfidf,outcomes,ridge,policy,features,config,controller,engine,analysis}.py`
- `research/experiments/safety-selection-v2-decision-protocol.md` (draft)

**Commands and evidence:** no commands run, so there are no exit statuses and no evidence files. All acceptance criteria are not tested. Each item from the brief's test list has a matching test; `test_dp_engine.py` drives the real engine API on the engine's CPU test fixtures.

**How it works, in brief:**
- **Policy:** ranking, the acquisition schedule and the choice rule are pure functions shared by both methods. The full purchase plan depends only on quotes, so it is fixed before any full run executes. Failures and overruns never trigger re-planning.
- **Shared runs:** each artifact is always produced by the same operation, whichever policy buys it. A run both policies need executes once but is charged in both ledgers. The continuation at z0 counts as one observation, never a second seed.
- **Final runs:** they are refused unless a choice lock file exists with a matching hash. The controller and both backends check this.
- **Records:** every derived record is write-once, so a resumed block that computes anything different is refused.
- **Uncertainty:** no zero-width intervals. The approximate t interval is withheld for one block or zero spread. A Hoeffding bound for outcomes in [−1, 1] is always reported.

**Decisions of mine you should confirm or overrule:**
1. Utility ties containing the answer count as unresolved in [0,1]. The brief only specified intervals for safety and refusal.
2. Normalized violation is the *sum* of the two scaled excesses.
3. Predictors learn the adverse (upper) endpoint of each full-minus-a0 change.
4. The proxy rule is the smallest sum over targets of cross-validated loss divided by target variance. Freezing enforces the record's lambdas and proxy, so both methods get identical tuning; the short checkpoint stays your choice.
5. X0 must contain the six TF-IDF features, all short-run observations with explicit unresolved rates, and at least one static, one guard and one label-score feature.
6. Training quotes are linear in seed-independent example counts, with a fixed quote per evaluation.
7. The config states the four rules verbatim but omits the catalogue and TF-IDF definition hashes, because I couldn't compute them by hand. The policy code pin covers both.
8. The one-extra-purchase sensitivity is "the schedule's next purchase if the budget allowed one more step". It runs before the lock and stays out of S-'s ledgers.
9. Final costs are split into the chosen arm's deployment and the a0 reference run. The engine's evaluation-stage seconds are reported alongside.

**Weakest assumption:** that the unresolved-item intervals at the full checkpoint are narrow relative to real safety effects.

- **Counterexample:** if an edit's unresolved safety fraction exceeds its true safety gain, the adverse safety change is above zero. Then both policies keep a0 in every block and Y is 0 by construction, whatever attribution knows.
- **Settling test:** in development, compare the distribution of full-checkpoint interval widths with the observed paired differences before freezing.

**Simpler alternative:** a held-out-group predictor ablation alone (no budget policy). Rejected, as the brief says, because it can't answer the costed decision.

**Unresolved concerns:**
- If a fresh-start run is killed without the engine writing `error.txt`, the engine's registry blocks retries. The attempts then run out, and you would need to intervene by hand.
- Replay seeds are only checked against the development record's seeds; you must also avoid any other calibration seeds yourself.
- Run one block per process, or later blocks show no measured setup cost.
- Fitting needs numpy 2.2.6. The engine test runs about 35–40 tiny CPU jobs.

**Minimal command sequence** (prefix each with `python -m experiments.safety_decision_policy`):
1. `pytest -q -rs experiments/safety_decision_policy/tests` (run with python directly)
2. `simulate`
3. `pins`, then `relevance`, then `dev-table`, then `dev-fit`
4. Write a new frozen config, then `freeze`
5. `run-block --block b`, once per block
6. `analyze`, then `verify-study`

Full flags are in the README.
