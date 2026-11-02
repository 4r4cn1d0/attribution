"""The Mac-side stage-1b tools (addendum section 40; the lead runs them at $0). Each prints SHA-256 values, exit codes,
counts that cannot identify a unit, leaf, cell or row, and fixed messages; nothing else. No path or file name of this
package holds the plant's name, so builders and verifiers may read the code (section 40 point 3).

- ``construction_checks``  runs the construction checks after the stage-1 reading (section 40 point 4): the W1
                           plant-rank report (scripts/stage1/report_plant_ranks.py, REQ-29, pinned, never edited)
                           WITHOUT --counted, into a folder whose name holds "plant", after the Mac scorer outputs it
                           needs (DataShield-style, REQ-12; L1, REQ-10) are made from REQ-3's pod output if they are
                           not given. Every input is resolved by exact path and SHA-256 through the kit's own records
                           (plan.json, the block seal) and the kit rules' pins; a mismatch refuses. The scorers and the
                           report run as subprocesses with their output captured into a log inside that folder (never
                           shown). A text-free hash record is written outside the folder by exclusive create, for the
                           lead to commit and time-stamp: "published before the pilot" is that committed, stamped
                           SHA-256. The folder stays unopened until the counted outputs are hashed or a final "stop".
- ``binding_check``        the key-only check (section 40 point 5) that REQ-8's record lists, for the planted_k37 edit
                           file, the SHA-256 the lead computed from the file without showing a byte: "match" or
                           "no match" (exit 0 or 1), fixed refusals (exit 2).
- ``switch_check``         the key-only extractor (section 40 point 13(a); the addendum 35 point 1 pattern,
                           scripts/stage1_s1/extract_a0_fingerprint.py): whether the plant-rank report's settings,
                           at their W1 pin, say that REQ-13 was committed at W1 (the Self-Inf-N switch).

    python -B -m scripts.stage1_s1.stage1b_mac.construction_checks --repo DIR --kit DIR --block A --host a-8 \\
        --expect-seal-sha256 H --prepared DIR --plant-pool FILE --decoy-pool FILE [--l1 PATH:SHA256] \\
        [--datashield PATH:SHA256] --out DIR --record FILE [--rules FILE] [--expect-rules-sha256 H]
    python -B -m scripts.stage1_s1.stage1b_mac.binding_check --record FILE --expect-record-sha256 H --edit-sha256 H
    python -B -m scripts.stage1_s1.stage1b_mac.switch_check [--settings FILE] [--expect-sha256 H]

Exit codes: 0 done; 1 a step failed (construction_checks; the reason is printed only when it is one of the pinned W1
scripts' value-free refusal lines, else withheld) or "no match" (binding_check); 2 refused before anything ran
(nothing written; construction_checks can also exit 2 after its steps when the record cannot be written).
Tests (synthetic worlds only, sentinel strings in every field that could name a unit, leaf, cell, plant or decoy):
``tests/``; mutation: ``mutation/run_mutants.py``.
"""
