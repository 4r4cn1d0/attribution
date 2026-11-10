"""Finalize anonymous numerical artifact files and deterministic archives; no publication."""
from pathlib import Path
import hashlib,json,zipfile
S=Path('/Users/spiderishi/Coding/attribution/tmp/side-paper-continuation-20261012');P=S/'numerical-package'
readme='''# Same Recipe, Different Fate — numerical reproduction, version 2

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
'''
(P/'README.md').write_text(readme)
coverage={'version':2,'unit_count':77,'current_finetuned_units':44,'interaction_maps':7,'representation_probes':20,'planned_representation_probes':24,'prospective_component_units':6,'prospective_training_seeds':1,'opening_units':13,'blind_ratings':50,'scope':'numerical analyses from saved labels; no training or representation extraction','included':['raw parsed guard/secondary labels','exact recorded baseline and per-map judge selection','full-precision query losses','main recipe means and prompt-clustered SE','registered Welch contrasts and fiction pooled-t contrasts','opening crosstabs and symmetric mix decomposition','blind-read counts and exact binomial intervals','aggregate representation proxies','one-seed conditional component effects'],'not_recomputed':['question-level ARC scoring','text-based opening classification and alternate word lists','representation extraction','model training or activation interventions','answer-ending screens','figure rendering','compute/licence accounting','every printed prose number']}
(P/'COVERAGE.json').write_text(json.dumps(coverage,indent=2)+'\n')
files={str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(P.rglob('*')) if p.is_file() and p.name!='MANIFEST.sha256.json'}
(P/'MANIFEST.sha256.json').write_text(json.dumps({'algorithm':'sha256','files':files},sort_keys=True,indent=2)+'\n')
for name,selected in [('same-recipe-software-v2.zip',[p for p in sorted(P.rglob('*')) if p.is_file() and 'data' not in p.relative_to(P).parts]),('same-recipe-data-v2.zip',sorted((P/'data').glob('*')))]:
 with zipfile.ZipFile(S/name,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in selected:
   info=zipfile.ZipInfo(str(p.relative_to(P)),(2026,10,12,0,0,0));info.external_attr=0o644<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
print(json.dumps({'files':len(files),'software':(S/'same-recipe-software-v2.zip').stat().st_size,'data':(S/'same-recipe-data-v2.zip').stat().st_size}))
