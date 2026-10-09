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
- **Next:**
  1. The screen, once the lead's pod Granite mode lands.
  2. sf_screen refill, then final data and configs.
  3. The preparer run.
  4. The post-screen swap, in each KIT-README §3.
  5. Freeze the pre-registration and send its hash to the lead for FOCUS.
  6. The lead launches the two a0 kits; after they are sealed, initialise and launch the four seed kits (README §4).
