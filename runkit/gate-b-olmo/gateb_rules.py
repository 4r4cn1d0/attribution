"""The Gate B kit's rules (brief gate-b-engine-kit-reading-20261008, Part B: B1, B3, B4, B5; stdlib only).

This module runs on the Mac (plan_tool, orchestrate, launch) and on the pod (the job runner imports it from the
setup folder), so the per-job gate, the caps and the environment comparison are one implementation. Every DRAFT
constant is in the ONE block below (a one-place edit at the user's review); the administrative names follow it.

Per job (B3): ``upper_s`` is arm: the fixture's e1_upper_s + training_s x steps/38 + 1,000 + 900; retrain:
training_s x steps/38 + 1,000 + 900; diagnostics: 1.5 x its 2.0 h measured upper = 3.0 h ([D11], [D13]); anchor:
0.25 h. ``start_requirement_s`` = upper_s + 1,800: an arm needs 2.32 h at 33 steps and 2.33 h at 38 ([D11] B-5),
the retrain 1.12 h, the diagnostics 3.5 h, the anchor 0.75 h. On a pod a
job needs max(its plan value, this pod's preflight projection); the retrain needs max(its own, its measured upper +
the diagnostics' requirement) when a later diagnostics job names it (``a0_source``), so the pair starts together or
not at all. A missing or unreadable remaining time never fits.

Cap (B4): the largest, over a host's jobs k, of 42 min + the measured uppers of the jobs before k + job k's start
requirement, rounded up to 0.25 h; the guard needs balance - cap x $1.85 (PLANNING_PRICE_USD) >= $6. Funding (B4,
DRAFT:205): the base need = the largest, over a path's launches k, of the upper spend of the launches before k + $6 +
$1.85 x the summed caps of launch k; a launch is one pod or parallel pods; a pod's upper spend is (42 min + its jobs'
measured spend uppers) x $1.79 (RATE_USD; the anchor's spend upper is 0.15 h, its cap upper 0.25 h; [D9] B-1). Wave 1
needs CONTINGENCY_FACTOR x the base need ([D11], [D13]): the extra is the contingency from which re-runs are paid, in
launch order. [D20] as amended: host.py refuses at create a missing or non-finite price and one above MAX_PRICE_USD.
[D21]: no pod holds more than MAX_ARMS_PER_POD arms; a wave of n arms is ceil(n / MAX_ARMS_PER_POD) parallel pods with
the arms dealt evenly in order (pod_sizes), and the need counts every later launch of the worst path split that way.
[D21] (5): with GRANITE_ON_POD the need also counts a pod Granite judge launch after wave 2 and after the extension
(granite_pod: the judge launcher's cap rule; guard term cap x $1.85, upper spend cap x $1.79).
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
import math

# ===== DRAFT constants: DRAFT revision 4b §1, §5, §9 and brief B3-B5 with [D5], [D8], [D9], [D11], [D13]; THE one place to edit =====
POD_OVERHEAD_S = 42 * 60                  # per pod (B4; [D9] B-2)
START_MARGIN_S = 1800                     # a job starts only with its upper + 30 min left (§9)
OVERHEAD_FLOOR_S = 1000                   # scripts/cuda_preflight_family.py:77
SAFETY_MARGIN_S = 900                     # scripts/cuda_preflight_family.py:82
FIXTURE_STEPS = 38                        # the fixture's training_s covers 38 steps (cuda_preflight_family.py:78)
DIAGNOSTICS_UPPER_S = 2.0 * 3600          # [D11]: the diagnostics' measured upper, all rows (DRAFT revision 4b §5)
DIAGNOSTICS_UPPER_FACTOR = 1.5            # upper_s = 1.5 x 2.0 h = 3.0 h; start requirement 3.5 h ([D13])
ANCHOR_UPPER_S = 0.25 * 3600              # §9 (I)
MEASURED_UPPER_S = {"arm": 52 * 60, "retrain": 0.15 * 3600, "diagnostics": 2.0 * 3600, "anchor": 0.25 * 3600}
SPEND_UPPER_S = {"arm": 52 * 60, "retrain": 0.15 * 3600, "diagnostics": 2.0 * 3600,
                 "anchor": 0.15 * 3600}   # [D9] B-1: the anchor's spend upper (its cap still uses 0.25 h)
CONTINGENCY_FACTOR = 1.25                 # [D22] (the user, 9 Oct; was 1.15 [D11]): wave 1 needs 1.25 x the worst
                                          # path's need, so the rest pays two 4-arm pre-job re-runs, not one
CAP_STEP_S = 0.25 * 3600                  # caps are rounded up to 0.25 h
MAX_PRICE_USD = 10.0                      # [D20] as amended (the user, brief revision 17): the create-time limit
PLANNING_PRICE_USD = 1.85                 # [D20]: the guard's planning $/h (budget.py check and intents, launch.py,
                                          # host.py extend-cap, guard_usd, the need's cap terms); not a create limit
RATE_USD = 1.79                           # [D20]: the A100's measured $/h, 8-9 Oct pods (costPerHr in
                                          # tmp/family-probe-sp-llama32-1b-b-seed110{2,3}/hosts/*/pod.json)
RESERVE_USD = 6.0                         # KIT/budget.py:19; the DRAFT's rule, unchanged by [D20]
SETUPTOOLS_PIN = "78.1.0"                 # [D5]; setup/constraints.txt holds exactly this line
PIP_PIN = None                            # bootstrap.pip_pin [D5]: null; a version only by a recorded lead decision
DEV_SEEDS = (1101, 2099)                  # the development seed namespace (study-kt-data-dolly-olmo2.json)
R_SEED_BASE = 1100                        # R_d runs at seed 1100 + d
WAVE0A_DRAWS = (1, 2, 3)
EXTENSION_DRAWS = (4, 5)
UNIT_SEED = 1101                          # wave 1: every unit at 1101
RETRAIN_SEED = 1101                       # wave 0b: the retrain and the diagnostics at 1101
WAVE2_SEEDS = (1102, 1103)
EXTENSION_SEEDS = (1104, 1105)
UNITS = 8
WORST_PATH_AFTER_WAVE1 = (("2", 8), ("ext", 6), ("lc", 4))   # §9: wave 2 at m = 4, extension with 2 units, control
MAX_ARMS_PER_POD = 4                      # [D21]; confirmed by the user 9 Oct 19:37 UTC for the whole path: every arm wave is split into pods of at most this many arms
                                          # (pod_sizes); the user confirms the value at the freeze (DRAFT rev. 5 §12)
GRANITE_ON_POD = True                     # [D22] (the user, 9 Oct; parity PASS in FOCUS 17:22 UTC); [D21] (5): True = Gate B's Granite files come from the judge pod, so the
                                          # wave-1 need also counts the mid-path Granite launches (granite_pod);
                                          # False = the Mac judges Granite (no pod launch counted). The pod route
                                          # needs the Granite parity PASS recorded before the freeze; the lead sets
                                          # the value at the freeze, so the default stays the Mac route
GRANITE_POD_AFTER = ("2", "ext")          # [D21] (5): one pod Granite launch after wave 2 and after the extension
                                          # (not after wave 1 or the length control)
PREREG_FIXTURE_SHA256 = "98d775f10ccc032e006c3ebb27c3c70e58c9affda49b6881bc054992216c67b0"  # Gate A's fixture (B-5)
LOCK_SHA256 = "7e0dd99892300a27ab797be746f465860d8ea4055dda36c46d78e743381d15ee"  # Gate A's environment-linux.lock (the lead, 10 Oct)
# ===== end of the DRAFT constants =====

# the judge launcher's cap rule ([D21] (5); scripts/gate_b_mac_judges/pod/README.md at 2694bd0, "The cap" and
# "Granite: time and cost"; judge_pod.cap_hours_for with GRANITE_UPPER_S_PER_ITEM): the smallest half hour of at least
# 30 min setup + 0.5 s per answer + 15 min margin, never below 1 h, above 6 h refused; Granite judges the 200 greedy
# answers of each arm, and the known-answer gate (on for every Gate B launch) adds its 200 answers to the cap
GRANITE_SETUP_UPPER_S = 1800              # judge_pod.SETUP_UPPER_S
GRANITE_S_PER_ANSWER = 0.5                # judge_pod.GRANITE_UPPER_S_PER_ITEM
GRANITE_MARGIN_S = 900                    # judge_pod.MARGIN_S
GRANITE_CAP_MIN_H, GRANITE_CAP_MAX_H = 1.0, 6.0   # judge_pod: at least 1 h; MAX_CAP_HOURS 6 h (split the units)
GRANITE_GREEDY_PER_ARM = 200              # --expect-greedy 200: Granite judges the greedy answers only
GRANITE_KNOWN_ANSWERS = 200               # the known-answer gate's 200 answers, judged first and counted in the cap

# pins (brief R lines, SEAL, [D10]); a null is filled by the lead, and every script that needs it refuses until then
MAN_PATH = ".ai/inputs/gate-b-sealed-20261008/out/MANIFEST.json"
MAN_SHA256 = "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8"
PREPARED_MANIFESTS = {"prepared-kt-dolly-olmo2": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"}
REC = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json"
RECIPE_S = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json"
GATE_A_FIXTURE = "tmp/family-probe-olmo2-1b/expected-fixture-probe.json"
ANCHOR_PROMPTS_PIN = {"path": "tmp/gate-b-anchors/anchor_prompts.json",
                      "sha256": "78467c97c40e7e9fd39e8061219517853e7292a25881700da5e9115604117b97"}
ANCHOR_FILE_PIN = {"path": "tmp/gate-b-anchors/anchor_bank.json",
                   "sha256": "2cf9633613e235d1f33deee3530c3e53b037845bd3979568887742457c1801ed"}  # the pod-made anchor file, sealed 10 Oct ([D10])
PINNED_SCRIPTS = {"scripts/make_anchor_answers.py": "5a686a82eb80d0a6da3f4f232b31bcda7c7840ced0038f666fe2a0e4a4d34146",
                  "scripts/gate_c_representation.py": "998231ea6efd99871bbf0086619975f8bba4b147d7b2c350215653f9df63e5fe",
                  "scripts/gate_c_classifier.py": "23a7f5f0d91bc71813ab55d01694ee3fae488097a58a706d63403f985ab1932e",
                  "scripts/make_gateb_recipe.py": "4823de42bdbfc3ad29755b1e221fc041eba678839759d0abab5bb8247bc4f460"}  # the lead, 10 Oct, at c9aa7ca
STAGE_SCRIPTS = {"anchor": ("scripts/make_anchor_answers.py",),
                 "gateb": ("scripts/make_anchor_answers.py", "scripts/gate_c_representation.py",
                           "scripts/gate_c_classifier.py", "scripts/make_gateb_recipe.py")}

# administrative (not DRAFT values)
TOKEN_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
PREPARED_NAME = "prepared-kt-dolly-olmo2"
PREPARED_LOCAL = "tmp/kt-prepared"
PROBE_KEY = "olmo2-1b"                    # probes.py row: the policy and guard downloads and weight pins
POD_SIZES = {"preflight_wait_s": 3600, "container_disk_gb": 60, "volume_gb": 20}
KINDS =("anchor", "retrain", "arm", "diagnostics")
WAVES = ("anchor", "0a", "0b", "1", "2", "ext", "lc")
HOST_PREFIX = {"anchor": "anchor", "0a": "w0a", "0b": "w0b", "1": "w1", "2": "w2", "ext": "ext", "lc": "lc"}
STATUSES = ("planned", "complete", "crashed", "deferred", "not_started")
BOOTSTRAP_FIELDS = ("lock_sha256", "pip_version", "gpu", "cuda_runtime")
LOG_ONLY_FIELDS = ("pip_version",)        # B5, [D5]: logged, never stops the pod


def hours(seconds: float) -> float:
    return seconds / 3600


def training_s(fixture: dict, steps: int) -> float:
    """The fixture's training seconds scaled to ``steps`` (x steps/38; [D11] B-5)."""
    return fixture["training_s"] * steps / FIXTURE_STEPS


def upper_s(kind: str, fixture: dict | None, steps: int | None) -> float:
    """A job's worst-case seconds (B3)."""
    if kind == "arm":
        return fixture["e1_upper_s"] + training_s(fixture, steps) + OVERHEAD_FLOOR_S + SAFETY_MARGIN_S
    if kind == "retrain":
        return training_s(fixture, steps) + OVERHEAD_FLOOR_S + SAFETY_MARGIN_S
    if kind == "diagnostics":
        return DIAGNOSTICS_UPPER_FACTOR * DIAGNOSTICS_UPPER_S
    if kind == "anchor":
        return ANCHOR_UPPER_S
    raise ValueError(f"unknown job kind {kind!r}")


def start_requirement_s(upper: float) -> float:
    return upper + START_MARGIN_S


def job_record(kind: str, arm: str | None, seed: int | None, edit: str | None, steps: int | None, fixture: dict | None,
               a0_source: int | None = None) -> dict:
    """One plan job (B1) with its timing fields from this module's rules."""
    up = upper_s(kind, fixture, steps)
    job = {"kind": kind, "arm": arm, "seed": seed, "edit": edit, "steps": steps, "upper_s": up,
           "start_requirement_s": start_requirement_s(up), "measured_upper_s": MEASURED_UPPER_S[kind],
           "status": "planned"}
    if kind == "diagnostics":
        job["a0_source"] = a0_source
    return job


def projected_requirement_s(job: dict, projection: dict | None) -> float | None:
    """This pod's preflight projection of a job's start requirement (arm and retrain only; None otherwise).
    ``projection`` is the preflight's cap_projection block (e1_upper_s, training_s, overhead_s, margin_s)."""
    if job["kind"] not in ("arm", "retrain"):
        return None
    if not projection:
        raise ValueError("no preflight projection for an arm or the retrain")
    fixture = {"e1_upper_s": projection["e1_upper_s"], "training_s": projection["training_s"]}
    over = max(projection.get("overhead_s") or 0.0, OVERHEAD_FLOOR_S) + max(projection.get("margin_s") or 0.0,
                                                                           SAFETY_MARGIN_S)
    base = training_s(fixture, job["steps"]) + over
    return start_requirement_s(base + (fixture["e1_upper_s"] if job["kind"] == "arm" else 0.0))


def own_requirement_s(job: dict, projection: dict | None = None) -> float:
    """max(the plan value, this pod's projection) [V21g]."""
    projected = projected_requirement_s(job, projection) if projection is not None else None
    return max(job["start_requirement_s"], projected if projected is not None else 0.0)


def linked_diagnostics(jobs: list[dict], index: int) -> int | None:
    """The index of the later diagnostics job whose a0_source names the retrain at ``index``, or None."""
    for later in range(index + 1, len(jobs)):
        if jobs[later]["kind"] == "diagnostics" and jobs[later].get("a0_source") == index:
            return later
    return None


def requirements(jobs: list[dict], projection: dict | None = None) -> list[float]:
    """Each job's start requirement on a pod: its own (plan and projection), and for a retrain named by a later
    diagnostics job, max(its own, its measured upper + the diagnostics' requirement) (B3 [V7])."""
    own = [own_requirement_s(job, projection) for job in jobs]
    out = list(own)
    for k, job in enumerate(jobs):
        if job["kind"] == "retrain":
            later = linked_diagnostics(jobs, k)
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
    """[D21]: how a wave of ``n`` arms is split: ceil(n / MAX_ARMS_PER_POD) pods, the arms dealt as evenly as possible
    in order, the earlier pods taking the one extra arm (8 -> 4 + 4, 6 -> 3 + 3, 5 -> 3 + 2, 4 -> 4). Each pod's cap
    is cap_hours of its own jobs; the pods of one wave are one launch (parallel pods: their caps add in the need)."""
    m = MAX_ARMS_PER_POD
    if type(m) is not int or m < 1:
        raise ValueError("MAX_ARMS_PER_POD must be a positive integer")
    if type(n) is not int or n < 1:
        raise ValueError("a wave needs at least one arm")
    k = -(-n // m)
    return [n // k + (1 if i < n % k else 0) for i in range(k)]


def split_pods(jobs: list) -> list[list]:
    """``jobs`` in order, cut into the pods of pod_sizes(len(jobs)) ([D21])."""
    out, start = [], 0
    for size in pod_sizes(len(jobs)):
        out.append(list(jobs[start:start + size]))
        start += size
    return out


def arm_count(jobs: list[dict]) -> int:
    return sum(1 for j in jobs if j["kind"] == "arm")


def guard_usd(cap_h: float) -> float:
    """What the budget guard needs for one pod of this cap: $6 + cap x $1.85 (KIT/budget.py's rule; [D20])."""
    return RESERVE_USD + cap_h * PLANNING_PRICE_USD


def pod_spend_usd(kinds: list[str]) -> float:
    """One pod's upper spend: (42 min + its jobs' spend uppers) x $1.79 ([D20])."""
    return hours(POD_OVERHEAD_S + sum(SPEND_UPPER_S[k] for k in kinds)) * RATE_USD


def granite_on_pod() -> bool:
    """[D21] (5): the GRANITE_ON_POD flag, which must be a bool (a string such as "False" refuses)."""
    if type(GRANITE_ON_POD) is not bool:
        raise ValueError("GRANITE_ON_POD must be True (pod Granite) or False (Mac Granite)")
    return GRANITE_ON_POD


def granite_cap_hours(answers: int) -> float:
    """[D21] (5): the judge launcher's cap for ``answers`` (the gate's included): the smallest half hour of at least
    (30 min + 0.5 s x answers + 15 min), never below 1 h; above 6 h the launcher refuses, and so does this."""
    if type(answers) is not int or answers < 1:
        raise ValueError("a Granite launch judges at least one answer")
    need = (GRANITE_SETUP_UPPER_S + answers * GRANITE_S_PER_ANSWER + GRANITE_MARGIN_S) / 3600
    cap = max(GRANITE_CAP_MIN_H, math.ceil(need * 2) / 2)
    if cap > GRANITE_CAP_MAX_H:
        raise ValueError(f"a Granite launch of {answers} answers needs a cap above {GRANITE_CAP_MAX_H} h")
    return cap


def granite_pod(arms: int) -> dict:
    """[D21] (5): one pod Granite judge launch of ``arms`` arms (200 greedy answers each, plus the known-answer gate's
    200) as a launch's pod for funding_need_usd: its guard term counts cap x $1.85 (PLANNING_PRICE_USD), and its upper
    spend for the later terms is cap x $1.79 (RATE_USD; the in-pod timer stops it at the cap, so the cap bounds it)."""
    if type(arms) is not int or arms < 1:
        raise ValueError("a Granite launch judges at least one arm")
    answers = arms * GRANITE_GREEDY_PER_ARM + GRANITE_KNOWN_ANSWERS
    return {"judge": "granite", "arms": arms, "answers": answers, "kinds": [], "cap_hours": granite_cap_hours(answers)}


def launch_pod_spend_usd(pod: dict) -> float:
    """A launch pod's upper spend: a kit pod's pod_spend_usd of its job kinds; a judge pod's cap x $1.79."""
    if pod.get("judge"):
        return pod["cap_hours"] * RATE_USD
    return pod_spend_usd(pod["kinds"])


def cents(usd: float) -> float:
    """An amount rounded to the cent, half up (decimal, not binary, rounding)."""
    return float(Decimal(repr(usd)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def funding_need_usd(launches: list[list[dict]], factor: float = 1.0) -> dict:
    """B4: ``launches`` in path order; each launch is a list of pods {"kinds": [...], "cap_hours": h} (or a judge pod
    from granite_pod, [D21] (5), whose spend is its cap x $1.79: launch_pod_spend_usd). Returns every
    term, the base need (the largest term, rounded to the cent) and the need: the factor (wave 1:
    CONTINGENCY_FACTOR) times the rounded base, rounded to the cent ([D20]: round(55.78 x 1.15, 2) = 64.15). The
    contingency is the need minus the rounded base."""
    terms, spent = [], 0.0
    for launch in launches:
        terms.append(spent + RESERVE_USD + PLANNING_PRICE_USD * sum(p["cap_hours"] for p in launch))
        spent += sum(launch_pod_spend_usd(p) for p in launch)
    base = cents(max(terms))
    need = cents(float(Decimal(repr(base)) * Decimal(repr(factor))))
    return {"base_need_usd": base, "factor": factor, "need_usd": need, "contingency_usd": cents(need - base),
            "terms_usd": terms}


def rerun_cost_usd(kind: str, new_pod: bool) -> float:
    """A re-run's upper spend, paid from the contingency: its spend upper x $1.79, plus 42 min when it needs a new pod."""
    return hours(SPEND_UPPER_S[kind] + (POD_OVERHEAD_S if new_pod else 0)) * RATE_USD


def unit_rerun_cost_usd(kinds: list[str], new_pod: bool) -> float:
    """[D21] (3): a pre-job requeue's jobs paid as one unit: their spend uppers x $1.79, plus one 42 min when they need
    a new pod (on a new pod, pod_spend_usd of the same kinds). It is, by construction, the sum of the one-by-one costs
    that plan_tool.pay_reruns charges for the same jobs in order (rerun_cost_usd, the 42 min on the first only), so a
    unit and its jobs paid one by one cost the same; the one-by-one rule governs when the contingency is short."""
    return sum(rerun_cost_usd(k, new_pod and i == 0) for i, k in enumerate(kinds))


def default_jobs(kinds: list[str], fixture: dict, arm_steps: int = 33, retrain_steps: int = 38) -> list[dict]:
    """Jobs of the given kinds with the default timing (a diagnostics job names the last retrain before it)."""
    out = []
    for kind in kinds:
        steps = arm_steps if kind == "arm" else retrain_steps if kind == "retrain" else None
        source = max((i for i, j in enumerate(out) if j["kind"] == "retrain"), default=None)
        out.append(job_record(kind, None, None, None, steps, fixture, source if kind == "diagnostics" else None))
    return out


def gate(remaining_s: float | None, requirement_s: float) -> bool:
    """A job starts only when the remaining time is known and at least its requirement (None never fits)."""
    return remaining_s is not None and remaining_s >= requirement_s


def compare(new: dict, reference: dict, fields) -> dict:
    """Field names (never values) that differ, that are missing (None or absent) in the new record, and the
    log-only differences (LOG_ONLY_FIELDS). ``stop`` is true when any non-log-only field differs or is missing."""
    missing = sorted(f for f in fields if new.get(f) is None)
    differ = sorted(f for f in fields if f not in missing and new.get(f) != reference.get(f))
    logged = [f for f in differ if f in LOG_ONLY_FIELDS]
    stopping = [f for f in differ if f not in LOG_ONLY_FIELDS]
    return {"differ": stopping, "missing": missing, "logged": logged, "stop": bool(stopping or missing)}
