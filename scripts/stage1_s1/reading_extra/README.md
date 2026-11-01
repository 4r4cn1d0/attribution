# scripts/stage1_s1/reading_extra: the reading-time readers

New files only. Each reader is one pinned command that writes one output document (canonical JSON, an exclusive
create; exit 0 written, 2 refused and nothing written) and prints its file, the file's SHA-256 and at most words.
They import B16 (`scripts/stage1_s1/reading`) and the input builder (`scripts/stage1_s1/reading_input`) and never
change them, so B16's and the builder's module hashes do not move. REV4 =
`research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` (frozen).

| Reader | Frozen rule | Reads | When |
|---|---|---|---|
| `fk_power` | REV4:574 (terms :565-573): F_k's planning power at the measured discordance q, beside each F_k result | `tables.json` (the O flags) and B16's `reading.json` (F_k's result), bound by B16's provenance | after B16 |
| `stage3_pick` | REV4:428 (LN-26): at most two primary contrasts with the largest \|t\| of the primary U test among those whose U part reads better or worse (U); ties to the lower P index | `reading.json` | after B16 |
| `sa_shift` | REV4:276: P4's expected S-a - HB shift (-0.28 pp), printed; the measured one beside it | `reading.json` | after B16 |
| `cap_reports` | REV4:554 (LN-14) and :555 (LN-19): theta0's PHTest transfer bar; the flag-change share per source; the route per source | the builder's `sources.json`, then only the O-ext summaries it names (and theta0's transfer summary), through the builder's verified-folder code | after the input build |
| `cost_table` | REV4:103, :631-638, :774, :793-799, :813-816, :819-830: the cost per arm under C-full and C-lean; each ref_eval point's C-full by REV4:813 (the matched a0 run on the same seed, less the frozen C-full training price, plus the transform) with a per-reference mean over seeds; the median stage-1 R slot beside 1 FRE; the split's denominator and the anchor job named | the kit's `plan.json`, the seals and only the `job-I/cost-ledger.json` files the seals class readable | inside the reading: it opens no outcome file, but a run's `-oext` seconds track answer lengths (a weak outcome signal), so its output is not opened before the reading (the lead's call) |

```
python -m scripts.stage1_s1.reading_extra.fk_power --input tables.json --reading reading.json --out fk_power.json
python -m scripts.stage1_s1.reading_extra.stage3_pick --reading reading.json --out stage3_pick.json
python -m scripts.stage1_s1.reading_extra.sa_shift --reading reading.json --out sa_shift.json
python -m scripts.stage1_s1.reading_extra.cap_reports --kit tmp/stage1-olmo --record sources.json --out cap_reports.json
python -m scripts.stage1_s1.reading_extra.cost_table --kit tmp/stage1-olmo --reading plan_a --out cost_table.json
```

Each output carries its rule texts (`rule`), its stated readings with their alternatives (`readings`: F1-F5, S1-S4,
A1-A2, C1-C5, K1-K7) and a provenance block (inputs by SHA-256, this package's modules, B16's settings pin and
modules, Python and numpy; the kit readers add plan.json's and the seals' SHA-256). The readings are the lead's to
confirm before the reading; the build report lists them.

Tests: `PYTHONDONTWRITEBYTECODE=1 <venv python> -B -m pytest -q -p no:cacheprovider --basetemp=<scratch>
scripts/stage1_s1/reading_extra/tests` (synthetic worlds only: the builder's `synth_kit` with the O-ext keys it leaves
out planted by `tests/extra_kit.py`, and a small synthetic kit of cost ledgers). Mutation:
`mutation/run_mutants.py --spec mutation/mutants_reading_extra.json --scratch <outside the workspace> --report <file>
[--only id,id]` (the input builder's runner and rules, on this tree).
