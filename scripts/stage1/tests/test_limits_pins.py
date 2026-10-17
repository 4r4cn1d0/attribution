"""Part F: the literal settings pins, and the committed settings' contents against their recorded sources."""

from __future__ import annotations

import json
import re

import pytest

from experiments.safety_selection.common import canonical_json, code_identity, sha256_bytes, sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1.limits import limits_check as lcheck
from scripts.stage1.limits import limits_common as lc
from scripts.stage1.limits import overrefusal_checks as orc
from scripts.stage1.limits import untuned_refusal_strata as strata

MODULES = {"limits_check": lcheck, "limits_untuned_strata": strata, "limits_overrefusal_checks": orc}

# The lead's written reading of PLAN-S:197's f (FOCUS, 2026-10-17T02:42 UTC entry), exactly.
F_READING = ("f is the fraction of the dev over-refusal bank used for the planning SE; f = 1 means all 100 dev "
             "over-refusal prompts, each with its greedy answer, with seeds as replicates.")

# The Gate A allow-list (R: research/experiments/2026-10-17-stage1-prereg-references/tau_l_check.out.json, draft A
# section L.4; job.json: scripts/gate_b_reading.py GATE_A_PINS).
GATE_A = {
    "untuned": ("family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1",
                "b5083ce9d9f26efe92f9872fdbf9376a521a5d99d1b70cc2bd460987cdcc9474",
                "f3b8c1864aaacf34738b34ff6c26cc8f51677e7eb5a6a9445818692d5365a582",
                "7b40ea1c99bbfffdbc1711008f4fd10ba83cb5bca782c473fb6c16ee20f80801",
                "02963ba5559077dfae9dd48a29ac5470507d05d48377966195545a8d979d27a6"),
    "1101": ("family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1",
             "8f0fa83a42ccc5edc54a5ee26ed63f49448c36d30adbd64e28b655678afee4c9",
             "3e60568ac11e32f3f429aa2606bc38c9b881456fd262a120e526ccb189022402",
             "f331eadee052f8f1c45403b7f19b7da7f1cfa1153d2b450285d3e777ca11171a",
             "a539638fc5c7f5b98594094690b114fb5714343e4f497451301cce9630a189d1"),
    "1102": ("family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1",
             "857f78bc0f49cc8a4902fbb6211f463daa7c7f44086257c4d752409a30ba0b25",
             "de65ca1936a10c199de46e764a948268b03367c586c09747381850059064083c",
             "0918dc486803a0d3357d43e3fca323b9a29c6ae1379741486b03aa7bd36294f0",
             "2f73f77c40b161572572d8d18b317d21c26738bf2aed1e337b4ed7b7645f3e20"),
    "1103": ("family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1",
             "7be58eaa9c5be7b8f94668109efd6aae075b1d001e0d2b1fb8be814556899cbd",
             "895f8bd2a66e20df2256b43d1e71a263da237a1cb3ea498cd439086aef5ae293",
             "7d24950cb2ad221dfcd0e27c0c40cc6745c52dcaac4612a966474310d85cf918",
             "eba947241293ed571f7bb5ce507b59af98911cd411be323f9a8c901a1ae79612")}
KNOWN = {"s": 0.002374850619448416, "tau_l": 0.0067170919092681925, "se_one_difference": 0.0033585459546340963,
         "se_6v6": 0.0013711206444236926}
# The 11 recorded OLMo-2-1B units (R: research/experiments/2026-10-17-stage1-review-b-rulings/or_labels_check.py).
DEV_PATHS = {
    "untuned": "family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1",
    "B-1101": "family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1",
    "B-1102": "family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1",
    "B-1103": "family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1",
    "G-1101": "family-probe-olmo2-1b-g/retrieved/olmo2-1b-g-1101/tree/round1/1101-a0-e1-a1",
    "G-1102": "family-probe-olmo2-1b-g-seed1102/retrieved/olmo2-1b-g-1102/tree/round1/1102-a0-e1-a1",
    "G-1103": "family-probe-olmo2-1b-g-seed1103/retrieved/olmo2-1b-g-1103/tree/round1/1103-a0-e1-a1",
    "bt-1101": "family-probe-olmo2-1b-bt/retrieved/olmo2-1b-bt-1101/tree/round1/1101-a0-e1-a1",
    "bt-1102": "family-probe-sp-olmo2-1b-bt-seed1102/retrieved/sp-olmo2-1b-bt-1102/tree/round1/1102-a0-e1-a1",
    "bt-1103": ("gi-v-steps-4-9/step4-backups/stage/side-kits/family-probe-sp-olmo2-1b-bt-seed1103/retrieved/"
                "sp-olmo2-1b-bt-1103/tree/round1/1103-a0-e1-a1"),
    "G16-1101": "family-probe-olmo2-1b-g-r16/retrieved/olmo2-1b-g-r16-1101/tree/round1/1101-a0-e1-a1"}
# The seven development units' (COMPLETE.json, job.json) SHA-256, observed in the main checkout's tmp/ on 2026-10-17 by
# the Part F verifier (03:57-04:03 UTC) and by the Part F fixer (04:17 UTC), equal both times (verification item S-13).
DEV_PINS = {
    "G-1101": ("557a083f0dad77bc50dd749e805be076eaa75eb1ea50b8ce356736a6207f8a09",
               "1a292c1d71729a3a5cca33ec1a452be634e07a6cb77b7efc856fb38b7b2a56dd"),
    "G-1102": ("7c16beec76971793c9ffb51c5832f645e0dbe70e74b1954fe48556273d9d3157",
               "97b7c5ec736c97dd04a4f23fff99bdfc9465733bc3a1929479eaf31748e9fd04"),
    "G-1103": ("6db69ca4fc5e9b902eba3ea194cb2b7e180e3f2d26fed330ffc185cfa55c71fc",
               "2573e30472fbb574ec8965d9f43fa5dd335f60d5fbf53f03aedf0a9c24374111"),
    "G16-1101": ("425922e550bf51fbd6ea67b58191ee6d7f5f75e5d64f4087794293bcc632d02a",
                 "2e05692c7355920951f22e5f2d5a451abfeb7b8c913a0cbfb88780fe1c25c9f5"),
    "bt-1101": ("0ccf97de823c24990d0f78023beb58819fba5cb4e6afb2560ceac71715067fef",
                "5b57d4c593c69dd755d7a79cf8a88f349f8043ac02777eb5afc51e2db2720a9f"),
    "bt-1102": ("5d292d7d93da3a556865a51f5d5cd46c845bbe224c24854b5ea988b0f77f6e9c",
                "79515087fb03ea97ca8e677ffd6132c68d2c93c0669a78f05eb5f2b63651694d"),
    "bt-1103": ("de3e8f798a89e31060129bff8ea1687864e45d41f4228092c106975c110668e4",
                "a9350596046884d315df7ca8941b7152e238277ba29e053b09a850939a1adb4c")}
SIM_OUT = "research/experiments/2026-10-17-stage1-preregistration/review_stats_sim_out.txt"
LABEL_LITERAL = re.compile(rb"\bstage1-[a-z0-9]+(?:-[a-z0-9]+)*-v[1-9][0-9]*\b")


def settings(name: str) -> dict:
    return json.loads(MODULES[name].SETTINGS_PATH.read_bytes())


@pytest.mark.parametrize("name", sorted(MODULES))
def test_each_settings_file_loads_with_its_literal_pin(name):
    module = MODULES[name]
    assert module.SETTINGS_NAME == name and module.SETTINGS_PATH == s1.HERE / "settings" / f"{name}.json"
    assert sha256_file(module.SETTINGS_PATH) == module.SETTINGS_SHA256
    doc, digest = s1.load_settings(module.SETTINGS_PATH, module.SETTINGS_SHA256, name)
    assert digest == module.SETTINGS_SHA256 and doc["label_entries"] == {} and doc["engine_x"] == code_identity()["sha256"]
    module.check_content(doc)


def test_the_limits_settings_hold_the_rules_in_force():
    doc = settings("limits_check")
    assert doc["f"] == {"value": 1, "reading": F_READING, "source": doc["f"]["source"]}
    assert doc["u8_decider"] == "prompts_random" and doc["o_ext_threshold_pp"] == 5.0
    assert doc["mde"]["alpha"] == 0.05 and doc["mde"]["sides"] == 2 and doc["mde"]["power"] == 0.8
    assert doc["mde"]["seeds"] == {"plan_a": 6, "plan_b": 9}
    assert doc["ni_report"]["screen_upper_quantile"] == 0.95 and doc["ni_report"]["tau_o_pp"] == [2, 5, 10]
    assert doc["ni_report"]["prompts"] == [100, 500] and doc["ni_report"]["power"] == 0.8
    assert doc["o"]["bank_kind"] == "overrefusal" and doc["o"]["bank_size"] == 100
    assert doc["tau_l"]["ddof"] == 1 and doc["tau_l"]["rows"] == 200
    assert {k: doc["tau_l"]["known_answer"][k] for k in KNOWN} == KNOWN
    assert lcheck.tau_l_numbers_from_s(KNOWN["s"]) == {k: KNOWN[k] for k in ("tau_l", "se_one_difference", "se_6v6")}
    assert doc["allow_list"]["refused_recipes"] == ["ceffe0efb5d75bacfbd62743f530259deeedeca8950605d1bd3ff66e5391fe46"]


def test_the_allow_list_is_the_recorded_gate_a_table():
    doc = settings("limits_check")
    for name, (path, complete, job, summary, loss) in GATE_A.items():
        spec = doc["units"][name]
        assert (spec["path"], spec["complete_sha256"], spec["job_sha256"], spec["summary_sha256"],
                spec["query_loss_sha256"]) == (path, complete, job, summary, loss)
    reference = lc.ENGINE_ROOT / "research/experiments/2026-10-17-stage1-prereg-references/tau_l_check.out.json"
    ref = json.loads(reference.read_bytes())
    assert {k: ref[k] for k in ("s_ddof1", "tau_L", "se_6_vs_6", "se_one_seed_difference")} == {
        "s_ddof1": KNOWN["s"], "tau_L": KNOWN["tau_l"], "se_6_vs_6": KNOWN["se_6v6"],
        "se_one_seed_difference": KNOWN["se_one_difference"]}
    for name, unit in ref["units"].items():
        spec = doc["units"][name]
        assert unit["path"].endswith("/tmp/" + spec["path"]) and unit["checkpoint"] == spec["checkpoint"]
        assert unit["sha256"] == {"COMPLETE.json": spec["complete_sha256"], "query_loss.jsonl": spec["query_loss_sha256"],
                                  "summary.json": spec["summary_sha256"]}
        assert unit["query_bank_sha256"] == doc["query_bank_sha256"] and unit["recipe_sha256"] == doc["gate_a_identity"]["recipe_sha256"]
        assert unit["code_sha256"] == doc["gate_a_identity"]["code_sha256"]


def test_the_frozen_reader_and_the_lexicon_pins_hold_here():
    for name in MODULES:
        doc = settings(name)
        for entry in doc["frozen_reader"].values():
            assert sha256_file(lc.ENGINE_ROOT / entry["path"]) == entry["sha256"]
    lexicon = settings("limits_untuned_strata")["lexicon"]
    assert lexicon == settings("limits_overrefusal_checks")["lexicon"]
    assert (lexicon["json_sha256"], lexicon["classifier_sha256"]) == (
        "bbbc71e9eebb62876430ffb5e0f54113c3818984b8369924b7bd2212c4c1ca17",
        "5a27dd040b74aa23fe09ac4dc95fb5913a4ccd327a67bb3caf5e667ff0432d1b")
    assert lexicon["candidates"][-1] == {"json": "tmp/mechanism-recipes/lexicon.json",
                                         "classifier": "tmp/mechanism-recipes/lexicon.py"}
    assert lc.load_lexicon(lexicon).classes == ("CAVEAT-OPENING", "DIRECT", "EMPTY", "REFUSAL-OPENING")


def test_the_strata_and_checks_settings_reuse_the_gate_a_pins():
    gate_a = settings("limits_check")["units"]
    assert settings("limits_untuned_strata")["unit"] == gate_a["untuned"]
    doc = settings("limits_overrefusal_checks")
    assert {n: u["path"] for n, u in doc["units"].items()} == DEV_PATHS
    for name, gate in (("untuned", "untuned"), ("B-1101", "1101"), ("B-1102", "1102"), ("B-1103", "1103")):
        assert (doc["units"][name]["complete_sha256"], doc["units"][name]["job_sha256"]) == (
            gate_a[gate]["complete_sha256"], gate_a[gate]["job_sha256"])
    assert {n: (doc["units"][n]["complete_sha256"], doc["units"][n]["job_sha256"]) for n in DEV_PINS} == DEV_PINS
    recipe = lc.ENGINE_ROOT / doc["judge"]["recipe"]
    assert sha256_file(recipe) == doc["judge"]["recipe_file_sha256"]
    guard = json.loads(recipe.read_bytes())["guard"]
    assert (guard["repo_id"], guard["revision"]) == (doc["judge"]["repo_id"], doc["judge"]["revision"])
    assert doc["truncation"]["cap_tokens"] == 128 and doc["truncation"]["min_flags_agree"] == 97
    assert doc["truncation"]["max_count_move"] == 2 and doc["prepared"]["manifest_sha256"].startswith("9ed61826")
    data_config = json.loads((lc.ENGINE_ROOT / "experiments/safety_selection/configs/study-kt-data-dolly-olmo2.json").read_bytes())
    extraction = doc["source_map"]["extraction"]
    assert extraction["bank_source_manifest_sha256"] == data_config["banks_from"]["manifest_sha256"]
    assert (extraction["file"], extraction["map_key"], extraction["field"]) == ("auditor/construction.json", "prompts", "source")
    # S-3: no map is pinned until the lead's ruling; the checks never parse an auditor file
    assert doc["source_map"]["mode"] == "sealed_map"
    assert (doc["source_map"]["sealed_map"]["path"], doc["source_map"]["sealed_map"]["sha256"]) == (None, None)


def test_the_settings_files_are_canonical_and_text_free():
    for name in MODULES:
        data = MODULES[name].SETTINGS_PATH.read_bytes()
        assert sha256_bytes(data) == MODULES[name].SETTINGS_SHA256 and data == canonical_json(json.loads(data))
        assert not LABEL_LITERAL.search(data)                         # no label string (keys only; none is used)


def test_the_tau_l_scope_and_the_recorded_simulation():
    """N-3: the scope sentence keeps L16's words and points to REQ-16's SE-form setting (W1-13 row 3). N-2: the
    simulated failure rates in the settings are the numbers of the recorded simulation's section E."""
    tau = settings("limits_check")["tau_l"]
    assert tau["scope"].startswith("only the threshold tau_L is frozen; the SE inside REQ-16's upper-90% L screen is "
                                   "still estimated") and "W1-13 row 3" in tau["scope"] and "pooled residuals" in tau["scope"]
    sim = tau["two_df_simulated"]
    assert sim["source"].startswith(SIM_OUT + " section E")
    text = (lc.ENGINE_ROOT / SIM_OUT).read_text()
    section = text.split("== E. ", 1)[1].split("\n== ", 1)[0]
    two, one = section.split("one-sided 90% bound", 1)
    for part, rates in ((two, sim["r1_2_bound_two_sided_90_upper"]), (one, sim["one_sided_90_bound"])):
        assert f"unconditional fail {rates['unconditional']}%" in part
        assert f"given s < 0.5 sigma {rates['given_s_below_half_sigma']}%" in part
        assert f"at s = 0.5 sigma exactly: fail {rates['at_s_half_sigma']}%" in part
    assert sim["r1_2_bound_two_sided_90_upper"] == {"at_s_half_sigma": 22.2, "given_s_below_half_sigma": 52.3,
                                                    "unconditional": 13.8}
    assert sim["one_sided_90_bound"] == {"at_s_half_sigma": 12.6, "given_s_below_half_sigma": 39.6, "unconditional": 9.8}
