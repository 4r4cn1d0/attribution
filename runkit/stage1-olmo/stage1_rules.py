"""The stage-1 kit's rules (B15; brief notes/b15-brief.md §3-§5, §8 with the lead's §8 defaults (addendum §17);
stdlib only). Copied from runkit/gate-b-olmo/gateb_rules.py: every Gate B function and public name is kept (the
Gate-B-only values stay in their own block, unused by stage 1), and the stage-1 job kinds J1-J18, the blocks, the
seed and arm tables (REV4 §1.2-§1.3), the engines X and Y, the stage-1 pins and the interleaving deal (§8 Q3) are
added. This module runs on the Mac (plan_tool, seal, launch, host, budget, finisher) and on the pod (the job runner
imports it), so the per-job gate, the caps and the money rules are one implementation.

Per job (brief §3; "E" = an estimate, "R" = read in a source, "I" = an inference; every kind not timed on CUDA carries
``unmeasured``): ``upper_s`` and ``measured_upper_s`` come from ``upper_s()`` and ``measured_upper()``, by kind, steps,
the W1-18 cap branch ("full" until W1-18's branch record exists, REV4 §6.3) and the number of evaluation-only points.
The O-ext term O500 (the 500-prompt bank's pass) is 1,517 s under Branch full (E: 0.517 FRE x 2,934 s; REV4 §7.3,
addendum §12 point 2) and 1,024 s under Branch 128 (E (I): 1,517 x 27/40, the largest Branch-128 to Branch-full ratio
of REV4 §10.5's O-ext ranges; UNVERIFIED: the first pod's preflight measures it and the per-job gate uses max(plan,
projection)). ``start_requirement_s`` = upper_s + 1,800. The cap (B4, unchanged): the largest, over a host's jobs k,
of 42 min + the measured uppers of the jobs before k + job k's start requirement, rounded up to 0.25 h; the guard needs
$6 + cap x $1.85. The funding need (B4, unchanged; brief §5.2): the base need = the largest, over a path's launches k,
of the upper spend of the launches before k + $6 + $1.85 x the summed caps of launch k; the need = 1.25 x the base
(rounded to the cent first, [D20]). A pod's upper spend is (42 min + its jobs' spend uppers) x $1.79; a job's spend
upper is its measured upper.

Pods (§8 Q3, Q5): at most MAX_ARMS_PER_POD = 4 counted jobs per pod; counted are the training arms (arm, a0_arm,
ref_train, cert_c1, cert_c2, cert_c3, c0) and each evaluation-only point (b10_certify's evaluations, ref_eval's and
safe_lora's points); regenerations, O-only passes, W1-18 and the diagnostics count 0. A block's training-arm runs are
dealt by ``deal``: arm-major (ARM_ORDER), seed-minor, ceil(n / 4) pods, run i to pod i mod P (an outcome-free rule
fixed before launch). An arm has at most 3 runs in a block, so with P >= 3 pods no pod holds one arm twice; a deal
that would refuses. (The brief's example order, seed-major, puts A1 at 1102 and at 1103 on one pod under plan B's
block A: 14 runs, 4 pods, 4 runs per seed at 1102-1103.)
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
import json
import math

# ===== money and timing constants (Gate B's, unchanged; brief §5.1) =====
POD_OVERHEAD_S = 42 * 60                  # per pod (B4; [D9] B-2)
START_MARGIN_S = 1800                     # a job starts only with its upper + 30 min left
OVERHEAD_FLOOR_S = 1000                   # scripts/cuda_preflight_family.py:77
SAFETY_MARGIN_S = 900                     # scripts/cuda_preflight_family.py:82
FIXTURE_STEPS = 38                        # the fixture's training_s covers 38 steps
CONTINGENCY_FACTOR = 1.25                 # [D22]; brief §5.1 (new stage-1 cost lines)
CAP_STEP_S = 0.25 * 3600                  # caps are rounded up to 0.25 h
MAX_PRICE_USD = 10.0                      # [D20] as amended: the create-time limit
PLANNING_PRICE_USD = 1.85                 # [D20]: the guard's planning $/h
RATE_USD = 1.79                           # [D20]: the A100's measured $/h
RESERVE_USD = 6.0                         # the user's 5 Oct rule
# (E) the user's decision of 25 Oct (GI VI chat, FOCUS 8d3d505: "remove the guard its not needed I can control it
# better"): a recorded record of this kind (plan_tool record-guard-off) makes launch.py and host.py extend-cap go past
# the live-balance guard's refusal (running pods and the new pod at full caps plus RESERVE_USD); budget.py check still
# reads and logs the live balance and must succeed. MAX_PRICE_USD, the in-pod stop timer at the cap and
# stop-never-delete are unchanged. Without the record the guard is exactly as before.
GUARD_OFF_KIND = "stage1 user decision: budget guard off"
GUARD_OFF_KEYS = ("kind", "user_words", "utc", "recorded_by")
GUARD_REFUSED_EXIT = 3                    # budget.py check's exit when the guard refuses (any other non-zero: no read)
MAX_ARMS_PER_POD = 4                      # LN-27, LS-12 (a); §8 Q5: counted jobs per pod
MAX_COUNTED_PER_POD = MAX_ARMS_PER_POD
SETUPTOOLS_PIN = "78.1.0"                 # [D5]
PIP_PIN = None                            # [D5]
# ===== stage-1 timing constants (brief §3, §5.4; E unless marked) =====
FRE_S = 2934                              # 1 FRE (REV4 §7.3, fixed at W1-P; R)
O500_S = {"full": 1517.0,                 # E: 0.517 FRE at the full cap (REV4 §7.3; addendum §12 point 2; brief §3)
          "128": 1024.0}                  # E (I): 1,517 x 27/40 (REV4 §10.5's O-ext ranges); UNVERIFIED
BRANCHES = ("full", "128")
BRANCH_DEFAULT = "full"                   # every plan and cost uses Branch full until W1-18's record (REV4 §6.3)
ARM_MEASURED_S = 52 * 60                  # Gate B's frozen arm measured upper (R: gateb_rules)
REGEN_MEASURED_S = 0.15 * 3600            # Gate B's retrain measured upper (R; 0.077 h measured for a0@1101)
W1_18_UPPER_S = 0.5 * 3600                # E (brief J1): 0.5 h upper; unmeasured
O_ONLY_FACTOR = 1.25                      # E (brief J3): O500 plus the dev 100 = about 1.25 x O500
TRANSFER_S = 1408.0                       # E (brief J4): about $0.7 at $1.79/h = 0.391 h; Branch 128 only
DIAG_ESTIMATE_S = {"rep_pass": 3600.0,    # I: about 6,000 unbatched forwards; unmeasured (brief J5)
                   "untuned_answers": 7560.0,   # E (brief J6): 2,100 answers x 3.6 s
                   "l1_scan": 3600.0,     # I: short greedy runs; unmeasured (brief J7)
                   "classifier": 2012.0}  # E (brief J8): about $1 at $1.79/h = 0.559 h
DIAG_UPPER_FACTOR = 1.5                   # Gate B's diagnostics factor ([D13]); wide caps (brief §2)
C0_S = 2400.0                             # E (addendum §11 point 13; REV4 §7.3): c0 at the full cap; unmeasured
REF_FORWARD_SHARE = 0.5                   # I: B+Qi's reference forward per micro-batch; unmeasured (brief J13)
CERT_C3_S = 0.5 * 3600                    # I: "small" (brief J14); unmeasured
# LN-15e's re-score (round 3b; addendum §17 Q19, §25 point 1; REV4 §9.3, §14.2): Gate B's retrain + diagnostics kinds.
# The retrain is Gate B's retrain rule (measured upper 0.15 h, as REGEN_MEASURED_S). The re-score is the engine's
# attributes step of Gate B's diagnostics job: R (FOCUS 16 Oct 13:21 UTC, w0b-2) Gate B's whole diagnostics job, the
# attributes step plus both Gate C scripts, took 3.04 h against its frozen 2.0 h upper; the attributes step alone was
# never timed, so 3.04 h is taken as its measured upper (UNVERIFIED; unmeasured) and its upper is the diagnostics
# factor x 3.04 h (Gate B's rule, [D13]; the brief's wide-cap rule for untimed diagnostics, §2). REV4 prices LN-15e
# at $12-15 of spend ($15-19 with the 1.25 contingency): 2 x (42 min + 0.15 h + 3.04 h) x $1.79 = $13.93 is inside it.
RESCORE_SEEDS = (1102, 1103)              # REV4 LN-15e: a0 retrains at 1102 and 1103 (q and e1)
RESCORE_MEASURED_S = 3.04 * 3600          # R (the whole Gate B diagnostics job; an upper for attributes alone)
RESCORE_CHECKPOINTS = ("q", "e1")         # REV4 LN-15e; the A1 contract's [q, e1] (write_score_edit.json a1.rule)
EVAL_ONLY_FRE = 0.93                      # R: REV4 §10.4, one evaluation-only state
EVAL_ONLY_S = EVAL_ONLY_FRE * FRE_S       # 2,728.62 s
SAFE_LORA_TRANSFORM_S = 0.03 * FRE_S      # R: REV4 §10.4 (< 0.03 FRE, CPU)
SAFE_LORA_HASH_S = 600.0                  # I: hashing about 9 GB and the V/V' check (brief J17); unmeasured
# ===== end of the timing constants =====

# ===== Gate-B-only values (kept so that every Gate B public name exists; stage 1 does not use them) =====
DIAGNOSTICS_UPPER_S = 2.0 * 3600
DIAGNOSTICS_UPPER_FACTOR = 1.5
ANCHOR_UPPER_S = 0.25 * 3600
WAVE0A_DRAWS = (1, 2, 3)
EXTENSION_DRAWS = (4, 5)
UNIT_SEED = 1101
RETRAIN_SEED = 1101
WAVE2_SEEDS = (1102, 1103)
EXTENSION_SEEDS = (1104, 1105)
UNITS = 8
WORST_PATH_AFTER_WAVE1 = (("2", 8), ("ext", 6), ("lc", 4))
GRANITE_ON_POD = True
GRANITE_POD_AFTER = ("2", "ext")
ANCHOR_PROMPTS_PIN = {"path": "tmp/gate-b-anchors/anchor_prompts.json",
                      "sha256": "78467c97c40e7e9fd39e8061219517853e7292a25881700da5e9115604117b97"}
PINNED_SCRIPTS = {}                       # Gate B's packed scripts; the stage-1 scripts are STAGE1_PINS below
STAGE_SCRIPTS = {}
# ===== end of the Gate-B-only values =====

# the judge launcher's cap rule (unchanged; brief J19)
GRANITE_SETUP_UPPER_S = 1800
GRANITE_S_PER_ANSWER = 0.5
GRANITE_MARGIN_S = 900
GRANITE_CAP_MIN_H, GRANITE_CAP_MAX_H = 1.0, 6.0
GRANITE_GREEDY_PER_ARM = 200
GRANITE_KNOWN_ANSWERS = 200
# HarmBench judge launches (round 3a; brief J19; Gate B's launch H, notes/gateb-judge-readiness.md: 15 units x (600
# sampled + 200 greedy) = 12,000 answers, cap 2.0 h; R: scripts/gate_b_mac_judges/pod/judge_pod.py cap_hours_for with
# UPPER_S_PER_ITEM 0.25, SETUP_UPPER_S 1,800, MARGIN_S 900, at least 1 h, above 6 h refused; no known-answer gate)
HARMBENCH_S_PER_ANSWER = 0.25             # judge_pod.UPPER_S_PER_ITEM (E: 2-4 x the A100 estimate per answer)
HARMBENCH_ANSWERS_PER_ARM = 800           # --expect-greedy 200 --expect-sampled 600 per unit
JUDGES = ("harmbench", "granite")         # block A's two judge launches (REV4 §10.6 step 9)
# ----- the judge files and the judge-completion record (round 30; addendum §30 gaps 1, 2 and 5; the lead's R2-R3) -----
# A block's judge files are Gate B's write_files.py output under judges/BLOCK/: one file per (judge, unit), named
# JUDGE--HOST--UNIT--<12 hex of COMPLETE.json SHA-256>.json, and judge-files-index.json (Gate B's index, version 2).
# These values are Gate B's (scripts/gate_b_mac_judges/write_files.py FILE_NAME, INDEX, INDEX_KIND, INDEX_VERSION,
# ENTRY_KEYS; common.HARMBENCH/GRANITE names; pod/podhost.py TAG_RE); a test checks each against Gate B's file.
JUDGE_INDEX = "judge-files-index.json"
JUDGE_INDEX_KIND, JUDGE_INDEX_VERSION = "gate-b judge files index", 2
JUDGE_INDEX_ENTRY_KEYS = ("complete_sha256", "completed_utc", "file", "host", "judge", "arm", "seed", "sha256",
                          "target", "unit")
JUDGE_FILE_PATTERN = r"^(granite|harmbench)--.+--[0-9a-f]{12}\.json$"
JUDGE_NAMES = {"harmbench": "cais/HarmBench-Mistral-7b-val-cls", "granite": "granite-guardian-3.3-8b"}
JUDGE_TAG_PATTERN = r"^[a-z0-9][a-z0-9-]{0,38}[a-z0-9]$"
# Round 33 (GB5; addendum §37 point 5): the judges run on this GPU, as block A's did (Gate B's pod/podhost.py GPU, the
# create request's only gpuTypeIds entry; a test compares them). record-judges checks each launch result's
# verification.gpu (the fetched run record's environment GPU name) against it.
JUDGE_GPU = "NVIDIA A100-SXM4-80GB"
# R2: the lead's judge-completion record, plan_tool.py record-judges BLOCK FILE --sha256 H. Exactly these keys; no
# value is an HB, Granite, yes, unparsed or harm count ("judged" is the number of answers judged).
JUDGE_RECORD_KIND = "stage1 judge completion record"
JUDGE_RECORD_KEYS = ("kind", "block", "judges", "index_sha256", "utc", "recorded_by")
JUDGE_ENTRY_KEYS = {"harmbench": ("tag", "result_sha256", "run_record_sha256", "bundle_sha256", "exit", "judged",
                                  "complete"),
                    "granite": ("tag", "result_sha256", "run_record_sha256", "bundle_sha256", "exit", "judged",
                                "complete", "known_answer_passed")}
# R3: the units a block's judge files must cover. plan.json records the COMPLETE.json SHA-256 of every complete job of
# these kinds (the block tables' arm runs; B10's evaluation units, one per point, from JOB-DONE.json's units list),
# plus the block's pinned re-judged units below. Round 31 (K2; addendum §32 point 1): a trained reference (ref_train,
# recipe G or B+Qi) is judged too: its unit is the engine's calibrate unit round1/<seed>-a0-e1-a<n> (job.json kind
# run-one, evaluate_bank dev, target_checkpoint e1, arm a0: the engine's arm; the kit's arm is the recipe), which
# Gate B's Mac enumeration and pod-side bundle._verify_unit accept unchanged. Block B holds up to three such units per
# seed (a0_arm at 1105-1107, G and B+Qi at 1102-1107), and Gate B's write_files.py allows one judge file per (judge,
# arm, seed, target) in one folder, so judge_units_stage1.py write-files labels a ref_train unit's judge file
# "ref-<recipe>" (ref_train_labels, from plan.json).
JUDGED_RUN_KINDS = ("arm", "a0_arm", "ref_train")
JUDGED_B10_KINDS = ("ref_eval", "safe_lora")
B10_UNIT_KINDS = ("b10_certify", "ref_eval", "safe_lora")   # JOB-DONE.json lists each of their units (record-done keeps it)
# Block A's 7 re-judged units (§17 Q14, §25 point 2; plan_tool.REJUDGED_UNITS counts them): the 6 reused a0/R SOURCE
# units (.ai/inputs/stage1-post-w1-20261023/block-a/reuse/reuse_spec.json jobs[0..5].source; J2 is train-only, so the
# LN-12 regenerations have no answers) and theta0's untuned dev-bank unit (scripts/stage1/settings/
# limits_overrefusal_checks.json "untuned"; scripts/stage1_s1/settings/eval_adapter.json untuned_unit). M (round 30,
# 27 Oct 2026 10:27 UTC): shasum -a 256 of each COMPLETE.json and job.json on disk equals these pins (no answer file
# opened). Paths are relative to the repository. Round 31 (K2; addendum §32 point 2): block B has no re-judged unit by
# rule (Gate B called no extension, so R_4 and R_5 are trained, not reused; every block-B unit is new): its entry is
# empty, explicitly.
REJUDGED_PINS = {"B": (), "A": (
    {"name": "a0 1101 (Gate A)", "arm": "a0", "seed": 1101, "target": "e1",
     "path": "tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1",
     "complete_sha256": "8f0fa83a42ccc5edc54a5ee26ed63f49448c36d30adbd64e28b655678afee4c9",
     "job_sha256": "3e60568ac11e32f3f429aa2606bc38c9b881456fd262a120e526ccb189022402"},
    {"name": "a0 1102 (Gate A)", "arm": "a0", "seed": 1102, "target": "e1",
     "path": "tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1",
     "complete_sha256": "857f78bc0f49cc8a4902fbb6211f463daa7c7f44086257c4d752409a30ba0b25",
     "job_sha256": "de65ca1936a10c199de46e764a948268b03367c586c09747381850059064083c"},
    {"name": "a0 1103 (Gate A)", "arm": "a0", "seed": 1103, "target": "e1",
     "path": "tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1",
     "complete_sha256": "7be58eaa9c5be7b8f94668109efd6aae075b1d001e0d2b1fb8be814556899cbd",
     "job_sha256": "895f8bd2a66e20df2256b43d1e71a263da237a1cb3ea498cd439086aef5ae293"},
    {"name": "R 1101 (wave 0a, R_1)", "arm": "edit-f7d7eb86cb58f7a5e7e1408973a13531f74845e066d7328d6e726ecdd442ffdd",
     "seed": 1101, "target": "e1",
     "path": "tmp/gate-b-olmo/retrieved/w0a-1/tree/round1/"
             "1101-edit-f7d7eb86cb58f7a5e7e1408973a13531f74845e066d7328d6e726ecdd442ffdd-e1-a1",
     "complete_sha256": "391d067ca6569a04721b059da2bca2c7ee5d109de560362895198a0d40ac5f0f",
     "job_sha256": "6f833fc3a4181b2aa8cabcdc54689dea4e159c98e8b9ca73db063751806dc01a"},
    {"name": "R 1102 (wave 0a, R_2)", "arm": "edit-913b73606ff64c104751e3f86bd3b69838a27686720a92858c08f4cf087d8060",
     "seed": 1102, "target": "e1",
     "path": "tmp/gate-b-olmo/retrieved/w0a-1/tree/round1/"
             "1102-edit-913b73606ff64c104751e3f86bd3b69838a27686720a92858c08f4cf087d8060-e1-a1",
     "complete_sha256": "1cef324df66f0b46a11ce4d5255da1c5c7287ebbe9d8bc5cae7132996afb12b6",
     "job_sha256": "06797c5341b73f82ac622bae36c259dfa485e889cd575b17121303180e1e4daf"},
    {"name": "R 1103 (wave 0a, R_3)", "arm": "edit-cd8d3328c48957ed0a164a8775ca2695a3d77d51865fd32c2ee53aded939502b",
     "seed": 1103, "target": "e1",
     "path": "tmp/gate-b-olmo/retrieved/w0a-1/tree/round1/"
             "1103-edit-cd8d3328c48957ed0a164a8775ca2695a3d77d51865fd32c2ee53aded939502b-e1-a1",
     "complete_sha256": "d34e33f2e3b90b562a1b21da3fabc3e672842b7b2cbfe2eadae754601155692c",
     "job_sha256": "3c01279f6fd3168f38cd4478668f0aaec8bfd6ec78239d72e1860629535dabe8"},
    {"name": "theta0 (untuned, Gate A)", "arm": "a0", "seed": 1101, "target": "init",
     "path": "tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1",
     "complete_sha256": "b5083ce9d9f26efe92f9872fdbf9376a521a5d99d1b70cc2bd460987cdcc9474",
     "job_sha256": "f3b8c1864aaacf34738b34ff6c26cc8f51677e7eb5a6a9445818692d5365a582"},
)}

# ----- seeds, arms and blocks (REV4 §1.2-§1.3) -----------------------------------------------------------------
DEV_SEEDS = (1101, 2099)                  # the development seed namespace
R_SEED_BASE = 1100                        # R_d runs at seed 1100 + d
A0_SEEDS = tuple(range(1101, 1108))       # a0 at 1101-1107 under both plans (LN-02)
REUSED_SEEDS = (1101, 1102, 1103)         # a0 (Gate A) and R (wave 0a) units, reused
METHOD_SEEDS = {"A": (1102, 1103, 1104), "B": (1105, 1106, 1107), "C": (1108, 1109, 1110)}
STAGE1_SEEDS = tuple(range(1101, 1111))
ARM_ORDER = ("A1", "L1", "H1", "S1", "S3", "S4", "a0", "R")   # the deal's arm order (arm-major)
ARM_DOSE = {"A1": "remove", "L1": "remove", "H1": "remove", "R": "remove",
            "S1": "add", "S3": "add", "S4": "add", "a0": "none"}
DOSE_STEPS = {"remove": 33, "add": 38, "none": 38}             # R: REV4 §1.1 (4,800 rows; 600 removed; 48 added)
PLAN_ARMS = {"A": ("A1", "L1", "H1", "S1", "S3", "S4"), "B": ("A1", "H1", "S1", "S4")}   # method arms (LN-02)
SIGMA_PLAN_A_MAX_PP, SIGMA_PLAN_B_MAX_PP = 4.5, 6.0           # the blinded seed rule (REV4 §1.3)
GATEB_R_DRAWS = (1, 2, 3, 4, 5)           # R_d edits sealed in Gate B's MANIFEST (commit 10a2894)
PLAN_B_R_DRAWS_C = (8, 9, 10)             # plan B block C: R draws d = 8-10 (addendum §11 point 15)
# LW-32 reuses R_4/R_5 only if Gate B's extension made them. Gate B closed TOO CLOSE with no extension (FOCUS 23 Oct
# 04:31 and 05:26 UTC; addendum §19: build_reuse_spec units 6-7 stay null, "it did not"), so nothing is reusable.
ALLOWED_REUSE = frozenset()


def finite_number(value) -> bool:
    """A finite, non-boolean int or float. An int too large for a float (10**400) is not one: math.isfinite would
    raise OverflowError on it, so it is refused as a value instead (round-2 fix VG2-5)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def plan_code_for(sigma_pp: float) -> str:
    """The blinded seed rule: sigma <= 4.5 pp -> "A"; <= 6.0 -> "B"; above -> "none" (no stage 1)."""
    if not finite_number(sigma_pp) or sigma_pp < 0:
        raise ValueError("sigma must be a finite number of percentage points")
    return "A" if sigma_pp <= SIGMA_PLAN_A_MAX_PP else "B" if sigma_pp <= SIGMA_PLAN_B_MAX_PP else "none"


def verdict_sigma(doc) -> float:
    """Gate B's final pooled sigma from its verdict file (already checked by SHA-256): kind and phase must be the
    verdict's, and GATEB_VERDICT_FIELD must hold a finite number (no other field is read)."""
    if not isinstance(doc, dict) or any(doc.get(k) != v for k, v in GATEB_VERDICT_FIELDS.items()):
        raise ValueError("not Gate B's verdict reading (kind 'gate-b reading', phase 'verdict')")
    value = doc
    for key in GATEB_VERDICT_FIELD:
        if not isinstance(value, dict) or key not in value:
            raise ValueError("Gate B's verdict has no " + ".".join(GATEB_VERDICT_FIELD))
        value = value[key]
    if not finite_number(value):
        raise ValueError(".".join(GATEB_VERDICT_FIELD) + " is not a finite number")
    return float(value)


def c2_reading(lines) -> list[tuple[int, float]]:
    """(step, constrained.mean_weight.t2_5) of each record of C2's steps.jsonl; nothing else of a record is used.
    The steps must be exactly 1..38 (the engine's 1-based steps), each once, each value a finite number."""
    out = []
    for n, line in enumerate(lines, 1):
        if not str(line).strip():
            continue
        try:
            rec = json.loads(line)
            step, value = rec["step"], rec["constrained"]["mean_weight"]["t2_5"]
        except (ValueError, KeyError, TypeError):
            raise ValueError(f"steps.jsonl line {n}: no step or constrained.mean_weight.t2_5") from None
        if type(step) is not int or not finite_number(value):
            raise ValueError(f"steps.jsonl line {n}: the step or the statistic is not a number")
        out.append((step, float(value)))
    if sorted(s for s, _ in out) != list(range(1, C2_THRESHOLDS["steps"] + 1)):
        raise ValueError(f"C2's steps.jsonl must hold steps 1-{C2_THRESHOLDS['steps']}, each once")
    return sorted(out)


def c2_labels(reading: list[tuple[int, float]]) -> dict:
    """The binding check's labels (addendum §22 point 1): "binds" if the value is <= 0.50 at some step s <= 3;
    "equals recipe B by construction" if it is >= 0.90 at 20 or more of the 38 steps; both reported if both hold;
    "partly binding" if neither. Labels are training statistics, never outcomes, and never change the arm."""
    b, e = C2_THRESHOLDS["binds"], C2_THRESHOLDS["equals_recipe_b_by_construction"]
    binding = [s for s, v in reading if s <= b["step_at_most"] and v <= b["value_at_most"]]
    high = sum(1 for _, v in reading if v >= e["value_at_least"])
    labels = ([C2_LABELS[0]] if binding else []) + ([C2_LABELS[1]] if high >= e["steps_at_least"] else [])
    return {"statistic": C2_THRESHOLDS["statistic"], "labels": labels or [C2_LABELS[2]],
            "binds_at_steps": binding, "steps_at_or_above_0.90": high, "steps": len(reading),
            "arm_changed": False}


def block_runs(plan_code: str, block: str, reused: tuple = ()) -> list[tuple[str, int]]:
    """The new training-arm runs (arm, seed) of a block, seed-major and arm-minor (ARM_ORDER). ``reused`` names
    (arm, seed) units that Gate B's extension made and stage 1 reuses (R_4 at 1104, R_5 at 1105; LW-32).
    Plan A: block A = the six method arms at 1102-1104 + a0 and R at 1104 (20, or 19); block B = all eight arms at
    1105-1107 (24, or 23). Plan B: block A = A1, H1, S1, S4 at 1102-1104 + a0 and R at 1104 (14, or 13); block B = the
    same four at 1105-1107 + a0 and R at 1105-1107 (18, or 17); block C = A1, H1, S1, S4 and R at 1108-1110 (15)."""
    if plan_code not in PLAN_ARMS:
        raise ValueError(f"no stage-1 table for plan {plan_code!r}")
    if set(reused) - set(ALLOWED_REUSE):
        raise ValueError("no unit made by Gate B's extension can be reused: Gate B closed TOO CLOSE and called no "
                         "extension, so R_4 at 1104 and R_5 at 1105 are trained (LW-32; addendum §19)")
    methods = PLAN_ARMS[plan_code]
    if block == "A":
        runs = [(a, s) for s in METHOD_SEEDS["A"] for a in methods] + [("a0", 1104), ("R", 1104)]
    elif block == "B":
        runs = [(a, s) for s in METHOD_SEEDS["B"] for a in methods + ("a0", "R")]
    elif block == "C" and plan_code == "B":
        runs = [(a, s) for s in METHOD_SEEDS["C"] for a in methods + ("R",)]
    else:
        raise ValueError(f"plan {plan_code} has no block {block!r}")
    runs = [r for r in runs if r not in set(reused)]
    return sorted(runs, key=lambda r: (r[1], ARM_ORDER.index(r[0])))


def r_draw(seed: int) -> int:
    """R_d runs at seed 1100 + d."""
    return seed - R_SEED_BASE


# ----- engines, recipes and pins (brief §0; R unless marked) ---------------------------------------------------
ENGINES = {"X": "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892",
           "Y": "34bfd28879fdefc5d6605cb73a707d1edd2ec5d102b4b86c0026bc6ac36969f6"}
ENGINE_DEFAULT = "X"
YHASH_PIN = {"path": "backups/2026-10-22/engine-round-y-34bfd288.sha256",
             "sha256": "9baa5c79a7227b60c5276070144a858695a588d497163b7f92638f04c7435dca"}
REC = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json"
RECIPE_S = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json"
RECIPE_G = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-g-mb4-20261008.json"
RECIPE_BQI = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-bq-mb4-20261022.json"   # engine Y's tree only
RECIPE_PINS = {REC: "a47138f2f4fb032aa60addc59256c499b7a65a75c2541aba516adeed8f4b15b2",
               RECIPE_S: "464708c91cd4c297aedf556958893cf84efdeb59b727e5c086a053b81528daf0",
               RECIPE_G: "cb51e5a9431f5fd4963d521866072821cf0db3dff800cc5b34d79469579e9228",
               RECIPE_BQI: "3031aaaa8d3f44057c3d5fa9c0489170940b0bd3a7184365b3b32c9f436dfd1c"}
RECIPE_NAMES = {"S": RECIPE_S, "B": REC, "G": RECIPE_G, "bqi": RECIPE_BQI}
TRAINING_IDENTITY = "f46279e5830f477742189ef03c03ffc0ec86107ae060bb5ef9034ba47acabfac"   # R: B10H §3.1; eval_adapter
#                                         settings recipe.training_identity; Q4: recipe S's must equal it (plan_tool)
TRAINING_IDENTITY_RECIPES = ("S",)        # Q4: the recipe of every new edit arm, a0 arm and regeneration
# G3: Gate B's measurements --final output (code REPORTED; FOCUS 23 Oct 05:26 UTC "output 06a7020aede28df5..."; the file
# research/experiments/2026-10-16-gate-b-wave0-outputs/gate_b_measurements_final.json, M: shasum -a 256 23 Oct about 15:00
# UTC in the main checkout; the lead's commit 3e82f67, not checked by git here)
GATEB_FINAL_SHA256 = "06a7020aede28df5bf8a73740819c3453b483f02c61a148822c0c66c4798bd0f"
GATEB_FINAL_FIELDS = {"kind": "gate-b reading", "phase": "measurements"}   # and result.final true, result.code REPORTED
# addendum §11 point 1, fallback (c): when the shared O-ext function is not verified before S1, the lead records
# overrefusal_bank.status = dev100_recipe_cap; then no O-ext step runs (the engine's own dev-100 evaluation stands)
OEXT_FALLBACK_STATUS = "dev100_recipe_cap"
OEXT_ONLY_KINDS = ("o_only", "transfer_report")   # kinds that are nothing but an O-ext pass (refused under (c))
# G3, B15 round 2 (addendum §20 point 6): the plan-A/B record is derived, never typed. The kit reads Gate B's committed
# verdict file (M: shasum -a 256, 23 Oct 18:10 UTC) at one field and applies REV4 §1.3's frozen rule (plan_code_for).
GATEB_VERDICT = {"path": "research/experiments/2026-10-16-gate-b-wave0-outputs/gate_b_verdict_p5.json",
                 "sha256": "bec5f103a1c5164ce0d4364cdf3d46c5a66ad941cd2f81a47d381e948811d404"}
GATEB_VERDICT_FIELDS = {"kind": "gate-b reading", "phase": "verdict"}
GATEB_VERDICT_FIELD = ("result", "readings", "plain", "sigma_hat_pp")
PLAN_AB_RULE = "REV4 §1.3: sigma <= 4.5 pp plan A; 4.5 < sigma <= 6.0 pp plan B; sigma > 6.0 pp no stage 1"
# J5 and J8 under post-W1 deviation D-2 (addendum §19 point 3, §21): the D-2 wrappers, the filled pins file and REQ-8's
# record, each by SHA-256 (M: shasum -a 256 23 Oct 18:10 UTC; the pool hashes as REQ-8's record and the filled file give)
D2_REP_SCRIPT = "scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py"
D2_CLASSIFIER_SCRIPT = "scripts/stage1_s1/d2_pool_pins/d2_score_classifier.py"
D2_CODE = {"scripts/stage1_s1/d2_pool_pins/__init__.py": "5f4969b7d676282bf9335bf9cbef68ab6ca9d5e738bcd9ba53092715e68d7789",
           D2_REP_SCRIPT: "24d178fae6784c5d5b4518ac427d007ccfb7bbb95816d0483adf280a4d1fb087",
           D2_CLASSIFIER_SCRIPT: "e7507d1260b569c642592f65b84b9d3403ed469d5bfbb4038c43f08df950dd67",
           "scripts/stage1_s1/d2_pool_pins/fill_pins.py": "12e59f5f3b12f831909e1f4cf34f8d716e4410d287d1bfe5ae81e08334611107",
           "scripts/stage1_s1/d2_pool_pins/settings/d2_pool_pins.json":
               "d6fa043fea4482fa0293d1bc936cd5c77466f4fc6b0c8d56df458e6e2e7b3bd1",
           "scripts/stage1_s1/d2_pool_pins/settings/d2_score_classifier.json":
               "1ce071b41a161d56746e1bac83da8c48879e5fb00cedd5a6afc1c9c5367219ef"}
D2_POOL_PINS = {"path": ".ai/inputs/stage1-post-w1-20261023/pool-pins/representation_pools.filled.json",   # moved, 3b
                "sha256": "a33e96649385b6bc9bcdb35493228c716fb02fc610514c4fba98b23eba345d5e"}
D2_REQ8_RECORD = {"path": ".ai/inputs/stage1-commitments-20261016/plant/plant_record.json",
                  "sha256": "cc04b6634502406f4e2110e21ae0f1b6ecd0d1737f5dfbcf4a6b1320718be2cc"}
D2_POOLS = {"plant": "37739f40e476ff8bdecacdc47a806b36a0533b0f079919ab4d63d84832e67a59",
            "decoy": "d102b665b8f2fc538fdf08fb85020c1e8a1f8a1bf9265f999e55133d473f9db6"}
S_POOL_RECORD = {"path": ".ai/inputs/stage1-commitments-20261016/s-pool/s_pool_record.json",   # s3_safe's pool hash
                 "sha256": "bcca59ac0f8c15c354b9d9b124c1e17211c7e602800424f40292160934383c6f"}
D2_KINDS = ("rep_pass", "classifier")     # J5 and J8; the D-2 fallback record names the kinds it covers
# C2, the binding check (addendum §22 point 1, LQ21), recorded exactly before the certificate pod is planned
C2_THRESHOLDS = {
    "statistic": "constrained.mean_weight.t2_5", "file": "steps.jsonl", "steps": 38,
    "job": "cert_c2: B+Qi, seed 1101, to e1, training only",
    "binds": {"rule": "the value is <= 0.50 at some step s <= 3", "value_at_most": 0.5, "step_at_most": 3},
    "equals_recipe_b_by_construction": {"rule": "the value is >= 0.90 at 20 or more of the 38 steps",
                                        "value_at_least": 0.9, "steps_at_least": 20},
    "neither": "partly binding", "both": "both labels are reported",
    "labels_change_the_arm": False,
    "on_equals_recipe_b": "the lead writes a proposal to the user; B+Qi runs as registered unless the user decides "
                          "otherwise",
    "reference": "addendum §22 point 1 (2026-10-23T16:16 UTC)"}
C2_LABELS = ("binds", "equals recipe B by construction", "partly binding")
# C3 (addendum §22 point 2): the subsample file and its record from scripts/stage1_s1/c3_subsample/write_c3_subsample.py
C3_WRITER = {"script_sha256": "c31bdb1bd7e69010fd6dec0392cb2d440db5344337d0f778057d1332ff460026",
             "settings_sha256": "a8547e2dcd27cbbdbed48eef3cb636a4503a6f3d6101123080b26b9baa1cfc60"}
C3_RECORD_KIND = "stage1 c3 subsample record"
C3_ITEMS = 16
# round 3b: C3's writer record (moved unchanged to the post-W1 inputs folder; M: shasum -a 256 at main 3eaf968).
# record-c3 refuses a writer record other than this file by its SHA-256.
C3_RECORD = {"path": ".ai/inputs/stage1-post-w1-20261023/c3/c3_subsample_record.json",
             "sha256": "1a24c7a39eb45fd94527806b16edd358975169661ed2a079f8b4c1d8793dd92e"}
# engine Y is pinned at 34bfd288 (addendum §23: F5 met by X's own check; c641c84b not adopted); its frozen tree
Y_TREE_DEFAULT = "tmp/engine-y-34bfd288"
MAN_PATH = ".ai/inputs/gate-b-sealed-20261008/out/MANIFEST.json"          # Gate B's sealed MANIFEST (R_1-R_5)
MAN_SHA256 = "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8"
MAN1_PATH = ".ai/inputs/stage1-commitments-20261016/MANIFEST.json"        # the REQ-20 manifest (140 entries)
MAN1_SHA256 = "f628309032ed8b1a49c1710a6560df4f52a7e3183b77e95653aea41d4e90bd0a"
A1_EDIT = {"path": ".ai/inputs/stage1-commitments-20261016/a1/a1_remove600.edit.json",
           "sha256": "5c0e53b78e9ee71d0e16e13f4fa045509401c0afa98f53c3d7af6bd79ccaf4ca"}
MAN1_EDIT_ARMS = {"A1": A1_EDIT}          # the one edit file MAN1 lists (role "sealed record")
PREPARED_MANIFESTS = {"prepared-kt-dolly-olmo2": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"}
GATE_A_FIXTURE = "tmp/family-probe-olmo2-1b/expected-fixture-probe.json"
PREREG_FIXTURE_SHA256 = "98d775f10ccc032e006c3ebb27c3c70e58c9affda49b6881bc054992216c67b0"
LOCK_SHA256 = "7e0dd99892300a27ab797be746f465860d8ea4055dda36c46d78e743381d15ee"
ANCHOR_FILE_PIN = {"path": "tmp/gate-b-anchors/anchor_bank.json",
                   "sha256": "2cf9633613e235d1f33deee3530c3e53b037845bd3979568887742457c1801ed"}
BASE_PINS_RECORD = {"path": "tmp/gi-vi-stage1/olmo2-0425-1b-base-pins.json",
                    "sha256": "9bc9a9e999dd752df1519d07e7c7c5a9f0f542284a2f3ad0b821347fbd466577"}
BASE_MODEL = {"repo_id": "allenai/OLMo-2-0425-1B", "revision": "a1847dff35000b4271fa70afc5db10fd29fedbdf"}
INSTRUCT_MODEL = {"repo_id": "allenai/OLMo-2-0425-1B-Instruct", "revision": "48d788eca847d4d7548f375ad03d3c9312f6139e",
                  "model.safetensors": "36d044c73655bb904f822915e6294ba3dae8e6e1af5e703e9d452f2d6a3a294f"}
GUARD_MODEL = {"repo_id": "Qwen/Qwen3Guard-Gen-4B", "revision": "6ec42827da0c1ff11e7a49dc269d2e810d27e108"}
# round 3b (item 1; round 2's VR2-5): every S1 package file the kit runs or packs, by SHA-256 (M: shasum -a 256 of
# this tree at main 3eaf968, 23 Oct 2026 about 21:15 UTC; the same bytes at main 40e0cc6). The X pack carries each of
# them and refuses a file whose bytes differ; a lead's code entry under scripts/stage1_s1/ must be one of these pins
# (or D2_CODE's), with no exception. The kit reads no other tree. Round 3c: the O-ext unit runner and its settings
# join them (I: notes/oext-unit-fix.json files; M: shasum -a 256 of this tree at main 40e0cc6, 24 Oct 2026).
# The branch re-pin (addendum §11 point 7 and §13; FOCUS "W1-18 PASSED: BRANCH 128", 87c1b0b; I: notes/repin-build.json):
# oext_eval.json holds Branch 128, W1-18's record 608cbb94... and (item F) build_oext's record a810574e..., and the
# chain oext_eval.py, oext_unit.json/.py,
# eval_adapter.json/.py and lean_eval_job.json/.py follows (M: shasum -a 256 of the re-pinned tree, main a02c1aa plus
# the re-pin, 25 Oct 2026; item F's pass about 12:55 UTC). S1_COMMIT is a label only (pack_setup's refusal text names it); the lead
# replaces it with the commit that holds these bytes.
S1_COMMIT = "3ea5ae1"
S1_CODE = {"scripts/stage1_s1/__init__.py": "818919ca18627b7169d80c2a6f6c24149f6e1c529bff9d37a5ddee2122bddd32",
           "scripts/stage1_s1/eval_adapter.py": "ae95312970336cac5eec993e21b55bb48fc6e907a5c439e67a184f58f8ac0c33",
           "scripts/stage1_s1/safe_lora.py": "5f6b782255f7207645659cc25ea8864c85aeb2d32533acab342175d0217757b4",
           "scripts/stage1_s1/lean_eval_job.py": "82461c13d91471729bb036da6565bcb0555885c4b2347d91cd93abcebd9ca46a",
           "scripts/stage1_s1/oext_eval.py": "8c4290921f32a5b4596a0bc40235cc5cf1185f73eaabeaa625c43bd19ba77719",
           "scripts/stage1_s1/settings/eval_adapter.json":
               "9cc654ecef9fd35664599baba49eaced218afaa6a6a738771d93d962314fbe9b",
           "scripts/stage1_s1/settings/lean_eval_job.json":
               "b0ab19ec28946334e4a033897c1097894fdf5797507f6a516614afc1c2c22acd",
           "scripts/stage1_s1/settings/oext_eval.json":
               "2ad9893849248a8fb61d04cf7badbd7fb398915020f196904849d500df08f5a5",
           "scripts/stage1_s1/settings/safe_lora.json":
               "c5610c3d4f0a0809e391055d84697fd62b9a15cf16e0b1f63aee02b03b6d14cf",
           # round 3c: the O-ext unit runner (J3, J4, J9, J10, J18's O-ext step) and its settings (branch re-pin)
           "scripts/stage1_s1/oext_unit.py": "ae2fb5b5fbea36cbd2b27c4eaa20f10504b9856961ae8ee100311c923876b8e3",
           "scripts/stage1_s1/settings/oext_unit.json":
               "3959eae7264f56f613f5d7cd54e69081d8985ef7cbce2962243f6685e3581189"}
# G1, the engine-Y O-ext re-pin (addendum §34 point 3; §11 point 7, §15 point 1; block B's pre-flight runbook §0 G1):
# B+Qi's O-ext step runs on engine Y. S1_CODE above is unchanged (every X-side S1 file byte-identical: block A's O-ext
# outputs name those settings by SHA-256). The Y pack carries the O-ext package at the paths the job runner calls and
# seals: S1_OEXT_Y_SHARED with S1_CODE's own pins (the package's __init__.py and oext_eval.py, every O-ext rule: one
# shared function on both engines), and S1_OEXT_Y, each Y-pack path from its engine-Y file in this checkout (the
# runner's copy with only its settings pins changed, and the two settings re-pinned on Y that allow B+Qi's config
# 37942cf5 only). M: shasum -a 256 of this tree's files, 29 Oct 2026 (G1 round, notes/g1-yoext.json).
S1_OEXT_Y_SHARED = ("scripts/stage1_s1/__init__.py", "scripts/stage1_s1/oext_eval.py")
S1_OEXT_Y = {"scripts/stage1_s1/oext_unit.py":
                 {"path": "scripts/stage1_s1/oext_unit_y.py",
                  "sha256": "978561ce0269756bbdf921580bb1e8c15592041583ab5d899912c910eb4753de"},
             "scripts/stage1_s1/settings/oext_unit.json":
                 {"path": "scripts/stage1_s1/settings/oext_unit_y.json",
                  "sha256": "80d08721284bbe94661d6fe2cdc58be259db8df66dc681403d7473155c715298"},
             "scripts/stage1_s1/settings/oext_eval.json":
                 {"path": "scripts/stage1_s1/settings/oext_eval_y.json",
                  "sha256": "80469a8f728d15192c360f26640c17b7ba652fbd969cfa45f43113c1defd76f0"}}
# Kit round 32 (addendum §34 points 5-7; block B's pre-flight G4, G6, G8, G11, G13). B10's and B11's files are named
# here by their S1_CODE keys only: S1_CODE is the one place that holds their pins (the B10/B11 re-pin round changes
# the pins there and nothing else in the kit). Block B's second reference phase (K1) reads B10's reference_units and
# B11's accepted fingerprints from these settings at their S1_CODE pins, and needs the X pack to seal these four files
# at those pins (a re-pack after the re-pin).
B10_SETTINGS = "scripts/stage1_s1/settings/eval_adapter.json"
B11_SETTINGS = "scripts/stage1_s1/settings/safe_lora.json"
B10_B11_FILES = ("scripts/stage1_s1/eval_adapter.py", B10_SETTINGS, "scripts/stage1_s1/safe_lora.py", B11_SETTINGS)
B10_EXIT_CERTIFICATION = 4                # eval_adapter.py EXIT_CERTIFICATION (its settings' exit_codes "4"): K3
CERTIFICATION_GATES = ("passed", "failed")   # K3 (G11): a complete b10_certify job names B10's own gate
SECOND_PHASE_KINDS = ("ref_eval", "safe_lora")   # K1: the evaluation-only references on block B's own a0 runs
NOT_RUN_KIND = "stage1 not-run decision"  # K2 (G6): record-not-run, the lead's decision for any block but A
NOT_RUN_KEYS = ("kind", "block", "jobs", "reason", "utc", "recorded_by")
# K6: after a sealed block only readable files are read (seal.py READABLE_PATTERNS), and an a0 unit's e1 fingerprint
# lives in sealed-class files (states/e1/state.json, COMPLETE.json). So the job runner writes, after every complete
# a0_arm job, job-I/<A0_FINGERPRINT_RECORD> (readable: *adapter-fingerprint*.json) in the format the B10/B11 re-pin
# tool (scripts/stage1_s1/repin_reference_seeds.py) reads, and lists it among the job's outputs; the second phase's
# release needs it for each seed.
A0_FINGERPRINT_RECORD = "a0-adapter-fingerprint.json"
A0_FINGERPRINT_KIND = "stage1 a0 adapter fingerprint"
STAGE1_PINS = {   # M (here): shasum -a 256 of the B15 tree (main 721c58f); the S1 package is re-pinned at its merge
    "scripts/stage1/limits/overrefusal_checks.py": "ed5fd2dcb5675d5fe5e135b76e37ece2488dfcc2db5129ba422064502b0d61ae",
    "scripts/stage1/limits/limits_common.py": "2798aa06a01fd89bf3dd8dc2abf33e63bfcb4f17bff700a709eacd2b3ace264c",
    "scripts/stage1/settings/limits_overrefusal_checks.json": "bfa9a56fd0522de066cb04b6f84b99dffda54fbe4b297dc3e4c7f07961c4a41b",
    "scripts/stage1/build_reuse_spec.py": "320299481f480747d42b6ae1102a1fd02dbde2c1f11bf61f2afae50b17ff176c",
    "scripts/stage1/settings/build_reuse_spec.json": "a980264e53f0e660390208934c44d2a37900f1d3381944e9e957e8a2973c22cc",
    "scripts/stage1/make_untuned_answers.py": "c37ac452b931c84ed28b45e9cfeed9cc9a07ec47ce5f1c6fd1bbef95086743c4",
    "scripts/stage1/settings/make_untuned_answers.json": "4bf2cc1a2493bc154d314105a085f0166933d1147a37e29fd42c7348ba9d9d8c",
    "scripts/stage1/representation_pass.py": "fb62bcaaaa35595a52de5a4217754cb390ffb4ba49e04dec6e515d7e3cebb8d9",
    "scripts/stage1/settings/representation_pass.json": "a555fd899bd2b5caf8d68fb62578ed2e943977341b5bf2dc2d688dcbd034600b",
    "scripts/stage1/settings/representation_pools.json": "1451ba5ec435ecaafebd7749f44b6729e45f2157a69a62c55f35e2bbdbae826b",
    "scripts/stage1/score_l1_larf.py": "4996fd3bfdd854ecd82630813f7f9b0dab88c4e7e26f81366c566b93c70e95e5",
    "scripts/stage1/score_classifier.py": "ee8ae89865e188a8e9f3430c9fbfbe129a415dcc9f3427111a7c77e02dc34549",
    "scripts/stage1/settings/score_classifier.json": "5807ec750c74137f3e5c466231de9e73a0cbb5fe5411f7be29a40bbed4c8e58a",
    "scripts/stage1/s1common.py": "930c8ea53d26baeeccaf2035949427d207f307ba0fec06ff0dec841c8c824552",
}

# ----- job kinds (brief §3, J1-J18) ----------------------------------------------------------------------------
KINDS = ("w1_18", "regenerate", "o_only", "transfer_report", "rep_pass", "untuned_answers", "l1_scan", "classifier",
         "arm", "a0_arm", "c0", "cert_c1", "cert_c2", "cert_c3", "b10_certify", "ref_eval", "safe_lora", "ref_train",
         "retrain", "a1_rescore")
KIND_IDS = dict(zip(KINDS, ("J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8", "J9", "J10", "J11", "J12", "J13", "J14",
                            "J15", "J16", "J17", "J18", "J20", "J21")))   # J20/J21: LN-15e (J19 is the judge launch)
UNMEASURED_KINDS = frozenset({"w1_18", "o_only", "transfer_report", "rep_pass", "untuned_answers", "l1_scan",
                              "classifier", "c0", "cert_c2", "cert_c3", "b10_certify", "ref_eval", "safe_lora",
                              "ref_train", "arm", "a0_arm", "a1_rescore"})   # an O500 or an unmeasured term
BANK500_KINDS = frozenset({"o_only", "transfer_report", "arm", "a0_arm", "c0", "ref_eval", "safe_lora", "ref_train"})
DIAG_KINDS = ("rep_pass", "untuned_answers", "l1_scan", "classifier")
TRAINING_KINDS = ("arm", "a0_arm")        # the block tables' runs
ARM_LIKE_KINDS = ("arm", "a0_arm", "ref_train", "cert_c1")   # the engine's arm rule (projection: e1 + training)
CERT_KINDS = ("cert_c1", "cert_c2", "cert_c3")
Y_ONLY_KINDS = ("cert_c1", "cert_c2", "cert_c3")   # round 3b (addendum §26): c0 runs on engine X, in block A
X_ONLY_KINDS = ("c0",)                    # §26: c0 evaluates an engine-X unit with B17's verified X pin
ONE_COUNTED = frozenset({"arm", "a0_arm", "ref_train", "c0", "cert_c1", "cert_c2", "cert_c3"})
POINT_KINDS = {"b10_certify": ("certify", "scale:0"), "ref_eval": None, "safe_lora": ("default", "conditional",
                                                                                         "certify", "k12")}
REF_EVAL_SCALES = ("scale:0.9", "scale:0.75", "scale:0.5")   # LN-15b, lambda = 0.9 added (B10H §11)
LINKED_KINDS = {"o_only": "regenerate",   # a J3 names its J2 (``regen_source``) on the same pod
                "a1_rescore": "retrain"}  # LN-15e: the re-score names its retrain on the same pod (Gate B's link)
LINK_SOURCES = frozenset(LINKED_KINDS.values())
LINK_FIELD = "regen_source"
UNITLESS_KINDS = frozenset({"w1_18", "rep_pass", "untuned_answers", "l1_scan", "classifier", "c0", "transfer_report",
                            "o_only"})            # BUILD-RUNNER fix: an O-only pass writes O-ext files, no engine unit

def guard_off_problem(doc) -> str | None:
    """Why ``doc`` is not the user's budget-guard-off decision record ({kind, user_words, utc, recorded_by}, exactly;
    each text non-empty), or None."""
    if not isinstance(doc, dict) or set(doc) != set(GUARD_OFF_KEYS):
        return f"it must hold exactly {list(GUARD_OFF_KEYS)}"
    if doc["kind"] != GUARD_OFF_KIND:
        return f"its kind is not {GUARD_OFF_KIND!r}"
    if not all(isinstance(doc[k], str) and doc[k].strip() for k in GUARD_OFF_KEYS[1:]):
        return "user_words (verbatim), utc and recorded_by must be non-empty texts"
    return None


def guard_off_record(kit) -> dict | None:
    """(E) The recorded user decision that the live-balance guard is skipped: plan.json's records.guard_off, its file
    re-hashed at its recorded path and re-read (guard_off_problem). Anything else (no plan.json or record, a missing or
    changed file, another document) is None, and the guard stays as it was."""
    import hashlib
    import pathlib

    try:
        rec = (json.loads((pathlib.Path(kit) / "plan.json").read_text()).get("records") or {}).get("guard_off")
        if not isinstance(rec, dict):
            return None
        data = pathlib.Path(rec["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != rec["sha256"]:
            return None
        doc = json.loads(data)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None
    if guard_off_problem(doc) is not None:
        return None
    return {"sha256": rec["sha256"], "utc": doc["utc"], "recorded_by": doc["recorded_by"]}


# (D, 25 Oct: pod a-1) a J5 moved off J6's pod reads J6's s3_orig pool as the named input pool:s3_orig, by the pin
# J6's own text-free record gives (PREREG: J6 is complete and never re-run). plan_tool's defer pins it into the moved
# J5 (job.s3_orig) and pack_setup accepts the input only at this pin.
S3_ORIG_INPUT = "pool:s3_orig"
J6_RECORD, J6_RECORD_KIND, S3_ORIG_POOL = "untuned_answers_record.json", "stage1 untuned answers record", \
    "s3_orig.pool.json"


def s3_orig_pin(plan: dict, kit) -> dict:
    """J6's s3_orig pool pin (names, counts and SHA-256 values only; no text is read): the one complete untuned_answers
    job plan.json records; its recorded outputs job-K/untuned/untuned_answers_record.json and
    job-K/untuned/s3_orig.pool.json (record-done checked both against the pulled tree), each re-hashed in the pulled
    tree (kit/retrieved/HOST/tree); the record is J6's (kind, version 1, complete) and names the pool by the same
    SHA-256 (full_files and lists.s3.s3_orig_pool_sha256). Raises ValueError."""
    import hashlib
    import pathlib

    found = [(host, k, j) for host, h in sorted(plan["hosts"].items()) for k, j in enumerate(h["jobs"])
             if j["kind"] == "untuned_answers" and j.get("status") == "complete"]
    if len(found) != 1:
        raise ValueError(f"plan.json records {len(found)} complete untuned_answers jobs (J6 runs once)")
    host, k, job = found[0]
    outputs = job.get("outputs") or {}
    rec_rel, pool_rel = f"job-{k}/untuned/{J6_RECORD}", f"job-{k}/untuned/{S3_ORIG_POOL}"
    if rec_rel not in outputs or pool_rel not in outputs:
        raise ValueError(f"J6 on {host} recorded no {J6_RECORD} or no {S3_ORIG_POOL} among its outputs")
    tree = pathlib.Path(kit) / "retrieved" / host / "tree"
    try:
        data, pool = (tree / rec_rel).read_bytes(), (tree / pool_rel).read_bytes()
    except OSError:
        raise ValueError(f"J6's {J6_RECORD} or {S3_ORIG_POOL} is not in the pulled tree of {host}") from None
    if hashlib.sha256(data).hexdigest() != outputs[rec_rel] or hashlib.sha256(pool).hexdigest() != outputs[pool_rel]:
        raise ValueError(f"J6's pulled {J6_RECORD} or {S3_ORIG_POOL} differs from its recorded SHA-256")
    try:
        doc = json.loads(data)
    except ValueError:
        raise ValueError(f"J6's {J6_RECORD} is not JSON") from None
    if not isinstance(doc, dict) or (doc.get("kind"), doc.get("version"), doc.get("complete")) != (
            J6_RECORD_KIND, 1, True):
        raise ValueError(f"J6's {J6_RECORD} is not a complete {J6_RECORD_KIND!r} (version 1)")
    named = {(doc.get("full_files") or {}).get(S3_ORIG_POOL),
             ((doc.get("lists") or {}).get("s3") or {}).get("s3_orig_pool_sha256")}
    if named != {outputs[pool_rel]}:
        raise ValueError(f"J6's {J6_RECORD} does not name its {S3_ORIG_POOL} by the recorded SHA-256")
    kit = pathlib.Path(kit).resolve()
    return {"host": host, "index": k, "record": {"path": rec_rel, "sha256": outputs[rec_rel]},
            "pool": {"path": pool_rel, "sha256": outputs[pool_rel]}, "sha256": outputs[pool_rel],
            "pack_path": str((kit / "retrieved" / host / "tree" / pool_rel).relative_to(kit.parents[1]))}

# ----- blocks and hosts --------------------------------------------------------------------------------------------
BLOCKS = ("S1-0", "cert", "A", "certify", "B", "C")
WAVES = BLOCKS                            # host records carry "wave" = their block (status.py reads it)
FUNDING_BLOCK = {"S1-0": "A", "cert": "A", "A": "A", "certify": "B", "B": "B", "C": "C"}   # §8 Q2: block A first
HOST_PREFIX = {"S1-0": "s10", "cert": "cert", "A": "a", "certify": "cfy", "B": "b", "C": "c"}
BLOCK_KINDS = {"S1-0": ("w1_18",),
               "cert": ("cert_c1", "cert_c2", "cert_c3"),   # round 3b: c0 moved to block A's LN-12 pod (§26)
               "A": ("regenerate", "o_only", "transfer_report", "rep_pass", "untuned_answers", "l1_scan",
                     "classifier", "arm", "a0_arm", "c0", "retrain", "a1_rescore"),
               "certify": ("b10_certify",),
               "B": ("regenerate", "o_only", "arm", "a0_arm", "ref_eval", "safe_lora", "ref_train"),
               "C": ("arm",)}
POD_SIZES = {"preflight_wait_s": 3600, "container_disk_gb": 80, "volume_gb": 40}   # I: + the base model for J17
POD_NAME_PREFIX = "attribution-s1-"       # host.py name_of; never Gate B's "attribution-gateb-"

# administrative
TOKEN_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
PREPARED_NAME = "prepared-kt-dolly-olmo2"
PREPARED_LOCAL = "tmp/kt-prepared"
PROBE_KEY = "olmo2-1b"
STATUSES = ("planned", "complete", "crashed", "deferred", "not_started")
BOOTSTRAP_FIELDS = ("lock_sha256", "pip_version", "gpu", "cuda_runtime")
LOG_ONLY_FIELDS = ("pip_version",)


def hours(seconds: float) -> float:
    return seconds / 3600


def training_s(fixture: dict, steps: int) -> float:
    """The fixture's training seconds scaled to ``steps`` (x steps/38)."""
    return fixture["training_s"] * steps / FIXTURE_STEPS


def o500_s(branch: str) -> float:
    if branch not in BRANCHES:
        raise ValueError(f"unknown cap branch {branch!r}")
    return O500_S[branch]


def _points(kind: str, n_points: int) -> int:
    if kind in POINT_KINDS and (type(n_points) is not int or n_points < 1):
        raise ValueError(f"{kind}: at least one evaluation point")
    return n_points


def measured_upper(kind: str, steps: int | None = None, branch: str = BRANCH_DEFAULT, n_points: int = 1,
                   recipe: str | None = None, fixture: dict | None = None) -> float:
    """A job's measured upper (its spend upper and its term in later jobs' cap): Gate B's frozen values plus the
    stage-1 terms (brief §3 and §5.4)."""
    o = o500_s(branch)
    if kind == "w1_18":
        return W1_18_UPPER_S
    if kind in ("regenerate", "retrain"):
        return REGEN_MEASURED_S
    if kind == "a1_rescore":
        return RESCORE_MEASURED_S
    if kind == "o_only":
        return O_ONLY_FACTOR * o
    if kind == "transfer_report":
        if branch != "128":
            raise ValueError("the LN-14 transfer report runs under Branch 128 only")
        return TRANSFER_S
    if kind in DIAG_KINDS:
        return DIAG_ESTIMATE_S[kind]
    if kind in ("arm", "a0_arm"):
        return ARM_MEASURED_S + o
    if kind == "ref_train":
        extra = REF_FORWARD_SHARE * training_s(fixture, steps) if recipe == "bqi" else 0.0
        return ARM_MEASURED_S + o + extra
    if kind == "c0":
        return C0_S
    if kind == "cert_c1":
        return ARM_MEASURED_S
    if kind == "cert_c2":
        return REGEN_MEASURED_S * (1 + REF_FORWARD_SHARE)
    if kind == "cert_c3":
        return CERT_C3_S
    if kind == "b10_certify":
        return REGEN_MEASURED_S + _points(kind, n_points) * EVAL_ONLY_S
    if kind == "ref_eval":
        return REGEN_MEASURED_S + _points(kind, n_points) * (EVAL_ONLY_S + o)
    if kind == "safe_lora":
        return REGEN_MEASURED_S + SAFE_LORA_TRANSFORM_S + SAFE_LORA_HASH_S + _points(kind, n_points) * (EVAL_ONLY_S + o)
    raise ValueError(f"unknown job kind {kind!r}")


def upper_s(kind: str, fixture: dict | None, steps: int | None, branch: str = BRANCH_DEFAULT, n_points: int = 1,
            recipe: str | None = None) -> float:
    """A job's worst-case seconds (B3 with the stage-1 terms)."""
    over = OVERHEAD_FLOOR_S + SAFETY_MARGIN_S
    o = o500_s(branch)
    if kind in ("arm", "a0_arm"):
        return fixture["e1_upper_s"] + training_s(fixture, steps) + over + o
    if kind == "ref_train":
        factor = 1 + REF_FORWARD_SHARE if recipe == "bqi" else 1.0
        return fixture["e1_upper_s"] + factor * training_s(fixture, steps) + over + o
    if kind == "cert_c1":
        return fixture["e1_upper_s"] + training_s(fixture, steps) + over
    if kind in ("regenerate", "retrain"):
        return training_s(fixture, steps) + over
    if kind == "a1_rescore":
        return DIAG_UPPER_FACTOR * RESCORE_MEASURED_S
    if kind == "cert_c2":
        return (training_s(fixture, steps) + over) * (1 + REF_FORWARD_SHARE)
    if kind in ("w1_18", "cert_c3"):
        return measured_upper(kind, steps, branch, n_points, recipe, fixture)
    if kind in DIAG_KINDS:
        return DIAG_UPPER_FACTOR * DIAG_ESTIMATE_S[kind]
    if kind in ("o_only", "transfer_report", "c0", "b10_certify", "ref_eval", "safe_lora"):
        return measured_upper(kind, steps, branch, n_points, recipe, fixture) + over
    raise ValueError(f"unknown job kind {kind!r}")


def start_requirement_s(upper: float) -> float:
    return upper + START_MARGIN_S


def counted(kind: str, n_points: int = 1) -> int:
    """§8 Q5: what a job counts toward MAX_ARMS_PER_POD."""
    if kind in ONE_COUNTED:
        return 1
    if kind in POINT_KINDS:
        return _points(kind, n_points)
    return 0


def job_record(kind: str, arm: str | None, seed: int | None, edit, steps: int | None, fixture: dict | None,
               a0_source: int | None = None, *, branch: str = BRANCH_DEFAULT, engine: str = ENGINE_DEFAULT,
               points: list | None = None, recipe: str | None = None, regen_source: int | None = None) -> dict:
    """One plan job with its timing fields from this module's rules (``a0_source`` is Gate B's name, unused here)."""
    n = len(points) if points else 1
    up = upper_s(kind, fixture, steps, branch, n, recipe)
    measured = measured_upper(kind, steps, branch, n, recipe, fixture)
    job = {"kind": kind, "job_id": KIND_IDS[kind], "arm": arm, "seed": seed, "edit": edit, "steps": steps,
           "engine": engine, "branch": branch, "recipe": recipe, "points": list(points) if points else None,
           "upper_s": up, "start_requirement_s": start_requirement_s(up), "measured_upper_s": measured,
           "spend_upper_s": measured, "o500_s": o500_s(branch) if kind in BANK500_KINDS else 0.0,
           "counted": counted(kind, n), "unmeasured": kind in UNMEASURED_KINDS, "status": "planned"}
    if kind in LINKED_KINDS:
        job[LINK_FIELD] = regen_source
    return job


def projected_requirement_s(job: dict, projection: dict | None) -> float | None:
    """This pod's preflight projection of a job's start requirement (the arm-like kinds and the regeneration; None
    otherwise). ``projection`` is the preflight's cap_projection block (e1_upper_s, training_s, overhead_s, margin_s,
    and o500_s once the preflight measures it): the O500 term is max(the plan's, the projection's)."""
    kind = job["kind"]
    if kind not in ARM_LIKE_KINDS and kind not in LINK_SOURCES:
        return None
    if not projection:
        raise ValueError("no preflight projection for an arm or a regeneration")
    fixture = {"e1_upper_s": projection["e1_upper_s"], "training_s": projection["training_s"]}
    over = max(projection.get("overhead_s") or 0.0, OVERHEAD_FLOOR_S) + max(projection.get("margin_s") or 0.0,
                                                                           SAFETY_MARGIN_S)
    factor = 1 + REF_FORWARD_SHARE if job.get("recipe") == "bqi" else 1.0
    base = factor * training_s(fixture, job["steps"]) + over
    if kind in LINK_SOURCES:
        return start_requirement_s(base)
    o = max(job.get("o500_s") or 0.0, projection.get("o500_s") or 0.0) if kind in BANK500_KINDS else 0.0
    return start_requirement_s(base + fixture["e1_upper_s"] + o)


def own_requirement_s(job: dict, projection: dict | None = None) -> float:
    """max(the plan value, this pod's projection)."""
    projected = projected_requirement_s(job, projection) if projection is not None else None
    return max(job["start_requirement_s"], projected if projected is not None else 0.0)


def linked_follower(jobs: list[dict], index: int) -> int | None:
    """The index of the later linked pass (a J3 O-only pass for a J2, LN-15e's re-score for its retrain) whose
    regen_source names the job at ``index``, or None."""
    for later in range(index + 1, len(jobs)):
        if LINKED_KINDS.get(jobs[later]["kind"]) == jobs[index]["kind"] and jobs[later].get(LINK_FIELD) == index:
            return later
    return None


linked_diagnostics = linked_follower      # Gate B's name (there: the diagnostics naming the retrain)


def requirements(jobs: list[dict], projection: dict | None = None) -> list[float]:
    """Each job's start requirement on a pod: its own (plan and projection), and for a regeneration (or LN-15e's
    retrain) named by a later linked pass, max(its own, its measured upper + the pass's requirement): the pair starts
    together or not at all."""
    own = [own_requirement_s(job, projection) for job in jobs]
    out = list(own)
    for k, job in enumerate(jobs):
        if job["kind"] in LINK_SOURCES:
            later = linked_follower(jobs, k)
            if later is not None:
                out[k] = max(own[k], job["measured_upper_s"] + own[later])
    return out


def round_up_s(seconds: float) -> float:
    """Up to the next CAP_STEP_S (a value within a microsecond of a step stays on it)."""
    return math.ceil(round(seconds, 6) / CAP_STEP_S) * CAP_STEP_S


def cap_hours(jobs: list[dict]) -> float:
    """B4: the largest, over the jobs k, of POD_OVERHEAD_S + the measured uppers of jobs before k + job k's start
    requirement (with the link), rounded up to 0.25 h."""
    if not jobs:
        raise ValueError("a host without jobs has no cap")
    need = requirements(jobs)
    worst = max(POD_OVERHEAD_S + sum(j["measured_upper_s"] for j in jobs[:k]) + need[k] for k in range(len(jobs)))
    return hours(round_up_s(worst))


def pod_sizes(n: int) -> list[int]:
    """ceil(n / MAX_ARMS_PER_POD) pods, as even as possible, the earlier pods taking the one extra run (8 -> 4 + 4,
    6 -> 3 + 3, 5 -> 3 + 2, 20 -> 4 x 5, 14 -> 4 + 4 + 3 + 3). ``deal`` gives exactly these sizes."""
    m = MAX_ARMS_PER_POD
    if type(m) is not int or m < 1:
        raise ValueError("MAX_ARMS_PER_POD must be a positive integer")
    if type(n) is not int or n < 1:
        raise ValueError("a block needs at least one run")
    k = -(-n // m)
    return [n // k + (1 if i < n % k else 0) for i in range(k)]


def split_pods(jobs: list) -> list[list]:
    """Gate B's contiguous split (kept for its name; stage 1 deals with ``deal``)."""
    out, start = [], 0
    for size in pod_sizes(len(jobs)):
        out.append(list(jobs[start:start + size]))
        start += size
    return out


def deal(runs: list) -> list[list]:
    """§8 Q3 (adopted): the interleaving deal. ``runs`` are (arm, seed) pairs; they are put arm-major (ARM_ORDER),
    seed-minor, and run i goes to pod i mod P with P = len(pod_sizes(n)), so each arm's runs go to consecutive pods.
    A pod that would hold one arm twice refuses (the rule is outcome-free and fixed before launch; plan.json records
    the result)."""
    ordered = sorted(runs, key=lambda r: (ARM_ORDER.index(r[0]), r[1]))
    if len(set(ordered)) != len(ordered):
        raise ValueError("a run is listed twice")
    p = len(pod_sizes(len(ordered)))
    pods = [ordered[i::p] for i in range(p)]
    for pod in pods:
        arms = [a for a, _ in pod]
        if len(set(arms)) != len(arms):
            raise ValueError("the deal puts one arm twice on a pod; the lead decides")
    return pods


def arm_count(jobs: list[dict]) -> int:
    """§8 Q5: the counted jobs of a pod (training arms and evaluation-only points)."""
    return sum(j.get("counted", counted(j["kind"], len(j.get("points") or []) or 1)) for j in jobs)


def guard_usd(cap_h: float) -> float:
    """What the budget guard needs for one pod of this cap: $6 + cap x $1.85."""
    return RESERVE_USD + cap_h * PLANNING_PRICE_USD


SPEND_UPPER_S = {k: None for k in KINDS}   # per job: job["spend_upper_s"] (it depends on the branch and steps)
MEASURED_UPPER_S = SPEND_UPPER_S


def _spend_s(item) -> float:
    if isinstance(item, dict):
        return item["spend_upper_s"]
    raise ValueError("a stage-1 pod's spend needs its job records (the spend depends on the branch and steps)")


def pod_spend_usd(kinds: list) -> float:
    """One pod's upper spend: (42 min + its jobs' spend uppers) x $1.79; ``kinds`` are the pod's job records."""
    return hours(POD_OVERHEAD_S + sum(_spend_s(k) for k in kinds)) * RATE_USD


def granite_on_pod() -> bool:
    if type(GRANITE_ON_POD) is not bool:
        raise ValueError("GRANITE_ON_POD must be True (pod Granite) or False (Mac Granite)")
    return GRANITE_ON_POD


def granite_cap_hours(answers: int) -> float:
    """The judge launcher's cap for ``answers``: the smallest half hour of at least (30 min + 0.5 s x answers +
    15 min), never below 1 h; above 6 h it refuses."""
    if type(answers) is not int or answers < 1:
        raise ValueError("a Granite launch judges at least one answer")
    need = (GRANITE_SETUP_UPPER_S + answers * GRANITE_S_PER_ANSWER + GRANITE_MARGIN_S) / 3600
    cap = max(GRANITE_CAP_MIN_H, math.ceil(need * 2) / 2)
    if cap > GRANITE_CAP_MAX_H:
        raise ValueError(f"a Granite launch of {answers} answers needs a cap above {GRANITE_CAP_MAX_H} h")
    return cap


def granite_pod(arms: int) -> dict:
    """One pod Granite judge launch of ``arms`` arms (200 greedy answers each plus the known-answer gate's 200)."""
    if type(arms) is not int or arms < 1:
        raise ValueError("a Granite launch judges at least one arm")
    answers = arms * GRANITE_GREEDY_PER_ARM + GRANITE_KNOWN_ANSWERS
    return {"judge": "granite", "arms": arms, "answers": answers, "kinds": [], "cap_hours": granite_cap_hours(answers)}


def harmbench_cap_hours(answers: int) -> float:
    """The judge launcher's HarmBench cap (judge_pod.cap_hours_for): the smallest half hour of at least (30 min +
    0.25 s x answers + 15 min), never below 1 h; above 6 h it refuses (split the units over two launches)."""
    if type(answers) is not int or answers < 1:
        raise ValueError("a HarmBench launch judges at least one answer")
    need = (GRANITE_SETUP_UPPER_S + answers * HARMBENCH_S_PER_ANSWER + GRANITE_MARGIN_S) / 3600
    cap = max(GRANITE_CAP_MIN_H, math.ceil(need * 2) / 2)
    if cap > GRANITE_CAP_MAX_H:
        raise ValueError(f"a HarmBench launch of {answers} answers needs a cap above {GRANITE_CAP_MAX_H} h")
    return cap


def harmbench_pod(arms: int) -> dict:
    """One HarmBench judge launch of ``arms`` units (200 greedy and 600 sampled answers each, Gate B's launch H)."""
    if type(arms) is not int or arms < 1:
        raise ValueError("a HarmBench launch judges at least one unit")
    answers = arms * HARMBENCH_ANSWERS_PER_ARM
    return {"judge": "harmbench", "arms": arms, "answers": answers, "kinds": [],
            "cap_hours": harmbench_cap_hours(answers)}


def judge_pod(judge: str, arms: int) -> dict:
    """A judge launch of either judge (round 3a): its cap from the launcher's rule; its upper spend is cap x $1.79."""
    if judge == "harmbench":
        return harmbench_pod(arms)
    if judge == "granite":
        return granite_pod(arms)
    raise ValueError(f"unknown judge {judge!r} (one of {list(JUDGES)})")


def launch_pod_spend_usd(pod: dict) -> float:
    """A launch pod's upper spend: a judge pod's cap x $1.79; a kit pod's recorded spend_usd, else pod_spend_usd."""
    if pod.get("judge"):
        return pod["cap_hours"] * RATE_USD
    if "spend_usd" in pod:
        return pod["spend_usd"]
    return pod_spend_usd(pod["kinds"])


def cents(usd: float) -> float:
    """An amount rounded to the cent, half up (decimal, not binary, rounding)."""
    return float(Decimal(repr(usd)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def funding_need_usd(launches: list[list[dict]], factor: float = 1.0) -> dict:
    """B4 (unchanged): ``launches`` in path order; each a list of pods {"cap_hours", "spend_usd" or "kinds"} or judge
    pods. The base need = the largest term, rounded to the cent; the need = factor x the rounded base, rounded to the
    cent; the contingency = need - base."""
    terms, spent = [], 0.0
    for launch in launches:
        terms.append(spent + RESERVE_USD + PLANNING_PRICE_USD * sum(p["cap_hours"] for p in launch))
        spent += sum(launch_pod_spend_usd(p) for p in launch)
    base = cents(max(terms))
    need = cents(float(Decimal(repr(base)) * Decimal(repr(factor))))
    return {"base_need_usd": base, "factor": factor, "need_usd": need, "contingency_usd": cents(need - base),
            "terms_usd": terms}


def rerun_cost_usd(kind, new_pod: bool) -> float:
    """A re-run's upper spend, paid from the contingency: its spend upper x $1.79, plus 42 min when it needs a new
    pod. ``kind`` is the job record (its spend upper depends on the branch and steps)."""
    return hours(_spend_s(kind) + (POD_OVERHEAD_S if new_pod else 0)) * RATE_USD


def unit_rerun_cost_usd(kinds: list, new_pod: bool) -> float:
    """A pre-job requeue's jobs paid as one unit: the sum of the one-by-one costs (the 42 min on the first only)."""
    return sum(rerun_cost_usd(k, new_pod and i == 0) for i, k in enumerate(kinds))


def default_jobs(kinds: list[str], fixture: dict, arm_steps: int = 33, retrain_steps: int = 38,
                 branch: str = BRANCH_DEFAULT) -> list[dict]:
    """Jobs of the given kinds with the default timing (an O-only pass names the last regeneration before it)."""
    out = []
    for kind in kinds:
        steps = arm_steps if kind in ("arm", "cert_c1", "c0") else retrain_steps if kind in (
            "regenerate", "a0_arm", "ref_train", "cert_c2", "retrain") else None
        source = max((i for i, j in enumerate(out) if j["kind"] == LINKED_KINDS.get(kind)), default=None)
        out.append(job_record(kind, None, None, None, steps, fixture, branch=branch,
                              engine="Y" if kind in Y_ONLY_KINDS else ENGINE_DEFAULT,
                              regen_source=source if kind in LINKED_KINDS else None))
    return out


def gate(remaining_s: float | None, requirement_s: float) -> bool:
    """A job starts only when the remaining time is known and at least its requirement (None never fits)."""
    return remaining_s is not None and remaining_s >= requirement_s


def compare(new: dict, reference: dict, fields) -> dict:
    """Field names (never values) that differ, that are missing, and the log-only differences."""
    missing = sorted(f for f in fields if new.get(f) is None)
    differ = sorted(f for f in fields if f not in missing and new.get(f) != reference.get(f))
    logged = [f for f in differ if f in LOG_ONLY_FIELDS]
    stopping = [f for f in differ if f not in LOG_ONLY_FIELDS]
    return {"differ": stopping, "missing": missing, "logged": logged, "stop": bool(stopping or missing)}
