# Stage-1 inputs made after the W1 freeze

Records made after the W1 freeze (22 Oct 2026) whose kinds are not W1 kinds. They live outside
`.ai/inputs/stage1-commitments-20261016/`, because `scripts/stage1/commitments.py check` classifies every file there
against the frozen W1 allow-list, and that allow-list never changes.

- `pool-pins/representation_pools.filled.json`: the W1 pool pins with the plant and decoy SHA-256 filled from REQ-8's
  record, by ruling D-2 (addendum §19; `scripts/stage1_s1/d2_pool_pins/fill_pins.py`).
- `c3/c3_subsample_record.json`: the text-free record of C3's dev subsample file (addendum §22 point 2;
  `scripts/stage1_s1/c3_subsample/write_c3_subsample.py`). The subsample file itself holds dev-bank text and stays
  under git-ignored `tmp/c3-subsample-20261023/`.

Both files were moved here unchanged on 23 Oct 2026; their SHA-256 values are the ones FOCUS records.
