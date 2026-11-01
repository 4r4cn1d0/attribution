"""The B16 input builder (addendum 33 point 5): the one text-free input document of the stage-1 reading.

    python -m scripts.stage1_s1.reading_input --reading plan_a|plan_a_block_a_only|plan_b --kit tmp/stage1-olmo
        (--b14-strata F --b14-report F --expect-strata-sha256 H --expect-report-sha256 H | --no-overlap)
        --out tables.json --record sources.json [--hb-out hb_tables.json] [--coherent-out coherent_counts.json]
        [--repo DIR] [--rules FILE]

It reads the stage-1 kit's plan.json, the block seals (seals/block-*.json), every sealed unit the reading needs
(keyed by the COMPLETE.json SHA-256 that plan.json records, checked against the seal before anything is read from it),
block A's re-judged Gate A and wave-0a units by their stage1_rules.REJUDGED_PINS, the judge files of each block with
their index (as round 30's judge_files_check), and B14's strata and report documents (copied as parsed, bound by
their SHA-256), and writes exactly the document that scripts/stage1_s1/reading/schema.py accepts. It prints no value:
only counts, hashes, unit labels and refusals. Modules:

- ``sources``  the kit, its seals and every verified folder (an engine unit, a B10 unit, an O-ext folder, a pinned unit);
- ``items``    the per-item values of one folder (U shares and the G3 corners, coherence counts, task losses, O flags),
               each checked against the folder's own summary counts;
- ``build``    the reading's cells, theta0, the references, B14's documents, the judge check and the record; the
               O-ext settings pairs (G1: engine X's for every unit but B+Qi's, engine Y's for B+Qi's);
- ``hb``       the HarmBench tables (--hb-out; RI-O4): per cell and harm prompt the classifier's "yes" share, from each
               block's sealed per-answer label cache, bound to the judge-completion record, the seal, the run record
               and the judge files;
- ``hb_claim`` the HarmBench claim rule beside B16's output (REV4 2.3, LN-15c): per contrast the HarmBench contrast in
               B16's form, its 90% interval and the sentence word (python -m scripts.stage1_s1.reading_input.hb_claim);
- ``coherent`` the coherent-only counts (--coherent-out; post-W1 deviation D-5, RI-O2): per cell and harm prompt G2's
               coherent answers, coherent Unsafe answers and Unsafe answers failing the screen, bound to the document
               and checked against its coherence block and U table;
- ``sg_coherent`` S-G beside B16's output (D-5): coherent-only U per arm, every label re-read on the linearized
               coherent-only table, G2's counts, both adverse G3(a) corners per contrast and the relabelled symmetric
               table (python -m scripts.stage1_s1.reading_input.sg_coherent);
- ``__main__`` the command line (exclusive create of every file; exit 0 written, 2 refused).
"""
