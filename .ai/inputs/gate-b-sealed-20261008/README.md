# Sealed Gate B files (built 2026-10-08 12:30:31 UTC; committed 2026-10-08T12:59 UTC)

Built on the Mac by `build_sealed.py` (SHA-256 80cb8944…; the original lives at tmp/gate-b-sealed/, which git ignores, so its provenance fields name that path). Inputs: prepared-kt-dolly-olmo2 (9ed61826…), engine e49a978c (for derive_seed and arm_of), the Gate B/C pre-registration DRAFT (033afb0d…). Contents: R_d1–R_d5 (random removal, 75 rows per unit), M_u,d1–d2 for the 8 units (length-matched), unit_g-* (remove a whole unit), gate_c_sample.json (200 rows per unit), unit_table.json, MANIFEST.json with every SHA-256.

- **Independent verification:** 340 checks, all passed (a separate script recomputed every draw from the DRAFT spec before reading build_sealed.py).
- **Decisions recorded with this commit (lead, before any Gate B run):**
  - M_u,d seeds use derive_seed(20261008, "gate-b-length-matched-v2", d, u, b) with u = the unit's group id and b = the 0-based bin index (the DRAFT did not say; both builder and verifier chose this independently).
  - Unit removal in waves 1–2 and the length control uses these sealed edit files (arm edit-<SHA-256>), not the engine's native group arms, so every Gate B arm has the same form.
  - build_sealed.py is frozen: the edit files embed its SHA-256, so any byte change would change every arm hash.
  - gate_c_sample.json's schema is provisional until engine X defines what the attributes job reads; a new schema would give a new SHA-256 for the same 1,600 rows.
- Per-unit table (unit_table.json): the short-answer categories are classification (37.5% of answers under 16 tokens; first-5-token share 0.288), open_qa, closed_qa and information_extraction; creative_writing is the longest (1.5% short; 0.055).
