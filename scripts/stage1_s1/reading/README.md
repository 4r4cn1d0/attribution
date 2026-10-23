# scripts/stage1_s1/reading: B16, the stage-1 confirmatory reading

New files only. numpy and the standard library; the one import from the committed tree is `scripts.stage1.dose_axis`
(pure, for the token axis). Nothing here draws a random number, opens a network connection or reads a data file on its
own: `python -m scripts.stage1_s1.reading --input tables.json --out reading.json` reads one text-free input document
and writes one output document (canonical JSON, never overwriting).

**Specs.** REV3 = `research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-DRAFT-rev3.md`
(sections 1.2-1.3, 2.1-2.3, 3, 4, 5.3, 6.4-6.7), every [LEAD-NEEDED] item at the recommended ruling of
`lead-rulings-needed.md` (LN-01, LN-02, LN-05, LN-08, LN-12, LN-15b, LN-20, LN-21, LN-22, LN-35, LN-36, LN-37, LN-38);
AMD = the analysis-model draft (sections A, B, D, E, F); the statistics review (ST items) and its scripts as cross-checks.

## Modules and the rule each implements

| Module | Rule |
|---|---|
| `settings.py`, `settings/reading.json` | the settings pinned by `SETTINGS_SHA256`; the sealed designs (plan A = D1, "block A only", plan B), contrasts, delta, tau_O, tau_L, floors, the REML stop rule, the graph's weights, the texts (REV3 1.2-1.3, 3.2, 3.5, 4.2, 4.4, 6.4-6.7) |
| `schema.py` | the one input schema; anything else is refused (arms and seeds equal the sealed design; the O endpoint may hold a subset of R's seeds, LN-12) |
| `tdist.py` | Student t tails and quantiles (regularized incomplete beta), Welch df |
| `reml.py` | HB-C and HB: one variance per arm by REML, Fisher scoring on log sigma^2, start at each arm's residual mean square, the endpoint's floor, stop when the largest step among the arms above the floor is below 1e-6 or after 25 steps (REV3 3.2; AMD A.3; LN-35); the two-arm cluster by the sum rule (REV3 3.5); the information on the sigma^2 scale (AMD A.4) |
| `contrast.py` | the paired-mean estimator, the seed part, the crossed item part, Satterthwaite df, tests and intervals (REV3 3.1-3.2; AMD A.2-A.5); LN-20's theta0 form and cross-cluster paired form (REV3 3.6); the forms of S-a, S-aW, S-b2x, S-p, S-A8 |
| `phi.py` | the graphical family Phi with exact fractions: weights, the LN-05 edge F_k -> L_k 1, the update, the sequential rule, local levels, IUT nodes, Holm; plan B's graph (REV3 4.1-4.3; AMD B.2-B.3; LN-21) |
| `labels.py` | equivalence grades, the U part with the note (MSG-09; LN-36), feasibility states (REV3 6.4), the coherence screen's flags (REV3 3.7), the headline word's partition (REV3 4.6), the separation rule (REV3 4.9) |
| `sensitivities.py` | HB, S-a (with its equal-variance flag), S-aW, S-b2x, S-0, S-G, S-p, S-tok (LN-38), the fits per cluster (REV3 3.4) |
| `references.py` | "m beats r", the adapter-scaling curve matched on L with the revised switch, dominance (family 1b), the 3-seed fallback (REV3 5.3; AMD D.1-D.4; LN-15b) |
| `reading.py` | the whole reading: fits per endpoint, the nodes' p-values, Phi, per-arm states, label rows, headline words, sensitivities, references, the best feasible repair, the actor menus (LN-08) |

## Readings the input may name

- `plan_a`: D1 (a0 and R at 1101-1107, six method arms at 1102-1107; 50 cells), P1-P6, the familywise grade at alpha/6 per side.
- `plan_a_block_a_only`: block A alone (a0, R at 1101-1104; method arms at 1102-1104); every cell carries "block A only (3 seeds per method arm)" and the planning MDE at Phi's start level is printed per contrast.
- `plan_b`: P1, P3, P6; R at 1101-1110, A1, H1, S1, S4 at 1102-1110, a0 at 1101-1107 outside the fit; the two-arm cluster {S1, S4} by the sum rule (P6 = the paired t on 9 pairs, 8 df, plus the item part; no split printed); the a0 parts by the paired form on 1102-1107; the familywise grade at alpha/3 per side.

## What the output holds

`fits` (per endpoint and cluster: the arm variances, arms at the floor, iterations, convergence, residual df),
`arms` (means, restoration G_m, the O states at tau_O = 2, 5, 10, the L state, the coherence screen), `contrasts`
(U_k, O_k's two parts, L_k's two parts, F_k; estimates, SEs, df, intervals, p-values), `phi` (the rejections in order with
the local level each was tested at, the start and final levels as exact fractions), `rows` (the five parts of REV3 4.6
and the headline word), `sensitivities`, `references` (per repair and reference; family 1b), `best_feasible_repair`,
`actors`, `notes`, and a provenance block (settings pin, module hashes, input hash, Python and numpy versions).

## Tests and mutation

`tests/`: the settings pin and designs; t quantiles against table values; REML (recovery at many seeds, the score
against finite differences, the fit as the maximum, the information against the mean observed Hessian, the two-arm
rule, the floors and the stop rule, the cross-check against the planning routine); the item part and Satterthwaite's
hand case; Phi's levels against `phi_levels_check.py` and `phi_planb_check.py`, the largest reachable levels of the
statistics review, Holm equivalence, order independence; one test per case of REV3 4.6's partition and the review's
420-state enumeration; every sensitivity's estimate; the whole reading under plan A, block A only and plan B; the schema's
refusals; the references with the fallback; the command line.

Run: `PYTHONDONTWRITEBYTECODE=1 <venv python> -B -m pytest -q -p no:cacheprovider --basetemp=<scratch> scripts/stage1_s1/reading/tests`
from the workspace root. Mutation: `mutation/run_mutants.py --spec mutation/mutants_b16.json --scratch <outside the
workspace> --report <file> [--only id,id]` (the same rules and format as `scripts/stage1/mutation/run_mutants.py`).

## Implementation notes for the lead (also in the build and fix reports)

1. **The floor as an active set, now a pinned setting.** The planning routine (AMD SIM `reml_hetero`) solves one Fisher
   step for every arm and floors afterwards; at its fixed point the free arms' scores are not zero when an arm is floored
   (about half of all D1 fits). This code removes a floored arm whose score points below the floor from the step and
   solves the free arms' own block, so the fixed point is the REML maximum subject to the floor. The choice is
   `reml.floor_mode` in the pinned settings: `"active_set"` (built; the two verify passes measured it near nominal and
   about 0.4 points more liberal at 5% than the planning form, whose sizes the statistics review printed) or
   `"planning"` (the review's form). Changing it changes the pin. Without a floor event the two agree. **The lead rules.**
2. **The stop rule after a floor event (verify-stats F1).** A step in which an arm newly reaches the floor never ends the
   fit: the free arms' steps were computed with that arm still free, so a sub-tolerance largest step said nothing about
   the new fixed point (in about 11% of plan-B three-arm L fits the first build stopped with a free arm's log-score up to
   0.99). The fit now goes on; every converged fit satisfies the KKT condition on the free arms (tested). This is a
   reading of LN-35's text ("the largest step among the arms above the floor"); the 1e-6 and the 25 steps stay.
3. **25 steps.** Fisher scoring converges linearly; in 15-25% of synthetic D1 fits the largest step is still above 1e-6
   at step 25. The fit record says so (`converged`), and the notes carry it. The rule is implemented as written.
4. **Exact ties at delta (verify-stats F2).** U shares are k/3, so a paired mean can equal 5 pp exactly as a rational
   while its float lands 1e-15 below it. Every comparison of the estimate with delta reads through
   `margin.tie_tolerance_pp` (1e-9 pp, pinned); interval ends (irrational) do not.
5. **Readings the record should state** (verify-stats N3): LN-12's O comparator part on the R seeds present, "not
   tested" below 3; the S-a equal-variance flag from the S-a and S-aW Phi runs' rejection sets; under plan B, S-a and
   S-b2x pool a0 as well (a0 is outside the HB-C fit, but S-a is "pooled over the arms"); the two-arm cluster's sum is
   floored at one floor, not twice it (verify-stats N2).

## What the fix pass added (22-23 Oct 2026; notes/b16-fix.json)

S-a's O and L tests (REV3 3.4; Welch comparator parts, LW-33's theta0 part, their own Phi run); the seed-only value
"on these prompts" beside every O number and state (REV3 3.6, 6.6); the per-actor best data arm at tau_O 2, 5, 10 and
tau_L (REV3 4.9, 9.4); the 4 pp margin as a reported sensitivity (REV3 4.4); the text "below the bank's resolution";
every number the code used to hold twice now read from the settings (alpha, the interval level, the REML stop values,
the floor mode, the bounds' one-sided level); a coherence-failing repair's D_k carries p = 1 and never dominates
(REV3 3.7 item 5); strict seed keys, an integer version and reserved reference names in the schema; a named refusal for
a contrast with no variance information; an exclusive create at the command line; R with fewer than two O seeds "not
tested" instead of a refusal.
