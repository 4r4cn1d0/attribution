def test_29_the_branch_record_the_500_bank_kinds_and_the_flags(monkeypatch):
    """Part 2 §4.2; DES E2; DESO item 9; K1V-5: BRANCHES ("full", "128"), Branch full by default; each family's branch
    is read only from its pinned branch record (BRANCH_78B[family] = {path, sha256}, null until W1-18's record-done);
    every 500-bank job (o_only, o_only_with_regenerate, c0, the references, ref_train, and arm and a0_arm in blocks A
    and B, never block 0) refuses before the pin, and with bytes that are not the pinned record; 128 only from that
    family's W1-18 record; the branch never switches; under 128 every O-ext command takes --w1-18-record and the
    regenerated units --dev100-source."""
    assert R.BRANCHES == ("full", "128") and R.BRANCH_DEFAULT == "full"
    assert R.BRANCH_78B == {"olmo2-7b": None, "llama31-8b": None}
    assert R.BANK500_KINDS == frozenset({"o_only", "o_only_with_regenerate", "c0", "ref_eval", "safe_lora", "ref_train",
                                         "ref_train_bqi"})
    assert not R.bank500_job("arm", "0") and not R.bank500_job("a0_arm", "0") and not R.bank500_job("anchor", "sc")
    assert R.bank500_job("arm", "A") and R.bank500_job("a0_arm", "B") and R.bank500_job("o_only", "sc")
    f = "llama31-8b"
    full = json.dumps(branch_doc(f)).encode()
    for kind, block in (("o_only", "sc"), ("c0", "sc"), ("arm", "A"), ("ref_eval", "B")):
        assert "waits for llama31-8b's branch record (BRANCH_78B" in R.bank500_problem(f, kind, block, full)
    assert R.bank500_problem(f, "arm", "0", None) is None
    pin_of_item(monkeypatch, R.BRANCH_78B, f, full)
    for kind, block in (("o_only", "sc"), ("c0", "sc"), ("arm", "A"), ("ref_eval", "B")):
        assert R.bank500_problem(f, kind, block, full) is None
    assert "not the pinned one" in R.bank500_problem(f, "o_only", "sc", json.dumps(branch_doc(f, "128", "w1_18",
                                                                                              hx("w1"))).encode())
    assert "not the pinned one" in R.bank500_problem(f, "o_only", "sc", None)
    other = json.dumps(branch_doc("olmo2-7b")).encode()
    pin_of_item(monkeypatch, R.BRANCH_78B, f, other)
    assert "not the pinned one" in R.bank500_problem(f, "o_only", "sc", other)            # another family's record
    assert R.branch_record_problem(branch_doc(f, "128", "w1_18", hx("w1")), f) is None
    assert R.branch_record_problem(branch_doc(f, "full", "w1_18", hx("w1")), f) is None   # the bar failed: full
    assert "names its W1-18 record" in R.branch_record_problem(branch_doc(f, "128", "w1_18"), f)
    assert "default record is Branch full" in R.branch_record_problem(branch_doc(f, "128", "default"), f)
    assert "default record is Branch full" in R.branch_record_problem(branch_doc(f, "full", "default", hx("w1")), f)
    assert R.branch_record_problem({**branch_doc(f), "branch": "64"}, f)
    assert R.branch_record_problem({**branch_doc(f), "source": "lead"}, f)
    assert R.branch_record_problem({**branch_doc(f), "version": True}, f)
    # never switched: the pinned record is the old one
    monkeypatch.setitem(R.BRANCH_78B, f, None)
    assert R.branch_switch_problem(f, branch_doc(f)) is None                        # no record yet: the first one
    b128 = branch_doc(f, "128", "w1_18", hx("w1"))
    data128 = json.dumps(b128).encode()
    pin_of_item(monkeypatch, R.BRANCH_78B, f, data128)
    assert R.branch_switch_problem(f, b128, data128) is None
    for new in (branch_doc(f), branch_doc(f, "128", "w1_18", hx("w2")), {**b128, "source": "default"},
                {**b128, "family": "olmo2-7b"}):
        assert "never switched" in R.branch_switch_problem(f, new, data128), new
    with pytest.raises(R.Refused, match="do not hash"):
        R.branch_switch_problem(f, b128, full)
    # the flags, from the pinned record only
    assert R.oext_flags(f, "c0", data128)["w1_18_record"] == hx("w1")
    for kind in ("c0", "o_only", "o_only_with_regenerate", "arm", "a0_arm"):
        assert R.oext_flags(f, kind, data128)["w1_18_record"] == hx("w1")
    assert R.oext_flags(f, "o_only_with_regenerate", data128, regenerated=True)["dev100_source"] is True
    assert R.oext_flags(f, "o_only", data128)["dev100_source"] is False              # theta0 is never regenerated
    with pytest.raises(R.Refused, match="no O-ext step"):
        R.oext_flags(f, "anchor", data128)
    with pytest.raises(R.Refused, match="do not hash"):
        R.oext_flags(f, "o_only", full)
    pin_of_item(monkeypatch, R.BRANCH_78B, f, full)
    assert R.oext_flags(f, "o_only_with_regenerate", full, regenerated=True) == {"w1_18_record": None,
                                                                                   "dev100_source": False}
    monkeypatch.setitem(R.BRANCH_78B, f, None)
    with pytest.raises(R.Refused, match="BRANCH_78B\\['llama31-8b'\\] is null"):
        R.oext_flags(f, "o_only", full)


def test_29b_every_oext_kind_refuses_its_job_while_oext_78b_or_the_branch_record_is_null(monkeypatch):
    """GXB R-4 (K1V-10): until K3 wires `oext_78b.py <command> --family F`, no test asserts an O-ext command line;
    instead every scorer-block O-ext kind (c0, o_only, o_only_with_regenerate) refuses to build its job while
    OEXT_78B or the family's branch record (BRANCH_78B) is null, and w1_18 while its own route pin W1_18_78B is null
    (I: T-O2 fills OEXT_78B and the branch only after the W1-18 pod, so W1-18 cannot wait on them)."""
    f = "olmo2-7b"
    oext = {"files": {R.OEXT_UNIT_SCRIPT: hx("w")}, "inputs": {"oext_bank": hx("b"), "oext_record": hx("r")}}
    monkeypatch.setitem(R.C0_SOURCE, f, {"complete_sha256": hx("c"), "e1_fingerprint": hx("e")})
    units = {"o_only": (None, None), "c0": ("R", 1101), "o_only_with_regenerate": ("a0", 1102)}
    for o, b in ((None, None), (oext, None), (None, {"path": "records/branch.json", "sha256": hx("br")})):
        monkeypatch.setitem(R.OEXT_78B, f, o)
        monkeypatch.setitem(R.BRANCH_78B, f, b)
        for kind, (arm, seed) in units.items():
            want = ([] if o else ["OEXT_78B"]) + ([] if b else ["BRANCH_78B"])
            with pytest.raises(R.Refused, match=" ".join(f"{p} waits for" for p in want[:1])):
                R.sc_pins_or_refuse(f, kind, "X", pins78_doc(), arm, seed)
            missing = [p for p, _ in R.sc_missing_pins(f, kind, "X", pins78_doc(), arm, seed)]
            assert set(want) <= set(missing), (kind, missing)
    monkeypatch.setitem(R.OEXT_78B, f, oext)
    monkeypatch.setitem(R.BRANCH_78B, f, {"path": "records/branch.json", "sha256": hx("br")})
    for kind, (arm, seed) in units.items():
        R.sc_pins_or_refuse(f, kind, "X", pins78_doc(), arm, seed)
    with pytest.raises(R.Refused, match="W1_18_78B waits for"):
        R.sc_pins_or_refuse(f, "w1_18", "X", pins78_doc())
    monkeypatch.setitem(R.BRANCH_78B, f, {"path": "/abs.json", "sha256": hx("br")})
    with pytest.raises(R.Refused, match="BRANCH_78B\\['olmo2-7b'\\] is not a .path, sha256. pin"):
        R.sc_pin_values(f, pins78_doc())
