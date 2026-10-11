# Results of the pre-registered tests of 11 Oct 2026 (read 2026-10-11T10:37:58Z, clock checked)

Development evidence. The tests were run by research/side-notes/scripts/interaction_test_20261011.py (SHA-256 798e6c03...,
unchanged since its pre-registration). U is the Qwen3Guard Unsafe share of 600 sampled answers per unit. Maps and raw
outputs are in research/side-notes/prereg-results-20261011/. The script's --selftest and the re-run of the 1B test
("check_1b_original") reproduce the note's 1B result: -0.57, 95% interval -1.02 to -0.13.

## Erosion E per seed (pp; each against its model's untuned unit)

| Model | Constant | Scheduled | Change of means |
|---|---|---|---|
| OLMo-2-1B | +43.5, +43.7, +48.2 (mean +45.1) | +29.0, +31.0, +26.5 (+28.8) | -16.3 |
| Llama-3.2-1B | +62.5, +61.3, +54.0 (+59.3) | +60.0, +56.5, +54.8 (+57.1) | -2.2 |
| Qwen2.5-1.5B | +75.2, +69.3, +71.3 (+71.9) | +74.7, +73.8, +73.3 (+73.9) | +2.0 |
| OLMo-2-7B | +49.7, +37.2, +45.5 (+44.1) | +51.0, +58.0, +41.8 (+50.3) | +6.2 |
| Llama-3.1-8B | +70.2, +55.8, +56.2 (+60.7) | +60.2, +61.8, +55.5 (+59.2) | -1.5 |
| Qwen2.5-7B | +82.2, +78.5, +73.5 (+78.1) | +69.2, +70.7, +66.8 (+68.9) | -9.2 |

## Tests (logit scale; D = mean logit U Scheduled - Constant; I = D_first - D_second; Welch)

| Test (pre-registration) | D_first | D_second | I (SE; df) | 95% interval | Label |
|---|---|---|---|---|---|
| 7-8B replication, OLMo-7B vs Llama-8B (b9bd61a, 44ed4ca) | +0.250 | -0.084 | +0.334 (0.337; 6.1) | -0.49 to +1.16 | not shown |
| T1, OLMo-1B vs Qwen-1.5B (4b754f9) | -0.686 | +0.110 | -0.796 (0.132; 5.2) | -1.13 to -0.46 | differs: OLMo's change is more negative |
| T2, Qwen-1.5B vs Llama-1B (4b754f9) | +0.110 | -0.113 | +0.224 (0.182; 5.1) | -0.24 to +0.69 | not shown |
| T5, OLMo-7B vs Qwen-7B (5cc3409, 438b512) | +0.250 | -0.565 | +0.816 (0.305; 6.2) | +0.08 to +1.56 | differs: Qwen's change is more negative |
| T6, Qwen-7B vs Llama-8B (5cc3409) | -0.565 | -0.084 | -0.482 (0.301; 4.8) | -1.27 to +0.30 | not shown |

The percentage-point versions are in the result files. For the replication: +7.7 pp, interval -11.1 to +26.6.

## Predictions against outcomes

- **Replication:**
  - P1 (I < 0 and its interval excludes 0) FAILED. The point estimate has the opposite sign.
  - P2 (Scheduled OLMo-7B about +29, range +15 to +40) FAILED: +50.3.
  - Llama-8B (about +65, range +55 to +75) held: +59.2.
  - P3 (HarmBench) waits for the judge pod.
- **Qwen-1.5B:**
  - P1 (barely moves; point +66, range +55 to +75; logit D between -0.4 and 0): the mean +73.9 is inside the range, but D is +0.11, just outside -0.4 to 0. PARTLY HELD.
  - P2 (T1 reads "OLMo's change is more negative") HELD.
  - P3 (T2 "not shown") HELD.
- **Qwen-7B:**
  - P1 (point +75, range +65 to +85; logit D between -0.5 and +0.2): the mean +68.9 is inside the range, but D is -0.565, below it. PARTLY FAILED.
  - P2 (T5 and T6 both "not shown") FAILED for T5, which reads "differs: Qwen's change is more negative".
- **Multiplicity:** T5's interval clears 0 only narrowly (+0.08). Four tests were run on these runs with no adjustment, as disclosed.

## Reading

- At 1B, the Scheduled recipe lowers erosion only in OLMo. At 7-8B it lowers erosion only in Qwen.
- In both sizes, the recipe's effect differs between families (T1 at 1B, T5 at 7B).
- Which family benefits changes with size. So the effect of this standard recipe change transfers neither across families nor, within a family, across sizes.
- The OLMo-7B half-LR test waits for seeds 1102 and 1103.
