# SR-2's error-rate simulation: the full run and the lead's reading (GI XI, 8 Nov 2026)

Recorded 2026-11-08T19:11 UTC by General Implementation XI. Part 2 §10.3 (DES K6; DESO3 V2), with the lead's build
rulings S-1 to S-10, R-10 to R-13, R-27 and R-28 (`78b/lead-rulings-ab-build-20261108.md`). $0, on the Mac, from
Track S's worktree (detached at `3481d85`) with the files that merge in R1 (M: the outputs' own hash fields):
`scripts/scale78b/sr2_simulation.py` `0ff5e54596a144d6cd4d3643ce83bc14bd21ebc9ea80b2416ebab645fd29fe89` and
`scripts/scale78b/settings/sr2_simulation.json` `c6f0c81e418e4efe8f876655621bbb1dbfa51ca91aa88a335a812e53eaa04b88`
(the reading rule written into it before this run; no full run before this one). 20,000 replicates per row, seed
7820261108, 9 σ_pair values (3 to 8.24 pp), 5 scenarios (none; arm × seed at shares 0.5 and 1; Llama's σ at 3/2 and
2/3 of OLMo's), both families under [B], OLMo-2-7B under [C], the full design (no anchor stop is known). Nine shards
per option ran at once and were merged (`run.sh`; 18:30-19:10 UTC; every exit 0, `summary.txt`).

| Option | Largest familywise rate (U claims; Holm at 5%) | Where | Refused contrasts | Reading |
|---|---|---|---|---|
| [B] (`sr2-B-full.json`, `671f64a74dc037ec…`) | **0.05145** | σ_pair 5.5 pp, Llama's σ at 2/3 of OLMo's, OLMo-2-7B's family | 0 | not above 6% |
| [C] (`sr2-C-full.json`, `21738afc70689bf4…`) | **0.05175** | σ_pair 4.0 pp, arm × seed 0.5, OLMo-2-7B | 0 | not above 6% |

**The lead's reading (DES K6):** no simulated familywise rate exceeds 6% at any σ or scenario, under either option,
so SR-2's simulation trigger is passed: SR-2 stands on the full design, with the size printed above. SR-2's other
trigger (ruling 3; P1 §6.4) is unchanged: the kit's block-A record-done must print no block-A U value and
`blinded_sigma.py`'s byte-for-byte test must hold, verified before block A's first pod (K2's half is still to be
built). If an anchor stop becomes known before block A's first pod, the simulation runs again on the reduced design
and that run's reading governs (GXB S-10).

**Non-converged REML fits.** The outputs count 262,336 ([B]) and 145,571 ([C]) cluster fits whose REML reached its
iteration cap without meeting the tolerance (about 7% and 8% of the fits, E: 20,000 × 9 × 5 × families × 2 clusters).
The simulation uses such a fit's last estimate, which is what B16's real reading does: B16 adds a note ("the REML
stopped at … steps without meeting the tolerance") and does not refuse (R: `scripts/stage1_s1/reading/reading.py:603-604`).
So these fits are part of the simulated procedure, not a fault in it.

Limits (stated in the outputs): the prompt part of the claim test's SE is omitted (no prompt data before block A);
Φ's adverse O and L words are not simulated (the rate is the U claims'; R-10, R-11, R-27); N's σ_eval,0 is the 1B
value 1.28 pp (it reaches only N's printed plan); seed effects are zero; H is read as H (b) covered.
