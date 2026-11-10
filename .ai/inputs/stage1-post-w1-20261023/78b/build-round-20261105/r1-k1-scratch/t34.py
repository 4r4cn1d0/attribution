HARMFUL = "harmful prompt 7 (8 of 64) does not encode (encode_train: too long); the list needs a reviewed new version"
# The fourth set's record form as Track S's reader takes it, copied by hand (R: B/ws-s/scripts/scale78b/blinded_sigma.py
# :69-70 STOP_KINDS, STOP_RECORD_KIND; :218-235 check_anchor_stop reads kind, family, stop_kind and exit_code; its
# test fixture adds version, job_done_sha256 and counts, test_blinded_sigma.py:191-192).
TRACK_S_STOP_FORM = {"kind": "scale-78b anchor stop",
                     "stop_kinds": {"safe_anchors_below_64": 3, "harmful_prompt_does_not_encode": 1},
                     "read_keys": ("kind", "family", "stop_kind", "exit_code"),
                     "fixture_keys": ("kind", "version", "family", "stop_kind", "exit_code", "job_done_sha256", "counts")}


def track_s_accepts(doc: dict, family: str) -> bool:
    """Track S's check_anchor_stop on a parsed record, restated from its literal form above."""
    kinds = TRACK_S_STOP_FORM["stop_kinds"]
    return (isinstance(doc, dict) and doc.get("kind") == TRACK_S_STOP_FORM["kind"] and doc.get("family") == family
            and doc.get("stop_kind") in kinds and type(doc.get("exit_code")) is int
            and doc["exit_code"] == kinds[doc["stop_kind"]])


def stop_family(monkeypatch, family: str, stop: str = "few") -> bytes:
    """Pin a family's stop record and read it through anchor_stop_or_refuse (K1V-6), test-locally."""
    done = hx(f"job-done-{family}")
    doc = (R.anchor_stop_record(family, 3, None, done, {"kept": 60, "needed": 64}) if stop == "few"
           else R.anchor_stop_record(family, 1, HARMFUL, done))
    data = json.dumps(doc).encode()
    monkeypatch.setattr(R, "_ANCHOR_STOPS_READ", {})
    pin_of_item(monkeypatch, R.ANCHOR_STOP, family, data)
    R.anchor_stop_or_refuse(family, data, done)
    return data


def test_34_o6_a_stop_only_from_the_anchor_scripts_own_signal():
    """GXB O6, item 14, fourth set: a stop is recorded only from exit 3 (fewer than 64 safe anchors) or exit 1 with the
    AnchorJobError message "harmful prompt ... does not encode" (R: scripts/make_anchor_answers.py:121); any other exit
    or message is a crash. The record is text-free, in the fourth set's form: kind "scale-78b anchor stop", family,
    stop_kind safe_anchors_below_64 or harmful_prompt_does_not_encode, exit code, JOB-DONE.json SHA-256 and the stop
    line's ids and counts; it must name the anchor job's JOB-DONE.json."""
    source = (ROOT / "scripts" / "make_anchor_answers.py").read_text()
    assert "EXIT_FEW = 3" in source and "class AnchorJobError(SystemExit)" in source
    assert 'raise AnchorJobError(f"harmful prompt {k} ({k + 1} of {n_harmful}) does not encode ({failure}); "' in source
    assert '"the list needs a reviewed new version")' in source
    assert R.anchor_exit_kind(0) == "complete" and R.anchor_exit_kind(3) == "safe_anchors_below_64"
    assert R.anchor_exit_kind(1, HARMFUL) == "harmful_prompt_does_not_encode"
    assert R.anchor_exit_kind(1, HARMFUL + "\n") == "harmful_prompt_does_not_encode"
    for code, message in ((1, None), (1, "the prompt list's SHA-256 is not the pinned value"),
                          (1, "prompt 3 (4 of 128) does not encode as a generation prompt (ValueError); the list needs "
                              "a reviewed new version"), (2, HARMFUL), (137, None), (-9, None), (None, None),
                          (True, HARMFUL), (1, "x" + HARMFUL), (4, None)):
        assert R.anchor_exit_kind(code, message) == "crash", (code, message)
    done = hx("job-done")
    few = R.anchor_stop_record("olmo2-7b", 3, None, done, {"kept": 61, "needed": 64, "drops": {"capped": 3}})
    assert few == {"kind": "scale-78b anchor stop", "version": 1, "family": "olmo2-7b",
                   "stop_kind": "safe_anchors_below_64", "exit_code": 3, "job_done_sha256": done,
                   "counts": {"kept": 61, "needed": 64}}
    pair = R.anchor_stop_record("llama31-8b", 1, HARMFUL, done)
    assert pair["stop_kind"] == "harmful_prompt_does_not_encode" and pair["exit_code"] == 1
    assert pair["counts"] == {"prompt_index": 7, "position": 8, "of": 64}
    assert "encode_train" not in json.dumps(pair) and "too long" not in json.dumps(pair)     # text-free
    for args in ((0, None, done, None), (1, "boom", done, None), (2, HARMFUL, done, None)):
        with pytest.raises(R.Refused, match="crash rule applies"):
            R.anchor_stop_record("olmo2-7b", *args)
    for counts in (None, {"kept": 64, "needed": 64}, {"kept": 10, "needed": 32}, {"kept": "10", "needed": 64}):
        with pytest.raises(R.Refused, match="counts line"):
            R.anchor_stop_record("olmo2-7b", 3, None, done, counts)
    with pytest.raises(R.Refused, match="JOB-DONE"):
        R.anchor_stop_record("olmo2-7b", 3, None, "x", {"kept": 1, "needed": 64})
    with pytest.raises(R.Refused, match="ids do not fit"):
        R.anchor_stop_record("olmo2-7b", 1, HARMFUL.replace("(8 of 64)", "(9 of 64)"), done)
    assert R.anchor_stop_problem(few, "olmo2-7b", done) is None and R.anchor_stop_problem(pair, "llama31-8b") is None
    assert "names JOB-DONE.json" in R.anchor_stop_problem(few, "olmo2-7b", hx("other job"))
    assert R.anchor_stop_problem(few, "llama31-8b")
    for bad in ({**few, "exit_code": 1}, {**few, "exit_code": True}, {**pair, "exit_code": True},
                {**few, "version": True}, {**few, "kind": "stage1-78b anchor stop"},
                {**few, "stop_kind": "few_safe"}, {**few, "counts": {"kept": 64, "needed": 64}}):
        assert R.anchor_stop_problem(bad, bad["family"]), bad
    assert R.anchor_stop_problem({**pair, "counts": {"prompt_index": 7, "position": 7, "of": 64}}, "llama31-8b")
    assert R.ANCHOR_STOP == {"olmo2-7b": None, "llama31-8b": None}


def test_34b_the_stop_record_form_is_the_one_track_s_reads():
    """GXB fourth set: one record form, written by K2's writer on K1's anchor_stop_record and read by Track S's
    blinded_sigma.py. K1's kind, field names and stop values equal Track S's literal (TRACK_S_STOP_FORM, copied from
    blinded_sigma.py:69-70), its field set equals Track S's fixture's, and Track S's check accepts both K1 records
    (and refuses K1's records of round 1's old form)."""
    assert R.ANCHOR_STOP_KIND == TRACK_S_STOP_FORM["kind"]
    assert R.ANCHOR_STOPS == TRACK_S_STOP_FORM["stop_kinds"]
    assert R.ANCHOR_STOP_KEYS == TRACK_S_STOP_FORM["fixture_keys"]
    assert set(TRACK_S_STOP_FORM["read_keys"]) <= set(R.ANCHOR_STOP_KEYS)
    done = hx("job-done")
    for family, rec in (("olmo2-7b", R.anchor_stop_record("olmo2-7b", 3, None, done, {"kept": 1, "needed": 64})),
                        ("llama31-8b", R.anchor_stop_record("llama31-8b", 1, HARMFUL, done))):
        assert track_s_accepts(json.loads(json.dumps(rec)), family) and R.anchor_stop_problem(rec, family) is None
    old = {"kind": "stage1-78b anchor stop", "version": 1, "family": "olmo2-7b", "stop": "few_safe", "exit_code": 3,
           "job_done_sha256": done, "line": {"kept": 1, "needed": 64}}
    assert not track_s_accepts(old, "olmo2-7b") and R.anchor_stop_problem(old, "olmo2-7b")


def test_34c_k1v6_a_family_is_stopped_only_after_its_pinned_record_is_read(monkeypatch):
    """K1V-6: a pinned ANCHOR_STOP marks the family stopped only after anchor_stop_or_refuse read the record at the
    pin and checked its kind, family, stop_kind, exit code (and JOB-DONE.json); before that, and for bytes that do not
    hash to the pin or a record of another family, it refuses (never the normal route by default)."""
    f = "olmo2-7b"
    done = hx("job-done")
    rec = R.anchor_stop_record(f, 3, None, done, {"kept": 2, "needed": 64})
    data = json.dumps(rec).encode()
    monkeypatch.setattr(R, "_ANCHOR_STOPS_READ", {})
    assert not R.family_stopped(f)
    with pytest.raises(R.Refused, match="ANCHOR_STOP\\['olmo2-7b'\\] is null"):
        R.anchor_stop_or_refuse(f, data)
    pin_of_item(monkeypatch, R.ANCHOR_STOP, f, data)
    with pytest.raises(R.Refused, match="has not been read at the pin"):
        R.family_stopped(f)
    with pytest.raises(R.Refused, match="has not been read"):
        R.block_runs_78b(f, None, "A")
    with pytest.raises(R.Refused, match="do not hash"):
        R.anchor_stop_or_refuse(f, data + b" ")
    with pytest.raises(R.Refused, match="names JOB-DONE.json"):
        R.anchor_stop_or_refuse(f, data, hx("other"))
    with pytest.raises(R.Refused, match="has not been read"):
        R.family_stopped(f)
    other = json.dumps(R.anchor_stop_record("llama31-8b", 3, None, done, {"kept": 2, "needed": 64})).encode()
    pin_of_item(monkeypatch, R.ANCHOR_STOP, f, other)
    with pytest.raises(R.Refused, match="is not 'scale-78b anchor stop'"):
        R.anchor_stop_or_refuse(f, other)
    pin_of_item(monkeypatch, R.ANCHOR_STOP, f, data)
    assert R.anchor_stop_or_refuse(f, data, done) == rec and R.family_stopped(f)
    assert len(R.block_runs_78b(f, None, "A")) == 12
    pin_of_item(monkeypatch, R.ANCHOR_STOP, f, json.dumps({**rec, "counts": {"kept": 3, "needed": 64}}).encode())
    with pytest.raises(R.Refused, match="has not been read"):               # a re-pinned record must be read again
        R.family_stopped(f)


def test_35_a_stopped_family_s78_kinds_refuse_for_good_and_the_retrain_runs_under_main_f(monkeypatch):
    """DESO2 item 36 (1), (2); AM1 changes 2, 5, 13 (DESO3 V1); GXB O6, item 14: once a family's stop record is
    pinned and read, rep_pass, l1_scan, the classifier, a1_pass (and the anchor job) refuse for good there (at the key
    check, the runner's gate, the pins and the order), the a0-1101 retrain is planned under MAIN_F (recipe "B") without
    RECIPE_S or a complete anchor job, on Y with ENGINE_Y (filled when that retrain is prepared), and the X retrain
    under MAIN_F after the Y one. An unstopped family refuses a main-config retrain."""
    f, main = "olmo2-7b", R.CONFIGS["olmo2-7b"]["main"][1]
    with pytest.raises(R.Refused, match="recipe S_78"):
        R.check_keys(**keys_of(f, kind="retrain", recipe_sha256=main))        # unstopped: S_78 only
    assert R.sc_recipe(f, "retrain") == "S" and R.sc_needed_pins("retrain", "Y", f) == ("RECIPE_S", "ENGINE_Y")
    assert "after anchor" in R.sc_order_problem("retrain", [], f)
    stop_family(monkeypatch, f)
    assert R.family_stopped(f) and not R.family_stopped("llama31-8b")
    for kind in ("rep_pass", "l1_scan", "classifier", "a1_pass", "anchor"):
        recipe = R.CONFIGS[f]["main"][1]
        with pytest.raises(R.Refused, match="never runs on that family"):
            R.check_keys(**keys_of(f, kind=kind, recipe_sha256=recipe))
        with pytest.raises(R.Refused, match="never runs on that family"):
            R.sc_pins_or_refuse(f, kind, "X", pins78_doc())
        assert "never runs" in R.sc_order_problem(kind, ["anchor", "retrain", "untuned_answers"], f)
        with pytest.raises(R.Refused, match="never runs"):
            R.job_decision(f, *preflight_pair(f), R.job_record(f, kind), 10 ** 6, 100.0)
    monkeypatch.setitem(R.RECIPE_S, f, "ab" * 32)                     # even with S_78 filled, never
    with pytest.raises(R.Refused, match="never runs"):
        R.check_keys(**keys_of(f, kind="rep_pass", recipe_sha256="ab" * 32))
    monkeypatch.setitem(R.RECIPE_S, f, None)
    y = "d3" * 32
    monkeypatch.setattr(R, "ENGINE_Y", y)
    R.check_keys(**keys_of(f, kind="retrain", recipe_sha256=main, engine_sha256=y))      # MAIN_F on Y
    for recipe in (R.CONFIGS[f]["g"][1], "ab" * 32):
        with pytest.raises(R.Refused, match="main config only"):
            R.check_keys(**keys_of(f, kind="retrain", recipe_sha256=recipe, engine_sha256=y))
    assert R.sc_recipe(f, "retrain") == "B" and R.sc_recipe(f, "untuned_answers") == "B"
    assert R.sc_needed_pins("retrain", "Y", f) == ("ENGINE_Y",) and R.sc_needed_pins("retrain", "X", f) == ()
    assert R.sc_order_problem("retrain", [], f) is None                     # the stop record replaces the anchor job
    assert R.sc_pins_or_refuse(f, "retrain", "Y", pins78_doc())["ENGINE_Y"] == y
    assert R.sc_engine_problem("retrain", "X", ()) and R.sc_engine_problem("retrain", "X", ("Y",)) is None
    d = R.job_decision(f, *preflight_pair(f), R.job_record(f, "retrain"), 10 ** 6, 100.0)
    assert d["action"] == "run"                                             # RECIPE_S null, yet the MAIN_F retrain runs
    monkeypatch.setattr(R, "ENGINE_Y", None)
    with pytest.raises(R.Refused, match="ENGINE_Y waits for .*main-config \\(MAIN_F\\) retrain is prepared"):
        R.sc_pins_or_refuse(f, "retrain", "Y", pins78_doc())
    assert R.sc_pins_or_refuse("llama31-8b", "anchor", "X", pins78_doc()) is not None      # the other family: normal
    monkeypatch.setitem(R.ANCHOR_STOP, f, {"path": "/abs.json", "sha256": hx("stop")})
    with pytest.raises(R.Refused, match="not a .path, sha256. pin"):
        R.family_stopped(f)


def test_35b_a_stopped_familys_kit_copy_plans_the_main_f_retrain(tmp_path, monkeypatch):
    """The kit copy's retrain_job: on a stopped family (its record read at the pin) it plans recipe "B" (MAIN_F) with
    RECIPE_S null; unstopped, it still refuses while RECIPE_S is null."""
    sr = kit_copy(tmp_path, "llama31-8b", "sc")
    with pytest.raises(R.Refused, match="not written yet"):
        sr.retrain_job()
    stop_family(monkeypatch, "llama31-8b", "harmful")
    job = sr.retrain_job()
    assert job["kind"] == "retrain" and job["recipe"] == "B" and job["seed"] == 1101 and job["unmeasured"]
