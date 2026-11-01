"""Write and update plan.json for the stage-1 kit (administrative; B15, brief notes/b15-brief.md §4-§6 with the lead's
§8 defaults, addendum §17). Copied from runkit/gate-b-olmo/plan_tool.py: blocks replace waves; requeue,
confirm-stopped, defer, the stranded exception (now a J3 O-only pass and its J2 regeneration), pay_reruns and pay_unit
are kept.

    plan_tool.py init-block BLOCK --jobs FILE --funding FILE [--dry-run]    plan a block and release its launch 0
    plan_tool.py release BLOCK                     release the block's next launch (its hosts become launchable);
                                                   with the guard-off record, without waiting for the launch
                                                   before it (addendum §28; a judge launch still waits)
    plan_tool.py deal BLOCK [--reuse ARM SEED]     print the interleaving deal of a block's training runs (no write)
    plan_tool.py record-done HOST | defer HOST | confirm-stopped HOST | requeue HOST [--rerun-mismatched SHA ...]
    plan_tool.py record-branch FILE --sha256 H     W1-18's branch record, or a "Branch full by default" record (G1)
    plan_tool.py record-guard-off FILE --sha256 H  (E) the user's decision {kind "stage1 user decision: budget guard
                                                   off", user_words, utc, recorded_by}: launch.py and host.py extend-cap
                                                   go past the live-balance guard (still read and logged); the $10/h
                                                   limit, the stop timer and stop-never-delete stay
    plan_tool.py record-gateb-final FILE --sha256 H                                                    (G3)
    plan_tool.py record-plan-ab VERDICT --sha256 H Gate B's verdict file itself (rules.GATEB_VERDICT, by its pin): the
                                                   kit reads result.readings.plain.sigma_hat_pp and applies REV4 §1.3
                                                   (plan_code_for); the record (plan.json) names the file by SHA-256,
                                                   the field, the value and the code; nothing is typed (round 2)
    plan_tool.py record-certificate FILE --sha256 H | record-certification FILE --sha256 H            (G4, LS-08)
    plan_tool.py write-thresholds --out FILE --recorded-by WHO   C2's thresholds record, exactly rules.C2_THRESHOLDS
    plan_tool.py record-thresholds FILE --sha256 H (it must carry addendum §22 point 1 exactly; once)
    plan_tool.py c2-label STEPS --sha256 H         label C2's steps.jsonl from constrained.mean_weight.t2_5 only
    plan_tool.py record-c3 FILE --sha256 H         {kind: "stage1 c3 subsample pin", subsample: {path, sha256}, record:
                                                   {path, sha256}, utc, recorded_by}: J14's file and the writer's record
    plan_tool.py record-c3-fallback FILE --sha256 H   {kind: "stage1 c3 fallback", status: "dropped", reason, utc,
                                                   recorded_by}: C3's smoke is dropped (addendum §22 point 2)
    plan_tool.py record-d2-fallback FILE --sha256 H   {kind: "stage1 d2 fallback", jobs: ["rep_pass"|"classifier"],
                                                   reason, utc, recorded_by}: J5 without plant and decoy (§19 point 4),
                                                   J8 by the W1 script with no pools (§21)
    plan_tool.py record-prefix FILE --sha256 H | record-user-yes FILE --sha256 H
    plan_tool.py record-sealed FILE --sha256 H     a lead's sealed edit record (edits are bound only from MAN1, Gate
                                                   B's MANIFEST or such a record, never typed)
    plan_tool.py import-reference FILE --sha256 H  Gate B's environment reference (its plan.json "reference"; Q11)
    plan_tool.py record-oext-fallback FILE --sha256 H   fallback (c), {kind: "stage1 oext fallback", status:
                                                   "dev100_recipe_cap", reason, utc, recorded_by} (addendum §11.1)
    plan_tool.py write-block-a-plan --out FILE --recorded-by WHO [--split 2,2,1]   the kit's default block-A plan with
                                                   the lead's split of the deal (round 3a), never over a file
    plan_tool.py record-block-a-plan FILE --sha256 H    the block-A plan (refused once S1-0 or the cert pod is planned)
    plan_tool.py record-block-a-replan FILE --sha256 H  a new plan after that: every planned part must fit it and the
                                                   group's first funding record must cover its need
    plan_tool.py block-a-need [FILE --sha256 H]   every launch's caps, spends, unmeasured terms, the terms in cents and
                                                   the need (Branch full, Branch 128, frozen); no write
    plan_tool.py record-block-a-not-run FILE --sha256 H   {kind: "stage1 block-a not-run decision", jobs: [name,
                                                   ...], reason, utc, recorded_by}: jobs the block-A plan requires that
                                                   will not run (round 3c; names as block A's refusal prints them)
    plan_tool.py record-unpulled FILE --sha256 H   {kind: "stage1 unpulled outputs decision", host, jobs: [index, ...],
                                                   reason, utc, recorded_by} (addendum §29 point 3): HOST's jobs that
                                                   are complete on the pod whose unit the pull did not fetch; then
                                                   record-done HOST records them "complete (not pulled)" (pulled
                                                   false), the seal lists them with no hashes, and block A's
                                                   completeness counts them as decided; re-hashed at every use
    plan_tool.py record-rerun-payment FILE --sha256 H   the user's decision {kind: "stage1 user decision: pay re-runs
                                                   beyond the contingency", user_words (verbatim), block, jobs: [{arm,
                                                   seed}], amount_usd, utc, recorded_by}: requeue HOST then moves the
                                                   named jobs an earlier move of HOST held as not re-run and pays them,
                                                   as one unit, beyond the contingency (logged; contingency.user_paid),
                                                   and nothing else; re-hashed at every use
    plan_tool.py record-judges BLOCK FILE --sha256 H   (round 30, R2) the block's judge-completion record {kind: "stage1
                                                   judge completion record", block, judges: {harmbench: {tag,
                                                   result_sha256, run_record_sha256, bundle_sha256, exit, judged,
                                                   complete}, granite: {the same, known_answer_passed}}, index_sha256,
                                                   utc, recorded_by}: a judge launch is done only while this record
                                                   names it and is valid (re-hashed, its index and judge files checked
                                                   at every use); works on a sealed block and changes no seal
    plan_tool.py record-not-run FILE --sha256 H    (round 32, K2) the lead's decision {kind: "stage1 not-run
                                                   decision", block, jobs: ["HOST:INDEX", ...], reason, utc,
                                                   recorded_by} that jobs of a block other than A will not run;
                                                   re-hashed at every use
    plan_tool.py init-block certify --jobs FILE --funding FILE --group-jobs B=FILE   (round 32, K4) block B's group:
                                                   the first init's funding record covers the whole group

BLOCKS (rules.BLOCKS, in order): "S1-0" (W1-18 alone, §8 Q1), "cert" (C1-C3, on Y), "A", "certify" (B10's
certification pod), "B", "C" (plan B only). A block's jobs FILE is {"launches": [L, ...], "reused": [[arm, seed]],
"engine": "X"}, each launch L one of {"hosts": [[job, ...], ...]} (parallel pods given job by job), {"deal": [i, ...]}
(pods i of the block's interleaving deal, rules.deal, of exactly the table's training runs, rules.block_runs) or
{"judge": {"arms": n, "judge": "harmbench"|"granite"}} (a judge launch, rules.judge_pod; Granite by default). A job is {kind, arm, seed, engine, points, recipe,
regen_source, role}. The tool fills steps (REV4 §1.1 by dose), the engine (Y for C1-C3 and B+Qi), the recipe
(Q4: recipe S for new arms and regenerations; REC for B10's references), the timing (rules.job_record under the
recorded W1-18 branch, else Branch full), each host's cap, guard and spend, and the block's funding need: CONTINGENCY
x the worst path over its funding group (rules.FUNDING_BLOCK: S1-0, cert and A on block A's funding event, certify and
B on block B's, C on its own), every earlier part of the group counted first. Block A's group (S1-0, cert, A) follows
the BLOCK-A PLAN (round 3a; the user's rule, "it must cover the block's cap-based need before the block launches",
and addendum §20 point 1): a pre-set, outcome-free list of the group's launches, S1-0 -> the cert pod -> the
diagnostics pod -> the LN-12 pod(s) -> the arm launches (a split of the deal) -> HarmBench and Granite, recorded by the
lead before S1-0 (record-block-a-plan) or, if none is, the kit default (split 2+2+1; recorded at the group's first
init). S1-0's and the cert pod's need counts every later launch of the plan (each pod at the larger of its Branch-full
and Branch-128 cap and spend); every init-block and release of the group refuses a launch that departs from the plan
(another order, more pods, a pod with a larger cap or spend, another job; a launch may be left out or its pods spread
over consecutive launches, which never raises a term), and the plan is re-derived at each use (its file by SHA-256;
the default from its recorded inputs). A changed plan after S1-0 is a re-plan, recorded only if every planned part
fits it and the group's first funding record covers its need. Round 3a's fix round: a plan must hold all of block A's
G5 content (C3 unless its fallback, J5-J8, the six J2/J3 pairs, theta0's J3 and LN-14 unless the O-ext fallback,
judges over the new plus the re-judged units); every later init in the group must also be covered by the group's first
funding record (S1-0's, re-hashed from its file); the group's parts are read in planning order (each block record's
seq); a pod that received deferred or re-queued jobs is checked as it was planned (its plan_shape: those moves are
paid from the contingency, outside the plan). Round 3b: c0 (J11) runs on engine X on the LN-12 pod, not on the cert
pod (addendum §26); LN-15e's report-only A1 re-score is in the plan (§17 Q19, §25 point 1): Gate B's retrain (J20, a0
at 1102 and 1103, train only to e1) and diagnostics attributes step (J21, a1_rescore: A1's bi-anchored cosine at q and
e1, linked by regen_source on the same pod), both required on the LN-12 pod; V2a stays on its fallback (NOT_IN_PLAN,
recorded in every plan as not_in_plan and printed by block-a-need); the judges run over 27 units (20 new + the 6
reused a0/R units + theta0's; §25 point 2). init-block refuses
unless
--funding FILE is {block, amount_usd, utc (UTC, not in the future), source: "user RunPod top-up", user_words,
recorded_by} with block = the group and amount_usd >= the need (the user's rule). Launch 0 is released at once; later launches by ``release`` after every
host of the launch before is done or moved (the need's path assumes it). While the user's budget-guard-off decision is
recorded (record-guard-off), ``release`` releases a hosts launch without that wait and records it in the block's
released_early (addendum §28: the user manages the balance; the order, the block-A plan, the need against the
funding record and every gate stay; a judge launch still waits until every earlier launch's hosts are done or
moved). Every gate below is checked at init for the
whole block and again at release:
- G1: a 500-bank job (rules.BANK500_KINDS) refuses while no branch record exists; a W1-18 job anywhere but job 0 of
  an S1-0 host (W1-18 alone) refuses; any other block before an S1-0 host refuses unless a "Branch full by default"
  record exists; a branch record whose output SHA-256 differs from the pulled W1-18 output refuses; a branch change
  refuses once any 500-bank job is planned. "Branch full by default" is accepted only if W1-18 cannot run or failed:
  never over W1-18's branch record, never while an S1-0 host is not done, never after W1-18 completed; once it is
  recorded no S1-0 pod is planned.
- G3: Gate B's final record is its measurements --final output (code REPORTED) pinned by rules.GATEB_FINAL_SHA256,
  recorded once; cert needs it; A, certify, B and C need it and the plan-A/B record derived from Gate B's verdict
  file (rules.GATEB_VERDICT; any other file, hash or typed record refuses); a "none" code refuses every block. Once
  recorded, the record is re-derived from the verdict file (by its pin) at every init-block, release and deal
  (``plan_ab_checked``): a hand-edited plan.json record or a changed verdict file refuses.
- D-2 (addendum §19, §21): every J5 and J8 job carries the filled pins file, REQ-8's record and its pools by SHA-256
  (s3_safe from the S-pool record), or the D-2 fallback record; J5 needs J6 earlier on its pod (the s3_orig pass);
  both run on engine X. C3 (§22 point 2): a cert_c3 job carries the lead's subsample file and record by SHA-256; the
  cert block plans C3 or has its fallback record (C3 dropped).
- G4: one engine per pod; a Y job refuses before a recorded passing certificate, except C1-C3 on the cert pod
  and, after a recorded failing certificate, B+Qi (ref_train bqi) with its own a0 (a0_arm role "bqi_own_a0"); c0,
  LN-15e's retrain and re-score run on engine X only (addendum §26); a
  packed engine whose identity is not rules.ENGINES' refuses. The cert block is one pod with C1 and C2 once each
  (so C2's thresholds record and binding check are never skipped).
- G5: certify and B refuse before block A is complete and sealed (seal.py); C before block B is complete; C under
  plan A refuses.
- Q16/Q17/K = 12: an SP prefix point refuses without the prefix record; cert_c2 without the thresholds record; a
  Safe LoRA k12 point without the user's recorded yes. An evaluation-only reference refuses before a passing B10
  certification record. B10's certification runs certify first. Recipe S's training identity must be
  rules.TRAINING_IDENTITY (§8 Q4). After a failed certificate every B+Qi seed has its own a0 on Y, each once.
  A host's recipe is checked at release in its own engine's tree with that engine's code: an X host's in main's tree
  (engine X), a Y host's in engine Y's frozen tree by engine Y's own code (check_recipe_y; B+Qi's recipe is there only).
- At most rules.MAX_ARMS_PER_POD counted jobs per pod; two a0 calibrations at one seed never share a pod; an O-only
  pass on a0 or R must name its regeneration earlier on the same pod (no state moves between pods); a block's
  training runs are exactly the table's, dealt by the rule; no run (or evaluation point) is planned twice; under
  fallback (c) an O-only pass or transfer report refuses. No R_4/R_5 is reused (rules.ALLOWED_REUSE: no extension).
- A block is complete when every launch is released (judge launches included: ``release`` records a judge launch)
  and every host is done or moved. Round 3c (VP3b-3): block A is complete only when, in addition, every job the
  recorded block-A plan requires for block A (block_a_required: the diagnostics and LN-12 pods' jobs, theta0's LN-14
  report under Branch 128 only and no O-only pass under fallback (c), every dealt arm run, each judge launch over its
  planned units) has a completion record (recorded complete on a block-A host; a judge launch released over at least
  those units) or is named by a recorded lead decision (record-block-a-not-run) as not run, with a reason.
- Round 30 (addendum §30, the lead's R2-R3): a judge launch's completion record is the block's judge-completion
  record (record-judges), never its release: a released judge launch counts as done only while that record names its
  judge and is valid at that use (judge_record_valid: the file re-hashed, judges/BLOCK/judge-files-index.json at its
  index_sha256, and judge_files_check: every indexed file present at its SHA-256, no unindexed judge-named file, one
  file per judge for each required unit: plan.json's arm jobs and B10 units plus rules.REJUDGED_PINS). For every
  block, not only A. A released judge launch with no record may be named by a not-run decision, also after block A's
  seal (a failed Granite is recorded so).
- Round 31 (addendum §32 points 1-3): record-judge-not-run FILE --sha256 H, the lead's decision {kind: "stage1 judge
  not-run decision", block, judges, reason, utc, recorded_by} for a released judge launch of any block but A (block A
  keeps record-block-a-not-run), also after the block's seal (it changes no seal), re-hashed at every use; then
  record-judges needs only the other judges, and block completeness, seal.py and seal.py status count and list it. A
  block's judged units include its ref_train runs (rules.JUDGED_RUN_KINDS); block B has no re-judged pins
  (rules.REJUDGED_PINS["B"] is empty). init-block of a block other than A refuses a judge launch over fewer units than
  the judged units its jobs will produce (planned_judged_units; block A: its plan's check).
- Round 32 (addendum §34 points 5-7; block B's pre-flight G4, G6, G8, G11, G13):
  K1, block B's second reference phase: a launch {"second_phase": [[job, ...], ...]} of block B holds the
  evaluation-only references (ref_eval, safe_lora) on block B's own a0 runs (the deal's a0 seeds, 1105-1107); every
  such reference must be in one, it comes after every deal launch and before every judge launch, and it is part of
  block B's need, completeness and seal like any launch. It is released only when (second_phase_gate) block B's a0
  run at each of its seeds is recorded complete (record-done) with its readable fingerprint record (K6: the runner's
  job-I/a0-adapter-fingerprint.json among its outputs), B10's settings at their S1_CODE pin name that run's
  COMPLETE.json SHA-256 as the seed's reference unit with that record's fingerprint prefixes (and, for safe_lora,
  B11's settings at their pin accept exactly the record's e1): the B10/B11 re-pin; and the packed stage1-X holds the
  input gate_a_complete:SEED at that SHA-256 and B10's and B11's four files at their S1_CODE pins: the re-pack. The
  guard-off record never releases it early.
  K6: after a complete a0_arm job the runner writes job-I/a0-adapter-fingerprint.json (readable after the seal), the
  format of the B10/B11 re-pin tool, e1 from states/e1/state.json (B11's field) equal to COMPLETE.json's.
  K2, a not-run decision for any block but A (record-not-run): a job that will not run is named "HOST:INDEX": a job of
  a done, unmoved host that is not complete; a job a move left behind without re-running it (not carried to a
  target); or every job of a pending host (a held launch that will never be released). Such a block is complete when
  every launch is released or holds only decided hosts (release skips such a launch and records it under "skipped")
  and every job of the block is complete, carried by a move, or decided (block_open_jobs); defer and every move leave
  a decided job where it is. The seal and seal.py status list each decision.
  K3, a failed B10 certification: the runner records B10's exit 4 at b10_certify as complete with certification_gate
  "failed" (the certify unit and its comparison file), record-done keeps the gate, record-certification refuses pass
  true over a failed gate, and init-block (not only release) refuses every evaluation-only reference without a
  passing certification (LS-08).
  K4, block B's group on one funding record: the first init of group B (certify) takes --group-jobs B=FILE (the jobs
  file of each later part of the group, used for the need only) and its funding record must cover the whole group's
  need (addendum §20 point 1, as group A has it); every later init of the group takes that same record (its SHA-256),
  re-hashed, and the need of every part planned so far must stay within it.
- Kit round 34 (1 Nov 2026; the lead's ruling, FOCUS 2026-11-01T04:55 UTC; REV4 §9.4): block "sim" plans B14's
  similarity pass (J22, kind "similarity") alone on one pod, engine X, recipe REC (its settings pin REC; a job naming
  another recipe or engine refuses), on its own funding group "sim" (addendum §36: the start-from-the-balance record
  is accepted as for any block). Its jobs FILE is {"launches": [{"hosts": [[{"kind": "similarity"}]]}]}; any other
  shape refuses. At init and again at release (similarity_entry) the job carries its inputs by SHA-256: the script
  and settings at their stage1_rules.S1_CODE pins, the prepared manifest and dev bank (SIM_DEV_BANK) and the three add
  sets (SIM_ADD_SETS), each resolved from the kit's edit sources (one file per arm, on disk at its pin) and each the
  edit file every S1, S3 and S4 arm run of plan.json names, with at least one such run complete (the pass reads the
  files the arms trained on). record-done checks the pulled similarity.json and the runner's record
  (stage1_rules.similarity_record_problem) and prints the output's path and SHA-256 for the strata step. The block
  holds no outcome and needs no seal.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gateb_mac as mac  # noqa: E402
import stage1_rules as rules  # noqa: E402

ROOT = HERE.parents[1]
ENGINE_ROOT = ROOT
PY = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"
SEAL_OUT = pathlib.Path(rules.MAN_PATH).parent
JOB_KEYS = {"kind", "arm", "seed", "engine", "points", "recipe", "regen_source", "role"}
FUNDING_KEYS = ("block", "amount_usd", "utc", "source", "user_words", "recorded_by")
FUNDING_SOURCE = "user RunPod top-up"
FUNDING_SOURCE_RULE = "user rule: start from the balance"   # addendum §36: the user's rule of 29 Oct 2026
FUNDING_RULE_KIND = "stage1 user decision: start without a covering top-up"
RECORD_KINDS = {"branch": "stage1 w1-18 branch record", "default_full": "stage1 branch full by default",
                "plan_ab": "stage1 plan-ab record", "certificate": "stage1 x-y certificate",
                "certification": "stage1 b10 certification", "thresholds": "stage1 c2 binding thresholds",
                "prefix": "stage1 sp prefix pin", "user_yes": "stage1 user yes", "sealed": "stage1 sealed edits",
                "oext_fallback": "stage1 oext fallback", "c3": "stage1 c3 subsample pin",
                "c3_fallback": "stage1 c3 fallback", "d2_fallback": "stage1 d2 fallback",
                "not_run": "stage1 block-a not-run decision",       # round 3c (VP3b-3): record-block-a-not-run
                "guard_off": rules.GUARD_OFF_KIND,                  # (E): record-guard-off, the user's decision
                "unpulled": "stage1 unpulled outputs decision",     # §29 point 3: record-unpulled, the lead's
                "rerun_payment": "stage1 user decision: pay re-runs beyond the contingency",   # record-rerun-payment
                "judge_not_run": "stage1 judge not-run decision",   # round 31 (K1): record-judge-not-run
                "not_run_block": rules.NOT_RUN_KIND}                # round 32 (K2): record-not-run (not block A)
UNPULLED_KEYS = ("kind", "host", "jobs", "reason", "utc", "recorded_by")
JUDGE_NOT_RUN_KEYS = ("kind", "block", "judges", "reason", "utc", "recorded_by")   # round 31 (K1)
RERUN_PAYMENT_KEYS = ("kind", "user_words", "block", "jobs", "amount_usd", "utc", "recorded_by")
HELD_STATUSES = ("not_started", "crashed", "deferred")    # a job a move left behind (not re-run) keeps one of these
C2_THRESHOLDS_JSON = json.dumps(rules.C2_THRESHOLDS, sort_keys=True)
W1_18_OUTPUT_KIND = "stage1 over-refusal checks"
SHA_RE = re.compile(r"[0-9a-f]{64}")


def fail(message: str):
    raise SystemExit(message)


# ----- engine-backed values -----------------------------------------------------------------------------------------


def _engine(code: str) -> str:
    return subprocess.run([str(PY), "-c", code], cwd=ENGINE_ROOT, capture_output=True, text=True, check=True,
                          env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}).stdout.strip()


def recipe_sha(path: str) -> str:
    return _engine("from experiments.safety_selection.config import load_recipe,config_sha256;"
                   f"print(config_sha256(load_recipe({str(ENGINE_ROOT / path)!r})))")


def recipe_training_identity(path: str) -> str:
    """The engine's training identity of a recipe file (§8 Q4: recipe S's must equal rules.TRAINING_IDENTITY)."""
    return _engine("from experiments.safety_selection.config import load_recipe,training_identity;"
                   f"print(training_identity(load_recipe({str(ENGINE_ROOT / path)!r})))")


# A Y host's recipes (the branch re-pin round): engine Y's frozen tree and engine Y's own code. B+Qi's recipe exists
# only in Y's tree, and engine X's load_recipe refuses its train.constrained_sft field, so a Y host's recipe is never
# read from main's tree or hashed by engine X's code. An X host's recipes are checked as before (ENGINE_ROOT, _engine).


def y_tree() -> pathlib.Path:
    """Engine Y's frozen tree (ROOT / rules.Y_TREE_DEFAULT, as pack_setup.py Y packs it by default)."""
    return ROOT / rules.Y_TREE_DEFAULT


def _engine_y(code: str) -> str:
    """``code`` run by engine Y's own code: an isolated interpreter (-I: no PYTHONPATH, no user site, no current
    folder on the path; -B: no bytecode is written into Y's frozen tree, since -I ignores PYTHONDONTWRITEBYTECODE)
    whose working folder is Y's tree and whose import path starts with it; it refuses unless the engine package it
    imported lies in Y's tree and its code identity is rules.ENGINES["Y"]. Prints the result."""
    tree = str(y_tree())
    guard = (f"import sys,pathlib;sys.path.insert(0,{tree!r});import experiments.safety_selection as _y;"
             f"from experiments.safety_selection.common import code_identity as _ci;"
             f"assert pathlib.Path(_y.__file__).resolve().is_relative_to(pathlib.Path({tree!r}).resolve()),"
             f"'the engine imported is not the one in engine Y tree';"
             f"assert _ci()['sha256']=={rules.ENGINES['Y']!r},'the code in engine Y tree is not engine Y';")
    try:
        out = subprocess.run([str(PY), "-I", "-B", "-c", guard + code], cwd=tree, capture_output=True, text=True,
                             check=True,
                             env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
    except (OSError, subprocess.CalledProcessError) as exc:
        last = (getattr(exc, "stderr", None) or "").strip().splitlines()[-1:] or [type(exc).__name__]
        fail(f"engine Y's own code in its tree refused the recipe check: {last[0][:300]}")
    return out.stdout.strip()


def recipe_sha_y(path: str) -> str:
    """The config SHA-256 of engine Y's tree's recipe file, by engine Y's own load_recipe and config_sha256."""
    return _engine_y("from experiments.safety_selection.config import load_recipe,config_sha256;"
                     f"print(config_sha256(load_recipe({str(y_tree() / path)!r})))")


def recipe_training_identity_y(path: str) -> str:
    """The training identity of engine Y's tree's recipe file, by engine Y's own code (§8 Q4 for recipe S on Y)."""
    return _engine_y("from experiments.safety_selection.config import load_recipe,training_identity;"
                     f"print(training_identity(load_recipe({str(y_tree() / path)!r})))")


RECIPE_ENGINES_DIFFER = ("recipe {name}: engine Y's config SHA-256 differs from engine X's (plan.json's recipes hold "
                         "one value per recipe file, which every pod's runner checks): refused")


def check_recipe_y(plan: dict, name_r: str) -> None:
    """A Y host's recipe: the file in engine Y's tree must hash to its pin, and engine Y's own code (_engine_y) gives
    its config SHA-256 (and, for recipe S, its training identity, which must be rules.TRAINING_IDENTITY). Y's values
    are kept in plan["recipes_y"]. plan["recipes"] (what the runner checks on every pod) takes Y's config SHA-256 when
    no X host has hashed the file yet, marked engine Y (an X host then hashes it again with X's code); when an X host
    has, the two must be equal."""
    path = rules.RECIPE_NAMES[name_r]
    pin = rules.RECIPE_PINS[path]
    tree = y_tree()
    if not (tree / path).is_file() or mac.sha(tree / path) != pin:
        fail(f"{path}: missing from engine Y's tree or differs from its pin (recipe {name_r}, {rules.Y_TREE_DEFAULT})")
    own = plan.setdefault("recipes_y", {})
    if path not in own:
        own[path] = {"sha256": pin, "config_sha256": recipe_sha_y(path)}
    if name_r in rules.TRAINING_IDENTITY_RECIPES:
        own[path].setdefault("training_identity", recipe_training_identity_y(path))
        if own[path]["training_identity"] != rules.TRAINING_IDENTITY:
            fail(f"recipe {name_r}: its training identity under engine Y is not {rules.TRAINING_IDENTITY[:8]}... (§8 Q4)")
    shared = plan["recipes"].get(path)
    if shared is None:
        plan["recipes"][path] = {"sha256": pin, "config_sha256": own[path]["config_sha256"], "engine": "Y"}
    elif shared["config_sha256"] != own[path]["config_sha256"]:
        fail(RECIPE_ENGINES_DIFFER.format(name=name_r))


def stream_steps(arm: str) -> int:
    """e1's step by the arm's dose (REV4 §1.1: 600 removed -> 33, 48 added -> 38, none -> 38)."""
    return rules.DOSE_STEPS[rules.ARM_DOSE[arm]]


# ----- the sealed files and records -------------------------------------------------------------------------------


def manifest() -> dict:
    """Gate B's sealed MANIFEST (R_1-R_5 edits), checked against its pin."""
    path = ROOT / rules.MAN_PATH
    if not path.is_file() or mac.sha(path) != rules.MAN_SHA256:
        fail("Gate B's sealed MANIFEST.json is missing or differs from its pin")
    return json.loads(path.read_text())


def man1() -> dict:
    path = ROOT / rules.MAN1_PATH
    if not path.is_file() or mac.sha(path) != rules.MAN1_SHA256:
        fail("MAN1 (the REQ-20 manifest) is missing or differs from its pin")
    return json.loads(path.read_text())


def rescore_groups() -> list[str]:
    """LN-15e's re-score groups: Gate B's 8 unit groups from its sealed MANIFEST (checked against its pin), the groups
    the A1 contract's attributes unit holds (write_score_edit: "the 8 units"; Gate B's diagnostics --groups)."""
    groups = sorted(e["unit"] for e in manifest()["files"] if e.get("family") == "unit")
    if len(groups) != rules.UNITS or len(set(groups)) != len(groups) or not all(isinstance(g, str) for g in groups):
        fail(f"Gate B's sealed MANIFEST must list exactly {rules.UNITS} unit groups for LN-15e's re-score")
    return groups


def man_arms(man: dict) -> dict:
    """Gate B's MANIFEST: arm -> its entry (edit files only)."""
    return {e["arm"]: e for e in man["files"] if e.get("role") == "edit"}


def fixture() -> dict:
    path = ROOT / rules.GATE_A_FIXTURE
    if not path.is_file() or mac.sha(path) != rules.PREREG_FIXTURE_SHA256:
        fail("the expected fixture is missing or differs from its pin")
    projection = json.loads(path.read_text())["cap_projection"]
    return {"path": rules.GATE_A_FIXTURE, "sha256": rules.PREREG_FIXTURE_SHA256,
            "e1_upper_s": projection["e1_upper_s"], "training_s": projection["training_s"]}


def receipt(stage: str) -> dict:
    path = HERE / "setup" / f"packed-{stage}" / "setup-receipt.json"
    if not path.is_file():
        fail(f"no packed {stage} setup (pack_setup.py {stage}) before planning its pods")
    return json.loads(path.read_text())


def engine_receipt(engine: str) -> dict:
    """G4: the packed setup of ``engine`` must carry rules.ENGINES[engine] (a packed identity that differs refuses)."""
    rec = receipt(f"stage1-{engine}")
    if rec.get("engine_sha256") != rules.ENGINES[engine]:
        fail(f"the packed engine {engine} differs from its pin")
    return rec


def file_record(path: str, expected: str) -> tuple[dict, dict]:
    """A record file read once: its SHA-256 must be ``expected`` (the lead's hash on the command line)."""
    p = pathlib.Path(path)
    if not p.is_file():
        fail(f"{p.name}: no such record")
    digest = mac.sha(p)
    if not (isinstance(expected, str) and SHA_RE.fullmatch(expected)) or digest != expected:
        fail(f"{p.name}: its SHA-256 differs from the one given")
    try:
        doc = json.loads(p.read_text())
    except ValueError:
        fail(f"{p.name}: not JSON")
    if not isinstance(doc, dict):
        fail(f"{p.name}: not a JSON object")
    return doc, {"path": str(p), "sha256": digest}


def records(plan: dict) -> dict:
    return plan["records"]


def pinned_doc(pin: dict, what: str) -> dict:
    """A text-free record at ROOT/pin["path"]: its SHA-256 must be pin["sha256"]; returns its JSON object."""
    p = ROOT / pin["path"]
    if not p.is_file() or mac.sha(p) != pin["sha256"]:
        fail(f"{what} ({pin['path']}) is missing or differs from its pin")
    try:
        doc = json.loads(p.read_text())
    except ValueError:
        fail(f"{what}: not JSON")
    if not isinstance(doc, dict):
        fail(f"{what}: not a JSON object")
    return doc


def s3_safe_sha256() -> str:
    """s3_safe's pool hash from the S-pool record (pinned): s3_pool.sha256, equal to full_files["s3_safe.pool.json"]."""
    doc = pinned_doc(rules.S_POOL_RECORD, "the S-pool record")
    value = (doc.get("s3_pool") or {}).get("sha256")
    if doc.get("kind") != "stage1 s-pool record" or not SHA_RE.fullmatch(str(value)) or \
            (doc.get("full_files") or {}).get("s3_safe.pool.json") != value:
        fail("the S-pool record names no s3_safe pool SHA-256 (s3_pool.sha256 = full_files['s3_safe.pool.json'])")
    return value


def d2_entry(plan: dict, kind: str) -> dict:
    """The pins a J5 (rep_pass) or J8 (classifier) job carries in plan.json (addendum §19 point 3, §21): the filled pins
    file and REQ-8's record by SHA-256 and the pools (plant and decoy as both records give them; J5 also s3_safe from
    the S-pool record). Under a recorded D-2 fallback that covers the kind: the fallback record, no plant or decoy."""
    fb = records(plan).get("d2_fallback")
    extra = {"s3_safe": s3_safe_sha256()} if kind == "rep_pass" else {}
    if fb and kind in fb["jobs"]:
        return {"fallback": {"path": fb["path"], "sha256": fb["sha256"]}, "pools": extra}
    filled = pinned_doc(rules.D2_POOL_PINS, "the filled pool pins file (D-2)")
    req8 = pinned_doc(rules.D2_REQ8_RECORD, "REQ-8's plant record")
    for name, pin in rules.D2_POOLS.items():
        if ((filled.get("pools") or {}).get(name) or {}).get("sha256") != pin or \
                ((req8.get("pools") or {}).get(name) or {}).get("sha256") != pin or \
                (req8.get("full_files") or {}).get(f"{name}.pool.json") != pin:
            fail(f"the {name} pool's SHA-256 in the filled pins or REQ-8's record is not its pin")
    return {"pool_pins": dict(rules.D2_POOL_PINS), "req8_record": dict(rules.D2_REQ8_RECORD),
            "pools": {**rules.D2_POOLS, **extra}}


def c3_entry(plan: dict) -> dict:
    """J14's inputs (addendum §22 point 2): the subsample file and its record, by SHA-256 from the lead's record."""
    rec = records(plan)
    if rec.get("c3_fallback"):
        fail("C3 is dropped: the §22 point 2 fallback record is recorded (C3's smoke never runs)")
    if not rec.get("c3"):
        fail("C3 needs the lead's subsample record (record-c3) or its fallback record (record-c3-fallback)")
    return {"subsample": dict(rec["c3"]["subsample"]), "record": dict(rec["c3"]["record"])}


def plan_ab_derived(ab: dict) -> bool:
    """A plan-A/B record the kit derived itself: Gate B's verdict file by its pin, the one field, the rule's code."""
    try:
        return (ab.get("sha256") == rules.GATEB_VERDICT["sha256"] and ab.get("derived") is True
                and ab.get("field") == ".".join(rules.GATEB_VERDICT_FIELD)
                and ab.get("code") == rules.plan_code_for(ab.get("sigma_pp")))
    except ValueError:
        return False


def plan_ab_checked(plan: dict) -> dict | None:
    """G3 at every use (round-2 fix VG2-1 / VR2-1): plan.json's plan-A/B record re-derived from Gate B's verdict file
    itself. The file at ROOT / rules.GATEB_VERDICT["path"] must hash to its pin; its one field's value and the rule's
    code must equal the record's sigma_pp and code. A hand edit of plan.json (one that keeps sigma and code in
    agreement too) or a verdict file changed after recording refuses. None while no record exists."""
    ab = records(plan).get("plan_ab")
    if ab is None:
        return None
    path = ROOT / rules.GATEB_VERDICT["path"]
    if not path.is_file() or mac.sha(path) != rules.GATEB_VERDICT["sha256"]:
        fail("Gate B's verdict file (rules.GATEB_VERDICT) is missing or differs from its pin: the plan-A/B record "
             "cannot be re-derived (G3)")
    try:
        sigma = rules.verdict_sigma(json.loads(path.read_text()))
        code = rules.plan_code_for(sigma)
    except ValueError as exc:
        fail(f"Gate B's verdict file: {exc} (G3)")
    if not plan_ab_derived(ab) or type(ab.get("sigma_pp")) is not float or ab["sigma_pp"] != sigma \
            or ab["code"] != code:
        fail("the plan-A/B record is not the one derived from Gate B's verdict file (G3: its sigma_pp and code must "
             "equal the file's field and the rule's code)")
    return ab


# ----- seeds, jobs and blocks ---------------------------------------------------------------------------------------


def dev_seed(seed) -> bool:
    return isinstance(seed, int) and not isinstance(seed, bool) and rules.DEV_SEEDS[0] <= seed <= rules.DEV_SEEDS[1]


def default_engine(job: dict) -> str:
    if job["kind"] in rules.Y_ONLY_KINDS or (job["kind"] == "ref_train" and job.get("recipe") == "bqi") \
            or job.get("role") == "bqi_own_a0":
        return "Y"
    return rules.ENGINE_DEFAULT


# (G, 25 Oct) the recipe a kind's job record always names, because its step's script pins it (J5: REQ-3's
# representation_pass.json pins recipe S); new plans, deferred hosts and the re-run keys all use it. Kit round 34:
# B14's similarity pass runs REC (overlap_similarity.json pins its config SHA-256)
RECORDED_RECIPE = {"rep_pass": "S", "similarity": "B"}


def default_recipe(job: dict) -> str | None:
    kind = job["kind"]
    if kind in ("arm", "a0_arm", "regenerate", "cert_c1", "c0", "classifier", "retrain", "a1_rescore"):
        return "S"                                   # LN-15e: the A1 contract's recipe S                                   # §8 Q4: recipe S for new arms (training identity checked)
    if kind in RECORDED_RECIPE:
        return RECORDED_RECIPE[kind]                 # (G) J5: recipe S, as its two steps pass it
    if kind == "cert_c2":
        return "bqi"
    if kind in ("b10_certify", "ref_eval", "safe_lora", "w1_18", "l1_scan"):
        return "B"                                   # REC: B10's references, the guard's recipe, the scans
    return job.get("recipe")


def recipe_of(job: dict) -> str | None:
    """The recipe a job record names for the re-run keys: RECORDED_RECIPE's for its kind (an older record of that
    kind may name another), else the record's own."""
    return RECORDED_RECIPE.get(job["kind"]) or job.get("recipe")


def steps_of(job: dict) -> int | None:
    kind, arm = job["kind"], job.get("arm")
    if kind in ("arm", "regenerate") and arm in rules.ARM_DOSE:
        return stream_steps(arm)
    if kind in ("a0_arm", "ref_train", "cert_c2", "retrain"):
        return rules.DOSE_STEPS["none"]
    if kind in ("cert_c1", "c0"):
        return rules.DOSE_STEPS["remove"]
    return None


def check_job(job: dict, index: int, host_jobs: list[dict], block: str, plan: dict, reused: set) -> None:
    """One job's own rules; every refusal names ids only."""
    if set(job) - JOB_KEYS or "kind" not in job:
        fail(f"job {index}: keys must be among {sorted(JOB_KEYS)}")
    kind, arm, seed, points = job["kind"], job.get("arm"), job.get("seed"), job.get("points")
    if kind not in rules.KINDS:
        fail(f"job {index}: unknown kind {kind!r}")
    if kind not in rules.BLOCK_KINDS[block]:
        fail(f"job {index}: a {kind} job does not belong to block {block}")
    if kind not in rules.LINKED_KINDS and job.get("regen_source") is not None:
        fail(f"job {index}: regen_source belongs to a linked pass only (a J3 O-only pass, LN-15e's re-score)")
    if job.get("engine") not in (None, *rules.ENGINES):
        fail(f"job {index}: unknown engine")
    if seed is not None and not dev_seed(seed):
        fail(f"job {index}: seed {seed!r} is not a development seed")
    if kind in rules.POINT_KINDS:
        allowed = rules.POINT_KINDS[kind] or rules.REF_EVAL_SCALES + ("prefix",)
        if not (isinstance(points, list) and points and len(set(points)) == len(points) and set(points) <= set(allowed)):
            fail(f"job {index}: {kind} points must be a non-empty list among {list(allowed)}")
        if kind == "b10_certify" and points[0] != "certify":
            fail(f"job {index}: the certification pod runs the certify evaluation first (B10: a gated run starts "
                 "with certify)")
    elif points is not None:
        fail(f"job {index}: points belong to an evaluation-only job")
    if kind in RECORDED_RECIPE and job.get("recipe") not in (None, RECORDED_RECIPE[kind]):
        fail(f"job {index}: a {kind} job runs recipe {RECORDED_RECIPE[kind]} (its script's settings pin it)")
    if kind in rules.OEXT_ONLY_KINDS and records(plan).get("oext_fallback"):
        fail(f"job {index}: a {kind} job is an O-ext pass only; fallback (c) ({rules.OEXT_FALLBACK_STATUS}) is "
             "recorded, so it never runs")
    no_arm = ("w1_18", "rep_pass", "untuned_answers", "l1_scan", "classifier", "cert_c3", "similarity")
    if kind in no_arm and (arm is not None or seed is not None):
        fail(f"job {index}: a {kind} job has no arm or seed")
    if kind in ("arm", "a0_arm") and job.get("role") != "bqi_own_a0":
        fail(f"job {index}: training arms come from the block's deal only (§8 Q3)")
    if job.get("role") not in (None, "bqi_own_a0"):
        fail(f"job {index}: unknown role")
    if job.get("role") == "bqi_own_a0" and not (kind == "a0_arm" and arm == "a0" and seed in range(1102, 1108)):
        fail(f"job {index}: B+Qi's own a0 is an a0_arm at 1102-1107")
    if kind == "regenerate":
        ok = arm in ("a0", "R") and (seed in rules.REUSED_SEEDS or (arm, seed) in reused)
        if not ok:
            fail(f"job {index}: a regeneration is a0 or R at a reused seed (1101-1103, or a reused R_4/R_5)")
    if kind == "o_only":
        if arm == "theta0":
            if seed is not None or job.get("regen_source") is not None:
                fail(f"job {index}: theta0's O-only pass has no seed or regeneration")
        else:
            source = job.get("regen_source")
            ok = (arm in ("a0", "R") and isinstance(source, int) and not isinstance(source, bool)
                  and 0 <= source < index and host_jobs[source]["kind"] == "regenerate"
                  and (host_jobs[source].get("arm"), host_jobs[source].get("seed")) == (arm, seed))
            if not ok:
                fail(f"job {index}: an O-only pass on {arm} must name its regeneration earlier on the same pod "
                     "(no state moves between pods)")
    if kind == "retrain" and not (arm == "a0" and seed in rules.RESCORE_SEEDS):
        fail(f"job {index}: LN-15e's retrain is a0 at {list(rules.RESCORE_SEEDS)} (REV4 §14.2)")
    if kind == "a1_rescore":
        source = job.get("regen_source")
        ok = (arm == "a0" and seed in rules.RESCORE_SEEDS and isinstance(source, int) and not isinstance(source, bool)
              and 0 <= source < index and host_jobs[source]["kind"] == "retrain"
              and (host_jobs[source].get("arm"), host_jobs[source].get("seed")) == (arm, seed))
        if not ok:
            fail(f"job {index}: LN-15e's re-score on a0 at {seed} must name its retrain (a0, same seed) earlier on the "
                 "same pod (its q and e1 states never move between pods)")
    if kind == "transfer_report" and arm != "theta0":
        fail(f"job {index}: the transfer report is theta0's")
    if kind in ("cert_c1", "c0") and (arm, seed) != ("R", 1101):
        fail(f"job {index}: {kind} runs Gate B's R_1 edit at seed 1101")
    if kind == "cert_c2" and (arm, seed) != ("bqi", 1101):
        fail(f"job {index}: C2 trains B+Qi at seed 1101")
    if kind == "cert_c3":
        c3_entry(plan)
    if kind == "b10_certify" and (arm, seed) != ("a0", 1101):
        fail(f"job {index}: B10's certification runs a0 at seed 1101")
    if kind in ("ref_eval", "safe_lora") and not (arm == "a0" and seed in rules.A0_SEEDS):
        fail(f"job {index}: {kind} evaluates an a0 state at 1101-1107")
    if kind == "ref_train":
        if job.get("recipe") not in ("G", "bqi") or arm != job.get("recipe") or seed not in range(1102, 1108):
            fail(f"job {index}: a reference training arm is recipe G or bqi (arm = recipe) at 1102-1107")
    engine = job.get("engine") or default_engine(job)
    if kind in rules.Y_ONLY_KINDS and engine != "Y":
        fail(f"job {index}: {kind} runs on engine Y")
    if kind in rules.X_ONLY_KINDS and engine != "X":
        fail(f"job {index}: {kind} runs on engine X (addendum §26: its source unit ran on X and B17 is pinned on X)")
    if kind in ("retrain", "a1_rescore") and engine != "X":
        fail(f"job {index}: LN-15e runs on engine X (the A1 contract and its sealed set are engine X's)")
    if kind == "ref_train" and job.get("recipe") == "bqi" and engine != "Y":
        fail(f"job {index}: B+Qi runs on engine Y only")
    if job.get("role") == "bqi_own_a0" and engine != "Y":
        fail(f"job {index}: B+Qi's own a0 runs on engine Y")
    if kind in rules.D2_KINDS and engine != "X":
        fail(f"job {index}: {kind} runs on engine X (the D-2 settings and every W1 script pin X; addendum §13 point 1)")
    if kind == "similarity" and engine != "X":
        fail(f"job {index}: B14's similarity pass runs on engine X (its settings pin engine X's identity; kit round 34)")


A0_CALIBRATIONS = ("a0_arm", "ref_train")   # both run the engine's calibrate --arms a0 into round1/<seed>-a0-e1-a<n>


def check_host(jobs: list[dict]) -> None:
    """One pod's own rules: two a0 calibrations at one seed (an a0 arm and a recipe-G or B+Qi reference, or B+Qi and
    its own a0) would share round1/<seed>-a0-e1-a<n>, and the engine refuses the second as other science."""
    seeds = [j.get("seed") for j in jobs if j["kind"] in A0_CALIBRATIONS]
    if len(set(seeds)) != len(seeds):
        fail("a pod holds two a0 calibrations at one seed (they would share one run folder); put them on two pods")
    for k, j in enumerate(jobs):
        if j["kind"] == "rep_pass" and not any(e["kind"] == "untuned_answers" for e in jobs[:k]):
            fail("J5 (rep_pass) needs J6 (untuned_answers) earlier on its pod: its s3_orig pools-only pass reads "
                 "J6's s3_orig pool (both passes run, REQ-3)")


def job_keys(job: dict) -> list[tuple]:
    """A job's identity for the re-run rule, one key per evaluation point."""
    base = (job["kind"], job.get("arm"), job.get("seed"), job.get("engine") or default_engine(job),
            recipe_of(job) or default_recipe(job), job.get("role"))
    return [(*base, p) for p in job.get("points") or [None]]


def refuse_duplicates(plan: dict, jobs: list[dict]) -> None:
    """PREREG's re-run rule (read the first complete attempt; never re-run a completed job): a block never plans a
    run that it or an earlier block already plans (G6)."""
    seen = {k for h in plan["hosts"].values() for j in h["jobs"] for k in job_keys(j)}
    seen |= {k for b in plan["blocks"].values() for h in (b.get("pending") or {}).values() for j in h["jobs"]
             for k in job_keys(j)}
    for job in jobs:
        for k in job_keys(job):
            if k in seen:
                fail(f"{job['kind']} {job.get('arm')} at {job.get('seed')}"
                     + (f" ({k[-1]})" if k[-1] else "") + ": planned twice (never re-run a planned or completed job)")
            seen.add(k)


def gate_bqi_pairs(plan: dict, jobs: list[dict]) -> None:
    """G4 after a failed certificate: B+Qi on Y is paired with its own a0 on Y at the same seeds, each once (YB X-10;
    no Y unit is paired with an X unit)."""
    cert = records(plan).get("certificate")
    if cert is None or cert["pass"]:
        return
    bqi = sorted(j["seed"] for j in jobs if j["kind"] == "ref_train" and j.get("recipe") == "bqi")
    own = sorted(j["seed"] for j in jobs if j.get("role") == "bqi_own_a0")
    if bqi != own or len(set(bqi)) != len(bqi):
        fail("after a failed certificate every B+Qi seed needs its own a0 on Y at that seed, each once "
             f"(B+Qi {bqi}, own a0 {own})")


def branch_name(plan: dict) -> str:
    rec = records(plan).get("branch")
    return rec["branch"] if rec else rules.BRANCH_DEFAULT


def bank500_planned(plan: dict) -> bool:
    for b in plan["blocks"].values():
        for h in list(b.get("pending", {}).values()):
            if any(j["kind"] in rules.BANK500_KINDS for j in h["jobs"]):
                return True
    return any(j["kind"] in rules.BANK500_KINDS for h in plan["hosts"].values() for j in h["jobs"])


def gate_g1(plan: dict, block: str, jobs: list[dict]) -> None:
    """G1 (REV4 §6.3; addendum §13 point 2)."""
    branch = records(plan).get("branch")
    if any(j["kind"] in rules.BANK500_KINDS for j in jobs) and branch is None:
        fail("a 500-bank job before W1-18's branch record (or a 'Branch full by default' record) refuses")
    if any(j["kind"] == "transfer_report" for j in jobs) and branch_name(plan) != "128":
        fail("the LN-14 transfer report runs under Branch 128 only")
    if block != "S1-0":
        has_s10 = any(h["block"] == "S1-0" for h in plan["hosts"].values())
        default = branch is not None and branch.get("source") == "default"
        if not has_s10 and not default:
            fail("W1-18 is the first job of the first stage-1 pod: plan block S1-0 first (or record "
                 "'Branch full by default')")


def gate_g4(plan: dict, block: str, jobs: list[dict]) -> None:
    """G4: a Y job before a recorded passing certificate refuses (exceptions in the module doc)."""
    cert = records(plan).get("certificate")
    for j in jobs:
        if j["engine"] != "Y" or block == "cert":
            continue
        bqi = j["kind"] == "ref_train" and j.get("recipe") == "bqi"
        own_a0 = j.get("role") == "bqi_own_a0"
        if cert is not None and cert["pass"] and not own_a0:
            continue
        if cert is not None and not cert["pass"] and (bqi or own_a0):
            continue
        fail(f"a {j['kind']} job on engine Y before a recorded passing X -> Y certificate refuses"
             + (" (B+Qi's own a0 runs only after a failed certificate)" if own_a0 else ""))


def gate_records(plan: dict, jobs: list[dict]) -> None:
    """Q16, Q17, K = 12."""
    rec = records(plan)
    for j in jobs:
        if j["kind"] == "cert_c2" and rec.get("thresholds") is None:
            fail("C2 refuses before the lead's binding-check thresholds record (Q17)")
        if j["kind"] == "ref_eval" and "prefix" in (j.get("points") or []) and rec.get("prefix") is None:
            fail("the SP prefix point refuses before its pinned text SHA-256 is recorded (Q16)")
        if j["kind"] == "safe_lora" and "k12" in (j.get("points") or []) and \
                "safe_lora_k12" not in (rec.get("user_yes") or {}):
            fail("Safe LoRA K = 12 refuses without the user's recorded yes (FC-27)")


def gate_certification(plan: dict, jobs: list[dict]) -> None:
    """LS-08 at init-block (round 32, K3) and at every release: an evaluation-only reference needs a recorded passing
    B10 certification; after a failed one (pass false) every reference stops."""
    cert = records(plan).get("certification")
    if any(j["kind"] in ("ref_eval", "safe_lora") for j in jobs) and not (cert and cert["pass"]):
        if cert is not None and cert["pass"] is False:
            fail("a failed B10 certification is recorded (pass false): every evaluation-only reference stops (LS-08)")
        fail("an evaluation-only reference refuses before a passing B10 certification (REV4 §5.4)")


def moved_hosts(plan: dict) -> dict:
    """host -> the hosts its jobs moved to (deferrals and requeues, ``from`` -> ``to``; a move that re-ran nothing has
    no target). Round 30 (R6): seal.py skips a moved host that is not done and lists it with these targets."""
    out: dict = {}
    for d in [*(plan.get("deferrals") or []), *(plan.get("requeues") or [])]:
        targets = out.setdefault(d["from"], [])
        if d.get("to") and d["to"] not in targets:
            targets.append(d["to"])
    return out


def block_complete(plan: dict, block: str) -> bool:
    b = plan["blocks"].get(block)
    decided = not_run_decided(plan, block) if b and block != "A" else {}   # round 32 (K2): not block A (its route)
    if decided:
        b = settled_view(b, decided)                  # decided pending hosts and the launches they fill are settled
    if not b or b.get("pending") or b["released"] < len(b["launches"]):
        return False                                  # every launch released, judge launches included
    moved = {d["from"] for d in plan["deferrals"]} | {r["from"] for r in plan.get("requeues") or []}
    for name, h in plan["hosts"].items():
        if h["block"] == block and name not in moved and any(j.get("status") != "complete" and (name, i) not in decided
                                                             for i, j in enumerate(h["jobs"])):
            return False
    if block != "A" and block_open_jobs(plan, block, decided):   # K2: a job a move left behind needs a decision
        return False
    if block == "A" and block_a_open(plan):           # round 3c (VP3b-3): every job the block-A plan requires
        return False
    released_judges = {x["judge"]["judge"] for k, x in enumerate(b["launches"]) if x.get("judge") and k < b["released"]}
    if block != "A" and released_judges and \
            not released_judges <= judges_done(plan, block) | set(judge_not_run(plan, block)):
        return False                     # round 30 (R2): a judge launch is done only with its valid record;
    return True                          # round 31 (K1): or when a recorded judge not-run decision names it


def gate_order(plan: dict, block: str) -> None:
    """G3 and G5."""
    rec = records(plan)
    if block in plan["blocks"]:
        fail(f"block {block} is already planned (defer adds hosts)")
    if block == "S1-0" and plan["hosts"]:
        fail("block S1-0 (W1-18 alone) is the first stage-1 pod")
    if block == "S1-0" and rec.get("branch") is not None:
        fail("block S1-0: a branch record exists ('Branch full by default' says W1-18 cannot run)")
    ab = plan_ab_checked(plan)                       # re-read from the verdict file at every block (VG2-1)
    if ab is not None and ab["code"] == "none":
        fail(f"block {block}: the plan-A/B record says no stage 1 (sigma above 6.0 pp): no stage-1 pod")
    if block != "S1-0" and rec.get("gateb_final") is None:
        fail(f"block {block}: Gate B's final record is not recorded (G3)")
    if block in ("A", "certify", "B", "C"):
        if ab is None:
            fail(f"block {block}: the plan-A/B record is not recorded (G3)")
        if ab.get("gateb_final_sha256") != rec["gateb_final"]["sha256"]:
            fail(f"block {block}: the plan-A/B record does not name the recorded Gate B final record (G3)")
        if not plan_ab_derived(ab):
            fail(f"block {block}: the plan-A/B record is not the one derived from Gate B's verdict file (G3)")
    if block in ("certify", "B"):
        if not block_complete(plan, "A"):
            fail(f"block {block}: block A is not complete (G5){block_a_open_note(plan)}")
        if "A" not in plan["seals"]:
            fail(f"block {block}: block A is not sealed (seal.py block A)")
    if block == "C":
        if rec["plan_ab"]["code"] != "B":
            fail("block C runs under plan B only")
        if not block_complete(plan, "B"):
            fail("block C: block B is not complete (G5)")


# ----- edits (by SHA-256 only, from MAN1, Gate B's MANIFEST or a lead's sealed record) -----------------------------


def edit_sources(plan: dict) -> dict:
    """(arm, draw) -> [{path, sha256, source}] over every source; draw is None except for R."""
    out: dict = {}
    m1 = {(e["path"], e["sha256"]) for e in man1()["entries"] if e.get("role") == "sealed record"}
    for arm, pin in rules.MAN1_EDIT_ARMS.items():
        if (pin["path"], pin["sha256"]) in m1:
            out.setdefault((arm, None), []).append({**pin, "source": "MAN1"})
    for e in man_arms(manifest()).values():
        if e.get("family") == "R" and e.get("draw") in rules.GATEB_R_DRAWS:
            out.setdefault(("R", e["draw"]), []).append({"path": str(SEAL_OUT / e["path"]), "sha256": e["sha256"],
                                                         "source": "gateb-MAN", "engine_arm": e["arm"]})
    for rec in records(plan)["sealed"]:
        p = pathlib.Path(rec["path"])
        if not p.is_file() or mac.sha(p) != rec["sha256"]:
            fail("a recorded sealed edit record is missing or changed")
        for e in json.loads(p.read_text())["edits"]:
            out.setdefault((e["arm"], e.get("draw")), []).append({"path": e["path"], "sha256": e["sha256"],
                                                                  "source": f"sealed:{rec['sha256']}"})
    return out


def resolve_edit(job: dict, sources: dict, required: bool) -> dict | None:
    arm = job["arm"]
    if job["kind"] not in ("arm", "regenerate", "cert_c1", "c0") or arm == "a0":
        return None
    key = (arm, rules.r_draw(job["seed"]) if arm == "R" else None)
    found = {(e["path"], e["sha256"]): e for e in sources.get(key, [])}
    if len(found) > 1:
        fail(f"{arm} at {job['seed']}: two sources name different edit files; the lead decides")
    if not found:
        if required:
            fail(f"{arm} at {job['seed']}: no edit file in MAN1, Gate B's MANIFEST or a recorded sealed record")
        return None
    entry = next(iter(found.values()))
    path = ROOT / entry["path"]
    if not path.is_file() or mac.sha(path) != entry["sha256"]:
        fail(f"{arm} at {job['seed']}: the edit file is missing or its SHA-256 is not the sealed one")
    return dict(entry)


def similarity_entry(plan: dict) -> dict:
    """Kit round 34 (J22): what B14's similarity pass reads, by SHA-256, for its job record (the runner checks every
    packed file against it; the runner's record checks the output against stage1_rules): the script and its settings
    at their stage1_rules.S1_CODE pins, the prepared manifest (PREPARED_MANIFESTS) and its dev bank (SIM_DEV_BANK), and
    each add set of SIM_ADD_SETS. An add set is bound like an arm's edit (edit_sources: MAN1, Gate B's MANIFEST, the
    lead's recorded sealed records): exactly one file for its arm, at the kit's pin, on disk at that SHA-256; and it is
    the file the arm trained on: every S1, S3 or S4 arm run in plan.json that names an edit names this one, and at
    least one such run is complete (the B14 report later checks each add arm's unit against edit-<this SHA-256>).
    Refuses (arm names and hash prefixes only) otherwise."""
    sources = edit_sources(plan)
    add_sets = {}
    for name, pin in sorted(rules.SIM_ADD_SETS.items()):
        found = {(e["path"], e["sha256"]): e for e in sources.get((name, None), [])}
        if len(found) != 1:
            fail(f"B14's add set {name}: {len(found)} edit files are named for arm {name} in MAN1, Gate B's MANIFEST "
                 "and the recorded sealed records; exactly one must be (kit round 34)")
        entry = next(iter(found.values()))
        if entry["sha256"] != pin:
            fail(f"B14's add set {name}: the edit sources name {entry['sha256'][:12]}..., not the kit's pin "
                 f"{pin[:12]}... (stage1_rules.SIM_ADD_SETS)")
        path = ROOT / entry["path"]
        if not path.is_file() or mac.sha(path) != pin:
            fail(f"B14's add set {name}: the edit file is missing or its SHA-256 is not the pin")
        runs = [j for h in plan["hosts"].values() for j in h["jobs"] if j["kind"] == "arm" and j.get("arm") == name]
        named = {(j.get("edit") or {}).get("sha256") for j in runs if j.get("edit")}
        if named != {pin} or not any(j.get("status") == "complete" for j in runs):
            fail(f"B14's add set {name}: the pass reads the edit file the {name} arm runs trained on, but plan.json's "
                 f"{len(runs)} {name} run(s), {sum(j.get('status') == 'complete' for j in runs)} complete, name "
                 f"{sorted(str(d)[:12] + '...' for d in named)} (the pin is {pin[:12]}...)")
        add_sets[name] = {"path": entry["path"], "sha256": pin, "source": entry["source"]}
    return {"script": {"path": rules.SIM_SCRIPT, "sha256": rules.S1_CODE[rules.SIM_SCRIPT]},
            "settings": {"path": rules.SIM_SETTINGS, "sha256": rules.S1_CODE[rules.SIM_SETTINGS]},
            "manifest_sha256": rules.PREPARED_MANIFESTS[rules.PREPARED_NAME], "dev_bank": dict(rules.SIM_DEV_BANK),
            "add_sets": add_sets}


# ----- host records -----------------------------------------------------------------------------------------------


def host_record(plan: dict, block: str, role: str, jobs: list[dict], sealed_files_sha256: str | None,
                launch: int) -> dict:
    engines = {j["engine"] for j in jobs}
    if len(engines) != 1:
        fail(f"block {block}: one engine per pod (G4)")
    if rules.arm_count(jobs) > rules.MAX_ARMS_PER_POD:
        fail(f"block {block}: a pod would hold {rules.arm_count(jobs)} counted jobs, more than "
             f"{rules.MAX_ARMS_PER_POD} (§8 Q5)")
    engine = engines.pop()
    cap = rules.cap_hours(jobs)
    return {"wave": block, "block": block, "launch": launch, "role": role, "base_eval": False, "engine": engine,
            "engine_sha256": rules.ENGINES[engine], "stage": f"stage1-{engine}",
            "sealed_files_sha256": sealed_files_sha256, "cap_hours": cap, "guard_usd": rules.guard_usd(cap),
            "spend_upper_usd": rules.pod_spend_usd(jobs), "counted": rules.arm_count(jobs), "jobs": jobs,
            "done": False, **rules.POD_SIZES}


def new_host_name(plan: dict, block: str) -> str:
    prefix = rules.HOST_PREFIX[block]
    names = set(plan["hosts"]) | {n for b in plan["blocks"].values() for n in b.get("pending", {})}
    taken = [int(h.rsplit("-", 1)[1]) for h in names if h.rsplit("-", 1)[0] == prefix]
    return f"{prefix}-{max(taken, default=0) + 1}"


def skeleton() -> dict:
    return {"name": "stage1-olmo", "brief": "notes/b15-brief.md (2026-10-23); addendum §17",
            "status": "stage 1 on OLMo-2-1B (per-pod user approval)", "fixture": fixture(),
            "engines": dict(rules.ENGINES), "prepared": dict(rules.PREPARED_MANIFESTS),
            "records": {"gateb_final": None, "plan_ab": None, "branch": None, "branch_history": [],
                        "certificate": None, "certification": None, "thresholds": None, "prefix": None,
                        "user_yes": {}, "sealed": [], "oext_fallback": None, "c3": None, "c3_fallback": None,
                        "d2_fallback": None, "block_a_plan": None, "block_a_plan_history": [],
                        "block_a_not_run": []},
            "recipes": {}, "reference": None, "blocks": {}, "contingency": {}, "seals": {}, "deferrals": [],
            "requeues": [], "hosts": {}}


def load() -> dict:
    return mac.load_plan() if mac.PLAN.exists() else skeleton()


def funding_record(path: str, group: str) -> dict:
    """The lead's record of the user's top-up (the user's rule: "A funding event is any RunPod top-up I make and say
    is for that stage-1 block (block A first); it must cover the block's cap-based need before the block launches")."""
    p = pathlib.Path(path)
    try:
        rec = json.loads(p.read_text())
    except (OSError, ValueError):
        fail("--funding FILE: not a readable JSON record")
    if not isinstance(rec, dict) or any(k not in rec for k in FUNDING_KEYS):
        fail(f"--funding FILE must hold {list(FUNDING_KEYS)}")
    amount = rec["amount_usd"]
    if not rules.finite_number(amount) or amount <= 0:
        fail("the funding record's amount_usd must be a positive finite number")
    if rec["source"] == FUNDING_SOURCE_RULE:
        funding_rule_decision(rec)                      # addendum §36: no covering top-up, by the user's rule
    elif rec["source"] != FUNDING_SOURCE:
        fail(f"the funding record's source must be {FUNDING_SOURCE!r} or {FUNDING_SOURCE_RULE!r}")
    if not (isinstance(rec["user_words"], str) and rec["user_words"].strip()):
        fail("the funding record needs the user's words, verbatim")
    if not (isinstance(rec["recorded_by"], str) and rec["recorded_by"].strip()):
        fail("the funding record needs recorded_by")
    try:
        when = dt.datetime.fromisoformat(str(rec["utc"]).replace("Z", "+00:00"))
        if when.utcoffset() != dt.timedelta(0):
            raise ValueError
    except (ValueError, TypeError):
        fail("the funding record's utc is not a UTC time")
    if when > dt.datetime.now(dt.timezone.utc):
        fail("the funding record's utc is in the future")
    if rec["block"] != group:
        fail(f"the funding record is for block {rec['block']!r}; this needs block {group}'s funding event")
    out = {**{k: rec[k] for k in FUNDING_KEYS}, "path": str(p.resolve()), "sha256": mac.sha(p)}
    if rec["source"] == FUNDING_SOURCE_RULE:
        out["user_decision"] = {"path": rec["user_decision"]["path"], "sha256": rec["user_decision"]["sha256"]}
    return out


def funding_rule_decision(rec: dict) -> None:
    """Addendum §36 (the user, 29 Oct 2026: "no just start it now ill fund it when i feel like this is a rule"): a
    funding record whose source is FUNDING_SOURCE_RULE starts a block from the balance without a covering top-up. Its
    amount_usd is the plan's cap-based need; it names the user's decision record {path, sha256} (path absolute or
    relative to the repository), which must hash as named at every use and be that decision's kind with the user's
    words."""
    d = rec.get("user_decision")
    if not (isinstance(d, dict) and isinstance(d.get("path"), str) and SHA_RE.fullmatch(str(d.get("sha256")))):
        fail("a funding record under the user's start-from-the-balance rule must name its decision record {path, sha256}")
    q = pathlib.Path(d["path"])
    q = q if q.is_absolute() else ROOT / q
    if not q.is_file() or mac.sha(q) != d["sha256"]:
        fail("the funding record's user decision record is missing or differs from its SHA-256")
    try:
        doc = json.loads(q.read_text())
    except ValueError:
        fail("the funding record's user decision record is not JSON")
    if not isinstance(doc, dict) or doc.get("kind") != FUNDING_RULE_KIND or not str(doc.get("user_words") or "").strip():
        fail(f"the funding record's decision record is not a {FUNDING_RULE_KIND!r} record with the user's words")


def planned_parts(plan: dict, group: str) -> list[str]:
    """The group's planned parts in PLANNING order (round 3a fix, VG3-3): each block record carries ``seq``, the
    number of blocks planned before it, because plan.json is saved with sort_keys and reads back alphabetically (A,
    S1-0, cert). A record without seq (a plan.json written before this fix) sorts first, by rules.BLOCKS."""
    parts = [b for b in plan["blocks"] if rules.FUNDING_BLOCK[b] == group]
    return sorted(parts, key=lambda b: (plan["blocks"][b].get("seq", rules.BLOCKS.index(b) - len(rules.BLOCKS)),
                                        rules.BLOCKS.index(b)))


def group_launches(plan: dict, group: str) -> list:
    """The need launches of the group's parts planned so far, in planning order."""
    return [launch for b in planned_parts(plan, group) for launch in plan["blocks"][b]["need_launches"]]


def group_anchor(plan: dict, group: str) -> dict | None:
    """The group's first funding record (block A's: S1-0's), re-hashed from its file (VG3-4): every later init and
    re-plan in the group must also be covered by it (the user's rule as §20 point 1 applies it: block A's funding event
    covers the whole group before S1-0 launches). None while no part is planned."""
    parts = planned_parts(plan, group)
    if not parts:
        return None
    anchor = plan["blocks"][parts[0]]["funding"]
    p = pathlib.Path(str(anchor.get("path")))
    try:
        on_disk = json.loads(p.read_text()) if p.is_file() else None
    except ValueError:
        on_disk = None
    if on_disk is None or mac.sha(p) != anchor.get("sha256") or not isinstance(on_disk, dict) or \
            on_disk.get("amount_usd") != anchor.get("amount_usd") or on_disk.get("block") != group:
        fail(f"block {group}'s first funding record ({parts[0]}'s) is missing or differs from its recorded SHA-256; "
             "it must stay at its recorded path, unchanged")
    return anchor


CERT_FLOOR_POD = ({"kind": "cert_c1", "arm": "R", "seed": 1101}, {"kind": "cert_c2", "arm": "bqi", "seed": 1101},
                  {"kind": "cert_c3"})    # G4 and J12-J14: one pod (round 3b: c0 moved to the LN-12 pod, §26)


# ----- the block-A launch plan (round 3a; addendum §20 point 1; the user's rule) -----------------------------------
# A pre-set, outcome-free plan of every launch that block A's funding event pays for, recorded before the group's
# first launch (S1-0): S1-0 -> the cert pod -> the diagnostics pod -> the LN-12 pod(s) -> the arm launches (a split of
# the deal) -> the judge launches. S1-0's init needs the [D20] funding need over that whole sequence; every later
# init-block and release in the group refuses a launch that departs from it (another order, more pods, a pod with a
# larger cap or spend, a job the plan does not hold), unless a re-plan whose need the group's first funding record
# still covers is recorded first (record-block-a-replan).

BLOCK_A_PLAN_KIND = "stage1 block-a launch plan"
BLOCK_A_PLAN_KEYS = {"kind", "version", "plan_code", "launches", "not_in_plan", "utc", "recorded_by"}
PLAN_ROLE_PART = {"s1_0": "S1-0", "cert": "cert", "diagnostics": "A", "ln12": "A", "arms": "A", "judge": "A"}
PLAN_ROLE_KINDS = {"s1_0": ("w1_18",), "cert": rules.BLOCK_KINDS["cert"], "diagnostics": rules.DIAG_KINDS,
                   "ln12": ("regenerate", "o_only", "transfer_report", "c0", "retrain", "a1_rescore")}
GROUP_A_PARTS = ("S1-0", "cert", "A")
DEFAULT_SPLIT = {"A": (2, 2, 1), "B": (2, 2)}   # the arm launches when the lead records no plan (plan A: 5 pods)
DEFAULT_DIAG_POD = ({"kind": "untuned_answers"}, {"kind": "rep_pass"}, {"kind": "l1_scan"}, {"kind": "classifier"})
LN12_UNITS = (("a0", 1101), ("a0", 1102), ("a0", 1103), ("R", 1101), ("R", 1102), ("R", 1103))   # brief J2/J3
REJUDGED_UNITS = LN12_UNITS + (("theta0", None),)   # §17 Q14 + §25 point 2: the 6 reused units and theta0's unit
#                                                   are re-judged on the stage-1 judge pods (27 units under plan A)
C0_JOB = {"kind": "c0", "arm": "R", "seed": 1101}   # J11 on engine X in the LN-12 pod (addendum §26)
PLAN_TOL = 1e-9
NOT_IN_PLAN = ({"job": "V2a: LN-15e's scored-only pass (a0-1101's 3 samples per anchor prompt at T = 0.7; REV4 §9.2)",
                "why": "no V2a script exists (brief §3; addendum §25 point 1): V2a stays on its fallback, FO-04's "
                       "figures as the stated limit, and its REV4 price ($5.6-7.1) is not in this need; building it "
                       "later needs a re-plan that the group's first funding record covers"},)
LN15E_IN_PLAN = {"job": "LN-15e: the report-only A1 re-score (REV4 §9.3 item 3, §14.2; addendum §17 Q19, §25 point 1)",
                 "units": "a0 retrains at 1102 and 1103 (retrain, J20: train only to e1, recipe S, dev split, engine X)",
                 "scorer": "A1's bi-anchored cosine: the engine's attributes step on each retrain's q and e1 states with "
                           "the sealed anchor bank and Gate B's 8 unit groups (a1_rescore, J21; Gate B's diagnostics "
                           "attributes step)",
                 "outputs": "each re-score's attributes unit, hashed into the block's seal; on the Mac (outside the "
                            "kit) top-600 Jaccard and Kendall tau against the sealed A1 set; never changes the arm",
                 "pods": "the LN-12 pod (the retrain and its re-score on one pod)",
                 "unmeasured": "the attributes step alone was never timed: measured upper 3.04 h (Gate B's whole "
                               "diagnostics job, FOCUS 16 Oct 13:21 UTC), upper 1.5 x 3.04 h"}


def canonical(doc) -> str:
    return json.dumps(doc, sort_keys=True, separators=(",", ":"))


def plan_code_now(plan: dict) -> str:
    """The plan code the block-A plan is built for: the re-derived plan-A/B record's, else plan A (the larger table)."""
    code = (plan_ab_checked(plan) or {}).get("code")
    return code if code in rules.PLAN_ARMS else "A"


def deal_pod_count(code: str) -> int:
    return len(rules.deal(rules.block_runs(code, "A")))


def default_ln12_pods() -> list[list[dict]]:
    """The default LN-12 launch (round 3b; LN12_LAYOUT): one pod, J2 + its J3 for a0 and R at 1101-1103 first (timed
    kinds), then LN-15e's two retrain + re-score pairs (each pair starts only with 0.15 h + 4.56 h + 30 min left),
    theta0's 500-bank pass and its Branch-128 LN-14 report, and c0 (J11, engine X, addendum §26)."""
    pods = []
    for layout in LN12_LAYOUT:
        pod = []
        for item in layout:
            if item == "rescore":
                for seed in rules.RESCORE_SEEDS:
                    pod.append({"kind": "retrain", "arm": "a0", "seed": seed})
                    pod.append({"kind": "a1_rescore", "arm": "a0", "seed": seed, "regen_source": len(pod) - 1})
            elif item == "theta0":
                pod += [{"kind": "o_only", "arm": "theta0"}, {"kind": "transfer_report", "arm": "theta0"}]
            elif item == "c0":
                pod.append(dict(C0_JOB))
            else:
                for arm, seed in LN12_UNITS:
                    if arm == item:
                        pod.append({"kind": "regenerate", "arm": arm, "seed": seed})
                        pod.append({"kind": "o_only", "arm": arm, "seed": seed, "regen_source": len(pod) - 1})
        pods.append(pod)
    return pods


# one pod: of every order of these five groups on one or two pods, one pod gives the smallest need (2+2+1, frozen:
# $130.59; the best two-pod split, c0 alone beside the rest, $132.16: one more 42 min overhead) and this order the
# smallest cap (13.5 h; rescore last 14.5 h) (round 3b, notes/b15r3b-build-evidence/layouts.out.txt)
LN12_LAYOUT = (("a0", "R", "rescore", "theta0", "c0"),)


def default_block_a_doc(code: str, with_c3: bool, split, utc: str, recorded_by: str) -> dict:
    """The kit's default block-A plan (pure; the inputs are recorded with it): S1-0 (W1-18 alone); the cert pod (C1,
    C2, C3 unless its fallback; round 3b: c0 moved to the LN-12 pod, addendum §26); the diagnostics pod (J6 before J5,
    J7, J8; J5's s3_orig pass runs after J6 on it); the LN-12 launch (default_ln12_pods: LN-15e's two retrain +
    re-score pairs, J2 + its J3 for a0 and R at 1101-1103, theta0's 500-bank pass and its Branch-128 LN-14 report, and
    c0); the deal's pods in launches of ``split``; HarmBench then Granite over block A's new units plus the 7
    re-judged units (the six reused a0/R units and theta0's; §25 point 2). not_in_plan records V2a's fallback."""
    split = [int(n) for n in split]
    ln12 = default_ln12_pods()
    cert = [dict(j) for j in CERT_FLOOR_POD if with_c3 or j["kind"] != "cert_c3"]
    arms, k = [], 0
    for n in split:
        arms.append({"role": "arms", "deal": list(range(k, k + n))})
        k += n
    units = len(rules.block_runs(code, "A")) + len(REJUDGED_UNITS)
    return {"kind": BLOCK_A_PLAN_KIND, "version": 1, "plan_code": code, "utc": utc, "recorded_by": recorded_by,
            "launches": [{"role": "s1_0", "hosts": [[{"kind": "w1_18"}]]}, {"role": "cert", "hosts": [cert]},
                         {"role": "diagnostics", "hosts": [[dict(j) for j in DEFAULT_DIAG_POD]]},
                         {"role": "ln12", "hosts": ln12}, *arms,
                         {"role": "judge", "judge": {"judge": "harmbench", "arms": units}},
                         {"role": "judge", "judge": {"judge": "granite", "arms": units}}],
            "not_in_plan": [dict(x) for x in NOT_IN_PLAN]}


def default_block_a_plan(plan: dict, split=None, utc: str | None = None,
                         recorded_by: str = "kit default (no lead record)") -> tuple[dict, dict]:
    code = plan_code_now(plan)
    split = DEFAULT_SPLIT[code] if split is None else split
    with_c3 = not records(plan).get("c3_fallback")
    args = {"plan_code": code, "c3": with_c3, "split": [int(n) for n in split]}
    return default_block_a_doc(code, with_c3, split, utc or mac.utc(), recorded_by), args


def _plan_job_key(job: dict) -> tuple:
    points = job.get("points")
    return (job["kind"], job.get("arm"), job.get("seed"), job.get("engine") or default_engine(job),
            tuple(points) if points else None, job.get("role"))


def validate_block_a_plan(plan: dict, doc: dict, check_code: bool = True) -> None:
    """The plan's own rules (every refusal names the rule, never a value)."""
    if not isinstance(doc, dict) or set(doc) != BLOCK_A_PLAN_KEYS:
        fail(f"a block-A plan holds exactly {sorted(BLOCK_A_PLAN_KEYS)}")
    if doc["kind"] != BLOCK_A_PLAN_KIND or type(doc["version"]) is not int or doc["version"] != 1:
        fail(f"not a {BLOCK_A_PLAN_KIND!r} version 1")
    code = doc["plan_code"]
    if code not in rules.PLAN_ARMS:
        fail(f"the block-A plan's plan_code must be one of {sorted(rules.PLAN_ARMS)}")
    if check_code and records(plan).get("plan_ab") is not None and plan_code_now(plan) != code:
        fail("the block-A plan's plan_code is not the re-derived plan-A/B record's code")
    if not (isinstance(doc["utc"], str) and doc["utc"].strip()) or \
            not (isinstance(doc["recorded_by"], str) and doc["recorded_by"].strip()):
        fail("the block-A plan needs utc and recorded_by")
    if canonical(doc["not_in_plan"]) != canonical([dict(x) for x in NOT_IN_PLAN]):
        fail("the block-A plan's not_in_plan must record the kit's NOT_IN_PLAN exactly (V2a on its fallback, FO-04's "
             "figures as the stated limit; addendum §25 point 1)")
    launches = doc["launches"]
    if not isinstance(launches, list) or not all(isinstance(x, dict) and x.get("role") in PLAN_ROLE_PART
                                                 for x in launches):
        fail(f"every block-A plan launch has a role among {sorted(PLAN_ROLE_PART)}")
    roles = [x["role"] for x in launches]
    a_roles = [r for r in roles if r not in ("s1_0", "cert")]
    n_arms, n_judge = a_roles.count("arms"), a_roles.count("judge")
    if roles[:1] != ["s1_0"] or roles.count("s1_0") != 1 or roles.count("cert") != 1 or \
            roles.index("cert") not in (1, len(roles) - 1) or n_arms < 1 or n_judge < 1 or \
            a_roles != ["diagnostics", "ln12"] + ["arms"] * n_arms + ["judge"] * n_judge:
        fail("the block-A plan's launch order is S1-0 -> the cert pod -> the diagnostics pod -> the LN-12 pod(s) -> "
             "the arm launches -> the judge launches (the cert pod may instead come last)")
    seen, deal_idx, judges = set(), [], []
    runs = rules.block_runs(code, "A")
    view = {"records": {}}                       # the job rules alone (records are checked when the job is planned)
    for k, x in enumerate(launches):
        role = x["role"]
        if role == "arms":
            if set(x) != {"role", "deal"} or not isinstance(x["deal"], list) or not x["deal"] or \
                    not all(type(i) is int for i in x["deal"]):
                fail(f"plan launch {k}: an arm launch is {{role, deal: [i, ...]}}")
            deal_idx += x["deal"]
            continue
        if role == "judge":
            j = x.get("judge")
            if set(x) != {"role", "judge"} or not isinstance(j, dict) or set(j) != {"judge", "arms"} or \
                    j["judge"] not in rules.JUDGES or type(j["arms"]) is not int or j["arms"] < len(runs):
                fail(f"plan launch {k}: a judge launch is {{judge: harmbench|granite, arms: n}} with n at least "
                     f"block A's {len(runs)} new units")
            try:
                rules.judge_pod(j["judge"], j["arms"])
            except ValueError as exc:
                fail(f"plan launch {k}: {exc}")
            judges.append(j["judge"])
            continue
        hosts = x.get("hosts")
        if set(x) != {"role", "hosts"} or not isinstance(hosts, list) or not hosts or \
                any(not isinstance(h, list) or not h for h in hosts):
            fail(f"plan launch {k}: a {role} launch is {{role, hosts: [[job, ...], ...]}}")
        if role != "ln12" and len(hosts) != 1:
            fail(f"plan launch {k}: the {role} launch is one pod")
        part = PLAN_ROLE_PART[role]
        for h in hosts:
            if not all(isinstance(j, dict) and j.get("kind") in PLAN_ROLE_KINDS[role] for j in h):
                fail(f"plan launch {k}: a {role} pod holds only {list(PLAN_ROLE_KINDS[role])}")
            for i, job in enumerate(h):
                if job["kind"] == "cert_c3":
                    if set(job) - {"kind", "engine"} or job.get("engine") not in (None, "Y"):
                        fail(f"plan launch {k}: C3 has no arm or seed and runs on engine Y")
                else:
                    check_job(dict(job), i, h, part, view, set())
            check_host(h)
            if len({j.get("engine") or default_engine(j) for j in h}) != 1:
                fail(f"plan launch {k}: one engine per pod (G4)")
            if sum(rules.counted(j["kind"], len(j.get("points") or []) or 1) for j in h) > rules.MAX_ARMS_PER_POD:
                fail(f"plan launch {k}: a pod holds more than {rules.MAX_ARMS_PER_POD} counted jobs")
            for job in h:
                key = _plan_job_key(job)
                if key in seen:
                    fail(f"plan launch {k}: {job['kind']} {job.get('arm')} at {job.get('seed')} is planned twice")
                seen.add(key)
        kinds = [j["kind"] for h in hosts for j in h]
        if role == "cert" and (kinds.count("cert_c1") != 1 or kinds.count("cert_c2") != 1):
            fail("the block-A plan's cert pod runs C1 and C2 once each (G4)")
    if deal_idx != list(range(deal_pod_count(code))):
        fail(f"the block-A plan's arm launches split the deal's {deal_pod_count(code)} pods in order, each once")
    if sorted(judges) != sorted(rules.JUDGES):
        fail("the block-A plan holds one HarmBench and one Granite judge launch")
    check_block_a_content(plan, doc)


def check_block_a_content(plan: dict, doc: dict) -> None:
    """Round 3a fix (VG3-1): the plan holds all of block A's G5 content (brief §4 G5; §3 J2-J14, J19), so a plan that
    leaves a required job out can never lower S1-0's floor: the cert pod's C3 (unless its §22 point 2 fallback is
    recorded); the diagnostics pod's J5-J8; on the LN-12 pod(s) c0 (J11; round 3b, addendum §26), LN-15e's retrain and
    re-score for a0 at 1102 and 1103 (round 3b, §25 point 1), a J2 regeneration for each of a0 and R at 1101-1103,
    and (unless the O-ext fallback (c) is recorded, under which neither runs) each one's linked J3, theta0's J3 and
    theta0's LN-14 report (counted only under Branch 128); each judge launch over block A's new units plus the 7
    re-judged units (§17 Q14, §25 point 2). Leaving a job out of a LAUNCH stays allowed (it never raises a term)."""
    rec = records(plan)
    kinds = {role: [(j["kind"], j.get("arm"), j.get("seed")) for x in doc["launches"] if x["role"] == role
                    for h in x.get("hosts") or [] for j in h] for role in ("cert", "diagnostics", "ln12")}
    missing = []
    cert = {k for k, _, _ in kinds["cert"]}
    missing += [k for k in (() if rec.get("c3_fallback") else ("cert_c3",)) if k not in cert]
    diag = {k for k, _, _ in kinds["diagnostics"]}
    missing += [k for k in rules.DIAG_KINDS if k not in diag]
    ln12 = set(kinds["ln12"])
    missing += [k for k in ("c0",) if (k, "R", 1101) not in ln12]
    missing += [f"{k} a0 {seed}" for seed in rules.RESCORE_SEEDS for k in ("retrain", "a1_rescore")
                if (k, "a0", seed) not in ln12]
    oext = not rec.get("oext_fallback")
    for arm, seed in LN12_UNITS:
        missing += [f"{k} {arm} {seed}" for k in ("regenerate",) + (("o_only",) if oext else ())
                    if (k, arm, seed) not in ln12]
    if oext:
        missing += [f"{k} theta0" for k in ("o_only", "transfer_report") if (k, "theta0", None) not in ln12]
    if missing:
        fail(f"the block-A plan leaves out block A's required jobs (G5): {', '.join(missing)}")
    units = len(rules.block_runs(doc["plan_code"], "A")) + len(REJUDGED_UNITS)
    if any(x["judge"]["arms"] < units for x in doc["launches"] if x["role"] == "judge"):
        fail(f"the block-A plan's judge launches are each over at least {units} units: block A's new units and the "
             f"{len(REJUDGED_UNITS)} re-judged units (the reused a0/R units and theta0's; §17 Q14, §25 point 2)")


def _plan_pod(jobs_raw: list[dict], fx: dict, branch: str) -> dict | None:
    """One planned hosts pod under ``branch`` (an LN-14 transfer report exists only under Branch 128)."""
    keep, remap = [], {}
    for i, j in enumerate(jobs_raw):
        if j["kind"] == "transfer_report" and branch != "128":
            continue
        remap[i] = len(keep)
        keep.append(j)
    if not keep:
        return None
    recs = []
    for j in keep:
        src = j.get("regen_source")
        recs.append(rules.job_record(j["kind"], j.get("arm"), j.get("seed"), None, steps_of(j), fx, branch=branch,
                                     engine=j.get("engine") or default_engine(j), points=j.get("points"),
                                     recipe=j.get("recipe") or default_recipe(j),
                                     regen_source=remap.get(src) if src is not None else None))
    return {"cap_hours": rules.cap_hours(recs), "spend_usd": rules.pod_spend_usd(recs),
            "unmeasured": sorted({r["kind"] for r in recs if r["unmeasured"]})}


def plan_launches(plan: dict, doc: dict, branch: str | None = None) -> list[dict]:
    """The plan's launches with each pod's cap and upper spend: under ``branch``, or (None) the larger of Branch full
    and Branch 128 for each pod (the frozen numbers every check uses; Branch full is the larger for every pod of the
    default plan)."""
    fx, code = plan["fixture"], doc["plan_code"]
    deal_pods = rules.deal(rules.block_runs(code, "A"))
    out = []
    for x in doc["launches"]:
        role = x["role"]
        entry = {"role": role, "part": PLAN_ROLE_PART[role], "type": "hosts", "pods": []}
        if role == "judge":
            j = rules.judge_pod(x["judge"]["judge"], x["judge"]["arms"])
            entry.update(type="judge", jobs={})
            entry["pods"].append({"judge": j["judge"], "arms": j["arms"], "answers": j["answers"],
                                  "cap_hours": j["cap_hours"], "spend_usd": j["cap_hours"] * rules.RATE_USD,
                                  "unmeasured": ["judge (the launcher's per-answer planning upper)"]})
        elif role == "arms":
            entry["type"] = "deal"
            for i in x["deal"]:
                runs = [("a0_arm" if a == "a0" else "arm", a, s) for a, s in deal_pods[i]]
                per = []
                for br in ((branch,) if branch else rules.BRANCHES):
                    recs = [rules.job_record(kd, a, s, None, stream_steps(a), fx, branch=br, recipe="S")
                            for kd, a, s in runs]
                    per.append((rules.cap_hours(recs), rules.pod_spend_usd(recs)))
                entry["pods"].append({"deal": i, "cap_hours": max(c for c, _ in per),
                                      "spend_usd": max(s for _, s in per), "unmeasured": ["a0_arm", "arm"]})
        else:
            for h in x["hosts"]:
                per = [p for p in (_plan_pod(h, fx, br) for br in ((branch,) if branch else rules.BRANCHES)) if p]
                if not per:
                    continue
                entry["pods"].append({"cap_hours": max(p["cap_hours"] for p in per),
                                      "spend_usd": max(p["spend_usd"] for p in per),
                                      "unmeasured": sorted({k for p in per for k in p["unmeasured"]})})
        if entry["type"] == "hosts":
            entry["jobs"] = {}
            for h in x["hosts"]:
                for j in h:
                    if branch != "full" or j["kind"] != "transfer_report":
                        key = _plan_job_key(j)
                        entry["jobs"][key] = entry["jobs"].get(key, 0) + 1
        out.append(entry)
    return out


def need_of(launches: list[dict]) -> dict:
    """The [D20] need of plan launches (rules.funding_need_usd, CONTINGENCY x the largest term)."""
    return rules.funding_need_usd([[{"cap_hours": p["cap_hours"], "spend_usd": p["spend_usd"]} for p in x["pods"]]
                                   for x in launches if x["pods"]], rules.CONTINGENCY_FACTOR)


def block_a_plan_checked(plan: dict) -> dict | None:
    """The recorded block-A plan, re-derived at every use: a lead file must still hash to its recorded SHA-256 and
    hold the recorded plan; the kit default must equal the default rebuilt from its recorded inputs, and those inputs
    must be ones the kit records (split = DEFAULT_SPLIT of its plan code; plan A, or the re-derived plan-A/B code;
    C3 dropped only under a recorded C3 fallback). An edit of one part of the record refuses. LIMIT (VG3-4): a
    coherent edit of the whole record (a lead file re-pointed with its path, SHA-256 and copy) passes this check; the
    money is then held by the group's first funding record, re-hashed and checked at every init and re-plan
    (group_anchor). None while no plan is recorded."""
    rec = records(plan).get("block_a_plan")
    if rec is None:
        return None
    doc = rec.get("doc")
    if rec.get("source") == "kit default":
        args = rec.get("default") or {}
        try:
            rebuilt = default_block_a_doc(args["plan_code"], args["c3"], args["split"], doc["utc"], doc["recorded_by"])
            kit_inputs = list(args["split"]) == list(DEFAULT_SPLIT[args["plan_code"]]) and \
                args["plan_code"] in ("A", plan_code_now(plan)) and \
                (args["c3"] is True or (args["c3"] is False and bool(records(plan).get("c3_fallback"))))
        except (KeyError, TypeError, ValueError):
            fail("the recorded block-A plan (kit default) cannot be rebuilt from its recorded inputs")
        if not kit_inputs or canonical(rebuilt) != canonical(doc) or hashlib_sha(canonical(doc)) != rec.get("sha256"):
            fail("the recorded block-A plan (kit default) is not the default rebuilt from its recorded inputs")
    else:
        p = pathlib.Path(str(rec.get("path")))
        if not p.is_file() or mac.sha(p) != rec.get("sha256"):
            fail("the block-A plan file is missing or differs from its recorded SHA-256")
        try:
            on_disk = json.loads(p.read_text())
        except ValueError:
            fail("the block-A plan file is not JSON")
        if canonical(on_disk) != canonical(doc):
            fail("plan.json's block-A plan is not the recorded file's")
    validate_block_a_plan(plan, doc, check_code=False)
    return doc


def hashlib_sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def part_order(doc: dict) -> list[str]:
    out = []
    for x in doc["launches"]:
        part = PLAN_ROLE_PART[x["role"]]
        if part not in out:
            out.append(part)
    return out


def rest_launches(plan: dict, frozen: list[dict], doc: dict, pivot: str) -> list[dict]:
    """The plan's launches of the group's parts after ``pivot`` (in the plan's order) that are not planned yet."""
    order = part_order(doc)
    later = order[order.index(pivot) + 1:]
    return [x for x in frozen if x["part"] in later and x["part"] not in plan["blocks"]]


def _match(actual: list[dict], offered: list[dict], ok) -> dict | None:
    """An injective assignment of the actual pods to offered pods with ok(a, p) (augmenting paths); None if none."""
    owner: dict = {}

    def place(i: int, seen: set) -> bool:
        for j, p in enumerate(offered):
            if j in seen or not ok(actual[i], p):
                continue
            seen.add(j)
            if j not in owner or place(owner[j], seen):
                owner[j] = i
                return True
        return False

    for i in range(len(actual)):
        if not place(i, set()):
            return None
    return {i: j for j, i in owner.items()}


def _pod_ok(a: dict, p: dict) -> bool:
    if a["cap_hours"] > p["cap_hours"] + PLAN_TOL or a["spend_usd"] > p["spend_usd"] + PLAN_TOL:
        return False
    if a.get("deal") is not None or p.get("deal") is not None:
        return a.get("deal") == p.get("deal")
    if a.get("judge") is not None or p.get("judge") is not None:
        return a.get("judge") == p.get("judge") and a["arms"] <= p["arms"]
    return True


def conform_part(actual: list[dict], frozen: list[dict], part: str) -> list[int]:
    """Map a planned part's launches, in order, onto the plan's launches of that part: each actual launch goes to the
    first plan launch at or after the previous one where it fits (same type; its jobs, with those of the earlier
    actual launches mapped there, among the plan launch's; its pods matched one to one to unused plan pods with no
    larger cap or spend, a dealt pod to the same deal pod, a judge to the same judge with no more units). A plan
    launch may be left out, or its pods spread over consecutive launches (neither raises a term of the need); a
    merged launch, another order, more pods, a larger cap or another job refuses. Returns the plan launch index of
    each actual launch (indices into the part's plan launches)."""
    plan_part = [x for x in frozen if x["part"] == part]
    used = [{"pods": set(), "jobs": {}} for _ in plan_part]
    out, start = [], 0
    for k, a in enumerate(actual):
        placed = None
        for jj in range(start, len(plan_part)):
            p = plan_part[jj]
            if a["type"] != p["type"]:
                continue
            jobs = dict(used[jj]["jobs"])
            if a["type"] == "hosts":
                over = False
                for pod in a["pods"]:
                    for key in pod["jobs"]:
                        jobs[key] = jobs.get(key, 0) + 1
                        over = over or jobs[key] > p["jobs"].get(key, 0)
                if over:
                    continue
            free = [i for i in range(len(p["pods"])) if i not in used[jj]["pods"]]
            got = _match(a["pods"], [p["pods"][i] for i in free], _pod_ok)
            if got is None:
                continue
            used[jj]["pods"] |= {free[j] for j in got.values()}
            used[jj]["jobs"] = jobs
            placed = jj
            break
        if placed is None:
            fail(f"block {part}: launch {k} departs from the recorded block-A plan (another order, more pods, a "
                 "larger cap or spend, or a job the plan does not hold); record a re-plan first "
                 "(record-block-a-replan), which the same funding record must cover")
        out.append(placed)
        start = placed
    return out


def _actual_key(job: dict) -> tuple:
    points = job.get("points")
    return (job["kind"], job.get("arm"), job.get("seed"), job["engine"], tuple(points) if points else None,
            job.get("role"))


def launch_shapes(launches: list, deal: list | None) -> list[dict]:
    """The planned (or built) launches of one part as conform_part reads them. ``launches`` items are {"judge":
    pod} or {"hosts": [host record, ...]}."""
    deal_sets = [sorted(tuple(r) for r in pod) for pod in (deal or [])]
    out = []
    for launch in launches:
        if "judge" in launch:
            j = launch["judge"]
            out.append({"type": "judge", "pods": [{"judge": j["judge"], "arms": j["arms"], "cap_hours": j["cap_hours"],
                                                   "spend_usd": j["cap_hours"] * rules.RATE_USD}]})
            continue
        pods, dealt = [], []
        for h in launch["hosts"]:
            runs = sorted((j.get("arm"), j.get("seed")) for j in h["jobs"]) if h.get("role") == "arms" else None
            idx = deal_sets.index(runs) if runs is not None and runs in deal_sets else None
            dealt.append(idx is not None)
            pods.append({"cap_hours": h["cap_hours"], "spend_usd": h["spend_upper_usd"], "deal": idx,
                         "jobs": [_actual_key(j) for j in h["jobs"]]})
        out.append({"type": "deal" if pods and all(dealt) else "hosts", "pods": pods})
    return out


def planned_shapes(plan: dict, block: str) -> list[dict]:
    """The block's planned launches as conform_part reads them. A host that received deferred or re-queued jobs
    (place) is read as it was planned, from its ``plan_shape`` (VG3-2): those moves stay outside the block-A plan and
    are paid from the contingency, as in rounds 1 and 2."""
    b = plan["blocks"][block]
    hosts = {n: ({**h, **h["plan_shape"]} if h.get("plan_shape") else h)
             for n, h in {**plan["hosts"], **(b.get("pending") or {})}.items()}
    launches = [launch if "judge" in launch else {"hosts": [hosts[n] for n in launch["hosts"]]}
                for launch in b["launches"]]
    return launch_shapes(launches, b.get("deal"))


def block_a_plan_for(plan: dict) -> tuple[dict, dict | None]:
    """The plan in force: the recorded one (re-derived), else the kit's default (split 2+2+1) and its inputs."""
    doc = block_a_plan_checked(plan)
    if doc is not None:
        return doc, None
    if planned_parts(plan, "A"):                      # VG3-4: never a silent new default after the group launched
        fail("block A's funding group has a planned part but no block-A plan is recorded; record a re-plan first "
             "(record-block-a-replan)")
    doc, args = default_block_a_plan(plan)
    validate_block_a_plan(plan, doc)
    return doc, args


def check_group_a(plan: dict, block: str, shapes: list[dict]) -> dict:
    """At init-block of S1-0, cert or A: the part's launches against the plan in force; returns the plan, its frozen
    launches, the rest of the plan after this part and the launch map."""
    doc, default_args = block_a_plan_for(plan)
    order = part_order(doc)
    if any(p in plan["blocks"] for p in order[order.index(block) + 1:]):
        fail(f"block {block}: the recorded block-A plan orders it before a part that is already planned (another "
             "order); record a re-plan first")
    if block == "A" and plan_code_now(plan) != doc["plan_code"]:
        fail(f"block A: the block-A plan is for plan {doc['plan_code']}, the plan-A/B record says "
             f"{plan_code_now(plan)}; record a re-plan first (record-block-a-replan)")
    frozen = plan_launches(plan, doc)
    mapping = conform_part(shapes, frozen, block)
    return {"doc": doc, "default": default_args, "frozen": frozen, "map": mapping,
            "rest": rest_launches(plan, frozen, doc, block)}


def check_planned_group_a(plan: dict, block: str) -> None:
    """At release: the block's planned launches against the recorded plan (re-derived)."""
    doc = block_a_plan_checked(plan)
    if doc is None:
        fail(f"block {block}: no block-A plan is recorded (record-block-a-replan)")
    conform_part(planned_shapes(plan, block), plan_launches(plan, doc), block)


def record_block_a_plan(path: str, sha256: str, replan: bool = False) -> dict:
    """record-block-a-plan (before the group's first launch) and record-block-a-replan (after it: every planned part
    must fit the new plan, and the group's first funding record must cover the new plan's need)."""
    plan = load()
    doc, ref = file_record(path, sha256)
    ref["path"] = str(pathlib.Path(path).resolve())   # VG3-7: re-hashed at every use from any working directory
    validate_block_a_plan(plan, doc)
    parts = planned_parts(plan, "A")                  # in planning order (VG3-3)
    rec = records(plan)
    old = rec.get("block_a_plan")
    frozen = plan_launches(plan, doc)
    if not replan:
        if parts:
            fail("record-block-a-plan is refused once block A's funding group has a planned launch (S1-0 or the "
                 "cert pod); a changed plan is a re-plan (record-block-a-replan)")
        need = need_of(frozen)
    else:
        if not parts:
            fail("record-block-a-replan follows the group's first launch; before it, use record-block-a-plan")
        order = part_order(doc)
        if [order.index(b) for b in parts] != sorted(order.index(b) for b in parts):
            fail("the re-plan orders the planned parts otherwise than they were planned")
        for b in parts:
            conform_part(planned_shapes(plan, b), frozen, b)
        last = max(parts, key=order.index)
        need = rules.funding_need_usd(group_launches(plan, "A") + [
            [{"cap_hours": p["cap_hours"], "spend_usd": p["spend_usd"]} for p in x["pods"]]
            for x in rest_launches(plan, frozen, doc, last) if x["pods"]], rules.CONTINGENCY_FACTOR)
        anchor = group_anchor(plan, "A")                  # the group's first funding record (S1-0's), re-hashed
        if not anchor["amount_usd"] >= need["need_usd"]:
            fail(f"the re-plan needs ${need['need_usd']:.2f}; the group's funding record "
                 f"({anchor['sha256'][:8]}...) is ${anchor['amount_usd']:.2f}")
    entry = {**ref, "source": "lead file", "doc": doc, "plan_code": doc["plan_code"], "need_usd": need["need_usd"],
             "utc": mac.utc(), "replan": replan}
    if old is not None:
        rec.setdefault("block_a_plan_history", []).append(old)
    rec["block_a_plan"] = entry
    mac.save_plan(plan)
    mac.operator_action({"action": "record-block-a-replan" if replan else "record-block-a-plan",
                         "sha256": ref["sha256"], "need_usd": need["need_usd"]})
    return {"recorded": "block_a_plan", "sha256": ref["sha256"], "replan": replan, "need_usd": need["need_usd"],
            "launches": [x["role"] for x in doc["launches"]]}


def write_block_a_plan(out: str, recorded_by: str, split: str | None) -> dict:
    """Write the kit's default block-A plan (with the lead's split of the deal) to a new file; never over a file."""
    p = pathlib.Path(out)
    if p.exists() or p.is_symlink():
        fail(f"{p.name} exists: a record is never overwritten")
    if not recorded_by.strip():
        fail("--recorded-by is needed")
    plan = load()
    try:
        parts = [int(n) for n in split.split(",")] if split else None
    except ValueError:
        fail("--split is a comma-separated list of pod counts, e.g. 2,2,1")
    doc, _ = default_block_a_plan(plan, parts, recorded_by=recorded_by)
    validate_block_a_plan(plan, doc)
    with p.open("x") as handle:
        handle.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return {"path": str(p), "sha256": mac.sha(p), "need_usd": need_of(plan_launches(plan, doc))["need_usd"]}


def plan_report(plan: dict, doc: dict) -> dict:
    """Every launch of a block-A plan with each pod's cap, upper spend and unmeasured terms, the terms in cents and
    the need, for Branch full, Branch 128 and the frozen numbers (each pod's larger) that S1-0's init uses."""
    out = {"plan_code": doc["plan_code"], "roles": [x["role"] for x in doc["launches"]],
           "not_in_plan": [dict(x) for x in doc["not_in_plan"]], "ln15e": dict(LN15E_IN_PLAN),
           "judge_units": {x["judge"]["judge"]: x["judge"]["arms"] for x in doc["launches"] if x["role"] == "judge"}}
    for name, branch in (("full", "full"), ("128", "128"), ("frozen", None)):
        launches = plan_launches(plan, doc, branch)
        need = need_of(launches)
        out[name] = {"launches": [{"role": x["role"], "pods": [
            {k: (round(v, 6) if isinstance(v, float) else v) for k, v in p.items()} for p in x["pods"]]}
            for x in launches if x["pods"]],
            "terms_cents": [round(t * 100, 4) for t in need["terms_usd"]],
            "base_need_usd": need["base_need_usd"], "need_usd": need["need_usd"]}
    return out


def block_a_need(path: str | None, sha256: str | None) -> dict:
    """block-a-need [FILE --sha256 H]: the report for a plan file, else the recorded plan, else the kit default."""
    plan = load()
    if path:
        doc, _ = file_record(path, sha256)
        validate_block_a_plan(plan, doc)
        source = "file"
    else:
        doc = block_a_plan_checked(plan)
        source = "recorded"
        if doc is None:
            doc, _ = default_block_a_plan(plan)
            source = "kit default (split 2+2+1 under plan A, 2+2 under plan B)"
    return {"source": source, **plan_report(plan, doc)}


# ----- block A's completion against the recorded block-A plan (round 3c; round 3b's VP3b-3) ----------------------
# A launch may leave a planned job out (it never raises a term), so block A could complete without, say, LN-15e's
# re-score or c0. Block A completes only when every job the recorded block-A plan requires for block A has a
# completion record, or a recorded lead decision (record-block-a-not-run) names it as not run, with a reason.


def job_label(kind: str, arm=None, seed=None) -> str:
    """A job's name in block A's completion check and in a not-run decision: kind, arm and seed without the empty
    parts ('c0 R 1101', 'retrain a0 1103', 'o_only theta0', 'untuned_answers', 'arm A1 1102', 'judge harmbench')."""
    return " ".join(str(x) for x in (kind, arm, seed) if x is not None)


def block_a_required(plan: dict, doc: dict) -> dict:
    """Every job the recorded block-A plan ``doc`` requires for block A, in plan order: label -> the units a judge
    launch must cover (0 for a host job). Each job of the plan's diagnostics and LN-12 pods (theta0's LN-14 report
    only under Branch 128, block A's recorded branch; no O-only pass or transfer report under the O-ext fallback (c),
    under which neither runs), each run of the deal's pods that the plan's arm launches name, and each judge launch
    (over at least its planned units)."""
    rec = records(plan)
    branch = (plan["blocks"].get("A") or {}).get("branch") or branch_name(plan)
    oext = not rec.get("oext_fallback")
    deal_pods = rules.deal(rules.block_runs(doc["plan_code"], "A"))
    out = {}
    for x in doc["launches"]:
        if PLAN_ROLE_PART[x["role"]] != "A":
            continue
        if x["role"] == "judge":
            out[job_label("judge", x["judge"]["judge"])] = x["judge"]["arms"]
        elif x["role"] == "arms":
            for i in x["deal"]:
                for arm, seed in deal_pods[i]:
                    out[job_label("a0_arm" if arm == "a0" else "arm", arm, seed)] = 0
        else:
            for h in x["hosts"]:
                for j in h:
                    if (j["kind"] == "transfer_report" and branch != "128") or \
                            (j["kind"] in rules.OEXT_ONLY_KINDS and not oext):
                        continue
                    out[job_label(j["kind"], j.get("arm"), j.get("seed"))] = 0
    return out


def block_a_done(plan: dict, required: dict) -> set:
    """The labels with a completion record: a job recorded complete on a block-A host (record-done, from its pulled
    JOB-DONE.json; a moved host's complete jobs count), and a judge launch of block A that is released, covers at
    least the plan's units for that judge, and (round 30, R2) is named by block A's judge-completion record, valid at
    this use (judges_done: the record re-hashed, the index and the judge files checked). A job recorded complete (not
    pulled) is not counted here: it counts as decided by its unpulled outputs decision (block_a_unpulled), re-hashed
    at every use (§29 point 3)."""
    done = {job_label(j["kind"], j.get("arm"), j.get("seed")) for h in plan["hosts"].values() if h["block"] == "A"
            for j in h["jobs"] if j.get("status") == "complete" and j.get("pulled") is not False}
    b = plan["blocks"].get("A") or {}
    judged = judges_done(plan, "A") if any(x.get("judge") for x in b.get("launches") or []) else set()
    for k, launch in enumerate(b.get("launches") or []):
        j = launch.get("judge")
        if j and k < b.get("released", 0) and j["arms"] >= required.get(job_label("judge", j["judge"]), math.inf):
            if j["judge"] in judged:                  # round 30 (R2): released is not done; the valid record is
                done.add(job_label("judge", j["judge"]))
    return done


def block_a_planned(plan: dict, required: dict) -> dict:
    """label -> where block A still holds it: a host of block A that is not moved (released or pending), or a judge
    launch over at least the plan's units that is not released yet."""
    moved = {d["from"] for d in plan["deferrals"]} | {r["from"] for r in plan.get("requeues") or []}
    b = plan["blocks"]["A"]
    hosts = {**{n: h for n, h in plan["hosts"].items() if h["block"] == "A"}, **(b.get("pending") or {})}
    out = {}
    for name, h in sorted(hosts.items()):
        if name not in moved:
            for j in h["jobs"]:
                out.setdefault(job_label(j["kind"], j.get("arm"), j.get("seed")), f"host {name}")
    for k, launch in enumerate(b["launches"]):
        j = launch.get("judge")
        if j and k >= b["released"] and j["arms"] >= required.get(job_label("judge", j["judge"]), math.inf):
            out.setdefault(job_label("judge", j["judge"]), f"launch {k}, not released")
    return out


def block_a_not_run(plan: dict) -> dict:
    """label -> the SHA-256 of the recorded lead decision that names it as not run. Each decision file is re-hashed
    at every use: it must stay at its recorded path, unchanged, and hold the recorded jobs and reason."""
    out = {}
    for e in records(plan).get("block_a_not_run") or []:
        p = pathlib.Path(str(e.get("path")))
        try:
            on_disk = json.loads(p.read_text()) if p.is_file() else None
        except ValueError:
            on_disk = None
        if not isinstance(on_disk, dict) or mac.sha(p) != e.get("sha256") or on_disk.get("jobs") != e.get("jobs") or \
                on_disk.get("reason") != e.get("reason"):
            fail("a recorded not-run decision of block A is missing or differs from its recorded SHA-256; it must "
                 "stay at its recorded path, unchanged")
        for label in e["jobs"]:
            out[label] = e["sha256"]
    return out


def block_a_open(plan: dict) -> list[str]:
    """The jobs the recorded block-A plan requires for block A (block_a_required, in plan order) that have neither a
    completion record (block_a_done) nor a recorded not-run decision (block_a_not_run). Block A is complete only when
    this is empty (block_complete; seal.py block A, and certify's and B's init-block refuse otherwise)."""
    doc = block_a_plan_checked(plan)
    if doc is None:
        return ["(no block-A plan is recorded)"]
    required = block_a_required(plan, doc)
    done, decided, unpulled = block_a_done(plan, required), block_a_not_run(plan), block_a_unpulled(plan)
    return [label for label in required if label not in done and label not in decided and label not in unpulled]


def block_a_unpulled(plan: dict) -> dict:
    """label -> the SHA-256 of the unpulled outputs decision under which record-done recorded a block-A job complete
    (not pulled) (§29 point 3; the decisions re-hashed here, not_pulled_jobs)."""
    return {e["job"]: e["decision_sha256"] for e in not_pulled_jobs(plan, "A")}


def block_a_open_note(plan: dict) -> str:
    """The refusal's list of block A's open jobs ('' when none is open)."""
    left = block_a_open(plan) if "A" in plan["blocks"] else []
    if not left:
        return ""
    return (f"; {len(left)} job(s) the block-A plan requires have no completion record and no not-run decision: "
            f"{', '.join(left[:12])}{', ...' if len(left) > 12 else ''} (record-block-a-not-run names a job that "
            "will not run, with a reason)")


def record_block_a_not_run(path: str, sha256: str) -> dict:
    """record-block-a-not-run FILE --sha256 H (round 3c, VP3b-3): the lead's decision {kind: "stage1 block-a not-run
    decision", jobs: [label, ...], reason, utc, recorded_by} that jobs the recorded block-A plan requires for block A
    will not run. Each label (job_label: the names the refusal prints) must be a job the plan requires for block A,
    have no completion record, be held by no block-A host that is not moved and by no unreleased judge launch over
    its planned units (such a job runs, or its host is deferred or requeued first), and be named by no earlier
    decision. Refused before block A is planned and once it is sealed, except (round 30, R2) a decision naming only
    judge launches: a released judge launch with no judge-completion record may be named after the seal too (block A
    is sealed with the old seal.py before round 30 lands; a failed Granite is recorded so)."""
    plan = load()
    doc, ref = file_record(path, sha256)
    ref.update(path=str(pathlib.Path(path).resolve()))   # re-hashed at every completion check, from any directory
    jobs = doc.get("jobs")
    if doc.get("kind") != RECORD_KINDS["not_run"] or not isinstance(jobs, list) or not jobs or \
            not all(isinstance(j, str) and j.strip() for j in jobs) or len(set(jobs)) != len(jobs):
        fail("not a block-A not-run decision: {kind: 'stage1 block-a not-run decision', jobs: [distinct job names], "
             "reason, utc, recorded_by}")
    _need(doc, ("reason", "utc", "recorded_by"), "a block-A not-run decision")
    if not isinstance(doc["reason"], str) or not doc["reason"].strip():
        fail("a block-A not-run decision needs its reason")
    if "A" not in plan["blocks"]:
        fail("block A is not planned: a not-run decision names jobs of a planned block A (init-block A first)")
    if "A" in plan["seals"] and not set(jobs) <= {job_label("judge", k) for k in rules.JUDGES}:
        fail("block A is sealed: a not-run decision is recorded before its seal (after it, round 30: only for a "
             "released judge launch that has no judge-completion record)")
    plan_doc = block_a_plan_checked(plan)
    if plan_doc is None:
        fail("no block-A plan is recorded")
    required = block_a_required(plan, plan_doc)
    done, planned, decided = block_a_done(plan, required), block_a_planned(plan, required), block_a_not_run(plan)
    for label in jobs:
        if label not in required:
            fail(f"{label!r} is not a job the recorded block-A plan requires for block A")
        if label in done:
            fail(f"{label!r} has a completion record (it ran); a not-run decision cannot name it")
        if label in planned:
            fail(f"{label!r} is still planned in block A ({planned[label]}): it runs, or its host is deferred or "
                 "requeued first")
        if label in decided:
            fail(f"{label!r} is already named by a recorded not-run decision")
    entry = {**ref, "jobs": list(jobs), "reason": doc["reason"], "utc": mac.utc()}
    records(plan).setdefault("block_a_not_run", []).append(entry)
    mac.save_plan(plan)
    mac.operator_action({"action": "record-block-a-not-run", "sha256": ref["sha256"], "jobs": list(jobs)})
    return {"recorded": "block_a_not_run", "sha256": ref["sha256"], "jobs": list(jobs), "open": block_a_open(plan)}


# ----- the judge-completion record and the judge files (round 30; addendum §30 gaps 1, 2 and 5; the lead's R2, R3) ---
# Gap 1: a judge launch counted as done once released. Now a block's judge launch is done only while the block's
# judge-completion record (record-judges) names its judge and is valid at that use: the record file re-hashes to its
# recorded SHA-256 and holds the recorded entries; judges/BLOCK/judge-files-index.json hashes to its index_sha256;
# and judge_files_check passes for the record's judges (gap 2; seal.py runs the same check). The required units are
# plan.json's and the block's pins (gap 5). Nothing here parses a judge file or prints a count other than files and
# units: the judge files are hashed only.

JUDGE_FOLDER = HERE / "judges"                    # judges/BLOCK/: Gate B's write_files.py output (seal.py seals it)
JUDGE_POD_ROOT = ROOT / "tmp/judge-pod"           # the judge launcher's folders (judge_pod.JUDGE_POD_ROOT): read once,
#                                                   at record time, by key (never printed)
JUDGE_RESULT, JUDGE_RESULT_KIND, JUDGE_RUN_RECORD = "judge-pod-result.json", "judge-pod result", "out/run-record.json"
JUDGE_FILE_RE = re.compile(rules.JUDGE_FILE_PATTERN)
JUDGE_TAG_RE = re.compile(rules.JUDGE_TAG_PATTERN)
JUDGE_KEY_OF_NAME = {name: key for key, name in rules.JUDGE_NAMES.items()}


def judge_required_units(plan: dict, block: str) -> dict:
    """complete_sha256 -> a label: the units the block's judge files must cover (R3). The COMPLETE.json SHA-256 that
    plan.json records for each complete arm job of the block (rules.JUDGED_RUN_KINDS) and for each unit of each
    complete B10 job (rules.JUDGED_B10_KINDS; record-done keeps JOB-DONE.json's units list), plus the block's pinned
    re-judged units (rules.REJUDGED_PINS). A job recorded complete (not pulled) is left out (its unit is not here)."""
    out = {}
    for name, h in sorted(plan["hosts"].items()):
        if h["block"] != block:
            continue
        for i, j in enumerate(h["jobs"]):
            if j.get("status") != "complete" or j.get("pulled") is False:
                continue
            label = f"{name} job {i} ({job_label(j['kind'], j.get('arm'), j.get('seed'))})"
            if j["kind"] in rules.JUDGED_RUN_KINDS:
                digests = [j.get("complete_sha256")]
            elif j["kind"] in rules.JUDGED_B10_KINDS:
                units = j.get("units")
                if not isinstance(units, list) or not units:
                    fail(f"{label}: plan.json holds no list of its B10 units (record-done keeps JOB-DONE.json's)")
                digests = [u.get("complete_sha256") if isinstance(u, dict) else None for u in units]
            else:
                continue
            for digest in digests:
                if not (isinstance(digest, str) and SHA_RE.fullmatch(digest)):
                    fail(f"{label}: plan.json records no COMPLETE.json SHA-256 for its unit")
                out[digest] = label
    for pin in rules.REJUDGED_PINS.get(block, ()):
        out[pin["complete_sha256"]] = f"re-judged {pin['name']}"
    return out


def judge_files_check(plan: dict, block: str, judges) -> dict:
    """R3, the one check of a block's judge files (seal.py and every use of a judge-completion record): judges/BLOCK/
    judge-files-index.json is Gate B's index (its kind, version 2, exactly its entry keys); every listed file is a
    top-level judge-named file, named for its entry's judge and COMPLETE.json SHA-256, present with its indexed
    SHA-256 (no symbolic link); no other top-level judge-named file (subfolders such as pods/ are allowed); no (judge,
    unit) twice; and for each judge in ``judges`` exactly one file per required unit (judge_required_units), keyed by
    COMPLETE.json SHA-256. Files of other units or judges are allowed and counted. Returns hashes and counts only."""
    folder = JUDGE_FOLDER / block
    index = folder / rules.JUDGE_INDEX
    where = f"judges/{block}/{rules.JUDGE_INDEX}"
    if not index.is_file() or index.is_symlink():
        fail(f"block {block}: no {where} (Gate B's write_files.py writes it)")
    try:
        doc = json.loads(index.read_text())
    except ValueError:
        doc = None
    entries = doc.get("files") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or doc.get("kind") != rules.JUDGE_INDEX_KIND or \
            doc.get("version") != rules.JUDGE_INDEX_VERSION or not isinstance(entries, list):
        fail(f"{where} is not Gate B's judge files index (version {rules.JUDGE_INDEX_VERSION})")
    count, listed = {}, set()
    for e in entries:
        if not isinstance(e, dict) or set(e) != set(rules.JUDGE_INDEX_ENTRY_KEYS):
            fail(f"{where}: an entry does not hold exactly Gate B's index keys")
        name, key, unit = e["file"], JUDGE_KEY_OF_NAME.get(e["judge"]), e["complete_sha256"]
        if not (isinstance(name, str) and "/" not in name and JUDGE_FILE_RE.match(name) and key is not None
                and name.startswith(f"{key}--") and isinstance(unit, str) and SHA_RE.fullmatch(unit)
                and name.endswith(f"--{unit[:12]}.json")):
            fail(f"{where}: entry {str(name)[:60]!r} is not a judge file named for its judge and COMPLETE.json SHA-256")
        if name in listed:
            fail(f"{where} lists {name[:60]} twice")
        listed.add(name)
        p = folder / name
        if not p.is_file() or p.is_symlink() or mac.sha(p) != e["sha256"]:
            fail(f"judges/{block}/{name[:60]} is missing or differs from its indexed SHA-256")
        count[(key, unit)] = count.get((key, unit), 0) + 1
    unlisted = sorted(p.name for p in folder.iterdir() if p.is_file() and JUDGE_FILE_RE.match(p.name)
                      and p.name not in listed)
    if unlisted:
        fail(f"judges/{block}: {len(unlisted)} judge-named file(s) not in its index ({unlisted[0][:60]})")
    twice = sorted(k for k, n in count.items() if n > 1)
    if twice:
        fail(f"{where}: two {twice[0][0]} files for the unit with COMPLETE.json {twice[0][1][:16]}")
    required = judge_required_units(plan, block)
    for key in sorted(judges):
        missing = [label for unit, label in required.items() if (key, unit) not in count]
        if missing:
            fail(f"block {block}: {len(missing)} required unit(s) have no {key} judge file in {where} "
                 f"({missing[0]})")
    other = sum(1 for key, unit in count if key not in judges or unit not in required)
    return {"index_sha256": mac.sha(index), "files": len(entries), "units": len(required), "judges": sorted(judges),
            "other_files": other}


def judge_record_problem(doc, block: str) -> str | None:
    """Why ``doc`` is not block BLOCK's judge-completion record (rules.JUDGE_RECORD_KEYS exactly; per judge exactly
    rules.JUDGE_ENTRY_KEYS: a launch tag, the SHA-256 of its judge-pod-result.json, of its fetched run record and of
    its bundle, exit 0, the number of answers judged, complete true; Granite also its known-answer gate passed), or
    None. No value is an HB, Granite, yes, unparsed or harm count: any other key refuses."""
    if not isinstance(doc, dict) or set(doc) != set(rules.JUDGE_RECORD_KEYS):
        return f"it must hold exactly {list(rules.JUDGE_RECORD_KEYS)}"
    if doc["kind"] != rules.JUDGE_RECORD_KIND:
        return f"its kind is not {rules.JUDGE_RECORD_KIND!r}"
    if doc["block"] != block:
        return f"its block is not {block}"
    if not (isinstance(doc["index_sha256"], str) and SHA_RE.fullmatch(doc["index_sha256"])):
        return "index_sha256 is not a SHA-256"
    if not all(isinstance(doc[k], str) and doc[k].strip() for k in ("utc", "recorded_by")):
        return "utc and recorded_by must be non-empty texts"
    judges = doc["judges"]
    if not isinstance(judges, dict) or not judges or set(judges) - set(rules.JUDGE_ENTRY_KEYS):
        return f"judges must name one or both of {list(rules.JUDGE_ENTRY_KEYS)}"
    for key, e in sorted(judges.items()):
        want = rules.JUDGE_ENTRY_KEYS[key]
        if not isinstance(e, dict) or set(e) != set(want):
            return f"judges.{key} must hold exactly {list(want)}"
        if not (isinstance(e["tag"], str) and JUDGE_TAG_RE.match(e["tag"])):
            return f"judges.{key}.tag is not a judge launch tag"
        if not all(isinstance(e[k], str) and SHA_RE.fullmatch(e[k])
                   for k in ("result_sha256", "run_record_sha256", "bundle_sha256")):
            return f"judges.{key}: result_sha256, run_record_sha256 and bundle_sha256 must be SHA-256"
        if type(e["exit"]) is not int or e["exit"] != 0:
            return f"judges.{key}: a judge launch is recorded done with exit 0 only (a failed one: record-block-a-not-run)"
        if type(e["judged"]) is not int or e["judged"] < 1 or e["complete"] is not True:
            return f"judges.{key}: judged must be the number of answers judged and complete true"
        if key == "granite" and e["known_answer_passed"] is not True:
            return "judges.granite: its known-answer gate must have passed"
    if len({e["tag"] for e in judges.values()}) != len(judges):
        return "each judge has its own launch tag"
    return None


def judge_result_problem(key: str, e: dict, required: dict) -> str | None:
    """At record time only: the launch's own result (JUDGE_POD_ROOT/TAG/judge-pod-result.json, as judge_pod.py wrote
    it) hashes to result_sha256 and agrees with the entry (kind, tag, judge, bundle, exit, complete, judged, the
    fetched run record's SHA-256, a confirmed stop; Granite: the gate; round 33, GB5: verification.gpu is
    rules.JUDGE_GPU), its fetched run record hashes to run_record_sha256, and its verified units include every required
    unit. Read by key, never printed."""
    d = JUDGE_POD_ROOT / e["tag"]
    path = d / JUDGE_RESULT
    where = f"tmp/judge-pod/{e['tag']}/{JUDGE_RESULT}"
    if not path.is_file() or mac.sha(path) != e["result_sha256"]:
        return f"{where} is missing or its SHA-256 is not result_sha256"
    try:
        r = json.loads(path.read_text())
    except ValueError:
        return f"{where} is not JSON"
    r = r if isinstance(r, dict) else {}
    v = r.get("verification") if isinstance(r.get("verification"), dict) else {}
    stop = r.get("stop") if isinstance(r.get("stop"), dict) else {}
    fetched = r.get("fetched") if isinstance(r.get("fetched"), dict) else {}
    gate = v.get("known_answers") if isinstance(v.get("known_answers"), dict) else {}
    checks = [(r.get("kind") == JUDGE_RESULT_KIND, "kind"), (r.get("tag") == e["tag"], "tag"),
              ((r.get("judge") or "harmbench") == key, "judge"), (r.get("bundle_sha256") == e["bundle_sha256"], "bundle"),
              (r.get("exit") == e["exit"], "exit"), (v.get("complete") is e["complete"], "complete"),
              (type(v.get("judged")) is int and v.get("judged") == e["judged"], "judged"),
              (fetched.get(JUDGE_RUN_RECORD) == e["run_record_sha256"], "run record"),
              (stop.get("confirmed") is True, "stop confirmed"), (v.get("gpu") == rules.JUDGE_GPU, "gpu")]
    if key == "granite":
        checks.append((gate.get("passed") is e["known_answer_passed"], "known-answer gate"))
    bad = [what for ok, what in checks if not ok]
    if bad:
        return f"{where} differs from the record ({', '.join(bad)})"
    run_record = d / "fetched" / JUDGE_RUN_RECORD
    if not run_record.is_file() or mac.sha(run_record) != e["run_record_sha256"]:
        return f"tmp/judge-pod/{e['tag']}/fetched/{JUDGE_RUN_RECORD} is missing or not run_record_sha256"
    judged = {u.get("complete_sha256") for u in v.get("units") or [] if isinstance(u, dict)}
    missing = [label for unit, label in required.items() if unit not in judged]
    if missing:
        return f"the launch judged {len(missing)} required unit(s) less ({missing[0]})"
    return None


def judge_record_valid(plan: dict, block: str, entry: dict) -> dict:
    """R2 at record and at every later use: the record file at its recorded path re-hashes to its recorded SHA-256
    and holds the recorded block, judges and index_sha256; judges/BLOCK/judge-files-index.json hashes to
    index_sha256; a sealed block's seal (re-hashed) lists that index with that SHA-256; and judge_files_check passes
    for the record's judges. Refuses otherwise; returns the check's hashes and counts."""
    p = pathlib.Path(str(entry.get("path")))
    try:
        on_disk = json.loads(p.read_text()) if p.is_file() else None
    except ValueError:
        on_disk = None
    if not isinstance(on_disk, dict) or mac.sha(p) != entry.get("sha256") or on_disk.get("block") != block or \
            on_disk.get("judges") != entry.get("judges") or on_disk.get("index_sha256") != entry.get("index_sha256"):
        fail(f"block {block}'s judge-completion record is missing or differs from its recorded SHA-256; it must stay "
             "at its recorded path, unchanged")
    index = JUDGE_FOLDER / block / rules.JUDGE_INDEX
    if not index.is_file() or mac.sha(index) != entry["index_sha256"]:
        fail(f"judges/{block}/{rules.JUDGE_INDEX} is missing or not the judge-completion record's index_sha256")
    seal = (plan.get("seals") or {}).get(block)
    if seal:                                      # sealed (block A: by the old seal.py): its seal hashed this index
        sp = HERE / seal["path"]
        try:
            sdoc = json.loads(sp.read_text()) if sp.is_file() else None
        except ValueError:
            sdoc = None
        if not isinstance(sdoc, dict) or mac.sha(sp) != seal.get("sha256"):
            fail(f"block {block}'s seal is missing or differs from the SHA-256 plan.json records")
        hashed = {(f.get("host"), f.get("path")): f.get("sha256") for f in sdoc.get("files") or [] if isinstance(f, dict)}
        if hashed.get((f"judges/{block}", rules.JUDGE_INDEX)) != entry["index_sha256"]:
            fail(f"block {block}'s seal does not hold judges/{block}/{rules.JUDGE_INDEX} with the record's "
                 "index_sha256")
    return judge_files_check(plan, block, set(entry["judges"]))


def judge_record_checked(plan: dict, block: str) -> dict | None:
    """The block's judge-completion record, checked now (judge_record_valid), or None when none is recorded."""
    entry = ((plan.get("records") or {}).get("judges") or {}).get(block)
    if not entry:
        return None
    return {**judge_record_valid(plan, block, entry), "record_sha256": entry["sha256"]}


def judges_done(plan: dict, block: str) -> set:
    """The judges whose launch is done (R2): those the block's judge-completion record names, valid at this use."""
    checked = judge_record_checked(plan, block)
    return set() if checked is None else set(checked["judges"])


def judges_needed(plan: dict, block: str) -> list[str]:
    """The judges of the block's judge launches that a recorded not-run decision does not name (judges_decided: block
    A's record-block-a-not-run, round 31 (K1) every other block's record-judge-not-run): the judges whose files
    seal.py requires."""
    decided = judges_decided(plan, block)
    out = []
    for x in plan["blocks"][block]["launches"]:
        j = x.get("judge")
        if j and j["judge"] not in out and j["judge"] not in decided:
            out.append(j["judge"])
    return out


# ----- round 31 (K1; addendum §32 point 3): a not-run route for a released judge launch of any block ---------------
# Block A keeps its own route (record-block-a-not-run names "judge harmbench" or "judge granite"). Every other block's
# released judge launch that will not be recorded done (a failed Granite, a launch that cannot be paid again) is named
# by the lead's judge not-run decision; record-judges then needs only the other judges, and block completeness, the seal
# and seal.py status count and list the decision. Accepted after the block's seal too: it adds a record and changes no
# seal (the seal's own judge check ran when it was written).

def judge_not_run_problem(e: dict) -> str | None:
    """Why a recorded judge not-run decision no longer holds (its file at the recorded path re-hashed, and the recorded
    block, judges and reason equal to the file's), or None."""
    p = pathlib.Path(str(e.get("path")))
    try:
        on_disk = json.loads(p.read_text()) if p.is_file() else None
    except ValueError:
        on_disk = None
    if not isinstance(on_disk, dict) or mac.sha(p) != e.get("sha256") or on_disk.get("block") != e.get("block") or \
            on_disk.get("judges") != e.get("judges") or on_disk.get("reason") != e.get("reason"):
        return ("a recorded judge not-run decision is missing or differs from its recorded SHA-256; it must stay at "
                "its recorded path, unchanged")
    return None


def judge_not_run(plan: dict, block: str) -> dict:
    """K1: judge -> the SHA-256 of the recorded judge not-run decision that names block BLOCK's judge launch of that
    judge (record-judge-not-run; never block A). Each of the block's decisions is re-hashed at every use."""
    out = {}
    for e in (plan.get("records") or {}).get("judge_not_run") or []:
        if e.get("block") != block:
            continue
        problem = judge_not_run_problem(e)
        if problem:
            fail(f"block {block}: {problem}")
        for key in e["judges"]:
            out[key] = e["sha256"]
    return out


def judges_decided(plan: dict, block: str) -> dict:
    """judge -> the SHA-256 of the recorded decision naming the block's judge launch of that judge as not run: block
    A's record-block-a-not-run ("judge harmbench", "judge granite"), every other block's record-judge-not-run (K1)."""
    if block != "A":
        return judge_not_run(plan, block)
    decided = block_a_not_run(plan)
    return {k: decided[job_label("judge", k)] for k in rules.JUDGES if job_label("judge", k) in decided}


def record_judge_not_run(path: str, sha256: str) -> dict:
    """record-judge-not-run FILE --sha256 H (round 31, K1): the lead's decision {kind: "stage1 judge not-run decision",
    block, judges: [harmbench|granite, ...], reason, utc, recorded_by} that the block's released judge launch of each
    named judge will not be recorded done. Each judge must have a released judge launch in the block, no judge-
    completion record naming it, and no earlier decision naming it. Block A refuses (its route is
    record-block-a-not-run). Accepted after the block's seal: it adds a record and changes no seal. The file is
    re-hashed at every use (judge_not_run)."""
    plan = load()
    doc, ref = file_record(path, sha256)
    ref.update(path=str(pathlib.Path(path).resolve()))   # re-hashed at every use, from any directory
    judges = doc.get("judges")
    if set(doc) != set(JUDGE_NOT_RUN_KEYS) or doc.get("kind") != RECORD_KINDS["judge_not_run"] or \
            not isinstance(judges, list) or not judges or len(set(map(str, judges))) != len(judges) or \
            not all(isinstance(j, str) and j in rules.JUDGES for j in judges):
        fail("not a judge not-run decision: exactly {kind: 'stage1 judge not-run decision', block, judges: [distinct "
             f"judges among {list(rules.JUDGES)}], reason, utc, recorded_by}}")
    if not all(isinstance(doc[k], str) and doc[k].strip() for k in ("block", "reason", "utc", "recorded_by")):
        fail("a judge not-run decision needs its block, reason, utc and recorded_by")
    _utc_past(doc["utc"], "the judge not-run decision")
    block = doc["block"]
    if block == "A":
        fail("block A's judge launches are named by record-block-a-not-run ('judge harmbench', 'judge granite')")
    if block not in plan["blocks"]:
        fail(f"block {block} is not planned")
    b = plan["blocks"][block]
    planned = {x["judge"]["judge"] for x in b["launches"] if x.get("judge")}
    released = {x["judge"]["judge"] for k, x in enumerate(b["launches"]) if x.get("judge") and k < b["released"]}
    recorded = set((((records(plan).get("judges") or {}).get(block) or {}).get("judges") or {}))
    decided = judge_not_run(plan, block)
    for key in judges:
        if key not in planned:
            fail(f"block {block} has no {key} judge launch")
        if key not in released:
            fail(f"block {block}'s {key} judge launch is not released: a not-run decision names a released judge "
                 "launch only")
        if key in recorded:
            fail(f"'judge {key}' has a judge-completion record (it ran); a not-run decision cannot name it")
        if key in decided:
            fail(f"'judge {key}' is already named by a recorded judge not-run decision")
    entry = {**ref, "block": block, "judges": list(judges), "reason": doc["reason"], "utc": mac.utc()}
    records(plan).setdefault("judge_not_run", []).append(entry)
    mac.save_plan(plan)
    mac.operator_action({"action": "record-judge-not-run", "block": block, "sha256": ref["sha256"],
                         "judges": list(judges)})
    return {"recorded": "judge_not_run", "block": block, "sha256": ref["sha256"], "judges": list(judges),
            "needed": judges_needed(plan, block), "complete": block_complete(plan, block),
            "sealed": block in (plan.get("seals") or {})}


def record_judges(block: str, path: str, sha256: str) -> dict:
    """record-judges BLOCK FILE --sha256 H (round 30, R2): the lead's judge-completion record {kind: "stage1 judge
    completion record", block, judges: {harmbench: {tag, result_sha256, run_record_sha256, bundle_sha256, exit,
    judged, complete}, granite: {the same, known_answer_passed}}, index_sha256, utc, recorded_by} (one or both
    judges; judge_record_problem). Each judge must have a released judge launch in the block and no not-run decision;
    its launch's own result and fetched run record must agree (judge_result_problem); the index and the judge files
    must pass judge_files_check. One record per block; it works for a sealed block (block A, sealed by the old
    seal.py: the seal must hold the same index) and changes no seal. The file is re-hashed at every use."""
    plan = load()
    doc, ref = file_record(path, sha256)
    problem = judge_record_problem(doc, block)
    if problem:
        fail(f"not a judge-completion record: {problem}")
    _utc_past(doc["utc"], "the judge-completion record")
    if block not in plan["blocks"]:
        fail(f"block {block} is not planned")
    if (records(plan).get("judges") or {}).get(block):
        fail(f"block {block} already has a judge-completion record")
    b = plan["blocks"][block]
    released = {x["judge"]["judge"] for k, x in enumerate(b["launches"]) if x.get("judge") and k < b["released"]}
    decided = judges_decided(plan, block)            # round 31 (K1): every block's not-run route
    required = judge_required_units(plan, block)
    for key, e in sorted(doc["judges"].items()):
        if key not in released:
            fail(f"block {block} has no released {key} judge launch")
        if key in decided:
            fail(f"'judge {key}' is named by a recorded not-run decision")
        problem = judge_result_problem(key, e, required)
        if problem:
            fail(f"judge {key}: {problem}")
    entry = {**ref, "path": str(pathlib.Path(path).resolve()), "block": block, "judges": doc["judges"],
             "index_sha256": doc["index_sha256"], "utc": doc["utc"], "recorded_by": doc["recorded_by"],
             "recorded_utc": mac.utc()}
    check = judge_record_valid(plan, block, entry)
    records(plan).setdefault("judges", {})[block] = entry
    mac.save_plan(plan)
    tags = {key: e["tag"] for key, e in sorted(doc["judges"].items())}
    mac.operator_action({"action": "record-judges", "block": block, "sha256": ref["sha256"], "tags": tags,
                         "index_sha256": doc["index_sha256"]})
    out = {"recorded": "judges", "block": block, "sha256": ref["sha256"], "tags": tags, **check}
    return {**out, "open": block_a_open(plan)} if block == "A" else out


# ----- round 32 (K2; addendum §34 point 6; block B's pre-flight G6): a not-run decision for any block but A ---------
# Block A keeps record-block-a-not-run (its plan's job names). Every other block's job that will not run is named by
# the lead's decision as "HOST:INDEX": a job of a done, unmoved host that is not complete (crashed, deferred or not
# started, and not to be re-run); a job a deferral or requeue left behind without taking it to a target (the
# contingency could not pay it); or every job of a pending host (a held launch, such as the second reference phase,
# that will never be released). The decision file is re-hashed at every use; completeness, the seal and seal.py status
# count and list it; release skips a launch that holds only decided hosts; no move ever takes a decided job.

NOT_RUN_JOB_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*:(0|[1-9][0-9]*)")


def not_run_problem(doc) -> str | None:
    """Why ``doc`` is not the lead's not-run decision {kind: rules.NOT_RUN_KIND, block, jobs: ["HOST:INDEX", ...],
    reason, utc, recorded_by} (exactly these keys; distinct job names; non-empty texts), or None."""
    if not isinstance(doc, dict) or set(doc) != set(rules.NOT_RUN_KEYS):
        return f"it must hold exactly {list(rules.NOT_RUN_KEYS)}"
    if doc["kind"] != rules.NOT_RUN_KIND:
        return f"its kind is not {rules.NOT_RUN_KIND!r}"
    if not all(isinstance(doc[k], str) and doc[k].strip() for k in ("block", "reason", "utc", "recorded_by")):
        return "block, reason, utc and recorded_by must be non-empty texts"
    jobs = doc["jobs"]
    if not isinstance(jobs, list) or not jobs or len(set(map(str, jobs))) != len(jobs) or \
            not all(isinstance(j, str) and NOT_RUN_JOB_RE.fullmatch(j) for j in jobs):
        return 'jobs must be a non-empty list of distinct "HOST:INDEX" names'
    return None


def not_run_entry_problem(e: dict) -> str | None:
    """Why a recorded not-run decision no longer holds (its file at the recorded path re-hashed, and the recorded
    block, jobs and reason equal to the file's), or None."""
    p = pathlib.Path(str(e.get("path")))
    try:
        on_disk = json.loads(p.read_text()) if p.is_file() else None
    except ValueError:
        on_disk = None
    if not isinstance(on_disk, dict) or mac.sha(p) != e.get("sha256") or \
            any(on_disk.get(k) != e.get(k) for k in ("block", "jobs", "reason")):
        return "a recorded not-run decision is missing or differs from its recorded SHA-256; it must stay at its " \
               "recorded path, unchanged"
    return None


def not_run_decided(plan: dict, block: str) -> dict:
    """(host, job index) -> the SHA-256 of the recorded not-run decision of block BLOCK that names it. Each of the
    block's decision files is re-hashed at every use and must hold the recorded block, jobs and reason."""
    out = {}
    for e in (plan.get("records") or {}).get("not_run") or []:
        if e.get("block") != block:
            continue
        problem = not_run_entry_problem(e)
        if problem:
            fail(f"block {block}: {problem}")
        for name in e["jobs"]:
            host, _, index = name.rpartition(":")
            out[(host, int(index))] = e["sha256"]
    return out


def launch_decided(b: dict, k: int, decided: dict) -> bool:
    """A hosts launch of block record ``b`` that holds only pending hosts every job of which is decided not run."""
    names, pending = b["launches"][k].get("hosts"), b.get("pending") or {}
    return bool(names) and all(n in pending and all((n, i) in decided for i in range(len(pending[n]["jobs"])))
                               for n in names)


def settled_view(b: dict, decided: dict) -> dict:
    """Block record ``b`` as block_complete reads it under not-run decisions: the launches from b["released"] on that
    hold only decided pending hosts count as released (release_next skips them so), and a pending host whose every
    job is decided is not pending."""
    released = b["released"]
    while released < len(b["launches"]) and launch_decided(b, released, decided):
        released += 1
    pending = {n: h for n, h in (b.get("pending") or {}).items()
               if not all((n, i) in decided for i in range(len(h["jobs"])))}
    return {**b, "released": released, "pending": pending}


def _carry_key(job: dict) -> tuple:
    return job["kind"], job.get("arm"), job.get("seed"), tuple(job.get("points") or ()), job.get("role")


def carried(plan: dict, host: str, job: dict) -> bool:
    """A job of a moved host that its move took along: a job of some host names it (deferred_from HOST, the same kind,
    arm, seed, points and role)."""
    key = _carry_key(job)
    return any(x.get("deferred_from") == host and _carry_key(x) == key for h in plan["hosts"].values()
               for x in h["jobs"])


def block_open_jobs(plan: dict, block: str, decided: dict | None = None) -> list[str]:
    """Round 32 (K2): every job of block BLOCK (not A) that is not complete, not taken along by a move and not named
    by a not-run decision, as "HOST:INDEX (kind arm seed)": each job of a pending host; each job of a released host
    that is not moved (a running host's planned jobs too); each job of a moved host that its move did not take along
    (carried). The block is complete only when this is empty (block_complete)."""
    decided = not_run_decided(plan, block) if decided is None else decided
    moved = moved_hosts(plan)
    hosts = [(n, h, False) for n, h in plan["hosts"].items() if h["block"] == block]
    hosts += [(n, h, True) for n, h in ((plan["blocks"].get(block) or {}).get("pending") or {}).items()]
    out = []
    for name, h, pending in sorted(hosts, key=lambda x: (x[0], x[2])):
        for i, j in enumerate(h["jobs"]):
            if j.get("status") == "complete" or (name, i) in decided or \
                    (not pending and name in moved and carried(plan, name, j)):
                continue
            out.append(f"{name}:{i} ({job_label(j['kind'], j.get('arm'), j.get('seed'))})")
    return out


def record_not_run(path: str, sha256: str) -> dict:
    """record-not-run FILE --sha256 H (round 32, K2): the lead's decision {kind: "stage1 not-run decision", block,
    jobs: ["HOST:INDEX", ...], reason, utc, recorded_by} that jobs of a planned, unsealed block other than A will not
    run. Each named job must be one of block_open_jobs (not complete, not taken along by a move, not decided before),
    and: on a released host that is not moved, the host is recorded done (record-done first: a running pod may still
    run it); on a moved host, the job was not taken along (name it where it moved); on a pending host, the decision
    (with any earlier one) names every job of that host (its pod would run every job it holds). The file is re-hashed
    at every use: keep it at its path, unchanged."""
    plan = load()
    doc, ref = file_record(path, sha256)
    problem = not_run_problem(doc)
    if problem:
        fail(f"not a not-run decision: {problem}")
    _utc_past(doc["utc"], "the not-run decision")
    block = doc["block"]
    if block == "A":
        fail("block A's jobs are named by record-block-a-not-run (its plan's job names)")
    if block not in plan["blocks"]:
        fail(f"block {block} is not planned")
    if block in plan["seals"]:
        fail(f"block {block} is sealed: a not-run decision is recorded before its seal")
    pending, moved = plan["blocks"][block].get("pending") or {}, moved_hosts(plan)
    decided, named = not_run_decided(plan, block), set()
    for name in doc["jobs"]:
        host, _, index = name.rpartition(":")
        h, i = pending.get(host) or plan["hosts"].get(host), int(index)
        if h is None or h["block"] != block:
            fail(f"{name}: {host} is not a host of block {block}")
        if i >= len(h["jobs"]):
            fail(f"{name}: {host} has no job {i}")
        j = h["jobs"][i]
        label = f"{name} ({job_label(j['kind'], j.get('arm'), j.get('seed'))})"
        if (host, i) in decided:
            fail(f"{label} is already named by a recorded not-run decision")
        if j.get("status") == "complete":
            fail(f"{label} is complete (it ran); a not-run decision cannot name it")
        if host not in pending and host in moved:
            if carried(plan, host, j):
                fail(f"{label}: a move took it to {', '.join(moved[host]) or 'another host'}; name it where it moved")
        elif host not in pending and not h.get("done"):
            fail(f"{label}: {host} is not recorded done (record-done first; its pod may still run it)")
        named.add((host, i))
    for host in sorted({x for x, _ in named if x in pending}):
        left = [i for i in range(len(pending[host]["jobs"])) if (host, i) not in named and (host, i) not in decided]
        if left:
            fail(f"{host} is not released: a not-run decision names every job of a pending host (its pod runs every "
                 f"job it holds); job(s) {left} are not named")
    entry = {**ref, "path": str(pathlib.Path(path).resolve()), "block": block, "jobs": list(doc["jobs"]),
             "reason": doc["reason"], "utc": doc["utc"], "recorded_by": doc["recorded_by"], "recorded_utc": mac.utc()}
    records(plan).setdefault("not_run", []).append(entry)
    mac.save_plan(plan)
    mac.operator_action({"action": "record-not-run", "block": block, "sha256": ref["sha256"], "jobs": list(doc["jobs"])})
    return {"recorded": "not_run", "block": block, "sha256": ref["sha256"], "jobs": list(doc["jobs"]),
            "open": block_open_jobs(plan, block), "complete": block_complete(plan, block)}


def build_block(plan: dict, block: str, spec: dict) -> dict:
    """The block's launches as host records (unnamed) and need launches; refuses every rule of the module doc."""
    if set(spec) - {"launches", "reused", "engine"} or not isinstance(spec.get("launches"), list) or not spec["launches"]:
        fail('--jobs FILE must be {"launches": [...], "reused": [...], "engine": "X"}')
    reused = {tuple(r) for r in spec.get("reused") or []}
    deal_engine = spec.get("engine", rules.ENGINE_DEFAULT)
    if deal_engine not in rules.ENGINES:
        fail("unknown engine for the deal")
    fx = plan["fixture"]
    branch = branch_name(plan)
    deal_pods = None
    if any("deal" in launch for launch in spec["launches"]):
        code = (plan_ab_checked(plan) or {}).get("code")
        try:
            deal_pods = rules.deal(rules.block_runs(code, block, tuple(sorted(reused))))
        except ValueError as exc:
            fail(f"block {block}: {exc}")
    used, launches = [], []
    for k, launch in enumerate(spec["launches"]):
        if not isinstance(launch, dict) or len(launch) != 1:
            fail(f"launch {k}: one of hosts, deal or judge")
        if "judge" in launch:
            spec_j = launch["judge"] or {}
            if not isinstance(spec_j, dict) or set(spec_j) - {"arms", "judge"}:
                fail(f'launch {k}: a judge launch is {{"judge": {{"arms": n, "judge": "harmbench"|"granite"}}}}')
            try:
                launches.append({"judge": rules.judge_pod(spec_j.get("judge", "granite"), spec_j.get("arms"))})
            except ValueError as exc:
                fail(f"launch {k}: {exc}")
            continue
        hosts, phase2 = [], "second_phase" in launch       # round 32 (K1): block B's second reference phase
        if phase2:
            if block != "B":
                fail(f"launch {k}: a second reference phase belongs to block B (the references on its own a0 runs)")
            launch = {"hosts": launch["second_phase"]}
        if "deal" in launch:
            idx = launch["deal"]
            if not (isinstance(idx, list) and idx and all(isinstance(i, int) and 0 <= i < len(deal_pods) for i in idx)):
                fail(f"launch {k}: deal indices must name the block's dealt pods")
            used += idx
            for i in idx:
                raw = [{"kind": "a0_arm" if a == "a0" else "arm", "arm": a, "seed": s, "engine": deal_engine}
                       for a, s in deal_pods[i]]
                hosts.append(("arms", raw))
        elif "hosts" in launch:
            if not (isinstance(launch["hosts"], list) and launch["hosts"]) or any(
                    not isinstance(h, list) or not h for h in launch["hosts"]):
                fail(f"launch {k}: every host needs at least one job")
            for h in launch["hosts"]:
                raw = [dict(j) for j in h]
                for i, job in enumerate(raw):
                    check_job(job, i, raw, block, plan, reused)
                    if phase2 and job["kind"] not in rules.SECOND_PHASE_KINDS:
                        fail(f"launch {k}: the second reference phase holds evaluation-only references only "
                             f"({', '.join(rules.SECOND_PHASE_KINDS)}), not {job['kind']}")
                check_host(raw)
                hosts.append(("job", raw))
        else:
            fail(f"launch {k}: one of hosts, deal or judge")
        launches.append({"hosts": hosts, "second_phase": True} if phase2 else {"hosts": hosts})
    if deal_pods is not None and sorted(used) != list(range(len(deal_pods))):
        fail(f"block {block}: every dealt pod appears exactly once in the launches")
    if block in ("A", "B", "C") and deal_pods is None:
        fail(f"block {block}: its training runs come from the deal")
    if block == "B":
        second_phase_layout(launches, deal_pods)
    if block == "S1-0":
        shapes = [[[j["kind"] for j in jobs] for _, jobs in launch.get("hosts", [])] for launch in launches]
        if shapes != [[["w1_18"]]]:
            fail("block S1-0: one pod, W1-18 alone (§8 Q1)")
    elif any(j["kind"] == "w1_18" for launch in launches for _, jobs in launch.get("hosts", []) for j in jobs):
        fail("W1-18 runs only as job 0 of an S1-0 pod")
    if block == "sim":                                   # kit round 34: B14's pass runs once, alone, on one pod
        shapes = [[[j["kind"] for j in jobs] for _, jobs in launch.get("hosts", [])] for launch in launches]
        if shapes != [[["similarity"]]]:
            fail('block sim: one launch of one pod holding B14\'s similarity pass alone ({"launches": [{"hosts": '
                 '[[{"kind": "similarity"}]]}]}; kit round 34)')
    if block in ("cert", "certify") and len([1 for launch in launches for _ in launch.get("hosts", [])]) != 1:
        fail(f"block {block}: one pod")
    cert_kinds = [j["kind"] for launch in launches for _, jobs in launch.get("hosts", []) for j in jobs]
    if block == "cert" and (cert_kinds.count("cert_c1") != 1 or cert_kinds.count("cert_c2") != 1):
        fail("block cert: the certificate pod runs C1 and C2 once each (G4: C1, C2 and C3 on one pod; addendum §22 "
             "point 1's binding check is read from C2)")
    if block == "cert" and not any(j["kind"] == "cert_c3" for launch in launches for _, jobs in launch.get("hosts", [])
                                   for j in jobs) and not records(plan).get("c3_fallback"):
        fail("block cert: plan C3 (cert_c3) or record its §22 point 2 fallback (record-c3-fallback), which says it "
             "is dropped")
    out, all_jobs = [], []
    for k, launch in enumerate(launches):
        if "judge" in launch:
            out.append({"judge": launch["judge"]})
            continue
        records_k = []
        for role, raw in launch["hosts"]:
            jobs = []
            for job in raw:
                job["engine"] = job.get("engine") or default_engine(job)
                recipe = job.get("recipe") or default_recipe(job)
                rec = rules.job_record(job["kind"], job.get("arm"), job.get("seed"), None, steps_of(job), fx,
                                       branch=branch, engine=job["engine"], points=job.get("points"), recipe=recipe,
                                       regen_source=job.get("regen_source"))
                if job.get("role"):
                    rec["role"] = job["role"]
                if job["kind"] in rules.D2_KINDS:
                    rec["d2"] = d2_entry(plan, job["kind"])
                if job["kind"] == "cert_c3":
                    rec["c3"] = c3_entry(plan)
                if job["kind"] == "a1_rescore":
                    rec["groups"] = rescore_groups()
                if job["kind"] == "similarity":          # kit round 34: B14's inputs by SHA-256
                    rec["similarity"] = similarity_entry(plan)
                jobs.append(rec)
            role = {"S1-0": "w1_18", "cert": "cert", "certify": "certify"}.get(block, role)
            if role == "job" and all(j["kind"] in rules.DIAG_KINDS for j in jobs):
                role = "diagnostics"
            records_k.append(host_record(plan, block, role, jobs, None, k))
            all_jobs += jobs
        out.append({"hosts": records_k, "second_phase": True} if launch.get("second_phase") else {"hosts": records_k})
    if block != "A":                     # round 31 (K2); block A: its plan's own check (check_block_a_content)
        units = planned_judged_units(block, all_jobs)
        for k, launch in enumerate(out):
            j = launch.get("judge")
            if j and j["arms"] < units:
                fail(f"launch {k}: the {j['judge']} judge launch is over {j['arms']} units, below the {units} judged "
                     f"units block {block}'s jobs will produce (arm, a0_arm and ref_train runs, one per ref_eval and "
                     "safe_lora point, and the block's re-judged pins; addendum §32 point 1)")
    return {"launches": out, "jobs": all_jobs, "branch": branch, "deal": deal_pods, "reused": sorted(reused)}


def planned_judged_units(block: str, jobs: list[dict]) -> int:
    """Round 31 (K2; addendum §32 point 1): the number of judged units a block's planned jobs will produce, the units
    judge_required_units requires once they ran: one per arm, a0_arm and ref_train run (rules.JUDGED_RUN_KINDS), one
    per evaluation point of each ref_eval and safe_lora job (rules.JUDGED_B10_KINDS; B10 writes one unit per point),
    plus the block's pinned re-judged units (rules.REJUDGED_PINS; none for block B)."""
    n = sum(1 for j in jobs if j["kind"] in rules.JUDGED_RUN_KINDS)
    n += sum(len(j.get("points") or ()) for j in jobs if j["kind"] in rules.JUDGED_B10_KINDS)
    return n + len(rules.REJUDGED_PINS.get(block, ()))


# ----- round 32 (K1; addendum §34 point 5; block B's pre-flight G4): block B's second reference phase ----------------
# The evaluation-only references at a0 1105-1107 evaluate block B's own a0 runs, whose adapters exist only after block
# B's a0 arm pods. They are planned with block B (its need, completeness and seal count them) in a launch
# {"second_phase": [[job, ...], ...]} that release holds until the a0 runs are recorded done, B10/B11 are re-pinned
# with them and engine X is re-packed (second_phase_gate). Nothing else of the kit changes: the held launch is an
# ordinary hosts launch of block B once released.


def second_phase_layout(launches: list[dict], deal_pods) -> None:
    """K1 at init (block B): a reference (ref_eval, safe_lora) on one of the block's own a0 runs (the deal's a0 seeds)
    is in a second-phase launch, and a second-phase launch holds only such references; every second-phase launch
    comes after every deal launch (the a0 runs) and before every judge launch (which judges its units)."""
    own = {s for pod in deal_pods or [] for a, s in pod if a == "a0"}
    for k, x in enumerate(launches):
        for _, raw in x.get("hosts", []):
            for j in raw:
                if j["kind"] not in rules.SECOND_PHASE_KINDS or (j.get("seed") in own) == bool(x.get("second_phase")):
                    continue
                if x.get("second_phase"):
                    fail(f"launch {k}: the second reference phase evaluates block B's own a0 runs only (seeds "
                         f"{sorted(own)}), not a0 at {j.get('seed')}")
                fail(f"launch {k}: {j['kind']} on a0 at {j.get('seed')} evaluates block B's own a0 run, whose adapter "
                     'exists only after its arm pod: plan it in a {"second_phase": [...]} launch (addendum §34 point 5)')
    deals = [k for k, x in enumerate(launches) if any(role == "arms" for role, _ in x.get("hosts", []))]
    second = [k for k, x in enumerate(launches) if x.get("second_phase")]
    judges = [k for k, x in enumerate(launches) if "judge" in x]
    if second and min(second) < max(deals, default=-1):
        fail("the second reference phase comes after every deal launch (block B's a0 runs come first)")
    if second and judges and max(second) > min(judges):
        fail("the second reference phase comes before every judge launch (the judges judge its units)")


def pinned_s1_settings(rel: str) -> dict:
    """K1: an S1 settings file read at its stage1_rules.S1_CODE pin, the one place that holds B10's and B11's pins:
    ROOT/rel must hash to S1_CODE[rel] (the B10/B11 re-pin round changes that pin and the file together)."""
    return pinned_doc({"path": rel, "sha256": rules.S1_CODE[rel]}, f"{rel} at its stage1_rules.S1_CODE pin")


def own_a0_runs(plan: dict, block: str) -> dict:
    """K1: seed -> (host, job index, job) of block BLOCK's own a0 run at that seed (an a0_arm job of the block's deal,
    not B+Qi's own a0), recorded complete by record-done with its unit pulled and its COMPLETE.json SHA-256. Two
    complete attempts at one seed refuse (the lead decides which unit B10 pins)."""
    out = {}
    for name, h in sorted(plan["hosts"].items()):
        if h["block"] != block:
            continue
        for i, j in enumerate(h["jobs"]):
            if j["kind"] != "a0_arm" or j.get("role") is not None or j.get("status") != "complete" or \
                    j.get("pulled") is False:
                continue
            if j["seed"] in out:
                fail(f"block {block}: two complete a0 runs at {j['seed']}; the lead decides which unit B10 pins")
            if not (isinstance(j.get("complete_sha256"), str) and SHA_RE.fullmatch(j["complete_sha256"])):
                fail(f"{name}: its a0 run at {j['seed']} has no COMPLETE.json SHA-256 in plan.json")
            out[j["seed"]] = (name, i, j)
    return out


def a0_fingerprint(host: str, index: int, job: dict) -> dict:
    """K6: the a0 run's e1 and q adapter fingerprints from its readable record job-I/rules.A0_FINGERPRINT_RECORD (the
    job runner writes it after a complete a0_arm job; record-done keeps its SHA-256 among the job's outputs): the
    pulled file re-hashed to that SHA-256, of the record's kind and version 1, naming this job, arm a0, its seed, unit
    and COMPLETE.json SHA-256, with a 64-hex e1 (and q 64-hex or null). Nothing sealed is opened."""
    rel = f"job-{index}/{rules.A0_FINGERPRINT_RECORD}"
    digest = (job.get("outputs") or {}).get(rel)
    p = HERE / "retrieved" / host / "tree" / rel
    if not digest:
        fail(f"the second reference phase waits: {host}'s a0 run at {job['seed']} lists no readable fingerprint record "
             f"{rel} among its outputs (the job runner of kit round 32 writes it, K6)")
    if not p.is_file() or mac.sha(p) != digest:
        fail(f"{host}: {rel} is missing from the pulled tree or differs from its recorded SHA-256")
    try:
        doc = json.loads(p.read_text())
    except ValueError:
        doc = None
    points = doc.get("checkpoints") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or (doc.get("kind"), doc.get("version"), doc.get("job"), doc.get("arm"),
                                     doc.get("seed"), doc.get("unit"), doc.get("complete_sha256")) != (
            rules.A0_FINGERPRINT_KIND, 1, index, "a0", job["seed"], job.get("unit"), job.get("complete_sha256")) or \
            not isinstance(points, dict) or set(points) != {"e1", "q"} or not SHA_RE.fullmatch(str(points["e1"])) or \
            not (points["q"] is None or SHA_RE.fullmatch(str(points["q"]))):
        fail(f"{host}: {rel} is not this a0 run's fingerprint record ({rules.A0_FINGERPRINT_KIND!r}, version 1, its "
             "job, seed, unit and COMPLETE.json SHA-256, a 64-hex e1)")
    return {"e1": points["e1"], "q": points["q"]}


def second_phase_gate(plan: dict, block: str, hosts: list[dict]) -> dict:
    """K1 at release: a second-phase launch is released only when, for each of its jobs' seeds S, (1) block BLOCK's
    own a0 run at S is recorded complete (own_a0_runs) with its readable fingerprint record (K6, a0_fingerprint);
    (2) B10's settings at their S1_CODE pin name that run's COMPLETE.json SHA-256 as S's reference unit with e1 (and,
    if pinned, q) fingerprint prefixes of the record's fingerprints, and for a safe_lora job B11's settings at their
    pin accept at S exactly the record's e1 fingerprint (the B10/B11 re-pin with these fingerprints); (3) the packed
    stage of the host's engine holds the input gate_a_complete:S at that SHA-256 and seals B10's and B11's four files
    at their S1_CODE pins (the re-pack after the re-pin). Returns seed -> the COMPLETE.json SHA-256 checked."""
    runs, checked = own_a0_runs(plan, block), {}
    for seed in sorted({j["seed"] for h in hosts for j in h["jobs"]}):   # the a0 runs first, then the re-pin
        if seed not in runs:
            fail(f"the second reference phase waits: block {block}'s a0 run at {seed} is not recorded complete "
                 "(its arm pod first; record-done)")
    b10 = pinned_s1_settings(rules.B10_SETTINGS)
    b11 = pinned_s1_settings(rules.B11_SETTINGS) if any(j["kind"] == "safe_lora" for h in hosts for j in h["jobs"]) \
        else None
    for h in hosts:
        for j in h["jobs"]:
            seed = j["seed"]
            complete, fp = runs[seed][2]["complete_sha256"], a0_fingerprint(*runs[seed])
            ref = (b10.get("reference_units") or {}).get(str(seed))
            if not isinstance(ref, dict) or ref.get("complete_sha256") != complete:
                fail(f"the second reference phase waits for the B10/B11 re-pin: {rules.B10_SETTINGS} at its S1_CODE pin "
                     f"names no reference unit for a0 {seed} with the COMPLETE.json SHA-256 plan.json records "
                     f"({complete[:12]}...)")
            prefixes = ref.get("fingerprint_prefixes") if isinstance(ref.get("fingerprint_prefixes"), dict) else {}
            e1, q = prefixes.get("e1"), prefixes.get("q")
            if not (isinstance(e1, str) and e1 and fp["e1"].startswith(e1)) or \
                    (q is not None and not (isinstance(q, str) and q and str(fp["q"]).startswith(q))):
                fail(f"the second reference phase waits for the B10/B11 re-pin: {rules.B10_SETTINGS}'s fingerprint "
                     f"prefixes for a0 {seed} are not those of the run's readable fingerprint record (K6)")
            if j["kind"] == "safe_lora":
                accepted = ((((b11.get("adapter") or {}).get("accepted") or {}).get(str(seed))) or {}).get("fingerprint")
                if accepted != fp["e1"]:
                    fail(f"the second reference phase waits for the B10/B11 re-pin: {rules.B11_SETTINGS} at its S1_CODE "
                         f"pin does not accept a0 {seed}'s e1 fingerprint from its readable record (K6)")
            checked[seed] = complete
    for h in hosts:                                   # the re-pack, after the re-pin
        for j in h["jobs"]:
            packed, _ = packed_input_sha(h["engine"], f"gate_a_complete:{j['seed']}")
            if packed != checked[j["seed"]]:
                fail(f"the second reference phase waits for the re-pack: the packed stage1-{h['engine']} holds no "
                     f"gate_a_complete:{j['seed']} at the a0 run's COMPLETE.json SHA-256 (pack_setup.py {h['engine']} "
                     "with it)")
    for engine in sorted({h["engine"] for h in hosts}):
        files = (packed_sealed(engine)[0].get("files") or {})
        stale = [rel for rel in rules.B10_B11_FILES if files.get(rel) != rules.S1_CODE[rel]]
        if stale:
            fail(f"the second reference phase waits for the re-pack: the packed stage1-{engine} seals {stale[0]} at "
                 "another SHA-256 than its stage1_rules.S1_CODE pin (re-pack after the B10/B11 re-pin)")
    return checked


def need_launches(built: dict) -> list:
    out = []
    for launch in built["launches"]:
        if "judge" in launch:
            out.append([launch["judge"]])
        else:
            out.append([{"cap_hours": h["cap_hours"], "spend_usd": h["spend_upper_usd"]} for h in launch["hosts"]])
    return out


def check_launch_gates(plan: dict, block: str, hosts: list[dict]) -> None:
    jobs = [j for h in hosts for j in h["jobs"]]
    ab = plan_ab_checked(plan)                       # G3 again at release (VG2-1): a record edited after init refuses
    if ab is not None and ab["code"] == "none":
        fail(f"block {block}: the plan-A/B record says no stage 1 (sigma above 6.0 pp): no stage-1 pod")
    if block in ("A", "certify", "B", "C") and ab is None:
        fail(f"block {block}: the plan-A/B record is not recorded (G3)")
    gate_g1(plan, block, jobs)
    gate_g4(plan, block, jobs)
    gate_records(plan, jobs)
    gate_certification(plan, jobs)


def release_hosts(plan: dict, block: str, names_hosts: list[tuple[str, dict]]) -> list[str]:
    """Bind every edit by SHA-256, check the recipes' pins and the packed engine, then move the hosts into
    plan["hosts"] (launch.py and host.py read only those)."""
    sources = edit_sources(plan) if any(j["kind"] in ("arm", "regenerate", "cert_c1", "c0")
                                        for _, h in names_hosts for j in h["jobs"]) else {}
    check_launch_gates(plan, block, [h for _, h in names_hosts])
    for name, h in names_hosts:
        rec = engine_receipt(h["engine"])
        h["sealed_files_sha256"] = rec.get("sealed_files_sha256")
        for job in h["jobs"]:
            if job["kind"] in ("arm", "regenerate", "cert_c1", "c0") and job["arm"] != "a0":
                job["edit"] = resolve_edit(job, sources, required=True)
            if job["kind"] == "similarity" and job.get("similarity") != similarity_entry(plan):
                fail(f"{name}: B14's inputs (similarity_entry) differ from the ones planned at init-block; the lead "
                     "decides (kit round 34)")
            name_r = job.get("recipe")
            if name_r and h["engine"] == "Y":
                check_recipe_y(plan, name_r)            # engine Y's tree and code (B+Qi's recipe is only there)
            elif name_r:
                path = rules.RECIPE_NAMES[name_r]
                if not (ENGINE_ROOT / path).is_file() or mac.sha(ENGINE_ROOT / path) != rules.RECIPE_PINS[path]:
                    fail(f"{path}: missing or differs from its pin (recipe {name_r})")
                if path not in plan["recipes"]:
                    plan["recipes"][path] = {"sha256": rules.RECIPE_PINS[path], "config_sha256": recipe_sha(path)}
                elif plan["recipes"][path].get("engine") == "Y":          # only engine Y's code has hashed it so far
                    config_x = recipe_sha(path)
                    if plan["recipes"][path]["config_sha256"] != config_x:
                        fail(RECIPE_ENGINES_DIFFER.format(name=name_r))
                    plan["recipes"][path] = {"sha256": rules.RECIPE_PINS[path], "config_sha256": config_x}
                if name_r in rules.TRAINING_IDENTITY_RECIPES:
                    entry = plan["recipes"][path]
                    entry.setdefault("training_identity", recipe_training_identity(path))
                    if entry["training_identity"] != rules.TRAINING_IDENTITY:
                        fail(f"recipe {name_r}: its training identity is not {rules.TRAINING_IDENTITY[:8]}... (§8 Q4)")
    for name, h in names_hosts:
        plan["hosts"][name] = h
    return [n for n, _ in names_hosts]


# ----- round 32 (K4; addendum §34 point 7, §20 point 1; block B's pre-flight G8): block B's group on one record -----


def group_jobs(plan: dict, block: str, given) -> dict:
    """K4: block B's group (certify, B) on one funding record. At the group's first init, every later part of the
    group that is not planned (rules.BLOCKS order: certify, then B) must be given as PART=FILE, its jobs file; each is
    built now (build_block: every rule of its init but the gates its own init and release check again) for its need
    launches only, so the first funding record covers the whole group before its first launch (addendum §20 point 1,
    as group A's plan does). No other part may be given, and no group but B takes the option. Returns part -> its
    jobs file (path, SHA-256), its number of pods and its need launches."""
    group, given = rules.FUNDING_BLOCK[block], list(given or [])
    if group != "B":
        if given:
            fail("--group-jobs belongs to block B's group (certify, B)")
        return {}
    later = [] if planned_parts(plan, group) else [
        p for p in rules.BLOCKS if rules.FUNDING_BLOCK[p] == group and rules.BLOCKS.index(p) > rules.BLOCKS.index(block)
        and p not in plan["blocks"]]
    out = {}
    for item in given:
        part, sep, path = str(item).partition("=")
        if not sep or part not in later or part in out:
            fail(f"--group-jobs {str(item)[:40]!r}: give PART=FILE once for each later part of block B's group that "
                 f"is not planned at its first init ({', '.join(later) or 'none here'})")
        p = pathlib.Path(path)
        try:
            spec = json.loads(p.read_text())
        except (OSError, ValueError):
            fail(f"--group-jobs {part}=FILE: not a readable JSON file")
        if not isinstance(spec, dict):
            fail(f"--group-jobs {part}=FILE must be a JSON object")
        built = build_block(plan, part, spec)
        out[part] = {"path": str(p.resolve()), "sha256": mac.sha(p), "need_launches": need_launches(built),
                     "pods": sum(len(x.get("hosts", [])) for x in built["launches"])}
    missing = [p for p in later if p not in out]
    if missing:
        fail(f"init-block {block} is the first init of block B's group: its funding record must cover the whole "
             f"group's need (addendum §20 point 1, §34 point 7): give --group-jobs {missing[0]}=FILE")
    return out


def group_summary(plan: dict, block: str, jobs_path: str, later: dict) -> dict:
    """K4: what the need of an init in block B's group counts: the parts planned before it, this part and the later
    parts given at the first init; at a later init, whether this jobs file is the one the first init counted."""
    parts = planned_parts(plan, "B")
    out = {"planned": parts, "this": block, "later": {p: {"sha256": x["sha256"], "pods": x["pods"]}
                                                      for p, x in later.items()}}
    if parts:
        counted = (plan["blocks"][parts[0]].get("group_jobs") or {}).get(block)
        out["counted_at_first_init"] = None if counted is None else (
            "the same jobs file" if counted["sha256"] == mac.sha(pathlib.Path(jobs_path)) else
            "another jobs file (its need is checked against the first funding record here)")
    return out


def init_block(args: argparse.Namespace) -> dict:
    block = args.block
    if block not in rules.BLOCKS:
        fail(f"unknown block {block!r}")
    plan = load()
    gate_order(plan, block)
    try:
        spec = json.loads(pathlib.Path(args.jobs).read_text())
    except (OSError, ValueError):
        fail("--jobs FILE: not a readable JSON file")
    if not isinstance(spec, dict):
        fail("--jobs FILE must be a JSON object")
    built = build_block(plan, block, spec)
    gate_g1(plan, block, built["jobs"])
    gate_g4(plan, block, built["jobs"])
    gate_bqi_pairs(plan, built["jobs"])
    gate_records(plan, built["jobs"])
    gate_certification(plan, built["jobs"])            # round 32 (K3): LS-08 at planning too, not only at release
    refuse_duplicates(plan, built["jobs"])
    group = rules.FUNDING_BLOCK[block]
    mine = need_launches(built)
    plan_a = check_group_a(plan, block, launch_shapes(built["launches"], built["deal"])) if group == "A" else None
    rest = [[{"cap_hours": p["cap_hours"], "spend_usd": p["spend_usd"]} for p in x["pods"]]
            for x in (plan_a["rest"] if plan_a else []) if x["pods"]]
    later = group_jobs(plan, block, getattr(args, "group_jobs", None))   # round 32 (K4): block B's whole group
    rest += [x for part in later.values() for x in part["need_launches"]]
    need = rules.funding_need_usd(group_launches(plan, group) + mine + rest, rules.CONTINGENCY_FACTOR)
    pods = [{"launch": k, "cap_hours": h["cap_hours"], "guard_usd": rules.cents(h["guard_usd"]),
             "counted": h["counted"], "jobs": [f"{j['kind']}:{j.get('arm')}:{j.get('seed')}" for j in h["jobs"]]}
            for k, launch in enumerate(built["launches"]) for h in launch.get("hosts", [])]
    summary = {"block": block, "funding_block": group, "branch": built["branch"], "pods": pods,
               "need_usd": need["need_usd"], "base_need_usd": need["base_need_usd"],
               "contingency_usd": need["contingency_usd"], "terms_cents": [round(t * 100, 4) for t in need["terms_usd"]]}
    if plan_a:
        summary["block_a_plan"] = {
            "source": "kit default (recorded at this init)" if plan_a["default"] else "recorded",
            "plan_code": plan_a["doc"]["plan_code"], "launch_map": plan_a["map"],
            "not_in_plan": [dict(x) for x in plan_a["doc"]["not_in_plan"]], "ln15e": dict(LN15E_IN_PLAN),
            "rest": [{"role": x["role"], "pods": [{"cap_hours": p["cap_hours"], "spend_usd": round(p["spend_usd"], 6),
                                                   "unmeasured": p["unmeasured"]} for p in x["pods"]]}
                     for x in plan_a["rest"]]}
    if block == "cert":
        summary["c3"] = ("dropped: the §22 point 2 fallback record is recorded" if records(plan).get("c3_fallback")
                         else "planned: subsample " + records(plan)["c3"]["subsample"]["sha256"])
    second = [k for k, x in enumerate(built["launches"]) if x.get("second_phase")]
    if second:                                         # round 32 (K1): held until second_phase_gate passes
        summary["second_phase_launches"] = second
    if group == "B":                                   # round 32 (K4): the parts the need counts
        summary["group"] = group_summary(plan, block, args.jobs, later)
    if args.dry_run:
        return {"dry_run": True, **summary}
    if not args.funding:
        fail(f"init-block {block} needs --funding FILE (the lead's record of the user's top-up for block {group})")
    funding = funding_record(args.funding, group)
    if not funding["amount_usd"] >= need["need_usd"]:
        fail(f"the funding ${funding['amount_usd']:.2f} is below the need ${need['need_usd']:.2f} "
             f"({rules.CONTINGENCY_FACTOR} x ${need['base_need_usd']:.2f})")
    first = group_anchor(plan, group) if group == "A" else None
    if first is not None and not first["amount_usd"] >= need["need_usd"]:
        fail(f"block {block}: the need ${need['need_usd']:.2f} is above block A's first funding record "
             f"(${first['amount_usd']:.2f}, {first['sha256'][:8]}...): block A's funding event covers the whole group "
             "before S1-0 launches (addendum §20 point 1)")
    anchor_b = group_anchor(plan, group) if group == "B" else None   # round 32 (K4), re-hashed at its path
    if anchor_b is not None and funding["sha256"] != anchor_b["sha256"]:
        fail(f"block {block}: block B's group has one funding record (addendum §34 point 7): give the first init's "
             f"record ({anchor_b['sha256'][:8]}...), which must cover the need of every part planned")
    names, pending = [], []
    for k, launch in enumerate(built["launches"]):
        if "judge" in launch:
            pending.append({"judge": launch["judge"], "hosts": []})
            continue
        entry = []
        for h in launch["hosts"]:
            name = new_host_name({"hosts": {**plan["hosts"], **{n: 1 for n in names}}, "blocks": plan["blocks"]},
                                 block)
            names.append(name)
            entry.append((name, h))
        pending.append({"hosts": entry, "second_phase": True} if launch.get("second_phase") else {"hosts": entry})
    record = {"funding": funding, "need": need, "need_launches": mine, "branch": built["branch"],
              "deal": built["deal"], "reused": built["reused"], "utc": mac.utc(),
              "launches": [{"judge": p["judge"]} if "judge" in p else
                           {"hosts": [n for n, _ in p["hosts"]], **({"second_phase": True} if p.get("second_phase")
                                                                    else {})}
                           for p in pending],
              "released": 0, "pending": {n: h for p in pending for n, h in p.get("hosts", [])},
              "seq": max([b.get("seq", -1) for b in plan["blocks"].values()] + [len(plan["blocks"]) - 1]) + 1}
    if later:                                          # round 32 (K4): what the first funding record covers
        record["group_jobs"] = {part: dict(x) for part, x in later.items()}
    if plan_a and plan_a["default"] is not None:       # no lead record: the kit's default is the plan from now on
        doc = plan_a["doc"]
        records(plan)["block_a_plan"] = {"source": "kit default", "path": None, "sha256": hashlib_sha(canonical(doc)),
                                         "doc": doc, "default": plan_a["default"], "plan_code": doc["plan_code"],
                                         "need_usd": need_of(plan_a["frozen"])["need_usd"], "utc": mac.utc(),
                                         "replan": False}
    plan["blocks"][block] = record
    contingency = plan["contingency"].setdefault(group, {"usd": 0.0, "remaining_usd": 0.0, "spent": [],
                                                         "not_rerun": []})
    spent = sum(s["cost_usd"] for s in contingency["spent"])
    contingency.update(usd=need["contingency_usd"], remaining_usd=need["contingency_usd"] - spent)
    released = release_next(plan, block)
    mac.save_plan(plan)
    mac.operator_action({"action": "init-block", "block": block, "hosts": names, "need_usd": need["need_usd"],
                         "funding_sha256": funding["sha256"]})
    return {**summary, "hosts": names, "released": released}


def release_next(plan: dict, block: str) -> list[str]:
    """Release the block's next launch (judge launches are recorded, not hosts). A launch waits until the launch
    before it has no host that is not done or moved; while the user's budget-guard-off decision is recorded
    (rules.guard_off_record: plan.json's records.guard_off, its file re-hashed at its recorded path), a hosts launch
    is released without that wait and the release is recorded in the block's released_early (addendum §28). Every
    other check of a release stays: the order of the launches, the block-A plan (check_planned_group_a) and every
    gate of release_hosts. A judge launch judges the earlier launches' units, so it still waits, the guard off or not,
    until every earlier launch's hosts are done or moved. Round 32: a hosts launch whose every pending host's jobs are
    all named by not-run decisions (K2) is skipped (counted released, recorded under "skipped", its hosts never
    released), after the same wait as a release; a second-phase launch (K1) is released only when second_phase_gate
    passes, the guard off or not."""
    b = plan["blocks"][block]
    decided = not_run_decided(plan, block) if block != "A" else {}
    while b["released"] < len(b["launches"]):
        k = b["released"]
        launch = b["launches"][k]
        skip = launch_decided(b, k, decided)          # round 32 (K2): it holds only decided pending hosts
        if rules.FUNDING_BLOCK[block] == "A":
            check_planned_group_a(plan, block)        # round 3a: the block-A plan again at every release
        if k > 0:
            before = b["launches"][k - 1].get("hosts", [])
            moved = {d["from"] for d in plan["deferrals"]} | {r["from"] for r in plan.get("requeues") or []}
            open_hosts = [n for n in before if n in plan["hosts"] and not plan["hosts"][n].get("done") and n not in moved]
            off = rules.guard_off_record(HERE)        # (§28) the user's recorded decision, re-hashed; None: no record
            if off is not None and "judge" in launch:
                waiting = [n for x in b["launches"][:k] for n in x.get("hosts", [])
                           if n in plan["hosts"] and not plan["hosts"][n].get("done") and n not in moved]
                if waiting:
                    fail(f"block {block}: launch {k} is a judge launch; it waits until every earlier launch's hosts are "
                         f"done, with the budget guard off too ({waiting[0]})")
            if skip and off is not None:
                open_hosts = []                       # a skipped launch releases no host: nothing is released early
            if open_hosts:
                if off is None:
                    fail(f"block {block}: launch {k - 1}'s hosts are not done ({open_hosts[0]})")
                b.setdefault("released_early", []).append({"launch": k, "open_hosts": open_hosts,
                                                           "guard_off_sha256": off["sha256"], "utc": mac.utc()})
        if skip:
            names = launch["hosts"]
            b.setdefault("skipped", []).append({"launch": k, "hosts": list(names), "utc": mac.utc(), "decisions": sorted(
                {decided[(n, i)] for n in names for i in range(len(b["pending"][n]["jobs"]))})})
            b["released"] += 1
            continue
        if "judge" in launch:
            b["released"] += 1
            continue
        if launch.get("second_phase"):                # round 32 (K1): a0 runs done, B10/B11 re-pinned, X re-packed
            second_phase_gate(plan, block, [b["pending"][n] for n in launch["hosts"]])
        names = release_hosts(plan, block, [(n, b["pending"][n]) for n in launch["hosts"]])
        for n in names:
            del b["pending"][n]
        b["released"] += 1
        return names
    return []


def release(block: str) -> dict:
    plan = mac.load_plan()
    if block not in plan["blocks"]:
        fail(f"block {block} is not planned")
    before = plan["blocks"][block]["released"]
    early_before = len(plan["blocks"][block].get("released_early") or [])
    names = release_next(plan, block)
    if not names and plan["blocks"][block]["released"] == before:
        fail(f"block {block}: no launch left to release")
    early = (plan["blocks"][block].get("released_early") or [])[early_before:]   # (§28) released under the decision
    skipped = [x for x in plan["blocks"][block].get("skipped") or [] if x["launch"] >= before]   # round 32 (K2)
    mac.save_plan(plan)
    mac.operator_action({"action": "release", "block": block, "hosts": names,
                         "released": plan["blocks"][block]["released"], **({"released_early": early} if early else {})})
    if skipped:                                       # round 32 (K2): launches skipped under not-run decisions
        mac.operator_action({"action": "release-skipped", "block": block, "skipped": skipped})
    out = {"block": block, "released": names, "launches_released": plan["blocks"][block]["released"],
           **({"skipped": skipped} if skipped else {})}
    return {**out, "released_early": early} if early else out


def deal_command(block: str, reuse: list) -> dict:
    plan = mac.load_plan() if mac.PLAN.exists() else {"records": {"plan_ab": None}}
    code = (plan_ab_checked(plan) or {}).get("code")
    try:
        pods = rules.deal(rules.block_runs(code, block, tuple(tuple(r) for r in reuse or [])))
    except ValueError as exc:
        fail(f"block {block}: {exc}")
    return {"block": block, "plan": code, "pods": [[f"{a}@{s}" for a, s in p] for p in pods]}


# ----- records (G1, G3, G4, Q16, Q17, K = 12, sealed edits) --------------------------------------------------------


def _need(doc: dict, keys: tuple, what: str) -> None:
    if any(doc.get(k) in (None, "") for k in keys):
        fail(f"{what} must hold {list(keys)}")


def _host_job(plan: dict, host: str, kind: str, block: str) -> dict:
    h = plan["hosts"].get(host)
    if h is None or h["block"] != block:
        fail(f"{host} is not a host of block {block}")
    job = next((j for j in h["jobs"] if j["kind"] == kind), None)
    if job is None or job.get("status") != "complete":
        fail(f"{host}: its {kind} job is not recorded complete (record-done first)")
    return job


def _evidence(host: str, items) -> list:
    if not isinstance(items, list) or not items:
        fail("the record must list its evidence files [{path, sha256}]")
    tree = HERE / "retrieved" / host / "tree"
    for e in items:
        p = tree / str(e.get("path"))
        if ".." in pathlib.PurePath(str(e.get("path"))).parts or not p.is_file() or mac.sha(p) != e.get("sha256"):
            fail(f"{host}: an evidence file is missing from the pulled tree or differs from the record")
    return items


def record_branch(path: str, sha256: str) -> dict:
    plan = load()
    doc, ref = file_record(path, sha256)
    old = records(plan).get("branch")
    if old is not None and bank500_planned(plan):
        fail("the cap branch never changes once a 500-bank job is planned (REV4 §6.3)")
    if doc.get("kind") == RECORD_KINDS["default_full"]:
        _need(doc, ("reason", "utc", "recorded_by"), "a 'Branch full by default' record")
        if doc.get("branch", "full") != "full":
            fail("a default record is Branch full")
        if old is not None and old.get("source") == "w1_18":
            fail("W1-18's branch record exists: Branch full by default applies only if W1-18 cannot run or fails")
        s10 = [h for h in plan["hosts"].values() if h["block"] == "S1-0"]
        s10 += [h for h in ((plan["blocks"].get("S1-0") or {}).get("pending") or {}).values()]
        if any(not h.get("done") for h in s10):
            fail("W1-18 is planned or running: Branch full by default waits for its pod (record-done first)")
        if any(j["kind"] == "w1_18" and j.get("status") == "complete" for h in s10 for j in h["jobs"]):
            fail("W1-18 completed: record its branch from its output (pass -> 128, fail -> full)")
        new = {"branch": "full", "source": "default", **ref, "reason": doc["reason"]}
    elif doc.get("kind") == RECORD_KINDS["branch"]:
        _need(doc, ("branch", "host", "output_path", "output_sha256", "focus_commit", "utc", "recorded_by"),
              "a W1-18 branch record")
        if doc["branch"] not in rules.BRANCHES:
            fail("the branch is 'full' or '128'")
        job = _host_job(plan, doc["host"], "w1_18", "S1-0")
        out = HERE / "retrieved" / doc["host"] / "tree" / doc["output_path"]
        if ".." in pathlib.PurePath(doc["output_path"]).parts or not out.is_file():
            fail(f"{doc['host']}: W1-18's output is not in the pulled tree")
        if mac.sha(out) != doc["output_sha256"] or (job.get("outputs") or {}).get(doc["output_path"]) != doc["output_sha256"]:
            fail("the branch record's output SHA-256 differs from the pulled W1-18 output")
        result = json.loads(out.read_text())
        check = result.get("truncation_check") if isinstance(result, dict) else None
        if result.get("kind") != W1_18_OUTPUT_KIND or not isinstance(check, dict) or check.get("units") != 11 or \
                type(check.get("pass")) is not bool:
            fail("the pulled W1-18 output is not a complete over-refusal checks record")
        if (doc["branch"] == "128") != check["pass"]:
            fail("the branch must follow W1-18's bar (pass -> 128; fail -> full)")
        new = {"branch": doc["branch"], "source": "w1_18", **ref, "host": doc["host"],
               "output_sha256": doc["output_sha256"], "focus_commit": doc["focus_commit"]}
    else:
        fail("not a W1-18 branch record or a 'Branch full by default' record")
    if old is not None:
        records(plan)["branch_history"].append(old)
    records(plan)["branch"] = {**new, "utc": mac.utc()}
    mac.save_plan(plan)
    mac.operator_action({"action": "record-branch", "branch": new["branch"], "source": new["source"],
                         "sha256": ref["sha256"]})
    return {"branch": new["branch"], "source": new["source"]}


def record_simple(name: str, path: str, sha256: str) -> dict:
    plan = load()
    doc, ref = file_record(path, sha256)
    rec = records(plan)
    if name == "gateb_final":
        if rec.get("gateb_final") is not None:
            fail("Gate B's final record is already recorded")
        result = doc.get("result")
        if ref["sha256"] != rules.GATEB_FINAL_SHA256 or any(doc.get(k) != v for k, v in
                                                            rules.GATEB_FINAL_FIELDS.items()) \
                or not isinstance(result, dict) or result.get("final") is not True or result.get("code") != "REPORTED":
            fail("not Gate B's measurements --final output (code REPORTED) pinned by rules.GATEB_FINAL_SHA256")
        rec["gateb_final"] = ref
    elif name == "plan_ab":
        if ref["sha256"] != rules.GATEB_VERDICT["sha256"]:
            fail("the plan-A/B record is derived from Gate B's verdict file only (rules.GATEB_VERDICT, "
                 f"{rules.GATEB_VERDICT['sha256'][:8]}...): another file or hash, or a typed record, refuses")
        try:
            sigma = rules.verdict_sigma(doc)
            code = rules.plan_code_for(sigma)
        except ValueError as exc:
            fail(str(exc))
        if rec.get("gateb_final") is None:
            fail("the plan-A/B record needs Gate B's final record first (record-gateb-final)")
        if rec.get("plan_ab") is not None:
            fail("the plan-A/B record is already recorded")
        rec["plan_ab"] = {**ref, "derived": True, "field": ".".join(rules.GATEB_VERDICT_FIELD), "sigma_pp": sigma,
                          "code": code, "rule": rules.PLAN_AB_RULE, "gateb_final_sha256": rec["gateb_final"]["sha256"],
                          "utc": mac.utc()}
    elif name in ("certificate", "certification"):
        kind, job_kind, block = (("certificate", "cert_c1", "cert") if name == "certificate"
                                 else ("certification", "b10_certify", "certify"))
        if doc.get("kind") != RECORD_KINDS[kind] or type(doc.get("pass")) is not bool:
            fail(f"not a {kind} record with a boolean pass")
        _need(doc, ("host", "utc", "recorded_by"), f"a {kind} record")
        job = _host_job(plan, doc["host"], job_kind, block)
        if name == "certification" and doc["pass"] and job.get("certification_gate") != "passed":
            fail("the certification pod's B10 gate is recorded failed (certification_gate): the certification "
                 "record's pass must be false (round 32, K3; LS-08)")
        _evidence(doc["host"], doc.get("evidence"))
        if rec.get(name) is not None:
            fail(f"the {kind} is already recorded")
        rec[name] = {**ref, "pass": doc["pass"], "host": doc["host"]}
    elif name == "thresholds":
        if doc.get("kind") != RECORD_KINDS["thresholds"]:
            fail("not a binding-check thresholds record")
        _need(doc, ("thresholds", "utc", "recorded_by"), "a thresholds record")
        if json.dumps(doc["thresholds"], sort_keys=True) != C2_THRESHOLDS_JSON:
            fail("the thresholds record must carry addendum §22 point 1 exactly (rules.C2_THRESHOLDS; write it with "
                 "write-thresholds)")
        if rec.get("thresholds") is not None:
            fail("the thresholds record is already recorded")
        rec["thresholds"] = ref
    elif name == "c3":
        if doc.get("kind") != RECORD_KINDS["c3"]:
            fail("not a C3 subsample pin record")
        _need(doc, ("subsample", "record", "utc", "recorded_by"), "a C3 subsample pin record")
        if rec.get("c3") is not None or rec.get("c3_fallback") is not None:
            fail("C3's subsample or its fallback is already recorded")
        rec["c3"] = {**ref, **c3_files(doc)}
    elif name == "c3_fallback":
        if doc.get("kind") != RECORD_KINDS["c3_fallback"] or doc.get("status") != "dropped":
            fail("not a C3 fallback record with status 'dropped'")
        _need(doc, ("reason", "utc", "recorded_by"), "a C3 fallback record")
        if rec.get("c3") is not None or rec.get("c3_fallback") is not None:
            fail("C3's subsample or its fallback is already recorded")
        if any(j["kind"] == "cert_c3" for j in planned_jobs(plan)):
            fail("C3 is already planned: its fallback is recorded before the certificate pod is planned")
        rec["c3_fallback"] = {**ref, "status": "dropped", "reason": doc["reason"]}
    elif name == "d2_fallback":
        jobs = doc.get("jobs")
        if doc.get("kind") != RECORD_KINDS["d2_fallback"] or not isinstance(jobs, list) or not jobs or \
                len(set(jobs)) != len(jobs) or not set(jobs) <= set(rules.D2_KINDS):
            fail(f"not a D-2 fallback record with jobs among {list(rules.D2_KINDS)}")
        _need(doc, ("reason", "utc", "recorded_by"), "a D-2 fallback record")
        if rec.get("d2_fallback") is not None:
            fail("the D-2 fallback is already recorded")
        if any(j["kind"] in jobs for j in planned_jobs(plan)):
            fail("a J5/J8 job is already planned: its D-2 route never changes")
        rec["d2_fallback"] = {**ref, "jobs": sorted(jobs), "reason": doc["reason"]}
    elif name == "prefix":
        if doc.get("kind") != RECORD_KINDS["prefix"] or not SHA_RE.fullmatch(str(doc.get("text_sha256"))):
            fail("not a prefix record with a 64-hex text_sha256")
        _need(doc, ("source", "utc", "recorded_by"), "a prefix record")
        rec["prefix"] = {**ref, "text_sha256": doc["text_sha256"], "source": doc["source"]}
    elif name == "user_yes":
        if doc.get("kind") != RECORD_KINDS["user_yes"] or doc.get("item") != "safe_lora_k12":
            fail("not a user-yes record for safe_lora_k12")
        _need(doc, ("user_words", "utc", "recorded_by"), "a user-yes record")
        rec["user_yes"][doc["item"]] = ref
    elif name == "oext_fallback":
        if doc.get("kind") != RECORD_KINDS["oext_fallback"] or doc.get("status") != rules.OEXT_FALLBACK_STATUS:
            fail(f"not an O-ext fallback record with status {rules.OEXT_FALLBACK_STATUS!r}")
        _need(doc, ("reason", "utc", "recorded_by"), "an O-ext fallback record")
        if rec.get("oext_fallback") is not None:
            fail("the O-ext fallback is already recorded")
        if bank500_planned(plan):
            fail("the O-ext route never changes once a 500-bank job is planned")
        rec["oext_fallback"] = {**ref, "status": doc["status"]}
    elif name == "guard_off":                    # (E) the user's decision (FOCUS 8d3d505): launch past the guard
        problem = rules.guard_off_problem(doc)
        if problem:
            fail(f"not the user's budget-guard-off decision record: {problem}")
        try:
            decided = dt.datetime.fromisoformat(doc["utc"].replace("Z", "+00:00"))
            if decided.utcoffset() != dt.timedelta(0):
                raise ValueError
        except ValueError:
            fail("the budget-guard-off record's utc is not a UTC time")
        if decided > dt.datetime.now(dt.timezone.utc):
            fail("the budget-guard-off record's utc is in the future")
        if rec.get("guard_off") is not None:
            fail("the budget guard is already recorded off")
        rec["guard_off"] = {**ref, "path": str(pathlib.Path(path).resolve()), "user_words": doc["user_words"],
                            "utc": doc["utc"], "recorded_by": doc["recorded_by"], "recorded_utc": mac.utc()}
    elif name == "sealed":
        edits = doc.get("edits")
        if doc.get("kind") != RECORD_KINDS["sealed"] or not isinstance(edits, list) or not edits:
            fail("not a sealed edit record")
        for e in edits:
            ok = (e.get("arm") in rules.ARM_DOSE and e["arm"] != "a0" and isinstance(e.get("path"), str)
                  and SHA_RE.fullmatch(str(e.get("sha256"))) and (e.get("draw") is None) == (e["arm"] != "R"))
            if not ok:
                fail("every sealed edit is {arm, path, sha256} (R with its draw)")
        if ref["sha256"] not in {r["sha256"] for r in rec["sealed"]}:
            rec["sealed"].append(ref)
    else:
        fail(f"unknown record {name}")
    mac.save_plan(plan)
    mac.operator_action({"action": f"record-{name}", "sha256": ref["sha256"]})
    if name == "plan_ab":
        return {"recorded": name, "sha256": ref["sha256"], "field": rec["plan_ab"]["field"],
                "sigma_pp": rec["plan_ab"]["sigma_pp"], "code": rec["plan_ab"]["code"]}
    return {"recorded": name, "sha256": ref["sha256"]}


def planned_jobs(plan: dict) -> list[dict]:
    """Every job planned so far: released hosts and every block's pending hosts."""
    jobs = [j for h in plan["hosts"].values() for j in h["jobs"]]
    return jobs + [j for b in plan["blocks"].values() for h in (b.get("pending") or {}).values() for j in h["jobs"]]


def c3_files(doc: dict) -> dict:
    """The lead's C3 pin (addendum §22 point 2): the subsample file (hashed only: it holds dev-bank text) and the
    writer's text-free record (read), each by SHA-256; the record must name that file and its bank, P's manifest, the
    development role, the dev source, 16 items and the verified writer's script and settings."""
    out, paths = {}, {}
    for key in ("subsample", "record"):
        e = doc.get(key)
        if not isinstance(e, dict) or not isinstance(e.get("path"), str) or not SHA_RE.fullmatch(str(e.get("sha256"))):
            fail(f"the C3 pin's {key} must be {{path, sha256}}")
        p = pathlib.Path(e["path"])
        p = p if p.is_absolute() else ROOT / p
        if not p.is_file() or mac.sha(p) != e["sha256"]:
            fail(f"the C3 {key} file is missing or differs from its SHA-256")
        out[key], paths[key] = {"path": e["path"], "sha256": e["sha256"]}, p
    if out["record"]["sha256"] != rules.C3_RECORD["sha256"] or \
            paths["record"].resolve() != (ROOT / rules.C3_RECORD["path"]).resolve():
        fail(f"the C3 record must be the writer's record at {rules.C3_RECORD['path']} "
             f"({rules.C3_RECORD['sha256'][:8]}...; rules.C3_RECORD)")
    try:
        rec = json.loads(paths["record"].read_text())
    except ValueError:
        fail("the C3 record is not JSON")
    sub, s = out["subsample"]["sha256"], (rec.get("subsample") if isinstance(rec, dict) else None) or {}
    src, draw, prepared = rec.get("source") or {}, rec.get("draw") or {}, rules.PREPARED_MANIFESTS[rules.PREPARED_NAME]
    ok = (rec.get("kind") == rules.C3_RECORD_KIND and type(rec.get("version")) is int and rec.get("version") == 1
          and rec.get("role") == "development" and s.get("file_sha256") == sub and s.get("bank") == f"subsample-{sub}"
          and type(s.get("items")) is int and s.get("items") == rules.C3_ITEMS
          and src.get("bank") == "dev" and src.get("manifest_sha256") == prepared
          and rec.get("prepared_manifest_sha256") == prepared
          and draw.get("script_sha256") == rules.C3_WRITER["script_sha256"]
          and draw.get("settings_sha256") == rules.C3_WRITER["settings_sha256"])
    if not ok:
        fail("the C3 record does not name this subsample file, P, the dev source, the development role, 16 items and "
             "the verified writer (write_c3_subsample.py and its settings)")
    return out


def write_thresholds(out: str, recorded_by: str) -> dict:
    """Write the C2 thresholds record (addendum §22 point 1, exactly rules.C2_THRESHOLDS); never over a file."""
    p = pathlib.Path(out)
    if p.exists() or p.is_symlink():
        fail(f"{p.name} exists: a record is never overwritten")
    if not recorded_by.strip():
        fail("--recorded-by is needed")
    body = json.dumps({"kind": RECORD_KINDS["thresholds"], "thresholds": rules.C2_THRESHOLDS, "utc": mac.utc(),
                       "recorded_by": recorded_by}, indent=1, sort_keys=True) + "\n"
    with p.open("x") as handle:
        handle.write(body)
    return {"path": str(p), "sha256": mac.sha(p)}


def c2_label(path: str, sha256: str) -> dict:
    """Label C2's steps.jsonl by the recorded thresholds, reading only constrained.mean_weight.t2_5 and the step of
    each record (rules.c2_reading, rules.c2_labels). The labels never change the arm (addendum §22 point 1)."""
    plan = load()
    t = records(plan).get("thresholds")
    if t is None:
        fail("the C2 thresholds record is not recorded (record-thresholds first)")
    doc, _ = file_record(t["path"], t["sha256"])
    if json.dumps(doc.get("thresholds"), sort_keys=True) != C2_THRESHOLDS_JSON:
        fail("the recorded thresholds file no longer carries addendum §22 point 1 exactly")
    p = pathlib.Path(path)
    if not p.is_file() or not SHA_RE.fullmatch(str(sha256)) or mac.sha(p) != sha256:
        fail(f"{p.name}: missing, or its SHA-256 differs from the one given")
    try:
        out = rules.c2_labels(rules.c2_reading(p.read_text().splitlines()))
    except ValueError as exc:
        fail(str(exc))
    return {**out, "steps_sha256": sha256, "thresholds_sha256": t["sha256"]}


def import_reference(path: str, sha256: str) -> dict:
    """§8 Q11: stage-1 arm pods compare with Gate B's environment reference (its plan.json "reference")."""
    plan = load()
    doc, ref = file_record(path, sha256)
    reference = doc.get("reference")
    if not isinstance(reference, dict) or not reference.get("fields"):
        fail("the file holds no environment reference")
    if plan.get("reference"):
        fail("the reference is already set")
    plan["reference"] = {**reference, "imported_from": ref}
    mac.save_plan(plan)
    mac.operator_action({"action": "import-reference", "sha256": ref["sha256"]})
    return {"reference": "gate-b", "sha256": ref["sha256"]}


# ----- complete attempts and re-runs -----------------------------------------------------------------------------


def job_key(job: dict) -> tuple:
    return (job["kind"], job.get("arm"), job.get("seed"), job.get("engine"), tuple(job.get("points") or ()),
            recipe_of(job), job.get("role"))


def complete_keys(plan: dict) -> dict:
    """job_key -> complete attempts: the jobs plan.json records complete, and the complete records of pulled
    JOB-DONE.json files of hosts not yet recorded."""
    found: dict = {}
    for host, h in plan["hosts"].items():
        for job in h["jobs"]:
            if job.get("status") == "complete":
                found.setdefault(job_key(job), []).append({"host": host, "unit": job.get("unit"),
                                                           "complete_sha256": job.get("complete_sha256"),
                                                           "path": None})
        done = HERE / "retrieved" / host / "tree" / "JOB-DONE.json"
        if not h.get("done") and done.is_file():
            records_ = {r.get("index"): r for r in json.loads(done.read_text()).get("jobs") or []}
            for i, job in enumerate(h["jobs"]):
                r = records_.get(i)
                if r and r.get("status") == "complete":
                    unit = HERE / "retrieved" / host / "tree" / r["unit"] if r.get("unit") else None
                    found.setdefault(job_key(job), []).append({"host": host, "unit": r.get("unit"),
                                                               "complete_sha256": r.get("complete_sha256"),
                                                               "path": str(unit) if unit else None})
    return found


def mismatch(plan: dict, attempt: dict) -> list[str]:
    """The compared fields in which a complete attempt's unit differs from the plan's reference (names only)."""
    if not plan.get("reference") or not attempt.get("path"):
        return []
    unit = pathlib.Path(attempt["path"])
    if not (unit / "assets.json").is_file():
        return []
    assets = json.loads((unit / "assets.json").read_text())
    lock = (assets.get("environment_lock") or {}).get("sha256")
    fields = mac.compared_fields(assets.get("environment") or {}, lock, assets.get("policy"))
    ref = plan["reference"]["fields"]
    return sorted(k for k in set(ref) | set(fields) if fields.get(k) != ref.get(k))


RERUN_MARKS = ("mismatched_complete_sha256", "stranded_complete_sha256")


def requeued_attempts(plan: dict) -> set:
    marked = {j.get(m) for h in plan["hosts"].values() for j in h["jobs"] for m in RERUN_MARKS}
    return {d for r in plan.get("requeues") or [] for d in r["complete_sha256"]} | (marked - {None})


def refuse_complete(plan: dict, jobs: list[dict], rerun: list[str], allow_stranded: set | None = None,
                    linked: set | None = None) -> list[dict]:
    """Refuse a job whose run is complete (PREREG's re-run rule: never re-run a completed job), unless
    --rerun-mismatched names an environment-mismatched attempt of it; returns the re-runs to record."""
    found, allowed, requeued = complete_keys(plan), [], requeued_attempts(plan)
    for job in jobs:
        attempts = [a for a in found.get(job_key(job), []) if not any(m in job for m in RERUN_MARKS)
                    or a["complete_sha256"] not in requeued]
        if linked and id(job) in linked:
            attempts = [a for a in attempts if a["complete_sha256"] != job["mismatched_complete_sha256"]]
        if not attempts or (allow_stranded and id(job) in allow_stranded):
            continue
        named = [a for a in attempts if a["complete_sha256"] in rerun]
        if named:
            fields = mismatch(plan, named[0])
            if fields:
                allowed.append({"kind": job["kind"], "arm": job.get("arm"), "seed": job.get("seed"),
                                "complete_sha256": named[0]["complete_sha256"], "host": named[0]["host"],
                                "mismatched_fields": fields})
                continue
            fail(f"{job.get('arm') or job['kind']} at {job.get('seed')}: the named attempt shows no environment "
                 "mismatch against the reference")
        fail(f"{job.get('arm') or job['kind']} at {job.get('seed')}: a complete attempt exists; it is never re-run")
    return allowed


def pay_reruns(plan: dict, reruns: list[dict], new_pod: bool, where: str, wave: str | None = None) -> list[dict]:
    """Pay each re-run from its funding group's contingency, in order; one it cannot pay is recorded "not re-run".
    ``wave`` is the host's block."""
    c = plan.get("contingency", {}).get(rules.FUNDING_BLOCK.get(wave)) if wave else None
    if c is None:
        return list(reruns)
    paid = []
    for job in reruns:
        cost = rules.rerun_cost_usd(job, new_pod and not paid)
        record = {"kind": job["kind"], "arm": job.get("arm"), "seed": job.get("seed"), "cost_usd": cost, "where": where}
        if cost <= c["remaining_usd"] + 1e-9:
            c["remaining_usd"] -= cost
            c["spent"].append(record)
            paid.append(job)
        else:
            c["not_rerun"].append(record)
            mac.operator_action({"action": "not-rerun", "reason": "contingency exhausted", **record,
                                 "remaining_usd": c["remaining_usd"]})
    return paid


def pay_unit(plan: dict, jobs: list[dict], new_pod: bool, where: str, wave: str | None = None) -> list[dict]:
    """A pre-job requeue's moved jobs paid as one unit (rules.unit_rerun_cost_usd); when the unit does not fit, one by
    one in order (pay_reruns). The two agree on which jobs are paid."""
    c = plan.get("contingency", {}).get(rules.FUNDING_BLOCK.get(wave)) if wave else None
    if c is None or not jobs:
        return pay_reruns(plan, jobs, new_pod, where, wave)
    cost = rules.unit_rerun_cost_usd(jobs, new_pod)
    if cost > c["remaining_usd"] + 1e-9:
        return pay_reruns(plan, jobs, new_pod, where, wave)
    c["remaining_usd"] -= cost
    c["spent"].append({"unit": [{"kind": j["kind"], "arm": j.get("arm"), "seed": j.get("seed")} for j in jobs],
                       "new_pod": new_pod, "cost_usd": cost, "where": where})
    return list(jobs)


def pay_user(plan: dict, jobs: list[dict], new_pod: bool, where: str, wave: str | None, payment: dict) -> list[dict]:
    """The user's recorded re-run payment (record-rerun-payment) pays ``jobs`` as one unit (rules.unit_rerun_cost_usd)
    beyond the funding group's contingency: the contingency's remaining_usd, spent and not_rerun are unchanged; the
    payment goes to its user_paid list and the operator log. It refuses when the unit's cost in cents ([D20]'s
    rounding) is above what the decision still covers (its amount_usd less its earlier payments): the user decides
    again. Nothing else is paid by it."""
    group = rules.FUNDING_BLOCK.get(wave)
    c = plan.get("contingency", {}).get(group)
    if c is None or group != payment["block"]:
        fail(f"{where}: the user's re-run payment is for block {payment['block']}'s funding group, not this host's")
    cost = rules.unit_rerun_cost_usd(jobs, new_pod)
    earlier = sum(p["cost_cents_usd"] for p in c.get("user_paid") or [] if p.get("decision_sha256") == payment["sha256"])
    left = round(payment["amount_usd"] - earlier, 2)
    if rules.cents(cost) > left + 1e-9:
        fail(f"{where}: the re-run unit costs ${rules.cents(cost):.2f} (the kit's figure), more than the ${left:.2f} the "
             "user's recorded payment still covers; the user decides again")
    record = {"unit": [{"kind": j["kind"], "arm": j.get("arm"), "seed": j.get("seed")} for j in jobs],
              "new_pod": new_pod, "cost_usd": cost, "cost_cents_usd": rules.cents(cost),
              "amount_usd": payment["amount_usd"], "where": where, "decision_sha256": payment["sha256"],
              "utc": mac.utc()}
    c.setdefault("user_paid", []).append(record)
    mac.operator_action({"action": "rerun-user-paid", **record, "contingency_remaining_usd": c["remaining_usd"]})
    return list(jobs)


def rerun_payment_problem(doc) -> str | None:
    """Why ``doc`` is not the user's re-run payment decision {kind, user_words (verbatim), block, jobs: [{arm, seed}],
    amount_usd, utc, recorded_by} (exactly these keys; each job exactly {arm: text, seed: integer}, distinct; the
    amount a finite number above 0; the texts non-empty), or None."""
    if not isinstance(doc, dict) or set(doc) != set(RERUN_PAYMENT_KEYS):
        return f"it must hold exactly {list(RERUN_PAYMENT_KEYS)}"
    if doc["kind"] != RECORD_KINDS["rerun_payment"]:
        return f"its kind is not {RECORD_KINDS['rerun_payment']!r}"
    if not all(isinstance(doc[k], str) and doc[k].strip() for k in ("user_words", "block", "utc", "recorded_by")):
        return "user_words (verbatim), block, utc and recorded_by must be non-empty texts"
    amount = doc["amount_usd"]
    if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not math.isfinite(amount) or amount <= 0:
        return "amount_usd must be a finite number above 0"
    jobs = doc["jobs"]
    if not isinstance(jobs, list) or not jobs or not all(
            isinstance(j, dict) and set(j) == {"arm", "seed"} and isinstance(j["arm"], str) and j["arm"].strip()
            and type(j["seed"]) is int for j in jobs) or len({(j["arm"], j["seed"]) for j in jobs}) != len(jobs):
        return "jobs must be a non-empty list of distinct {arm, seed} (arm a text, seed an integer)"
    return None


def record_rerun_payment(path: str, sha256: str) -> dict:
    """record-rerun-payment FILE --sha256 H: the user's decision {kind: "stage1 user decision: pay re-runs beyond the
    contingency", user_words (verbatim), block, jobs: [{arm, seed}], amount_usd, utc, recorded_by} that the balance
    pays the named re-runs beyond the funding group's contingency. block is a funding group with a contingency
    (block A's: "A"); each named job must be held by that contingency's not_rerun list (a re-run it could not pay) and
    paid by no earlier payment; the group's block is not sealed. A later decision naming a job that an earlier one
    named but did not pay supersedes it for that job (the user decides again, e.g. on a new amount; a recorded file is
    never edited). The file is re-hashed at every use. With it, requeue HOST moves the named jobs HOST holds and pays
    them, as one unit, from the decision (pay_user), and nothing else."""
    plan = load()
    doc, ref = file_record(path, sha256)
    problem = rerun_payment_problem(doc)
    if problem:
        fail(f"not the user's re-run payment decision: {problem}")
    _utc_past(doc["utc"], "the re-run payment decision")
    block = doc["block"]
    c = plan.get("contingency", {}).get(block)
    if block not in set(rules.FUNDING_BLOCK.values()) or c is None:
        fail(f"block {block!r} is not a funding group with a contingency in plan.json")
    if block in plan["seals"]:
        fail(f"block {block} is sealed: a re-run payment is recorded before its seal")
    held = [(e.get("arm"), e.get("seed")) for e in c.get("not_rerun") or []]
    paid = {(u.get("arm"), u.get("seed")) for p in c.get("user_paid") or [] for u in p["unit"]}
    rerun_payments_checked(plan)                  # the earlier decisions re-hashed (a later one supersedes, unpaid)
    for j in doc["jobs"]:
        key = (j["arm"], j["seed"])
        if key not in held:
            fail(f"{j['arm']} at {j['seed']}: not held by block {block}'s contingency as not re-run")
        if key in paid:
            fail(f"{j['arm']} at {j['seed']}: already paid by a recorded re-run payment")
    entry = {**ref, "path": str(pathlib.Path(path).resolve()), "block": block, "jobs": [dict(j) for j in doc["jobs"]],
             "amount_usd": doc["amount_usd"], "user_words": doc["user_words"], "utc": doc["utc"],
             "recorded_by": doc["recorded_by"], "recorded_utc": mac.utc()}
    records(plan).setdefault("rerun_payments", []).append(entry)
    mac.save_plan(plan)
    mac.operator_action({"action": "record-rerun-payment", "sha256": ref["sha256"], "block": block,
                         "jobs": entry["jobs"], "amount_usd": entry["amount_usd"]})
    return {"recorded": "rerun_payment", "sha256": ref["sha256"], "block": block, "jobs": entry["jobs"],
            "amount_usd": entry["amount_usd"]}


def rerun_payments_checked(plan: dict) -> list[dict]:
    """The recorded re-run payment decisions, each file re-hashed at its recorded path: it must be unchanged and hold
    the recorded block, jobs, amount and words."""
    out = []
    for e in (plan.get("records") or {}).get("rerun_payments") or []:
        p = pathlib.Path(str(e.get("path")))
        try:
            on_disk = json.loads(p.read_text()) if p.is_file() else None
        except ValueError:
            on_disk = None
        if not isinstance(on_disk, dict) or mac.sha(p) != e.get("sha256") or \
                any(on_disk.get(k) != e.get(k) for k in ("block", "jobs", "amount_usd", "user_words")):
            fail("a recorded re-run payment decision is missing or differs from its recorded SHA-256; it must stay at "
                 "its recorded path, unchanged")
        out.append(e)
    return out


def user_paid_held(plan: dict, host: str, h: dict) -> tuple[dict | None, list[int]]:
    """(the decision, the indices of HOST's jobs it pays): HOST's jobs that an earlier move of HOST left as not re-run
    (block's contingency not_rerun, where "requeue HOST" or "defer HOST"; the job still at a held status) and that a
    recorded re-run payment of HOST's funding group names (the latest decision naming it), not paid yet. One decision
    per requeue."""
    group = rules.FUNDING_BLOCK.get(h["block"])
    c = plan.get("contingency", {}).get(group) or {}
    held = {(e.get("arm"), e.get("seed")) for e in c.get("not_rerun") or []
            if e.get("where") in (f"requeue {host}", f"defer {host}")}
    paid = {(u.get("arm"), u.get("seed")) for p in c.get("user_paid") or [] for u in p["unit"]}
    latest: dict = {}
    for e in rerun_payments_checked(plan):
        if e["block"] == group:
            for j in e["jobs"]:
                latest[(j["arm"], j["seed"])] = e
    by_decision: dict = {}
    for key, e in latest.items():
        if key not in held or key in paid:
            continue
        idx = [i for i, job in enumerate(h["jobs"]) if (job.get("arm"), job.get("seed")) == key
               and job.get("status") in HELD_STATUSES]
        if len(idx) != 1:
            fail(f"{host}: {key[0]} at {key[1]} is held as not re-run but is not one held job of this host")
        by_decision.setdefault(e["sha256"], (e, []))[1].append(idx[0])
    if len(by_decision) >= 2:
        fail(f"{host}: two recorded re-run payments name jobs of this host; one decision per requeue (the lead decides)")
    if not by_decision:
        return None, []
    e, idx = next(iter(by_decision.values()))
    return e, sorted(idx)


def requeue_user_paid(plan: dict, host: str, h: dict, payment: dict, idx: list[int]) -> dict:
    """requeue HOST under the user's re-run payment: the named jobs HOST holds move, in order, to the next
    unlaunched host of the block with room or a new host (move_open: never a completed job again, at most 4 counted
    jobs), paid by the decision beyond the contingency (pay_user). A regeneration, O-only pass, retrain, re-score or
    W1-18 job is never moved this way (its linked partner and state stay where they ran): the lead decides."""
    for i in idx:
        kind = h["jobs"][i]["kind"]
        if kind in rules.LINKED_KINDS or kind in rules.LINK_SOURCES or kind == "w1_18":
            fail(f"{host}: job {i} ({kind}) is not re-run by a payment decision; the lead decides")
    return move_open(plan, host, h, idx, "requeue", "user-paid-rerun", payment=payment)


# ----- after a host: record-done, defer, requeue -----------------------------------------------------------------


def record_done(host: str) -> dict:
    plan = mac.load_plan()
    h = plan["hosts"].get(host) or fail(f"{host} is not a host of plan.json")
    path = HERE / "retrieved" / host / "tree" / "JOB-DONE.json"
    if not path.is_file():
        fail(f"{host}: no pulled JOB-DONE.json")
    done = json.loads(path.read_text())
    recs = {r["index"]: r for r in done.get("jobs") or []}
    if done.get("host") != host or sorted(recs) != list(range(len(h["jobs"]))):
        fail(f"{host}: JOB-DONE.json does not cover this host's jobs")
    tree = HERE / "retrieved" / host / "tree"
    decided = unpulled_decided(plan).get(host, {})       # §29 point 3: the lead's decisions, re-hashed here
    similarity = []                                      # kit round 34: B14's output, for the strata step
    for i, job in enumerate(h["jobs"]):
        r = recs[i]
        if (r["kind"], r.get("arm"), r.get("seed")) != (job["kind"], job["arm"], job["seed"]):
            fail(f"{host}: job {i} in JOB-DONE.json is another job")
        if r.get("engine") != job["engine"] or r.get("engine_sha256") != rules.ENGINES[job["engine"]]:
            fail(f"{host}: job {i}'s record does not name the engine it was planned on (G4)")
        if r["status"] not in ("complete", "crashed", "deferred", "not_started"):
            fail(f"{host}: job {i} has an unknown status")
        outputs = r.get("outputs") or {}
        states = 0
        for rel, digest in outputs.items():
            p = tree / rel
            if ".." in pathlib.PurePath(rel).parts:
                fail(f"{host}: job {i}'s output is missing from the pulled tree or differs")
            if rel.endswith(".safetensors") and not p.exists() and not p.is_symlink():
                states += 1                              # §29: the light pull leaves model states on the pod's volume
                continue
            if not p.is_file() or mac.sha(p) != digest:
                fail(f"{host}: job {i}'s output is missing from the pulled tree or differs")
        if i in decided:                                 # complete on the pod; its unit was not fetched (§29 point 3)
            unit_problem(tree, r, i, host)
        elif r["status"] == "complete" and r.get("complete_sha256"):
            complete = tree / r["unit"] / "COMPLETE.json"
            if not complete.is_file() or mac.sha(complete) != r["complete_sha256"]:
                fail(f"{host}: job {i}'s COMPLETE.json is missing from the pulled tree or differs" +
                     ("; if the light pull did not fetch its unit, record the lead's decision first (record-unpulled)"
                      if not complete.is_file() else ""))
        elif r["status"] == "complete" and not (job["kind"] in rules.UNITLESS_KINDS and outputs):
            fail(f"{host}: job {i} is complete without a complete_sha256 (or, for a unit-free job, its outputs)")
        if job["kind"] == "similarity" and r["status"] == "complete":   # kit round 34: the pass and its record
            problem = rules.similarity_record_problem(tree, r, host, ((plan.get("recipes") or {}).get(rules.REC) or {})
                                                      .get("config_sha256"))
            if problem:
                fail(f"{host}: job {i} (similarity): {problem}")
            out_rel = rules.similarity_output(i)
            similarity.append({"job": i, "path": (tree / out_rel).relative_to(ROOT).as_posix(),
                               "sha256": outputs[out_rel], "record_sha256": outputs[rules.similarity_record_path(i)]})
        units = b10_units(tree, r, i, host, i in decided) if job["kind"] in rules.B10_UNIT_KINDS and \
            r["status"] == "complete" and "units" in r else None
        gate = certification_gate_of(host, i, job, r, units, outputs)   # round 32 (K3): B10's gate, or None
        job.update(status=r["status"], unit=r.get("unit"), complete_sha256=r.get("complete_sha256"),
                   outputs=outputs or None, reason=r.get("reason"))
        if gate is not None:
            job["certification_gate"] = gate
        if units is not None:                            # round 30: every B10 unit, for the judge check (R3, R5)
            job["units"] = units
        if i in decided:
            job.update(pulled=False, unpulled_decision_sha256=decided[i])
        if states:
            job["states_on_pod"] = states
    h["done"], h["job_done_sha256"] = True, mac.sha(path)
    mac.save_plan(plan)
    not_pulled = sorted(decided)
    mac.operator_action({"action": "record-done", "host": host, "statuses": [j["status"] for j in h["jobs"]],
                         **({"not_pulled": not_pulled} if not_pulled else {})})
    out = {"host": host, "statuses": [j["status"] for j in h["jobs"]]}
    if similarity:                                       # kit round 34: the strata step's input, by path and SHA-256
        out["similarity"] = similarity
    return {**out, "not_pulled": not_pulled} if not_pulled else out


def certification_gate_of(host: str, i: int, job: dict, r: dict, units: list | None, outputs: dict) -> str | None:
    """Round 32 (K3, G11): B10's gate of a complete b10_certify job, as the runner records it (certification_gate
    "passed" or "failed"): its comparison file job-I/evals/<seed>-certify.compare.json is among the job's recorded
    outputs, and a failed gate leaves exactly the certify unit job-I/evals/<seed>-certify (B10 stops after a failed
    gate). A record without the gate (a runner before this round) refuses; no other job names one. None otherwise."""
    gate = r.get("certification_gate")
    if job["kind"] != "b10_certify" or r["status"] != "complete":
        if gate is not None:
            fail(f"{host}: job {i} names a certification gate; only a complete b10_certify job does")
        return None
    if gate not in rules.CERTIFICATION_GATES:
        fail(f"{host}: job {i} (b10_certify) is complete without B10's gate (certification_gate "
             f"{' or '.join(rules.CERTIFICATION_GATES)}: the job runner of kit round 32 records it; re-pack)")
    if f"job-{i}/evals/{job['seed']}-certify.compare.json" not in outputs:
        fail(f"{host}: job {i} (b10_certify): its certification comparison file is not among its recorded outputs")
    if gate == "failed" and [u["unit"] for u in units or []] != [f"job-{i}/evals/{job['seed']}-certify"]:
        fail(f"{host}: job {i} (b10_certify): a failed gate leaves the certify unit only (B10 stops after it)")
    return gate


def b10_units(tree: pathlib.Path, r: dict, i: int, host: str, unpulled: bool) -> list[dict]:
    """Round 30: JOB-DONE.json's list of a complete B10 job's units (one per evaluation point), kept in plan.json for
    the judge check (judge_required_units). Each names a plain path under the run folder and its COMPLETE.json
    SHA-256, and that COMPLETE.json is in the pulled tree with that SHA-256 (not checked for a job an unpulled
    outputs decision names); no unit twice."""
    units = r.get("units")
    if not isinstance(units, list) or not units:
        fail(f"{host}: job {i}'s units list in JOB-DONE.json is empty or not a list")
    out = []
    for u in units:
        rel, digest = (u.get("unit"), u.get("complete_sha256")) if isinstance(u, dict) else (None, None)
        if not (isinstance(rel, str) and rel and isinstance(digest, str) and SHA_RE.fullmatch(digest)) or \
                pathlib.PurePosixPath(rel).is_absolute() or ".." in pathlib.PurePosixPath(rel).parts:
            fail(f"{host}: job {i}'s units list names a unit without a plain path and a COMPLETE.json SHA-256")
        complete = tree / rel / "COMPLETE.json"
        if not unpulled and (not complete.is_file() or mac.sha(complete) != digest):
            fail(f"{host}: job {i}'s unit {rel} is missing from the pulled tree or its COMPLETE.json differs")
        out.append({"unit": rel, "complete_sha256": digest})
    if len({u["complete_sha256"] for u in out}) != len(out):
        fail(f"{host}: job {i}'s units list names one unit twice")
    return out


def unit_problem(tree: pathlib.Path, r: dict, i: int, host: str) -> None:
    """§29 point 3: a job an unpulled outputs decision names must be complete on the pod with a unit and its
    COMPLETE.json SHA-256 (JOB-DONE.json), and that unit's COMPLETE.json must be absent from the pulled tree."""
    unit = r.get("unit")
    if r.get("status") != "complete" or not isinstance(unit, str) or not unit or \
            not SHA_RE.fullmatch(str(r.get("complete_sha256"))):
        fail(f"{host}: job {i} is not a complete unit job in the pulled JOB-DONE.json; an unpulled outputs decision "
             "names only a complete job whose unit the pull did not fetch")
    if pathlib.PurePosixPath(unit).is_absolute() or ".." in pathlib.PurePosixPath(unit).parts:
        fail(f"{host}: job {i}'s unit is not a plain path under the run folder")
    if (tree / unit / "COMPLETE.json").exists():
        fail(f"{host}: job {i}'s unit is in the pulled tree; an unpulled outputs decision cannot name it")


def _utc_past(text, what: str) -> None:
    """A UTC time (offset zero) that is not in the future."""
    try:
        at = dt.datetime.fromisoformat(str(text).replace("Z", "+00:00"))
        if at.utcoffset() != dt.timedelta(0):
            raise ValueError
    except ValueError:
        fail(f"{what}'s utc is not a UTC time")
    if at > dt.datetime.now(dt.timezone.utc):
        fail(f"{what}'s utc is in the future")


def unpulled_problem(doc) -> str | None:
    """Why ``doc`` is not the lead's unpulled outputs decision {kind, host, jobs: [index, ...], reason, utc,
    recorded_by} (exactly these keys; distinct job indices; non-empty texts), or None."""
    if not isinstance(doc, dict) or set(doc) != set(UNPULLED_KEYS):
        return f"it must hold exactly {list(UNPULLED_KEYS)}"
    if doc["kind"] != RECORD_KINDS["unpulled"]:
        return f"its kind is not {RECORD_KINDS['unpulled']!r}"
    jobs = doc["jobs"]
    if not isinstance(jobs, list) or not jobs or not all(type(i) is int and i >= 0 for i in jobs) or \
            len(set(jobs)) != len(jobs):
        return "jobs must be a non-empty list of distinct job indices"
    if not all(isinstance(doc[k], str) and doc[k].strip() for k in ("host", "reason", "utc", "recorded_by")):
        return "host, reason, utc and recorded_by must be non-empty texts"
    return None


def record_unpulled(path: str, sha256: str) -> dict:
    """record-unpulled FILE --sha256 H (addendum §29 point 3): the lead's decision {kind: "stage1 unpulled outputs
    decision", host, jobs: [index, ...], reason, utc, recorded_by} for jobs of HOST that are complete on the pod (its
    pulled JOB-DONE.json: complete, with a unit and its COMPLETE.json SHA-256) whose unit the pull did not fetch (the
    unit's COMPLETE.json is absent from retrieved/HOST/tree). Recorded before record-done HOST and before the block's
    seal; a job is named by one decision only. The file is re-hashed at every use (record-done, block A's
    completeness, the seal): it must stay at its recorded path, unchanged. record-done then records those jobs
    complete with pulled false ("complete (not pulled)"), the seal lists them with no hashes, and block A's
    completeness counts them as decided by this record."""
    plan = load()
    doc, ref = file_record(path, sha256)
    problem = unpulled_problem(doc)
    if problem:
        fail(f"not the lead's unpulled outputs decision: {problem}")
    _utc_past(doc["utc"], "the unpulled outputs decision")
    host = doc["host"]
    h = plan["hosts"].get(host) or fail(f"{host} is not a host of plan.json")
    if h["block"] in plan["seals"]:
        fail(f"block {h['block']} is sealed: an unpulled outputs decision is recorded before its seal")
    if h.get("done"):
        fail(f"{host} is recorded done: an unpulled outputs decision is recorded before record-done {host}")
    taken = unpulled_decided(plan).get(host, {})
    if any(i in taken for i in doc["jobs"]):
        fail(f"{host}: a job is already named by a recorded unpulled outputs decision")
    done_path = HERE / "retrieved" / host / "tree" / "JOB-DONE.json"
    if not done_path.is_file():
        fail(f"{host}: no pulled JOB-DONE.json")
    done = json.loads(done_path.read_text())
    recs = {r.get("index"): r for r in done.get("jobs") or [] if isinstance(r, dict)}
    if done.get("host") != host:
        fail(f"{host}: JOB-DONE.json does not cover this host's jobs")
    for i in doc["jobs"]:
        if i >= len(h["jobs"]) or i not in recs:
            fail(f"{host}: job {i} is not a job of this host's JOB-DONE.json")
        job, r = h["jobs"][i], recs[i]
        if (r.get("kind"), r.get("arm"), r.get("seed")) != (job["kind"], job["arm"], job["seed"]):
            fail(f"{host}: job {i} in JOB-DONE.json is another job")
        unit_problem(HERE / "retrieved" / host / "tree", r, i, host)
    entry = {**ref, "path": str(pathlib.Path(path).resolve()), "host": host, "jobs": sorted(doc["jobs"]),
             "reason": doc["reason"], "utc": doc["utc"], "recorded_by": doc["recorded_by"], "recorded_utc": mac.utc()}
    records(plan).setdefault("unpulled", []).append(entry)
    mac.save_plan(plan)
    labels = [job_label(h["jobs"][i]["kind"], h["jobs"][i].get("arm"), h["jobs"][i].get("seed")) for i in entry["jobs"]]
    mac.operator_action({"action": "record-unpulled", "sha256": ref["sha256"], "host": host, "jobs": entry["jobs"]})
    return {"recorded": "unpulled", "sha256": ref["sha256"], "host": host, "jobs": entry["jobs"], "labels": labels}


def unpulled_decided(plan: dict) -> dict:
    """host -> {job index: the SHA-256 of the recorded unpulled outputs decision that names it}. Each decision file is
    re-hashed at every use: it must stay at its recorded path, unchanged, and hold the recorded host, jobs and
    reason."""
    out: dict = {}
    for e in (plan.get("records") or {}).get("unpulled") or []:
        p = pathlib.Path(str(e.get("path")))
        try:
            on_disk = json.loads(p.read_text()) if p.is_file() else None
        except ValueError:
            on_disk = None
        if not isinstance(on_disk, dict) or mac.sha(p) != e.get("sha256") or on_disk.get("host") != e.get("host") or \
                sorted(on_disk.get("jobs") or []) != e.get("jobs") or on_disk.get("reason") != e.get("reason"):
            fail("a recorded unpulled outputs decision is missing or differs from its recorded SHA-256; it must stay "
                 "at its recorded path, unchanged")
        for i in e["jobs"]:
            out.setdefault(e["host"], {})[i] = e["sha256"]
    return out


def not_pulled_jobs(plan: dict, block: str | None = None) -> list[dict]:
    """The jobs recorded "complete (not pulled)" (record-done under an unpulled outputs decision, re-hashed here),
    of one block or of all: {host, index, job (its label), unit, decision_sha256}; no file hash (the unit is not
    in the pulled tree)."""
    out = []
    for host, decided in sorted(unpulled_decided(plan).items()):
        h = plan["hosts"][host]
        if block is not None and h["block"] != block:
            continue
        for i, digest in sorted(decided.items()):
            j = h["jobs"][i]
            if h.get("done") and j.get("status") == "complete" and j.get("pulled") is False and \
                    j.get("unpulled_decision_sha256") == digest:
                out.append({"host": host, "index": i, "job": job_label(j["kind"], j.get("arm"), j.get("seed")),
                            "unit": j.get("unit"), "decision_sha256": digest})
    return out


def destination(plan: dict, host: str, wave: str, arms: int = 0, engine: str | None = None) -> str | None:
    """The next unlaunched host of the same block and engine that is not done and has room."""
    return next((name for name, d in plan["hosts"].items() if name != host and d["block"] == wave
                 and (engine is None or d["engine"] == engine) and not mac.launched(name) and not d.get("done")
                 and rules.arm_count(d["jobs"]) + arms <= rules.MAX_ARMS_PER_POD), None)


def too_many(host: str, moved: list[dict]) -> None:
    if rules.arm_count(moved) > rules.MAX_ARMS_PER_POD:
        fail(f"{host}: {rules.arm_count(moved)} counted jobs would move to one pod, more than "
             f"MAX_ARMS_PER_POD = {rules.MAX_ARMS_PER_POD}; the lead decides")


def packed_sealed(engine: str) -> tuple[dict, str]:
    """(the engine's current packed sealed-files.json, its sealed_files_sha256), checked against its receipt."""
    rec = engine_receipt(engine)
    path = HERE / "setup" / f"packed-stage1-{engine}" / "sealed-files.json"
    if not path.is_file() or mac.sha(path) != rec.get("sealed_files_sha256"):
        fail(f"the packed stage1-{engine}'s sealed-files.json is missing or is not its receipt's")
    return json.loads(path.read_text()), rec["sealed_files_sha256"]


def packed_input_sha(engine: str, name: str) -> tuple[str | None, str]:
    """(the SHA-256 the engine's current packed stage seals for the named input, or None; that stage's
    sealed_files_sha256), with sealed-files.json checked against its receipt."""
    doc, digest = packed_sealed(engine)
    rel = (doc.get("inputs") or {}).get(name)
    return (doc.get("files") or {}).get(rel) if rel else None, digest


def pin_s3_orig(plan: dict, host: str, h: dict, moving_idx: list[int], index_map: dict, moved: list[dict]) -> str | None:
    """(D, pod a-1) A J5 (rep_pass) that moves off a host whose earlier J6 (untuned_answers) stays there (complete,
    never re-run: PREREG) gets plan.json's pin of J6's s3_orig pool (rules.s3_orig_pin, from J6's own record), and the
    engine's current packed stage must hold the input pool:s3_orig at that pin (pack_setup.py X with it, before this
    defer). Returns that stage's sealed_files_sha256 (the moved jobs' pod is bound to it), or None when no J5 needs it."""
    jobs, bound = h["jobs"], None
    for i in moving_idx:
        earlier = [k for k in range(i) if jobs[k]["kind"] == "untuned_answers"]
        if jobs[i]["kind"] != "rep_pass" or not earlier or earlier[-1] in moving_idx:
            continue                                  # no J6 beside it, or J6 moves with it (same pod)
        try:
            pin = rules.s3_orig_pin(plan, HERE)
        except ValueError as exc:
            fail(f"{host}: J5 moves off J6's pod, so J6's s3_orig pool must be pinned from J6's record: {exc}")
        if (pin["host"], pin["index"]) != (host, earlier[-1]):
            fail(f"{host}: the complete J6 that plan.json records is not the one earlier on this host")
        packed, bound = packed_input_sha(h["engine"], rules.S3_ORIG_INPUT)
        if packed != pin["sha256"]:
            fail(f"{host}: the packed stage1-{h['engine']} holds no {rules.S3_ORIG_INPUT} at J6's pin: pack engine "
                 f"{h['engine']} with the input {rules.S3_ORIG_INPUT} (path {pin['pack_path']}, sha256 {pin['sha256']}) "
                 "before the defer")
        moved[index_map[i]]["s3_orig"] = {k: pin[k] for k in ("host", "index", "record", "pool", "sha256")}
    return bound


def place(plan: dict, h: dict, moved: list[dict], dest: str | None, role: str = "job",
          sealed_files_sha256: str | None = None) -> str:
    """``moved`` in order at the front of ``dest``, or on a new host of the block (cap, guard and spend from B4). A new
    host is bound to ``sealed_files_sha256`` when given (the current packed stage a moved job's input needs), else to
    the source host's packed stage."""
    if rules.arm_count(moved) + (rules.arm_count(plan["hosts"][dest]["jobs"]) if dest else 0) > rules.MAX_ARMS_PER_POD:
        fail(f"{h['block']}: a pod would hold more than {rules.MAX_ARMS_PER_POD} counted jobs; the lead decides")
    if dest is None:
        dest = new_host_name(plan, h["block"])
        plan["hosts"][dest] = host_record(plan, h["block"], role, moved, sealed_files_sha256 or h["sealed_files_sha256"],
                                          h["launch"])
        return dest
    if sealed_files_sha256 is not None and plan["hosts"][dest]["sealed_files_sha256"] != sealed_files_sha256:
        fail(f"{dest}: the destination is bound to another packed stage than the one the moved jobs' input needs")
    target = plan["hosts"][dest]
    target.setdefault("plan_shape", {"cap_hours": target["cap_hours"], "spend_upper_usd": target["spend_upper_usd"],
                                     "jobs": [{k: job.get(k) for k in ("kind", "arm", "seed", "engine", "points",
                                                                       "role")} for job in target["jobs"]]})
    for job in target["jobs"]:
        if job["kind"] in rules.LINKED_KINDS and job.get(rules.LINK_FIELD) is not None:
            job[rules.LINK_FIELD] += len(moved)
    target["jobs"] = moved + target["jobs"]
    target.update(cap_hours=rules.cap_hours(target["jobs"]), counted=rules.arm_count(target["jobs"]),
                  spend_upper_usd=rules.pod_spend_usd(target["jobs"]))
    target["guard_usd"] = rules.guard_usd(target["cap_hours"])
    return dest


def defer(host: str) -> dict:
    """Move a done host's crashed, deferred and not-started jobs (move_open; a crashed job is a re-run paid from its
    funding group's contingency). (D) For pod a-1 (J6 complete, J5 crashed, J7 and J8 not started): first pack engine
    X with the input pool:s3_orig at J6's record's pin (stage1_rules.s3_orig_pin), then defer: J5, J7 and J8 go in
    order to a new diagnostics host of block A bound to that pack, and J5 reads J6's pool by its pin."""
    plan = mac.load_plan()
    h = plan["hosts"].get(host) or fail(f"{host} is not a host of plan.json")
    if not h.get("done"):
        fail(f"{host}: record-done first")
    if any(d["from"] == host for d in plan["deferrals"]):
        fail(f"{host} was already deferred")
    decided = not_run_decided(plan, h["block"]) if h["block"] != "A" else {}   # round 32 (K2): they stay where they are
    moving_idx = [i for i, j in enumerate(h["jobs"]) if j["status"] in ("crashed", "deferred", "not_started")
                  and (host, i) not in decided]
    if not moving_idx:
        fail(f"{host}: nothing to defer")
    return move_open(plan, host, h, moving_idx, "defer")


def _strip(job: dict) -> dict:
    return {k: v for k, v in job.items() if k not in ("unit", "complete_sha256", "outputs", "reason")}


def move_open(plan: dict, host: str, h: dict, moving_idx: list[int], action: str, reason: str | None = None,
              payment: dict | None = None) -> dict:
    """``defer``'s move of the jobs at ``moving_idx``; ``requeue`` uses it for a pre-job stop. The stranded exception:
    when the first deferred job is an O-only pass whose regen_source names a complete regeneration, that regeneration
    is re-queued in front of it ("stranded-regenerate"); an O-only pass moved without its regeneration refuses.
    ``payment``: the user's recorded re-run payment (requeue_user_paid): every moved job is paid by it, as one unit,
    beyond the contingency (pay_user), never from the contingency."""
    jobs = h["jobs"]
    if h["block"] != "A" and any((host, i) in not_run_decided(plan, h["block"]) for i in moving_idx):
        fail(f"{host}: a job named by a not-run decision never moves (round 32, K2: the lead decided it does not run)")
    first_deferred = next((i for i in moving_idx if jobs[i]["status"] == "deferred"), None)
    stranded = None
    if first_deferred is not None and jobs[first_deferred]["kind"] in rules.LINKED_KINDS:
        source = jobs[first_deferred].get(rules.LINK_FIELD)
        if source is not None and jobs[source]["kind"] == rules.LINKED_KINDS[jobs[first_deferred]["kind"]] and \
                jobs[source]["status"] == "complete":
            stranded = source
    moved, index_map = [], {}
    for i in moving_idx:
        if i == first_deferred and stranded is not None:
            regen = _strip(jobs[stranded])
            regen.update(status="planned", reason="stranded-regenerate",
                         stranded_complete_sha256=jobs[stranded]["complete_sha256"], stranded_host=host)
            index_map[stranded] = len(moved)
            moved.append(regen)
        job = _strip(jobs[i])
        job["status"], job["deferred_from"] = "planned", host
        if job["kind"] in RECORDED_RECIPE and job.get("recipe") != RECORDED_RECIPE[job["kind"]]:
            job["recipe_was"], job["recipe"] = job.get("recipe"), RECORDED_RECIPE[job["kind"]]   # (G) an older record
            if rules.RECIPE_NAMES[job["recipe"]] not in plan["recipes"]:
                fail(f"{host}: recipe {job['recipe']} is not in plan.json's recipes (released hosts register it); the "
                     f"moved {job['kind']} job's pod checks it")
        index_map[i] = len(moved)
        moved.append(job)
    for job in moved:
        if job["kind"] in rules.LINKED_KINDS and job.get(rules.LINK_FIELD) is not None:
            if job[rules.LINK_FIELD] not in index_map:
                fail(f"{host}: an O-only pass would move without its regeneration (no state moves between pods)")
            job[rules.LINK_FIELD] = index_map[job[rules.LINK_FIELD]]
    stranded_ids = {id(moved[index_map[stranded]])} if stranded is not None else set()
    refuse_complete(plan, moved, [], stranded_ids)
    too_many(host, moved)
    bound = pin_s3_orig(plan, host, h, moving_idx, index_map, moved)
    dest = destination(plan, host, h["block"], rules.arm_count(moved), h["engine"])
    if payment is not None:                      # the user's decision pays these jobs beyond the contingency
        to_pay = list(moved)

        def payer(plan_, jobs_, new_pod, where, wave):
            return pay_user(plan_, jobs_, new_pod, where, wave, payment)
        for job in moved:
            job["rerun_payment_sha256"] = payment["sha256"]
    elif reason == "pre-job-failed":
        to_pay, payer = list(moved), pay_unit
    else:
        to_pay = [moved[index_map[i]] for i in moving_idx if jobs[i]["status"] == "crashed"]
        payer = pay_reruns
    paid = {id(j) for j in payer(plan, to_pay, dest is None, f"{action} {host}", h["block"])}
    dropped = {id(j) for j in to_pay if id(j) not in paid}
    if dropped:
        if any(j["kind"] in ("regenerate", "o_only", "w1_18", "retrain", "a1_rescore") for j in to_pay
               if id(j) in dropped):
            fail(f"{host}: the contingency cannot pay a W1-18, regeneration, O-only, retrain or re-score re-run; the "
                 "lead decides")
        moved = [j for j in moved if id(j) not in dropped]
        if not moved:
            entry = {"from": host, "to": None, "from_indices": moving_idx, "to_indices": [], "stranded": None,
                     "not_rerun": len(dropped), **({"reason": reason} if reason else {})}
            plan["deferrals"].append(entry)
            mac.save_plan(plan)
            mac.operator_action({"action": action, **entry})
            return {"from": host, "to": None, "jobs": 0, "not_rerun": len(dropped)}
    dest = place(plan, h, moved, dest, h["role"], bound)
    entry = {"from": host, "to": dest, "from_indices": moving_idx, "to_indices": list(range(len(moved))),
             "stranded": None if stranded is None else
             {"from_index": stranded, "complete_sha256": jobs[stranded]["complete_sha256"]},
             **({"reason": reason} if reason else {}),
             **({"rerun_payment_sha256": payment["sha256"]} if payment is not None else {})}
    plan["deferrals"].append(entry)
    mac.save_plan(plan)
    mac.operator_action({"action": action, **entry})
    if stranded is not None:
        mac.operator_action({"action": "stranded-regenerate", "from": host, "to": dest,
                             "complete_sha256": jobs[stranded]["complete_sha256"]})
    return {"from": host, "to": dest, "jobs": len(moved), "cap_hours": plan["hosts"][dest]["cap_hours"],
            "role": plan["hosts"][dest]["role"]}


def orchestrate_records(host: str) -> list[dict]:
    path = HERE / "hosts" / host / "orchestrate.jsonl"
    if not path.is_file():
        return []
    out = []
    for k, line in enumerate(path.read_text().splitlines()):
        try:
            record = json.loads(line)
            record["event"]
        except (ValueError, KeyError, TypeError):
            fail(f"{host}: orchestrate.jsonl line {k + 1} is unreadable")
        out.append(record)
    return out


def orchestrate_events(host: str) -> list[str]:
    return [r["event"] for r in orchestrate_records(host)]


def operator_records() -> list[dict]:
    if not mac.OPERATOR_LOG.is_file():
        return []
    out = []
    for k, line in enumerate(mac.OPERATOR_LOG.read_text().splitlines()):
        try:
            record = json.loads(line)
            record["action"]
        except (ValueError, KeyError, TypeError):
            fail(f"operator-actions.jsonl line {k + 1} is unreadable")
        out.append(record)
    return out


def _exit_zero(record: dict) -> bool:
    return type(record.get("exit")) is int and record["exit"] == 0


def stop_evidence(host: str, recs: list[dict]) -> dict:
    """How the pod's stop is known before a pre-job requeue: the log (a failure before start-job and a later
    pre-job-stop with exit 0, no job-start-unknown) or the operator's confirm-stopped record of the log as it is."""
    failed = [k for k, r in enumerate(recs) if r["event"] == "pre-job-failed"]
    if failed and "job-start-unknown" not in (r["event"] for r in recs):
        last = recs[failed[-1]]
        if isinstance(last.get("step"), str) and last["step"] != "start-job" and \
                any(r["event"] == "pre-job-stop" and _exit_zero(r) for r in recs[failed[-1] + 1:]):
            return {"by": "log"}
    digest = mac.sha(HERE / "hosts" / host / "orchestrate.jsonl")
    confirmed = [r for r in operator_records() if r["action"] == "confirm-stopped" and r.get("host") == host
                 and r.get("orchestrate_sha256") == digest]
    if confirmed:
        return {"by": "operator", "pod_latest_sha256": confirmed[-1].get("pod_latest_sha256")}
    fail(f"{host}: the pod's stop is not confirmed by the log: check its status with host.py get {host}, then "
         f"plan_tool.py confirm-stopped {host}")


def confirm_stopped(host: str) -> dict:
    """The operator's record that ``host.py get HOST`` read desiredStatus EXITED after the log's last record."""
    plan = mac.load_plan()
    if host not in plan["hosts"]:
        fail(f"{host} is not a host of plan.json")
    recs = orchestrate_records(host)
    events = [r["event"] for r in recs]
    if "job-started" in events:
        fail(f"{host}: its job started; record-done and defer it")
    if "pre-job-failed" not in events and "job-start-unknown" not in events:
        fail(f"{host}: no logged pre-job failure in hosts/{host}/orchestrate.jsonl")
    latest_path = HERE / "hosts" / host / "pod-latest.json"
    if not latest_path.is_file():
        fail(f"{host}: no pod status read (host.py get {host})")
    latest = json.loads(latest_path.read_text())
    if latest.get("desiredStatus") != "EXITED":
        fail(f"{host}: the pod's status is not EXITED; stop it (host.py stop {host}) and read it again")
    try:
        read_at = dt.datetime.fromisoformat(str(latest.get("utc")).replace("Z", "+00:00"))
        last_at = dt.datetime.fromisoformat(str(recs[-1].get("utc")).replace("Z", "+00:00"))
        if read_at.utcoffset() is None or last_at.utcoffset() is None:
            raise ValueError
    except ValueError:
        fail(f"{host}: the pod status read or the last log record has no readable UTC time")
    if read_at < last_at:
        fail(f"{host}: the pod status was read before the last orchestrate record; read it again (host.py get {host})")
    mac.operator_action({"action": "confirm-stopped", "host": host, "desiredStatus": "EXITED",
                         "pod_read_utc": latest["utc"], "pod_latest_sha256": mac.sha(latest_path),
                         "orchestrate_sha256": mac.sha(HERE / "hosts" / host / "orchestrate.jsonl")})
    return {"host": host, "confirmed": True}


def requeue(host: str, rerun: list[str] | None = None) -> dict:
    """A pre-job stop (no flag) or environment-mismatched complete attempts (--rerun-mismatched SHA ...). A stopped
    kit pod is never restarted: the jobs go to its replacement. With the user's recorded re-run payment
    (record-rerun-payment) naming jobs an earlier move of HOST held as not re-run, requeue HOST moves exactly those
    jobs and pays them beyond the contingency (requeue_user_paid); without one, nothing changes."""
    plan = mac.load_plan()
    h = plan["hosts"].get(host) or fail(f"{host} is not a host of plan.json")
    if rerun:
        return requeue_mismatched(plan, host, h, rerun)
    payment, held = user_paid_held(plan, host, h)
    if payment is not None:
        return requeue_user_paid(plan, host, h, payment, held)
    recs = orchestrate_records(host)
    events = [r["event"] for r in recs]
    if h.get("done") or (HERE / "retrieved" / host / "tree" / "JOB-DONE.json").exists() or "job-started" in events:
        fail(f"{host}: its job started (a JOB-DONE.json or a logged job-started): record-done and defer it")
    if "pre-job-failed" not in events and "job-start-unknown" not in events:
        fail(f"{host}: no logged pre-job failure in hosts/{host}/orchestrate.jsonl")
    if any(d["from"] == host for d in plan["deferrals"]):
        fail(f"{host} was already deferred")
    if any(j.get("status") != "planned" for j in h["jobs"]):
        fail(f"{host}: a job has a recorded status; only a host whose job never started is requeued")
    stop = stop_evidence(host, recs)
    for job in h["jobs"]:
        job["status"] = "not_started"
    h["pre_job_failed"] = {"orchestrate_sha256": mac.sha(HERE / "hosts" / host / "orchestrate.jsonl"), "stop": stop}
    return move_open(plan, host, h, list(range(len(h["jobs"]))), "requeue", "pre-job-failed")


def requeue_mismatched(plan: dict, host: str, h: dict, rerun: list[str]) -> dict:
    """Queue again each complete job of HOST whose COMPLETE.json SHA-256 is named and whose unit differs from the
    reference; a named regeneration or O-only pass brings its linked partner; paid from the contingency."""
    if not h.get("done"):
        fail(f"{host}: record-done first")
    if len(set(rerun)) != len(rerun):
        fail(f"{host}: --rerun-mismatched names one hash more than once")
    earlier = requeued_attempts(plan)
    picked, partners = [], set()
    for digest in rerun:
        if digest in earlier:
            fail(f"{host}: that attempt was already re-queued")
        found = [i for i, j in enumerate(h["jobs"]) if j.get("status") == "complete" and j.get("complete_sha256") == digest]
        if not found:
            fail(f"{host}: --rerun-mismatched names no complete job of this host")
        i = found[0]
        picked.append(i)
        jobs = h["jobs"]
        pair = (jobs[i].get(rules.LINK_FIELD), i) if jobs[i]["kind"] in rules.LINKED_KINDS else \
            (i, rules.linked_follower(jobs, i)) if jobs[i]["kind"] in rules.LINK_SOURCES else None
        if pair and None not in pair:
            if any(jobs[k].get("status") != "complete" for k in pair):
                fail(f"{host}: a regeneration and its O-only pass are re-queued together; both must be complete")
            partners.update(pair)
    named = set(picked)
    picked = sorted(named | partners)
    moved, index_map = [], {}
    for i in picked:
        job = _strip(h["jobs"][i])
        job.update(status="planned", deferred_from=host, reason="environment-mismatch",
                   mismatched_complete_sha256=h["jobs"][i]["complete_sha256"])
        if i not in named:
            job["linked_rerun"] = True
        index_map[i] = len(moved)
        moved.append(job)
    for job in moved:
        if job["kind"] in rules.LINKED_KINDS and job.get(rules.LINK_FIELD) is not None:
            job[rules.LINK_FIELD] = index_map[job[rules.LINK_FIELD]]
    reruns = refuse_complete(plan, moved, rerun, linked={id(moved[index_map[k]]) for k in partners - named})
    too_many(host, moved)
    dest = destination(plan, host, h["block"], rules.arm_count(moved), h["engine"])
    kept = pay_reruns(plan, moved, dest is None, f"requeue {host}", h["block"])
    dest = place(plan, h, kept, dest, h["role"]) if kept else None
    entry = {"from": host, "to": dest, "reason": "environment-mismatch", "from_indices": picked,
             "to_indices": list(range(len(kept))), "complete_sha256": [h["jobs"][i]["complete_sha256"] for i in picked],
             "not_rerun": len(moved) - len(kept)}
    plan.setdefault("requeues", []).append(entry)
    mac.save_plan(plan)
    for record in reruns:
        mac.operator_action({"action": "rerun-mismatched", "where": f"requeue {host}", **record})
    mac.operator_action({"action": "requeue", **entry})
    return {"from": host, "to": dest, "jobs": len(kept), "not_rerun": entry["not_rerun"]}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="plan_tool.py")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init-block")
    p.add_argument("block")
    p.add_argument("--jobs", required=True)
    p.add_argument("--funding")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--group-jobs", action="append", metavar="PART=FILE")   # round 32 (K4): block B's whole group
    sub.add_parser("release").add_argument("block")
    d = sub.add_parser("deal")
    d.add_argument("block")
    d.add_argument("--reuse", nargs=2, action="append", type=lambda v: int(v) if v.isdigit() else v)
    for name in ("record-done", "defer", "confirm-stopped"):
        sub.add_parser(name).add_argument("host")
    q = sub.add_parser("requeue")
    q.add_argument("host")
    q.add_argument("--rerun-mismatched", action="extend", nargs="+")
    simple = {"record-gateb-final": "gateb_final", "record-plan-ab": "plan_ab", "record-certificate": "certificate",
              "record-certification": "certification", "record-thresholds": "thresholds", "record-prefix": "prefix",
              "record-user-yes": "user_yes", "record-sealed": "sealed", "record-oext-fallback": "oext_fallback",
              "record-c3": "c3", "record-c3-fallback": "c3_fallback", "record-d2-fallback": "d2_fallback",
              "record-guard-off": "guard_off"}
    wb = sub.add_parser("write-block-a-plan")
    wb.add_argument("--out", required=True)
    wb.add_argument("--recorded-by", required=True)
    wb.add_argument("--split")
    bn = sub.add_parser("block-a-need")
    bn.add_argument("file", nargs="?")
    bn.add_argument("--sha256")
    wt = sub.add_parser("write-thresholds")
    wt.add_argument("--out", required=True)
    wt.add_argument("--recorded-by", required=True)
    for name in ("record-branch", "import-reference", "c2-label", "record-block-a-plan", "record-block-a-replan",
                 "record-block-a-not-run", "record-unpulled", "record-rerun-payment", "record-judge-not-run",
                 "record-not-run", *simple):
        r = sub.add_parser(name)
        r.add_argument("file")
        r.add_argument("--sha256", required=True)
    rj = sub.add_parser("record-judges")                 # round 30 (R2): the block's judge-completion record
    rj.add_argument("block")
    rj.add_argument("file")
    rj.add_argument("--sha256", required=True)
    a = ap.parse_args(argv)
    if a.command in simple:
        out = record_simple(simple[a.command], a.file, a.sha256)
    else:
        out = {"init-block": lambda: init_block(a), "release": lambda: release(a.block),
               "deal": lambda: deal_command(a.block, a.reuse), "record-done": lambda: record_done(a.host),
               "defer": lambda: defer(a.host), "requeue": lambda: requeue(a.host, a.rerun_mismatched),
               "confirm-stopped": lambda: confirm_stopped(a.host),
               "record-branch": lambda: record_branch(a.file, a.sha256),
               "import-reference": lambda: import_reference(a.file, a.sha256),
               "write-thresholds": lambda: write_thresholds(a.out, a.recorded_by),
               "c2-label": lambda: c2_label(a.file, a.sha256),
               "write-block-a-plan": lambda: write_block_a_plan(a.out, a.recorded_by, a.split),
               "record-block-a-plan": lambda: record_block_a_plan(a.file, a.sha256),
               "record-block-a-replan": lambda: record_block_a_plan(a.file, a.sha256, replan=True),
               "record-block-a-not-run": lambda: record_block_a_not_run(a.file, a.sha256),
               "record-unpulled": lambda: record_unpulled(a.file, a.sha256),
               "record-rerun-payment": lambda: record_rerun_payment(a.file, a.sha256),
               "record-judges": lambda: record_judges(a.block, a.file, a.sha256),
               "record-judge-not-run": lambda: record_judge_not_run(a.file, a.sha256),
               "record-not-run": lambda: record_not_run(a.file, a.sha256),
               "block-a-need": lambda: block_a_need(a.file, a.sha256)}[a.command]()
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
