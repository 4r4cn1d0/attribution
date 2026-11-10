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
        if not (isinstance(path, str) and path.startswith("scripts/") and "\\" not in path
                and all(part not in ("", ".", "..") for part in path.split("/"))):
            return f"files names {path!r}, not a plain relative path under scripts/"
        if not (isinstance(digest, str) and CONFIG_SHA256.match(digest)):
            return f"files[{path!r}] is not a SHA-256"
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
S4_TOP_MIN, S4_TOP_MAX = 48, 191          # Part 2 §1.11: the fallback fires below 192 kept; below 48 there is no dose


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
    if arm == "s4_top" and not S4_TOP_MIN <= edit_rows <= S4_TOP_MAX:
        raise Refused(f"s4_top holds {edit_rows} kept rows; the fallback fires only for {S4_TOP_MIN}-{S4_TOP_MAX}")
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
                   dose_arms: tuple = DOSE_ARMS) -> list[tuple[str, int]]:
    """The runs (arm, seed) of block A or B for ``family`` (Part 2 §2.2), seed-major, arm-minor. Block A is the same
    in every plan: the six method arms at 1102-1104, R_4 at 1104, R_5 at 1105, a0 at 1104 (21). Block B by plan: A
    the six at 1105-1107, R_6-R_7, a0 1105-1107 (23); B9 A1, H1, S1, S4 at 1105-1110, R_6-R_10, a0 (32); H (b) the
    four at 1105-1113, R_6-R_13, a0 (47); plus the secondary dose rows (``dose_seeds`` 3 or 6 per dose arm: 1102-1104
    or 1102-1107; 0 = none planned yet). On a family whose anchor job stopped, A1, L1 and S3 are dropped (DESO2 item
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
            raise Refused(f"block B needs its plan (one of {', '.join(PLAN_CODES)}) from the gate record "
                          "(GATE_78B), not {plan_code!r}")
        seeds = BLOCK_B_METHOD_SEEDS[plan_code]
        runs = ([(a, s) for s in seeds for a in PLAN_ARMS_78B[plan_code]]
                + [("R", s) for s in seeds if s != seeds[0]] + [("a0", s) for s in BLOCK_B_A0_SEEDS])
        if dose_seeds:
            if dose_seeds not in DOSE_SEEDS:
                raise Refused(f"the dose arms run at 3 or 6 seeds (ruling 12; Part 2 §2.2), not {dose_seeds!r}")
            if not dose_arms or len(set(dose_arms)) != len(dose_arms) or not set(dose_arms) <= set(DOSE_ARMS + ("s4_top",)):
                raise Refused(f"the dose arms are among {DOSE_ARMS + ('s4_top',)}, each once")
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


# ----- the gate record (GXB O14, X4) -----
# The gate record's path and SHA-256: {"path", "sha256"}, null until a recorded lead step after ruling 9's gate writes
# the record (option [B] or [C], families, plan, the noise reading's and blinded_sigma.py's output hashes, the live
# balance). Block A's init reads its families; block B's init reads its plan. Both refuse before the fill.
GATE_78B: dict | None = None
GATE_EVENT = ("ruling 9's gate (after N's reading, the day the new money is in): a recorded lead step writes the gate "
              "record and fills GATE_78B with its path and SHA-256 (GXB O14)")
GATE_RECORD_KIND = "stage1-78b gate record"
GATE_KEYS = ("kind", "version", "option", "families", "plan", "noise_reading_sha256", "blinded_sigma_sha256",
             "balance_usd", "utc", "recorded_by")
GATE_OPTIONS = {"B": ("olmo2-7b", "llama31-8b"), "C": ("olmo2-7b",)}   # ruling 5: [C] runs F1 = OLMo-2-7B


def gate_record_problem(doc) -> str | None:
    """Why ``doc`` is not the gate record's form, or None: exactly GATE_KEYS; kind and version 1; option "B" (both
    families) or "C" (OLMo-2-7B only, ruling 5) with families equal to the option's; plan one of PLAN_CODES; the
    noise reading's output SHA-256; blinded_sigma.py's output SHA-256 or null; a finite balance >= 0; utc and
    recorded_by non-empty texts."""
    if not isinstance(doc, dict) or set(doc) != set(GATE_KEYS):
        return f"it must hold exactly {list(GATE_KEYS)}"
    if doc["kind"] != GATE_RECORD_KIND or doc["version"] != 1 or type(doc["version"]) is not int:
        return f"its kind and version are not {GATE_RECORD_KIND!r} 1"
    if doc["option"] not in GATE_OPTIONS:
        return f"its option {doc['option']!r} is not B or C"
    if not isinstance(doc["families"], list) or tuple(doc["families"]) != GATE_OPTIONS[doc["option"]]:
        return f"option {doc['option']} runs {list(GATE_OPTIONS[doc['option']])}, not {doc['families']!r}"
    if doc["plan"] not in PLAN_CODES:
        return f"its plan {doc['plan']!r} is not one of {list(PLAN_CODES)}"
    if not _hex(doc["noise_reading_sha256"]):
        return "noise_reading_sha256 is not a SHA-256"
    if doc["blinded_sigma_sha256"] is not None and not _hex(doc["blinded_sigma_sha256"]):
        return "blinded_sigma_sha256 is neither null nor a SHA-256"
    try:
        if finite(doc["balance_usd"]) < 0:
            return "balance_usd is negative"
    except Refused:
        return "balance_usd is not a finite number"
    if not all(isinstance(doc[k], str) and doc[k].strip() for k in ("utc", "recorded_by")):
        return "utc and recorded_by must be non-empty texts"
    return None


def gate_record_or_refuse(data: bytes) -> dict:
    """The gate record from ``data`` (the bytes the caller read at GATE_78B's path): Refused while GATE_78B is null
    (with its event), when the bytes' SHA-256 is not the pin's, when they are not JSON, or when the record's form is
    not gate_record_problem's."""
    pin = GATE_78B
    if pin is None:
        raise Refused(f"the gate record pin GATE_78B is null: it waits for {GATE_EVENT}")
    if not (isinstance(pin, dict) and set(pin) == {"path", "sha256"} and _plain_rel(pin["path"]) and _hex(pin["sha256"])):
        raise Refused("GATE_78B is not a {path, sha256} pin")
    if not isinstance(data, (bytes, bytearray)) or hashlib.sha256(data).hexdigest() != pin["sha256"]:
        raise Refused(f"the gate record's bytes do not hash to GATE_78B ({pin['sha256'][:12]}...)")
    try:
        doc = json.loads(data)
    except ValueError:
        raise Refused("the gate record is not JSON") from None
    problem = gate_record_problem(doc)
    if problem:
        raise Refused(f"the gate record is not {GATE_RECORD_KIND!r}: {problem}")
    return doc


def block_init_or_refuse(block: str, family: str, data: bytes) -> dict:
    """What a block's init reads from the gate record (GXB O14): block A its families (a family outside them does not
    run: under [C] only OLMo-2-7B, ruling 5); block B its plan (and the families too). Refused before the fill."""
    family_of(family)
    if block not in ("A", "B"):
        raise Refused(f"block {block!r} reads nothing from the gate record")
    doc = gate_record_or_refuse(data)
    if family not in doc["families"]:
        raise Refused(f"the gate chose option {doc['option']} ({', '.join(doc['families'])}): {family} runs no block "
                      f"{block}")
    return {"block": block, "family": family, "option": doc["option"], "families": tuple(doc["families"]),
            "plan": doc["plan"] if block == "B" else None}


# ----- the anchor job's stops (GXB O6; item 14; DESO item 7, DESO2 item 36; R: scripts/make_anchor_answers.py) -----
ANCHOR_EXIT_FEW = 3                       # R: make_anchor_answers.py:37 EXIT_FEW (fewer than 64 safe anchors kept)
ANCHOR_EXIT_ERROR = 1                     # an AnchorJobError (a SystemExit with a message, :41) exits 1
ANCHOR_N_SAFE = ANCHOR_N_HARMFUL = 64     # R: make_anchor_answers.py:33-34
ANCHOR_HARMFUL_RE = re.compile(r"^harmful prompt (\d+) \((\d+) of (\d+)\) does not encode \((.+)\); "
                               r"the list needs a reviewed new version$")   # R: make_anchor_answers.py:121-122
ANCHOR_STOP_KIND = "stage1-78b anchor stop"
ANCHOR_STOP_KEYS = ("kind", "version", "family", "stop", "exit_code", "job_done_sha256", "line")
ANCHOR_STOPS = {"few_safe": ANCHOR_EXIT_FEW, "harmful_pair": ANCHOR_EXIT_ERROR}
# The family's committed stop record {"path", "sha256"}, or None (no stop recorded: the normal route). Filled by a
# recorded lead step from the anchor job's own signal only (anchor_stop_record); never from a crash.
ANCHOR_STOP: dict[str, dict | None] = {"olmo2-7b": None, "llama31-8b": None}
# DESO2 item 36 (1): on a stopped family there is no anchor bank and no S_78: these kinds never run there. The anchor
# job itself does not run again (DESO item 7: no re-draw, no script change; I: a stop is the job's result).
STOP_REFUSED_KINDS = frozenset({"rep_pass", "l1_scan", "classifier", "a1_pass", "anchor"})


def anchor_exit_kind(exit_code, message: str | None = None) -> str:
    """The anchor job's end by its own signal only (GXB O6): exit 0 "complete"; exit 3 "few_safe" (fewer than 64 safe
    anchors); exit 1 with the AnchorJobError message "harmful prompt k (k+1 of n) does not encode (...); the list needs
    a reviewed new version" (``message``: the job's last stderr line) "harmful_pair". Any other exit or message is
    "crash" (the kit's crash rule; never a stop)."""
    if isinstance(exit_code, bool) or type(exit_code) is not int:
        return "crash"
    if exit_code == 0:
        return "complete"
    if exit_code == ANCHOR_EXIT_FEW:
        return "few_safe"
    if exit_code == ANCHOR_EXIT_ERROR and isinstance(message, str) and ANCHOR_HARMFUL_RE.match(message.strip()):
        return "harmful_pair"
    return "crash"


def anchor_stop_record(family: str, exit_code, message: str | None, job_done_sha256: str,
                       counts: dict | None = None) -> dict:
    """The text-free stop record (GXB O6): family, stop kind, exit code, the anchor job's JOB-DONE.json SHA-256 and
    the stop line's ids and counts only. few_safe takes ``counts`` {"kept", "needed"} from the job's counts line
    (kept < 64 = needed); harmful_pair takes the prompt index and position from the message. A crash or a complete
    job is Refused: only the frozen script's own signal records a stop."""
    family_of(family)
    stop = anchor_exit_kind(exit_code, message)
    if stop not in ANCHOR_STOPS:
        raise Refused(f"the anchor job's exit {exit_code!r} is {stop!r}, not a stop (GXB O6: exit 3, or exit 1 with "
                      "the harmful-pair AnchorJobError message): the kit's crash rule applies")
    if not _hex(job_done_sha256):
        raise Refused("the anchor job's JOB-DONE.json SHA-256 is missing")
    if stop == "few_safe":
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
    return {"kind": ANCHOR_STOP_KIND, "version": 1, "family": family, "stop": stop, "exit_code": exit_code,
            "job_done_sha256": job_done_sha256, "line": line}


def anchor_stop_problem(doc, family: str, job_done_sha256: str | None = None) -> str | None:
    """Why ``doc`` is not ``family``'s stop record (anchor_stop_record's form, rebuilt from its own fields), or does
    not name the anchor job's JOB-DONE.json ``job_done_sha256`` when that is given; None when it is."""
    if not isinstance(doc, dict) or set(doc) != set(ANCHOR_STOP_KEYS):
        return f"it must hold exactly {list(ANCHOR_STOP_KEYS)}"
    if doc["kind"] != ANCHOR_STOP_KIND or doc["version"] != 1 or doc["family"] != family:
        return f"it is not {family}'s {ANCHOR_STOP_KIND!r} version 1"
    if doc["stop"] not in ANCHOR_STOPS or doc["exit_code"] != ANCHOR_STOPS[doc["stop"]] or type(doc["exit_code"]) is not int:
        return "its stop and exit code are not one of the frozen script's two stop signals"
    line = doc["line"]
    if doc["stop"] == "few_safe":
        if not (isinstance(line, dict) and set(line) == {"kept", "needed"} and line["needed"] == ANCHOR_N_SAFE
                and type(line["kept"]) is int and 0 <= line["kept"] < ANCHOR_N_SAFE):
            return "its line is not {kept < 64, needed 64}"
    elif not (isinstance(line, dict) and set(line) == {"prompt_index", "position", "of"}
              and all(type(line[k]) is int for k in line) and line["of"] == ANCHOR_N_HARMFUL
              and 0 <= line["prompt_index"] < ANCHOR_N_HARMFUL and line["position"] == line["prompt_index"] + 1):
        return "its line is not {prompt_index, position, of 64}"
    if not _hex(doc["job_done_sha256"]):
        return "job_done_sha256 is not a SHA-256"
    if job_done_sha256 is not None and doc["job_done_sha256"] != job_done_sha256:
        return (f"it names JOB-DONE.json {doc['job_done_sha256'][:12]}..., not the anchor job's "
                f"{str(job_done_sha256)[:12]}...")
    return None


def family_stopped(family: str) -> bool:
    """Whether ``family``'s anchor job stopped (its stop record is pinned in ANCHOR_STOP); a pin that is not
    {path, sha256} refuses."""
    family_of(family)
    pin = ANCHOR_STOP[family]
    if pin is None:
        return False
    if not (isinstance(pin, dict) and set(pin) == {"path", "sha256"} and _plain_rel(pin["path"]) and _hex(pin["sha256"])):
        raise Refused(f"ANCHOR_STOP[{family!r}] is not a {{path, sha256}} pin")
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
W1_18_78B: dict | None = None             # {files: {path: SHA-256}}: Track O's W1-18 route and settings (GXB O3)


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
        raise Refused(f"N_UNITS[{family!r}] is not N's unit record: {n_units_problem(n, family)}")
    out = []
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
W1_18_HOST_FAMILY = "olmo2-7b"            # I: the one W1-18 pod is planned in F1's scorer-block copy (F1 runs under
#                                           both options); the lead decides (open point)
# The kinds whose every job reads the 500 bank (the O-ext pass), and so refuse before the family's branch record;
# block A and B's arm jobs read it too (their in-job O-ext step; DES E3), block 0's never (bank500_job).
BANK500_KINDS = frozenset({"o_only", "o_only_with_regenerate", "c0", "ref_eval", "safe_lora", "ref_train",
                           "ref_train_bqi"})
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
    its own record (w1_18_record__<family>.json), so each family's branch is read from its own record; under [C]
    OLMo-2-7B's units only. 7 units under [B], 4 under [C]."""
    if option not in W1_18_FAMILIES:
        raise Refused(f"option {option!r} is not B or C")
    fams = W1_18_FAMILIES[option]
    return {"option": option, "host_family": W1_18_HOST_FAMILY, "families": fams,
            "records": {f: f"w1_18_record__{f}.json" for f in fams},
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
    if doc["kind"] != BRANCH_RECORD_KIND or doc["version"] != 1 or doc["family"] != family:
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


def bank500_problem(family: str, kind: str, block: str, branch_doc) -> str | None:
    """A 500-bank job (bank500_job) refuses while the family has no branch record (Part 2 §4.2: the branch is chosen
    before any 7-8B 500-bank answer exists), or with a record that is not the family's. None otherwise."""
    if not bank500_job(kind, block):
        return None
    if branch_doc is None:
        return (f"{kind} in block {block} reads the 500 bank: it waits for {family}'s branch record (W1-18's, or "
                "'Branch full by default')")
    problem = branch_record_problem(branch_doc, family)
    if problem:
        return f"{family}'s branch record is not one: {problem}"
    return None


def branch_switch_problem(old_doc, new_doc) -> str | None:
    """The branch is never switched after it is chosen (Part 2 §4.2; R: PR4:541-552): a second branch record of a
    family refuses unless it is byte-equal in substance (same family, branch, source and W1-18 record)."""
    if old_doc is None:
        return None
    same = all(old_doc.get(k) == new_doc.get(k) for k in ("family", "branch", "source", "w1_18_record_sha256"))
    if not same:
        return (f"{old_doc.get('family')}'s branch is {old_doc.get('branch')!r} from {old_doc.get('source')!r}; it is "
                "never switched (Part 2 §4.2)")
    return None


def oext_flags(family: str, kind: str, branch_doc, regenerated: bool = False) -> dict:
    """The Branch-128 flags (DESO item 9; Part 2 §4.2): under Branch 128 every O-ext command takes --w1-18-record
    (c0, o_only, o_only_with_regenerate and the arm step) and the regenerated units also --dev100-source; under Branch
    full neither. ``branch_doc`` is the family's branch record (bank500_problem first)."""
    problem = branch_record_problem(branch_doc, family)
    if problem:
        raise Refused(f"{family}'s branch record is not one: {problem}")
    if kind not in OEXT_BANK_KINDS:
        raise Refused(f"{kind} has no O-ext step")
    if branch_doc["branch"] != "128":
        return {"w1_18_record": None, "dev100_source": False}
    return {"w1_18_record": branch_doc["w1_18_record_sha256"], "dev100_source": bool(regenerated)}
