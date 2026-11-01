"""The measured cost per arm under C-full and C-lean, from the kit's readable cost ledgers (REV4 7.3, 10.1-10.4;
report only). Exit 0: the file written; 2: refused, nothing written.

    python -m scripts.stage1_s1.reading_extra.cost_table --kit tmp/stage1-olmo --reading plan_a --out cost.json

When: it opens plan.json, the reading's block seals and only the cost ledgers the seals class readable (REV4:158 lets
a block's cost ledgers be read after it), never an outcome file. A run's stage split (its -oext step: the greedy
over-refusal answers) tracks answer lengths, and refusals are short, so the per-run seconds carry a weak outcome
signal: run it inside the reading, or do not open its output before the reading (the lead's call).

REV4 = research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md (frozen). The rules:
- REV4:103: the headline's first item is each repair's label "with its over-refusal, task loss and measured cost";
  REV4:774: each actor menu reports every arm "with its label, O, L and cost under both conventions".
- REV4:158: "After block A, only its cost ledgers, completion records and adapter fingerprints are read."
- REV4:632: "1 FRE = 2,934 s (the median job slot of the three wave-0a R arms; about $1.46 at $1.79/h), fixed at W1-P
  and never re-estimated; the median of all stage-1 R arms is reported beside it (LW-16)."
- REV4:633: "C-full (LW-16; REF LQ26): every in-job stage (load, tokenize, edit, training, the task-loss pass, greedy
  generation of all evaluation prompts, sampled generation, ARC, Qwen3Guard on greedy and sampled answers, the
  secondary harm scores, verification). Out, reported apart: pod overhead, the HarmBench and Granite judge pods,
  backups and storage. The unit is 1 FRE." REV4:634 (LN-33): C-full holds the 868 greedy answers after O-ext.
- REV4:635-637: "C-lean (LW-15): training, 200 harm prompts × 1 sample, the task-loss pass, and the greedy
  over-refusal answers with their guard ... The unit is the measured c0." "Lean prices are frozen at W1-P from the
  three wave-0a ledgers (LW-16)." "c0 = one real job: a cold start, full R-arm training, exactly the C-lean evaluation".
  REV4:815: the c0 job "is a cost-measurement job ...; only its ledger is read".
- REV4:794-796: "Every arm and diagnostic is logged in GPU-seconds by stage"; "Every pool filter, untuned-answer
  generation, anchor job and scorer is charged in full; "≈ 0" only below 0.01 FRE. A1 is priced only from the wave-0b
  ledger."
- REV4:813: "C-full: §7.3. For an evaluation-only reference: the same minus training, plus its transform." Read
  literally for the ref_eval points (adapter scaling 0.9, 0.75, 0.5 and the prefix, SP; reading K8): "the same" is
  the C-full cost of the full run the reference is built on, the a0 run at the same seed (the kit runs each ref_eval
  job on block B's own a0 run at its seed: runkit/stage1-olmo/plan_tool.py K1, stage1_rules SECOND_PHASE_KINDS), so a
  point's C-full cost = that a0 run's measured slot - the frozen C-full training price (FULL_TRAINING_S, 219.7 s:
  selector_spec.json cost_conventions C-full training_s, the median training of R_1-R_3 at REV4:804-806) + the job
  ledger's measured transform stage, over 2,934 s; a per-reference mean over seeds is printed (b10_per_reference).
  "null: not stated" (K5) is printed beside each value as the alternative reading. REV4:774 needs the value: every
  menu arm is reported "with its label, O, L and cost under both conventions".
- REV4:816 (LS-13; LN-27): "a reference is charged what a practitioner who already has a0 pays on top of it; a0's
  regeneration is a study cost, reported apart; each scorer that uses the shared representation pass is charged the
  whole pass, with the shared split as a second number; ... A1's stages are named from the w0b-2 ledger (the
  diagnostics took 3.04 h against a frozen upper of 2.0 h; the retrain 0.077 h)."
- REV4:819-830 (§10.4, "Reference costs under both conventions", E): "| One evaluation-only state | 0.93 FRE | 0.75 c0
  |" (:825); "| a0 adapter regeneration, per seed | 0.094 FRE (0.077 h measured) | 0.32 c0 | $0.14 (3 seeds $0.41);
  a study cost |" (:823); "The c0 column is in the dev-100 form" (:830).

Which ledgers: each kit job writes job-I/cost-ledger.json (runkit/stage1-olmo/setup/job_runner_stage1.py write_ledger:
the stages setup, training, greedy_generation, sampled_generation, judging, scoring, pod_overhead and transform in
seconds, the steps, and the job slot), the block seal classes every file named *cost-ledger*.json "readable"
(runkit/stage1-olmo/seal.py READABLE_PATTERNS), and record-done copies its SHA-256 into the job's plan.json outputs.
This reader opens plan.json and the seals of the reading's blocks (through the builder's Kit, imported and never
edited) and, for each job of a done host, only job-I/cost-ledger.json, and only when the seal lists it as readable at
the SHA-256 plan.json records; it never opens a file the seal classes sealed and never lists a folder. READINGS gives
each reading of the rules and its alternative (K1-K8). The charging block names the split's denominator (the reading's
arms only: the representation pass also serves DataShield-style, REQ-12, which is not charged here) and Gate B's anchor
job (REV4:796; outside the kit, not priced here). Printed on stdout: the file and its SHA-256 only.
"""

from __future__ import annotations

import statistics

from scripts.stage1_s1.reading.settings import Refusal, design
from scripts.stage1_s1.reading_extra import common
from scripts.stage1_s1.reading_input.build import READING_BLOCKS
from scripts.stage1_s1.reading_input.sources import Kit, read_bytes, sha256_bytes, strict_json

KIND = "stage1 reading cost per arm"
LEDGER_KIND = "stage1 cost ledger"                       # job_runner_stage1.write_ledger
LEDGER_FILE = "cost-ledger.json"                         # job_runner_stage1.LEDGER_FILE
LEDGER_STAGES = ("setup", "training", "greedy_generation", "sampled_generation", "judging", "scoring",
                 "pod_overhead", "transform")             # job_runner_stage1.LEDGER_STAGES
FRE_S = 2934.0                                           # REV4:632, :810 (stage1_rules.FRE_S)
APPROX_ZERO_FRE = 0.01                                   # REV4:796: '"≈ 0" only below 0.01 FRE'
C0_ESTIMATE_S = 2400.0                                   # REV4:638 (E): the c0 estimate with the 500-prompt bank
LEAN_TRAINING_S = 220.0                                  # REV4:636: the frozen lean price of training (W1-P, from the
#                                                          three wave-0a ledgers): scripts/stage1/settings/
#                                                          selector_spec.json cost_conventions C-lean variants a
FULL_TRAINING_S = 219.7                                  # REV4:813's "minus training" under C-full: the frozen C-full
#                                                          training price, selector_spec.json cost_conventions C-full
#                                                          training_s = the median training of R_1-R_3 (REV4:804-806:
#                                                          220.4, 219.7, 216.0 s)
REF_EVAL_MENU = {"scale:0.9": "adapter scaling 0.9", "scale:0.75": "adapter scaling 0.75",
                 "scale:0.5": "adapter scaling 0.5", "prefix": "SP (the system prompt prefix)"}   # REV4:770's names
A1_W0B2 = {"diagnostics_s": 3.04 * 3600.0, "retrain_s": 0.077 * 3600.0,
           "source": "REV4:816 (R: w0b-2's ledger, FOCUS 16 Oct 13:21 UTC): the diagnostics took 3.04 h against a "
                     "frozen upper of 2.0 h; the retrain 0.077 h; the whole diagnostics job (the attributes step and "
                     "both Gate C scripts), so an upper for A1's scoring (stage1_rules RESCORE_MEASURED_S)"}
REUSED_SEEDS = {"a0": (1101, 1102, 1103), "R": (1101, 1102, 1103)}   # REV4:124-125: Gate A and wave-0a units
RUN_KINDS = ("arm", "a0_arm", "ref_train")
EVAL_ONLY_KINDS = ("ref_eval", "safe_lora")              # B10 references: evaluation-only states (reading K6)
REF_TRAIN = {"G": "ref-G", "bqi": "ref-bqi"}             # build.REF_TRAIN, the kit's round-31 labels
# reading K3: the kit's diagnostic jobs each primary arm uses (REV4:127, :130-131, :155: "REQ-3 and REQ-10 for L1;
# REQ-9 for S3 and S4"; the kit's J5 rep_pass = REQ-3's representation pass with S3's pools, J6 untuned_answers =
# REQ-9, J7 l1_scan = REQ-10; job_runner_stage1's job table). A1's scoring is Gate B's w0b-2 job (outside the kit).
CHARGES = {"L1": ("l1_scan", "rep_pass"), "S3": ("untuned_answers", "rep_pass"), "S4": ("untuned_answers",)}
SPLIT_DENOMINATOR = ("the reading's arms that use the job (L1 and S3 share rep_pass; S3 and S4 share untuned_answers), "
                     "in equal shares. The representation pass also serves DataShield-style (REQ-12, a stage-1c "
                     "secondary arm), a reproduction of Gate C's representation score (scripts/stage1/"
                     "representation_pass.py's docstring) and stage 1b's plant and decoy pools (the kit's D-2 route), "
                     "none of them a stage-1 arm, so they are not in the denominator and each stage-1 share is an "
                     "upper (reading K3)")
ANCHOR_JOB = {"what": "Gate B's anchor job (host anchor-1, launched 2026-10-10 13:29 UTC, done 14:01 UTC: the untuned "
                      "model's greedy answers to the 128 sealed PKU anchor prompts, kept 64 harmful + 64 safe; the "
                      "sealed anchor bank anchor_bank.json 2cf96336...)",
              "serves": "A1's bi-anchored score and L1's layer scan on the 64 harmful anchor prompts (REV4:62, :127)",
              "charged_here": None,
              "why": "REV4:796 charges every anchor job in full; it ran in Gate B, before stage 1 and outside this "
                     "kit, so no stage-1 ledger holds it and this table does not price it: the lead prices it from "
                     "Gate B's record (the job took 2.2 min; pod overhead 26.0 min on anchor-1, REV4:808) beside A1's "
                     "w0b-2 charge",
              "sources": "REV4:62, :127, :796, :808; docs/study-plan-full.md:211, :250; research/FOCUS.md:198-199 "
                         "(at commit 55d5f8b)"}
MAC_NOTE = ("no kit diagnostic job: its selection ran on the Mac (CPU), which no ledger measures, so it is printed as "
            "0 GPU-seconds (REV4:794 logs GPU-seconds; reading K3)")
K5_NULL = {"seconds": None, "c_full_fre": None,
           "why": "not stated: one -b10-run step holds every point and a0's regeneration, so no per-point C-full "
                  "cost is measured (reading K5, the alternative to K8)"}
OVER_C0_NOTE = ("C-full's unit is 1 FRE (REV4:633), so c_full_fre is the C-full value; seconds_over_c0 is the same "
                "seconds over the measured c0 (the lead's 1 Nov ruling says 'over c0'), for a comparison with the "
                "C-lean column only")
BY_KIND_BASIS = ("reading K2: the measured seconds / the measured c0 (a diagnostic, scorer, study cost or the c0 job: "
                 "work the convention does not change); the B10 references are priced in b10_references (K6)")
RULE = [
    "REV4:103: each repair labelled ... with its over-refusal, task loss and measured cost; REV4:774: report every arm "
    "in the menu with its label, O, L and cost under both conventions.",
    "REV4:632: 1 FRE = 2,934 s (the median job slot of the three wave-0a R arms), fixed at W1-P and never "
    "re-estimated; the median of all stage-1 R arms is reported beside it (LW-16).",
    "REV4:633-634: C-full: every in-job stage; out, reported apart: pod overhead, the HarmBench and Granite judge "
    "pods, backups and storage; the unit is 1 FRE; C-full holds the 868 greedy answers after O-ext.",
    "REV4:635-637: C-lean: training, 200 harm prompts x 1 sample, the task-loss pass, and the greedy over-refusal "
    "answers with their guard; the unit is the measured c0; lean prices are frozen at W1-P; c0 = one real job: a cold "
    "start, full R-arm training, exactly the C-lean evaluation.",
    "REV4:794-796: every arm and diagnostic is logged in GPU-seconds by stage; every pool filter, untuned-answer "
    "generation, anchor job and scorer is charged in full; \"≈ 0\" only below 0.01 FRE; A1 is priced only from "
    "the wave-0b ledger.",
    "REV4:774: at each tau_O and tau_L, report every arm in the menu with its label, O, L and cost under both "
    "conventions (the Sp and Ow menus hold SP, adapter scaling, Safe LoRA, recipe G, B+Qi, REV4:770-771).",
    "REV4:813: C-full: for an evaluation-only reference: the same minus training, plus its transform.",
    "REV4:816 (LS-13; LN-27): a reference is charged what a practitioner who already has a0 pays on top of it; a0's "
    "regeneration is a study cost, reported apart; each scorer that uses the shared representation pass is charged the "
    "whole pass, with the shared split as a second number; A1's stages are named from the w0b-2 ledger.",
    "REV4:819-830 (10.4, E): reference costs under both conventions; one evaluation-only state 0.93 FRE and 0.75 c0 "
    "(the c0 column in the dev-100 form); a0's regeneration per seed 0.094 FRE and 0.32 c0, a study cost."]
READINGS = {
    "K1": "A run's C-full cost is its job slot (slot_s: start to end inside the pod, every in-job stage, the O-ext "
          "pass included) / 2,934 s, the definition FRE itself uses (a job slot); pod overhead is per pod and is not "
          "in a job's ledger. The stage split (stages_s) is printed beside it. Alternative: the sum of the stages.",
    "K2": "Under C-lean a full run (an arm, a0, or a reference trained by another recipe) is one lean job, so it costs "
          "1 c0 by the convention's definition (the frozen selector spec's C-lean unit is its own lean job); c0 is "
          "measured once (the c0 job's slot) and no run's own lean job ran, so a run's C-lean cost is not measured "
          "per run. Recipe G's and B+Qi's training differ from R's (REV4:827 prices B+Qi at 6.7-6.9 c0 for 6 seeds "
          "in the dev-100 form, E), and the readable ledger cannot separate a run's training from its evaluation "
          "(one -calibrate step), so their 1 c0 leaves that training difference out (E: a few per cent at the "
          "500-prompt form; c_lean_note). Every other job whose work does not change with the convention (the "
          "diagnostics, the scorers and the study costs: regenerations, O-only passes, the transfer report, the "
          "certification jobs, b10_certify among them) costs its measured seconds / the measured c0, as REV4:823 "
          "converts a0's regeneration (0.077 h: 0.094 FRE and 0.32 c0). The B10 references: K6. Alternative: the "
          "frozen lean price (about 2,386 s) / the measured c0 for every run.",
    "K3": "Diagnostics are charged by CHARGES (L1: l1_scan and rep_pass; S3: untuned_answers and rep_pass; S4: "
          "untuned_answers; A1: Gate B's w0b-2 diagnostics, 3.04 h, outside the kit) to the reading's arms only; a "
          "job shared by two of the reading's arms is charged whole to each, with the split (equal shares among the "
          "reading's arms that use it) as the second number (LS-13's rule for the representation pass, applied to "
          "the untuned answers too). The split's denominator is the reading's arms only: the representation pass "
          "also serves DataShield-style (REQ-12, a stage-1c secondary arm, not a stage-1 arm), Gate C's reproduction "
          "and stage 1b's plant and decoy pools, none charged here, so each share is an upper (charging."
          "split_denominator). A job no arm of the reading uses (rep_pass under plan B) is printed by kind only. An "
          "arm one of whose kinds has no complete job with a ledger gets no charge (null, with the reason), never 0. "
          "H1, S1, R and a0 have no kit diagnostic. Mac work (REQ-7, REQ-11's scoring, the S-pool, the length sort) "
          "has no ledger: H1's and S1's diagnostic prints 0 GPU-seconds with that note. REV4:796's anchor job (Gate "
          "B's anchor-1 job, which made A1's and L1's anchor bank) is named in charging.anchor_job and not priced "
          "here: it is outside the kit, like A1's w0b-2 job. Alternative: the lead's own map.",
    "K4": "The reused a0 and R units at 1101-1103 ran in Gate A and wave 0a: their runs are not in the stage-1 "
          "ledgers, so an arm's run cost is the mean over its seeds in the kit; their regenerations and O-only passes "
          "are study costs, reported apart. Alternative: wave 0a's ledgers for R (REV4 10.2's table).",
    "K5": "References: ref_train runs (recipe G, B+Qi) are runs like an arm's; a B10 job (ref_eval, safe_lora) is "
          "printed whole and, where its steps name a point (Safe LoRA's transform and evaluate steps), per point under "
          "C-full from the measured steps; Safe LoRA's -b10-regenerate step (a0's regeneration) is the study cost "
          "reported apart. ref_eval's one -b10-run step holds every point and a0's regeneration, so its C-full cost "
          "is measured whole only (includes_a0_regeneration); each ref_eval point's C-full cost is K8's (REV4:813), "
          "and this reading's 'null: not stated' is printed beside it (alternative_k5) as the alternative. "
          "Alternative: an equal split of the whole over its points.",
    "K6": "Under C-lean a B10 reference state is evaluation-only: REV4:813's rule for an evaluation-only reference "
          "(the same minus training, plus its transform) applied to C-lean's lean job, as REV4 10.4 prices it (:825, "
          "one evaluation-only state 0.75 c0 in the dev-100 form = (15 + 635) / 870 s at the frozen lean prices). A "
          "B10 job runs the full evaluation (eval_adapter.py: the engine's evaluation, then O-ext), so its measured "
          "seconds are C-full work, and no lean evaluation-only job ran. One lean state = the measured c0 less the "
          "frozen lean training price (LEAN_TRAINING_S, 220 s: REV4:636; selector_spec.json C-lean variant a), so it "
          "holds the measured lean evaluation at the run's own O cap; a point's C-lean cost = one lean state + its "
          "transform's measured seconds (Safe LoRA's -transform-P step; ref_eval's scaling and prefix transforms run "
          "inside its one step and are not added: about 0). A Safe LoRA job's whole C-lean cost = its slot with each "
          "-evaluate-P step replaced by one lean state; ref_eval's whole is not split (one step), so its C-lean cost "
          "is per point only. The B10 kinds are not in diagnostics_by_kind. Alternatives: REV4 10.4's form, the "
          "frozen lean evaluation price (15 + 2,151.2 = 2,166.2 s at the full cap) over the measured c0 (it "
          "overstates under Branch 128's cap, and a c0 below 2,166.2 s would price one state above a whole lean "
          "run); or no C-lean value for B10 (null).",
    "K7": "REV4:632's median of all stage-1 R arms = the median job slot (seconds and FRE) of the complete stage-1 R "
          "runs with a ledger in the reading's blocks (the reused R units at 1101-1103 ran in wave 0a); report only, "
          "beside the fixed 1 FRE, which it never re-estimates. A stage-1 slot holds the 400 PHTest answers (LN-33), "
          "so it exceeds the wave-0a basis by design. Alternative: the median slot without the -oext step (wave 0a's "
          "468 prompts).",
    "K8": "REV4:813 read literally for the ref_eval points (adapter scaling 0.9, 0.75, 0.5 and the prefix, SP; "
          "REV4:774 needs their cost under both conventions): 'the same' is the C-full cost of the full run the "
          "reference is built on, the a0 run at the same seed (the kit runs each ref_eval job on block B's own a0 run "
          "at its seed: plan_tool K1, stage1_rules SECOND_PHASE_KINDS), so a point's C-full cost = the matched a0 "
          "run's measured slot (K1: start to end inside the pod, the O-ext pass included, as the point's own "
          "evaluation holds it) - the frozen C-full training price (FULL_TRAINING_S, 219.7 s: selector_spec.json "
          "C-full training_s, the median training of R_1-R_3, REV4:804-806; not the lean 220 s) + the job ledger's "
          "measured transform stage (the runner records a transform stage only for Safe LoRA, so a ref_eval ledger's "
          "is 0: its scalar on the adapter weights and its prompt prefix run inside the one -b10-run step), over "
          "2,934 s (c_full_fre; the same seconds over the measured c0 beside it, OVER_C0_NOTE). The a0 run is named "
          "(c_full_basis.a0_run); a seed with no complete a0 run with a ledger in the reading's blocks gets null with "
          "the reason. b10_per_reference prints, per B10 kind and point, the mean (min, max) over the jobs' seeds of "
          "c_full_fre and c_lean_c0, listing a seed without a value; two complete jobs at one seed refuse. Safe "
          "LoRA's points keep their measured per-point C-full (K5). Alternatives: K5's null (printed beside it as "
          "alternative_k5); an equal split of the ref_eval slot over its points (it includes a0's regeneration, a "
          "study cost); the same seed's measured Safe LoRA -evaluate-P step as the price of one full "
          "evaluation-only state."}


def _num(value, what: str) -> float:
    v = common.number(value, what)
    if v < 0:
        raise Refusal(f"{what} is negative")
    return v


class Ledgers:
    """Every job of the reading's blocks with its readable cost ledger (module doc)."""

    def __init__(self, kit: Kit, blocks: tuple):
        self.kit, self.jobs = kit, []
        for block in blocks:
            seal = kit.seal(block)
            classes = {(f.get("host"), f.get("path")): f.get("class") for f in seal.doc["files"]}
            for host, h in kit.hosts(block):
                for i, job in enumerate(h["jobs"]):
                    if not isinstance(job, dict):
                        raise Refusal(f"{host} job {i}: plan.json's job record is not an object")
                    self.jobs.append(self._one(block, host, i, job, seal, classes))

    def _one(self, block, host, i, job, seal, classes) -> dict:
        rel = f"job-{i}/{LEDGER_FILE}"
        base = {"block": block, "host": host, "index": i, "kind": job.get("kind"), "arm": job.get("arm"),
                "seed": job.get("seed"), "status": job.get("status"), "pulled": job.get("pulled") is not False,
                "points": job.get("points")}
        digest = seal.files.get((host, rel))
        named = (job.get("outputs") or {}).get(rel) if isinstance(job.get("outputs"), dict) else None
        if digest is None:
            if job.get("status") == "complete" and job.get("pulled") is not False:
                raise Refusal(f"{host} job {i}: a complete, pulled job whose cost ledger is not in block {block}'s seal")
            return {**base, "ledger": None, "why": "no cost ledger in the seal (job status "
                                                   f"{str(job.get('status'))[:20]}, pulled {base['pulled']})"}
        if classes.get((host, rel)) != "readable":
            raise Refusal(f"{host} job {i}: block {block}'s seal does not class its cost ledger readable; it is not opened")
        if named is not None and named != digest:
            raise Refusal(f"{host} job {i}: plan.json and block {block}'s seal name two SHA-256 for its cost ledger")
        data = read_bytes(self.kit.root / "retrieved" / host / "tree" / rel, f"{host} {rel}")
        if sha256_bytes(data) != digest:
            raise Refusal(f"{host} {rel} hashes to {sha256_bytes(data)[:16]}, the seal lists {digest[:16]}")
        doc = strict_json(data)
        if not isinstance(doc, dict) or doc.get("kind") != LEDGER_KIND or doc.get("version") != 1:
            raise Refusal(f"{host} {rel} is not a version-1 {LEDGER_KIND!r}")
        same = {"host": host, "index": i, "job_kind": job.get("kind"), "arm": job.get("arm"), "seed": job.get("seed")}
        wrong = sorted(k for k, v in same.items() if doc.get(k) != v)
        if wrong:
            raise Refusal(f"{host} {rel}: its {', '.join(wrong)} differ from plan.json's job")
        stages = doc.get("stages_s")
        if not isinstance(stages, dict) or tuple(sorted(stages)) != tuple(sorted(LEDGER_STAGES)):
            raise Refusal(f"{host} {rel}: its stages are not the runner's {len(LEDGER_STAGES)} stages")
        steps = doc.get("steps")
        if not isinstance(steps, list) or not all(isinstance(s, dict) and isinstance(s.get("name"), str)
                                                  for s in steps):
            raise Refusal(f"{host} {rel}: its steps are not named")
        slot = _num(doc.get("slot_s"), f"{host} {rel}: slot_s")
        return {**base, "ledger": {"sha256": digest, "named_by_plan_outputs": named is not None, "slot_s": slot,
                                   "stages_s": {k: _num(v, f"{host} {rel}: {k}") for k, v in sorted(stages.items())},
                                   "steps": [{"name": s["name"], "seconds": _num(s.get("seconds", 0.0),
                                                                                 f"{host} {rel}: a step")}
                                             for s in steps]},
                "c_full_fre": slot / FRE_S}

    def of(self, kind: str, arm=None) -> list:
        return [j for j in self.jobs if j["kind"] == kind and j["ledger"] is not None and j["status"] == "complete"
                and (arm is None or j["arm"] == arm)]


def _c0(ledgers: Ledgers) -> dict:
    jobs = ledgers.of("c0")
    lean = {"lean_training_s": LEAN_TRAINING_S, "lean_state_rule": "reading K6: one evaluation-only state under C-lean "
            "= the measured c0 less the frozen lean training price"}
    if len(jobs) != 1:
        return {"measured_s": None, "estimate_s": C0_ESTIMATE_S, **lean, "lean_state_s": None,
                "why": f"{len(jobs)} complete c0 job(s) with a ledger in the reading's blocks; the unit needs one"}
    j = jobs[0]
    slot = j["ledger"]["slot_s"]
    state = slot - LEAN_TRAINING_S
    return {"measured_s": slot, "estimate_s": C0_ESTIMATE_S, "c_full_fre": j["c_full_fre"],
            "host": j["host"], "index": j["index"],
            "rule": "c0 = the c0 job's slot (a cold start, full R-arm training, exactly the C-lean evaluation)",
            **lean, "lean_state_s": state if state > 0 else None,
            **({} if state > 0 else {"lean_state_why": "the measured c0 is not above the frozen lean training price"})}


def _money(seconds: float, c0_s: float | None) -> dict:
    fre = seconds / FRE_S
    return {"seconds": seconds, "c_full_fre": fre, "c_lean_c0": None if c0_s is None else seconds / c0_s,
            "approximately_zero": fre < APPROX_ZERO_FRE}


def _priced(full_s, lean_s, c0_s) -> dict:
    """A B10 amount: C-full from its measured seconds (None: not separable), C-lean from its lean-priced seconds
    (reading K6; None without a lean state)."""
    return {"seconds": full_s, "c_full_fre": None if full_s is None else full_s / FRE_S,
            "c_lean_seconds": lean_s, "c_lean_c0": None if lean_s is None or c0_s is None else lean_s / c0_s,
            "approximately_zero": None if full_s is None else full_s / FRE_S < APPROX_ZERO_FRE}


def _runs(jobs: list) -> dict:
    by_seed = {}
    for j in jobs:
        key = str(j["seed"])
        if key in by_seed:
            raise Refusal(f"{j['arm']} at {key}: two complete runs with a ledger")
        by_seed[key] = {"host": j["host"], "index": j["index"], "slot_s": j["ledger"]["slot_s"],
                        "c_full_fre": j["c_full_fre"], "stages_s": j["ledger"]["stages_s"]}
    return dict(sorted(by_seed.items()))


def _arm_record(name: str, runs: dict, missing: list, diag: dict | None, c0_s, note: str | None = None) -> dict:
    fre = [r["c_full_fre"] for r in runs.values()]
    run = {"seeds": len(fre), "c_full_fre_mean": statistics.fmean(fre) if fre else None,
           "c_full_fre_min": min(fre) if fre else None, "c_full_fre_max": max(fre) if fre else None,
           "c_lean_c0": 1.0 if c0_s is not None else None}
    if note is not None:
        run["c_lean_note"] = note
    rec = {"runs": runs, "run": run, "seeds_not_in_kit": missing}
    if diag is not None:
        rec["diagnostic"] = diag
        if run["c_full_fre_mean"] is not None:
            rec["total"] = {part: None if diag[part] is None else
                            {"c_full_fre": run["c_full_fre_mean"] + diag[part]["c_full_fre"],
                             "c_lean_c0": None if c0_s is None else 1.0 + diag[part]["c_lean_c0"]}
                            for part in ("whole", "split")}
    return rec


def _diagnostics(ledgers: Ledgers, c0_s, arms: tuple) -> tuple:
    """(totals by kind, the per-arm charge {arm: {whole, split, kinds}}) under readings K2 and K3, for the reading's
    arms; every job kind but the runs and the B10 references, and every kind a reading's arm is charged."""
    used_by = {arm: used for arm, used in CHARGES.items() if arm in arms}
    kinds = sorted({j["kind"] for j in ledgers.jobs if j["ledger"] is not None and isinstance(j["kind"], str)
                    and j["kind"] not in RUN_KINDS and j["kind"] not in EVAL_ONLY_KINDS}
                   | {k for used in used_by.values() for k in used})
    totals = {}
    for k in kinds:
        done = ledgers.of(k)
        totals[k] = ({**_money(sum(j["ledger"]["slot_s"] for j in done), c0_s), "jobs": len(done),
                      "c_lean_basis": BY_KIND_BASIS} if done else
                     {"seconds": None, "c_full_fre": None, "c_lean_c0": None, "approximately_zero": None, "jobs": 0,
                      "why": "no complete job with a cost ledger in the reading's blocks"})
    users = {}
    for arm, used in used_by.items():
        for kind in used:
            users.setdefault(kind, []).append(arm)
    charge = {}
    for arm, used in used_by.items():
        kinds_rec = {k: {"jobs": totals[k]["jobs"], "shared_with": users[k]} for k in used}
        absent = [k for k in used if totals[k]["seconds"] is None]
        if absent:
            charge[arm] = {"whole": None, "split": None, "kinds": kinds_rec,
                           "why": f"no complete {', '.join(absent)} job with a cost ledger in the reading's blocks"}
            continue
        whole = sum(totals[k]["seconds"] for k in used)
        split = sum(totals[k]["seconds"] / len(users[k]) for k in used)
        charge[arm] = {"whole": _money(whole, c0_s), "split": _money(split, c0_s), "kinds": kinds_rec}
    a1 = A1_W0B2["diagnostics_s"]
    charge["A1"] = {"whole": _money(a1, c0_s), "split": _money(a1, c0_s), "kinds": {"w0b-2 diagnostics": {}},
                    "retrain_s_reported_apart": A1_W0B2["retrain_s"], "source": A1_W0B2["source"]}
    return totals, charge


def _ref_eval_point(a0: dict | None, seed, transform_s: float, lean_s, c0_s) -> dict:
    """One ref_eval point (adapter scaling or the prefix): C-full by REV4:813 read literally (reading K8) = the matched
    a0 run's slot on the same seed - the frozen C-full training price + the job ledger's measured transform stage;
    C-lean one lean state (K6); K5's "null: not stated" beside it."""
    basis = {"rule": "REV4:813 (reading K8): the matched a0 run's measured slot on the same seed - the frozen C-full "
                     "training price + the measured transform",
             "a0_run": None if a0 is None else {"seed": seed, "host": a0["host"], "index": a0["index"],
                                                "slot_s": a0["slot_s"]},
             "full_training_s": FULL_TRAINING_S, "transform_s": transform_s,
             "transform_basis": "the job ledger's transform stage (job_runner_stage1.write_ledger records one for "
                                "Safe LoRA only; a ref_eval point's scaling or prefix runs inside the one -b10-run "
                                "step, so it is 0 here)"}
    full = None if a0 is None else a0["slot_s"] - FULL_TRAINING_S + transform_s
    if a0 is None:
        basis["why"] = f"no complete a0 run with a cost ledger at seed {seed} in the reading's blocks"
    elif full < 0:
        basis["why"], full = "the a0 run's slot is below the frozen C-full training price", None
    else:
        basis["seconds_over_c0"] = None if c0_s is None else full / c0_s
        basis["units"] = OVER_C0_NOTE
    return {**_priced(full, lean_s, c0_s), "c_full_basis": basis, "alternative_k5": dict(K5_NULL)}


def _per_reference(b10: dict) -> dict:
    """Reading K8's per-reference mean over seeds: per B10 kind and point, the mean (min, max) over the jobs' seeds
    of the point's c_full_fre and c_lean_c0; a seed without a value is listed, not averaged; two complete jobs at one
    seed refuse."""
    rows: dict = {}
    for key, rec in b10.items():
        kind = key.split(" ", 1)[0]
        for p, point in rec["per_point"].items():
            seeds = rows.setdefault(kind, {}).setdefault(p, {})
            if str(rec["seed"]) in seeds:
                raise Refusal(f"{kind} at {rec['seed']}: two complete jobs with a ledger")
            seeds[str(rec["seed"])] = point
    out = {}
    for kind, points in sorted(rows.items()):
        out[kind] = {}
        for p, seeds in sorted(points.items()):
            rec = {"menu_name": REF_EVAL_MENU.get(p, f"Safe LoRA {p}" if kind == "safe_lora" else p),
                   "seeds": sorted(seeds), "jobs": len(seeds)}
            for name in ("c_full_fre", "c_lean_c0"):
                have = {s: v[name] for s, v in seeds.items() if v[name] is not None}
                rec[f"{name}_mean"] = statistics.fmean(have.values()) if have else None
                rec[f"{name}_min"] = min(have.values()) if have else None
                rec[f"{name}_max"] = max(have.values()) if have else None
                rec[f"seeds_without_{name}"] = sorted(s for s in seeds if s not in have)
            out[kind][p] = rec
    return out


def _b10(ledgers: Ledgers, c0_s, lean_s, a0_runs: dict) -> dict:
    """Each B10 reference job: C-full measured (whole; per point where its steps name the point; a ref_eval point by
    REV4:813 from the matched a0 run, reading K8), C-lean priced by reading K6 from one lean state (lean_s: the
    measured c0 less the frozen lean training price)."""
    out = {}
    for kind in EVAL_ONLY_KINDS:
        for j in ledgers.of(kind):
            slot, steps, points = j["ledger"]["slot_s"], j["ledger"]["steps"], list(j["points"] or [])
            where = f"{j['host']} job {j['index']} ({kind})"
            rec = {"points": j["points"], "seed": j["seed"]}
            if kind == "safe_lora":
                per, evaluated = {}, 0.0
                for p in points:
                    transform = [x["seconds"] for x in steps if x["name"].endswith(f"-transform-{p}")]
                    evaluate = [x["seconds"] for x in steps if x["name"].endswith(f"-evaluate-{p}")]
                    if len(transform) != 1 or len(evaluate) != 1:
                        raise Refusal(f"{where}: its ledger does not name one transform and one evaluate step of each "
                                      "point")
                    evaluated += evaluate[0]
                    per[p] = _priced(transform[0] + evaluate[0], None if lean_s is None else transform[0] + lean_s,
                                     c0_s)
                rest = slot - evaluated
                whole_lean = None if lean_s is None or rest < 0 else rest + len(points) * lean_s
                rec.update(_priced(slot, whole_lean, c0_s), per_point=per, per_point_c_full_why=None,
                           c_lean_why=None if whole_lean is not None else (
                               "no measured c0" if c0_s is None else "no lean state (units.c0)" if lean_s is None
                               else "its evaluate steps exceed its slot"),
                           includes_a0_regeneration=True)
                rec["a0_regeneration_reported_apart"] = _money(
                    sum(x["seconds"] for x in steps if x["name"].endswith("-b10-regenerate")), c0_s)
            else:
                a0 = a0_runs.get(str(j["seed"]))
                transform = j["ledger"]["stages_s"]["transform"]
                rec.update(_priced(slot, None, c0_s),
                           per_point={p: _ref_eval_point(a0, j["seed"], transform, lean_s, c0_s) for p in points},
                           per_point_c_full_why="reading K8: REV4:813 from the matched a0 run on the same seed "
                                                "(c_full_basis); reading K5's null beside it (alternative_k5)",
                           c_lean_why="reading K6: one -b10-run step holds a0's regeneration and every point's full "
                                      "evaluation, so its whole is not re-priced; per point only",
                           includes_a0_regeneration=True, a0_regeneration_reported_apart=None)
            out[f"{kind} {j['host']} job {j['index']}"] = rec
    return out


def _fre_beside(r_runs: dict) -> dict:
    """Reading K7: the median job slot of the stage-1 R runs, beside the fixed 1 FRE (report only)."""
    slots = [r["slot_s"] for r in r_runs.values()]
    median = statistics.median(slots) if slots else None
    return {"rule": "REV4:632: the median of all stage-1 R arms is reported beside it (LW-16)",
            "report_only": "1 FRE stays 2,934 s: fixed at W1-P and never re-estimated (REV4:632, :810)",
            "r_runs": len(slots), "median_slot_s": median,
            "median_slot_fre": None if median is None else median / FRE_S}


def table(kit_root, reading: str) -> dict:
    """The whole output (module doc)."""
    dsg = design(reading)
    kit = Kit(kit_root)
    blocks = READING_BLOCKS[reading]
    ledgers = Ledgers(kit, blocks)
    c0 = _c0(ledgers)
    c0_s = c0["measured_s"]
    totals, charge = _diagnostics(ledgers, c0_s, dsg.arms)
    arms = {}
    for arm in dsg.arms:
        runs = _runs(ledgers.of("a0_arm" if arm == "a0" else "arm", arm))
        missing = [{"seed": j, "why": ("reused (Gate A / wave 0a): not in the stage-1 ledgers"
                                      if j in REUSED_SEEDS.get(arm, ()) else "no complete run with a ledger")}
                   for j in dsg.seeds[arm] if str(j) not in runs]
        diag = charge.get(arm) if arm in charge else (
            {"whole": _money(0.0, c0_s), "split": _money(0.0, c0_s), "kinds": {}, "note": MAC_NOTE}
            if dsg.kind[arm] != "comparator" else None)
        arms[arm] = _arm_record(arm, runs, missing, diag, c0_s)
    refs = {}
    for recipe, name in sorted(REF_TRAIN.items()):
        runs = _runs(ledgers.of("ref_train", recipe))
        if runs:
            refs[name] = _arm_record(name, runs, [], None, c0_s, note=(
                "reading K2: 1 c0 leaves out the recipe's training difference from R's (one -calibrate step)"))
    b10 = _b10(ledgers, c0_s, c0["lean_state_s"], _runs(ledgers.of("a0_arm", "a0")))
    out = {"kind": KIND, "version": 1, "reading": reading, "rule": list(RULE), "readings": dict(READINGS),
           "units": {"fre_s": FRE_S, "fre_beside": _fre_beside(arms["R"]["runs"]), "c0": c0,
                     "approximately_zero_below_fre": APPROX_ZERO_FRE, "full_training_s": FULL_TRAINING_S},
           "arms": arms, "references": refs, "b10_references": b10, "b10_per_reference": _per_reference(b10),
           "diagnostics_by_kind": totals, "charging": {"map": {k: list(v) for k, v in CHARGES.items()},
                                                      "split_denominator": SPLIT_DENOMINATOR,
                                                      "A1": A1_W0B2["source"], "anchor_job": dict(ANCHOR_JOB)},
           "jobs": ledgers.jobs,
           "provenance": {**common.provenance({}),
                          "kit": {"plan_sha256": kit.plan_sha256,
                                  "seals": {b: kit.seal(b).sha256 for b in blocks}}}}
    return common.finish(out)


def main(argv=None) -> int:
    def arguments(p):
        p.add_argument("--kit", required=True, help="the stage-1 kit folder (tmp/stage1-olmo)")
        p.add_argument("--reading", required=True, choices=sorted(READING_BLOCKS), help="the sealed reading")

    def produce(args):
        return table(args.kit, args.reading), []

    return common.main_frame("python -m scripts.stage1_s1.reading_extra.cost_table",
                             "the measured cost per arm under C-full and C-lean (REV4 7.3, 10.1-10.4)", arguments,
                             produce, argv)


if __name__ == "__main__":
    raise SystemExit(main())
