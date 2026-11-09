"""R2 K2: the 7-8B kit's planning layer for blocks A and B (plan-ab items 1, 5c, 7, 8, 10-12, 14; the lead's build
rulings GXB B-2, K-1 to K-8, O6, O7, O14 corrected, R-1, R-24, R-26, R-30 to R-33; Part 2 §2, §6, §10.1). On CPU, no
pod, no network, no real process: working copies tmp/family-probe-s78-<family>-<block>/ (ROOT = tmp) with synthetic
pins filled TEST-LOCALLY (the committed pins stay null; A13's pattern). Every unit, answer and U value below is a
synthetic sentinel; no sealed list, row, answer or real unit is read (the SR-2 simulation's merged outputs, committed
records of simulated rates, are read by key in one test). Expected values are written by hand.

    PYTHONDONTWRITEBYTECODE=1 PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests/test_planning_ab_78b.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import math
import shutil
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pytest

import test_stage1_runkit as rk

KIT = rk.KIT
REPO = KIT.parents[1]
X = rk.X
FAMILIES = ("olmo2-7b", "llama31-8b")
NR_SHA = "94b679ffeee7656c5b8c6e97b2275bb05260b61cac50743f357ef8ce2c40d436"
SENTINELS = ("SENTINEL-U-0.73192847", "0.7319284756", "SENTINEL-HARMBENCH-0.4142", "SENTINEL-ANSWER-TEXT",
             "0.6180339887", "SENTINEL-QUERY-LOSS-2.7182818", "SENTINEL-COHERENCE-0.5772", rk.SENTINEL)
MODULES = rk.MODULES + ("judge_units_stage1", "states_tool", "orchestrate")
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SHARED_STOP = FIXTURES / "anchor_stop__olmo2-7b__safe_anchors_below_64.json"   # KR5: the one shared stop fixture


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hx(tag: str) -> str:
    return hashlib.sha256(tag.encode()).hexdigest()


def write(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(obj if isinstance(obj, str) else json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return path


def canon(obj) -> bytes:                       # the engine's canonical JSON, by hand (stage1_rules.canonical_bytes)
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def cents(x: float) -> float:
    return float(Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def load_by_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SIGMA_OF = {("A", False): 4.0, ("B9", False): 5.5, ("H", False): 8.0, ("H", True): 11.0}   # each plan's own sigma


def rule(plan: str, review: bool, sigma: float | None = None) -> dict:
    return {"plan": plan, "review": review, "sigma_pp": SIGMA_OF[(plan, review)] if sigma is None else sigma}


def noise_doc(plan: str = "A", review: bool = False, sigma_f=("A", False), engines: dict | None = None,
              sigma_f_llama=None) -> dict:
    """A synthetic output of scripts/scale78b/noise_reading.py in its own fields (kind, version, script_sha256,
    families.F.engine and .seed_rule_by_sigma_F, seed_rule and pooled.seed_rule, each with its sigma_pp); no U value.
    Llama-3.1-8B's sigma_F plan is ``sigma_f_llama`` when given (K2V-6: [C] reads OLMo-2-7B's)."""
    out = {"kind": "scale-78b noise reading", "version": 1, "script_sha256": NR_SHA, "families": {},
           "seed_rule": rule(plan, review), "pooled": {"seed_rule": rule(plan, review)}}
    for f in FAMILIES:
        sf = sigma_f_llama if (f == "llama31-8b" and sigma_f_llama) else sigma_f
        out["families"][f] = {"engine": dict(engines or {"a0": X, "R": X}), "seed_rule_by_sigma_F": rule(*sf)}
    return out


BLINDING_FILES = ("scripts/scale78b/blinded_sigma.py", "scripts/scale78b/tests/test_blinded_sigma.py",
                  "runkit/stage1-78b/plan_tool.py", "runkit/stage1-78b/tests/test_planning_ab_78b.py")


METHOD_ROWS = {"A1": 600, "L1": 600, "H1": 600, "S1": 48, "S3": 48, "S4": 48, "S4_96": 96, "S4_192": 192}


class ABWorld:
    """A block-A or block-B working copy of the kit for one family (the World of test_stage1_runkit.py at block A/B)."""

    def __init__(self, tmp: Path, monkeypatch, family: str = "olmo2-7b", block: str = "A"):
        self.repo, self.family, self.block, self.mp = tmp, family, block, monkeypatch
        self.root = tmp / "tmp" / f"family-probe-s78-{family}-{block}"
        shutil.copytree(KIT, self.root, ignore=shutil.ignore_patterns("__pycache__", "tests", "packed-*"))
        monkeypatch.syspath_prepend(str(self.root))
        for name in MODULES:
            monkeypatch.delitem(sys.modules, name, raising=False)
        self.r78 = r78 = importlib.import_module("rules_78b")
        folder = tmp / Path(r78.SEALED_SETS[family]["path"]).parent
        man = rk.write_json(folder / "MANIFEST.json", rk.synthetic_manifest(folder, family, r78, rk.MANIFEST_FORMS[family]))
        monkeypatch.setitem(r78.SEALED_SETS[family], "sha256", sha(man))
        kit = r78.KIT[family]
        fx = rk.write_json(tmp / kit["fixture"]["path"],
                           {"kind": "preflight verification (synthetic)", "recipe_sha256": kit["rec"][1],
                            "manifest_sha256": kit["manifest_sha256"], "training_identity": kit["training_identity"],
                            "cap_projection": {"e1_upper_s": 16695.63, "training_s": 952.03, "untuned_projected_s": 2337.4,
                                               "projected_job_upper_s": 36243.3, "batches_capped": 34}})
        monkeypatch.setitem(r78.KIT[family]["fixture"], "sha256", sha(fx))
        self.rules = r = importlib.import_module("stage1_rules")
        self.mac = importlib.import_module("gateb_mac")
        self.tool = importlib.import_module("plan_tool")
        assert r.FAMILY == family and r.KIT_BLOCK == block and r.KIT_PROBLEM is None
        rec = rk.write_json(tmp / r.REC, {"recipe": r.REC, "synthetic": True})
        monkeypatch.setitem(r.RECIPE_PINS, r.REC, sha(rec))
        self.config = {r.REC: r.REC_CONFIG_SHA256}
        monkeypatch.setattr(self.tool, "recipe_sha", lambda path: self.config.get(path, "0" * 64))
        monkeypatch.setattr(self.tool, "recipe_training_identity",
                            lambda path: r.TRAINING_IDENTITY if path == r.REC else "1" * 64)
        rk.write_json(self.root / "setup" / "packed-stage1-X" / "setup-receipt.json",
                      {"engine_sha256": X, "sealed_files_sha256": "f" * 64, "family": family})
        self.n = 0

    # ----- records and test-local pins -----
    def record(self, obj, name: str | None = None) -> Path:
        self.n += 1
        return write(self.repo / "records" / (name or f"r{self.n}.json"), obj)

    def rel(self, path: Path) -> str:
        return Path(path).relative_to(self.repo).as_posix()

    def pin(self, attr: str, path: Path, key: str | None = None) -> dict:
        value = {"path": self.rel(path), "sha256": sha(path)}
        if key is None:
            self.mp.setattr(self.r78 if hasattr(self.r78, attr) else self.tool, attr, value)
        else:
            self.mp.setitem(getattr(self.r78 if hasattr(self.r78, attr) else self.tool, attr), key, value)
        return value

    def gate(self, option: str = "B", **noise) -> dict:
        """N's noise reading (synthetic) and the gate record written by the kit's own record step, then GATE_78B."""
        self.noise = self.record(noise_doc(**noise), "noise-reading.json")
        out = self.repo / "records" / f"gate-{self.n}.json"
        got = self.tool.record_gate_78b(str(self.noise), sha(self.noise), option, "512.5", "test", str(out))
        self.pin("GATE_78B", out)
        return got

    def blinding(self, verified: bool = True, files: dict | None = None) -> Path:
        """GXB R-44: the blinding record test-locally: the checkout's files at REPO's bytes (copied into ROOT), the
        copy's own plan_tool.py, each by SHA-256, and a commit; SR2_BLINDING_RECORD pinned to it."""
        got = {}
        for rel in BLINDING_FILES:
            if rel == "runkit/stage1-78b/plan_tool.py":
                got[rel] = sha(self.root / "plan_tool.py")
                continue
            dest = self.repo / rel
            if not dest.is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(REPO / rel, dest)
            got[rel] = sha(dest)
        got.update(files or {})
        p = self.record({"kind": "stage1-78b sr2 blinding test record", "version": 1, "verified": verified,
                         "files": got, "commit": "b" * 40, "evidence": f"the verifier's report (synthetic {self.n})",
                         "utc": "2026-11-20T12:00:00+00:00", "recorded_by": "test"}, f"blinding-{self.n}.json")
        self.mp.setattr(self.tool, "SR2_BLINDING_RECORD", {"path": self.rel(p), "sha256": sha(p)})
        return p

    def fill(self, edits: bool = True, branch: bool = True, oext: bool = True, padded: float | None = 38342.79,
             blinding: bool = True) -> None:
        fam, r78 = self.family, self.r78
        if blinding and self.tool.SR2_BLINDING_RECORD is None:
            self.blinding()
        if edits:
            for arm in ("A1", "L1", "S3", "S4"):
                self.mp.setitem(r78.METHOD_EDITS[fam], arm, {"path": f".ai/inputs/test/{fam}-{arm}.edit.json",
                                                             "sha256": hx(f"{fam}-{arm}-edit"), "rows": METHOD_ROWS[arm]})
        if branch:
            b = self.record({"kind": "stage1-78b branch record", "version": 1, "family": fam, "branch": "full",
                             "source": "default", "w1_18_record_sha256": None, "utc": "2026-11-20T12:00:00+00:00",
                             "recorded_by": "test"}, f"branch-{fam}.json")
            self.pin("BRANCH_78B", b, fam)
        if oext:
            files = {r78.OEXT_WRAPPER_78B: hx("wrapper"), f"scripts/scale78b/settings/OEXT-78B__{fam}.json": hx("index")}
            self.mp.setitem(r78.OEXT_78B, fam, {"files": files, "inputs": {"oext_bank": hx("bank"), "oext_record": hx("rec")}})
        if padded is not None:
            edits_map = {}
            for d in range(4, 14):
                edits_map[r78.R_DRAW_SOURCES[fam][d]["sha256"]] = padded
            for arm, pin in r78.METHOD_EDITS[fam].items():
                if pin is not None:
                    edits_map[pin["sha256"]] = padded
            p = self.record({"kind": "stage1-78b padded tokens record", "version": 1, "family": fam, "edits": edits_map,
                             "source": "synthetic token counts", "utc": "2026-11-20T12:00:00+00:00", "recorded_by": "test"},
                            f"padded-{fam}.json")
            self.pin("PADDED_TOKENS_78B", p, fam)

    def jobs(self, n_pods: int, extra: dict | None = None, launches=None) -> str:
        launches = launches if launches is not None else \
            [{"deal": list(range(n_pods))}, {"judge": {"judge": "harmbench"}}, {"judge": {"judge": "granite"}}]
        return str(self.record({"family": self.family, "launches": launches, **(extra or {})}))

    def funding(self, amount: float) -> str:
        return str(self.record({"block": self.block, "amount_usd": amount, "utc": "2026-11-05T12:00:00Z",
                                "source": "user RunPod top-up", "user_words": "synthetic words", "recorded_by": "test"}))

    def init(self, n_pods: int = 6, amount: float | None = 2000.0, dry_run: bool = False, noise: bool = True,
             blinded: str | None = None, anchor_job_done: str | None = None, extra=None, launches=None):
        return self.tool.init_block(argparse.Namespace(
            block=self.block, jobs=self.jobs(n_pods, extra, launches), dry_run=dry_run, group_jobs=None,
            funding=None if amount is None else self.funding(amount), noise_reading=str(self.noise) if noise else None,
            blinded_sigma=blinded, anchor_job_done=anchor_job_done))

    def plan(self) -> dict:
        return self.mac.load_plan()


def close(world) -> None:
    for name in MODULES:
        sys.modules.pop(name, None)


@pytest.fixture
def wa(tmp_path, monkeypatch):
    world = ABWorld(tmp_path, monkeypatch, "olmo2-7b", "A")
    yield world
    close(world)


@pytest.fixture(params=FAMILIES)
def waf(request, tmp_path, monkeypatch):
    world = ABWorld(tmp_path, monkeypatch, request.param, "A")
    yield world
    close(world)


# ===== 1. the lean route: init-block A (GXB B-2, K-2, O14, R-1, R-30) ===============================================
def test_init_block_a_plans_21_runs_on_six_pods_and_two_judge_launches_over_28_units(waf, capsys):
    """Block A per family (Part 2 §2.2): 21 runs (A1, L1, H1, S1, S3, S4 at 1102-1104; R_4, R_5; a0 1104), dealt
    4, 4, 4, 3, 3, 3 (Part 2 §2.4), every arm job carrying its edit by path and SHA-256, its O-ext step and its train
    scale; then HarmBench and Granite over 21 + 7 re-judged units. The judge caps by hand (the launcher's rule): HarmBench
    28 x 800 x 0.25 s + 2,700 s = 8,300 s -> 2.5 h; Granite (28 x 200 + 200) x 0.5 s + 2,700 s = 5,600 s -> 2.0 h. The
    need is 1.25 x the largest launch term (each term the reserve $6 + $1.85 x the launch's caps + the spend before),
    computed here by hand from the printed caps and spends. The dry run writes nothing."""
    w = waf
    w.gate()
    w.fill()
    out = w.init(dry_run=True)
    lines = capsys.readouterr().out.strip().splitlines()
    assert out["dry_run"] and out["runs"] == 21 and out["judge_units"] == 28 and out["plan"] is None
    assert [len(p["runs"]) for p in out["pods"]] == [4, 4, 4, 3, 3, 3]
    runs = sorted(r for p in out["pods"] for r in p["runs"])
    want = sorted([f"{a}@{s}" for a in ("A1", "L1", "H1", "S1", "S3", "S4") for s in (1102, 1103, 1104)]
                  + ["R@1104", "R@1105", "a0@1104"])
    assert runs == want
    for p in out["pods"]:
        arms = [r.split("@")[0] for r in p["runs"]]
        assert len(set(arms)) == len(arms) and p["counted"] == len(arms)          # one arm once per pod (KD2)
    edits = {(e["arm"], e["seed"]): e["sha256"] for p in out["pods"] for e in p["edits"]}
    assert edits[("R", 1104)] == w.r78.R_DRAW_SOURCES[w.family][4]["sha256"]
    assert edits[("A1", 1102)] == hx(f"{w.family}-A1-edit") and ("a0", 1104) not in edits
    caps = [p["cap_hours"] for p in out["pods"]]
    spends = [p["spend_upper_usd"] for p in out["pods"]]
    spent_pods = sum(spends)
    terms = [6 + 1.85 * sum(caps), spent_pods + 6 + 1.85 * 2.5, spent_pods + 2.5 * 1.79 + 6 + 1.85 * 2.0]
    base = cents(max(terms))
    assert out["base_need_usd"] == base and out["need_usd"] == cents(float(Decimal(repr(base)) * Decimal("1.25")))
    assert lines[-1].startswith("idle storage block A in all (KD5, PP14; E): 6 pod(s) keeping states: $1.98 per day")
    assert sum(x.startswith("need block A pod ") for x in lines) == 6
    assert sum(x.startswith("idle storage olmo2-7b-a-" if w.family == "olmo2-7b" else "idle storage llama31-8b-a-")
               for x in lines) == 6
    assert any("judge launch 1 harmbench (28 units: 21 runs + 7 re-judged; cap 2.50 h" in x for x in lines)
    assert any("judge launch 2 granite (28 units: 21 runs + 7 re-judged; cap 2.00 h" in x for x in lines)
    assert not (w.root / "plan.json").exists() and not (w.root / "operator-actions.jsonl").exists()
    plan = w.tool.skeleton()
    pods = w.rules.block_pods(None, "A", w.tool.padded_tokens(w.family, w.rules.block_runs(None, "A")))
    assert all(j["oext"] is True and j["train_scale"] == 1.0 for p in pods for j in p["jobs"])
    assert plan["kit_block"] == "A"


def test_init_block_a_writes_plan_json_releases_launch_0_and_rebinds_every_edit_at_release(wa):
    """With the funding record the plan is written and launch 0 (the six arm pods) released; the block record names the
    gate record and the noise reading by SHA-256. An edit pin changed after init refuses at a later release (the
    judge launches wait for the arm pods anyway); a gate pin changed after init refuses too."""
    w = wa
    w.gate()
    w.fill()
    out = w.init(amount=2000.0)
    assert out["hosts"] == [f"olmo2-7b-a-{i}" for i in range(1, 7)] and out["released"] == out["hosts"]
    plan = w.plan()
    b = plan["blocks"]["A"]
    assert b["gate"]["sha256"] == w.r78.GATE_78B["sha256"] and b["gate"]["noise_reading"]["sha256"] == sha(w.noise)
    assert [x.get("judge", {}).get("judge") for x in b["launches"]] == [None, "harmbench", "granite"]
    assert all(plan["hosts"][h]["block"] == "A" for h in out["hosts"]) and b["released"] == 1
    tool = w.tool
    names = [(n, plan["hosts"][n]) for n in out["hosts"][:1]]
    assert tool.release_hosts_ab(plan, "A", names) == [names[0][0]]           # unchanged pins: the release passes
    a1 = w.r78.METHOD_EDITS[w.family]["A1"]
    w.mp.setitem(w.r78.METHOD_EDITS[w.family], "A1", {"path": ".ai/inputs/test/other.json", "sha256": hx("other"),
                                                      "rows": 600})
    host = next(n for n, h in plan["hosts"].items() if any(j["arm"] == "A1" for j in h["jobs"]))
    with pytest.raises(SystemExit, match="the edit bound at init for A1 at 110[234] differs from its pin now"):
        tool.release_hosts_ab(plan, "A", [(host, plan["hosts"][host])])
    w.mp.setitem(w.r78.METHOD_EDITS[w.family], "A1", a1)
    old = dict(w.r78.GATE_78B)
    w.gate(plan="B9")                                    # a second gate record pinned after init
    assert w.r78.GATE_78B["sha256"] != old["sha256"]
    with pytest.raises(SystemExit, match="GATE_78B now pins another gate record"):
        tool.release_hosts_ab(plan, "A", names)


def test_init_block_a_refuses_before_the_gate_record_under_review_and_outside_the_gates_families(tmp_path, monkeypatch):
    """GXB O14 corrected and R-1: block A's init reads GATE_78B's record at its pin: null refuses with its event; a
    'review' provisional plan plans nothing; under [C] Llama-3.1-8B runs no block A (ruling 5)."""
    w = ABWorld(tmp_path, monkeypatch, "llama31-8b", "A")
    try:
        w.fill()
        w.noise = w.record(noise_doc(), "noise-reading.json")
        with pytest.raises(SystemExit, match="the pin GATE_78B is null: it waits for ruling 9's gate"):
            w.init(dry_run=True)
        w.gate(option="B", plan="H", review=True)
        with pytest.raises(SystemExit, match="provisional plan is 'review'"):
            w.init(dry_run=True)
        w.gate(option="C", sigma_f=("B9", False))
        with pytest.raises(SystemExit, match="the gate chose option C \\(olmo2-7b\\): llama31-8b runs no block A"):
            w.init(dry_run=True)
        assert not (w.root / "plan.json").exists()
    finally:
        close(w)


def test_r30_block_as_init_rereads_the_noise_reading_and_refuses_a_recorded_plan_that_differs(wa):
    """GXB R-30 (KR2-1): the gate record's provisional plan and, under [C], its sigma_F plan must be the ones N's
    noise-reading output gives, that output read at the SHA-256 the record names: a hand-made record whose plan differs
    refuses; a missing --noise-reading, another file, or an output not by the pinned noise_reading.py refuses."""
    w = wa
    w.fill()
    w.gate(option="C", plan="A", sigma_f=("B9", False))
    assert json.loads((w.repo / w.r78.GATE_78B["path"]).read_text())["sigma_F_plan"] == "B9"
    w.init(dry_run=True)                                 # the step's own record passes
    with pytest.raises(SystemExit, match="give its file \\(--noise-reading\\)"):
        w.init(dry_run=True, noise=False)
    original = json.loads((w.repo / w.r78.GATE_78B["path"]).read_text())
    for change, match in ((dict(provisional_plan="B9"), "provisional plan 'B9' is not the plan N's noise reading gives"),
                          (dict(sigma_F_plan="A"), "sigma_F_plan 'A' is not the plan N's noise reading gives")):
        doc = {**original, **change}
        w.pin("GATE_78B", w.record(doc))
        with pytest.raises(SystemExit, match=match):
            w.init(dry_run=True)
    w.gate(option="C", plan="A", sigma_f=("B9", False))
    real = w.noise
    w.noise = w.record({**noise_doc(sigma_f=("B9", False)), "note": "another file"})
    with pytest.raises(SystemExit, match="is missing or is not the file the record names"):
        w.init(dry_run=True)
    w.noise = real
    bad = w.record({**noise_doc(), "script_sha256": hx("another script")}, "noise-reading-2.json")
    with pytest.raises(SystemExit, match="not the pinned noise reading's output"):
        w.tool.record_gate_78b(str(bad), sha(bad), "B", "1", "test", str(w.repo / "records" / "g-bad.json"))


def test_k8_block_as_arm_jobs_wait_for_the_branch_record_read_by_its_bytes_and_for_oext(wa):
    """K-8, DES E3: every block-A arm and a0_arm job reads the 500 bank (its in-job O-ext step), so init refuses while
    BRANCH_78B is null, when the file at the pin is not the pinned bytes, and while OEXT_78B is null; a Branch-128
    record needs the O-ext pin to name the family's W1-18 record at the branch record's SHA-256 (GXB R-33)."""
    w = wa
    w.gate()
    w.fill(branch=False)
    with pytest.raises(SystemExit, match="waits for olmo2-7b's branch record \\(BRANCH_78B"):
        w.init(dry_run=True)
    w.fill(edits=False, oext=False, padded=None)
    path = w.repo / w.r78.BRANCH_78B[w.family]["path"]
    path.write_text(path.read_text() + " ")
    with pytest.raises(SystemExit, match="BRANCH_78B\\['olmo2-7b'\\] \\(records/branch-olmo2-7b.json\\) is missing or differs"):
        w.init(dry_run=True)
    w.fill(edits=False, oext=False, padded=None)
    w.mp.setitem(w.r78.OEXT_78B, w.family, None)
    with pytest.raises(SystemExit, match="carries the O-ext step: OEXT_78B\\['olmo2-7b'\\] is null"):
        w.init(dry_run=True)
    w.fill(edits=False, branch=False, padded=None)
    rec = f"{w.r78.W1_18_RECORD_DIR}overrefusal_checks__{w.family}.json"
    b = w.record({"kind": "stage1-78b branch record", "version": 1, "family": w.family, "branch": "128",
                  "source": "w1_18", "w1_18_record_sha256": hx("the w1-18 record"), "utc": "2026-11-20T12:00:00+00:00",
                  "recorded_by": "test"}, "branch-128.json")
    w.pin("BRANCH_78B", b, w.family)
    with pytest.raises(SystemExit, match="so the O-ext pin's files name exactly"):
        w.init(dry_run=True)
    oext = w.r78.OEXT_78B[w.family]
    w.mp.setitem(w.r78.OEXT_78B, w.family, {**oext, "files": {**oext["files"], rec: hx("another record")}})
    with pytest.raises(SystemExit, match="is not the branch record's w1_18_record_sha256"):
        w.init(dry_run=True)
    w.mp.setitem(w.r78.OEXT_78B, w.family, {**oext, "files": {**oext["files"], rec: hx("the w1-18 record")}})
    assert w.init(dry_run=True)["runs"] == 21


def test_k8_the_w1_18_hold_never_applies_to_block_0(tmp_path, monkeypatch):
    """K-8: block 0 (N) reads no 500 bank: with every branch pin null its init plans and releases N's pod, no block-0
    kind is a 500-bank kind, and the orchestrator's hold lets its pod start."""
    w = rk.World(tmp_path, monkeypatch, "llama31-8b")
    try:
        assert all(v is None for v in w.r78.BRANCH_78B.values()) and w.r78.W1_18_78B is None
        assert not any(w.r78.bank500_job(k, "0") for k in w.rules.BLOCK_KINDS["0"])
        assert w.r78.bank500_job("arm", "A") and w.r78.bank500_job("a0_arm", "B")
        host = w.init()["released"][0]
        orch = importlib.import_module("orchestrate")
        monkeypatch.setattr(orch, "log", lambda *a, **k: None)
        assert orch.w1_18_hold(host) is None             # no hold for block 0's pod
    finally:
        close(w)


def test_the_lean_jobs_file_and_its_deal_are_checked(wa):
    """The jobs file: the deal launches name the deal's 6 pods once, in order, then exactly one HarmBench and one
    Granite launch; block A takes no dose seeds; another family's file refuses (KD7)."""
    w = wa
    w.gate()
    w.fill()
    for launches, match in (([{"deal": [0, 1, 2]}, {"judge": {"judge": "harmbench"}}, {"judge": {"judge": "granite"}}],
                             "must name the deal's 6 pods exactly once"),
                            ([{"deal": [1, 0, 2, 3, 4, 5]}, {"judge": {"judge": "harmbench"}},
                              {"judge": {"judge": "granite"}}], "exactly once, in order"),
                            ([{"deal": [0, 1, 2, 3, 4, 5]}, {"judge": {"judge": "harmbench"}}], "one HarmBench and one"),
                            ([{"judge": {"judge": "harmbench"}}, {"deal": [0, 1, 2, 3, 4, 5]},
                              {"judge": {"judge": "granite"}}], "a deal launch comes before the judge launches"),
                            ([{"hosts": [[{"kind": "arm"}]]}], "a launch is"),
                            ([{"deal": [0, 1, 2, 3, 4, 5]}, {"judge": {"judge": "granite"}}, {"judge": {"judge": "granite"}}],
                             "given twice")):
        with pytest.raises(SystemExit, match=match):
            w.init(dry_run=True, launches=launches)
    with pytest.raises(SystemExit, match="block A plans no dose row"):
        w.init(dry_run=True, extra={"dose_seeds": 3})
    with pytest.raises(SystemExit, match="this working copy is olmo2-7b's"):
        w.init(dry_run=True, extra={"family": "llama31-8b"})
    two = w.init(dry_run=True, launches=[{"deal": [0, 1, 2]}, {"deal": [3, 4, 5]}, {"judge": {"judge": "harmbench"}},
                                         {"judge": {"judge": "granite"}}])
    assert [p["launch"] for p in two["pods"]] == [0, 0, 0, 1, 1, 1]
    assert w.tool.main(["deal", "A"]) == 0


def test_train_scales_input_is_the_padded_tokens_record_by_edit_sha256(wa):
    """Part 2 §2.1 (KCR:104): each edit arm's padded tokens per step come from PADDED_TOKENS_78B's record by the edit's
    SHA-256 (null refuses with its event; an edit it omits refuses; another family's record refuses); a count above
    a0's raises the job's train_scale and its cap."""
    w = wa
    w.gate()
    w.fill(padded=None)
    with pytest.raises(SystemExit, match="PADDED_TOKENS_78B\\['olmo2-7b'\\] is null: it waits for the lead's token-count"):
        w.init(dry_run=True)
    w.fill(edits=False, branch=False, oext=False, padded=38342.79)
    small = w.init(dry_run=True)
    w.fill(edits=False, branch=False, oext=False, padded=2 * 38342.79)
    big = w.init(dry_run=True)
    assert sum(p["cap_hours"] for p in big["pods"]) > sum(p["cap_hours"] for p in small["pods"])
    doc = json.loads((w.repo / w.tool.PADDED_TOKENS_78B[w.family]["path"]).read_text())
    del doc["edits"][hx("olmo2-7b-S3-edit")]
    w.pin("PADDED_TOKENS_78B", w.record(doc), w.family)
    with pytest.raises(SystemExit, match="holds no padded token count for S3's edit"):
        w.init(dry_run=True)
    w.pin("PADDED_TOKENS_78B", w.record({**doc, "family": "llama31-8b"}), w.family)
    with pytest.raises(SystemExit, match="is not olmo2-7b's 'stage1-78b padded tokens record'"):
        w.init(dry_run=True)


# ===== 2. the record steps: GATE_78B and PLAN_B_78B from their sources (GXB O14 corrected, K-6, R-24, R-30) ========
def sim_doc(option: str, count: int = 1000, reps: int = 20000, stopped=(), summary_count: int | None = None,
            above: bool | None = None, threshold: str = "0.06", script: str | None = None) -> dict:
    """A synthetic merged output of scripts/scale78b/sr2_simulation.py in its own fields (rows x scenarios x
    families with familywise counts; the summary's largest count, flag and threshold)."""
    tool_pins = {"script_sha256": "0ff5e54596a144d6cd4d3643ce83bc14bd21ebc9ea80b2416ebab645fd29fe89",
                 "settings_sha256": "c6f0c81e418e4efe8f876655621bbb1dbfa51ca91aa88a335a812e53eaa04b88"}
    fams = ("llama31-8b", "olmo2-7b") if option == "B" else ("olmo2-7b",)
    rows = [{"sigma_index": i, "sigma_pair_pp": str(3 + i), "scenarios": {
        sc: {"families": {f: {"familywise_count": max(0, count - 7 * i - (3 if sc == "none" else 0) - (1 if f[0] == "l" else 0))}
                          for f in fams}} for sc in ("none", "arm x seed 1")}} for i in range(3)]
    flag = Decimal(count) / Decimal(reps) > Decimal(threshold)
    if script:
        tool_pins["script_sha256"] = script
    return {"kind": "scale-78b sr2 simulation", "version": 1, "option": option, **tool_pins, "reps": reps,
            "design": {"name": "reduced" if stopped else "full", "stopped": list(stopped)}, "rows": rows,
            "summary": {"max_familywise": {"familywise_count": count if summary_count is None else summary_count},
                        "max_above_threshold": flag if above is None else above, "threshold_familywise": threshold}}


def a_snapshot(w, families) -> None:
    """GXB R-44 stand-ins: each family's block-A copy plan.json (a stub when no real one exists) keeps the blinding
    record its init read; record-plan-b-78b and block B compare the pinned record with it."""
    pin = w.tool.SR2_BLINDING_RECORD
    for f in families:
        path = w.repo / "tmp" / f"family-probe-s78-{f}-A" / "plan.json"
        doc = json.loads(path.read_text()) if path.is_file() else {"name": "stage1-78b", "family": f, "kit_block": "A",
                                                                     "stub": True}
        if doc.get("stub"):
            doc.setdefault("blocks", {}).setdefault("A", {})["blinding"] = {"sha256": pin["sha256"]}
            write(path, doc)
            if not (path.parent / "plan_tool.py").exists():    # GXB R-49: record-done's code in that copy
                shutil.copy(w.root / "plan_tool.py", path.parent / "plan_tool.py")


class SR2:
    """Test-local SR-2 pins of a world: the governing simulation output and the blinding record (with the block-A
    copies' snapshots of it)."""

    def __init__(self, w, option: str):
        self.w, self.families = w, w.r78.GATE_OPTIONS[option]
        self.sim(option)
        self.blinding()

    def sim(self, option: str, reduced: bool = False, **kw):
        p = self.w.record(sim_doc(option, **kw), f"sim-{option}-{self.w.n}.json")
        self.w.mp.setitem(self.w.tool.SR2_SIMULATION_REDUCED if reduced else self.w.tool.SR2_SIMULATION, option,
                          {"path": self.w.rel(p), "sha256": sha(p)})

    def blinding(self, snapshot: bool = True, **kw):
        self.w.blinding(**kw)
        if snapshot:
            a_snapshot(self.w, self.families)


def blinded_output(w, sigma: float, option: str = "B", families=FAMILIES) -> tuple[Path, Path]:
    """A synthetic blinded_sigma.py output and a stand-in inputs file at the kit's place (BLINDED_INPUTS), with the
    kit's rebuild (kit_inputs) and blinded_sigma.read (GXB R-50) stood in TEST-LOCALLY; the real rebuild from the
    block-A copies' parts and the real read are held end to end by the S-8/S-9 and K2V-5 tests."""
    inputs = write(w.tool.BLINDED_INPUTS, {"kind": "scale-78b blinded sigma inputs", "version": 1, "option": option,
                                           "families": {f: {"design": "full", "n": w.n} for f in families}})
    w.n += 1
    data = inputs.read_bytes()
    w.mp.setattr(w.tool, "kit_inputs", lambda gate: data)
    doc = {"df": 12 * len(families), "inputs_sha256": sha(inputs), "kind": "scale-78b blinded sigma",
           "sigma_A_pp": sigma, "version": 1}
    w.mp.setattr(w.tool, "blinded_sigma_read", lambda path, digest, script: {**doc, "inputs_sha256": digest})
    out = w.record(doc, f"blinded-{w.n}.json")
    return out, inputs


def plan_b(w, blinded=None, inputs=None) -> dict:
    out = w.repo / "records" / f"plan-b-{w.n}.json"
    w.n += 1
    got = w.tool.record_plan_b_78b(str(w.noise), None if blinded is None else str(blinded),
                                   None if blinded is None else sha(blinded), "test", str(out))
    w.pin("PLAN_B_78B", out)
    return got


def test_record_gate_78b_writes_the_gate_record_from_the_noise_reading_only(wa):
    """GXB O14 corrected, R-24, R-30: the provisional plan is the noise reading's seed rule on sigma_pool (review when
    its review flag is set), sigma_F_plan OLMo-2-7B's own sigma_F plan under [C] and null under [B]; the record is
    rules_78b's gate form, written once, and the record's option and balance are the lead's."""
    w = wa
    got = w.gate(option="B", plan="B9", sigma_f=("H", False))
    doc = json.loads((w.repo / w.r78.GATE_78B["path"]).read_text())
    assert (got["provisional_plan"], got["sigma_F_plan"]) == ("B9", None)
    assert doc["option"] == "B" and doc["families"] == ["olmo2-7b", "llama31-8b"] and doc["balance_usd"] == 512.5
    assert doc["noise_reading_sha256"] == sha(w.noise) and w.r78.gate_record_problem(doc) is None
    assert (w.repo / w.r78.GATE_78B["path"]).read_bytes() == canon(doc)
    got = w.gate(option="C", plan="A", sigma_f=("H", True))
    assert (got["provisional_plan"], got["sigma_F_plan"]) == ("A", "review")
    got = w.gate(option="B", plan="H", review=True)
    assert got["provisional_plan"] == "review"
    with pytest.raises(SystemExit, match="exists: a record is written once"):
        w.tool.record_gate_78b(str(w.noise), sha(w.noise), "B", "1", "test", str(w.repo / w.r78.GATE_78B["path"]))
    with pytest.raises(SystemExit, match="--option is B or C"):
        w.tool.record_gate_78b(str(w.noise), sha(w.noise), "A", "1", "test", str(w.repo / "records" / "g-x.json"))
    with pytest.raises(SystemExit, match="is missing or is not the file the record names"):
        w.tool.record_gate_78b(str(w.noise), hx("other"), "B", "1", "test", str(w.repo / "records" / "g-y.json"))


def test_record_plan_b_78b_carries_sr2s_status_from_the_pinned_records_only(wa):
    """K-6, R-24, R-30 and the brief's note: SR-2's status comes from the pinned records, never by hand. The blinding
    record null refuses (its event); verified and the simulation not above 6% -> adopted, plan and sigma_A_pp from
    blinded_sigma.py's output; not verified -> not adopted, reason blinding_test_not_verified, the gate's plan; the
    simulation above 6% -> reason simulation_reading; a summary that disagrees with its rows refuses."""
    w = wa
    w.gate(option="B", plan="B9")
    with pytest.raises(SystemExit, match="the pin SR2_BLINDING_RECORD is null: it waits for the verification"):
        plan_b(w)
    s = SR2(w, "B")
    with pytest.raises(SystemExit, match="SR-2 is adopted: give blinded_sigma.py's output"):
        plan_b(w)
    out, inputs = blinded_output(w, 6.4)
    got = plan_b(w, out, inputs)
    doc = json.loads((w.repo / w.r78.PLAN_B_78B["path"]).read_text())
    assert got["sr2_adopted"] is True and doc["plan"] == "H" and doc["sigma_A_pp"] == 6.4 and doc["plan_basis"] == "sigma_A"
    assert doc["blinded_sigma_output_sha256"] == sha(out) and doc["blinded_sigma_inputs_sha256"] == sha(inputs)
    assert got["simulation"]["max_familywise_count"] == 1000 and got["simulation"]["above_threshold"] is False
    assert got["blinded_sigma"] == {"sigma_A_pp": 6.4, "df": 24}     # GXB R-50: sigma_A and df only
    assert w.r78.plan_b_record_problem(doc, "B") is None
    s.blinding(verified=False)
    with pytest.raises(SystemExit, match="SR-2 is not adopted \\(blinding_test_not_verified\\): no blinded_sigma"):
        plan_b(w, out, inputs)
    got = plan_b(w)
    doc = json.loads((w.repo / w.r78.PLAN_B_78B["path"]).read_text())
    assert (doc["sr2_adopted"], doc["sr2_reason"], doc["plan"], doc["plan_basis"]) == \
        (False, "blinding_test_not_verified", "B9", "sigma_pool_N")
    assert doc["sigma_A_pp"] is None and doc["blinded_sigma_output_sha256"] is None
    s.blinding(verified=True)
    s.sim("B", count=1201)                               # 1,201 of 20,000 is above 6%
    assert plan_b(w)["sr2_reason"] == "simulation_reading"
    s.sim("B", count=1200)                               # exactly 6% is not above
    assert plan_b(w, *blinded_output(w, 4.5))["plan"] == "A"
    s.sim("B", count=1100, summary_count=999)
    with pytest.raises(SystemExit, match="summary disagrees with its rows"):
        plan_b(w)
    s.sim("B", script=hx("another simulation script"))
    with pytest.raises(SystemExit, match="is not the pinned simulation's output for option B"):
        plan_b(w)
    s.sim("B", threshold="0.07")
    with pytest.raises(SystemExit, match="reading threshold is not DES K6's 0.06"):
        plan_b(w)
    s.sim("C")
    s.sim("B")
    s.blinding(verified=True, snapshot=False)            # GXB R-44: a record no block-A copy read
    with pytest.raises(SystemExit, match="was not planned under the pinned blinding record"):
        plan_b(w)
    s.blinding(verified=True, files={"scripts/scale78b/blinded_sigma.py": hx("another blinded_sigma.py")})
    with pytest.raises(SystemExit, match="verified another scripts/scale78b/blinded_sigma.py"):
        plan_b(w)                                        # the first round's check, restored (GXB R-49)


def test_record_plan_b_78b_under_c_takes_sigma_f_and_a_stopped_family_needs_the_reduced_run(wa):
    """[C]: without SR-2 the plan is the gate's sigma_F_plan (P1 §6.2); the inputs file must be of the gate's option;
    once a family's ANCHOR_STOP is pinned the reduced-design run governs (GXB S-10) and refuses while it is null."""
    w = wa
    w.gate(option="C", plan="A", sigma_f=("B9", False))
    s = SR2(w, "C")
    s.blinding(verified=False)
    assert plan_b(w)["plan"] == "B9"
    s.blinding(verified=True)
    out, inputs = blinded_output(w, 3.0, option="C", families=("olmo2-7b",))
    inputs.write_text(inputs.read_text() + " ")          # not the kit's inputs file (K2V-3)
    with pytest.raises(SystemExit, match="is not the one the kit writes from the block-A copies' parts"):
        plan_b(w, out, inputs)
    out, inputs = blinded_output(w, 3.0, option="C", families=("olmo2-7b",))
    w.mp.setattr(w.tool, "kit_inputs", lambda gate: b"the kit's own rebuild (other bytes)")
    with pytest.raises(SystemExit, match="is not the one the kit writes from the block-A copies' parts"):
        plan_b(w, out, inputs)                           # the file matches the output's hash, not the kit's rebuild
    assert plan_b(w, *blinded_output(w, 3.0, option="C", families=("olmo2-7b",)))["plan"] == "A"
    w.mp.setitem(w.r78.ANCHOR_STOP, "olmo2-7b", {"path": "records/stop.json", "sha256": hx("stop")})
    with pytest.raises(SystemExit, match="SR2_SIMULATION_REDUCED\\['C'\\] is null: it waits for GXB S-10"):
        plan_b(w)
    s.sim("C", reduced=True, stopped=("olmo2-7b",))
    s.blinding(verified=False)
    assert plan_b(w)["plan"] == "B9"
    s.sim("C", reduced=True)                             # a "reduced" run of another design refuses
    with pytest.raises(SystemExit, match="ran on another design than the one block A runs"):
        plan_b(w)


def test_the_committed_sr2_simulation_pins_are_the_lead_s_records_and_read_not_above_6_percent(wa):
    """M (the brief's note): SR2_SIMULATION pins the committed merged outputs of R78/sr2-simulation-20261108/ by their
    SHA-256 (671f64a7... [B], 21738afc... [C]); their reading, recomputed from every row, is 1,029 and 1,035 of 20,000
    (0.05145, 0.05175): not above 6% (the lead's reading, README.md). Simulated rates only; no outcome."""
    w = wa
    for option, (count, digest) in {"B": (1029, "671f64a74dc037ec54b9465c24b8aa54e1c3b632e53556ddd4d00116c3f7e47f"),
                                    "C": (1035, "21738afc70689bf4ba249402befe8d1b035b895b2c597c6fb90a111ae5869465")}.items():
        pin = w.tool.SR2_SIMULATION[option]
        assert pin["sha256"] == digest and sha(REPO / pin["path"]) == digest
        shutil.copy(REPO / pin["path"], write(w.repo / pin["path"], ""))
        got = w.tool.sr2_simulation_reading(option, w.r78.GATE_OPTIONS[option])
        assert (got["max_familywise_count"], got["reps"], got["above_threshold"]) == (count, 20000, False)
    assert w.tool.SR2_SIMULATION_REDUCED == {"B": None, "C": None} and w.tool.SR2_BLINDING_RECORD is None


# ===== 3. block B: its plan, block A's seal, the dose rows from the dose record (R-24, R-26, R-30; K-5) =============
def seal_sibling(w, block: str, extra: dict | None = None) -> Path:
    """A sibling working copy's plan.json with its block sealed (a synthetic seal record), for GXB O7 / G5's 7-8B form
    (a stub's blinding snapshot is kept)."""
    copy = w.repo / "tmp" / f"family-probe-s78-{w.family}-{block}"
    seal = write(copy / "seals" / f"block-{block}.json", {"kind": "stage1 block seal", "version": 1, "block": block,
                                                           "files": [], **(extra or {})})
    path = copy / "plan.json"
    doc = json.loads(path.read_text()) if path.is_file() else {"name": "stage1-78b", "family": w.family,
                                                                 "kit_block": block, "stub": True}
    doc["seals"] = {block: {"path": f"seals/block-{block}.json", "sha256": sha(seal)}}
    write(path, doc)
    return seal


@pytest.fixture
def wb(tmp_path, monkeypatch):
    world = ABWorld(tmp_path, monkeypatch, "olmo2-7b", "B")
    yield world
    close(world)


def b_ready(w, sigma: float | None = 4.0, option: str = "B"):
    w.gate(option=option, plan="A", sigma_f=("A", False))
    w.fill()
    s = SR2(w, option)
    if sigma is None:
        s.blinding(verified=False)
        plan_b(w)
        return None
    out, inputs = blinded_output(w, sigma, option=option, families=w.r78.GATE_OPTIONS[option])
    plan_b(w, out, inputs)
    return out


def test_init_block_b_plans_its_plan_after_block_as_seal_and_rereads_blinded_sigma(wb):
    """Block B per plan (Part 2 §2.2): plan A 23 runs (the six arms at 1105-1107, R_6-R_7, a0 1105-1107) dealt
    4, 4, 4, 4, 4, 3; its init reads PLAN_B_78B's plan, re-reads blinded_sigma.py's output (R-30), and refuses before
    block A's seal in tmp/<prefix><F>-A/ (G5's 7-8B form)."""
    w = wb
    blinded = b_ready(w, sigma=4.0)
    with pytest.raises(SystemExit, match="block A of olmo2-7b is not sealed"):
        w.init(dry_run=True, blinded=str(blinded))
    seal_sibling(w, "A")
    with pytest.raises(SystemExit, match="give its file \\(--blinded-sigma\\)"):
        w.init(dry_run=True)
    out = w.init(dry_run=True, blinded=str(blinded))
    assert (out["plan"], out["runs"], out["judge_units"]) == ("A", 23, 23)
    assert [len(p["runs"]) for p in out["pods"]] == [4, 4, 4, 4, 4, 3]
    runs = sorted(r for p in out["pods"] for r in p["runs"])
    assert runs == sorted([f"{a}@{s}" for a in ("A1", "L1", "H1", "S1", "S3", "S4") for s in (1105, 1106, 1107)]
                          + ["R@1106", "R@1107", "a0@1105", "a0@1106", "a0@1107"])
    other = w.record({"df": 24, "inputs_sha256": hx("x"), "kind": "scale-78b blinded sigma", "sigma_A_pp": 4.1,
                      "version": 1}, "blinded-other.json")
    with pytest.raises(SystemExit, match="is missing or is not the file the record names"):
        w.init(dry_run=True, blinded=str(other))
    doc = json.loads((w.repo / w.r78.PLAN_B_78B["path"]).read_text())
    w.pin("PLAN_B_78B", w.record({**doc, "sigma_A_pp": 4.2}))
    with pytest.raises(SystemExit, match="sigma_A_pp is not blinded_sigma.py's printed value"):
        w.init(dry_run=True, blinded=str(blinded))


def test_init_block_b_takes_the_dose_rows_kept_count_from_the_dose_record(wb):
    """GXB K-5, R-26: block B's dose rows come from the untuned pass's s4_doses_record.json at S4_DOSES_RECORD's pin
    (null refuses with its event; a record whose fallback flag or top dose does not fit its kept count refuses): kept
    200 at 3 seeds -> S4_96 and S4_192 at 1102-1104 (6 more runs, 29); kept 150 -> S4_96 and s4_top (150 rows)."""
    w = wb
    b_ready(w, sigma=None)
    seal_sibling(w, "A")
    for arm in ("S4_96", "S4_192"):
        w.mp.setitem(w.r78.METHOD_EDITS[w.family], arm, {"path": f".ai/inputs/test/{arm}.json", "sha256": hx(arm),
                                                         "rows": METHOD_ROWS[arm]})
    w.fill(edits=False, branch=False, oext=False)
    rules = w.rules
    with pytest.raises(SystemExit, match="S4_DOSES_RECORD\\['olmo2-7b'\\] is null: it waits for the scorer block's untuned"):
        w.init(dry_run=True, extra={"dose_seeds": 3})

    def doses(kept, fired, top):
        p = w.record({"kind": "scale78b s4 doses record", "version": 1, "kept": kept, "fallback_fired": fired,
                      "top_dose": top, "doses": {}}, f"doses-{w.n}.json")
        w.pin("S4_DOSES_RECORD", p, w.family)

    doses(200, False, "s4_192")
    n = len(rules.deal(rules.block_runs("A", "B", (), 3, 200), "B"))
    out = w.init(n_pods=n, dry_run=True, extra={"dose_seeds": 3})
    assert out["runs"] == 29 and out["kept"] == 200
    assert sorted(r for p in out["pods"] for r in p["runs"] if r.startswith("S4_")) == \
        sorted(f"{a}@{s}" for a in ("S4_96", "S4_192") for s in (1102, 1103, 1104))
    doses(200, True, "s4_192")
    with pytest.raises(SystemExit, match="fallback_fired = kept < 192"):
        w.init(n_pods=n, dry_run=True, extra={"dose_seeds": 3})
    doses(150, True, "s4_96")
    with pytest.raises(SystemExit, match="top dose 's4_96' is not the one its kept count gives \\(s4_top\\)"):
        w.init(n_pods=n, dry_run=True, extra={"dose_seeds": 3})
    doses(150, True, "s4_top")
    w.mp.setitem(w.r78.METHOD_EDITS[w.family], "s4_top", {"path": ".ai/inputs/test/s4_top.json", "sha256": hx("top"),
                                                          "rows": 150})
    w.fill(edits=False, branch=False, oext=False)
    n = len(rules.deal(rules.block_runs("A", "B", (), 3, 150), "B"))
    out = w.init(n_pods=n, dry_run=True, extra={"dose_seeds": 3})
    assert sorted(r for p in out["pods"] for r in p["runs"] if r[0] in "Ss" and "4_" in r) == \
        sorted(f"{a}@{s}" for a in ("S4_96", "s4_top") for s in (1102, 1103, 1104))


def test_init_block_b_refuses_before_its_plan_record_and_under_a_review_plan(wb):
    """O14 corrected: block B refuses while PLAN_B_78B is null (its event) and plans nothing under 'review' (P1 §6.1)."""
    w = wb
    w.gate(option="B", plan="A")
    w.fill()
    seal_sibling(w, "A")
    with pytest.raises(SystemExit, match="the pin PLAN_B_78B is null: it waits for block A's record-done"):
        w.init(dry_run=True)
    s = SR2(w, "B")
    out, inputs = blinded_output(w, 11.0)                # above H (b)'s review ceiling (GXB R-29)
    assert plan_b(w, out, inputs)["plan"] == "review"
    with pytest.raises(SystemExit, match="block B's plan is 'review'"):
        w.init(dry_run=True, blinded=str(out))
    assert s is not None


# ===== 4. the branch-record step (K-8, R-21, R-33; K1V-5) ============================================================
def w1_18_route(r78, settings_sha: dict | None = None) -> dict:
    """W1_18_78B in Track O's maker's printed form (GXB R-20, R-32), both families, from KIT a0_units."""
    files, units = {r78.W1_18_SCRIPT: hx("wrapper")}, {}
    for f in FAMILIES:
        files[f"scripts/scale78b/settings/OEXT-78B-W1__{f}.json"] = hx(f"w1-index-{f}")
        files[f"scripts/scale78b/settings/limits_overrefusal_checks__{f}.json"] = (settings_sha or {}).get(f, hx(f"w1-{f}"))
        units[f] = {("untuned" if k == "untuned" else f"a0-{k}"): {"path": u["path"][4:], "complete_sha256": u["complete_sha256"],
                                                                 "job_sha256": u["job_sha256"]}
                    for k, u in r78.KIT[f]["a0_units"].items()}
    return {"files": files, "side_units": units}


def w1_18_record(w, passed: bool, units: int | None = None, settings: str | None = None, where: str | None = None) -> Path:
    n = units if units is not None else len(w.r78.w1_18_units(w.family))
    doc = {"kind": "stage1 over-refusal checks", "version": 1,
           "provenance": {"settings_sha256": settings or hx(f"w1-{w.family}")},
           "truncation_check": {"pass": passed}, "units": {f"u{i}": {"truncation": {"cap_tokens": 128}} for i in range(n)}}
    rel = where or f"{w.r78.W1_18_RECORD_DIR}overrefusal_checks__{w.family}.json"
    return write(w.repo / rel, doc)


def test_record_branch_78b_reads_the_familys_w1_18_record_at_its_r21_place(waf):
    """K-8, R-21: the branch record comes from the family's W1-18 record committed at
    .ai/inputs/stage1-post-w1-20261023/78b/w1-18/overrefusal_checks__<F>.json (pass -> 128, fail -> full), made under the
    family's W1-18 settings as W1_18_78B pins them, over the family's units; written in BRANCH_78B's form; the
    default record only while no W1-18 record exists; a pinned branch is never switched."""
    w = waf
    (w.repo / "records").mkdir(exist_ok=True)
    w.mp.setattr(w.r78, "W1_18_78B", w1_18_route(w.r78))
    out = lambda: str(w.repo / "records" / f"branch-out-{w.n}.json")      # noqa: E731
    w.n += 1
    rec = w1_18_record(w, passed=True)
    got = w.tool.record_branch_78b(str(rec), sha(rec), False, "test", out())
    doc = json.loads(Path(got["path"]).read_text())
    assert (got["branch"], doc["source"], doc["w1_18_record_sha256"]) == ("128", "w1_18", sha(rec))
    assert w.r78.branch_record_problem(doc, w.family) is None
    with pytest.raises(SystemExit, match="exists: the branch comes from that W1-18 record"):
        w.tool.record_branch_78b(None, None, True, "test", out())
    rec = w1_18_record(w, passed=False)
    w.n += 1
    assert w.tool.record_branch_78b(str(rec), sha(rec), False, "test", out())["branch"] == "full"
    for kw, match in ((dict(units=1), "units, not"), (dict(settings=hx("other settings")), "was not made under"),
                      (dict(where=".ai/inputs/stage1-post-w1-20261023/78b/other/w.json"), "not .*'s committed record")):
        bad = w1_18_record(w, passed=True, **kw)
        w.n += 1
        with pytest.raises(SystemExit, match=match):
            w.tool.record_branch_78b(str(bad), sha(bad), False, "test", out())
    rec = w1_18_record(w, passed=True)
    w.mp.setattr(w.r78, "W1_18_78B", None)
    with pytest.raises(SystemExit, match="W1_18_78B is null or off its form"):
        w.tool.record_branch_78b(str(rec), sha(rec), False, "test", out())
    w.mp.setattr(w.r78, "W1_18_78B", w1_18_route(w.r78))
    default = Path(w.repo / "records" / "default.json")
    (w.repo / f"{w.r78.W1_18_RECORD_DIR}overrefusal_checks__{w.family}.json").unlink()
    got = w.tool.record_branch_78b(None, None, True, "test", str(default))
    assert json.loads(default.read_text())["source"] == "default" and got["branch"] == "full"
    w.pin("BRANCH_78B", default, w.family)
    rec = w1_18_record(w, passed=True)
    w.n += 1
    with pytest.raises(SystemExit, match="it is never switched"):
        w.tool.record_branch_78b(str(rec), sha(rec), False, "test", out())
    w.n += 1
    with pytest.raises(SystemExit, match="either --w1-18-record FILE --sha256 H or --default"):
        w.tool.record_branch_78b(str(rec), sha(rec), True, "test", out())


# ===== 5. the anchor-stop record step and the one shared fixture (GXB O6, the fourth set; KR5, KR8) =================
def sc_world(tmp_path, monkeypatch, family: str = "olmo2-7b"):
    import test_scorer_block_78b as sb               # imported here: the scorer test module imports this one's tests
    w = sb.ScWorld(tmp_path, monkeypatch, family)
    w.pack(*sb.stand_in_lists(w))
    return w, sb


def stopped_anchor(w, exit_code: int, counts: dict | None = None, message: str | None = None) -> tuple[str, Path | None]:
    """An anchor host released, then its pulled JOB-DONE.json (the runner's form: status crashed, the anchor step's
    exit) recorded done; exit 3 leaves anchors.counts.json (make_anchor_answers.py:167-169's fields), exit 1 a stderr
    file with the step's last line."""
    host = w.init([{"kind": "anchor"}])["released"][0]
    tree = w.root / "retrieved" / host / "tree"
    if counts is not None:
        write(tree / "job-0" / "anchors" / "anchors.counts.json",
              {"kind": "gate-c anchor bank record", "version": 1, "complete": False, **counts,
               "walk": [{"index": 0, "outcome": "kept"}], "drops": {"capped": 3}})
    msg = None
    if message is not None:
        msg = write(tree / "job-0" / "olmo2-7b-sc-1-anchor.stderr.txt", "Traceback (synthetic)\n" + message + "\n")
    w.done(host, status="crashed", exits={f"{host}-anchor": exit_code}, why=f"exit {exit_code} in {host}-anchor")
    return host, msg


HARMFUL = ("harmful prompt 17 (18 of 64) does not encode (longer than max_train_tokens); the list needs a reviewed new "
           "version")


def test_record_anchor_stop_writes_the_shared_fixture_and_rk_and_the_reader_accept_it(tmp_path, monkeypatch):
    """KR5: the stop record the writer writes from a real (synthetic) anchor job's JOB-DONE.json and counts is the
    shared fixture tests/fixtures/anchor_stop__olmo2-7b__safe_anchors_below_64.json byte for byte; rules_78b's
    anchor_stop_problem accepts it for its family and its JOB-DONE.json, and anchor_stop_or_refuse reads it at a pin.
    (The cross-track test with scripts/scale78b/blinded_sigma.py's reader is K3's.)"""
    w, sb = sc_world(tmp_path, monkeypatch)
    try:
        host, _ = stopped_anchor(w, 3, counts={"kept": 61, "needed": 64})
        got = w.tool.record_anchor_stop(host, None, str(w.repo / "records" / "stop.json"))
        data = Path(got["path"]).read_bytes()
        assert data == SHARED_STOP.read_bytes()
        assert (got["stop_kind"], got["exit_code"], got["counts"]) == ("safe_anchors_below_64", 3, {"kept": 61, "needed": 64})
        doc = json.loads(data)
        done = w.plan()["hosts"][host]["job_done_sha256"]
        assert doc["job_done_sha256"] == done and w.r78.anchor_stop_problem(doc, "olmo2-7b", done) is None
        w.mp.setitem(w.r78.ANCHOR_STOP, "olmo2-7b", {"path": "records/stop.json", "sha256": sha(got["path"])})
        assert w.r78.anchor_stop_or_refuse("olmo2-7b", data, done) == doc and w.r78.family_stopped("olmo2-7b")
    finally:
        close(w)


@pytest.mark.parametrize("case", ["harmful", "other-message", "no-message", "exit-2", "counts-64", "complete"])
def test_record_anchor_stop_takes_only_the_frozen_scripts_two_signals(tmp_path, monkeypatch, case):
    """GXB O6: exit 3 with its counts, or exit 1 with the AnchorJobError harmful-pair message (the step's last stderr
    line, a file of the pulled tree), is a stop; any other exit or message is a crash (the kit's crash rule)."""
    w, sb = sc_world(tmp_path, monkeypatch)
    try:
        out = str(w.repo / "records" / "stop.json")
        if case == "harmful":
            host, msg = stopped_anchor(w, 1, message=HARMFUL)
            got = w.tool.record_anchor_stop(host, str(msg), out)
            assert (got["stop_kind"], got["counts"]) == ("harmful_prompt_does_not_encode",
                                                         {"prompt_index": 17, "position": 18, "of": 64})
            return
        if case == "other-message":
            host, msg = stopped_anchor(w, 1, message="CUDA out of memory")
            with pytest.raises(SystemExit, match="'crash', not a stop"):
                w.tool.record_anchor_stop(host, str(msg), out)
        elif case == "no-message":
            host, msg = stopped_anchor(w, 1, message=HARMFUL)
            with pytest.raises(SystemExit, match="give the step's stderr"):
                w.tool.record_anchor_stop(host, None, out)
            outside = write(w.repo / "elsewhere.txt", HARMFUL + "\n")
            with pytest.raises(SystemExit, match="a file of the pulled tree"):
                w.tool.record_anchor_stop(host, str(outside), out)
        elif case == "exit-2":
            host, msg = stopped_anchor(w, 2)
            with pytest.raises(SystemExit, match="'crash', not a stop"):
                w.tool.record_anchor_stop(host, None, out)
        elif case == "counts-64":
            host, msg = stopped_anchor(w, 3, counts={"kept": 64, "needed": 64})
            with pytest.raises(SystemExit, match="needs the job's counts line"):
                w.tool.record_anchor_stop(host, None, out)
        else:
            host = w.init([{"kind": "anchor"}])["released"][0]
            sb.anchor_done(w, host)
            with pytest.raises(SystemExit, match="the anchor job is not recorded crashed"):
                w.tool.record_anchor_stop(host, None, out)
        assert not Path(out).exists()
    finally:
        close(w)


def test_kr4_a_pinned_stop_record_is_read_before_any_block_a_planning(wa):
    """KR4, KR8: once ANCHOR_STOP[F] is pinned, block A's init refuses without the anchor job's JOB-DONE.json, refuses
    one that is not the record's, and with it reads and checks the record first: the stopped family's table drops A1,
    L1 and S3 (12 runs; DESO2 item 36 (1))."""
    w = wa
    w.gate()
    w.fill()
    stop = SHARED_STOP.read_bytes()
    doc = json.loads(stop)
    rec = write(w.repo / "records" / "stop.json", stop.decode())
    w.pin("ANCHOR_STOP", rec, "olmo2-7b")
    with pytest.raises(SystemExit, match="give the anchor job's JOB-DONE.json \\(--anchor-job-done\\)"):
        w.init(dry_run=True)
    other = write(w.repo / "records" / "JOB-DONE-other.json", {"host": "x"})
    with pytest.raises(SystemExit, match="not the anchor job's"):
        w.init(dry_run=True, anchor_job_done=str(other))
    done = w.repo / "records" / "JOB-DONE.json"
    done.write_bytes(b"x")
    w.mp.setitem(w.r78.ANCHOR_STOP, "olmo2-7b", None)
    doc2 = {**doc, "job_done_sha256": sha(done)}
    rec2 = write(w.repo / "records" / "stop2.json", canon(doc2).decode())
    w.pin("ANCHOR_STOP", rec2, "olmo2-7b")
    stopped_runs = [(a, s) for s in (1102, 1103, 1104) for a in ("H1", "S1", "S4")] + [("R", 1104), ("R", 1105),
                                                                                      ("a0", 1104)]
    n = len(w.rules.deal(stopped_runs, "A"))
    out = w.init(n_pods=n, dry_run=True, anchor_job_done=str(done))
    assert out["runs"] == 12 and not any(r.split("@")[0] in ("A1", "L1", "S3") for p in out["pods"] for r in p["runs"])
    assert out["anchor_stop"]["job_done_sha256"] == sha(done)


# ===== 6. block A's record-done: no outcome value, and blinded_sigma.py's inputs (P2 §10.1; S-8, S-9; item 8) ======
def n_units(w, complete=None) -> dict:
    """N_UNITS filled TEST-LOCALLY: N's units in block 0's copy (paths under tmp/<prefix><F>-0/), each by its
    COMPLETE.json and job.json SHA-256 (an R unit also its R_d edit's)."""
    out = {}
    for arm, seed in w.r78.block0_runs(w.family):
        unit = f"tmp/family-probe-s78-{w.family}-0/retrieved/{w.family}-0-1/tree/round1/{seed}-{arm}-e1-a1"
        entry = {"path": unit, "complete_sha256": (complete or {}).get((arm, seed), hx(f"N {arm} {seed}")),
                 "job_sha256": hx(f"N job {arm} {seed}")}
        if arm == "R":
            entry["edit_sha256"] = hx(f"R_d{seed - 1100}")
        out[f"{arm}-{seed}"] = entry
    w.mp.setitem(w.r78.N_UNITS, w.family, out)
    return out


ENGINES_A0_R = {"a0": hx("engine of the reused a0 units"), "R": hx("engine of N's R units")}   # R-13: per role


def released_a(w) -> list[str]:
    w.gate(option="C", engines=ENGINES_A0_R)
    w.fill()
    n_units(w)
    return w.init(amount=3000.0)["hosts"]


def unit_name(job: dict) -> str:
    arm = "a0" if job["arm"] == "a0" else job["edit"]["engine_arm"]
    return f"round1/{job['seed']}-{arm}-e1-a1"


def pull_planted(w, host: str) -> dict:
    """A pulled tree for HOST in the runner's form, each unit holding planted outcome sentinels (a U value in
    COMPLETE.json's evaluation, summary.json, the query losses, an answer, a coherence flag), and a judge file under
    judges/A/ with a HarmBench sentinel. Returns {job index: COMPLETE.json SHA-256}."""
    h = w.plan()["hosts"][host]
    tree = w.root / "retrieved" / host / "tree"
    recs, keys = [], {}
    for i, job in enumerate(h["jobs"]):
        unit = unit_name(job)
        folder = tree / unit
        write(folder / "eval" / "e1" / "summary.json", {"u": SENTINELS[1], "coherence": SENTINELS[6]})
        write(folder / "eval" / "e1" / "query_loss.jsonl", json.dumps({"loss": SENTINELS[5]}) + "\n")
        write(folder / "generations" / "e1" / "answers.jsonl", json.dumps({"text": SENTINELS[3]}) + "\n")
        c = write(folder / "COMPLETE.json", {"complete": True, "unit": f"{host}/{unit}",
                                              "evaluation": {"u": SENTINELS[0], "o": SENTINELS[4]}})
        ledger = write(tree / f"job-{i}" / "cost-ledger.json", {"kind": "stage1 cost ledger"})
        keys[i] = sha(c)
        recs.append({"index": i, "kind": job["kind"], "arm": job["arm"], "seed": job["seed"], "engine": "X",
                     "engine_sha256": X, "status": "complete", "unit": unit, "complete_sha256": sha(c),
                     "outputs": {f"job-{i}/cost-ledger.json": sha(ledger)}})
    write(tree / "JOB-DONE.json", {"host": host, "jobs": recs})
    write(w.root / "judges" / "A" / f"harmbench--{host}--{'a' * 12}.json", {"harm": SENTINELS[2]})
    return keys


def expected_part(w, keys: dict) -> dict:
    """The part blinded_sigma.py's inputs take for this family, by hand from the test's own files and pins."""
    cells, edits = {}, {}
    for host, h in sorted(w.plan()["hosts"].items()):
        for i, job in enumerate(h["jobs"]):
            entry = {"path": f"tmp/family-probe-s78-{w.family}-A/retrieved/{host}/tree/{unit_name(job)}",
                     "complete_sha256": keys[(host, i)]}
            if job["arm"] == "R":
                entry["arm"] = f"edit-{w.r78.R_DRAW_SOURCES[w.family][job['seed'] - 1100]['sha256']}"
            elif job["arm"] != "a0":
                edits[job["arm"]] = w.r78.METHOD_EDITS[w.family][job["arm"]]["sha256"]
            cells.setdefault(job["arm"], {})[str(job["seed"])] = entry
    for key, u in w.r78.N_UNITS[w.family].items():
        arm, seed = key.split("-")
        cells.setdefault(arm, {})[seed] = {"path": u["path"], "complete_sha256": u["complete_sha256"],
                                           **({"arm": f"edit-{u['edit_sha256']}"} if arm == "R" else {})}
    for seed, u in w.r78.KIT[w.family]["a0_units"].items():
        if seed != "untuned":
            cells.setdefault("a0", {})[str(seed)] = {"path": u["path"], "complete_sha256": u["complete_sha256"]}
    return {"kind": "stage1-78b blinded sigma inputs part", "version": 1, "family": w.family, "option": "C",
            "gate_sha256": w.r78.GATE_78B["sha256"],
            "entry": {"design": "full", "engine": {**ENGINES_A0_R, "block_a": X}, "edits": dict(sorted(edits.items())),
                      "cells": cells}}


def test_record_done_of_block_a_prints_no_outcome_and_its_whole_printout_is_held_byte_for_byte(wa, capsys):
    """P2 §10.1 (SR-2's hard trigger, the kit half): block A's record-done prints and writes no U, HarmBench, O, L or
    coherence value (planted sentinels in COMPLETE.json, summary.json, query_loss.jsonl, the answers and a judge file;
    stdout, stderr, plan.json, the operator log and the inputs part are scanned), and its whole printout is held byte
    for byte: the host and its statuses, and on the last host the part's path and SHA-256 computed here by hand."""
    w = wa
    hosts = released_a(w)
    capsys.readouterr()
    keys = {}
    for host in hosts:
        for i, digest in pull_planted(w, host).items():
            keys[(host, i)] = digest
    printed = []
    for host in hosts:
        assert w.tool.main(["record-done", host]) == 0
        printed.append(capsys.readouterr())
    for got, host in zip(printed[:-1], hosts[:-1]):
        n = len(w.plan()["hosts"][host]["jobs"])
        assert got.out == json.dumps({"host": host, "statuses": ["complete"] * n}) + "\n" and got.err == ""
    part = expected_part(w, keys)
    last = hosts[-1]
    rel = "tmp/family-probe-s78-olmo2-7b-A/blinded/blinded-sigma-inputs-part__olmo2-7b.json"
    want = json.dumps({"host": last, "statuses": ["complete"] * len(w.plan()["hosts"][last]["jobs"]),
                       "blinded_inputs_part": {"path": rel, "sha256": hashlib.sha256(canon(part)).hexdigest()}}) + "\n"
    assert printed[-1].out == want and printed[-1].err == ""
    assert (w.repo / rel).read_bytes() == canon(part)
    texts = [p.out + p.err for p in printed] + [(w.root / "plan.json").read_text(),
                                                (w.root / "operator-actions.jsonl").read_text(), (w.repo / rel).read_text()]
    for text in texts:
        assert not any(s in text for s in SENTINELS), text[:120]
    assert w.tool.main(["record-done", last]) == 0         # a second record-done finds the same bytes
    assert json.loads(capsys.readouterr().out)["blinded_inputs_part"]["sha256"] == hashlib.sha256(canon(part)).hexdigest()


def test_s9_the_part_waits_for_n_units_and_write_blinded_inputs_rebases_the_paths(wa, capsys):
    """S-9: with N_UNITS null at the last record-done the part is not written and the printout names what it waits for
    (no value); write-blinded-part writes it later; write-blinded-inputs takes the gate's families' parts (each once,
    of this gate) and rebases each path to the inputs file's folder."""
    w = wa
    hosts = released_a(w)
    w.mp.setitem(w.r78.N_UNITS, w.family, None)
    for host in hosts:
        pull_planted(w, host)
        out = w.tool.record_done(host)
    assert "N_UNITS['olmo2-7b'] is null" in out["blinded_inputs_part"]["waits"]
    assert not (w.root / "blinded").exists()
    n_units(w)
    a1 = w.r78.METHOD_EDITS[w.family]["A1"]
    w.mp.setitem(w.r78.METHOD_EDITS[w.family], "A1", {**a1, "sha256": hx("another A1 edit")})
    with pytest.raises(SystemExit, match="A1's bound edit is not METHOD_EDITS' pin"):
        w.tool.write_blinded_part_command()
    w.mp.setitem(w.r78.METHOD_EDITS[w.family], "A1", a1)
    part = w.tool.write_blinded_part_command()["blinded_inputs_part"]
    got = w.tool.write_blinded_inputs()
    out_path = w.tool.BLINDED_INPUTS
    assert got["path"] == "tmp/stage1-78b-blinded-sigma/blinded-sigma-inputs.json" and got["sha256"] == sha(out_path)
    doc = json.loads(out_path.read_text())
    assert doc["kind"] == "scale-78b blinded sigma inputs" and doc["option"] == "C" and list(doc["families"]) == ["olmo2-7b"]
    cell = doc["families"]["olmo2-7b"]["cells"]["A1"]["1102"]
    assert cell["path"].startswith("../family-probe-s78-olmo2-7b-A/retrieved/")
    assert (out_path.parent / cell["path"]).resolve() == (w.root / "retrieved").resolve() / cell["path"].split("retrieved/")[1]
    assert got["files_named"] == {"olmo2-7b": 27}
    assert w.tool.write_blinded_inputs()["sha256"] == got["sha256"]          # the same bytes again pass
    out_path.write_text(out_path.read_text() + " ")
    with pytest.raises(SystemExit, match="exists with other bytes"):
        w.tool.write_blinded_inputs()
    assert (w.repo / part["path"]) == w.tool.part_path(w.family)


def test_s8_s9_the_kit_written_inputs_are_read_by_blinded_sigma_on_block_a_units_in_the_kits_unit_form(wa, monkeypatch):
    """S-8 and S-9 end to end: block A's jobs run the same engine command as N's (run-one e1 units of the dev bank,
    split dev, role development; stage1_rules.arm_commands), so units in that form (Track S's fixture builder,
    make_unit) at the paths the runner records, N's units at N_UNITS' paths and the side units at KIT a0_units' paths,
    through the kit's own record-done part and write-blinded-inputs, are read by scripts/scale78b/blinded_sigma.py:
    12 df on OLMo-2-7B's full design under [C], sigma_A equal to an independent numpy fit."""
    w = wa
    monkeypatch.syspath_prepend(str(REPO))
    ts = load_by_path("ts_blinded_sigma_tests_k2", REPO / "scripts/scale78b/tests/test_blinded_sigma.py")
    fam, r78 = w.family, w.r78
    r_edits = {d: ts.r_edit(fam, d) for d in range(1, 6)}
    m_edits = {a: ts.method_edit(fam, a) for a in ("A1", "L1", "H1", "S1", "S3", "S4")}
    for d in (4, 5):
        monkeypatch.setitem(r78.R_DRAW_SOURCES[fam], d, {"path": f".ai/inputs/test/R_d{d}.json",
                                                         "sha256": hashlib.sha256(r_edits[d]).hexdigest()})
    w.gate(option="C")
    w.fill()
    for a, data in m_edits.items():
        monkeypatch.setitem(r78.METHOD_EDITS[fam], a, {"path": f".ai/inputs/test/{a}.json",
                                                       "sha256": hashlib.sha256(data).hexdigest(), "rows": METHOD_ROWS[a]})
    w.fill(edits=False, branch=False, oext=False)          # padded counts for the new edit hashes
    count = ts.unsafe_count
    complete = {}
    for arm, seed in r78.block0_runs(fam):                 # N's R units in block 0's copy
        rel = f"tmp/family-probe-s78-{fam}-0/retrieved/{fam}-0-1/tree/round1/{seed}-{arm}-e1-a1"
        complete[(arm, seed)] = ts.make_unit(w.repo / rel, fam, arm, seed, count(fam, arm, seed), r_edits[seed - 1100])
    units = n_units(w, complete)
    for key in units:
        arm, seed = key.split("-")
        units[key]["edit_sha256"] = hashlib.sha256(r_edits[int(seed) - 1100]).hexdigest()
    for seed, u in r78.KIT[fam]["a0_units"].items():       # the side units at their KIT paths (under ROOT/tmp)
        if seed != "untuned":
            monkeypatch.setitem(u, "complete_sha256", ts.make_unit(w.repo / u["path"], fam, "a0", seed, count(fam, "a0", seed)))
    hosts = w.init(amount=3000.0)["hosts"]
    for host in hosts:
        h = w.plan()["hosts"][host]
        tree = w.root / "retrieved" / host / "tree"
        recs = []
        for i, job in enumerate(h["jobs"]):
            arm, seed = job["arm"], job["seed"]
            edit = None if arm == "a0" else (r_edits[seed - 1100] if arm == "R" else m_edits[arm])
            key = ts.make_unit(tree / unit_name(job), fam, arm, seed, count(fam, arm, seed), edit)
            recs.append({"index": i, "kind": job["kind"], "arm": arm, "seed": seed, "engine": "X", "engine_sha256": X,
                         "status": "complete", "unit": unit_name(job), "complete_sha256": key, "outputs": {}})
        write(tree / "JOB-DONE.json", {"host": host, "jobs": recs})
        out = w.tool.record_done(host)
    assert "path" in out["blinded_inputs_part"]
    inputs = w.repo / w.tool.write_blinded_inputs()["path"]
    doc = ts.bs.read(inputs, sha(inputs))
    fit = ts.numpy_fit(fam, "full")
    assert doc["df"] == 12 and doc["inputs_sha256"] == sha(inputs)
    assert math.isclose(doc["sigma_A_pp"], math.sqrt(2 * sum(c["rss"] for c in fit.values()) / 12), rel_tol=1e-12)
    job = w.plan()["hosts"][hosts[0]]["jobs"][0]
    a0_n = {"kind": "a0_arm", "arm": "a0", "seed": 1103, "edit": None, "recipe": "B", "family": fam}
    assert [c[0] for c in w.rules.arm_commands(job, "p")] == ["calibrate"]
    argv = w.rules.arm_commands(job, "p")[0][1]
    base = w.rules.arm_commands(a0_n, "p")[0][1]           # N's command form (block 0's a0_arm on Llama; same engine)
    def strip(a):                                      # the command less its arm, seed and edit flags and values
        out, skip = [], False
        for x in a:
            if skip:
                skip = False
            elif x in ("--arms", "--seeds", "--edit"):
                skip = True
            else:
                out.append(x)
        return out
    assert strip(argv) == strip(base) and argv[argv.index("--checkpoints") + 1] == "e1"


# ===== 7. judges, seal and states (items 6, 7, 10, 11; DESO item 26; GXB O7; Part 2 §2.5, §2.6) ====================
def done_block_a(w) -> list[str]:
    hosts = released_a(w)
    for host in hosts:
        pull_planted(w, host)
        w.tool.record_done(host)
    return hosts


def rejudged_on_disk(w) -> None:
    """The 7 re-judged units' COMPLETE.json at their pinned paths under ROOT (N's in block 0's copy, the side units and
    theta0 in their own trees), each pin set TEST-LOCALLY to its file."""
    complete = {}
    for arm, seed in w.r78.block0_runs(w.family):
        rel = f"tmp/family-probe-s78-{w.family}-0/retrieved/{w.family}-0-1/tree/round1/{seed}-{arm}-e1-a1"
        complete[(arm, seed)] = sha(write(w.repo / rel / "COMPLETE.json", {"complete": True, "u": SENTINELS[0], "n": rel}))
    n_units(w, complete)
    for key, u in w.r78.KIT[w.family]["a0_units"].items():
        w.mp.setitem(u, "complete_sha256", sha(write(w.repo / u["path"] / "COMPLETE.json", {"complete": True, "k": key})))


def test_units_of_block_a_lists_21_units_and_the_7_re_judged_ones_and_waits_for_n(wa):
    """Item 7 (DESO item 26; X5): block A's judged units are its 21 runs' units (in this copy's pulled trees) and the
    7 re-judged ones, OLMo-2-7B 3 N + 3 a0 + theta0, at their repository paths (N's in block 0's copy); while
    N_UNITS is null the list refuses (never a null path); plan_tool's judge_required_units reads the same 7."""
    w = wa
    done_block_a(w)
    judge = importlib.import_module("judge_units_stage1")
    w.mp.setattr(judge, "JUDGES", REPO / "scripts" / "gate_b_mac_judges")   # Gate B's units.py, read only
    w.mp.syspath_prepend(str(REPO / "scripts" / "gate_b_mac_judges"))
    w.mp.delitem(sys.modules, "units", raising=False)
    plan = w.plan()
    w.mp.setitem(w.r78.N_UNITS, w.family, None)
    with pytest.raises(judge.gate_b_units().Refusal, match="re-judged units \\['N R 1101', 'N R 1102', 'N R 1103'\\] are null"):
        judge.block_units(plan, "A", w.root, w.repo)
    rejudged_on_disk(w)
    found = judge.block_units(plan, "A", w.root, w.repo)
    kinds = [u["kind"] for u in found]
    assert kinds.count("arm") == 20 and kinds.count("a0_arm") == 1 and kinds.count("re-judged") == 7
    paths = {str(u["path"].relative_to(w.repo)) for u in found if u["kind"] == "re-judged"}
    assert f"tmp/family-probe-s78-{w.family}-0/retrieved/{w.family}-0-1/tree/round1/1101-R-e1-a1" in paths
    req = w.tool.judge_required_units(plan, "A")
    assert len(req) == 28 and sum(v.startswith("re-judged ") for v in req.values()) == 7
    out = w.repo / "records" / "units-A.txt"
    assert judge.main(["units-of-block", "A", "--out", str(out), "--plan", str(w.root / "plan.json")]) == 0
    assert len(out.read_text().splitlines()) == 28


def test_seal_of_block_a_names_block_0s_and_the_scorer_blocks_seals_by_sha256(wa):
    """GXB O7: block A's seal refuses until block 0's and the scorer block's copies are sealed, then names both seal
    records by path and SHA-256 and carries their named exceptions (Llama's a0-1103 task loss; W1-18's flags); block A
    is complete once its judge launches are recorded (here: named by judge not-run decisions, the 7-8B A's route)."""
    w = wa
    done_block_a(w)
    assert w.tool.release("A")["launches_released"] == 3   # both judge launches (they wait for the arm pods)
    seal = load_by_path("seal_k2", w.root / "seal.py")
    with pytest.raises(SystemExit, match="block A is not complete"):
        seal.seal_block("A")
    decision = w.record({"kind": "stage1 judge not-run decision", "block": "A", "judges": ["harmbench", "granite"],
                         "reason": "synthetic", "utc": "2026-11-05T12:00:00Z", "recorded_by": "test"})
    w.tool.record_judge_not_run(str(decision), sha(decision))
    with pytest.raises(SystemExit, match="block 0 of olmo2-7b is not sealed|block 0's working copy .* has no readable"):
        seal.seal_block("A")
    s0 = seal_sibling(w, "0", {"named_exceptions": [{"what": "synthetic exception", "host": "h", "files": ["f"],
                                                     "fields": []}]})
    ssc = seal_sibling(w, "sc")
    got = seal.seal_block("A")
    doc = json.loads((w.root / "seals" / "block-A.json").read_text())
    assert [(c["block"], c["sha256"]) for c in doc["copies"]] == [("0", sha(s0)), ("sc", sha(ssc))]
    assert doc["named_exceptions"] == [{"what": "synthetic exception", "host": "h", "files": ["f"], "fields": [],
                                        "copy_block": "0"}]
    assert got["files"] == len(doc["files"]) and not any(s in (w.root / "seals" / "block-A.json").read_text()
                                                         for s in SENTINELS)
    assert all(f["class"] == "sealed" for f in doc["files"] if f["path"].endswith(("COMPLETE.json", "summary.json",
                                                                                  "query_loss.jsonl")))


def test_the_named_exceptions_of_block_0_and_the_scorer_block(wa):
    """P2 §2.5, DESO item 25: Llama-3.1-8B's block 0 names its a0-1103 unit's eval/e1/query_loss.jsonl as the one
    readable exception (its COMPLETE.json stays sealed, named by its one key evaluation.query_loss); OLMo-2-7B's names
    none; the scorer block names its W1-18 job's outputs (§4.2)."""
    seal = load_by_path("seal_k2_exc", wa.root / "seal.py")
    jobs = [{"kind": "arm", "arm": "R", "seed": 1101, "status": "complete", "unit": "round1/1101-R"},
            {"kind": "a0_arm", "arm": "a0", "seed": 1103, "status": "complete", "unit": "round1/1103-a0-e1-a1"}]
    llama = {"family": "llama31-8b", "hosts": {"llama31-8b-0-1": {"block": "0", "jobs": jobs}}}
    got = seal.named_exceptions(llama, "0")
    assert got["files"] == {("llama31-8b-0-1", "round1/1103-a0-e1-a1/eval/e1/query_loss.jsonl")}
    assert got["named"][0]["fields"] == [{"file": "round1/1103-a0-e1-a1/COMPLETE.json", "keys": ["evaluation.query_loss"]}]
    assert seal.named_exceptions({**llama, "family": "olmo2-7b"}, "0") == {"files": set(), "named": []}
    sc = {"family": "olmo2-7b", "hosts": {"olmo2-7b-sc-1": {"block": "sc", "jobs": [
        {"kind": "w1_18", "status": "complete", "outputs": {"job-0/w1_18/overrefusal_checks__olmo2-7b.json": hx("r")}}]}}}
    assert seal.named_exceptions(sc, "sc")["files"] == {("olmo2-7b-sc-1", "job-0/w1_18/overrefusal_checks__olmo2-7b.json")}


def test_the_state_rule_keeps_a0_1104_until_its_references_and_the_list_names_every_stopped_pod(wa):
    """Part 2 §2.6, DESO2 item 31: the per-block deletion list names every stopped pod of the block, each with its e1
    states verified and the backup's manifest at its SHA-256; the pod holding a0-1104's e1 state is kept (the list
    refuses) until every reference job at 1104 in the family's block-B copy is complete."""
    w = wa
    hosts = done_block_a(w)
    st = load_by_path("states_k2", w.root / "states_tool.py")
    for host in hosts:
        write(w.root / "hosts" / host / "pod.json", {"id": "synthetic"})
        write(w.root / "retrieved" / host / "states-e1-check-20261120T000000Z.json",
              {"kind": st.RECORD_KIND, "host": host, "checkpoint": "e1", "verified_units": 3})
    manifest = write(w.repo / "backup" / "manifest.json", {"release": "tag-1", "files": []})
    a0_host = next(h for h, x in w.plan()["hosts"].items() if any(j["arm"] == "a0" for j in x["jobs"]))

    def deletion_list(pods, tag="tag-1"):
        p = w.record({"kind": "stage1-78b deletion list", "version": 1, "block": "A", "pods": pods,
                      "backup": {"tag": tag, "manifest": {"path": str(manifest), "sha256": sha(manifest)}},
                      "utc": "2026-11-20T12:00:00Z", "recorded_by": "test"})
        return str(p), sha(p)

    keep = st.keep_list()["pods"]
    assert keep[a0_host]["kept_until"] == ["the references at seed 1104 have used its a0 e1 state"]
    assert all(not keep[h]["kept_until"] for h in hosts if h != a0_host)
    with pytest.raises(SystemExit, match="hold an a0 e1 state at 1104-1107 .*" + a0_host):
        st.check_deletion_list(*deletion_list(hosts))
    with pytest.raises(SystemExit, match="must name every stopped pod"):
        st.check_deletion_list(*deletion_list(hosts[:-1]))
    write(w.repo / "tmp" / "family-probe-s78-olmo2-7b-B" / "plan.json", {"hosts": {"olmo2-7b-b-9": {"jobs": [
        {"kind": "ref_eval", "seed": 1104, "status": "complete"}, {"kind": "safe_lora", "seed": 1104, "status": "planned"}]}}})
    with pytest.raises(SystemExit, match="hold an a0 e1 state"):
        st.check_deletion_list(*deletion_list(hosts))
    write(w.repo / "tmp" / "family-probe-s78-olmo2-7b-B" / "plan.json", {"hosts": {"olmo2-7b-b-9": {"jobs": [
        {"kind": "ref_eval", "seed": 1104, "status": "complete"}, {"kind": "safe_lora", "seed": 1104, "status": "complete"}]}}})
    assert st.check_deletion_list(*deletion_list(hosts))["pods"] == 6
    with pytest.raises(SystemExit, match="not the named release tag's"):
        st.check_deletion_list(*deletion_list(hosts, tag="tag-2"))
    (w.root / "retrieved" / hosts[0] / "states-e1-check-20261120T000000Z.json").unlink()
    with pytest.raises(SystemExit, match="whose e1 states are not verified"):
        st.check_deletion_list(*deletion_list(hosts))


# ===== 8. the scorer block: K-1's command words, K-4's idle lines for N's units, R-16's strict unit form ===========
def test_k1_kr6_each_oext_kind_is_checked_by_its_command_word_from_oext_wrapper_commands(tmp_path, monkeypatch):
    """GXB K-1, KR6: one wrapper serves c0 and the O-ext kinds, so the planner checks each kind's command word from
    rules_78b.OEXT_WRAPPER_COMMANDS (c0 'lean', o_only and o_only_with_regenerate 'unit', W1-18 'w1_18') and that word's
    files in the pin the job packs: c0 refuses without the lean copy; a word that is not the kind's refuses."""
    w, sb = sc_world(tmp_path, monkeypatch)
    try:
        w.fill(oext=True, c0=True)
        assert len(w.init([{"kind": "c0"}, {"kind": "o_only"}], amount=None, dry_run=True)["pods"]) == 2
        oext = w.r78.OEXT_78B[w.family]
        files = {k: v for k, v in oext["files"].items() if k != "scripts/scale78b/lean_eval_job_78b.py"}
        w.mp.setitem(w.r78.OEXT_78B, w.family, {**oext, "files": files})
        with pytest.raises(SystemExit, match="c0: OEXT_78B\\['olmo2-7b'\\] does not list scripts/scale78b/lean_eval_job_78b.py"):
            w.init([{"kind": "c0"}], amount=None, dry_run=True)
        assert len(w.init([{"kind": "o_only"}], amount=None, dry_run=True)["pods"]) == 1
        w.mp.setitem(w.r78.OEXT_78B, w.family, oext)
        w.mp.setitem(w.r78.OEXT_WRAPPER_COMMANDS, "c0", "unit")
        with pytest.raises(SystemExit, match="c0 runs the wrapper's 'lean' command, but rules_78b.OEXT_WRAPPER_COMMANDS names 'unit'"):
            w.init([{"kind": "c0"}], amount=None, dry_run=True)
        w.mp.setitem(w.r78.OEXT_WRAPPER_COMMANDS, "c0", "lean")
        w.mp.setitem(w.r78.OEXT_WRAPPER_COMMANDS, "o_only", "lean")
        with pytest.raises(SystemExit, match="o_only runs the wrapper's 'unit' command"):
            w.init([{"kind": "o_only"}], amount=None, dry_run=True)
        w.mp.setitem(w.r78.OEXT_WRAPPER_COMMANDS, "o_only", "unit")
        route = w1_18_route(w.r78)
        w.mp.setattr(w.r78, "W1_18_78B", route)
        with pytest.raises(SystemExit, match="w1_18: W1_18_78B does not list scripts/stage1/limits/overrefusal_checks.py"):
            w.init([{"kind": "w1_18"}], amount=None, dry_run=True)
        w.mp.setattr(w.r78, "W1_18_78B", {**route, "files": {**route["files"],
                                                             "scripts/stage1/limits/overrefusal_checks.py": hx("orc")}})
        assert len(w.init([{"kind": "w1_18"}], amount=None, dry_run=True)["pods"]) == 1
        branch = w.repo / w.r78.BRANCH_78B[w.family]["path"]       # K-8 in the scorer block: read by its bytes
        branch.write_text(branch.read_text() + " ")
        with pytest.raises(SystemExit, match=r"BRANCH_78B\['olmo2-7b'\] \(records/branch-olmo2-7b.json\) is missing or differs"):
            w.init([{"kind": "o_only"}], amount=None, dry_run=True)
    finally:
        close(w)


@pytest.mark.parametrize("family", FAMILIES)
def test_k4_ns_o_only_with_regenerate_pods_are_scorer_block_pods_with_idle_lines_named_by_arm_and_seed(tmp_path,
                                                                                                      monkeypatch, family):
    """GXB K-4, DES E5, R-16: N's units (OLMo-2-7B R 1101-1103; Llama-3.1-8B R 1101-1103 and a0 1103) are planned as
    o_only_with_regenerate pods of the scorer block by (arm, seed), each with its N inputs (n_complete, and an R
    unit's sealed edit), each printing its need and idle-storage line (they keep states); they wait for N_UNITS; the
    side unit at the same seed (OLMo's a0-1101) is another unit; block 0's printout is unchanged (test_42's bytes)."""
    w, sb = sc_world(tmp_path, monkeypatch, family)
    try:
        w.fill(oext=True)
        n_jobs = [{"kind": "o_only_with_regenerate", "arm": a, "seed": s} for a, s in w.r78.block0_runs(family)]
        with pytest.raises(SystemExit, match="N_UNITS waits for block 0"):
            w.init(n_jobs[:1], amount=None, dry_run=True)
        n_units(w)
        out = w.init(n_jobs, amount=None, dry_run=True)
        assert len(out["pods"]) == (3 if family == "olmo2-7b" else 4)
        for pod, job in zip(out["pods"], n_jobs):
            want = {f"n_complete:{job['arm']}:{job['seed']}", "oext_bank", "oext_record"} | \
                ({f"regen_edit:R:{job['seed']}"} if job["arm"] == "R" else set())
            assert set(pod["inputs"]) == want and pod["idle_storage"]["keeps_states"] is True
        idle = [x for x in out["need_lines"] if x.startswith(f"idle storage {family}-sc-")]
        assert len(idle) == len(n_jobs) and all("keeps the regenerated a0 unit's states" in x for x in idle)
        if family == "olmo2-7b":                         # the seed key: R_1101 and the side a0-1101 are two units
            both = w.init([{"kind": "o_only_with_regenerate", "arm": "R", "seed": 1101},
                           {"kind": "o_only_with_regenerate", "arm": "a0", "seed": 1101}], amount=None, dry_run=True)
            assert [sorted(p["inputs"])[0] for p in both["pods"]] == ["n_complete:R:1101", "oext_bank"]
    finally:
        close(w)


# ===== 9. the rules layer's R-32 and R-33 (RK; GXB R-20, R-21, R-32, R-33) =========================================
def test_r32_w1_18_78b_takes_track_os_files_and_side_units_form(wa):
    """GXB R-20, R-32: W1_18_78B is the maker's printed {files, side_units}: the wrapper and exactly each named
    family's W1 index at its standard path (no X or Y index, no look-alike in any case); side_units each family's W1-18
    units with the KIT a0_units path (under the data root tmp/) and both SHA-256s (theta0's job pin filled first, R-20)."""
    r78 = wa.r78
    good = w1_18_route(r78)
    assert r78.w1_18_route_problem(good) is None
    assert r78.w1_18_route_problem({"files": good["files"]}) == "its keys are not exactly files and side_units"
    olmo_only = {"files": {k: v for k, v in good["files"].items() if "llama" not in k},
                 "side_units": {"olmo2-7b": good["side_units"]["olmo2-7b"]}}
    assert r78.w1_18_route_problem(olmo_only) is None                   # [C]: OLMo-2-7B's alone
    for change, match in (
            (lambda d: d["files"].pop(r78.W1_18_SCRIPT), "do not pin the wrapper"),
            (lambda d: d["files"].pop("scripts/scale78b/settings/OEXT-78B-W1__llama31-8b.json"), "exactly the W1-18 index"),
            (lambda d: d["files"].update({"scripts/scale78b/settings/OEXT-78B__olmo2-7b.json": hx("x")}), "exactly the W1-18"),
            (lambda d: d["files"].update({"scripts/other/oext-78b-w1__olmo2-7b.json": hx("x")}), "exactly the W1-18"),
            (lambda d: d["side_units"]["olmo2-7b"]["untuned"].update(job_sha256=None), "job_sha256 is not KIT"),
            (lambda d: d["side_units"]["olmo2-7b"]["a0-1101"].update(path="elsewhere/u"), "path is not KIT a0_units'"),
            (lambda d: d["side_units"]["llama31-8b"].pop("a0-1102"), "is not the family's W1-18 units"),
            (lambda d: d["side_units"].update({"olmo2-1b": {}}), "families among")):
        bad = json.loads(json.dumps(good))
        change(bad)
        assert match in str(r78.w1_18_route_problem(bad)), match
    wa.mp.setattr(r78, "W1_18_78B", {**good, "side_units": {}})
    with pytest.raises(r78.Refused, match="GXB R-20, R-32"):
        r78.sc_pin_values("olmo2-7b", json.loads((REPO / wa.rules.PINS_78B).read_text()))


def test_r33_the_index_and_w1_18_record_names_are_exactly_the_standard_ones_and_plan_for_sigma_refuses(wa):
    """GXB R-33 (KR2-4, KR2-5): an O-ext pin holds exactly one index, at its standard path, its own family's and
    engine's: a look-alike in another folder or case, or the W1 index, refuses; its one W1-18 record is
    overrefusal_checks__<its family>.json, at the branch record's w1_18_record_sha256 when the branch comes from W1-18, none
    under Branch full by default; plan_for_sigma refuses (not raises) an int too large for a float."""
    r78, fam = wa.r78, "olmo2-7b"
    base = {"files": {r78.OEXT_WRAPPER_78B: hx("w"), f"scripts/scale78b/settings/OEXT-78B__{fam}.json": hx("i")},
            "inputs": {"oext_bank": hx("b"), "oext_record": hx("r")}}
    assert r78.oext_form_problem(base, fam, "X") is None
    for extra in ("scripts/other/OEXT-78B__llama31-8b.json", "scripts/scale78b/settings/oext-78b-y__olmo2-7b.json",
                  f"scripts/scale78b/settings/OEXT-78B-W1__{fam}.json"):
        bad = {**base, "files": {**base["files"], extra: hx("x")}}
        assert "2 O-ext index file(s)" in r78.oext_form_problem(bad, fam, "X"), extra
    rec = f"{r78.W1_18_RECORD_DIR}overrefusal_checks__{fam}.json"
    other = f"{r78.W1_18_RECORD_DIR}overrefusal_checks__llama31-8b.json"
    assert "another family's W1-18 record" in r78.oext_form_problem({**base, "files": {**base["files"], other: hx("r")}},
                                                                     fam, "X")
    loose = {**base, "files": {**base["files"], f"{r78.W1_18_RECORD_DIR}record.json": hx("r")}}
    assert "not the standard overrefusal_checks__<family>.json" in r78.oext_form_problem(loose)
    with_rec = {**base, "files": {**base["files"], rec: hx("the record")}}
    w118 = {"source": "w1_18", "w1_18_record_sha256": hx("the record")}
    assert r78.oext_w1_18_record_problem(with_rec, fam, w118) is None
    assert "is not the branch record's" in r78.oext_w1_18_record_problem(with_rec, fam, {**w118, "w1_18_record_sha256": hx("x")})
    assert "name exactly" in r78.oext_w1_18_record_problem(base, fam, w118)
    assert "names none" in r78.oext_w1_18_record_problem(with_rec, fam, {"source": "default", "w1_18_record_sha256": None})
    assert r78.oext_w1_18_record_problem(base, fam, {"source": "default", "w1_18_record_sha256": None}) is None
    for bad in (10 ** 400, -(10 ** 400), float("inf")):
        with pytest.raises(r78.Refused, match="is not a finite number of percentage points"):
            r78.plan_for_sigma(bad)
    assert "sigma_A_pp is blinded_sigma.py's sigma_A" in r78.plan_b_record_problem(
        {"kind": r78.PLAN_B_RECORD_KIND, "version": 1, "plan": "A", "sr2_adopted": True, "sr2_reason": None,
         "plan_basis": "sigma_A", "sigma_A_pp": 10 ** 400, "blinded_sigma_output_sha256": hx("o"),
         "blinded_sigma_inputs_sha256": hx("i"), "utc": "u", "recorded_by": "t"})


def test_w1_18_is_one_pod_in_olmos_scorer_copy_and_the_first_o_job(tmp_path, monkeypatch):
    """DES E2, DESO2 item 37, GXB K-3: the W1-18 pod is planned only in OLMo-2-7B's scorer-block copy and only while no
    500-bank job is planned or complete there (it is the first O job)."""
    w, sb = sc_world(tmp_path, monkeypatch)
    try:
        w.fill(oext=True)
        route = w1_18_route(w.r78)
        route["files"]["scripts/stage1/limits/overrefusal_checks.py"] = hx("orc")
        w.mp.setattr(w.r78, "W1_18_78B", route)
        w.pack(*sb.oext_inputs(w))
        w.init([{"kind": "o_only"}])
        with pytest.raises(SystemExit, match="W1-18 is the first O job, before any O-ext pod; o_only is already planned"):
            w.init([{"kind": "w1_18"}], amount=None, dry_run=True)
    finally:
        close(w)
    w, sb = sc_world(tmp_path / "l", monkeypatch, "llama31-8b")
    try:
        w.fill(oext=True)
        w.mp.setattr(w.r78, "W1_18_78B", route)
        with pytest.raises(SystemExit, match="is planned in olmo2-7b's scorer-block copy, not llama31-8b's"):
            w.init([{"kind": "w1_18"}], amount=None, dry_run=True)
    finally:
        close(w)


def test_kr4_the_scorer_block_reads_its_own_stop_record_and_plans_the_main_config_retrain(tmp_path, monkeypatch):
    """KR4, DESO2 item 36 (2), item 14: in the stopped family's scorer copy the planner reads the pinned stop record
    against its own anchor host's JOB-DONE.json, then plans the a0-1101 retrain under the family's main config (recipe
    B; no RECIPE_S, no complete anchor job) and refuses the S_78 kinds for good."""
    (tmp_path / "records").mkdir()
    w, sb = sc_world(tmp_path, monkeypatch)
    try:
        host, _ = stopped_anchor(w, 3, counts={"kept": 61, "needed": 64})
        got = w.tool.record_anchor_stop(host, None, str(w.repo / "records" / "stop.json"))
        w.mp.setitem(w.r78.ANCHOR_STOP, "olmo2-7b", {"path": "records/stop.json", "sha256": got["sha256"]})
        w.mp.setattr(w.r78, "ENGINE_Y", sb.Y)
        out = w.init([{"kind": "retrain"}], amount=None, dry_run=True)
        assert [p["kind"] for p in out["pods"]] == ["retrain"] and w.r78.family_stopped("olmo2-7b")
        for kind in ("l1_scan", "rep_pass"):
            with pytest.raises(SystemExit, match=r"anchor job stopped \(ANCHOR_STOP\): " + kind + " never runs"):
                w.init([{"kind": kind}], amount=None, dry_run=True)
        with pytest.raises(SystemExit, match="retrain runs under recipe B only"):
            w.init([{"kind": "retrain", "recipe": "S"}], amount=None, dry_run=True)
    finally:
        close(w)


def test_safe_lora_plans_its_default_and_certify_points_only_at_7_8b(wa):
    """The lead (9 Nov; Part 2 §3.2: Safe LoRA at K = 78 only): stage1_rules.POINT_KINDS["safe_lora"] is ("default",
    "certify"); the 1B conditional and k12 points refuse by name when a job is built; block 0's jobs carry no point."""
    r = wa.rules
    assert r.POINT_KINDS["safe_lora"] == ("default", "certify")
    assert r.job_record("safe_lora", "a0", 1105, points=["default", "certify"])["points"] == ["default", "certify"]
    for point in ("conditional", "k12"):
        with pytest.raises(ValueError, match=f"safe_lora's {point} point is not run at 7-8B; Part 2 §3.2"):
            r.job_record("safe_lora", "a0", 1105, points=["default", point])
    with pytest.raises(ValueError, match="point 'other' is not one of"):
        r.job_record("safe_lora", "a0", 1105, points=["other"])
    assert all(not j.get("points") for j in r.r78.block0_jobs(wa.family))


# ===== 10. the fix round: K2V-1 to K2V-11 and GXB R-43 to R-45 ======================================================
def plan_b_doc(**change) -> dict:
    doc = {"kind": "stage1-78b block-B plan record", "version": 1, "plan": "A", "sr2_adopted": False,
           "sr2_reason": "blinding_test_not_verified", "plan_basis": "sigma_pool_N", "sigma_A_pp": None,
           "blinded_sigma_output_sha256": None, "blinded_sigma_inputs_sha256": None,
           "utc": "2026-11-20T12:00:00+00:00", "recorded_by": "test"}
    return {**doc, **change}


def test_r43_block_b_rederives_sr2s_status_and_refuses_a_hand_written_one_at_init_and_release(wb):
    """GXB R-43 (K2V-1; the verifier's P3a, P3b): block B's init and release re-derive SR-2's status from the pinned
    simulation and blinding records (as block A read it) and refuse a PLAN_B_78B whose status differs: 'adopted' while
    the blinding test is not verified (P3a), and 'not adopted' while both triggers pass (P3b)."""
    w = wb
    b_ready(w, sigma=None)                               # the kit's own record: not adopted (blinding), plan A
    seal_sibling(w, "A")
    assert w.init(dry_run=True)["plan"] == "A"
    out, inputs = blinded_output(w, 5.0)
    w.pin("PLAN_B_78B", w.record(plan_b_doc(plan="B9", sr2_adopted=True, sr2_reason=None, plan_basis="sigma_A",
                                            sigma_A_pp=5.0, blinded_sigma_output_sha256=sha(out),
                                            blinded_sigma_inputs_sha256=sha(inputs))))
    with pytest.raises(SystemExit, match=r"says SR-2 adopted True \(None\); the pinned records give False "
                                         r"\(blinding_test_not_verified\) \(GXB R-43\)"):
        w.init(dry_run=True, blinded=str(out))
    s = SR2(w, "B")                                      # both triggers pass now
    blinded = w.record({"df": 24, "inputs_sha256": sha(inputs), "kind": "scale-78b blinded sigma", "sigma_A_pp": 5.0,
                        "version": 1}, "blinded-b9.json")
    plan_b(w, blinded)
    kit = inputs.read_bytes()
    w.mp.setattr(w.tool, "kit_inputs", lambda gate: b"the kit's own rebuild (other bytes)")
    with pytest.raises(SystemExit, match="is not the one the kit writes from the block-A copies' parts"):
        w.init(dry_run=True, blinded=str(blinded))      # K2V-3: block B's init takes only the kit's inputs file
    w.mp.setattr(w.tool, "kit_inputs", lambda gate: kit)
    host_out = w.init(blinded=str(blinded), amount=3000.0, n_pods=len(w.rules.deal(w.rules.block_runs("B9", "B"), "B")))
    w.pin("PLAN_B_78B", w.record(plan_b_doc(sr2_reason="simulation_reading")))
    with pytest.raises(SystemExit, match="PLAN_B_78B now pins another plan record"):
        w.tool.release_hosts_ab(w.plan(), "B", [(host_out["hosts"][0], w.plan()["hosts"][host_out["hosts"][0]])])
    plan = w.plan()
    plan["blocks"]["B"]["plan_b"]["sha256"] = w.tool.r78.PLAN_B_78B["sha256"]
    with pytest.raises(SystemExit, match=r"the pinned records give True \(None\) \(GXB R-43\)"):
        w.tool.release_hosts_ab(plan, "B", [(host_out["hosts"][0], plan["hosts"][host_out["hosts"][0]])])
    assert s is not None


def test_r44_block_a_refuses_unless_the_blinding_record_verified_the_code_that_runs(wa):
    """GXB R-44 (K2V-8): the blinding record names blinded_sigma.py, record-done's code (this copy's plan_tool.py) and
    the two tests that hold both outputs by SHA-256, with a commit; block A's init and release refuse while it is null,
    off its form, or when any file differs now; release refuses a re-pinned record; init keeps its snapshot."""
    w = wa
    w.gate()
    w.fill(blinding=False)
    with pytest.raises(SystemExit, match="the pin SR2_BLINDING_RECORD is null"):
        w.init(dry_run=True)
    p = w.blinding()
    doc = json.loads(p.read_text())
    for change, match in ((dict(commit="nothex"), "a 40-hex commit"), (dict(files={}), "files exactly"),
                          (dict(files={**doc["files"], "x.py": hx("x")}), "files exactly")):
        bad = w.record({**doc, **change})
        w.mp.setattr(w.tool, "SR2_BLINDING_RECORD", {"path": w.rel(bad), "sha256": sha(bad)})
        with pytest.raises(SystemExit, match="is not a 'stage1-78b sr2 blinding test record'"):
            w.init(dry_run=True)
    for rel in BLINDING_FILES:
        w.blinding(files={rel: hx("another " + rel)})
        where = "that runs here" if rel.endswith("plan_tool.py") else "in this checkout"
        with pytest.raises(SystemExit, match=f"verified another {rel} than the one {where}"):
            w.init(dry_run=True)
    w.blinding()
    out = w.init(amount=3000.0)
    assert w.plan()["blocks"]["A"]["blinding"]["sha256"] == w.tool.SR2_BLINDING_RECORD["sha256"]
    plan = w.plan()
    name = out["hosts"][0]
    assert w.tool.release_hosts_ab(plan, "A", [(name, plan["hosts"][name])]) == [name]
    w.blinding(verified=False)
    with pytest.raises(SystemExit, match="SR2_BLINDING_RECORD now pins another record"):
        w.tool.release_hosts_ab(plan, "A", [(name, plan["hosts"][name])])
    (w.root / "plan_tool.py").write_text((w.root / "plan_tool.py").read_text() + "\n# a change after the verification\n")
    with pytest.raises(SystemExit, match="runkit/stage1-78b/plan_tool.py than the one that runs here"):
        w.tool.release_hosts_ab(plan, "A", [(name, plan["hosts"][name])])


def defer_one(w, hosts) -> tuple[str, str]:
    """The last job of the first host deferred (the runner's code "remaining"), record-done of every host, then defer:
    the job goes to a new block-A host, released and recorded complete there."""
    first = hosts[0]
    tree = w.root / "retrieved" / first / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    done["jobs"][-1].update(status="deferred", reason="remaining")
    done["jobs"][-1].pop("complete_sha256")
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    for h in hosts:
        w.tool.record_done(h)
    new = w.tool.defer(first)["to"]
    if new not in w.plan()["hosts"]:
        w.tool.release("A")
    return first, new


def test_k2v2_the_part_reads_each_runs_completed_unit_wherever_it_ran_after_a_deferral(wa):
    """K2V-2 (the verifier's P9): after a deferral in block A the part is written at the last record-done, its cell
    taken from the host where the job completed (the deferred job on the first host is skipped: a move took it); two
    complete units for one run refuse."""
    w = wa
    hosts = released_a(w)
    for host in hosts:
        pull_planted(w, host)
    first, new = defer_one(w, hosts)
    pull_planted(w, new)
    out = w.tool.record_done(new)
    assert "path" in out["blinded_inputs_part"]
    job = w.plan()["hosts"][new]["jobs"][0]
    part = json.loads((w.repo / out["blinded_inputs_part"]["path"]).read_text())
    cell = part["entry"]["cells"][job["arm"]][str(job["seed"])]
    assert f"/retrieved/{new}/tree/" in cell["path"] and cell["complete_sha256"] == w.plan()["hosts"][new]["jobs"][0]["complete_sha256"]
    plan = w.plan()
    old = plan["hosts"][first]["jobs"][-1]
    old.update(status="complete", unit="round1/x", complete_sha256=hx("a second unit"))
    with pytest.raises(SystemExit, match="two complete units"):
        w.tool.blinded_inputs_part(plan, w.family)
    plan = w.plan()                                      # the moved host's deferred job, but no move took it along
    plan["hosts"][new]["jobs"][0].pop("deferred_from")
    with pytest.raises(SystemExit, match=f"{first}:{len(plan['hosts'][first]['jobs']) - 1} .* is not complete"):
        w.tool.blinded_inputs_part(plan, w.family)
    plan = w.plan()                                      # an open job on a host no move left
    plan["hosts"][hosts[1]]["jobs"][0].update(status="deferred")
    with pytest.raises(SystemExit, match=f"{hosts[1]}:0 .* is not complete"):
        w.tool.blinded_inputs_part(plan, w.family)


def test_k2v2_the_part_after_a_pre_job_requeue_of_a_whole_host(wa):
    """K2V-2: a block-A pod that failed before its job started is requeued (the log's pre-job failure and stop): its
    jobs run on the replacement host, and the part names their units there."""
    w = wa
    hosts = released_a(w)
    first = hosts[0]
    write(w.root / "hosts" / first / "orchestrate.jsonl",
          json.dumps({"event": "pre-job-failed", "step": "bootstrap"}) + "\n" + json.dumps({"event": "pre-job-stop", "exit": 0}) + "\n")
    new = w.tool.requeue(first)["to"]
    if new not in w.plan()["hosts"]:
        w.tool.release("A")
    for host in hosts[1:] + [new]:
        pull_planted(w, host)
        out = w.tool.record_done(host)
    assert "path" in out["blinded_inputs_part"], out
    part = json.loads((w.repo / out["blinded_inputs_part"]["path"]).read_text())
    paths = [c["path"] for v in part["entry"]["cells"].values() for c in v.values()]
    assert not any(f"/retrieved/{first}/" in x for x in paths) and any(f"/retrieved/{new}/" in x for x in paths)


def test_r45_the_orchestrators_hold_reads_branch_78b_by_its_bytes(tmp_path, monkeypatch):
    """GXB R-45 (K2V-4; the verifier's P8): a released scorer-block O-ext pod is not held once the family's branch
    record is pinned (read by its bytes); with the pin null, or its file off its bytes, it is held."""
    w, sb = sc_world(tmp_path, monkeypatch)
    try:
        w.fill(oext=True)
        w.pack(*sb.oext_inputs(w))
        host = w.init([{"kind": "o_only"}])["released"][0]
        orch = importlib.import_module("orchestrate")
        monkeypatch.setattr(orch, "log", lambda *a, **k: None)
        assert orch.w1_18_hold(host) is None
        branch = w.repo / w.r78.BRANCH_78B[w.family]["path"]
        branch.write_text(branch.read_text() + " ")
        with pytest.raises(SystemExit, match="waits for W1-18's branch record \\(G1\\): olmo2-7b's branch record is not the pinned one"):
            orch.w1_18_hold(host)
        w.mp.setitem(w.r78.BRANCH_78B, w.family, None)
        with pytest.raises(SystemExit, match="waits for W1-18's branch record"):
            orch.w1_18_hold(host)
    finally:
        close(w)


def test_k2v3_only_the_kits_own_parts_are_merged(wa):
    """K2V-3 (the verifier's P4b): write-blinded-inputs reads each family's part at its one place and only when it is
    the part its block-A copy's plan.json gives again; a hand-made or edited part, a part of another gate, or no part
    refuses; init-block B and record-plan-b-78b compare the inputs file with the kit's rebuild (tests above)."""
    w = wa
    hosts = released_a(w)
    for host in hosts:
        pull_planted(w, host)
        w.tool.record_done(host)
    part = w.tool.part_path(w.family)
    good = part.read_bytes()
    doc = json.loads(good)
    doc["entry"]["cells"]["A1"]["1102"]["complete_sha256"] = hx("a hand-made cell")
    part.write_bytes(canon(doc))
    with pytest.raises(SystemExit, match="is not the one its block-A copy's plan.json gives"):
        w.tool.write_blinded_inputs()
    part.unlink()
    with pytest.raises(SystemExit, match="part is missing at its place"):
        w.tool.write_blinded_inputs()
    part.write_bytes(good)
    doc = json.loads((w.repo / w.r78.GATE_78B["path"]).read_text())
    w.pin("GATE_78B", w.record({**doc, "balance_usd": 1.0}))   # another gate record pinned after block A's init
    with pytest.raises(SystemExit, match="planned under another gate record than the pinned one"):
        w.tool.write_blinded_inputs()


def test_k2v5_the_anchor_stopped_part_is_read_by_blinded_sigma_with_per_role_engines(wa, monkeypatch):
    """K2V-5, S-6 (the verifier's P6): on OLMo-2-7B with its anchor stop pinned (and read against its JOB-DONE.json),
    block A runs H1, S1, S4, R and a0 only; record-done's part names the design anchor_stopped and the stop record, the
    engines per role (R-13: a0, R and block A each its own), and through write-blinded-inputs the real blinded_sigma.py
    reads it: df 6 and sigma_A equal to an independent numpy fit."""
    w = wa
    monkeypatch.syspath_prepend(str(REPO))
    ts = load_by_path("ts_blinded_sigma_tests_k2_stop", REPO / "scripts/scale78b/tests/test_blinded_sigma.py")
    fam, r78 = w.family, w.r78
    split = ts.ENGINES_SPLIT
    r_edits = {d: ts.r_edit(fam, d) for d in range(1, 6)}
    m_edits = {a: ts.method_edit(fam, a) for a in ("A1", "L1", "H1", "S1", "S3", "S4")}
    for d in (4, 5):
        monkeypatch.setitem(r78.R_DRAW_SOURCES[fam], d, {"path": f".ai/inputs/test/R_d{d}.json",
                                                         "sha256": hashlib.sha256(r_edits[d]).hexdigest()})
    w.gate(option="C", engines={"a0": split["a0"], "R": split["R"]})
    w.fill()
    for a, data in m_edits.items():
        monkeypatch.setitem(r78.METHOD_EDITS[fam], a, {"path": f".ai/inputs/test/{a}.json",
                                                       "sha256": hashlib.sha256(data).hexdigest(), "rows": METHOD_ROWS[a]})
    w.fill(edits=False, branch=False, oext=False)
    done = w.repo / "records" / "JOB-DONE.json"
    done.write_bytes(b"anchor job done (synthetic)")
    stop = write(w.repo / "records" / "stop.json", canon({**json.loads(SHARED_STOP.read_bytes()),
                                                         "job_done_sha256": sha(done)}).decode())
    w.pin("ANCHOR_STOP", stop, fam)
    count = ts.unsafe_count
    complete = {}
    for arm, seed in r78.block0_runs(fam):
        rel = f"tmp/family-probe-s78-{fam}-0/retrieved/{fam}-0-1/tree/round1/{seed}-{arm}-e1-a1"
        complete[(arm, seed)] = ts.make_unit(w.repo / rel, fam, arm, seed, count(fam, arm, seed), r_edits[seed - 1100],
                                             engine=split["R"])
    units = n_units(w, complete)
    for key in units:
        units[key]["edit_sha256"] = hashlib.sha256(r_edits[int(key.split("-")[1]) - 1100]).hexdigest()
    for seed, u in r78.KIT[fam]["a0_units"].items():
        if seed != "untuned":
            monkeypatch.setitem(u, "complete_sha256", ts.make_unit(w.repo / u["path"], fam, "a0", seed,
                                                                   count(fam, "a0", seed), engine=split["a0"]))
    stopped = [(a, s) for s in (1102, 1103, 1104) for a in ("H1", "S1", "S4")] + [("R", 1104), ("R", 1105), ("a0", 1104)]
    hosts = w.init(n_pods=len(w.rules.deal(stopped, "A")), amount=3000.0, anchor_job_done=str(done))["hosts"]
    for host in hosts:
        h = w.plan()["hosts"][host]
        tree = w.root / "retrieved" / host / "tree"
        recs = []
        for i, job in enumerate(h["jobs"]):
            arm, seed = job["arm"], job["seed"]
            edit = None if arm == "a0" else (r_edits[seed - 1100] if arm == "R" else m_edits[arm])
            key = ts.make_unit(tree / unit_name(job), fam, arm, seed, count(fam, arm, seed), edit)
            recs.append({"index": i, "kind": job["kind"], "arm": arm, "seed": seed, "engine": "X", "engine_sha256": X,
                         "status": "complete", "unit": unit_name(job), "complete_sha256": key, "outputs": {}})
        write(tree / "JOB-DONE.json", {"host": host, "jobs": recs})
        w.tool.record_done(host)
    pdoc = json.loads(w.tool.part_path(fam).read_text())
    assert pdoc["entry"]["design"] == "anchor_stopped" and set(pdoc["entry"]["edits"]) == {"H1", "S1", "S4"}
    assert pdoc["entry"]["engine"] == {"a0": split["a0"], "R": split["R"], "block_a": X}
    assert pdoc["entry"]["anchor_stop"] == {"path": "records/stop.json", "sha256": sha(stop)}
    got = w.tool.write_blinded_inputs()
    inputs = w.repo / got["path"]
    assert json.loads(inputs.read_text())["families"][fam]["anchor_stop"]["path"] == "../../records/stop.json"
    doc = ts.bs.read(inputs, sha(inputs))
    fit = ts.numpy_fit(fam, "anchor_stopped")
    assert doc["df"] == sum(c["df"] for c in fit.values()) == 6
    assert math.isclose(doc["sigma_A_pp"], math.sqrt(2 * sum(c["rss"] for c in fit.values()) / 6), rel_tol=1e-12)
    s = SR2.__new__(SR2)                                 # GXB R-50: record-plan-b-78b's own blinded_sigma.read, real
    s.w, s.families = w, (fam,)
    s.sim("C", reduced=True, stopped=(fam,))
    monkeypatch.setattr(w.tool, "blinded_sigma_script", lambda: REPO / "scripts/scale78b/blinded_sigma.py")
    real = w.record(doc, "blinded-real.json")
    rec = w.tool.record_plan_b_78b(str(w.noise), str(real), sha(real), "test", str(w.repo / "records" / "pb-real.json"))
    assert rec["sr2_adopted"] is True and rec["blinded_sigma"] == {"sigma_A_pp": doc["sigma_A_pp"], "df": 6}
    assert rec["plan"] == w.r78.plan_for_sigma(doc["sigma_A_pp"])
    hand = w.record({**doc, "sigma_A_pp": doc["sigma_A_pp"] + 0.5}, "blinded-hand.json")
    with pytest.raises(SystemExit, match="is not the one blinded_sigma.read gives on the kit's inputs file"):
        w.tool.record_plan_b_78b(str(w.noise), str(hand), sha(hand), "test", str(w.repo / "records" / "pb-hand.json"))
    monkeypatch.setattr(w.tool, "blinded_sigma_script", lambda: w.repo / "records" / "blinded-hand.json")
    with pytest.raises(SystemExit, match="is not the file the blinding record verified"):
        w.tool.record_plan_b_78b(str(w.noise), str(real), sha(real), "test", str(w.repo / "records" / "pb-x.json"))
    w.tool.release_hosts_ab(w.plan(), "A", [])           # the stop record is re-read at release (KR4)
    done.write_bytes(b"another JOB-DONE.json")
    with pytest.raises(SystemExit, match="not the anchor job's"):
        w.tool.release_hosts_ab(w.plan(), "A", [])
    stop2 = write(w.repo / "records" / "stop2.json", canon({**json.loads(SHARED_STOP.read_bytes()),
                                                           "job_done_sha256": sha(done)}).decode())
    w.pin("ANCHOR_STOP", stop2, fam)                     # a re-pinned record for another JOB-DONE.json
    with pytest.raises(SystemExit, match="the anchor job's JOB-DONE.json differs from the one read at init-block"):
        w.tool.release_hosts_ab(w.plan(), "A", [])


def test_k2v6_the_remaining_checks_each_refuse(wa, monkeypatch):
    """K2V-6: block A's part refuses an unpulled unit and two engines; the sibling seal refuses a seal record off its
    SHA-256; under [C] the gate's sigma_F plan is OLMo-2-7B's own (a noise output whose families' plans differ), at
    record-gate-78b and at init."""
    w = wa
    hosts = released_a(w)
    for host in hosts:
        pull_planted(w, host)
        w.tool.record_done(host)
    plan = w.plan()
    plan["hosts"][hosts[0]]["jobs"][0]["pulled"] = False
    with pytest.raises(SystemExit, match="complete but not pulled with its unit"):
        w.tool.blinded_inputs_part(plan, w.family)
    assert not w.tool.block_a_arms_done(plan)
    plan = w.plan()
    plan["hosts"][hosts[1]]["engine_sha256"] = hx("another engine")
    with pytest.raises(SystemExit, match="block A ran on two engines"):
        w.tool.blinded_inputs_part(plan, w.family)
    seal = seal_sibling(w, "sc")
    seal.write_text(seal.read_text() + " ")
    with pytest.raises(SystemExit, match="seal record in tmp/family-probe-s78-olmo2-7b-sc/ is missing or differs"):
        w.tool.sibling_seal(w.family, "sc")
    got = w.gate(option="C", plan="A", sigma_f=("B9", False), sigma_f_llama=("H", False))
    assert got["sigma_F_plan"] == "B9"
    doc = json.loads((w.repo / w.r78.GATE_78B["path"]).read_text())
    w.pin("GATE_78B", w.record({**doc, "sigma_F_plan": "H"}))
    with pytest.raises(SystemExit, match="sigma_F_plan 'H' is not the plan N's noise reading gives \\('B9'"):
        w.tool.gate_noise_check(json.loads((w.repo / w.r78.GATE_78B["path"]).read_text()), str(w.noise))


def test_k2v6_block_bs_inputs_hash_and_a0_1105_to_1107_states(wb):
    """K2V-6: block B refuses a plan record whose inputs hash is not blinded_sigma.py's output's; block B's a0 pods
    (1105-1107) are kept for their references like block A's a0-1104."""
    w = wb
    blinded = b_ready(w, sigma=4.0)
    seal_sibling(w, "A")
    doc = json.loads((w.repo / w.r78.PLAN_B_78B["path"]).read_text())
    w.pin("PLAN_B_78B", w.record({**doc, "blinded_sigma_inputs_sha256": hx("other inputs")}))
    with pytest.raises(SystemExit, match="names another blinded_sigma inputs file than the output's"):
        w.init(dry_run=True, blinded=str(blinded))
    w.pin("PLAN_B_78B", w.record(doc))
    hosts = w.init(blinded=str(blinded), amount=3000.0)["hosts"]
    st = load_by_path("states_k2_b", w.root / "states_tool.py")
    keep = st.keep_list()["pods"]
    kept = {h for h in hosts if keep[h]["kept_until"]}
    seeds = {j["seed"] for h in kept for j in w.plan()["hosts"][h]["jobs"] if j["arm"] == "a0"}
    assert seeds == {1105, 1106, 1107}


@pytest.mark.parametrize("kept,top,ok", [(48, "s4_top", True), (49, "s4_top", True), (95, "s4_top", True),
                                         (96, "s4_top", True), (96, "s4_96", False), (97, "s4_top", True),
                                         (191, "s4_top", True), (192, "s4_192", True), (192, "s4_top", False),
                                         (47, "s4_top", False)])
def test_k2v7_the_dose_records_top_dose_is_the_scorer_layers_at_every_boundary(wa, kept, top, ok):
    """K2V-7 (K-5's cases): the scorer layer's nested_doses writes top_dose s4_192 from 192 kept rows and s4_top below
    (96 and 48 included); s4_kept reads that rule; fewer than 48 is the build stop."""
    w = wa
    p = w.record({"kind": "scale78b s4 doses record", "version": 1, "kept": kept, "fallback_fired": kept < 192,
                  "top_dose": top, "doses": {}})
    w.pin("S4_DOSES_RECORD", p, w.family)
    if ok:
        assert w.tool.s4_kept(w.family) == kept
    else:
        with pytest.raises(SystemExit):
            w.tool.s4_kept(w.family)


def test_k2v9_the_noise_outputs_plans_must_be_the_ones_its_own_sigma_gives(wa):
    """K2V-9 (the verifier's P5): a noise output whose seed rule says plan A at sigma 9.0 pp (H by the rule), whose
    pooled reading's seed rule differs, or whose family sigma_F plan contradicts its sigma, refuses."""
    w = wa
    out = lambda: str(w.repo / "records" / f"g-{w.n}.json")      # noqa: E731
    for doc, match in ((dict(noise_doc(), seed_rule=rule("A", False, 9.0), pooled={"seed_rule": rule("A", False, 9.0)}),
                        "is not the one its own sigma_pp gives"),
                       (dict(noise_doc(), pooled={"seed_rule": rule("B9", False)}), "is not its pooled reading's"),
                       (dict(noise_doc(sigma_f=("A", False))), None)):
        p = w.record(doc)
        if match is None:
            doc["families"]["llama31-8b"]["seed_rule_by_sigma_F"] = rule("A", False, 7.0)
            p = w.record(doc)
            match = "for llama31-8b: its seed rule's plan 'A' is not the one its own sigma_pp gives \\('H'"
        with pytest.raises(SystemExit, match=match):
            w.tool.record_gate_78b(str(p), sha(p), "B", "1", "test", out())


@pytest.mark.parametrize("cmd", [["block-a-need"], ["write-block-a-plan", "--out", "x", "--recorded-by", "t"],
                                 ["record-block-a-plan", "x", "--sha256", "0" * 64],
                                 ["record-block-a-replan", "x", "--sha256", "0" * 64],
                                 ["record-block-a-not-run", "x", "--sha256", "0" * 64]])
def test_k2v10_the_1b_block_a_commands_refuse_by_name(wa, cmd):
    """K2V-10 (the verifier's P7): the 1B block-A plan commands refuse by name in a 7-8B copy (no crash, no write)."""
    with pytest.raises(SystemExit, match=f"{cmd[0]} is the stage-1 \\(1B\\) block-A plan route"):
        wa.tool.main(cmd)
    assert not (wa.root / "plan.json").exists()


def test_k2v11_record_done_keeps_only_the_runners_reason_codes(wa):
    """K2V-11 (the verifier's P1b): record-done copies a job's reason into plan.json only when it is one of the job
    runner's codes (the runner's REFUSAL_REASONS, DEFER_REASONS and LS-04, read from its source); other text refuses."""
    import ast
    w = wa
    src = (w.root / "setup" / "job_runner_stage1.py").read_text()
    codes = []
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) in ("REFUSAL_REASONS", "DEFER_REASONS", "LS04"):
            value = ast.literal_eval(node.value)
            codes += list(value) if isinstance(value, tuple) else [value]
    assert sorted(codes) == sorted(w.tool.RUNNER_REASONS)
    hosts = released_a(w)
    pull_planted(w, hosts[0])
    tree = w.root / "retrieved" / hosts[0] / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    done["jobs"][0].update(status="crashed", reason=SENTINELS[0])
    done["jobs"][0].pop("complete_sha256")
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    with pytest.raises(SystemExit, match="job 0's reason is not one of the job runner's reason codes"):
        w.tool.record_done(hosts[0])
    assert SENTINELS[0] not in (w.root / "plan.json").read_text()
    done["jobs"][0]["reason"] = "s_obs"
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    w.tool.record_done(hosts[0])
    assert w.plan()["hosts"][hosts[0]]["jobs"][0]["reason"] == "s_obs"


def test_k2v3_under_b_the_kits_inputs_take_every_gate_family_once(wa, monkeypatch):
    """K2V-3 / V-merge-family-set: under [B] the kit's inputs file holds exactly the gate's two families' parts (each
    family's kit part, stood in here by synthetic entries)."""
    w = wa
    w.gate(option="B")
    entry = {"design": "full", "engine": {}, "edits": {}, "cells": {"a0": {"1101": {"path": "tmp/u", "complete_sha256": hx("u")}}}}
    monkeypatch.setattr(w.tool, "kit_part", lambda f, g: {"entry": json.loads(json.dumps(entry)), "family": f})
    doc = json.loads(w.tool.kit_inputs(json.loads((w.repo / w.r78.GATE_78B["path"]).read_text())))
    assert sorted(doc["families"]) == sorted(FAMILIES) and doc["option"] == "B"
    assert doc["families"]["llama31-8b"]["cells"]["a0"]["1101"]["path"] == "../u"


def a_done_c(w) -> list[str]:
    """Block A of OLMo-2-7B under [C], every host pulled and recorded; the governing simulation pinned for [C]."""
    hosts = released_a(w)
    for host in hosts:
        pull_planted(w, host)
        w.tool.record_done(host)
    s = SR2.__new__(SR2)
    s.w, s.families = w, ("olmo2-7b",)
    s.sim("C")
    return hosts


def test_r49_record_done_code_edited_after_block_as_last_release_voids_sr2(wa):
    """GXB R-49 (K2R-1; the re-verifier's R4b): record-done (the A copy's plan_tool.py) runs after block A's last
    release; an edit of it after the blinding record refuses at record-plan-b-78b, though the part and the inputs file
    were written."""
    w = wa
    hosts = released_a(w)
    (w.root / "plan_tool.py").write_text((w.root / "plan_tool.py").read_text() + "\n# record-done edited after release\n")
    for host in hosts:
        pull_planted(w, host)
        out = w.tool.record_done(host)
    assert "path" in out["blinded_inputs_part"]
    got = w.tool.write_blinded_inputs()
    s = SR2.__new__(SR2)
    s.w, s.families = w, ("olmo2-7b",)
    s.sim("C")
    blinded = w.record({"df": 12, "inputs_sha256": got["sha256"], "kind": "scale-78b blinded sigma", "sigma_A_pp": 4.0,
                        "version": 1}, "blinded-after-edit.json")
    with pytest.raises(SystemExit, match="verified another runkit/stage1-78b/plan_tool.py than the one that runs here"):
        w.tool.record_plan_b_78b(str(w.noise), str(blinded), sha(blinded), "test", str(w.repo / "records" / "pb.json"))
    assert not (w.repo / "records" / "pb.json").exists()


def test_r49_blinded_sigma_edited_after_block_a_voids_sr2_and_an_unverified_record_is_not_voided(wa):
    """GXB R-49 (the re-verifier's R4c): blinded_sigma.py edited after block A's init refuses at record-plan-b-78b; an
    unverified record adopts nothing, so the edit leaves its 'not adopted' reading as it is."""
    w = wa
    a_done_c(w)
    got = w.tool.write_blinded_inputs()
    bs = w.repo / "scripts/scale78b/blinded_sigma.py"
    kept = bs.read_bytes()
    bs.write_text(bs.read_text() + "\n# edited after block A\n")
    blinded = w.record({"df": 12, "inputs_sha256": got["sha256"], "kind": "scale-78b blinded sigma", "sigma_A_pp": 4.0,
                        "version": 1}, "blinded-after-bs-edit.json")
    with pytest.raises(SystemExit, match="verified another scripts/scale78b/blinded_sigma.py than the one in this checkout"):
        w.tool.record_plan_b_78b(str(w.noise), str(blinded), sha(blinded), "test", str(w.repo / "records" / "pb.json"))
    for rel in ("scripts/scale78b/tests/test_blinded_sigma.py", "runkit/stage1-78b/tests/test_planning_ab_78b.py"):
        bs.write_bytes(kept)
        other = w.repo / rel
        keep = other.read_bytes()
        other.write_bytes(keep + b"\n# edited after block A\n")
        with pytest.raises(SystemExit, match=f"verified another {rel} than the one in this checkout"):
            w.tool.record_plan_b_78b(str(w.noise), str(blinded), sha(blinded), "test", str(w.repo / "records" / "pb.json"))
        other.write_bytes(keep)
    bs.write_text(bs.read_text() + "\n# edited after block A\n")    # an unverified record, snapshotted by block A
    a = json.loads((w.root / "plan.json").read_text())
    w.blinding(verified=False, files={"scripts/scale78b/blinded_sigma.py": hx("the bytes before the edit")})
    a["blocks"]["A"]["blinding"]["sha256"] = w.tool.SR2_BLINDING_RECORD["sha256"]
    (w.root / "plan.json").write_text(json.dumps(a))
    rec = w.tool.record_plan_b_78b(str(w.noise), None, None, "test", str(w.repo / "records" / "pb-not.json"))
    assert (rec["sr2_adopted"], rec["sr2_reason"]) == (False, "blinding_test_not_verified")


def test_r49_block_b_rehashes_every_familys_block_a_code_at_init_and_release(wb):
    """GXB R-49 under [B]: init-block B and release B re-hash the blinding record's files, with each family's block-A
    copy's plan_tool.py (record-done's code there): an edit of Llama-3.1-8B's, or of the blinded_sigma test, refuses."""
    w = wb
    b_ready(w, sigma=4.0)
    seal_sibling(w, "A")
    out = json.loads((w.repo / w.r78.PLAN_B_78B["path"]).read_text())
    blinded = w.repo / "records" / [p.name for p in (w.repo / "records").glob("blinded-*.json")][-1]
    assert out["sr2_adopted"] is True and sha(blinded) == out["blinded_sigma_output_sha256"]
    llama = w.repo / "tmp" / "family-probe-s78-llama31-8b-A" / "plan_tool.py"
    keep = llama.read_bytes()
    llama.write_bytes(keep + b"\n# record-done edited in Llama's block-A copy\n")
    with pytest.raises(SystemExit, match="plan_tool.py than the one in tmp/family-probe-s78-llama31-8b-A/ "
                                         "\\(record-done's code\\)"):
        w.init(dry_run=True, blinded=str(blinded))
    llama.write_bytes(keep)
    host_out = w.init(blinded=str(blinded), amount=3000.0,
                      n_pods=len(w.rules.deal(w.rules.block_runs(out["plan"], "B"), "B")))
    test = w.repo / "scripts/scale78b/tests/test_blinded_sigma.py"
    test.write_bytes(test.read_bytes() + b"\n# edited after block B's init\n")
    plan = w.plan()
    name = host_out["hosts"][0]
    with pytest.raises(SystemExit, match="verified another scripts/scale78b/tests/test_blinded_sigma.py"):
        w.tool.release_hosts_ab(plan, "B", [(name, plan["hosts"][name])])


def test_r52_every_familys_block_a_snapshot_is_compared_under_b(wb):
    """GXB R-52 (K2R-4; the re-verifier's R1g): under [B] Llama-3.1-8B's block-A copy snapshotted another blinding
    record: block B refuses, though OLMo-2-7B's snapshot is the pinned one."""
    w = wb
    b_ready(w, sigma=None)
    seal_sibling(w, "A")
    path = w.repo / "tmp" / "family-probe-s78-llama31-8b-A" / "plan.json"
    doc = json.loads(path.read_text())
    doc["blocks"]["A"]["blinding"] = {"sha256": hx("another record")}
    path.write_text(json.dumps(doc))
    with pytest.raises(SystemExit, match="block A of llama31-8b .* was not planned under the pinned blinding record"):
        w.init(dry_run=True)


def test_r52_the_kit_inputs_file_must_hash_to_the_outputs_inputs_sha256(wa):
    """GXB R-52: the inputs file equal to the kit's rebuild but named by another SHA-256 in blinded_sigma.py's output
    refuses at record-plan-b-78b."""
    w = wa
    w.gate(option="B", plan="B9")
    SR2(w, "B")
    out, inputs = blinded_output(w, 4.0)
    doc = json.loads(out.read_text())
    other = w.record({**doc, "inputs_sha256": hx("another inputs file")}, "blinded-other-inputs.json")
    with pytest.raises(SystemExit, match="is not the one the kit writes from the block-A copies' parts"):
        plan_b(w, other)
    assert plan_b(w, out)["sr2_adopted"] is True


def test_r50_record_plan_b_reruns_blinded_sigma_and_refuses_a_hand_written_sigma_or_df(wa):
    """GXB R-50 (K2R-3): record-plan-b-78b runs blinded_sigma.read on the kit's inputs file itself (stood in here; the
    real read is held by the K2V-5 test) and refuses an output whose sigma_A_pp or df differs from it."""
    w = wa
    w.gate(option="B", plan="B9")
    SR2(w, "B")
    out, inputs = blinded_output(w, 5.0)
    calls = []
    for again in ({"sigma_A_pp": 4.0}, {"df": 23}, {"sigma_A_pp": 5}):
        w.mp.setattr(w.tool, "blinded_sigma_read",
                     lambda path, digest, script, again=again: calls.append((path, digest, script)) or
                     {"kind": "scale-78b blinded sigma", "version": 1, "inputs_sha256": digest, "sigma_A_pp": 5.0,
                      "df": 24, **again})
        with pytest.raises(SystemExit, match="is not the one blinded_sigma.read gives on the kit's inputs file"):
            plan_b(w, out)
    assert calls[0] == (w.tool.BLINDED_INPUTS, sha(inputs), sha(w.repo / "scripts/scale78b/blinded_sigma.py"))


def test_r51_the_kits_rerun_mismatched_requeue_takes_the_re_runs_unit(wa):
    """GXB R-51 (K2R-2; the re-verifier's R2c): after the kit's own requeue --rerun-mismatched in block A (the
    environment mismatch stood in), the replaced attempt is skipped and the cell is the re-run's on the new host; the
    part written before the requeue is replaced (only while no merged inputs file exists); two complete units that no
    kit record explains still refuse."""
    w = wa
    hosts = released_a(w)
    for host in hosts:
        pull_planted(w, host)
        w.tool.record_done(host)
    first = hosts[0]
    digest = w.plan()["hosts"][first]["jobs"][0]["complete_sha256"]
    w.mp.setattr(w.tool, "mismatch", lambda plan, attempt: ["device_name"])   # the environment differs (stand-in)
    new = w.tool.requeue(first, [digest])["to"]
    if new not in w.plan()["hosts"]:
        w.tool.release("A")
    pull_planted(w, new)
    written = w.tool.part_path(w.family).read_bytes()    # the part written at the last record-done before the requeue
    write(w.tool.BLINDED_INPUTS, "a merged inputs file (stand-in)")
    out = w.tool.record_done(new)
    assert "the merged inputs file exists" in out["blinded_inputs_part"]["waits"]
    assert w.tool.part_path(w.family).read_bytes() == written
    w.tool.BLINDED_INPUTS.unlink()
    out = w.tool.record_done(new)
    assert "path" in out["blinded_inputs_part"], out
    job = w.plan()["hosts"][new]["jobs"][0]
    part = json.loads((w.repo / out["blinded_inputs_part"]["path"]).read_text())
    cell = part["entry"]["cells"][job["arm"]][str(job["seed"])]
    assert f"/retrieved/{new}/tree/" in cell["path"] and cell["complete_sha256"] == job["complete_sha256"] != digest
    assert w.tool.part_superseded(written, part, w.plan())
    assert not w.tool.part_superseded(written, part, {**w.plan(), "requeues": []})
    for change in (lambda d: d["entry"].update(design="anchor_stopped"), lambda d: d.update(gate_sha256=hx("g"))):
        bad = json.loads(written)
        change(bad)
        assert not w.tool.part_superseded(canon(bad), part, w.plan())
    edited = json.loads(written)                         # a written cell that no kit record replaced
    cell = next(c for v in edited["entry"]["cells"].values() for c in v.values()
                if c["complete_sha256"] not in w.tool.replaced_attempts(w.plan()))
    cell["complete_sha256"] = hx("a hand-made cell")
    w.tool.part_path(w.family).write_bytes(canon(edited))
    assert "exists with other bytes" in w.tool.record_done(new)["blinded_inputs_part"]["waits"]
    plan = w.plan()
    plan["requeues"][-1]["complete_sha256"] = [hx("another attempt")]
    with pytest.raises(SystemExit, match="two complete units"):
        w.tool.blinded_inputs_part(plan, w.family)
    plan = w.plan()
    plan["requeues"][-1]["reason"] = "pre-job-failed"
    with pytest.raises(SystemExit, match="two complete units"):
        w.tool.blinded_inputs_part(plan, w.family)
    plan = w.plan()
    plan["requeues"][-1]["from"] = hosts[1]
    with pytest.raises(SystemExit, match="two complete units"):
        w.tool.blinded_inputs_part(plan, w.family)
