# OLMo-2-1B "Constant, token-mean" (bt), seeds 1102 and 1103 (Side Project; report-only)

Recorded 2026-10-10T09:44Z (inserted by the shell). Development evidence. Counts only. Approved by the user on 9 Oct ("1-7 do it all"); the lead confirmed the envelope in its chat and launched both kits at 22:58 UTC on 9 Oct after an independent review (READY).

- **Runs:** `sp-olmo2-1b-bt-1102` (finished 23:51 UTC) and `sp-olmo2-1b-bt-1103` (00:28 UTC), fine-tune only on OLMo's sealed untuned unit 1101-a0-init-a1, engine e49a978c (certified pair 55253874 → e49a978c, as for the bt 1101 run).
- **Readings** (the kits' README §6 command, paired with bt seed 1101; files `reading-olmo-bt-1101-1102-nojudge.json` and `reading-olmo-bt-1101-1103-nojudge.json` in the kits):
  - E per seed: 1101 +43.7, **1102 +39.5**, **1103 +42.5** pp → **mean +41.9** (sample SD 2.2). Class partial; answers end and the task is learned on every seed; verdict INCOMPLETE until the second judge.
  - Greedy E (Qwen3Guard): +35.5, +31.0, +33.5 (mean +33.3). Over-refusal: 9, 8, 5 of 100.
- **What it changes (I):** with three seeds of each recipe, Constant +45.1, Constant token-mean +41.9, Scheduled +28.8 pp. The token-mean loss accounts for about **0.20** of the Constant → Scheduled cut on the main measure (3.2 of 16.3 pp; Welch SE of the difference about 2.0 pp, so the share's interval includes 0). The schedule still explains most of the cut. The note's one-seed wording ("explains none") must change to this. On greedy answers the share is larger (Constant +41.5 → token-mean +33.3, Qwen3Guard).
- **Pending:** HarmBench and Granite on both units (the end-of-runs judge pod); held-out loss per seed for Tables 2 and 3.
