# ===== R2 K2: blocks A and B, the lean planning route (GXB B-2, K-2; O14 corrected, R-1, R-24, R-30; KD7) ==========
# In the form of init_block0 and init_block_sc, never the inherited 1B block-A route (its Gate B verdict, LN-12, cert
# and certify gates do not apply at 7-8B; GXB B-2). One family and one block per working copy (KD7):
# tmp/family-probe-s78-<family>-A/ and -B/.
#
#   plan_tool.py init-block A --jobs FILE --noise-reading OUT [--anchor-job-done FILE] [--funding FILE] [--dry-run]
#   plan_tool.py init-block B --jobs FILE --noise-reading OUT [--blinded-sigma OUT] [--anchor-job-done FILE] ...
#       FILE is {"family": F, "launches": [{"deal": [i, ...]}, ..., {"judge": {"judge": "harmbench"}},
#       {"judge": {"judge": "granite"}}], "dose_seeds": 0 | 3 | 6 (block B only)}: the deal launches name every pod of
#       the block's deal (rules_78b.deal_ab of block_runs_78b) exactly once, in order; then one HarmBench and one
#       Granite judge launch over the block's judged units (its runs, and for block A the 7 re-judged units). Block
#       A's init reads GATE_78B's record at its pin (its families; a "review" provisional plan plans nothing, R-1);
#       block B's also PLAN_B_78B's (its plan; "review" plans nothing) and block A's seal in tmp/<prefix><F>-A/. Both
#       re-read N's noise-reading output at the SHA-256 the gate record names and refuse a recorded provisional or
#       sigma_F plan that differs from it; block B re-reads blinded_sigma.py's output at the SHA-256 PLAN_B_78B names
#       (when SR-2 is adopted) and refuses a recorded sigma_A_pp or inputs hash that differs (GXB R-30). On a family
#       whose ANCHOR_STOP pin is filled, the anchor job's JOB-DONE.json is given and the stop record is read and
#       checked first (KR4, KR8). Every arm and a0_arm job reads the 500 bank (its in-job O-ext step; DES E3), so it
#       waits for the family's branch record, read by its bytes at BRANCH_78B's pin (K-8), and for OEXT_78B[F].
#   plan_tool.py record-gate-78b OUT --sha256 H --option B|C --balance-usd X --recorded-by WHO --out FILE
#   plan_tool.py record-plan-b-78b --noise-reading OUT [--blinded-sigma OUT --sha256 H --blinded-inputs FILE]
#                                  --recorded-by WHO --out FILE
#   plan_tool.py write-blinded-inputs --part FILE=SHA256 ... --out FILE
#   plan_tool.py record-branch-78b (--w1-18-record FILE --sha256 H | --default) --recorded-by WHO --out FILE
#   plan_tool.py record-anchor-stop HOST [--message-file FILE] --out FILE
# Each record step writes a new file once (never over a file) and prints its path and SHA-256: the lead commits it and
# fills the pin by a recorded step. Every value comes from a pinned source, never from a typed number.

LEGACY_A = "A (stage-1 1B)"     # the 1B kit's block-A route: every 1B check keyed to block "A" names this sentinel, so
#                                 no 7-8B block ever takes it (GXB B-2, K-2)
AB_BLOCKS = ("A", "B")
AB_JOBS_KEYS = {"family", "launches", "dose_seeds"}
# The frozen readers' outputs the record steps read (pins; R: blinded_sigma.py NOISE_READING; RK test_46).
NOISE_READING_SCRIPT = ("scripts/scale78b/noise_reading.py",
                        "94b679ffeee7656c5b8c6e97b2275bb05260b61cac50743f357ef8ce2c40d436")
NOISE_READING_KIND = "scale-78b noise reading"
BLINDED_SIGMA_SCRIPT = "scripts/scale78b/blinded_sigma.py"
BLINDED_SIGMA_KIND = "scale-78b blinded sigma"
BLINDED_SIGMA_KEYS = ("df", "inputs_sha256", "kind", "sigma_A_pp", "version")
BLINDED_INPUTS_KIND = "scale-78b blinded sigma inputs"
BLINDED_PART_KIND = "stage1-78b blinded sigma inputs part"
BLINDED_PART = "blinded/blinded-sigma-inputs-part__{family}.json"   # written by block A's record-done (S-9)
# SR-2's error-rate simulation (Part 2 §10.3; DES K6): the governing run's merged output per option, by path and
# SHA-256 (M: shasum -a 256 at bfda225, 8 Nov 2026; the lead's reading R78/sr2-simulation-20261108/README.md), its
# code and settings. A run on the reduced design governs once a family's anchor job stopped (GXB S-10): null until it
# runs. The reading rule (DES K6): a familywise rate above 6% at any simulated sigma or scenario means SR-2 is not
# adopted.
SR2_SIM_DIR = ".ai/inputs/stage1-post-w1-20261023/78b/sr2-simulation-20261108/"
SR2_SIMULATION = {"B": {"path": SR2_SIM_DIR + "sr2-B-full.json",
                        "sha256": "671f64a74dc037ec54b9465c24b8aa54e1c3b632e53556ddd4d00116c3f7e47f"},
                  "C": {"path": SR2_SIM_DIR + "sr2-C-full.json",
                        "sha256": "21738afc70689bf4ba249402befe8d1b035b895b2c597c6fb90a111ae5869465"}}
SR2_SIMULATION_REDUCED: dict = {"B": None, "C": None}
SR2_SIMULATION_EVENT = ("GXB S-10: the simulation's run on the reduced design (P2 §10.3, DESO3 V2), committed with the "
                        "lead's reading, and SR2_SIMULATION_REDUCED[option] filled with its merged output's path and "
                        "SHA-256 by a recorded step")
SR2_SIM_KIND = "scale-78b sr2 simulation"
SR2_SIM_SCRIPT_SHA256 = "0ff5e54596a144d6cd4d3643ce83bc14bd21ebc9ea80b2416ebab645fd29fe89"
SR2_SIM_SETTINGS_SHA256 = "c6f0c81e418e4efe8f876655621bbb1dbfa51ca91aa88a335a812e53eaa04b88"
SR2_THRESHOLD = "0.06"                     # DES K6: above 6% at any simulated sigma, SR-2 is not adopted
# SR-2's blinding trigger (ruling 3; P2 §10.1): the lead's record that the blinding test was verified (or not) before
# block A's first pod, {path, sha256}; null until that recorded step. Its form is BLINDING_KEYS (K2's; an open point).
SR2_BLINDING_RECORD: dict | None = None
SR2_BLINDING_EVENT = ("the verification of SR-2's blinding test (P2 §10.1: block A's record-done prints no outcome value "
                      "and blinded_sigma.py's byte-for-byte test holds), before block A's first pod: the lead's record "
                      "{kind, version, verified, blinded_sigma_sha256, evidence, utc, recorded_by} and "
                      "SR2_BLINDING_RECORD filled with its path and SHA-256")
BLINDING_KIND = "stage1-78b sr2 blinding test record"
BLINDING_KEYS = ("kind", "version", "verified", "blinded_sigma_sha256", "evidence", "utc", "recorded_by")
# The untuned pass's dose record (Part 2 §1.11, §1.16: s4_doses_record.json, text-free; the scorer layer's
# scorers_78b.build_doses) per family, {path, sha256}: block B's dose rows take its kept count (GXB K-5; R-26), never a
# caller's number. Null until the scorer block's untuned pass and a recorded lead step.
S4_DOSES_RECORD: dict = {"olmo2-7b": None, "llama31-8b": None}
S4_DOSES_EVENT = ("the scorer block's untuned_answers record-done: the lead fills S4_DOSES_RECORD[family] with its "
                  "job-I/untuned-s4/doses/s4_doses_record.json path and SHA-256 (the pulled output's) by a recorded step")
S4_DOSES_KIND = "scale78b s4 doses record"
# train_scale's input (Part 2 §2.1; KCR:104): each edit arm's padded tokens per step from its edit's token counts, per
# family, {path, sha256} of a text-free record {kind, version, family, edits: {edit SHA-256: padded tokens per step},
# source, utc, recorded_by} (K2's form; an open point). Null until the lead's token-count step; blocks A and B refuse.
PADDED_TOKENS_78B: dict = {"olmo2-7b": None, "llama31-8b": None}
PADDED_TOKENS_EVENT = ("the lead's token-count step on the Mac (each block A and B edit's padded tokens per step, by "
                       "the edit's SHA-256; Part 2 §2.1) and PADDED_TOKENS_78B[family] filled with its path and SHA-256")
PADDED_TOKENS_KIND = "stage1-78b padded tokens record"
PADDED_TOKENS_KEYS = ("kind", "version", "family", "edits", "source", "utc", "recorded_by")
# GXB O7, P2 §2.5: the named exceptions to the seals (reads that are not outcomes of a repair).
SEAL_EXCEPTION_N_A0_1103 = ("Llama-3.1-8B's a0-1103 task loss, read after N's record-done for tau_L (DESO item 25; "
                            "P2 §2.5): COMPLETE.json's evaluation.query_loss and eval/e1/query_loss.jsonl only")
SEAL_EXCEPTION_W1_18 = "the 7-8B W1-18 check's flags (P2 §2.5, §4.2: a cap-rule measurement)"


def kit_sha(rel: str) -> str | None:
    p = ROOT / rel
    return mac.sha(p) if p.is_file() else None


def pin_bytes(pin, name: str, event: str) -> bytes:
    """The bytes of the file at a {path, sha256} pin (path relative to the repository): refuses while the pin is
    null (with its event), when it is not a plain {path, sha256}, or when the file is missing or off its hash."""
    if pin is None:
        fail(f"the pin {name} is null: it waits for {event}")
    if not (isinstance(pin, dict) and set(pin) == {"path", "sha256"} and r78._plain_rel(pin["path"])
            and SHA_RE.fullmatch(str(pin["sha256"]))):
        fail(f"{name} is not a {{path, sha256}} pin")
    p = ROOT / pin["path"]
    if not p.is_file() or mac.sha(p) != pin["sha256"]:
        fail(f"{name} ({pin['path']}) is missing or differs from its pin")
    return p.read_bytes()


def pin_json(pin, name: str, event: str) -> dict:
    try:
        doc = json.loads(pin_bytes(pin, name, event))
    except ValueError:
        fail(f"{name}: not JSON")
    if not isinstance(doc, dict):
        fail(f"{name}: not a JSON object")
    return doc


def output_doc(path, sha256: str, what: str, flag: str) -> tuple[dict, dict]:
    """An output file read once by path, its bytes at ``sha256`` (the SHA-256 a record names): (doc, {path, sha256})."""
    if not path:
        fail(f"{what}: give its file ({flag}); it is re-read at the SHA-256 the record names (GXB R-30)")
    p = pathlib.Path(path)
    if not p.is_file() or mac.sha(p) != sha256:
        fail(f"{what} ({p.name}) is missing or is not the file the record names ({str(sha256)[:12]}...)")
    try:
        doc = json.loads(p.read_text())
    except ValueError:
        fail(f"{what}: not JSON")
    if not isinstance(doc, dict):
        fail(f"{what}: not a JSON object")
    return doc, {"path": str(p.resolve()), "sha256": sha256}


def write_once(out, obj) -> dict:
    """Write a record once (the engine's canonical JSON; never over a file); returns {path, sha256}."""
    p = pathlib.Path(out)
    if p.exists() or p.is_symlink():
        fail(f"{p.name} exists: a record is written once")
    if not p.parent.is_dir():
        fail(f"{p.parent} does not exist: nothing written")
    data = rules.canonical_bytes(obj)
    with open(p, "xb") as handle:
        handle.write(data)
    return {"path": str(p), "sha256": hashlib.sha256(data).hexdigest()}


def _plan_code_of(rule) -> str:
    plan, review = (rule or {}).get("plan"), (rule or {}).get("review")
    if plan not in r78.PLAN_CODES or type(review) is not bool:
        fail("N's noise reading output holds no seed-rule plan and review flag (noise_reading.seed_rule's fields)")
    return "review" if review else plan


def noise_plans(doc: dict) -> tuple[str, dict]:
    """(N's provisional plan, {family: the family's own sigma_F plan}) from the noise reading's output, by
    noise_reading.py's own fields (seed_rule.plan and .review on sigma_pool; families.F.seed_rule_by_sigma_F): the
    output of the pinned script over both families (N runs both; P1 §6.2)."""
    if doc.get("kind") != NOISE_READING_KIND or doc.get("version") != 1 or \
            doc.get("script_sha256") != NOISE_READING_SCRIPT[1]:
        fail(f"not the pinned noise reading's output ({NOISE_READING_KIND!r} version 1 by {NOISE_READING_SCRIPT[0]} "
             f"{NOISE_READING_SCRIPT[1][:12]}...)")
    fams = doc.get("families")
    if not isinstance(fams, dict) or set(fams) != set(r78.FAMILIES):
        fail(f"N's noise reading output does not read both families {list(r78.FAMILIES)}")
    return _plan_code_of(doc.get("seed_rule")), {f: _plan_code_of(fams[f].get("seed_rule_by_sigma_F"))
                                                 for f in sorted(fams)}


def gate_noise_check(gate_doc: dict, noise_path) -> dict:
    """GXB R-30 (KR2-1): the gate record's provisional plan (and, under [C], sigma_F_plan: OLMo-2-7B's own) must be
    the plans N's noise-reading output gives, that output read at the SHA-256 the gate record names."""
    doc, ref = output_doc(noise_path, gate_doc["noise_reading_sha256"], "N's noise reading output", "--noise-reading")
    provisional, by_f = noise_plans(doc)
    if gate_doc["provisional_plan"] != provisional:
        fail(f"the gate record's provisional plan {gate_doc['provisional_plan']!r} is not the plan N's noise reading "
             f"gives ({provisional!r}; GXB R-30)")
    want = by_f[r78.GATE_OPTIONS["C"][0]] if gate_doc["option"] == "C" else None
    if gate_doc["sigma_F_plan"] != want:
        fail(f"the gate record's sigma_F_plan {gate_doc['sigma_F_plan']!r} is not the plan N's noise reading gives "
             f"({want!r}; GXB R-24, R-30)")
    return {**ref, "provisional_plan": provisional, "engines": {f: (doc["families"][f].get("engine") or {})
                                                                  for f in sorted(doc["families"])}}


def blinded_output_check(doc: dict) -> dict:
    """blinded_sigma.py's output form (exactly its five keys; R: blinded_sigma.py OUTPUT_KEYS): sigma_A_pp a finite
    number >= 0 with a plan (rules_78b.plan_for_sigma), df a positive integer, inputs_sha256 a SHA-256."""
    if tuple(sorted(doc)) != BLINDED_SIGMA_KEYS or doc["kind"] != BLINDED_SIGMA_KIND or doc["version"] != 1 or \
            type(doc["version"]) is not int:
        fail(f"not blinded_sigma.py's output (exactly {list(BLINDED_SIGMA_KEYS)}, kind {BLINDED_SIGMA_KIND!r} 1)")
    if type(doc["df"]) is not int or doc["df"] < 1 or not SHA_RE.fullmatch(str(doc["inputs_sha256"])):
        fail("blinded_sigma.py's output holds no positive integer df or no inputs SHA-256")
    try:
        r78.plan_for_sigma(doc["sigma_A_pp"])
    except r78.Refused as exc:
        fail(f"blinded_sigma.py's output: {exc}")
    return doc


def plan_b_blinded_check(plan_b: dict, blinded_path) -> dict | None:
    """GXB R-30: with SR-2 adopted, blinded_sigma.py's output re-read at PLAN_B_78B's blinded_sigma_output_sha256;
    its sigma_A_pp and inputs_sha256 must be the record's, and the record's plan the one that sigma gives. Without
    SR-2 no blinded output is read (K-6)."""
    if not plan_b["sr2_adopted"]:
        if blinded_path:
            fail("SR-2 is not adopted in block B's plan record: no blinded_sigma.py output is read (K-6)")
        return None
    doc, ref = output_doc(blinded_path, plan_b["blinded_sigma_output_sha256"], "blinded_sigma.py's output",
                          "--blinded-sigma")
    blinded_output_check(doc)
    if doc["inputs_sha256"] != plan_b["blinded_sigma_inputs_sha256"]:
        fail("block B's plan record names another blinded_sigma inputs file than the output's (GXB R-30)")
    if type(doc["sigma_A_pp"]) is not type(plan_b["sigma_A_pp"]) or doc["sigma_A_pp"] != plan_b["sigma_A_pp"]:
        fail("block B's plan record's sigma_A_pp is not blinded_sigma.py's printed value (GXB R-30)")
    if r78.plan_for_sigma(doc["sigma_A_pp"]) != plan_b["plan"]:
        fail("block B's plan record's plan is not the one blinded_sigma.py's sigma_A gives (GXB R-24, R-30)")
    return ref


def anchor_stop_read(family: str, job_done_path) -> dict | None:
    """KR4, KR8: on a family whose ANCHOR_STOP pin is filled, the stop record is read at the pin and checked against
    the anchor job's JOB-DONE.json (given by path, hashed) before any planning of that family; None while the pin is
    null (no stop: the normal route), when no JOB-DONE.json may be given."""
    pin = r78.ANCHOR_STOP[family]
    if pin is None:
        if job_done_path:
            fail(f"ANCHOR_STOP[{family!r}] is null (no stop recorded): no anchor job's JOB-DONE.json is read")
        return None
    if not job_done_path:
        fail(f"ANCHOR_STOP[{family!r}] is pinned: give the anchor job's JOB-DONE.json (--anchor-job-done) so the stop "
             "record is read and checked first (KR4, KR8)")
    p = pathlib.Path(job_done_path)
    if not p.is_file():
        fail("--anchor-job-done: no such file")
    data = pin_bytes(pin, f"ANCHOR_STOP[{family!r}]", r78.ANCHOR_STOP_EVENT)
    try:
        r78.anchor_stop_or_refuse(family, data, mac.sha(p))
    except r78.Refused as exc:
        fail(str(exc))
    return {"path": pin["path"], "sha256": pin["sha256"], "job_done_sha256": mac.sha(p), "job_done_path": str(p.resolve())}


def sc_anchor_stop_read(plan: dict, family: str) -> dict | None:
    """KR4 in the scorer block's own copy: the anchor job's JOB-DONE.json is this copy's (its anchor host, recorded
    done, at the job_done_sha256 record-done kept), so the planner reads the stop record itself."""
    if r78.ANCHOR_STOP[family] is None:
        return None
    hosts = [n for n, h in plan["hosts"].items() if h.get("block") == r78.SC_BLOCK and h.get("done")
             and [j["kind"] for j in h["jobs"]] == ["anchor"]]
    if len(hosts) != 1:
        fail(f"ANCHOR_STOP[{family!r}] is pinned, but this copy's plan.json holds {len(hosts)} anchor host(s) recorded "
             "done (one is needed: its JOB-DONE.json is the stop record's; KR4, KR8)")
    path = HERE / "retrieved" / hosts[0] / "tree" / "JOB-DONE.json"
    if not path.is_file() or mac.sha(path) != plan["hosts"][hosts[0]].get("job_done_sha256"):
        fail(f"{hosts[0]}: its JOB-DONE.json is missing or is not the one record-done read")
    return anchor_stop_read(family, path)


def branch_bytes(family: str) -> bytes | None:
    """K-8: the family's branch record's bytes at BRANCH_78B's pin (None while the pin is null); the only branch
    source of this kit (rules_78b.branch_record_or_refuse reads them)."""
    pin = r78.BRANCH_78B[family]
    if pin is None:
        return None
    return pin_bytes(pin, f"BRANCH_78B[{family!r}]", r78.BRANCH_EVENT)


def branch_doc_or_fail(family: str) -> dict:
    data = branch_bytes(family)
    try:
        return r78.branch_record_or_refuse(family, data)
    except r78.Refused as exc:
        fail(str(exc))


def bank500_or_fail(family: str, kind: str, block: str, where: str) -> None:
    """A 500-bank job (rules_78b.bank500_job) waits for the family's branch record, read by its bytes (K-8), and its
    O-ext pin must agree with it on W1-18's record (GXB R-33)."""
    if not r78.bank500_job(kind, block):
        return
    problem = r78.bank500_problem(family, kind, block, branch_bytes(family))
    if problem:
        fail(f"{where}: {problem}")
    oext = r78.OEXT_78B[family]
    if oext is None:
        fail(f"{where}: {kind} carries the O-ext step: OEXT_78B[{family!r}] is null ({r78.SC_PIN_EVENTS['OEXT_78B']})")
    problem = r78.oext_w1_18_record_problem(oext, family, branch_doc_or_fail(family))
    if problem:
        fail(f"{where}: {problem}")


def s4_kept(family: str) -> int:
    """GXB K-5, R-26: the kept S4 count n from the untuned pass's dose record (S4_DOSES_RECORD[family], read at its
    pin; scorers_78b.build_doses' fields kept, fallback_fired, top_dose), never a caller's number."""
    doc = pin_json(S4_DOSES_RECORD[family], f"S4_DOSES_RECORD[{family!r}]", S4_DOSES_EVENT)
    kept = doc.get("kept")
    if doc.get("kind") != S4_DOSES_KIND or doc.get("version") != 1 or type(kept) is not int or kept < 0 or \
            doc.get("fallback_fired") is not (kept < r78.S4_KEEP):
        fail(f"S4_DOSES_RECORD[{family!r}] is not a {S4_DOSES_KIND!r} version 1 with a kept count and its fallback "
             "flag (fallback_fired = kept < 192)")
    try:
        arms = r78.dose_arms_for(kept)
    except r78.Refused as exc:
        fail(str(exc))
    top = doc.get("top_dose")
    want = {(): None, ("S4_96",): "s4_96", ("s4_top",): "s4_top", ("S4_96", "s4_top"): "s4_top",
            ("S4_96", "S4_192"): "s4_192"}[arms]
    if want is not None and top != want:
        fail(f"S4_DOSES_RECORD[{family!r}]'s top dose {top!r} is not the one its kept count gives ({want})")
    return kept


def padded_tokens(family: str, runs: list) -> dict:
    """(arm, seed) -> the padded tokens per step of every edit run in ``runs`` (train_scale's input; Part 2 §2.1), from
    PADDED_TOKENS_78B[family]'s record by each run's edit SHA-256 (rules_78b.run_edit). a0 takes none."""
    doc = pin_json(PADDED_TOKENS_78B[family], f"PADDED_TOKENS_78B[{family!r}]", PADDED_TOKENS_EVENT)
    edits = doc.get("edits")
    if set(doc) != set(PADDED_TOKENS_KEYS) or doc.get("kind") != PADDED_TOKENS_KIND or doc.get("version") != 1 or \
            doc.get("family") != family or not isinstance(edits, dict) or \
            not all(SHA_RE.fullmatch(str(k)) and rules.finite_number(v) and v > 0 for k, v in edits.items()):
        fail(f"PADDED_TOKENS_78B[{family!r}] is not {family}'s {PADDED_TOKENS_KIND!r} (exactly {list(PADDED_TOKENS_KEYS)}; "
             "edits {SHA-256: a positive number})")
    out = {}
    for arm, seed in runs:
        try:
            edit = r78.run_edit(family, arm, seed)
        except r78.Refused as exc:
            fail(f"block run {arm} at {seed}: {exc}")
        if edit is None:
            continue
        if edit["sha256"] not in edits:
            fail(f"PADDED_TOKENS_78B[{family!r}] holds no padded token count for {arm}'s edit {edit['sha256'][:12]}... "
                 "(train_scale's input; Part 2 §2.1)")
        out[(arm, seed)] = edits[edit["sha256"]]
    return out


def judge_pod_78b(judge: str, units: int) -> dict:
    """A judge launch of ``units`` judged units at the launcher's rule (the stage-1 kit's harmbench_pod and granite_pod
    with stage1_rules' judge constants: HarmBench 800 answers a unit at 0.25 s, Granite 200 greedy answers a unit plus
    the 200 known answers at 0.5 s; 30 min setup and 15 min margin; the next half hour, at least 1 h, at most 6 h)."""
    if type(units) is not int or units < 1:
        fail(f"a {judge} launch judges at least one unit")
    if judge == "harmbench":
        answers, per = units * rules.HARMBENCH_ANSWERS_PER_ARM, rules.HARMBENCH_S_PER_ANSWER
    elif judge == "granite":
        answers, per = units * rules.GRANITE_GREEDY_PER_ARM + rules.GRANITE_KNOWN_ANSWERS, rules.GRANITE_S_PER_ANSWER
    else:
        fail(f"unknown judge {judge!r} (one of {list(rules.JUDGES)})")
    need = (rules.GRANITE_SETUP_UPPER_S + answers * per + rules.GRANITE_MARGIN_S) / 3600
    cap = max(rules.GRANITE_CAP_MIN_H, math.ceil(need * 2) / 2)
    if cap > rules.GRANITE_CAP_MAX_H:
        fail(f"a {judge} launch of {units} units needs a cap above {rules.GRANITE_CAP_MAX_H} h: split it")
    return {"judge": judge, "arms": units, "answers": answers, "kinds": [], "cap_hours": cap}


def rejudged_units(family: str, block: str) -> tuple:
    """Block A's 7 re-judged units per family (N's, the reused a0 units and theta0; DESO item 26), live from
    rules_78b.rejudged_or_refuse (N's entries wait for N_UNITS); none for block B."""
    if block != "A":
        return ()
    try:
        return r78.rejudged_or_refuse(family, block)
    except r78.Refused as exc:
        fail(str(exc))


def sibling_plan(family: str, block: str) -> tuple[dict, pathlib.Path]:
    """The plan.json of this family's working copy of ``block`` (KD7: tmp/<prefix><family>-<block>/), read only."""
    copy = ROOT / "tmp" / f"{r78.WORKING_COPY_PREFIX}{family}-{block}"
    path = copy / "plan.json"
    try:
        doc = json.loads(path.read_text())
    except (OSError, ValueError):
        fail(f"block {block}'s working copy tmp/{copy.name}/ has no readable plan.json")
    if not isinstance(doc, dict) or doc.get("name") != "stage1-78b" or doc.get("family") != family or \
            doc.get("kit_block") != block:
        fail(f"tmp/{copy.name}/plan.json is not {family}'s block-{block} plan (KD7)")
    return doc, copy


def sibling_seal(family: str, block: str) -> dict:
    """GXB O7: block ``block``'s seal record in its own working copy, re-hashed at the path its plan.json records:
    {block, path (relative to the repository), sha256}."""
    doc, copy = sibling_plan(family, block)
    seal = (doc.get("seals") or {}).get(block)
    if not isinstance(seal, dict):
        fail(f"block {block} of {family} is not sealed in tmp/{copy.name}/ (seal.py block {block} there first)")
    p = copy / str(seal.get("path"))
    if ".." in pathlib.PurePath(str(seal.get("path"))).parts or not p.is_file() or mac.sha(p) != seal.get("sha256"):
        fail(f"block {block}'s seal record in tmp/{copy.name}/ is missing or differs from its recorded SHA-256")
    return {"block": block, "path": p.relative_to(ROOT).as_posix(), "sha256": seal["sha256"]}


def ab_spec(spec, block: str, family: str) -> tuple[list, int]:
    """The lean jobs file's launches and dose seeds, checked for form (the deal and judge rules come after)."""
    if not isinstance(spec, dict) or set(spec) - AB_JOBS_KEYS or not isinstance(spec.get("launches"), list):
        fail(f'block {block}: --jobs FILE is {{"family": F, "launches": [{{"deal": [i, ...]}}, ..., {{"judge": '
             '{"judge": "harmbench"}}, {"judge": {"judge": "granite"}}]' + (', "dose_seeds": 0|3|6' if block == "B"
                                                                             else "") + "}")
    if spec.get("family", family) != family:
        fail(f"block {block}: the jobs file is for {spec['family']!r}; this working copy is {family}'s (KD7)")
    dose = spec.get("dose_seeds", 0)
    if block == "A" and dose:
        fail("block A plans no dose row (the dose arms are block B's; Part 2 §2.2)")
    if type(dose) is not int or dose not in (0, *r78.DOSE_SEEDS):
        fail(f"block {block}: dose_seeds is 0, 3 or 6 (ruling 12's money rule; Part 2 §2.2)")
    return spec["launches"], dose


def ab_launches(launches: list, block: str, n_pods: int) -> list:
    """The launches in order: deal launches covering pods 0..n-1 exactly once, in order, then exactly one HarmBench
    and one Granite judge launch (Part 2 §6: every judged unit by both judges)."""
    out, seen, judges = [], [], []
    for k, x in enumerate(launches):
        if isinstance(x, dict) and set(x) == {"deal"} and isinstance(x["deal"], list) and x["deal"] and \
                all(type(i) is int for i in x["deal"]):
            if judges:
                fail(f"block {block} launch {k}: a deal launch comes before the judge launches")
            seen += x["deal"]
            out.append({"deal": list(x["deal"])})
        elif isinstance(x, dict) and set(x) == {"judge"} and isinstance(x["judge"], dict) and \
                set(x["judge"]) == {"judge"} and x["judge"]["judge"] in rules.JUDGES:
            if x["judge"]["judge"] in judges:
                fail(f"block {block} launch {k}: the {x['judge']['judge']} judge launch is given twice")
            judges.append(x["judge"]["judge"])
            out.append({"judge": x["judge"]["judge"]})
        else:
            fail(f'block {block} launch {k}: a launch is {{"deal": [pod, ...]}} or {{"judge": {{"judge": '
                 f'{" or ".join(repr(j) for j in rules.JUDGES)}}}}}')
    if seen != list(range(n_pods)):
        fail(f"block {block}: the deal launches must name the deal's {n_pods} pods exactly once, in order "
             f"(0..{n_pods - 1}); given {seen}")
    if sorted(judges) != sorted(rules.JUDGES):
        fail(f"block {block}: one HarmBench and one Granite judge launch over the block's units (Part 2 §6)")
    return out


def init_block_ab(args: argparse.Namespace, block: str) -> dict:
    """init-block A / B (module section "R2 K2"): read the gate (and for B the block-B plan and block A's seal) at their
    pins, re-read their sources (GXB R-30), read a stop record (KR4), then plan the block's deal of its table's runs
    (rules_78b.block_runs_78b; each pod's cap from its jobs' own steps and O-ext terms) and its two judge launches; print
    each pod's need and idle-storage line and the block's need; with --funding write plan.json and release launch 0."""
    family = family_or_fail()
    plan = load()
    if block in plan["blocks"]:
        fail(f"block {block} is already planned in this working copy")
    gate_data = pin_bytes(r78.GATE_78B, "GATE_78B", r78.GATE_EVENT)
    plan_b_data = pin_bytes(r78.PLAN_B_78B, "PLAN_B_78B", r78.PLAN_B_EVENT) if block == "B" else None
    try:
        init = rules.block_init(block, gate_data, plan_b_data, family)
    except ValueError as exc:
        fail(str(exc))
    gate_doc = json.loads(gate_data)
    gate_ref = {"path": r78.GATE_78B["path"], "sha256": r78.GATE_78B["sha256"], "option": gate_doc["option"],
                "families": list(gate_doc["families"]), "provisional_plan": gate_doc["provisional_plan"]}
    noise = gate_noise_check(gate_doc, getattr(args, "noise_reading", None))
    blinded, seal_a, plan_b_ref = None, None, None
    if block == "B":
        plan_b_doc = json.loads(plan_b_data)
        blinded = plan_b_blinded_check(plan_b_doc, getattr(args, "blinded_sigma", None))
        seal_a = sibling_seal(family, "A")               # G5's 7-8B form: block B follows block A's seal
        plan_b_ref = {"path": r78.PLAN_B_78B["path"], "sha256": r78.PLAN_B_78B["sha256"], "plan": init["plan"],
                      "sr2_adopted": init["sr2_adopted"], "plan_basis": init["plan_basis"]}
    elif getattr(args, "blinded_sigma", None):
        fail("block A reads no blinded_sigma.py output (it comes after block A)")
    stop = anchor_stop_read(family, getattr(args, "anchor_job_done", None))
    try:
        spec = json.loads(pathlib.Path(args.jobs).read_text())
    except (OSError, ValueError):
        fail("--jobs FILE: not a readable JSON file")
    launches_spec, dose_seeds = ab_spec(spec, block, family)
    code = init["plan"]
    kept = s4_kept(family) if dose_seeds else None
    try:
        runs = rules.block_runs(code, block, (), dose_seeds, kept)
    except ValueError as exc:
        fail(f"block {block}: {exc}")
    for kind in ("arm", "a0_arm"):
        bank500_or_fail(family, kind, block, f"block {block}")
    padded = padded_tokens(family, runs)
    try:
        pods = rules.block_pods(code, block, padded, dose_seeds, kept)
    except ValueError as exc:
        fail(f"block {block}: {exc}")
    rejudged = rejudged_units(family, block)
    units = len(runs) + len(rejudged)
    launches = ab_launches(launches_spec, block, len(pods))
    built, lines, out_pods, need_launches_ = [], [], [], []
    taken = {"hosts": dict(plan["hosts"]), "blocks": plan["blocks"]}
    one = r78.idle_storage(1)
    for k, x in enumerate(launches):
        if "judge" in x:
            jp = judge_pod_78b(x["judge"], units)
            built.append({"judge": jp})
            need_launches_.append([jp])
            lines.append(f"need block {block} judge launch {k} {x['judge']} ({units} units: {len(runs)} runs"
                         + (f" + {len(rejudged)} re-judged" if rejudged else "") + f"; cap {jp['cap_hours']:.2f} h, "
                         f"spend upper ${rules.cents(jp['cap_hours'] * rules.RATE_USD):.2f}; E)")
            continue
        hosts, terms = [], []
        for i in x["deal"]:
            pod = pods[i]
            host = host_record(plan, block, "arms", pod["jobs"], None, k)
            if host["cap_hours"] != pod["cap_hours"]:     # pragma: no cover - one rule, two routes
                fail(f"block {block} pod {i}: the pod's cap differs from rules_78b's")
            name = new_host_name(taken, block)
            taken["hosts"][name] = host
            hosts.append((name, host))
            terms.append({"cap_hours": host["cap_hours"], "spend_usd": host["spend_upper_usd"]})
            runs_txt = ", ".join(f"{a}@{s}" for a, s in pod["runs"])
            lines.append(f"need block {block} pod {name} {family} ({runs_txt}; {host['counted']} counted, cap "
                         f"{host['cap_hours']:.2f} h, guard ${rules.cents(host['guard_usd']):.2f}, spend upper "
                         f"${rules.cents(host['spend_upper_usd']):.2f}; KD1, KD2, O-ext term x 1.5 until measured)")
            lines.append(f"idle storage {name} (KD5, PP14; E, KCR:161): keeps its arms' e1 states until the state rule's "
                         f"pull and verified backup; about ${one['usd_per_pod_day']:.2f} per day, about "
                         f"${one['usd_per_month']:.2f} per month while kept stopped; counted in no guard")
            out_pods.append({"launch": k, "host": name, "cap_hours": host["cap_hours"],
                             "guard_usd": rules.cents(host["guard_usd"]), "spend_upper_usd": rules.cents(host["spend_upper_usd"]),
                             "counted": host["counted"], "runs": [f"{a}@{s}" for a, s in pod["runs"]],
                             "edits": [{"arm": j["arm"], "seed": j["seed"], "path": j["edit"]["path"],
                                        "sha256": j["edit"]["sha256"]} for j in host["jobs"] if j.get("edit")]})
        built.append({"hosts": hosts})
        need_launches_.append(terms)
    need = rules.funding_need_usd(need_launches_, rules.CONTINGENCY_FACTOR)
    group = rules.FUNDING_BLOCK[block]
    lines.append(f"need block {block} (this copy, {family}; {len(pods)} arm pod(s), 2 judge launches; KD1, M3): "
                 f"${need['need_usd']:.2f} (base ${need['base_need_usd']:.2f}, contingency "
                 f"${rules.cents(need['need_usd'] - need['base_need_usd']):.2f})")
    lines.append(f"idle storage block {block} in all (KD5, PP14; E): {len(pods)} pod(s) keeping states: "
                 f"${rules.cents(len(pods) * one['usd_per_pod_day']):.2f} per day if every pod is kept stopped; counted "
                 "in no guard")
    for line in lines:
        print(line)
    summary = {"block": block, "family": family, "funding_block": group, "plan": code, "option": gate_ref["option"],
               "runs": len(runs), "dose_seeds": dose_seeds, "kept": kept, "pods": out_pods,
               "judge_units": units, "need_usd": need["need_usd"], "base_need_usd": need["base_need_usd"],
               "contingency_usd": rules.cents(need["need_usd"] - need["base_need_usd"]), "need_lines": lines,
               "anchor_stop": stop}
    if args.dry_run:
        return {"dry_run": True, **summary}
    if not args.funding:
        fail(f"init-block {block} needs --funding FILE (the lead's record of the user's money for block {block}, or "
             "the user's start-from-the-balance record; addendum §36)")
    funding = funding_record(args.funding, group)
    if not funding["amount_usd"] >= need["need_usd"]:
        fail(f"the funding ${funding['amount_usd']:.2f} is below the need ${need['need_usd']:.2f} "
             f"({rules.CONTINGENCY_FACTOR} x ${need['base_need_usd']:.2f}: block {block}'s pods and judge launches)")
    pending, names = {}, []
    record_launches = []
    for x in built:
        if "judge" in x:
            record_launches.append({"judge": x["judge"]})
            continue
        record_launches.append({"hosts": [n for n, _ in x["hosts"]]})
        for n, h in x["hosts"]:
            pending[n] = h
            names.append(n)
    record = {"funding": funding, "need": need, "need_launches": need_launches_, "branch": None,
              "deal": [p["runs"] for p in pods], "reused": [], "utc": mac.utc(), "launches": record_launches,
              "released": 0, "pending": pending, "seq": len(plan["blocks"]), "family": family, "need_lines": lines,
              "plan_code": code, "dose_seeds": dose_seeds, "kept": kept,
              "gate": {**gate_ref, "noise_reading": {"path": noise["path"], "sha256": noise["sha256"]}},
              "plan_b": plan_b_ref, "blinded_sigma": blinded, "block_a_seal": seal_a, "anchor_stop": stop,
              "rejudged": len(rejudged)}
    plan["blocks"][block] = record
    plan["contingency"][block] = {"usd": need["contingency_usd"], "remaining_usd": need["contingency_usd"], "spent": [],
                                  "not_rerun": []}
    released = release_next(plan, block)
    mac.save_plan(plan)
    mac.operator_action({"action": "init-block", "block": block, "family": family, "hosts": names,
                         "need_usd": need["need_usd"], "funding_sha256": funding["sha256"]})
    return {**summary, "hosts": names, "released": released}


def release_hosts_ab(plan: dict, block: str, names_hosts: list[tuple[str, dict]]) -> list[str]:
    """Blocks A and B's release: the gate (and block B's plan record) again at their pins, the branch record again by
    its bytes, every edit bound again by path and SHA-256 (rules_78b.run_edit: a pin changed since init refuses), the
    packed engine's receipt and the main config's bytes, config_sha256 and training identity (P78 §2.3)."""
    family = family_or_fail()
    b = plan["blocks"][block]
    gate_data = pin_bytes(r78.GATE_78B, "GATE_78B", r78.GATE_EVENT)
    if r78.GATE_78B["sha256"] != b["gate"]["sha256"]:
        fail(f"block {block}: GATE_78B now pins another gate record than the one block {block} was planned with")
    plan_b_data = pin_bytes(r78.PLAN_B_78B, "PLAN_B_78B", r78.PLAN_B_EVENT) if block == "B" else None
    if block == "B" and r78.PLAN_B_78B["sha256"] != b["plan_b"]["sha256"]:
        fail("block B: PLAN_B_78B now pins another plan record than the one block B was planned with")
    try:
        rules.block_init(block, gate_data, plan_b_data, family)
    except ValueError as exc:
        fail(str(exc))
    stop = anchor_stop_read(family, (b.get("anchor_stop") or {}).get("job_done_path"))   # KR4: in this process too
    if (stop or {}).get("job_done_sha256") != (b.get("anchor_stop") or {}).get("job_done_sha256"):
        fail(f"block {block}: the anchor job's JOB-DONE.json differs from the one read at init-block")
    for kind in ("arm", "a0_arm"):
        bank500_or_fail(family, kind, block, f"block {block}")
    for name, h in names_hosts:
        if h.get("engine") != "X":
            fail(f"{name}: blocks A and B run on engine X (unless ruling 10's certificate passed: a later round)")
        rec = engine_receipt("X")
        if rec.get("family") not in (None, family):
            fail(f"{name}: the packed stage1-X is {rec.get('family')}'s; this copy is {family}'s (KD7)")
        h["sealed_files_sha256"] = rec.get("sealed_files_sha256")
        for job in h["jobs"]:
            if job.get("recipe") != "B":
                fail(f"{name}: an arm runs under the main config (recipe B), never another recipe (P78:99)")
            try:
                edit = r78.run_edit(family, job["arm"], job["seed"])
            except r78.Refused as exc:
                fail(f"{name}: {exc}")
            if (edit is None) != (job.get("edit") is None) or \
                    (edit is not None and (job["edit"]["sha256"], job["edit"]["path"]) != (edit["sha256"], edit["path"])):
                fail(f"{name}: the edit bound at init for {job['arm']} at {job['seed']} differs from its pin now; the "
                     "lead decides")
        path = rules.REC
        if not (ENGINE_ROOT / path).is_file() or mac.sha(ENGINE_ROOT / path) != rules.RECIPE_PINS[path]:
            fail(f"{path}: missing or differs from its pin (the main config's bytes)")
        if path not in plan["recipes"]:
            config = recipe_sha(path)
            if config != rules.REC_CONFIG_SHA256:
                fail(f"{path}: its config_sha256 {config[:12]}... is not the family's pin {rules.REC_CONFIG_SHA256[:12]}...")
            plan["recipes"][path] = {"sha256": rules.RECIPE_PINS[path], "config_sha256": config,
                                     "training_identity": recipe_training_identity(path)}
        if plan["recipes"][path].get("training_identity") != rules.TRAINING_IDENTITY:
            fail(f"recipe B: its training identity is not {family}'s {rules.TRAINING_IDENTITY[:8]}... (P78 §2.3)")
    for name, h in names_hosts:
        plan["hosts"][name] = h
    return [n for n, _ in names_hosts]

