"""T5: the noise reader reproduces Gate B's wave-0a values on its inputs (σ̂_gate 1.83, the a0-free fallback 2.16,
σ_eval,0 1.28; P78:345), keys every input by complete_sha256 and family, refuses a 1B unit's record in a 7-8B family,
a method arm as an R unit, a wrong key and a wrong seed set, applies the seed rule exactly on the pair scale with the
thresholds 4.5 / 6.0 and the review ceiling, reproduces rows of CALC rule_oc2_out.txt, and prints no U.

Fix round (5 Nov 2026): σ̂_pool, the pooled six-SE median and s_arm are pinned on exact synthetic inputs and on wave 0a
(C-D1); the review ceiling is one constant with the printed MDE, tested at the exact boundary (C-D2); the duplicate-unit
check is reached (C-D4); the fresh-R and the parity-with-tier refusals are tested (C-D5); one family's fallback puts
its R-R pair terms beside the other family's seed-matched terms in the pooled median (addendum A6); the rebuilt Llama
sealed set's R files pass the reader's edit-provenance check (track B).

The parity tests read the Gate B wave-0a units and the Gate A a0 units on this Mac through the frozen reader functions
only (counts and aggregates; no text). They are skipped, with the reason, where those folders are absent. Run with the
repository's .venv (scipy for the constants' check) or the engine environment (every other test)."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from scripts.scale78b import noise_reading as nr

ROOT = Path(__file__).resolve().parents[3]
MAIN = Path("/Users/spiderishi/Coding/attribution")
GATE_A = MAIN / "tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1"
GATE_A_1102 = MAIN / "tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1"
GATE_A_1103 = MAIN / "tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1"
W0A = MAIN / "tmp/gate-b-olmo/retrieved/w0a-1/tree/round1"
W1 = MAIN / "tmp/gate-b-olmo/retrieved/w1-1/tree/round1"
R_ARMS = {1101: "f7d7eb86cb58f7a5e7e1408973a13531f74845e066d7328d6e726ecdd442ffdd",
          1102: "913b73606ff64c104751e3f86bd3b69838a27686720a92858c08f4cf087d8060",
          1103: "cd8d3328c48957ed0a164a8775ca2695a3d77d51865fd32c2ee53aded939502b"}
# The keys: the Gate A pins (gate_b_reading.GATE_A_PINS) and the wave-0a noise-gate output's units (committed under
# research/experiments/2026-10-16-gate-b-wave0-outputs/noise-gate-wave0a.json, SHA-256 4b817f73…).
A0_KEYS = {1101: "8f0fa83a42ccc5edc54a5ee26ed63f49448c36d30adbd64e28b655678afee4c9",
           1102: "857f78bc0f49cc8a4902fbb6211f463daa7c7f44086257c4d752409a30ba0b25",
           1103: "7be58eaa9c5be7b8f94668109efd6aae075b1d001e0d2b1fb8be814556899cbd"}
R_KEYS = {1101: "391d067ca6569a04721b059da2bca2c7ee5d109de560362895198a0d40ac5f0f",
          1102: "1cef324df66f0b46a11ce4d5255da1c5c7287ebbe9d8bc5cae7132996afb12b6",
          1103: "d34e33f2e3b90b562a1b21da3fabc3e672842b7b2cbfe2eadae754601155692c"}
ENGINE_GATE_A = "552538748acec1a8ffd1ee976b9eb3c3fdfe9ca01b8148ee8810291409357441"
ENGINE_X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
NG = ROOT / "research/experiments/2026-10-16-gate-b-wave0-outputs/noise-gate-wave0a.json"
OC = ROOT / "research/review/2026-10-17-icml-78b-prep/calc/rule_oc2_out.txt"
SEAL = ROOT / ".ai/inputs/gate-b-sealed-20261008/out"
LLAMA_SEALED = ROOT / ".ai/inputs/scale-78b-sealed-llama3-20261105/out"             # track B's Llama sealed set
OLMO_DRAWS = ROOT / ".ai/inputs/scale-78b-r-draws-olmo2-20261105/out"               # track B's OLMo R_d11-R_d16
LLAMA_H1 = ROOT / ".ai/inputs/scale-78b-length-rules-llama3-20261105/out/edits/octile_0.json"


def wave0a_present() -> bool:
    return all(p.is_dir() for p in (GATE_A, GATE_A_1102, GATE_A_1103)) and W0A.is_dir()


needs_wave0a = pytest.mark.skipif(not wave0a_present(), reason="Gate B's wave-0a units and the Gate A units are not on this Mac")


def r_unit(seed: int) -> Path:
    return W0A / f"{seed}-edit-{R_ARMS[seed]}-e1-a1"


def parity_family(name: str = "olmo2-1b", fingerprint: str = "not run") -> dict:
    a0 = {1101: GATE_A, 1102: GATE_A_1102, 1103: GATE_A_1103}
    return {"engine": {"a0": ENGINE_GATE_A, "R": ENGINE_X},
            "a0": {str(s): {"path": str(a0[s]), "complete_sha256": A0_KEYS[s]} for s in (1101, 1102, 1103)},
            "R": {str(s): {"path": str(r_unit(s)), "complete_sha256": R_KEYS[s], "arm": f"edit-{R_ARMS[s]}"}
                  for s in (1101, 1102, 1103)},
            "fingerprint_check": fingerprint}


def write_inputs(tmp_path: Path, families: dict, name: str = "inputs.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps({"kind": nr.INPUTS_KIND, "version": 1, "families": families}, indent=1))
    return path


def no_u_anywhere(obj, path="") -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k != "U" and not str(k).startswith("U_"), path + "/" + str(k)
            assert not (isinstance(v, str) and len(v) > 160), path + "/" + str(k)      # ids, hashes and short labels only
            no_u_anywhere(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            no_u_anywhere(v, f"{path}[{i}]")


# ----- parity with Gate B's wave 0a --------------------------------------------------------------------------------------


@needs_wave0a
def test_parity_with_gate_b_wave_0a_to_two_decimals_and_exactly(tmp_path):
    doc = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))
    fam = doc["families"]["olmo2-1b"]
    assert fam["governing"] == "plain" and fam["triggers"] == {
        "environment": False, "environment_differs": {k: [] for k in fam["triggers"]["environment_differs"]},
        "fingerprint_check": "not run", "fingerprint": False, "fallback": False}
    assert round(fam["plain"]["sigma_gate_pp"], 2) == 1.83
    assert round(fam["plain"]["sigma_eval0_pp"], 2) == 1.28
    assert round(fam["fallback"]["sigma_gate_pp"], 2) == 2.16
    assert round(fam["sigma_F_pp"], 2) == 1.83 and fam["sigma_F_df"] == 2
    ng = json.loads(NG.read_text())["result"]                       # the frozen reading's own output, byte for byte
    for mode in ("plain", "fallback"):
        for key in ("sigma_gate_pp", "sd_r_pp", "sigma_eval0_pp"):
            assert fam[mode][key] == ng[mode][key], (mode, key)
        assert fam[mode]["r_pp"] == ng[mode]["r_pp"], mode
    assert fam["plain"]["mean_r_pp"] == ng["P4"]["mean_r_pp"] and fam["plain"]["se_mean_r_pp"] == ng["P4"]["se_pp"]
    assert sorted(fam["plain"]["pairs"]) == ["a0@1101|R1@1101", "a0@1102|R2@1102", "a0@1103|R3@1103"]
    assert sorted(fam["fallback"]["pairs"]) == ["R1@1101|R2@1102", "R1@1101|R3@1103", "R2@1102|R3@1103"]
    assert fam["units"]["olmo2-1b a0@1101"]["complete_sha256"] == A0_KEYS[1101]
    assert fam["units"]["olmo2-1b R@1101"]["complete_sha256"] == R_KEYS[1101]
    assert fam["G1_failed_arms"] == [] and all(v["pass"] and v["n"] == 600 for v in fam["G1"].values())
    pool = doc["pooled"]
    assert pool["k"] == 1 and pool["df"] == 2 and pool["s_arm_df"] == 4
    # C-D1 on wave 0a: the per-arm seed SDs of U (P78:127's "1.35 against 2.65"), s_arm = √[(SD_a0² + SD_R²) / 2] on
    # 4 df (2 per arm: n − 1 = 2 seeds' worth each), and, with one family, σ̂_pool = σ̂_F and the pooled median over its
    # three seed-matched pair SEs is σ_eval,0 (1.28); the √P_pool term is SD(r) itself (2 SD(r)² / 2).
    sd = fam["per_arm_sd_u_pp"]
    assert round(sd["a0"], 4) == 2.6475 and round(sd["R"], 4) == 1.3472
    assert math.isclose(pool["s_arm_pp"], math.sqrt((sd["a0"] ** 2 + sd["R"] ** 2) / 2)) and round(pool["s_arm_pp"], 4) == 2.1005
    assert math.isclose(pool["sqrt2_s_arm_pp"], math.sqrt(2) * pool["s_arm_pp"]) and round(pool["sqrt2_s_arm_pp"], 4) == 2.9705
    assert pool["sigma_pool_pp"] == fam["sigma_F_pp"] and pool["sqrt_P_pool_pp"] == fam["plain"]["sd_r_pp"]
    assert pool["median_pair_se_pp"] == fam["plain"]["sigma_eval0_pp"] and round(pool["median_pair_se_pp"], 6) == 1.279264
    assert pool["n_pair_ses"] == 3 and pool["governing_by_family"] == {"olmo2-1b": "plain"}
    assert pool["pair_terms_by_family"] == {"olmo2-1b": fam["plain"]["pair_se_pp"]}
    assert doc["seed_rule"]["plan"] == "A" and doc["seed_rule"]["outcome"] == "plan A"   # 1.83 ≤ 4.5
    assert doc["frozen_sha256"]["gate_b_reading"] == nr.FROZEN["gate_b_reading"][1]
    no_u_anywhere(doc)


@needs_wave0a
def test_the_fingerprint_trigger_makes_the_fallback_govern(tmp_path):
    doc = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family(fingerprint="differs")}))
    fam = doc["families"]["olmo2-1b"]
    assert fam["governing"] == "fallback" and fam["triggers"]["fingerprint"] and fam["triggers"]["fallback"]
    assert not fam["triggers"]["environment"]
    assert round(fam["sigma_F_pp"], 2) == 2.16 and round(fam["fallback"]["sigma_eval0_pp"], 2) == 2.16
    assert fam["fallback"]["fallback"] is True and fam["plain"]["fallback"] is False


@needs_wave0a
def test_an_environment_difference_triggers_the_fallback(tmp_path, monkeypatch):
    real = nr.environment_differs

    def differs(unit, reference):
        return real(unit, reference) + (["gpu"] if unit["role"] == "R" and unit["seed"] == 1102 else [])
    monkeypatch.setattr(nr, "environment_differs", differs)
    doc = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))
    fam = doc["families"]["olmo2-1b"]
    assert fam["triggers"]["environment"] and fam["triggers"]["environment_differs"]["R@1102"] == ["gpu"]
    assert fam["governing"] == "fallback" and round(fam["sigma_F_pp"], 2) == 2.16


@needs_wave0a
def test_the_cli_writes_a_canonical_text_free_output_once(tmp_path):
    inputs = write_inputs(tmp_path, {"olmo2-1b": parity_family()})
    out = tmp_path / "out.json"
    cmd = [sys.executable, "-I", "-B", str(ROOT / "scripts/scale78b/noise_reading.py"), "--inputs", str(inputs), "--out", str(out)]
    run = subprocess.run(cmd, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    printed = json.loads(run.stdout)
    doc = json.loads(out.read_text())
    assert doc["kind"] == nr.OUTPUT_KIND and doc["seed_rule"]["outcome"] == "plan A"
    assert printed["seed_rule"] == "plan A" and round(printed["families"]["olmo2-1b"]["sigma_F_pp"], 2) == 1.83
    assert out.read_bytes() == nr.GB.canonical(doc)
    no_u_anywhere(doc)
    no_u_anywhere(printed)
    again = subprocess.run(cmd, capture_output=True, text=True)
    assert again.returncode != 0 and "written once" in again.stderr


# ----- refusals ----------------------------------------------------------------------------------------------------------------


@needs_wave0a
def test_a_1b_unit_in_a_7_8b_family_refuses(tmp_path):
    """OLMo-2-7B shares the 1B prepared manifest (9ed61826…), so there the training identity is what refuses the 1B
    record (f46279e5… is not 36738c38…); Llama-3.1-8B's manifest (c52a50af…) refuses it one check earlier."""
    with pytest.raises(SystemExit, match="training_identity is not the family's \\(36738c38"):
        nr.read(write_inputs(tmp_path, {"olmo2-7b": parity_family()}, "olmo2-7b.json"))
    with pytest.raises(SystemExit, match="manifest_sha256 is not the family's"):
        nr.read(write_inputs(tmp_path, {"llama31-8b": parity_family()}, "llama31-8b.json"))
    assert nr.FAMILIES["olmo2-7b"]["manifest_sha256"] == nr.FAMILIES["olmo2-1b"]["manifest_sha256"]
    assert nr.FAMILIES["olmo2-7b"]["training_identity"] != nr.FAMILIES["olmo2-1b"]["training_identity"]


@needs_wave0a
def test_a_wrong_complete_sha256_key_refuses(tmp_path):
    fam = parity_family()
    fam["a0"]["1102"]["complete_sha256"] = A0_KEYS[1103]
    with pytest.raises(SystemExit, match="COMPLETE.json's SHA-256 is not the key given"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}))


@needs_wave0a
def test_a_unit_listed_twice_refuses_on_the_duplicate_check(tmp_path):
    """C-D4: the same unit in another seed's slot refuses as a duplicate (its COMPLETE.json SHA-256 is already read),
    because the key is checked before the unit's own checks; a different unit in the wrong slot refuses on the seed."""
    fam = parity_family()
    fam["a0"]["1102"] = dict(fam["a0"]["1101"])
    with pytest.raises(SystemExit, match="olmo2-1b a0@1102: its COMPLETE.json SHA-256 is already read as olmo2-1b a0@1101"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}))
    fam = parity_family()
    fam["R"]["1103"] = dict(fam["R"]["1101"])
    with pytest.raises(SystemExit, match="olmo2-1b R@1103: its COMPLETE.json SHA-256 is already read as olmo2-1b R@1101"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}, "r-twice.json"))
    fam = parity_family()
    fam["a0"]["1102"], fam["a0"]["1103"] = fam["a0"]["1103"], fam["a0"]["1102"]
    with pytest.raises(SystemExit, match="olmo2-1b a0@1102: job.json's seed is not 1102"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}, "swap.json"))


@needs_wave0a
def test_a_unit_listed_under_two_families_refuses_as_a_duplicate(tmp_path):
    """The same six units under olmo2-1b and olmo2-7b: the second family's a0@1101 is already read. The duplicate check
    runs before the identity checks (which would refuse the 1B unit in the 7-8B family one step later)."""
    with pytest.raises(SystemExit, match="olmo2-7b a0@1101: its COMPLETE.json SHA-256 is already read as olmo2-1b a0@1101"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family(), "olmo2-7b": parity_family()}))


@needs_wave0a
def test_an_r_unit_that_resumed_refuses_and_an_a0_unit_may_resume(tmp_path, monkeypatch):
    """C-D5 (the verifier's N15): an R arm is a fresh trajectory. R@1101's job.json is read as if it carried resume_from
    (the file on disk is untouched: the frozen read_json is wrapped for that one path); the a0 rule is Gate B's
    gate_a_unit's: Gate A's 1101 resumed from its init unit, and the resume source is recorded by its COMPLETE.json hash."""
    real = nr.GB.read_json
    target = (r_unit(1101) / "job.json").resolve()

    def with_resume(path, what):
        doc = real(path, what)
        if Path(path).resolve() == target:
            doc = dict(doc)
            doc["resume_from"] = "an-init-unit"
        return doc
    monkeypatch.setattr(nr.GB, "read_json", with_resume)
    with pytest.raises(SystemExit, match="olmo2-1b R@1101: an R arm is a fresh trajectory \\(no resume\\)"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))
    monkeypatch.undo()
    units = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}, "plain.json"))["families"]["olmo2-1b"]["units"]
    assert all(units[f"olmo2-1b R@{s}"]["resumed_from_complete_sha256"] is None for s in (1101, 1102, 1103))
    assert units["olmo2-1b a0@1101"]["resumed_from_complete_sha256"] == "b5083ce9d9f26efe92f9872fdbf9376a521a5d99d1b70cc2bd460987cdcc9474"
    assert all(units[f"olmo2-1b a0@{s}"]["resumed_from_complete_sha256"] is None for s in (1102, 1103))


def test_a_parity_only_family_is_never_pooled_with_a_tier_family(tmp_path, monkeypatch):
    """C-D5 (the verifier's N17): olmo2-1b serves the Gate B parity only. With family_reading stubbed (no 7-8B R unit
    exists yet, so no real tier family can be read), a file that lists olmo2-1b beside a tier family refuses; two tier
    families pool with k = 2 on 4 df; one family reads alone."""
    def stub(name, spec, bars, base, seen):
        return {"family": name, "parity_only": bool(nr.FAMILIES[name].get("parity_only")),
                **exact_family("4", ["1", "2", "3"], ["6", "3"])}
    monkeypatch.setattr(nr, "family_reading", stub)
    with pytest.raises(SystemExit, match="a parity-only family \\(olmo2-1b\\) is never pooled with a 7-8B family"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": {}, "olmo2-7b": {}}))
    with pytest.raises(SystemExit, match="never pooled with a 7-8B family"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": {}, "llama31-8b": {}, "olmo2-7b": {}}, "three.json"))
    tier = nr.read(write_inputs(tmp_path, {"olmo2-7b": {}, "llama31-8b": {}}, "tier.json"))
    assert tier["pooled"]["k"] == 2 and tier["pooled"]["df"] == 4 and set(tier["families"]) == {"olmo2-7b", "llama31-8b"}
    assert tier["pooled"]["families"] == ["llama31-8b", "olmo2-7b"] and "_exact" not in tier["families"]["olmo2-7b"]
    alone = nr.read(write_inputs(tmp_path, {"olmo2-1b": {}}, "alone.json"))
    assert alone["pooled"]["k"] == 1 and alone["families"]["olmo2-1b"]["parity_only"] is True


@needs_wave0a
def test_a_method_arm_as_an_r_unit_refuses(tmp_path):
    """A wave-1 unit-removal arm at 1101 (its edit file's provenance says family unit) is not an R unit."""
    if not W1.is_dir():
        pytest.skip("Gate B's wave-1 units are not on this Mac")
    units = sorted(p for p in W1.iterdir() if p.name.startswith("1101-edit-") and (p / "COMPLETE.json").is_file())
    assert units, "no wave-1 unit at seed 1101"
    unit = units[0]
    arm = json.loads((unit / "job.json").read_text())["arm"]
    fam = parity_family()
    fam["R"]["1101"] = {"path": str(unit), "complete_sha256": nr.sha256_file(unit / "COMPLETE.json"), "arm": arm}
    with pytest.raises(SystemExit, match="only a0 and R units are N's inputs"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}))


@needs_wave0a
def test_the_seed_set_the_engine_and_the_arm_name_are_checked(tmp_path):
    fam = parity_family()
    fam["R"]["1104"] = fam["R"].pop("1103")
    with pytest.raises(SystemExit, match="seeds 1101, 1102 and 1103 are required"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}, "seeds.json"))
    fam = parity_family()
    fam["engine"]["R"] = ENGINE_GATE_A
    with pytest.raises(SystemExit, match="code_sha256 is not the family's R value"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}, "engine.json"))
    fam = parity_family()
    fam["R"]["1101"]["arm"] = f"edit-{R_ARMS[1102]}"
    with pytest.raises(SystemExit, match="job.json's arm is not the named R edit"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}, "arm.json"))
    fam = parity_family()
    fam["fingerprint_check"] = "maybe"
    with pytest.raises(SystemExit, match="fingerprint_check must be one of"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}, "fp.json"))


def test_unknown_families_and_malformed_inputs_refuse(tmp_path):
    with pytest.raises(SystemExit, match="not a family of this reading"):
        nr.read(write_inputs(tmp_path, {"qwen25-7b": {}}, "fam.json"))
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"kind": "something else", "version": 1, "families": {}}))
    with pytest.raises(SystemExit, match="not a scale-78b noise reading inputs file"):
        nr.read(bad)
    with pytest.raises(SystemExit, match="exactly"):
        nr.read(write_inputs(tmp_path, {"olmo2-7b": {"engine": {}}}, "keys.json"))


# ----- the seed rule, exactly -------------------------------------------------------------------------------------------------


def sigma_of(pp: str):
    """A Sigma whose value is exactly pp (one radicand, the σ_eval term below it)."""
    return sigma_exact(Fraction(pp))


def sigma_exact(value: Fraction):
    return ((value * value,), (Fraction(1),))


def exact_family(sd_r: str, se_list: list, arm_sds: list, governing: str = "plain", n: int = 3) -> dict:
    """A family reading's pooled part from decimals: SD(r), its three pair SEs, the per-arm seed SDs of U (n seeds each),
    as family_reading's ``_exact`` block holds them (exact squares)."""
    return {"governing": governing,
            "_exact": {"sdr2": Fraction(sd_r) ** 2, "pair_se2": {f"p{i}": Fraction(s) ** 2 for i, s in enumerate(se_list)},
                       "arm_ss": sum((Fraction(a) ** 2 * (n - 1) for a in arm_sds), Fraction(0)), "arm_df": (n - 1) * len(arm_sds)}}


def test_sigma_pool_the_pooled_median_and_s_arm_on_exact_inputs():
    """C-D1 (the verifier's N4, N5, N6): σ̂_pool = max(√[(2 SD(r_O)² + 2 SD(r_L)²) / 4], the median of the six pair SEs)
    on 4 df; s_arm = √(Σ SS / Σ df) over the four arms (2 df each, 8 df); the median term governs when it is larger; the
    review case; one family alone."""
    O = exact_family("4", ["1", "2", "3"], ["6", "3"])              # SD(r_O) 4; pair SEs 1, 2, 3; a0 SD 6, R SD 3
    L = exact_family("2", ["4", "5", "6"], ["1", "1"])              # SD(r_L) 2; pair SEs 4, 5, 6; both arm SDs 1
    pool = nr.pooled({"olmo2-7b": O, "llama31-8b": L})
    assert pool["k"] == 2 and pool["df"] == 4 and pool["n_pair_ses"] == 6 and pool["families"] == ["llama31-8b", "olmo2-7b"]
    assert pool["P_pool_pp2"] == 10.0 and math.isclose(pool["sqrt_P_pool_pp"], math.sqrt(10))    # (2·16 + 2·4) / 4
    assert pool["median_pair_se_pp"] == 3.5                                                     # SEs 1..6: (3 + 4) / 2
    assert pool["sigma_pool_pp"] == 3.5                                                         # the larger term
    assert not math.isclose(pool["sigma_pool_pp"], math.sqrt(20))                               # a divisor k would read √20
    assert math.isclose(pool["s_arm_pp"], math.sqrt((36 * 2 + 9 * 2 + 1 * 2 + 1 * 2) / 8)) and pool["s_arm_df"] == 8
    assert round(pool["s_arm_pp"], 4) == 3.4278 and math.isclose(pool["sqrt2_s_arm_pp"], math.sqrt(2) * pool["s_arm_pp"])
    assert pool["seed_rule"]["plan"] == "A" and pool["seed_rule"]["df"] == 4 and pool["seed_rule"]["sigma_pp"] == 3.5
    assert pool["pair_terms_by_family"] == {"llama31-8b": {"p0": 4.0, "p1": 5.0, "p2": 6.0},
                                            "olmo2-7b": {"p0": 1.0, "p1": 2.0, "p2": 3.0}}
    assert pool["governing_by_family"] == {"llama31-8b": "plain", "olmo2-7b": "plain"}
    # the median term governs when it is larger: SEs 7..12 → (9 + 10) / 2 = 9.5 → branch H
    pool2 = nr.pooled({"a": exact_family("4", ["10", "11", "12"], ["1", "1"]), "b": exact_family("2", ["7", "8", "9"], ["1", "1"])})
    assert pool2["sigma_pool_pp"] == 9.5 == pool2["median_pair_se_pp"] and pool2["seed_rule"]["plan"] == "H"
    # the review case: SD(r) 11 on both → √[(2·121 + 2·121) / 4] = 11 → review; MDE 0.9340 × 11 = 10.274
    pool3 = nr.pooled({"a": exact_family("11", ["1", "1", "1"], ["1", "1"]), "b": exact_family("11", ["1", "1", "1"], ["1", "1"])})
    assert pool3["sigma_pool_pp"] == 11.0 and pool3["seed_rule"]["outcome"] == "review" and pool3["seed_rule"]["review"] is True
    assert math.isclose(pool3["seed_rule"]["removal_mde_pp"], 10.274)
    # one family: σ̂_pool is its σ̂_F (2 SD(r)² / 2), the median its own three SEs, s_arm on 4 df
    one = nr.pooled({"olmo2-7b": O})
    assert one["k"] == 1 and one["df"] == 2 and one["sigma_pool_pp"] == 4.0 and one["median_pair_se_pp"] == 2.0
    assert one["s_arm_df"] == 4 and math.isclose(one["s_arm_pp"], math.sqrt((36 * 2 + 9 * 2) / 4))


def test_the_seed_rule_thresholds_are_inclusive_and_exact():
    assert nr.seed_rule(sigma_of("4.5"), 4)["plan"] == "A"
    assert nr.seed_rule(sigma_of("4.5000001"), 4)["plan"] == "B9"
    assert nr.seed_rule(sigma_of("6.0"), 4)["plan"] == "B9"
    assert nr.seed_rule(sigma_of("6.0000001"), 4)["plan"] == "H"
    rule = nr.seed_rule(sigma_of("4.5"), 4)
    assert rule["sigma_pp"] == 4.5 and rule["df"] == 4 and rule["method_seeds"] == 6 and rule["primary_contrasts"] == 6
    assert rule["sesoi_pp"] == 5 and rule["review"] is False and rule["outcome"] == "plan A"
    assert round(rule["removal_mde_pp"], 2) == 6.39                   # CALC rule_oc2_out.txt: plan A at 4.5: 6.39
    assert round(nr.seed_rule(sigma_of("6.0"), 4)["removal_mde_pp"], 2) == 6.47    # B9 at 6.0: 6.47
    h = nr.seed_rule(sigma_of("8.24"), 4)
    assert h["plan"] == "H" and h["method_seeds"] == 12 and h["primary_contrasts"] == 3 and h["outcome"] == "branch H (b)"
    # the σ_eval term decides when it is the larger one (the median of two SEs is the mean of two square roots)
    two = ((Fraction(1),), (Fraction(36), Fraction(49)))              # mean of 6 and 7 = 6.5 > 6.0
    assert nr.seed_rule(two, 4)["plan"] == "H"


def test_the_review_ceiling_is_the_mde_rule_itself_one_constant_at_the_boundary():
    """C-D2: review when MDE_FACTOR × σ̂ > 2 × SESOI, compared exactly on squares; the printed ceiling 2 × SESOI /
    MDE_FACTOR is derived from the same factor, so ``review`` and the printed ``removal_mde_pp`` never contradict each
    other. At the exact ceiling the MDE is 2 × SESOI and there is no review; one part in 10⁷ above it there is."""
    for plan, factor in nr.MDE_FACTOR.items():
        assert nr.CEILING_SIGMA_PP[plan] == Fraction(2 * nr.SESOI_PP) / Fraction(factor)
        assert nr.CEILING_SIGMA_PP[plan] * Fraction(factor) == 2 * nr.SESOI_PP               # exact, not within 1e-4
    assert [round(float(nr.CEILING_SIGMA_PP[p]), 4) for p in ("A", "B9", "H")] == [7.0388, 9.2721, 10.7066]
    assert float(nr.CEILING_SIGMA_PP["A"]) > 4.5 and float(nr.CEILING_SIGMA_PP["B9"]) > 6.0    # never binds in A or B9
    ceiling = nr.CEILING_SIGMA_PP["H"]
    at = nr.seed_rule(sigma_exact(ceiling), 4)
    assert at["plan"] == "H" and at["review"] is False and at["outcome"] == "branch H (b)"
    assert math.isclose(at["removal_mde_pp"], 2 * nr.SESOI_PP, abs_tol=1e-9) and at["review_ceiling_sigma_pp"] == float(ceiling)
    above = nr.seed_rule(sigma_exact(ceiling + Fraction(1, 10 ** 7)), 4)
    assert above["review"] is True and above["outcome"] == "review" and above["removal_mde_pp"] > 2 * nr.SESOI_PP
    below = nr.seed_rule(sigma_exact(ceiling - Fraction(1, 10 ** 7)), 4)
    assert below["review"] is False and below["outcome"] == "branch H (b)" and below["removal_mde_pp"] < 2 * nr.SESOI_PP
    # a two-radicand σ_eval term at the boundary (the median of two SEs): the same exact decision
    two_at = ((Fraction(1),), ((ceiling - 1) ** 2, (ceiling + 1) ** 2))      # mean of the roots = ceiling
    assert nr.seed_rule(two_at, 4)["review"] is False
    two_above = ((Fraction(1),), ((ceiling - 1) ** 2, (ceiling + 1 + Fraction(2, 10 ** 7)) ** 2))
    assert nr.seed_rule(two_above, 4)["review"] is True
    # the verifier's band (10.7062, 10.70664): review and the printed MDE now agree (neither says "above 10")
    band = nr.seed_rule(sigma_of("10.7064"), 4)
    assert band["review"] is False and band["removal_mde_pp"] < 10
    assert nr.seed_rule(sigma_of("10.7062"), 4)["review"] is False and nr.seed_rule(sigma_of("10.70"), 4)["removal_mde_pp"] < 10
    r = nr.seed_rule(sigma_of("10.71"), 4)
    assert r["plan"] == "H" and r["review"] is True and r["outcome"] == "review" and r["removal_mde_pp"] > 10
    for plan in ("A", "B9"):                                          # a σ̂ at plan A's or B9's ceiling is already in H
        assert nr.seed_rule(sigma_exact(nr.CEILING_SIGMA_PP[plan]), 4)["plan"] == "H"


def test_the_constants_against_scipy():
    scipy = pytest.importorskip("scipy")
    from scipy.stats import norm
    z80 = norm.ppf(0.8)
    k = {"A": (norm.ppf(1 - 0.05 / 12) + z80) / math.sqrt(6), "B9": (norm.ppf(1 - 0.05 / 6) + z80) / 3,
         "H": (norm.ppf(1 - 0.05 / 6) + z80) / math.sqrt(12)}
    for plan in k:
        assert abs(float(nr.MDE_FACTOR[plan]) - k[plan]) < 5e-5, plan
        assert abs(float(nr.CEILING_SIGMA_PP[plan]) - 2 * nr.SESOI_PP / k[plan]) < 5e-4, plan


# ----- operating characteristics (CALC rule_oc2_out.txt) ------------------------------------------------------------------------


def oc_rows() -> dict:
    rows = {}
    for line in OC.read_text().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 5 and parts[0].replace(".", "").isdigit():
            rows[(float(parts[0]), int(parts[1]))] = tuple(float(p.rstrip("%")) for p in parts[2:])
    return rows


def test_one_row_of_the_operating_characteristics_table_reproduces():
    rows = oc_rows()
    assert rows[(4.5, 4)] == (59.4, 27.6, 13.0)                       # the table's row, as written
    oc = nr.operating_characteristics(4.5, 4)
    assert (round(100 * oc["P_plan_A"], 1), round(100 * oc["P_plan_B9"], 1), round(100 * oc["P_branch_H"], 1)) == (59.4, 27.6, 13.0)


def test_every_row_of_the_table_reproduces_to_its_printed_precision():
    for (sigma, df), (a, b, h) in oc_rows().items():
        oc = nr.operating_characteristics(sigma, df)
        got = (round(100 * oc["P_plan_A"], 1), round(100 * oc["P_plan_B9"], 1), round(100 * oc["P_branch_H"], 1))
        assert all(abs(x - y) <= 0.11 for x, y in zip(got, (a, b, h))), (sigma, df, got, (a, b, h))


def test_the_chi_square_cdf_against_scipy():
    scipy = pytest.importorskip("scipy")
    from scipy.stats import chi2
    for df in (2, 4, 30):
        for x in (0.5, 2.0, 4.0, 9.0, 25.0, 40.0):
            assert math.isclose(nr.chi2_cdf_even(x, df), chi2.cdf(x, df), rel_tol=1e-9, abs_tol=1e-12), (df, x)
    with pytest.raises(ValueError):
        nr.chi2_cdf_even(1.0, 3)


def test_the_pins_and_the_frozen_readers():
    assert nr.SEEDS == (1101, 1102, 1103) == tuple(nr.GB.A0_SEEDS)
    assert set(nr.FAMILIES) == {"olmo2-7b", "llama31-8b", "olmo2-1b"} and nr.TIER_FAMILIES == ("olmo2-7b", "llama31-8b")
    assert nr.FAMILIES["olmo2-1b"]["training_identity"] == nr.GB.TRAINING_IDENTITY       # Gate B's REC and S
    assert nr.FAMILIES["olmo2-7b"]["manifest_sha256"] == nr.GB.PREPARED_MANIFEST_SHA256   # the same prepared set
    assert nr.FROZEN_SHA256 == {name: want for name, (_, want) in nr.FROZEN.items()}
    assert nr.FROZEN_SHA256["gate_b_reading"] == nr.GB.SELF_SHA256


# ----- addendum A6: one family's fallback in the pooled median -----------------------------------------------------------------


@needs_wave0a
def test_one_familys_fallback_puts_its_r_r_pair_terms_beside_the_others_seed_matched_terms(tmp_path):
    """Addendum A6: each family's GOVERNING reading enters the pool. The parity family is read twice at the family level,
    once plain and once with the fingerprint trigger (the one two-family case the data allow: no 7-8B R unit exists):
    the fallback family's terms are its three R-R pair SEs, the plain family's its three seed-matched pair SEs, and the
    pooled median is the median of those six (the mean of the 3rd and 4th); √P_pool pools the two governing SD(r)."""
    bars = nr.GB.read_json(nr.FR.DEFAULT_BARS, "bars")
    plain = nr.family_reading("olmo2-1b", parity_family(), bars, tmp_path, {})
    fallen = nr.family_reading("olmo2-1b", parity_family(fingerprint="differs"), bars, tmp_path, {})
    assert plain["governing"] == "plain" and fallen["governing"] == "fallback"
    assert sorted(plain["_exact"]["pair_se2"]) == ["a0@1101|R1@1101", "a0@1102|R2@1102", "a0@1103|R3@1103"]
    assert sorted(fallen["_exact"]["pair_se2"]) == ["R1@1101|R2@1102", "R1@1101|R3@1103", "R2@1102|R3@1103"]
    for f, mode in ((plain, "plain"), (fallen, "fallback")):
        assert {k: math.sqrt(v) for k, v in f["_exact"]["pair_se2"].items()} == f[mode]["pair_se_pp"]
        assert math.isclose(math.sqrt(f["_exact"]["sdr2"]), f[mode]["sd_r_pp"])
    pool = nr.pooled({"olmo2-7b": plain, "llama31-8b": fallen})       # stand-in names: pooled() reads the blocks only
    seed_matched = sorted(plain["plain"]["pair_se_pp"].values())        # 1.18, 1.28, 1.29
    r_r = sorted(fallen["fallback"]["pair_se_pp"].values())              # 2.00, 2.16, 2.16
    six = sorted(seed_matched + r_r)
    assert pool["n_pair_ses"] == 6 and math.isclose(pool["median_pair_se_pp"], (six[2] + six[3]) / 2)
    assert math.isclose(pool["median_pair_se_pp"], (seed_matched[2] + r_r[0]) / 2)              # (1.29 + 2.00) / 2
    assert round(pool["median_pair_se_pp"], 2) == 1.65
    assert pool["governing_by_family"] == {"llama31-8b": "fallback", "olmo2-7b": "plain"}
    assert pool["pair_terms_by_family"] == {"llama31-8b": fallen["fallback"]["pair_se_pp"], "olmo2-7b": plain["plain"]["pair_se_pp"]}
    assert math.isclose(pool["sqrt_P_pool_pp"],
                        math.sqrt((2 * plain["plain"]["sd_r_pp"] ** 2 + 2 * fallen["fallback"]["sd_r_pp"] ** 2) / 4))
    assert pool["sigma_pool_pp"] == max(pool["sqrt_P_pool_pp"], pool["median_pair_se_pp"]) and pool["df"] == 4
    # both plain: the six seed-matched terms; both fallback: the six R-R terms
    both_plain = nr.pooled({"a": plain, "b": plain})
    assert math.isclose(both_plain["median_pair_se_pp"], (seed_matched[1] + seed_matched[1]) / 2)   # the 3rd and 4th of a doubled list
    both_fallen = nr.pooled({"a": fallen, "b": fallen})
    assert math.isclose(both_fallen["median_pair_se_pp"], r_r[1])


# ----- track B's edit files: what the reader checks on an R unit's edit.json -------------------------------------------------------


@pytest.mark.skipif(not (LLAMA_SEALED / "MANIFEST.json").is_file(), reason="the Llama sealed set is not in this checkout")
def test_the_edit_provenance_check_accepts_the_llama_sealed_sets_r_files_for_n():
    """The rebuilt Llama R_d1-R_d3 (N's Llama R units at 1101-1103) carry exactly the five fields read_unit checks on an R
    unit's edit.json (kind, edit_kind, manifest_sha256, provenance.selection.family, provenance.selection.draw); each is
    refused for another family (the manifest) and another seed (the draw); the OLMo d = 11-16 files and SEAL's R_d1 pass
    for olmo2-7b at their seeds; a unit-removal file and the Llama H1 file are not R units."""
    listed = {r["path"]: r for r in json.loads((LLAMA_SEALED / "MANIFEST.json").read_text())["files"]}
    for d in (1, 2, 3):
        path = LLAMA_SEALED / f"edits/R_d{d}.json"
        doc = json.loads(path.read_text())
        assert nr.sha256_file(path) == listed[f"edits/R_d{d}.json"]["sha256"] == listed[f"edits/R_d{d}.json"]["arm"][len("edit-"):]
        assert nr.r_edit_matches(doc, "llama31-8b", 1100 + d)
        assert not nr.r_edit_matches(doc, "olmo2-7b", 1100 + d) and not nr.r_edit_matches(doc, "olmo2-1b", 1100 + d)
        assert not nr.r_edit_matches(doc, "llama31-8b", 1100 + d + 1) and not nr.r_edit_matches(doc, "llama31-8b", 1100 + d - 1)
        selection = doc["provenance"]["selection"]
        assert (doc["kind"], doc["edit_kind"], doc["manifest_sha256"], selection["family"], selection["draw"]) == \
            ("safety-selection edit", "remove", nr.FAMILIES["llama31-8b"]["manifest_sha256"], "R", d)
        assert doc["provenance"]["seed"] == 1100 + d and len(doc["remove"]) == 600 and doc["counts"]["remove"] == 600
    for d in range(4, 17):
        assert nr.r_edit_matches(json.loads((LLAMA_SEALED / f"edits/R_d{d}.json").read_text()), "llama31-8b", 1100 + d)
    units = sorted((LLAMA_SEALED / "edits").glob("unit_*.json"))
    assert len(units) == 8 and not any(nr.r_edit_matches(json.loads(u.read_text()), "llama31-8b", 1101) for u in units)
    assert not nr.r_edit_matches({}, "llama31-8b", 1101) and not nr.r_edit_matches(None, "llama31-8b", 1101)
    if (OLMO_DRAWS / "MANIFEST.json").is_file():
        for d in range(11, 17):
            doc = json.loads((OLMO_DRAWS / f"edits/R_d{d}.json").read_text())
            assert nr.r_edit_matches(doc, "olmo2-7b", 1100 + d) and nr.r_edit_matches(doc, "olmo2-1b", 1100 + d)
            assert not nr.r_edit_matches(doc, "llama31-8b", 1100 + d)
    seal = json.loads((SEAL / "edits/R_d1.json").read_text())
    assert nr.r_edit_matches(seal, "olmo2-7b", 1101) and nr.r_edit_matches(seal, "olmo2-1b", 1101)
    assert not nr.r_edit_matches(seal, "llama31-8b", 1101) and not nr.r_edit_matches(seal, "olmo2-7b", 1102)
    if LLAMA_H1.is_file():
        assert not nr.r_edit_matches(json.loads(LLAMA_H1.read_text()), "llama31-8b", 1101)


# ----- RV-2 (the second fix round): the re-verifier's test gaps, each with a mutant that dies on it only ------------------

REC_1B = ROOT / "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json"
SYNTHETIC_ENVIRONMENT = {"python": "3.11.9", "machine": "x86_64", "device": "cuda", "packages": {"torch": "2.4.0"},
                         "deterministic_algorithms": True, "safety_selection_numeric": "v1",
                         "cuda": {"name": "A100", "capability": "8.0", "torch_cuda_runtime": "12.1", "cudnn": 8902,
                                  "settings": {}, "env": {}}}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def synthetic_r_unit(folder: Path, edit_bytes: bytes, seed: int, arm: str | None = None) -> dict:
    """A sealed olmo2-1b R unit holding the metadata read_unit reads and nothing else (no eval output, no text):
    job.json, identity.json (REC 1B's recipe, the family's training identity), assets.json (a CUDA environment record,
    a policy and a guard block, the lock's hash), edit.json (the bytes given), the lock, and a COMPLETE.json that lists
    exactly those files with their hashes. The arm defaults to edit-<SHA-256 of edit.json>; another arm makes the unit
    name an edit file that is not its own. Returns the inputs entry {path, complete_sha256, arm}."""
    folder.mkdir(parents=True)
    recipe = json.loads(REC_1B.read_text(encoding="utf-8"))
    fam = nr.FAMILIES["olmo2-1b"]
    recipe_sha = nr.GB.canonical_sha256(recipe)
    arm = arm or "edit-" + sha256_bytes(edit_bytes)
    lock = b"environment-lock-bytes\n"
    job = {"kind": "run-one", "target_checkpoint": "e1", "replicate_of": None, "resume_from": None, "evaluate_bank": "dev",
           "split": "dev", "role": "development", "seed": seed, "arm": arm, "code_sha256": ENGINE_X,
           "manifest_sha256": fam["manifest_sha256"], "recipe_sha256": recipe_sha}
    identity = {"code_sha256": ENGINE_X, "manifest_sha256": fam["manifest_sha256"], "training_identity": fam["training_identity"],
                "recipe": recipe, "recipe_sha256": recipe_sha}
    assets = {"environment": SYNTHETIC_ENVIRONMENT, "policy": {"name": "synthetic"},
              "guard": {"repo": "g", "revision": "r", "files": {}}, "environment_lock": {"sha256": sha256_bytes(lock)}}
    files = {"job.json": canonical(job), "identity.json": canonical(identity), "assets.json": canonical(assets),
             "edit.json": edit_bytes, nr.LOCK_NAME: lock}
    for name, data in files.items():
        (folder / name).write_bytes(data)
    marker = {"complete": True, "kind": "run-one", "job_sha256": sha256_bytes(files["job.json"]),
              "completed_utc": "2026-11-05T15:00:00+00:00", "files": {name: sha256_bytes(data) for name, data in files.items()},
              "identity": {k: identity[k] for k in ("code_sha256", "manifest_sha256", "training_identity", "recipe_sha256")}}
    data = canonical(marker)
    (folder / "COMPLETE.json").write_bytes(data)
    return {"path": str(folder), "complete_sha256": sha256_bytes(data), "arm": arm}


def test_an_r_unit_whose_edit_file_hashes_to_another_arm_refuses(tmp_path):
    """RV-2 (the re-verifier's R3): an R unit's edit.json must hash to the arm the inputs and its job.json name. On a
    synthetic sealed unit (self-consistent: its COMPLETE.json lists the edit file it holds): SEAL's R_d1 bytes under
    their own arm pass read_unit; the same unit holding SEAL's R_d2 file, or R_d1 with one row changed (its five
    provenance fields intact, so only the hash binding can refuse it), under R_d1's arm refuses."""
    r1 = (SEAL / "edits/R_d1.json").read_bytes()
    assert sha256_bytes(r1) == R_ARMS[1101]
    genuine = synthetic_r_unit(tmp_path / "genuine", r1, 1101)
    unit = nr.read_unit(genuine, "R", 1101, "olmo2-1b", ENGINE_X, "olmo2-1b R@1101", tmp_path)
    assert unit["complete_sha256"] == genuine["complete_sha256"] and unit["resumed_from_complete_sha256"] is None
    other_arm = synthetic_r_unit(tmp_path / "other-arm", (SEAL / "edits/R_d2.json").read_bytes(), 1101, arm=genuine["arm"])
    with pytest.raises(SystemExit, match="olmo2-1b R@1101: edit.json is missing or is not the arm's edit file"):
        nr.read_unit(other_arm, "R", 1101, "olmo2-1b", ENGINE_X, "olmo2-1b R@1101", tmp_path)
    doc = json.loads(r1)
    doc["remove"] = sorted(doc["remove"][1:] + [doc["remove"][0] + "0"])
    tampered = canonical(doc)
    assert nr.r_edit_matches(json.loads(tampered), "olmo2-1b", 1101) and sha256_bytes(tampered) != R_ARMS[1101]
    row = synthetic_r_unit(tmp_path / "row-changed", tampered, 1101, arm=genuine["arm"])
    with pytest.raises(SystemExit, match="olmo2-1b R@1101: edit.json is missing or is not the arm's edit file"):
        nr.read_unit(row, "R", 1101, "olmo2-1b", ENGINE_X, "olmo2-1b R@1101", tmp_path)


@needs_wave0a
def test_a_copied_unit_at_another_path_with_the_same_complete_json_refuses_as_a_duplicate(tmp_path):
    """RV-2 (C-D4b): the duplicate key is the COMPLETE.json SHA-256, not the path. Gate A's a0-1101 metadata files are
    copied to another folder (COMPLETE.json, job.json, identity.json, assets.json; no eval output) and listed with the
    same key as a0@1102 of the same family, and as a0@1101 of a second family: each second listing refuses as a
    duplicate before the copy is read."""
    copy = tmp_path / "a0-1101-copy"
    copy.mkdir()
    for name in ("COMPLETE.json", "job.json", "identity.json", "assets.json"):
        (copy / name).write_bytes((GATE_A / name).read_bytes())
    assert nr.sha256_file(copy / "COMPLETE.json") == A0_KEYS[1101] and copy.resolve() != GATE_A.resolve()
    fam = parity_family()
    fam["a0"]["1102"] = {"path": str(copy), "complete_sha256": A0_KEYS[1101]}
    with pytest.raises(SystemExit, match="olmo2-1b a0@1102: its COMPLETE.json SHA-256 is already read as olmo2-1b a0@1101"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}))
    second = parity_family()
    second["a0"]["1101"] = {"path": str(copy), "complete_sha256": A0_KEYS[1101]}
    with pytest.raises(SystemExit, match="olmo2-7b a0@1101: its COMPLETE.json SHA-256 is already read as olmo2-1b a0@1101"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family(), "olmo2-7b": second}, "two-families.json"))


def test_the_edit_provenance_check_refuses_a_rewrite_or_add_edit_and_a_wrong_kind():
    """RV-2 (the re-verifier's R2): each of r_edit_matches's five fields refuses on its own. SEAL's R_d1 passes for
    olmo2-7b at 1101; the same document with edit_kind "rewrite" or "add", with another kind, with another manifest,
    with selection.family "unit" or "H", or with another draw does not."""
    doc = json.loads((SEAL / "edits/R_d1.json").read_text())
    assert nr.r_edit_matches(doc, "olmo2-7b", 1101)
    for edit_kind in ("rewrite", "add", "", None):
        assert not nr.r_edit_matches({**doc, "edit_kind": edit_kind}, "olmo2-7b", 1101), edit_kind
    assert not nr.r_edit_matches({**doc, "kind": "safety-selection recipe"}, "olmo2-7b", 1101)
    assert not nr.r_edit_matches({**doc, "manifest_sha256": nr.FAMILIES["llama31-8b"]["manifest_sha256"]}, "olmo2-7b", 1101)
    selection = doc["provenance"]["selection"]
    for change in ({"family": "unit"}, {"family": "H"}, {"draw": 2}):
        changed = {**doc, "provenance": {**doc["provenance"], "selection": {**selection, **change}}}
        assert not nr.r_edit_matches(changed, "olmo2-7b", 1101), change


@needs_wave0a
def test_an_environment_difference_on_a0_1102_alone_is_attributed_to_it_against_the_a0_1101_reference(tmp_path, monkeypatch):
    """RV-2 (the re-verifier's R4): the family's reference environment is a0-1101's (the module doc; Gate B's rule). The
    a0@1102 unit is read as if its GPU name differed (the record read_unit returns is changed; the files are untouched):
    the trigger fires, the difference is recorded on a0@1102 alone, and every other unit, a0@1101 among them, differs
    in nothing. With a0@1102 as the reference the attribution would invert (five units differing, a0@1102 in nothing)."""
    real = nr.read_unit

    def read_unit(spec, role, seed, family, engine, where, base):
        unit = real(spec, role, seed, family, engine, where, base)
        if role == "a0" and seed == 1102:
            unit = {**unit, "fields": {**unit["fields"], "gpu": "another device"}}
        return unit
    monkeypatch.setattr(nr, "read_unit", read_unit)
    fam = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))["families"]["olmo2-1b"]
    assert fam["triggers"]["environment_differs"] == {"a0@1101": [], "a0@1102": ["gpu"], "a0@1103": [],
                                                      "R@1101": [], "R@1102": [], "R@1103": []}
    assert fam["triggers"]["environment"] and fam["triggers"]["fallback"] and fam["governing"] == "fallback"
    assert round(fam["sigma_F_pp"], 2) == 2.16


def test_hex64_accepts_sixty_four_lower_case_hex_digits_only(tmp_path):
    """RV-2 (the re-verifier's R5): keys, arms and engine ids are 64 lower-case hex digits (hashlib's and the engine's
    spelling). Upper or mixed case, other lengths, other characters and non-strings are refused; through the inputs
    file, an upper-case engine id refuses on the engine check itself, before any unit is read."""
    low = "0123456789abcdef" * 4
    assert nr.hex64(low) and nr.hex64(ENGINE_X) and nr.hex64(R_ARMS[1101])
    for bad in (low.upper(), low[:-1] + "F", low[:63], low + "0", low[:-1] + "g", "edit-" + low, low.encode(), None, 7, [low]):
        assert not nr.hex64(bad), bad
    assert all(nr.hex64(v) for f in nr.FAMILIES.values() for v in (f["training_identity"], f["manifest_sha256"], f["main_config_sha256"]))
    fam = parity_family()
    fam["engine"]["R"] = ENGINE_X.upper()
    with pytest.raises(SystemExit, match="engine must give the a0 and R code identities \\(64 hex each\\)"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}))
