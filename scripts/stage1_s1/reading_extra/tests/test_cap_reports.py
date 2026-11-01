"""LN-14's transfer bar and LN-19's flag-change shares (cap_reports.py; REV4:554-555): every unit's planted values
copied by key and pooled by hand; the routes; the bar both ways and its recomputed pass; Branch full; a missing or a
second transfer report; the bindings to the builder's record, plan.json and the seals; the command line."""

from __future__ import annotations

import copy
import json
import re

import extra_kit as ek
import pytest
import synth_kit as sk

from scripts.stage1_s1.reading.settings import Refusal
from scripts.stage1_s1.reading_extra import cap_reports as cap
from scripts.stage1_s1.reading_input.__main__ import main as builder

VALUE = re.compile(r"\d\.\d{3,}")


@pytest.fixture(scope="module")
def worlds(tmp_path_factory):
    cache = {}

    def get(reading="plan_a", branch="128", transfer=None, transfers=1):
        key = (reading, branch, json.dumps(transfer, sort_keys=True), transfers)
        if key not in cache:
            root = tmp_path_factory.mktemp("cap")
            s = sk.make(root / "w", reading, branch=branch)
            planted = ek.with_caps(s, transfer=transfer, transfers=transfers)
            rec = root / "sources.json"
            assert builder(s.args(root / "tables.json", rec, overlap=False)) == 0
            cache[key] = (s, planted, rec)
        return cache[key]
    return get


def read(s, rec, record=None):
    return cap.read(s.kit, record if record is not None else json.loads(rec.read_text()), sk.sha(rec.read_bytes()))


def test_every_unit_copied_and_pooled_by_hand(worlds):
    s, planted, rec = worlds()
    out = read(s, rec)
    record = json.loads(rec.read_text())
    units = out["ln19"]["units"]
    assert set(units) == set(record["cells"]) | set(record["references"]) | {"theta0"}
    assert len(record["references"]) == 24 and out["branch"] == "128"
    used = []
    for label, u in units.items():
        src = u["source"]
        assert u["flag_change"] == planted[(src["host"], src["folder"])], label
        used.append(u["flag_change"])
        if label == "theta0":
            assert u["dev100_route"] == "generated" and u["group"] == "theta0"
        elif label in record["references"] and label.startswith(("ref-prefix", "ref-scale", "ref-external")):
            assert u["dev100_route"] is None and src["folder"] == record["references"][label]["unit"]["folder"].split(":")[-1].split("/", 1)[1]
        elif label.split(" ")[0] in ("a0", "R") and int(label.split(" ")[1]) <= 1103:
            assert u["dev100_route"] == "source_unit"
        elif label in record["cells"]:
            assert u["dev100_route"] == "unit_eval"
    for source in ("dev100", "phtest"):
        n = sum(f[source]["prompts_with_both_forms"] for f in used)
        changed = sum(f[source]["changed"] for f in used)
        pooled = dict(out["ln19"]["pooled"][source])
        theta0 = pooled.pop("theta0_ln14", None)
        assert pooled == {"units": len(used), "prompts_with_both_forms": n, "changed": changed,
                          "share": changed / n if n else None, "note": None if n else cap.NO_BOTH_FORMS[source]}
        assert (theta0 is None) == (source == "dev100")
    a1 = [units[k]["flag_change"]["dev100"] for k in units if k.startswith("A1 ")]
    assert out["ln19"]["by_arm_or_reference"]["A1"]["dev100"]["changed"] == sum(f["changed"] for f in a1)
    assert out["ln19"]["by_arm_or_reference"]["A1"]["dev100"]["units"] == 6
    assert "ref-scale 0.9" in out["ln19"]["by_arm_or_reference"] and "theta0" not in out["ln19"]["by_arm_or_reference"]
    assert out["route_per_source"] == ek.ROUTES["128"]
    assert out["provenance"]["kit"]["plan_sha256"] == record["kit"]["plan_sha256"]


def test_the_transfer_bar_passes(worlds):
    s, planted, rec = worlds()
    ln14 = read(s, rec)["ln14"]
    t = ek.transfer_summary()
    assert ln14["applies"] is True and ln14["passes"] is True and ln14["text"] == cap.LN14_PASS
    assert {k: ln14["report"][k] for k in ("prompts", "flags_agree", "refused_full", "refused_cut", "count_move")} == \
        {k: t["bar"][k] for k in ("prompts", "flags_agree", "refused_full", "refused_cut", "count_move")}
    assert ln14["report"]["flag_change"] == t["flag_change"] and ln14["source"]["host"] == "a-2"


@pytest.mark.parametrize("agree,full,cut,passes", [(388, 50, 49, True), (387, 50, 49, False), (396, 50, 42, True),
                                                   (396, 50, 41, False)])
def test_the_bar_at_its_edges(worlds, agree, full, cut, passes):
    s, planted, rec = worlds("plan_a_block_a_only", transfer=ek.transfer_summary(agree=agree, full=full, cut=cut))
    ln14 = read(s, rec)["ln14"]
    assert ln14["passes"] is passes and ln14["text"] == (cap.LN14_PASS if passes else cap.LN14_FAIL)


def test_a_pass_that_its_counts_do_not_give_refuses(worlds):
    s, planted, rec = worlds("plan_a_block_a_only", transfer=ek.transfer_summary(agree=380, passes=True))
    with pytest.raises(Refusal, match="pass is not its counts read by W1-18's bar"):
        read(s, rec)


def test_the_phtest_line_points_to_theta0s_ln14_pass(worlds):
    """The lead's R4.2: under Branch 128 no unit holds both forms of its PHTest answers (made at the cut cap only),
    but theta0's LN-14 pass holds both forms of its 400; the LN-19 PHTest lines say so, never "no full answer
    exists", and the pooled line copies theta0's LN-14 share beside it."""
    s, planted, rec = worlds()
    out = read(s, rec)
    line = out["ln19"]["pooled"]["phtest"]
    assert line["prompts_with_both_forms"] == 0 and line["share"] is None
    assert "no full answer exists" not in line["note"] and "theta0's LN-14" in line["note"]
    assert "ln14.report.flag_change" in line["note"] and "cut cap only" in line["note"]
    fc = out["ln14"]["report"]["flag_change"]
    assert fc == {"prompts_with_both_forms": 400, "changed": 4, "share": 4 / 400, "became_refused": 0,
                  "became_not_refused": 4, "note": None}
    assert line["theta0_ln14"] == {"prompts_with_both_forms": 400, "changed": 4, "share": fc["share"],
                                   "source": "ln14.report.flag_change (theta0's transfer pass, REV4:554)"}
    for arm, lines in out["ln19"]["by_arm_or_reference"].items():
        assert lines["phtest"]["note"] == line["note"] and "theta0_ln14" not in lines["phtest"], arm
        assert lines["dev100"]["note"] is None, arm
    assert "theta0_ln14" not in out["ln19"]["pooled"]["dev100"]
    assert "no full answer exists" not in json.dumps(out["ln19"]["pooled"]) + json.dumps(out["readings"])
    s2, planted2, rec2 = worlds("plan_a_block_a_only", transfers=0)              # LN-14 not run: the pointer says why
    line2 = read(s2, rec2)["ln19"]["pooled"]["phtest"]
    assert line2["note"] == cap.NO_BOTH_FORMS["phtest"] and line2["theta0_ln14"]["share"] is None
    assert line2["theta0_ln14"]["why"].startswith("not run") and line2["theta0_ln14"]["changed"] is None
    s3, planted3, rec3 = worlds("plan_a_block_a_only", branch="full")           # every unit holds both forms
    line3 = read(s3, rec3)["ln19"]["pooled"]["phtest"]
    assert line3["note"] is None and line3["share"] is not None
    assert line3["theta0_ln14"]["share"] is None and "Branch 128 only" in line3["theta0_ln14"]["why"]


def test_branch_full_has_no_transfer_report(worlds):
    s, planted, rec = worlds("plan_a_block_a_only", branch="full")
    out = read(s, rec)
    assert out["branch"] == "full" and out["ln14"]["applies"] is False and out["ln14"]["report"] is None
    assert out["route_per_source"] == ek.ROUTES["full"]
    assert out["ln19"]["pooled"]["phtest"]["prompts_with_both_forms"] == 400 * out["ln19"]["pooled"]["phtest"]["units"]


def test_a_missing_transfer_report_is_not_run(worlds):
    s, planted, rec = worlds("plan_a_block_a_only", transfers=0)
    ln14 = read(s, rec)["ln14"]
    assert ln14["applies"] is True and ln14["report"] is None and ln14["text"].startswith("not run")


def test_two_transfer_reports_refuse(worlds):
    s, planted, rec = worlds("plan_a_block_a_only", transfers=2)
    with pytest.raises(Refusal, match="2 complete transfer_report jobs"):
        read(s, rec)


def _record_edit(fn):
    def apply(record):
        r = copy.deepcopy(record)
        fn(r)
        return r
    return apply


@pytest.mark.parametrize("edit,match", [
    (_record_edit(lambda r: r.update(kind="x")), "not the input builder's version-1 sources record"),
    (_record_edit(lambda r: r["kit"].update(plan_sha256="0" * 64)), "plan.json is not the one"),
    (_record_edit(lambda r: r["kit"]["seals"].update(A="0" * 64)), "block A's seal is not the one"),
    (_record_edit(lambda r: r["kit"]["seals"].update(Z="0" * 64)), "does not name the seals of the reading's blocks"),
    (_record_edit(lambda r: r["cells"]["S1 1104"]["o"][0]["files"].update({"oext_summary.json": "1" * 64})),
     "S1 1104: oext_summary.json is not the file the builder's record names"),
    (_record_edit(lambda r: r["cells"]["S1 1104"]["o"][0].update(complete_sha256="1" * 64)),
     "S1 1104: no folder of the reading's blocks"),
    (_record_edit(lambda r: r["cells"]["S1 1104"].update(o=[])), "S1 1104: the builder's record names no single"),
    (_record_edit(lambda r: r["theta0"].update(o=None)), "theta0: the builder's record names no O-only folder"),
])
def test_binding_refusals(worlds, edit, match):
    s, planted, rec = worlds("plan_a_block_a_only")
    with pytest.raises(Refusal, match=match):
        read(s, rec, edit(json.loads(rec.read_text())))


def test_a_changed_summary_refuses(worlds, tmp_path):
    s0, planted, rec = worlds("plan_a_block_a_only")
    s = sk.copy(s0, tmp_path / "w")
    host, i, job = sk.find_job(s.plan(), "arm", "S1", 1104)
    path = s.kit / "retrieved" / host / "tree" / f"job-{i}" / "oext" / "oext_summary.json"
    doc = json.loads(path.read_text())
    doc["flag_change"]["dev100"]["changed"] += 1
    path.write_bytes(sk.jbytes(doc))
    with pytest.raises(Refusal, match="hashes to"):                     # the builder's Folder: COMPLETE.json's hash
        read(s, rec)


def test_an_inconsistent_flag_change_refuses(tmp_path):
    s = sk.make(tmp_path / "w", "plan_a_block_a_only")
    ek.with_caps(s)
    host, i, job = sk.find_job(s.plan(), "arm", "H1", 1103)
    path = s.kit / "retrieved" / host / "tree" / f"job-{i}" / "oext" / "oext_summary.json"
    doc = json.loads(path.read_text())
    doc["flag_change"]["dev100"]["share"] = 0.5
    path.write_bytes(sk.jbytes(doc))
    sk.rehash_job(s, host, i)
    rec = tmp_path / "sources.json"
    assert builder(s.args(tmp_path / "tables.json", rec, overlap=False)) == 0
    with pytest.raises(Refusal, match="H1 1103: flag_change dev100: the share is not changed / prompts"):
        read(s, rec)


def test_two_routes_refuse(tmp_path):
    s = sk.make(tmp_path / "w", "plan_a_block_a_only")
    ek.with_caps(s)
    host, i, job = sk.find_job(s.plan(), "arm", "L1", 1102)
    path = s.kit / "retrieved" / host / "tree" / f"job-{i}" / "oext" / "oext_summary.json"
    doc = json.loads(path.read_text())
    doc["route"]["phtest"] = "another route"
    path.write_bytes(sk.jbytes(doc))
    sk.rehash_job(s, host, i)
    rec = tmp_path / "sources.json"
    assert builder(s.args(tmp_path / "tables.json", rec, overlap=False)) == 0
    with pytest.raises(Refusal, match="do not hold one branch and one route per source"):
        read(s, rec)


@pytest.mark.parametrize("block,match", [
    ({"prompts_with_both_forms": 100, "changed": 3, "share": 0.03, "became_refused": 1, "became_not_refused": 1},
     "do not add up"),
    ({"prompts_with_both_forms": 2, "changed": 3, "share": 1.5, "became_refused": 3, "became_not_refused": 0},
     "do not add up"),
    ({"prompts_with_both_forms": 0, "changed": 0, "share": 0.0, "became_refused": 0, "became_not_refused": 0},
     "a share with no prompt"),
    ({"prompts_with_both_forms": 100, "changed": True, "share": 0.01, "became_refused": 1, "became_not_refused": 0},
     "changed is not a count"),
    ({"prompts_with_both_forms": 100, "changed": 1, "share": None, "became_refused": 1, "became_not_refused": 0},
     "share is not a finite number"),
    (None, "no flag_change block"),
])
def test_flag_change_blocks(block, match):
    with pytest.raises(Refusal, match=match):
        cap.flag_change(block, "x")


def test_the_pinned_rule_texts_are_rev4s():
    rev4 = (sk.TREE / "research" / "experiments" / "2026-10-17-stage1-preregistration-rev3" /
            "stage1-preregistration-rev4.md")
    if not rev4.is_file():
        pytest.skip("the pre-registration is not in this tree")
    text = rev4.read_text()
    for needle in ("If θ0 fails the bar, the paper states the cut as a limit for PHTest; the cap rule does not switch.",
                   "The record states the route per source. The cap record also prints the measured flag-change share "
                   "per source (full against cut, where both exist)"):
        assert needle in text and any(needle in r for r in cap.RULE)


def test_command_line_prints_the_bar_word_only(worlds, tmp_path, capsys):
    s, planted, rec = worlds("plan_a_block_a_only", transfer=ek.transfer_summary(agree=380))
    capsys.readouterr()                                                  # the fixture's builder lines
    out = tmp_path / "cap.json"
    args = ["--kit", str(s.kit), "--record", str(rec), "--out", str(out)]
    assert cap.main(args) == 0
    printed = capsys.readouterr()
    assert printed.out.splitlines() == [f"wrote {out} sha256 {sk.sha(out.read_bytes())}", "LN-14 transfer bar: fails"]
    assert not VALUE.search(printed.out) and sk.TEXT not in out.read_text()
    assert cap.main(args) == 2 and "cap.json exists" in capsys.readouterr().err
