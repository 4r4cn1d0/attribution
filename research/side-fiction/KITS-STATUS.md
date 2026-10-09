# Fiction run kits: status

Written 2026-10-09T16:42 UTC (inserted by the shell). The kits live in the main checkout's tmp/ (the budget guard reads kits only there). This file records their state on the Side Project branch.

| Kit (main checkout tmp/) | Host | Role | Cap (upper cost at $1.85/h) |
|---|---|---|---|
| family-probe-sp-fiction-dark-a0 | sp-fic-dark-1101 | untuned a0 plus seed 1101 | 4.75 h ($8.79) |
| family-probe-sp-fiction-dark-seed1102 | sp-fic-dark-1102 | fine-tune only on dark a0 | 5.0 h ($9.25) |
| family-probe-sp-fiction-dark-seed1103 | sp-fic-dark-1103 | fine-tune only on dark a0 | 5.0 h ($9.25) |
| family-probe-sp-fiction-light-a0 | sp-fic-light-1101 | untuned a0 plus seed 1101 | 4.75 h ($8.79) |
| family-probe-sp-fiction-light-seed1102 | sp-fic-light-1102 | fine-tune only on light a0 | 5.0 h ($9.25) |
| family-probe-sp-fiction-light-seed1103 | sp-fic-light-1103 | fine-tune only on light a0 | 5.0 h ($9.25) |

- **State: PRE-SCREEN, hard-blocked.**
  - No kit has a plan.json, so launch.py, host.py, orchestrate.py and finisher.py all stop at the plan read.
  - The a0 kits hold plan.PRE-SCREEN.json on the dry preparation.
- **Code against the reviewed Llama seed kit:**
  - host.py (`95302419…`): MAX_PRICE 10.0 and a finite-price check; NaN, inf, None, bool and huge integers are refused.
  - probes.py and probe_constants.py: fiction probe keys; the prepared pins live only in PREPARED_MANIFESTS.
  - The patched pack_setup.py (invalidate_caches).
  - A new fiction_plan.py (`4f4c3570…`).
- **Reviews:** the builder's local checks passed. An adversarial review found READY WITH FIXES, with a full post-screen swap rehearsed on scratch copies. Fixes A–E are applied:
  - the swap's rm -f;
  - a content guard that refuses the dry or pre-screen sets, with fiction_plan.py deciding pre-screen by content;
  - the launch precondition (pre-registration frozen and in FOCUS);
  - seed caps 5.0 h;
  - the overflow-safe price check.
- **Expected cost:** six kits about $12–19, plus the screen pod about $2.4–5.6 and HarmBench about $0.5. The cap-based upper bound for the six kits is $54.58. The lead's record holds the approval at about $20; the user was asked to raise it to about $25 to avoid a stop partway.
- **Screen round 1: done** (recorded 2026-10-09T20:31Z, inserted by the shell). Pod `sp-fiction-screen-r1`, launched by General Implementation V, ran 18:22:53–20:08:48 UTC: exit 0, stop confirmed, about $3.16 at $1.79/h (the lead's report). The known-answer gate passed (200/200 identical; yes 93 on both). Granite: 20,000 of 20,000 records; Qwen3Guard: 14,800 rows. The lead's summarize step wrote `tmp/side-fiction/screen/round1-{dark,light,dolly}.jsonl` and `round1-summary.json` (`199a0ad5…`).
  - Rules-v2 drops: Granite harm flagged 167 dark and 40 light rows.
  - **The pre-registered sexual-content gate fired in both arms:** Qwen3Guard's sexual-category share of the rows that rules-v2 keeps was 1.26% (dark) and 1.05% (light), above 0.5%. So this chat issued **rules-v3** (`research/side-fiction/rules-v3.json`, `cd4e9bc4…`): drop on Granite harm OR Granite sexual_content. Qwen3Guard still drops nothing. Rules-v3 drops 179 dark and 47 light rows.
  - **Projection at issue:** Qwen3Guard's sexual-category share stays near 1% after rules-v3 (1.12% dark, 0.97% light), because the two judges seldom agree on sexual content. The remedy is the pre-registered one; the residual is reported with the final reads, and any further change is the user's decision (rules-v4).
  - Other round-1 reads (descriptive, before refill): the manipulation-check direction holds (dark's Unsafe and Violent shares above light's, both small); book concentration flags dark_b6 and light_b7 (each over 40% of its arm's Unsafe-labelled rows).
- **Screen round 2: prepared, not launched.** `sf_screen.py` (`adc3fcd7…`, its new `--screen-rules` option; self-tests pass, and without the option its final files are byte-identical to `165f1a30…`) wrote `refill-r2.jsonl` (`b5165add…`, 1,130 rows: 5 candidates for each of 226 dropped rows; no short list; 19 out-of-band fallback candidates) and `refill-r2-report.json` (`06d976ee…`). The screen kit's pins move to the revised tool and the revised SCREEN-SPEC (§9, `d880c746…`); its README and one test's copy of the tool pin change with them, and nothing else. The kit's MANIFEST.sha256 goes from `78d60319…` to `e55adf31…` (same 26 files; 3 changed). The development copy passed the kit's full suite (175 passed with SCREEN_SLOW=1).
- **Next:**
  1. The lead launches round 2 (`sp-fiction-screen-r2`) and runs its summarize step.
  2. sf_screen finalize with `--screen-rules` (round 3 only if a dropped row has no clean candidate), then final data and configs.
  3. The preparer run.
  4. The post-screen swap, in each KIT-README §3.
  5. Freeze the pre-registration and send its hash to the lead for FOCUS.
  6. The lead launches the two a0 kits; after they are sealed, initialise and launch the four seed kits (README §4).
