"""Kit round 34 (1 Nov 2026; B14's similarity pass on its own block; the lead's ruling, FOCUS 2026-11-01T04:55 UTC; the
design report reading-prep/1b-b14-similarity.md route (i)), on CPU, without RunPod, Hugging Face or GitHub. Expected
values are written by hand; every input is synthetic but the pins' own sources in this repository (B14's script and
settings, the three add-edit records), which are hashed or read by key only.

J22 ("similarity"): its numbers and block "sim"'s cap, guard, spend and need by hand; init-block from the balance
(addendum §36's record) with the job's inputs by SHA-256 (similarity_entry: the kit's pins, the edit sources, the
files the S1, S3 and S4 arm runs trained on) and every refusal of another shape, engine, recipe, arm or block; the
re-check at release; the runner's exact command and its checks before any step; its output and text-free record (an
output off the pins, a missing printed SHA-256 or an existing record is a crash that the record explains); check-plan
on the round-33 and round-34 packs; the finisher's light check and record-done (which prints the output's path and
SHA-256 for the strata step); a crashed pass re-run once from the block's contingency. No similarity value is printed
or recorded (SENTINEL scan)."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import sys

import pytest

import test_stage1_runkit as rk
import test_stage1_runner as rn
from test_stage1_runkit import w  # noqa: F401 - the World fixture (a copy of the kit, synthetic pins)
from test_stage1_runner import kit  # noqa: F401 - the kit fixture (a copy of the kit and a module loader)

sha, write_json = rk.sha, rk.write_json
Pod, job, write, H, P, REC, REPO, KIT = rn.Pod, rn.job, rn.write, rn.H, rn.P, rn.REC, rn.REPO, rn.KIT
SENTINELS = rn.SENTINELS
SIM = [{"hosts": [[{"kind": "similarity"}]]}]
USER_WORDS = "no just start it now ill fund it when i feel like this is a rule"     # addendum §36, verbatim
OUT, RECORD, LEDGER = "job-0/similarity/similarity.json", "job-0/similarity-record.json", "job-0/cost-ledger.json"


def _real_rules():
    """The kit's own stage1_rules.py, loaded by path under its own name (no sys.modules entry is left)."""
    spec = importlib.util.spec_from_file_location("s1_rules_round34", KIT / "stage1_rules.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _good_doc(r, recipe: str = "c" * 64) -> dict:
    """A synthetic similarity.json on the rules' pins, its provenance written out by hand as overlap_similarity.py
    writes it (inputs: prepared/manifest.json, prepared/banks/dev.jsonl, recipe, add/NAME); per-prompt values carry a
    SENTINEL."""
    return {"kind": "stage1 overlap similarity", "version": 1, "requirement": "synthetic",
            "eval": {"bank": "dev", "kinds": ["harm"], "prompts": 200, "prompt_ids": ["dev-1"]},
            "add_sets": {n: {"edit_sha256": d, "rows": 48, "row_ids": ["r1"],
                             "per_prompt": {"dev-1": {"s_max": float(SENTINELS[0]), "nearest": "r1"}}}
                         for n, d in r.SIM_ADD_SETS.items()},
            "provenance": {"script_sha256": r.S1_CODE["scripts/stage1_s1/overlap_similarity.py"],
                           "settings_sha256": r.S1_CODE["scripts/stage1_s1/settings/overlap_similarity.json"],
                           "inputs": {"prepared/manifest.json": r.PREPARED_MANIFESTS["prepared-kt-dolly-olmo2"],
                                      "prepared/banks/dev.jsonl": r.SIM_DEV_BANK["sha256"], "recipe": recipe,
                                      **{f"add/{n}": d for n, d in r.SIM_ADD_SETS.items()}}}}


# ===== J22's numbers and the pins' sources =========================================================================

def test_j22_numbers_and_block_sims_cap_guard_spend_and_need_by_hand(w):
    """J22: measured upper 600 s (E), upper 1.5 x 600 = 900 s, start requirement 900 + 1,800 = 2,700 s, counted 0,
    unmeasured, unit-free, no O500 term; block sim only. One pod: cap = 42 min + 2,700 s = 5,220 s, up to 0.25 h ->
    1.5 h; guard $6 + 1.5 x $1.85 = $8.775; upper spend (2,520 + 600) / 3,600 x $1.79 = $1.5513; need: base = $8.775
    to the cent, half up, $8.78; 1.25 x $8.78 = $10.975 -> $10.98; contingency $2.20, which pays one re-run on a new
    pod ($1.5513) and not a second."""
    r = w.rules
    j = r.job_record("similarity", None, None, None, None, {"e1_upper_s": rk.E1, "training_s": rk.T}, recipe="B")
    assert (j["job_id"], j["upper_s"], j["start_requirement_s"], j["measured_upper_s"], j["spend_upper_s"],
            j["counted"], j["unmeasured"], j["o500_s"], j["engine"], j["recipe"]) == \
        ("J22", 900.0, 2700.0, 600.0, 600.0, 0, True, 0.0, "X", "B")
    assert list(r.KIND_IDS.values()).count("J22") == 1 and r.KINDS[-1] == "similarity"
    assert "similarity" in r.UNITLESS_KINDS and "similarity" not in r.BANK500_KINDS | r.ONE_COUNTED
    assert (r.BLOCKS[6], r.FUNDING_BLOCK["sim"], r.HOST_PREFIX["sim"], r.BLOCK_KINDS["sim"]) == \
        ("sim", "sim", "sim", ("similarity",))           # kit round 35 appends block P after sim
    assert [b for b, kinds in r.BLOCK_KINDS.items() if "similarity" in kinds] == ["sim"]
    cap = r.cap_hours([j])
    assert cap == rk.quarter_up(2520 + 2700) == 1.5
    assert r.guard_usd(cap) == pytest.approx(8.775) and rk.cents(r.guard_usd(cap)) == 8.78
    spend = (2520 + 600) / 3600 * 1.79
    assert r.pod_spend_usd([j]) == pytest.approx(spend) and round(spend, 4) == 1.5513
    need = r.funding_need_usd([[{"cap_hours": cap, "spend_usd": spend}]], r.CONTINGENCY_FACTOR)
    assert (need["base_need_usd"], need["need_usd"], need["contingency_usd"]) == (8.78, 10.98, 2.2)
    assert rk.times_125(8.78) == 10.98
    assert r.rerun_cost_usd(j, True) == pytest.approx(spend) and 2.2 - spend < spend    # one re-run, not two


def test_the_pins_are_this_repositorys_b14_files_settings_and_add_edit_records():
    """The pins against their sources here (hashes and keys only): B14's script and settings are S1_CODE's and the
    script's own SETTINGS_SHA256 literal names those settings; its output's name, kind and printed line are the kit's
    (SIM_OUTPUT, SIM_OUTPUT_KIND, SIM_PRINTED); the settings pin PREPARED_MANIFESTS' manifest, engine X, the dev bank's
    200 harm prompts and the add sets S1, S3 and S4 of 48 rows, a pure add edit; each add set's pin is the edit file its
    add-edit record names (.ai/inputs/stage1-commitments-20261016/add-sN/add_edit_record.json, file add_sN.json, arm
    edit-<SHA-256>). The dev bank's pin is its prepared manifest's entry (M, outside this repository)."""
    r = _real_rules()
    script, settings = REPO / r.SIM_SCRIPT, REPO / r.SIM_SETTINGS
    assert (r.SIM_SCRIPT, r.SIM_SETTINGS) == ("scripts/stage1_s1/overlap_similarity.py",
                                              "scripts/stage1_s1/settings/overlap_similarity.json")
    assert sha(script) == r.S1_CODE[r.SIM_SCRIPT] == "f8305c712109b1bc733769b806c3a37cee9726feab0694e89f42dfc47d4f79f4"
    assert sha(settings) == r.S1_CODE[r.SIM_SETTINGS] == \
        "27db4c3faafc41c4278ff6ca7d1ded0a0fb1a07ae484c4bbf65702f5545ac754"
    text = script.read_text()
    assert re.findall(r'^SETTINGS_SHA256 = "([0-9a-f]{64})"$', text, re.M) == [r.S1_CODE[r.SIM_SETTINGS]]
    assert f'OUTPUT = "{r.SIM_OUTPUT}"' in text and f'RECORD_KIND = "{r.SIM_OUTPUT_KIND}"' in text
    assert 'print(f"wrote {OUTPUT} into {args.out} ({sha256_bytes(data)})")' in text
    assert re.fullmatch(r.SIM_PRINTED, f"wrote similarity.json into job-0/similarity ({'a' * 64})")
    s = json.loads(settings.read_text())
    assert s["prepared_manifest_sha256"] == r.PREPARED_MANIFESTS["prepared-kt-dolly-olmo2"] and s["engine_x"] == \
        r.ENGINES["X"]
    assert (s["eval"]["bank"], s["eval"]["kinds"], s["eval"]["prompts"]) == ("dev", ["harm"], r.SIM_PROMPTS) and \
        r.SIM_PROMPTS == 200
    assert (s["add_sets"]["names"], s["add_sets"]["rows_each"], s["add_sets"]["edit_kind"]) == \
        (sorted(r.SIM_ADD_SETS), r.SIM_ROWS, "add") == (["S1", "S3", "S4"], 48, "add")
    for name, pin in r.SIM_ADD_SETS.items():
        rec = json.loads((REPO / ".ai/inputs/stage1-commitments-20261016" / f"add-{name.lower()}" /
                          "add_edit_record.json").read_text())
        found = [(e["sha256"], e["arm"]) for e in rec["edits"] if e["file"] == f"add_{name.lower()}.json"]
        assert rec["kind"] == "stage1 add-edit record" and found == [(pin, f"edit-{pin}")], name
    assert r.SIM_DEV_BANK == {"path": "banks/dev.jsonl",
                              "sha256": "1438ff51c7e470bec43f7127e8121db3aa0f41ed5e434402b8c81688d6f7da7e"}


# ===== the output check and the record (stage1_rules) ===============================================================

def _set(path, value):
    """A change of one field of a document: ``path`` is a dotted name or a tuple of keys; ``value`` KeyError deletes
    the field."""
    def change(doc):
        keys = path.split(".") if isinstance(path, str) else list(path)
        node = doc
        for k in keys[:-1]:
            node = node[k]
        if value is KeyError:
            del node[keys[-1]]
        else:
            node[keys[-1]] = value
    return change


@pytest.mark.parametrize("change, problems", [
    (None, []),
    (_set("kind", "stage1 overlap strata"), ["not a version-1 'stage1 overlap similarity' record"]),
    (_set("version", 2), ["not a version-1 'stage1 overlap similarity' record"]),
    (_set("provenance.script_sha256", "0" * 64), ["provenance.script_sha256"]),
    (_set("provenance.settings_sha256", "0" * 64), ["provenance.settings_sha256"]),
    (_set(("provenance", "inputs", "add/S3"), "1" * 64), ["provenance.inputs[add/S3]"]),
    (_set(("provenance", "inputs", "recipe"), "2" * 64), ["provenance.inputs[recipe]"]),
    (_set(("provenance", "inputs", "prepared/manifest.json"), KeyError),
     ["provenance.inputs[prepared/manifest.json]"]),
    (_set(("provenance", "inputs", "prepared/banks/selector.jsonl"), "3" * 64),
     ["provenance.inputs[prepared/banks/selector.jsonl]"]),
    (_set(("provenance", "inputs", "add/S1"), "a harm prompt's text"), ["provenance.inputs[add/S1]"]),
    (_set("eval.prompts", 199), ["eval.prompts"]),
    (_set("eval.prompts", 200.0), ["eval.prompts"]),
    (_set("eval.prompts", True), ["eval.prompts"]),
    (_set("add_sets.S4", KeyError), ["add_sets (names)", "add_sets.S4"]),
    (_set("add_sets.S2", {"edit_sha256": "4" * 64, "rows": 48}), ["add_sets (names)"]),
    (_set("add_sets.S1.rows", 47), ["add_sets.S1"]),
    (_set("add_sets.S1.edit_sha256", "5" * 64), ["add_sets.S1"])])
def test_the_output_check_names_every_field_off_the_pins(w, change, problems):
    """stage1_rules.similarity_problems by hand: each field off the kit's pins is named (names only); the per-prompt
    values are never read (a changed one is no problem)."""
    doc = _good_doc(w.rules)
    if change:
        change(doc)
    assert w.rules.similarity_problems(doc, "c" * 64) == problems
    doc["add_sets"]["S1"]["per_prompt"]["dev-1"]["s_max"] = -1.0
    assert w.rules.similarity_problems(doc, "c" * 64) == problems
    if change is None:
        assert w.rules.similarity_problems(doc, None) == ["provenance.inputs[recipe]"]   # no REC config: never on pins
        assert w.rules.similarity_problems([doc], "c" * 64) == ["not a version-1 'stage1 overlap similarity' record"]
        del doc["provenance"]["inputs"]["recipe"]
        assert w.rules.similarity_problems(doc, None) == ["provenance.inputs[recipe]"]   # both absent: still no pin


def test_the_record_by_hand_is_canonical_and_text_free(w):
    """similarity_record_doc by hand: ids, the output's path and SHA-256, the printed SHA-256, the provenance's hashes
    and the counts, no problem; a printed SHA-256 that differs or is missing is a problem; a text where a SHA-256
    belongs is recorded as None (no output text reaches the record); canonical_bytes is the engine's canonical JSON."""
    r = w.rules
    doc = _good_doc(r)
    digest = hashlib.sha256(json.dumps(doc).encode()).hexdigest()
    rec = r.similarity_record_doc(doc, "sim-1", 0, digest, digest, "c" * 64)
    assert rec == {"kind": "stage1 similarity record", "version": 1, "host": "sim-1", "job": 0,
                   "output": {"path": OUT, "sha256": digest}, "printed_sha256": digest,
                   "script_sha256": r.S1_CODE[r.SIM_SCRIPT], "settings_sha256": r.S1_CODE[r.SIM_SETTINGS],
                   "inputs": {"add/S1": r.SIM_ADD_SETS["S1"], "add/S3": r.SIM_ADD_SETS["S3"],
                              "add/S4": r.SIM_ADD_SETS["S4"], "prepared/banks/dev.jsonl": r.SIM_DEV_BANK["sha256"],
                              "prepared/manifest.json": r.PREPARED_MANIFESTS["prepared-kt-dolly-olmo2"],
                              "recipe": "c" * 64},
                   "counts": {"prompts": 200, "rows": {"S1": 48, "S3": 48, "S4": 48}}, "problems": []}
    printed = "the SHA-256 the script printed is missing or not the file's"
    assert r.similarity_record_doc(doc, "sim-1", 0, digest, "0" * 64, "c" * 64)["problems"] == [printed]
    assert r.similarity_record_doc(doc, "sim-1", 0, digest, None, "c" * 64)["problems"] == [printed]
    doc["provenance"]["inputs"]["add/S1"] = "TEXT OF AN ADDED ROW"
    doc["provenance"]["script_sha256"] = "TEXT"
    bad = r.similarity_record_doc(doc, "sim-1", 0, digest, digest, "c" * 64)
    assert (bad["inputs"]["add/S1"], bad["script_sha256"]) == (None, None) and "TEXT" not in json.dumps(bad)
    assert bad["problems"] == ["provenance.script_sha256", "provenance.inputs[add/S1]"]
    assert not any(s in json.dumps(rec) for s in SENTINELS)
    assert r.canonical_bytes(rec) == (json.dumps(rec, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    with pytest.raises(ValueError):
        r.canonical_bytes({"x": float("nan")})


# ===== plan_tool: block sim ==========================================================================================

def _arms_done(w) -> tuple[dict, str]:
    """W1-18 (S1-0), Gate B's records and the sealed edit record (L1, H1, S1, S3, S4 and R 6-10), then block A
    planned and done (the deal's 20 runs, S1, S3 and S4 at 1102-1104 among them, with the sealed record's files);
    stage1_rules.SIM_ADD_SETS set to those three files' SHA-256 for this test. Returns (pins, the record's SHA-256)."""
    w.s10()
    w.gateb()
    sealed = w.sealed()
    rk._finish_block_a(w)
    pins = {n: sha(w.repo / "tmp" / "sealed" / f"{n}.edit.json") for n in ("S1", "S3", "S4")}
    w.mp.setattr(w.rules, "SIM_ADD_SETS", dict(pins))
    return pins, sealed


def _rule_funding(w, amount: float = 10.98, **change) -> str:
    """Block sim's funding record under the user's start-from-the-balance rule (addendum §36): source and the user's
    decision record {path, sha256} (a synthetic copy here)."""
    dec = write_json(w.repo / "records" / "user_decision_start.json",
                     {"kind": w.tool.FUNDING_RULE_KIND, "user_words": USER_WORDS})
    return w.funding("sim", amount, source=w.tool.FUNDING_SOURCE_RULE,
                     user_decision={"path": str(dec), "sha256": sha(dec)}, **change)


def _init_sim(w, launches=SIM, funding=None, dry_run: bool = False) -> dict:
    return w.tool.init_block(argparse.Namespace(block="sim", jobs=w.jobs(launches), funding=funding or _rule_funding(w),
                                                dry_run=dry_run, group_jobs=None))


def _entry(r, pins: dict, sealed: str) -> dict:
    """plan_tool.similarity_entry by hand."""
    return {"script": {"path": "scripts/stage1_s1/overlap_similarity.py",
                       "sha256": "f8305c712109b1bc733769b806c3a37cee9726feab0694e89f42dfc47d4f79f4"},
            "settings": {"path": "scripts/stage1_s1/settings/overlap_similarity.json",
                         "sha256": "27db4c3faafc41c4278ff6ca7d1ded0a0fb1a07ae484c4bbf65702f5545ac754"},
            "manifest_sha256": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9",
            "dev_bank": {"path": "banks/dev.jsonl",
                         "sha256": "1438ff51c7e470bec43f7127e8121db3aa0f41ed5e434402b8c81688d6f7da7e"},
            "add_sets": {n: {"path": f"tmp/sealed/{n}.edit.json", "sha256": d, "source": f"sealed:{sealed}"}
                         for n, d in pins.items()}}


def test_block_sim_plans_one_pod_with_the_pinned_inputs_from_the_balance(w):
    """init-block sim: the dry run prints the need by hand ($10.98; one pod, 1.5 h, guard $8.78, counted 0); a record
    $0.01 below it refuses; under addendum §36's record the block is planned and its launch released at once: host
    sim-1 (block sim, role job, engine X, cap 1.5 h), its one job J22 with recipe B (REC registered in plan.json's
    recipes), no arm, seed or edit, and its inputs by hand; the funding group sim with its contingency $2.20; a second
    init refuses."""
    pins, sealed = _arms_done(w)
    dry = _init_sim(w, dry_run=True)
    assert (dry["funding_block"], dry["need_usd"], dry["base_need_usd"], dry["contingency_usd"]) == \
        ("sim", 10.98, 8.78, 2.2)
    assert dry["pods"] == [{"launch": 0, "cap_hours": 1.5, "guard_usd": 8.78, "counted": 0,
                            "jobs": ["similarity:None:None"]}]
    assert "sim" not in w.plan()["blocks"] and "sim-1" not in w.plan()["hosts"]
    with pytest.raises(SystemExit, match=r"the funding \$10\.97 is below the need \$10\.98"):
        _init_sim(w, funding=_rule_funding(w, amount=10.97))
    out = _init_sim(w)
    assert out["hosts"] == ["sim-1"] and out["released"] == ["sim-1"] and out["need_usd"] == 10.98
    plan = w.plan()
    h = plan["hosts"]["sim-1"]
    assert (h["block"], h["wave"], h["role"], h["engine"], h["engine_sha256"], h["cap_hours"], h["counted"],
            h["launch"], h["base_eval"]) == ("sim", "sim", "job", "X", rk.X, 1.5, 0, 0, False)
    assert h["guard_usd"] == pytest.approx(8.775) and h["spend_upper_usd"] == pytest.approx(3120 / 3600 * 1.79)
    [j] = h["jobs"]
    assert (j["kind"], j["job_id"], j["recipe"], j["engine"], j["arm"], j["seed"], j["edit"], j["status"]) == \
        ("similarity", "J22", "B", "X", None, None, None, "planned")
    assert j["similarity"] == _entry(w.rules, pins, sealed)
    assert plan["recipes"][w.rules.REC]["sha256"] == w.rules.RECIPE_PINS[w.rules.REC]
    b = plan["blocks"]["sim"]
    assert (b["released"], b["launches"], b["funding"]["source"], b["funding"]["block"]) == \
        (1, [{"hosts": ["sim-1"]}], "user rule: start from the balance", "sim")
    assert plan["contingency"]["sim"]["usd"] == plan["contingency"]["sim"]["remaining_usd"] == 2.2
    with pytest.raises(SystemExit, match="block sim is already planned"):
        _init_sim(w)


@pytest.mark.parametrize("launches, match", [
    ([{"hosts": [[{"kind": "similarity"}, {"kind": "similarity"}]]}], "block sim: one launch of one pod"),
    ([{"hosts": [[{"kind": "similarity"}], [{"kind": "similarity"}]]}], "block sim: one launch of one pod"),
    (SIM + SIM, "block sim: one launch of one pod"),
    (SIM + [{"judge": {"arms": 1, "judge": "granite"}}], "block sim: one launch of one pod"),
    ([{"hosts": [[{"kind": "similarity", "engine": "Y"}]]}], "similarity pass runs on engine X"),
    ([{"hosts": [[{"kind": "similarity", "recipe": "S"}]]}], "a similarity job runs recipe B"),
    ([{"hosts": [[{"kind": "similarity", "arm": "S1"}]]}], "a similarity job has no arm or seed"),
    ([{"hosts": [[{"kind": "similarity", "seed": 1101}]]}], "a similarity job has no arm or seed"),
    ([{"hosts": [[{"kind": "w1_18"}]]}], "a w1_18 job does not belong to block sim"),
    ([{"hosts": [[{"kind": "l1_scan"}]]}], "a l1_scan job does not belong to block sim"),
    ([{"deal": [0]}], "plan A has no block 'sim'")])
def test_block_sim_refuses_another_shape_engine_recipe_arm_or_job(w, launches, match):
    """Block sim holds B14's pass alone on one pod, engine X, recipe REC, no arm or seed; anything else refuses at
    init (nothing is planned)."""
    _arms_done(w)
    with pytest.raises(SystemExit, match=match):
        _init_sim(w, launches)
    assert "sim" not in w.plan()["blocks"] and not any(n.startswith("sim-") for n in w.plan()["hosts"])


def test_a_similarity_job_belongs_to_block_sim_only(w):
    """BLOCK_KINDS: a similarity job in block A's plan refuses (check_job), before anything is planned."""
    w.s10()
    w.gateb()
    w.sealed()
    with pytest.raises(SystemExit, match="a similarity job does not belong to block A"):
        w.init("A", [{"hosts": [[{"kind": "similarity"}]]}] + rk.A_LAUNCHES)
    assert "A" not in w.plan()["blocks"]


def test_the_add_sets_must_be_the_pinned_files_the_s_arm_runs_trained_on(w):
    """similarity_entry both ways: no S1 arm run yet (0 runs, 0 complete); block A's first launch released (2 S1 runs
    with the pinned file, none complete); after block A, a pin that is not the sealed record's file; the edit file
    changed on disk after its record; an S1 arm run that names another edit file; a second sealed record naming
    another S4 file (two sources). Each refuses at init with nothing planned; the good world plans."""
    w.s10()
    w.gateb()
    w.sealed()
    pins = {n: sha(w.repo / "tmp" / "sealed" / f"{n}.edit.json") for n in ("S1", "S3", "S4")}
    w.mp.setattr(w.rules, "SIM_ADD_SETS", dict(pins))

    def refused(match: str) -> None:
        with pytest.raises(SystemExit, match=match):
            _init_sim(w)
        assert "sim" not in w.plan()["blocks"]

    refused(r"B14's add set S1: the pass reads the edit file the S1 arm runs trained on, but plan\.json's 0 S1 "
            r"run\(s\), 0 complete, name \[\]")
    w.init("A", rk.A_LAUNCHES)                          # the deal's pods 0-2 released: S1 at 1103 and 1104 (planned)
    refused(rf"B14's add set S1: .* plan\.json's 2 S1 run\(s\), 0 complete, name \['{pins['S1'][:12]}\.\.\.'\]")
    for host in ("a-1", "a-2", "a-3"):                  # block A done, as test_stage1_runkit._finish_block_a
        w.done(host)
    w.tool.release("A")
    for host in ("a-4", "a-5"):
        w.done(host)
    w.not_run()
    w.mp.setitem(w.rules.SIM_ADD_SETS, "S3", "0" * 64)
    refused(r"B14's add set S3: the edit sources name [0-9a-f]{12}\.\.\., not the kit's pin 000000000000\.\.\.")
    w.mp.setitem(w.rules.SIM_ADD_SETS, "S3", pins["S3"])
    edit = w.repo / "tmp" / "sealed" / "S4.edit.json"
    kept = edit.read_bytes()
    edit.write_bytes(kept + b" ")
    refused("B14's add set S4: the edit file is missing or its SHA-256 is not the pin")
    edit.write_bytes(kept)
    plan = w.plan()
    good = json.loads(json.dumps(plan))
    s1 = sorted((j for h in plan["hosts"].values() for j in h["jobs"] if j["kind"] == "arm" and j["arm"] == "S1"),
                key=lambda j: j["seed"])
    s1[0]["edit"]["sha256"] = "1" * 64
    w.mac.save_plan(plan)
    refused(r"B14's add set S1: .* plan\.json's 3 S1 run\(s\), 3 complete, name \[.*'111111111111\.\.\.'")
    w.mac.save_plan(good)
    other = write_json(w.repo / "tmp" / "sealed" / "S4b.edit.json", {"arm": "S4", "v": 2})
    record = w.plan()["records"]["sealed"]
    w.tool.record_simple("sealed", *w.record({"kind": "stage1 sealed edits", "edits": [
        {"arm": "S4", "path": "tmp/sealed/S4b.edit.json", "sha256": sha(other)}]}))
    refused("B14's add set S4: 2 edit files are named for arm S4 in MAN1, Gate B's MANIFEST and the recorded sealed "
            "records; exactly one must be")
    plan = w.plan()
    plan["records"]["sealed"] = record
    w.mac.save_plan(plan)
    assert _init_sim(w)["hosts"] == ["sim-1"]


def test_release_refuses_inputs_that_differ_from_the_planned_ones(w):
    """release_hosts re-derives similarity_entry and refuses a job whose entry differs (here the S1 path); with the
    entry derived now it releases."""
    _arms_done(w)
    plan = w.tool.load()
    h = w.tool.build_block(plan, "sim", {"launches": SIM})["launches"][0]["hosts"][0]
    h["jobs"][0]["similarity"]["add_sets"]["S1"]["path"] = "tmp/sealed/elsewhere.edit.json"
    with pytest.raises(SystemExit, match=r"sim-1: B14's inputs \(similarity_entry\) differ from the ones planned at "
                                         r"init-block"):
        w.tool.release_hosts(plan, "sim", [("sim-1", h)])
    h["jobs"][0]["similarity"] = w.tool.similarity_entry(plan)
    assert w.tool.release_hosts(plan, "sim", [("sim-1", h)]) == ["sim-1"]


def _sim_done(w, host: str, status: str = "complete") -> dict:
    """HOST's pulled tree as the runner leaves it for one similarity job (complete: similarity.json on the pins and
    the runner's record by stage1_rules.similarity_record_doc), then record-done by the kit's own function."""
    r = w.rules
    tree = w.root / "retrieved" / host / "tree"
    rec = {"index": 0, "kind": "similarity", "arm": None, "seed": None, "status": status, "engine": "X",
           "engine_sha256": rk.X, "job_id": "J22"}
    if status == "complete":
        recipe = w.plan()["recipes"][r.REC]["config_sha256"]
        doc = _good_doc(r, recipe)
        digest = sha(write_json(tree / OUT, doc))
        (tree / RECORD).write_bytes(r.canonical_bytes(r.similarity_record_doc(doc, host, 0, digest, digest, recipe)))
        rec["outputs"] = {OUT: digest, RECORD: sha(tree / RECORD)}
    write_json(tree / "JOB-DONE.json", {"host": host, "jobs": [rec]})
    return w.tool.record_done(host)


def test_a_crashed_pass_is_re_run_once_from_block_sims_contingency_and_the_block_completes(w):
    """The kit's re-run rule on block sim: record-done of a crashed pass; defer moves it to sim-2 (the same inputs),
    paid from the contingency on a new pod ($1.5513 of $2.20); record-done of sim-2 prints the output's path and
    SHA-256 for the strata step; the block is then complete (no judge, no seal needed)."""
    _arms_done(w)
    _init_sim(w)
    assert _sim_done(w, "sim-1", status="crashed") == {"host": "sim-1", "statuses": ["crashed"]}
    assert w.tool.block_complete(w.plan(), "sim") is False
    moved = w.tool.defer("sim-1")
    assert (moved["to"], moved["jobs"], moved["cap_hours"]) == ("sim-2", 1, 1.5)
    plan = w.plan()
    c = plan["contingency"]["sim"]
    spend = (600 + 2520) / 3600 * 1.79
    assert [s["cost_usd"] for s in c["spent"]] == [pytest.approx(spend)] and c["remaining_usd"] == pytest.approx(
        2.2 - spend)
    assert plan["hosts"]["sim-2"]["jobs"][0]["similarity"] == plan["hosts"]["sim-1"]["jobs"][0]["similarity"]
    assert plan["hosts"]["sim-2"]["jobs"][0]["deferred_from"] == "sim-1"
    out = _sim_done(w, "sim-2")
    tree = w.root / "retrieved" / "sim-2" / "tree"
    assert out == {"host": "sim-2", "statuses": ["complete"], "similarity": [
        {"job": 0, "path": f"runkit/stage1-olmo/retrieved/sim-2/tree/{OUT}", "sha256": sha(tree / OUT),
         "record_sha256": sha(tree / RECORD)}]}
    assert w.tool.block_complete(w.plan(), "sim") is True


# ===== the runner (a synthetic pod) =================================================================================

def sim_pod(kit, tmp_path, monkeypatch, jobs=None, **options):
    return Pod(kit, tmp_path, monkeypatch, jobs or (lambda r: [job(r, "similarity", recipe="B")]), **options)


def test_the_runner_runs_b14_on_the_pins_and_returns_the_output_and_its_record(kit, tmp_path, monkeypatch, capsys):
    """One step, job-0-similarity, by hand: B14's script with the prepared set, REC and the three add sets as edits/
    <SHA-256>.edit.json with their SHA-256 (S1, S3, S4), out job-0/similarity. The job is complete with no unit; its
    outputs are similarity.json, the engine's ledger, the record and the cost ledger, each at its SHA-256; the record is
    the canonical record by hand (the printed SHA-256 equals the file's; no problem); the ledger puts the step under
    scoring with job id J22. No SENTINEL is in JOB-DONE.json, the record or anything printed."""
    pod = sim_pod(kit, tmp_path, monkeypatch)
    r, sets = pod.rules, pod.sim_sets
    pod.remaining([30 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete"] and pod.receipts() == ["job-0-similarity"]
    [argv] = [a[5:] for a in pod.ran if a[:2] == ["python3", "process_receipt.py"]]
    assert argv == ["venv/bin/python", "scripts/stage1_s1/overlap_similarity.py", "--prepared", P, "--recipe", REC,
                    "--add-set", "S1", f"edits/{sets['S1']}.edit.json", sets["S1"],
                    "--add-set", "S3", f"edits/{sets['S3']}.edit.json", sets["S3"],
                    "--add-set", "S4", f"edits/{sets['S4']}.edit.json", sets["S4"], "--out", "job-0/similarity"]
    rec = pod.done()["jobs"][0]
    assert (rec["unit"], rec["complete_sha256"], rec["job_id"], rec["verified"]) == (None, None, "J22", None)
    assert set(rec["outputs"]) == {OUT, "job-0/similarity/ledger.jsonl", RECORD, LEDGER}
    assert all(rec["outputs"][rel] == sha(pod.root / rel) for rel in rec["outputs"])
    digest = sha(pod.root / OUT)
    want = {"kind": "stage1 similarity record", "version": 1, "host": "h-1", "job": 0,
            "output": {"path": OUT, "sha256": digest}, "printed_sha256": digest,
            "script_sha256": r.S1_CODE[r.SIM_SCRIPT], "settings_sha256": r.S1_CODE[r.SIM_SETTINGS],
            "inputs": {"add/S1": sets["S1"], "add/S3": sets["S3"], "add/S4": sets["S4"],
                       "prepared/banks/dev.jsonl": sha(pod.root / P / "banks" / "dev.jsonl"),
                       "prepared/manifest.json": sha(pod.root / P / "manifest.json"), "recipe": "c" * 64},
            "counts": {"prompts": 200, "rows": {"S1": 48, "S3": 48, "S4": 48}}, "problems": []}
    data = (pod.root / RECORD).read_bytes()
    assert json.loads(data) == want and data == (json.dumps(want, sort_keys=True, indent=2) + "\n").encode()
    ledger = json.loads((pod.root / LEDGER).read_text())
    assert ledger["job_id"] == "J22" and [s["name"] for s in ledger["steps"]] == ["job-0-similarity"]
    assert ledger["stages_s"]["scoring"] == ledger["steps"][0]["seconds"]
    printed = capsys.readouterr().out
    for text in (json.dumps(pod.done()), data.decode(), printed):
        assert not any(s in text for s in SENTINELS)


def _edit(r) -> dict:
    return rn.sim_entry(r)


@pytest.mark.parametrize("change, match", [
    (lambda e: {}, "plan.json carries no B14 inputs for this job"),
    (lambda e: {**e, "add_sets": {**{k: v for k, v in e["add_sets"].items() if k != "S1"},
                                  "S2": e["add_sets"]["S1"]}}, "plan.json carries no B14 inputs for this job"),
    (lambda e: {**e, "script": {**e["script"], "path": "scripts/stage1_s1/overlap_strata.py"}},
     "plan.json carries no B14 inputs for this job"),
    (lambda e: {**e, "manifest_sha256": "not a sha"}, "plan.json carries no B14 inputs for this job"),
    (lambda e: {**e, "dev_bank": {**e["dev_bank"], "sha256": "1" * 64}},
     r"1 input\(s\) not packed at the plan's pins \(pack engine X after kit round 34\): "
     r"\['data/kt-prepared/prepared-kt-dolly-olmo2/banks/dev\.jsonl'\]"),
    (lambda e: {**e, "settings": {**e["settings"], "sha256": "2" * 64}},
     r"not packed at the plan's pins .*\['scripts/stage1_s1/settings/overlap_similarity\.json'\]"),
    (lambda e: {**e, "manifest_sha256": "3" * 64},
     r"not packed at the plan's pins .*\['data/kt-prepared/prepared-kt-dolly-olmo2/manifest\.json'\]")])
def test_the_runner_never_starts_b14_without_its_pins(kit, tmp_path, monkeypatch, change, match):
    """Before any step (no receipt; the job crashed, named): plan.json's entry missing, naming another add set, the
    script at another path, a manifest pin that is no SHA-256; a pin that the packed file at its fixed path does not
    have (the dev bank, the settings, the manifest: a pack older than the plan)."""
    pod = sim_pod(kit, tmp_path, monkeypatch, jobs=lambda r: [{**job(r, "similarity", recipe="B"),
                                                               "similarity": change(_edit(r))}])
    pod.remaining([30 * H])
    assert pod.main() == 1 and pod.statuses() == ["crashed"] and pod.receipts() == []
    assert re.search(match, pod.done()["jobs"][0]["why"]), pod.done()["jobs"][0]["why"]
    assert not (pod.root / RECORD).exists()


def test_an_add_set_the_pack_lacks_stops_the_host_and_fails_check_plans_runner_check(kit, tmp_path, monkeypatch):
    """An add set whose plan.json pin no packed file has (edits/<SHA-256>.edit.json is named by its SHA-256): on the
    pod the sealed-file check lists it first and stops the host (not_started, no receipt); the runner's own check names
    it too (as check-plan reports it on the Mac)."""
    def jobs(r):
        e = _edit(r)
        e["add_sets"]["S3"] = {**e["add_sets"]["S3"], "sha256": "0" * 64}
        return [{**job(r, "similarity", recipe="B"), "similarity": e}]
    pod = sim_pod(kit, tmp_path, monkeypatch, jobs=jobs)
    with pytest.raises(pod.runner.Unrunnable, match=r"1 input\(s\) not packed at the plan's pins .*"
                                                     r"\['edits/0{64}\.edit\.json'\]"):
        pod.runner.job_commands(pod.plan, "h-1", 0, pod.root, {})
    pod.remaining([30 * H])
    assert pod.main() == 1 and pod.statuses() == ["not_started"] and pod.receipts() == []
    assert pod.done()["stopped"] == "sealed_file_mismatch"
    assert pod.done()["jobs"][0]["sealed_mismatch"] == [f"edits/{'0' * 64}.edit.json"]


@pytest.mark.parametrize("which", ["S3", "dev bank", "manifest", "script", "settings"])
def test_a_changed_byte_in_any_file_the_pass_reads_stops_the_host_before_it(kit, tmp_path, monkeypatch, which):
    """sealed_paths lists B14's script and settings (and the W1 modules and registry they load), the prepared manifest,
    the dev bank and the three add-set files, so a byte changed after sealing stops the host at the job
    (sealed_file_mismatch, not_started) before the pass runs (the mid-host check alone, as for every other kind)."""
    text = "add set S3 (synthetic edit file)\n"                       # the Pod's S3 edit file, by hand
    pod = sim_pod(kit, tmp_path, monkeypatch)
    rel = {"S3": f"edits/{hashlib.sha256(text.encode()).hexdigest()}.edit.json", "dev bank": f"{P}/banks/dev.jsonl",
           "manifest": f"{P}/manifest.json", "script": "scripts/stage1_s1/overlap_similarity.py",
           "settings": "scripts/stage1_s1/settings/overlap_similarity.json"}[which]
    h = pod.plan["hosts"]["h-1"]
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    assert pod.runner.sealed_paths(h["jobs"][0], h, 0, doc) == [
        "scripts/stage1_s1/overlap_similarity.py", "scripts/stage1_s1/settings/overlap_similarity.json",
        "scripts/stage1/s1common.py", "scripts/stage1/limits/limits_common.py", "scripts/stage1/labels.json",
        f"{P}/manifest.json", f"{P}/banks/dev.jsonl", *[f"edits/{pod.sim_sets[n]}.edit.json" for n in ("S1", "S3", "S4")]]
    assert pod.runner.sealed_check(h["jobs"][0], doc["files"], pod.root, h, 0, doc) == []
    write(pod.root / rel, "changed after sealing\n")
    assert pod.runner.sealed_check(h["jobs"][0], doc["files"], pod.root, h, 0, doc) == [rel]
    monkeypatch.setattr(pod.runner, "preflight_checks", lambda *a: doc)       # the mid-host check, alone
    pod.remaining([30 * H])
    assert pod.main() == 1 and pod.statuses() == ["not_started"] and pod.receipts() == []
    assert pod.done()["stopped"] == "sealed_file_mismatch" and pod.done()["jobs"][0]["sealed_mismatch"] == [rel]


@pytest.mark.parametrize("change, problem", [
    (_set("add_sets.S4.edit_sha256", "0" * 64), "add_sets.S4"),
    (_set(("provenance", "inputs", "add/S1"), "1" * 64), "provenance.inputs[add/S1]"),
    (_set("provenance.settings_sha256", "2" * 64), "provenance.settings_sha256"),
    (_set(("provenance", "inputs", "recipe"), "3" * 64), "provenance.inputs[recipe]"),
    (_set("eval.prompts", 199), "eval.prompts"),
    (_set("add_sets.S1.rows", 47), "add_sets.S1"),
    (_set("kind", "something else"), "not a version-1 'stage1 overlap similarity' record"),
    ("no printed line", "the SHA-256 the script printed is missing or not the file's")])
def test_an_output_off_the_pins_or_without_its_printed_sha256_is_a_crash_its_record_explains(kit, tmp_path,
                                                                                           monkeypatch, change, problem):
    """The pass exits 0 but its output is not on the kit's pins (or the script's printed SHA-256 is missing): the job
    is crashed with the problem named, no output is listed, and the record (written once) says why."""
    pod = sim_pod(kit, tmp_path, monkeypatch)
    if change == "no printed line":
        pod.sim_print = False
    else:
        pod.sim_change = change
    pod.remaining([30 * H])
    assert pod.main() == 1 and pod.statuses() == ["crashed"] and pod.receipts() == ["job-0-similarity"]
    rec = pod.done()["jobs"][0]
    assert rec["why"].startswith("the similarity output does not carry the kit's pins (") and problem in rec["why"]
    assert "outputs" not in rec and problem in json.loads((pod.root / RECORD).read_text())["problems"]


def test_a_record_that_exists_already_is_never_written_over(kit, tmp_path, monkeypatch):
    """Exclusive create: a job-0/similarity-record.json present before the pass makes the job a crash, and the file
    is left as it was."""
    pod = sim_pod(kit, tmp_path, monkeypatch)
    write(pod.root / RECORD, "an earlier record\n")
    pod.remaining([30 * H])
    assert pod.main() == 1 and pod.statuses() == ["crashed"]
    assert pod.done()["jobs"][0]["why"] == "the similarity record could not be written (FileExistsError)"
    assert (pod.root / RECORD).read_text() == "an earlier record\n"


# ===== check-plan on the packed stage ================================================================================

def _sim_check_plan(kit, round34: bool) -> dict:
    """orchestrate.py check-plan for a block-sim host whose plan.json entry is the kit's real pins, on a packed stage
    (sealed-files.json) that holds the prepared set's two files and the three add sets at those pins, and (round34)
    B14's script and settings at their S1_CODE pins (a round-33 pack has neither)."""
    o = kit("orchestrate.py")
    r = o.rules
    entry = {"script": {"path": r.SIM_SCRIPT, "sha256": r.S1_CODE[r.SIM_SCRIPT]},
             "settings": {"path": r.SIM_SETTINGS, "sha256": r.S1_CODE[r.SIM_SETTINGS]},
             "manifest_sha256": r.PREPARED_MANIFESTS[r.PREPARED_NAME], "dev_bank": dict(r.SIM_DEV_BANK),
             "add_sets": {n: {"path": f"tmp/x/{n}.edit.json", "sha256": d, "source": "test"}
                          for n, d in r.SIM_ADD_SETS.items()}}
    h = rn.host_record(r, [{**job(r, "similarity", recipe="B"), "similarity": entry}], "X", block="sim")
    packed = kit.root / "setup" / "packed-stage1-X"
    files = {rel: "a" * 64 for rels in o.runner.SCRIPTS.values() for rel in rels
             if rel not in (r.SIM_SCRIPT, r.SIM_SETTINGS)}
    files.update({f"{P}/manifest.json": entry["manifest_sha256"], f"{P}/banks/dev.jsonl": r.SIM_DEV_BANK["sha256"],
                  **{f"edits/{d}.edit.json": d for d in r.SIM_ADD_SETS.values()}})
    if round34:
        files.update({r.SIM_SCRIPT: r.S1_CODE[r.SIM_SCRIPT], r.SIM_SETTINGS: r.S1_CODE[r.SIM_SETTINGS]})
    sealed = write(packed / "sealed-files.json", {"files": files, "inputs": {}})
    write(packed / "setup-receipt.json", {"engine_sha256": r.ENGINES["X"], "sealed_files_sha256": sha(sealed)})
    h["sealed_files_sha256"] = sha(sealed)
    write(kit.root / "plan.json", {"hosts": {"sim-1": h}, "records": {"branch": None, "certification": None},
                                   "reference": {"fields": {"f": 1}, "bootstrap": {}, "guard": None}})
    return o.check_plan("sim-1") if round34 else o


def test_check_plan_passes_only_on_a_pack_made_after_this_round(kit):
    """$0 on the Mac: a round-33 X pack (no B14 script or settings) cannot run the host (both the runner's own check
    and the missing sealed files are named); a round-34 pack, the real pins throughout, passes."""
    o = _sim_check_plan(kit, round34=False)
    with pytest.raises(SystemExit) as caught:
        o.check_plan("sim-1")
    text = str(caught.value)
    assert "sim-1: the plan cannot run on its packed stage" in text and "not packed at the plan's pins" in text
    assert "job 0 (similarity): 2 file(s) not packed: ['scripts/stage1_s1/overlap_similarity.py', " \
           "'scripts/stage1_s1/settings/overlap_similarity.json']" in text
    shutil.rmtree(kit.root / "setup" / "packed-stage1-X")
    assert _sim_check_plan(kit, round34=True) == {"host": "sim-1", "jobs": 1, "ok": True}


# ===== the finisher's light check and record-done ===================================================================

def _pulled(kit, tmp_path, monkeypatch):
    """A synthetic sim pod run to completion, its run folder as the light pull unpacks it into the kit's
    retrieved/h-1/tree, and plan.json naming h-1 (block sim) with the pod's job and recipes. Returns (pod, tree)."""
    pod = sim_pod(kit, tmp_path, monkeypatch)
    pod.remaining([30 * H])
    assert pod.main() == 0
    tree = kit.root / "retrieved" / "h-1" / "tree"
    tree.mkdir(parents=True)
    for rel in ("job-0", "job-0-similarity", "job-done"):
        shutil.copytree(pod.root / rel, tree / rel)
    shutil.copy2(pod.root / "JOB-DONE.json", tree / "JOB-DONE.json")
    h = {**pod.plan["hosts"]["h-1"], "block": "sim", "wave": "sim"}
    write(kit.root / "plan.json", {"hosts": {"h-1": h}, "recipes": pod.plan["recipes"], "deferrals": [],
                                   "requeues": [], "records": {}})
    (kit.root / "hosts" / "h-1").mkdir(parents=True)
    return pod, tree


def test_record_done_and_the_light_check_take_the_pulled_output_by_its_record(kit, tmp_path, monkeypatch):
    """Both ways. Good: the light check's entry for job-0/similarity is exit 0, the finisher's status
    verified-and-stopped, and record-done prints the output's path (from the repository root) and SHA-256 and the
    record's. Then, one at a time (each restored): similarity.json changed after the pod; the record rewritten (and
    listed at its new SHA-256 in JOB-DONE.json) with a problem it does not explain; a record whose printed SHA-256 is
    not the file's (its own problem listed); the record not among the outputs; similarity.json a symbolic link; another
    REC config SHA-256 in plan.json. Each is review-needed-stopped and record-done refuses (nothing recorded)."""
    pod, tree = _pulled(kit, tmp_path, monkeypatch)
    fin, tool = kit("finisher.py"), kit("plan_tool.py")
    r = tool.rules
    assert fin.similarity_check("h-1", tree) == {"job-0/similarity": {
        "exit": 0, "tail": "similarity.json and its record agree with each other and the kit's pins"}}
    assert rn._finish(fin, kit, monkeypatch, tree)[0] == "verified-and-stopped"
    done_path, plan_path = tree / "JOB-DONE.json", kit.root / "plan.json"
    keep = {p: p.read_bytes() for p in (tree / OUT, tree / RECORD, done_path, plan_path)}

    def restore():
        for p, data in keep.items():
            if p.is_symlink():
                p.unlink()
            p.write_bytes(data)
        (tree / "job-0" / "similarity" / "kept.json").unlink(missing_ok=True)

    def relisted(rel: str) -> None:
        doc = json.loads(done_path.read_text())
        doc["jobs"][0]["outputs"][rel] = sha(tree / rel)
        done_path.write_text(json.dumps(doc, indent=2) + "\n")

    def record(**change) -> None:
        rec = {**json.loads((tree / RECORD).read_text()), **change}
        (tree / RECORD).write_bytes(r.canonical_bytes(rec))
        relisted(RECORD)

    def plan_recipe() -> None:
        plan = json.loads(plan_path.read_text())
        plan["recipes"][REC]["config_sha256"] = "d" * 64
        plan_path.write_text(json.dumps(plan))

    def link() -> None:
        moved = tree / "job-0" / "similarity" / "kept.json"
        (tree / OUT).rename(moved)
        (tree / OUT).symlink_to(moved)

    def unlisted() -> None:
        doc = json.loads(done_path.read_text())
        del doc["jobs"][0]["outputs"][RECORD]
        done_path.write_text(json.dumps(doc, indent=2) + "\n")

    not_listed = "{} is not among the job's outputs, or not a regular file in the pulled tree at its recorded SHA-256"
    other_record = f"{RECORD} is not the record of the pulled similarity.json (fields ['problems'])"
    cases = [(lambda: (tree / OUT).write_bytes(keep[tree / OUT] + b" "), not_listed.format(OUT),
              "h-1: job 0's output is missing from the pulled tree or differs"),     # record-done's own output check
             (lambda: record(problems=["something"]), other_record, None),
             (lambda: record(printed_sha256="0" * 64, problems=[
                 "the SHA-256 the script printed is missing or not the file's"]),
              "the pulled similarity.json does not carry the kit's pins (the SHA-256 the script printed is missing or "
              "not the file's)", None),
             (unlisted, not_listed.format(RECORD), None),
             (link, not_listed.format(OUT), None),
             (plan_recipe, other_record, None)]
    for make, tail, done_message in cases:
        make()
        check = fin.similarity_check("h-1", tree)["job-0/similarity"]
        assert check == {"exit": 1, "tail": tail}, (tail, check)
        assert rn._finish(fin, kit, monkeypatch, tree)[0] == "review-needed-stopped"
        with pytest.raises(SystemExit) as refused:
            tool.record_done("h-1")
        assert str(refused.value) == (done_message or f"h-1: job 0 (similarity): {tail}")
        assert json.loads(plan_path.read_text())["hosts"]["h-1"].get("done") is not True
        restore()
    out = tool.record_done("h-1")
    assert out == {"host": "h-1", "statuses": ["complete"], "similarity": [
        {"job": 0, "path": f"runkit/stage1-olmo/retrieved/h-1/tree/{OUT}", "sha256": sha(tree / OUT),
         "record_sha256": sha(tree / RECORD)}]}
    assert not any(s in json.dumps(out) + (kit.root / "plan.json").read_text() for s in SENTINELS)


def test_a_light_check_without_a_similarity_job_is_unchanged(kit, monkeypatch):
    """A tree whose JOB-DONE.json holds no similarity job (or none at all) gives the light check nothing new: the
    round-29 role test's tree is verified exactly as before."""
    fin, tree, _ = rn._finisher_tree(kit, "job")
    assert fin.similarity_check("h-1", tree) == {}
    (tree / "JOB-DONE.json").unlink()
    assert fin.similarity_check("h-1", tree) == {}


def test_the_round_34_files_compile_and_hold_no_secret(tmp_path):
    """The round's changed kit files compile and hold no secret pattern (the kit's own scanner)."""
    import py_compile
    names = ("stage1_rules.py", "plan_tool.py", "finisher.py", "setup/job_runner_stage1.py", "tests/test_round34.py")
    for rel in names:
        py_compile.compile(str(KIT / rel), cfile=str(tmp_path / "x.pyc"), doraise=True)
    spec = importlib.util.spec_from_file_location("s1_scan_round34", KIT / "secret_scan.py")
    scan = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scan)
    assert scan.scan_paths([KIT / rel for rel in (*names, "README.md")]) == []
    assert "s1_scan_round34" not in sys.modules
