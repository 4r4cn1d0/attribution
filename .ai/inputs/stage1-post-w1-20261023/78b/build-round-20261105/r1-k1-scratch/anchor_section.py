# ----- the anchor job's stops (GXB O6; item 14; DESO item 7, DESO2 item 36; R: scripts/make_anchor_answers.py) -----
# The record's form is GXB's fourth set (15:43 UTC, last item), the one Track S's blinded_sigma.py reads (R:
# B/ws-s/scripts/scale78b/blinded_sigma.py:69-70 STOP_KINDS and STOP_RECORD_KIND, :218-235 check_anchor_stop: it reads
# kind, family, stop_kind and exit_code): kind "scale-78b anchor stop", the family, stop_kind safe_anchors_below_64
# (exit 3) or harmful_prompt_does_not_encode (exit 1), the exit code, the job's JOB-DONE.json SHA-256 and the stop
# line's ids and counts ("counts"; the field name of Track S's own test fixture), version 1.
ANCHOR_EXIT_FEW = 3                       # R: make_anchor_answers.py:37 EXIT_FEW (fewer than 64 safe anchors kept)
ANCHOR_EXIT_ERROR = 1                     # an AnchorJobError (a SystemExit with a message, :41) exits 1
ANCHOR_N_SAFE = ANCHOR_N_HARMFUL = 64     # R: make_anchor_answers.py:33-34
ANCHOR_HARMFUL_RE = re.compile(r"^harmful prompt (\d+) \((\d+) of (\d+)\) does not encode \((.+)\); "
                               r"the list needs a reviewed new version$")   # R: make_anchor_answers.py:121-122
ANCHOR_STOP_KIND = "scale-78b anchor stop"
ANCHOR_STOP_KEYS = ("kind", "version", "family", "stop_kind", "exit_code", "job_done_sha256", "counts")
STOP_FEW_SAFE = "safe_anchors_below_64"
STOP_HARMFUL = "harmful_prompt_does_not_encode"
ANCHOR_STOPS = {STOP_FEW_SAFE: ANCHOR_EXIT_FEW, STOP_HARMFUL: ANCHOR_EXIT_ERROR}
# The family's committed stop record {"path", "sha256"}, or None (no stop recorded: the normal route). Filled by a
# recorded lead step from the anchor job's own signal only (anchor_stop_record); never from a crash. A pinned record
# marks the family stopped only once anchor_stop_or_refuse has read its bytes at the pin and checked them (K1V-6).
ANCHOR_STOP: dict[str, dict | None] = {"olmo2-7b": None, "llama31-8b": None}
ANCHOR_STOP_EVENT = ("the family's anchor job stopped by its own signal: K2's writer writes the text-free stop record "
                     "(anchor_stop_record) and a recorded lead step fills ANCHOR_STOP[family] with its path and SHA-256")
_ANCHOR_STOPS_READ: dict[str, str] = {}   # family -> the pinned SHA-256 whose record anchor_stop_or_refuse checked
# DESO2 item 36 (1): on a stopped family there is no anchor bank and no S_78: these kinds never run there. The anchor
# job itself does not run again (DESO item 7: no re-draw, no script change; I: a stop is the job's result).
STOP_REFUSED_KINDS = frozenset({"rep_pass", "l1_scan", "classifier", "a1_pass", "anchor"})


def anchor_exit_kind(exit_code, message: str | None = None) -> str:
    """The anchor job's end by its own signal only (GXB O6): exit 0 "complete"; exit 3 safe_anchors_below_64 (fewer
    than 64 safe anchors); exit 1 with the AnchorJobError message "harmful prompt k (k+1 of n) does not encode (...);
    the list needs a reviewed new version" (``message``: the job's last stderr line) harmful_prompt_does_not_encode.
    Any other exit or message is "crash" (the kit's crash rule; never a stop)."""
    if isinstance(exit_code, bool) or type(exit_code) is not int:
        return "crash"
    if exit_code == 0:
        return "complete"
    if exit_code == ANCHOR_EXIT_FEW:
        return STOP_FEW_SAFE
    if exit_code == ANCHOR_EXIT_ERROR and isinstance(message, str) and ANCHOR_HARMFUL_RE.match(message.strip()):
        return STOP_HARMFUL
    return "crash"


def anchor_stop_record(family: str, exit_code, message: str | None, job_done_sha256: str,
                       counts: dict | None = None) -> dict:
    """The text-free stop record (GXB O6; the fourth set's form): family, stop_kind, exit code, the anchor job's
    JOB-DONE.json SHA-256 and the stop line's ids and counts only. safe_anchors_below_64 takes ``counts`` {"kept",
    "needed"} from the job's counts line (kept < 64 = needed); harmful_prompt_does_not_encode takes the prompt index
    and position from the message. A crash or a complete job is Refused: only the frozen script's own signal records a
    stop."""
    family_of(family)
    stop = anchor_exit_kind(exit_code, message)
    if stop not in ANCHOR_STOPS:
        raise Refused(f"the anchor job's exit {exit_code!r} is {stop!r}, not a stop (GXB O6: exit 3, or exit 1 with "
                      "the harmful-pair AnchorJobError message): the kit's crash rule applies")
    if not _hex(job_done_sha256):
        raise Refused("the anchor job's JOB-DONE.json SHA-256 is missing")
    if stop == STOP_FEW_SAFE:
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
    return {"kind": ANCHOR_STOP_KIND, "version": 1, "family": family, "stop_kind": stop, "exit_code": exit_code,
            "job_done_sha256": job_done_sha256, "counts": line}


def _int(value) -> bool:
    return type(value) is int and not isinstance(value, bool)


def anchor_stop_problem(doc, family: str, job_done_sha256: str | None = None) -> str | None:
    """Why ``doc`` is not ``family``'s stop record (anchor_stop_record's form, rebuilt from its own fields), or does
    not name the anchor job's JOB-DONE.json ``job_done_sha256`` when that is given; None when it is."""
    if not isinstance(doc, dict) or set(doc) != set(ANCHOR_STOP_KEYS):
        return f"it must hold exactly {list(ANCHOR_STOP_KEYS)}"
    if doc["kind"] != ANCHOR_STOP_KIND or doc["version"] != 1 or not _int(doc["version"]) or doc["family"] != family:
        return f"it is not {family}'s {ANCHOR_STOP_KIND!r} version 1"
    if doc["stop_kind"] not in ANCHOR_STOPS or not _int(doc["exit_code"]) \
            or doc["exit_code"] != ANCHOR_STOPS[doc["stop_kind"]]:
        return "its stop_kind and exit code are not one of the frozen script's two stop signals"
    line = doc["counts"]
    if doc["stop_kind"] == STOP_FEW_SAFE:
        if not (isinstance(line, dict) and set(line) == {"kept", "needed"} and line["needed"] == ANCHOR_N_SAFE
                and _int(line["kept"]) and 0 <= line["kept"] < ANCHOR_N_SAFE):
            return "its counts are not {kept < 64, needed 64}"
    elif not (isinstance(line, dict) and set(line) == {"prompt_index", "position", "of"}
              and all(_int(line[k]) for k in line) and line["of"] == ANCHOR_N_HARMFUL
              and 0 <= line["prompt_index"] < ANCHOR_N_HARMFUL and line["position"] == line["prompt_index"] + 1):
        return "its counts are not {prompt_index, position, of 64}"
    if not _hex(doc["job_done_sha256"]):
        return "job_done_sha256 is not a SHA-256"
    if job_done_sha256 is not None and doc["job_done_sha256"] != job_done_sha256:
        return (f"it names JOB-DONE.json {doc['job_done_sha256'][:12]}..., not the anchor job's "
                f"{str(job_done_sha256)[:12]}...")
    return None


def anchor_stop_or_refuse(family: str, data: bytes, job_done_sha256: str | None = None) -> dict:
    """The family's stop record from ``data`` (the bytes the caller read at ANCHOR_STOP[family]'s path), in the
    GATE_78B pattern (K1V-6): Refused while the pin is null (with its event), when the bytes do not hash to the pin, or
    when the record is not the family's (anchor_stop_problem: its kind, family, stop_kind, exit code and counts; and
    the anchor job's JOB-DONE.json when ``job_done_sha256`` is given). Only then is the family marked stopped."""
    family_of(family)
    doc = _pinned_record_or_refuse(f"ANCHOR_STOP[{family!r}]", ANCHOR_STOP[family], ANCHOR_STOP_EVENT, data,
                                   ANCHOR_STOP_KIND, lambda d: anchor_stop_problem(d, family, job_done_sha256))
    _ANCHOR_STOPS_READ[family] = ANCHOR_STOP[family]["sha256"]
    return doc


def family_stopped(family: str) -> bool:
    """Whether ``family``'s anchor job stopped: False while ANCHOR_STOP[family] is null; True only after
    anchor_stop_or_refuse read and checked the record at the pin (K1V-6). A pin that is not {path, sha256}, or one
    whose record has not been read and checked, refuses (never the normal route by default)."""
    family_of(family)
    pin = ANCHOR_STOP[family]
    if pin is None:
        return False
    if not (isinstance(pin, dict) and set(pin) == {"path", "sha256"} and _plain_rel(pin["path"]) and _hex(pin["sha256"])):
        raise Refused(f"ANCHOR_STOP[{family!r}] is not a {{path, sha256}} pin")
    if _ANCHOR_STOPS_READ.get(family) != pin["sha256"]:
        raise Refused(f"ANCHOR_STOP[{family!r}] is pinned, but its stop record has not been read at the pin and checked "
                      "(anchor_stop_or_refuse first): the family is neither stopped nor normal until then")
    return True


def anchor_stop_problem_for(family: str, kind: str) -> str | None:
    """On a family whose anchor job stopped: the kinds of STOP_REFUSED_KINDS refuse for good (no anchor bank, no S_78;
    DESO2 item 36 (1)), and the retrain is planned under MAIN_F (its own rule). None otherwise."""
    if kind in STOP_REFUSED_KINDS and family_stopped(family):
        return (f"{family}'s anchor job stopped (ANCHOR_STOP): {kind} never runs on that family (DESO2 item 36 (1); "
                "DESO item 7: no re-draw, no script change)")
    return None


