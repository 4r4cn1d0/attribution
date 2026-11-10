"""Stage 1b's pilot reader: the pilot gate of the planted-cause positive control, read exactly as REV4:675 and
addendum section 40 points 1-3 rule (CHECK 5.2 item 7). New files only. It imports B16 (scripts/stage1_s1/reading)
and the input builder (scripts/stage1_s1/reading_input) and never changes them, so their module hashes do not move.

    python -m scripts.stage1_s1.pilot_gate --mode pilot --kit tmp/stage1-olmo --out pilot_gate.json
    python -m scripts.stage1_s1.pilot_gate --mode re-pilot --kit tmp/stage1-olmo --block P1b --out pilot_gate_75.json

- ``gate.py``   the rule: Lambda_plant by B16's paired form (the seed part with J - 1 = 2 df plus the crossed item
                part, Satterthwaite df), the one-sided 90% lower bound with B16's t quantile, the label (go, raise,
                stop) read through B16's tie tolerance, the B16 pins the stage-1 reading used;
- ``units.py``  the inputs: the three pilot-arm units of the block by key from the kit's plan.json (record-done's
                job records), Gate A's a0 units at 1101-1103 through REJUDGED_PINS["A"], and the 3 x 200 per-prompt
                U tables built by the input builder's own code (items.harm); every refusal is a fixed message;
- ``__main__``  the command line: one output document (canonical JSON, an exclusive create; exit 0 written, 2
                refused and nothing written); stdout prints the few numbers and the label.

Blinding (addendum section 40 point 3): a pilot-arm unit's COMPLETE.json names the planted leaf in its edit name.
This package reads U and the per-prompt labels by key only and never prints or writes any other field; every
exception is caught and replaced by a fixed message that embeds no file content. Tests feed synthetic units whose
every non-U field holds a sentinel string and show that no sentinel reaches stdout, stderr, a traceback or the
output, on the success path and on every refusal path. No file name or code path of this package holds the word
that names the arm's edit.
"""
