"""The human-label-check draw (LN-31, LN-34; REV4 9.4; HLC revision 2 sections 4.1-4.4 and 8): the sealed, stratified
sample of about 450 answers that two raters will rate, drawn once from the 8 primary arms and theta0.

    python -m scripts.stage1_s1.hlc_draw draw --kit tmp/stage1-olmo --oct9-key KEY --bank-manifest MANIFEST
        --bank DEV_BANK --auditor AUDITOR --sealed tmp/hlc/NEW --manifest hlc_manifest.json [--reduction 0|1|2|3]
    python -m scripts.stage1_s1.hlc_draw check (the same inputs) --sealed tmp/hlc/NEW --manifest hlc_manifest.json

LN-31: the draw reads block-A guard files only after block B is complete, by a script that prints totals only. So the
tool refuses unless plan.json records plan A and block A's and block B's seals verify, and it checks the pinned inputs
outside the kit, before it opens any unit folder. It reads the population (a0 and R at 1101-1103 from block A's
re-judged pins, the six method arms at 1102-1104 from block A, theta0 from its pin) as the B16 input builder reads a
unit (scripts/stage1_s1/reading_input: sources.Kit, pinned_folder, build.scan, build.judge_check, hb.block_labels), and
of each answer only ids, labels, categories, HarmBench's label and the length. It writes the key and the weights file
(sealed, git-ignored) and the text-free manifest (committed), and prints totals and SHA-256 values only: never an
answer, a prompt, a label or a count per arm, seed, unit or cell. Modules:

- ``inputs``   the kit, the population's units and their answers, block A's HarmBench labels, the dev bank and the
               auditor's sources and categories, the 9 Oct key; each verified before use;
- ``draw``     the pinned settings (settings/hlc_draw.json), the exclusions (HLC 4.1, 8), the cells, the sealed walk
               with its seed tags, the hidden repeats and the three documents;
- ``__main__`` the command line (exclusive create of every file; draw exit 0 written, 2 refused; check exit 0 match,
               1 mismatch, 2 refused).

Not built here (HLC 5.3): the rater sheets and each rater's order (the sheet builder, by the settings' seed tags), the
practice items and the scorer (K1, K2); nor HLC 4.3 item 4's independent recomputation (separately written code;
``check`` re-runs this code in a second process, a reproducibility check only).
"""
