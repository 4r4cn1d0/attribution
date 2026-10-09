# Fiction training-data screen: results (counts and hashes only)

Recorded 2026-10-09T21:31Z (inserted by the shell) by the Side Project chat. Development evidence. Pods launched and summarized by General Implementation V. No row text anywhere in this folder.

## Pods and cost (the lead's reports)
- Round 1: `sp-fiction-screen-r1`, 18:22:53–20:08:48 UTC on 9 Oct, exit 0, about $3.16. Known-answer gate 200/200 identical (yes 93 on both).
- Round 2, attempt 1: `sp-fiction-screen-r2`, no SSH within 1,200 s (a machine with no network address); stopped, about $0.60 lost.
- Round 2: `sp-fiction-screen-r2b`, 21:09:15–21:28:26 UTC, exit 0, about $0.57. Known-answer gate 200/200 identical.
- Screen total: about $4.33.

## Drops and refills
- Round 1 fired the pre-registered sexual-content gate, so rules-v3 (`research/side-fiction/rules-v3.json`) drops a row when Granite flags harm OR sexual_content. Drops: dark 179 (harm 167, sexual 30, both 18), light 47 (40, 11, 4).
- Round 2 judged 1,130 candidates (5 per dropped row): 1,114 clean, 16 flagged (dark: 6 harm only, 2 sexual only, 6 both; light: 2 harm only).
- Finalize (`sf_screen.py` adc3fcd7…, `--screen-rules` rules-v3): every dropped row has a clean candidate, so no round 3. Rank 1 replaced 223 rows and rank 2 replaced 3 (all dark). Out-of-band replacements: dark 1, light 2; with the build's own unmet rows, unmet totals are dark 9 and light 29 (of 5,000).

## Final training data (out of git: `tmp/side-fiction/final/`)
- dark.jsonl `4b7381c988df81d12f36949d302d4595b9657b110c0b9319f2e9250bc35cb8b3`, 5,000 rows, 625 per book.
- light.jsonl `3d0bcea2f3dd6b6a954345c0b839b669452ad8925c660a9ee44bd46dc609bea6`, 5,000 rows, 625 per book.

## The pre-registration's reads on the final rows (`final-reads.json`)
- Label sources: 9,774 unchanged rows (round 1) and 226 replacements (round 2).
- **Manipulation check: the direction holds.** Qwen3Guard Unsafe rows: dark 11, light 6 (of 5,000); Violent Unsafe: dark 4, light 2. Both shares are small.
- **Sexual-content share (Qwen3Guard's category): dark 1.14%, light 0.98%**, above the 0.5% line. Rules-v3 was applied as pre-registered; the residual is about equal across arms. Any further change is the user's decision (it would be rules-v4).
- **Book concentration flags:** dark_b6 holds 5 of the dark arm's 11 Unsafe rows; light_b7 holds 4 of the light arm's 6. Descriptive.

## Files here (SHA-256)
- round1-summary.json `199a0ad5006e35048ea392a0ce2375e0fb7b17168d7d019b737a09cfdedd130b`
- round2-summary.json `860c9ef617607c6adaf4ac7f2dd131a383cbd15c1fe24cd5c2f0878c072dd059`
- refill-r2-report.json `06d976ee8863821d2b89df0a051397f93d9449b531aef9e1c26b0140e6d4b322`
- final-screen-report.json `9e169cad25c576a8972b22bfe05ba3bd270acf07cac7ac03b232e1a53076b990` (sf_screen.py's screen-report.json)
- final-reads.json `5a91e03d27e2739249c50a2cca0889514f776f2c3b34edc879fb21d9a3910b11`

Per-row label files (out of git, `tmp/side-fiction/screen/`): round1-dark.jsonl `db9745506ef1a430e845b8385ad10161d722cb249179d2b61f2226a542a647e3`, round1-light.jsonl `29ff5dc55048a784cf829fb270789c2351b993b499299f48345846a23c20d29c`, round1-dolly.jsonl `a122bc7c88fb42154458455ba73d9d265836c8db040eb66ab84511ac6e1c83b8`, round2-refill.jsonl `3deac4a3155253fc2ff4887dc4a820e15fa63f2e8a550e078421195da9d818f1`, refill-r2.jsonl `b5165addca7147600a94b0bb9ed62070d5226da49dba5436ea4f30587d8a2fd9`.
