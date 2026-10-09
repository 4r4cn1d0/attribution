# Side Project: decisions for the user

> **Decisions, 2026-10-09 (clock checked 10:20 UTC):**
> - **Ownership:** side-project development is done in this chat, not offloaded. The lead presses launch on finished kits that this chat has reviewed.
> - **The fiction study is approved** at recipe B (FOCUS 09:29 UTC).
> - **The HarmBench add-on on the recipe-G side runs is binned:** it does not serve the main paper.
> - **Two Llama recipe-B seeds (1102, 1103) are approved** (about $4–5). The lead confirms the spend with the user before launch.
> - **The Qwen recipe-G run is binned** ("do whats recommended": not useful to the main paper; the Llama seeds carry the OLMo-against-Llama recipe test).
> - **The Hawkins-like Llama check stays approved.** It waits for its config to reach the main checkout.
> - **Later on 9 Oct:**
>   - fiction budget: "No budget do what needs to be done" (no cap; costs are still reported as they happen). In the lead's chat the user approved "up to about $20" (FOCUS entry stamped 15:23 UTC), and that is the figure the lead launches against;
>   - author name and affiliation: the user fills them in later;
>   - blind read: "give it to me and direct me what I need to do".

> **Update, 2026-10-08T19:21 UTC (clock checked).** The user decided several of these points through the lead (FOCUS "Decisions, 2026-10-08 17:36 UTC", commit `0bc5f1f` on the lead's branch). Where they conflict with this file's recommendations, the user's decisions stand:
> - **Recipe G is the common recipe** for both families in the main study, with an LR ladder (G at 1e-4, then 5e-5, then 2e-5). The Llama probe under G launched at about 19:10 UTC.
> - **Qwen spend for the arXiv note: approved ("do it").** The plan is Qwen2.5-1.5B under the common recipe, 1–3 seeds, with a fresh untuned baseline. Its recipe file and kit come from Specialized after Gate B Parts B and C. Then HarmBench on the Qwen units, about 50 human-read answers (the lead prepares the sheet), and a Substack post by the Public Posts chat. This supersedes C and B3 below.
> - **G+Qi reference arm in stage 1: approved ("Ok").** This supersedes this chat's "nothing now" recommendation in D below.
> - **Open point:** FOCUS names the Public Posts chat for the Substack post, while this chat's brief covers both the note and the post. The user decides who drafts and who polishes.

Written 2026-10-08T17:11 UTC (clock checked). Nothing below is approved. Costs are estimates. The RunPod balance was $12.93 at 16:49 UTC, and Gate B needs about $51–62 (about $33–44 with its extension and control declined), per the lead's DRAFT 4a/4b. So every paid item competes with Gate B. The lead is told before any pod or money is used.

Files: `2026-10-08-white-paper-outline.md`, `2026-10-08-substack-outline.md` (this folder) and `research/review/2026-10-08-refusal-opening-loss-options.md`.

## A. Free items (no money; need your go because they use the Mac GPU or your time)

| # | Item | Cost | Recommendation |
|---|---|---|---|
| A1 | HarmBench compliance judge on the Qwen 1.5B, Qwen 7B, Qwen r16 and Llama units (the generations are already on the Mac) | $0; about 8 h of Mac GPU (estimate); the lead's own HarmBench run is paused for swap | **Yes**, after the lead's OLMo HarmBench run finishes |
| A2 | Blind human read of about 50 answers against a 3-level rubric fixed before reading; this chat prepares a blinded file and never prints answer text | $0; 1–2 h of your time; you would read harmful text | **Yes**, if you are willing |
| A3 | Full screening disclosure and placeholders filled | $0; this chat | **Yes** (writing only) |

## B. Paid runs (each needs your explicit go; the lead drives every pod)

| # | Run | Cost | What it adds | Recommendation |
|---|---|---|---|---|
| B1 | Recipe G on OLMo-2-1B, seeds 1102 and 1103 | about $3–5 | "Recipe matters on OLMo" at 3 seeds. It may also count as the main study's mandatory "recipe G at 3 seeds" reference, if the lead confirms the pins match | **Yes, first paid item**, after a top-up |
| B2 | `bt` arm on OLMo: recipe B + token-mean loss only, seed 1101 | about $1.5 | Separates G's two changes; also informs the refusal-loss question | Yes, second, after a top-up |
| B3 | Recipe G on Qwen2.5-1.5B, 1 seed | about $3–4 | A direction only. One seed cannot pass the project's interaction MDE rule | **Skip** (see C) |
| B4 | Interaction version: Qwen B +2 seeds, Qwen G 3 seeds, OLMo G +2 seeds | about $20–25 | Can support "the family changes how much the recipe matters" | Only if funded beyond Gate B |

## C. The 7 October "no more Qwen spend" rule

- **My recommendation: keep it.** Post the note with title A ("One LoRA Recipe Near-Saturates Qwen2.5 and Llama-3.2 but Only Partly Erodes OLMo-2 at 1B"). Every claim in that version is supported now, except the placeholders in A1–A3.
- If you want the "family × recipe interaction" claim, B4 is the version that can carry it. B3 alone cannot.

## D. The refusal-opening loss

| Option | Cost | Recommendation |
|---|---|---|
| Nothing now (record the novelty check and the corrected ceiling) | $0 | **Recommended** |
| Prefill check: does a forced refusal opening stay safe? Decides whether any loss is worth building | about $0.5–1.5 plus Mac time | Optional, after Gate B funding |
| Reference arm G + Qi in stage 1, 6 seeds | about $12 plus 1–2 engine rounds; amends stage 1 | Only if the lead wants a model-level defence reference |
| Full experiment G vs G+Qi vs G+variant, 6 seeds each | about $38 plus 1–2 engine rounds | Not before Gate B |

Correction to the brief: the 0.42–0.64 "opening share" is a symmetric split, not a ceiling. On top of recipe G an opening loss could remove anything from about 0 to about 21 pp (sampled). The prefill check is what narrows that range.

## E. Logistics to check (no cost)

1. **arXiv endorsement.** First-time cs.LG submitters may need an endorsement (UNVERIFIED). Check your arXiv account early.
2. **Authors and affiliation** for the note.
3. **Main-paper venue policy.** FOCUS now targets TMLR or NeurIPS 2027 (ICML 2027 only if funded by about 1 December). The main paper cites the note and does not re-claim it.
4. **For the lead (not this chat's file):** the ICML draft's abstract and §1 say Llama-3.2-1B "replicates the comparison". Recipe B saturated Llama, so that wording now depends on L1 or L2.
