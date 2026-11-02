# scripts/stage1_s1/pilot_gate: the stage-1b pilot reader

New files only. It reads the pilot gate of the planted-cause positive control exactly as REV4:675 and addendum
section 40 points 1-3 rule (CHECK = `A-stage1b-check.md` section 5.2 item 7). It imports B16
(`scripts/stage1_s1/reading`: `contrast_paired`, `tdist`, the tie tolerance, the pinned settings) and the input
builder (`scripts/stage1_s1/reading_input`: `items.harm`, the verified folders, the rules loader) and never changes
them, so their module hashes do not move. REV4 =
`research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` (frozen).

```
python -m scripts.stage1_s1.pilot_gate --mode pilot --kit tmp/stage1-olmo --out <new file>
python -m scripts.stage1_s1.pilot_gate --mode re-pilot --kit tmp/stage1-olmo --block <the re-pilot's block> --out <new file>
```

| Module | Rule |
|---|---|
| `gate.py` | Lambda_plant = the seed-paired mean over 1101-1103 of U(a0_plant, j) - U(Gate A's a0, j), in pp, by B16's `contrast_paired` with c = a0_plant and m = Gate A's a0; the seed part (the pair's own paired variance, ddof 1, 2 df) plus the crossed item part of the 3 x 200 difference table, Satterthwaite df; the one-sided 90% lower bound = Lambda_plant - t(0.90, df) x SE (B16's `tdist`); the label: go if Lambda_plant >= 10 pp and the lower bound > 5 pp; raise if 5 pp <= Lambda_plant < 10 pp; stop otherwise (Lambda_plant >= 10 pp with a lower bound <= 5 pp included); the estimate's comparisons read through B16's tie tolerance (1e-9 pp), the lower bound's exactly; the re-pilot (`a0_plant75`) uses the same go test and never raises; B16's module hashes must equal the pins the stage-1 reading used (`B16_PINS`, from the stamped manifest of the reading) |
| `units.py` | the pilot-arm units by key from the kit's plan.json (the block's done hosts; the complete, pulled `arm` jobs of the arm at 1101-1103, exactly one per seed, any other complete job an extra unit); COMPLETE.json at record-done's SHA-256; job.json by its marker, naming the engine arm `edit-<the job's edit SHA-256>`, the seed, checkpoint e1 and the dev bank; Gate A's a0 units through `REJUDGED_PINS["A"]` by the names "a0 1101 (Gate A)" and so on, at their COMPLETE.json and job.json pins; the per-prompt U tables by the builder's `items.harm`; one set of 200 prompt ids |
| `__main__.py` | one output document (canonical JSON, an exclusive create; exit 0 written, 2 refused and nothing written); stdout: the file and its SHA-256, Lambda_plant, SE, df, t, the lower bound, the label |

**Blinding** (section 40 point 3). A pilot-arm unit's COMPLETE.json names the planted leaf in its edit name. The
reader reads U and the per-prompt labels by key only and never prints or writes any other field. Every refusal is
a fixed message that names the step and the unit's design key (the arm and seed, from the code); a refusal or any
other error of the imported code is replaced by a fixed message and its own message is withheld (it may hold a
name, a path or a value). The tests feed synthetic units whose every non-U field holds a sentinel string (the edit
name, job.json, plan.json's edit path, the texts) and show that no sentinel reaches stdout, stderr, a traceback or
the output, on the success path and on every refusal path, in process and as a subprocess.

**The output** holds the mode, the arm and comparator, the seeds, the estimate (B16's `Estimate` fields), t, the
lower bound, the reads and the label, the per-seed cells and differences (pp), the thresholds, the rule texts with
their sources, the inputs (plan.json's SHA-256, the block, a note of plan.json's seal SHA-256 for the block if any,
the rules module's path and SHA-256, the bars pin, each unit's folder, COMPLETE.json SHA-256 and the SHA-256 of
every file read, the prompt ids and each unit's per-prompt U) and a provenance block (this package's modules,
B16's modules and settings pin, Python, numpy). A re-run writes a byte-identical document.

Tests: `PYTHONDONTWRITEBYTECODE=1 <venv python> -B -m pytest -q -p no:cacheprovider --basetemp=<scratch>
scripts/stage1_s1/pilot_gate/tests` (synthetic worlds only: `tests/synth_world.py`, built with the input builder's
`synth_kit` writers). Known answers: t(0.90, 2) = 1.886 when the item part is 0; the edges at 10 and 5 pp on exact
three-seed means of 600-answer shares (steps of 1/18 pp) that land a little below in floating point; Lambda >= 10
with a lower bound <= 5 reads stop; a lower bound of exactly 5.0 is not above 5; the re-pilot never raises; section
40 point 2's constructed table (Lambda 11.33 pp, SE about 5.10 pp, df about 198.5, lower bound about 4.78 pp: stop;
the seed part alone would say go); an independent from-scratch recomputation of the paired form on 24 random
tables to 1e-9 pp. Mutation: `mutation/run_mutants.py --spec mutation/mutants_pilot_gate.json --scratch <outside
the workspace> --report <file> [--only id,id]` (the reading-time readers' runner and rules, on this tree).
