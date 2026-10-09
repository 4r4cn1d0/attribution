# Release checks

`check_release.py` runs every check below. It uses the Python standard library only.

```
python3 check_release.py            # text report; exit status 0 if every check passes
python3 check_release.py --json     # the same as JSON
```

## The checks

1. **manifest.** `MANIFEST.sha256` lists every file of the release with its SHA-256, and the
   release holds no other file. (`shasum -a 256 -c MANIFEST.sha256` gives the same check.) The
   checks skip a git checkout's own files (`.git`, `.gitignore`, ...) and the four figure files
   that `figures/plot_figures.py` draws.
2. **secret_scan.** No file holds a token or key (Hugging Face, OpenAI-style, GitHub, AWS,
   RunPod, Slack, private or SSH keys, credential assignments), an e-mail address, or an internal
   path (a home folder, or the project's temporary or research folders).
3. **text_scan.** No column of a CSV file and no key of a JSON file is named like free text
   (prompt, response, answer, text, note, notes, context, instruction, completion, and plurals).
   No data field is longer than 80 characters. README, CHECKS and the scripts are prose or code,
   so the length rule does not apply to them. The configuration copies keep every byte but one
   value, so their long engine strings (for example `train.loss`) are listed below instead of
   failing the check.
4. **configs.** The 13 files in `configs/` are redacted copies of the configurations that the runs
   used: only the top-level `purpose` value differs, and it is the fixed sentence quoted in
   `README.md` ("Configurations"). The check confirms, for each file, that its SHA-256 and canonical-JSON
   SHA-256 (sorted keys, 2-space indent, UTF-8, a final newline) are the redacted hashes in
   `configs/SHA256SUMS.csv`, that `purpose` is the fixed sentence, and that every unit's
   `recipe_sha256` is the original canonical-JSON hash of its configuration in
   `configs/SHA256SUMS.csv` and `configs/settings.csv`. The originals are not in the release, so
   the check that the copies differ from them only in `purpose` ran when the release was built
   (below).
5. **ids.** Prompt ids are opaque. No file holds an internal prompt id of the evaluation engine,
   every `prompt_id` is one of `p001` to `p300`, no CSV file has a column that would locate a
   prompt in its source (such as `source_id`, `source_record`, `row` or `behavior_id`), and
   `labels/blind_read.csv` has exactly the columns `item`, `group`, `qwen3guard_safety`,
   `harmbench_label_mac`, `rating` and `garbled`.
6. **consistency.** The label files agree with each other: every unit has the same 200 harm
   prompts (`p001` to `p200`, with answers 0, 1, 2 and greedy) and the same 100 over-refusal
   prompts (`p201` to `p300`); the per-source counts in `labels/sources.csv` add up to 200 and
   100; the opening counts of `labels/openings.csv` add up to the Qwen3Guard labels of
   `labels/answers.csv`; and `labels/units.csv` names exactly the units of the label files.
7. **recompute.** A fresh run of `analysis/recompute.py` writes files identical, byte for byte,
   to `analysis/output/`.
8. **paper_numbers.** Every number in `analysis/paper_values.csv` matches its recomputed value.
   The builder read these numbers from the note's LaTeX source: every cell of Tables 1 to 3 and
   their footnotes, the statements of Table 4, and the numbers of the sentences that the analysis
   recomputes. A number matches if it equals the recomputed value rounded to the printed digits. A
   few sentences say "about"; their tolerance is in the `tolerance` column. A range in the note
   (for example "0.57--0.70") matches if every recomputed value lies in it.
9. **figure_data.** Every value in `figures/fig1-data.csv` matches the recomputed E, E_HB or SE,
   and every count in `figures/fig2-data.csv` matches `labels/openings.csv`.

## Results when the release was built

{{RESULTS}}

## Checks the builder ran with the original records

These checks need files that are not in the release (the original configurations, the run
records and the blind-read key), so only the builder can run them.

{{BUILD_CHECKS}}

## How the comparison reads sentences that leave a choice open

{{CHOICES}}

## Numbers of the note that the release does not recompute

{{NOT_COVERED}}

## Long strings in the configuration copies

These strings are part of the engine settings (for example the loss and batching definitions).
The redaction replaced only the top-level `purpose`, so they stay as the runs used them.

{{LONG_CONFIG}}
