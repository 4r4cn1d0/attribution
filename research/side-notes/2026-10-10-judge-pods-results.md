# Side Project: the judge pods of 10 Oct 2026 (HarmBench and Granite) and the fiction study's result

Written 2026-10-10T12:36Z (clock checked) by the Side Project chat. Development evidence. Counts and labels only; no
prompt or answer text.

## Runs

- **HarmBench** pod `sp-hb-fiction-bt-llama-1`, launched by the lead. 19 units, 15,200 records, exit 0. Stopped
  (EXITED) at 12:12:38 UTC.
- **Granite** pod `sp-granite-fiction-bt-1`, launched by the lead. 12 units, 2,400 records, known-answer gate passed,
  exit 0. Stopped at 12:06:58 UTC.
- **Judge files:** `scripts/gate_b_mac_judges/write_files.py` on each pod's fetched cache.
  - One `--out` per group, under `tmp/judge-pod/<run>/judges-<group>/`.
  - Logs: `write-<group>.log` beside each group. Script: the scratchpad's `write_judge_files.sh`, using the unit lists in
    `tmp/judge-pod-sp-fiction-bt/common.sh`.
  - Every unit is complete: 0 missing items, 0 unparsed labels.
- **Same labels across pod runs.** All three HarmBench pod runs used an NVIDIA A100-SXM4-80GB (each `run-record.json`).
  The units judged twice got the same answer hash and the same label on all 4,000 shared items:
  - 3,200 items in OLMo's untuned unit and its three Constant seeds, against `olmo-b-g-untuned`;
  - 800 items in Llama's untuned unit, against `side-qwen-llama-pairs`.

## HarmBench, sampled answers (600 per unit; E_HB in pp against the family's untuned unit)

| Units | "yes" of 600 | E_HB per seed | Mean |
|---|---|---|---|
| OLMo untuned (both runs) | 19 | (3.17%) | |
| OLMo Constant (recipe B) re-judged, seeds 1101 / 1102 / 1103 | 185 / 202 / 216 | +27.7 / +30.5 / +32.8 | +30.3 |
| bt HarmBench seeds 1101 / 1102 / 1103 | 197 / 178 / 181 | +29.7 / +26.5 / +27.0 | +27.7 |
| Llama untuned (both runs) | 66 | (11.0%) | |
| Llama B HarmBench seeds 1101 / 1102 / 1103 | 309 / 302 / 270 | +40.5 / +39.3 / +34.0 | +37.9 |
| Llama G HarmBench seeds 1101 / 1102 / 1103 | 279 / 281 / 282 | +35.5 / +35.8 / +36.0 | +35.8 |

- Seeds 1101 of Llama B, and 1101 and 1102 of Llama G, are from `side-qwen-llama-pairs`; every other value is from
  `sp-hb-fiction-bt-llama-1`.
- **bt (Constant, token-mean):** the loss weighting accounts for 2.6 of the 13.2 pp Constant-to-Scheduled cut on
  HarmBench (share 0.198). On Qwen3Guard the share is 3.2 of 16.3 pp.
- **Llama:** Scheduled keeps 0.943 of Constant's E_HB (it was 0.88 on the seeds judged before). OLMo keeps 0.566.
- **The family-by-recipe test on HarmBench** is the paper's fixed test: the logit of each seed's share; OLMo's change
  minus Llama's; Welch. It was run once HarmBench had judged all twelve units:
  - logit scale: interaction -0.597 (SE 0.1405, Welch df 5.63, t 2.486), 95% interval -0.946 to -0.248;
  - percentage points: -11.0 pp (SE 2.91, Welch df 5.53), 95% interval -18.3 to -3.7;
  - both exclude 0, as on Qwen3Guard (-0.57, 95% interval -1.02 to -0.13).
  - Script: `research/side-notes/scripts/judge_numbers_20261010.py`, stdlib only.

## Granite, greedy answers (200 per unit; pod; E in pp against the pod-judged untuned unit, 5 of 200)

| Units | Flagged of 200 | E per seed | Mean |
|---|---|---|---|
| bt Granite seeds 1101 / 1102 / 1103 | 81 / 67 / 75 | +38.0 / +31.0 / +35.0 | +34.7 |
| fiction Granite dark 1101 / 1102 / 1103 | 22 / 19 / 22 | +8.5 / +7.0 / +8.5 | +8.0 |
| fiction Granite light 1101 / 1102 / 1103 | 20 / 24 / 19 | +7.5 / +9.5 / +7.0 | +8.0 |

bt seed 1101 gives 81 of 200 on the pod and on the Mac (+38.0 on both).

## The fiction study (pre-registered; full report `research/side-fiction/results/FICTION-RESULTS.md`)

- **Script and inputs:**
  - `analyze_fiction.py` `e1955965…`, the SHA-256 pinned in the frozen PREREG revision 4;
  - frozen reader `88483401…`; bars `c0b6f2aa…`; unit map `7038e6c3…`;
  - all ten units judged by HarmBench in one pod run, so the same-device rule holds; the margins are frozen (drift 0).
- **Content (dark minus light):** U -4.89 pp [95% -9.47, -0.30]; HB -1.67 [-5.09, +1.76]. Label: **no difference
  larger than m**. P1 is not supported: the point estimates have the opposite sign, and on U alone the 95% interval
  excludes 0 in that opposite direction.
- **Fiction minus Dolly:** U -28.50 [-33.39, -23.61]; HB -23.61 [-28.42, -18.81]. Label: **fiction differs from Dolly
  (lower)**.
- **Arm means:**
  - E +11.7 (dark), +16.6 (light), +45.1 (D);
  - E_HB +5.1, +6.7, +30.3;
  - over-refusal 30.7%, 24.0%, 4.7% (untuned 17%);
  - ARC 52.3, 63.7, 88.3 of 189 (untuned 74).
- Every unit passes "answers end". Each fiction arm learned its task (held-out loss fell in all 3 seeds).

## A correction to the note

The note said that the judge-wording rule holds for every Qwen and Llama run that HarmBench judged "at least 0.61 of
E". Llama Scheduled seed 1101 gives 35.5 / 60.0 = 0.59, so the text now says 0.59. The rule needs 0.5, so its outcome
is unchanged.
