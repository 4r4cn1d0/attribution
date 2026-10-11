# Pre-registration: the Scheduled recipe on a third family at 1B (Qwen2.5-1.5B)

Written 2026-10-11T04:45:14Z (clock checked) by the Side Project chat, **before any Qwen2.5-1.5B Scheduled run exists**. The user approved
three seeds in the Side Project chat on 11 Oct 2026 ("Qwen-1.5B Scheduled, 3 seeds"), about $13. Development evidence.
Not edited after the first launch. Later facts go in dated addenda.

## Question

At 1B, the Scheduled recipe cut OLMo-2-1B's erosion by 16.3 pp (logit -0.69) but Llama-3.2-1B's by only 2.2 pp (logit
-0.11). Which pattern does Qwen2.5-1.5B follow? With the 7-8B replication not showing the interaction (interim data), a
third family tells whether OLMo or Llama is the unusual one at 1B.

## Design

- **Qwen2.5-1.5B Constant:** study-kt-instruct-r64-b-20261007 (config_sha256 787ccff0...). Engine-X seeds 1101, 1102 and
  1103 are known: U 479, 444 and 456 of 600 (E +75.17, +69.33, +71.33 pp).
- **Qwen2.5-1.5B Scheduled:** study-kt-instruct-r64-g-20261008 (file 51be32be..., config_sha256 f5005e8e...). Checked
  now: against the Constant file, only name, purpose and the five 1B B->G train keys differ (token-mean loss,
  warmup_cosine, 4 warmup steps, schedule until e1); LR 1e-4.
  - Seeds 1101, 1102 and 1103 are new. Each is fine-tune only on the engine-X untuned unit of sp-qwen15-b-1101.
- **The 1B comparison cells (all known, from Appendix A of the note):**
  - OLMo-2-1B Constant U 280, 281, 308; Scheduled U 193, 205, 178.
  - Llama-3.2-1B Constant U 458, 451, 407; Scheduled U 443, 422, 412.

## Tests (fixed now; the hashed script research/side-notes/scripts/interaction_test_20261011.py, SHA-256 798e6c03...)

- **T1, Qwen against OLMo:** the OLMo-1B cells go in the script's "olmo" slot and Qwen in its "llama" slot, so I is
  D_OLMo - D_Qwen.
  - Label "OLMo's change is more negative" if the 95% interval excludes 0 with I < 0.
  - "Qwen's change is more negative" if it excludes 0 with I > 0.
  - Otherwise "not shown".
- **T2, Qwen against Llama:** Qwen goes in the "olmo" slot and Llama-1B in the "llama" slot, so I is D_Qwen - D_Llama.
  The labels are the same, in the same sense.
- **Descriptive:** Qwen's own D, with a Welch interval, in logit and in pp; HarmBench from the units' judge pod.
- Two tests are run, with no multiplicity adjustment. This is disclosed.
- The families' cells come from different engine identities: Qwen engine X; the OLMo and Llama 1B units are as in the
  note's Appendix B. Each family's two cells share one engine, so every within-family change compares units on one
  engine.

## Predictions

- **P1:** Qwen behaves like Llama. The Scheduled recipe barely moves Qwen's erosion: mean E point +66 pp, range +55 to
  +75; logit D between -0.4 and 0.
- **P2:** T1 reads "OLMo's change is more negative".
- **P3:** T2 reads "not shown".

## Rules

As in the other pre-registrations of 11 Oct:
- one re-run, only after an infrastructure failure;
- "not tested" for a cell with fewer than 2 seeds;
- every unit is reported.

## Addenda
