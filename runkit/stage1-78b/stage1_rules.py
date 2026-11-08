"""The 7-8B kit's rules (runkit/stage1-78b/; K1 of the readiness plan's T4; the lead's Part 1 rulings, ruling 11 KD1-KD11;
the addendum's A1, A2, A8, A13; stdlib plus rules_78b.py beside it). A copy of the stage-1 kit's stage1_rules.py
(runkit/stage1-olmo/, byte for byte at COPY-MANIFEST.json's source_head) with these changes and no other:

1. Caps, guards, spend uppers and the funding need come from rules_78b.py's M-cap rule (KD1): job_record, cap_hours,
   pod_spend_usd, requirements, arm_count, guard_usd, cents, funding_need_usd, pod_sizes, round_up_s, gate and the money
   constants are rules_78b's (the stage-1 kit's values; 48 min pod overhead, KCR §4). The 1B timing constants (FRE_S,
   O500_S, ARM_MEASURED_S, REGEN_MEASURED_S, DIAG_ESTIMATE_S, C0_S, EVAL_ONLY_S, ...) are gone: nothing in this copy
   prices a job from them. Money rules unchanged (plan_tool records them): planning $1.85/h, spend $1.79/h, create
   refused above $10/h, $6 reserve, contingency 1.25, the user's guard-off decision (GUARD_OFF_*), in-pod stop timers at
   the cap, stop never delete, GATE_B_HOLD_USD = 0 with its reason string (KD4).
2. The family is part of the working copy (KD7): a copy is tmp/family-probe-s78-<family>-<block>/ for ONE family and ONE
   block, and FAMILY / KIT_BLOCK are read from the folder's name (kit_identity). A copy may also carry kit-family.json
   (pack_setup.py writes it into the pod's setup tar, so the pod knows its family); when both exist they must agree.
   Every per-family value (REC, PROBE_KEY, PREPARED_NAME, the sealed set, the fixture, the a0 side units, the models,
   TRAINING_IDENTITY) is the family's from rules_78b.KIT; family_or_refuse() refuses when the folder names no family
   (the committed runkit/stage1-78b/ itself plans, packs and launches nothing), and plan_tool refuses a jobs file, a
   plan.json or an inputs record that names the other family (the test holds it).
3. Blocks: "0" only in this round (N, ruling 11): block_runs("0") is rules_78b.block0_runs(FAMILY) (R_1-R_3 at
   1101-1103 under the family's MAIN config, never a recipe-S sibling, P78:99; a0 at 1103 on Llama-3.1-8B only, ruling
   8); deal() puts N's runs on one pod. The 1B blocks (S1-0, cert, A, certify, B, C, sim, P) refuse in this copy; they
   belong to runkit/stage1-olmo/. Kinds allowed in block 0: arm (an edit file) and a0_arm. The retrain kind (ruling 10,
   addendum A2, A8: one single-job pod per family, recipe S_78, after the anchor job) is defined through rules_78b: its
   E cap prints in the need (M3) and it refuses to be planned or run through rules_78b.recipe_s_or_refuse while
   RECIPE_S is null (A1). The scorer kinds are defined the same way (E caps in the need; their jobs come in a later round).
3a. R1 K1 (8 Nov 2026; GXB, PLAN-AB §2 Track K row K1): BLOCKS gains "A" and "B" with HOST_PREFIX, FUNDING_BLOCK and
   BLOCK_KINDS; block_runs("A" / "B") is rules_78b.block_runs_78b (Part 2 §2.2: block A 21 runs per family, block B
   23 / 32 / 47 by plan, plus the dose rows; A1, L1 and S3 dropped on a family whose anchor job stopped); deal(runs,
   block) interleaves blocks A and B (rules_78b.deal_ab); block_jobs prices them with each arm's own steps derived
   from its edit's rows (GXB O1), its train_scale input and the O-ext cap term; REJUDGED_PINS["A"] holds the 7
   re-judged units (N's null until block 0's record-done); BANK500_KINDS and BRANCHES are rules_78b's; the scorer
   block's unit inputs are keyed by (arm, seed). The planning route that calls these (init-block A / B, the gate
   record, the branch record) is K2's; the runner's commands are K3's.
4. Everything the job runner, the launch path, the seal and the judge route import by name from the stage-1 kit's
   module keeps its name here (the names in "kept for the copied modules" below), with a 7-8B value or a neutral one;
   the 1B-only machinery (W1-18 branches, Gate B's final and verdict records, certificates, C2/C3, D-2, the S1 package
   pins, the block-A plan, B14's similarity pass, the plant pilot) has no value here and the copied code paths that need
   it are not reachable from block 0 (they are the next stages' to port or drop).

Labels: M = measured (command given in the K1 report), R = read (path:line), E = estimate (basis), I = inference.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent

try:
    import rules_78b as r78                   # the kit folder is on sys.path (every kit script puts HERE there)
except ImportError:                           # loaded by path (a test, a tool): the module beside this file
    _spec = importlib.util.spec_from_file_location("rules_78b", HERE / "rules_78b.py")
    r78 = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(r78)

# ===== money and timing constants (rules_78b's; the stage-1 kit's values, KCR §4's 48 min overhead) ================
POD_OVERHEAD_S = r78.POD_OVERHEAD_S       # 48 min (KCR §4; the stage-1 kit's 42 min is the one deliberate difference)
START_MARGIN_S = r78.START_MARGIN_S       # a job starts only with its requirement left
OVERHEAD_FLOOR_S = r78.OVERHEAD_FLOOR_S
SAFETY_MARGIN_S = r78.SAFETY_MARGIN_S
FIXTURE_STEPS = r78.FIXTURE_STEPS
CONTINGENCY_FACTOR = r78.CONTINGENCY_FACTOR   # 1.25
CAP_STEP_S = r78.CAP_STEP_S               # caps are rounded up to 0.25 h
MAX_PRICE_USD = r78.MAX_PRICE_USD         # $10/h: the create-time limit (the user's rule, kept)
PLANNING_PRICE_USD = r78.PLANNING_PRICE_USD   # $1.85/h: the guard's planning price
RATE_USD = r78.RATE_USD                   # $1.79/h: the A100's measured price
RESERVE_USD = r78.RESERVE_USD             # $6: the user's 5 Oct rule
GATE_B_HOLD_USD = r78.GATE_B_HOLD_USD     # 0 (KD4)
GATE_B_HOLD_REASON = r78.GATE_B_HOLD_REASON
# (E) the user's decision of 25 Oct (GI VI chat, FOCUS 8d3d505: "remove the guard its not needed I can control it
# better"): a recorded record of this kind (plan_tool record-guard-off) makes launch.py and host.py extend-cap go past
# the live-balance guard's refusal (running pods and the new pod at full caps plus RESERVE_USD); budget.py check still
# reads and logs the live balance and must succeed. MAX_PRICE_USD, the in-pod stop timer at the cap and
# stop-never-delete are unchanged. Without the record the guard is exactly as before. (Unchanged from the stage-1 kit;
# the 7-8B kit carries the decision over: ruling 11, the K1 brief.)
GUARD_OFF_KIND = "stage1 user decision: budget guard off"
GUARD_OFF_KEYS = ("kind", "user_words", "utc", "recorded_by")
GUARD_REFUSED_EXIT = 3                    # budget.py check's exit when the guard refuses (any other non-zero: no read)
MAX_ARMS_PER_POD = r78.MAX_ARMS_PER_POD_78B   # 4 (KD2: a lead ruling under the delegation; caps 10.5 h OLMo, 12.5 h Llama)
MAX_COUNTED_PER_POD = MAX_ARMS_PER_POD
SETUPTOOLS_PIN = "78.1.0"                 # [D5], unchanged
PIP_PIN = None                            # [D5], unchanged

# ===== the working copy's identity (KD7) ===========================================================================
FAMILIES = tuple(r78.FAMILIES)            # ("olmo2-7b", "llama31-8b")
WORKING_COPY_PREFIX = r78.WORKING_COPY_PREFIX   # "family-probe-s78-": the frozen budget.py's KITS_GLOB sees it (C7)
WORKING_COPY_RE = re.compile(r"^family-probe-s78-(olmo2-7b|llama31-8b)-([0-9A-Za-z][0-9A-Za-z-]*)$")
KIT_FAMILY_FILE = "kit-family.json"       # {"kind": KIT_FAMILY_KIND, "family", "block"}: written by pack_setup into the
KIT_FAMILY_KIND = "stage1-78b kit family"  # pod's setup tar; optional in a working copy (it must agree with the name)


def kit_identity(here: pathlib.Path | None = None) -> dict:
    """{"family", "block", "problem"} of the kit folder: the family and block from the KD7 name
    tmp/family-probe-s78-<family>-<block>/, or from kit-family.json beside the module (the pod). Both present must
    agree. The committed kit folder (runkit/stage1-78b) names no family: family None, problem None (nothing to plan)."""
    here = pathlib.Path(here or HERE)
    named = WORKING_COPY_RE.match(here.name)
    family, block = (named.group(1), named.group(2)) if named else (None, None)
    path = here / KIT_FAMILY_FILE
    if path.is_file():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return {"family": None, "block": None, "problem": f"{KIT_FAMILY_FILE} is not JSON"}
        if not isinstance(doc, dict) or doc.get("kind") != KIT_FAMILY_KIND or doc.get("family") not in FAMILIES \
                or not isinstance(doc.get("block"), str) or not doc["block"]:
            return {"family": None, "block": None, "problem": f"{KIT_FAMILY_FILE} is not a {KIT_FAMILY_KIND!r} record"}
        if family is not None and (doc["family"], doc["block"]) != (family, block):
            return {"family": None, "block": None,
                    "problem": f"{KIT_FAMILY_FILE} names {doc['family']} block {doc['block']}, the folder {family} block {block}"}
        family, block = doc["family"], doc["block"]
    return {"family": family, "block": block, "problem": None}


_IDENTITY = kit_identity()
FAMILY: str | None = _IDENTITY["family"]  # None in the committed folder: nothing is planned, packed or launched there
KIT_BLOCK: str | None = _IDENTITY["block"]
KIT_PROBLEM: str | None = _IDENTITY["problem"]


def family_or_refuse(family: str | None = None) -> str:
    """The copy's family (or ``family`` when given, which must be the copy's). Raises ValueError when this folder names
    no family (not a KD7 working copy), when its name and kit-family.json disagree, or when ``family`` is another."""
    if KIT_PROBLEM:
        raise ValueError(f"this kit folder's identity is inconsistent: {KIT_PROBLEM}")
    if FAMILY is None:
        raise ValueError(f"{HERE.name} names no family: a 7-8B working copy is tmp/{WORKING_COPY_PREFIX}<family>-<block>/ "
                         f"(KD7; families {', '.join(FAMILIES)}); the committed kit plans, packs and launches nothing")
    if family is not None and family != FAMILY:
        if family not in FAMILIES:
            raise ValueError(f"unknown family {family!r} (one of {', '.join(FAMILIES)})")
        raise ValueError(f"this working copy is {FAMILY}'s (block {KIT_BLOCK}); it never plans, packs or launches "
                         f"{family}'s jobs (one family per copy, KD7)")
    return FAMILY


def other_family(family: str) -> str:
    return [f for f in FAMILIES if f != family][0]


def family_block(family: str | None = None) -> dict:
    """The per-family constants block (rules_78b.KIT) of the copy's family, or of ``family`` (which must be the copy's)."""
    return r78.kit_of(family_or_refuse(family))


# ===== per-family values (rules_78b.KIT; None in the committed folder) ===============================================
_KIT = r78.KIT[FAMILY] if FAMILY in FAMILIES and not KIT_PROBLEM else None
PROBE_KEY = _KIT["probe_key"] if _KIT else None                     # probes.PROBES key
REC = _KIT["rec"][0] if _KIT else None                              # the family's MAIN config path (every arm runs it)
REC_CONFIG_SHA256 = _KIT["rec"][1] if _KIT else None                # its config_sha256 (the engine's canonical hash)
# The recipe files by their BYTES (M: shasum -a 256 at f5e3b4c, 5 Nov 2026), for the pack and the release; the engine's
# config_sha256 of each is rules_78b.CONFIGS' (the release checks both). Recipe S_78, G and B+Qi join when their pins
# are filled (rules_78b.RECIPE_S / RECIPE_G / RECIPE_BQI; addendum A1, A13).
RECIPE_FILE_SHA256 = {
    "experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json":
        "e9e98e8427575eaa68ae093ebe90bfb0db5264850dfda77e4c2e629c14a952c5",
    "experiments/safety_selection/configs/study-kt-llama31-8b-r64-b5e5-mb2-20261010.json":
        "3d437bd631653130d408158728002a8b970f5aba195f323499151b2b074c9e87",
}
RECIPE_S = None                           # addendum A1: the family's S_78 config path, pinned by the lead after its
RECIPE_G = None                           # anchor job (rules_78b.RECIPE_S); G and B+Qi before block A (A13)
RECIPE_BQI = None
RECIPE_PINS = {REC: RECIPE_FILE_SHA256[REC]} if REC else {}        # path -> the file's SHA-256 (the pack's byte check)
RECIPE_NAMES = {"B": REC} if REC else {}                            # the recipe names a job may carry: "B" = the main
#                                                                     config (P78:99: never a recipe-S sibling for arms)
TRAINING_IDENTITY = _KIT["training_identity"] if _KIT else None    # P78 §2.3 condition 2 (M: the fixture's field)
TRAINING_IDENTITY_RECIPES = ("B",)        # the release checks the main config's training identity against it
PREPARED_NAME = _KIT["prepared_name"] if _KIT else None
PREPARED_MANIFESTS = {_KIT["prepared_name"]: _KIT["manifest_sha256"]} if _KIT else {}
PREPARED_MANIFESTS_ALL = {r78.KIT[f]["prepared_name"]: r78.KIT[f]["manifest_sha256"] for f in FAMILIES}
PREPARED_LOCAL = "tmp/kt-prepared"
MAN_PATH = r78.SEALED_SETS[FAMILY]["path"] if _KIT else None       # the family's sealed edit set (ruling 14, A3)
MAN_SHA256 = r78.SEALED_SETS[FAMILY]["sha256"] if _KIT else None   # both pins filled (Llama: the lead's PP7, 2a1db220...)
FIXTURE = dict(_KIT["fixture"]) if _KIT else None                   # the a0-1101 side unit's preflight verification.json
GATE_A_FIXTURE = FIXTURE["path"] if FIXTURE else None               # (the stage-1 kit's name for it; plan_tool.fixture)
PREREG_FIXTURE_SHA256 = FIXTURE["sha256"] if FIXTURE else None
A0_UNITS = dict(_KIT["a0_units"]) if _KIT else {}                   # P78 §2.1's side units by COMPLETE.json SHA-256
BASE_MODEL = dict(_KIT["base_model"]) if _KIT else None             # revision None until the lead pins it (no Safe LoRA)
INSTRUCT_MODEL = dict(_KIT["instruct_model"]) if _KIT else None
GUARD_MODEL = {"repo_id": "Qwen/Qwen3Guard-Gen-4B", "revision": "6ec42827da0c1ff11e7a49dc269d2e810d27e108"}
BASE_PINS_RECORD = None                   # the 1B base pins record has no 7-8B counterpart yet (BASE_MODEL is null)

# ===== engines and keys (rules_78b's) ==============================================================================
ENGINES = dict(r78.ENGINES)               # {"X": 472fc7f6...}; engine Y joins through rules_78b.ENGINE_Y (A13)
ENGINE_DEFAULT = "X"
ENGINE_X = r78.ENGINE_X
Y_TREE_DEFAULT = "tmp/engine-y-34bfd288"  # engine Y's frozen tree (the stage-1 kit's); a Y pack comes with KD9
YHASH_PIN = {"path": "backups/2026-10-22/engine-round-y-34bfd288.sha256",
             "sha256": "9baa5c79a7227b60c5276070144a858695a588d497163b7f92638f04c7435dca"}
GPU_NAME = r78.GPU_NAME
BANK = dict(r78.BANK)

# ===== seeds, arms and blocks ======================================================================================
DEV_SEEDS = (1101, 2099)                  # the development seed namespace
R_SEED_BASE = r78.R_SEED_BASE             # R_d runs at seed 1100 + d
A0_SEEDS = tuple(range(1101, 1108))       # a0 at 1101-1107 in every plan (ruling 2)
REUSED_SEEDS = (1101, 1102, 1103)         # the side units' seeds (ruling 7)
METHOD_SEEDS = {"A": r78.BLOCK_A_METHOD_SEEDS,   # block A: the six method arms at 1102-1104 (Part 1 §5; Part 2 §2.2)
                "B": r78.BLOCK_B_METHOD_SEEDS["A"]}   # block B under plan A (B9 and H (b): rules_78b.BLOCK_B_METHOD_SEEDS)
ARM_ORDER = tuple(r78.AB_ARM_ORDER)       # the deal's arm order (arm-major): the method arms, the doses, a0, R
ARM_DOSE = {"A1": "remove", "L1": "remove", "H1": "remove", "R": "remove", "S1": "add", "S3": "add", "S4": "add",
            "S4_96": "dose", "S4_192": "dose", "a0": "none"}
DOSE_STEPS = {"remove": r78.STEPS["remove"], "add": r78.STEPS["add"], "none": r78.STEPS["a0"],
              "dose": r78.STEPS["dose"]}  # 33, 38, 38, 39 (GXB O1: ceil(rows / 128); s4_top takes its derived steps)
GATEB_R_DRAWS = r78.BLOCK0_R_DRAWS        # the sealed R draws this round plans (1, 2, 3)
ALLOWED_REUSE = frozenset()
BLOCKS = ("0", "sc", "A", "B")            # N (ruling 11), K4b's pre-block-A scorer block (KD10; C1) and R1 K1's blocks A
#                                           and B (Part 2 §2.2); the 1B blocks refuse
BLOCKS_1B = ("S1-0", "cert", "A", "certify", "B", "C", "sim", "P")   # the stage-1 kit's; named in refusals only
WAVES = BLOCKS
FUNDING_BLOCK = {"0": "0", "sc": "sc", "A": "A", "B": "B"}   # block 0 is its own funding group (one record covers N's
#                                           two pods); each init of the scorer block carries its own funding record
#                                           (K4b); blocks A and B each their own (R1 K1; the gate funds A, block B
#                                           follows A's seal; I)
HOST_PREFIX = {"0": f"{FAMILY}-0", "sc": f"{FAMILY}-sc"} if FAMILY else {}   # hosts olmo2-7b-0-1, ...-sc-1, ...
if FAMILY:                                # R1 K1: blocks A and B's hosts ...-a-1, ...-b-1
    HOST_PREFIX.update({"A": f"{FAMILY}-a", "B": f"{FAMILY}-b"})
BLOCK_KINDS = {"0": ("arm", "a0_arm"),    # block 0: an edit arm under the main config; a0 at 1103 (Llama)
               "sc": tuple(r78.SC_KINDS),   # K4b: one single-job pod per kind (KD6), A2's order (rules_78b.SC_AFTER)
               "A": ("arm", "a0_arm"),      # R1 K1: block A's 21 arm runs per family (Part 2 §2.2)
               "B": ("arm", "a0_arm", "ref_eval", "safe_lora", "ref_train", "ref_train_bqi")}   # + the references (§3)
KINDS = tuple(r78.KINDS)                  # the 7-8B kinds (rules_78b: measured + E-capped)
KIND_IDS = {k: k for k in KINDS}          # the stage-1 J-numbers do not carry over; job_id = kind
MEASURED_KINDS = tuple(r78.MEASURED_KINDS)
E_KINDS = tuple(r78.E_KINDS)
UNMEASURED_KINDS = frozenset(r78.E_KINDS)
DIAG_KINDS = ("rep_pass", "a1_pass", "untuned_answers", "l1_scan", "classifier")   # the scorer kinds (C1; E caps; PP3)
SCORER_KINDS = tuple(r78.SCORER_KINDS)
TRAINING_KINDS = ("arm", "a0_arm")
ARM_LIKE_KINDS = ("arm", "a0_arm")
ONE_COUNTED = frozenset(r78.COUNTED_KINDS)
RETRAIN_KINDS = frozenset(r78.S78_KINDS)  # the S_78 kinds (retrain, rep_pass, a1_pass, classifier; PP8): each refuses
#                                           through rules_78b.recipe_s_or_refuse while RECIPE_S is null (A1)
POD_SIZES = {"preflight_wait_s": 5400, "container_disk_gb": r78.CONTAINER_DISK_GB, "volume_gb": r78.VOLUME_GB}
#                                           probes.py's 7B/8B preflight wait; 60 GB container; 50 GB volume (KD5)
POD_NAME_PREFIX = r78.POD_NAME_PREFIX     # "attribution-s78-": never Gate B's or stage 1's prefix
FREE_SPACE_MIN_GB = r78.FREE_SPACE_MIN_GB

# ===== K4b: the scorer block's code and inputs (the bundle; plan T4 step 3's scorer part; SCORERS-78B.md section 6
# item 10: the kit carries scripts/scale78b/scorers_78b.py and settings/ to the pod and pins them, beside the 1B
# scripts they import). The STAGE1_PINS form of the stage-1 kit (R: runkit/stage1-olmo/stage1_rules.py:581): bundle
# path -> SHA-256. M: shasum -a 256 of track M's final files (reports/m-fix.md; copied byte for byte into this
# worktree, 6 Nov 2026), round 4b's five (m-verify D4: the regenerated pins text, PINS-78B.json, the two classifier
# settings files and the wrapper's PINS_FILE_SHA256 literal; reports/k4b-fix.md) and the HEAD d203070 files they import. pack_setup.py refuses a file that differs at pack
# time; the scorer layer's own literals (PINS_FILE_SHA256, STAGE1_CODE) check the same files again on the pod.
WRAPPER = "scripts/scale78b/scorers_78b.py"
ANCHOR_SCRIPT = "scripts/make_anchor_answers.py"          # the pinned Gate B script, unchanged (Gate B's PINNED_SCRIPTS)
SCORER_SETTINGS = "scripts/scale78b/settings"
PINS_78B = f"{SCORER_SETTINGS}/pins_78b.json"
PINS_INDEX = f"{SCORER_SETTINGS}/PINS-78B.json"
SCORER_PINS = {
    "scripts/scale78b/__init__.py": "54e2663909e5fc4d8b27f1d3f473a019e14d2da5d4f88a54aa390e42a4de9fba",
    WRAPPER: "c5895adc246c26cca93b427e6ece2e136f6fe8ea566654e591d0854d6b495671",
    PINS_INDEX: "df3a787882d1c539a60b496d2f61f9ab9f3ff723e6bbf24e2ca806b20c6e9163",
    PINS_78B: "057db73b3b5ebe899a4e88e943f33c65e711228a4e176ec3f8fff5a5b5e45eab",
    f"{SCORER_SETTINGS}/build_s_pool__llama31-8b.json": "38a3c7b4bd9704624f5dc7a734807025e9a9bb512711698e6d6aed15013456c9",
    f"{SCORER_SETTINGS}/build_s_pool__olmo2-7b.json": "9fefe991ad2b125536555d1415f0b311c2177c48f4573669f37a9f4e9d75b23f",
    f"{SCORER_SETTINGS}/make_untuned_answers__llama31-8b.json": "2d32312156f16e6a074e41d06473665e5cba87f9da90b6411393669fed149d43",
    f"{SCORER_SETTINGS}/make_untuned_answers__olmo2-7b.json": "b489d00a6dce8a988c86c5045e2efe7776e3103e3317af7f69c1c39350f10a41",
    f"{SCORER_SETTINGS}/representation_pass__llama31-8b.json": "d11187be40c51cb587f045f4b45e154ba3893b35210b815a5194844104969a20",
    f"{SCORER_SETTINGS}/representation_pass__olmo2-7b.json": "492a190669198a39443f9b1f491a6182c9b096a9a0585ef440d027affa145238",
    f"{SCORER_SETTINGS}/representation_pools__llama31-8b.json": "9ae948b9a2150c018681a18e6e715050830987c03025e8580ca242cefc9edd54",
    f"{SCORER_SETTINGS}/representation_pools__olmo2-7b.json": "ff310c9c2a54053fe8da99120ea3f29c6b81e3280cec2d41b97cf5623d9c9c4d",
    f"{SCORER_SETTINGS}/score_classifier__llama31-8b.json": "625c61a3a004f3b23386a39070b859cdd7d0142ccf7d5a83f824e0a9ebc43c5d",
    f"{SCORER_SETTINGS}/score_classifier__olmo2-7b.json": "f6e883cdc9a827e0e5f176c0877185ca3eef16625b849f6c9ba4c3d029b7c582",
    f"{SCORER_SETTINGS}/score_l1_larf__llama31-8b.json": "0de7cfe5915eca98ad3a751704a4a0e9ebd96a635271beb3db0e8c9ac448befb",
    f"{SCORER_SETTINGS}/score_l1_larf__olmo2-7b.json": "9f9089f167728ef2d1e3d4b75e525a2003408c732eec1641beed4fd783a97c24",
    f"{SCORER_SETTINGS}/score_s3_datarx__llama31-8b.json": "784be58af9fd7c7d44cb934e8ca68ca7c57867f0b0f8172a100e008ab5c45c9f",
    f"{SCORER_SETTINGS}/score_s3_datarx__olmo2-7b.json": "5203499c14575a048977a8c8d7426e60aa0aabd0e1ae5f5e565799f0ef506610",
    f"{SCORER_SETTINGS}/write_add_edit__llama31-8b.json": "e2fbabf43625c53a9dce96ef06190a1fc2a20c42b37dede3f305da1c3ad9ccf0",
    f"{SCORER_SETTINGS}/write_add_edit__olmo2-7b.json": "f6420d002ca6b4cc8d277ee3973f391eedadb162432ec7eabd9ff115312c7615",
    f"{SCORER_SETTINGS}/write_score_edit__llama31-8b.json": "6c132873622bad55ec33b507afc8ac34fcb8ca2343565e87279ae772c1a4244e",
    f"{SCORER_SETTINGS}/write_score_edit__olmo2-7b.json": "56ccd80bb840f6a7abb3828f0bbc8fdae7ada4ab5b76ca32e8cd9493ad25f322",
    # the 1B scripts the wrapper runs (its STAGE1_CODE, the same SHA-256 values) and what they import or read
    "scripts/stage1/__init__.py": "86831803524affbd466f64a9de01ef543a5d955fd71f71c86bdae219a2a1f4ab",
    "scripts/stage1/s1common.py": "930c8ea53d26baeeccaf2035949427d207f307ba0fec06ff0dec841c8c824552",
    "scripts/stage1/labels.json": "260389f3fbfd8e7ff11ee06b5d5aba48e7d56b34140d9c9a634682125a86d570",
    "scripts/stage1/lexicon_pin.py": "bf4412211c5ff681f41c9ae40bfe8d5078964942fa034645daed96e1a0681634",
    "scripts/stage1/lexicon/lexicon.json": "bbbc71e9eebb62876430ffb5e0f54113c3818984b8369924b7bd2212c4c1ca17",
    "scripts/stage1/lexicon/lexicon.py": "5a27dd040b74aa23fe09ac4dc95fb5913a4ccd327a67bb3caf5e667ff0432d1b",
    "scripts/stage1/token_accounting.py": "b9a51f6fc66fb3011c7448d0869f65848d407fa4d901ba10216312e0a93a6024",
    "scripts/stage1/make_untuned_answers.py": "c37ac452b931c84ed28b45e9cfeed9cc9a07ec47ce5f1c6fd1bbef95086743c4",
    "scripts/stage1/representation_pass.py": "fb62bcaaaa35595a52de5a4217754cb390ffb4ba49e04dec6e515d7e3cebb8d9",
    "scripts/stage1/score_l1_larf.py": "4996fd3bfdd854ecd82630813f7f9b0dab88c4e7e26f81366c566b93c70e95e5",
    "scripts/stage1/score_classifier.py": "ee8ae89865e188a8e9f3430c9fbfbe129a415dcc9f3427111a7c77e02dc34549",
    "scripts/stage1/score_s3_datarx.py": "772e6ae546843b42c3a7564a644cffa269c38ffb30f4db0d59f0f405a9d5aace",
    "scripts/stage1/write_score_edit.py": "2721dbe7239e297b8771795efe04e280297e2e601d65499807f47be4ecf7ead5",
    "scripts/stage1/write_add_edit.py": "8b866b3d22bd0656bccd8dbb21ccabde3fda2726b85f149711455836928ad27c",
    "scripts/stage1/build_s_pool.py": "cb2ca385a3917d0f4be041ae08b1e121bc67f82a7fc95165e33550f053f463df",
    ANCHOR_SCRIPT: "5a686a82eb80d0a6da3f4f232b31bcda7c7840ced0038f666fe2a0e4a4d34146",
}
WRAPPER_KINDS = {"untuned_answers": ("make_untuned_answers",), "rep_pass": ("representation_pass", "representation_pools"),
                 "l1_scan": ("score_l1_larf",), "classifier": ("score_classifier", "representation_pools")}
WRAPPER_COMMAND = {"untuned_answers": "untuned_answers", "rep_pass": "rep_pass", "l1_scan": "scan",
                   "classifier": "classifier"}        # the scorer layer's command name its settings' waits key on
WRAPPER_RECORD = "wrapper_78b_record.json"            # scorers_78b.WRAPPER_RECORD (the runner reads it by key)
UNTUNED_CALLS = ("untuned", "untuned-s4")             # PP2: the S3 call's and the S4 call's --out folders


def scorer_code(kind: str) -> list[str]:
    """The SCORER_PINS files a scorer-block job runs or reads on the pod: every wrapper kind the whole wrapper set (the
    wrapper, its settings index and pins, the settings files, the 1B scripts it imports); the anchor job its script;
    the engine's own kinds (retrain, a1_pass) nothing beyond the engine; o_only, o_only_with_regenerate (PP17) and c0
    the files of rules_78b.OEXT_78B[family] (null until filled; their jobs refuse until then)."""
    if kind in WRAPPER_KINDS:
        return sorted(p for p in SCORER_PINS if p != ANCHOR_SCRIPT)
    if kind == "anchor":
        return [ANCHOR_SCRIPT]
    if kind in OEXT_KINDS:
        oext = r78.OEXT_78B.get(FAMILY) if FAMILY else None
        return sorted((oext or {}).get("files") or {})
    return []


# The named inputs of each scorer-block kind (sealed-files.json "inputs": name -> bundle path; the pack's --inputs
# record names each by {name, path, sha256}). Their pins (sc_input_pins): the 1B sealed lists and the anchor prompt
# list from pins_78b.json shared (the scorer layer's record of them); the anchor bank, the untuned pass's s3_orig pool
# and the retrain's unit from the family's pins_78b.json block (null until their events); N's R_1-1101 unit from
# rules_78b.C0_SOURCE; the O-ext bank and record from rules_78b.OEXT_78B (null until M1's re-derivation); the reused a0
# side unit's COMPLETE.json (o_only_with_regenerate's acceptance check, PP17) by its KIT a0_units pin (ruling 7).
OEXT_KINDS = ("o_only", "o_only_with_regenerate", "c0")   # the kinds that run the S1 package's O-ext code (OEXT_78B)
SIDE_COMPLETE = "side_complete:a0:{seed}"             # o_only_with_regenerate's input: the side unit's COMPLETE.json
N_COMPLETE = "n_complete:{arm}:{seed}"                # R1 K1 (DES E5): N's unit's COMPLETE.json (its acceptance input)
REGEN_EDIT = "regen_edit:R:{seed}"                    # R1 K1: an N R unit's sealed R_d edit (its regeneration's input)
SC_INPUTS = {"anchor": ("anchor_prompts",), "untuned_answers": ("list:s3", "loss:s1", "loss:s3_safe", "list:s4"),
             "o_only": ("oext_bank", "oext_record"),
             "o_only_with_regenerate": (SIDE_COMPLETE, "oext_bank", "oext_record"),
             "c0": ("source_complete:R:1101", "oext_bank", "oext_record"), "l1_scan": ("anchor_bank",),
             "rep_pass": ("anchor_bank", "pool:s3_safe", "pool:s3_orig"), "classifier": ("anchor_bank",),
             "retrain": (), "a1_pass": ("anchor_bank", "retrain_unit"),
             "w1_18": ()}                          # R1 K1: its units and settings are W1_18_78B's pinned files (K3)
SC_FOLDER_INPUTS = frozenset({"retrain_unit"})        # a unit folder: its pin is its COMPLETE.json's SHA-256


def _unit_source(kind: str, seed, arm) -> str | None:
    """R1 K1, the seed key: the source of o_only_with_regenerate's unit (arm, seed) in this copy's family ("side" or
    "n"). The seed-only call (no arm) is the K4b side-unit form that today's runner, pack and planner still make; new
    callers use sc_unit_input_names / sc_unit_input_pins, which refuse a missing arm (K1V-9)."""
    if kind != "o_only_with_regenerate" or arm is None:
        return "side" if kind == "o_only_with_regenerate" else None
    return r78.sc_unit_source(family_or_refuse(), kind, arm, seed)


def sc_input_names(kind: str, seed=None, arm=None) -> tuple:
    """The named inputs of a scorer-block job of ``kind`` at ``seed`` (SC_INPUTS with the seed filled in). R1 K1:
    o_only_with_regenerate's inputs are keyed by (arm, seed) (DES E5; GXB's seed key): a side unit (arm a0, or no arm)
    takes side_complete:a0:<seed>; one of N's units takes n_complete:<arm>:<seed> and, for an R unit, its sealed R_d
    edit regen_edit:R:<seed>; then the O-ext bank and record."""
    if _unit_source(kind, seed, arm) == "n":
        names = (N_COMPLETE.format(arm=arm, seed=seed),) + ((REGEN_EDIT.format(seed=seed),) if arm == "R" else ())
        return names + ("oext_bank", "oext_record")
    return tuple(n.format(seed=seed) if n == SIDE_COMPLETE else n for n in SC_INPUTS[kind])


def sc_unit_input_names(kind: str, arm, seed) -> tuple:
    """K1V-9, the seed key without a default: the named inputs of a scorer-block job's unit named by (arm, seed). For
    o_only_with_regenerate a missing arm refuses (ValueError), and so does an (arm, seed) that is not one of its units;
    the other kinds take their own arm (SC_ARM) or none. K2's planner, the pack and K3's runner call this form; the
    seed-only form sc_input_names(kind, seed) stays only for the call sites the kit test lists until they move."""
    if kind == "o_only_with_regenerate":
        if arm is None:
            raise ValueError("o_only_with_regenerate names its unit by (arm, seed): the arm is missing (GXB's seed key)")
        try:
            r78.sc_unit_source(family_or_refuse(), kind, arm, seed)
        except r78.Refused as exc:
            raise ValueError(str(exc)) from None
    return sc_input_names(kind, seed, arm)


def sc_unit_input_pins(kind: str, pins78: dict, values: dict, arm, seed) -> dict:
    """sc_input_pins with the unit named by (arm, seed) (K1V-9: no default arm; see sc_unit_input_names)."""
    sc_unit_input_names(kind, arm, seed)
    return sc_input_pins(kind, pins78, values, seed, arm)


def sc_input_pins(kind: str, pins78: dict, values: dict, seed=None, arm=None) -> dict:
    """name -> the SHA-256 the job's input must have (None while its pin is null), for ``kind``'s inputs at ``seed``
    (and ``arm``: R1 K1's (arm, seed) key; N's unit pins come from values["N_UNITS"], null until block 0's
    record-done). ``values`` is rules_78b.sc_pin_values(family, pins78)."""
    shared = pins78.get("shared") if isinstance(pins78, dict) else None
    lists = (shared or {}).get("sealed_lists_1b") or {}
    oext = (values.get("OEXT_78B") or {}).get("inputs") or {}
    c0 = values.get("C0_SOURCE") or {}
    table = {"list:s3": (lists.get("s3_safe") or {}).get("sha256"), "loss:s3_safe": (lists.get("s3_safe") or {}).get("sha256"),
             "pool:s3_safe": (lists.get("s3_safe") or {}).get("sha256"), "loss:s1": (lists.get("s1") or {}).get("sha256"),
             "list:s4": (lists.get("s4_candidates") or {}).get("sha256"),
             "anchor_prompts": (shared or {}).get("anchor_prompt_list_sha256"),
             "anchor_bank": values.get("ANCHOR_BANK"), "pool:s3_orig": values.get("S3_ORIG_POOL"),
             "retrain_unit": values.get("RETRAIN_UNIT"), "source_complete:R:1101": c0.get("complete_sha256"),
             "oext_bank": oext.get("oext_bank"), "oext_record": oext.get("oext_record")}
    source = _unit_source(kind, seed, arm)
    if source == "n":                                    # R1 K1 (DES E5): N's unit, by its (arm, seed) key
        unit = ((values.get("N_UNITS") or {}).get(r78.unit_key(arm, seed))) or {}
        table[N_COMPLETE.format(arm=arm, seed=seed)] = unit.get("complete_sha256")
        if arm == "R":
            table[REGEN_EDIT.format(seed=seed)] = unit.get("edit_sha256")
    elif seed in A0_UNITS and seed != "untuned":         # PP17: the reused side unit's COMPLETE.json (ruling 7's pin)
        table[SIDE_COMPLETE.format(seed=seed)] = A0_UNITS[seed]["complete_sha256"]
    out = {}
    for name in sc_input_names(kind, seed, arm):
        pin = table.get(name)
        out[name] = pin if hex64(pin) else None
    return out


def wrapper_settings_waits(kind: str, settings_docs: dict) -> list[tuple[str, str]]:
    """(dotted path, event) of every null pin the scorer layer's settings hold for ``kind``'s command (the settings'
    family_78b.waits; scorers_78b.null_pins's rule): the wrapper refuses those on the pod, so the kit refuses them at
    planning. ``settings_docs`` maps a settings script name to its family document (read at its SCORER_PINS pin)."""
    out = []
    command = WRAPPER_COMMAND[kind]
    for script in WRAPPER_KINDS[kind]:
        doc = settings_docs[script]
        waits = ((doc.get("family_78b") or {}).get("waits") or {})
        for dotted, entry in sorted(waits.items()):
            needed = entry.get("needed_by", []) if isinstance(entry, dict) else []
            if "*" not in needed and command not in needed:
                continue
            node = doc
            for key in dotted.split("."):
                node = node.get(key) if isinstance(node, dict) else None
            if node is None:
                out.append((f"{script}: {dotted}", entry.get("event", "")))
    return out


# ===== kept for the copied modules (the launch path, the runner, the seal, the judge route) =========================
TOKEN_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
STATUSES = ("planned", "complete", "crashed", "deferred", "not_started")
BOOTSTRAP_FIELDS = ("lock_sha256", "pip_version", "gpu", "cuda_runtime")
LOG_ONLY_FIELDS = ("pip_version",)
LINKED_KINDS: dict = {}                   # no linked pass in block 0 (the stage-1 J3 O-only link comes with its kind)
LINK_SOURCES = frozenset()
LINK_FIELD = "regen_source"
# The core verifier's D8 and PP18: a1_pass writes an engine attributes unit (the runner records it by its COMPLETE.json
# and the engine's verify, as the 1B kit's a1_rescore), so it is not unitless; c0 is unitless (PP18: the runner
# hashes its outputs under its job folder, as the 1B kit did, R: runkit/stage1-olmo/stage1_rules.py:623).
UNITLESS_KINDS = frozenset({"untuned_answers", "rep_pass", "l1_scan", "classifier", "anchor", "o_only", "c0"})
BANK500_KINDS = frozenset(r78.BANK500_KINDS)   # R1 K1: the kinds whose every job reads the 500 bank (the O-ext pass);
#                                           block A and B arm jobs read it too (rules_78b.bank500_job; block 0 never)
BRANCHES = tuple(r78.BRANCHES)            # ("full", "128"): W1-18's branch per family (DES E2; GXB O4)
BRANCH_DEFAULT = r78.BRANCH_DEFAULT       # "full" until the family's branch record
X_ONLY_KINDS = ()
Y_ONLY_KINDS = ()
POINT_KINDS = {"ref_eval": None, "safe_lora": ("default", "conditional", "certify", "k12")}
REF_EVAL_SCALES = ("scale:0.9", "scale:0.75", "scale:0.5")
JUDGED_RUN_KINDS = ("arm", "a0_arm")
JUDGED_B10_KINDS = ("ref_eval", "safe_lora")
B10_UNIT_KINDS = ("ref_eval", "safe_lora")
# N has no re-judged unit (its R arms are judged with block A's pods, A9). R1 K1 (Part 2 §6; DESO item 26): block A
# re-judges N's units, the reused a0 side units and theta0, 7 per family (rules_78b.rejudged_pins: N's entries null
# until block 0's record-done; rules_78b.rejudged_or_refuse refuses a judge launch until then); block B none.
REJUDGED_PINS = {"0": (), "A": r78.rejudged_pins(FAMILY, "A") if _KIT else (), "B": ()}
NOT_RUN_KIND = "stage1 not-run decision"
NOT_RUN_KEYS = ("kind", "block", "jobs", "reason", "utc", "recorded_by")
A0_FINGERPRINT_RECORD = "a0-adapter-fingerprint.json"
A0_FINGERPRINT_KIND = "stage1 a0 adapter fingerprint"
ARM_FINGERPRINT_RECORD = "arm-adapter-fingerprint.json"
ARM_FINGERPRINT_KIND = "stage1 arm adapter fingerprint"
PLANT_ARMS = frozenset()                  # K2: no plant arm at 7-8B (plan_tool.record_done reads it for every arm job)
UNITS = 8                                 # the prepared sets' 8 unit groups (both manifests; P78:343)
# the judge route (T4 step 5: unchanged; Gate B's write_files.py names; a stage-1 test compares them to Gate B's file)
GRANITE_SETUP_UPPER_S = 1800
GRANITE_S_PER_ANSWER = 0.5
GRANITE_MARGIN_S = 900
GRANITE_CAP_MIN_H, GRANITE_CAP_MAX_H = 1.0, 6.0
GRANITE_GREEDY_PER_ARM = 200
GRANITE_KNOWN_ANSWERS = 200
HARMBENCH_S_PER_ANSWER = 0.25
HARMBENCH_ANSWERS_PER_ARM = 800
JUDGES = ("harmbench", "granite")
JUDGE_INDEX = "judge-files-index.json"
JUDGE_INDEX_KIND, JUDGE_INDEX_VERSION = "gate-b judge files index", 2
JUDGE_INDEX_ENTRY_KEYS = ("complete_sha256", "completed_utc", "file", "host", "judge", "arm", "seed", "sha256",
                          "target", "unit")
JUDGE_FILE_PATTERN = r"^(granite|harmbench)--.+--[0-9a-f]{12}\.json$"
JUDGE_NAMES = {"harmbench": "cais/HarmBench-Mistral-7b-val-cls", "granite": "granite-guardian-3.3-8b"}
JUDGE_TAG_PATTERN = r"^[a-z0-9][a-z0-9-]{0,38}[a-z0-9]$"
JUDGE_GPU = "NVIDIA A100-SXM4-80GB"
JUDGE_RECORD_KIND = "stage1 judge completion record"
JUDGE_RECORD_KEYS = ("kind", "block", "judges", "index_sha256", "utc", "recorded_by")
JUDGE_ENTRY_KEYS = {"harmbench": ("tag", "result_sha256", "run_record_sha256", "bundle_sha256", "exit", "judged",
                                  "complete"),
                    "granite": ("tag", "result_sha256", "run_record_sha256", "bundle_sha256", "exit", "judged",
                                "complete", "known_answer_passed")}


# ===== the guard-off record (unchanged from the stage-1 kit) ========================================================
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


# ===== small helpers (the stage-1 kit's, unchanged) =================================================================
def finite_number(value) -> bool:
    """A finite, non-boolean int or float. An int too large for a float (10**400) is not one."""
    import math
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def hex64(value) -> str | None:
    """``value`` if it is a lowercase SHA-256 hex string, else None."""
    return value if isinstance(value, str) and len(value) == 64 and not set(value) - set("0123456789abcdef") else None


def canonical_bytes(obj) -> bytes:
    """The engine's canonical JSON: sorted keys, 2-space indent, UTF-8, a trailing newline; NaN and infinity refused."""
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def compare(new: dict, reference: dict, fields) -> dict:
    """Field names (never values) that differ, that are missing, and the log-only differences."""
    missing = sorted(f for f in fields if new.get(f) is None)
    differ = sorted(f for f in fields if f not in missing and new.get(f) != reference.get(f))
    logged = [f for f in differ if f in LOG_ONLY_FIELDS]
    stopping = [f for f in differ if f not in LOG_ONLY_FIELDS]
    return {"differ": stopping, "missing": missing, "logged": logged, "stop": bool(stopping or missing)}


def r_draw(seed: int) -> int:
    """R_d runs at seed 1100 + d."""
    return seed - R_SEED_BASE


def plan_code_for(sigma_pp: float) -> str:
    """The seed rule (ruling 3; P78 §4): sigma <= 4.5 pp -> "A"; <= 6.0 -> "B9"; above -> "H" (the high-noise
    branch, ruling 4). Kept as a pure function; N's reading (scripts/scale78b/noise_reading.py) applies it."""
    if not finite_number(sigma_pp) or sigma_pp < 0:
        raise ValueError("sigma must be a finite number of percentage points")
    return "A" if sigma_pp <= 4.5 else "B9" if sigma_pp <= 6.0 else "H"


# ===== block tables ================================================================================================
def block_runs(plan_code: str | None, block: str, reused: tuple = (), dose_seeds: int = 0,
               kept: int | None = None) -> list[tuple[str, int]]:
    """The runs (arm, seed) of a block of THIS copy's family. Block "0" = N (rules_78b.block0_runs: R_1-R_3 at
    1101-1103; a0 at 1103 on Llama-3.1-8B). R1 K1: blocks "A" and "B" = rules_78b.block_runs_78b (Part 2 §2.2; block
    B by ``plan_code``, block B's plan record's plan, with ``dose_seeds`` 0, 3 or 6 and the kept S4 count ``kept``). The 1B blocks refuse: they belong to
    runkit/stage1-olmo/."""
    if block in ("A", "B"):
        if reused:
            raise ValueError(f"block {block} reuses no unit (Part 2 §2.2: every block A and B run is new)")
        try:
            return r78.block_runs_78b(family_or_refuse(), plan_code, block, dose_seeds, kept)
        except r78.Refused as exc:
            raise ValueError(str(exc)) from None
    if block != "0":
        where = "runkit/stage1-olmo/" if block in BLOCKS_1B else "no 7-8B block table"
        raise ValueError(f"block {block!r} is not planned by this copy (block 0 only, or blocks A and B; ruling 11); "
                         f"it belongs to {where}")
    if reused:
        raise ValueError("block 0 reuses no unit: its R arms are new runs (ruling 7 reuses the a0 side units, not R)")
    return r78.block0_runs(family_or_refuse())


def deal(runs: list, block: str = "0") -> list[list]:
    """N's one pod per family (ruling 11): the runs in N's order, on one pod. A run outside N's table, one listed
    twice, or a layout that is not N's refuses (outcome-free and fixed before launch). R1 K1: blocks "A" and "B" take
    the interleaving deal (rules_78b.deal_ab: arm-major, seed-minor, run i to pod i mod P; at most 4 per pod)."""
    if block in ("A", "B"):
        try:
            return r78.deal_ab(runs)
        except r78.Refused as exc:
            raise ValueError(str(exc)) from None
    if block != "0":
        raise ValueError(f"block {block!r} has no deal here")
    expected = block_runs(None, "0")
    given = [tuple(r) for r in runs]
    if len(set(given)) != len(given):
        raise ValueError("a run is listed twice")
    if sorted(given) != sorted(expected):
        raise ValueError(f"block 0's runs are N's layout for {FAMILY} only: {expected}")
    return [list(expected)]


def split_pods(jobs: list) -> list[list]:
    """Gate B's contiguous split (kept for its name)."""
    out, start = [], 0
    for size in pod_sizes(len(jobs)):
        out.append(list(jobs[start:start + size]))
        start += size
    return out


def stream_steps(arm: str) -> int:
    """e1's step by the arm's dose (PR4 §1.1: 600 removed -> 33, 48 added -> 38, none -> 38)."""
    return DOSE_STEPS[ARM_DOSE[arm]]


# ===== jobs, caps and money: rules_78b's M-cap rule (KD1) ==========================================================
hours = r78.hours
round_up_s = r78.round_up_s
pod_sizes = r78.pod_sizes
guard_usd = r78.guard_usd
cents = r78.cents
funding_need_usd = r78.funding_need_usd
launch_pod_spend_usd = r78.launch_pod_spend_usd
gate = r78.gate
arm_count = r78.arm_count
Refused = r78.Refused


def counted(kind: str, n_points: int = 1) -> int:
    """What a job counts toward MAX_ARMS_PER_POD (rules_78b.COUNTED_KINDS; a point kind counts its points)."""
    if kind in POINT_KINDS:
        if type(n_points) is not int or n_points < 1:
            raise ValueError(f"{kind}: at least one evaluation point")
        return n_points
    return 1 if kind in ONE_COUNTED else 0


def steps_for(kind: str, arm: str | None, steps: int | None) -> int | None:
    """The step count of a job: the given one, else by the arm's dose (arm), 38 for a0_arm and the train-only kinds,
    None for the evaluation-only and E kinds that have none."""
    if steps is not None:
        return steps
    if kind == "arm" and arm in ARM_DOSE:
        return stream_steps(arm)
    if kind in ("a0_arm", "retrain", "o_only_with_regenerate", "ref_train_bqi", "safe_lora", "ref_train"):
        return DOSE_STEPS["none"]
    return None


def job_record(kind: str, arm: str | None = None, seed: int | None = None, edit=None, steps: int | None = None,
               fixture: dict | None = None, a0_source: int | None = None, *, branch=None, engine: str = ENGINE_DEFAULT,
               points: list | None = None, recipe: str | None = None, regen_source: int | None = None,
               family: str | None = None, padded_tokens_per_step: float | None = None, oext: bool = False) -> dict:
    """One plan job in the stage-1 kit's shape, its timing from rules_78b.job_record (KD1): upper_s,
    start_requirement_s, measured_upper_s, spend_upper_s, counted, unmeasured; plus the kit's fields (job_id, arm,
    seed, edit, engine, recipe, points, status). ``fixture``, ``branch`` and ``a0_source`` are the stage-1 signature's
    and are not read (no fixture prices a 7-8B job). A kind that needs a null pin (the retrain, A1's pass, B+Qi) is
    still priced here (M3's need) and refuses at planning through plan_tool and at the pod through rules_78b. R1 K1:
    ``padded_tokens_per_step`` is train_scale's input (Part 2 §2.1) and ``oext`` plans the in-job O-ext step with its
    cap term (blocks A and B; DES E3)."""
    fam = family_or_refuse(family)
    n = len(points) if points else 1
    rec = r78.job_record(fam, kind, steps_for(kind, arm, steps), arm, seed, padded_tokens_per_step, n_points=n,
                         oext=oext)
    job = {**rec, "job_id": KIND_IDS[kind], "edit": edit, "engine": engine, "branch": branch,
           "recipe": recipe if recipe is not None else ("B" if kind in TRAINING_KINDS else None),
           "points": list(points) if points else None, "o500_s": 0.0, "status": "planned"}
    if regen_source is not None:
        job[LINK_FIELD] = regen_source
    return job


def requirements(jobs: list[dict], projection: dict | None = None) -> list[float]:
    """Each job's start requirement at s = 1 (rules_78b.requirements). The pod's preflight projection is applied by
    the job runner through rules_78b.job_decision (s_pod, the sanity floor); it is not read here."""
    return r78.requirements(jobs)


def projected_requirement_s(job: dict, projection: dict | None) -> float | None:
    """The stage-1 name: at 7-8B the pod-side requirement is rules_78b.requirement_s with the preflight's fields
    (job_decision); here the plan value is returned for the measured kinds, None for an E kind (its explicit window)."""
    if job.get("unmeasured"):
        return None
    return job["start_requirement_s"]


def own_requirement_s(job: dict, projection: dict | None = None) -> float:
    return job["start_requirement_s"]


def linked_follower(jobs: list[dict], index: int) -> int | None:
    """No linked pass in block 0 (LINKED_KINDS is empty): None."""
    for later in range(index + 1, len(jobs)):
        if LINKED_KINDS.get(jobs[later]["kind"]) == jobs[index]["kind"] and jobs[later].get(LINK_FIELD) == index:
            return later
    return None


linked_diagnostics = linked_follower


def cap_hours(jobs: list[dict]) -> float:
    """KCR §4 through rules_78b.cap_hours: 48 min + the measured uppers of the jobs before k + job k's requirement,
    the largest over k, rounded up to 0.25 h; at most 4 counted jobs; an E kind alone; one family per pod."""
    try:
        return r78.cap_hours(jobs)
    except r78.Refused as exc:
        raise ValueError(str(exc)) from None


def pod_spend_usd(kinds: list) -> float:
    """One pod's upper spend: (48 min + its jobs' spend uppers) x $1.79; ``kinds`` are the pod's job records."""
    if not all(isinstance(k, dict) for k in kinds):
        raise ValueError("a 7-8B pod's spend needs its job records")
    return r78.pod_spend_usd(kinds)


def rerun_cost_usd(kind, new_pod: bool) -> float:
    """A re-run's upper spend, paid from the contingency: its spend upper x $1.79, plus 48 min when it needs a new pod."""
    if not isinstance(kind, dict):
        raise ValueError("a 7-8B re-run's cost needs its job record")
    return hours(kind["spend_upper_s"] + (POD_OVERHEAD_S if new_pod else 0)) * RATE_USD


def unit_rerun_cost_usd(kinds: list, new_pod: bool) -> float:
    """A pre-job requeue's jobs paid as one unit: the sum of the one-by-one costs (the 48 min on the first only)."""
    return sum(rerun_cost_usd(k, new_pod and i == 0) for i, k in enumerate(kinds))


def default_jobs(kinds: list[str], fixture: dict | None = None, arm_steps: int = 33, retrain_steps: int = 38,
                 branch=None) -> list[dict]:
    """Jobs of the given kinds with the default timing (the stage-1 name; no fixture is read)."""
    return [job_record(k, None, None, None, arm_steps if k == "arm" else retrain_steps if k in ("a0_arm", "retrain")
                       else None) for k in kinds]


def block_jobs(plan_code: str | None, block: str, padded_tokens: dict | None = None, dose_seeds: int = 0,
               kept: int | None = None) -> list[dict]:
    """R1 K1: the job records of block A or B of this copy's family (Part 2 §2.1-§2.3), in block_runs' order. Each
    edit arm trains on its edit (rules_78b.run_edit: by path and SHA-256 only; a null method-edit pin refuses with its
    event) at the steps derived from the edit's rows (GXB O1), with its in-job O-ext step and train_scale's input
    ``padded_tokens[(arm, seed)]`` (a missing count refuses); a0 at 38 steps, train_scale 1. Each job is in the kit's
    shape (job_record) with its bound edit {path, sha256, engine_arm}."""
    fam = family_or_refuse()
    padded_tokens = padded_tokens or {}
    out = []
    for arm, seed in block_runs(plan_code, block, (), dose_seeds, kept):
        try:
            rec = r78.block_job_78b(fam, arm, seed, padded_tokens.get((arm, seed)))
        except r78.Refused as exc:
            raise ValueError(str(exc)) from None
        edit = rec["edit"]
        job = job_record(rec["kind"], arm, seed, None if edit is None else {"path": edit["path"],
                         "sha256": edit["sha256"], "engine_arm": edit["engine_arm"]}, rec["steps"], family=fam,
                         padded_tokens_per_step=rec["padded_tokens_per_step"], oext=True)
        job["train_scale"] = rec["train_scale"]
        job["block"] = block
        out.append(job)
    return out


def block_pods(plan_code: str | None, block: str, padded_tokens: dict | None = None, dose_seeds: int = 0,
               kept: int | None = None) -> list[dict]:
    """R1 K1 (Part 2 §2.4): block A's or B's pods: the deal of its runs (at most 4 counted per pod, arms interleaved,
    33-, 38- and 39-step arms mixed), each pod's cap from its jobs' own steps and O-ext terms (rules_78b.cap_hours),
    its guard and spend upper."""
    jobs = {(j["arm"], j["seed"]): j for j in block_jobs(plan_code, block, padded_tokens, dose_seeds, kept)}
    pods = []
    for runs in deal(list(jobs), block):
        pod_jobs = [jobs[r] for r in runs]
        cap = cap_hours(pod_jobs)
        pods.append({"runs": runs, "jobs": pod_jobs, "cap_hours": cap, "guard_usd": cents(guard_usd(cap)),
                     "spend_usd": cents(pod_spend_usd(pod_jobs)), "counted": arm_count(pod_jobs)})
    return pods


def block_init(block: str, gate_bytes: bytes, plan_b_bytes: bytes | None = None, family: str | None = None) -> dict:
    """R1 K1 (GXB O14, corrected): what block A's or B's init reads: block A the gate record's families (its bytes read
    at GATE_78B's path); block B also its plan from block B's plan record (read at PLAN_B_78B's path; "review" plans
    nothing); Refused (ValueError) before each pin is filled."""
    try:
        return r78.block_init_or_refuse(block, family_or_refuse(family), gate_bytes, plan_b_bytes)
    except r78.Refused as exc:
        raise ValueError(str(exc)) from None


def retrain_job(seed: int = 1101, family: str | None = None) -> dict:
    """Ruling 10, addendum A2 and A8: the a0-1101 retrain (train only, recipe S_78, engine Y) on its own single-job
    pod. It is priced (rules_78b's retrain E cap, 4.5 h) and REFUSES to be planned while the family's RECIPE_S pin is
    null (addendum A1: rules_78b.recipe_s_or_refuse). Its pod's need is printed by init-block 0 (M3) all the same."""
    fam = family_or_refuse(family)
    if r78.family_stopped(fam):                        # R1 K1 (DESO2 item 36 (2)): the MAIN_F retrain on a stopped
        return job_record("retrain", "a0", seed, None, DOSE_STEPS["none"], family=fam, recipe="B")   # family
    r78.recipe_s_or_refuse(fam)                        # Refused while RECIPE_S[family] is None
    return job_record("retrain", "a0", seed, None, DOSE_STEPS["none"], family=fam)


def block0_need_report(family: str | None = None) -> dict:
    """The money of block 0 and the first days after it, each part separately (the check's M3; ruling 11; addendum A8):
    N's two pods (both families, one launch; KCR:177: $56.06 with the contingency), this family's pod alone, each
    family's retrain pod and each scorer pod (rules_78b.block0_report), with one labelled line per part."""
    fam = family_or_refuse(family)
    report = r78.block0_report()
    n = report["n"]
    mine = next(p for p in n["pods"] if p["family"] == fam)
    alone = funding_need_usd([[{"cap_hours": mine["cap_hours"], "spend_usd": mine["spend_usd"]}]], CONTINGENCY_FACTOR)
    lines = [f"need N (block 0, both families, one launch of {len(n['pods'])} pods; KCR:177): ${n['need_usd']:.2f} "
             f"(guard ${n['guard_usd']:.2f}, spend upper ${n['spend_upper_usd']:.2f}, contingency "
             f"${cents(n['need_usd'] - n['base_need_usd']):.2f})",
             f"need N this family's pod alone ({mine['host']}, cap {mine['cap_hours']:.2f} h, spend upper "
             f"${mine['spend_usd']:.2f}): ${alone['need_usd']:.2f}"]
    for f, pod in report["retrain_pods"].items():
        lines.append(f"need retrain pod {f} (a0-1101, engine Y, recipe S_78 after the anchor job; ruling 10, addendum "
                     f"A2, A8; cap {pod['cap_hours']:.2f} h, guard ${pod['guard_usd']:.2f}): ${pod['need_usd_alone']:.2f}")
    for f, kinds in report["scorer_pods"].items():
        for kind, pod in kinds.items():
            label = r78.KIND_LABELS.get(kind, kind)
            n_pods = len(r78.sc_seeds(f, kind))      # PP17: o_only_with_regenerate has one pod per reused a0 seed
            each = f"{n_pods} pods, one per reused a0 seed, each: " if kind in r78.SC_PER_SEED_KINDS else ""
            lines.append(f"need scorer pod {f} {kind} ({label}; {each}single-job E cap {pod['cap_hours']:.2f} h, guard "
                         f"${pod['guard_usd']:.2f}; KD6, the check's C1 and M3): ${pod['need_usd_alone']:.2f}")
    idle = report["idle_storage"]                      # KD5's idle-storage line (D2; Part 1 §12; KCR:161)
    lines.extend(r78.idle_storage_lines(report))        # N's line, then PP14's line per other pod that keeps states
    return {"family": fam, "n": n, "this_pod_need_usd": alone["need_usd"], "retrain_pods": report["retrain_pods"],
            "scorer_pods": report["scorer_pods"], "idle_storage": idle,
            "idle_storage_pods": report["idle_storage_pods"], "idle_storage_all": report["idle_storage_all"],
            "lines": lines}


# ===== the engine's command lines for an arm (P78:99; the runner calls this; a test holds the shape) ================
ENGINE_ARGV = ["venv/bin/python", "-m", "experiments.safety_selection"]
ROUND_DIR = "round1"


def engine_arm(job: dict) -> str | None:
    """The engine's arm id of an edit job: edit-<SHA-256 of the edit file> (a0 jobs: "a0")."""
    edit = job.get("edit")
    if not edit:
        return "a0" if job.get("arm") == "a0" or job["kind"] == "a0_arm" else None
    return edit.get("engine_arm") or f"edit-{edit['sha256']}"


def arm_commands(job: dict, prepared: str, family: str | None = None) -> list[tuple[str, list[str]]]:
    """The calibrate command of one block-0 job on the pod: the engine's ``calibrate`` with the FAMILY'S MAIN config
    (REC, P78:99: never a recipe-S sibling), the edit bundle edits/<SHA-256>.edit.json for an edit arm (none for
    a0), the job's seed, checkpoint e1 and the round folder. Refuses a kind outside block 0, a recipe other than "B",
    an edit arm without its bound edit, or a job of another family."""
    fam = family_or_refuse(family)
    if job.get("family") not in (None, fam):
        raise ValueError(f"the job is {job.get('family')}'s; this copy is {fam}'s")
    if job["kind"] not in BLOCK_KINDS["0"]:
        raise ValueError(f"{job['kind']} is not a block-0 kind ({', '.join(BLOCK_KINDS['0'])})")
    if job.get("recipe") != "B":
        raise ValueError("an arm runs under the family's main config (recipe B; P78:99), never another recipe")
    arm = engine_arm(job)
    if job["kind"] == "arm" and (not job.get("edit") or not hex64(job["edit"].get("sha256"))):
        raise ValueError("an edit arm needs its bound edit {path, sha256}")
    if job["kind"] == "a0_arm" and (job.get("arm") != "a0" or job.get("edit")):
        raise ValueError("an a0_arm is a0 without an edit")
    edit = ["--edit", f"edits/{job['edit']['sha256']}.edit.json"] if job.get("edit") else []
    argv = [*ENGINE_ARGV, "calibrate", "--prepared", prepared, "--recipe", REC, "--arms", arm, *edit,
            "--seeds", str(job["seed"]), "--checkpoints", "e1", "--out-root", ROUND_DIR]
    return [("calibrate", argv)]
