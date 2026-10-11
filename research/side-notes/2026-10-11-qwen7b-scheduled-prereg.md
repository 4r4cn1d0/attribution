# Pre-registration: the Scheduled recipe on a third family at 7B (Qwen2.5-7B)

Written 2026-10-11T05:07:08Z (clock checked) by the Side Project chat, **before any Qwen2.5-7B Scheduled run exists, and before its
config exists**. The user approved three seeds in the Side Project chat on 11 Oct 2026 ("#26 Qwen-7B Scheduled"), about
$15. Development evidence. Not edited after the first launch. Later facts go in dated addenda; the config hash goes in
addendum 1.

## Question

At 7-8B, does the Scheduled recipe move any family's erosion? The pre-registered 7-8B replication compares OLMo-2-7B with
Llama-3.1-8B (research/side-notes/2026-10-11-7b-replication-prereg.md). Qwen2.5-7B adds a third family at 7B, as
Qwen2.5-1.5B does at 1B (research/side-notes/2026-10-11-qwen-scheduled-prereg.md).

## Design

- **Qwen2.5-7B Constant:** study-kt-qwen7b-r64-b-mb2-20261007 (config_sha256 ba5c402f...). The engine-X seeds are known:
  U 522, 500 and 470 of 600; untuned 29 of 600; E +82.17, +78.50 and +73.50 pp.
- **Qwen2.5-7B Scheduled:** study-kt-qwen7b-r64-g-mb2-20261011. It is the Constant file with exactly the 1B B->G train
  change (token-mean loss, warmup_cosine, 4 warmup steps, schedule until e1; LR 1e-4), committed by the lead and
  checked in addendum 1.
  - Seeds 1101, 1102 and 1103 are new. Each is fine-tune only on sp-qwen7-b-1101's engine-X untuned unit.
- **The 7-8B comparison cells:** OLMo-2-7B and Llama-3.1-8B from the replication design, read when complete.

## Tests (fixed now; the hashed script research/side-notes/scripts/interaction_test_20261011.py, SHA-256 798e6c03...)

- **T5, OLMo-2-7B against Qwen2.5-7B:** I = D_OLMo7 - D_Qwen7.
- **T6, Qwen2.5-7B against Llama-3.1-8B:** I = D_Qwen7 - D_Llama8.
- The labels are the script's, two-sided, as in the 1B third-family pre-registration.
- **Descriptive:** Qwen-7B's own D, with a Welch interval, in logit and in pp; HarmBench from the units' judge pod.
- Two tests, with no multiplicity adjustment. This is disclosed.

## Predictions

- **P1:** the Scheduled recipe barely moves Qwen2.5-7B's erosion: mean E point +75 pp, range +65 to +85; logit D
  between -0.5 and +0.2.
- **P2:** T5 and T6 both read "not shown".

## Rules

As in the other pre-registrations of 11 Oct:
- one re-run, only after an infrastructure failure;
- "not tested" for a cell with fewer than 2 seeds;
- every unit is reported.

## Addenda
