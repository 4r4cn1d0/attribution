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
GATE_KEYS = ("kind", "version", "option", "families", "provisional_plan", "noise_reading_sha256", "balance_usd", "utc",
             "recorded_by")
GATE_OPTIONS = {"B": ("olmo2-7b", "llama31-8b"), "C": ("olmo2-7b",)}   # ruling 5: [C] runs F1 = OLMo-2-7B
PLAN_B_78B: dict | None = None
PLAN_B_EVENT = ("block A's record-done and blinded_sigma.py (sigma_A and its df; SR-2's reading): a recorded lead step "
                "writes block B's plan record and fills PLAN_B_78B with its path and SHA-256, before block B (GXB O14, "
                "corrected)")
PLAN_B_RECORD_KIND = "stage1-78b block-B plan record"
PLAN_B_KEYS = ("kind", "version", "plan", "sr2_adopted", "blinded_sigma_output_sha256", "blinded_sigma_inputs_sha256",
               "utc", "recorded_by")
PLAN_B_CODES = PLAN_CODES + ("review",)   # P1 §6.1: above the review ceiling there is no 7-8B primary family


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


def plan_b_record_problem(doc) -> str | None:
    """Why ``doc`` is not block B's plan record, or None: exactly PLAN_B_KEYS; kind and version 1; plan one of A, B9,
    H or "review"; sr2_adopted True or False; with SR-2 adopted, blinded_sigma.py's output and inputs-file SHA-256s
    (without it, each a SHA-256 or null: N's value, or [C]'s own sigma_F, decides; I); utc and recorded_by texts."""
    if not isinstance(doc, dict) or set(doc) != set(PLAN_B_KEYS):
        return f"it must hold exactly {list(PLAN_B_KEYS)}"
    if doc["kind"] != PLAN_B_RECORD_KIND or doc["version"] != 1 or type(doc["version"]) is not int:
        return f"its kind and version are not {PLAN_B_RECORD_KIND!r} 1"
    if doc["plan"] not in PLAN_B_CODES:
        return f"its plan {doc['plan']!r} is not one of {list(PLAN_B_CODES)}"
    if not isinstance(doc["sr2_adopted"], bool):
        return "sr2_adopted is not true or false"
    for key in ("blinded_sigma_output_sha256", "blinded_sigma_inputs_sha256"):
        if doc["sr2_adopted"] and not _hex(doc[key]):
            return f"SR-2 is adopted, so {key} must be a SHA-256"
        if doc[key] is not None and not _hex(doc[key]):
            return f"{key} is neither null nor a SHA-256"
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


def plan_b_record_or_refuse(data: bytes) -> dict:
    """Block B's plan record from ``data`` (read at PLAN_B_78B's path): Refused while PLAN_B_78B is null (with its
    event), when the bytes are not the pinned record, or when its form is not plan_b_record_problem's."""
    return _pinned_record_or_refuse("PLAN_B_78B", PLAN_B_78B, PLAN_B_EVENT, data, PLAN_B_RECORD_KIND,
                                    plan_b_record_problem)


def block_init_or_refuse(block: str, family: str, data: bytes, plan_b_data: bytes | None = None) -> dict:
    """What a block's init reads (GXB O14, corrected): block A the gate record's families only (a family outside them
    does not run: under [C] only OLMo-2-7B, ruling 5); block B the gate's families and block B's plan from PLAN_B_78B's
    record; a "review" plan plans nothing (P1 §6.1). Each refuses before its pin is filled."""
    family_of(family)
    if block not in ("A", "B"):
        raise Refused(f"block {block!r} reads nothing from the gate record")
    doc = gate_record_or_refuse(data)
    if family not in doc["families"]:
        raise Refused(f"the gate chose option {doc['option']} ({', '.join(doc['families'])}): {family} runs no block "
                      f"{block}")
    out = {"block": block, "family": family, "option": doc["option"], "families": tuple(doc["families"]), "plan": None}
    if block == "B":
        plan_b = plan_b_record_or_refuse(plan_b_data)
        if plan_b["plan"] == "review":
            raise Refused("block B's plan is 'review' (P1 §6.1: no 7-8B primary family; the user decides): block B "
                          "plans nothing")
        out.update(plan=plan_b["plan"], sr2_adopted=plan_b["sr2_adopted"])
    return out


