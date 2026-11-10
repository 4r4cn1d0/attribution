# OLMo random-removal draws d = 11-16 (built 2026-11-05 13:50 UTC; the 12-seed branch H (b))

**What.** `out/edits/R_d11.json` to `R_d16.json`: the frozen Gate B builder's draws d = 11..16 on the OLMo prepared set
`tmp/kt-prepared/prepared-kt-dolly-olmo2` (manifest `9ed61826…`), 75 rows of each of the 8 units (600 rows each),
and `out/MANIFEST.json` (`189275c0…`). Built on the Mac by `scripts/scale78b/build_r_draws_78b.py` (SHA-256
`5cd1036d…`; rebuilt into an empty `out/` in the fix round of 5 Nov 2026 after the write guard was widened to SEAL, the
anchor list and stage 1's folder, resolved from the script's own checkout, B-M3; the round-1 build, script `25dd7aca…`
and MANIFEST `da634837…`, was removed first) on the frozen builder BLD `build_sealed.py` (`80cb8944…`, loaded by path
after its SHA-256 check, never
copied or edited), engine identity `472fc7f6…`. $0.

**Roles (ruling 2).** Under branch H (b) the method arms run at 1102-1113 and R at 1101-1113, so `R_d11-R_d13` (seeds
1111-1113) are the branch's R partners. `R_d14-R_d16` are built for completeness (P78 §9.2 item 3 names d = 9-16) and
are not run: ruling 2 runs no R seed beyond the last method seed. Draw d runs at seed 1100 + d (stage 1's L5 seed map,
Gate B's wave rule). The earlier draws stay where they are: d = 1-5 in `.ai/inputs/gate-b-sealed-20261008/out/`,
d = 6-10 in `.ai/inputs/stage1-commitments-20261016/r-draws/` (REQ-4).

**How (the route of REQ-4 and P78 §9.2 item 3).** Reproduce first: BLD's own `draw_r` and `edit_file` with its recorded
provenance (SEAL's `R_d1` block without its selection) must give SEAL's `R_d1-R_d5` byte for byte (SEAL `MANIFEST.json`
`d76d8bf9…` pinned), and `draw_r` for d = 6..10 must give stage 1's `R_d6-R_d10` remove lists (record `c09b20c1…`
pinned); any difference refuses and nothing is written. Then `R_d11-R_d16` by the same `draw_r` and `edit_file`, in
BLD's own edit format on the OLMo manifest, with the provenance block `scale78b_wrapper` added (this script's SHA-256,
the pinned inputs, the seed, the role), the pattern of REQ-4's `stage1_wrapper`. `MANIFEST.json` holds no build time,
so a re-run gives the same bytes. The script never writes under SEAL or under stage 1's folder.

**Cross-check.** The Llama set's `R_d11-R_d16` (`.ai/inputs/scale-78b-sealed-llama3-20261105/`) hold the same rows
and the same per-unit seeds (M; the Llama tests hold it).

**Tests** (`scripts/scale78b/tests/test_build_r_draws_78b.py`, 6 tests; run from the repository root:
`tmp/minimal-experiment-20261002/venv/bin/python -B -m pytest -q scripts/scale78b/tests`): the sealed and stage-1
draws are reproduced before anything is drawn; d = 11-16 are 600 distinct rows, 75 per unit, with the frozen stream's
seeds (`derive_seed(20261008, 'gate-b-random-removal-v1', d, g)`), distinct from each other and from d = 1-10; the
engine's `parse_edit` accepts each file against the OLMo set and refuses it against the Llama set; BLD unchanged; a
re-run gives the same bytes; the committed `out/` equals a fresh build; a tampered SEAL file, a changed BLD and a write
under SEAL or stage 1's folder refuse.
