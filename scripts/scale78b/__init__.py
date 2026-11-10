"""The 7-8B tier's own $0 scripts (P78 section 9.2; the readiness plan T3, T5, T6a; the lead's Part 1 rulings of
5 Nov 2026 and their addendum). New files only: the engine, the stage-1 builders under scripts/stage1/, the Gate B
pinned readers, every sealed file and runkit/ stay untouched.

Track B (T3): build_r_draws_78b.py (OLMo-2-7B R_d11-R_d16 on the frozen Gate B builder, loaded by path and pinned) and
build_h1_llama3.py (H1 on the Llama manifest by the stage-1 length rule, imported read-only). The Llama sealed set's
own wrapper lives beside its output, .ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py.

Track C (T5, T6a, the Llama G1 check): noise_reading.py (N's reading and the seed rule), make_recipe_s78.py (the
recipe-S_78 maker) and g1_check_78b.py. Each loads the frozen Gate B reading (scripts/gate_b_reading.py) by path and
pins its SHA-256; nothing is copied from it."""
