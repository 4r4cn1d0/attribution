# The 7-8B tier's $0 checks (GI XI, 8 Nov 2026)

Run by General Implementation XI on the Mac, from the main checkout, under the network-deny sandbox with
`HF_HUB_OFFLINE=1` and the main venv (`tmp/minimal-experiment-20261002/venv/bin/python -I -B`). Counts, ids and hashes
only: every input was read by its exact path and pinned SHA-256 through the frozen readers the tools call, and no
prompt, response or answer text was printed or written. Code: `scripts/scale78b/encode_count_78b.py` (`132dcd5b…`)
and `scripts/scale78b/tau_l_78b.py` (`5a3f4eda…`) at HEAD `3ca3e21`; `scripts/scale78b/s1_olmo2_7b_check.py`
(`2a160990…`). Each `.json` is the tool's text-free record (written once); each `.out.txt` is its printout with the
exit status.

| Check (ruling) | Result | Record |
|---|---|---|
| S-pool lists' encode count, OLMo-2-7B (DESO items 6, 17; DESO3 item 38) | all accepted: S1 48/48 and 48/48; `s3_safe` 861/861 and 861/861; `s4_candidates` 512/512; `s3_subset` 855/855 and 855/855 (generation prompt; train pair) | `encode-count-olmo2-7b-lists.json` |
| The same, Llama-3.1-8B | all accepted (the same counts) | `encode-count-llama31-8b-lists.json` |
| The 400 PHTest prompts, Llama-3.1-8B (DES E1) | 400/400 accepted; LN-24's shortfall rule is not needed | `encode-count-llama31-8b-bank.json` |
| The same, OLMo-2-7B (informational) | 400/400 accepted | `encode-count-olmo2-7b-bank.json` |
| The anchor list, both families (informational, GXB O6) | harmful pairs 64/64, generation prompts 128/128, on both; the anchor job decides its own stops | `encode-count-*-anchor.json` |
| OLMo-2-7B τ_L from losses only (DES K2, GXB O9) | s = 0.0025692013329847124 nats (ddof 1; a0 1101-1103 at e1, 200 task rows each); τ_L = 2√2 × s = 0.00726679873914803 nats | `tau-l-olmo2-7b.json` |
| OLMo-2-7B S1 re-check with the merged script (DESO item 20) | the record equals round 4's byte for byte (`9b340bf5…`); verdict "equal as it stands" | `s1_olmo2_7b_check_record.json` |
| Llama-3.1-8B θ0's recipe against MAIN_F (GXB T-O4) | generation and guard blocks equal | `t-o4-llama-theta0-recipe-check.md` |

Inputs (paths and pinned SHA-256): S1 list `tmp/stage1-mac-runs-20261023/s-pool/s1.json` `389c20ad…`; `s3_safe`
`tmp/stage1-mac-runs-20261023/s-pool/s3_safe.pool.json` `6801652c…`; `s4_candidates`
`tmp/stage1-mac-runs-20261023/s-pool/s4_candidates.json` `798613c4…`; the s-pool record
`.ai/inputs/stage1-commitments-20261016/s-pool/` (`bcca59ac…`); the PHTest bank
`tmp/stage1-mac-runs-20261023/oext-bank/oext_bank.json` `6487ed2b…` through its record
`.ai/inputs/stage1-commitments-20261016/oext-bank/oext_record.json` `a810574e…`; the anchor list
`tmp/gate-b-anchors/anchor_prompts.json` `78467c97…`; the OLMo-2-7B side a0 units by their COMPLETE.json pins
(`4a6d9ebc…`, `43e8412d…`, `4b5bd06d…`; RK KIT `a0_units`). Tokenizers: OLMo `48d788eca847`, Llama `0e9e39f249a1`
(the prepared manifests' revisions). Limits: `model.max_prompt_tokens` 1536 and `model.max_train_tokens` 3072 on
both main configs.

**What follows (I).** No list prompt fails on either family, so no reduced list or reduced s-pool record is built
(DESO2 item 33; DESO3 item 33 (b)), and Part 2 §15 item 15 is "not needed". Llama-3.1-8B's τ_L waits for N's
record-done (DES K2; DESO item 25). These values enter Part 2's [to be entered] places at the freeze.
