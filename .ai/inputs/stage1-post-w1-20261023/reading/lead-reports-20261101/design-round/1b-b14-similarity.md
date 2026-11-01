# Task 1b: B14's similarity pass (§9.4 overlap control)

Written for the lead by the Opus worker, 2026-10-31 at 23:58 UTC (clock checked with `date -u` at 23:57:25 UTC).
Read-only. The only file written is this report, in the scratchpad.

Paths are relative to the main checkout `/Users/spiderishi/Coding/attribution` (branch
`stageb-costs-and-recovery-safeguards-20261003`, HEAD `95f7a79`, checked). Short names:

| Short | Path |
|---|---|
| NEXT | `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md` |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` |
| REV4 | `research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` |
| PLAN-S | `research/review/2026-10-08-sharpened-direction-DRAFT.md` (SHA-256 `6ff3ff2b…`, checked) |
| W1R | `research/experiments/2026-10-16-stage1-commitments.md` (the W1 record) |
| SIM / SIMS | `scripts/stage1_s1/overlap_similarity.py` / `scripts/stage1_s1/settings/overlap_similarity.json` |
| STR / STRS | `scripts/stage1_s1/overlap_strata.py` / `scripts/stage1_s1/settings/overlap_strata.json` |
| KIT / RUN | `tmp/stage1-olmo/stage1_rules.py` / `tmp/stage1-olmo/setup/job_runner_stage1.py` |
| B15B | `tmp/gi-vi-handoff-20261027/notes/b15-brief.md` (the B15 build brief) |

---

## 0. Short answer

- **The finding holds.** No `similarity.json`, `strata.json` or `overlap_report.json` exists anywhere in the
  checkout. No kit job kind runs the pass.
- **It was planned and missed.** The plan required it "on the pod" (PLAN-S:172; W1R:129). No source put it in
  block A or block B. The kit's job list never had it. Nobody recorded the gap before 31 Oct (FOCUS:75; NEXT:31).
- **Running it now biases nothing.** The code reads only θ0, the 200 dev harm prompts and the three add sets. It
  reads no outcome. The strata must be sealed (SHA-256 in FOCUS) before any add-arm outcome is read.
- **New blocker (not in NEXT).** B14's *report* step, as pinned, refuses every unit trained with recipe S. Every
  stage-1 arm and every new a0 run used recipe S. So `overlap_strata.py report` will refuse at the first kit unit.
  The fix is a small settings re-pin. It must land **before** the strata are made, because the strata record
  carries the strata settings' hash and the report checks it. Details in §5.
- **Recommended route:** a kit round adds one job kind; one A100 pod runs the pinned script once. Cost about
  $0.60–0.75 (E). Fallback: a one-off pod with the same command. Last resort: B16's "not computed". The Mac route
  is not recommended: the committed script cannot run there, the weights are not on the Mac, and it would need new
  code that the engine forbids for scientific runs.

---

## 1. Verification of the finding

- `find` over the whole checkout for the three file names printed no path (23:57 UTC). It printed names only. I
  listed no forbidden folder.
- The kit has no such job. In KIT, RUN and `tmp/stage1-olmo/plan.json`, the words "similarity", "overlap" and
  "strata" occur 0 times each (`grep -o … | wc -l`).
- KIT:505-507 lists 20 job kinds (J1–J18, J20, J21). None runs SIM. KIT:619-626 maps blocks to kinds; no block has
  such a kind. The kit's S1 code pins (KIT:433-456) do not include SIM or SIMS, so the kit could not pack it.
- The B15 brief lists 19 job kinds (B15B:149-185) and two extra jobs, the A1 re-score and V2a (B15B:186-190). None is
  B14's pass. When the brief was written, the S1 package (with `overlap_similarity.py` `f8305c71…`) was not yet in
  main (B15B:54-58).

## 2. Where the plan scheduled it, and whether its absence was noticed

| Source | What it says | Block? |
|---|---|---|
| PLAN-S:172 | "report each eval prompt's highest similarity to the add set (untuned-model embeddings, **on the pod**)". It sits in §5.5, whose heading says "built on the Mac, CPU, $0" (PLAN-S:170), so the pod is a stated exception. | none |
| PLAN-S:214 | "the similarity strata" is one of the "New pinned scripts". A script, not a run slot. | none |
| PLAN-S:222-223 | Block A: arms, "diagnostics", c0. Block B: arms and references. | not named |
| W1R:129 (rule 10b) | "θ0 embeddings, on the pod; B14 builds the strata at S1". REV4:29 defines S1 as "before the stage-1 freeze, which comes before block A". | build deadline only |
| REV4:757 (§9.4) | The rule text (LN-26). No device, no block. | none |
| REV4:155-156 | "Other block-A contents" and "Block-B contents". The pass is not listed. REV4 §10 (from line 791) has no cost line and no sequencing step (§10.6, REV4:861-873) for it. | not listed |
| ADD:375 (§11 point 12) | "The SHA-256 of `strata.json` goes into FOCUS before any add-arm outcome is read." This is the only timing rule. | none |
| ADD:430-445 (§17), ADD:513 (§25) | B15's job kinds; block A's whole-block plan (S1-0, cert, diagnostics, LN-12, arms, judges). No similarity job. | missing |
| `research/experiments/2026-10-27-block-b-prep/reading-input/reading-input-build.json`, `does_not_exist_yet` (29 Oct 10:34 UTC) | "B14's strata.json SHA-256 is to be in FOCUS". It assumed the strata would exist. It did not note that no job makes `similarity.json`. | — |
| FOCUS:75 (31 Oct 22:15 UTC), NEXT:31 | First record that the pass never ran. | — |

**Verdict.** It was planned (PLAN-S:172, W1R:129, REV4:757, ADD:375) and missed. No source chose block A or block
B. Its natural slot was a θ0-only pod pass, like J5–J8 in block A. It could only run after the S3 and S4 edit files
existed: their file times are 25 Oct 15:42 UTC (S4) and 16:46 UTC (S3); S1's is 23 Oct 14:53 UTC (`stat`, local IST
converted). That is after block A's diagnostics pod started (FOCUS:120, 11:37 UTC). So any later block-A or block-B
pod could have carried it. The miss happened when B15's job list was fixed (ADD §17) and again at block A's plan
(ADD §25).

## 3. Does running it now bias anything?

**What the code reads** (it reads nothing else):
- From the prepared set, only `manifest.json` and `banks/dev.jsonl` (SIM:133-165). It never reads the selector or
  hidden bank (SIM:28-30).
- The three edit files, each checked against its SHA-256, each a pure add edit of 48 rows (SIM:176-207).
- The recipe, by its config hash (SIM:339-345). The model through the engine's loaders (SIM:355-360).
- Every vector is made under `torch.no_grad(), model.disable_adapter()` (SIM:375). So the LoRA adapter, and its
  random start, plays no part. θ0 is the untuned Instruct model.
- The output holds prompt ids, row ids, numbers and hashes. Texts are scanned out before writing (SIM:394-406).
- `strata` reads only `similarity.json` by its SHA-256 and the settings (STR:248-261). The split draws no random
  number (STR:148-163).
- No path leads to a unit, an `eval/` folder, a guard file, a seal or `plan.json`.

So the strata are a fixed function of θ0 (weights and tokenizer), the 200 dev harm prompts and the 144 added
prompts, plus the numeric environment. The add sets are the very files the arms trained on: `plan.json`'s S1, S3
and S4 arm jobs name the same paths and SHA-256 as in §4. Running the pass after the blocks gives the same numbers
it would have given in block A (same code, inputs and engine). No outcome can enter.

**What must hold:**
1. Nobody reads any stage-1 outcome of a0 or S1/S3/S4 (U, HB, O, task loss, coherence, guard files) before
   `strata.json`'s SHA-256 is in FOCUS (ADD:375; STRS:16).
2. `similarity.json` is made under the pinned settings `27db4c3f…`; `strata` refuses anything else (STR:222-225).
3. The add sets named are exactly `904a0cf1…` (S1), `a2f18a3d…` (S3) and `24aed3fb…` (S4). The report later checks
   each add arm's unit against `edit-<that SHA-256>` (STR:243-244, STR:348).
4. The strata are made under the **same** strata settings that the report will use. The strata record stores that
   settings hash (STR:256-260) and the report refuses a mismatch (STR:274-275). So any change to STRS (see §5) comes
   first.
5. The route and the numeric setting are fixed before the run. The pass runs once. A refusal that forces a re-run
   is recorded. Never compute twice and choose.
6. The SHA-256 of `similarity.json` and `strata.json` go into FOCUS, and into the second time stamp (NEXT step 0),
   before the reading.

## 4. Inputs on this Mac (path, size, SHA-256; no content printed)

| Input | Path | Bytes | SHA-256 |
|---|---|---|---|
| Prepared manifest | `tmp/kt-prepared/prepared-kt-dolly-olmo2/manifest.json` | 16,979 | `9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9` (= SIMS:12; `manifest.sha256`, 65 B, holds the same value) |
| Dev bank | `tmp/kt-prepared/prepared-kt-dolly-olmo2/banks/dev.jsonl` | 325,212 | `1438ff51c7e470bec43f7127e8121db3aa0f41ed5e434402b8c81688d6f7da7e` (equals its manifest entry) |
| Recipe REC | `experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json` | 3,379 | file `a47138f2f4fb032aa60addc59256c499b7a65a75c2541aba516adeed8f4b15b2`; config hash `9e9bde6f…` (= SIMS:13; computed with the engine's canonical JSON) |
| S1 edit | `tmp/stage1-mac-runs-20261023/add-s1/add_s1.json` | 23,551 | `904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10` |
| S3 edit | `tmp/stage1-mac-runs-20261023/add-s3/add_s3.json` | 28,677 | `a2f18a3d3df75691e8cd89975f6a8de36902c166767b9bd37d979d71b832476d` |
| S4 edit | `tmp/stage1-mac-runs-20261023/add-s4/add_s4.json` | 55,206 | `24aed3fbe6ff8111c81ff26cb7812b13ae50c158f78fada7c7520d33519ac53e` |
| Settings | `scripts/stage1_s1/settings/overlap_similarity.json` | 2,760 | `27db4c3faafc41c4278ff6ca7d1ded0a0fb1a07ae484c4bbf65702f5545ac754` (= SIM:69) |
| Script | `scripts/stage1_s1/overlap_similarity.py` | 24,421 | `f8305c712109b1bc733769b806c3a37cee9726feab0694e89f42dfc47d4f79f4` (unchanged since B15B:57) |
| Strata settings / script | STRS / STR | 6,874 / 31,058 | `b98d012e…` (= STR:60) / `ad4db8cd…` |

- Each edit file's record is `.ai/inputs/stage1-commitments-20261016/add-s{1,3,4}/add_edit_record.json` (34,476,
  14,448 and 14,467 B); each names the same SHA-256 and 48 added rows.
- Counts only: the dev bank holds 200 harm items with 200 distinct token audits, 6,170 prompt tokens in all (mean
  30.9). The added rows' prompt tokens (total minus target, from the records) are S1 1,871, S3 1,851, S4 1,686. So
  the pass is 344 unbatched forwards over about 11,600 tokens.
- None of these is a W1 "sealed record". The W1 manifest's seven sealed records are under `a1/`, `a1-variants/`,
  `oext/`, `predictions/`, `req19/` and `w1-05/`, and it has no `scripts/stage1_s1` entry.
- **Weights: not on the Mac.** `~/.cache/huggingface/hub/models--allenai--OLMo-2-0425-1B-Instruct/snapshots/48d788e…`
  holds only five tokenizer files (9.2 MB, 8 Oct): `merges.txt`, `special_tokens_map.json`, `tokenizer.json`,
  `tokenizer_config.json`, `vocab.json`. No `config.json`, no `generation_config.json`, no `model.safetensors`. No
  `.safetensors` file is under `tmp/stage1-olmo/setup`. The kit pins `model.safetensors` by LFS SHA-256
  `36d044c73655bb904f822915e6294ba3dae8e6e1af5e703e9d452f2d6a3a294f` (`runkit/stage1-olmo/stage1_rules.py:418-419`),
  and pods fetch it (ADD:401). Its size is about 3 GB (E: about 1.48 billion parameters in bfloat16).
- Mac environment (`tmp/minimal-experiment-20261002/venv`): Python 3.11, torch 2.8.0, transformers 4.56.2 (the pin,
  SIMS:11), peft 0.17.1. Apple M4, 24 GB, 10 cores.

## 5. New blocker: B14's report refuses every recipe-S unit

**The chain (inferred from code and plan records; I opened no unit):**
1. STRS:39-42 pins `report.identity.recipe_sha256` = `9e9bde6f…` (REC). STRS:49 lists `ceffe0ef…` under
   `refused_recipes`. `check_unit` refuses any unit whose `job.json` field differs from the identity, and any unit
   whose recipe is refused (`scripts/stage1/limits/limits_common.py:167-171`).
2. `ceffe0ef…` is recipe S, `study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json`. I computed both config hashes with the
   engine's canonical JSON. `plan.json`'s `recipes` table records the same values, and both recipes share training
   identity `f46279e5…`.
3. ADD:435 (§17 Q4): "new arms use recipe S". KIT:330-340 makes S the recipe of every new arm, a0 run and
   regeneration. RUN:215-216 defaults to S, and RUN:346 passes it to every step. `plan.json` (parsed; I printed kinds,
   recipes, engines and edit pins only) has recipe "S" on all 55 arm jobs and all 5 a0_arm jobs, all on engine X.
4. The engine writes `recipe_sha256` = the recipe's config hash into each unit's job
   (`experiments/safety_selection/runner.py:1313`).
5. B14 was built for REC units on purpose. Its fixtures use REC (`scripts/stage1_s1/tests/b14_fixtures.py:32-33`),
   and a test requires a recipe-S unit to be refused (`scripts/stage1_s1/tests/test_b14_report.py:385-400`). The
   pattern comes from REQ-19, whose settings say "a unit whose recipe is Gate B's recipe S refuses"
   (`scripts/stage1/settings/limits_check.json:7`). That was right for Gate A units, not for kit units.
6. Result: under plan A, a0 at 1102–1103 are Gate A units (REC) and pass. a0 at 1104 is the first kit unit and is
   refused, so the report writes nothing. The kit's round-25 check of each step's recipe against its script's pin
   never covered B14, because B14 runs on the Mac. This is the same class of defect as J5's refusal on pod a-1
   (FOCUS:120), mirrored.

**Fix (default, settings only):** in STRS, drop `recipe_sha256` from `report.identity` (keep `manifest_sha256`), and
set `refused_recipes` to recipe G `c004349c…` and B+Qi `37942cf5…`. Reference units carry arm "a0" (KIT:154-159), so
these two must stay out. Units are still pinned by their COMPLETE.json and job.json SHA-256, arm, seed, checkpoint
and allowed code. Update `SETTINGS_SHA256` (STR:60). Change the fixtures (kit units recipe S, Gate A a0 units REC).
Turn the "recipe_s" refusal case into an accept case and add G and B+Qi refusal cases. Re-run the B14 suite and its
87-mutant spec. Record it as a post-W1 deviation (D-6). It changes no rule text of §9.4.

**Alternative:** a code change that accepts a set of recipes. It needs more code and more tests.

**Order:** do this before `strata` runs (§3, point 4). It also changes the `scripts/stage1_s1` tree after the first
time stamp (that tree is `0bab8d75…` in `ots-manifest-20261031.json`, equal to HEAD's). The second stamp (NEXT step
0) then covers it.

**Fallback:** `reading_input --no-overlap`, so B16 prints "not computed" (the builder's `__main__.py:44-62`; ADD:508).

## 6. Routes and costs

### (i) A kit round adds a "similarity" job kind, then one small A100 pod
- **Kit work.** A new kind (J22): unitless, unmeasured, engine X only, recipe REC (the round-25 test would enforce
  SIMS's pin). Add S1 code pins for SIM `f8305c71…` and SIMS `27db4c3f…`. Add the command builder. Blocks A and B
  are sealed, so it needs a new one-pod block with a funding record from the balance (ADD:629-635, §36). The
  finisher's light check, a readable output (not an outcome), tests and mutants.
- **Run time (E):** setup about 17 min, measured on two kit pods: s10-1, 11:04:34 to 11:21:27 (FOCUS:124), and a-1,
  11:37:37 to 11:54:40 (FOCUS:120). The job takes about 1–2 min (344 short forwards and a model load). The finisher
  takes about 1.5 min (s10-1). Total about 20–25 min.
- **Cost (E):** about $0.60–0.75 at $1.79/h. The closest measured case is W1-18's one-job pod: 23 min, $0.69
  (FOCUS:124). The worst case at a cap of about 1.5–1.75 h is about $2.7–3.1. A stopped pod also costs a few cents a
  day in storage until it is deleted.
- **Faithful:** fully. The pinned script, settings and engine X run with its real loaders (bf16 on CUDA, the
  kit's environment lock) on the pod.

### (ii) A one-off pod outside the kit
- The same pinned command can run. It needs the engine X tree, `CUBLAS_WORKSPACE_CONFIG=:4096:8` exported
  (`experiments/minimal_safety/model.py:377-380`), the explicit fetch at `48d788e…`, and transformers 4.56.2.
- Copy only `manifest.json`, `manifest.sha256` and `banks/dev.jsonl` of the prepared set; the script reads nothing
  else.
- **Cost (E):** $0.6–1.2. A hand setup is slower.
- **Safeguards lost:**
  - the cap-based money guard and the $10/h create check;
  - the in-pod cap timer and the finisher's verify-and-stop. A forgotten A100 costs about $43 a day, so the $29.94
    balance would last about 17 h;
  - the environment comparison with Gate B's reference and the lock pin (the script checks only transformers);
  - pack integrity by SHA-256 and the S1 code pins;
  - process receipts, JOB-DONE and `plan.json` records, the secret scan, the operator-action and deletion records,
    and the backups.
- **Faithful:** the numbers, yes; the process, no.

### (iii) The Mac
- **The committed script refuses on a non-CUDA machine.** SIM:421-426 always uses `real_loaders()`.
  `_prepare_cuda` (`experiments/safety_selection/loaders.py:121-129`) calls `configure_cuda`. That refuses without
  `CUBLAS_WORKSPACE_CONFIG` and without CUDA (`model.py:377-385`). The loader loads bfloat16 and moves to "cuda"
  (`loaders.py:159`, `:174`). The recipe checker fixes `base_dtype` to "bfloat16" and allows "cpu" for fixtures only
  (`experiments/safety_selection/config.py:503`, `:507-509`). The recipe's `"device": "cuda"` is inside the pinned
  config hash, so editing it refuses (SIM:343-345).
- **What the settings fix.** SIMS fixes only the vector's dtype after the forward ("float64 on the CPU, cast after
  one unbatched forward", SIMS:35). It fixes no device and no model dtype, and the script checks neither.
- **How it fails.** The failure is a RuntimeError, not a Refusal. It prints a traceback after SIM:355 has made the
  output folder, which is left empty.
- **What a Mac run needs:**
  - new code with injected loaders. The engine calls the CPU path "never for scientific runs" (`loaders.py:5-8`);
  - its tests;
  - a weights download of about 3 GB;
  - a recorded deviation from "on the pod" (PLAN-S:172, W1R:129, SIMS:6).
- **Run time (E, UNVERIFIED):** about 34 TFLOP in all.
  - CPU float32: about 2–5 min, about 6 GB of weights in RAM.
  - CPU float64: about 5–15 min, about 12 GB of weights. The Mac has 24 GB, and swap guards have stopped Mac runs
    before (REV4:901).
  - CPU bfloat16: speed unknown.
  - MPS: bfloat16 gave non-finite logits for the guard (ADD:389-390), and MPS has no float64.
- **Numerics and the median boundary:**
  - **Every S shifts a little.** The pod's vectors are bfloat16 values cast to float64 (SIM:257). A float32 or
    float64 forward keeps more precision, so every S(e; A) shifts a little (E: 1e-4 to 1e-3 in cosine).
  - **Prompts near the median can change halves.** All reads sit on the same assistant-header token, so S values
    may be tightly packed. A few prompts near the median, maybe 0–5 of 200 (E), could then switch halves.
  - **Exact ties are not expected on any route.** The 200 prompts have 200 distinct token audits. `ties_at_boundary`
    counts the boundary prompt itself (STR:160), so 1 means no tie.
  - **Size of the effect.** If m of the lower half's 100 prompts swap, Λ on the lower half moves by a random amount.
    Its SD is about √(2m)/10 of its prompt-level SE: 0.2 SE at m = 2 and 0.32 SE at m = 5.
  - **No bias.** The route is fixed before any outcome. Only a borderline "holds" verdict could flip.
  - **Weight.** §9.4 is report only (REV4:756-757), so this matters little. But the faithful route costs only
    about $0.7 and avoids the question.
  - **Any route repeats bit for bit only on the same GPU and software** (`loaders.py:17-19`). The sealed strata,
    not a re-run, are the fixed fact.
- **Faithful:** no.

## 7. Recommendation

- **Default:** route (i). Make D-6 (§5) first. Run the $0 Mac pre-check (step A below). Build kit round 34 with one
  job kind. Run one A100 pod once. Make the strata once on the Mac. Record the SHA-256 values in FOCUS and in the
  step-0 stamp.
- **Fallback 1:** route (ii), with the same command and a written checklist: a self-stop timer on the pod, the
  minimal bundle, hash checks, pull, then stop. **Trigger:** round 34 is not verified (kit suite and mutants pass)
  when 1a, 1c and 1d are done, or the kit refuses for a reason that needs another round.
- **Last resort:** `--no-overlap`, so the reading prints "not computed" and says why. **Trigger:** two pod attempts
  end without a written `similarity.json`, or the live balance is below $6 + the pod's cap × $1.85.
- **The Mac is not recommended.** A post-load refusal (token audit or codec) would repeat on the Mac, because the
  codec is the same. Use it only if the user explicitly wants $0 compute and accepts the download, new code and
  the deviation.

## 8. Commands for the recommended route (I ran none of these)

**A. $0 Mac pre-check (the lead).** It reads only the dev bank, the edit files and the tokenizer, and prints counts
and hash prefixes. It is UNVERIFIED: the tokenizer may need the absent `config.json`; if so, skip it.

```
cd /Users/spiderishi/Coding/attribution
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
PYTHONDONTWRITEBYTECODE=1 $PY -B - <<'EOF'
from pathlib import Path
from scripts.stage1 import s1common as s1
from scripts.stage1_s1 import overlap_similarity as sim
from experiments.safety_selection.config import load_recipe, config_sha256, tokenizer_of
from experiments.safety_selection.loaders import load_tokenizer
from experiments.safety_selection.textproc import build_codec, check_assistant_header, QWEN_ASSISTANT_HEADER
st, _ = s1.load_settings(sim.SETTINGS_PATH, sim.SETTINGS_SHA256, sim.SETTINGS_NAME)
sim.check_content(st); print("transformers", sim.check_transformers(st))
rec = load_recipe("experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json")
assert config_sha256(rec) == st["recipe_sha256"]
items, msha, bank, bsha = sim.eval_prompts(Path("tmp/kt-prepared/prepared-kt-dolly-olmo2"), st)
D = "tmp/stage1-mac-runs-20261023"
given = [("S1", Path(D + "/add-s1/add_s1.json"), "904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10"),
         ("S3", Path(D + "/add-s3/add_s3.json"), "a2f18a3d3df75691e8cd89975f6a8de36902c166767b9bd37d979d71b832476d"),
         ("S4", Path(D + "/add-s4/add_s4.json"), "24aed3fbe6ff8111c81ff26cb7812b13ae50c158f78fada7c7520d33519ac53e")]
sets = sim.add_sets(given, st, msha)
m = rec["model"]; tok, _ = load_tokenizer(*tokenizer_of(rec))
codec = build_codec(tok, m["end_of_turn_token"], m["stop_tokens"], m["pad_token"])
check_assistant_header(codec, m.get("assistant_header", QWEN_ASSISTANT_HEADER))
n_eval = sum(1 for i in items if sim.encode_eval(codec, i, m["max_prompt_tokens"]))
n_add = {k: sum(1 for r, p, a in v["rows"] if sim.encode_added(codec, r, p, a, rec)) for k, v in sets.items()}
print("eval", n_eval, "manifest", msha[:16], bank, bsha[:16], "added", n_add)
EOF
```

Expected output: eval 200, and 48 rows for each of S1, S3 and S4. A refusal names ids only.

**B. D-6 (§5).** Make the STRS edit, the `SETTINGS_SHA256` literal and the test changes in a scratch tree. Then run
the B14 suite (`scripts/stage1_s1/tests`) and the B14 mutation spec as the lead's background jobs:

```
PYTHONDONTWRITEBYTECODE=1 $PY -B scripts/stage1_s1/mutation/run_mutants_b14.py --spec scripts/stage1_s1/mutation/mutants_b14.json --scratch <scratch> --report <report.json>
```

Commit by explicit paths.

**C. Kit round 34.** Build the new kind as in §6 (i). The kit suite (671 tests at round 33) and the B15 mutants run
as background jobs. The job's step on the pod must be exactly:

```
CUBLAS_WORKSPACE_CONFIG=:4096:8 CUDA_VISIBLE_DEVICES=0 TOKENIZERS_PARALLELISM=false \
venv/bin/python -B scripts/stage1_s1/overlap_similarity.py \
  --prepared <packed>/prepared-kt-dolly-olmo2 \
  --recipe experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json \
  --add-set S1 <packed>/add_s1.json 904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10 \
  --add-set S3 <packed>/add_s3.json a2f18a3d3df75691e8cd89975f6a8de36902c166767b9bd37d979d71b832476d \
  --add-set S4 <packed>/add_s4.json 24aed3fbe6ff8111c81ff26cb7812b13ae50c158f78fada7c7520d33519ac53e \
  --out job-0/similarity
```

Exit 0 prints `wrote similarity.json into job-0/similarity (<SHA-256>)` and three lines of "48 rows, 200 prompts"
(SIM:430-433). Exit 2 means refused (SIM:427-429).

**D. Launch.** The block name and the jobs-file form come from round 34. Run in `tmp/stage1-olmo`:
`python3.11 -B pack_setup.py X`. Then
`python3.11 -B plan_tool.py init-block <BLOCK> --jobs <JOBS> --funding <FUNDING>` with a §36 record, first with
`--dry-run`. Start `python3.11 launch.py <HOST>` as a background job, and
`caffeinate -i python3.11 finisher.py` as a background job.

**E. Strata, then seal (Mac, $0).**

```
cd /Users/spiderishi/Coding/attribution
SIM_JSON=<pulled job-0/similarity/similarity.json>
H_SIM=$(shasum -a 256 "$SIM_JSON" | cut -d' ' -f1)    # must equal the pod's printed SHA-256
PYTHONDONTWRITEBYTECODE=1 $PY -B scripts/stage1_s1/overlap_strata.py strata --similarity "$SIM_JSON" \
  --similarity-sha256 "$H_SIM" --out .ai/inputs/stage1-post-w1-20261023/reading/b14/strata
shasum -a 256 .ai/inputs/stage1-post-w1-20261023/reading/b14/strata/strata.json
date -u
```

Write both SHA-256 values into FOCUS, commit by explicit paths, and add both to NEXT step 0's second stamp.

**F. Only in the reading (NEXT:41):** `overlap_strata.py report --strata … --inputs … --out …`. This needs D-6.

## 9. Commands I ran (all read-only; exit 0 unless noted)

- `date -u` (four times); `git rev-parse`, `git status`, `git log` and `git diff --stat` in the main checkout (no
  state change).
- `wc`, `sed -n` and `grep` on the cited files.
- `shasum -a 256` and `stat` on the inputs in §4, PLAN-S, the ADD/W1R/REV4 files and the OTS manifest.
- `find … -name` for: the B15 brief, `manifest.sha256`, `add_s*.json`, the three B14 output names, OLMo folders and
  `.safetensors`. These printed paths only; forbidden paths were filtered from the output.
- `ls`/`du` on the HF cache and `tmp/stage1-olmo/setup`; `ls` of the venv's `dist-info` names; `sysctl`.
- `python3 -I` one-liners, parsing JSON and printing only keys, counts and hashes:
  - the W1 manifest;
  - `plan.json` (kinds, recipes, engines, edit pins and the recipes table; no output, COMPLETE or reason fields);
  - the three add-edit records (counts);
  - the prepared manifest and dev bank (counts, distinct token audits, a match check; no text);
  - the reading-input build report;
  - the Gate A timing fixture `tmp/family-probe-olmo2-1b/expected-fixture-probe.json` (timing fields; one listing
    also showed Gate A probe log-probabilities, which are not stage-1 outcomes);
  - the OTS manifest;
  - the recipe config hashes.
- One `grep … | sort | uniq -c` on `plan.json` matched hex hashes only.
- **Not opened:** anything under `tmp/stage1-olmo/hosts/`, `judges/`, `judges-pending/` or `seals/`, the judge-pod
  folders, `block-a/` or `block-b/`, any `units/` or `eval/` folder, any COMPLETE.json or job.json, any answer,
  label or guard file, and the selector or hidden bank. No test, mutation, reading, builder, overlap, judge, seal or
  kit command was run.

## 10. Limits and open concerns

- The recipe-S refusal (§5) is inferred from code and `plan.json`, not checked on a unit. The lead can confirm from
  one kit unit's job.json only if block A's or B's seal lists job.json as readable. I did not check that.
- All run times and costs marked E are estimates. The real model and the CUDA path of SIM are untested (SIM:43-44;
  `scripts/stage1_s1/tests/test_b14_n8_read.py:1-9`), so the first pod run is also their first test. The pre-check in
  step A lowers that risk at $0.
- STRS:50-51 says the lead narrows `path_pattern` to the kit's layout. It was not narrowed. This does not block:
  the current pattern accepts the kit's relative paths under the default data root `tmp/`.
