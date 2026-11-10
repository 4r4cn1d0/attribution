

# ==================================================================================== R1 K1: blocks A and B (8 Nov)
def hx(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def kit_copy(tmp_path: pathlib.Path, family: str, block: str):
    """stage1_rules.py in a KD7 working copy (tmp/family-probe-s78-<family>-<block>/); it imports this rules_78b."""
    folder = tmp_path / f"family-probe-s78-{family}-{block}"
    folder.mkdir(parents=True)
    shutil.copy2(KIT / "stage1_rules.py", folder / "stage1_rules.py")
    name = f"sr78_k1_{family}_{block}".replace("-", "_")
    try:
        module = load_by_path(name, folder / "stage1_rules.py")
    finally:
        sys.modules.pop(name, None)
    assert module.r78 is R and module.FAMILY == family
    return module


def test_23_k1_the_block_table_tests_run_here_too(tmp_path):
    """The rules mutation runner runs this file only, so every test of test_block_tables_78b.py (each takes at most
    tmp_path and monkeypatch, no parameters) also runs here, each in its own folder and monkeypatch context."""
    bt = load_by_path("test_block_tables_78b_via_rules", HERE / "test_block_tables_78b.py")
    try:
        names = sorted(n for n in dir(bt) if n.startswith("test_") and callable(getattr(bt, n)))
        assert len(names) >= 19
        for name in names:
            fn = getattr(bt, name)
            params = set(inspect.signature(fn).parameters)
            assert params <= {"tmp_path", "monkeypatch"}, name
            with pytest.MonkeyPatch.context() as mp:
                kwargs = {}
                if "tmp_path" in params:
                    (tmp_path / name).mkdir()
                    kwargs["tmp_path"] = tmp_path / name
                if "monkeypatch" in params:
                    kwargs["monkeypatch"] = mp
                fn(**kwargs)
    finally:
        sys.modules.pop("test_block_tables_78b_via_rules", None)


def test_24_o1_every_arm_trains_ceil_rows_over_128_steps():
    """GXB O1 (ruled): steps = ceil(rows / 128) of the arm's training rows, derived from its edit's resulting row
    count; a named arm whose derived steps differ from RK's STEPS refuses (33 removal, 38 add and a0, 39 for S4_96 and
    S4_192); S4_top takes ceil((4,800 + n) / 128). The named steps are RK's STEPS."""
    assert R.ROWS_PER_STEP == 128 and R.BASE_ROWS == 4800
    assert R.STEPS == {"remove": 33, "add": 38, "a0": 38, "dose": 39}
    assert R.ARM_STEPS == {"R": 33, "A1": 33, "L1": 33, "H1": 33, "S1": 38, "S3": 38, "S4": 38, "S4_96": 39,
                           "S4_192": 39, "a0": 38}
    for arm, (op, rows) in R.ARM_EDIT.items() if False else ():
        pass
    for arm in R.ARM_STEPS:
        edit = R.ARM_EDIT[arm]
        rows = 4800 if edit is None else R.arm_training_rows(arm, edit[1])
        assert R.arm_steps(arm, rows) == R.ARM_STEPS[arm] == -(-rows // 128), arm
    assert [R.arm_steps("s4_top", 4800 + n) for n in (48, 64, 65, 191)] == [38, 38, 39, 39]
    with pytest.raises(R.Refused, match="RK names 39"):
        R.arm_steps("S4_96", 4848)
    with pytest.raises(R.Refused, match="RK names 33"):
        R.arm_steps("A1", 4224)
    with pytest.raises(R.Refused, match="unknown arm"):
        R.arm_steps("S5", 4800)


def test_25_kd2_the_pod_layout_and_train_scales_input():
    """Part 2 §2.4 (KD2) and §2.1: at most 4 counted arms per pod, arms interleaved across pods within a block, mixed
    33/38/39-step pods with each arm's own steps in its cap; train_scale's input per arm (the edit's padded tokens per
    step) reaches the cap's requirement (requirements() reads the job's own count, not 1)."""
    for family in R.FAMILIES:
        pods = R.deal_ab(R.block_runs_78b(family, None, "A"))
        assert [len(p) for p in pods] == [4, 4, 4, 3, 3, 3]
        assert [p[0] for p in pods] == [("A1", 1102), ("A1", 1103), ("A1", 1104), ("L1", 1102), ("L1", 1103),
                                        ("L1", 1104)]                    # interleaved: A1's seeds on three pods
        a0 = R.FAMILIES[family]["A0_PADDED_TOKENS_PER_STEP"]
        job = R.job_record(family, "arm", 33, "H1", 1102, a0 * 1.5, oext=True)
        assert job["padded_tokens_per_step"] == a0 * 1.5
        assert R.requirements([job])[0] == pytest.approx(R.requirement_s(family, 33, "arm", 1.0, 1.0, None, a0 * 1.5,
                                                                          True))
        assert R.requirements([job])[0] > R.requirements([R.job_record(family, "arm", 33, oext=True)])[0]
        mixed = [R.job_record(family, "arm", s, oext=True) for s in (33, 38, 39)]
        assert [j["steps"] for j in mixed] == [33, 38, 39]
        assert R.requirements(mixed)[2] - R.requirements(mixed)[1] == pytest.approx(R.FAMILIES[family]["TRAIN_STEP_MAX_S"])
    with pytest.raises(R.Refused, match="one arm twice"):
        R.deal_ab([("S1", 1105), ("S1", 1106), ("S1", 1107), ("S1", 1108), ("S1", 1109)])


def test_26_the_oext_cap_term_x15_until_measured(monkeypatch):
    """DESO item 24 (a), (b); Part 2 §4.3; GXB O12: the in-job O-ext term (13 PHTest batches at the cap, half the
    scoring allowance, the early and outside time: 3,959 s OLMo, 4,061 s Llama) x 1.5 until measured, in the arm's cap
    (arm, a0_arm, ref_train) and the references' E caps. 4 arms per pod: 17.25 h / 19.25 h; four-pod need $167.06 /
    $185.56 (Part 2 §4.3's table). Block 0's arms carry no term (N's caps stay 8.5 h / 12.5 h). A measured value
    replaces the 1.5 x term by a recorded step."""
    want = {"olmo2-7b": (3958.904, 17.25, 167.06, 10.5), "llama31-8b": (4061.446, 19.25, 185.56, 12.5)}
    for family, (pass_s, cap, need, plain) in want.items():
        assert R.oext_pass_of(R.FAMILIES[family]) == pytest.approx(pass_s)
        assert R.oext_term_s(family) == pytest.approx(1.5 * pass_s) and R.OEXT_TERM_FACTOR == 1.5
        jobs = R.arm_pod(family, [33, 33, 33, 38], oext=True)
        assert R.cap_hours(jobs) == cap and R.cap_hours(R.arm_pod(family, [33, 33, 33, 38])) == plain
        assert all(j["oext"] is True for j in jobs)
        assert jobs[0]["measured_upper_s"] == pytest.approx(R.measured_upper_s(family) + R.oext_term_s(family))
        assert jobs[0]["spend_upper_s"] == jobs[0]["measured_upper_s"]
        assert jobs[0]["upper_s"] == pytest.approx(R.upper_m_s(family, 33) + R.oext_term_s(family))
        pods = [{"cap_hours": cap, "spend_usd": 0.0}] * 4
        assert R.funding_need_usd([pods], R.CONTINGENCY_FACTOR)["need_usd"] == need
        assert R.cap_hours(R.block0_jobs(family)) == R.KIT[family]["block0"]["cap_hours"]   # N: no O-ext step
        assert not any(j["oext"] for j in R.block0_jobs(family))
        for kind in ("a0_arm", "ref_train"):
            assert R.job_record(family, kind, oext=True)["upper_s"] == pytest.approx(
                R.job_record(family, kind)["upper_s"] + R.oext_term_s(family))
        with pytest.raises(R.Refused, match="carries no in-job O-ext step"):
            R.job_record(family, "evalonly", oext=True)
        with pytest.raises(R.Refused, match="E-capped kind"):
            R.job_record(family, "o_only", oext=True)
        with pytest.raises(R.Refused, match="True or False"):
            R.job_record(family, "arm", 33, oext=1)
        for kind, per in (("ref_eval", 2), ("safe_lora", 2)):           # the references: one term per point
            assert R.e_upper_s(family, kind, 2)["upper_s"] - R.e_upper_s(family, kind, 1)["upper_s"] == pytest.approx(
                R.evalonly_upper_s(family) + R.oext_term_s(family))
            assert "O-ext" in R.e_upper_s(family, kind)["basis"]
        bqi = R.e_upper_s(family, "ref_train_bqi")["upper_s"]
        monkeypatch.setitem(R.OEXT_TERM_MEASURED_S, family, 1000.0)
        assert R.oext_term_s(family) == 1000.0                          # measured: x 1
        assert R.e_upper_s(family, "ref_train_bqi")["upper_s"] == pytest.approx(bqi - 1.5 * pass_s + 1000.0)
        assert R.cap_hours(R.arm_pod(family, [33, 33, 33, 38], oext=True)) < cap
        for bad in (0.0, -1.0, float("nan"), "1000"):
            monkeypatch.setitem(R.OEXT_TERM_MEASURED_S, family, bad)
            with pytest.raises(R.Refused):
                R.oext_term_s(family)
        monkeypatch.setitem(R.OEXT_TERM_MEASURED_S, family, None)
    assert R.OEXT_TERM_MEASURED_S == {"olmo2-7b": None, "llama31-8b": None}


def test_26b_the_runner_gate_keeps_the_oext_term(tmp_path):
    """job_decision (the pod's gate) and pod_dry_run take the job's own O-ext term and padded tokens: an O-ext arm's
    requirement on the pod is the planned requirement at s = 1, not the arm's without the term."""
    done, ver = fake_preflight_done(tmp_path), fake_verification()
    for family in R.FAMILIES:
        job = R.job_record(family, "arm", 33, "H1", 1102, R.FAMILIES[family]["A0_PADDED_TOKENS_PER_STEP"] * 1.1, oext=True)
        d = R.job_decision(family, done, ver, job, 10 ** 6, 100.0)
        assert d["requirement_s"] == pytest.approx(max(job["start_requirement_s"],
                                                       R.sanity_floor_s(family, R.preflight_fields(done, ver), 33)))
        assert d["requirement_s"] > R.requirement_s(family, 33) + R.oext_term_s(family)


def test_27_check_keys_takes_the_oext_bank_as_a_second_pin(monkeypatch):
    """SCOUT §1.3; Part 2 §4.3: a job with an O-ext step names its O-ext bank; check_keys holds it against OEXT_78B's
    inputs.oext_bank (null refuses), and a kind without an O-ext step names none."""
    family = "olmo2-7b"
    R.check_keys(**keys_of(family))                                     # no O-ext bank named: as before
    with pytest.raises(R.Refused, match="O-ext bank pin is null"):
        R.check_keys(**keys_of(family), oext_bank=hx("bank"))
    monkeypatch.setitem(R.OEXT_78B, family, {"files": {R.OEXT_UNIT_SCRIPT: hx("w")},
                                             "inputs": {"oext_bank": hx("bank"), "oext_record": hx("rec")}})
    R.check_keys(**keys_of(family), oext_bank=hx("bank"))
    R.check_keys(**keys_of(family, kind="a0_arm"), oext_bank=hx("bank"))
    with pytest.raises(R.Refused, match="not olmo2-7b's pinned O-ext bank"):
        R.check_keys(**keys_of(family), oext_bank=hx("other"))
    with pytest.raises(R.Refused, match="names no O-ext bank"):
        R.check_keys(**keys_of(family, kind="evalonly"), oext_bank=hx("bank"))
    assert R.OEXT_BANK_KINDS == R.BANK500_KINDS | {"arm", "a0_arm"}


def test_28_the_w1_18_kind_one_pod_one_record_per_family(monkeypatch):
    """DES E2; DESO2 item 37; GXB O4: w1_18 is a single-job E kind (alone on its pod), X only, the scorer block's first
    O job (refused once a 500-bank job is planned), one pod with one check and one record per family; under [C]
    OLMo-2-7B's units only. Its E cap is 2.25 h ($10.16 guard), inside Part 2 §4.2's 2-3 h."""
    assert "w1_18" in R.E_KINDS and "w1_18" in R.SC_KINDS and "w1_18" in R.X_ONLY_KINDS
    assert R.SC_KIND_PINS["w1_18"] == ("W1_18_78B",) and R.W1_18_78B is None
    for family in R.FAMILIES:
        assert R.e_cap_hours(family, "w1_18") == 2.25 and R.e_pod(family, "w1_18")["guard_usd"] == 10.16
        with pytest.raises(R.Refused, match="runs alone"):
            R.cap_hours([R.job_record(family, "w1_18"), R.job_record(family, "arm", 33)])
        assert not R.engine_allowed("w1_18", "d3" * 32)
    b, c = R.w1_18_plan("B"), R.w1_18_plan("C")
    assert b["families"] == ("olmo2-7b", "llama31-8b") and c["families"] == ("olmo2-7b",)
    assert b["records"] == {"olmo2-7b": "w1_18_record__olmo2-7b.json", "llama31-8b": "w1_18_record__llama31-8b.json"}
    assert b["n_units"] == 7 and c["n_units"] == 4 and set(c["records"]) == {"olmo2-7b"}
    assert [u["unit"] for u in b["units"]["olmo2-7b"]] == ["untuned", 1101, 1102, 1103]
    assert [u["unit"] for u in b["units"]["llama31-8b"]] == ["untuned", 1101, 1102]
    assert all(u["complete_sha256"] == R.KIT[f]["a0_units"][u["unit"]]["complete_sha256"]
               for f in b["families"] for u in b["units"][f])
    with pytest.raises(R.Refused, match="not B or C"):
        R.w1_18_plan("A")
    assert R.w1_18_host_problem("olmo2-7b") is None and "olmo2-7b's scorer-block copy" in R.w1_18_host_problem("llama31-8b")
    assert R.w1_18_first_problem(["anchor", "untuned_answers"]) is None
    for kind in ("o_only", "o_only_with_regenerate", "c0"):
        assert "first O job" in R.w1_18_first_problem(["anchor", kind])
    assert R.sc_needed_pins("w1_18", "X") == ("W1_18_78B",)
    with pytest.raises(R.Refused, match="W1_18_78B waits for"):
        R.sc_pins_or_refuse("olmo2-7b", "w1_18", "X", pins78_doc())
    monkeypatch.setattr(R, "W1_18_78B", {"files": {R.W1_18_SCRIPT: hx("w")}})
    assert R.sc_pins_or_refuse("olmo2-7b", "w1_18", "X", pins78_doc())["W1_18_78B"] == {"files": {R.W1_18_SCRIPT: hx("w")}}
    monkeypatch.setattr(R, "W1_18_78B", {"files": {}})
    with pytest.raises(R.Refused, match="not a .files"):
        R.sc_pin_values("olmo2-7b", pins78_doc())


def pins78_doc() -> dict:
    """The scorer layer's committed pins_78b.json (its null pins as committed)."""
    return json.loads((ROOT / "scripts" / "scale78b" / "settings" / "pins_78b.json").read_text())


def branch_doc(family, branch="full", source="default", record=None) -> dict:
    return {"kind": R.BRANCH_RECORD_KIND, "version": 1, "family": family, "branch": branch, "source": source,
            "w1_18_record_sha256": record, "utc": "2026-11-12T10:00:00Z", "recorded_by": "GI XI"}


def test_29_the_branch_record_the_500_bank_kinds_and_the_flags():
    """Part 2 §4.2; DES E2; DESO item 9: BRANCHES ("full", "128"), Branch full by default; every 500-bank job (o_only,
    o_only_with_regenerate, c0, the references, ref_train, and arm and a0_arm in blocks A and B, never block 0) refuses
    before the family's branch record; 128 only from that family's W1-18 record; the branch never switches; under 128
    every O-ext command takes --w1-18-record and the regenerated units --dev100-source."""
    assert R.BRANCHES == ("full", "128") and R.BRANCH_DEFAULT == "full"
    assert R.BANK500_KINDS == frozenset({"o_only", "o_only_with_regenerate", "c0", "ref_eval", "safe_lora", "ref_train",
                                         "ref_train_bqi"})
    assert not R.bank500_job("arm", "0") and not R.bank500_job("a0_arm", "0") and not R.bank500_job("anchor", "sc")
    assert R.bank500_job("arm", "A") and R.bank500_job("a0_arm", "B") and R.bank500_job("o_only", "sc")
    f = "llama31-8b"
    for kind, block in (("o_only", "sc"), ("c0", "sc"), ("arm", "A"), ("ref_eval", "B")):
        assert "waits for llama31-8b's branch record" in R.bank500_problem(f, kind, block, None)
        assert R.bank500_problem(f, kind, block, branch_doc(f)) is None
    assert R.bank500_problem(f, "arm", "0", None) is None
    assert "not one" in R.bank500_problem(f, "o_only", "sc", branch_doc("olmo2-7b"))
    assert R.branch_record_problem(branch_doc(f, "128", "w1_18", hx("w1")), f) is None
    assert R.branch_record_problem(branch_doc(f, "full", "w1_18", hx("w1")), f) is None   # the bar failed: full
    assert "names its W1-18 record" in R.branch_record_problem(branch_doc(f, "128", "w1_18"), f)
    assert "default record is Branch full" in R.branch_record_problem(branch_doc(f, "128", "default"), f)
    assert "default record is Branch full" in R.branch_record_problem(branch_doc(f, "full", "default", hx("w1")), f)
    assert R.branch_record_problem({**branch_doc(f), "branch": "64"}, f)
    assert R.branch_record_problem({**branch_doc(f), "source": "lead"}, f)
    assert R.branch_switch_problem(None, branch_doc(f)) is None
    assert R.branch_switch_problem(branch_doc(f), branch_doc(f)) is None
    assert "never switched" in R.branch_switch_problem(branch_doc(f), branch_doc(f, "128", "w1_18", hx("w1")))
    assert "never switched" in R.branch_switch_problem(branch_doc(f, "128", "w1_18", hx("w1")), branch_doc(f))
    assert R.oext_flags(f, "o_only", branch_doc(f)) == {"w1_18_record": None, "dev100_source": False}
    b128 = branch_doc(f, "128", "w1_18", hx("w1"))
    for kind in ("c0", "o_only", "o_only_with_regenerate", "arm", "a0_arm"):
        assert R.oext_flags(f, kind, b128)["w1_18_record"] == hx("w1")
    assert R.oext_flags(f, "o_only_with_regenerate", b128, regenerated=True)["dev100_source"] is True
    assert R.oext_flags(f, "o_only", b128)["dev100_source"] is False                # theta0 is never regenerated
    with pytest.raises(R.Refused, match="no O-ext step"):
        R.oext_flags(f, "anchor", b128)


def n_units_doc(family: str) -> dict:
    out = {}
    for arm, seed in R.block0_runs(family):
        u = {"path": f"tmp/family-probe-s78-{family}-0/retrieved/{family}-0-1/tree/round1/{seed}-{arm}-e1-a1",
             "complete_sha256": hx(f"n-{family}-{arm}-{seed}"), "job_sha256": hx(f"job-{family}-{arm}-{seed}")}
        if arm == "R":
            u["edit_sha256"] = hx(f"edit-{family}-{seed}")
        out[R.unit_key(arm, seed)] = u
    return out


def test_30_the_seed_key_olmo_n_r1101_and_side_a0_1101(tmp_path, monkeypatch):
    """GXB's seed key: o_only_with_regenerate and every unit input are keyed by (arm, seed), not seed alone. On
    OLMo-2-7B N's R_1101 and the side unit a0-1101 share seed 1101: two units, two keys, two input sets, two pins."""
    units = R.sc_units("olmo2-7b", "o_only_with_regenerate")
    assert [(u["arm"], u["seed"], u["source"]) for u in units] == [
        ("a0", 1101, "side"), ("a0", 1102, "side"), ("a0", 1103, "side"), ("R", 1101, "n"), ("R", 1102, "n"),
        ("R", 1103, "n")]
    assert [(u["arm"], u["seed"], u["source"]) for u in R.sc_units("llama31-8b", "o_only_with_regenerate")] == [
        ("a0", 1101, "side"), ("a0", 1102, "side"), ("R", 1101, "n"), ("R", 1102, "n"), ("R", 1103, "n"),
        ("a0", 1103, "n")]                                            # 6 + 6 = 12; with theta0's 2 o_only: 14 pods
    assert R.sc_unit_source("olmo2-7b", "o_only_with_regenerate", "R", 1101) == "n"
    assert R.sc_unit_source("olmo2-7b", "o_only_with_regenerate", "a0", 1101) == "side"
    assert R.sc_unit_source("llama31-8b", "o_only_with_regenerate", "a0", 1103) == "n"
    for bad in (("R", 1104), ("a0", 1104), ("H1", 1101), ("R", None)):
        with pytest.raises(R.Refused, match="not one of its units"):
            R.sc_unit_source("olmo2-7b", "o_only_with_regenerate", *bad)
    assert R.SC_ARMS == {"o_only_with_regenerate": ("a0", "R")} and R.SC_ARM["o_only_with_regenerate"] == "a0"
    assert R.sc_needed_pins("o_only_with_regenerate", "X", "olmo2-7b", "R", 1101) == ("OEXT_78B", "N_UNITS")
    assert R.sc_needed_pins("o_only_with_regenerate", "X", "olmo2-7b", "a0", 1101) == ("OEXT_78B",)
    sr = kit_copy(tmp_path, "olmo2-7b", "sc")
    side, n = sr.sc_input_names("o_only_with_regenerate", 1101, "a0"), sr.sc_input_names("o_only_with_regenerate", 1101, "R")
    assert side == ("side_complete:a0:1101", "oext_bank", "oext_record") == sr.sc_input_names("o_only_with_regenerate", 1101)
    assert n == ("n_complete:R:1101", "regen_edit:R:1101", "oext_bank", "oext_record")
    values = R.sc_pin_values("olmo2-7b", pins78_doc())
    assert sr.sc_input_pins("o_only_with_regenerate", pins78_doc(), values, 1101, "R") == {
        "n_complete:R:1101": None, "regen_edit:R:1101": None, "oext_bank": None, "oext_record": None}
    assert sr.sc_input_pins("o_only_with_regenerate", pins78_doc(), values, 1101, "a0")["side_complete:a0:1101"] == \
        R.KIT["olmo2-7b"]["a0_units"][1101]["complete_sha256"]
    monkeypatch.setitem(R.N_UNITS, "olmo2-7b", n_units_doc("olmo2-7b"))
    values = R.sc_pin_values("olmo2-7b", pins78_doc())
    pins_n = sr.sc_input_pins("o_only_with_regenerate", pins78_doc(), values, 1101, "R")
    pins_side = sr.sc_input_pins("o_only_with_regenerate", pins78_doc(), values, 1101, "a0")
    assert pins_n["n_complete:R:1101"] == hx("n-olmo2-7b-R-1101") and pins_n["regen_edit:R:1101"] == hx("edit-olmo2-7b-1101")
    assert pins_side["side_complete:a0:1101"] != pins_n["n_complete:R:1101"]
    assert set(pins_n) & set(pins_side) == {"oext_bank", "oext_record"}
    llama = kit_copy(tmp_path / "l", "llama31-8b", "sc")
    assert llama.sc_input_names("o_only_with_regenerate", 1103, "a0") == ("n_complete:a0:1103", "oext_bank", "oext_record")


def test_31_n_units_are_null_pins_that_refuse_until_block_0s_record_done(monkeypatch):
    """DES E5; Part 2 §4.5: N_UNITS[family] is null until block 0's record-done and a recorded lead step; N's
    regenerations refuse until then (sc_pins_or_refuse names N_UNITS and its event); a filled pin holds exactly N's
    units under block 0's working copy."""
    assert R.N_UNITS == {"olmo2-7b": None, "llama31-8b": None}
    monkeypatch.setitem(R.OEXT_78B, "olmo2-7b", {"files": {R.OEXT_UNIT_SCRIPT: hx("w")},
                                                 "inputs": {"oext_bank": hx("b"), "oext_record": hx("r")}})
    with pytest.raises(R.Refused, match="N_UNITS waits for block 0 \\(N\\)"):
        R.sc_pins_or_refuse("olmo2-7b", "o_only_with_regenerate", "X", pins78_doc(), "R", 1102)
    R.sc_pins_or_refuse("olmo2-7b", "o_only_with_regenerate", "X", pins78_doc(), "a0", 1102)   # the side unit runs
    with pytest.raises(R.Refused, match="is null"):
        R.n_unit_or_refuse("olmo2-7b", "R", 1101)
    with pytest.raises(R.Refused, match="not one of olmo2-7b's N units"):
        R.n_unit_or_refuse("olmo2-7b", "a0", 1103)
    doc = n_units_doc("olmo2-7b")
    assert R.n_units_problem(doc, "olmo2-7b") is None
    monkeypatch.setitem(R.N_UNITS, "olmo2-7b", doc)
    assert R.n_unit_or_refuse("olmo2-7b", "R", 1101)["complete_sha256"] == hx("n-olmo2-7b-R-1101")
    R.sc_pins_or_refuse("olmo2-7b", "o_only_with_regenerate", "X", pins78_doc(), "R", 1102)
    bad = {k: dict(v) for k, v in doc.items()}
    bad["R-1101"]["path"] = "tmp/family-probe-s78-olmo2-7b-sc/x"
    assert "is not under" in R.n_units_problem(bad, "olmo2-7b")
    assert "keys are not N's units" in R.n_units_problem({k: v for k, v in doc.items() if k != "R-1103"}, "olmo2-7b")
    assert "must hold exactly" in R.n_units_problem({**doc, "R-1101": {k: v for k, v in doc["R-1101"].items()
                                                                       if k != "edit_sha256"}}, "olmo2-7b")
    assert "keys are not N's units" in R.n_units_problem(n_units_doc("llama31-8b"), "olmo2-7b")
    monkeypatch.setitem(R.N_UNITS, "olmo2-7b", bad)
    with pytest.raises(R.Refused, match="not N's unit record"):
        R.sc_pin_values("olmo2-7b", pins78_doc())


def test_32_rejudged_a_seven_per_family_with_ns_entries_null(tmp_path, monkeypatch):
    """Part 2 §6; DESO item 26: block A re-judges N's units, the reused a0 units and theta0: OLMo 3 + 3 + 1, Llama
    4 + 2 + 1; N's entries are null until N runs (a judge launch refuses through rejudged_or_refuse); the side units
    and theta0 carry their COMPLETE.json and job.json pins (M); block B and block 0 have none."""
    for family, (n, side) in (("olmo2-7b", (3, 3)), ("llama31-8b", (4, 2))):
        pins = R.rejudged_pins(family, "A")
        assert len(pins) == 7 == n + side + 1
        assert [p["complete_sha256"] is None for p in pins] == [True] * n + [False] * (side + 1)
        assert all(p["path"] is None and p["arm"] is None and p["job_sha256"] is None for p in pins[:n])
        assert [(p["seed"], p["target"]) for p in pins[:n]] == [(s, "e1") for _, s in R.block0_runs(family)]
        assert pins[-1]["name"] == "theta0 (untuned)" and pins[-1]["target"] == "init"
        for p in pins[n:]:
            assert set(p) == {"name", "arm", "seed", "target", "path", "complete_sha256", "job_sha256"}
            assert len(p["job_sha256"]) == 64 and p["path"].startswith("tmp/family-probe-sp-")
        with pytest.raises(R.Refused, match="wait for block 0 \\(N\\)"):
            R.rejudged_or_refuse(family, "A")
        assert R.rejudged_pins(family, "B") == () == R.rejudged_pins(family, "0")
        monkeypatch.setitem(R.N_UNITS, family, n_units_doc(family))
        filled = R.rejudged_or_refuse(family, "A")
        assert filled[0]["arm"] == f"edit-{hx(f'edit-{family}-1101')}" and filled[0]["path"].startswith(
            f"tmp/family-probe-s78-{family}-0/")
        assert len({p["complete_sha256"] for p in filled}) == 7
        sr = kit_copy(tmp_path / family, family, "A")
        assert sr.REJUDGED_PINS["A"] == filled and sr.REJUDGED_PINS["B"] == () == sr.REJUDGED_PINS["0"]
        monkeypatch.setitem(R.N_UNITS, family, None)
    for family in R.FAMILIES:                                   # the job.json pins re-measured (no answer file opened)
        for key, unit in R.KIT[family]["a0_units"].items():
            folder = MEASURED_ROOT.parent / unit["path"]
            if not (folder / "job.json").is_file():
                continue
            assert hashlib.sha256((folder / "job.json").read_bytes()).hexdigest() == unit["job_sha256"], (family, key)
            assert hashlib.sha256((folder / "COMPLETE.json").read_bytes()).hexdigest() == unit["complete_sha256"]


def gate_doc(**changes) -> dict:
    doc = {"kind": R.GATE_RECORD_KIND, "version": 1, "option": "B", "families": ["olmo2-7b", "llama31-8b"],
           "plan": "A", "noise_reading_sha256": hx("noise"), "blinded_sigma_sha256": None, "balance_usd": 300.0,
           "utc": "2026-11-20T10:00:00Z", "recorded_by": "GI XI"}
    doc.update(changes)
    return doc


def test_33_o14_gate_78b_is_null_and_blocks_a_and_b_refuse_before_its_fill(monkeypatch):
    """GXB O14, X4: GATE_78B (the gate record's path and SHA-256) is null; block A's init reads its families, block
    B's its plan; both refuse before the fill. The record holds the option ([B] both families, [C] OLMo-2-7B only),
    families, plan, the noise reading's and blinded_sigma.py's output hashes and the live balance."""
    assert R.GATE_78B is None
    data = json.dumps(gate_doc()).encode()
    for block in ("A", "B"):
        with pytest.raises(R.Refused, match="GATE_78B is null: it waits for ruling 9's gate"):
            R.block_init_or_refuse(block, "olmo2-7b", data)
    monkeypatch.setattr(R, "GATE_78B", {"path": "records/gate.json", "sha256": hashlib.sha256(data).hexdigest()})
    a = R.block_init_or_refuse("A", "llama31-8b", data)
    assert a["families"] == ("olmo2-7b", "llama31-8b") and a["plan"] is None and a["option"] == "B"
    assert R.block_init_or_refuse("B", "olmo2-7b", data)["plan"] == "A"
    with pytest.raises(R.Refused, match="reads nothing"):
        R.block_init_or_refuse("sc", "olmo2-7b", data)
    c = json.dumps(gate_doc(option="C", families=["olmo2-7b"], plan="H", blinded_sigma_sha256=hx("bs"))).encode()
    monkeypatch.setattr(R, "GATE_78B", {"path": "records/gate.json", "sha256": hashlib.sha256(c).hexdigest()})
    assert R.block_init_or_refuse("B", "olmo2-7b", c)["plan"] == "H"
    for block in ("A", "B"):
        with pytest.raises(R.Refused, match="llama31-8b runs no block"):
            R.block_init_or_refuse(block, "llama31-8b", c)
    with pytest.raises(R.Refused, match="do not hash"):
        R.block_init_or_refuse("A", "olmo2-7b", data)
    for change, match in (({"option": "C"}, "option C runs"), ({"families": ["llama31-8b"], "option": "C"}, "runs"),
                          ({"plan": "B10"}, "plan"), ({"noise_reading_sha256": None}, "noise_reading"),
                          ({"blinded_sigma_sha256": "x"}, "blinded_sigma"), ({"balance_usd": -1}, "negative"),
                          ({"balance_usd": "300"}, "finite"), ({"kind": "gate"}, "kind"), ({"utc": ""}, "utc"),
                          ({"extra": 1}, "exactly")):
        assert match in (R.gate_record_problem(gate_doc(**change)) or ""), change
    bad = json.dumps(gate_doc(plan="B10")).encode()
    monkeypatch.setattr(R, "GATE_78B", {"path": "records/gate.json", "sha256": hashlib.sha256(bad).hexdigest()})
    with pytest.raises(R.Refused, match="is not 'stage1-78b gate record'"):
        R.block_init_or_refuse("B", "olmo2-7b", bad)
    monkeypatch.setattr(R, "GATE_78B", {"path": "/abs/gate.json", "sha256": hashlib.sha256(bad).hexdigest()})
    with pytest.raises(R.Refused, match="not a .path, sha256. pin"):
        R.block_init_or_refuse("B", "olmo2-7b", bad)


HARMFUL = "harmful prompt 7 (8 of 64) does not encode (encode_train: too long); the list needs a reviewed new version"


def test_34_o6_a_stop_only_from_the_anchor_scripts_own_signal():
    """GXB O6 and item 14: a stop is recorded only from exit 3 (fewer than 64 safe anchors) or exit 1 with the
    AnchorJobError message "harmful prompt ... does not encode" (R: scripts/make_anchor_answers.py:121); any other exit
    or message is a crash. The stop record is text-free: family, stop kind, exit code, JOB-DONE.json SHA-256 and the
    stop line's ids and counts; it must name the anchor job's JOB-DONE.json."""
    source = (ROOT / "scripts" / "make_anchor_answers.py").read_text()
    assert "EXIT_FEW = 3" in source and "class AnchorJobError(SystemExit)" in source
    assert 'raise AnchorJobError(f"harmful prompt {k} ({k + 1} of {n_harmful}) does not encode ({failure}); "' in source
    assert '"the list needs a reviewed new version")' in source
    assert R.anchor_exit_kind(0) == "complete" and R.anchor_exit_kind(3) == "few_safe"
    assert R.anchor_exit_kind(1, HARMFUL) == "harmful_pair" and R.anchor_exit_kind(1, HARMFUL + "\n") == "harmful_pair"
    for code, message in ((1, None), (1, "the prompt list's SHA-256 is not the pinned value"),
                          (1, "prompt 3 (4 of 128) does not encode as a generation prompt (ValueError); the list needs "
                              "a reviewed new version"), (2, HARMFUL), (137, None), (-9, None), (None, None),
                          (True, HARMFUL), (1, "x" + HARMFUL), (4, None)):
        assert R.anchor_exit_kind(code, message) == "crash", (code, message)
    done = hx("job-done")
    few = R.anchor_stop_record("olmo2-7b", 3, None, done, {"kept": 61, "needed": 64, "drops": {"capped": 3}})
    assert few == {"kind": R.ANCHOR_STOP_KIND, "version": 1, "family": "olmo2-7b", "stop": "few_safe", "exit_code": 3,
                   "job_done_sha256": done, "line": {"kept": 61, "needed": 64}}
    pair = R.anchor_stop_record("llama31-8b", 1, HARMFUL, done)
    assert pair["stop"] == "harmful_pair" and pair["line"] == {"prompt_index": 7, "position": 8, "of": 64}
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
    assert R.anchor_stop_problem({**few, "exit_code": 1}, "olmo2-7b")
    assert R.anchor_stop_problem({**few, "line": {"kept": 64, "needed": 64}}, "olmo2-7b")
    assert R.anchor_stop_problem({**pair, "line": {"prompt_index": 7, "position": 7, "of": 64}}, "llama31-8b")
    assert R.ANCHOR_STOP == {"olmo2-7b": None, "llama31-8b": None}


def test_35_a_stopped_family_s78_kinds_refuse_for_good_and_the_retrain_runs_under_main_f(monkeypatch):
    """DESO2 item 36 (1), (2); AM1 changes 2, 5, 13 (DESO3 V1); GXB O6, item 14: once a family's stop record is
    pinned, rep_pass, l1_scan, the classifier, a1_pass (and the anchor job) refuse for good there (at the key check,
    the runner's gate, the pins and the order), the a0-1101 retrain is planned under MAIN_F (recipe "B") without
    RECIPE_S or a complete anchor job, on Y with ENGINE_Y (filled when that retrain is prepared), and the X retrain
    under MAIN_F after the Y one. An unstopped family refuses a main-config retrain."""
    f, main = "olmo2-7b", R.CONFIGS["olmo2-7b"]["main"][1]
    with pytest.raises(R.Refused, match="recipe S_78"):
        R.check_keys(**keys_of(f, kind="retrain", recipe_sha256=main))        # unstopped: S_78 only
    assert R.sc_recipe(f, "retrain") == "S" and R.sc_needed_pins("retrain", "Y", f) == ("RECIPE_S", "ENGINE_Y")
    assert "after anchor" in R.sc_order_problem("retrain", [], f)
    monkeypatch.setitem(R.ANCHOR_STOP, f, {"path": "records/anchor-stop.json", "sha256": hx("stop")})
    assert R.family_stopped(f) and not R.family_stopped("llama31-8b")
    for kind in ("rep_pass", "l1_scan", "classifier", "a1_pass", "anchor"):
        recipe = R.CONFIGS[f]["main"][1]
        with pytest.raises(R.Refused, match="never runs on that family"):
            R.check_keys(**keys_of(f, kind=kind, recipe_sha256=recipe))
        with pytest.raises(R.Refused, match="never runs on that family"):
            R.sc_pins_or_refuse(f, kind, "X", pins78_doc())
        assert "never runs" in R.sc_order_problem(kind, ["anchor", "retrain", "untuned_answers"], f)
        with pytest.raises(R.Refused, match="never runs"):
            R.job_decision(f, fake_preflight_done_dict(), fake_verification(), R.job_record(f, kind), 10 ** 6, 100.0)
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
    d = R.job_decision(f, fake_preflight_done_dict(), fake_verification(), R.job_record(f, "retrain"), 10 ** 6, 100.0)
    assert d["action"] == "run"                                             # RECIPE_S null, yet the MAIN_F retrain runs
    monkeypatch.setattr(R, "ENGINE_Y", None)
    with pytest.raises(R.Refused, match="ENGINE_Y waits for .*main-config \\(MAIN_F\\) retrain is prepared"):
        R.sc_pins_or_refuse(f, "retrain", "Y", pins78_doc())
    assert R.sc_pins_or_refuse("llama31-8b", "anchor", "X", pins78_doc()) is not None      # the other family: normal
    monkeypatch.setitem(R.ANCHOR_STOP, f, {"path": "/abs.json", "sha256": hx("stop")})
    with pytest.raises(R.Refused, match="not a .path, sha256. pin"):
        R.family_stopped(f)


def test_35b_a_stopped_familys_kit_copy_plans_the_main_f_retrain(tmp_path, monkeypatch):
    """The kit copy's retrain_job: on a stopped family it plans recipe "B" (MAIN_F) with RECIPE_S null; unstopped, it
    still refuses while RECIPE_S is null."""
    sr = kit_copy(tmp_path, "llama31-8b", "sc")
    with pytest.raises(R.Refused, match="not written yet"):
        sr.retrain_job()
    monkeypatch.setitem(R.ANCHOR_STOP, "llama31-8b", {"path": "records/stop.json", "sha256": hx("stop")})
    job = sr.retrain_job()
    assert job["kind"] == "retrain" and job["recipe"] == "B" and job["seed"] == 1101 and job["unmeasured"]


def test_36_ref_train_runs_under_recipe_g_only():
    """Part 2 §3.2; P2FV D6: ref_train (recipe G's reference, the 1B form) is a measured kind, 38 steps, counted, under
    RECIPE_G only (null refuses at the key check and the runner's gate); the main config never passes for it."""
    assert "ref_train" in R.MEASURED_KINDS and "ref_train" in R.COUNTED_KINDS and R.G_KINDS == frozenset({"ref_train"})
    for family in R.FAMILIES:
        job = R.job_record(family, "ref_train", oext=True)
        assert job["steps"] == 38 and job["counted"] == 1 and not job["unmeasured"]
        for recipe in (R.CONFIGS[family]["main"][1], R.CONFIGS[family]["g"][1]):
            with pytest.raises(R.Refused, match="RECIPE_G for .* is null"):
                R.check_keys(**keys_of(family, kind="ref_train", recipe_sha256=recipe))
        with pytest.raises(R.Refused, match="RECIPE_G"):
            R.job_decision(family, fake_preflight_done_dict(), fake_verification(), job, 10 ** 6, 100.0)


def test_36b_ref_train_takes_its_filled_recipe_g_pin_only(monkeypatch):
    for family in R.FAMILIES:
        g = R.CONFIGS[family]["g"][1]
        monkeypatch.setitem(R.RECIPE_G, family, g)
        R.check_keys(**keys_of(family, kind="ref_train", recipe_sha256=g))
        with pytest.raises(R.Refused, match="RECIPE_G only"):
            R.check_keys(**keys_of(family, kind="ref_train", recipe_sha256=R.CONFIGS[family]["main"][1]))
        assert R.job_decision(family, fake_preflight_done_dict(), fake_verification(),
                              R.job_record(family, "ref_train", oext=True), 10 ** 6, 100.0)["action"] == "run"


def test_37_the_oext_scripts_are_track_os_wrapper():
    """GXB B-3; PLAN-AB item 5d: OEXT_UNIT_SCRIPT, C0_SCRIPT and W1_18_SCRIPT are Track O's one wrapper
    scripts/scale78b/oext_78b.py (its unit, lean and w1_18 commands); the 1B scripts are not named."""
    assert R.OEXT_UNIT_SCRIPT == R.C0_SCRIPT == R.W1_18_SCRIPT == R.OEXT_WRAPPER_78B == "scripts/scale78b/oext_78b.py"
    assert R.OEXT_WRAPPER_COMMANDS == {"o_only": "unit", "o_only_with_regenerate": "unit", "c0": "lean", "w1_18": "w1_18"}
    assert R.oext_form_problem({"files": {R.OEXT_UNIT_SCRIPT: hx("w")},
                                "inputs": {"oext_bank": hx("b"), "oext_record": hx("r")}}) is None


def test_38_every_new_k1_pin_is_null_and_names_its_event():
    """A13's pattern for every pin R1 K1 adds: GATE_78B, N_UNITS, W1_18_78B, ANCHOR_STOP (null = no stop), the O-ext
    term's measured value, and the null method edits; each refusal names the event that fills it."""
    assert R.GATE_78B is None and R.W1_18_78B is None
    assert R.N_UNITS == {"olmo2-7b": None, "llama31-8b": None} == R.ANCHOR_STOP == R.OEXT_TERM_MEASURED_S
    for family in R.FAMILIES:
        assert {a for a, v in R.METHOD_EDITS[family].items() if v is None} == {"A1", "L1", "S3", "S4", "S4_96",
                                                                               "S4_192", "s4_top"}
    for pin in ("N_UNITS", "W1_18_78B", "ENGINE_Y"):
        assert R.SC_PIN_EVENTS[pin] and "recorded" in R.SC_PIN_EVENTS[pin] or "fills" in R.SC_PIN_EVENTS[pin]
    assert "AM1" in R.SC_PIN_EVENTS["ENGINE_Y"] and "main-config (MAIN_F) retrain" in R.SC_PIN_EVENTS["ENGINE_Y"]
    assert "ruling 9's gate" in R.GATE_EVENT and set(R.METHOD_EDIT_EVENTS) == {"A1", "L1", "S3", "S4", "S4_96",
                                                                               "S4_192", "s4_top"}
