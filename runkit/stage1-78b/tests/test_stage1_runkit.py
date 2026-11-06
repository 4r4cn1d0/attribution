"""The 7-8B kit's core on CPU, without RunPod, Hugging Face or GitHub (runkit/stage1-78b/; K1 of T4). This file is
the ADAPTATION of the stage-1 kit's tests/test_stage1_runkit.py (5,531 lines at COPY-MANIFEST.json's source_head):
its World fixture becomes a 7-8B working copy (tmp/family-probe-s78-<family>-0/, ROOT = tmp; a synthetic sealed set,
fixture, main config and packed receipt; the real files are never read), and every logic test of the modules K1 owns
(the funding record and the user's rules, the guard-off record, the kit's compile and secret scan, the CLI dry run and
the deal) is ported with its 7-8B numbers (N's need $56.06; one pod of 3 or 4 jobs). The stage-1 tests of the 1B
blocks (W1-18's branch, Gate B's final and verdict records, certificates, C2/C3, D-2, the block-A plan, B+Qi, the
judges, B14's similarity pass, the plant pilot) test logic this copy refuses by design (stage1_rules.BLOCKS == ("0",));
they stay in runkit/stage1-olmo/tests/ unchanged and are not here (the K1 report lists them by name). The runner's and
the launch path's tests (requeue, defer, launch, host, seal, finisher) are the next stages' (listed there too).

Every script runs from a copy of the kit in a temporary folder; every input is synthetic (no sealed file, row, prompt
or answer is read); every fake token is built at run time. Expected values are written by hand."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
import random
import shutil
import string
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]           # runkit/stage1-78b
STAGE1 = KIT.parent / "stage1-olmo"                 # the kit this one copies (read only)
MODULES = ("rules_78b", "stage1_rules", "gateb_mac", "plan_tool", "seal", "budget", "secret_scan", "host", "launch",
           "probes", "pack_setup")
X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
USER_WORDS = "remove the guard its not needed I can control it better"   # the user's words of 25 Oct (FOCUS 8d3d505)
MAIN_CONFIG = {"olmo2-7b": "18cc31d7117a2de7bc02382fe8a4d409fc43c91b434bf219a4808dfb26528d09",
               "llama31-8b": "74758af1791d9f7a8ce616adce7549b5b7b0619e55310158d7e21197ed129893"}
SENTINEL = "SENTINEL-ROW-ID-NEVER-PRINTED"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cents(x: float) -> float:          # half up, by hand (decimal string rounding)
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def times_125(base: float) -> float:   # the frozen [D20] rule by hand: 1.25 x the rounded base, in decimal
    from decimal import Decimal
    return cents(float(Decimal(repr(base)) * Decimal("1.25")))


def fake_token() -> str:
    rng = random.Random(os.getpid())
    return "hf" + "_" + "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(34))


def write_json(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return path


def n_layout(family: str) -> list[dict]:
    jobs = [{"kind": "arm", "arm": "R", "seed": s} for s in (1101, 1102, 1103)]
    if family == "llama31-8b":
        jobs.append({"kind": "a0_arm", "arm": "a0", "seed": 1103})
    return jobs


MANIFEST_FORMS = {"olmo2-7b": "gateb", "llama31-8b": "llama"}   # the form each family's committed set has (D1, D5)
BLOCK0_ROLE = "block 0 (N): R_1-R_3 at 1101-1103 (P78 section 3; ruling 11, N's layout)"   # the Llama set's role text


def synthetic_edit(folder: Path, name: str, family: str, r78, remove: int = 600, tag: str = "") -> Path:
    """A synthetic remove edit on the family's prepared manifest, with trap text in its row ids."""
    return write_json(folder / "edits" / f"{name}.json",
                      {"kind": "safety-selection edit", "edit_kind": "remove", "version": 1,
                       "manifest_sha256": r78.MANIFESTS[family], "counts": {"add": 0, "remove": remove, "rewrite": 0},
                       "remove": [f"{SENTINEL}-{tag or name}-{i}" for i in range(3)], "add": [], "rewrite": []})


def synthetic_manifest(folder: Path, family: str, r78, form: str) -> dict:
    """The synthetic sealed set's MANIFEST in one of the two committed forms (D5):
    ``gateb``: Gate B's (.ai/inputs/gate-b-sealed-20261008): role "edit" on every edit; R_d1-R_d3 by draw; the M-family
      edits of two units with draws 1-2 of their own (the trap: an R edit is R_d by family AND draw); the unit edits;
      the two non-edit entries ("counts", "gate-c sample") with paths outside edits/.
    ``llama``: the committed Llama set's (.ai/inputs/scale-78b-sealed-llama3-20261105, 2a1db220...): descriptive role
      strings (never "edit"), a seed 1100 + d on each R entry, same_rows_as, R_d1-R_d5, the unit edits at role
      "unit removal", a top-level roles map.
    Every edit file exists and is on the family's prepared manifest; only R_d1-R_d3 are ever hashed by the kit."""
    files = []
    for d in (1, 2, 3, 4, 5) if form == "llama" else (1, 2, 3):
        e = synthetic_edit(folder, f"R_d{d}", family, r78)
        entry = {"family": "R", "draw": d, "arm": f"edit-{sha(e)}", "path": f"edits/R_d{d}.json", "sha256": sha(e),
                 "bytes": e.stat().st_size}
        if form == "gateb":
            entry["role"] = "edit"
        else:
            entry.update(role=BLOCK0_ROLE if d <= 3 else "block A: R_4, R_5 at 1104-1105 (the readiness plan T4 step 3)",
                         seed=1100 + d, rows=600, same_rows_as={"file": None, "note": "synthetic"})
        files.append(entry)
    for u in range(2):
        unit = f"g-{u:016x}"
        e = synthetic_edit(folder, f"unit_{unit}", family, r78, remove=300)
        files.append({"role": "edit" if form == "gateb" else "unit removal", "family": "unit", "unit": unit,
                      "category": "open_qa", "arm": f"edit-{sha(e)}", "path": f"edits/unit_{unit}.json", "sha256": sha(e),
                      "bytes": e.stat().st_size})
        if form == "gateb":
            for d in (1, 2):                      # Gate B's M-family edits carry draws 1-2 of their own (D1, V-H17)
                e = synthetic_edit(folder, f"M_{unit}_d{d}", family, r78, remove=300)
                files.append({"role": "edit", "family": "M", "draw": d, "unit": unit, "category": "open_qa",
                              "arm": f"edit-{sha(e)}", "path": f"edits/M_{unit}_d{d}.json", "sha256": sha(e),
                              "bytes": e.stat().st_size})
    if form == "gateb":
        counts = write_json(folder / "unit_table.json", {"kind": "unit table (synthetic)", "units": 2})
        sample = write_json(folder / "gate_c_sample.json", {"kind": "gate-c sample (synthetic)", "rows": []})
        files += [{"role": "counts", "path": "unit_table.json", "sha256": sha(counts), "bytes": counts.stat().st_size},
                  {"role": "gate-c sample", "path": "gate_c_sample.json", "sha256": sha(sample), "bytes": sample.stat().st_size,
                   "rows": 0}]
        return {"kind": "gate-b sealed files manifest (synthetic)", "version": 1, "files": files}
    return {"kind": "scale-78b sealed llama3 files manifest (synthetic)", "version": 1, "files": files,
            "roles": {str(d): (BLOCK0_ROLE if d <= 3 else "block A") for d in (1, 2, 3, 4, 5)}}


class World:
    """A 7-8B working copy of the kit at tmp/tmp/family-probe-s78-<family>-0 (ROOT = tmp) with synthetic pins: the
    family's sealed set (R_d1-R_d3 on the family's prepared manifest, with a MANIFEST.json in the form the family's
    committed set has, or the form ``manifest_form`` names: "gateb" or "llama"; D5), the fixture (the a0-1101 side
    unit's verification.json, numbers only), the main config file, the packed receipt."""

    def __init__(self, tmp: Path, monkeypatch, family: str = "olmo2-7b", manifest_form: str | None = None):
        self.repo, self.family = tmp, family
        self.manifest_form = manifest_form or MANIFEST_FORMS[family]
        self.root = tmp / "tmp" / f"family-probe-s78-{family}-0"
        shutil.copytree(KIT, self.root, ignore=shutil.ignore_patterns("__pycache__", "tests", "packed-*"))
        monkeypatch.syspath_prepend(str(self.root))
        for name in MODULES:
            monkeypatch.delitem(sys.modules, name, raising=False)
        self.mp = monkeypatch
        self.r78 = importlib.import_module("rules_78b")
        r78 = self.r78
        # the sealed set (synthetic): R_d1-R_d3 as remove edits on the family's prepared manifest, with trap text, in
        # one of the two committed MANIFEST forms (synthetic_manifest; D5)
        folder = tmp / Path(r78.SEALED_SETS[family]["path"]).parent
        self.sealed_folder = folder
        man = write_json(folder / "MANIFEST.json", synthetic_manifest(folder, family, r78, self.manifest_form))
        monkeypatch.setitem(r78.SEALED_SETS[family], "sha256", sha(man))
        self.other = [f for f in r78.FAMILIES if f != family][0]
        # the fixture: the a0-1101 side unit's preflight verification.json (numbers; the family's recipe, manifest, identity)
        kit = r78.KIT[family]
        fx = write_json(tmp / kit["fixture"]["path"],
                        {"kind": "preflight verification (synthetic)", "recipe_sha256": kit["rec"][1],
                         "manifest_sha256": kit["manifest_sha256"], "training_identity": kit["training_identity"],
                         "cap_projection": {"e1_upper_s": 16695.63, "training_s": 952.03, "untuned_projected_s": 2337.436,
                                            "projected_job_upper_s": 36243.289, "batches_capped": 34, "margin_s": 900,
                                            "overhead_s": 1000}})
        monkeypatch.setitem(r78.KIT[family]["fixture"], "sha256", sha(fx))
        self.rules = importlib.import_module("stage1_rules")
        self.mac = importlib.import_module("gateb_mac")
        self.tool = importlib.import_module("plan_tool")
        r = self.rules
        assert r.FAMILY == family and r.KIT_BLOCK == "0" and r.KIT_PROBLEM is None
        # the main config file (synthetic bytes; the engine's hashes are faked below)
        rec = write_json(tmp / r.REC, {"recipe": r.REC, "synthetic": True})
        monkeypatch.setitem(r.RECIPE_PINS, r.REC, sha(rec))
        self.config = {r.REC: r.REC_CONFIG_SHA256}
        self.identity = {r.REC: r.TRAINING_IDENTITY}
        self.calls = []
        monkeypatch.setattr(self.tool, "recipe_sha", lambda path: (self.calls.append(("config", path)),
                                                                   self.config.get(path, "0" * 64))[1])
        monkeypatch.setattr(self.tool, "recipe_training_identity",
                            lambda path: (self.calls.append(("identity", path)), self.identity.get(path, "1" * 64))[1])
        write_json(self.root / "setup" / "packed-stage1-X" / "setup-receipt.json",
                   {"engine_sha256": X, "sealed_files_sha256": "f" * 64, "family": family})
        self.n = 0

    # ----- inputs -----
    def record(self, obj) -> tuple[str, str]:
        self.n += 1
        p = write_json(self.repo / "records" / f"r{self.n}.json", obj)
        return str(p), sha(p)

    def funding(self, blk: str, amount: float, **change) -> str:
        rec = {"block": blk, "amount_usd": amount, "utc": "2026-11-05T12:00:00Z", "source": "user RunPod top-up",
               "user_words": "synthetic words for this test", "recorded_by": "test", **change}
        return self.record(rec)[0]

    def jobs(self, launches, **extra) -> str:
        return self.record({"launches": launches, **extra})[0]

    def n_jobs(self, **extra) -> str:
        return self.jobs([{"hosts": [n_layout(self.family)]}], family=self.family, **extra)

    def init(self, block: str = "0", launches=None, amount: float = 56.06, dry_run: bool = False, **extra):
        jobs = self.n_jobs(**extra) if launches is None else self.jobs(launches, **extra)
        return self.tool.init_block(argparse.Namespace(block=block, jobs=jobs, funding=self.funding(block, amount),
                                                       dry_run=dry_run, group_jobs=None))

    def plan(self) -> dict:
        return self.mac.load_plan()


@pytest.fixture
def w(tmp_path, monkeypatch):
    world = World(tmp_path, monkeypatch)
    yield world
    for name in MODULES:
        sys.modules.pop(name, None)


@pytest.fixture(params=["olmo2-7b", "llama31-8b"])
def wf(request, tmp_path, monkeypatch):
    """A World of either family (parametrized)."""
    world = World(tmp_path, monkeypatch, request.param)
    yield world
    for name in MODULES:
        sys.modules.pop(name, None)


# ===== the need and the funding rule (ported from test_stage1_runkit.py:619-680, 1999-2005, 2912-2935) =============
def test_the_need_and_the_funding_rule_at_init(w, capsys):
    """N's need by hand (KCR:177): guard $6 + (8.5 + 12.5) x $1.85 = $44.85; need 1.25 x $44.85 = $56.06. Exactly the
    need is enough (>=); a cent below refuses; the dry run writes nothing."""
    base = cents(6 + 1.85 * (8.5 + 12.5))
    assert base == 44.85 and times_125(base) == 56.06
    out = w.init(dry_run=True)
    assert out["dry_run"] and out["base_need_usd"] == 44.85 and out["need_usd"] == 56.06
    assert out["contingency_usd"] == cents(56.06 - 44.85) and out["family"] == "olmo2-7b"
    assert not (w.root / "plan.json").exists()
    with pytest.raises(SystemExit, match="below the need"):
        w.init(amount=56.05)
    assert not (w.root / "plan.json").exists()
    w.init(amount=56.06)
    plan = w.plan()
    assert plan["blocks"]["0"]["need"]["need_usd"] == 56.06 and plan["blocks"]["0"]["funding"]["amount_usd"] == 56.06
    assert plan["contingency"]["0"]["usd"] == cents(56.06 - 44.85)
    assert plan["blocks"]["0"]["released"] == 1 and plan["blocks"]["0"]["pending"] == {}
    assert list(plan["hosts"]) == ["olmo2-7b-0-1"]
    with pytest.raises(SystemExit, match="already planned"):
        w.init(amount=56.06)


@pytest.mark.parametrize("change, match", [({"source": "gate B balance"}, "source"), ({"block": "A"}, "block 'A'"),
                                           ({"user_words": " "}, "user's words"), ({"amount_usd": float("nan")}, "finite"),
                                           ({"amount_usd": True}, "finite"), ({"utc": "yesterday"}, "UTC"),
                                           ({"recorded_by": ""}, "recorded_by")])
def test_a_funding_record_that_breaks_the_users_rule_refuses(w, change, match):
    path = w.funding("0", 500.0, **change)
    with pytest.raises(SystemExit, match=match):
        w.tool.init_block(argparse.Namespace(block="0", jobs=w.n_jobs(), funding=path, dry_run=False, group_jobs=None))
    with pytest.raises(SystemExit, match="needs --funding"):
        w.tool.init_block(argparse.Namespace(block="0", jobs=w.n_jobs(), funding=None, dry_run=False, group_jobs=None))
    assert not (w.root / "plan.json").exists()


def test_a_funding_record_under_the_users_start_from_the_balance_rule(w, tmp_path):
    """Addendum §36: a funding record without a covering top-up is accepted only with the user's decision record,
    re-hashed at every use; a record with any other source still refuses. Carried over unchanged (the K1 brief)."""
    assert w.tool.FUNDING_SOURCE_RULE == "user rule: start from the balance"
    assert w.tool.FUNDING_RULE_KIND == "stage1 user decision: start without a covering top-up"
    dec = tmp_path / "decision.json"
    dec.write_text(json.dumps({"kind": w.tool.FUNDING_RULE_KIND, "user_words": "start it now"}))
    named = {"path": str(dec), "sha256": hashlib.sha256(dec.read_bytes()).hexdigest()}
    path = w.funding("0", 56.06, source=w.tool.FUNDING_SOURCE_RULE, user_decision=named)
    rec = w.tool.funding_record(path, "0")
    assert rec["source"] == w.tool.FUNDING_SOURCE_RULE and rec["user_decision"] == named
    assert "user_decision" not in w.tool.funding_record(w.funding("0", 56.06), "0")
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"kind": "something else", "user_words": "x"}))
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"kind": w.tool.FUNDING_RULE_KIND, "user_words": " "}))
    for change, match in (({}, "path, sha256"),
                          ({"user_decision": {"path": str(dec), "sha256": "0" * 64}}, "differs"),
                          ({"user_decision": {"path": str(tmp_path / "gone.json"), "sha256": named["sha256"]}}, "differs"),
                          ({"user_decision": {"path": str(other), "sha256": hashlib.sha256(other.read_bytes()).hexdigest()}},
                           "not a"),
                          ({"user_decision": {"path": str(empty), "sha256": hashlib.sha256(empty.read_bytes()).hexdigest()}},
                           "not a")):
        bad = w.funding("0", 56.06, source=w.tool.FUNDING_SOURCE_RULE, **change)
        with pytest.raises(SystemExit, match=match):
            w.tool.funding_record(bad, "0")
    # init-block 0 under the rule plans the block (the decision record named in plan.json).
    out = w.tool.init_block(argparse.Namespace(block="0", jobs=w.n_jobs(), funding=path, dry_run=False, group_jobs=None))
    assert out["hosts"] == ["olmo2-7b-0-1"] and w.plan()["blocks"]["0"]["funding"]["user_decision"] == named
    dec.write_text(json.dumps({"kind": w.tool.FUNDING_RULE_KIND, "user_words": "changed after recording"}))
    with pytest.raises(SystemExit, match="differs"):                   # re-hashed at every use
        w.tool.funding_record(path, "0")


@pytest.mark.parametrize("utc", ["2026-11-05T12:00:00+05:30", "2099-01-01T00:00:00Z"])
def test_a_funding_record_in_another_zone_or_the_future_refuses(w, utc):
    path = w.funding("0", 500.0, utc=utc)
    with pytest.raises(SystemExit, match="utc"):
        w.tool.init_block(argparse.Namespace(block="0", jobs=w.n_jobs(), funding=path, dry_run=False, group_jobs=None))


def test_a_huge_integer_refuses_cleanly_as_a_funding_amount_or_a_sigma(w):
    """VG2-5 (ported): an integer too large for a float (10**400) is refused as a ValueError / SystemExit, never an
    OverflowError traceback."""
    huge = 10 ** 400
    with pytest.raises(ValueError):
        w.rules.plan_code_for(huge)
    with pytest.raises(SystemExit, match="positive finite number"):
        w.tool.funding_record(w.funding("0", huge), "0")
    assert w.rules.plan_code_for(4.5) == "A" and w.rules.plan_code_for(6.0) == "B9" and w.rules.plan_code_for(6.01) == "H"


# ===== the guard-off record (ported from test_stage1_runkit.py:760-790) =============================================
def _guard_off(w, **change) -> tuple[str, str]:
    rec = {"kind": "stage1 user decision: budget guard off", "user_words": USER_WORDS, "utc": "2026-10-25T12:00:00Z",
           "recorded_by": "test", **change}
    return w.record({k: v for k, v in rec.items() if v is not ...})


@pytest.mark.parametrize("change, match", [({"kind": "stage1 user decision: pay re-runs"}, "kind"),
                                           ({"user_words": ...}, "exactly"), ({"user_words": " "}, "non-empty"),
                                           ({"utc": "2099-01-01T00:00:00Z"}, "future"), ({"utc": "noon"}, "UTC"),
                                           ({"extra": 1}, "exactly")])
def test_record_guard_off_takes_only_the_users_decision_record(w, change, match):
    w.init()
    with pytest.raises(SystemExit, match=match):
        w.tool.record_simple("guard_off", *_guard_off(w, **change))
    assert w.plan()["records"].get("guard_off") is None and w.rules.guard_off_record(w.root) is None


def test_record_guard_off_is_recorded_once_by_sha256_and_a_changed_file_turns_the_guard_back_on(w):
    w.init()
    assert w.rules.guard_off_record(w.root) is None                          # no record: the guard as before
    p, h = _guard_off(w)
    assert w.tool.record_simple("guard_off", p, h) == {"recorded": "guard_off", "sha256": h}
    rec = w.plan()["records"]["guard_off"]
    assert rec["sha256"] == h and rec["user_words"] == USER_WORDS and Path(rec["path"]).is_absolute()
    assert w.rules.guard_off_record(w.root) == {"sha256": h, "utc": "2026-10-25T12:00:00Z", "recorded_by": "test"}
    with pytest.raises(SystemExit, match="already recorded off"):
        w.tool.record_simple("guard_off", *_guard_off(w, recorded_by="another"))
    Path(p).write_text(Path(p).read_text().replace("test", "tset"))
    assert w.rules.guard_off_record(w.root) is None                          # re-hashed at every use
    # The CLI: record-guard-off and record-sealed are this copy's records; a stage-1 record command refuses.
    with pytest.raises(SystemExit, match="stage-1 \\(1B\\) record"):
        w.tool.main(["record-gateb-final", p, "--sha256", h])


# ===== the kit compiles, holds no secret, keeps the stage-1 files it does not adapt (ported from :1714-1755) ========
ADAPTED = {"stage1_rules.py", "probes.py", "plan_tool.py", "pack_setup.py", "README.md", "tests/test_stage1_runkit.py"}
ADAPTED_BY_K2 = {"setup/job_runner_stage1.py", "setup/preflight_stage1.py", "finisher.py", "status.py",
                 "backup_records_stage1.py", "tests/test_stage1_runner.py", "tests/test_round30a.py",
                 "tests/test_round34.py", "tests/test_round35.py", "tests/test_g1_yoext.py"}   # K2: the runner stage
ADAPTED_BY_K3 = {"launch.py", "host.py", "orchestrate.py", "setup/download_models_stage1.py",
                 "setup/setup_and_fetch_stage1.sh", "tests/test_round31.py", "tests/test_round33.py",
                 "tests/test_stage1_judge_route.py"}                        # K3: the gated-token launch path


def test_the_kit_compiles_holds_no_secret_and_keeps_the_copied_files_byte_for_byte(tmp_path):
    manifest = json.loads((KIT / "COPY-MANIFEST.json").read_text())
    assert manifest["kind"] == "stage1-78b copy manifest" and set(manifest["adapted_by_k1"]) == ADAPTED
    assert set(manifest["adapted_by_k2"]) == ADAPTED_BY_K2                 # K2: every later stage unions its list here
    assert set(manifest["adapted_by_k3"]) == ADAPTED_BY_K3
    assert not (ADAPTED & ADAPTED_BY_K2) and not (ADAPTED_BY_K2 & ADAPTED_BY_K3) and not (ADAPTED & ADAPTED_BY_K3)
    adapted = ADAPTED | ADAPTED_BY_K2 | ADAPTED_BY_K3
    listed = {e["path"]: e["sha256"] for e in manifest["files"]}
    assert len(listed) == 36 and "budget.py" in listed and "setup/job_runner_stage1.py" in listed
    for rel, digest in listed.items():
        assert (KIT / rel).is_file(), rel
        if rel not in adapted:
            assert sha(KIT / rel) == digest, f"{rel} differs from the stage-1 kit's bytes"
            if (STAGE1 / rel).is_file():
                assert (KIT / rel).read_bytes() == (STAGE1 / rel).read_bytes(), rel
    assert sha(KIT / "budget.py") == listed["budget.py"]                   # KITS_GLOB unchanged (C7; KD7)
    names = sorted(p.name for p in KIT.glob("*.py"))
    assert names == ["account.py", "backup_records_stage1.py", "budget.py", "compare_c1.py", "derive_78b_basis.py",
                     "finisher.py", "gateb_mac.py", "host.py", "judge_units_stage1.py", "launch.py", "orchestrate.py",
                     "pack_setup.py", "plan_tool.py", "probes.py", "rules_78b.py", "seal.py", "secret_scan.py",
                     "stage1_rules.py", "states_tool.py", "status.py"]                 # K2: states_tool.py (KD5)
    import py_compile
    for n in names:
        py_compile.compile(str(KIT / n), cfile=str(tmp_path / "x.pyc"), doraise=True)
    sys.path.insert(0, str(KIT))
    try:
        sys.modules.pop("secret_scan", None)
        import secret_scan
        assert secret_scan.scan_paths([KIT / n for n in names if n != "secret_scan.py"]) == []
        assert secret_scan.scan_paths(list(KIT.glob("*.md")) + list(KIT.glob("*.json")) + list((KIT / "tests").glob("*"))
                                      + list((KIT / "setup").glob("*"))) == []
        assert secret_scan.scan_text(fake_token()) == ["hf_token"]       # the scanner sees a token; the kit holds none
    finally:
        sys.path.remove(str(KIT))
        sys.modules.pop("secret_scan", None)


# ===== the CLI dry run writes nothing; deal prints N (ported from :1757-1780) =======================================
def test_the_cli_dry_run_writes_nothing_and_deal_prints_n(wf, capsys):
    w = wf
    jobs = w.n_jobs()
    assert w.tool.main(["init-block", "0", "--jobs", jobs, "--dry-run"]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    out = json.loads(lines[-1])
    assert out["dry_run"] is True and out["family"] == w.family
    assert [p["cap_hours"] for p in out["pods"]] == [8.5 if w.family == "olmo2-7b" else 12.5]
    assert len([x for x in lines[:-1] if x.startswith("need ")]) == 2 + 2 + 16          # N, this pod, 2 retrain, 16 scorer
    assert len(lines[:-1]) == len(out["need_lines"]) == 2 + 2 + 16 + 1                  # + KD5's idle-storage line (D2)
    assert lines[-2].startswith("idle storage (KD5; E, KCR:161): about $0.33 per day per stopped 50 GB pod")
    assert not (w.root / "plan.json").exists() and not (w.root / "operator-actions.jsonl").exists()
    assert w.tool.main(["deal", "0"]) == 0
    pods = json.loads(capsys.readouterr().out)["pods"]
    expect = ["R@1101", "R@1102", "R@1103"] + (["a0@1103"] if w.family == "llama31-8b" else [])
    assert pods == [expect]
    with pytest.raises(SystemExit, match="reuses no unit"):
        w.tool.main(["deal", "0", "--reuse", "R", "1101"])
    for block in ("A", "S1-0", "B", "P", "sim"):
        with pytest.raises(SystemExit, match="block 0 only"):
            w.tool.main(["init-block", block, "--jobs", jobs, "--dry-run"])
        with pytest.raises(SystemExit, match="block 0 only"):
            w.tool.main(["deal", block])
