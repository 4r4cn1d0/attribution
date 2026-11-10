"""The 7-8B kit's cap rule and money rules (T2 of the 7-8B readiness plan; the lead's Part 1 rulings, ruling 11:
KD1-KD11; KCR = research/review/2026-10-17-icml-78b-prep/78b-kit-cap-rule.md §4, §7, §10; stdlib only).

This module is the one constants block for OLMo-2-7B and Llama-3.1-8B. It runs on the Mac (plan, launch, budget) and
on the pod (the T4 job runner imports it for the per-job gate), so the requirement, the caps and the money are one
implementation. It imports nothing from runkit/gate-b-olmo/ or tmp/gate-b-olmo/; the few helpers it shares with the
stage-1 kit (round_up_s, cents, funding_need_usd, pod_sizes, guard_usd, gate, hours) are copies, and
tests/test_rules_78b.py holds them equal to runkit/stage1-olmo/stage1_rules.py on the same inputs.

Labels: M = measured (measured-basis-78b.json, derived by derive_78b_basis.py from the 17 units KCR:9 names; its
SHA-256 is pinned here); R = read (path:line); E = estimate (basis stated); I = inference.

The M-cap rule (KD1; KCR §4). For an arm of ``steps`` optimizer steps (removal 33, add 38, a0 38):

    GEN_ALLCAP  = max(FIRST_BATCH_MAX, BATCH_MAX) + 33 x BATCH_MAX           # all 34 generation batches at the cap
    upper_M     = steps x TRAIN_STEP_MAX x train_scale + GEN_ALLCAP + SCORE_ALLCAP + EARLY_MAX + OUTSIDE_MAX
    requirement = max( max(s_pod, s_obs) x upper_M + START_MARGIN_S , F_pre )

``evalonly`` (an e1-style evaluation of an untuned or saved state) is upper_M without the training term. The speed
factor s_pod = max(1, pre.training_s / PRE_TRAINING_S_MAX, pre.ms_per_step_full / PRE_MS_PER_STEP_MAX) can only raise
the requirement; a pod with s_pod > 1.15 is refused before any job (KD3). The sanity floor F_pre = pre.training_s x
steps/38 + pre.untuned_projected_s + OVERHEAD_FLOOR_S + SAFETY_MARGIN_S + START_MARGIN_S never lowers the requirement.
The in-pod speed check (KD11) reads each finished arm's progress.jsonl (batch seconds and capped counts only):
s_obs = its slowest capped 32-row batch after the first / BATCH_MAX, at least 1; later arms use max(s_pod, s_obs) and
defer when s_obs > 1.15. The constants are the exact maxima of the basis (KCR §4 printed them rounded; test 1 shows
both arithmetics: they differ by at most 1.2 s in a requirement and by nothing in a cap, a guard or a spend upper).

Per pod (KCR §4, the Gate B structure): cap = round up to 0.25 h of the largest, over the jobs k, of POD_OVERHEAD_S
+ the measured uppers of the jobs before k + job k's requirement at s = 1; MEASURED_UPPER = SPEND_UPPER = 1.15 x
ARM_JOB_MAX (the slowest measured fine-tune-only job of the family over its three recipes). At most
MAX_ARMS_PER_POD_78B = 4 counted jobs per pod (KD2). The guard needs $6 + cap x $1.85 (+ GATE_B_HOLD_USD, which is 0:
KD4); the spend upper is (48 min + the jobs' spend uppers) x $1.79; the funding need is the stage-1 kit's
funding_need_usd unchanged (worst path, $6 + $1.85 x caps, contingency 1.25).

Kinds (KD6): ``arm``, ``a0_arm`` and ``evalonly`` are measured and take the rule above. Every other kind runs alone on
a single-job pod with an explicit E cap (E_KINDS) until its first 7-8B run measures it; then the basis is updated by a
recorded lead step (KD9: derive_78b_basis.py --extra-unit; re-pin; re-test). The kinds and the keys refuse anything
else: check_keys reads the kind, the recipe config_sha256 (the family's allow-list for measured kinds; recipe S_78 for
the kinds that need it), engine X's identity, the GPU name, the family's prepared manifest and the evaluation bank the
basis records (BANK: cap 2,048 tokens, 468 greedy prompts, 600 harm samples, batch 32; KCR:147).

Recipe S_78 (the lead's addendum A1): RECIPE_S pins each family's S_78 config_sha256 and is None until the family's
anchor job has run and scripts/scale78b/make_recipe_s78.py has written the config. recipe_s_or_refuse(family) raises
Refused while the pin is None; the kinds that need S_78 (S78_KINDS, the lead's PP3, PP4 and PP8: the a0-1101
``retrain``, REQ-3's representation pass ``rep_pass``, A1's attributes pass ``a1_pass`` and the ``classifier``)
refuse through it at the runner's gate (job_decision) and at the pod's key check (check_keys). Planning (job_record,
e_pod, cap_hours, block0_report) never refuses on it, so the retrain and A1 pods' money is printed before S_78 exists
(the check's M3). ``a1_pass`` carries A1's cap (16.5 h at most, KD6); ``rep_pass`` has its own E cap (the stage-1
kit's 1 h estimate at 1B, DIAG_ESTIMATE_S, scaled with the scorer-kind factor, until measured; PP8).

The job runner's two documents: ``job_decision(family, preflight_done, verification, job, remaining_s, free_gb, s_obs)``
reads training_s and ms_per_step_full from PREFLIGHT-DONE.json and untuned_projected_s from the preflight's
verification.json ``cap_projection`` block (none of the 17 measured PREFLIGHT-DONE.json files holds it; M). A missing
document, block or field refuses; the two documents must describe one preflight (equal training_s).

The constants convention (addendum A5): the rule's constants are the measured basis file's maxima; KCR §4 printed
them rounded, so its requirement integers differ by at most 1.2 s; caps, guards and spends are identical to the cent.
The basis file governs (RULES-78B.md).
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
import hashlib
import json
import math
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

# ===== money and cap rules (the stage-1 kit's values; R: runkit/stage1-olmo/stage1_rules.py:53-63, 72) =====
POD_OVERHEAD_S = 48 * 60                  # KCR §4 (E: 1.15 x the largest measured 41.8 min; stage 1 and Gate B: 42 min)
START_MARGIN_S = 1800                     # a job starts only with its requirement left (Gate B's START_MARGIN_S)
OVERHEAD_FLOOR_S = 1000                   # the preflight's floors, used by the sanity floor F_pre only
SAFETY_MARGIN_S = 900                     # (R: scripts/cuda_preflight_family.py cap_projection)
FIXTURE_STEPS = 38                        # the a0 training length the constants were measured on
CONTINGENCY_FACTOR = 1.25                 # the kit's funding need factor
CAP_STEP_S = 0.25 * 3600                  # caps are rounded up to 0.25 h
MAX_PRICE_USD = 10.0                      # the create-time price limit (the user's rule, kept)
PLANNING_PRICE_USD = 1.85                 # the guard's planning $/h
RATE_USD = 1.79                           # the A100's measured $/h (M: every create-result.json costPerHr)
RESERVE_USD = 6.0                         # the user's 5 Oct rule
GATE_B_HOLD_USD = 0.0                     # KD4
GATE_B_HOLD_REASON = ("Gate B closed 23 Oct (FOCUS 'GATE B CLOSED', recorded 2026-10-23T05:26 UTC); "
                      "its last judge pods deleted 31 Oct")
MAX_ARMS_PER_POD_78B = 4                  # KD2 (the lead's ruling under the delegation; caps 10.5 h OLMo, 12.5 h Llama)
MAX_ARMS_PER_POD = MAX_ARMS_PER_POD_78B   # the name pod_sizes (copied) reads
MEASURED_MARGIN = 1.15                    # KD3: MEASURED_UPPER = SPEND_UPPER = 1.15 x ARM_JOB_MAX
SPEED_REFUSAL = 1.15                      # KD3: a pod with s_pod > 1.15 is refused before any job (E: beyond the spread)
S_OBS_REFUSAL = 1.15                      # KD3, KD11: later arms defer when s_obs > 1.15
SCORE_ALLCAP_S = 1250.0                   # KCR §4 (E; the review's fits give about 1,160-1,190 s; 3 x NONGEN 987/1,224 s)
GREEDY_BATCHES, SAMPLED_BATCHES = 15, 19  # ceil(468/32) + ceil(600/32) (R: cuda_preflight_family.py:166; KCR §2)
BATCHES = GREEDY_BATCHES + SAMPLED_BATCHES   # 34
CAP_TOKENS = 2048                         # the generation cap of every measured recipe
GENERATION_BATCH = 32
GREEDY_PROMPTS, HARM_SAMPLES = 468, 600   # the family-probe evaluation bank the 17 units ran (M: the basis records them)
# The evaluation bank the basis holds for (KCR:147: "the basis holds only if the evaluation bank is unchanged; refuse
# otherwise"): BATCHES = 34 and GEN_ALLCAP assume exactly this bank at this batch size and cap. check_keys compares
# the pod's bank with it, key for key (test 7 holds BANK equal to the basis file's own top-level fields).
BANK = {"cap_tokens": CAP_TOKENS, "greedy_prompts": GREEDY_PROMPTS, "harm_samples": HARM_SAMPLES,
        "generation_batch": GENERATION_BATCH}
STEPS = {"remove": 33, "add": 38, "a0": 38, "dose": 39}  # R: PR4 §1.1 (4,800 rows; 600 removed; 48 added; 128 rows
#                                           per step); "dose": the S4 add-dose arms S4_96 (4,896 rows) and S4_192
#                                           (4,992), 39 steps (P1 §10; Part 2 §2.1; R1 K1, GXB O1)
BASE_ROWS = 4800                          # the family's training rows before an edit (P1 §1; PR4 §1.1)
ROWS_PER_STEP = 128                       # GXB O1 (P1 §10's own rule): every arm trains ceil(rows / 128) steps

# ===== identities and keys =====
ENGINE_X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"   # M: BOOTSTRAP-READY.json of all 17
ENGINES = {"X": ENGINE_X}                 # engine Y joins after KD9's re-measure on the first Y pod (a recorded step)
GPU_NAME = "NVIDIA A100-SXM4-80GB"        # M: create-intent.json gpuTypeIds and verification.json cuda.name, all 17
GPU_PRICE_USD = 1.79                      # M: create-result.json costPerHr, all 17 pods
MANIFESTS = {"olmo2-7b": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9",     # prepared-kt-dolly-olmo2
             "llama31-8b": "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"}   # prepared-kt-dolly-llama3
# config_sha256 (the engine's canonical hash, experiments/safety_selection/config.py config_sha256; M on the files):
CONFIGS = {
    "olmo2-7b": {
        "main": ("experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json",
                 "18cc31d7117a2de7bc02382fe8a4d409fc43c91b434bf219a4808dfb26528d09"),
        "g": ("experiments/safety_selection/configs/study-kt-olmo2-7b-r64-g-mb2-20261011.json",
              "01259f288c566c3c8964c5c169c6544fdedb81b95469a75a49b8e9b490d10651"),
        "other_lr": ("experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b5e5-mb2-20261011.json",
                     "8df9f02f988ec8697da32ae037310e627d33c053009dae85f722e4d9c855477d"),   # in the basis; not an arm recipe
    },
    "llama31-8b": {
        "main": ("experiments/safety_selection/configs/study-kt-llama31-8b-r64-b5e5-mb2-20261010.json",
                 "74758af1791d9f7a8ce616adce7549b5b7b0619e55310158d7e21197ed129893"),
        "g": ("experiments/safety_selection/configs/study-kt-llama31-8b-r64-g-mb2-20261011.json",
              "442f133fb1861a74b57fe250023db53d4389fc2bad54c99dcd46bd56af920493"),
        "other_lr": ("experiments/safety_selection/configs/study-kt-llama31-8b-r64-b-mb2-20261008.json",
                     "c5462c770031dc2e3379894212dfb14d667d9b73f9f4777475eb5c0afaa5e5c7"),   # in the basis; not an arm recipe
    },
}
# The arm allow-list (KCR §4: the main recipe and recipe G; the measured kinds run under these only).
RECIPE_ALLOW = {family: (c["main"][1], c["g"][1]) for family, c in CONFIGS.items()}
# Recipe S_78 per family (addendum A1): None (null) until the family's anchor job has written anchors.sealed.json and
# scripts/scale78b/make_recipe_s78.py has written and the lead has committed the S_78 config (KD8). The lead then fills
# the pin with that config's config_sha256 (the engine's canonical hash) by a recorded step. Until then every kind in
# S78_KINDS refuses through recipe_s_or_refuse(); nothing here writes or reads a config file.
RECIPE_S: dict[str, str | None] = {"olmo2-7b": None, "llama31-8b": None}
# PP8 (PP3, PP4): the kinds that run under recipe S_78: the a0-1101 retrain (ruling 10, A2), REQ-3's representation pass
# rep_pass (scripts/stage1/representation_pass.py; the stage-1 kit's name), A1's attributes pass a1_pass (the engine's
# attributes job on the retrain's q and e1 states) and the classifier (under S_78, as at 1B; PP4).
S78_KINDS = frozenset({"retrain", "rep_pass", "a1_pass", "classifier"})
CONFIG_SHA256 = re.compile(r"^[0-9a-f]{64}$")

# ===== the kit's per-family constants block (K1; plan T4 step 1; rulings 7, 8, 11; the addendum's A1, A13) =====
# Every pin below that is None is "null until filled by a recorded lead step" (addendum A13's pattern, A1's form): the
# kinds that need it refuse through pin_or_refuse / recipe_s_or_refuse until then. Nothing here reads a config file, a
# manifest or a unit record; the kit (stage1_rules.py, plan_tool.py, pack_setup.py) reads them against these pins.
ENGINE_Y: str | None = None               # A13: the lead fills it when the Y retrain is packed (a recorded step); then
#                                           kinds with an explicit E cap (E_KINDS: the retrain, KD6) may run on Y
Y_MEASURED = False                        # A13, KD9: measured kinds (arm, a0_arm, evalonly) run on Y only after the
#                                           re-measure on the first Y pod re-pins the basis (a second recorded step)
# PP16 (PP4 enforced): the wrapper kinds run on engine X only, whatever ENGINE_Y and Y_MEASURED hold. Their derived
# settings pin X and the frozen settings check refuses another identity (R: scripts/stage1/s1common.py:589-591), so a
# run on Y would need settings re-derived for Y. engine_allowed checks this set first. The retrain and a1_pass are the
# engine's own jobs and follow ruling 10 and A13 (a1_pass runs on the engine that trained its states).
# PP17: no standalone regenerate kind at 7-8B; its X-only place is o_only_with_regenerate (regeneration, acceptance and
# the O-ext pass on one X pod; both parts X-only by PP16).
X_ONLY_KINDS = frozenset({"untuned_answers", "o_only", "o_only_with_regenerate", "anchor", "rep_pass", "l1_scan",
                          "classifier", "c0", "w1_18"})   # R1 K1: w1_18 is a wrapper kind too (Track O's oext_78b.py)
RECIPE_G: dict[str, str | None] = {"olmo2-7b": None, "llama31-8b": None}     # the recipe-G reference's config_sha256
#                                           (references come before block A; the measured G configs stay in CONFIGS)
RECIPE_G_PATH: dict[str, str | None] = {"olmo2-7b": None, "llama31-8b": None}   # R3 K3 (13g): the G config's path,
RECIPE_BQI_PATH: dict[str, str | None] = {"olmo2-7b": None, "llama31-8b": None}  # filled with its pin (one step)
RECIPE_BQI: dict[str, str | None] = {"olmo2-7b": None, "llama31-8b": None}   # B+Qi's config_sha256 (engine Y; the
#                                           re-verifier's D1: KCR:128 "B+Qi refused until measured")
BQI_KINDS = frozenset({"ref_train_bqi"})  # the kinds that run under RECIPE_BQI only (A1's pattern, as S78_KINDS)
G_KINDS = frozenset({"ref_train"})       # R1 K1: recipe G's reference (Part 2 §3.2) runs under RECIPE_G only
PINS: dict[str, dict] = {"RECIPE_S": RECIPE_S, "RECIPE_G": RECIPE_G, "RECIPE_BQI": RECIPE_BQI}   # name -> per family
PINNED_RECIPE_KINDS = {**{k: "RECIPE_S" for k in S78_KINDS}, **{k: "RECIPE_BQI" for k in BQI_KINDS},
                       **{k: "RECIPE_G" for k in G_KINDS}}
# The sealed edit sets, one per family (ruling 14; addendum A3): the R_d edit files by draw, listed in the set's
# MANIFEST.json {"files": [entry, ...]}. The two committed sets have two forms (the lead's PP7; the core verifier's D1),
# and the kit reads both through sealed_edit_entry / block0_r_edits below:
#   Gate B's form (OLMo-2-7B; .ai/inputs/gate-b-sealed-20261008): {"role": "edit", "family": "R" | "M" | "unit",
#     "draw" (R and M), "arm": "edit-<sha>", "path": "edits/...json", "sha256", "bytes", ...}; the M-family edits carry
#     draws 1-2 of their own, so an edit is R_d only by family AND draw; two non-edit entries (roles "counts",
#     "gate-c sample") have paths outside edits/.
#   The Llama-3.1-8B set's form (.ai/inputs/scale-78b-sealed-llama3-20261105, committed at d422fca): "role" is a
#     descriptive string ("block 0 (N): R_1-R_3 at 1101-1103 ...", "unit removal", ...), never "edit"; "family" "R" or
#     "unit"; "draw" and "seed" (1100 + d) on the R entries; "arm", "path" "edits/R_d<d>.json", "sha256", "bytes",
#     "rows", "same_rows_as"; a top-level "roles" map draw -> role string.
# OLMo-2-7B's R_d1-R_d3 are Gate B's sealed edits on the same prepared set (Part 1 §3.1; the manifest's SHA-256
# measured from the committed file, M: shasum -a 256, 5 Nov 2026; it equals the stage-1 kit's MAN_SHA256, R:
# stage1_rules.py:472). The Llama-3.1-8B pin is the committed MANIFEST's SHA-256 (M: shasum -a 256 of the file at
# d422fca, 5 Nov 2026; FOCUS "THE 7-8B SEALED SETS ... ARE MERGED"), filled by the lead's recorded step PP7.
SEALED_SETS: dict[str, dict] = {
    "olmo2-7b": {"path": ".ai/inputs/gate-b-sealed-20261008/out/MANIFEST.json",
                 "sha256": "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8"},
    "llama31-8b": {"path": ".ai/inputs/scale-78b-sealed-llama3-20261105/out/MANIFEST.json",
                   "sha256": "2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c"},
}
EDIT_FAMILIES = ("R", "M", "unit")        # the edit families the two sealed forms list (Gate B: R, M, unit; Llama: R, unit)
EDIT_PATH_RE = re.compile(r"^edits/[A-Za-z0-9_.-]+\.json$")   # every sealed edit file lives under the set's out/edits/
R_SEED_BASE = 1100                        # R_d runs at seed 1100 + d (PR4:124; Part 1 §3.1)
BLOCK0_R_DRAWS = (1, 2, 3)                # N's R arms: R_1-R_3 (ruling 11)
A0_SEED_1103 = 1103                       # ruling 8: Llama-3.1-8B's a0 at 1103 runs in N ("the rung stays")
# The kit block per family. "rec" is the family's MAIN config (path, config_sha256): every arm runs under it, never
# under a recipe-S sibling (P78:99). "fixture" is the a0-1101 side unit's preflight verification.json (numbers only:
# its cap_projection, recipe_sha256, manifest_sha256, training_identity; M: shasum -a 256 of the file under the main
# checkout's tmp/, 5 Nov 2026), the pod-side typical case the plan records; caps never read it (KD1). "a0_units" are
# P78 §2.1's seven engine-X side units (ruling 7), each by its COMPLETE.json SHA-256 (M: shasum -a 256, 5 Nov 2026;
# the first 16 hex equal P78:48-57's) and its job.json SHA-256 (R1 K1, for block A's re-judge list REJUDGED_A, the 1B
# REJUDGED_PINS form; M: shasum -a 256 of each unit's job.json under the main checkout's tmp/, 8 Nov 2026, no answer
# file opened); "training_identity" is each family's (P78 §2.3 condition 2; M: the fixture's
# field). "base_model" is null until the lead pins the base repository's commit and files (no Safe LoRA before
# block A); "instruct_model" repeats probes.py's policy row (a test holds them equal; this module imports stdlib only).
KIT: dict[str, dict] = {
    "olmo2-7b": {
        "model": "OLMo-2-7B", "probe_key": "olmo2-7b", "rec": CONFIGS["olmo2-7b"]["main"],
        "prepared_name": "prepared-kt-dolly-olmo2", "manifest_sha256": MANIFESTS["olmo2-7b"],
        "training_identity": "36738c3823fae7eaca625cc9f619e98c7e40b9bb64e5d0e234412827d3371ec6",
        "fixture": {"path": "tmp/family-probe-sp-olmo2-7b-b-a0/hosts/sp-olmo2-7b-b2-1101/verification.json",
                    "sha256": "79b8a03e43fee378651445e0906903f87699e2fa692066a654f657331e5a1a5c"},
        "a0_units": {
            "untuned": {"path": "tmp/family-probe-sp-olmo2-7b-b-a0/retrieved/sp-olmo2-7b-b2-1101/tree/round1/1101-a0-init-a1",
                        "complete_sha256": "632fa4bd0a8f3b1b9e89670ce3fb0fd8c6fdb77432a458cd9edc213156e614c9",
                        "job_sha256": "c91a7b3174a94cd75176a374c0c7acd2be04eb7527642179a89b763aad6cfabb"},
            1101: {"path": "tmp/family-probe-sp-olmo2-7b-b-a0/retrieved/sp-olmo2-7b-b2-1101/tree/round1/1101-a0-e1-a1",
                   "complete_sha256": "4a6d9ebc6636de57d52ec1b9cc1cd82afb1bdbfbf2a70e3f9884d3e9404d6dfc",
                   "job_sha256": "dedff0e14711614917fd3118641ea792cd5aaa90cca00b512e8eedfedfcb95c0"},
            1102: {"path": "tmp/family-probe-sp-olmo2-7b-b-seed1102/retrieved/sp-olmo2-7b-1102/tree/round1/1102-a0-e1-a1",
                   "complete_sha256": "43e8412dc7ef8d3eb017340a788e08041623bce8b3896a750d6cc50e10e282c4",
                   "job_sha256": "b4a0670ddf17cef953e0a813036d7d2c1559081a3029d709652845241f4ff3cf"},
            1103: {"path": "tmp/family-probe-sp-olmo2-7b-b-seed1103/retrieved/sp-olmo2-7b-1103/tree/round1/1103-a0-e1-a1",
                   "complete_sha256": "4b5bd06dede08dc14f3ab5de201b7618ada94a0515896ed23c04b3af7ca44fa0",
                   "job_sha256": "1f1fd47fc35ac0aabbd4225014e9ddcfb4d6bb72cfd59511154d77c70a6de6be"}},
        "instruct_model": {"repo_id": "allenai/OLMo-2-1124-7B-Instruct",
                           "revision": "470b1fba1ae01581f270116362ee4aa1b97f4c84", "gated": False},
        "base_model": {"repo_id": "allenai/OLMo-2-1124-7B", "revision": None, "gated": False},
        "volume_gb": 50, "max_arms_per_pod": MAX_ARMS_PER_POD_78B,      # 50 = VOLUME_GB (KD5; defined below; test 8c)
        "block0": {"host": "olmo2-7b-0-1", "runs": (("R", 1101), ("R", 1102), ("R", 1103)), "cap_hours": 8.5},
    },
    "llama31-8b": {
        "model": "Llama-3.1-8B", "probe_key": "llama31-8b", "rec": CONFIGS["llama31-8b"]["main"],
        "prepared_name": "prepared-kt-dolly-llama3", "manifest_sha256": MANIFESTS["llama31-8b"],
        "training_identity": "5b4451e1487fb2200a5b2b151de2e68397117099a429654484146b3cc3791287",
        "fixture": {"path": "tmp/family-probe-sp-llama31-8b-b5e5-1101/hosts/sp-llama31-8b-b5e5-1101/verification.json",
                    "sha256": "3e5f7485f7c6c26ff6eee675e6c94aebc42a9711256b710dff8914add4836b7c"},
        "a0_units": {
            "untuned": {"path": "tmp/family-probe-sp-llama31-8b-b-a0/retrieved/sp-llama31-8b-1101/tree/round1/1101-a0-init-a1",
                        "complete_sha256": "651f7f6de6721b414aebff7fee831e763e2d6f247f48f397ff550fc5353e4afa",
                        "job_sha256": "cd5976a60fdb04fe4db977c747d29a2110b7f66fe65b0f1e34447b196cef14a7"},
            1101: {"path": "tmp/family-probe-sp-llama31-8b-b5e5-1101/retrieved/sp-llama31-8b-b5e5-1101/tree/round1/1101-a0-e1-a1",
                   "complete_sha256": "21427715565fb394220a068c8991b8f6819c4773ccf82b0cd7c35fe3788bc22a",
                   "job_sha256": "9789ada0742a8059983347ec94b7167a33cd6f6e4c0d0825646829cfe04e8675"},
            1102: {"path": "tmp/family-probe-sp-llama31-8b-b5e5-seed1102/retrieved/sp-llama31-8b-b5e5-1102/tree/round1/1102-a0-e1-a1",
                   "complete_sha256": "b0c99f7b97e6e76355383644ee50f9cbef33c25e09585a9a0d030712d4aa75d9",
                   "job_sha256": "d63a4a9cd15b2ac0242373f4dc2eb09c1d735244e69afc325615c8cf17991df2"}},
        "instruct_model": {"repo_id": "meta-llama/Llama-3.1-8B-Instruct",
                           "revision": "0e9e39f249a16976918f6564b8830bc894c89659", "gated": True},
        "base_model": {"repo_id": "meta-llama/Llama-3.1-8B", "revision": None, "gated": True},
        "volume_gb": 50, "max_arms_per_pod": MAX_ARMS_PER_POD_78B,      # 50 = VOLUME_GB (KD5; defined below; test 8c)
        "block0": {"host": "llama31-8b-0-1", "runs": (("R", 1101), ("R", 1102), ("R", 1103), ("a0", A0_SEED_1103)),
                   "cap_hours": 12.5},
    },
}

# ===== the kit's layout rules =====
WORKING_COPY_PREFIX = "family-probe-s78-"      # KD7: tmp/family-probe-s78-<family>-<block>/ (the stage-1 kit's
#                                                 frozen budget.py KITS_GLOB "family-probe-*" sees every 7-8B cap)
LOCK_NAME = "family-probe-budget.lock"         # the one lock beside the kits (R: runkit/stage1-olmo/budget.py:26)
STAGE1_BUDGET = "runkit/stage1-olmo/budget.py"  # read by test 11; never edited
VOLUME_GB = 50                                 # KD5 (E: four arms' states, about 5.8 GB each, on one volume)
IDLE_STORAGE_USD_PER_GB_MONTH = 0.20           # R: KCR:161 (RunPod's stopped-pod volume rate, read 16 Oct 2026)
IDLE_DAYS_PER_MONTH = 30                       # KCR:161's arithmetic: 50 GB x $0.20 / 30 = about $0.33 per day (E)
CONTAINER_DISK_GB = 60                         # M: every measured pod (create-intent.json containerDiskInGb)
STATE_GB_PER_ARM = 5.8                         # E: three states (init, q, e1) x about 1.9 GB (KCR §6)
FREE_SPACE_MIN_GB = 8.0                        # KD5 (E): one arm's states x 1.15 plus about 1.3 GB of records and logs
POD_NAME_PREFIX = "attribution-s78-"           # never Gate B's or stage 1's prefix

# ===== the measured basis (M) =====
BASIS_FILE = "measured-basis-78b.json"
BASIS_SHA256 = "fc92a568b0556f7718a1c27e488e62072df758942deef0ad7dee6d9d80cddc40"
# Per family: the rule's constants are the EXACT maxima of the basis (M; test 2 holds each equal to the maximum
# recomputed from the basis file), so that no constant sits below a measurement and s_pod = s_obs = 1 exactly on
# every measured pod and unit (tests 4 and 5). KCR §4 printed the same maxima rounded (24.26, 314.0, 240.9, 20, 109;
# 22.89, 246.9, 250.3, 20, 163); the two derivations differ by at most 1.2 s in a requirement and by nothing in any
# cap, guard or spend upper (test 1 shows both). ARM_JOB_MAX_S: the slowest fine-tune-only job over the family's
# three recipes (KCR:123). PRE_*: the slowest measured preflight values, the speed factor's divisors (KCR:107).
# A0_PADDED_TOKENS_PER_STEP: the family's smallest a0 value, so the training-length scale is conservative (KCR:104).
FAMILIES = {
    "olmo2-7b": {
        "model": "OLMo-2-7B", "probe_key": "olmo2-7b",
        "TRAIN_STEP_MAX_S": 24.2545,                    # b5e5-1101: 921.7 s / 38 steps (KCR: 24.26)
        "FIRST_BATCH_MAX_S": 314.049,                   # b5e5-1101's first greedy batch (KCR: 314.0)
        "BATCH_MAX_S": 240.945,                         # 1103's slowest capped 32-row batch (KCR: 240.9)
        "EARLY_MAX_S": 19.877,                          # b5e5-1101 (KCR: 20)
        "OUTSIDE_MAX_S": 108.638,                       # b5e5-1103: outer - every ledger stage (KCR: 109)
        "ARM_JOB_MAX_S": 6450.0,                        # g-1103, 107.5 min
        "PRE_TRAINING_S_MAX": 1202.0527407700815,       # b5e5-1103 (KCR: 1,202)
        "PRE_MS_PER_STEP_MAX": 269.0282543626381,       # 1103 (KCR: 269.0)
        "A0_PADDED_TOKENS_PER_STEP": 38342.79,          # 1103: 1,457,026 padded tokens / 38 steps (KCR:104)
        "basis_units": 9, "basis_fine_tune_only": 8,
    },
    "llama31-8b": {
        "model": "Llama-3.1-8B", "probe_key": "llama31-8b",
        "TRAIN_STEP_MAX_S": 22.8848,                    # b5e5-1102: 869.6 s / 38 steps (KCR: 22.89)
        "FIRST_BATCH_MAX_S": 246.86,                    # g-1102's first greedy batch (KCR: 246.9)
        "BATCH_MAX_S": 250.305,                         # g-1102's slowest capped 32-row batch (KCR: 250.3)
        "EARLY_MAX_S": 19.703,                          # b5e5-1101 (KCR: 20)
        "OUTSIDE_MAX_S": 162.778,                       # g-1103 (KCR: 163)
        "ARM_JOB_MAX_S": 8466.0,                        # g-1103, 141.1 min
        "PRE_TRAINING_S_MAX": 1261.7852040079888,       # b5e5-1101 (KCR: 1,262)
        "PRE_MS_PER_STEP_MAX": 104.31670475918509,      # b5e5-1102 (KCR: 104.3)
        "A0_PADDED_TOKENS_PER_STEP": 41311.74,          # 1103 / g-1103: 1,569,846 padded tokens / 38 steps
        "basis_units": 8, "basis_fine_tune_only": 7,
    },
}
# KCR §4's printed constants (R: KCR:100), kept so that test 1 can show KCR's own arithmetic beside the rule's.
KCR_PRINTED = {
    "olmo2-7b": {"TRAIN_STEP_MAX_S": 24.26, "FIRST_BATCH_MAX_S": 314.0, "BATCH_MAX_S": 240.9, "EARLY_MAX_S": 20.0,
                 "OUTSIDE_MAX_S": 109.0, "ARM_JOB_MAX_S": 6450.0, "A0_PADDED_TOKENS_PER_STEP": 38342.79},
    "llama31-8b": {"TRAIN_STEP_MAX_S": 22.89, "FIRST_BATCH_MAX_S": 246.9, "BATCH_MAX_S": 250.3, "EARLY_MAX_S": 20.0,
                   "OUTSIDE_MAX_S": 163.0, "ARM_JOB_MAX_S": 8466.0, "A0_PADDED_TOKENS_PER_STEP": 41311.74},
}
BASIS_MAXIMA = {"TRAIN_STEP_MAX_S": "train_step_max_s", "FIRST_BATCH_MAX_S": "first_batch_max_s",
                "BATCH_MAX_S": "batch_max_s", "EARLY_MAX_S": "early_max_s", "OUTSIDE_MAX_S": "outside_max_s",
                "ARM_JOB_MAX_S": "arm_job_max_s", "PRE_TRAINING_S_MAX": "preflight_training_s_max",
                "PRE_MS_PER_STEP_MAX": "preflight_ms_per_step_full_max"}   # constant -> the basis family field

# ===== kinds =====
MEASURED_KINDS = ("arm", "a0_arm", "evalonly", "ref_train")   # R1 K1: ref_train = recipe G's reference, an a0-like
#                                           38-step train + evaluation under RECIPE_G (Part 2 §3.2; the basis holds
#                                           the family's G config among its three recipes, KCR:123)
# KD6: every other kind runs alone on a single-job pod with an explicit E cap until it is measured. Each entry gives
# the E upper's formula inputs and its basis; e_upper_s() turns them into seconds, e_cap_hours() into the pod's cap.
SIZE_FACTOR_1B_TO_78B = 2.3               # E: a 7-8B job is 1.9x (OLMo) to 2.3x (Llama) a 1B job (RP:43 via the plan §4)
WIDE_CAP_FACTOR = 1.5                     # R: the stage-1 kit's DIAG_UPPER_FACTOR (Gate B's [D13]; untimed kinds)
STATE_WRITE_S = 300.0                     # E: one adapter + optimizer + RNG state of about 1.9 GB written and fsynced
REF_FORWARD_SHARE = 0.5                   # R: stage1_rules.py REF_FORWARD_SHARE (B+Qi's reference forward; I, unmeasured)
Y_ENGINE_FACTOR = 2.0                     # E: engine Y has no 7-8B timing; its training term is doubled until KD9
STAGE1_1B_ESTIMATES_S = {"rep_pass": 3600.0, "untuned_answers": 7560.0, "l1_scan": 3600.0, "classifier": 2012.0,
                         "c0": 2400.0, "anchor": 900.0, "safe_lora_hash": 600.0, "safe_lora_transform": 88.02,
                         "w1_18": 1800.0}
#                                           R: runkit/stage1-olmo/stage1_rules.py:87 DIAG_ESTIMATE_S (rep_pass 3,600 s,
#                                           the 1 h estimate at 1B), C0_S, ANCHOR_UPPER_S, SAFE_LORA_*, W1_18_UPPER_S
#                                           (stage1_rules.py:84: 0.5 h, E there)
A1_PASS_CAP_H_MAX = 16.5                  # KD6, PP8: A1's attributes pass (a1_pass) at RP:43's 6-11 h is a 16.5 h cap at most
S_POOL_CHUNKS = 16                        # R: PR4 S4 row via ruling 12: 512 prompts in 32-prompt chunks
S3_POOL_ITEMS = 861                       # R: scripts/scale78b/settings/pins_78b.json shared.sealed_lists_1b.s3_safe.items
#                                           (the untuned pass's S3 call answers every prompt of the s3_safe pool; PP2)
O_EXT_PROMPTS = 600                       # R: stage1_rules.py O_ONLY_FACTOR: the 500-prompt bank plus the dev 100
E_KINDS = ("untuned_answers", "o_only", "o_only_with_regenerate", "anchor", "rep_pass", "a1_pass",
           "l1_scan", "classifier", "c0", "retrain", "ref_train_bqi", "safe_lora", "ref_eval", "w1_18", "b10_certify")
# R1 K1, the O-ext cap term (DESO item 24 (a), (b); Part 2 §4.3; GXB O12). Block A and B arm jobs (arm, a0_arm) and
# recipe G's ref_train evaluate O-ext on the new unit's e1 state in the same job (DES E3), and so do the references
# (ref_eval and safe_lora per point, ref_train_bqi once; DESO item 24 (b)). The in-job pass answers the 400 PHTest
# prompts (Part 2 §4.1; the dev 100 are the arm's own dev-bank answers) in ceil(400 / 32) = 13 batches, every batch at
# the 2,048 cap (M: the family's first-batch and capped-batch maxima), with half the scoring allowance for the guard
# (E) and the early and outside time (M): 3,959 s OLMo-2-7B, 4,061 s Llama-3.1-8B (Part 2 §4.3's figures). Until the
# pre-block-A O pods measure it, the term is x OEXT_TERM_FACTOR = 1.5, the kit's upper-factor form (DESO item 24 (a)).
# A measured value replaces it by a recorded lead step (OEXT_TERM_MEASURED_S[family], seconds per pass, then x 1).
# Branch full's term (every batch at the full cap) is used under both branches: under Branch 128 the pass is shorter
# (E: about 0.3-0.45 h, Part 2 §4.3), so the full term is an upper bound; caps use Branch full until W1-18's record
# (the stage-1 kit's BRANCH_DEFAULT rule). Block 0's arms (N) carry no O-ext step (their O comes from
# o_only_with_regenerate, Part 2 §4.5): a job carries the term only when planned with oext=True.
OEXT_PHTEST_PROMPTS = 400                 # R: Part 2 §4.1 (the sealed PHTest record a810574e..., 400 items)
OEXT_TERM_FACTOR = 1.5                    # DESO item 24 (a): x 1.5 until measured
OEXT_TERM_MEASURED_S: dict[str, float | None] = {"olmo2-7b": None, "llama31-8b": None}   # null until a recorded step
OEXT_CAP_KINDS = frozenset({"arm", "a0_arm", "ref_train"})          # measured kinds that may carry the in-job term
OEXT_REF_KINDS = frozenset({"ref_eval", "safe_lora", "ref_train_bqi"})   # E kinds whose upper always carries it
KINDS = MEASURED_KINDS + E_KINDS
# The need printout's labels (PP3, PP8; the check's M3): what each S_78 or scorer kind is, in the kit's own words.
KIND_LABELS = {
    "rep_pass": "REQ-3's representation pass, scripts/stage1/representation_pass.py; recipe S_78 (PP3, PP4, PP8)",
    "a1_pass": "A1's attributes pass on the a0-1101 retrain's q and e1 states; recipe S_78; A1's 16.5 h cap at most (PP3, PP8, KD6)",
    "classifier": "the classifier under recipe S_78, as at 1B (PP4, PP8)",
    "retrain": "the a0-1101 retrain, engine Y, recipe S_78 after the anchor job (ruling 10, addendum A2, A8)",
    "untuned_answers": "the untuned-answers pass under the main recipe (PP1, PP2)",
    "o_only": "the O-ext pass at one state (the check's M1)",
    "anchor": "the anchor job before S_78 (addendum A1, A2)",
    "l1_scan": "the L1 scan (engine X; PP4)",
    "c0": "c0 on an engine-X unit (B17's X-pin check)",
    "o_only_with_regenerate": "a reused a0 side unit regenerated train only, checked against its fingerprints, then "
                              "the O-ext pass on its e1 state (PP17; ruling 7; M1)",
    "w1_18": "the 7-8B W1-18 check on the reused side units, one pod, one record per family (DES E2; DESO2 item 37; "
             "GXB O4)",
    "ref_train": "recipe G's reference under RECIPE_G, with its in-job O-ext pass (Part 2 §3.2, §4.3)",
}
COUNTED_KINDS = frozenset({"arm", "a0_arm", "evalonly", "c0", "retrain", "ref_train_bqi", "o_only_with_regenerate",
                           "ref_train"})
#                                           counted toward MAX_ARMS_PER_POD_78B (the E kinds run alone anyway)


class Refused(ValueError):
    """A key, kind, field or pod the rule refuses (the caller records the case; nothing runs)."""


# ===== copied helpers (equal to the stage-1 kit's on the same inputs; test 9) =====
def hours(seconds: float) -> float:
    return seconds / 3600


def round_up_s(seconds: float) -> float:
    """Up to the next CAP_STEP_S (a value within a microsecond of a step stays on it)."""
    return math.ceil(round(seconds, 6) / CAP_STEP_S) * CAP_STEP_S


def pod_sizes(n: int) -> list[int]:
    """ceil(n / MAX_ARMS_PER_POD) pods, as even as possible, the earlier pods taking the one extra run (8 -> 4 + 4,
    6 -> 3 + 3, 5 -> 3 + 2, 20 -> 4 x 5, 14 -> 4 + 4 + 3 + 3)."""
    m = MAX_ARMS_PER_POD
    if type(m) is not int or m < 1:
        raise ValueError("MAX_ARMS_PER_POD must be a positive integer")
    if type(n) is not int or n < 1:
        raise ValueError("a block needs at least one run")
    k = -(-n // m)
    return [n // k + (1 if i < n % k else 0) for i in range(k)]


def guard_usd(cap_h: float) -> float:
    """What the budget guard needs for one pod of this cap: $6 + cap x $1.85 (the hold is 0, KD4)."""
    return RESERVE_USD + GATE_B_HOLD_USD + cap_h * PLANNING_PRICE_USD


def cents(usd: float) -> float:
    """An amount rounded to the cent, half up (decimal, not binary, rounding)."""
    return float(Decimal(repr(usd)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def launch_pod_spend_usd(pod: dict) -> float:
    """A launch pod's upper spend: a judge pod's cap x $1.79; a kit pod's recorded spend_usd, else pod_spend_usd."""
    if pod.get("judge"):
        return pod["cap_hours"] * RATE_USD
    if "spend_usd" in pod:
        return pod["spend_usd"]
    return pod_spend_usd(pod["kinds"])


def funding_need_usd(launches: list[list[dict]], factor: float = 1.0) -> dict:
    """The stage-1 kit's rule, unchanged: ``launches`` in path order; each a list of pods {"cap_hours", "spend_usd" or
    "kinds"} or judge pods. The base need = the largest term, rounded to the cent; the need = factor x the rounded
    base, rounded to the cent; the contingency = need - base."""
    terms, spent = [], 0.0
    for launch in launches:
        terms.append(spent + RESERVE_USD + PLANNING_PRICE_USD * sum(p["cap_hours"] for p in launch))
        spent += sum(launch_pod_spend_usd(p) for p in launch)
    base = cents(max(terms))
    need = cents(float(Decimal(repr(base)) * Decimal(repr(factor))))
    return {"base_need_usd": base, "factor": factor, "need_usd": need, "contingency_usd": cents(need - base),
            "terms_usd": terms}


def gate(remaining_s: float | None, requirement_s: float) -> bool:
    """A job starts only when the remaining time is known and at least its requirement (None never fits)."""
    return remaining_s is not None and remaining_s >= requirement_s


# ===== the basis =====
def basis_path() -> pathlib.Path:
    return HERE / BASIS_FILE


def basis_sha256(path: pathlib.Path | None = None) -> str:
    return hashlib.sha256((path or basis_path()).read_bytes()).hexdigest()


def load_basis(path: pathlib.Path | None = None) -> dict:
    """The pinned basis, or Refused when its bytes differ from BASIS_SHA256 (a re-measure re-pins by a recorded step)."""
    path = path or basis_path()
    digest = basis_sha256(path)
    if digest != BASIS_SHA256:
        raise Refused(f"{path.name} has SHA-256 {digest[:12]}..., the pin is {BASIS_SHA256[:12]}...")
    return json.loads(path.read_text(encoding="utf-8"))


# ===== keys and kinds =====
def family_of(name: str) -> dict:
    if name not in FAMILIES:
        raise Refused(f"unknown family {name!r}")
    return FAMILIES[name]


def recipe_s_or_refuse(family: str) -> str:
    """Addendum A1: the family's recipe-S_78 config_sha256, or Refused while RECIPE_S[family] is None (the anchor job
    has not run, or the maker has not written and the lead has not committed and pinned the config). A pin that is
    not a 64-hex config_sha256 refuses too."""
    family_of(family)
    value = RECIPE_S[family]
    if value is None:
        raise Refused(f"recipe S_78 for {family} is not written yet (addendum A1: it follows the family's anchor job); "
                      f"the kinds that need it ({', '.join(sorted(S78_KINDS))}) do not run")
    if not isinstance(value, str) or not CONFIG_SHA256.match(value):
        raise Refused(f"RECIPE_S[{family!r}] is not a config_sha256")
    return value


def kit_of(family: str) -> dict:
    """The family's kit block (KIT), or Refused for an unknown family."""
    family_of(family)
    return KIT[family]


def pin_or_refuse(pin: str, family: str) -> str:
    """Addendum A13's pattern for every per-family recipe pin (PINS: RECIPE_S, RECIPE_G, RECIPE_BQI): the family's
    config_sha256, or Refused while the pin is None (not yet filled by a recorded lead step) or not a 64-hex string."""
    family_of(family)
    if pin not in PINS:
        raise Refused(f"unknown pin {pin!r}")
    value = PINS[pin][family]
    if value is None:
        raise Refused(f"{pin} for {family} is null until the lead fills it by a recorded step (addendum A13); the kinds "
                      f"that need it ({', '.join(sorted(k for k, p in PINNED_RECIPE_KINDS.items() if p == pin)) or 'none yet'}) "
                      "do not run")
    if not isinstance(value, str) or not CONFIG_SHA256.match(value):
        raise Refused(f"{pin}[{family!r}] is not a config_sha256")
    return value


def oext_y_or_refuse(family: str) -> dict:
    """R1 K1 (GXB T-O3; DESO2 item 24 (c)): the family's OEXT_78B_Y record (B+Qi's O-ext pass on engine Y), or
    Refused while it is null (with its filling event), or while ENGINE_Y or the family's RECIPE_BQI is still null (its
    fill comes after both), or when it is not OEXT_78B's form."""
    family_of(family)
    value = OEXT_78B_Y[family]
    if value is None:
        raise Refused(f"OEXT_78B_Y[{family!r}] is null: B+Qi's O-ext pass on engine Y waits for "
                      f"{SC_PIN_EVENTS['OEXT_78B_Y']}")
    if ENGINE_Y is None or RECIPE_BQI[family] is None:
        raise Refused(f"OEXT_78B_Y[{family!r}] is filled before ENGINE_Y and RECIPE_BQI[{family!r}]: its fill comes "
                      "after both (DESO2 item 24 (c))")
    problem = oext_form_problem(value, family, "Y")
    if problem:
        raise Refused(f"OEXT_78B_Y[{family!r}] is not OEXT_78B's form: {problem}")
    return value


def recipe_bqi_or_refuse(family: str) -> str:
    """D1 (the re-verifier; KCR:128): B+Qi's config_sha256, or Refused while RECIPE_BQI[family] is None."""
    return pin_or_refuse("RECIPE_BQI", family)


def engine_allowed(kind: str, engine_sha256) -> bool:
    """PP16 first: a wrapper kind (X_ONLY_KINDS; PP4) runs on engine X only. Then A13: engine X (the measured basis)
    runs every kind. Engine Y, once ENGINE_Y is filled, runs the other kinds with an explicit E cap (E_KINDS: the
    retrain, a1_pass, ...); the measured kinds run on Y only after KD9's re-measure sets Y_MEASURED. Any other engine,
    and Y while its pin is None, is refused."""
    if kind in X_ONLY_KINDS:
        return engine_sha256 == ENGINE_X
    if engine_sha256 == ENGINE_X:
        return True
    if ENGINE_Y is not None and engine_sha256 == ENGINE_Y:      # R3 K3 (R-67): measured kinds need the record pin too
        return kind in E_KINDS or (Y_MEASURED is True and Y_MEASURED_RECORD is not None)
    return False


def sealed_set_or_refuse(family: str) -> dict:
    """The family's sealed edit set {path, sha256} (SEALED_SETS), or Refused while its MANIFEST pin is None (the Llama
    set: not merged yet, A13) or not a 64-hex string. The caller reads the manifest at that path and checks its hash."""
    family_of(family)
    pin = SEALED_SETS[family]
    if pin.get("sha256") is None:
        raise Refused(f"the {family} sealed set's MANIFEST pin is null (addendum A13): the lead fills "
                      f"SEALED_SETS[{family!r}]['sha256'] by a recorded step after merging {pin['path']}; until then no "
                      f"{family} edit arm is planned")
    if not isinstance(pin["sha256"], str) or not CONFIG_SHA256.match(pin["sha256"]):
        raise Refused(f"SEALED_SETS[{family!r}]['sha256'] is not a SHA-256")
    return {"path": pin["path"], "sha256": pin["sha256"]}


def sealed_edit_entry(entry) -> bool:
    """Is ``entry`` (one element of a sealed set's MANIFEST ``files``) an edit file's entry, in either committed form
    (D1)? Gate B's form marks edits by ``role == "edit"``; the Llama set's form carries a descriptive role string. Both
    put every edit under ``edits/`` with a ``family`` in EDIT_FAMILIES, a 64-hex ``sha256`` and an ``arm``; the
    non-edit entries (Gate B's "counts" and "gate-c sample") have paths outside edits/ and no family. The entry's
    text is never read beyond these keys."""
    if not isinstance(entry, dict):
        return False
    role, path = entry.get("role"), entry.get("path")
    if not (isinstance(role, str) and role) or not (isinstance(path, str) and EDIT_PATH_RE.match(path)):
        return False
    return entry.get("family") in EDIT_FAMILIES and isinstance(entry.get("sha256"), str) \
        and bool(CONFIG_SHA256.match(entry["sha256"])) and isinstance(entry.get("arm"), str) and bool(entry["arm"])


def block0_r_edits(manifest: dict, draws: tuple = BLOCK0_R_DRAWS) -> dict[int, dict]:
    """N's R edits from a sealed set's MANIFEST document, in either form (D1): draw -> {"draw", "seed", "arm", "path",
    "sha256"} for every draw in ``draws``. An edit entry is R_d only by ``family == "R"`` AND ``draw == d`` (Gate B's M
    edits carry draws 1-2 of their own); a Llama-form ``seed`` must be R_SEED_BASE + d; a draw listed twice, or
    missing, is Refused. ``path`` is relative to the set's out/ folder (the caller joins it)."""
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise Refused("the sealed set's MANIFEST.json is not a {files: [...]} manifest")
    out: dict[int, dict] = {}
    for e in manifest["files"]:
        if not sealed_edit_entry(e) or e.get("family") != "R":
            continue
        d = e.get("draw")
        if isinstance(d, bool) or type(d) is not int or d not in draws:
            continue
        seed = e.get("seed", R_SEED_BASE + d)
        if seed != R_SEED_BASE + d:
            raise Refused(f"the sealed set's MANIFEST lists R_d{d} at seed {seed!r}, not {R_SEED_BASE + d} (R_d at 1100 + d)")
        if d in out:
            raise Refused(f"the sealed set's MANIFEST lists two R_d{d} edit entries; the lead decides")
        out[d] = {"draw": d, "seed": R_SEED_BASE + d, "arm": e["arm"], "path": e["path"], "sha256": e["sha256"]}
    missing = [d for d in draws if d not in out]
    if missing:
        raise Refused(f"the sealed set's MANIFEST lists no R edit for draw(s) {missing} (R_d<d> under edits/, family R)")
    return out


def idle_storage(n_pods: int, volume_gb: int = VOLUME_GB) -> dict:
    """KD5's idle-storage line (Part 1 §12; KCR:161): a stopped pod keeps its volume at IDLE_STORAGE_USD_PER_GB_MONTH,
    about $0.33 per day per stopped 50 GB pod; ``n_pods`` is the number of this block's pods kept stopped for their
    states (every N pod keeps its e1 states until the state rule's pull and verified backup). An E; counted in no guard
    (the guard reads running pods only), so it erodes the balance on its own."""
    if type(n_pods) is not int or n_pods < 0:
        raise Refused("the idle-storage line needs a whole number of pods")
    per_pod_day = cents(volume_gb * IDLE_STORAGE_USD_PER_GB_MONTH / IDLE_DAYS_PER_MONTH)
    per_month = n_pods * volume_gb * IDLE_STORAGE_USD_PER_GB_MONTH          # unrounded; the day total is its 1/30
    return {"volume_gb": volume_gb, "usd_per_gb_month": IDLE_STORAGE_USD_PER_GB_MONTH,
            "usd_per_pod_day": per_pod_day, "n_pods_kept": n_pods, "usd_per_day": cents(per_month / IDLE_DAYS_PER_MONTH),
            "usd_per_month": cents(per_month),
            "basis": (f"E: RunPod lists a stopped pod's volume at ${IDLE_STORAGE_USD_PER_GB_MONTH:.2f} per GB per month "
                      f"(KCR:161, read 16 Oct 2026); {volume_gb} GB / {IDLE_DAYS_PER_MONTH} days = ${per_pod_day:.2f} per "
                      "pod per day while it keeps its states (KD5); counted in no guard")}


def block0_runs(family: str) -> list[tuple[str, int]]:
    """N's runs for the family (ruling 11; Part 1 §3.1): R_1-R_3 at 1101-1103 (R_d at R_SEED_BASE + d) on both
    families, and on Llama-3.1-8B a0 at 1103 (ruling 8)."""
    runs = [(a, s) for a, s in kit_of(family)["block0"]["runs"]]
    expected = [("R", R_SEED_BASE + d) for d in BLOCK0_R_DRAWS]
    if family == "llama31-8b":
        expected.append(("a0", A0_SEED_1103))
    if runs != expected:
        raise Refused(f"{family}'s block-0 table is not N's layout")
    return runs


def block0_jobs(family: str) -> list[dict]:
    """N's job records for the family's one pod: ``arm`` at 33 steps for each R draw, ``a0_arm`` at 38 for a0."""
    out = []
    for arm, seed in block0_runs(family):
        kind = "a0_arm" if arm == "a0" else "arm"
        out.append(job_record(family, kind, STEPS["a0"] if arm == "a0" else STEPS["remove"], arm, seed))
    return out


def check_keys(family: str, kind: str, recipe_sha256: str, engine_sha256: str, gpu_name: str, manifest_sha256: str,
               bank: dict, oext_bank: str | None = None) -> None:
    """KCR §4 and KCR:147, the pod's key check (before the pod): the kind must be known; the recipe must be on the
    family's allow-list (measured kinds and the other E kinds), or recipe S_78 for the kinds that need it (S78_KINDS,
    through recipe_s_or_refuse), RECIPE_G for ref_train, RECIPE_BQI for B+Qi; on a family whose anchor job stopped,
    the retrain under the family's main config only and the other S_78 kinds never (R1 K1, GXB O6; DESO2 item 36);
    the engine must be one with a measured basis (X); the GPU the measured one; the prepared manifest the family's; the
    evaluation bank exactly BANK (A-V3). R1 K1 (Part 2 §4.3; SCOUT §1.3): a job with an O-ext step also names its O-ext
    bank's SHA-256 (``oext_bank``), the second bank pin beside BANK: it must equal OEXT_78B[family]'s inputs.oext_bank
    (null refuses), and only a kind with an O-ext step (OEXT_BANK_KINDS) may name one."""
    family_of(family)
    check_kind(kind)
    stop = anchor_stop_problem_for(family, kind)
    if stop:
        raise Refused(stop)
    if kind == "retrain" and family_stopped(family):
        if recipe_sha256 != CONFIGS[family]["main"][1]:
            raise Refused(f"the retrain on {family}, whose anchor job stopped, runs under the family's main config only "
                          f"(DESO2 item 36 (2)); recipe {str(recipe_sha256)[:12]}... is not it")
    elif kind in S78_KINDS:
        if recipe_sha256 != recipe_s_or_refuse(family):
            raise Refused(f"{kind} runs under recipe S_78 only; recipe {str(recipe_sha256)[:12]}... is not {family}'s S_78")
    elif kind in BQI_KINDS:
        if recipe_sha256 != recipe_bqi_or_refuse(family):
            raise Refused(f"{kind} runs under RECIPE_BQI only; recipe {str(recipe_sha256)[:12]}... is not {family}'s B+Qi")
    elif kind in G_KINDS:
        if recipe_sha256 != pin_or_refuse("RECIPE_G", family):
            raise Refused(f"{kind} runs under RECIPE_G only; recipe {str(recipe_sha256)[:12]}... is not {family}'s G")
    elif recipe_sha256 not in RECIPE_ALLOW[family]:
        raise Refused(f"recipe {str(recipe_sha256)[:12]}... is not on the {family} allow-list")
    if not engine_allowed(kind, engine_sha256):
        raise Refused(f"engine {str(engine_sha256)[:12]}... has no measured basis for {kind} (X runs every kind and "
                      "the wrapper kinds only, PP16; Y runs the other E-capped kinds once ENGINE_Y is filled and "
                      "measured kinds after KD9; A13)")
    if gpu_name != GPU_NAME:
        raise Refused(f"GPU {gpu_name!r} has no measured basis")
    if manifest_sha256 != MANIFESTS[family]:
        raise Refused(f"prepared manifest {str(manifest_sha256)[:12]}... is not {family}'s ({MANIFESTS[family][:12]}...)")
    if not isinstance(bank, dict) or set(bank) != set(BANK):
        raise Refused(f"the evaluation bank record must hold exactly {sorted(BANK)}")
    for key, value in BANK.items():
        if type(bank[key]) is not int or bank[key] != value:
            raise Refused(f"evaluation bank {key} = {bank[key]!r}; the basis holds for {value} only (KCR:147)")
    if oext_bank is not None:
        if kind not in OEXT_BANK_KINDS:
            raise Refused(f"{kind} has no O-ext step: it names no O-ext bank")
        engine = "X" if engine_sha256 == ENGINE_X else "Y"           # GXB R-5: the engine's own O-ext pin
        name, pin = (f"OEXT_78B[{family!r}]", OEXT_78B[family]) if engine == "X" else \
            (f"OEXT_78B_Y[{family!r}]", OEXT_78B_Y[family])
        if pin is None or oext_form_problem(pin, family, engine):
            raise Refused(f"the O-ext bank pin is null or off its form ({name}): "
                          f"{SC_PIN_EVENTS['OEXT_78B' if engine == 'X' else 'OEXT_78B_Y']}")
        if oext_bank != pin["inputs"]["oext_bank"]:
            raise Refused(f"O-ext bank {str(oext_bank)[:12]}... is not {family}'s pinned O-ext bank "
                          f"({pin['inputs']['oext_bank'][:12]}...)")


def check_kind(kind: str) -> str:
    if kind in MEASURED_KINDS:
        return "measured"
    if kind in E_KINDS:
        return "single-job E cap"
    raise Refused(f"job kind {kind!r} has no 7-8B basis and no E cap: it does not run")


def steps_of(dose: str) -> int:
    if dose not in STEPS:
        raise Refused(f"unknown dose {dose!r}")
    return STEPS[dose]


# ===== the M-cap rule =====
def finite(value) -> float:
    """A finite number, else Refused (Gate B's 'none never fits': a missing or bad field refuses)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise Refused(f"a required field is missing or not finite: {value!r}")
    return float(value)


def gen_allcap_of(c: dict) -> float:
    """All 34 generation batches at the cap: the first greedy batch at its own maximum (KCR:64), the rest at
    BATCH_MAX. ``c`` is a family's constants block (FAMILIES[family], or KCR_PRINTED[family] in test 1)."""
    return max(c["FIRST_BATCH_MAX_S"], c["BATCH_MAX_S"]) + (BATCHES - 1) * c["BATCH_MAX_S"]


def gen_allcap_s(family: str) -> float:
    return gen_allcap_of(family_of(family))


def train_scale_of(c: dict, padded_tokens_per_step: float | None) -> float:
    """KCR:104: max(1, the arm's padded tokens per step / the a0's), from token counts only; None means 1."""
    if padded_tokens_per_step is None:
        return 1.0
    return max(1.0, finite(padded_tokens_per_step) / c["A0_PADDED_TOKENS_PER_STEP"])


def train_scale(family: str, padded_tokens_per_step: float | None) -> float:
    return train_scale_of(family_of(family), padded_tokens_per_step)


def oext_pass_of(c: dict) -> float:
    """One in-job O-ext pass before its factor (R1 K1; Part 2 §4.3): the 400 PHTest prompts in ceil(400 / 32) = 13
    batches, the first at the first-batch maximum and the rest at the capped-batch maximum (M), half the scoring
    allowance (E) and the early and outside time (M). 3,958.9 s OLMo-2-7B, 4,061.4 s Llama-3.1-8B."""
    batches = -(-OEXT_PHTEST_PROMPTS // GENERATION_BATCH)
    return (max(c["FIRST_BATCH_MAX_S"], c["BATCH_MAX_S"]) + (batches - 1) * c["BATCH_MAX_S"] + 0.5 * SCORE_ALLCAP_S
            + c["EARLY_MAX_S"] + c["OUTSIDE_MAX_S"])


def oext_term_s(family: str) -> float:
    """The O-ext cap term of one job (DESO item 24 (a)): the measured value once a recorded lead step fills
    OEXT_TERM_MEASURED_S[family] (x 1), else the pass of oext_pass_of x OEXT_TERM_FACTOR (1.5). A filled value that is
    not a positive finite number refuses."""
    c = family_of(family)
    measured = OEXT_TERM_MEASURED_S[family]
    if measured is not None:
        if finite(measured) <= 0:
            raise Refused(f"OEXT_TERM_MEASURED_S[{family!r}] is not a positive number of seconds")
        return float(measured)
    return OEXT_TERM_FACTOR * oext_pass_of(c)


def upper_m_of(c: dict, steps: int | None, kind: str = "arm", padded_tokens_per_step: float | None = None,
               oext_s: float = 0.0) -> float:
    """The measured physical upper bound of one job (KCR §4) from a constants block: training + all-capped
    generation + the scoring allowance + the early stages + the time outside the stages, plus ``oext_s`` (the O-ext cap
    term of a job with an in-job O-ext step; R1 K1). ``evalonly`` has no training term."""
    if check_kind(kind) != "measured":
        raise Refused(f"{kind!r} is an E-capped kind: use e_upper_s")
    if kind == "evalonly":
        training = 0.0
    else:
        if type(steps) is not int or steps < 1:
            raise Refused("an arm needs its optimizer step count")
        training = steps * c["TRAIN_STEP_MAX_S"] * train_scale_of(c, padded_tokens_per_step)
    return training + gen_allcap_of(c) + SCORE_ALLCAP_S + c["EARLY_MAX_S"] + c["OUTSIDE_MAX_S"] + oext_s


def upper_m_s(family: str, steps: int | None, kind: str = "arm", padded_tokens_per_step: float | None = None,
              oext: bool = False) -> float:
    """upper_m_of for the family; ``oext`` adds the family's O-ext cap term (OEXT_CAP_KINDS only; R1 K1)."""
    if oext and kind not in OEXT_CAP_KINDS:
        raise Refused(f"{kind} carries no in-job O-ext step (the term is for {', '.join(sorted(OEXT_CAP_KINDS))})")
    return upper_m_of(family_of(family), steps, kind, padded_tokens_per_step, oext_term_s(family) if oext else 0.0)


def speed_factor(family: str, preflight: dict) -> float:
    """s_pod from the pod's preflight (training_s and ms_per_step_full; KCR:107): at least 1, so it only raises the
    requirement; above SPEED_REFUSAL the pod is refused before any job (KCR:108); a missing or non-finite field
    refuses."""
    f = family_of(family)
    if not isinstance(preflight, dict):
        raise Refused("no preflight record")
    training_s = finite(preflight.get("training_s"))
    ms_full = finite(preflight.get("ms_per_step_full"))
    if training_s <= 0 or ms_full <= 0:
        raise Refused("a preflight speed field is not positive")
    s = max(1.0, training_s / f["PRE_TRAINING_S_MAX"], ms_full / f["PRE_MS_PER_STEP_MAX"])
    if s > SPEED_REFUSAL:
        raise Refused(f"the pod is {s:.3f} x the slowest measured pod (limit {SPEED_REFUSAL}): refused before any job")
    return s


def sanity_floor_s(family: str, preflight: dict, steps: int | None, kind: str = "arm") -> float:
    """F_pre (KCR:109): the pod's typical-case projection with the preflight's floors and the start margin. It can
    only raise the requirement (the caller takes the max)."""
    if not isinstance(preflight, dict):
        raise Refused("no preflight record")
    training_s = finite(preflight.get("training_s"))
    untuned = finite(preflight.get("untuned_projected_s"))
    training = 0.0 if kind == "evalonly" else training_s * steps / FIXTURE_STEPS
    return training + untuned + OVERHEAD_FLOOR_S + SAFETY_MARGIN_S + START_MARGIN_S


def requirement_s(family: str, steps: int | None, kind: str = "arm", s_pod: float = 1.0, s_obs: float = 1.0,
                  preflight: dict | None = None, padded_tokens_per_step: float | None = None,
                  oext: bool = False) -> float:
    """The start requirement (KCR §4): max(s_pod, s_obs) x upper_M + START_MARGIN_S, never below F_pre when the
    preflight is given. s_pod and s_obs below 1 count as 1 (a faster pod never lowers the bound). ``oext``: the job's
    upper_M carries the O-ext cap term (R1 K1)."""
    s = max(1.0, finite(s_pod), finite(s_obs))
    need = s * upper_m_s(family, steps, kind, padded_tokens_per_step, oext) + START_MARGIN_S
    if preflight is not None:
        need = max(need, sanity_floor_s(family, preflight, steps, kind))
    return need


def s_obs_from_progress(family: str, progress_rows: list) -> float:
    """KD11 (KCR:113): the finished arm's slowest capped 32-row generation batch after the first, over BATCH_MAX, at
    least 1. Batch seconds are the differences of consecutive ``generate`` rows' elapsed_s, as derive_78b_basis.py
    measures them (the first greedy batch carries the process start effect and is excluded; a sampled series' first
    batch counts, with its small stage gap). An empty or missing record refuses the next arm."""
    f = family_of(family)
    if not isinstance(progress_rows, list) or not progress_rows:
        raise Refused("no progress record for the finished arm: the next arm does not start")
    rows = [r for r in progress_rows if isinstance(r, dict) and r.get("kind") == "generate"]
    if len(rows) < 2:
        raise Refused("the finished arm's progress record holds no generation batches")
    # A-V1: every generate row must carry its integer ``capped`` and ``rows`` (a drifted format must not pass as
    # s_obs = 1 and switch KD11 off), and the record must hold 32-row batches at all (the batch size has a basis).
    for row in rows:
        batch_count(row, "capped")
        batch_count(row, "rows")
    if not any(row["rows"] == GENERATION_BATCH for row in rows):
        raise Refused(f"the finished arm's progress record holds no {GENERATION_BATCH}-row batch: no basis for s_obs")
    slowest = 0.0
    for previous, row in zip(rows, rows[1:]):
        seconds = round(finite(row.get("elapsed_s")) - finite(previous.get("elapsed_s")), 3)   # the basis's precision
        if row["capped"] > 0 and row["rows"] == GENERATION_BATCH:
            slowest = max(slowest, seconds)
    return max(1.0, slowest / f["BATCH_MAX_S"])


def batch_count(row: dict, key: str) -> int:
    """A generate row's ``capped`` or ``rows``: a non-negative integer, else Refused (A-V1)."""
    value = row.get(key)
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise Refused(f"a generate row of the finished arm lacks an integer {key!r} ({value!r}): the next arm does not start")
    return value


def s_obs_defers(s_obs: float) -> bool:
    """KD11: later arms defer when the finished arm ran its capped batches more than 1.15 x slower than the basis."""
    return finite(s_obs) > S_OBS_REFUSAL


# ===== per-pod: measured uppers, caps, guards, spend =====
def measured_upper_s(family: str, kind: str = "arm") -> float:
    """The term a finished job counts in later jobs' caps, and its spend upper: 1.15 x the slowest measured
    fine-tune-only job (KCR:119)."""
    if check_kind(kind) != "measured":
        raise Refused(f"{kind!r} has no measured upper: it runs alone with its E cap")
    return MEASURED_MARGIN * family_of(family)["ARM_JOB_MAX_S"]


def job_record(family: str, kind: str, steps: int | None = None, arm: str | None = None, seed: int | None = None,
               padded_tokens_per_step: float | None = None, n_points: int = 1, oext: bool = False) -> dict:
    """One plan job with its timing fields from this module's rules (the shape the stage-1 kit's plan uses). Refuses
    an unknown kind, an arm without its step count and, for every kind, ``n_points`` that is not a positive integer
    (D2: the E kinds refused it through e_upper_s; the measured kinds now refuse it here too). R1 K1: ``oext`` plans
    the job with its in-job O-ext step (blocks A and B; OEXT_CAP_KINDS): its upper, measured upper and spend upper
    each carry the O-ext cap term (oext_term_s), so a later job's cap counts the earlier jobs' O-ext passes too."""
    if type(n_points) is not int or n_points < 1:
        raise Refused("at least one evaluation point")
    if not isinstance(oext, bool):
        raise Refused("oext is True or False")
    group = check_kind(kind)
    if group == "measured":
        if kind in ("a0_arm", "ref_train"):
            steps = STEPS["a0"] if steps is None else steps
        if kind == "evalonly":
            steps = None
        up = upper_m_s(family, steps, kind, padded_tokens_per_step, oext)
        measured = measured_upper_s(family, kind) + (oext_term_s(family) if oext else 0.0)
        unmeasured = False
    else:
        if oext:
            raise Refused(f"{kind} is an E-capped kind: its O-ext term, if any, is in its E upper (OEXT_REF_KINDS)")
        up = e_upper_s(family, kind, n_points)["upper_s"]
        measured = up                       # an E kind's spend upper is its E upper (nothing measured yet)
        unmeasured = True
    job = {"kind": kind, "family": family, "arm": arm, "seed": seed, "steps": steps,
           "upper_s": up, "start_requirement_s": up + START_MARGIN_S, "measured_upper_s": measured,
           "spend_upper_s": measured, "counted": 1 if kind in COUNTED_KINDS else 0, "unmeasured": unmeasured,
           "n_points": n_points, "status": "planned"}
    if oext or padded_tokens_per_step is not None:       # GXB R-3: the two keys only on block A and B jobs, so block
        job.update(oext=oext, padded_tokens_per_step=padded_tokens_per_step)   # 0's plan.json keeps 3481d85's bytes
    return job


def arm_count(jobs: list[dict]) -> int:
    return sum(int(j.get("counted", 0)) for j in jobs)


def requirements(jobs: list[dict], s: float = 1.0, preflight: dict | None = None) -> list[float]:
    """Each job's start requirement on a pod at speed factor s (the plan uses s = 1)."""
    out = []
    for job in jobs:
        if job["unmeasured"]:
            out.append(job["start_requirement_s"])     # an E kind: its explicit cap window, no speed scaling
        else:
            out.append(requirement_s(job["family"], job["steps"], job["kind"], s, 1.0, preflight,
                                     job.get("padded_tokens_per_step"), job.get("oext", False) is True))
    return out


def cap_hours(jobs: list[dict]) -> float:
    """KCR §4: the largest, over the jobs k, of POD_OVERHEAD_S + the measured uppers of the jobs before k + job k's
    requirement at s = 1, rounded up to 0.25 h. More than MAX_ARMS_PER_POD_78B counted jobs refuse; an E kind
    runs alone."""
    if not jobs:
        raise Refused("a host without jobs has no cap")
    if arm_count(jobs) > MAX_ARMS_PER_POD_78B:
        raise Refused(f"{arm_count(jobs)} counted jobs on one pod; at most {MAX_ARMS_PER_POD_78B} (KD2)")
    if any(j["unmeasured"] for j in jobs) and len(jobs) > 1:
        raise Refused("an unmeasured kind runs alone on its pod (KD6)")
    if len({j["family"] for j in jobs}) != 1:
        raise Refused("one family per pod")
    need = requirements(jobs)
    worst = max(POD_OVERHEAD_S + sum(j["measured_upper_s"] for j in jobs[:k]) + need[k] for k in range(len(jobs)))
    return hours(round_up_s(worst))


def pod_spend_usd(jobs: list[dict]) -> float:
    """One pod's upper spend: (48 min + its jobs' spend uppers) x $1.79."""
    return hours(POD_OVERHEAD_S + sum(j["spend_upper_s"] for j in jobs)) * RATE_USD


def arm_pod(family: str, steps_list: list[int], kinds: list[str] | None = None, oext: bool = False) -> list[dict]:
    """The job records of one pod of arms (each at its step count; kinds default to ``arm``); ``oext`` plans each with
    its in-job O-ext step (blocks A and B; R1 K1)."""
    kinds = kinds or ["arm"] * len(steps_list)
    return [job_record(family, k, s, oext=oext) for k, s in zip(kinds, steps_list)]


def launch_allowed(free_after_commitments_usd: float, cap_h: float, price: float = PLANNING_PRICE_USD) -> bool:
    """The guard (KCR §4, test 10 with KD4's zero hold): free balance after every running commitment, minus the new
    pod at its cap x the planning price, must leave the reserve plus the hold. Decided in cents. A balance, cap or
    price that is not a finite number raises Refused (A-V4), never a decimal or type error."""
    free = Decimal(repr(cents(finite(free_after_commitments_usd))))
    need = Decimal(repr(cents(finite(cap_h) * finite(price))))
    floor = Decimal(repr(cents(RESERVE_USD + GATE_B_HOLD_USD)))
    return free - need >= floor


def price_allowed(price) -> bool:
    """The create-time limit: a finite price at or below $10/h."""
    try:
        return finite(price) <= MAX_PRICE_USD
    except Refused:
        return False


def free_space_ok(free_gb) -> bool:
    """KD5: a job starts only with FREE_SPACE_MIN_GB free on the volume; a missing or non-finite reading is not ok."""
    try:
        return finite(free_gb) >= FREE_SPACE_MIN_GB
    except Refused:
        return False


# ===== KD6: the E caps of the unmeasured kinds =====
def evalonly_upper_s(family: str) -> float:
    return upper_m_s(family, None, "evalonly")


def e_upper_s(family: str, kind: str, n_points: int = 1) -> dict:
    """The E upper of an unmeasured kind on its single-job pod, with its basis (KD6). The measured parts (training
    steps, all-capped batches) use the family's M constants; the kind's own unmeasured work is an E, and the stage-1
    kit's wide-cap factor 1.5 applies to the E parts. a1_pass is pinned by KD6's 16.5 h cap (PP8); rep_pass takes the
    stage-1 kit's 1 h estimate x the scorer-kind factor (PP8)."""
    f = family_of(family)
    if kind not in E_KINDS:
        raise Refused(f"{kind!r} is not an E-capped kind")
    if type(n_points) is not int or n_points < 1:
        raise Refused("at least one evaluation point")
    train38 = FIXTURE_STEPS * f["TRAIN_STEP_MAX_S"] + f["EARLY_MAX_S"] + f["OUTSIDE_MAX_S"]
    batch, first = f["BATCH_MAX_S"], max(f["FIRST_BATCH_MAX_S"], f["BATCH_MAX_S"])
    ends = f["EARLY_MAX_S"] + f["OUTSIDE_MAX_S"]
    size = SIZE_FACTOR_1B_TO_78B
    regen = WIDE_CAP_FACTOR * (train38 + 3 * STATE_WRITE_S)            # a train-only a0 regeneration (no kind; PP17)
    o_pass = WIDE_CAP_FACTOR * (first + (-(-O_EXT_PROMPTS // GENERATION_BATCH) - 1) * batch + 0.5 * SCORE_ALLCAP_S + ends)
    if kind == "untuned_answers":                                       # PP2: both calls under one cap
        s3_chunks = -(-S3_POOL_ITEMS // GENERATION_BATCH)
        s3_call = first + (s3_chunks - 1) * batch + ends
        s4_call = first + (S_POOL_CHUNKS - 1) * batch + ends
        upper = WIDE_CAP_FACTOR * (s3_call + s4_call)
        basis = ("E: two calls on one pod (PP2), one E cap for both (K4b). The S3 call answers the s3_safe pool's 861 "
                 "prompts in 27 chunks of 32 at max_new_tokens 512 (the settings' lists.s3) with the s1 and s3_safe loss "
                 "forwards; the S4 call answers at most 512 prompts in 16 chunks of 32 (PR4 S4 row; ruling 12's stop rule "
                 "at the chunk holding the 192nd kept row). Every chunk of both calls at the family's capped-batch "
                 "maximum measured at 2,048 tokens (M; an upper bound for the S3 call's 512-token chunks), each call's "
                 "first at the first-batch maximum, plus each call's early and outside time (M); x 1.5 (the stage-1 "
                 "wide-cap factor) for the LEX and encode_train checks, the loss forwards and the record writes. Source: "
                 "KCR §3-§4; stage1_rules.py J6; scripts/scale78b/SCORERS-78B.md section 2.")
    elif kind == "o_only":
        upper = o_pass
        basis = ("E: the O-ext pass at one state: 600 prompts (the 500-prompt bank plus the dev 100, stage1_rules.py "
                 "O_ONLY_FACTOR) in 19 batches, every batch capped (M), the guard on 600 answers at half the scoring "
                 "allowance (E), the early and outside time (M); x 1.5. Source: KCR §4; stage1_rules.py J3.")
    elif kind == "o_only_with_regenerate":
        upper = regen + o_pass
        basis = ("E: PP17's one job on one pod (KD6): the train-only regeneration of a reused a0 side unit (38 x "
                 "TRAIN_STEP_MAX + the early and outside time (M) plus three state writes of about 1.9 GB (E, 300 s "
                 "each), x 1.5; the engine's verify and the acceptance check against the side unit's fingerprints read "
                 "the unit's records only and sit inside that 1.5), then the O-ext pass on its e1 state (the o_only "
                 "upper). Source: KCR §4, §6; the stage-1 kit's J2 and J3 (REGEN_MEASURED_S is a 1B value).")
    elif kind == "anchor":
        upper = WIDE_CAP_FACTOR * size * STAGE1_1B_ESTIMATES_S["anchor"]
        basis = ("E: the anchor answers at 1B had a 0.25 h upper (stage1_rules.py ANCHOR_UPPER_S); x 2.3 for the 7-8B "
                 "job-time ratio (RP:43) x 1.5. The anchor bank's size is not read here.")
    elif kind == "a1_pass":
        upper = A1_PASS_CAP_H_MAX * 3600 - POD_OVERHEAD_S - START_MARGIN_S
        basis = ("E: A1's attributes pass (PP3: the engine's attributes job on the a0-1101 retrain's q and e1 states) at "
                 "RP:43's 6-11 h; KD6 caps its pod at 16.5 h at most, so the job's window is 16.5 h - 48 min - 30 min = "
                 "15.2 h (1.38 x the 11 h upper). Source: KCR:128; ruling 11 KD6; PP8.")
    elif kind == "rep_pass":
        upper = WIDE_CAP_FACTOR * size * STAGE1_1B_ESTIMATES_S["rep_pass"]
        basis = ("E: REQ-3's representation pass (PP3): the stage-1 kit's 1 h estimate at 1B (stage1_rules.py "
                 "DIAG_ESTIMATE_S, 3,600 s; I there) x 2.3 (the scorer-kind size factor, RP:43) x 1.5, until measured. "
                 "Source: PP8; ruling 11 KD6.")
    elif kind == "l1_scan":
        upper = WIDE_CAP_FACTOR * size * STAGE1_1B_ESTIMATES_S["l1_scan"]
        basis = "E: the 1B estimate 3,600 s (stage1_rules.py J7, I there) x 2.3 (RP:43) x 1.5."
    elif kind == "classifier":
        upper = WIDE_CAP_FACTOR * size * STAGE1_1B_ESTIMATES_S["classifier"]
        basis = "E: the 1B estimate 2,012 s (stage1_rules.py J8) x 2.3 (RP:43) x 1.5."
    elif kind == "c0":
        upper = max(evalonly_upper_s(family) + WIDE_CAP_FACTOR * 600.0,
                    WIDE_CAP_FACTOR * size * STAGE1_1B_ESTIMATES_S["c0"])
        basis = ("E: c0 evaluates an engine-X unit: the evalonly bound (M: all 34 batches capped, the scoring allowance) "
                 "plus 1.5 x 600 s for B17's X-pin check and hashing (E); never below the 1B estimate 2,400 s x 2.3 x "
                 "1.5. Source: stage1_rules.py C0_S, X_ONLY_KINDS.")
    elif kind == "retrain":
        upper = 3.0 * 3600
        basis = ("E: the a0-1101 retrain on engine Y (ruling 10), train only to q and e1: expected under 0.5 h (38 x "
                 "TRAIN_STEP_MAX <= 922 s (M) plus loads and two state writes); the first job on engine Y at 7-8B is "
                 "unmeasured, and a stop mid-retrain loses the X -> Y certificate, so the upper is 3 h (about 6 x the "
                 "expected); the pod's cap is then 4.5 h, inside the check's M3 figure (4-5 h). Re-measured by KD9.")
    elif kind == "ref_train_bqi":
        upper = (FIXTURE_STEPS * f["TRAIN_STEP_MAX_S"] * (1 + REF_FORWARD_SHARE) * Y_ENGINE_FACTOR
                 + gen_allcap_s(family) + SCORE_ALLCAP_S + ends + oext_term_s(family))
        basis = ("E: B+Qi (constrained SFT, engine Y): the a0 training term x (1 + 0.5) for the reference forward "
                 "(stage1_rules.py REF_FORWARD_SHARE, I) x 2 because engine Y is unmeasured at 7-8B, plus the evalonly "
                 "bound (M), plus its in-job O-ext pass on Y (oext_term_s: x 1.5 until measured; DESO item 24 (b), "
                 "(c); GXB O12). Source: KCR:128 (B+Qi refused until measured); ruling 10.")
    elif kind == "safe_lora":
        upper = (WIDE_CAP_FACTOR * (train38 + 3 * STATE_WRITE_S + size * STAGE1_1B_ESTIMATES_S["safe_lora_hash"]
                                    + size * STAGE1_1B_ESTIMATES_S["safe_lora_transform"])
                 + n_points * (evalonly_upper_s(family) + oext_term_s(family)))
        basis = ("E: Safe LoRA: a regenerate's training (M) and states (E), the hash of about 15-16 GB of weights and "
                 "the V/V' check (the 1B 600 s x 2.3), the CPU transform (the 1B 88 s x 2.3), all x 1.5; plus one "
                 "evalonly bound (M) and one O-ext pass (oext_term_s: x 1.5 until measured; DESO item 24 (b); GXB O12) "
                 "per evaluation point. Source: stage1_rules.py J17.")
    elif kind == "ref_eval":
        upper = (WIDE_CAP_FACTOR * (train38 + 3 * STATE_WRITE_S + 300.0)
                 + n_points * (evalonly_upper_s(family) + oext_term_s(family)))
        basis = ("E: the evaluation-only references (adapter scaling, the safety prompt): a regenerate's training (M) "
                 "and states (E) when the state is not on the pod, 300 s of adapter scaling (E), x 1.5; plus one "
                 "evalonly bound (M) and one O-ext pass (oext_term_s: x 1.5 until measured; DESO item 24 (b); GXB O12) "
                 "per point. Source: stage1_rules.py J16, REF_EVAL_SCALES.")
    elif kind == "b10_certify":                # R3 K3 (GXB O2, X2): one certify evaluation of seed S's regenerated a0
        upper = (WIDE_CAP_FACTOR * (train38 + 3 * STATE_WRITE_S)
                 + evalonly_upper_s(family) + oext_term_s(family))
        basis = ("E: B10's certification of one reference seed (GXB O2): a regenerate's training (M) and states (E), x "
                 "1.5; plus one evalonly bound (M) and one O-ext pass (certify records O-ext as a report; oext_term_s: x "
                 "1.5 until measured). Source: the stage-1 kit's b10_certify; ref_eval's bound at one point.")
    elif kind == "w1_18":
        upper = WIDE_CAP_FACTOR * STAGE1_1B_ESTIMATES_S["w1_18"]
        basis = ("E: the 7-8B W1-18 check (DES E2; DESO2 item 37): guard-only, the same guard model as at 1B "
                 "(Qwen3Guard-Gen-4B), on the seven reused side units' stored dev-100 answers and their 128-token cuts "
                 "(about 1,400 judged items; 1B: 11 units), one policy codec per family; the 1B upper 0.5 h "
                 "(stage1_rules.py:84 W1_18_UPPER_S, E there) x 1.5; cap 2.25 h, inside Part 2 §4.2's 2-3 h E. No size "
                 "factor: the guard, not the policy, does the work (I).")
    else:                                   # pragma: no cover - E_KINDS is closed above
        raise Refused(kind)
    return {"kind": kind, "family": family, "upper_s": upper, "n_points": n_points, "basis": basis}


def e_cap_hours(family: str, kind: str, n_points: int = 1) -> float:
    """The single-job pod's cap for an unmeasured kind: 48 min + its E upper + the start margin, rounded up."""
    return hours(round_up_s(POD_OVERHEAD_S + e_upper_s(family, kind, n_points)["upper_s"] + START_MARGIN_S))


def e_pod(family: str, kind: str, n_points: int = 1) -> dict:
    """One single-job E pod: its cap, guard and spend upper (its spend upper is its E upper, nothing measured)."""
    job = job_record(family, kind, n_points=n_points)
    cap = e_cap_hours(family, kind, n_points)
    return {"family": family, "kind": kind, "cap_hours": cap, "guard_usd": cents(guard_usd(cap)),
            "spend_usd": cents(pod_spend_usd([job])), "upper_s": job["upper_s"], "e_cap": True}


# ===== the job runner's gate (test 12; called by T4's runner before each job) =====
def preflight_fields(preflight_done: dict, verification: dict) -> dict:
    """The three speed fields the rule reads, from the preflight's two documents: training_s and ms_per_step_full
    from PREFLIGHT-DONE.json; untuned_projected_s from verification.json's ``cap_projection`` block, where the
    preflight script writes it (M: none of the 17 measured PREFLIGHT-DONE.json files holds it, so there is no
    fallback to a field of that name there). A missing document, block or field refuses, and the two documents must
    describe one preflight: cap_projection.training_s equals PREFLIGHT-DONE's training_s."""
    if not isinstance(preflight_done, dict):
        raise Refused("no PREFLIGHT-DONE record")
    if not isinstance(verification, dict):
        raise Refused("no verification record (the preflight's verification.json)")
    cap_projection = verification.get("cap_projection")
    if not isinstance(cap_projection, dict):
        raise Refused("the verification record has no cap_projection block")
    out = {"training_s": finite(preflight_done.get("training_s")),
           "ms_per_step_full": finite(preflight_done.get("ms_per_step_full")),
           "untuned_projected_s": finite(cap_projection.get("untuned_projected_s"))}
    if not math.isclose(finite(cap_projection.get("training_s")), out["training_s"], rel_tol=1e-9, abs_tol=1e-6):
        raise Refused("PREFLIGHT-DONE.json and verification.json cap_projection disagree on training_s: not one preflight")
    return out


def job_decision(family: str, preflight_done: dict, verification: dict, job: dict, remaining_s: float | None, free_gb,
                 s_obs: float = 1.0) -> dict:
    """What the runner does with the next job: ``run`` or ``defer``, with the requirement it computed. Takes the
    preflight's two documents (PREFLIGHT-DONE.json and verification.json; preflight_fields). Refuses (raises) on a
    missing document or field, a pod past SPEED_REFUSAL, a volume below FREE_SPACE_MIN_GB (KD5), or a kind that needs
    recipe S_78 while RECIPE_S[family] is None (addendum A1)."""
    fields = preflight_fields(preflight_done, verification)
    s_pod = speed_factor(family, fields)
    if not free_space_ok(free_gb):
        raise Refused(f"{free_gb!r} GB free on the volume, below {FREE_SPACE_MIN_GB} GB or unreadable: no job starts (KD5)")
    stop = anchor_stop_problem_for(family, job["kind"])
    if stop:
        raise Refused(stop)                            # R1 K1 (GXB O6): the S_78 kinds refuse for good after a stop
    if job["kind"] in S78_KINDS and not (job["kind"] == "retrain" and family_stopped(family)):
        recipe_s_or_refuse(family)
    if job["kind"] in BQI_KINDS:
        recipe_bqi_or_refuse(family)                   # D1: B+Qi refuses until its config is pinned (KCR:128)
        oext_y_or_refuse(family)                       # R1 K1: and its O-ext pass on Y until OEXT_78B_Y is filled
    if job["kind"] in G_KINDS:
        pin_or_refuse("RECIPE_G", family)              # R1 K1: ref_train refuses until RECIPE_G is filled
    if job["unmeasured"]:
        need = job["start_requirement_s"]
    else:
        need = requirement_s(family, job["steps"], job["kind"], s_pod, s_obs, fields,
                             job.get("padded_tokens_per_step"), job.get("oext", False) is True)
    reason = None
    if s_obs_defers(s_obs):
        action, reason = "defer", "s_obs"
    elif gate(remaining_s, need):
        action = "run"
    else:
        action, reason = "defer", "remaining"
    return {"action": action, "reason": reason, "requirement_s": need, "s_pod": s_pod, "s_obs": float(s_obs),
            "s": max(1.0, s_pod, float(s_obs)), "remaining_s": remaining_s}


def pod_dry_run(family: str, preflight_done: dict, verification: dict, jobs: list[dict], remaining_s: float, free_gb,
                s_obs: float = 1.0) -> list[dict]:
    """A dry run of a pod: each job in order, the remaining time falling by each run job's measured upper; the first
    deferred job defers every later one (the Gate B rule). Takes the preflight's two documents like job_decision."""
    out, left, deferred = [], remaining_s, False
    for k, job in enumerate(jobs):
        d = job_decision(family, preflight_done, verification, job, left, free_gb, s_obs)
        if deferred:
            d.update(action="defer", reason=d["reason"] or "earlier job deferred")
        out.append({"index": k, **d})
        if d["action"] == "run":
            left = left - job["measured_upper_s"]
        else:
            deferred = True
    return out


# ===== block 0 (N) and the first days after the money (the check's M3) =====
def n_pods() -> list[dict]:
    """N's layout (ruling 11): OLMo one pod, 3 arms (R_1-R_3 at 33 steps; cap 8.5 h); Llama one pod, 4 jobs (R_1-R_3
    at 33 steps and a0 1103 at 38; cap 12.5 h); in parallel, one launch."""
    olmo = arm_pod("olmo2-7b", [33, 33, 33])
    llama = arm_pod("llama31-8b", [33, 33, 33, 38], ["arm", "arm", "arm", "a0_arm"])
    return [{"family": "olmo2-7b", "host": "olmo2-7b-0-1", "jobs": olmo, "cap_hours": cap_hours(olmo),
             "spend_usd": cents(pod_spend_usd(olmo))},
            {"family": "llama31-8b", "host": "llama31-8b-0-1", "jobs": llama, "cap_hours": cap_hours(llama),
             "spend_usd": cents(pod_spend_usd(llama))}]


# The pre-block-A scorer kinds (ruling 11 KD10; PP3, PP8: rep_pass is REQ-3's representation pass, a1_pass A1's).
SCORER_KINDS = ("untuned_answers", "o_only", "o_only_with_regenerate", "anchor", "rep_pass", "a1_pass", "l1_scan",
                "classifier", "c0")             # PP17: o_only_with_regenerate replaces KD10's "o_only / regenerate" pair
# PP14: the ONE definition of the pre-block-A pods that keep training states after their job (each a stopped 50 GB
# volume until the state rule's pull and verified backup, KD5), read by block 0's printout (idle_storage_pods) and by
# the scorer block's (sc_pod) alike (the core verifier's D4). The retrain writes the a0-1101 retrain's q and e1 states
# that A1's pass reads (PP3); a1_pass holds those states as its input; o_only_with_regenerate writes the regenerated a0
# unit's states (PP17); c0 writes its R_1 training unit's states (R: scripts/stage1_s1/lean_eval_job.py:147, OUT/train
# is an ordinary engine unit; the light pull leaves model states on the volume, plan_tool record-done). The other kinds
# read answers, units or the anchor file and write no training state.
IDLE_RETRAIN_WHY = "keeps the a0-1101 retrain's q and e1 states for A1's pass (PP3)"
SC_STATE_KINDS = {"retrain": IDLE_RETRAIN_WHY,
                  "a1_pass": "holds the retrain's q and e1 states that A1's pass reads (PP3, PP16)",
                  "o_only_with_regenerate": "keeps the regenerated a0 unit's states (PP17; a train-only job like the "
                                            "retrain)",
                  "c0": "keeps its R_1 training unit's states (lean_eval_job.py's OUT/train; the light pull leaves them)"}
IDLE_SCORER_KINDS = {k: why for k, why in SC_STATE_KINDS.items() if k != "retrain"}   # the scorer kinds among them


def idle_storage_pods(n_hosts: list[str]) -> list[dict]:
    """PP14: one entry per pod of block 0 that keeps states after its jobs: N's pods (by host), and per family every
    pod of SC_STATE_KINDS the scorer block plans (sc_seeds: one retrain pod, one a1_pass pod, one c0 pod, one
    o_only_with_regenerate pod per reused a0 seed); each at idle_storage(1)'s rate (about $0.33 per day)."""
    one = idle_storage(1)
    pods = [{"pod": f"N {host}", "why": "keeps its arms' e1 states until the state rule's pull and verified backup (KD5)"}
            for host in n_hosts]
    for family in FAMILIES:
        for kind, why in SC_STATE_KINDS.items():
            for seed in sc_seeds(family, kind):
                label = "retrain" if kind == "retrain" else "scorer"
                pods.append({"pod": f"{label} {family}" + ("" if kind == "retrain" else f" {kind}")
                             + (f" {seed}" if kind in SC_PER_SEED_KINDS else ""), "why": why})
    return [{**p, "usd_per_day": one["usd_per_pod_day"], "usd_per_month": one["usd_per_month"]} for p in pods]


def idle_storage_lines(report: dict) -> list[str]:
    """The need printout's idle-storage lines (KD5, PP14): N's line (both N pods, D2), one line per other pod of
    block 0 that keeps states (each retrain pod, each scorer pod of IDLE_SCORER_KINDS), and the block's total if every
    such pod is kept stopped. Each is an E counted in no guard (the guard reads running pods only)."""
    idle, pods, total = report["idle_storage"], report["idle_storage_pods"], report["idle_storage_all"]
    lines = [f"idle storage (KD5; E, KCR:161): about ${idle['usd_per_pod_day']:.2f} per day per stopped "
             f"{idle['volume_gb']} GB pod that keeps its states (${idle['usd_per_gb_month']:.2f} per GB per month); "
             f"N's {idle['n_pods_kept']} pods kept stopped: ${idle['usd_per_day']:.2f} per day, about "
             f"${idle['usd_per_month']:.2f} per month; counted in no guard"]
    for p in pods:
        if p["pod"].startswith("N "):
            continue
        lines.append(f"idle storage {p['pod']} (KD5, PP14; E, KCR:161): {p['why']}; about ${p['usd_per_day']:.2f} per "
                     f"day, about ${p['usd_per_month']:.2f} per month while kept stopped; counted in no guard")
    lines.append(f"idle storage block 0 in all (KD5, PP14; E): {total['n_pods_kept']} pods if every pod above is kept "
                 f"stopped: ${total['usd_per_day']:.2f} per day, about ${total['usd_per_month']:.2f} per month; "
                 "counted in no guard")
    return lines


def block0_report() -> dict:
    """The money of block 0 and the first days after it, each part separately (the check's M3): N's two pods in one
    launch (KCR:177: guard $44.85, spend upper $33.30, need $56.06 with the contingency), each family's retrain pod
    (ruling 10, engine Y) and each scorer pod (C1; KD6 caps), every pod alone with its guard, spend upper and need;
    KD5's idle storage of N's pods kept stopped for their states (D2); PP14: ``idle_storage_pods``, one entry per
    block-0 pod that keeps states (N's, the retrain pods, the scorer pods of IDLE_SCORER_KINDS), and
    ``idle_storage_all``, their total."""
    pods = n_pods()
    launch = [{"cap_hours": p["cap_hours"], "spend_usd": p["spend_usd"]} for p in pods]
    n_need = funding_need_usd([launch], CONTINGENCY_FACTOR)
    out = {"n": {"pods": [{k: v for k, v in p.items() if k != "jobs"} for p in pods],
                 "guard_usd": cents(RESERVE_USD + GATE_B_HOLD_USD
                                    + PLANNING_PRICE_USD * sum(p["cap_hours"] for p in pods)),
                 "spend_upper_usd": cents(sum(p["spend_usd"] for p in pods)),
                 "need_usd": n_need["need_usd"], "base_need_usd": n_need["base_need_usd"]},
           "idle_storage": idle_storage(len(pods)), "retrain_pods": {}, "scorer_pods": {}}
    kept = idle_storage_pods([p["host"] for p in pods])                # PP14: every block-0 pod that keeps states
    out["idle_storage_pods"] = kept
    out["idle_storage_all"] = idle_storage(len(kept))
    for family in FAMILIES:
        pod = e_pod(family, "retrain")
        pod["need_usd_alone"] = funding_need_usd([[pod]], CONTINGENCY_FACTOR)["need_usd"]
        out["retrain_pods"][family] = pod
        out["scorer_pods"][family] = {}
        for kind in SCORER_KINDS:
            pod = e_pod(family, kind)
            pod["need_usd_alone"] = funding_need_usd([[pod]], CONTINGENCY_FACTOR)["need_usd"]
            out["scorer_pods"][family][kind] = pod
    return out


# ===== K4b: the pre-block-A scorer block "sc" (ruling 11 KD6, KD10; the check's C1, M1; A1, A2, A8, A13; PP1-PP16) =====
# One working copy per family: tmp/family-probe-s78-<family>-sc/ (KD7). Every pod holds ONE job of one of SC_KINDS with
# its explicit E cap (KD6; e_pod). A kind is planned (and run) only when every pin it needs is filled (A13's pattern)
# and the kinds that must come before it (A2: the anchor job, then S_78, then the retrain; then A1's pass on the
# retrain's states) are recorded complete in the copy's plan. The pins live in two places, each filled by a recorded
# lead step: this module (RECIPE_S, ENGINE_Y, OEXT_78B, C0_SOURCE) and the scorer layer's settings/pins_78b.json
# (the anchor bank, the untuned pass's s3_orig pool, the retrain's COMPLETE.json; read by the kit through its pins,
# stage1_rules.SCORER_PINS). sc_pin_values reads both; a pin set in both places must agree.
SC_BLOCK = "sc"
SC_KINDS = ("anchor", "untuned_answers", "o_only", "o_only_with_regenerate", "c0", "l1_scan", "rep_pass", "classifier",
            "retrain", "a1_pass", "w1_18")       # R1 K1: the 7-8B W1-18 check, the scorer block's first O job
# M1 (O and L at 7-8B; PP17): the O-ext unit pass of the S1 package pins the 1B recipes and manifest in its settings (R:
# scripts/stage1_s1/settings/oext_unit.json recipes.allowed, prepared.manifest_sha256), so at 7-8B it needs settings
# re-derived per family; Part 2 names the evaluation bank (M1). Null until the lead fills it by a recorded step with
# exactly this form (sc_pin_values validates it; the core verifier's D6):
#   {"files": {path: SHA-256, ...}, "inputs": {"oext_bank": SHA-256, "oext_record": SHA-256}}
# "files": every S1-package file the o_only, o_only_with_regenerate and c0 commands run or read on the pod, each a
# plain relative path under scripts/ (OEXT_UNIT_SCRIPT and C0_SCRIPT among them; plan_tool refuses a kind whose script
# is not listed), packed and sealed by those pins; "inputs": the O-ext bank file's and its record's SHA-256 (the named
# inputs oext_bank and oext_record). o_only, o_only_with_regenerate and c0 refuse until then.
OEXT_78B: dict[str, dict | None] = {"olmo2-7b": None, "llama31-8b": None}
# R1 K1 (GXB T-O3; DESO2 item 24 (c); Part 2 §3.2, §4.4): the Y variant of OEXT_78B's files per family (the 1B
# oext_unit_y.json form), in OEXT_78B's form, for B+Qi's in-job O-ext pass on engine Y (also when B+Qi is unpaired).
# Null until a recorded lead step fills it once ENGINE_Y and the family's RECIPE_BQI are filled; B+Qi refuses until then.
OEXT_78B_Y: dict[str, dict | None] = {"olmo2-7b": None, "llama31-8b": None}
OEXT_INPUTS = ("oext_bank", "oext_record")
# R1 K1 (GXB B-3): the 7-8B O-ext route is ONE wrapper, Track O's scripts/scale78b/oext_78b.py, with three commands
# (unit: the O-ext unit pass; lean: c0's lean job; w1_18: the W1-18 check) over the unchanged 1B scripts
# (scripts/stage1_s1/oext_unit.py, lean_eval_job.py, oext_eval.py, scripts/stage1/limits/overrefusal_checks.py). The
# path may be a stub until Track O's file is merged; OEXT_78B[family]["files"] must list it (plan_tool refuses a kind
# whose script is not listed). The runner's command words for it are K3's (it still writes the 1B "run" form).
OEXT_WRAPPER_78B = "scripts/scale78b/oext_78b.py"
OEXT_UNIT_SCRIPT = OEXT_WRAPPER_78B                      # its "unit" command (the stage-1 kit's J3 form)
C0_SCRIPT = OEXT_WRAPPER_78B                             # its "lean" command (B17's lean job; the stage-1 kit's J11)
W1_18_SCRIPT = OEXT_WRAPPER_78B                          # its "w1_18" command (DES E2; GXB O3, O4)
OEXT_WRAPPER_COMMANDS = {"o_only": "unit", "o_only_with_regenerate": "unit", "c0": "lean", "w1_18": "w1_18"}
# c0 (B17's X-pin check on an engine-X unit) re-trains N's R_1 at 1101 and expects that unit's e1 adapter fingerprint:
# {"complete_sha256", "e1_fingerprint"} of block 0's R_1-1101 unit, filled by a recorded lead step after block 0's
# record-done (the unit lives in another working copy, KD7). Null until then; c0 refuses.
C0_SOURCE: dict[str, dict | None] = {"olmo2-7b": None, "llama31-8b": None}
C0_SEED = 1101
RETRAIN_SEED = 1101                                       # ruling 10: the a0-1101 retrain
SC_PIN_EVENTS = {
    "RECIPE_S": "the family's anchor job, then scripts/scale78b/make_recipe_s78.py, the lead's commit of the S_78 config "
                "and RECIPE_S[family] filled, the same value as pins_78b.json recipe_s78 (addendum A1, A2)",
    "ANCHOR_BANK": "the family's anchor job: its anchors.sealed.json anchor_file_sha256 in pins_78b.json "
                   "families.<family>.anchor_bank_sha256 (addendum A1; the scorer layer's pin)",
    "S3_ORIG_POOL": "the family's untuned-answers pass: its s3_orig.pool.json SHA-256 in pins_78b.json "
                    "families.<family>.untuned_pass.s3_orig_pool_sha256",
    "RETRAIN_UNIT": "the family's a0-1101 retrain: its COMPLETE.json SHA-256 in pins_78b.json "
                    "families.<family>.a1_attributes_unit.retrain_complete_sha256 (PP3)",
    "OEXT_78B": "Part 2 names the 7-8B evaluation bank (the check's M1) and the lead re-derives the O-ext unit pass's "
                "settings for the family: OEXT_78B[family] filled by a recorded step as {files: {path: SHA-256}, "
                "inputs: {oext_bank: SHA-256, oext_record: SHA-256}} (PP17)",
    "C0_SOURCE": "block 0 (N): R_1 at 1101's COMPLETE.json SHA-256 and e1 adapter fingerprint, C0_SOURCE[family] "
                 "filled by a recorded lead step after block 0's record-done",
    "ENGINE_Y": "addendum A13: the lead fills ENGINE_Y by a recorded step when the Y retrain is packed; on a family "
                "whose anchor job stopped, when that family's main-config (MAIN_F) retrain is prepared (AM1 changes 2, "
                "5, 13; DESO3 V1)",
    "BRANCH_78B": "the W1-18 pod's record-done (or the 'Branch full by default' record): K2's branch-record step and a "
                  "recorded lead step fill BRANCH_78B[family] with the family's branch record's path and SHA-256 "
                  "(K1V-5; GXB K-8)",
    "OEXT_78B_Y": "ENGINE_Y and the family's RECIPE_BQI filled, then the lead re-derives the O-ext settings for engine Y "
                  "(the 1B oext_unit_y.json form) and fills OEXT_78B_Y[family] by a recorded step in OEXT_78B's form "
                  "(DESO2 item 24 (c); GXB T-O3)",
    "N_UNITS": "block 0 (N): each N unit's folder, COMPLETE.json and job.json SHA-256 (and an R unit's sealed R_d "
               "edit SHA-256), N_UNITS[family] filled by a recorded lead step after block 0's record-done (Part 2 "
               "§4.5; DES E5)",
    "W1_18_78B": "Track O's W1-18 route (scripts/scale78b/oext_78b.py w1_18) and the per-family W1-18 settings made by "
                 "a recorded step (GXB O3), W1_18_78B filled by a recorded lead step in the maker's printed form {files: "
                 "{path: SHA-256}, side_units: {family: {unit: {path, complete_sha256, job_sha256}}}} (GXB R-20, R-32)",
}
# What each kind needs filled (A13's pattern). The retrain on engine Y also needs ENGINE_Y (sc_needed_pins).
SC_KIND_PINS = {
    "anchor": (), "untuned_answers": (),
    "o_only": ("OEXT_78B",), "o_only_with_regenerate": ("OEXT_78B",), "c0": ("OEXT_78B", "C0_SOURCE"),
    "l1_scan": ("ANCHOR_BANK",), "classifier": ("RECIPE_S", "ANCHOR_BANK"),
    "rep_pass": ("RECIPE_S", "ANCHOR_BANK", "S3_ORIG_POOL"), "retrain": ("RECIPE_S",),
    "a1_pass": ("RECIPE_S", "ANCHOR_BANK", "RETRAIN_UNIT"),
    "w1_18": ("W1_18_78B",),
}
# A2's order, enforced at planning: the kinds that must be recorded complete in this copy's plan first. The anchor job
# makes the anchor file (S_78's query bank, A1) before S_78, the retrain and every kind that reads the anchor bank;
# rep_pass's second pass reads the untuned pass's s3_orig pool; A1's pass reads the retrain's q and e1 states.
SC_AFTER = {"l1_scan": ("anchor",), "classifier": ("anchor",), "rep_pass": ("anchor", "untuned_answers"),
            "retrain": ("anchor",), "a1_pass": ("anchor", "retrain")}
SC_RECIPE = {k: "S" if k in S78_KINDS else "B" for k in SC_KINDS}   # PP1: untuned_answers and the anchor job run MAIN
# The arm and seed a job of each kind carries (the plan's job keys): o_only is the family's untuned model (theta0,
# the O-ext pass's --untuned route; M1), o_only_with_regenerate one of the family's reused a0 side units (ruling 7,
# PP17), c0 N's R_1, the retrain and A1's pass the a0-1101 retrain (ruling 10). The other kinds carry neither.
SC_ARM = {"o_only": "theta0", "o_only_with_regenerate": "a0", "c0": "R", "retrain": "a0", "a1_pass": "a0"}
SC_PER_SEED_KINDS = frozenset({"o_only_with_regenerate"})   # one pod per reused a0 seed (KIT a0_units)
# PP14's state-keeping kinds: SC_STATE_KINDS above (one definition for both printouts).


SC_ARMS = {"o_only_with_regenerate": ("a0", "R")}   # R1 K1 (DES E5): its units are keyed by (arm, seed); SC_ARM's "a0"
#                                                    stays the default arm of a job that names none (the side units)


def sc_seeds(family: str, kind: str) -> list:
    """The seeds a scorer-block job of ``kind`` may carry: the family's reused a0 side units for
    o_only_with_regenerate (KIT a0_units, ruling 7: OLMo 1101-1103, Llama 1101-1102), 1101 for c0, the retrain and
    A1's pass (ruling 10), None for the other kinds."""
    if kind == "o_only_with_regenerate":
        return sorted(s for s in KIT[family]["a0_units"] if s != "untuned")
    if kind == "c0":
        return [C0_SEED]
    if kind in ("retrain", "a1_pass"):
        return [RETRAIN_SEED]
    return [None]


def engine_sha(engine: str) -> str:
    """A13: engine X's identity, or engine Y's once ENGINE_Y is filled; Refused otherwise."""
    if engine == "X":
        return ENGINE_X
    if engine == "Y":
        if ENGINE_Y is None or not isinstance(ENGINE_Y, str) or not CONFIG_SHA256.match(ENGINE_Y):
            raise Refused(f"engine Y's pin is null (ENGINE_Y): {SC_PIN_EVENTS['ENGINE_Y']}")
        return ENGINE_Y
    raise Refused(f"unknown engine {engine!r}")


def _pins78_family(pins78, family: str) -> dict:
    fams = pins78.get("families") if isinstance(pins78, dict) else None
    fam = fams.get(family) if isinstance(fams, dict) else None
    if not isinstance(fam, dict):
        raise Refused(f"pins_78b.json holds no {family} block")
    return fam


def _hex_or_none(value, what: str):
    if value is None:
        return None
    if not isinstance(value, str) or not CONFIG_SHA256.match(value):
        raise Refused(f"{what} is neither null nor a SHA-256")
    return value


# GXB R-22 (ninth set; R-19): Track O's index names: OEXT-78B__<F>.json for engine X, OEXT-78B-Y__<F>.json for Y.
OEXT_INDEX_RE = re.compile(r"^scripts/scale78b/settings/OEXT-78B(-Y)?__(olmo2-7b|llama31-8b)\.json$")
# GXB R-33 (KR2-4): any basename that starts with OEXT-78B, in any case and any folder, is an index candidate; an O-ext
# pin holds exactly one, at its canonical path, its own family's for its own engine; the W1-18 pod's own index
# (OEXT-78B-W1__<F>.json, R-20) belongs to W1_18_78B only, never to OEXT_78B or OEXT_78B_Y.
OEXT_INDEX_CANDIDATE_RE = re.compile(r"(^|/)oext-78b[^/]*$", re.IGNORECASE)
W1_18_INDEX_RE = re.compile(r"^scripts/scale78b/settings/OEXT-78B-W1__(olmo2-7b|llama31-8b)\.json$")
# GXB R-21: the family's W1-18 record is committed under this folder; an O-ext pin's files may name it there (that one
# entry only, a plain .json file directly in the folder); every other entry stays under scripts/.
W1_18_RECORD_DIR = ".ai/inputs/stage1-post-w1-20261023/78b/w1-18/"
# GXB R-53: the record's standard file name is Track O's maker's, overrefusal_checks__<F>.json (after the 1B
# record kind, "stage1 over-refusal checks"); R-33: exactly that name, directly in the folder (w1_18_plan's too).
W1_18_RECORD_NAME = "overrefusal_checks__{family}.json"
W1_18_RECORD_RE = re.compile(r"^\.ai/inputs/stage1-post-w1-20261023/78b/w1-18/overrefusal_checks__(olmo2-7b|llama31-8b)\.json$")


def oext_index_problem(oext: dict, family: str, engine: str) -> str | None:
    """GXB R-5 (sixth set): an O-ext pin names exactly one O-ext index file, its own family's for its own engine
    (OEXT_78B[F] engine X, OEXT_78B_Y[F] engine Y), by path and SHA-256 among its files, beside the wrapper's own pin;
    another family's or engine's index refuses. Track O's names (GXB R-22): scripts/scale78b/settings/OEXT-78B__<F>.json
    (engine X) and OEXT-78B-Y__<F>.json (engine Y)."""
    candidates = [p for p in oext["files"] if isinstance(p, str) and OEXT_INDEX_CANDIDATE_RE.search(p)]
    indexes = [p for p in candidates if OEXT_INDEX_RE.match(p)]
    if len(candidates) != 1 or len(indexes) != 1:
        return (f"its files name {len(candidates)} O-ext index file(s); exactly one, {family}'s for engine {engine} at "
                "its standard path (GXB R-5, R-33)")
    y, fam = OEXT_INDEX_RE.match(indexes[0]).groups()
    eng = "Y" if y else "X"
    if (fam, eng) != (family, engine):
        return f"its index {indexes[0]} is {fam}'s for engine {eng}, not {family}'s for engine {engine} (GXB R-5)"
    if OEXT_WRAPPER_78B not in oext["files"]:
        return f"its files do not pin the wrapper {OEXT_WRAPPER_78B} (GXB R-5)"
    return None


def oext_form_problem(oext, family: str | None = None, engine: str | None = None) -> str | None:
    """Why ``oext`` is not OEXT_78B's documented form, or None: exactly {"files", "inputs"}; files a non-empty
    {plain relative path under scripts/: SHA-256}; inputs exactly {oext_bank: SHA-256, oext_record: SHA-256}. Given
    the pin's family and engine, also GXB R-5's one index of that family and engine (oext_index_problem)."""
    if not isinstance(oext, dict) or set(oext) != {"files", "inputs"}:
        return "its keys are not exactly files and inputs"
    files, inputs = oext["files"], oext["inputs"]
    if not isinstance(files, dict) or not files:
        return "files is not a non-empty mapping"
    records = [p for p in files if isinstance(p, str) and p.startswith(W1_18_RECORD_DIR)]
    if len(records) > 1:
        return f"files name {len(records)} entries under {W1_18_RECORD_DIR}; at most the one W1-18 record (GXB R-21)"
    for path, digest in files.items():
        if path in records:
            if not W1_18_RECORD_RE.match(path):
                return (f"files names {path!r}, not the standard overrefusal_checks__<family>.json W1-18 record "
                        f"directly under {W1_18_RECORD_DIR} (GXB R-21, R-33, R-53)")
            if family is not None and W1_18_RECORD_RE.match(path).group(1) != family:
                return f"files names {path!r}, another family's W1-18 record (GXB R-33)"
        elif not (isinstance(path, str) and path.startswith("scripts/") and "\\" not in path
                and all(part not in ("", ".", "..") for part in path.split("/"))):
            return f"files names {path!r}, not a plain relative path under scripts/"
        if not (isinstance(digest, str) and CONFIG_SHA256.match(digest)):
            return f"files[{path!r}] is not a SHA-256"
    if not isinstance(inputs, dict) or set(inputs) != set(OEXT_INPUTS):
        return f"inputs does not hold exactly {list(OEXT_INPUTS)}"
    if not all(isinstance(v, str) and CONFIG_SHA256.match(v) for v in inputs.values()):
        return "an input is not a SHA-256"
    if family is not None:
        return oext_index_problem(oext, family, engine or "X")
    return None


def oext_w1_18_record_problem(oext: dict, family: str, branch_doc: dict) -> str | None:
    """GXB R-33 (KR2-4): the family's O-ext pin and its branch record agree on W1-18's record. A branch read from
    W1-18 (source "w1_18", Branch 128 or a failing record's Branch full) needs the pin's files to name exactly the
    family's standard record .ai/inputs/stage1-post-w1-20261023/78b/w1-18/overrefusal_checks__<F>.json at the branch
    record's w1_18_record_sha256 (the O-ext eval settings pin it; T-O3: it joins the job's files); "Branch full by
    default" (source "default") names none. None when they agree."""
    want = W1_18_RECORD_DIR + W1_18_RECORD_NAME.format(family=family)
    records = {p: d for p, d in oext["files"].items() if isinstance(p, str) and p.startswith(W1_18_RECORD_DIR)}
    if branch_doc.get("source") == "w1_18":
        if set(records) != {want}:
            return (f"{family}'s branch comes from its W1-18 record, so the O-ext pin's files name exactly {want} "
                    "(GXB R-21, R-33)")
        if records[want] != branch_doc.get("w1_18_record_sha256"):
            return (f"the O-ext pin's W1-18 record {str(records[want])[:12]}... is not the branch record's "
                    f"w1_18_record_sha256 {str(branch_doc.get('w1_18_record_sha256'))[:12]}... (GXB R-33)")
        return None
    if records:
        return f"{family}'s branch is 'Branch full by default' (no W1-18 record), so the O-ext pin names none (GXB R-33)"
    return None


def sc_pin_values(family: str, pins78: dict) -> dict:
    """Every pin the scorer block reads, by name (None while null): RECIPE_S (this module, which must equal
    pins_78b.json's recipe_s78.config_sha256 when either is set), ANCHOR_BANK, S3_ORIG_POOL, RETRAIN_UNIT (pins_78b.json,
    the document the caller read at its pin), OEXT_78B, C0_SOURCE and ENGINE_Y (this module). A value that is not a
    SHA-256 (or the documented record) refuses."""
    family_of(family)
    fam = _pins78_family(pins78, family)
    rs = fam.get("recipe_s78") if isinstance(fam.get("recipe_s78"), dict) else {}
    layer = _hex_or_none(rs.get("config_sha256"), f"pins_78b.json {family} recipe_s78.config_sha256")
    kit = _hex_or_none(RECIPE_S[family], f"RECIPE_S[{family!r}]")
    if layer != kit:
        raise Refused(f"recipe S_78 for {family}: rules_78b.RECIPE_S ({str(kit)[:12]}) and pins_78b.json recipe_s78 "
                      f"({str(layer)[:12]}) disagree; the lead fills both by one recorded step (A1)")
    if kit is not None and not (isinstance(rs.get("path"), str) and rs["path"].startswith(
            "experiments/safety_selection/configs/") and rs["path"].endswith(".json")):
        raise Refused(f"pins_78b.json {family} recipe_s78.path is not a committed config path")
    untuned = fam.get("untuned_pass") if isinstance(fam.get("untuned_pass"), dict) else {}
    a1 = fam.get("a1_attributes_unit") if isinstance(fam.get("a1_attributes_unit"), dict) else {}
    oext = OEXT_78B[family]
    if oext is not None and oext_form_problem(oext):
        raise Refused(f"OEXT_78B[{family!r}] is not a {{files: {{path: SHA-256}}, inputs: {{oext_bank, oext_record}}}} "
                      f"record: {oext_form_problem(oext)}")
    if oext is not None and oext_index_problem(oext, family, "X"):        # GXB R-5: its own family's X index
        raise Refused(f"OEXT_78B[{family!r}] is not a {{files: {{path: SHA-256}}, inputs: {{oext_bank, oext_record}}}} "
                      f"record: {oext_index_problem(oext, family, 'X')}")
    c0 = C0_SOURCE[family]
    if c0 is not None and not (isinstance(c0, dict) and set(c0) == {"complete_sha256", "e1_fingerprint"}
                               and all(isinstance(v, str) and CONFIG_SHA256.match(v) for v in c0.values())):
        raise Refused(f"C0_SOURCE[{family!r}] is not a {{complete_sha256, e1_fingerprint}} record")
    branch = BRANCH_78B[family]
    if branch is not None and not (isinstance(branch, dict) and set(branch) == {"path", "sha256"}
                                   and _plain_rel(branch["path"]) and _hex(branch["sha256"])):
        raise Refused(f"BRANCH_78B[{family!r}] is not a {{path, sha256}} pin")
    n_units = N_UNITS[family]
    if n_units is not None and n_units_problem(n_units, family):
        raise Refused(f"N_UNITS[{family!r}] is not N's unit record: {n_units_problem(n_units, family)}")
    if W1_18_78B is not None and w1_18_route_problem(W1_18_78B):
        raise Refused(f"W1_18_78B is not a {{files: {{path: SHA-256}}, side_units: {{...}}}} record (GXB R-20, R-32): "
                      f"{w1_18_route_problem(W1_18_78B)}")
    return {"RECIPE_S": kit, "RECIPE_S_PATH": rs.get("path") if kit is not None else None,
            "ANCHOR_BANK": _hex_or_none(fam.get("anchor_bank_sha256"), f"pins_78b.json {family} anchor_bank_sha256"),
            "S3_ORIG_POOL": _hex_or_none(untuned.get("s3_orig_pool_sha256"),
                                         f"pins_78b.json {family} untuned_pass.s3_orig_pool_sha256"),
            "RETRAIN_UNIT": _hex_or_none(a1.get("retrain_complete_sha256"),
                                         f"pins_78b.json {family} a1_attributes_unit.retrain_complete_sha256"),
            "OEXT_78B": oext, "C0_SOURCE": c0,
            "ENGINE_Y": ENGINE_Y, "N_UNITS": n_units, "W1_18_78B": W1_18_78B, "BRANCH_78B": branch}


def sc_needed_pins(kind: str, engine: str, family: str | None = None, arm: str | None = None,
                   seed: int | None = None) -> tuple:
    """The pins a scorer-block job needs: SC_KIND_PINS, plus ENGINE_Y for a job on engine Y. R1 K1: given the
    family, the retrain on a family whose anchor job stopped needs no RECIPE_S (it runs under MAIN_F; DESO2 item 36
    (2)); given the unit (arm, seed), o_only_with_regenerate of one of N's units also needs N_UNITS (DES E5)."""
    if kind not in SC_KINDS:
        raise Refused(f"{kind!r} is not a kind of the scorer block ({', '.join(SC_KINDS)})")
    pins = _sc_kind_engine_pins(kind, engine)
    if kind in SC_BRANCH_KINDS:
        pins = pins + ("BRANCH_78B",)                    # GXB R-4: the scorer block's O-ext kinds wait on the branch
    if family is not None and kind == "retrain" and family_stopped(family):
        pins = tuple(p for p in pins if p != "RECIPE_S")
    if family is not None and arm is not None and sc_unit_source(family, kind, arm, seed) == "n":
        pins = pins + ("N_UNITS",)
    return pins


def _sc_kind_engine_pins(kind: str, engine: str) -> tuple:
    """SC_KIND_PINS of the kind, plus ENGINE_Y for a job on engine Y (K4b's rule)."""
    return SC_KIND_PINS[kind] + (("ENGINE_Y",) if engine == "Y" else ())


def sc_missing_pins(family: str, kind: str, engine: str, pins78: dict, arm: str | None = None,
                    seed: int | None = None) -> list[tuple[str, str]]:
    """(pin, the event that fills it) of every pin the job needs that is still null."""
    values = sc_pin_values(family, pins78)
    return [(p, SC_PIN_EVENTS[p]) for p in sc_needed_pins(kind, engine, family, arm, seed) if values[p] is None]


def sc_pins_or_refuse(family: str, kind: str, engine: str, pins78: dict, arm: str | None = None,
                      seed: int | None = None) -> dict:
    """The pin values, or Refused naming each null pin the job needs and its event (A13: the pod does not run). R1
    K1: on a family whose anchor job stopped, the S_78 kinds and the anchor job refuse for good first (GXB O6)."""
    stop = anchor_stop_problem_for(family, kind)
    if stop:
        raise Refused(stop)
    missing = sc_missing_pins(family, kind, engine, pins78, arm, seed)
    if missing:
        raise Refused(f"{kind} for {family}: {len(missing)} pin(s) it needs are null (addendum A13): "
                      + "; ".join(f"{p} waits for {event}" for p, event in missing))
    return sc_pin_values(family, pins78)


def sc_order_problem(kind: str, complete_kinds, family: str | None = None) -> str | None:
    """A2's order: why ``kind`` cannot be planned yet (the kinds that must be recorded complete before it), or None.
    R1 K1: given the family, on a family whose anchor job stopped the retrain needs no complete anchor job (the
    committed stop record takes its place; DESO2 item 36 (2)), and the kinds of STOP_REFUSED_KINDS never plan."""
    if kind not in SC_KINDS:
        return f"{kind!r} is not a kind of the scorer block"
    if family is not None:
        stop = anchor_stop_problem_for(family, kind)
        if stop:
            return stop
        if kind == "retrain" and family_stopped(family):
            return None
    before = [k for k in SC_AFTER.get(kind, ()) if k not in set(complete_kinds)]
    if before:
        return (f"{kind} comes after {', '.join(before)} (addendum A2: the anchor job, then S_78, then the retrain, then "
                "A1's pass): record it complete in this copy's plan first")
    return None


def sc_engine_problem(kind: str, engine: str, retrain_engines=()) -> str | None:
    """PP16 and ruling 10 / A13 at planning: the wrapper kinds (X_ONLY_KINDS) on engine X only; the retrain on engine
    Y first (ruling 10) and on X only as the pre-set second job (a Y retrain recorded complete before it); A1's pass on
    the engine that trained its states (``retrain_engines``: the engines of the complete retrains whose unit is the
    RETRAIN_UNIT pin). None when allowed."""
    if engine not in ("X", "Y"):
        return f"unknown engine {engine!r}"
    if kind in X_ONLY_KINDS and engine != "X":
        return f"{kind} runs on engine X only (PP4, PP16)"
    if kind == "retrain" and engine == "X" and "Y" not in tuple(retrain_engines):
        return ("the X retrain is ruling 10's pre-set second job: it comes only after the Y retrain is recorded "
                "complete in this copy's plan")
    if kind == "a1_pass" and engine not in tuple(retrain_engines):
        return ("A1's pass runs on the engine that trained its states (ruling 10, EYD:81): the engine of the complete "
                "retrain whose unit is the RETRAIN_UNIT pin")
    return None


def sc_pod(family: str, kind: str, engine: str = "X") -> dict:
    """One scorer-block pod: its single job's E cap, guard, spend upper, need alone (KD6) and its idle-storage line
    (PP14; every stopped pod keeps its volume, KCR:161; the kinds of SC_STATE_KINDS keep training states on it)."""
    if kind not in SC_KINDS:
        raise Refused(f"{kind!r} is not a kind of the scorer block")
    pod = e_pod(family, kind)
    pod["engine"] = engine
    pod["need_usd_alone"] = funding_need_usd([[pod]], CONTINGENCY_FACTOR)["need_usd"]
    one = idle_storage(1)
    keeps = SC_STATE_KINDS.get(kind)
    pod["idle_storage"] = {"usd_per_day": one["usd_per_pod_day"], "usd_per_month": one["usd_per_month"],
                           "keeps_states": keeps is not None,
                           "why": keeps or "keeps no training state (its outputs are pulled; the volume costs the same "
                                           "while the pod is kept stopped)"}
    return pod


def sc_lines(family: str, host: str, kind: str, pod: dict) -> list[str]:
    """The two lines a scorer pod prints at init (the check's M3; A8; PP14): its need, then its idle-storage line."""
    label = KIND_LABELS.get(kind, kind)
    idle = pod["idle_storage"]
    return [f"need scorer-block pod {host} {family} {kind} ({label}; engine {pod['engine']}; single-job E cap "
            f"{pod['cap_hours']:.2f} h, guard ${pod['guard_usd']:.2f}, spend upper ${pod['spend_usd']:.2f}; KD6): "
            f"${pod['need_usd_alone']:.2f}",
            f"idle storage {host} (KD5, PP14; E, KCR:161): {idle['why']}; about ${idle['usd_per_day']:.2f} per day, "
            f"about ${idle['usd_per_month']:.2f} per month while kept stopped; counted in no guard"]


# ===== R1 K1: blocks A and B, the rules layer (GXB B-1..B-5, O1, O4, O6, O14; Part 2 §2-§4, §6, §15; DES E2-E5) =====
# Every pin below that is None is null until a recorded lead step fills it (addendum A13's pattern); each refuses with
# the event that fills it. Nothing here opens an edit file, a unit record or a gate or stop record: the caller reads
# a file at its pinned path and passes its bytes or parsed document; the edit files are named by path and SHA-256 only.

def files_form_problem(doc) -> str | None:
    """Why ``doc`` is not a {"files": {plain relative path under scripts/: SHA-256}} record (W1_18_78B's form), or
    None."""
    if not isinstance(doc, dict) or set(doc) != {"files"}:
        return "its keys are not exactly files"
    files = doc["files"]
    if not isinstance(files, dict) or not files:
        return "files is not a non-empty mapping"
    for path, digest in files.items():
        if not _plain_rel(path, "scripts/"):
            return f"files names {path!r}, not a plain relative path under scripts/"
        if not (isinstance(digest, str) and CONFIG_SHA256.match(digest)):
            return f"files[{path!r}] is not a SHA-256"
    return None


W1_18_UNIT_KEYS = ("path", "complete_sha256", "job_sha256")
DATA_ROOT = "tmp/"                       # the side units' data root (Track O's side_units paths are under it)


def w1_18_route_problem(doc) -> str | None:
    """GXB R-20, R-32: why ``doc`` is not W1_18_78B's form, Track O's maker's printout {files, side_units}, or None.
    files: files_form_problem's {plain path under scripts/: SHA-256}, holding the wrapper (W1_18_SCRIPT) and exactly one
    W1-18 index per family it names, at the standard path scripts/scale78b/settings/OEXT-78B-W1__<F>.json, and no other
    O-ext index (any basename starting OEXT-78B, any case; R-33). side_units: per family (one or both) exactly the
    family's W1-18 units (theta0 "untuned" and "a0-<seed>" of KIT a0_units), each exactly {path, complete_sha256,
    job_sha256} with the path under the data root tmp/ and both SHA-256s equal to KIT a0_units' (R-20: filled after
    theta0's job pins)."""
    if not isinstance(doc, dict) or set(doc) != {"files", "side_units"}:
        return "its keys are not exactly files and side_units"
    problem = files_form_problem({"files": doc["files"]})
    if problem:
        return problem
    units = doc["side_units"]
    if not isinstance(units, dict) or not units or not set(units) <= set(FAMILIES):
        return f"side_units is not a non-empty mapping of families among {list(FAMILIES)}"
    files = doc["files"]
    if W1_18_SCRIPT not in files:
        return f"its files do not pin the wrapper {W1_18_SCRIPT}"
    candidates = sorted(p for p in files if OEXT_INDEX_CANDIDATE_RE.search(p))
    standard = sorted(f"scripts/scale78b/settings/OEXT-78B-W1__{f}.json" for f in units)
    if candidates != standard:
        return (f"its files name the O-ext index file(s) {candidates}; exactly the W1-18 index of each family it "
                f"names, {standard} (GXB R-20, R-33)")
    for family, by_unit in sorted(units.items()):
        kit = KIT[family]["a0_units"]
        want = {("untuned" if k == "untuned" else f"a0-{k}"): v for k, v in kit.items()}
        if not isinstance(by_unit, dict) or set(by_unit) != set(want):
            return f"side_units[{family!r}] is not the family's W1-18 units {sorted(want)}"
        for name, u in sorted(by_unit.items()):
            if not isinstance(u, dict) or set(u) != set(W1_18_UNIT_KEYS):
                return f"side_units[{family!r}][{name!r}] must hold exactly {list(W1_18_UNIT_KEYS)}"
            if not _plain_rel(u["path"]) or DATA_ROOT + u["path"] != want[name]["path"]:
                return f"side_units[{family!r}][{name!r}]'s path is not KIT a0_units' (under the data root {DATA_ROOT})"
            for key in ("complete_sha256", "job_sha256"):
                if u[key] != want[name][key]:
                    return (f"side_units[{family!r}][{name!r}].{key} is not KIT a0_units' (R-20: filled after theta0's "
                            "job pins)")
    return None


def _plain_rel(path, under: str = "") -> bool:
    return (isinstance(path, str) and path.startswith(under) and not path.startswith("/") and "\\" not in path
            and all(part not in ("", ".", "..") for part in path.split("/")))


def _hex(value) -> bool:
    return isinstance(value, str) and bool(CONFIG_SHA256.match(value))


# ----- the arms, their edits and their steps (Part 2 §2.1-§2.3; GXB O1) -----
# What each arm's edit does to the 4,800 training rows (P1 §1, §10; Part 2 §1.5-§1.11): the removal arms remove 600
# rows (R: the sealed draws, MANIFEST "rows" 600; A1 and L1 k = 600; H1 octile 0, 600 rows), the add arms add 48, the
# dose arms 96 and 192; s4_top (the dose fallback) adds its kept count n, known only when the fallback fires.
ARM_EDIT = {"R": ("remove", 600), "A1": ("remove", 600), "L1": ("remove", 600), "H1": ("remove", 600),
            "S1": ("add", 48), "S3": ("add", 48), "S4": ("add", 48), "S4_96": ("add", 96), "S4_192": ("add", 192),
            "s4_top": ("add", None), "a0": None}
# RK's named steps per arm (GXB O1: 33 removal, 38 add and a0, 39 for S4_96 and S4_192); s4_top has none (derived).
ARM_STEPS = {**{a: STEPS["remove"] for a in ("R", "A1", "L1", "H1")}, **{a: STEPS["add"] for a in ("S1", "S3", "S4")},
             "S4_96": STEPS["dose"], "S4_192": STEPS["dose"], "a0": STEPS["a0"]}
METHOD_ARMS = ("A1", "L1", "H1", "S1", "S3", "S4")
DOSE_ARMS = ("S4_96", "S4_192")
S4_KEEP = 192                             # Part 2 §1.11: lists.s4.keep (the dose fallback fires below it)
S4_DOSE_96 = 96
S4_MIN_KEPT = 48                          # fewer than 48 kept: the untuned pass exits 3 (a build stop)


def dose_arms_for(kept) -> tuple:
    """GXB K-5 (Part 2 §5, P1 §10, DESO item 34's boundary cases): the dose arms for ``kept`` kept S4 rows n:
    n >= 192: (S4_96, S4_192); 97-191: (S4_96, s4_top) with s4_top = n rows; exactly 96: (S4_96,) (S4_top would equal
    it); 49-95: (s4_top,); exactly 48: () (no dose arm; s4_top would equal S4); fewer than 48: Refused (the untuned
    pass exits 3, a build stop)."""
    if isinstance(kept, bool) or type(kept) is not int:
        raise Refused(f"the kept count is a whole number, not {kept!r}")
    if kept < S4_MIN_KEPT:
        raise Refused(f"{kept} kept S4 rows: fewer than {S4_MIN_KEPT}, the untuned pass exits 3 (a build stop; no dose "
                      "and no S4)")
    if kept >= S4_KEEP:
        return ("S4_96", "S4_192")
    if kept > S4_DOSE_96:
        return ("S4_96", "s4_top")
    if kept == S4_DOSE_96:
        return ("S4_96",)
    if kept > S4_MIN_KEPT:
        return ("s4_top",)
    return ()


def s4_top_rows_ok(n) -> bool:
    """s4_top exists only for 49-95 and 97-191 kept rows (K-5): at 48 it equals S4, at 96 S4_96, from 192 S4_192."""
    if not _int(n) or n < S4_MIN_KEPT:
        return False
    return "s4_top" in dose_arms_for(n)


def steps_for_rows(rows) -> int:
    """GXB O1: ceil(rows / 128) optimizer steps for ``rows`` training rows (a positive integer)."""
    if isinstance(rows, bool) or type(rows) is not int or rows < 1:
        raise Refused(f"a training row count must be a positive integer, not {rows!r}")
    return -(-rows // ROWS_PER_STEP)


def arm_training_rows(arm: str, edit_rows) -> int:
    """The arm's training rows after its edit: BASE_ROWS minus a removal's rows, plus an add's rows (a0: BASE_ROWS)."""
    if arm not in ARM_EDIT:
        raise Refused(f"unknown arm {arm!r}")
    if ARM_EDIT[arm] is None:
        if edit_rows is not None:
            raise Refused("a0 has no edit")
        return BASE_ROWS
    op, fixed = ARM_EDIT[arm]
    if isinstance(edit_rows, bool) or type(edit_rows) is not int or edit_rows < 1:
        raise Refused(f"{arm}'s edit row count must be a positive integer, not {edit_rows!r}")
    if fixed is not None and edit_rows != fixed:
        raise Refused(f"{arm}'s edit {op}s {fixed} rows by its contract, not {edit_rows}")
    if arm == "s4_top" and not s4_top_rows_ok(edit_rows):
        raise Refused(f"s4_top holds {edit_rows} kept rows; it exists only for 49-95 and 97-191 kept rows (GXB K-5)")
    return BASE_ROWS - edit_rows if op == "remove" else BASE_ROWS + edit_rows


def arm_steps(arm: str, training_rows) -> int:
    """GXB O1: the arm's steps = ceil(training rows / 128), derived from its edit's resulting row count; a named arm
    whose derived steps differ from ARM_STEPS (RK's STEPS) refuses; s4_top takes ceil((4,800 + n) / 128): 38 for
    n <= 64, 39 for n >= 65."""
    if arm not in ARM_EDIT:
        raise Refused(f"unknown arm {arm!r}")
    derived = steps_for_rows(training_rows)
    if arm in ARM_STEPS and derived != ARM_STEPS[arm]:
        raise Refused(f"{arm}: ceil({training_rows} / {ROWS_PER_STEP}) = {derived} steps, but RK names {ARM_STEPS[arm]} "
                      "(GXB O1); the edit's row count does not fit the arm")
    return derived


# The R_d edits of blocks A and B, by family and draw (Part 2 §2.3; M: shasum -a 256 at 3481d85, 8 Nov 2026, equal to
# Part 2's table): OLMo-2-7B's R_d4-R_d5 from SEAL, R_d6-R_d10 from stage 1's r-draws/edits/, R_d11-R_d13 from the
# OLMo folder; Llama-3.1-8B's from its sealed set (each equal to its MANIFEST entry). Draw d runs at seed 1100 + d.
_R_OLMO_SEAL = ".ai/inputs/gate-b-sealed-20261008/out/edits/"
_R_OLMO_STAGE1 = ".ai/inputs/stage1-commitments-20261016/r-draws/edits/"
_R_OLMO_78B = ".ai/inputs/scale-78b-r-draws-olmo2-20261105/out/edits/"
_R_LLAMA = ".ai/inputs/scale-78b-sealed-llama3-20261105/out/edits/"
R_DRAW_SOURCES: dict[str, dict[int, dict]] = {
    "olmo2-7b": {d: {"path": f"{base}R_d{d}.json", "sha256": sha} for d, base, sha in (
        (4, _R_OLMO_SEAL, "5cf35162ec9f22e90fa9d053c4c75ee8c1287f06975dda2310095aa9ed58900e"),
        (5, _R_OLMO_SEAL, "73d336ccf27e12d5e6f7c2b5c06cd89b14498804a4d140ef87e10a7afcf0be7a"),
        (6, _R_OLMO_STAGE1, "c41c3df7721356eeeea4399edbc0ffbff17b06b256d934d216929cb0766fdfb1"),
        (7, _R_OLMO_STAGE1, "dbb4b554c1062d9845b732c65bf95d0601909ce21ff72487d426dc32d3944b1b"),
        (8, _R_OLMO_STAGE1, "b3a9dee0a429ed1c85ae1f3ea5dc4dc3f50da3a0b59acbca4601e071104ba92c"),
        (9, _R_OLMO_STAGE1, "55066a0407b7578f8cf724a2c350ea6cf4a3d89d4f90a06713c6d50d7f5a58dc"),
        (10, _R_OLMO_STAGE1, "805fb6faa49b51ffde3732d1c68553249620e14eec5cfb827db2c01021321c57"),
        (11, _R_OLMO_78B, "94af783311716eae36ab5ae0e8e72e6f8ecda15c047d5d4d2f23a0dbf7130ee0"),
        (12, _R_OLMO_78B, "21e0dc208465cb042c330d1d48e4c3a185e34fde62ec12db8a3bd079bd8499e5"),
        (13, _R_OLMO_78B, "bb1e3bf4743468eef789027486b28d8e8faad7db2f977aa9cd6057412192cd43"))},
    "llama31-8b": {d: {"path": f"{_R_LLAMA}R_d{d}.json", "sha256": sha} for d, sha in (
        (4, "37235592ad186d9ae6174250f5bda1a9e253b9c8627f7c7cf727faa2564d42e0"),
        (5, "222487acccdecc04c9b6cb0b0f8fdd4cfd8ef5551e5993ec5d10460e0c29db03"),
        (6, "73b10a31b16e6054fa87a813551fb8e3a4ccf6ac5b94c4ea040abd35c2d34b6e"),
        (7, "bba6568c59c4899c5f30595a22773c92f39244e615eb363cd37d3361e40b5d1d"),
        (8, "097260ffb47ac112fd114e5ae3eb92d68a8d0b8117a74073255c3edb357e5ca1"),
        (9, "8dd2a194ace3a498141bfb10993636d7373db0343d18539563bcdd80066acbf6"),
        (10, "f20e6be770d765c75be45b92d5be4ff00c801d76cdbb9964d1a2b4adde52d016"),
        (11, "664c6f1b2aafe342fad29e1df93515b2869e9b63ffe4e1c1f3fe69f626c4cd95"),
        (12, "3a43db9653048854e2f2588aa3a7e94a547398d5144dca54af390d2741073e6a"),
        (13, "07ccde7185a68461a759db952bc5297382f1dcabf6dfe00044e1dac907e4b5dd"))},
}
R_DRAW_ROWS = 600                         # every R_d removes 600 rows (P1 §3.1; the Llama MANIFEST's "rows")

# The method arms' edits per family: {"path", "sha256", "rows"} ("rows" = the rows the edit removes or adds), or None
# until the scorer block writes it and a recorded lead step fills it (Part 2 §2.3 "[to be entered]"; DESO item 22).
# H1 and S1 are filled (Part 2 §1.7, §1.9; M: shasum -a 256 of the committed H1 files at 3481d85; the S1 files hold
# text and live in git-ignored tmp/, named by hash only; R: .ai/inputs/scale-78b-s1-llama3-20261105/
# build_s1_llama3.py:88 for OLMo's path, its README.md:21 for Llama's).
METHOD_EDITS: dict[str, dict[str, dict | None]] = {
    "olmo2-7b": {
        "H1": {"path": ".ai/inputs/stage1-commitments-20261016/length-rules/edits/octile_0.json",
               "sha256": "f5b1762f662e931235f798497248b2f342e6d2b2011ce5a0bfecf53678b4def7", "rows": 600},
        "S1": {"path": "tmp/stage1-olmo/retrieved/a-3/tree/round1/1103-edit-"
                       "904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10-e1-a1/edit.json",
               "sha256": "904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10", "rows": 48},
        "A1": None, "L1": None, "S3": None, "S4": None, "S4_96": None, "S4_192": None, "s4_top": None},
    "llama31-8b": {
        "H1": {"path": ".ai/inputs/scale-78b-length-rules-llama3-20261105/out/edits/octile_0.json",
               "sha256": "9a01637ec63dc38f6e4dec646a0bc4b8c00c36521fa8831fe4fb87e8df3a1c5f", "rows": 600},
        "S1": {"path": "tmp/scale-78b-s1-llama3-20261105/edits/add_s1.json",
               "sha256": "6942699398ade7f7ddb6f5b47b06e8b253de6ff9bbd142b8138acc061468dd0a", "rows": 48},
        "A1": None, "L1": None, "S3": None, "S4": None, "S4_96": None, "S4_192": None, "s4_top": None},
}
METHOD_EDIT_EVENTS = {
    "A1": "the scorer block's a1_pass, then scorers_78b.py score_edit a1 on the Mac (Part 2 §1.5); the lead fills "
          "METHOD_EDITS[family]['A1'] with its a1_remove600.edit.json path, SHA-256 and rows 600",
    "L1": "the scorer block's l1_scan, then scorers_78b.py score_edit scorer --name l1 (Part 2 §1.6); the lead fills "
          "METHOD_EDITS[family]['L1']",
    "S3": "the untuned pass and rep_pass, then s3_score, write_score_add and add_edit (Part 2 §1.10); the lead fills "
          "METHOD_EDITS[family]['S3']",
    "S4": "the untuned pass's S4 call, then add_edit of dose_s4.json (Part 2 §1.11); the lead fills it",
    "S4_96": "the untuned pass's S4 call, then add_edit of dose_s4_96.json (Part 2 §1.11); the lead fills it",
    "S4_192": "the untuned pass's S4 call, then add_edit of dose_s4_192.json (Part 2 §1.11); the lead fills it",
    "s4_top": "only if the dose fallback fires: add_edit of dose_s4_top.json with its kept count n from "
              "s4_doses_record.json (Part 2 §1.11, §1.16 lists.s4_top.rows); the lead fills it",
}


def edit_pin_problem(pin, arm: str) -> str | None:
    """Why ``pin`` is not an edit pin {path, sha256, rows} for ``arm`` (a plain relative path, a SHA-256, the arm's
    row count), or None."""
    if not isinstance(pin, dict) or set(pin) != {"path", "sha256", "rows"}:
        return "its keys are not exactly path, sha256 and rows"
    if not (_plain_rel(pin["path"]) and pin["path"].endswith(".json")):
        return f"its path {pin['path']!r} is not a plain relative .json path"
    if not _hex(pin["sha256"]):
        return "its sha256 is not a SHA-256"
    try:
        arm_training_rows(arm, pin["rows"])
    except Refused as exc:
        return str(exc)
    return None


def run_edit(family: str, arm: str, seed: int) -> dict | None:
    """The edit a block A or B run of ``arm`` at ``seed`` trains on, by path and SHA-256 only, with its training rows
    and derived steps: R at seed s is R_d with d = s - 1100 (R_DRAW_SOURCES); a0 has none (None); a method or dose
    arm's pin is METHOD_EDITS[family][arm], and a null pin refuses with its filling event (A13's pattern). Another
    family's pin is never read (each family's table is its own)."""
    family_of(family)
    if arm == "a0":
        return None
    if arm == "R":
        d = seed - R_SEED_BASE if type(seed) is int else None
        src = R_DRAW_SOURCES[family].get(d)
        if src is None:
            raise Refused(f"no R_d edit for {family} at seed {seed!r} in Part 2 §2.3's table (R_d4-R_d13 at 1104-1113)")
        rows = arm_training_rows("R", R_DRAW_ROWS)
        return {"arm": "R", "draw": d, "path": src["path"], "sha256": src["sha256"], "rows": R_DRAW_ROWS,
                "training_rows": rows, "steps": arm_steps("R", rows), "engine_arm": f"edit-{src['sha256']}"}
    if arm not in METHOD_EDITS[family]:
        raise Refused(f"{arm!r} is not an arm of the 7-8B block tables")
    pin = METHOD_EDITS[family][arm]
    if pin is None:
        raise Refused(f"{arm}'s edit for {family} is null (Part 2 §2.3 [to be entered]; addendum A13): it waits for "
                      f"{METHOD_EDIT_EVENTS[arm]}")
    problem = edit_pin_problem(pin, arm)
    if problem:
        raise Refused(f"METHOD_EDITS[{family!r}][{arm!r}] is not an edit pin: {problem}")
    rows = arm_training_rows(arm, pin["rows"])
    return {"arm": arm, "path": pin["path"], "sha256": pin["sha256"], "rows": pin["rows"], "training_rows": rows,
            "steps": arm_steps(arm, rows), "engine_arm": f"edit-{pin['sha256']}"}


# ----- the block tables per plan (Part 2 §2.2) -----
PLAN_CODES = ("A", "B9", "H")             # stage1_rules.plan_code_for's codes; "H" is the high-noise branch H (b)
PLAN_ARMS_78B = {"A": METHOD_ARMS, "B9": ("A1", "H1", "S1", "S4"), "H": ("A1", "H1", "S1", "S4")}
BLOCK_A_METHOD_SEEDS = (1102, 1103, 1104)
BLOCK_A_R_SEEDS = (1104, 1105)            # R_4 and R_5
BLOCK_A_A0_SEEDS = (1104,)
BLOCK_B_METHOD_SEEDS = {"A": (1105, 1106, 1107), "B9": tuple(range(1105, 1111)), "H": tuple(range(1105, 1114))}
BLOCK_B_A0_SEEDS = (1105, 1106, 1107)     # a0 at 1101-1107 in every plan
DOSE_SEEDS = {3: (1102, 1103, 1104), 6: (1102, 1103, 1104, 1105, 1106, 1107)}   # ruling 12's money rule; DES F1's order
STOP_DROPPED_ARMS = ("A1", "L1", "S3")    # DESO2 item 36 (1): not run on a family whose anchor job stopped
AB_ARM_ORDER = ("A1", "L1", "H1", "S1", "S3", "S4", "S4_96", "S4_192", "s4_top", "a0", "R")   # the deal's arm order


def block_runs_78b(family: str, plan_code: str | None, block: str, dose_seeds: int = 0,
                   kept: int | None = None) -> list[tuple[str, int]]:
    """The runs (arm, seed) of block A or B for ``family`` (Part 2 §2.2), seed-major, arm-minor. Block A is the same
    in every plan: the six method arms at 1102-1104, R_4 at 1104, R_5 at 1105, a0 at 1104 (21). Block B by plan: A
    the six at 1105-1107, R_6-R_7, a0 1105-1107 (23); B9 A1, H1, S1, S4 at 1105-1110, R_6-R_10, a0 (32); H (b) the
    four at 1105-1113, R_6-R_13, a0 (47); plus the secondary dose rows (``dose_seeds`` 3 or 6 per dose arm: 1102-1104
    or 1102-1107; 0 = none planned yet) of the dose arms dose_arms_for(``kept``) gives for the untuned pass's kept S4
    count (GXB K-5; a filled s4_top pin must hold exactly ``kept`` rows). On a family whose anchor job stopped, A1, L1 and S3 are dropped (DESO2 item
    36 (1)): block A 12 runs, B plan A 14, B9 26, H (b) 38."""
    family_of(family)
    if block == "A":
        if plan_code is not None and plan_code not in PLAN_CODES:
            raise Refused(f"unknown plan {plan_code!r} (one of {', '.join(PLAN_CODES)})")
        if dose_seeds:
            raise Refused("the dose rows are block B's (Part 2 §2.2)")
        runs = ([(a, s) for s in BLOCK_A_METHOD_SEEDS for a in METHOD_ARMS]
                + [("R", s) for s in BLOCK_A_R_SEEDS] + [("a0", s) for s in BLOCK_A_A0_SEEDS])
    elif block == "B":
        if plan_code not in PLAN_CODES:
            raise Refused(f"block B needs its plan (one of {', '.join(PLAN_CODES)}) from block B's plan record "
                          f"(PLAN_B_78B), not {plan_code!r}")
        seeds = BLOCK_B_METHOD_SEEDS[plan_code]
        runs = ([(a, s) for s in seeds for a in PLAN_ARMS_78B[plan_code]]
                + [("R", s) for s in seeds if s != seeds[0]] + [("a0", s) for s in BLOCK_B_A0_SEEDS])
        if dose_seeds:
            if dose_seeds not in DOSE_SEEDS:
                raise Refused(f"the dose arms run at 3 or 6 seeds (ruling 12; Part 2 §2.2), not {dose_seeds!r}")
            dose_arms = dose_arms_for(kept)
            top = METHOD_EDITS[family].get("s4_top")
            if "s4_top" in dose_arms and isinstance(top, dict) and top.get("rows") != kept:
                raise Refused(f"the s4_top pin holds {top.get('rows')!r} rows, not the {kept} kept (GXB K-5)")
            runs += [(a, s) for s in DOSE_SEEDS[dose_seeds] for a in dose_arms]
    else:
        raise Refused(f"block {block!r} has no 7-8B block table here (blocks A and B; block 0 is N's)")
    if family_stopped(family):
        runs = [r for r in runs if r[0] not in STOP_DROPPED_ARMS]
    return sorted(runs, key=lambda r: (r[1], AB_ARM_ORDER.index(r[0])))


def deal_ab(runs: list) -> list[list]:
    """The interleaving deal of blocks A and B (Part 2 §2.4; the stage-1 kit's deal, R: runkit/stage1-olmo/
    stage1_rules.py:1085-1100): arm-major (AB_ARM_ORDER), seed-minor, run i to pod i mod P with P = len(pod_sizes(n)),
    so at most MAX_ARMS_PER_POD_78B (4) runs per pod and each arm's runs on consecutive pods. A run listed twice, or a
    pod holding one arm twice, refuses (an outcome-free rule fixed before launch)."""
    ordered = sorted((tuple(r) for r in runs), key=lambda r: (AB_ARM_ORDER.index(r[0]), r[1]))
    if len(set(ordered)) != len(ordered):
        raise Refused("a run is listed twice")
    p = len(pod_sizes(len(ordered)))
    pods = [ordered[i::p] for i in range(p)]
    for pod in pods:
        arms = [a for a, _ in pod]
        if len(set(arms)) != len(arms):
            raise Refused("the deal puts one arm twice on a pod; the lead decides")
        if len(pod) > MAX_ARMS_PER_POD_78B:
            raise Refused(f"a pod of {len(pod)} runs; at most {MAX_ARMS_PER_POD_78B} (KD2)")
    return pods


def block_job_78b(family: str, arm: str, seed: int, padded_tokens_per_step: float | None = None) -> dict:
    """One block A or B training job: ``a0_arm`` for a0, else ``arm`` on its edit (run_edit, by path and SHA-256), at
    the steps derived from the edit's row count (GXB O1), with its in-job O-ext step (DES E3: the cap term) and its
    train_scale input (Part 2 §2.1): an edit arm needs its padded tokens per step from the edit's token counts (a
    missing count refuses; a0 takes none: train_scale 1)."""
    edit = run_edit(family, arm, seed)
    if edit is None:
        if padded_tokens_per_step is not None:
            raise Refused("a0's train_scale is 1 by definition (its own padded tokens): give no count")
        job = job_record(family, "a0_arm", STEPS["a0"], "a0", seed, oext=True)
    else:
        if padded_tokens_per_step is None:
            raise Refused(f"{arm} at {seed}: its padded tokens per step (from its edit's token counts; Part 2 §2.1) "
                          "are missing: train_scale has no input")
        finite(padded_tokens_per_step)
        if padded_tokens_per_step <= 0:
            raise Refused("padded tokens per step must be positive")
        job = job_record(family, "arm", edit["steps"], arm, seed, padded_tokens_per_step, oext=True)
    job["edit"] = None if edit is None else {k: edit[k] for k in ("path", "sha256", "rows", "engine_arm")}
    job["train_scale"] = train_scale(family, padded_tokens_per_step)
    return job


# ----- the gate record and block B's plan record (GXB O14 as corrected in its second set, 15:22 UTC; X4) -----
# Two null pins, each {"path", "sha256"} of a committed record, each filled by a recorded lead step:
# 1. GATE_78B, after ruling 9's gate and before block A: option ([B] or [C]), families, N's PROVISIONAL plan, the noise
#    reading's output SHA-256 and the live balance. Block A's init reads its families only (block A is the same in
#    every plan; P1 §6.4).
# 2. PLAN_B_78B, after block A's record-done and blinded_sigma.py, before block B: blinded_sigma.py's output SHA-256
#    (sigma_A and df only) and its inputs file's SHA-256, whether SR-2 is adopted, and block B's plan by P1 §6.1 (A,
#    B9, H (b) or "review"). Block B's init reads its plan (and the gate's families); a "review" plan plans nothing
#    (P1 §6.1: the user decides). Both refuse before their fill.
GATE_78B: dict | None = None
GATE_EVENT = ("ruling 9's gate (after N's reading, the day the new money is in): a recorded lead step writes the gate "
              "record and fills GATE_78B with its path and SHA-256 (GXB O14, corrected)")
GATE_RECORD_KIND = "stage1-78b gate record"
GATE_KEYS = ("kind", "version", "option", "families", "provisional_plan", "sigma_F_plan", "noise_reading_sha256",
             "balance_usd", "utc", "recorded_by")       # GXB R-24: sigma_F_plan, the chosen family's own plan under [C]
GATE_OPTIONS = {"B": ("olmo2-7b", "llama31-8b"), "C": ("olmo2-7b",)}   # ruling 5: [C] runs F1 = OLMo-2-7B
PLAN_B_78B: dict | None = None
PLAN_B_EVENT = ("block A's record-done and blinded_sigma.py (sigma_A and its df; SR-2's reading): a recorded lead step "
                "writes block B's plan record and fills PLAN_B_78B with its path and SHA-256, before block B (GXB O14, "
                "corrected)")
PLAN_B_RECORD_KIND = "stage1-78b block-B plan record"
PLAN_B_KEYS = ("kind", "version", "plan", "sr2_adopted", "sr2_reason", "plan_basis", "sigma_A_pp",
               "blinded_sigma_output_sha256", "blinded_sigma_inputs_sha256", "utc", "recorded_by")   # R-24: sigma_A_pp
PLAN_B_CODES = PLAN_CODES + ("review",)   # P1 §6.1: above the review ceiling there is no 7-8B primary family
# GXB K-6 (fourth set): without SR-2 the record names why (the blinding test not verified, or the simulation's reading)
# and the plan's basis: N's sigma_pool under [B], the chosen family's sigma_F under [C] (P1 §6.2, §6.4); with SR-2,
# block A's sigma_A from blinded_sigma.py, whose output and inputs-file SHA-256s it then carries.
SR2_REASONS = ("blinding_test_not_verified", "simulation_reading")
PLAN_BASES = {"adopted": "sigma_A", "B": "sigma_pool_N", "C": "sigma_F"}


# GXB R-29 (twelfth set): P1 §6.4 applies §6.1's whole rule to sigma_A, the review ceiling included. The per-plan
# removal-MDE factors are noise_reading.py's pinned ones (R: scripts/scale78b/noise_reading.py:93 MDE_FACTOR; :281-299
# seed_rule): review when factor x sigma > 2 x SESOI (5 pp), i.e. above 7.0388 / 9.2721 / 10.7066 pp for A / B9 /
# H (b); only H (b)'s can fire (sigma <= 4.5 for A, <= 6.0 for B9). Compared exactly, as noise_reading does.
PLAN_MDE_FACTORS = {"A": "1.4207", "B9": "1.0785", "H": "0.9340"}
SESOI_PP = 5


def plan_for_sigma(sigma_pp) -> str:
    """P1 §6.1's rule on sigma (ruling 3; GXB R-29): <= 4.5 pp A, <= 6.0 pp B9, above H (stage1_rules.plan_code_for's
    thresholds); then the review ceiling: "review" when the plan's removal MDE, PLAN_MDE_FACTORS[plan] x sigma, is above
    2 x SESOI (exact, on the decimal value of sigma). A sigma that is not a finite number >= 0 refuses."""
    try:                                  # GXB R-33 (KR2-5): an int too large for a float refuses, never raises
        finite_float = not isinstance(sigma_pp, bool) and isinstance(sigma_pp, (int, float)) \
            and math.isfinite(float(sigma_pp))
    except OverflowError:
        finite_float = False
    if not finite_float or sigma_pp < 0:
        raise Refused(f"sigma {repr(sigma_pp)[:40]} is not a finite number of percentage points >= 0")
    sigma = Fraction(repr(sigma_pp)) if isinstance(sigma_pp, float) else Fraction(sigma_pp)
    plan = "A" if sigma <= Fraction("4.5") else "B9" if sigma <= Fraction("6.0") else "H"
    if Fraction(PLAN_MDE_FACTORS[plan]) * sigma > 2 * SESOI_PP:
        return "review"
    return plan


def _texts_ok(doc) -> bool:
    return all(isinstance(doc[k], str) and doc[k].strip() for k in ("utc", "recorded_by"))


def gate_record_problem(doc) -> str | None:
    """Why ``doc`` is not the gate record's form, or None: exactly GATE_KEYS; kind and version 1; option "B" (both
    families) or "C" (OLMo-2-7B only, ruling 5) with families equal to the option's; N's provisional plan one of
    PLAN_CODES or "review"; the noise reading's output SHA-256; a finite balance >= 0; utc and recorded_by texts."""
    if not isinstance(doc, dict) or set(doc) != set(GATE_KEYS):
        return f"it must hold exactly {list(GATE_KEYS)}"
    if doc["kind"] != GATE_RECORD_KIND or doc["version"] != 1 or type(doc["version"]) is not int:
        return f"its kind and version are not {GATE_RECORD_KIND!r} 1"
    if doc["option"] not in GATE_OPTIONS:
        return f"its option {doc['option']!r} is not B or C"
    if not isinstance(doc["families"], list) or tuple(doc["families"]) != GATE_OPTIONS[doc["option"]]:
        return f"option {doc['option']} runs {list(GATE_OPTIONS[doc['option']])}, not {doc['families']!r}"
    if doc["provisional_plan"] not in PLAN_B_CODES:
        return f"its provisional plan {doc['provisional_plan']!r} is not one of {list(PLAN_B_CODES)}"
    if doc["option"] == "C" and doc["sigma_F_plan"] not in PLAN_B_CODES:
        return f"under [C] sigma_F_plan (the chosen family's own sigma_F plan, P1 §6.2) is one of {list(PLAN_B_CODES)}"
    if doc["option"] == "B" and doc["sigma_F_plan"] is not None:
        return "under [B] sigma_F_plan is null (sigma_F decides only under [C])"
    if not _hex(doc["noise_reading_sha256"]):
        return "noise_reading_sha256 is not a SHA-256"
    try:
        if finite(doc["balance_usd"]) < 0:
            return "balance_usd is negative"
    except Refused:
        return "balance_usd is not a finite number"
    if not _texts_ok(doc):
        return "utc and recorded_by must be non-empty texts"
    return None


def plan_b_record_problem(doc, option: str | None = None) -> str | None:
    """Why ``doc`` is not block B's plan record, or None (GXB O14 corrected; K-6): exactly PLAN_B_KEYS; kind and
    version 1; plan one of A, B9, H or "review"; sr2_adopted True or False. Adopted: sr2_reason null, plan_basis
    "sigma_A", both blinded_sigma.py SHA-256s given. Not adopted: sr2_reason one of SR2_REASONS, plan_basis
    "sigma_pool_N" under [B] or "sigma_F" under [C] (checked against ``option``, the gate's, when given), both
    blinded_sigma.py hashes null (refused if given). utc and recorded_by non-empty texts."""
    if not isinstance(doc, dict) or set(doc) != set(PLAN_B_KEYS):
        return f"it must hold exactly {list(PLAN_B_KEYS)}"
    if doc["kind"] != PLAN_B_RECORD_KIND or doc["version"] != 1 or type(doc["version"]) is not int:
        return f"its kind and version are not {PLAN_B_RECORD_KIND!r} 1"
    if doc["plan"] not in PLAN_B_CODES:
        return f"its plan {doc['plan']!r} is not one of {list(PLAN_B_CODES)}"
    if not isinstance(doc["sr2_adopted"], bool):
        return "sr2_adopted is not true or false"
    hashes = ("blinded_sigma_output_sha256", "blinded_sigma_inputs_sha256")
    if doc["sr2_adopted"]:
        if doc["sr2_reason"] is not None:
            return "SR-2 is adopted, so sr2_reason is null"
        if doc["plan_basis"] != PLAN_BASES["adopted"]:
            return "SR-2 is adopted, so plan_basis is sigma_A (block A's sigma_A from blinded_sigma.py)"
        try:
            sigma_plan = plan_for_sigma(doc["sigma_A_pp"])
        except Refused:
            return "SR-2 is adopted, so sigma_A_pp is blinded_sigma.py's sigma_A (a finite number >= 0)"
        if doc["plan"] != sigma_plan:
            return f"plan {doc['plan']!r} is not the plan sigma_A = {doc['sigma_A_pp']} pp gives ({sigma_plan}; GXB R-24)"
        for key in hashes:
            if not _hex(doc[key]):
                return f"SR-2 is adopted, so {key} must be a SHA-256"
    else:
        if doc["sr2_reason"] not in SR2_REASONS:
            return f"SR-2 is not adopted, so sr2_reason is one of {list(SR2_REASONS)}"
        if doc["plan_basis"] not in (PLAN_BASES["B"], PLAN_BASES["C"]):
            return "SR-2 is not adopted, so plan_basis is sigma_pool_N ([B]) or sigma_F ([C])"
        if doc["sigma_A_pp"] is not None:
            return "SR-2 is not adopted, so sigma_A_pp is null"
        if option is not None and doc["plan_basis"] != PLAN_BASES.get(option):
            return f"under option {option} the plan's basis without SR-2 is {PLAN_BASES.get(option)}, not {doc['plan_basis']}"
        for key in hashes:
            if doc[key] is not None:
                return f"SR-2 is not adopted, so {key} must be null"
    if not _texts_ok(doc):
        return "utc and recorded_by must be non-empty texts"
    return None


def _pinned_record_or_refuse(name: str, pin, event: str, data: bytes, kind: str, problem_of) -> dict:
    if pin is None:
        raise Refused(f"the pin {name} is null: it waits for {event}")
    if not (isinstance(pin, dict) and set(pin) == {"path", "sha256"} and _plain_rel(pin["path"]) and _hex(pin["sha256"])):
        raise Refused(f"{name} is not a {{path, sha256}} pin")
    if not isinstance(data, (bytes, bytearray)) or hashlib.sha256(data).hexdigest() != pin["sha256"]:
        raise Refused(f"the record's bytes do not hash to {name} ({pin['sha256'][:12]}...)")
    try:
        doc = json.loads(data)
    except ValueError:
        raise Refused(f"the record at {name} is not JSON") from None
    problem = problem_of(doc)
    if problem:
        raise Refused(f"the record at {name} is not {kind!r}: {problem}")
    return doc


def gate_record_or_refuse(data: bytes) -> dict:
    """The gate record from ``data`` (the bytes the caller read at GATE_78B's path): Refused while GATE_78B is null
    (with its event), when the bytes' SHA-256 is not the pin's, when they are not JSON, or when the form is not
    gate_record_problem's."""
    return _pinned_record_or_refuse("GATE_78B", GATE_78B, GATE_EVENT, data, GATE_RECORD_KIND, gate_record_problem)


def plan_b_record_or_refuse(data: bytes, option: str | None = None) -> dict:
    """Block B's plan record from ``data`` (read at PLAN_B_78B's path): Refused while PLAN_B_78B is null (with its
    event), when the bytes are not the pinned record, or when its form is not plan_b_record_problem's (with the
    gate's ``option`` for the plan's basis)."""
    return _pinned_record_or_refuse("PLAN_B_78B", PLAN_B_78B, PLAN_B_EVENT, data, PLAN_B_RECORD_KIND,
                                    lambda d: plan_b_record_problem(d, option))


def block_init_or_refuse(block: str, family: str, data: bytes, plan_b_data: bytes | None = None) -> dict:
    """What a block's init reads (GXB O14, corrected): block A the gate record's families only (a family outside them
    does not run: under [C] only OLMo-2-7B, ruling 5); block B the gate's families and block B's plan from PLAN_B_78B's
    record; a "review" plan plans nothing (P1 §6.1). Each refuses before its pin is filled."""
    family_of(family)
    if block not in ("A", "B"):
        raise Refused(f"block {block!r} reads nothing from the gate record")
    doc = gate_record_or_refuse(data)
    if block == "A" and doc["provisional_plan"] == "review":
        raise Refused("the gate's provisional plan is 'review' (P1 §6.1: no 7-8B primary family; the user decides the "
                      "next step, GXB R-1): block A plans nothing by default")
    if family not in doc["families"]:
        raise Refused(f"the gate chose option {doc['option']} ({', '.join(doc['families'])}): {family} runs no block "
                      f"{block}")
    out = {"block": block, "family": family, "option": doc["option"], "families": tuple(doc["families"]), "plan": None}
    if block == "B":
        plan_b = plan_b_record_or_refuse(plan_b_data, doc["option"])
        if plan_b["plan_basis"] == PLAN_BASES["B"] and plan_b["plan"] != doc["provisional_plan"]:
            raise Refused(f"block B's plan {plan_b['plan']!r} on N's sigma_pool is not the gate's provisional plan "
                          f"{doc['provisional_plan']!r} (GXB R-24; P1 §6.4: N's value decides alone)")
        if plan_b["plan_basis"] == PLAN_BASES["C"] and plan_b["plan"] != doc["sigma_F_plan"]:
            raise Refused(f"block B's plan {plan_b['plan']!r} on sigma_F is not the gate's sigma_F plan "
                          f"{doc['sigma_F_plan']!r} (GXB R-24; P1 §6.2)")
        if plan_b["plan"] == "review":
            raise Refused("block B's plan is 'review' (P1 §6.1: no 7-8B primary family; the user decides): block B "
                          "plans nothing")
        out.update(plan=plan_b["plan"], sr2_adopted=plan_b["sr2_adopted"], plan_basis=plan_b["plan_basis"])
    return out


# ----- the anchor job's stops (GXB O6; item 14; DESO item 7, DESO2 item 36; R: scripts/make_anchor_answers.py) -----
# The record's form is GXB's fourth set (15:43 UTC, last item), the one Track S's blinded_sigma.py reads (R:
# B/ws-s/scripts/scale78b/blinded_sigma.py:69-70 STOP_KINDS and STOP_RECORD_KIND, :218-235 check_anchor_stop: it reads
# kind, family, stop_kind and exit_code): kind "scale-78b anchor stop", the family, stop_kind safe_anchors_below_64
# (exit 3) or harmful_prompt_does_not_encode (exit 1), the exit code, the job's JOB-DONE.json SHA-256 and the stop
# line's ids and counts ("counts"; the field name of Track S's own test fixture), version 1.
ANCHOR_EXIT_FEW = 3                       # R: make_anchor_answers.py:37 EXIT_FEW (fewer than 64 safe anchors kept)
ANCHOR_EXIT_ERROR = 1                     # an AnchorJobError (a SystemExit with a message, :41) exits 1
ANCHOR_N_SAFE = ANCHOR_N_HARMFUL = 64     # R: make_anchor_answers.py:33-34
ANCHOR_HARMFUL_RE = re.compile(r"^harmful prompt (\d+) \((\d+) of (\d+)\) does not encode \((.+)\); "
                               r"the list needs a reviewed new version$")   # R: make_anchor_answers.py:121-122
ANCHOR_STOP_KIND = "scale-78b anchor stop"
ANCHOR_STOP_KEYS = ("kind", "version", "family", "stop_kind", "exit_code", "job_done_sha256", "counts")
STOP_FEW_SAFE = "safe_anchors_below_64"
STOP_HARMFUL = "harmful_prompt_does_not_encode"
ANCHOR_STOPS = {STOP_FEW_SAFE: ANCHOR_EXIT_FEW, STOP_HARMFUL: ANCHOR_EXIT_ERROR}
# The family's committed stop record {"path", "sha256"}, or None (no stop recorded: the normal route). Filled by a
# recorded lead step from the anchor job's own signal only (anchor_stop_record); never from a crash. A pinned record
# marks the family stopped only once anchor_stop_or_refuse has read its bytes at the pin and checked them (K1V-6).
ANCHOR_STOP: dict[str, dict | None] = {"olmo2-7b": None, "llama31-8b": None}
ANCHOR_STOP_EVENT = ("the family's anchor job stopped by its own signal: K2's writer writes the text-free stop record "
                     "(anchor_stop_record) and a recorded lead step fills ANCHOR_STOP[family] with its path and SHA-256")
_ANCHOR_STOPS_READ: dict[str, str] = {}   # family -> the pinned SHA-256 whose record anchor_stop_or_refuse checked
# DESO2 item 36 (1): on a stopped family there is no anchor bank and no S_78: these kinds never run there. The anchor
# job itself does not run again (DESO item 7: no re-draw, no script change; I: a stop is the job's result).
STOP_REFUSED_KINDS = frozenset({"rep_pass", "l1_scan", "classifier", "a1_pass", "anchor"})


def anchor_exit_kind(exit_code, message: str | None = None) -> str:
    """The anchor job's end by its own signal only (GXB O6): exit 0 "complete"; exit 3 safe_anchors_below_64 (fewer
    than 64 safe anchors); exit 1 with the AnchorJobError message "harmful prompt k (k+1 of n) does not encode (...);
    the list needs a reviewed new version" (``message``: the job's last stderr line) harmful_prompt_does_not_encode.
    Any other exit or message is "crash" (the kit's crash rule; never a stop)."""
    if isinstance(exit_code, bool) or type(exit_code) is not int:
        return "crash"
    if exit_code == 0:
        return "complete"
    if exit_code == ANCHOR_EXIT_FEW:
        return STOP_FEW_SAFE
    if exit_code == ANCHOR_EXIT_ERROR and isinstance(message, str) and ANCHOR_HARMFUL_RE.match(message.strip()):
        return STOP_HARMFUL
    return "crash"


def anchor_stop_record(family: str, exit_code, message: str | None, job_done_sha256: str,
                       counts: dict | None = None) -> dict:
    """The text-free stop record (GXB O6; the fourth set's form): family, stop_kind, exit code, the anchor job's
    JOB-DONE.json SHA-256 and the stop line's ids and counts only. safe_anchors_below_64 takes ``counts`` {"kept",
    "needed"} from the job's counts line (kept < 64 = needed); harmful_prompt_does_not_encode takes the prompt index
    and position from the message. A crash or a complete job is Refused: only the frozen script's own signal records a
    stop."""
    family_of(family)
    stop = anchor_exit_kind(exit_code, message)
    if stop not in ANCHOR_STOPS:
        raise Refused(f"the anchor job's exit {exit_code!r} is {stop!r}, not a stop (GXB O6: exit 3, or exit 1 with "
                      "the harmful-pair AnchorJobError message): the kit's crash rule applies")
    if not _hex(job_done_sha256):
        raise Refused("the anchor job's JOB-DONE.json SHA-256 is missing")
    if stop == STOP_FEW_SAFE:
        if not (isinstance(counts, dict) and set(counts) >= {"kept", "needed"}
                and all(type(counts[k]) is int and not isinstance(counts[k], bool) for k in ("kept", "needed"))
                and counts["needed"] == ANCHOR_N_SAFE and 0 <= counts["kept"] < ANCHOR_N_SAFE):
            raise Refused("an exit-3 stop needs the job's counts line {kept < 64, needed 64}")
        line = {"kept": counts["kept"], "needed": counts["needed"]}
    else:
        m = ANCHOR_HARMFUL_RE.match(message.strip())
        k, pos, n = (int(m.group(i)) for i in (1, 2, 3))
        if pos != k + 1 or n != ANCHOR_N_HARMFUL or not 0 <= k < n:
            raise Refused("the harmful-pair message's ids do not fit the frozen script's form")
        line = {"prompt_index": k, "position": pos, "of": n}
    return {"kind": ANCHOR_STOP_KIND, "version": 1, "family": family, "stop_kind": stop, "exit_code": exit_code,
            "job_done_sha256": job_done_sha256, "counts": line}


def _int(value) -> bool:
    return type(value) is int and not isinstance(value, bool)


def anchor_stop_problem(doc, family: str, job_done_sha256: str | None = None) -> str | None:
    """Why ``doc`` is not ``family``'s stop record (anchor_stop_record's form, rebuilt from its own fields), or does
    not name the anchor job's JOB-DONE.json ``job_done_sha256`` when that is given; None when it is."""
    if not isinstance(doc, dict) or set(doc) != set(ANCHOR_STOP_KEYS):
        return f"it must hold exactly {list(ANCHOR_STOP_KEYS)}"
    if doc["kind"] != ANCHOR_STOP_KIND or doc["version"] != 1 or not _int(doc["version"]) or doc["family"] != family:
        return f"it is not {family}'s {ANCHOR_STOP_KIND!r} version 1"
    if doc["stop_kind"] not in ANCHOR_STOPS or not _int(doc["exit_code"]) \
            or doc["exit_code"] != ANCHOR_STOPS[doc["stop_kind"]]:
        return "its stop_kind and exit code are not one of the frozen script's two stop signals"
    line = doc["counts"]
    if doc["stop_kind"] == STOP_FEW_SAFE:
        if not (isinstance(line, dict) and set(line) == {"kept", "needed"} and line["needed"] == ANCHOR_N_SAFE
                and _int(line["kept"]) and 0 <= line["kept"] < ANCHOR_N_SAFE):
            return "its counts are not {kept < 64, needed 64}"
    elif not (isinstance(line, dict) and set(line) == {"prompt_index", "position", "of"}
              and all(_int(line[k]) for k in line) and line["of"] == ANCHOR_N_HARMFUL
              and 0 <= line["prompt_index"] < ANCHOR_N_HARMFUL and line["position"] == line["prompt_index"] + 1):
        return "its counts are not {prompt_index, position, of 64}"
    if not _hex(doc["job_done_sha256"]):
        return "job_done_sha256 is not a SHA-256"
    if job_done_sha256 is not None and doc["job_done_sha256"] != job_done_sha256:
        return (f"it names JOB-DONE.json {doc['job_done_sha256'][:12]}..., not the anchor job's "
                f"{str(job_done_sha256)[:12]}...")
    return None


def anchor_stop_or_refuse(family: str, data: bytes, job_done_sha256: str) -> dict:
    """The family's stop record from ``data`` (the bytes the caller read at ANCHOR_STOP[family]'s path), in the
    GATE_78B pattern (K1V-6): Refused while the pin is null (with its event), when the bytes do not hash to the pin, or
    when the record is not the family's (anchor_stop_problem: its kind, family, stop_kind, exit code and counts) or
    does not name the anchor job's JOB-DONE.json ``job_done_sha256`` (required, KR8). Only then is the family marked
    stopped."""
    family_of(family)
    if not _hex(job_done_sha256):
        raise Refused("the anchor job's JOB-DONE.json SHA-256 is required to read a stop record (KR8)")
    doc = _pinned_record_or_refuse(f"ANCHOR_STOP[{family!r}]", ANCHOR_STOP[family], ANCHOR_STOP_EVENT, data,
                                   ANCHOR_STOP_KIND, lambda d: anchor_stop_problem(d, family, job_done_sha256))
    _ANCHOR_STOPS_READ[family] = ANCHOR_STOP[family]["sha256"]
    return doc


def family_stopped(family: str) -> bool:
    """Whether ``family``'s anchor job stopped: False while ANCHOR_STOP[family] is null; True only after
    anchor_stop_or_refuse read and checked the record at the pin (K1V-6). A pin that is not {path, sha256}, or one
    whose record has not been read and checked, refuses (never the normal route by default)."""
    family_of(family)
    pin = ANCHOR_STOP[family]
    if pin is None:
        return False
    if not (isinstance(pin, dict) and set(pin) == {"path", "sha256"} and _plain_rel(pin["path"]) and _hex(pin["sha256"])):
        raise Refused(f"ANCHOR_STOP[{family!r}] is not a {{path, sha256}} pin")
    if _ANCHOR_STOPS_READ.get(family) != pin["sha256"]:
        raise Refused(f"ANCHOR_STOP[{family!r}] is pinned, but its stop record has not been read at the pin and checked "
                      "(anchor_stop_or_refuse first): the family is neither stopped nor normal until then")
    return True


def anchor_stop_problem_for(family: str, kind: str) -> str | None:
    """On a family whose anchor job stopped: the kinds of STOP_REFUSED_KINDS refuse for good (no anchor bank, no S_78;
    DESO2 item 36 (1)), and the retrain is planned under MAIN_F (its own rule). None otherwise."""
    if kind in STOP_REFUSED_KINDS and family_stopped(family):
        return (f"{family}'s anchor job stopped (ANCHOR_STOP): {kind} never runs on that family (DESO2 item 36 (1); "
                "DESO item 7: no re-draw, no script change)")
    return None


def sc_recipe(family: str, kind: str) -> str:
    """The recipe name a scorer-block job of ``kind`` carries: SC_RECIPE's, except the retrain on a family whose
    anchor job stopped, which runs under the family's main config "B" (DESO2 item 36 (2); AM1 changes 2, 5)."""
    if kind not in SC_KINDS:
        raise Refused(f"{kind!r} is not a kind of the scorer block")
    if kind == "retrain" and family_stopped(family):
        return "B"
    return SC_RECIPE[kind]


# ----- N's units for o_only_with_regenerate, keyed by (arm, seed) (DES E5; Part 2 §4.5; the seed key) -----
# N_UNITS[family]: {"<arm>-<seed>": {"path", "complete_sha256", "job_sha256"[, "edit_sha256" for R]}} for every N run
# (block0_runs), null until block 0's record-done and a recorded lead step (SC_PIN_EVENTS["N_UNITS"]). The paths are
# relative to the repository and lie in block 0's working copy (KD7).
N_UNITS: dict[str, dict | None] = {"olmo2-7b": None, "llama31-8b": None}
W1_18_78B: dict | None = None             # {files: {path: SHA-256}, side_units: {F: {unit: {path, complete_sha256,
#                                           job_sha256}}}}: Track O's W1-18 route and settings (GXB O3, R-20, R-32)


def unit_key(arm: str, seed: int) -> str:
    return f"{arm}-{seed}"


def n_units_problem(doc, family: str) -> str | None:
    """Why ``doc`` is not N_UNITS[family]'s form, or None: exactly one entry per N run of the family keyed
    "<arm>-<seed>"; each {path, complete_sha256, job_sha256} (an R unit also edit_sha256) with a plain relative path
    under the family's block-0 working copy tmp/family-probe-s78-<family>-0/."""
    if not isinstance(doc, dict):
        return "it is not a mapping"
    want = {unit_key(a, s): a for a, s in block0_runs(family)}
    if set(doc) != set(want):
        return f"its keys are not N's units {sorted(want)}"
    for key, arm in want.items():
        u = doc[key]
        keys = {"path", "complete_sha256", "job_sha256"} | ({"edit_sha256"} if arm == "R" else set())
        if not isinstance(u, dict) or set(u) != keys:
            return f"{key} must hold exactly {sorted(keys)}"
        if not _plain_rel(u["path"], f"tmp/{WORKING_COPY_PREFIX}{family}-0/"):
            return f"{key}'s path is not under tmp/{WORKING_COPY_PREFIX}{family}-0/"
        if not all(_hex(u[k]) for k in keys - {"path"}):
            return f"{key} holds a value that is not a SHA-256"
    return None


def sc_units(family: str, kind: str) -> list[dict]:
    """The units a scorer-block job of ``kind`` may carry, each keyed by (arm, seed) with its source: for
    o_only_with_regenerate the family's reused a0 side units ("side", KIT a0_units) and N's units ("n", block0_runs:
    OLMo R 1101-1103; Llama R 1101-1103 and a0 1103), so on OLMo-2-7B N's R_1101 and the side a0-1101 are two units of
    one seed; for the other kinds sc_seeds' seeds with SC_ARM's arm (source None)."""
    family_of(family)
    if kind not in SC_KINDS:
        raise Refused(f"{kind!r} is not a kind of the scorer block")
    if kind == "o_only_with_regenerate":
        out = [{"arm": "a0", "seed": s, "source": "side"} for s in sc_seeds(family, kind)]
        out += [{"arm": a, "seed": s, "source": "n"} for a, s in block0_runs(family)]
        keys = [unit_key(u["arm"], u["seed"]) for u in out]
        if len(set(keys)) != len(keys):
            raise Refused(f"{family}: two units with one (arm, seed) key")
        return out
    return [{"arm": SC_ARM.get(kind), "seed": s, "source": None} for s in sc_seeds(family, kind)]


def sc_unit_source(family: str, kind: str, arm: str | None, seed) -> str | None:
    """The source ("side" or "n") of the unit (arm, seed) of a scorer-block job, None for a kind without units;
    Refused when (arm, seed) is not one of sc_units (the seed alone never names a unit)."""
    for u in sc_units(family, kind):
        if u["arm"] == arm and u["seed"] == seed:
            return u["source"]
    raise Refused(f"{kind} for {family}: ({arm!r}, {seed!r}) is not one of its units "
                  f"{[unit_key(u['arm'], u['seed']) for u in sc_units(family, kind)]}")


def n_unit_or_refuse(family: str, arm: str, seed: int) -> dict:
    """N's unit (arm, seed) of the family from N_UNITS: Refused while the pin is null (its event), or when the unit is
    not one of N's."""
    if (arm, seed) not in block0_runs(family):
        raise Refused(f"({arm!r}, {seed!r}) is not one of {family}'s N units")
    doc = N_UNITS[family]
    if doc is None:
        raise Refused(f"N_UNITS[{family!r}] is null: N's unit {unit_key(arm, seed)} waits for {SC_PIN_EVENTS['N_UNITS']}")
    problem = n_units_problem(doc, family)
    if problem:
        raise Refused(f"N_UNITS[{family!r}] is not N's unit record: {problem}")
    return dict(doc[unit_key(arm, seed)])


# ----- block A's re-judged units (Part 2 §6; DESO item 26: N's units, the reused a0 units and theta0, 7 per family) --
def rejudged_pins(family: str, block: str) -> tuple:
    """The re-judged units of ``block`` for ``family`` in the 1B REJUDGED_PINS form ({name, arm, seed, target, path,
    complete_sha256, job_sha256}). Block A: N's units (from N_UNITS; their arm, path and hashes null until block 0's
    record-done), the reused a0 side units and theta0 (from KIT a0_units): OLMo 3 + 3 + 1, Llama 4 + 2 + 1. Every
    other block: none."""
    family_of(family)
    if block != "A":
        return ()
    n = N_UNITS[family]
    if n is not None and n_units_problem(n, family):
        n = None                                         # K1V-8: a malformed pin never breaks an import; it refuses at
    out = []                                             # use (rejudged_or_refuse names its problem)
    for arm, seed in block0_runs(family):
        u = n[unit_key(arm, seed)] if n is not None else None
        label = f"edit-{u['edit_sha256']}" if u is not None and arm == "R" else (arm if u is not None else None)
        out.append({"name": f"N {arm} {seed}", "arm": label, "seed": seed, "target": "e1",
                    "path": u["path"] if u else None, "complete_sha256": u["complete_sha256"] if u else None,
                    "job_sha256": u["job_sha256"] if u else None})
    units = KIT[family]["a0_units"]
    for seed in sorted(s for s in units if s != "untuned"):
        out.append({"name": f"a0 {seed} (side unit)", "arm": "a0", "seed": seed, "target": "e1", **units[seed]})
    out.append({"name": "theta0 (untuned)", "arm": "a0", "seed": 1101, "target": "init", **units["untuned"]})
    return tuple(out)


def rejudged_or_refuse(family: str, block: str) -> tuple:
    """rejudged_pins, or Refused naming each entry with a null field and N_UNITS's event (a judge launch over block A
    waits for block 0's record-done)."""
    n = N_UNITS[family]
    if block == "A" and n is not None and n_units_problem(n, family):
        raise Refused(f"N_UNITS[{family!r}] is not N's unit record: {n_units_problem(n, family)}; block A's judge "
                      "launch does not run")
    pins = rejudged_pins(family, block)
    null = [p["name"] for p in pins if any(p[k] is None for k in ("arm", "path", "complete_sha256", "job_sha256"))]
    if null:
        raise Refused(f"block {block}'s re-judged units {null} are null for {family}: they wait for "
                      f"{SC_PIN_EVENTS['N_UNITS']}")
    return pins


# ----- W1-18, the answer-cap branch and the 500-bank kinds (DES E2; DESO2 item 37; Part 2 §4.2; GXB O3, O4) -----
BRANCHES = ("full", "128")
BRANCH_DEFAULT = "full"                   # every cap and plan uses Branch full until a family's branch record
W1_18_FAMILIES = {"B": ("olmo2-7b", "llama31-8b"), "C": ("olmo2-7b",)}   # DESO2 item 37: [C] OLMo-2-7B's units only
W1_18_HOST_FAMILY = "olmo2-7b"            # GXB K-3 (fourth set): the one W1-18 pod lives in OLMo-2-7B's scorer-block
#                                           copy; under [B] it packs both families' W1-18 settings and side units
# The kinds whose every job reads the 500 bank (the O-ext pass), and so refuse before the family's branch record;
# block A and B's arm jobs read it too (their in-job O-ext step; DES E3), block 0's never (bank500_job).
BANK500_KINDS = frozenset({"o_only", "o_only_with_regenerate", "c0", "ref_eval", "safe_lora", "ref_train",
                           "ref_train_bqi", "b10_certify"})   # R3 K3: certify runs O-ext as a report (B10's settings)
BANK500_BLOCKS = ("A", "B")               # the blocks whose arm and a0_arm jobs carry the in-job O-ext step
OEXT_BANK_KINDS = BANK500_KINDS | {"arm", "a0_arm"}   # the kinds that may name an O-ext bank in check_keys
BRANCH_RECORD_KIND = "stage1-78b branch record"
BRANCH_KEYS = ("kind", "version", "family", "branch", "source", "w1_18_record_sha256", "utc", "recorded_by")


def bank500_job(kind: str, block: str) -> bool:
    """Whether a job of ``kind`` in ``block`` reads the 500 bank: the BANK500_KINDS anywhere, and arm and a0_arm in
    blocks A and B (never in block 0)."""
    return kind in BANK500_KINDS or (kind in ("arm", "a0_arm") and block in BANK500_BLOCKS)


def w1_18_units(family: str) -> list[dict]:
    """The family's W1-18 units: theta0 and the reused a0 side units (KIT a0_units; Part 2 §4.2: OLMo-2-7B theta0 and
    a0 1101-1103, Llama-3.1-8B theta0 and a0 1101-1102), each by path and COMPLETE.json and job.json SHA-256."""
    units = kit_of(family)["a0_units"]
    keys = ["untuned"] + sorted(s for s in units if s != "untuned")
    return [{"unit": k, **units[k]} for k in keys]


def w1_18_plan(option: str) -> dict:
    """The one W1-18 pod (DESO2 item 37; GXB O4): one check per family of the option, each with its own settings and
    its own record (overrefusal_checks__<family>.json, GXB R-53), so each family's branch is read from its own record;
    under [C] OLMo-2-7B's units only. 7 units under [B], 4 under [C]."""
    if option not in W1_18_FAMILIES:
        raise Refused(f"option {option!r} is not B or C")
    fams = W1_18_FAMILIES[option]
    return {"option": option, "host_family": W1_18_HOST_FAMILY, "families": fams,
            "records": {f: W1_18_RECORD_NAME.format(family=f) for f in fams},
            "units": {f: w1_18_units(f) for f in fams}, "n_units": sum(len(w1_18_units(f)) for f in fams)}


def w1_18_host_problem(family: str) -> str | None:
    """The W1-18 pod is planned in W1_18_HOST_FAMILY's scorer-block copy only (one pod for both families)."""
    if family != W1_18_HOST_FAMILY:
        return (f"the one W1-18 pod (DESO2 item 37) is planned in {W1_18_HOST_FAMILY}'s scorer-block copy, not "
                f"{family}'s")
    return None


def w1_18_first_problem(planned_kinds) -> str | None:
    """W1-18 is the scorer block's first O job (DES E2; DESO2 item 37): it cannot be planned once a 500-bank job is
    planned or complete in the copy. None when it can."""
    before = sorted({k for k in planned_kinds if k in BANK500_KINDS})
    if before:
        return f"W1-18 is the first O job, before any O-ext pod; {', '.join(before)} is already planned"
    return None


def branch_record_problem(doc, family: str) -> str | None:
    """Why ``doc`` is not ``family``'s branch record, or None: exactly BRANCH_KEYS; Branch "128" only from that
    family's W1-18 record (source "w1_18", its SHA-256 given; Part 2 §4.2: 128 only if every unit of the family
    passes); "Branch full by default" (source "default", no W1-18 record) when the check was not built or did not
    finish (DESO2 item 37); Branch "full" may also come from a W1-18 record that failed the bar."""
    if not isinstance(doc, dict) or set(doc) != set(BRANCH_KEYS):
        return f"it must hold exactly {list(BRANCH_KEYS)}"
    if doc["kind"] != BRANCH_RECORD_KIND or doc["version"] != 1 or not _int(doc["version"]) or doc["family"] != family:
        return f"it is not {family}'s {BRANCH_RECORD_KIND!r} version 1"
    if doc["branch"] not in BRANCHES:
        return f"its branch {doc['branch']!r} is not one of {list(BRANCHES)}"
    if doc["source"] == "w1_18":
        if not _hex(doc["w1_18_record_sha256"]):
            return "a branch from W1-18 names its W1-18 record's SHA-256"
    elif doc["source"] == "default":
        if doc["branch"] != BRANCH_DEFAULT or doc["w1_18_record_sha256"] is not None:
            return "the default record is Branch full with no W1-18 record"
    else:
        return f"its source {doc['source']!r} is not w1_18 or default"
    if not all(isinstance(doc[k], str) and doc[k].strip() for k in ("utc", "recorded_by")):
        return "utc and recorded_by must be non-empty texts"
    return None


# K1V-5: each family's branch is read only from its pinned branch record: BRANCH_78B[family] = {path, sha256}, null
# until W1-18's record-done (or the "Branch full by default" record) and K2's branch-record step (GXB K-8).
BRANCH_78B: dict[str, dict | None] = {"olmo2-7b": None, "llama31-8b": None}
BRANCH_EVENT = ("the W1-18 pod's record-done (or the 'Branch full by default' record when the check is not built or does "
                "not finish; DESO2 item 37): K2's branch-record step writes the family's branch record and a recorded "
                "lead step fills BRANCH_78B[family] with its path and SHA-256")
SC_BRANCH_KINDS = frozenset({"o_only", "o_only_with_regenerate", "c0"})   # the scorer block's O-ext kinds (GXB R-4)


def branch_record_or_refuse(family: str, data: bytes) -> dict:
    """The family's branch record from ``data`` (the bytes read at BRANCH_78B[family]'s path): Refused while the pin
    is null (with its event), when the bytes do not hash to it, or when the record is not the family's."""
    family_of(family)
    return _pinned_record_or_refuse(f"BRANCH_78B[{family!r}]", BRANCH_78B[family], BRANCH_EVENT, data,
                                    BRANCH_RECORD_KIND, lambda d: branch_record_problem(d, family))


def bank500_problem(family: str, kind: str, block: str, branch_bytes: bytes | None = None) -> str | None:
    """A 500-bank job (bank500_job) refuses while the family's branch record pin is null (Part 2 §4.2: the branch is
    chosen before any 7-8B 500-bank answer exists), or when ``branch_bytes`` are not the pinned record. None
    otherwise."""
    if not bank500_job(kind, block):
        return None
    if BRANCH_78B[family] is None:
        return (f"{kind} in block {block} reads the 500 bank: it waits for {family}'s branch record (BRANCH_78B: "
                f"{BRANCH_EVENT})")
    try:
        branch_record_or_refuse(family, branch_bytes)
    except Refused as exc:
        return f"{family}'s branch record is not the pinned one: {exc}"
    return None


def branch_switch_problem(family: str, new_doc, pinned_bytes: bytes | None = None) -> str | None:
    """The branch is never switched after it is chosen (Part 2 §4.2; R: PR4:541-552): once BRANCH_78B[family] is
    filled, a new branch record refuses unless it equals the pinned one (read at the pin) in family, branch, source and
    W1-18 record."""
    if BRANCH_78B[family] is None:
        return None
    old_doc = branch_record_or_refuse(family, pinned_bytes)
    same = all(old_doc.get(k) == (new_doc or {}).get(k) for k in ("family", "branch", "source", "w1_18_record_sha256"))
    if not same:
        return (f"{old_doc.get('family')}'s branch is {old_doc.get('branch')!r} from {old_doc.get('source')!r}; it is "
                "never switched (Part 2 §4.2)")
    return None


def oext_flags(family: str, kind: str, branch_bytes: bytes, regenerated: bool = False) -> dict:
    """The Branch-128 flags (DESO item 9; Part 2 §4.2): under Branch 128 every O-ext command takes --w1-18-record
    (c0, o_only, o_only_with_regenerate and the arm step) and the regenerated units also --dev100-source; under Branch
    full no --dev100-source. The branch is read only from the family's pinned record (``branch_bytes`` at BRANCH_78B).
    R3 K3 (GXB R-47, M: a fixture through the unchanged oext_eval, tests/test_runner_ab_78b.py): under Branch full
    from a FAILING W1-18 record (source "w1_18") the O-ext eval settings pin that record, and oext_eval.prepare ->
    read_w1_18 reads it at run time (a missing --w1-18-record refuses "W1-18's record cannot be read"), so the flag is
    passed whenever the branch record names a W1-18 record; "Branch full by default" (no record) passes none."""
    branch_doc = branch_record_or_refuse(family, branch_bytes)
    if kind not in OEXT_BANK_KINDS:
        raise Refused(f"{kind} has no O-ext step")
    record = branch_doc["w1_18_record_sha256"] if branch_doc["source"] == "w1_18" else None
    return {"w1_18_record": record, "dev100_source": branch_doc["branch"] == "128" and bool(regenerated)}


# ----- R3 K3 (item 13): the evaluation-only references through scripts/scale78b/refs_78b.py (Part 2 §3.1, §3.2, §16.1;
# GXB O2, X2, R-34, R-35, R-37, R-38 amended, R-41, R-42; Track R's P7) -----
REFERENCE_SEEDS = (1102, 1103, 1104, 1105, 1106, 1107)   # R: refs_78b.REFERENCE_SEEDS (the 6-seed set; F1 drops 1105-1107)
REF_KINDS = ("b10_certify", "ref_eval", "safe_lora")     # B10 / B11 through Track R's wrapper, per reference seed
REFS_WRAPPER_78B = "scripts/scale78b/refs_78b.py"
REFS_INDEX_RE = re.compile(r"^scripts/scale78b/settings/REFS-78B__(olmo2-7b|llama31-8b)__(110[2-7])\.json$")
REFS_INDEX_CANDIDATE_RE = re.compile(r"(^|/)refs-78b[^/]*$", re.IGNORECASE)
# REFS_78B[F][S]: Track R's maker's printed form (make_refs_settings_78b.py --refs-78b F S): {"files": {path under
# scripts/: SHA-256} (the wrapper, the seed's index and settings, the 1B B10/B11 code), "inputs": {"oext_bank",
# "oext_record"}}; null until a recorded lead step fills it (after Track O's O-ext fill: P6 (b)).
REFS_78B: dict[str, dict[int, dict | None]] = {f: {s: None for s in REFERENCE_SEEDS} for f in ("olmo2-7b", "llama31-8b")}
REFS_EVENT = ("Track R's maker prints REFS_78B[F][S]'s form (make_refs_settings_78b.py --refs-78b F S) once seed S's a0 "
              "unit and 1101's fingerprints are filled in Track R's pins; a recorded lead step fills it (Track R's P7)")
# The 1B safety-prompt text file (the B10 settings' prefix.text_sha256; Part 2 §3.2): packed by path and this SHA-256.
REF_PREFIX_SHA256 = "0fcc6beb8240d7b8e7b8c19bb033af6c8a66e568e50afc33f58707a503fdec98"
B10_EXIT_CERTIFICATION = 4                # R: eval_adapter.py EXIT_CERTIFICATION (the stage-1 kit's B10's failed gate)


def ref_cert_source(family: str, seed) -> str:
    """GXB R-35: the a0 unit seed S's certification pins: "side" (a reused side unit: 1102; 1103 on OLMo-2-7B), "n"
    (N's a0-1103 on Llama-3.1-8B, ruling 8), "A" (block A's a0, 1104) or "B" (block B's a0, 1105-1107)."""
    family_of(family)
    if seed not in REFERENCE_SEEDS:
        raise Refused(f"{seed!r} is not a reference seed {list(REFERENCE_SEEDS)}")
    if seed == 1103 and family == "llama31-8b":
        return "n"
    if seed in KIT[family]["a0_units"]:
        return "side"
    return "A" if seed in BLOCK_A_A0_SEEDS else "B"


def refs_form_problem(pin, family: str, seed) -> str | None:
    """Why ``pin`` is not REFS_78B[family][seed]'s form, or None: exactly {files, inputs}; files plain paths under
    scripts/ with SHA-256s, the wrapper among them, exactly one refs index (any basename starting REFS-78B) and it the
    family's and seed's standard one; inputs exactly OEXT_INPUTS' SHA-256s."""
    if not isinstance(pin, dict) or set(pin) != {"files", "inputs"}:
        return "its keys are not exactly files and inputs"
    files, inputs = pin["files"], pin["inputs"]
    if not isinstance(files, dict) or not files:
        return "files is not a non-empty mapping"
    for path, digest in files.items():
        if not _plain_rel(path, "scripts/") or not _hex(digest):
            return f"files[{path!r}] is not a plain path under scripts/ with a SHA-256"
    if REFS_WRAPPER_78B not in files:
        return f"its files do not pin the wrapper {REFS_WRAPPER_78B}"
    found = [p for p in files if REFS_INDEX_CANDIDATE_RE.search(p)]
    want = f"scripts/scale78b/settings/REFS-78B__{family}__{seed}.json"
    if found != [want]:
        return f"its files name the refs index file(s) {sorted(found)}; exactly {want}"
    if not isinstance(inputs, dict) or set(inputs) != set(OEXT_INPUTS) or not all(_hex(v) for v in inputs.values()):
        return f"inputs does not hold exactly {list(OEXT_INPUTS)} as SHA-256s"
    return None


def refs_or_refuse(family: str, seed) -> dict:
    """REFS_78B[family][seed] in its form; Refused while null (its event) or off its form."""
    ref_cert_source(family, seed)
    pin = REFS_78B[family].get(seed)
    if pin is None:
        raise Refused(f"REFS_78B[{family!r}][{seed}] is null: {REFS_EVENT}")
    problem = refs_form_problem(pin, family, seed)
    if problem:
        raise Refused(f"REFS_78B[{family!r}][{seed}] is not in its form: {problem}")
    return pin


# ----- R3 K3 (R-67; KD9): the engine-Y measured record, the pin measured kinds on Y wait for -----
Y_MEASURED_RECORD_KIND = "stage1-78b engine-Y measured record"
Y_MEASURED_KEYS = ("kind", "version", "engine_y", "gpu", "records", "utc", "recorded_by")
Y_REMEASURE_KIND = "stage1-78b engine-Y re-measure"      # the runner's per-job record (job-I/y-remeasure.json)
Y_MEASURED_RECORD: dict | None = None     # {path, sha256} of record-y-measured's record, filled by a recorded step
Y_MEASURED_EVENT = ("the first engine-Y pod (ruling 10's a0-1101 retrain) pulled and recorded done, then plan_tool.py "
                    "record-y-measured writes the measured record from its y-remeasure.json files; a recorded lead step "
                    "fills Y_MEASURED_RECORD with its path and SHA-256 and sets Y_MEASURED (KD9; GXB R-67)")


def y_measured_problem(doc) -> str | None:
    """Why ``doc`` is not the engine-Y measured record (record-y-measured's form), or None: exactly Y_MEASURED_KEYS;
    engine_y = ENGINE_Y's pin, gpu the measured GPU, records a non-empty list of {path, sha256, family, job_kind} with
    a retrain among them (the first Y pod's job, ruling 10)."""
    if not isinstance(doc, dict) or set(doc) != set(Y_MEASURED_KEYS):
        return f"it must hold exactly {list(Y_MEASURED_KEYS)}"
    if doc["kind"] != Y_MEASURED_RECORD_KIND or doc["version"] != 1 or not _int(doc["version"]):
        return f"it is not a {Y_MEASURED_RECORD_KIND!r} version 1"
    if ENGINE_Y is None or doc["engine_y"] != ENGINE_Y:
        return "its engine_y is not ENGINE_Y's pin"
    if doc["gpu"] != GPU_NAME:
        return "its GPU is not the measured one"
    recs = doc["records"]
    if not isinstance(recs, list) or not recs or not all(
            isinstance(r, dict) and set(r) == {"path", "sha256", "family", "job_kind"} and _plain_rel(r["path"])
            and _hex(r["sha256"]) and r["family"] in FAMILIES for r in recs):
        return "records is not a non-empty list of {path, sha256, family, job_kind}"
    if not any(r["job_kind"] == "retrain" for r in recs):
        return "no record is the a0-1101 retrain's (the first Y pod, ruling 10)"
    if not (isinstance(doc["utc"], str) and doc["utc"].strip() and isinstance(doc["recorded_by"], str)
            and doc["recorded_by"].strip()):
        return "utc and recorded_by must be non-empty texts"
    return None


def y_measured_or_refuse(data: bytes | None) -> dict:
    """The engine-Y measured record from ``data`` (the bytes at Y_MEASURED_RECORD's path): Refused while the pin is
    null, when the bytes do not hash to it, or when the record is off its form."""
    return _pinned_record_or_refuse("Y_MEASURED_RECORD", Y_MEASURED_RECORD, Y_MEASURED_EVENT, data or b"",
                                    Y_MEASURED_RECORD_KIND, y_measured_problem)


def golden_table() -> dict:
    """KCR §4 and §7 reproduced from this module (test 1 compares it with KCR's printed values)."""
    out = {}
    for family in FAMILIES:
        caps = {n: cap_hours(arm_pod(family, [33] * (n - 1) + [38])) for n in range(1, 5)}
        out[family] = {"gen_allcap_s": gen_allcap_s(family),
                       "upper_m_38_s": upper_m_s(family, 38), "upper_m_33_s": upper_m_s(family, 33),
                       "requirement_38_s": requirement_s(family, 38), "requirement_33_s": requirement_s(family, 33),
                       "measured_upper_s": measured_upper_s(family), "caps_h": caps,
                       "guards_usd": {n: cents(guard_usd(c)) for n, c in caps.items()},
                       "spend_upper_usd": {n: cents(pod_spend_usd(arm_pod(family, [33] * (n - 1) + [38])))
                                           for n in range(1, 5)},
                       "evalonly_upper_s": evalonly_upper_s(family)}
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["block0"]:
        print(json.dumps(block0_report(), indent=1, sort_keys=True))
        return 0
    if argv[:1] == ["golden"]:
        print(json.dumps(golden_table(), indent=1, sort_keys=True))
        return 0
    if argv[:1] == ["e-caps"]:
        table = {f: {k: {"cap_h": e_cap_hours(f, k), "upper_s": round(e_upper_s(f, k)["upper_s"], 1),
                         "guard_usd": cents(guard_usd(e_cap_hours(f, k)))} for k in E_KINDS} for f in FAMILIES}
        print(json.dumps(table, indent=1, sort_keys=True))
        return 0
    if argv[:1] == ["kit"]:                 # K1: the per-family constants block and the null-until-filled pins
        print(json.dumps({"kit": {f: {k: (v if k != "a0_units" else {str(s): u for s, u in v.items()})
                                      for k, v in KIT[f].items()} for f in FAMILIES},
                          "pins": {"ENGINE_Y": ENGINE_Y, "Y_MEASURED": Y_MEASURED, **PINS,
                                   "SEALED_SETS": SEALED_SETS, "GATE_78B": GATE_78B, "PLAN_B_78B": PLAN_B_78B,
                                   "N_UNITS": N_UNITS, "ANCHOR_STOP": ANCHOR_STOP, "W1_18_78B": W1_18_78B,
                                   "BRANCH_78B": BRANCH_78B,
                                   "OEXT_TERM_MEASURED_S": OEXT_TERM_MEASURED_S, "OEXT_78B_Y": OEXT_78B_Y,
                                   "METHOD_EDITS": METHOD_EDITS}}, indent=1, sort_keys=True))
        return 0
    print(__doc__.split("\n\n")[0])
    print("commands: golden | block0 | e-caps | kit")
    return 2


if __name__ == "__main__":
    sys.exit(main())
