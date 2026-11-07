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
STEPS = {"remove": 33, "add": 38, "a0": 38}  # R: PR4 §1.1 (4,800 rows; 600 removed; 48 added; 128 rows per step)

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
                          "classifier", "c0"})
RECIPE_G: dict[str, str | None] = {"olmo2-7b": None, "llama31-8b": None}     # the recipe-G reference's config_sha256
#                                           (references come before block A; the measured G configs stay in CONFIGS)
RECIPE_BQI: dict[str, str | None] = {"olmo2-7b": None, "llama31-8b": None}   # B+Qi's config_sha256 (engine Y; the
#                                           re-verifier's D1: KCR:128 "B+Qi refused until measured")
BQI_KINDS = frozenset({"ref_train_bqi"})  # the kinds that run under RECIPE_BQI only (A1's pattern, as S78_KINDS)
PINS: dict[str, dict] = {"RECIPE_S": RECIPE_S, "RECIPE_G": RECIPE_G, "RECIPE_BQI": RECIPE_BQI}   # name -> per family
PINNED_RECIPE_KINDS = {**{k: "RECIPE_S" for k in S78_KINDS}, **{k: "RECIPE_BQI" for k in BQI_KINDS}}
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
# the first 16 hex equal P78:48-57's); "training_identity" is each family's (P78 §2.3 condition 2; M: the fixture's
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
                        "complete_sha256": "632fa4bd0a8f3b1b9e89670ce3fb0fd8c6fdb77432a458cd9edc213156e614c9"},
            1101: {"path": "tmp/family-probe-sp-olmo2-7b-b-a0/retrieved/sp-olmo2-7b-b2-1101/tree/round1/1101-a0-e1-a1",
                   "complete_sha256": "4a6d9ebc6636de57d52ec1b9cc1cd82afb1bdbfbf2a70e3f9884d3e9404d6dfc"},
            1102: {"path": "tmp/family-probe-sp-olmo2-7b-b-seed1102/retrieved/sp-olmo2-7b-1102/tree/round1/1102-a0-e1-a1",
                   "complete_sha256": "43e8412dc7ef8d3eb017340a788e08041623bce8b3896a750d6cc50e10e282c4"},
            1103: {"path": "tmp/family-probe-sp-olmo2-7b-b-seed1103/retrieved/sp-olmo2-7b-1103/tree/round1/1103-a0-e1-a1",
                   "complete_sha256": "4b5bd06dede08dc14f3ab5de201b7618ada94a0515896ed23c04b3af7ca44fa0"}},
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
                        "complete_sha256": "651f7f6de6721b414aebff7fee831e763e2d6f247f48f397ff550fc5353e4afa"},
            1101: {"path": "tmp/family-probe-sp-llama31-8b-b5e5-1101/retrieved/sp-llama31-8b-b5e5-1101/tree/round1/1101-a0-e1-a1",
                   "complete_sha256": "21427715565fb394220a068c8991b8f6819c4773ccf82b0cd7c35fe3788bc22a"},
            1102: {"path": "tmp/family-probe-sp-llama31-8b-b5e5-seed1102/retrieved/sp-llama31-8b-b5e5-1102/tree/round1/1102-a0-e1-a1",
                   "complete_sha256": "b0c99f7b97e6e76355383644ee50f9cbef33c25e09585a9a0d030712d4aa75d9"}},
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
MEASURED_KINDS = ("arm", "a0_arm", "evalonly")
# KD6: every other kind runs alone on a single-job pod with an explicit E cap until it is measured. Each entry gives
# the E upper's formula inputs and its basis; e_upper_s() turns them into seconds, e_cap_hours() into the pod's cap.
SIZE_FACTOR_1B_TO_78B = 2.3               # E: a 7-8B job is 1.9x (OLMo) to 2.3x (Llama) a 1B job (RP:43 via the plan §4)
WIDE_CAP_FACTOR = 1.5                     # R: the stage-1 kit's DIAG_UPPER_FACTOR (Gate B's [D13]; untimed kinds)
STATE_WRITE_S = 300.0                     # E: one adapter + optimizer + RNG state of about 1.9 GB written and fsynced
REF_FORWARD_SHARE = 0.5                   # R: stage1_rules.py REF_FORWARD_SHARE (B+Qi's reference forward; I, unmeasured)
Y_ENGINE_FACTOR = 2.0                     # E: engine Y has no 7-8B timing; its training term is doubled until KD9
STAGE1_1B_ESTIMATES_S = {"rep_pass": 3600.0, "untuned_answers": 7560.0, "l1_scan": 3600.0, "classifier": 2012.0,
                         "c0": 2400.0, "anchor": 900.0, "safe_lora_hash": 600.0, "safe_lora_transform": 88.02}
#                                           R: runkit/stage1-olmo/stage1_rules.py:87 DIAG_ESTIMATE_S (rep_pass 3,600 s,
#                                           the 1 h estimate at 1B), C0_S, ANCHOR_UPPER_S, SAFE_LORA_*
A1_PASS_CAP_H_MAX = 16.5                  # KD6, PP8: A1's attributes pass (a1_pass) at RP:43's 6-11 h is a 16.5 h cap at most
S_POOL_CHUNKS = 16                        # R: PR4 S4 row via ruling 12: 512 prompts in 32-prompt chunks
S3_POOL_ITEMS = 861                       # R: scripts/scale78b/settings/pins_78b.json shared.sealed_lists_1b.s3_safe.items
#                                           (the untuned pass's S3 call answers every prompt of the s3_safe pool; PP2)
O_EXT_PROMPTS = 600                       # R: stage1_rules.py O_ONLY_FACTOR: the 500-prompt bank plus the dev 100
E_KINDS = ("untuned_answers", "o_only", "o_only_with_regenerate", "anchor", "rep_pass", "a1_pass",
           "l1_scan", "classifier", "c0", "retrain", "ref_train_bqi", "safe_lora", "ref_eval")
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
}
COUNTED_KINDS = frozenset({"arm", "a0_arm", "evalonly", "c0", "retrain", "ref_train_bqi", "o_only_with_regenerate"})
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
    if ENGINE_Y is not None and engine_sha256 == ENGINE_Y:
        return kind in E_KINDS or Y_MEASURED is True
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
               bank: dict) -> None:
    """KCR §4 and KCR:147, the pod's key check (before the pod): the kind must be known; the recipe must be on the
    family's allow-list (measured kinds and the other E kinds), or recipe S_78 for the kinds that need it (S78_KINDS,
    through recipe_s_or_refuse); the engine must be one with a measured basis (X); the GPU the measured one; the
    prepared manifest the family's; the evaluation bank exactly BANK (A-V3)."""
    family_of(family)
    check_kind(kind)
    if kind in S78_KINDS:
        if recipe_sha256 != recipe_s_or_refuse(family):
            raise Refused(f"{kind} runs under recipe S_78 only; recipe {str(recipe_sha256)[:12]}... is not {family}'s S_78")
    elif kind in BQI_KINDS:
        if recipe_sha256 != recipe_bqi_or_refuse(family):
            raise Refused(f"{kind} runs under RECIPE_BQI only; recipe {str(recipe_sha256)[:12]}... is not {family}'s B+Qi")
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


def upper_m_of(c: dict, steps: int | None, kind: str = "arm", padded_tokens_per_step: float | None = None) -> float:
    """The measured physical upper bound of one job (KCR §4) from a constants block: training + all-capped
    generation + the scoring allowance + the early stages + the time outside the stages. ``evalonly`` has no
    training term."""
    if check_kind(kind) != "measured":
        raise Refused(f"{kind!r} is an E-capped kind: use e_upper_s")
    if kind == "evalonly":
        training = 0.0
    else:
        if type(steps) is not int or steps < 1:
            raise Refused("an arm needs its optimizer step count")
        training = steps * c["TRAIN_STEP_MAX_S"] * train_scale_of(c, padded_tokens_per_step)
    return training + gen_allcap_of(c) + SCORE_ALLCAP_S + c["EARLY_MAX_S"] + c["OUTSIDE_MAX_S"]


def upper_m_s(family: str, steps: int | None, kind: str = "arm", padded_tokens_per_step: float | None = None) -> float:
    return upper_m_of(family_of(family), steps, kind, padded_tokens_per_step)


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
                  preflight: dict | None = None, padded_tokens_per_step: float | None = None) -> float:
    """The start requirement (KCR §4): max(s_pod, s_obs) x upper_M + START_MARGIN_S, never below F_pre when the
    preflight is given. s_pod and s_obs below 1 count as 1 (a faster pod never lowers the bound)."""
    s = max(1.0, finite(s_pod), finite(s_obs))
    need = s * upper_m_s(family, steps, kind, padded_tokens_per_step) + START_MARGIN_S
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
               padded_tokens_per_step: float | None = None, n_points: int = 1) -> dict:
    """One plan job with its timing fields from this module's rules (the shape the stage-1 kit's plan uses). Refuses
    an unknown kind, an arm without its step count and, for every kind, ``n_points`` that is not a positive integer
    (D2: the E kinds refused it through e_upper_s; the measured kinds now refuse it here too)."""
    if type(n_points) is not int or n_points < 1:
        raise Refused("at least one evaluation point")
    group = check_kind(kind)
    if group == "measured":
        if kind == "a0_arm":
            steps = STEPS["a0"] if steps is None else steps
        if kind == "evalonly":
            steps = None
        up = upper_m_s(family, steps, kind, padded_tokens_per_step)
        measured = measured_upper_s(family, kind)
        unmeasured = False
    else:
        up = e_upper_s(family, kind, n_points)["upper_s"]
        measured = up                       # an E kind's spend upper is its E upper (nothing measured yet)
        unmeasured = True
    return {"kind": kind, "family": family, "arm": arm, "seed": seed, "steps": steps,
            "upper_s": up, "start_requirement_s": up + START_MARGIN_S, "measured_upper_s": measured,
            "spend_upper_s": measured, "counted": 1 if kind in COUNTED_KINDS else 0, "unmeasured": unmeasured,
            "n_points": n_points, "status": "planned"}


def arm_count(jobs: list[dict]) -> int:
    return sum(int(j.get("counted", 0)) for j in jobs)


def requirements(jobs: list[dict], s: float = 1.0, preflight: dict | None = None) -> list[float]:
    """Each job's start requirement on a pod at speed factor s (the plan uses s = 1)."""
    out = []
    for job in jobs:
        if job["unmeasured"]:
            out.append(job["start_requirement_s"])     # an E kind: its explicit cap window, no speed scaling
        else:
            out.append(requirement_s(job["family"], job["steps"], job["kind"], s, 1.0, preflight))
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


def arm_pod(family: str, steps_list: list[int], kinds: list[str] | None = None) -> list[dict]:
    """The job records of one pod of arms (each at its step count; kinds default to ``arm``)."""
    kinds = kinds or ["arm"] * len(steps_list)
    return [job_record(family, k, s) for k, s in zip(kinds, steps_list)]


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
                 + gen_allcap_s(family) + SCORE_ALLCAP_S + ends)
        basis = ("E: B+Qi (constrained SFT, engine Y): the a0 training term x (1 + 0.5) for the reference forward "
                 "(stage1_rules.py REF_FORWARD_SHARE, I) x 2 because engine Y is unmeasured at 7-8B, plus the evalonly "
                 "bound (M). Source: KCR:128 (B+Qi refused until measured); ruling 10.")
    elif kind == "safe_lora":
        upper = (WIDE_CAP_FACTOR * (train38 + 3 * STATE_WRITE_S + size * STAGE1_1B_ESTIMATES_S["safe_lora_hash"]
                                    + size * STAGE1_1B_ESTIMATES_S["safe_lora_transform"])
                 + n_points * evalonly_upper_s(family))
        basis = ("E: Safe LoRA: a regenerate's training (M) and states (E), the hash of about 15-16 GB of weights and "
                 "the V/V' check (the 1B 600 s x 2.3), the CPU transform (the 1B 88 s x 2.3), all x 1.5; plus one "
                 "evalonly bound (M) per evaluation point. Source: stage1_rules.py J17.")
    elif kind == "ref_eval":
        upper = WIDE_CAP_FACTOR * (train38 + 3 * STATE_WRITE_S + 300.0) + n_points * evalonly_upper_s(family)
        basis = ("E: the evaluation-only references (adapter scaling, the safety prompt): a regenerate's training (M) "
                 "and states (E) when the state is not on the pod, 300 s of adapter scaling (E), x 1.5; plus one "
                 "evalonly bound (M) per point. Source: stage1_rules.py J16, REF_EVAL_SCALES.")
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
    if job["kind"] in S78_KINDS:
        recipe_s_or_refuse(family)
    if job["kind"] in BQI_KINDS:
        recipe_bqi_or_refuse(family)                   # D1: B+Qi refuses until its config is pinned (KCR:128)
    if job["unmeasured"]:
        need = job["start_requirement_s"]
    else:
        need = requirement_s(family, job["steps"], job["kind"], s_pod, s_obs, fields)
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
            "retrain", "a1_pass")
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
OEXT_INPUTS = ("oext_bank", "oext_record")
OEXT_UNIT_SCRIPT = "scripts/stage1_s1/oext_unit.py"      # the stage-1 kit's O-ext unit runner (R: its job runner J3)
C0_SCRIPT = "scripts/stage1_s1/lean_eval_job.py"         # B17's lean job (R: the stage-1 job runner J11)
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
    "ENGINE_Y": "addendum A13: the lead fills ENGINE_Y by a recorded step when the Y retrain is packed",
}
# What each kind needs filled (A13's pattern). The retrain on engine Y also needs ENGINE_Y (sc_needed_pins).
SC_KIND_PINS = {
    "anchor": (), "untuned_answers": (),
    "o_only": ("OEXT_78B",), "o_only_with_regenerate": ("OEXT_78B",), "c0": ("OEXT_78B", "C0_SOURCE"),
    "l1_scan": ("ANCHOR_BANK",), "classifier": ("RECIPE_S", "ANCHOR_BANK"),
    "rep_pass": ("RECIPE_S", "ANCHOR_BANK", "S3_ORIG_POOL"), "retrain": ("RECIPE_S",),
    "a1_pass": ("RECIPE_S", "ANCHOR_BANK", "RETRAIN_UNIT"),
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


def oext_form_problem(oext) -> str | None:
    """Why ``oext`` is not OEXT_78B's documented form, or None: exactly {"files", "inputs"}; files a non-empty
    {plain relative path under scripts/: SHA-256}; inputs exactly {oext_bank: SHA-256, oext_record: SHA-256}."""
    if not isinstance(oext, dict) or set(oext) != {"files", "inputs"}:
        return "its keys are not exactly files and inputs"
    files, inputs = oext["files"], oext["inputs"]
    if not isinstance(files, dict) or not files:
        return "files is not a non-empty mapping"
    for path, digest in files.items():
        if not (isinstance(path, str) and path.startswith("scripts/") and "\\" not in path
                and all(part not in ("", ".", "..") for part in path.split("/"))):
            return f"files names {path!r}, not a plain relative path under scripts/"
        if not (isinstance(digest, str) and CONFIG_SHA256.match(digest)):
            return f"files[{path!r}] is not a SHA-256"
    if not isinstance(inputs, dict) or set(inputs) != set(OEXT_INPUTS):
        return f"inputs does not hold exactly {list(OEXT_INPUTS)}"
    if not all(isinstance(v, str) and CONFIG_SHA256.match(v) for v in inputs.values()):
        return "an input is not a SHA-256"
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
    c0 = C0_SOURCE[family]
    if c0 is not None and not (isinstance(c0, dict) and set(c0) == {"complete_sha256", "e1_fingerprint"}
                               and all(isinstance(v, str) and CONFIG_SHA256.match(v) for v in c0.values())):
        raise Refused(f"C0_SOURCE[{family!r}] is not a {{complete_sha256, e1_fingerprint}} record")
    return {"RECIPE_S": kit, "RECIPE_S_PATH": rs.get("path") if kit is not None else None,
            "ANCHOR_BANK": _hex_or_none(fam.get("anchor_bank_sha256"), f"pins_78b.json {family} anchor_bank_sha256"),
            "S3_ORIG_POOL": _hex_or_none(untuned.get("s3_orig_pool_sha256"),
                                         f"pins_78b.json {family} untuned_pass.s3_orig_pool_sha256"),
            "RETRAIN_UNIT": _hex_or_none(a1.get("retrain_complete_sha256"),
                                         f"pins_78b.json {family} a1_attributes_unit.retrain_complete_sha256"),
            "OEXT_78B": oext, "C0_SOURCE": c0,
            "ENGINE_Y": ENGINE_Y}


def sc_needed_pins(kind: str, engine: str) -> tuple:
    """The pins a scorer-block job needs: SC_KIND_PINS, plus ENGINE_Y for a job on engine Y."""
    if kind not in SC_KINDS:
        raise Refused(f"{kind!r} is not a kind of the scorer block ({', '.join(SC_KINDS)})")
    return SC_KIND_PINS[kind] + (("ENGINE_Y",) if engine == "Y" else ())


def sc_missing_pins(family: str, kind: str, engine: str, pins78: dict) -> list[tuple[str, str]]:
    """(pin, the event that fills it) of every pin the job needs that is still null."""
    values = sc_pin_values(family, pins78)
    return [(p, SC_PIN_EVENTS[p]) for p in sc_needed_pins(kind, engine) if values[p] is None]


def sc_pins_or_refuse(family: str, kind: str, engine: str, pins78: dict) -> dict:
    """The pin values, or Refused naming each null pin the job needs and its event (A13: the pod does not run)."""
    missing = sc_missing_pins(family, kind, engine, pins78)
    if missing:
        raise Refused(f"{kind} for {family}: {len(missing)} pin(s) it needs are null (addendum A13): "
                      + "; ".join(f"{p} waits for {event}" for p, event in missing))
    return sc_pin_values(family, pins78)


def sc_order_problem(kind: str, complete_kinds) -> str | None:
    """A2's order: why ``kind`` cannot be planned yet (the kinds that must be recorded complete before it), or None."""
    if kind not in SC_KINDS:
        return f"{kind!r} is not a kind of the scorer block"
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
                                   "SEALED_SETS": SEALED_SETS}}, indent=1, sort_keys=True))
        return 0
    print(__doc__.split("\n\n")[0])
    print("commands: golden | block0 | e-caps | kit")
    return 2


if __name__ == "__main__":
    sys.exit(main())
