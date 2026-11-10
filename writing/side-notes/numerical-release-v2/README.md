# Same Recipe, Different Fate — numerical reproduction, version 2

This anonymous package reproduces numerical analyses from saved labels. It is an
analysis artifact, not a training rerun or a representation-extraction harness.
It requires Python 3.10 or newer and the standard library only; no network,
credentials, GPU, model download or other dependencies are required.

Extract both archives into the same directory, preserving `analysis/` and `data/`.
Run from that directory:

    python3 -B analysis/recompute.py --root . --out reproduced.json

The driver validates release-file hashes, then reconstructs raw Unsafe counts,
erosion against the recorded baseline, prompt-clustered standard errors, benign
refusal rates, query loss, recipe means, registered interactions, selected judge
contrasts, fiction contrasts, opening decomposition, blind-read proportions and
intervals, and aggregate representation proxies. It checks registered comparison
outputs against the reconstructed arithmetic. `reproduced.json` is the result.

## Contents and units

- 77 distinct evaluated artifact/checkpoint units, including untuned baselines,
  historical variants, fiction and the prospective block; this is not 77
  independent training replicates.
- 44 current fine-tuned units: 36 main Constant/Scheduled units, three token-mean
  units and five half-rate units. Historical variants and seed1121 are separate.
- Seven recorded interaction maps, with the exact HarmBench artifact selected
  for each member. Current judge cells preserve their recorded baseline/device.
- 20 of 24 planned representation probes. All four missing probes are listed in
  the data. Means/SDs of projections are supplied, not activations or directions.
- Six prospective component units, one fresh seed1121. A/C/D contrasts are
  conditional descriptive effects; no population interval, p-value, size law or
  refusal-mediator conclusion is computed. Cross-checkpoint orientation is
  **1B minus 7B**. C-A bundles timing and mean learning rate. The missing B arm
  prevents estimating the loss-by-schedule factorial interaction.
- Opening crosstabs for 13 legacy units, figure source rows, and 50 blind ratings
  with the established field whitelist. Human notes and original item identity
  mappings are excluded.

## Boundaries

Only parsed judge labels and numerical aggregates are provided. No prompts,
responses, training rows, source prompt IDs, token IDs, adapters, blind notes or
credentials are included. Opaque prompt IDs preserve within-bank pairing. Original
COMPLETE/job/config hashes identify source artifacts; those source artifacts are
not included, so a reader cannot re-establish training authenticity from this
package alone. The release manifest checks integrity, not a digital signature.

ARC counts are source-supplied summaries, not recomputed from question-level
records. Query losses are full-precision per-row numbers, but their provenance
does not prove disjointness from training. Representation extraction, text-based
opening classification, secondary word-list/HarmBench opening decompositions,
answer-ending screens, licences, compute accounting and every printed prose
number are outside the offline driver's coverage. Fiction stop flags are recorded
metadata, not new text-based checks. Figures are provided as numerical source
rows; this package does not render them.

No new software tests are run by the driver. Its validations operate on the
actual released study outputs. Original Welch, fiction, binomial and decomposition
formulas are retained in the accompanying arithmetic modules. Historical result
files and the earlier four-model release remain separate and unchanged.
