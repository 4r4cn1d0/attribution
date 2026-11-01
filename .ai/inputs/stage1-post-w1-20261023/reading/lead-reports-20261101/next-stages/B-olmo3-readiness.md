# OLMo 3 7B probe: what it needs, and whether to spend on it now (Task B)

Read-only scouting for the lead (GI VIII). Written 2026-11-01 at about 00:45 UTC (clock checked with `date -u`). This report adopts nothing. It authorizes no spend, download or install. Every fact has a `path:line` source.

All paths are relative to the main checkout `/Users/spiderishi/Coding/attribution` (branch `stageb-costs-and-recovery-safeguards-20261003`). Labels: **M** = measured here (a command I ran). **E** = my estimate. **I** = my inference.

## Source key

| Short | Path |
|---|---|
| PLAN | `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md` |
| UI | `.ai/inputs/stage1-post-w1-20261023/reading/user_instruction_keep_working_20261031.json` |
| O3A | `research/review/2026-10-17-olmo3-7b/olmo3-7b-addendum.md` (the OLMo 3 plan, DRAFT) |
| MC | `research/review/2026-10-17-olmo3-7b/model-check.md` |
| CM | `research/review/2026-10-17-olmo3-7b/compat-memory.md` |
| KCR | `research/review/2026-10-17-icml-78b-prep/78b-kit-cap-rule.md` |
| FOCUS | `research/FOCUS.md` |
| README | `README.md` |
| SPF | `docs/study-plan-full.md` |
| PR4 | `research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` |
| S1K | `runkit/stage1-olmo/` (the tracked copy of `tmp/stage1-olmo/`) |
| FPK | `runkit/family-probe/` |
| PRE-F | `scripts/cuda_preflight_family.py` |
| LOCK | `experiments/minimal_safety/requirements.lock` |
| ID | `experiments/safety_selection/common.py` |

---

## 0. The answer in brief

- The OLMo 3 rules are a DRAFT that adopts nothing (O3A:3). The addition itself is the user's decision of 17 Oct (FOCUS:158).
- None of the probe's $0 build exists. There is no lock, no kit entry, no prepared set and no new preflight (section 1.7). So the probe cannot launch today at any price.
- The three blockers need about **11–21 builder hours** (E). The whole probe-only build needs about **2–3 builder days** plus review (E). Two of the three blockers need a user approval first: the tokenizer download and a Mac install.
- The probe pod costs about **$4.33 expected, $5.29 upper, $10.95 if every batch hits the cap** (O3A:71). Its cap is 7.0 h and its guard $18.95 (O3A:101).
- About $23.94 is usable. Stage 1b ($17–35) comes first in the plan. Stage 1b plus the cheapest probe path is $23.19–44.35 (M). So the draft's own money check C1 fails.
- **Recommendation:** do not run the probe. Do not start the $0 build yet. Ask the user one question now. **Default: OLMo 3 goes to level 0 on 13 Nov.** **Trigger to prepare and run:** by 8 Nov the user commits option B's money and gives the two approvals (section 4).

---

## 1. The plan

### 1.1 Status

- The rules file says: "Status: DRAFT. It adopts nothing." (O3A:3). The full plan lists it as a draft (SPF:39).
- The user confirmed the addition on 17 Oct: a third 7–8B model if funded, keeping OLMo-2-7B and Llama-3.1-8B, and the first 7–8B model cut if money is short, after 70B and 32B (FOCUS:158).
- The frozen stage-1 pre-registration records this as FR-24. It leaves OLMo 3's rules to the 7–8B pre-registration (PR4:75, PR4:1041; `research/experiments/2026-10-17-stage1-preregistration-rev3/decision-ledger.md`:73).
- The 7–8B pre-registration is also a draft. Its freeze deadline lapsed (README:95).
- The lead's plan restates the cost and the 13 Nov rule (PLAN:61).

### 1.2 The levels (O3A:21-28; README:99; SPF:533)

| Level | What runs | Spend (E, with +20%) |
|---|---|---|
| L0 | nothing; OLMo 3 is named as a limitation | $0 |
| L1 | Gate A: the untuned unit + 3 seeds at the chosen rung (up to 3 rungs) | $16–44 ($6–9 if rung 1 reads weak and OLMo 3 stops) |
| L2 | L1 + the noise block R_1–R_3 | $27–57 |
| L3 | L2 + the full comparison at plan A (the default) | $266–390 |
| L4 | L3 + a 7–8B confirmation (not recommended) | $329–491 |

- The default is L3. The fallbacks are L2, L1 and L0. Their triggers are money and the calendar only (O3A:177).

### 1.3 The rung probe at seed 1101

- **Rule.** The learning rate is the highest of 1e-4, 5e-5 and 2e-5 whose erosion probe reads partial (20–55 pp) under the frozen family-probe bars. It is chosen from erosion probes only (O3A:193).
- **R1.** One probe pod runs the untuned unit (evaluation only) and seed 1101 at 1e-4 (O3A:196).
- **R2.** Read seed 1101 alone (O3A:197-201):
  - partial, with no edge inside E ± 2·SE: rung 1 is chosen;
  - TOO CLOSE: seed 1102 at the same rung, after the user's go (pre-set answer P0 would give it);
  - saturated (E > 55 pp, or U_ft > 75%): go to rung 2;
  - weak (10–20 pp) or too little (< 10 pp): stop at L1.
- **R3, R4.** Seed 1101 at 5e-5, then at 2e-5. If no rung reads partial, stop at L1 (O3A:202-203).
- **R5.** The remaining Gate A seeds at the chosen rung, then the 3-seed Gate A reading (O3A:204).
- The other one-seed bars are read at the same time. A definite FAIL stops OLMo 3 at L1 (O3A:206). Granite's direction comes later from a judge pod (O3A:208).

### 1.4 The 13 Nov rule and the money checks

- **Calendar rule:** "If the probe pod has not launched by 13 Nov, OLMo 3 goes to L0" (O3A:288; README:100; PLAN:61). The draft's latest launch was 2 Nov; 13 Nov is the hard date (O3A:38, O3A:133).
- If Gate A is not read by 20 Nov, check C3 cannot fund L3 (O3A:288).
- **Money checks** (O3A:283-286; SPF:529):
  - C1 before the probe pod (latest 2 Nov), for L1 and L2;
  - C2 before the noise pod (latest 16 Nov);
  - C3 at the 20 Nov gate, for L3;
  - C4 before OLMo 3's block B (latest 7 Dec).
- **What each check needs.** The free balance must cover the running commitments and the guard, the next needs of every item ranked above OLMo 3 up to its next funding gate, and the next OLMo 3 level's planning spend (O3A:287).
- **The money effect.** L1 and L2 spend before 20 Nov lowers the money at the B/C gate. The draft recommends one more condition for C1 and C2: the account, or an award in writing, covers option B's F2 low end ($900) plus OLMo 3's next step (O3A:293; SPF:538). This was a user item due 31 Oct (O3A:398). I found no answer (section 1.7).
- **Pre-set stops.** A weak rung 1, no partial rung or a Gate A FAIL stops OLMo 3 at L1 (O3A:289). No OLMo 3 result decides a cut (O3A:291).

### 1.5 Its role: option B of the 7–8B tier only

- OLMo 3 runs under option B only (O3A:176; README:99; SPF:525). Under option C it runs no L3. Report-only L1 or L2 under C need the user's word; the default is no (O3A:176, O3A:397).
- Option B is the full comparison on OLMo-2-7B and Llama-3.1-8B plus confirmation. B or C is chosen about 20 Nov by the money in the account and the noise reading (README:93).
- Money: B $1,180–1,760; C $770–1,160 (README:95; PLAN:62). B needs about $900–1,300 more by about 20 Nov (SPF:521). With OLMo 3 at L3, B is about $1,450–2,150 (O3A:339).
- Cut order: 70B, then 32B, then OLMo 3 at its next level boundary, before every other cut (O3A:361-362; FOCUS:158).
- Purpose: a "same lab, newer data and recipe" contrast with OLMo-2-7B (SPF:527; MC:84).

### 1.6 The three blockers, as the records state them

- "Blockers: transformers ≥ 4.57.0, the chat-template download, a new preflight script. No unit has run." (README:101).
- The same three appear in MC:18-21, SPF:531 and FOCUS:158.

### 1.7 What has happened since 17 Oct

- **No OLMo 3 file exists** (M). No file name holds `olmo3` or `olmo-3` under `experiments/`, `scripts/` or `runkit/`. `tmp/` has no such top-level entry. The Hugging Face cache has no OLMo 3 snapshot.
- **No user item is recorded.** The draft's user items were due 24 and 31 Oct: the tokenizer download, the Mac venv, the input choices, the pre-set answers P0–P4 and the money-effect option (O3A:388-398). FOCUS mentions OLMo 3 only at lines 75 and 158 (M: grep). The 17 Oct "Saying yes to all" covered Gemma, the OLMo-2-1B base, the public copy and the funding note, not OLMo 3's tokenizer (FOCUS:151).
- **No lead task is done.** The draft's lead tasks were due 26–31 Oct: kit route, lock, pins, codec check, prepared set, preflight, recipes, predictions, state rule (O3A:402-410).
- So the draft's 2 Nov launch cannot happen. Only the 13 Nov hard date remains (I).

---

## 2. The three blockers in detail

| # | Blocker | What is needed | Files that change | Frozen engine identity | Needs the user | Hours (E) |
|---|---|---|---|---|---|---|
| B1 | transformers ≥ 4.57.0 | An OLMo 3-only lock (LOCK with one line changed to 4.57.1), then the checks under it | A new lock file outside `experiments/`; the new kit's pack step. Not `constraints.txt` | Code identity unchanged. The environment (lock hash) changes | Yes: a Mac venv install (O3A:391) | 5–9 |
| B2 | the chat-template download | `chat_template.jinja` in the OLMo 3 download patterns and in a new Mac fetch entry; then the codec check, data config and prepared set | The new kit entry, a new Mac fetch entry, a new data config, a new prepared folder. Not `assets.py` | Unchanged, if `assets.py` stays unedited | Yes: the tokenizer download, about 9.7 MB (O3A:390) | 2–4 |
| B3 | a new preflight script | A new script that compares the chat rows with the unused `<|extra_id_N|>` rows by a cosine or distance rule | A new script outside `scripts/` until committed; the new kit's preflight step. PRE-F unedited | Unchanged | No (a lead rule, D-O4) | 4–8 |

### 2.1 B1: transformers ≥ 4.57.0

**Facts.**
- LOCK pins transformers 4.56.2 (LOCK:29), peft 0.17.1 (LOCK:16), tokenizers 0.22.2 (LOCK:26), torch 2.8.0 (LOCK:27) and huggingface-hub 0.36.2 (LOCK:7).
- 4.56.2 has no `olmo3` code (CM:20, CM:68). The model card asks for 4.57.0 or higher. The config was saved with 4.57.1 (MC:43).
- In 4.57.6, `Olmo3ForCausalLM` is a subclass of `Olmo2ForCausalLM`. The only model changes are the sliding layers and two rotary embeddings (CM:70).
- 4.57.6 has the same dependency bounds as 4.56.2. So the OLMo 3 lock can be LOCK with one changed line. Whether peft 0.17.1 works with 4.57.x is unverified (CM:71-72; MC:223; O3A:432).

**What changes.**
- A new lock file for OLMo 3 only, transformers 4.57.1 recommended (O3A:185, O3A:403; CM:205).
- Both kits pack LOCK by path (FPK `pack_setup.py`:87, :138; S1K `pack_setup.py`:504). Both bootstraps install torch 2.8.0 for CUDA 12.8 and then that lock (S1K `setup/bootstrap_hr.sh`:21-22; FPK `setup/bootstrap_hr.sh`:6-7). So the OLMo 3 kit must pack its own lock (CM:136).
- Keep the new lock outside `experiments/minimal_safety/` and `experiments/safety_selection/`. The stage-1 pack bundles every `.lock` there (S1K `pack_setup.py`:194-200). It refuses any uncommitted file under `experiments/` or `scripts/` (S1K `pack_setup.py`:179-183). The draft gives the same rule (O3A:300; CM:74).
- **`constraints.txt` does not change.** The stage-1 kit's file holds one line, `setuptools==78.1.0` (S1K `setup/constraints.txt`:1; pin S1K `stage1_rules.py`:57). The bootstrap and the pack refuse any other content (S1K `setup/bootstrap_hr.sh`:14-16; S1K `pack_setup.py`:188-191). The transformers pin belongs in the lock (I).
- **The stage-1 kit's lock pin refuses it.** The kit pins the pod lock's hash `7e0dd998…` (S1K `stage1_rules.py`:412). It stops a pod whose lock SHA-256 differs from its reference at BOOTSTRAP-READY (S1K `orchestrate.py`:273-276, :280-282; fields S1K `stage1_rules.py`:635). An OLMo 3 lock freezes to another hash (I). The OLMo 3 kit records its own reference fixture on its first pod (CM:130).

**Engine identity.**
- The code identity hashes the `safety_selection` `.py` files and seven reused `minimal_safety` modules (ID:28-36). A lock is not part of it. So engine X stays `472fc7f6…` (S1K `stage1_rules.py`:324; CM:57).
- But engine X is certified only under 4.56.2 (CM:146). OLMo 3 units carry another environment. Every cross-family contrast with OLMo 3 carries a library-version difference, stated as a limit (O3A:185; SPF:532).

**Work (E): 5–9 h.** Lock text 0.5 h. Venv install and `pip check` 0.5–1 h. The engine's CPU suite under 4.57.1, 1–2 h (more if a golden test differs; U). A tiny `Olmo3ForCausalLM` test and the LoRA count (`scripts/family_lora_count.py` exists, M), 2–3 h. The kit's lock-path change with a test, 1–2 h.

### 2.2 B2: the chat-template download

**Facts.**
- OLMo 3 keeps its chat template in a separate file, `chat_template.jinja` (2,613 B). Its `tokenizer_config.json` has no `chat_template` key (MC:124-125, MC:149).
- The family-probe kit's open-repository patterns have no `*.jinja` (FPK `probes.py`:17). They go to `snapshot_download` as `allow_patterns` (FPK `setup/download_models_probe.py`:84-86).
- The Mac fetch has fixed families with blob pins, `olmo2` and `llama3` only (FPK `fetch_tokenizers_mac.py`:27-41).
- The engine's own lists also lack the file (`experiments/safety_selection/assets.py`:25-28).
- Without the file the template probe fails before any training (MC:181; CM:23).

**What changes.**
- Add the file by name to the OLMo 3 probe entry. Add a new Mac fetch entry with blob pins for the six files, read by a direct Hub API read (CM:134-135; O3A:404).
- Then run the codec check (`scripts/family_codec_check.py` exists, M) with end `<|endoftext|>`, stops `<|endoftext|>` and `<|im_end|>`, pad `<|pad|>` and header `<|im_start|>assistant\n` (CM:195).
- Build the data config `study-kt-data-dolly-olmo3.json` with `<function` and `</function` forbidden (O3A:186; CM:95). Build the prepared set `prepared-kt-dolly-olmo3`. Its `construction_sha256` must equal `2f5802f5…`, or the lead records an amendment (O3A:186; CM:195).
- These steps run in the existing 4.56.2 venv. They need only the download (O3A:405; CM:121).
- **Do not edit `assets.py`.** It is one of the engine's `.py` files, so an edit changes the engine identity (ID:34; CM:147). Record the template's blob in the fetch receipt and in the data config's amendment text instead (CM:119).

**Needs the user.**
- The download of six tokenizer files, about 9.7 MB, no weights (O3A:390). The 31 Oct instruction keeps "a new data download needing approval" with the user (UI:9).
- Two input choices go with it: keep the template's default system block in every prompt, and end of turn `<|endoftext|>` with both stops. They are fixed before the first fine-tune (O3A:187, O3A:392; CM:203-204). They are choices about the model's input (CM:94).

**Engine identity:** unchanged, if `assets.py` stays unedited (I).

**Work (E): 2–4 h** after the user's yes.

### 2.3 B3: a new preflight script

**Facts.**
- PRE-F compares the chat rows with padding rows (more embedding rows than tokens) or with `<|reserved_special_token_N|>` rows; otherwise the kind is "none" (PRE-F:94-103).
- With no comparison rows, `chat_rows_distinct` is null (PRE-F:109-110). `use_this_recipe` needs every part to be True (PRE-F:231-233, :242).
- OLMo 3 has 100,278 embedding rows for 100,278 tokens and no reserved-token names (MC:95; CM:125). So every OLMo 3 candidate is refused (MC:21, MC:182).

**What changes.**
- A new script, for example `cuda_preflight_olmo3.py`. It imports PRE-F's helpers and adds a comparison rule on the seven unused `<|extra_id_N|>` rows (100256, 100270–100275). The rule should be cosine or distance, not bit identity. It is fixed before the first pod (CM:126-127, CM:206).
- PRE-F stays unedited (O3A:299; CM:218).
- The new kit's preflight step calls the new script. The OLMo 3 expected fixture is recorded fresh on its first pod (CM:130).
- **Where it lives matters.** The stage-1 pack bundles PRE-F by name (S1K `pack_setup.py`:76-77). It refuses any uncommitted file under `scripts/` (S1K `pack_setup.py`:179-183). So the draft script waits outside `scripts/`, or is committed by explicit path while no stage-1 pack runs (O3A:304).

**Engine identity:** unchanged. `scripts/` is outside the 29 hashed files (ID:28-36).

**Work (E): 4–8 h.** Rule and script 2–3 h. A unit test of the rule on synthetic rows 1–2 h. A tiny-model run under the 4.57 venv 1–2 h. Review 1 h.

### 2.4 The kit route (not one of the three blockers, but the probe needs it)

- The stage-1 kit is bound to OLMo-2-1B. It names the prepared set `prepared-kt-dolly-olmo2` and the probe key `olmo2-1b` (S1K `stage1_rules.py`:631, :633), the OLMo-2-1B Instruct pin (S1K `stage1_rules.py`:418) and its lock pin (S1K `stage1_rules.py`:412). It cannot host OLMo 3 unchanged (I).
- The 7–8B kit `runkit/stage1-78b/` was only a proposal (SPF:503). `runkit/` holds `family-probe`, `gate-b-olmo`, `kill-test-stage0` and `stage1-olmo` only (M: `ls`).
- The draft's lead choice: the 7–8B kit if it can run "untuned + a0", otherwise a family-probe copy at a new path for Gate A only (O3A:402). The family-probe kit ran both 7–8B probes. Its OLMo-2-7B entry shows the shape of a new entry (FPK `probes.py`:38-46).
- I recommend the family-probe copy for the probe (E: the least new code).
- Work (E): 6–10 h for the copy, an OLMo 3 entry (open repository, three shard pins, the jinja pattern, the new lock path, the new preflight, a 7.0 h cap), its tests and a dry pack.

### 2.5 The rest of the probe's $0 build, and the total

- Still needed: recipes for 3 rungs × mb2, mb1-gc and mb2-g16, with a new date suffix (O3A:184, O3A:407); the pins by a direct Hub read (O3A:404); the ids-only control-token count and a copy of the Gate A tool (O3A:189); the predictions (O3A:307-313, O3A:409); the state rule (O3A:410).
- Still needed from the user: the input choices and the pre-set answers P0–P4 (O3A:392-393).
- **Total (E).** The three blockers: 11–21 h. With the kit copy and the rest: about 25–40 h, so about 2–3 builder days plus review. The draft put the whole $0 build at about 4–6 days (O3A:323).

---

## 3. The probe's cost, and what it decides

### 3.1 The measured basis

- Nine OLMo-2-7B units ran on A100-SXM4-80GB at $1.79/h on engine X (O3A:46; KCR:70):
  - fine-tune-only job: 86.1–107.5 min, median 90.9 (n = 8);
  - a job with the untuned evaluation too: 114.6 min (n = 1);
  - pod overhead: 21.8–41.8 min, median 30.4 (KCR:74-76; SPF:503).
- The architecture factor is 1.00, because OLMo 3 has OLMo-2-7B's shapes (O3A:57; MC:16).
- The probes that produced these times: OLMo-2-7B seed 1101 at 1e-4 read E = +49.67 pp (FOCUS:196); the two-seed mean was +43.42 pp, partial (FOCUS:194).

### 3.2 The probe pod

One 7B LoRA fine-tune (38 steps) and two evaluations: the untuned unit and seed 1101's e1 (O3A:196; KCR:75).

| Case | A100-hours | Cost at $1.79/h |
|---|---|---|
| Expected (114.6 + 30.4 min) | 2.42 | $4.33 |
| Upper (114.6 × 107.5/90.9 + 41.8 min) | 2.96 | $5.29 |
| Every generation batch at the cap | — | $10.95 |

- Source: O3A:71, O3A:77. My arithmetic reproduces $4.33 and $5.29 (M).
- Cap 7.00 h. Guard $6 + 7.0 × $1.85 = $18.95 (O3A:101; the rule is S1K `stage1_rules.py`:14-16).
- A stop before the job costs $0.55–1.10. The first pod is the first real test of the new lock (O3A:93).
- Paths, with +20% and judges (O3A:85-88):
  - G0, rung 1 weak, stop: $6.19–9.35;
  - G1, rung 1 chosen, two more seeds: $15.88–23.04;
  - G2, rung 2 chosen: $20.22–33.73;
  - G3, rung 3 chosen: $24.56–44.42.
- Judges cost $2–6 (O3A:92). Each extra rung is a fine-tune-only pod: $3.62 expected, $4.45 upper (O3A:72).
- If every batch hits the cap, a fine-tune-only job takes about 176 min, not 91 (O3A:64).
- **A stale figure.** The draft's "about $103 in the account" includes Gate B's $83.91 hold (O3A:32, O3A:101). Gate B is complete (README:57; FOCUS:77), so the hold no longer binds (I). Under today's rule the pod alone needs its $18.95 guard. The live-balance guard is off by the user's 25 Oct decision (S1K `stage1_rules.py`:47-52). The lead's safeguard is to launch only when the live balance covers the cap-based spend (ADD:635).

### 3.3 The money now

- Balance $29.94 at 22:13 UTC on 31 Oct; idle spend about $0.04/h (PLAN:14; FOCUS:75). Reserve $6 (S1K `stage1_rules.py`:46; UI:8). **Usable: about $23.94** (M).
- Before OLMo 3 in the plan's order: the reading's step-1b pod, about $1 (PLAN:31); stage 1b, $17–35 (PLAN:57); then stage 1c, the human check and stage 2 (PLAN:58-60).
- Stage 1b + the G0 path = $23.19–44.35. With the $1 pod: $24.19–45.35. Stage 1b + G1 = $32.88–58.04 (M). Each is above $23.94. So C1 fails on the balance (I, by O3A:287).
- The probe pod alone fits its guard ($18.95 ≤ $29.94). But it would leave $19.0–25.6, which is $13.0–19.6 above the reserve. Stage 1b needs $17–35 (M).
- Option B needs about $900–1,300 of new money by about 20 Nov (SPF:521).
- No grant award is recorded. Three grants were submitted on 13 Oct, none awarded. The Transformative AI Fund decides about 24 Nov – 8 Dec, after the 20 Nov gate (FOCUS:179).
- The latest top-up was $40 (FOCUS:78). The balance reached −$0.02 on 31 Oct (FOCUS:79).

### 3.4 What the probe decides, and what it does not

**It decides:**
- OLMo 3's learning rate, by the per-family rule (O3A:193-204).
- Whether OLMo 3 stops at L1: a weak or too-little rung 1, or a definite one-seed FAIL (O3A:201, O3A:206).
- Whether a TOO CLOSE seed or the next rung is needed (O3A:199-200).

**It also measures, for the first time on OLMo 3:** the lock and the new preflight on a real GPU, the memory ladder, which end token the model emits, and answer length, which sets the cost basis (O3A:63-65, O3A:93; CM:197; MC:205).

**It does not decide:**
- Gate A. Gate A needs three seeds and, later, Granite's direction (O3A:206-208, O3A:229-235).
- Option B or C. That reads money and the noise reading (README:93).
- Anything in stage 1 (O3A:292).

---

## 4. Recommendation

**Do not run the probe. Do not start the $0 build yet. Ask the user one question now. Default: OLMo 3 goes to level 0 on 13 Nov. Trigger to prepare and run: by 8 Nov the user commits option B's money and gives the two approvals.**

### 4.1 Default, from now

1. Spend nothing on OLMo 3. Keep the $23.94 for the reading's step-1b pod and stage 1b, in the plan's order (PLAN:57; UI:7).
2. In the lead's next report, ask the user the question in 4.6.
3. Do no OLMo 3 builder work before the answer. Builder time goes first to the reading's preparation 1a, 1c and 1d (PLAN:30-33) and to stage 1b's $0 kit round (PLAN:72).

### 4.2 Trigger to switch to "prepare and run"

All three, by **8 Nov, 23:59 UTC** (E: about 2–3 builder days plus review must fit before 13 Nov):
- (a) The user says option B's new money (about $900–1,300; SPF:521) will be in the account, or awarded in writing, by 20 Nov. This is the draft's own recommended C1 condition (O3A:293).
- (b) The user approves the tokenizer download (six files, about 9.7 MB) and a separate Mac venv with transformers 4.57.1 (O3A:390-391).
- (c) The user fixes the input choices and P0–P4, or delegates them to the lead (O3A:392-393).

Then:
- Build the probe-only subset (section 2). Keep it outside `experiments/` and `scripts/`, or commit it by explicit path while no stage-1 pack runs (S1K `pack_setup.py`:179-183).
- Launch the probe pod by 13 Nov from the new money, once C1 passes. Never use the money stage 1b needs.

### 4.3 Fallback

- **The trigger does not fire by 8 Nov:** record OLMo 3 at level 0 at the 13 Nov date (O3A:288) in a FOCUS entry. The paper names it as a limitation (O3A:23; SPF:540).
- **The user funds the probe but not option B:** still level 0. Under option C, OLMo 3 runs no L3, and report-only L1 defaults to no (O3A:176, O3A:397). The user may override; then L1 runs as a report-only set.
- **The user says yes after 8 Nov:** the lead checks whether the build can finish by 13 Nov. If not, level 0. The 13 Nov rule reads only the calendar (O3A:288).

### 4.4 Why not the other two options

- **"Run the probe now"** is not possible. No lock, kit entry, prepared set or preflight exists (section 1.7). Even if it were, C1 fails on the balance (section 3.3). It would take money stage 1b needs. It would skip the plan's order (PLAN:55-61; UI:7). And its result is used only under option B (O3A:176).
- **"Prepare the blockers at $0 now"** (the lead's item 4, PLAN:73-74):
  - two of the three blockers cannot be verified without the user's yes, for the download and the install (O3A:390-391; UI:9);
  - the build costs builder days (O3A:323) that the reading and stage 1b need first;
  - draft files left uncommitted under `experiments/` or `scripts/` would block every stage-1 pack, stage 1b's included (S1K `pack_setup.py`:179-183);
  - it pays off only if option B is funded, and no record supports that (FOCUS:179).
  One $0 question decides whether any of it is needed.
- **"Level 0 now, without asking"** is cheap. But it drops a user-confirmed item (FOCUS:158) without the user's word on money. The draft's own triggers are money and the calendar (O3A:177). Asking costs one message.

### 4.5 Decisions for the lead

1. Ask the user now (recommended), or let the 13 Nov date pass without asking.
2. If funded: may the probe run ahead of stage 1c, the human check and stage 2, to meet 13 Nov? The plan's order and the 31 Oct instruction say "in its order" (PLAN:55-61; UI:7). The reorder is driven by the calendar, not by an outcome (UI:10). But it changes an order the user approved.
3. The kit route: a family-probe copy at a new path (recommended, E) or a stage-1 kit fork (O3A:402). The stage-1 kit cannot host OLMo 3 unchanged (section 2.4).
4. Mark the draft's stale parts: the $83.91 Gate B hold in its money needs (O3A:32, O3A:99-107) and its 24 Oct – 2 Nov dates (O3A:129-133).

### 4.6 A draft question for the user (one message)

> OLMo 3 7B is the planned third 7–8B model. It runs only under option B, which needs about $900–1,300 more by about 20 Nov. Its first step, a probe pod (about $4–11), must launch by 13 Nov, or OLMo 3 drops to level 0. Today's balance ($29.94) is needed for stage 1b. Will option B's money be in the account by 20 Nov? If yes, may I download OLMo 3's tokenizer files (6 files, about 9.7 MB, from huggingface.co) and install a separate Mac environment with transformers 4.57.1? Without a yes by 8 Nov, OLMo 3 goes to level 0 on 13 Nov.

---

## 5. Weak points and limits

- Every OLMo 3 time and cost is borrowed from OLMo-2-7B. No OLMo 3 unit has run (O3A:429; README:101).
- Answer length is unknown. If every batch hits the cap, an arm costs about 1.9× as much (O3A:64, O3A:430).
- transformers 4.57.x with peft 0.17.1 is unverified (O3A:432).
- The hours in section 2 and the 8 Nov date are my estimates, not measurements.
- The 13 Nov rule sits in a file that adopts nothing (O3A:3). The README and the plan restate it as the rule (README:100; PLAN:61). If the lead treats it as non-binding, the real limit is 20 Nov: Gate A must be read by then for C3 (O3A:288).
- I read the tracked kit `runkit/stage1-olmo/`, not the installed `tmp/stage1-olmo/`. Round 33 changed installed hashes (FOCUS:78), so line numbers may differ there.
- I did not read the 7–8B pre-registration draft or the re-plan. Their figures reach this report through O3A, SPF and the README.
- I ran no code, test, kit command or network call.

---

## 6. Process

**Changed files:** only this report.

**Commands run (all read-only; exit 0 unless noted):**
- `date -u` (twice: 23:18 UTC on 31 Oct and 00:45 UTC on 1 Nov).
- `git -C <main checkout> branch --show-current`.
- `ls` of: the reading folder; `.ai/`; `.ai/inputs/`; `.ai/inputs/stage1-post-w1-20261023/` (top-level names only); `runkit/`; `runkit/stage1-olmo/` and its `setup/`; `runkit/family-probe/` and its `setup/`; `experiments/minimal_safety/`; `research/review/2026-10-17-olmo3-7b/` and `calc/`; `research/grant/`.
- `python3 -I` reads of `MANIFEST.json`: its structure, entry paths and roles. `head -c 3000` of the same file; it lists label keys and owner scripts, including plant label names, and no leaf identity.
- `find` over `research/`, `.ai/`, `docs/`, `runkit/`, `scripts/` and `README.md` with risky folders pruned and risky names excluded (see below). Then `grep` of that list for OLMo 3 patterns: 43 files. A wider pattern added 13 false positives.
- `grep -n`, `sed -n` and `cut` reads of FOCUS, README, SPF, PR4, ADD, the decision ledger, the freeze changelog, the grant dossier, S1K `stage1_rules.py`, `pack_setup.py` (both kits), S1K `orchestrate.py`, both `bootstrap_hr.sh`, S1K `constraints.txt`, FPK `download_models_probe.py`, FPK `fetch_tokenizers_mac.py`, S1K `download_models_stage1.py`, PRE-F, `assets.py`, ID, LOCK and KCR.
- Full reads: PLAN, UI, O3A, MC, CM, parts of KCR and SPF sections 9–12.
- Name-only searches: `find experiments scripts runkit -iname '*olmo3*' -o -iname '*olmo-3*'` (0 names; this walk was not pruned, and it printed nothing); `ls tmp | grep -i olmo3` (0); `ls ~/.cache/huggingface/hub | grep -i olmo-3` (0).
- Two commands failed: one `grep` hit ugrep's pattern-complexity limit, and one zsh line failed on an `====` expansion. Neither opened a sealed file.

**Not opened (hard rule 1):** `tmp/stage1-olmo/` `hosts/`, `judges/`, `judges-pending/` and `seals/`; `tmp/judge-pod/`, `tmp/judge-pod-dry/`, `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`; `.ai/inputs/stage1-post-w1-20261023/block-a/` and `block-b/` (their names appeared in one top-level `ls`; their contents were not listed); every folder named `units` or `eval`; every `COMPLETE.json`; every answer, label, guard-sample or judge-cache file; every path containing `plant` or `decoy`; all of `.ai/inputs/stage1-commitments-20261016/` except `MANIFEST.json`; the seven records the manifest classifies as sealed (used by path only). The pruned `find` also excluded paths with `judge`, `hidden`, `selector`, `bank`, `answer`, `label`, `guard` or `seal` in the name. I hashed nothing.
