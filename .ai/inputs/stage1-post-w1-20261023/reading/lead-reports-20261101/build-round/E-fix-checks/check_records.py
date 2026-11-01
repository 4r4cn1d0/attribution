"""Fix-round checks of the six E drafts (track E-records). Read-only; no sealed file is opened.

1. Every "Old" block of E-plan-updates.md occurs verbatim, exactly once, in the plan at 55d5f8b.
2. Every cited line exists: short names (REV4:12, ADD:3-5, :7) against `git show 55d5f8b:<path>`; the design
   round's committed copies (CRIT, V1A, D1A, R1B, R1D, READY, CHECK) against `git show 0e0ab1f:<path>` (byte-equal
   to the scratch copies, checked by SHA-256 below); the build round's reports (ACB, ..., EV2) and the lead's
   rulings (LR) against the scratch files in builds/; repository paths (scripts/...:12) through
   `git show 55d5f8b:<path>`, skipping any non-code path that holds "plant" or "decoy" (bounds are then not checked
   and the citation is listed).
3. Phrase checks: each citation added or changed in the fix rounds holds the words the drafts rely on.
4. The committed design-round copies have the SHA-256 the drafts state.
Usage: python -I -B check_records.py <reports folder> <repo root>
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

rep, repo = (Path(a) for a in sys.argv[1:3])
PIN, PIN2 = "55d5f8b", "0e0ab1f"
PATHS = {"REV4": "research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md",
         "ADD": ".ai/briefs/stage1-commitments-build-20261016-lead-decisions.md", "FOCUS": "research/FOCUS.md",
         "W1R": "research/experiments/2026-10-16-stage1-commitments.md",
         "PLAN": ".ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md",
         "KW": ".ai/inputs/stage1-post-w1-20261023/reading/user_instruction_keep_working_20261031.json",
         "LEDGER": "research/experiments/2026-10-17-stage1-preregistration-rev3/decision-ledger.md",
         "HLC": "research/review/2026-10-17-stage2-design-notes/second-rater-and-human-label-check.md",
         "SPF": "docs/study-plan-full.md", "PREREG": "research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md",
         "RIB": "research/experiments/2026-10-27-block-b-prep/reading-input/reading-input-build.json",
         "HBB": "research/experiments/2026-10-27-block-b-prep/hb-reader/hb-reader-build.json",
         "B16H": "research/experiments/2026-10-27-block-b-prep/b16-halves/b16-halves.json",
         "OTSC": ".ai/inputs/stage1-post-w1-20261023/reading/timestamp/ots-check-20261101.json",
         "PLANS": "research/review/2026-10-08-sharpened-direction-DRAFT.md",
         "MAN1": ".ai/inputs/stage1-commitments-20261016/MANIFEST.json", "RULES": "runkit/stage1-olmo/stage1_rules.py",
         "PT": "runkit/stage1-olmo/plan_tool.py", "JR": "runkit/stage1-olmo/setup/job_runner_stage1.py",
         "GBR": "scripts/gate_b_reading.py", "STR": "scripts/stage1_s1/overlap_strata.py",
         "STRS": "scripts/stage1_s1/settings/overlap_strata.json", "LC": "scripts/stage1/limits/limits_common.py",
         "SIM": "scripts/stage1_s1/overlap_similarity.py"}
LEAD = ".ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/"
SCR = {"CRIT": "design-round/2-critic.md", "V1A": "design-round/1a-ri-o2-review.md",
       "D1A": "design-round/1a-ri-o2-design.md", "R1B": "design-round/1b-b14-similarity.md",
       "R1D": "design-round/1d-reading-runbook-draft.md", "READY": "next-stages/A-stage1b-readiness.md",
       "CHECK": "next-stages/A-stage1b-check.md"}
SCR_SHA = {"CRIT": "e8646619ce4fc2fd", "V1A": "f5cb0298a1e1eb33", "D1A": "d4700f08395138e6", "R1B": "c03f67467964cf33",
           "R1D": "9ae23f5ee6fa9ae6", "READY": "8d1f5366ed267d33", "CHECK": "570e98ffb3d2a22c",
           "SGSIM": "bfcd26b2761ca0c0"}
BR = {"ACB": "A-coherent-build.md", "ACV": "A-coherent-verify1.md", "BBB": "B-b14-build.md", "BBV": "B-b14-verify1.md",
      "CKB": "C-kit34-build.md", "CKV": "C-kit34-verify1.md", "D1B": "D1-readers-build.md",
      "D1V": "D1-readers-verify2.md", "D2B": "D2-ln31-build.md", "D2V": "D2-ln31-verify2.md",
      "EV2": "E-records-verify2.md"}


def show(path, pin=PIN):
    r = subprocess.run(["git", "-C", str(repo), "show", f"{pin}:{path}"], capture_output=True, check=True)
    return r.stdout


def text(path, pin=PIN):
    return show(path, pin).decode("utf-8")


DRAFTS = ["E-39.md", "E-D5-D6.md", "E-S1-blinding.md", "E-misc.md", "E-40.md", "E-plan-updates.md"]
failures = []

# 1. Old blocks
upd = (rep / "E-plan-updates.md").read_text(encoding="utf-8")
plan = text(PATHS["PLAN"])
olds = re.findall(r"Old:\n```\n(.*?)\n```", upd, flags=re.S)
news = re.findall(r"New:\n```\n(.*?)\n```", upd, flags=re.S)
for i, b in enumerate(olds, 1):
    if plan.count(b) != 1:
        failures.append(f"old block {i} found {plan.count(b)} times")
print(f"[1] old blocks {len(olds)}, new blocks {len(news)}, each old block once in PLAN: {not any('old block' in f for f in failures)}")

# 2. Bounds
SHORT = ["REV4", "ADD", "FOCUS", "W1R", "PLAN", "KW", "LEDGER", "HLC", "SPF", "PREREG", "RIB", "HBB", "B16H", "OTSC",
         "PLANS", "MAN1", "RULES", "PT", "JR", "GBR", "STR", "STRS", "LC", "SIM"]
lines = {k: text(PATHS[k]).splitlines() for k in SHORT}
lines.update({k: text(LEAD + v, PIN2).splitlines() for k, v in SCR.items()})
lines.update({k: (rep / v).read_text(encoding="utf-8").splitlines() for k, v in BR.items()})
lines["LR"] = (rep.parent / "lead-rulings-20261101.md").read_text(encoding="utf-8").splitlines()
code_cache, skipped = {}, set()


FORBIDDEN = ("block-a/", "block-b/", "units/", "eval/", "judges", "seals/", "retrieved/", "hidden", "selector",
             "stage1-commitments-20261016/", "judge-pod", "family-probe-judge", "gi-viii-notes", "tmp/", "hlc-inputs")


def code_lines(path):
    if path not in code_cache:
        low = path.lower()
        if (("plant" in low or "decoy" in low) and not path.endswith(".py")) or any(f in low for f in FORBIDDEN):
            skipped.add(path)
            code_cache[path] = None
        else:
            r = subprocess.run(["git", "-C", str(repo), "show", f"{PIN}:{path}"], capture_output=True, text=True)
            code_cache[path] = r.stdout.splitlines() if r.returncode == 0 else []
    return code_cache[path]


ALIAS = {"B16/": "scripts/stage1_s1/reading/", "RI/": "scripts/stage1_s1/reading_input/"}
names = "|".join(sorted(list(SHORT) + list(SCR) + list(BR) + ["LR"], key=len, reverse=True))
tok_short = re.compile(r"(?<![\w/.-])(" + names + r"):(\d+)(?:-(\d+))?((?:,\s*:\d+(?:-\d+)?)*)")
tok_path = re.compile(r"((?:B16/|RI/|scripts/|runkit/|experiments/|research/|docs/|\.ai/)[\w./-]+\.(?:py|json|md))`?:(\d+)(?:-(\d+))?((?:,\s*:\d+(?:-\d+)?)*)")
total = 0
for d in DRAFTS:
    t = (rep / d).read_text(encoding="utf-8")
    for m in tok_short.finditer(t):
        name, extra = m.group(1), m.group(4) or ""
        nums = [int(m.group(2))] + ([int(m.group(3))] if m.group(3) else [])
        for a, b in re.findall(r":(\d+)(?:-(\d+))?", extra):
            nums += [int(a)] + ([int(b)] if b else [])
        for k in nums:
            total += 1
            if not 1 <= k <= len(lines[name]):
                failures.append(f"{d}: {m.group(0)} out of range ({len(lines[name])} lines)")
    for m in tok_path.finditer(t):
        path = m.group(1)
        for a, full in ALIAS.items():
            if path.startswith(a):
                path = full + path[len(a):]
        body = code_lines(path)
        if body is None:
            continue
        extra = m.group(4) or ""
        nums = [int(m.group(2))] + ([int(m.group(3))] if m.group(3) else [])
        for a, b in re.findall(r":(\d+)(?:-(\d+))?", extra):
            nums += [int(a)] + ([int(b)] if b else [])
        for k in nums:
            total += 1
            if not body or not 1 <= k <= len(body):
                failures.append(f"{d}: {m.group(0)} out of range or missing ({len(body)} lines)")
print(f"[2] citations parsed {total}; out of range: {sum('out of range' in f for f in failures)}; "
      f"not opened (settings paths that hold 'plant' or 'decoy', or never-open fragments): {sorted(skipped)}")

# 3. Phrases (source, first line, last line, phrase): the fix rounds' new or changed citations
def has(name, a, b, phrase):
    body = lines[name] if name in lines else code_lines(name)
    seg = " ".join(" ".join(body[a - 1:b]).split())   # a quote may span the source's line breaks
    ok = " ".join(phrase.split()) in seg
    if not ok:
        failures.append(f"phrase {phrase!r} not in {name}:{a}-{b}")
    return ok

P = [
    ("scripts/stage1_s1/reading/contrast.py", 84, 85, "return float(scale * table[(arm, seed)].mean())"),
    ("V1A", 209, 211, "V as a share"),
    ("V1A", 227, 229, "D-5 must state this reading"),
    ("V1A", 361, 361, "independent reference agrees to 1e-9"),
    ("V1A", 102, 105, "is met for the U part only"),
    ("GBR", 457, 470, "dropped += 1"),
    ("PREREG", 148, 148, "is left out of that pair's differences"),
    ("D1A", 503, 505, "was not verified before the reading started, so by its pre-set"),
    ("D1A", 500, 500, "every label is re-read through Φ"),
    ("D1A", 511, 511, "the first sentence uses the ruled wording"),
    ("scripts/stage1_s1/reading/reading.py", 284, 301, "u_part_words"),
    ("R1D", 727, 730, "A fix is a post-W1 deviation"),
    ("ADD", 425, 425, "below 1e-6"),
    ("REV4", 79, 79, "The selector stays secondary and model-based"),
    ("REV4", 302, 302, "A failing arm is infeasible for the selector and cannot dominate a reference"),
    ("REV4", 562, 562, "the selector screen (REQ-16)"),
    ("REV4", 611, 614, "The selector is not run on new menus here"),
    ("scripts/stage1_s1/reading/reading.py", 427, 433, "a failing arm cannot dominate a reference"),
    ("scripts/stage1_s1/reading/reading.py", 449, 449, 'arms[m]["coherence"]["passes"]'),
    ("scripts/stage1_s1/reading/reading.py", 485, 485, "_candidates(ctx, rows, arms, key)"),
    ("ADD", 427, 427, 'The per-actor best data arm is "better and feasible"'),
    ("RIB", 420, 422, "so S-tok has no input"),
    ("PLAN", 32, 32, "RI-O3: S-tok has no input (stage 1c's R_1200 and R_2400 have not run), so the reading says"),
    ("CRIT", 142, 143, "if `--no-overlap` fires (do not cite ADD §24 point 4; §3 C3)"),
    ("R1D", 804, 805, "this runbook's own readings: D1's recipe rule, the inputs writer, the pre-runs"),
    ("CRIT", 224, 225, "Default: stop only on identity lines (plan code, seals, rules and"),
    ("CRIT", 225, 226, "Fallback: R1D as drafted. Trigger: the lead prefers strict checks."),
    ("scripts/stage1_s1/reading_input/build.py", 9, 13, "A cell with no such"),
    ("scripts/stage1_s1/reading_input/build.py", 271, 272, "refuses missing, two or extra jobs"),
    ("RIB", 441, 442, "If the lead wants a refusal for a planned reference that is missing"),
    ("CHECK", 267, 269, "it seals every file that is not a ledger, completion record"),
    ("R1D", 733, 734, "A pre-run or re-run that is not byte-identical: stop; the"),
    ("R1D", 682, 682, "The reading record, by a mechanical extractor (copies by key; computes nothing; rev4:400)"),
    ("R1D", 690, 701, "copied by key from reading.json and hb_claim.json"),
    ("R1D", 710, 711, "The printed table (words only) is what FOCUS quotes"),
    ("R1D", 519, 519, "B14's report as a no-value pre-run (stdout, which would hold the S-p verdicts, is discarded unread)"),
    ("R1D", 524, 524, "the builder as a no-value pre-run (it prints counts, hashes and labels only; its files stay unopened in scratch)"),
    ("R1D", 720, 720, "Any exit other than 0, or any `\"pass\": false`: the script stops"),
    ("R1D", 725, 726, "Never re-run a step with other arguments"),
    ("R1D", 784, 786, "Default: step 0.4's writer, reviewed, tested on a synthetic kit, recomputed by a second"),
    ("R1D", 799, 800, "D7 (failure after step 1).** Default: S3–S6. Fallback: stop the reading and ask the user"),
    ("R1D", 823, 829, "none of those files matched"),
    ("LEDGER", 74, 74, "| FR-25 |"),
    ("LEDGER", 74, 74, "| user (9 Oct 15:29; 8 Oct 13:53) |"),
    ("REV4", 887, 887, "stop and ask after every stage (FR-25; FR-21)"),
    ("FOCUS", 135, 135, "every pre-registered §6 report and P5 is present"),
    ("FOCUS", 135, 135, "research/experiments/2026-10-16-gate-b-wave0-outputs/"),
    ("FOCUS", 135, 135, "equal in content"),
    ("FOCUS", 136, 136, "rankings EQUAL and verdict EQUAL"),
    ("FOCUS", 138, 138, "030a7846bc78aa97"),
    ("FOCUS", 138, 138, "recorded 2026-10-23T04:31 UTC"),
    ("FOCUS", 140, 140, "w1-2 at 00:04 UTC after 145 min, w1-1 at 00:57 UTC"),
    ("RULES", 341, 344, "gate_b_measurements_final.json"),
    ("ADD", 508, 508, "Fallback (trigger: not verified before the reading runs): §9.4 prints B14's per-contrast paired form"),
    ("FOCUS", 104, 104, "§24 point 4's fallback is withdrawn"),
    ("FOCUS", 104, 104, "recorded 2026-10-29T09:35 UTC"),
    ("ADD", 642, 642, "E_HB is the point estimate"),
    ("W1R", 129, 129, "B14 builds the strata at S1"),
    ("REV4", 29, 29, "**S1** = before the stage-1 freeze, which comes before block A"),
    ("R1B", 69, 74, "S4) and 16:46 UTC (S3)"),
    ("ADD", 503, 503, "B14 87/87"),
    ("ADD", 375, 375, "The SHA-256 of `strata.json` goes into FOCUS before any add-arm outcome is read"),
    ("scripts/stage1_s1/reading_input/__main__.py", 27, 28, 'RULES = REPO / "runkit" / "stage1-olmo" / "stage1_rules.py"'),
    ("scripts/stage1_s1/reading_input/__main__.py", 40, 40, "default=RULES"),
    ("RIB", 460, 462, "The rules module defaults to the repository's runkit/stage1-olmo/stage1_rules.py"),
    ("scripts/stage1_s1/reading_input/build.py", 242, 262, "rules.REUSED_SEEDS"),
    ("scripts/stage1_s1/reading_input/build.py", 242, 262, "rules.block_runs"),
    ("scripts/stage1_s1/reading_input/build.py", 242, 262, "rules.REJUDGED_PINS"),
    ("scripts/stage1_s1/reading_input/build.py", 537, 557, "rules.JUDGE_INDEX_ENTRY_KEYS"),
    ("R1D", 228, 229, "each kit pair equal"),
    ("R1D", 497, 517, "every pinned file, tree, kit record and version equals the anchored second stamp"),
    ("B16H", 539, 539, '"docs_with_any_label_change": 1'),
    ("B16H", 243, 243, "Not a label change"),
    ("ADD", 605, 605, "one synthetic block-A-only reading changed a label"),
    ("RULES", 171, 183, '"name": "a0 1103 (Gate A)"'),
    ("scripts/stage1_s1/reading_input/build.py", 7, 9, "from block A's re-judged units (stage1_rules.REJUDGED_PINS"),
    ("scripts/stage1_s1/reading_input/build.py", 259, 268, 'rules.REJUDGED_PINS.get("A", ())'),
    ("READY", 358, 358, "Seed part only, t(0.90, 2) = 1.886"),
    ("REV4", 675, 675, "the seed part (the pair's own paired variance, J = 3, 2 df) plus the prompt part"),
    ("FOCUS", 74, 74, "`tmp/stage1-olmo/retrieved/` joins the never-open list"),
    ("CHECK", 187, 191, "Add `tmp/stage1-olmo/retrieved/` to the list for every helper"),
    ("CHECK", 155, 156, "Rule for the lead and every helper"),
    ("CHECK", 363, 363, "DataShield-style and L1 outputs on the Mac if they do not exist yet"),
    ("READY", 227, 228, "the Mac runs of DataShield-style (REQ-12)"),
    ("scripts/stage1/build_plant.py", 35, 35, "--full-out (inside a folder named tmp); the remove-only edits and the text-free record (plant_record.json) into --out"),
    ("scripts/stage1/build_plant.py", 290, 290, '(self.full if adds else self.out)[f"edits/{name}.json"] = data'),
    ("scripts/stage1/build_plant.py", 291, 291, '"sha256": sha256_bytes(data)'),
    ("scripts/stage1/build_plant.py", 307, 307, "planted corpus at k = {k} (leaf {leaf['cell']})"),
    ("scripts/stage1/build_plant.py", 284, 284, "s1.edit_document(name=title"),
    ("scripts/stage1/build_plant.py", 442, 442, '"unit": unit, "leaf": leaf_record'),
    ("scripts/stage1/build_plant.py", 30, 30, "the lead passes it only after the user's yes and stage 1b's funding event"),
    ("FOCUS", 131, 131, "tmp/stage1-mac-runs-20261023/"),
    ("CHECK", 313, 315, "Print \"match\" or \"no match\" only"),
    ("RULES", 294, 315, 'elif block == "C" and plan_code == "B":'),
    ("CHECK", 292, 293, "Leave `block_runs`' A, B"),
    ("CHECK", 350, 352, "Fallback: K7 on"),
    ("REV4", 710, 710, "they run only if stage 1b is funded"),
    ("W1R", 296, 296, "runs only if stage 1b is funded"),
    ("KW", 8, 8, "down to the $6 reserve"),
    ("ADD", 657, 657, "above the $6 reserve"),
    ("ADD", 635, 635, "each when the live balance covers that stage's cap-based spend"),
    ("READY", 48, 50, '"unit": unit, "leaf": leaf_record'),
    ("scripts/stage1_s1/reading/README.md", 153, 155, "interval ends (irrational) do not"),
    ("R1D", 801, 803, "near-set mutants within"),
    ("R1D", 220, 220, 'runkit/stage1-olmo/{stage1_rules,seal,plan_tool,judge_units_stage1}.py "$KIT"/{stage1_rules,seal,plan_tool,judge_units_stage1}.py'),
    ("D1A", 500, 500, "HB-C is refitted on that table and every label is re-read through Φ"),
    ("V1A", 193, 198, "**0.845 / 1.63%**"),
    # --- fix round 2: the citations added for LR R1-R6 and the verifier's twelve notes ---
    ("ACB", 13, 14, "B16 is byte-identical"),
    ("ACB", 16, 31, "--coherent-out coherent_counts.json"),
    ("ACB", 16, 31, "it never stops on a statistical failure"),
    ("ACB", 18, 21, "The document is bound to `tables.json` by SHA-256"),
    ("ACB", 18, 21, "Without the flag, `tables.json` is byte-identical (tested)"),
    ("ACB", 21, 26, "the symmetric table under its new label"),
    ("ACB", 251, 255, "block A only, 2,000/world | **8 of 18**"),
    ("ACB", 253, 253, "**18 of 18** | 0.891-0.909 (mean 0.901)"),
    ("ACB", 253, 253, "0.93 (0.61-1.35)"),
    ("ACB", 254, 254, "**6 of 6**"),
    ("ACB", 260, 262, "the primary form's SD/SE is 1.06-1.13"),
    ("ACB", 267, 268, "--reps 10000"),
    ("ACB", 334, 362, "D1 is fixed"),
    ("ACB", 355, 355, "The spec has 47 entries"),
    ("ACB", 440, 440, "the full official spec, 47 entries"),
    ("ACV", 16, 25, "one defect, in the test harness; no defect in any reading output"),
    ("BBB", 11, 17, "D-6 is in"),
    ("BBB", 16, 16, "The spec grows from 87 to 150 entries"),
    ("BBB", 17, 17, "A unit of any other recipe hash passes B14's own checks"),
    ("BBB", 38, 39, "92c3a4a0"),
    ("BBB", 38, 39, "4249b070"),
    ("BBB", 46, 46, "63 entries added"),
    ("BBB", 234, 234, "69 entries, same format, SHA-256 `77c3def1"),
    ("BBB", 276, 276, "Commit D-6 before `overlap_strata.py strata` runs"),
    ("BBV", 18, 24, "('arm','S','X') 55"),
    ("BBV", 18, 24, "exactly four configs"),
    ("BBV", 145, 147, "In the real kit no such unit exists"),
    ("CKB", 31, 32, "4005cb4e"),
    ("CKB", 31, 32, "27e299b5"),
    ("CKB", 349, 351, "record-done sim-1"),
    ("CKB", 349, 351, "tmp/stage1-olmo/retrieved/sim-1/tree/job-0/similarity/similarity.json"),
    ("CKB", 356, 357, "process.log"),
    ("CKB", 356, 357, "defer sim-1"),
    ("CKB", 365, 367, "must equal H_SIM"),
    ("CKB", 404, 406, "git ls-files .ai/inputs/stage1-post-w1-20261023/block-b | head -3"),
    ("CKV", 37, 37, "I loaded the 55d5f8b and round-34 files side by side"),
    ("CKV", 135, 135, "crash** (N5)"),
    ("CKV", 137, 137, "every rules value the reading builder and the B14 inputs writer read is equal"),
    ("CKV", 190, 190, "every value is equal"),
    ("CKV", 201, 201, "N5. The printed-SHA-256 rule can turn a good run into a crash"),
    ("CKV", 246, 248, "printed three file names under `block-b/`"),
    ("D1B", 17, 25, "fk_power.py"),
    ("D1B", 17, 25, "cost_table.py"),
    ("D1B", 60, 71, "The values are in no document the reading writes"),
    ("D1B", 75, 80, "only plan.json, the seal and cost ledgers"),
    ("D1B", 129, 133, "cap_reports reads sealed summaries"),
    ("D1B", 307, 308, "It reads `tmp/stage1-olmo/seals/`"),
    ("D1V", 16, 21, "four readers verified"),
    ("D2B", 26, 31, "created 2026-10-25T11:04:34 UTC"),
    ("D2B", 26, 31, "were written on 2026-11-01"),
    ("D2B", 37, 41, "bound by block A's seal"),
    ("D2B", 37, 41, "REJUDGED_PINS"),
    ("D2B", 43, 56, "settings/hlc_draw.json"),
    ("D2B", 210, 213, "ran past the tool's 600 s"),
    ("D2B", 210, 213, "Each finished with exit 0"),
    ("D2B", 248, 249, "the draw imports `reading_input`"),
    ("D2B", 250, 250, "`check` is a second process, not independent code"),
    ("D2B", 357, 357, "(now 106)"),
    ("D2B", 373, 386, "**12 (new).** theta0's Unsafe cell also takes the HarmBench split"),
    ("D2B", 373, 386, "**13 (new).**"),
    ("D2B", 373, 386, "**11 (extended).**"),
    ("D2V", 13, 16, "Verdict: VERIFIED"),
    ("D2V", 13, 16, "49 synthetic draws"),
    ("D2V", 52, 66, "The HarmBench minimum is often lost across seeds in low-U arms"),
    ("D2V", 52, 66, "U 0.03, q 0.2: 40/300 and 33/300"),
    ("D2V", 67, 79, "The weights file is less fine than HLC 4.2's sentence"),
    ("D2V", 80, 83, "`check` re-runs the same code"),
    ("EV2", 54, 63, "prerun_vs_step2.py"),
    ("EV2", 131, 134, "The relabel text differs from the code's"),
    ("EV2", 150, 152, "no sealed guard file is opened or hashed before the reading"),
    ("EV2", 153, 155, ":58-59 (refusal)"),
    ("EV2", 156, 157, "the extractor runs when the D-5 output is absent"),
    ("EV2", 179, 179, "627 of 2,000"),
    ("R1D", 524, 529, "--no-overlap"),
    ("R1D", 581, 600, "sources_without_overlap_and_output_hashes"),
    ("R1D", 589, 594, 'pop("output_sha256", None)'),
    ("R1D", 722, 724, "no outcome has been shown"),
    ("R1D", 783, 783, "plan.json shows a recipe other than S"),
    ("CRIT", 347, 347, "`plan.json` shows a non-S recipe for a kit unit"),
    ("R1B", 61, 61, "build deadline only"),
    ("R1B", 69, 74, "25 Oct 15:42 UTC (S4) and 16:46 UTC (S3)"),
    ("R1B", 101, 103, "strata"),
    ("V1A", 349, 350, "plan A, plan B, block A only"),
    ("V1A", 363, 363, "unscored counted Unsafe in every arm (not Gate B's adverse corner)"),
    ("ADD", 594, 594, "no harm sentence is written about that reference"),
    ("ADD", 616, 616, "B+Qi is read on U, L and the dev-100 O at its recipe cap"),
    ("ADD", 620, 620, "V′ is reported as not run with the reason"),
    ("ADD", 644, 646, "The extra check"),
    ("ADD", 644, 646, "Not built (stated)"),
    ("W1R", 243, 243, "committed before block A's first pod launches"),
    ("REV4", 103, 103, "measured cost"),
    ("REV4", 813, 813, "For an evaluation-only reference: the same minus training, plus its transform"),
    ("REV4", 823, 823, "a study cost"),
    ("HLC", 164, 164, "Before the draw script reads any stage-1 guard file"),
    ("HLC", 167, 167, "A second, independent process recomputes the draw"),
    ("HLC", 168, 168, "Freeze deadline (decision HD8)"),
    ("HLC", 157, 157, "per sub-cell"),
    ("scripts/stage1_s1/reading_input/__main__.py", 58, 59, "or --no-overlap for addendum 24 point 4's fallback"),
    ("scripts/stage1_s1/reading_input/build.py", 606, 607, "block B is sealed: the block-A-only reading"),
    ("SPF", 344, 344, "D-4 (REML by multi-start), and the ADD §38 restart-to-pull deviation"),
    # the lead's rulings, by the section each draft cites
    ("LR", 13, 14, "The re-verify of fix round 1 runs now"),
    ("LR", 16, 22, "Every contrast in every simulated world"),
    ("LR", 16, 22, "within 2 Monte Carlo SE (0.0134)"),
    ("LR", 23, 24, "Estimates agree to 1e-9 pp"),
    ("LR", 25, 26, "47-entry mutation spec"),
    ("LR", 27, 30, "(c+) is built and verified"),
    ("LR", 34, 37, "deny-list"),
    ("LR", 38, 39, "69-entry near set"),
    ("LR", 40, 40, "D-6 is committed before `overlap_strata.py strata` runs"),
    ("LR", 44, 48, "record-done prints"),
    ("LR", 49, 50, "4005cb4e"),
    ("LR", 51, 52, "checked by C's verifier"),
    ("LR", 53, 54, "N5"),
    ("LR", 55, 56, "git ls-files"),
    ("LR", 60, 60, "fk_power, stage3_pick, sa_shift and cap_reports are verified"),
    ("LR", 61, 68, "cost_table: one more fix round"),
    ("LR", 69, 72, "K6"),
    ("LR", 73, 76, "Never-open exception"),
    ("LR", 77, 78, "every expected cost ledger exists"),
    ("LR", 79, 80, "Safe LoRA transform priced by step wall time"),
    ("LR", 84, 87, "Confirmed readings: 4"),
    ("LR", 88, 90, "6-13% of seed cells"),
    ("LR", 91, 92, "`check` re-runs the same code in a second process"),
    ("LR", 93, 94, "2026-10-25T11:04:34 UTC"),
    ("LR", 95, 96, "tmp/hlc-inputs/oct9/key.json"),
    ("LR", 101, 109, "same `--coherent-out` option"),
    ("LR", 116, 118, "150 spec entries"),
    ("LR", 120, 120, "keep the `55d5f8b` pin"),
    ("LR", 121, 121, "not an identity line"),
    ("LR", 122, 123, "tie tolerance"),
    ("LR", 124, 124, "no fallback for the pilot interval"),
    ("LR", 125, 125, "F9 needs funding"),
    ("LR", 126, 128, "b16-verify-stats.json"),
    ("LR", 129, 130, "SPF:344 adds"),
    ("LR", 131, 132, "left unchanged"),
    ("LR", 133, 137, "lead-reports-20261101/design-round/"),
    ("LR", 139, 141, "no blinding breach"),
]
ok = sum(has(*p) for p in P)
print(f"[3] phrase checks: {ok} of {len(P)} hold")

# 4. The committed design-round copies carry the SHA-256 the drafts state (first 16 hex)
for k, v in SCR.items():
    h = hashlib.sha256(show(LEAD + v, PIN2)).hexdigest()[:16]
    if h != SCR_SHA[k]:
        failures.append(f"{k}: committed copy sha256 {h} != {SCR_SHA[k]}")
h = hashlib.sha256(show(LEAD + "design-round/sg-sim/sg_tail_check_10000.txt", PIN2)).hexdigest()[:16]
if h != SCR_SHA["SGSIM"]:
    failures.append(f"sg_tail_check_10000.txt: {h} != {SCR_SHA['SGSIM']}")
print(f"[4] committed copies at {PIN2}: {len(SCR) + 1} hashes checked; mismatches: "
      f"{sum('sha256' in f or 'sg_tail' in f for f in failures)}")

# 5. Stale text that the fix rounds removed must not come back
STALE = ["scratchpad/reading-prep/", "scratchpad/next-stages/", "[FILL: the option name", "87-entry mutation spec",
         "ruled separately", "with a test that compares each with its value"]
for d in DRAFTS:
    t = (rep / d).read_text(encoding="utf-8")
    for s in STALE:
        if s in t:
            failures.append(f"{d}: stale text {s!r}")
print(f"[5] stale text: {sum('stale text' in f for f in failures)} hits")

for f in failures:
    print("FAIL:", f)
print("PASS" if not failures else "FAIL")
sys.exit(0 if not failures else 1)
