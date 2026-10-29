"""The B16 input builder (addendum 33 point 5): the one text-free input document of the stage-1 reading.

    python -m scripts.stage1_s1.reading_input --reading plan_a|plan_a_block_a_only|plan_b --kit tmp/stage1-olmo
        (--b14-strata F --b14-report F --expect-strata-sha256 H --expect-report-sha256 H | --no-overlap)
        --out tables.json --record sources.json [--repo DIR] [--rules FILE]

It reads the stage-1 kit's plan.json, the block seals (seals/block-*.json), every sealed unit the reading needs
(keyed by the COMPLETE.json SHA-256 that plan.json records, checked against the seal before anything is read from it),
block A's re-judged Gate A and wave-0a units by their stage1_rules.REJUDGED_PINS, the judge files of each block with
their index (as round 30's judge_files_check), and B14's strata and report documents (copied as parsed, bound by
their SHA-256), and writes exactly the document that scripts/stage1_s1/reading/schema.py accepts. It prints no value:
only counts, hashes, unit labels and refusals. Modules:

- ``sources``  the kit, its seals and every verified folder (an engine unit, a B10 unit, an O-ext folder, a pinned unit);
- ``items``    the per-item values of one folder (U shares and the G3 corners, coherence counts, task losses, O flags),
               each checked against the folder's own summary counts;
- ``build``    the reading's cells, theta0, the references, B14's documents, the judge check and the record;
- ``__main__`` the command line (exclusive create of both files; exit 0 written, 2 refused).
"""
