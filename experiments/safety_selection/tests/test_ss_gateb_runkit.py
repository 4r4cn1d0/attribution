"""The Gate B run kit (runkit/gate-b-olmo/; brief gate-b-engine-kit-reading-20261008, Part B: B1-B9 with [D9]) on CPU,
without RunPod, Hugging Face or GitHub: the per-job numbers, caps, guards and funding amounts against hand computations
from the DRAFT and the fixture; the plan tool's wave rules and refusals; the job runner's exact commands (each parsed by
the engine's own CLI), its per-job gate with a fake heartbeat (fits, does not fit, missing, unreadable, deferral in
order, the linked retrain and diagnostics, crashes, a sealed-file mismatch); defer (to an unlaunched host, to a new
host, the stranded retrain); the B5 environment checks at both points through the shared compared_fields; the static
bootstrap run with a fake python; the generated worker bootstrap's two processes run on a synthetic bundle with a fake
torch; the pack's sealed-file refusals; the backup's dry runs. Every script runs from a copy of the kit in a temporary
folder (ROOT = tmp); the sealed files are parsed for ids and counts only and nothing prints an id list or any text;
every fake token is built at run time; no token-like literal is written here. Expected values come from hand
computations written in each test, never from the kit's own output."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import io
import json
import math
import os
import py_compile
import random
import re
import shutil
import stat
import string
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from experiments.safety_selection.__main__ import _parser

ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "runkit" / "gate-b-olmo"
FAMILY_KIT = ROOT / "runkit" / "family-probe"
SEAL_REL = ".ai/inputs/gate-b-sealed-20261008/out"
SEAL = ROOT / SEAL_REL
FIXTURE_REL = "tmp/family-probe-olmo2-1b/expected-fixture-probe.json"
READING = ROOT / "scripts" / "gate_b_reading.py"
REC = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json"
S = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json"
KIT_MODULES = ("gateb_rules", "gateb_mac", "secret_scan", "budget", "probes")
PY = sys.executable
CLEAN_ENV = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}

# a synthetic guard record (the engine's guard_pin shape: pin, present, files with blob ids), R_1101's in the tests
GUARD = {"repo_id": "Qwen/Qwen3Guard-Gen-4B", "revision": "a" * 40, "present": True,
         "files": [{"file": "model.safetensors", "blob": "b" * 64}]}

# the fixture's cap_projection (tmp/family-probe-olmo2-1b/expected-fixture-probe.json), read once by hand
E1_UPPER_S, TRAINING_S = 4360.619162873324, 333.6683323532343

# a synthetic wave-1 balance above the default worst-path need ([D22]: factor 1.25 and pod Granite, every pod at most
# 4 arms: $78.45 = 1.25 x $62.76; Mac Granite $72.85 = 1.25 x $58.28; computed by hand in the [D21] (5) tests and
# test_wave_1_needs_the_funding_record). Tests at other limits or routes pass their own balance.
FUNDED = 80.0


def fake_token() -> str:
    rng = random.Random(os.getpid())
    return "hf" + "_" + "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(34))


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def quarter_up(hours: float) -> float:
    return math.ceil(round(hours * 4, 9)) / 4


def man() -> dict:
    return json.loads((SEAL / "MANIFEST.json").read_text())


def entries() -> dict:
    files = man()["files"]
    return {"R": {e["draw"]: e for e in files if e.get("family") == "R"},
            "unit": sorted((e for e in files if e.get("family") == "unit"), key=lambda e: e["unit"]),
            "M": {(e["unit"], e["draw"]): e for e in files if e.get("family") == "M"}}


def arm_job(entry: dict, seed: int) -> dict:
    return {"kind": "arm", "arm": entry["arm"], "seed": seed, "edit": entry["path"]}


@pytest.fixture
def kit(tmp_path, monkeypatch):
    """A copy of the kit at tmp/runkit/gate-b-olmo (so ROOT = tmp), the sealed folder, the Gate A fixture and REC and
    S (a copy of REC) at their repository paths under tmp, and a loader of the copy's modules."""
    copy = tmp_path / "runkit" / "gate-b-olmo"
    shutil.copytree(KIT, copy, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(SEAL, tmp_path / SEAL_REL)
    (tmp_path / FIXTURE_REL).parent.mkdir(parents=True)
    shutil.copy(ROOT / FIXTURE_REL, tmp_path / FIXTURE_REL)
    for rel in (REC, S):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / REC, tmp_path / rel)
    for p in tmp_path.rglob("*"):
        if p.is_file():
            p.chmod(p.stat().st_mode | stat.S_IWUSR)
    monkeypatch.syspath_prepend(str(copy))
    for name in KIT_MODULES:
        monkeypatch.delitem(sys.modules, name, raising=False)

    def load(relative: str):
        spec = importlib.util.spec_from_file_location(f"gateb_kit_{Path(relative).stem}", copy / relative)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    load.root = copy
    load.repo = tmp_path
    import gateb_mac
    monkeypatch.setattr(gateb_mac, "READING", READING)
    yield load
    for name in KIT_MODULES:
        sys.modules.pop(name, None)


def steps_by_hand(rows: int, removed: int, added: int, recipe: str) -> int:
    return math.ceil((rows - removed + added) / 128)


def plan_tool(kit, monkeypatch):
    """The copy's plan tool with the engine-backed values replaced (the real stream plan has its own test), both
    stages packed (synthetic receipts) and LOCK_SHA256 pinned to a synthetic value."""
    tool = kit("plan_tool.py")
    monkeypatch.setattr(tool.rules, "LOCK_SHA256", "7" * 64)             # [D14]: the lead's pin, synthetic here
    monkeypatch.setattr(tool, "recipe_sha", lambda path: hashlib.sha256(path.encode()).hexdigest())
    monkeypatch.setattr(tool, "stream_steps", steps_by_hand)
    for stage in ("anchor", "gateb"):
        folder = kit.root / "setup" / f"packed-{stage}"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "setup-receipt.json").write_text(json.dumps({"engine_sha256": "e" * 64,
                                                               "sealed_files_sha256": stage[0] * 64}))
    return tool


def init(tool, tmp_path, wave: str, hosts: list[list[dict]], reading: dict | None = None, balance: float | None = None,
         rerun: list[str] | None = None, extra: dict | None = None) -> dict:
    jobs = tmp_path / f"jobs-{wave}-{random.random()}.json"
    jobs.write_text(json.dumps({"hosts": hosts, **(extra or {})}))
    reading_path = None
    if reading is not None:
        reading_path = tmp_path / f"reading-{wave}.json"
        reading_path.write_text(json.dumps(reading))
    balance_path = None
    if balance is not None:
        balance_path = tmp_path / f"balance-{random.random()}.json"
        balance_path.write_text(json.dumps({"usd": balance, "utc": "2026-10-08T12:00:00Z", "source": "lead record"}))
    args = argparse.Namespace(wave=wave, jobs=str(jobs), reading=str(reading_path) if reading_path else None,
                              balance=str(balance_path) if balance_path else None, rerun_mismatched=rerun)
    return tool.init_wave(args)


def complete(tool, wave: str) -> None:
    """Mark every job of a wave complete in plan.json (as record-done would after a clean host)."""
    plan = tool.mac.load_plan()
    for h in plan["hosts"].values():
        if h["wave"] == wave:
            for i, j in enumerate(h["jobs"]):
                j.update(status="complete", unit=f"u{i}", complete_sha256="c" * 64)
            h["done"] = True
    tool.mac.save_plan(plan)


def through(tool, tmp_path, last: str) -> None:
    """Plan and complete every wave before ``last`` (anchor, 0a, 0b, then 1 with enough balance)."""
    e = entries()
    order = ["anchor", "0a", "0b", "1", "2"]
    hosts = {"anchor": [[{"kind": "anchor"}]],
             "0a": [[arm_job(e["R"][d], 1100 + d) for d in (1, 2, 3)]],
             "0b": [[{"kind": "retrain", "arm": "a0", "seed": 1101}, {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]],
             "1": [[arm_job(u, 1101) for u in e["unit"]]]}
    for wave in order[:order.index(last)]:
        init(tool, tmp_path, wave, hosts[wave], balance=FUNDED if wave == "1" else None)
        complete(tool, wave)


# ----- B3: per-job uppers and start requirements, from the fixture by hand -------------------------------------------


def test_the_job_numbers_reproduce_the_draft_from_the_fixture(kit):
    rules = kit("gateb_rules.py")
    fx = {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S}
    fixture = json.loads((ROOT / FIXTURE_REL).read_text())["cap_projection"]
    assert (fixture["e1_upper_s"], fixture["training_s"]) == (E1_UPPER_S, TRAINING_S)
    assert (fixture["overhead_s"], fixture["margin_s"]) == (1000, 900)
    assert sha(ROOT / FIXTURE_REL) == rules.PREREG_FIXTURE_SHA256
    arm = rules.job_record("arm", None, None, None, 33, fx)
    by_hand = E1_UPPER_S + TRAINING_S * 33 / 38 + 1000 + 900       # [D11] B-5: training x steps/38 (289.8 s)
    assert arm["upper_s"] == pytest.approx(by_hand) and arm["start_requirement_s"] == pytest.approx(by_hand + 1800)
    assert round(TRAINING_S * 33 / 38, 1) == 289.8
    assert round(arm["start_requirement_s"] / 3600, 2) == 2.32                       # a 33-step removal arm
    at38 = rules.job_record("arm", None, None, None, 38, fx)
    assert round(at38["start_requirement_s"] / 3600, 2) == 2.33                      # 38 steps
    retrain = rules.job_record("retrain", "a0", 1101, None, 38, fx)
    assert retrain["start_requirement_s"] == pytest.approx(TRAINING_S + 1000 + 900 + 1800)
    assert round(retrain["start_requirement_s"] / 3600, 2) == 1.12
    diagnostics = rules.job_record("diagnostics", None, 1101, None, None, fx, 0)
    assert diagnostics["upper_s"] == pytest.approx(1.5 * 2.0 * 3600)                 # [D13]: 1.5 x its 2.0 h upper
    assert diagnostics["start_requirement_s"] == pytest.approx(3.5 * 3600)
    assert rules.job_record("anchor", None, None, None, None, fx)["start_requirement_s"] == pytest.approx(0.75 * 3600)
    longer = rules.job_record("arm", None, None, None, 76, fx)                       # steps scale both ways
    assert longer["upper_s"] == pytest.approx(E1_UPPER_S + 2 * TRAINING_S + 1900)
    pair = rules.default_jobs(["retrain", "diagnostics"], fx)
    assert [round(r / 3600, 4) for r in rules.requirements(pair)] == [3.65, 3.5]   # the link: 0.15 + 3.5 = 3.65 h
    assert pair[1]["a0_source"] == 0
    alone = rules.default_jobs(["retrain"], fx)
    assert rules.requirements(alone) == [pytest.approx(TRAINING_S + 3700)]
    assert {k: rules.MEASURED_UPPER_S[k] / 3600 for k in rules.KINDS} == pytest.approx(
        {"anchor": 0.25, "retrain": 0.15, "arm": 52 / 60, "diagnostics": 2.0})          # [D11]
    assert rules.SPEND_UPPER_S["anchor"] == pytest.approx(0.15 * 3600)                # [D9] B-1
    assert rules.CAP_STEP_S == 900 and rules.POD_OVERHEAD_S == 42 * 60 and rules.START_MARGIN_S == 1800


def test_a_pod_uses_the_larger_of_the_plan_and_its_own_projection(kit):
    rules = kit("gateb_rules.py")
    fx = {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S}
    jobs = [rules.job_record("arm", "x", 1101, "e", 33, fx), rules.job_record("retrain", "a0", 1101, None, 38, fx),
            rules.job_record("diagnostics", None, 1101, None, None, fx, 1)]
    slower = {"e1_upper_s": 6000.0, "training_s": 400.0, "overhead_s": 1200.0, "margin_s": 900}
    need = rules.requirements(jobs, slower)
    assert need[0] == pytest.approx(6000.0 + 400.0 * 33 / 38 + 1200.0 + 900 + 1800)     # x steps/38 ([D11] B-5)
    assert need[1] == pytest.approx(max(400.0 + 1200.0 + 900 + 1800, 0.15 * 3600 + 3.5 * 3600))
    faster = {"e1_upper_s": 100.0, "training_s": 10.0, "overhead_s": 5.0, "margin_s": 1}
    assert rules.requirements(jobs, faster)[0] == pytest.approx(jobs[0]["start_requirement_s"])   # never below plan
    with pytest.raises(ValueError):
        rules.requirements(jobs, {})
    assert rules.gate(None, 1.0) is False and rules.gate(10.0, 10.0) is True and rules.gate(9.99, 10.0) is False


# ----- B4: caps, guards and the funding amounts --------------------------------------------------------------------


def test_every_draft_cap_and_guard(kit):
    rules = kit("gateb_rules.py")
    fx = {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S}
    arm, retrain, diag, anchor = ((E1_UPPER_S + TRAINING_S * 33 / 38 + 1900 + 1800) / 3600, (TRAINING_S + 3700) / 3600,
                                  3.5, 0.75)
    m_arm, m_retrain, m_diag = 52 / 60, 0.15, 2.0

    def cap(kinds):
        return rules.cap_hours(rules.default_jobs(kinds, fx))

    def arms_by_hand(n):
        return quarter_up(max(0.7 + k * m_arm + arm for k in range(n)))
    # [D20]: the guard's planning price is $1.85/h: 6 + 1.5 x 1.85 = 6 + 2.775 = 8.775; 6 + 5 x 1.85 = 6 + 9.25 = 15.25
    assert cap(["anchor"]) == quarter_up(0.7 + anchor) == 1.5 and rules.guard_usd(1.5) == pytest.approx(8.775)
    assert cap(["arm"] * 3) == arms_by_hand(3) == 5.0 and rules.guard_usd(5.0) == pytest.approx(15.25)
    by_hand_0b = quarter_up(max(0.7 + max(retrain, m_retrain + diag), 0.7 + m_retrain + diag))
    # 6 + 4.5 x 1.85 = 6 + 8.325 = 14.325; 6 + 9.25 x 1.85 = 6 + 17.1125 = 23.1125
    assert cap(["retrain", "diagnostics"]) == by_hand_0b == 4.5 and rules.guard_usd(4.5) == pytest.approx(14.325)  # [D11]
    assert cap(["arm"] * 8) == arms_by_hand(8) == 9.25 and rules.guard_usd(9.25) == pytest.approx(23.1125)
    assert [cap(["arm"] * n) for n in (4, 6, 8)] == [5.75, 7.5, 9.25]                      # wave 2 at m = 2 / 3 / 4
    assert [cap(["arm"] * n) for n in (4, 6)] == [5.75, 7.5]                              # extension: 1 / 2 units
    assert cap(["arm"] * 4) == 5.75                                                       # the length control
    # two parallel wave-1 pods: 6 + (5.75 + 5.75) x 1.85 = 6 + 21.275 = 27.275; one pod of 7.5 h: 6 + 13.875 = 19.875
    assert 2 * rules.guard_usd(5.75) - rules.RESERVE_USD == pytest.approx(27.275)
    assert rules.guard_usd(7.5) == pytest.approx(19.875)
    # one order whose first job attains the maximum: [diagnostics, retrain] (no link: the retrain comes after)
    order = [rules.job_record("diagnostics", None, 1101, None, None, fx, None),
             rules.job_record("retrain", "a0", 1101, None, 38, fx)]
    assert 0.7 + diag == pytest.approx(4.2) and rules.cap_hours(order) == quarter_up(4.2) == 4.25   # [D13]
    last_only = quarter_up(0.7 + m_diag + retrain)
    assert round(0.7 + m_diag + retrain, 2) == 3.82 and last_only == 4.0 and rules.cap_hours(order) != last_only


def test_the_funding_amounts_to_the_cent(kit):
    rules = kit("gateb_rules.py")
    fx = {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S}

    def pod(kinds):
        return {"kinds": kinds, "cap_hours": rules.cap_hours(rules.default_jobs(kinds, fx))}

    def spend(hours_of_jobs):                                  # [D20]: spend at the measured $1.79/h
        return (0.7 + hours_of_jobs) * 1.79
    # by hand, [D20] ($1.79/h spend, $1.85/h at the guard): 8 arms (0.7 + 6.9333) x 1.79 = 13.6637; 6 arms 5.9 x 1.79 =
    # 10.561; 4 arms (0.7 + 3.4667) x 1.79 = 7.4583; 3 arms 3.3 x 1.79 = 5.907; the anchor 0.85 x 1.79 = 1.5215
    w2, ext, lc = [pod(["arm"] * 8)], [pod(["arm"] * 6)], [pod(["arm"] * 4)]
    one = rules.funding_need_usd([[pod(["arm"] * 8)], w2, ext, lc])["need_usd"]          # factor 1: the base
    # terms: 6 + 1.85 x 9.25 = 23.1125; 13.6637 + 23.1125 = 36.7762; 2 x 13.6637 + 6 + 1.85 x 7.5 = 47.2023;
    # 2 x 13.6637 + 10.561 + 6 + 1.85 x 5.75 = 54.5258 -> $54.53
    by_hand_one = max(6 + 1.85 * 9.25, spend(8 * 52 / 60) + 6 + 1.85 * 9.25,
                      2 * spend(8 * 52 / 60) + 6 + 1.85 * 7.5, 2 * spend(8 * 52 / 60) + spend(6 * 52 / 60) + 6 + 1.85 * 5.75)
    assert one == round(by_hand_one, 2) == 54.53                                       # needs are in cents
    two = rules.funding_need_usd([[pod(["arm"] * 4), pod(["arm"] * 4)], w2, ext, lc])["need_usd"]
    # 2 x 7.4583 + 13.6637 + 10.561 + 6 + 1.85 x 5.75 = 14.9167 + 13.6637 + 10.561 + 16.6375 = 55.7788 -> $55.78
    by_hand_two = 2 * spend(4 * 52 / 60) + spend(8 * 52 / 60) + spend(6 * 52 / 60) + 6 + 1.85 * 5.75   # 42 min per pod
    assert two == round(by_hand_two, 2) == 55.78
    waves12 = rules.funding_need_usd([[pod(["arm"] * 8)], w2])["need_usd"]
    assert waves12 == round(spend(8 * 52 / 60) + 6 + 1.85 * 9.25, 2) == 36.78                # 13.6637 + 23.1125 = 36.7762
    pre = rules.funding_need_usd([[pod(["anchor"])], [pod(["arm"] * 3)], [pod(["retrain", "diagnostics"])]])["need_usd"]
    by_hand_pre = spend(0.15) + spend(3 * 52 / 60) + 6 + 1.85 * 4.5                       # [D9] B-1: anchor spend 0.15 h
    # 1.5215 + 5.907 + 6 + 8.325 = 21.7535 -> $21.75 (the earlier terms: 8.775 and 1.5215 + 6 + 9.25 = 16.7715)
    assert pre == round(by_hand_pre, 2) == 21.75                                           # [D11]: wave 0b at 4.5 h
    capped = rules.funding_need_usd([[pod(["anchor"])], [pod(["arm"] * 3)],
                                     [{"kinds": ["retrain", "diagnostics"], "cap_hours": 3.5}]])["need_usd"]
    # with cap_0b 3.5 h: 1.5215 + 5.907 + 6 + 1.85 x 3.5 = 7.4285 + 6 + 6.475 = 19.9035 -> $19.90
    assert capped == round(spend(0.15) + spend(3 * 52 / 60) + 6 + 1.85 * 3.5, 2) == 19.90
    # [D11], [D13]: wave 1 needs 1.15 x the base; the extra is the contingency
    factored = {n: rules.funding_need_usd(path, rules.CONTINGENCY_FACTOR) for n, path in (
        ("one", [[pod(["arm"] * 8)], w2, ext, lc]), ("two", [[pod(["arm"] * 4), pod(["arm"] * 4)], w2, ext, lc]),
        ("waves12", [[pod(["arm"] * 8)], w2]))}
    for n, base in (("one", one), ("two", two), ("waves12", waves12)):
        f = factored[n]
        assert f["base_need_usd"] == base and f["contingency_usd"] == round(f["need_usd"] - base, 2)
    # the DRAFT: the factor multiplies the base rounded to the cent, then the product is rounded to the cent ([D20]).
    # [D22]: the factor is 1.25: 1.25 x 54.53 = 68.1625 -> $68.16 (contingency $13.63); 1.25 x 55.78 = 69.725 -> $69.73
    # ($13.95); 1.25 x 36.78 = 45.975 -> $45.98 ($9.20)
    assert rules.CONTINGENCY_FACTOR == 1.25
    assert [factored[n]["need_usd"] for n in ("one", "two", "waves12")] == [68.16, 69.73, 45.98]
    assert [factored[n]["contingency_usd"] for n in ("one", "two", "waves12")] == [13.63, 13.95, 9.20]
    # the old factor still gives the [D20] figures: 1.15 x 54.53 = 62.7095 -> $62.71 ($8.18); 1.15 x 55.78 = 64.147 ->
    # $64.15 ($8.37); 1.15 x 36.78 = 42.297 -> $42.30 ($5.52)
    old = {n: rules.funding_need_usd(path, 1.15) for n, path in (
        ("one", [[pod(["arm"] * 8)], w2, ext, lc]), ("two", [[pod(["arm"] * 4), pod(["arm"] * 4)], w2, ext, lc]),
        ("waves12", [[pod(["arm"] * 8)], w2]))}
    assert [old[n]["need_usd"] for n in ("one", "two", "waves12")] == [62.71, 64.15, 42.30]
    assert [old[n]["contingency_usd"] for n in ("one", "two", "waves12")] == [8.18, 8.37, 5.52]
    assert rules.cents(62.7095) == 62.71 and rules.cents(64.147) == 64.15 and rules.cents(0.125) == 0.13
    assert rules.cents(68.1625) == 68.16 and rules.cents(69.725) == 69.73 and rules.cents(45.975) == 45.98
    # a half-cent tie: the term 6 + 1.85 x 0.1 = $6.185 gives the base $6.19; at 1.15 the need 1.15 x 6.19 = 7.1185 ->
    # $7.12 and the contingency is the need minus the rounded base, $0.93 (not 7.12 - 6.185 = 0.935 -> $0.94); at 1.25
    # the need 1.25 x 6.19 = 7.7375 -> $7.74 and the contingency $1.55
    tie = rules.funding_need_usd([[{"kinds": ["anchor"], "cap_hours": 0.1}]], 1.15)
    assert (tie["base_need_usd"], tie["need_usd"], tie["contingency_usd"]) == (6.19, 7.12, 0.93)
    tie = rules.funding_need_usd([[{"kinds": ["anchor"], "cap_hours": 0.1}]], rules.CONTINGENCY_FACTOR)
    assert (tie["base_need_usd"], tie["need_usd"], tie["contingency_usd"]) == (6.19, 7.74, 1.55)
    # re-run uppers at $1.79/h ([D20]); a new pod adds 42 min = 0.7 x 1.79 = $1.253:
    # arm 52/60 x 1.79 = $1.5513 (new pod $2.8043); retrain and anchor 0.15 x 1.79 = $0.2685 (new pod 0.85 x 1.79 =
    # $1.5215); diagnostics 2.0 x 1.79 = $3.58 (new pod 2.7 x 1.79 = $4.833)
    for kind, h in (("arm", 52 / 60), ("retrain", 0.15), ("anchor", 0.15), ("diagnostics", 2.0)):
        assert rules.rerun_cost_usd(kind, False) == pytest.approx(h * 1.79)
        assert rules.rerun_cost_usd(kind, True) == pytest.approx((0.7 + h) * 1.79)
    assert rules.rerun_cost_usd("arm", True) == pytest.approx(2.804333, abs=1e-6)
    assert rules.rerun_cost_usd("diagnostics", True) == pytest.approx(4.833)
    assert rules.WORST_PATH_AFTER_WAVE1 == (("2", 8), ("ext", 6), ("lc", 4))


def test_d21_a_wave_is_split_into_pods_of_at_most_four_arms_dealt_evenly_in_order(kit, monkeypatch):
    """[D21] (1): ceil(n / MAX_ARMS_PER_POD) pods, the arms dealt as evenly as possible in order, the earlier pods
    taking the one extra arm; the value is configurable and validated."""
    rules = kit("gateb_rules.py")
    assert rules.MAX_ARMS_PER_POD == 4
    by_hand = {1: [1], 3: [3], 4: [4], 5: [3, 2], 6: [3, 3], 7: [4, 3], 8: [4, 4], 9: [3, 3, 3], 10: [4, 3, 3],
               13: [4, 3, 3, 3]}
    assert {n: rules.pod_sizes(n) for n in by_hand} == by_hand
    assert rules.split_pods(list("abcdefg")) == [list("abcd"), list("efg")]
    monkeypatch.setattr(rules, "MAX_ARMS_PER_POD", 8)
    assert [rules.pod_sizes(n) for n in (4, 6, 8, 9)] == [[4], [6], [8], [5, 4]]
    monkeypatch.setattr(rules, "MAX_ARMS_PER_POD", 3)
    assert [rules.pod_sizes(n) for n in (3, 4, 8)] == [[3], [2, 2], [3, 3, 2]]
    for bad in (0, -1, 2.0, True, None):
        monkeypatch.setattr(rules, "MAX_ARMS_PER_POD", bad)
        with pytest.raises(ValueError, match="positive integer"):
            rules.pod_sizes(8)
    monkeypatch.setattr(rules, "MAX_ARMS_PER_POD", 4)
    with pytest.raises(ValueError):
        rules.pod_sizes(0)


def test_d21_the_worst_path_need_counts_every_later_launch_in_pods_of_at_most_four_arms(kit, monkeypatch):
    """[D21] (2), at the rules level: the plan tool's worst_path_need builds wave 2 (8 arms) as 4 + 4, the extension
    (6) as 3 + 3 and the length control (4) as one pod, each launch's pods in parallel (caps summed at $1.85/h). By
    hand ([D20]): 4-arm pod: spend (0.7 + 3.46667) x 1.79 = 7.45833, cap quarter_up(0.7 + 3 x 52/60 + 2.31955) =
    quarter_up(5.61955) = 5.75 h; 3-arm pod: spend 3.3 x 1.79 = 5.907, cap quarter_up(0.7 + 1.73333 + 2.31955) =
    quarter_up(4.75288) = 5.0 h. Terms: 6 + 1.85 x 11.5 = 27.275; 14.91667 + 27.275 = 42.19167; 29.83333 + 6 + 18.5 =
    54.33333; 29.83333 + 11.814 + 6 + 10.6375 = 58.28483 -> $58.28; [D22] x 1.25 = 72.85 -> $72.85 (contingency $14.57;
    at [D21]'s 1.15 it was $67.02). The extension's split does not change it: 4 + 2 would spend the same (6 arms, two
    pods: 7.45833 + 4.35567 = 11.814) and its term 29.83333 + 6 + 1.85 x (5.75 + 4.0) = 53.87083 is not the largest.
    With MAX_ARMS_PER_POD = 8 the path is revision 4b's: $54.53 -> $68.16 (1.25 x 54.53 = 68.1625) with one wave-1
    pod, $55.78 -> $69.73 (69.725) with two. The Mac route (GRANITE_ON_POD False) is set here: the pod route is
    tested in the [D21] (5) tests."""
    tool = kit("plan_tool.py")
    monkeypatch.setattr(tool.rules, "GRANITE_ON_POD", False)
    fx = {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S}
    arm_h = (E1_UPPER_S + TRAINING_S * 33 / 38 + 3700) / 3600
    assert round(arm_h, 5) == 2.31955
    assert quarter_up(0.7 + 3 * 52 / 60 + arm_h) == 5.75 and quarter_up(0.7 + 2 * 52 / 60 + arm_h) == 5.0
    assert quarter_up(0.7 + 52 / 60 + arm_h) == 4.0

    def wave1(sizes):
        return [tool.rules.default_jobs(["arm"] * n, fx) for n in sizes]
    four, three = (0.7 + 4 * 52 / 60) * 1.79, (0.7 + 3 * 52 / 60) * 1.79
    terms = [6 + 1.85 * 11.5, 2 * four + 6 + 1.85 * 11.5, 4 * four + 6 + 1.85 * 10.0,
             4 * four + 2 * three + 6 + 1.85 * 5.75]
    need = tool.worst_path_need({"fixture": fx}, wave1([4, 4]))
    assert need["terms_usd"] == pytest.approx(terms)
    assert round(terms[-1], 5) == 58.28483 and max(terms) == terms[-1]
    assert (need["base_need_usd"], need["need_usd"], need["contingency_usd"]) == (58.28, 72.85, 14.57)
    assert round(29.83333 + 6 + 1.85 * (5.75 + 4.0), 5) == 53.87083 < 58.28           # the 4 + 2 extension term
    monkeypatch.setattr(tool.rules, "MAX_ARMS_PER_POD", 8)
    one, two = tool.worst_path_need({"fixture": fx}, wave1([8])), tool.worst_path_need({"fixture": fx}, wave1([4, 4]))
    assert (one["base_need_usd"], one["need_usd"]) == (54.53, 68.16)
    assert (two["base_need_usd"], two["need_usd"]) == (55.78, 69.73)


def test_the_budget_guard_shares_the_rules_constants_and_its_rule(kit):
    budget = kit("budget.py")
    rules = kit("gateb_rules.py")
    assert budget.RESERVE_USD == rules.RESERVE_USD == 6.0                                # [D20]: the reserve stays $6
    assert budget.PLANNING_PRICE == rules.PLANNING_PRICE_USD == 1.85 and rules.RATE_USD == 1.79   # [D20]
    assert rules.MAX_PRICE_USD == 10.0 and not hasattr(budget, "MAX_PRICE")             # [D20] amended: create only
    family = (FAMILY_KIT / "budget.py").read_text()
    rule = family[family.index("def main() -> int:"):]
    assert rule in (kit.root / "budget.py").read_text()                                  # [D9] B-7: unchanged rule
    assert "gate-b-olmo*" in budget.KITS_GLOB and "family-probe-*" in budget.KITS_GLOB


# ----- [D20] as amended: a $10.00/h limit at create; the planning price at the guard -----------------------------


ABSENT = object()          # a create reply with no costPerHr key at all


def _fake_pod_api(price, calls: list):
    """host.api without RunPod: an empty pod listing, a create that returns ``price`` as costPerHr (no costPerHr key
    when ``price`` is ABSENT), a stop that succeeds and a read that shows the pod EXITED."""
    def api(method, path, payload=None):
        calls.append((method, path))
        if (method, path) == ("GET", "/pods"):
            return 200, []
        if (method, path) == ("POST", "/pods"):
            pod = {"id": "pod-synthetic", "name": payload["name"], "desiredStatus": "RUNNING"}
            return 201, pod if price is ABSENT else {**pod, "costPerHr": price}
        if method == "POST" and path.endswith("/stop"):
            return 200, {}
        return 200, {"desiredStatus": "EXITED"}
    return api


@pytest.mark.parametrize("price, created", [(1.79, True), (3.50, True), (10.0, True), (10.01, False), (1.79e2, False),
                                            (0.0, True), (-1.0, True), (float("nan"), False), (float("inf"), False), (float("-inf"), False),
                                            (None, False), pytest.param(ABSENT, False, id="absent-key-False"),
                                            ("1.79", False), (True, False)])
def test_create_refuses_a_missing_non_finite_or_over_ten_dollar_price(kit, monkeypatch, price, created):
    """[D20] (1) as amended (the user, brief revision 17): host.py create keeps a pod at a finite costPerHr up to $10.00/h
    (the measured $1.79/h, $3.50/h, exactly $10.00/h; $0 and -$1 too: there is no lower bound) and stops at once one
    whose price is above $10.00/h ($10.01, $179), NaN, +-infinite, missing (None, or a reply with no costPerHr key:
    never a default price), a string or a boolean (price-guard-stop.json, stop confirmed)."""
    host = kit("host.py")
    assert host.MAX_PRICE == kit("gateb_rules.py").MAX_PRICE_USD == 10.0
    (kit.root / "plan.json").write_text(json.dumps({"hosts": {"anchor-1": {"cap_hours": 1.5, "container_disk_gb": 60,
                                                                           "volume_gb": 20}}}))
    (kit.root / "ssh").mkdir(exist_ok=True)
    (kit.root / "ssh" / "key.pub").write_text("synthetic public key\n")

    def timer_settings(args, **kwargs):                       # the pod-timer settings without the engine
        out = Path(args[args.index("--out") + 1])
        out.write_text(json.dumps({"env": {"POD_TIMER_CAP_MINUTES": "90"}, "docker_start_cmd": ["bash"],
                                   "cap_stop_utc": "2026-10-09T20:00:00+00:00"}))
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(host, "subprocess", argparse.Namespace(run=timer_settings, DEVNULL=subprocess.DEVNULL))
    calls = []
    monkeypatch.setattr(host, "api", _fake_pod_api(price, calls))
    monkeypatch.setattr(host, "SLEEP", lambda s: None)
    folder = kit.root / "hosts" / "anchor-1"
    if created:
        record = host.create("anchor-1")
        stops = [c for c in calls if c[1].endswith("/stop")]
        assert record["costPerHr"] == price and record["id"] == "pod-synthetic" and stops == []
        assert (folder / "pod.json").exists() and not (folder / "price-guard-stop.json").exists()
    else:
        with pytest.raises(SystemExit, match=r"missing, not finite or above \$10\.00/h"):
            host.create("anchor-1")
        stops = [c for c in calls if c[1].endswith("/stop")]
        assert stops == [("POST", "/pods/pod-synthetic/stop")]
        guard_stop = json.loads((folder / "price-guard-stop.json").read_text())
        assert guard_stop["stop"]["confirmed"] is True
        if price is ABSENT or price is None:
            assert guard_stop["costPerHr"] is None                # the reply's price as read, no default filled in


def test_the_guard_counts_intents_and_extensions_at_the_planning_price(kit, monkeypatch):
    """[D20] (2): a create intent without a pod counts at $1.85/h until its cap (2 h: 2 x 1.85 = $3.70), and
    host.py extend-cap asks budget.py check for the added hours at $1.85/h."""
    budget = kit("budget.py")
    now = dt.datetime(2026, 10, 9, 12, 0, tzinfo=dt.timezone.utc)
    intent = kit.root / "hosts" / "w0a-1" / "create-intent.json"
    intent.parent.mkdir(parents=True)
    intent.write_text(json.dumps({"cap_stop_utc": (now + dt.timedelta(hours=2)).isoformat()}))
    (row,) = budget.pending_intents(now)
    assert row["costPerHr"] == 1.85 and row["hours_left_upper"] == 2.0 and row["committed_usd"] == pytest.approx(3.70)
    host = kit("host.py")
    (kit.root / "plan.json").write_text(json.dumps({"hosts": {"w0a-1": {"cap_hours": 5.0}}}))
    stop_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
    (intent.parent / "pod.json").write_text(json.dumps({"id": "pod-synthetic", "name": host.name_of("w0a-1"),
                                                        "cap_stop_utc": stop_at.isoformat()}))
    monkeypatch.setattr(host, "ssh_base", lambda h: [])
    runs = []

    def runner(args, **kwargs):
        runs.append(args)
        if "check" in args:
            return subprocess.CompletedProcess(args, 0, "", "")
        line = {"governs": True, "acknowledged": True, "lease": "l", "stop_at_utc": "2026-10-09T20:00:00Z"}
        return subprocess.CompletedProcess(args, 0, json.dumps(line) + "\n", "")
    host.extend_cap("w0a-1", 2 * 3600, runner=runner)                # one more hour than the recorded stop
    check = runs[0]                                                  # [python, budget.py, check, HOURS, PRICE]
    assert Path(check[1]).name == "budget.py" and check[2] == "check" and check[4] == "1.85"
    assert float(check[3]) == pytest.approx(1.0, abs=0.01)


# ----- B1: the plan tool -----------------------------------------------------------------------------------------


def test_the_engine_stream_plan_gives_33_and_38_steps(kit, monkeypatch):
    tool = kit("plan_tool.py")
    monkeypatch.setattr(tool, "ENGINE_ROOT", ROOT)
    monkeypatch.setattr(tool, "PY", Path(PY))
    assert tool.stream_steps(4800, 600, 0, REC) == 33 == steps_by_hand(4800, 600, 0, REC)
    assert tool.stream_steps(4800, 0, 0, REC) == 38 == steps_by_hand(4800, 0, 0, REC)


def test_the_waves_before_wave_1(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    e = entries()
    out = init(tool, tmp_path, "anchor", [[{"kind": "anchor"}]])
    plan = tool.mac.load_plan()
    host = plan["hosts"][out["hosts"][0]]
    assert out["hosts"] == ["anchor-1"] and host["role"] == "anchor" and host["base_eval"] is False
    assert host["recipe_path"] == REC and host["stage"] == "anchor" and host["cap_hours"] == 1.5
    assert host["guard_usd"] == pytest.approx(6 + 1.5 * 1.85) and host["sealed_files_sha256"] == "a" * 64   # $8.775
    funding = plan["funding"][0]
    # [D11], [D20]: cap_0b 4.5 h; 1.5215 + 5.907 + 6 + 1.85 x 4.5 = 21.7535 -> $21.75
    assert funding["report_only"] is True and funding["need_usd"] == 21.75
    with pytest.raises(SystemExit, match="already planned"):
        init(tool, tmp_path, "anchor", [[{"kind": "anchor"}]])
    with pytest.raises(SystemExit, match="wave anchor is not complete"):
        init(tool, tmp_path, "0a", [[arm_job(e["R"][d], 1100 + d) for d in (1, 2, 3)]])
    complete(tool, "anchor")
    out = init(tool, tmp_path, "0a", [[arm_job(e["R"][d], 1100 + d) for d in (3, 1, 2)]])
    host = tool.mac.load_plan()["hosts"][out["hosts"][0]]
    assert host["role"] == "first" and host["recipe_path"] == S and host["cap_hours"] == 5.0
    assert [j["steps"] for j in host["jobs"]] == [33, 33, 33] and all(j["status"] == "planned" for j in host["jobs"])
    complete(tool, "0a")
    out = init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                       {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])
    host = tool.mac.load_plan()["hosts"][out["hosts"][0]]
    assert [j["kind"] for j in host["jobs"]] == ["retrain", "diagnostics"] and host["jobs"][1]["a0_source"] == 0
    assert host["jobs"][0]["steps"] == 38 and host["cap_hours"] == 4.5
    assert host["guard_usd"] == pytest.approx(6 + 4.5 * 1.85)                            # [D11], [D20]: $14.325
    log = [json.loads(line) for line in (kit.root / "operator-actions.jsonl").read_text().splitlines()]
    assert [r["action"] for r in log] == ["init-wave"] * 3


R_SEEDS = {1: 1101, 2: 1102, 3: 1103}


@pytest.mark.parametrize("case", ["base_eval true", "base_eval in a job", "a0 outside the retrain", "a group-id arm",
                                  "an edit outside MAN", "an edit that is not its arm's", "a non-development seed",
                                  "R_d at another seed", "a fourth R arm", "two pods", "an unknown key",
                                  "diagnostics without its retrain", "a retrain at another seed"])
def test_the_plan_tool_refuses(kit, tmp_path, monkeypatch, case):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    good = [arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]
    hosts, extra, wave, match = [list(good)], None, "0a", None
    if case == "base_eval true":
        extra, match = {"base_eval": True}, "base_eval is false"
    elif case == "base_eval in a job":
        hosts[0][0] = {**good[0], "base_eval": False}
        match = "base_eval is false"
    elif case == "a0 outside the retrain":
        hosts[0][0] = {"kind": "arm", "arm": "a0", "seed": 1101, "edit": None}
        match = "a0 is the retrain's arm only"
    elif case == "a group-id arm":
        hosts[0][0] = {"kind": "arm", "arm": e["unit"][0]["unit"], "seed": 1101, "edit": e["unit"][0]["path"]}
        match = "not an edit arm listed in MAN"
    elif case == "an edit outside MAN":
        hosts[0][0] = {"kind": "arm", "arm": "edit-" + "0" * 64, "seed": 1101, "edit": "edits/R_d1.json"}
        match = "not an edit arm listed in MAN"
    elif case == "an edit that is not its arm's":
        hosts[0][0] = {**good[0], "edit": e["R"][2]["path"]}
        match = "edit must be the MAN file of its arm"
    elif case == "a non-development seed":
        hosts[0][0] = {**good[0], "seed": 2101}
        match = "not a development seed"
    elif case == "R_d at another seed":
        hosts[0][0] = {**good[0], "seed": 1104}
        match = "R_1-R_3, R_d at seed 1100"
    elif case == "a fourth R arm":
        hosts[0].append(arm_job(e["R"][4], 1104))
        match = "R_1-R_3"
    elif case == "two pods":
        hosts = [good[:2], good[2:]]
        match = "one pod"
    elif case == "an unknown key":
        hosts[0][0] = {**good[0], "measured_upper_s": 1}
        match = "keys must be among"
    elif case == "diagnostics without its retrain":
        wave, hosts = "0b", [[{"kind": "diagnostics", "seed": 1101, "a0_source": 0}]]
        match = "a0_source must name an earlier retrain"
    elif case == "a retrain at another seed":
        wave, hosts = "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1102},
                              {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]]
        match = "the retrain is a0 at seed 1101"
    if wave == "0b":
        complete_0a = [arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]
        init(tool, tmp_path, "0a", [complete_0a])
        complete(tool, "0a")
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match=match):
        init(tool, tmp_path, wave, hosts, extra=extra)
    assert (kit.root / "plan.json").read_bytes() == before


def _complete_unit(kit_root: Path, host: str, arm: str, seed: int, assets: dict | None = None, n: int = 1) -> Path:
    unit = kit_root / "retrieved" / host / "tree" / "round1" / f"{seed}-{arm}-e1-a{n}"
    unit.mkdir(parents=True)
    (unit / "job.json").write_text(json.dumps({"kind": "run-one", "arm": arm, "seed": seed, "target_checkpoint": "e1"}))
    (unit / "assets.json").write_text(json.dumps(assets or {}))
    (unit / "COMPLETE.json").write_text(json.dumps({"files": {"job.json": sha(unit / "job.json")}, "n": n}))
    return unit


def _environment(**changes) -> dict:
    env = json.loads((ROOT / FIXTURE_REL).read_text())["environment"]
    env = json.loads(json.dumps(env))
    for key, value in changes.items():
        if key in ("name", "capability", "torch_cuda_runtime", "cudnn", "settings", "env", "driver"):
            env["cuda"][key] = value
        else:
            env[key] = value
    return env


def _policy(**changes) -> dict:
    policy = json.loads(json.dumps(json.loads((ROOT / FIXTURE_REL).read_text())["policy_identity"]))
    policy.update(changes)
    return policy


def test_a_complete_arm_and_seed_is_never_queued_again_unless_its_environment_mismatched(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    jobs = [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]]
    lock = "1" * 64
    reading = tool.mac.reading_module()
    reference = reading.compared_fields(_environment(), lock, _policy())
    unit = _complete_unit(kit.root, "w0a-9", e["R"][1]["arm"], 1101,
                          {"environment": _environment(), "environment_lock": {"sha256": lock}, "policy": _policy()})
    with pytest.raises(SystemExit, match="a complete attempt exists"):
        init(tool, tmp_path, "0a", jobs)
    named = sha(unit / "COMPLETE.json")
    with pytest.raises(SystemExit, match="shows no environment mismatch"):       # no reference: nothing mismatched
        init(tool, tmp_path, "0a", jobs, rerun=[named])
    plan = tool.mac.load_plan()
    plan["reference"] = {"fields": reference, "bootstrap": {}}
    tool.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="shows no environment mismatch"):       # equal fields: never re-run
        init(tool, tmp_path, "0a", jobs, rerun=[named])
    with pytest.raises(SystemExit, match="a complete attempt exists"):           # another attempt's hash
        init(tool, tmp_path, "0a", jobs, rerun=["f" * 64])
    (unit / "assets.json").write_text(json.dumps({"environment": _environment(cudnn=1), "environment_lock":
                                                  {"sha256": lock}, "policy": _policy()}))
    init(tool, tmp_path, "0a", jobs, rerun=[named])
    actions = [json.loads(line) for line in (kit.root / "operator-actions.jsonl").read_text().splitlines()]
    rerun = [a for a in actions if a["action"] == "rerun-mismatched"]
    assert len(rerun) == 1 and rerun[0]["mismatched_fields"] == ["cudnn"] and rerun[0]["complete_sha256"] == named
    job = next(j for h in tool.mac.load_plan()["hosts"].values() if h["wave"] == "0a" and not h.get("done")
               for j in h["jobs"] if j["arm"] == e["R"][1]["arm"])
    assert job["mismatched_complete_sha256"] == named and job["reason"] == "environment-mismatch"   # [D14]


def test_wave_1_needs_the_funding_record(kit, tmp_path, monkeypatch):
    """[D21]: wave 1 is planned as two 4-arm pods (given as one host, which the tool splits, or as that split); the
    need counts every later launch of the worst path in pods of at most 4 arms: wave 2 as 4 + 4, the extension as
    3 + 3, the length control as 4, each launch's pods in parallel. By hand ([D20]: $1.79/h spend, $1.85/h guard):
    a 4-arm pod spends (0.7 + 4 x 52/60) x 1.79 = 4.16667 x 1.79 = $7.4583 and caps 5.75 h; a 3-arm pod (0.7 + 2.6) x
    1.79 = $5.907 and caps 5.0 h. The terms: 6 + 1.85 x 11.5 = 27.275; 14.9167 + 27.275 = 42.1917; 29.8333 + 6 + 1.85 x
    10 = 54.3333; 29.8333 + 11.814 + 6 + 1.85 x 5.75 = 41.6473 + 16.6375 = 58.2848 -> base $58.28; [D22] 1.25 x
    58.28 = 72.85 -> $72.85 (contingency $14.57; [D21]'s 1.15 gave the verifier's $67.02). The Mac route is set here
    (GRANITE_ON_POD False); the default pod route ($78.45) is test_d21_5_init_wave_1_funds_the_route_the_flag_names."""
    tool = plan_tool(kit, monkeypatch)
    monkeypatch.setattr(tool.rules, "GRANITE_ON_POD", False)
    through(tool, tmp_path, "1")
    e = entries()
    units = [arm_job(u, 1101) for u in e["unit"]]
    four, three = (0.7 + 4 * 52 / 60) * 1.79, (0.7 + 3 * 52 / 60) * 1.79
    base = max(6 + 1.85 * 11.5, 2 * four + 6 + 1.85 * 11.5, 4 * four + 6 + 1.85 * 10,
               4 * four + 2 * three + 6 + 1.85 * 5.75)
    assert round(base, 4) == 58.2848
    by_hand = round(1.25 * round(base, 2), 2)
    assert by_hand == 72.85
    with pytest.raises(SystemExit, match="needs --balance"):
        init(tool, tmp_path, "1", [units])
    with pytest.raises(SystemExit, match="below the worst path's need"):
        init(tool, tmp_path, "1", [units], balance=by_hand - 0.01)
    with pytest.raises(SystemExit, match="below the worst path's need"):          # the base alone is not enough
        init(tool, tmp_path, "1", [units], balance=round(base, 2) + 0.01)
    with pytest.raises(SystemExit, match="the 8 unit_g-"):
        init(tool, tmp_path, "1", [units[:7]], balance=100.0)
    with pytest.raises(SystemExit, match="the 8 unit_g-"):
        init(tool, tmp_path, "1", [units[:7] + [arm_job(e["unit"][7], 1102)]], balance=100.0)
    for grouping in ([units[:5], units[5:]], [units[:2], units[2:4], units[4:6], units[6:]], [units[:3], units[3:]]):
        with pytest.raises(SystemExit, match="pods of at most 4 arms, dealt evenly"):   # not the split [4, 4]
            init(tool, tmp_path, "1", grouping, balance=100.0)
    assert not any(h["wave"] == "1" for h in tool.mac.load_plan()["hosts"].values())
    out = init(tool, tmp_path, "1", [units], balance=by_hand)                   # exactly the need passes
    plan = tool.mac.load_plan()
    assert out["hosts"] == ["w1-1", "w1-2"] and out["caps"] == [5.75, 5.75]
    assert [[j["arm"] for j in plan["hosts"][h]["jobs"]] for h in out["hosts"]] == [
        [u["arm"] for u in units[:4]], [u["arm"] for u in units[4:]]]            # dealt in order
    assert [plan["hosts"][h]["guard_usd"] for h in out["hosts"]] == pytest.approx([6 + 5.75 * 1.85] * 2)
    record = plan["funding"][-1]
    assert record["wave"] == "1" and record["need_usd"] == by_hand == 72.85
    assert record["base_need_usd"] == round(base, 2) == 58.28 and record["factor"] == 1.25
    assert record["terms_usd"] == pytest.approx([27.275, 2 * four + 27.275, 4 * four + 24.5,
                                                 4 * four + 2 * three + 16.6375])
    assert plan["contingency"]["usd"] == round(72.85 - 58.28, 2) == 14.57 == plan["contingency"]["remaining_usd"]
    assert record["balance"]["source"] == "lead record" and len(record["balance"]["sha256"]) == 64


@pytest.mark.parametrize("grouping", ["one host", "the split"])
def test_with_eight_arms_per_pod_wave_1_is_one_pod_and_the_need_is_revision_4bs(kit, tmp_path, monkeypatch, grouping):
    """[D21]: with MAX_ARMS_PER_POD = 8 the old one-pod plan returns: wave 1, wave 2 and the extension are one pod
    each, and the need is revision 4b's shape at [D20]'s prices. By hand: 8 arms (0.7 + 8 x 52/60) x 1.79 = 13.6637,
    cap 9.25 h; 6 arms 5.9 x 1.79 = 10.561, 7.5 h; 4 arms 5.75 h. Terms: 6 + 1.85 x 9.25 = 23.1125; 13.6637 + 23.1125
    = 36.7762; 27.3273 + 6 + 13.875 = 47.2023; 27.3273 + 10.561 + 6 + 10.6375 = 54.5258 -> $54.53; 1.15 x 54.53 =
    62.7095 -> $62.71. The two-pod grouping is no longer the split, so it refuses. [D22]: this is the test that the old
    factor still gives the [D21] figures: it sets CONTINGENCY_FACTOR 1.15 and the Mac route (GRANITE_ON_POD False)."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    monkeypatch.setattr(tool.rules, "MAX_ARMS_PER_POD", 8)
    monkeypatch.setattr(tool.rules, "CONTINGENCY_FACTOR", 1.15)                  # [D22]: the old factor, kept on purpose
    monkeypatch.setattr(tool.rules, "GRANITE_ON_POD", False)
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    eight, six = (0.7 + 8 * 52 / 60) * 1.79, (0.7 + 6 * 52 / 60) * 1.79
    base = max(6 + 1.85 * 9.25, eight + 6 + 1.85 * 9.25, 2 * eight + 6 + 1.85 * 7.5,
               2 * eight + six + 6 + 1.85 * 5.75)
    assert round(base, 2) == 54.53 and round(1.15 * 54.53, 2) == 62.71
    if grouping == "the split":
        with pytest.raises(SystemExit, match="pods of at most 8 arms"):
            init(tool, tmp_path, "1", [units[:4], units[4:]], balance=100.0)
    out = init(tool, tmp_path, "1", [units], balance=62.71)
    plan = tool.mac.load_plan()
    assert out["hosts"] == ["w1-1"] and out["caps"] == [9.25]
    record = plan["funding"][-1]
    assert (record["base_need_usd"], record["need_usd"]) == (54.53, 62.71)
    assert plan["contingency"]["usd"] == round(62.71 - 54.53, 2) == 8.18


def _reading(wave_name: str, runs: list[tuple], phase: str | None = None) -> dict:
    """scripts/gate_b_reading.py's output shape: ``calls`` names the wave the runs belong to; wave 2 comes from the
    wave2 phase, the extension from verdict, the length control from verdict (or extension)."""
    calls = {"wave2": "2", "extension": "ext", "length-control": "lc"}[wave_name]
    phase = phase or {"2": "wave2", "ext": "verdict", "lc": "verdict"}[calls]
    return {"kind": "gate-b reading", "phase": phase, "calls": calls, "runs": [{"arm": a, "seed": s} for a, s in runs]}


def test_waves_after_wave_1_are_exactly_the_readings_runs(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "2")
    e = entries()
    u0, u1 = e["unit"][0], e["unit"][1]
    runs = [(u0["arm"], 1102), (u0["arm"], 1103), (u1["arm"], 1102), (u1["arm"], 1103)]
    jobs = [[arm_job(u0, 1102), arm_job(u0, 1103), arm_job(u1, 1102), arm_job(u1, 1103)]]
    with pytest.raises(SystemExit, match="--reading FILE"):
        init(tool, tmp_path, "2", jobs)
    with pytest.raises(SystemExit, match="exactly the reading output's runs"):
        init(tool, tmp_path, "2", jobs, reading=_reading("wave2", runs[:3]))
    with pytest.raises(SystemExit, match="calls wave"):
        init(tool, tmp_path, "2", jobs, reading=_reading("extension", runs))
    bad = [(u0["arm"], 1104)]
    with pytest.raises(SystemExit, match="unit files at 1102 and 1103"):
        init(tool, tmp_path, "2", [[arm_job(u0, 1104)]], reading=_reading("wave2", bad))
    out = init(tool, tmp_path, "2", jobs, reading=_reading("wave2", runs))
    plan = tool.mac.load_plan()
    assert plan["hosts"][out["hosts"][0]]["cap_hours"] == 5.75
    assert plan["readings"]["2"]["sha256"] == sha(tmp_path / "reading-2.json")
    complete(tool, "2")
    ext = [(e["R"][4]["arm"], 1104), (e["R"][5]["arm"], 1105), (u0["arm"], 1104), (u0["arm"], 1105)]
    ext_jobs = [[arm_job(e["R"][4], 1104), arm_job(e["R"][5], 1105), arm_job(u0, 1104), arm_job(u0, 1105)]]
    wrong = [(e["R"][4]["arm"], 1105), (e["R"][5]["arm"], 1104), (u0["arm"], 1104), (u0["arm"], 1105)]
    with pytest.raises(SystemExit, match="R_4, R_5 at 1100"):
        init(tool, tmp_path, "ext", [[arm_job(e["R"][4], 1105), arm_job(e["R"][5], 1104), arm_job(u0, 1104),
                                      arm_job(u0, 1105)]], reading=_reading("extension", wrong))
    init(tool, tmp_path, "ext", ext_jobs, reading=_reading("extension", ext))
    complete(tool, "ext")
    m1, m2 = e["M"][(u0["unit"], 1)], e["M"][(u0["unit"], 2)]
    lc = [(m1["arm"], 1106), (u0["arm"], 1106), (m2["arm"], 1107), (u0["arm"], 1107)]
    lc_jobs = [[arm_job(m1, 1106), arm_job(u0, 1106), arm_job(m2, 1107), arm_job(u0, 1107)]]
    crossed = [(m1["arm"], 1106), (u0["arm"], 1107), (m2["arm"], 1107), (u0["arm"], 1108)]
    with pytest.raises(SystemExit, match="M_u,1 and u at one seed"):
        init(tool, tmp_path, "lc", [[arm_job(m1, 1106), arm_job(u0, 1107), arm_job(m2, 1107), arm_job(u0, 1108)]],
             reading=_reading("length-control", crossed))
    out = init(tool, tmp_path, "lc", lc_jobs, reading=_reading("length-control", lc))
    assert tool.mac.load_plan()["hosts"][out["hosts"][0]]["cap_hours"] == 5.75


def test_d21_waves_2_ext_and_lc_are_split_into_pods_of_at_most_four_arms(kit, tmp_path, monkeypatch):
    """[D21] (1): wave 2 at m = 4 (8 runs) is planned as two 4-arm pods, the extension with 2 contested units (6 runs)
    as 3 + 3, the length control (4 runs) as one pod; arms dealt in the given order. Caps by hand: 4 arms
    quarter_up(0.7 + 3 x 52/60 + 2.31955) = 5.75 h; 3 arms quarter_up(0.7 + 2 x 52/60 + 2.31955) = 5.0 h."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "2")
    e = entries()
    u = e["unit"]
    w2 = [arm_job(u[k], s) for k in range(4) for s in (1102, 1103)]
    out = init(tool, tmp_path, "2", [w2], reading=_reading("wave2", [(j["arm"], j["seed"]) for j in w2]))
    plan = tool.mac.load_plan()
    assert out["hosts"] == ["w2-1", "w2-2"] and out["caps"] == [5.75, 5.75]
    assert [[(j["arm"], j["seed"]) for j in plan["hosts"][h]["jobs"]] for h in out["hosts"]] == [
        [(j["arm"], j["seed"]) for j in w2[:4]], [(j["arm"], j["seed"]) for j in w2[4:]]]
    complete(tool, "2")
    ext = [arm_job(e["R"][4], 1104), arm_job(e["R"][5], 1105)] + [arm_job(u[k], s) for k in (0, 1) for s in (1104, 1105)]
    reading = _reading("extension", [(j["arm"], j["seed"]) for j in ext])
    with pytest.raises(SystemExit, match="pods of at most 4 arms, dealt evenly"):
        init(tool, tmp_path, "ext", [ext[:4], ext[4:]], reading=reading)            # 4 + 2 is not the split
    out = init(tool, tmp_path, "ext", [ext[:3], ext[3:]], reading=reading)          # the split as given
    plan = tool.mac.load_plan()
    assert out["hosts"] == ["ext-1", "ext-2"] and out["caps"] == [5.0, 5.0]
    assert [len(plan["hosts"][h]["jobs"]) for h in out["hosts"]] == [3, 3]
    complete(tool, "ext")
    m1, m2 = e["M"][(u[0]["unit"], 1)], e["M"][(u[0]["unit"], 2)]
    lc = [arm_job(m1, 1106), arm_job(u[0], 1106), arm_job(m2, 1107), arm_job(u[0], 1107)]
    out = init(tool, tmp_path, "lc", [lc], reading=_reading("length-control", [(j["arm"], j["seed"]) for j in lc]))
    assert out["hosts"] == ["lc-1"] and out["caps"] == [5.75]


def test_d21_the_limit_is_configurable_at_three_arms_per_pod(kit, tmp_path, monkeypatch):
    """[D21]: the value is the user's at the freeze, so another value must plan and fund every wave the same way.
    MAX_ARMS_PER_POD = 3: wave 0a (R_1-R_3) still fits one pod; waves 1 and 2 (8 arms) are 3 + 3 + 2, the extension (6)
    3 + 3, the length control (4) 2 + 2. By hand ([D20]): a 3-arm pod spends 3.3 x 1.79 = 5.907, cap
    quarter_up(0.7 + 2 x 52/60 + 2.31955) = quarter_up(4.75288) = 5.0 h; a 2-arm pod spends (0.7 + 1.73333) x 1.79 =
    4.35567, cap quarter_up(0.7 + 52/60 + 2.31955) = quarter_up(3.88622) = 4.0 h. Terms: 6 + 1.85 x 14 = 31.9;
    16.16967 + 31.9 = 48.06967; 32.33933 + 6 + 1.85 x 10 = 56.83933; 32.33933 + 11.814 + 6 + 1.85 x 8 = 64.95333 ->
    $64.95; [D22] 1.25 x 64.95 = 81.1875 -> $81.19 (contingency $16.24; at [D21]'s 1.15 it was $74.69). Mac Granite is
    set here (the split's arithmetic); the pod route is tested in the [D21] (5) tests."""
    tool = plan_tool(kit, monkeypatch)
    monkeypatch.setattr(tool.rules, "MAX_ARMS_PER_POD", 3)
    monkeypatch.setattr(tool.rules, "GRANITE_ON_POD", False)
    through(tool, tmp_path, "1")                                                   # wave 0a at the boundary, 3 arms
    assert [len(h["jobs"]) for h in tool.mac.load_plan()["hosts"].values() if h["wave"] == "0a"] == [3]
    e = entries()
    u = e["unit"]
    three, two = 3.3 * 1.79, (0.7 + 2 * 52 / 60) * 1.79
    terms = [6 + 1.85 * 14, 2 * three + two + 6 + 1.85 * 14, 4 * three + 2 * two + 6 + 1.85 * 10,
             4 * three + 2 * two + 2 * three + 6 + 1.85 * 8]
    assert [round(t, 5) for t in terms] == [31.9, 48.06967, 56.83933, 64.95333]
    units = [arm_job(x, 1101) for x in u]
    with pytest.raises(SystemExit, match="below the worst path's need"):
        init(tool, tmp_path, "1", [units], balance=81.18)
    out = init(tool, tmp_path, "1", [units], balance=81.19)
    plan = tool.mac.load_plan()
    assert out["hosts"] == ["w1-1", "w1-2", "w1-3"] and out["caps"] == [5.0, 5.0, 4.0]
    assert [[j["arm"] for j in plan["hosts"][h]["jobs"]] for h in out["hosts"]] == [
        [x["arm"] for x in units[k:k + n]] for k, n in ((0, 3), (3, 3), (6, 2))]
    record = plan["funding"][-1]
    assert record["terms_usd"] == pytest.approx(terms)
    assert (record["base_need_usd"], record["need_usd"], plan["contingency"]["usd"]) == (64.95, 81.19, 16.24)
    complete(tool, "1")
    w2 = [arm_job(u[k], s) for k in range(4) for s in (1102, 1103)]
    out = init(tool, tmp_path, "2", [w2], reading=_reading("wave2", [(j["arm"], j["seed"]) for j in w2]))
    assert out["hosts"] == ["w2-1", "w2-2", "w2-3"] and out["caps"] == [5.0, 5.0, 4.0]
    complete(tool, "2")
    ext = [arm_job(e["R"][4], 1104), arm_job(e["R"][5], 1105)] + [arm_job(u[k], s) for k in (0, 1) for s in (1104, 1105)]
    out = init(tool, tmp_path, "ext", [ext], reading=_reading("extension", [(j["arm"], j["seed"]) for j in ext]))
    assert out["hosts"] == ["ext-1", "ext-2"] and out["caps"] == [5.0, 5.0]
    complete(tool, "ext")
    m1, m2 = e["M"][(u[0]["unit"], 1)], e["M"][(u[0]["unit"], 2)]
    lc = [arm_job(m1, 1106), arm_job(u[0], 1106), arm_job(m2, 1107), arm_job(u[0], 1107)]
    reading = _reading("length-control", [(j["arm"], j["seed"]) for j in lc])
    with pytest.raises(SystemExit, match="pods of at most 3 arms, dealt evenly"):
        init(tool, tmp_path, "lc", [lc[:3], lc[3:]], reading=reading)
    out = init(tool, tmp_path, "lc", [lc], reading=reading)
    plan = tool.mac.load_plan()
    assert out["hosts"] == ["lc-1", "lc-2"] and out["caps"] == [4.0, 4.0]
    assert [[(j["arm"], j["seed"]) for j in plan["hosts"][h]["jobs"]] for h in out["hosts"]] == [
        [(m1["arm"], 1106), (u[0]["arm"], 1106)], [(m2["arm"], 1107), (u[0]["arm"], 1107)]]
    assert max(len(h["jobs"]) for h in plan["hosts"].values() if h["wave"] in ("1", "2", "ext", "lc")) == 3


def test_d21_a_pre_job_unit_moved_onto_an_unlaunched_host_with_room_pays_no_new_pod(kit, tmp_path, monkeypatch):
    """[D21] (3) on an existing pod: the extension is 3 + 3; ext-1 crashes its last arm, which defer puts on a new pod
    ext-3 (ext-2 holds 3 + 1 = 4 <= 4 arms, but ext-2 is launched); ext-2 then stops before its job, and its 3 arms fit
    on the unlaunched ext-3 (1 + 3 = 4). By hand ([D20], [D21], [D22]: the default pod route, 78.45 - 62.76): contingency
    $15.69; the crash on a new pod costs (0.7 + 52/60) x 1.79 = $2.8043 -> $12.8857; the unit of 3 arms on ext-3 needs
    no 42 min: 3 x 52/60 x 1.79 = 2.6 x 1.79 = $4.654 -> $8.2317; ext-3's cap quarter_up(0.7 + 3 x 52/60 + 2.31955) =
    5.75 h."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "2")
    e = entries()
    u = e["unit"]
    w2 = [arm_job(u[k], s) for k in range(4) for s in (1102, 1103)]
    init(tool, tmp_path, "2", [w2], reading=_reading("wave2", [(j["arm"], j["seed"]) for j in w2]))
    complete(tool, "2")
    ext = [arm_job(e["R"][4], 1104), arm_job(e["R"][5], 1105)] + [arm_job(u[k], s) for k in (0, 1) for s in (1104, 1105)]
    init(tool, tmp_path, "ext", [ext], reading=_reading("extension", [(j["arm"], j["seed"]) for j in ext]))
    _launch(kit.root, "ext-1")
    _launch(kit.root, "ext-2")
    _done(tool, kit.root, "ext-1", ["complete", "complete", "crashed"])
    assert tool.defer("ext-1")["to"] == "ext-3"
    remaining = tool.mac.load_plan()["contingency"]["remaining_usd"]
    assert remaining == pytest.approx(15.69 - (0.7 + 52 / 60) * 1.79)
    _orchestrate_log(kit.root, "ext-2", "pre-job-failed", "pre-job-stop")
    out = tool.requeue("ext-2")
    plan = tool.mac.load_plan()
    c = plan["contingency"]
    assert out["to"] == "ext-3" and [j["arm"] for j in plan["hosts"]["ext-3"]["jobs"]] == [j["arm"] for j in ext[3:]] + [
        ext[2]["arm"]]                                                              # moved in front
    assert plan["hosts"]["ext-3"]["cap_hours"] == 5.75
    assert c["spent"][-1]["new_pod"] is False and c["spent"][-1]["cost_usd"] == pytest.approx(3 * 52 / 60 * 1.79)
    assert c["remaining_usd"] == pytest.approx(remaining - 4.654) and c["not_rerun"] == []


def test_d21_wave_0a_stays_one_pod_and_needs_room_for_r1_to_r3(kit, tmp_path, monkeypatch):
    """[D21]: wave 0a's first host holds R_1-R_3 (it records the fixture and the reference), so a MAX_ARMS_PER_POD
    below 3 refuses wave 0a rather than splitting it; nothing is written."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    monkeypatch.setattr(tool.rules, "MAX_ARMS_PER_POD", 2)
    e = entries()
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="MAX_ARMS_PER_POD must be at least 3"):
        init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    assert (kit.root / "plan.json").read_bytes() == before


def test_d21_a_host_planned_above_the_limit_is_never_moved_whole(kit, tmp_path, monkeypatch):
    """[D21]: an 8-arm wave-1 host (planned with MAX_ARMS_PER_POD = 8) whose limit is then lowered to 4: a pre-job
    requeue would move 8 arms to one pod, so it refuses before anything is paid or saved (the lead decides)."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    monkeypatch.setattr(tool.rules, "MAX_ARMS_PER_POD", 8)
    init(tool, tmp_path, "1", [[arm_job(u, 1101) for u in entries()["unit"]]], balance=FUNDED)
    monkeypatch.setattr(tool.rules, "MAX_ARMS_PER_POD", 4)
    _launch(kit.root, "w1-1")
    _orchestrate_log(kit.root, "w1-1", "pre-job-failed", "pre-job-stop")
    before, log = (kit.root / "plan.json").read_bytes(), (kit.root / "operator-actions.jsonl").read_bytes()
    with pytest.raises(SystemExit, match="8 arms would move to one pod, more than MAX_ARMS_PER_POD = 4"):
        tool.requeue("w1-1")
    assert (kit.root / "plan.json").read_bytes() == before
    assert (kit.root / "operator-actions.jsonl").read_bytes() == log


def test_d21_only_arms_count_toward_the_limit_and_place_never_overfills_a_pod(kit, tmp_path, monkeypatch):
    """[D21]: the limit counts arms only (arm_count: the anchor, the retrain and the diagnostics are not arms), and
    place, the step every move ends in (defer, pre-job requeue, mismatched requeue), refuses on its own a move that
    would leave a pod with more than MAX_ARMS_PER_POD arms, behind destination and too_many: one arm onto w1-2
    (4 + 1 = 5 > 4) and five arms onto a new pod (5 > 4) refuse and leave the plan as it was; one arm onto a new pod
    (1 <= 4) is placed on w1-3."""
    tool = plan_tool(kit, monkeypatch)
    fx = {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S}
    mixed = tool.rules.default_jobs(["anchor", "retrain", "diagnostics", "arm"], fx)
    assert [tool.rules.arm_count(mixed[:k]) for k in range(5)] == [0, 0, 0, 0, 1]
    through(tool, tmp_path, "1")
    init(tool, tmp_path, "1", [[arm_job(u, 1101) for u in entries()["unit"]]], balance=FUNDED)
    plan = tool.mac.load_plan()
    h = plan["hosts"]["w1-1"]
    before = json.dumps(plan, sort_keys=True)
    with pytest.raises(SystemExit, match="a pod would hold more than 4 arms"):
        tool.place(plan, h, [dict(h["jobs"][0])], "w1-2")
    five = [dict(j) for j in h["jobs"]] + [dict(plan["hosts"]["w1-2"]["jobs"][0])]
    with pytest.raises(SystemExit, match="a pod would hold more than 4 arms"):
        tool.place(plan, h, five, None)
    assert json.dumps(plan, sort_keys=True) == before and "w1-3" not in plan["hosts"]
    assert tool.place(plan, h, [dict(h["jobs"][0])], None) == "w1-3"


def test_d21_a_unit_that_exactly_fits_the_contingency_is_paid_as_one_unit(kit, tmp_path, monkeypatch):
    """[D21] (3) at the boundary: with exactly the unit's cost left, by hand (0.7 + 4 x 52/60) x 1.79 = 4.16667 x 1.79
    = $7.4583, w1-1's pre-job stop is still paid as one unit (one record, new_pod true), not one job at a time, and
    nothing is left; no arm is reported not re-run."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units], balance=FUNDED)
    plan = tool.mac.load_plan()
    plan["contingency"]["remaining_usd"] = (0.7 + 4 * 52 / 60) * 1.79
    tool.mac.save_plan(plan)
    _launch(kit.root, "w1-1")
    _orchestrate_log(kit.root, "w1-1", "pre-job-failed", "pre-job-stop")
    out = tool.requeue("w1-1")
    c = tool.mac.load_plan()["contingency"]
    assert out["to"] == "w1-3" and out["jobs"] == 4
    assert len(c["spent"]) == 1 and c["spent"][0]["new_pod"] is True
    assert [u["arm"] for u in c["spent"][0]["unit"]] == [u["arm"] for u in units[:4]]
    assert c["remaining_usd"] == pytest.approx(0.0, abs=1e-9) and c["not_rerun"] == []


def test_the_readme_states_the_d21_rules():
    """[D21], [D22]: the README gives the limit, the split, the wave-1 need at [D20]'s prices ($72.85 = 1.25 x $58.28 by hand
    in test_wave_1_needs_the_funding_record) and the one-unit payment of a pre-job requeue ((0.7 + 4 x 52/60) x 1.79 =
    $7.4583 -> $7.46 of the $15.69 contingency at the default, [D22])."""
    text = " ".join((KIT / "README.md").read_text().split())
    assert "`gateb_rules.MAX_ARMS_PER_POD` (default 4;" in text
    assert "ceil(n / MAX_ARMS_PER_POD) pods" in text
    assert "it is $72.85 (1.25 x $58.28;" in text and round(1.25 * 58.28, 2) == 72.85 and round(1.15 * 58.28, 2) == 67.02
    assert "A pre-job requeue from wave 1 on is paid from the contingency as one unit" in text
    assert "$7.46 for a 4-arm pod of the $15.69 contingency" in text and round((0.7 + 4 * 52 / 60) * 1.79, 2) == 7.46
    assert 2 * (0.7 + 4 * 52 / 60) * 1.79 <= 15.69 < 3 * (0.7 + 4 * 52 / 60) * 1.79          # two such stops, not three


def test_d21_5_the_granite_cap_follows_the_judge_launchers_rule(kit, monkeypatch):
    """[D21] (5): a pod Granite launch's cap is the judge launcher's (scripts/gate_b_mac_judges/pod/README.md at
    2694bd0): the smallest half hour of at least 30 min + 0.5 s per answer + 15 min, at least 1 h, above 6 h refused;
    each arm adds its 200 greedy answers and every launch the known-answer gate's 200. By hand: 800 answers (the
    parity units, gate off) (1800 + 400 + 900) / 3600 = 0.861 -> 1.0 h (the README's 1.0 h); 1,800: exactly 1.0 h;
    1,801: 1.00014 -> 1.5 h; 6,000 (29 arms + the gate) 1.58333 -> 2.0 h (the README's Gate B 2.0 h); 37,800: exactly
    6.0 h; 37,801 refused. After wave 2 on the worst path: (3 + 8 + 8) x 200 + 200 = 4,000 answers, (1800 + 2000 +
    900) / 3600 = 1.30556 -> 1.5 h; the verdict's own 10 arms: 2,200, 1.05556 -> 1.5 h too; after the extension
    6 x 200 + 200 = 1,400, 0.94444 -> 1.0 h (the floor)."""
    rules = kit("gateb_rules.py")
    assert rules.GRANITE_ON_POD is True and rules.GRANITE_POD_AFTER == ("2", "ext")       # [D22]: the pod route by default
    by_hand = {800: 1.0, 1800: 1.0, 1801: 1.5, 2200: 1.5, 4000: 1.5, 1400: 1.0, 6000: 2.0, 37800: 6.0}
    assert {a: rules.granite_cap_hours(a) for a in by_hand} == by_hand
    assert round((1800 + 4000 * 0.5 + 900) / 3600, 5) == 1.30556 and round((1800 + 1400 * 0.5 + 900) / 3600, 5) == 0.94444
    with pytest.raises(ValueError, match="above 6.0 h"):
        rules.granite_cap_hours(37801)
    for bad in (0, -1, 2.0, True):
        with pytest.raises(ValueError):
            rules.granite_cap_hours(bad)
    assert rules.granite_pod(19) == {"judge": "granite", "arms": 19, "answers": 4000, "kinds": [], "cap_hours": 1.5}
    assert rules.granite_pod(10)["cap_hours"] == 1.5 and rules.granite_pod(6)["answers"] == 1400
    assert rules.launch_pod_spend_usd(rules.granite_pod(19)) == pytest.approx(1.5 * 1.79)          # 2.685
    assert rules.launch_pod_spend_usd({"kinds": ["arm"] * 4}) == pytest.approx((0.7 + 4 * 52 / 60) * 1.79)
    for bad in ("False", 0, 1, None):
        monkeypatch.setattr(rules, "GRANITE_ON_POD", bad)
        with pytest.raises(ValueError, match="GRANITE_ON_POD must be True"):
            rules.granite_on_pod()


def test_d21_5_the_granite_cap_floor_of_one_hour_is_a_rule_of_its_own(kit, monkeypatch):
    """[D21] (5): the judge launcher's cap is never below 1 h. With the launcher's setup and margin, setup + margin
    alone is (1800 + 900) / 3600 = 0.75 h, so one answer already rounds up to 1.0 h ((2700 + 0.5) / 3600 = 0.75014
    -> 1.0 h) and the floor cannot be seen; with setup and margin set to 0 it binds. By hand: 200 answers x 0.5 s =
    100 s = 0.02778 h -> 0.5 h by the half-hour rounding -> 1.0 h by the floor; 7,200 answers = 3,600 s = exactly
    1.0 h; 7,201 = 3,600.5 s = 1.00014 h -> 1.5 h."""
    rules = kit("gateb_rules.py")
    assert rules.granite_cap_hours(1) == 1.0 and round((1800 + 900 + 0.5) / 3600, 5) == 0.75014
    monkeypatch.setattr(rules, "GRANITE_SETUP_UPPER_S", 0)
    monkeypatch.setattr(rules, "GRANITE_MARGIN_S", 0)
    assert round(200 * 0.5 / 3600, 5) == 0.02778 and math.ceil(200 * 0.5 / 3600 * 2) / 2 == 0.5
    assert {a: rules.granite_cap_hours(a) for a in (1, 200, 7200, 7201)} == {1: 1.0, 200: 1.0, 7200: 1.0, 7201: 1.5}


@pytest.mark.parametrize("route", ["mac", "pod"])
def test_d21_5_the_worst_path_need_counts_the_mid_path_granite_launches_only_with_pod_granite(kit, monkeypatch, route):
    """[D21] (5): with pod Granite the worst path is wave 1, wave 2, Granite, extension, Granite, length control; each
    Granite launch's term counts cap x $1.85 and its spend cap x $1.79 enters the later terms. By hand (4-arm pod
    $7.4583, cap 5.75 h; 3-arm pod $5.907, 5.0 h):
      Mac (False): terms 27.275, 42.1917, 54.3333, 58.2848 -> $58.28 x 1.25 ([D22]) = $72.85 (contingency $14.57);
      pod (True): 6 + 1.85 x 11.5 = 27.275; 14.9167 + 27.275 = 42.1917; 29.8333 + 6 + 1.85 x 1.5 = 38.6083;
        29.8333 + 1.5 x 1.79 + 6 + 1.85 x 10 = 29.8333 + 2.685 + 24.5 = 57.0183; 29.8333 + 2.685 + 11.814 + 6 + 1.85 x
        1.0 = 52.1823; 29.8333 + 2.685 + 11.814 + 1.79 + 6 + 1.85 x 5.75 = 62.7598 -> $62.76; x 1.25 ([D22]) = 78.45
        -> $78.45 (contingency $15.69), the lead's "about $78.45" (at [D21]'s 1.15: $72.17, contingency $9.41)."""
    tool = kit("plan_tool.py")
    monkeypatch.setattr(tool.rules, "GRANITE_ON_POD", route == "pod")
    fx = {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S}
    four, three = (0.7 + 4 * 52 / 60) * 1.79, (0.7 + 3 * 52 / 60) * 1.79
    need = tool.worst_path_need({"fixture": fx}, [tool.rules.default_jobs(["arm"] * 4, fx)] * 2)
    assert need["granite_on_pod"] is (route == "pod")
    if route == "mac":
        terms = [6 + 1.85 * 11.5, 2 * four + 6 + 1.85 * 11.5, 4 * four + 6 + 1.85 * 10,
                 4 * four + 2 * three + 6 + 1.85 * 5.75]
        assert need["terms_usd"] == pytest.approx(terms) and need["granite_launches"] == []
        assert (need["base_need_usd"], need["need_usd"], need["contingency_usd"]) == (58.28, 72.85, 14.57)
        return
    g2, gext = 1.5 * 1.79, 1.0 * 1.79
    terms = [6 + 1.85 * 11.5, 2 * four + 6 + 1.85 * 11.5, 4 * four + 6 + 1.85 * 1.5, 4 * four + g2 + 6 + 1.85 * 10,
             4 * four + g2 + 2 * three + 6 + 1.85 * 1.0, 4 * four + g2 + 2 * three + gext + 6 + 1.85 * 5.75]
    assert need["terms_usd"] == pytest.approx(terms)
    assert [round(t, 4) for t in terms] == [27.275, 42.1917, 38.6083, 57.0183, 52.1823, 62.7598]
    assert round(1.25 * round(max(terms), 2), 2) == 78.45 and round(1.15 * round(max(terms), 2), 2) == 72.17
    assert (need["base_need_usd"], need["need_usd"], need["contingency_usd"]) == (62.76, 78.45, 15.69)
    assert [(g["after"], g["arms"], g["answers"], g["cap_hours"]) for g in need["granite_launches"]] == [
        ("2", 19, 4000, 1.5), ("ext", 6, 1400, 1.0)]


def test_d21_5_pod_granite_at_eight_arms_per_pod(kit, monkeypatch):
    """[D21] (5) with the old one-pod split (MAX_ARMS_PER_POD = 8): the Granite launches add the same (1.5 + 1.0) x 1.79
    = $4.475 to the last term. By hand: 8 arms $13.6637, cap 9.25 h; 6 arms $10.561, 7.5 h; 4 arms 5.75 h. Terms:
    23.1125; 36.7762; 27.3273 + 6 + 2.775 = 36.1023; 27.3273 + 2.685 + 6 + 13.875 = 49.8873; 27.3273 + 2.685 + 10.561 +
    6 + 1.85 = 48.4233; 27.3273 + 2.685 + 10.561 + 1.79 + 6 + 10.6375 = 59.0008 -> $59.00; x 1.25 ([D22]) = 73.75
    ($14.75); against $54.53 with Mac Granite (54.5258 + 4.475 = 59.0008)."""
    tool = kit("plan_tool.py")
    monkeypatch.setattr(tool.rules, "MAX_ARMS_PER_POD", 8)
    monkeypatch.setattr(tool.rules, "GRANITE_ON_POD", True)
    fx = {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S}
    eight, six = (0.7 + 8 * 52 / 60) * 1.79, (0.7 + 6 * 52 / 60) * 1.79
    terms = [6 + 1.85 * 9.25, eight + 6 + 1.85 * 9.25, 2 * eight + 6 + 1.85 * 1.5, 2 * eight + 2.685 + 6 + 1.85 * 7.5,
             2 * eight + 2.685 + six + 6 + 1.85, 2 * eight + 2.685 + six + 1.79 + 6 + 1.85 * 5.75]
    need = tool.worst_path_need({"fixture": fx}, [tool.rules.default_jobs(["arm"] * 8, fx)])
    assert need["terms_usd"] == pytest.approx(terms) and round(terms[-1], 4) == 59.0008
    assert (need["base_need_usd"], need["need_usd"], need["contingency_usd"]) == (59.0, 73.75, 14.75)


@pytest.mark.parametrize("route", ["mac", "pod"])
def test_d21_5_init_wave_1_funds_the_route_the_flag_names(kit, tmp_path, monkeypatch, route):
    """[D21] (5), the funding rule: init-wave 1 needs a route's own need (by hand in
    test_d21_5_the_worst_path_need_counts_the_mid_path_granite_launches_only_with_pod_granite); a cent less refuses,
    the need passes, and the record names the route and its launches. [D22] (factor 1.25): $72.85 with Mac Granite and
    $78.45 with pod Granite (the default); the contingency is 72.85 - 58.28 = $14.57 or 78.45 - 62.76 = $15.69."""
    tool = plan_tool(kit, monkeypatch)
    monkeypatch.setattr(tool.rules, "GRANITE_ON_POD", route == "pod")
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    need, base = (78.45, 62.76) if route == "pod" else (72.85, 58.28)
    with pytest.raises(SystemExit, match="below the worst path's need"):
        init(tool, tmp_path, "1", [units], balance=round(need - 0.01, 2))
    out = init(tool, tmp_path, "1", [units], balance=need)
    plan = tool.mac.load_plan()
    record = plan["funding"][-1]
    assert out["hosts"] == ["w1-1", "w1-2"] and out["caps"] == [5.75, 5.75]
    assert (record["need_usd"], record["base_need_usd"], record["granite_on_pod"]) == (need, base, route == "pod")
    assert [g["after"] for g in record["granite_launches"]] == (["2", "ext"] if route == "pod" else [])
    assert plan["contingency"]["usd"] == round(need - base, 2) == (15.69 if route == "pod" else 14.57)


def test_d21_5_a_flag_that_is_not_a_bool_refuses_the_need_and_init_wave_1(kit, tmp_path, monkeypatch):
    """[D21] (5): the need and the funding rule read the flag only through gateb_rules.granite_on_pod, so a string
    "False" (truthy) can never count the pod route by accident: worst_path_need and init-wave 1 refuse, and plan.json
    and operator-actions.jsonl are unchanged (no wave-1 host, no funding record)."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    fx = {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S}
    before = (tool.mac.PLAN.read_text(), (kit.root / "operator-actions.jsonl").read_text())
    for bad in ("False", "True", 0, 1, None):
        monkeypatch.setattr(tool.rules, "GRANITE_ON_POD", bad)
        with pytest.raises(ValueError, match="GRANITE_ON_POD must be True"):
            tool.worst_path_need({"fixture": fx}, [tool.rules.default_jobs(["arm"] * 4, fx)] * 2)
        with pytest.raises(ValueError, match="GRANITE_ON_POD must be True"):
            init(tool, tmp_path, "1", [units], balance=100.0)
        assert (tool.mac.PLAN.read_text(), (kit.root / "operator-actions.jsonl").read_text()) == before


def test_d21_5_the_final_granite_launch_after_the_length_control_does_not_bind(kit, monkeypatch):
    """[D21] (5) names the mid-path launches only; the pod Granite launch after the length control is not a term of
    worst_path_need. Appended by hand it would not change the need. By hand (4-arm pod $7.4583, cap 5.75 h; 3-arm pod
    $5.907, 5.0 h): the spend through the length control 4 x 7.4583 + 1.5 x 1.79 + 2 x 5.907 + 1.0 x 1.79 + 7.4583 =
    29.8333 + 2.685 + 11.814 + 1.79 + 7.4583 = 53.5807. The kit's construction leaves the length control's 4 arms:
    4 x 200 + 200 = 1,000 answers, (1800 + 500 + 900) / 3600 = 0.889 -> 1.0 h, term 53.5807 + 6 + 1.85 = 61.4307. If
    the launch after wave 2 judged only the verdict's 10 arms (2,200 answers, 1.05556 -> 1.5 h, the same spend), 13 are
    left (R_1, wave 1, the length control): 2,800 answers, 1.13889 -> 1.5 h, term 53.5807 + 6 + 2.775 = 62.3557. Both
    are below the length control's 62.7598, so the base stays $62.76 and the need $78.45 ([D22]: 1.25 x 62.76)."""
    rules = kit("gateb_rules.py")
    monkeypatch.setattr(rules, "GRANITE_ON_POD", True)
    four, three = (0.7 + 4 * 52 / 60) * 1.79, (0.7 + 3 * 52 / 60) * 1.79
    p4, p3 = {"kinds": ["arm"] * 4, "cap_hours": 5.75}, {"kinds": ["arm"] * 3, "cap_hours": 5.0}
    spent = 4 * four + 1.5 * 1.79 + 2 * three + 1.0 * 1.79 + four
    assert round(spent, 4) == 53.5807
    for after_wave2, final, final_cap, final_term in ((19, 4, 1.0, 61.4307), (10, 13, 1.5, 62.3557)):
        path = [[p4, p4], [p4, p4], [rules.granite_pod(after_wave2)], [p3, p3], [rules.granite_pod(6)], [p4],
                [rules.granite_pod(final)]]
        need = rules.funding_need_usd(path, rules.CONTINGENCY_FACTOR)
        assert path[-1][0]["cap_hours"] == final_cap and path[2][0]["cap_hours"] == 1.5
        assert round(need["terms_usd"][-1], 4) == round(spent + 6 + 1.85 * final_cap, 4) == final_term
        assert final_term < 62.7598 and round(need["terms_usd"][-2], 4) == 62.7598
        assert (need["base_need_usd"], need["need_usd"], need["contingency_usd"]) == (62.76, 78.45, 15.69)


def test_d21_3_a_unit_and_its_jobs_one_by_one_cost_and_pay_the_same(kit, tmp_path, monkeypatch):
    """[D21] (3) and the lead's 9 Oct question: unit_rerun_cost_usd is the sum of pay_reruns' one-by-one costs (the
    42 min on the first), so pay_unit pays exactly the jobs pay_reruns pays and leaves the same remaining; when the
    contingency is short, the one-by-one rule governs. By hand ($1.79/h; arm 52 min = $1.5513, 42 min = $1.253): a
    4-arm unit on a new pod (0.7 + 4 x 52/60) x 1.79 = $7.4583 = 2.8043 + 3 x 1.5513; on an existing pod 4 x 1.5513 =
    $6.2053; the wave-0b pair on a new pod (0.7 + 0.15 + 2.0) x 1.79 = 2.85 x 1.79 = $5.1015. Remaining $7.4583: all 4 as
    one unit; $7.45: the unit does not fit, one by one 2.8043 + 1.5513 x 2 = $5.907 for 3 arms, $1.543 left, 1 not
    re-run; $2.80: none (the first arm needs $2.8043, and so does each later one, the 42 min not yet paid)."""
    tool = plan_tool(kit, monkeypatch)
    rules = tool.rules
    arm, start = 52 / 60 * 1.79, 0.7 * 1.79
    for kinds, new_pod, by_hand in ((["arm"] * 4, True, (0.7 + 4 * 52 / 60) * 1.79), (["arm"] * 4, False, 4 * arm),
                                    (["retrain", "diagnostics"], True, 2.85 * 1.79), (["arm"], True, start + arm)):
        one_by_one = sum(rules.rerun_cost_usd(k, new_pod and i == 0) for i, k in enumerate(kinds))
        assert rules.unit_rerun_cost_usd(kinds, new_pod) == pytest.approx(by_hand) == pytest.approx(one_by_one)
        if new_pod:
            assert rules.unit_rerun_cost_usd(kinds, True) == pytest.approx(rules.pod_spend_usd(kinds))
    jobs = [{"kind": "arm", "arm": f"a{k}", "seed": 1101} for k in range(4)]
    for remaining, paid_n in (((0.7 + 4 * 52 / 60) * 1.79, 4), (7.45, 3), (2.80, 0)):
        results = {}
        for payer in (tool.pay_unit, tool.pay_reruns):
            plan = {"contingency": {"usd": 9.0, "remaining_usd": remaining, "spent": [], "not_rerun": []}}
            paid = payer(plan, [dict(j) for j in jobs], True, "requeue w1-1", "1")
            c = plan["contingency"]
            results[payer.__name__] = ([j["arm"] for j in paid], c["remaining_usd"], [r["arm"] for r in c["not_rerun"]])
        unit, single = results["pay_unit"], results["pay_reruns"]
        assert unit[0] == single[0] == [j["arm"] for j in jobs[:paid_n]] and unit[2] == single[2]
        assert unit[1] == pytest.approx(single[1], abs=1e-9)
    assert round(7.45 - start - 3 * arm, 4) == 1.543                       # 7.45 - (2.8043 + 2 x 1.5513)


@pytest.mark.parametrize("new_pod", [True, False])
def test_d21_3_the_one_by_one_rule_goes_on_after_a_job_it_cannot_pay(kit, tmp_path, monkeypatch, new_pod):
    """[D21] (3), the documented one-by-one rule when the contingency is short: each job in order is paid if its cost
    fits what is left (the 42 min on the first job PAID), the others are reported not re-run; a refused job does not
    stop the later ones. Arm-only lists cannot tell "go on" from "stop at the first refusal" (every later arm costs the
    same), so this pins it on a synthetic arm then retrain. By hand ($1.79/h): new pod, $2.00 left: the arm (0.7 +
    52/60) x 1.79 = $2.8043 does not fit; the retrain, now the first job paid, carries the 42 min: (0.7 + 0.15) x 1.79
    = $1.5215, $0.4785 left. Existing pod, $1.00 left: the arm 52/60 x 1.79 = $1.5513 does not fit; the retrain 0.15 x
    1.79 = $0.2685, $0.7315 left. The unit (2.8043 + 0.2685 = $3.0728, or 1.5513 + 0.2685 = $1.8198) does not fit
    either, so pay_unit pays the same."""
    tool = plan_tool(kit, monkeypatch)
    remaining, cost, left = (2.00, 0.85 * 1.79, 0.4785) if new_pod else (1.00, 0.15 * 1.79, 0.7315)
    assert round(remaining - cost, 4) == left and round((0.7 + 52 / 60) * 1.79, 4) == 2.8043
    assert round(52 / 60 * 1.79, 4) == 1.5513 and round(0.15 * 1.79, 4) == 0.2685
    jobs = [{"kind": "arm", "arm": "a0", "seed": 1101}, {"kind": "retrain", "arm": None, "seed": 1101}]
    for payer in (tool.pay_reruns, tool.pay_unit):
        plan = {"contingency": {"usd": 9.0, "remaining_usd": remaining, "spent": [], "not_rerun": []}}
        paid = payer(plan, [dict(j) for j in jobs], new_pod, "requeue w1-1", "1")
        c = plan["contingency"]
        assert [j["kind"] for j in paid] == ["retrain"] and [r["arm"] for r in c["not_rerun"]] == ["a0"]
        assert [r["kind"] for r in c["spent"]] == ["retrain"] and c["spent"][0]["cost_usd"] == pytest.approx(cost)
        assert c["remaining_usd"] == pytest.approx(left, abs=1e-9)


def test_the_readme_states_the_d21_granite_route_and_the_payment_rule():
    """[D21] (4), (5) and the one-by-one rule: the README names the flag, its default, the launches and their caps
    (4,000 answers -> 1.5 h, 1,400 -> 1.0 h, by hand in test_d21_5_the_granite_cap_follows_the_judge_launchers_rule)
    and the pod-Granite need ($78.45 = 1.25 x $62.76 since [D22], by hand in the worst-path test)."""
    text = " ".join((KIT / "README.md").read_text().split())
    assert "this even split is the pre-registered one, [D21] (4)" in text
    assert "`gateb_rules.GRANITE_ON_POD` chooses where Gate B's Granite files come from: True (the default since [D22]" in text
    assert "one after the extension (not after wave 1 or the length control)" in text
    assert "4,000 answers -> 1.5 h, 1,400 answers -> 1.0 h" in text
    assert "The wave-1 need is then $78.45 (1.25 x $62.76" in text and round(1.25 * 62.76, 2) == 78.45
    assert "with a $15.69 contingency" in text and round(78.45 - 62.76, 2) == 15.69
    assert "when it does not fit, the one-by-one rule governs" in text
    assert ("each moved job in order is paid if its cost fits what is left (the 42 min on the first job paid), and the "
            "rest are reported not re-run.") in text
    # the judge launcher's cap rule as the kit restates it, and the two prices of a judge launch
    assert ("the smallest half hour of at least 30 min + 0.5 s per answer + 15 min, at least 1 h, at most 6 h)"
            in text) and (1800, 0.5, 900) == (30 * 60, 0.5, 15 * 60)
    assert "Its term counts cap x $1.85 at the guard, and its upper spend in the later terms is cap x $1.79." in text
    # the final pod Granite launch is not a term and does not bind (by hand in test_d21_5_the_final_granite_launch_...)
    assert "The pod Granite launch after the length control (its 4 arms and the gate: 1,000 answers -> 1.0 h) is not a term" in text
    assert "53.5807, + $6 + 1.85 x 1.0 = 61.4307, below 62.7598" in text and "give 62.3557, also below" in text


# ----- B2: the job runner's exact commands ---------------------------------------------------------------------------


def _pod_plan(jobs: list[dict], role: str = "job", recipe: str = S) -> dict:
    groups = [u["unit"] for u in entries()["unit"]]
    return {"engine_sha256": None, "prepared": {"prepared-kt-dolly-olmo2": "m" * 64}, "prepared_name": "prepared-kt-dolly-olmo2",
            "unit_groups": groups, "fixture_compare": {"equal_keys": ["k"], "resume_keys": ["r"]},
            "hosts": {"h-1": {"wave": "0b", "role": role, "base_eval": False, "recipe_path": recipe, "recipe_sha256": None,
                              "sealed_files_sha256": None, "jobs": jobs}}}


def _jobs(kit) -> dict:
    rules = kit("gateb_rules.py")
    fx = {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S}
    r1 = entries()["R"][1]
    return {"anchor": rules.job_record("anchor", None, None, None, None, fx),
            "arm": rules.job_record("arm", r1["arm"], 1101, r1["path"], 33, fx),
            "retrain": rules.job_record("retrain", "a0", 1101, None, 38, fx),
            "diagnostics": rules.job_record("diagnostics", None, 1101, None, None, fx, 0)}


def test_the_dry_run_prints_exactly_the_brief_commands(kit, tmp_path):
    j = _jobs(kit)
    r1 = entries()["R"][1]
    ids = sorted(u["unit"] for u in entries()["unit"])
    groups = "sha256:" + hashlib.sha256(",".join(ids).encode()).hexdigest()   # [D14]: the id list is never compared
    work = tmp_path / "work"
    work.mkdir()
    (work / "plan.json").write_text(json.dumps(_pod_plan([j["retrain"], j["diagnostics"], j["arm"], j["anchor"]])))
    before = sorted(p.name for p in work.iterdir())
    done = subprocess.run([PY, "-B", str(kit.root / "setup" / "job_runner_gateb.py"), "h-1", "--dry-run"], cwd=work,
                          capture_output=True, text=True, env=CLEAN_ENV)
    assert done.returncode == 0, done.stderr[-500:]
    assert sorted(p.name for p in work.iterdir()) == before
    out = json.loads(done.stdout)
    engine = ["venv/bin/python", "-m", "experiments.safety_selection"]
    p, rec = "prepared-kt-dolly-olmo2", S
    expected = [
        [["job-0-make-job", [*engine, "make-job", "run-one", "--prepared", p, "--recipe", rec, "--split", "dev", "--arm", "a0",
                             "--seed", "1101", "--role", "development", "--target", "e1", "--pin-code", "--out",
                             "jobs/retrain-1101-a1.json"]],
         ["job-0-run-one", [*engine, "run-one", "--job", "jobs/retrain-1101-a1.json", "--prepared", p, "--recipe", rec,
                            "--out", "round1/1101-a0-e1-a1", "--registry", "round1/registry.jsonl"]]],
        [["job-1-make-job", [*engine, "make-job", "attributes", "--prepared", p, "--recipe", rec, "--split", "dev",
                             "--seed", "1101", "--role", "development", "--a0-state", "q=round1/1101-a0-e1-a1",
                             "--a0-state", "e1=round1/1101-a0-e1-a1", "--groups", groups,
                             "--anchors", "anchors/anchor_bank.json", "--pin-code", "--out", "jobs/attributes-1101-a1.json"]],
         ["job-1-attributes", [*engine, "attributes", "--job", "jobs/attributes-1101-a1.json", "--prepared", p, "--recipe",
                               rec, "--out", "round1/1101-attributes-a1"]],
         ["job-1-representation", ["venv/bin/python", "scripts/gate_c_representation.py", "--prepared", p, "--recipe", rec,
                                   "--anchors", "anchors/anchor_bank.json", "--groups", groups, "--out", "gatec/representation-a1"]],
         ["job-1-classifier", ["venv/bin/python", "scripts/gate_c_classifier.py", "--prepared", p, "--recipe", rec,
                               "--anchors", "anchors/anchor_bank.json", "--groups", groups, "--out", "gatec/classifier-a1"]]],
        [["job-2-calibrate", [*engine, "calibrate", "--prepared", p, "--recipe", rec, "--arms", r1["arm"], "--edit",
                              "sealed/" + r1["path"], "--seeds", "1101", "--checkpoints", "e1", "--out-root", "round1"]]],
        [["job-3-anchor", ["venv/bin/python", "scripts/make_anchor_answers.py", "--prompts", "anchors/anchor_prompts.json",
                           "--recipe", rec, "--out", "anchor-1"]]]]
    hashed = [[[name, [("sha256:" + hashlib.sha256(v.encode()).hexdigest()) if k and argv[k - 1] == "--groups" else v
                       for k, v in enumerate(argv)]] for name, argv in job["commands"]] for job in out["jobs"]]
    assert hashed == expected
    assert [(job["kind"], job["seed"]) for job in out["jobs"]] == [("retrain", 1101), ("diagnostics", 1101),
                                                                   ("arm", 1101), ("anchor", None)]
    for job in expected:
        for _, argv in job:
            if argv[:3] == engine:
                parsed = _parser().parse_args(argv[3:])
                if argv[3:5] == ["make-job", "run-one"]:
                    assert parsed.bank is None and parsed.pin_code is True        # evaluate_bank null; code pinned
    assert len(ids) == 8 and sum(v == groups for job in hashed for _, argv in job for v in argv) == 3


# ----- B3: the per-job gate on the pod, with a fake heartbeat -----------------------------------------------------


def _pod(kit, tmp_path, jobs: list[dict], role: str = "job", projection: dict | None = None,
         tamper: str | None = None) -> tuple:
    """A pod folder for job_runner_gateb.main with real identities, sealed files and fake engine processes."""
    from experiments.safety_selection.common import code_identity
    from experiments.safety_selection.config import config_sha256, load_recipe
    root = tmp_path / "pod"
    root.mkdir()
    (root / Path(S).parent).mkdir(parents=True)
    shutil.copy(ROOT / REC, root / S)
    (root / "prepared-kt-dolly-olmo2").mkdir()
    (root / "prepared-kt-dolly-olmo2" / "manifest.sha256").write_text("m" * 64 + "\n")
    sealed = {}
    for rel, text in (("scripts/make_anchor_answers.py", "A = 1\n"), ("scripts/gate_c_representation.py", "R = 1\n"),
                      ("scripts/gate_c_classifier.py", "C = 1\n"), ("anchors/anchor_prompts.json", "{}\n"),
                      ("anchors/anchor_bank.json", "{}\n")):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
        sealed[rel] = sha(root / rel)
    for entry in man()["files"]:
        if entry["role"] == "edit":
            (root / "sealed" / entry["path"]).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(SEAL / entry["path"], root / "sealed" / entry["path"])
            sealed["sealed/" + entry["path"]] = entry["sha256"]
    (root / "sealed-files.json").write_text(json.dumps({"files": sealed}))
    if tamper:
        (root / tamper).write_text("changed after sealing\n")
    plan = _pod_plan(jobs, role)
    h = plan["hosts"]["h-1"]
    plan["engine_sha256"] = code_identity()["sha256"]
    h["recipe_sha256"] = config_sha256(load_recipe(str(root / S)))
    h["sealed_files_sha256"] = sha(root / "sealed-files.json")
    (root / "plan.json").write_text(json.dumps(plan))
    (root / "BOOTSTRAP-READY.json").write_text(json.dumps({"ok": True}))
    (root / "cuda-preflight-1").mkdir()
    (root / "cuda-preflight-1" / "verification.json").write_text(json.dumps({"k": 1, "resume": {"r": 2}}))
    (root / "expected-fixture-gateb.json").write_text(json.dumps({"k": 1, "resume": {"r": 2}}))
    projection = projection or {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S, "overhead_s": 1000, "margin_s": 900}
    (root / "PREFLIGHT-DONE.json").write_text(json.dumps({"ok": True, "recipe": S, "folder": "cuda-preflight-1",
                                                          "cap_projection": projection}))
    return root


def _engine_fake(root: Path, fail: dict | None = None, no_complete: set | None = None):
    """A fake subprocess.run: process_receipt steps write what the engine would (a unit's COMPLETE.json, the anchor
    output); ``fail`` maps a receipt name to its exit; the engine's verify passes."""
    ran = []

    def run(args, **kwargs):
        ran.append(list(args))
        if args[:2] == ["python3", "process_receipt.py"]:
            name, argv = args[3], args[5:]
            code = (fail or {}).get(name, 0)
            if code == 0 and name not in (no_complete or set()):
                out = argv[argv.index("--out") + 1] if "--out" in argv else None
                if "calibrate" in argv:
                    arm, seed = argv[argv.index("--arms") + 1], argv[argv.index("--seeds") + 1]
                    unit = root / "round1" / f"{seed}-{arm}-e1-a1"
                    unit.mkdir(parents=True)
                    (unit / "COMPLETE.json").write_text("{}")
                elif "run-one" in argv[:4] or "attributes" in argv[3:4]:
                    (root / out).mkdir(parents=True)
                    (root / out / "COMPLETE.json").write_text(json.dumps({"out": out}))
                elif "make_anchor_answers" in " ".join(argv):
                    (root / out).mkdir(parents=True)
                    (root / out / "record.json").write_text("{}")
            return subprocess.CompletedProcess(args, code, "", "")
        return subprocess.CompletedProcess(args, 0, "", "")
    return run, ran


def _runner(kit, tmp_path, monkeypatch, jobs, remaining=None, heartbeat: str | None = "ok", **pod):
    runner = kit("setup/job_runner_gateb.py")
    root = _pod(kit, tmp_path, jobs, **pod)
    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)
    beat = tmp_path / "heartbeat.json"
    monkeypatch.setattr(runner, "HEARTBEAT", beat)
    if heartbeat == "ok":
        values = list(remaining)

        def left(now):
            return values.pop(0) if len(values) > 1 else values[0]
        monkeypatch.setattr(runner, "remaining", left)
    elif heartbeat == "unreadable":
        beat.write_text("{not json")
    return runner, root


def _statuses(root: Path) -> list[str]:
    return [r["status"] for r in json.loads((root / "JOB-DONE.json").read_text())["jobs"]]


def _receipts(ran: list) -> list[str]:
    return [a[3] for a in ran if a[:2] == ["python3", "process_receipt.py"]]


H = 3600.0


def test_jobs_that_fit_run_in_order_and_are_verified(kit, tmp_path, monkeypatch):
    j = _jobs(kit)
    runner, root = _runner(kit, tmp_path, monkeypatch, [j["arm"], j["retrain"], {**j["diagnostics"], "a0_source": 1}],
                           remaining=[9 * H])
    run, ran = _engine_fake(root)
    monkeypatch.setattr(runner.subprocess, "run", run)
    assert runner.main(["h-1"]) == 0
    done = json.loads((root / "JOB-DONE.json").read_text())
    assert _statuses(root) == ["complete"] * 3 and done["ok"] is True and done["stopped"] is None
    assert _receipts(ran) == ["job-0-calibrate", "job-1-make-job", "job-1-run-one", "job-2-make-job", "job-2-attributes",
                              "job-2-representation", "job-2-classifier"]
    verified = [a[a.index("--run") + 1] for a in ran if "verify" in a]
    arm = entries()["R"][1]["arm"]
    assert verified == [f"round1/1101-{arm}-e1-a1", "round1/1101-a0-e1-a1", "round1/1101-attributes-a1"]
    assert sorted(p.name for p in (root / "job-done").iterdir()) == ["JOB-0.json", "JOB-1.json", "JOB-2.json"]
    assert done["jobs"][0]["complete_sha256"] == sha(root / f"round1/1101-{arm}-e1-a1" / "COMPLETE.json")


def test_a_job_that_does_not_fit_and_every_later_one_are_deferred_in_order(kit, tmp_path, monkeypatch):
    j = _jobs(kit)
    arm = j["arm"]["start_requirement_s"]
    # the first arm fits; the second does not; the retrain after it would fit (1.12 h) but never skips ahead
    remaining = [arm + 1, arm - 1, 2.0 * H]
    second = {**j["arm"], "arm": entries()["R"][2]["arm"], "seed": 1102, "edit": entries()["R"][2]["path"]}
    runner, root = _runner(kit, tmp_path, monkeypatch, [j["arm"], second, {**j["retrain"]}], remaining=remaining)
    run, ran = _engine_fake(root)
    monkeypatch.setattr(runner.subprocess, "run", run)
    assert runner.main(["h-1"]) == 0                                     # deferral is not a failure
    assert _statuses(root) == ["complete", "deferred", "deferred"]
    assert _receipts(ran) == ["job-0-calibrate"]
    deferral = json.loads((root / "deferral.json").read_text())
    assert deferral["first_deferred"] == 1 and deferral["deferred"] == [1, 2]
    assert deferral["requirement_s"] == pytest.approx(arm)


@pytest.mark.parametrize("heartbeat", ["missing", "unreadable"])
def test_a_missing_or_unreadable_heartbeat_stops_the_host(kit, tmp_path, monkeypatch, heartbeat):
    j = _jobs(kit)
    runner, root = _runner(kit, tmp_path, monkeypatch, [j["arm"], j["retrain"]], heartbeat=heartbeat)
    run, ran = _engine_fake(root)
    monkeypatch.setattr(runner.subprocess, "run", run)
    assert runner.main(["h-1"]) == 1
    done = json.loads((root / "JOB-DONE.json").read_text())
    assert done["stopped"] == "heartbeat_unreadable" and done["ok"] is False
    assert _statuses(root) == ["not_started", "not_started"] and _receipts(ran) == []
    assert not (root / "deferral.json").exists()


@pytest.mark.parametrize("hours, runs", [(3.6, False), (3.7, True)])            # [D13]: straddling 3.65 h
def test_the_retrain_and_its_diagnostics_start_together_or_not_at_all(kit, tmp_path, monkeypatch, hours, runs):
    j = _jobs(kit)
    runner, root = _runner(kit, tmp_path, monkeypatch, [j["retrain"], j["diagnostics"]],
                           remaining=[hours * H, hours * H - 0.12 * H])
    run, ran = _engine_fake(root)
    monkeypatch.setattr(runner.subprocess, "run", run)
    runner.main(["h-1"])
    if runs:
        assert _statuses(root) == ["complete", "complete"]
    else:                                     # 3.6 h > the retrain's own 1.12 h, but < 0.15 h + 3.5 h
        assert _statuses(root) == ["deferred", "deferred"] and _receipts(ran) == []


def test_a_retrain_that_overruns_strands_its_diagnostics(kit, tmp_path, monkeypatch):
    j = _jobs(kit)
    runner, root = _runner(kit, tmp_path, monkeypatch, [j["retrain"], j["diagnostics"]], remaining=[3.7 * H, 3.4 * H])
    run, ran = _engine_fake(root)
    monkeypatch.setattr(runner.subprocess, "run", run)
    assert runner.main(["h-1"]) == 0
    assert _statuses(root) == ["complete", "deferred"]


@pytest.mark.parametrize("why", ["exit", "no COMPLETE.json"])
def test_a_crash_stops_the_host_and_later_jobs_do_not_start(kit, tmp_path, monkeypatch, why):
    j = _jobs(kit)
    second = {**j["arm"], "arm": entries()["R"][2]["arm"], "seed": 1102, "edit": entries()["R"][2]["path"]}
    runner, root = _runner(kit, tmp_path, monkeypatch, [j["arm"], second], remaining=[9 * H])
    run, ran = _engine_fake(root, fail={"job-0-calibrate": 1} if why == "exit" else None,
                            no_complete={"job-0-calibrate"} if why != "exit" else None)
    monkeypatch.setattr(runner.subprocess, "run", run)
    assert runner.main(["h-1"]) == 1
    done = json.loads((root / "JOB-DONE.json").read_text())
    assert _statuses(root) == ["crashed", "not_started"] and done["stopped"] == "crashed" and done["ok"] is False
    assert _receipts(ran) == ["job-0-calibrate"]


@pytest.mark.parametrize("tamper", ["scripts/gate_c_classifier.py", "anchors/anchor_bank.json"])
def test_a_script_or_file_that_differs_from_sealed_files_refuses_its_job(kit, tmp_path, monkeypatch, tamper):
    j = _jobs(kit)
    runner = kit("setup/job_runner_gateb.py")
    root = _pod(kit, tmp_path, [j["retrain"], j["diagnostics"]])
    sealed = json.loads((root / "sealed-files.json").read_text())["files"]
    assert runner.sealed_check(j["diagnostics"], sealed, root) == []
    (root / tamper).write_text("changed after sealing\n")
    assert runner.sealed_check(j["diagnostics"], sealed, root) == [tamper]
    assert runner.sealed_check(j["retrain"], sealed, root) == []
    with pytest.raises(AssertionError, match="sealed file"):          # the start-up check refuses the whole host
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.delenv("HF_TOKEN", raising=False)
        runner.preflight_checks(json.loads((root / "plan.json").read_text()), "h-1",
                                json.loads((root / "PREFLIGHT-DONE.json").read_text()), root)


def test_an_edit_file_must_hash_to_its_arm(kit, tmp_path):
    j = _jobs(kit)
    runner = kit("setup/job_runner_gateb.py")
    root = _pod(kit, tmp_path, [j["arm"]])
    sealed = json.loads((root / "sealed-files.json").read_text())["files"]
    assert runner.sealed_check(j["arm"], sealed, root) == []
    other = {**j["arm"], "arm": entries()["R"][2]["arm"]}                 # the R_1 file under R_2's arm
    assert runner.sealed_check(other, sealed, root) == [f"sealed/{j['arm']['edit']} (its arm)"]


def test_a_mismatched_sealed_file_mid_host_stops_without_running(kit, tmp_path, monkeypatch):
    j = _jobs(kit)
    runner, root = _runner(kit, tmp_path, monkeypatch, [j["retrain"], j["diagnostics"]], remaining=[9 * H])
    monkeypatch.setattr(runner, "preflight_checks", lambda *a: json.loads((root / "sealed-files.json").read_text())["files"])
    (root / "scripts/gate_c_representation.py").write_text("changed\n")
    run, ran = _engine_fake(root)
    monkeypatch.setattr(runner.subprocess, "run", run)
    assert runner.main(["h-1"]) == 1
    done = json.loads((root / "JOB-DONE.json").read_text())
    assert _statuses(root) == ["complete", "not_started"] and done["stopped"] == "sealed_file_mismatch"
    assert not any("gate_c" in " ".join(a) for a in ran)


def test_the_runner_refuses_a_token_base_eval_and_a_second_run(kit, tmp_path, monkeypatch):
    j = _jobs(kit)
    runner, root = _runner(kit, tmp_path, monkeypatch, [j["arm"]], remaining=[9 * H])
    monkeypatch.setenv("HF_TOKEN", fake_token())
    with pytest.raises(AssertionError, match="a token is present"):
        runner.main(["h-1"])
    monkeypatch.delenv("HF_TOKEN")
    (root / "JOB-DONE.json").write_text("{}")
    with pytest.raises(AssertionError, match="already ran"):
        runner.main(["h-1"])
    plan = json.loads((root / "plan.json").read_text())
    plan["hosts"]["h-1"]["base_eval"] = True
    (root / "plan.json").write_text(json.dumps(plan))
    with pytest.raises(AssertionError, match="base_eval"):
        runner.main(["h-1"])


# ----- defer and record-done ----------------------------------------------------------------------------------


def _done(tool, kit_root: Path, host: str, statuses: list[str], units: dict | None = None) -> None:
    """A pulled JOB-DONE.json for ``host`` with the given statuses (units: index -> unit folder, sealed)."""
    plan = tool.mac.load_plan()
    tree = kit_root / "retrieved" / host / "tree"
    tree.mkdir(parents=True, exist_ok=True)
    records = []
    for i, (job, status) in enumerate(zip(plan["hosts"][host]["jobs"], statuses)):
        rec = {"index": i, "kind": job["kind"], "arm": job["arm"], "seed": job["seed"], "status": status}
        if status == "complete":
            unit = (units or {}).get(i, f"round1/unit-{i}")
            (tree / unit).mkdir(parents=True, exist_ok=True)
            (tree / unit / "COMPLETE.json").write_text(json.dumps({"files": {}, "i": i, "host": host}))
            rec.update(unit=unit, complete_sha256=sha(tree / unit / "COMPLETE.json"))
        records.append(rec)
    (tree / "JOB-DONE.json").write_text(json.dumps({"host": host, "jobs": records}))
    tool.record_done(host)


def _launch(kit_root: Path, host: str) -> None:
    (kit_root / "hosts" / host).mkdir(parents=True, exist_ok=True)
    (kit_root / "hosts" / host / "pod.json").write_text("{}")


def test_record_done_maps_the_pulled_statuses_and_checks_the_seals(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    init(tool, tmp_path, "anchor", [[{"kind": "anchor"}]])
    with pytest.raises(SystemExit, match="no pulled JOB-DONE"):
        tool.record_done("anchor-1")
    _done(tool, kit.root, "anchor-1", ["complete"], {0: "anchor-1"})
    job = tool.mac.load_plan()["hosts"]["anchor-1"]["jobs"][0]
    assert job["status"] == "complete" and job["unit"] == "anchor-1"
    tree = kit.root / "retrieved" / "anchor-1" / "tree"
    (tree / "anchor-1" / "COMPLETE.json").write_text("{}")
    with pytest.raises(SystemExit, match="differs"):
        tool.record_done("anchor-1")
    done = json.loads((tree / "JOB-DONE.json").read_text())                 # the anchor job writes no COMPLETE.json
    done["jobs"][0]["complete_sha256"] = None
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    assert tool.record_done("anchor-1")["statuses"] == ["complete"]


def test_record_done_refuses_a_complete_arm_without_its_seal(kit, tmp_path, monkeypatch):
    tool, _ = _wave1(kit, tmp_path, monkeypatch)
    tree = kit.root / "retrieved" / "w1-1" / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    assert done["jobs"][0]["status"] == "complete" and done["jobs"][0]["complete_sha256"]
    done["jobs"][0].pop("complete_sha256")
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    with pytest.raises(SystemExit, match="complete without a complete_sha256"):
        tool.record_done("w1-1")


def test_defer_moves_open_jobs_to_the_front_of_the_next_unlaunched_host(kit, tmp_path, monkeypatch):
    """With room on the unlaunched host ([D21]: MAX_ARMS_PER_POD = 7 here, so 4 + 3 moved arms fit; wave 1 is still
    4 + 4, since ceil(8 / 7) = 2)."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    monkeypatch.setattr(tool.rules, "MAX_ARMS_PER_POD", 7)
    e = entries()
    units = [arm_job(u, 1101) for u in e["unit"]]
    init(tool, tmp_path, "1", [units[:4], units[4:]], balance=FUNDED)
    _launch(kit.root, "w1-1")
    with pytest.raises(SystemExit, match="record-done first"):
        tool.defer("w1-1")
    _done(tool, kit.root, "w1-1", ["complete", "crashed", "not_started", "not_started"])
    before = tool.mac.load_plan()["hosts"]["w1-1"]
    out = tool.defer("w1-1")
    plan = tool.mac.load_plan()
    assert out["to"] == "w1-2" and plan["hosts"]["w1-1"] == before            # the launched host is never edited
    moved = [(j["arm"], j["seed"], j["status"]) for j in plan["hosts"]["w1-2"]["jobs"]]
    assert moved == [(u["arm"], 1101, "planned") for u in units[1:4]] + [(u["arm"], 1101, "planned") for u in units[4:]]
    assert plan["hosts"]["w1-2"]["cap_hours"] == quarter_up(0.7 + 6 * 52 / 60 + (E1_UPPER_S + TRAINING_S * 33 / 38 + 3700) / 3600)
    assert plan["deferrals"][0]["from_indices"] == [1, 2, 3]
    with pytest.raises(SystemExit, match="already deferred"):
        tool.defer("w1-1")


def test_d21_defer_never_fills_an_unlaunched_host_beyond_four_arms(kit, tmp_path, monkeypatch):
    """[D21]: w1-2 already holds 4 arms, so w1-1's 3 open jobs go to a new host w1-3 (3 arms, cap by hand
    quarter_up(0.7 + 2 x 52/60 + 2.31955) = quarter_up(4.75288) = 5.0 h), and w1-2 is unchanged; one crashed job is
    paid with the new pod's 42 min: (0.7 + 52/60) x 1.79 = $2.8043."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units], balance=FUNDED)
    _launch(kit.root, "w1-1")
    _done(tool, kit.root, "w1-1", ["complete", "crashed", "not_started", "not_started"])
    before, remaining = tool.mac.load_plan()["hosts"]["w1-2"], tool.mac.load_plan()["contingency"]["remaining_usd"]
    out = tool.defer("w1-1")
    plan = tool.mac.load_plan()
    assert out["to"] == "w1-3" and plan["hosts"]["w1-2"] == before
    assert [j["arm"] for j in plan["hosts"]["w1-3"]["jobs"]] == [u["arm"] for u in units[1:4]]
    assert plan["hosts"]["w1-3"]["cap_hours"] == quarter_up(0.7 + 2 * 52 / 60 + (E1_UPPER_S + TRAINING_S * 33 / 38
                                                                                 + 3700) / 3600) == 5.0
    assert plan["contingency"]["remaining_usd"] == pytest.approx(remaining - (0.7 + 52 / 60) * 1.79)
    assert max(len(h["jobs"]) for h in plan["hosts"].values() if h["wave"] == "1") == 4


def test_defer_creates_a_new_host_when_every_other_is_launched(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _launch(kit.root, "w0a-1")
    _done(tool, kit.root, "w0a-1", ["complete", "deferred", "deferred"])
    out = tool.defer("w0a-1")
    plan = tool.mac.load_plan()
    new = plan["hosts"][out["to"]]
    assert out["to"] == "w0a-2" and new["role"] == "job" and new["wave"] == "0a" and new["base_eval"] is False
    assert [j["arm"] for j in new["jobs"]] == [e["R"][2]["arm"], e["R"][3]["arm"]]
    assert new["cap_hours"] == quarter_up(0.7 + 52 / 60 + (E1_UPPER_S + TRAINING_S + 3700) / 3600) == 4.0
    assert new["guard_usd"] == pytest.approx(6 + 4.0 * 1.85) and new["sealed_files_sha256"] == plan["hosts"]["w0a-1"]["sealed_files_sha256"]


def test_defer_never_moves_jobs_into_another_launched_host(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units[:4], units[4:]], balance=FUNDED)
    _launch(kit.root, "w1-1")
    _launch(kit.root, "w1-2")                                     # launched, still running: never edited
    _done(tool, kit.root, "w1-1", ["complete", "complete", "deferred", "deferred"])
    before = tool.mac.load_plan()["hosts"]["w1-2"]
    out = tool.defer("w1-1")
    plan = tool.mac.load_plan()
    assert out["to"] == "w1-3" and plan["hosts"]["w1-2"] == before
    assert [j["arm"] for j in plan["hosts"]["w1-3"]["jobs"]] == [units[2]["arm"], units[3]["arm"]]


def test_a_stranded_retrain_is_requeued_in_front_of_its_diagnostics(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0b")
    init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                 {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])
    _launch(kit.root, "w0b-1")
    _done(tool, kit.root, "w0b-1", ["complete", "deferred"], {0: "round1/1101-a0-e1-a1"})
    stranded = tool.mac.load_plan()["hosts"]["w0b-1"]["jobs"][0]["complete_sha256"]
    out = tool.defer("w0b-1")
    plan = tool.mac.load_plan()
    jobs = plan["hosts"][out["to"]]["jobs"]
    assert [(j["kind"], j["arm"], j["seed"]) for j in jobs] == [("retrain", "a0", 1101), ("diagnostics", None, 1101)]
    assert jobs[0]["reason"] == "stranded-retrain" and jobs[0]["stranded_complete_sha256"] == stranded
    assert jobs[1]["a0_source"] == 0 and plan["hosts"][out["to"]]["cap_hours"] == 4.5
    assert plan["deferrals"][0]["stranded_retrain"] == {"from_index": 0, "complete_sha256": stranded}
    actions = [json.loads(x) for x in (kit.root / "operator-actions.jsonl").read_text().splitlines()]
    assert [a for a in actions if a["action"] == "stranded-retrain"][0]["complete_sha256"] == stranded


@pytest.mark.parametrize("statuses", [["complete", "crashed"], ["complete", "not_started"]])
def test_no_other_complete_job_is_requeued(kit, tmp_path, monkeypatch, statuses):
    """The exception covers a deferred diagnostics only: a crashed (or not started) diagnostics whose retrain is
    complete cannot move without its retrain, so defer refuses (no state moves between pods)."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0b")
    init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                 {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])
    _launch(kit.root, "w0b-1")
    _done(tool, kit.root, "w0b-1", statuses)
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="without its retrain"):
        tool.defer("w0b-1")
    assert (kit.root / "plan.json").read_bytes() == before


def test_a_crashed_retrain_moves_with_its_diagnostics(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0b")
    init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                 {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])
    _launch(kit.root, "w0b-1")
    _done(tool, kit.root, "w0b-1", ["crashed", "not_started"])
    out = tool.defer("w0b-1")
    jobs = tool.mac.load_plan()["hosts"][out["to"]]["jobs"]
    assert [j["kind"] for j in jobs] == ["retrain", "diagnostics"] and jobs[1]["a0_source"] == 0
    assert "reason" not in jobs[0]


def test_a_complete_arm_in_a_pulled_tree_is_never_moved_by_defer(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _launch(kit.root, "w0a-1")
    _done(tool, kit.root, "w0a-1", ["complete", "crashed", "not_started"])
    _complete_unit(kit.root, "w0a-1", e["R"][2]["arm"], 1102)               # crashed per JOB-DONE, yet sealed
    with pytest.raises(SystemExit, match="a complete attempt exists"):
        tool.defer("w0a-1")


# ----- B5: the environment checks, through the shared field set ---------------------------------------------------


def _orchestrate(kit, monkeypatch, wave: str = "1", reference: bool = True):
    orch = kit("orchestrate.py")
    plan = {"hosts": {"h": {"wave": wave, "role": "job", "jobs": [], "stage": "gateb"}}, "reference": None}
    lock = "1" * 64
    fields = orch.mac.compared_fields(_environment(), lock, _policy())
    if reference:
        plan["reference"] = {"bootstrap": {"lock_sha256": lock, "pip_version": "24.0", "gpu": "NVIDIA A100-SXM4-80GB",
                                           "cuda_runtime": "12.8"}, "fields": fields, "guard": GUARD}
    orch.mac.save_plan(plan)
    events = []
    monkeypatch.setattr(orch, "log", lambda host, event, **f: events.append((event, f)))
    return orch, events, lock


READY = {"lock_sha256": "1" * 64, "pip_version": "24.0", "gpu": "NVIDIA A100-SXM4-80GB", "cuda_runtime": "12.8"}
PRE = {"guard": GUARD}                       # PREFLIGHT-DONE.json's guard record ([D17] 4), equal to the reference's


@pytest.mark.parametrize("field", ["lock_sha256", "gpu", "cuda_runtime"])
def test_a_bootstrap_difference_stops_the_pod(kit, monkeypatch, field):
    orch, events, _ = _orchestrate(kit, monkeypatch)
    orch.bootstrap_check("h", READY)
    with pytest.raises(SystemExit, match="differs from the reference at bootstrap"):
        orch.bootstrap_check("h", {**READY, field: "other"})
    mismatch = [f for e, f in events if e == "environment-mismatch"]
    assert mismatch == [{"point": "bootstrap", "fields": [field], "missing": []}]
    assert "other" not in json.dumps(events)                               # field names only, never values
    with pytest.raises(SystemExit, match="differs from the reference"):
        orch.bootstrap_check("h", {k: v for k, v in READY.items() if k != field})     # a missing field refuses


def test_a_pip_version_difference_is_logged_and_never_stops(kit, monkeypatch):
    orch, events, _ = _orchestrate(kit, monkeypatch)
    result = orch.bootstrap_check("h", {**READY, "pip_version": "25.1"})
    assert result["stop"] is False and result["logged"] == ["pip_version"]
    assert [e for e, _ in events] == ["pip-version-differs"]
    records = [json.loads(x) for x in (kit.root / "hosts" / "h" / "environment-checks.jsonl").read_text().splitlines()]
    assert records[-1]["logged"] == ["pip_version"] and records[-1]["strict"] is True


THIRTEEN = {"python": {"python": "3.12.0 other"}, "machine": {"machine": "aarch64"}, "device": {"device": "cpu"},
            "packages": {"packages": {"torch": "2.9.0"}}, "deterministic_algorithms": {"deterministic_algorithms": False},
            "safety_selection_numeric": {"safety_selection_numeric": {"x": True}},
            "gpu": {"name": "NVIDIA H100"}, "capability": {"capability": "9.0"}, "cuda_runtime": {"torch_cuda_runtime": "12.4"},
            "cudnn": {"cudnn": 1}, "cuda_settings": {"settings": {"cudnn_benchmark": True}},
            "cuda_env": {"env": {"CUBLAS_WORKSPACE_CONFIG": None}}}


@pytest.mark.parametrize("field", sorted(THIRTEEN) + ["lock_sha256", "policy"])
def test_every_compared_field_stops_the_pod_after_the_preflight(kit, monkeypatch, field):
    orch, events, lock = _orchestrate(kit, monkeypatch)
    verification = {"environment": _environment(), "policy_identity": _policy()}
    orch.preflight_check("h", verification, {"lock_sha256": lock}, PRE)
    if field == "lock_sha256":
        ready = {"lock_sha256": "2" * 64}
    else:
        ready = {"lock_sha256": lock}
    if field in THIRTEEN:
        verification = {**verification, "environment": _environment(**THIRTEEN[field])}
    if field == "policy":
        verification = {**verification, "policy_identity": _policy(attn_implementation="eager")}
    with pytest.raises(SystemExit, match="at preflight"):
        orch.preflight_check("h", verification, ready, PRE)
    assert [f["fields"] for e, f in events if e == "environment-mismatch"] == [[field]]


@pytest.mark.parametrize("change", ["driver", "snapshot", "trainable_parameters", "trainable_token_ids", "platform"])
def test_driver_snapshot_and_trainable_differences_pass(kit, monkeypatch, change):
    orch, events, lock = _orchestrate(kit, monkeypatch)
    verification = {"environment": _environment(), "policy_identity": _policy()}
    if change == "driver":
        verification["environment"] = _environment(driver="NVRM another")
    elif change == "platform":
        verification["environment"] = _environment(platform="Linux-other")
    else:
        verification["policy_identity"] = _policy(**{change: "differs"})
    assert orch.preflight_check("h", verification, {"lock_sha256": lock}, PRE)["stop"] is False
    assert not [e for e, _ in events if e == "environment-mismatch"]


def test_a_missing_compared_field_refuses_after_the_preflight(kit, monkeypatch):
    orch, events, lock = _orchestrate(kit, monkeypatch)
    env = _environment()
    del env["cuda"]["cudnn"]
    with pytest.raises(SystemExit, match="at preflight"):
        orch.preflight_check("h", {"environment": env, "policy_identity": _policy()}, {"lock_sha256": lock}, PRE)
    assert [f["missing"] for e, f in events if e == "environment-mismatch"] == [["cudnn"]]
    with pytest.raises(SystemExit, match="at preflight"):                 # a missing policy block refuses too
        orch.preflight_check("h", {"environment": _environment()}, {"lock_sha256": lock}, PRE)


@pytest.mark.parametrize("wave, stops", [("anchor", False), ("0a", False), ("0b", True), ("1", True)])
def test_before_the_reference_only_the_anchor_and_wave_0a_pods_log(kit, monkeypatch, wave, stops):
    orch, events, lock = _orchestrate(kit, monkeypatch, wave=wave, reference=False)
    ready = {**READY, "gpu": "other GPU"}
    if stops:
        with pytest.raises(SystemExit, match="no environment reference yet"):
            orch.bootstrap_check("h", ready)
    else:
        result = orch.bootstrap_check("h", ready)
        assert "gpu" in result["differ"] and [e for e, _ in events if e == "environment-provisional"]
        orch.preflight_check("h", {"environment": _environment(cudnn=7), "policy_identity": _policy()}, ready)
        assert not [e for e, _ in events if e == "environment-mismatch"]


def test_an_environment_mismatch_stops_the_pod_through_the_pre_job_path(kit, monkeypatch):
    orch, events, _ = _orchestrate(kit, monkeypatch)
    calls = []
    monkeypatch.setattr(orch, "tool", lambda *a, **k: calls.append(a) or subprocess.CompletedProcess(a, 1 if a[0] == "ssh" else 0, "", ""))
    for name in ("wait_ssh", "check", "bootstrap"):
        monkeypatch.setattr(orch, name, lambda host: None)
    monkeypatch.setattr(orch, "wait_file", lambda *a, **k: {})
    monkeypatch.setattr(orch, "fetch", lambda host, remote, local: {**READY, "gpu": "NVIDIA H100"})
    monkeypatch.setattr(orch, "preflight", lambda host: pytest.fail("no preflight after a bootstrap mismatch"))
    with pytest.raises(SystemExit, match="differs from the reference at bootstrap"):
        orch.after_create("h")
    assert calls[1:] == [("extend-cap", "h", "120"), ("stop", "h")]
    assert [f["step"] for e, f in events if e == "pre-job-failed"] == ["bootstrap-check"]


def test_set_reference_stores_the_wave_0a_fields(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    folder = kit.root / "hosts" / "w0a-1"
    folder.mkdir(parents=True)
    (folder / "bootstrap-ready.json").write_text(json.dumps({**READY, "ok": True}))
    (folder / "verification.json").write_text(json.dumps({"environment": _environment(), "policy_identity": _policy()}))
    with pytest.raises(SystemExit, match="wave 0a's first host"):
        tool.set_reference("anchor-1")
    tool.set_reference("w0a-1")
    ref = tool.mac.load_plan()["reference"]
    reading = tool.mac.reading_module()
    assert ref["fields"] == reading.compared_fields(_environment(), READY["lock_sha256"], _policy())
    assert ref["bootstrap"] == READY and "snapshot" not in ref["fields"]["policy"]
    with pytest.raises(SystemExit, match="already set"):
        tool.set_reference("w0a-1")


def test_compared_fields_agrees_with_environment_of_on_the_13_fields(kit, tmp_path):
    """The kit imports the reading's one field set (B5 [V20]); on one synthetic assets.json and lock it gives
    environment_of's 13 fields with the same names and values."""
    spec = importlib.util.spec_from_file_location("fpr_for_kit_test", ROOT / "scripts" / "family_probe_reading.py")
    fpr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fpr)
    run = tmp_path / "run"
    unit = run / "round1" / "u"
    unit.mkdir(parents=True)
    (unit / "assets.json").write_text(json.dumps({"environment": _environment()}))
    (run / "environment-linux.lock").write_text("setuptools==78.1.0\n")
    match, _ = fpr.environment_of(unit)
    import gateb_mac
    fields = gateb_mac.compared_fields(_environment(), sha(run / "environment-linux.lock"), None)
    assert fields == match and len(match) == 13


# ----- B3: the Mac-side cap gate --------------------------------------------------------------------------------


def test_the_mac_cap_gate_uses_the_first_jobs_requirement_without_a_second_margin(kit, monkeypatch):
    orch = kit("orchestrate.py")
    j = _jobs(kit)
    orch.mac.save_plan({"hosts": {"h": {"jobs": [j["retrain"], j["diagnostics"]]}}})
    now = dt.datetime(2026, 10, 8, 10, tzinfo=dt.timezone.utc)
    projection = {"e1_upper_s": E1_UPPER_S, "training_s": TRAINING_S, "overhead_s": 1000, "margin_s": 900,
                  "projected_job_upper_s": 99 * H}
    for hours, ok in ((3.64, False), (3.66, True)):
        stop = (now + dt.timedelta(hours=hours)).isoformat()
        gate = orch.cap_gate("h", {"governing_stop_utc": stop, "cap_projection": projection}, now)
        assert gate["ok"] is ok and gate["requirement_s"] == pytest.approx(3.65 * H)
    assert orch.cap_gate("h", {"governing_stop_utc": None, "cap_projection": projection}, now)["ok"] is False
    assert orch.cap_gate("h", {"governing_stop_utc": (now + dt.timedelta(hours=9)).isoformat()}, now)["ok"] is False


# ----- B5, B6: the static bootstrap and the generated worker bootstrap ---------------------------------------------


FAKE_PYTHON = """#!/bin/bash
echo "$0 $*" >> "$GATEB_FAKE_LOG"
if [ "$1" = "-m" ] && [ "$2" = "venv" ]; then mkdir -p "$3/bin"; cp "$0" "$3/bin/python"; exit 0; fi
if [ "$1" = "-m" ] && [ "$2" = "pip" ] && [ "$3" = "freeze" ]; then printf '%b' "$GATEB_FAKE_FREEZE"; exit 0; fi
if [ "$1" = "-m" ] && [ "$2" = "pip" ] && [ "$3" = "--version" ]; then echo "pip 24.0 from x (python 3.12)"; exit 0; fi
if [ "$1" = "-" ]; then cat > /dev/null; exit 0; fi
exit 0
"""


def _bootstrap(kit, tmp_path, freeze: str, pin: str | None = None) -> tuple:
    run = tmp_path / "run"
    run.mkdir()
    shutil.copy(kit.root / "setup" / "constraints.txt", run / "constraints.txt")
    (run / "requirements.lock").write_text("torch==2.8.0\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python").write_text(FAKE_PYTHON)
    (bin_dir / "python").chmod(0o755)
    log = tmp_path / "python.log"
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "GATEB_RUN_ROOT": str(run), "GATEB_FAKE_LOG": str(log),
           "GATEB_FAKE_FREEZE": freeze}
    if pin:
        env["GATEB_PIP_PIN"] = pin
    done = subprocess.run(["bash", str(kit.root / "setup" / "bootstrap_hr.sh")], capture_output=True, text=True, env=env)
    calls = [line.split(" ", 1)[1] for line in log.read_text().splitlines()] if log.exists() else []
    return done, calls, run


GOOD_FREEZE = "numpy==2.2.6\\nsetuptools==78.1.0\\ntorch==2.8.0\\n"


@pytest.mark.parametrize("pin", [None, "24.0"])
def test_the_static_bootstrap_constrains_both_installs_and_pins_pip_only_when_set(kit, tmp_path, pin):
    rules = kit("gateb_rules.py")
    assert (kit.root / "setup" / "constraints.txt").read_text() == f"setuptools=={rules.SETUPTOOLS_PIN}\n" \
        == "setuptools==78.1.0\n" and rules.PIP_PIN is None
    done, calls, run = _bootstrap(kit, tmp_path, GOOD_FREEZE, pin)
    assert done.returncode == 0, done.stderr[-400:]
    installs = [c for c in calls if c.startswith("-m pip install")]
    constraint = f"-c {run}/constraints.txt"
    main = [c for c in installs if "pip==" not in c]
    assert len(main) == 2 and all(c.endswith(constraint) for c in main)
    assert main[0].startswith("-m pip install torch==2.8.0") and main[1].startswith(f"-m pip install -r {run}/requirements.lock")
    pins = [i for i, c in enumerate(installs) if "pip==" in c]
    assert pins == ([] if pin is None else [0]) and (pin is None or installs[0] == f"-m pip install pip=={pin}")
    assert (run / "environment-linux.lock").read_text() == GOOD_FREEZE.replace("\\n", "\n")
    assert calls.index(next(c for c in calls if c == "-m pip freeze")) < calls.index("-")
    text = (kit.root / "setup" / "bootstrap_hr.sh").read_text()
    assert text.count('-c "$CONSTRAINTS"') == 2 and 'CONSTRAINTS="$RUN/constraints.txt"' in text
    assert 'RUN="${GATEB_RUN_ROOT:-/workspace/attribution-headroom}"' in text


@pytest.mark.parametrize("freeze, why", [("setuptools==78.1.0\\nwheel==0.45.1\\n", "wheel line"),
                                         ("setuptools==78.1.0\\nWheel @ file:///x\\n", "wheel line"),
                                         ("setuptools==80.0.0\\n", "setuptools line"),
                                         ("numpy==2.2.6\\n", "setuptools line")])
def test_the_static_bootstrap_refuses_a_wheel_line_or_another_setuptools(kit, tmp_path, freeze, why):
    done, calls, _ = _bootstrap(kit, tmp_path, freeze)
    assert done.returncode == 3 and why in done.stderr and "-" not in calls


def _worker_bootstrap(kit, pin=None, bundle="bundle-gateb-gateb.tar.gz", bundle_sha="b" * 64, code="c" * 64):
    pack = kit("pack_setup.py")
    return pack, pack.worker_bootstrap("gateb", bundle, bundle_sha, code, {"prepared-kt-dolly-olmo2": "m" * 64}, pin)


def _heredocs(text: str) -> dict:
    return dict(re.findall(r"venv/bin/python - <<'(PY\d)'\n(.*?)\n\1\n", text, flags=re.S))


def test_the_worker_bootstrap_starts_process_2_after_the_extraction(kit):
    _, text = _worker_bootstrap(kit)
    docs = _heredocs(text)
    assert sorted(docs) == ["PY1", "PY2"] and text.index("\nPY1\n") < text.index("<<'PY2'")
    assert "extractall" in docs["PY1"] and "extractall" not in docs["PY2"]
    lines = docs["PY2"].splitlines()
    assert lines[:2] == ["import importlib", "importlib.invalidate_caches()"]
    assert all(not l.startswith(("from experiments", "import torch")) for l in lines[:2])
    assert lines.index("from experiments.safety_selection.common import code_identity") > 1
    assert "GATEB_PIP_PIN" not in text
    assert "export GATEB_PIP_PIN=24.0\n" in _worker_bootstrap(kit, pin="24.0")[1]
    assert text.index("setup_and_fetch_gateb.sh") < text.index("<<'PY1'")


def _bundle_dir(tmp_path: Path) -> tuple:
    """A synthetic pod folder with a bundle: one engine-like file, a prepared manifest and one sealed file."""
    src = tmp_path / "src"
    (src / "prepared-kt-dolly-olmo2").mkdir(parents=True)
    (src / "prepared-kt-dolly-olmo2" / "manifest.sha256").write_text("m" * 64 + "\n")
    (src / "sealed").mkdir()
    (src / "sealed" / "x.json").write_text("{}\n")
    (src / "code.py").write_text("X = 1\n")
    files = {"code.py": sha(src / "code.py"), "prepared-kt-dolly-olmo2/manifest.sha256":
             sha(src / "prepared-kt-dolly-olmo2" / "manifest.sha256"), "sealed/x.json": sha(src / "sealed" / "x.json")}
    pod = tmp_path / "pod"
    pod.mkdir()
    bundle = pod / "bundle-gateb-gateb.tar.gz"
    with tarfile.open(bundle, "w:gz") as t:
        for name in files:
            t.add(src / name, arcname=name)
        for name, payload in (("bundle-manifest.json", {"files": files}), ("sealed-files.json", {"files": {"sealed/x.json": files["sealed/x.json"]}})):
            data = json.dumps(payload).encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    return pod, bundle


FAKE_TORCH = """class cuda:
    @staticmethod
    def get_device_name(i):
        return 'NVIDIA A100-SXM4-80GB'
class version:
    cuda = '12.8'
"""


@pytest.mark.parametrize("lock, ok", [("numpy==2.2.6\nsetuptools==78.1.0\n", True), ("setuptools==78.1.0\nwheel==0.45.1\n", False),
                                      ("setuptools==78.1.0\nwheel @ file:///x\n", False),      # [D14]
                                      ("setuptools==78.1.0\nWheel@file:///x\n", False), ("setuptools==78.1.0\nwheel>=0.45\n", False),
                                      ("setuptools==78.1.0\nwheel\n", False), ("setuptools==78.1.0\nwheelhouse==1.0\n", True),
                                      ("setuptools==75.0.0\n", False)])
def test_the_worker_bootstraps_two_processes_run_on_a_synthetic_bundle(kit, tmp_path, lock, ok):
    pod, bundle = _bundle_dir(tmp_path)
    _, text = _worker_bootstrap(kit, bundle=bundle.name, bundle_sha=sha(bundle), code="c" * 64)
    docs = _heredocs(text)
    one = subprocess.run([PY, "-"], input=docs["PY1"], cwd=pod, capture_output=True, text=True, env=CLEAN_ENV)
    assert one.returncode == 0, one.stderr[-400:]
    assert json.loads((pod / "BUNDLE-CHECKED.json").read_text())["ok"] is True and (pod / "code.py").is_file()
    # process 2 in a fresh interpreter: a fake engine and torch on the pod's path, the lock, pip from this venv
    (pod / "experiments" / "safety_selection").mkdir(parents=True)
    (pod / "experiments" / "__init__.py").write_text("")
    (pod / "experiments" / "safety_selection" / "__init__.py").write_text("")
    (pod / "experiments" / "safety_selection" / "common.py").write_text(
        "def code_identity():\n    return {'sha256': '" + "c" * 64 + "'}\n")
    (pod / "torch.py").write_text(FAKE_TORCH)
    (pod / "pip").mkdir()                                                  # this venv has no pip: a fake one
    (pod / "pip" / "__init__.py").write_text("")
    (pod / "pip" / "__main__.py").write_text("print('pip 24.0 from fake (python 3.11)')\n")
    (pod / "environment-linux.lock").write_text(lock)
    two = subprocess.run([PY, "-"], input=docs["PY2"], cwd=pod, capture_output=True, text=True,
                         env={**CLEAN_ENV, "PYTHONPATH": str(pod)})
    if ok:
        assert two.returncode == 0, two.stderr[-400:]
        ready = json.loads((pod / "BOOTSTRAP-READY.json").read_text())
        assert ready["lock_sha256"] == hashlib.sha256(lock.encode()).hexdigest() and ready["gpu"] == "NVIDIA A100-SXM4-80GB"
        assert ready["cuda_runtime"] == "12.8" and re.fullmatch(r"\d+(\.\d+)+", ready["pip_version"])
    else:
        assert two.returncode != 0 and not (pod / "BOOTSTRAP-READY.json").exists()
    (pod / "BUNDLE-CHECKED.json").unlink()                                 # process 2 never runs on an unchecked bundle
    again = subprocess.run([PY, "-"], input=docs["PY2"], cwd=pod, capture_output=True, text=True,
                           env={**CLEAN_ENV, "PYTHONPATH": str(pod)})
    assert again.returncode != 0


def test_process_1_refuses_a_changed_bundle_file(kit, tmp_path):
    pod, bundle = _bundle_dir(tmp_path)
    _, text = _worker_bootstrap(kit, bundle=bundle.name, bundle_sha="0" * 64)
    one = subprocess.run([PY, "-"], input=_heredocs(text)["PY1"], cwd=pod, capture_output=True, text=True, env=CLEAN_ENV)
    assert one.returncode != 0 and "bundle" in one.stderr and not (pod / "code.py").exists()


# ----- B7: the pack's sealed files ---------------------------------------------------------------------------------


def _pins(pack, kit, monkeypatch, stage: str) -> None:
    """Pin synthetic prompt and anchor files and the stage's scripts in the copy's rules (the real ones are not here)."""
    repo = kit.repo
    prompts = repo / "tmp" / "gate-b-anchors" / "anchor_prompts.json"
    prompts.parent.mkdir(parents=True, exist_ok=True)
    prompts.write_text("{}\n")
    monkeypatch.setattr(pack.rules, "ANCHOR_PROMPTS_PIN", {"path": "tmp/gate-b-anchors/anchor_prompts.json",
                                                           "sha256": sha(prompts)})
    bank = repo / "tmp" / "gate-b-anchors" / "anchor_bank.json"
    bank.write_text("{}\n")
    monkeypatch.setattr(pack.rules, "ANCHOR_FILE_PIN", {"path": "tmp/gate-b-anchors/anchor_bank.json", "sha256": sha(bank)})
    pins = {}
    for script in pack.rules.STAGE_SCRIPTS["gateb"]:
        (repo / script).parent.mkdir(parents=True, exist_ok=True)
        (repo / script).write_text(f"# {script}\n")
        pins[script] = sha(repo / script)
    monkeypatch.setattr(pack.rules, "PINNED_SCRIPTS", pins)


@pytest.mark.parametrize("stage", ["anchor", "gateb"])
def test_the_pack_lists_every_sealed_file_by_its_pin(kit, monkeypatch, stage):
    pack = kit("pack_setup.py")
    _pins(pack, kit, monkeypatch, stage)
    files, pins = pack.sealed_files(stage)
    assert len([n for n in pins if n.startswith("sealed/")]) == 32                     # MAN and its 31 files
    assert pins["sealed/MANIFEST.json"] == pack.rules.MAN_SHA256
    assert ("anchors/anchor_bank.json" in pins) is (stage == "gateb")
    assert sorted(n for n in pins if n.startswith("scripts/")) == sorted(pack.rules.STAGE_SCRIPTS[stage])
    assert all(sha(files[n]) == d for n, d in pins.items())


@pytest.mark.parametrize("change", ["a sealed edit file", "MAN", "the prompt list", "a pinned script", "an unpinned script",
                                    "the anchor file unpinned"])
def test_a_sealed_files_mismatch_refuses_packing(kit, monkeypatch, change):
    pack = kit("pack_setup.py")
    _pins(pack, kit, monkeypatch, "gateb")
    repo = kit.repo
    if change == "a sealed edit file":
        (repo / SEAL_REL / "edits" / "R_d2.json").write_text("{}")
    elif change == "MAN":
        (repo / SEAL_REL / "MANIFEST.json").write_text("{}")
    elif change == "the prompt list":
        (repo / "tmp" / "gate-b-anchors" / "anchor_prompts.json").write_text("[]\n")
    elif change == "a pinned script":
        (repo / "scripts" / "gate_c_classifier.py").write_text("changed\n")
    elif change == "an unpinned script":
        monkeypatch.setitem(pack.rules.PINNED_SCRIPTS, "scripts/make_gateb_recipe.py", None)
    else:
        monkeypatch.setattr(pack.rules, "ANCHOR_FILE_PIN", {"path": None, "sha256": None})
    with pytest.raises(SystemExit, match="MANIFEST|pins"):
        pack.sealed_files("gateb")
    assert not list((kit.root / "setup").glob("packed-*"))


def test_the_pack_refuses_before_writing_anything(kit, monkeypatch):
    pack = kit("pack_setup.py")
    with pytest.raises(SystemExit, match="give the stage"):
        pack.main([])
    (kit.root / "setup" / "constraints.txt").write_text("setuptools==78.1.0\nwheel==0.45.1\n")
    with pytest.raises(SystemExit, match="exactly the line setuptools==78.1.0"):
        pack.main(["anchor"])
    (kit.root / "setup" / "constraints.txt").write_text("setuptools==78.1.0\n")
    _pins(pack, kit, monkeypatch, "anchor")
    with pytest.raises(SystemExit, match="process_receipt.py is missing"):               # [D9] B-6
        pack.main(["anchor"])
    (kit.repo / S).unlink()
    with pytest.raises(SystemExit, match="does not exist"):
        pack.main(["gateb"])
    assert not list((kit.root / "setup").glob("packed-*"))


# ----- B8: pull items and the backup's dry runs --------------------------------------------------------------------


def test_the_pull_items_cover_the_gate_b_outputs(kit):
    host = kit("host.py")
    items = host.PULL_ITEMS.split()
    for item in ("round1", "anchor-*", "gatec", "deferral.json", "job-*", "jobs", "BUNDLE-CHECKED.json",
                 "pip-version.txt", "BOOTSTRAP-READY.json", "JOB-DONE.json", "environment-linux.lock"):
        assert item in items
    assert host.name_of.__doc__ and "attribution-gateb-" in (kit.root / "host.py").read_text()
    assert "gated" not in host.PULL_ITEMS and not hasattr(host, "gated_download")


def _backup_kit(tool, kit, tmp_path) -> None:
    """Two hosts that both hold 1101-a0-e1-a1 (a stranded retrain re-run on a second pod), records and analyses."""
    through(tool, tmp_path, "0b")
    init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                 {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])
    _launch(kit.root, "w0b-1")
    _done(tool, kit.root, "w0b-1", ["complete", "deferred"], {0: "round1/1101-a0-e1-a1"})
    tool.defer("w0b-1")
    _launch(kit.root, "w0b-2")
    _done(tool, kit.root, "w0b-2", ["complete", "complete"], {0: "round1/1101-a0-e1-a1", 1: "round1/1101-attributes-a1"})
    for host in ("w0b-1", "w0b-2"):
        folder = kit.root / "hosts" / host
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "finished.json").write_text("{}")
        (folder / "environment-checks.jsonl").write_text(json.dumps({"point": "bootstrap"}) + "\n")
        (kit.root / f"hosts-full-{host}.log").write_text("log\n")
    for name in ("budget-checks.jsonl", "launch-w0b.log", "finisher-1.log"):
        (kit.root / name).write_text("{}\n")
    (kit.root / "judges").mkdir()
    (kit.root / "judges" / "granite-w0b-2.json").write_text(json.dumps({"kind": "gate-b judge file"}))
    (kit.root / "gate_b_rankings.json").write_text("{}")
    prepared = kit.repo / "tmp" / "kt-prepared" / "prepared-kt-dolly-olmo2"
    prepared.mkdir(parents=True)
    (prepared / "manifest.json").write_text("{}")
    (prepared / "manifest.sha256").write_text(sha(prepared / "manifest.json") + "\n")
    plan = tool.mac.load_plan()
    plan["prepared"] = {"prepared-kt-dolly-olmo2": sha(prepared / "manifest.json")}
    tool.mac.save_plan(plan)


def _backup(kit, capsys, *extra) -> tuple:
    backup = kit("backup_records_gateb.py")
    code = backup.main(["--dry-run", "--tag", "backup-2026-10-09-gate-b", *extra])
    out = capsys.readouterr().out
    summary = json.loads(out[out.index("\n{") + 1:])
    return code, summary, out, backup


def test_the_backup_keys_units_by_host_and_stages_the_gate_b_records(kit, tmp_path, monkeypatch, capsys):
    tool = plan_tool(kit, monkeypatch)
    _backup_kit(tool, kit, tmp_path)
    code, summary, out, backup = _backup(kit, capsys, "--host", "w0b-1", "--host", "w0b-2")
    assert summary["missing"] == [] and code == 0, summary["missing"]
    assert {"w0b-1/round1/1101-a0-e1-a1", "w0b-2/round1/1101-a0-e1-a1"} <= set(summary["units"])   # both, never merged
    for staged in ("units/w0b-1/round1/1101-a0-e1-a1/COMPLETE.json", "units/w0b-2/round1/1101-a0-e1-a1/COMPLETE.json",
                   "analyses/operator-actions.jsonl", "analyses/judges/granite-w0b-2.json", "analyses/gate_b_rankings.json",
                   "records/w0b-1/environment-checks.jsonl", "analyses/setup/packed-gateb/setup-receipt.json"):
        assert f"  {staged}  <- " in out, staged
    assert "second" not in json.dumps(summary).replace("seconds", "")
    assert summary["jobs"]["w0b-1"][1]["status"] == "deferred"
    assert summary["kit_code"]["runkit"] == "runkit/gate-b-olmo" and summary["kit_code"]["staged_absent_or_different"] == []
    with pytest.raises(SystemExit):
        backup.parse(["--dry-run"])                                                    # no default tag


def test_the_backup_requires_every_complete_job_sealed_and_operator_actions(kit, tmp_path, monkeypatch, capsys):
    tool = plan_tool(kit, monkeypatch)
    _backup_kit(tool, kit, tmp_path)
    shutil.rmtree(kit.root / "retrieved" / "w0b-2" / "tree" / "round1" / "1101-attributes-a1")
    (kit.root / "operator-actions.jsonl").unlink()
    code, summary, _, _ = _backup(kit, capsys, "--host", "w0b-1", "--host", "w0b-2")
    assert code == 2
    assert "w0b-2: job 1 is complete in plan.json but its unit is not sealed in the pulled tree" in summary["missing"]
    assert "operator-actions.jsonl" in summary["missing"]
    assert not [m for m in summary["missing"] if "w0b-1: job 1" in m]                 # the deferred job is only listed


def test_the_backup_stages_the_used_sealed_edit_files(kit, tmp_path, monkeypatch, capsys):
    tool = plan_tool(kit, monkeypatch)
    _backup_kit(tool, kit, tmp_path)
    e = entries()
    plan = tool.mac.load_plan()
    rules = tool.rules
    jobs = [rules.job_record("arm", e["R"][d]["arm"], 1100 + d, e["R"][d]["path"], 33, plan["fixture"]) for d in (1, 2, 3)]
    for job, status in zip(jobs, ("complete", "crashed", "deferred")):
        job["status"] = status
    jobs[0].update(unit=f"round1/1101-{e['R'][1]['arm']}-e1-a1")
    unit = kit.root / "retrieved" / "w0b-2" / "tree" / jobs[0]["unit"]
    unit.mkdir(parents=True)
    (unit / "COMPLETE.json").write_text("{}")
    jobs[0]["complete_sha256"] = sha(unit / "COMPLETE.json")
    plan["hosts"]["w0b-2"]["jobs"] += jobs
    tool.mac.save_plan(plan)
    code, summary, out, _ = _backup(kit, capsys, "--host", "w0b-1", "--host", "w0b-2")
    assert code == 0, summary["missing"]
    assert "  edits/R_d1.json  <- " in out and "  edits/R_d2.json  <- " in out and "edits/R_d3.json" not in out
    (kit.repo / SEAL_REL / "edits" / "R_d2.json").write_text("{}")
    code, summary, _, _ = _backup(kit, capsys, "--host", "w0b-1", "--host", "w0b-2")
    assert code == 2 and "sealed edit file edits/R_d2.json (missing or differs from MAN)" in summary["missing"]


# ----- launch, finisher and the kit's contents -----------------------------------------------------------------


def test_launch_refuses_base_eval_a_host_without_jobs_and_a_wrong_cap(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    init(tool, tmp_path, "anchor", [[{"kind": "anchor"}]])
    launch = kit("launch.py")
    plan = tool.mac.load_plan()
    launch.check_hosts(plan, ["anchor-1"])
    for change, match in (({"base_eval": True}, "base_eval"), ({"jobs": []}, "no jobs"), ({"cap_hours": 1.25}, "cap")):
        bad = json.loads(json.dumps(plan))
        bad["hosts"]["anchor-1"].update(change)
        with pytest.raises(SystemExit, match=match):
            launch.check_hosts(bad, ["anchor-1"])
    with pytest.raises(SystemExit, match="not a host"):
        launch.check_hosts(plan, ["w9-1"])


def test_launch_gives_no_child_a_token_and_runs_the_guard_at_the_cap(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    init(tool, tmp_path, "anchor", [[{"kind": "anchor"}]])
    launch = kit("launch.py")
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    runs, popens = [], []

    def run(args, **kwargs):
        runs.append((args, kwargs))
        if args[1:3] == ["host.py", "create"]:
            folder = kit.root / "hosts" / args[3]
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "pod.json").write_text("{}")
        return subprocess.CompletedProcess(args, 0, "", "")

    assert launch.main(["anchor-1"], run=run, popen=lambda a, **k: popens.append((a, k)), sleep=lambda s: None) == 0
    assert [a[1:3] for a, _ in runs] == [["host.py", "reconcile"], ["budget.py", "check"], ["host.py", "create"]]
    assert runs[1][0][3:] == ["1.5", "1.85"]                                             # [D20]: the planning price
    for args, kwargs in runs + popens:
        assert "HF_TOKEN" not in kwargs["env"] and token not in json.dumps(kwargs["env"]) and token not in args


def test_a_budget_guard_refusal_creates_no_pod(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    init(tool, tmp_path, "anchor", [[{"kind": "anchor"}]])
    launch = kit("launch.py")
    runs, popens = [], []

    def run(args, **kwargs):
        runs.append(args[1:3])
        refused = args[1:3] == ["budget.py", "check"]
        return subprocess.CompletedProcess(args, 3 if refused else 0, "refused: balance" if refused else "", "")

    class Paused(Exception):
        pass

    def sleep(seconds):                                    # launch retries until its deadline; stop after one round
        raise Paused

    with pytest.raises(Paused):
        launch.main(["anchor-1"], run=run, popen=lambda a, **k: popens.append(a), sleep=sleep)
    assert ["host.py", "create"] not in runs and runs[:2] == [["host.py", "reconcile"], ["budget.py", "check"]]
    assert popens == [] and not (kit.root / "hosts" / "anchor-1" / "pod.json").exists()


@pytest.mark.parametrize("second_refused", [False, True])
def test_d21_each_pod_of_a_split_wave_passes_the_guard_at_its_own_cap(kit, tmp_path, monkeypatch, second_refused):
    """[D21] (1): the two 4-arm wave-1 pods are launched together (launch.py w1-1 w1-2) and each passes the budget guard
    at its own cap before its create, so they run in parallel only when the guard allows. By hand: a 4-arm cap is
    quarter_up(0.7 + 3 x 52/60 + 2.31955) = quarter_up(5.61955) = 5.75 h, checked at $1.85/h ([D20]). When the guard
    refuses w1-2, w1-1 is still created and w1-2 is not."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    init(tool, tmp_path, "1", [[arm_job(u, 1101) for u in entries()["unit"]]], balance=FUNDED)
    launch = kit("launch.py")
    runs, popens = [], []

    def run(args, **kwargs):
        runs.append(args[1:])
        refused = second_refused and args[1:3] == ["budget.py", "check"] and runs[-2][-1] == "w1-2"
        if args[1:3] == ["host.py", "create"]:
            (kit.root / "hosts" / args[3]).mkdir(parents=True, exist_ok=True)
            (kit.root / "hosts" / args[3] / "pod.json").write_text("{}")
        return subprocess.CompletedProcess(args, 3 if refused else 0, "refused" if refused else "", "")

    class Paused(Exception):
        pass

    def sleep(seconds):                                    # stop at the end of the first round
        if seconds == launch.ROUND_PAUSE:
            raise Paused

    if second_refused:
        with pytest.raises(Paused):
            launch.main(["w1-1", "w1-2"], run=run, popen=lambda a, **k: popens.append(a), sleep=sleep)
    else:
        assert launch.main(["w1-1", "w1-2"], run=run, popen=lambda a, **k: popens.append(a), sleep=sleep) == 0
    created = [] if second_refused else [["host.py", "create", "w1-2"]]
    assert runs == [["host.py", "reconcile", "w1-1"], ["budget.py", "check", "5.75", "1.85"], ["host.py", "create", "w1-1"],
                    ["host.py", "reconcile", "w1-2"], ["budget.py", "check", "5.75", "1.85"]] + created
    assert (kit.root / "hosts" / "w1-1" / "pod.json").exists()
    assert (kit.root / "hosts" / "w1-2" / "pod.json").exists() is not second_refused
    assert len(popens) == (1 if second_refused else 2)


def test_d21_each_pod_of_a_launch_is_guarded_at_its_own_cap_when_the_caps_differ(kit, tmp_path, monkeypatch):
    """[D21] (1): at MAX_ARMS_PER_POD = 3 wave 1 is 3 + 3 + 2 arms; launch.py w1-1 w1-2 w1-3 runs the budget guard for
    each pod at that pod's own cap, never at another pod's. By hand: 3 arms quarter_up(0.7 + 2 x 52/60 + 2.31955) =
    quarter_up(4.75288) = 5.0 h; 2 arms quarter_up(0.7 + 52/60 + 2.31955) = quarter_up(3.88622) = 4.0 h; at $1.85/h.
    (The need at this limit is $86.79 with pod Granite, the default since [D22] (1.25 x $69.43; Mac Granite $81.19,
    test_d21_the_limit_is_configurable_at_three_arms_per_pod), so $100 funds it.)"""
    tool = plan_tool(kit, monkeypatch)
    monkeypatch.setattr(tool.rules, "MAX_ARMS_PER_POD", 3)
    through(tool, tmp_path, "1")
    init(tool, tmp_path, "1", [[arm_job(u, 1101) for u in entries()["unit"]]], balance=100.0)
    launch = kit("launch.py")
    runs = []

    def run(args, **kwargs):
        runs.append(args[1:])
        if args[1:3] == ["host.py", "create"]:
            (kit.root / "hosts" / args[3]).mkdir(parents=True, exist_ok=True)
            (kit.root / "hosts" / args[3] / "pod.json").write_text("{}")
        return subprocess.CompletedProcess(args, 0, "", "")

    assert launch.main(["w1-1", "w1-2", "w1-3"], run=run, popen=lambda a, **k: None, sleep=lambda s: None) == 0
    assert [r[2:] for r in runs if r[:2] == ["budget.py", "check"]] == [["5.0", "1.85"], ["5.0", "1.85"], ["4.0", "1.85"]]


def test_d21_the_guard_counts_a_launchs_earlier_pod_in_flight_and_running(kit, monkeypatch):
    """[D21] (1): the pods of one launch run in parallel only when the guard allows, so the guard for w1-2 counts w1-1,
    both while w1-1's create is in flight (create-intent.json without pod.json: its cap at $1.85/h) and once w1-1 runs
    (the account's RUNNING pod until its recorded cap, at its own price). By hand, a $25.00 balance and 4-arm pods
    (cap 5.75 h): with nothing counted, 25 - 5.75 x 1.85 = 25 - 10.6375 = 14.3625 >= 6 (allowed); with w1-1 in flight,
    committed round(5.75 x 1.85, 2) = 10.64 and 25 - 10.64 - 10.6375 = 3.7225 < 6 (refused); with w1-1 running at
    $1.79/h, committed round(5.75 x 1.79, 2) = round(10.2925, 2) = 10.29 and 25 - 10.29 - 10.6375 = 4.0725 < 6
    (refused)."""
    budget = kit("budget.py")
    pods = []

    def call(method, url, payload=None):
        if url.endswith("/graphql"):
            return {"data": {"myself": {"clientBalance": 25.0, "currentSpendPerHr": 0.0}}}
        return list(pods)

    monkeypatch.setattr(budget, "call", call)
    monkeypatch.setattr(sys, "argv", ["budget.py", "check", "5.75", "1.85"])
    assert budget.main() == 0                                                     # nothing else counted
    cap = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5.75)).isoformat()
    folder = kit.root / "hosts" / "w1-1"
    folder.mkdir(parents=True)
    (folder / "create-intent.json").write_text(json.dumps({"cap_stop_utc": cap}))
    assert budget.projection()["committed_upper_usd"] == 10.64
    assert budget.main() == 3                                                     # w1-1's create in flight
    (folder / "pod.json").write_text(json.dumps({"id": "pod-synthetic-1", "cap_stop_utc": cap}))
    pods.append({"id": "pod-synthetic-1", "name": "w1-1", "desiredStatus": "RUNNING", "costPerHr": 1.79})
    assert budget.projection()["committed_upper_usd"] == 10.29
    assert budget.main() == 3                                                     # w1-1 running


def test_the_finisher_checks_units_outside_round1_and_anchor_hosts(kit, monkeypatch):
    fin = kit("finisher.py")
    (kit.root / "plan.json").write_text(json.dumps({"hosts": {"anchor-1": {"role": "anchor", "cap_hours": 1.5}}}))
    tree = kit.root / "retrieved" / "anchor-1" / "tree"
    (tree / "anchor-1").mkdir(parents=True)
    (tree / "anchor-1" / "record.json").write_text("{}")
    unit = tree / "round1" / "1101-attributes-a1"
    unit.mkdir(parents=True)
    (unit / "groups.json").write_text("{}")
    (unit / "COMPLETE.json").write_text(json.dumps({"files": {"groups.json": "0" * 64}}))
    (tree / "JOB-DONE.json").write_text(json.dumps({"ok": True}))
    results = fin.light_check("anchor-1", tree)
    assert results == {"round1/1101-attributes-a1": {"exit": 1, "tail": "bad ['groups.json']; states left on the pod: 0"}}
    calls = []
    monkeypatch.setattr(fin, "tool", lambda *a: calls.append(a) or subprocess.CompletedProcess(a, 0, "stopped", ""))
    monkeypatch.setattr(fin, "unpack", lambda h: tree)
    monkeypatch.setattr(fin, "log", lambda **f: None)
    (kit.root / "hosts" / "anchor-1").mkdir(parents=True)
    fin.finish("anchor-1", {"exit_code": 0})
    assert json.loads((kit.root / "hosts" / "anchor-1" / "finished.json").read_text())["status"] == "review-needed-stopped"
    assert calls[-2:] == [("extend-cap", "anchor-1", "120"), ("stop", "anchor-1")]


def test_the_kit_holds_its_scripts_only_compiles_and_holds_no_secret(tmp_path):
    names = {p.relative_to(KIT).as_posix() for p in KIT.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    assert names == {"README.md", "account.py", "backup_records_gateb.py", "budget.py", "finisher.py", "gateb_mac.py",
                     "gateb_rules.py", "host.py", "launch.py", "orchestrate.py", "pack_setup.py", "plan_tool.py", "probes.py",
                     "secret_scan.py", "status.py", "setup/bootstrap_hr.sh", "setup/constraints.txt",
                     "setup/download_models_gateb.py", "setup/extend_cap.py", "setup/job_runner_gateb.py",
                     "setup/preflight_gateb.py", "setup/setup_and_fetch_gateb.sh"}
    for name in names:
        if name.endswith(".py"):
            py_compile.compile(str(KIT / name), cfile=str(tmp_path / "x.pyc"), doraise=True)
    sys.path.insert(0, str(KIT))
    try:
        import secret_scan
        assert secret_scan.scan_paths([KIT / n for n in sorted(names) if n != "secret_scan.py"]) == []
    finally:
        sys.path.remove(str(KIT))
        sys.modules.pop("secret_scan", None)
    for same in ("secret_scan.py", "probes.py", "setup/extend_cap.py"):                 # copied unchanged
        assert (KIT / same).read_bytes() == (FAMILY_KIT / same).read_bytes()
    rules_text = (KIT / "gateb_rules.py").read_text()
    block = rules_text[rules_text.index("# ===== DRAFT constants"):rules_text.index("# ===== end of the DRAFT constants")]
    for name in ("POD_OVERHEAD_S", "START_MARGIN_S", "MEASURED_UPPER_S", "SPEND_UPPER_S", "PLANNING_PRICE_USD", "RATE_USD",
                 "RESERVE_USD", "SETUPTOOLS_PIN", "PIP_PIN", "DIAGNOSTICS_UPPER_S", "ANCHOR_UPPER_S", "WAVE2_SEEDS"):
        assert f"\n{name} = " in block, name
    for other in ("plan_tool.py", "orchestrate.py", "setup/job_runner_gateb.py", "launch.py", "budget.py", "host.py"):
        text = (KIT / other).read_text()
        for value in ("1.59", "1.79", "1.85", "52 * 60", "0.15 * 3600", "78.1.0"):
            assert value not in text, (other, value)


def test_the_data_config_namespace_and_the_seal_pins(kit):
    rules = kit("gateb_rules.py")
    data = json.loads((ROOT / "experiments/safety_selection/configs/study-kt-data-dolly-olmo2.json").read_text())
    assert tuple(data["seed_namespaces"]["development"]) == rules.DEV_SEEDS
    assert sha(SEAL / "MANIFEST.json") == rules.MAN_SHA256
    assert man()["prepared"]["manifest_sha256"] == rules.PREPARED_MANIFESTS["prepared-kt-dolly-olmo2"]
    recipe = json.loads((ROOT / REC).read_text())
    assert recipe["train"]["micro_batch"] * recipe["train"]["grad_accum"] == 128


def test_the_kit_reads_the_readings_calls_and_runs(kit, tmp_path, monkeypatch):
    """Part C's output names the wave it calls (``calls``) and its runs; anything else refuses."""
    tool = plan_tool(kit, monkeypatch)
    arms = tool.man_arms(tool.manifest())
    u = entries()["unit"][0]["arm"]
    cases = [("2", _reading("wave2", [(u, 1102)]), True),
             ("2", {**_reading("wave2", [(u, 1102)]), "kind": "other"}, False),
             ("2", _reading("extension", [(u, 1104)]), False),                     # calls ext, asked for wave 2
             ("2", _reading("wave2", [(u, 1102)], phase="verdict"), False),        # wave 2 comes from wave2 only
             ("lc", _reading("length-control", [(u, 1104)], phase="extension"), True),
             ("ext", _reading("extension", [(u, 1104)], phase="extension"), False),  # the extension comes from verdict
             ("lc", _reading("length-control", [(u, 1104)], phase="wave2"), False),   # lc comes from verdict or extension
             ("lc", _reading("extension", [(u, 1104)]), False)]          # a verdict that calls the extension, not lc
    for k, (wave, doc, ok) in enumerate(cases):
        path = tmp_path / f"reading-{k}.json"
        path.write_text(json.dumps(doc))
        if ok:
            assert tool.read_reading(str(path), wave, arms)["runs"] == [(r["arm"], r["seed"]) for r in doc["runs"]]
        else:
            with pytest.raises(SystemExit, match="calls wave"):
                tool.read_reading(str(path), wave, arms)



# ----- [D11]: re-runs from wave 1 on are paid from the contingency in launch order -----------------------------------


def _wave1(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units[:4], units[4:]], balance=FUNDED)
    _launch(kit.root, "w1-1")
    _done(tool, kit.root, "w1-1", ["complete", "crashed", "not_started", "not_started"])
    return tool, units


def test_a_crashed_arm_after_wave_1_is_paid_from_the_contingency(kit, tmp_path, monkeypatch):
    tool, units = _wave1(kit, tmp_path, monkeypatch)
    before = tool.mac.load_plan()["contingency"]["remaining_usd"]
    out = tool.defer("w1-1")
    plan = tool.mac.load_plan()
    c = plan["contingency"]
    # [D21]: the unlaunched w1-2 holds 4 arms, so the 3 moved jobs need a new pod w1-3; its 42 min is paid with the
    # crashed arm: (0.7 + 52/60) x 1.79 = 1.253 + 1.5513 = $2.8043 ([D20])
    assert out["to"] == "w1-3"
    assert c["remaining_usd"] == pytest.approx(before - (0.7 + 52 / 60) * 1.79)
    assert [(r["arm"], r["cost_usd"]) for r in c["spent"]] == [(units[1]["arm"], pytest.approx((0.7 + 52 / 60) * 1.79))]
    assert c["not_rerun"] == [] and plan["hosts"]["w1-3"]["jobs"][0]["arm"] == units[1]["arm"]


def test_a_rerun_the_contingency_cannot_pay_is_reported_not_rerun(kit, tmp_path, monkeypatch):
    tool, units = _wave1(kit, tmp_path, monkeypatch)
    plan = tool.mac.load_plan()
    plan["contingency"]["remaining_usd"] = 1.0                         # less than one arm's 52/60 x 1.79 = $1.551
    tool.mac.save_plan(plan)
    tool.defer("w1-1")
    plan = tool.mac.load_plan()
    moved = [j["arm"] for j in plan["hosts"]["w1-3"]["jobs"]]         # [D21]: w1-2 is full, so a new host
    assert units[1]["arm"] not in moved                                # the crashed arm is not re-run
    assert moved == [units[2]["arm"], units[3]["arm"]]                 # the not-started jobs still move, in order
    assert [r["arm"] for r in plan["contingency"]["not_rerun"]] == [units[1]["arm"]]
    assert plan["contingency"]["remaining_usd"] == 1.0
    actions = [json.loads(x) for x in (kit.root / "operator-actions.jsonl").read_text().splitlines()]
    assert [a["arm"] for a in actions if a["action"] == "not-rerun"] == [units[1]["arm"]]


def test_before_wave_1_a_crash_is_retried_without_a_contingency(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _launch(kit.root, "w0a-1")
    _done(tool, kit.root, "w0a-1", ["complete", "crashed", "not_started"])
    out = tool.defer("w0a-1")
    plan = tool.mac.load_plan()
    assert "contingency" not in plan and [j["arm"] for j in plan["hosts"][out["to"]]["jobs"]] == [
        e["R"][2]["arm"], e["R"][3]["arm"]]


# ----- [D14]: anchor deferral, requeue, the lock pin, the anchor text in backups ------------------------------------


def test_defer_of_the_anchor_host_creates_an_anchor_host(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    init(tool, tmp_path, "anchor", [[{"kind": "anchor"}]])
    _launch(kit.root, "anchor-1")
    _done(tool, kit.root, "anchor-1", ["deferred"])
    out = tool.defer("anchor-1")
    new = tool.mac.load_plan()["hosts"][out["to"]]
    assert out["to"] == "anchor-2" and new["role"] == "anchor" and new["wave"] == "anchor"
    assert new["stage"] == "anchor" and new["recipe_path"] == REC and new["cap_hours"] == quarter_up(0.7 + 0.75) == 1.5
    assert [(j["kind"], j["status"]) for j in new["jobs"]] == [("anchor", "planned")]


def test_init_wave_anchor_refuses_while_the_lock_pin_is_null(kit, tmp_path, monkeypatch):
    # the lead pinned Gate A's full lock hash on 10 Oct (shipped null until then); the refusals below still hold
    assert kit("gateb_rules.py").LOCK_SHA256 == "7e0dd99892300a27ab797be746f465860d8ea4055dda36c46d78e743381d15ee"
    tool = plan_tool(kit, monkeypatch)
    for unpinned in (None, "7e0dd998"):                                     # null, or a prefix only
        monkeypatch.setattr(tool.rules, "LOCK_SHA256", unpinned)
        with pytest.raises(SystemExit, match="LOCK_SHA256 is not pinned"):
            init(tool, tmp_path, "anchor", [[{"kind": "anchor"}]])
        assert not (kit.root / "plan.json").exists() and not (kit.root / "operator-actions.jsonl").exists()
    monkeypatch.setattr(tool.rules, "LOCK_SHA256", "7" * 64)
    assert init(tool, tmp_path, "anchor", [[{"kind": "anchor"}]])["hosts"] == ["anchor-1"]


@pytest.mark.parametrize("diagnostics", ["not_started", "deferred"])        # deferred: the [D7] exception's own case
def test_a_crashed_retrain_sealed_in_the_pulled_tree_is_not_exempt(kit, tmp_path, monkeypatch, diagnostics):
    """The stranded-retrain exception covers a retrain recorded complete only: a retrain JOB-DONE calls crashed whose
    sealed COMPLETE.json is in the pulled tree is a complete attempt, so defer refuses."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0b")
    init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                 {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])
    _launch(kit.root, "w0b-1")
    _done(tool, kit.root, "w0b-1", ["crashed", diagnostics])
    _complete_unit(kit.root, "w0b-1", "a0", 1101)                         # crashed per JOB-DONE, yet sealed
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="a complete attempt exists"):
        tool.defer("w0b-1")
    assert (kit.root / "plan.json").read_bytes() == before


LOGGED_FIELDS = {"pre-job-failed": {"step": "bootstrap"}, "pre-job-stop": {"exit": 0}}   # as orchestrate.after_create


def _orchestrate_log(kit_root: Path, host: str, *events) -> None:
    """orchestrate.py's per-host log (hosts/HOST/orchestrate.jsonl). An event name gets the fields after_create logs
    with it ([D17] 3: pre-job-failed at step bootstrap, pre-job-stop with exit 0, the stop confirmed); a dict is
    written as given (with utc and host)."""
    (kit_root / "hosts" / host).mkdir(parents=True, exist_ok=True)
    with open(kit_root / "hosts" / host / "orchestrate.jsonl", "a") as handle:
        for event in events:
            fields = dict(event) if isinstance(event, dict) else {"event": event, **LOGGED_FIELDS.get(event, {})}
            handle.write(json.dumps({"utc": "2026-10-09T10:00:00+00:00", "host": host, **fields}) + "\n")


def _actions(kit_root: Path) -> list[dict]:
    return [json.loads(x) for x in (kit_root / "operator-actions.jsonl").read_text().splitlines()]


def test_requeue_moves_every_job_of_a_host_stopped_before_its_job(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0b")
    init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                 {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])
    _launch(kit.root, "w0b-1")
    _orchestrate_log(kit.root, "w0b-1", "bootstrap-started")
    with pytest.raises(SystemExit, match="no logged pre-job failure"):
        tool.requeue("w0b-1")
    _orchestrate_log(kit.root, "w0b-1", "pre-job-failed", "pre-job-stop")
    out = tool.requeue("w0b-1")
    plan = tool.mac.load_plan()
    assert out["to"] == "w0b-2" and out["role"] == "job"
    assert [j["status"] for j in plan["hosts"]["w0b-1"]["jobs"]] == ["not_started", "not_started"]
    assert plan["hosts"]["w0b-1"]["pre_job_failed"]["orchestrate_sha256"] == sha(kit.root / "hosts/w0b-1/orchestrate.jsonl")
    new = plan["hosts"]["w0b-2"]
    assert [(j["kind"], j["status"], j["deferred_from"]) for j in new["jobs"]] == [("retrain", "planned", "w0b-1"),
                                                                                   ("diagnostics", "planned", "w0b-1")]
    assert new["jobs"][1]["a0_source"] == 0 and new["cap_hours"] == 4.5 and "reason" not in new["jobs"][0]
    assert plan["deferrals"] == [{"from": "w0b-1", "to": "w0b-2", "from_indices": [0, 1], "to_indices": [0, 1],
                                  "stranded_retrain": None, "reason": "pre-job-failed"}]
    assert [a["reason"] for a in _actions(kit.root) if a["action"] == "requeue"] == ["pre-job-failed"]
    with pytest.raises(SystemExit, match="already deferred"):
        tool.requeue("w0b-1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    with pytest.raises(SystemExit, match=r"wave 0b is not complete \(w0b-2\)"):      # the moved jobs must complete
        init(tool, tmp_path, "1", [units], balance=FUNDED)


def _first_host_files(kit_root: Path, host: str) -> Path:
    """What orchestrate fetches before record_first: hosts/HOST/bootstrap-ready.json and verification.json."""
    folder = kit_root / "hosts" / host
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "bootstrap-ready.json").write_text(json.dumps({**READY, "ok": True}))
    (folder / "verification.json").write_text(json.dumps({"environment": _environment(), "policy_identity": _policy()}))
    return folder / "verification.json"


def _record_first(kit, tool, monkeypatch, host: str, set_reference_ok: bool = True):
    """orchestrate.record_first for HOST, its set-reference subprocess replaced by the plan tool's own call (or by a
    failure: the [D16] 7 case, the fixture written and no reference)."""
    orch = kit("orchestrate.py")

    def run(args, **kwargs):
        if set_reference_ok:
            tool.set_reference(args[-1])
        return subprocess.CompletedProcess(args, 0 if set_reference_ok else 1, "", "synthetic failure")

    monkeypatch.setattr(orch, "subprocess", argparse.Namespace(run=run))
    orch.record_first(host, _first_host_files(kit.root, host))
    return orch


@pytest.mark.parametrize("stage", ["before record_first", "fixture without reference", "fixture and reference"])
def test_requeue_of_wave_0as_first_host_keeps_it_first_and_undoes_record_first(kit, tmp_path, monkeypatch, capsys,
                                                                                stage):
    """[D16] 7: a first host whose job never started is replaced by a first host. Whatever record_first left (the
    expected fixture, and the reference if set-reference ran) is undone: the fixture is renamed with a stamp and kept,
    the reference is cleared from plan.json (kept in the host's record), and operator-actions.jsonl records it."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _launch(kit.root, "w0a-1")
    fixture = kit.root / "expected-fixture-gateb.json"
    if stage == "fixture without reference":
        with pytest.raises(SystemExit, match="set-reference failed"):
            _record_first(kit, tool, monkeypatch, "w0a-1", set_reference_ok=False)
    elif stage == "fixture and reference":
        _record_first(kit, tool, monkeypatch, "w0a-1")
        assert tool.mac.load_plan()["reference"]["host"] == "w0a-1"
    written = fixture.read_bytes() if fixture.exists() else None
    assert (written is None) == (stage == "before record_first")
    _orchestrate_log(kit.root, "w0a-1", "pre-job-failed", "pre-job-stop")
    capsys.readouterr()
    out = tool.requeue("w0a-1")
    plan = tool.mac.load_plan()
    new = plan["hosts"][out["to"]]
    assert out["to"] == "w0a-2" and new["role"] == "first" and new["cap_hours"] == 5.0 and plan["reference"] is None
    assert [j["arm"] for j in new["jobs"]] == [e["R"][d]["arm"] for d in (1, 2, 3)]
    assert not fixture.exists()
    aside = sorted(kit.root.glob("expected-fixture-gateb.moved-*.json"))
    reset = [a for a in _actions(kit.root) if a["action"] == "first-host-reset"]
    assert len(reset) == 1 and reset[0]["host"] == "w0a-1" and reset[0]["to"] == "w0a-2"
    kept = plan["hosts"]["w0a-1"]["pre_job_failed"]["first_reset"]
    assert reset[0]["reference_cleared"] is (stage == "fixture and reference")
    if stage == "fixture and reference":
        assert kept["reference"]["host"] == "w0a-1"
        assert reset[0]["reference_verification_sha256"] == sha(kit.root / "hosts" / "w0a-1" / "verification.json")
    else:
        assert kept["reference"] is None
    if written is None:
        assert aside == [] and reset[0]["fixture"] is None and kept["fixture"] is None
    else:
        assert [p.name for p in aside] == [reset[0]["fixture"]["moved_to"]] == [kept["fixture"]["moved_to"]]
        assert re.fullmatch(r"expected-fixture-gateb\.moved-w0a-1-\d{14}Z\.json", aside[0].name)
        assert aside[0].read_bytes() == written and reset[0]["fixture"]["sha256"] == hashlib.sha256(written).hexdigest()
        assert reset[0]["fixture"]["recorded_by_host"] is True
    _record_first(kit, tool, monkeypatch, "w0a-2")                   # the replacement runs as first: no deadlock
    assert tool.mac.load_plan()["reference"]["host"] == "w0a-2" and fixture.exists()


def test_without_the_reset_a_replacement_first_host_cannot_record_its_fixture(kit, tmp_path, monkeypatch):
    """The [D16] 7 deadlock itself: with the first host's fixture still in place, record_first refuses."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    with pytest.raises(SystemExit, match="set-reference failed"):
        _record_first(kit, tool, monkeypatch, "w0a-1", set_reference_ok=False)
    with pytest.raises(SystemExit, match="an expected fixture is already recorded"):
        _record_first(kit, tool, monkeypatch, "w0a-1")


def test_requeue_of_a_first_host_refuses_a_reference_from_another_host(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    plan = tool.mac.load_plan()
    plan["reference"] = {"host": "w0a-9", "fields": {}, "bootstrap": {}}
    tool.mac.save_plan(plan)
    fixture = kit.root / "expected-fixture-gateb.json"
    fixture.write_text("{}")
    _launch(kit.root, "w0a-1")
    _orchestrate_log(kit.root, "w0a-1", "pre-job-failed", "pre-job-stop")
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match=r"set by another host \(w0a-9\)"):
        tool.requeue("w0a-1")
    assert (kit.root / "plan.json").read_bytes() == before and fixture.read_text() == "{}"
    assert not list(kit.root.glob("expected-fixture-gateb.moved-*.json"))


def test_a_requeued_first_host_never_acts_as_first_again(kit, tmp_path, monkeypatch):
    """[D16] 7 and 8: after the reset, the stopped w0a-1 (still role "first" in its own record) can neither record a
    fixture nor set the reference, so only its replacement w0a-2 acts as first; nothing is written by the refusals."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _launch(kit.root, "w0a-1")
    _record_first(kit, tool, monkeypatch, "w0a-1")
    _orchestrate_log(kit.root, "w0a-1", "pre-job-failed", "pre-job-stop")
    assert tool.requeue("w0a-1")["to"] == "w0a-2"
    fixture = kit.root / "expected-fixture-gateb.json"
    before = (kit.root / "plan.json").read_bytes()
    assert tool.mac.load_plan()["hosts"]["w0a-1"]["role"] == "first"
    with pytest.raises(SystemExit, match="moved to its replacement"):
        _record_first(kit, tool, monkeypatch, "w0a-1")                # a restarted stopped pod
    with pytest.raises(SystemExit, match="moved to its replacement"):
        tool.set_reference("w0a-1")
    assert not fixture.exists() and (kit.root / "plan.json").read_bytes() == before
    _record_first(kit, tool, monkeypatch, "w0a-2")
    assert tool.mac.load_plan()["reference"]["host"] == "w0a-2" and fixture.exists()


@pytest.mark.parametrize("started", ["a pulled JOB-DONE.json", "a logged job-started", "record-done"])
def test_requeue_refuses_a_host_whose_job_started(kit, tmp_path, monkeypatch, started):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _launch(kit.root, "w0a-1")
    _orchestrate_log(kit.root, "w0a-1", "pre-job-failed")
    if started == "a pulled JOB-DONE.json":
        (kit.root / "retrieved" / "w0a-1" / "tree").mkdir(parents=True)
        (kit.root / "retrieved" / "w0a-1" / "tree" / "JOB-DONE.json").write_text("{}")
    elif started == "a logged job-started":                     # orchestrate: "started although <step> reported ..."
        _orchestrate_log(kit.root, "w0a-1", "job-started")
    else:
        _done(tool, kit.root, "w0a-1", ["complete", "crashed", "not_started"])
        (kit.root / "retrieved" / "w0a-1" / "tree" / "JOB-DONE.json").unlink()   # the plan's record alone refuses
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="its job started"):
        tool.requeue("w0a-1")
    assert (kit.root / "plan.json").read_bytes() == before


@pytest.mark.parametrize("line", ['{"utc": "2026-10-09T10:01:00+00:00"', '{"utc": "2026-10-09T10:01:00+00:00"}'])
def test_requeue_refuses_an_unreadable_orchestrate_log_line(kit, tmp_path, monkeypatch, line):
    """A torn line or a line without an event never reads as "no job-started": requeue refuses and writes nothing."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _launch(kit.root, "w0a-1")
    _orchestrate_log(kit.root, "w0a-1", "pre-job-failed")
    with open(kit.root / "hosts" / "w0a-1" / "orchestrate.jsonl", "a") as handle:
        handle.write(line + "\n")
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="orchestrate.jsonl line 2 is unreadable"):
        tool.requeue("w0a-1")
    assert (kit.root / "plan.json").read_bytes() == before
    assert [a["action"] for a in _actions(kit.root)] == ["init-wave"] * 2                # anchor, 0a; no requeue


def test_the_requeue_command_passes_every_named_hash(kit, monkeypatch, capsys):
    tool = kit("plan_tool.py")
    calls = []
    monkeypatch.setattr(tool, "requeue", lambda host, rerun=None: calls.append((host, rerun)) or {"from": host})
    a, b, c = ("a" * 64, "b" * 64, "c" * 64)
    assert tool.main(["requeue", "w1-1"]) == 0
    assert tool.main(["requeue", "w1-1", "--rerun-mismatched", a, b, "--rerun-mismatched", c]) == 0
    assert calls == [("w1-1", None), ("w1-1", [a, b, c])]


@pytest.mark.parametrize("funded", [True, False])
def test_a_mismatched_requeue_onto_a_new_pod_pays_its_start_or_is_not_rerun(kit, tmp_path, monkeypatch, funded):
    """No wave-1 host has room ([D21]: the unlaunched w1-2 holds 4 arms): the re-run needs a new pod, paid with its
    42 min from the contingency; when the contingency cannot pay it, the arm is reported not re-run, and that attempt
    is never re-queued again."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units], balance=FUNDED)                             # split into w1-1 and w1-2
    lock = "1" * 64
    plan = tool.mac.load_plan()
    plan["reference"] = {"fields": tool.mac.reading_module().compared_fields(_environment(), lock, _policy()),
                         "bootstrap": {}}
    if not funded:
        plan["contingency"]["remaining_usd"] = 1.0                                 # less than one arm's $1.551
    tool.mac.save_plan(plan)
    _launch(kit.root, "w1-1")
    _complete_unit(kit.root, "w1-1", units[0]["arm"], 1101,
                   {"environment": _environment(cudnn=1), "environment_lock": {"sha256": lock}, "policy": _policy()})
    _done(tool, kit.root, "w1-1", ["complete"] * 4, {0: f"round1/1101-{units[0]['arm']}-e1-a1"})
    plan = tool.mac.load_plan()
    named, remaining = plan["hosts"]["w1-1"]["jobs"][0]["complete_sha256"], plan["contingency"]["remaining_usd"]
    w12 = plan["hosts"]["w1-2"]
    out = tool.requeue("w1-1", [named])
    plan = tool.mac.load_plan()
    c = plan["contingency"]
    assert plan["hosts"]["w1-2"] == w12                                            # full: never edited
    if funded:
        new = plan["hosts"]["w1-3"]
        assert out["to"] == "w1-3" and out["jobs"] == 1 and new["role"] == "job"
        assert [(j["arm"], j["mismatched_complete_sha256"]) for j in new["jobs"]] == [(units[0]["arm"], named)]
        assert c["remaining_usd"] == pytest.approx(remaining - (0.7 + 52 / 60) * 1.79) and c["not_rerun"] == []
    else:
        assert out["to"] is None and out["jobs"] == 0 and out["not_rerun"] == 1 and "w1-3" not in plan["hosts"]
        assert c["remaining_usd"] == 1.0 and [r["arm"] for r in c["not_rerun"]] == [units[0]["arm"]]
        assert [a["arm"] for a in _actions(kit.root) if a["action"] == "not-rerun"] == [units[0]["arm"]]
        assert plan["requeues"][0]["complete_sha256"] == [named]
    with pytest.raises(SystemExit, match="already re-queued"):
        tool.requeue("w1-1", [named])


def test_requeue_reruns_an_environment_mismatched_attempt_named_by_its_hash(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units[:4], units[4:]], balance=FUNDED)
    lock = "1" * 64
    plan = tool.mac.load_plan()
    plan["reference"] = {"fields": tool.mac.reading_module().compared_fields(_environment(), lock, _policy()),
                         "bootstrap": {}}
    tool.mac.save_plan(plan)
    _launch(kit.root, "w1-1")
    for k, env in ((0, _environment(cudnn=1)), (1, _environment())):                 # job 0 mismatched, job 1 equal
        _complete_unit(kit.root, "w1-1", units[k]["arm"], 1101,
                       {"environment": env, "environment_lock": {"sha256": lock}, "policy": _policy()})
    folders = {k: f"round1/1101-{units[k]['arm']}-e1-a1" for k in (0, 1)}
    _done(tool, kit.root, "w1-1", ["complete"] * 4, folders)
    plan = tool.mac.load_plan()
    named, equal = (plan["hosts"]["w1-1"]["jobs"][k]["complete_sha256"] for k in (0, 1))
    with pytest.raises(SystemExit, match="names no complete job of this host"):
        tool.requeue("w1-1", ["f" * 64])
    with pytest.raises(SystemExit, match="shows no environment mismatch"):
        tool.requeue("w1-1", [equal])
    with pytest.raises(SystemExit, match="its job started"):                         # no flag: not a pre-job stop
        tool.requeue("w1-1")
    with pytest.raises(SystemExit, match="record-done first"):
        tool.requeue("w1-2", [named])
    plan = tool.mac.load_plan()
    before_host, remaining = plan["hosts"]["w1-1"], plan["contingency"]["remaining_usd"]
    w12 = plan["hosts"]["w1-2"]
    out = tool.requeue("w1-1", [named])
    plan = tool.mac.load_plan()
    assert out["to"] == "w1-3" and out["jobs"] == 1 and plan["hosts"]["w1-1"] == before_host   # the attempt stays
    assert plan["hosts"]["w1-2"] == w12                          # [D21]: the unlaunched w1-2 holds 4 arms already
    first = plan["hosts"]["w1-3"]["jobs"][0]
    assert (first["arm"], first["seed"], first["status"]) == (units[0]["arm"], 1101, "planned")
    assert first["reason"] == "environment-mismatch" and first["mismatched_complete_sha256"] == named
    assert len(plan["hosts"]["w1-3"]["jobs"]) == 1
    arm_h = (E1_UPPER_S + TRAINING_S * 33 / 38 + 3700) / 3600
    assert plan["hosts"]["w1-3"]["cap_hours"] == quarter_up(0.7 + arm_h) == 3.25    # quarter_up(3.01955)
    c = plan["contingency"]                                                        # a new pod: its 42 min too
    assert c["remaining_usd"] == pytest.approx(remaining - (0.7 + 52 / 60) * 1.79)
    assert [(r["arm"], r["where"]) for r in c["spent"]] == [(units[0]["arm"], "requeue w1-1")]
    assert plan["requeues"][0]["complete_sha256"] == [named] and plan["deferrals"] == []
    rerun = [a for a in _actions(kit.root) if a["action"] == "rerun-mismatched"]
    assert len(rerun) == 1 and rerun[0]["mismatched_fields"] == ["cudnn"] and rerun[0]["complete_sha256"] == named
    assert [a["to"] for a in _actions(kit.root) if a["action"] == "requeue"] == ["w1-3"]
    with pytest.raises(SystemExit, match="already re-queued"):
        tool.requeue("w1-1", [named])


@pytest.mark.parametrize("stop", ["crashed", "pre-job"])
def test_a_rerun_of_a_mismatched_attempt_moves_again_after_a_crash_or_a_pre_job_stop(kit, tmp_path, monkeypatch, stop):
    """The re-queued mismatched attempt does not block its own re-run: a crashed re-run is deferred (and paid again),
    a pre-job stop of its host is requeued (every moved job paid, [D16] 5); the same arm without the re-run's record
    still refuses."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units[:4], units[4:]], balance=FUNDED)
    lock = "1" * 64
    plan = tool.mac.load_plan()
    plan["reference"] = {"fields": tool.mac.reading_module().compared_fields(_environment(), lock, _policy()),
                         "bootstrap": {}}
    tool.mac.save_plan(plan)
    _launch(kit.root, "w1-1")
    _complete_unit(kit.root, "w1-1", units[0]["arm"], 1101,
                   {"environment": _environment(cudnn=1), "environment_lock": {"sha256": lock}, "policy": _policy()})
    _done(tool, kit.root, "w1-1", ["complete"] * 4, {0: f"round1/1101-{units[0]['arm']}-e1-a1"})
    named = tool.mac.load_plan()["hosts"]["w1-1"]["jobs"][0]["complete_sha256"]
    tool.requeue("w1-1", [named])            # [D21]: w1-2 holds 4 arms, so the re-run is a new pod w1-3's job 0
    _launch(kit.root, "w1-3")
    remaining = tool.mac.load_plan()["contingency"]["remaining_usd"]
    if stop == "crashed":
        _done(tool, kit.root, "w1-3", ["crashed"])
        out = tool.defer("w1-3")
    else:
        _orchestrate_log(kit.root, "w1-3", "pre-job-failed", "pre-job-stop")
        out = tool.requeue("w1-3")
    plan = tool.mac.load_plan()
    moved = plan["hosts"][out["to"]]["jobs"]
    arm, start = 52 / 60 * 1.79, 0.7 * 1.79                                       # $1.5513 per arm; a new pod's 42 min
    # the contingency $78.45 - $62.76 = $15.69 ([D22], the default pod route) less the first re-run on its new pod:
    # 15.69 - 2.8043 = 12.8857
    assert remaining == pytest.approx(round(78.45 - 62.76, 2) - start - arm)
    # either way the one re-run moves again to a new pod w1-4 (w1-2 is still full), paid start + arm = $2.8043: a crash
    # pays the crashed job; a pre-job stop pays its moved jobs as one unit ([D16] 5, [D21] (3))
    assert out["to"] == "w1-4" and [j["arm"] for j in moved] == [units[0]["arm"]]
    assert moved[0]["mismatched_complete_sha256"] == named and moved[0]["reason"] == "environment-mismatch"
    assert plan["contingency"]["remaining_usd"] == pytest.approx(remaining - start - arm)
    assert plan["contingency"]["not_rerun"] == []
    last = plan["contingency"]["spent"][-1]
    if stop == "crashed":
        assert (last["arm"], last["cost_usd"]) == (units[0]["arm"], pytest.approx(start + arm))
    else:
        assert [u["arm"] for u in last["unit"]] == [units[0]["arm"]] and last["cost_usd"] == pytest.approx(start + arm)
    plan["hosts"]["w1-4"]["jobs"][0].pop("mismatched_complete_sha256")              # without the re-run's record
    tool.mac.save_plan(plan)
    _launch(kit.root, "w1-4")
    _done(tool, kit.root, "w1-4", ["crashed"])
    with pytest.raises(SystemExit, match="a complete attempt exists"):
        tool.defer("w1-4")


@pytest.mark.parametrize("stop", ["crashed", "pre-job"])
def test_a_stranded_retrain_rerun_moves_again_after_a_crash_or_a_pre_job_stop(kit, tmp_path, monkeypatch, stop):
    """[D7] then [D14]: the stranded attempt does not block its re-run's next move; a re-run sealed in its own pulled
    tree still refuses."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0b")
    init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                 {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])
    _launch(kit.root, "w0b-1")
    _done(tool, kit.root, "w0b-1", ["complete", "deferred"], {0: "round1/1101-a0-e1-a1"})
    stranded = tool.mac.load_plan()["hosts"]["w0b-1"]["jobs"][0]["complete_sha256"]
    assert tool.defer("w0b-1")["to"] == "w0b-2"
    _launch(kit.root, "w0b-2")
    if stop == "crashed":
        _done(tool, kit.root, "w0b-2", ["crashed", "not_started"])
        before = (kit.root / "plan.json").read_bytes()
        _complete_unit(kit.root, "w0b-2", "a0", 1101)                          # the re-run sealed after all
        with pytest.raises(SystemExit, match="a complete attempt exists"):
            tool.defer("w0b-2")
        assert (kit.root / "plan.json").read_bytes() == before
        shutil.rmtree(kit.root / "retrieved" / "w0b-2" / "tree" / "round1")
        out = tool.defer("w0b-2")
    else:
        _orchestrate_log(kit.root, "w0b-2", "pre-job-failed", "pre-job-stop")
        out = tool.requeue("w0b-2")
    moved = tool.mac.load_plan()["hosts"][out["to"]]["jobs"]
    assert out["to"] == "w0b-3" and [(j["kind"], j["status"]) for j in moved] == [("retrain", "planned"),
                                                                                  ("diagnostics", "planned")]
    assert moved[0]["stranded_complete_sha256"] == stranded and moved[1]["a0_source"] == 0


def test_the_backup_records_that_the_private_draft_may_hold_the_anchor_text(kit):
    backup = kit("backup_records_gateb.py")
    _, notes, _ = backup.texts({"name": "gate-b-olmo", "hosts": {"anchor-1": {"wave": "anchor"}}}, ["anchor-1"],
                               "backup-2026-10-09-gate-b")
    for text in (notes, backup.__doc__):
        assert "anchor-*/anchors.json" in text and "CC-BY-NC" in text and "git commits" in text
    assert "[D14]" in backup.__doc__ and "do not publish" in notes


# ----- [D16]: the pre-job requeue paid from the contingency, the wave-0b pair re-run, the first host, the README ------


@pytest.mark.parametrize("max_arms", [4, 8])
def test_a_pre_job_requeue_from_wave_1_on_is_paid_from_the_contingency(kit, tmp_path, monkeypatch, max_arms):
    """[D16] 5 and [D21] (3): every job a pre-job requeue moves from wave 1 on is paid, as one unit: the replacement
    pod's 42 min once plus each job's spend upper; when the unit does not fit, the jobs are paid one by one (the first
    with the 42 min) and an unpaid job is reported not re-run and logged. By hand ([D20]: $1.79/h; an arm's spend upper
    52 min = $1.5513; 42 min = $1.253):
      MAX_ARMS_PER_POD = 4 (the default; [D22] 1.25, pod Granite): contingency $78.45 - $62.76 = $15.69; w1-1's 4 arms
        go to a new pod w1-3 (w1-2 holds 4): one unit of (0.7 + 4 x 52/60) x 1.79 = $7.4583 <= $15.69, $8.2317 left;
        no missing arm;
      MAX_ARMS_PER_POD = 8 (the old one-pod plan, [D21]'s reason, kept at [D21]'s factor 1.15 and Mac Granite on
        purpose): contingency $62.71 - $54.53 = $8.18; the 8-arm unit
        (0.7 + 8 x 52/60) x 1.79 = $13.6637 does not fit, so one by one: 1.253 + 1.5513 = $2.8043 -> $5.3757, then
        1.5513 three times -> $0.7217; the fifth arm does not fit, nor any later one: 4 moved, 4 not re-run."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    monkeypatch.setattr(tool.rules, "MAX_ARMS_PER_POD", max_arms)
    if max_arms == 8:                                   # [D21]'s motivating shortfall, at its own factor and route
        monkeypatch.setattr(tool.rules, "CONTINGENCY_FACTOR", 1.15)
        monkeypatch.setattr(tool.rules, "GRANITE_ON_POD", False)
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units], balance=FUNDED)
    _launch(kit.root, "w1-1")
    _orchestrate_log(kit.root, "w1-1", "pre-job-failed", "pre-job-stop")
    out = tool.requeue("w1-1")
    plan = tool.mac.load_plan()
    c = plan["contingency"]
    arm, start = 52 / 60 * 1.79, 0.7 * 1.79
    if max_arms == 4:
        assert c["usd"] == pytest.approx(15.69) and out["to"] == "w1-3" and out["jobs"] == 4
        assert [j["arm"] for j in plan["hosts"]["w1-3"]["jobs"]] == [u["arm"] for u in units[:4]]
        assert [j["arm"] for j in plan["hosts"]["w1-2"]["jobs"]] == [u["arm"] for u in units[4:]]   # unchanged
        assert plan["hosts"]["w1-3"]["cap_hours"] == 5.75                              # as planned for w1-1
        assert len(c["spent"]) == 1 and c["spent"][0]["new_pod"] is True
        assert [u["arm"] for u in c["spent"][0]["unit"]] == [u["arm"] for u in units[:4]]
        assert c["spent"][0]["cost_usd"] == pytest.approx((0.7 + 4 * 52 / 60) * 1.79) == pytest.approx(7.458333, abs=1e-6)
        assert c["remaining_usd"] == pytest.approx(15.69 - 7.458333, abs=1e-6) and c["not_rerun"] == []
        assert "not-rerun" not in [a["action"] for a in _actions(kit.root)]
    else:
        assert c["usd"] == pytest.approx(8.18) and out["to"] == "w1-2"
        assert [j["arm"] for j in plan["hosts"]["w1-2"]["jobs"]] == [u["arm"] for u in units[:4]]
        assert [r["cost_usd"] for r in c["spent"]] == pytest.approx([start + arm, arm, arm, arm])
        assert c["remaining_usd"] == pytest.approx(8.18 - start - 4 * arm)
        assert [r["arm"] for r in c["not_rerun"]] == [u["arm"] for u in units[4:]]
        assert [a["arm"] for a in _actions(kit.root) if a["action"] == "not-rerun"] == [u["arm"] for u in units[4:]]
    assert all(r["where"] == "requeue w1-1" for r in c["spent"] + c["not_rerun"])
    assert plan["deferrals"][0]["reason"] == "pre-job-failed"


def test_d21_a_pre_job_stop_of_each_wave_1_pod_in_turn(kit, tmp_path, monkeypatch):
    """[D21] (3) with [D22]'s factor 1.25: both 4-arm wave-1 pods stop before their jobs. By hand (the default pod
    route: contingency 78.45 - 62.76 = $15.69): the first requeue is paid as one unit, (0.7 + 4 x 52/60) x 1.79 =
    $7.4583 -> $8.2317; the second unit, $7.4583 <= $8.2317, is paid too -> $0.7733; no arm is missing, so the
    contingency pays two 4-arm pre-job stops in full ([D22]'s reason; at [D21]'s 1.15, $8.74, the second pod's 4 arms
    were reported not re-run). The second unit goes to a new pod w1-4 (w1-3 holds 4)."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units], balance=FUNDED)
    for host in ("w1-1", "w1-2"):
        _launch(kit.root, host)
        _orchestrate_log(kit.root, host, "pre-job-failed", "pre-job-stop")
    first, second = tool.requeue("w1-1"), tool.requeue("w1-2")
    plan = tool.mac.load_plan()
    c = plan["contingency"]
    unit = (0.7 + 4 * 52 / 60) * 1.79
    assert first["to"] == "w1-3" and first["jobs"] == 4
    assert second["to"] == "w1-4" and second["jobs"] == 4 and second.get("not_rerun", 0) == 0
    assert [j["arm"] for j in plan["hosts"]["w1-4"]["jobs"]] == [u["arm"] for u in units[4:]]
    assert [r["cost_usd"] for r in c["spent"]] == pytest.approx([unit, unit])
    assert c["remaining_usd"] == pytest.approx(15.69 - 2 * unit) == pytest.approx(0.773333, abs=1e-6)
    assert c["not_rerun"] == [] and "not-rerun" not in [a["action"] for a in _actions(kit.root)]


def test_d21_a_crash_then_a_later_waves_pre_job_stop_are_paid_in_launch_order(kit, tmp_path, monkeypatch):
    """[D11], [D21] (3): the contingency pays in launch order across waves. w1-1 crashes its last arm; w1-2 holds 4, so
    defer puts it on a new pod w1-3: (0.7 + 52/60) x 1.79 = $2.8043, leaving 15.69 - 2.8043 = $12.8857 ([D22]: the
    default pod route's contingency 78.45 - 62.76). Wave 2 is 4 + 4; w2-1 stops before its job: the unit (0.7 + 4 x
    52/60) x 1.79 = $7.4583 <= $12.8857 is paid as one unit -> $5.4273, so no arm is missing (at [D21]'s 1.15, $8.74,
    the same path left one arm missing; the one-by-one shortfall is pinned in the [D21] (3) tests)."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    u = entries()["unit"]
    init(tool, tmp_path, "1", [[arm_job(x, 1101) for x in u]], balance=FUNDED)
    _launch(kit.root, "w1-1")
    _done(tool, kit.root, "w1-1", ["complete", "complete", "complete", "crashed"])
    assert tool.defer("w1-1")["to"] == "w1-3"
    complete(tool, "1")
    w2 = [arm_job(u[k], s) for k in range(4) for s in (1102, 1103)]
    init(tool, tmp_path, "2", [w2], reading=_reading("wave2", [(j["arm"], j["seed"]) for j in w2]))
    _launch(kit.root, "w2-1")
    _orchestrate_log(kit.root, "w2-1", "pre-job-failed", "pre-job-stop")
    out = tool.requeue("w2-1")
    plan = tool.mac.load_plan()
    c = plan["contingency"]
    new, arm = (0.7 + 52 / 60) * 1.79, 52 / 60 * 1.79
    unit = (0.7 + 4 * 52 / 60) * 1.79
    assert out["to"] == "w2-3" and out["jobs"] == 4                                 # w2-2 holds 4: a new pod
    assert [(j["arm"], j["seed"]) for j in plan["hosts"]["w2-3"]["jobs"]] == [(j["arm"], j["seed"]) for j in w2[:4]]
    assert plan["hosts"]["w2-3"]["cap_hours"] == 5.75
    assert [(r["where"], r["cost_usd"]) for r in c["spent"]] == [
        ("defer w1-1", pytest.approx(new)), ("requeue w2-1", pytest.approx(unit))]
    assert c["remaining_usd"] == pytest.approx(15.69 - new - unit) == pytest.approx(5.427333, abs=1e-6)
    assert c["not_rerun"] == [] and "not-rerun" not in [a["action"] for a in _actions(kit.root)]


def test_a_pre_job_requeue_the_contingency_cannot_pay_at_all_moves_nothing_and_is_logged(kit, tmp_path, monkeypatch):
    """[D16] 5 with $1.00 left: w1-1 (4 arms; [D21]) needs a new pod since w1-2 holds 4; by hand ([D20]) the unit
    (0.7 + 4 x 52/60) x 1.79 = $7.4583 > $1.00, and one by one the first arm costs 1.253 + 1.5513 = $2.8043 > $1.00, and
    since none is paid each later arm is charged the same: all 4 are not re-run, no host is created, and both the
    requeue (to: null) and the 4 not-rerun records are in operator-actions.jsonl."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units], balance=FUNDED)
    plan = tool.mac.load_plan()
    plan["contingency"]["remaining_usd"] = 1.0
    tool.mac.save_plan(plan)
    _launch(kit.root, "w1-1")
    _orchestrate_log(kit.root, "w1-1", "pre-job-failed", "pre-job-stop")
    out = tool.requeue("w1-1")
    plan = tool.mac.load_plan()
    c = plan["contingency"]
    assert out["to"] is None and out["jobs"] == 0 and out["not_rerun"] == 4 and "w1-3" not in plan["hosts"]
    assert c["remaining_usd"] == 1.0 and c["spent"] == []
    assert [r["cost_usd"] for r in c["not_rerun"]] == pytest.approx([(0.7 + 52 / 60) * 1.79] * 4)
    assert plan["deferrals"] == [{"from": "w1-1", "to": None, "from_indices": list(range(4)), "to_indices": [],
                                  "stranded_retrain": None, "not_rerun": 4, "reason": "pre-job-failed"}]
    actions = _actions(kit.root)
    assert [a["arm"] for a in actions if a["action"] == "not-rerun"] == [u["arm"] for u in units[:4]]
    requeued = [a for a in actions if a["action"] == "requeue"]
    assert len(requeued) == 1 and requeued[0]["to"] is None and requeued[0]["reason"] == "pre-job-failed"
    with pytest.raises(SystemExit, match="already deferred"):
        tool.requeue("w1-1")


def _attributes_unit(kit_root: Path, host: str, assets: dict) -> Path:
    """A complete attributes unit (the diagnostics' engine unit) in HOST's pulled tree."""
    unit = kit_root / "retrieved" / host / "tree" / "gatec" / "1101-attributes-a1"
    unit.mkdir(parents=True)
    (unit / "job.json").write_text(json.dumps({"kind": "attributes", "seed": 1101}))
    (unit / "assets.json").write_text(json.dumps(assets))
    (unit / "COMPLETE.json").write_text("{}")
    return unit


def _wave0b_pair(kit, tmp_path, monkeypatch, mismatched: str, diagnostics: str = "complete"):
    """Wave 0b done on w0b-1 with the retrain and the diagnostics both pulled; ``mismatched`` names the unit whose
    recorded cudnn differs from the reference ("retrain", "diagnostics" or "neither")."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0b")
    init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                 {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])
    lock = "1" * 64
    plan = tool.mac.load_plan()
    plan["reference"] = {"host": "w0a-1", "fields": tool.mac.reading_module().compared_fields(_environment(), lock,
                                                                                              _policy()), "bootstrap": {}}
    tool.mac.save_plan(plan)
    _launch(kit.root, "w0b-1")

    def assets(which):
        env = _environment(cudnn=1) if mismatched == which else _environment()
        return {"environment": env, "environment_lock": {"sha256": lock}, "policy": _policy()}

    _complete_unit(kit.root, "w0b-1", "a0", 1101, assets("retrain"))
    folders = {0: "round1/1101-a0-e1-a1"}
    if diagnostics == "complete":
        _attributes_unit(kit.root, "w0b-1", assets("diagnostics"))
        folders[1] = "gatec/1101-attributes-a1"
    _done(tool, kit.root, "w0b-1", ["complete", diagnostics], folders)
    jobs = tool.mac.load_plan()["hosts"]["w0b-1"]["jobs"]
    return tool, [j["complete_sha256"] for j in jobs]


@pytest.mark.parametrize("named", [0, 1])                     # 0: the retrain's hash; 1: the diagnostics'
def test_rerun_mismatched_requeues_the_wave_0b_retrain_and_diagnostics_together(kit, tmp_path, monkeypatch, named):
    """[D16] 6: naming either one's COMPLETE.json SHA-256 (with that unit's environment mismatched) re-queues the
    linked pair; the diagnostics' a0_source names the moved retrain; wave 0b is before wave 1, so a contingency that
    exists is not touched. By hand: the new w0b-2 holds [retrain, diagnostics] at a0_source 0, cap 4.5 h (the wave-0b
    cap of [D11])."""
    tool, digests = _wave0b_pair(kit, tmp_path, monkeypatch, ["retrain", "diagnostics"][named])
    plan = tool.mac.load_plan()
    plan["contingency"] = {"usd": 8.37, "remaining_usd": 8.37, "spent": [], "not_rerun": []}   # synthetic
    tool.mac.save_plan(plan)
    before_host = plan["hosts"]["w0b-1"]
    with pytest.raises(SystemExit, match="shows no environment mismatch"):           # the matched partner's hash
        tool.requeue("w0b-1", [digests[1 - named]])
    out = tool.requeue("w0b-1", [digests[named]])
    plan = tool.mac.load_plan()
    jobs = plan["hosts"]["w0b-2"]["jobs"]
    assert out["to"] == "w0b-2" and out["jobs"] == 2 and plan["hosts"]["w0b-1"] == before_host
    assert [(j["kind"], j["arm"], j["seed"], j["status"]) for j in jobs] == [("retrain", "a0", 1101, "planned"),
                                                                            ("diagnostics", None, 1101, "planned")]
    assert jobs[1]["a0_source"] == 0 and plan["hosts"]["w0b-2"]["cap_hours"] == 4.5
    assert [j["mismatched_complete_sha256"] for j in jobs] == digests
    assert [j["reason"] for j in jobs] == ["environment-mismatch"] * 2
    assert [bool(j.get("linked_rerun")) for j in jobs] == [k != named for k in (0, 1)]
    assert plan["requeues"][0]["complete_sha256"] == digests and plan["requeues"][0]["from_indices"] == [0, 1]
    assert plan["contingency"] == {"usd": 8.37, "remaining_usd": 8.37, "spent": [], "not_rerun": []}
    rerun = [a for a in _actions(kit.root) if a["action"] == "rerun-mismatched"]
    assert [(a["kind"], a["complete_sha256"], a["mismatched_fields"]) for a in rerun] == [
        (["retrain", "diagnostics"][named], digests[named], ["cudnn"])]
    for digest in digests:                                                            # each attempt is re-queued once
        with pytest.raises(SystemExit, match="already re-queued"):
            tool.requeue("w0b-1", [digest])
    _launch(kit.root, "w0b-2")                                   # the re-run pair crashes: it moves again, together
    _done(tool, kit.root, "w0b-2", ["crashed", "not_started"])
    to = tool.defer("w0b-2")["to"]
    moved = tool.mac.load_plan()["hosts"][to]["jobs"]
    assert to == "w0b-3" and [j["kind"] for j in moved] == ["retrain", "diagnostics"] and moved[1]["a0_source"] == 0
    assert [j["mismatched_complete_sha256"] for j in moved] == digests


def test_a_pre_job_stop_of_the_wave_0b_rerun_pair_requeues_the_pair_together(kit, tmp_path, monkeypatch):
    """[D16] 6 with the arm path's pre-job case: the re-run pair's host stops before its job; requeue moves both, in
    order, a0_source 0, each still naming its mismatched attempt (which does not block its own re-run), and a
    contingency that exists is not touched (wave 0b is before wave 1)."""
    tool, digests = _wave0b_pair(kit, tmp_path, monkeypatch, "retrain")
    tool.requeue("w0b-1", [digests[0]])
    plan = tool.mac.load_plan()
    plan["contingency"] = {"usd": 8.37, "remaining_usd": 8.37, "spent": [], "not_rerun": []}   # synthetic
    tool.mac.save_plan(plan)
    _launch(kit.root, "w0b-2")
    _orchestrate_log(kit.root, "w0b-2", "pre-job-failed", "pre-job-stop")
    out = tool.requeue("w0b-2")
    plan = tool.mac.load_plan()
    moved = plan["hosts"][out["to"]]["jobs"]
    assert out["to"] == "w0b-3" and [j["kind"] for j in moved] == ["retrain", "diagnostics"]
    assert moved[1]["a0_source"] == 0 and [j["mismatched_complete_sha256"] for j in moved] == digests
    assert [bool(j.get("linked_rerun")) for j in moved] == [False, True]
    assert plan["contingency"] == {"usd": 8.37, "remaining_usd": 8.37, "spent": [], "not_rerun": []}


@pytest.mark.parametrize("diagnostics", ["crashed", "deferred"])
def test_rerun_mismatched_refuses_a_retrain_whose_diagnostics_is_not_complete(kit, tmp_path, monkeypatch, diagnostics):
    tool, digests = _wave0b_pair(kit, tmp_path, monkeypatch, "retrain", diagnostics)
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="both must be complete on this host"):
        tool.requeue("w0b-1", [digests[0]])
    assert (kit.root / "plan.json").read_bytes() == before


def test_the_backup_stages_a_first_hosts_moved_fixture(kit, tmp_path, monkeypatch, capsys):
    tool = plan_tool(kit, monkeypatch)
    _backup_kit(tool, kit, tmp_path)
    name = "expected-fixture-gateb.moved-w0a-1-20261009100000Z.json"
    (kit.root / name).write_text("{}")
    code, summary, out, _ = _backup(kit, capsys, "--host", "w0b-1", "--host", "w0b-2")
    assert code == 0 and f"  analyses/{name}  <- " in out


def test_the_readme_states_the_operator_rule():
    text = " ".join((KIT / "README.md").read_text().split())
    assert "A stopped kit pod is never restarted." in text
    assert "A requeued host's jobs run only on its replacement." in text


def test_requeue_of_a_first_host_never_overwrites_a_kept_fixture(kit, tmp_path, monkeypatch):
    """[D16] 7: the moved fixture is kept, never overwritten. With the clock at 2026-10-09T10:00:00+00:00 the stamped
    name is expected-fixture-gateb.moved-w0a-1-20261009100000Z.json (by hand: the first 14 digits); when that name is
    already taken, requeue refuses and changes nothing (plan.json, the fixture and the file already there)."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _launch(kit.root, "w0a-1")
    with pytest.raises(SystemExit, match="set-reference failed"):
        _record_first(kit, tool, monkeypatch, "w0a-1", set_reference_ok=False)
    _orchestrate_log(kit.root, "w0a-1", "pre-job-failed", "pre-job-stop")
    monkeypatch.setattr(tool.mac, "utc", lambda: "2026-10-09T10:00:00+00:00")
    fixture = kit.root / "expected-fixture-gateb.json"
    taken = kit.root / "expected-fixture-gateb.moved-w0a-1-20261009100000Z.json"
    taken.write_text("{}")
    before, written = (kit.root / "plan.json").read_bytes(), fixture.read_bytes()
    with pytest.raises(SystemExit, match="already exists"):
        tool.requeue("w0a-1")
    assert (kit.root / "plan.json").read_bytes() == before and fixture.read_bytes() == written
    assert taken.read_text() == "{}" and not [a for a in _actions(kit.root) if a["action"] == "first-host-reset"]


@pytest.mark.parametrize("log", ["no record", "another hash"])
def test_a_moved_fixture_the_host_did_not_record_is_kept_and_marked_so(kit, tmp_path, monkeypatch, log):
    """[D16] 7: recorded_by_host is true only when this host's orchestrate log recorded the fixture's own SHA-256. A
    fixture in place that the log never recorded (or recorded with another hash) is still moved aside and kept, with
    recorded_by_host false."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _launch(kit.root, "w0a-1")
    fixture = kit.root / "expected-fixture-gateb.json"
    fixture.write_text(json.dumps({"synthetic": True}))
    if log == "another hash":
        (kit.root / "hosts" / "w0a-1").mkdir(parents=True, exist_ok=True)
        with open(kit.root / "hosts" / "w0a-1" / "orchestrate.jsonl", "a") as handle:
            handle.write(json.dumps({"utc": "2026-10-09T10:00:00+00:00", "host": "w0a-1",
                                     "event": "expected-fixture-recorded", "sha256": "e" * 64}) + "\n")
    _orchestrate_log(kit.root, "w0a-1", "pre-job-failed", "pre-job-stop")
    out = tool.requeue("w0a-1")
    reset = [a for a in _actions(kit.root) if a["action"] == "first-host-reset"]
    assert out["to"] == "w0a-2" and len(reset) == 1 and not fixture.exists()
    assert reset[0]["fixture"]["recorded_by_host"] is False
    assert reset[0]["fixture"]["sha256"] == hashlib.sha256(json.dumps({"synthetic": True}).encode()).hexdigest()
    assert (kit.root / reset[0]["fixture"]["moved_to"]).read_text() == json.dumps({"synthetic": True})


def test_the_linked_partner_is_exempt_from_its_own_attempt_only(kit, tmp_path, monkeypatch):
    """[D16] 6: the partner moved with a named retrain skips only its own complete attempt; another complete attempt
    of the diagnostics (here sealed in a second pulled tree, w0b-9) still refuses, and nothing is written."""
    tool, digests = _wave0b_pair(kit, tmp_path, monkeypatch, "retrain")
    other = _attributes_unit(kit.root, "w0b-9", {})
    (other / "COMPLETE.json").write_text(json.dumps({"attempt": 2}))         # a different attempt (another hash)
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="diagnostics at 1101: a complete attempt exists"):
        tool.requeue("w0b-1", [digests[0]])
    assert (kit.root / "plan.json").read_bytes() == before
    assert not [a for a in _actions(kit.root) if a["action"] in ("requeue", "rerun-mismatched")]


# ----- [D17]: a requeue never follows a failed or unknown stop; the guard record; wave order and repeated hashes ------


def _stop_fakes(orch, monkeypatch, ssh_exit: int, stop_exit: int) -> list:
    """orchestrate's host tool replaced: ssh exits ``ssh_exit`` (0: started.json exists; 1: it does not; 255: no
    connection), extend-cap 0 when ssh works (else 1), stop ``stop_exit``; returns the calls."""
    calls = []

    def tool(*a, **k):
        calls.append(a)
        code = ssh_exit if a[0] == "ssh" else stop_exit if a[0] == "stop" else (0 if ssh_exit in (0, 1) else 1)
        return subprocess.CompletedProcess(a, code, "", "")

    monkeypatch.setattr(orch, "tool", tool)
    return calls


def _log_records(kit_root: Path, host: str) -> list[dict]:
    return [json.loads(x) for x in (kit_root / "hosts" / host / "orchestrate.jsonl").read_text().splitlines()]


def _pod_latest(kit_root: Path, host: str, status: str = "EXITED", minutes: float = 1) -> None:
    """hosts/HOST/pod-latest.json as host.py get writes it: the pod's desiredStatus, read ``minutes`` after now."""
    read = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=minutes)
    (kit_root / "hosts" / host / "pod-latest.json").write_text(json.dumps({"desiredStatus": status,
                                                                           "utc": read.isoformat(timespec="seconds")}))


def _wave1_hosts(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units[:4], units[4:]], balance=FUNDED)
    _launch(kit.root, "w1-1")
    return tool, units


@pytest.mark.parametrize("code, started", [(0, True), (1, False), (255, None), ("raise", None)])
def test_job_started_reads_exit_0_and_1_and_nothing_else(kit, monkeypatch, code, started):
    """[D17] 3: ``test -f started.json`` exits 0 (present) or 1 (absent); any other exit (ssh's 255 on a dropped
    connection) or an exception is unknown (None), never "not started"."""
    orch = kit("orchestrate.py")

    def ssh(host, command):
        if code == "raise":
            raise OSError("synthetic")
        return subprocess.CompletedProcess([host], code, "", "")

    monkeypatch.setattr(orch, "ssh", ssh)
    assert orch.job_started("w1-1") is started


def test_k4_an_ssh_drop_at_start_job_is_an_unknown_start_and_requeue_waits_for_the_operator(kit, tmp_path, monkeypatch):
    """Re-review probe k4: start_background's nohup ran on the pod, then its 15 s check lost the connection; ssh stays
    down (exit 255) and the stop fails (exit 1). By hand: job_started is None, so the log holds job-start-unknown at
    step start-job (never pre-job-failed) and pre-job-stop with exit 1; requeue refuses and writes nothing; once
    host.py get reads EXITED after the log and the operator records confirm-stopped, requeue moves w1-1's 4 jobs."""
    tool, units = _wave1_hosts(kit, tmp_path, monkeypatch)
    orch = kit("orchestrate.py")
    launched = []
    for name in ("wait_ssh", "check", "bootstrap"):
        monkeypatch.setattr(orch, name, lambda host: None)
    monkeypatch.setattr(orch, "wait_file", lambda *a, **k: {})
    monkeypatch.setattr(orch, "fetch", lambda host, remote, local: {})
    monkeypatch.setattr(orch, "bootstrap_check", lambda *a: {})
    monkeypatch.setattr(orch, "preflight_check", lambda *a: {})
    monkeypatch.setattr(orch, "preflight", lambda host: {"folder": "pf"})
    monkeypatch.setattr(orch, "cap_gate", lambda *a: {"ok": True})
    monkeypatch.setattr(orch, "wait_for", lambda *a, **k: None)
    monkeypatch.setattr(orch, "send", lambda *a: None)

    def start_background(host, outer, command):
        launched.append(outer)                                  # the nohup ran on the pod
        raise SystemExit(f"{host}: {outer} did not start:\n")    # the 15 s check lost its connection

    monkeypatch.setattr(orch, "start_background", start_background)
    calls = _stop_fakes(orch, monkeypatch, 255, 1)
    with pytest.raises(SystemExit):
        orch.after_create("w1-1")
    events = _log_records(kit.root, "w1-1")
    assert launched == ["job-outer"] and ("stop", "w1-1") in calls
    assert [(e["event"], e.get("step"), e.get("exit")) for e in events] == [("job-start-unknown", "start-job", None),
                                                                           ("pre-job-stop", None, 1)]
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="stop is not confirmed"):
        tool.requeue("w1-1")
    assert (kit.root / "plan.json").read_bytes() == before
    with pytest.raises(SystemExit, match="no pod status read"):
        tool.confirm_stopped("w1-1")
    _pod_latest(kit.root, "w1-1")
    assert tool.confirm_stopped("w1-1") == {"host": "w1-1", "confirmed": True}
    out = tool.requeue("w1-1")
    plan = tool.mac.load_plan()
    assert out["jobs"] == 4 and out["to"] == "w1-3"                     # [D21]: w1-2 holds 4 arms, so a new pod
    assert plan["hosts"]["w1-1"]["pre_job_failed"]["stop"]["by"] == "operator"
    confirm = [a for a in _actions(kit.root) if a["action"] == "confirm-stopped"]
    assert len(confirm) == 1 and confirm[0]["orchestrate_sha256"] == sha(kit.root / "hosts/w1-1/orchestrate.jsonl")


@pytest.mark.parametrize("stop_exit", [0, 1])
def test_a_stop_with_exit_1_is_not_a_confirmed_stop(kit, tmp_path, monkeypatch, stop_exit):
    """[D17] 3: a bootstrap failure with the job runner never started (ssh exit 1) logs pre-job-failed at step
    bootstrap and pre-job-stop with the stop's exit. By hand: exit 0 lets requeue read the stop from the log; exit 1
    (host.py could not confirm EXITED) refuses until the operator's confirm-stopped record."""
    tool, units = _wave1_hosts(kit, tmp_path, monkeypatch)
    orch = kit("orchestrate.py")
    for name in ("wait_ssh", "check"):
        monkeypatch.setattr(orch, name, lambda host: None)

    def bootstrap(host):
        raise SystemExit(f"{host}: setup unpack failed")

    monkeypatch.setattr(orch, "bootstrap", bootstrap)
    calls = _stop_fakes(orch, monkeypatch, 1, stop_exit)
    with pytest.raises(SystemExit, match="setup unpack failed"):
        orch.after_create("w1-1")
    assert calls[1:] == [("extend-cap", "w1-1", "120"), ("stop", "w1-1")]
    events = _log_records(kit.root, "w1-1")
    assert [(e["event"], e.get("step"), e.get("exit")) for e in events] == [("pre-job-failed", "bootstrap", None),
                                                                           ("pre-job-stop", None, stop_exit)]
    if stop_exit == 1:
        before = (kit.root / "plan.json").read_bytes()
        with pytest.raises(SystemExit, match="stop is not confirmed"):
            tool.requeue("w1-1")
        assert (kit.root / "plan.json").read_bytes() == before
        _pod_latest(kit.root, "w1-1")
        tool.confirm_stopped("w1-1")
    out = tool.requeue("w1-1")
    assert out["jobs"] == 4
    assert tool.mac.load_plan()["hosts"]["w1-1"]["pre_job_failed"]["stop"]["by"] == ("log" if stop_exit == 0 else "operator")


@pytest.mark.parametrize("records, by", [
    ([{"event": "pre-job-failed", "step": "start-job"}, {"event": "pre-job-stop", "exit": 0}], None),
    ([{"event": "pre-job-failed"}, {"event": "pre-job-stop", "exit": 0}], None),                        # no step
    ([{"event": "pre-job-failed", "step": "bootstrap"}, {"event": "pre-job-stop", "exit": False}], None),   # not an int
    ([{"event": "pre-job-stop", "exit": 0}, {"event": "pre-job-failed", "step": "bootstrap"}], None),      # stop first
    ([{"event": "pre-job-failed", "step": "bootstrap"}, {"event": "pre-job-stop", "exit": 0},
      {"event": "pre-job-failed", "step": "start-job"}, {"event": "pre-job-stop", "exit": 0}], None),     # the last counts
    ([{"event": "pre-job-failed", "step": "start-job"}, {"event": "pre-job-stop", "exit": 0},
      {"event": "pre-job-failed", "step": "bootstrap"}, {"event": "pre-job-stop", "exit": 0}], "log"),
    ([{"event": "pre-job-failed", "step": "bootstrap"}, {"event": "job-start-unknown", "step": "start-job"},
      {"event": "pre-job-stop", "exit": 0}], None),
    ([{"event": "pre-job-failed", "step": "preflight-check"}, {"event": "pre-job-stop", "exit": 0}], "log"),
])
def test_requeue_reads_the_stop_from_the_log_only_after_a_confirmed_stop_before_start_job(kit, tmp_path, monkeypatch,
                                                                                          records, by):
    """[D17] 3, by hand per row: the log alone counts only when the last pre-job-failed names a step (a string) other
    than start-job, a later pre-job-stop has the int exit 0, and no job-start-unknown is logged; every other row
    refuses until the operator confirms."""
    tool, units = _wave1_hosts(kit, tmp_path, monkeypatch)
    _orchestrate_log(kit.root, "w1-1", *records)
    if by is None:
        before = (kit.root / "plan.json").read_bytes()
        with pytest.raises(SystemExit, match="stop is not confirmed"):
            tool.requeue("w1-1")
        assert (kit.root / "plan.json").read_bytes() == before
        assert not [a for a in _actions(kit.root) if a["action"] == "requeue"]
    else:
        assert tool.requeue("w1-1")["jobs"] == 4
        assert tool.mac.load_plan()["hosts"]["w1-1"]["pre_job_failed"]["stop"] == {"by": "log"}


def test_confirm_stopped_needs_an_exited_pod_read_after_the_log_and_binds_to_the_log(kit, tmp_path, monkeypatch):
    """[D17] 3, the operator's route. The log's records are at 10:00:00 UTC. By hand: no pod read, a RUNNING pod, or a
    read at 09:59 refuse; a read at 10:05 showing EXITED is recorded with the log's SHA-256; a record appended to the
    log afterwards voids it (requeue refuses again) until the operator confirms the new log."""
    tool, units = _wave1_hosts(kit, tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="no logged pre-job failure"):
        tool.confirm_stopped("w1-1")
    _orchestrate_log(kit.root, "w1-1", {"event": "pre-job-failed", "step": "start-job"},
                     {"event": "pre-job-stop", "exit": 0})
    folder = kit.root / "hosts" / "w1-1"
    with pytest.raises(SystemExit, match="no pod status read"):
        tool.confirm_stopped("w1-1")
    for status, utc, why in (("RUNNING", "2026-10-09T10:05:00+00:00", "not EXITED"),
                             ("EXITED", "2026-10-09T09:59:00+00:00", "read before the last orchestrate record"),
                             ("EXITED", "2026-10-09T10:05:00", "no readable UTC time")):
        (folder / "pod-latest.json").write_text(json.dumps({"desiredStatus": status, "utc": utc}))
        with pytest.raises(SystemExit, match=why):
            tool.confirm_stopped("w1-1")
    assert not [a for a in _actions(kit.root) if a["action"] == "confirm-stopped"]
    (folder / "pod-latest.json").write_text(json.dumps({"desiredStatus": "EXITED", "utc": "2026-10-09T10:05:00+00:00"}))
    tool.confirm_stopped("w1-1")
    _orchestrate_log(kit.root, "w1-1", {"event": "pre-job-stop", "exit": 1})            # the log changed after it
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="stop is not confirmed"):
        tool.requeue("w1-1")
    assert (kit.root / "plan.json").read_bytes() == before
    tool.confirm_stopped("w1-1")
    assert tool.requeue("w1-1")["jobs"] == 4
    host = kit.root / "hosts" / "w1-2"
    _orchestrate_log(kit.root, "w1-2", "pre-job-failed", "job-started")
    with pytest.raises(SystemExit, match="its job started"):
        tool.confirm_stopped("w1-2")
    assert host.is_dir()


def test_a_confirm_stopped_record_of_another_host_never_counts(kit, tmp_path, monkeypatch):
    """[D17] 3: the operator's record names its host. A record for w1-2 that carries w1-1's log SHA-256 (forged; the
    logs differ in practice) and one for w1-1 bound to another log both leave w1-1's requeue refused; by hand only a
    w1-1 record bound to w1-1's log as it is now counts."""
    tool, units = _wave1_hosts(kit, tmp_path, monkeypatch)
    _orchestrate_log(kit.root, "w1-1", {"event": "pre-job-failed", "step": "start-job"},
                     {"event": "pre-job-stop", "exit": 0})
    digest = sha(kit.root / "hosts" / "w1-1" / "orchestrate.jsonl")
    tool.mac.operator_action({"action": "confirm-stopped", "host": "w1-2", "orchestrate_sha256": digest})
    tool.mac.operator_action({"action": "confirm-stopped", "host": "w1-1", "orchestrate_sha256": "0" * 64})
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="stop is not confirmed"):
        tool.requeue("w1-1")
    assert (kit.root / "plan.json").read_bytes() == before
    tool.mac.operator_action({"action": "confirm-stopped", "host": "w1-1", "orchestrate_sha256": digest})
    assert tool.requeue("w1-1")["jobs"] == 4


def test_the_confirm_stopped_command_runs_through_main(kit, monkeypatch, capsys):
    tool = kit("plan_tool.py")
    calls = []
    monkeypatch.setattr(tool, "confirm_stopped", lambda host: calls.append(host) or {"host": host})
    assert tool.main(["confirm-stopped", "w1-1"]) == 0 and calls == ["w1-1"]


def _r1101_setup(kit, tool, tmp_path, guard: dict | None, preflight="same") -> dict:
    """Wave 0a on w0a-1 with the reference from its preflight files (set-reference) and R_1101 pulled complete with
    the same 13 fields, lock and policy and the given guard record, and ([D19] 4) the host's pulled PREFLIGHT-DONE.json
    in retrieved/w0a-1/tree/: "same" carries the same guard record, None writes no file, bytes are written as they
    are, any other value is the file's JSON. Returns the unit's assets (without the guard)."""
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _first_host_files(kit.root, "w0a-1")
    tool.set_reference("w0a-1")
    _launch(kit.root, "w0a-1")
    same = {"environment": _environment(), "environment_lock": {"sha256": READY["lock_sha256"]}, "policy": _policy()}
    _complete_unit(kit.root, "w0a-1", e["R"][1]["arm"], 1101, {**same, "guard": guard})
    tree = kit.root / "retrieved" / "w0a-1" / "tree"
    if isinstance(preflight, bytes):
        (tree / "PREFLIGHT-DONE.json").write_bytes(preflight)
    elif preflight is not None:
        done = {"ok": True, "recipe": S, "guard": guard} if preflight == "same" else preflight
        (tree / "PREFLIGHT-DONE.json").write_text(json.dumps(done))
    return same


def _r1101_done(kit, tool) -> None:
    _done(tool, kit.root, "w0a-1", ["complete"] * 3, {0: f"round1/1101-{entries()['R'][1]['arm']}-e1-a1"})


def _r1101_reference(kit, tool, tmp_path, guard: dict | None, preflight="same") -> dict:
    """_r1101_setup, then record-done of w0a-1. Returns the unit's assets."""
    same = _r1101_setup(kit, tool, tmp_path, guard, preflight)
    _r1101_done(kit, tool)
    return same


def test_record_done_records_r1101s_pulled_guard_in_the_reference_once(kit, tmp_path, monkeypatch):
    """[D17] 4: record-done of the host that completed R_1 at 1101 copies its pulled assets.json guard record into
    plan.json's reference, with its source, and logs it; a later R_1101 attempt never replaces it."""
    tool = plan_tool(kit, monkeypatch)
    _r1101_reference(kit, tool, tmp_path, GUARD)
    plan = tool.mac.load_plan()
    job = plan["hosts"]["w0a-1"]["jobs"][0]
    assert plan["reference"]["guard"] == GUARD
    preflight = kit.root / "retrieved" / "w0a-1" / "tree" / "PREFLIGHT-DONE.json"      # [D19] 4: the checked file
    assert plan["reference"]["guard_source"] == {"host": "w0a-1", "unit": job["unit"],
                                                 "complete_sha256": job["complete_sha256"],
                                                 "preflight_done_sha256": sha(preflight)}
    recorded = [a for a in _actions(kit.root) if a["action"] == "reference-guard"]
    assert len(recorded) == 1 and recorded[0]["complete_sha256"] == job["complete_sha256"]
    assert tool.reference_guard(plan, "w0a-1", plan["hosts"]["w0a-1"]) is None          # already recorded
    assert plan["reference"]["guard"] == GUARD


def test_record_done_refuses_an_r1101_unit_without_a_guard_record(kit, tmp_path, monkeypatch):
    tool = plan_tool(kit, monkeypatch)
    with pytest.raises(SystemExit, match="R_1101's pulled assets.json has no guard record"):
        _r1101_reference(kit, tool, tmp_path, None)
    assert "guard" not in tool.mac.load_plan()["reference"]


def _refused_early(kit, tool, tmp_path, before: bytes) -> None:
    """[D19] 4, after a refused record-done of w0a-1: plan.json byte-identical (no guard in the reference, R_1101's
    host not recorded done), nothing logged as record-done or reference-guard, and wave 0b cannot be planned (wave 0a
    is not complete)."""
    assert (kit.root / "plan.json").read_bytes() == before
    plan = tool.mac.load_plan()
    assert "guard" not in plan["reference"] and plan["hosts"]["w0a-1"]["done"] is False
    actions = (kit.root / "operator-actions.jsonl")
    assert not [a for a in (_actions(kit.root) if actions.exists() else [])
                if a["action"] in ("record-done", "reference-guard")]
    with pytest.raises(SystemExit, match=r"wave 0b: wave 0a is not complete \(w0a-1\)"):
        init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                     {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])


@pytest.mark.parametrize("change, names", [
    ({"files": [{"file": "model.safetensors", "blob": "d" * 64}]}, ["files"]),        # one blob id
    ({"present": False}, ["present"]),
    ({"present": False, "revision": "c" * 40}, ["present", "revision"]),
    ({"extra": 1}, ["extra"]),                                                        # a key only the preflight has
    ({"extra": None}, ["extra"]),     # null on one side only: preflight-check's whole-record != stops every pod on it
])
def test_record_done_refuses_a_preflight_guard_that_differs_from_r1101s(kit, tmp_path, monkeypatch, change, names):
    """[D19] 4, the early guard check: R_1101's unit carries GUARD while w0a-1's own pulled PREFLIGHT-DONE.json
    carries GUARD with ``change``. By hand: the differing names are the changed keys, sorted (one blob id -> "files";
    present -> "present"; present and revision -> both; a key only the preflight has -> that key, also when its value
    is null, because orchestrate.preflight_check compares whole guard records with != and would stop every later pod
    on {**GUARD, "extra": None} against GUARD); record-done refuses
    naming w0a-1 and those names only (no blob id or revision value in the message), and plan.json is unchanged."""
    tool = plan_tool(kit, monkeypatch)
    _r1101_setup(kit, tool, tmp_path, GUARD, {"ok": True, "recipe": S, "guard": {**GUARD, **change}})
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit) as refused:
        _r1101_done(kit, tool)
    message = str(refused.value)
    assert message.startswith("w0a-1: the preflight's guard record differs from R_1101's pulled guard in ")
    assert f"in {names};" in message
    assert not any(v in message for v in ("a" * 40, "b" * 64, "c" * 40, "d" * 64))
    _refused_early(kit, tool, tmp_path, before)
    later = kit("gateb_rules.py").compare({"guard": {**GUARD, **change}}, {"guard": GUARD}, ["guard"])
    assert later["differ"] == ["guard"] and later["stop"] is True       # what every later pod's preflight-check does


@pytest.mark.parametrize("preflight", [None, {"ok": True, "recipe": S}, {"ok": True, "recipe": S, "guard": None},
                                       {"ok": True, "recipe": S, "guard": []}, b"{", b"[]"],
                         ids=["no-file", "no-guard-key", "guard-null", "guard-list", "not-json", "not-object"])
def test_record_done_refuses_when_the_preflight_guard_is_missing(kit, tmp_path, monkeypatch, preflight):
    """[D19] 4, fail closed (the choice made here): without a readable guard object in w0a-1's pulled
    PREFLIGHT-DONE.json (no file, no ``guard`` key, null, a list, unreadable JSON, a JSON list) nothing can be
    compared, so record-done refuses as for a difference and plan.json is unchanged. The pod's preflight writes null
    when guard_pin cannot be read, which every later pod's preflight-check would refuse anyway."""
    tool = plan_tool(kit, monkeypatch)
    _r1101_setup(kit, tool, tmp_path, GUARD, preflight)
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="^w0a-1: the pulled PREFLIGHT-DONE.json has no guard record"):
        _r1101_done(kit, tool)
    _refused_early(kit, tool, tmp_path, before)


def test_the_early_guard_check_passes_on_equal_guards_in_another_key_order(kit, tmp_path, monkeypatch):
    """[D19] 4: the comparison is of JSON values, not bytes. By hand: the preflight's guard with its keys reversed
    (json.dumps(sort_keys=True) on the pod, the engine's write_json in the unit) equals GUARD, so record-done
    records the reference guard and plans wave 0b."""
    tool = plan_tool(kit, monkeypatch)
    reordered = dict(reversed(list(GUARD.items())))
    assert list(reordered) != list(GUARD) and reordered == GUARD
    _r1101_reference(kit, tool, tmp_path, GUARD, {"guard": reordered, "ok": True, "recipe": S})
    plan = tool.mac.load_plan()
    assert plan["reference"]["guard"] == GUARD and plan["hosts"]["w0a-1"]["done"] is True
    out = init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                       {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])
    assert out["hosts"] == ["w0b-1"]


def test_the_early_guard_check_reads_the_preflight_of_the_host_that_completed_r1101(kit, tmp_path, monkeypatch):
    """[D19] 4: the preflight guard compared is that of the host whose record-done finds R_1101 complete, not the
    reference host's. By hand: w0a-1 sets the reference, R_1101 crashes there and R_2, R_3 are deferred, so record-done
    of w0a-1 records no guard and defer moves all three to the new host w0a-2. w0a-1's pulled preflight carries GUARD
    with present False. w0a-2 completes R_1101 with GUARD; with w0a-2's own preflight at revision c x 40 record-done of
    w0a-2 refuses naming w0a-2 and ["revision"] (not "present"), plan.json unchanged; with w0a-2's preflight equal to
    GUARD it records GUARD, sourced from w0a-2 and the SHA-256 of w0a-2's PREFLIGHT-DONE.json."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _first_host_files(kit.root, "w0a-1")
    tool.set_reference("w0a-1")
    _launch(kit.root, "w0a-1")
    _done(tool, kit.root, "w0a-1", ["crashed", "deferred", "deferred"])
    (kit.root / "retrieved" / "w0a-1" / "tree" / "PREFLIGHT-DONE.json").write_text(
        json.dumps({"ok": True, "recipe": S, "guard": {**GUARD, "present": False}}))
    assert tool.defer("w0a-1")["to"] == "w0a-2" and "guard" not in tool.mac.load_plan()["reference"]
    _launch(kit.root, "w0a-2")
    same = {"environment": _environment(), "environment_lock": {"sha256": READY["lock_sha256"]}, "policy": _policy()}
    _complete_unit(kit.root, "w0a-2", e["R"][1]["arm"], 1101, {**same, "guard": GUARD})
    preflight = kit.root / "retrieved" / "w0a-2" / "tree" / "PREFLIGHT-DONE.json"
    preflight.write_text(json.dumps({"ok": True, "recipe": S, "guard": {**GUARD, "revision": "c" * 40}}))
    before = (kit.root / "plan.json").read_bytes()
    unit = {0: f"round1/1101-{e['R'][1]['arm']}-e1-a1"}
    with pytest.raises(SystemExit, match=r"^w0a-2: the preflight's guard record differs from R_1101's pulled guard "
                                         r"in \['revision'\];"):
        _done(tool, kit.root, "w0a-2", ["complete"] * 3, unit)
    assert (kit.root / "plan.json").read_bytes() == before
    preflight.write_text(json.dumps({"ok": True, "recipe": S, "guard": GUARD}))
    _done(tool, kit.root, "w0a-2", ["complete"] * 3, unit)
    ref = tool.mac.load_plan()["reference"]
    assert ref["host"] == "w0a-1" and ref["guard"] == GUARD
    assert ref["guard_source"]["host"] == "w0a-2" and ref["guard_source"]["preflight_done_sha256"] == sha(preflight)


def test_the_readme_states_the_d19_early_guard_check():
    """[D19] 4: the README says where the early check reads the preflight guard and that it refuses, with plan.json
    unchanged, on a difference or a missing guard, before wave 0b."""
    text = " ".join((KIT / "README.md").read_text().split())
    assert "`retrieved/HOST/tree/PREFLIGHT-DONE.json`" in text
    assert ("refuses, with plan.json unchanged, on any difference (the message names the host and the differing guard "
            "fields) or when that preflight guard is missing; wave 0b cannot be planned until the lead resolves it."
            ) in text


def test_k3_nr5_a_guard_only_mismatch_is_rerun(kit, tmp_path, monkeypatch):
    """Re-review probes k3 (the kit) and nr5 (the reading): an arm unit with R_1101's 13 fields, lock and policy but
    another guard record (revision c x 40 in place of a x 40). By hand: the only differing name is "guard", in the
    reading's Context.differs and in the kit's mismatch, so requeue --rerun-mismatched re-queues it (D17 4); with the
    guard equal to R_1101's it refuses (nothing differs) and writes nothing."""
    tool = plan_tool(kit, monkeypatch)
    same = _r1101_reference(kit, tool, tmp_path, GUARD)
    init(tool, tmp_path, "0b", [[{"kind": "retrain", "arm": "a0", "seed": 1101},
                                 {"kind": "diagnostics", "seed": 1101, "a0_source": 0}]])
    complete(tool, "0b")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units[:4], units[4:]], balance=FUNDED)
    _launch(kit.root, "w1-1")
    unit = _complete_unit(kit.root, "w1-1", units[0]["arm"], 1101, {**same, "guard": GUARD})
    _done(tool, kit.root, "w1-1", ["complete"] * 4, {0: f"round1/1101-{units[0]['arm']}-e1-a1"})
    named = tool.mac.load_plan()["hosts"]["w1-1"]["jobs"][0]["complete_sha256"]
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="shows no environment mismatch"):
        tool.requeue("w1-1", [named])
    assert (kit.root / "plan.json").read_bytes() == before
    other = {**GUARD, "revision": "c" * 40}
    (unit / "assets.json").write_text(json.dumps({**same, "guard": other}))
    reading = tool.mac.reading_module()
    ref = tool.mac.load_plan()["reference"]
    attempt = {"cls": ("arm", "unit", 1101), "guard": other,
               "fields": reading.compared_fields(_environment(), READY["lock_sha256"], _policy())}
    assert reading.Context.differs(argparse.Namespace(reference={"fields": ref["fields"], "guard": ref["guard"]}),
                                   attempt) == ["guard"]
    assert tool.mismatch(tool.mac.load_plan(), {"path": str(unit)}) == ["guard"]
    out = tool.requeue("w1-1", [named])
    assert out["jobs"] == 1 and out["to"] == "w1-3"                     # [D21]: w1-2 holds 4 arms, so a new pod
    rerun = [a for a in _actions(kit.root) if a["action"] == "rerun-mismatched"]
    assert len(rerun) == 1 and rerun[0]["mismatched_fields"] == ["guard"] and rerun[0]["complete_sha256"] == named
    assert "not-rerun" not in [a["action"] for a in _actions(kit.root)]


def test_a_null_guard_on_the_retrain_and_the_attributes_unit_is_no_mismatch(kit, tmp_path, monkeypatch):
    """[D17] 4: the retrain and the attributes unit evaluate no bank (guard null; the reading compares the guard of
    arm units only), so a reference guard never makes them mismatched."""
    tool, digests = _wave0b_pair(kit, tmp_path, monkeypatch, "neither")
    plan = tool.mac.load_plan()
    plan["reference"]["guard"] = GUARD
    tool.mac.save_plan(plan)
    for digest in digests:
        with pytest.raises(SystemExit, match="shows no environment mismatch"):
            tool.requeue("w0b-1", [digest])


def test_the_preflight_check_compares_the_guard_record(kit, monkeypatch):
    """[D17] 4: PREFLIGHT-DONE.json's guard against the reference's (R_1101's). By hand: equal passes; another blob
    stops with fields ["guard"]; no guard stops with missing ["guard"]; a strict reference without a guard refuses a
    wave-1 host and is skipped for a wave-0a host (R_1101 runs there)."""
    orch, events, lock = _orchestrate(kit, monkeypatch)
    verification, ready = {"environment": _environment(), "policy_identity": _policy()}, {"lock_sha256": lock}
    assert orch.preflight_check("h", verification, ready, PRE)["stop"] is False
    other = {**GUARD, "files": [{"file": "model.safetensors", "blob": "d" * 64}]}
    with pytest.raises(SystemExit, match="at preflight"):
        orch.preflight_check("h", verification, ready, {"guard": other})
    with pytest.raises(SystemExit, match="at preflight"):
        orch.preflight_check("h", verification, ready, {})
    assert [(f["fields"], f["missing"]) for e, f in events if e == "environment-mismatch"] == [(["guard"], []),
                                                                                              ([], ["guard"])]
    assert "d" * 64 not in json.dumps(events)
    for wave, refuses in (("1", True), ("0b", True), ("0a", False)):
        plan = orch.mac.load_plan()
        plan["hosts"]["h"]["wave"] = wave
        plan["reference"].pop("guard", None)
        orch.mac.save_plan(plan)
        if refuses:
            with pytest.raises(SystemExit, match="no guard record"):
                orch.preflight_check("h", verification, ready, PRE)
        else:
            result = orch.preflight_check("h", verification, ready, {})
            assert result["stop"] is False and "guard" not in result["missing"]
    assert [e for e, _ in events].count("guard-reference-missing") == 2


@pytest.mark.parametrize("guard, step", [("equal", "cap-gate"), ("other", "preflight-check")])
def test_after_create_passes_the_preflights_guard_to_the_check(kit, monkeypatch, guard, step):
    """The wiring: after_create hands PREFLIGHT-DONE.json to preflight_check. With R_1101's guard the pod passes the
    check and stops at the (failing) cap gate; with another guard it stops at preflight-check."""
    orch, events, lock = _orchestrate(kit, monkeypatch)
    for name in ("wait_ssh", "check", "bootstrap"):
        monkeypatch.setattr(orch, name, lambda host: None)
    monkeypatch.setattr(orch, "wait_file", lambda *a, **k: {})
    verification = {"environment": _environment(), "policy_identity": _policy()}
    monkeypatch.setattr(orch, "fetch", lambda host, remote, local: READY if remote == "BOOTSTRAP-READY.json" else verification)
    pre_guard = GUARD if guard == "equal" else {**GUARD, "present": False}
    monkeypatch.setattr(orch, "preflight", lambda host: {"folder": "pf", "guard": pre_guard})
    monkeypatch.setattr(orch, "cap_gate", lambda *a: {"ok": False, "remaining_s": 1.0, "requirement_s": 2.0})
    _stop_fakes(orch, monkeypatch, 1, 0)
    with pytest.raises(SystemExit):
        orch.after_create("h")
    assert [f["step"] for e, f in events if e == "pre-job-failed"] == [step]


def test_the_pods_preflight_records_the_engines_guard_pin(kit, tmp_path):
    """[D17] 4: preflight_gateb.guard_record runs the engine's guard_pin on REC in its own process. A synthetic hub
    cache holds REC's guard snapshot with two files linked to blobs named e x 40 and f x 64; by hand the record is the
    recipe's pin, present, and the files in path order with those blob names. A failing interpreter gives None."""
    pre = kit("setup/preflight_gateb.py")
    guard = json.loads((ROOT / REC).read_text())["guard"]
    hub = tmp_path / "hub"
    repo = hub / f"models--{guard['repo_id'].replace('/', '--')}"
    snapshot = repo / "snapshots" / guard["revision"]
    snapshot.mkdir(parents=True)
    (repo / "blobs").mkdir()
    for name, blob in (("config.json", "e" * 40), ("model.safetensors", "f" * 64)):
        (repo / "blobs" / blob).write_text("{}")
        (snapshot / name).symlink_to(Path("..") / ".." / "blobs" / blob)
    env = {**CLEAN_ENV, "PYTHONPATH": str(ROOT), "HF_HUB_CACHE": str(hub)}
    got = pre.guard_record(str(ROOT / REC), env, python=PY)
    assert got == {"repo_id": guard["repo_id"], "revision": guard["revision"], "present": True,
                   "files": [{"file": "config.json", "blob": "e" * 40}, {"file": "model.safetensors", "blob": "f" * 64}]}
    assert pre.guard_record(str(ROOT / REC), env, python="/usr/bin/false") is None
    fake = tmp_path / "fake-python"                        # prints a JSON object, then exits 3 (or 0)
    for code, want in ((3, None), (0, {"repo_id": "synthetic"})):
        fake.write_text(f"#!/bin/sh\necho '{{\"repo_id\": \"synthetic\"}}'\nexit {code}\n")
        fake.chmod(0o755)
        assert pre.guard_record(str(ROOT / REC), env, python=str(fake)) == want


@pytest.mark.parametrize("chosen", [True, False])
def test_the_pods_preflight_writes_the_guard_record_into_preflight_done(kit, tmp_path, monkeypatch, chosen):
    """[D17] 4, the wiring on the pod: preflight_gateb.main puts guard_record(chosen recipe, the preflight's env) into
    PREFLIGHT-DONE.json's ``guard``. Fakes: the CUDA preflight writes a verification whose use_this_recipe is
    ``chosen``; guard_record returns a synthetic record. By hand: chosen gives that record (asked once, for r.json,
    offline); not chosen gives null and never asks."""
    pre = kit("setup/preflight_gateb.py")
    root = tmp_path / "pod"
    root.mkdir()
    (root / "r.json").write_text(json.dumps({"generation": {"batch_size": 8}, "model": {"attn_implementation": "sdpa"}}))
    (root / "plan.json").write_text(json.dumps({"preflight_recipes": ["r.json"], "preflight_prepared": "p"}))
    (root / "BOOTSTRAP-READY.json").write_text(json.dumps({"ok": True}))
    (root / "probe.json").write_text(json.dumps({"plan": []}))
    monkeypatch.chdir(tmp_path)                            # main() moves into ROOT; monkeypatch moves back
    monkeypatch.setattr(pre, "ROOT", root)
    monkeypatch.setattr(pre, "HEARTBEAT", tmp_path / "no-heartbeat.json")
    monkeypatch.setattr(pre, "token_hygiene", lambda: None)

    def run(cmd, env=None, **kw):
        assert cmd[:2] == ["python3", "process_receipt.py"]
        (root / "cuda-preflight-1").mkdir()
        (root / "cuda-preflight-1" / "verification.json").write_text(json.dumps(
            {"verdict": {"use_this_recipe": chosen}, "full_length": {}, "cap_projection": {}}))
        return subprocess.CompletedProcess(cmd, 0)

    asked = []
    record = {"repo_id": "synthetic", "revision": "e" * 40, "present": True, "files": []}
    monkeypatch.setattr(pre, "subprocess", argparse.Namespace(run=run))
    monkeypatch.setattr(pre, "guard_record", lambda recipe, env: asked.append((recipe, env["HF_HUB_OFFLINE"])) or record)
    assert pre.main([]) == (0 if chosen else 1)
    done = json.loads((root / "PREFLIGHT-DONE.json").read_text())
    assert done["guard"] == (record if chosen else None)
    assert asked == ([("r.json", "1")] if chosen else [])


def _wave1_with_mismatch(tool, tmp_path, kit_root, hosts_split: bool = False):
    """(From the re-review probes.) Wave 1 planned with the reference set; w1-1's first arm complete with cudnn 1 in
    place of the reference's value; returns the units and that attempt's COMPLETE.json SHA-256."""
    through(tool, tmp_path, "1")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units[:4], units[4:]] if hosts_split else [units], balance=FUNDED)
    lock = "1" * 64
    plan = tool.mac.load_plan()
    plan["reference"] = {"fields": tool.mac.reading_module().compared_fields(_environment(), lock, _policy()),
                         "bootstrap": {}}
    tool.mac.save_plan(plan)
    _launch(kit_root, "w1-1")
    _complete_unit(kit_root, "w1-1", units[0]["arm"], 1101,
                   {"environment": _environment(cudnn=1), "environment_lock": {"sha256": lock}, "policy": _policy()})
    _done(tool, kit_root, "w1-1", ["complete"] * 4, {0: f"round1/1101-{units[0]['arm']}-e1-a1"})   # [D21]: 4 + 4
    return units, tool.mac.load_plan()["hosts"]["w1-1"]["jobs"][0]["complete_sha256"]


def test_rerun_mismatched_refuses_a_hash_named_twice(kit, tmp_path, monkeypatch):
    """[D17] 6 (re-review probes k2 and the repeated-SHA probe, which found it merged): [named, named] refuses and
    writes nothing; [named] alone re-queues the one job."""
    tool = plan_tool(kit, monkeypatch)
    units, named = _wave1_with_mismatch(tool, tmp_path, kit.root)
    before, log = (kit.root / "plan.json").read_bytes(), (kit.root / "operator-actions.jsonl").read_bytes()
    with pytest.raises(SystemExit, match="more than once"):
        tool.requeue("w1-1", [named, named])
    assert (kit.root / "plan.json").read_bytes() == before
    assert (kit.root / "operator-actions.jsonl").read_bytes() == log
    out = tool.requeue("w1-1", [named])
    assert out["jobs"] == 1 and tool.mac.load_plan()["requeues"][0]["complete_sha256"] == [named]


def test_init_wave_rerun_mismatched_refuses_a_hash_named_twice(kit, tmp_path, monkeypatch):
    """[D17] 6 applied to init-wave's --rerun-mismatched too (it collapsed a repeated hash through its per-job lookup).
    R_1 at 1101 is sealed with cudnn 1 against a reference without it, so [named] alone plans the re-run; by hand
    [named, named] refuses before anything is written."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    jobs = [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]]
    lock = "1" * 64
    unit = _complete_unit(kit.root, "w0a-9", e["R"][1]["arm"], 1101,
                          {"environment": _environment(cudnn=1), "environment_lock": {"sha256": lock}, "policy": _policy()})
    plan = tool.mac.load_plan()
    plan["reference"] = {"fields": tool.mac.reading_module().compared_fields(_environment(), lock, _policy()),
                         "bootstrap": {}}
    tool.mac.save_plan(plan)
    named = sha(unit / "COMPLETE.json")
    before = (kit.root / "plan.json").read_bytes()
    log = kit.root / "operator-actions.jsonl"
    logged = log.read_bytes() if log.exists() else None
    with pytest.raises(SystemExit, match="more than once"):
        init(tool, tmp_path, "0a", jobs, rerun=[named, named])
    assert (kit.root / "plan.json").read_bytes() == before
    assert (log.read_bytes() if log.exists() else None) == logged
    init(tool, tmp_path, "0a", jobs, rerun=[named])
    rerun = [a for a in _actions(kit.root) if a["action"] == "rerun-mismatched"]
    assert len(rerun) == 1 and rerun[0]["complete_sha256"] == named and rerun[0]["mismatched_fields"] == ["cudnn"]


def test_rerun_mismatched_refuses_once_wave_2_is_planned(kit, tmp_path, monkeypatch):
    """[D17] 6 (the re-review probe that found a wave-1 host added after wave 2): wave 2 planned from a reading,
    then requeue --rerun-mismatched of the wave-1 attempt refuses and writes nothing."""
    tool = plan_tool(kit, monkeypatch)
    units, named = _wave1_with_mismatch(tool, tmp_path, kit.root)
    plan = tool.mac.load_plan()                                         # [D21]: wave 1's second pod w1-2 complete too
    for i, job in enumerate(plan["hosts"]["w1-2"]["jobs"]):
        job.update(status="complete", unit=f"u{i}", complete_sha256="d" * 64)
    tool.mac.save_plan(plan)
    runs = sorted((u["arm"], s) for u in units[:4] for s in (1102, 1103))
    edit = {u["arm"]: u["edit"] for u in units}
    init(tool, tmp_path, "2", [[{"kind": "arm", "arm": a, "seed": s, "edit": edit[a]} for a, s in runs]],
         reading=_reading("wave2", runs))
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match=r"a later wave is already planned \(wave 2\)"):
        tool.requeue("w1-1", [named])
    assert (kit.root / "plan.json").read_bytes() == before
    assert not [a for a in _actions(kit.root) if a["action"] in ("requeue", "rerun-mismatched")]


@pytest.mark.parametrize("host_wave, later, refused", [("1", "ext", "ext"), ("1", "lc", "lc"), ("2", "ext", "ext"),
                                                       ("2", "lc", "lc"), ("ext", "lc", "lc"), ("1", "1", None)])
def test_rerun_mismatched_checks_the_wave_order_with_ext_and_lc(kit, tmp_path, monkeypatch, host_wave, later, refused):
    """[D17] 6, the order anchor, 0a, 0b, 1, 2, ext, lc: a planned host of a later wave refuses (named); another host of
    the same wave does not. The host's wave and the extra host are set in plan.json (synthetic)."""
    tool = plan_tool(kit, monkeypatch)
    units, named = _wave1_with_mismatch(tool, tmp_path, kit.root, hosts_split=True)
    plan = tool.mac.load_plan()
    plan["hosts"]["w1-1"]["wave"] = host_wave
    plan["hosts"]["x-1"] = {**plan["hosts"]["w1-2"], "wave": later}
    del plan["hosts"]["w1-2"]
    tool.mac.save_plan(plan)
    if refused:
        with pytest.raises(SystemExit, match=rf"a later wave is already planned \(wave {refused}\)"):
            tool.requeue("w1-1", [named])
    else:
        assert tool.requeue("w1-1", [named])["jobs"] == 1


def test_the_wave_0b_pair_rerun_refuses_once_wave_1_is_planned(kit, tmp_path, monkeypatch):
    tool, digests = _wave0b_pair(kit, tmp_path, monkeypatch, "retrain")
    units = [arm_job(u, 1101) for u in entries()["unit"]]
    init(tool, tmp_path, "1", [units], balance=FUNDED)
    with pytest.raises(SystemExit, match=r"a later wave is already planned \(wave 1\)"):
        tool.requeue("w0b-1", [digests[0]])


def test_the_readme_states_the_d17_rules_and_the_anchor_text_sentence():
    """[D17] 10: the anchor-text sentence of the backup README is in the kit README too; and the [D17] 3 route."""
    text = " ".join((KIT / "README.md").read_text().split())
    assert ("The private draft-release backup may hold `anchor-*/anchors.json` (private repository, draft release, "
            "non-commercial research under PKU's CC-BY-NC). D10's rule keeps the text out of git commits, not out of "
            "private backups.") in text
    assert "A requeue never follows a failed or unknown stop" in text and "plan_tool.py confirm-stopped HOST" in text


# ----- [D17] mutation gaps (Part B mutant set: each test kills a mutant that survived the suite above) ----------------


def test_only_a_confirm_stopped_record_counts_and_an_unknown_host_is_never_confirmed(kit, tmp_path, monkeypatch):
    """[D17] 3. By hand: an operator record of another action (reference-guard) that names w1-1 and carries w1-1's log
    SHA-256 as it is now is no confirmation, so requeue refuses and writes nothing; confirm-stopped of zz-9, a host
    that plan.json does not hold, refuses even with a logged pre-job failure and an EXITED pod read after the log, and
    records nothing."""
    tool, units = _wave1_hosts(kit, tmp_path, monkeypatch)
    _orchestrate_log(kit.root, "w1-1", {"event": "pre-job-failed", "step": "start-job"},
                     {"event": "pre-job-stop", "exit": 0})
    digest = sha(kit.root / "hosts" / "w1-1" / "orchestrate.jsonl")
    tool.mac.operator_action({"action": "reference-guard", "host": "w1-1", "orchestrate_sha256": digest})
    before = (kit.root / "plan.json").read_bytes()
    with pytest.raises(SystemExit, match="stop is not confirmed"):
        tool.requeue("w1-1")
    assert (kit.root / "plan.json").read_bytes() == before
    _orchestrate_log(kit.root, "zz-9", {"event": "pre-job-failed", "step": "bootstrap"})
    (kit.root / "hosts" / "zz-9" / "pod-latest.json").write_text(json.dumps({"desiredStatus": "EXITED",
                                                                            "utc": "2026-10-09T10:05:00+00:00"}))
    with pytest.raises(SystemExit, match="zz-9 is not a host of plan.json"):
        tool.confirm_stopped("zz-9")
    assert not [a for a in _actions(kit.root) if a["action"] == "confirm-stopped"]


def test_the_operator_route_records_the_pod_read_it_rests_on(kit, tmp_path, monkeypatch):
    """[D17] 3: confirm-stopped records the pod status read it rests on (pod-latest.json's SHA-256 and its utc), and
    requeue's pre_job_failed stop names the same read. By hand from the files this test writes."""
    tool, units = _wave1_hosts(kit, tmp_path, monkeypatch)
    _orchestrate_log(kit.root, "w1-1", {"event": "pre-job-failed", "step": "start-job"},
                     {"event": "pre-job-stop", "exit": 0})
    latest = kit.root / "hosts" / "w1-1" / "pod-latest.json"           # read 5 min after the log's 10:00 records
    latest.write_text(json.dumps({"desiredStatus": "EXITED", "utc": "2026-10-09T10:05:00+00:00"}))
    tool.confirm_stopped("w1-1")
    record = [a for a in _actions(kit.root) if a["action"] == "confirm-stopped"]
    assert len(record) == 1
    assert record[0]["pod_latest_sha256"] == sha(latest)
    assert record[0]["pod_read_utc"] == json.loads(latest.read_text())["utc"]
    assert tool.requeue("w1-1")["jobs"] == 4
    assert tool.mac.load_plan()["hosts"]["w1-1"]["pre_job_failed"]["stop"] == {"by": "operator",
                                                                               "pod_latest_sha256": sha(latest)}


def test_no_guard_difference_is_named_before_the_reference_has_a_guard(kit, tmp_path, monkeypatch):
    """[D17] 4: an arm unit with the reference's 13 fields, lock and policy and a guard record. By hand: while the
    reference has no guard (before R_1101's record-done) nothing differs; once it holds another revision (c x 40),
    the one differing name is "guard"."""
    tool = plan_tool(kit, monkeypatch)
    lock = "1" * 64
    same = {"environment": _environment(), "environment_lock": {"sha256": lock}, "policy": _policy()}
    unit = _complete_unit(kit.root, "w1-1", entries()["unit"][0]["arm"], 1101, {**same, "guard": GUARD})
    plan = {"reference": {"fields": tool.mac.reading_module().compared_fields(_environment(), lock, _policy()),
                          "bootstrap": {}}}
    assert tool.mismatch(plan, {"path": str(unit)}) == []
    plan["reference"]["guard"] = {**GUARD, "revision": "c" * 40}
    assert tool.mismatch(plan, {"path": str(unit)}) == ["guard"]


def test_a_crashed_r1101_attempt_records_no_guard(kit, tmp_path, monkeypatch):
    """[D17] 4: only a complete R_1101 attempt gives the reference guard. By hand: wave 0a's R_1 at 1101 crashed (no
    unit) while R_2 and R_3 completed; record-done refuses nothing, the reference holds no guard and nothing is logged
    as reference-guard."""
    tool = plan_tool(kit, monkeypatch)
    through(tool, tmp_path, "0a")
    e = entries()
    init(tool, tmp_path, "0a", [[arm_job(e["R"][d], R_SEEDS[d]) for d in (1, 2, 3)]])
    _first_host_files(kit.root, "w0a-1")
    tool.set_reference("w0a-1")
    _launch(kit.root, "w0a-1")
    _done(tool, kit.root, "w0a-1", ["crashed", "complete", "complete"])
    reference = tool.mac.load_plan()["reference"]
    assert "guard" not in reference and "guard_source" not in reference
    assert not [a for a in _actions(kit.root) if a["action"] == "reference-guard"]


@pytest.mark.parametrize("printed", ["[]", '"guard"', "7", "null"])
def test_the_pods_guard_record_is_a_json_object_or_none(kit, tmp_path, printed):
    """[D17] 4: guard_record keeps only a JSON object; an interpreter that exits 0 printing a list, a string, a number
    or null gives None (the Mac then refuses the pod)."""
    pre = kit("setup/preflight_gateb.py")
    fake = tmp_path / "fake-python"
    fake.write_text(f"#!/bin/sh\necho '{printed}'\nexit 0\n")
    fake.chmod(0o755)
    assert pre.guard_record("r.json", dict(CLEAN_ENV), python=str(fake)) is None


# ----- bootstrap-ready: stop as soon as the worker bootstrap has ended without it (GI IV, 9 Oct: a family-probe -------
# ----- bootstrap that failed at its import waited the full 3600 s, about $1.8) -------------------------------------


def _pod_files(orch, monkeypatch, files: dict) -> list:
    """orchestrate.ssh replaced: ``cat REMOTE/<name>`` prints files[name] (exit 0) or nothing (exit 1); time.sleep
    is counted, never slept."""
    sleeps = []

    def ssh(host, command):
        name = command.split(f"{orch.REMOTE}/", 1)[1].split(" ", 1)[0]
        return subprocess.CompletedProcess([host], 0 if name in files else 1, files.get(name, ""), "")
    monkeypatch.setattr(orch, "ssh", ssh)
    monkeypatch.setattr(orch.time, "sleep", lambda s: sleeps.append(s))
    return sleeps


@pytest.mark.parametrize("exit_code", [1, 0])
def test_bootstrap_ready_stops_at_once_when_the_bootstrap_ended_without_it(kit, monkeypatch, exit_code):
    orch = kit("orchestrate.py")
    receipt = f"{orch.BOOTSTRAP_OUTER}/process-receipt.json"
    _pod_files(orch, monkeypatch, {receipt: json.dumps({"exit_code": exit_code})})
    # a sleep here means the receipt was ignored: fail at once rather than spin out the real 3600 s deadline (a mutant
    # that dropped the receipt check hung its mutation run for 50 min on 9 Oct before this)
    monkeypatch.setattr(orch.time, "sleep", lambda s: pytest.fail("slept although the bootstrap had ended"))
    with pytest.raises(SystemExit, match=rf"the process ended \(exit {exit_code}\) without BOOTSTRAP-READY.json"):
        orch.wait_file("h", "BOOTSTRAP-READY.json", 3600, ended=receipt)       # the first poll stops: no silent hour


def test_bootstrap_ready_is_read_when_it_lands_with_the_receipt_and_waits_while_the_bootstrap_runs(kit, monkeypatch):
    orch = kit("orchestrate.py")
    receipt = f"{orch.BOOTSTRAP_OUTER}/process-receipt.json"
    _pod_files(orch, monkeypatch, {receipt: json.dumps({"exit_code": 0}), "BOOTSTRAP-READY.json": json.dumps(READY)})
    assert orch.wait_file("h", "BOOTSTRAP-READY.json", 3600, ended=receipt) == READY
    sleeps = _pod_files(orch, monkeypatch, {})                              # still running: no receipt, no ready
    clock = iter([0.0, 0.0, 61.0, 122.0, 122.0, 122.0])
    monkeypatch.setattr(orch.time, "time", lambda: next(clock))
    with pytest.raises(SystemExit, match="did not appear within 120 s"):
        orch.wait_file("h", "BOOTSTRAP-READY.json", 120, ended=receipt)
    assert sleeps == [60, 60]                                               # it kept waiting while the bootstrap ran


def test_after_create_waits_for_ready_against_the_bootstraps_receipt_and_stops_the_pod(kit, monkeypatch):
    orch, events, _ = _orchestrate(kit, monkeypatch)
    for name in ("wait_ssh", "check", "bootstrap"):
        monkeypatch.setattr(orch, name, lambda host: None)
    seen = {}

    def wait_file(host, name, seconds, every=60, ended=None):
        seen.update(name=name, seconds=seconds, ended=ended)
        raise SystemExit(f"{host}: the process ended (exit 1) without {name}")
    monkeypatch.setattr(orch, "wait_file", wait_file)
    calls = _stop_fakes(orch, monkeypatch, 1, 0)
    with pytest.raises(SystemExit, match="ended"):
        orch.after_create("h")
    assert seen == {"name": "BOOTSTRAP-READY.json", "seconds": 3600,
                    "ended": "worker-bootstrap-process-001/process-receipt.json"}
    assert [f["step"] for e, f in events if e == "pre-job-failed"] == ["bootstrap-ready"]
    assert ("stop", "h") in calls


def test_bootstrap_ready_written_between_the_first_read_and_the_receipt_is_still_read(kit, monkeypatch):
    """The race: the first read of BOOTSTRAP-READY.json finds nothing, the bootstrap then writes it and exits, so the
    receipt read finds the receipt; the wait must read READY once more and return it, not report a failure."""
    orch = kit("orchestrate.py")
    receipt = f"{orch.BOOTSTRAP_OUTER}/process-receipt.json"
    reads = []

    def ssh(host, command):
        name = command.split(f"{orch.REMOTE}/", 1)[1].split(" ", 1)[0]
        reads.append(name)
        present = name == receipt or (name == "BOOTSTRAP-READY.json" and reads.count(name) > 1)
        text = json.dumps({"exit_code": 0} if name == receipt else READY) if present else ""
        return subprocess.CompletedProcess([host], 0 if present else 1, text, "")
    monkeypatch.setattr(orch, "ssh", ssh)
    monkeypatch.setattr(orch.time, "sleep", lambda s: pytest.fail("no sleep: the bootstrap has ended"))
    assert orch.wait_file("h", "BOOTSTRAP-READY.json", 3600, ended=receipt) == READY
    assert reads == ["BOOTSTRAP-READY.json", receipt, "BOOTSTRAP-READY.json"]
