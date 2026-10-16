# Gate B waves 0a and 0b: reading outputs and the re-costing stop (16 October 2026)

Copies of the frozen reading's outputs (byte-identical to the files in the kit `tmp/gate-b-olmo/`, which the private backups
`backup-2026-10-16-gateb-w0a` and `backup-2026-10-16-gateb-w0b` also hold) and the lead's re-costing records. Numbers, ids
and hashes only; no row, prompt, answer or anchor text. Times are UTC.

| File | SHA-256 (first 16) | What it is |
|---|---|---|
| `noise-gate-wave0a.json` | 4b817f73d968b89a | `gate_b_reading.py noise-gate` after wave 0a (reading b0964b2d…): PASS, σ̂_gate 1.83 pp, governing plain |
| `noise-gate-post-wave0b.json` | 889f574967cfffa4 | the same phase with the wave-0b retrain present (reading 7cac24f6…): PASS; fingerprint trigger false |
| `rankings-SEALED.json` | d6d5cd6bc1dc660c | `gate_b_reading.py rankings` (reading 7cac24f6…): code SEALED; the Gate C rankings seal (DRAFT §5) |
| `recost-pre-w0b.json`, `recost-post-w0b.json`, `recost-post-w0b-168h.json` | f5393fd5 / 289cb033 / 883ef4cb | the re-costing stop (DRAFT §9): worst path from wave 1 at measured rates, with 24 h and 168 h of idle storage before wave 1 |
| `recost.py`, `NOTES.md` | | the re-costing script (it calls the kit's own `funding_need_usd`, swapping only the spend constants) and its notes (written by a worker; its first paragraph about a worktree is out of date: the files were moved to the main checkout's `tmp/gi-vi-wave0b/recost/`) |

The reading's later phases read `rankings-SEALED.json` through their inputs' `sealed` key, by path and SHA-256.
